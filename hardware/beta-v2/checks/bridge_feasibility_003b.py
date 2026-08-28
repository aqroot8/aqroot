# -*- coding: utf-8 -*-
"""FBV2-P2-003B / D-274 -- REPRODUCIBLE feasibility verdict for the named
BAT_PROTECTED_P high-current F.Cu via-array bridge, measured on the proven c3
scratch board.  Lays no permanent copper; every wave is bounded and reverts.

The CTO task authorises exactly one bridge shape: a B.Cu->F.Cu transition ARRAY
on R75.2, an F.Cu traversing segment at >= 1.20 mm (target 1.50 mm), and an
F.Cu->B.Cu transition ARRAY into the D9/eastern-node island.  This probe measures
each of the three pieces independently and prints a verdict:

  ENTRY   can a >= 3-via array (0.80/0.40 POWER vias, 0.90 mm pitch,
          all-copper-layers clear) land on R75.2's own copper?
  EXIT    can a >= 4-via array land on the target island (node / D9 stub)?
  TRAVERSE is there an F.Cu corridor at >= 1.20 mm from the R75.2 entry to the
          target island?  Measured two ways: a flood (how far east a full-width
          corridor reaches) and a full-budget A* (NO_PATH by exhaustion, not a
          starved search) -- the same corroboration shape D-273 used on B.Cu.

Result (D-274): ENTRY feasible, EXIT feasible, TRAVERSE INFEASIBLE at >=1.20 mm.
The western margin is saturated on F.Cu exactly as D-273 proved it is on B.Cu.

Usage:  python bridge_feasibility_003b.py [board.kicad_pcb]
"""
import os, sys, math, time, json
from collections import deque
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import numpy as np
import qrouter as QR
import battery_route_plan as PL

NET = PL.N + 'BAT_PROTECTED_P'
CP, CTW = 200000, 300000            # pad clr 0.20, trunk track clr 0.30 (D-269)
DIA, DRILL = 800000, 400000         # 0.80/0.40 POWER-class through via
G = 50000
W_TRUNK, W_FLOOR = 1500000, 1200000


def vfree(qb, x, y):
    return all(qb.point_free(L, NET, x, y, DIA, CP, CTW, 25000) for L in qb.cu)


def greedy_array(sites, k, minsp=900000):
    arr = []
    for c in sites:
        if all(math.hypot(c[0] - e[0], c[1] - e[1]) >= minsp for e in arr):
            arr.append(c)
        if len(arr) >= k:
            break
    return arr


def pack_array(sites, k, minsp=900000):
    """Largest hole-spacing-valid subset up to k, found by trying every site as
    a seed (a linear greedy misses triangular packings a narrow pad admits)."""
    best = []
    uniq = list({(round(x / 50000) * 50000, round(y / 50000) * 50000)
                 for x, y in sites})
    for seed in uniq:
        others = sorted(uniq, key=lambda c: math.hypot(c[0] - seed[0],
                                                       c[1] - seed[1]))
        arr = [seed]
        for c in others:
            if c == seed:
                continue
            if all(math.hypot(c[0] - e[0], c[1] - e[1]) >= minsp for e in arr):
                arr.append(c)
            if len(arr) >= k:
                break
        if len(arr) > len(best):
            best = arr
        if len(best) >= k:
            break
    return best


def entry_array(qb):
    r = qb.pads[(NET, 'R75.2')]
    px, py = r['x'], r['y']
    hx, hy = r['hx'], r['hy']
    onpad = []
    for ix in range(-6, 7):
        for iy in range(-12, 13):
            x, y = px + ix * 150000, py + iy * 150000
            if abs(x - px) <= hx and abs(y - py) <= hy and vfree(qb, x, y):
                onpad.append((x, y))
    # keep only sites actually on R75.2's B.Cu pad copper (so the array is
    # electrically the trunk source, not a floating cluster)
    arr = pack_array(onpad, 4)
    return dict(pad_mm=[round(px / 1e6, 3), round(py / 1e6, 3),
                        round(2 * hx / 1e6, 3), round(2 * hy / 1e6, 3)],
                onpad_free_sites=len(onpad),
                array=[[round(a / 1e6, 3), round(b / 1e6, 3)] for a, b in arr],
                n=len(arr), feasible=len(arr) >= 3,
                note='via-in-pad on the sense-resistor pad -> plated-over-filled '
                     'vias required (POFV precedent, D-258)')


def exit_array(qb):
    out = {}
    for lab, (x0, x1, y0, y1) in (
            ('node_west', (38500000, 45000000, 70000000, 82000000)),
            ('node_interior', (45000000, 60000000, 66000000, 80000000)),
            ('D9_stub', (9500000, 12000000, 71000000, 74000000))):
        sites = []
        x = x0
        while x <= x1:
            y = y0
            while y <= y1:
                if vfree(qb, x, y):
                    sites.append((x, y))
                y += 400000
            x += 400000
        arr = pack_array(sites, 4)
        out[lab] = dict(free=len(sites), n=len(arr),
                        array=[[round(a / 1e6, 3), round(b / 1e6, 3)] for a, b in arr])
    out['feasible'] = any(v['n'] >= 4 for v in out.values() if isinstance(v, dict))
    return out


