#!/usr/bin/env python3
"""Enumerate directional fine-pitch launches for the Demo BQ25185_SYS walls.

The generic pad escape engine searches only footprint axes and diagonals and
requires its full clearance at the pad centre.  That is intentionally too
conservative for a package-local neck leaving a fine-pitch land.  This
scratch-only screen instead sweeps bounded rays, checks the complete neck and
immediately widened trunk against retained copper, and reports only ordinary
0.90/0.40 mm B.Cu-to-In3 via sites reachable from that trunk.
"""

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

NET = "/01_POWER_TREE/BQ25185_SYS"
CASES = {
    # The current accepted USB charger refloor leaves this 0805 bypass land
    # without a generic 0.90/0.40 mm barrel site.  Keep the full SYS geometry
    # while checking whether a deterministic directional launch reaches one.
    "C26.2": {
        "neck_width": 500_000, "trunk_width": 500_000,
        "local_clearance": 250_000, "clearance": 250_000,
    },
    "U11.1": {
        "neck_width": 200_000, "trunk_width": 500_000,
        "local_clearance": 200_000, "clearance": 300_000,
    },
    "U21.3": {
        "neck_width": 250_000, "trunk_width": 800_000,
        "local_clearance": 200_000, "clearance": 250_000,
    },
}
ANGLES = tuple(range(0, 360, 5))
NECK_LENGTHS = tuple(range(200_000, 1_525_000, 25_000))
TRUNK_LENGTHS = (250_000, 500_000, 750_000, 1_000_000, 1_500_000)


def segment_blocker(board, net, width, clearance, start, end):
    """Return the first retained obstacle violating a routed segment."""
    for shape in board.obstacles("B", net):
        margin = board.margin(shape, width, clearance, clearance)
        if qr.seg_shape_dist(*start, *end, shape) < margin:
            return shape.tag
    return None


def scan():
    base = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(base)
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(base, NET)}
    rows = []
    for ref, rule in CASES.items():
        pad = pads[ref]
        candidates = []
        blockers = Counter()
        for angle in ANGLES:
            if len(candidates) >= 24:
                break
            ux = math.cos(math.radians(angle))
            uy = math.sin(math.radians(angle))
            for neck_length in NECK_LENGTHS:
                neck_end = (round(pad["x"] + ux * neck_length),
                            round(pad["y"] + uy * neck_length))
                blocker = segment_blocker(
                    base, NET, rule["neck_width"], rule["local_clearance"],
                    (pad["x"], pad["y"]), neck_end,
                )
                if blocker:
                    blockers[f"neck:{blocker}"] += 1
                    # Every longer neck on this ray contains the same blocked
                    # prefix, so continuing cannot discover a legal result.
                    break
                for trunk_length in TRUNK_LENGTHS:
                    trunk_end = (round(neck_end[0] + ux * trunk_length),
                                 round(neck_end[1] + uy * trunk_length))
                    blocker = segment_blocker(
                        base, NET, rule["trunk_width"], rule["clearance"],
                        neck_end, trunk_end,
                    )
                    if blocker:
                        blockers[f"trunk:{blocker}"] += 1
                        # Trunk lengths are ascending; a longer segment keeps
                        # this already-illegal prefix.
                        break
                    # The ray ends at its barrel.  This deliberately stricter
                    # screen avoids claiming a landing reachable only through
                    # a later unproven dogleg.
                    sites = [trunk_end] if all(
                        base.point_free(layer, NET, *trunk_end, 900_000,
                                        rule["clearance"],
                                        rule["clearance"], 25_000)
                        for layer in base.cu
                    ) else []
                    if not sites:
                        blockers["no_all_layer_via_site"] += 1
                        continue
                    candidates.append({
                        "angle_deg": angle,
                        "neck_length_mm": neck_length / 1e6,
                        "trunk_length_mm": trunk_length / 1e6,
                        "neck_end_mm": [round(v / 1e6, 4) for v in neck_end],
                        "trunk_end_mm": [round(v / 1e6, 4) for v in trunk_end],
                        "sites_mm": [[round(x / 1e6, 3), round(y / 1e6, 3)]
                                     for x, y in sites],
                    })
                    break
                if candidates and candidates[-1]["angle_deg"] == angle:
                    break
        candidates.sort(key=lambda row: (row["neck_length_mm"],
                                          row["trunk_length_mm"],
                                          row["angle_deg"]))
        rows.append({
            "pad": ref,
            "pad_position_mm": [round(pad["x"] / 1e6, 4),
                                round(pad["y"] / 1e6, 4)],
            "neck_width_mm": rule["neck_width"] / 1e6,
            "package_local_clearance_mm": rule["local_clearance"] / 1e6,
            "trunk_width_mm": rule["trunk_width"] / 1e6,
            "routed_clearance_mm": rule["clearance"] / 1e6,
            "candidate_count": len(candidates),
            "candidates": candidates[:24],
            "blockers": dict(blockers.most_common(12)),
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    rows = scan()
    after = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    report = {
        "schema": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == after,
        "net": NET,
        "method": "5deg_directional_neck_25um_length_sweep_then_reachable_In3_via",
        "angle_step_deg": 5,
        "neck_length_range_mm": [0.2, 1.5],
        "neck_length_step_mm": 0.025,
        "power_via_mm": {"diameter": 0.90, "drill": 0.40},
        "pads": rows,
        "all_wall_pads_have_candidates": all(row["candidate_count"] for row in rows),
        "promotion_candidate": False,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
