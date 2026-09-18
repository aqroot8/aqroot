#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- review the fabrication package against the board it claims.

`export_fab_package.py` runs the tools a factory runs.  This file is the
review: it opens the SHIPPED artifacts as a stranger would, re-derives what
they assert from the authoritative board and the schematic, and reports where
the two disagree.  It never reads the exporter's intentions -- only its output.

D-612's lesson is the design rule here: **measure the consequence, not the
flag**.  So the drill claim is not "a drill file exists", it is "every hole in
this Excellon file is a hole in the board and every hole in the board is in the
file, at the same coordinate, to the micron".  The position claim is not "the
CPL has rows", it is "every row places the part where `pcbnew` says it is".

  FAB1  PROVENANCE   the manifest names the AUTHORITATIVE board sha256, and
                     every artifact on disk still hashes to what the manifest
                     recorded -- nothing was hand-edited after generation.
  FAB2  FILL         the committed board is BYTE-IDENTICAL after
                     `--refill-zones --save-board`, so the copper these Gerbers
                     plot is the copper the promotion gate ran DRC on.  Gerber
                     export does not refill; a stale stored fill would ship
                     copper no check in this repository has ever seen.
  FAB3  LAYERS       the shipped copper Gerbers are exactly the board's enabled
                     copper layers, in stackup order; the `.gbrjob` agrees;
                     both masks, both pastes, both silkscreens and the profile
                     are present; and no shipped layer file is empty of
                     graphics.
  FAB4  DRILL        the PTH + NPTH hole multiset EQUALS the board's own
                     (`pcbnew` vias + pad drills), matched on plating,
                     position, diameter and slot end-points.  The pairing is a
                     BIJECTION within one micron, not a sorted zip: the file
                     quantises to three decimals and quantisation may REVERSE
                     the order of two holes it collapses onto one coordinate
                     (D-625).  What the quantisation costs is reported --
                     `max_residual_nm` and a full residual histogram -- and the
                     matcher proves it can refuse by displacing one shipped
                     hole past the tolerance in a control.
  FAB5  CPL          `pos-fitted` rows are exactly the fitted, placeable board
                     references -- no DNP part survives, no fitted part is
                     dropped -- and every row's X/Y/side matches `pcbnew`.
  FAB6  BOM          every fitted BOM-eligible reference appears exactly once;
                     no reference is in both the fitted BOM and the
                     do-not-populate list; the BOARD and the SCHEMATIC agree on
                     which references are BOM lines at all; and no single part
                     identity (MPN or LCSC) is used on two different footprints.
  FAB7  SOURCING     every fitted, BOM-eligible, on-board reference carries an
                     orderable identity -- a manufacturer part number or an
                     LCSC code.  A line a supplier cannot quote is not a
                     finished BOM.
  FAB8  OUTLINE      the `Edge.Cuts` Gerber's profile is the board's own
                     outline: same extent, to the micron.
  FAB9  VIA-IN-PAD   every via whose drilled hole opens into a solderable land
                     is named in the package, and the notes state the fill/cap
                     process those lands require.  KiCad has no rule for this
                     and the vias are same-net, so nothing else can see them.
  FAB10 VIA GEOMETRY every via below the board's OWN `.kicad_dru` annular-ring
                     floor or below its board-setup minimum via diameter is
                     named in the package and the notes ASK the fabricator to
                     confirm it.  DRC passes them on an internal licence; a
                     concession nobody was asked about is not a concession.
  FAB11 MASK DAMS    every solder-mask web below the package's stated floor is
                     named in the package.  `solder_mask_min_width` is 0.000 mm
                     on this board, so KiCad's `solder_mask_bridge` test is OFF
                     and a clean DRC report carries no information here.

Read-only.  `hardware/demo/kicad/aqroot-demo/` is copied to a temporary
directory before the refill test touches anything.

`--provenance-only` runs FAB1 and nothing else -- no `pcbnew` board load, no
`kicad-cli` refill -- so the package's provenance can be re-asked on every
promotion from `contract_regression.py` instead of once per release.  FAB2-FAB8
remain the release review.  D-666.

    python3 hardware/demo/manufacturing/checks/fab_package_contract.py \
        [--package DIR] [-o OUT] [--provenance-only]
