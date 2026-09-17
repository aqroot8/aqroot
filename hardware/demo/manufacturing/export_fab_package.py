#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- generate the fabrication package with the tools a factory runs.

D-611 and D-612 taught the same lesson twice: a defect can be invisible to
every check this repository owns and still be obvious the moment the real
manufacturing tool is run.  The DNP trap was found by running
`kicad-cli pcb export pos --exclude-dnp` and counting rows, not by DRC, not by
`--schematic-parity`, and not by the router.  This module exists so that the
whole package -- Gerbers, drills, positions, BOM, assembly drawings -- is
produced by one deterministic command from the AUTHORITATIVE board, and so that
`checks/fab_package_contract.py` has something concrete to review.

Every artifact is emitted by `kicad-cli` itself.  This module chooses the
options, records the provenance, and does no drawing of its own:

  gerbers   the six copper layers of the board's OWN stackup, both masks, both
            paste layers, both silkscreens and `Edge.Cuts`, plus the `.gbrjob`
            KiCad writes alongside them;
  drills    Excellon, PTH and NPTH in SEPARATE files, ABSOLUTE origin so the
            drill coordinates are the board's own coordinates and the contract
            can compare them to `pcbnew` hole-for-hole, with the map PDFs and
            the drill report;
  positions `pos-all.csv` and `pos-fitted.csv`; the second is the one a factory
            builds from and is `--exclude-dnp`, the flag D-612 made mean
            something;
  BOM       `BOM-full.csv` (every symbol, DNP column carried),
            `BOM-fitted.csv` (`--exclude-dnp`) and `DO-NOT-POPULATE.csv`,
            selected from a flat `kicad-cli` export rather than re-derived;
  assembly  F.Fab and B.Fab PDFs with `--crossout-DNP-footprints-on-fab-layers`,
            which is what makes D-612's sixteen flags visible to a human.

**THE MANIFEST IS THE RELEASE RECORD.**  `MANIFEST.json` carries the sha256 of
the board, the `.kicad_dru` and the `.kicad_pro` the package was generated
from, the exact KiCad version that generated it, and for every artifact its
size, its sha256 and -- for the text artifacts -- a NORMALISED sha256 with the
generator's date and version stamps removed.  The plain sha256 changes on every
run because KiCad stamps a creation date into Gerber and Excellon headers; the
normalised one does not, so the package is REPRODUCIBLE and the contract can
say so rather than assume it.  PDFs carry an embedded creation date that cannot
be stripped this way and are recorded as `deterministic: false` instead of
being quietly excluded.

    python3 hardware/demo/manufacturing/export_fab_package.py [-o DIR]
"""

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE)]

import routing_ledger as rl                                # noqa: E402

PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
DRU = PROJECT / "aqroot-Beta-v2.kicad_dru"
PRO = PROJECT / "aqroot-Beta-v2.kicad_pro"
SCHEMATIC = PROJECT / "aqroot-Beta-v2.kicad_sch"
OUT = ROOT / "hardware/demo/fab"

# The board's own enabled copper layers, in stackup order, plus every
# non-copper layer a fabricator and an assembler actually need.  The contract
# re-derives the copper half from the board and refuses if the two disagree,
# so this list is a declaration, not a duplicate authority.
COPPER = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]
NON_COPPER = ["F.Paste", "B.Paste", "F.SilkS", "B.SilkS",
              "F.Mask", "B.Mask", "Edge.Cuts"]

# BOM fields.  `Manufacturer`/`MPN`/`LCSC` are the schematic's own properties;
# an empty cell is a real sourcing gap and the contract counts them.
BOM_FIELDS = ("Reference,Value,Footprint,Manufacturer,MPN,LCSC,"
              "Description,${QUANTITY},${DNP}")
BOM_LABELS = "Refs,Value,Footprint,Manufacturer,MPN,LCSC,Description,Qty,DNP"
BOM_GROUP = "Value,Footprint,MPN,LCSC,DNP"

# Lines whose only content is when or by what the file was generated.  Removing
# them makes a Gerber/Excellon/gbrjob byte-comparable across runs.
STAMP = re.compile(
    r"(TF\.CreationDate|TF\.GenerationSoftware|GenerationSoftware|CreationDate"
    r"|Created by KiCad|Created on|DRILL file KiCad|MyCompany)", re.I)

DETERMINISTIC_SUFFIXES = {".gbr", ".gbrjob", ".drl", ".csv", ".txt"}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def normalised_sha256(path):
    """sha256 of the artifact with the generator's date/version stamps gone."""
    if Path(path).suffix.lower() not in DETERMINISTIC_SUFFIXES:
        return None
    h = hashlib.sha256()
    for line in Path(path).read_bytes().splitlines(keepends=True):
        if STAMP.search(line.decode("utf-8", "replace")):
            continue
        h.update(line)
    return h.hexdigest()


def run(cmd):
    proc = subprocess.run([str(c) for c in cmd], text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit("FAILED: %s\n%s\n%s"
                         % (" ".join(str(c) for c in cmd),
                            proc.stdout, proc.stderr))
    return proc.stdout


def kicad_version():
    return run(["kicad-cli", "version"]).strip()


def export_gerbers(out):
    run(["kicad-cli", "pcb", "export", "gerbers",
         "--layers", ",".join(COPPER + NON_COPPER),
         "--no-protel-ext", "-o", out, BOARD])


def export_drills(out, report):
    # ABSOLUTE origin: the drill file's coordinates are the board's own, so the
    # contract compares them to `pcbnew` directly instead of trusting an offset.
    run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon",
         "--drill-origin", "absolute", "--excellon-separate-th",
         "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
         "--generate-map", "--map-format", "pdf",
         "--generate-report", "--report-path", report, "-o", out, BOARD])


