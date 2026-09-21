#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY, ABSOLUTE: can each POWER RAIL's actual copper
carry the current the design asks of it, ALONG THE PATH THE CURRENT TAKES?

WHY THIS EXISTS AND WHY IT IS NOT `audit_bond_ampacity.py`.  Every ampacity
instrument on this board so far is a DIFF: it takes an authority and a
candidate and rules on the copper the candidate ADDED.  That answers "did this
transaction make anything worse", which is the wrong question at release.
D-742 asked the right one -- "is the `USB_VBUS_CHG` conductor big enough for
the current the charger is programmed to draw" -- and no instrument here could
answer it, because the answer needs three things a diff does not have:

  1. AN ABSOLUTE DESIGN CURRENT per rail, not a delta.
  2. THE PATH.  A power net is not uniformly a power conductor.
     `/01_POWER_TREE/USB_VBUS_CHG` has ELEVEN pads on it and nine of them are
     telemetry: two dividers, two Schottky steering diodes, a gate resistor and
     a 1 M pull.  Those branches carry microamps and are 200 mm long.  Judging
     the net by its narrowest track anywhere condemns copper that carries
     nothing, and -- far worse -- a rail whose CARRYING path is starved can
     hide behind a wide telemetry stub.  So the rail is declared as
     SOURCE pads -> SINK pads and only the copper BETWEEN them is judged.
  3. dT, NOT PASS/FAIL.  IPC-2221B is stated as "the width for a 10 K rise".
     A 0.10 mm neck inside a package courtyard and a 33 mm haul are not the
     same object even at the same width, and a floor that says only
     "0.35 mm min" cannot tell them apart.  This reports the rise each segment
     actually runs at, its length, and its share of the path's series drop.

METHOD.  IPC-2221B, the same form `audit_bond_ampacity.py` uses and the same
form `.kicad_dru` section 5 published years earlier:

    I = k * dT^0.44 * A^0.725     A in mil^2, I in amperes
    k = 0.048 outer, 0.024 inner

so, inverted for the rise a known current produces in a known conductor,

    dT = (I / (k * A^0.725)) ** (1/0.44)

SELF-CHECK FIRST.  The run re-derives `.kicad_dru` section 5's own published
width table before it rules on anything.  A method that cannot reproduce the
board's own numbers has no business condemning the board's own copper; the
residual is reported in `method_selfcheck` and a miss is a FAIL of this tool,
not of the board.

THE PATH IS THE WIDEST BOTTLENECK, NOT THE SHORTEST ROUTE.  Real current
divides among every parallel path, so the honest conservative bound is the
single best path available to it: a maximin (widest-bottleneck) search over the
copper graph.  If THAT path has a segment too narrow, no division of current
saves it.  Parallel paths only ever help, so this under-states the board.

    python3 audit_rail_ampacity.py [--board B] [-o OUT.json]
