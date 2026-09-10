#!/usr/bin/env python3
"""READ-ONLY: score candidate destinations for a 2-pad part by the CLEARANCE
its lands would have to every foreign object -- pads, tracks, vias and other
courtyards -- not just by endpoints, which is what apply_part_shift measures and
what let a B.Cu diagonal pass 0.0482 mm under R100.1."""
import itertools, sys
from pathlib import Path
import pcbnew

SRC = "/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
MM = 1e6
REF = sys.argv[1]
XS = [float(v) for v in sys.argv[2].split(",")]
YS = [float(v) for v in sys.argv[3].split(",")]
WANT = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25

b = pcbnew.LoadBoard(SRC)
fp = next(f for f in b.GetFootprints() if f.GetReference() == REF)
mine = {p.GetNetname() for p in fp.Pads()} | {""}
pads = [(p.GetNumber(), p.GetNetname(),
         set(p.GetLayerSet().CuStack()),
         (p.GetPosition().x - fp.GetPosition().x,
          p.GetPosition().y - fp.GetPosition().y),
         p.GetSize().x, p.GetSize().y) for p in fp.Pads()]
cy = fp.GetCourtyard(fp.GetLayer()).BBox()
cw, ch = cy.GetWidth(), cy.GetHeight()
cdx = cy.GetCenter().x - fp.GetPosition().x
cdy = cy.GetCenter().y - fp.GetPosition().y

obs = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        for L in t.GetLayerSet().CuStack():
            obs.append((t.GetNetname(), {L}, t.GetEffectiveShape(L)))
    else:
        obs.append((t.GetNetname(), {t.GetLayer()},
                    t.GetEffectiveShape(t.GetLayer())))
for f in b.GetFootprints():
    if f.GetReference() == REF:
        continue
    for p in f.Pads():
        for L in p.GetLayerSet().CuStack():
            obs.append((p.GetNetname(), {L}, p.GetEffectiveShape(L)))
cys = []
for f in b.GetFootprints():
    if f.GetReference() == REF:
        continue
    if f.GetLayer() != fp.GetLayer():
        continue
    bb = f.GetBoundingBox(False, False)
    cys.append((f.GetReference(), bb))

rows = []
for x, y in itertools.product(XS, YS):
    px, py = int(round(x * MM)), int(round(y * MM))
    worst, who = 1e9, None
    for num, net, pl, (ox, oy), sx, sy in pads:
        shp = pcbnew.SHAPE_RECT(pcbnew.VECTOR2I(px + ox - sx // 2,
                                                py + oy - sy // 2),
                                int(sx), int(sy))
        for onet, ol, oshape in obs:
            if onet in mine or not (pl & ol):
                continue
            # bisect the clearance the two shapes actually have, in 5 um
            # steps up to the ceiling -- SHAPE.Collide(other, clearance) is the
            # same predicate KiCad's DRC evaluates
            lo, hi = 0, int(round(0.60 * MM))
            if not shp.Collide(oshape, hi):
                d = hi
            else:
                while hi - lo > 5000:
                    mid = (lo + hi) // 2
                    if shp.Collide(oshape, mid):
                        hi = mid
                    else:
                        lo = mid
                d = lo
            if d < worst:
                worst, who = d, "%s.%s vs %s" % (REF, num, onet)
    cbb = pcbnew.BOX2I(pcbnew.VECTOR2I(px + cdx - cw // 2, py + cdy - ch // 2),
                       pcbnew.VECTOR2I(cw, ch))
    clash = [r for r, bb in cys if cbb.Intersects(bb)]
    rows.append((worst / MM, x, y, who, clash))
rows.sort(reverse=True)
for w, x, y, who, clash in rows:
    print("(%7.3f,%7.3f)  min copper clearance %6.4f mm  %-40s courtyard %s"
          % (x, y, w, who or "", clash or "clear"))
