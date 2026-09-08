#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- gated batch driver for the whole-board all-layer maze router.

`maze3d.route_net` is a PROPOSER.  This module is the AUTHORITY: it never lets
proposed copper touch `hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb`
unless every gate below passes on a scratch copy.

    1. the authoritative board is byte-identical before and after the run
       (and again immediately before a `--promote` write);
    2. every net is routed at its OWN netclass width / via / clearance, raised
       where the project DRU imposes a stricter routed minimum, and restricted
       to the layers the DRU allows that netclass;
    3. real KiCad `--refill-zones --save-board --severity-all
       --schematic-parity` DRC on the scratch board reports NO violation
       outside the three inherited classes, and the inherited class counts do
       not grow;
    4. the fitted-pad routing ledger shows the whole board's retained open
       edges strictly DECREASE and no other net regress -- measured after the
       optional `--repair-planes` stitch and its own second refill and DRC, so
       a pour a signal track split is given the barrel -- or, inside the
       stitch's own 8 mm locality window, the short track -- that re-bonds it
       before the verdict, and is still a refusal if neither exists;
    5. every pre-existing track/via signature still exists, and every ADDED
       object is on a net that SUCCEEDED -- copper is added, never moved or
       removed, and every failed net's revert is proven rather than assumed.
       The ONE exception is `--evict`, and it is an exception in bookkeeping
       only: a removal is legal solely when the object is on a NAMED evicted
       net and lies wholly inside the corridor the requested nets themselves
       define, and clause 4 then still requires that evicted net to end the
       transaction no worse off than it started;
    6. with `--plane`, the candidate's zone inventory differs from the
       authority's by exactly ONE added zone, on the requested net and layer,
       and no existing zone's net, layer, outline or fill parameters changed;
       and RULE AREAS are audited alongside pours -- none may be lost, and every
       added one must be a licence area this run's own `--bridge` emitter asked
       for, on all six copper layers, forbidding nothing.

Failing any gate the run is characterization: it prints its evidence, writes no
candidate, and leaves the authoritative board untouched.
"""

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from screen_inner_plane import (OUTLINE, insert_zone, parse_outline,
                                zone_sexpr)

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
# THE AUTHORITY IS A CONSTANT; THE BASE BOARD IS A CHOICE (D-668).
# `AUTHORITY` is the one file this module may ever WRITE, and it never moves.
# `BOARD` is the board a run READS -- its base, its ledger-before, its
# `.kicad_dru`/`.kicad_pro`, the pour-partition `--pre-board`, the board every
# removal is priced against.  Until D-668 the two were the same name, so a
# screen that offered `--board` (screen_partial_pairs.py did) took its CENSUS
# from a candidate and then drove a router that answered about the authority --
# a question and an answer about two different boards, which is how a 26.5 s
# screen came back empty on a pair that provably exists.  `--board` separates
# them; `--promote` is refused outright whenever they differ, and the
# `authority_unchanged` clause now watches BOTH files.
AUTHORITY = PROJECT / "aqroot-Beta-v2.kicad_pcb"
BOARD = AUTHORITY
LEDGER = ROOT / "hardware/demo/manufacturing/routing_ledger.py"
LOCAL_TWO_PAD = Path(__file__).with_name("route_local_two_pad.py")
# CLAUSE 8 (D-623): the pour-partition contract is invoked BY the gate.
POUR_PARTITION = Path(__file__).with_name("checks") / "pour_partition_contract.py"

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# Inherited DRC classes: present on the accepted board before any Demo routing
# and not attributable to it.  Their counts are pinned, not merely ignored.
INHERITED = {"lib_footprint_issues": 199, "hole_clearance": 5,
             "solder_mask_bridge": 1}

# Per-netclass routing contract taken from `aqroot-Beta-v2.kicad_dru`, because a
# netclass width/clearance is a DEFAULT and several DRU rules are stricter or
# forbid layers outright.  `layers=None` means "every routable layer".
#   width    -- max(netclass track width, DRU track_width min)
#   clr      -- max(netclass clearance,  DRU routed clearance min)
#   layers   -- routable layers the DRU permits for the class
#   drill    -- DRU `hole_size` min for a via on the class ("POWER-class vias
#               use the 0.40 mm drill"); a request may never go under it
#   width_cap -- the widest track this class's OWN LAND GEOMETRY can launch.
#               A netclass width is a TARGET; a pad is a fact.  Where the two
#               disagree the pad wins, because a track that cannot leave the
#               part it serves is not a route at any width.  This figure is a
#               MEASUREMENT of the board, it is asserted at import to be no
#               lower than the same class's DRU `width` floor, and it can
#               therefore never ask for copper narrower than a rule allows --
#               it only stops the proposer aiming at a width the package
#               forbids.  D-620.
DRU_CLASS = {
    "Default":      dict(clr=200000, layers=None),
    "I2C":          dict(clr=200000, layers=None),
    "I2S":          dict(clr=200000, layers=None),
    # THE THREE NFC FAMILIES CARRY LAYER CONTRACTS AND THE TABLE DID NOT SAY SO,
    # which is the USB_D lesson unlearned three more times.  `.kicad_dru`
    # section 6 states them in its own words -- "NFC crystal nets stay on
    # B.Cu", "NFC crystal nets are forbidden on In2", "NFC crystal nets carry
    # no via", and the same three for the transmit arms -- and `layers=None`
    # let the maze reach every pad on all four routable layers.  The first U9
    # fanout batch measured the consequence rather than arguing it: with
    # `NFC_VDD_A` and `NFC_VDD_D` both closed, the evicted `NFC_XOUT` came back
    # with a 0.7211 mm and a 1.3416 mm track on In2 and TWO F-to-B barrels, and
    # the authoritative gate refused the run on FOUR real `items_not_allowed`
    # reports naming those two rules.
    #
    # The fix is the one D-596 already wrote down for `USB_D`: a SINGLE-layer
    # contract makes the via inexpressible rather than merely forbidden -- the
    # maze's via move has no second layer to land on -- so the In2 prohibition
    # and the no-via rule stop being rules the proposer may break and become a
    # shape it cannot draw.  `NFC_RX` is deliberately NOT single-layer: its
    # rule disallows a TRACK on F.Cu and says nothing about vias or In2, so it
    # keeps `B` and `In2` and the barrel it is allowed to have.
    "NFC_RX":       dict(clr=200000, layers=("B", "I2")),
    "NFC_OSC":      dict(clr=200000, layers=("B",)),
    "GND":          dict(clr=200000, layers=None),
    "SPK_OUT":      dict(width=250000, clr=200000, layers=("F", "B")),
    "LED_BOOST":    dict(clr=300000, layers=None),
    "SWITCH_NODE":  dict(width=400000, clr=300000, layers=("F", "B")),
    "SYS_MAIN":     dict(width=500000, clr=250000, drill=400000, layers=None),
    "ACC_3V3":      dict(width=350000, clr=250000, drill=400000, layers=None),
    "ACC_5V":       dict(width=400000, clr=250000, drill=400000, layers=None),
    "VBUS_CHG":     dict(width=350000, clr=250000, drill=400000, layers=None),
    "NFC_5V_PA":    dict(width=350000, clr=250000, drill=400000, layers=None),
    "P3V3":         dict(width=400000, clr=200000, drill=400000, layers=None),
    "BAT_MAIN":     dict(width=600000, clr=300000, drill=400000, layers=None),
    # `clr` is 0.25 mm because section 8 says "NFC transmit arm routed
    # clearance (min 0.25mm)" and the NFC_RF NETCLASS carries only 0.20 mm --
    # the same gap the table already records for NFC_5V_PA, VBUS_CHG and the
    # ACC rails.  The width floor is the DRU's 0.30 mm; the netclass is already
    # 0.40 mm and `max()` keeps it, so the figure is stated for the record
    # rather than to lower anything.
    # WIDTH_CAP, AND IT IS ARITHMETIC RATHER THAN APPETITE.  `U9` is a
    # UFQFPN-32 at 0.500 mm pitch whose transmit-arm lands are 0.300 mm wide:
    # `U9.15` (`NFC_RFO2`) sits at x = 35.250 between `U9.14` at 34.750 and
    # `U9.16` at 35.750, so the neighbouring lands' inner edges are 34.900 and
    # 35.600 and this class owes a PAD 0.200 mm (the DRU's 0.25 mm figure is a
    # ROUTED clearance and says `A.Type != 'Pad' && B.Type != 'Pad'` in its own
    # words).  The widest track whose centre may sit on that land is therefore
    # 35.600 - 0.200 - 35.250 doubled = 0.300 mm, and it is 0.300 mm in EVERY
    # direction, because a track leaving the land starts inside the
    # neighbours' own 0.750 mm y-span.  `U9.13` (`NFC_RFO1`) is the same
    # arithmetic mirrored.  The netclass asks for 0.400 mm -- the DRU's `opt`
    # -- so `max()` made this class UNLAUNCHABLE FROM THE PART IT SERVES, and
    # both promoted arms have always been 0.300 mm.  The cap states what the
    # board can build; the DRU's 0.30 mm `min` still binds underneath it and
    # KiCad still judges the result.
    "NFC_RF":       dict(width=300000, width_cap=300000, clr=250000,
                         layers=("B",)),
    # USB_D is the one class on this board whose layer set is a SINGLE layer,
    # and the first screen that actually routed it proved why.  Given `F, B`
    # the maze reached every USB pad -- all four nets routed, 126 -> 121 open
    # edges -- and the authoritative gate then refused the run on NINE real
    # KiCad violations, all from the same root: eight `items_not_allowed`,
    # one per through via, because `USB pair is forbidden on In2` and a F-to-B
    # barrel PIERCES In2; plus one `diff_pair_uncoupled_length_too_long`,
    # because a `USB_D_CONN_P` that is free to dive to B.Cu takes 36.653 mm to
    # reach a pad 8.465 mm away and the DRU's uncoupled budget is 25 mm.
    #
    # Both are the same mistake, and `.kicad_dru` section 6 already names the
    # fix in its own heading: "USB 2.0 - FULL SPEED, ON F.Cu OVER In1, NO
    # VIAS, NO THEATRE".  On ONE routable layer the maze's via move has no
    # second layer to land on, so it cannot emit a barrel AT ALL -- the
    # In2 prohibition stops being a rule the router may break and becomes a
    # shape it cannot express -- and the path collapses toward the direct run,
    # which is what keeps the pair inside its uncoupled budget.
    #
    # WHAT THAT COSTS, MEASURED, so the contract is not read as free.  Only the
    # CONNECTOR half of the pair is routable under it.  On F.Cu alone
    # `USB_D_MCU_P` (R34.2 -> U1.14, 24.281 mm) and `USB_D_MCU_N` (R33.2 ->
    # U1.13, 21.858 mm) are both `NO_PATH` with healthy terminals -- 10/9 and
    # 11/9 legal escapes -- and NO whole-net rip-up opens either: the sixteen
    # nets with the most copper in each corridor were each removed BOARD-WIDE,
    # one at a time, and all thirty-two trials stayed `NO_PATH`.  The corridor
    # only opens with every one of the 104 F.Cu routed nets gone at once
    # (28.645 mm / 32.011 mm), which is a diagnosis and not a transaction.
    # So the MCU half is a recorded CROSSING-COPPER wall under this contract:
    # it is not a placement wall -- with F and B it routes today in 22.771 mm
    # and 22.344 mm with two vias each -- and closing it needs either a real
    # `.kicad_dru` section-6 ruling on whether a through via that merely
    # PIERCES In2 is the In2 excursion that rule forbids, or an F.Cu
    # refloorplan of the MCU fanout.  Neither is smuggled in here.
    "USB_D":        dict(clr=200000, layers=("F",)),
}

# A `width_cap` may state what a package can LAUNCH; it may never state less
# than what a rule DEMANDS.  Asserted at import so the day someone tunes a cap
# below its own class floor the module refuses to load rather than quietly
# proposing illegal copper.
for _cls, _over in DRU_CLASS.items():
    if _over.get("width_cap") is not None:
        assert _over["width_cap"] >= _over.get("width", 0), _cls
del _cls, _over

# `(rule "Via annular ring floor") (constraint annular_width (min 0.125mm))`.
ANNULAR_MIN = 125000

# --------------------------------------------------------------------------- #
# POUR BRIDGES -- ONE BARREL, NO TRACK, NO ESCAPE
# --------------------------------------------------------------------------- #
# The pours' own residual is the largest single block of open edges on this
# board, and D-594 measured why the stitch cannot close it: `stitch_pad` asks a
# PAD to launch, and these pads have no legal launch at any width the board
# licenses.  They do not need one.  A pad stranded on its own severed piece of
# pour already HAS copper; what it lacks is a barrel down to the same net's
# copper on another layer.  `maze3d.bridge_islands` is exactly that primitive
# and this is the lever that admits it into a gated transaction.
#
# THE BARREL IS CHOSEN COARSEST-FIRST, and that ordering is electrical, not
# cosmetic.  `+3V3` `U1.2` is the ESP32-S3 module's rail pin and takes the full
# POWER-class 0.65/0.40 mm barrel because one fits; a 2.2k I2C pull-up top does
# not need one and could not have one.  A barrel below an ordinary floor is
# emitted ONLY where the `.kicad_dru` grants that net that geometry inside the
# rule area named for that cluster -- the same plated 0.20 mm process this
# board already licenses by name six times (D-257 / D-266 / D-531).
BRIDGE_LADDER = ((650000, 400000),      # POWER class floor -- no exception
                 (600000, 300000),      # GND netclass via  -- no exception
                 (550000, 250000),      # THERMAL class     -- no exception
                 (500000, 250000),      # board min_via_diameter
                 (450000, 200000),      # 0.20 mm drill, ordinary 0.125 ring
                 (350000, 200000))      # the licensed fine-pitch process

# `aqroot-Beta-v2.kicad_pro`, board.design_settings.rules.  Transcribed here
# for the same reason `DRU_CLASS` is: a floor the driver enforces must be
# readable next to the code that enforces it.
BOARD_VIA_DIA_MIN = 500000              # min_via_diameter
BOARD_HOLE_MIN = 200000                 # min_through_hole_diameter
BOARD_TRACK_MIN = 150000                # min_track_width

# How far a licence area extends BEYOND the barrel it licenses.  KiCad answers
# `enclosedByArea` against the item's copper, not its centre, so the area has to
# contain the whole annulus -- the first run of this lever drew a fixed 0.5 mm
# square, the emitter chose a 0.60 mm barrel for `R19.1`, the area did not
# enclose it and the POWER-class 0.40 mm drill rule correctly won.  The area is
# therefore sized FROM the barrel.  0.15 mm of margin is comfortably more than
# the rounding and comfortably less than the 0.25 mm hole-to-hole minimum, so
# no second via can ever be enclosed by another via's licence.
BRIDGE_AREA_MARGIN_MM = 0.15

# D-606.  The barrel a PAD-ESCAPE RELIEF area licenses, in nm.  It is not a new
# figure: 0.35 mm diameter on a 0.20 mm hole with a 0.075 mm ring is the
# fine-pitch plated process this board's own `.kicad_dru` already licenses by
# name for D-257 escape vias, D-266 Kelvin reservations, D-531 USB-C VBUS POFV
# and D-595's `POUR_BRIDGE_U11_11`.  What a relief area changes is only WHERE
# it may be used, and only for the one net the rule names.
RELIEF_VIA = (350000, 200000)

RULE_AREA = """
	(zone
		(layers "F.Cu" "B.Cu" "In1.Cu" "In2.Cu" "In3.Cu" "In4.Cu")
		(uuid "%(uuid)s")
		(name "%(name)s")
		(hatch edge 0.5)
		(connect_pads
			(clearance 0)
		)
		(min_thickness 0.25)
		(keepout
			(tracks allowed)
			(vias allowed)
			(pads allowed)
			(copperpour allowed)
			(footprints allowed)
		)
		(placement
			(enabled no)
			(sheetname "")
		)
		(fill
			(thermal_gap 0.5)
			(thermal_bridge_width 0.5)
			(island_removal_mode 0)
		)
		(polygon
			(pts
				%(pts)s
			)
		)
	)
"""


def via_floors(netclass):
    """The ordinary via floors a barrel on this class must meet unaided.

    Board setup gives `min_via_diameter` and `min_through_hole_diameter`; the
    `.kicad_dru` gives the unconditional annular ring floor and, for the seven
    POWER classes, the 0.40 mm `hole_size` minimum -- which is exactly the
    `drill` column of `DRU_CLASS`.  Nothing new is decided here; this is the
    same table the contract already reads, asked a different question.
    """
    return dict(dia=BOARD_VIA_DIA_MIN,
                drill=max(BOARD_HOLE_MIN,
                          DRU_CLASS.get(netclass, {}).get("drill", 0)),
                annular=ANNULAR_MIN)


def bridge_area_sexpr(name, x_nm, y_nm, via_dia_nm,
                      margin_mm=BRIDGE_AREA_MARGIN_MM):
    """A square, all-permitted rule area centred on a bridge barrel.

    Every keep-out flag is `allowed`, so this area forbids nothing and the
    router does not even see it (`qrouter.QBoard` rasterises a rule area only
    when it disallows tracks).  Its ONLY job is to be the region a `.kicad_dru`
    `enclosedByArea` condition names -- the same device D-257, D-266 and D-531
    already use to scope a fine-pitch via exception to one pad.
    """
    x, y = x_nm / 1e6, y_nm / 1e6
    h = via_dia_nm / 2e6 + margin_mm
    pts = [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)]
    return RULE_AREA % dict(
        name=name,
        uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, "aqroot-demo/rule-area/" + name)),
        pts=" ".join("(xy %g %g)" % q for q in pts))


# --------------------------------------------------------------------------- #
# THE WIDTH LICENCE IS DECLARED BEFORE THE ROUTER MOVES -- D-610
# --------------------------------------------------------------------------- #
# D-606's `PAD_ESCAPE_<REF>` areas license a BARREL and are drawn by the
# promoting transaction AROUND the barrel it actually laid, sized from it.  That
# is safe for a barrel because a barrel is a point: its area is a fixed square
# whose only free parameter is where the point is, and clause 6 audits the count
# and the shape.
#
# A RUN IS NOT A POINT, and an area drawn around whatever run the router
# happened to lay would be a licence whose EXTENT the router chooses.  That is
# a blank cheque written in the one currency this board treats as most
# expensive.  So the rectangle is DECLARED -- in a tracked JSON spec, reviewed
# and committed BEFORE the run, exactly as `--guard` and `--detour-spec`
# already are -- and the transaction draws that rectangle and no other.  A run
# that does not fit is refused by `maze3d._run_licence` with
# `RUN_OUTSIDE_LICENCE_AREA`, three minutes before real DRC would have said the
# same thing less clearly.
#
#   {"schema": 1, "net": "+3V3",
#    "areas": {"U12.4": [x0, y0, x1, y1], ...}}      millimetres
#
# The `.kicad_dru` rule naming `PAD_ESCAPE_RUN_<REF>` must exist as well; the
# spec says WHERE the area is, the rule says WHAT it grants, and neither alone
# lays a micron of copper.
def load_run_areas(path):
    """{REF.NUM: (x0, y0, x1, y1) in nm} from a declared width-licence spec."""
    if not path:
        return {}
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for ref, box in (doc.get("areas") or {}).items():
        if len(box) != 4:
            raise SystemExit("--relief-run-area: %s needs [x0,y0,x1,y1] mm"
                             % ref)
        x0, y0, x1, y1 = (float(v) for v in box)
        if x1 <= x0 or y1 <= y0:
            raise SystemExit("--relief-run-area: %s rectangle is empty" % ref)
        out[ref] = tuple(int(round(v * 1e6)) for v in (x0, y0, x1, y1))
    return out


def run_area_sexpr(name, x0_nm, y0_nm, x1_nm, y1_nm):
    """The DECLARED rectangle, as the same all-permitted rule area a bridge draws.

    Same object, same keep-out flags (every one `allowed`), same clause-6
    audit; only the outline differs, because a run has an extent and a barrel
    does not.
    """
    x0, y0, x1, y1 = (v / 1e6 for v in (x0_nm, y0_nm, x1_nm, y1_nm))
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return RULE_AREA % dict(
        name=name,
        uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, "aqroot-demo/rule-area/" + name)),
        pts=" ".join("(xy %g %g)" % q for q in pts))


def rule_areas(path):
    """A comparable signature for every RULE AREA on a board.

    Clause 6 audits pours; without this it would not audit these, and a
    transaction could quietly draw a region that licenses a geometry nobody
    reviewed.  A rule area is not copper, so it is a separate signature and a
    separate claim -- not a hole in the copper one.
    """
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for z in board.Zones():
        if not z.GetIsRuleArea():
            continue
        o = z.Outline().Outline(0)
        out.append((z.GetZoneName(),
                    tuple(board.GetLayerName(l) for l in z.GetLayerSet().Seq()),
                    bool(z.GetDoNotAllowTracks()), bool(z.GetDoNotAllowVias()),
                    bool(z.GetDoNotAllowPads()), bool(z.GetDoNotAllowZoneFills()),
                    tuple((o.CPoint(i).x, o.CPoint(i).y)
                          for i in range(o.PointCount()))))
    return sorted(out)


# The plane repair's residual-join bound, in millimetres.  It is not a taste
# figure: `maze3d.stitch_pad` and `maze3d.join_residual_islands` both work in an
# 8 mm window (`escape_limit=8`, `near=8`), so a re-bond inside that window is
# the same LOCAL question the stitch was already asking, answered with track
# instead of a barrel.  Anything longer stops being a repair.
REPAIR_JOIN_MAX_MM = 8.0

# THE ORPHAN JOIN IS BOUNDED FOR THE SAME ELECTRICAL REASON THE RESIDUAL JOIN
# IS, and more tightly.  D-608.  A residual join puts a pad ON the plane; an
# orphan join only ties two pads that are BOTH still off it, so what it buys is
# one open edge and what it spends is outer-layer capacity the unrouted signal
# nets still need.  A short one is unarguable -- `U12.4` to `U12.5` is 0.500 mm
# between two pins the TPS63020's datasheet requires connected anyway -- and a
# long one is a lateral haul that should have been a barrel.
JOIN_ORPHAN_MAX_MM = 4.0
# D-631.  A PAD BRIDGE is a straight track between two lands with no escape and
# no via, so its length is bounded by the geometry that makes it possible at all
# -- two lands close enough that the strip between them is the only legal
# copper.  3.0 mm is that shape; the board-wide screen finds the same single
# pair at 3.0 mm and at 8.0 mm, so the bound is not what is limiting it.
BRIDGE_PAD_MAX_MM = 3.0

# --------------------------------------------------------------------------- #
# THE TAP -- A BRANCH ONTO THE NET'S OWN CONDUCTOR
# --------------------------------------------------------------------------- #
# D-664.  `--tap` hands `maze3d.join_taps` an orphan LAND and lets it aim at the
# net's own nearest CONNECTED COPPER instead of at the nearest PAD.  The
# doctrine, the five clauses TAP1-TAP5 and the whole argument live above
# `maze3d.join_taps`; what belongs HERE is only the one list both files must
# agree on.
#
# A TAP MAKES A STUB, SO THE NETCLASS DECIDES WHETHER IT MAY BE ASKED.  These
# classes are refused BY NAME, before any search: their rules govern the SHAPE
# of the conductor -- matched length, controlled impedance, a reserved layer, a
# switching node's loop area, an RF arm's symmetry -- and none of those survive
# an unbudgeted branch.  It is stated here and stated again in
# `screen_net_tap.STUB_FORBIDDEN`, and the two being EQUAL is a CONTRACT, not a
# convention: a screen and its writer disagreeing about which nets may be asked
# is exactly the failure this primitive exists to avoid.  `checks/tap_contract.py`
# clause TC1 fails the standing suite the day they drift.  (The list is restated
# rather than imported because the screen imports THIS module; a module-level
# import the other way is a cycle, and a lazy one would put the contract inside
# the code it is meant to police.)
TAP_STUB_FORBIDDEN = ("USB_D", "NFC_RF", "NFC_RX", "SWITCH_NODE", "SPK_OUT")

# --------------------------------------------------------------------------- #
# BOND REDUNDANCY -- A STITCH FOR A PAD THAT IS ALREADY CONNECTED
# --------------------------------------------------------------------------- #
# `--bond-pad REF.NUM` hands `maze3d.bond_pads` a pad whose only bond to its net
# is POUR COPPER and asks for a second one: an escape, a short run and a through
# barrel down to the same net's inner-layer plane.  See the doctrine block above
# `maze3d.bond_pads` for why it is a pad question and not an island one.
#
# It is a lever on the PRIMARY proposal only.  The plane repair re-bonds what a
# run severed and does it with the stitch; letting it also add redundancy to
# pads this run never touched would be a second transaction wearing a repair's
# name, exactly as it would for `--bridge`.
#
# The window is `stitch_pad`'s own 8 mm, for the same reason `REPAIR_JOIN_MAX_MM`
# is: a bond is LOCAL, and a barrel eight millimetres from the pad it is meant
# to hold has stopped being redundancy and started being a detour.
BOND_MAX_MM = 8.0

# --------------------------------------------------------------------------- #
# EVICTION -- THE ONE PLACE THIS DRIVER MAY REMOVE COPPER
# --------------------------------------------------------------------------- #
# Every promotion from D-578 to D-583 only ADDED copper, and clause 5 said so in
# the strongest possible terms: nothing pre-existing may disappear.  That rule
# was right for a board being filled from empty and it is the wrong rule for a
# board that is now congested, because it makes the order in which nets happened
# to be routed permanent.  `screen_corridor_blockers.py` measured the cost
# exactly: `/01_POWER_TREE/USB_D_CONN_P` cannot reach `U10.3` -- 7.5 mm, both
# terminals healthy with 8 and 10 legal escapes -- because eight ground segments
# and two barrels a later whole-board maze batch laid are standing in a corridor
# the `.kicad_dru` had already reserved for the USB pair.  No search fixes that.
# The copper has to move.
#
# So eviction is added as a BOOKKEEPING exception to clause 5 and nothing more.
# It does not relax clause 3 (real KiCad DRC) or clause 4 (no net regresses, the
# whole board improves).  Four properties keep it a transaction rather than a
# licence:
#
#   * ONLY NAMED NETS.  `--evict` takes explicit net names.  A run can never
#     discover for itself that some net is in the way and delete it.
#   * ONLY INSIDE THE CORRIDOR THE REQUESTED NETS THEMSELVES DEFINE.  The window
#     is the bounding box of ONE requested net's own fitted pads grown by
#     `--evict-margin-mm`, computed PER NET and never unioned, so asking for
#     twenty nets buys twenty local windows and not one board-sized one.
#   * ONLY ROUTED COPPER, ONLY WHOLLY CONTAINED, ONLY ON A LAYER THAT ACTUALLY
#     OBSTRUCTS.  A pad is where a part is soldered and is never evictable.  A
#     track that merely CROSSES the window is left alone, because a track cannot
#     be ripped up piecewise and pretending otherwise reports an opening no
#     transaction can deliver.  And copper on a layer the requested nets may not
#     route on is not in anybody's way, so it is not touched: with the USB pair
#     pinned to `F.Cu`, a ground track on `In2` inside the same box stays.
#   * THE EVICTED NET IS RE-PROPOSED, NOT ABANDONED.  Any evicted net whose open
#     edges grew is handed to the repair pass along with the pour-owning nets,
#     at the same 8 mm locality bound, and clause 4 then still requires it to
#     end the transaction NO WORSE OFF than it started.  A rip-up whose reroute
#     fails is a refusal, exactly as if the copper had never been touched.
#
# `--evict-whole` IS THE OTHER HONEST UNIT, and the board asked for it.  The
# first eviction transaction here ripped `/09_COMMUNITY_HEADER/EXT_SCL` inside
# the `EXT_SDA` window and was refused for `track_dangling`: `EXT_SCL` carries
# legacy copper on `In3.Cu`, a RESERVED plane layer that is never in
# `keep_layers`, so the window took its barrels and left its fragments.  The
# closure below rescues the contained ones; the cascade then outgrew what the
# 8 mm repair pass could rebuild, and the run was refused again -- correctly, on
# clause 4.  Both failures say the same thing: when the point of the rip-up is
# to REROUTE a net rather than to clear a strip of it, the net is the unit.
# `--evict-whole` therefore removes every routed object of a named net on every
# layer, and REQUIRES that net to be requested, so it is rebuilt by the same
# primary proposer at its own contract instead of by the local repair.  Blast
# radius is still exactly one named net per name, clause 4 still demands it end
# no worse off, and the reserved inner planes come out cleaner than they went
# in, because a foreign fragment on a poured plane is a slot that this removes.
#
# `--evict` is OFF by default, so every accepted result reproduces without it.
EVICT_MARGIN_MM = 3.0
ROUTED_TAGS = ("PCB_TRACK", "PCB_VIA")


def evict_boxes(board, nets, margin_nm):
    """One corridor window per requested net: its own pad bbox plus a margin.

    Per net, deliberately.  A union over several requested nets would grow one
    window big enough to contain copper that is nowhere near any corridor, and
    the report would then claim an authority the transaction does not have.
    """
    span = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name = pad.GetNetname()
            if name not in nets:
                continue
            p = pad.GetPosition()
            box = span.get(name)
            span[name] = (p.x, p.y, p.x, p.y) if box is None else (
                min(box[0], p.x), min(box[1], p.y),
                max(box[2], p.x), max(box[3], p.y))
    return {n: (b[0] - margin_nm, b[1] - margin_nm,
                b[2] + margin_nm, b[3] + margin_nm)
            for n, b in span.items()}


# --------------------------------------------------------------------------- #
# EVICTION MUST BE CLOSED UNDER DANGLEMENT
# --------------------------------------------------------------------------- #
# The first `--evict` transaction on this board -- `/09_COMMUNITY_HEADER/EXT_SDA`
# with `/09_COMMUNITY_HEADER/EXT_SCL` ripped up -- routed, regressed nothing,
# re-proposed the evicted net in full, and was still refused, for three
# `track_dangling` warnings on `In3.Cu`.
#
# The cause is a seam between two of eviction's own rules.  A VIA obstructs on
# every layer, so it is evictable wherever it sits; a TRACK is evictable only on
# a layer the requested nets may actually route on.  `EXT_SCL` carries legacy
# copper on `In3.Cu` -- laid before D-580 poured `+3V3` there -- which is now a
# RESERVED plane layer and therefore never in `keep_layers`.  Removing the
# barrels that terminated those three fragments left them stranded: real copper,
# on a plane, connected to nothing, which is exactly what KiCad reported.
#
# The layer rule is still right -- eviction should be minimal, and a foreign
# net's copper on a layer nobody is routing on obstructs nothing.  What was
# missing is that minimality is a property of the SELECTION, not a licence to
# leave the board in a state the selection created.  So the selection is
# unchanged and a CLOSURE is added on top of it:
#
#   * SUPPORT IS MEASURED TWICE.  An endpoint is supported when some other
#     object of its own net -- a pad it lands in, a barrel at that point, or
#     another track that meets or crosses it on that layer -- holds it.  Support
#     is computed BEFORE the removals and again after, and only an object that
#     the removals themselves stranded is added.  Copper that was already
#     dangling on the authoritative board is not this transaction's business and
#     is left exactly where it is.
#   * ONLY THE EVICTED NETS, ONLY INSIDE THE SAME WINDOWS.  The closure obeys
#     every clause the selection obeys except the layer filter, because the
#     object it removes is one this run's own removals made purposeless.
#   * WHAT IT CANNOT REACH, IT REPORTS.  A stranded object outside every corridor
#     window is named in `dangling_unevictable` rather than silently left, so the
#     DRC refusal that follows has an explanation in the same record.
#   * FIXED POINT.  Removing a stranded track can strand the next one, so the
#     closure iterates until nothing changes.
#
# Removing a foreign net's copper from a poured inner plane is also the strictly
# better outcome on its own terms: that fragment was a slot through `+3V3`, and
# the repair pass re-proposes the whole evicted net on `F`/`B`/`In2` only.
def _pt(v):
    return (int(v.x), int(v.y))


def uid(item):
    return item.m_Uuid.AsString()


def _meets(track, pt):
    """Does `pt` lie on this track's centreline (endpoint or T-junction)?"""
    a, b = _pt(track.GetStart()), _pt(track.GetEnd())
    if pt == a or pt == b:
        return True
    ax, ay = a
    bx, by = b
    px, py = pt
    if (bx - ax) * (py - ay) != (by - ay) * (px - ax):
        return False
    return (min(ax, bx) <= px <= max(ax, bx)
            and min(ay, by) <= py <= max(ay, by))


