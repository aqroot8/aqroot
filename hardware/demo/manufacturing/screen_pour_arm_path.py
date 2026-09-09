#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: WHICH COPPER DOES A POUR ACTUALLY USE TO REACH A LAND?

Every pour instrument on this board answers a COUNT.  `routing_ledger.py` says
how many islands a net is in, `screen_pour_cut_blame.py` says which foreign
objects, if removed, would make it fewer, and `screen_pour_neck_fragility.py`
says how thin the thinnest place is.  None of them says WHERE the conductor
runs, and on a pour that is the whole question: a rail delivered by a plane is
delivered along ONE path, and until that path is drawn a reader cannot tell
whether a proposed track crosses it, whether a barrel site is beside it or on
it, or which PART bounds it.

D-659 priced `BQ25185_SYS`'s `U11.1` cut at three objects and then had to
reason about the geometry in prose.  This screen draws it instead.

METHOD.  KiCad's own filled polygons ARE the conductor: each outline of a
zone's `SHAPE_POLY_SET`, minus its holes, is one connected island.  The island
holding `--from` is rasterised at `--grid` and a breadth-first search is run
from that land to `--to`.  BFS on a uniform lattice returns a SHORTEST path, so
the polyline is a witness that the two lands are one piece and a map of roughly
where the metal goes -- it is not a claim that the current density follows it.

Then the path is PRICED.  At each station the free width of the island is
measured ACROSS the path (perpendicular to the local direction, both ways until
the raster leaves the island), the narrowest station is the `pinch`, and the
two nearest FOREIGN objects on either side of the pinch are NAMED -- because a
channel is bounded by parts, and "the pour is thin here" is only actionable
once a reader knows whose pad, track or barrel makes it thin.

    python3 screen_pour_arm_path.py NET --from REF.PIN --to REF.PIN \
        [--board B] [--grid 0.05] [--search-mm 2.0] -o OUT.json

NOTHING IS WRITTEN.  The board is opened once, read, and its sha256 is
re-checked at exit.
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTHORITY = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
M = 1e6


def _ring(o):
    return np.array([(o.CPoint(k).x / M, o.CPoint(k).y / M)
                     for k in range(o.PointCount())])


