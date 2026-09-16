#!/usr/bin/env python3
"""Score a proposed multi-part B.Cu placement: courtyard overlaps + land
clearance to every foreign object, using the same SHAPE.Collide predicate
KiCad's DRC evaluates.  READ-ONLY on the source board."""
import json, sys
from pathlib import Path
import pcbnew

MM = 1e6
SRC = sys.argv[1]
PLAN = json.loads(Path(sys.argv[2]).read_text())   # {ref: [x_mm, y_mm, rot_deg]}
WANT = float(sys.argv[3]) if len(sys.argv) > 3 else 0.20

b = pcbnew.LoadBoard(SRC)
moving = set(PLAN)

# ---- apply the plan in memory -------------------------------------------
for ref, (x, y, rot) in PLAN.items():
    f = b.FindFootprintByReference(ref)
    assert f is not None, ref
    f.SetOrientationDegrees(float(rot))
    f.SetPosition(pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM))))

# ---- obstacles: everything not on a moving footprint ---------------------
obs = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        for L in t.GetLayerSet().CuStack():
            obs.append((t.GetNetname(), L, t.GetEffectiveShape(L), "via@%.3f,%.3f" % (t.GetStart().x/MM, t.GetStart().y/MM)))
    else:
        obs.append((t.GetNetname(), t.GetLayer(), t.GetEffectiveShape(t.GetLayer()),
                    "%s trk (%.3f,%.3f)-(%.3f,%.3f)" % (b.GetLayerName(t.GetLayer()),
                     t.GetStart().x/MM, t.GetStart().y/MM, t.GetEnd().x/MM, t.GetEnd().y/MM)))
for f in b.GetFootprints():
    if f.GetReference() in moving:
        continue
    for p in f.Pads():
        for L in p.GetLayerSet().CuStack():
            obs.append((p.GetNetname(), L, p.GetEffectiveShape(L),
                        "%s.%s pad" % (f.GetReference(), p.GetNumber())))

rows = []
worst_all = (1e9, None)
for ref in PLAN:
    f = b.FindFootprintByReference(ref)
    for p in f.Pads():
        mynet = p.GetNetname()
        for L in p.GetLayerSet().CuStack():
            shp = p.GetEffectiveShape(L)
            for onet, oL, oshp, who in obs:
                if oL != L: continue
                if onet and onet == mynet: continue
                lo, hi = 0, int(round(0.60 * MM))
                if not shp.Collide(oshp, hi):
                    dist = hi
                else:
                    while hi - lo > 2500:
                        mid = (lo + hi) // 2
                        if shp.Collide(oshp, mid): hi = mid
                        else: lo = mid
                    dist = lo
                if dist < WANT * MM:
                    rows.append({"pad": "%s.%s" % (ref, p.GetNumber()), "layer": b.GetLayerName(L),
                                 "net": mynet, "vs": who, "vs_net": onet, "clearance_mm": round(dist/MM, 4)})
                if dist/MM < worst_all[0]:
                    worst_all = (dist/MM, "%s.%s vs %s" % (ref, p.GetNumber(), who))

# ---- courtyard overlaps --------------------------------------------------
cys = []
for f in b.GetFootprints():
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.GetLayer() == pcbnew.B_Cu else pcbnew.F_CrtYd)
    if cy and cy.OutlineCount():
        bb = cy.BBox()
        cys.append((f.GetReference(), f.GetLayer(),
                    bb.GetLeft()/MM, bb.GetTop()/MM, bb.GetRight()/MM, bb.GetBottom()/MM))
overlaps = []
for ref in PLAN:
    me = [c for c in cys if c[0] == ref][0]
    for c in cys:
        if c[0] == ref or c[1] != me[1]: continue
        if me[2] < c[4] and c[2] < me[4] and me[3] < c[5] and c[3] < me[5]:
            overlaps.append({"a": ref, "b": c[0],
                             "a_box": [me[2], me[3], me[4], me[5]], "b_box": [c[2], c[3], c[4], c[5]]})

# ---- THT/NPTH hole proximity --------------------------------------------
holes = []
for f in b.GetFootprints():
    if f.GetReference() in moving: continue
    for p in f.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            holes.append((f.GetReference()+"."+p.GetNumber(), p.GetPosition().x/MM, p.GetPosition().y/MM, max(p.GetDrillSizeX(), p.GetDrillSizeY())/MM))

out = {"want_mm": WANT, "violations": rows, "courtyard_overlaps": overlaps,
       "worst_pad_clearance_mm": round(worst_all[0], 4), "worst_pair": worst_all[1],
       "placed": {r: PLAN[r] for r in PLAN}}
print(json.dumps(out, indent=1))
