#!/usr/bin/env python3
"""Screen the atomic ACC_5V_RAW/ACC_5V_LX core after the U21/L4 refloor."""

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
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

RAW = "/01_POWER_TREE/ACC_5V_RAW"
RAW_ORDER = ("C65.1", "R99.1", "C66.1", "TP28.1", "U22.2")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def route_tree(routed, net, order):
    pads = {p["ref"]: p for p in ir.physical_net_pads(routed, net)}
    centroid = (round(sum(pads[r]["x"] for r in order) / len(order)),
                round(sum(pads[r]["y"] for r in order) / len(order)))
    reservations = []
    for ref in order:
        row = qr.reserve_escape(
            routed, net, pads[ref], 400_000, 250_000, 250_000,
            near="B", far="I3", G=25_000, fine=25_000,
            via_dia=900_000, via_drill=400_000, target=centroid,
            site_separation=450_000,
        )
        reservations.append({"pad": ref, **row})
        if not row.get("ok"):
            return reservations, []
    parent = list(range(len(reservations)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    pairs = sorted(
        ((a, b) for a in range(len(reservations)) for b in range(a + 1, len(reservations))),
        key=lambda p: ((reservations[p[0]]["via"][0] - reservations[p[1]]["via"][0]) ** 2
                       + (reservations[p[0]]["via"][1] - reservations[p[1]]["via"][1]) ** 2),
    )
    joins = []
    for a, b in pairs:
        if root(a) == root(b):
            continue
        result = None
        for layer in ("I3", "I2"):
            result = qr.join_reserved(
                routed, net, reservations[a]["via"], reservations[b]["via"],
                400_000, 250_000, 250_000, layer=layer, G=25_000, fine=25_000,
            )
            if result.get("ok"):
                result["selected_layer"] = layer
                break
        joins.append({"a": reservations[a]["pad"], "b": reservations[b]["pad"], **result})
        if not result.get("ok"):
            break
        parent[root(b)] = root(a)
        if len(joins) == len(reservations) - 1:
            break
    return reservations, joins


def route_core(candidate):
    routed = qr.QBoard(candidate)
    ir.inject_existing_via_obstacles(routed)
    pads = {p["ref"]: p for p in ir.physical_net_pads(routed, RAW)}
    neck_x = pads["U21.6"]["x"] - 510_000
    routed.track(RAW, "B", pads["U21.6"]["x"], pads["U21.6"]["y"],
                 neck_x, pads["U21.6"]["y"], 250_000)
    routed.track(RAW, "B", neck_x, pads["U21.6"]["y"],
                 pads["C65.1"]["x"], pads["C65.1"]["y"], 400_000)
    reservations, joins = route_tree(routed, RAW, RAW_ORDER)
    routed.save(candidate)
    print(json.dumps({"reservations": reservations, "joins": joins}, sort_keys=True))


def main():
    before = sha256(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-acc5v-core-") as td:
        candidate = Path(td) / BOARD.name
        candidate.write_bytes(BOARD.read_bytes())
        candidate.with_suffix(".kicad_dru").write_bytes(DRU.read_bytes())
        board = pcbnew.LoadBoard(str(candidate))
        board.FindFootprintByReference("U21").SetOrientationDegrees(180)
        board.FindFootprintByReference("L4").SetOrientationDegrees(180)
        removed = 0
        for item in list(board.GetTracks()):
            if item.GetNetname() == RAW:
                board.Remove(item)
                removed += 1
        pcbnew.SaveBoard(str(candidate), board)

        lx = subprocess.run(
            [sys.executable, str(ROUTER), "ACC_5V_LX", "--route", str(candidate)],
            check=True, capture_output=True, text=True,
        )
        lx_result = json.loads(lx.stdout.strip().splitlines()[-1])["result"]
        core = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--route-core", str(candidate)],
            check=True, capture_output=True, text=True,
        )
        core_result = json.loads(core.stdout.strip().splitlines()[-1])
        reservations, joins = core_result["reservations"], core_result["joins"]
        drc_path = Path(td) / "drc.json"
        drc = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc_path), str(candidate),
        ], capture_output=True, text=True)
        violations = json.loads(drc_path.read_text()).get("violations", [])
        types = {}
        for row in violations:
            types[row.get("type", "unknown")] = types.get(row.get("type", "unknown"), 0) + 1
        attributable = [row for row in violations if row.get("type") not in {
            "lib_footprint_issues", "hole_clearance", "solder_mask_bridge"
        }]
        raw_complete = (len(reservations) == 5 and len(joins) == 4
                        and all(x.get("ok") for x in reservations + joins))
        report = {
            "schema": 1, "authoritative_board_sha256": before,
            "authoritative_board_unchanged": before == sha256(BOARD),
            "placement": {"U21_rotation_deg": 180, "L4_rotation_deg": 180},
            "withdrawn_acc_5v_raw_objects": removed,
            "acc_5v_raw": {"complete": raw_complete, "reservations": reservations, "joins": joins},
            "acc_5v_lx": lx_result, "drc_exit": drc.returncode,
            "drc_types": types, "attributable_drc": attributable,
            "power_core_candidate": raw_complete and lx_result.get("ok") and not attributable,
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_board_unchanged"] else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--route-core":
        route_core(Path(sys.argv[2]))
        raise SystemExit(0)
    raise SystemExit(main())
