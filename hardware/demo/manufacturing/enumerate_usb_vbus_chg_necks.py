#!/usr/bin/env python3
"""Qualify package-local necks for the two USB_VBUS_CHG escape walls.

The whole-tree router keeps every haul at 0.50/0.25 mm.  This bounded screen
only permits a narrower B.Cu launch from R91.1 or U11.10, widens to the haul
width, and requires an immediately reachable 0.90/0.40 mm all-layer via.
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

NET = "/01_POWER_TREE/USB_VBUS_CHG"
CASES = {
    # The 0.80 mm resistor land can carry a 0.30 mm local launch while retaining
    # the net's 0.25 mm routed clearance outside any package exception.
    "R91.1": {"neck_width": 300_000, "local_clearance": 250_000,
              "angles": tuple(range(120, 241, 20))},
    # U11 is already governed by the board's fine-pitch 0.20/0.20 mm courtyard
    # rules.  The exception ends before the 0.50/0.25 mm haul begins.
    "U11.10": {"neck_width": 200_000, "local_clearance": 200_000,
                "angles": tuple(range(-80, 81, 20))},
}
TRUNK_WIDTH = 500_000
CLEARANCE = 250_000
VIA_DIAMETER = 900_000
VIA_DRILL = 400_000
NECK_LENGTHS = tuple(range(200_000, 1_501_000, 100_000))
VIA_OFFSETS = tuple(range(-2_500_000, 2_500_001, 500_000))


def blocker(board, shapes, width, clearance, start, end):
    for shape in shapes:
        if qr.seg_shape_dist(*start, *end, shape) < board.margin(
                shape, width, clearance, clearance):
            return shape.tag
    return None


def compact(points):
    return tuple(point for index, point in enumerate(points)
                 if not index or point != points[index - 1])


def trunk_paths(start, end):
    yield "direct", (start, end)
    yield "x_then_y", compact((start, (end[0], start[1]), end))
    yield "y_then_x", compact((start, (start[0], end[1]), end))


def scan():
    seed = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(seed)
    shapes = tuple(seed.obstacles("B", NET))
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(seed, NET)}
    rows = []
    for ref, rule in CASES.items():
        pad = pads[ref]
        candidates = []
        blockers = Counter()
        via_cache = {}
        for angle in rule["angles"]:
            ux = math.cos(math.radians(angle))
            uy = math.sin(math.radians(angle))
            for neck_length in NECK_LENGTHS:
                neck_end = (round(pad["x"] + ux * neck_length),
                            round(pad["y"] + uy * neck_length))
                hit = blocker(seed, shapes, rule["neck_width"],
                              rule["local_clearance"],
                              (pad["x"], pad["y"]), neck_end)
                if hit:
                    blockers[f"neck:{hit}"] += 1
                    break
                found_on_ray = False
                sites = sorted(((neck_end[0] + dx, neck_end[1] + dy)
                                for dx in VIA_OFFSETS for dy in VIA_OFFSETS
                                if dx or dy),
                               key=lambda site: ((site[0] - neck_end[0]) ** 2 +
                                                 (site[1] - neck_end[1]) ** 2))
                for via in sites:
                    if via not in via_cache:
                        via_cache[via] = all(
                            seed.point_free(layer, NET, *via, VIA_DIAMETER,
                                            CLEARANCE, CLEARANCE, 25_000)
                            for layer in seed.cu)
                    if not via_cache[via]:
                        blockers["no_all_layer_via_site"] += 1
                        continue
                    for family, points in trunk_paths(neck_end, via):
                        hits = [blocker(seed, shapes, TRUNK_WIDTH, CLEARANCE, a, b)
                                for a, b in zip(points, points[1:])]
                        if any(hits):
                            blockers[f"trunk:{next(h for h in hits if h)}"] += 1
                            continue
                        candidates.append({
                            "angle_deg": angle,
                            "neck_length_mm": neck_length / 1e6,
                            "trunk_family": family,
                            "neck_end_mm": [round(v / 1e6, 4) for v in neck_end],
                            "via_mm": [round(v / 1e6, 4) for v in via],
                        })
                        found_on_ray = True
                        break
                    if found_on_ray:
                        break
                if found_on_ray:
                    break
        candidates.sort(key=lambda row: (row["neck_length_mm"],
                                          row["angle_deg"]))
        rows.append({
            "pad": ref,
            "pad_position_mm": [pad["x"] / 1e6, pad["y"] / 1e6],
            "neck_width_mm": rule["neck_width"] / 1e6,
            "package_clearance_mm": rule["local_clearance"] / 1e6,
            "candidate_count": len(candidates),
            "candidates": candidates[:24],
            "blockers": dict(blockers.most_common(12)),
        })
    return rows


def main():
    global BOARD
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    args = parser.parse_args()
    BOARD = args.board
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    rows = scan()
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "net": NET,
        "method": "5deg package-neck ray then full-width trunk and all-layer via",
        "haul_contract": {"width_mm": 0.5, "clearance_mm": 0.25,
                          "via_mm": [0.9, 0.4]},
        "pads": rows,
        "all_wall_pads_have_candidates": all(row["candidate_count"] for row in rows),
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
