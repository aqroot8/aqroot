#!/usr/bin/env python3
"""Bound the J3 VBUS escape and qualify the existing POFV process geometry."""

import hashlib
import json
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

NET = "/01_POWER_TREE/USB_VBUS_RAW"
LANDS = ("J3.A4", "J3.A9", "J3.B4", "J3.B9")
WIDTHS = (500_000, 350_000, 300_000, 250_000, 200_000, 150_000)
CLEARANCE = 200_000
POFV_DIAMETER = 350_000
POFV_DRILL = 200_000


def mm(value):
    return round(value / 1e6, 6)


def main():
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    board = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    if not set(LANDS) <= set(pads):
        raise RuntimeError(f"missing VBUS lands: {sorted(set(LANDS) - set(pads))}")

    launches = []
    for width in WIDTHS:
        for ref in ("J3.A4", "J3.A9"):
            rows = board.escape(pads[ref], "F", width, width, CLEARANCE,
                                CLEARANCE, 25_000, board.ex0, board.ey0)
            launches.append({
                "land": ref,
                "width_mm": mm(width),
                "count": len(rows),
                "failure": None if rows else board.escape_why[0],
                "landings_mm": [[mm(r["x"]), mm(r["y"])] for r in rows],
            })

    raw = pcbnew.LoadBoard(str(BOARD))
    j3 = raw.FindFootprintByReference("J3")
    physical = {p.GetNumber(): p for p in j3.Pads() if p.GetNumber()}
    a9 = physical["A9"]
    a12 = physical["A12"]
    b5 = physical["B5"]
    side_gaps = {
        "A9_to_A12_mm": mm(abs(a9.GetPosition().x - a12.GetPosition().x)
                            - (a9.GetSize().x + a12.GetSize().x) // 2),
        "A9_to_B5_mm": mm(abs(a9.GetPosition().x - b5.GetPosition().x)
                           - (a9.GetSize().x + b5.GetSize().x) // 2),
    }
    usable = {name.replace("_mm", "_usable_after_clearance_mm"):
              round(gap - 2 * mm(CLEARANCE), 6)
              for name, gap in side_gaps.items()}
    pad_width = a9.GetSize().x
    annular = (POFV_DIAMETER - POFV_DRILL) // 2
    edge_copper = (pad_width - POFV_DIAMETER) // 2

    result = {
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "contract": "J3 VBUS F.Cu neck screen at 0.20 mm clearance; existing 0.35/0.20 mm POFV geometry",
        "launches": launches,
        "decisive_left_land": {
            **side_gaps,
            **usable,
            "positive_width_planar_throat": all(value > 0 for value in usable.values()),
        },
        "pofv": {
            "diameter_mm": mm(POFV_DIAMETER),
            "drill_mm": mm(POFV_DRILL),
            "annular_ring_mm": mm(annular),
            "vbus_land_width_mm": mm(pad_width),
            "land_copper_each_side_mm": mm(edge_copper),
            # D-257's already-fitted Q3.3 POFV is exactly 0.35/0.20 mm:
            # 0.075 mm plated annulus and 0.125 mm host-pad copper per side.
            "fits_existing_approved_process_geometry": annular >= 75_000 and edge_copper >= 125_000,
        },
        "conclusion": "PLANAR_POUR_OR_NECK_CANNOT_ESCAPE_A9_B4; POFV_BOUNDARY_QUALIFIED",
        "promotion_candidate": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if (result["authoritative_unchanged"]
                 and not result["decisive_left_land"]["positive_width_planar_throat"]
                 and result["pofv"]["fits_existing_approved_process_geometry"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