def _supported(obj, survivors, pads):
    """Is every end of this routed object held by other copper of its net?

    A via is held when anything at all meets it; a track needs BOTH ends.
    """
    import pcbnew
    if obj.GetClass() == "PCB_VIA":
        ends = [(_pt(obj.GetStart()), None)]
    else:
        L = obj.GetLayer()
        ends = [(_pt(obj.GetStart()), L), (_pt(obj.GetEnd()), L)]
    for pt, layer in ends:
        ok = False
        for o in survivors:
            if o is obj:
                continue
            if o.GetClass() == "PCB_VIA":
                if _pt(o.GetStart()) == pt and (layer is None
                                                or o.IsOnLayer(layer)):
                    ok = True
                    break
            elif layer is None or o.GetLayer() == layer:
                if _meets(o, pt):
                    ok = True
                    break
        if not ok:
            for p in pads:
                if (layer is None or p.IsOnLayer(layer)) and p.HitTest(
                        pcbnew.VECTOR2I(pt[0], pt[1])):
                    ok = True
                    break
        if not ok:
            return False
    return True


def evict_closure(board, evict_nets, doomed, contained):
    """Objects this run's own removals stranded, and the ones it cannot reach.

    Returns `(extra, unevictable)`.  `extra` is appended to `doomed`;
    `unevictable` names stranded copper outside every corridor window.
    """
    live = {}
    pads = {}
    for t in board.GetTracks():
        if t.GetClass() in ROUTED_TAGS and t.GetNetname() in evict_nets:
            live.setdefault(t.GetNetname(), []).append(t)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() in evict_nets:
                pads.setdefault(p.GetNetname(), []).append(p)

    # Identity is the item UUID, never `id()`: `doomed` and `live` were built
    # from separate `GetTracks()` walks and this KiCad build hands out a fresh
    # SWIG proxy each time, so a Python identity set would silently match
    # nothing and the closure would find nothing to do.
    was = {uid(o): _supported(o, live[n], pads.get(n, []))
           for n in live for o in live[n]}
    gone = {uid(o) for o in doomed}
    extra, unevictable = [], []
    while True:
        added = False
        for net, objs in live.items():
            keep = [o for o in objs if uid(o) not in gone]
            for o in keep:
                if not was.get(uid(o), True):
                    continue            # already dangling before this run
                if _supported(o, keep, pads.get(net, [])):
                    continue
                gone.add(uid(o))
                added = True
                if contained(o):
                    extra.append(o)
                else:
                    unevictable.append(dict(
                        net=net,
                        kind="via" if o.GetClass() == "PCB_VIA" else "track",
                        layer=(None if o.GetClass() == "PCB_VIA"
                               else board.GetLayerName(o.GetLayer())),
                        xy_mm=[round(v / 1e6, 4)
                               for v in _pt(o.GetStart())]))
        if not added:
            break
    return extra, unevictable


def evict_copper(path, nets, evict_nets, margin_nm, whole=False,
                 window_nm=None):
    """Rip up the evictable copper IN PLACE and describe every removal.

    Runs in the `--evict-apply` CHILD, never in the authority process, and for a
    concrete reason: removing tracks from a loaded `BOARD` and saving it leaves
    this KiCad build's SWIG bindings returning an untyped `SwigPyObject` from
    the next `LoadBoard`, so the gate's own later `plane_nets` / `zones` /
    `copper` reads would silently fail.  Every other board MUTATION in this
    module already happens in a child; this one is no different.

    Copper is evictable only if it is ROUTED (a pad is where a part is soldered
    and is never touched), on a NAMED net, WHOLLY inside one requested net's own
    corridor window, and on a layer the requested nets are actually permitted to
    route on -- copper that obstructs nothing is nobody's business.  A via is a
    barrel through the whole stack, so it obstructs on every layer, which is the
    honest reading rather than the convenient one.

    D-655.  `window_nm` NAMES THE CORRIDOR INSTEAD OF DERIVING IT, and the
    reason it has to exist is that the derived one is an UPPER BOUND that stops
    being a bound when the evicted net is long.  The default corridor is the
    requested nets' own pad bounding boxes, which is honest when the request is
    local; `/I2C_SCL_INT` and `/I2C_SDA_INT` each span this board corner to
    corner, so the derived corridor is 6166 mm2 and `--evict /I2C_SCL_INT`
    takes 84 objects and 178.9 mm -- the WHOLE net -- when the measurement that
    asked for it named TWO 0.200 mm tracks in one 3 mm pocket.  A transaction
    that rips up 178.9 mm to admit 19.7 mm is not the transaction anybody
    measured, and it is not reviewable.

    So a caller that has SCREENED the pocket may state it.  The window is a
    RESTRICTION and never a licence: an object still has to be routed, on a
    named evicted net, on a permitted layer, and WHOLLY inside -- the window
    only replaces the derived box with a smaller stated one, so nothing becomes
    evictable that was not evictable before.  It is reported verbatim next to
    the derived corridors it overrode, because the difference between the two
    is the whole review.
    """
    import pcbnew
    import qrouter as qr
    import incremental_router as ir

    board = pcbnew.LoadBoard(str(path))
    reserved = reserved_inner_planes(board)
    routable = qr.ROUTABLE.get(board.GetCopperLayerCount(), ("F", "B"))
    short = set()
    for n in nets:
        c = net_contract(board, n)
        short.update(permitted_layers(routable, c["layers"], reserved, n))
    boxes = evict_boxes(board, set(nets), margin_nm)
    missing = sorted(set(nets) - set(boxes))
    if missing:
        raise SystemExit("--evict: requested nets own no pads: %s"
                         % ", ".join(missing))
    keep_layers = {qr.LNAME[s] for s in short}

    windows = [tuple(window_nm)] if window_nm else list(boxes.values())

    def contained(item):
        if whole:
            return True
        bb = item.GetBoundingBox()
        return any(bb.GetLeft() >= box[0] and bb.GetTop() >= box[1]
                   and bb.GetRight() <= box[2] and bb.GetBottom() <= box[3]
                   for box in windows)

    doomed = []
    for t in board.GetTracks():
        cls = t.GetClass()
        if cls not in ROUTED_TAGS or t.GetNetname() not in evict_nets:
            continue
        if not whole and cls == "PCB_TRACK" and t.GetLayer() not in keep_layers:
            continue
        if contained(t):
            doomed.append(t)

    extra, unevictable = evict_closure(board, set(evict_nets), doomed,
                                       contained)
    doomed += extra

    sigs = []
    for t in doomed:
        sigs.append(ir._via_sig(t) if t.GetClass() == "PCB_VIA"
                    else ir._track_sig(t))
        board.Remove(t)
    pcbnew.SaveBoard(str(path), board)
    return dict(
        evicted_nets=sorted(set(evict_nets)),
        whole_net=bool(whole),
        stated_window_mm=([round(v / 1e6, 4) for v in window_nm]
                          if window_nm else None),
        corridor_layers=sorted(short),
        margin_mm=round(margin_nm / 1e6, 3),
        corridors={n: dict(
            box_mm=[round(v / 1e6, 3) for v in b],
            area_mm2=round((b[2] - b[0]) * (b[3] - b[1]) / 1e12, 3))
            for n, b in sorted(boxes.items())},
        removed_signatures=sorted(str(s) for s in sigs),
        removed_count=len(sigs),
        closure_count=len(extra),
        dangling_unevictable=unevictable,
        removed_by_net={n: sum(1 for s in sigs if s[1] == n)
                        for n in sorted({s[1] for s in sigs})})


