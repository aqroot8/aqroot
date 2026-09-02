#!/usr/bin/env python3
"""Build and gate the symmetric NFC receiver-input pair atomically."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
ORDERS = {
    "rfi1-first": ("NFC_RFI1", "NFC_RFI2"),
    "rfi2-first": ("NFC_RFI2", "NFC_RFI1"),
}
NETS = ("/04_SPI_B_RADIOS_NFC/NFC_RFI1", "/04_SPI_B_RADIOS_NFC/NFC_RFI2")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(board):
    result = Counter()
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            result[(item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu),
                    item.GetDrillValue(), p.x, p.y)] += 1
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y),
                           (item.GetEnd().x, item.GetEnd().y)))
            result[(item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)] += 1
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch-order", choices=sorted(ORDERS), default="rfi1-first")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--screen-c17-east", action="store_true",
                        help="characterize C17 at (40.0,30.25); never promotable")
    args = parser.parse_args()
    before_sha = sha256(BOARD)
    baseline_copper = copper(pcbnew.LoadBoard(str(BOARD)))
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-rfi-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        if args.screen_c17_east:
            moved = pcbnew.LoadBoard(str(scratch))
            moved.FindFootprintByReference("C17").SetPosition(
                pcbnew.VECTOR2I(40_000_000, 30_250_000)
            )
            moved.Save(str(scratch))
        routes = []
        for name in ORDERS[args.launch_order]:
            run = subprocess.run([sys.executable, str(LOCAL), name, "--route", str(scratch)],
                                 check=True, text=True, capture_output=True)
            routes.append(json.loads(run.stdout))
        drc = work / "drc.json"
        checked = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = Counter(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED]
        after_copper = copper(pcbnew.LoadBoard(str(scratch)))
        removed = baseline_copper - after_copper
        added = after_copper - baseline_copper
        wrong = [list(item) for item in added if item[0] not in NETS]
        ledger_path = work / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        rows = {r["net"]: r for r in ledger["nets"] if r["net"] in NETS}
        promotion = (all(r["result"].get("ok") for r in routes)
                     and all(rows[n]["open_edges"] == 0 for n in NETS)
                     and not attributable and not removed and not wrong
                     and not args.screen_c17_east)
        candidate = scratch.read_bytes()
        if args.candidate and promotion:
            args.candidate.write_bytes(candidate)
        if args.promote:
            if not promotion or sha256(BOARD) != before_sha:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(candidate)
        report = {
            "schema": 1, "authoritative_board_sha256": before_sha,
            "authoritative_unchanged": sha256(BOARD) == before_sha,
            "tactic": "atomic symmetric NFC receiver-input B.Cu/no-via pair",
            "c17_screen_position_mm": ([40.0, 30.25] if args.screen_c17_east else None),
            "launch_order": args.launch_order, "routes": routes,
            "drc_exit": checked.returncode, "drc_types": dict(types),
            "attributable_drc": attributable,
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "target_open_edges": {n: rows[n]["open_edges"] for n in NETS},
            "connectivity": ledger["connectivity"], "promotion_candidate": promotion,
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
