#!/usr/bin/env python3
"""THE TPS61023 ACCESSORY BOOST: close /01_POWER_TREE/ACC_5V_LX."""
import sys, json, subprocess
from pathlib import Path
import pcbnew
MFG = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
BRD = sys.argv[1]; LOG = {}
def E(t): return frozenset({(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)})
def nm(v): return int(round(v * 1e6))

b = pcbnew.LoadBoard(BRD)
GND_KILL = {frozenset({(58700000, 39375000), (60600000, 38425000)})}
RAW_KILL = {frozenset({(59022500, 40400000), (60085000, 40475000)}),
            frozenset({(60085000, 40475000), (61050000, 39500000)}),
            frozenset({(61050000, 39500000), (60975000, 39425000)}),
            frozenset({(60975000, 39425000), (60950000, 39425000)}),
            frozenset({(58512500, 40400000), (59022500, 40400000)})}
NFC_KILL = {frozenset({(63500000, 42750000), (63500000, 41800000)}),
            frozenset({(63500000, 42750000), (63500000, 43700000)})}
cnt = {}
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T: continue
    n = t.GetNetname()
    if n == "GND" and E(t) in GND_KILL: b.RemoveNative(t); cnt["gnd"] = cnt.get("gnd",0)+1
    elif n == "/01_POWER_TREE/ACC_5V_RAW" and E(t) in RAW_KILL: b.RemoveNative(t); cnt["raw"] = cnt.get("raw",0)+1
    elif n == "/NFC_5V_EN" and E(t) in NFC_KILL: b.RemoveNative(t); cnt["nfc5ven"] = cnt.get("nfc5ven",0)+1
LOG["removed"] = cnt
b.Save(BRD)

# SYS POUR 2 shrinks from a 5 x 9 mm rectangle to the 1.55 x 5.10 mm strip that
# actually serves its two lands.  The rectangle ISLANDED the converter's GND pin
# from the B.Cu ground plane; the strip leaves the plane continuous from U21.4
# up the inductor canyon, over L4.2's land and east into the plane body.
b = pcbnew.LoadBoard(BRD)
NEW = [(56.60,34.60),(58.15,34.60),(58.15,39.70),(56.60,39.70)]
for z in list(b.Zones()):
    if z.GetZoneName() == "B /01_POWER_TREE/BQ25185_SYS POUR 2":
        sp = pcbnew.SHAPE_POLY_SET(); sp.NewOutline()
        for x, y in NEW: sp.Append(nm(x), nm(y))
        z.SetOutline(sp); LOG["sys_pour_2"] = NEW
b.Save(BRD)

def shift(ref, dx, dy, rot, nets, extra=()):
    rep = Path(BRD).parent / ("shift-%s.json" % ref.lower())
    cmd = [sys.executable, str(MFG / "apply_part_shift.py"), "--board", BRD, "--ref", ref,
           "--dx-nm", str(dx), "--dy-nm", str(dy)]
    if rot: cmd += ["--rot-deg", str(rot)]
    if nets:
        cmd += ["--release"]
        for n in nets: cmd += ["--release-net", n]
    cmd += list(extra) + ["--apply", "--report", str(rep)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    d = json.loads(rep.read_text())
    LOG.setdefault("moves", {})[ref] = {k: d.get(k) for k in
        ("verdict","released_count","release_refusals","vias_in_moved_pads",
         "courtyard_overlaps_new","position_now_mm")}
    if r.returncode != 0:
        print(json.dumps(LOG, indent=1)); print(r.stdout[-2000:]); sys.exit(1)
shift("TP10", 150000, 3250000, 0, ["/NFC_5V_EN"])
shift("C65", 0, 1000000, 0, ["GND", "/01_POWER_TREE/ACC_5V_RAW"], ["--allow-via-in-pad"])

b = pcbnew.LoadBoard(BRD)
def trk(net, x0, y0, x1, y1, w, layer=pcbnew.B_Cu):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(nm(x0), nm(y0))); t.SetEnd(pcbnew.VECTOR2I(nm(x1), nm(y1)))
    t.SetWidth(nm(w)); t.SetLayer(layer); t.SetNet(b.FindNet(net)); b.Add(t)
LX, RAW = "/01_POWER_TREE/ACC_5V_LX", "/01_POWER_TREE/ACC_5V_RAW"
for s in [(58.513, 39.900, 59.150, 39.900, 0.200),
          (59.150, 39.900, 59.900, 39.500, 0.400),
          (59.900, 39.500, 59.900, 38.000, 0.400)]: trk(LX, *s)
for s in [(58.513, 40.400, 58.995, 40.700, 0.200),
          (58.995, 40.700, 60.085, 41.475, 0.400),
          (60.085, 41.475, 60.950, 39.425, 0.400)]: trk(RAW, *s)
trk("/NFC_5V_EN", 63.500, 41.800, 63.500, 43.700, 0.200)
f21 = b.FindFootprintByReference("U21")
for p in f21.Pads():
    if p.GetNumber() == "4":
        p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); LOG["u21_4_zone_connection"] = "FULL"
b.Save(BRD)
for _ in range(2):
    b = pcbnew.LoadBoard(BRD); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(BRD)
print(json.dumps(LOG, indent=1))
