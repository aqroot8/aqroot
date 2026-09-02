#!/usr/bin/env python3
"""Build and gate the complete shared SPI-A clock/data trees atomically."""

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
NETS = ("/SPI_A_SCK", "/SPI_A_MOSI")
SINGLE_ORDERS = {
    "sck": ("SPI_A_SCK_DISPLAY", "SPI_A_SCK_SD"),
    "mosi": ("SPI_A_MOSI_DISPLAY", "SPI_A_MOSI_SD"),
}
ORDERS = {
    "clock-first": ("SPI_A_SCK_DISPLAY", "SPI_A_SCK_SD", "SPI_A_MOSI_DISPLAY", "SPI_A_MOSI_SD"),
    "data-first": ("SPI_A_MOSI_DISPLAY", "SPI_A_MOSI_SD", "SPI_A_SCK_DISPLAY", "SPI_A_SCK_SD"),
}
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(board):
    result = Counter()
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            key = (item.GetNetname(), "VIA", item.GetWidth(), item.GetDrillValue(),
                   item.GetPosition().x, item.GetPosition().y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y),
                           (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        result[key] += 1
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch-order", choices=sorted(ORDERS), default="clock-first")
    parser.add_argument("--only", choices=sorted(SINGLE_ORDERS))
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    before_sha = sha256(BOARD)
    baseline = copper(pcbnew.LoadBoard(str(BOARD)))
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-spi-a-clock-data-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        routes = []
        route_order = SINGLE_ORDERS[args.only] if args.only else ORDERS[args.launch_order]
        target_nets = (("/SPI_A_SCK",) if args.only == "sck" else
                       ("/SPI_A_MOSI",) if args.only == "mosi" else NETS)
        for name in route_order:
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
        after = copper(pcbnew.LoadBoard(str(scratch)))
        removed = baseline - after
        added = after - baseline
        wrong = [list(item) for item in added if item[0] not in target_nets]
        ledger_path = work / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        rows = {r["net"]: r for r in ledger["nets"] if r["net"] in target_nets}
        promotion = (all(r["result"].get("ok") for r in routes)
                     and all(rows[n]["open_edges"] == 0 for n in target_nets)
                     and not attributable and not removed and not wrong)
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
            "launch_order": args.launch_order, "only": args.only, "routes": routes,
            "drc_exit": checked.returncode, "drc_types": dict(types),
            "attributable_drc": attributable,
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "target_open_edges": {n: rows[n]["open_edges"] for n in target_nets},
            "connectivity": ledger["connectivity"], "promotion_candidate": promotion,
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
