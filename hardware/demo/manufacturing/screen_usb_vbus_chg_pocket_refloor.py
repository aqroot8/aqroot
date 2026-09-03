#!/usr/bin/env python3
"""Bound complete-net copper withdrawals around USB_VBUS_CHG wall pads.

Characterization only.  Accepted copper is removed only from temporary board
copies.  A later promotable transaction must route the complete CHG tree and
replay every withdrawn net under the authoritative full-board gate.
"""

import hashlib
import json
import math
import argparse
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

import enumerate_usb_vbus_chg_necks as necks

BOARD = necks.BOARD
RADIUS = 5_000_000
WALLS = ("R91.1", "U11.10")


def last_json(output):
    decoder = json.JSONDecoder()
    records = []
    for offset, char in enumerate(output):
        if char != "{":
            continue
        try:
            record, end = decoder.raw_decode(output[offset:])
            records.append((end, record))
        except json.JSONDecodeError:
            pass
    if not records:
        raise RuntimeError(f"subprocess emitted no JSON: {output!r}")
    return max(records, key=lambda row: row[0])[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pad_position(board, ref):
    footprint_ref, pad_number = ref.split(".")
    footprint = board.FindFootprintByReference(footprint_ref)
    pad = next(p for p in footprint.Pads() if p.GetNumber() == pad_number)
    return pad.GetPosition()


def nearby_complete_nets(path, ref):
    board = pcbnew.LoadBoard(str(path))
    center = pad_position(board, ref)
    rows = {}
    for item in board.GetTracks():
        points = ([item.GetPosition()] if item.GetClass() == "PCB_VIA" else
                  [item.GetStart(), item.GetEnd()])
        distance = min(math.hypot(point.x - center.x, point.y - center.y)
                       for point in points)
        net = str(item.GetNetname())
        if (distance <= RADIUS and net and net != necks.NET):
            row = rows.setdefault(net, {"nearby_objects": 0,
                                        "minimum_distance_mm": distance / 1e6})
            row["nearby_objects"] += 1
            row["minimum_distance_mm"] = min(row["minimum_distance_mm"],
                                               distance / 1e6)
    return dict(sorted(rows.items(), key=lambda item:
                       (item[1]["minimum_distance_mm"], item[0])))


def withdraw(path, net):
    board = pcbnew.LoadBoard(str(path))
    items = [item for item in list(board.GetTracks())
             if str(item.GetNetname()) == net]
    layers = Counter("VIA" if item.GetClass() == "PCB_VIA"
                     else item.GetLayerName() for item in items)
    for item in items:
        board.Remove(item)
    board.Save(str(path))
    return {"objects": len(items), "layers": dict(layers)}


def screen(path, wall):
    run = subprocess.run([sys.executable, str(Path(necks.__file__)),
                          "--board", str(path)], text=True,
                         capture_output=True)
    if run.returncode not in (0, 2):
        raise RuntimeError(run.stderr)
    record = last_json(run.stdout)
    row = next(row for row in record["pads"] if row["pad"] == wall)
    return {"candidate_count": row["candidate_count"],
            "first_candidates": row["candidates"][:4],
            "blockers": row["blockers"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", type=Path)
    parser.add_argument("--net")
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(withdraw(args.prepare, args.net)))
        return 0
    before = sha256(BOARD)
    inventory = {wall: nearby_complete_nets(BOARD, wall) for wall in WALLS}
    cases = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-chg-pocket-") as td:
        work = Path(td)
        for wall in WALLS:
            for index, net in enumerate(inventory[wall]):
                scratch = work / f"{wall.replace('.', '-')}-{index}.kicad_pcb"
                scratch.write_bytes(BOARD.read_bytes())
                prepared = subprocess.run(
                    [sys.executable, str(Path(__file__)), "--prepare",
                     str(scratch), "--net", net], check=True, text=True,
                    capture_output=True)
                removed = last_json(prepared.stdout)
                result = screen(scratch, wall)
                cases.append({"wall": wall, "withdrawn_net": net,
                              "withdrawn": removed, **result})
    winners = [case for case in cases if case["candidate_count"]]
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": sha256(BOARD) == before,
        "contract": {"radius_mm": RADIUS / 1e6,
                     "withdrawal_scope": "one complete copper net per case",
                     "characterization_only": True,
                     "promotion_requires_complete_chg_tree_and_net_replay": True},
        "inventory": inventory,
        "cases_tested": len(cases),
        "single_net_winners": winners,
        "cases": cases,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if winners else 2


if __name__ == "__main__":
    raise SystemExit(main())
