#!/usr/bin/env python3
"""Screen an LX-first, accepted-tree-preserving ACC_5V boost-core refloor."""

import hashlib
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

# Bounded inductor offsets around the D-416 rotation-only wall.  U21 stays in
# place so every non-LX package endpoint remains a deterministic replay target.
CASES_MM = ((0.0, 0.0), (0.0, 0.5), (0.0, 1.0), (-0.5, 0.5), (0.5, 0.5))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_mm(x, y):
    return pcbnew.VECTOR2I(round(x * 1e6), round(y * 1e6))


def prepare(path, dx, dy):
    board = pcbnew.LoadBoard(str(BOARD))
    u21 = board.FindFootprintByReference("U21")
    l4 = board.FindFootprintByReference("L4")
    u21.SetOrientationDegrees(180)
    l4.SetOrientationDegrees(180)
    old = l4.GetPosition()
    l4.SetPosition(point_mm(old.x / 1e6 + dx, old.y / 1e6 + dy))
    pcbnew.SaveBoard(str(path), board)
    board = pcbnew.LoadBoard(str(path))

    # Preserve the accepted five-via raw-output distribution tree verbatim.
    # Withdraw only its old U21.6 package neck, whose endpoint moves on rotate.
    removed = []
    for item in list(board.GetTracks()):
        if item.GetNetname() != RAW or isinstance(item, pcbnew.PCB_VIA):
            continue
        a, b = item.GetStart(), item.GetEnd()
        if (a.x, a.y) in ((58_512_500, 40_400_000), (59_022_500, 40_400_000)) or \
           (b.x, b.y) in ((58_512_500, 40_400_000), (59_022_500, 40_400_000)):
            removed.append(((a.x, a.y), (b.x, b.y)))
            board.Remove(item)

    pcbnew.SaveBoard(str(path), board)
    path.with_suffix(".kicad_dru").write_bytes(DRU.read_bytes())
    return len(removed)


def add_raw_neck(path):
    board = pcbnew.LoadBoard(str(path))
    # Rotated U21.6 -> the stable accepted tree anchor. LX must already own its
    # escape before this branch is restored (D-416's material route ordering).
    net = board.FindNet(RAW)
    sx, sy = 57_087_500, 39_400_000
    start = pcbnew.VECTOR2I(sx, sy)
    elbow = point_mm(sx / 1e6 - 0.510, sy / 1e6)
    anchor = point_mm(59.0225, 40.4)
    for a, b, width in ((start, elbow, 0.25), (elbow, anchor, 0.40)):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(a); track.SetEnd(b); track.SetWidth(round(width * 1e6))
        track.SetLayer(pcbnew.B_Cu); track.SetNet(net); board.Add(track)
    pcbnew.SaveBoard(str(path), board)


def main():
    before = sha256(BOARD)
    results = []
    with tempfile.TemporaryDirectory(prefix="aqroot-acc5v-bcu-") as td:
        td = Path(td)
        for index, (dx, dy) in enumerate(CASES_MM):
            child = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                    "--case", str(index), str(td)],
                                   capture_output=True, text=True, check=True)
            line = next(x for x in reversed(child.stdout.splitlines()) if x.startswith("{"))
            results.append(json.loads(line))
    report = {"schema": 1, "authoritative_board_sha256": before,
              "authoritative_board_unchanged": before == sha256(BOARD), "cases": results}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_board_unchanged"] else 2


def run_case(index, td):
    dx, dy = CASES_MM[index]
    candidate = td / f"case-{index}.kicad_pcb"
    removed = prepare(candidate, dx, dy)
    lx = subprocess.run([sys.executable, str(ROUTER), "ACC_5V_LX", "--route", str(candidate)],
                        capture_output=True, text=True, check=True)
    lx_result = json.loads(lx.stdout.strip().splitlines()[-1])["result"]
    subprocess.run([sys.executable, str(Path(__file__).resolve()), "--neck", str(candidate)],
                   capture_output=True, text=True, check=True)
    drc_path = td / f"case-{index}-drc.json"
    drc = subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                          "--format", "json", "--units", "mm", "--severity-all",
                          "--schematic-parity", "-o", str(drc_path), str(candidate)],
                         capture_output=True, text=True)
    violations = json.loads(drc_path.read_text()).get("violations", [])
    types = {}
    for row in violations:
        types[row.get("type", "unknown")] = types.get(row.get("type", "unknown"), 0) + 1
    attributable = [row for row in violations if row.get("type") not in {
        "lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}]
    print(json.dumps({"l4_offset_mm": [dx, dy], "withdrawn_raw_neck_segments": removed,
                      "acc_5v_lx": lx_result, "drc_exit": drc.returncode,
                      # KiCad can classify coincident scratch collisions as a
                      # short versus crossing nondeterministically.  Normalize
                      # the gate to the stable engineering predicates.
                      "drc_has_attributable": bool(attributable),
                      "courtyard_overlap": types.get("courtyards_overlap", 0) > 0,
                      "candidate": lx_result.get("ok") and not attributable}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--neck":
        add_raw_neck(Path(sys.argv[2]))
        raise SystemExit(0)
    if len(sys.argv) == 4 and sys.argv[1] == "--case":
        run_case(int(sys.argv[2]), Path(sys.argv[3]))
        raise SystemExit(0)
    raise SystemExit(main())
