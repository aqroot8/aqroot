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
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from screen_inner_plane import insert_zone, zone_sexpr

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
LEDGER = ROOT / "hardware/demo/manufacturing/routing_ledger.py"

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
DRU_CLASS = {
    "Default":      dict(clr=200000, layers=None),
    "I2C":          dict(clr=200000, layers=None),
    "I2S":          dict(clr=200000, layers=None),
    "NFC_RX":       dict(clr=200000, layers=None),
    "NFC_OSC":      dict(clr=200000, layers=None),
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
    "NFC_RF":       dict(clr=200000, layers=None),
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

# How far a licence area extends BEYOND the barrel it licenses.  KiCad answers
# `enclosedByArea` against the item's copper, not its centre, so the area has to
# contain the whole annulus -- the first run of this lever drew a fixed 0.5 mm
# square, the emitter chose a 0.60 mm barrel for `R19.1`, the area did not
# enclose it and the POWER-class 0.40 mm drill rule correctly won.  The area is
# therefore sized FROM the barrel.  0.15 mm of margin is comfortably more than
# the rounding and comfortably less than the 0.25 mm hole-to-hole minimum, so
# no second via can ever be enclosed by another via's licence.
BRIDGE_AREA_MARGIN_MM = 0.15

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


def evict_copper(path, nets, evict_nets, margin_nm):
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

    def contained(item):
        bb = item.GetBoundingBox()
        return any(bb.GetLeft() >= box[0] and bb.GetTop() >= box[1]
                   and bb.GetRight() <= box[2] and bb.GetBottom() <= box[3]
                   for box in boxes.values())

    doomed = []
    for t in board.GetTracks():
        cls = t.GetClass()
        if cls not in ROUTED_TAGS or t.GetNetname() not in evict_nets:
            continue
        if cls == "PCB_TRACK" and t.GetLayer() not in keep_layers:
            continue
        if contained(t):
            doomed.append(t)

    sigs = []
    for t in doomed:
        sigs.append(ir._via_sig(t) if t.GetClass() == "PCB_VIA"
                    else ir._track_sig(t))
        board.Remove(t)
    pcbnew.SaveBoard(str(path), board)
    return dict(
        evicted_nets=sorted(set(evict_nets)),
        corridor_layers=sorted(short),
        margin_mm=round(margin_nm / 1e6, 3),
        corridors={n: dict(
            box_mm=[round(v / 1e6, 3) for v in b],
            area_mm2=round((b[2] - b[0]) * (b[3] - b[1]) / 1e12, 3))
            for n, b in sorted(boxes.items())},
        removed_signatures=sorted(str(s) for s in sigs),
        removed_count=len(sigs),
        removed_by_net={n: sum(1 for s in sigs if s[1] == n)
                        for n in sorted({s[1] for s in sigs})})


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
EXCLUDE = {
    "/04_SPI_B_RADIOS_NFC/NFC_RFI1",    # NFC receive arms: length/symmetry
    "/04_SPI_B_RADIOS_NFC/NFC_RFI2",
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def net_contract(board, net):
    """The width / clearance / via / layer contract for ONE net."""
    info = board.FindNet(net)
    if info is None:
        raise SystemExit("net %r is not on the board" % net)
    cls = info.GetNetClassName()
    nc = info.GetNetClassSlow()
    over = DRU_CLASS.get(cls, {})
    return dict(
        net=net, netclass=cls,
        width=max(nc.GetTrackWidth(), over.get("width", 0)),
        clr=max(nc.GetClearance(), over.get("clr", 0)),
        via_dia=nc.GetViaDiameter(), via_drill=nc.GetViaDrill(),
        layers=over.get("layers"),
        known_class=cls in DRU_CLASS,
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
    """
    out = {}
    for g in spec.get("guards", ()):
        if not g.get("ok") or g["net"] == net:
            continue
        out.setdefault(g["lkey"], []).extend(
            (p[0], p[1], g["keepout_radius"]) for p in g["points"])
    return out


def propose(path, nets, grid, via_cost_mm, stitch_width=0, stitch_via=None,
            join_residual=False, join_max_mm=0.0, neck=False,
            neck_max_mm=0.0, partial=False, attempt_cap=0,
            split_islands=False, guard_spec=None, bridge=False):
    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz

    ref = pcbnew.LoadBoard(str(path))
    contracts = {n: net_contract(ref, n) for n in nets}
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
        if stitch_width:
            c["width"] = max(stitch_width,
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
                qb, net, c["width"], c["clr"], c["clr"], BRIDGE_LADDER,
                via_floors(c["netclass"]), G=grid, layers=c["layers"], guard=g)
        field = mz.Field(qb, net, c["width"], c["clr"], c["clr"],
                         c["via_dia"], c["via_drill"], G=grid,
                         layers=c["layers"], neck=neck_rule, guard=g)
        # A net that owns a filled pour is completed by dropping each island
        # onto that pour, not by a pad-to-pad MST across the signal layers.
        if mz.has_plane(qb, net):
            r = mz.stitch_net(qb, net, width=c["width"], clr_pad=c["clr"],
                              clr_trk=c["clr"], via_dia=c["via_dia"],
                              via_drill=c["via_drill"], G=grid, field=field,
                              split_islands=split_islands)
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
        else:
            r = mz.route_net(qb, net, width=c["width"], clr_pad=c["clr"],
                             clr_trk=c["clr"], via_dia=c["via_dia"],
                             via_drill=c["via_drill"], G=grid,
                             via_cost_mm=via_cost_mm, field=field,
                             partial=partial, attempt_cap=attempt_cap,
                             join_max_mm=join_max_mm)
            r["mode"] = "maze+partial" if partial else "maze"
        if bridged is not None:
            r["bridge"] = bridged
            r["mode"] = "bridge+" + r["mode"]
            r["ok"] = bool(r.get("ok")) or bool(bridged.get("bridged"))
        r["seconds"] = round(time.time() - t0, 1)
        print("  %-44s %-6s %s %.0fs" % (
            net, r["mode"], "ok" if r.get("ok") else r.get("reason", "FAIL"),
            time.time() - t0), file=sys.stderr, flush=True)
        r["contract"] = {k: c[k] for k in
                         ("netclass", "width", "clr", "via_dia", "via_drill",
                          "layers", "reserved_inner_planes",
                          "guarded_layers")}
        results.append(r)
    qb.save(str(path))
    print(json.dumps(dict(results=results), default=str))


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
         plane=None, zone_clearance=0.25, stitch_width=0, stitch_via=None,
         join_residual=False, join_max_mm=0.0, neck=False, neck_max_mm=0.0,
         partial=False, attempt_cap=0, repair_planes=False,
         split_islands=False, repair_join_max_mm=REPAIR_JOIN_MAX_MM,
         evict=(), evict_margin_mm=EVICT_MARGIN_MM, guard=None,
         bridge=False):
    before = sha256_file(BOARD)
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
            + [x for n in evict for x in ("--evict", n)]
            + list(nets), check=True, text=True, capture_output=True)
        eviction = json.loads(report.read_text())

    # `--plane`: give a plane-less power net a pour, then let the ordinary
    # stitch primitive plant its islands on it.  The pour is added UNFILLED and
    # filled by the real KiCad engine; its first fill must keep every island
    # (a net that owns no copper yet has no connection for `remove` to spare),
    # and the mode is flipped back to `remove` after the stitch so the promoted
    # board carries no island that the stitch did not actually connect.
    plane_zone = None
    if plane:
        if len(nets) != 1:
            raise SystemExit("--plane routes exactly one net")
        plane_zone = dict(net=nets[0], layer=plane,
                          name="%s %s PLANE" % (plane.split(".")[0], nets[0]),
                          clearance=zone_clearance)
        insert_zone(scratch, zone_sexpr(nets[0], plane, plane_zone["name"],
                                        clearance=zone_clearance, islands=1))
        plane_zone["first_fill_exit"] = fill_only(scratch, work / "fill.json")

    def child(target_nets, use_search_levers=True):
        """Run the proposer on the scratch board for these nets."""
        cmd = [sys.executable, __file__, "--propose", str(scratch),
               "--grid", str(grid), "--via-cost", str(via_cost_mm)]
        # The guard binds the REPAIR too.  A repair that re-bonded one pad by
        # slotting another pad's only bond would be trading one orphan for the
        # next, and clause 4 would refuse the run either way.
        if guard:
            cmd += ["--guard", str(guard)]
        if stitch_width:
            cmd += ["--stitch-width", str(stitch_width)]
        if stitch_via:
            cmd += ["--stitch-via", "%d:%d" % stitch_via]
        if neck:
            cmd += ["--neck", "--neck-max-mm", str(neck_max_mm)]
        # The bridge is the primary proposal's lever, not the repair's.  A
        # repair re-bonds copper THIS run severed and does it with the stitch;
        # letting it also drop fine barrels into pours it never touched would
        # be a second transaction wearing a repair's name.
        if bridge and use_search_levers:
            cmd += ["--bridge"]
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
            capture_output=True).stdout)["results"]

    routed = child(nets)

    if plane_zone:
        text = scratch.read_text(encoding="utf-8")
        marker = '(name "%s")' % plane_zone["name"]
        head, _, tail = text.partition(marker)
        tail = tail.replace("(island_removal_mode 1)",
                            "(island_removal_mode 0)", 1)
        scratch.write_text(head + marker + tail, encoding="utf-8")
        plane_zone["island_removal_restored"] = (
            "(island_removal_mode 1)" not in (head + marker + tail))

    # A bridge barrel finer than the board's ordinary via floors is legal only
    # because a `.kicad_dru` rule says so INSIDE A NAMED RULE AREA, and the
    # emitter has already refused any barrel whose rule is missing.  Drawing
    # that area is this transaction's job: the rule text names the cluster, the
    # area is centred on the barrel the run actually laid, and clause 6 below
    # audits every rule area on the board so this can never be a back door.
    bridge_areas = []
    for r in routed:
        for b in (r.get("bridge") or {}).get("bridges", ()):
            if b.get("area"):
                bridge_areas.append(dict(name=b["area"], net=r["net"],
                                         cluster=b["cluster"], xy=b["xy"],
                                         via_dia=b["via_dia"],
                                         via_drill=b["via_drill"],
                                         licence=b.get("licence")))
    for a in bridge_areas:
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
            repair["routed"] = child(hurt, use_search_levers=False)
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

    zone_before, zone_after = zones(BOARD), zones(scratch)
    zone_added = [z for z in zone_after if z not in zone_before]
    zone_lost = [z for z in zone_before if z not in zone_after]
    zone_ok = (not zone_lost and len(zone_added) == (1 if plane else 0)
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
                    and len(ra_added) == len(bridge_areas)
                    and all(z[0] in want_areas and len(z[1]) == 6
                            and not any(z[2:6]) for z in ra_added))
    zone_ok = zone_ok and rule_area_ok

    base_cu, cand_cu = copper(BOARD), copper(scratch)
    # Clause 5 is unweakened, it is PARAMETERISED.  Without `--evict` the
    # licensed-removal set is empty and `removed` must be empty, exactly as
    # before.  With it, a removal is legal only if this run's own eviction
    # step recorded that signature -- so a removal the transaction did not
    # authorise, or one the repair child made on its own, is still a refusal.
    licensed = set((eviction or {}).get("removed_signatures", ()))
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
    ok_nets = sorted({r["net"] for r in routed if r.get("ok")}
                     | {r["net"] for r in repaired})
    failed = sorted(r["net"] for r in routed if not r.get("ok"))
    foreign = sorted(set(added_nets) - set(ok_nets))

    # A run must CHANGE the board, not merely survive the gate.  For a maze or
    # stitch run that means at least one net actually routed.  Under `--plane`
    # it does NOT: the pour IS the copper.  A pour that lands on pads the net
    # already reaches closes those edges with no track and no barrel at all,
    # and `edges_after < edges_before` above is the honest proof that it did.
    # Requiring a stitch as well would refuse a promotion whose whole value is
    # the plane -- which is exactly what a plane is for.
    changed = (bool(plane)
               or any(r.get("ok") and not r.get("already") for r in routed)
               or any(not r.get("already") for r in repaired))
    ok = (not attributable and inherited_ok and not regressed
          and not unlicensed and not foreign and edges_after < edges_before
          and zone_ok and changed and before == sha256_file(BOARD))

    summary = dict(
        schema=1,
        authoritative_board_sha256=before,
        authoritative_unchanged=(before == sha256_file(BOARD)),
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
        # PROVENANCE, not a clause.  The guard changes what the router is
        # allowed to take; the report has to say which spec was in force, or a
        # promotion cannot be reproduced from its own evidence.
        guard=(dict(spec=str(guard), sha256=sha256_file(Path(guard)),
                    tubes=len(load_guard(guard).get("guards", ())))
               if guard else None),
        eviction=eviction,
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
        bridges=dict(requested=bool(bridge), licensed_areas=bridge_areas,
                     ladder=[list(v) for v in BRIDGE_LADDER]) if bridge
        else None,
        candidate_sha256=sha256_file(scratch),
        promotion_candidate=ok,
    )
    if candidate and ok:
        Path(candidate).write_bytes(scratch.read_bytes())
    if promote:
        if not ok:
            raise SystemExit("refuse promotion: gate failed")
        if before != sha256_file(BOARD):
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
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--plane", help="add a pour for the single named net on "
                                    "this layer, then stitch its islands")
    ap.add_argument("--zone-clearance", type=float, default=0.25)
    ap.add_argument("--stitch-width", type=int, default=0,
                    help="stub width in nm; clamped UP to the DRU class floor")
    ap.add_argument("--join-residual", action="store_true",
                    help="for a plane-served net, maze-join the islands the "
                         "local stitch reported as unreachable")
    ap.add_argument("--join-max-mm", type=float, default=0.0,
                    help="revert and report ANY single join longer than this "
                         "many millimetres of copper -- residual-island joins "
                         "and --partial joins alike; 0 disables the bound")
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
    ap.add_argument("--evict-margin-mm", type=float, default=EVICT_MARGIN_MM,
                    help="how far outside a requested net's own pad bounding "
                         "box the eviction corridor extends")
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
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec: keep every net OTHER than "
                         "a tube's own out of the copper that is the only "
                         "bond between a pour pad and its island")
    ap.add_argument("--work", default=None)
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    via = None
    if a.stitch_via:
        via = tuple(int(v) for v in a.stitch_via.split(":"))
    if a.propose:
        propose(a.propose, a.nets, a.grid, a.via_cost, a.stitch_width, via,
                a.join_residual, a.join_max_mm, a.neck, a.neck_max_mm,
                a.partial, a.attempt_cap, a.split_islands,
                load_guard(a.guard), a.bridge)
        return 0
    if a.evict_apply:
        doc = evict_copper(a.evict_apply, a.nets, set(a.evict),
                           int(round(a.evict_margin_mm * 1e6)))
        text = json.dumps(doc, indent=2, sort_keys=True, default=str)
        if a.evict_report:
            a.evict_report.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0
    if not a.nets:
        ap.error("name at least one net")
    bad = sorted(set(a.nets) & EXCLUDE)
    if bad:
        ap.error("excluded from generic maze routing: %s" % ", ".join(bad))

    extra = dict(plane=a.plane, zone_clearance=a.zone_clearance,
                 stitch_width=a.stitch_width, stitch_via=via,
                 join_residual=a.join_residual, join_max_mm=a.join_max_mm,
                 neck=a.neck, neck_max_mm=a.neck_max_mm,
                 partial=a.partial, attempt_cap=a.attempt_cap,
                 repair_planes=a.repair_planes,
                 split_islands=a.split_islands,
                 repair_join_max_mm=a.repair_join_max_mm,
                 evict=tuple(a.evict), evict_margin_mm=a.evict_margin_mm,
                 guard=a.guard, bridge=a.bridge)
    if a.work:
        summary = gate(a.nets, a.grid, a.via_cost, a.work, a.promote,
                       a.candidate, **extra)
    else:
        with tempfile.TemporaryDirectory(prefix="aqroot-demo-maze-") as tmp:
            summary = gate(a.nets, a.grid, a.via_cost, tmp, a.promote,
                           a.candidate, **extra)
    text = json.dumps(summary, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if summary["promotion_candidate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
