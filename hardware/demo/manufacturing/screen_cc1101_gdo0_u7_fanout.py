#!/usr/bin/env python3
"""Bound ordinary-via B.Cu perimeter fanouts from fitted U7.15.

The generic CC1101_GDO0 long-haul contract cannot reserve the radio endpoint.
This scratch-only screen exhaustively tests short orthogonal shoulders on both
free sides of the bottom-side module land.  It emits no partial PCB candidate.
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
NET = "/CC1101_GDO0"
REF = "U7.15"
WIDTH = CLEARANCE = 200_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge",
            "via_dangling"}

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(board, a, b):
    for shape in board.obstacles("B", NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    board.track(NET, "B", *a, *b, WIDTH)
    return True


def points(pad, shoulder_x, via):
    raw = [(pad["x"], pad["y"]), (shoulder_x, pad["y"]),
           (shoulder_x, via[1]), via]
    return [point for index, point in enumerate(raw)
            if not index or point != raw[index - 1]]


def main():
    before = sha(BOARD)
    seed = qr.QBoard(BOARD)
    pad = {p["ref"]: p for p in ir.physical_net_pads(seed, NET)}[REF]
    # U7 lands lie on a vertical B.Cu row at x=20 mm. Test east and west
    # shoulders beyond the 1.8 mm-long land, with staggered via positions.
    shoulder_xs = list(range(18_250_000, 18_751_000, 250_000))
    shoulder_xs += list(range(21_250_000, 21_751_000, 250_000))
    via_xs = range(17_000_000, 23_001_000, 250_000)
    via_ys = range(139_000_000, 141_501_000, 250_000)
    tested = 0
    legal = []
    witness_shapes = []
    board = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(board)
    for shoulder_x, x, y in itertools.product(shoulder_xs, via_xs, via_ys):
        if (shoulder_x < pad["x"]) != (x <= shoulder_x):
            continue
        tested += 1
        mark = board.mark()
        via = (x, y)
        path = points(pad, shoulder_x, via)
        if (all(board.point_free(layer, NET, *via, 600_000,
                                 CLEARANCE, CLEARANCE, 25_000)
                for layer in board.cu)
                and all(emit(board, a, b)
                        for a, b in zip(path, path[1:]))):
            board.via(NET, *via, 600_000, 300_000)
            legal.append({
                "shoulder_x_mm": shoulder_x / 1e6,
                "via_mm": [x / 1e6, y / 1e6],
                "path_mm": [[px / 1e6, py / 1e6] for px, py in path],
            })
            witness_shapes.append((via, path))
        board.revert(mark)
    drc_cases = []
    clean_witness = None
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-gdo0-u7-") as td:
        for index, (via, path) in enumerate(witness_shapes[:8]):
            candidate = Path(td) / f"candidate-{index}.kicad_pcb"
            board = qr.QBoard(BOARD)
            ir.inject_existing_via_obstacles(board)
            if not all(emit(board, a, b) for a, b in zip(path, path[1:])):
                continue
            board.via(NET, *via, 600_000, 300_000)
            board.save(candidate)
            candidate.with_suffix(".kicad_dru").write_bytes(
                BOARD.with_suffix(".kicad_dru").read_bytes())
            report = candidate.with_suffix(".drc.json")
            subprocess.run([
                "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                "--format", "json", "--units", "mm", "--severity-all",
                "--schematic-parity", "-o", str(report), str(candidate),
            ], check=True, text=True, capture_output=True)
            violations = json.loads(report.read_text()).get("violations", [])
            types = Counter(v.get("type", "unknown") for v in violations)
            attributable = [v for v in violations
                            if v.get("type") not in ACCEPTED]
            row = {"fanout_index": index, "drc_types": dict(types),
                   "attributable_drc_count": len(attributable)}
            drc_cases.append(row)
            if not attributable:
                clean_witness = legal[index]
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
        "real_drc_cases": drc_cases,
        "clean_witness": clean_witness,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if clean_witness else 2


if __name__ == "__main__":
    raise SystemExit(main())