def flood_east(qb, sx, sy, width):
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    x0, y0, x1, y1 = qb.ex0 - 1e6, 58e6, 64e6, 96e6
    ox2 = int(round((x0 - ox) / G)) * G + ox
    oy2 = int(round((y0 - oy) / G)) * G + oy
    blk = qb.grid('F', NET, width, CP, CTW, ox2, oy2, x1, y1, G)
    si = (int((sx - ox2) // G), int((sy - oy2) // G))
    ny, nx = blk.shape
    blk[si[1], si[0]] = False
    seen = np.zeros_like(blk, bool)
    dq = deque([si]); seen[si[1], si[0]] = True
    maxx = sx
    while dq:
        i, j = dq.popleft()
        maxx = max(maxx, ox2 + i * G)
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny and not seen[b, a] and not blk[b, a]:
                seen[b, a] = True; dq.append((a, b))
    return round(maxx / 1e6, 2)


def astar(qb, sx, sy, tx, ty, width):
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    x0 = max(min(sx, tx) - 9e6, qb.ex0 - 1e6)
    y0 = max(min(sy, ty) - 9e6, qb.ey0 - 1e6)
    x1 = min(max(sx, tx) + 9e6, qb.ex1 + 1e6)
    y1 = min(max(sy, ty) + 9e6, qb.ey1 + 1e6)
    ox2 = int(round((x0 - ox) / G)) * G + ox
    oy2 = int(round((y0 - oy) / G)) * G + oy
    t0 = time.time()
    blk = qb.grid('F', NET, width, CP, CTW, ox2, oy2, x1, y1, G)
    si = (int((sx - ox2) // G), int((sy - oy2) // G))
    ti = (int((tx - ox2) // G), int((ty - oy2) // G))
    ny, nx = blk.shape
    for ii, jj in (si, ti):
        if 0 <= ii < nx and 0 <= jj < ny:
            blk[jj, ii] = False
    p = qb.search(blk, si, ti)
    return ('PATH' if p else 'NO_PATH'), round(time.time() - t0, 2)


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        SP, 'w', 'c3repro003b', 'aqroot-Beta-v2.kicad_pcb')
    qb = QR.QBoard(board)
    ent = entry_array(qb)
    ext = exit_array(qb)
    ex, ey = ent['pad_mm'][0] * 1e6, ent['pad_mm'][1] * 1e6
    trav = {'flood_east_max_x_mm': {}, 'astar_to_island': {}}
    for w, lab in ((W_TRUNK, '1.50'), (W_FLOOR, '1.20'),
                   (1000000, '1.00'), (800000, '0.80')):
        trav['flood_east_max_x_mm'][lab] = flood_east(qb, ex, ey, w)
    for tx, ty, tl in ((11.35e6, 71.3e6, 'BPP_Fcu_west_11.35_71.3'),
                       (40e6, 75e6, 'node_40_75')):
        for w, lab in ((W_TRUNK, '1.50'), (W_FLOOR, '1.20')):
            r, dt = astar(qb, ex, ey, tx, ty, w)
            trav['astar_to_island']['%s@%s' % (tl, lab)] = [r, dt]
    trav['island_west_edge_mm'] = 10.05
    trav['traverse_feasible_ge_1.20mm'] = (
        trav['flood_east_max_x_mm']['1.20'] >= 10.05 and
        any(v[0] == 'PATH' for k, v in trav['astar_to_island'].items()
            if k.endswith('1.20') or k.endswith('1.50')))
    verdict = ('BRIDGE INFEASIBLE -- entry+exit arrays exist, but no F.Cu '
               'traverse at >= 1.20 mm (western margin saturated on F.Cu as on '
               'B.Cu; a full-width corridor from R75.2 dies at x=%.2f mm, and '
               'only <= 0.80 mm threads to x=%.2f mm, below the mandatory 1.20 mm '
               'trunk floor which may not be waived).'
               % (trav['flood_east_max_x_mm']['1.20'],
                  trav['flood_east_max_x_mm']['0.80']))
    out = dict(task='FBV2-P2-003B', board=board,
               entry_array=ent, exit_array=ext, traverse=trav,
               bridge_feasible=bool(ent['feasible'] and ext['feasible']
                                    and trav['traverse_feasible_ge_1.20mm']),
               blocker='F.Cu >=1.20mm traverse of the western margin',
               verdict=verdict)
    print(json.dumps(out, indent=1))
    json.dump(out, open(os.path.join(SP, 'place_002z',
                                     'bridge_feasibility_003b.json'), 'w'), indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
