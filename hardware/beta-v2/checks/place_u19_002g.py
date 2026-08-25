# -*- coding: utf-8 -*-
"""FBV2-P2-002G sections 9-11 -- the JOINT U19 + R80 + R81 placement search.

FBV2-P2-002F closed U18 and left three pads open, and all three are the same
shape of problem one region over:

  R80.1   a BAT_RAW pad in a ~1 mm slot, boxed by its OWN partner's route to
          U18.6 and by R81's to U18.7
  U19.3   an SOT-23-8 pin whose row faces the board edge with one lane
  U19.8   NO_PATH across 2.668 mm, because the 0.93 mm gap beside U19 is full

Section 9 forbids searching U19 in isolation, and it is right to: R80/R81 sit in
the same west margin and it is one capacity problem.

THE METHOD IS SECTION 11's, AND THE ORDER MATTERS.

  A  courtyard / edge / rule-area filter                     (cheap, analytic)
  B  pad-escape margin filter                                (cheap, analytic)
  C  section 6 span cap, so a candidate cannot buy escape
     room with a 25 mm megohm node                           (cheap, analytic)
  D  PREFIX-COPPER REAL-ROUTER PROBE                         (expensive, honest)
  E  rank

Stage D is the whole point.  FBV2-P2-002F proved four separate times that a
bare-board escape count predicts nothing: a pad emits a 0.5 mm stub and a
connection is a route.  So a candidate is only ever accepted on what the REAL
router does to it, against the copper the plan actually lays first, and it is
judged on PR-39 connectivity rather than on a returned `ok`.
"""
import os, sys, json, math, time, collections, faulthandler
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import place_search_002f as PS
import place_deadcell_002f as DC
import path_role_util as RU
import qrouter as QR
import battery_route_plan as PL
import place_p2_002f as ECO
import pcbnew

N = PL.N
CP, CT_W, CT_S = 200000, 300000, 200000
WIDE = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                 'BAT_SENSE', 'BAT_PROTECTED_P'))
MOVE = ['U19', 'R80', 'R81']
U19SIG = ['1', '2', '3', '5', '6', '7', '8']          # 4 is GND

# The prefix the routing plan lays BEFORE the taps and the dead-cell block,
# with PR-36 in force (taps precede the trip network).  The U11.2 flare and the
# 64 mm FAULT_N run are deliberately omitted: neither touches R80 or U19 before
# the items under test, and together they cost eight minutes a candidate.
PREFIX = [
    ('BAT_PROTECTED_P', 'R75.2', 'D9.1', [PL.W_TRUNK_BPP, 1200000], CT_W),
    ('BAT_SENSE', 'Q3.6', 'R75.1', PL.LAD_BAT, CT_W),
    ('BAT_SENSE', 'Q3.5', 'Q3.6', PL.LAD_BAT, CT_W),
    ('BAT_MID', 'Q2.6', 'Q3.8', PL.LAD_BAT, CT_W),
    ('BAT_MID', 'Q2.5', 'Q2.6', PL.LAD_BAT, CT_W),
    ('BAT_MID', 'Q3.8', 'Q3.7', PL.LAD_BAT, CT_W),
    ('BAT_RAW', 'F1.2', 'Q2.8', PL.LAD_BAT, CT_W),
    ('BAT_RAW', 'Q2.8', 'Q2.7', PL.LAD_BAT, CT_W),
    ('BAT_CONNECTOR_P', 'J4.1', 'F1.1', PL.LAD_BAT, CT_W),
    # U18's pin field: these are the routes that boxed R80.1 in
    ('BAT_SENSE', 'U18.9', 'R75.1', [PL.W_SENSE], CT_W),
    ('BAT_PROTECTED_P', 'U18.8', 'R75.2', [PL.W_SENSE], CT_W),
    ('BAT_RAW', 'U18.1', 'R77.1', [PL.W_SENSE], CT_W),
    ('LTC4368_FAULT_N', 'U18.7', 'R81.2', PL.LAD_SIG, CT_W),
    ('LTC_GATE', 'U18.10', 'R76.1', PL.LAD_SIG, CT_W),
    ('LTC_UV', 'U18.2', 'R79.2', PL.LAD_SIG, CT_W),
    ('LTC_OV', 'U18.3', 'R77.2', PL.LAD_SIG, CT_W),
    ('LTC_SHDN', 'U18.6', 'R80.2', PL.LAD_SIG, CT_W),
]
# the items under test, in the plan's own order
TAPS = [
    ('BAT_RAW', 'R80.1', 'Q2.7', PL.LAD_TAP, CT_W),
    ('BAT_RAW', 'R79.1', 'R80.1', PL.LAD_TAP, CT_W),
    ('BAT_RAW', 'R77.1', 'R79.1', PL.LAD_TAP, CT_W),
]


