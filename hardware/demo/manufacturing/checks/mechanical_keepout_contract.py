#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the MECHANICAL KEEP-OUT contract (MK1-MK12).

WHY THIS FILE EXISTS.  `FBV2_P1_KEEPOUTS.md` is marked **NORMATIVE for FBV2-P2
and for the enclosure CAD**, and until D-759 not one of its statements was
checked against the board.  `keepout_stackup_contract` audits the rule areas
that forbid COPPER; `placement_contract` audits what a MOVE did.  Neither can
say whether a mounting hole is where the register puts it, whether the sealed
acoustic cavity is still free of rear parts, or whether a moulded support rib
would land on a switching converter.

D-758 AND D-759 ARE BOTH WHAT HAPPENS WITHOUT IT.  `BOSS1`'s hole was the one
object on this board that never took the FBV2-EXP-002 re-base: it sat 1.000 mm
west of its own keep-out for the whole programme, so four pours stood 0.2505 mm
from the edge of a 2.200 mm NPTH instead of 1.1505 mm.  And D-758, reading the
register's section-1 coordinates as current when the file's own header says they
all gain +1.000 mm, "fixed" it by moving the two keep-outs and `BOSS2` to the
PRE-REBASE positions -- correcting a real defect into a different one.

    MK1  THE DATUM IS PROVED BY THE BOARD, not assumed.  Four parts whose
         mechanical window is their own reason for existing -- `U6` in
         IR_RX_OPTICAL, `D1` in IR_TX_OPTICAL, `J3` in USB_APERTURE, `MK1` in
         MIC_ACOUSTIC -- must each lie inside the RE-BASED window, and at least
         one of them must NOT fit the section-1 window.  If the board ever
         stops being on this datum, every clause below is asking the wrong
         question and this one says so first.
    MK2  BOSS RETENTION.  Each M2 hole sits at its registered doc position;
         its keep-out rule area is the registered rectangle; that rectangle
         covers the Ø4.500 mm the footprint specifies ABOUT THE HOLE; and no
         routed copper, pour fill, pad or courtyard lies inside that circle.
    MK3  REAR SUPPORT RIBS are component-free on the BACK.  A rib is moulded
         plastic bearing on the rear face; a part under one is crushed or
         stops the shell closing.
    MK4  SPEAKER_ZONE carries no back-side component at all -- it is a sealed
         acoustic cavity.
    MK5  BATTERY_SHADOW carries no through-hole lead.  A clipped lead against
         a LiPo pouch is a puncture risk, which is why the register writes the
         rule in those words.
    MK6  BOSS2's Ø4.500 mm keep-out lies WHOLLY INSIDE the opaque IR_BARRIER
         that D-226 widened 3.0 -> 5.0 mm specifically to carry it, and clear
         of both optical windows.
    MK7  NOT VACUOUS.  Synthetic perturbations of the board -- a boss nudged,
         a rib region slid onto a part, a lead planted in the battery volume,
         a declaration removed, a trim that does not meet its own allowance --
         must each be caught by the clause that owns them, and moving `J4`
         clear of `DISPLAY_SHADOW` must make MK10's finding DISAPPEAR, so the
         clause is measuring membership rather than asserting a reference.
    MK10 A THROUGH-HOLE LEAD PROTRUDES ON THE FACE ITS BODY IS NOT ON, AND
         THAT FACE MAY BE HEIGHT-LIMITED.  `MK5` asks this question for
         `BATTERY_SHADOW` ONLY, because the register writes the words there
         and nowhere else.  `MK8` measures COMPONENT bodies, and a component
         on `B.Cu` is not an `F.Cu` component -- so between them the two
         clauses left `J4` unexamined for the whole programme.

         `J4` is now the D-781 MANUAL 26-AWG battery-pigtail land, not a fitted
         JST header.  The wire enters from `B.Cu`, is soldered on `F.Cu`, and
         both joints are inside `DISPLAY_SHADOW`, whose allowance is **0.80 mm**.
         J4-T1 therefore defines the finished conductive profile as **<=0.50 mm**
         and J4-T3 adds **<=0.10 mm** polyimide, leaving 0.20 mm geometric spare.

         So MK10 asks the opposite-face question for EVERY height-limited region.
         Vendor lead lengths still apply to real fitted THT parts such as J6;
         reference-specific manual lands such as J4 must carry an explicit
         assembly profile and normative declaration.  Missing either is refused.


    MK11 EXTERNAL INTERFACE AUTHORITY.  D-764 found that DEVICE_SPEC still
         called BOOT and POWER positions "UNRESOLVED" even though D-242 and
         the live board agree, while the mechanical spec still carried the
         superseded 2x12 J5 drill/aperture as current in several places.  Pin
         the board-side facts that enclosure CAD and manual assembly consume:
         SW1 front-wall tool-hole datum, SW9 right-wall datum, and the current
         1x24 J5 identity/position/drill/pitch/mating-face geometry plus the
         conservative M-09 Z bound.

    MK12 THE GOVERNING TEXT SAYS WHAT THE BOARD IS (D-801 / D801-02).  The
         spec's machine-readable MK1 side, port type and acoustic face must
         equal the board's (MK1 on B.Cu, Ø1.05 mm NPTH concentric with pad 4,
         bottom port per the archived PUI Rev A drawing -> sound arrives from
         F.Cu = FRONT); the spec's IR axis figure must equal MK9's formed-axis
         measurement (13.73 mm) with barrier + ±10° cone + C-IR-01 stated as
         the acceptance; the antenna<->IR 15 mm c-c / 8 mm edge rules must
         still be stated; and no governing mechanical / assembly document may
         state a wrong mic direction or the D-162 15 mm TX<->RX figure as
         CURRENT.  Its destructive controls run inside MK7.

    python3 hardware/demo/manufacturing/checks/mechanical_keepout_contract.py \
        [--board B.kicad_pcb] [-o REPORT.json]
"""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"

import pcbnew  # noqa: E402

# ---------------------------------------------------------------------------
# THE REGISTER, ON THE DATUM THE BOARD IS ACTUALLY BUILT ON.
#
# `FBV2_P1_KEEPOUTS.md` section 1 is written on the PRE-REBASE 70.000 mm board.
# Its own header (FBV2-EXP-002) says the board grew SYMMETRICALLY to 72.000 mm
# and that "every X coordinate below gains +1.0 mm", and restates by hand the
# handful of regions that changed by more than the shift.  Every coordinate in
# this file is the RE-BASED one, and MK1 proves that is the right choice
# against the board rather than asserting it.
#
# Doc datum: origin at the lower-left board corner, Y up.  Y_kicad = 148 - Y_doc.
REBASE_X = 1.000
BOARD_H = 148.000

# D-763.  Vendor LEAD LENGTH below the seating plane, per footprint identity --
# the figure that decides how far a through-hole part protrudes through the
# board.  `no_lead` is a positive declaration, not an absence: a mounting boss
# is a hole, a locating peg is moulded plastic that does not pass through, and
# a via-in-thermal-land is not a lead.  MK10 refuses a through-hole footprint
# inside a height-limited region that has neither a figure nor a declaration.
THT_LEAD_MM = {
    "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical":
        (3.4, "vendor", "JST ePH, Header (Through-hole type), top entry, "
                        "2 circuits: body 6.0 mm, lead (3.4) mm below the "
                        "seating plane; this applies to fitted J6, NOT D-781 J4"),
    # Lead-formed 90 degrees at assembly under assembly/IR_LEAD_FORMING.md,
    # which is NORMATIVE and specifies the trim; the unformed lead length is
    # not what reaches the board.
    "LED_D5.0mm": (0.0, "assembly", "TSAL6100 lead-formed 90 deg and trimmed, "
                                    "assembly/IR_LEAD_FORMING.md"),
    "Vishay_TSOP382xx_Minicast_3Pin_P2.54mm":
        (0.0, "assembly", "TSOP38238 lead-formed 90 deg and trimmed, "
                          "assembly/IR_LEAD_FORMING.md"),
    "Samtec_SSQ-124-02-G-S-RA":
        (2.54, "vendor", "Samtec SSW/SSQ .100 in series, RIGHT-ANGLE lead "
                         "style -02: tail B = (2.54) .100 in"),
    "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal":
        (0.0, "no_lead", "the PTH entries are SHELL ground tabs and NPTH "
                         "locating pins of a TOP-MOUNT receptacle: neither "
                         "passes a lead through the board"),
    "ESP32-S3-WROOM-1":
        (0.0, "no_lead", "the PTH entries on pad 41 are THERMAL VIAS inside "
                         "the module's own thermal land, not leads"),
    "MountingBoss_M2_NPTH": (0.0, "no_lead", "an M2 NPTH is a hole"),
    "SW_SPDT_CK_JS102011SAQN":
        (0.0, "no_lead", "the two NPTH entries are moulded locating pegs on "
                         "an SMD switch; the terminals are surface-mount"),
    "PUI_DMM-4026-B-I2S_4.0x3.0mm":
        (0.0, "no_lead", "the NPTH entry is the microphone's acoustic port"),
}

# D-781. J4 reuses the existing plated-hole pair as a MANUAL WIRE LAND.  There
# is no connector seating plane and therefore no vendor "lead length" to subtract
# from board thickness.  Its opposite-face geometry is an ASSEMBLY requirement:
# after soldering from F.Cu, each conductor is trimmed to <=0.50 mm and insulated.
# Keep this reference-specific so J6 can continue using the real JST header row.
MANUAL_THT_PROTRUSION_MM = {
    "J4": (0.50, "assembly",
           "D-781 manual 26-AWG battery-pigtail conductor; J4-T1 requires "
           "the post-solder conductive profile <=0.50 mm above F.Cu"),
}


def board_thickness_mm(path):
    """The board's OWN stackup total, not a constant.

    D-760 and D-761 were both a retained figure that had stopped being true.
    A lead protrusion is (lead - board), so reading the thickness from
    anywhere but the board would put this clause in the same family.
    """
    import re
    src = Path(path).read_text(encoding="utf-8")
    i = src.index("(stackup")
    depth = 0
    for j in range(i - 1, len(src)):
        if src[j] == "(":
            depth += 1
        elif src[j] == ")":
            depth -= 1
            if depth == 0:
                break
    blk = src[i - 1:j + 1]
    total, k = 0.0, 0
    while True:
        k = blk.find('(layer "', k + 1)
        if k < 0:
            break
        d2 = 0
        for j2 in range(k - 1, len(blk)):
            if blk[j2] == "(":
                d2 += 1
            elif blk[j2] == ")":
                d2 -= 1
                if d2 == 0:
                    break
        m = re.search(r"\(thickness ([\d.]+)\)", blk[k - 1:j2 + 1])
        if m:
            total += float(m.group(1))
    return round(total, 4)


def doc_box(x0, x1, dy0, dy1):
    """(x0, x1, kicad_y0, kicad_y1) from a doc-datum rectangle."""
    return (x0, x1, BOARD_H - dy1, BOARD_H - dy0)


# section-1 rectangles, BEFORE the re-base -- MK1 needs both forms
SECTION1 = {
    "IR_RX_OPTICAL": (61.50, 70.00, 140.00, 148.00),
    "IR_TX_OPTICAL": (48.00, 56.50, 140.00, 148.00),
    "USB_APERTURE": (36.00, 48.00, -3.50, 1.20),
    "MIC_ACOUSTIC": (0.50, 5.50, 46.50, 53.50),
}
# the four parts whose window is their own reason for existing
DATUM_PARTS = {"IR_RX_OPTICAL": "U6", "IR_TX_OPTICAL": "D1",
               "USB_APERTURE": "J3", "MIC_ACOUSTIC": "MK1"}

# regions the RE-BASE header RESTATES by hand rather than shifting
RESTATED = {
    "BATTERY_SHADOW": (7.00, 64.00, 23.50, 98.50),
    "IR_BARRIER": (57.50, 62.50, 140.00, 148.00),
}
# regions that simply take the +1.000 mm
SHIFTED = {
    "SPEAKER_ZONE": (48.00, 68.00, 1.00, 21.00),
    "DISPLAY_SHADOW": (3.39, 59.93, 55.04, 140.00),
    "RIB_R1": (66.20, 69.70, 24.00, 44.00),
    "RIB_R3": (66.20, 69.70, 76.00, 97.00),
    "RIB_B1": (44.00, 47.60, 21.20, 23.30),
}
# D-759.  RIB_R2 as registered -- X 66.20..69.70 (67.20..70.70 re-based),
# doc Y 45..64 -- is NO LONGER COMPONENT-FREE: D-719 re-floorplanned the
# TPS63020 block into it and C28, C31, R39, R40 and U12 are inside.  The rib is
# RETIRED and replaced by RIB_R2A, the largest clear rear window that still
# backs the A/B control row: its doc-Y top edge stands 1.000 mm from the row,
# against the 5.500 mm the retired rib's centre stood from it.
REBASED_DIRECT = {
    "RIB_R2A": (65.500, 69.000, 36.000, 48.000),
}
RIBS = ("RIB_R1", "RIB_R2A", "RIB_R3", "RIB_B1")

# M2 retention: hole doc position, keep-out rectangle, required keep-out
# diameter.  The diameter is the footprint's own: "the moulded boss OD is
# 4.0 mm, so the reserved component-and-copper keep-out is Ø4.5 mm".
BOSSES = {
    "BOSS1": dict(hole=(41.000, 12.000), keepout=(38.75, 43.25, 9.75, 14.25)),
    "BOSS2": dict(hole=(60.000, 145.000), keepout=(57.75, 62.25, 142.75, 147.25)),
}
BOSS_DIA = 4.500


def regions():
    out = {}
    for n, v in RESTATED.items():
        out[n] = doc_box(*v)
    for n, (x0, x1, d0, d1) in SHIFTED.items():
        out[n] = doc_box(x0 + REBASE_X, x1 + REBASE_X, d0, d1)
    for n, v in REBASED_DIRECT.items():
        out[n] = doc_box(*v)
    for n, (x0, x1, d0, d1) in SECTION1.items():
        out[n] = doc_box(x0 + REBASE_X, x1 + REBASE_X, d0, d1)
    return out


def sha256(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def body_box(f):
    """The part's own extent: its courtyard when it has one, else pads+shapes."""
    c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    bb = c.BBox() if (c and c.OutlineCount()) else f.GetBoundingBox(False, False)
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
            bb.GetRight() / 1e6, bb.GetBottom() / 1e6)