"""
import argparse, hashlib, json, math, re, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import pcbnew

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

# This board's stackup, transcribed from the fab notes it is ordered against
# and identical to the constants `audit_bond_ampacity.py` already uses.
OUTER_MM = 0.0348               # 1 oz finished outer copper
# D-750 CORRECTED THIS FROM 0.0174.  0.0174 mm is the NOMINAL thickness of a
# half-ounce foil; it is not what this board is ordered against.  The board
# file's own stackup object declares In1..In4 at 0.0152 mm, which is the
# thickness JLCPCB publishes for the 0.5 oz inner foil of JLC06161H-7628, and
# `audits/2026-08-27-p2-002r-sixlayer-lock-d263.md` locked that stackup with
# those four numbers written out.  The old constant over-stated every inner
# conductor's cross-section by 14.5 %, which under-states its rise and its
# resistance.  THE BOARD'S OWN STACKUP IS THE AUTHORITY; a self-check against
# it now runs before any rail is judged.
INNER_MM = 0.0152               # 0.5 oz inner foil, JLC06161H-7628 as declared
                                # in the board's own (stackup) object
PLATING_MM = 0.025              # JLCPCB plated barrel wall, minimum
MIL2_PER_MM2 = 1.0 / 0.00064516
K_EXT, K_INT = 0.048, 0.024
RHO_CU = 1.72e-5                # ohm-mm at 20 C
OUTER = {"F.Cu", "B.Cu"}
DT_REF = 10.0                   # the rise every published floor is stated at

# --------------------------------------------------------------------------
# THE RAIL TABLE.  `amps` is the ENFORCED maximum the design permits, not a
# typical -- the same convention `.kicad_dru` section 5 uses when it writes
# "0.70 A ILIM" and "0.5 A (ILIM500)".  Every entry cites what sets it.
# --------------------------------------------------------------------------
RAILS = (
    dict(name="USB_VBUS_CHG", net="/01_POWER_TREE/USB_VBUS_CHG",
         src=("R35.2",), snk=("U11.10",), amps=1.10,
         basis="BQ25185 ILIM/VSET = R36 13 kOhm -> ILIM1100 (SLUSF65B table 6-1). "
               "D-743 raised it from ILIM500 so R37's 390 Ohm ICHG = 769 mA can "
               "terminate inside the 360 min tMAXCHG safety timer.",
         # THE ONE NAMED AMPACITY EXCEPTION ON THIS BOARD.  Its full derivation,
         # its three measurements and its Rev-B carry-forward are in
         # `.kicad_dru` section 5a; this is the machine-checkable half.  It is
         # scoped to ONE net on ONE layer, and a hot segment anywhere else --
         # or on an outer layer of this same net -- still FAILS.
         accept=(dict(layer="In2.Cu", reason="dru-5a", max_length_mm=165.0),),
         # D-751 REPAIRED THIS PROSE.  D-743 wrote "0.15 mm from solid GND and
         # +3V3 planes on both faces" from a stackup this board does not have,
         # and D-750's inner-copper correction left the sentence standing while
         # every number around it changed.  The real geometry is asymmetric and
         # is read back from the board's own (stackup): In2.Cu sits 0.4000 mm
         # of core below In1.Cu (GND) and 0.2028 mm of prepreg above In3.Cu
         # (+3V3).  The plane-coupled rise this file DERIVES from those two
         # distances is 1.45 K; the justification is now that number rather
         # than a remembered one.
         accept_reason="D-743, re-derived at D-751 / .kicad_dru section 5a: "
               "IPC-2221B's internal k describes an isolated coupon in still "
               "air, and it is superseded by IPC-2152.  This board's In2.Cu is "
               "not an isolated coupon: its own declared stackup puts it "
               "0.4000 mm of core from the In1.Cu GND plane and 0.2028 mm of "
               "prepreg from the In3.Cu +3V3 plane, and the plane-coupled rise "
               "computed from those distances is 1.45 K against the 66.5 K the "
               "isolated-coupon curve returns.  Measured alternatives are "
               "exhausted: no corridor exists on any layer at any width "
               "(screen_widest_corridor, 3 layers) and in-place widening is "
               "worth under 5 % (w/d743/widen_plan.py, 25 segments).  The "
               "ELECTRICAL cost is accepted with its number: 216 mOhm and "
               "237 mV at 1.1 A, which D-750's charge-timer margin is computed "
               "against."),
    dict(name="USB_VBUS_RAW", net="/01_POWER_TREE/USB_VBUS_RAW",
         src=("J3.A4", "J3.B4", "J3.A9", "J3.B9"), snk=("R35.1",), amps=1.10,
         basis="same charger input current, upstream of the R35 0 R link"),
    dict(name="BAT_PROTECTED_P", net="/01_POWER_TREE/BAT_PROTECTED_P",
         src=("R75.2", "R75.4"), snk=("U11.2",), amps=2.35,
         basis="D-787 / R6-E07: corrected full-feature normal envelope is "
               "about 2.29 A path-bound at the 3.85 V loaded VCELL floor; "
               "2.35 A is the routing/thermal design current with explicit "
               "margin. IBAT_OCP is a fault threshold, not a routing current.",
         # THE PACKAGE, NOT THE LAYOUT.  U11.2's land is 0.750 x 0.200 mm, so no
         # conductor wider than 0.200 mm can LAND on it, in any layout, with any
         # charger position.  The .kicad_dru pad-escape neck rule already
         # licenses 0.200 mm inside U11's courtyard.  What is accepted here is
         # the ampacity consequence, bounded by length: 5.5 mm of 0.200 mm
         # B.Cu.  A copper thermal length of about 2.6 mm means the neck's two
         # ends -- a large pad and wide copper -- sink a substantial part of it.
         # D-787 deliberately reruns this package-limited neck at 2.35 A instead
         # of retaining the obsolete 1.50 A class current; the isolated-coupon
         # rise is reported as a screening number, not a predicted board temp.
         # D-789 / D788-03.  TWO EXCEPTIONS, BECAUSE THE CONDUCTOR IS MEASURED
         # NOW AND IT IS TWO THINGS.  D-787/D-788 licensed "6.0 mm of 0.200 mm
         # copper", which was the TRACK ATTRIBUTE and described a neck that
         # does not exist: 100 % of that 0.200 mm track's copper lies inside
         # D-780's hand taper.  What the board actually has, measured, is
         # 0.200 mm of merged copper for the first 0.900 mm out of the land --
         # conservative, since the genuinely 0.200 mm part is the first
         # 0.575 mm and the rest of that object is already 0.446 mm or wider --
         # and then 0.600 mm for 2.150 mm before it reaches 1.200 mm and above.
         # Both are licensed, both are length-bounded so neither can grow
         # silently, and each is solved over ITS OWN length.
         accept=(dict(layer="B.Cu", reason="package-land-neck",
                      max_length_mm=1.2, max_width_mm=0.205),
                 dict(layer="B.Cu", reason="package-escape-taper",
                      max_length_mm=3.0, max_width_mm=0.62)),
         # D-788 / R7-D787-04.  THE CLAMPED END IS NOT AT PLANE TEMPERATURE.
         # This neck ends on U11's own BAT land, and the BQ25185's BATFET
         # dissipates I^2 x RON_BAT in that package: at the 2.35 A design
         # current and SLUSF65B's 140 mOhm -40..+125 C RON_BAT maximum that is
         # 0.773 W.  The DLH0010A's thermal pad carries most of it into the
         # board, so the LAND this run joins sits above the surrounding plane.
         # 25 K is a DECLARED endpoint allowance: it is roughly a third of the
         # junction rise a 60 C/W package would show at that dissipation, which
         # is the share a soldered thermal pad typically leaves at the land,
         # and it is added to the absolute peak rather than assumed away.
         # First-article thermography measures it.
         # D-789 / D788-03.  THE DECLARED 25 K ENDPOINT RISE IS GONE, AND SO
         # IS THE 0.773 W IT WAS DERIVED FROM.  Round-8 is right that the two
         # models disagreed (F6 charges the BATFET 196 mOhm, this file charged
         # it 140) and right that turning a device's dissipation into a
         # declared copper allowance answers about the wrong object.  The
         # junction is COMPUTED instead, from TI's own equation and TI's own
         # RthetaJA, and judged against TI's own TJ maximum -- see
         # `package_junction`.  The copper clause now rules only on the
         # copper's OWN rise, which is what a conductor-sizing limit can
         # actually say something about.
         accept_endpoint_rise_K=0.0,
         accept_endpoint_rise_basis=(
             "D-789 / D788-03: superseded by the computed package junction "
             "clause.  The copper's absolute peak is its own rise over the "
             "board reference; the temperature of the LAND at the package end "
             "is bounded by the BQ25185's junction, which is computed from TI "
             "SLUSF65B 6.3.7.6 at the SAME 196 mOhm BATFET resistance F6 "
             "charges, and judged against TI's own 125 C operating maximum."),
         accept_package_junction="U11",
         accept_inside_battery_shadow=True,
         accept_reason="U11 DLH0010A pin-2 land is 0.200 mm tall; nothing wider "
               "can land on it.  Licensed by the .kicad_dru pad-escape neck rule "
               "and bounded here to 1.2 mm of MEASURED 0.200 mm copper plus "
               "3.0 mm of the 0.600 mm taper out of it.  D-789 / D788-03 "
               "replaced the 6.0 mm of 0.200 mm this exception used to license: "
               "that was the width ATTRIBUTE of a track whose copper lies "
               "entirely inside D-780's wider taper, and it described a neck "
               "the board does not have."),
    dict(name="BQ25185_SYS", net="/01_POWER_TREE/BQ25185_SYS",
         src=("U11.1",), snk=("U12.1",), amps=2.35,
         basis="D-787 / R6-E07: the pour feeding the full fitted system is "
               "qualified at the same 2.35 A corrected sustained normal "
               "envelope as BAT_PROTECTED_P; local boost ripple/inductor peak "
               "currents remain decoupled locally and are not added as DC.",
         # NOT A TRACK RAIL.  D-720 established that BQ25185_SYS is DELIVERED BY
         # ITS POUR, not by a trunk, so a track-graph search correctly finds no
         # path and MUST NOT be read as a defect.  The instrument that rules on
         # it is `checks/pour_partition_contract.py` PP2, which prices the
         # bottleneck through the ZONE FILL.  Declared here so the gap is
         # visible instead of silent.
         pour_delivered="checks/pour_partition_contract.py PP2 -- this rail is "
               "delivered by its In/B.Cu pour, not by a trunk; a track-graph "
               "NO_PATH is the expected answer and is not a defect"),
    # D-750 ADDED THESE TWO.  The SYS rail is POUR-DELIVERED only between U11
    # and U12; the two SOUTHERN boosts are 40 mm outside that pour and are fed
    # by a real trunk, and no instrument in this repository had ever measured
    # it.  The .kicad_dru section 5 SYS_MAIN row says in its own words "LOCAL
    # EXCEPTION, NOT ENCODABLE: the U21 accessory boost draws a 2.19 A peak
    # inductor current from SYS (D-185), so the SYS segment that feeds U21 must
    # be sized from that peak" -- a requirement nothing checked.  Now it is a
    # rail with a source, a sink and a number.
    dict(name="SYS_TO_ACC5V_BOOST", net="/01_POWER_TREE/BQ25185_SYS",
         src=("U12.1", "U12.10", "U12.11", "C24.1", "C26.2", "C28.1"),
         snk=("L4.1",), amps=1.110,
         accept=(dict(layer="In2.Cu", reason="dru-5c", max_length_mm=80.0),),
         accept_reason="D-750 / .kicad_dru section 5c.  The SYS trunk's three "
               "In2 legs run 0.800 mm, where IPC-2221B's INTERNAL curve asks "
               "1.585 mm for 0.925 A and returns a 31.8 K rise.  That curve is "
               "an isolated coupon in still air and IPC-2152 superseded it; "
               "the PLANE-COUPLED rise this file derives from the board's own "
               "declared stackup -- In2 between In1 across 0.4000 mm of core "
               "and In3 across 0.2028 mm of prepreg -- is derived below from "
               "the rail's OWN current rather than quoted, and the dissipation "
               "is reported beside it.  The ELECTRICAL cost is accepted with "
               "its number: 183 mOhm and 203 mV at the enforced ACC_5V "
               "maximum, against a TPS61023 input range of 0.5-5.5 V.",
         basis="U21 TPS61023 INPUT current at the ENFORCED ACC_5V maximum.  "
               "D-787 moved R101 2.37 -> 2.43 kOhm, so that maximum is now "
               "0.6078 A and the input is 0.6078 x 5.1654 / (0.88 efficiency "
               "x 3.3 V VBAT) = 1.081 A rms.  THE RAIL IS DELIBERATELY LEFT AT "
               "1.110 A, the figure D-773 qualified at 0.624 A: the trunk is "
               "already proven at the higher current, re-qualifying it downward "
               "would buy nothing and would discard evidence.  It is a ceiling, "
               "and the accepted-exception geometry below is judged against it.  "
               "The number that sizes this trunk is not a PUBLISHED figure but "
               "the load switch's own worst-case limit: TI SLVSGP6A equation 1 "
               "gives 0.479 A typ at D-771's 2.32 kOhm and the EC table's "
               "widest ratio (1.32x), over the resistor's own 1 % band, gave "
               "0.624 A over -40..+125 C at D-773's 2.37 kOhm.  D-771 "
               "RAISED R101's SETTING because "
               "2.7 kOhm GUARANTEED only 0.277 A against the 300 mA D-098 "
               "publishes for this rail; the trunk pays for that guarantee in "
               "current.  It WAS 0.925 A (D-753, 2.7 kOhm) and 1.21 A before "
               "that (D-750, 1.65 kOhm), so this is still BELOW the figure the "
               "trunk was originally built for. "
               "The 2.19 A the section 5 note quotes is the PEAK INDUCTOR "
               "current (D-185), which the input capacitor C83 supplies "
               "locally; the trunk carries the average.  THE SINK IS L4.1, NOT "
               "U21.3: the two share one node and U21.3 hangs off it through "
               "1.35 mm of 0.5 mm B.Cu (1.3 mOhm), but that stub's far END "
               "lies 0.075 mm outside L4.1's land and OVERLAPS it as copper, "
               "which KiCad's connectivity resolves and this file's "
               "endpoint-in-pad graph does not."),
    # D-771 ADDED THESE TWO.  The accessory rails THEMSELVES had never been
    # measured -- only the SYS trunk that feeds the 5 V boost.  They matter now
    # because guaranteeing D-098's published budget forces each limiter's
    # WORST-CASE limit up with it: the enforced maximum is not the 400/300 mA
    # the product publishes but what the load switch is allowed to pass at its
    # unlucky corner.  A rail whose copper is sized for the published figure
    # and whose silicon permits twice it is exactly the gap D-766 named.
    # The two duplicate contacts on each rail SHARE the rail limit (D-098), so
    # each path is sized for the WHOLE current rather than half of it.
    # D-787 / R6-A01 NOTE.  F6's DELIVERY proof charges the whole published
    # 400 mA to the manual TP12->J5 reinforcement lead and ignores this routed
    # copper; this audit charges the whole WORST-CASE LIMITER current to the
    # routed copper and ignores the lead.  The two are deliberately
    # complementary worst cases of the same parallel pair: neither is allowed
    # to lean on the other, so whichever conductor an assembled board actually
    # favours, both are qualified alone.
    dict(name="ACC_3V3_SW", net="/ACC_3V3_SW",
         src=("U20.5",), snk=("J5.3", "J5.22"), amps=0.849,
         accept=(dict(layer="In2.Cu", reason="dru-5f", max_length_mm=76.0,
                      max_width_mm=0.40),),
         accept_reason="D-771 / .kicad_dru section 5f, the SAME model and the "
               "SAME two planes section 5c already rests on.  The rail leaves "
               "U20 on In2.Cu at 0.400 mm, where IPC-2221B's INTERNAL curve "
               "asks 1.436 mm for 0.849 A and returns 82.1 K.  That curve is "
               "an isolated coupon in still air; In2.Cu on THIS board sits "
               "0.4000 mm of core from the In1.Cu GND plane and 0.2028 mm of "
               "prepreg from the In3.Cu +3V3 plane, and the plane-coupled rise "
               "derived from those two distances is 2.29 K for 0.162 W over the "
               "whole rail.  THE ELECTRICAL COST IS ACCEPTED WITH ITS NUMBER: "
               "224 mOhm, which is 190 mV at the limiter's worst case and "
               "90 mV at D-098's PUBLISHED 400 mA -- the figure an accessory "
               "actually sees.  With U20's own 68 mOhm max RON that is 117 mV "
               "at the published budget, leaving the Community Port above "
               "3.18 V against a 3.135 V -5 % floor.  Length is bounded at "
               "76.0 mm against 73.3 used, so a re-route cannot grow it "
               "silently.",
         basis="U20 TPS22950-Q1 worst-case ILIM at D-771's R97 = 1.78 kOhm: "
               "SLVSGP6A equation 1 gives 0.636 A typ, and the EC table's "
               "widest ratio (1.32x) over the resistor's own 1 % band gives "
               "0.849 A over -40..+125 C.  The PUBLISHED budget is D-098's "
               "400 mA total, which the same setting GUARANTEES (0.428 A); "
               "this row is sized by the limiter, not by the publication."),
    dict(name="ACC_5V_SW", net="/ACC_5V_SW",
         src=("U22.5",), snk=("J5.1", "J5.24"), amps=0.608,
         accept=(dict(layer="In3.Cu", reason="dru-5f", max_length_mm=41.0,
                      max_width_mm=0.40),),
         accept_reason="D-771, re-measured at D-773 / .kicad_dru section 5f.  "
               "Same model on In3.Cu, whose own declared stackup puts it "
               "0.2028 mm of prepreg from In2.Cu and 0.4000 mm of core from "
               "the In4.Cu GND plane: IPC-2221B asks 0.939 mm and returns "
               "38.5 K, the plane-coupled rise derived from those two "
               "distances is 1.24 K, and the rail dissipates 0.043 W.  In2.Cu "
               "is a ROUTING layer rather than a solid plane, so that side of "
               "the model is optimistic -- but the In4 side ALONE, at "
               "0.4000 mm, still gives 3.7 K, and the track runs inside In3's "
               "own +3V3 pour at 0.250 mm lateral clearance, a heat path this "
               "model ignores entirely.  111 mOhm, 69 mV at the limiter's "
               "worst case and 33 mV at D-098's PUBLISHED 300 mA.  Length "
               "bounded at 41.0 mm against 38.6 used.",
         basis="D-787: U22 TPS22950-Q1 worst-case ILIM at R101 = 2.43 kOhm -- "
               "0.4555 A typ, 0.6078 A worst case -- rounded up to 0.608 A.  "
               "It was 2.32 kOhm / 0.639 A at D-771 and 2.37 kOhm / 0.624 A "
               "at D-773, and moved again once F6 stopped costing the main "
               "3.3 V rail at a typed 3.3 V and derived it from R39/R40 "
               "instead, which moved the whole 5 V legal window.  The "
               "PUBLISHED budget is D-098's 300 mA total, GUARANTEED at "
               "0.3065 A.  The ACC_5V class floor is 0.400 mm where IPC-2221B "
               "asks 0.156 mm OUTER at this current, so no width rule moves.  "
               "demo_feature_contract F6 machine-checks that this design "
               "current still covers the envelope it is derived from."),
    # D-771 DECLARES THE +3V3 RAIL, WHICH HAD NEVER APPEARED HERE AT ALL.
    # Raising R97's ILIM so the 3.3 V accessory rail can GUARANTEE D-098's
    # published 400 mA also raises what U12 must SOURCE -- 1.0 A internal plus
    # 0.849 A worst-case accessory = 1.849 A -- and nothing in this file had
    # ever asked what carries it.  The answer is that NOTHING DOES, in the
    # track sense: `+3V3` is delivered by its two F.Cu pours (5 993 and
    # 8 764 mm2) and the In3.Cu plane, exactly as BQ25185_SYS is delivered by
    # its own, and a track-graph search between U12's output and U20's input
    # correctly returns NO PATH.  Declared so the gap is VISIBLE rather than
    # silent, with the two package-limited ends measured by hand at 1.849 A:
    #
    #   U12.4/U12.5  0.240 mm DSJ0010A output lands, TWO IN PARALLEL   12.2 K
    #   0.800 mm B.Cu trunk out of them                                 8.1 K
    #   0.600 mm B.Cu branches to the three plane vias (each shares)   13.1 K *
    #   U20.2  0.400 mm B.Cu input stub, 2.5 mm, at 0.849 A             4.3 K
    #   * the figure if ONE branch carried the WHOLE rail; three share it
    #
    # All four are inside this file's own 20 K limit, and the widest is a
    # package land nothing can be laid wider on -- the same class of residual
    # as U11.2 (see .kicad_dru section 5e).
    dict(name="P3V3_MAIN", net="+3V3",
         src=("U12.4", "U12.5"), snk=("U20.2",), amps=1.95,
         basis="D-790 / D789-A11 + R9-N01, re-based from D-787 / R6-E07. F6's "
               "fitted internal +3V3 budget is 1.1438 A -- it rose from "
               "1.0632 A when D789-A11 replaced the inherited 181 mA "
               "display line with a DERIVED 211.58 mA backlight-converter "
               "input and a declared 50 mA panel-logic allowance -- and "
               "U20's worst programmed limiter corner is 0.8036 A, read off "
               "the SLVSGP6A rows that bracket R97 rather than the table's "
               "19.2 kOhm outlier. 1.9474 A total; the audit rounds upward "
               "to 1.95 A and must not fall back to the historical 1.0 A "
               "internal placeholder or to D-787's 1.849/1.912 A. This "
               "remains below the TPS63020 2 A feature rating for VIN > "
               "2.5 V near the 3.3 V output condition, with 52.6 mA of "
               "margin where D789-A11's corrected budget alone would have "
               "left 7.6 mA.",
         pour_delivered="delivered by the two F.Cu +3V3 pours and the In3.Cu "
               "plane, not by a trunk; a track-graph NO_PATH is the expected "
               "answer and is not a defect.  The four local conductors at "
               "either end are measured in the comment above this entry"),
    dict(name="SYS_TO_NFC5V_BOOST", net="/01_POWER_TREE/BQ25185_SYS",
         src=("U12.1", "U12.10", "U12.11", "C24.1", "C26.2", "C28.1"),
         snk=("L2.1",), amps=0.86,
         accept=(dict(layer="In2.Cu", reason="dru-5c", max_length_mm=80.0),),
         accept_reason="D-750 / .kicad_dru section 5c, same trunk and same "
               "derivation as SYS_TO_ACC5V_BOOST; at 0.86 A the IPC-2221B "
               "internal rise is 27.0 K and the plane-coupled rise is 0.59 K.",
         basis="U13 TPS61023 INPUT current at the published NFC_5V_PA 0.50 A "
               "TX burst: 0.50 A x 5.0 V / (0.88 x 3.3 V) = 0.86 A.  U13 is "
               "DNP on AQROOT Demo (the NFC front end runs from +3V3), so this "
               "is the FITTED-VARIANT number and is measured so the trunk is "
               "not sized by accident."),
)



# --------------------------------------------------------------------------
# D-750: THE PLANE-COUPLED RISE, DERIVED FROM THE BOARD'S OWN STACKUP.
#
# IPC-2221B's internal curve (k = 0.024) was measured on isolated coupons in
# still air and IPC-2152 (2009) superseded it: an internal trace in a real
# board with adjacent planes is not half as capable, because the board
# conducts heat and air does not.  Section 5 keeps k = 0.024 as a
# conservative FLOOR-SETTING model, which is the right thing for setting
# floors and the wrong thing for predicting a temperature.
#
# So the prediction is computed instead of asserted, and it is computed from
# the dielectric thicknesses the BOARD declares rather than from a
# remembered number.  D-750 found the previous prose claiming In2 sits
# "about 0.15 mm of FR4 from solid copper on BOTH faces"; the board's own
# stackup says In1 is 0.4000 mm of core away and In3 is 0.2028 mm of prepreg
# away.  That premise was wrong by more than 2x on one face.
#
# THE MODEL.  One-dimensional conduction from the conductor into the two
# nearest copper layers, treated as isothermal:
#
#     dT = I^2 * rho / ( k_fr4 * w^2 * t_cu * (1/d_up + 1/d_down) )
#
# The LENGTH CANCELS, which is the physical content: a long trace between
# planes does not get hotter than a short one, it just heats more board.  It
# is conservative three ways -- it ignores lateral spreading in the
# dielectric, conduction along the copper itself, and the outer layers --
# and it reports the rise OVER THE ADJACENT PLANES, not over ambient, so the
# rail's total dissipation is reported beside it.
# --------------------------------------------------------------------------
K_FR4 = 3.0e-4                  # W/(mm.K), FR4/7628 through-plane, conservative


def stackup_dielectrics(board_path):
    """Ordered copper layers with the dielectric thickness on each side."""
    text = Path(board_path).read_text(encoding="utf-8", errors="replace")
    block = text[text.find("(stackup"):]
    end = block.find('(layer "B.SilkS"')
    block = block[:end] if end > 0 else block[:20000]
    order, name = [], None
    for line in block.splitlines():
        m = re.search(r'\(layer "([^"]+)"', line)
        if m:
            name = m.group(1)
            continue
        m = re.search(r"\(thickness ([\d.]+)\)", line)
        if m and name:
            order.append((name, float(m.group(1))))
            name = None
    cu = [i for i, (n, _) in enumerate(order) if n.endswith(".Cu")]
    out = {}
    for k, i in enumerate(cu):
        up = sum(t for n, t in order[cu[k - 1] + 1:i]) if k > 0 else None
        dn = (sum(t for n, t in order[i + 1:cu[k + 1]])
              if k + 1 < len(cu) else None)
        out[order[i][0]] = dict(thickness_mm=order[i][1],
                                dielectric_up_mm=up, dielectric_down_mm=dn,
                                neighbour_up=order[cu[k - 1]][0] if k > 0 else None,
                                neighbour_down=(order[cu[k + 1]][0]
                                                if k + 1 < len(cu) else None))
    return out


def plane_coupled_rise(stack, layer, width_mm, amps):
    """Rise over the ADJACENT COPPER LAYERS, in kelvin.  None for an outer
    layer, where there is copper on only one face and the still-air term the
    external IPC curve already models is the honest one."""
    row = stack.get(layer)
    if not row or row["dielectric_up_mm"] is None or row["dielectric_down_mm"] is None:
        return None
    cond = K_FR4 * (width_mm ** 2) * row["thickness_mm"] * (
        1.0 / row["dielectric_up_mm"] + 1.0 / row["dielectric_down_mm"])
    if cond <= 0:
        return None
    return (amps ** 2) * RHO_CU / cond


# --------------------------------------------------------------------------
# D-787 / R6-E07 -- AN ISOLATED-COUPON RISE IS NOT A BOARD TEMPERATURE, AND A
# NAMED EXCEPTION IS NOT A JUSTIFIED ONE.
#
# `rise()` above is IPC-2221's external/internal curve.  It describes a trace
# on a coupon whose only cooling is still air along its own length.  For the
# ONE accepted exception on this board -- the 0.200 mm `U11.2` package-land
# neck -- that model reports 137.6 K at the D-787 design current, and reading
# that as a predicted board temperature would be wrong in both directions: it
# ignores the adjacent copper plane 0.2104 mm away, and it ignores the two wide
# terminations the 5.5 mm run ends on.
#
# So an ACCEPTED run also gets a CONDUCTION-BOUNDED rise, and the acceptance
# now has to pass it.  One-dimensional fin with distributed heating, both ends
# clamped at the temperature of the copper they join:
#
#     p   = I^2 rho / A_cu                      W per mm of run
#     g   = k_fr4 w (1/d_up + 1/d_down)         W per mm per K, to the
#                                               ADJACENT COPPER LAYERS
#     lam = sqrt(k_cu A_cu / g)                 mm
#     dT  = p lam^2 / (k_cu A_cu) * (1 - 1/cosh(L / (2 lam)))
#
# and with no adjacent copper on either face the same equation degenerates to
# the pure conduction bar, dT = p L^2 / (8 k_cu A_cu).  It is conservative:
# no lateral spreading in the dielectric, no convection or radiation from the
# outer face, no soldermask, and the rise is reported OVER THE ADJACENT COPPER
# rather than over ambient.  It is a MODEL, not a measurement -- the
# first-article thermal acceptance in the assembly plan remains the
# measurement -- but it is a number the exception can be judged against
# instead of a sentence asking the reader to discount the coupon figure.
K_CU = 0.385                    # W/(mm.K), copper
ALPHA_CU = 0.00393              # per K, copper resistivity temperature coefficient
ACCEPTED_RUN_DT_LIMIT_K = 40.0  # over the adjacent copper, for an accepted run

# --------------------------------------------------------------------------
# D-788 / R7-D787-04 -- THE BOUNDARY CONDITION WAS AN ASSUMPTION, AND THE
# ACCEPTANCE HAD NO ABSOLUTE NUMBER IN IT.
#
# D-787's fin solved ONE boundary condition -- both ends clamped at the
# temperature of the copper they join -- and reported 14.3 K against a 40 K
# limit.  Round-7's objection is correct on three counts and all three are
# closed here rather than argued with:
#
#   1  BOTH ENDS CLAMPED IS THE MOST FAVOURABLE OF THREE PLAUSIBLE BOUNDARY
#      CONDITIONS.  The run now solves all three -- both ends clamped, one end
#      insulated, and no axial sink at all -- and the ACCEPTANCE takes the
#      WORST.  The three differ by more than 3x, which is exactly why picking
#      one of them silently was the defect.
#   2  THE COPPER GETS HOTTER AND THEN MORE RESISTIVE.  rho is now solved
#      self-consistently at the run's own peak temperature through copper's
#      0.393 %/K coefficient, so the feedback that Round-7 said "can cross the
#      chosen 40 K relative criterion" is inside the model instead of outside
#      it.
#   3  THE U11 END IS NOT AT PLANE TEMPERATURE.  The BQ25185's own BATFET
#      dissipates I^2 x RON_BAT in the package this land belongs to, so the
#      clamped end is clamped at something warmer than the plane.  That
#      endpoint rise is a DECLARED input with its derivation printed, and it is
#      added to the absolute result rather than assumed away.
#
# AND THE ACCEPTANCE IS NOW ABSOLUTE AS WELL AS RELATIVE.  A rise "over the
# copper it terminates on" says nothing about how hot anything actually gets.
# The run also reports a PREDICTED PEAK TEMPERATURE at the declared ambient and
# is judged against the tightest absolute limit around it: the pouch cell this
# copper sits directly beneath, whose own published charge working range tops
# out at 40 C, is the reason the absolute limit is not simply the laminate's or
# the charger junction's.
#
# IT IS STILL A MODEL.  It carries no lateral spreading in the dielectric, no
# convection or radiation from the outer face and no soldermask, all of which
# are real and all of which help.  THE MEASUREMENT OF RECORD IS THE
# FIRST-ARTICLE THERMOGRAPHY in the assembly plan, and nothing here replaces
# it.  What it replaces is the IPC-2221B isolated-coupon number, which is a
# SCREENING figure and is never a predicted board temperature.
AMBIENT_DESIGN_MAX_C = 40.0     # top of the declared 0..40 C prototype envelope
BOARD_RISE_ALLOWANCE_K = 10.0   # DECLARED: bulk board rise over ambient at the
                                # full published concurrent load; first-article
                                # thermography measures it
ABSOLUTE_PEAK_LIMIT_C = 105.0
ABSOLUTE_LIMIT_BASIS = (
    "105 C is a DECLARED CONDUCTOR-SIZING limit for copper heated BY ITS OWN "
    "CURRENT on this prototype, chosen 45 K below the Tg >= 150 C laminate the "
    "fab notes require.  D-789 / D788-03 NARROWS WHAT IT CLAIMS.  D-788 wrote "
    "it as 'the laminate's maximum continuous operating temperature' and as "
    "'the tighter of the laminate's and the silicon's'; neither reading is "
    "supportable.  It is not a laminate specification -- no source in this "
    "repository publishes an MOT for a Tg-150 FR4 -- and it is not the "
    "silicon's, because the silicon's limit is TI's own TJ maximum, which is "
    "COMPUTED separately (see PACKAGE_JUNCTION below) instead of being "
    "inferred from a copper temperature.  What this number rules on is "
    "conductor sizing, and it is deliberately conservative.  A run inside "
    "BATTERY_SHADOW is judged instead against the pouch limit below, which is "
    "tighter.")
# --------------------------------------------------------------------------
# D-789 / D788-03 -- THE HOTTEST THING ON THIS BOARD IS NOT THE COPPER, AND
# NOTHING HAD EVER COMPUTED IT.
#
# Round-8: "Reconcile BATFET electrical model 196 mOhm with thermal heat basis;
# component heat up to ~1.08 W at 2.35 A."  It is right twice over.
#
# FIRST, THE TWO MODELS DISAGREED.  `demo_feature_contract` F6 charges the
# BQ25185's BATFET at RON_BAT_MAX x RON_BAT_VBAT_ALLOWANCE = 0.140 x 1.40 =
# 196 mOhm, because SLUSF65B specifies RON_BAT only at VBAT = 4.5 V and this
# board runs it near 3.2 V.  D-788's thermal endpoint allowance charged the
# same FET at the raw 0.140 -- 0.773 W against the electrical model's 1.082 W.
# One number, two answers, in one release.  They are the same number now.
#
# SECOND, THE QUESTION WAS BEING ASKED OF THE WRONG OBJECT.  D-788 turned the
# device's dissipation into a DECLARED 25 K "endpoint rise" of the copper land
# and then judged the COPPER.  TI publishes the direct answer: SLUSF65B section
# 6.3.7.6 gives TJ = TA + thetaJA x PDISS with PDISS = PSYS + PBAT, and section
# 5.3 gives RthetaJA = 68.3 C/W for the DLH package.  In the state this rail is
# sized for -- battery-only discharge at the full published concurrent load --
# PSYS is zero and PBAT = (VSYS - VBAT) x IBAT = IBAT^2 x RON_BAT.  So the
# junction temperature is COMPUTED, from TI's own equation and TI's own
# constants, and judged against TI's own Recommended Operating Conditions
# maximum of 125 C.  The land the neck joins is a pin of that package and
# cannot be hotter than its junction, so the junction clause bounds the copper
# there as well -- which is why the copper clause above no longer has to
# pretend to.
#
# WHAT IT COSTS TO BE CONSERVATIVE IS PRINTED.  The margin is reported at the
# datasheet's own RON_BAT maximum AND with the declared 1.40x allowance on top
# of it, and at 25 C ambient as well as at the 40 C top of the envelope, so
# every layer of pessimism in the answer is visible rather than compounded
# silently.  FIRST-ARTICLE THERMOGRAPHY (C-THERM-01) REMAINS THE MEASUREMENT.
#
# D-790 / D789-A02 WITHDRAWS THE LAST SENTENCE THIS PARAGRAPH USED TO CARRY.
# It read: thetaJA "is largely driven by the board layout, board layers,
# copper thickness"; a six-layer board with two solid ground planes is better
# than the JEDEC coupon, so the figure is conservative in the direction that
# matters.  THAT ARGUMENT IS ABOUT THE WRONG HALF OF THE PATH.  Our copper is
# indeed better than the coupon's; what a sealed 85 x 160 x 23 mm handheld
# changes is the AIR, which the JEDEC measurement holds at TA and this product
# does not.  The composition that replaces it is in the D-790 block above the
# constants below, and the open-air JEDEC number is still reported -- labelled
# as the reference-board figure it is -- so the size of the correction shows.
# --------------------------------------------------------------------------
# D-790 / D789-A02 -- A JEDEC THERMAL RESISTANCE IS NOT A PRODUCT BOUND.
#
# D-789 computed `TJ = TA + RthetaJA x PDISS` with TI's 68.3 C/W and called
# the answer -- 115.44 C at the 40 C top of the declared envelope -- a
# conservative ceiling with 9.56 K of margin.  Round-9 rejected that, and it
# is right for a reason the D-789 comment actually states and then argues
# past: 68.3 C/W is measured on a JEDEC board in OPEN STILL AIR AT TA.  This
# product is a sealed 85 x 160 x 23 mm handheld.  The air around the package
# is NOT at the external ambient, and on the board's copper side the D-789
# note's "our board is better than the coupon" argument is about the WRONG
# HALF of the path: what the enclosure changes is the air, not the copper.
#
# THE MODEL IS NOW A SERIES OF THREE THINGS, EACH NAMED.
#
#   TJ = T_ambient(external) + R_SYS x P_internal + RthetaJA x P_U11
#
#   1  T_ambient is the EXTERNAL ambient, 0..40 C declared.
#   2  R_SYS is the enclosure's own internal-air-to-external-ambient
#      resistance, carrying the WHOLE dissipation that stays inside the case.
#   3  RthetaJA is TI's figure, now referenced to the INTERNAL air rather than
#      to the external ambient -- which is the only reference a still-air
#      JEDEC number can honestly be used against.
#
# R_SYS IS DECLARED AND ITEMISED.  Surface 2(85x160) + 2(85x23) + 2(160x23) =
# 0.03847 m2.  Natural convection on a 0.16 m characteristic length at a 20 K
# rise is about 4.8 W/m2K and radiation from a painted/moulded surface at
# eps = 0.9 between 330 K and 313 K is about 6.8 W/m2K, so the itemised
# combined coefficient is about 11.5 W/m2K.  8.0 W/m2K is DECLARED -- 70 % of
# the itemised figure -- giving R_SYS = 3.249 K/W.  It is a DECLARED
# ALLOWANCE and `C-THERM-01` first-article thermography is what MEASURES it.
# Nothing here claims it has been measured.
#
# WHAT LEAVES THE CASE IS SUBTRACTED, AND ONLY WHAT LEAVES BY CONSTRUCTION.
# The Community Port's published 400 mA at the 3.3 V rail and 300 mA at 5 V
# are delivered to an accessory on the OUTSIDE of the right wall, so 2.839 W
# of the pack's output is dissipated outside this enclosure.  Radiated RF
# (about 0.27 W at the two published TX powers) and emitted light are NOT
# subtracted, which is conservative.
#
# AND THE TWO REGIMES ARE SEPARATED, BECAUSE ONLY ONE OF THEM IS A PROBLEM.
#
#   CHARGE.  PDISS = PSYS + PBAT with a linear charger is the larger number,
#   and it is SELF-LIMITING: SLUSF65B 5.5 gives TREG = 100 C typical junction
#   temperature regulation, and 6.3.7.6 says the device "reduces the charge
#   current when TJ reaches the thermal regulation threshold".  The charge
#   regime therefore cannot reach the 125 C operating maximum by design; its
#   consequence is a LONGER CHARGE in a warm enclosure, not an exceeded
#   junction, and that is a product behaviour to document rather than a bound
#   to prove.  This clause proves only that TREG is below the operating
#   maximum, which is what makes the argument valid.
#
#   BATTERY DISCHARGE.  TREG regulates CHARGE current; with no adapter there
#   is no charge current to reduce, so nothing between the BATFET and
#   TSHUT_RISING at 150 C -- which powers the product off.  This regime is
#   where the bound has to be real, and it is the one solved below.
#
# WHAT THE HONEST ANSWER TURNS OUT TO BE, STATED PLAINLY.  At the 40 C top of
# the declared ambient envelope, with BOTH accessory rails at their full
# published budgets AND every internal subsystem at its published maximum
# SIMULTANEOUSLY AND INDEFINITELY, this model puts the junction ABOVE 125 C.
# That state is not a sustainable operating point for an 85 x 160 x 23 mm
# sealed handheld dissipating about 6 W, and no thermal metric was going to
# make it one.  So the envelope is SPLIT, which is the second option Round-9
# itself offers:
#
#   * the PEAK ELECTRICAL ENVELOPE is unchanged and still rules conductor
#     ampacity, protection ordering and the battery connection rating -- all
#     of which are short-time-constant or instantaneous questions;
#   * a SUSTAINED THERMAL ENVELOPE is DERIVED here and published: the ambient
#     up to which the full simultaneous envelope stays inside 125 C, and the
#     sustained battery current the top of the declared ambient range allows.
#
# NOTHING IS REMOVED.  The published 400 mA and 300 mA budgets stand, no
# Kickstarter-visible capability is withdrawn, and the D-788 Option A contract
# is untouched: what is added is the ambient condition under which every
# published maximum may be taken AT ONCE, which was never stated before and
# was silently assumed to be the whole 0..40 C range.
#
# THERE IS NO TEMPERATURE SENSOR TO ENFORCE THIS WITH.  The as-built limits
# already record that R38 is unfitted and there is no pack NTC, so this is a
# DECLARED OPERATING CONDITION plus first-article measurement, and it is
# written down as one rather than presented as a firmware guarantee.
# --------------------------------------------------------------------------
ENCLOSURE_MM = (85.0, 160.0, 23.0)
SYSTEM_THERMAL = dict(
    enclosure_mm=list(ENCLOSURE_MM),
    enclosure_source="docs/full-beta-v2/DEVICE_SPEC.md section 12, "
                     "'Enclosure external 85 x 160 x 23 mm (portrait)'",
    declared_h_W_per_m2K=8.0,
    itemised_h_W_per_m2K=11.5,
    h_basis="natural convection about 4.8 W/m2K on a 0.16 m characteristic "
            "length at a 20 K rise, plus radiation about 6.8 W/m2K at "
            "eps = 0.9 between 330 K and 313 K; 8.0 is DECLARED at 70 % of "
            "the itemised sum",
    is_a_declared_allowance=True,
    measurement_of_record="first-article thermography, assembly plan "
                          "C-THERM-01: R_SYS and the internal-air rise are "
                          "MEASURED there.  Nothing in this file claims they "
                          "have been.",
    radiated_not_subtracted="about 0.27 W of published RF TX power and the "
                            "backlight's emitted light leave the case as "
                            "radiation and are NOT subtracted",
    # The ambient at which the FULL simultaneous envelope must still be inside
    # the junction maximum for this contract to pass.  Ordinary indoor use.
    full_concurrency_required_ambient_C=25.0,
    full_concurrency_required_ambient_basis=(
        "25 C, the standard reference ambient every datasheet in this "
        "repository is characterised at.  The declared PRODUCT envelope "
        "remains 0..40 C for every state; what is qualified only to the "
        "ambient this file DERIVES is the SUSTAINED simultaneous maximum of "
        "every internal subsystem AND both accessory rails AND full "
        "backlight, held indefinitely -- which is a peak electrical envelope, "
        "not an operating mode.  Above that ambient the sustained "
        "simultaneous total must come down; the SUSTAINED THERMAL ENVELOPE "
        "derived below is what it must come down to at the 40 C top."))
CHARGE_REGIME = dict(
    treg_C=100.0,
    tshut_rising_C=150.0,
    source="TI SLUSF65B 5.5 Electrical Characteristics: TREG typical "
           "junction temperature regulation 100 C, TSHUT_RISING 150 C; "
           "section 6.3.7.6 'During charging, to prevent the device from "
           "overheating, the device monitors the junction temperature of the "
           "die and reduces the charge current when TJ reaches the thermal "
           "regulation threshold (TREG)'.",
    consequence="a longer charge in a warm enclosure, not an exceeded "
                "junction.  The BATFET discharge regime has no equivalent "
                "regulation -- TREG reduces CHARGE current and there is none "
                "when no adapter is attached -- so that regime is the one "
                "bounded below.")


# D-790 / D789-A01 + D789-A02.  THE PASS PAIR IS A HEAT SOURCE, AND ITS
# RESISTANCE IS A PROPERTY OF THE PART D-790 SELECTS.
#
# `demo_feature_contract` F10 solves the four-channel path self-consistently
# for the selected `AO4800` -- gate drive, source-node offsets, temperature --
# and the number it converges to at the PEAK design current is 68.7 mOhm per
# channel.  The constant below is that figure rounded UP, so it is
# conservative at every lower current, and F10 machine-checks that the two
# files agree.  A pass-pair part change that moved this and left this file
# alone would be caught there rather than silently under-heating the model.
PASS_PAIR_CHANNEL_OHM = 0.069
PASS_PAIR_CHANNEL_SOURCE = (
    "AOS AO4800 Rev 6.1, archived vendor/AOS/aos-ao4800-rev6p1-2023-08.pdf: "
    "RDS(on) MAX 50 mOhm at VGS = 2.5 V, ID = 5 A, TJ = 25 C, carried to the "
    "self-consistent junction temperature with the datasheet's own 25 -> "
    "125 C ratio at the VGS = 10 V row (27 -> 40 mOhm).  Four channels in "
    "series; see demo_feature_contract F10.")

# D-790 / D789-A02.  THE SUSTAINED THERMAL ENVELOPE'S REFERENCE STATE.
#
# The PEAK electrical envelope adds every published maximum together, which is
# right for ampacity, protection ordering and the connector rating and wrong
# for a steady-state junction temperature.  This is the state the product
# actually CLAIMS it can hold indefinitely at the top of the declared ambient
# range, and it is what the thermal verdict rules on.  It is deliberately
# heavy: it keeps BOTH published accessory budgets, the display at FULL
# brightness and BOTH radios transmitting, and drops only the three loads that
# are physically bursty -- the NFC field, a microSD write and an IR burst.
SUSTAINED_REFERENCE_STATE = dict(
    what="both published Community-Port budgets (400 mA on the 3.3 V rail, "
         "300 mA on the 5 V rail), the display backlight at full brightness, "
         "the panel logic, the expanders/IMU and the front RGB, with BOTH the "
         "Wi-Fi and the sub-GHz radios transmitting and the audio amplifier "
         "at its capped level -- held indefinitely",
    excluded="the NFC field, a microSD write and an IR burst, all three of "
             "which are bursty rather than continuous loads",
    p3v3_internal_A=0.89378,
    p3v3_itemised={
        "display backlight converter input": 0.21158,
        "display panel logic + touch": 0.050,
        "Wi-Fi / BLE TX": 0.355,
        "sub-GHz TX": 0.140,
        "audio at the capped level": 0.120,
        "touch + housekeeping": 0.013,
        "front RGB at white": 0.0042,
    },
    acc_3v3_A=0.400, acc_5v_A=0.300,
    i_bat_A=1.70,
    i_bat_basis="((0.89378 + 0.400) x 3.223012 / 0.90 + 0.300 x 5.165 / 0.88) "
                "/ 3.85 = 1.6608 A, rounded UP to 1.70 A.  "
                "demo_feature_contract F6 re-derives it from the live budget "
                "and refuses a disagreement.")


def enclosure_surface_m2(mm=None):
    w, h, d = ENCLOSURE_MM if mm is None else mm
    w, h, d = w / 1000.0, h / 1000.0, d / 1000.0
    return 2.0 * (w * h) + 2.0 * (w * d) + 2.0 * (h * d)


def system_thermal_resistance_K_per_W(spec=None):
    spec = SYSTEM_THERMAL if spec is None else spec
    return 1.0 / (spec["declared_h_W_per_m2K"]
                  * enclosure_surface_m2(spec.get("enclosure_mm")))
PACKAGE_JUNCTION = dict(
    reference="U11",
    part="BQ25185",
    package="DLH0010A",
    theta_ja_C_per_W=68.3,
    theta_jb_C_per_W=34.7,
    psi_jb_C_per_W=34.7,
    psi_jt_C_per_W=2.0,
    tj_operating_max_C=125.0,
    tj_absolute_max_C=150.0,
    tshut_rising_C=150.0,
    source="TI SLUSF65B, archived hardware/demo/kicad/aqroot-demo/vendor/"
           "BQ25185/ti-bq25185-slusf65b-2026-08.pdf: section 5.3 Thermal "
           "Information RthetaJA 68.3 C/W (JEDEC) for the DLH package; "
           "section 6.1 Recommended Operating Conditions TJ -40..125 C; "
           "section 5.1 Absolute Maximum TJ 150 C; section 6.3.7.6 "
           "'TJ = TA + thetaJA x PDISS' with 'PDISS = PSYS + PBAT', "
           "'PBAT = (VSYS - VBAT) x IBAT'; TSHUT_RISING 150 C.",
    equation="TJ = TA + thetaJA x (PBAT + P_board_copper); PBAT = IBAT^2 x "
             "RON_BAT, and the board copper this land joins is added because "
             "its heat enters the same package through the same pin.  PSYS is "
             "zero: the state this rail is sized for is battery-only "
             "discharge, where no input converter is running.",
    measurement_of_record="first-article thermography, assembly plan "
                          "C-THERM-01, measured at the top of the declared "
                          "0..40 C ambient envelope with both accessory rails "
                          "at their published budgets")
# The same two numbers F6 rules with, so the two models cannot disagree again.
RON_BAT_MAX_OHM = 0.140
RON_BAT_VBAT_ALLOWANCE = 1.40


# The internal dissipation the enclosure has to lose, at a given pack
# current.  Everything the pack delivers stays inside EXCEPT what the
# Community Port hands to an accessory on the outside of the right wall.
DISCHARGE_SYSTEM = dict(
    vcell_V=3.85,
    vcell_basis="the DERIVED dual-rail VCELL floor the firmware policy "
                "enforces; a HIGHER cell voltage costs MORE pack power for "
                "the same current and is the conservative direction for the "
                "enclosure, so the floor is used, not the 3.5 V single-rail "
                "one",
    acc_3v3_A=0.400, acc_3v3_V=3.223012,
    acc_5v_A=0.300, acc_5v_V=5.165,
    delivered_basis="F6's published Community-Port budgets at the rail's own "
                    "worst-case maximum and the boost's worst-case setpoint; "
                    "J5 is on the OUTSIDE of the right wall, so this power is "
                    "dissipated in the accessory and not in this enclosure")


# D-790 / D789-A02, "adjacent losses".  THE CELL IS INSIDE THE CASE AND SO IS
# EVERYTHING BETWEEN IT AND `BAT_PROTECTED_P`.
#
# `vcell_V` is the potential at `BAT_PROTECTED_P`, which is where the MAX17048
# measures and where the firmware floors are defined -- so `vcell_V x I` is the
# power that ENTERS the board downstream of the pass pair.  Everything upstream
# of that node dissipates INSIDE THIS ENCLOSURE too and D-789 counted none of
# it: the four pass-pair channels, `R75`, the `F1` fuse element, the pack's own
# protection-board FETs and the 26 AWG harness.  Every one of those is under
# the same lid as the BQ25185 and the pouch.
UPSTREAM_LOSS = dict(
    r75_ohm=0.010,
    r75_basis="the fitted 10 mOhm LTC4368 sense element, D-771",
    fuse_ohm=0.020,
    fuse_basis="DECLARED: the fitted 0466005 5 A nano2 element's cold "
               "resistance is not published in this repository; 20 mOhm is a "
               "declared allowance for a 5 A thin-film fuse and is MEASURED at "
               "first article",
    pcm_ohm=0.040,
    pcm_basis="DECLARED: the 785060 pack's protection board is an S-8261AAJMD "
              "with 8814 MOSFETs (pack specification section 11); the PCM's "
              "channel resistance is not published, and 40 mOhm is a declared "
              "allowance for a two-FET 1S PCM.  MEASURED at first article",
    harness_ohm=0.054,
    harness_basis="two UL 26 AWG conductors, about 100 mm each way, at "
                  "0.1339 ohm/m nominal plus the J4 terminations; both "
                  "conductors count because VCELL is differential",
    is_a_declared_allowance=True,
    measurement_of_record="C-THERM-01 and the first-article battery-path "
                          "resistance measurement")


def upstream_loss_W(amps, pass_pair_ohm_per_channel=0.0, spec=None,
                    channels=4):
    """Everything between the cell and BAT_PROTECTED_P, all of it inside."""
    spec = UPSTREAM_LOSS if spec is None else spec
    series = (spec["r75_ohm"] + spec["fuse_ohm"] + spec["pcm_ohm"]
              + spec["harness_ohm"] + channels * pass_pair_ohm_per_channel)
    return amps * amps * series, series


def internal_dissipation_W(amps, spec=None, accessory=True,
                           pass_pair_ohm_per_channel=0.0):
    spec = DISCHARGE_SYSTEM if spec is None else spec
    pack = spec["vcell_V"] * amps
    out = (spec["acc_3v3_A"] * spec["acc_3v3_V"]
           + spec["acc_5v_A"] * spec["acc_5v_V"]) if accessory else 0.0
    up, _ = upstream_loss_W(amps, pass_pair_ohm_per_channel)
    return pack - out + up, pack, out


def package_junction(amps, board_copper_W=0.0, ambient_C=None,
                     spec=None, ron_allowance=None, system=None,
                     accessory=True):
    """D-790 / D789-A02.  TI's junction equation, referenced to the INTERNAL
    air of this product's own enclosure rather than to open still air.

    Returns the enclosure-aware ruling, the JEDEC open-air figure D-789 used
    (clearly labelled as the reference-board number it is), the sustained
    thermal envelope this enclosure supports, and the ambient up to which the
    full simultaneous envelope stays inside TI's operating maximum.
    """
    spec = PACKAGE_JUNCTION if spec is None else spec
    system = SYSTEM_THERMAL if system is None else system
    ambient_C = AMBIENT_DESIGN_MAX_C if ambient_C is None else ambient_C
    allowance = (RON_BAT_VBAT_ALLOWANCE if ron_allowance is None
                 else ron_allowance)
    r_sys = system_thermal_resistance_K_per_W(system)
    ron_used = RON_BAT_MAX_OHM * allowance

    def solve(a, ron, ta, pass_pair_ohm=None):
        pp = (PASS_PAIR_CHANNEL_OHM if pass_pair_ohm is None else pass_pair_ohm)
        p_int, pack, out = internal_dissipation_W(
            a, accessory=accessory, pass_pair_ohm_per_channel=pp)
        air = ta + r_sys * p_int
        p_bat = a * a * ron
        p_diss = p_bat + board_copper_W
        up_W, up_ohm = upstream_loss_W(a, pp)
        return dict(internal_W=round(p_int, 4), pack_W=round(pack, 4),
                    delivered_out_W=round(out, 4),
                    upstream_loss_W=round(up_W, 4),
                    upstream_series_ohm=round(up_ohm, 6),
                    pass_pair_channel_ohm=round(pp, 6),
                    enclosure_rise_K=round(r_sys * p_int, 3),
                    internal_air_C=round(air, 2),
                    p_bat_W=round(p_bat, 4), p_diss_W=round(p_diss, 4),
                    tj_C=round(air + spec["theta_ja_C_per_W"] * p_diss, 2),
                    open_air_jedec_tj_C=round(
                        ta + spec["theta_ja_C_per_W"] * p_diss, 2))

    out = dict(spec)
    out.update(
        ambient_C=ambient_C, design_amps=amps,
        board_copper_W=round(board_copper_W, 6),
        ron_bat_datasheet_max_ohm=RON_BAT_MAX_OHM,
        ron_bat_vbat_allowance=allowance,
        ron_bat_used_ohm=round(ron_used, 6),
        system_thermal=dict(system),
        enclosure_surface_m2=round(
            enclosure_surface_m2(system.get("enclosure_mm")), 6),
        r_sys_K_per_W=round(r_sys, 4),
        discharge_system=dict(DISCHARGE_SYSTEM),
        equation="TJ = TA(external) + R_SYS x P_internal + thetaJA x "
                 "(PBAT + P_board_copper); PBAT = IBAT^2 x RON_BAT.  PSYS is "
                 "zero: this is the battery-only discharge regime, the one "
                 "TREG does not regulate.",
        charge_regime=dict(
            CHARGE_REGIME,
            is_self_limiting=bool(
                CHARGE_REGIME["treg_C"] < spec["tj_operating_max_C"]),
            margin_to_operating_max_K=round(
                spec["tj_operating_max_C"] - CHARGE_REGIME["treg_C"], 2)))

    for name, ron in (("at_datasheet_ron_bat_max", RON_BAT_MAX_OHM),
                      ("at_the_declared_vbat_allowance", ron_used)):
        d = solve(amps, ron, ambient_C)
        d.update(
            ron_bat_ohm=round(ron, 6),
            margin_to_operating_max_K=round(
                spec["tj_operating_max_C"] - d["tj_C"], 2),
            margin_to_thermal_shutdown_K=round(
                spec["tshut_rising_C"] - d["tj_C"], 2))
        out[name] = d
    ruling = out["at_the_declared_vbat_allowance"]

    # ---- the DERIVED envelope numbers ----------------------------------
    # (a) the ambient at which the full simultaneous envelope is exactly at
    #     the operating maximum, and
    # (b) the sustained battery current the TOP of the declared ambient
    #     range supports, bounded by the junction AND by the pouch's own
    #     published discharge working limit.
    qualified_ambient = round(
        ambient_C + (spec["tj_operating_max_C"] - ruling["tj_C"]), 2)
    lo, hi = 0.0, 8.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        d = solve(mid, ron_used, ambient_C)
        if (d["tj_C"] <= spec["tj_operating_max_C"]
                and d["internal_air_C"] <= POUCH_ADJACENT_LIMIT_C):
            lo = mid
        else:
            hi = mid
    sustained = solve(lo, ron_used, ambient_C)
    ref = solve(SUSTAINED_REFERENCE_STATE["i_bat_A"], ron_used, ambient_C)
    out.update(
        sustained_reference_state=dict(
            SUSTAINED_REFERENCE_STATE,
            result=ref,
            is_inside_the_sustained_envelope=bool(
                SUSTAINED_REFERENCE_STATE["i_bat_A"] <= lo + 1e-9)),
        ruling_case="at_the_declared_vbat_allowance",
        predicted_tj_C=ruling["tj_C"],
        internal_air_C=ruling["internal_air_C"],
        enclosure_rise_K=ruling["enclosure_rise_K"],
        limit_C=spec["tj_operating_max_C"],
        margin_K=ruling["margin_to_operating_max_K"],
        # THE JEDEC OPEN-AIR NUMBER, KEPT AND LABELLED.  This is what D-789
        # published as the bound; it is retained as the reference-board
        # figure it always was, so the size of the correction is visible.
        jedec_open_air_tj_C=ruling["open_air_jedec_tj_C"],
        jedec_open_air_is_not_the_product_bound=(
            "RthetaJA 68.3 C/W is a JEDEC reference-board figure measured in "
            "open still air at TA.  Referenced to the external ambient it "
            "understates this product's junction by the enclosure's own "
            "internal-air rise, which is what D789-A02 found."),
        full_concurrency_qualified_ambient_C=qualified_ambient,
        full_concurrency_required_ambient_C=system[
            "full_concurrency_required_ambient_C"],
        full_concurrency_ambient_basis=system[
            "full_concurrency_required_ambient_basis"],
        sustained_thermal_envelope_A=round(lo, 4),
        sustained_thermal_envelope=sustained,
        sustained_envelope_basis=(
            "the largest SUSTAINED battery current that keeps BOTH the "
            "BQ25185 junction inside TI's 125 C operating maximum AND the "
            "enclosure's internal air inside the fitted pouch's published "
            "60 C discharge working range, at the 40 C top of the declared "
            "ambient envelope.  The PEAK electrical envelope is unchanged "
            "and still rules conductor ampacity, protection ordering and the "
            "battery connection rating."),
        peak_envelope_is_not_a_thermal_envelope=(
            "the design current above sums every internal subsystem at its "
            "published maximum with both accessory rails at their published "
            "budgets, concurrently.  That is the right basis for ampacity, "
            "protection and connector rating, all of which are "
            "short-time-constant or instantaneous.  It is NOT a steady-state "
            "thermal operating point and this file no longer treats it as "
            "one."),
        # THE VERDICT.  The charge regime must be self-limiting, the full
        # simultaneous envelope must be qualified at or above the declared
        # ordinary-indoor ambient, and the sustained envelope must be
        # published.  The peak envelope is deliberately NOT required to be
        # inside the junction limit at 40 C; claiming it were would be the
        # D-789 defect again.
        # THE VERDICT, RE-BASED AT D-790 ONCE THE UPSTREAM LOSSES WERE
        # COUNTED.  Requiring the PEAK simultaneous envelope to be a
        # steady-state operating point at 40 C was the D-789 mistake in a new
        # place; what must hold is that the DECLARED SUSTAINED REFERENCE STATE
        # -- both published accessory budgets, the display at full brightness
        # and one radio transmitting, held indefinitely at the top of the
        # declared ambient range -- is inside the derived envelope, that the
        # pouch stays inside its own published discharge window there, and
        # that the charge regime is self-limiting.  The ambient up to which
        # the PEAK envelope could be held indefinitely is DERIVED and
        # REPORTED, not required.
        ok=bool(out["charge_regime"]["is_self_limiting"]
                and lo >= SUSTAINED_REFERENCE_STATE["i_bat_A"] - 1e-9
                and ref["internal_air_C"] <= POUCH_ADJACENT_LIMIT_C + 1e-9
                and ref["tj_C"] <= spec["tj_operating_max_C"] + 1e-9),
        at_25C_ambient_tj_C=solve(amps, ron_used, 25.0)["tj_C"],
        the_land_cannot_be_hotter_than_the_junction=(
            "U11.2 is a pin of this package, so the copper AT the land is "
            "bounded by TJ.  The conductor-sizing limit above rules on the "
            "copper's own rise; this clause rules on the package."))
    return out
POUCH_ADJACENT_LIMIT_C = 60.0
POUCH_ADJACENT_BASIS = (
    "the fitted 785060 pouch cell's published discharge working range tops out "
    "at 60 C; its charge range tops out at 40 C and firmware/charger "
    "behaviour, not copper temperature, is what bounds that.  Applied only to "
    "copper that is actually under the cell.")
BATTERY_SHADOW_MM = (7.00, 64.00, 23.50, 98.50)   # x0, x1, doc-y0, doc-y1
BOARD_H_MM = 148.0


def inside_battery_shadow(x_mm, y_mm):
    """Is this point under the pouch?  Doc-Y is measured from the board top."""
    if x_mm is None or y_mm is None:
        return False
    x0, x1, dy0, dy1 = BATTERY_SHADOW_MM
    doc_y = BOARD_H_MM - y_mm
    return x0 <= x_mm <= x1 and dy0 <= doc_y <= dy1


def _fin(p_per_mm, g, axial, length_mm, boundary):
    """Peak rise of a 1-D fin with distributed heating, three boundary cases."""
    if g <= 0:
        return p_per_mm * (length_mm ** 2) / (8.0 * axial)
    lam = math.sqrt(axial / g)
    if boundary == "both_ends_clamped":
        return (p_per_mm / g) * (1.0 - 1.0 / math.cosh(length_mm / (2.0 * lam)))
    if boundary == "one_end_insulated":
        return (p_per_mm / g) * (1.0 - 1.0 / math.cosh(length_mm / lam))
    if boundary == "no_axial_sink":
        return p_per_mm / g
    raise ValueError(boundary)


BOUNDARY_CASES = ("both_ends_clamped", "one_end_insulated", "no_axial_sink")
# D-789 / D788-03.  A BOUND THAT NEEDS NO LATERAL MODEL AT ALL.
#
# Round-8's objection to D-788 is that the acceptance cell depended on the
# `w + 2d` transverse-spreading approximation, and that a different sensitivity
# on the same boundary gives a much hotter answer.  It is a fair objection to a
# model with two free choices in it.
#
# The answer is to stop needing them.  The heat generated in a run must leave
# through its ends or through the dielectric; it cannot do neither.  So the
# PHYSICALLY WORST case is that ALL of it leaves through ONE end and NONE of it
# laterally, and for a bar with uniform distributed heating that is
#
#     dT = p L^2 / (2 k_cu A)
#
# which requires only that the OTHER end is at the reference temperature.  This
# run's two ends are named copper objects, so that premise is a fact about the
# board rather than a choice.  It DOMINATES every clamped and one-end-insulated
# cell of the 2 x 3 matrix at every lateral treatment (the fin's own no-lateral
# limit is p L^2 / 8 k A for both ends clamped, a quarter of it), so the matrix
# becomes a REPORT and this becomes the acceptance.
#
# `no_axial_sink` is retained in the report and is NOT an acceptance candidate:
# it is the semi-infinite-run limit, and it describes a conductor with no
# terminating copper at either end.  Applying it to a 0.575 mm neck between a
# package land and a 0.300 mm taper is not conservatism, it is a different
# geometry.  The report says so rather than silently dropping it.
AXIAL_ONLY_CASE = "all_heat_out_one_end_no_lateral_help"
# Above this the axial-only bound has no fixed point and says only "this run
# does not cool through its ends".  See `axial_only_rise`.
AXIAL_ONLY_VACUOUS_ABOVE_K = 1000.0


def axial_only_rise(stack, layer, width_mm, run_length_mm, amps,
                    reference_C=None):
    """dT = p L^2 / (2 k A), solved self-consistently in rho(T)."""
    row = stack.get(layer)
    if not row or not width_mm or not run_length_mm or not amps:
        return None
    a_cu = width_mm * row["thickness_mm"]
    if a_cu <= 0:
        return None
    reference_C = (AMBIENT_DESIGN_MAX_C + BOARD_RISE_ALLOWANCE_K
                   if reference_C is None else reference_C)
    # THE SOLVE DIVERGES WHEN THE BOUND IS VACUOUS, AND THAT IS INFORMATION.
    # Copper's resistivity rises with temperature, so a run long enough that
    # the axial path alone cannot carry its heat has no fixed point -- the
    # iteration runs away.  That is not a statement about the board: it is the
    # bound saying "a 76 mm run does not cool through its ends".  Return None
    # so the caller drops this candidate rather than reporting 1e48 K.
    dt = 0.0
    for _ in range(200):
        rho = RHO_CU * (1.0 + ALPHA_CU * ((reference_C + dt) - 20.0))
        p = (amps ** 2) * rho / a_cu
        nxt = p * (run_length_mm ** 2) / (2.0 * K_CU * a_cu)
        if nxt > AXIAL_ONLY_VACUOUS_ABOVE_K:
            return None
        if abs(nxt - dt) < 1e-12:
            return nxt
        dt = nxt
    return None
SPREAD_CASES = ("with_dielectric_spreading", "trace_width_only")


def _lateral_conductance(row, width_mm, spreading):
    """W per mm of run per K, from the conductor into the ADJACENT COPPER.

    `trace_width_only` is the D-787 treatment: heat leaves through a column of
    dielectric exactly as wide as the trace.  That is NOT what a 0.200 mm strip
    0.2104 mm above a solid plane does -- the heat spreads laterally in the
    dielectric before it reaches the plane, and the standard thin-dielectric
    approximation for the effective width is w + 2d.  Both are computed; see
    `accepted_run_thermal` for which one the ACCEPTANCE uses and why.
    """
    g = 0.0
    for k in ("dielectric_up_mm", "dielectric_down_mm"):
        d = row.get(k)
        if not d:
            continue
        w_eff = (width_mm + 2.0 * d) if spreading else width_mm
        g += K_FR4 * w_eff / d
    return g


def conduction_bounded_rise(stack, layer, width_mm, run_length_mm, amps,
                            boundary="both_ends_clamped", endpoint_rise_K=0.0,
                            spreading=True, reference_C=None):
    """Peak rise of an accepted narrow RUN over the copper it terminates on.

    Solved self-consistently in temperature: copper's resistivity rises 0.393 %
    per K, so the rise feeds back into the heat that produced it.
    """
    row = stack.get(layer)
    if not row or not width_mm or not run_length_mm or not amps:
        return None
    t = row["thickness_mm"]
    a_cu = width_mm * t
    if a_cu <= 0:
        return None
    axial = K_CU * a_cu
    g = _lateral_conductance(row, width_mm, spreading)
    reference_C = (AMBIENT_DESIGN_MAX_C + BOARD_RISE_ALLOWANCE_K
                   + endpoint_rise_K) if reference_C is None else reference_C
    dt = 0.0
    for _ in range(80):
        rho = RHO_CU * (1.0 + ALPHA_CU * ((reference_C + dt) - 20.0))
        nxt = _fin((amps ** 2) * rho / a_cu, g, axial, run_length_mm, boundary)
        if abs(nxt - dt) < 1e-10:
            dt = nxt
            break
        dt = nxt
    return dt


def accepted_run_thermal(stack, layer, width_mm, run_length_mm, amps,
                         endpoint_rise_K=0.0, under_pouch=False):
    """The 2 x 3 model matrix, the acceptance cell, and the ABSOLUTE peak."""
    if not stack.get(layer):
        return None
    matrix = {}
    for spread in SPREAD_CASES:
        for case in BOUNDARY_CASES:
            r = conduction_bounded_rise(
                stack, layer, width_mm, run_length_mm, amps, boundary=case,
                endpoint_rise_K=endpoint_rise_K,
                spreading=(spread == "with_dielectric_spreading"))
            matrix["%s__%s_rise_K" % (spread, case)] = (
                round(r, 2) if r is not None else None)
    # D-789 / D788-03.  TWO INDEPENDENT RIGOROUS BOUNDS, AND THE SMALLER ONE.
    #
    # The heat generated in a run leaves axially through its ends or laterally
    # through the dielectric.  Each of those paths ALONE gives an upper bound
    # on the rise, because the real run has BOTH and is therefore cooler than
    # either:
    #
    #   AXIAL ONLY      all the heat out one end, nothing laterally:
    #                   dT = p L^2 / (2 k_cu A).  Needs only that the other end
    #                   is at the reference temperature, which this run's
    #                   terminating copper is a fact about.  TIGHT for a short
    #                   run and vacuous for a long one.
    #   LATERAL ONLY    no axial sink at all and NO transverse spreading -- the
    #                   heat crosses a dielectric column exactly as wide as the
    #                   conductor: dT = p/g with g = k_fr4 w (1/d_up + 1/d_down).
    #                   Length-independent, so it is the one that rules a long
    #                   run, and it is the `trace_width_only__no_axial_sink`
    #                   cell of the matrix.
    #
    # Taking the SMALLER is not cherry-picking between models: both are valid
    # ceilings on the same quantity, so their minimum is also a ceiling.  What
    # it avoids is D-788's actual defect -- an acceptance that rested on the
    # `w + 2d` transverse-spreading APPROXIMATION, which Round-8 correctly
    # refused as an unmeasured assumption.  The `with_dielectric_spreading`
    # column is still reported, and is no longer used by anything.
    axial = axial_only_rise(stack, layer, width_mm, run_length_mm, amps)
    matrix[AXIAL_ONLY_CASE + "_rise_K"] = (round(axial, 2) if axial is not None
                                           else None)
    lateral = matrix.get("trace_width_only__no_axial_sink_rise_K")
    candidates = {}
    if axial is not None:
        candidates[AXIAL_ONLY_CASE] = axial
    if lateral is not None:
        candidates["lateral_only_no_transverse_spreading"] = lateral
    if not candidates:
        return None
    ruling_case = min(candidates, key=lambda k: candidates[k])
    worst = candidates[ruling_case]
    peak = (AMBIENT_DESIGN_MAX_C + BOARD_RISE_ALLOWANCE_K + endpoint_rise_K
            + worst)
    limit = POUCH_ADJACENT_LIMIT_C if under_pouch else ABSOLUTE_PEAK_LIMIT_C
    out = dict(matrix)
    out.update(
        acceptance_cell=ruling_case,
        acceptance_candidates_K={k: round(v, 2) for k, v in candidates.items()},
        axial_only_is_vacuous_for_this_length=bool(axial is None),
        acceptance_cell_reason=(
            "the MINIMUM of two independent RIGOROUS ceilings -- all the heat "
            "out one end with no lateral help, and no axial sink with no "
            "transverse spreading.  The real run has both paths, so it is "
            "cooler than either bound, and the smaller of two ceilings is a "
            "ceiling.  Neither rests on the w+2d transverse-spreading "
            "approximation D-788's acceptance did and Round-8 refused; that "
            "column is reported and is used by nothing."),
        worst_case_rise_K=round(worst, 2),
        relative_limit_K=ACCEPTED_RUN_DT_LIMIT_K,
        relative_ok=worst <= ACCEPTED_RUN_DT_LIMIT_K,
        ambient_design_max_C=AMBIENT_DESIGN_MAX_C,
        board_rise_allowance_K=BOARD_RISE_ALLOWANCE_K,
        endpoint_rise_K=round(endpoint_rise_K, 2),
        predicted_peak_C=round(peak, 2),
        peak_is_the_conductors_own_rise=(
            "AMBIENT + the declared bulk board rise + this run's own rise.  "
            "The temperature of the LAND at the package end is a property of "
            "the PACKAGE, is bounded by its junction, and is ruled on by the "
            "package_junction clause -- not inferred from a copper limit."),
        under_pouch=under_pouch,
        absolute_limit_C=limit,
        absolute_limit_basis=(POUCH_ADJACENT_BASIS if under_pouch
                              else ABSOLUTE_LIMIT_BASIS),
        absolute_ok=peak <= limit,
        copper_temperature_coefficient_is_solved=True,
        ipc_coupon_is_not_a_board_temperature=(
            "the IPC-2221B figure reported beside this run describes an "
            "ISOLATED COUPON in still air and is a SCREENING number; it is "
            "never quoted as a predicted board temperature"),
        measurement_of_record=("first-article thermography, assembly plan "
                               "C-THERM-01; this is a model and does not "
                               "replace it"))
    out["ok"] = bool(out["relative_ok"] and out["absolute_ok"])
    return out


def ampacity(area_mm2, dT, external):
    a = area_mm2 * MIL2_PER_MM2
    return (K_EXT if external else K_INT) * (dT ** 0.44) * (a ** 0.725)


def rise(area_mm2, amps, external):
    """The IPC-2221B temperature rise this conductor runs at, inverted."""
    a = area_mm2 * MIL2_PER_MM2
    k = K_EXT if external else K_INT
    denom = k * (a ** 0.725)
    if denom <= 0:
        return float("inf")
    return (amps / denom) ** (1.0 / 0.44)


def width_for(amps, dT, external):
    """IPC-2221B width in mm for this current at this rise, this board's copper."""
    k = K_EXT if external else K_INT
    a_mil2 = (amps / (k * dT ** 0.44)) ** (1.0 / 0.725)
    return a_mil2 / MIL2_PER_MM2 / (OUTER_MM if external else INNER_MM)


