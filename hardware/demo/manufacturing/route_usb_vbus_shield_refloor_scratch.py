#!/usr/bin/env python3
"""Atomically refloor USB_VBUS_RAW and the complete USB-C shield tree."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

import route_usb_vbus_raw_tree_scratch as raw_route

ROOT = Path(__file__).resolve().parents[3]
BOARD = raw_route.BOARD
LEDGER = Path(__file__).with_name("routing_ledger.py")
RAW = raw_route.NET
SHIELD = "Net-(J3-SHIELD)"
VBUS_CLEARANCE = 250_000
ACCEPTED = raw_route.ACCEPTED
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

SHIELD_PADS = (
    "J3.SH@38.680,141.625", "J3.SH@38.680,145.805",
    "J3.SH@47.320,141.625", "J3.SH@47.320,145.805", "R32.1",
)
SHIELD_BRANCH_ORDERS = (
    (("R32.1", "J3.SH@47.320,141.625", "HOP"),
     ("J3.SH@47.320,141.625", "J3.SH@47.320,145.805", "B"),
     ("J3.SH@47.320,145.805", "J3.SH@38.680,145.805", "B"),
     ("J3.SH@38.680,145.805", "J3.SH@38.680,141.625", "B")),
    (("R32.1", "J3.SH@47.320,141.625", "HOP"),
     ("J3.SH@47.320,141.625", "J3.SH@38.680,141.625", "B"),
     ("J3.SH@38.680,141.625", "J3.SH@38.680,145.805", "B"),
     ("J3.SH@38.680,145.805", "J3.SH@47.320,145.805", "B")),
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def pad_key(pad):
    if pad["ref"] != "J3.SH":
        return pad["ref"]
    return f'{pad["ref"]}@{pad["x"] / 1e6:.3f},{pad["y"] / 1e6:.3f}'


def withdraw_shield(path):
    board = pcbnew.LoadBoard(str(path))
    items = [item for item in list(board.GetTracks())
             if item.GetNetname() == SHIELD]
    for item in items:
        board.Remove(item)
    board.Save(str(path))
    return len(items)


def replay_shield(board, pads, order):
    routes = []
    for left, right, role in order:
        if role == "HOP":
            route = qr.connect_hop(
                board, SHIELD, pads[left], pads[right], 300_000,
                VBUS_CLEARANCE, VBUS_CLEARANCE, near="F", far="B",
                G=25_000, fine=25_000,
                via_dia=600_000, via_drill=300_000)
        else:
            route = qr.connect_role(board, SHIELD, pads[left], pads[right],
                                    role, 300_000, VBUS_CLEARANCE,
                                    VBUS_CLEARANCE, G=25_000)
        routes.append(route)
        if not route.get("ok"):
            break
    return routes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--prepare", type=Path)
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps({"withdrawn_shield_items": withdraw_shield(args.prepare)}))
        return 0
    before_sha = sha256(BOARD)
    baseline = copper(pcbnew.LoadBoard(str(BOARD)))
    rows = []
    winner = None
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-vbus-shield-") as td:
        work = Path(td)
        for order_index, order in enumerate(SHIELD_BRANCH_ORDERS):
            scratch = work / f"case-{order_index}.kicad_pcb"
            for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
                scratch.with_suffix(suffix).write_bytes(
                    BOARD.with_suffix(suffix).read_bytes())
            prepared = subprocess.run(
                [sys.executable, str(Path(__file__)), "--prepare", str(scratch)],
                check=True, text=True, capture_output=True)
            withdrawn = last_json(prepared.stdout)["withdrawn_shield_items"]
            seed = qr.QBoard(scratch)
            physical = ir.physical_net_pads(seed, RAW)
            raw_pads = {pad["ref"]: pad for pad in physical}
            board, raw_routes = raw_route.route_candidate(scratch, raw_pads, 0, 0)
            shield_physical = ir.physical_net_pads(board, SHIELD)
            shield_pads = {pad_key(pad): pad for pad in shield_physical}
            if set(shield_pads) != set(SHIELD_PADS):
                raise RuntimeError(f"unexpected shield pads: {sorted(shield_pads)}")
            shield_routes = []
            if (len(raw_routes) == raw_route.EXPECTED_STAGES and
                    all(route.get("ok") for route in raw_routes)):
                shield_routes = replay_shield(board, shield_pads, order)
            board.save(scratch)
            drc_path = work / f"drc-{order_index}.json"
            checked = subprocess.run([
                "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                "--format", "json", "--units", "mm", "--severity-all",
                "--schematic-parity", "-o", str(drc_path), str(scratch),
            ], text=True, capture_output=True)
            violations = json.loads(drc_path.read_text()).get("violations", [])
            types = Counter(v.get("type", "unknown") for v in violations)
            attributable = [v for v in violations
                            if v.get("type") not in ACCEPTED]
            ledger_path = work / f"ledger-{order_index}.json"
            subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                            str(ledger_path)], check=True,
                           stdout=subprocess.DEVNULL)
            ledger = json.loads(ledger_path.read_text())
            net_rows = {row["net"]: row for row in ledger["nets"]}
            after = copper(pcbnew.LoadBoard(str(scratch)))
            removed = baseline - after
            added = after - baseline
            removed_nonshield = [list(item) for item in removed
                                 if item[0] != SHIELD]
            added_wrong = [list(item) for item in added
                           if item[0] not in (RAW, SHIELD)]
            complete = (
                len(raw_routes) == raw_route.EXPECTED_STAGES and
                all(route.get("ok") for route in raw_routes) and
                len(shield_routes) == len(order) and
                all(route.get("ok") for route in shield_routes) and
                net_rows[RAW]["open_edges"] == 0 and
                net_rows[SHIELD]["open_edges"] == 0 and not attributable and
                not removed_nonshield and not added_wrong)
            row = {
                "order": order_index, "withdrawn_shield_items": withdrawn,
                "raw_routes": raw_routes, "shield_routes": shield_routes,
                "drc_exit": checked.returncode, "drc_types": dict(types),
                "attributable_drc": attributable,
                "raw_open_edges": net_rows[RAW]["open_edges"],
                "shield_open_edges": net_rows[SHIELD]["open_edges"],
                "removed_nonshield_items": removed_nonshield,
                "added_wrong_net_items": added_wrong,
                "promotion_candidate": complete,
            }
            rows.append(row)
            if complete and winner is None:
                candidate = scratch.read_bytes()
                winner = (row, candidate)
        promotion = winner is not None
        if args.candidate and promotion:
            args.candidate.write_bytes(winner[1])
        if args.promote:
            if not promotion or sha256(BOARD) != before_sha:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winner[1])
    print(json.dumps({
        "schema": 1, "authoritative_board_sha256": before_sha,
        "authoritative_unchanged": sha256(BOARD) == before_sha,
        "contract": {"raw_width_mm": 0.5, "raw_clearance_mm": 0.2,
                     "vbus_to_shield_clearance_mm": 0.25,
                     "complete_shield_replay_required": True},
        "cases": rows, "promotion_candidate": promotion,
        "candidate_sha256": (hashlib.sha256(winner[1]).hexdigest()
                             if winner else None),
    }, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