def inside(bb, box):
    x0, x1, y0, y1 = box
    return bb[0] >= x0 - 1e-6 and bb[2] <= x1 + 1e-6 and \
        bb[1] >= y0 - 1e-6 and bb[3] <= y1 + 1e-6


def overlaps(bb, box):
    x0, x1, y0, y1 = box
    return not (bb[2] < x0 or bb[0] > x1 or bb[3] < y0 or bb[1] > y1)


def mk1(board):
    reg = regions()
    rows, fits_section1 = [], []
    for name, ref in DATUM_PARTS.items():
        f = board.FindFootprintByReference(ref)
        if f is None:
            rows.append(dict(region=name, part=ref, present=False))
            continue
        bb = body_box(f)
        s1 = doc_box(*SECTION1[name])
        # THE RE-BASE IS AN X SHIFT, so the datum question is an X question.
        # These windows are enclosure APERTURES: a part may stand proud of one
        # in Y -- J3's body reaches inboard of the wall it mates through -- and
        # that says nothing about which datum the board is on.
        def fits_x(box):
            return bb[0] >= box[0] - 1e-6 and bb[2] <= box[1] + 1e-6
        rows.append(dict(region=name, part=ref, present=True,
                         part_x_mm=[round(bb[0], 3), round(bb[2], 3)],
                         rebased_window_x_mm=[reg[name][0], reg[name][1]],
                         section1_window_x_mm=[s1[0], s1[1]],
                         fits_rebased=fits_x(reg[name]),
                         fits_section1=fits_x(s1)))
        fits_section1.append(fits_x(s1))
    ok = (all(r.get("fits_rebased") for r in rows) and not all(fits_section1))
    return dict(ok=ok, rebase_mm=REBASE_X, parts=rows,
                every_datum_part_fits_the_rebased_window=all(
                    r.get("fits_rebased") for r in rows),
                at_least_one_does_not_fit_section_1=not all(fits_section1))


def mk2(board):
    rows, ok = [], True
    for ref, spec in BOSSES.items():
        f = board.FindFootprintByReference(ref)
        if f is None:
            rows.append(dict(ref=ref, present=False))
            ok = False
            continue
        pos = f.GetPosition()
        hole = (pos.x / 1e6, round(BOARD_H - pos.y / 1e6, 4))
        z = next((z for z in board.Zones()
                  if z.GetZoneName() == ref + "_KEEPOUT"), None)
        row = dict(ref=ref, present=True, hole_doc_mm=[hole[0], hole[1]],
                   register_hole_doc_mm=list(spec["hole"]),
                   hole_as_registered=(abs(hole[0] - spec["hole"][0]) < 1e-4
                                       and abs(hole[1] - spec["hole"][1]) < 1e-4),
                   keepout_present=z is not None)
        if z is not None:
            o = z.Outline().Outline(0)
            xs = [o.CPoint(i).x / 1e6 for i in range(o.PointCount())]
            ys = [o.CPoint(i).y / 1e6 for i in range(o.PointCount())]
            kx0, kx1, kd0, kd1 = spec["keepout"]
            row["keepout_x_mm"] = [round(min(xs), 4), round(max(xs), 4)]
            row["keepout_doc_y_mm"] = [round(BOARD_H - max(ys), 4),
                                       round(BOARD_H - min(ys), 4)]
            row["keepout_as_registered"] = (
                abs(min(xs) - kx0) < 1e-4 and abs(max(xs) - kx1) < 1e-4
                and abs((BOARD_H - max(ys)) - kd0) < 1e-4
                and abs((BOARD_H - min(ys)) - kd1) < 1e-4)
            inr = min(pcbnew.SEG(o.CPoint(i), o.CPoint((i + 1) % o.PointCount()))
                      .Distance(pos) / 1e6 for i in range(o.PointCount()))
            row["keepout_inradius_about_the_hole_mm"] = round(inr, 4)
            row["covers_the_required_diameter"] = inr >= BOSS_DIA / 2 - 1e-6
        r = BOSS_DIA / 2
        cu = []
        for t in board.GetTracks():
            d = ((t.GetPosition() - pos).EuclideanNorm() / 1e6
                 - t.GetWidth(pcbnew.F_Cu) / 2e6) if isinstance(t, pcbnew.PCB_VIA) \
                else (pcbnew.SEG(t.GetStart(), t.GetEnd()).Distance(pos) / 1e6
                      - t.GetWidth() / 2e6)
            if d < r:
                cu.append([round(d, 4), t.GetNetname()])
        po = []
        for z2 in board.Zones():
            if z2.GetIsRuleArea():
                continue
            for lay in z2.GetLayerSet().CuStack():
                fz = z2.GetFilledPolysList(lay)
                if fz and fz.OutlineCount() and fz.Distance(pos) / 1e6 < r:
                    po.append([round(fz.Distance(pos) / 1e6, 4),
                               pcbnew.LayerName(lay), z2.GetNetname()])
        pa = []
        for g in board.GetFootprints():
            if g.GetReference() == ref:
                continue
            c = g.GetCourtyard(pcbnew.B_CrtYd if g.IsFlipped() else pcbnew.F_CrtYd)
            if c and c.OutlineCount() and c.Distance(pos) / 1e6 < r:
                pa.append(g.GetReference())
        row.update(copper_inside_the_circle=sorted(cu),
                   pour_inside_the_circle=sorted(po),
                   components_inside_the_circle=sorted(pa))
        row["ok"] = bool(row.get("hole_as_registered")
                         and row.get("keepout_as_registered")
                         and row.get("covers_the_required_diameter")
                         and not cu and not po and not pa)
        ok = ok and row["ok"]
        rows.append(row)
    return dict(ok=ok, required_keepout_diameter_mm=BOSS_DIA, bosses=rows)


def _back_side_occupants(board, box):
    return sorted(f.GetReference() for f in board.GetFootprints()
                  if f.IsFlipped() and overlaps(body_box(f), box))


def mk3(board, reg=None):
    reg = reg or regions()
    rows = {r: _back_side_occupants(board, reg[r]) for r in RIBS}
    return dict(ok=not any(rows.values()), ribs=rows,
                retired=dict(RIB_R2="D-759: the D-719 TPS63020 re-floorplan "
                                    "occupies it; replaced by RIB_R2A"))


def mk4(board, reg=None):
    reg = reg or regions()
    occ = _back_side_occupants(board, reg["SPEAKER_ZONE"])
    return dict(ok=not occ, back_side_occupants=occ)


def mk5(board, reg=None):
    reg = reg or regions()
    x0, x1, y0, y1 = reg["BATTERY_SHADOW"]
    leads = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() not in (pcbnew.PAD_ATTRIB_PTH,
                                        pcbnew.PAD_ATTRIB_NPTH):
                continue
            q = p.GetPosition()
            if x0 <= q.x / 1e6 <= x1 and y0 <= q.y / 1e6 <= y1:
                leads.append("%s.%s" % (f.GetReference(), p.GetNumber()))
    return dict(ok=not leads, through_hole_leads_inside=sorted(leads),
                region_mm=[round(v, 3) for v in (x0, x1, y0, y1)])


