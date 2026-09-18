#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the MECHANICAL KEEP-OUT contract (MK1-MK11).

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

         `J4`, the BATTERY CONNECTOR, is the ONLY through-hole part on this
         board whose body is on `B.Cu`.  It is a JST `B2B-PH-K-S`: JST's own
         `ePH.pdf` gives the body **6.0 mm** and the lead **(3.4) mm** below
         the seating plane.  The board's OWN stackup totals **1.5744 mm**, so
         the lead stands **1.826 mm proud of `F.Cu`** -- and both of `J4`'s
         pads are inside `DISPLAY_SHADOW`, where the register's rule is
         **F.Cu height <= 0.80 mm**.  That is **1.026 mm over**, directly
         under the 3.5-inch panel, and untrimmed it stops the display seating.

         So MK10 asks it for EVERY height-limited region, on the board's own
         stackup thickness rather than a constant: a lead over the region's
         allowance must be DECLARED in `assembly/THT_LEAD_TRIM.md` with a trim
         that meets the allowance, and a through-hole part inside a region
         with NO vendor lead figure is REFUSED rather than skipped.


    MK11 EXTERNAL INTERFACE AUTHORITY.  D-764 found that DEVICE_SPEC still
         called BOOT and POWER positions "UNRESOLVED" even though D-242 and
         the live board agree, while the mechanical spec still carried the
         superseded 2x12 J5 drill/aperture as current in several places.  Pin
         the board-side facts that enclosure CAD and manual assembly consume:
         SW1 front-wall tool-hole datum, SW9 right-wall datum, and the current
         1x24 J5 identity/position/drill/pitch/mating-face geometry plus the
         conservative M-09 Z bound.

    python3 hardware/demo/manufacturing/checks/mechanical_keepout_contract.py \
        [--board B.kicad_pcb] [-o REPORT.json]
"""
import argparse
import hashlib
import json
import math
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
                        "seating plane"),
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
    "C_1206_3216Metric": (1.80, "vendor", "Murata GRM31C 1206: T = 1.6 +/- 0.2 mm"),
    "C_1210_3225Metric": (2.00, "eia", "MLCC, 1210, high-capacitance build"),
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

# The region allowances MK8 enforces, and the rule each one is measured
# against.  `allowance_mm` is a NO-REGRESSION CEILING set at the board's own
# measured profile -- the board may not get taller here without a decision --
# and `register_limit_mm` is the inherited rule the register still states.
# Where the two differ the gap is REPORTED, not hidden: it is an open CAD item
# and closing it is a stack calculation nobody on this repository can do
# without the enclosure.
HEIGHT_REGIONS = {
    "DISPLAY_SHADOW": dict(side="F", register_limit_mm=0.80, allowance_mm=0.80),
    "BATTERY_SHADOW": dict(side="B", register_limit_mm=1.20, allowance_mm=1.80),
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
            h = MAX_HEIGHT_MM.get(fid)
            if h is None:
                unknown.add(fid)
                parts.append(dict(ref=f.GetReference(), footprint=fid,
                                  max_height_mm=None, source=None))
                continue
            parts.append(dict(ref=f.GetReference(), footprint=fid,
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
                         measured_tallest_mm=round(tallest, 3),
                         parts_over_the_allowance=over_allowance,
                         parts_over_the_register_limit=over_register,
                         open_cad_gap_mm=round(max(0.0, tallest - spec["register_limit_mm"]), 3),
                         parts=sorted(parts, key=lambda p: (-(p["max_height_mm"] or 0),
                                                            p["ref"])))
    return dict(ok=ok, regions=out,
                footprints_with_no_height_figure=sorted(unknown),
                note="allowance_mm is a no-regression ceiling at the board's own "
                     "measured profile; register_limit_mm is the inherited rule "
                     "and the gap between them is an OPEN CAD ITEM (D-760)")



# D-761.  THE IR PAIR, WHICH IS A FUNCTIONAL RULE WITH 0.133 mm OF MARGIN.
#
# `FBV2_P1_KEEPOUTS.md` §4 cites "the >= 15 mm IR TX<->RX rule" as the reason
# `D1` cannot move, and `D-226` widened `IR_BARRIER` 3.0 -> 5.0 mm to stand
# between them.  Neither statement was checked by anything.  The pair measures
# 15.1327 mm centre to centre -- the rule is MET, and by 0.133 mm, which is
# exactly the kind of margin that a 0.2 mm placement nudge spends without
# anybody noticing.
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
        requirement="J4-T1", trim_to_mm=0.80,
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
            lead = THT_LEAD_MM.get(fid)
            if lead is None:
                unknown.append([ref, fid, name])
                continue
            proud = round(max(0.0, lead[0] - thick), 4)
            row = dict(ref=ref, footprint=fid, region=name, region_face=side,
                       body_face=body, pads=sorted(q.GetNumber() for q in inside),
                       lead_mm=lead[0], lead_source=lead[1], lead_basis=lead[2],
                       board_thickness_mm=thick, protrusion_mm=proud,
                       allowance_mm=spec["allowance_mm"],
                       over_mm=round(max(0.0, proud - spec["allowance_mm"]), 4))
            if row["over_mm"] > 1e-9:
                d = DECLARED_LEAD_TRIM.get((ref, name))
                if not d:
                    undeclared.append([ref, name, row["over_mm"]])
                elif (d["trim_to_mm"] > spec["allowance_mm"] + 1e-9
                      or d["requirement"] not in doc or ref not in doc):
                    bad_trim.append([ref, name, d["requirement"]])
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


def mk9(board, reg=None):
    reg = reg or regions()
    d1 = board.FindFootprintByReference("D1")
    u6 = board.FindFootprintByReference("U6")
    if d1 is None or u6 is None:
        return dict(ok=False, why="D1 or U6 missing")
    a, b2 = d1.GetPosition(), u6.GetPosition()
    sep = math.hypot(a.x - b2.x, a.y - b2.y) / 1e6
    bar = reg["IR_BARRIER"]
    d1_east = max(q.GetPosition().x / 1e6 for q in d1.Pads())
    u6_west = min(q.GetPosition().x / 1e6 for q in u6.Pads())
    between = d1_east <= bar[0] + 1e-6 and u6_west >= bar[1] - 1e-6
    return dict(ok=sep >= IR_TX_RX_MIN_MM - 1e-6 and between,
                separation_mm=round(sep, 4), rule_min_mm=IR_TX_RX_MIN_MM,
                margin_mm=round(sep - IR_TX_RX_MIN_MM, 4),
                ir_barrier_x_mm=[bar[0], bar[1]],
                d1_easternmost_pad_x_mm=round(d1_east, 3),
                u6_westernmost_pad_x_mm=round(u6_west, 3),
                barrier_stands_between_them=between)



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
    d1 = board.FindFootprintByReference("D1")
    was = d1.GetPosition()
    d1.SetPosition(pcbnew.VECTOR2I(was.x + 200000, was.y))
    ctl["the_ir_pair_nudged_0_200_mm_together_is_refused"] = not mk9(board, reg)["ok"]
    d1.SetPosition(was)

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

    # 3. a through-hole part in a limited region with NO vendor lead figure
    saved4 = THT_LEAD_MM.pop("JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical")
    ctl["a_through_hole_part_with_no_lead_figure_is_refused"] = (
        not mk10(board, reg)["ok"])
    THT_LEAD_MM["JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"] = saved4

    # 4. MEMBERSHIP IS LIVE, NOT A HARD-CODED REFERENCE.  Move J4 clear of
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
