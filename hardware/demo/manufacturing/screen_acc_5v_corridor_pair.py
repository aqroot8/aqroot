#!/usr/bin/env python3
"""Bound coordinated B.Cu corridors for the rotated U21 LX/raw crossover."""

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

# D-418 fixes R99 +0.5 mm east.  The remaining planar crossover can only put
# the raw arm outside the west/south extent of LX.  These cases bound that
# useful family without disturbing accepted raw distribution copper.
LX_WEST_MM = (55.925, 55.625)
RAW_WEST_MM = (55.100, 54.700)
RAW_SOUTH_MM = (35.300, 34.900, 34.500)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point(x, y):
    return pcbnew.VECTOR2I(round(x * 1e6), round(y * 1e6))


def add_path(board, net_name, coordinates, widths):
    net = board.FindNet(net_name)
    for (ax, ay), (bx, by), width in zip(coordinates, coordinates[1:], widths):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(point(ax, ay)); track.SetEnd(point(bx, by))
        track.SetWidth(round(width * 1e6)); track.SetLayer(pcbnew.B_Cu)
        track.SetNet(net); board.Add(track)


def prepare(path, lx_west, raw_west, raw_south):
    board = pcbnew.LoadBoard(str(BOARD))
    board.FindFootprintByReference("U21").SetOrientationDegrees(180)
    board.FindFootprintByReference("L4").SetOrientationDegrees(180)
    r99 = board.FindFootprintByReference("R99")
    r99.SetPosition(point(r99.GetPosition().x / 1e6 + 0.5,
                          r99.GetPosition().y / 1e6))
    removed = 0
    neck_points = {(58_512_500, 40_400_000), (59_022_500, 40_400_000)}
    for item in list(board.GetTracks()):
        if item.GetNetname() != RAW or isinstance(item, pcbnew.PCB_VIA):
            continue
        a, b = item.GetStart(), item.GetEnd()
        if (a.x, a.y) in neck_points or (b.x, b.y) in neck_points:
            board.Remove(item); removed += 1

    # LX owns the inner lane and reaches L4 without the generic router's
    # diagonal incursion into the raw outer lane.
    lx_points = [(57.0875, 39.9), (55.925, 39.9), (lx_west, 38.8),
                 (56.725, 38.0), (56.725, 36.25), (56.675, 36.2),
                 (57.715, 36.2)]
    add_path(board, LX, lx_points, [0.25, 0.40, 0.40, 0.40, 0.40, 0.40])

    # RAW stays exactly one legal lane below its adjacent U21 launch, then
    # passes outside LX and returns east below L4 before rising to the stable
    # accepted-tree anchor.  The first segment retains the package neck floor.
    raw_points = [(57.0875, 39.4), (55.925, 39.4), (raw_west, 38.55),
                  (raw_west, raw_south), (60.75, raw_south),
                  (60.75, 37.15), (59.0225, 40.4)]
    add_path(board, RAW, raw_points, [0.25, 0.40, 0.40, 0.40, 0.40, 0.40])
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
    return {"lx_west_mm": case[0], "raw_west_mm": case[1],
            "raw_south_mm": case[2], "withdrawn_raw_neck_segments": removed,
            "drc_exit": run.returncode, "drc_types": counts,
            "attributable": attributable, "candidate": not attributable}


def main():
    before = sha256(BOARD)
    cases = list(itertools.product(LX_WEST_MM, RAW_WEST_MM, RAW_SOUTH_MM))
    results = []
    with tempfile.TemporaryDirectory(prefix="aqroot-acc5v-pair-") as td:
        td = Path(td)
        for index, case in enumerate(cases):
            child = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--case",
                 str(index), str(td)], check=True, capture_output=True, text=True)
            results.append(json.loads(next(line for line in reversed(
                child.stdout.splitlines()) if line.startswith("{"))))
    report = {"schema": 1, "tactic": "coordinated LX/raw outer B.Cu corridor",
              "authoritative_board_sha256": before,
              "authoritative_board_unchanged": before == sha256(BOARD),
              "cases": results}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_board_unchanged"] else 2


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--case":
        index = int(sys.argv[2]); td = Path(sys.argv[3])
        cases = list(itertools.product(LX_WEST_MM, RAW_WEST_MM, RAW_SOUTH_MM))
        print(json.dumps(run_case(td / f"case-{index}.kicad_pcb",
                                  td / f"case-{index}-drc.json", cases[index]),
                         sort_keys=True))
        raise SystemExit(0)
    raise SystemExit(main())