def mk6(board, reg=None):
    reg = reg or regions()
    f = board.FindFootprintByReference("BOSS2")
    x = f.GetPosition().x / 1e6
    lo, hi = x - BOSS_DIA / 2, x + BOSS_DIA / 2
    bar = reg["IR_BARRIER"]
    rx, tx = reg["IR_RX_OPTICAL"], reg["IR_TX_OPTICAL"]
    return dict(ok=(lo >= bar[0] - 1e-6 and hi <= bar[1] + 1e-6),
                boss2_keepout_x_mm=[round(lo, 3), round(hi, 3)],
                ir_barrier_x_mm=[bar[0], bar[1]],
                into_ir_rx_optical_mm=round(max(0.0, hi - rx[0]), 4),
                into_ir_tx_optical_mm=round(max(0.0, tx[1] - lo), 4))



# ---------------------------------------------------------------------------
# D-760.  THE THREE HEIGHT RULES, WHICH NOTHING HAS EVER CHECKED.
#
# `FBV2_P1_KEEPOUTS.md` section 3 carries three of them -- `DISPLAY_SHADOW`
# F.Cu <= 0.8 mm, `BATTERY_SHADOW` B.Cu <= 1.2 mm, `NFC_CLEAR_D48` B.Cu <=
# 1.0 mm -- and names the first two "measured Beta-DM limit, retained".  A
# retained heuristic is not a stack calculation, and no gate has ever compared
# either of them with a part.
#
# MAX_HEIGHT_MM is a package-to-height table.  `src` records WHERE each figure
# comes from, because the difference matters: the generic SOT-23 maximum is
# 1.45 mm and TI's own DDC0006A outline says "SOT-23 - 1.1 max height", so
# reading the family instead of the part would have reported `U20` over a limit
# it meets.  `vendor` rows are from the manufacturer's own document; `eia` rows
# are the worst-case chip maximum for that case code across common dielectric
# builds, which is the conservative direction.
MAX_HEIGHT_MM = {
    # passives, by case code -- RESISTORS and CAPACITORS are NOT the same part
    "R_0402_1005Metric": (0.45, "eia", "thick-film chip resistor, 0402"),
    "R_0603_1608Metric": (0.55, "eia", "thick-film chip resistor, 0603"),
    "R_0805_2012Metric": (0.65, "eia", "thick-film chip resistor, 0805"),
    "R_1206_3216Metric": (0.75, "eia", "thick-film chip resistor, 1206"),
    "C_0402_1005Metric": (0.55, "eia", "MLCC, 0402"),
    "C_0603_1608Metric": (0.90, "eia", "MLCC, 0603, high-capacitance build"),
    "C_0805_2012Metric": (1.25, "eia", "MLCC, 0805, high-capacitance build"),
    # D-789 / D788-19: this row no longer names a manufacturer, because it is
    # applied to whatever 1206 capacitor happens to be fitted.  The PURCHASED
    # part's own figure is in MAX_HEIGHT_BY_MPN below and takes precedence.
    "C_1206_3216Metric": (1.90, "eia",
                          "MLCC, 1206, high-capacitance build -- the worst "
                          "case across common 1206 thickness codes, used only "
                          "when the fitted MPN has no published figure"),
    # D-789 / D788-19: the generic 1210 row was 2.00 mm, which no
    # high-capacitance 1210 build actually meets -- Samsung's own 1210
    # thickness table runs to 2.50 +/- 0.30.  A family fallback must be the
    # WORST case of the family, not a typical one.
    "C_1210_3225Metric": (2.80, "eia",
                          "MLCC, 1210, worst-case high-capacitance build "
                          "(thickness code V, 2.50 +/- 0.30 mm, from "
                          "Samsung's published 1210 thickness table); used "
                          "only when the fitted MPN has no published figure"),
    "L_0603_1608Metric": (0.95, "eia", "chip inductor / ferrite bead, 0603"),
    "TestPoint_Pad_D1.0mm": (0.00, "geometry", "a bare copper pad has no body"),
    # discretes
    "D_SOD-323": (1.10, "eia", "SOD-323 / SC-76 maximum"),
    "D_SOD-123": (1.35, "eia", "SOD-123 maximum"),
    "SOT-23": (1.12, "vendor", "Alpha & Omega AO3400A SOT-23: A max 1.12 mm"),
    "SOT-23-6": (1.10, "vendor", "TI DDC0006A package outline: SOT-23 - 1.1 max height"),
    "SOT-563": (0.60, "eia", "SOT-563 maximum"),
    "SOT-353_SC-70-5": (1.10, "eia", "SC-70 maximum"),
    "SOT-23-8": (1.45, "eia", "SOT-23-8 maximum"),
    "SOIC-8_3.9x4.9mm_P1.27mm": (1.75, "eia", "JEDEC MS-012 SOIC-8 maximum"),
    # ICs
    "TSSOP-24_4.4x7.8mm_P0.65mm": (1.20, "eia", "JEDEC MO-153 TSSOP maximum"),
    "VSSOP-8_3x3mm_P0.65mm": (1.10, "eia", "TI DGK / JEDEC MO-187 maximum"),
    "MSOP-10_3x3mm_P0.5mm": (1.10, "eia", "JEDEC MO-187 MSOP maximum"),
    "Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270": (0.83, "vendor", "Bosch BMI270 LGA-14: 0.83 mm max"),
    "ST25R3916_AQET": (0.60, "eia", "UFQFPN-32 maximum"),
    "MAX17048_T822": (0.65, "eia", "TDFN-8 maximum"),
    "Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm":
        (0.80, "eia", "WSON-10 maximum"),
    # connectors and crystals
    "JST_ACH_BM02B-ACHSS-GAN-ETF_1x02-1MP_P1.20mm_Vertical":
        (1.40, "vendor", "JST eACH: low-profile type, height 1.4 mm, width 4.3 mm"),
    "Crystal_SMD_3225-4Pin_3.2x2.5mm": (0.80, "eia", "3225 4-pad SMD crystal maximum"),
    # D1 is a T-1 3/4 through-hole emitter that assembly LEAD-FORMS 90 degrees
    # so its 8.7 mm body lies flat and fires out of the TOP panel
    # (docs/full-beta-v2/assembly/IR_LEAD_FORMING.md, NORMATIVE).  Its body
    # therefore leaves DISPLAY_SHADOW entirely; what stands inside the region is
    # nothing, and its pads are north of the region's own edge, which is why
    # membership below is decided by PADS and not by an unformed courtyard.
    "LED_D5.0mm": (5.95, "vendor", "Vishay TSAL6100 doc 81009: package "
                                   "dia 5.8 +/- 0.15 mm, lead-formed 90 deg"),
    "Vishay_TSOP382xx_Minicast_3Pin_P2.54mm":
        (6.95, "vendor", "Vishay doc 82491: minicast 5.0 W x 6.95 H x 4.8 D mm, "
                         "lead-formed 90 deg"),
}

# --------------------------------------------------------------------------
# D-789 / D788-19 -- A FOOTPRINT IS NOT A PART, AND THE CENSUS WAS PRICING
# FOUR CAPACITORS AGAINST ANOTHER MANUFACTURER'S DATASHEET.
#
# `MAX_HEIGHT_MM` is keyed by FOOTPRINT, and its `C_1206_3216Metric` row read
# 1.80 mm on the basis "Murata GRM31C 1206: T = 1.6 +/- 0.2 mm".  `C26` and
# `C27` ARE Murata `GRM31CR71E106KA12L`.  `C29`, `C30`, `C31` and `C32` are
# CCTC `TCC1206X7R226K160HT`, and nothing in this file had ever looked.
#
# CCTC's own document (DRAAW108N/0, archived `vendor/CCTC/`) prints TWO 1206
# dimension rows: T = 1.60 +/- 0.20 and, marked `*1` for "1uF and above", T =
# 1.60 +/- 0.30.  These parts are 22 uF, so the applicable MAXIMUM is 1.90 mm
# and not 1.80 mm.  `C29` and `C30` stand inside `BATTERY_SHADOW`, whose
# measured-profile allowance had been set at 1.80 mm BECAUSE this table said
# they were 1.80 mm -- a ceiling derived from its own error.
#
# So the census is MPN-FIRST now.  The MPN is read from the schematic, the
# figure comes from the purchased part's own document, and a part inside a
# height-limited region that falls back to a family row is REPORTED as such --
# a fallback is not wrong, but it must be visible.
MAX_HEIGHT_BY_MPN = {
    "TCC1206X7R226K160HT": (
        1.90, "vendor",
        "CCTC DRAAW108N/0 section 5 Dimensions, the 1206 row marked *1 "
        "('1uF and above'): T = 1.60 +/- 0.30 mm.  Thickness code H = 1.60 mm "
        "from the same document's ordering table.  Archived at "
        "vendor/CCTC/cctc-mlcc-DRAAW108N-0.pdf with its source record."),
    "GRM31CR71E106KA12L": (
        1.80, "vendor", "Murata GRM31C 1206: T = 1.6 +/- 0.2 mm"),
    "CL32B226KAJNNNE": (
        2.70, "vendor",
        "Samsung MLCC CL series catalogue, archived at "
        "vendor/SAMSUNG/samsung-mlcc-CL-series.pdf.  The part number's "
        "eleventh character is the THICKNESS CODE: CL-32-B-226-K-A-**J**-NNNE, "
        "and the 1210(3225) thickness table gives J = 2.50 mm +/- 0.20, so the "
        "MAXIMUM is 2.70 mm -- 0.70 mm more than the generic 1210 family row "
        "this census used to apply to it.  C12 is not inside a height-limited "
        "region, so no verdict moves; the figure is corrected because the "
        "next 1210 might be."),
}


def mpn_by_reference():
    """{REF: MPN} from the schematic sheets, for the height census."""
    import re as _re
    out = {}
    for sheet in sorted(PROJECT.glob("*.kicad_sch")):
        text = sheet.read_text(encoding="utf-8", errors="replace")
        for m in _re.finditer(r'\(property "Reference" "([^"]+)"', text):
            ref = m.group(1)
            tail = text[m.end():m.end() + 6000]
            nxt = tail.find('(property "Reference"')
            if nxt > 0:
                tail = tail[:nxt]
            n = _re.search(r'\(property "MPN" "([^"]*)"', tail)
            if n and n.group(1):
                out.setdefault(ref, n.group(1))
    return out


