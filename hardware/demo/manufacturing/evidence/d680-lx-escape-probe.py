#!/usr/bin/env python3
"""READ-ONLY: does U21.5 get a legal ACC_5V_LX escape once maze3d.Neck may run
past U21's courtyard?  Asks pad_escapes at several reaches, on the AUTHORITY
board and (optionally) on a candidate named with --board."""
import json, sys
from pathlib import Path
HERE = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "hardware/beta-v2/checks"))
import qrouter as qr, maze3d as mz, incremental_router as ir
from route_maze_batch import net_contract, permitted_layers, reserved_inner_planes

BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    HERE.parent / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb")
NET = "/01_POWER_TREE/ACC_5V_LX"
G, MM = 25000, qr.MM
qb = qr.QBoard(str(BOARD))
ir.inject_existing_via_obstacles(qb)
res = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
lays = list(permitted_layers(qb.routable, c["layers"], res, NET))
isl = mz.net_islands(qb, NET)
pads = {p["ref"]: p for i in isl for p in i}
src, dst = pads["U21.5"], pads["L4.2"]
print("board", BOARD.name, "class", c["netclass"], "trunk width", c["width"], flush=True)
for reach in (0.0, 0.3, 0.5, 0.8):
    nk = mz.neck_rule(qb, 1.5, reach)
    f = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"], c["via_dia"],
                 c["via_drill"], G=G, layers=lays, neck=nk)
    e = mz.pad_escapes(qb, f, src, toward=(dst["x"], dst["y"]), limit=8)
    print("reach %.2f mm -> %d escape(s) for U21.5" % (reach, len(e)), flush=True)
    for k in e[:4]:
        print("    %s (%.3f,%.3f) w=%.3f len=%.3f neck=%s outside=%s"
              % (k["layer"], k["x"] / MM, k["y"] / MM, k["w"] / MM, k["ln"] / MM,
                 k.get("neck", False), k.get("neck_outside_mm")))
