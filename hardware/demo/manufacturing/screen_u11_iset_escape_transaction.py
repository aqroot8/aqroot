#!/usr/bin/env python3
"""Bound U11.8 ISET after reserving both adjacent charger-pin escapes."""

import hashlib
import json
import math
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

WIDTH = CLEARANCE = 200_000
DIRECTIONS = tuple(
    (name, int(round(math.cos(math.radians(angle)) * 2_000_000)),
     int(round(math.sin(math.radians(angle)) * 2_000_000)))
    for name, angle in (
        ("E", 0), ("SE", 45), ("S", 90), ("SW", 135),
        ("W", 180), ("NW", 225), ("N", 270), ("NE", 315),
    )
)


def pads(board, net):
    return {p["ref"]: p for p in ir.physical_net_pads(board, net)}


def run_case(source, ts_direction, stat_direction, order):
    board = qr.QBoard(source)
    ir.inject_existing_via_obstacles(board)
    ts = pads(board, "Net-(U11-TS_MR)")["U11.6"]
    stat = pads(board, "/BQ25185_STAT1")["U11.9"]
    iset = pads(board, "/01_POWER_TREE/ISET")
    results = []
    reservations = {"TS_FIRST": ((ts, ts_direction), (stat, stat_direction)),
                    "STAT1_FIRST": ((stat, stat_direction), (ts, ts_direction))}
    for pad, direction in reservations[order]:
        name, dx, dy = direction
        result = qr.reserve_run(
            board, pad["net"], pad, WIDTH, CLEARANCE, CLEARANCE,
            layer="B", target=(pad["x"] + dx, pad["y"] + dy), G=25_000,
            fine=25_000,
        )
        results.append({"pad": pad["ref"], "direction": name, "result": result})
        if not result.get("ok"):
            return {"ok": False, "reservations": results, "iset": None}
    result = qr.connect_role(
        board, "/01_POWER_TREE/ISET", iset["U11.8"], iset["R37.1"],
        "B", WIDTH, CLEARANCE, CLEARANCE, G=25_000,
    )
    return {"ok": result.get("ok", False), "reservations": results, "iset": result}


def main():
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    cases = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-u11-iset-") as temporary:
        source = Path(temporary) / BOARD.name
        source.write_bytes(BOARD.read_bytes())
        for order in ("TS_FIRST", "STAT1_FIRST"):
            for ts_direction in DIRECTIONS:
                for stat_direction in DIRECTIONS:
                    cases.append({
                        "order": order, "ts": ts_direction[0],
                        "stat1": stat_direction[0],
                        **run_case(source, ts_direction, stat_direction, order),
                    })
    reason_counts = {}
    for case in cases:
        failed = next(
            (r["result"] for r in case["reservations"] if not r["result"].get("ok")),
            case["iset"] if case["iset"] and not case["iset"].get("ok") else None,
        )
        if failed:
            key = failed.get("reason", "UNKNOWN")
            reason_counts[key] = reason_counts.get(key, 0) + 1
    print(json.dumps({
        "schema": 1,
        "board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "contract": {"layer": "B.Cu", "width_mm": 0.2, "clearance_mm": 0.2,
                     "reservation_radius_mm": 2.0},
        "case_count": len(cases),
        "complete_count": sum(case["ok"] for case in cases),
        "both_reservations_count": sum(
            len(case["reservations"]) == 2 and
            all(r["result"].get("ok") for r in case["reservations"])
            for case in cases
        ),
        "failure_reasons": reason_counts,
        "cases": cases,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