"""

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE.parent)]

import routing_ledger as rl                                # noqa: E402
import pcbnew                                              # noqa: E402

PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
PACKAGE = ROOT / "hardware/demo/fab"

# One micron.  Every geometric comparison in this file is exact to this, which
# is the resolution the Excellon and Gerber files were written at.
TOL_NM = 1000

REQUIRED_NON_COPPER = {"F_Paste", "B_Paste", "F_Silkscreen", "B_Silkscreen",
                       "F_Mask", "B_Mask", "Edge_Cuts"}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# --------------------------------------------------------------------------
# the board's own answers


def board_facts():
    b = pcbnew.LoadBoard(str(BOARD))
    copper = [b.GetLayerName(l) for l in b.GetEnabledLayers().CuStack()]

    holes = Counter()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetStart()
            holes[("P", p.x, p.y, t.GetDrill(), t.GetDrill())] += 1
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            d = pad.GetDrillSize()
            if d.x == 0 and d.y == 0:
                continue
            plated = "N" if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "P"
            p = pad.GetPosition()
            holes[(plated, p.x, p.y, min(d.x, d.y), max(d.x, d.y))] += 1

    placeable, bom_excluded, dnp_attr, geometry = set(), set(), set(), {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        attrs = fp.GetAttributes()
        if fp.IsDNP():
            dnp_attr.add(ref)
        if attrs & pcbnew.FP_EXCLUDE_FROM_BOM:
            bom_excluded.add(ref)
        if not (attrs & pcbnew.FP_EXCLUDE_FROM_POS_FILES):
            placeable.add(ref)
        pos = fp.GetPosition()
        # D-750.  ROTATION IS PART OF A PLACEMENT.  Before D-750 this tuple was
        # (x, y, side) and FAB5 compared only those three, so a CPL row with a
        # 180-degrees-wrong rotation on a polarised part passed the release
        # gate -- a scrapped board that every check in this repository called
        # correct.  The convention is measured, not assumed: on the released
        # package all 262 rows satisfy `Rot == GetOrientationDegrees()`
        # normalised to (-180, 180], on BOTH sides.
        rot = ((fp.GetOrientationDegrees() + 180.0) % 360.0) - 180.0
        geometry[ref] = (pos.x, pos.y, "bottom" if fp.IsFlipped() else "top",
                         round(rot, 3), fp.GetFPIDAsString())

    poly = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(poly, False)
    box = poly.BBox()
    outline = (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom())

    # D-750.  FAB12 needs the PHYSICAL shape of every land pattern, because
    # the J5 defect was a BOM row whose own words -- "2x12 24-contact 2.54 mm"
    # -- contradicted the footprint it shipped on, which is one row of 24.
    # Nothing in this file could see that, because every other check asks only
    # whether the package is INTERNALLY consistent.
    lands = {}
    for fp in b.GetFootprints():
        xs, ys, pts, pad_area = set(), set(), [], []
        for pad in fp.Pads():
            n = pad.GetNumber()
            if not n or not n.strip():
                continue                      # unnamed mechanical land
            sz = pad.GetSize()
            pad_area.append(sz.x / 1e6 * sz.y / 1e6)
            q = pad.GetPosition() - fp.GetPosition()
            # de-rotate into the footprint's own frame
            th = math.radians(fp.GetOrientationDegrees())
            lx = q.x * math.cos(th) - q.y * math.sin(th)
            ly = q.x * math.sin(th) + q.y * math.cos(th)
            xs.add(round(lx / 1e3)); ys.add(round(ly / 1e3))
            pts.append((lx / 1e6, ly / 1e6))
        if not pts:
            continue
        pitch = None
        for axis in (0, 1):
            vals = sorted({round(v[axis], 3) for v in pts})
            gaps = [round(b_ - a_, 4) for a_, b_ in zip(vals, vals[1:])]
            gaps = [g for g in gaps if g > 0.05]
            if gaps:
                cand = min(gaps)
                pitch = cand if pitch is None else min(pitch, cand)
        # A DATASHEET PIN COUNT EXCLUDES THE THERMAL PAD.  `U11` is a
        # "10-pin WSON" with eleven numbered lands, `U12` a "14-pin VSON"
        # with fifteen and `U14` an "8-pin TDFN" with nine; a contact-count
        # claim must be allowed to mean either.  The exposed pad is found by
        # AREA, not by number: it is several times the size of a signal land.
        areas = sorted(a for a in pad_area if a > 0)
        med = areas[len(areas) // 2] if areas else 0.0
        ep = sum(1 for a in pad_area if med and a > 3.0 * med)
        lands[fp.GetReference()] = dict(
            pads=len(pts), pads_without_exposed_pad=len(pts) - ep,
            exposed_pads=ep,
            distinct_x=len(xs), distinct_y=len(ys),
            rows=min(len(xs), len(ys)), cols=max(len(xs), len(ys)),
            pitch_mm=(round(pitch, 4) if pitch else None),
            footprint=fp.GetFPIDAsString())

    return dict(copper=copper, holes=holes, placeable=placeable,
                bom_excluded=bom_excluded, dnp_attr=dnp_attr,
                geometry=geometry, refs=set(geometry), outline=outline,
                lands=lands)


# --------------------------------------------------------------------------
# the package's answers


def read_excellon(path, plated):
    """Hole multiset from one Excellon file, in nanometres, board coordinates.

    The file is metric/decimal/absolute, and Excellon's Y axis points the other
    way from `pcbnew`'s, which is the whole of the conversion.  `G85` is a
    slot: two end-points at the tool diameter, which is the board's oval pad
    drill seen edge on.
    """
    tools, holes, current = {}, Counter(), None
    coord = re.compile(r"X(-?[\d.]+)Y(-?[\d.]+)")
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line.startswith(";"):
            continue
        m = re.fullmatch(r"T(\d+)C([\d.]+)", line)
        if m:
            tools[int(m.group(1))] = round(float(m.group(2)) * 1e6)
            continue
        m = re.fullmatch(r"T(\d+)", line)
        if m:
            current = tools.get(int(m.group(1)))
            continue
        if not line.startswith("X") or current is None:
            continue
        pts = [(round(float(x) * 1e6), -round(float(y) * 1e6))
               for x, y in coord.findall(line)]
        if len(pts) == 1:
            holes[(plated, pts[0][0], pts[0][1], current, current)] += 1
        elif len(pts) == 2:
            (x1, y1), (x2, y2) = pts
            span = max(abs(x2 - x1), abs(y2 - y1)) + current
            holes[(plated, (x1 + x2) // 2, (y1 + y2) // 2, current, span)] += 1
    return holes


def gerber_extent(path):
    """Bounding box of every coordinate in a Gerber, in board nanometres."""
    text = Path(path).read_text()
    fmt = re.search(r"%FSLAX(\d)(\d)Y(\d)(\d)\*%", text)
    scale = 10 ** (6 - int(fmt.group(2))) if fmt else 1
    xs, ys, ops = [], [], 0
    for m in re.finditer(r"X(-?\d+)Y(-?\d+)D0([123])", text):
        xs.append(int(m.group(1)) * scale)
        ys.append(-int(m.group(2)) * scale)
        ops += 1
    if not xs:
        return None, 0
    return (min(xs), min(ys), max(xs), max(ys)), ops


def gerber_is_drawn(path):
    """Does this layer file actually carry graphics, or only a header?"""
    text = Path(path).read_text()
    return bool(re.search(r"D0[13]\*", text)) and "%AD" in text


def read_csv(path):
    return list(csv.DictReader(Path(path).open(newline="",
                                               encoding="utf-8-sig")))


def expand(cell):
    return rl.expand_refs(cell)


# --------------------------------------------------------------------------
# claims


def fab1(pkg, manifest):
    board_sha = sha256(BOARD)
    drift = []
    for entry in manifest["files"]:
        path = pkg / entry["path"]
        if not path.exists():
            drift.append(dict(path=entry["path"], why="missing"))
        elif sha256(path) != entry["sha256"]:
            drift.append(dict(path=entry["path"], why="sha256 differs"))
    stray = sorted(str(p.relative_to(pkg)) for p in pkg.rglob("*")
                   if p.is_file() and p.name != "MANIFEST.json"
                   and str(p.relative_to(pkg)) not in
                   {e["path"] for e in manifest["files"]})
    # The BOM views come out of the WHOLE schematic hierarchy, so provenance
    # that names only the root sheet does not cover the package's own output.
    sheets = {s.name: sha256(s) for s in sorted(BOARD.parent.glob("*.kicad_sch"))}
    recorded = manifest["source"].get("schematic_sheet_sha256")
    sheet_drift = ([] if recorded == sheets else
                   sorted(set(sheets) ^ set(recorded or {}))
                   or sorted(k for k in sheets
                             if (recorded or {}).get(k) != sheets[k]))
    return dict(ok=(manifest["source"]["board_sha256"] == board_sha
                    and recorded == sheets and not drift and not stray),
                authoritative_board_sha256=board_sha,
                manifest_board_sha256=manifest["source"]["board_sha256"],
                kicad=manifest["kicad"],
                artifacts=len(manifest["files"]),
                deterministic=sum(f["deterministic"] for f in manifest["files"]),
                schematic_sheets=len(sheets),
                schematic_sheet_drift=sheet_drift,
                drift=drift, unmanifested=stray)


def fab2():
    """Refill a COPY and compare bytes.  Gerber export plots the stored fill."""
    before = sha256(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-fill-") as tmp:
        tmp = Path(tmp)
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            src = BOARD.with_suffix(suffix)
            if src.exists():
                shutil.copy2(src, tmp / src.name)
        copy = tmp / BOARD.name
        subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones",
                        "--save-board", "--format", "json",
                        "-o", str(tmp / "drc.json"), str(copy)],
                       capture_output=True, text=True)
        after = sha256(copy)
    return dict(ok=before == after, before=before, after=after,
                note="Gerber export does not refill; a stale stored fill would "
                     "ship copper the gate never inspected")


def fab3(pkg, board):
    gerbers = pkg / "gerbers"
    shipped = {p.stem.split("-")[-1]: p for p in gerbers.glob("*.gbr")}
    want_copper = [c.replace(".", "_") for c in board["copper"]]
    have_copper = [n for n in want_copper if n in shipped]
    job = next(gerbers.glob("*.gbrjob"), None)
    job_layers = []
    if job:
        doc = json.loads(job.read_text())
        job_layers = [f["Path"].rsplit("-", 1)[-1].removesuffix(".gbr")
                      for f in doc.get("FilesAttributes", [])]
    empty = sorted(n for n, p in shipped.items() if not gerber_is_drawn(p))
    missing_nc = sorted(REQUIRED_NON_COPPER - set(shipped))
    return dict(ok=(have_copper == want_copper
                    and not missing_nc and not empty
                    and set(job_layers) == set(shipped)),
                board_copper_stackup=board["copper"],
                shipped_copper=have_copper,
                missing_non_copper=missing_nc,
                gbrjob_layers=sorted(job_layers),
                shipped_layers=sorted(shipped),
                empty_layer_files=empty)


def pair_within_tolerance(bs, fs, tol=None):
    """A BIJECTION, not an ordering.  Returns (pairs, unmatched_board,
    unmatched_file).

    D-625.  The old code sorted both sides and zipped them, which is a correct
    pairing only while the quantisation the Excellon file applies PRESERVES
    SORT ORDER.  It does not have to.  The board holds two `0.300 mm` barrels
    at `x = 64.100000` and `x = 64.100500 mm`; the file, written in millimetres
    to three decimals, prints BOTH as `X64.1`, and their `y` order is the
    reverse of the board's.  Sorted and zipped, each is paired with the OTHER
    and the report claims a 2.178 mm displacement that does not exist.

    The claim FAB4 has always MADE is a claim about existence -- "every hole in
    the board is in the file, at the same coordinate, to the micron" -- so it
    is asked here as existence: is there a perfect matching in the bipartite
    graph whose edges are the pairs within `tol`?  Kuhn's augmenting path over
    a `tol`-bucketed neighbour index answers it exactly.  Candidate lists are
    near-singleton at a one-micron tolerance, so this is linear in practice and
    NEVER order-dependent.
    """
    tol = TOL_NM if tol is None else tol
    bucket = defaultdict(list)
    # `widest_candidate_list` is returned so the caller can say whether the
    # matching was CHOSEN or FORCED.  On this board every hole has exactly one
    # partner within a micron, so there is only one bijection to find and the
    # verdict cannot depend on which one an algorithm happened to reach.
    for j, (fx, fy) in enumerate(fs):
        bucket[(fx // tol, fy // tol)].append(j)
    cand = []
    for bx, by in bs:
        near = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near += bucket.get((bx // tol + dx, by // tol + dy), [])
        cand.append(sorted(j for j in near
                           if abs(bx - fs[j][0]) <= tol
                           and abs(by - fs[j][1]) <= tol))

    owner = [-1] * len(fs)

    def augment(i, seen):
        for j in cand[i]:
            if j in seen:
                continue
            seen.add(j)
            if owner[j] == -1 or augment(owner[j], seen):
                owner[j] = i
                return True
        return False

    unmatched_b = [i for i in range(len(bs)) if not augment(i, set())]
    pairs = [(i, j) for j, i in enumerate(owner) if i != -1]
    unmatched_f = [j for j, i in enumerate(owner) if i == -1]
    return pairs, unmatched_b, unmatched_f, max((len(c) for c in cand),
                                                default=0)


def fab4(pkg, board):
    gerbers = pkg / "gerbers"
    pth = next(gerbers.glob("*-PTH.drl"), None)
    npth = next(gerbers.glob("*-NPTH.drl"), None)
    shipped = Counter()
    if pth:
        shipped += read_excellon(pth, "P")
    if npth:
        shipped += read_excellon(npth, "N")
    want = board["holes"]

    # Group both sides by (plating, diameter, slot span), then MATCH each group
    # within one micron.  The Excellon file is written in millimetres to three
    # decimals, so a hole the board holds at 17.298200 mm is printed 17.298;
    # the claim is equality TO THE MICRON, the resolution the file itself has,
    # not to the nanometre the board is stored at.  What that quantisation
    # COSTS is now published rather than implied: `residual_histogram_nm` is
    # every matched pair's Chebyshev distance and `max_residual_nm` its worst.
    # On this board 819 holes are exact and the rest are sub-micron -- a
    # standing property of a 33.3 um router lattice printed on a 1 um grid, not
    # something any one route introduced.
    def group(counter):
        out = defaultdict(list)
        for (plated, x, y, dmin, dmax), n in counter.items():
            out[(plated, dmin, dmax)].extend([(x, y)] * n)
        return {k: sorted(v) for k, v in out.items()}

    gb, gf = group(want), group(shipped)

    def survey(gb, gf):
        count_mismatch, unmatched, residuals = [], [], Counter()
        choices = 0
        for key in sorted(set(gb) | set(gf)):
            bs, fs = gb.get(key, []), gf.get(key, [])
            if len(bs) != len(fs):
                count_mismatch.append(dict(tool=key, board=len(bs),
                                           file=len(fs)))
                continue
            pairs, ub, uf, widest = pair_within_tolerance(bs, fs)
            choices = max(choices, widest)
            for i, j in pairs:
                residuals[max(abs(bs[i][0] - fs[j][0]),
                              abs(bs[i][1] - fs[j][1]))] += 1
            for i in ub:
                unmatched.append(dict(tool=key, side="board", at=bs[i]))
            for j in uf:
                unmatched.append(dict(tool=key, side="file", at=fs[j]))
        return count_mismatch, unmatched, residuals, choices

    count_mismatch, unmatched, residuals, widest = survey(gb, gf)

    # NON-VACUITY.  A matcher that pairs everything is worth nothing unless it
    # can REFUSE.  Displace one shipped hole by one nanometre past the
    # tolerance and require the survey to report it -- on BOTH sides, since a
    # hole that moved leaves a board hole unmatched and a file hole unmatched.
    control = dict(ran=False)
    ctl_key = next((k for k in sorted(gf) if gf[k]), None)
    if ctl_key is not None:
        moved = dict(gf)
        x, y = gf[ctl_key][0]
        moved[ctl_key] = sorted([(x, y + TOL_NM + 1)] + gf[ctl_key][1:])
        c_mismatch, c_unmatched, _, _ = survey(gb, moved)
        control = dict(ran=True, tool=list(ctl_key), moved_by_nm=TOL_NM + 1,
                       displaced_hole=[x, y],
                       count_mismatch=c_mismatch,
                       unmatched=len(c_unmatched),
                       fires=bool(c_unmatched) and not c_mismatch)

    diameters = sorted({k[3] for k in shipped})
    return dict(ok=(bool(shipped) and not count_mismatch and not unmatched
                    and control.get("fires") is True
                    and sum(want.values()) == sum(shipped.values())),
                board_holes=sum(want.values()),
                shipped_holes=sum(shipped.values()),
                plated=sum(v for k, v in shipped.items() if k[0] == "P"),
                unplated=sum(v for k, v in shipped.items() if k[0] == "N"),
                slots=sum(v for k, v in shipped.items() if k[3] != k[4]),
                tools=len(gf),
                min_drill_mm=min(diameters) / 1e6 if diameters else None,
                tool_count_mismatch=count_mismatch,
                unmatched_holes=unmatched[:20],
                max_residual_nm=max(residuals) if residuals else None,
                residual_histogram_nm={str(k): v
                                       for k, v in sorted(residuals.items())},
                tolerance_nm=TOL_NM,
                widest_candidate_list=widest,
                control=control,
                tool_census={"%s %.3f%s" % (k[0], k[1] / 1e6,
                                            "" if k[1] == k[2]
                                            else "x%.3f" % (k[2] / 1e6)): len(v)
                             for k, v in sorted(gf.items())})


ROT_TOL_DEG = 0.01


def _fab5_survey(board, name, rows):
    """Geometry verdict for ONE placement file: every row placed where the
    board says, at the rotation the board says, exactly once."""
    misplaced = []
    seen = Counter(r["Ref"] for r in rows)
    duplicated = ["%s:%s x%d" % (name, r, n)
                  for r, n in sorted(seen.items()) if n > 1]
    for row in rows:
        want = board["geometry"].get(row["Ref"])
        if want is None:
            misplaced.append(dict(file=name, ref=row["Ref"],
                                  why="not on board"))
            continue
        x = round(float(row["PosX"]) * 1e6)
        y = -round(float(row["PosY"]) * 1e6)
        rot = ((float(row["Rot"]) + 180.0) % 360.0) - 180.0
        why = []
        if abs(x - want[0]) > TOL_NM or abs(y - want[1]) > TOL_NM:
            why.append("position")
        if row["Side"] != want[2]:
            why.append("side")
        if abs(((rot - want[3] + 180.0) % 360.0) - 180.0) > ROT_TOL_DEG:
            why.append("rotation")
        if why:
            misplaced.append(dict(file=name, ref=row["Ref"],
                                  why="/".join(why),
                                  file_row=(x, y, row["Side"], rot),
                                  board=list(want[:4])))
    return misplaced, duplicated


def fab5(pkg, board, fitted, dnp):
    """Every placement row places the part where the board says, at the
    ROTATION the board says, exactly once.

    D-750 strengthened this on an external review's negative controls.  The
    old form compared X/Y/side only, and compared reference SETS, so three
    different corruptions passed: a wrong rotation, a duplicated row, and a
    corrupted `pos-fitted` file (only `pos-all` was ever geometry-checked).

    D-751 ADDS THE CONTROLS.  A strengthened comparator that is never shown
    to REFUSE anything is indistinguishable from a comparator with a typo in
    it, and this one was written against defects nobody could reproduce on
    the released package -- every row is correct, so every clause passes
    vacuously.  The three corruptions the review named are therefore
    injected into a COPY of the real rows and each must be refused."""
    rows_all = read_csv(pkg / "aqroot-Demo-pos-all.csv")
    rows_fit = read_csv(pkg / "aqroot-Demo-pos-fitted.csv")
    refs_fit = {r["Ref"] for r in rows_fit}
    expect = {r for r in board["placeable"] if r not in board["dnp_attr"]}
    misplaced, duplicated = [], []
    for name, rows in (("pos-all", rows_all), ("pos-fitted", rows_fit)):
        m, d = _fab5_survey(board, name, rows)
        misplaced += m
        duplicated += d

    # NON-VACUITY.  Each control mutates ONE field of ONE row of the REAL
    # `pos-fitted` file and asks this same comparator; a control that is not
    # refused means the clause it exercises is not doing anything.
    controls = {}
    if rows_fit:
        def refused(rows, key=None):
            m, d = _fab5_survey(board, "control", rows)
            if key == "duplicate":
                return bool(d)
            return bool(m)
        r = [dict(x) for x in rows_fit]
        r[0]["Rot"] = "%.4f" % (float(r[0]["Rot"]) + 180.0)
        controls["rotation_180"] = refused(r)
        r = [dict(x) for x in rows_fit]
        r[0]["PosX"] = "%.4f" % (float(r[0]["PosX"]) + 10.0)
        controls["position_plus_10mm"] = refused(r)
        r = [dict(x) for x in rows_fit]
        r[0]["Side"] = "bottom" if r[0]["Side"] == "top" else "top"
        controls["side_flipped"] = refused(r)
        r = [dict(x) for x in rows_fit] + [dict(rows_fit[0])]
        controls["duplicate_fitted_row"] = refused(r, "duplicate")

    return dict(ok=(refs_fit == expect
                    and {r["Ref"] for r in rows_all} == board["placeable"]
                    and not misplaced and not duplicated
                    and bool(controls) and all(controls.values())),
                rows_all=len(rows_all), rows_fitted=len(rows_fit),
                board_placeable=len(board["placeable"]),
                dnp_still_placed=sorted(refs_fit & dnp),
                fitted_dropped=sorted(expect - refs_fit),
                unexpected_rows=sorted(refs_fit - expect),
                duplicated_rows=duplicated,
                controls_refused=controls,
                checks="position, side and ROTATION, on BOTH placement files,"
                       " with per-file reference uniqueness and four live"
                       " negative controls (D-750, controls D-751)",
                misplaced=misplaced[:20])



# --------------------------------------------------------------------------
# FAB12 -- D-750.  DOES THE BOM ROW DESCRIBE THE PART IT SHIPS ON?
#
# Every other check in this file asks whether the package is INTERNALLY
# consistent: the CPL agrees with the board, the BOM views partition the
# schematic, the manifest hashes match.  All of that was TRUE of the release
# that shipped `J5` as "Samtec BCS-112-S-D-HE 2x12 24-contact 2.54 mm female
# horizontal pass-through socket strip" against a footprint that is ONE ROW OF
# TWENTY-FOUR.  A consistently regenerated wrong identity is invisible to a
# consistency check, and that is the class of defect this closes.
#
#   FAB12a  THE ROW'S OWN WORDS vs THE LAND PATTERN.  A description or MPN
#           that states a row x column geometry, a contact count or a pitch is
#           a CLAIM ABOUT COPPER, and the copper is right here.  A claim that
#           contradicts the footprint's own pads FAILS.
#   FAB12b  CRITICAL IDENTITIES ARE PINNED BY NAME.  A curated table of the
#           references whose package identity is load-bearing -- every
#           connector, every converter, every radio, the fuel gauge, the
#           charger, the microphone -- each with the MPN and the footprint the
#           authoritative documents name.  This is a REGRESSION pin, not an
#           independent truth: it cannot find a wrong identity that was wrong
#           when the table was written, which is exactly why FAB12a exists
#           beside it.
# --------------------------------------------------------------------------
CRITICAL_IDENTITY = Path(__file__).resolve().parent.parent / \
    "evidence/d750-critical-identity.json"

_GEOM = re.compile(r"(?<![\d.])(\d{1,3})\s*[xX\u00d7]\s*(\d{1,3})(?![\d.])")
_COUNT = re.compile(r"(?<![\d.])(\d{1,3})[\s-]*(?:contact|position|pos\b|pin)",
                    re.I)
_PITCH = re.compile(r"([\d.]+)\s*mm\s*pitch|pitch\s*([\d.]+)\s*mm", re.I)


def _fab12a_scan(views, lands):
    """FAB12a: every BOM row's OWN WORDS against the pads it ships on."""
    contradictions, examined = [], 0
    for view, rows in sorted(views.items()):
        for row in rows:
            text = " ".join(filter(None, (row.get("Description"),
                                          row.get("MPN"), row.get("Value"))))
            for ref in sorted(expand(row["Refs"])):
                land = lands.get(ref)
                if land is None:
                    continue
                examined += 1
                claims = []
                for m in _GEOM.finditer(text):
                    a, b_ = int(m.group(1)), int(m.group(2))
                    if not (1 <= a <= 100 and 1 <= b_ <= 100):
                        continue
                    if a * b_ != land["pads"]:
                        continue        # not a pin-field claim; e.g. "3.5 x 2"
                    claims.append(("geometry", "%dx%d" % (a, b_),
                                   sorted((a, b_)),
                                   sorted((land["rows"], land["cols"]))))
                for m in _COUNT.finditer(text):
                    n = int(m.group(1))
                    ok_counts = {land["pads"],
                                 land["pads_without_exposed_pad"]}
                    if n not in ok_counts and 2 <= n <= 200:
                        claims.append(("contacts", n, n,
                                       sorted(ok_counts)))
                for m in _PITCH.finditer(text):
                    v = float(m.group(1) or m.group(2))
                    if land["pitch_mm"] and abs(v - land["pitch_mm"]) > 0.05 * v:
                        claims.append(("pitch", v, v, land["pitch_mm"]))
                for kind, said, want, got in claims:
                    if want != got:
                        contradictions.append(dict(
                            view=view, ref=ref, kind=kind, row_says=said,
                            row_value=want, footprint_value=got,
                            footprint=land["footprint"],
                            text=text[:160]))
    return contradictions, examined


