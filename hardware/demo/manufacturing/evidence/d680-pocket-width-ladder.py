#!/usr/bin/env python3
"""READ-ONLY: at which TRACK WIDTH does an outer-layer corridor exist between
the BQ25185_SYS trunk and the U21/L4 accessory-boost pocket?

Floods maze3d.Field's own free map inside a WINDOW, on the layers the net's own
contract permits, with a through-via move wherever the Field calls a barrel
legal.  Nothing is written."""
import sys, time
from pathlib import Path
import numpy as np
HERE = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "hardware/beta-v2/checks"))
import qrouter as qr, maze3d as mz, incremental_router as ir
from route_maze_batch import net_contract, permitted_layers, reserved_inner_planes

BOARD = HERE.parent / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET = "/01_POWER_TREE/BQ25185_SYS"
G = 50000
MM = qr.MM
WIN = (44.0, 14.0, 64.0, 48.0)          # mm
qb = qr.QBoard(str(BOARD))
ir.inject_existing_via_obstacles(qb)
res = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
lays = [L for L in permitted_layers(qb.routable, c["layers"], res, NET)]
OUTER = [L for L in lays if L in ("F", "B")]
print("permitted layers", lays, "-> flooding OUTER only", OUTER, flush=True)
SEEDS = [(52.000, 36.700, "F", "trunk vertex F.Cu"),
         (56.000, 20.100, "B", "trunk B.Cu at L2"),
         (54.700, 23.900, "F", "trunk F.Cu at 54.7,23.9")]
TARGETS = [(57.715, 36.200, "L4.1 land"), (57.087, 39.400, "U21.3 land"),
           (58.400, 36.200, "B.Cu pour east of L4.1")]
for w_mm in (0.800, 0.700, 0.600, 0.500, 0.400, 0.300):
    t0 = time.time()
    w = int(round(w_mm * MM))
    f = mz.Field(qb, NET, w, c["clr_pad"], c["clr"], c["via_dia"],
                 c["via_drill"], G=G, layers=lays)
    i0, j0 = f.cell(int(WIN[0] * MM), int(WIN[1] * MM))
    i1, j1 = f.cell(int(WIN[2] * MM), int(WIN[3] * MM))
    sl = (slice(j0, j1 + 1), slice(i0, i1 + 1))
    free = {L: ~f.blk[L][sl] for L in OUTER}
    via = f.via[sl] if getattr(f, "via", None) is not None else None
    seen = {L: np.zeros_like(free[L]) for L in OUTER}
    ok = False
    for (sx, sy, sL, nm) in SEEDS:
        si, sj = f.cell(int(sx * MM), int(sy * MM))
        si, sj = si - i0, sj - j0
        if sL in free and free[sL][sj, si]:
            seen[sL][sj, si] = True
            ok = True
        else:
            print("   seed %-24s BLOCKED at %.3f mm" % (nm, w_mm), flush=True)
    if not ok:
        print("%.3f mm  ALL SEEDS BLOCKED" % w_mm, flush=True)
        continue
    cur = {L: seen[L].copy() for L in OUTER}
    for _ in range(20000):
        moved = False
        nxt = {L: mz._shift_or(cur[L], free[L]) & free[L] & ~seen[L] for L in OUTER}
        if via is not None and len(OUTER) > 1:
            for L in OUTER:
                for M in OUTER:
                    if L == M:
                        continue
                    nxt[M] |= (seen[L] | nxt[L]) & via & free[M] & ~seen[M]
        for L in OUTER:
            if nxt[L].any():
                moved = True
                seen[L] |= nxt[L]
            cur[L] = nxt[L]
        if not moved:
            break
    got = []
    for (tx, ty, nm) in TARGETS:
        i, j = f.cell(int(tx * MM), int(ty * MM))
        i, j = i - i0, j - j0
        r = [L for L in OUTER if seen[L][j, i]]
        fr = [L for L in OUTER if free[L][j, i]]
        got.append("%s reached=%s free=%s" % (nm, ",".join(r) or "-", ",".join(fr) or "-"))
    print("%.3f mm  %s   [%.0fs]" % (w_mm, " | ".join(got), time.time() - t0), flush=True)
