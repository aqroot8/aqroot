#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- does the PART the BOM orders fit the LAND the board has?

D-613's `C26` was one part number on two land patterns: a 1206 line carrying a
0603 part's LCSC code.  It was found by eye.  This asks the question of EVERY
sourced reference at once, and it asks the only authority that can answer it --
the distributor's own package field, read live and archived by `jlc_live.py`.

Read-only.  It changes nothing and decides nothing; it reports three verdicts:

    MATCH          the record's package and the board's land are the same part
    MISMATCH       they are not, and the board would be built wrong
    UNCOMPARABLE   this screen cannot map one to the other, stated openly
                   rather than silently counted as a pass

The comparison is on a FAMILY and a PIN COUNT, never on a string, because
`MSOP-10` and `MSOP-10_3x3mm_P0.5mm` are the same land and `DFN-10-EP(3x3)`
and `MSOP-10` are not.

    python3 screen_part_land_parity.py [--refresh] [-o REPORT.json]
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import screen_bom_sourcing as S            # noqa: E402
from jlc_live import fetch                 # noqa: E402

# --------------------------------------------------------------------------
# WHAT THIS SCREEN IS ALLOWED TO DECIDE.
#
# A footprint name is not a package: `MAX17048_T822`, `ST25R3916_AQET` and
# `Coilcraft_XFL4020` name a PART, and no rule can turn them into a JEDEC body
# without guessing.  So the screen decides only the two classes where both
# sides state the same kind of thing, and says UNCOMPARABLE -- out loud, in the
# report -- everywhere else.  A screen that quietly counted the rest as passes
# would be the D-611 failure again: a check that reads TRUE because it was
# never asked.
#
#   CHIP   an imperial chip land, `0603` either side.  This is the `C26` class.
#   BODY   a leaded or bottom-terminated body with a PIN COUNT.  This is the
#          class where a land is right and the ORDER CODE is for a different
#          package -- and where FBV2-PWR-002 forbids the substitution outright.
# --------------------------------------------------------------------------
RE_CHIP_LAND = re.compile(r"^[A-Z]+_(\d{4})_\d+Metric$")
RE_CHIP_BARE = re.compile(r"^(\d{4})$")
RE_BODY = re.compile(r"^(U?[A-Z]{2,7})-(\d+)(?!\d)")

BODY_CLASS = {
    "SOIC": "SOIC", "SOP": "SOIC", "SO": "SOIC",
    "MSOP": "MSOP", "VSSOP": "MSOP",
    "TSSOP": "TSSOP", "HTSSOP": "TSSOP", "SSOP": "SSOP",
    "DFN": "DFN", "WSON": "DFN", "SON": "DFN", "USON": "DFN", "UDFN": "DFN",
    "QFN": "QFN", "UFQFPN": "QFN", "VQFN": "QFN", "WQFN": "QFN",
    "LQFP": "LQFP", "TQFP": "LQFP",
}
LEADED = {"SOIC", "MSOP", "TSSOP", "SSOP", "LQFP"}
BOTTOM = {"DFN", "QFN"}


def family(text):
    """(CLASS, key) for a land or a catalogue package, or None if this screen
    is not entitled to an opinion about it."""
    if not text:
        return None
    t = text.strip().rsplit(":", 1)[-1]
    m = RE_CHIP_LAND.match(t) or RE_CHIP_BARE.match(t)
    if m:
        return ("CHIP", m.group(1))
    m = RE_BODY.match(t.replace("(", " ").replace(")", " "))
    if m and m.group(1).upper() in BODY_CLASS:
        return (BODY_CLASS[m.group(1).upper()], int(m.group(2)))
    return None


