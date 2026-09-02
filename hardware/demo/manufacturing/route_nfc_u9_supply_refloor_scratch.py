#!/usr/bin/env python3
"""Atomically move U9 east, replay its accepted fanout, and close VDD_D/A."""

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
ACCEPTED_DRC = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
REPLAY_NETS = {
    "/04_SPI_B_RADIOS_NFC/NFC_XIN",
    "/04_SPI_B_RADIOS_NFC/NFC_XOUT",
    "/04_SPI_B_RADIOS_NFC/NFC_RFO1",
    "/04_SPI_B_RADIOS_NFC/NFC_RFO2",
    "/04_SPI_B_RADIOS_NFC/NFC_AGDC",
    "/04_SPI_B_RADIOS_NFC/NFC_VDD_AM",
}
SUPPLY_NETS = {
    "/04_SPI_B_RADIOS_NFC/NFC_VDD_D",
    "/04_SPI_B_RADIOS_NFC/NFC_VDD_A",
}
ALL_NETS = REPLAY_NETS | SUPPLY_NETS
ORDERS = {
    "signals-first": (
        "NFC_XOUT_CRYSTAL", "NFC_XIN_CRYSTAL", "NFC_RFO2", "NFC_RFO1",
        "NFC_AGDC_UPPER", "NFC_AGDC_LOWER",
        "NFC_VDD_AM_UPPER", "NFC_VDD_AM_LOWER",
        "NFC_VDD_D_UPPER", "NFC_VDD_D_LOWER",
        "NFC_VDD_A_UPPER", "NFC_VDD_A_LOWER",
    ),
    "supplies-first": (
        "NFC_VDD_D_UPPER", "NFC_VDD_D_LOWER",
        "NFC_VDD_A_UPPER", "NFC_VDD_A_LOWER",
        "NFC_VDD_AM_UPPER", "NFC_VDD_AM_LOWER",
        "NFC_AGDC_UPPER", "NFC_AGDC_LOWER",
        "NFC_RFO2", "NFC_RFO1", "NFC_XOUT_CRYSTAL", "NFC_XIN_CRYSTAL",
    ),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(path):
    run = subprocess.run([sys.executable, __file__, "--snapshot", str(path)],
                         text=True, capture_output=True, check=True)
    def freeze(value):
        return tuple(freeze(v) for v in value) if isinstance(value, list) else value
    payload = json.loads(run.stdout.splitlines()[0])
    return Counter({freeze(json.loads(key)): value for key, value in payload.items()})


def copper_in_process(path):
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


def move_and_withdraw(path):
    board = pcbnew.LoadBoard(str(path))
    u9 = board.FindFootprintByReference("U9")
    pads = list(u9.Pads())
    position = u9.GetPosition()
    old = (position.x, position.y)
    removed = []
    for item in list(board.GetTracks()):
        if item.GetClass() == "PCB_VIA" or item.GetNetname() not in REPLAY_NETS:
            continue
        if any(pad.HitTest(item.GetStart()) or pad.HitTest(item.GetEnd()) for pad in pads):
            removed.append((item.GetNetname(), item.GetLayerName(), item.GetWidth()))
            board.Remove(item)
    u9.SetPosition(pcbnew.VECTOR2I(old[0] + 500_000, old[1]))
    pcbnew.SaveBoard(str(path), board)
    return {"old": old, "withdrawn": removed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", choices=sorted(ORDERS), default="signals-first")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    before_hash = sha256(BOARD)
    baseline = copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-u9-refloor-") as td:
        scratch = Path(td) / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        prepared = subprocess.run([sys.executable, __file__, "--prepare", str(scratch)],
                                  text=True, capture_output=True, check=True)
        prepared = json.loads(prepared.stdout.splitlines()[0])
        old, withdrawn = prepared["old"], prepared["withdrawn"]
        routes = []
        for name in ORDERS[args.order]:
            run = subprocess.run([sys.executable, str(LOCAL), name, "--route", str(scratch)],
                                 text=True, capture_output=True)
            if run.returncode not in (0, 2) or not run.stdout.strip():
                routes.append({"name": name, "process_error": run.stderr, "exit": run.returncode})
                break
            result = json.loads(run.stdout)
            routes.append(result)
            if not result["result"].get("ok"):
                break
        # Inspect geometry before invoking kicad-cli.  KiCad 10's Python SWIG
        # module and a child kicad-cli --save-board are not safely mixed in
        # the opposite order in one process.
        after = copper(scratch)
        removed = baseline - after
        added = after - baseline
        drc_path = Path(td) / "drc.json"
        subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                        "--format", "json", "--units", "mm", "--severity-all",
                        "--schematic-parity", "-o", str(drc_path), str(scratch)],
                       text=True, capture_output=True)
        violations = json.loads(drc_path.read_text()).get("violations", [])
        types = Counter(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED_DRC]
        ledger_path = Path(td) / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        targets = {r["net"]: r["open_edges"] for r in ledger["nets"] if r["net"] in ALL_NETS}
        outside_removed = [list(k) for k in removed if k[0] not in REPLAY_NETS]
        wrong_added = [list(k) for k in added if k[0] not in ALL_NETS]
        route_ok = len(routes) == len(ORDERS[args.order]) and all(
            r.get("result", {}).get("ok") for r in routes)
        ok = (route_ok and targets == {n: 0 for n in ALL_NETS} and not attributable
              and not outside_removed and not wrong_added
              and len(withdrawn) == 8)
        if ok and args.candidate:
            args.candidate.write_bytes(scratch.read_bytes())
        if args.promote:
            if not ok or sha256(BOARD) != before_hash:
                raise RuntimeError("refuse promotion: full atomic gate failed or authority changed")
            BOARD.write_bytes(scratch.read_bytes())
        report = {
            "schema": 1, "authoritative_board_sha256": before_hash,
            "authoritative_unchanged": sha256(BOARD) == before_hash,
            "order": args.order, "u9_delta_mm": [0.5, 0.0],
            "withdrawn_pad_attached_items": len(withdrawn),
            "withdrawn_by_net": dict(Counter(x[0] for x in withdrawn)),
            "routes": routes, "target_open_edges": targets,
            "connectivity": ledger["connectivity"], "drc_types": dict(types),
            "attributable_drc": attributable,
            "removed_items": sum(removed.values()), "added_items": sum(added.values()),
            "outside_boundary_removals": outside_removed, "wrong_net_additions": wrong_added,
            "promotion_candidate": ok, "candidate_sha256": sha256(scratch),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--snapshot":
        snap = copper_in_process(Path(sys.argv[2]))
        print(json.dumps({json.dumps(list(key)): value for key, value in snap.items()}))
    elif len(sys.argv) == 3 and sys.argv[1] == "--prepare":
        print(json.dumps(move_and_withdraw(Path(sys.argv[2]))))
    else:
        raise SystemExit(main())
