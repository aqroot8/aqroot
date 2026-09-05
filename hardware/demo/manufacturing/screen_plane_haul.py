#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: lay ONE proposed haul on a RESERVED INNER PLANE
and publish its EXACT geometry, so the return path can be PRICED before any
licence is written.

WHY THIS EXISTS.  D-635 measured that the board's largest connected routing
surface is a `GND` PLANE -- `In1.Cu` and `In4.Cu`, 8635.9 mm2 free EACH in ONE
piece against `In2.Cu`'s 6524.6 mm2 in 223 pieces -- and that offering one to
`maze3d.offcentre_route` turns `/I2C_SCL_INT` `U1.38 <-> TP5.1` from `NO_PATH`
into a closure at the FULL 0.200 mm netclass trunk with no width licence of any
kind.  It then stopped, correctly, at the one thing it could not answer:

    A SIGNAL TRACK ON A PLANE IS A SLOT, AND A SLOT COSTS EVERY TRACE THAT
    REFERENCES THAT PLANE ITS RETURN PATH.

`screen_plane_slot.py` priced the GEOMETRIC half -- does the plane stay one
piece -- from the WORST-CASE STRAIGHT CUT between the two barrel sites, which
is deliberately not the path the router found.  Pricing the ELECTRICAL half
needs the real path: which segments, on which layer, at which width, and where
the two barrels actually land.  `screen_offcentre_hop.py --route` knows all of
that and publishes none of it: it reports `mm_by_layer` and `via_xy` and
reverts.

This screen is that report.  It asks ONE pad pair, at ONE trunk width, with ONE
`--far` set, and dumps EVERY object `maze3d.offcentre_route` laid -- layer,
endpoints, width, barrel diameter and drill -- before reverting it.  Nothing
else changes, and the board's `sha256` is re-read afterwards and published.

