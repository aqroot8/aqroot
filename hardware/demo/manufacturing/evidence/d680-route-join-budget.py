#!/usr/bin/env python3
"""READ-ONLY: ask maze3d.route_join itself -- the instrument the gate uses --
whether {L4.1,U21.3} reaches the BQ25185_SYS trunk cluster on the EVICTED
board, at several budgets, and report which island it is aimed at."""
import sys, time
from pathlib import Path
HERE = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "hardware/beta-v2/checks"))
import qrouter as qr, maze3d as mz, incremental_router as ir
from route_maze_batch import net_contract, permitted_layers, reserved_inner_planes

BOARD = Path(sys.argv[1])
NET = "/01_POWER_TREE/BQ25185_SYS"
G = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
qb = qr.QBoard(str(BOARD))
ir.inject_existing_via_obstacles(qb)
res = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
lays = list(permitted_layers(qb.routable, c["layers"], res, NET))
isl = mz.net_islands(qb, NET)
print("islands:", flush=True)
for i, g in enumerate(isl):
    print("  %d  %s" % (i, [p["ref"] for p in g]), flush=True)
src = next(g for g in isl if any(p["ref"] == "L4.1" for p in g))
body = max(isl, key=len)
print("src", [p["ref"] for p in src], " dst(body)", [p["ref"] for p in body], flush=True)
f = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"], c["via_dia"],
             c["via_drill"], G=G, layers=lays)
for mx in (0.0, 45.0, 120.0):
    t0 = time.time()
    m = qb.mark()
    try:
        r = mz.route_join(qb, f, src, body, max_mm=(mx or None)) if mx else \
            mz.route_join(qb, f, src, body)
    except TypeError:
        r = mz.route_join(qb, f, src, body)
    finally:
        qb.revert(m)
    print("max_mm=%-6s -> %s  [%.0fs]" % (mx, {k: v for k, v in r.items()
                                               if k in ("ok", "reason", "why", "mm", "vias",
                                                        "src_escapes", "dst_escapes")},
                                          time.time() - t0), flush=True)
