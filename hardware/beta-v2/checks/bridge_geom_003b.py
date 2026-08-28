# -*- coding: utf-8 -*-
"""FBV2-P2-003B -- decisive GEOMETRY feasibility probe for the named
BAT_PROTECTED_P F.Cu high-current via-array bridge.  Reads the reproduced c3
scratch board; lays copper only to measure and reverts it.

The bridge, if it exists, is three bounded pieces:
   (1) a B.Cu -> F.Cu via ARRAY on the WEST BAT_PROTECTED_P island (R75.2 side),
   (2) an F.Cu traversing run at >= 1.20 mm (target 1.50 mm),
   (3) an F.Cu -> B.Cu via ARRAY into the EAST node copper (D9.1/U11.2 side).

This probe answers, with real obstacle-aware searches on the proven board:
   Q1  Is there a WEST array site: a 4-via cluster free on ALL copper layers,
       reachable on B.Cu at trunk width from the west island's own copper?
   Q2  Is there an EAST array site on the node the same way?
   Q3  Is there an F.Cu corridor at 1.20 / 1.50 mm between a west and an east
       site?
A NONE on Q1 corroborates D-273's in-plane saturation; a NONE on Q3 is the
F.Cu-corridor blocker; all-yes selects a real candidate to route.

Usage:  python bridge_geom_003b.py <board.kicad_pcb> [map|west|east|corridor]
"""
import os, sys, math, json, signal, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import qrouter as QR
import battery_route_plan as PL

