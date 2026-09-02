#!/usr/bin/env python3
"""Bound the independent-leg tactic for the local USB ESD differential pair."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
NAMES = ("USB_D_ESD_N", "USB_D_ESD_P")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    before = sha256(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-pair-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())

        routes = []
        for name in NAMES:
            completed = subprocess.run(
                [sys.executable, str(LOCAL), name, "--route", str(scratch)],
                check=True, text=True, capture_output=True,
            )
            routes.append(json.loads(completed.stdout))

        drc = work / "drc.json"
        completed = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = {}
        for violation in violations:
            kind = violation.get("type", "unknown")
            types[kind] = types.get(kind, 0) + 1

        board = pcbnew.LoadBoard(str(scratch))
        lengths = {}
        for name in ("/01_POWER_TREE/USB_D_ESD_N", "/01_POWER_TREE/USB_D_ESD_P"):
            lengths[name] = round(sum(
                track.GetLength() / 1e6 for track in board.GetTracks()
                if track.GetNetname() == name
            ), 6)

        attributable = [
            {"type": violation["type"], "description": violation["description"]}
            for violation in violations if violation.get("type") not in ACCEPTED
        ]
        report = {
            "schema": 1,
            "authoritative_board_sha256": before,
            "authoritative_unchanged": before == sha256(BOARD),
            "tactic": "independent sequential F.Cu routes at USB_D width/clearance",
            "routes": routes,
            "lengths_mm": lengths,
            "skew_mm": round(abs(lengths[next(iter(lengths))] - lengths[next(reversed(lengths))]), 6),
            "drc_exit": completed.returncode,
            "drc_types": types,
            "attributable_drc": attributable,
            "promotion_candidate": all(route["result"].get("ok") for route in routes) and not attributable,
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
