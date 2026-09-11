"""D-690: publish the two BQ25185 charge-status signals' width floor BEFORE the
router runs."""
from pathlib import Path

DRU = Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/"
           "aqroot-Beta-v2.kicad_dru")
ADD = '''

# =====================================================================
# SECTION 19 - D-690: THE TWO `BQ25185` CHARGE-STATUS SIGNALS PUBLISH A
#              WIDTH FLOOR OF THEIR OWN, AND IT IS THE BOARD'S OWN
#              `min_track_width`
#
# `/BQ25185_STAT1` and `/BQ25185_STAT2` are the charger's two OPEN-DRAIN
# charge-status outputs.  Each runs from the `BQ25185`'s WSON -- `U11.9`
# and `U11.3` -- to a pull-up (`R127` / `R128`), a test point
# (`TP6` / `TP7`) and one pin of the `PCAL9535A` I2C expander `U2`
# (`U2.9` / `U2.10`).  Between them they hold FOUR of the board's
# nineteen remaining open edges, and D-165/D-166 record that this
# telemetry is the reason `U2` keeps those two pins at all.
#
# THE WALL IS A VENDOR LAND PATTERN AND EXACTLY ZERO MICRONS OF MARGIN.
# `screen_fanout_channel.py` walked both lands outward in 25 um stations
# (`evidence/d690-stat-fanout-channels.json`):
#
#   U11.9   at 0.00 mm  gap 0.600 mm (U11.8 <-> U11.10)  admits 0.200 mm
#           at 0.25 mm  gap 1.975 mm                     admits 1.575 mm
#   U11.3   at 0.00 mm  gap 0.600 mm (U11.4 <-> U11.2)   admits 0.200 mm
#           at 0.25 mm  gap 5.975 mm                     admits 5.575 mm
#
# The channel is WIDE OPEN a quarter of a millimetre out.  At the land
# row itself the `BQ25185`'s 0.4 mm-pitch WSON leaves 0.600 mm between
# neighbouring lands, and a 0.200 mm track at this board's 0.200 mm
# routed clearance needs 0.600 mm -- it fits, with ZERO margin, and no
# rasterised lattice can ever express zero: `QBoard.grid`'s guard band
# is 0.75 of a cell, so the launch is refused at 0.100 mm, at 0.050 mm,
# at 0.025 mm and at every finer pitch alike.  A 0.150 mm track needs
# 0.550 mm and has 0.050 mm of real margin.
#
# WHY A RULE AND NOT A DEFAULT.  Section 5 prices nine RAILS by
# netclass, because for a rail a width IS an ampacity.  A signal class
# is priced nowhere, and letting the router descend to board setup's
# `min_track_width` for ANY unpriced class would be wrong and
# measurably so: it would admit `GND`, which section 5 deliberately does
# not price (D-643) and which carries every return on this board, and
# `USB_D`, whose width is an IMPEDANCE and not an ampacity at all.  So
# the floor is published for ONE NAMED NET at a time, here, where a
# reviewer reads it -- and `route_maze_batch.net_width_licence` accepts
# only the exact `A.NetName == '<net>'` condition below, so broadening
# this text can never silently broaden the router.
#
# THE FIGURE IS THE BOARD'S OWN AND IS NOT NEW.  0.150 mm is
# `board.design_settings.rules.min_track_width` in
# `aqroot-Beta-v2.kicad_pro`; `audit_narrow_copper.py` has ALWAYS taken
# `max(BOARD_TRACK_MIN, DRU_CLASS[cls].width)` as the floor below which
# a promoted track owes a rule-area licence, so a 0.150 mm `Default`
# track is ORDINARY COPPER on this board and owes none; and the board
# already carries EIGHTY-FOUR tracks at 0.150 mm.  JLCPCB's published
# 4-layer-and-up minimum is 0.127 mm (5 mil) at 1 oz.  Nothing here asks
# the fabricator for anything it is not already making.
#
# CURRENT, MEASURED.  These are open-drain STATUS outputs pulled up
# through `R127` / `R128`; the conductor carries the pull-up current and
# the expander's input leakage, which is microamps.  IPC-2221B at 10 K
# on this board's 1 oz outer copper gives 0.150 mm = 0.602 A -- three
# orders of magnitude of margin -- and section 5 publishes no design
# current for either net, so there is no bar for this width to fail.
# `leaf_land_contract.py` types both lands as signal, not as a supply
# port.
#
# SCOPE.  Two nets, named individually.  No netclass moves, no clearance
# is weakened, and the 0.200 mm routed clearance every other rule on
# this board states is untouched -- the narrow rung buys its margin out
# of the TRACK, never out of the gap.
# ---------------------------------------------------------------------

(rule "D-690 BQ25185_STAT1 charge-status signal - width floor"
\t(constraint track_width (min 0.15mm))
\t(condition "A.NetName == '/BQ25185_STAT1'"))

(rule "D-690 BQ25185_STAT2 charge-status signal - width floor"
\t(constraint track_width (min 0.15mm))
\t(condition "A.NetName == '/BQ25185_STAT2'"))
'''

s = DRU.read_text(encoding="utf-8")
if "D-690 BQ25185_STAT1" in s:
    raise SystemExit("already authored")
DRU.write_text(s.rstrip("\n") + "\n" + ADD, encoding="utf-8")
print("authored the two D-690 width floors")
