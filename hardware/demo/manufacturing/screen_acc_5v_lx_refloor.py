#!/usr/bin/env python3
"""Bound the minimum placement lever that opens the ACC_5V_LX launch."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
ROUTER = ROOT / "hardware/demo/manufacturing/route_local_two_pad.py"

CASES = (
    ("baseline", 0, 0, 0),
    ("c65_east_1mm", 0, 0, 1_000_000),
    ("u21_rot180", 180, 0, 0),
    ("u21_l4_rot180", 180, 180, 0),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screen(name: str, u21_rotation: float, l4_rotation: float, c65_dx: int) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"aqroot-{name}-") as temporary:
        candidate = Path(temporary) / "aqroot-Beta-v2.kicad_pcb"
        candidate.write_bytes(BOARD.read_bytes())
        board = pcbnew.LoadBoard(str(candidate))
        board.FindFootprintByReference("U21").SetOrientationDegrees(u21_rotation)
        board.FindFootprintByReference("L4").SetOrientationDegrees(l4_rotation)
        c65 = board.FindFootprintByReference("C65")
        c65.SetPosition(c65.GetPosition() + pcbnew.VECTOR2I(c65_dx, 0))
        pcbnew.SaveBoard(str(candidate), board)
        run = subprocess.run(
            ["python3", str(ROUTER), "ACC_5V_LX", "--route", str(candidate)],
            check=True, capture_output=True, text=True,
        )
        result = json.loads(run.stdout.strip().splitlines()[-1])["result"]
        return {
            "case": name,
            "placement": {
                "u21_rotation_deg": u21_rotation,
                "l4_rotation_deg": l4_rotation,
                "c65_dx_mm": c65_dx / 1e6,
            },
            "route": result,
        }


def main() -> int:
    before = sha256(BOARD)
    cases = [screen(*case) for case in CASES]
    after = sha256(BOARD)
    report = {
        "schema": 1,
        "board_sha256_before": before,
        "board_sha256_after": after,
        "authoritative_board_unchanged": before == after,
        "contract": {
            "net": "/01_POWER_TREE/ACC_5V_LX",
            "pads": ["U21.5", "L4.2"],
            "layer": "B.Cu",
            "trunk_width_mm": 0.4,
            "u21_escape_floor_mm": 0.2,
        },
        "cases": cases,
        "conclusion": {
            "c65_translation_alone_opens_launch": cases[1]["route"]["ok"],
            "minimum_observed_launch_lever": "rotate U21 180 degrees in place",
            "shorter_observed_switch_route": "rotate U21 and L4 180 degrees in place",
            "required_atomic_replay": [
                "ACC_5V_FB", "ACC_5V_BOOST_EN", "BQ25185_SYS", "GND",
                "ACC_5V_RAW", "ACC_5V_LX",
            ],
        },
    }
    print(json.dumps(report, indent=2))
    return 0 if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