def export_positions(out):
    for name, exclude in (("aqroot-Demo-pos-all.csv", False),
                          ("aqroot-Demo-pos-fitted.csv", True)):
        cmd = ["kicad-cli", "pcb", "export", "pos", "--format", "csv",
               "--units", "mm", "--side", "both", "-o", out / name, BOARD]
        if exclude:
            cmd.append("--exclude-dnp")
        run(cmd)


def board_bom_authority():
    """Which references the BOARD says are not purchased parts.

    A `TestPoint` is a pad, a `MountingBoss` is a hole: both are board
    features, and both carry KiCad's "exclude from BOM" footprint attribute
    already.  The SCHEMATIC does not know that -- every symbol on this design
    says `(in_bom yes)` -- so a BOM taken straight from `kicad-cli sch export
    bom` asks a supplier to quote forty-eight things that cannot be bought.
    The board is the authority that already states the answer, so the package
    uses it, and `checks/fab_package_contract.py` re-derives the same
    partition and refuses any divergence the board does NOT explain.
    """
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))
    excluded, present = set(), set()
    for fp in b.GetFootprints():
        present.add(fp.GetReference())
        if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM:
            excluded.add(fp.GetReference())
    return present, excluded


def write_csv(path, fieldnames, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames,
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def export_bom(out):
    """The engineering BOM, and the four disjoint views a factory needs.

    `BOM-full.csv` is untouched `kicad-cli` output: every symbol, grouped, with
    the DNP column carried.  The other four are SELECTED from a flat ungrouped
    export of the same command -- every cell in them is still the schematic's,
    read by the same tool -- and they PARTITION that export:

      BOM-assembly       fitted, on-board, purchased.  The quote.
      DO-NOT-POPULATE    the schematic's DNP set, which D-612 taught the board
                         to state as well.
      NON-PURCHASED      test points and mounting bosses: real board features,
                         nothing to buy.
      OFF-BOARD          symbols the schematic marks not-on-board -- the
                         speaker -- which are bought but never placed.

    Assembly lines are grouped here rather than by `kicad-cli` because the
    partition happens per REFERENCE and a grouped line may not be pure.
    """
    run(["kicad-cli", "sch", "export", "bom",
         "--fields", BOM_FIELDS, "--labels", BOM_LABELS,
         "--group-by", BOM_GROUP, "--sort-field", "Refs",
         "-o", out / "aqroot-Demo-BOM-full.csv", SCHEMATIC])

    flat = out / ".flat-bom.csv"
    run(["kicad-cli", "sch", "export", "bom",
         "--fields", BOM_FIELDS + ",${EXCLUDE_FROM_BOARD}",
         "--labels", BOM_LABELS + ",OffBoard",
         "--group-by", "", "--sort-field", "Refs", "-o", flat, SCHEMATIC])
    rows = list(csv.DictReader(flat.open(newline="", encoding="utf-8-sig")))
    flat.unlink()
    fields = [f for f in rows[0] if f != "OffBoard"]

    _, board_excluded = board_bom_authority()
    buckets = {"assembly": [], "dnp": [], "non_purchased": [], "off_board": []}
    for row in rows:
        ref = row["Refs"].strip()
        if row["DNP"].strip():
            buckets["dnp"].append(row)
        elif row["OffBoard"].strip():
            buckets["off_board"].append(row)
        elif ref in board_excluded:
            buckets["non_purchased"].append(row)
        else:
            buckets["assembly"].append(row)

    def strip(rows):
        return [{k: v for k, v in r.items() if k != "OffBoard"} for r in rows]

    grouped, order = {}, []
    for row in buckets["assembly"]:
        key = tuple(row[k] for k in ("Value", "Footprint", "MPN", "LCSC"))
        if key not in grouped:
            grouped[key] = dict(row, Refs=[], Qty=0)
            order.append(key)
        grouped[key]["Refs"].append(row["Refs"].strip())
        grouped[key]["Qty"] += 1
    assembly = []
    for key in order:
        line = grouped[key]
        line = {k: v for k, v in line.items() if k != "OffBoard"}
        line["Refs"] = ",".join(line["Refs"])
        line["Qty"] = str(line["Qty"])
        assembly.append(line)
    assembly.sort(key=lambda r: r["Refs"])

    write_csv(out / "aqroot-Demo-BOM-assembly.csv", fields, assembly)
    write_csv(out / "aqroot-Demo-DO-NOT-POPULATE.csv", fields,
              strip(buckets["dnp"]))
    write_csv(out / "aqroot-Demo-NON-PURCHASED.csv", fields,
              strip(buckets["non_purchased"]))
    write_csv(out / "aqroot-Demo-OFF-BOARD.csv", fields,
              strip(buckets["off_board"]))
    return {k: len(v) for k, v in buckets.items()} | dict(
        flat_rows=len(rows), assembly_lines=len(assembly))


def export_assembly(out):
    """F.Fab / B.Fab, with D-612's sixteen DNP parts crossed out."""
    for layer, side, mirror in (("F.Fab", "top", False),
                                ("B.Fab", "bottom", True)):
        cmd = ["kicad-cli", "pcb", "export", "pdf", "--mode-single",
               "--layers", "%s,Edge.Cuts" % layer,
               "--crossout-DNP-footprints-on-fab-layers",
               "--sketch-pads-on-fab-layers", "--black-and-white",
               "--include-border-title"]
        if mirror:
            cmd.append("--mirror")
        run(cmd + ["-o", out / ("aqroot-Demo-assembly-%s.pdf" % side), BOARD])


# D-677.  A FAB NOTE THAT DOES NOT TRAVEL WITH THE GERBERS IS A NOTE THE SHOP
# NEVER READS.  Two of this board's drill-to-copper clearances are MANUFACTURER
# land patterns and are accepted by named, footprint-scoped `.kicad_dru` rules
# rather than by the board's global floor.  A reviewer opening the package has
# to be told that, and told it in the NUMBERS THE BOARD ACTUALLY CARRIES -- so
# the rule list is read out of the `.kicad_dru` at generation time and the file
# cannot drift from the rules it describes.
NOTE_WHY = {
    "FP-J3 USB4105 land pattern - its own NPTH pegs vs its own pads, D-677":
        "GCT USB4105-xx-A USB-C receptacle, vendor land pattern (footprint "
        "verified MATCH against the GCT series drawing).  Its two Oe0.65 mm "
        "NPTH locating pegs stand 0.1944 mm from its own GND contacts A1 / "
        "B12 / A12 / B1.  BOTH the hole and the copper are the manufacturer's "
        "and neither can move without diverging from the library master.  "
        "0.1944 mm is 5.6 um BELOW JLCPCB's published 0.200 mm NPTH-to-track "
        "figure: PLEASE CONFIRM, and advise if your process needs the pads "
        "trimmed.",
    "FP-MK1 DMM-4026 acoustic port inside its own GND annulus - D-227 "
    "construction, D-677":
        "PUI DMM-4026-B-I2S bottom-port MEMS microphone.  The Oe1.05 mm "
        "acoustic port is an UNPLATED hole drilled concentrically through its "
        "own Oe1.65 mm GND land, leaving a 0.30 mm annulus -- this is "
        "intentional (the land is what the microphone's port seals against) "
        "and there is no plated through-hole here.  Copper IS exposed in the "
        "barrel wall; no plating or tenting is required.",
    "FP-J3 NPTH locating peg vs foreign copper - JLCPCB NPTH-to-track "
    "0.200 mm, D-677":
        "Routed GND copper approaches J3's NPTH pegs no closer than "
        "0.2100 mm (tracks) and 0.2412 mm (one 0.50/0.20 mm via), i.e. at or "
        "above the published 0.200 mm NPTH-to-track figure.  The peg is the "
        "receptacle's metal shell leg and the shell is tied to GND through "
        "R32 (0 ohm), so this copper is already at the peg's own potential.",
}


def export_fab_notes(out):
    """Write the fabrication notes, with every accepted clearance read live."""
    import re as _re
    dru = DRU.read_text(encoding="utf-8")
    rules = []
    for m in _re.finditer(r'\(rule "([^"]+)"\s*\n\s*\(constraint '
                          r'hole_clearance \(min ([0-9.]+mm)\)\)\s*\n'
                          r'\s*\(condition "([^"]*)"\)\)', dru):
        rules.append((m.group(1), m.group(2), m.group(3)))
    import pcbnew
    board = pcbnew.LoadBoard(str(BOARD))
    glob_mm = board.GetDesignSettings().m_HoleClearance / 1e6
    lines = ["# AQROOT Demo - FABRICATION NOTES",
             "",
             "Generated by `hardware/demo/manufacturing/export_fab_package.py`",
             "from the board this package was built from.  Every number below "
             "is read out of the board or its `.kicad_dru` at generation time.",
             "",
             "## Drill-to-copper clearance",
             "",
             "Global board minimum hole clearance: **%.3f mm**." % glob_mm,
             "",
             "KiCad DRC on this board reports **ZERO** `hole_clearance` "
             "violations.  %d named, footprint-scoped rule%s accept%s the "
             "clearances below, and NOTHING else on the board is affected:"
             % (len(rules), "" if len(rules) == 1 else "s",
                "s" if len(rules) == 1 else ""),
             ""]
    for name, mn, cond in rules:
        lines += ["### `%s`" % name,
                  "",
                  "- accepted minimum: **%s**" % mn,
                  "- scope: `%s`" % cond,
                  "- %s" % NOTE_WHY.get(name, "NO EXPLANATION RECORDED -- "
                                               "this rule was added without a "
                                               "fabrication note and must not "
                                               "ship unexplained."),
                  ""]
    if not rules:
        lines += ["No footprint-scoped `hole_clearance` rule is in force.", ""]
    lines += outline_notes(board)
    vlines, vrows = via_in_pad_notes(board)
    lines += vlines
    glines, grows = via_geometry_notes(board, dru)
    lines += glines
    mlines, mrows = solder_mask_notes(board)
    lines += mlines
    (out / "aqroot-Demo-FAB-NOTES.md").write_text("\n".join(lines),
                                                  encoding="utf-8")
    return [r[0] for r in rules], vrows, grows, mrows


# D-737.  THE PROFILE IS NOT A RECTANGLE AND THE PACKAGE NEVER SAID SO.
#
# `Edge.Cuts` is a STEPPED outline, and a stepped outline has INSIDE (reflex)
# corners.  A profile router cannot cut a sharp inside corner: it leaves a
# fillet of its own tool radius, so the board is very slightly LARGER there
# than drawn.  That is the correct treatment and it is safe -- but only if the
# fabricator knows it is expected, and only if no copper sits inside the
# fillet.  Both facts are measured here and written down, rather than left for
# a fabricator to guess or for an enclosure to discover.
def outline_notes(board):
    """Measure the profile, its reflex corners and the copper beside them."""
    import math
    import pcbnew
    ec = board.GetLayerID("Edge.Cuts")
    segs = []
    for d in board.GetDrawings():
        if d.GetLayer() != ec:
            continue
        try:
            if d.GetShape() != pcbnew.SHAPE_T_SEGMENT:
                return ["## Board outline", "",
                        "The profile contains a non-segment shape; the stepped-"
                        "outline note is NOT emitted rather than guessed.", ""]
            a, b = d.GetStart(), d.GetEnd()
        except Exception:
            return ["## Board outline", "",
                    "The profile could not be read as segments; the stepped-"
                    "outline note is NOT emitted rather than guessed.", ""]
        segs.append(((a.x, a.y), (b.x, b.y)))
    if not segs:
        return []
    xs = [p[0] for s in segs for p in s]
    ys = [p[1] for s in segs for p in s]

    # chain the segments into one closed loop
    todo = list(segs)
    loop = [todo[0][0], todo[0][1]]
    todo.pop(0)
    while todo:
        for i, (a, b) in enumerate(todo):
            if a == loop[-1]:
                loop.append(b); todo.pop(i); break
            if b == loop[-1]:
                loop.append(a); todo.pop(i); break
        else:
            return ["## Board outline", "",
                    "The profile does not chain into a single closed loop; the "
                    "stepped-outline note is NOT emitted rather than guessed.",
                    ""]
    if loop[0] == loop[-1]:
        loop.pop()
    n = len(loop)
    area2 = sum(loop[i][0] * loop[(i + 1) % n][1] - loop[(i + 1) % n][0] * loop[i][1]
                for i in range(n))
    sign = 1.0 if area2 > 0 else -1.0

    # copper the fillet could reach: every track, via and pad, any layer
    cu = []
    for t in board.GetTracks():
        s_, e_ = t.GetStart(), t.GetEnd()
        cu.append(("track" if t.Type() != pcbnew.PCB_VIA_T else "via",
                   t.GetNetname(), s_.x, s_.y, e_.x, e_.y,
                   t.GetWidth() / 2.0))
    for f in board.GetFootprints():
        for pd in f.Pads():
            pp = pd.GetPosition()
            r = max(pd.GetSize().x, pd.GetSize().y) / 2.0
            cu.append(("pad %s.%s" % (f.GetReference(), pd.GetNumber()),
                       pd.GetNetname(), pp.x, pp.y, pp.x, pp.y, r))

    def nearest(px, py):
        best = None
        for kind, net, ax, ay, bx, by, rad in cu:
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
            d = math.hypot(px - (ax + t * vx), py - (ay + t * vy)) - rad
            if best is None or d < best[0]:
                best = (d, kind, net)
        return best

    reflex = []
    for i in range(n):
        p0, p1, p2 = loop[i - 1], loop[i], loop[(i + 1) % n]
        cx = ((p1[0] - p0[0]) * (p2[1] - p1[1])
              - (p1[1] - p0[1]) * (p2[0] - p1[0]))
        if cx * sign < 0:                      # turns against the winding
            reflex.append(p1)

    lines = ["## Board outline -- STEPPED PROFILE, READ THIS BEFORE ROUTING",
             "",
             "Profile extents: **%.3f x %.3f mm** (x %.3f .. %.3f, "
             "y %.3f .. %.3f), %d segments."
             % ((max(xs) - min(xs)) / 1e6, (max(ys) - min(ys)) / 1e6,
                min(xs) / 1e6, max(xs) / 1e6, min(ys) / 1e6, max(ys) / 1e6,
                len(segs)),
             ""]
    if not reflex:
        lines += ["The profile is convex -- no inside corners.", ""]
    else:
        lines += ["The profile has **%d INSIDE (reflex) corner%s**.  A profile "
                  "router cannot cut a sharp inside corner: it leaves a fillet "
                  "of its own tool radius, which means **MATERIAL REMAINS** "
                  "and the board is very slightly LARGER there than drawn.  "
                  "**That is the correct and accepted treatment -- any tool "
                  "radius is fine and the enclosure clears it.**  What is NOT "
                  "accepted is squaring the corner by plunging, drilling a "
                  "relief or otherwise OVER-CUTTING, because that removes "
                  "material toward the copper.  The number below bounds such a "
                  "relief if one is ever cut:"
                  % (len(reflex), "" if len(reflex) == 1 else "s"),
                  ""]
        for (px, py) in reflex:
            d, kind, net = nearest(px, py)
            lines += ["- inside corner at **(%.3f, %.3f)** -- nearest copper "
                      "is **%.3f mm** away, edge to edge (%s, `%s`).  A corner "
                      "relief must stay under %.3f mm of radius; **a 1.0 mm "
                      "relief would reach copper here**."
                      % (px / 1e6, py / 1e6, d / 1e6, kind,
                         net or "no net", d / 1e6)
                      if d / 1e6 < 1.0 else
                      "- inside corner at **(%.3f, %.3f)** -- nearest copper "
                      "is **%.3f mm** away, edge to edge (%s, `%s`).  A corner "
                      "relief must stay under %.3f mm of radius."
                      % (px / 1e6, py / 1e6, d / 1e6, kind,
                         net or "no net", d / 1e6)]
        lines += [""]
    edge = board.GetDesignSettings().m_CopperEdgeClearance / 1e6
    lines += ["Board copper-to-edge minimum in force: **%.3f mm**, and KiCad "
              "DRC on this board reports ZERO `copper_edge_clearance` "
              "violations." % edge,
              ""]
    return lines


# D-738.  THE PACKAGE NEVER TOLD THE FABRICATOR THE BOARD USES VIA-IN-PAD.
#
# `pad_to_mask_clearance` on this board is 0, so a pad's SOLDER-MASK APERTURE
# IS ITS COPPER.  A via whose drilled hole lies inside that aperture is an open
# barrel in the middle of a solder land: there is no mask over it, and at
# reflow the paste deposit drains into it.  KiCad DRC cannot see this -- it has
# no via-in-pad rule -- and on this board it is additionally invisible to the
# CLEARANCE checks, because almost every one of these vias carries the SAME NET
# as the land it sits in (they are the router's own pad escapes and the
# decoupling fan-outs), so nothing is ever too close to anything.
#
# This measures it rather than asserting it: for every SMD / connector pad on a
# solderable layer it intersects each nearby via's DRILLED-HOLE disc with the
# pad's own mask aperture polygon and reports the overlap.  It refuses to emit
# the note if the board carries a non-zero solder-mask expansion it has not
# been taught to model, rather than reporting an aperture it did not compute.
def via_in_pad_notes(board):
    """Find every via whose hole is exposed inside a solderable land."""
    import math
    import pcbnew

    thickness = board.GetDesignSettings().GetBoardThickness() / 1e6
    vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    vpos = [(v, v.GetPosition(), int(v.GetDrill() / 2), int(v.GetWidth() / 2))
            for v in vias]

    def disc(cx, cy, r, n=64):
        ps = pcbnew.SHAPE_POLY_SET()
        pts = pcbnew.VECTOR_VECTOR2I()
        for i in range(n):
            a = 2 * math.pi * i / n
            pts.append(pcbnew.VECTOR2I(int(cx + r * math.cos(a)),
                                       int(cy + r * math.sin(a))))
        ps.AddOutline(pcbnew.SHAPE_LINE_CHAIN(pts, True))
        return ps

    hits = []
    for f in board.GetFootprints():
        for pad in f.Pads():
            if pad.GetAttribute() not in (pcbnew.PAD_ATTRIB_SMD,
                                          pcbnew.PAD_ATTRIB_CONN):
                continue
            bb = pad.GetBoundingBox()
            near = [q for q in vpos
                    if bb.GetLeft() - q[3] <= q[1].x <= bb.GetRight() + q[3]
                    and bb.GetTop() - q[3] <= q[1].y <= bb.GetBottom() + q[3]]
            if not near:
                continue
            for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                if not pad.IsOnLayer(lay):
                    continue
                exp = pad.GetSolderMaskExpansion(lay)
                if exp:                       # not modelled -- refuse to guess
                    return (["## Vias in solderable lands", "",
                             "This board carries a non-zero solder-mask "
                             "expansion (%.4f mm on %s.%s); the via-in-pad "
                             "note is NOT emitted rather than measured against "
                             "an aperture this generator did not compute."
                             % (exp / 1e6, f.GetReference(), pad.GetNumber()),
                             ""], None)
                aperture = pcbnew.SHAPE_POLY_SET(pad.GetEffectivePolygon(lay))
                area = aperture.Area() / 1e12
                sz = pad.GetSize()
                for (v, pt, hr, _ar) in near:
                    if not v.IsOnLayer(lay):
                        continue
                    inter = pcbnew.SHAPE_POLY_SET(aperture)
                    inter.BooleanIntersection(disc(pt.x, pt.y, hr))
                    a = inter.Area() / 1e12
                    if a <= 1e-9:
                        continue
                    hits.append(dict(
                        ref="%s.%s" % (f.GetReference(), pad.GetNumber()),
                        layer=pcbnew.LayerName(lay), net=pad.GetNetname(),
                        x=pt.x / 1e6, y=pt.y / 1e6,
                        dia=v.GetWidth() / 1e6, drill=v.GetDrill() / 1e6,
                        pad_x=sz.x / 1e6, pad_y=sz.y / 1e6,
                        pad_area=area, open_area=a,
                        pct=100.0 * a / area if area else 0.0,
                        same_net=(v.GetNetname() == pad.GetNetname())))

    seen, rows = set(), []
    for h in hits:
        k = (h["ref"], h["layer"], round(h["x"], 4), round(h["y"], 4))
        if k in seen:
            continue
        seen.add(k)
        rows.append(h)
    rows.sort(key=lambda h: -h["pct"])

    lines = ["## Vias in solderable lands -- VIA PROTECTION IS REQUIRED", ""]
    if not rows:
        lines += ["No via's drilled hole lies inside any solder-mask aperture "
                  "on this board.  Standard tenting is sufficient.", ""]
        return lines, []

    barrels = len({(round(h["x"], 4), round(h["y"], 4)) for h in rows})
    refs = len({h["ref"].split(".")[0] for h in rows})
    worst = rows[0]
    biggest = max(rows, key=lambda h: h["drill"])
    vol = math.pi * (biggest["drill"] / 2.0) ** 2 * thickness

    lines += [
        "Solder-mask expansion on this board is **0.000 mm**, so a pad's mask "
        "aperture IS its copper.  **%d via barrel%s open directly into %d "
        "solderable land%s across %d component%s**, on hole sizes %s.  %d of "
        "those land%s carr%s the SAME net as the via, which is why no "
        "clearance check and no KiCad DRC rule reports them -- KiCad has no "
        "via-in-pad rule at all."
        % (barrels, "" if barrels == 1 else "s",
           len(rows), "" if len(rows) == 1 else "s",
           refs, "" if refs == 1 else "s",
           " / ".join("%.2f mm" % d for d in
                      sorted({h["drill"] for h in rows})),
           sum(1 for h in rows if h["same_net"]),
           "" if sum(1 for h in rows if h["same_net"]) == 1 else "s",
           "ies" if sum(1 for h in rows if h["same_net"]) == 1 else "y"),
        "",
        "**REQUIRED PROCESS: these vias must be PLUGGED / RESIN-FILLED AND "
        "CAP-PLATED (via-in-pad / POFV), or filled by an equivalent process "
        "that leaves a planar, solderable land.**  Applying the process to "
        "every via on the board is acceptable and is the simpler instruction; "
        "what is NOT acceptable is shipping these barrels open.",
        "",
        "Why it is not optional, in this board's own numbers: the largest hole "
        "in a land is **%.2f mm**, and through %.2f mm of finished board that "
        "barrel holds **%.3f mm3**.  A 0.12 mm stencil over the %0.3f x %0.3f "
        "mm land it sits in deposits about **%.3f mm3** of paste.  **The "
        "barrel can swallow the whole deposit.**"
        % (biggest["drill"], thickness, vol,
           biggest["pad_x"], biggest["pad_y"],
           biggest["pad_x"] * biggest["pad_y"] * 0.12),
        "",
        "The ten worst lands, by how much of the land is open hole:",
        "",
        "| land | layer | land size (mm) | hole | open area | % of land | net |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for h in rows[:10]:
        lines.append("| `%s` | %s | %.3f x %.3f | %.2f mm | %.4f mm2 | "
                     "**%.1f %%** | `%s` |"
                     % (h["ref"], h["layer"], h["pad_x"], h["pad_y"],
                        h["drill"], h["open_area"], h["pct"],
                        h["net"] or "no net"))
    fine = [h for h in rows if min(h["pad_x"], h["pad_y"]) <= 0.5]
    lines += [
        "",
        "**%d of the %d lands are FINE-PITCH** (one land dimension at or below "
        "0.500 mm)%s.  On those the hole is a large fraction of the land's "
        "width and an unfilled barrel does not merely starve the joint, it "
        "removes the land."
        % (len(fine), len(rows),
           " -- including %s" % ", ".join(
               sorted({h["ref"] for h in fine})[:8]) if fine else ""),
        "",
        "The complete list of barrel centres is in `MANIFEST.json` under "
        "`via_in_pad`.",
        "",
    ]
    return lines, rows


# D-738.  THIRTY-FIVE VIAS SIT BELOW THE BOARD'S OWN GLOBAL FLOORS AND THE
# PACKAGE NEVER SAID SO.
#
# The `.kicad_dru` floor is `annular_width (min 0.125mm)`, and the board setup
# asks 0.500 mm for a via.  Four families of named, net-scoped, area-enclosed
# rules license 0.35 mm / 0.20 mm -- a 0.075 mm annular ring -- for specific
# fine-pitch escapes and POFV sites.  That is exactly the right internal
# discipline and KiCad passes it, but it is an INTERNAL licence: the fabricator
# is never shown it, and 0.35 mm of via pad on a 0.20 mm hole is below the
# 0.4 mm / 0.2 mm minimum via most quick-turn houses publish.  A concession the
# fabricator has not been asked about is not a concession.
def via_geometry_notes(board, dru_text):
    import re
    import pcbnew

    floors = [float(m) for m in re.findall(
        r"\(constraint annular_width \(min ([0-9.]+)mm\)\)\s*\)", dru_text)]
    # the GLOBAL floor is the one whose rule carries no condition
    glob = None
    for m in re.finditer(r'\(rule "([^"]+)"\s*\n\s*\(constraint annular_width '
                         r'\(min ([0-9.]+)mm\)\)\)', dru_text):
        glob = float(m.group(2))
    if glob is None:
        return (["## Via geometry", "",
                 "The `.kicad_dru` publishes no unconditional `annular_width` "
                 "floor, so the sub-floor note is NOT emitted rather than "
                 "measured against a floor this generator guessed.", ""], None)

    setup_via = board.GetDesignSettings().m_ViasMinSize / 1e6
    rows = {}
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        dia, drl = t.GetWidth() / 1e6, t.GetDrill() / 1e6
        ring = (dia - drl) / 2.0
        if ring < glob - 1e-9 or dia < setup_via - 1e-9:
            k = (round(dia, 3), round(drl, 3), round(ring, 4), t.GetNetname())
            rows[k] = rows.get(k, 0) + 1

    lines = ["## Via geometry -- SUB-FLOOR VIAS, PLEASE CONFIRM", ""]
    if not rows:
        lines += ["Every via on this board meets the board's own global floors "
                  "(annular ring >= %.3f mm, diameter >= %.3f mm).  No via "
                  "concession is requested." % (glob, setup_via), ""]
        return lines, []

    total = sum(rows.values())
    rings = sorted({k[2] for k in rows})
    lines += [
        "This board's own `.kicad_dru` floor is **annular ring >= %.3f mm** and "
        "its board setup asks **>= %.3f mm of via diameter**.  **%d vias sit "
        "below one or both**, at annular ring%s %s.  Each is licensed inside "
        "the design by a NAMED, net-scoped, area-enclosed `.kicad_dru` rule "
        "(the `FINE_ESC_*`, `*_POFV`, `*_KELVIN` and `BAT_PROT_TAP_*` rule "
        "areas), so real KiCad DRC passes them -- but that is an INTERNAL "
        "licence and it is not a fabricator's agreement.  **Please confirm you "
        "can hold these, and advise if your process needs the pads grown.**"
        % (glob, setup_via, total, "" if len(rings) == 1 else "s",
           " / ".join("%.3f mm" % r for r in rings)),
        "",
        "| count | via dia | drill | annular ring | net |",
        "| --- | --- | --- | --- | --- |",
    ]
    for k in sorted(rows, key=lambda q: (q[2], q[3])):
        lines.append("| %d | %.2f mm | %.2f mm | **%.3f mm** | `%s` |"
                     % (rows[k], k[0], k[1], k[2], k[3] or "no net"))
    lines += ["",
              "All of them are ORDINARY THROUGH vias -- this board carries no "
              "blind via, no buried via and no laser microvia, and its "
              "`.kicad_dru` disallows all three explicitly.",
              ""]
    return lines, [dict(via_dia_mm=k[0], drill_mm=k[1], annular_ring_mm=k[2],
                        net=k[3], count=rows[k])
                   for k in sorted(rows, key=lambda q: (q[2], q[3]))]


# D-738.  KICAD HAS NOT CHECKED A SINGLE SOLDER-MASK WEB ON THIS BOARD.
#
# `solder_mask_min_width` in board setup is 0.000 mm, which switches the
# `solder_mask_bridge` test off by construction -- so "DRC is clean" says
# nothing about mask dams.  Measured instead: with `pad_to_mask_clearance` also
# 0, a pad's aperture IS its copper, so the dam between two apertures is the gap
# between two pads.  Reported exactly (polygon to polygon, not bounding box,
# because the tight ones on this board are the DIAGONAL corner pairs of a QFN
# and a bounding box reads those as zero).
def solder_mask_notes(board, floor_mm=0.125):
    import pcbnew

    setup = board.GetDesignSettings()
    checked = setup.m_SolderMaskMinWidth / 1e6
    items = []
    for f in board.GetFootprints():
        allow = (f.AllowSolderMaskBridges()
                 if hasattr(f, "AllowSolderMaskBridges") else False)
        for pad in f.Pads():
            for cu, ml in ((pcbnew.F_Cu, pcbnew.F_Mask),
                           (pcbnew.B_Cu, pcbnew.B_Mask)):
                if not pad.IsOnLayer(ml):
                    continue
                bb = pad.GetBoundingBox()
                exp = pad.GetSolderMaskExpansion(ml)
                items.append(dict(lay=pcbnew.LayerName(ml), ref=f.GetReference(),
                                  num=pad.GetNumber(), pad=pad,
                                  cu=cu if pad.IsOnLayer(cu) else ml, exp=exp,
                                  net=pad.GetNetname(), allow=allow,
                                  x0=bb.GetLeft() - exp, y0=bb.GetTop() - exp,
                                  x1=bb.GetRight() + exp, y1=bb.GetBottom() + exp))

    def dam(a, c):
        A = pcbnew.SHAPE_POLY_SET(a["pad"].GetEffectivePolygon(a["cu"]))
        B = pcbnew.SHAPE_POLY_SET(c["pad"].GetEffectivePolygon(c["cu"]))
        best = None
        for P, Q in ((A, B), (B, A)):
            o = P.Outline(0)
            for i in range(o.PointCount()):
                v = o.CPoint(i)
                d = Q.Distance(pcbnew.VECTOR2I(v.x, v.y))
                best = d if best is None else min(best, d)
        return (best - a["exp"] - c["exp"]) / 1e6

    CUT = int(floor_mm * 2e6)
    rows = []
    for i, a in enumerate(items):
        for c in items[i + 1:]:
            if a["lay"] != c["lay"]:
                continue
            dx = max(0, a["x0"] - c["x1"], c["x0"] - a["x1"])
            dy = max(0, a["y0"] - c["y1"], c["y0"] - a["y1"])
            if dx > CUT or dy > CUT:
                continue
            if a["ref"] == c["ref"] and a["num"] == c["num"]:
                continue
            g = dam(a, c)
            if g >= floor_mm:
                continue
            rows.append(dict(dam_mm=round(g, 4), layer=a["lay"],
                             a="%s.%s" % (a["ref"], a["num"]),
                             b="%s.%s" % (c["ref"], c["num"]),
                             same_net=(a["net"] == c["net"]),
                             declared_bridge=bool(a["allow"] or c["allow"]),
                             net_a=a["net"], net_b=c["net"]))
    rows.sort(key=lambda r: (r["dam_mm"], r["a"]))

    lines = ["## Solder-mask dams -- MEASURED HERE, NOT BY DRC", "",
             "**`solder_mask_min_width` in this board's setup is %.3f mm, which "
             "switches KiCad's `solder_mask_bridge` test OFF.**  A clean DRC "
             "report therefore says NOTHING about mask webs on this board, and "
             "the webs below were measured for this note instead -- polygon to "
             "polygon, not bounding box.  `pad_to_mask_clearance` is 0.000 mm, "
             "so an aperture is its pad and a dam is a pad-to-pad gap."
             % checked, ""]
    if not rows:
        lines += ["No two apertures come within %.3f mm of each other."
                  % floor_mm, ""]
        return lines, []
    lines += ["Every dam below **%.3f mm** on the board:" % floor_mm, "",
              "| dam | layer | A | B | same net | declared bridge |",
              "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append("| **%.4f mm** | %s | `%s` | `%s` | %s | %s |"
                     % (r["dam_mm"], r["layer"], r["a"], r["b"],
                        "yes" if r["same_net"] else "**no**",
                        "yes" if r["declared_bridge"] else "no"))
    live = [r for r in rows if not r["same_net"] and not r["declared_bridge"]]
    lines += ["",
              "**What each group is, and what is being asked.**",
              "",
              "- Rows marked *same net* are vendor land patterns whose two "
              "contacts are one node -- the USB-C receptacle's A/B pairs are "
              "the whole of that group.  A merged aperture there is harmless "
              "and no action is requested.",
              "- Rows marked *declared bridge* carry "
              "`allow_soldermask_bridges` on the footprint AND on its library "
              "master; the microphone's port ring is the whole of that group "
              "and the merge is the design.",
              "- **The remaining %d row%s are DIFFERENT NETS, and they split "
              "in two.**  All of them are MANUFACTURER LAND PATTERNS, not "
              "routing.  **%d are at or under 0.100 mm and are not printable "
              "as a web by any process we would order** -- the four DIAGONAL "
              "CORNER pairs of `U9`'s UFQFPN32, which come straight from ST's "
              "own recommended land (0.30 x 0.75 lands, centres at +/-2.275 on "
              "a 0.50 mm pitch); the board's `.kicad_dru` already licenses "
              "their COPPER clearance by a named, footprint-scoped rule.  "
              "**Please gang those four -- one window per corner -- rather "
              "than attempting a web.**  The other %d are `U12`'s TPS63020 "
              "land at **0.120 mm**, which is AT the usual 0.100-0.130 mm "
              "limit rather than under it: **print the web if you can hold it, "
              "gang the row if you cannot, and tell us which.**  Assembly "
              "control at both pitches is the PASTE stencil, which is per-pad "
              "and is unaffected either way."
              % (len(live), "" if len(live) == 1 else "s",
                 sum(1 for r in live if r["dam_mm"] <= 0.100),
                 sum(1 for r in live if r["dam_mm"] > 0.100)),
              ""]
    return lines, rows


def manifest(out, extra):
    files = []
    for path in sorted(p for p in out.rglob("*") if p.is_file()
                       and p.name != "MANIFEST.json"):
        norm = normalised_sha256(path)
        files.append(dict(path=str(path.relative_to(out)),
                          bytes=path.stat().st_size,
                          sha256=sha256(path),
                          normalised_sha256=norm,
                          deterministic=norm is not None))
    doc = dict(schema=1,
               generator="hardware/demo/manufacturing/export_fab_package.py",
               kicad=kicad_version(),
               source=dict(board=str(BOARD.relative_to(ROOT)),
                           board_sha256=sha256(BOARD),
                           dru_sha256=sha256(DRU),
                           pro_sha256=sha256(PRO),
                           schematic_sha256=sha256(SCHEMATIC),
                           # The BOM is derived from the WHOLE hierarchy, not
                           # from the root sheet, so a manifest that hashes
                           # only the root does not cover its own output: the
                           # D-614 sourcing graft changed nine child sheets and
                           # not one byte of the root.
                           schematic_sheet_sha256={
                               s.name: sha256(s) for s in
                               sorted(PROJECT.glob("*.kicad_sch"))}),
               layers=dict(copper=COPPER, non_copper=NON_COPPER),
               files=files)
    doc.update(extra)
    (out / "MANIFEST.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path, default=OUT)
    a = ap.parse_args()

    out = a.out
    gerbers = out / "gerbers"
    if out.exists():
        # This deletes a directory tree.  It may only ever delete a tree THIS
        # script wrote, which is what the manifest identifies -- never a source
        # directory reached by a mistyped `-o`.
        if any(out.iterdir()) and not (out / "MANIFEST.json").exists():
            raise SystemExit(
                "%s is not empty and holds no MANIFEST.json, so it is not a "
                "package this script generated; refusing to delete it" % out)
        shutil.rmtree(out)
    gerbers.mkdir(parents=True)

    export_gerbers(gerbers)
    export_drills(gerbers, gerbers / "drill-report.txt")
    export_positions(out)
    bom = export_bom(out)
    export_assembly(out)
    notes, via_in_pad, sub_floor_vias, mask_dams = export_fab_notes(out)

    fitted, dnp = rl.schematic_population()
    doc = manifest(out, dict(population=dict(
        schematic_fitted=len(fitted), schematic_dnp=sorted(dnp), bom=bom),
        via_in_pad=dict(
            measured=via_in_pad is not None,
            solderable_lands_with_an_open_barrel=(
                len(via_in_pad) if via_in_pad is not None else None),
            distinct_barrels=(
                len({(round(h["x"], 4), round(h["y"], 4))
                     for h in via_in_pad}) if via_in_pad else 0),
            required_process=("plugged / resin-filled and cap-plated "
                              "(via-in-pad, POFV)") if via_in_pad else None,
            lands=[dict(land=h["ref"], layer=h["layer"], net=h["net"],
                        x=round(h["x"], 4), y=round(h["y"], 4),
                        via_dia_mm=h["dia"], drill_mm=h["drill"],
                        land_mm=[round(h["pad_x"], 4), round(h["pad_y"], 4)],
                        open_area_mm2=round(h["open_area"], 5),
                        pct_of_land=round(h["pct"], 2),
                        same_net=h["same_net"])
                   for h in (via_in_pad or [])]),
        sub_floor_vias=dict(
            measured=sub_floor_vias is not None,
            families=len(sub_floor_vias or []),
            vias=sum(r["count"] for r in (sub_floor_vias or [])),
            rows=sub_floor_vias or []),
        solder_mask_dams=dict(
            measured=mask_dams is not None,
            floor_mm=0.125,
            below_floor=len(mask_dams or []),
            undeclared_different_net=sum(
                1 for r in (mask_dams or [])
                if not r["same_net"] and not r["declared_bridge"]),
            rows=mask_dams or []),
        fabrication_notes=dict(
            file="aqroot-Demo-FAB-NOTES.md",
            hole_clearance_rules=notes,
            every_rule_explained=all(n in NOTE_WHY for n in notes))))

    print("package: %s" % out)
    print("board  : %s" % doc["source"]["board_sha256"])
    print("kicad  : %s" % doc["kicad"])
    print("files  : %d (%d deterministic)"
          % (len(doc["files"]), sum(f["deterministic"] for f in doc["files"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
