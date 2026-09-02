#!/usr/bin/env python3
"""Screen explicit outward package fanouts for the two boxed radio controls.

The generic escape search starts every trial at the pad centre and rejects the
whole segment when a long-axis escape must first follow a package-specific
corridor.  This scratch-only screen supplies that short corridor explicitly
and proves the ordinary-via reservation with real KiCad DRC.  Long-haul routing
is intentionally a later transaction so this bounded screen cannot turn into
an unbounded full-board A* search.
"""

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


TRIALS = {
    "NFC_IRQ": {
        "net": "/NFC_IRQ", "forced": "U9.27", "other": "U1.11",
        "other_near": "F", "forced_near": "B",
        # Leave the south edge of U9, run below pads 25/26, then go around the
        # accepted AGDC fanout's eastern endpoint before planting a via.
        "path_mm": [(34.750, 32.275), (34.750, 32.825),
                    (37.700, 32.825), (37.600, 33.700)],
    },
    "SX1262_DIO1": {
        "net": "/SX1262_DIO1", "forced": "U2.20", "other": "U8.13",
        "other_near": "B", "forced_near": "B",
        # Enter the empty TSSOP body corridor, clearing the accepted BTN_B and
        # ACC_5V_SW_EN fanouts, and use a tented ordinary via under the body.
        "path_mm": [(59.8625, 88.975), (59.050, 88.975),
                    (58.750, 89.250), (57.200, 89.050)],
    },
}


def um(x):
    return int(round(x * 1_000_000))


def run_trial(name, spec, out):
    qb = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(qb)
    pads = {p["ref"]: p for p in ir.physical_net_pads(qb, spec["net"])}
    path = [(um(x), um(y)) for x, y in spec["path_mm"]]
    forced_via = path[-1]
    free = all(qb.point_free(layer, spec["net"], forced_via[0], forced_via[1],
                             600_000, 200_000, 200_000, 25_000)
               for layer in qb.cu)
    if not free:
        return {"name": name, "result": "NO_FORCED_VIA_SITE",
                "forced_via_mm": spec["path_mm"][-1]}

    mark = qb.mark()
    for a, b in zip(path, path[1:]):
        qb.track(spec["net"], spec["forced_near"], *a, *b, 200_000)
    qb.via(spec["net"], *forced_via, 600_000, 300_000)
    qb.save(out)
    return {"name": name, "result": "FANOUT_RESERVED",
            "forced_path_mm": spec["path_mm"],
            "forced_via_mm": spec["path_mm"][-1]}


def main():
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    reports = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-package-fanout-") as td:
        td = Path(td)
        for name, spec in TRIALS.items():
            candidate = td / f"{name}.kicad_pcb"
            report = run_trial(name, spec, candidate)
            if candidate.exists():
                candidate.with_suffix(".kicad_dru").write_bytes(BOARD.with_suffix(".kicad_dru").read_bytes())
                drc = td / f"{name}-drc.json"
                proc = subprocess.run([
                    "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                    "--format", "json", "--units", "mm", "--severity-all",
                    "--schematic-parity", "-o", str(drc), str(candidate),
                ], text=True, capture_output=True)
                data = json.loads(drc.read_text()) if drc.exists() else {}
                types = {}
                for row in data.get("violations", []):
                    types[row.get("type", "unknown")] = types.get(row.get("type", "unknown"), 0) + 1
                attributable = [row for row in data.get("violations", [])
                                if row.get("type") not in {
                                    "lib_footprint_issues", "hole_clearance",
                                    "solder_mask_bridge", "via_dangling"}]
                report.update(drc_exit=proc.returncode, drc_types=types,
                              attributable_drc=attributable)
                if attributable:
                    report["result"] = "REJECTED_BY_REAL_DRC"
            reports.append(report)
    print(json.dumps({
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "trials": reports, "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
