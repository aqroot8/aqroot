#!/usr/bin/env python3
"""Bound U9 poses that unlock both VDD_D/VDD_A package escapes.

This is characterization-only.  Moving U9 invalidates accepted pad-attached
copper, so the screen records that replay boundary and never writes a candidate.
Translations are included only to distinguish board-obstacle effects from the
rotation-dependent package-pin geometry.
"""

import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

TARGETS = {
    "NFC_VDD_D": ("/04_SPI_B_RADIOS_NFC/NFC_VDD_D", "U9.3"),
    "NFC_VDD_A": ("/04_SPI_B_RADIOS_NFC/NFC_VDD_A", "U9.7"),
}
OFFSETS_MM = (-0.5, 0.0, 0.5)
ROTATIONS_DEG = (0.0, 90.0, 180.0, 270.0)
WIDTH = 300_000
CLEARANCE = 200_000
GRID = 25_000
ACCEPTED_DRC = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def attached_copper(board, footprint):
    rows = []
    pads = list(footprint.Pads())
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            continue
        hit = [pad.GetNumber() for pad in pads
               if pad.HitTest(item.GetStart()) or pad.HitTest(item.GetEnd())]
        if hit:
            rows.append({"net": item.GetNetname(), "layer": item.GetLayerName(),
                         "width_mm": item.GetWidth() / 1e6,
                         "u9_pads": sorted(set(hit))})
    return rows


def main() -> int:
    before = sha256(BOARD)
    authority = pcbnew.LoadBoard(str(BOARD))
    u9 = authority.FindFootprintByReference("U9")
    origin = u9.GetPosition()
    original_rotation = u9.GetOrientationDegrees()
    replay = attached_copper(authority, u9)
    rows = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-u9-refloor-") as td:
        work = Path(td)
        for dx, dy, rotation in itertools.product(OFFSETS_MM, OFFSETS_MM, ROTATIONS_DEG):
            scratch = work / f"u9-{dx:+.1f}-{dy:+.1f}-{rotation:.0f}.kicad_pcb"
            scratch.write_bytes(BOARD.read_bytes())
            scratch.with_suffix(".kicad_dru").write_bytes(
                BOARD.with_suffix(".kicad_dru").read_bytes())
            scratch.with_suffix(".kicad_pro").write_bytes(
                BOARD.with_suffix(".kicad_pro").read_bytes())
            candidate = pcbnew.LoadBoard(str(scratch))
            moved = candidate.FindFootprintByReference("U9")
            moved.SetPosition(pcbnew.VECTOR2I(origin.x + round(dx * 1e6),
                                              origin.y + round(dy * 1e6)))
            moved.SetOrientationDegrees(rotation)
            pcbnew.SaveBoard(str(scratch), candidate)
            qb = qr.QBoard(scratch)
            ir.inject_existing_via_obstacles(qb)
            launches = {}
            failures = {}
            for name, (net, ref) in TARGETS.items():
                pads = {pad["ref"]: pad for pad in ir.physical_net_pads(qb, net)}
                found = qb.escape(pads[ref], "B", WIDTH, WIDTH, CLEARANCE,
                                  CLEARANCE, GRID, qb.ex0, qb.ey0)
                launches[name] = len(found)
                failures[name] = None if found else qb.escape_why[0]
            rows.append({"offset_mm": [dx, dy], "rotation_deg": rotation,
                         "launch_counts": launches, "failures": failures,
                         "both_rails_escape": all(launches.values())})

        viable = [row for row in rows if row["both_rails_escape"]]
        # Run real DRC on the best geometrically viable pose only.  It is an
        # impact measurement, not a candidate gate: accepted U9 copper has not
        # yet been withdrawn/replayed.
        drc_summary = None
        if viable:
            best = min(viable, key=lambda row: (
                abs(row["offset_mm"][0]) + abs(row["offset_mm"][1]),
                -sum(row["launch_counts"].values()), row["rotation_deg"]))
            dx, dy = best["offset_mm"]
            scratch = work / f"u9-{dx:+.1f}-{dy:+.1f}-{best['rotation_deg']:.0f}.kicad_pcb"
            drc = work / "best-drc.json"
            proc = subprocess.run([
                "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                "--format", "json", "--units", "mm", "--severity-all",
                "--schematic-parity", "-o", str(drc), str(scratch),
            ], text=True, capture_output=True)
            violations = json.loads(drc.read_text()).get("violations", [])
            types = Counter(v.get("type", "unknown") for v in violations)
            drc_summary = {"pose": best, "exit": proc.returncode,
                           "types": dict(types),
                           "attributable_count": sum(
                               v.get("type") not in ACCEPTED_DRC for v in violations)}

    report = {
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": before == sha256(BOARD),
        "contract": {"u9_origin_mm": [origin.x / 1e6, origin.y / 1e6],
                     "u9_original_rotation_deg": original_rotation,
                     "offsets_mm": list(OFFSETS_MM),
                     "rotations_deg": list(ROTATIONS_DEG),
                     "layer": "B.Cu", "width_mm": 0.3,
                     "clearance_mm": 0.2, "grid_mm": 0.025},
        "cases_tested": len(rows), "viable_case_count": len(viable),
        "viable_cases": viable,
        "accepted_u9_pad_attached_replay_items": len(replay),
        "accepted_u9_pad_attached_replay_by_net": dict(Counter(r["net"] for r in replay)),
        "accepted_u9_pad_attached_replay": replay,
        "best_pose_unreplayed_drc": drc_summary,
        "rows": rows,
        "promotion_candidate": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
