#!/usr/bin/env python3
"""READ-ONLY: which BARREL does the SYS island jumper close on, at the class
floor WIDTH?  D-688 proved the wall is the barrel and not the track: at
0.500 mm the join refuses with 0.750/0.250 and with 0.650/0.400 and closes
with 0.650/0.250.  Section 11's doctrine is that a rule area states the
LARGEST geometry that fits, not the smallest the fab can make -- so before a
licence is authored the barrel ladder must be swept, not guessed.  emit=False,
nothing written."""
import hashlib, json, sys, time
from pathlib import Path
ROOT = Path("/home/aqroot8/aqroot-demo")
HERE = ROOT / "hardware/demo/manufacturing"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

import qrouter as qr, incremental_router as ir, maze3d as mz
from route_maze_batch import (net_contract, permitted_layers,
                              reserved_inner_planes)

NET = sys.argv[1]
WIDTH = int(sys.argv[2])
VDIA = int(sys.argv[3])
VDRILL = int(sys.argv[4])
GRID = int(sys.argv[5]) if len(sys.argv) > 5 else 25000
MAXMM = float(sys.argv[6]) if len(sys.argv) > 6 else 14.0

sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()
qb = qr.QBoard(str(BOARD)); ir.inject_existing_via_obstacles(qb)
reserved = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
layers = permitted_layers(qb.routable, c["layers"], reserved, NET)
t0 = time.time()
field = mz.Field(qb, NET, WIDTH, c["clr_pad"], c["clr"], VDIA, VDRILL,
                 G=GRID, layers=layers)
r = mz.join_islands(qb, NET, field, via_cost_mm=1.5, max_mm=MAXMM, emit=False)
print(json.dumps(dict(
    schema=1, net=NET, netclass=c["netclass"], board_sha256=sha,
    authoritative_unchanged=(sha == hashlib.sha256(BOARD.read_bytes()).hexdigest()),
    grid_nm=GRID, max_mm=MAXMM, width_nm=WIDTH, via=[VDIA, VDRILL],
    joined=r.get("joined", 0), unjoined=r.get("unjoined", 0), mm=r.get("mm"),
    joins=r.get("joins", []),
    failures=[dict(cluster=f["cluster"], reason=f["reason"])
              for f in r.get("failures", [])],
    seconds=round(time.time() - t0, 1)), indent=2, sort_keys=True, default=str))