def _inside(ring, X, Y):
    """even-odd point-in-polygon, vectorised over a raster"""
    x, y = ring[:, 0], ring[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    res = np.zeros(X.shape, bool)
    for k in range(len(x)):
        a, b, c, d = x[k], y[k], x2[k], y2[k]
        if b == d:
            continue
        cond = (b > Y) != (d > Y)
        xint = (c - a) * (Y - b) / (d - b) + a
        res ^= cond & (X < xint)
    return res


def _pt_in(ring, px, py):
    return bool(_inside(ring, np.array([px]), np.array([py]))[0])


def islands(board, net):
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net:
            continue
        for lid in z.GetLayerSet().Seq():
            fps = z.GetFilledPolysList(lid)
            for i in range(fps.OutlineCount()):
                out.append(dict(layer=board.GetLayerName(lid),
                                outer=_ring(fps.Outline(i)),
                                holes=[_ring(fps.Hole(i, h))
                                       for h in range(fps.HoleCount(i))],
                                zone=z.m_Uuid.AsString()))
    return out


def holds(isl, x, y, slack=0.35, step=0.05):
    n = int(slack / step)
    for dj in range(-n, n + 1):
        for di in range(-n, n + 1):
            px, py = x + di * step, y + dj * step
            if not _pt_in(isl["outer"], px, py):
                continue
            if any(_pt_in(h, px, py) for h in isl["holes"]):
                continue
            return True
    return False


def foreign_near(board, net, layer, x, y, r):
    """nearest foreign copper objects to a point, on one layer"""
    import pcbnew
    lid = board.GetLayerID(layer)
    hits = []
    for fp in board.Footprints():
        for pd in fp.Pads():
            if pd.GetNetname() == net or not pd.IsOnLayer(lid):
                continue
            d = pd.GetEffectiveShape(lid).Distance(
                pcbnew.VECTOR2I(int(x * M), int(y * M))) / M
            if d <= r:
                hits.append(dict(kind="pad", land="%s.%s" % (fp.GetReference(),
                                                             pd.GetNumber()),
                                 net=pd.GetNetname(), mm=round(d, 4)))
    for t in board.GetTracks():
        if t.GetNetname() == net:
            continue
        via = t.GetClass() == "PCB_VIA"
        if not via and t.GetLayer() != lid:
            continue
        if via and not t.IsOnLayer(lid):
            continue
        d = t.GetEffectiveShape(lid).Distance(
            pcbnew.VECTOR2I(int(x * M), int(y * M))) / M
        if d <= r:
            hits.append(dict(kind="via" if via else "track", land=None,
                             net=t.GetNetname(), mm=round(d, 4)))
    hits.sort(key=lambda h: h["mm"])
    return hits[:4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("net")
    ap.add_argument("--board", type=Path, default=AUTHORITY)
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--grid", type=float, default=0.05,
                    help="raster pitch in mm")
    ap.add_argument("--search-mm", type=float, default=2.0,
                    help="how far to look for the objects that bound a pinch")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    for suffix in (".kicad_dru", ".kicad_pro"):
        if not a.board.with_suffix(suffix).is_file():
            raise SystemExit("--board %s has no %s beside it"
                             % (a.board, suffix))
    before = hashlib.sha256(a.board.read_bytes()).hexdigest()

    import pcbnew
    b = pcbnew.LoadBoard(str(a.board))
    pads = {}
    for fp in b.Footprints():
        for pd in fp.Pads():
            if pd.GetNetname() == a.net:
                pads["%s.%s" % (fp.GetReference(), pd.GetNumber())] = (
                    pd.GetPosition().x / M, pd.GetPosition().y / M)
    for ref in (a.src, a.dst):
        if ref not in pads:
            raise SystemExit("%s is not a pad of %s" % (ref, a.net))
    s, t = pads[a.src], pads[a.dst]

    isl = None
    for cand in islands(b, a.net):
        if holds(cand, *s):
            isl = cand
            break
    doc = dict(schema=1, board=str(a.board), board_sha256=before,
               board_is_authority=(a.board.resolve() == AUTHORITY.resolve()),
               net=a.net, src=a.src, dst=a.dst, grid_mm=a.grid)
    if isl is None:
        doc.update(verdict="NO_ISLAND_HOLDS_SRC")
    elif not holds(isl, *t):
        doc.update(verdict="NOT_ONE_ISLAND", layer=isl["layer"],
                   zone=isl["zone"])
    else:
        doc.update(_trace(b, a, isl, s, t))

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc["authoritative_unchanged"] = (before == after)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print("%s -> %s  %s" % (a.src, a.dst, doc.get("verdict")))
    if doc.get("pinch"):
        p = doc["pinch"]
        print("  path %.3f mm, pinch %.3f mm at (%.3f, %.3f) on %s"
              % (doc["path_mm"], p["width_mm"], p["at"][0], p["at"][1],
                 doc["layer"]))
        for side in ("side_a", "side_b"):
            for h in p[side][:1]:
                print("    %-5s %-6s %-28s %.4f mm"
                      % (side[-1], h["kind"], h["land"] or h["net"], h["mm"]))
    return 0


def _trace(b, a, isl, s, t):
    G = a.grid
    outer, holes = isl["outer"], isl["holes"]
    x0, y0 = outer[:, 0].min(), outer[:, 1].min()
    x1, y1 = outer[:, 0].max(), outer[:, 1].max()
    xs = np.arange(x0, x1 + G, G)
    ys = np.arange(y0, y1 + G, G)
    X, Y = np.meshgrid(xs, ys)
    grid = _inside(outer, X, Y)
    for h in holes:
        grid &= ~_inside(h, X, Y)
    ny, nx = grid.shape

    def cell(p):
        return (int(round((p[1] - y0) / G)), int(round((p[0] - x0) / G)))

    def nearest(c):
        q, seen = collections.deque([c]), {c}
        while q:
            j, i = q.popleft()
            if 0 <= j < ny and 0 <= i < nx and grid[j, i]:
                return (j, i)
            for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (j + dj, i + di)
                if n not in seen and abs(n[0] - c[0]) < 60 \
                        and abs(n[1] - c[1]) < 60:
                    seen.add(n)
                    q.append(n)
        return None

    sc, tc = nearest(cell(s)), nearest(cell(t))
    prev = {sc: None}
    q = collections.deque([sc])
    while q:
        cur = q.popleft()
        if cur == tc:
            break
        j, i = cur
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (j + dj, i + di)
            if 0 <= n[0] < ny and 0 <= n[1] < nx and grid[n] and n not in prev:
                prev[n] = cur
                q.append(n)
    if tc not in prev:
        return dict(verdict="NO_RASTER_PATH", layer=isl["layer"],
                    note="the lands share an island but not at this --grid")
    path = []
    c = tc
    while c:
        path.append(c)
        c = prev[c]
    path.reverse()

    def width(k):
        """free width of the island across the path at station k"""
        j, i = path[k]
        k2 = min(len(path) - 1, k + 3)
        k1 = max(0, k - 3)
        dj = path[k2][0] - path[k1][0]
        di = path[k2][1] - path[k1][1]
        n = (di * di + dj * dj) ** 0.5 or 1.0
        # normal is (-dj, di) rotated into (row, col) space
        nj, ni = di / n, -dj / n
        w = 0.0
        for sgn in (1, -1):
            for step in range(1, 400):
                jj = int(round(j + sgn * nj * step))
                ii = int(round(i + sgn * ni * step))
                if not (0 <= jj < ny and 0 <= ii < nx) or not grid[jj, ii]:
                    break
                w += 1
        return (w + 1) * G

    ws = [width(k) for k in range(len(path))]
    kmin = int(np.argmin(ws))
    px = x0 + path[kmin][1] * G
    py = y0 + path[kmin][0] * G
    # name the two sides at the pinch
    j, i = path[kmin]
    k2 = min(len(path) - 1, kmin + 3)
    k1 = max(0, kmin - 3)
    dj = path[k2][0] - path[k1][0]
    di = path[k2][1] - path[k1][1]
    n = (di * di + dj * dj) ** 0.5 or 1.0
    nj, ni = di / n, -dj / n
    sides = {}
    for tag, sgn in (("side_a", 1), ("side_b", -1)):
        qx = px + sgn * ni * G * (ws[kmin] / G / 2 + 2)
        qy = py + sgn * nj * G * (ws[kmin] / G / 2 + 2)
        sides[tag] = foreign_near(b, a.net, isl["layer"], qx, qy, a.search_mm)
    poly = [[round(x0 + c[1] * G, 4), round(y0 + c[0] * G, 4)]
            for c in path[::max(1, len(path) // 200)]]
    return dict(verdict="ONE_ISLAND", layer=isl["layer"], zone=isl["zone"],
                path_mm=round(len(path) * G, 3), stations=len(path),
                polyline=poly,
                profile=[[round(x0 + path[k][1] * G, 3),
                          round(y0 + path[k][0] * G, 3), round(ws[k], 3)]
                         for k in range(0, len(path), max(1, len(path) // 40))],
                pinch=dict(at=[round(px, 4), round(py, 4)],
                           width_mm=round(ws[kmin], 4),
                           station=kmin, **sides))


if __name__ == "__main__":
    raise SystemExit(main())