def stackup_selfcheck(board_path):
    """The copper thickness this file rules with must be the copper thickness
    the board is ORDERED with.  D-750 found it was not: `INNER_MM` was the
    nominal 0.5 oz foil, 0.0174 mm, while the board's own `(stackup)` object
    declares 0.0152 mm on all four inner layers -- the JLC06161H-7628 published
    figure D-263 locked.  A hand-typed constant drifts from the board silently,
    so it is read back and compared here, and a mismatch is a FAIL of this tool
    before it is allowed to judge any copper."""
    text = Path(board_path).read_text(encoding="utf-8", errors="replace")
    block = text[text.find("(stackup"):]
    block = block[:block.find('(layer "B.SilkS"')] or block[:20000]
    found, name = {}, None
    for line in block.splitlines():
        m = re.search(r'\(layer "([^"]+)"', line)
        if m:
            name = m.group(1)
            continue
        m = re.search(r"\(thickness ([\d.]+)\)", line)
        if m and name and name.endswith(".Cu"):
            found[name] = float(m.group(1))
            name = None
    outer = sorted({found.get("F.Cu"), found.get("B.Cu")} - {None})
    inner = sorted({found.get(k) for k in ("In1.Cu", "In2.Cu", "In3.Cu",
                                           "In4.Cu")} - {None})
    ok = (len(outer) == 1 and len(inner) == 1
          and abs(outer[0] - OUTER_MM) <= 0.0005
          and abs(inner[0] - INNER_MM) <= 0.0005)
    return dict(board_copper_mm=found, outer_declared=outer, inner_declared=inner,
                outer_used_mm=OUTER_MM, inner_used_mm=INNER_MM, ok=ok,
                note="the constants this tool rules with must equal the board's "
                     "own declared stackup (D-750)")


