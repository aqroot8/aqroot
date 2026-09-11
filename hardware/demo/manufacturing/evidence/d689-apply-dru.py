"""D-689: author the two ISLAND_JOIN licences BEFORE the router runs."""
from pathlib import Path

DRU = Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/"
           "aqroot-Beta-v2.kicad_dru")
ANCHOR = '''(rule "D-649 GND U9.16 NFC driver-ground pour bridge - drill"
\t(constraint hole_size (min 0.20mm) (opt 0.20mm))
\t(condition "A.NetName == 'GND' && A.enclosedByArea('POUR_BRIDGE_U9_16')"))
'''
ADD = '''

# ---------------------------------------------------------------------
# 11c. THE ISLAND JUMPER - BQ25185_SYS, SW9's OWN CLUSTER TO THE BODY
#      (D-689)
#
# `/01_POWER_TREE/BQ25185_SYS` is delivered by a POUR, and that pour is
# in seven pieces.  `SW9.2` - the slide switch pole that is the SOURCE
# of the whole rail - sits with `C28.1` and `U12.1` on a piece of its
# own, and the 78.8 mm2 BODY that carries `C24.1`, `C33.1`, `C64.1` and
# `L2.1` is NOT FED BY ANYTHING.  One lateral jumper between those two
# pieces of filled copper closes that, and section 11's three bridges
# cannot: a bridge is a barrel dropped straight down INSIDE one island
# over another cluster's copper, and these two islands overlap nowhere.
#
# THE WALL IS THE BARREL, NOT THE TRACK, AND IT WAS MEASURED TWICE.
# D-688 ran `maze3d.join_islands` read-only down a width ladder and
# found the corridor exists at 0.400 mm and not at the class's own
# 0.500 mm - then found the same corridor OPEN at 0.500 mm the moment
# the barrel changed.  D-689 swept the barrel and the width together,
# twelve read-only runs at a 0.025 mm lattice
# (`evidence/d689-sys-island-jumper.json`), and the frontier is exact:
#
#   width 0.500 mm   0.55/0.30 JOIN   0.60/0.25 JOIN   0.60/0.30 JOIN
#                    0.65/0.25 JOIN   0.65/0.30 JOIN   0.70/0.30 NO
#   width 0.600 mm   0.65/0.25 JOIN   0.65/0.30 JOIN   <-- LARGEST
#   width 0.650 mm   0.65/0.30 NO
#   width 0.700 mm   0.65/0.25 NO     0.65/0.30 NO
#   width 0.800 mm   0.65/0.25 NO     (and D-687: 0.65/0.40 NO)
#
# THE RULE STATES THE LARGEST GEOMETRY THAT FITS, which is section 11's
# own doctrine and not the smallest the fabricator can make.  The
# transaction lays 0.600 mm of track - a width `(rule "SYS_MAIN minimum
# width")` itself publishes as legal, `min 0.50mm`, so NO width licence
# is asked for or granted here - through two 0.650 / 0.300 mm barrels.
# ONE number needs an exception and only one: the 0.300 mm drill,
# against section 8's `POWER-class vias use the 0.40 mm drill`.  The
# 0.650 mm diameter is over board setup's `min_via_diameter` of
# 0.500 mm and the 0.175 mm annular ring is over the unconditional
# 0.125 mm floor, so both are stated below at the value actually laid
# rather than relaxed.
#
# NO NEW FAB CAPABILITY.  A 0.30 mm drill in a 0.65 mm pad is COARSER
# than the 0.20 mm process this file already licenses by name in nine
# places (D-257 escape vias, D-266 Kelvin reservations, D-531 USB-C
# VBUS POFV, D-595 `POUR_BRIDGE_C63_2` and `POUR_BRIDGE_U11_11`, D-632
# `U4.12`, D-649 `POUR_BRIDGE_U9_16`), and D-595 already licenses a
# 0.30 mm drill by name for `POUR_BRIDGE_R19_1`.  What is new is only
# WHERE it is used, and only for the one net the rules name.
#
# CURRENT, MEASURED, AND IT IS THE WHOLE POINT OF TAKING THE LARGEST
# RUNG.  IPC-2221B, 10 K rise, this board's 1 oz outer copper and
# JLCPCB's 0.025 mm plated wall - the same `audit_bond_ampacity` call
# `PP2` and `--trunk-floor` use:
#
#   track  0.600 mm            0.02088 mm2   1.645 A
#   barrel 0.300 mm drill      0.02553 mm2   1.902 A
#   in SERIES, the conductor is worth the smaller:  1.645 A
#
# against the **1.0 A** the `SYS_MAIN` row of section 5 publishes as
# this class's design current - 64 % of margin.  End to end the jumper
# is about 4.3 mOhm of track plus about 1.1 mOhm per barrel, so about
# 6.4 mOhm and about 6 mV at 1.0 A.
#
# AND THE 2.19 A FIGURE IN THE `SYS_MAIN` ROW IS NOT THIS SEGMENT'S.
# Section 5 records a LOCAL EXCEPTION: the `U21` accessory boost draws
# a 2.19 A peak inductor current, so *the SYS segment that feeds U21*
# must be sized from that peak.  `U21.3` is on `POUR 2` with `L4.1` and
# is one of this net's still-OPEN clusters - there is no such segment
# on this board yet, and this jumper is not it.  It joins `SW9.2`'s
# cluster to the body.  When the `U21` feed is eventually built it owes
# that 2.19 A on its own copper, and NOTHING ON THIS BOARD MEETS IT
# TODAY: `SYS_MAIN`'s own 0.800 mm `opt` carries 2.026 A.  That is an
# OPEN width finding on one segment, recorded in `CURRENT_STATE.md`,
# and it is not closed, weakened or inherited by this rule.
#
# Scoped, as every rule in section 11 is, to ONE net and ONE pad-sized
# rule area per barrel, drawn by the promoting transaction around the
# barrel it actually laid and audited by that transaction's clause 6.
# The two areas are named for the CLUSTER and the barrel's ORDINAL
# along the jumper - `C28.1` is the orphan's own first pad - so the
# rule text could be authored, reviewed and committed BEFORE the router
# chose a coordinate, and a jumper that turns out to want a THIRD
# barrel is refused rather than licensed by accident.
# ---------------------------------------------------------------------

(rule "D-689 BQ25185_SYS island jumper barrel 1 - barrel diameter"
\t(constraint via_diameter (min 0.65mm) (opt 0.65mm))
\t(condition "A.NetName == '/01_POWER_TREE/BQ25185_SYS' && A.enclosedByArea('ISLAND_JOIN_C28_1_1')"))

(rule "D-689 BQ25185_SYS island jumper barrel 1 - annular ring"
\t(constraint annular_width (min 0.175mm))
\t(condition "A.NetName == '/01_POWER_TREE/BQ25185_SYS' && A.enclosedByArea('ISLAND_JOIN_C28_1_1')"))

(rule "D-689 BQ25185_SYS island jumper barrel 1 - drill"
\t(constraint hole_size (min 0.30mm) (opt 0.30mm))
\t(condition "A.NetName == '/01_POWER_TREE/BQ25185_SYS' && A.enclosedByArea('ISLAND_JOIN_C28_1_1')"))

(rule "D-689 BQ25185_SYS island jumper barrel 2 - barrel diameter"
\t(constraint via_diameter (min 0.65mm) (opt 0.65mm))
\t(condition "A.NetName == '/01_POWER_TREE/BQ25185_SYS' && A.enclosedByArea('ISLAND_JOIN_C28_1_2')"))

(rule "D-689 BQ25185_SYS island jumper barrel 2 - annular ring"
\t(constraint annular_width (min 0.175mm))
\t(condition "A.NetName == '/01_POWER_TREE/BQ25185_SYS' && A.enclosedByArea('ISLAND_JOIN_C28_1_2')"))

(rule "D-689 BQ25185_SYS island jumper barrel 2 - drill"
\t(constraint hole_size (min 0.30mm) (opt 0.30mm))
\t(condition "A.NetName == '/01_POWER_TREE/BQ25185_SYS' && A.enclosedByArea('ISLAND_JOIN_C28_1_2')"))
'''

s = DRU.read_text(encoding="utf-8")
if "ISLAND_JOIN_C28_1_1" in s:
    raise SystemExit("already authored")
if ANCHOR not in s:
    raise SystemExit("anchor not found")
DRU.write_text(s.replace(ANCHOR, ANCHOR + ADD, 1), encoding="utf-8")
print("authored ISLAND_JOIN_C28_1_1 and ISLAND_JOIN_C28_1_2")
