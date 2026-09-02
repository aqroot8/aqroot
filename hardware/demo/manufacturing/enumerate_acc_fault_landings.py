#!/usr/bin/env python3
"""Enumerate legal offset landings for the Demo U21-side fault refloor.

This is a scratch-only characterization tool.  It removes the one accepted
ACC_POWER_FAULT_N segment that blocks U21.6, replays the already characterized
optional TP9/TP10/R50 placement transaction in memory, and asks the established
AQROOT routing geometry engine for B.Cu-reachable, all-layer-clear 0.60/0.30 mm
through-via sites at each old segment endpoint.  The authoritative PCB is never
saved or modified.
"""

import hashlib
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
import qrouter as qr  # noqa: E402

NET = "/ACC_POWER_FAULT_N"
ENDPOINTS_MM = ((59.25, 35.15), (59.20, 42.20))
MOVES_MM = {"TP9": (49.50, 39.25), "TP10": (63.50, 42.75), "R50": (49.50, 57.735)}


def point(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(round(x_mm * 1_000_000), round(y_mm * 1_000_000))


def same_point(actual: pcbnew.VECTOR2I, expected: tuple[float, float]) -> bool:
    return (actual.x, actual.y) == (round(expected[0] * 1_000_000), round(expected[1] * 1_000_000))


def scan_scratch(path: str) -> int:
    routed = qr.QBoard(path)
    net = routed.nets[NET]
    endpoint_sites = {}
    for endpoint in ENDPOINTS_MM:
        x, y = round(endpoint[0] * 1e6), round(endpoint[1] * 1e6)
        sites = routed.via_sites(
            "B", "I3", net, {"x": x, "y": y},
            width=200_000, via_dia=600_000,
            clr_pad=200_000, clr_trk=200_000,
            G=25_000, span=3_000_000,
            via_drill=300_000, hole_clr=250_000,
            limit=12, separation=300_000,
        )
        endpoint_sites[f"{endpoint[0]:.2f},{endpoint[1]:.2f}"] = [
            [round(px / 1e6, 3), round(py / 1e6, 3)] for px, py in sites
        ]
    print(json.dumps(endpoint_sites, sort_keys=True))
    return 0


def main() -> int:
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(BOARD.resolve()))

    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for ref, xy in MOVES_MM.items():
        footprint = footprints.get(ref)
        if footprint is None:
            raise RuntimeError(f"missing footprint {ref}")
        footprint.SetPosition(point(*xy))

    removed = []
    for item in list(board.GetTracks()):
        if item.GetClass() != "PCB_TRACK" or item.GetNetname() != NET:
            continue
        ends = (item.GetStart(), item.GetEnd())
        if ((same_point(ends[0], ENDPOINTS_MM[0]) and same_point(ends[1], ENDPOINTS_MM[1])) or
                (same_point(ends[1], ENDPOINTS_MM[0]) and same_point(ends[0], ENDPOINTS_MM[1]))):
            removed.append({"width_mm": item.GetWidth() / 1e6,
                            "layer": board.GetLayerName(item.GetLayer())})
            board.Remove(item)
    if len(removed) != 1:
        raise RuntimeError(f"expected exactly one blocking segment, found {len(removed)}")

    with tempfile.TemporaryDirectory(prefix="aqroot-demo-fault-landings-") as temporary:
        scratch = Path(temporary) / BOARD.name
        board.Save(str(scratch))
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--scan", str(scratch)],
            check=True, text=True, capture_output=True,
        )
        endpoint_sites = json.loads(completed.stdout)

    distinct_pairs = []
    left, right = endpoint_sites.values()
    for a in left:
        for b in right:
            if a != b:
                distinct_pairs.append({"a_mm": a, "b_mm": b})

    after = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    report = {
        "schema": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == after,
        "net": NET,
        "removed_scratch_segment": removed[0],
        "scratch_moves_mm": MOVES_MM,
        "method": "25um_BCu_reachability_all_copper_clearance_In3_offset_landing_enumeration",
        "signal_via_mm": {"diameter": 0.60, "drill": 0.30},
        "site_separation_mm": 0.30,
        "endpoint_sites": endpoint_sites,
        "distinct_pair_count": len(distinct_pairs),
        "distinct_pairs": distinct_pairs,
        "promotion_candidate": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if before == after else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--scan":
        raise SystemExit(scan_scratch(sys.argv[2]))
    raise SystemExit(main())
