#!/usr/bin/env python3
"""Route and fully gate the local ST25R3916 VDD_D/VDD_A trees atomically."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from itertools import permutations, product
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
NETS = ("/04_SPI_B_RADIOS_NFC/NFC_VDD_D", "/04_SPI_B_RADIOS_NFC/NFC_VDD_A")
LEGS = {
    NETS[0]: ("NFC_VDD_D_UPPER", "NFC_VDD_D_LOWER"),
    NETS[1]: ("NFC_VDD_A_UPPER", "NFC_VDD_A_LOWER"),
}
CASES = tuple(
    tuple(leg for net in net_order for leg in leg_orders[net])
    for net_order in permutations(NETS)
    for choices in product((0, 1), repeat=2)
    for leg_orders in ({
        net: LEGS[net] if choices[index] == 0 else tuple(reversed(LEGS[net]))
        for index, net in enumerate(NETS)
    },)
)
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(path):
    result = Counter()
    board = pcbnew.LoadBoard(str(path))
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu),
                   item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y),
                           (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        result[key] += 1
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--case", type=int, choices=range(len(CASES)), default=0)
    args = parser.parse_args()
    before = sha256(BOARD)
    baseline = copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-vdd-da-") as tmp:
        scratch = Path(tmp) / "candidate.kicad_pcb"
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        routes = []
        for leg in CASES[args.case]:
            run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)],
                                 text=True, capture_output=True, check=True)
            routes.append(json.loads(run.stdout))
            if not routes[-1]["result"].get("ok"):
                break
        drc = scratch.with_suffix(".drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                        "--format", "json", "--units", "mm", "--severity-all",
                        "--schematic-parity", "-o", str(drc), str(scratch)],
                       text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = Counter(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED]
        ledger_path = scratch.with_suffix(".ledger.json")
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        targets = {row["net"]: row["open_edges"] for row in ledger["nets"] if row["net"] in NETS}
        after = copper(scratch)
        removed = baseline - after
        added = after - baseline
        wrong = [list(item) for item in added if item[0] not in NETS]
        ok = (len(routes) == 4 and all(r["result"].get("ok") for r in routes)
              and targets == {net: 0 for net in NETS} and not attributable
              and not removed and not wrong and not any(item[1] == "VIA" for item in added))
        if ok and args.candidate:
            args.candidate.write_bytes(scratch.read_bytes())
        if args.promote:
            if not ok or sha256(BOARD) != before:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(scratch.read_bytes())
        report = {
            "schema": 1, "authoritative_board_sha256": before,
            "authoritative_unchanged": sha256(BOARD) == before,
            "case": args.case, "legs": CASES[args.case], "routes": routes,
            "drc_types": dict(types), "attributable_drc": attributable,
            "target_open_edges": targets, "connectivity": ledger["connectivity"],
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "promotion_candidate": ok, "candidate_sha256": sha256(scratch),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
