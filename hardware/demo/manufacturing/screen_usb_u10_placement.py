#!/usr/bin/env python3
"""Bound whether a local U10 refloor can open the fixed J3.B7 USB launch.

The connector and its mechanical placement are locked.  Every complete
connector-side N tree must first admit an F.Cu launch from J3.B7.  U10 is the
only movable footprint in this transaction, so candidates that fail that
unchanged necessary condition are pruned before accepted U10 branches are
withdrawn or replayed.
"""

import hashlib
import itertools
import json
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
import sys
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

NET = "/01_POWER_TREE/USB_D_CONN_N"
WIDTH = 230_000
CLEARANCE = 200_000
GRID = 25_000
OFFSETS_MM = (-1.0, -0.5, 0.0, 0.5, 1.0)
ROTATIONS_DEG = (0.0, 180.0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    before = sha256(BOARD)
    rows = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-u10-place-") as temporary:
        work = Path(temporary)
        for dx, dy, rotation in itertools.product(
                OFFSETS_MM, OFFSETS_MM, ROTATIONS_DEG):
            scratch = work / f"u10-{dx:+.1f}-{dy:+.1f}-{rotation:.0f}.kicad_pcb"
            scratch.write_bytes(BOARD.read_bytes())
            candidate = pcbnew.LoadBoard(str(scratch))
            u10 = candidate.FindFootprintByReference("U10")
            origin = u10.GetPosition()
            u10.SetPosition(pcbnew.VECTOR2I(
                origin.x + round(dx * 1e6), origin.y + round(dy * 1e6)))
            u10.SetOrientationDegrees(rotation)
            pcbnew.SaveBoard(str(scratch), candidate)

            board = qr.QBoard(scratch)
            ir.inject_existing_via_obstacles(board)
            pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, NET)}
            launches = board.escape(pads["J3.B7"], "F", WIDTH, WIDTH,
                                    CLEARANCE, CLEARANCE, GRID,
                                    board.ex0, board.ey0)
            rows.append({
                "u10_offset_mm": [dx, dy],
                "u10_rotation_deg": rotation,
                "j3_b7_launch_count": len(launches),
                "pruned_before_branch_replay": not launches,
                "failure": None if launches else board.escape_why[0],
            })

    viable = [row for row in rows if row["j3_b7_launch_count"]]
    report = {
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == sha256(BOARD),
        "contract": (
            "J3 fixed; U10 offsets +/-1.0 mm on 0.5 mm grid; 0/180 deg; "
            "USB F.Cu only, 0.23 mm width, 0.20 mm clearance, zero vias"
        ),
        "necessary_condition": "J3.B7 has at least one legal F.Cu launch",
        "cases_tested": len(rows),
        "cases_pruned_before_accepted_u10_branch_withdrawal": sum(
            row["pruned_before_branch_replay"] for row in rows),
        "viable_case_count": len(viable),
        "viable_cases": viable,
        "conclusion": (
            "U10-only placement cannot change the fixed J3.B7 launch wall"
            if not viable else "at least one U10 placement merits atomic branch replay"
        ),
        "promotion_candidate": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not viable and report["authoritative_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
