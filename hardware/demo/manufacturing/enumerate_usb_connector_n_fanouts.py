#!/usr/bin/env python3
"""Enumerate every cardinal/diagonal F.Cu launch family for USB connector N."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

NET = "/01_POWER_TREE/USB_D_CONN_N"
PADS = ("J3.A7", "J3.B7", "U10.1")
WIDTH = 230_000
CLEARANCE = 200_000
GRIDS = (50_000, 25_000)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mm(value):
    return round(value / 1e6, 6)


def main():
    before = sha256(BOARD)
    board = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(board)
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, NET)}
    if set(pads) != set(PADS):
        raise RuntimeError(f"unexpected {NET} pads: {sorted(pads)}")
    rows = []
    for grid in GRIDS:
        for ref in PADS:
            launches = board.escape(pads[ref], "F", WIDTH, WIDTH,
                                    CLEARANCE, CLEARANCE, grid,
                                    board.ex0, board.ey0)
            rows.append({
                "grid_mm": mm(grid),
                "pad": ref,
                "launch_count": len(launches),
                "failure": None if launches else board.escape_why[0],
                "launches": [{
                    "landing_mm": [mm(row["x"]), mm(row["y"])],
                    "direction": [round(row["dir"][0], 6),
                                  round(row["dir"][1], 6)],
                    "length_mm": mm(row["ln"]),
                } for row in launches],
            })
    boxed = all(row["launch_count"] == 0 for row in rows
                if row["pad"] == "J3.B7")
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == sha256(BOARD),
        "contract": "all 4 cardinal + 4 diagonal F.Cu launches; 0.23 mm width; 0.20 mm clearance; zero vias",
        "rows": rows,
        "j3_b7_boxed_at_all_grids": boxed,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if boxed and before == sha256(BOARD) else 2


if __name__ == "__main__":
    raise SystemExit(main())
