#!/usr/bin/env python3
"""READ-ONLY: score a COORDINATED multi-part move by the clearance every moved
land would have to every foreign object, and by courtyard overlap, with ALL the
moves applied at once.  d680-placement-site-clearance.py answers for ONE part
against a board where the others have not moved, which cannot score a column
that has to travel together."""
import sys, json, itertools
from pathlib import Path
import pcbnew
SRC = "/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
MM = 1e6
# argv: REF:dx_mm:dy_mm  [REF:dx:dy ...]
MOVES = {}
for a in sys.argv[1:]:
    r, dx, dy = a.split(":")
    MOVES[r] = (int(round(float(dx) * MM)), int(round(float(dy) * MM)))

b = pcbnew.LoadBoard(SRC)
for ref, (dx, dy) in MOVES.items():
    f = b.FindFootprintByReference(ref)
    if f is None:
        raise SystemExit("no such ref %s" % ref)
    p = f.GetPosition()
    f.SetPosition(pcbnew.VECTOR2I(p.x + dx, p.y + dy))

moved = set(MOVES)
mine = set()
for ref in moved:
    mine |= {p.GetNetname() for p in b.FindFootprintByReference(ref).Pads()}
mine.add("")

obs = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        for L in t.GetLayerSet().CuStack():
            obs.append(("via " + t.GetNetname(), {L}, t.GetEffectiveShape(L)))
    else:
        obs.append(("trk " + t.GetNetname(), {t.GetLayer()},
                    t.GetEffectiveShape(t.GetLayer())))
for f in b.GetFootprints():
    if f.GetReference() in moved:
        continue
    for p in f.Pads():
        for L in p.GetLayerSet().CuStack():
            obs.append(("%s.%s %s" % (f.GetReference(), p.GetNumber(),
                                      p.GetNetname()), {L},
                        p.GetEffectiveShape(L)))

worst = []
for ref in sorted(moved):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        pl = set(p.GetLayerSet().CuStack())
        net = p.GetNetname()
        for oname, ol, oshape in obs:
            if not (pl & ol):
                continue
            if oname.split(" ", 1)[-1] == net and net:
                continue
            shp = p.GetEffectiveShape(next(iter(pl & ol)))
            hi = int(round(0.60 * MM))
            if not shp.Collide(oshape, hi):
                continue
            lo = 0
            while hi - lo > 5000:
                mid = (lo + hi) // 2
                if shp.Collide(oshape, mid):
                    hi = mid
                else:
                    lo = mid
            worst.append((lo / MM, "%s.%s(%s)" % (ref, p.GetNumber(), net),
                          oname))
worst.sort()
print("== 15 tightest moved-land clearances (foreign nets only)")
for d, a, o in worst[:15]:
    print("   %6.4f mm  %-32s vs %s" % (d, a, o))

print("== courtyard overlaps on the moved parts' own side")
for ref in sorted(moved):
    fp = b.FindFootprintByReference(ref)
    cy = fp.GetCourtyard(pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu)
    if not cy.OutlineCount():
        print("   %s: NO COURTYARD" % ref); continue
    bb = cy.BBox()
    for g in b.GetFootprints():
        if g.GetReference() == ref or g.IsFlipped() != fp.IsFlipped():
            continue
        gc = g.GetCourtyard(pcbnew.B_Cu if g.IsFlipped() else pcbnew.F_Cu)
        if not gc.OutlineCount():
            continue
        if bb.Intersects(gc.BBox()):
            print("   %s OVERLAPS %s" % (ref, g.GetReference()))
    print("   %s court (%.3f,%.3f)-(%.3f,%.3f)" % (
        ref, bb.GetLeft()/MM, bb.GetTop()/MM, bb.GetRight()/MM, bb.GetBottom()/MM))

print("== moved-land to NPTH hole edge")
holes = []
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetDrillSizeX() > 0:
            holes.append((f.GetReference()+"."+p.GetNumber(), p.GetPosition(),
                          p.GetDrillSizeX()/2, p.GetAttribute()))
import math
for ref in sorted(moved):
    fp = b.FindFootprintByReference(ref)
    best = (9e9, None, None)
    for p in fp.Pads():
        for hn, hp, hr, at in holes:
            if hn.split('.')[0] in moved: continue
            d = math.hypot(p.GetPosition().x-hp.x, p.GetPosition().y-hp.y)
            d = (d - hr - max(p.GetSizeX(), p.GetSizeY())/2)/MM
            if d < best[0]: best = (d, "%s.%s"%(ref,p.GetNumber()), hn)
    print("   %s: %.4f mm  %s vs hole %s" % (ref, best[0], best[1], best[2]))