def joined(b, a, c):
    b.BuildConnectivity()
    cn = b.GetConnectivity()
    pp = {}
    for f in b.GetFootprints():
        for q in f.Pads():
            pp[f.GetReference() + '.' + q.GetNumber()] = q
    if a not in pp or c not in pp:
        return False
    grp = {str(i.m_Uuid.AsString()) for i in cn.GetConnectedItems(pp[a])}
    return str(pp[c].m_Uuid.AsString()) in grp


def anchor(qb, net, pa, w, ct):
    LID = qb.b.GetLayerID('B.Cu')
    cand = []
    for t in qb.b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != LID:
            continue
        if t.GetNetname() != net:
            continue
        ax, ay, bx, by = (t.GetStart().x, t.GetStart().y,
                          t.GetEnd().x, t.GetEnd().y)
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L // 500000))
        for k in range(n + 1):
            u = k / float(n)
            cand.append((math.hypot(int(ax + u * (bx - ax)) - pa['x'],
                                    int(ay + u * (by - ay)) - pa['y']),
                         int(ax + u * (bx - ax)), int(ay + u * (by - ay))))
    cand.sort()
    for (_, px, py) in cand[:200]:
        if qb.point_free('B', net, px, py, w, CP, ct, 50000):
            d = RU.pseudo_pad(net, px, py, QR)
            d['anchor'] = True
            d['ref'] = '(node)'
            return d
    return None


def lay(qb, P, net, a, b_, ladder, ct):
    """Route, then judge by PR-39: the REQUESTED pads must end up connected."""
    pa, pb = P.get(a), P.get(b_)
    if pa is None or pb is None:
        return False, 0.0
    if joined(qb.b, a, b_):
        return True, 0.0
    m = qb.mark()
    for w in ladder:
        r = QR.connect_role(qb, N + net, pa, pb, 'B', w, CP, ct)
        if r['ok'] and joined(qb.b, a, b_):
            return True, r['mm']
        qb.revert(m)
    for w in ladder[-1:]:
        tgt = anchor(qb, N + net, pa, w, ct)
        if tgt is not None:
            r = QR.connect_role(qb, N + net, pa, tgt, 'B', w, CP, ct)
            if r['ok'] and joined(qb.b, a, b_):
                return True, r['mm']
            qb.revert(m)
        r = QR.connect_hop(qb, N + net, pa, pb, w, CP, ct,
                           via_dia=600000, via_drill=300000)
        if r['ok'] and joined(qb.b, a, b_):
            return True, r['mm']
        qb.revert(m)
    return False, 0.0


def mst(pads):
    refs = list(pads)
    if len(refs) < 2:
        return []
    ins, out = {refs[0]}, []
    while len(ins) < len(refs):
        best = None
        for a in ins:
            for b in refs:
                if b in ins:
                    continue
                d = math.hypot(pads[a]['x'] - pads[b]['x'],
                               pads[a]['y'] - pads[b]['y'])
                if best is None or d < best[0]:
                    best = (d, a, b)
        out.append((best[1], best[2]))
        ins.add(best[2])
    return out