# The region allowances MK8 enforces, and the rule each one is measured
# against.  `allowance_mm` is a NO-REGRESSION CEILING set at the board's own
# measured profile -- the board may not get taller here without a decision --
# and `register_limit_mm` is the inherited rule the register still states.
# Where the two differ the gap is REPORTED, not hidden: it is an open CAD item
# and closing it is a stack calculation nobody on this repository can do
# without the enclosure.
HEIGHT_REGIONS = {
    "DISPLAY_SHADOW": dict(side="F", register_limit_mm=0.80, allowance_mm=0.80),
    # D-789 / D788-19: 1.80 -> 1.90 mm.  THIS IS A CORRECTED MEASUREMENT, NOT
    # A TALLER BOARD.  The allowance is defined as the board's own measured
    # profile, and it had been set at 1.80 mm because this file priced C29 and
    # C30 -- CCTC TCC1206X7R226K160HT, 22 uF -- against MURATA's GRM31C
    # dimensions.  CCTC's own document gives T = 1.60 +/- 0.30 for 1206 parts
    # of 1 uF and above, so those two capacitors have always been 1.90 mm and
    # the ceiling was derived from the census's own error.  Not one component
    # moved and no part changed.  What DID change is the size of the open CAD
    # item: the B-side profile under the pouch is 1.90 mm against a register
    # limit of 1.20 mm, a 0.70 mm gap rather than 0.60 mm, and closing it is
    # still a stack calculation that needs the enclosure.
    "BATTERY_SHADOW": dict(side="B", register_limit_mm=1.20, allowance_mm=1.90,
                           allowance_basis=(
                               "measured profile, D-789 / D788-19: C29/C30 "
                               "CCTC TCC1206X7R226K160HT at 1.90 mm max "
                               "(T = 1.60 +/- 0.30, the *1 '1uF and above' "
                               "1206 row of CCTC DRAAW108N/0)")),
    "NFC_CLEAR_D48": dict(side="B", register_limit_mm=1.00, allowance_mm=1.40),
}
NFC_CLEAR_CENTRE_DOC = (31.800, 124.500)
NFC_CLEAR_R = 24.000


def mk8(board, reg=None):
    """Every part in a height-limited region, against its package maximum."""
    reg = reg or regions()
    dnp = set()
    for f in board.GetFootprints():
        try:
            if f.IsDNP():
                dnp.add(f.GetReference())
        except Exception:
            pass
    out, ok, unknown = {}, True, set()
    mpns = mpn_by_reference()
    for name, spec in HEIGHT_REGIONS.items():
        side = spec["side"]
        parts = []
        for f in board.GetFootprints():
            if (f.IsFlipped() and side != "B") or (not f.IsFlipped() and side != "F"):
                continue
            if f.GetReference() in dnp:
                continue
            if name == "NFC_CLEAR_D48":
                cx, cy = NFC_CLEAR_CENTRE_DOC[0], BOARD_H - NFC_CLEAR_CENTRE_DOC[1]
                if not any(math.hypot(q.GetPosition().x / 1e6 - cx,
                                      q.GetPosition().y / 1e6 - cy) <= NFC_CLEAR_R
                           for q in f.Pads()):
                    continue
            else:
                # MEMBERSHIP IS BY PADS, not by courtyard.  A component's mass
                # stands over its own lands, and `D1` and `U6` are LEAD-FORMED
                # 90 degrees at assembly so their bodies end up nowhere near
                # the circle their unformed courtyards draw.
                x0, x1, y0, y1 = reg[name]
                if not any(x0 <= q.GetPosition().x / 1e6 <= x1
                           and y0 <= q.GetPosition().y / 1e6 <= y1
                           for q in f.Pads()):
                    continue
            fid = f.GetFPIDAsString().split(":")[-1]
            ref = f.GetReference()
            # D-789 / D788-19: THE PURCHASED PART FIRST.
            mpn = mpns.get(ref)
            h = MAX_HEIGHT_BY_MPN.get(mpn) if mpn else None
            keyed_by = "mpn" if h else "footprint"
            if h is None:
                h = MAX_HEIGHT_MM.get(fid)
            if h is None:
                unknown.add(fid)
                parts.append(dict(ref=ref, footprint=fid, mpn=mpn,
                                  keyed_by=None,
                                  max_height_mm=None, source=None))
                continue
            parts.append(dict(ref=ref, footprint=fid, mpn=mpn,
                              keyed_by=keyed_by,
                              max_height_mm=h[0], source=h[1], basis=h[2]))
        known = [p for p in parts if p["max_height_mm"] is not None]
        tallest = max((p["max_height_mm"] for p in known), default=0.0)
        over_allowance = sorted(p["ref"] for p in known
                                if p["max_height_mm"] > spec["allowance_mm"] + 1e-9)
        over_register = sorted(p["ref"] for p in known
                               if p["max_height_mm"] > spec["register_limit_mm"] + 1e-9)
        clause_ok = (not over_allowance
                     and not any(p["max_height_mm"] is None for p in parts))
        ok = ok and clause_ok
        out[name] = dict(ok=clause_ok, side=side,
                         register_limit_mm=spec["register_limit_mm"],
                         allowance_mm=spec["allowance_mm"],
                         allowance_basis=spec.get("allowance_basis"),
                         measured_tallest_mm=round(tallest, 3),
                         parts_over_the_allowance=over_allowance,
                         parts_over_the_register_limit=over_register,
                         open_cad_gap_mm=round(max(0.0, tallest - spec["register_limit_mm"]), 3),
                         # D-789 / D788-19: which figures came from the
                         # PURCHASED part and which fell back to a family row.
                         priced_by_purchased_mpn=sorted(
                             p["ref"] for p in parts if p.get("keyed_by") == "mpn"),
                         priced_by_footprint_family=sorted(
                             p["ref"] for p in parts
                             if p.get("keyed_by") == "footprint"),
                         parts=sorted(parts, key=lambda p: (-(p["max_height_mm"] or 0),
                                                            p["ref"])))
    return dict(ok=ok, regions=out,
                footprints_with_no_height_figure=sorted(unknown),
                priced_by_purchased_mpn=sorted(MAX_HEIGHT_BY_MPN),
                note="allowance_mm is a no-regression ceiling at the board's own "
                     "measured profile; register_limit_mm is the inherited rule "
                     "and the gap between them is an OPEN CAD ITEM (D-760).  "
                     "D-789 / D788-19: every part's figure is taken from its "
                     "PURCHASED MPN where this repository has read one, and "
                     "`priced_by_footprint_family` names every part still "
                     "priced by its package rather than by its part.")



# D-761.  THE IR PAIR, WHICH IS A FUNCTIONAL RULE WITH 0.133 mm OF MARGIN.
#
# `FBV2_P1_KEEPOUTS.md` §4 cites "the >= 15 mm IR TX<->RX rule" as the reason
# `D1` cannot move, and `D-226` widened `IR_BARRIER` 3.0 -> 5.0 mm to stand
# between them.  Neither statement was checked by anything.  The pair measures
# 15.1327 mm centre to centre -- the rule is MET, and by 0.133 mm, which is
# exactly the kind of margin that a 0.2 mm placement nudge spends without
# anybody noticing.
#
# SUPERSEDED D-800 / D-801.  That 15.1327 mm was footprint ORIGINS; the formed
# optical axes are 13.73 mm apart (MK9).  The figure survives only so MK9 can
# REPORT the historical heuristic as unmet; MK12 refuses any governing document
# that states it as a current TX<->RX requirement.
IR_TX_RX_MIN_MM = 15.000



# ---------------------------------------------------------------------------
# D-763.  THE LEAD THAT PROTRUDES ON THE OTHER FACE.
#
# MK5 asks this for BATTERY_SHADOW because the register writes the words there.
# MK8 measures COMPONENT bodies and filters by face.  `J4` -- the battery
# connector, the ONLY through-hole part on this board with its body on B.Cu --
# is invisible to both: its leads stand 3.4 - 1.5744 = 1.826 mm proud of F.Cu
# and both its pads are inside DISPLAY_SHADOW, whose allowance is 0.80 mm.
TRIM_DOC = ROOT / "docs/full-beta-v2/assembly/THT_LEAD_TRIM.md"

# A protrusion over a region's allowance must be DECLARED here AND carried by
# the normative assembly document, with a trim that meets the allowance.
DECLARED_LEAD_TRIM = {
    ("J4", "DISPLAY_SHADOW"): dict(
        requirement="J4-T1", trim_to_mm=0.50,
        insulation_requirement="J4-T3", insulation="polyimide",
        insulation_max_mm=0.10,
        doc="docs/full-beta-v2/assembly/THT_LEAD_TRIM.md"),
}


def mk10(board, reg=None, board_path=None):
    """Through-hole leads against the allowance of the face they emerge on."""
    reg = reg or regions()
    thick = board_thickness_mm(board_path or BOARD)
    dnp = set()
    for f in board.GetFootprints():
        try:
            if f.IsDNP():
                dnp.add(f.GetReference())
        except Exception:
            pass
    findings, unknown, undeclared, bad_trim = [], [], [], []
    doc = TRIM_DOC.read_text(encoding="utf-8") if TRIM_DOC.is_file() else ""
    for name, spec in HEIGHT_REGIONS.items():
        side = spec["side"]
        for f in board.GetFootprints():
            if f.GetReference() in dnp:
                continue
            tht = [q for q in f.Pads()
                   if q.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,
                                           pcbnew.PAD_ATTRIB_NPTH)]
            if not tht:
                continue
            body = "B" if f.IsFlipped() else "F"
            # A body ON the region's face is a COMPONENT; MK8 owns it.  This
            # clause owns the LEAD, which emerges on the OTHER face.
            if body == side:
                continue
            if name == "NFC_CLEAR_D48":
                cx, cy = NFC_CLEAR_CENTRE_DOC[0], BOARD_H - NFC_CLEAR_CENTRE_DOC[1]
                inside = [q for q in tht
                          if math.hypot(q.GetPosition().x / 1e6 - cx,
                                        q.GetPosition().y / 1e6 - cy)
                          <= NFC_CLEAR_R]
            else:
                x0, x1, y0, y1 = reg[name]
                inside = [q for q in tht
                          if x0 <= q.GetPosition().x / 1e6 <= x1
                          and y0 <= q.GetPosition().y / 1e6 <= y1]
            if not inside:
                continue
            ref = f.GetReference()
            fid = f.GetFPIDAsString().split(":")[-1]
            manual = MANUAL_THT_PROTRUSION_MM.get(ref)
            lead = manual or THT_LEAD_MM.get(fid)
            if lead is None:
                unknown.append([ref, fid, name])
                continue
            proud = round(lead[0] if manual else max(0.0, lead[0] - thick), 4)
            row = dict(ref=ref, footprint=fid, region=name, region_face=side,
                       body_face=body, pads=sorted(q.GetNumber() for q in inside),
                       lead_mm=None if manual else lead[0],
                       manual_protrusion_mm=lead[0] if manual else None,
                       lead_source=lead[1], lead_basis=lead[2],
                       board_thickness_mm=thick, protrusion_mm=proud,
                       allowance_mm=spec["allowance_mm"],
                       over_mm=round(max(0.0, proud - spec["allowance_mm"]), 4))
            d = DECLARED_LEAD_TRIM.get((ref, name))
            # A reference-specific manual profile is itself a manufacturing
            # mitigation, so its declaration/document/insulation must be proved
            # even though the finished 0.50 mm conductor is already below 0.80 mm.
            needs_declaration = bool(manual) or row["over_mm"] > 1e-9
            if needs_declaration:
                if not d:
                    undeclared.append([ref, name, row["over_mm"]])
                elif (d["trim_to_mm"] > spec["allowance_mm"] + 1e-9
                      or d["requirement"] not in doc or ref not in doc
                      or not d.get("insulation_requirement")
                      or d["insulation_requirement"] not in doc
                      or not d.get("insulation")
                      or d["insulation"].lower() not in doc.lower()
                      or d["trim_to_mm"] + d.get("insulation_max_mm", 0.0)
                         >= spec["allowance_mm"] - 1e-9):
                    bad_trim.append([ref, name, d["requirement"],
                                     d.get("insulation_requirement")])
                else:
                    row["declared"] = d
            findings.append(row)
    return dict(ok=(not unknown and not undeclared and not bad_trim),
                board_thickness_mm=thick,
                trim_doc_present=bool(doc),
                leads_in_a_limited_region=sorted(
                    findings, key=lambda r: (-r["protrusion_mm"], r["ref"])),
                through_hole_without_a_lead_figure=sorted(unknown),
                over_the_allowance_and_undeclared=sorted(undeclared),
                declared_but_the_trim_does_not_meet_the_allowance=sorted(bad_trim),
                note="a body ON the region's face is a COMPONENT and MK8 owns "
                     "it; this clause owns the LEAD, which emerges on the "
                     "OTHER face")


