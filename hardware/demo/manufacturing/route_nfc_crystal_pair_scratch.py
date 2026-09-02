#!/usr/bin/env python3
"""Build and gate the ST25R3916 crystal and load-capacitor pair atomically."""

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
ORDERS = {
    "xin-first": ("NFC_XIN_CRYSTAL", "NFC_XIN_CAP", "NFC_XOUT_CRYSTAL", "NFC_XOUT_CAP"),
    "xout-first": ("NFC_XOUT_CRYSTAL", "NFC_XOUT_CAP", "NFC_XIN_CRYSTAL", "NFC_XIN_CAP"),
}
NETS = ("/04_SPI_B_RADIOS_NFC/NFC_XIN", "/04_SPI_B_RADIOS_NFC/NFC_XOUT")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry(path: Path) -> tuple[dict[str, float], str]:
    board = pcbnew.LoadBoard(str(path))
    items = []
    lengths = {}
    for net in NETS:
        tracks = [item for item in board.GetTracks() if item.GetNetname() == net]
        lengths[net] = round(sum(item.GetLength() for item in tracks) / 1e6, 6)
        for item in tracks:
            ends = sorted(((item.GetStart().x, item.GetStart().y),
                           (item.GetEnd().x, item.GetEnd().y)))
            items.append((net, item.GetLayerName(), item.GetWidth(), *ends))
    digest = hashlib.sha256(json.dumps(sorted(items), separators=(",", ":")).encode()).hexdigest()
    return lengths, digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--launch-order", choices=sorted(ORDERS), default="xout-first")
    args = parser.parse_args()
    before = sha256(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-crystal-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        routes = []
        for name in ORDERS[args.launch_order]:
            run = subprocess.run([sys.executable, str(LOCAL), name, "--route", str(scratch)],
                                 check=True, text=True, capture_output=True)
            routes.append(json.loads(run.stdout))
        drc = work / "drc.json"
        run = subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                              "--format", "json", "--units", "mm", "--severity-all",
                              "--schematic-parity", "-o", str(drc), str(scratch)],
                             text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = {}
        for violation in violations:
            kind = violation.get("type", "unknown")
            types[kind] = types.get(kind, 0) + 1
        attributable = [{"type": v["type"], "description": v["description"]}
                        for v in violations if v.get("type") not in ACCEPTED]
        lengths, digest = geometry(scratch)
        promotion = all(route["result"].get("ok") for route in routes) and not attributable
        candidate = scratch.read_bytes()
        if args.candidate and promotion:
            args.candidate.write_bytes(candidate)
        report = {"schema": 1, "authoritative_board_sha256": before,
                  "authoritative_unchanged": before == sha256(BOARD),
                  "tactic": "atomic local NFC crystal/load-cap pair; B.Cu, no vias",
                  "launch_order": args.launch_order,
                  "routes": routes, "lengths_mm": lengths, "drc_exit": run.returncode,
                  "drc_types": types, "attributable_drc": attributable,
                  "promotion_candidate": promotion, "pair_geometry_sha256": digest,
                  "candidate_sha256": hashlib.sha256(candidate).hexdigest()}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
