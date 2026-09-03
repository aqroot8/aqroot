#!/usr/bin/env python3
"""Atomically refloor IR_RX_GPIO44 and ILIM_VSET around BQ25185_SYS."""

import argparse, hashlib, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

import enumerate_bq25185_sys_dogleg_landings as landings
import route_bq25185_sys_scratch as sysroute

BOARD = sysroute.BOARD
IR_NET = "/IR_RX_GPIO44"
ILIM_NET = "/01_POWER_TREE/ILIM_VSET"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
IR_LEGS = ("IR_RX_MCU_TP", "IR_RX_TP_RECEIVER")
REPLAY = (*IR_LEGS, "ILIM_VSET")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def last_json(text):
    decoder = json.JSONDecoder(); records = []
    for offset, char in enumerate(text):
        if char != "{": continue
        try:
            record, end = decoder.raw_decode(text[offset:]); records.append((end, record))
        except json.JSONDecodeError: pass
    if not records: raise RuntimeError("subprocess emitted no JSON")
    return max(records, key=lambda row: row[0])[1]

def copper(path):
    out = Counter()
    for item in pcbnew.LoadBoard(str(path)).GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition(); key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y), (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        out[key] += 1
    return out

def measured_copper(path):
    def freeze(value):
        return tuple(freeze(item) for item in value) if isinstance(value, list) else value
    run = subprocess.run([sys.executable, str(Path(__file__)), "--measure", str(path)],
                         check=True, text=True, capture_output=True)
    return Counter({freeze(row[0]): row[1] for row in last_json(run.stdout)["items"]})

def withdraw_refloor_nets(path):
    board = pcbnew.LoadBoard(str(path)); removed = 0
    for item in list(board.GetTracks()):
        if item.GetNetname() in (IR_NET, ILIM_NET): board.Remove(item); removed += 1
    board.Save(str(path)); return removed

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", type=Path); ap.add_argument("--promote", action="store_true"); ap.add_argument("--case-limit", type=int, default=24); ap.add_argument("--measure", type=Path, help=argparse.SUPPRESS); args = ap.parse_args()
    if args.measure:
        print(json.dumps({"items": [[list(key), count] for key, count in copper(args.measure).items()]})); return 0
    before = sha(BOARD); baseline = measured_copper(BOARD); rows = []; winner = None
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-sys-ir-refloor-") as td:
        work = Path(td); seed = work / "seed.kicad_pcb"
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            seed.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        removed_refloor = withdraw_refloor_nets(seed)
        scans = {}
        for pad in ("C26.2", "C27.1"):
            scan = subprocess.run([sys.executable, str(Path(landings.__file__)),
                                   "--board", str(seed), "--pad", pad],
                                  check=True, text=True, capture_output=True)
            scans[pad] = last_json(scan.stdout)["pads"][0]["candidates"]
        pairs = [(a, b) for a in scans["C26.2"] for b in scans["C27.1"]]
        for index, (c26_candidate, c27_candidate) in enumerate(pairs[:args.case_limit]):
            scratch = work / f"case-{index}.kicad_pcb"
            for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
                scratch.with_suffix(suffix).write_bytes(seed.with_suffix(suffix).read_bytes())
            routed = json.loads(subprocess.run([
                sys.executable, str(Path(sysroute.__file__)), "--route", str(scratch),
                "--c26-candidate-json", json.dumps(c26_candidate),
                "--c27-candidate-json", json.dumps(c27_candidate),
            ], check=True, text=True, capture_output=True).stdout)
            successful = [join for join in routed["joins"] if join.get("ok")]
            sys_complete = len(routed["reservations"]) == len(sysroute.FITTED) and all(row.get("ok") for row in routed["reservations"]) and len(successful) == len(sysroute.FITTED)-1
            replay = []
            if sys_complete:
                for leg in REPLAY:
                    run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)], text=True, capture_output=True)
                    record = json.loads(run.stdout); replay.append({"leg": leg, **record})
                    if run.returncode or not record["result"].get("ok"): break
            complete = sys_complete and len(replay) == len(REPLAY) and all(row["result"].get("ok") for row in replay)
            types = Counter(); attributable = []; opens = {}; drc_exit = None
            if complete:
                drc = scratch.with_suffix(".drc.json")
                run = subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board", "--format", "json", "--units", "mm", "--severity-all", "--schematic-parity", "-o", str(drc), str(scratch)], text=True, capture_output=True)
                drc_exit = run.returncode; violations = json.loads(drc.read_text()).get("violations", []); types = Counter(v.get("type", "unknown") for v in violations); attributable = [v for v in violations if v.get("type") not in ACCEPTED]
                ledger_path = scratch.with_suffix(".ledger.json"); subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
                ledger = json.loads(ledger_path.read_text()); opens = {row["net"]: row["open_edges"] for row in ledger["nets"] if row["net"] in (sysroute.NET, IR_NET, ILIM_NET)}
            after = measured_copper(scratch); removed = baseline-after; added = after-baseline
            wrong_removed = sum(n for key,n in removed.items() if key[0] not in (IR_NET, ILIM_NET))
            wrong_added = sum(n for key,n in added.items() if key[0] not in (IR_NET, ILIM_NET, sysroute.NET))
            ok = complete and all(opens.get(net) == 0 for net in (sysroute.NET, IR_NET, ILIM_NET)) and not attributable and not wrong_removed and not wrong_added
            row = {"case": index, "c26_candidate": c26_candidate, "c27_candidate": c27_candidate, "sys_complete": sys_complete, "sys_route": routed, "refloor_replay": replay, "open_edges": opens, "drc_exit": drc_exit, "drc_types": dict(types), "attributable_drc_count": len(attributable), "removed_wrong_net_items": wrong_removed, "added_wrong_net_items": wrong_added, "promotion_candidate": ok, "path": scratch}
            rows.append(row)
            if ok: winner = row; break
        if winner and args.candidate: args.candidate.write_bytes(winner["path"].read_bytes())
        if args.promote:
            if not winner or sha(BOARD) != before: raise RuntimeError("refuse promotion: atomic gate failed or authority changed")
            BOARD.write_bytes(winner["path"].read_bytes())
        for row in rows: row.pop("path", None)
    print(json.dumps({"schema": 2, "authoritative_board_sha256": before, "authoritative_unchanged": sha(BOARD) == before, "withdrawn_complete_refloor_items": removed_refloor, "c26_candidates_available": len(scans["C26.2"]), "c27_candidates_available": len(scans["C27.1"]), "candidate_pairs_available": len(pairs), "cases_tested": len(rows), "promotion_candidate": winner is not None, "cases": rows}, indent=2, sort_keys=True))
    return 0 if winner else 2

if __name__ == "__main__": raise SystemExit(main())
