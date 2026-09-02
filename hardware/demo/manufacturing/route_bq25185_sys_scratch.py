#!/usr/bin/env python3
"""Characterize a complete outer-layer BQ25185_SYS fitted-pad tree in scratch."""

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

NET = "/01_POWER_TREE/BQ25185_SYS"
GRID = 50_000
FITTED = (
    "C24.1", "C26.2", "C27.1", "C28.1", "C33.1", "C64.1", "L4.1",
    "SW9.2", "U11.1", "U12.1", "U12.10", "U12.11", "U21.3",
)
FINE_PITCH = {"U11.1", "U12.1", "U12.10", "U12.11", "U21.3"}


def face(pad):
    faces = [name for name in ("F", "B") if pad[name]]
    if len(faces) != 1:
        raise ValueError(f"{pad['ref']} has ambiguous copper faces {faces}")
    return faces[0]


def route(path: Path):
    board = qr.QBoard(path)
    ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    missing = sorted(set(FITTED) - pads.keys())
    if missing:
        raise RuntimeError(f"missing fitted pads: {missing}")
    centroid = (
        round(sum(pads[r]["x"] for r in FITTED) / len(FITTED)),
        round(sum(pads[r]["y"] for r in FITTED) / len(FITTED)),
    )
    reservations = []
    anchors = []
    for ref in FITTED:
        print(f"reserve {ref}", file=sys.stderr, flush=True)
        pad = pads[ref]
        near = face(pad)
        if near == "F":
            result = qr.reserve_escape(
                board, NET, pad, 500_000, 250_000, 250_000,
                near="F", far="B", G=GRID, fine=GRID,
                via_dia=900_000, via_drill=400_000, target=centroid,
                site_separation=450_000,
            )
            reservations.append({"pad": ref, **result})
            if not result.get("ok"):
                board.save(path)
                print(json.dumps({"reservations": reservations, "joins": []}, sort_keys=True))
                return
            anchors.append((ref, tuple(result["via"])))
            continue
        if ref == "U11.1":
            # BQ25185 WSON has 0.20 mm-high lands on 0.40 mm pitch.  The
            # generic radial flare cannot represent its one legal direction:
            # leave top-edge pad 1 away from adjacent BAT pad 2, then widen
            # outside the body.  A west launch runs parallel to BAT and fails
            # D-269 even though it clears the package land pattern.
            neck_end = (pad["x"], 79_200_000)
            anchor = (pad["x"], 79_500_000)
            board.track(NET, "B", pad["x"], pad["y"], *neck_end, 200_000)
            board.track(NET, "B", *neck_end, *anchor, 500_000)
            reservations.append({
                "pad": ref, "ok": True, "face": "B", "anchor": list(anchor),
                "neck_mm": 0.6, "neck_width_mm": 0.2,
                "launch": "outward_wson_land_width",
            })
            anchors.append((ref, anchor))
        elif ref == "U21.3":
            # The SYS input is the end pad on the TPS61023 west column.  Launch
            # away from P2, then immediately widen to the 0.80 mm peak-current
            # feed required by D-185.  L4.1 is connected by the tree later.
            neck_end = (pad["x"], 38_890_000)
            anchor = (pad["x"], 38_500_000)
            board.track(NET, "B", pad["x"], pad["y"], *neck_end, 250_000)
            board.track(NET, "B", *neck_end, *anchor, 800_000)
            reservations.append({
                "pad": ref, "ok": True, "face": "B", "anchor": list(anchor),
                "neck_mm": 0.51, "neck_width_mm": 0.25,
                "sub_trunk_width_mm": 0.8, "launch": "outward_peak_feed",
            })
            anchors.append((ref, anchor))
        elif ref in FINE_PITCH:
            flare = board.flare(NET, pad, "B", 500_000, 250_000,
                                250_000, 250_000, 25_000)
            if flare is None:
                reservations.append({"pad": ref, "ok": False, "reason": "NO_FLARE"})
                board.save(path)
                print(json.dumps({"reservations": reservations, "joins": []}, sort_keys=True))
                return
            anchor = (flare["x"], flare["y"])
            reservations.append({
                "pad": ref, "ok": True, "face": "B", "anchor": list(anchor),
                "neck_mm": flare["neck_len"], "sub_trunk_mm": flare["sub_trunk"],
            })
            anchors.append((ref, anchor))
        else:
            reservations.append({"pad": ref, "ok": True, "face": "B",
                                 "anchor": [pad["x"], pad["y"]]})
            anchors.append((ref, (pad["x"], pad["y"])))

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
        print(f"join {anchors[a][0]} {anchors[b][0]}", file=sys.stderr, flush=True)
        result = qr.join_reserved(
            board, NET, anchors[a][1], anchors[b][1], 500_000,
            250_000, 250_000, layer="B", G=GRID, fine=GRID,
        )
        joins.append({"a": anchors[a][0], "b": anchors[b][0], **result})
        if not result.get("ok"):
            continue
        parent[root(b)] = root(a)
        if len({root(i) for i in range(len(anchors))}) == 1:
            break
    board.save(path)
    print(json.dumps({"reservations": reservations, "joins": joins}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--route", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.route:
        route(args.route)
        return 0
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-bq25185-sys-") as temp:
        scratch = Path(temp) / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        routed = json.loads(subprocess.run(
            [sys.executable, __file__, "--route", str(scratch)], check=True,
            text=True, capture_output=True,
        ).stdout)
        drc = Path(temp) / "drc.json"
        completed = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", []) if drc.exists() else []
        accepted = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
        attributable = [v for v in violations if v.get("type") not in accepted]
        types = {}
        for violation in violations:
            kind = violation.get("type", "unknown")
            types[kind] = types.get(kind, 0) + 1
        successful = [j for j in routed["joins"] if j.get("ok")]
        complete = (len(routed["reservations"]) == len(FITTED)
                    and all(r.get("ok") for r in routed["reservations"])
                    and len(successful) == len(FITTED) - 1)
        candidate = scratch.read_bytes()
    report = {
        "schema": 1, "net": NET, "fitted_pads": list(FITTED),
        "search_grid_mm": GRID / 1_000_000,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "route": routed, "complete_route": complete,
        "drc_exit": completed.returncode, "drc_types": types,
        "attributable_drc": attributable,
        "promotion_candidate": complete and not attributable,
    }
    if args.candidate and report["promotion_candidate"]:
        args.candidate.write_bytes(candidate)
        report["candidate"] = str(args.candidate)
        report["candidate_sha256"] = hashlib.sha256(candidate).hexdigest()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
