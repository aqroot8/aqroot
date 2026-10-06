#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- D-806 vendor drawings: REFERENCE LOCATOR and BOARD PROFILE.

WHY.  JLCPCB's engineering review of 2026-10-06 could not locate component
footprints: the production silkscreen carries no reference designators (by
design) and the KiCad assembly plots are A4 at 0.60 scale, where a 0402's
reference is a fraction of a millimetre and overprinted by its own body.  The
same review did not understand the phrase "stepped board profile".

D-806 answers both WITHOUT touching the silkscreen or the outline:

  * `aqroot-Demo-assembly-locator-{top,bottom}.pdf` -- A3, scale 2.5:1, one
    label per FITTED reference, drawn AT THE CPL CENTROID (red cross), sized to
    the part's own courtyard so labels cannot collide, over a lettered 10 mm
    grid; the bottom sheet is mirrored as the assembler sees it.  Each file
    ends with an index (ref, side, grid cell, CPL X/Y/rot, value, package).
  * `aqroot-Demo-assembly-ref-index.csv` -- the same index, machine readable.
  * `aqroot-Demo-board-profile.pdf` / `.json` -- the outline, dimensioned:
    tabs, drawn fillets, outside radii, sharp inside corners, routed slots,
    and what CAM must not normalise.

Everything is read from the board and the fitted CPL at generation time.  The
PDF writer below is dependency-free and emits no timestamp, so the files are
byte-deterministic for a given board.

    python3 jlc_drawings.py --board B --cpl pos-fitted.csv --all-cpl pos-all.csv
        --release D-806 -o OUTDIR
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import pcbnew

MM = 1e6
PT = 72.0 / 25.4                     # points per mm
A3 = (297.0, 420.0)                  # portrait, mm
GRID = 10.0                          # board mm per grid cell
COLS = "ABCDEFGH"                    # x 0..80
LOCATOR_SCALE = 2.5
PROFILE_SCALE = 1.8
FILES = dict(top="aqroot-Demo-assembly-locator-top.pdf",
             bottom="aqroot-Demo-assembly-locator-bottom.pdf",
             index="aqroot-Demo-assembly-ref-index.csv",
             profile_pdf="aqroot-Demo-board-profile.pdf",
             profile_json="aqroot-Demo-board-profile.json")


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# a minimal deterministic PDF writer (Helvetica, lines, polygons, text)
# --------------------------------------------------------------------------
def _esc(s):
    s = s.encode("latin-1", "replace").decode("latin-1")
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class Page:
    def __init__(self, size=A3):
        self.w, self.h = size
        self.ops = []

    # all public coordinates are millimetres from the TOP-LEFT of the sheet
    def _p(self, x, y):
        return x * PT, (self.h - y) * PT

    def stroke(self, rgb=(0, 0, 0), width=0.15, dash=None):
        self.ops.append("%.3f %.3f %.3f RG %.3f w %s" % (
            rgb[0], rgb[1], rgb[2], width * PT,
            ("[%s] 0 d" % " ".join("%.2f" % (d * PT) for d in dash)) if dash else "[] 0 d"))

    def fill(self, rgb):
        self.ops.append("%.3f %.3f %.3f rg" % rgb)

    def poly(self, pts, close=True, fill=False):
        if len(pts) < 2:
            return
        x, y = self._p(*pts[0])
        o = ["%.2f %.2f m" % (x, y)]
        for q in pts[1:]:
            x, y = self._p(*q)
            o.append("%.2f %.2f l" % (x, y))
        o.append(("h " if close else "") + ("B" if fill else "S"))
        self.ops.append(" ".join(o))

    def line(self, a, b):
        self.poly([a, b], close=False)

    def rect(self, x0, y0, x1, y1, fill=False):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill=fill)

    def circle(self, cx, cy, r, fill=False, n=24):
        self.poly([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
                   for k in range(n)], fill=fill)

    def text(self, x, y, s, size=2.5, rgb=(0, 0, 0), rot=0, anchor="l", bold=False):
        """size in mm (cap-ish height ~0.72 size); (x, y) baseline-left unless anchor."""
        wid = text_width(s, size)
        # anchor offset in the text's own frame (PDF, y up), then rotate CCW by rot
        ux, uy = {"c": (-wid / 2, -0.36 * size), "r": (-wid, 0.0)}.get(anchor, (0.0, 0.0))
        c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        px, py = self._p(x + (ux * c - uy * s_), y - (ux * s_ + uy * c))
        self.ops.append("BT /%s %.2f Tf %.3f %.3f %.3f rg %.5f %.5f %.5f %.5f %.2f %.2f Tm (%s) Tj ET" % (
            "F2" if bold else "F1", size * PT, rgb[0], rgb[1], rgb[2], c, s_, -s_, c, px, py, _esc(s)))


