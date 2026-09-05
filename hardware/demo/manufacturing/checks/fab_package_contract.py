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
                     position, diameter and slot end-points.
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

Read-only.  `hardware/demo/kicad/aqroot-demo/` is copied to a temporary
directory before the refill test touches anything.

    python3 hardware/demo/manufacturing/checks/fab_package_contract.py \
        [--package DIR] [-o OUT]
"""

import argparse
import csv
import hashlib
import json
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
        geometry[ref] = (pos.x, pos.y, "bottom" if fp.IsFlipped() else "top")

    poly = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(poly, False)
    box = poly.BBox()
    outline = (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom())

    return dict(copper=copper, holes=holes, placeable=placeable,
                bom_excluded=bom_excluded, dnp_attr=dnp_attr,
                geometry=geometry, refs=set(geometry), outline=outline)


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

    # Group both sides by (plating, diameter, slot span) and pair the groups
    # positionally.  The Excellon file is written in millimetres to three
    # decimals, so a hole the board holds at 17.298200 mm is printed 17.298;
    # the claim is therefore equality TO THE MICRON, the resolution the file
    # itself has, not to the nanometre the board is stored at.
    def group(counter):
        out = defaultdict(list)
        for (plated, x, y, dmin, dmax), n in counter.items():
            out[(plated, dmin, dmax)].extend([(x, y)] * n)
        return {k: sorted(v) for k, v in out.items()}

    gb, gf = group(want), group(shipped)
    count_mismatch, displaced = [], []
    for key in sorted(set(gb) | set(gf)):
        bs, fs = gb.get(key, []), gf.get(key, [])
        if len(bs) != len(fs):
            count_mismatch.append(dict(tool=key, board=len(bs), file=len(fs)))
            continue
        for (bx, by), (fx, fy) in zip(bs, fs):
            if abs(bx - fx) > TOL_NM or abs(by - fy) > TOL_NM:
                displaced.append(dict(tool=key, board=(bx, by), file=(fx, fy)))

    diameters = sorted({k[3] for k in shipped})
    return dict(ok=(bool(shipped) and not count_mismatch and not displaced
                    and sum(want.values()) == sum(shipped.values())),
                board_holes=sum(want.values()),
                shipped_holes=sum(shipped.values()),
                plated=sum(v for k, v in shipped.items() if k[0] == "P"),
                unplated=sum(v for k, v in shipped.items() if k[0] == "N"),
                slots=sum(v for k, v in shipped.items() if k[3] != k[4]),
                tools=len(gf),
                min_drill_mm=min(diameters) / 1e6 if diameters else None,
                tool_count_mismatch=count_mismatch,
                displaced_holes=displaced[:20],
                tool_census={"%s %.3f%s" % (k[0], k[1] / 1e6,
                                            "" if k[1] == k[2]
                                            else "x%.3f" % (k[2] / 1e6)): len(v)
                             for k, v in sorted(gf.items())})


def fab5(pkg, board, fitted, dnp):
    rows_all = read_csv(pkg / "aqroot-Demo-pos-all.csv")
    rows_fit = read_csv(pkg / "aqroot-Demo-pos-fitted.csv")
    refs_fit = {r["Ref"] for r in rows_fit}
    expect = {r for r in board["placeable"] if r not in board["dnp_attr"]}
    misplaced = []
    for row in rows_all:
        want = board["geometry"].get(row["Ref"])
        if want is None:
            misplaced.append(dict(ref=row["Ref"], why="not on board"))
            continue
        x = round(float(row["PosX"]) * 1e6)
        y = -round(float(row["PosY"]) * 1e6)
        if (abs(x - want[0]) > TOL_NM or abs(y - want[1]) > TOL_NM
                or row["Side"] != want[2]):
            misplaced.append(dict(ref=row["Ref"], file=(x, y, row["Side"]),
                                  board=want))
    return dict(ok=(refs_fit == expect
                    and {r["Ref"] for r in rows_all} == board["placeable"]
                    and not misplaced),
                rows_all=len(rows_all), rows_fitted=len(rows_fit),
                board_placeable=len(board["placeable"]),
                dnp_still_placed=sorted(refs_fit & dnp),
                fitted_dropped=sorted(expect - refs_fit),
                unexpected_rows=sorted(refs_fit - expect),
                misplaced=misplaced[:20])


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", type=Path, default=PACKAGE)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    pkg = a.package
    manifest = json.loads((pkg / "MANIFEST.json").read_text())
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
    }
    doc = dict(schema=1, package=str(pkg.relative_to(ROOT))
               if pkg.is_relative_to(ROOT) else str(pkg),
               board=str(BOARD.relative_to(ROOT)),
               board_sha256=sha256(BOARD),
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