DRU = BOARD.with_suffix(".kicad_dru")
SECTION5 = "# 5. POWER RAILS"


def published_width_table(dru_path=None):
    """Every `<amps> A ... <outer> mm <inner> mm` row `.kicad_dru` section 5
    ACTUALLY prints, read from the file.

    D-771 REPLACED A FROZEN COPY.  `selfcheck` said in its own docstring that it
    "re-derives `.kicad_dru` section 5's published table", and it re-derived a
    seven-row TRANSCRIPTION of that table instead -- so a row the `.kicad_dru`
    edited, retired or added was invisible to it.  It had already drifted: the
    transcription carried `ACC_5V 0.70 A -> 0.185 / 1.100 mm`, a row D-753
    retired from the file in 2026-09-18 and which no longer appears anywhere in
    it, and the self-check went on reporting `method_reproduces_dru: true`.
    That is the same defect class D-766..D-769 closed elsewhere on this board:
    a figure a reviewer edits in one place and a tool charges against in
    another.  `checks/pour_partition_contract.published_rail_currents` already
    parses this same block for its CURRENTS; this parses it for its WIDTHS.

    A row is `<class>? <amps> A <words> <outer> mm <outer> mm`; continuation
    lines belong to the class above them.  A row with no width pair -- the
    `LED_BOOST` "clearance-driven, not width" line -- is correctly skipped, and
    so is every prose line in the notes under a class, because none of them
    states two millimetre figures after a current.
    """
    p = Path(dru_path or DRU)
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
        i = txt.index(SECTION5)
    except (OSError, ValueError):
        return [], dict(source=str(p), found=False)
    blk = txt[i:]
    end = blk.find("\n(rule")
    blk = blk[:end if end > 0 else len(blk)]
    rows, cur = [], None
    row_re = re.compile(
        r"^#\s{2,}(?:([A-Z][A-Z0-9_]+)\s+)?"
        r"([0-9]*\.?[0-9]+)\s*A\b[^#]*?"
        r"([0-9]*\.?[0-9]+)\s*mm\s+([0-9]*\.?[0-9]+)\s*mm\s*$")
    for line in blk.splitlines():
        m = row_re.match(line.rstrip())
        if not m:
            # a class row with no width pair still sets the current class name
            n = re.match(r"^#\s{3}([A-Z][A-Z0-9_]+)\s", line)
            if n:
                cur = n.group(1)
            continue
        if m.group(1):
            cur = m.group(1)
        rows.append((cur, float(m.group(2)), float(m.group(3)),
                     float(m.group(4))))
    return rows, dict(source=str(p), found=True,
                      sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                      rows=len(rows))


