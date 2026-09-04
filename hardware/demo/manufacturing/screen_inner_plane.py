#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- screen an inner-layer POUR for a plane-less power net.

`+3V3` reaches 80 fitted pads over a 157 mm span and owns no copper at all, so
it is 79 of the board's remaining retained open edges.  Completing it as a
pad-to-pad MST would spend ~80 long 0.60 mm runs on the two inner signal
layers; completing it as a POUR spends one zone plus one short via per pad --
the primitive that has already planted 204 GND islands.

This module answers, on evidence and without touching the authority, the only
question that decides between them: does a pour on In2.Cu / In3.Cu actually
FILL, and does it come within reach of every pad?

It is read-only with respect to `hardware/demo/kicad/aqroot-demo/`.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"

# The GND reference zones' own outline and fill parameters, reused verbatim so
# a power pour cannot be judged against a softer geometry than the planes it
# sits between.  `island_removal_mode 1` (keep) is required for the FIRST fill
# only: a pour whose net owns no copper yet has no connection to survive mode 0.
OUTLINE = ((0.5, 0.5), (71.5, 0.5), (71.5, 147.5), (0.5, 147.5))


# A BOUNDED POUR IS A DIFFERENT INSTRUMENT FROM A PLANE.
# ---------------------------------------------------------------------------
# `OUTLINE` is the whole board, and that is the only shape a power PLANE should
# ever have: `+3V3` owns `F`/`In3`, `GND` owns `B`/`In1`/`In4`, and each of those
# five pours is the layer.  A fourth board-wide pour has nowhere to go.
#
# But a plane is not the only pour a power net can want.  `BQ25185_SYS` -- the
# charger output rail -- has THIRTEEN retained lands in three widely separated
# clusters and no pour at all, and eight of those lands sit on `B.Cu` inside a
# 10 x 34 mm column of the east power block.  A pour bounded to THAT column is
# ordinary power-supply practice: local copper for a rail that carries amps,
# not a plane competing for a layer.  It bonds every same-net land it overlaps
# through `connect_pads yes`, with no track, no barrel and no pad escape -- which
# is the whole point on a net whose every open edge is `NO_LEGAL_ESCAPE_SRC`.
#
# KiCad needs no zone priority for this.  Two pours of DIFFERENT nets at the
# same priority do not nest; each retreats from the other by its clearance.  So
# a bounded `BQ25185_SYS` pour on `B.Cu` takes its column out of the `GND` pour
# and gives it back at the boundary, and `GND`'s return path is unharmed because
# `GND` also owns the whole of `In1` and `In4`.
def bbox_outline(x0, y0, x1, y1):
    """The rectangle (x0,y0)-(x1,y1) as a zone outline, corners clockwise."""
    x0, x1 = sorted((float(x0), float(x1)))
    y0, y1 = sorted((float(y0), float(y1)))
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def parse_outline(spec):
    """`x0,y0,x1,y1` (a rectangle) or `x,y x,y x,y ...` (a polygon)."""
    if spec is None:
        return OUTLINE
    nums = [float(v) for v in spec.replace(",", " ").split()]
    if len(nums) == 4:
        return bbox_outline(*nums)
    if len(nums) % 2 or len(nums) < 6:
        raise ValueError("outline needs 4 numbers (bbox) or >=3 x,y pairs")
    return tuple((nums[i], nums[i + 1]) for i in range(0, len(nums), 2))

ZONE = """	(zone
		(net "%(net)s")
		(layer "%(layer)s")
		(uuid "%(uuid)s")
		(name "%(name)s")
		(hatch edge 0.5)
		(connect_pads yes
			(clearance %(clearance).2f)
		)
		(min_thickness %(min_thickness).2f)
		(fill yes
			(thermal_gap 0.3)
			(thermal_bridge_width 0.4)
			(island_removal_mode %(islands)d)
		)
		(polygon
			(pts
				%(pts)s
			)
		)
	)
"""


def zone_sexpr(net, layer, name, clearance=0.25, min_thickness=0.2, islands=1,
               outline=OUTLINE, zuuid=None):
    """The s-expression for ONE unfilled zone, in the board's own dialect."""
    return ZONE % dict(
        net=net, layer=layer, name=name, clearance=clearance,
        min_thickness=min_thickness, islands=islands,
        uuid=zuuid or str(uuid.uuid5(uuid.NAMESPACE_URL,
                                     "aqroot-demo/%s/%s" % (net, layer))),
        pts=" ".join("(xy %g %g)" % p for p in outline))


