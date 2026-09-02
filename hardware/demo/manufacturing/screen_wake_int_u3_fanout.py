#!/usr/bin/env python3
"""Bound U3.1 B.Cu fanouts while reserving the proven WAKE_INT_N middle chain.

The generic five-land tree stops at U3.1 before it can exercise the complete
lower branch.  This scratch-only screen enumerates package-specific perimeter
and under-body shoulders, then replays U2.1->Q10.3->U1.23 for each qualified
fanout until a coexistence witness is found.  It never emits partial copper.
"""

import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
NET = "/WAKE_INT_N"
REF = "U3.1"
WIDTH = CLEARANCE = 200_000

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(points):
    return [p for i, p in enumerate(points) if not i or p != points[i - 1]]


def emit(board, a, b):
    for shape in board.obstacles("B", NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    board.track(NET, "B", *a, *b, WIDTH)
    return True


def add_fanout(source, target, via, path):
    trial = qr.QBoard(source)
    ir.inject_existing_via_obstacles(trial)
    if not all(emit(trial, a, b) for a, b in zip(path, path[1:])):
        return False
    trial.via(NET, *via, 600_000, 300_000)
    trial.save(target)
    for suffix in (".kicad_dru", ".kicad_pro"):
        target.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    return True


def main():
    before = sha(BOARD)
    seed = qr.QBoard(BOARD)
    pad = {p["ref"]: p for p in ir.physical_net_pads(seed, NET)}[REF]

    # U3.1 is the left end of the bottom-side TSSOP's upper row.  Cover the
    # outward west perimeter and the eastward under-body space on a 0.25 mm
    # lattice.  The bounds extend several ordinary-via diameters beyond the
    # land but remain local to the package neighborhood.
    shoulder_xs = range(49_000_000, 57_001_000, 250_000)
    via_xs = range(47_500_000, 58_501_000, 250_000)
    via_ys = range(78_000_000, 85_001_000, 250_000)
    board = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(board)
    tested = 0
    legal = []
    witnesses = []
    for shoulder_x, via_x, via_y in itertools.product(
            shoulder_xs, via_xs, via_ys):
        if (shoulder_x < pad["x"]) != (via_x <= shoulder_x):
            continue
        tested += 1
        mark = board.mark()
        via = (via_x, via_y)
        path = compact([(pad["x"], pad["y"]),
                        (shoulder_x, pad["y"]),
                        (shoulder_x, via_y), via])
        if (all(board.point_free(layer, NET, *via, 600_000,
                                 CLEARANCE, CLEARANCE, 25_000)
                for layer in board.cu)
                and all(emit(board, a, b) for a, b in zip(path, path[1:]))):
            board.via(NET, *via, 600_000, 300_000)
            legal.append({
                "shoulder_x_mm": shoulder_x / 1e6,
                "via_mm": [via_x / 1e6, via_y / 1e6],
                "path_mm": [[x / 1e6, y / 1e6] for x, y in path],
            })
            witnesses.append((via, path))
        board.revert(mark)

    coexistence = []
    clean = None
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-wake-u3-") as td:
        work = Path(td)
        for index, (via, path) in enumerate(witnesses):
            candidate = work / f"candidate-{index:04d}.kicad_pcb"
            if not add_fanout(BOARD, candidate, via, path):
                continue
            routes = []
            for leg in ("WAKE_INT_U2_Q10", "WAKE_INT_Q10_U1"):
                run = subprocess.run(
                    [sys.executable, str(LOCAL), leg, "--route", str(candidate)],
                    text=True, capture_output=True, check=True)
                result = json.loads(run.stdout)["result"]
                routes.append({"leg": leg, "ok": result.get("ok", False),
                               "reason": result.get("reason", "OK")})
                if not result.get("ok"):
                    break
            row = {"fanout_index": index, "routes": routes,
                   "middle_chain_complete": len(routes) == 2 and
                   all(r["ok"] for r in routes)}
            coexistence.append(row)
            if row["middle_chain_complete"]:
                clean = {"fanout_index": index, **legal[index]}
                break

    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before,
        "contract": {"net": NET, "pad": REF, "native_layer": "B.Cu",
                     "width_mm": 0.2, "clearance_mm": 0.2,
                     "via_mm": [0.6, 0.3], "characterization_only": True},
        "shapes_tested": tested,
        "legal_fanout_count": len(legal),
        "legal_fanouts": legal,
        "coexistence_cases": coexistence,
        "clean_middle_chain_witness": clean,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if clean else 2


if __name__ == "__main__":
    raise SystemExit(main())