def _fab12b_drift(views, lands, pinned):
    """FAB12b: the curated identity pin, against BOM row AND board."""
    drift = []
    seen = {}
    for rows in views.values():
        for row in rows:
            for ref in expand(row["Refs"]):
                seen[ref] = row
    for ref, want in sorted(pinned.items()):
        row = seen.get(ref)
        if row is None:
            drift.append(dict(ref=ref, why="no BOM row"))
            continue
        got = dict(MPN=(row.get("MPN") or "").strip(),
                   Footprint=(row.get("Footprint") or "").strip(),
                   Value=(row.get("Value") or "").strip())
        for key in ("MPN", "Footprint", "Value"):
            if want.get(key) is not None and got[key] != want[key]:
                drift.append(dict(ref=ref, field=key,
                                  pinned=want[key], package=got[key]))
        land = lands.get(ref)
        if land and want.get("Footprint") not in (None, land["footprint"]):
            drift.append(dict(ref=ref, field="board_footprint",
                              pinned=want["Footprint"],
                              board=land["footprint"]))
    return drift


def fab12(pkg, board):
    views = {name: read_csv(pkg / ("aqroot-Demo-%s.csv" % name))
             for name in ("BOM-assembly", "BOM-full", "DO-NOT-POPULATE",
                          "NON-PURCHASED", "OFF-BOARD")}
    lands = board["lands"]
    contradictions, examined = _fab12a_scan(views, lands)
    pinned, drift, unpinned = {}, [], []
    if CRITICAL_IDENTITY.exists():
        pinned = json.loads(CRITICAL_IDENTITY.read_text())["identities"]
        drift = _fab12b_drift(views, lands, pinned)
    else:
        unpinned.append(str(CRITICAL_IDENTITY))

    # NON-VACUITY -- D-751.  On a CORRECTED package both halves of FAB12 pass
    # with empty lists, which is exactly the shape a broken check has.  The
    # controls put the DEFECT BACK: `J5` is restored to the superseded
    # BCS-112-S-D-HE 2x12 identity that survived eight months of gates, and
    # both halves must refuse it -- FAB12a because "2x12" contradicts a
    # one-row-of-24 land pattern, FAB12b because the MPN is not the pinned
    # one.  A third control moves a footprint, which only the board-side
    # clause can see.
    controls = {}
    if pinned and "J5" in pinned and "J5" in lands:
        def mutate(field, value):
            out = {}
            for name, rows in views.items():
                new_rows = []
                for row in rows:
                    if "J5" in expand(row["Refs"]):
                        row = dict(row)
                        row[field] = value
                    new_rows.append(row)
                out[name] = new_rows
            return out
        bad = mutate("Description",
                     "2x12 24-contact 2.54 mm female pass-through socket strip")
        controls["fab12a_refuses_2x12_on_a_1x24_land"] = \
            bool(_fab12a_scan(bad, lands)[0])
        bad = mutate("MPN", "BCS-112-S-D-HE")
        controls["fab12b_refuses_superseded_j5_mpn"] = \
            bool(_fab12b_drift(bad, lands, pinned))
        bad = mutate("Footprint", "AQROOT_Beta:Samtec_BCS-112-S-D-HE")
        controls["fab12b_refuses_footprint_the_board_does_not_carry"] = \
            bool(_fab12b_drift(bad, lands, pinned))

    return dict(ok=(not contradictions and not drift and not unpinned
                    and bool(controls) and all(controls.values())),
                rows_examined=examined,
                critical_identities=len(pinned),
                contradictions=contradictions[:30],
                contradiction_count=len(contradictions),
                identity_drift=drift[:30],
                missing_pin_file=unpinned,
                controls_refused=controls,
                method="FAB12a: the row's stated geometry/contact-count/pitch "
                       "against the footprint's own pads.  FAB12b: a curated "
                       "pin of the identities whose package is load-bearing "
                       "(D-750); three live negative controls that put the J5 "
                       "defect back (D-751)")