def insert_zone(path, sexpr):
    """Append a zone to a .kicad_pcb, before its final closing paren."""
    text = Path(path).read_text(encoding="utf-8")
    cut = text.rstrip()
    assert cut.endswith(")"), "board does not end in a closing paren"
    Path(path).write_text(cut[:-1] + sexpr + ")\n", encoding="utf-8")


def refill(path, out):
    """Fill zones with the real KiCad engine and report its DRC."""
    done = subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "-o", str(out), str(path)], text=True, capture_output=True)
    report = json.loads(Path(out).read_text())
    counts = {}
    for v in report.get("violations", []):
        counts[v.get("type", "unknown")] = counts.get(v.get("type"), 0) + 1
    return done.returncode, counts, report


def measure(path, net, layer):
    """Filled area, island count and per-pad reach of `net`'s pour on `layer`."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    polys, area = [], 0.0
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net:
            continue
        if not z.IsOnLayer(board.GetLayerID(layer)):
            continue
        shape = z.GetFilledPolysList(board.GetLayerID(layer))
        area += z.GetFilledArea() / 1e12
        for i in range(shape.OutlineCount()):
            poly = pcbnew.SHAPE_POLY_SET()
            poly.AddOutline(shape.Outline(i))
            for h in range(shape.HoleCount(i)):
                poly.AddHole(shape.Hole(i, h), 0)
            polys.append((poly, abs(shape.Outline(i).Area()) / 1e12))
    polys.sort(key=lambda p: -p[1])

    pads = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net or not p.GetNumber():
                continue
            pos = p.GetPosition()
            best, which = None, None
            for idx, (poly, _a) in enumerate(polys):
                d = poly.Distance(pos) / 1e6
                if best is None or d < best:
                    best, which = d, idx
            pads.append(dict(pad=f.GetReference() + "." + p.GetNumber(),
                             x=round(pos.x / 1e6, 3), y=round(pos.y / 1e6, 3),
                             side="F" if p.IsOnLayer(pcbnew.F_Cu) else "B",
                             mm_to_pour=round(best, 3) if best is not None else None,
                             island=which))
    return dict(
        filled_area_mm2=round(area, 1),
        islands=len(polys),
        island_area_mm2=[round(a, 1) for _p, a in polys[:12]],
        pads=sorted(pads, key=lambda r: -(r["mm_to_pour"] or 0)),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="+3V3")
    ap.add_argument("--layers", default="In3.Cu,In2.Cu")
    ap.add_argument("--work", required=True)
    ap.add_argument("--clearance", type=float, default=0.25)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    before = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    cases = []
    for layer in a.layers.split(","):
        cell = work / layer.replace(".", "_")
        cell.mkdir(exist_ok=True)
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            shutil.copyfile(BOARD.with_suffix(suffix),
                            (cell / BOARD.name).with_suffix(suffix))
        scratch = cell / BOARD.name
        insert_zone(scratch, zone_sexpr(
            a.net, layer, "%s %s PLANE" % (layer.split(".")[0], a.net),
            clearance=a.clearance, islands=1))
        code, counts, _r = refill(scratch, cell / "drc.json")
        m = measure(scratch, a.net, layer)
        reach = [p["mm_to_pour"] for p in m["pads"]]
        cases.append(dict(layer=layer, drc_exit=code, drc_types=counts,
                          pads_out_of_reach=sum(1 for d in reach if d > 1.0),
                          worst_mm=max(reach) if reach else None,
                          **m))
        print("  %-7s area %8.1f mm2  islands %3d  worst pad reach %.2f mm"
              % (layer, m["filled_area_mm2"], m["islands"],
                 max(reach) if reach else -1), file=sys.stderr, flush=True)

    out = dict(schema=1, net=a.net, authoritative_board_sha256=before,
               authoritative_unchanged=(
                   before == hashlib.sha256(BOARD.read_bytes()).hexdigest()),
               zone_clearance_mm=a.clearance, outline=OUTLINE, cases=cases)
    text = json.dumps(out, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
