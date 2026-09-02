#!/usr/bin/env python3
"""Enumerate legal B.Cu launch/via anchors at the two BQ25185_SYS walls.

Scratch-only focused successor to ``route_bq25185_sys_scratch.py``.  The first
tree screen proved every other fitted endpoint can escape, but its hand-seeded
U11.1 and U21.3 north launches violate retained D-269 / ACC_DETECT_N copper.
This tool enumerates materially distinct reachable ordinary power-via sites
from the real package pads without changing the authoritative PCB.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

NET = "/01_POWER_TREE/BQ25185_SYS"
CASES = {
    # The 0.20 mm land-width neck is package-local.  D-269 governs its escape
    # against the retained BAT_PROTECTED_P current corridor.
    "U11.1": {"width": 200_000, "clearance": 300_000},
    # TPS61023 input pad uses a 0.25 mm package neck before the D-185 0.80 mm
    # peak-current feed.  The launch must first clear ACC_DETECT_N legally.
    "U21.3": {"width": 250_000, "clearance": 250_000},
}


def scan() -> list[dict]:
    board = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    net = board.nets[NET]
    rows = []
    for ref, rule in CASES.items():
        pad = pads[ref]
        escapes = board.escape(
            pad, "B", rule["width"], rule["width"], rule["clearance"],
            rule["clearance"], 25_000, board.ex0 - 2_000_000,
            board.ey0 - 2_000_000,
        )
        candidates = []
        for rank, escape in enumerate((escapes or [])[:16]):
            sites = board.via_sites(
                "B", "I3", net, escape, width=rule["width"],
                via_dia=900_000, clr_pad=rule["clearance"],
                clr_trk=rule["clearance"], G=25_000, span=5_000_000,
                via_drill=400_000, hole_clr=250_000, limit=16,
                separation=450_000,
            )
            candidates.append({
                "escape_rank": rank,
                "escape_mm": [round(escape["x"] / 1e6, 3),
                              round(escape["y"] / 1e6, 3)],
                "escape_width_mm": round(escape["w"] / 1e6, 3),
                "escape_length_mm": round(escape["ln"] / 1e6, 4),
                "sites_mm": [[round(x / 1e6, 3), round(y / 1e6, 3)]
                             for x, y in sites],
            })
        rows.append({
            "pad": ref,
            "pad_position_mm": [round(pad["x"] / 1e6, 3),
                                round(pad["y"] / 1e6, 3)],
            "neck_width_mm": rule["width"] / 1e6,
            "routed_clearance_mm": rule["clearance"] / 1e6,
            "escape_count": len(escapes or []),
            "escape_failure": None if escapes else board.escape_why[0],
            "candidates": candidates,
            "site_count": sum(len(c["sites_mm"]) for c in candidates),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    rows = scan()
    after = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    report = {
        "schema": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == after,
        "net": NET,
        "method": "focused_25um_BCu_escape_and_reachable_In3_power_via_enumeration",
        "power_via_mm": {"diameter": 0.90, "drill": 0.40},
        "site_separation_mm": 0.45,
        "pads": rows,
        "all_wall_pads_have_sites": all(row["site_count"] for row in rows),
        "promotion_candidate": False,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
