#!/usr/bin/env python3
"""READ-ONLY: the same question with the /ACC_DETECT_N BARREL at (57.900,38.800)
also out -- a 0.60 mm via plus the zone's own 0.25 mm local clearance excludes
1.10 mm of x, which is wider than the 0.751 mm channel it stands at the head of."""
import shutil, sys, tempfile
from pathlib import Path
import pcbnew
SRC = Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else None
tmp = Path(tempfile.mkdtemp(prefix="aqroot-u214b-"))
for ext in (".kicad_pcb", ".kicad_pro", ".kicad_dru"):
    shutil.copy(SRC.with_suffix(ext), tmp / ("p" + ext))
b = pcbnew.LoadBoard(str(tmp / "p.kicad_pcb"))
def near(p, q): return abs(p.x/1e6-q[0]) < 1e-4 and abs(p.y/1e6-q[1]) < 1e-4
DROP = [("GND", (58.700,39.375), (60.600,38.425)),
        ("/ACC_DETECT_N", (57.800,40.700), (57.800,38.900)),
        ("/ACC_DETECT_N", (57.650,40.850), (57.800,40.700))]
doomed = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        if t.GetNetname() == "/ACC_DETECT_N" and near(t.GetPosition(), (57.900, 38.800)):
            doomed.append(t)
        continue
    for net, a, c in DROP:
        if t.GetNetname() != net: continue
        s, e = t.GetStart(), t.GetEnd()
        if (near(s,a) and near(e,c)) or (near(s,c) and near(e,a)): doomed.append(t)
print("removing", len(doomed))
for t in doomed: b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(str(tmp / "p.kicad_pcb"), b)
del b
if OUT:
    for ext in (".kicad_pcb", ".kicad_pro", ".kicad_dru"):
        shutil.copy(tmp / ("p" + ext), OUT.with_suffix(ext))
b = pcbnew.LoadBoard(str(tmp / "p.kicad_pcb"))
sys.path.insert(0, "/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
import pour_bond_guard as pbg
a = (int(58.4e6), int(39.4e6)); c = (int(58.0e6), int(41.6e6))
for pour in pbg.read_pours(b):
    if pour["net"] != "GND" or pour["layer"] != "B.Cu": continue
    for isl in pour["islands"]:
        if isl["poly"].Contains(pcbnew.VECTOR2I(*a), -1, 0):
            both = isl["poly"].Contains(pcbnew.VECTOR2I(*c), -1, 0)
            print("U21.4 island area %.3f mm2   holds the body south of U21: %s"
                  % (isl["area_mm2"], both))
            if both:
                g = pbg.geodesic(isl["edges"], (a[0],a[1],100000), (c[0],c[1],150000), 400000, 25000)
                if g: print("  narrowest pour path %.3f mm over %.3f mm" % (2*g["radius"]/1e6, g["mm"]))
            raise SystemExit
print("U21.4 in no GND pour island at all")
