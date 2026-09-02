#!/usr/bin/env python3
"""Build and gate both three-pad NFC receive arms as one transaction."""

import argparse
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
NAMES = ("NFC_RXA_UPPER", "NFC_RXA_LOWER", "NFC_RXB_LOWER", "NFC_RXB_UPPER")
NETS = (
    "/04_SPI_B_RADIOS_NFC/NFC_RXA",
    "/04_SPI_B_RADIOS_NFC/NFC_RXB",
)
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_geometry(path: Path) -> tuple[dict[str, float], str]:
    board = pcbnew.LoadBoard(str(path))
    geometry = []
    lengths = {}
    for net in NETS:
        tracks = [track for track in board.GetTracks() if track.GetNetname() == net]
        lengths[net] = round(sum(track.GetLength() for track in tracks) / 1e6, 6)
        for track in tracks:
            ends = sorted(((track.GetStart().x, track.GetStart().y),
                           (track.GetEnd().x, track.GetEnd().y)))
            geometry.append((net, track.GetLayerName(), track.GetWidth(), *ends))
    digest = hashlib.sha256(
        json.dumps(sorted(geometry), separators=(",", ":")).encode()
    ).hexdigest()
    return lengths, digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    before = sha256(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-rx-") as temporary:
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
        attributable = [
            {"type": violation["type"], "description": violation["description"]}
            for violation in violations if violation.get("type") not in ACCEPTED
        ]
        lengths, geometry_sha = pair_geometry(scratch)
        promotion = all(route["result"].get("ok") for route in routes) and not attributable
        candidate = scratch.read_bytes()
        if args.candidate and promotion:
            args.candidate.write_bytes(candidate)
        report = {
            "schema": 1,
            "authoritative_board_sha256": before,
            "authoritative_unchanged": before == sha256(BOARD),
            "tactic": "atomic symmetric NFC receive outer-layer, no-via pair",
            "routes": routes,
            "lengths_mm": lengths,
            "arm_length_delta_mm": round(abs(lengths[NETS[0]] - lengths[NETS[1]]), 6),
            "drc_exit": completed.returncode,
            "drc_types": types,
            "attributable_drc": attributable,
            "promotion_candidate": promotion,
            "pair_geometry_sha256": geometry_sha,
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
