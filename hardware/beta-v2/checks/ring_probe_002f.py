# -*- coding: utf-8 -*-
"""FBV2-P2-002F -- CHOOSE THE RING WITH THE REAL ROUTER.

The fan-out proxy in place_search_002f.py routes the eight U18 pins on a grid
with only the pads in the way.  That is enough to reject a ring whose targets
CROSS or STACK, and it caught both - but it cannot see the copper the routing
plan lays BEFORE the pin field: a 1.50 mm trunk, a 75 mm BAT_PROTECTED_P run,
BAT_SENSE with two vias, BAT_MID and BAT_RAW.  Section 8 puts all of that first
(PR-18) and it is most of the copper near U18.

So the ring is chosen by ROUTING it.  For each ring variant the real router
lays exactly the prefix the plan lays - trunk, U11.2 flare, the BAT_MAIN chain -
and then tries all eight U18 pins in the plan's own order.  The ring that closes
the most wins; ties go to the shortest pin-field copper.

    "<KICAD>/bin/python.exe" ring_probe_002f.py [pose_index]
"""
import os, sys, json, time, math, faulthandler
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import place_search_002f as PS
import path_role_util as RU
import qrouter as QR
import battery_route_plan as PL
import pcbnew

N = PL.N
CP, CT_W, CT_S = 200000, 300000, 200000
WIDE = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                 'BAT_SENSE', 'BAT_PROTECTED_P'))
CHAIN = [
    ('BAT_PROTECTED_P', 'R75.2', 'D9.1', [PL.W_TRUNK_BPP, 1200000], CT_W),
    ('BAT_SENSE', 'Q3.6', 'R75.1', PL.LAD_BAT, CT_W),
    ('BAT_SENSE', 'Q3.5', 'Q3.6', PL.LAD_BAT, CT_W),
    ('BAT_MID', 'Q2.6', 'Q3.8', PL.LAD_BAT, CT_W),
    ('BAT_MID', 'Q2.5', 'Q2.6', PL.LAD_BAT, CT_W),
    ('BAT_MID', 'Q3.8', 'Q3.7', PL.LAD_BAT, CT_W),
    ('BAT_RAW', 'F1.2', 'Q2.8', PL.LAD_BAT, CT_W),
    ('BAT_RAW', 'Q2.8', 'Q2.7', PL.LAD_BAT, CT_W),
    ('BAT_CONNECTOR_P', 'J4.1', 'F1.1', PL.LAD_BAT, CT_W),
]
PINS = [
    ('LTC_GATE', 'U18.10', 'R76.1', PL.LAD_SIG, CT_W),
    ('BAT_RAW', 'U18.1', 'R77.1', [PL.W_SENSE], CT_W),
    ('BAT_SENSE', 'U18.9', 'R75.1', [PL.W_SENSE], CT_W),
    ('BAT_PROTECTED_P', 'U18.8', 'R75.2', [PL.W_SENSE], CT_W),
    ('LTC4368_FAULT_N', 'U18.7', 'R81.2', PL.LAD_SIG, CT_W),
    ('LTC_SHDN', 'U18.6', 'R80.2', PL.LAD_SIG, CT_W),
    ('LTC_OV', 'U18.3', 'R77.2', PL.LAD_SIG, CT_W),
    ('LTC_UV', 'U18.2', 'R79.2', PL.LAD_SIG, CT_W),
]


def lay(qb, P, net, a, b_, ladder, ct):
    pa, pb = P.get(a), P.get(b_)
    if pa is None or pb is None:
        return dict(ok=False, reason='MISSING', mm=0)
    m = qb.mark()
    r = None
    for w in ladder:
        r = QR.connect_role(qb, N + net, pa, pb, 'B', w, CP, ct)
        if r['ok']:
            return r
        qb.revert(m)
    for w in ladder[-1:]:
        r = QR.connect_hop(qb, N + net, pa, pb, w, CP, ct,
                           via_dia=600000, via_drill=300000)
        if r['ok']:
            return r
        qb.revert(m)
    return r


def freedom(qb, pad, need):
    return len(qb.escape(pad, 'B', need, need, CP, CT_W, 25000, qb.ex0, qb.ey0))