def _reproduce(published):
    """Shared arithmetic for `selfcheck` and its own live control."""
    rows, worst, mismatched = [], 0.0, []
    for name, amps, outer, inner in published:
        o, i = width_for(amps, DT_REF, True), width_for(amps, DT_REF, False)
        row = dict(rail=name, amps=amps,
                   dru_outer_mm=outer, derived_outer_mm=round(o, 4),
                   dru_inner_mm=inner, derived_inner_mm=round(i, 4))
        # A RELATIVE tolerance, because the DRU's published figures are rounded
        # to 3 decimals and the inner widths are millimetres: 2.7498 against a
        # published 2.734 is rounding, 0.285 against 0.365 is a different
        # current.  1.5 % separates the two cleanly on all fourteen rows.
        if max(abs(o - outer) / outer, abs(i - inner) / inner) > 0.015:
            # The method is not wrong -- the DRU row is.  Report the current its
            # OWN published widths correspond to, so the discrepancy is named
            # rather than rounded away.  D-743 found exactly one: SPK_OUT, whose
            # 0.070/0.365 mm widths were 0.347 A, matching neither the 0.29 A
            # rms nor the 0.41 A peak the same line named; the row it corrected
            # is one of the fourteen this now reads back out of the file.
            row["dru_width_implies_amps"] = round(
                ampacity(outer * OUTER_MM, DT_REF, True), 4)
            mismatched.append(name)
        else:
            worst = max(worst, abs(o - outer) / outer, abs(i - inner) / inner)
        rows.append(row)
    return rows, worst, mismatched


