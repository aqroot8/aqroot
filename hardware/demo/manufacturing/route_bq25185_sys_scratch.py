#!/usr/bin/env python3
"""Characterize a complete BQ25185_SYS fitted-pad tree in scratch.

The ranked package doglegs and through-via reservations close the 13-pad tree
over I2/I3.  Promotion still requires the real full-board gate; in particular,
the geometric landing screen must not override D-269 at U11.1.
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

NET = "/01_POWER_TREE/BQ25185_SYS"
GRID = 50_000
FITTED = (
    # Test the boxed C26 endpoint before its less-constrained C24 neighbor so
    # an intrinsic C26 wall cannot be misclassified as an ordering casualty.
    "C26.2", "C24.1", "C27.1", "C28.1", "C33.1", "C64.1", "L4.1",
    "SW9.2", "U11.1", "U12.1", "U12.10", "U12.11", "U21.3",
)
FINE_PITCH = {"U11.1", "U12.1", "U12.10", "U12.11", "U21.3"}
DOGLEG = {
    "U11.1": {
        "neck_end": (66_586_400, 78_866_200),
        "anchor": (66_729_800, 79_071_000),
        "via": (66_977_300, 79_318_500),
        "neck_width": 200_000, "trunk_width": 500_000,
        "clearance": 300_000,
    },
    "U21.3": {
        "neck_end": (56_212_500, 39_400_000),
        "anchor": (55_962_500, 39_400_000),
        "via": (56_048_000, 39_634_900),
        "neck_width": 250_000, "trunk_width": 800_000,
        "clearance": 250_000,
    },
}


def face(pad):
    faces = [name for name in ("F", "B") if pad[name]]
    if len(faces) != 1:
        raise ValueError(f"{pad['ref']} has ambiguous copper faces {faces}")
    return faces[0]


def route(path: Path, c26_candidate=None, c27_candidate=None):
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
    order = FITTED if not (c26_candidate or c27_candidate) else FITTED
    for ref in order:
        print(f"reserve {ref}", file=sys.stderr, flush=True)
        pad = pads[ref]
        near = face(pad)
        qualified = (c26_candidate if ref == "C26.2" else
                     c27_candidate if ref == "C27.1" else None)
        if qualified:
            def point(key):
                return tuple(round(value * 1e6) for value in qualified[key])
            neck_end = point("neck_end_mm")
            anchor = point("anchor_mm")
            via = point("via_mm")
            board.track(NET, "B", pad["x"], pad["y"], *neck_end, 500_000)
            board.track(NET, "B", *neck_end, *anchor, 500_000)
            board.track(NET, "B", *anchor, *via, 500_000)
            board.via(NET, *via, 900_000, 400_000)
            reservations.append({"pad": ref, "ok": True, "face": "B",
                                 "via": list(via),
                                 "launch": f"qualified_{ref.lower().replace('.', '_')}_refloor_dogleg",
                                 "candidate": qualified})
            anchors.append((ref, via))
            continue
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
                print(json.dumps({"reservations": reservations,
                                  "joins": []}, sort_keys=True))
                return
            anchors.append((ref, tuple(result["via"])))
            continue
        if ref in DOGLEG:
            landing = DOGLEG[ref]
            neck_end = landing["neck_end"]
            anchor = landing["anchor"]
            via = landing["via"]
            board.track(NET, "B", pad["x"], pad["y"], *neck_end,
                        landing["neck_width"])
            board.track(NET, "B", *neck_end, *anchor,
                        landing["trunk_width"])
            board.track(NET, "B", *anchor, *via, landing["trunk_width"])
            board.via(NET, *via, 900_000, 400_000)
            reservations.append({
                "pad": ref, "ok": True, "face": "B", "via": list(via),
                "neck_width_mm": landing["neck_width"] / 1e6,
                "trunk_width_mm": landing["trunk_width"] / 1e6,
                "clearance_mm": landing["clearance"] / 1e6,
                "launch": "ranked_directional_dogleg_landing",
            })
            anchors.append((ref, via))
        elif ref in FINE_PITCH:
            flare = board.flare(NET, pad, "B", 500_000, 250_000,
                                250_000, 250_000, 25_000)
            if flare is None:
                reservations.append({"pad": ref, "ok": False, "reason": "NO_FLARE"})
                board.save(path)
                print(json.dumps({"reservations": reservations,
                                  "joins": []}, sort_keys=True))
                return
            escape = {"x": flare["x"], "y": flare["y"], "ln": 0,
                      "w": 500_000}
            sites = board.via_sites(
                "B", "I2", NET, escape, 500_000, 900_000,
                250_000, 250_000, 25_000, span=5_000_000,
                via_drill=400_000, hole_clr=250_000, limit=96,
                separation=450_000,
            )
            sites = [(x, y) for x, y in sites if all(board.point_free(
                layer, NET, x, y, 900_000, 250_000, 250_000, 25_000
            ) for layer in board.cu)]
            landing = None
            for site in sites:
                mark = board.mark()
                joined = qr.join_reserved(
                    board, NET, (flare["x"], flare["y"]), site, 500_000,
                    250_000, 250_000, layer="B", G=25_000, fine=25_000,
                )
                if joined.get("ok"):
                    landing = (site, joined)
                    break
                board.revert(mark)
            if landing is None:
                reservations.append({"pad": ref, "ok": False,
                                     "reason": "NO_LANDING_PATH"})
                board.save(path)
                print(json.dumps({"reservations": reservations,
                                  "joins": []}, sort_keys=True))
                return
            anchor, joined = landing
            board.via(NET, *anchor, 900_000, 400_000)
            reservations.append({
                "pad": ref, "ok": True, "face": "B", "via": list(anchor),
                "neck_mm": flare["neck_len"], "sub_trunk_mm": flare["sub_trunk"],
                "landing": joined,
            })
            anchors.append((ref, anchor))
        else:
            result = qr.reserve_escape(
                board, NET, pad, 500_000, 250_000, 250_000,
                near="B", far="I2", G=GRID, fine=25_000,
                via_dia=900_000, via_drill=400_000, target=centroid,
                site_separation=450_000,
            )
            reservations.append({"pad": ref, **result})
            if not result.get("ok"):
                board.save(path)
                print(json.dumps({"reservations": reservations,
                                  "joins": []}, sort_keys=True))
                return
            anchors.append((ref, tuple(result["via"])))

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
        result = None
        for layer in ("I2", "I3"):
            result = qr.join_reserved(
                board, NET, anchors[a][1], anchors[b][1], 500_000,
                250_000, 250_000, layer=layer, G=GRID, fine=25_000,
            )
            if result.get("ok"):
                result["selected_layer"] = layer
                break
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
    parser.add_argument("--c26-candidate-json", help=argparse.SUPPRESS)
    parser.add_argument("--c27-candidate-json", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.route:
        route(args.route,
              json.loads(args.c26_candidate_json) if args.c26_candidate_json else None,
              json.loads(args.c27_candidate_json) if args.c27_candidate_json else None)
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
