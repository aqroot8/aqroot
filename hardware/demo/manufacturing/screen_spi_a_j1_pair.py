#!/usr/bin/env python3
"""Co-reserve the adjacent J1 SPI-A clock/data fanouts before either haul."""

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
DRU = BOARD.with_suffix(".kicad_dru")
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

TREES = {
    "/SPI_A_SCK": ("J1.36", "U1.20", "J2.5"),
    "/SPI_A_MOSI": ("J1.34", "U1.19", "J2.3"),
}
LAYERS = (("I2", "I3"), ("I3", "I2"))
SITE_INDICES = range(4)
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(path, sck_index, mosi_index, layers):
    board = qr.QBoard(path)
    ir.inject_existing_via_obstacles(board)
    reserved = {}

    # The scarce adjacent connector barrels are always committed first.
    for net, index, layer in (("/SPI_A_SCK", sck_index, layers[0]),
                              ("/SPI_A_MOSI", mosi_index, layers[1])):
        pads = {p["ref"]: p for p in ir.physical_net_pads(board, net)}
        j1, u1, _ = TREES[net]
        row = qr.reserve_escape(board, net, pads[j1], 200_000, 200_000, 200_000,
                                near="F", far=layer, via_dia=600_000,
                                via_drill=300_000, target=(pads[u1]["x"], pads[u1]["y"]),
                                site_index=index, site_separation=300_000)
        reserved[(net, j1)] = row
        if not row.get("ok"):
            return {"ok": False, "stage": "j1-pair", "reserved": reserved}

    # Only after both J1 barrels exist may either bus claim its other endpoints.
    for net, layer in zip(TREES, layers):
        pads = {p["ref"]: p for p in ir.physical_net_pads(board, net)}
        j1, u1, j2 = TREES[net]
        anchor = reserved[(net, j1)]["via"]
        for ref in (u1, j2):
            row = qr.reserve_escape(board, net, pads[ref], 200_000, 200_000, 200_000,
                                    near="F", far=layer, via_dia=600_000,
                                    via_drill=300_000, target=anchor)
            reserved[(net, ref)] = row
            if not row.get("ok"):
                return {"ok": False, "stage": ref, "reserved": reserved}
        for ref in (u1, j2):
            row = qr.join_reserved(board, net, anchor, reserved[(net, ref)]["via"],
                                   200_000, 200_000, 200_000, layer=layer,
                                   G=25_000, fine=25_000)
            if not row.get("ok"):
                return {"ok": False, "stage": f"join-{ref}", "reserved": reserved,
                        "join": row}
    board.save(path)
    return {"ok": True, "stage": "complete", "reserved": reserved}


def main():
    before = sha256(BOARD)
    results = []
    with tempfile.TemporaryDirectory(prefix="aqroot-spi-a-j1-pair-") as td:
        td = Path(td)
        for layers in LAYERS:
            for sck_index in SITE_INDICES:
                for mosi_index in SITE_INDICES:
                    candidate = td / f"{layers[0]}-{sck_index}-{mosi_index}.kicad_pcb"
                    candidate.write_bytes(BOARD.read_bytes())
                    candidate.with_suffix(".kicad_dru").write_bytes(DRU.read_bytes())
                    route = run_case(candidate, sck_index, mosi_index, layers)
                    if not route["ok"]:
                        results.append({"layers": layers, "sites": [sck_index, mosi_index],
                                        "route_ok": False, "stage": route["stage"]})
                        continue
                    out = td / f"drc-{layers[0]}-{sck_index}-{mosi_index}.json"
                    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                                    "--format", "json", "--units", "mm", "--severity-all",
                                    "--schematic-parity", "-o", str(out), str(candidate)],
                                   check=False, capture_output=True, text=True)
                    violations = json.loads(out.read_text()).get("violations", [])
                    types = Counter(v.get("type", "unknown") for v in violations)
                    attributable = sum(n for kind, n in types.items() if kind not in ACCEPTED)
                    results.append({"layers": layers, "sites": [sck_index, mosi_index],
                                    "route_ok": True, "drc_types": dict(types),
                                    "attributable": attributable,
                                    "candidate": attributable == 0})
    report = {"schema": 1, "authoritative_board_sha256": before,
              "authoritative_board_unchanged": before == sha256(BOARD),
              "summary": {
                  "cases": len(results),
                  "route_ok": sum(bool(r.get("route_ok")) for r in results),
                  "failure_stages": dict(sorted(Counter(
                      r.get("stage", "unknown") for r in results if not r.get("route_ok")
                  ).items())),
              },
              "cases": results, "candidates": [r for r in results if r.get("candidate")]}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_board_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