# D-800 (Round-19 full review).  MK9 MEASURED THE WRONG POINTS.
#
# D-759's MK9 took the distance between the two footprint ORIGINS -- D1's
# origin is its PAD 1, not its optical axis -- and included their 2 mm Y
# offset, which vanishes once both parts are lead-formed 90 degrees to look
# out of the same top panel (IR_LEAD_FORMING.md).  The formed optical axes are
# D1's lead midpoint (a T-1 3/4 dome is centred between its leads) and U6's
# centre lead, both pointing +Y: they are 13.73 mm apart, not 15.13 mm.  The
# ">= 15 mm" figure (D-162) is a heuristic carried from a +/-17 degree
# TSAL6200 and has no primary source; what it stands for is PHYSICAL and is
# what this clause now gates: (1) the opaque IR_BARRIER stands between the
# two parts' whole courtyards, and (2) the receiver is outside the emitter's
# half-intensity cone (TSAL6100 doc 81009 rev 1.8: phi = +/-10 deg) anywhere
# inside the enclosure.  The heuristic is REPORTED, unmet, and the coupling
# itself is measured at first article (C-IR-01).
IR_TX_HALF_ANGLE_DEG = 10.0        # Vishay 81009 rev 1.8, archived
IR_TX_DOME_RADIUS_MM = 2.9         # 5.8 mm flange / 2 (81009)
IR_RX_HALF_WIDTH_MM = 2.5          # TSOP382 minicast 5.0 mm wide (82491)
IR_INSIDE_ENCLOSURE_MM = 2.5       # top wall: cavity to external face


def _formed_axis_x(fp):
    xs = [q.GetPosition().x / 1e6 for q in fp.Pads()]
    return sum(xs) / len(xs)


def _courtyard_x(fp):
    bb = fp.GetCourtyard(fp.GetLayer()).BBox()
    return bb.GetLeft() / 1e6, bb.GetRight() / 1e6


def mk9(board, reg=None):
    reg = reg or regions()
    d1 = board.FindFootprintByReference("D1")
    u6 = board.FindFootprintByReference("U6")
    if d1 is None or u6 is None:
        return dict(ok=False, why="D1 or U6 missing")
    a, b2 = d1.GetPosition(), u6.GetPosition()
    origin_sep = math.hypot(a.x - b2.x, a.y - b2.y) / 1e6
    ax_d1, ax_u6 = _formed_axis_x(d1), _formed_axis_x(u6)
    sep = abs(ax_u6 - ax_d1)
    bar = reg["IR_BARRIER"]
    d1_cy, u6_cy = _courtyard_x(d1), _courtyard_x(u6)
    west, east = (d1_cy, u6_cy) if ax_d1 < ax_u6 else (u6_cy, d1_cy)
    between = west[1] <= bar[0] + 1e-6 and east[0] >= bar[1] - 1e-6
    lateral_gap = sep - IR_TX_DOME_RADIUS_MM - IR_RX_HALF_WIDTH_MM
    cone_reach = (lateral_gap / math.tan(math.radians(IR_TX_HALF_ANGLE_DEG))
                  if lateral_gap > 0 else 0.0)
    outside_cone = cone_reach > IR_INSIDE_ENCLOSURE_MM
    return dict(ok=bool(between and outside_cone),
                formed_optical_axis_x_mm=dict(D1=round(ax_d1, 3),
                                              U6=round(ax_u6, 3)),
                formed_axis_separation_mm=round(sep, 4),
                heuristic_min_mm=IR_TX_RX_MIN_MM,
                heuristic_met=bool(sep >= IR_TX_RX_MIN_MM - 1e-6),
                heuristic_shortfall_mm=round(max(0.0, IR_TX_RX_MIN_MM - sep), 4),
                footprint_origin_separation_mm_d759=round(origin_sep, 4),
                ir_barrier_x_mm=[bar[0], bar[1]],
                courtyards_x_mm=dict(D1=[round(v, 3) for v in d1_cy],
                                     U6=[round(v, 3) for v in u6_cy]),
                barrier_stands_between_the_courtyards=between,
                emitter_half_angle_deg=IR_TX_HALF_ANGLE_DEG,
                forward_distance_before_the_cone_reaches_the_receiver_mm=round(
                    cone_reach, 2),
                receiver_outside_the_emission_cone_inside_the_enclosure=
                outside_cone,
                measurement_of_record="C-IR-01 (first article, fitted "
                                      "enclosure)",
                why="D-800: the formed axes, not the footprint origins; the "
                    "15 mm heuristic is reported and the physical isolation "
                    "is gated")



# D-764. EXTERNAL INTERFACES THAT ENCLOSURE CAD CONSUMES.
# Doc datum is lower-left, +Y up.  The board is KiCad top-view coordinates.
EXTERNAL = {
    "SW1": dict(doc=(28.300, 6.000), side="F", rotation=0.0),
    "SW9": dict(doc=(66.700, 61.500), side="F", rotation=90.0),
    "J5": dict(doc=(65.900, 108.790), side="F", rotation=-90.0),
}
J5_FPID = "AQROOT_Beta:Samtec_SSQ-124-02-G-S-RA"
J5_DRILL_MM = 1.020
J5_PITCH_MM = 2.540
J5_PIN_SPAN_MM = 58.420
J5_TAIL_TO_MATING_FACE_MM = 6.530
J5_BODY_LENGTH_MM = 61.470
J5_RECESS_MM = 62.500
J5_BODY_MAX_MM = 8.510
ENCLOSURE_EXTERNAL_Z_MM = 23.000


def mk11(board):
    rows, ok = {}, True
    for ref, spec in EXTERNAL.items():
        f = board.FindFootprintByReference(ref)
        if f is None:
            rows[ref] = dict(ok=False, present=False)
            ok = False
            continue
        p = f.GetPosition()
        doc = (p.x / 1e6, BOARD_H - p.y / 1e6)
        side = "B" if f.IsFlipped() else "F"
        row = dict(present=True,
                   doc_mm=[round(doc[0], 3), round(doc[1], 3)],
                   expected_doc_mm=list(spec["doc"]), side=side,
                   expected_side=spec["side"],
                   rotation_deg=round(f.GetOrientationDegrees(), 3),
                   expected_rotation_deg=spec["rotation"])
        row["ok"] = (abs(doc[0] - spec["doc"][0]) <= 1e-4
                     and abs(doc[1] - spec["doc"][1]) <= 1e-4
                     and side == spec["side"]
                     and abs(f.GetOrientationDegrees() - spec["rotation"]) <= 1e-4)
        rows[ref] = row
        ok = ok and row["ok"]

    j5 = board.FindFootprintByReference("J5")
    geo = dict(ok=False)
    if j5 is not None:
        pads = sorted(j5.Pads(), key=lambda p: int(p.GetNumber()))
        xs = [p.GetPosition().x / 1e6 for p in pads]
        ys = [p.GetPosition().y / 1e6 for p in pads]
        drills = [p.GetDrillSize().x / 1e6 for p in pads]
        pitches = [round(ys[i + 1] - ys[i], 6) for i in range(len(ys) - 1)]
        pin_span = max(ys) - min(ys) if ys else 0.0
        row_x = sum(xs) / len(xs) if xs else 0.0
        mating_x = row_x + J5_TAIL_TO_MATING_FACE_MM
        body_y = [min(ys) - (J5_BODY_LENGTH_MM - J5_PIN_SPAN_MM) / 2.0,
                  max(ys) + (J5_BODY_LENGTH_MM - J5_PIN_SPAN_MM) / 2.0]
        z_bound = 2.0 + J5_BODY_MAX_MM + 1.6 + 8.0 + 0.6 + 2.0
        geo = dict(
            ok=(j5.GetFPIDAsString() == J5_FPID and len(pads) == 24
                and all(abs(d - J5_DRILL_MM) <= 1e-6 for d in drills)
                and all(abs(q - J5_PITCH_MM) <= 1e-6 for q in pitches)
                and abs(pin_span - J5_PIN_SPAN_MM) <= 1e-6
                and abs(mating_x - 72.430) <= 1e-6
                and z_bound <= ENCLOSURE_EXTERNAL_Z_MM + 1e-9),
            footprint=j5.GetFPIDAsString(), contacts=len(pads),
            drill_mm=sorted(set(round(d, 3) for d in drills)),
            pitch_mm=sorted(set(round(q, 3) for q in pitches)),
            pin_span_mm=round(pin_span, 3), pin_row_x_mm=round(row_x, 3),
            body_y_mm=[round(v, 3) for v in body_y],
            mating_face_x_mm=round(mating_x, 3),
            closed_end_recess_mm=J5_RECESS_MM,
            conservative_largest_body_mm=J5_BODY_MAX_MM,
            z_bound_mm=round(z_bound, 3),
            z_spare_mm=round(ENCLOSURE_EXTERNAL_Z_MM - z_bound, 3),
            note="62.5 mm is an enclosure requirement; the board-side geometry "
                 "that drives it is measured here")
        ok = ok and geo["ok"]
    return dict(ok=ok, interfaces=rows, j5=geo,
                datum="doc origin lower-left; Y_kicad = 148 - Y_doc")


