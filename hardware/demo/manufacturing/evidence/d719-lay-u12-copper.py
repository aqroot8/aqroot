#!/usr/bin/env python3
"""D-719 step 2 -- the converter block's own power copper, laid by hand.

The switch node, the output path, the feedback node and the thermal/return
barrels are the four things a switching-converter layout is judged on, so they
are drawn explicitly rather than left to a maze router:

  SWITCH NODE   one 0.600 mm stub per side, ~2.2 mm each, from the shared
                launch point that covers BOTH pads of each pair (they are the
                same net, so the 0.26 mm inter-pad gap costs nothing) east into
                L1's rotated terminals.  13 mm -> 2.2 mm.
  OUTPUT        one 0.800 mm track that covers BOTH VOUT pads and lands in
                C31.1, then 0.600 mm on to C32.1, with two 0.800/0.400 P3V3
                barrels to the In3/F planes.
  FEEDBACK      U12.3 -> R39.2 -> R40.1 in 6.1 mm down the 0.925 mm corridor
                between R39's lands and C31's, instead of 28 mm on In2/In3.
  RETURN        four 0.600/0.300 barrels on stubs off the PGND thermal pad,
                plus U12.2 and U12.13 tied into it, plus one barrel per moved
                bypass/bias land.
"""
import json, sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent
BRD = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "cand1/aqroot-Beta-v2.kicad_pcb"

L1P1 = "Net-(L1-Pad1)"
L1P2 = "Net-(L1-Pad2)"
FB = "/01_POWER_TREE/V3V3_FB"

TRACKS = [
    # net,  x0,      y0,      x1,      y1,      width, layer
    (L1P2, 70.850, 96.200, 73.000, 96.415, 0.600, "B.Cu"),
    (L1P2, 70.650, 96.200, 70.850, 96.200, 0.400, "B.Cu"),
    (L1P2, 71.050, 96.200, 70.850, 96.200, 0.400, "B.Cu"),
    (L1P1, 70.850, 99.000, 73.000, 98.785, 0.600, "B.Cu"),
    (L1P1, 70.650, 99.000, 70.850, 99.000, 0.400, "B.Cu"),
    (L1P1, 71.050, 99.000, 70.850, 99.000, 0.400, "B.Cu"),

    # The 0.800 mm VOUT trunk covers BOTH pads; the two 0.400 mm spurs give
    # each land an ENDPOINT of its own, which is what placement PL8 measures.
    ("+3V3", 69.850, 96.200, 69.850, 95.000, 0.800, "B.Cu"),
    ("+3V3", 69.650, 96.200, 69.850, 96.200, 0.400, "B.Cu"),
    ("+3V3", 70.050, 96.200, 69.850, 96.200, 0.400, "B.Cu"),
    ("+3V3", 70.000, 94.625, 72.000, 94.200, 0.600, "B.Cu"),
    ("+3V3", 69.300, 93.400, 69.300, 94.400, 0.600, "B.Cu"),
    ("+3V3", 74.000, 94.075, 73.100, 94.075, 0.600, "B.Cu"),
    ("+3V3", 66.300, 94.725, 67.100, 94.725, 0.400, "B.Cu"),
    ("+3V3", 74.800, 103.000, 74.100, 102.800, 0.400, "B.Cu"),

    (FB, 69.100, 96.200, 69.100, 95.600, 0.200, "B.Cu"),
    (FB, 69.100, 95.600, 68.300, 95.600, 0.200, "B.Cu"),
    (FB, 68.300, 95.600, 68.300, 93.300, 0.200, "B.Cu"),
    (FB, 68.300, 93.300, 67.500, 93.075, 0.200, "B.Cu"),
    (FB, 67.400, 93.075, 67.900, 91.600, 0.200, "B.Cu"),
    (FB, 67.900, 91.600, 68.400, 90.100, 0.200, "B.Cu"),

    # the WEST thermal barrels stop at y 97.6: a third rung at 96.9 sealed
    # the pocket that feeds U12.1 (VINA) off the SYS pour.
    ("GND", 66.800, 97.600, 68.300, 97.600, 0.300, "B.Cu"),
    ("GND", 66.800, 98.300, 68.300, 98.300, 0.300, "B.Cu"),
    ("GND", 71.800, 97.300, 71.000, 97.300, 0.300, "B.Cu"),
    ("GND", 71.800, 97.900, 71.000, 97.900, 0.300, "B.Cu"),
    ("GND", 68.600, 96.200, 68.600, 96.900, 0.300, "B.Cu"),
    ("GND", 68.600, 99.000, 68.600, 98.300, 0.300, "B.Cu"),
    ("GND", 70.100, 103.300, 70.100, 102.400, 0.300, "B.Cu"),
    ("GND", 68.600, 92.700, 69.100, 91.900, 0.300, "B.Cu"),
    ("GND", 73.800, 91.125, 73.200, 91.125, 0.300, "B.Cu"),
    ("GND", 69.500, 88.375, 68.700, 88.375, 0.300, "B.Cu"),
    ("GND", 74.900, 100.600, 74.200, 100.900, 0.300, "B.Cu"),
]

VIAS = [
    # net,   x,      y,      dia,   drill
    ("+3V3", 69.300, 93.400, 0.800, 0.400),
    ("+3V3", 74.000, 94.075, 0.800, 0.400),
    ("+3V3", 66.300, 94.725, 0.800, 0.400),
    ("+3V3", 74.800, 103.000, 0.800, 0.400),
    # SW2.2's replacement ground barrel, inside its own F.Cu land.
    ("GND", 68.600, 101.250, 0.600, 0.300),
    ("GND", 66.800, 97.600, 0.600, 0.300),
    ("GND", 66.800, 98.300, 0.600, 0.300),
    ("GND", 71.800, 97.300, 0.600, 0.300),
    ("GND", 71.800, 97.900, 0.600, 0.300),
    ("GND", 70.100, 103.300, 0.600, 0.300),
    ("GND", 68.600, 92.700, 0.600, 0.300),
    ("GND", 73.800, 91.125, 0.600, 0.300),
    ("GND", 69.500, 88.375, 0.600, 0.300),
    ("GND", 74.900, 100.600, 0.600, 0.300),
]

b = pcbnew.LoadBoard(str(BRD))
LAYER = {"B.Cu": pcbnew.B_Cu, "F.Cu": pcbnew.F_Cu, "In2.Cu": pcbnew.In2_Cu,
         "In3.Cu": pcbnew.In3_Cu}
for net, x0, y0, x1, y1, w, lay in TRACKS:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(int(x0 * 1e6), int(y0 * 1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(x1 * 1e6), int(y1 * 1e6)))
    t.SetWidth(int(w * 1e6))
    t.SetLayer(LAYER[lay])
    t.SetNet(b.FindNet(net))
    b.Add(t)
for net, x, y, dia, drill in VIAS:
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(int(x * 1e6), int(y * 1e6)))
    v.SetWidth(int(dia * 1e6))
    v.SetDrill(int(drill * 1e6))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(b.FindNet(net))
    b.Add(v)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BRD))
print("  +%d tracks, +%d vias, refilled" % (len(TRACKS), len(VIAS)))
