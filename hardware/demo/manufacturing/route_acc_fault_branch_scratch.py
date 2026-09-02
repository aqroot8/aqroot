#!/usr/bin/env python3
"""Build and gate a complete ACC_POWER_FAULT_N replacement in scratch only."""

import hashlib
import json
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

NET = "/ACC_POWER_FAULT_N"
MOVES_MM = {"TP9": (49.50, 39.25), "TP10": (63.50, 42.75), "R50": (49.50, 57.735)}
ORDER = ("U22.6", "R103.2", "U20.6", "TP27.1", "U3.18", "TP33.1")


def point(x, y):
    return pcbnew.VECTOR2I(round(x * 1e6), round(y * 1e6))


def route_scratch(path):
    routed = qr.QBoard(path)
    ir.inject_existing_via_obstacles(routed)
    pads = {p["ref"]: p for p in ir.physical_net_pads(routed, NET)}
    target = (round(sum(pads[r]["x"] for r in ORDER) / len(ORDER)),
              round(sum(pads[r]["y"] for r in ORDER) / len(ORDER)))
    targets = {"U3.18": (pads["TP33.1"]["x"], pads["TP33.1"]["y"]),
               "TP33.1": (pads["U3.18"]["x"], pads["U3.18"]["y"])}
    reservations = []
    for ref in ORDER:
        result = qr.reserve_escape(
            routed, NET, pads[ref], 200_000, 200_000, 200_000,
            near="B", far="I3", G=25_000, fine=25_000,
            via_dia=600_000, via_drill=300_000, target=targets.get(ref, target),
            site_separation=300_000,
        )
        reservations.append({"pad": ref, **result})
        if not result.get("ok"):
            break
    joins = []
    if len(reservations) == len(ORDER) and all(r.get("ok") for r in reservations):
        parent = list(range(len(reservations)))
        def root(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        edges = sorted(((i, j) for i in range(len(reservations)) for j in range(i + 1, len(reservations))),
                       key=lambda p: ((reservations[p[0]]["via"][0] - reservations[p[1]]["via"][0]) ** 2
                                      + (reservations[p[0]]["via"][1] - reservations[p[1]]["via"][1]) ** 2))
        for a, b in edges:
            if root(a) == root(b):
                continue
            result = None
            for layer in ("I3", "I2"):
                result = qr.join_reserved(routed, NET, reservations[a]["via"],
                                          reservations[b]["via"], 200_000, 200_000, 200_000,
                                          layer=layer, G=25_000, fine=25_000)
                if result.get("ok"):
                    result["selected_layer"] = layer
                    break
            joins.append({"a": reservations[a]["pad"], "b": reservations[b]["pad"], **result})
            if not result.get("ok"):
                break
            parent[root(b)] = root(a)
            if len(joins) == len(reservations) - 1:
                break
    routed.save(path)
    print(json.dumps({"reservations": reservations, "joins": joins}, sort_keys=True))


def main():
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(BOARD))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, xy in MOVES_MM.items():
        footprints[ref].SetPosition(point(*xy))
    removed = 0
    for item in list(board.GetTracks()):
        if item.GetNetname() == NET:
            board.Remove(item)
            removed += 1

    with tempfile.TemporaryDirectory(prefix="aqroot-demo-fault-route-") as td:
        scratch = Path(td) / BOARD.name
        scratch.with_suffix(".kicad_dru").write_bytes(BOARD.with_suffix(".kicad_dru").read_bytes())
        board.Save(str(scratch))
        child = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--route", str(scratch)],
                               check=True, text=True, capture_output=True)
        route = json.loads(child.stdout)
        reservations, joins = route["reservations"], route["joins"]

        drc = Path(td) / "drc.json"
        completed = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all", "--schematic-parity",
            "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        drc_data = json.loads(drc.read_text()) if drc.exists() else {}
        violations = drc_data.get("violations", [])
        types = {}
        for row in violations:
            key = row.get("type", "unknown")
            types[key] = types.get(key, 0) + 1

    report = {
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "scratch_moves_mm": MOVES_MM, "withdrawn_copper_objects": removed,
        "reservation_order": ORDER, "reservations": reservations, "joins": joins,
        "complete_transaction": len(reservations) == 6 and len(joins) == 5
                                and all(r.get("ok") for r in reservations + joins),
        "drc_exit": completed.returncode, "drc_types": types,
        "drc_stderr": completed.stderr.strip(), "promotion_candidate": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_unchanged"] else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--route":
        route_scratch(sys.argv[2])
        raise SystemExit(0)
    raise SystemExit(main())
