#!/usr/bin/env python3
"""Exhaustively screen package-specific U2.20 fanouts for SX1262_DIO1.

The generic ordinary-via escape and the earlier hand-picked under-body path
are blocked on the accepted board.  This scratch-only screen enumerates short
B.Cu perimeter/under-body doglegs and ordinary 0.60/0.30 mm via sites.  It
does not emit a PCB candidate: a clean witness, if any, is input to a later
atomic endpoint-plus-haul transaction.
"""

import hashlib
import argparse
import itertools
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET = "/SX1262_DIO1"
REF = "U2.20"
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


def compact(points):
    return [p for index, p in enumerate(points)
            if not index or p != points[index - 1]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--skip-real-drc", action="store_true")
    parser.add_argument("--first-witness-only", action="store_true")
    args = parser.parse_args()
    source = args.board
    before = sha(source)
    seed = qr.QBoard(source)
    pad = {p["ref"]: p for p in ir.physical_net_pads(seed, NET)}[REF]

    # U2.20 is the lower-right TSSOP land.  Include both the outward east
    # perimeter and the westward under-body corridor.  A 0.25 mm lattice is
    # finer than the ordinary via diameter and keeps the family bounded.
    shoulder_xs = range(56_750_000, 62_001_000, 250_000)
    via_xs = range(56_000_000, 63_001_000, 250_000)
    via_ys = range(86_000_000, 92_001_000, 250_000)
    tested = 0
    legal = []
    witnesses = []
    board = qr.QBoard(source)
    ir.inject_existing_via_obstacles(board)
    for shoulder_x, via_x, via_y in itertools.product(
            shoulder_xs, via_xs, via_ys):
        # Keep the via on the same side of the first shoulder excursion so a
        # candidate never doubles back across the package land.
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
                and all(emit(board, a, b)
                        for a, b in zip(path, path[1:]))):
            board.via(NET, *via, 600_000, 300_000)
            row = {"shoulder_x_mm": shoulder_x / 1e6,
                   "via_mm": [via_x / 1e6, via_y / 1e6],
                   "path_mm": [[x / 1e6, y / 1e6] for x, y in path]}
            legal.append(row)
            witnesses.append((via, path))
        board.revert(mark)
        if args.first_witness_only and legal:
            break

    drc_cases = []
    clean = None
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-dio1-u2-") as td:
        baseline_types = Counter()
        if not args.skip_real_drc and witnesses:
            baseline = Path(td) / "baseline.kicad_pcb"
            baseline.write_bytes(source.read_bytes())
            baseline.with_suffix(".kicad_dru").write_bytes(
                BOARD.with_suffix(".kicad_dru").read_bytes())
            baseline_report = baseline.with_suffix(".drc.json")
            subprocess.run([
                "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                "--format", "json", "--units", "mm", "--severity-all",
                "--schematic-parity", "-o", str(baseline_report), str(baseline),
            ], check=True, text=True, capture_output=True)
            baseline_types = Counter(
                v.get("type", "unknown") for v in
                json.loads(baseline_report.read_text()).get("violations", []))
        if args.skip_real_drc:
            witnesses = []
        for index, (via, path) in enumerate(witnesses[:16]):
            candidate = Path(td) / f"candidate-{index}.kicad_pcb"
            trial = qr.QBoard(source)
            ir.inject_existing_via_obstacles(trial)
            if not all(emit(trial, a, b) for a, b in zip(path, path[1:])):
                continue
            trial.via(NET, *via, 600_000, 300_000)
            trial.save(candidate)
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
                            if (v.get("type") not in ACCEPTED and
                                types[v.get("type", "unknown")] >
                                baseline_types[v.get("type", "unknown")])]
            drc_cases.append({"fanout_index": index, "drc_types": dict(types),
                              "attributable_drc_count": len(attributable),
                              "attributable_samples": [
                                  {"type": v.get("type"),
                                   "description": v.get("description")}
                                  for v in attributable[:4]]})
            if not attributable:
                clean = legal[index]
                break

    print(json.dumps({
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(source) == before,
        "contract": {"net": NET, "pad": REF, "native_layer": "B.Cu",
                     "width_mm": 0.2, "clearance_mm": 0.2,
                     "via_mm": [0.6, 0.3], "characterization_only": True},
        "shapes_tested": tested, "legal_fanout_count": len(legal),
        "legal_fanouts": legal, "real_drc_cases": drc_cases,
        "scratch_baseline_drc_types": dict(baseline_types),
        "clean_witness": clean, "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if clean else 2


if __name__ == "__main__":
    raise SystemExit(main())
