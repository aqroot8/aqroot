#!/usr/bin/env python3
"""D-725 STAGE 3 -- U21.4's ground stitch.

A separate stage for one reason, and it is a KiCad fact worth writing down:
`BOARD::Save` re-assigns a newly added VIA's net to whatever track it lands
on, silently, whatever `SetNet`/`SetNetCode`/`SetIsFree(False)` said.  Stage 2
moves `EXT_SDA_BUF`'s In2 run out of the L4.1<->L4.2 channel; on the board
stage 2 LOADS that run still passes 0.034 mm from (58.900,35.000), so a GND
barrel placed there in stage 2 comes back as `EXT_SDA_BUF`.  Placed after
stage 2 has saved, it stays GND.
"""
import sys, json
import pcbnew
SRC, DST = sys.argv[1], sys.argv[2]
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(SRC)
LOG = {}

def trk(n, x0, y0, x1, y1, w, layer=pcbnew.B_Cu):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(nm(x0), nm(y0))); t.SetEnd(pcbnew.VECTOR2I(nm(x1), nm(y1)))
    t.SetWidth(nm(w)); t.SetLayer(layer); t.SetNet(b.FindNet(n)); b.Add(t)

def via(n, x, y, d, dr):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
    v.SetWidth(nm(d)); v.SetDrill(nm(dr)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(n)); b.Add(v)

# U21.4 carries the TPS61023's full inductor current to ground through the
# low-side FET.  It sits on the B GND PLANE body; this adds the stitch into
# the In1 and In4 GND references that a switching converter's ground pin owes:
# two 0.800/0.400 POWER-class barrels, 4.4 A, 1.6 mm from the pad.
trk("GND", 58.600, 39.300, 58.900, 38.400, 0.400)
trk("GND", 58.900, 38.400, 58.900, 36.000, 0.600)
# ONE barrel, not two: the channel's north mouth belongs to EXT_SDA_BUF's
# F->In2 transition and to XGPIO4 (PROTECTED copper, not relaid), so the only
# site that clears both is (58.900,36.000).  A 0.400 mm drill carries 2.211 A
# at IPC-2221B / 10 K against the 2.19 A this pin owes, and it is stitching on
# top of a pad that already sits on the 202 mm2 B GND PLANE body.
via("GND", 58.900, 36.000, 0.800, 0.400)
LOG["gnd_stitch"] = [[58.9, 36.0, 0.8, 0.4]]

b.Save(DST)
for _ in range(2):
    bb = pcbnew.LoadBoard(DST); pcbnew.ZONE_FILLER(bb).Fill(bb.Zones()); bb.Save(DST)
print(json.dumps(LOG, indent=1))
