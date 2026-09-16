#!/usr/bin/env python3
"""PM-3 STEP A -- /NFC_SUPPLY reaches U9.10, the ST25R3916's VDD_TX pin."""
import sys, json
import pcbnew
BRD = sys.argv[1]; LOG = {}
def E(t): return frozenset({(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)})
def nm(v): return int(round(v * 1e6))
b = pcbnew.LoadBoard(BRD)
# C45.2's ground barrel is REDUNDANT -- its land sits in the B GND PLANE fill --
# and it is one of the two objects that box VDD_TX's only channel.
kill_via = 0
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND" \
       and (t.GetStart().x, t.GetStart().y) == (32200000, 26000000):
        b.RemoveNative(t); kill_via += 1
# NFC_VDD_RF's barrel -- the other one -- steps 0.250 mm west and 0.050 north.
moved = []
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T and (t.GetStart().x, t.GetStart().y) == (32200000, 26900000):
        t.SetPosition(pcbnew.VECTOR2I(31950000, 26850000)); moved.append(t.GetNetname())
KILL = {frozenset({(32250000, 27725000), (32200000, 26900000)}),
        frozenset({(32300000, 27000000), (32200000, 26900000)}),
        frozenset({(32150000, 24800000), (32200000, 26000000)})}
n = 0
for t in list(b.GetTracks()):
    if t.Type() != pcbnew.PCB_VIA_T and E(t) in KILL: b.RemoveNative(t); n += 1
LOG.update(gnd_barrel_removed=kill_via, vdd_rf_barrel_moved=moved, tracks_removed=n)
def trk(net, x0, y0, x1, y1, w, layer=pcbnew.B_Cu):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(nm(x0), nm(y0))); t.SetEnd(pcbnew.VECTOR2I(nm(x1), nm(y1)))
    t.SetWidth(nm(w)); t.SetLayer(layer); t.SetNet(b.FindNet(net)); b.Add(t)
VRF = "/04_SPI_B_RADIOS_NFC/NFC_VDD_RF"
trk(VRF, 32.250, 27.725, 31.950, 26.850, 0.200)
trk(VRF, 32.300, 27.000, 31.950, 26.850, 0.200, pcbnew.F_Cu)
# U9.10 VDD_TX -> NFC_SUPPLY's own 0.400 mm trunk.  The 0.200 mm segment
# INTERSECTS U9's courtyard, which is what the .kicad_dru's pad-escape necking
# rule asks; ST's 350 mArms VDD_RF limit is what makes 0.200 mm right.
trk("/NFC_SUPPLY", 32.750, 27.725, 32.600, 26.200, 0.200)
trk("/NFC_SUPPLY", 32.600, 26.200, 31.230, 25.950, 0.400)
b.Save(BRD)
for _ in range(2):
    b = pcbnew.LoadBoard(BRD); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(BRD)
print(json.dumps(LOG, indent=1))