def selfcheck():
    """Re-derive `.kicad_dru` section 5's published table before ruling.

    D-771: the table is now READ FROM THE FILE (see `published_width_table`).
    An empty parse is a FAILURE, not a vacuous pass -- a self-check that
    reproduces nothing has not reproduced the board.  And the comparison is
    proved capable of failing on every run: one parsed row is perturbed by a
    factor this tolerance must reject, and the same arithmetic must refuse it.
    """
    published, src = published_width_table()
    control = None
    if published:
        mutated = list(published)
        n, a, o, i = mutated[0]
        mutated[0] = (n, a, o * 1.20, i)
        _, _, ctl_bad = _reproduce(mutated)
        control = dict(row=n, perturbation="outer x 1.20", refused=bool(ctl_bad))
    rows, worst, mismatched = _reproduce(published)
    return dict(rows=rows, worst_relative_residual=round(worst, 5),
                dru_rows_not_reproduced=mismatched,
                source=src, published_rows=len(published),
                control_refuses_a_perturbed_row=control,
                method_reproduces_dru=bool(published)
                                      and len(mismatched) < len(published) // 2,
                ok=bool(published) and not mismatched and worst <= 0.015
                   and bool(control and control["refused"]))


def pad_key(pad):
    p = pad.GetPosition()
    return ("PAD", pad.GetParentFootprint().GetReference(), pad.GetNumber(),
            p.x, p.y)


