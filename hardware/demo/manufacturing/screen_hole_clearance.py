#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: WHOSE GEOMETRY IS EACH DRILL-TO-COPPER ERROR?

`hole_clearance` has been carried on this board as a count -- five inherited
errors, quoted in every decision since D-302 -- and a count cannot be acted on.
D-676 took the question apart by hand for ONE footprint and found two different
things wearing one name:

  * a LAND PATTERN error, where the hole and the copper are BOTH placed by the
    same footprint and neither can move without revising the footprint.  `J3`'s
    own Oe0.65 mm locating pegs stand **0.1944 mm** from `J3`'s own `GND`
    contacts; `MK1`'s Oe1.05 mm acoustic port is INSIDE its own Oe1.65 mm `GND`
    annulus by the construction D-227 ratified.  No router can move either.
    The levers are a FOOTPRINT REVISION, a DIFFERENT PART, or a rule scoped to
    that footprint's own objects.

  * a ROUTED-COPPER error, where one side is a track or a barrel some
    transaction laid.  That one IS routing, and it is the one a scoped rule must
    never touch -- which is why the classification is the point: D-676's `GND`
    `J3.A12/B1` transaction put ELEVEN such errors against the same peg, and a
    rule written to accept the receptacle's own land pattern must still refuse
    every one of them.

So this screen answers, for every drilled hole on the board:

    OWN_FOOTPRINT_LAND_PATTERN   hole and copper belong to the SAME footprint
                                 and both are PADS -- vendor geometry
    FOREIGN_FOOTPRINT_PAD        pads of two DIFFERENT footprints -- PLACEMENT
    ROUTED_COPPER                the copper is a track or a via -- ROUTING
    OWN_ROUTED_COPPER            a track/via of a net, against a hole of the
                                 footprint that net's own pad sits in

and it measures the gap itself -- the hole's `GetEffectiveHoleShape()` capsule
against the copper's `GetEffectivePolygon()` / segment -- so the number is not a
re-print of a DRC sentence.  It then RE-READS KiCad's own DRC on the same board
and reports `agrees_with_drc`, `drc_pairs_not_found` and `found_below_rule_not_in_drc`,
because a geometry screen that silently disagrees with the authority is worth
nothing.

    python3 screen_hole_clearance.py [--board PCB] [--rule-mm X] [-o OUT.json]

`--rule-mm` defaults to the board's own `min_hole_clearance`.  Nothing is
written: the board's sha256 is re-read at exit.
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTHORITY = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
M = 1000000.0
NPTH = pcbnew.PAD_ATTRIB_NPTH
PTH = pcbnew.PAD_ATTRIB_PTH
SEARCH_MM = 3.0


def _seg_seg(ax, ay, bx, by, cx, cy, dx, dy):
    """Shortest distance between segments AB and CD (nm in, nm out)."""
    def pt_seg(px, py, x0, y0, x1, y1):
        vx, vy = x1 - x0, y1 - y0
        den = float(vx * vx + vy * vy)
        if den <= 0.0:
            return math.hypot(px - x0, py - y0)
        t = ((px - x0) * vx + (py - y0) * vy) / den
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        return math.hypot(px - (x0 + t * vx), py - (y0 + t * vy))

    def cross(ox, oy, px, py, qx, qy):
        return (px - ox) * (qy - oy) - (py - oy) * (qx - ox)

    d1 = cross(ax, ay, bx, by, cx, cy)
    d2 = cross(ax, ay, bx, by, dx, dy)
    d3 = cross(cx, cy, dx, dy, ax, ay)
    d4 = cross(cx, cy, dx, dy, bx, by)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg(cx, cy, ax, ay, bx, by), pt_seg(dx, dy, ax, ay, bx, by),
               pt_seg(ax, ay, cx, cy, dx, dy), pt_seg(bx, by, cx, cy, dx, dy))


def _in_poly(px, py, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > py) != (y1 > py):
            t = (py - y0) / float(y1 - y0)
            if px < x0 + t * (x1 - x0):
                inside = not inside
    return inside


def _capsule_poly(seg, r, poly):
    """Gap between a capsule (segment `seg`, radius r) and a polygon.

    A hole whose axis runs INSIDE the copper is an overlap, not a gap: the
    edge-to-edge distance would report the annulus half-width and call a hole
    drilled through its own pad the widest clearance on the board.  `MK1`'s
    acoustic port is exactly that geometry, so the containment test comes first.
    """
    (ax, ay), (bx, by) = seg
    if _in_poly(ax, ay, poly) or _in_poly(bx, by, poly):
        return 0.0
    best = None
    n = len(poly)
    for i in range(n):
        cx, cy = poly[i]
        dx, dy = poly[(i + 1) % n]
        d = _seg_seg(ax, ay, bx, by, cx, cy, dx, dy)
        best = d if best is None else min(best, d)
    return (best or 0.0) - r


def _capsule_capsule(seg_a, ra, seg_b, rb):
    (ax, ay), (bx, by) = seg_a
    (cx, cy), (dx, dy) = seg_b
    return _seg_seg(ax, ay, bx, by, cx, cy, dx, dy) - ra - rb


