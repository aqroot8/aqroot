#!/usr/bin/env python3
"""Score candidate sites for ANY footprint: min clearance of every land to
foreign copper, and courtyard overlap under D-691's SHARED-SIDE predicate."""
import sys, itertools
sys.path.insert(0, "/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
import pcbnew
import apply_part_shift as aps
SRC = __import__("os").environ.get("PROBE_BOARD","/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb")
MM = 1e6
REF = sys.argv[1]
XS = [float(v) for v in sys.argv[2].split(",")]
YS = [float(v) for v in sys.argv[3].split(",")]
ROT = float(sys.argv[4]) if len(sys.argv) > 4 else None
SKIP = set(sys.argv[5].split(",")) if len(sys.argv) > 5 else set()
b = pcbnew.LoadBoard(SRC)
fp = b.FindFootprintByReference(REF)
if ROT is not None:
    fp.SetOrientationDegrees(ROT)
pos = fp.GetPosition()
mine = {p.GetNetname() for p in fp.Pads()} | {""}
pads = [(p.GetNumber(), p.GetNetname(), set(p.GetLayerSet().CuStack()),
         p.GetPosition().x - pos.x, p.GetPosition().y - pos.y,
         p.GetSizeX(), p.GetSizeY()) for p in fp.Pads()]
bb0 = fp.GetBoundingBox(False, False)
bw, bh = bb0.GetWidth(), bb0.GetHeight()
bdx = bb0.GetCenter().x - pos.x
bdy = bb0.GetCenter().y - pos.y
MYSIDES = aps._sides(fp)
obs = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        for L in t.GetLayerSet().CuStack():
            obs.append(("via " + t.GetNetname(), {L}, t.GetEffectiveShape(L)))
    else:
        obs.append(("trk " + t.GetNetname(), {t.GetLayer()},
                    t.GetEffectiveShape(t.GetLayer())))
boxes = []
for f in b.GetFootprints():
    if f.GetReference() == REF or f.GetReference() in SKIP:
        continue
    for p in f.Pads():
        for L in p.GetLayerSet().CuStack():
            obs.append(("%s.%s %s" % (f.GetReference(), p.GetNumber(),
                                      p.GetNetname()), {L},
                        p.GetEffectiveShape(L)))
    if MYSIDES & aps._sides(f):
        boxes.append((f.GetReference(), f.GetBoundingBox(False, False)))
rows = []
for x, y in itertools.product(XS, YS):
    px, py = int(round(x * MM)), int(round(y * MM))
    worst, who = int(0.60 * MM), None
    for num, net, pl, ox, oy, sx, sy in pads:
        shp = pcbnew.SHAPE_RECT(pcbnew.VECTOR2I(px + ox - sx // 2,
                                                py + oy - sy // 2),
                                int(sx), int(sy))
        for oname, ol, osh in obs:
            if oname.split(" ", 1)[-1] in mine or not (pl & ol):
                continue
            hi = int(0.60 * MM)
            if not shp.Collide(osh, hi):
                continue
            lo = 0
            while hi - lo > 5000:
                mid = (lo + hi) // 2
                if shp.Collide(osh, mid):
                    hi = mid
                else:
                    lo = mid
            if lo < worst:
                worst, who = lo, "%s.%s vs %s" % (REF, num, oname)
    nb = pcbnew.BOX2I(pcbnew.VECTOR2I(px + bdx - bw // 2, py + bdy - bh // 2),
                      pcbnew.VECTOR2I(bw, bh))
    clash = sorted({r for r, bx in boxes if nb.Intersects(bx)})
    rows.append((worst / MM, x, y, who, clash))
rows.sort(reverse=True)
for w, x, y, who, cl in rows[:20]:
    print("(%6.2f,%6.2f) clr %6.4f  %-34s courts %s"
          % (x, y, w, who or "-", cl or "CLEAR"))
