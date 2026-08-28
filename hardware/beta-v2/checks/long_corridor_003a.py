# -*- coding: utf-8 -*-
"""FBV2-P2-003A / D-273 -- MEASURE the legal LONG B.Cu corridor families for
the BAT_PROTECTED_P trunk R75.2 -> (net copper) at 1.50 mm target / 1.20 mm
floor, zero via, that LEAVE the saturated west margin.

The CTO ruling: before any F.Cu high-current via bridge, test the
reservation-dependent long outer-B.Cu route.  This is a MEASUREMENT harness --
it lays real scratch copper for each trial (via QR.connect_role, the same path
search the router uses for the trunk) and reverts it, so every number is a real
obstacle-aware search result, not an analytic clearance.

Input board is the post-pass-1 c3_00 scratch board (U18 8/8, control field,
U11.2->D9.1 leg and the D9 reservation laid, western BPP trunk still OPEN).  The
existing BAT_PROTECTED_P copper is the join target set: R75.2 must reach ANY
point on it via a >=1.20 mm B.Cu corridor with zero vias, going the long way if
the short west-margin corridor is severed.

    python long_corridor_003a.py [board.kicad_pcb] [out.json]
"""
import os, sys, io, json, math, time
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import battery_route_plan as PL
import qrouter as QR
import path_role_util as RU

N = PL.N
CP, CT_W = 200000, 300000
NET = N + 'BAT_PROTECTED_P'
WIDE = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                 'BAT_SENSE', 'BAT_PROTECTED_P'))
W150, W120 = 1500000, 1200000


def net_copper(qb):
    """Every BAT_PROTECTED_P B.Cu segment on the board, as (x0,y0,x1,y1,w)."""
    LID = qb.b.GetLayerID('B.Cu')
    out = []
    for t in qb.b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != LID:
            continue
        if t.GetNetname() != NET:
            continue
        s, e = t.GetStart(), t.GetEnd()
        out.append((s.x, s.y, e.x, e.y, t.GetWidth()))
    return out


