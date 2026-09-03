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
    # The accepted USB charger refloor boxes this 0805 bypass land.  Preserve
    # the full SYS haul geometry while testing whether one short turn after a
    # legal straight prefix can reach an ordinary all-layer barrel site.
    "C26.2": {"neck_width": 500_000, "trunk_width": 500_000,
               "local_clearance": 250_000, "clearance": 250_000},
    # The full-tree transaction reaches this bulk SYS capacitor first after a
    # qualified C26 refloor.  Keep the same governed SYS haul and power-via
    # contract while searching its independent local pocket.
    "C27.1": {"neck_width": 500_000, "trunk_width": 500_000,
               "local_clearance": 250_000, "clearance": 250_000},
    # Successor wall exposed only after the qualified C26/C27 refloor pair.
    # It is another bulk SYS capacitor land, so retain the identical governed
    # haul and ordinary power-via contract.
    "C28.1": {"neck_width": 500_000, "trunk_width": 500_000,
               "local_clearance": 250_000, "clearance": 250_000},
    # The joint C26/C27/C28 transaction reaches the accessory-boost input
    # inductor next.  Screen this ordinary SYS land with the same locked
    # current-path geometry before extending the atomic full-tree replay.
    "L4.1": {"neck_width": 500_000, "trunk_width": 500_000,
              "local_clearance": 250_000, "clearance": 250_000},
    # D-269 applies to the SYS/BAT current-path relationship even inside the
    # charger breakout.  Screening the neck at only 0.20 mm produced apparent
    # landings that real KiCad DRC correctly rejected at exactly 0.20 mm.
    "U11.1": {"neck_width": 200_000, "trunk_width": 500_000,
               "local_clearance": 300_000, "clearance": 300_000},
    # TPS63020 VOUT land.  The package neck may use the 0.20 mm fine-pitch
    # escape, but the SYS haul and ordinary power barrel retain the governed
    # 0.50 mm / 0.25 mm contract outside the package courtyard.
    "U12.10": {"neck_width": 200_000, "trunk_width": 500_000,
                "local_clearance": 200_000, "clearance": 250_000},
    "U21.3": {"neck_width": 250_000, "trunk_width": 800_000,
               "local_clearance": 200_000, "clearance": 250_000},
}
ANGLES = tuple(range(0, 360, 5))
NECK_LENGTHS = tuple(range(200_000, 1_525_000, 25_000))
TRUNK_LENGTHS = (250_000, 500_000, 750_000, 1_000_000, 1_500_000)
DOGLEG_LENGTHS = tuple(range(250_000, 2_025_000, 50_000))


def obstacle_index(board, shapes, width, clearance):
    """Index obstacles by their exact expanded collision bounding boxes."""
    buckets = {}
    for shape in shapes:
        margin = board.margin(shape, width, clearance, clearance)
        x0, y0, x1, y1 = shape.bbox(margin)
        for bx in range(math.floor(x0 / VIA_BUCKET),
                        math.floor(x1 / VIA_BUCKET) + 1):
            for by in range(math.floor(y0 / VIA_BUCKET),
                            math.floor(y1 / VIA_BUCKET) + 1):
                buckets.setdefault((bx, by), []).append((shape, margin))
    return buckets


def segment_blocker(index, start, end):
    seen = set()
    x0, x1 = sorted((start[0], end[0]))
    y0, y1 = sorted((start[1], end[1]))
    for bx in range(math.floor(x0 / VIA_BUCKET),
                    math.floor(x1 / VIA_BUCKET) + 1):
        for by in range(math.floor(y0 / VIA_BUCKET),
                        math.floor(y1 / VIA_BUCKET) + 1):
            for shape, margin in index.get((bx, by), ()):
                identity = id(shape)
                if identity in seen:
                    continue
                seen.add(identity)
                sx0, sy0, sx1, sy1 = shape.bbox(margin)
                if (x1 < sx0 or x0 > sx1 or y1 < sy0 or y0 > sy1):
                    continue
                if qr.seg_shape_dist(*start, *end, shape) < margin:
                    return shape.tag
    return None


