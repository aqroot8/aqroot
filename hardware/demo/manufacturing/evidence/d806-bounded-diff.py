#!/usr/bin/env python3
"""D-806 bounded diff: frozen D-805 board vs D-806 board, object by object.

Every difference must be one of the three declared D-806 acts, and nothing else:
  G1  J2 pose (0, -0.150 mm) and the J2-pad track ends that moved with it,
      each inside J2's courtyard inflated 0.5 mm;
  G2  the eight U9 corner lands (size and centre), nothing else of U9;
  G3  a via that kept position, net and drill and only grew to hole + 0.20 mm.
Zone FILLS are expected to differ (refill); zone OUTLINES, rule areas, Edge.Cuts,
every other footprint pose and every pad->net assignment must be identical.

    python3 d806-bounded-diff.py D805.kicad_pcb D806.kicad_pcb [-o OUT.json]
"""
import argparse
import json
import sys

import pcbnew

NM = 1e6


def snap(path):
    b = pcbnew.LoadBoard(path)
    fps, pads, tracks, vias, zones, draws = {}, {}, set(), {}, {}, set()
    for f in b.GetFootprints():
        p = f.GetPosition()
        fps[f.GetReference()] = (p.x, p.y, round(f.GetOrientationDegrees(), 6), f.IsFlipped(), f.GetFPIDAsString())
        for q in f.Pads():
            s = q.GetSize(pcbnew.F_Cu)
            pads[(f.GetReference(), q.GetNumber(), q.GetPosition().x, q.GetPosition().y)] = None
            pads.setdefault("__by__", {}).setdefault((f.GetReference(), q.GetNumber()), []).append(
                (q.GetPosition().x, q.GetPosition().y, s.x, s.y, q.GetNetname(), q.GetShape(pcbnew.F_Cu)))
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            vias[(t.GetPosition().x, t.GetPosition().y, t.GetNetname())] = (t.GetWidth(pcbnew.F_Cu), t.GetDrillValue())
        else:
            tracks.add((t.GetNetname(), t.GetLayerName(), t.GetStart().x, t.GetStart().y,
                        t.GetEnd().x, t.GetEnd().y, t.GetWidth(), t.Type()))
    for z in b.Zones():
        o = z.Outline()
        pts = tuple((o.CVertex(i).x, o.CVertex(i).y) for i in range(o.TotalVertices()))
        zones[(z.GetZoneName(), z.GetNetname(), z.GetLayerSet().FmtHex(), z.GetIsRuleArea(), pts)] = 1
    for d in b.GetDrawings():
        draws.add((d.GetLayerName(), d.GetClass(), d.GetPosition().x, d.GetPosition().y,
                   getattr(d, "GetStart", lambda: d.GetPosition())().x, getattr(d, "GetEnd", lambda: d.GetPosition())().y))
    j2 = b.FindFootprintByReference("J2")
    cy = j2.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return b, dict(fps=fps, pads=pads.pop("__by__"), tracks=tracks, vias=vias, zones=zones, draws=draws,
                   j2box=(cy.GetLeft(), cy.GetTop(), cy.GetRight(), cy.GetBottom()))


def inside(box, x, y, m=500000):
    return box[0] - m <= x <= box[2] + m and box[1] - m <= y <= box[3] + m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pre")
    ap.add_argument("post")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    _, A = snap(a.pre)
    _, B = snap(a.post)
    rep, bad = {}, []
    moved = sorted(r for r in set(A["fps"]) | set(B["fps"]) if A["fps"].get(r) != B["fps"].get(r))
    rep["footprints_changed"] = {r: dict(pre=A["fps"].get(r), post=B["fps"].get(r)) for r in moved}
    for r in moved:
        if r != "J2":
            bad.append("footprint %s changed" % r)
    if "J2" in moved:
        p0, p1 = A["fps"]["J2"], B["fps"]["J2"]
        if (p1[0] - p0[0], p1[1] - p0[1]) != (0, -150000) or p0[2:] != p1[2:]:
            bad.append("J2 moved by something other than (0, -0.150 mm)")
    net_changes = [k for k in A["pads"] if [x[4] for x in A["pads"][k]] != [x[4] for x in B["pads"].get(k, [])]]
    rep["pad_net_changes"] = net_changes
    if net_changes or set(A["pads"]) != set(B["pads"]):
        bad.append("pad->net identity changed")
    geo = []
    for k in A["pads"]:
        if k[0] == "J2":
            continue
        if A["pads"][k] != B["pads"][k]:
            geo.append("%s.%s" % k)
    rep["pad_geometry_changes_outside_J2"] = sorted(geo)
    allowed = {"U9.%s" % n for n in ("1", "8", "9", "16", "17", "24", "25", "32")}
    if set(geo) - allowed:
        bad.append("pad geometry changed outside the U9 corner lands: %s" % sorted(set(geo) - allowed))
    out_t, in_t = A["tracks"] - B["tracks"], B["tracks"] - A["tracks"]
    stray = [t for t in (out_t | in_t)
             if not (inside(A["j2box"], t[2], t[3]) and inside(A["j2box"], t[4], t[5]))
             and not (inside(B["j2box"], t[2], t[3]) and inside(B["j2box"], t[4], t[5]))]
    rep["tracks"] = dict(pre=len(A["tracks"]), post=len(B["tracks"]), out=len(out_t), into=len(in_t),
                         outside_J2_window=len(stray),
                         nets=sorted({t[0] for t in out_t | in_t}))
    if stray:
        bad.append("%d track changes outside the J2 window" % len(stray))
    vchg, vbad = [], []
    for k in set(A["vias"]) | set(B["vias"]):
        if A["vias"].get(k) == B["vias"].get(k):
            continue
        pre, post = A["vias"].get(k), B["vias"].get(k)
        ok = pre and post and pre[1] == post[1] and pre[0] < post[0] and post[0] == post[1] + 200000
        (vchg if ok else vbad).append(dict(at=[k[0] / NM, k[1] / NM], net=k[2], pre=pre, post=post))
    rep["vias"] = dict(pre=len(A["vias"]), post=len(B["vias"]), grown_to_hole_plus_0_20=len(vchg),
                       other_via_changes=vbad)
    if vbad:
        bad.append("%d via changes that are not a G3 growth" % len(vbad))
    zd = set(A["zones"]) ^ set(B["zones"])
    rep["zone_outline_or_rule_area_changes"] = len(zd)
    if zd:
        bad.append("zone outlines / rule areas changed")
    dd = A["draws"] ^ B["draws"]
    rep["board_drawing_changes_incl_edge_cuts"] = len(dd)
    if dd:
        bad.append("board drawings / Edge.Cuts changed")
    rep["bounded"] = not bad
    rep["violations"] = bad
    txt = json.dumps(rep, indent=1, sort_keys=True, default=str)
    if a.out:
        open(a.out, "w").write(txt + "\n")
    print(txt)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