def sample_points(segs, step=1000000):
    """Sample candidate join points along the net copper at `step` nm."""
    pts = []
    for (x0, y0, x1, y1, w) in segs:
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L // step))
        for k in range(n + 1):
            u = k / float(n)
            pts.append((int(x0 + u * (x1 - x0)), int(y0 + u * (y1 - y0))))
    # de-dup on a 0.5 mm grid
    seen, uniq = set(), []
    for (x, y) in pts:
        key = (x // 500000, y // 500000)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((x, y))
    return uniq


def trial(qb, src, x, y, w):
    """Lay a real connect_role from R75.2 to an anchor at (x,y); measure; revert."""
    anchor = RU.pseudo_pad(NET, x, y, QR)
    anchor['anchor'] = True
    anchor['ref'] = '(node)'
    m = qb.mark()
    t0 = time.time()
    r = QR.connect_role(qb, NET, src, anchor, 'B', w, CP, CT_W)
    qb.revert(m)
    r['dt'] = round(time.time() - t0, 1)
    return r


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        SP, 'w', 'c3repro003a', 'aqroot-Beta-v2.kicad_pcb')
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        SP, 'place_002z', 'long_corridor_003a.json')
    qb = QR.QBoard(board)
    qb.wide_nets = WIDE
    src = qb.pads[(NET, 'R75.2')]
    d91 = qb.pads.get((NET, 'D9.1'))
    u112 = qb.pads.get((NET, 'U11.2'))
    print('board   %s' % board)
    print('R75.2   (%.3f, %.3f)' % (src['x'] / 1e6, src['y'] / 1e6))
    if d91:
        print('D9.1    (%.3f, %.3f)' % (d91['x'] / 1e6, d91['y'] / 1e6))
    if u112:
        print('U11.2   (%.3f, %.3f)' % (u112['x'] / 1e6, u112['y'] / 1e6))
    segs = net_copper(qb)
    xs = [s[0] for s in segs] + [s[2] for s in segs]
    print('net copper: %d B.Cu segs, x-extent %.2f..%.2f mm'
          % (len(segs), min(xs) / 1e6, max(xs) / 1e6))

    rec = {'board': board, 'src': [src['x'], src['y']],
           'net_segs': len(segs), 'control': {}, 'candidates': []}

    # ---- CONTROL: the SHORT direct trunk, expected to fail (west margin) -----
    if d91:
        for w in (W150, W120):
            r = trial(qb, src, d91['x'], d91['y'], w)
            rec['control']['R75.2->D9.1 @%.2f' % (w / 1e6)] = {
                'ok': r['ok'], 'mm': round(r.get('mm', 0), 3),
                'reason': r.get('reason'), 'why': r.get('why'), 'dt': r['dt']}
            print('  CONTROL R75.2->D9.1 @%.2f  ok=%s  %s  %s'
                  % (w / 1e6, r['ok'], r.get('reason', ''), r.get('why', '')[:60]))

    # ---- LONG families: reach ANY point on the net copper -------------------
    # Sample the net copper at 3 mm.  A LONG family must join EAST of the west
    # margin (x >= 13.5 mm); the west points are the short corridor the control
    # already covers, so we test at most a few of them and focus on the east.
    cands = sample_points(segs, step=3000000)
    east = [c for c in cands if c[0] >= 13500000]
    west = [c for c in cands if c[0] < 13500000]
    cands = east + west[::3]        # every east point; a sparse west sample
    print('sampling %d join candidates (%d east, %d west-sparse)'
          % (len(cands), len(east), len(west[::3])))
    best = {W150: None, W120: None}
    for (x, y) in cands:
        is_west = x < 13500000
        row = {'x': x, 'y': y, 'x_mm': round(x / 1e6, 2), 'y_mm': round(y / 1e6, 2),
               'region': 'west' if is_west else 'east', 'w': {}}
        for w in (W150, W120):
            r = trial(qb, src, x, y, w)
            row['w']['%.2f' % (w / 1e6)] = {
                'ok': r['ok'], 'mm': round(r.get('mm', 0), 3),
                'reason': r.get('reason'), 'dt': r['dt']}
            if r['ok']:
                cand = (round(r['mm'], 3), x, y)
                if best[w] is None or cand[0] < best[w][0]:
                    best[w] = cand
        rec['candidates'].append(row)
        anyok = any(row['w'][k]['ok'] for k in row['w'])
        if anyok:
            print('  JOIN  (%.2f,%.2f) %-4s  1.50:%s %s  1.20:%s %s'
                  % (x / 1e6, y / 1e6, row['region'],
                     row['w']['1.50']['ok'], row['w']['1.50']['mm'],
                     row['w']['1.20']['ok'], row['w']['1.20']['mm']))

    rec['best'] = {'%.2f' % (w / 1e6): (None if best[w] is None else
                   {'mm': best[w][0], 'x_mm': round(best[w][1] / 1e6, 2),
                    'y_mm': round(best[w][2] / 1e6, 2)}) for w in (W150, W120)}
    # east-only best (a real LONG family that leaves the margin)
    east_best = {W150: None, W120: None}
    for row in rec['candidates']:
        if row['region'] != 'east':
            continue
        for w in (W150, W120):
            k = '%.2f' % (w / 1e6)
            if row['w'][k]['ok']:
                c = (row['w'][k]['mm'], row['x'], row['y'])
                if east_best[w] is None or c[0] < east_best[w][0]:
                    east_best[w] = c
    rec['east_best'] = {'%.2f' % (w / 1e6): (None if east_best[w] is None else
                        {'mm': east_best[w][0], 'x_mm': round(east_best[w][1] / 1e6, 2),
                         'y_mm': round(east_best[w][2] / 1e6, 2)}) for w in (W150, W120)}

    json.dump(rec, open(out, 'w'), indent=1)
    print('=' * 72)
    print('BEST any-region  1.50: %s   1.20: %s' % (rec['best']['1.50'], rec['best']['1.20']))
    print('BEST east (long) 1.50: %s   1.20: %s' % (rec['east_best']['1.50'], rec['east_best']['1.20']))
    print('wrote %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
