#!/usr/bin/env python3
"""D-729 STAGE 1 -- PM-3, reduced to ONE capacitor and 0.500 mm.

D-728's addendum proved `U9.14` `VDD_DR` is a TOPOLOGICAL wall: it sits between
`RFO1` and `RFO2` on 0.500 mm pitch, both arms must cross its lane to reach
inductors that are EAST, and `NFC_RF` may leave neither `B.Cu` nor carry a via.
`VDD_DR` escapes the moment ONE arm stops crossing the lane -- and `RFO1` can
stop crossing it by turning WEST at its existing turn, running north OUTSIDE
`VDD_DR`'s barrel site and coming back east ABOVE it.

The only object in that northern lane is `C47`, `NFC_VDD_A`'s 2.2 uF, which
D-722 already flagged as sitting 4.5 mm from the pin it decouples.  A placement
sweep says the NFC block has no other home for it -- and it does not need one:
**0.500 mm north is enough**, and that also moves it 0.5 mm CLOSER to `U9.7`.

A probe with `C47` parked 4 mm away routed all three nets and took the board
8 -> 4 edges; this is the same shape at the real 0.500 mm.
"""
import sys, json
import pcbnew
SRC, DST = sys.argv[1], sys.argv[2]
LOG = {"removed": []}
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(SRC)
c47 = b.FindFootprintByReference("C47")
p = c47.GetPosition(); c47.SetPosition(pcbnew.VECTOR2I(p.x, p.y - nm(0.5)))
LOG["c47"] = [[round(p.x/1e6,3), round(p.y/1e6,3)], [round(p.x/1e6,3), round(p.y/1e6-0.5,3)]]
# the local copper of the three nets that must be re-laid around the new lane
X0,Y0,X1,Y1 = 30.0, 21.0, 40.0, 29.5
def inside(pt):
    x,y = pt.x/1e6, pt.y/1e6
    return X0 <= x <= X1 and Y0 <= y <= Y1
NETS = ["/04_SPI_B_RADIOS_NFC/NFC_RFO1", "/04_SPI_B_RADIOS_NFC/NFC_VDD_A",
        "/04_SPI_B_RADIOS_NFC/NFC_VDD_AM"]
for t in list(b.GetTracks()):
    if t.GetNetname() not in NETS: continue
    if t.Type()==pcbnew.PCB_VIA_T: continue     # a via under a moved land stays
    s_,e_=t.GetStart(),t.GetEnd()
    if not (inside(s_) and inside(e_)): continue
    LOG["removed"].append([t.GetNetname(),"via" if t.Type()==pcbnew.PCB_VIA_T else "trk",
                           round(s_.x/1e6,3),round(s_.y/1e6,3),round(e_.x/1e6,3),round(e_.y/1e6,3)])
    b.RemoveNative(t)
b.Save(DST)
print(json.dumps({"removed": len(LOG["removed"]), "c47": LOG["c47"]}))
