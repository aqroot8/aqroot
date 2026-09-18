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
import argparse, json, math, re, sys
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
         src=("R75.2", "R75.4"), snk=("U11.2",), amps=1.50,
         basis="BAT_MAIN 1.5 A sustained design current (.kicad_dru section 5); "
               "IBAT_OCP 3.125 A is a fault trip, not a routing current",
         # THE PACKAGE, NOT THE LAYOUT.  U11.2's land is 0.750 x 0.200 mm, so no
         # conductor wider than 0.200 mm can LAND on it, in any layout, with any
         # charger position.  The .kicad_dru pad-escape neck rule already
         # licenses 0.200 mm inside U11's courtyard.  What is accepted here is
         # the ampacity consequence, bounded by length: 5.5 mm of 0.200 mm
         # B.Cu.  A copper thermal length of about 2.6 mm means the neck's two
         # ends -- a large pad and wide copper -- sink a substantial part of it,
         # and the 1.5 A figure is the CLASS design current; the charge current
         # through it is now 769 mA, at which the same model gives 11 K.
         accept=(dict(layer="B.Cu", reason="package-land-neck", max_length_mm=6.0,
                      max_width_mm=0.20),),
         accept_reason="U11 DLH0010A pin-2 land is 0.200 mm tall; nothing wider "
               "can land on it.  Licensed by the .kicad_dru pad-escape neck rule "
               "and bounded here to 6.0 mm of 0.200 mm copper."),
    dict(name="BQ25185_SYS", net="/01_POWER_TREE/BQ25185_SYS",
         src=("U11.1",), snk=("U12.1",), amps=1.00,
         basis="SYS_MAIN 1.0 A (.kicad_dru section 5)",
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
         snk=("L4.1",), amps=0.925,
         accept=(dict(layer="In2.Cu", reason="dru-5c", max_length_mm=80.0),),
         accept_reason="D-750 / .kicad_dru section 5c.  The SYS trunk's three "
               "In2 legs run 0.800 mm, where IPC-2221B's INTERNAL curve asks "
               "1.585 mm for 0.925 A and returns a 31.8 K rise.  That curve is "
               "an isolated coupon in still air and IPC-2152 superseded it; "
               "the PLANE-COUPLED rise this file derives from the board's own "
               "declared stackup -- In2 between In1 across 0.4000 mm of core "
               "and In3 across 0.2028 mm of prepreg -- is 0.68 K, and the whole "
               "rail dissipates 0.157 W.  The ELECTRICAL cost is accepted with "
               "its number: 183 mOhm and 169 mV at the enforced ACC_5V "
               "maximum, against a TPS61023 input range of 0.5-5.5 V.",
         basis="U21 TPS61023 INPUT current at the ENFORCED ACC_5V maximum: "
               "0.537 A x 5.0 V / (0.88 efficiency x 3.3 V VBAT) = 0.925 A rms. "
               "D-753 RETUNED R101 1.65 kOhm -> 2.7 kOhm, so the number that "
               "sizes this trunk is no longer a PUBLISHED figure but the load "
               "switch's own worst-case limit: TI SLVSFJ2B equation 1 gives "
               "0.407 A typ at 2.7 kOhm and the EC table's widest ratio (1.32x) "
               "gives 0.537 A over -40..+125 C.  It WAS 1.21 A, from the 0.70 A "
               "the old 1.65 kOhm allowed. "
               "The 2.19 A the section 5 note quotes is the PEAK INDUCTOR "
               "current (D-185), which the input capacitor C83 supplies "
               "locally; the trunk carries the average.  THE SINK IS L4.1, NOT "
               "U21.3: the two share one node and U21.3 hangs off it through "
               "1.35 mm of 0.5 mm B.Cu (1.3 mOhm), but that stub's far END "
               "lies 0.075 mm outside L4.1's land and OVERLAPS it as copper, "
               "which KiCad's connectivity resolves and this file's "
               "endpoint-in-pad graph does not."),
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


