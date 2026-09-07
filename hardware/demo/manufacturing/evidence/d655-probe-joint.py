"""D-655 READ-ONLY: probe_joint.py with a `--detour-spec` RESERVE in force.

`route_maze_batch.propose` hands `guard_for(guard_spec, net)` to the main
proposal's own `Field`, not only to detours and bonds, so a reserve disc is a
lever on where a REQUESTED net may go.  This asks -- for a fraction of a gate
run -- whether the disc still leaves both edges routable before three hours are
spent finding out."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import qrouter as qr                                              # noqa: E402
import incremental_router as ir                                   # noqa: E402
import maze3d as mz                                               # noqa: E402
from route_maze_batch import (net_contract, reserved_inner_planes,  # noqa: E402
                              permitted_layers, detour_guard, guard_for)

BOARD = sys.argv[1]
GRID = int(sys.argv[2])
ORDER = sys.argv[3].split(",")
SPEC = json.loads(Path(sys.argv[4]).read_text()) if len(sys.argv) > 4 else None

EDGE = {"SDA": ("/I2C_SDA_INT", "U3.23", "U2.23"),
        "SCL": ("/I2C_SCL_INT", "U2.22", "U3.22")}

qb = qr.QBoard(BOARD)
ir.inject_existing_via_obstacles(qb)
reserved = reserved_inner_planes(qb.b)
gspec = detour_guard(SPEC) if SPEC else {"guards": []}

res = {}
for tag in ORDER:
    net, a, b = EDGE[tag]
    c = net_contract(qb.b, net)
    far = list(permitted_layers(qb.routable, c["layers"], reserved, net))
    pads = {p["ref"]: p for isl in mz.net_islands(qb, net) for p in isl}
    g = guard_for(gspec, net) if gspec["guards"] else None
    field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                     c["via_dia"], c["via_drill"], G=GRID, layers=far, guard=g)
    r = mz.offcentre_route(qb, field, pads[a], pads[b], G=GRID)
    res[tag] = {k: v for k, v in r.items() if k != "mark"}
    print(tag, json.dumps(res[tag]), flush=True)
