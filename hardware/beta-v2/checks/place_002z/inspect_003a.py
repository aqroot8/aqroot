# -*- coding: utf-8 -*-
"""FBV2-P2-003A / D-273 -- READ-ONLY geometry inspection (no routing).

Loads the parent's proven c3 scratch board and reports the facts a bounded
long-corridor probe needs: board edges, the R75.2 source and D9 reservation
copper, and the far BAT_PROTECTED_P net copper (the join-target set), clustered
so distinct far regions are visible.  Lays NO copper and runs NO wave.
"""
import os, sys, math, json, collections
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SP)
import qrouter as QR

BOARD = os.path.join(SP, 'w', 'c3repro003a_parent', 'aqroot-Beta-v2.kicad_pcb')
N = 'Net-(BAT_'   # net-name prefix guard, real prefix resolved from PL
import battery_route_plan as PL
NET = PL.N + 'BAT_PROTECTED_P'


def segs_of_net(qb, netname, layer='B.Cu'):
    LID = qb.b.GetLayerID(layer)
    out = []
    for t in qb.b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != LID:
            continue
        if t.GetNetname() != netname:
            continue
        s, e = t.GetStart(), t.GetEnd()
        out.append((s.x, s.y, e.x, e.y, t.GetWidth()))
    return out


def cluster(segs, gap=2000000):
    """Union-find segments whose endpoints are within `gap`; return clusters."""
    pts = []
    for i, (x0, y0, x1, y1, w) in enumerate(segs):
        pts.append((i, x0, y0)); pts.append((i, x1, y1))
    parent = list(range(len(segs)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def uni(a, b):
        parent[find(a)] = find(b)
    for a in range(len(pts)):
        ia, xa, ya = pts[a]
        for b in range(a + 1, len(pts)):
            ib, xb, yb = pts[b]
            if ia == ib:
                continue
            if math.hypot(xa - xb, ya - yb) <= gap:
                uni(ia, ib)
    groups = collections.defaultdict(list)
    for i in range(len(segs)):
        groups[find(i)].append(i)
    return list(groups.values())


def main():
    qb = QR.QBoard(BOARD)
    print('board  %s' % BOARD)
    print('edges  x %.3f .. %.3f   y %.3f .. %.3f  (mm, copper->edge clr applied)'
          % (qb.ex0 / 1e6, qb.ex1 / 1e6, qb.ey0 / 1e6, qb.ey1 / 1e6))
    for ref in ('R75.2', 'D9.1', 'U11.2', 'U14.2', 'C25.1', 'C36.1', 'C58.1'):
        p = qb.pads.get((NET, ref))
        if p:
            print('pad    %-8s (%.3f, %.3f)' % (ref, p['x'] / 1e6, p['y'] / 1e6))

    segs = segs_of_net(qb, NET, 'B.Cu')
    xs = [s[0] for s in segs] + [s[2] for s in segs]
    ys = [s[1] for s in segs] + [s[3] for s in segs]
    print('\nBAT_PROTECTED_P B.Cu: %d segs   x %.2f..%.2f  y %.2f..%.2f mm'
          % (len(segs), min(xs) / 1e6, max(xs) / 1e6, min(ys) / 1e6, max(ys) / 1e6))

    cl = cluster(segs)
    cl.sort(key=lambda g: -sum(math.hypot(segs[i][2] - segs[i][0],
                                          segs[i][3] - segs[i][1]) for i in g))
    print('\n%d B.Cu cluster(s) (>=0.5mm shown), largest first:' % len(cl))
    rows = []
    for g in cl:
        gx = [segs[i][0] for i in g] + [segs[i][2] for i in g]
        gy = [segs[i][1] for i in g] + [segs[i][3] for i in g]
        L = sum(math.hypot(segs[i][2] - segs[i][0], segs[i][3] - segs[i][1]) for i in g)
        cx, cy = sum(gx) / len(gx), sum(gy) / len(gy)
        # nearest endpoint of this cluster to R75.2
        rows.append((L, len(g), min(gx), max(gx), min(gy), max(gy), cx, cy))
    r75 = qb.pads[(NET, 'R75.2')]
    for (L, n, x0, x1, y0, y1, cx, cy) in rows:
        if L < 500000:
            continue
        # closest point on cluster bbox to R75.2 (rough)
        print('  L=%6.2fmm  n=%2d  x %.2f..%.2f  y %.2f..%.2f  centroid(%.2f,%.2f)'
              % (L / 1e6, n, x0 / 1e6, x1 / 1e6, y0 / 1e6, y1 / 1e6,
                 cx / 1e6, cy / 1e6))

    # the reservation stub off D9.1 (short, near west margin)
    d9 = qb.pads.get((NET, 'D9.1'))
    if d9:
        print('\nreservation stub candidates (BPP B.Cu within 12mm of D9.1):')
        for (x0, y0, x1, y1, w) in segs:
            if (math.hypot(x0 - d9['x'], y0 - d9['y']) < 12000000 or
                    math.hypot(x1 - d9['x'], y1 - d9['y']) < 12000000):
                print('    (%.3f,%.3f)->(%.3f,%.3f) w=%.2f'
                      % (x0 / 1e6, y0 / 1e6, x1 / 1e6, y1 / 1e6, w / 1e6))

    # free-lane sniff: obstacle copper x-extent on B.Cu (all nets) to see margins
    LID = qb.b.GetLayerID('B.Cu')
    allx = []
    for t in qb.b.GetTracks():
        if t.GetClass() == 'PCB_TRACK' and t.GetLayer() == LID:
            allx.append(t.GetStart().x); allx.append(t.GetEnd().x)
    if allx:
        print('\nall-net B.Cu x-extent %.2f..%.2f mm' % (min(allx) / 1e6, max(allx) / 1e6))
    return 0


if __name__ == '__main__':
    sys.exit(main())
