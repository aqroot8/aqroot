#!/usr/bin/env python3
"""Bound a package-local U21.6 transition into the accepted In3 raw tree."""

import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
DRU = BOARD.with_suffix(".kicad_dru")
RAW = "/01_POWER_TREE/ACC_5V_RAW"
LX = "/01_POWER_TREE/ACC_5V_LX"
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}

# The raw pad moves to (57.0875, 39.4) when U21 is rotated.  Each candidate
# uses only a courtyard-local 0.25 mm B.Cu neck, then changes to the already
# accepted 0.40 mm In3 raw tree.  The target is an existing raw via, so the
# accepted five-endpoint distribution topology remains intact.
VIA_SITES_MM = ((56.45, 39.40), (56.45, 39.15), (56.20, 39.40),
                (56.20, 39.15), (56.70, 38.95), (56.45, 38.80))
IN3_BENDS_MM = ((56.00, 38.50), (56.35, 38.25))
RAW_TREE_VIA_MM = (55.85, 38.00)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point(x, y):
    return pcbnew.VECTOR2I(round(x * 1e6), round(y * 1e6))


def add_track(board, net, layer, a, b, width):
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(point(*a)); track.SetEnd(point(*b))
    track.SetWidth(round(width * 1e6)); track.SetLayer(layer)
    track.SetNet(net); board.Add(track)


def prepare(path, via_site, bend):
    board = pcbnew.LoadBoard(str(BOARD))
    board.FindFootprintByReference("U21").SetOrientationDegrees(180)
    board.FindFootprintByReference("L4").SetOrientationDegrees(180)
    r99 = board.FindFootprintByReference("R99")
    old = r99.GetPosition()
    r99.SetPosition(point(old.x / 1e6 + 0.5, old.y / 1e6))

    # Withdraw only the obsolete package neck.  All five raw-tree vias and
    # their accepted B.Cu/In3 distribution copper remain byte-geometrically
    # present in the scratch candidate.
    removed = 0
    neck_points = {(58_512_500, 40_400_000), (59_022_500, 40_400_000)}
    for item in list(board.GetTracks()):
        if item.GetNetname() != RAW or isinstance(item, pcbnew.PCB_VIA):
            continue
        a, b = item.GetStart(), item.GetEnd()
        if (a.x, a.y) in neck_points or (b.x, b.y) in neck_points:
            board.Remove(item); removed += 1

    raw = board.FindNet(RAW)
    lx = board.FindNet(LX)

    # Retain the shorter generic B.Cu LX route proven by the D-416 refloor;
    # raw leaves B.Cu before the two power paths need to cross.
    lx_points = ((57.0875, 39.9), (55.925, 39.9), (55.925, 39.2),
                 (56.725, 38.4), (56.725, 36.25), (56.675, 36.2),
                 (57.715, 36.2))
    for a, b in zip(lx_points, lx_points[1:]):
        add_track(board, lx, pcbnew.B_Cu, a, b, 0.25 if a == lx_points[0] else 0.40)

    add_track(board, raw, pcbnew.B_Cu, (57.0875, 39.4), via_site, 0.25)
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(point(*via_site)); via.SetWidth(900_000)
    via.SetDrill(400_000); via.SetLayerPair(pcbnew.B_Cu, pcbnew.In3_Cu)
    via.SetNet(raw); board.Add(via)
    add_track(board, raw, pcbnew.In3_Cu, via_site, bend, 0.40)
    add_track(board, raw, pcbnew.In3_Cu, bend, RAW_TREE_VIA_MM, 0.40)

    pcbnew.SaveBoard(str(path), board)
    path.with_suffix(".kicad_dru").write_bytes(DRU.read_bytes())
    return removed


def run_case(path, report_path, case):
    removed = prepare(path, *case)
    run = subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(report_path), str(path),
    ], capture_output=True, text=True)
    rows = json.loads(report_path.read_text()).get("violations", [])
    counts = {}
    attributable = []
    for row in rows:
        kind = row.get("type", "unknown")
        counts[kind] = counts.get(kind, 0) + 1
        if kind not in ACCEPTED:
            attributable.append({"type": kind,
                                "description": row.get("description", "")})
    return {"via_site_mm": case[0], "in3_bend_mm": case[1],
            "withdrawn_raw_neck_segments": removed, "drc_exit": run.returncode,
            "drc_types": counts, "attributable": attributable,
            "candidate": not attributable}


def main():
    before = sha256(BOARD)
    cases = list(itertools.product(VIA_SITES_MM, IN3_BENDS_MM))
    results = []
    with tempfile.TemporaryDirectory(prefix="aqroot-acc5v-raw-in3-") as td:
        td = Path(td)
        for index in range(len(cases)):
            child = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--case",
                 str(index), str(td)], check=True, capture_output=True, text=True)
            results.append(json.loads(next(line for line in reversed(
                child.stdout.splitlines()) if line.startswith("{"))))
    report = {"schema": 1,
              "tactic": "courtyard-local U21.6 B.Cu-to-In3 raw transition",
              "authoritative_board_sha256": before,
              "authoritative_board_unchanged": before == sha256(BOARD),
              "cases": results}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_board_unchanged"] else 2


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--case":
        index = int(sys.argv[2]); td = Path(sys.argv[3])
        cases = list(itertools.product(VIA_SITES_MM, IN3_BENDS_MM))
        print(json.dumps(run_case(td / f"case-{index}.kicad_pcb",
                                  td / f"case-{index}-drc.json", cases[index]),
                         sort_keys=True))
        raise SystemExit(0)
    raise SystemExit(main())
