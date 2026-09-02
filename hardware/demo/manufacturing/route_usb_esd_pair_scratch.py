#!/usr/bin/env python3
"""Build and gate the coordinated local USB ESD differential pair."""

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
NAMES = ("USB_D_ESD_N", "USB_D_ESD_P")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def normalize_pair_transition(path: Path) -> None:
    """Replace the sole loose P transition with the fixed-gap pair transition."""
    board = pcbnew.LoadBoard(str(path))
    net = board.FindNet("/01_POWER_TREE/USB_D_ESD_P")
    old = {(53_300_000, 144_425_000), (53_600_000, 144_725_000)}
    matches = []
    for track in board.GetTracks():
        endpoints = {
            (track.GetStart().x, track.GetStart().y),
            (track.GetEnd().x, track.GetEnd().y),
        }
        if track.GetNetname() == net.GetNetname() and endpoints == old:
            matches.append(track)
    if len(matches) != 1:
        raise RuntimeError(f"expected one loose P transition, found {len(matches)}")
    board.Remove(matches[0])
    points = [
        ((53_300_000, 144_425_000), (53_300_000, 144_800_000)),
        ((53_300_000, 144_800_000), (53_600_000, 144_725_000)),
    ]
    for start, end in points:
        track = pcbnew.PCB_TRACK(board)
        track.SetNet(net)
        track.SetLayer(pcbnew.F_Cu)
        track.SetWidth(230_000)
        track.SetStart(pcbnew.VECTOR2I(*start))
        track.SetEnd(pcbnew.VECTOR2I(*end))
        board.Add(track)
    pcbnew.SaveBoard(str(path), board)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_geometry_sha256(path: Path) -> str:
    board = pcbnew.LoadBoard(str(path))
    geometry = []
    for track in board.GetTracks():
        if "USB_D_ESD_" not in track.GetNetname():
            continue
        start = (track.GetStart().x, track.GetStart().y)
        end = (track.GetEnd().x, track.GetEnd().y)
        geometry.append((track.GetNetname(), track.GetLayerName(), track.GetWidth(), *sorted((start, end))))
    encoded = json.dumps(sorted(geometry), separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
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
        normalize_pair_transition(scratch)

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
            "tactic": "coordinated F.Cu pair with fixed-gap shared corridor and bounded endpoint fanouts",
            "routes": routes,
            "lengths_mm": lengths,
            "skew_mm": round(abs(lengths[next(iter(lengths))] - lengths[next(reversed(lengths))]), 6),
            "drc_exit": completed.returncode,
            "drc_types": types,
            "attributable_drc": attributable,
            "promotion_candidate": all(route["result"].get("ok") for route in routes) and not attributable,
        }
        candidate = scratch.read_bytes()
        if args.candidate and report["promotion_candidate"]:
            args.candidate.write_bytes(candidate)
        report["pair_geometry_sha256"] = pair_geometry_sha256(scratch)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