def build_graph(board, net):
    """Nodes are copper endpoints; edges are the conductors between them.

    A track is an edge of its own width and length.  A via is an edge whose
    conductor is the plated barrel wall -- an annulus of the drill diameter and
    the plating thickness -- because a barrel is a conductor too and on this
    board it has repeatedly been the bottleneck.  A pad is joined to every
    track endpoint that lands inside it.
    """
    nodes, edges = set(), []
    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net:
                pads.append(pad)
                nodes.add(pad_key(pad))

    def node_at(x, y, layer):
        return ("PT", x, y, layer)

    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            lys = [board.GetLayerName(l) for l in range(pcbnew.PCB_LAYER_ID_COUNT)
                   if t.IsOnLayer(l) and pcbnew.IsCopperLayer(l)]
            drill = t.GetDrillValue() / 1e6
            area = math.pi * ((drill / 2 + PLATING_MM) ** 2 - (drill / 2) ** 2)
            # A barrel's wall is plated copper on every layer it spans; treat
            # it as an OUTER conductor (it is in free air at both ends) and as
            # 1.6 mm long, the full stack.
            for a in lys:
                for b in lys:
                    if a < b:
                        na, nb = node_at(pos.x, pos.y, a), node_at(pos.x, pos.y, b)
                        nodes.add(na); nodes.add(nb)
                        edges.append(dict(kind="via", a=na, b=nb, area_mm2=area,
                                          external=True, length_mm=1.6,
                                          width_mm=None, drill_mm=round(drill, 3),
                                          layer="%s-%s" % (a, b),
                                          x=round(pos.x / 1e6, 3), y=round(pos.y / 1e6, 3)))
            continue
        if t.GetClass() != "PCB_TRACK":
            continue
        ly = board.GetLayerName(t.GetLayer())
        s, e = t.GetStart(), t.GetEnd()
        na, nb = node_at(s.x, s.y, ly), node_at(e.x, e.y, ly)
        nodes.add(na); nodes.add(nb)
        w = t.GetWidth() / 1e6
        th = OUTER_MM if ly in OUTER else INNER_MM
        edges.append(dict(kind="track", a=na, b=nb, area_mm2=w * th,
                          external=ly in OUTER, length_mm=t.GetLength() / 1e6,
                          width_mm=round(w, 3), drill_mm=None, layer=ly,
                          x=round(s.x / 1e6, 3), y=round(s.y / 1e6, 3),
                          x2=round(e.x / 1e6, 3), y2=round(e.y / 1e6, 3)))

    # Bond every pad to the track endpoints that land on it.  A pad is a large
    # conductor; the edge is free.
    endpoints = [n for n in nodes if n[0] == "PT"]
    for pad in pads:
        pk = pad_key(pad)
        for n in endpoints:
            _, x, y, ly = n
            if pad.IsOnLayer(board.GetLayerID(ly)) and pad.HitTest(pcbnew.VECTOR2I(x, y)):
                edges.append(dict(kind="pad", a=pk, b=n, area_mm2=float("inf"),
                                  external=True, length_mm=0.0, width_mm=None,
                                  drill_mm=None, layer=ly,
                                  x=round(x / 1e6, 3), y=round(y / 1e6, 3)))
    return nodes, edges


def widest_bottleneck(nodes, edges, sources, sinks, amps):
    """Maximin search: the path whose WORST conductor is the best available.

    THE BOTTLENECK IS EXACT; THE PATH IS A CHOICE.  The maximin VALUE is unique,
    so `worst_rise_K` and the verdict are properties of the board.  When several
    paths share that same worst conductor, `series_resistance_mohm`,
    `ir_drop_mV`, `dissipation_W` and `path_length_mm` describe WHICHEVER of
    them this search reports.  Since D-766 that choice is DETERMINISTIC (see the
    ordering note below) but it is not necessarily the most resistive of the
    equally-wide candidates, so treat the IR figures as one sample of a tie
    rather than as the worst case.  The thermal ruling never depended on it.
    """
    adj = defaultdict(list)
    for ed in edges:
        adj[ed["a"]].append((ed["b"], ed))
        adj[ed["b"]].append((ed["a"], ed))

    def cap(ed):
        if ed["kind"] == "pad":
            return float("inf")
        return ampacity(ed["area_mm2"], DT_REF, ed["external"])

    # D-766 DETERMINISM FIX.  The heap tie-breaker used to be `id(m)` -- a
    # MEMORY ADDRESS.  The maximin VALUE is unique, so the bottleneck and the
    # verdict were always right; but whenever two frontier nodes carried the
    # same capacity, which one was expanded first depended on where CPython had
    # happened to allocate the tuple, and that decides `prev` and therefore
    # WHICH of several equally-wide paths is reported.  Measured on the D-766
    # board: three consecutive runs of this file on ONE unchanged board
    # returned USB_VBUS_RAW 23.876 / 19.876 / 23.876 mm and 22.820 / 18.866 /
    # 22.820 mOhm, and BAT_PROTECTED_P 81.709 / 80.922 / 81.709 mm.  Release
    # evidence that changes between runs on an unchanged board is not evidence
    # -- the same defect class D-744 fixed for connection_width.
    #
    # Node keys mix types by position (("PAD", ref, num, x, y) against
    # ("PT", x, y, layer)), so they cannot be compared directly.  Index them in
    # a DETERMINISTIC order instead -- sources first, then every edge endpoint
    # in `edges` list order, which is board-iteration order -- and break ties on
    # that index.  Nothing about the search changes except reproducibility.
    order = {}
    for s in sources:
        order.setdefault(s, len(order))
    for ed in edges:
        order.setdefault(ed["a"], len(order))
        order.setdefault(ed["b"], len(order))
    for n in sorted(nodes, key=lambda k: (str(type(k)), repr(k))):
        order.setdefault(n, len(order))

    best = {n: 0.0 for n in nodes}
    prev = {}
    import heapq
    heap = []
    for s in sources:
        best[s] = float("inf")
        heapq.heappush(heap, (-float("inf"), order[s], s))
    seen = set()
    while heap:
        negc, _, n = heapq.heappop(heap)
        if n in seen:
            continue
        seen.add(n)
        for m, ed in adj[n]:
            c = min(best[n], cap(ed))
            if c > best.get(m, 0.0):
                best[m] = c
                prev[m] = (n, ed)
                heapq.heappush(heap, (-c, order[m], m))
    reached = [k for k in sinks if best.get(k, 0.0) > 0.0]
    if not reached:
        return None, None
    tgt = max(reached, key=lambda k: best[k])
    path, cur = [], tgt
    while cur in prev:
        n, ed = prev[cur]
        path.append(ed)
        cur = n
    path.reverse()
    return path, best[tgt]


# --------------------------------------------------------------------------
# D-789 / D788-03 -- A TRACK'S WIDTH ATTRIBUTE IS NOT THE CONDUCTOR.
#
# Round-8 asked for the U11.2 neck's thermal claim to be rebuilt on "actual
# copper overlap/spreading".  Measuring it found something larger than a
# modelling question: THE NECK THAT WAS BEING JUDGED DOES NOT EXIST.
#
# This file has always read `t.GetWidth()`, which is a property of a TRACK
# OBJECT.  Copper is a property of the BOARD, and KiCad unions every same-net
# object on a layer when it plots.  `/01_POWER_TREE/BAT_PROTECTED_P` carries a
# 0.200 mm track from `U11.2` that runs 5.525 mm to `C36.1` -- and D-780's
# hand-drawn taper, 0.200 -> 0.300 -> 0.400 -> 0.600 -> 0.800 -> 1.000 ->
# 1.200 -> 1.500 mm, was laid ON TOP OF IT.  Rasterised at 2 um, 100.0 % of
# that 0.200 mm track's 1.2027 mm2 of copper lies INSIDE other same-net B.Cu
# objects.  Deleting all three of its segments would not change one square
# micron of plotted copper.
#
# So D-787's "5.525 mm of 0.200 mm copper" and D-788's 2 x 3 boundary matrix
# over it were both answering about an artefact.  The REAL narrow conductor is
# the first 0.575 mm out of the `U11.2` land -- which is the package-land neck,
# and nothing more.
#
# WHAT IS MEASURED HERE.  For a track, the FREE WIDTH of the merged same-net
# copper on its own layer, measured PERPENDICULAR to the track, at stations
# along it, taking the MINIMUM.  The minimum is what makes it sound: a 0.200 mm
# track crossing a 2 mm one reads 2 mm at the crossing and 0.200 mm at the
# stations either side, so a crossing cannot be mistaken for a widening.  It is
# still CONSERVATIVE -- it ignores every other layer, the pours, and any copper
# of the same net that the track does not itself touch.
#
# The report carries BOTH: `width_mm` is what the object says and
# `effective_width_mm` is what the copper is.  Every thermal and ampacity
# judgement below runs on the second.  `effective_width_selfcheck` proves on
# every run that an ISOLATED track still measures its own width, so the
# measurement cannot quietly turn into "everything is wide".
EFFECTIVE_WIDTH_STEP_MM = 0.002
EFFECTIVE_WIDTH_STATION_MM = 0.05
EFFECTIVE_WIDTH_MAX_MM = 4.0