NET = PL.N + 'BAT_PROTECTED_P'
CP, CT_W = 200000, 300000          # pad clr 0.20, trunk track clr 0.30 (D-269)
VIA_DIA, VIA_DRILL = 800000, 400000
W_TRUNK, W_FLOOR = 1500000, 1200000
PITCH = 1000000                    # via-to-via pitch in the array (1.0 mm)
# 2x2 array offsets (nm) about the centre
ARRAY = [(-PITCH // 2, -PITCH // 2), (PITCH // 2, -PITCH // 2),
         (-PITCH // 2, PITCH // 2), (PITCH // 2, PITCH // 2)]


class TimeOut(Exception):
    pass


def _alarm(s, f):
    raise TimeOut()


def bounded(fn, secs=25):
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(secs)
    try:
        return fn()
    except TimeOut:
        return 'TIMEOUT'
    finally:
        signal.alarm(0)


def segs_of(qb, layer):
    LID = qb.b.GetLayerID(layer)
    out = []
    for t in qb.b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != LID:
            continue
        if t.GetNetname() != NET:
            continue
        s, e = t.GetStart(), t.GetEnd()
        out.append((s.x, s.y, e.x, e.y, t.GetWidth()))
    return out


def cluster(segs, gap=1500000):
    pts = []
    for i, (x0, y0, x1, y1, w) in enumerate(segs):
        pts += [(i, x0, y0), (i, x1, y1)]
    par = list(range(len(segs)))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for a in range(len(pts)):
        ia, xa, ya = pts[a]
        for b in range(a + 1, len(pts)):
            ib, xb, yb = pts[b]
            if ia != ib and math.hypot(xa - xb, ya - yb) <= gap:
                par[find(ia)] = find(ib)
    g = collections.defaultdict(list)
    for i in range(len(segs)):
        g[find(i)].append(i)
    return list(g.values())


def bbox(segs, idx):
    xs = [segs[i][0] for i in idx] + [segs[i][2] for i in idx]
    ys = [segs[i][1] for i in idx] + [segs[i][3] for i in idx]
    return min(xs), min(ys), max(xs), max(ys)


def array_free(qb, cx, cy):
    """True if a 4-via cluster centred at (cx,cy) is clear on EVERY copper
    layer for this net (a through via is copper on all six)."""
    for (dx, dy) in ARRAY:
        x, y = cx + dx, cy + dy
        for L in qb.cu:
            if not qb.point_free(L, NET, x, y, VIA_DIA, CP, CT_W, 25000):
                return False
    return True


def reachable_bcu(qb, fromxy, toxy, width, win=7000000, secs=25):
    """A real B.Cu obstacle-aware search from `fromxy` to `toxy` at `width`."""
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    x0 = min(fromxy[0], toxy[0]) - win; x1 = max(fromxy[0], toxy[0]) + win
    y0 = min(fromxy[1], toxy[1]) - win; y1 = max(fromxy[1], toxy[1]) + win
    x0 = max(x0, qb.ex0 - 1000000); y0 = max(y0, qb.ey0 - 1000000)
    x1 = min(x1, qb.ex1 + 1000000); y1 = min(y1, qb.ey1 + 1000000)
    G = 50000
    ox2 = int(round((x0 - ox) / G)) * G + ox
    oy2 = int(round((y0 - oy) / G)) * G + oy
    def go():
        blk = qb.grid('B', NET, width, CP, CT_W, ox2, oy2, x1, y1, G)
        si = ((fromxy[0] - ox2) // G, (fromxy[1] - oy2) // G)
        ti = ((toxy[0] - ox2) // G, (toxy[1] - oy2) // G)
        ny, nx = blk.shape
        for (ii, jj) in (si, ti):
            if 0 <= ii < nx and 0 <= jj < ny:
                blk[jj, ii] = False
        return qb.search(blk, si, ti)
    return bounded(go, secs)


def fcu_corridor(qb, fromxy, toxy, width, win=7000000, secs=60):
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    x0 = min(fromxy[0], toxy[0]) - win; x1 = max(fromxy[0], toxy[0]) + win
    y0 = min(fromxy[1], toxy[1]) - win; y1 = max(fromxy[1], toxy[1]) + win
    x0 = max(x0, qb.ex0 - 1000000); y0 = max(y0, qb.ey0 - 1000000)
    x1 = min(x1, qb.ex1 + 1000000); y1 = min(y1, qb.ey1 + 1000000)
    G = 50000
    ox2 = int(round((x0 - ox) / G)) * G + ox
    oy2 = int(round((y0 - oy) / G)) * G + oy
    def go():
        blk = qb.grid('F', NET, width, CP, CT_W, ox2, oy2, x1, y1, G)
        si = ((fromxy[0] - ox2) // G, (fromxy[1] - oy2) // G)
        ti = ((toxy[0] - ox2) // G, (toxy[1] - oy2) // G)
        ny, nx = blk.shape
        for (ii, jj) in (si, ti):
            if 0 <= ii < nx and 0 <= jj < ny:
                blk[jj, ii] = False
        p = qb.search(blk, si, ti)
        if p is None:
            return None
        pts = QR.simplify(p, ox2, oy2, G)
        L = sum(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
                for k in range(len(pts) - 1))
        return ('PATH', round(L / 1e6, 3), pts[0], pts[-1])
    return bounded(go, secs)


def scan_sites(qb, x0, x1, y0, y1, island_pts, step=500000, need_reach=True,
               max_sites=40):
    """Grid-scan for array sites: all-layers-free AND (optionally) reachable on
    B.Cu at the trunk floor from the island's own copper."""
    sites = []
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            if array_free(qb, x, y):
                reach = None
                if need_reach:
                    # try nearest island point first
                    ipts = sorted(island_pts,
                                  key=lambda p: math.hypot(p[0] - x, p[1] - y))[:4]
                    for ip in ipts:
                        r = reachable_bcu(qb, ip, (x, y), W_FLOOR, secs=15)
                        if r not in (None, 'TIMEOUT'):
                            reach = (round(ip[0] / 1e6, 3), round(ip[1] / 1e6, 3))
                            break
                    if reach is None:
                        y += step
                        continue
                sites.append((round(x / 1e6, 3), round(y / 1e6, 3), reach))
                if len(sites) >= max_sites:
                    return sites
            y += step
        x += step
    return sites


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        SP, 'w', 'c3repro003b', 'aqroot-Beta-v2.kicad_pcb')
    phase = sys.argv[2] if len(sys.argv) > 2 else 'map'
    qb = QR.QBoard(board)
    r75 = qb.pads[(NET, 'R75.2')]
    out = {'board': board, 'phase': phase, 'cu_layers': list(qb.cu),
           'edges_mm': [round(qb.ex0 / 1e6, 3), round(qb.ex1 / 1e6, 3),
                        round(qb.ey0 / 1e6, 3), round(qb.ey1 / 1e6, 3)]}

    bseg = segs_of(qb, 'B.Cu')
    fseg = segs_of(qb, 'F.Cu')
    bcl = cluster(bseg); fcl = cluster(fseg)
    bcl.sort(key=lambda idx: -sum(math.hypot(bseg[i][2] - bseg[i][0],
                                             bseg[i][3] - bseg[i][1]) for i in idx))
    # west island = cluster nearest R75.2 pad; east node = the longest cluster
    def near_r75(idx):
        return min(min(math.hypot(bseg[i][0] - r75['x'], bseg[i][1] - r75['y']),
                       math.hypot(bseg[i][2] - r75['x'], bseg[i][3] - r75['y']))
                   for i in idx)
    west = min(bcl, key=near_r75)
    east = max(bcl, key=lambda idx: sum(math.hypot(bseg[i][2] - bseg[i][0],
                                                   bseg[i][3] - bseg[i][1]) for i in idx))
    out['pads'] = {ref: [round(qb.pads[(NET, ref)]['x'] / 1e6, 3),
                         round(qb.pads[(NET, ref)]['y'] / 1e6, 3)]
                   for ref in ('R75.2', 'D9.1', 'U11.2', 'C25.1', 'C36.1', 'C58.1')
                   if (NET, ref) in qb.pads}
    out['west_island_bbox_mm'] = [round(v / 1e6, 3) for v in bbox(bseg, west)]
    out['east_node_bbox_mm'] = [round(v / 1e6, 3) for v in bbox(bseg, east)]
    out['n_bcu_clusters'] = len(bcl)
    out['fcu_bpp_clusters'] = [[round(v / 1e6, 3) for v in bbox(fseg, idx)]
                               for idx in fcl] if fseg else []

    west_pts = [(bseg[i][0], bseg[i][1]) for i in west] + \
               [(bseg[i][2], bseg[i][3]) for i in west]
    east_pts = [(bseg[i][0], bseg[i][1]) for i in east] + \
               [(bseg[i][2], bseg[i][3]) for i in east]

    if phase == 'map':
        print(json.dumps(out, indent=1))
        return 0

    if phase == 'west':
        wx0, wy0, wx1, wy1 = bbox(bseg, west)
        # scan the island and a 6 mm collar east/around it
        sites = scan_sites(qb, max(wx0 - 1000000, qb.ex0),
                           wx1 + 6000000, wy0 - 3000000, wy1 + 3000000,
                           west_pts, need_reach=True)
        out['west_sites'] = sites
        out['west_site_count'] = len(sites)

    elif phase == 'east':
        ex0, ey0, ex1, ey1 = bbox(bseg, east)
        sites = scan_sites(qb, ex0 - 3000000, min(ex0 + 12000000, qb.ex1),
                           ey0 - 2000000, ey1 + 2000000, east_pts,
                           need_reach=True, max_sites=25)
        out['east_sites'] = sites
        out['east_site_count'] = len(sites)

    elif phase == 'corridor':
        # west/east candidate centres from argv 3,4 as "x,y" or auto: pick the
        # west site closest to the node and the east site closest to west.
        w_arg = sys.argv[3] if len(sys.argv) > 3 else None
        e_arg = sys.argv[4] if len(sys.argv) > 4 else None
        if w_arg and e_arg:
            wc = tuple(int(float(v) * 1e6) for v in w_arg.split(','))
            ec = tuple(int(float(v) * 1e6) for v in e_arg.split(','))
        else:
            out['error'] = 'supply west "x,y" and east "x,y" centres'
            print(json.dumps(out, indent=1)); return 1
        res = {}
        for w, lab in ((W_TRUNK, '1.50'), (W_FLOOR, '1.20')):
            res[lab] = fcu_corridor(qb, wc, ec, w, secs=90)
        out['west_centre_mm'] = w_arg
        out['east_centre_mm'] = e_arg
        out['fcu_corridor'] = {k: (v if not isinstance(v, tuple) else list(v))
                               for k, v in res.items()}

    print(json.dumps(out, indent=1))
    op = os.path.join(SP, 'place_002z', 'bridge_geom_003b_%s.json' % phase)
    json.dump(out, open(op, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
