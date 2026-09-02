#!/usr/bin/env python3
"""Build and gate the coherent ACC_3V3_SW fitted-pad tree in scratch."""

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

NET = "/ACC_3V3_SW"
SMD_ORDER = (
    "U20.5", "C63.1", "R50.1", "R63.1", "R46.1", "C37.1", "R49.1",
    "C39.1", "U16.8", "Q10.1", "TP12.1",
)
# TP25 is B.Cu-only but has no legal 0.90/0.40 mm via pocket.  Treat it as a
# face anchor and require its spanning-tree edge to close on B.Cu.
PTH_ORDER = ("J5.3", "J5.22", "TP25.1", "J8.2")


def exclusive_face(pad):
    faces = [face for face in ("F", "B") if pad[face]]
    if len(faces) != 1:
        raise ValueError(f"{pad['ref']} is not an exclusive-face SMD pad: {faces}")
    return faces[0]


def route_scratch(path: Path):
    routed = qr.QBoard(path)
    ir.inject_existing_via_obstacles(routed)
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(routed, NET)}
    centroid = (
        round(sum(pads[ref]["x"] for ref in SMD_ORDER + PTH_ORDER) / 15),
        round(sum(pads[ref]["y"] for ref in SMD_ORDER + PTH_ORDER) / 15),
    )
    def reserve_flared(ref):
        pad = pads[ref]
        flare = routed.flare(
            NET, pad, "B", 400_000, 250_000, 250_000, 250_000, 25_000
        )
        if flare is None:
            return {"pad": ref, "ok": False, "reason": "NO_FLARE"}
        escape = {"x": flare["x"], "y": flare["y"], "ln": 0, "w": 400_000}
        sites = routed.via_sites(
            "B", "I2", NET, escape, 400_000, 900_000,
            250_000, 250_000, 25_000, span=5_000_000,
            via_drill=400_000, hole_clr=250_000, limit=96,
            separation=450_000,
        )
        sites = [(x, y) for x, y in sites if all(routed.point_free(
            layer, NET, x, y, 900_000, 250_000, 250_000, 25_000
        ) for layer in routed.cu)]
        for via in sites:
            mark = routed.mark()
            joined = qr.join_reserved(
                routed, NET, (flare["x"], flare["y"]), via,
                400_000, 250_000, 250_000, layer="B", G=25_000, fine=25_000,
            )
            if not joined.get("ok"):
                routed.revert(mark)
                continue
            routed.via(NET, *via, 900_000, 400_000)
            return {
                "pad": ref, "ok": True, "reservation": True, "near": "B",
                "layer": "I2", "via": list(via),
                "via_xy": [[round(via[0] / 1e6, 3), round(via[1] / 1e6, 3)]],
                "via_dia": 0.9, "via_drill": 0.4, "minw": 0.25,
                "neck_mm": flare["neck_len"],
                "sub_trunk_mm": flare["sub_trunk"],
                "landing_rank_count": len(sites), "landing": joined,
            }
        return {"pad": ref, "ok": False, "reason": "NO_LANDING_PATH",
                "site_count": len(sites)}

    reservations = [reserve_flared("U20.5")]
    for ref in SMD_ORDER[1:]:
        if ref == "U16.8":
            reservations.append(reserve_flared(ref))
            continue
        face = exclusive_face(pads[ref])
        result = qr.reserve_escape(
            routed, NET, pads[ref], 400_000, 250_000, 250_000,
            near=face, far="I2", G=25_000, fine=25_000,
            via_dia=900_000, via_drill=400_000, target=centroid,
            site_separation=450_000,
        )
        reservations.append({"pad": ref, **result})
        if not result.get("ok"):
            routed.save(path)
            print(json.dumps({"reservations": reservations, "joins": []}, sort_keys=True))
            return

    anchors = [(row["pad"], tuple(row["via"])) for row in reservations]
    anchors.extend((ref, (pads[ref]["x"], pads[ref]["y"])) for ref in PTH_ORDER)
    parent = list(range(len(anchors)))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    # Exhaust the finite 15-anchor graph.  The first screen's arbitrary
    # twelve-failure cutoff stopped before longer cross-component joins and
    # incorrectly made the C63/R63 corridor look terminal.
    edges = sorted(
        ((a, b) for a in range(len(anchors)) for b in range(a + 1, len(anchors))),
        key=lambda pair: sum(
            (anchors[pair[0]][1][axis] - anchors[pair[1]][1][axis]) ** 2
            for axis in (0, 1)
        ),
    )
    joins = []
    for a, b in edges:
        if root(a) == root(b):
            continue
        result = None
        pair_refs = (anchors[a][0], anchors[b][0])
        if "TP25.1" in pair_refs:
            layers = ("B",)
        elif "J8.2" in pair_refs:
            layers = ("F",)
        else:
            layers = ("I2", "I3")
        for layer in layers:
            # B.Cu crosses the retained BAT_PROTECTED_P current-path region.
            # Enforce D-269's 0.300 mm floor there rather than relying on the
            # ordinary ACC_3V3 0.250 mm routed-clearance contract.
            clearance = 300_000 if layer == "B" else 250_000
            result = qr.join_reserved(
                routed, NET, anchors[a][1], anchors[b][1], 400_000,
                clearance, clearance, layer=layer, G=25_000, fine=25_000,
            )
            if result.get("ok"):
                result["selected_layer"] = layer
                break
        joins.append({"a": anchors[a][0], "b": anchors[b][0], **result})
        if not result.get("ok"):
            # A blocked shortest edge is not a terminal routing wall: retain
            # the current forest and screen the remaining ranked edges for an
            # alternate legal spanning-tree connection.
            continue
        parent[root(b)] = root(a)
        if len({root(index) for index in range(len(anchors))}) == 1:
            break
    routed.save(path)
    print(json.dumps({"reservations": reservations, "joins": joins}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path,
                        help="write the routed scratch board here after the gate")
    args = parser.parse_args()
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-acc-3v3-sw-") as temporary:
        scratch = Path(temporary) / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            source = BOARD.with_suffix(suffix)
            scratch.with_suffix(suffix).write_bytes(source.read_bytes())
        route = json.loads(subprocess.run(
            [sys.executable, __file__, "--route", str(scratch)],
            check=True, text=True, capture_output=True,
        ).stdout)
        drc = Path(temporary) / "drc.json"
        completed = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", []) if drc.exists() else []
        types = {}
        for row in violations:
            types[row.get("type", "unknown")] = types.get(row.get("type", "unknown"), 0) + 1
        attributable = [row for row in violations if row.get("type") not in {
            "lib_footprint_issues", "hole_clearance", "solder_mask_bridge"
        }]
        candidate_bytes = scratch.read_bytes()
    successful_joins = [row for row in route["joins"] if row.get("ok")]
    complete = (len(route["reservations"]) == len(SMD_ORDER)
                and len(successful_joins) == len(SMD_ORDER) + len(PTH_ORDER) - 1
                and all(row.get("ok") for row in route["reservations"]))
    report = {
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "route": route, "complete_route": complete, "drc_exit": completed.returncode,
        "drc_types": types, "attributable_drc": attributable,
        "promotion_candidate": complete and not attributable,
    }
    if args.candidate and report["promotion_candidate"]:
        args.candidate.write_bytes(candidate_bytes)
        report["candidate"] = str(args.candidate)
        report["candidate_sha256"] = hashlib.sha256(candidate_bytes).hexdigest()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_unchanged"] else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--route":
        route_scratch(Path(sys.argv[2]))
        raise SystemExit(0)
    raise SystemExit(main())
