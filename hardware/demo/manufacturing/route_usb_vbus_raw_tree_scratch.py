#!/usr/bin/env python3
"""Route and fully gate the fitted USB_VBUS_RAW front-side power tree."""

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
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/01_POWER_TREE/USB_VBUS_RAW"
PADS = ("C20.1", "J3.A4", "J3.A9", "J3.B4", "J3.B9", "R35.1", "U10.5")
# A4/B9 and A9/B4 are coincident USB-C lands and connect as physical islands.
BRANCHES = (("R35.1", "C20.1"), ("C20.1", "J3.A9"),
            ("J3.A9", "J3.A4"), ("J3.A4", "U10.5"))
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(board):
    result = Counter()
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
    args = parser.parse_args()
    before_sha = sha256(BOARD)
    baseline = copper(pcbnew.LoadBoard(str(BOARD)))
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-vbus-raw-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        baseline_ledger_path = work / "baseline-ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(baseline_ledger_path)], check=True, stdout=subprocess.DEVNULL)
        baseline_ledger = json.loads(baseline_ledger_path.read_text())
        baseline_row = next(r for r in baseline_ledger["nets"] if r["net"] == NET)
        if baseline_row["open_edges"] == 0:
            print(json.dumps({"authoritative_board_sha256": before_sha,
                              "promotion_candidate": False,
                              "refusal": "target is already connected"}, indent=2))
            return 2
        board = qr.QBoard(scratch)
        ir.inject_existing_via_obstacles(board)
        physical = ir.physical_net_pads(board, NET)
        if {p["ref"] for p in physical} != set(PADS):
            raise RuntimeError(f"unexpected fitted pads: {sorted(p['ref'] for p in physical)}")
        pads = {p["ref"]: p for p in physical}
        routes = []
        for a, b in BRANCHES:
            routes.append(qr.connect_role(board, NET, pads[a], pads[b], "F",
                                           500_000, 200_000, 200_000, G=25_000))
            if not routes[-1].get("ok"):
                break
        board.save(scratch)
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
        wrong = [list(item) for item in added if item[0] != NET]
        ledger_path = work / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        row = next(r for r in ledger["nets"] if r["net"] == NET)
        promotion = (len(routes) == len(BRANCHES) and all(r.get("ok") for r in routes)
                     and row["open_edges"] == 0 and not attributable
                     and not removed and not wrong)
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
            "baseline_open_edges": baseline_row["open_edges"], "routes": routes,
            "drc_exit": checked.returncode, "drc_types": dict(types),
            "attributable_drc": attributable,
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "target_open_edges": row["open_edges"], "connectivity": ledger["connectivity"],
            "promotion_candidate": promotion,
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
