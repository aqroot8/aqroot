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
PLACEMENTS = {
    # Rotate Y1 to match U9's vertical pin order and exchange the two load
    # capacitors so each remains on the outside of its oscillator arm.
    "rotate-swap-caps": {
        "Y1": (28.6, 30.0, 180.0),
        "C79": (28.6, 32.9, 0.0),
        "C80": (28.6, 27.1, 0.0),
    },
}


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
    parser.add_argument("--rotate-crystal-180", action="store_true",
                        help="characterize an in-place Y1 pin-order correction")
    parser.add_argument("--placement", choices=sorted(PLACEMENTS),
                        help="screen a coherent Y1/C79/C80 placement transaction")
    args = parser.parse_args()
    before = sha256(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-crystal-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        if args.rotate_crystal_180 and args.placement:
            parser.error("select either --rotate-crystal-180 or --placement")
        placement_delta = {}
        if args.rotate_crystal_180:
            rotated = pcbnew.LoadBoard(str(scratch))
            crystal = rotated.FindFootprintByReference("Y1")
            crystal.SetOrientationDegrees((crystal.GetOrientationDegrees() + 180.0) % 360.0)
            pcbnew.SaveBoard(str(scratch), rotated)
        elif args.placement:
            placed = pcbnew.LoadBoard(str(scratch))
            for ref, (x_mm, y_mm, angle) in PLACEMENTS[args.placement].items():
                footprint = placed.FindFootprintByReference(ref)
                old = footprint.GetPosition()
                placement_delta[ref] = {
                    "from_mm": [old.x / 1e6, old.y / 1e6,
                                footprint.GetOrientationDegrees()],
                    "to_mm": [x_mm, y_mm, angle],
                }
                footprint.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
                footprint.SetOrientationDegrees(angle)
            pcbnew.SaveBoard(str(scratch), placed)
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
        electrically_complete = all(route["result"].get("ok") for route in routes)
        # Rotation proves the pin-order cause, but the generic sequential router
        # sends a load-capacitor branch around the cluster.  It is deliberately
        # characterization-only until Y1/C79/C80 are screened as one placement
        # transaction and the complete oscillator geometry is reviewed.
        geometry_reviewed = bool(args.placement)
        promotion = electrically_complete and not attributable and geometry_reviewed
        candidate = scratch.read_bytes()
        if args.candidate and promotion:
            args.candidate.write_bytes(candidate)
        report = {"schema": 1, "authoritative_board_sha256": before,
                  "authoritative_unchanged": before == sha256(BOARD),
                  "tactic": "atomic local NFC crystal/load-cap pair; B.Cu, no vias",
                  "crystal_rotation_delta_deg": 180 if args.rotate_crystal_180 else 0,
                  "placement_tactic": args.placement,
                  "placement_delta": placement_delta,
                  "electrically_complete": electrically_complete,
                  "oscillator_geometry_reviewed": geometry_reviewed,
                  "launch_order": args.launch_order,
                  "routes": routes, "lengths_mm": lengths, "drc_exit": run.returncode,
                  "drc_types": types, "attributable_drc": attributable,
                  "promotion_candidate": promotion, "pair_geometry_sha256": digest,
                  "candidate_sha256": hashlib.sha256(candidate).hexdigest()}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