def text_width(s, size):
    # Helvetica advance widths (per 1000 em) for the characters these sheets use
    w = 0
    for ch in s:
        if ch in "0123456789":
            w += 556
        elif ch in "ABCDEFGHKNPRSUVXYZ":
            w += 667
        elif ch in "MW":
            w += 833 if ch == "M" else 944
        elif ch in "OQG":
            w += 778
        elif ch in "IJLT":
            w += {"I": 278, "J": 500, "L": 556, "T": 611}[ch]
        elif ch in " .,:;|/-()_'":
            w += 278 if ch in " .,:;|/'" else 333
        else:
            w += 556
    return w / 1000.0 * size


def write_pdf(path, pages, title):
    objs = []

    def add(b):
        objs.append(b)
        return len(objs)
    cat = add(None)
    pages_id = add(None)
    f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    kids = []
    for pg in pages:
        data = "\n".join(pg.ops).encode("latin-1", "replace")
        cs = add(b"<< /Length %d >>\nstream\n" % len(data) + data + b"\nendstream")
        kids.append(add(("<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
                         "/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>"
                         % (pages_id, pg.w * PT, pg.h * PT, f1, f2, cs)).encode()))
    objs[cat - 1] = ("<< /Type /Catalog /Pages %d 0 R >>" % pages_id).encode()
    objs[pages_id - 1] = ("<< /Type /Pages /Kids [%s] /Count %d >>"
                          % (" ".join("%d 0 R" % k for k in kids), len(kids))).encode()
    info = add(("<< /Title (%s) /Producer (AQROOT jlc_drawings.py) >>" % _esc(title)).encode())
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offs = []
    for i, b in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + b + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1, cat, info, xref)
    Path(path).write_bytes(bytes(out))


# --------------------------------------------------------------------------
# board facts
# --------------------------------------------------------------------------
def outline_items(board):
    items = []
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        s, e = d.GetStart(), d.GetEnd()
        it = dict(kind="line" if d.GetShape() == pcbnew.SHAPE_T_SEGMENT else
                  "arc" if d.GetShape() == pcbnew.SHAPE_T_ARC else "other",
                  start=[round(s.x / MM, 4), round(s.y / MM, 4)],
                  end=[round(e.x / MM, 4), round(e.y / MM, 4)])
        if it["kind"] == "arc":
            c, m = d.GetCenter(), d.GetArcMid()
            it.update(centre=[round(c.x / MM, 4), round(c.y / MM, 4)],
                      mid=[round(m.x / MM, 4), round(m.y / MM, 4)],
                      radius=round(d.GetRadius() / MM, 4))
        items.append(it)
    items.sort(key=lambda i: (i["kind"], i["start"], i["end"]))
    return items


def arc_points(it, n=16):
    cx, cy = it["centre"]
    r = it["radius"]
    a0 = math.atan2(it["start"][1] - cy, it["start"][0] - cx)
    a1 = math.atan2(it["end"][1] - cy, it["end"][0] - cx)
    am = math.atan2(it["mid"][1] - cy, it["mid"][0] - cx)
    # choose the sweep that passes through mid
    def between(a, b, m):
        d1 = (m - a) % (2 * math.pi)
        d2 = (b - a) % (2 * math.pi)
        return d1 <= d2
    if between(a0, a1, am):
        sweep = (a1 - a0) % (2 * math.pi)
    else:
        sweep = -((a0 - a1) % (2 * math.pi))
    return [(cx + r * math.cos(a0 + sweep * k / n), cy + r * math.sin(a0 + sweep * k / n)) for k in range(n + 1)]


def read_cpl(path):
    return list(csv.DictReader(open(path, newline="")))


def footprint_facts(board):
    out = {}
    for f in board.GetFootprints():
        side = "bottom" if f.IsFlipped() else "top"
        lay = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd
        cy = f.GetCourtyard(lay)
        court = []
        if cy.OutlineCount():
            o = cy.Outline(0)
            court = [(o.CPoint(i).x / MM, o.CPoint(i).y / MM) for i in range(o.PointCount())]
        pads = []
        for p in f.Pads():
            bb = p.GetBoundingBox()
            pads.append(dict(num=p.GetNumber(), box=(bb.GetLeft() / MM, bb.GetTop() / MM,
                                                     bb.GetRight() / MM, bb.GetBottom() / MM),
                             drill=(p.GetDrillSize().x / MM if p.GetDrillSize().x else 0.0),
                             pos=(p.GetPosition().x / MM, p.GetPosition().y / MM)))
        if not court and pads:
            xs = [q for pd in pads for q in (pd["box"][0], pd["box"][2])]
            ys = [q for pd in pads for q in (pd["box"][1], pd["box"][3])]
            court = [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]
        out[f.GetReference()] = dict(side=side, pos=(f.GetPosition().x / MM, f.GetPosition().y / MM),
                                     court=court, pads=pads, fpid=f.GetFPIDAsString())
    return out


