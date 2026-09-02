#!/usr/bin/env python3
"""Atomically screen and gate the five-land retained WAKE_INT_N tree."""

import argparse, hashlib, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/WAKE_INT_N"
LEGS = ("WAKE_INT_U3_U2", "WAKE_INT_U2_Q10", "WAKE_INT_Q10_U1", "WAKE_INT_U1_R3")
# Four rotations put every branch first on pristine geometry while retaining
# a bounded atomic interaction screen for the branches that succeed.
ORDERS = tuple(LEGS[i:] + LEGS[:i] for i in range(len(LEGS)))
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def copper(path):
    out = Counter()
    for item in pcbnew.LoadBoard(str(path)).GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y), (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        out[key] += 1
    return out

def run_case(work, index, order, baseline):
    scratch = work / f"case-{index:02d}.kicad_pcb"
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    routes = []
    for leg in order:
        run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)],
                             text=True, capture_output=True, check=True)
        route = json.loads(run.stdout); routes.append(route)
        if not route["result"].get("ok"): break
    ledger_path = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(ledger_path)],
                   check=True, stdout=subprocess.DEVNULL)
    ledger = json.loads(ledger_path.read_text())
    target = next(row for row in ledger["nets"] if row["net"] == NET)
    after = copper(scratch); removed = baseline - after; added = after - baseline
    complete = len(routes) == len(LEGS) and all(r["result"].get("ok") for r in routes)
    types = Counter(); attributable = []
    if complete:
        drc = scratch.with_suffix(".drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                        "--format", "json", "--units", "mm", "--severity-all",
                        "--schematic-parity", "-o", str(drc), str(scratch)],
                       check=True, text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types.update(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED]
    promotion = (complete and target["open_edges"] == 0 and not attributable and
                 not removed and not any(key[0] != NET for key in added))
    terminal = routes[-1]["result"]
    return {"order": order, "routes_completed": sum(r["result"].get("ok", False) for r in routes),
            "terminal_leg": routes[-1]["name"], "terminal_reason": terminal.get("reason", "OK"),
            "terminal_attempt": terminal.get("attempt"), "routes": routes,
            "drc_types": dict(types), "attributable_drc_count": len(attributable),
            "target_open_edges": target["open_edges"], "connectivity": ledger["connectivity"],
            "removed_accepted_copper_items": sum(removed.values()), "added_items": sum(added.values()),
            "wrong_net_additions": sum(n for key, n in added.items() if key[0] != NET),
            "promotion_candidate": promotion, "candidate_sha256": sha(scratch), "path": scratch}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", type=Path); ap.add_argument("--promote", action="store_true")
    args = ap.parse_args(); before = sha(BOARD); baseline = copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-wake-int-") as td:
        cases = [run_case(Path(td), i, order, baseline)
                 for i, order in enumerate(ORDERS)]
        winners = [case for case in cases if case["promotion_candidate"]]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD) != before: raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for case in cases: case.pop("path", None)
    summary = Counter((case["terminal_leg"], case["terminal_reason"]) for case in cases)
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before, "cases_tested": len(cases),
        "terminal_outcomes": {f"{leg}:{reason}": count for (leg, reason), count in summary.items()},
        "cases": cases, "promotion_candidates": len(winners)}, indent=2, sort_keys=True))
    return 0 if winners else 2

if __name__ == "__main__": raise SystemExit(main())
