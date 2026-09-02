#!/usr/bin/env python3
"""Enumerate legal package-neck landings for the Demo switched 3.3 V rail.

Scratch only.  The complete ACC_3V3_SW spanning tree is already proven, but
the first candidate used fixed U20.5 and U16.8 power-via coordinates that
collide with retained copper.  This screen lays only each accepted-length
package neck, then enumerates materially distinct B.Cu-reachable ordinary
0.90/0.40 mm through-via sites that clear every copper layer and every hole.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

NET = "/ACC_3V3_SW"
ENDPOINTS = ("U20.5", "U16.8")


def scan(path: Path) -> list[dict]:
    results = []
    for ref in ENDPOINTS:
        routed = qr.QBoard(path)
        ir.inject_existing_via_obstacles(routed)
        pads = {pad["ref"]: pad for pad in ir.physical_net_pads(routed, NET)}
        pad = pads[ref]
        flare = routed.flare(
            NET, pad, "B", 400_000, 250_000, 250_000, 250_000, 25_000
        )
        if flare is None:
            results.append({"pad": ref, "face": "B.Cu", "flare": None,
                            "site_count": 0, "sites_mm": []})
            continue
        escape = {"x": flare["x"], "y": flare["y"], "ln": 0, "w": 400_000}
        candidates = routed.via_sites(
            "B", "I2", NET, escape,
            width=400_000, via_dia=900_000,
            clr_pad=250_000, clr_trk=250_000,
            G=25_000, span=5_000_000,
            via_drill=400_000, hole_clr=250_000,
            limit=96, separation=450_000,
        )
        sites = []
        for x, y in candidates:
            if not all(routed.point_free(
                layer, NET, x, y, 900_000, 250_000, 250_000, 25_000
            ) for layer in routed.cu):
                continue
            sites.append([round(x / 1e6, 3), round(y / 1e6, 3)])
        results.append({
            "pad": ref,
            "pad_position_mm": [round(pad["x"] / 1e6, 3), round(pad["y"] / 1e6, 3)],
            "face": "B.Cu",
            "flare_end_mm": [round(flare["x"] / 1e6, 4), round(flare["y"] / 1e6, 4)],
            "flare_segments": flare["segs"],
            "neck_width_mm": 0.25,
            "neck_length_mm": flare["neck_len"],
            "sub_trunk_length_mm": flare["sub_trunk"],
            "trunk_width_mm": 0.40,
            "site_count": len(sites),
            "sites_mm": sites,
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--scan", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.scan:
        print(json.dumps(scan(args.scan), sort_keys=True))
        return 0

    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-acc-3v3-landings-") as temporary:
        scratch = Path(temporary) / BOARD.name
        scratch.write_bytes(BOARD.read_bytes())
        completed = subprocess.run(
            [sys.executable, __file__, "--scan", str(scratch)],
            check=True, text=True, capture_output=True,
        )
        endpoints = json.loads(completed.stdout)
    after = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    report = {
        "schema": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == after,
        "net": NET,
        "method": "package_neck_then_BCu_reachable_all_layer_power_via_enumeration_25um",
        "power_via_mm": {"diameter": 0.90, "drill": 0.40},
        "site_separation_mm": 0.45,
        "endpoints": endpoints,
        "zero_site_pads": [row["pad"] for row in endpoints if not row["site_count"]],
        "promotion_candidate": False,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
