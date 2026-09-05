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

    fitted, dnp = rl.schematic_population()
    doc = manifest(out, dict(population=dict(
        schematic_fitted=len(fitted), schematic_dnp=sorted(dnp), bom=bom)))

    print("package: %s" % out)
    print("board  : %s" % doc["source"]["board_sha256"])
    print("kicad  : %s" % doc["kicad"])
    print("files  : %d (%d deterministic)"
          % (len(doc["files"]), sum(f["deterministic"] for f in doc["files"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
