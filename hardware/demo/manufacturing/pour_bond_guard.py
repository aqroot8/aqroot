#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- POUR-BOND PROTECTION: keep foreign copper out of a bond neck.

D-582 and D-583 poured both outer layers, and D-584 measured what that costs:
a signal track laid on `F.Cu`/`B.Cu` is a SLOT through the pour that owns the
layer, KiCad re-pours around it, the pour splits, and every pad that was bonded
ACROSS the cut goes open.  Gate clause 4 refuses the whole run for one orphaned
pad, so after D-584 the screen reports ZERO `PROMOTABLE` nets left while SIX
nets -- `/I2C_SDA_INT`, `/I2C_SCL_INT`, `BTN_DOWN_N`, `EXT_SDA`, `/NFC_CS_N`,
`/ACC_5V_BOOST_EN`, together ~18 retained edges including the whole internal
I2C bus -- route cleanly and are refused for exactly FOUR pads: `GND` `U3.12`
and `+3V3` `J1.35` / `R19.1` / `R26.1`.

The plane repair cannot rescue those four.  It ran on the refused I2C batch and
reported `J1.35`: `NO LEGAL ESCAPE at >= 0.600 mm; blocked by J1.34 (x45)` --
it is a 0.30 mm finger inside a 0.5 mm-pitch FPC row -- and `R19.1` / `R26.1`:
`no legal 0.80 mm barrel within 8.0 mm of any escape`.  A bond that no router
move can restore must not be broken in the first place, so this module answers
the prevention question instead of the repair one:

    WHICH COPPER, IF A FOREIGN TRACK TOOK IT, WOULD ORPHAN A PAD FOR GOOD?

METHOD.  KiCad already knows the islands: each outline of a zone's filled
polygon set IS one connected island, so island membership is read, not modelled.
For every island of an OUTER pour the pads it bonds are collected and the island
is guarded when either clause holds:

  SMALL_ISLAND  the island is at most `--area-max` mm2 and bonds two or more
                pads.  A small island is a LOCAL bond with no redundancy: one
                slot severs it and the repair has no via site to answer with.
                Measured on this board, `GND` `B.Cu` island 18 (10.29 mm2) is
                `C4.2` + `U3.12`, and `+3V3` `F.Cu` island 6 (21.07 mm2) is
                `R19.1` + `R26.1` -- three of the four fatal pads.

  NO_ESCAPE     a pad on ANY island for which `maze3d.pad_escapes` -- the same
                primitive the repair launches from -- returns nothing at the
                net's own contract width.  That pad can never be re-bonded by
                any router move on this geometry, whatever the island's size.
                This is `J1.35`, on the 972.89 mm2 main `+3V3` island.

What is then protected is a TUBE: for each edge of a Euclidean MST over the
island's anchors, the geodesic path between them THROUGH THE ISLAND'S OWN
COPPER, eroded first so the path only runs where a tube of radius
`--tube-radius` fits.  The tube is the promise: keep foreign copper far enough
away and KiCad's re-pour must leave at least that much metal joining the pads,
because the fill is a subtraction and nothing else touched it.

The keep-out radius a router owes the tube is `tube-radius + zone clearance`,
which is what this file emits.  The router adds its own half-width and lattice
guard band, because those depend on the net being routed and not on the bond.