# ---------------------------------------------------------------------------
# D-801 (Round-20, D801-02).  THE GOVERNING MECHANICAL TEXT MUST SAY WHAT THE
# BOARD IS.
#
# Two current requirements in the enclosure authority disagreed with the frozen
# board and no clause read them.  (1) MECHANICAL_INTERFACE_SPEC §8 still stated
# D-162's ">= 15 mm" emitter<->receiver separation as CURRENT while MK9 had
# measured the formed axes at 13.73 mm and moved the acceptance to barrier +
# cone + first-article C-IR-01.  (2) M-14 and FOOTPRINT_VERIFICATION_LEDGER
# B-63 said MK1 "sits on the TOP of the PCB" and that the acoustic path, the
# enclosure aperture and the gasket are on the BOTTOM face -- the footprint
# LIBRARY's own frame, never re-stated for the board.  D-214 put MK1 on B.Cu
# (REAR); PUI's drawing puts the Ø0.25 mm port on the PAD face inside the pad-4
# ring (bottom port); the board carries the Ø1.05 mm NPTH concentric with pad
# 4.  So the port faces the board and sound arrives from F.Cu (FRONT).
#
# MK12 reads the BOARD for the mic's side and port, reads the spec's
# machine-readable block for what the spec says they are, binds the spec's IR
# axis figure to MK9's measurement, requires the current IR acceptance and the
# (separate, unchanged) antenna<->IR rules to be stated, and scans every
# governing mechanical / assembly document for a wrong mic direction or the
# 15 mm TX<->RX figure stated as current.  A sentence is FENCED -- historical,
# not current -- only when it is struck (~~..~~) or says so in words.
MIC_REF = "MK1"
MIC_PORT_DRILL_MM = 1.050
MIC_DATASHEET = ("hardware/demo/kicad/aqroot-demo/vendor/PUI/"
                 "pui-dmm-4026-b-i2s-r-revA.pdf")
MIC_DATASHEET_SHA256 = ("ce42c9bf03b671cd6e7e95a4bfc414a9"
                        "ffbd61747dbe4c76220ce650535f1a19")
SPEC_DOC = "docs/full-beta-v2/mechanical/MECHANICAL_INTERFACE_SPEC.md"
GOVERNING_MECH_DOCS = (
    SPEC_DOC,
    "docs/full-beta-v2/mechanical/P1_FLOORPLAN_INPUTS.md",
    "docs/full-beta-v2/pcb/FBV2_P1_KEEPOUTS.md",
    "docs/full-beta-v2/pcb/FBV2_P1_FLOORPLAN.md",
    "docs/full-beta-v2/assembly/IR_LEAD_FORMING.md",
    "docs/full-beta-v2/assembly/FOOTPRINT_VERIFICATION_LEDGER.md",
    "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md",
    "docs/full-beta-v2/DEVICE_SPEC.md",
)
# words that make a sentence historical rather than current
_FENCE = re.compile(r"SUPERSEDED|SUPERSEDES|HISTORICAL|\bnot met\b|"
                    r"under D-162's|no longer current", re.I)
_IR_PAIR = re.compile(r"\b(IR|TX|RX|emitter|receiver|TSAL6100|TSOP\d+|D1|U6)"
                      r"\b|IR[_ ]?TX|TX[_ ]?RX", re.I)
_IR_15 = re.compile(r"(≥|>=|at least|no less than|minimum(?: of)?|min\.?)\s*"
                    r"15(?:\.0+)?\s*mm|\b15(?:\.0+)?\s*(?:mm)?\s*"
                    r"(?:min\b|minimum|apart)|rule\s*(?:≥|>=)\s*15", re.I)
_ANTENNA = re.compile(r"SMA|bulkhead|antenna|whip|pigtail|service loop|coax|"
                      r"(c-c|centre-to-centre|edge-to-edge)\s+(to|from)\s+"
                      r"(either\s+)?IR\s+(window|aperture)", re.I)
_MIC_CTX = re.compile(r"\bMK1\b|microphone|\bmic\b|DMM-4026|acoustic", re.I)
_MIC_WRONG = (
    ("mic_mounted_on_top_or_front_copper",
     re.compile(r"\b(MK1|microphone|mic|part|it)\b[^.;|]{0,30}\b(sits|placed|"
                r"mounted|soldered|fitted|is)\s+on\s+(the\s+)?(top|F\.Cu|"
                r"front\s+(copper|of\s+the\s+(PCB|board)))\b(?!\s*(edge|"
                r"panel|shell|enclosure|aperture|wall|crown))", re.I)),
    ("acoustic_path_leaves_bottom_or_rear",
     re.compile(r"acoustic\s+(path|port|opening|hole)[^.;:|]{0,40}\b(leaves"
                r"|exits|opens|faces|points)\b[^.;:|]{0,25}\b(bottom|rear|back"
                r"|B\.Cu)\b", re.I)),
    ("aperture_or_gasket_on_bottom_or_rear",
     re.compile(r"\b(aperture|opening|gasket)s?\b(?:(?!MK1|microphone)"
                r"[^.;:|]){0,60}\b(belong|belongs|sit|sits|is|are|go|goes)\b"
                r"[^.;:|]{0,20}\bon\s+(the\s+)?(bottom|rear|back|B\.Cu)\b",
                re.I)),
    ("mic_called_top_port", re.compile(r"\btop[- ]port(ed)?\b", re.I)),
)


def _current_units(text):
    """Sentence-sized units of CURRENT text: struck spans removed, markdown
    emphasis dropped, table cells and code lines kept as their own units."""
    text = re.sub(r"~~.*?~~", " ", text, flags=re.S)
    # inline code ticks go; ``` fences stay, they delimit code units
    text = re.sub(r"(?<!`)`(?!`)", "", text.replace("**", ""))
    units, para, in_code = [], [], False

    def flush():
        if para:
            units.extend(re.split(r"(?<=[.!?])\s+", " ".join(para)))
            para.clear()
    # a unit is (sentence, row); a table cell's row is its whole table ROW,
    # so the antenna<->IR rule's cells stay attributed to the antenna row.
    # The FENCE is never taken from context: one struck cell does not fence
    # its neighbours.
    for raw in text.splitlines():
        line = re.sub(r"^\s*>\s?", "", raw)
        if line.strip().startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            units.append(line)
        elif line.strip().startswith("|"):
            flush()
            for cell in line.split("|"):
                units.extend((u, line) for u in
                             re.split(r"(?<=[.!?])\s+", cell))
        elif not line.strip() or line.lstrip().startswith("#"):
            flush()
            if line.strip():
                units.append(line)
        else:
            para.append(line.strip())
    flush()
    out = []
    for u in units:
        u, ctx = u if isinstance(u, tuple) else (u, None)
        if u.strip():
            out.append((u.strip(), ctx))
    return out


def _scan_governing(texts):
    ir, mic = [], []
    for rel, t in texts.items():
        prev = ""
        for u, ctx in _current_units(t):
            # "It sits on ..." names the part one sentence back
            subject_ctx, prev = prev + " " + u, u
            if _FENCE.search(u):
                continue
            # the antenna<->IR rule is told apart LOCALLY: a table cell by
            # its row, prose by the 80 characters before the figure and 40
            # after, so one sentence naming both the SMA and the IR pair
            # still answers for the pair
            for m in _IR_15.finditer(u):
                near = u[max(0, m.start() - 80):m.end() + 40]
                if not (_IR_PAIR.search(near) or
                        (ctx and _IR_PAIR.search(ctx))):
                    continue
                if _ANTENNA.search(near) or (ctx and _ANTENNA.search(ctx)):
                    continue
                ir.append(dict(doc=rel, text=u[:240]))
                break
            if _MIC_CTX.search(subject_ctx):
                for name, rx in _MIC_WRONG:
                    if rx.search(u):
                        mic.append(dict(doc=rel, form=name, text=u[:240]))
    return ir, mic


def _spec_field(spec, key):
    """A machine-readable block field, WITH its indented continuation lines."""
    m = re.search(r"^%s:\s+(.*(?:\n[ \t]+\S.*)*)" % re.escape(key), spec,
                  re.M)
    return " ".join(m.group(1).split()) if m else None


