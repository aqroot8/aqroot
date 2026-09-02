#!/usr/bin/env python3
"""Bound R33/R34 pivot refloors that preserve the accepted ESD-side copper."""

import hashlib
import json
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
ANGLES = (0, 90, 180, 270)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_mm(point) -> list[float]:
    return [round(point.x / 1e6, 6), round(point.y / 1e6, 6)]


def rotate_about_pad_one(board, reference: str, degrees: int) -> None:
    footprint = board.FindFootprintByReference(reference)
    anchor = next(pad.GetPosition() for pad in footprint.Pads() if pad.GetNumber() == "1")
    footprint.Rotate(anchor, pcbnew.EDA_ANGLE(degrees, pcbnew.DEGREES_T))


def route_pose(source: Path, work: Path, n_angle: int, p_angle: int) -> dict:
    scratch = work / f"usb-order-{n_angle}-{p_angle}.kicad_pcb"
    scratch.write_bytes(source.read_bytes())
    board = pcbnew.LoadBoard(str(scratch))
    anchors_before = {
        ref: next(pad.GetPosition() for pad in board.FindFootprintByReference(ref).Pads()
                  if pad.GetNumber() == "1")
        for ref in ("R33", "R34")
    }
    rotate_about_pad_one(board, "R33", n_angle)
    rotate_about_pad_one(board, "R34", p_angle)
    pcbnew.SaveBoard(str(scratch), board)

    moved = pcbnew.LoadBoard(str(scratch))
    pads = {}
    anchors_preserved = True
    for ref in ("R33", "R34"):
        footprint = moved.FindFootprintByReference(ref)
        for pad in footprint.Pads():
            if pad.GetNumber() in ("1", "2"):
                pads[f"{ref}.{pad.GetNumber()}"] = point_mm(pad.GetPosition())
        pad_one = next(pad.GetPosition() for pad in footprint.Pads() if pad.GetNumber() == "1")
        anchors_preserved &= pad_one == anchors_before[ref]
    return {
        "angles_deg": {"R33": n_angle, "R34": p_angle},
        "accepted_pad1_anchors_preserved": anchors_preserved,
        "pad_centres_mm": pads,
        "mcu_pad2_order": "N-left-of-P" if pads["R33.2"][0] < pads["R34.2"][0]
        else "P-left-of-N",
    }


def main() -> int:
    before = sha256(BOARD)
    board = pcbnew.LoadBoard(str(BOARD))
    anchors = {}
    radii = {}
    for ref in ("R33", "R34"):
        footprint = board.FindFootprintByReference(ref)
        lands = {pad.GetNumber(): pad.GetPosition() for pad in footprint.Pads()}
        anchors[ref] = lands["1"]
        radii[ref] = ((lands["2"].x - lands["1"].x) ** 2
                      + (lands["2"].y - lands["1"].y) ** 2) ** 0.5
    continuous_minimum_x_separation = (
        anchors["R34"].x - anchors["R33"].x - radii["R33"] - radii["R34"]
    )
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-order-") as temporary:
        work = Path(temporary)
        poses = [route_pose(BOARD, work, n, p) for n in ANGLES for p in ANGLES]
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == sha256(BOARD),
        "contract": "pivot each series resistor about its accepted ESD-side pad-1 anchor; F.Cu only, zero vias",
        "poses_tested": len(poses),
        "reversed_endpoint_order_poses": sum(p["mcu_pad2_order"] == "P-left-of-N" for p in poses),
        "continuous_rotation_bound": {
            "pad1_anchor_x_separation_mm": round((anchors["R34"].x - anchors["R33"].x) / 1e6, 6),
            "pad1_to_pad2_radius_mm": {ref: round(radius / 1e6, 6) for ref, radius in radii.items()},
            "minimum_possible_p_minus_n_pad2_x_mm": round(continuous_minimum_x_separation / 1e6, 6),
            "endpoint_order_can_reverse": continuous_minimum_x_separation <= 0,
        },
        "poses": poses,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