THE `--far` SET IS THE QUESTION, NOT A SETTING.  D-635 found the choice of
plane FREE to the ROUTER: `In1.Cu` and `In4.Cu` close the same three pairs at
the same widths.  They are NOT free to the BOARD -- `In1` references the `F.Cu`
side and `In4` the `B.Cu` side (`.kicad_dru` section 2b), so the two hauls are
the same copper cutting two completely different sets of return paths.  Run
this screen once per candidate plane and hand each artifact to
`checks/plane_return_path.py`; the cheaper plane is an OUTPUT of that
comparison and not an assumption of this one.

    python3 screen_plane_haul.py NET --a REF.PAD --b REF.PAD
        --far F,B,I2,I4 [--width NM] [--grid NM] [--board B] [-o OUT]
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("net")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--a", required=True, help="REF.PAD, e.g. U1.38")
    ap.add_argument("--b", required=True, help="REF.PAD, e.g. TP5.1")
    ap.add_argument("--far", default="",
                    help="comma-separated short layer names offered to the "
                         "haul; default = the net's own permitted set")
    ap.add_argument("--width", type=int, default=0,
                    help="trunk width in nm; default = the netclass width")
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--return-keepout", default="",
                    help="short name of a PLANE layer (e.g. I4).  Project the\n"
                         "copper of the layers that plane REFERENCES onto the\n"
                         "plane itself as obstacles, so the haul is searched\n"
                         "for a path that crosses NO reference-critical return\n"
                         "path at all.  Read the doctrine below")
    ap.add_argument("--keepout-nets", default="",
                    help="comma-separated net names to project; default = every\n"
                         "foreign net on the referencing layers")
    ap.add_argument("--plane-block", action="append", default=[],
                    help="LAYER:X0,Y0,X1,Y1 in mm.  Block a rectangle of one\n"
                         "layer outright.  A slot's return detour is twice the\n"
                         "distance from the crossing to the nearest END of the\n"
                         "slot, so where a crossing is FORCED the cheap answer\n"
                         "is to make the slot START just before it: block the\n"
                         "plane on the far side of the crossing and the haul\n"
                         "must stay on an outer layer until it is past")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, DRU_CLASS, BOARD_TRACK_MIN,
                                  reserved_inner_planes, permitted_layers)

    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)

    c = net_contract(qb.b, a.net)
    width = a.width or c["width"]
    floor = max(BOARD_TRACK_MIN,
                DRU_CLASS.get(c["netclass"], {}).get("width", 0))
    far = ([x for x in a.far.split(",") if x] if a.far
           else list(permitted_layers(qb.routable, c["layers"], reserved,
                                      a.net)))

    # ------------------------------------------------------- RETURN KEEP-OUT
    # A SLOT'S PRICE IS PAID BY THE LAYERS THE PLANE REFERENCES, SO MAKE THE
    # ROUTER SEE THEM.
    #
    # `checks/plane_return_path.py` prices a haul AFTER it is found: it reads
    # the copper layers adjacent to the plane in the board's own stack-up,
    # finds every foreign track whose centreline the haul cuts, and measures
    # the arc the return current must take around the void.  That answers "what
    # does THIS path cost".  It cannot answer "is there a path that costs
    # NOTHING", because the router never knew the question was being asked.
    #
    # This lever asks it.  Every foreign track on a referencing layer is
    # injected into THIS QBoard instance as an obstacle ON THE PLANE, stroked
    # at its own half-width plus the haul's clearance -- exactly the idiom
    # `incremental_router.inject_existing_via_obstacles` uses for barrels, and
    # add-only in the same way: it can only make the search MORE conservative,
    # it edits no file, and it touches nothing but this transient object.  A
    # closure under the keep-out is a haul that crosses no return path at all
    # and whose licence is therefore FREE; a refusal is proof that the crossing
    # is FORCED by the board and not by the router's taste, which is a finding
    # in its own right and the thing a detour budget then has to price.
    keepout = None
    if a.return_keepout:
        want = qr.LNAME[a.return_keepout]
        names = [qb.b.GetLayerName(l)
                 for l in qb.b.GetEnabledLayers().CuStack()]
        pname = qb.b.GetLayerName(want)
        k = names.index(pname)
        refs = {names[i] for i in (k - 1, k + 1) if 0 <= i < len(names)}
        only = {x for x in a.keepout_nets.split(",") if x}
        n = 0
        for t in qb.b.GetTracks():
            if t.GetClass() == "PCB_VIA":
                continue
            if qb.b.GetLayerName(t.GetLayer()) not in refs:
                continue
            if t.GetNetname() == a.net:
                continue
            if only and t.GetNetname() not in only:
                continue
            s0, e0 = t.GetStart(), t.GetEnd()
            qb.shapes[a.return_keepout].append(
                qr.SEG(s0.x, s0.y, e0.x, e0.y,
                       t.GetWidth() / 2.0 + c["clr"],
                       "RETURN_PATH::" + t.GetNetname(), "return-keepout"))
            n += 1
        keepout = dict(plane=pname, references=sorted(refs), projected=n,
                       nets=sorted(only) or None,
                       clearance_nm=c["clr"])
        print("  return keep-out: %d segments of %s projected onto %s"
              % (n, ",".join(sorted(refs)), pname), file=sys.stderr)

    blocks = []
    for spec in a.plane_block:
        lay, box = spec.split(":", 1)
        x0, y0, x1, y1 = (float(v) for v in box.split(","))
        cx, cy = (x0 + x1) / 2e0, (y0 + y1) / 2e0
        qb.shapes[lay].append(qr.RR(cx * 1e6, cy * 1e6,
                                    abs(x1 - x0) / 2.0 * 1e6,
                                    abs(y1 - y0) / 2.0 * 1e6, 0, 0,
                                    "PLANE_BLOCK", "plane-block"))
        blocks.append(dict(layer=lay, box=[x0, y0, x1, y1]))
    if blocks:
        print("  plane blocks: %s" % blocks, file=sys.stderr)

    islands = mz.net_islands(qb, a.net)
    pads = {p["ref"]: p for isl in islands for p in isl}
    for want in (a.a, a.b):
        if want not in pads:
            raise SystemExit("%s owns no land %s" % (a.net, want))
    p, q = pads[a.a], pads[a.b]
    gap = math.hypot(p["x"] - q["x"], p["y"] - q["y"]) / 1e6

    fld = mz.Field(qb, a.net, width, c["clr_pad"], c["clr"], c["via_dia"],
                   c["via_drill"], G=a.grid, layers=far)
    m = qb.mark()
    t0 = time.time()
    r = mz.offcentre_route(qb, fld, p, q, stub_widths=[width], G=a.grid,
                           limit=a.limit)
    dt = time.time() - t0

    # EVERY OBJECT, BEFORE THE REVERT.  `qb.laid[n:]` is exactly what this
    # trial added and nothing else -- the same slice `qb.revert` is about to
    # remove -- so the dump cannot drift from the copper that was proved.
    tracks, vias = [], []
    if r.get("ok"):
        for t in qb.laid[m[0]:]:
            if t.GetClass() == "PCB_VIA":
                pos = t.GetPosition()
                vias.append(dict(x_mm=round(pos.x / 1e6, 6),
                                 y_mm=round(pos.y / 1e6, 6),
                                 x_nm=pos.x, y_nm=pos.y,
                                 dia_nm=t.GetWidth(), drill_nm=t.GetDrill()))
            else:
                s, e = t.GetStart(), t.GetEnd()
                tracks.append(dict(layer=t.GetLayerName(),
                                   x0_mm=round(s.x / 1e6, 6),
                                   y0_mm=round(s.y / 1e6, 6),
                                   x1_mm=round(e.x / 1e6, 6),
                                   y1_mm=round(e.y / 1e6, 6),
                                   x0_nm=s.x, y0_nm=s.y, x1_nm=e.x, y1_nm=e.y,
                                   width_nm=t.GetWidth(),
                                   mm=round(math.hypot(e.x - s.x,
                                                       e.y - s.y) / 1e6, 4)))
    qb.revert(m)
    after = hashlib.sha256(a.board.read_bytes()).hexdigest()

    doc = dict(
        schema=1, board=str(a.board), board_sha256=sha,
        authoritative_unchanged=(sha == after),
        question=("what EXACT copper does maze3d.offcentre_route lay for this "
                  "pad pair when a reserved inner plane is offered as a haul "
                  "layer"),
        method=("read-only; one pad pair, one trunk width, one --far set; "
                "every object the trial laid is dumped from qb.laid before "
                "qb.revert removes it, and the board's sha256 is re-read "
                "afterwards.  A closure here is a LICENCE QUESTION and never "
                "copper: the plane is reserved to GND by .kicad_dru sections "
                "2a/2b and no rule area names a corridor in it"),
        net=a.net, netclass=c["netclass"], a=a.a, b=a.b,
        gap_mm=round(gap, 4), trunk_width_nm=width, dru_floor_nm=floor,
        licensed_unconditionally=bool(r.get("ok") and width >= floor),
        far=far, grid_nm=a.grid, seconds=round(dt, 2),
        return_keepout=keepout, plane_blocks=blocks,
        ok=bool(r.get("ok")), reason=r.get("reason"), why=r.get("why"),
        layers=r.get("layers"), terminals=r.get("terminals"),
        mm=r.get("mm"), stub_mm=r.get("stub_mm"),
        mm_by_layer=r.get("mm_by_layer"), vias_count=r.get("vias"),
        launches=r.get("launches"),
        tracks=tracks, barrels=vias)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    print(" %s %s<->%s %.3f mm far=%s -> %s"
          % (a.net, a.a, a.b, gap, ",".join(far),
             ("CLOSES trunk %.3f mm, %d barrel%s, %s, %.4f mm"
              % (width / 1e6, r.get("vias") or 0,
                 "" if r.get("vias") == 1 else "s",
                 "->".join(r.get("layers") or []), r.get("mm") or 0.0))
             if r.get("ok") else "%s (%s)" % (r.get("reason"), r.get("why"))),
          file=sys.stderr, flush=True)
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
