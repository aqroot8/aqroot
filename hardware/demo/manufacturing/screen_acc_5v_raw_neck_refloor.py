#!/usr/bin/env python3
"""Bound R99 placement and B.Cu raw-neck geometry after the D-417 screen."""

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
ROUTER = ROOT / "hardware/demo/manufacturing/route_local_two_pad.py"
RAW = "/01_POWER_TREE/ACC_5V_RAW"

# R99 is the only newly admitted placement member.  Eastward moves preserve its
# feedback-divider ordering and pull it away from the rotated L4 courtyard.
R99_OFFSETS_MM = ((0.5, 0.0), (1.0, 0.0), (1.5, 0.0), (1.0, -0.5))

# Explicit B.Cu necks cross from the rotated U21.6 west side to the immutable
# accepted raw-tree anchor.  They bound the two meaningful obstacle families:
# above the ACC_DETECT_N suffix, or below its via/vertical B.Cu branch.
NECKS_MM = {
    "north_tight": ((57.0875, 39.4), (56.55, 41.35), (58.45, 41.35), (59.0225, 40.4)),
    "north_wide": ((57.0875, 39.4), (56.20, 41.65), (58.70, 41.65), (59.0225, 40.4)),
    "south_tight": ((57.0875, 39.4), (56.55, 37.80), (58.55, 37.80), (59.0225, 40.4)),
    "south_wide": ((57.0875, 39.4), (56.20, 37.35), (59.10, 37.35), (59.0225, 40.4)),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_mm(x, y):
    return pcbnew.VECTOR2I(round(x * 1e6), round(y * 1e6))


def prepare(path, r99_dx, r99_dy):
    board = pcbnew.LoadBoard(str(BOARD))
    board.FindFootprintByReference("U21").SetOrientationDegrees(180)
    board.FindFootprintByReference("L4").SetOrientationDegrees(180)
    r99 = board.FindFootprintByReference("R99")
    old = r99.GetPosition()
    r99.SetPosition(point_mm(old.x / 1e6 + r99_dx, old.y / 1e6 + r99_dy))

    removed = 0
    for item in list(board.GetTracks()):
        if item.GetNetname() != RAW or isinstance(item, pcbnew.PCB_VIA):
            continue
        a, b = item.GetStart(), item.GetEnd()
        neck_points = {(58_512_500, 40_400_000), (59_022_500, 40_400_000)}
        if (a.x, a.y) in neck_points or (b.x, b.y) in neck_points:
            board.Remove(item)
            removed += 1
    pcbnew.SaveBoard(str(path), board)
    path.with_suffix(".kicad_dru").write_bytes(DRU.read_bytes())
    return removed


def add_neck(path, name):
    board = pcbnew.LoadBoard(str(path))
    net = board.FindNet(RAW)
    points = [point_mm(*p) for p in NECKS_MM[name]]
    for index, (a, b) in enumerate(zip(points, points[1:])):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(a)
        track.SetEnd(b)
        track.SetWidth(250_000 if index == 0 else 400_000)
        track.SetLayer(pcbnew.B_Cu)
        track.SetNet(net)
        board.Add(track)
    pcbnew.SaveBoard(str(path), board)


def violation_summary(rows):
    counts = {}
    implicated = []
    ignored = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
    for row in rows:
        kind = row.get("type", "unknown")
        counts[kind] = counts.get(kind, 0) + 1
        if kind not in ignored:
            implicated.append({"type": kind, "description": row.get("description", "")})
    return counts, implicated


def run_case(index, temporary):
    combinations = list(itertools.product(R99_OFFSETS_MM, NECKS_MM))
    (dx, dy), neck = combinations[index]
    candidate = temporary / f"case-{index}.kicad_pcb"
    removed = prepare(candidate, dx, dy)
    lx_run = subprocess.run(
        [sys.executable, str(ROUTER), "ACC_5V_LX", "--route", str(candidate)],
        check=True, capture_output=True, text=True,
    )
    lx = json.loads(lx_run.stdout.strip().splitlines()[-1])["result"]
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--neck", neck, str(candidate)],
        check=True, capture_output=True, text=True,
    )
    drc_path = temporary / f"case-{index}-drc.json"
    drc = subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(drc_path), str(candidate),
    ], capture_output=True, text=True)
    counts, attributable = violation_summary(json.loads(drc_path.read_text()).get("violations", []))
    print(json.dumps({
        "r99_offset_mm": [dx, dy], "neck": neck,
        "withdrawn_raw_neck_segments": removed, "acc_5v_lx": lx,
        "drc_exit": drc.returncode, "drc_types": counts,
        "attributable": attributable,
        "candidate": lx.get("ok") and not attributable,
    }, sort_keys=True))


def main():
    before = sha256(BOARD)
    combinations = list(itertools.product(R99_OFFSETS_MM, NECKS_MM))
    results = []
    with tempfile.TemporaryDirectory(prefix="aqroot-acc5v-raw-neck-") as td:
        temporary = Path(td)
        for index in range(len(combinations)):
            child = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--case", str(index), str(temporary)],
                check=True, capture_output=True, text=True,
            )
            results.append(json.loads(next(x for x in reversed(child.stdout.splitlines()) if x.startswith("{"))))
    report = {
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_board_unchanged": before == sha256(BOARD),
        "cases": results,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_board_unchanged"] else 2


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--neck":
        add_neck(Path(sys.argv[3]), sys.argv[2])
        raise SystemExit(0)
    if len(sys.argv) == 4 and sys.argv[1] == "--case":
        run_case(int(sys.argv[2]), Path(sys.argv[3]))
        raise SystemExit(0)
    raise SystemExit(main())
