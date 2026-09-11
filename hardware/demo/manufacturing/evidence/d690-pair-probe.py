#!/usr/bin/env python3
"""READ-ONLY: can the EXACT launcher join these two named lands, and at what
length?  `route_join` picks its own pairs; this asks about one."""
import sys, time, json
from pathlib import Path
ROOT = Path("/home/aqroot8/aqroot-demo")
sys.path.insert(0, str(ROOT / "hardware/demo/manufacturing"))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import qrouter as qr, incremental_router as ir, maze3d as mz
from route_maze_batch import net_contract, permitted_layers, reserved_inner_planes, via_floors
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET, A, B = sys.argv[1], sys.argv[2], sys.argv[3]
GRID = int(sys.argv[4]) if len(sys.argv) > 4 else 25000
VIA = tuple(int(v) for v in sys.argv[5].split(":")) if len(sys.argv) > 5 else None
qb = qr.QBoard(str(BOARD)); ir.inject_existing_via_obstacles(qb)
res = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET, trunk_floor=True)
lay = list(permitted_layers(qb.routable, c["layers"], res, NET))
vd, vk = c["via_dia"], c["via_drill"]
if VIA:
    fl = via_floors(c["netclass"])
    vk = max(VIA[1], fl["drill"]); vd = max(VIA[0], fl["dia"], vk + 2 * fl["annular"])
field = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"], vd, vk, G=GRID, layers=lay)
pads = {p["ref"]: p for isl in mz.net_islands(qb, NET) for p in isl}
t0 = time.time()
m = qb.mark()
try:
    r = mz.offcentre_route(qb, field, pads[A], pads[B], G=GRID)
finally:
    qb.revert(m)
print(json.dumps(dict(net=NET, a=A, b=B, grid=GRID, width=c["width"],
                      via=[vd, vk], layers=lay, seconds=round(time.time()-t0,1),
                      result={k: v for k, v in (r or {}).items() if k != 'mark'}),
                 indent=1, default=str))
