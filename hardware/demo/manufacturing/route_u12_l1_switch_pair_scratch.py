#!/usr/bin/env python3
"""Route and fully gate the two local U12/L1 buck-boost switch nodes."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
NETS = ("Net-(L1-Pad1)", "Net-(L1-Pad2)")
PADS = {
    "Net-(L1-Pad1)": ("L1.1", "U12.8", "U12.9"),
    "Net-(L1-Pad2)": ("L1.2", "U12.6", "U12.7"),
}
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def add_track(board, net, start, end, width):
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(board.FindNet(net))
    track.SetLayer(pcbnew.B_Cu)
    track.SetWidth(width)
    track.SetStart(pcbnew.VECTOR2I(*start))
    track.SetEnd(pcbnew.VECTOR2I(*end))
    board.Add(track)


def route(board):
    mm = lambda x: int(round(x * 1_000_000))
    # U12.8 exits east, clear of the exposed GND pad, then returns around the
    # package north edge to L1.1.  The 0.20 mm U12.8/U12.9 land join is the
    # only sub-trunk segment and remains wholly inside the VSON courtyard.
    geometry = {
        "Net-(L1-Pad1)": [
            ((67.600, 102.800), (68.100, 102.800), 0.200),
            ((68.100, 102.800), (68.875, 102.800), 0.400),
            ((68.875, 102.800), (68.875, 94.400), 0.400),
            ((68.875, 94.400), (65.415, 94.400), 0.400),
            ((65.415, 94.400), (65.415, 96.600), 0.400),
        ],
        # U12.6/U12.7 are adjacent same-net lands facing L1.2.  Join them at
        # package pitch and flare immediately into the short vertical trunk.
        "Net-(L1-Pad2)": [
            ((67.600, 100.000), (68.100, 100.000), 0.200),
            ((67.600, 100.000), (67.600, 99.500), 0.200),
            ((67.600, 99.500), (67.785, 99.315), 0.400),
            ((67.785, 99.315), (67.785, 96.600), 0.400),
        ],
    }
    for net, segments in geometry.items():
        for start, end, width in segments:
            add_track(board, net, tuple(map(mm, start)), tuple(map(mm, end)), mm(width))
    return geometry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    before_sha = sha256(BOARD)
    baseline = copper(pcbnew.LoadBoard(str(BOARD)))
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-u12-l1-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        board = pcbnew.LoadBoard(str(scratch))
        geometry = route(board)
        pcbnew.SaveBoard(str(scratch), board)
        drc = work / "drc.json"
        checked = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = Counter(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED]
        after = copper(pcbnew.LoadBoard(str(scratch)))
        removed = baseline - after
        added = after - baseline
        wrong = [list(item) for item in added if item[0] not in NETS]
        ledger_path = work / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        rows = {r["net"]: r for r in ledger["nets"] if r["net"] in NETS}
        promotion = (set(rows) == set(NETS)
                     and all(rows[n]["open_edges"] == 0 for n in NETS)
                     and not attributable and not removed and not wrong
                     and checked.returncode == 0)
        candidate = scratch.read_bytes()
        if args.candidate and promotion:
            args.candidate.write_bytes(candidate)
        if args.promote:
            if not promotion or sha256(BOARD) != before_sha:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(candidate)
        report = {
            "schema": 1, "authoritative_board_sha256": before_sha,
            "authoritative_unchanged": sha256(BOARD) == before_sha,
            "geometry": geometry, "drc_exit": checked.returncode,
            "drc_types": dict(types), "attributable_drc": attributable,
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "target_open_edges": {n: rows[n]["open_edges"] for n in rows},
            "connectivity": ledger["connectivity"],
            "promotion_candidate": promotion,
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
