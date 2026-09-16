#!/usr/bin/env python3
"""How WIDE can one net's trunk get between two points, and what pinches it?

A `NO_PATH` says a corridor is not there at ONE width.  A power rail asks the
other question: *what is the widest conductor that fits at all, and which
object is the bottleneck?*  This rasterises every foreign copper object on one
layer, takes a Euclidean distance transform, and runs a MAXIMIN (bottleneck
shortest path) search, so the answer is a width and a NAMED blocker, not a
verdict.

    screen_widest_corridor.py --board B --layer F.Cu --net NET \
        --from X,Y --to X,Y [--clearance 0.25] [--grid 0.05] [-o OUT.json]
"""
import argparse, heapq, json, math, sys
import numpy as np
import pcbnew

CU = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu,
      "In3.Cu": pcbnew.In3_Cu, "In4.Cu": pcbnew.In4_Cu, "B.Cu": pcbnew.B_Cu}


def obstacles(b, layer, net, free=()):
    """(kind, label, sampled points, own radius) for every FOREIGN object."""
    out = []
    for t in b.GetTracks():
        if t.GetNetname() == net or t.GetNetname() in free:
            continue
        s, e = t.GetStart(), t.GetEnd()
        if t.Type() == pcbnew.PCB_VIA_T:
            if not t.IsOnLayer(layer):
                continue
            out.append(("via", t.GetNetname(), [(s.x/1e6, s.y/1e6)], t.GetWidth(layer)/2e6))
        else:
            if t.GetLayer() != layer:
                continue
            n = max(2, int(math.dist((s.x, s.y), (e.x, e.y)) / 50000) + 1)
            pts = [((s.x + (e.x-s.x)*i/(n-1))/1e6, (s.y + (e.y-s.y)*i/(n-1))/1e6)
                   for i in range(n)]
            out.append(("trk", t.GetNetname(), pts, t.GetWidth()/2e6))
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            if pd.GetNetname() == net or pd.GetNetname() in free or not pd.IsOnLayer(layer):
                continue
            p, sz = pd.GetPosition(), pd.GetSize()
            out.append(("pad", f"{fp.GetReference()}.{pd.GetNumber()}",
                        [(p.x/1e6, p.y/1e6)], max(sz.x, sz.y)/2e6))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--layer", required=True, choices=sorted(CU))
    ap.add_argument("--net", required=True)
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--clearance", type=float, default=0.25)
    ap.add_argument("--grid", type=float, default=0.05)
    ap.add_argument("--margin", type=float, default=3.0)
    ap.add_argument("--free", action="append", default=[],
                    help="treat this net as REMOVABLE -- what the corridor would be "
                         "if it were re-laid elsewhere. Repeatable")
    ap.add_argument("-o", dest="out")
    a = ap.parse_args()
    sx, sy = [float(v) for v in a.src.split(",")]
    dx, dy = [float(v) for v in a.dst.split(",")]
    x0, x1 = min(sx, dx) - a.margin, max(sx, dx) + a.margin
    y0, y1 = min(sy, dy) - a.margin, max(sy, dy) + a.margin
    b = pcbnew.LoadBoard(a.board)
    layer = CU[a.layer]
    g = a.grid
    nx, ny = int((x1-x0)/g)+1, int((y1-y0)/g)+1
    # clearance-to-copper field: distance from each cell to the nearest obstacle
    big = 1e6
    D = np.full((ny, nx), big, dtype=np.float32)
    OWN = np.empty((ny, nx), dtype=object)
    xs = x0 + np.arange(nx)*g
    ys = y0 + np.arange(ny)*g
    XX, YY = np.meshgrid(xs, ys)
    obs = obstacles(b, layer, a.net, set(a.free))
    for kind, lbl, pts, r in obs:
        px = np.array([p[0] for p in pts]); py = np.array([p[1] for p in pts])
        if px.max() < x0-5 or px.min() > x1+5 or py.max() < y0-5 or py.min() > y1+5:
            continue
        d = np.full((ny, nx), big, dtype=np.float32)
        for qx, qy in zip(px, py):
            np.minimum(d, np.hypot(XX-qx, YY-qy).astype(np.float32) - r, out=d)
        m = d < D
        D[m] = d[m]
        for j, i in zip(*np.nonzero(m)):
            OWN[j, i] = (kind, lbl)
    # usable half-width at each cell
    W = np.maximum(0.0, D - a.clearance) * 2.0        # full track width that fits
    def cell(x, y):
        return (int(round((y-y0)/g)), int(round((x-x0)/g)))
    s = cell(sx, sy); t = cell(dx, dy)
    # MAXIMIN dijkstra: maximise the minimum W along the path
    best = np.full((ny, nx), -1.0, dtype=np.float32)
    prev = {}
    best[s] = W[s]
    pq = [(-float(W[s]), s)]
    while pq:
        negw, u = heapq.heappop(pq)
        w = -negw
        if w < best[u]:
            continue
        if u == t:
            break
        uj, ui = u
        for dj, di in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            vj, vi = uj+dj, ui+di
            if not (0 <= vj < ny and 0 <= vi < nx):
                continue
            nw = min(w, float(W[vj, vi]))
            if nw > best[vj, vi]:
                best[vj, vi] = nw
                prev[(vj, vi)] = u
                heapq.heappush(pq, (-nw, (vj, vi)))
    width = float(best[t])
    path, u = [], t
    while u in prev or u == s:
        path.append((round(x0+u[1]*g, 3), round(y0+u[0]*g, 3)))
        if u == s:
            break
        u = prev[u]
    path.reverse()
    pinch, pinch_xy, pinch_by = width, None, None
    for (px, py) in path:
        j, i = cell(px, py)
        if abs(float(W[j, i]) - width) < g:
            pinch_xy = [px, py]
            pinch_by = OWN[j, i]
            break
    rep = dict(schema=1, freed_nets=a.free, board=a.board, layer=a.layer, net=a.net,
               clearance_mm=a.clearance, grid_mm=g,
               src=[sx, sy], dst=[dx, dy],
               widest_trunk_mm=round(width, 4),
               pinch_at=pinch_xy,
               pinch_by=(list(pinch_by) if pinch_by else None),
               path_mm=path if len(path) < 400 else path[::max(1, len(path)//200)])
    print(json.dumps({k: v for k, v in rep.items() if k != "path_mm"}, indent=1))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
