#!/usr/bin/env python3
"""Atomically refloor retained complete nets around the BQ25185_SYS tree."""

import argparse, hashlib, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

import enumerate_bq25185_sys_dogleg_landings as landings
import route_bq25185_sys_scratch as sysroute

BOARD = sysroute.BOARD
IR_NET = "/IR_RX_GPIO44"
ILIM_NET = "/01_POWER_TREE/ILIM_VSET"
L1_NET = "Net-(L1-Pad1)"
NFC_ANT_B_NET = "/04_SPI_B_RADIOS_NFC/NFC_ANT_B"
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
        if item.GetNetname() in (IR_NET, ILIM_NET, L1_NET, NFC_ANT_B_NET):
            board.Remove(item); removed += 1
    board.Save(str(path)); return removed

def replay_l1_pad1(path):
    """Replay the complete accepted five-segment switch-node route exactly."""
    board = pcbnew.LoadBoard(str(path)); net = board.FindNet(L1_NET)
    geometry = (
        ((67.600, 102.800), (68.100, 102.800), 0.200),
        ((68.100, 102.800), (68.875, 102.800), 0.400),
        ((68.875, 102.800), (68.875, 94.400), 0.400),
        ((68.875, 94.400), (65.415, 94.400), 0.400),
        ((65.415, 94.400), (65.415, 96.600), 0.400),
    )
    for start, end, width in geometry:
        track = pcbnew.PCB_TRACK(board); track.SetNet(net); track.SetLayer(pcbnew.B_Cu)
        track.SetWidth(round(width * 1e6))
        track.SetStart(pcbnew.VECTOR2I(*(round(v * 1e6) for v in start)))
        track.SetEnd(pcbnew.VECTOR2I(*(round(v * 1e6) for v in end)))
        board.Add(track)
    board.Save(str(path))
    return {"ok": True, "objects": len(geometry), "mode": "exact_accepted_geometry"}