def widest(qb, pad):
    lo, hi, best = 50000, 1000000, 0
    while hi - lo > 5000:
        mid = ((lo + hi) // 2 // 5000) * 5000
        if qb.escape(pad, 'B', mid, mid, CP, CT_W, 25000, qb.ex0, qb.ey0):
            best, lo = mid, mid
        else:
            hi = mid
    return best


def probe(M, place, tag):
    RU.fresh(PS.WORK, tag)
    pcb = os.path.join(PS.WORK, tag, RU.PCBNAME)
    M.write(pcb, place)
    qb = QR.QBoard(pcb)
    qb.wide_nets = WIDE
    P = PS.qpads(qb)
    t0 = time.time()
    for (net, a, b_, lad, ct) in CHAIN:
        lay(qb, P, net, a, b_, lad, ct)
    # the U11.2 flare goes with the trunk, exactly as the plan emits it
    try:
        eD = qb.escape(P['D9.1'], 'B', PL.W_TRUNK_BPP, PL.W_TRUNK_BPP, CP, CT_W,
                       50000, qb.ex0, qb.ey0)
        regs = {}
        if eD:
            seed = (eD[0]['x'], eD[0]['y'])
            for w in (300000, 400000, 600000, 800000, 1000000, 1200000,
                      PL.W_TRUNK_BPP):
                regs[w] = qb.free_region('B', N + 'BAT_PROTECTED_P', w, CP,
                                         CT_W, 50000, seed, qb.ex0 - 1000000,
                                         qb.ey0 - 1000000, qb.ex1 + 1000000,
                                         qb.ey1 + 1000000)
        f = qb.flare(N + 'BAT_PROTECTED_P', P['U11.2'], 'B', PL.W_TRUNK_BPP,
                     PL.W_SENSE, CP, CT_W, 25000, region=regs)
        if f:
            lp = dict(ref='U11.2/launch', x=f['x'], y=f['y'], F=False, B=True,
                      shape=QR.RR(f['x'], f['y'], 1, 1, 0, 0,
                                  N + 'BAT_PROTECTED_P', 'launch'),
                      hx=1, hy=1, r=0, ang=0, net=N + 'BAT_PROTECTED_P',
                      tht=False, anchor=True)
            QR.connect_role(qb, N + 'BAT_PROTECTED_P', lp, P['D9.1'], 'B',
                            PL.W_TRUNK_BPP, CP, CT_W)
    except Exception as e:
        print('   flare skipped: %s' % e)

    # the pin field, ordered the way the plan orders it: tightest slack first,
    # ties broken by how many ways out the pad still has (PR-30)
    todo = list(PINS)
    done, mm, detail = 0, 0.0, []
    while todo:
        rows = []
        for k, (net, a, b_, lad, ct) in enumerate(todo):
            pad = P.get(a)
            need = min(lad)
            w = widest(qb, pad) if pad else 0
            nd = freedom(qb, pad, need) if pad else 0
            rows.append((w - need, nd, w, k))
        rows.sort(key=lambda r: (r[0], r[1], r[2]))
        k = rows[0][3]
        (net, a, b_, lad, ct) = todo.pop(k)
        r = lay(qb, P, net, a, b_, lad, ct)
        if r and r['ok']:
            done += 1
            mm += r['mm']
            detail.append('%s=%.1f' % (a.split('.')[-1], r['mm']))
        else:
            detail.append('%s=X' % a.split('.')[-1])
    return done, round(mm, 2), detail, round(time.time() - t0, 1)


def main():
    faulthandler.enable()
    idx = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 0
    M = PS.Model(RU.fresh(PS.WORK, 'RP'))
    ctx = PS.build_ctx(M)
    scored = json.load(open(os.path.join(SP, 'place_002f_stage1.json')))['scored']
    s_ = PS.shortlist(scored, 20)[idx]
    print('pose %d: rot %d at (%.2f, %.2f)  k8=%.2f k9=%.2f mis=%.2f'
          % (idx, s_['rot'], s_['x'], s_['y'], s_['k8'], s_['k9'], s_['mis']))
    tab = PS.slot_table(M, ctx)
    tl, corr = PS.trunk_corridor(M, ctx, s_)
    seen, best, rows = set(), None, []
    for k, (cw, order) in enumerate(PS.RESTARTS):
        pl = PS.ring(M, ctx, tab, s_, corridor=corr, chain_w=cw, order=order)
        if pl is None:
            continue
        key = tuple(sorted((r, tuple(round(v, 3) for v in p))
                           for r, p in pl.items()))
        if key in seen:
            print('  V%d  (identical to an earlier variant)' % k)
            continue
        seen.add(key)
        nf, _l, _d = PS.fanout(M, pl, ctx['PG'], ctx['FP'])
        done, mm, det, secs = probe(M, pl, 'RP%d' % k)
        rows.append(dict(v=k, chain_w=cw, fanout=nf, routed=done, mm=mm,
                         detail=det, secs=secs, pose=idx,
                         place={a: [round(x, 3) for x in b]
                                for a, b in pl.items()}))
        print('  V%d chain_w=%.1f  proxy %d/8  ROUTED %d/8  %7.2f mm  %5.0fs  %s'
              % (k, cw, nf, done, mm, secs, ' '.join(det)))
        sys.stdout.flush()
        json.dump(rows, open(os.path.join(SP, 'ring_probe_002f.json'), 'w'),
                  indent=1)
        if best is None or (done, -mm) > (best['routed'], -best['mm']):
            best = rows[-1]
        if done == 8:
            break
    if best:
        print('\nBEST: V%d  routed %d/8  %.2f mm'
              % (best['v'], best['routed'], best['mm']))
        json.dump(best['place'],
                  open(os.path.join(SP, 'place_002f_C00.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
