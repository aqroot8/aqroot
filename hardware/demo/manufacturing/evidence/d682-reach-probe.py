#!/usr/bin/env python3
"""READ-ONLY: where can /I2C_SCL_INT's U16.3 lattice escapes actually REACH?

D-672 proved the two launchers disagree on this land: `maze3d.pad_escapes`
(the GATE's) finds escapes where `offcentre_route` (every screen's, and
`join_taps`') refuses.  Every corridor verdict on U16.3 taken through the
second launcher is therefore a LAUNCH refusal wearing a corridor's clothes.
This asks the first launcher's question and nothing else: flood the free map
from U16.3's own escapes and report which of the net's own retained copper
points, and which of its pads' escapes, the wavefront touches.  Writes nothing.
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "beta-v2/checks"))
import numpy as np
import route_maze_batch as rb
import qrouter as qr
import maze3d as mz
import incremental_router as ir
import pcbnew

BOARD = sys.argv[1] if len(sys.argv) > 1 else str(rb.BOARD)
NET = "/I2C_SCL_INT"
LAND = "U16.3"
G = int(sys.argv[2]) if len(sys.argv) > 2 else 50000

ref = pcbnew.LoadBoard(BOARD)
reserved = rb.reserved_inner_planes(ref)
c = rb.net_contract(ref, NET)
del ref
qb = qr.QBoard(BOARD)
ir.inject_existing_via_obstacles(qb)
c["layers"] = rb.permitted_layers(qb.routable, c["layers"], reserved, NET)
field = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"],
                 c["via_dia"], c["via_drill"], G=G, layers=c["layers"])
pads = ir.physical_net_pads(qb, NET)
by_ref = {p["ref"]: p for p in pads}
pad = by_ref[LAND]
esc = mz.pad_escapes(qb, field, pad, (56.587e6, 70.0e6), limit=8)
print("escapes for", LAND, len(esc))
for e in esc:
    print("   ", e["layer"], round(e["x"]/1e6, 3), round(e["y"]/1e6, 3),
          "w", e["w"]/1e6, "cell", e["i"], e["j"])
seeds = [(e["layer"], e["i"], e["j"]) for e in esc]
# a deliberately unreachable goal so the wavefront runs to exhaustion
goal = [(c["layers"][0], 1, 1)]
dist, reached = mz.wave3d(field, seeds, goal, 30, budget=200000)
print("goal reached:", reached)
tot = {k: int((v >= 0).sum()) for k, v in dist.items()}
print("reached cells per layer:", tot)
# bounding box of the reached region, per layer
for k, v in dist.items():
    ys, xs = np.nonzero(v >= 0)
    if not len(xs):
        print("  ", k, "EMPTY"); continue
    x0 = (field.ox + xs.min() * field.G) / 1e6
    x1 = (field.ox + xs.max() * field.G) / 1e6
    y0 = (field.oy + ys.min() * field.G) / 1e6
    y1 = (field.oy + ys.max() * field.G) / 1e6
    print("  ", k, "bbox mm", round(x0,3), round(y0,3), round(x1,3), round(y1,3),
          "cells", len(xs))
# is the net's own nearest copper point reachable?
probes = [("F", 55.700, 60.300), ("F", 57.300, 61.800), ("F", 49.000, 56.800),
          ("F", 50.500, 58.400), ("B", 55.700, 60.300), ("I2", 61.300, 65.100)]
print("probe points:")
for L, x, y in probes:
    if L not in dist:
        print("   ", L, x, y, "layer not routable"); continue
    i, j = field.cell(int(x*1e6), int(y*1e6))
    ok = field.inside(i, j) and dist[L][j, i] >= 0
    print("   ", L, x, y, "reachable" if ok else "NOT reachable",
          "" if not field.inside(i,j) else "d=%d" % dist[L][j, i])