def replay_nfc_ant_b(path):
    """Replay the complete accepted antenna-B tree from the authority exactly."""
    source = pcbnew.LoadBoard(str(BOARD)); board = pcbnew.LoadBoard(str(path))
    net = board.FindNet(NFC_ANT_B_NET); objects = 0
    for item in source.GetTracks():
        if item.GetNetname() != NFC_ANT_B_NET:
            continue
        if item.GetClass() == "PCB_VIA":
            clone = pcbnew.PCB_VIA(board)
            clone.SetPosition(item.GetPosition()); clone.SetWidth(item.GetWidth())
            clone.SetDrill(item.GetDrillValue()); clone.SetViaType(item.GetViaType())
            clone.SetLayerPair(item.TopLayer(), item.BottomLayer())
        else:
            clone = pcbnew.PCB_TRACK(board)
            clone.SetStart(item.GetStart()); clone.SetEnd(item.GetEnd())
            clone.SetWidth(item.GetWidth()); clone.SetLayer(item.GetLayer())
        clone.SetNet(net); board.Add(clone); objects += 1
    board.Save(str(path))
    return {"ok": objects > 0, "objects": objects,
            "mode": "exact_authoritative_complete_net_geometry"}

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
        for pad in ("C26.2", "C27.1", "C28.1", "L4.1"):
            scan_board = seed
            if pad == "L4.1":
                scan_board = work / "l4-scan.kicad_pcb"
                scan_board.write_bytes(seed.read_bytes())
                subprocess.run([sys.executable, str(Path(__file__).with_name(
                    "screen_bq25185_sys_c26_pocket_refloor.py")), "--prepare",
                    str(scan_board), "--net", NFC_ANT_B_NET], check=True,
                    text=True, capture_output=True)
            scan = subprocess.run([sys.executable, str(Path(landings.__file__)),
                                   "--board", str(scan_board), "--pad", pad],
                                  check=True, text=True, capture_output=True)
            scans[pad] = last_json(scan.stdout)["pads"][0]["candidates"]
        # L4 is the newly introduced coexistence boundary.  Vary its qualified
        # witnesses first so a bounded 24-case run covers the complete L4 set
        # instead of spending the window on C28 variants behind one bad L4 site.
        cases = [(a, b, c, d) for a in scans["C26.2"]
                 for b in scans["C27.1"] for c in scans["C28.1"]
                 for d in scans["L4.1"]]
        for index, (c26_candidate, c27_candidate, c28_candidate,
                    l4_candidate) in enumerate(cases[:args.case_limit]):
            scratch = work / f"case-{index}.kicad_pcb"
            for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
                scratch.with_suffix(suffix).write_bytes(seed.with_suffix(suffix).read_bytes())
            routed = json.loads(subprocess.run([
                sys.executable, str(Path(sysroute.__file__)), "--route", str(scratch),
                "--c26-candidate-json", json.dumps(c26_candidate),
                "--c27-candidate-json", json.dumps(c27_candidate),
                "--c28-candidate-json", json.dumps(c28_candidate),
                "--l4-candidate-json", json.dumps(l4_candidate),
                "--u12-10-first",
            ], check=True, text=True, capture_output=True).stdout)
            successful = [join for join in routed["joins"] if join.get("ok")]
            sys_complete = len(routed["reservations"]) == len(sysroute.FITTED) and all(row.get("ok") for row in routed["reservations"]) and len(successful) == len(sysroute.FITTED)-1
            replay = []
            if sys_complete:
                replay.append({"leg": "L1_PAD1", "result": replay_l1_pad1(scratch)})
                replay.append({"leg": "NFC_ANT_B", "result": replay_nfc_ant_b(scratch)})
                for leg in REPLAY:
                    run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)], text=True, capture_output=True)
                    record = json.loads(run.stdout); replay.append({"leg": leg, **record})
                    if run.returncode or not record["result"].get("ok"): break
            complete = sys_complete and len(replay) == len(REPLAY) + 2 and all(row["result"].get("ok") for row in replay)
            types = Counter(); attributable = []; opens = {}; drc_exit = None
            if complete:
                drc = scratch.with_suffix(".drc.json")
                run = subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board", "--format", "json", "--units", "mm", "--severity-all", "--schematic-parity", "-o", str(drc), str(scratch)], text=True, capture_output=True)
                drc_exit = run.returncode; violations = json.loads(drc.read_text()).get("violations", []); types = Counter(v.get("type", "unknown") for v in violations); attributable = [v for v in violations if v.get("type") not in ACCEPTED]
                ledger_path = scratch.with_suffix(".ledger.json"); subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
                ledger = json.loads(ledger_path.read_text()); opens = {row["net"]: row["open_edges"] for row in ledger["nets"] if row["net"] in (sysroute.NET, IR_NET, ILIM_NET, L1_NET, NFC_ANT_B_NET)}
            after = measured_copper(scratch); removed = baseline-after; added = after-baseline
            refloor_nets = (IR_NET, ILIM_NET, L1_NET, NFC_ANT_B_NET)
            wrong_removed = sum(n for key,n in removed.items() if key[0] not in refloor_nets)
            wrong_added = sum(n for key,n in added.items() if key[0] not in (*refloor_nets, sysroute.NET))
            ok = complete and all(opens.get(net) == 0 for net in (sysroute.NET, *refloor_nets)) and not attributable and not wrong_removed and not wrong_added
            row = {"case": index, "reservation_order": "u12_10_before_l4", "c26_candidate": c26_candidate, "c27_candidate": c27_candidate, "c28_candidate": c28_candidate, "l4_candidate": l4_candidate, "sys_complete": sys_complete, "sys_route": routed, "refloor_replay": replay, "open_edges": opens, "drc_exit": drc_exit, "drc_types": dict(types), "attributable_drc_count": len(attributable), "removed_wrong_net_items": wrong_removed, "added_wrong_net_items": wrong_added, "promotion_candidate": ok, "path": scratch}
            rows.append(row)
            if ok: winner = row; break
        if winner and args.candidate: args.candidate.write_bytes(winner["path"].read_bytes())
        if args.promote:
            if not winner or sha(BOARD) != before: raise RuntimeError("refuse promotion: atomic gate failed or authority changed")
            BOARD.write_bytes(winner["path"].read_bytes())
        for row in rows: row.pop("path", None)
    print(json.dumps({"schema": 6, "authoritative_board_sha256": before, "authoritative_unchanged": sha(BOARD) == before, "withdrawn_complete_refloor_items": removed_refloor, "c26_candidates_available": len(scans["C26.2"]), "c27_candidates_available": len(scans["C27.1"]), "c28_candidates_available": len(scans["C28.1"]), "l4_candidates_available": len(scans["L4.1"]), "reservation_order": "u12_10_before_l4", "case_order": "c26_c27_c28_l4_with_l4_varying_first", "candidate_quadruples_available": len(cases), "cases_tested": len(rows), "promotion_candidate": winner is not None, "cases": rows}, indent=2, sort_keys=True))
    return 0 if winner else 2

if __name__ == "__main__": raise SystemExit(main())