def grid_cell(x, y):
    c = int(max(0, min(len(COLS) - 1, math.floor(x / GRID))))
    r = int(max(0, math.floor(y / GRID))) + 1
    return "%s%d" % (COLS[c], r)


# --------------------------------------------------------------------------
# reference locator
# --------------------------------------------------------------------------
def locator(board, cpl_rows, dnp_refs, release, board_sha, out_dir):
    facts = footprint_facts(board)
    items = outline_items(board)
    bb = board.GetBoardEdgesBoundingBox()
    W = round(bb.GetRight() / MM - 0.05, 3)          # outline centre-line extent
    index = []
    for r in cpl_rows:
        ref = r["Ref"]
        f = facts[ref]
        x, y = float(r["PosX"]), -float(r["PosY"])
        index.append(dict(Ref=ref, Side=r["Side"], Grid=grid_cell(x, y),
                          CPL_X=r["PosX"], CPL_Y=r["PosY"], Rot=r["Rot"],
                          Value=r["Val"], Package=r["Package"],
                          Board_X_mm="%.4f" % f["pos"][0], Board_Y_down_mm="%.4f" % f["pos"][1]))
    index.sort(key=lambda d: (d["Side"] != "top", natural(d["Ref"])))
    S, X0, Y0 = LOCATOR_SCALE, 15.0, 15.0
    files = {}
    for side in ("top", "bottom"):
        mir = side == "bottom"

        def P(x, y):
            return (X0 + S * ((W - x) if mir else x), Y0 + S * y)
        pg = Page()
        # sheet frame
        pg.stroke(width=0.5)
        pg.rect(8, 8, A3[0] - 8, A3[1] - 8)
        # grid
        pg.stroke(rgb=(0.82, 0.86, 0.95), width=0.12)
        for k in range(0, 9):
            xg = k * GRID
            if xg <= 80:
                a, b = P(xg, 0), P(xg, 160)
                pg.line((a[0], Y0 - 3), (b[0], min(b[1], Y0 + S * 152)))
        for k in range(0, 17):
            yg = k * GRID
            if yg <= 152:
                a, b = P(0, yg), P(80, yg)
                pg.line((min(a[0], b[0]) - 2, a[1]), (max(a[0], b[0]), a[1]))
        for k, col in enumerate(COLS):
            cx = P(k * GRID + GRID / 2, 0)[0]
            pg.text(cx, Y0 - 4.5, col, size=3.2, rgb=(0.2, 0.3, 0.7), anchor="c", bold=True)
        for k in range(16):
            ry = P(0, k * GRID + GRID / 2)[1]
            pg.text(X0 - 6.2 if not mir else X0 - 6.2, ry, str(k + 1), size=3.2, rgb=(0.2, 0.3, 0.7),
                    anchor="c", bold=True)
        # outline
        pg.stroke(width=0.45)
        for it in items:
            pts = arc_points(it) if it["kind"] == "arc" else [tuple(it["start"]), tuple(it["end"])]
            pg.poly([P(*q) for q in pts], close=False)
        # other-side parts: faint context only
        pg.stroke(rgb=(0.88, 0.88, 0.88), width=0.1)
        for ref, f in facts.items():
            if f["side"] != side and f["court"]:
                pg.poly([P(*q) for q in f["court"]])
        # this side
        placed = 0
        for d in index:
            if d["Side"] != side:
                continue
            f = facts[d["Ref"]]
            pg.stroke(rgb=(0.55, 0.55, 0.55), width=0.12)
            for pd in f["pads"]:
                x0, y0, x1, y1 = pd["box"]
                a, b = P(x0, y0), P(x1, y1)
                pg.rect(min(a[0], b[0]), a[1], max(a[0], b[0]), b[1])
                if pd["num"] in ("1", "A1"):
                    c = P(*pd["pos"])
                    pg.fill((0.1, 0.1, 0.1))
                    pg.circle(c[0], c[1], 0.35, fill=True, n=10)
            pg.stroke(rgb=(0.15, 0.15, 0.15), width=0.2)
            pg.poly([P(*q) for q in f["court"]])
            # label at the CPL centroid, sized to the courtyard
            cx, cy = float(d["CPL_X"]), -float(d["CPL_Y"])
            xs = [q[0] for q in f["court"]]
            ys = [q[1] for q in f["court"]]
            cw, ch = S * (max(xs) - min(xs)), S * (max(ys) - min(ys))
            n = max(1, len(d["Ref"]))
            horiz = min(cw * 0.92 / (text_width(d["Ref"], 1.0)), ch * 0.62)
            vert = min(ch * 0.92 / (text_width(d["Ref"], 1.0)), cw * 0.62)
            rot = 90 if vert > horiz * 1.25 else 0
            size = max(1.4, min(4.2, max(horiz, vert) if rot else horiz))
            c = P(cx, cy)
            pg.stroke(rgb=(0.85, 0.1, 0.1), width=0.18)
            pg.line((c[0] - 0.9, c[1]), (c[0] + 0.9, c[1]))
            pg.line((c[0], c[1] - 0.9), (c[0], c[1] + 0.9))
            pg.text(c[0], c[1], d["Ref"], size=size, rot=rot, anchor="c", bold=True)
            placed += 1
        # title / legend column
        tx = X0 + S * 80 + 6
        y = 22
        lines = [("AQROOT DEMO", 4.0, True),
                 ("REFERENCE LOCATOR - %s" % side.upper(), 3.6, True),
                 ("Release %s" % release, 3.2, True),
                 ("Board sha256:", 2.2, False), (board_sha[:32], 2.2, False), (board_sha[32:], 2.2, False),
                 ("", 2, False),
                 ("VIEW: %s" % ("BOTTOM (B.Cu), MIRRORED - AS THE" if mir else "TOP (F.Cu), NOT MIRRORED"), 2.6, True)]
        if mir:
            lines.append(("ASSEMBLER SEES IT.  Grid letters run R->L.", 2.6, True))
        lines += [("Scale %.1f : 1 on A3.  Grid = 10 mm board." % S, 2.6, False),
                  ("", 2, False),
                  ("%d FITTED parts on this side; every one" % placed, 2.6, True),
                  ("is labelled AT ITS CPL CENTROID (red +).", 2.6, True),
                  ("Placement file: aqroot-Demo-pos-fitted.csv", 2.4, False),
                  ("(JLCPCB copy: *_JLCPCB_CPL.csv).", 2.4, False),
                  ("Index: last page(s) of this file and", 2.4, False),
                  ("aqroot-Demo-assembly-ref-index.csv.", 2.4, False),
                  ("", 2, False),
                  ("LEGEND", 2.8, True),
                  ("dark outline = courtyard (this side)", 2.4, False),
                  ("grey boxes = copper lands", 2.4, False),
                  ("black dot = pad 1 / A1", 2.4, False),
                  ("red + = CPL centroid", 2.4, False),
                  ("faint outline = parts on the other side", 2.4, False),
                  ("", 2, False),
                  ("CPL frame: X right; Y UP (negative on", 2.4, False),
                  ("this board).  Board/grid frame here:", 2.4, False),
                  ("Y_down = -CPL Y.  Bottom-side Rot is", 2.4, False),
                  ("as seen from the TOP (KiCad).", 2.4, False),
                  ("", 2, False),
                  ("DNP - NOT DRAWN, DO NOT PLACE:", 2.6, True)]
        dl = sorted(dnp_refs, key=natural)
        for k in range(0, len(dl), 6):
            lines.append((" ".join(dl[k:k + 6]), 2.4, False))
        lines += [("", 2, False),
                  ("Silkscreen intentionally carries no", 2.4, False),
                  ("reference designators.  This sheet is", 2.4, False),
                  ("the authoritative reference locator.", 2.4, False),
                  ("", 2, False),
                  ("PARTS PLACEMENT CONFIRMATION IS A", 2.6, True),
                  ("REQUIRED MANUAL APPROVAL GATE.", 2.6, True)]
        for s_, sz, bold in lines:
            pg.text(tx, y, s_, size=sz, bold=bold)
            y += sz * 1.55
        pages = [pg]
        # index pages
        rows = [d for d in index if d["Side"] == side]
        per = 82
        for k0 in range(0, len(rows), per):
            ip = Page()
            ip.stroke(width=0.5)
            ip.rect(8, 8, A3[0] - 8, A3[1] - 8)
            ip.text(15, 18, "REFERENCE INDEX - %s - %s (page %d of %d)" % (
                side.upper(), release, k0 // per + 1, (len(rows) + per - 1) // per), size=3.6, bold=True)
            cols = [("Ref", 15), ("Side", 33), ("Grid", 50), ("CPL X mm", 64), ("CPL Y mm", 88),
                    ("Rot", 114), ("Value", 128), ("Package", 175)]
            yy = 27
            for name, x in cols:
                ip.text(x, yy, name, size=2.8, bold=True)
            ip.stroke(width=0.2)
            ip.line((14, yy + 1.2), (A3[0] - 14, yy + 1.2))
            yy += 5.4
            for d in rows[k0:k0 + per]:
                vals = [d["Ref"], d["Side"], d["Grid"], d["CPL_X"][:10], d["CPL_Y"][:11],
                        d["Rot"].split(".")[0], d["Value"][:24], d["Package"][:40]]
                for (name, x), v in zip(cols, vals):
                    ip.text(x, yy, v, size=2.6, bold=(name == "Ref"))
                yy += 4.6
            pages.append(ip)
        fn = out_dir / FILES[side]
        write_pdf(fn, pages, "AQROOT Demo reference locator %s %s" % (side, release))
        files[side] = dict(file=FILES[side], fitted_labelled=placed, pages=len(pages),
                           mirrored=mir, scale="%.1f" % S)
    with open(out_dir / FILES["index"], "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(index[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(index)
    return dict(release=release, board_sha256=board_sha, files=files, index=FILES["index"],
                fitted=len(index), dnp_not_drawn=sorted(dnp_refs, key=natural),
                label_anchor="CPL centroid", grid_mm=GRID)


def natural(ref):
    import re
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


# --------------------------------------------------------------------------
# board profile
# --------------------------------------------------------------------------
def profile(board, release, board_sha, out_dir, slots):
    items = outline_items(board)
    bb = board.GetBoardEdgesBoundingBox()
    box = [round(bb.GetLeft() / MM + 0.05, 3), round(bb.GetTop() / MM + 0.05, 3),
           round(bb.GetRight() / MM - 0.05, 3), round(bb.GetBottom() / MM - 0.05, 3)]
    arcs = [i for i in items if i["kind"] == "arc"]
    # an arc is an INSIDE fillet when its centre lies outside the board
    poly = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(poly, False)

    def inside(x, y):
        return poly.Contains(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))
    inside_fillets = [a for a in arcs if not inside(*a["centre"])]
    outside_corners = [a for a in arcs if inside(*a["centre"])]
    # sharp corners: line-line vertices; reflex if a point just inside the bisector is outside
    pts = {}
    for i in items:
        if i["kind"] == "line":
            for q in (tuple(i["start"]), tuple(i["end"])):
                pts[q] = pts.get(q, 0) + 1
    arc_ends = {tuple(q) for a in arcs for q in (a["start"], a["end"])}
    sharp = sorted(q for q, n in pts.items() if n == 2 and q not in arc_ends)
    sharp_inside = [q for q in sharp if sum(inside(q[0] + dx, q[1] + dy)
                                            for dx in (-0.2, 0.2) for dy in (-0.2, 0.2)) == 3]
    sharp_outside = [q for q in sharp if q not in sharp_inside]
    main_bottom = 148.0
    tabs = []
    # tabs = the outline runs ON the bbox bottom edge (below the main bottom edge)
    tab_edges = sorted([i for i in items if i["kind"] == "line" and abs(i["start"][1] - box[3]) < 1e-6
                        and abs(i["end"][1] - box[3]) < 1e-6], key=lambda i: min(i["start"][0], i["end"][0]))
    for k, e in enumerate(tab_edges):
        xa, xb = sorted((e["start"][0], e["end"][0]))
        r_out = next((a["radius"] for a in outside_corners
                      if abs(a["centre"][0] - xa) < 0.6 or abs(a["centre"][0] - xb) < 0.6), 0.0)
        tabs.append(dict(name=("J2_TAB", "J3_TAB")[k] if len(tab_edges) == 2 else "TAB%d" % k,
                         x_from=round(xa - r_out, 3), x_to=round(xb + r_out, 3),
                         width=round(xb - xa + 2 * r_out, 3), edge_y=box[3],
                         depth_below_main_edge=round(box[3] - main_bottom, 3),
                         outside_corner_radius=r_out,
                         inside_fillet_radius=next((a["radius"] for a in inside_fillets
                                                    if abs(a["centre"][0] - (xa - r_out)) < 1.1
                                                    or abs(a["centre"][0] - (xb + r_out)) < 1.1), 0.0)))
    step = dict(what="east step (bump) for SW9 / J8: board widens from x 72.000 to x 77.000",
                x_from=72.0, x_to=box[2], y_from=min(q[1] for q in sharp_inside) if sharp_inside else None,
                y_to=max(q[1] for q in sharp_inside) if sharp_inside else None)
    doc = dict(schema=1, decision="D-806", release=release, board_sha256=board_sha,
               frames=dict(kicad="X right, Y DOWN, origin KiCad page origin",
                           gerber="X right, Y UP: Y_gerber = -Y_kicad (the Gerber/Excellon/CPL frame)",
                           drawing_datum="lower-left of the bbox: X_d = X_kicad, Y_d = %.3f - Y_kicad" % box[3]),
               bbox_kicad=box, size_mm=[round(box[2] - box[0], 3), round(box[3] - box[1], 3)],
               main_bottom_edge_y_kicad=main_bottom, items=items,
               counts=dict(lines=sum(i["kind"] == "line" for i in items), arcs=len(arcs),
                           inside_fillets=len(inside_fillets), outside_corners=len(outside_corners),
                           sharp_inside_corners=len(sharp_inside), sharp_outside_corners=len(sharp_outside)),
               tabs=tabs, east_step=step,
               inside_fillets=[dict(centre=a["centre"], radius=a["radius"]) for a in inside_fillets],
               outside_corners=[dict(centre=a["centre"], radius=a["radius"]) for a in outside_corners],
               sharp_inside_corners=[list(q) for q in sharp_inside],
               sharp_outside_corners=[list(q) for q in sharp_outside],
               routed_slots=slots,
               must_not_normalise=[
                   "The outline is NOT a rectangle.  Do not straighten, square, extend or fill the bottom edge "
                   "between or beside the two tabs.",
                   "J2_TAB and J3_TAB project %.3f mm below the main bottom edge; keep both, at the stated X spans."
                   % (box[3] - main_bottom),
                   "The four r 1.000 inside fillets are DRAWN: rout them as drawn (tool radius <= 1.000 mm); do "
                   "not replace them with sharp corners or larger radii.",
                   "The four r 0.500 outside corners are drawn; keep them.",
                   "The two sharp inside corners of the east step keep the router's own retained radius "
                   "(<= 1.00 mm); NO plunge, relief or over-cut toward copper.",
                   "The east step x 72..77 is real board; do not trim it to the 72 mm main width.",
                   "The four J3 shell slots are PLATED ROUTED SLOTS (Excellon G85): do not convert them to "
                   "drilled holes.",
                   "If edge rails / a panel are added, the finished single-board outline must be exactly this "
                   "profile after depanelization."])
    (out_dir / FILES["profile_json"]).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    _profile_pdf(doc, out_dir / FILES["profile_pdf"])
    return doc


def _dim_h(pg, x0, x1, y, label, size=2.6):
    pg.stroke(width=0.15)
    pg.line((x0, y), (x1, y))
    for x in (x0, x1):
        pg.line((x, y - 1.2), (x, y + 1.2))
    pg.text((x0 + x1) / 2, y - 1.0, label, size=size, anchor="c")


def _dim_v(pg, x, y0, y1, label, size=2.6):
    pg.stroke(width=0.15)
    pg.line((x, y0), (x, y1))
    for y in (y0, y1):
        pg.line((x - 1.2, y), (x + 1.2, y))
    pg.text(x - 1.0, (y0 + y1) / 2, label, size=size, anchor="c", rot=90)


def _profile_pdf(doc, path):
    items = doc["items"]
    bx = doc["bbox_kicad"]
    S, X0, Y0 = PROFILE_SCALE, 30.0, 44.0
    yb = bx[3]

    def P(x, y):
        return X0 + S * x, Y0 + S * y
    pg = Page()
    pg.stroke(width=0.5)
    pg.rect(8, 8, A3[0] - 8, A3[1] - 8)
    pg.text(15, 18, "AQROOT DEMO - BOARD PROFILE (Edge.Cuts) - %s" % doc["release"], size=4.2, bold=True)
    pg.text(15, 23.5, "TOP VIEW, scale %.1f : 1 on A3.  All dimensions mm.  Gerber frame: Y_gerber = -Y_kicad."
            % S, size=2.6)
    pg.stroke(width=0.5)
    for it in items:
        q = arc_points(it) if it["kind"] == "arc" else [tuple(it["start"]), tuple(it["end"])]
        pg.poly([P(*p) for p in q], close=False)
    # slots
    pg.stroke(rgb=(0.1, 0.3, 0.8), width=0.3)
    for s in doc["routed_slots"]:
        (xa, ya), (xb, yb_) = s["from_kicad"], s["to_kicad"]
        r = s["width"] / 2
        a, b = P(xa, ya - r), P(xb, yb_ + r)
        pg.rect(min(a[0], b[0]) - S * r, a[1], max(a[0], b[0]) + S * r, b[1])
    # overall dimensions
    _dim_h(pg, *[P(bx[0], 0)[0], P(bx[2], 0)[0]], P(0, bx[1])[1] - 6, "%.3f overall" % (bx[2] - bx[0]))
    _dim_h(pg, P(0, 0)[0], P(72, 0)[0], P(0, bx[1])[1] - 12, "72.000 main body")
    _dim_v(pg, P(bx[0], 0)[0] - 8, P(0, bx[1])[1], P(0, bx[3])[1], "%.3f overall" % (bx[3] - bx[1]))
    _dim_v(pg, P(bx[0], 0)[0] - 15, P(0, bx[1])[1], P(0, doc["main_bottom_edge_y_kicad"])[1],
           "%.3f to main bottom edge" % doc["main_bottom_edge_y_kicad"])
    st = doc["east_step"]
    if st["y_from"] is not None:
        _dim_v(pg, P(bx[2], 0)[0] + 8, P(0, st["y_from"])[1], P(0, st["y_to"])[1],
               "east step %.3f" % (st["y_to"] - st["y_from"]))
        _dim_h(pg, P(72, 0)[0], P(bx[2], 0)[0], P(0, st["y_from"])[1] - 4, "5.000")
        pg.text(P(72, 0)[0] - 2, P(0, st["y_from"])[1] - 8,
                "step y %.3f .. %.3f (KiCad)" % (st["y_from"], st["y_to"]), size=2.2, anchor="r")
    for t in doc["tabs"]:
        _dim_h(pg, P(t["x_from"], 0)[0], P(t["x_to"], 0)[0], P(0, yb)[1] + 7,
               "%s %.3f..%.3f (w %.3f)" % (t["name"], t["x_from"], t["x_to"], t["width"]), size=2.3)
    _dim_v(pg, P(bx[2], 0)[0] + 4, P(0, doc["main_bottom_edge_y_kicad"])[1], P(0, yb)[1],
           "%.3f" % (yb - doc["main_bottom_edge_y_kicad"]), size=2.3)
    # callouts
    for f in doc["inside_fillets"]:
        c = P(*f["centre"])
        pg.stroke(rgb=(0.8, 0.1, 0.1), width=0.2)
        pg.circle(c[0], c[1], S * f["radius"] + 0.6, n=20)
    for q in doc["sharp_inside_corners"]:
        c = P(*q)
        pg.stroke(rgb=(0.8, 0.4, 0.0), width=0.3)
        pg.circle(c[0], c[1], 2.2, n=16)
        pg.text(c[0] - 3, c[1] + 0.8, "SHARP INSIDE CORNER - NO OVERCUT", size=2.0, rgb=(0.8, 0.4, 0.0), anchor="r")
    # detail views of the two tabs, dimensioned
    yd = Y0 + S * 151 + 30
    for k, t in enumerate(doc["tabs"]):
        x0 = t["x_from"] - 1.8
        ox = 24 + k * 150
        D2 = min(6.0, 112.0 / (t["width"] + 3.6))

        def Q(x, y):
            return ox + D2 * (x - x0), yd + D2 * (y - 147.0)
        pg.text(ox, yd - 9, "DETAIL %s  (scale %.1f : 1)" % (t["name"], D2), size=2.8, bold=True)
        pg.stroke(width=0.4)
        for it in items:
            pts = arc_points(it, 24) if it["kind"] == "arc" else [tuple(it["start"]), tuple(it["end"])]
            if any(x0 <= p[0] <= t["x_to"] + 1.8 for p in pts) and all(p[1] >= 147.9 for p in pts):
                pts = [(min(max(p[0], x0), t["x_to"] + 1.8), p[1]) for p in pts]
                pg.poly([Q(*p) for p in pts], close=False)
        _dim_h(pg, Q(t["x_from"], 0)[0], Q(t["x_to"], 0)[0], Q(0, t["edge_y"])[1] + 6,
               "%.3f  (X %.3f .. %.3f)" % (t["width"], t["x_from"], t["x_to"]), size=2.3)
        _dim_v(pg, Q(t["x_to"] + 1.5, 0)[0], Q(0, 148.0)[1], Q(0, t["edge_y"])[1],
               "%.3f" % t["depth_below_main_edge"], size=2.3)
        for it in items:
            if it["kind"] != "arc" or not (x0 - 0.5 <= it["centre"][0] <= t["x_to"] + 1.8):
                continue
            m = Q(*it["mid"])
            inside_f = tuple(it["centre"]) in {tuple(f["centre"]) for f in doc["inside_fillets"]}
            pg.stroke(rgb=(0.8, 0.1, 0.1) if inside_f else (0.1, 0.4, 0.1), width=0.2)
            lx = m[0] + (-7 if it["mid"][0] < it["centre"][0] else 7)
            ly = m[1] + (-6 if inside_f else 6)
            pg.line(m, (lx, ly))
            pg.text(lx, ly - (0.6 if inside_f else -2.6), ("R%.3f inside fillet" if inside_f else "R%.3f outside")
                    % it["radius"], size=2.1, rgb=(0.8, 0.1, 0.1) if inside_f else (0.1, 0.4, 0.1),
                    anchor="r" if lx < m[0] else "l")
        pg.text(ox, Q(0, t["edge_y"])[1] + 13,
                "tab edge Y %.3f, main bottom edge Y %.3f (KiCad, Y down)" % (t["edge_y"], 148.0), size=2.2)
    y = yd + 44
    pg.text(15, y, "The outline is NOT a rectangle: two bottom tabs (J2 microSD, J3 USB-C) and an east step (SW9 / J8).",
            size=2.6, bold=True)
    pg.text(15, y + 4.5, "Page 2 lists WHAT CAM MUST NOT NORMALISE and every Edge.Cuts primitive; "
            "aqroot-Demo-board-profile.json is the machine-readable copy.", size=2.4)
    c = doc["counts"]
    pg.text(15, y + 9, "Edge.Cuts: %d lines + %d arcs (%d drawn inside fillets R1.000, %d outside corners R0.500); "
            "%d sharp inside + %d sharp outside corners; %d plated routed slots."
            % (c["lines"], c["arcs"], c["inside_fillets"], c["outside_corners"], c["sharp_inside_corners"],
               c["sharp_outside_corners"], len(doc["routed_slots"])), size=2.2)
    pg.text(15, y + 13, "Board sha256 %s" % doc["board_sha256"], size=2.2)
    # page 2: coordinate table
    tp = Page()
    tp.stroke(width=0.5)
    tp.rect(8, 8, A3[0] - 8, A3[1] - 8)
    tp.text(15, 18, "BOARD PROFILE - EVERY Edge.Cuts PRIMITIVE (KiCad frame, Y down; Gerber Y = -Y)", size=3.4, bold=True)
    yy = 28
    tp.text(15, yy, "WHAT CAM MUST NOT NORMALISE", size=3.2, bold=True)
    yy += 5.5
    for s_ in doc["must_not_normalise"]:
        words, line, first = s_.split(), "", True
        for w_ in words:
            if text_width(line + " " + w_, 2.5) > A3[0] - 40:
                tp.text(18, yy, ("- " if first else "  ") + line.strip(), size=2.5)
                yy += 3.6
                line, first = "", False
            line += " " + w_
        tp.text(18, yy, ("- " if first else "  ") + line.strip(), size=2.5)
        yy += 4.6
    yy += 6
    for name, x in (("#", 15), ("kind", 24), ("start", 40), ("end", 80), ("centre", 120), ("radius", 160), ("role", 180)):
        tp.text(x, yy, name, size=2.8, bold=True)
    yy += 6
    fil = {tuple(f["centre"]) for f in doc["inside_fillets"]}
    for k, it in enumerate(items, 1):
        role = ("inside fillet (drawn)" if it.get("centre") and tuple(it["centre"]) in fil else
                "outside corner" if it["kind"] == "arc" else
                "tab edge" if abs(it["start"][1] - yb) < 1e-6 and abs(it["end"][1] - yb) < 1e-6 else "edge")
        vals = [str(k), it["kind"], "(%.3f, %.3f)" % tuple(it["start"]), "(%.3f, %.3f)" % tuple(it["end"]),
                "(%.3f, %.3f)" % tuple(it["centre"]) if it.get("centre") else "-",
                "%.3f" % it["radius"] if it.get("radius") else "-", role]
        for v, x in zip(vals, (15, 24, 40, 80, 120, 160, 180)):
            tp.text(x, yy, v, size=2.6)
        yy += 4.4
    yy += 6
    tp.text(15, yy, "PLATED ROUTED SLOTS (Excellon G85, PTH file)", size=3.0, bold=True)
    yy += 5.5
    for s in doc["routed_slots"]:
        tp.text(18, yy, "%s  width %.3f  length %.3f  centre (%.3f, %.3f) KiCad  - plated, routed, NOT a drilled hole"
                % (s["pad"], s["width"], s["length"], s["centre_kicad"][0], s["centre_kicad"][1]), size=2.6)
        yy += 4.4
    write_pdf(path, [pg, tp], "AQROOT Demo board profile %s" % doc["release"])


def board_slots(board):
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            ds = p.GetDrillSize()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and ds.x and ds.y and ds.x != ds.y:
                c = p.GetPosition()
                w, l = min(ds.x, ds.y) / MM, max(ds.x, ds.y) / MM
                vert = ds.y > ds.x
                ang = p.GetOrientationDegrees() % 180
                if abs(ang - 90) < 1e-6:
                    vert = not vert
                half = (l - w) / 2
                a = (c.x / MM, c.y / MM - half) if vert else (c.x / MM - half, c.y / MM)
                b = (c.x / MM, c.y / MM + half) if vert else (c.x / MM + half, c.y / MM)
                out.append(dict(pad="%s.%s" % (f.GetReference(), p.GetNumber()), plated=True,
                                width=round(w, 4), length=round(l, 4),
                                centre_kicad=[round(c.x / MM, 4), round(c.y / MM, 4)],
                                from_kicad=[round(a[0], 4), round(a[1], 4)],
                                to_kicad=[round(b[0], 4), round(b[1], 4)]))
    out.sort(key=lambda s: (s["centre_kicad"][0], s["centre_kicad"][1]))
    return out


def build(board_path, cpl_fitted, cpl_all, release, out_dir):
    board = pcbnew.LoadBoard(str(board_path))
    bsha = sha256(board_path)
    fit = read_cpl(cpl_fitted)
    allr = read_cpl(cpl_all)
    dnp = sorted({r["Ref"] for r in allr} - {r["Ref"] for r in fit}, key=natural)
    loc = locator(board, fit, dnp, release, bsha, Path(out_dir))
    prof = profile(board, release, bsha, Path(out_dir), board_slots(board))
    return dict(locator=loc, profile=dict(pdf=FILES["profile_pdf"], json=FILES["profile_json"],
                                          counts=prof["counts"], tabs=prof["tabs"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, required=True)
    ap.add_argument("--cpl", type=Path, required=True)
    ap.add_argument("--all-cpl", type=Path, required=True)
    ap.add_argument("--release", required=True)
    ap.add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    print(json.dumps(build(a.board, a.cpl, a.all_cpl, a.release, a.out), indent=1))


if __name__ == "__main__":
    main()