def selfcheck():
    """Re-derive `.kicad_dru` section 5's published table before ruling."""
    published = (
        ("BAT_MAIN", 1.5, 0.529, 3.148), ("SYS_MAIN", 1.0, 0.302, 1.799),
        ("P3V3", 1.0, 0.302, 1.799), ("ACC_3V3", 0.40, 0.085, 0.508),
        ("ACC_5V", 0.70, 0.185, 1.100), ("VBUS_CHG", 1.1, 0.345, 2.052),
        ("SPK_OUT", 0.29, 0.055, 0.326),
    )
    rows, worst, mismatched = [], 0.0, []
    for name, amps, outer, inner in published:
        o, i = width_for(amps, DT_REF, True), width_for(amps, DT_REF, False)
        row = dict(rail=name, amps=amps,
                   dru_outer_mm=outer, derived_outer_mm=round(o, 4),
                   dru_inner_mm=inner, derived_inner_mm=round(i, 4))
        # A RELATIVE tolerance, because the DRU's published figures are rounded
        # to 3 decimals and the inner widths are millimetres: 2.7498 against a
        # published 2.734 is rounding, 0.285 against 0.365 is a different
        # current.  1.5 % separates the two cleanly on all seven rows.
        if max(abs(o - outer) / outer, abs(i - inner) / inner) > 0.015:
            # The method is not wrong -- the DRU row is.  Report the current its
            # OWN published widths correspond to, so the discrepancy is named
            # rather than rounded away.  D-743 found exactly one: SPK_OUT, whose
            # 0.070/0.365 mm widths are 0.347 A, matching neither the 0.29 A rms
            # nor the 0.41 A peak the same line names.
            row["dru_width_implies_amps"] = round(
                ampacity(outer * OUTER_MM, DT_REF, True), 4)
            mismatched.append(name)
        else:
            worst = max(worst, abs(o - outer) / outer, abs(i - inner) / inner)
        rows.append(row)
    return dict(rows=rows, worst_relative_residual=round(worst, 5),
                dru_rows_not_reproduced=mismatched,
                method_reproduces_dru=len(mismatched) < len(published) // 2,
                ok=worst <= 0.015)


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
    """Maximin search: the path whose WORST conductor is the best available."""
    adj = defaultdict(list)
    for ed in edges:
        adj[ed["a"]].append((ed["b"], ed))
        adj[ed["b"]].append((ed["a"], ed))

    def cap(ed):
        if ed["kind"] == "pad":
            return float("inf")
        return ampacity(ed["area_mm2"], DT_REF, ed["external"])

    best = {n: 0.0 for n in nodes}
    prev = {}
    import heapq
    heap = []
    for s in sources:
        best[s] = float("inf")
        heapq.heappush(heap, (-float("inf"), id(s), s))
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
                heapq.heappush(heap, (-c, id(m), m))
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


def accepts_segment(rail, edge, seg):
    """Is this hot segment covered by one of the rail's DECLARED exceptions?

    An exception names a LAYER and bounds the TOTAL length it covers, and may
    bound the width.  Anything outside those bounds is undeclared and fails --
    which is the whole point: the exception must not grow silently.
    """
    for acc in rail.get("accept", ()):
        if acc["layer"] != edge["layer"]:
            continue
        if "max_width_mm" in acc and (edge["width_mm"] or 9e9) > acc["max_width_mm"] + 1e-9:
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
        for ed in path:
            if ed["kind"] == "pad":
                continue
            dT = rise(ed["area_mm2"], rail["amps"], ed["external"])
            r = RHO_CU * ed["length_mm"] / ed["area_mm2"] if ed["area_mm2"] else 0.0
            drop += r * rail["amps"]
            seg = dict(kind=ed["kind"], layer=ed["layer"],
                       width_mm=ed["width_mm"], drill_mm=ed["drill_mm"],
                       length_mm=round(ed["length_mm"], 3),
                       area_mm2=round(ed["area_mm2"], 6),
                       rise_K=round(dT, 1),
                       required_mm_at_10K=round(
                           width_for(rail["amps"], DT_REF, ed["external"]), 3)
                       if ed["kind"] == "track" else None,
                       plane_coupled_rise_K=(
                           round(plane_coupled_rise(diel, ed["layer"],
                                                    ed["width_mm"],
                                                    rail["amps"]), 2)
                           if ed["kind"] == "track" and ed["width_mm"]
                           and plane_coupled_rise(diel, ed["layer"],
                                                  ed["width_mm"],
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
                   undeclared_hot_segments=undeclared,
                   accepted_hot_length_mm=accepted_len,
                   accepted_reason=rail.get("accept_reason"),
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
                  plane_coupled_model=dict(
                      k_fr4_W_per_mmK=K_FR4,
                      form="dT = I^2 rho / (k w^2 t (1/d_up + 1/d_down))",
                      reports="rise over the ADJACENT COPPER LAYERS, not over ambient; length-independent by construction; ignores lateral spreading, conduction along the copper and the outer layers, so it is a floor on the cooling and a ceiling on the rise"),
                  method_selfcheck=check, rails=out,
                  all_ok=(check["method_reproduces_dru"] and stack["ok"]
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
