#!/usr/bin/env python3
"""The EXACT copper a pair lays once NAMED objects are withheld -- D-668

    screen_opening_path.py BOARD NET A_REF B_REF CUT.json OUT.json [GRID]

`screen_pair_corridor_blame.py --per-object` ends at a MINIMAL OBJECT SET and a
price -- "one unit, 15.041 mm, 3 vias".  A price is not a lane.
`reserve_corridor.py --lane "F.Cu:x,y x,y ..."` needs the GEOMETRY, and until
this existed the only way to get it was to guess, which is what D-667 spent an
arm learning not to do.  This withholds exactly the unit the blame named,
re-runs `maze3d.offcentre_route`, and dumps what it laid.

CUT.json is one `unit_spec` record straight out of the blame report:

    {"kind": "track", "net": "/WAKE_INT_N", "layer": "F.Cu",
     "a_mm": [58.1, 113.9], "b_mm": [57.55, 110.9], "width_mm": 0.2}

A LANE IS A POLYLINE, NOT A BAG OF ENDPOINTS.  `qb.laid` order is stubs-first,
then the run, so appending endpoints in that order yields a list that LOOKS
like a lane and reserves corridors the route never took.  `lane_chains_by_layer`
chains each layer's segments end to end and reports EVERY disjoint chain.

AND THE BARREL SITES ARE PART OF THE LANE.  D-668 arm N reserved a route's
tracks and not its via sites; `/WAKE_INT_N` took the barrel site at
[53.0, 117.95] that the reserved net needed and both nets ended worse.  `via_xy`
is in the report for that reason -- reserve it as a single-point all-layer lane.

It removes nothing, writes nothing to any board and takes no licence.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import qrouter as qr              # noqa: E402
import incremental_router as ir   # noqa: E402
import maze3d as mz               # noqa: E402
from route_maze_batch import (net_contract, reserved_inner_planes,  # noqa: E402
                              permitted_layers)
from screen_corridor_blockers import WithoutObjects  # noqa: E402

BOARD = Path(sys.argv[1]).resolve()
NET, A_REF, B_REF = sys.argv[2], sys.argv[3], sys.argv[4]
CUT = json.loads(Path(sys.argv[5]).read_text())     # the Q4 unit to withhold
OUT = Path(sys.argv[6])
GRID = int(sys.argv[7]) if len(sys.argv) > 7 else 50000

qb = qr.QBoard(str(BOARD))
ir.inject_existing_via_obstacles(qb)
reserved = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
far = list(permitted_layers(qb.routable, c["layers"], reserved, NET))
islands = mz.net_islands(qb, NET)
pads = {p["ref"]: p for isl in islands for p in isl}
pa, pb = pads[A_REF], pads[B_REF]
field = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"],
                 c["via_dia"], c["via_drill"], G=GRID, layers=far)

# THE WITHHELD OBJECT, FOUND THE WAY THE BLAME FOUND IT: by exact endpoint and
# layer, on the router's own shape pool, so the object dropped here is the same
# object the minimisation named.
LAYER_NAME = {"F": "F.Cu", "I1": "In1.Cu", "I2": "In2.Cu", "I3": "In3.Cu",
              "I4": "In4.Cu", "B": "B.Cu"}
want = []
for L in qb.shapes:
    for s_ in qb.shapes[L]:
        if s_.net != CUT["net"] or not hasattr(s_, "x0"):
            continue
        if LAYER_NAME.get(L, L) != CUT["layer"]:
            continue
        ab = (round(s_.x0 / 1e6, 4), round(s_.y0 / 1e6, 4),
              round(s_.x1 / 1e6, 4), round(s_.y1 / 1e6, 4))
        if ab == tuple(CUT["a_mm"]) + tuple(CUT["b_mm"]) or \
           ab == tuple(CUT["b_mm"]) + tuple(CUT["a_mm"]):
            want.append(s_)
if not want:
    raise SystemExit("the Q4 unit was not found on this board: %r" % CUT)

t0 = time.time()
m = qb.mark()
n_laid = len(qb.laid)
segs = []
try:
    with WithoutObjects(qb, field, [id(o) for o in want]):
        r = mz.offcentre_route(qb, field, pa, pb, G=GRID)
        if r.get("ok"):
            for t in qb.laid[n_laid:]:
                if t.GetClass() == "PCB_VIA":
                    p = t.GetPosition()
                    segs.append(dict(kind="via",
                                     at_mm=[round(p.x / 1e6, 4),
                                            round(p.y / 1e6, 4)]))
                else:
                    s, e = t.GetStart(), t.GetEnd()
                    segs.append(dict(
                        kind="track",
                        layer=qb.b.GetLayerName(t.GetLayer()),
                        a_mm=[round(s.x / 1e6, 4), round(s.y / 1e6, 4)],
                        b_mm=[round(e.x / 1e6, 4), round(e.y / 1e6, 4)],
                        width_mm=round(t.GetWidth() / 1e6, 4)))
finally:
    qb.revert(m)

# A LANE IS A POLYLINE, NOT A BAG OF ENDPOINTS.  `qb.laid` order is the order
# the emitter used -- stubs first, then the run -- so appending endpoints in
# that order yields a list that LOOKS like a lane and is not one.
# `reserve_corridor.py --lane "F.Cu:x,y ..."` walks its points in order and
# reserves the segments BETWEEN them, so an unordered bag would reserve
# corridors this route never took.  Chain each layer's segments end-to-end
# instead, and report every chain rather than silently keeping one.
def chains(rows):
    todo, out = list(rows), []
    while todo:
        seg = todo.pop(0)
        chain = [tuple(seg["a_mm"]), tuple(seg["b_mm"])]
        moved = True
        while moved:
            moved = False
            for other in list(todo):
                a, b = tuple(other["a_mm"]), tuple(other["b_mm"])
                if a == chain[-1]:
                    chain.append(b)
                elif b == chain[-1]:
                    chain.append(a)
                elif a == chain[0]:
                    chain.insert(0, b)
                elif b == chain[0]:
                    chain.insert(0, a)
                else:
                    continue
                todo.remove(other)
                moved = True
        out.append([list(pt) for pt in chain])
    return out


lane = {}
for s_ in segs:
    if s_["kind"] != "track":
        continue
    lane.setdefault(s_["layer"], []).append(s_)
lane = {L: chains(v) for L, v in lane.items()}

OUT.write_text(json.dumps(dict(
    schema=1, what=__doc__.strip(), board=str(BOARD),
    board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),
    net=NET, a=A_REF, b=B_REF, grid_nm=GRID, layers=far,
    withheld=CUT, withheld_router_objects=len(want),
    seconds=round(time.time() - t0, 1),
    ok=bool(r.get("ok")), reason=r.get("reason"), mm=r.get("mm"),
    vias=r.get("vias"), route_layers=r.get("layers"),
    via_xy=r.get("via_xy"), mm_by_layer=r.get("mm_by_layer"),
    objects=segs, lane_chains_by_layer=lane,
    lane_note="ordered polylines, one list per disjoint chain on that layer; this is the spelling reserve_corridor.py --lane reads"), indent=2, sort_keys=True) + "\n")
print("OPENS %s mm / %s via -- %d objects" % (r.get("mm"), r.get("vias"),
                                              len(segs)), file=sys.stderr)
