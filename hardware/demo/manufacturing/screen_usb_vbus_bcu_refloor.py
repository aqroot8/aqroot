#!/usr/bin/env python3
"""Bound the complete-net refloor needed by the USB_VBUS_RAW B.Cu haul.

This is characterization only.  Each case removes all accepted copper on one
explicit nearby net, then replays the complete RAW-tree routing attempt.  It
never writes a candidate or the authoritative board: a future promotion must
also replay every withdrawn net and pass the full-board gate atomically.
"""

import hashlib
import json
import tempfile
import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pcbnew

import route_usb_vbus_raw_tree_scratch as raw_route

BOARD = raw_route.BOARD
NEIGHBORS = ("Net-(J3-SHIELD)",)


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


def withdraw_complete_net(path, net):
    board = pcbnew.LoadBoard(str(path))
    items = [item for item in list(board.GetTracks())
             if item.GetNetname() == net]
    layers = Counter("VIA" if item.GetClass() == "PCB_VIA"
                     else item.GetLayerName() for item in items)
    for item in items:
        board.Remove(item)
    board.Save(str(path))
    return {"net": net, "objects": len(items), "layers": dict(layers)}


def probe(path, site):
    seed = raw_route.qr.QBoard(path)
    physical = raw_route.ir.physical_net_pads(seed, raw_route.NET)
    pads = {pad["ref"]: pad for pad in physical}
    routed, routes = raw_route.route_candidate(path, pads, site, 0)
    return {"stages_reached": len(routes), "routes": routes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", type=Path)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--net")
    parser.add_argument("--site", type=int)
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(withdraw_complete_net(args.prepare, args.net)))
        return 0
    if args.probe:
        print(json.dumps(probe(args.probe, args.site)))
        return 0
    before = sha256(BOARD)
    rows = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-vbus-refloor-") as td:
        work = Path(td)
        for net in NEIGHBORS:
            for site in range(8):
                scratch = work / f"case-{site}.kicad_pcb"
                for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
                    scratch.with_suffix(suffix).write_bytes(
                        BOARD.with_suffix(suffix).read_bytes())
                prepared = subprocess.run(
                    [sys.executable, str(Path(__file__)), "--prepare", str(scratch),
                     "--net", net], check=True, text=True, capture_output=True)
                withdrawn = last_json(prepared.stdout)
                tested = subprocess.run(
                    [sys.executable, str(Path(__file__)), "--probe", str(scratch),
                     "--site", str(site)], check=True, text=True, capture_output=True)
                probe_row = last_json(tested.stdout)
                routes = probe_row["routes"]
                # Do not save: this screen needs only deterministic geometric
                # feasibility and must not emit even a partial candidate.
                first_haul = routes[3] if len(routes) > 3 else None
                rows.append({"withdrawn": withdrawn, "c20_site": site,
                             "stages_reached": probe_row["stages_reached"],
                             "first_haul": first_haul,
                             "complete_raw_tree_geometry": (
                                 len(routes) == raw_route.EXPECTED_STAGES and
                                 all(route.get("ok") for route in routes))})
    winners = [row for row in rows if row["first_haul"] and
               row["first_haul"].get("ok")]
    complete = [row for row in rows if row["complete_raw_tree_geometry"]]
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": sha256(BOARD) == before,
        "contract": {"raw_width_mm": 0.5, "clearance_mm": 0.2,
                     "withdrawal_scope": "complete-net copper",
                     "characterization_only": True,
                     "promotion_requires_atomic_withdrawn_net_replay": True},
        "neighbors": list(NEIGHBORS),
        "cases_tested": len(rows),
        "first_haul_winners": winners,
        "complete_raw_tree_winners": complete,
        "cases": rows,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if winners else 2


if __name__ == "__main__":
    raise SystemExit(main())