def fab6(pkg, board, fitted, dnp):
    """The four BOM views must PARTITION the schematic, exactly once each."""
    views = {name: read_csv(pkg / ("aqroot-Demo-%s.csv" % name))
             for name in ("BOM-assembly", "DO-NOT-POPULATE",
                          "NON-PURCHASED", "OFF-BOARD")}
    refs = {}
    counted = Counter()
    for name, rows in views.items():
        got = set()
        for row in rows:
            got |= expand(row["Refs"])
            counted.update(expand(row["Refs"]))
        refs[name] = got

    duplicated = sorted(r for r, n in counted.items() if n > 1)
    every = fitted | dnp
    unpartitioned = sorted(every - set().union(*refs.values()))
    invented = sorted(set().union(*refs.values()) - every)

    assembly = refs["BOM-assembly"]
    built = {r for r in board["refs"] if r not in board["dnp_attr"]}
    # An assembly line for a part the board does not build, or a built,
    # purchased part with no line, is a package the factory cannot reconcile.
    not_built = sorted(assembly - built)
    missing = sorted(built - board["bom_excluded"] - assembly)
    # The board's own "not a purchased part" attribute must EXPLAIN the
    # non-purchased view exactly; a new divergence fails here.
    mismatched_non_purchased = sorted(
        refs["NON-PURCHASED"] ^ (board["bom_excluded"] & every))
    wrong_dnp = sorted(refs["DO-NOT-POPULATE"] ^ dnp)

    # One orderable identity, one footprint.  Reusing a part number across two
    # packages is a part that cannot be placed on one of them.
    identity = defaultdict(set)
    for rows in views.values():
        for row in rows:
            for key in ("MPN", "LCSC"):
                value = row.get(key, "").strip()
                if value:
                    identity[(key, value)].add(row["Footprint"].strip())
    collisions = sorted(("%s=%s" % (k, v), sorted(fps))
                        for (k, v), fps in identity.items() if len(fps) > 1)

    return dict(ok=(not duplicated and not unpartitioned and not invented
                    and not not_built and not missing and not wrong_dnp
                    and not mismatched_non_purchased and not collisions),
                view_lines={k: len(v) for k, v in views.items()},
                view_refs={k: len(v) for k, v in refs.items()},
                schematic_symbols=len(every),
                references_in_two_views=duplicated,
                schematic_refs_in_no_view=unpartitioned,
                view_refs_not_in_schematic=invented,
                assembly_ref_not_built=not_built,
                built_purchased_ref_without_line=missing,
                do_not_populate_mismatch=wrong_dnp,
                non_purchased_mismatch=mismatched_non_purchased,
                board_says_not_purchased=sorted(board["bom_excluded"]),
                part_identity_on_two_footprints=collisions)