def _mic_on_board(board):
    f = board.FindFootprintByReference(MIC_REF)
    if f is None:
        return dict(present=False)
    side = "B" if f.IsFlipped() else "F"
    pads = list(f.Pads())
    p4 = next((p for p in pads if p.GetNumber() == "4"), None)
    port = [p for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    concentric = bool(p4 is not None and any(
        abs(p.GetPosition().x - p4.GetPosition().x) <= 1000
        and abs(p.GetPosition().y - p4.GetPosition().y) <= 1000
        and abs(p.GetDrillSize().x / 1e6 - MIC_PORT_DRILL_MM) <= 1e-6
        for p in port))
    words = (f.GetLibDescription() + " " + f.GetKeywords()).lower()
    bottom_port = bool(re.search(r"bottom[- ]port", words)) and concentric
    return dict(present=True, side=side, layer=f.GetLayerName(),
                port_npth_concentric_with_pad4=concentric,
                port_drill_mm=MIC_PORT_DRILL_MM if concentric else None,
                footprint_declares_bottom_port=bool(
                    re.search(r"bottom[- ]port", words)),
                bottom_port=bottom_port,
                # a bottom port faces the board, so sound arrives from the
                # OTHER copper face, through the NPTH
                acoustic_face=(("F" if side == "B" else "B")
                               if bottom_port else side))


def mk12(board, reg=None, doc_paths=None, mk9_result=None):
    reg = reg or regions()
    paths = {r: ROOT / r for r in GOVERNING_MECH_DOCS}
    paths.update(doc_paths or {})
    texts = {r: (paths[r].read_text(encoding="utf-8")
                 if paths[r].exists() else "") for r in GOVERNING_MECH_DOCS}
    missing_docs = [r for r in GOVERNING_MECH_DOCS if not texts[r]]
    spec = texts[SPEC_DOC]

    # -- the board ---------------------------------------------------------
    mic = _mic_on_board(board)
    ds = ROOT / MIC_DATASHEET
    ds_ok = ds.exists() and sha256(ds) == MIC_DATASHEET_SHA256

    # -- what the spec's machine-readable block says -----------------------
    conv = _spec_field(spec, "FBV2_SIDE_CONVENTION") or ""
    m = re.search(r"F\.Cu\s*=\s*(FRONT|REAR)", conv)
    front = ("F" if m.group(1) == "FRONT" else "B") if m else None
    fs = _spec_field(spec, "FBV2_MIC_SIDE") or ""
    m = re.search(r"MK1 on ([FB])\.Cu", fs)
    spec_side = m.group(1) if m else None
    fp = _spec_field(spec, "FBV2_MIC_PORT") or ""
    m = re.search(r"\b(BOTTOM|TOP)-PORT\b", fp)
    spec_port = m.group(1) if m else None
    fa = _spec_field(spec, "FBV2_MIC_ACOUSTIC_FACE") or ""
    m = re.search(r"\b([FB])\.Cu\b", fa)
    spec_face = m.group(1) if m else None

    mic_ok = bool(mic.get("present") and ds_ok and mic["bottom_port"]
                  and spec_side == mic["side"] and spec_port == "BOTTOM"
                  and spec_face == mic["acoustic_face"]
                  and front is not None and mic["acoustic_face"] == front)

    # -- IR: the spec's axis figure is MK9's measurement --------------------
    r9 = mk9_result or mk9(board, reg)
    fx = _spec_field(spec, "FBV2_IR_TX_RX_AXIS_MM") or ""
    m = re.match(r"([\d.]+)", fx)
    spec_axis = float(m.group(1)) if m else None
    iso = _spec_field(spec, "FBV2_IR_ISOLATION") or ""
    iso_terms = {t: (t in iso) for t in ("IR_BARRIER", "10 deg", "C-IR-01")}
    axis_ok = bool(spec_axis is not None and abs(
        spec_axis - r9["formed_axis_separation_mm"]) <= 0.005)
    ir_ok = bool(axis_ok and all(iso_terms.values()) and r9["ok"])

    # -- the antenna<->IR rules are a DIFFERENT requirement and stay -------
    c = _spec_field(spec, "FBV2_SMA_IR_CENTRE_MM") or ""
    e = _spec_field(spec, "FBV2_SMA_IR_EDGE_MM") or ""
    ant_ok = bool(re.match(r"15\.0 min c-c", c) and re.match(r"8\.0 min", e))

    # -- every governing document, current text only ------------------------
    ir_hits, mic_hits = _scan_governing(texts)

    ok = bool(mic_ok and ir_ok and ant_ok and not ir_hits and not mic_hits
              and not missing_docs)
    return dict(
        ok=ok,
        microphone=dict(ok=mic_ok, board=mic,
                        datasheet=MIC_DATASHEET, datasheet_sha256_ok=ds_ok,
                        datasheet_fact="PUI DMM-4026-B-I2S-R Rev A 5/26/2021 "
                                       "p.6: Ø0.25 mm acoustic port on the "
                                       "PAD face inside the pad-4 GND ring",
                        spec_front_copper=front, spec_side=spec_side,
                        spec_port=spec_port, spec_acoustic_face=spec_face),
        ir=dict(ok=ir_ok, spec_axis_mm=spec_axis,
                measured_axis_mm=r9["formed_axis_separation_mm"],
                spec_axis_matches_mk9=axis_ok, spec_isolation_terms=iso_terms,
                mk9_ok=r9["ok"]),
        antenna_ir_rules_retained=dict(ok=ant_ok, centre=c, edge=e),
        ir_15mm_stated_as_current=ir_hits,
        wrong_microphone_direction=mic_hits,
        governing_documents=list(GOVERNING_MECH_DOCS),
        missing_documents=missing_docs)


def mk12_controls(board, reg):
    """D-801 destructive controls, on TEMPORARY COPIES of the documents and
    on in-memory board edits that are restored."""
    import tempfile
    ctl = {}
    base = mk12(board, reg)
    tmp = Path(tempfile.mkdtemp(prefix="mk12-"))

    # A control is CAUGHT when the injection adds a finding the untouched
    # documents do not have -- measured against the baseline, so a control
    # stays meaningful (and MK12, not MK7, reports) if a live document is
    # wrong today.
    def more(r, key):
        return len(r[key]) > len(base[key])

    def with_doc(rel, mutate):
        src = (ROOT / rel).read_text(encoding="utf-8")
        out = mutate(src)
        if out == src:
            # the mutation found nothing to change: the control CANNOT be
            # said to have been caught, so it reads as a clean document
            return dict(ok=True, microphone=dict(ok=True),
                        ir=dict(ok=True, spec_axis_matches_mk9=True),
                        antenna_ir_rules_retained=dict(ok=True),
                        ir_15mm_stated_as_current=[],
                        wrong_microphone_direction=[])
        p = tmp / Path(rel).name
        p.write_text(out, encoding="utf-8")
        return mk12(board, reg, doc_paths={rel: p})

    def append(s, extra):
        return s + "\n\n" + extra + "\n"

    # wrong microphone direction, each written form, into the spec copy
    for key, sentence in (
            ("the_old_M14_top_mount_sentence",
             "MK1 is a BOTTOM-PORT MEMS microphone. It sits on the TOP of the "
             "PCB and listens THROUGH the board."),
            ("an_aperture_on_the_bottom_face",
             "The microphone enclosure aperture and any acoustic gasket "
             "belong on the BOTTOM face, not the component face."),
            ("an_acoustic_path_to_the_rear",
             "The microphone acoustic path leaves on the rear (B.Cu) face."),
            ("a_top_port_microphone",
             "MK1 is a top-port microphone.")):
        r = with_doc(SPEC_DOC, lambda s, x=sentence: append(s, x))
        ctl["d801_mic_" + key + "_is_refused"] = more(
            r, "wrong_microphone_direction")
    # ...and into the footprint ledger copy (a second governing document)
    r = with_doc("docs/full-beta-v2/assembly/FOOTPRINT_VERIFICATION_LEDGER.md",
                 lambda s: append(s, "Orientation: MK1 sits on the top of the "
                                     "PCB; the acoustic path leaves on the "
                                     "bottom face."))
    ctl["d801_mic_wrong_direction_in_the_ledger_is_refused"] = more(
        r, "wrong_microphone_direction")
    # the structured fields
    r = with_doc(SPEC_DOC, lambda s: s.replace(
        "FBV2_MIC_SIDE:           MK1 on B.Cu", "FBV2_MIC_SIDE:           MK1 on F.Cu"))
    ctl["d801_spec_mic_side_F_is_refused"] = not r["microphone"]["ok"]
    r = with_doc(SPEC_DOC, lambda s: re.sub(
        r"^(FBV2_MIC_ACOUSTIC_FACE:\s+)F\.Cu", r"\1B.Cu", s, flags=re.M))
    ctl["d801_spec_acoustic_face_B_is_refused"] = not r["microphone"]["ok"]

    # 15 mm TX<->RX stated as CURRENT
    r = with_doc(SPEC_DOC, lambda s: append(
        s, "| **Emitter ↔ receiver separation** | **≥ 15 mm**, plus an opaque "
           "barrier | current |"))
    ctl["d801_ir_15mm_row_in_the_spec_is_refused"] = more(
        r, "ir_15mm_stated_as_current")
    r = with_doc("docs/full-beta-v2/assembly/IR_LEAD_FORMING.md", lambda s: append(
        s, "The IR emitter and receiver must be at least 15 mm apart."))
    ctl["d801_ir_15mm_in_the_forming_traveler_is_refused"] = more(
        r, "ir_15mm_stated_as_current")
    # the D-800 DEVICE_SPEC §13 form: the SMA and the IR pair in ONE sentence
    r = with_doc(SPEC_DOC, lambda s: append(
        s, "- **TOP edge:** **915 MHz SMA bulkhead** (Ø6.5 mm hole, left half); "
           "**IR TX window**\n  and **IR RX window** with a **mandatory opaque "
           "IR barrier** between them (emitter↔\n  receiver ≥15 mm)."))
    ctl["d801_ir_15mm_beside_the_sma_in_one_sentence_is_refused"] = more(
        r, "ir_15mm_stated_as_current")
    r = with_doc(SPEC_DOC, lambda s: append(
        s, "FBV2_IR_TX_RX_MIN_MM:    15.0 min   LOCKED (D-162)"))
    ctl["d801_ir_15mm_block_field_is_refused"] = more(
        r, "ir_15mm_stated_as_current")
    # POSITIVE: the fence is a word, not a blanket keyword ban
    r = with_doc(SPEC_DOC, lambda s: append(
        s, "D-162's emitter ↔ receiver ≥ 15 mm figure is SUPERSEDED for this "
           "frozen design."))
    ctl["d801_a_fenced_15mm_sentence_is_accepted"] = not more(
        r, "ir_15mm_stated_as_current")
    # the spec's axis figure must be the measurement, and the acceptance stated
    r = with_doc(SPEC_DOC, lambda s: re.sub(
        r"^(FBV2_IR_TX_RX_AXIS_MM:\s+)13\.73", r"\g<1>15.13", s, flags=re.M))
    ctl["d801_spec_axis_15_13_origin_figure_is_refused"] = not r["ir"]["ok"]
    r = with_doc(SPEC_DOC, lambda s: re.sub(
        r"^(FBV2_IR_ISOLATION:.*?)C-IR-01", r"\1first article", s,
        count=1, flags=re.M | re.S))
    ctl["d801_dropping_C_IR_01_is_refused"] = not r["ir"]["ok"]
    # the antenna rules are not collateral
    r = with_doc(SPEC_DOC, lambda s: re.sub(
        r"^FBV2_SMA_IR_CENTRE_MM:.*\n", "", s, flags=re.M))
    ctl["d801_deleting_the_antenna_ir_15mm_rule_is_refused"] = not r[
        "antenna_ir_rules_retained"]["ok"]

    # the board: MK1 flipped to F.Cu, its port removed, D1 moved
    f = board.FindFootprintByReference(MIC_REF)
    f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    ctl["d801_mk1_flipped_to_F_Cu_is_refused"] = not mk12(
        board, reg)["microphone"]["ok"]
    f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    port = next(p for p in f.Pads()
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH)
    ds0 = port.GetDrillSize()
    was = pcbnew.VECTOR2I(int(ds0.x), int(ds0.y))   # a COPY, not a view
    port.SetDrillSize(pcbnew.VECTOR2I(800000, 800000))
    ctl["d801_mk1_port_not_the_1_05_mm_npth_is_refused"] = not mk12(
        board, reg)["microphone"]["ok"]
    port.SetDrillSize(was)
    d1 = board.FindFootprintByReference("D1")
    p0 = d1.GetPosition()
    was = pcbnew.VECTOR2I(int(p0.x), int(p0.y))
    d1.SetPosition(pcbnew.VECTOR2I(was.x - 500000, was.y))
    ctl["d801_board_axis_moved_off_the_spec_figure_is_refused"] = not mk12(
        board, reg)["ir"]["spec_axis_matches_mk9"]
    d1.SetPosition(was)
    ctl["d801_board_restored"] = mk12(board, reg)["ok"] == base["ok"]
    return ctl


def mk7(board):
    """Live negative controls: each puts a specific defect back."""
    reg = regions()
    ctl = {}

    # a boss nudged 0.100 mm off its registered position
    f = board.FindFootprintByReference("BOSS1")
    was = f.GetPosition()
    f.SetPosition(pcbnew.VECTOR2I(was.x + 100000, was.y))
    ctl["a_boss_nudged_0_100_mm_is_refused"] = not mk2(board)["ok"]
    f.SetPosition(was)

    # a rib region slid onto the converter block -- the D-759 defect itself
    slid = dict(reg)
    slid["RIB_R2A"] = doc_box(67.20, 70.70, 45.00, 64.00)
    saved = list(RIBS)
    ctl["the_retired_RIB_R2_footprint_is_refused"] = bool(
        _back_side_occupants(board, slid["RIB_R2A"]))

    # a through-hole lead planted in the battery volume
    x0, x1, y0, y1 = reg["BATTERY_SHADOW"]
    j = board.FindFootprintByReference("J3")
    pad = next(iter(j.Pads()))
    keep_pos, keep_attr = pad.GetPosition(), pad.GetAttribute()
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad.SetPosition(pcbnew.VECTOR2I(int((x0 + x1) / 2 * 1e6),
                                    int((y0 + y1) / 2 * 1e6)))
    ctl["a_lead_in_the_battery_volume_is_refused"] = not mk5(board, reg)["ok"]
    pad.SetPosition(keep_pos)
    pad.SetAttribute(keep_attr)

    # the section-1 datum, which is the mistake D-758 made
    def fits_x(bb, box):
        return bb[0] >= box[0] - 1e-6 and bb[2] <= box[1] + 1e-6
    ctl["reading_the_pre_rebase_datum_is_visible"] = not all(
        fits_x(body_box(board.FindFootprintByReference(r)),
               doc_box(*SECTION1[n])) for n, r in DATUM_PARTS.items())

    # a part one micron taller than its region's allowance must be refused
    tallest = max(MAX_HEIGHT_MM.values(), key=lambda v: v[0])[0]
    saved = dict(MAX_HEIGHT_MM)
    MAX_HEIGHT_MM["C_0603_1608Metric"] = (tallest + 0.001, "control",
                                          "synthetic: one micron over the ceiling")
    ctl["a_part_over_its_region_allowance_is_refused"] = not mk8(board, reg)["ok"]
    MAX_HEIGHT_MM.clear()
    MAX_HEIGHT_MM.update(saved)

    # a footprint with NO height figure must be refused rather than skipped
    saved2 = MAX_HEIGHT_MM.pop("R_0603_1608Metric")
    ctl["a_footprint_with_no_height_figure_is_refused"] = not mk8(board, reg)["ok"]
    MAX_HEIGHT_MM["R_0603_1608Metric"] = saved2

    # the IR pair nudged 0.200 mm together must be refused -- the rule has
    # 0.133 mm of margin, so 0.200 mm spends it
    # D-800: MK9 gates the barrier and the cone.  D1 moved east until its
    # courtyard crosses the barrier face (+1.300 mm) must be refused, and so
    # must U6 moved west into the barrier.
    d1 = board.FindFootprintByReference("D1")
    was = d1.GetPosition()
    d1.SetPosition(pcbnew.VECTOR2I(was.x + 1300000, was.y))
    ctl["d800_d1_courtyard_pushed_into_the_ir_barrier_is_refused"] = \
        not mk9(board, reg)["ok"]
    d1.SetPosition(was)
    u6 = board.FindFootprintByReference("U6")
    was = u6.GetPosition()
    u6.SetPosition(pcbnew.VECTOR2I(was.x - 600000, was.y))
    ctl["d800_u6_courtyard_pushed_into_the_ir_barrier_is_refused"] = \
        not mk9(board, reg)["ok"]
    u6.SetPosition(was)

    # D-763.  Four controls on MK10, the clause that owns the lead rather than
    # the body.  Each puts back a different way J4 could have gone unnoticed.

    # 1. the declaration removed -- a 1.026 mm overshoot with nothing behind it
    saved3 = dict(DECLARED_LEAD_TRIM)
    DECLARED_LEAD_TRIM.clear()
    ctl["an_undeclared_lead_over_the_allowance_is_refused"] = not mk10(board, reg)["ok"]
    DECLARED_LEAD_TRIM.update(saved3)

    # 2. a declaration whose TRIM does not meet the allowance it is declared
    #    against -- a mitigation that does not mitigate
    DECLARED_LEAD_TRIM[("J4", "DISPLAY_SHADOW")] = dict(
        saved3[("J4", "DISPLAY_SHADOW")], trim_to_mm=1.50)
    ctl["a_trim_that_does_not_meet_the_allowance_is_refused"] = not mk10(board, reg)["ok"]
    DECLARED_LEAD_TRIM.clear()
    DECLARED_LEAD_TRIM.update(saved3)

    # 3. J4 is a manual pigtail land.  If its reference-specific assembly
    #    protrusion declaration disappears, the old JST footprint identity must
    #    NOT silently make it look like a fitted header again.
    saved4 = MANUAL_THT_PROTRUSION_MM.pop("J4")
    saved_hdr = THT_LEAD_MM.pop("JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical")
    ctl["a_manual_J4_with_no_profile_is_refused"] = not mk10(board, reg)["ok"]
    THT_LEAD_MM["JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"] = saved_hdr
    MANUAL_THT_PROTRUSION_MM["J4"] = saved4

    # 4. the old zero-margin D-763 declaration (0.80 mm under a 0.80 mm
    #    allowance) is no longer acceptable once insulation is required.
    DECLARED_LEAD_TRIM[("J4", "DISPLAY_SHADOW")] = dict(
        saved3[("J4", "DISPLAY_SHADOW")], trim_to_mm=0.80,
        insulation_max_mm=0.0)
    ctl["the_old_zero_margin_0_80_mm_trim_is_refused"] = not mk10(board, reg)["ok"]
    DECLARED_LEAD_TRIM.clear()
    DECLARED_LEAD_TRIM.update(saved3)

    # 5. losing the insulation declaration must be refused even when the
    #    conductor trim itself is good.
    no_ins = dict(saved3[("J4", "DISPLAY_SHADOW")])
    no_ins.pop("insulation_requirement", None)
    no_ins.pop("insulation", None)
    no_ins.pop("insulation_max_mm", None)
    DECLARED_LEAD_TRIM[("J4", "DISPLAY_SHADOW")] = no_ins
    ctl["missing_J4_polyimide_insulation_is_refused"] = not mk10(board, reg)["ok"]
    DECLARED_LEAD_TRIM.clear()
    DECLARED_LEAD_TRIM.update(saved3)

    # 6. MEMBERSHIP IS LIVE, NOT A HARD-CODED REFERENCE.  Move J4 clear of
    #    DISPLAY_SHADOW and the finding must DISAPPEAR -- otherwise the clause
    #    is asserting J4 rather than measuring it.
    j4 = board.FindFootprintByReference("J4")
    was4 = j4.GetPosition()
    j4.SetPosition(pcbnew.VECTOR2I(was4.x, int(5.0 * 1e6)))
    ctl["moving_J4_clear_of_the_region_removes_the_finding"] = not mk10(
        board, reg)["leads_in_a_limited_region"]
    j4.SetPosition(was4)

    # D-764.  External-interface authority must be live rather than prose.
    sw1 = board.FindFootprintByReference("SW1")
    was_sw1 = sw1.GetPosition()
    sw1.SetPosition(pcbnew.VECTOR2I(was_sw1.x + 100000, was_sw1.y))
    ctl["a_0_100_mm_BOOT_nudge_is_refused"] = not mk11(board)["ok"]
    sw1.SetPosition(was_sw1)

    sw9 = board.FindFootprintByReference("SW9")
    was_sw9 = sw9.GetPosition()
    sw9.SetPosition(pcbnew.VECTOR2I(was_sw9.x, was_sw9.y + 100000))
    ctl["a_0_100_mm_POWER_nudge_is_refused"] = not mk11(board)["ok"]
    sw9.SetPosition(was_sw9)

    j5c = board.FindFootprintByReference("J5")
    was_j5 = j5c.GetPosition()
    j5c.SetPosition(pcbnew.VECTOR2I(was_j5.x + 100000, was_j5.y))
    ctl["a_0_100_mm_J5_nudge_is_refused"] = not mk11(board)["ok"]
    j5c.SetPosition(was_j5)

    # D-801.  MK12's controls: wrong mic direction, 15 mm TX<->RX as current,
    # the antenna rules deleted, and MK1 / D1 moved on the board.
    ctl.update(mk12_controls(board, reg))

    return dict(ok=all(ctl.values()), controls=ctl)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    board = pcbnew.LoadBoard(str(a.board))
    reg = regions()
    checks = {
        "MK1_datum_proved_by_the_board": mk1(board),
        "MK2_boss_retention": mk2(board),
        "MK3_rear_support_ribs_component_free": mk3(board, reg),
        "MK4_speaker_cavity_has_no_rear_part": mk4(board, reg),
        "MK5_no_through_hole_lead_in_the_battery_volume": mk5(board, reg),
        "MK6_boss2_is_inside_the_ir_barrier": mk6(board, reg),
        "MK7_not_vacuous": mk7(board),
        "MK8_component_height_in_the_limited_regions": mk8(board, reg),
        "MK9_ir_pair_separation_and_barrier": mk9(board, reg),
        "MK10_through_hole_lead_on_the_opposite_face":
            mk10(board, reg, a.board),
        "MK11_external_interface_authority": mk11(board),
        "MK12_governing_text_matches_the_board_mic_and_ir": mk12(board, reg),
    }
    doc = dict(schema=1, board=str(a.board), board_sha256=sha256(a.board),
               datum="FBV2-EXP-002 RE-BASED: section-1 X + %.3f mm; "
                     "Y_kicad = %.3f - Y_doc" % (REBASE_X, BOARD_H),
               regions={k: [round(v, 4) for v in reg[k]] for k in sorted(reg)},
               checks=checks,
               all_pass=all(c["ok"] for c in checks.values()))
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    for k, c in sorted(checks.items()):
        print(" %-50s %s" % (k, "PASS" if c["ok"] else "FAIL"), file=sys.stderr)
    return 0 if doc["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
