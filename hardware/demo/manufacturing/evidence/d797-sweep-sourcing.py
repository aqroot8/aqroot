#!/usr/bin/env python3
"""D-797 -- re-sweep every exact MPN on the RELEASED assembly BOM, live.

R7-N05 found the D-789 sweep carrying `R40 = ARG03BTC1783` -- the D-787 part --
after the divider had already moved twice inside the same milestone.  An archive
hand-built beside the BOM drifts from it; this script READS the released BOM, so
it cannot.

    python3 evidence/d797-sweep-sourcing.py [-o evidence/d797-sourcing-sweep.json]

`need5` is the per-board quantity times the five-board build.  A line whose live
stock is under `need5` is a CONSIGNMENT line: buy the exact part from a
franchised distributor and ship it to the assembler.  Archived counts are NOT
purchasing authority -- re-check immediately before the order.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "hardware/demo/manufacturing"))
import jlc_live                                                  # noqa: E402

BOM = ROOT / "hardware/demo/fab/aqroot-Demo-BOM-assembly.csv"
OUT = ROOT / "hardware/demo/manufacturing/evidence/d797-sourcing-sweep.json"
FIRST_FIVE = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path, default=OUT)
    a = ap.parse_args()

    rows, short = [], []
    with BOM.open(newline="", encoding="utf-8") as fh:
        for line in csv.DictReader(fh):
            mpn = (line.get("MPN") or "").strip()
            lcsc = (line.get("LCSC") or "").strip()
            refs = (line.get("Refs") or "").strip()
            try:
                qty = int(float(line.get("Qty") or 0))
            except ValueError:
                qty = 0
            if not mpn:
                continue
            doc = jlc_live.fetch(mpn, pages=1, quiet=True)
            rec = next((r for r in doc["records"]
                        if (r.get("componentModelEn") or "").strip().upper()
                        == mpn.upper()), None)
            if rec is None:
                rec = next((r for r in doc["records"]
                            if (r.get("componentCode") or "") == lcsc), None)
            row = dict(refs=refs, mpn=mpn, lcsc=lcsc, qty=qty,
                       need5=qty * FIRST_FIVE)
            if rec is None:
                row.update(stock=None, record_lcsc=None, brand=None,
                           library=None, buyable=None, no_buy=None,
                           note="no live record matched this exact MPN")
                short.append(row["mpn"])
            else:
                row.update(stock=rec.get("stockCount"),
                           record_lcsc=rec.get("componentCode"),
                           brand=rec.get("componentBrandEn"),
                           library=rec.get("componentLibraryType"),
                           buyable=str(rec.get("isBuyComponent")),
                           no_buy=rec.get("noBuyReason"),
                           note=None)
                if (rec.get("stockCount") or 0) < row["need5"]:
                    short.append(row["mpn"])
            rows.append(row)

    report = dict(
        schema=1, decision="D-797",
        what_this_is=__doc__.strip().splitlines()[0],
        method="every exact MPN on hardware/demo/fab/aqroot-Demo-BOM-assembly.csv, "
               "queried through the D-096 JLCPCB parts API and archived so the "
               "consignment plan replays rather than re-queries.  Archived "
               "counts are NOT purchasing authority -- re-check immediately "
               "before the order.",
        source=str(BOM.relative_to(ROOT)),
        assembly_lines=len(rows),
        short_or_unknown=sorted(set(short)),
        rows=rows)
    a.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("lines %d   short/unknown %d -> %s"
          % (len(rows), len(set(short)), a.out))
    for m in sorted(set(short)):
        r = next(x for x in rows if x["mpn"] == m)
        print("  %-28s %-10s need %-4s stock %s %s"
              % (m, r["lcsc"], r["need5"], r["stock"], r["no_buy"] or ""))


if __name__ == "__main__":
    main()
