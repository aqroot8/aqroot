#!/usr/bin/env python3
"""D-719 step 3 -- the block's three SIGNAL nets, laid by hand.

`Net-(U12-PG)` and `Net-(SW9-A)` both leave U12's SOUTH row into the 4.7 mm
band the `SYS` pour now occupies, so BOTH cross it on **In2**: a B.Cu stub off
the land, one barrel, and the crossing is under the pour instead of through it.
PG takes the SOUTH lane and EN the NORTH one -- R41 (PG) sits south of R43 (EN)
in the east cluster precisely so the two In2 lanes do not have to swap sides.

`/BQ25185_STAT1` lost the B.Cu detour that TP6 stood in; it is re-laid on F.Cu
down the empty east step, with one barrel at (75.600,88.500) picking TP6 up.
"""
import sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent
BRD = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "cand1/aqroot-Beta-v2.kicad_pcb"

PG = "Net-(U12-PG)"
EN = "Net-(SW9-A)"
S1 = "/BQ25185_STAT1"

TRACKS = [
    # ---- PG: U12.14 -> In2 south lane -> R41.2 -> TP8.1 -------------------
    (PG, 68.100, 99.000, 68.100, 99.650, 0.200, "B.Cu"),
    (PG, 68.100, 99.650, 71.500, 102.400, 0.200, "In2.Cu"),
    (PG, 71.500, 102.400, 72.175, 102.600, 0.200, "B.Cu"),
    (PG, 72.175, 102.600, 72.100, 101.800, 0.200, "B.Cu"),
    (PG, 72.100, 101.800, 75.400, 101.800, 0.200, "B.Cu"),
    # ---- EN east branch: U12.12 -> In2 north lane -> R43.1 ----------------
    (EN, 69.100, 99.000, 69.100, 99.650, 0.200, "B.Cu"),
    (EN, 69.100, 99.650, 71.700, 100.500, 0.200, "In2.Cu"),
    (EN, 71.700, 100.500, 72.175, 100.900, 0.200, "B.Cu"),
    # ---- STAT1: re-laid down the empty east step, TP6 picked up ----------
    (S1, 71.300, 99.700, 74.500, 99.000, 0.200, "F.Cu"),
    (S1, 74.500, 99.000, 75.600, 88.500, 0.200, "F.Cu"),
    (S1, 75.600, 88.500, 76.400, 85.525, 0.200, "F.Cu"),
    (S1, 75.600, 88.500, 75.000, 88.000, 0.200, "B.Cu"),
]

VIAS = [
    (PG, 68.100, 99.650, 0.600, 0.300),
    (PG, 71.500, 102.400, 0.600, 0.300),
    (EN, 69.100, 99.650, 0.600, 0.300),
    (EN, 71.700, 100.500, 0.600, 0.300),
    (S1, 75.600, 88.500, 0.600, 0.300),
]

b = pcbnew.LoadBoard(str(BRD))
LAYER = {"B.Cu": pcbnew.B_Cu, "F.Cu": pcbnew.F_Cu, "In2.Cu": pcbnew.In2_Cu,
         "In3.Cu": pcbnew.In3_Cu}
for net, x0, y0, x1, y1, w, lay in TRACKS:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(int(x0 * 1e6), int(y0 * 1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(x1 * 1e6), int(y1 * 1e6)))
    t.SetWidth(int(w * 1e6)); t.SetLayer(LAYER[lay]); t.SetNet(b.FindNet(net))
    b.Add(t)
for net, x, y, dia, drill in VIAS:
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(int(x * 1e6), int(y * 1e6)))
    v.SetWidth(int(dia * 1e6)); v.SetDrill(int(drill * 1e6))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(b.FindNet(net)); b.Add(v)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BRD))
print("  +%d tracks, +%d vias, refilled" % (len(TRACKS), len(VIAS)))

# ---- EN's WEST branch, added after the maze run was measured ---------------
# `--partial` closed it in 14.5 mm of B.Cu straight through the SYS pour's west
# passage and `pour_partition` refused; and it also routed a DNP island (R68).
# This is the same join drawn deliberately.  It leaves U12.12 at y 100.250 --
# 0.95 mm below the pad row, ABOVE everything else in the band -- so the pour
# keeps the whole 3.6 mm strip south of it AND the VIN pocket stays open to the
# east, where C28.1 is.  Then down the pour's own western margin to TP13.
WEST = [
    (EN, 69.100, 99.650, 69.300, 100.250, 0.200, "B.Cu"),
    (EN, 69.300, 100.250, 64.900, 100.250, 0.200, "B.Cu"),
    (EN, 64.900, 100.250, 64.900, 93.000, 0.200, "B.Cu"),
    (EN, 64.900, 93.000, 65.500, 93.000, 0.200, "B.Cu"),
]
b = pcbnew.LoadBoard(str(BRD))
for net, x0, y0, x1, y1, w, lay in WEST:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(int(x0 * 1e6), int(y0 * 1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(x1 * 1e6), int(y1 * 1e6)))
    t.SetWidth(int(w * 1e6)); t.SetLayer(LAYER[lay]); t.SetNet(b.FindNet(net))
    b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BRD))
# THE FILL IS RUN TO ITS FIXED POINT.  fab_package_contract FAB2 refills and
# compares, so a board saved one fill short of convergence ships a stored fill
# the gate never inspected.  Measured: the second pass changes the file, the
# third does not.
b = pcbnew.LoadBoard(str(BRD))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BRD))
print("  +%d EN west-branch tracks, refilled to the fixed point" % len(WEST))