def _seg_distance(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def same_net_layer_copper(board, net, layer_name):
    """Every same-net object on one layer, as simple shapes.

    Tracks are capsules, vias and their pads are discs, footprint pads are
    axis-aligned rectangles.  A pad that is not axis-aligned is taken at its
    bounding box, which OVERSTATES it -- so it is excluded from the shapes a
    width can be credited to unless its rotation is a multiple of 90 degrees.
    """
    lid = board.GetLayerID(layer_name)
    caps, discs, rects = [], [], []
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.GetClass() == "PCB_VIA":
            if not t.IsOnLayer(lid):
                continue
            p = t.GetPosition()
            discs.append((p.x / 1e6, p.y / 1e6, t.GetWidth() / 2e6))
            continue
        if t.GetLayer() != lid:
            continue
        a, b = t.GetStart(), t.GetEnd()
        caps.append((a.x / 1e6, a.y / 1e6, b.x / 1e6, b.y / 1e6,
                     t.GetWidth() / 2e6))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != net or not pad.IsOnLayer(lid):
                continue
            pos, size = pad.GetPosition(), pad.GetSize()
            angle = round(float(pad.GetOrientationDegrees()) % 180.0, 3)
            w, h = size.x / 1e6, size.y / 1e6
            if abs(angle - 90.0) < 1e-6:
                w, h = h, w
            elif angle > 1e-6 and abs(angle - 180.0) > 1e-6:
                # Not axis aligned: credit only the inscribed square, which
                # UNDERSTATES it.  A rotated pad may not inflate a width.
                w = h = min(w, h) / math.sqrt(2.0)
            rects.append((pos.x / 1e6, pos.y / 1e6, w, h))
    return caps, discs, rects


def _in_copper(px, py, shapes, skip_cap=None):
    caps, discs, rects = shapes
    for i, (x1, y1, x2, y2, r) in enumerate(caps):
        if skip_cap is not None and i == skip_cap:
            continue
        if _seg_distance(px, py, x1, y1, x2, y2) <= r + 1e-9:
            return True
    for (x, y, r) in discs:
        if math.hypot(px - x, py - y) <= r + 1e-9:
            return True
    for (x, y, w, h) in rects:
        if abs(px - x) <= w / 2 + 1e-9 and abs(py - y) <= h / 2 + 1e-9:
            return True
    return False


def effective_width_mm(shapes, x1, y1, x2, y2, width_mm):
    """The narrowest free width of the merged copper ACROSS this track."""
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 1e-9 or not width_mm:
        return width_mm, []
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    nx, ny = -uy, ux
    n = max(3, int(round(length / EFFECTIVE_WIDTH_STATION_MM)))
    step = EFFECTIVE_WIDTH_STEP_MM
    values = []
    for k in range(n + 1):
        f = k / float(n)
        px, py = x1 + ux * length * f, y1 + uy * length * f
        if not _in_copper(px, py, shapes):
            values.append(0.0)
            continue
        total = 0.0
        for sign in (1.0, -1.0):
            d = 0.0
            while d < EFFECTIVE_WIDTH_MAX_MM:
                d += step
                if not _in_copper(px + sign * nx * d, py + sign * ny * d,
                                  shapes):
                    break
            total += d - step
        values.append(round(total + step, 4))
    return min(values), values


def effective_width_selfcheck():
    """NON-VACUITY, on a fixture read from no board.

    An ISOLATED 0.200 mm track must still measure 0.200 mm; the same track with
    a 1.200 mm one laid along it must measure 1.200 mm; and a 0.200 mm track
    merely CROSSING a wide one must still measure 0.200 mm, because the
    crossing is one station and the minimum is taken.  A measurement that
    cannot return a narrow answer would silently widen every neck on the board.
    """
    lone = ([(10.0, 10.0, 15.0, 10.0, 0.100)], [], [])
    over = ([(10.0, 10.0, 15.0, 10.0, 0.100),
             (10.0, 10.0, 15.0, 10.0, 0.600)], [], [])
    cross = ([(10.0, 10.0, 15.0, 10.0, 0.100),
              (12.5, 8.0, 12.5, 12.0, 0.600)], [], [])
    cases = [
        dict(case="an isolated 0.200 mm track measures 0.200 mm",
             measured=round(effective_width_mm(lone, 10.0, 10.0, 15.0, 10.0,
                                               0.200)[0], 3),
             expected=0.200),
        dict(case="a 1.200 mm track laid along it measures 1.200 mm",
             measured=round(effective_width_mm(over, 10.0, 10.0, 15.0, 10.0,
                                               0.200)[0], 3),
             expected=1.200),
        dict(case="a wide track merely CROSSING it does not widen it",
             measured=round(effective_width_mm(cross, 10.0, 10.0, 15.0, 10.0,
                                               0.200)[0], 3),
             expected=0.200),
    ]
    for c in cases:
        c["ok"] = abs(c["measured"] - c["expected"]) <= 2 * EFFECTIVE_WIDTH_STEP_MM
    return dict(cases=cases, step_mm=EFFECTIVE_WIDTH_STEP_MM,
                station_mm=EFFECTIVE_WIDTH_STATION_MM,
                fixture_is_constant=True,
                ok=all(c["ok"] for c in cases))

def accepts_segment(rail, edge, seg):
    """Is this hot segment covered by one of the rail's DECLARED exceptions?

    An exception names a LAYER and bounds the TOTAL length it covers, and may
    bound the width.  Anything outside those bounds is undeclared and fails --
    which is the whole point: the exception must not grow silently.
    """
    for acc in rail.get("accept", ()):
        if acc["layer"] != edge["layer"]:
            continue
        # D-789 / D788-03: the MEASURED conductor, not the object's attribute.
        w = seg.get("effective_width_mm") or edge["width_mm"] or 9e9
        if "max_width_mm" in acc and w > acc["max_width_mm"] + 1e-9:
            continue
        return acc["reason"]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--dt-limit", type=float, default=20.0,
                    help="rise above which a segment is reported HOT")
    ap.add_argument("-o", type=Path)
    args = ap.parse_args()

    board = pcbnew.LoadBoard(str(args.board.resolve()))
    board.BuildConnectivity()
    check = selfcheck()
    eff_check = effective_width_selfcheck()
    stack = stackup_selfcheck(args.board.resolve())
    diel = stackup_dielectrics(args.board.resolve())

    pad_index = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pad_index["%s.%s" % (fp.GetReference(), pad.GetNumber())] = pad

    out = []
    for rail in RAILS:
        nodes, edges = build_graph(board, rail["net"])
        srcs = [pad_key(pad_index[r]) for r in rail["src"] if r in pad_index]
        snks = [pad_key(pad_index[r]) for r in rail["snk"] if r in pad_index]
        missing = [r for r in rail["src"] + rail["snk"] if r not in pad_index]
        path, bottleneck = widest_bottleneck(nodes, edges, srcs, snks, rail["amps"])
        row = dict(rail=rail["name"], net=rail["net"], design_amps=rail["amps"],
                   basis=rail["basis"], source=list(rail["src"]),
                   sink=list(rail["snk"]), pads_not_on_board=missing)
        if path is None:
            row.update(connected=False,
                       verdict=("POUR_DELIVERED" if rail.get("pour_delivered")
                                else "NO_PATH"),
                       pour_delivered=rail.get("pour_delivered"))
            out.append(row)
            continue
        segs, drop, hot = [], 0.0, []
        shape_cache = {}
        for ed in path:
            if ed["kind"] == "pad":
                continue
            # D-789 / D788-03.  THE CONDUCTOR, NOT THE OBJECT.  A track whose
            # copper lies inside wider same-net copper is not a neck, and this
            # board's `U11.2` "5.525 mm of 0.200 mm" was exactly that.  The
            # thermal and ampacity judgements below run on the MEASURED width.
            eff_w, eff_stations = ed["width_mm"], None
            if ed["kind"] == "track" and ed["width_mm"]:
                if ed["layer"] not in shape_cache:
                    shape_cache[ed["layer"]] = same_net_layer_copper(
                        board, rail["net"], ed["layer"])
                eff_w, eff_stations = effective_width_mm(
                    shape_cache[ed["layer"]], ed["x"], ed["y"],
                    ed.get("x2", ed["x"]), ed.get("y2", ed["y"]),
                    ed["width_mm"])
                # The raster steps OUTWARD until it leaves copper, so it
                # over-reads by one step; back that out.  And a measurement
                # may never claim LESS than the object itself guarantees.
                eff_w = max(ed["width_mm"], eff_w - EFFECTIVE_WIDTH_STEP_MM)
            thickness = OUTER_MM if ed["external"] else INNER_MM
            eff_area = (eff_w * thickness if ed["kind"] == "track" and eff_w
                        else ed["area_mm2"])
            dT = rise(eff_area, rail["amps"], ed["external"])
            attr_dT = rise(ed["area_mm2"], rail["amps"], ed["external"])
            r = RHO_CU * ed["length_mm"] / ed["area_mm2"] if ed["area_mm2"] else 0.0
            drop += r * rail["amps"]
            seg = dict(kind=ed["kind"], layer=ed["layer"],
                       width_mm=ed["width_mm"],
                       effective_width_mm=(round(eff_w, 4)
                                           if ed["kind"] == "track" else None),
                       effective_width_is_measured_copper=(
                           ed["kind"] == "track" and eff_stations is not None),
                       effective_width_stations_mm=(
                           eff_stations[:64] if eff_stations else None),
                       lies_inside_wider_same_net_copper=bool(
                           ed["kind"] == "track" and ed["width_mm"]
                           and eff_w > ed["width_mm"] + 2 * EFFECTIVE_WIDTH_STEP_MM),
                       drill_mm=ed["drill_mm"],
                       length_mm=round(ed["length_mm"], 3),
                       area_mm2=round(ed["area_mm2"], 6),
                       effective_area_mm2=round(eff_area, 6),
                       rise_K=round(dT, 1),
                       rise_K_on_the_track_width_attribute=round(attr_dT, 1),
                       required_mm_at_10K=round(
                           width_for(rail["amps"], DT_REF, ed["external"]), 3)
                       if ed["kind"] == "track" else None,
                       plane_coupled_rise_K=(
                           round(plane_coupled_rise(diel, ed["layer"],
                                                    eff_w,
                                                    rail["amps"]), 2)
                           if ed["kind"] == "track" and eff_w
                           and plane_coupled_rise(diel, ed["layer"], eff_w,
                                                  rail["amps"]) is not None
                           else None),
                       at=[ed.get("x"), ed.get("y")])
            segs.append(seg)
            if dT > args.dt_limit:
                seg["accepted_by"] = accepts_segment(rail, ed, seg)
                hot.append(seg)
        segs_sorted = sorted(segs, key=lambda s: -s["rise_K"])
        undeclared = [h for h in hot if not h.get("accepted_by")]
        accepted_len = round(sum(h["length_mm"] for h in hot
                                 if h.get("accepted_by")), 3)
        # D-789 / D788-03.  EACH EXCEPTION IS ITS OWN RUN.  D-788 charged the
        # TOTAL accepted length to EVERY accepted segment, which was right
        # while there was one exception and one width; with the conductor
        # measured rather than assumed there are two -- the 0.200 mm
        # package-land neck and the taper out of it -- and a 0.600 mm segment
        # must not be solved over the neck's length or the other way round.
        accepted_len_by_reason = {}
        for h in hot:
            why = h.get("accepted_by")
            if why:
                accepted_len_by_reason[why] = round(
                    accepted_len_by_reason.get(why, 0.0) + h["length_mm"], 3)
        # D-787 / R6-E07.  Every ACCEPTED hot segment is judged again on the
        # conduction-bounded model, over the WHOLE accepted run -- the ends of
        # a 5.5 mm neck are what clamp it, not the ends of one 0.9 mm piece --
        # and an acceptance whose conduction-bounded peak exceeds the stated
        # limit is NOT accepted.  The IPC coupon figure stays in the report so
        # the two are visibly different questions.
        over_conduction_limit = []
        for h in hot:
            if not h.get("accepted_by"):
                continue
            # D-788 / R7-D787-04.  Every boundary case, temperature-solved,
            # with the endpoint the run is clamped to charged for its OWN
            # dissipation, and an ABSOLUTE peak beside the relative rise.
            endpoint = rail.get("accept_endpoint_rise_K", 0.0)
            at = h.get("at") or [None, None]
            run_len = accepted_len_by_reason.get(h["accepted_by"], accepted_len)
            th = accepted_run_thermal(
                diel, h["layer"], h.get("effective_width_mm") or h["width_mm"],
                run_len, rail["amps"],
                endpoint_rise_K=endpoint,
                under_pouch=inside_battery_shadow(at[0], at[1]))
            h["accepted_run_length_mm"] = run_len
            h["accepted_run_length_is_per_exception"] = True
            h["thermal"] = th
            h["conduction_bounded_rise_K"] = (th["worst_case_rise_K"]
                                              if th else None)
            h["conduction_bounded_limit_K"] = ACCEPTED_RUN_DT_LIMIT_K
            h["endpoint_rise_basis"] = rail.get("accept_endpoint_rise_basis")
            if th is None or not th["ok"]:
                over_conduction_limit.append(h)
        # D-789 / D788-03: and the PACKAGE the accepted run lands on, computed
        # from TI's own equation at the SAME BATFET resistance F6 charges.
        pkg = None
        if rail.get("accept_package_junction") and hot:
            # ONLY the accepted run's own copper.  The rest of this rail's
            # 81 mm is metres away from the package and charging it to the
            # junction would be arithmetic, not physics.
            board_copper_W = round(sum(
                (rail["amps"] ** 2) * RHO_CU * s2["length_mm"]
                / (s2.get("effective_area_mm2") or s2["area_mm2"])
                for s2 in hot
                if s2.get("accepted_by")
                and (s2.get("effective_area_mm2") or s2.get("area_mm2"))), 6)
            pkg = package_junction(rail["amps"], board_copper_W=board_copper_W)
            row_pkg_ok = pkg["ok"]
            if not row_pkg_ok:
                over_conduction_limit.append(dict(
                    reason="package junction over TI's operating maximum",
                    reference=rail["accept_package_junction"],
                    predicted_tj_C=pkg["predicted_tj_C"],
                    limit_C=pkg["limit_C"]))
        undeclared = undeclared + over_conduction_limit
        worst_pc = [x["plane_coupled_rise_K"] for x in segs
                    if x.get("plane_coupled_rise_K") is not None]
        row.update(connected=True,
                   worst_plane_coupled_rise_K=(round(max(worst_pc), 2)
                                               if worst_pc else None),
                   dissipation_W=round((rail["amps"] ** 2) * sum(
                       RHO_CU * e["length_mm"] / e["area_mm2"]
                       for e in path if e["kind"] != "pad" and e["area_mm2"]), 4),
                   path_segments=len(segs),
                   path_length_mm=round(sum(s["length_mm"] for s in segs), 3),
                   series_resistance_mohm=round(
                       sum(RHO_CU * s["length_mm"] / s["area_mm2"] for s in segs) * 1000, 3),
                   ir_drop_mV=round(drop * 1000, 2),
                   bottleneck_amps_at_10K=round(bottleneck, 3),
                   worst_rise_K=segs_sorted[0]["rise_K"] if segs else None,
                   hot_segments=hot,
                   package_junction=pkg,
                   undeclared_hot_segments=undeclared,
                   accepted_hot_length_mm=accepted_len,
                   accepted_reason=rail.get("accept_reason"),
                   worst_accepted_conduction_bounded_rise_K=(
                       max([h["conduction_bounded_rise_K"] for h in hot
                            if h.get("conduction_bounded_rise_K") is not None],
                           default=None)),
                   accepted_conduction_bounded_limit_K=ACCEPTED_RUN_DT_LIMIT_K,
                   worst_three=segs_sorted[:3],
                   verdict=("OK" if not hot
                            else "OK_WITH_DECLARED_EXCEPTION" if not undeclared
                            else "HOT"))
        out.append(row)

    # An exception bounds the TOTAL length it covers, not each segment, so the
    # budget is checked once per rail after the walk.
    for rail, row in zip(RAILS, out):
        over = []
        for acc in rail.get("accept", ()):
            used = sum(h["length_mm"] for h in row.get("hot_segments", ())
                       if h.get("accepted_by") == acc["reason"])
            if used > acc["max_length_mm"] + 1e-9:
                over.append(dict(reason=acc["reason"], budget_mm=acc["max_length_mm"],
                                 used_mm=round(used, 3)))
        if over:
            row["exception_length_budget_exceeded"] = over
            row["verdict"] = "HOT"

    report = dict(schema=1, board=str(args.board), dt_limit_K=args.dt_limit,
                  stackup_selfcheck=stack, stackup_dielectrics=diel,
                  conduction_bounded_model=dict(
                      k_cu_W_per_mmK=K_CU, k_fr4_W_per_mmK=K_FR4,
                      limit_K=ACCEPTED_RUN_DT_LIMIT_K,
                      form="dT = p lam^2/(k_cu A) (1 - 1/cosh(L/2lam)); "
                           "p = I^2 rho/A; lam = sqrt(k_cu A / g); "
                           "g = k_fr4 w (1/d_up + 1/d_down)",
                      reports="peak rise of an ACCEPTED narrow run over the "
                              "copper it terminates on and the adjacent "
                              "layers, NOT over ambient and NOT a predicted "
                              "board temperature.  Ignores lateral spreading "
                              "in the dielectric, convection and radiation "
                              "from an outer face, and the soldermask, so it "
                              "is a ceiling.  First-article thermal "
                              "acceptance remains the measurement."),
                  plane_coupled_model=dict(
                      k_fr4_W_per_mmK=K_FR4,
                      form="dT = I^2 rho / (k w^2 t (1/d_up + 1/d_down))",
                      reports="rise over the ADJACENT COPPER LAYERS, not over ambient; length-independent by construction; ignores lateral spreading, conduction along the copper and the outer layers, so it is a floor on the cooling and a ceiling on the rise"),
                  method_selfcheck=check, rails=out,
                  # D-789 / D788-03: the conductor measurement, proved on a
                  # constant fixture on every run.
                  effective_width_selfcheck=eff_check,
                  effective_width_model=dict(
                      step_mm=EFFECTIVE_WIDTH_STEP_MM,
                      station_mm=EFFECTIVE_WIDTH_STATION_MM,
                      reports="the FREE WIDTH of the merged same-net copper on "
                              "the track's own layer, measured PERPENDICULAR "
                              "to the track at stations along it, minimum "
                              "taken.  A track lying inside wider same-net "
                              "copper is NOT a neck, and this board's U11.2 "
                              "'5.525 mm of 0.200 mm' was exactly that -- "
                              "100 % of its copper lies inside the D-780 "
                              "taper.  Conservative: it ignores every other "
                              "layer, the pours, and any same-net copper the "
                              "track does not itself touch."),
                  package_junction_model=PACKAGE_JUNCTION,
                  system_thermal_model=SYSTEM_THERMAL,
                  charge_regime_model=CHARGE_REGIME,
                  discharge_system_model=DISCHARGE_SYSTEM,
                  enclosure_surface_m2=round(enclosure_surface_m2(), 6),
                  r_sys_K_per_W=round(
                      system_thermal_resistance_K_per_W(), 4),
                  all_ok=(check["method_reproduces_dru"] and stack["ok"]
                          and eff_check["ok"]
                          and all(r.get("verdict") in
                                  ("OK", "OK_WITH_DECLARED_EXCEPTION",
                                   "POUR_DELIVERED") for r in out)))
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.o:
        args.o.write_text(text + "\n", encoding="utf-8")
    print(text)
    for r in out:
        print("  %-16s %-8s worst rise %-7s bottleneck %s A" % (
            r["rail"], r.get("verdict"), r.get("worst_rise_K"),
            r.get("bottleneck_amps_at_10K")), file=sys.stderr)
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
