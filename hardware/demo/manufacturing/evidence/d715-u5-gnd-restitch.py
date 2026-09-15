r"""D-715 -- `+3V3` `U5.2` is a POUR CUT, not a routing problem.

`U5.2` is the `MAX98357A`'s `GAIN_SLOT` pin, strapped to `+3V3` for 6 dB
(sheet 06's own note: "GAIN_SLOT -> VDD = 6 dB (WAS GND = 12 dB)").  It has
been an island of ONE land since the fork.

`screen_offcentre_launch` says the land has **NO LEGAL ESCAPE AT ANY WIDTH**
down to 0.150 mm -- blocked by `U5.3`, `U5.1`, `U5.17` and `R15.2` -- so no
route can ever reach it, and the only conductor that can is the `F.Cu` `+3V3`
POUR.  The pour already comes to the land: `U5.2` sits inside filled outline
12 of the `F +3V3 PLANE`, a scrap of **0.183 mm2**, 0.337 mm from the body.
What holds the scrap apart from the body is EIGHT `F.Cu` `GND` objects -- the
local stitch mesh that carries `U5.3` and `R15.2` to their barrels, laid
before the pour was filled and never revisited.

THE SET IS MINIMAL, BY REVERSE GREEDY.  Thirteen `GND` objects lie in the
26.5,113.5 - 29.15,117.0 window.  Removing all thirteen joins `U5.2` to the
82-land `+3V3` body; putting each back one at a time and re-filling with
KiCad's own `ZONE_FILLER` re-opens it for exactly eight of them, and the other
five go back.  The eight are below.  One of them -- the 0.600/0.300 barrel at
(28.500, 115.800) -- is `R15.2`'s only tie, so the transaction owes that land a
new one: a single 0.300 mm `F.Cu` track to the barrel at (27.500, 113.900),
which survives, 1.208 mm away.

GND DOES NOT REGRESS: every other `GND` land in the pocket -- `U5.3`, `U5.11`,
`U5.15`, `U5.17`, `C8.2`, `C10.2` -- keeps its own path, and the routing
ledger reads `GND` at ZERO open edges afterwards.

Usage:  python3 evidence/d715-u5-gnd-restitch.py <BOARD.kicad_pcb>
"""
import sys
import pcbnew

BRD = sys.argv[1]
b = pcbnew.LoadBoard(BRD)
gnd = b.FindNet("GND")

TRACKS = [
    ((27725481, 115086793), (28500000, 115800000), 300000, "R15.2 -> the barrel"),
    ((28600000, 115100000), (27500000, 113900000), 300000, "mesh SW leg"),
    ((28600000, 115650000), (28600000, 115100000), 300000, "mesh N spur"),
    ((28875000, 116125000), (27600000, 115800000), 300000, "mesh W leg"),
    ((28875000, 116125000), (28000000, 115300000), 300000, "mesh NW leg"),
    ((28875000, 116125000), (28600000, 115650000), 300000, "mesh N leg"),
    ((29075000, 116250000), (28875000, 116125000), 300000, "U5.3 corner (x3)"),
    ((27600000, 115800000), (27300000, 115300000), 300000,
     "the stub the mesh left behind: its only neighbour was the W leg"),
]
VIA = (28500000, 115800000)

removed = 0
for a, c, w, why in TRACKS:
    key = frozenset([a, c])
    doomed = [t for t in b.GetTracks()
              if t.Type() != pcbnew.PCB_VIA_T
              and t.GetNetname() == "GND"
              and b.GetLayerName(t.GetLayer()) == "F.Cu"
              and t.GetWidth() == w
              and frozenset([(t.GetStart().x, t.GetStart().y),
                             (t.GetEnd().x, t.GetEnd().y)]) == key]
    assert doomed, why
    for t in doomed:
        b.RemoveNative(t)
    removed += len(doomed)
    print("  -%d  F.Cu GND  %s" % (len(doomed), why))

doomed = [t for t in b.GetTracks()
          if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"
          and (t.GetPosition().x, t.GetPosition().y) == VIA]
assert len(doomed) == 1, doomed
b.RemoveNative(doomed[0])
removed += 1
print("  -1  GND barrel (28.500, 115.800) 0.600/0.300")

t = pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(27725481, 115086793))
t.SetEnd(pcbnew.VECTOR2I(27500000, 113900000))
t.SetWidth(300000)
t.SetLayer(b.GetLayerID("F.Cu"))
t.SetNet(gnd)
b.Add(t)
print("  +1  F.Cu GND  R15.2 -> the surviving barrel (27.500, 113.900), 1.208 mm")

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(BRD)
print("removed %d, added 1, refilled -> %s" % (removed, BRD))
