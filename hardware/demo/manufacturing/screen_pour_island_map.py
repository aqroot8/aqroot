#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: is this open LAND a land, or a SEVERED POUR ISLAND?

`maze3d.net_islands` groups a net's PADS by the copper that joins them, and
every routing instrument in this directory takes its islands from it.  That is
the right grouping for CONNECTIVITY and it is the wrong picture for a
POUR-OWNING net, because it says nothing about the copper a land is already
bonded to.  On this board `R129.1` is reported as an island of ONE land, and
KiCad's own connectivity joins it to `ZONE:F +3V3 PLANE`, to
`ZONE:In3 +3V3 PLANE`, to a `PCB_TRACK` and to a `PCB_VIA` -- it is bonded to a
25.2 mm2 SEVERED PIECE of its own plane, 1.77 mm from the plane body.

The distinction is not academic and D-647 measured what it cost.  This board's
`.kicad_dru` section 12b records that every `R129.1` escape relief since D-606
was REVERTED by `relief_stitch`'s connectivity retake -- *"the same refusal, to
the same 0.547 mm figure, twenty-six decisions later"* -- and the reason is that
EVERY barrel site the relief can find lies inside the SAME severed island the
land is already bonded to.  The barrel connects the land to itself.  Nothing in
the repository could say so, because nothing asked which OUTLINE a land sits on.

So this screen asks exactly that, per land, per pour-owning net:

  * WHICH filled outline of WHICH zone contains the land, on every layer;
  * that outline's AREA, and whether it is the zone's BODY -- the largest;
  * when it is not, the GAP from it to the body, which is the distance an
    island jumper, a detour or a placement change actually has to close.

It is read-only: it loads the board, reads `GetFilledPolysList` for each zone
and never writes anything.  It states its own limits before its numbers:

  * `PointInside` is asked of the pad's CENTRE, so a land whose centre sits in
    a zone's thermal or clearance carve-out reads as "on no outline" even where
    the plane passes under its edge -- and a land whose centre is over the
    plane is not thereby CONNECTED to it, which is exactly the `U4.5`/`U4.8`
    case: the `In3` body runs directly beneath both and neither has a barrel.
    Read this beside KiCad's own connectivity, never instead of it.
  * the gap is measured vertex-to-edge between the two closed chains, which is
    exact for the polygons KiCad fills and is a LOWER bound on the copper a
    jumper would need.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def _pts(outline):
    return [(outline.CPoint(i).x, outline.CPoint(i).y)
            for i in range(outline.PointCount())]


def _pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy)
                     / float(dx * dx + dy * dy)))
    return ((px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2) ** 0.5


def _outline_gap(a, b):
    """Min vertex-to-edge distance between two closed chains, in nm."""
    pa, pb = _pts(a), _pts(b)
    best = float("inf")
    for src, dst in ((pa, pb), (pb, pa)):
        for px, py in src:
            for i in range(len(dst)):
                ax, ay = dst[i]
                bx, by = dst[(i + 1) % len(dst)]
                best = min(best, _pt_seg(px, py, ax, ay, bx, by))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*", help="default = every pour-owning net")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--open-only", action="store_true",
                    help="report only the lands KiCad's connectivity leaves "
                         "joined to no other pad of the net")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    before = hashlib.sha256(a.board.read_bytes()).hexdigest()
    b = pcbnew.LoadBoard(str(a.board))
    b.BuildConnectivity()
    conn = b.GetConnectivity()

    zones = []
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for lid in z.GetLayerSet().Seq():
            poly = z.GetFilledPolysList(lid)
            if poly is None or not poly.OutlineCount():
                continue
            ols = [poly.Outline(i) for i in range(poly.OutlineCount())]
            big = max(range(len(ols)), key=lambda i: ols[i].Area())
            zones.append(dict(net=z.GetNetname(), name=z.GetZoneName(),
                              layer=b.GetLayerName(lid), outlines=ols, body=big))

    wanted = set(a.nets) or {z["net"] for z in zones}
    doc = dict(schema=1, board=str(a.board), board_sha256=before,
               question="for every land of a pour-owning net: which FILLED "
                        "OUTLINE holds it, is that outline the zone's BODY, "
                        "and if not how far is the body",
               method="read-only; KiCad's own GetFilledPolysList and "
                      "GetConnectedItems, pad CENTRE tested by PointInside, "
                      "gap measured vertex-to-edge between the two chains",
               zones=[dict(net=z["net"], zone=z["name"], layer=z["layer"],
                           outlines=len(z["outlines"]),
                           body_area_mm2=round(z["outlines"][z["body"]].Area() / 1e12, 4))
                      for z in zones],
               lands={})

    for f in b.GetFootprints():
        for p in f.Pads():
            net = p.GetNetname()
            if net not in wanted or not p.GetNumber():
                continue
            joined = [i for i in conn.GetConnectedItems(p)
                      if i.GetClass() == "PAD"]
            alone = len(joined) <= 1
            if a.open_only and not alone:
                continue
            pos = p.GetPosition()
            rec = dict(net=net, at=[round(pos.x / 1e6, 4), round(pos.y / 1e6, 4)],
                       joined_pads=len(joined), alone=alone, on={})
            V = pcbnew.VECTOR2I(int(pos.x), int(pos.y))
            for z in zones:
                if z["net"] != net:
                    continue
                hit = None
                for i, o in enumerate(z["outlines"]):
                    if o.PointInside(V):
                        hit = i
                        break
                if hit is None:
                    continue
                body = z["body"]
                gap = (None if hit == body else
                       round(_outline_gap(z["outlines"][hit],
                                          z["outlines"][body]) / 1e6, 4))
                rec["on"]["%s|%s" % (z["name"], z["layer"])] = dict(
                    outline=hit, is_body=(hit == body),
                    area_mm2=round(z["outlines"][hit].Area() / 1e12, 4),
                    gap_to_body_mm=gap,
                    body_area_mm2=round(z["outlines"][body].Area() / 1e12, 4))
            doc["lands"][f.GetReference() + "." + p.GetNumber()] = rec

    doc["board_sha256_at_write"] = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc["authoritative_unchanged"] = doc["board_sha256_at_write"] == before
    for ref in sorted(doc["lands"]):
        r = doc["lands"][ref]
        if r["alone"] or not a.open_only:
            print("%-10s %-6s alone=%-5s %s"
                  % (ref, r["net"][:6], r["alone"], json.dumps(r["on"])),
                  flush=True)
    if a.out:
        a.out.write_text(json.dumps(doc, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
