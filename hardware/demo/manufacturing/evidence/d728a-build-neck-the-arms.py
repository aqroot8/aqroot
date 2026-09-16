#!/usr/bin/env python3
"""D-728 OPTION A (HEDGE, NOT PROMOTED) -- neck the two antenna arms through
U9's north-row channel so a 0.400 mm barrel fits between them for VDD_DR.

The 0.200 mm width is NOT a new licence: `.kicad_dru` section 9's "Pad-escape
necking - width, fine-pitch power packages" already grants 0.200 mm to any
track intersecting `U9`'s courtyard and sits AFTER the `NFC_RF` block, so it
wins.  `rf_symmetry_contract` RF2 measures arm LENGTH, which does not change.
"""
import sys, json
import pcbnew
SRC, DST = sys.argv[1], sys.argv[2]
LOG = {"necked": []}
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(SRC)
TOL = 4000
NECK = [("/04_SPI_B_RADIOS_NFC/NFC_RFO1", 34.250, 27.725, 34.250, 26.800),
        ("/04_SPI_B_RADIOS_NFC/NFC_RFO2", 35.250, 27.725, 35.250, 26.800)]
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T: continue
    s_, e_ = t.GetStart(), t.GetEnd()
    for (n, x0, y0, x1, y1) in NECK:
        if t.GetNetname() != n: continue
        if (abs(s_.x-nm(x0))<=TOL and abs(s_.y-nm(y0))<=TOL and abs(e_.x-nm(x1))<=TOL and abs(e_.y-nm(y1))<=TOL) or \
           (abs(e_.x-nm(x0))<=TOL and abs(e_.y-nm(y0))<=TOL and abs(s_.x-nm(x1))<=TOL and abs(s_.y-nm(y1))<=TOL):
            LOG["necked"].append([n, round(t.GetWidth()/1e6,3), 0.200])
            t.SetWidth(nm(0.200))
# The rule area the licence names, drawn around the one barrel it licenses.
zone = pcbnew.ZONE(b)
zone.SetIsRuleArea(True)
zone.SetZoneName("NFC_VDD_DR_ESCAPE")
zone.SetLayerSet(pcbnew.LSET.AllCuMask(b.GetCopperLayerCount()))
for f in (zone.SetDoNotAllowTracks, zone.SetDoNotAllowVias, zone.SetDoNotAllowPads,
          zone.SetDoNotAllowZoneFills, zone.SetDoNotAllowFootprints):
    f(False)
o = zone.Outline(); o.NewOutline()
for (x, y) in ((34.425,26.775),(35.075,26.775),(35.075,27.425),(34.425,27.425)):
    o.Append(nm(x), nm(y))
b.Add(zone)
LOG["rule_area"] = ["NFC_VDD_DR_ESCAPE", 34.425, 26.775, 35.075, 27.425]

b.Save(DST)
print(json.dumps(LOG))