VIA_BUCKET = 2_000_000


def via_index(board, obstacles_by_layer, clearance):
    """Index exact expanded via obstacles into coarse 2 mm spatial buckets."""
    width = 900_000
    guard = 25_000 * 0.75
    indexes = {}
    for layer, shapes in obstacles_by_layer.items():
        buckets = {}
        for shape in shapes:
            margin = board.margin(shape, width, clearance, clearance) + guard
            x0, y0, x1, y1 = shape.bbox(margin)
            for bx in range(math.floor(x0 / VIA_BUCKET),
                            math.floor(x1 / VIA_BUCKET) + 1):
                for by in range(math.floor(y0 / VIA_BUCKET),
                                math.floor(y1 / VIA_BUCKET) + 1):
                    buckets.setdefault((bx, by), []).append((shape, margin))
        indexes[layer] = buckets
    return indexes


def via_free(board, indexes, point):
    """Fast equivalent of QBoard.point_free() for a fixed 0.90 mm barrel.

    The generic helper walks every board shape for every candidate.  This
    bounded enumerator can reject by expanded bounding box first, preserving
    the exact margin, distance, edge, and 25 um guard tests while making the
    exhaustive dogleg family practical.
    """
    width = 900_000
    guard = 25_000 * 0.75
    edge_limit = qr.EDGE_CLR + width / 2.0 + guard
    x, y = point
    if not (board.ex0 + edge_limit <= x <= board.ex1 - edge_limit and
            board.ey0 + edge_limit <= y <= board.ey1 - edge_limit):
        return False
    bucket = (math.floor(x / VIA_BUCKET), math.floor(y / VIA_BUCKET))
    for layer in board.cu:
        for shape, margin in indexes[layer].get(bucket, ()):
            if shape.dist(x, y) < margin:
                return False
    return True


def scan(selected_pads=None, board_path=BOARD):
    board = qr.QBoard(board_path)
    ir.inject_existing_via_obstacles(board)
    obstacles_by_layer = {layer: tuple(board.obstacles(layer, NET))
                          for layer in board.cu}
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, NET)}
    rows = []
    for ref, rule in CASES.items():
        if selected_pads and ref not in selected_pads:
            continue
        pad = pads[ref]
        indexes = via_index(board, obstacles_by_layer, rule["clearance"])
        bcu_shapes = obstacles_by_layer["B"]
        neck_index = obstacle_index(board, bcu_shapes, rule["neck_width"],
                                    rule["local_clearance"])
        trunk_index = obstacle_index(board, bcu_shapes, rule["trunk_width"],
                                     rule["clearance"])
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
                blocker = segment_blocker(neck_index,
                                          (pad["x"], pad["y"]), neck_end)
                if blocker:
                    blockers[f"neck:{blocker}"] += 1
                    break
                for trunk_length in TRUNK_LENGTHS:
                    anchor = (round(neck_end[0] + ux * trunk_length),
                              round(neck_end[1] + uy * trunk_length))
                    blocker = segment_blocker(trunk_index, neck_end, anchor)
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
                    blocker = segment_blocker(trunk_index, anchor, site)
                    if blocker:
                        blockers[f"dogleg:{blocker}"] += 1
                        break
                    if site in seen_sites or not via_free(board, indexes, site):
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
    parser.add_argument("--board", type=Path, default=BOARD,
                        help="board copy to screen (defaults to authority)")
    parser.add_argument("--pad", action="append", choices=tuple(CASES),
                        help="screen only this wall pad (repeatable)")
    args = parser.parse_args()
    before = hashlib.sha256(args.board.read_bytes()).hexdigest()
    rows = scan(set(args.pad) if args.pad else None, args.board)
    unchanged = before == hashlib.sha256(args.board.read_bytes()).hexdigest()
    report = {
        "schema": 1, "board": str(args.board), "net": NET,
        "authoritative_board_sha256": before,
        # Keep the original key for callers while naming scratch-board checks
        # accurately for the new pocket-refloor screen.
        "authoritative_unchanged": unchanged,
        "screened_board_unchanged": unchanged,
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
    return 0 if report["screened_board_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