# --------------------------------------------------------------------------- #
# THE DETOUR -- THE SEGMENT EVICTION THIS BOARD HAS NAMED FOUR TIMES
# --------------------------------------------------------------------------- #
# D-602, D-603, D-605 and D-606 each ended by naming the same missing unit, and
# four independent walls ask for it: the USB connector corridor, the `U9` west
# channel, and the `GND` and `BQ25185_SYS` pour residuals are every one of them
# a FOREIGN TRACK LYING ACROSS a pocket that would otherwise hold a barrel.
# Neither existing eviction can take one -- `--evict` removes only copper
# WHOLLY INSIDE a corridor window, `--evict-whole` removes a whole net
# board-wide -- and D-602 proved no whole-net eviction of any size opens the
# USB corridor at all.
#
# `screen_segment_evict.py` measured the family on the promoted D-606 board:
# of the sixteen open pour lands that fail `stitch_pad` with `NO_VIA_SITE`,
# CUTTING FOREIGN TRACK OPENS TEN, most of them with ONE track moved out of a
# disc under a millimetre across.  The pocket is not full of pads.  It is full
# of copper that has somewhere else to be.
#
# WHY A DETOUR AND NOT A SPLIT.  "Split the track at the pocket boundary and
# rip up the piece inside" leaves two stubs with FREE ENDS, and on this board a
# free end is not cosmetic: D-580's first `--evict` transaction routed,
# regressed nothing, re-proposed its evicted net in full and was still REFUSED,
# for three `track_dangling` warnings.  So the split owes a re-join, and the
# re-join owes a terminal the lattice cannot express.  Removing the crossing
# track WHOLE and laying it again BETWEEN ITS OWN TWO END COORDINATES is the
# same transaction with the trap taken out: both endpoints keep their exact
# coordinates, so everything that met that track still meets it, nothing is
# stranded, no stub exists to re-join, and the cut net's cluster count cannot
# move.  `maze3d.route_points` is the primitive and the doctrine above it in
# `maze3d.py` is the argument.
#
# THE POCKET IS HELD BY THE GUARD THIS BOARD ALREADY OWNS.  A detour that
# simply retraced its old path would free nothing, so the site is reserved as
# an ordinary `Field` guard -- the same object `pour_bond_guard.py` writes and
# `reserve_corridor.py` emits, with `exempt` naming the pour net the pocket is
# being freed FOR.  No new keep-out concept, no rule area, no licence.
#
# THE TRANSACTION IS NAMED, NOT SEARCHED.  A spec file lists exactly which
# tracks move and exactly which discs are reserved, the applier refuses
# anything it cannot resolve to a single track, and clause 5 licenses the
# removals by SIGNATURE exactly as it licenses an eviction's.  A detour that
# will not route is a REFUSAL of the whole run, never a track left out.
def exact_relay_pads(board_path, key, d, tol_nm=1000):
    """None when `key` may stand in for detour `d`, else the reason it may not.

    THREE THINGS ARE CHECKED AND ALL THREE MATTER.  The named route must be an
    entry this module's own allowlist already carries, it must be on the
    detour's OWN net -- so this can never put somebody else's copper back -- and
    its two pads must be the chain's own two ends to a micron, so it puts back
    the track that was taken and not a different one wearing its name.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("_rl2p", LOCAL_TWO_PAD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rule = mod.ROUTES.get(key)
    if rule is None:
        return "no such route_local_two_pad route: %r" % key
    if rule["net"] != d["net"]:
        return ("route %r is on %s, the detour is on %s"
                % (key, rule["net"], d["net"]))
    import pcbnew
    board = pcbnew.LoadBoard(str(Path(board_path).resolve()))
    want = [tuple(int(round(v * 1e6)) for v in d["a_mm"]),
            tuple(int(round(v * 1e6)) for v in d["b_mm"])]
    got = []
    for ref in rule["pads"]:
        r, num = ref.split(".")
        fp = board.FindFootprintByReference(r)
        pad = fp and next((p for p in fp.Pads() if p.GetNumber() == num), None)
        if pad is None:
            return "route %r names a pad this board has not got: %s" % (key, ref)
        pos = pad.GetPosition()
        got.append((pos.x, pos.y))
    for w in want:
        if not any(abs(w[0] - g[0]) <= tol_nm and abs(w[1] - g[1]) <= tol_nm
                   for g in got):
            return ("route %r joins %s, which are not the chain's two ends %s"
                    % (key, rule["pads"], want))
    return None


def load_detours(path):
    """Read a detour spec, or {} when none was asked for."""
    if not path:
        return {}
    doc = json.loads(Path(path).read_text())
    if doc.get("schema") != 1:
        raise SystemExit("--detour-spec: unknown schema %r" % doc.get("schema"))
    return doc


DETOUR_RESERVE_LAYERS = ("F", "I1", "I2", "I3", "I4", "B")


def detour_guard(spec):
    """The reserved discs as a `pour_bond_guard.py` guard record per layer.

    One record per copper layer per disc, because a barrel is copper on every
    layer of the stack and a reservation that held only the outer two would let
    the detour tunnel under the site it was moved to free.  `net` carries the
    first exempt net so `guard_for`'s own one-net exemption does the work, and
    the rest ride in `exempt`, which D-602 added for exactly this shape.

    A RESERVATION FOR A TRACK IS A PER-LAYER FACT.  D-649.  Every reservation
    written before this one was made for a BARREL, and a barrel really is
    copper on all six layers, so "all six" was the only truth the spec could
    tell.  A reservation made for ONE STRAIGHT TRACK on ONE layer is a
    different object: copper on `F.Cu` or `In2.Cu` crossing under a `B.Cu`
    pad bridge threatens nothing, and reserving those layers anyway is not
    conservative -- it refuses relays for a danger that does not exist.  It
    cost a gate run to find out: the `Net-(U12-PS_SYNC)` relay this decision
    needed came back `NO_PATH` at 0.200 mm with `layers_allowed` `F, B, I2`
    and every one of the three reserved.  So a reserve record may name its own
    `"layers"`; ABSENT, it is all six and every spec written before this reads
    exactly as it did.
    """
    guards = []
    for k, d in enumerate(spec.get("reserve", ())):
        ex = list(d.get("exempt", ()))
        lkeys = list(d.get("layers", DETOUR_RESERVE_LAYERS))
        bad = [L for L in lkeys if L not in DETOUR_RESERVE_LAYERS]
        if bad:
            raise SystemExit("--detour-spec: reserve names no such copper "
                             "layer key %s (want %s)"
                             % (", ".join(map(repr, bad)),
                                "/".join(DETOUR_RESERVE_LAYERS)))
        for lkey in lkeys:
            guards.append(dict(
                ok=True, net=(ex[0] if ex else ""), exempt=ex[1:],
                lkey=lkey, keepout_radius=int(round(d["r_mm"] * 1e6)),
                points=[[int(round(d["x_mm"] * 1e6)),
                         int(round(d["y_mm"] * 1e6))]],
                tube="DETOUR_RESERVE_%d" % (k + 1)))
    return dict(guards=guards)


INERT_PRICE_GRID = 25000        # nm; `pour_bond_guard.TUBE_GRID`
INERT_PRICE_CEILING = 400000    # nm of erosion radius: 0.800 mm of conductor
INERT_SEED_RADIUS = 150000      # nm; the anchor disc `pour_bond_guard` uses
                                # for a via, so an end that is one is seeded
                                # exactly as that module already seeds it


def inert_removal_price(board_path, entries, grid=INERT_PRICE_GRID):
    """What the board REPLACED a `relay: false` chain with, as a number.

    D-646.  A relay owes the board the same conductor somewhere else and
    `route_points` proves it.  A REMOVAL owes the board a conductor it already
    has, and until this function existed nothing measured that: the run would
    have rested on the author's assertion that the copper was redundant, which
    is exactly the `unmeasured-vs-refused` failure this project keeps paying
    for.

    So the claim is settled with the instrument this board already uses for the
    same question -- D-644 priced `U3.12`'s ground bond by walking
    `pour_bond_guard.geodesic` out from the pad and reading the narrowest place
    at 0.150 mm.  Two things must hold and both are geometry, not opinion:

      * ONE FILLED ISLAND of that net, on that layer, must contain BOTH ENDS
        of the chain that was removed.  That is the connectivity claim, read
        off KiCad's own fill rather than asserted -- if the removal severed
        anything, no island holds both ends and the clause refuses by name.

      * THE WIDEST PATH between those ends, inside that island, must be at
        least as wide as the copper that was taken.  `geodesic` erodes from
        the ceiling down and returns the first radius the whole path survives,
        so `2 * radius` is the narrowest place on the best conductor the pour
        offers.  Below the removed track's own width the removal is a
        DERATING, and a derating is a decision somebody has to take
        deliberately -- not a side effect of a routing run.

    AND IT IS ASKED OF THE BOARD THE COPPER WAS TAKEN FROM, NOT OF THE
    CANDIDATE.  The claim this clause owns is "that copper was already
    redundant when this run removed it", and the only board on which that is
    even a well-posed question is the one it was removed from.  Asking it of
    the candidate conflates it with a DIFFERENT claim -- "and nothing this run
    laid afterwards split that pour" -- which is `pour_partition_contract.py`'s
    entire subject and which it answers with a priced bar rather than a
    yes/no.  This board proved the difference costs an edge: D-646's `+3V3`
    route through `U4`'s courtyard deliberately severs `GND` `B.Cu` island 38
    (12.626 mm2) into `C6.2`'s 4.314 mm2 fragment and `U20.3`'s 7.859 mm2
    body, `PP2` prices the fragment 1.902 A against its 1.000 A bar and admits
    it -- and a candidate-side reading of this clause called the same board
    `NO_FILLED_ISLAND_HOLDS_BOTH_ENDS` and refused the run for a fact `PP2`
    had already judged.  Two clauses, two questions, no overlap.
    """
    import pcbnew
    sys.path.insert(0, str(HERE))
    import pour_bond_guard as pbg

    board = pcbnew.LoadBoard(str(board_path))
    pours = pbg.read_pours(board)
    out = []
    for d in entries:
        a = tuple(int(round(v * 1e6)) for v in d["a_mm"])
        b = tuple(int(round(v * 1e6)) for v in d["b_mm"])
        rec = dict(net=d["net"], layer=d["layer"], a_mm=d["a_mm"],
                   b_mm=d["b_mm"], removed_mm=d.get("was_mm"),
                   bar_width_mm=round(d["width_nm"] / 1e6, 3))
        found = None
        for pour in pours:
            if pour["net"] != d["net"] or pour["layer"] != d["layer"]:
                continue
            for isl in pour["islands"]:
                if (isl["poly"].Contains(pcbnew.VECTOR2I(a[0], a[1]), -1, 0)
                        and isl["poly"].Contains(pcbnew.VECTOR2I(b[0], b[1]),
                                                 -1, 0)):
                    found = (pour, isl)
                    break
            if found:
                break
        if found is None:
            rec.update(ok=False, reason="NO_FILLED_ISLAND_HOLDS_BOTH_ENDS")
            out.append(rec)
            continue
        pour, isl = found
        rec.update(zone_name=pour["zone_name"], island=isl["index"],
                   island_area_mm2=round(isl["area_mm2"], 3))
        g = pbg.geodesic(isl["edges"],
                         (a[0], a[1], INERT_SEED_RADIUS),
                         (b[0], b[1], INERT_SEED_RADIUS),
                         INERT_PRICE_CEILING, grid)
        if not g:
            rec.update(ok=False, reason="NO_POUR_PATH_BETWEEN_THE_ENDS")
            out.append(rec)
            continue
        width = 2 * g["radius"]
        rec.update(pour_path_mm=g["mm"],
                   pour_path_width_mm=round(width / 1e6, 3),
                   pour_path_width_max_mm=round(2 * g["radius_max"] / 1e6, 3),
                   ratio=round(width / float(d["width_nm"]), 3),
                   ok=bool(width >= d["width_nm"]),
                   reason=(None if width >= d["width_nm"]
                           else "POUR_PATH_NARROWER_THAN_THE_COPPER_REMOVED"))
        out.append(rec)
    return out


def rebond_price(auth_path, cand_path, entries):
    """What replaced a barrel this run REMOVED, as geometry.  D-653.

    `inert_removal_price` prices a CHAIN and asks a question about ONE layer:
    does the pour already join the chain's two ends, at least as wide?  A
    BARREL has no two ends on one layer.  What it does is bond an outer-layer
    filled island to the net's inner planes, and on this board that is
    sometimes the only thing holding a pad to ground: `B.Cu` `GND` island 24 is
    16.523 mm2, contains exactly one pad (`U2.21`) and exactly one via
    (61.200, 90.800), and until D-653 no transaction could name that via at
    all.

    So the price of removing one is the BARREL THAT REPLACES IT, and this
    measures it on the two boards where each half of the claim is well posed:

      * ON THE AUTHORITATIVE BOARD -- the board the barrel was taken from --
        which outer-layer filled islands did it sit in, and which PADS of its
        own net sat in those islands with it.  Those pads are what the barrel
        served.  A barrel that served no pad on any outer layer is recorded
        `SERVED_NO_PAD` and is priced `ok`: it was a stitching via, its removal
        strands nothing, and the ledger's own open-edge test is the whole
        check.

      * ON THE CANDIDATE, AFTER THE REAL REFILL -- every pad the barrel served
        must sit in a filled island of its own net that contains a barrel of
        that net at least as WIDE and at least as DEEP in drill as the one
        removed.  Not "somewhere on the net": in the island the pad is
        actually in, because that is the copper the pad can reach without a
        track.  A pad the run re-bonded with a track and a barrel of its own
        satisfies this by the same test -- the stitch's barrel lands in the
        pad's island.

    WHAT THIS DOES NOT CLAIM.  It does not price the return LOOP, and it does
    not claim the new barrel is as good a bond as the old one for high
    frequency -- moving a ground bond moves a loop, and `screen_inert_copper`
    already says in its own words that area is not width.  It prices
    CONDUCTOR, which is the claim the gate can settle, and it names what it
    leaves to the reviewer.
    """
    import pcbnew
    sys.path.insert(0, str(HERE))
    import pour_bond_guard as pbg

    def barrels(board, net):
        """Every via of `net`, with the two numbers this clause compares."""
        out = []
        for t in board.Tracks():
            if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
                continue
            v = pcbnew.Cast_to_PCB_VIA(t)
            p = v.GetPosition()
            out.append((p, int(v.GetWidth()), int(v.GetDrillValue())))
        return out

    auth = pcbnew.LoadBoard(str(auth_path))
    cand = pcbnew.LoadBoard(str(cand_path))
    a_pours, c_pours = pbg.read_pours(auth), pbg.read_pours(cand)
    for p in a_pours:
        pbg.assign(auth, p)
    for p in c_pours:
        pbg.assign(cand, p)

    out = []
    for d in entries:
        bar = d["barrel"]
        net = d["net"]
        x, y = [int(round(v * 1e6)) for v in bar["at_mm"]]
        want_d = int(round(bar["dia_mm"] * 1e6))
        want_h = int(round(bar["drill_mm"] * 1e6))
        rec = dict(net=net, at_mm=bar["at_mm"], dia_mm=bar["dia_mm"],
                   drill_mm=bar["drill_mm"], served=[], ok=True, reason=None)
        P = pcbnew.VECTOR2I(x, y)
        for pour in a_pours:
            if pour["net"] != net:
                continue
            for isl in pour["islands"]:
                if not isl["poly"].Contains(P, -1, 0):
                    continue
                rec["served"].append(dict(
                    layer=pour["layer"], island=isl["index"],
                    island_area_mm2=round(isl["area_mm2"], 3),
                    pads=[q["ref"] for q in isl["pads"]],
                    other_barrels=max(0, len(isl["vias"]) - 1)))
        served_pads = sorted({q for s in rec["served"] for q in s["pads"]})
        if not served_pads:
            rec.update(reason="SERVED_NO_PAD")
            out.append(rec)
            continue
        # The pad's own position, read off the AUTHORITATIVE board: a pad does
        # not move and the candidate's fill is the only thing being re-asked.
        where = {}
        for fp in auth.GetFootprints():
            for q in fp.Pads():
                ref = "%s.%s" % (fp.GetReference(), q.GetNumber())
                if ref in served_pads and q.GetNetname() == net:
                    where[ref] = q.GetPosition()
        cand_vias = barrels(cand, net)
        rec["rebonds"] = []
        for ref in served_pads:
            pos = where.get(ref)
            hit = None
            if pos is not None:
                for pour in c_pours:
                    if pour["net"] != net:
                        continue
                    for isl in pour["islands"]:
                        if not isl["poly"].Contains(
                                pcbnew.VECTOR2I(pos.x, pos.y), -1, 0):
                            continue
                        good = [(p, w, h) for p, w, h in cand_vias
                                if w >= want_d and h >= want_h
                                and isl["poly"].Contains(
                                    pcbnew.VECTOR2I(p.x, p.y), -1, 0)]
                        cand_rec = dict(
                            pad=ref, layer=pour["layer"], island=isl["index"],
                            island_area_mm2=round(isl["area_mm2"], 3),
                            barrels=len(good),
                            nearest_mm=(round(min(
                                math.hypot(p.x - pos.x, p.y - pos.y)
                                for p, _, _ in good) / 1e6, 4)
                                if good else None))
                        if good or hit is None:
                            hit = cand_rec
                        if good:
                            break
                    if hit and hit.get("barrels"):
                        break
            if hit is None:
                hit = dict(pad=ref, layer=None, island=None, barrels=0,
                           nearest_mm=None)
            rec["rebonds"].append(hit)
        bad = [h for h in rec["rebonds"] if not h.get("barrels")]
        if bad:
            rec.update(ok=False, reason="NO_REPLACEMENT_BARREL_IN_THE_PAD_"
                                        "ISLAND",
                       unbonded=[h["pad"] for h in bad])
        out.append(rec)
    return out


def detour_apply(path, spec):
    """Remove every named track IN PLACE and resolve it to exact coordinates.

    Runs in a CHILD for the same reason `evict_copper` does -- removing tracks
    from a loaded `BOARD` and saving it leaves this KiCad build's SWIG bindings
    returning an untyped object from the next `LoadBoard`.

    A detour names a track by (net, layer, both endpoints, width) in
    millimetres.  Resolution must be EXACT and UNIQUE: a spec that matches no
    track, or more than one, is a spec whose author was describing a board that
    is not this one, and the run stops rather than guessing.  The endpoints the
    report carries are the BOARD's own integer nanometres, never the spec's
    rounded millimetres, because those coordinates are the whole contract -- a
    micron of drift at either end strands whatever met it.
    """
    import pcbnew
    import incremental_router as ir

    board = pcbnew.LoadBoard(str(path))
    lname = {}
    for k, v in (("F", pcbnew.F_Cu), ("I1", pcbnew.In1_Cu), ("I2", pcbnew.In2_Cu),
                 ("I3", pcbnew.In3_Cu), ("I4", pcbnew.In4_Cu),
                 ("B", pcbnew.B_Cu)):
        lname[board.GetLayerName(v)] = (k, v)

    def key(pt):
        return (round(pt.x / 1e6, 4), round(pt.y / 1e6, 4))

    def resolve(net, layer, a_mm, b_mm, width_mm, count=1):
        """The tracks this description names, or a hard stop.

        Resolution must be EXACT and COMPLETE: a description that matches a
        number of tracks OTHER than the number it declares is a description of
        a board that is not this one, and the run stops rather than guessing.

        `count` DEFAULTS TO 1 AND EVERY EXISTING SPEC IS UNCHANGED.  D-648.
        D-645 recorded that this board carries 93 EXACTLY DUPLICATE track
        objects, 28 of them on `GND`, and filed them as harmless -- "inert in
        the Gerber, but they inflate every object count a preservation check
        compares".  They are not harmless to a transaction: a description of a
        duplicated track matched two objects, `len(hits) != 1` stopped the run,
        and REMOVING ONE COPY WOULD LEAVE THE OTHER standing in exactly the
        corridor the removal was for.  Two coincident copies are ONE conductor
        and one obstacle; the physical unit is the pair, exactly as a barrel's
        physical unit is its hole and all six annuli.  So the spec may DECLARE
        the multiplicity, and declaring it is the only way to take it -- a
        silent "remove them all" would let a spec written against a
        de-duplicated board quietly take copper its author never saw.
        """
        if layer not in lname:
            raise SystemExit("--detour: no such copper layer %r" % layer)
        lkey, lid = lname[layer]
        want_pts = sorted([tuple(round(v, 4) for v in a_mm),
                           tuple(round(v, 4) for v in b_mm)])
        want_w = int(round(width_mm * 1e6))
        hits = [t for t in board.GetTracks()
                if t.GetClass() == "PCB_TRACK"
                and t.GetNetname() == net and t.GetLayer() == lid
                and t.GetWidth() == want_w
                and sorted([key(t.GetStart()), key(t.GetEnd())]) == want_pts]
        if len(hits) != int(count):
            raise SystemExit(
                "--detour: %s on %s %s..%s at %.3f mm matches %d tracks, "
                "not the %d this spec declares" % (net, layer, a_mm, b_mm,
                                                   width_mm, len(hits),
                                                   int(count)))
        return lkey, lid, hits

    # D-653 -- A BARREL IS THE SIXTH KIND OF OBJECT A TRANSACTION MAY NAME.
    #
    # Every move this file owns adds a bond or moves a track; none MOVES a
    # bond.  `--detour-spec` resolves `PCB_TRACK` and nothing else, so the one
    # object standing in `U2`'s I2C pocket that a transaction could not name
    # was the 0.600/0.300 mm `GND` barrel at (61.200, 90.800) -- and that
    # barrel is the ONLY connection between `B.Cu` `GND` island 24 (16.523 mm2,
    # one pad: `U2.21`) and the `In1`/`In4` planes.  D-652 recorded the gap and
    # called the missing move a RE-BOND: remove a pad's bond chain AND its
    # barrel, and let the run give that pad a new barrel somewhere else.
    #
    # THE PHYSICAL UNIT IS THE `PCB_VIA` OBJECT, and saying so is not
    # pedantry.  In the router's own model a barrel is SEVEN objects -- a
    # drill disc in `qb.holes` and one annulus per copper layer in
    # `qb.shapes[L]` -- and the first probe written for this decision held out
    # the drill alone, read `NO_PATH`, and would have recorded the corridor as
    # closed had it not been checked against `screen_corridor_blockers` on the
    # same window.  KiCad carries the hole and all six annuli as ONE item, so
    # the removal is one `board.Remove` and the licence is one `_via_sig`.
    #
    # Resolution is EXACT, UNIQUE and DECLARED, exactly as `resolve` is: the
    # net, the centre in millimetres, the diameter and the drill must all
    # match, and `count` (default 1) must equal the number of hits, so a spec
    # written against a board carrying coincident duplicate barrels cannot
    # take one and leave the other.
    def resolve_barrel(net, at_mm, dia_mm, drill_mm, count=1):
        want = tuple(round(v, 4) for v in at_mm)
        want_d = int(round(dia_mm * 1e6))
        want_h = int(round(drill_mm * 1e6))
        hits = []
        for t in board.GetTracks():
            if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
                continue
            v = pcbnew.Cast_to_PCB_VIA(t)
            if key(v.GetPosition()) != want:
                continue
            if int(v.GetWidth()) != want_d or int(v.GetDrillValue()) != want_h:
                continue
            hits.append(v)
        if len(hits) != int(count):
            raise SystemExit(
                "--detour: barrel %s at %s, %.3f/%.3f mm matches %d vias, not "
                "the %d this spec declares"
                % (net, at_mm, dia_mm, drill_mm, len(hits), int(count)))
        return hits

    # A CHAIN IS ONE TRACK THAT THE EDITOR HAPPENED TO SPLIT, AND THE BOARD SAYS
    # SO OR IT IS NOT A CHAIN.  `/ACC_DETECT_N` reaches the `+3V3` `R129.1`
    # pocket as two collinear `B.Cu` segments meeting at (59.05, 56.80), and
    # that junction is INSIDE the disc the barrel needs -- so detouring either
    # segment alone would have to terminate on a point the reservation forbids,
    # and both refuse.  Detouring the PAIR, from one free end to the other, is
    # the same move at the right granularity.
    #
    # What makes it safe is not that the segments look collinear; it is that
    # NOTHING ELSE OF THAT NET MEETS THE INTERIOR JUNCTIONS.  A chain whose
    # middle carries a barrel, a pad or a third branch is a TEE, and removing it
    # would strand whatever hung off it -- so the interior is measured against
    # every track, via and pad of the net on the board, and a chain that fails
    # that test stops the run by name.  One layer and one width throughout, too:
    # "lay it again as one run" cannot mean "and change its width halfway".
    def chain_ends(net, items, lid, mine=None):
        """The two free ends of a simple chain.

        `items` is ONE representative per DESCRIPTION and `mine` is every
        object those descriptions resolved to.  The distinction is D-648's:
        a duplicated track contributes ONE edge to the topology -- two
        coincident copies are one conductor -- but BOTH copies must be in
        `mine`, or the second copy is found standing on the chain's own
        interior junction and the run stops calling it a tee.
        """
        deg = {}
        for t in items:
            for pt in (key(t.GetStart()), key(t.GetEnd())):
                deg[pt] = deg.get(pt, 0) + 1
        ends = sorted(p for p, n in deg.items() if n == 1)
        inner = sorted(p for p, n in deg.items() if n != 1)
        if len(ends) != 2 or any(deg[p] != 2 for p in inner):
            raise SystemExit(
                "--detour: the %d tracks named on %s do not form a simple "
                "chain (%d free ends)" % (len(items), net, len(ends)))
        # IDENTITY IS THE ITEM UUID, NEVER `id()`.  `items` and this walk come
        # from separate `GetTracks()` passes and this KiCad build hands out a
        # fresh SWIG proxy each time, so a Python identity set matches nothing
        # and every chain would report itself as a tee -- which is exactly what
        # the first run of this check did.  `evict_closure` learned the same
        # lesson and says so in the same words.
        mine = {uid(t) for t in (mine if mine is not None else items)}
        for pt in inner:
            P = pcbnew.VECTOR2I(int(round(pt[0] * 1e6)),
                                int(round(pt[1] * 1e6)))
            for t in board.GetTracks():
                if t.GetNetname() != net or uid(t) in mine:
                    continue
                if t.GetClass() == "PCB_VIA":
                    if key(t.GetStart()) == pt:
                        raise SystemExit(
                            "--detour: a via of %s sits on the chain's "
                            "interior junction at %s; that is a tee, not a "
                            "chain" % (net, pt))
                elif t.GetLayer() == lid and (key(t.GetStart()) == pt
                                              or key(t.GetEnd()) == pt):
                    raise SystemExit(
                        "--detour: a third track of %s meets the chain's "
                        "interior junction at %s; that is a tee, not a chain"
                        % (net, pt))
            for f in board.GetFootprints():
                for pad in f.Pads():
                    if pad.GetNetname() == net and pad.HitTest(P):
                        raise SystemExit(
                            "--detour: pad %s.%s of %s covers the chain's "
                            "interior junction at %s; that is a tee, not a "
                            "chain" % (f.GetReference(), pad.GetNumber(),
                                       net, pt))
        return ends

    doomed, resolved, doomed_vias, born = [], [], [], []
    for d in spec.get("detours", ()):
        # D-653.  A BARREL ENTRY IS NOT A DETOUR AND DOES NOT PRETEND TO BE.
        # A relay puts the same conductor back between its own two ends; a
        # barrel's two ends are on different LAYERS and no track can stand in
        # for it, so a barrel is always `relay: false` and the gate prices it
        # under `rebond_priced` -- "the copper this barrel served still reaches
        # this net's plane through a barrel at least as wide" -- rather than
        # under `inert_removal_priced`, which asks about a pour path between
        # two points on ONE layer and has no meaning here.
        if "barrel" in d:
            q = d["barrel"]
            if d.get("relay", False):
                raise SystemExit("--detour: barrel %s at %s cannot declare "
                                 "`relay: true`; a barrel has no two ends on "
                                 "one layer to be re-laid between"
                                 % (d["net"], q["at_mm"]))
            vias = resolve_barrel(d["net"], q["at_mm"], q["dia_mm"],
                                  q["drill_mm"], q.get("count", 1))
            v = vias[0]
            doomed_vias += vias
            top = board.GetLayerName(v.TopLayer())
            bottom = board.GetLayerName(v.BottomLayer())
            # THE MOVE.  A barrel may declare WHERE IT GOES, and then this is
            # a MOVE and not a removal: the same net, the same diameter, the
            # same drill, the same two end layers, at a site the spec NAMES.
            #
            # Naming it is the point.  `--bond-pad` re-bonds by SEARCH, and on
            # the transaction this primitive was built for the search is the
            # wrong instrument twice over: `stitch_pad` re-derives the barrel
            # site the board already had (1.705 mm, (61.200, 90.800) --
            # exactly the copper the run is removing), and steering it away
            # with a `reserve` disc moves the BARREL but not the RUN, because
            # `QBoard.smooth` straightens a lattice path against the board's
            # own obstacle geometry and the pour-bond guard is not part of it.
            # Measured on this board: a 1.5 mm reserve disc centred 0.70 mm
            # off the run left the run unchanged to the micron.  A site a
            # human picked off `screen_bond_ladder`'s own island-barrel census
            # is reviewable, reproducible and exact; a site a search picked
            # under a guard that does not bind it is neither.
            to = q.get("to_mm")
            moved = None
            # D-658.  A MOVE MAY ALSO BE A RESIZE, and the two levers were only
            # ever refuted SEPARATELY.  On `Net-(U11-TS_MR)` the shrink alone
            # left `+3V3`'s `R129.1` severed at every rung down to 0.350/0.200
            # (`evidence/d657-barrel-shrink.json`) and the move alone freed it
            # only at +0.300 mm, where the barrel lands inside `/ACC_3V3_SW`'s
            # 0.250 mm rule clearance -- a rail `AQROOT_DEMO_SCOPE` requires.
            # The antipad a barrel subtracts from a pour and the clearance it
            # demands from its neighbours are the SAME radius, so shrink-and-
            # move is a different question from either arm, and the answer is
            # 0.450/0.200 at +0.200 mm: `via_diameter` and NOTHING else
            # (`evidence/d658-barrel-move-0450.json`).
            #
            # A geometry under the board's own `min_via_diameter` is a
            # FABRICATION EXCEPTION and is licensed exactly as a bridge barrel's
            # is -- `.kicad_dru` rule authored first, rule area drawn by this
            # run, audited by clause 6, checked by `barrel_move_licensed`.
            new_dia = (int(round(q["to_dia_mm"] * 1e6)) if q.get("to_dia_mm")
                       else int(v.GetWidth()))
            new_drill = (int(round(q["to_drill_mm"] * 1e6))
                         if q.get("to_drill_mm") else int(v.GetDrillValue()))
            if (new_dia, new_drill) != (int(v.GetWidth()),
                                        int(v.GetDrillValue())) and to is None:
                raise SystemExit(
                    "--detour: barrel %s at %s declares a new geometry but no "
                    "`to_mm`; resizing a barrel in place is a different "
                    "transaction and this primitive does not express it"
                    % (d["net"], q["at_mm"]))
            if new_dia - new_drill < 2 * ANNULAR_MIN:
                raise SystemExit(
                    "--detour: barrel %s at %s -> %.3f/%.3f mm is an annular "
                    "ring of %.4f mm, under the %.3f mm floor; no rule area "
                    "licenses a ring this board cannot plate"
                    % (d["net"], q["at_mm"], new_dia / 1e6, new_drill / 1e6,
                       (new_dia - new_drill) / 2e6, ANNULAR_MIN / 1e6))
            if to is not None:
                nv = pcbnew.PCB_VIA(board)
                nv.SetPosition(pcbnew.VECTOR2I(int(round(to[0] * 1e6)),
                                               int(round(to[1] * 1e6))))
                nv.SetWidth(new_dia)
                nv.SetDrill(new_drill)
                nv.SetViaType(v.GetViaType())
                nv.SetLayerPair(v.TopLayer(), v.BottomLayer())
                nv.SetNetCode(v.GetNetCode())
                born.append(nv)
                moved = [round(float(c), 4) for c in to]
            resolved.append(dict(
                net=d["net"], layer=top,
                lkey=lname[top][0] if top in lname else "F",
                relay=False, barrel=dict(
                    at_mm=[round(c, 4) for c in key(v.GetPosition())],
                    dia_mm=round(int(v.GetWidth()) / 1e6, 4),
                    drill_mm=round(int(v.GetDrillValue()) / 1e6, 4),
                    top=top, bottom=bottom, count=len(vias), to_mm=moved,
                    to_dia_mm=(round(new_dia / 1e6, 4) if moved else None),
                    to_drill_mm=(round(new_drill / 1e6, 4) if moved else None),
                    was_at_nm=[int(v.GetPosition().x), int(v.GetPosition().y)]),
                width_nm=int(v.GetWidth()), tracks=0, objects=len(vias),
                a_nm=[int(v.GetPosition().x), int(v.GetPosition().y)],
                b_nm=[int(v.GetPosition().x), int(v.GetPosition().y)],
                mm=0.0, max_mm=0.0, exact_relay=None))
            continue
        parts = list(d.get("tracks") or [d])
        got = [resolve(d["net"], q["layer"], q["a_mm"], q["b_mm"],
                       q["width_mm"], q.get("count", 1)) for q in parts]
        if len({(g[0], g[2][0].GetWidth()) for g in got}) != 1:
            raise SystemExit("--detour: a chain must be ONE layer and ONE "
                             "width throughout (%s)" % d["net"])
        lkey, lid = got[0][0], got[0][1]
        # ONE REPRESENTATIVE PER DESCRIPTION carries the TOPOLOGY and the
        # LENGTH; every copy carries the REMOVAL.  D-648.  Coincident
        # duplicates are one conductor, so counting their millimetres twice
        # would charge `inert_removal_price` a bar this copper never was.
        reps = [g[2][0] for g in got]
        items = [t for g in got for t in g[2]]
        if len(reps) == 1:
            t = reps[0]
            a_nm = [int(t.GetStart().x), int(t.GetStart().y)]
            b_nm = [int(t.GetEnd().x), int(t.GetEnd().y)]
        else:
            ends = chain_ends(d["net"], reps, lid, mine=items)
            a_nm = [int(round(v * 1e6)) for v in ends[0]]
            b_nm = [int(round(v * 1e6)) for v in ends[1]]
        t = reps[0]
        # D-658 -- A CHAIN MAY BE RE-LAID TO A POINT IT NEVER TOUCHED.
        #
        # Every relay this file has laid until now put a conductor back between
        # ITS OWN TWO ENDS: the copper moves, its terminals do not.  That is the
        # right contract when the reason for the detour is a corridor.  It is
        # the WRONG one when the reason is a BARREL MOVE, and D-657 measured the
        # price of not having the difference.  `--detour-spec`'s barrel entry
        # already accepts `to_mm` and calls that a MOVE (D-653); what it could
        # not do was bring the TRACK ENDS THAT LANDED ON THE OLD SITE with it.
        # So the only way to move a barrel and keep its net whole was to EVICT
        # the whole net and let the router re-derive it -- and on
        # `Net-(U11-TS_MR)`, a two-pad strap whose MST spans the board, that
        # meant 77.317 mm to move two barrels 0.05 mm, or 138.875 mm to move
        # them at all, on a southern haul that pinched a `GND` return fragment
        # to 2.117 A against its own 2.19 A bar and was refused by `PP2`
        # (`evidence/d657-gate-dryrun2.json`, `-dryrun3`, `-dryrun5`).  Nothing
        # about that haul was asked for; it was the only shape the primitive
        # could express.
        #
        # `move_ends` is that shape, stated exactly: for each entry, `from_mm`
        # must be one of THIS chain's OWN free ends and `to_mm` is where that
        # end now goes.  Both ends may move -- the `In2` hop BETWEEN two moved
        # barrels has no stationary end at all -- and neither may move twice.
        # Resolution is EXACT, as everywhere else here: an end this chain does
        # not have is a description of a board that is not this one and stops
        # the run, because a spec whose `from_mm` silently matched nothing would
        # relay the chain to its OLD site and quietly leave the barrel it was
        # written to follow standing alone.
        moves = []
        for mv in d.get("move_ends", ()):
            f = [int(round(v * 1e6)) for v in mv["from_mm"]]
            g = [int(round(v * 1e6)) for v in mv["to_mm"]]
            if f == a_nm and ("a" not in [m["end"] for m in moves]):
                a_nm, which = g, "a"
            elif f == b_nm and ("b" not in [m["end"] for m in moves]):
                b_nm, which = g, "b"
            else:
                raise SystemExit(
                    "--detour: move_ends names %s on %s, which is not one of "
                    "this chain's two free ends (%s, %s) or has already been "
                    "moved"
                    % (mv["from_mm"], d["net"],
                       [round(v / 1e6, 4) for v in a_nm],
                       [round(v / 1e6, 4) for v in b_nm]))
            moves.append(dict(end=which,
                              from_mm=[round(v / 1e6, 4) for v in f],
                              to_mm=[round(v / 1e6, 4) for v in g],
                              mm=round(math.hypot(g[0] - f[0],
                                                  g[1] - f[1]) / 1e6, 4)))
        doomed += items
        was = sum(math.hypot(q.GetEnd().x - q.GetStart().x,
                             q.GetEnd().y - q.GetStart().y)
                  for q in reps) / 1e6
        # THE BOUND IS MEASURED OFF THE RESERVATION, NOT CHOSEN.  Walking the
        # whole way round a reserved circle of radius R adds at most its
        # circumference, so `was + 2*pi*R_max` is the longest a genuine detour
        # of THIS track past THESE discs can be.  A route longer than that went
        # somewhere else entirely -- measured on `/NFC_5V_EN`, 2.500 mm of
        # track that came back 21.418 mm long -- and is a reroute wearing a
        # detour's name.  A spec may state its own `max_mm` and own that
        # judgement explicitly; it may not silently exceed this one.
        rmax = max([r["r_mm"] for r in spec.get("reserve", ())] or [0.0])
        # AND THE BOUND FOLLOWS THE ENDS.  `was + 2*pi*R_max` bounds a detour of
        # THIS track past THESE discs; a chain whose ends have MOVED is not that
        # track, and the shortest run it could possibly be is longer by at most
        # the displacements themselves (a -> to is never worse than a -> from ->
        # to).  So the default bound gains exactly the millimetres the spec
        # declared it was moving, and nothing else; a spec may still state its
        # own `max_mm` and own that judgement explicitly.
        movemm = sum(m["mm"] for m in moves)
        resolved.append(dict(
            net=d["net"], layer=parts[0]["layer"], lkey=lkey,
            # D-646.  A detour entry may declare `"relay": false`, and then
            # this chain is REMOVED AND NOT PUT BACK.  That is a strictly
            # larger claim than a relay -- a relay owes the board the same
            # conductor somewhere else, a removal owes it a conductor the
            # board ALREADY HAS -- so it is not admitted by the spec saying
            # so.  The gate's `inert_removal_priced` clause makes the
            # CANDIDATE prove it: same net, no new open edge, both ends in one
            # KiCad cluster, and the pour path that replaces the copper at
            # least as wide as the copper removed.
            relay=bool(d.get("relay", True)),
            width_nm=int(t.GetWidth()), tracks=len(reps),
            objects=len(items),
            a_nm=a_nm, b_nm=b_nm,
            mm=round(was, 4),
            move_ends=moves,
            max_mm=round(float(d.get("max_mm",
                                     was + 2.0 * math.pi * rmax + movemm)), 4),
            # Carried, never invented: the spec names the allowlisted
            # exact-geometry route that may stand in when the LATTICE refuses
            # this relay, and `exact_relay_pads` still has to agree it is the
            # same net and the same two ends before it is spent.
            exact_relay=d.get("exact_relay")))
    sigs = []
    for t in doomed:
        sigs.append(ir._track_sig(t))
        board.Remove(t)
    # D-653.  The same licence, in the same shape, for the barrel: clause 5
    # compares `ir.copper_sigs` before and after, and that counter already
    # keys a `PCB_VIA` by `_via_sig`, so a barrel removed without its
    # signature recorded here would be an UNLICENSED REMOVAL and refuse the
    # run -- which is exactly the protection this line is spending.
    for v in doomed_vias:
        sigs.append(ir._via_sig(v))
        board.Remove(v)
    # THE MOVED BARREL IS LAID BY THE APPLIER, NOT BY THE ROUTER, and the gate
    # is told whose copper it is: `detour_nets` already admits a detoured net
    # into the promotion set, so clause 5's "no foreign copper" reads this via
    # as GND copper THIS transaction asked for -- which is exactly what it is.
    for v in born:
        board.Add(v)
    pcbnew.SaveBoard(str(path), board)
    return dict(detours=resolved,
                reserve=list(spec.get("reserve", ())),
                removed_signatures=sorted(str(s) for s in sigs),
                removed_count=len(sigs),
                removed_barrels=len(doomed_vias),
                moved_barrels=[[round(v.GetPosition().x / 1e6, 4),
                                round(v.GetPosition().y / 1e6, 4)] for v in born],
                removed_mm=round(sum(d["mm"] for d in resolved), 4),
                nets=sorted({d["net"] for d in resolved}))


# --------------------------------------------------------------------------- #
# INNER PLANES ARE NOT SIGNAL LAYERS ANY MORE
# --------------------------------------------------------------------------- #
# `qrouter.ROUTABLE` calls the six-layer stack `F, B, In2, In3` -- In1 and In4
# are the solid GND references and were never routable.  That was the truth of
# this board until D-580 poured `+3V3` on `In3.Cu`.  It is not the truth now.
#
# The first `--partial` run measured the consequence rather than arguing it: a
# nine-island `/I2C_SCL_INT` proposal closed five edges and took FOUR of its
# five joins across `In3`, and the gate refused the whole run because `+3V3`
# REGRESSED -- foreign copper on a plane layer is a SLOT through that plane,
# and a slot long enough separates pads the pour used to bond.  D-580 predicted
# exactly this refusal in writing; this is it happening.
#
# The connectivity regression is only the visible half.  A track laid through a
# power plane also breaks the return path of every signal that crosses the slot
# and lengthens the PDN loop the plane exists to shorten, and neither of those
# shows up in a ledger at all.  So a layer that carries an INNER pour is
# reserved to the net that owns it, and the maze routes foreign nets on the
# three layers this board actually has left: `F`, `B` and `In2`.
#
# OUTER pours are deliberately NOT reserved.  The `+3V3` pour on `F.Cu` and the
# `GND` pour on `B.Cu` are fill-in copper on layers whose job is signal routing
# -- they flow around whatever is routed and were poured knowing it.  Reserving
# them would leave this board one signal layer, which is not a rule, it is a
# shutdown.  The no-net-regressed gate clause still governs them, so an outer
# pour that a run actually severs is still refused, and refused on the same
# evidence that produced this rule.
INNER = {"In1.Cu": "I1", "In2.Cu": "I2", "In3.Cu": "I3", "In4.Cu": "I4"}


def reserved_inner_planes(board):
    """Short names of the inner layers a filled pour owns, mapped to its nets.

    Read from the BOARD, not transcribed: pour one more inner plane tomorrow
    and the router reserves it on the next run with no edit here.
    """
    out = {}
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsFilled():
            continue
        for layer in z.GetLayerSet().Seq():
            name = board.GetLayerName(layer)
            if name in INNER:
                out.setdefault(INNER[name], set()).add(z.GetNetname())
    return out


def permitted_layers(routable, contract_layers, reserved, net):
    """The layers this net may lay copper on, after plane reservation.

    A net that OWNS a plane still routes on it -- its own copper is not a slot
    through the plane, it is more of the same plane -- so the reservation is
    per (layer, net) and never a blanket layer ban.
    """
    allowed = tuple(contract_layers or routable)
    keep = tuple(L for L in allowed
                 if net in reserved.get(L, ()) or L not in reserved)
    return keep or allowed


# --------------------------------------------------------------------------- #
# A DETOUR MAY RE-LAY A TRACK ON THE LAYER IT ALREADY LAWFULLY OCCUPIES
# --------------------------------------------------------------------------- #
# D-609.  `reserved_inner_planes` is a rule about NEW copper: do not cut a slot
# through somebody else's plane.  A DETOUR is not new copper.  It removes an
# existing track WHOLE and lays it again between its OWN TWO END COORDINATES,
# and D-607 built it precisely so that nothing is stranded and the cut net's
# cluster count cannot move.  Applying the plane reservation to it therefore
# answers a question nobody asked: the slot ALREADY EXISTS, it was cut before
# the plane was poured, and the only thing in dispute is where within a
# millimetre or two of itself it runs.
#
# The census is in `evidence/d608-undetourable-copper.json` and it is not
# small: 111 tracks / 969.6 mm of this board's 3054 / 8712.6 mm lie on a layer
# their own net may no longer route on, 29 (net, layer) pairs, EVERY ONE on
# `In3.Cu` -- legacy signal copper routed before the `+3V3` pour existed.
# `relay_price` reports each of them `UNDETOURABLE_LAYER`, and the FIRST thing
# that blocked is the single highest-leverage bond on this board: `U12.5`, the
# `TPS63020`'s own `VOUT`, whose barrel site is crossed by 27.119 mm of
# `/01_POWER_TREE/USB_VBUS_CHG` on `In3.Cu`.
#
# THE ALLOWANCE IS THE TIGHTEST ONE THAT EXISTS, AND THAT IS DELIBERATE.  A
# detour that spends it routes on THAT ONE LAYER AND NOTHING ELSE -- not on the
# union of its contract and its own layer.  Two consequences follow by
# construction rather than by clause:
#
#   * it CANNOT add a via, because a single-layer `Field` has no second layer
#     to via to -- so this allowance can never drill a new hole and a new
#     antipad through the plane it is being let back onto;
#   * it cannot wander onto a DIFFERENT reserved plane, because the only layer
#     it was given is the one it already had.
#
# What it can still do is occupy MORE of that plane than it did -- the bound is
# `was + 2*pi*R`, so at `R = 0.8 mm` the worst case is about 5 mm of extra slot.
# That is not free and it is not hidden: `mm_by_layer` reports it, gate clause 4
# measures the plane's own connectivity after a real refill, and a detour that
# actually severs the plane it crosses regresses that net and refuses the run.
# The allowance is OPT-IN per run for the same reason: it is a judgement about
# ONE transaction's copper, not a change to what this board considers routable.
def detour_layers(permitted, lkey, own_layer):
    """The layers ONE detour may use, and whether it spent the D-609 allowance.

    Returns (layers, spent).  Absent the allowance, or when the track's layer
    is one this net may route on anyway, this is exactly `permitted` and
    nothing about the run changes.
    """
    permitted = tuple(permitted)
    if lkey in permitted:
        return permitted, False
    if not own_layer:
        return permitted, False
    return (lkey,), True


# Nets excluded from generic maze routing.  Each is a documented physics or
# governance constraint the maze proposer does not model, NOT a difficulty
# judgement: it must keep being routed by its own purpose-built harness.
# The USB pair was here and is NOT any more, and the reason is a measurement
# rather than a change of appetite.  The exclusion said the maze does not model
# "gap / uncoupled DRU" physics, which is true of the PROPOSER and irrelevant to
# the AUTHORITY: `diff_pair_gap`, `diff_pair_uncoupled` and the In2 prohibition
# are real KiCad constraints that gate clause 3 already runs at
# `--severity-all`, and the first F/B screen was refused BY THEM -- eight
# `items_not_allowed` and one `diff_pair_uncoupled_length_too_long`.  A rule the
# gate enforces does not need a second enforcement by abstention.
#
# The physics itself is recorded in `.kicad_dru` section 6 and is not in doubt:
# ESP32-S3 has no High-Speed PHY, so this is USB 2.0 FULL SPEED at 12 Mbit/s
# over ~40 mm, "does NOT need impedance control, does NOT need length matching
# and does NOT need a via".  What the pair DOES need -- stay on F.Cu, keep the
# uncoupled budget -- is expressed to the router as the `USB_D` single-layer
# contract above and re-proved by KiCad afterwards.
#
# THE NFC RECEIVE PAIR WAS HERE AND IS NOT ANY MORE, for exactly the reason the
# USB pair left: the note read "NFC receive arms: length/symmetry", and that is
# a real constraint with NO enforcer -- `.kicad_dru` section 7 says only "NFC
# receive path stays on B.Cu" and has no length or symmetry rule at all, so the
# exclusion was ABSTENTION STANDING IN FOR A MEASUREMENT.  D-621 built the
# measurement instead: `checks/rf_symmetry_contract.py` RF1-RF5 reads the
# copper on all four front-end nets and judges the transmit arms' A/B mismatch
# against a DECLARED budget and the receive pair's against the bound the
# PLACEMENT itself imposes (|direct(U9.22->R116.2) - direct(U9.23->R117.2)| =
# 0.7085 mm), plus topological symmetry -- same barrel count, same layer set.
# A constraint a contract enforces does not need a second enforcement by
# abstention, and the first gated run under it measured the pair at 12.925 /
# 12.492 mm, 4 barrels each, `B/I2/B/I2/B` each: a 0.433 mm mismatch inside a
# 0.709 mm placement bound.  Also measured, and the reason the contract had to
# exist first: the relay this run needed would have cost the TRANSMIT arm
# +6.583 mm had `C17` stayed in the receive channel, and nothing on this board
# could have reported it.
#
# The set is empty on purpose rather than deleted: the mechanism is the right
# one for a net whose physics genuinely has no enforcer, and the day one appears
# it belongs here with its reason written down.
EXCLUDE = set()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


# A CLEARANCE THIS BOARD OWES A PAD IS NOT THE ONE IT OWES A TRACK, AND THE
# `.kicad_dru` SAYS SO IN WORDS.  Every elevated figure in `DRU_CLASS["clr"]`
# comes from a section-8 "routed clearance" rule, and every one of those rules
# carries `A.Type != 'Pad' && B.Type != 'Pad'`.  The section's own header states
# the intent rather than leaving it to be inferred:
#
#     Elevated clearances below are ROUTING clearances: they are scoped so
#     that vendor land patterns (J1 FH69 0.5 mm pitch, J3 USB-C, U11 WSON
#     0.4 mm pitch, U12 VSON, U14 WLP) are judged against the 0.20 mm
#     global figure they actually satisfy, not against a routing target.
#
# `net_contract` collapsed both into ONE scalar and every caller handed it to
# `maze3d.Field` as BOTH `clr_pad` and `clr_trk`, so the proposer owed a PAD a
# routing target the board judges at 0.20 mm.  That is not conservatism, it is
# a different rule: a fine-pitch land pattern is exactly where the extra tenths
# decide whether a pin can launch at all.  `maze3d` already models the
# distinction correctly -- `dru_overlay` and `obs_clearance` raise a track's or
# via's clearance by `CLASS_TRK_CLR` and skip that raise for a pad -- so the
# elevated figure is still applied to routed copper with no caller change at
# all, and the ONLY thing this split removes is the raise against pads.
#
# MEASURED, on `bfef0aa2...`, over every open retained net: it changes exactly
# one verdict.  `/03_SPI_A_DISPLAY_SD/LED_A` `J1.1 -> R71.2` reads
# `NO_LEGAL_ESCAPE_SRC` at 0.30 mm and routes at 0.20 mm -- the display
# backlight anode leaving the J1 FH69 flex land pattern the header names.
#
# BAT_MAIN IS DELIBERATELY NOT SPLIT.  Its 0.30 mm rule is D-269, the retained
# battery-safety clearance, and although that rule is written with the same
# pad exclusion, nothing currently open is BAT_MAIN, so relaxing the proposer
# there buys nothing and would make a safety ruling depend on reading its rule
# text the same way twice.  The conservatism is named here rather than hidden.
PAD_CLR_RETAINED = {"BAT_MAIN": 300000}


# --------------------------------------------------------------------------- #
# THE TRUNK FLOOR -- D-662
# --------------------------------------------------------------------------- #
# `--escape-floor` (D-630) lets a LAND launch at the width `.kicad_dru` section
# 5 publishes as its class MINIMUM instead of the `opt` figure the netclass
# carries.  It fixed the launch and left the other half of the same defect in
# place: `net_contract` takes `max(netclass width, DRU min)`, so the netclass
# `opt` becomes the width of the whole TRUNK, and a rail whose corridor is
# 0.400 mm wide is refused at 0.600 mm even though 0.400 mm is the width the
# board's own rule ENFORCES as legal for that class.
#
# `/NFC_SUPPLY` is the case that forced this.  `U9.8` is the ST25R3916's `VDD`
# and has NO supply connection today; `R107.2 -> U9.8` is `NO_PATH` at
# 0.600 mm at every pitch asked and ROUTES IN 13.806 mm at 0.400 mm and a
# 0.050 mm lattice.  Nothing about that copper needs a licence -- 0.400 mm is
# the minimum `(rule "P3V3 minimum width")` itself states.
#
# THIS IS A DESCENT, AND IT IS PRICED BEFORE IT IS TAKEN.  The floor is only
# offered where the class's published minimum, judged by IPC-2221B at this
# board's copper by the SAME `audit_bond_ampacity` call `PP2` uses, carries the
# design current `.kicad_dru` section 5 publishes for that class.  A class the
# table does not price does not move, and neither does one the price refuses:
# on this board that admits `P3V3`, `ACC_3V3`, `ACC_5V`, `SPK_OUT` and
# `VBUS_CHG`, and REFUSES `BAT_MAIN` (1.645 A at its floor against a 3.125 A
# bar), `SYS_MAIN` (1.441 A against 2.190 A), `NFC_RF`, `NFC_5V_PA` and
# `SWITCH_NODE` (no published current at all).  The refusal is RECORDED in the
# run's own contract, never silent, so a net that did not descend says so.
TRUNK_FLOOR_DT_K = 10.0                 # the dT `.kicad_dru` section 5 uses


def trunk_floor_price(cls, board_min_nm=0):
    """May this netclass route its TRUNK at the DRU-published class minimum?

    Read-only, deterministic and self-policing: the answer is the board's own
    published design current weighed against the board's own published class
    floor, so no figure here is transcribed and none is invented.
    """
    # `pour_partition_contract` lives in `checks/`, which this module does not
    # otherwise need on `sys.path`; the price is read from the SAME parser
    # `PP2` charges a bond with, so the two clauses cannot drift apart.
    if str(HERE / "checks") not in sys.path:
        sys.path.insert(0, str(HERE / "checks"))
    import audit_bond_ampacity as ab
    from pour_partition_contract import published_rail_currents
    floor = DRU_CLASS.get(cls, {}).get("width")
    out = dict(netclass=cls, floor_nm=floor, admitted=False,
               amps=None, required_amps=None, why=None)
    if not floor:
        out["why"] = "CLASS_HAS_NO_PUBLISHED_FLOOR"
        return out
    floor = max(floor, board_min_nm or 0)
    out["floor_nm"] = floor
    table, _ = published_rail_currents(str(BOARD.with_suffix(".kicad_dru")))
    required = (table.get(cls) or {}).get("amps")
    amps = round(ab.ampacity(ab.track_area(floor / 1e6), TRUNK_FLOOR_DT_K), 3)
    out["amps"], out["required_amps"] = amps, required
    if required is None:
        out["why"] = "NET_CARRIES_NO_PUBLISHED_CURRENT"
        return out
    if amps + 1e-9 < required:
        out["why"] = "TRUNK_UNDER_PRICED"
        return out
    out["admitted"], out["why"] = True, "PRICED_AT_THE_PUBLISHED_BAR"
    return out


def net_contract(board, net, trunk_floor=False):
    """The width / clearance / via / layer contract for ONE net.

    `clr` is the clearance owed ROUTED copper -- a track or a via -- and
    `clr_pad` the clearance owed a PAD.  See `PAD_CLR_RETAINED` above for why
    they are two numbers and why exactly one class keeps them equal.

    With `trunk_floor` the width DESCENDS to the class's published minimum
    where `trunk_floor_price` admits it -- see the block above.  The default is
    the behaviour every promoted route up to D-661 was proposed under, byte for
    byte.
    """
    info = board.FindNet(net)
    if info is None:
        raise SystemExit("net %r is not on the board" % net)
    cls = info.GetNetClassName()
    nc = info.GetNetClassSlow()
    over = DRU_CLASS.get(cls, {})
    width = max(nc.GetTrackWidth(), over.get("width", 0))
    cap = over.get("width_cap")
    if cap is not None:
        width = min(width, cap)
    floor_price = None
    if trunk_floor:
        board_min = board.GetDesignSettings().m_TrackMinWidth
        floor_price = trunk_floor_price(cls, board_min)
        # A DESCENT ONLY.  A class whose floor is at or above the width this
        # net already routes at cannot be widened by asking for its floor.
        if floor_price["admitted"] and floor_price["floor_nm"] < width:
            floor_price["from_nm"], floor_price["to_nm"] = \
                width, floor_price["floor_nm"]
            width = floor_price["floor_nm"]
        else:
            floor_price["from_nm"] = floor_price["to_nm"] = width
            if floor_price["admitted"]:
                floor_price["admitted"] = False
                floor_price["why"] = "FLOOR_IS_NOT_BELOW_THE_ROUTED_WIDTH"
    return dict(
        net=net, netclass=cls,
        width=width,
        clr=max(nc.GetClearance(), over.get("clr", 0)),
        clr_pad=max(nc.GetClearance(), PAD_CLR_RETAINED.get(cls, 0)),
        via_dia=nc.GetViaDiameter(), via_drill=nc.GetViaDrill(),
        layers=over.get("layers"),
        known_class=cls in DRU_CLASS,
        trunk_floor=floor_price,
    )


# --------------------------------------------------------------------------- #
# child: propose copper on a scratch board
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# pour-bond guard
# --------------------------------------------------------------------------- #
def load_guard(path):
    """Read a `pour_bond_guard.py` spec, or {} when no guard was asked for."""
    if not path:
        return {}
    return json.loads(Path(path).read_text())


def guard_for(spec, net):
    """{layer: [(x, y, keepout_nm), ...]} this net must keep clear.

    A pour's OWN net is exempt from its OWN tubes: the tube is that net's
    copper, so its stitch and its residual joins may run straight down it.  A
    guard on the OTHER pour's layer still binds -- `GND` may not slot `+3V3`'s
    bond any more than a signal net may.

    `exempt` GENERALISES that one-net rule to a FAMILY, and a corridor
    reservation is why it has to.  A bond tube belongs to exactly one net, so
    the record's own `net` field is the whole exemption; a lane reserved for a
    differential pair belongs to several, and `USB_D_CONN_N` must be as free to
    run down the USB corridor as `USB_D_CONN_P` is.  Absent from a record --
    which is every record `pour_bond_guard.py` has ever written -- the list is
    empty and this function is byte-identical to the one that had no such
    concept.  `reserve_corridor.py` is the emitter that fills it in.
    """
    out = {}
    for g in spec.get("guards", ()):
        if not g.get("ok") or g["net"] == net or net in g.get("exempt", ()):
            continue
        # D-610.  `point_keepout` is the PER-POINT figure: the widest disc the
        # tube actually occupies THERE, capped at the spec's own tube radius.
        # `keepout_radius` -- the single narrowest-place figure -- is the
        # fallback, so a spec written before this existed (and every
        # `detour_guard` record, which is a disc and not a tube) reads exactly
        # as it did.
        per = g.get("point_keepout")
        out.setdefault(g["lkey"], []).extend(
            (p[0], p[1], (per[i] if per else g["keepout_radius"]))
            for i, p in enumerate(g["points"]))
    return out


def terminal_lift(guard, lkey, ends, width_nm, grid_nm):
    """Lift a reservation off a relay's OWN TWO FIXED ENDS -- D-667.

    Returns `({lkey: [(x, y, keepout_nm), ...]}, [report, ...])` in
    `maze3d.Field(guard_free=...)`'s shape, or `({}, [])` when no reservation
    covers either end -- which is every run this file has ever made.

    A `--detour-spec` relay is asked to put a named chain back between its own
    two ends.  Those ends are not the transaction's to choose: they are the
    coordinates where the net's RETAINED conductor stands, and the relay is
    `WRONG_TERMINAL_LAYER` if it arrives anywhere else.  A corridor reservation
    is a rule about where NEW copper may lie, so it cannot coherently forbid
    them -- and it does, systematically, because of a half-lattice of arithmetic:

        guard reach   keepout + width/2 + G   0.300 + 0.100 + 0.050 = 0.450 mm
        DRC-legal     w/2 + clearance + w/2   0.100 + 0.200 + 0.100 = 0.400 mm

    A reservation is 0.050 mm STRONGER than the clearance rule it stands for,
    and it is strongest precisely where foreign copper legally hugs the lane.
    The ends of the copper the lane's own route DISPLACED are exactly there, by
    construction: the route went where that copper was.  D-666 arms D and E
    measured `NO_PATH` on both relays of the `/WAKE_INT_N` transaction at 15.0
    and 12.0 mm of budget and concluded the lane was "too strong"; the true
    reading is that `/IR_TX_GPIO16`'s goal cell lay 0.1597 mm from the lane
    centreline and `/SX1262_CS_N`'s 0.1510 mm, on all three reserved layers.
    `maze3d.point_terminals` opens a terminal's OWN cell whether the raster
    calls it free or not -- so the wave had a seed, and every one of its
    twenty-four neighbours was guarded.

    THE LIFT IS EXACTLY THE GUARD'S OWN REACH AND NOT ONE CELL MORE.  The disc
    subtracted at an end carries the widest `keepout` of the guard points that
    cover it, so `_guard_masks` stamps it with the identical formula.  That has
    a property worth stating, because it is what keeps this from becoming a
    gate through the lane: a lift centred `e` off the centreline frees the
    NEAR side out to `R + e` and the FAR side only to `R - e`.  A terminal is
    freed to leave on the side it already lives on, and a relay that wants the
    other side must still cross the corridor somewhere the reservation permits
    -- on another layer, which is what per-lane layers are for.

    Only the end's OWN layer is lifted.  A track end is copper on one layer;
    the reservation on every other layer is untouched.
    """
    pts = (guard or {}).get(lkey) or ()
    lift, report = [], []
    for (ex, ey) in ends:
        cover = [k for (x, y, k) in pts
                 if math.hypot(x - ex, y - ey) < k + width_nm / 2.0 + grid_nm]
        if not cover:
            continue
        k = max(cover)
        lift.append((ex, ey, k))
        report.append(dict(at_mm=[round(ex / 1e6, 4), round(ey / 1e6, 4)],
                           lkey=lkey, keepout_mm=round(k / 1e6, 4),
                           reach_mm=round((k + width_nm / 2.0 + grid_nm) / 1e6, 4),
                           guard_points=len(cover)))
    return ({lkey: lift} if lift else {}), report


def pad_owner_nets(board, refs):
    """{net: [pad ref, ...]} for the named pads, read from the board itself.

    A bond stitch is asked for by PAD, because that is the object whose bond is
    single-point.  Which net it belongs to is not the caller's to assert.
    """
    want = list(dict.fromkeys(refs))
    owner = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if not p.GetNumber():
                continue
            owner["%s.%s" % (f.GetReference(), p.GetNumber())] = p.GetNetname()
    out, missing = {}, []
    for r in want:
        n = owner.get(r)
        if n:
            out.setdefault(n, []).append(r)
        else:
            missing.append(r)
    if missing:
        raise SystemExit("no such pad(s): %s" % ", ".join(missing))
    return out


def propose(path, nets, grid, via_cost_mm, stitch_width=0, stitch_via=None,
            join_residual=False, join_max_mm=0.0, neck=False,
            neck_max_mm=0.0, partial=False, attempt_cap=0,
            split_islands=False, guard_spec=None, bridge=False,
            bond_pads=(), bond_max_mm=BOND_MAX_MM, bond_via=None,
            join_islands=False, join_island_max_mm=0.0,
            escape_relief=False, relief_via=None, detour_plan=None,
            body_landing=False, join_orphans=False,
            join_orphan_max_mm=JOIN_ORPHAN_MAX_MM,
            detour_own_layer=False, relief_extra_width=0,
            relief_pads=(), relief_bonds_per_island=1, relief_run_areas=None,
            escape_floor=False, bridge_pads=False,
            bridge_pad_max_mm=BRIDGE_PAD_MAX_MM, trunk_floor=False,
            tap=False, tap_max_mm=0.0, tap_pairs=3):
    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz

    # A SCRATCH BOARD WITHOUT ITS `.kicad_pro` HAS NO NETCLASSES, AND IT SAYS SO
    # QUIETLY.  `net_contract` reads the class off `NETINFO_ITEM`, which KiCad
    # resolves through the PROJECT's netclass patterns -- so a `.kicad_pcb`
    # copied on its own reads back `Default` for EVERY net, and this child would
    # then route `+3V3` at 0.200 mm with a 0.50/0.25 mm barrel and report it
    # without complaint.  `gate` copies `.kicad_pcb`, `.kicad_dru` AND
    # `.kicad_pro` together for exactly this reason; anything driving `--propose`
    # by hand owes the same three files, or its measurement is of a board that
    # does not exist.
    ref = pcbnew.LoadBoard(str(path))
    # THE TRUNK FLOOR TRAVELS WITH THE CONTRACT, NOT WITH THE SEARCH -- D-662,
    # the same reading `--escape-floor` carries.  A detour owes its own old
    # width (see the note beside `detours` below) and a re-laid net owes the
    # width the primary proposal was allowed, so the floor is handed to every
    # contract this child builds or the run would judge two nets by two rules.
    tf = bool(trunk_floor)
    contracts = {n: net_contract(ref, n, tf) for n in nets}
    bond_by_net = pad_owner_nets(ref, bond_pads) if bond_pads else {}
    for n in bond_by_net:
        contracts.setdefault(n, net_contract(ref, n, tf))
    for d in (detour_plan or {}).get("detours", ()):
        contracts.setdefault(d["net"], net_contract(ref, d["net"], tf))
    reserved = reserved_inner_planes(ref)
    del ref

    qb = qr.QBoard(str(path))
    ir.inject_existing_via_obstacles(qb)
    for n, c in contracts.items():
        c["layers"] = permitted_layers(qb.routable, c["layers"], reserved, n)
        c["reserved_inner_planes"] = {k: sorted(v) for k, v in reserved.items()}
    # The pad-escape necking allowance is read from the board's own .kicad_dru,
    # so the router cannot permit a neck the DRC would refuse, nor refuse one
    # the board's rules were written to allow.  None => the router behaves
    # exactly as it did before this flag existed.
    neck_rule = mz.neck_rule(qb, neck_max_mm or mz.NECK_MAX_MM) if neck else None
    # D-609.  The board's own pad-escape necking rule, read WHETHER OR NOT
    # `--neck` was asked for: `--neck` is a ROUTING lever (may this pad launch
    # narrow?) and this is a LICENCE fact (how narrow does the `.kicad_dru`
    # already allow inside the courtyards it names?).  The relief width ladder
    # is clamped to it, so no flag can ask for a width the board never names.
    licensed_neck = mz.neck_rule(qb)

    # BOND STITCHES RUN BEFORE ANY SIGNAL COPPER, and that ordering is the
    # whole point of the lever.  The tube a bond retires is copper the router
    # is otherwise forbidden to cross; laying the bonds first means the routes
    # proposed after them are proposed on a board where the pads they would
    # strand are already held by a track and a barrel of their own.
    # DETOURS RUN BEFORE ANYTHING ELSE, and the ordering is the whole point.
    # The applier has already removed the crossing tracks from this scratch
    # board, so the pocket is open right now and nothing else has been laid in
    # it yet; putting each track back FIRST means every stitch and every join
    # proposed afterwards is proposed on a board where the detoured copper is
    # already in its new place, obstacle and all.  The reserved disc is in the
    # guard spec, so the detour cannot retrace its own old path.
    #
    # A DETOUR OWES ITS OWN OLD WIDTH, not its netclass width.  The track being
    # put back is accepted copper with a width some earlier transaction chose;
    # re-laying it wider would be a silent second change riding on this one, and
    # re-laying it narrower would quietly weaken a rail.
    detours = []
    for d in (detour_plan or {}).get("detours", ()):
        net = d["net"]
        c = contracts[net]
        t0 = time.time()
        # D-646.  A REMOVAL WITH NO REPLACEMENT IS NOT A ROUTING PROBLEM.
        # `--detour-spec` was written for copper that has to be somewhere
        # else; this board also carries copper that does not have to be
        # anywhere -- legacy routed track of a POUR-OWNING net that duplicates
        # a connection the pour already makes.  Asking `route_points` to put
        # such a chain back is asking it to solve a problem the run has just
        # deleted, and on the `+3V3` / `U4` pocket it is unanswerable BY
        # CONSTRUCTION: the route this removal exists to admit is the very
        # thing that closes the corridor the relay would need.  So the chain is
        # removed, the record says so in its own words, and the GATE prices it.
        if d.get("relay") is False:
            # D-653.  A BARREL RIDES THIS BRANCH AND IS PRICED BY A DIFFERENT
            # CLAUSE.  It reaches here for the same reason an inert chain does
            # -- there is nothing for `route_points` to put back -- but the
            # claim it makes is not the chain's.  A chain says "the pour
            # already joins these two points on this layer"; a barrel says
            # "the copper I bonded still reaches this net's plane through a
            # barrel at least as wide".  Carrying `barrel` through is what
            # lets the gate tell the two apart.
            bar = d.get("barrel")
            detours.append(dict(
                net=net, layer=d["layer"], lkey=d["lkey"], relay=False,
                removed_only=True, ok=False,
                reason=("BARREL_REMOVED_NOT_REBONDED_YET" if bar
                        else "REMOVED_NOT_RELAID"),
                why=("declared as a barrel; the gate's rebond_priced clause "
                     "prices the barrel that replaces it" if bar else
                     "declared `relay: false`; the gate's inert_removal_priced "
                     "clause prices the conductor that replaces it"),
                barrel=bar,
                mm=0.0, vias=0, was_mm=d["mm"], width_nm=d["width_nm"],
                max_mm=d.get("max_mm"), own_layer=False,
                a_mm=[round(v / 1e6, 4) for v in d["a_nm"]],
                b_mm=[round(v / 1e6, 4) for v in d["b_nm"]],
                seconds=0.0))
            print("  %-44s detour %s %.3f mm %s"
                  % (net, ("BARREL_REMOVED %.3f/%.3f mm"
                           % (bar["dia_mm"], bar["drill_mm"])) if bar
                     else "REMOVED_NOT_RELAID", d["mm"], d["layer"]),
                  file=sys.stderr, flush=True)
            continue
        g = guard_for(guard_spec, net) if guard_spec else None
        # D-667.  A RELAY'S OWN TWO ENDS ARE NOT NEW COPPER.  A reservation
        # reaches `keepout + width/2 + G`, which is wider than the clearance
        # rule it stands for, so it swallows the terminals of the very copper
        # the lane's route displaced.  Lift it there and nowhere else; the
        # report rides on this detour's record so the gate and a reader can see
        # exactly which terminals were freed and how far.
        gfree, lift_report = terminal_lift(
            g, d["lkey"], (tuple(d["a_nm"]), tuple(d["b_nm"])),
            d["width_nm"], grid)
        # D-609.  A track being PUT BACK may be put back on the layer it was
        # already lawfully on, and on nothing else -- see `detour_layers`.
        layers, own = detour_layers(c["layers"], d["lkey"], detour_own_layer)
        field = mz.Field(qb, net, d["width_nm"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=grid,
                         layers=layers, guard=g, guard_free=gfree)
        r = mz.route_points(qb, field, tuple(d["a_nm"]), tuple(d["b_nm"]),
                            d["lkey"], via_cost_mm=via_cost_mm,
                            max_mm=d.get("max_mm", 0.0))
        r = dict(r)
        r.pop("mark", None)
        r.update(net=net, layer=d["layer"], was_mm=d["mm"],
                 exact_relay=d.get("exact_relay"),
                 # D-658.  A relay whose ends MOVED says so in its own record,
                 # so a reviewer reading `was_mm 0.707 -> mm 1.204` can see the
                 # 0.500 mm of that growth that is the barrel move and not the
                 # detour.
                 move_ends=d.get("move_ends") or [],
                 terminal_lift=lift_report,
                 max_mm=d.get("max_mm"), width_nm=d["width_nm"],
                 lkey=d["lkey"], layers_allowed=list(layers), own_layer=own,
                 a_mm=[round(v / 1e6, 4) for v in d["a_nm"]],
                 b_mm=[round(v / 1e6, 4) for v in d["b_nm"]],
                 seconds=round(time.time() - t0, 1))
        detours.append(r)
        print("  %-44s detour %s %.3f->%.3f mm %s%s"
              % (net, "ok" if r.get("ok") else r.get("reason"), d["mm"],
                 r.get("mm", 0.0), d["layer"], " OWN-LAYER" if own else ""),
              file=sys.stderr, flush=True)

    bonds = []
    for net in sorted(bond_by_net):
        c = contracts[net]
        if not c["known_class"]:
            bonds.append(dict(net=net, ok=False, reason="UNKNOWN_NETCLASS",
                              netclass=c["netclass"], bonds=[], failures=[]))
            continue
        t0 = time.time()
        gb = guard_for(guard_spec, net) if guard_spec else None
        # A BOND BARREL OWES THE FLOORS, NOT THE NETCLASS.  The netclass via is
        # sized for a rail trunk; what a bond needs is the smallest barrel the
        # BOARD licenses, because the pads that cannot be bonded at the
        # netclass via fail with `NO_VIA_SITE` and a site is a function of
        # diameter.  The request is clamped UP to the `.kicad_dru` class drill
        # floor and to the 0.125 mm annular ring, exactly as `--stitch-via` is,
        # so it can never ask for a via KiCad's own `hole_size` /
        # `annular_width` checks would refuse.  It is NOT clamped up to
        # `min_via_diameter`: a barrel under that floor is legal only inside a
        # rule area the `.kicad_dru` names, `bond_pads` has no licence
        # machinery, and the gate's clause 6 would refuse the run -- so asking
        # for one is a screen, not a promotion.
        if bond_via:
            drill = max(bond_via[1],
                        DRU_CLASS.get(c["netclass"], {}).get("drill", 0))
            c = dict(c, via_drill=drill,
                     via_dia=max(bond_via[0], drill + 2 * ANNULAR_MIN))
        field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=grid,
                         layers=c["layers"], guard=gb)
        r = mz.bond_pads(qb, net, field, bond_by_net[net], max_mm=bond_max_mm)
        r["via"] = [c["via_dia"], c["via_drill"]]
        r["seconds"] = round(time.time() - t0, 1)
        r["contract"] = {k: c[k] for k in ("netclass", "width", "clr",
                                           "clr_pad", "via_dia", "via_drill",
                                           "layers")}
        bonds.append(r)
        print("  %-44s bond   %d/%d %.0fs"
              % (net, r.get("bonded", 0), r.get("requested", 0),
                 time.time() - t0), file=sys.stderr, flush=True)

    results = []
    for net in nets:
        c = contracts[net]
        if not c["known_class"]:
            results.append(dict(net=net, ok=False, reason="UNKNOWN_NETCLASS",
                                netclass=c["netclass"]))
            continue
        # A plane STITCH stub is a few tenths of a millimetre of copper from a
        # pad to a barrel directly under it, so it is governed by the .kicad_dru
        # class floor rather than by the netclass DEFAULT width, which is sized
        # for a cross-board rail run.  The override can only ever RAISE the
        # floor: it is clamped to the DRU minimum for the class and the real
        # `track_width` DRC check re-proves every emitted segment regardless.
        #
        # D-604: THE BOARD FLOOR IS PART OF THAT CLAMP AND WAS MISSING.  Several
        # classes -- `GND` among them, and it is the one this lever pays on --
        # carry NO `.kicad_dru` `track_width` rule at all, so the class floor is
        # zero and the clamp above admitted any width the caller asked for,
        # including one under board setup's own `min_track_width`.  `--bond-via`
        # already refuses a sub-floor barrel by name; a sub-floor TRACK is
        # refused here for the same reason and in the same shape.
        if stitch_width:
            c["width"] = max(stitch_width, BOARD_TRACK_MIN,
                             DRU_CLASS.get(c["netclass"], {}).get("width", 0))
        # Same discipline for the barrel.  The netclass via is sized for a rail
        # trunk; a stitch barrel owes only the .kicad_dru floors -- the
        # POWER-class 0.40 mm drill and the 0.125 mm annular ring -- and the
        # request is clamped UP to both, so it can never ask for a via KiCad's
        # own `hole_size` / `annular_width` checks would refuse.
        if stitch_via:
            drill = max(stitch_via[1],
                        DRU_CLASS.get(c["netclass"], {}).get("drill", 0))
            c["via_drill"] = drill
            c["via_dia"] = max(stitch_via[0], drill + 2 * ANNULAR_MIN)
        t0 = time.time()
        g = guard_for(guard_spec, net) if guard_spec else None
        c["guarded_layers"] = {k: len(v) for k, v in (g or {}).items()}
        # BRIDGES RUN FIRST, and before the routing `Field` is built.  A barrel
        # straight down into the same net's copper on another layer is the
        # cheapest move available -- no escape, no track -- so it takes
        # priority over the stitch, and the stitch's lattice is then built with
        # those barrels already on the board rather than blind to them.
        bridged = None
        if bridge and mz.has_plane(qb, net):
            bridged = mz.bridge_islands(
                qb, net, c["width"], c["clr_pad"], c["clr"], BRIDGE_LADDER,
                via_floors(c["netclass"]), G=grid, layers=c["layers"], guard=g)
        # ESCAPE FLOOR -- D-630.  `net_contract` takes `max()` of the netclass
        # width (which carries `.kicad_dru` section 5's `opt`) and `DRU_CLASS`
        # (which carries its `min`), so the router routes at the OPTIMUM and
        # then treats it as the width a LAND must launch.  On this board that
        # made three lands on the two largest open nets unlaunchable from the
        # parts they serve, and it is the same defect `DRU_CLASS`'s `NFC_RF`
        # `width_cap` was written for.  `--escape-floor` hands the escape
        # ladder the class's PUBLISHED minimum as its rule minimum; the trunk
        # is unchanged, and `QBoard.escape` already refuses any launch point
        # where the trunk width is not also legal.  A class the `.kicad_dru`
        # does not price does not move -- the floor is never board setup's
        # `min_track_width` -- so this can never propose copper the DRC would
        # refuse, and no signal class and no return path is touched.
        floor = DRU_CLASS.get(c["netclass"], {}).get("width") if escape_floor \
            else None
        c["escape_floor"] = min(c["width"], floor or c["width"])
        field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=grid,
                         layers=c["layers"], neck=neck_rule, guard=g,
                         escape_floor=floor)
        # A net that owns a filled pour is completed by dropping each island
        # onto that pour, not by a pad-to-pad MST across the signal layers.
        # THE BARREL MUST LAND ON THE BODY, AND ONLY THE CALLER CAN SAY SO.
        # D-608.  `stitch_pad` proves its via is LEGAL; nothing in it asks
        # whether the copper under that via is the plane body, another orphan
        # of the same net, or no copper at all.  Three gate runs on `SW9.2`
        # (D-604) and one on `R129.1` (D-607) were spent finding that out
        # afterwards.  `--body-landing` hands the stitch the mask of cells
        # inside the body's own filled pour, so the site it takes is one the
        # refill will bond.  Off by default: the mask is a CERTIFICATE, not a
        # veto -- `C7.1`'s promoted barrel lay outside every filled `+3V3`
        # island on the board it was proposed on and closed its edge anyway.
        # PAD BRIDGES RUN NEXT, AND THE ORDER IS THE ARGUMENT.  D-631.  A
        # `bridge_islands` barrel is copper with no escape and no track; a PAD
        # BRIDGE is copper with no escape and no via -- one straight track
        # between two lands, both endpoints inside them.  Both are cheaper than
        # anything that has to launch, and both merge islands, so every move
        # below sees fewer of them and a board that already carries their
        # copper.  The width ladder is the netclass width and the `.kicad_dru`
        # class floor and NOTHING NARROWER -- a bridge is ordinary rail copper,
        # never a licensed neck -- and the proof is `maze3d.verify_laid`, which
        # is exact geometry, because the whole reason this primitive exists is
        # that no lattice can express the pairs it serves.  Off by default.
        bridged_pads = None
        if bridge_pads:
            w_floor_pb = max(BOARD_TRACK_MIN,
                             DRU_CLASS.get(c["netclass"], {}).get("width", 0))
            pb_widths = sorted({c["width"], min(c["width"], w_floor_pb)},
                               reverse=True)
            bridged_pads = mz.bridge_net_pads(qb, net, field, pb_widths,
                                              max_mm=bridge_pad_max_mm)
            bridged_pads["widths_offered"] = list(pb_widths)
        land_ok, land_info = None, None
        if body_landing and mz.has_plane(qb, net):
            land_ok, land_info = mz.body_landing(qb, net, field)
        if mz.has_plane(qb, net):
            r = mz.stitch_net(qb, net, width=c["width"],
                              clr_pad=c["clr_pad"],
                              clr_trk=c["clr"], via_dia=c["via_dia"],
                              via_drill=c["via_drill"], G=grid, field=field,
                              split_islands=split_islands, land_ok=land_ok)
            if land_info is not None:
                r["body_landing"] = land_info
            r["mode"] = "stitch-split" if split_islands else "stitch"
            # The stitch is LOCAL by construction -- one escape and one barrel
            # inside an 8 mm window.  An island it reports as unreachable may
            # still be a short ordinary run from copper that IS on the plane, so
            # the residual pass hands exactly those islands to the same
            # whole-board maze the plane-less nets use.  It runs AFTER the
            # stitch, never instead of it: a barrel straight down into the pour
            # is always the cheaper answer and keeps its priority.
            if join_residual:
                j = mz.join_residual_islands(qb, net, field,
                                             via_cost_mm=via_cost_mm,
                                             max_mm=join_max_mm)
                r["residual_join"] = j
                r["mode"] = "stitch+join"
                r["ok"] = bool(r.get("ok")) or bool(j.get("joined"))
            # ISLAND JOINS RUN LAST, AND THE ORDER IS THE ARGUMENT.  D-605.
            # A bridge is one barrel and no track; a stitch is one escape, one
            # short run and one barrel down to the net's own plane; a residual
            # join is a pad-to-pad maze run.  All three are cheaper or more
            # robust than a lateral jumper between two pieces of pour, so the
            # jumper is offered only what they could not close, and it is
            # offered on a board that already carries their copper.
            if join_islands:
                ji = mz.join_islands(qb, net, field, via_cost_mm=via_cost_mm,
                                     max_mm=join_island_max_mm)
                r["island_join"] = ji
                r["mode"] = r["mode"] + "+islands"
                r["ok"] = bool(r.get("ok")) or bool(ji.get("joined"))
            # THE ORPHAN JOIN RUNS AFTER EVERY MOVE THAT AIMS AT THE
            # PLANE, AND THE ORDER IS THE ARGUMENT.  D-608.  A stitch, a
            # bridge, a residual join and an island join all leave the pad ON
            # the pour, which is what a plane-served pad actually wants; an
            # orphan join leaves both pads off it and buys the edge only.  So
            # it is offered exactly what none of them could plant, on a board
            # that already carries their copper.
            if join_orphans:
                jo = mz.join_orphans(qb, net, field,
                                     via_cost_mm=via_cost_mm,
                                     max_mm=join_orphan_max_mm)
                r["orphan_join"] = jo
                r["mode"] = r["mode"] + "+orphans"
                r["ok"] = bool(r.get("ok")) or bool(jo.get("joined"))
            # THE RELIEF RUNS LAST, AND THE ORDER IS AGAIN THE ARGUMENT.
            # D-606.  Every primitive above lays copper the board licenses
            # UNCONDITIONALLY; this one lays a barrel that exists only because
            # a `.kicad_dru` rule names one net inside one pad-sized area.  A
            # licence is the most expensive thing a transaction can spend, so
            # it is offered only the lands nothing unconditional could close,
            # on a board that already carries their copper.
            if escape_relief:
                rv = relief_via or RELIEF_VIA
                # The netclass width FIRST and the floor only if it fails: a
                # relieved bond must never be quietly thinner than an
                # unrelieved one.  `min` keeps the ladder strictly descending
                # where a class floor is already at or above its netclass.
                w_floor = max(BOARD_TRACK_MIN,
                              DRU_CLASS.get(c["netclass"], {}).get("width", 0))
                widths = sorted({c["width"], min(c["width"], w_floor)},
                                reverse=True)
                # D-609.  ONE MORE RUNG, AND THE BOARD -- NOT THE CALLER --
                # SAYS HOW NARROW IT MAY BE.  `U12.4`/`U12.5` are the
                # `TPS63020`'s own `VOUT` pins and the rail has no connection
                # to them at all.  The width ladder measured why: at the P3V3
                # 0.400 mm floor NEITHER pin has a legal escape, at 0.250 mm
                # neither reaches a barrel, and at 0.200 mm BOTH escape, run
                # under 4.2 mm and plant an ORDINARY 0.65/0.40 mm POWER barrel
                # inside the plane BODY.  The wall was never the barrel and
                # never the pocket; it was the RUN.
                #
                # The rung is not a number this driver may choose.  It is
                # clamped UP to `maze3d.neck_rule`'s own minimum -- the width
                # `.kicad_dru`'s "Pad-escape necking - width, fine-pitch power
                # packages" already grants inside the ten courtyards it names,
                # `U12` among them -- and up to board setup's
                # `min_track_width`.  So this flag can ask for copper the board
                # already licenses somewhere, and can never invent a width the
                # board does not name at all.  WHERE that copper may lie is
                # KiCad's own question and gate clause 3 asks it: a segment
                # that leaves the licensed courtyard is judged at the class
                # floor and the whole run is refused.
                if relief_extra_width:
                    floor = max(BOARD_TRACK_MIN, relief_extra_width)
                    if licensed_neck is not None:
                        floor = max(floor, licensed_neck.min_w)
                    if floor < widths[-1]:
                        widths.append(floor)
                widths = tuple(widths)
                # D-610.  A run NARROWER than the class floor is licensed
                # copper or it is no copper: `narrow_below` is that floor and
                # `run_areas` is the declared rectangle each licence is
                # granted over.  Without a declared spec `narrow_below` is 0
                # and every rung behaves exactly as D-609's did -- laid, and
                # judged by real DRC -- so the measurement run that DISCOVERS
                # the rectangle is still expressible.
                rs = mz.relief_stitch(
                    qb, net, widths, c["clr_pad"], c["clr"], rv[0], rv[1],
                    via_floors(c["netclass"]), G=grid, layers=c["layers"],
                    neck=neck_rule, guard=g, land_ok=land_ok,
                    pads=(set(relief_pads) or None),
                    bonds_per_island=max(1, relief_bonds_per_island),
                    narrow_below=(w_floor if relief_run_areas else 0),
                    run_areas=relief_run_areas)
                rs["widths_offered"] = [w for w in widths]
                rs["pads_named"] = sorted(relief_pads or ())
                rs["bonds_per_island"] = max(1, relief_bonds_per_island)
                rs["run_areas_declared"] = sorted(relief_run_areas or ())
                r["escape_relief"] = rs
                r["mode"] = r["mode"] + "+relief"
                r["ok"] = bool(r.get("ok")) or bool(rs.get("stitched"))
        else:
            r = mz.route_net(qb, net, width=c["width"],
                             clr_pad=c["clr_pad"],
                             clr_trk=c["clr"], via_dia=c["via_dia"],
                             via_drill=c["via_drill"], G=grid,
                             via_cost_mm=via_cost_mm, field=field,
                             partial=partial, attempt_cap=attempt_cap,
                             join_max_mm=join_max_mm)
            r["mode"] = "maze+partial" if partial else "maze"
        # THE TAP RUNS AFTER EVERY MOVE THAT AIMS AT A PAD, AND THE ORDER IS
        # THE ARGUMENT.  D-664.  A stitch, a bridge, a residual join, an island
        # join and the whole-board maze all aim an orphan at a PAD or at the
        # net's own pour; a tap aims it at the net's own TRACK.  It is the
        # cheapest thing on this list -- it removes nothing, relays nothing and
        # licenses nothing (TAP2) -- but it is also the only one that leaves a
        # BRANCH on an accepted conductor, so it is offered exactly the lands
        # nothing else could close, on a board that already carries their
        # copper.  It runs for pour-owning and plane-less nets alike: the
        # branch is onto a TRACK either way, and `tap_sites` is what decides
        # whether the net owns one.
        if tap:
            tp = mz.join_taps(qb, net, field, width=c["width"], G=grid,
                              max_mm=tap_max_mm, pairs=tap_pairs,
                              netclass=c["netclass"],
                              forbidden=TAP_STUB_FORBIDDEN)
            r["tap"] = tp
            r["mode"] = r["mode"] + "+tap"
            r["ok"] = bool(r.get("ok")) or bool(tp.get("joined"))
        if bridged is not None:
            r["bridge"] = bridged
            r["mode"] = "bridge+" + r["mode"]
            r["ok"] = bool(r.get("ok")) or bool(bridged.get("bridged"))
        if bridged_pads is not None:
            r["pad_bridge"] = bridged_pads
            r["mode"] = "padbridge+" + r["mode"]
            r["ok"] = bool(r.get("ok")) or bool(bridged_pads.get("bridged"))
        r["seconds"] = round(time.time() - t0, 1)
        print("  %-44s %-6s %s %.0fs" % (
            net, r["mode"], "ok" if r.get("ok") else r.get("reason", "FAIL"),
            time.time() - t0), file=sys.stderr, flush=True)
        # `escape_floor` is in the contract because it is a WIDTH the run was
        # allowed to lay: a report that prints the trunk width and omits the
        # floor a land launched at describes a different run from the one that
        # happened.  It equals the trunk width whenever the lever is off.
        r["contract"] = {k: c[k] for k in
                         ("netclass", "width", "clr", "clr_pad", "via_dia",
                          "via_drill", "layers", "reserved_inner_planes",
                          "guarded_layers")}
        r["contract"]["escape_floor"] = c.get("escape_floor", c["width"])
        # D-662.  The trunk floor is recorded WHETHER OR NOT it moved the
        # width, and a refusal carries the price that refused it, so a net
        # that was offered the floor and did not take it says why.  `None`
        # means the lever was never asked for on this run.
        r["contract"]["trunk_floor"] = c.get("trunk_floor")
        results.append(r)
    qb.save(str(path))
    print(json.dumps(dict(results=results, bonds=bonds,
                          detours=detours), default=str))


# --------------------------------------------------------------------------- #
# THE LATTICE A LAND REQUIRES -- D-622
#
# `screen_land_escape_margin.py` (D-620) already publishes, per land and per
# direction, the COARSEST maze lattice whose 0.75-cell guard band still fits:
#
#     max_lattice_mm = margin / 0.75
#
# Nothing consumed it.  `--grid` defaulted to 0.100 mm for every run this
# project has ever made, and D-622 measured what that cost on ONE net.
# `/04_SPI_B_RADIOS_NFC/NFC_VDD_A`'s `U9.7` has exactly one launchable
# direction -- WEST, margin 0.050 mm, `max_lattice_mm` **0.0667** -- so at the
# default 0.100 mm lattice the only escape that land HAS cannot be expressed.
# The maze does not report that.  It reaches the pad the long way round
# instead, and the long way round was a 17.66 mm route whose 4.4 mm `B.Cu`
# wall severed the `GND` pour: the 12.461 mm2 `C45`-pocket fragment D-619
# refused, and D-619 refused it as a POUR question.  At 0.025 mm the same
# request routes in **8.352 mm** and severs nothing.
#
# So a land's lattice requirement is not a performance knob.  It is part of
# what the router can EXPRESS, exactly as D-620 said of the guard band, and
# `--grid auto` is the lever that reads it off the board instead of guessing.
# `lattice_advice()` runs on every invocation whatever `--grid` says, so a run
# at too coarse a pitch is named in its own report rather than discovered two
# decisions later.
# --------------------------------------------------------------------------- #
GRID_FLOOR_NM = 10000          # below this the wavefront stops being affordable
GRID_CEIL_NM = 100000          # `auto` never proposes a lattice COARSER than
                               # the default, so it can only ever refine


def lattice_advice(board_path, nets, grid_nm):
    """Per requested net: the lattice its tightest LAND can still be launched on.

    The direction reported is the one the maze would actually launch in -- the
    best-margin direction, which is what `screen_land_escape_margin.py` calls
    the land's verdict.  A land whose best margin is <= 0 has NO lattice at any
    pitch (D-620) and is reported as such rather than as a number.
    """
    from screen_land_escape_margin import screen
    doc = screen(board_path, list(nets), set())
    per_net, worst = {}, None
    for row in doc["pads"]:
        best = max(row["directions"].values(), key=lambda d: d["margin_mm"])
        need = best["max_lattice_mm"]
        e = per_net.setdefault(row["net"], dict(binding_pad=None,
                                                required_lattice_mm=None,
                                                unlaunchable_lands=[],
                                                verdict="CLEAR", lands=0))
        e["lands"] += 1
        if row["verdict"] != "CLEAR":
            # A LAND WITH NO LATTICE AT ANY PITCH DOES NOT GET TO BORROW A
            # NUMBER FROM ONE THAT HAS ONE.  D-623's ladder screen caught the
            # old shape lying by adjacency: `/01_POWER_TREE/ACC_5V_LX` reported
            # `binding_pad L4.2` -- the UNLAUNCHABLE land -- beside
            # `required_lattice_mm 2.8933`, which was read off a DIFFERENT and
            # perfectly clear land, and `too_coarse false`.  Three coherent
            # fields, one incoherent reading, and the reading is REASSURANCE
            # next to a verdict that means NEVER.  `binding_pad` is now set
            # ONLY where a requirement was, so the pair always describes one
            # land; the lands that have no pitch are NAMED instead.
            e["verdict"] = row["verdict"]
            e["unlaunchable_lands"].append(row["pad"])
            continue
        if need is not None and (e["required_lattice_mm"] is None
                                 or need < e["required_lattice_mm"]):
            e["required_lattice_mm"] = need
            e["binding_pad"] = row["pad"]
    for net, e in per_net.items():
        need = e["required_lattice_mm"]
        e["grid_mm"] = round(grid_nm / 1e6, 6)
        e["too_coarse"] = bool(need is not None and grid_nm > need * 1e6)
        # TOO_COARSE AND NO_LATTICE_AT_ANY_PITCH ARE DIFFERENT CLAIMS, and the
        # second is the stronger one.  `too_coarse` says "refine and ask
        # again"; this says "there is nothing to refine to" -- the answer is a
        # placement change, a land licence or `route_local_two_pad`, and
        # climbing a ladder against it is provably wasted search.  D-623 spent
        # five rungs on `ACC_5V_LX` learning that by hand.
        e["no_lattice_at_any_pitch"] = bool(e["unlaunchable_lands"])
        if e["too_coarse"] and (worst is None or need < worst):
            worst = need
    return dict(schema=1, grid_nm=grid_nm, nets=per_net,
                any_too_coarse=any(e["too_coarse"] for e in per_net.values()),
                any_unlaunchable=any(e["no_lattice_at_any_pitch"]
                                     for e in per_net.values()),
                tightest_required_mm=worst)


def resolve_grid(board_path, nets, spec):
    """`--grid auto` -> the finest lattice every requested land can launch on.

    Clamped to [GRID_FLOOR_NM, GRID_CEIL_NM] and floored to a whole nanometre;
    a net with no positive-margin land contributes nothing, because no lattice
    serves it and the answer there is `route_local_two_pad`, not a finer grid.
    """
    if str(spec).strip().lower() != "auto":
        return int(spec), None
    probe = lattice_advice(board_path, nets, GRID_CEIL_NM)
    need = [e["required_lattice_mm"] for e in probe["nets"].values()
            if e["required_lattice_mm"] is not None]
    g = GRID_CEIL_NM if not need else max(
        GRID_FLOOR_NM, min(GRID_CEIL_NM, int(min(need) * 1e6)))
    # re-read the advice AT THE PITCH ACTUALLY CHOSEN, so the block in the
    # report describes the run that happened and not the probe that sized it
    adv = lattice_advice(board_path, nets, g)
    adv["auto"] = True
    adv["auto_grid_nm"] = g
    # `auto` IS NECESSARY AND IT IS NOT SUFFICIENT, AND SAYING SO IS THE POINT.
    # D-622 swept the same request at four pitches -- 0.100 mm 17.660 mm,
    # 0.0667 mm 10.723 mm, 0.050 mm 10.384 mm, 0.025 mm 8.352 mm -- and only
    # the finest one stopped severing the `GND` pour.  The coarsest ADMISSIBLE
    # lattice is the cheapest search that can express every land's own escape;
    # it is not a claim that no finer pitch would route better, and the thing
    # that decides is `checks/pour_partition_contract.py`, not this number.
    adv["sufficiency"] = ("NECESSARY_NOT_SUFFICIENT: the coarsest lattice every "
                          "requested land admits.  A finer pitch may still "
                          "route shorter -- judge the result, not the pitch")
    return g, adv


# --------------------------------------------------------------------------- #
# THE LADDER -- D-623
#
# D-622 ended by naming this and not taking it:
#
#     A `--grid` LADDER bounded by a cell-count budget, rather than the single
#     coarsest-admissible pitch `auto` computes today, is the framework task
#     this decision names and does not take.
#
# `auto` answers the question "what is the coarsest lattice this net's own
# lands can be LAUNCHED on", and that answer is NECESSARY AND NOT SUFFICIENT in
# its own words: on `NFC_VDD_A` the coarsest admissible pitch still severed the
# `GND` pour, and only 0.025 mm -- four times finer than `auto` proposed -- both
# closed the edge and left the partition alone.  A single pitch cannot express
# that.  A LADDER can: try the coarsest admissible lattice first, because it is
# the cheapest search that can express every land's own escape, and refine only
# while the run is still refused.
#
# THE BUDGET IS THE HONEST BOUND, AND IT IS COUNTED IN CELLS.  A `maze3d.Field`
# rasterises the WHOLE board -- `(ex1 - ex0 + 2*margin) / G` by the same in `y`,
# once per routable layer -- so halving the pitch quadruples the raster and
# every mask built over it.  On this board:
#
#     0.1000 mm    761 x 1521 x 4 =    4.6 M cells
#     0.0500 mm   1521 x 3041 x 4 =   18.5 M
#     0.0250 mm   3041 x 6081 x 4 =   74.0 M
#     0.0125 mm   6081 x 12161 x 4 =  295.8 M
#
# so a ladder with no bound is a ladder that eventually wedges the machine.
# `--grid-cells` is that bound, stated in the unit that actually grows, and the
# rungs it refuses are REPORTED rather than silently absent: a run that stopped
# because it ran out of budget must not read like a run that ran out of ideas.
#
# AND CELLS ARE NOT WHAT THE BUDGET WAS PROTECTING -- D-626.  D-624 ran eight
# nets down this ladder and EVERY one of them ended on the 0.020 mm rung marked
# `over_budget`.  Run directly, that rung costs, on the SAME board and the SAME
# 115.6 M cells:
#
#     /I2S_LRCLK           NO_PATH     28.7 s
#     /SPI_B_SCK           NO_PATH     21.4 s
#     /SX1262_DIO1         NO_PATH   ~2400 s      (predicted; see below)
#
# A single cell count therefore refuses a twenty-second run and a forty-minute
# run with the SAME sentence.  What actually grows is not the raster, which is
# a property of the BOARD, but the REACHABLE SET the search has to exhaust,
# which is a property of the NET: an escape-bounded refusal never leaves its
# pocket and is FLAT in cells (D-624 measured `/I2S_LRCLK` at 19.4 s on 4.6 M
# cells and 26.5 s on 74.0 M -- a 16x raster for 1.4x the time), while a
# corridor-bounded refusal sweeps an open region and grows FASTER than the
# raster does (`/SX1262_DIO1`: 38.7 s -> 1538.9 s over the same range).
#
# SO THE LADDER PREDICTS, FROM THE NET'S OWN RUNGS.  Each rung that RUNS is a
# (cells, seconds) observation; the last two give a growth exponent
# `k = log(s2/s1) / log(c2/c1)`, and the next rung's cost is `s2 *
# (c/c2)**k`.  `--grid-seconds` bounds that PREDICTION, `--grid-cells` stays as
# the MEMORY ceiling it always really was, and every rung -- run or refused --
# carries `predicted_seconds` beside its measured `seconds`, because a
# predictor nobody scores is a guess.  `k` is clamped to [0.5, 3.0] so one
# noisy pair cannot invent a refusal, and with fewer than two observations the
# ladder does not predict at all: it runs.
# --------------------------------------------------------------------------- #
# AND A CEILING IN CELLS MEANS NOTHING WITHOUT BYTES PER CELL.  The old 80 M
# was never justified against memory either -- it was a TIME bound wearing a
# memory bound's units.  So the new one is MEASURED: three 0.020 mm workers
# (115,565,604 cells) peaked at `VmHWM` 3.00 / 3.01 / 3.04 GB, which is
# 27.9 - 28.2 bytes per cell, and 300 M cells is therefore ~7.9 GiB --
# the unit `rung_gb` reports, and the unit `MemAvailable` is read in
# (`evidence/d626-cell-bytes-measurement.json`).  Raise it only against a
# box that has the RAM: this is the one budget where being wrong is an OOM
# kill rather than a slow run.
#
# AND A CONSTANT CEILING DOES NOT KNOW WHAT ELSE IS RUNNING.  7.9 GiB is safe
# alone and fatal three-up, and the screen this ladder was built for runs
# several nets at once: the number that kills is GIGABYTES AGAINST THIS BOX,
# not cells against a constant.  So the rung is priced in bytes from the
# measured constant and weighed against `MemAvailable` read at ladder start --
# refused with BOTH numbers in the report, never silently.  Deriving a budget
# from the machine makes the ladder's floor machine-dependent, which is a real
# cost, so the derived figure is RECORDED in the report and `--grid-gb` pins it
# explicitly for a run that has to be reproducible.
CELL_BYTES_MEASURED = 28.2          # peak VmHWM / cells, worst of three runs
LADDER_CELL_BUDGET = 300_000_000    # MEMORY ceiling: ~0.0125 mm on this board,
                                    # ~7.9 GiB at the measured bytes/cell
LADDER_MEM_FRACTION = 0.60          # of MemAvailable, when --grid-gb is unset
LADDER_SECONDS_BUDGET = 1800        # per rung, PREDICTED from the net's own
                                    # measured rungs -- see the block above
LADDER_K_CLAMP = (0.5, 3.0)         # growth exponents a two-point fit may claim
FIELD_MARGIN_MM = 2.0               # maze3d.Field's own default


def mem_available_gb():
    """`MemAvailable` in GB -- what the kernel says is free for a new worker.

    Returns None off Linux or if /proc is unreadable, and the caller then does
    not bound by memory at all: a budget that cannot be measured must not be
    invented.
    """
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return round(int(line.split()[1]) / 1048576.0, 2)
    except (OSError, ValueError, IndexError):
        pass
    return None


def rung_gb(cells):
    """One `maze3d.Field` of this many cells, in GiB, at the measured rate.

    GiB rather than GB throughout, because that is the unit `MemAvailable` is
    reported in and the whole point of the number is to be weighed against it.
    """
    return round(cells * CELL_BYTES_MEASURED / (1024 ** 3), 2)


def predict_seconds(observed, cells):
    """Predicted wall-clock for a rung of `cells`, from THIS net's own rungs.

    `observed` is the (cells, seconds) of every rung already run, in order.
    Returns None with fewer than two -- a ladder that has not measured twice
    has nothing to extrapolate from and must RUN rather than guess.
    """
    usable = [(c, t) for c, t in observed if c > 0 and t and t > 0]
    if len(usable) < 2:
        return None
    (c1, t1), (c2, t2) = usable[-2], usable[-1]
    if c2 == c1:
        return round(t2, 1)
    k = math.log(t2 / t1) / math.log(c2 / c1)
    k = min(max(k, LADDER_K_CLAMP[0]), LADDER_K_CLAMP[1])
    return round(t2 * (cells / c2) ** k, 1)

# THE RUNGS ARE THE PITCHES THIS PROJECT HAS ACTUALLY MEASURED, not a halving.
# D-622's sweep was 0.100 / 0.0667 / 0.050 / 0.025 mm and the one that stopped
# severing the pour was the LAST; a bare halving from the coarsest admissible
# pitch (0.0667 -> 0.0334 -> 0.0167) would step straight over it.  0.0667 mm is
# 2/3 of the default and is where a 0.050 mm land margin lands; 0.0333 mm is
# where a 0.025 mm margin lands.  Anything finer than 0.010 mm is below
# `GRID_FLOOR_NM` and is not a rung at any budget.
LADDER_PITCHES = (100000, 66700, 50000, 33300, 25000, 20000, 12500, 10000)


def lattice_cells(board_path, grid_nm):
    """The raster one `maze3d.Field` costs at this pitch, by ITS own formula."""
    import maze3d as mz
    qb = mz.qr.QBoard(str(board_path))
    m = int(FIELD_MARGIN_MM * mz.qr.MM)
    ox, oy = qb.ex0 - m, qb.ey0 - m
    nx = int((qb.ex1 + m - ox) // grid_nm) + 1
    ny = int((qb.ey1 + m - oy) // grid_nm) + 1
    layers = len(qb.routable)
    return dict(grid_nm=int(grid_nm), grid_mm=round(grid_nm / 1e6, 6),
                nx=nx, ny=ny, layers=layers, cells=nx * ny * layers)


def grid_ladder(board_path, nets, coarsest_nm, budget, gb_budget=None):
    """Descending pitches worth trying, coarsest first, bounded by `budget`.

    Rung 0 is the coarsest ADMISSIBLE lattice -- `resolve_grid`'s answer, the
    cheapest search that can express every requested land's own escape.  After
    it come the `LADDER_PITCHES` strictly finer than it.  The first rung whose
    raster exceeds the budget ENDS the ladder and is kept in the report marked
    `over_budget`: the ladder's floor must be a number a reader can see, not a
    run that quietly did not happen.
    """
    pitches = [int(coarsest_nm)] + [p for p in LADDER_PITCHES
                                    if GRID_FLOOR_NM <= p < int(coarsest_nm)]
    rungs = []
    for g in pitches:
        row = lattice_cells(board_path, g)
        # THE CELL CEILING IS A MEMORY BOUND (D-626).  Time is bounded in the
        # driver, from the net's own measured rungs, because cells do not
        # predict it: see the doctrine block above `LADDER_CELL_BUDGET`.
        row["predicted_gb"] = rung_gb(row["cells"])
        row["over_cell_ceiling"] = row["cells"] > budget
        row["over_memory_budget"] = (gb_budget is not None
                                     and row["predicted_gb"] > gb_budget)
        row["over_budget"] = (row["over_cell_ceiling"]
                              or row["over_memory_budget"])
        rungs.append(row)
        if row["over_budget"]:
            break                       # every finer rung is over it too
    return rungs


# --------------------------------------------------------------------------- #
# authority: gate a scratch candidate
# --------------------------------------------------------------------------- #
def ledger(board, out):
    subprocess.run([sys.executable, str(LEDGER), "--board", str(board),
                    str(out)], check=True, capture_output=True, text=True)
    return json.loads(Path(out).read_text())


def zones(path):
    """A comparable signature for every non-rule-area zone on a board."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        outline = z.Outline().Outline(0)
        out.append((
            z.GetNetname(),
            tuple(board.GetLayerName(l) for l in z.GetLayerSet().Seq()),
            z.GetZoneName(),
            z.GetMinThickness(),
            z.GetLocalClearance(),
            int(z.GetIslandRemovalMode()),
            tuple((outline.CPoint(i).x, outline.CPoint(i).y)
                  for i in range(outline.PointCount())),
        ))
    return sorted(out)


