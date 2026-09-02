#!/usr/bin/env python3
"""Screen a coherent two-clock breakout from the rear-mounted I2S microphone.

The generic inner-haul endpoint search cannot leave MK1.5/MK1.6 because it
looks for an ordinary via before following the package-specific east corridor.
This screen reserves both corridors and vias together.  It intentionally stops
before either long haul: a later atomic route must attach U1 and U5 and pass the
complete connectivity gate before any copper is promoted.
"""

import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge",
            "via_dangling"}
NETS = {
    "LRCLK": ("/I2S_LRCLK", (5.075, 98.280)),
    "BCLK": ("/I2S_BCLK", (5.075, 98.930)),
}
# The 0.65 mm pad pitch cannot accept two 0.60 mm vias in one column.  Stagger
# the via columns while retaining straight, parallel B.Cu package exits.
LAYOUTS = (
    {"LRCLK": (7.000, 98.280), "BCLK": (7.750, 98.930)},
    {"LRCLK": (7.750, 98.280), "BCLK": (7.000, 98.930)},
    {"LRCLK": (7.000, 98.280), "BCLK": (8.000, 98.930)},
    {"LRCLK": (8.000, 98.280), "BCLK": (7.000, 98.930)},
)


def um(value):
    return int(round(value * 1_000_000))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def route_layout(layout, output):
    qb = qr.QBoard(BOARD)
    ir.inject_existing_via_obstacles(qb)
    reserved = []
    for name in ("LRCLK", "BCLK"):
        net, pad_mm = NETS[name]
        via_mm = layout[name]
        via = tuple(map(um, via_mm))
        if not all(qb.point_free(layer, net, *via, 600_000, 200_000,
                                 200_000, 25_000) for layer in qb.cu):
            return {"result": "NO_LEGAL_VIA_SITE", "failed": name}
        start = tuple(map(um, pad_mm))
        qb.track(net, "B", *start, *via, 200_000)
        qb.via(net, *via, 600_000, 300_000)
        reserved.append({"clock": name, "net": net, "pad_mm": pad_mm,
                         "via_mm": via_mm})
    qb.save(output)
    return {"result": "FANOUT_PAIR_RESERVED", "reserved": reserved}


def main():
    before = sha256(BOARD)
    trials = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-mk1-clocks-") as td:
        work = Path(td)
        for index, layout in enumerate(LAYOUTS):
            candidate = work / f"layout-{index}.kicad_pcb"
            report = {"layout": layout}
            report.update(route_layout(layout, candidate))
            if not candidate.exists():
                trials.append(report)
                continue
            candidate.with_suffix(".kicad_dru").write_bytes(
                BOARD.with_suffix(".kicad_dru").read_bytes())
            drc = work / f"layout-{index}-drc.json"
            proc = subprocess.run([
                "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                "--format", "json", "--units", "mm", "--severity-all",
                "--schematic-parity", "-o", str(drc), str(candidate),
            ], text=True, capture_output=True)
            violations = json.loads(drc.read_text()).get("violations", [])
            types = Counter(row.get("type", "unknown") for row in violations)
            attributable = [row for row in violations
                            if row.get("type") not in ACCEPTED]
            report.update(drc_exit=proc.returncode, drc_types=dict(types),
                          attributable_drc_count=len(attributable),
                          attributable_drc=attributable,
                          candidate_sha256=sha256(candidate))
            report["result"] = ("CLEAN_FANOUT_PAIR" if not attributable
                                else "REJECTED_BY_REAL_DRC")
            trials.append(report)
    clean = sum(row["result"] == "CLEAN_FANOUT_PAIR" for row in trials)
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": sha256(BOARD) == before,
        "trials": trials,
        "clean_fanout_pairs": clean,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if clean else 2


if __name__ == "__main__":
    raise SystemExit(main())
