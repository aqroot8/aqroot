#!/usr/bin/env python3
"""Enumerate short dogleg power-via landings for the Demo SYS package walls.

This extends the directional-neck screen without changing authoritative copper.
Every legal neck plus immediately widened radial trunk anchor is retained, then
a second full-width B.Cu segment is swept to an ordinary 0.90/0.40 mm through-
via site.  The search is deliberately finite and deterministic.
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
    "U11.1": {"neck_width": 200_000, "trunk_width": 500_000,
               "local_clearance": 200_000, "clearance": 300_000},
    "U21.3": {"neck_width": 250_000, "trunk_width": 800_000,
               "local_clearance": 200_000, "clearance": 250_000},
}
ANGLES = tuple(range(0, 360, 5))
NECK_LENGTHS = tuple(range(200_000, 1_525_000, 25_000))
TRUNK_LENGTHS = (250_000, 500_000, 750_000, 1_000_000, 1_500_000)
DOGLEG_LENGTHS = tuple(range(250_000, 2_025_000, 50_000))


def segment_blocker(board, width, clearance, start, end):
    for shape in board.obstacles("B", NET):
        margin = board.margin(shape, width, clearance, clearance)
        sx0, sy0, sx1, sy1 = shape.bbox(margin)
        if (max(start[0], end[0]) < sx0 or min(start[0], end[0]) > sx1 or
                max(start[1], end[1]) < sy0 or min(start[1], end[1]) > sy1):
            continue
        if qr.seg_shape_dist(*start, *end, shape) < margin:
            return shape.tag
    return None


def via_free(board, point, clearance):
    return all(board.point_free(layer, NET, *point, 900_000, clearance,
                                clearance, 25_000) for layer in board.cu)


def scan():
    board = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(board)
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, NET)}
    rows = []
    for ref, rule in CASES.items():
        pad = pads[ref]
        anchors = []
        candidates = []
        blockers = Counter()
        seen_anchors = set()
        seen_sites = set()
        for angle in ANGLES:
            ux = math.cos(math.radians(angle))
            uy = math.sin(math.radians(angle))
            for neck_length in NECK_LENGTHS:
                neck_end = (round(pad["x"] + ux * neck_length),
                            round(pad["y"] + uy * neck_length))
                blocker = segment_blocker(board, rule["neck_width"],
                                          rule["local_clearance"],
                                          (pad["x"], pad["y"]), neck_end)
                if blocker:
                    blockers[f"neck:{blocker}"] += 1
                    break
                for trunk_length in TRUNK_LENGTHS:
                    anchor = (round(neck_end[0] + ux * trunk_length),
                              round(neck_end[1] + uy * trunk_length))
                    blocker = segment_blocker(board, rule["trunk_width"],
                                              rule["clearance"], neck_end, anchor)
                    if blocker:
                        blockers[f"trunk:{blocker}"] += 1
                        break
                    if anchor in seen_anchors:
                        continue
                    seen_anchors.add(anchor)
                    anchors.append((angle, neck_length, trunk_length,
                                    neck_end, anchor))

        for angle, neck_length, trunk_length, neck_end, anchor in anchors:
            for dogleg_angle in ANGLES:
                ux = math.cos(math.radians(dogleg_angle))
                uy = math.sin(math.radians(dogleg_angle))
                for dogleg_length in DOGLEG_LENGTHS:
                    site = (round(anchor[0] + ux * dogleg_length),
                            round(anchor[1] + uy * dogleg_length))
                    blocker = segment_blocker(board, rule["trunk_width"],
                                              rule["clearance"], anchor, site)
                    if blocker:
                        blockers[f"dogleg:{blocker}"] += 1
                        break
                    if site in seen_sites or not via_free(board, site, rule["clearance"]):
                        blockers["dogleg:no_all_layer_via_site"] += 1
                        continue
                    seen_sites.add(site)
                    candidates.append({
                        "launch_angle_deg": angle,
                        "neck_length_mm": neck_length / 1e6,
                        "trunk_length_mm": trunk_length / 1e6,
                        "neck_end_mm": [round(v / 1e6, 4) for v in neck_end],
                        "anchor_mm": [round(v / 1e6, 4) for v in anchor],
                        "dogleg_angle_deg": dogleg_angle,
                        "dogleg_length_mm": dogleg_length / 1e6,
                        "via_mm": [round(v / 1e6, 4) for v in site],
                    })
                    break
                if len(candidates) >= 48:
                    break
            if len(candidates) >= 48:
                break
        candidates.sort(key=lambda row: (row["neck_length_mm"] +
                                          row["trunk_length_mm"] +
                                          row["dogleg_length_mm"],
                                          row["launch_angle_deg"],
                                          row["dogleg_angle_deg"]))
        rows.append({
            "pad": ref,
            "pad_position_mm": [round(pad["x"] / 1e6, 4),
                                round(pad["y"] / 1e6, 4)],
            "legal_directional_anchor_count": len(anchors),
            "candidate_count": len(candidates),
            "candidates": candidates[:24],
            "blockers": dict(blockers.most_common(16)),
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    rows = scan()
    report = {
        "schema": 1, "board": str(BOARD.relative_to(ROOT)), "net": NET,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "method": "all_legal_directional_anchors_then_5deg_50um_short_dogleg",
        "dogleg_length_range_mm": [0.25, 2.0], "dogleg_length_step_mm": 0.05,
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
    return 0 if report["authoritative_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
