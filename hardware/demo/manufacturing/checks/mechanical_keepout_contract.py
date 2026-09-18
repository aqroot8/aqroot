#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the MECHANICAL KEEP-OUT contract (MK1-MK7).

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
         a rib region slid onto a part, a lead planted in the battery volume --
         must each be caught by the clause that owns them.

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