Nothing here writes the board.  The spec is a prediction of what must be kept
clear; the full-board gate is still the only thing that promotes copper.
"""

import argparse
import collections
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

# The lattice the tube is found on.  25 um is a quarter of the 0.10 mm the
# narrowest guarded neck measured, so a neck cannot fall between two samples.
TUBE_GRID = 25000
# Half the copper the tube promises to leave standing.  0.125 mm gives a
# 0.25 mm-wide neck, above the 0.200 mm `min_thickness` every zone on this
# board is filled with, so KiCad's own fill cannot prune it as a sliver.
TUBE_RADIUS = 125000
# The zone clearance every pour on this board carries (`(clearance 0.25)` on
# all five zones).  A foreign track closer than this to the tube would make
# the re-pour eat into it.
ZONE_CLEARANCE = 250000
AREA_MAX_MM2 = 64.0
OUTER = {"F.Cu": "F", "B.Cu": "B"}


# --------------------------------------------------------------------------- #
# raster / geodesic primitives
# --------------------------------------------------------------------------- #
def chain_edges(chain):
    n = chain.PointCount()
    return [(chain.CPoint(k).x, chain.CPoint(k).y,
             chain.CPoint((k + 1) % n).x, chain.CPoint((k + 1) % n).y)
            for k in range(n)]


def raster(E, ox, oy, G, nx, ny):
    """Even-odd scan conversion of a closed edge soup onto a lattice.

    Outline and hole edges go in together: even-odd resolves the holes without
    caring which winding they were stored with.
    """
    if len(E) == 0:
        return np.zeros((ny, nx), dtype=bool)
    x0, y0, x1, y1 = E[:, 0], E[:, 1], E[:, 2], E[:, 3]
    keep = y0 != y1
    x0, y0, x1, y1 = x0[keep], y0[keep], x1[keep], y1[keep]
    ylo = np.minimum(y0, y1)
    yhi = np.maximum(y0, y1)
    d = np.zeros((ny, nx + 1), dtype=np.int32)
    rows, cols = [], []
    ytop = oy + (ny - 1) * G
    for k in range(len(x0)):
        if yhi[k] < oy or ylo[k] > ytop:
            continue
        a = max(0, int(math.ceil((ylo[k] - oy) / G)))
        b = min(ny - 1, int(math.floor((yhi[k] - oy) / G)))
        if b < a:
            continue
        j = np.arange(a, b + 1)
        Y = oy + j * G
        m = (Y >= ylo[k]) & (Y < yhi[k])        # half-open: no double count
        if not m.any():
            continue
        j, Y = j[m], Y[m]
        xint = x0[k] + (x1[k] - x0[k]) * (Y - y0[k]) / (y1[k] - y0[k])
        c = np.ceil((xint - ox) / G).astype(np.int64)
        np.clip(c, 0, nx, out=c)
        rows.append(j)
        cols.append(c)
    if not rows:
        return np.zeros((ny, nx), dtype=bool)
    np.add.at(d, (np.concatenate(rows), np.concatenate(cols)), 1)
    return (np.cumsum(d[:, :nx], axis=1) % 2).astype(bool)


def erode(m, k):
    """Octagonal erosion by `k` cells.  The array border counts as outside, so
    a tube can never be found running off the edge of the window."""
    cur = m.copy()
    cur[0, :] = cur[-1, :] = False
    cur[:, 0] = cur[:, -1] = False
    for s in range(k):
        p = cur
        e = p.copy()
        e[1:, :] &= p[:-1, :]
        e[:-1, :] &= p[1:, :]
        e[:, 1:] &= p[:, :-1]
        e[:, :-1] &= p[:, 1:]
        if s % 2:
            e[1:, 1:] &= p[:-1, :-1]
            e[1:, :-1] &= p[:-1, 1:]
            e[:-1, 1:] &= p[1:, :-1]
            e[:-1, :-1] &= p[1:, 1:]
        cur = e
    return cur


_N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def bfs_path(free, seeds, goals):
    """Shortest 8-connected path from any seed cell to any goal cell."""
    ny, nx = free.shape
    prev = np.full((ny, nx), -1, dtype=np.int64)
    seen = np.zeros((ny, nx), dtype=bool)
    dq = collections.deque()
    goalset = set(goals)
    for (j, i) in seeds:
        if 0 <= j < ny and 0 <= i < nx and free[j, i] and not seen[j, i]:
            seen[j, i] = True
            prev[j, i] = -2
            dq.append((j, i))
    while dq:
        j, i = dq.popleft()
        if (j, i) in goalset:
            path = []
            while True:
                path.append((j, i))
                p = int(prev[j, i])
                if p == -2:
                    break
                j, i = divmod(p, nx)
            return path[::-1]
        for dj, di in _N8:
            nj, ni = j + dj, i + di
            if 0 <= nj < ny and 0 <= ni < nx and free[nj, ni] and not seen[nj, ni]:
                seen[nj, ni] = True
                prev[nj, ni] = j * nx + i
                dq.append((nj, ni))
    return None


def disc_cells(cx, cy, r, ox, oy, G, nx, ny, mask):
    out = []
    i0 = max(0, int((cx - r - ox) / G))
    i1 = min(nx - 1, int((cx + r - ox) / G) + 1)
    j0 = max(0, int((cy - r - oy) / G))
    j1 = min(ny - 1, int((cy + r - oy) / G) + 1)
    for j in range(j0, j1 + 1):
        for i in range(i0, i1 + 1):
            if not mask[j, i]:
                continue
            if (ox + i * G - cx) ** 2 + (oy + j * G - cy) ** 2 <= r * r:
                out.append((j, i))
    return out


def geodesic(edges, a, b, radius, grid, win_mm=2.0, grows=4):
    """A tube of `radius` from anchor `a` to anchor `b` inside `edges`.

    Both anchors are (x, y, seed_radius).  The window starts at their bounding
    box plus `win_mm` and doubles until a path is found, so a bond that has to
    detour around a hole is not lost to an arbitrary box.
    """
    k = max(1, int(round(radius / float(grid))))
    for grow in range(grows):
        m = int((win_mm * (2 ** grow)) * 1e6)
        ox = min(a[0], b[0]) - m
        oy = min(a[1], b[1]) - m
        nx = int((max(a[0], b[0]) + m - ox) / grid) + 1
        ny = int((max(a[1], b[1]) + m - oy) / grid) + 1
        if nx * ny > 6000000:
            break
        cu = raster(edges, ox, oy, grid, nx, ny)
        for kk in range(k, 0, -1):
            core = erode(cu, kk)
            free = core.copy()
            seeds = disc_cells(a[0], a[1], a[2], ox, oy, grid, nx, ny, cu)
            goals = disc_cells(b[0], b[1], b[2], ox, oy, grid, nx, ny, cu)
            if not seeds or not goals:
                break
            for (j, i) in seeds + goals:
                free[j, i] = True
            p = bfs_path(free, seeds, goals)
            if p:
                pts = [(int(ox + i * grid), int(oy + j * grid)) for (j, i) in p]
                mm = sum(math.hypot(pts[t][0] - pts[t - 1][0],
                                    pts[t][1] - pts[t - 1][1])
                         for t in range(1, len(pts))) / 1e6
                return dict(points=decimate(pts, grid * 4),
                            radius=kk * grid, mm=round(mm, 3),
                            window_mm=round(m / 1e6, 3))
    return None


def decimate(pts, step):
    """Thin the polyline: the mask stamps a disc an order of magnitude wider."""
    out = [pts[0]]
    for p in pts[1:-1]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= step:
            out.append(p)
    if len(pts) > 1:
        out.append(pts[-1])
    return out


def mst_edges(nodes):
    """Euclidean MST over (x, y) nodes -- Prim, tiny N."""
    n = len(nodes)
    if n < 2:
        return []
    used = [0]
    rest = list(range(1, n))
    out = []
    while rest:
        best = None
        for u in used:
            for v in rest:
                d = math.hypot(nodes[u][0] - nodes[v][0], nodes[u][1] - nodes[v][1])
                if best is None or d < best[0]:
                    best = (d, u, v)
        out.append((best[1], best[2]))
        used.append(best[2])
        rest.remove(best[2])
    return out


# --------------------------------------------------------------------------- #
# board reading
# --------------------------------------------------------------------------- #
def read_pours(board):
    """[(net, layername, lkey, [island...])] for every filled OUTER pour."""
    import pcbnew
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lid in z.GetLayerSet().CuStack():
            lname = board.GetLayerName(lid)
            if lname not in OUTER:
                continue
            ps = z.GetFilledPolysList(lid)
            isl = []
            for i in range(ps.OutlineCount()):
                poly = pcbnew.SHAPE_POLY_SET()
                poly.AddOutline(ps.Outline(i))
                E = chain_edges(ps.Outline(i))
                for h in range(ps.HoleCount(i)):
                    poly.AddHole(ps.Hole(i, h), 0)
                    E += chain_edges(ps.Hole(i, h))
                isl.append(dict(index=i, poly=poly,
                                area_mm2=poly.Area() / 1e12,
                                edges=np.array(E, dtype=np.float64)))
            out.append(dict(net=z.GetNetname(), layer=lname,
                            lkey=OUTER[lname], islands=isl))
    return out


def assign(board, pour):
    """Which pads and which vias sit on each island of this pour."""
    import pcbnew
    for isl in pour["islands"]:
        isl["pads"] = []
        isl["vias"] = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != pour["net"]:
                continue
            if pour["layer"] not in [board.GetLayerName(l)
                                     for l in p.GetLayerSet().CuStack()]:
                continue
            pos = p.GetPosition()
            for isl in pour["islands"]:
                if isl["poly"].Contains(pcbnew.VECTOR2I(pos.x, pos.y), -1, 0):
                    isl["pads"].append(dict(
                        ref="%s.%s" % (fp.GetReference(), p.GetNumber()),
                        x=pos.x, y=pos.y,
                        r=min(p.GetSizeX(), p.GetSizeY()) / 2.0))
                    break
    for t in board.Tracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != pour["net"]:
            continue
        v = pcbnew.Cast_to_PCB_VIA(t)
        pos = v.GetPosition()
        for isl in pour["islands"]:
            if isl["poly"].Contains(pcbnew.VECTOR2I(pos.x, pos.y), -1, 0):
                isl["vias"].append(dict(x=pos.x, y=pos.y, r=150000))
                break


def no_escape_pads(board_path, pour_nets):
    """Pads of the pour nets that `maze3d.pad_escapes` cannot launch from.

    This is the repair's own primitive at the net's own contract width, so a
    pad it reports here is a pad no router move on this geometry can re-bond.
    """
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
    import pcbnew
    import route_maze_batch as rb
    import qrouter as qr
    import maze3d as mz
    import incremental_router as ir

    ref = pcbnew.LoadBoard(str(board_path))
    contracts = {n: rb.net_contract(ref, n) for n in pour_nets}
    reserved = rb.reserved_inner_planes(ref)
    del ref
    qb = qr.QBoard(str(board_path))
    ir.inject_existing_via_obstacles(qb)
    dead = {}
    for n, c in contracts.items():
        if not c["known_class"]:
            continue
        c["layers"] = rb.permitted_layers(qb.routable, c["layers"], reserved, n)
        field = mz.Field(qb, n, c["width"], c["clr"], c["clr"], c["via_dia"],
                         c["via_drill"], G=100000, layers=c["layers"])
        for pad in qb.pads.values():
            if pad.get("net") != n:
                continue
            if not pad_escapes_any(mz, qb, field, pad):
                dead[pad["ref"]] = dict(net=n, width=c["width"])
    return dead


def pad_escapes_any(mz, qb, field, pad):
    try:
        return bool(mz.pad_escapes(qb, field, pad, None, limit=4))
    except Exception:
        return True         # never claim a pad is dead because a probe threw


# --------------------------------------------------------------------------- #
def build(board_path, area_max, radius, grid, escapes=True):
    import pcbnew
    board = pcbnew.LoadBoard(str(board_path))
    pours = read_pours(board)
    for p in pours:
        assign(board, p)
    dead = no_escape_pads(board_path, sorted({p["net"] for p in pours})) \
        if escapes else {}

    guards, skipped = [], []
    for p in pours:
        for isl in p["islands"]:
            pads = isl["pads"]
            if len(pads) < 2:
                continue
            fatal = [q for q in pads if q["ref"] in dead]
            small = isl["area_mm2"] <= area_max
            if not small and not fatal:
                continue
            reason = "SMALL_ISLAND" if small else "NO_ESCAPE"
            # A small island is protected whole -- every pad it bonds.  A large
            # one is protected only where a pad that can never be re-bonded
            # hangs off it, and then only back to the nearest anchor that CAN
            # be: a via ties the island to a reserved inner plane and a pad
            # with an escape can be re-stitched.
            if small:
                nodes = [(q["x"], q["y"], q["r"]) for q in pads]
                labels = [q["ref"] for q in pads]
                pairs = mst_edges(nodes)
            else:
                anchors = [(v["x"], v["y"], v["r"], "via") for v in isl["vias"]]
                anchors += [(q["x"], q["y"], q["r"], q["ref"])
                            for q in pads if q["ref"] not in dead]
                if not anchors:
                    skipped.append(dict(net=p["net"], layer=p["layer"],
                                        island=isl["index"],
                                        reason="NO_ANCHOR",
                                        pads=[q["ref"] for q in fatal]))
                    continue
                nodes, labels, pairs = [], [], []
                for q in fatal:
                    a = min(anchors, key=lambda t: math.hypot(t[0] - q["x"],
                                                              t[1] - q["y"]))
                    nodes += [(q["x"], q["y"], q["r"]), (a[0], a[1], a[2])]
                    labels += [q["ref"], a[3]]
                    pairs.append((len(nodes) - 2, len(nodes) - 1))
            for (u, v) in pairs:
                t = geodesic(isl["edges"], nodes[u], nodes[v], radius, grid)
                rec = dict(net=p["net"], layer=p["layer"], lkey=p["lkey"],
                           island=isl["index"],
                           island_area_mm2=round(isl["area_mm2"], 3),
                           reason=reason, ends=[labels[u], labels[v]])
                if t is None:
                    rec["ok"] = False
                    rec["why"] = "NO_TUBE"
                    skipped.append(rec)
                    continue
                rec.update(ok=True, mm=t["mm"], tube_radius=t["radius"],
                           window_mm=t["window_mm"],
                           keepout_radius=t["radius"] + ZONE_CLEARANCE,
                           points=t["points"])
                guards.append(rec)
    return guards, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--area-max", type=float, default=AREA_MAX_MM2)
    ap.add_argument("--tube-radius", type=int, default=TUBE_RADIUS)
    ap.add_argument("--grid", type=int, default=TUBE_GRID)
    ap.add_argument("--no-escapes", action="store_true",
                    help="skip the pad-escape pass (SMALL_ISLAND clause only)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    sys.path.insert(0, str(HERE))
    from route_maze_batch import sha256_file

    guards, skipped = build(a.board, a.area_max, a.tube_radius, a.grid,
                            escapes=not a.no_escapes)
    doc = dict(schema=1, board=str(a.board), board_sha256=sha256_file(a.board),
               grid=a.grid, tube_radius=a.tube_radius,
               zone_clearance=ZONE_CLEARANCE, area_max_mm2=a.area_max,
               summary=dict(guards=len(guards), skipped=len(skipped),
                            mm=round(sum(g["mm"] for g in guards), 3),
                            points=sum(len(g["points"]) for g in guards)),
               guards=guards, skipped=skipped)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for g in guards:
        print("  %-6s %-5s island %-3d %-13s %-24s %6.3f mm r=%.3f"
              % (g["net"], g["lkey"], g["island"], g["reason"],
                 "-".join(g["ends"]), g["mm"], g["tube_radius"] / 1e6),
              file=sys.stderr)
    for s in skipped:
        print("  SKIP %s" % json.dumps(s, sort_keys=True, default=str)[:180],
              file=sys.stderr)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
