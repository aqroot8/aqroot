#!/usr/bin/env python3
"""Build and gate the coherent downstream ACC_5V_SW route in scratch."""

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

NET = "/ACC_5V_SW"
SMD_ORDER = ("C67.1", "TP29.1", "TP42.1", "C38.1")
PTH_ORDER = ("J5.1", "J5.24")
def exclusive_face(pad):
    """Return the copper face of an SMD pad, rejecting ambiguous geometry."""
    faces = [face for face in ("F", "B") if pad[face]]
    if len(faces) != 1:
        raise ValueError(f"{pad['ref']} is not an exclusive-face SMD pad: {faces}")
    return faces[0]


def route_scratch(path: Path):
    routed = qr.QBoard(path)
    ir.inject_existing_via_obstacles(routed)
    pads = {p["ref"]: p for p in ir.physical_net_pads(routed, NET)}
    centroid = (round(sum(pads[r]["x"] for r in SMD_ORDER + PTH_ORDER) / 6),
                round(sum(pads[r]["y"] for r in SMD_ORDER + PTH_ORDER) / 6))
    reservations = []
    # The U22 output needs its package-local 0.25 mm neck, but the eventual
    # barrel is still the ordinary 0.90/0.40 mm ACC_5V power via.  Reserving
    # that landing explicitly avoids forcing the B.Cu launch across the
    # retained ACC_DETECT_N branch.
    u22_pad = pads["U22.5"]
    u22_via = (55_250_000, 43_000_000)
    neck_end = (u22_pad["x"] - 512_500, u22_pad["y"])
    routed.track(NET, "B", u22_pad["x"], u22_pad["y"], *neck_end, 250_000)
    routed.track(NET, "B", *neck_end, *u22_via, 400_000)
    routed.via(NET, *u22_via, 900_000, 400_000)
    u22_escape = {
        "ok": True, "reservation": True, "near": "B", "layer": "I3",
        "via": list(u22_via), "via_xy": [[55.25, 43.0]],
        "via_dia": 0.9, "via_drill": 0.4, "minw": 0.25,
        "neck_mm": 0.5125,
    }
    reservations.append({"pad": "U22.5", **u22_escape})
    if not u22_escape.get("ok"):
        routed.save(path)
        print(json.dumps({"reservations": reservations, "joins": []}, sort_keys=True))
        return
    for ref in SMD_ORDER:
        near = exclusive_face(pads[ref])
        result = qr.reserve_escape(
            routed, NET, pads[ref], 400_000, 250_000, 250_000,
            near=near, far="I3", G=25_000, fine=25_000,
            via_dia=900_000, via_drill=400_000, target=centroid,
            site_separation=450_000,
        )
        reservations.append({"pad": ref, **result})
        if not result.get("ok"):
            routed.save(path)
            print(json.dumps({"reservations": reservations, "joins": []}, sort_keys=True))
            return

    # U22.5 is a fine-pitch load-switch output.  As with the accepted U21.6
    # launch, use a short package neck and let the adjacent output capacitor's
    # larger land own the already-reserved ordinary power via.
    anchors = [(r["pad"], tuple(r["via"])) for r in reservations]
    anchors.extend((ref, (pads[ref]["x"], pads[ref]["y"])) for ref in PTH_ORDER)
    parent = list(range(len(anchors)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    edges = sorted(
        ((i, j) for i in range(len(anchors)) for j in range(i + 1, len(anchors))),
        key=lambda pair: ((anchors[pair[0]][1][0] - anchors[pair[1]][1][0]) ** 2
                          + (anchors[pair[0]][1][1] - anchors[pair[1]][1][1]) ** 2),
    )
    joins = []
    for a, b in edges:
        if root(a) == root(b):
            continue
        result = None
        for layer in ("I3", "I2"):
            result = qr.join_reserved(
                routed, NET, anchors[a][1], anchors[b][1], 400_000,
                250_000, 250_000, layer=layer, G=25_000, fine=25_000,
            )
            if result.get("ok"):
                result["selected_layer"] = layer
                break
        joins.append({"a": anchors[a][0], "b": anchors[b][0], **result})
        if not result.get("ok"):
            break
        parent[root(b)] = root(a)
        if len(joins) == len(anchors) - 1:
            break
    routed.save(path)
    print(json.dumps({"reservations": reservations, "joins": joins}, sort_keys=True))


def build_candidate(path: Path):
    path.write_bytes(BOARD.read_bytes())
    path.with_suffix(".kicad_dru").write_bytes(BOARD.with_suffix(".kicad_dru").read_bytes())
    path.with_suffix(".kicad_pro").write_bytes(BOARD.with_suffix(".kicad_pro").read_bytes())
    subprocess.run([sys.executable, __file__, "--route", str(path)], check=True)


def main():
    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-acc-5v-sw-") as temporary:
        scratch = Path(temporary) / BOARD.name
        scratch.write_bytes(BOARD.read_bytes())
        scratch.with_suffix(".kicad_dru").write_bytes(BOARD.with_suffix(".kicad_dru").read_bytes())
        scratch.with_suffix(".kicad_pro").write_bytes(BOARD.with_suffix(".kicad_pro").read_bytes())
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
        complete = (len(route["reservations"]) == 5 and len(route["joins"]) == 6
                    and all(r.get("ok") for r in route["reservations"] + route["joins"]))
    report = {
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": before == hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "route": route, "complete_route": complete, "drc_exit": completed.returncode,
        "drc_types": types, "attributable_drc": attributable,
        "promotion_candidate": complete and not attributable,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["authoritative_unchanged"] else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--route":
        route_scratch(Path(sys.argv[2]))
        raise SystemExit(0)
    if len(sys.argv) == 3 and sys.argv[1] == "--build":
        build_candidate(Path(sys.argv[2]))
        raise SystemExit(0)
    raise SystemExit(main())
