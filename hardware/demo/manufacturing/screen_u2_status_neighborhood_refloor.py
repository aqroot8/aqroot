#!/usr/bin/env python3
"""Bound minimum complete-branch withdrawals around U2.9/U2.10.

This is a scratch-only sensitivity screen.  It removes complete copper for a
small, explicit set of nearby nets, then asks whether both charger-status lands
can simultaneously reach distinct ordinary through vias.  A positive result
defines a refloor/replay boundary; it is never itself a promotion candidate.
"""

import hashlib
import argparse
import itertools
import json
import tempfile
import subprocess
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
WIDTH = CLEARANCE = 200_000
STATUS = (("/BQ25185_STAT1", "U2.9", "R127.2"),
          ("/BQ25185_STAT2", "U2.10", "R128.2"))
# Measured copper within 3 mm of the midpoint between the two status lands.
# Withdraw whole nets, never geometric fragments, so every result names a
# coherent replay obligation.
NEIGHBORS = (
    "/TOUCH_RST_N",
    "/DISP_RST_N",
    "/SD_CARD_DETECT_N",
)
SITE_COUNT = 2

import sys
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def last_json_line(output):
    """Ignore pcbnew diagnostics, which can splice into the JSON line."""
    decoder = json.JSONDecoder()
    records = []
    for offset, char in enumerate(output):
        if char != "{":
            continue
        try:
            record, end = decoder.raw_decode(output[offset:])
            records.append((end, record))
        except json.JSONDecodeError:
            continue
    if records:
        return max(records, key=lambda row: row[0])[1]
    raise RuntimeError(f"subprocess emitted no JSON record: {output!r}")


def withdraw_complete_nets(path, nets):
    board = pcbnew.LoadBoard(str(path))
    counts = {net: 0 for net in nets}
    # Snapshot once.  Re-entering GetTracks() after removals can invalidate the
    # SWIG container on KiCad 10 when several complete nets are withdrawn.
    items = []
    for item in list(board.GetTracks()):
        net = item.GetNetname()
        if net in counts:
            counts[net] += 1
            items.append(item)
    for item in items:
        board.Remove(item)
    board.Save(str(path))
    del board
    return counts


def paired_launches(path):
    board = qr.QBoard(path)
    ir.inject_existing_via_obstacles(board)
    pads = []
    for net, u2, pullup in STATUS:
        by_ref = {p["ref"]: p for p in ir.physical_net_pads(board, net)}
        pads.append((net, by_ref[u2], by_ref[pullup]))
    rows = []
    for layers in itertools.permutations(("I2", "I3")):
        for order in ((0, 1), (1, 0)):
            for sites in itertools.product(range(SITE_COUNT), repeat=2):
                mark = board.mark(); results = []
                for i in order:
                    net, u2, pullup = pads[i]
                    result = qr.reserve_escape(
                        board, net, u2, WIDTH, CLEARANCE, CLEARANCE,
                        near="B", far=layers[i], via_dia=600_000,
                        via_drill=300_000, target=(pullup["x"], pullup["y"]),
                        site_index=sites[i], site_separation=300_000)
                    results.append(result)
                    if not result.get("ok"):
                        break
                ok = len(results) == 2 and all(r.get("ok") for r in results)
                if ok:
                    return {"ok": True, "layers": list(layers),
                            "order": list(order), "sites": list(sites),
                            "via_xy_mm": [[r["via"][0] / 1e6,
                                           r["via"][1] / 1e6]
                                          for r in results]}
                rows.append(results[-1].get("reason", "UNKNOWN"))
                board.revert(mark)
    return {"ok": False, "cases": len(rows),
            "last_reasons": {reason: rows.count(reason) for reason in set(rows)}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", type=Path)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("nets", nargs="*")
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(withdraw_complete_nets(args.prepare, args.nets)),
              flush=True)
        return 0
    if args.probe:
        print(json.dumps(paired_launches(args.probe)), flush=True)
        return 0
    before = sha(BOARD); rows = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-u2-status-refloor-") as td:
        work = Path(td)
        # Cardinality order makes the first successful row a minimum-size
        # complete-net withdrawal boundary within this measured neighborhood.
        for size in range(len(NEIGHBORS) + 1):
            winners = []
            for subset in itertools.combinations(NEIGHBORS, size):
                scratch = work / ("case-" + str(len(rows)) + ".kicad_pcb")
                scratch.write_bytes(BOARD.read_bytes())
                prep = subprocess.run([sys.executable, str(Path(__file__)),
                                       "--prepare", str(scratch), *subset],
                                      text=True, capture_output=True)
                if prep.returncode:
                    raise RuntimeError(
                        f"prepare failed for {subset}: rc={prep.returncode}: "
                        f"{prep.stdout}{prep.stderr}")
                probe = subprocess.run([sys.executable, str(Path(__file__)),
                                        "--probe", str(scratch)], text=True,
                                       capture_output=True, check=True)
                row = {"withdrawn_nets": list(subset),
                       "removed_copper_items": last_json_line(prep.stdout),
                       "launch": last_json_line(probe.stdout)}
                rows.append(row)
                if row["launch"].get("ok"):
                    winners.append(row)
            if winners:
                break
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before,
        "contract": {"width_mm": 0.2, "clearance_mm": 0.2,
                     "via_mm": [0.6, 0.3], "characterization_only": True,
                     "withdrawal_scope": "complete-net copper"},
        "neighbors": list(NEIGHBORS), "cases_tested": len(rows),
        "site_indices_per_land": SITE_COUNT,
        "minimum_withdrawal_cardinality": (len(winners[0]["withdrawn_nets"])
                                             if winners else None),
        "winners": winners, "cases": rows,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if winners else 2


if __name__ == "__main__":
    raise SystemExit(main())