def copper(path):
    import pcbnew
    import incremental_router as ir
    return ir.copper_sigs(pcbnew.LoadBoard(str(path)))


def fill_only(scratch, out):
    """Ask the real KiCad engine to FILL the zones and save the board."""
    return subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "-o", str(out), str(scratch),
    ], text=True, capture_output=True).returncode


def full_drc(scratch, out):
    """The authoritative DRC step: refill the zones, save, report everything.

    Extracted so the gate can run it AGAIN after a plane repair.  Refilling is
    the whole point: the pours the proposal perturbed are re-poured by the real
    KiCad engine, so what the ledger measures afterwards is the copper a
    fabricator would actually get, not the copper the router imagined.
    """
    return subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(out), str(scratch),
    ], text=True, capture_output=True)


def plane_nets(path):
    """Nets that own at least one filled, non-rule-area pour on this board."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    return sorted({z.GetNetname() for z in board.Zones()
                   if not z.GetIsRuleArea() and z.IsFilled()
                   and z.GetNetname()})


# --------------------------------------------------------------------------- #
# A POUR THAT A TRACK SPLIT IS NOT A REGRESSION.  IT IS AN UNFINISHED STITCH.
# --------------------------------------------------------------------------- #
# Gate clause 4 refuses any run in which ANY net's open-edge count grows, and it
# is right to: copper that disconnects something is not progress.  But on THIS
# board that clause had started refusing runs for a reason that is not a
# disconnection at all.
#
# After D-582 and D-583 the two outer layers carry pours -- `+3V3` on `F.Cu`,
# `GND` on `B.Cu` -- and those pours bond dozens of pads with no track and no
# via.  A foreign signal track laid across such a layer is a SLOT through the
# pour: KiCad re-pours around it, the pour splits into two islands, and every
# pad that was bonded across the cut goes open.  So a `--partial` run on
# `/I2C_SCL_INT` closed FIVE real edges, lost one to `+3V3` and one to `GND`,
# came out four edges AHEAD on the whole board -- and was refused.
#
# Refusing it is the wrong answer twice over.  It throws away five routed
# connections to avoid two that a via can restore, and it makes the outer pours
# behave like reserved planes, which D-581's rule text explicitly declined to do
# because it would leave this board one signal layer.
#
# The right answer is the one the board has been using since D-579: a pad that
# sits on its own pour island does not need a better search, it needs a BARREL
# down to the same net's copper on another layer.  `maze3d.stitch_net` is
# exactly that primitive, and after the refill the split is visible to it as an
# ordinary orphaned island -- indistinguishable from the two hundred a fresh
# pour leaves.
#
# So `--repair-planes` closes the loop inside ONE gate transaction:
#
#     propose signal copper -> real refill -> measure -> if a POUR-OWNING net
#     regressed, stitch exactly those nets on the refilled board -> real refill
#     again -> measure again, and judge the run on THAT.
#
# Three things keep this a repair and not a loophole.
#
#   * ONLY POUR-OWNING NETS ARE REPAIRED, and only ones that actually
#     regressed.  A plane-less net that a run disconnects is still a hard
#     refusal; there is no via that fixes it and no pretending otherwise.
#   * THE REPAIR IS ORDINARY GATED COPPER.  It goes through the same
#     `propose` child, the same DRU contract, the same analytic proofs, and it
#     is re-proved by a SECOND full `--severity-all --schematic-parity` DRC on
#     the refilled board.  Nothing is measured on a board that was not filled.
#   * THE VERDICT IS UNCHANGED AND UNWEAKENED.  Clause 4 still demands that no
#     net regress and that the whole board improve -- it is simply asked AFTER
#     the repair rather than in the middle of it.  A split the stitch cannot
#     close is still a regression and the run is still refused.
#
# `--repair-planes` is OFF by default, so every existing harness and every
# accepted result reproduces byte-identically without it.


def gate(nets, grid, via_cost_mm, workdir, promote=False, candidate=None,
         plane=None, plane_outline=None,
         zone_clearance=0.25, stitch_width=0, stitch_via=None,
         join_residual=False, join_max_mm=0.0, neck=False, neck_max_mm=0.0,
         partial=False, attempt_cap=0, repair_planes=False,
         split_islands=False, repair_join_max_mm=REPAIR_JOIN_MAX_MM,
         evict=(), evict_margin_mm=EVICT_MARGIN_MM, evict_whole=False,
         evict_window=None,
         guard=None,
         bridge=False, bond_pads=(), bond_max_mm=BOND_MAX_MM,
         bond_via=None, join_islands=False, join_island_max_mm=0.0,
         escape_relief=False, relief_via=None, detour_spec=None,
         body_landing=False, join_orphans=False,
         join_orphan_max_mm=JOIN_ORPHAN_MAX_MM,
         detour_own_layer=False, relief_extra_width=0,
         relief_pads=(), relief_bonds_per_island=1, relief_run_area=None,
         promote_soft=False, escape_floor=False, bridge_pads=False,
         bridge_pad_max_mm=BRIDGE_PAD_MAX_MM, trunk_floor=False,
         tap=False, tap_max_mm=0.0, tap_pairs=3):
    before = sha256_file(BOARD)
    # THE AUTHORITY IS WATCHED EVEN WHEN IT IS NOT THE BASE (D-668).  When
    # `--board` names a candidate, `before` is that candidate's hash and says
    # nothing about the file this repository ships; both are measured, and the
    # `authority_unchanged` clause is the AND of the two.  On an authority run
    # the two hashes are the same number and every field below is unchanged.
    authority_before = sha256_file(AUTHORITY)
    base_is_authority = (Path(BOARD).resolve() == Path(AUTHORITY).resolve())
    if promote and not base_is_authority:
        # Defence in depth: `main` refuses this at the CLI, and so does the one
        # function that can write the authority, because a screen that grows a
        # `--promote` pass-through must not be able to promote a candidate's
        # copper onto a board it never measured.
        raise SystemExit(
            "refuse promotion: --board %s is not the authority %s; a run whose "
            "base is a candidate may not write the shipped board"
            % (BOARD, AUTHORITY))
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    scratch = work / BOARD.name
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(
            BOARD.with_suffix(suffix).read_bytes())

    base_ledger = ledger(BOARD, work / "ledger-before.json")

    # `--evict`: rip up the named nets' routed copper inside the requested
    # nets' own corridor windows, on the layers those nets may actually route
    # on -- see the doctrine above.  It runs FIRST, on the scratch copy, so the
    # proposal that follows sees the opened corridor and every later clause
    # measures the whole transaction rather than half of it.
    # `--detour-spec`: move the named crossing tracks OUT of the pockets this
    # run is trying to open, before anything is proposed.  It runs before the
    # eviction for the same reason the eviction runs before the proposal --
    # every later clause must measure the whole transaction rather than half of
    # it -- and in its own child, because it mutates the board.
    detour = None
    detour_guard_file = None
    detour_rung = None
    if detour_spec:
        plan = load_detours(detour_spec)
        # D-639: THE RUNG TRAVELS WITH THE PLAN.  A rip-up-and-relay plan is a
        # measurement, and a measurement is taken at a WIDTH.  D-638 emitted
        # the geometry and not the width, this run was invoked without
        # `--stitch-width`, `net_contract` handed the stitch the netclass
        # (0.600 mm track, 0.800 mm barrel) where the screen had proved the
        # `.kicad_dru` floor (0.400 / 0.65:0.40), and the transaction reported
        # `NO_BODY_VIA_SITE: no legal 0.80 mm barrel` and `stitched: 0` --
        # every other clause of that gate run measured half a transaction.
        # So the plan states its rung and this adopts it when, and only when,
        # the caller named none.  An explicit CLI rung always wins and the
        # disagreement is RECORDED rather than silently resolved; the adopted
        # figures still go through the same clamp UP to BOARD_TRACK_MIN and the
        # `.kicad_dru` class floors, so a plan can license nothing.
        rg = plan.get("rung") or {}
        detour_rung = dict(
            plan_rung=rg.get("name"), plan_argv=rg.get("argv"),
            plan_why=rg.get("why"),
            cli_stitch_width=stitch_width or None,
            cli_stitch_via=list(stitch_via) if stitch_via else None,
            adopted=False, conflict=False)
        if rg.get("stitch_width_nm") and not stitch_width and not stitch_via:
            stitch_width = int(rg["stitch_width_nm"])
            stitch_via = (int(rg["stitch_via_dia_nm"]),
                          int(rg["stitch_via_drill_nm"]))
            detour_rung.update(adopted=True, stitch_width=stitch_width,
                               stitch_via=list(stitch_via))
        elif rg.get("stitch_width_nm"):
            detour_rung["conflict"] = (
                int(rg["stitch_width_nm"]) != int(stitch_width or 0)
                or (int(rg["stitch_via_dia_nm"]),
                    int(rg["stitch_via_drill_nm"])) != tuple(stitch_via or ()))
        report = work / "detour.json"
        subprocess.run(
            [sys.executable, __file__, "--detour-apply", str(scratch),
             "--detour-spec", str(detour_spec),
             "--detour-report", str(report)],
            check=True, text=True, capture_output=True)
        detour = json.loads(report.read_text())
        # THE RESERVED DISC AND THE POUR-BOND GUARD TRAVEL IN ONE FILE, because
        # `--guard` takes one path and a run that carried only the newer of the
        # two would silently retire the older.  `reserve_corridor.py --merge`
        # is the same move for a corridor; this is it for a pocket.
        merged = dict(load_guard(guard))
        merged.setdefault("guards", [])
        merged["guards"] = list(merged["guards"]) + \
            detour_guard(plan)["guards"]
        detour_guard_file = work / "guard-with-detour.json"
        detour_guard_file.write_text(
            json.dumps(merged, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")

    eviction = None
    if evict:
        # The child reports through a FILE, not through stdout.  Removing
        # tracks from a `BOARD` leaves SWIG objects it has no destructor for,
        # and it announces every one of them on stdout at interpreter shutdown
        # -- after the report -- so a stdout contract here would be hostage to
        # how many objects a run happened to evict.
        report = work / "eviction.json"
        subprocess.run(
            [sys.executable, __file__, "--evict-apply", str(scratch),
             "--evict-report", str(report),
             "--evict-margin-mm", str(evict_margin_mm)]
            + (["--evict-window", evict_window] if evict_window else [])
            + (["--evict-whole"] if evict_whole else [])
            + [x for n in evict for x in ("--evict", n)]
            + list(nets), check=True, text=True, capture_output=True)
        eviction = json.loads(report.read_text())

    # `--plane`: give a plane-less power net a pour, then let the ordinary
    # stitch primitive plant its islands on it.  The pour is added UNFILLED and
    # filled by the real KiCad engine; its first fill must keep every island
    # (a net that owns no copper yet has no connection for `remove` to spare),
    # and the mode is flipped back to `remove` after the stitch so the promoted
    # board carries no island that the stitch did not actually connect.
    #
    # A BOUNDED POUR IS THE SAME INSTRUMENT AIMED SMALLER.  `--plane-outline`
    # restricts the pour to a region instead of the board.  It is not a
    # weakening of `--plane`: a board-wide pour is the ONLY correct shape for a
    # net that owns a layer, and the wrong shape for every net that does not,
    # because at equal zone priority two different-net pours simply retreat from
    # each other and a board-wide fourth pour would fight `+3V3` and `GND` over
    # every square millimetre of `F` and `B`.  `BQ25185_SYS` is the case: a rail
    # with thirteen lands in three clusters, eight of them inside one 12 x 36 mm
    # column of the east power block.  Local copper there is ordinary
    # power-supply practice and costs `GND` -- which also owns the whole of
    # `In1` and `In4` -- nothing it needs.
    #
    # More than one region is the ORDINARY case, not an extension.  A rail's
    # lands cluster where its parts are, and `BQ25185_SYS` has two such
    # clusters -- the east power block around `U11`/`U12` and the boost pocket
    # at `L4`/`U21`, 34 mm apart with the whole 5 V converter in between.  One
    # pour per cluster is the same instrument twice; a single polygon spanning
    # both would be a plane wearing a costume, and would take copper from `GND`
    # across a corridor no `SYS` land is anywhere near.
    plane_zone = None
    if plane:
        if len(nets) != 1:
            raise SystemExit("--plane routes exactly one net")
        specs = list(plane_outline or [None])
        regions = []
        for idx, spec in enumerate(specs):
            outline = parse_outline(spec)
            kind = "PLANE" if tuple(outline) == tuple(OUTLINE) else "POUR"
            name = "%s %s %s" % (plane.split(".")[0], nets[0], kind)
            if len(specs) > 1:
                name += " %d" % (idx + 1)
            insert_zone(scratch, zone_sexpr(
                nets[0], plane, name, clearance=zone_clearance, islands=1,
                outline=outline,
                zuuid=str(uuid.uuid5(uuid.NAMESPACE_URL,
                                     "aqroot-demo/%s/%s/%d"
                                     % (nets[0], plane, idx)))))
            regions.append(dict(name=name, kind=kind,
                                outline=[list(pt) for pt in outline]))
        plane_zone = dict(net=nets[0], layer=plane, clearance=zone_clearance,
                          name=regions[0]["name"], kind=regions[0]["kind"],
                          outline=regions[0]["outline"], regions=regions)
        plane_zone["first_fill_exit"] = fill_only(scratch, work / "fill.json")

    def child(target_nets, use_search_levers=True):
        """Run the proposer on the scratch board for these nets."""
        cmd = [sys.executable, __file__, "--propose", str(scratch),
               "--grid", str(grid), "--via-cost", str(via_cost_mm)]
        # The guard binds the REPAIR too.  A repair that re-bonded one pad by
        # slotting another pad's only bond would be trading one orphan for the
        # next, and clause 4 would refuse the run either way.
        if detour_guard_file is not None:
            cmd += ["--guard", str(detour_guard_file)]
        elif guard:
            cmd += ["--guard", str(guard)]
        # THE DETOUR IS THE PRIMARY PROPOSAL'S BUSINESS, NOT THE REPAIR'S.  A
        # repair re-bonds copper THIS run severed inside an 8 mm window; laying
        # a track back between its own two ends is the transaction itself, and
        # doing it twice would put the same copper down twice.
        if detour is not None and use_search_levers:
            cmd += ["--detour-plan", str(work / "detour.json")]
            if detour_own_layer:
                cmd += ["--detour-own-layer"]
        if stitch_width:
            cmd += ["--stitch-width", str(stitch_width)]
        if stitch_via:
            cmd += ["--stitch-via", "%d:%d" % stitch_via]
        if neck:
            cmd += ["--neck", "--neck-max-mm", str(neck_max_mm)]
        # THE ESCAPE FLOOR IS NOT A SEARCH LEVER -- it is part of the WIDTH
        # CONTRACT the run is judged under, so unlike `--bridge` it is handed
        # to the repair pass too.  A repair that re-lays a net this run cut
        # must launch its lands at the same widths the primary proposal was
        # allowed to.
        if escape_floor:
            cmd += ["--escape-floor"]
        # THE TRUNK FLOOR IS A WIDTH CONTRACT TOO -- D-662, and it is handed to
        # the repair pass for the same reason the escape floor is: a net this
        # run cut and re-lays must be re-laid at the width the primary proposal
        # was allowed, or the run judges two pieces of one net by two rules.
        if trunk_floor:
            cmd += ["--trunk-floor"]
        # The bridge is the primary proposal's lever, not the repair's.  A
        # repair re-bonds copper THIS run severed and does it with the stitch;
        # letting it also drop fine barrels into pours it never touched would
        # be a second transaction wearing a repair's name.
        if bridge and use_search_levers:
            cmd += ["--bridge"]
        # THE ISLAND JOIN IS THE PRIMARY PROPOSAL'S LEVER, NOT THE REPAIR'S --
        # same reading as `--bridge` directly above.  A repair re-bonds copper
        # THIS run severed, inside an 8 mm window, with the stitch; a lateral
        # jumper across a pour cut somewhere else on the board is a second
        # transaction wearing a repair's name.
        if join_islands and use_search_levers:
            cmd += ["--join-islands"]
            if join_island_max_mm:
                cmd += ["--join-island-max-mm", str(join_island_max_mm)]
        # THE RELIEF IS THE PRIMARY PROPOSAL'S LEVER, NOT THE REPAIR'S -- and
        # here the reading is stronger than for `--bridge`.  A repair that
        # could spend a DRU licence would be authoring board rules while
        # wearing a repair's name.
        # THE BODY LANDING IS THE PRIMARY PROPOSAL'S LEVER, NOT THE
        # REPAIR'S -- same reading as `--bridge`.  A plane repair re-bonds
        # copper THIS run severed and is measured against the run's own
        # before/after; narrowing where its barrel may land could leave a
        # severed pad with no stitch at all rather than with a redundant one.
        if body_landing and use_search_levers:
            cmd += ["--body-landing"]
        # THE PAD BRIDGE IS THE PRIMARY PROPOSAL'S LEVER, NOT THE REPAIR'S --
        # same reading as `--bridge`.  It merges two islands that were already
        # apart before the run, which is a second transaction wearing a
        # repair's name.  D-631.
        if bridge_pads and use_search_levers:
            cmd += ["--bridge-pads"]
            if bridge_pad_max_mm != BRIDGE_PAD_MAX_MM:
                cmd += ["--bridge-pad-max-mm", str(bridge_pad_max_mm)]
        # THE ORPHAN JOIN IS THE PRIMARY PROPOSAL'S LEVER, NOT THE REPAIR'S --
        # same reading as `--bridge`.  A repair re-bonds copper THIS run
        # severed; tying two islands that were already apart before the run is
        # a second transaction wearing a repair's name.
        if join_orphans and use_search_levers:
            cmd += ["--join-orphans"]
            if join_orphan_max_mm != JOIN_ORPHAN_MAX_MM:
                cmd += ["--join-orphan-max-mm", str(join_orphan_max_mm)]
        # THE TAP IS THE PRIMARY PROPOSAL'S LEVER, NOT THE REPAIR'S -- D-664,
        # same reading as `--join-orphans` directly above.  A repair re-bonds
        # copper THIS run severed inside an 8 mm window; branching an orphan
        # land that was already apart before the run onto its own net's bus is
        # a second transaction wearing a repair's name.
        if tap and use_search_levers:
            cmd += ["--tap"]
            if tap_max_mm:
                cmd += ["--tap-max-mm", str(tap_max_mm)]
            if tap_pairs != 3:
                cmd += ["--tap-pairs", str(tap_pairs)]
        if escape_relief and use_search_levers:
            cmd += ["--escape-relief"]
            if relief_via:
                cmd += ["--relief-via", "%d:%d" % relief_via]
            if relief_extra_width:
                cmd += ["--relief-extra-width", str(relief_extra_width)]
            if relief_bonds_per_island > 1:
                cmd += ["--relief-bonds-per-island",
                        str(relief_bonds_per_island)]
            if relief_run_area:
                cmd += ["--relief-run-area", str(Path(relief_run_area).resolve())]
            cmd += [x for r in relief_pads for x in ("--relief-pad", r)]
        # THE BOND IS THE PRIMARY PROPOSAL'S LEVER, NOT THE REPAIR'S -- same
        # reading as `--bridge` directly above.
        if bond_pads and use_search_levers:
            cmd += ["--bond-max-mm", str(bond_max_mm)]
            if bond_via:
                cmd += ["--bond-via", "%d:%d" % bond_via]
            cmd += [x for r in bond_pads for x in ("--bond-pad", r)]
        # The repair is a STITCH and a BOUNDED LOCAL RE-BOND, and nothing else.
        # `--partial` is a search lever for the primary proposal; handing it to
        # the repair would let it lay whole-board tracks of its own, which is a
        # second routing run wearing a repair's name.
        #
        # `--join-residual` IS the repair's business, and the first `--partial`
        # run proved it.  A signal track that slots an outer pour severs the
        # pads the pour was bonding, and `stitch_pad` can only answer with a
        # BARREL: a pad it reports `NO_VIA_SITE` for -- `U3.12` on the expander,
        # 4.213 mm from the nearest ground pad still on the plane -- has no
        # barrel to plant and the whole run is refused for a bond a couple of
        # millimetres of track would restore.  So the repair may also maze-join
        # exactly the islands its own stitch reported unreachable, bounded by
        # `--repair-join-max-mm`, whose default is the 8 mm LOCALITY WINDOW
        # `stitch_pad`/`join_residual_islands` already use (`escape_limit` and
        # `near`) -- read from the primitive, not invented here.  The bound is
        # what keeps this a repair: it cannot haul across the board, and any
        # join over it is reverted and reported `TOO_LONG` rather than taken.
        #
        # `--split-islands` is ALWAYS the repair's question -- an island that
        # sits on its own severed piece of pour is exactly what the repair must
        # re-bond, and the default predicate hides it -- and is the CALLER's
        # choice for the primary proposal.  An earlier cut bound this to an
        # `else` on `if neck`, so the flag followed the necking lever instead of
        # the run: a `--neck` repair silently lost the predicate it exists for,
        # and every non-neck primary silently gained it.  Both halves are now
        # said explicitly.
        if split_islands or not use_search_levers:
            cmd += ["--split-islands"]
        if use_search_levers:
            if join_residual:
                cmd += ["--join-residual"]
            if partial:
                cmd += ["--partial", "--attempt-cap", str(attempt_cap)]
            if join_residual or partial:
                cmd += ["--join-max-mm", str(join_max_mm)]
        else:
            cmd += ["--join-residual",
                    "--join-max-mm", str(repair_join_max_mm)]
        return json.loads(subprocess.run(
            cmd + list(target_nets), check=True, text=True,
            capture_output=True).stdout)

    primary = child(nets)
    routed = primary["results"]
    bonded = primary.get("bonds", [])
    detoured = primary.get("detours", [])
    # ------------------------------------------------------------------ #
    # THE EXACT-GEOMETRY RELAY, AND WHY A LATTICE CANNOT BE THE ONLY ONE
    # ------------------------------------------------------------------ #
    # `maze3d` rasterises, and `QBoard.grid` / `dru_overlay` both add a
    # 0.75-CELL GUARD BAND on top of the clearance so a lattice can never
    # propose copper the exact geometry would refuse.  That guard is right, and
    # it has a consequence nothing here had ever stated: a land whose escape
    # margin is EXACTLY ZERO is buildable and unreachable at the same time.
    # KiCad passes it; the maze cannot propose it at ANY pitch, because the
    # required figure is `clr + 0.75*G` and that strictly exceeds `clr` for
    # every G > 0.
    #
    # D-620 measured the case that forces this.  `U9`'s north row is packed to
    # the micron: `U9.13`/`U9.15` are 0.300 mm transmit-arm lands whose only
    # escape is a 0.300 mm stub in their own 0.300 mm of width, and `U9.14`
    # between them has exactly 0.700 mm of gap for a 0.200 mm track that owes
    # 0.250 mm to each arm -- 0.200 + 0.250 + 0.250 = 0.700, spent exactly.
    # `screen_land_escape_margin.py` reads ZERO for all three, and the maze
    # relay of `NFC_RFO2` returns `NO_PATH` at 0.100 mm, 0.050 mm AND 0.025 mm
    # while `route_local_two_pad.py` -- which works in exact geometry, at its
    # own 0.025 mm lattice and with the pad clearance stated separately -- lays
    # the same arm in 8.674 mm.
    #
    # So a detour record may name an ALLOWLISTED `route_local_two_pad` route as
    # its fallback.  This is not a second router and it is not a weaker one: it
    # is the SAME primitive that laid the copper being put back, it is used only
    # after the maze has refused, the entry it names must be for the detour's
    # OWN net and must join the chain's OWN two ends to the micron, and every
    # gate below -- real KiCad DRC at `--severity-all`, the whole-board ledger,
    # and clause 5's preservation -- judges the result exactly as it judges the
    # maze's.  A relay that comes back illegal is refused here as loudly as one
    # that never came back at all.
    exact_relay = []
    for d in detoured:
        key = d.get("exact_relay")
        if d.get("ok") or not key:
            continue
        chk = exact_relay_pads(scratch, key, d)
        if chk is not None:
            d["reason"], d["why"] = "EXACT_RELAY_REFUSED", chk
            continue
        got = subprocess.run(
            [sys.executable, str(LOCAL_TWO_PAD), key, "--route", str(scratch)],
            text=True, capture_output=True)
        if got.returncode != 0:
            d["reason"] = "EXACT_RELAY_FAILED"
            d["why"] = (got.stderr or "").strip()[-400:]
            continue
        res = json.loads(got.stdout)["result"]
        exact_relay.append(dict(net=d["net"], route=key, ok=bool(res.get("ok")),
                                mm=res.get("mm"), grid=res.get("grid"),
                                was_mm=d.get("was_mm"),
                                reason=res.get("reason")))
        if res.get("ok"):
            d.update(ok=True, mm=res.get("mm"), vias=res.get("vias", 0),
                     exact_relay_used=key, reason=None,
                     why="the maze refused this zero-margin relay at every "
                         "lattice; put back by the exact-geometry primitive "
                         "that laid it")
        else:
            d["reason"] = res.get("reason", "EXACT_RELAY_NO_PATH")
    # EVERY DETOUR MUST HAVE ROUTED.  The applier has already taken the track
    # off the scratch board; a detour that did not go back is a hole in the cut
    # net that no later clause is guaranteed to name, because the two ends may
    # still be joined some other way and clause 4 would then see nothing.  One
    # failure refuses the run.
    detour_failed = [dict(net=d["net"], layer=d["layer"],
                          a_mm=d["a_mm"], b_mm=d["b_mm"],
                          reason=d.get("reason"), why=d.get("why"))
                     for d in detoured
                     if not d.get("ok") and not d.get("removed_only")]
    # D-609.  A detour that spent the OWN-LAYER allowance was handed exactly
    # one layer, so it cannot have left that layer and cannot have drilled a
    # barrel: a single-layer `Field` has nowhere to via to.  That is true by
    # CONSTRUCTION -- which is precisely why the authority states it as a
    # clause rather than trusting it.  A future caller that widens the
    # allowance to a layer SET meets this refusal, not a silent new hole
    # through somebody else's plane.
    for d in detoured:
        if not (d.get("ok") and d.get("own_layer")):
            continue
        if list(d.get("layers") or []) != [d["lkey"]] or d.get("vias"):
            detour_failed.append(dict(
                net=d["net"], layer=d["layer"], a_mm=d["a_mm"],
                b_mm=d["b_mm"], reason="OWN_LAYER_ESCAPED",
                why="the own-layer allowance let this detour onto %s with %s "
                    "via(s); it is licensed for %s alone and for no barrel"
                    % (d.get("layers"), d.get("vias"), d["lkey"])))

    if plane_zone:
        # Every requested region, not just the first: `keep` was a scaffold for
        # the FIRST fill of a pour whose net had no connection yet, and a region
        # left on `keep` would ship islands this run never actually bonded.
        text = scratch.read_text(encoding="utf-8")
        for region in plane_zone["regions"]:
            marker = '(name "%s")' % region["name"]
            head, sep, tail = text.partition(marker)
            if not sep:
                continue
            text = head + marker + tail.replace(
                "(island_removal_mode 1)", "(island_removal_mode 0)", 1)
        scratch.write_text(text, encoding="utf-8")
        plane_zone["island_removal_restored"] = (
            "(island_removal_mode 1)" not in text)

    # A bridge barrel finer than the board's ordinary via floors is legal only
    # because a `.kicad_dru` rule says so INSIDE A NAMED RULE AREA, and the
    # emitter has already refused any barrel whose rule is missing.  Drawing
    # that area is this transaction's job: the rule text names the cluster, the
    # area is centred on the barrel the run actually laid, and clause 6 below
    # audits every rule area on the board so this can never be a back door.
    import maze3d as mz
    bridge_areas = []
    # D-658.  A MOVED BARREL THAT CHANGED GEOMETRY IS LICENSED LIKE ANY OTHER
    # FABRICATION EXCEPTION ON THIS BOARD.  `--detour-spec` may now put a
    # barrel back at a diameter the board's own `min_via_diameter` refuses --
    # that is the whole reason `+3V3`'s `R129.1` is reachable at all -- and the
    # moment it may, this gate owes the same three questions the pour bridge
    # and the pad-escape relief already answer: does the `.kicad_dru` grant
    # THIS net a barrel inside an area named for THIS barrel, is the geometry
    # the spec asked for at least as large as the rule's own minima, and is the
    # area the run drew the area the rule names.  The first two are this
    # clause; the third is clause 6, which audits `want_areas` below and is
    # what stops this from being a back door.
    #
    # A barrel AT OR ABOVE the floor needs no area and gets none: the board
    # already licenses it, and drawing a rule area for it would be a licence
    # nobody asked for sitting on the board forever.
    class _Dru:
        class b:
            @staticmethod
            def GetFileName():
                return str(BOARD)
    move_licences, move_unlicensed = [], []
    for d in (detour or {}).get("detours", ()):
        bar = d.get("barrel") or {}
        if not bar.get("to_mm"):
            continue
        dia = int(round((bar.get("to_dia_mm") or bar["dia_mm"]) * 1e6))
        drill = int(round((bar.get("to_drill_mm") or bar["drill_mm"]) * 1e6))
        was = bar.get("was_at_nm") or [int(round(v * 1e6))
                                       for v in bar["at_mm"]]
        rec = dict(net=d["net"], was_mm=bar["at_mm"], to_mm=bar["to_mm"],
                   dia_mm=round(dia / 1e6, 4), drill_mm=round(drill / 1e6, 4),
                   area=mz.barrel_move_area_name(was[0], was[1]))
        if dia >= BOARD_VIA_DIA_MIN:
            rec.update(ok=True, needs_licence=False,
                       why="at or above the board's own min_via_diameter")
            move_licences.append(rec)
            continue
        lic = mz.barrel_move_licence(_Dru, d["net"], was[0], was[1])
        rec["needs_licence"] = True
        if lic is None:
            rec.update(ok=False, reason="NO_RULE_AREA_LICENCE",
                       why="the .kicad_dru grants %s no via_diameter / "
                           "annular_width / hole_size inside %r"
                           % (d["net"], rec["area"]))
        elif (dia < lic["via_dia"] or drill < lic["via_drill"]
              or (dia - drill) < 2 * lic["annular"]):
            rec.update(ok=False, reason="GEOMETRY_UNDER_LICENCE",
                       licence=dict(via_dia_mm=lic["via_dia"] / 1e6,
                                    via_drill_mm=lic["via_drill"] / 1e6,
                                    annular_mm=lic["annular"] / 1e6),
                       why="the licence's own minima are larger than the "
                           "geometry this spec asked for")
        else:
            rec.update(ok=True, licence=dict(rules=lic["rules"],
                                             via_dia_mm=lic["via_dia"] / 1e6,
                                             via_drill_mm=lic["via_drill"] / 1e6,
                                             annular_mm=lic["annular"] / 1e6))
            bridge_areas.append(dict(kind="barrel-move", name=rec["area"],
                                     net=d["net"], cluster=rec["area"],
                                     xy=[int(round(v * 1e6))
                                         for v in bar["to_mm"]],
                                     via_dia=dia, via_drill=drill,
                                     licence=lic))
        move_licences.append(rec)
        if not rec.get("ok"):
            move_unlicensed.append(rec)
    for r in routed:
        for b in (r.get("bridge") or {}).get("bridges", ()):
            if b.get("area"):
                bridge_areas.append(dict(kind="pour-bridge", name=b["area"],
                                         net=r["net"],
                                         cluster=b["cluster"], xy=b["xy"],
                                         via_dia=b["via_dia"],
                                         via_drill=b["via_drill"],
                                         licence=b.get("licence")))
        # D-606.  A pad-escape relief area is the SAME object as a pour-bridge
        # area -- a pad-sized region that forbids nothing and exists only to be
        # the region an `enclosedByArea` condition names -- so it is drawn by
        # the same code and audited by the same clause 6.  Keeping two lists
        # would have meant two audits, and the second one is the one that gets
        # forgotten.
        for b in (r.get("escape_relief") or {}).get("stitches", ()):
            if b.get("area"):
                bridge_areas.append(dict(kind="pad-escape", name=b["area"],
                                         net=r["net"],
                                         cluster=b["island"], xy=b["xy"],
                                         via_dia=b["via_dia"],
                                         via_drill=b["via_drill"],
                                         licence=b.get("licence")))
            # D-610.  THE RUN'S OWN AREA.  `b["run_rect"]` is the DECLARED
            # rectangle out of the tracked spec, not a box measured off the
            # copper, and `maze3d._run_licence` has already proved the copper
            # fits inside it.  Same object, same clause-6 audit as the barrel
            # area beside it.
            if b.get("run_area"):
                bridge_areas.append(dict(kind="pad-escape-run",
                                         name=b["run_area"], net=r["net"],
                                         cluster=b["island"],
                                         rect=b["run_rect"],
                                         bbox=b.get("run_bbox"),
                                         width_licence=b.get("run_licence_nm")))
    seen_areas = set()
    for a in bridge_areas:
        if a["name"] in seen_areas:
            continue
        seen_areas.add(a["name"])
        if a.get("rect"):
            insert_zone(scratch, run_area_sexpr(a["name"], *a["rect"]))
        else:
            insert_zone(scratch, bridge_area_sexpr(a["name"], a["xy"][0],
                                                   a["xy"][1], a["via_dia"]))

    drc_json = work / "drc.json"
    done = full_drc(scratch, drc_json)

    # ------------------------------------------------------------------ #
    # PLANE REPAIR -- see the doctrine above `gate`.
    # ------------------------------------------------------------------ #
    repair = None
    if repair_planes or eviction:
        mid = ledger(scratch, work / "ledger-mid.json")
        was = {r["net"]: r["open_edges"] for r in base_ledger["nets"]}
        now = {r["net"]: r["open_edges"] for r in mid["nets"]}
        owners = set(plane_nets(scratch))
        # A net this run RIPPED UP is repairable for the same reason a pour a
        # track slotted is: the run itself created the break, and the doctrine
        # is that an evicted net is re-proposed rather than abandoned.  It is
        # offered to the SAME bounded repair child -- 8 mm joins, no whole-board
        # search levers -- so a plane-less evicted net gets a short local
        # reroute and a pour-owning one gets its barrel.  Clause 4 still has the
        # last word: a rip-up whose reroute fails is a refusal.
        repairable = owners | set(eviction["evicted_nets"] if eviction else ())
        hurt = sorted(n for n, v in now.items()
                      if v > was.get(n, v) and n in repairable)
        repair = dict(candidates=hurt,
                      join_max_mm=repair_join_max_mm,
                      evicted_nets=sorted(eviction["evicted_nets"]) if eviction
                      else [],
                      pour_owning_nets=sorted(owners),
                      regressed_before_repair=sorted(
                          n for n, v in now.items() if v > was.get(n, v)),
                      retained_open_edges_before_repair=mid[
                          "connectivity"]["retained_open_edges"])
        if hurt:
            repair["routed"] = child(hurt, use_search_levers=False)["results"]
            drc_json = work / "drc-repaired.json"
            done = full_drc(scratch, drc_json)

    report = json.loads(drc_json.read_text())
    counts = {}
    for v in report.get("violations", []):
        counts[v.get("type", "unknown")] = counts.get(v.get("type"), 0) + 1
    attributable = [v for v in report.get("violations", [])
                    if v.get("type") not in INHERITED]
    inherited_ok = all(counts.get(k, 0) <= n for k, n in INHERITED.items())

    after_ledger = ledger(scratch, work / "ledger-after.json")
    before_open = {r["net"]: r["open_edges"] for r in base_ledger["nets"]}
    after_open = {r["net"]: r["open_edges"] for r in after_ledger["nets"]}
    regressed = sorted(n for n, v in after_open.items()
                       if v > before_open.get(n, v))
    closed = sorted(n for n in before_open
                    if after_open.get(n, 0) < before_open[n])
    edges_before = base_ledger["connectivity"]["retained_open_edges"]
    edges_after = after_ledger["connectivity"]["retained_open_edges"]

    # CLAUSE 13 -- AN INERT REMOVAL MUST BE PRICED.  D-646.  `--detour-spec`
    # may now declare `"relay": false`, which removes a named chain and does
    # NOT put it back, and that is the largest licence in this file: a relay
    # replaces a conductor, a removal claims the board never needed one.  On
    # the AUTHORITATIVE board -- the one the copper was taken from, see
    # `inert_removal_price` -- ONE filled island of that net on that layer must
    # hold both ends of the chain, and the widest pour path between them must
    # be at least as wide as the copper that went.  On the CANDIDATE, the
    # removed net's OWN open-edge count may not grow.  Whether this run's own
    # new copper then splits that pour is PP1-PP4's question and this clause
    # does not answer it.
    removed_only = [d for d in detoured if d.get("removed_only")]
    inert_entries = [d for d in removed_only if not d.get("barrel")]
    # CLAUSE 14 -- A BARREL REMOVAL MUST BE RE-BONDED.  D-653.  A barrel is
    # the one object `--detour-spec` could not name until now, and it is the
    # one whose removal cannot be priced by a pour path: its two ends are on
    # different layers.  `rebond_price` asks the question that belongs to it --
    # does every pad this barrel served still sit in a filled island holding a
    # barrel at least as wide? -- on the authoritative board for the "served"
    # half and on the REFILLED candidate for the "still" half.  The open-edge
    # test below is shared with the inert branch and is not a substitute: a
    # pad can be dragged back into the cluster by a long track and still have
    # lost its local bond, which is a derating nobody chose.
    rebond_entries = [d for d in removed_only if d.get("barrel")]
    inert_priced = (inert_removal_price(BOARD, inert_entries)
                    if inert_entries else [])
    inert_unpriced = [r for r in inert_priced if not r.get("ok")]
    rebond_priced = (rebond_price(BOARD, scratch, rebond_entries)
                     if rebond_entries else [])
    rebond_unpriced = [r for r in rebond_priced if not r.get("ok")]
    for d in removed_only:
        n = d["net"]
        if after_open.get(n, 0) > before_open.get(n, 0):
            grew = dict(net=n, ok=False,
                        reason="REMOVED_NET_OPEN_EDGES_GREW",
                        before=before_open.get(n), after=after_open.get(n))
            (rebond_unpriced if d.get("barrel") else inert_unpriced).append(grew)

    zone_before, zone_after = zones(BOARD), zones(scratch)
    zone_added = [z for z in zone_after if z not in zone_before]
    zone_lost = [z for z in zone_before if z not in zone_after]
    # One added pour per REQUESTED region, all on the requested net and layer.
    # Counting them matters: a run that quietly poured a second region nobody
    # asked for would otherwise pass clause 6 on the shape of the first.
    zone_ok = (not zone_lost
               and len(zone_added) == (len(plane_zone["regions"])
                                       if plane else 0)
               and all(z[0] == nets[0] and z[1] == (plane,)
                       for z in zone_added))

    # Clause 6 audits POURS.  A rule area is not a pour and `zones()` skips it,
    # so without this it would not be audited at all -- and a rule area is
    # exactly the object that can license a geometry nobody reviewed.  Every
    # added rule area must be one this run's own bridge emitter asked for, on
    # all six copper layers, and must FORBID NOTHING: an area that disallowed
    # tracks would be a keep-out, which is a routing decision and not a
    # licence.  None may be lost.
    ra_before, ra_after = rule_areas(BOARD), rule_areas(scratch)
    ra_added = [z for z in ra_after if z not in ra_before]
    ra_lost = [z for z in ra_before if z not in ra_after]
    want_areas = {a["name"] for a in bridge_areas}
    rule_area_ok = (not ra_lost
                    and len(ra_added) == len(want_areas)
                    and all(z[0] in want_areas and len(z[1]) == 6
                            and not any(z[2:6]) for z in ra_added))
    zone_ok = zone_ok and rule_area_ok

    base_cu, cand_cu = copper(BOARD), copper(scratch)
    # Clause 5 is unweakened, it is PARAMETERISED.  Without `--evict` the
    # licensed-removal set is empty and `removed` must be empty, exactly as
    # before.  With it, a removal is legal only if this run's own eviction
    # step recorded that signature -- so a removal the transaction did not
    # authorise, or one the repair child made on its own, is still a refusal.
    # Clause 5 is parameterised by the DETOUR in exactly the same shape it is
    # parameterised by the eviction: a removal is legal only where this run's
    # own applier recorded that signature.  Nothing is loosened -- without
    # `--detour-spec` the set is empty and `removed` must still be empty.
    licensed = (set((eviction or {}).get("removed_signatures", ()))
                | set((detour or {}).get("removed_signatures", ())))
    removed = sorted(str(k) for k in (base_cu - cand_cu))
    unlicensed = sorted(set(removed) - licensed)
    added_nets = sorted({k[1] for k in (cand_cu - base_cu)})
    # A net that fails is reverted atomically by `maze3d.route_net`, so a
    # partial batch is still promotable: the promotion set is exactly the nets
    # that succeeded.  Requiring every added object to be on a SUCCEEDED net is
    # strictly stronger than the old "requested net" test -- it proves the
    # revert of each failed net actually happened, rather than assuming it.
    # The repair lays copper too, so its successes join the promotion set --
    # otherwise clause 5 would call a stitch this gate itself asked for
    # "foreign".  Its FAILURES are not added to `failed`: a plane net the repair
    # could not fully re-bond is judged by clause 4 on the ledger, which is the
    # measurement that matters, not by whether the stitch primitive returned ok.
    repaired = [r for r in (repair or {}).get("routed", []) if r.get("ok")]
    # A net this run BONDED lays copper too, so its successes join the
    # promotion set for the same reason the repair's do -- otherwise clause 5
    # would call a stitch this gate itself asked for "foreign".  A bond that
    # failed is reverted inside `maze3d.bond_pads` and adds nothing, so a net
    # whose every bond failed is NOT admitted here.
    bond_nets = sorted({b["net"] for b in bonded if b.get("bonded")})
    # A DETOURED NET LAYS COPPER TOO, so its successes join the promotion set
    # for the same reason the repair's and the bonds' do -- otherwise clause 5
    # would call a track this gate itself asked for "foreign".  A detour that
    # failed is reverted inside `maze3d.route_points` and adds nothing.
    detour_nets = sorted({d["net"] for d in detoured
                          if d.get("ok") or d.get("removed_only")})
    ok_nets = sorted({r["net"] for r in routed if r.get("ok")}
                     | {r["net"] for r in repaired} | set(bond_nets)
                     | set(detour_nets))
    failed = sorted(r["net"] for r in routed if not r.get("ok"))
    foreign = sorted(set(added_nets) - set(ok_nets))

    # A run must CHANGE the board, not merely survive the gate.  For a maze or
    # stitch run that means at least one net actually routed.  Under `--plane`
    # it does NOT: the pour IS the copper.  A pour that lands on pads the net
    # already reaches closes those edges with no track and no barrel at all,
    # and `edges_after < edges_before` above is the honest proof that it did.
    # Requiring a stitch as well would refuse a promotion whose whole value is
    # the plane -- which is exactly what a plane is for.
    #
    # AND A DETOUR IS THE FOURTH MECHANISM, FOR THE SAME REASON.  D-639.
    # `ok_nets` twenty lines above already says it in its own words -- "A
    # DETOURED NET LAYS COPPER TOO, so its successes join the promotion set for
    # the same reason the repair's and the bonds' do" -- and this clause was
    # never told.  The gap is not hypothetical: the `GND C37.2` transaction
    # removed two crossing tracks under this run's own licence, put both back
    # (`all_relaid: true`, 19 tracks and 4 barrels on `/ACC_DETECT_N` and
    # `Net-(U11-TS_MR)`), and the REFILLED `GND` `B.Cu` pour then flowed into
    # the vacated channel and swallowed the `C37.2` land whole -- retained open
    # edges 44 -> 43, `nets_improved: ["GND"]`, `PP2` islands 58 -> 57 MERGED,
    # zero attributable DRC -- with `stitched: 0` and therefore no "routed"
    # net at all.  That is the `--plane` argument arriving by a different road:
    # the copper that closed the edge was the pour, and what let the pour reach
    # was the detour.
    #
    # THIS CANNOT ADMIT A NO-OP, AND THE REASON IS NOT THIS CLAUSE.
    # `detour_nets` is non-empty only where this run's own applier removed a
    # track by signature and `maze3d.route_points` proved it back, so the board
    # always differs; and clause 4 (`edges_after < edges_before`) still demands
    # the board IMPROVE, which is what refused D-638's own detour run at
    # 44 -> 44 with `all_relaid: true`.  The clause also still fails in its own
    # right: a run with no plane, nothing routed, nothing repaired, no bond and
    # no detour is exactly the vacuous promotion it was written to refuse.
    changed = (bool(plane)
               or any(r.get("ok") and not r.get("already") for r in routed)
               or any(not r.get("already") for r in repaired)
               or bool(bond_nets)
               or bool(detour_nets))
    # CLAUSE 7 -- A LICENCE MAY NOT BE SPENT ON COPPER THAT CONNECTS NOTHING.
    # D-606.  `--escape-relief` is the only lever on this board that lays a
    # barrel the ordinary floors forbid, and it pays for it with a permanent
    # `.kicad_dru` rule and a permanent rule area.  `maze3d.stitch_pad` proves
    # that barrel is LEGAL where it lands; nothing in the proposer proves the
    # pour under it is the plane BODY, and nothing in the proposer CAN -- the
    # pour it reads was filled before the barrel existed.  So the claim is
    # settled here, on the refilled candidate's own ledger, which is the same
    # evidence clause 4 uses: every land a relief stitch served must no longer
    # be a component of its own.  A stitch that leaves its land open is dead
    # copper behind a live licence, and one is enough to refuse the run --
    # remove that pad's rule and run again, which is what the finding is for.
    relief_open = []
    if escape_relief:
        after_groups = {frozenset(x.split("@")[0] for x in grp)
                        for row in after_ledger["nets"] for grp in row["groups"]}
        for r in routed:
            for st in (r.get("escape_relief") or {}).get("stitches", ()):
                if frozenset(st["island"]) in after_groups:
                    relief_open.append(dict(net=r["net"], pad=st["pad"],
                                            island=st["island"],
                                            area=st.get("area"),
                                            via_xy=st["via_xy"]))
    # CLAUSE 8 -- THE POUR PARTITION RIDES WITH THE RUN.  D-623.
    # D-622 built `checks/pour_partition_contract.py` and said in its own words
    # that PP1-PP4 IS THE JUDGE of whether a route severed a pour -- and then
    # left it as a thing a person runs by hand.  That is exactly the shape of
    # the failure it was written for.  D-619's route closed an edge, regressed
    # nothing and drew zero attributable DRC: clause 3 (real KiCad DRC), clause
    # 4 (the ledger's open edges), clause 5 (object preservation) and
    # `pour_bond_guard.py` ALL passed it, and a person caught the 12.461 mm2
    # `GND` fragment by reading island areas.  An instrument nothing invokes is
    # an instrument that catches the next one by luck.
    #
    # PRE IS THE AUTHORITATIVE FILE, NOT A COMMIT.  The contract's `--ref` reads
    # the board out of git, which is the right unit for auditing a promotion
    # after the fact and the wrong one here: the gate's question is about THIS
    # transaction, whose two sides are the authoritative board on disk and the
    # refilled candidate beside it.  `--pre-board` is that unit.
    #
    # AND IT IS RUN AFTER THE REFILL, ON THE SAVED CANDIDATE.  `full_drc` runs
    # `--refill-zones --save-board`, so `scratch` at this point carries the
    # copper a fabricator would get; a partition read before the refill would
    # be a partition of copper the router imagined.  THE FALSE-POSITIVE FLOOR
    # IS A PROPERTY, NOT A TEST: this board is FILL-STABLE -- refilling a fresh
    # copy of it reproduces it byte for byte, the same fact
    # `verify_promotion.py` asserts -- so clause 8 cannot manufacture a split
    # out of refill churn, because there is no refill churn to manufacture it
    # from.  A refill-only "control" would compare a file to itself and prove
    # nothing; the discriminating evidence is the D-621 replay in
    # `evidence/d623-clause8-nonvacuity-replay.json`.
    #
    # AND THE REPORT IS DELETED FIRST.  `--work` is reusable and this same gate
    # can run twice against one directory (a plane repair re-runs the DRC), so
    # a stale `pour-partition.json` left by an earlier pass would be read as
    # THIS pass's verdict if the contract died before writing.  The whole point
    # of the `PP_DID_NOT_RUN` branch is that silence is a refusal; a leftover
    # file would turn that silence back into assent.
    pp_report = work / "pour-partition.json"
    pp_report.unlink(missing_ok=True)
    pp_run = subprocess.run(
        [sys.executable, str(POUR_PARTITION), "--pre-board", str(BOARD),
         "--board", str(scratch), "-o", str(pp_report)],
        text=True, capture_output=True)
    if pp_report.exists():
        partition_doc = json.loads(pp_report.read_text())
        pp_failed = sorted(k for k in ("PP1", "PP2", "PP3", "PP4")
                           if not partition_doc["results"][k]["ok"])
    else:
        # A clause that could not be ASKED is a refusal, not a pass.  This is
        # the `aqroot-demo-unmeasured-vs-refused` reading applied to the gate's
        # own machinery: silence here used to be indistinguishable from assent.
        partition_doc = dict(ok=False, ran=False, returncode=pp_run.returncode,
                             stderr=pp_run.stderr[-2000:])
        pp_failed = ["PP_DID_NOT_RUN"]

    ok = (not attributable and inherited_ok and not regressed
          and not unlicensed and not foreign and edges_after < edges_before
          and zone_ok and changed and not relief_open and not detour_failed
          and not inert_unpriced
          and not rebond_unpriced
          and not pp_failed
          and before == sha256_file(BOARD)
          and authority_before == sha256_file(AUTHORITY))

    summary = dict(
        schema=1,
        # `authoritative_board_sha256` NAMES THE AUTHORITY, ALWAYS.  On a
        # `--board` run it is NOT the board the copper was proposed against;
        # `base_board_sha256` is.  On an authority run the two are one number
        # and this report is byte-identical to every earlier one.
        authoritative_board_sha256=authority_before,
        authoritative_unchanged=(before == sha256_file(BOARD)
                                 and authority_before
                                 == sha256_file(AUTHORITY)),
        base_board=str(BOARD),
        base_board_sha256=before,
        base_is_authority=bool(base_is_authority),
        requested_nets=list(nets),
        routed_nets=ok_nets,
        failed_nets=failed,
        routed=routed,
        drc_exit=done.returncode,
        drc_types=counts,
        inherited_within_baseline=inherited_ok,
        attributable_drc=attributable,
        connectivity=dict(
            retained_open_edges_before=edges_before,
            retained_open_edges_after=edges_after,
            open_retained_nets_before=base_ledger["connectivity"]["open_retained_nets"],
            open_retained_nets_after=after_ledger["connectivity"]["open_retained_nets"],
            nets_improved=closed, nets_regressed=regressed),
        plane=plane_zone,
        plane_repair=repair,
        # CLAUSE 8 -- D-623.  The verdict rides in the report whether it passed
        # or failed, for the same reason `lattice` does: a clause whose result
        # is only visible when it refuses cannot be audited afterwards.
        pour_partition=dict(
            ok=(not pp_failed), failed_clauses=pp_failed,
            pre_board=str(BOARD), report=str(pp_report),
            results={k: v.get("ok") for k, v
                     in (partition_doc.get("results") or {}).items()},
            detail=partition_doc.get("results")),
        bonds=(dict(requested=list(bond_pads), max_mm=bond_max_mm,
                    via=(list(bond_via) if bond_via else None),
                    bonded=sum(b.get("bonded", 0) for b in bonded),
                    nets=bond_nets, detail=bonded) if bond_pads else None),
        # PROVENANCE, not a clause.  The guard changes what the router is
        # allowed to take; the report has to say which spec was in force, or a
        # promotion cannot be reproduced from its own evidence.
        guard=(dict(spec=str(guard), sha256=sha256_file(Path(guard)),
                    tubes=len(load_guard(guard).get("guards", ())))
               if guard else None),
        eviction=eviction,
        exact_relay=exact_relay,
        detour=(dict(requested=str(detour_spec),
                     rung=detour_rung,
                     reserve=detour.get("reserve"),
                     removed_count=detour.get("removed_count"),
                     removed_mm=detour.get("removed_mm"),
                     nets=detour.get("nets"),
                     guard_spec=str(detour_guard_file),
                     own_layer_requested=bool(detour_own_layer),
                     own_layer_spent=[
                         dict(net=d["net"], layer=d["layer"],
                              was_mm=d["was_mm"], mm=d.get("mm"),
                              max_mm=d.get("max_mm"),
                              mm_by_layer=d.get("mm_by_layer"),
                              vias=d.get("vias"))
                         for d in detoured if d.get("own_layer")],
                     relaid=detoured, failed=detour_failed,
                     removed_not_relaid=inert_entries,
                     barrel_move_licences=move_licences,
                     barrel_move_unlicensed=move_unlicensed,
                     inert_price=inert_priced,
                     inert_unpriced=inert_unpriced,
                     removed_barrels=rebond_entries,
                     rebond_price=rebond_priced,
                     rebond_unpriced=rebond_unpriced,
                     all_relaid=(not detour_failed))
                if detour else None),
        preservation=dict(removed_objects=removed,
                          unlicensed_removals=unlicensed,
                          licensed_removals=len(licensed),
                          added_object_nets=added_nets,
                          foreign_added_nets=foreign,
                          reverted_failures_clean=(not foreign),
                          zones_added=zone_added, zones_removed=zone_lost,
                          rule_areas_added=ra_added,
                          rule_areas_removed=ra_lost,
                          rule_area_inventory_ok=rule_area_ok,
                          zone_inventory_ok=zone_ok),
        escape_relief=dict(
            requested=bool(escape_relief),
            via=list(relief_via or RELIEF_VIA),
            extra_width=relief_extra_width or None,
            pads=list(relief_pads),
            bonds_per_island=relief_bonds_per_island,
            # PROVENANCE, not a clause -- the same claim `guard` makes above.
            # A width licence is a permanent grant; a promotion cannot be
            # reproduced from its own evidence unless the evidence names the
            # spec that declared its rectangles and hashes it.
            run_area_spec=(dict(path=str(relief_run_area),
                                sha256=sha256_file(Path(relief_run_area)),
                                areas={k: [v / 1e6 for v in box] for k, box
                                       in load_run_areas(relief_run_area).items()})
                           if relief_run_area else None),
            run_areas_drawn=sorted({a["name"] for a in bridge_areas
                                    if a.get("kind") == "pad-escape-run"}),
            lands_still_open=relief_open,
            lands_closed_ok=(not relief_open),
            stitched=sum(len((r.get("escape_relief") or {}).get("stitches", ()))
                         for r in routed),
            nets=[dict(net=r["net"], **{k: v for k, v in
                                        (r.get("escape_relief") or {}).items()
                                        if k != "net"})
                  for r in routed if r.get("escape_relief")]) if escape_relief
        else None,
        bridges=dict(requested=bool(bridge), licensed_areas=bridge_areas,
                     ladder=[list(v) for v in BRIDGE_LADDER]) if bridge
        else None,
        # D-664.  THE TAP REPORTS ITSELF OR IT DID NOT HAPPEN.  A tap adds a
        # BRANCH to an accepted conductor, and a branch is the one thing a
        # reviewer of this board's copper must be able to find by name: the
        # ledger sees only that an edge closed, and clause 4 cannot tell a
        # T-junction from a pad-to-pad run.  So every tap this run laid is
        # named here with its land, its target object, the exact coordinate on
        # that object, the gap it stood off and the copper it cost.
        taps=dict(requested=bool(tap), max_mm=tap_max_mm, pairs=tap_pairs,
                  stub_forbidden=list(TAP_STUB_FORBIDDEN),
                  joined=sum(len((r.get("tap") or {}).get("taps", ()))
                             for r in routed),
                  nets=[dict(net=r["net"], **{k: v for k, v in
                                              (r.get("tap") or {}).items()
                                              if k != "net"})
                        for r in routed if r.get("tap")]) if tap
        else None,
        pad_bridges=dict(
            requested=bool(bridge_pads), max_mm=bridge_pad_max_mm,
            insets_mm=list(__import__("maze3d").PAD_BRIDGE_INSETS_MM),
            nets=[dict(net=r["net"], **{k: v for k, v
                                        in r["pad_bridge"].items()
                                        if k != "net"})
                  for r in routed if r.get("pad_bridge")]) if bridge_pads
        else None,
        candidate_sha256=sha256_file(scratch),
        # A REFUSAL MUST NAME ITSELF.  D-639.  `ok` is a conjunction of eleven
        # clauses and the summary reported the EVIDENCE for each without ever
        # reporting the VERDICT, so a refused run said only "refuse promotion:
        # gate failed" -- and under `--promote` it said it by raising, before
        # `--out` was ever written.  Two full-authority gate runs were then
        # spent on this board (D-638's, and D-639's first) working out which
        # clause had spoken.  This block is derived from the same locals `ok`
        # is, so it cannot drift from it, and `refused_clauses` is exactly the
        # set whose repair would flip the run.
        gate_clauses=dict(
            attributable_drc=not attributable,
            inherited_within_baseline=bool(inherited_ok),
            no_regression=not regressed,
            no_unlicensed_removal=not unlicensed,
            no_foreign_copper=not foreign,
            board_improved=bool(edges_after < edges_before),
            zones_and_rule_areas=bool(zone_ok),
            board_changed=bool(changed),
            no_open_relief_licence=not relief_open,
            every_detour_relaid=not detour_failed,
            barrel_move_licensed=not move_unlicensed,
            inert_removal_priced=not inert_unpriced,
            rebond_priced=not rebond_unpriced,
            pour_partition=not pp_failed,
            authority_unchanged=bool(before == sha256_file(BOARD)
                                     and authority_before
                                     == sha256_file(AUTHORITY)),
        ),
        promotion_candidate=ok,
    )
    summary["refused_clauses"] = sorted(k for k, v
                                        in summary["gate_clauses"].items()
                                        if not v)
    # AND IT MUST BE READABLE AFTER THE RAISE.  `--out` is written by `main`
    # AFTER `gate` returns, which a refused `--promote` never does, so the one
    # artifact that explains the refusal was the one the refusal destroyed.
    # The work directory is this run's own and is already the home of
    # `detour.json`, `drc.json`, `pour-partition.json` and both ledgers.
    (work / "gate-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8")
    if candidate and ok:
        Path(candidate).write_bytes(scratch.read_bytes())
    if promote:
        # `promote_soft` is the LADDER's contract and nothing else's (D-623).
        # A ladder rung that is refused is not an error -- it is the reason the
        # next rung exists -- so the ladder asks for a summary back and decides
        # for itself.  Without it, `--grid ladder --promote` would abort on the
        # first refusal and never reach the pitch that works.
        if not ok:
            if promote_soft:
                return summary
            raise SystemExit("refuse promotion: gate failed")
        if before != sha256_file(BOARD) or (authority_before
                                            != sha256_file(AUTHORITY)):
            raise SystemExit("refuse promotion: authority changed under the run")
        BOARD.write_bytes(scratch.read_bytes())
        summary["promoted"] = True
        summary["promoted_sha256"] = sha256_file(BOARD)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*")
    ap.add_argument("--propose", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--evict-apply", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--evict-report", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--detour-apply", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--detour-report", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--detour-plan", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--grid", default="100000",
                    help="lattice pitch in nm, `auto` to read it off the "
                         "requested nets' own land margins (D-622), or "
                         "`ladder` to start at `auto` and refine until the "
                         "gate accepts a rung or the cell budget stops it, or "
                         "`best` to run every in-budget rung and RANK the "
                         "accepted ones by copper (a screen; never promotes) "
                         "(D-623)")
    ap.add_argument("--grid-cells", type=int, default=LADDER_CELL_BUDGET,
                    help="`--grid ladder` MEMORY ceiling, in maze3d.Field "
                         "CELLS (nx*ny*layers).  Halving the pitch quadruples "
                         "the raster; the default %d reaches 0.0125 mm on this "
                         "board.  This bounds RAM, not time -- see "
                         "--grid-seconds (D-626)" % LADDER_CELL_BUDGET)
    ap.add_argument("--grid-seconds", type=int, default=LADDER_SECONDS_BUDGET,
                    help="`--grid ladder` TIME budget per rung, in seconds, "
                         "applied to the cost PREDICTED from this net's own "
                         "measured rungs (default %d; 0 disables).  Cells "
                         "cannot tell a 21-second refusal from a 40-minute "
                         "one and this board has both at the same raster "
                         "(D-626)" % LADDER_SECONDS_BUDGET)
    ap.add_argument("--grid-gb", type=float, default=0.0,
                    help="`--grid ladder` MEMORY budget per rung, in GiB, "
                         "priced from the measured %.1f bytes per cell.  "
                         "Default 0 derives it as %.2f of this box's "
                         "MemAvailable and RECORDS both numbers, because "
                         "%d cells is ~%.1f GiB -- safe alone and fatal "
                         "three-up (D-626)"
                         % (CELL_BYTES_MEASURED, LADDER_MEM_FRACTION,
                            LADDER_CELL_BUDGET, rung_gb(LADDER_CELL_BUDGET)))
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--plane", help="add a pour for the single named net on "
                                    "this layer, then stitch its islands")
    ap.add_argument("--plane-outline", action="append", default=None,
                    help="bound the --plane pour to a region instead of the "
                         "whole board: `x0,y0,x1,y1` for a rectangle or "
                         "`x,y x,y x,y ...` for a polygon, in mm.  Repeatable "
                         "-- one pour per cluster of the rail's lands")
    ap.add_argument("--zone-clearance", type=float, default=0.25)
    ap.add_argument("--stitch-width", type=int, default=0,
                    help="stub width in nm; clamped UP to the DRU class "
                         "floor and to board setup's min_track_width")
    ap.add_argument("--join-residual", action="store_true",
                    help="for a plane-served net, maze-join the islands the "
                         "local stitch reported as unreachable")
    ap.add_argument("--join-max-mm", type=float, default=0.0,
                    help="revert and report ANY single join longer than this "
                         "many millimetres of copper -- residual-island joins "
                         "and --partial joins alike; 0 disables the bound")
    ap.add_argument("--escape-floor", action="store_true",
                    help="let a LAND launch at the width `.kicad_dru` section "
                         "5 publishes as its class's MINIMUM, instead of at "
                         "the `opt` figure the .kicad_pcb netclass carries and "
                         "`net_contract` then treats as a floor.  The TRUNK "
                         "width is unchanged and `QBoard.escape` still refuses "
                         "any launch point where the trunk width is not legal, "
                         "so this widens what a package may LAUNCH and nothing "
                         "else.  A class the DRU does not price does not move "
                         "-- the floor is never board setup's min_track_width "
                         "-- so no signal class and no return path is touched. "
                         "Screen it first with screen_escape_class.py (D-630)")
    ap.add_argument("--trunk-floor", action="store_true",
                    help="D-662: let a net route its TRUNK at the width "
                         "`.kicad_dru` section 5 publishes as its class's "
                         "MINIMUM instead of the `opt` figure the .kicad_pcb "
                         "netclass carries and `net_contract` then treats as a "
                         "floor.  `--escape-floor` does this for the LAND; "
                         "this does it for the run, which is the other half of "
                         "the same defect -- `/NFC_SUPPLY` `R107.2 -> U9.8` is "
                         "NO_PATH at 0.600 mm at every pitch and routes in "
                         "13.806 mm at 0.400 mm, the minimum the board's own "
                         "`P3V3 minimum width` rule enforces.  THE DESCENT IS "
                         "PRICED FIRST: `trunk_floor_price` weighs the class "
                         "floor by IPC-2221B at this board's copper against "
                         "the design current section 5 publishes for that "
                         "class, so BAT_MAIN, SYS_MAIN and every unpriced "
                         "class are REFUSED and the refusal is recorded in the "
                         "run's own contract.  Never a licence and never a "
                         "netclass change: the width it descends to is one the "
                         "DRC already enforces as legal")
    ap.add_argument("--neck", action="store_true",
                    help="allow a pad with NO full-width escape to launch at "
                         "the .kicad_dru pad-escape necking minimum, for the "
                         "fine-pitch courtyards that rule names, bounded by "
                         "--neck-max-mm")
    ap.add_argument("--neck-max-mm", type=float, default=0.0,
                    help="bound on ONE necked stub in millimetres "
                         "(0 = the module default)")
    ap.add_argument("--partial", action="store_true",
                    help="complete each plane-less net BEST-EFFORT: union-find "
                         "Kruskal over every island pair, per-pair transaction, "
                         "instead of one all-or-nothing MST")
    ap.add_argument("--attempt-cap", type=int, default=0,
                    help="bound on join attempts per net under --partial "
                         "(0 = unbounded; the dead-terminal prune already "
                         "keeps the complete graph affordable)")
    ap.add_argument("--split-islands", action="store_true",
                    help="for a pour-owning net, also offer the stitch the "
                         "islands whose pads already touch a zone -- the shape "
                         "a SEVERED pour leaves; the plane repair always uses "
                         "this and needs no flag")
    ap.add_argument("--repair-planes", action="store_true",
                    help="after the refill, stitch any POUR-OWNING net whose "
                         "open edges grew, then refill and re-measure; a "
                         "signal track that slots a pour is repaired by a "
                         "barrel rather than refusing the whole run")
    ap.add_argument("--repair-join-max-mm", type=float,
                    default=REPAIR_JOIN_MAX_MM,
                    help="bound in millimetres on ONE plane-repair residual "
                         "join; the default is the 8 mm locality window the "
                         "stitch primitive itself uses")
    ap.add_argument("--evict", action="append", default=[],
                    metavar="NET",
                    help="rip up this net's ROUTED copper where it lies wholly "
                         "inside a requested net's own corridor window and on "
                         "a layer those nets may route on; repeatable.  The "
                         "evicted net is re-proposed by the bounded repair "
                         "pass and clause 4 still requires it to end no worse "
                         "off than it started")
    ap.add_argument("--evict-whole", action="store_true",
                    help="rip up the named evicted nets ENTIRELY -- every "
                         "routed object, every layer, board-wide -- instead of "
                         "only what lies inside a corridor window.  The honest "
                         "unit when the evicted net is itself re-proposed: it "
                         "strands nothing and it clears that net's legacy "
                         "copper off the reserved inner planes.  Every named "
                         "net must therefore also be REQUESTED, so it is "
                         "re-routed as a primary proposal rather than by the "
                         "8 mm local repair pass")
    ap.add_argument("--evict-margin-mm", type=float, default=EVICT_MARGIN_MM,
                    help="how far outside a requested net's own pad bounding "
                         "box the eviction corridor extends")
    ap.add_argument("--evict-window", default=None, metavar="X0,Y0,X1,Y1",
                    help="D-655: STATE the eviction corridor in millimetres "
                         "instead of deriving it from the requested nets' pad "
                         "bounding boxes.  The derived corridor is an upper "
                         "bound and stops being one when a requested net spans "
                         "the board: on `/I2C_SCL_INT` it is 6166 mm2, so "
                         "`--evict /I2C_SCL_INT` takes 84 objects and 178.9 mm "
                         "-- the whole net -- where the screen that asked for "
                         "it named TWO tracks in one 3 mm pocket.  This is a "
                         "RESTRICTION and never a licence: an object must "
                         "still be routed, on a named evicted net, on a "
                         "permitted layer and WHOLLY inside, so nothing "
                         "becomes evictable that was not.  Name the pocket "
                         "screen_pair_corridor_blame.py --per-object reported")
    ap.add_argument("--stitch-via", default=None,
                    help="DIA:DRILL in nm for stitch barrels; clamped UP to "
                         "the DRU hole-size and annular-ring floors")
    ap.add_argument("--bridge", action="store_true",
                    help="for a pour-owning net, join each ORPHAN cluster to "
                         "the plane body with ONE through barrel where its own "
                         "filled copper on one layer lies over another "
                         "cluster's on another -- no escape, no track.  The "
                         "barrel is the coarsest rung of BRIDGE_LADDER that fits; "
                         "one below an ordinary via floor is emitted only "
                         "where the .kicad_dru licenses that net that geometry "
                         "inside the rule area named for that cluster")
    ap.add_argument("--bond-pad", action="append", default=[],
                    metavar="REF.NUM",
                    help="give this pad its OWN escape, run and through barrel "
                         "down to its net's inner-layer plane, even though the "
                         "pour already connects it.  A pad whose only bond is "
                         "pour copper is a SINGLE-POINT bond and every route "
                         "that crosses the neck cuts it; a bonded pad survives "
                         "the cut.  Repeatable; each pad is its own reverted "
                         "transaction")
    ap.add_argument("--bond-via", default=None, metavar="DIA:DRILL",
                    help="nm barrel for bond stitches instead of the netclass "
                         "via; clamped UP to the DRU class drill floor and the "
                         "0.125 mm annular ring.  A bond fails with "
                         "NO_VIA_SITE as a function of DIAMETER, so the "
                         "smallest barrel the board licenses outright "
                         "(500000:250000) reaches pads the netclass via "
                         "cannot")
    ap.add_argument("--bond-max-mm", type=float, default=BOND_MAX_MM,
                    help="window in millimetres for ONE bond stitch; the "
                         "default is the 8 mm locality window `stitch_pad` "
                         "itself uses")
    ap.add_argument("--join-orphans", action="store_true",
                    help="D-608: offer every pair of ORPHAN islands of a "
                         "pour-owning net the same route_join the plane-less "
                         "nets use.  Every other move on this board aims an "
                         "orphan at the plane BODY; merging two orphans closes "
                         "an open edge just as well, and nothing could express "
                         "it")
    ap.add_argument("--join-orphan-max-mm", type=float,
                    default=JOIN_ORPHAN_MAX_MM,
                    help="electrical bound on ONE orphan join (default %.1f)"
                         % JOIN_ORPHAN_MAX_MM)
    ap.add_argument("--bridge-pads", action="store_true",
                    help="D-631: join two lands of the same net with ONE "
                         "STRAIGHT TRACK, both endpoints INSIDE the lands -- "
                         "no escape, no via.  Every other router here escapes "
                         "to a launch point first and reports NO LEGAL ESCAPE "
                         "on a pair that needs no launch; this is the lateral "
                         "twin of --bridge.  The width is the netclass width "
                         "or the .kicad_dru class floor and NOTHING NARROWER, "
                         "and the proof is exact geometry, not a lattice. "
                         "Screen it first with screen_pad_bridge.py")
    ap.add_argument("--bridge-pad-max-mm", type=float,
                    default=BRIDGE_PAD_MAX_MM,
                    help="centre-to-centre bound on ONE pad bridge "
                         "(default %.1f)" % BRIDGE_PAD_MAX_MM)
    ap.add_argument("--body-landing", action="store_true",
                    help="a stitch barrel may land ONLY inside the net's own "
                         "BODY pour (maze3d.body_landing).  A legal barrel is "
                         "not yet a barrel that connects; this is the "
                         "certificate that it will be")
    ap.add_argument("--escape-relief", action="store_true",
                    help="D-606: for a pour-owning net, offer every land the "
                         "unconditional primitives could not close a stitch "
                         "whose BARREL is licensed by a `.kicad_dru` rule "
                         "naming that net inside the pad-sized rule area "
                         "PAD_ESCAPE_<REF>_<PIN>.  Only the barrel is "
                         "relieved: the escape and the run are laid at the "
                         "netclass width, or at the class/board floor only if "
                         "the netclass width fails.  The rule must exist "
                         "BEFORE the run; the transaction draws the area "
                         "around the barrel it actually laid and clause 6 "
                         "audits it.  Screen it first with "
                         "screen_pad_escape_relief.py")
    ap.add_argument("--relief-pad", action="append", default=[],
                    metavar="REF.NUM",
                    help="D-609: offer --escape-relief ONLY these lands.  A "
                         "relief spends a licence or a narrow rung, which is "
                         "the most expensive copper a run can lay; naming the "
                         "lands keeps one measured exception from becoming "
                         "twenty unmeasured ones.  Repeatable; empty means "
                         "every orphan land, exactly as before")
    ap.add_argument("--relief-extra-width", type=int, default=0,
                    help="D-609: add ONE more, narrower rung to the "
                         "--escape-relief width ladder, in nm.  Clamped UP to "
                         "board setup's min_track_width AND to the minimum "
                         "the board's own `.kicad_dru` pad-escape necking rule "
                         "already grants inside the fine-pitch power-package "
                         "courtyards it names, so this can ask for copper the "
                         "board licenses somewhere and can never invent a "
                         "width the board does not name.  WHERE that copper "
                         "may lie stays KiCad's question: gate clause 3 judges "
                         "any segment outside a licensed courtyard at the "
                         "class floor and refuses the run")
    ap.add_argument("--relief-bonds-per-island", type=int, default=1,
                    help="D-610: let --escape-relief bond up to this many "
                         "SEPARATE lands of ONE island.  The default 1 is the "
                         "D-606 behaviour: an island is retired the moment any "
                         "one of its pads reaches the plane, which is right "
                         "when the question is CONNECTIVITY.  It is wrong when "
                         "the question is CURRENT: two 0.200 mm necks in "
                         "parallel carry 1.489 A where one carries 0.745 A, so "
                         "the `U12` VOUT bond is sound at two and thin at one "
                         "(FBV2_P2_ROUTING_PLAN.md section 17 clause 4, ruled "
                         "in D-609).  Every bond past the first closes no edge "
                         "and must ride with one that does -- clause 4 is "
                         "unchanged and still requires the board to improve")
    ap.add_argument("--relief-run-area", type=Path,
                    help="D-610: a tracked JSON spec DECLARING the rectangle "
                         "of each `PAD_ESCAPE_RUN_<REF>` width-licence area, "
                         "in mm: {\"areas\": {\"U12.4\": [x0,y0,x1,y1]}}.  "
                         "With this, a relief run narrower than its class "
                         "floor is laid ONLY where the .kicad_dru grants that "
                         "net that width inside that named area AND the whole "
                         "run fits the declared rectangle; without it the "
                         "narrow rung behaves exactly as D-609's did and is "
                         "judged by real DRC alone.  The rectangle is declared "
                         "BEFORE the router runs and the transaction draws "
                         "that rectangle and no other")
    ap.add_argument("--relief-via", default=None,
                    help="DIA:DRILL in nm for --escape-relief barrels "
                         "(default 350000:200000, the fine-pitch process this "
                         "board already licenses by name)")
    ap.add_argument("--join-islands", action="store_true",
                    help="D-605: after the bridge, the stitch and the residual "
                         "join, offer every still-orphan POUR ISLAND a JUMPER "
                         "to another cluster of the same net -- a track that "
                         "starts and ends INSIDE existing filled copper, with "
                         "no pad escape at either end.  A bridge is the "
                         "zero-length case of this move; screen it first with "
                         "screen_island_join.py")
    ap.add_argument("--join-island-max-mm", type=float, default=0.0,
                    help="cap an island jumper's wavefront at this run length "
                         "(0 = maze3d's own WAVE_STEPS budget)")
    ap.add_argument("--detour-spec", type=Path,
                    help="D-607: SEGMENT eviction.  A JSON spec naming the "
                         "crossing tracks to MOVE and the discs to RESERVE.  "
                         "Each named track is removed whole and laid again "
                         "between its own two end coordinates, around the "
                         "reserved site, so nothing is stranded and the cut "
                         "net's cluster count cannot move.  Clause 5 licenses "
                         "the removals by signature and a detour that will not "
                         "route refuses the whole run.  D-646: an entry may "
                         "declare `\"relay\": false` and be REMOVED and not put "
                         "back, which the gate's inert_removal_priced clause "
                         "then prices.  D-648: a track description may declare "
                         "`\"count\": N` when this board carries that exact "
                         "description N times -- two coincident duplicates are "
                         "ONE conductor and ONE obstacle, and taking only one "
                         "of them leaves the other in the corridor.  `count` "
                         "defaults to 1, so every earlier spec is unchanged.  "
                         "D-653 RE-BOND: an entry may name a BARREL instead "
                         "of a track chain -- {\"net\": ..., \"barrel\": "
                         "{\"at_mm\": [x, y], \"dia_mm\": d, \"drill_mm\": h}} "
                         "-- and that via is removed whole.  A barrel is "
                         "always `relay: false` (its two ends are on different "
                         "layers and no track stands in for it) and is priced "
                         "by the rebond_priced clause instead: every pad it "
                         "served must end in a filled island holding a barrel "
                         "at least as wide.  Use --repair-planes so the run "
                         "lays that replacement itself.  "
                         "Screen it first with screen_segment_evict.py "
                         "--plan-out")
    ap.add_argument("--detour-own-layer", action="store_true",
                    help="D-609: let a detour re-lay its track on the layer it "
                         "ALREADY lawfully occupies, even when that layer is a "
                         "RESERVED inner plane.  The reservation is a rule "
                         "about NEW copper; a detour puts EXISTING copper back "
                         "between its own two ends and the slot is already "
                         "there.  A detour that spends this is given that ONE "
                         "layer and nothing else, so it can add no via and can "
                         "reach no other plane; clause 4 still measures the "
                         "crossed plane's own connectivity after a real refill. "
                         "Price it first with screen_segment_evict.py "
                         "--relay-own-layer")
    ap.add_argument("--tap", action="store_true",
                    help="D-664: THE TAP.  Let an orphan LAND branch onto its "
                         "own net's nearest CONNECTED COPPER -- an ordinary "
                         "T-junction -- instead of hauling to the nearest PAD "
                         "the router is allowed to aim at.  Removes nothing, "
                         "relays nothing and licenses nothing; the target is "
                         "proved by KiCad's own connectivity (TAP1) and every "
                         "object is re-proved by maze3d.verify_laid.  Netclasses "
                         "whose rules govern the SHAPE of the conductor are "
                         "refused BY NAME (TAP4): " + ", ".join(TAP_STUB_FORBIDDEN)
                         + ".  Screen it first with screen_net_tap.py")
    ap.add_argument("--tap-max-mm", type=float, default=0.0,
                    help="skip a land whose nearest own-copper tap site is "
                         "further than this (0 = no bound); a land beyond it is "
                         "DECLINED and reported, never silently dropped")
    ap.add_argument("--tap-pairs", type=int, default=3,
                    help="nearest tap sites offered per land, on distinct "
                         "objects (default 3)")
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec: keep every net OTHER than "
                         "a tube's own out of the copper that is the only "
                         "bond between a pour pad and its island")
    ap.add_argument("--work", default=None)
    ap.add_argument("--board", type=Path, default=None,
                    help="D-668: put this run's question to a STATED base "
                         "board instead of the authority.  Until now this "
                         "module had no board argument at all: every screen "
                         "that drove it -- screen_partial_pairs.py among them "
                         "-- read its CENSUS off whatever board it was given "
                         "and then asked a router that always answered about "
                         "`hardware/demo/kicad/aqroot-demo`, so a question "
                         "about a candidate came back as an answer about the "
                         "authority and an empty report looked like a clean "
                         "one.  The named board's own `.kicad_dru` AND "
                         "`.kicad_pro` must sit beside it -- a scratch "
                         ".kicad_pcb without its project silently drops every "
                         "netclass to Default and every DRU-dependent clause "
                         "with it.  A run whose base is not the authority may "
                         "NEVER promote: --promote is refused at the CLI and "
                         "again inside the gate, `board_improved` is measured "
                         "against the named base, and the report carries "
                         "`base_board`, `base_board_sha256` and "
                         "`base_is_authority` so no reader can mistake one "
                         "for the other")
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    # THE REBIND HAPPENS BEFORE ANYTHING READS A BOARD.  `resolve_grid`,
    # `lattice_advice`, `grid_ladder` and `gate` all read the module global at
    # CALL time, so one assignment here moves the whole run onto the stated
    # base -- and the children (`--propose`, `--evict-apply`, `--detour-apply`)
    # are handed the SCRATCH path explicitly and need no argument of their own.
    if a.board is not None:
        global BOARD
        base = a.board.resolve()
        if not base.is_file():
            ap.error("--board %s does not exist" % a.board)
        missing = [x for x in (".kicad_dru", ".kicad_pro")
                   if not base.with_suffix(x).is_file()]
        if missing:
            ap.error("--board %s has no %s beside it.  A scratch .kicad_pcb "
                     "without its .kicad_pro resolves every netclass to "
                     "Default and the run would measure widths, clearances "
                     "and via floors this board does not have; copy the "
                     "project files next to it (a --work directory left by an "
                     "earlier gate already has them)"
                     % (a.board, " / ".join(missing)))
        if base != AUTHORITY.resolve() and a.promote:
            ap.error("--board %s is not the authority and --promote is "
                     "therefore refused: a transaction measured against a "
                     "candidate has not been measured against the board this "
                     "repository ships.  Take the same run against the "
                     "authority, or ask for --candidate and gate that"
                     % a.board)
        BOARD = base

    via = None
    if a.stitch_via:
        via = tuple(int(v) for v in a.stitch_via.split(":"))
    relief_via = None
    if a.relief_via:
        relief_via = tuple(int(v) for v in a.relief_via.split(":"))
    bond_via = None
    if a.bond_via:
        bond_via = tuple(int(v) for v in a.bond_via.split(":"))
        if bond_via[0] < BOARD_VIA_DIA_MIN:
            ap.error("--bond-via %d nm is under the board min_via_diameter "
                     "(%d nm); a barrel that fine is legal only inside a "
                     ".kicad_dru rule area and bond_pads has no licence "
                     "machinery, so the gate would refuse the run.  Screen it "
                     "with screen_bond_stitch.py --via instead"
                     % (bond_via[0], BOARD_VIA_DIA_MIN))
    if a.propose:
        # the child is always given a RESOLVED pitch by its parent
        propose(a.propose, a.nets, int(a.grid), a.via_cost, a.stitch_width, via,
                a.join_residual, a.join_max_mm, a.neck, a.neck_max_mm,
                a.partial, a.attempt_cap, a.split_islands,
                load_guard(a.guard), a.bridge,
                tuple(a.bond_pad), a.bond_max_mm, bond_via,
                a.join_islands, a.join_island_max_mm,
                a.escape_relief, relief_via,
                json.loads(a.detour_plan.read_text()) if a.detour_plan
                else None,
                a.body_landing, a.join_orphans, a.join_orphan_max_mm,
                a.detour_own_layer, a.relief_extra_width,
                tuple(a.relief_pad), a.relief_bonds_per_island,
                load_run_areas(a.relief_run_area), a.escape_floor,
                a.bridge_pads, a.bridge_pad_max_mm, a.trunk_floor,
                a.tap, a.tap_max_mm, a.tap_pairs)
        return 0
    evict_window_nm = None
    if a.evict_window:
        try:
            v = [float(x) for x in a.evict_window.split(",")]
        except ValueError:
            v = []
        if len(v) != 4 or v[0] >= v[2] or v[1] >= v[3]:
            ap.error("--evict-window wants X0,Y0,X1,Y1 in millimetres with "
                     "X0<X1 and Y0<Y1; got %r" % a.evict_window)
        evict_window_nm = tuple(int(round(x * 1e6)) for x in v)
    if a.evict_window and a.evict_whole:
        ap.error("--evict-window and --evict-whole are contradictory: one "
                 "states a pocket, the other says board-wide.  Pick the unit "
                 "the measurement was taken in")
    if a.evict_window and not a.evict:
        ap.error("--evict-window needs at least one --evict NET; a corridor "
                 "with nothing to evict in it removes nothing")
    if a.evict_apply:
        doc = evict_copper(a.evict_apply, a.nets, set(a.evict),
                           int(round(a.evict_margin_mm * 1e6)),
                           whole=a.evict_whole, window_nm=evict_window_nm)
        text = json.dumps(doc, indent=2, sort_keys=True, default=str)
        if a.evict_report:
            a.evict_report.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0
    if a.detour_apply:
        doc = detour_apply(a.detour_apply, load_detours(a.detour_spec))
        text = json.dumps(doc, indent=2, sort_keys=True, default=str)
        if a.detour_report:
            a.detour_report.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0
    if not a.nets:
        ap.error("name at least one net")
    bad = sorted(set(a.nets) & EXCLUDE)
    if bad:
        ap.error("excluded from generic maze routing: %s" % ", ".join(bad))
    if a.evict_whole:
        if not a.evict:
            ap.error("--evict-whole needs at least one --evict NET")
        orphan = sorted(set(a.evict) - set(a.nets))
        if orphan:
            ap.error("--evict-whole: %s must also be REQUESTED, or the rip-up "
                     "leaves it to the 8 mm repair pass, which cannot rebuild "
                     "a whole net" % ", ".join(orphan))

    extra = dict(plane=a.plane, plane_outline=a.plane_outline,
                 zone_clearance=a.zone_clearance,
                 stitch_width=a.stitch_width, stitch_via=via,
                 join_residual=a.join_residual, join_max_mm=a.join_max_mm,
                 neck=a.neck, neck_max_mm=a.neck_max_mm,
                 partial=a.partial, attempt_cap=a.attempt_cap,
                 repair_planes=a.repair_planes,
                 split_islands=a.split_islands,
                 repair_join_max_mm=a.repair_join_max_mm,
                 evict=tuple(a.evict), evict_margin_mm=a.evict_margin_mm,
                 evict_whole=a.evict_whole, evict_window=a.evict_window,
                 guard=a.guard, bridge=a.bridge,
                 bond_pads=tuple(a.bond_pad), bond_max_mm=a.bond_max_mm,
                 bond_via=bond_via, join_islands=a.join_islands,
                 join_island_max_mm=a.join_island_max_mm,
                 escape_relief=a.escape_relief, relief_via=relief_via,
                 detour_spec=a.detour_spec, body_landing=a.body_landing,
                 detour_own_layer=a.detour_own_layer,
                 relief_extra_width=a.relief_extra_width,
                 relief_pads=tuple(a.relief_pad),
                 relief_bonds_per_island=a.relief_bonds_per_island,
                 relief_run_area=a.relief_run_area,
                 join_orphans=a.join_orphans,
                 join_orphan_max_mm=a.join_orphan_max_mm,
                 escape_floor=a.escape_floor, bridge_pads=a.bridge_pads,
                 bridge_pad_max_mm=a.bridge_pad_max_mm,
                 trunk_floor=a.trunk_floor, tap=a.tap,
                 tap_max_mm=a.tap_max_mm, tap_pairs=a.tap_pairs)
    spec = str(a.grid).strip().lower()
    ladder_spec, best_spec = spec in ("ladder", "best"), spec == "best"
    # `best` REFUSES BOTH TRANSACTION OUTPUTS, not just `--promote`.  `gate()`
    # writes `--candidate` on EVERY rung it accepts, so on a net where two
    # pitches both pass, the candidate file left behind would be the LAST
    # accepted rung while `ladder.best` names the CHEAPEST -- a report and a
    # board that disagree about which run they describe.  A screen that ranks
    # four runs has no single candidate to hand over; ask for the winning pitch
    # by name.
    if best_spec and (a.promote or a.candidate):
        ap.error("--grid best is a SCREEN: it runs EVERY in-budget rung to "
                 "rank them, so it has no single transaction to emit -- a run "
                 "that lays copper at four pitches to keep one is not a "
                 "transaction, and the candidate it left behind would be the "
                 "LAST rung that passed rather than the best one.  Read the "
                 "`ladder.best` block, then take that pitch by name with "
                 "`--grid <nm> --promote` / `--candidate`")
    grid, auto = resolve_grid(BOARD, a.nets,
                              "auto" if ladder_spec else a.grid)
    advice = auto if auto is not None else lattice_advice(BOARD, a.nets, grid)

    def run(g, workdir, soft=False):
        return gate(a.nets, g, a.via_cost, workdir, a.promote, a.candidate,
                    promote_soft=soft, **extra)

    if not ladder_spec:
        if a.work:
            summary = run(grid, a.work)
        else:
            with tempfile.TemporaryDirectory(prefix="aqroot-demo-maze-") as tmp:
                summary = run(grid, tmp)
        # THE ADVICE RIDES WITH THE RUN, PASS OR FAIL.  A `NO_PATH` taken at a
        # lattice one of the net's own lands cannot launch on is not a wall; it
        # is an unasked question, and D-622 is what it costs to leave it
        # unasked.
        summary["lattice"] = advice
    else:
        # --grid ladder / --grid best (D-623).  Coarsest admissible pitch
        # first, then the measured pitches below it, bounded by the cell
        # budget.  `ladder` STOPS AT THE FIRST RUNG THE WHOLE GATE ACCEPTS --
        # and since clause 8 is part of that gate, it cannot stop on a rung
        # that closes an edge by cutting a pour.  `best` runs every in-budget
        # rung and ranks them, because FIRST IS NOT BEST and this board has the
        # number: `/NFC_IRQ` routes at 120.848 mm / 10 vias on the coarsest
        # admissible 0.0667 mm lattice, 105.709 mm / 9 vias at 0.050 mm for
        # 2.3x the search, and 105.492 mm / 9 vias at 0.0333 mm for 3.8x more
        # on top of that.  The knee is real and it is early; ranking is worth
        # paying for once per net, not on every run.
        # THE MEMORY BUDGET IS READ OFF THIS BOX, ONCE, BEFORE ANY RUNG (D-626).
        # Read once rather than per rung so the ladder's floor is a property of
        # the run and not of whatever landed on the machine halfway through.
        avail_gb = mem_available_gb()
        if a.grid_gb:
            gb_budget, gb_basis = a.grid_gb, "--grid-gb"
        elif avail_gb is not None:
            gb_budget = round(avail_gb * LADDER_MEM_FRACTION, 2)
            gb_basis = ("%.2f of MemAvailable %.2f GB"
                        % (LADDER_MEM_FRACTION, avail_gb))
        else:
            gb_budget, gb_basis = None, "unmeasurable, not bounded by memory"
        rungs = grid_ladder(BOARD, a.nets, grid, a.grid_cells, gb_budget)
        trail, summary, by_grid, observed = [], None, {}, []
        for row in rungs:
            # THREE CEILINGS, AND THEY REFUSE FOR DIFFERENT REASONS (D-626).
            # Cells are the hard raster ceiling and are known before anything
            # runs.  GIGABYTES price that raster against THIS box, because 8.5
            # GB is safe alone and fatal three-up.  Seconds bound TIME and are
            # PREDICTED from this net's own rungs, because a cell count cannot
            # tell a 21-second refusal from a 40-minute one.  All three name
            # their number and stay in the report.
            predicted = predict_seconds(observed, row["cells"])
            row = dict(row, predicted_seconds=predicted)
            if row["over_cell_ceiling"]:
                trail.append(dict(row, ran=False,
                                  why="OVER_CELL_CEILING %d > %d"
                                      % (row["cells"], a.grid_cells)))
                continue
            if row["over_memory_budget"]:
                trail.append(dict(row, ran=False,
                                  why="OVER_MEMORY_BUDGET %.2f GiB > %.2f "
                                      "GiB "
                                      "(%s; raise --grid-gb to run it)"
                                      % (row["predicted_gb"], gb_budget,
                                         gb_basis)))
                continue
            if (a.grid_seconds and predicted is not None
                    and predicted > a.grid_seconds):
                trail.append(dict(row, ran=False,
                                  over_budget=True,
                                  why="OVER_TIME_BUDGET predicted %.0f s > "
                                      "%d s (raise --grid-seconds to run it)"
                                      % (predicted, a.grid_seconds)))
                continue
            t0 = time.time()
            if a.work:
                wd = Path(a.work) / ("g%d" % row["grid_nm"])
                s_i = run(row["grid_nm"], wd, soft=True)
            else:
                with tempfile.TemporaryDirectory(
                        prefix="aqroot-demo-maze-") as tmp:
                    s_i = run(row["grid_nm"], tmp, soft=True)
            secs = round(time.time() - t0, 1)
            observed.append((row["cells"], secs))
            trail.append(dict(
                row, ran=True, seconds=secs,
                # THE PREDICTOR IS SCORED IN THE REPORT IT STEERS.  A ratio
                # beside every prediction is the only thing that keeps
                # `--grid-seconds` from being a number nobody can argue with.
                predicted_ratio=(round(secs / row["predicted_seconds"], 2)
                                 if row.get("predicted_seconds") else None),
                promotion_candidate=s_i["promotion_candidate"],
                promoted=bool(s_i.get("promoted")),
                routed_nets=s_i["routed_nets"], failed_nets=s_i["failed_nets"],
                pour_partition_ok=s_i["pour_partition"]["ok"],
                pour_partition_failed=s_i["pour_partition"]["failed_clauses"],
                mm={r["net"]: r.get("mm") for r in s_i["routed"]},
                vias={r["net"]: r.get("vias") for r in s_i["routed"]},
                reasons={r["net"]: r.get("reason") for r in s_i["routed"]}))
            summary = by_grid[row["grid_nm"]] = s_i
            if s_i["promotion_candidate"] and not best_spec:
                break
        if summary is None:
            raise SystemExit(
                "ladder: no rung ran -- every one is over the %d-cell memory "
                "ceiling or the %d s predicted-time budget; the coarsest "
                "admissible pitch for these nets is %d nm"
                % (a.grid_cells, a.grid_seconds, grid))
        # THE RANKING.  Only rungs the WHOLE gate accepted are ranked, so a
        # shorter route that severed a pour cannot win: clause 8 removed it
        # from the field before the sort.  Least copper first, then fewest
        # barrels, then the COARSEST pitch -- because two rungs that lay the
        # same copper are the same answer, and the cheaper search is the one to
        # reproduce it with.
        won = [r for r in trail if r.get("promotion_candidate")]
        for r in won:
            r["total_mm"] = round(sum(v or 0 for v in r["mm"].values()), 3)
            r["total_vias"] = sum(v or 0 for v in r["vias"].values())
        won.sort(key=lambda r: (r["total_mm"], r["total_vias"], -r["grid_nm"]))
        best = won[0] if won else None
        # THE REPORT IS THE BEST RUN, NOT THE LAST ONE.  `best` runs every
        # in-budget rung, so the final rung is simply the finest -- and on a net
        # whose knee is early that rung may be a REFUSAL while an earlier one
        # was accepted.  Flipping `promotion_candidate` on the last rung's
        # summary would publish a refused run's `NO_PATH` under a passing
        # verdict, which is the exact confusion this whole decision exists to
        # remove.  Swap in the winning rung's own summary instead.
        if best_spec and best is not None:
            summary = by_grid[best["grid_nm"]]
        reported_nm = next((g for g, s in by_grid.items() if s is summary),
                           None)
        summary["lattice"] = advice
        summary["ladder"] = dict(
            schema=1, mode=("best" if best_spec else "ladder"),
            # ONE NUMBER, ONE NAME.  D-623 called this `cell_budget` when it
            # was the only budget there was; D-626 gave time and memory their
            # own, so the cell figure is now a CEILING and is spelled that way
            # rather than carried twice under two names (older evidence files
            # keep `cell_budget` -- same number, superseded spelling).
            cell_ceiling=a.grid_cells,
            seconds_budget=a.grid_seconds,
            # A DERIVED BUDGET MUST PUBLISH WHAT IT WAS DERIVED FROM, or the
            # ladder's floor becomes a property of the box that nobody can
            # read back off the report (D-626).
            gb_budget=gb_budget, gb_basis=gb_basis,
            mem_available_gb_at_start=avail_gb,
            cell_bytes_measured=CELL_BYTES_MEASURED,
            coarsest_admissible_nm=grid, chosen_grid_nm=reported_nm,
            rungs_run=sum(1 for r in trail if r.get("ran")),
            rungs_over_budget=[r["grid_nm"] for r in trail
                               if not r.get("ran")],
            rungs=trail,
            accepted_grid_nm=[r["grid_nm"] for r in won],
            best=(dict(grid_nm=best["grid_nm"], grid_mm=best["grid_mm"],
                       total_mm=best["total_mm"], total_vias=best["total_vias"],
                       mm=best["mm"], vias=best["vias"],
                       seconds=best["seconds"], cells=best["cells"],
                       promote_with=("--grid %d --promote" % best["grid_nm"]))
                  if best else None),
            ranking=[dict(grid_nm=r["grid_nm"], grid_mm=r["grid_mm"],
                          total_mm=r["total_mm"], total_vias=r["total_vias"],
                          seconds=r["seconds"]) for r in won],
            doctrine=("coarsest admissible pitch first, then the measured "
                      "pitches below it.  `ladder` stops at the first rung the "
                      "WHOLE gate accepts -- clause 8 included, so a rung that "
                      "closes an edge by severing a pour is not a stopping "
                      "point.  `best` runs every in-budget rung and ranks the "
                      "accepted ones by copper, because FIRST IS NOT BEST"))
    text = json.dumps(summary, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if summary["promotion_candidate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
