#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- how much of the BOM sourcing gap does this repository ALREADY
know the answer to?

`checks/fab_package_contract.py` FAB7 measures the gap: of the fitted,
purchased, on-board references in the Demo assembly BOM, most carry neither a
manufacturer part number nor an LCSC code, and a line a supplier cannot quote
is not a finished BOM.  That is a number, not a plan.  This screen turns it
into a work list by asking, for every unsourced line, whether an EXISTING
reviewed decision in this repository already answers it.

Three prior authorities, all repo-local, none of them invented here:

  DEMO      the Demo schematic's own sourced lines.  If one 0603 100nF already
            names a part, the next one is not an open question.
  BETA-DM   `hardware/beta-dm/fab/jlcpcb/JLC-MATCH-AUDIT.csv` -- a per-line
            CTO audit of a JLCPCB match, carrying an APPROVED part number, a
            verdict and the reasoning, including explicit dielectric and
            voltage rulings.  This is the strongest prior the repository holds.
  LEDGER    `hardware/beta-dm/fab/BETA-DM-MPN-LEDGER.csv` -- the resolved
            manufacturer identity for the named parts of the same family.

**THE MATCH RULE IS DELIBERATELY BRITTLE.**  A candidate counts as EXACT only
when the value string and the footprint LEAF NAME are equal character for
character.  `10uF 10V X7R` and `10uF` are not the same specification: the first
states a dielectric and a rating and the second states neither, and the
beta-dm audit itself REJECTED two JLC matches for exactly that reason ("JLC
offered X5R against an X7R specification").  Anything that matches only after
case folding or after dropping a rating is reported as `NEAR_MISS` -- a line
that needs a ruling, not a graft.  D-611's lesson is that evidence read at a
moment it is not yet true is still wrong; a part number grafted across a
specification it does not satisfy is the same failure with a purchase order
attached.

Read-only.  It proposes; it changes nothing.

    python3 hardware/demo/manufacturing/screen_bom_sourcing.py \\
        [--package DIR] [-o OUT]
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

PACKAGE = ROOT / "hardware/demo/fab"
AUDIT = ROOT / "hardware/beta-dm/fab/jlcpcb/JLC-MATCH-AUDIT.csv"
LEDGER = ROOT / "hardware/beta-dm/fab/BETA-DM-MPN-LEDGER.csv"


def rows(path):
    if not Path(path).exists():
        return []
    return list(csv.DictReader(Path(path).open(newline="",
                                               encoding="utf-8-sig")))


def leaf(footprint):
    """`Capacitor_SMD:C_0603_1608Metric` and `C_0603_1608Metric` are one land."""
    return footprint.strip().rsplit(":", 1)[-1]


def loose(value):
    """The comparison a NEAR_MISS is allowed to make, and no more."""
    return " ".join(value.split()).casefold()


def priors(demo_bom):
    """(value, footprint-leaf) -> the candidates this repository already holds."""
    out = defaultdict(list)
    for row in demo_bom:
        mpn, lcsc = row.get("MPN", "").strip(), row.get("LCSC", "").strip()
        if mpn or lcsc:
            out[(row["Value"].strip(), leaf(row["Footprint"]))].append(dict(
                source="DEMO", mpn=mpn, lcsc=lcsc,
                manufacturer=row.get("Manufacturer", "").strip(),
                note="already sourced on this board: %s" % row["Refs"]))
    for row in rows(AUDIT):
        part = row.get("Approved JLCPCB Part #", "").strip()
        mpn = row.get("Approved MPN", "").strip()
        if not part and not mpn:
            continue
        out[(row["AQROOT Comment"].strip(),
             leaf(row["AQROOT Footprint"]))].append(dict(
                 source="BETA-DM", mpn=mpn, lcsc=part,
                 manufacturer=row.get("JLC Manufacturer", "").strip(),
                 verdict=row.get("JLC Auto-match Verdict", "").strip(),
                 note=row.get("Audit note", "").strip()))
    for row in rows(LEDGER):
        mpn = row.get("MPN", "").strip()
        if not mpn:
            continue
        out[(row["Value"].strip(), leaf(row["Footprint"]))].append(dict(
            source="LEDGER", mpn=mpn, lcsc="",
            manufacturer=row.get("Manufacturer", "").strip(),
            note=row.get("Status", "").strip()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", type=Path, default=PACKAGE)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    bom = rows(a.package / "aqroot-Demo-BOM-assembly.csv")
    if not bom:
        raise SystemExit("no assembly BOM at %s -- run export_fab_package.py"
                         % a.package)
    known = priors(bom)
    by_loose = defaultdict(list)
    for (value, land), cands in known.items():
        by_loose[(loose(value), land)].extend(
            dict(c, prior_value=value) for c in cands)

    exact, near, none_ = [], [], []
    for row in bom:
        if row.get("MPN", "").strip() or row.get("LCSC", "").strip():
            continue
        value, land = row["Value"].strip(), leaf(row["Footprint"])
        refs = [r for r in row["Refs"].split(",") if r]
        line = dict(refs=refs, qty=len(refs), value=value, footprint=land)
        if known.get((value, land)):
            exact.append(dict(line, candidates=known[(value, land)]))
        elif by_loose.get((loose(value), land)):
            near.append(dict(line, candidates=by_loose[(loose(value), land)],
                             why="matches only after case/whitespace folding"))
        else:
            near_land = sorted({v for v, l in known if l == land})
            none_.append(dict(line, other_values_on_this_land=near_land[:12]))

    def parts(bucket):
        return sum(row["qty"] for row in bucket)

    doc = dict(
        schema=1,
        package=str(a.package),
        assembly_lines=len(bom),
        unsourced_lines=len(exact) + len(near) + len(none_),
        unsourced_parts=parts(exact) + parts(near) + parts(none_),
        summary={
            "EXACT_PRIOR": dict(lines=len(exact), parts=parts(exact)),
            "NEAR_MISS": dict(lines=len(near), parts=parts(near)),
            "NO_CANDIDATE": dict(lines=len(none_), parts=parts(none_)),
        },
        prior_sources=dict(
            DEMO=sum(1 for c in known.values() for x in c
                     if x["source"] == "DEMO"),
            BETA_DM=sum(1 for c in known.values() for x in c
                        if x["source"] == "BETA-DM"),
            LEDGER=sum(1 for c in known.values() for x in c
                       if x["source"] == "LEDGER"),
        ),
        no_candidate_prefixes=dict(Counter(
            r.rstrip("0123456789") for row in none_ for r in row["refs"])),
        EXACT_PRIOR=exact, NEAR_MISS=near, NO_CANDIDATE=none_)

    text = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        a.out.write_text(text)
    print(json.dumps({k: doc[k] for k in
                      ("assembly_lines", "unsourced_lines", "unsourced_parts",
                       "summary", "prior_sources", "no_candidate_prefixes")},
                     indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
