#!/usr/bin/env python3
"""Is ONE island pair's `NO_PATH` a PITCH question or a WALL? -- D-668

    screen_pair_pitch_ladder.py BOARD NET A_REF B_REF OUT.json 50000,33333,25000

D-625 proved a corridor `NO_PATH` on this board is a LADDER question before it
is a wall: `BTN_DOWN_N` refused at 0.100 / 0.0667 / 0.050 mm under the same
guard that admitted it at 0.0333 mm.  Every refusal since has therefore carried
an unasked question, and `screen_partial_pairs.py` prints "CORRIDOR -- ladder
it" without anything in the tree that actually does.  This does: the SAME pair,
the SAME board, NOTHING removed, at every stated lattice.

It removes nothing, writes nothing to any board and takes no licence.  BOARD is
a path, so the pair may be asked of a CANDIDATE -- which is usually the only
board the pair is open on (D-668 §1).

WHAT AN ANSWER COSTS, measured on `/SX1262_CS_N` `R27.2 <-> U1.10`: 241.5 s at
0.050 mm (13.9 M cells), 779.1 s at 0.0333 mm (31.2 M), 1314.6 s at 0.025 mm
(55.5 M).  Three rungs is ~40 minutes and it retires or confirms the branch.
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

import qrouter as qr             # noqa: E402
import maze3d as mz              # noqa: E402
from route_maze_batch import (net_contract, reserved_inner_planes,  # noqa: E402
                              permitted_layers)

BOARD = Path(sys.argv[1]).resolve()
NET, A_REF, B_REF = sys.argv[2], sys.argv[3], sys.argv[4]
OUT = Path(sys.argv[5])
RUNGS = [int(x) for x in sys.argv[6].split(",")]

qb = qr.QBoard(str(BOARD))
import incremental_router as ir   # noqa: E402
ir.inject_existing_via_obstacles(qb)
reserved = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
far = list(permitted_layers(qb.routable, c["layers"], reserved, NET))
islands = mz.net_islands(qb, NET)
pads = {p["ref"]: p for isl in islands for p in isl}
pa, pb = pads[A_REF], pads[B_REF]

rows = []
for g in RUNGS:
    field = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"],
                     c["via_dia"], c["via_drill"], G=g, layers=far)
    cells = field.nx * field.ny * len(far)
    t0 = time.time()
    m = qb.mark()
    try:
        r = mz.offcentre_route(qb, field, pa, pb, G=g)
    finally:
        qb.revert(m)
    row = dict(grid_nm=g, grid_mm=round(g / 1e6, 4), cells=cells,
               seconds=round(time.time() - t0, 1), ok=bool(r.get("ok")),
               reason=r.get("reason"), why=r.get("why"), mm=r.get("mm"),
               vias=r.get("vias"), layers=r.get("layers"))
    rows.append(row)
    print("g=%-7d %-9s %s" % (g, "%.4f mm" % (g / 1e6),
                              ("OPENS %.3f mm / %s via" % (r["mm"], r["vias"]))
                              if r.get("ok") else r.get("reason")),
          file=sys.stderr, flush=True)
    OUT.write_text(json.dumps(
        dict(schema=1, what=__doc__.strip(), board=str(BOARD),
             board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),
             net=NET, a=A_REF, b=B_REF, layers=far,
             width_mm=round(c["width"] / 1e6, 4),
             removed="NOTHING -- this is the BASE corridor at every pitch",
             rows=rows), indent=2, sort_keys=True) + "\n")