def probe(M, place, tag):
    """Stage D.  Lay the real prefix, then the two things under test."""
    RU.fresh(PS.WORK, tag)
    pcb = os.path.join(PS.WORK, tag, RU.PCBNAME)
    ECO.apply(pcb, report=False)
    b = pcbnew.LoadBoard(pcb)
    for ref, (x, y, rot) in place.items():
        f = [g for g in b.GetFootprints() if g.GetReference() == ref][0]
        f.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6))))
        f.SetOrientationDegrees(rot)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(pcb)

    qb = QR.QBoard(pcb)
    qb.wide_nets = WIDE
    P = PS.qpads(qb)
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(net, {})[ref] = p

    for (net, a, b_, lad, ct) in PREFIX:
        lay(qb, P, net, a, b_, lad, ct)
    r80 = False
    for (net, a, b_, lad, ct) in TAPS:
        ok, _mm = lay(qb, P, net, a, b_, lad, ct)
        if a == 'R80.1' or b_ == 'R80.1':
            r80 = r80 or joined(qb.b, 'R80.1', 'Q2.7')
    r80 = joined(qb.b, 'R80.1', 'Q2.7')

    # the dead-cell block, ordered tightest-first by the TIGHTER end (PR-38)
    todo = []
    for short in PL.DEADCELL:
        for (a, b_) in mst(pads.get(N + short, {})):
            todo.append((short, a, b_))

    def widest(pad):
        lo, hi, best = 50000, 1000000, 0
        while hi - lo > 5000:
            mid = ((lo + hi) // 2 // 5000) * 5000
            if qb.escape(pad, 'B', mid, mid, CP, CT_W, 25000, qb.ex0, qb.ey0):
                best, lo = mid, mid
            else:
                hi = mid
        return best

    while todo:
        rows = []
        for k, (short, a, b_) in enumerate(todo):
            best = None
            for ref in (a, b_):
                pad = P.get(ref)
                if pad is None:
                    continue
                w = widest(pad)
                nd = len(qb.escape(pad, 'B', 150000, 150000, CP, CT_S, 25000,
                                   qb.ex0, qb.ey0))
                key = (w - 150000, nd, w)
                if best is None or key < best:
                    best = key
            rows.append(((best or (0, 0, 0)), k))
        rows.sort()
        k = rows[0][1]
        (short, a, b_) = todo.pop(k)
        lay(qb, P, short, a, b_, PL.LAD_SIG, CT_S)

    qb.save()
    u19 = 0
    for n_ in U19SIG:
        p = P.get('U19.' + n_)
        if p is None:
            continue
        nm = p['net'][len(N):]
        others = [r for r in pads.get(N + nm, {}) if r != 'U19.' + n_]
        if any(joined(qb.b, 'U19.' + n_, o) for o in others):
            u19 += 1
    return u19, r80, pcb


def main():
    faulthandler.enable()
    t0 = time.time()
    base = RU.fresh(PS.WORK, 'G0')
    ECO.apply(base, report=False)
    M = PS.Model(base)
    nm = DC.netmap(M)
    fixed = M.fixed_courts(MOVE)
    fixed_r = [c for (_, _, c) in fixed]

    # ---- stage A + B: legal poses whose pins have a real outward band -----
    def band_ok(ref, x, y, rot, pins, depth=1.30):
        d = dict(M.padrects_id(ref, x, y, rot))
        for n_ in pins:
            r = d.get(ref + '.' + n_)
            if r is None:
                return False
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            dx, dy = cx - x, cy - y
            if abs(dx) >= abs(dy):
                band = ((r[2] + 0.05, r[1] - 0.05, r[2] + depth, r[3] + 0.05)
                        if dx > 0 else
                        (r[0] - depth, r[1] - 0.05, r[0] - 0.05, r[3] + 0.05))
            else:
                band = ((r[0] - 0.05, r[3] + 0.05, r[2] + 0.05, r[3] + depth)
                        if dy > 0 else
                        (r[0] - 0.05, r[1] - depth, r[2] + 0.05, r[1] - 0.05))
            if (band[0] < M.edge[0] + 0.30 or band[1] < M.edge[1] + 0.30 or
                    band[2] > M.edge[2] - 0.30 or band[3] > M.edge[3] - 0.30):
                return False
            if any(PS.ovl(band, rr) for (_i, rr) in FPI):
                return False
        return True

    FPI = M.fixed_pads(MOVE)
    u19c = []
    for rot in (0, 90, 180, 270):
        rect, _ = M.local('U19', rot)
        x = 1.0
        while x <= 22.0:
            y = 8.0
            while y <= 34.0:
                c = (x + rect[0], y + rect[1], x + rect[2], y + rect[3])
                if (c[0] >= M.edge[0] and c[1] >= M.edge[1] and
                        c[2] <= M.edge[2] and c[3] <= M.edge[3] and
                        not any(PS.ovl(c, fr) for fr in fixed_r) and
                        not any(PS.ovl(c, rr) for rr in M.rule) and
                        band_ok('U19', x, y, rot, U19SIG)):
                    sp = DC.spans(M, nm, {'U19': (x, y, rot)})
                    w = max(sp.values())
                    if w <= 20.0:
                        u19c.append((round(w, 2), rot, round(x, 2), round(y, 2)))
                y += 0.5
            x += 0.5
    u19c.sort()
    print('stage A+B+C: %d U19 poses with a clear band on all seven signal '
          'pins and every dead-cell span <= 20 mm' % len(u19c))

    # ---- R80 / R81: BAT_RAW pad must face the BAT_RAW chain --------------
    u18_6 = M.pad('U18', '6', *ECO.MOVES['U18'][:3])
    u18_7 = M.pad('U18', '7', *ECO.MOVES['U18'][:3])
    r79_1 = M.pad('R79', '1', *ECO.MOVES['R79'][:3])
    r82_1 = M.pad('R82', '1', *ECO.MOVES['R82'][:3])

    def ring_slots(ref, serve_pad, serve_tgt, chain_pad, chain_tgt, box):
        out = []
        for rot in (0, 90, 180, 270):
            rect, _ = M.local(ref, rot)
            x = box[0]
            while x <= box[2]:
                y = box[1]
                while y <= box[3]:
                    c = (x + rect[0], y + rect[1], x + rect[2], y + rect[3])
                    if (not any(PS.ovl(c, fr) for fr in fixed_r) and
                            not any(PS.ovl(c, rr) for rr in M.rule) and
                            band_ok(ref, x, y, rot, [serve_pad, chain_pad])):
                        ps = M.pad(ref, serve_pad, x, y, rot)
                        pc = M.pad(ref, chain_pad, x, y, rot)
                        # PR-31: each pad must FACE the thing it serves
                        ws = 0.0
                        for (pd, tgt) in ((ps, serve_tgt), (pc, chain_tgt)):
                            dx, dy = pd[0] - x, pd[1] - y
                            o = ((1, 0) if (abs(dx) >= abs(dy) and dx > 0) else
                                 (-1, 0) if abs(dx) >= abs(dy) else
                                 (0, 1) if dy > 0 else (0, -1))
                            pr = (tgt[0] - pd[0]) * o[0] + (tgt[1] - pd[1]) * o[1]
                            if pr < 0:
                                ws += -pr
                        d = (math.dist(ps, serve_tgt) + math.dist(pc, chain_tgt))
                        out.append((round(ws, 2), round(d, 2), rot,
                                    round(x, 2), round(y, 2), c))
                    y += 0.5
                x += 0.5
        out.sort()
        return out

    r80s = ring_slots('R80', '2', u18_6, '1', r79_1, (4.0, 56.0, 18.0, 78.0))
    r81s = ring_slots('R81', '2', u18_7, '1', r82_1, (4.0, 56.0, 18.0, 78.0))
    print('stage A+B: R80 slots %d, R81 slots %d' % (len(r80s), len(r81s)))

    # ---- assemble joint candidates, mutually non-overlapping -------------
    cands = []
    for (w, rot, x, y) in u19c[:40]:
        for (ws0, d0, r0, x0, y0, c0) in r80s[:20]:
            for (ws1, d1, r1, x1, y1, c1) in r81s[:20]:
                if PS.ovl(c0, c1):
                    continue
                cands.append(dict(span=w, u19=(rot, x, y), r80=(r0, x0, y0),
                                  r81=(r1, x1, y1),
                                  score=(ws0 + ws1, w, d0 + d1)))
                break
            break
    cands.sort(key=lambda c: c['score'])
    cands = cands[:8]
    print('stage E: %d joint candidates carried to the real-router probe'
          % len(cands))
    json.dump(cands, open(os.path.join(SP, 'u19_candidates_002g.json'), 'w'),
              indent=1)

    rows = []
    for k, c in enumerate(cands):
        place = {'U19': c['u19'][1:] + (c['u19'][0],),
                 'R80': c['r80'][1:] + (c['r80'][0],),
                 'R81': c['r81'][1:] + (c['r81'][0],)}
        place = {'U19': (c['u19'][1], c['u19'][2], c['u19'][0]),
                 'R80': (c['r80'][1], c['r80'][2], c['r80'][0]),
                 'R81': (c['r81'][1], c['r81'][2], c['r81'][0])}
        t = time.time()
        u19ok, r80ok, _p = probe(M, place, 'G%02d' % k)
        rows.append(dict(i=k, place={a: list(b) for a, b in place.items()},
                         span=c['span'], u19=u19ok, r80=bool(r80ok),
                         secs=round(time.time() - t, 1)))
        print('  C%02d U19 %s(%.2f,%.2f) rot%d  R80 rot%d(%.2f,%.2f)  '
              'R81 rot%d(%.2f,%.2f)  ->  U19 %d/7  R80.1 %s  span %.2f  %.0fs'
              % (k, '', c['u19'][1], c['u19'][2], c['u19'][0],
                 c['r80'][0], c['r80'][1], c['r80'][2],
                 c['r81'][0], c['r81'][1], c['r81'][2],
                 u19ok, 'CONNECTED' if r80ok else 'open', c['span'],
                 time.time() - t))
        sys.stdout.flush()
        json.dump(rows, open(os.path.join(SP, 'u19_probe_002g.json'), 'w'),
                  indent=1)
        if u19ok == 7 and r80ok:
            print('  -> C%02d satisfies both bottlenecks; stopping the search.' % k)
            break
    print('\nprobe complete in %.1f s' % (time.time() - t0))


if __name__ == '__main__':
    main()
