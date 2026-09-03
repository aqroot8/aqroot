#!/usr/bin/env python3
"""Atomically screen the complete fitted USB_VBUS_CHG power tree."""

import argparse
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
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/01_POWER_TREE/USB_VBUS_CHG"
PADS = (
    "C23.2", "D10.2", "D11.2", "Q5.2", "R104.1", "R35.2",
    "R84.1", "R91.1", "R94.1", "R96.1", "U11.10",
)
WIDTH = 500_000
CLEARANCE = 250_000
VIA_DIAMETER = 900_000
VIA_DRILL = 400_000
GRID = 50_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(board):
    result = Counter()
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu),
                   item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y),
                           (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        result[key] += 1
    return result


def face(pad):
    faces = [name for name in ("F", "B") if pad[name]]
    if len(faces) != 1:
        raise RuntimeError(f"ambiguous copper face for {pad['ref']}: {faces}")
    return faces[0]


def route_candidate(path):
    board = qr.QBoard(path)
    ir.inject_existing_via_obstacles(board)
    physical = ir.physical_net_pads(board, NET)
    pads = {pad["ref"]: pad for pad in physical}
    if set(pads) != set(PADS):
        raise RuntimeError(f"unexpected fitted pads: {sorted(pads)}")
    centroid = (
        round(sum(pad["x"] for pad in physical) / len(physical)),
        round(sum(pad["y"] for pad in physical) / len(physical)),
    )
    reservations = []
    anchors = []
    for ref in PADS:
        pad = pads[ref]
        near = face(pad)
        far = "I2"
        reservation = qr.reserve_escape(
            board, NET, pad, WIDTH, CLEARANCE, CLEARANCE,
            near=near, far=far, G=GRID, fine=25_000,
            via_dia=VIA_DIAMETER, via_drill=VIA_DRILL,
            target=centroid, site_separation=450_000,
        )
        reservations.append({"pad": ref, **reservation})
        if not reservation.get("ok"):
            return board, reservations, []
        anchors.append((ref, tuple(reservation["via"])))

    # Kruskal-style shortest-first joins form one tree without committing a
    # failed edge. Try both signal inner layers for each bounded connection.
    parent = list(range(len(anchors)))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    edges = sorted(
        ((a, b) for a in range(len(anchors)) for b in range(a + 1, len(anchors))),
        key=lambda pair: sum((anchors[pair[0]][1][axis] - anchors[pair[1]][1][axis]) ** 2
                             for axis in (0, 1)),
    )
    joins = []
    for a, b in edges:
        if root(a) == root(b):
            continue
        result = None
        for layer in ("I2", "I3"):
            mark = board.mark()
            result = qr.join_reserved(
                board, NET, anchors[a][1], anchors[b][1], WIDTH,
                CLEARANCE, CLEARANCE, layer=layer, G=GRID, fine=25_000,
            )
            if result.get("ok"):
                result["selected_layer"] = layer
                break
            board.revert(mark)
        joins.append({"a": anchors[a][0], "b": anchors[b][0], **result})
        if result.get("ok"):
            parent[root(b)] = root(a)
            if len({root(i) for i in range(len(anchors))}) == 1:
                break
    return board, reservations, joins


def independent_endpoint_screen(path):
    seed = qr.QBoard(path)
    physical = ir.physical_net_pads(seed, NET)
    centroid = (
        round(sum(pad["x"] for pad in physical) / len(physical)),
        round(sum(pad["y"] for pad in physical) / len(physical)),
    )
    rows = []
    for ref in PADS:
        board = qr.QBoard(path)
        ir.inject_existing_via_obstacles(board)
        pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, NET)}
        pad = pads[ref]
        result = qr.reserve_escape(
            board, NET, pad, WIDTH, CLEARANCE, CLEARANCE,
            near=face(pad), far="I2", G=GRID, fine=25_000,
            via_dia=VIA_DIAMETER, via_drill=VIA_DRILL,
            target=centroid, site_separation=450_000,
        )
        rows.append({"pad": ref, **result})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    before_sha = sha256(BOARD)
    baseline = copper(pcbnew.LoadBoard(str(BOARD)))
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-vbus-chg-") as td:
        work = Path(td)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        endpoint_screen = independent_endpoint_screen(scratch)
        board, reservations, joins = route_candidate(scratch)
        board.save(scratch)
        drc_path = work / "drc.json"
        checked = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc_path), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc_path.read_text()).get("violations", [])
        types = Counter(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED]
        ledger_path = work / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        target = next(row for row in ledger["nets"] if row["net"] == NET)
        after = copper(pcbnew.LoadBoard(str(scratch)))
        removed = baseline - after
        added = after - baseline
        wrong = [list(item) for item in added if item[0] != NET]
        successful = [join for join in joins if join.get("ok")]
        promotion = (
            len(reservations) == len(PADS) and all(r.get("ok") for r in reservations)
            and len(successful) == len(PADS) - 1 and target["open_edges"] == 0
            and not attributable and not removed and not wrong
        )
        candidate = scratch.read_bytes()
        if args.candidate and promotion:
            args.candidate.write_bytes(candidate)
        if args.promote:
            if not promotion or sha256(BOARD) != before_sha:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(candidate)
    print(json.dumps({
        "schema": 1, "net": NET,
        "authoritative_board_sha256": before_sha,
        "authoritative_unchanged": sha256(BOARD) == before_sha,
        "contract": {"width_mm": 0.5, "clearance_mm": 0.25,
                     "via_mm": [0.9, 0.4], "atomic_whole_tree": True},
        "independent_endpoint_screen": endpoint_screen,
        "reservations": reservations, "joins": joins,
        "successful_joins": len(successful),
        "target_open_edges": target["open_edges"],
        "drc_exit": checked.returncode, "drc_types": dict(types),
        "attributable_drc": attributable,
        "removed_copper_items": sum(removed.values()),
        "wrong_net_additions": wrong,
        "promotion_candidate": promotion,
    }, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
