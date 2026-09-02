#!/usr/bin/env python3
"""Enumerate fitted-pad escapes for a complete Demo fault-branch refloor.

Scratch only.  Withdraw every ACC_POWER_FAULT_N track/via, replay the optional
TP9/TP10/R50 placement screen in memory, and enumerate B.Cu-reachable legal
0.60/0.30 mm through-via sites to In3 from each actual fitted pad.  This tests
the pad-first prerequisite for replacing the complete branch without retaining
the geometrically boxed intermediate endpoints of the rejected segment tactic.
"""

import hashlib
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
ROUTER_DIR = ROOT / "hardware/beta-v2/checks"
sys.path.insert(0, str(ROUTER_DIR))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

NET = "/ACC_POWER_FAULT_N"
MOVES_MM = {"TP9": (49.50, 39.25), "TP10": (63.50, 42.75), "R50": (49.50, 57.735)}


def point(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(round(x_mm * 1_000_000), round(y_mm * 1_000_000))


def scan_scratch(path: str) -> int:
    routed = qr.QBoard(path)
    ir.inject_existing_via_obstacles(routed)
    pads = ir.physical_net_pads(routed, NET)
    pads.sort(key=lambda pad: (pad["ref"], pad["x"], pad["y"]))
    net = routed.nets[NET]
    results = []
    for pad in pads:
        escapes = routed.escape(
            pad, "B", 200_000, 200_000, 200_000, 200_000, 25_000,
            routed.ex0 - 2_000_000, routed.ey0 - 2_000_000,
        )
        sites = []
        for escape in (escapes or [])[:12]:
            for x, y in routed.via_sites(
                "B", "I3", net, escape,
                width=200_000, via_dia=600_000,
                clr_pad=200_000, clr_trk=200_000,
                G=25_000, span=4_000_000,
                via_drill=300_000, hole_clr=250_000,
                limit=12, separation=300_000,
            ):
                xy = [round(x / 1e6, 3), round(y / 1e6, 3)]
                if xy not in sites:
                    sites.append(xy)
        results.append({
            "pad": pad["ref"],
            "position_mm": [round(pad["x"] / 1e6, 3), round(pad["y"] / 1e6, 3)],
            "escape_count": len(escapes or []),
            "site_count": len(sites),
            "sites_mm": sites[:12],
            "escape_failure": None if escapes else routed.escape_why[0],
        })
    print(json.dumps(results, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(BOARD.resolve()))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for ref, xy in MOVES_MM.items():
        footprints[ref].SetPosition(point(*xy))

    removed = {"tracks": 0, "vias": 0}
    for item in list(board.GetTracks()):
        if item.GetNetname() != NET:
            continue
        key = "vias" if item.GetClass() == "PCB_VIA" else "tracks"
        removed[key] += 1
        board.Remove(item)

    with tempfile.TemporaryDirectory(prefix="aqroot-demo-fault-pads-") as temporary:
        scratch = Path(temporary) / BOARD.name
        board.Save(str(scratch))
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--scan", str(scratch)],
            check=True, text=True, capture_output=True,
        )
        pads = json.loads(completed.stdout)

    after = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    zero_site = [row["pad"] for row in pads if not row["site_count"]]
    report = {
        "schema": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == after,
        "net": NET,
        "scratch_withdrawal": removed,
        "scratch_moves_mm": MOVES_MM,
        "method": "complete_branch_withdrawal_then_fitted_pad_BCu_to_In3_escape_enumeration_25um",
        "signal_via_mm": {"diameter": 0.60, "drill": 0.30},
        "pads": pads,
        "zero_site_pads": zero_site,
        "all_fitted_pads_have_sites": not zero_site,
        "promotion_candidate": False,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if before == after else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--scan":
        raise SystemExit(scan_scratch(sys.argv[2]))
    raise SystemExit(main())