def fab7(pkg, board):
    """Every fitted, purchased, on-board reference must be orderable.

    The PASS condition is unchanged and unweakened -- one unquotable line and
    this fails.  What is new is that the failure is PARTITIONED, because two
    very different things were being counted as one number.  A line whose value
    the schematic itself marks `TUNE` cannot be closed by any part number:
    DEVICE_SPEC s.14 records the NFC matching network as FIRST-ARTICLE TUNE,
    values pending VNA and the ST tool, and buying a part for a value that is
    not yet decided is not sourcing, it is guessing.  Reporting those together
    with the lines that genuinely await a purchasing decision overstates one
    and hides the other.
    """
    bom = read_csv(pkg / "aqroot-Demo-BOM-assembly.csv")
    orderable, gap, tune = set(), defaultdict(list), defaultdict(list)
    for row in bom:
        refs = expand(row["Refs"])
        if row.get("MPN", "").strip() or row.get("LCSC", "").strip():
            orderable |= refs
        elif "TUNE" in row["Value"].upper().split():
            tune[row["Value"] + " | " + row["Footprint"]].extend(sorted(refs))
        else:
            gap[row["Value"] + " | " + row["Footprint"]].extend(sorted(refs))
    unsourced = sorted(r for refs in gap.values() for r in refs)
    pending = sorted(r for refs in tune.values() for r in refs)
    total = len(orderable) + len(unsourced) + len(pending)
    return dict(ok=not unsourced and not pending,
                assembly_refs=total,
                orderable=len(orderable),
                unsourced=len(unsourced) + len(pending),
                coverage=round(len(orderable) / total, 4) if total else None,
                unsourced_lines=len(gap) + len(tune),
                needs_a_sourcing_decision=dict(
                    lines=len(gap), parts=len(unsourced),
                    by_line={k: v for k, v in sorted(gap.items())}),
                pending_first_article_tune=dict(
                    lines=len(tune), parts=len(pending),
                    basis="DEVICE_SPEC s.14 -- the VALUE is not final; no part"
                          " number can close these lines",
                    by_line={k: v for k, v in sorted(tune.items())}),
                unsourced_prefixes=dict(
                    Counter(r.rstrip("0123456789")
                            for r in unsourced + pending)))


