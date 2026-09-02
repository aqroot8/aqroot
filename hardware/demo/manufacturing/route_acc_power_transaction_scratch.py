#!/usr/bin/env python3
"""Build the atomic fault-refloor plus ACC_5V_RAW power route in scratch."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
ROUTER_DIR = ROOT / "hardware/beta-v2/checks"
sys.path.insert(0, str(ROUTER_DIR))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

FAULT = "/ACC_POWER_FAULT_N"
POWER = "/01_POWER_TREE/ACC_5V_RAW"
MOVES_MM = {"TP9": (49.50, 39.25), "TP10": (63.50, 42.75), "R50": (49.50, 57.735)}
FAULT_ORDER = ("U22.6", "R103.2", "U20.6", "TP27.1", "U3.18", "TP33.1")
POWER_ORDER = ("C65.1", "R99.1", "C66.1", "TP28.1", "U22.2")
NECK_LENGTH_UM = int(os.environ.get("AQROOT_ACC_NECK_LENGTH_UM", "510"))


def point(x, y):
    return pcbnew.VECTOR2I(round(x * 1e6), round(y * 1e6))


def route_tree(routed, net, order, width, clearance, via_dia, via_drill, layers, targets=None):
    pads = {p["ref"]: p for p in ir.physical_net_pads(routed, net)}
    centroid = (round(sum(pads[r]["x"] for r in order) / len(order)),
                round(sum(pads[r]["y"] for r in order) / len(order)))
    reservations = []
    for ref in order:
        result = qr.reserve_escape(
            routed, net, pads[ref], width, clearance, clearance,
            near="B", far=layers[0], G=25_000, fine=25_000,
            via_dia=via_dia, via_drill=via_drill,
            target=(targets or {}).get(ref, centroid),
            site_separation=max(via_dia // 2, 300_000),
        )
        reservations.append({"pad": ref, **result})
        if not result.get("ok"):
            return reservations, []

    parent = list(range(len(reservations)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    edges = sorted(
        ((i, j) for i in range(len(reservations)) for j in range(i + 1, len(reservations))),
        key=lambda pair: (
            (reservations[pair[0]]["via"][0] - reservations[pair[1]]["via"][0]) ** 2
            + (reservations[pair[0]]["via"][1] - reservations[pair[1]]["via"][1]) ** 2
        ),
    )
    joins = []
    for a, b in edges:
        if root(a) == root(b):
            continue
        result = None
        for layer in layers:
            result = qr.join_reserved(
                routed, net, reservations[a]["via"], reservations[b]["via"],
                width, clearance, clearance, layer=layer, G=25_000, fine=25_000,
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


def route_scratch(path):
    routed = qr.QBoard(path)
    ir.inject_existing_via_obstacles(routed)
    fault_pads = {p["ref"]: p for p in ir.physical_net_pads(routed, FAULT)}
    fault_targets = {
        "U3.18": (fault_pads["TP33.1"]["x"], fault_pads["TP33.1"]["y"]),
        "TP33.1": (fault_pads["U3.18"]["x"], fault_pads["U3.18"]["y"]),
    }
    fault_res, fault_joins = route_tree(
        routed, FAULT, FAULT_ORDER, 200_000, 200_000, 600_000, 300_000,
        ("I3", "I2"), fault_targets,
    )
    power_res, power_joins = [], []
    if len(fault_joins) == 5 and all(row.get("ok") for row in fault_res + fault_joins):
        # U21.6 is boxed by its own 0.15 mm-pitch neighbour pads at power width.
        # Use the intended output-capacitor branch as its package escape; C65's
        # larger land then owns the compliant power via.
        power_pads = {p["ref"]: p for p in ir.physical_net_pads(routed, POWER)}
        neck_end_x = power_pads["U21.6"]["x"] + NECK_LENGTH_UM * 1_000
        routed.track(POWER, "B", power_pads["U21.6"]["x"], power_pads["U21.6"]["y"],
                     neck_end_x, power_pads["U21.6"]["y"], 250_000)
        routed.track(POWER, "B", neck_end_x, power_pads["U21.6"]["y"],
                     power_pads["C65.1"]["x"], power_pads["C65.1"]["y"], 400_000)
        power_res, power_joins = route_tree(
            routed, POWER, POWER_ORDER, 400_000, 250_000, 900_000, 400_000,
            ("I3", "I2"),
        )
    routed.save(path)
    print(json.dumps({"fault": {"reservations": fault_res, "joins": fault_joins},
                      "power": {"reservations": power_res, "joins": power_joins}}, sort_keys=True))


def main():
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(BOARD))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, xy in MOVES_MM.items():
        footprints[ref].SetPosition(point(*xy))
    removed = 0
    for item in list(board.GetTracks()):
        if item.GetNetname() == FAULT:
            board.Remove(item)
            removed += 1

    with tempfile.TemporaryDirectory(prefix="aqroot-demo-power-transaction-") as temporary:
        scratch = Path(temporary) / BOARD.name
        scratch.with_suffix(".kicad_dru").write_bytes(BOARD.with_suffix(".kicad_dru").read_bytes())
        board.Save(str(scratch))
        child = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--route", str(scratch)],
            check=True, text=True, capture_output=True,
        )
        route = json.loads(child.stdout)
        drc = Path(temporary) / "drc.json"
        completed = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all", "--schematic-parity",
            "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", []) if drc.exists() else []
        types = {}
        for row in violations:
            types[row.get("type", "unknown")] = types.get(row.get("type", "unknown"), 0) + 1
        attributable = [row for row in violations if row.get("type") not in {
            "lib_footprint_issues", "hole_clearance", "solder_mask_bridge"
        }]

    power = route["power"]
    complete = (len(power["reservations"]) == 5 and len(power["joins"]) == 4
                and all(row.get("ok") for row in power["reservations"] + power["joins"]))
    report = {
        "schema": 1, "authoritative_board_sha256": before,
        "neck_length_mm": NECK_LENGTH_UM / 1000,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "scratch_moves_mm": MOVES_MM, "withdrawn_fault_objects": removed,
        "fault": route["fault"], "power": power,
        "complete_transaction": complete, "drc_exit": completed.returncode,
        "drc_types": types, "attributable_drc": attributable,
        "drc_stderr": completed.stderr.strip(),
        "promotion_candidate": complete and not any(
            key in types for key in (
                "clearance", "shorting_items", "tracks_crossing", "annular_width",
                "via_diameter", "track_width",
            )
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_unchanged"] else 2


def build_candidate(path):
    """Write the complete deterministic transaction to a caller-owned board."""
    board = pcbnew.LoadBoard(str(BOARD))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, xy in MOVES_MM.items():
        footprints[ref].SetPosition(point(*xy))
    for item in list(board.GetTracks()):
        if item.GetNetname() == FAULT:
            board.Remove(item)
    board.Save(str(path))
    path.with_suffix(".kicad_dru").write_bytes(
        BOARD.with_suffix(".kicad_dru").read_bytes()
    )
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--route", str(path)],
        check=True,
    )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--route":
        route_scratch(sys.argv[2])
        raise SystemExit(0)
    if len(sys.argv) == 3 and sys.argv[1] == "--build":
        build_candidate(Path(sys.argv[2]))
        raise SystemExit(0)
    raise SystemExit(main())
