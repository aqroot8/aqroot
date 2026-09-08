#!/usr/bin/env python3
"""READ-ONLY: reproduce the D-665 Q4 minimal-object opening of
/WAKE_INT_N U2.1 <-> U3.1 and PRINT THE ROUTE'S EXACT GEOMETRY, so the
reserve discs of the --detour-spec can be authored against the copper the
router actually wants instead of against a guess."""
import json, sys
from pathlib import Path
HERE = Path('/home/aqroot8/aqroot-demo/hardware/demo/manufacturing')
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import qrouter as qr
import incremental_router as ir
import maze3d as mz
from route_maze_batch import net_contract, reserved_inner_planes, permitted_layers
from screen_corridor_blockers import WithoutObjects

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET, A_REF, B_REF, GRID, MARGIN = "/WAKE_INT_N", "U2.1", "U3.1", 50000, 3.0
qb = qr.QBoard(str(BOARD)); ir.inject_existing_via_obstacles(qb)
reserved = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
far = list(permitted_layers(qb.routable, c["layers"], reserved, NET))
islands = mz.net_islands(qb, NET)
pads = {p["ref"]: p for isl in islands for p in isl}
pa, pb = pads[A_REF], pads[B_REF]
M = qr.MM
box = (min(pa["x"], pb["x"]) - MARGIN*M, min(pa["y"], pb["y"]) - MARGIN*M,
       max(pa["x"], pb["x"]) + MARGIN*M, max(pa["y"], pb["y"]) + MARGIN*M)
field = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"],
                 c["via_dia"], c["via_drill"], G=GRID, layers=far)
KEEP = {("T", "/SD_CARD_DETECT_N", "F", 54050000, 81500000, 53000000, 82550000),
        ("V", "GND", 54000000, 90400000)}
objs = []
for L in qb.shapes:
    for s in qb.shapes[L]:
        if s.tag not in ("track", "via"): continue
        a,b,cc,d = s.bbox(0)
        if a < box[0] or b < box[1] or cc > box[2] or d > box[3]: continue
        if s.tag == "via":
            k = ("V", s.net, int(s.cx), int(s.cy))
        else:
            k = ("T", s.net, L, int(s.x0), int(s.y0), int(s.x1), int(s.y1))
        if s.tag == "via":
            if k in KEEP: objs.append(s)
        elif k in KEEP: objs.append(s)
for h in qb.holes:
    if not h.tag.startswith("via"): continue
    a,b,cc,d = h.bbox(0)
    if a < box[0] or b < box[1] or cc > box[2] or d > box[3]: continue
    if ("V", h.net, int(h.cx), int(h.cy)) in KEEP: objs.append(h)
print("held out %d router objects" % len(objs), file=sys.stderr)
with WithoutObjects(qb, field, [id(o) for o in objs]):
    m = qb.mark()
    try:
        r = mz.offcentre_route(qb, field, pa, pb, G=GRID)
    finally:
        qb.revert(m)
print(json.dumps(r, indent=1, default=str))
