#!/usr/bin/env python3
"""READ-ONLY: the COARSEST lattice at which the U21/L4 boost pocket reaches the
BQ25185_SYS trunk once ACC_5V_FB and EXT_SCL_BUF are held out of the window."""
import sys
from pathlib import Path
import numpy as np
HERE = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "hardware/beta-v2/checks"))
import qrouter as qr, maze3d as mz, incremental_router as ir
from route_maze_batch import net_contract, permitted_layers, reserved_inner_planes
from screen_corridor_blockers import Without

import os
BOARD = Path(os.environ.get("PROBE_BOARD", str(HERE.parent / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb")))
NET = "/01_POWER_TREE/BQ25185_SYS"
MM = qr.MM
WIN = (44.0, 14.0, 66.0, 48.0)
NETS = [n for n in os.environ.get("PROBE_NETS", "/01_POWER_TREE/ACC_5V_FB,/09_COMMUNITY_HEADER/EXT_SCL_BUF").split(",") if n]
BOX = (55.5, 32.0, 58.0, 39.5)
qb = qr.QBoard(str(BOARD))
ir.inject_existing_via_obstacles(qb)
res = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
lays = list(permitted_layers(qb.routable, c["layers"], res, NET))
OUTER = [L for L in lays if L in ("F", "B")]
for G in (50000, 25000):
    f0 = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"], c["via_dia"],
                  c["via_drill"], G=G, layers=lays)
    with Without(qb, f0, NETS, tuple(int(round(v * MM)) for v in BOX)):
        f = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"], c["via_dia"],
                     c["via_drill"], G=G, layers=lays)
        i0, j0 = f.cell(int(WIN[0] * MM), int(WIN[1] * MM))
        i1, j1 = f.cell(int(WIN[2] * MM), int(WIN[3] * MM))
        sl = (slice(j0, j1 + 1), slice(i0, i1 + 1))
        free = {L: ~f.blk[L][sl] for L in OUTER}
        via = f.via_ok[sl]
        seen = {L: np.zeros_like(free[L]) for L in OUTER}
        si, sj = f.cell(int(57.715 * MM), int(36.200 * MM))
        si, sj = si - i0, sj - j0
        if not free["B"][sj, si]:
            print("G=%6d  L4.1 land BLOCKED" % G, flush=True); continue
        seen["B"][sj, si] = True
        cur = {L: seen[L].copy() for L in OUTER}
        for _ in range(20000):
            moved = False
            nxt = {L: mz._shift_or(cur[L], free[L]) & free[L] & ~seen[L] for L in OUTER}
            for L in OUTER:
                for M in OUTER:
                    if L != M:
                        nxt[M] |= (seen[L] | nxt[L]) & via & free[M] & ~seen[M]
            for L in OUTER:
                if nxt[L].any():
                    moved = True
                    seen[L] |= nxt[L]
                cur[L] = nxt[L]
            if not moved:
                break
        hits = []
        for (tx, ty, L, nm) in ((52.000, 36.700, "F", "trunkF"),
                                (56.000, 20.100, "B", "trunkB@L2")):
            i, j = f.cell(int(tx * MM), int(ty * MM))
            i, j = i - i0, j - j0
            hits.append("%s=%s" % (nm, "REACHED" if seen[L][j, i]
                                   else ("free" if free[L][j, i] else "blk")))
        print("G=%6d (%.4f mm)  %s   cells B=%d F=%d"
              % (G, G / MM, "  ".join(hits), int(seen["B"].sum()),
                 int(seen["F"].sum())), flush=True)