def _poly_points(sps):
    out = []
    for oi in range(sps.OutlineCount()):
        o = sps.Outline(oi)
        pts = [(o.CPoint(i).x, o.CPoint(i).y) for i in range(o.PointCount())]
        if len(pts) >= 3:
            out.append(pts)
    return out


def _hole(pad):
    """(segment, radius) of a pad's drilled hole, or None."""
    if not pad.HasDrilledHole() and not pad.HasHole():
        return None
    s = pad.GetEffectiveHoleShape()
    if s is None:
        return None
    try:
        a, b = s.GetSeg().A, s.GetSeg().B
        return ((a.x, a.y), (b.x, b.y)), s.GetWidth() / 2.0
    except Exception:
        p = pad.GetPosition()
        d = pad.GetDrillSize()
        return ((p.x, p.y), (p.x, p.y)), max(d[0], d[1]) / 2.0


def _bbox_near(c, o, slack):
    a, b = c.GetBoundingBox(), o.GetBoundingBox()
    return not (a.GetRight() + slack < b.GetLeft()
                or b.GetRight() + slack < a.GetLeft()
                or a.GetBottom() + slack < b.GetTop()
                or b.GetBottom() + slack < a.GetTop())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=AUTHORITY)
    ap.add_argument("--rule-mm", type=float, default=None)
    ap.add_argument("--search-mm", type=float, default=SEARCH_MM)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    before = hashlib.sha256(a.board.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(a.board))
    rule_nm = (int(round(a.rule_mm * M)) if a.rule_mm is not None
               else board.GetDesignSettings().m_HoleClearance)
    slack = int(round(a.search_mm * M))

    # every drilled hole, and every copper object, labelled once
    holes, coppers = [], []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for p in fp.Pads():
            h = _hole(p)
            if h is not None:
                holes.append(dict(ref=ref, num=p.GetNumber(), item=p,
                                  kind=("NPTH" if p.GetAttribute() == NPTH
                                        else "PTH"),
                                  seg=h[0], r=h[1],
                                  uuid=str(p.m_Uuid.AsString())))
            for lid in p.GetLayerSet().CuStack():
                try:
                    sps = p.GetEffectivePolygon(lid)
                except Exception:
                    continue
                for poly in _poly_points(sps):
                    coppers.append(dict(kind="pad", ref=ref, num=p.GetNumber(),
                                        net=p.GetNetname(), item=p,
                                        layer=board.GetLayerName(lid),
                                        poly=poly,
                                        uuid=str(p.m_Uuid.AsString())))
                break          # one copper outline per pad is enough
    for tr in board.GetTracks():
        if tr.GetClass() == "PCB_VIA":
            pos = tr.GetPosition()
            holes.append(dict(ref=None, num=None, item=tr, kind="VIA",
                              seg=((pos.x, pos.y), (pos.x, pos.y)),
                              r=tr.GetDrillValue() / 2.0,
                              uuid=str(tr.m_Uuid.AsString())))
            coppers.append(dict(kind="via", ref=None, num=None,
                                net=tr.GetNetname(), item=tr, layer="*",
                                seg=((pos.x, pos.y), (pos.x, pos.y)),
                                r=tr.GetWidth(pcbnew.F_Cu) / 2.0
                                if hasattr(tr, "GetWidth") else 0.0,
                                uuid=str(tr.m_Uuid.AsString())))
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        coppers.append(dict(kind="track", ref=None, num=None,
                            net=tr.GetNetname(), item=tr,
                            layer=board.GetLayerName(tr.GetLayer()),
                            seg=((s.x, s.y), (e.x, e.y)),
                            r=tr.GetWidth() / 2.0,
                            uuid=str(tr.m_Uuid.AsString())))

    def gap(h, c):
        if "poly" in c:
            return _capsule_poly(h["seg"], h["r"], c["poly"])
        return _capsule_capsule(h["seg"], h["r"], c["seg"], c["r"])

    def classify(h, c):
        if c["kind"] == "pad":
            if h["ref"] is not None and c["ref"] == h["ref"]:
                return "OWN_FOOTPRINT_LAND_PATTERN"
            return "FOREIGN_FOOTPRINT_PAD"
        if h["ref"] is None:
            return "ROUTED_COPPER"
        own = any(p.GetNetname() == c["net"]
                  for p in h["item"].GetParentFootprint().Pads()) \
            if h["ref"] is not None else False
        return "OWN_ROUTED_COPPER" if own else "ROUTED_COPPER"

    rows = []
    for h in holes:
        hole_net = (h["item"].GetNetname()
                    if h["kind"] != "NPTH" else None)
        for c in coppers:
            if c["uuid"] == h["uuid"]:
                continue
            # KiCad's hole-clearance check is between DIFFERENT nets: a via's
            # own track arrives AT the barrel, and reporting that as a drill
            # violation would bury the four errors that are real under two
            # hundred that are the connection working.  An NPTH has no net, so
            # every pad it stands beside is foreign to it.
            if hole_net and c["net"] and hole_net == c["net"]:
                continue
            if not _bbox_near(h["item"], c["item"], slack):
                continue
            g = gap(h, c)
            if g >= rule_nm:
                continue
            rows.append(dict(
                hole="%s.%s" % (h["ref"], h["num"]) if h["ref"] else "via",
                hole_kind=h["kind"],
                hole_xy=[round(h["seg"][0][0] / M, 4),
                         round(h["seg"][0][1] / M, 4)],
                hole_dia_mm=round(2 * h["r"] / M, 4),
                copper=("%s.%s" % (c["ref"], c["num"]) if c["ref"]
                        else c["kind"]),
                copper_kind=c["kind"], copper_net=c["net"],
                copper_layer=c["layer"],
                gap_mm=round(g / M, 4),
                deficit_mm=round((rule_nm - g) / M, 4),
                classification=classify(h, c),
                hole_uuid=h["uuid"], copper_uuid=c["uuid"]))
    rows.sort(key=lambda r: (r["classification"], r["gap_mm"], r["hole"],
                             r["copper"]))

    # THE AUTHORITY IS KiCad's OWN DRC, AND THE SCREEN SAYS SO.
    with tempfile.TemporaryDirectory(prefix="aqroot-hole-clr-") as tmp:
        rep = Path(tmp) / "drc.json"
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json",
                        "--severity-all", "-o", str(rep), str(a.board)],
                       check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        drc = json.loads(rep.read_text(encoding="utf-8"))
    drc_rows = [v for v in drc["violations"] if v["type"] == "hole_clearance"]
    drc_keys, drc_said = set(), {}
    for v in drc_rows:
        key = frozenset(i["uuid"] for i in v["items"])
        drc_keys.add(key)
        m = re.search(r"actual ([0-9.]+) mm", v["description"])
        rule = re.search(r"rule '([^']+)'", v["description"])
        drc_said[key] = dict(
            drc_actual_mm=float(m.group(1)) if m else None,
            drc_rule=(rule.group(1) if rule
                      else "board setup constraints hole clearance"))
    mine = {frozenset((r["hole_uuid"], r["copper_uuid"])): r for r in rows}
    not_found = [v["description"] + " | " + " / ".join(
        i["description"] for i in v["items"])
        for v in drc_rows
        if frozenset(i["uuid"] for i in v["items"]) not in mine]
    extra = [r for k, r in mine.items() if k not in drc_keys]
    for r in rows:
        key = frozenset((r["hole_uuid"], r["copper_uuid"]))
        r["in_drc"] = key in drc_keys
        # KiCad's own arc geometry is the AUTHORITY for the number; this
        # screen's polygon approximation of a roundrect corner reads a couple
        # of microns WIDE, so both figures are carried and neither is hidden.
        r.update(drc_said.get(key, {}))

    counts = {}
    for r in rows:
        if r["in_drc"]:
            counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(
        schema=1, board=str(a.board), board_sha256=before,
        authoritative_unchanged=(before == after),
        board_is_authority=(a.board.resolve() == AUTHORITY.resolve()),
        rule_mm=round(rule_nm / M, 4), search_mm=a.search_mm,
        question=("for every drill-to-copper error on this board, WHOSE "
                  "geometry is it -- a footprint's own land pattern, a "
                  "placement, or routed copper"),
        method=("read-only.  The gap is measured from the hole's own "
                "`GetEffectiveHoleShape()` capsule to the copper's "
                "`GetEffectivePolygon()` / segment, then KiCad's own DRC is "
                "re-run on the same board and the two are compared by item "
                "UUID.  Zone fills are NOT walked: a refill honours the rule "
                "by construction and KiCad reports none here"),
        drc_hole_clearance_errors=len(drc_rows),
        classification_counts=counts,
        # TWO DIRECTIONS, AND ONLY ONE OF THEM IS A BUG.  A pair KiCad
        # reports and this screen did not find is a hole in the geometry --
        # `agrees_with_drc` is that test and nothing else.  A pair this screen
        # finds BELOW the board-setup default that KiCad does NOT report is the
        # expected reading once a SCOPED `hole_clearance` rule covers it: the
        # screen measures against one number, the board may carry several, and
        # the rule that governs each pair is named in the `.kicad_dru`.
        agrees_with_drc=(not not_found),
        drc_pairs_not_found=not_found,
        below_board_default_accepted_by_a_scoped_rule=[
            {k: v for k, v in r.items() if k != "in_drc"} for r in extra],
        accepted_by_scoped_rule=len(extra),
        rows=rows)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for r in rows:
        print(" %-28s %-22s %-10s gap %7.4f  deficit %7.4f  %s%s"
              % (r["classification"], r["hole"] + " " + r["hole_kind"],
                 r["copper"], r["gap_mm"], r["deficit_mm"],
                 r["copper_net"] or "-", "" if r["in_drc"] else "  [NOT IN DRC]"))
    print("rule %.4f mm | DRC hole_clearance %d | classes %s | "
          "accepted by a scoped rule %d | agrees %s"
          % (rule_nm / M, len(drc_rows), counts, len(extra),
             doc["agrees_with_drc"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
