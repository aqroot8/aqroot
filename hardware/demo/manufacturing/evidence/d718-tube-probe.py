#!/usr/bin/env python3
"""What is the widest GND tube U21.4 can have to a barrel, anywhere in its island?"""
import sys
sys.path.insert(0, "/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
import pcbnew
import pour_bond_guard as pg

BRD = sys.argv[1]
REF = sys.argv[2] if len(sys.argv) > 2 else "U21.4"
board = pcbnew.LoadBoard(BRD)
pours = pg.read_pours(board)
for p in pours:
    pg.assign(board, p)
tgt = None
for p in pours:
    if p["net"] != "GND" or p["lkey"] != "B":
        continue
    for i, e in enumerate(p["islands"]):
        for q in e["pads"]:
            if q["ref"] == REF:
                tgt = (p, i, e, q)
assert tgt, "pad not on any B GND island"
p, i, e, q = tgt
print("island %d  area %.3f mm2  pads %s  vias %d"
      % (i, e["area_mm2"], [x["ref"] for x in e["pads"]], len(e["vias"])))
print("pad anchor x=%.3f y=%.3f r=%.3f" % (q["x"]/1e6, q["y"]/1e6, q["r"]/1e6))
import itertools
best = []
for dx in [x / 10.0 for x in range(-20, 21, 2)]:
    for dy in [y / 10.0 for y in range(-20, 21, 2)]:
        bx, by = q["x"] + dx * 1e6, q["y"] + dy * 1e6
        t = pg.geodesic(e["edges"], (q["x"], q["y"], q["r"]), (bx, by, 400000),
                        1500000, 25000, win_mm=3.0, grows=5)
        if t:
            best.append((2.0 * t["radius"] / 1e6, dx, dy, t["mm"]))
best.sort(reverse=True)
for w, dx, dy, mm in best[:12]:
    print("  tube %.3f mm  barrel at (%+.1f,%+.1f) -> (%.3f,%.3f)  path %.3f mm"
          % (w, dx, dy, q["x"]/1e6+dx, q["y"]/1e6+dy, mm))
