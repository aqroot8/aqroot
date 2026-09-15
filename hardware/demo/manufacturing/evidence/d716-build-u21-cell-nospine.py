r"""D-714 -- build the U21 accessory-boost cell candidate base from the authority.

THE ACCESSORY 5 V BOOST IS DEAD ON THE AUTHORITY.  `/01_POWER_TREE/ACC_5V_LX`
(U21.5 -> L4.2) has never routed and `/01_POWER_TREE/BQ25185_SYS`'s
{L4.1, U21.3} island has no supply, so the TPS61023 has neither its inductor
nor its input rail.  D-679/D-680/D-681 measured the LX wall end to end and
named the remaining move: the cell.  This is the cell, in FOUR edits, and the
third one is the one nobody had made.

  0. U21.6's OWN 0.250 mm RAW NECK IS THE FOURTH WALL.  It runs east at
     y = 40.400, so its copper stops at y = 40.275 and `/01_POWER_TREE/ACC_5V_LX`
     -- netclass SWITCH_NODE, track clearance 0.300 mm -- cannot put a 0.200 mm
     necked escape down U21.5's spine at y = 39.900 beside it: 0.275 mm of gap
     against 0.300 mm of rule.  Measured both ways on the same base: with the
     neck present `U21.5` is NO_LEGAL_ESCAPE_DST, without it the switch node
     routes in 3.412 mm with ZERO vias.  It comes out and the run re-lays it.
  1. C65 (22 uF ACC_5V_RAW output cap) sits 0.7345 mm due east of U21's east
     pad row, and `screen_fanout_channel` says U21.5's channel PINCHES TO ZERO
     at 0.75 mm on C65.1's own land.  C65 moves to (60.700, 42.200) -- D-681's
     measured site -- and the two RAW segments that ended on its old land come
     out.  The 0.6/0.3 GND stitch barrel at (62.000, 41.700) would otherwise
     land INSIDE C65.2, so it comes out too; the B.Cu GND pour and five more
     barrels within 1.5 mm already hold that copper.
  2. U21.4's east GND escape -- a DUPLICATE PAIR of 0.300 mm B.Cu tracks
     (58.700,39.375)->(60.600,38.425), 4.2485 mm, plus the 0.1 mm stub pair
     that continues it -- fences U21.5 off from L4.2 to the south.
     `screen_inert_copper.py` over 56.5,37.0-64.0,42.5 calls all twenty GND
     chains there INERT.
  3. THE SMALL `BQ25185_SYS` POUR IS WHY U21.4 HAS NO GROUND.  It is a plain
     rectangle (55,33)-(60,42) that blankets U21 on BOTH sides, and D-710
     already measured this shape once: a FOREIGN POUR starves a pad of its own
     plane.  With edit 2 alone GND loses U21.4 and the board gains an open
     edge.  Trimming the rectangle's east edge from x = 60.000 to x = 58.600
     lets the B.Cu GND pour reach U21.4's land, and `L4.1 <-> U21.3` stays ONE
     island -- measured at 58.0, 58.4 and 58.9; at 59.3 GND opens again.
     The pour serves exactly two lands, `L4.1` and `U21.3`, both west of 58.3.

Usage:  python3 evidence/d714-build-u21-cell.py <SRC_PROJECT_DIR> <DEST_DIR>
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_prl"):
    shutil.copy(SRC / ("aqroot-Beta-v2" + suf), DST / ("aqroot-Beta-v2" + suf))
BRD = DST / "aqroot-Beta-v2.kicad_pcb"


def ends(t):
    return {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)}


# ---- 1a. the two RAW segments that END on C65.1's old land -----------------
# The rest of the chain -- (61.050,39.500)->(60.975,39.425)->(60.950,39.425)
# and the 0.9/0.4 ACC_5V_RAW barrel it lands in -- SURVIVES, because that
# barrel is what carries the rail to In3 and on to TP28/U22/C66.  Releasing it
# with the move orphans the barrel and real DRC returns `via_dangling`.
b = pcbnew.LoadBoard(str(BRD))
WANT = [
    ({(58512500, 40400000), (59022500, 40400000)},
     "ACC_5V_RAW U21.6's own 0.250 mm neck"),
    ({(59022500, 40400000), (60085000, 40475000)}, "ACC_5V_RAW U21.6 -> C65.1"),
    ({(60085000, 40475000), (61050000, 39500000)}, "ACC_5V_RAW C65.1 -> barrel"),
    ({(58700000, 39375000), (60600000, 38425000)}, "GND U21.4 east escape"),
    ({(60600000, 38425000), (60700000, 38425000)}, "GND U21.4 east escape stub"),
]
for want, why in WANT:
    doomed = [t for t in b.GetTracks()
              if t.Type() != pcbnew.PCB_VIA_T and ends(t) == want]
    assert doomed, why
    for t in doomed:
        b.RemoveNative(t)
    print("  -%d  %s" % (len(doomed), why))
b.Save(str(BRD))

# ---- 1b. C65 moves, and the GND barrel that its new land would swallow -----
r = subprocess.run(
    [sys.executable, str(HERE.parent / "apply_part_shift.py"),
     "--board", str(BRD), "--ref", "C65",
     "--dx-nm", "-335000", "--dy-nm", "1725000",
     "--release", "--release-net", "GND",
     "--release-via", "GND:62.0,41.7", "--allow-via-in-pad",
     "--apply", "--report", str(DST / "shift-c65.json")],
    capture_output=True, text=True)
assert r.returncode == 0, r.stdout + r.stderr
print("  C65 -> (60.700, 42.200)")

# ---- 4. U21.4's GROUND SPINE, NORTH THROUGH L4's OWN PAD GAP --------------
# THIS IS THE EDIT THAT DOES NOT YET HOLD, AND IT IS THE WHOLE RESIDUAL.
# On this base the spine works: GND has ZERO open edges and real KiCad DRC is
# the inherited baseline exactly (199 lib_footprint + 1 solder_mask_bridge).
# It does NOT survive the LX route.  The 3.065 mm switch node the run lays
# climbs at x = 59.675 and the refill then cuts the L4-gap strip
# (x 58.15..59.34, y 34.26..39.47) off the eastern GND body, leaving `U21.4` an
# island of one -- D-681's topological finding restated: U21.4 is the NORTH pad
# of the east column, U21.5 the MIDDLE, and whatever the middle pin does after
# it leaves divides north from south.  Three exits from that strip were
# measured and all three are sealed:
#   SOUTH  R48's own via-in-pad, the 0.600/0.300 `/09_COMMUNITY_HEADER/
#          EXT_SDA_BUF` barrel at (58.700, 34.000), sits in L4's pad gap and
#          leaves 0.195 mm west of it and 0.595 mm east -- and 0.595 mm holds
#          only a 0.150 mm conductor, which prices at 0.602 A against a
#          converter ground return.
#   EAST   is the LX route itself.
#   WEST   is this pour and L4.1's own land.
#   A BARREL fits nowhere: a 0.500/0.250 through via was tried at
#          (58.800, 37.000) and (58.800, 37.200) and real DRC returned a
#          clearance failure against `/09_COMMUNITY_HEADER/ACC_DETECT_N_HDR` on
#          F.Cu both times; at (58.850, 38.950) it SHORTS `/XGPIO4` on In2 and
#          clears `/01_POWER_TREE/ACC_5V_RAW` on In3 by 0.0793 mm.  Four layers
#          cross this footprint and every one of them is occupied.
# D-681: "U21.4's ONLY pour path is the EAST corridor, and U21.5 sits directly
# SOUTH of it while L4.2 is NORTH-EAST of both -- so the switch node and the
# ground both go east then north and CROSS wherever they are drawn.
# Topological, not a search result."  That is still true with the cell opened:
# the 3.412 mm LX route measured on this base runs (59.225,39.900) ->
# (59.650,39.500) -> (59.175,38.825) -> (60.250,37.775) and the refill then
# leaves `U21.4` an island of one.  The honest answer to a converter's ground
# pin is not a pour corridor, it is a BARREL: U21.4 gets a 0.600/0.300 through
# via at (58.850, 38.950), down to the In1/In4 GND planes, 0.591 mm from its
# own land, with a two-step stub that clears U21.5 by 0.247 mm and R64's F.Cu
# lands by 0.249 mm.  The 0.200 mm first step is the width the board's own
# "Pad-escape necking - width, fine-pitch power packages" rule already grants
# inside U21's courtyard.
b = pcbnew.LoadBoard(str(BRD))
gnd = b.FindNet("GND")


def mk_track(net, layer, a, c, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(int(a[0] * 1e6), int(a[1] * 1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(c[0] * 1e6), int(c[1] * 1e6)))
    t.SetWidth(int(w))
    t.SetLayer(b.GetLayerID(layer))
    t.SetNet(net)
    b.Add(t)
    print("  +TRK %-4s %-6s (%.3f,%.3f)->(%.3f,%.3f) %.3f mm"
          % (net.GetNetname(), layer, a[0], a[1], c[0], c[1], w / 1e6))


#SKIPPED-D716: the spine blocks U21.5s 0.600 mm escape
#mk_track(gnd, "B.Cu", (58.513, 39.400), (58.900, 39.100), 250000)
#mk_track(gnd, "B.Cu", (58.900, 39.100), (58.900, 36.200), 300000)
b.Save(str(BRD))

# ---- 3. the small SYS pour's east edge, 60.000 -> 58.600 -------------------
b = pcbnew.LoadBoard(str(BRD))
n = 0
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() != "/01_POWER_TREE/BQ25185_SYS":
        continue
    if z.GetBoundingBox().GetTop() / 1e6 > 50:
        continue
    o = z.Outline()
    ch = o.Outline(0)
    pts = [(min(ch.CPoint(i).x, 58600000), ch.CPoint(i).y)
           for i in range(ch.PointCount())]
    o.RemoveAllContours()
    o.NewOutline()
    for (x, y) in pts:
        o.Append(x, y)
    n += 1
assert n == 1, n
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BRD))
print("  SYS POUR 2 east edge 60.000 -> 58.600, refilled")
print("wrote", BRD)
