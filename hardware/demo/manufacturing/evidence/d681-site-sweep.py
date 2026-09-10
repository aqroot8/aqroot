#!/usr/bin/env python3
"""READ-ONLY: sweep candidate placements for a footprint and report, per site,
the minimum copper clearance its lands would have to every FOREIGN object
(pads, tracks, vias) and which foreign courtyards its own courtyard overlaps.

Same predicate as evidence/d680-placement-site-clearance.py (SHAPE.Collide
bisection) but bbox-prefiltered so a fine sweep is affordable, and it accepts
--board / --rot / --ignore-net so a site can be scored on the board the
transaction will actually leave behind."""
import argparse, itertools, sys
import pcbnew

MM = 1e6
ap = argparse.ArgumentParser()
ap.add_argument("--board", default="/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb")
ap.add_argument("--ref", required=True)
ap.add_argument("--x", required=True, help="x0:x1:step or comma list")
ap.add_argument("--y", required=True)
ap.add_argument("--rot", type=float, default=None, help="absolute orientation in degrees")
ap.add_argument("--ignore-net", action="append", default=[],
                help="treat this net's routed copper as already ripped up")
ap.add_argument("--want", type=float, default=0.20)
ap.add_argument("--top", type=int, default=40)
a = ap.parse_args()

def axis(s):
    if ":" in s:
        p = [float(v) for v in s.split(":")]
        lo, hi, st = p[0], p[1], p[2]
        out, v = [], lo
        while v <= hi + 1e-9:
            out.append(round(v, 4)); v += st
        return out
    return [float(v) for v in s.split(",")]

XS, YS = axis(a.x), axis(a.y)
b = pcbnew.LoadBoard(a.board)
fp = next(f for f in b.GetFootprints() if f.GetReference() == a.ref)
mine = {p.GetNetname() for p in fp.Pads()} | {""}
ignore = set(a.ignore_net)

rot0 = fp.GetOrientationDegrees()
rot = rot0 if a.rot is None else a.rot
import math
dth = math.radians(rot - rot0)
cs, sn = math.cos(dth), math.sin(dth)
origin = fp.GetPosition()

pads = []
for p in fp.Pads():
    ox = p.GetPosition().x - origin.x
    oy = p.GetPosition().y - origin.y
    # KiCad y is down; a positive orientation is CCW on screen => rotate by -dth in screen coords
    nx = ox * cs + oy * sn
    ny = -ox * sn + oy * cs
    sx, sy = p.GetSize().x, p.GetSize().y
    if abs(((rot - rot0) % 180.0) - 90.0) < 1e-6:
        sx, sy = sy, sx
    pads.append((p.GetNumber(), p.GetNetname(), set(p.GetLayerSet().CuStack()),
                 int(round(nx)), int(round(ny)), sx, sy))

obs = []
def add(net, layers, shape):
    if net in mine or net in ignore:
        return
    bb = shape.BBox()
    obs.append((net, set(layers), shape, bb.GetLeft(), bb.GetRight(), bb.GetTop(), bb.GetBottom()))
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        for L in t.GetLayerSet().CuStack():
            add(t.GetNetname(), [L], t.GetEffectiveShape(L))
    else:
        add(t.GetNetname(), [t.GetLayer()], t.GetEffectiveShape(t.GetLayer()))
for f in b.GetFootprints():
    if f.GetReference() == a.ref:
        continue
    for p in f.Pads():
        for L in p.GetLayerSet().CuStack():
            add(p.GetNetname(), [L], p.GetEffectiveShape(L))

cy = fp.GetCourtyard(fp.GetLayer()).BBox()
cw, ch = cy.GetWidth(), cy.GetHeight()
if abs(((rot - rot0) % 180.0) - 90.0) < 1e-6:
    cw, ch = ch, cw
cys = []
for f in b.GetFootprints():
    if f.GetReference() == a.ref or f.GetLayer() != fp.GetLayer():
        continue
    cys.append((f.GetReference(), f.GetBoundingBox(False, False)))

CEIL = int(round(0.60 * MM))
rows = []
for x, y in itertools.product(XS, YS):
    px, py = int(round(x * MM)), int(round(y * MM))
    worst, who = CEIL, None
    for num, net, pl, ox, oy, sx, sy in pads:
        L = px + ox - sx // 2
        T = py + oy - sy // 2
        shp = pcbnew.SHAPE_RECT(pcbnew.VECTOR2I(L, T), int(sx), int(sy))
        R, B_ = L + sx, T + sy
        for onet, ol, oshape, obl, obr, obt, obb in obs:
            if obr < L - CEIL or obl > R + CEIL or obb < T - CEIL or obt > B_ + CEIL:
                continue
            if not (pl & ol):
                continue
            if not shp.Collide(oshape, worst):
                continue
            lo, hi = 0, worst
            while hi - lo > 5000:
                mid = (lo + hi) // 2
                if shp.Collide(oshape, mid):
                    hi = mid
                else:
                    lo = mid
            worst, who = lo, "%s.%s vs %s" % (a.ref, num, onet)
            if worst == 0:
                break
        if worst == 0:
            break
    cbb = pcbnew.BOX2I(pcbnew.VECTOR2I(px - cw // 2, py - ch // 2), pcbnew.VECTOR2I(cw, ch))
    clash = [r for r, bb in cys if cbb.Intersects(bb)]
    rows.append((worst / MM, x, y, who, clash))

rows.sort(key=lambda r: (-r[0], r[1], r[2]))
ok = [r for r in rows if r[0] >= a.want and not r[4]]
print("# %s rot=%.1f  sites=%d  clean(>=%.3f, no courtyard clash)=%d"
      % (a.ref, rot, len(rows), a.want, len(ok)))
for w, x, y, who, clash in rows[:a.top]:
    print("(%7.3f,%7.3f)  min %6.4f  %-42s courtyard %s"
          % (x, y, w, who or "", ",".join(clash) or "clear"))

if ok:
    print("# --- CLEAN SITES ---")
    for w, x, y, who, clash in ok:
        print("CLEAN (%7.3f,%7.3f)  min %6.4f  %s" % (x, y, w, who or ""))