def chip_size(land):
    m = RE_CHIP.match(land.rsplit(":", 1)[-1])
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", type=Path, default=S.PACKAGE)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--worklist", type=Path,
                    help="write the lines that cannot be bought for the first"
                         " build off this catalogue, as a purchasing brief")
    ap.add_argument("--boards", type=int, default=5)
    ap.add_argument("--liquidity", type=int, default=10)
    a = ap.parse_args()

    bom = S.rows(a.package / "aqroot-Demo-BOM-assembly.csv")
    if not bom:
        raise SystemExit("no assembly BOM -- run export_fab_package.py")

    match, mismatch, uncomparable, unlisted = [], [], [], []
    for row in bom:
        code = (row.get("LCSC") or "").strip()
        mpn = (row.get("MPN") or "").strip()
        land = S.leaf(row["Footprint"])
        refs = [r for r in row["Refs"].split(",") if r]
        if not code:
            continue
        doc = fetch(code, pages=1, refresh=a.refresh, quiet=True)
        rec = next((r for r in doc["records"]
                    if r["componentCode"] == code), None)
        entry = dict(refs=refs, value=row["Value"], footprint=land,
                     mpn=mpn, lcsc=code, fetched_utc=doc["fetched_utc"])
        if rec is None:
            unlisted.append(dict(entry, why="the code returns no record"))
            continue
        entry["record_mpn"] = rec["componentModelEn"]
        entry["record_package"] = rec["componentSpecificationEn"]
        entry["stock"] = rec["stockCount"]
        entry["library"] = rec["componentLibraryType"]
        if mpn and rec["componentModelEn"] and \
                mpn.upper().replace(" ", "") != \
                rec["componentModelEn"].upper().replace(" ", ""):
            entry["mpn_differs_from_record"] = True
        board, part = family(land), family(rec["componentSpecificationEn"])
        if board is None or part is None or (board[0] == "CHIP") != \
                (part[0] == "CHIP"):
            uncomparable.append(dict(entry, why=(
                "this screen has no comparable reading of the land %r against"
                " the catalogue package %r"
                % (land, rec["componentSpecificationEn"]))))
            continue
        entry["board_family"] = "%s-%s" % board
        entry["record_family"] = "%s-%s" % part
        ok = board == part
        if not ok and board[0] != "CHIP" and board[1] == part[1]:
            entry["termination_change"] = (
                "LEADED -> BOTTOM-TERMINATED (FBV2-PWR-002 forbids this on the"
                " safety parts)"
                if board[0] in LEADED and part[0] in BOTTOM else
                "BOTTOM-TERMINATED -> leaded"
                if board[0] in BOTTOM and part[0] in LEADED else
                "same pin count, different body family")
        (match if ok else mismatch).append(entry)

    zero = sorted((dict(refs=e["refs"], mpn=e["mpn"], lcsc=e["lcsc"],
                        stock=e["stock"])
                   for e in match + mismatch if e.get("stock") == 0),
                  key=lambda z: z["refs"])
    doc = dict(schema=1, package=str(a.package),
               lines_with_a_code=len(match) + len(mismatch)
               + len(uncomparable) + len(unlisted),
               verdict="FAIL" if mismatch or unlisted else "PASS",
               summary=dict(MATCH=len(match), MISMATCH=len(mismatch),
                            UNCOMPARABLE=len(uncomparable),
                            UNLISTED=len(unlisted)),
               zero_stock=zero,
               mpn_differs_from_record=[
                   dict(refs=e["refs"], bom_mpn=e["mpn"], lcsc=e["lcsc"],
                        record_mpn=e["record_mpn"])
                   for e in match + mismatch + uncomparable
                   if e.get("mpn_differs_from_record")],
               MISMATCH=mismatch, UNLISTED=unlisted,
               UNCOMPARABLE=uncomparable, MATCH=match)
    # A stock number is not a verdict.  Several of these are CONSIGNED parts
    # under D-206 and are bought from a broadline distributor, not from the
    # assembler -- so this is a brief to work, not a failure to report.
    short = sorted((e for e in match + mismatch + uncomparable
                    if e.get("stock") is not None
                    and e["stock"] < len(e["refs"]) * a.boards * a.liquidity),
                   key=lambda e: (e["stock"], e["refs"]))
    doc["short_on_the_assemblers_catalogue"] = [
        dict(refs=e["refs"], mpn=e["mpn"] or e["record_mpn"], lcsc=e["lcsc"],
             stock=e["stock"], first_five_need=len(e["refs"]) * a.boards,
             library=e["library"], fetched_utc=e["fetched_utc"])
        for e in short]
    if a.out:
        a.out.write_text(json.dumps(doc, indent=1, sort_keys=True,
                                    default=str) + "\n")
    if a.worklist:
        with a.worklist.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Refs", "Qty", "First_five_need", "MPN", "LCSC",
                        "JLC_library", "JLC_stock", "Read_utc", "Note"])
            for e in short:
                w.writerow([" ".join(e["refs"]), len(e["refs"]),
                            len(e["refs"]) * a.boards,
                            e["mpn"] or e["record_mpn"], e["lcsc"],
                            e["library"], e["stock"], e["fetched_utc"],
                            "under %dx the first-five need on the assembler's"
                            " own catalogue; D-206 may already class this"
                            " part CONSIGNED from a broadline distributor"
                            % a.liquidity])
    print(json.dumps({k: doc[k] for k in
                      ("lines_with_a_code", "summary", "verdict")},
                     indent=1, sort_keys=True))
    for e in mismatch:
        print("  MISMATCH  %-14s land %-28s record %-20s %s"
              % (" ".join(e["refs"])[:14], e["footprint"],
                 e["record_package"], e.get("termination_change", "")))
    for e in unlisted:
        print("  UNLISTED  %-14s %s (%s)"
              % (" ".join(e["refs"])[:14], e["mpn"], e["lcsc"]))
    print("  UNCOMPARABLE (stated, not counted as a pass): %d line(s)"
          % len(uncomparable))
    if zero:
        print("  ZERO STOCK on %d line(s): %s"
              % (len(zero), ", ".join("%s %s" % (" ".join(z["refs"]), z["mpn"])
                                      for z in zero)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
