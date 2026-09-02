#!/usr/bin/env python3
"""Bound the final F.Cu-only perimeter tactic for the MCU-side USB pair."""

import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

PAIR = {
    "N": ("/USB_D_MCU_N", "R33.2", "U1.13"),
    "P": ("/USB_D_MCU_P", "R34.2", "U1.14"),
}
WIDTH = 230_000
CLEARANCE = 200_000
GRID = 50_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect_full_board(board, net, start_ref, end_ref):
    """Search every legal F.Cu cell, rather than a local endpoint window."""
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, net)}
    start, end = pads[start_ref], pads[end_ref]
    ox = int(math.floor((board.ex0 - 1_000_000) / GRID)) * GRID
    oy = int(math.floor((board.ey0 - 1_000_000) / GRID)) * GRID
    x1, y1 = board.ex1 + 1_000_000, board.ey1 + 1_000_000
    starts = board.escape(start, "F", WIDTH, WIDTH, CLEARANCE, CLEARANCE,
                          GRID, ox, oy, prefer=(end["x"] - start["x"], end["y"] - start["y"]))
    start_why = list(board.escape_why)
    ends = board.escape(end, "F", WIDTH, WIDTH, CLEARANCE, CLEARANCE,
                        GRID, ox, oy, prefer=(start["x"] - end["x"], start["y"] - end["y"]))
    end_why = list(board.escape_why)
    if not starts or not ends:
        return {"ok": False, "reason": "NO_LEGAL_ESCAPE", "start_why": start_why,
                "end_why": end_why, "start_sites": len(starts), "end_sites": len(ends)}
    blocked = board.grid("F", net, WIDTH, CLEARANCE, CLEARANCE, ox, oy, x1, y1, GRID)
    ny, nx = blocked.shape
    attempts = 0
    # escape() is already widest-first and preference-ranked.  The two leading
    # sites per endpoint bound the destination-facing launch family without
    # multiplying a whole-board wavefront into an unbounded Cartesian sweep.
    ranked_starts = starts[:2]
    ranked_ends = ends[:2]
    for a in ranked_starts:
        for b in ranked_ends:
            attempts += 1
            si = ((a["x"] - ox) // GRID, (a["y"] - oy) // GRID)
            ti = ((b["x"] - ox) // GRID, (b["y"] - oy) // GRID)
            trial = blocked.copy()
            for i, j in (si, ti):
                if 0 <= i < nx and 0 <= j < ny:
                    trial[j, i] = False
            path = board.search(trial, si, ti)
            if path is None:
                continue
            points = qr.simplify(path, ox, oy, GRID)
            board.track(net, "F", start["x"], start["y"], a["x"], a["y"], a["w"])
            for p0, p1 in zip(points, points[1:]):
                board.track(net, "F", *p0, *p1, WIDTH)
            board.track(net, "F", end["x"], end["y"], b["x"], b["y"], b["w"])
            length = math.hypot(start["x"] - a["x"], start["y"] - a["y"])
            length += math.hypot(end["x"] - b["x"], end["y"] - b["y"])
            length += sum(math.hypot(q[0] - p[0], q[1] - p[1])
                          for p, q in zip(points, points[1:]))
            return {"ok": True, "attempts": attempts, "start_sites": len(starts),
                    "end_sites": len(ends), "ranked_sites_per_end": 2,
                    "grid_mm": GRID / 1e6,
                    "length_mm": round(length / 1e6, 6), "segments": len(points) + 1,
                    "bbox_mm": [round(min(p[0] for p in points) / 1e6, 3),
                                round(min(p[1] for p in points) / 1e6, 3),
                                round(max(p[0] for p in points) / 1e6, 3),
                                round(max(p[1] for p in points) / 1e6, 3)]}
    return {"ok": False, "reason": "NO_FULL_BOARD_FCU_PATH", "attempts": attempts,
            "start_sites": len(starts), "end_sites": len(ends),
            "ranked_sites_per_end": 2,
            "grid_mm": GRID / 1e6, "grid_cells": int(nx * ny)}


def run_order(source, work, order):
    scratch = work / ("usb-perimeter-" + "".join(order) + ".kicad_pcb")
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(source.with_suffix(suffix).read_bytes())
    board = qr.QBoard(scratch)
    ir.inject_existing_via_obstacles(board)
    routes = []
    for leg in order:
        routes.append({"leg": leg, **connect_full_board(board, *PAIR[leg])})
        if not routes[-1]["ok"]:
            break
    board.save(scratch)
    drc_path = work / ("drc-" + "".join(order) + ".json")
    completed = subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(drc_path), str(scratch),
    ], text=True, capture_output=True)
    violations = json.loads(drc_path.read_text()).get("violations", [])
    types = {}
    for violation in violations:
        kind = violation.get("type", "unknown")
        types[kind] = types.get(kind, 0) + 1
    attributable = [{"type": v.get("type"), "description": v.get("description")}
                    for v in violations if v.get("type") not in ACCEPTED]
    return {"order": list(order), "routes": routes, "drc_exit": completed.returncode,
            "drc_types": types, "attributable_drc": attributable,
            "promotion_candidate": len(routes) == 2 and all(r["ok"] for r in routes)
            and not attributable}


def main():
    before = sha256(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-perimeter-") as temporary:
        work = Path(temporary)
        attempts = [run_order(BOARD, work, order) for order in (("N", "P"), ("P", "N"))]
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == sha256(BOARD),
        "contract": "whole-board F.Cu-only, 0.23 mm width, 0.20 mm clearance, zero vias; both routing orders",
        "attempts": attempts,
        "promotion_candidate": any(a["promotion_candidate"] for a in attempts),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
