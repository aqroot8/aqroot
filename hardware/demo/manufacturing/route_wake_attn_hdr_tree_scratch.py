#!/usr/bin/env python3
"""Route and fully gate the retained Community Port wake/attention tree."""

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
NET = "/09_COMMUNITY_HEADER/WAKE_ATTN_N_HDR"
ORDERS = {
    "resistor-first": ("WAKE_ATTN_HDR_TVS_RESISTOR", "WAKE_ATTN_HDR_TVS_CONNECTOR"),
    "connector-first": ("WAKE_ATTN_HDR_TVS_CONNECTOR", "WAKE_ATTN_HDR_TVS_RESISTOR"),
}
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(path):
    result = Counter()
    for item in pcbnew.LoadBoard(str(path)).GetTracks():
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


def run_case(work, order, legs, baseline):
    scratch = work / f"{order}.kicad_pcb"
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    routes = []
    for leg in legs:
        run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)],
                             text=True, capture_output=True, check=True)
        routes.append(json.loads(run.stdout))
        if not routes[-1]["result"].get("ok"):
            break
    drc = scratch.with_suffix(".drc.json")
    checked = subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(drc), str(scratch),
    ], text=True, capture_output=True)
    violations = json.loads(drc.read_text()).get("violations", [])
    types = Counter(v.get("type", "unknown") for v in violations)
    attributable = [v for v in violations if v.get("type") not in ACCEPTED]
    ledger_path = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                    str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
    ledger = json.loads(ledger_path.read_text())
    row = next(r for r in ledger["nets"] if r["net"] == NET)
    after = copper(scratch); removed = baseline - after; added = after - baseline
    wrong = [list(item) for item in added if item[0] != NET]
    promotion = (len(routes) == 2 and all(r["result"].get("ok") for r in routes)
                 and row["open_edges"] == 0 and not attributable and not removed
                 and not wrong)
    return {"order": order, "routes": routes, "drc_exit": checked.returncode,
            "drc_types": dict(types), "attributable_drc_count": len(attributable),
            "target_open_edges": row["open_edges"], "connectivity": ledger["connectivity"],
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "promotion_candidate": promotion, "candidate_sha256": sha256(scratch),
            "path": scratch}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args(); before = sha256(BOARD); baseline = copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-wake-attn-preflight-") as temporary:
        ledger_path = Path(temporary) / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(BOARD),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        row = next(r for r in ledger["nets"] if r["net"] == NET)
        if row["open_edges"] == 0:
            print(json.dumps({"schema": 1, "authoritative_board_sha256": before,
                              "authoritative_unchanged": sha256(BOARD) == before,
                              "preflight_result": "REFUSED_CONNECTED_TARGET",
                              "target_open_edges": 0, "cases_tested": 0,
                              "promotion_candidates": 0}, indent=2, sort_keys=True))
            return 0
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-wake-attn-") as temporary:
        cases = [run_case(Path(temporary), order, legs, baseline)
                 for order, legs in ORDERS.items()]
        winners = [case for case in cases if case["promotion_candidate"]]
        if winners and args.candidate:
            args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha256(BOARD) != before:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for case in cases:
            case.pop("path", None)
        report = {"schema": 1, "authoritative_board_sha256": before,
                  "authoritative_unchanged": sha256(BOARD) == before,
                  "cases": cases, "promotion_candidates": len(winners),
                  "selected_candidate_sha256": winners[0]["candidate_sha256"] if winners else None}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if winners else 2


if __name__ == "__main__":
    raise SystemExit(main())
