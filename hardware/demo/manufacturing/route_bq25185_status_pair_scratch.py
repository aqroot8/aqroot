#!/usr/bin/env python3
"""Atomically route and gate the fitted BQ25185 STAT1/STAT2 trees."""

import argparse, hashlib, itertools, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
TREES = {
    "/BQ25185_STAT1": ("BQ25185_STAT1_U2_PULLUP", "BQ25185_STAT1_PULLUP_CHARGER",
                       "BQ25185_STAT1_PULLUP_TP"),
    "/BQ25185_STAT2": ("BQ25185_STAT2_U2_PULLUP", "BQ25185_STAT2_PULLUP_CHARGER",
                       "BQ25185_STAT2_PULLUP_TP"),
}
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def copper(path):
    out = Counter(); board = pcbnew.LoadBoard(str(path))
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition(); key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu),
                                            item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y),
                           (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        out[key] += 1
    return out

def run_case(work, tree_order, branch_orders, baseline):
    scratch = work / ("-".join(n.rsplit('/', 1)[-1] for n in tree_order) +
                      "-" + "".join(map(str, branch_orders)) + ".kicad_pcb")
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    routes = []
    for net, reverse in zip(tree_order, branch_orders):
        legs = TREES[net][::-1] if reverse else TREES[net]
        for leg in legs:
            run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)],
                                 text=True, capture_output=True, check=True)
            routes.append(json.loads(run.stdout))
            if not routes[-1]["result"].get("ok"): break
        if not routes[-1]["result"].get("ok"): break
    drc = scratch.with_suffix(".drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                    "--format", "json", "--units", "mm", "--severity-all",
                    "--schematic-parity", "-o", str(drc), str(scratch)],
                   text=True, capture_output=True)
    violations = json.loads(drc.read_text()).get("violations", [])
    types = Counter(v.get("type", "unknown") for v in violations)
    attributable = [v for v in violations if v.get("type") not in ACCEPTED]
    ledger_path = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(ledger_path)],
                   check=True, stdout=subprocess.DEVNULL)
    ledger = json.loads(ledger_path.read_text())
    targets = {r["net"]: r["open_edges"] for r in ledger["nets"] if r["net"] in TREES}
    after = copper(scratch); removed = baseline - after; added = after - baseline
    ok = (len(routes) == 6 and all(r["result"].get("ok") for r in routes)
          and all(targets[n] == 0 for n in TREES) and not attributable and not removed
          and not any(k[0] not in TREES for k in added))
    return {"tree_order": tree_order, "branch_orders_reversed": branch_orders,
            "routes": routes, "drc_types": dict(types),
            "attributable_drc_count": len(attributable), "target_open_edges": targets,
            "connectivity": ledger["connectivity"],
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "promotion_candidate": ok,
            "candidate_sha256": sha(scratch), "path": scratch}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", type=Path)
    ap.add_argument("--promote", action="store_true"); args = ap.parse_args()
    before = sha(BOARD); baseline = copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-bq25185-status-") as td:
        cases = [run_case(Path(td), order, reversals, baseline)
                 for order in itertools.permutations(TREES)
                 for reversals in itertools.product((False, True), repeat=2)]
        winners = [c for c in cases if c["promotion_candidate"]]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD) != before: raise RuntimeError("refuse promotion")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for case in cases: case.pop("path", None)
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before, "cases": cases,
        "promotion_candidates": len(winners)}, indent=2, sort_keys=True))
    return 0 if winners else 2

if __name__ == "__main__": raise SystemExit(main())
