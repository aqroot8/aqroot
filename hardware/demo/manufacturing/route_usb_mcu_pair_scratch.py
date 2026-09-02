#!/usr/bin/env python3
"""Screen the endpoint-order crossover for the MCU-side USB pair."""

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

PAIR = (
    ("/USB_D_MCU_N", "R33.2", "U1.13", "I2"),
    ("/USB_D_MCU_P", "R34.2", "U1.14", "I3"),
)
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = sha256(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-mcu-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        board = qr.QBoard(scratch)
        ir.inject_existing_via_obstacles(board)
        routes = []
        for net, start, end, inner in PAIR:
            pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, net)}
            result = qr.connect_hop(
                board, net, pads[start], pads[end], 230_000, 200_000, 200_000,
                near="F", far=inner, G=25_000, fine=25_000,
                via_dia=600_000, via_drill=300_000,
            )
            routes.append({"net": net, "inner": inner, "result": result})
        board.save(scratch)
        drc = work / "drc.json"
        completed = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = {}
        for violation in violations:
            kind = violation.get("type", "unknown")
            types[kind] = types.get(kind, 0) + 1
        attributable = [{"type": v["type"], "description": v["description"]}
                        for v in violations if v.get("type") not in ACCEPTED]
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == sha256(BOARD),
        "tactic": "symmetric two-via crossover on separate inner signal layers",
        "routes": routes,
        "drc_exit": completed.returncode,
        "drc_types": types,
        "attributable_drc": attributable,
        "promotion_candidate": all(r["result"].get("ok") for r in routes) and not attributable,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
