#!/usr/bin/env python3
"""Screen a shared U9.30/U9.31 SPI-B breakout around the QFN perimeter.

The generic reservation screen cannot leave either adjacent land.  This
scratch-only successor explicitly follows the native F.Cu north perimeter,
staggering ordinary through-vias only after both 0.20 mm launches coexist.
It never emits partial or authoritative copper.
"""

import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
WIDTH = CLEARANCE = 200_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge",
            "via_dangling"}

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(board, net, a, b):
    for shape in board.obstacles("F", net):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    board.track(net, "F", *a, *b, WIDTH)
    return True


def path_points(pad, via, shoulder_y):
    points = [(pad["x"], pad["y"]), (pad["x"], shoulder_y),
              (via[0], shoulder_y), via]
    return [p for i, p in enumerate(points) if not i or p != points[i - 1]]


def legal_shapes(net, pad):
    shapes = []
    # U9.30/U9.31 are top-edge F.Cu lands.  Extend beyond the 0.75 mm pad,
    # then fan sideways on successive shoulders before planting a via.
    shoulder_ys = range(32_750_000, 34_001_000, 250_000)
    via_xs = range(30_750_000, 35_251_000, 250_000)
    via_ys = range(33_000_000, 35_251_000, 250_000)
    qb = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(qb)
    tested = 0
    for shoulder_y, x, y in itertools.product(shoulder_ys, via_xs, via_ys):
        if y < shoulder_y:
            continue
        tested += 1
        mark = qb.mark()
        via = (x, y)
        path = path_points(pad, via, shoulder_y)
        if (all(qb.point_free(layer, net, *via, 600_000,
                              CLEARANCE, CLEARANCE, 25_000)
                for layer in qb.cu)
                and all(emit(qb, net, a, b)
                        for a, b in zip(path, path[1:]))):
            shapes.append((via, shoulder_y, path))
        qb.revert(mark)
    return tested, shapes


def main():
    before = sha(BOARD)
    seed = qr.QBoard(BOARD)
    specs = []
    for net, ref in (("/SPI_B_SCK", "U9.30"),
                     ("/SPI_B_MOSI", "U9.31")):
        pads = {p["ref"]: p for p in ir.physical_net_pads(seed, net)}
        specs.append((net, ref, pads[ref]))
    individual = [legal_shapes(net, pad) for net, _ref, pad in specs]
    tested_pairs = geometric_pairs = 0
    drc_rows = []
    winner = None
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-u9-spib-fanout-") as td:
        work = Path(td)
        for left, right, order in itertools.product(
                individual[0][1], individual[1][1], ((0, 1), (1, 0))):
            tested_pairs += 1
            shapes = (left, right)
            # Ordinary 0.60 mm vias need 0.20 mm edge clearance.
            if ((left[0][0] - right[0][0]) ** 2
                    + (left[0][1] - right[0][1]) ** 2 < 1_000_000 ** 2):
                continue
            qb = qr.QBoard(BOARD)
            ir.inject_existing_via_obstacles(qb)
            ok = True
            for index in order:
                net = specs[index][0]
                via, _shoulder, path = shapes[index]
                if not all(qb.point_free(layer, net, *via, 600_000,
                                         CLEARANCE, CLEARANCE, 25_000)
                           for layer in qb.cu):
                    ok = False
                    break
                if not all(emit(qb, net, a, b)
                           for a, b in zip(path, path[1:])):
                    ok = False
                    break
                qb.via(net, *via, 600_000, 300_000)
            if not ok:
                continue
            geometric_pairs += 1
            candidate = work / f"candidate-{tested_pairs}.kicad_pcb"
            qb.save(candidate)
            candidate.with_suffix(".kicad_dru").write_bytes(
                BOARD.with_suffix(".kicad_dru").read_bytes())
            drc = candidate.with_suffix(".drc.json")
            subprocess.run([
                "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                "--format", "json", "--units", "mm", "--severity-all",
                "--schematic-parity", "-o", str(drc), str(candidate),
            ], check=True, text=True, capture_output=True)
            violations = json.loads(drc.read_text()).get("violations", [])
            types = Counter(v.get("type", "unknown") for v in violations)
            attributable = [v for v in violations
                            if v.get("type") not in ACCEPTED]
            row = {
                "order": [specs[i][1] for i in order],
                "vias_mm": [[s[0][0] / 1e6, s[0][1] / 1e6] for s in shapes],
                "shoulder_y_mm": [s[1] / 1e6 for s in shapes],
                "paths_mm": [[[x / 1e6, y / 1e6] for x, y in s[2]]
                             for s in shapes],
                "drc_types": dict(types),
                "attributable_drc_count": len(attributable),
            }
            drc_rows.append(row)
            if not attributable:
                winner = row
                break
            if len(drc_rows) >= 4:
                break
    report = {
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before,
        "contract": {"native_layer": "F.Cu", "width_mm": 0.2,
                     "clearance_mm": 0.2, "via_mm": [0.6, 0.3],
                     "characterization_only": True},
        "individual_shapes_tested": [row[0] for row in individual],
        "legal_individual_fanouts": [len(row[1]) for row in individual],
        "pair_orders_tested": tested_pairs,
        "geometric_pairs": geometric_pairs,
        "real_drc_cases": drc_rows,
        "clean_pair_found": winner is not None,
        "winner": winner,
        "promotion_candidate": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if winner else 2


if __name__ == "__main__":
    raise SystemExit(main())