def fab8(pkg, board):
    profile = next((pkg / "gerbers").glob("*Edge_Cuts.gbr"), None)
    if profile is None:
        return dict(ok=False, why="no Edge_Cuts gerber")
    extent, ops = gerber_extent(profile)
    board_box = board["outline"]
    delta = [abs(a - b) for a, b in zip(extent or (0, 0, 0, 0), board_box)]
    return dict(ok=extent is not None and max(delta) <= TOL_NM and ops >= 3,
                gerber_extent_mm=[round(v / 1e6, 4) for v in extent]
                if extent else None,
                board_outline_mm=[round(v / 1e6, 4) for v in board_box],
                max_delta_nm=max(delta) if extent else None,
                profile_operations=ops,
                size_mm=[round((board_box[2] - board_box[0]) / 1e6, 3),
                         round((board_box[3] - board_box[1]) / 1e6, 3)])


# D-738.  A VIA WHOSE HOLE OPENS INTO A SOLDER LAND IS A PROCESS REQUIREMENT,
# AND NOTHING IN THIS REPOSITORY COULD SEE ONE.
#
# KiCad has no via-in-pad rule, and on this board the vias in question carry
# the SAME NET as the land they sit in -- they are the router's own escapes --
# so every clearance check is silent by construction.  The package now names
# them, and this clause re-derives the set FROM THE BOARD and refuses a package
# that under-reports it.  The failure mode it exists for is a stale package: a
# route promoted after the last export puts a new barrel in a land and the
# shipped note still says the old number.
#
# The test is a SUBSET test on purpose.  Every land this clause finds must be
# in the manifest; the manifest may carry more (a grazing overlap this sampler
# rounds away), and the note must be present and must state the process.
def fab9(pkg, manifest):
    import math
    b = pcbnew.LoadBoard(str(BOARD))
    vias = [(t, t.GetPosition(), t.GetDrill() / 2.0)
            for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    found = set()
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() not in (pcbnew.PAD_ATTRIB_SMD,
                                          pcbnew.PAD_ATTRIB_CONN):
                continue
            bb = pad.GetBoundingBox()
            for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                if not pad.IsOnLayer(lay):
                    continue
                if pad.GetSolderMaskExpansion(lay):
                    continue          # aperture is not the copper; not modelled
                for (v, pt, hr) in vias:
                    if not v.IsOnLayer(lay):
                        continue
                    if not (bb.GetLeft() - hr <= pt.x <= bb.GetRight() + hr
                            and bb.GetTop() - hr <= pt.y <= bb.GetBottom() + hr):
                        continue
                    pts = [(pt.x, pt.y)] + [
                        (pt.x + hr * math.cos(2 * math.pi * i / 16),
                         pt.y + hr * math.sin(2 * math.pi * i / 16))
                        for i in range(16)]
                    # a rim point strictly inside the land is an open barrel
                    if any(pad.HitTest(pcbnew.VECTOR2I(int(x), int(y)), 0)
                           for (x, y) in pts):
                        found.add(("%s.%s" % (fp.GetReference(),
                                              pad.GetNumber()),
                                   pcbnew.LayerName(lay),
                                   round(pt.x / 1e6, 4), round(pt.y / 1e6, 4)))

    block = manifest.get("via_in_pad") or {}
    listed = {(h["land"], h["layer"], round(h["x"], 4), round(h["y"], 4))
              for h in block.get("lands", [])}
    missing = sorted(found - listed)
    notes = (pkg / "aqroot-Demo-FAB-NOTES.md").read_text(encoding="utf-8")
    stated = ("PLUGGED / RESIN-FILLED AND CAP-PLATED" in notes
              if found else True)
    return dict(ok=(not missing) and stated and bool(block.get("measured")),
                board_lands_with_an_open_barrel=len(found),
                manifest_lands=len(listed),
                missing_from_the_package=missing[:20],
                required_process_stated_in_the_notes=stated,
                measured=bool(block.get("measured")))


# D-738.  A VIA BELOW THE BOARD'S OWN FLOORS IS A CONCESSION, AND A CONCESSION
# THE FABRICATOR HAS NOT BEEN ASKED ABOUT IS NOT A CONCESSION.
#
# The `.kicad_dru` licenses 0.35 mm / 0.20 mm vias -- a 0.075 mm annular ring --
# for named nets inside named rule areas.  DRC passes them because the licence
# exists; the fabricator has no idea they are there.  This clause re-derives the
# set from the board and refuses a package that does not name every one.
def fab10(pkg, manifest):
    b = pcbnew.LoadBoard(str(BOARD))
    dru = (BOARD.parent / "aqroot-Beta-v2.kicad_dru").read_text(encoding="utf-8")
    glob = None
    for m in re.finditer(r'\(rule "([^"]+)"\s*\n\s*\(constraint annular_width '
                         r'\(min ([0-9.]+)mm\)\)\)', dru):
        glob = float(m.group(2))
    setup_via = b.GetDesignSettings().m_ViasMinSize / 1e6
    found = {}
    if glob is not None:
        for t in b.GetTracks():
            if t.GetClass() != "PCB_VIA":
                continue
            dia, drl = t.GetWidth() / 1e6, t.GetDrill() / 1e6
            ring = (dia - drl) / 2.0
            if ring < glob - 1e-9 or dia < setup_via - 1e-9:
                k = (round(dia, 3), round(drl, 3), round(ring, 4), t.GetNetname())
                found[k] = found.get(k, 0) + 1
    block = manifest.get("sub_floor_vias") or {}
    listed = {(r["via_dia_mm"], r["drill_mm"], r["annular_ring_mm"], r["net"]): r["count"]
              for r in block.get("rows", [])}
    notes = (pkg / "aqroot-Demo-FAB-NOTES.md").read_text(encoding="utf-8")
    asked = ("SUB-FLOOR VIAS, PLEASE CONFIRM" in notes) if found else True
    return dict(ok=(found == listed) and asked and bool(block.get("measured")),
                dru_annular_floor_mm=glob,
                setup_min_via_diameter_mm=setup_via,
                board_sub_floor_vias=sum(found.values()),
                package_sub_floor_vias=sum(listed.values()),
                families_agree=(found == listed),
                concession_requested_in_the_notes=asked)


# D-738.  KICAD'S MASK-BRIDGE TEST IS OFF ON THIS BOARD, SO THE PACKAGE IS THE
# ONLY PLACE A TIGHT MASK WEB IS EVER NAMED.
#
# `solder_mask_min_width` is 0.000 mm.  That is not an oversight this clause
# fixes -- changing it is a board-setup change and belongs to a copper
# promotion -- but it does mean a clean DRC report carries no information about
# mask dams, and a package that is silent about them is silent for the wrong
# reason.  This re-derives the tight ones from the board and refuses a package
# that under-reports them.
def fab11(pkg, manifest):
    b = pcbnew.LoadBoard(str(BOARD))
    FLOOR = (manifest.get("solder_mask_dams") or {}).get("floor_mm", 0.125)
    items = []
    for f in b.GetFootprints():
        allow = (f.AllowSolderMaskBridges()
                 if hasattr(f, "AllowSolderMaskBridges") else False)
        for pad in f.Pads():
            for cu, ml in ((pcbnew.F_Cu, pcbnew.F_Mask),
                           (pcbnew.B_Cu, pcbnew.B_Mask)):
                if not pad.IsOnLayer(ml):
                    continue
                bb = pad.GetBoundingBox()
                exp = pad.GetSolderMaskExpansion(ml)
                items.append((pcbnew.LayerName(ml), f.GetReference(),
                              pad.GetNumber(), pad,
                              cu if pad.IsOnLayer(cu) else ml, exp,
                              pad.GetNetname(), allow,
                              bb.GetLeft() - exp, bb.GetTop() - exp,
                              bb.GetRight() + exp, bb.GetBottom() + exp))
    CUT = int(FLOOR * 2e6)
    found = {}
    for i, a in enumerate(items):
        for c in items[i + 1:]:
            if a[0] != c[0]:
                continue
            if max(0, a[8] - c[10], c[8] - a[10]) > CUT:
                continue
            if max(0, a[9] - c[11], c[9] - a[11]) > CUT:
                continue
            if a[1] == c[1] and a[2] == c[2]:
                continue
            A = pcbnew.SHAPE_POLY_SET(a[3].GetEffectivePolygon(a[4]))
            B = pcbnew.SHAPE_POLY_SET(c[3].GetEffectivePolygon(c[4]))
            best = None
            for P, Q in ((A, B), (B, A)):
                o = P.Outline(0)
                for k in range(o.PointCount()):
                    v = o.CPoint(k)
                    d = Q.Distance(pcbnew.VECTOR2I(v.x, v.y))
                    best = d if best is None else min(best, d)
            g = (best - a[5] - c[5]) / 1e6
            if g < FLOOR:
                found["%s|%s.%s|%s.%s" % (a[0], a[1], a[2], c[1], c[2])] = round(g, 4)
    block = manifest.get("solder_mask_dams") or {}
    listed = {"%s|%s|%s" % (r["layer"], r["a"], r["b"]): r["dam_mm"]
              for r in block.get("rows", [])}
    missing = sorted(k for k in found if k not in listed)
    notes = (pkg / "aqroot-Demo-FAB-NOTES.md").read_text(encoding="utf-8")
    stated = ("MEASURED HERE, NOT BY DRC" in notes) if found else True
    return dict(ok=(not missing) and stated and bool(block.get("measured")),
                floor_mm=FLOOR,
                kicad_solder_mask_min_width_mm=(
                    b.GetDesignSettings().m_SolderMaskMinWidth / 1e6),
                board_dams_below_floor=len(found),
                package_dams_below_floor=len(listed),
                missing_from_the_package=missing[:20],
                tightest_mm=min(found.values()) if found else None,
                named_in_the_notes=stated)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", type=Path, default=PACKAGE)
    ap.add_argument("-o", "--out", type=Path)
    # D-666.  THE WHOLE REVIEW IS A RELEASE ACTIVITY; FAB1 IS A HEARTBEAT.
    #
    # FAB2 refills a copy of the board under `kicad-cli` and FAB3-FAB8 re-derive
    # every hole, row and outline from `pcbnew` -- minutes, and the right price
    # for the question "is this package fit to send a factory".  But the
    # question that ROTS between releases is narrower and free: does the
    # package still name the board it was built from?  Nothing in this
    # repository asked it, and the answer had been NO for twenty decisions --
    # `5715bf5c` against an authority of `7b2ca325`, a shipped Excellon
    # carrying 846 holes where the board has 886.  A package that is 40 plated
    # holes short of the copper it plots is a fabrication blocker, and it was
    # invisible because the only instrument that could see it cost minutes and
    # so was never in the standing suite.
    #
    # `--provenance-only` is FAB1 alone: file hashes, the board's own sha256
    # and the ten schematic sheets'.  No `pcbnew`, no `kicad-cli`, no board
    # load -- fast enough to stand in `contract_regression.py` beside the
    # thirteen contracts that watch the copper, so the package's provenance is
    # re-asked on every promotion instead of once per release.  It is the SAME
    # `fab1()` the full review runs, not a second implementation of it, so the
    # heartbeat and the release gate cannot drift apart.
    ap.add_argument("--provenance-only", action="store_true")
    a = ap.parse_args()

    pkg = a.package
    manifest = json.loads((pkg / "MANIFEST.json").read_text())

    if a.provenance_only:
        checks = {"FAB1_provenance": fab1(pkg, manifest)}
    else:
        board = board_facts()
        fitted, dnp = rl.schematic_population()

        checks = {
            "FAB1_provenance": fab1(pkg, manifest),
            "FAB2_fill": fab2(),
            "FAB3_layers": fab3(pkg, board),
            "FAB4_drill": fab4(pkg, board),
            "FAB5_cpl": fab5(pkg, board, fitted, dnp),
            "FAB6_bom": fab6(pkg, board, fitted, dnp),
            "FAB7_sourcing": fab7(pkg, board),
            "FAB8_outline": fab8(pkg, board),
            "FAB9_via_in_pad": fab9(pkg, manifest),
            "FAB10_via_geometry": fab10(pkg, manifest),
            "FAB12_identity": fab12(pkg, board),
            "FAB11_mask_dams": fab11(pkg, manifest),
        }
    doc = dict(schema=1, package=str(pkg.relative_to(ROOT))
               if pkg.is_relative_to(ROOT) else str(pkg),
               board=str(BOARD.relative_to(ROOT)),
               board_sha256=sha256(BOARD),
               provenance_only=bool(a.provenance_only),
               checks=checks,
               failing=sorted(k for k, v in checks.items() if not v["ok"]),
               verdict="PASS" if all(v["ok"] for v in checks.values())
                       else "FAIL")
    text = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        a.out.write_text(text)
    print(text)
    return 0 if doc["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
