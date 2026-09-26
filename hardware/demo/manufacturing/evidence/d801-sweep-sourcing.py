#!/usr/bin/env python3
"""D-801 -- re-sweep every exact MPN on the RELEASED assembly BOM, with its freshness.

D-801 / Round-20 D801-08 (Fable R20-03).  D-800's sweep called itself "live"
while `jlc_live.fetch` REPLAYED cache records fetched 2026-09-05..21, because
`refresh` defaulted to False.  This sweep carries `fetched_utc` and the MODE
(`refresh` = queried now, `replay` = read from the archive) on EVERY row, and
the report states the oldest and newest fetch it rests on.  Nothing here is
called live unless it was fetched in this run.

    python3 evidence/d801-sweep-sourcing.py --refresh [-o evidence/d801-sourcing-sweep.json]

R7-N05 found the D-789 sweep carrying `R40 = ARG03BTC1783` -- the D-787 part --
after the divider had already moved twice inside the same milestone.  An archive
hand-built beside the BOM drifts from it; this script READS the released BOM, so
it cannot.

    python3 `need5` is the per-board quantity times the five-board build.  A line whose live
stock is under `need5` is a CONSIGNMENT line: buy the exact part from a
franchised distributor and ship it to the assembler.  Archived counts are NOT
purchasing authority -- re-check immediately before the order.
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "hardware/demo/manufacturing"))
import jlc_live                                                  # noqa: E402

BOM = ROOT / "hardware/demo/fab/aqroot-Demo-BOM-assembly.csv"
OUT = ROOT / "hardware/demo/manufacturing/evidence/d801-sourcing-sweep.json"
FIRST_FIVE = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path, default=OUT)
    # D-802: the tool is reused for the next release's sweep; the decision it
    # stamps is an argument, not a constant.
    ap.add_argument("--decision", default="D-801")
    ap.add_argument("--refresh", action="store_true",
                    help="query JLCPCB now for every line (archived); "
                         "without it every row is a REPLAY of the archive")
    a = ap.parse_args()
    run_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
            doc = jlc_live.fetch(mpn, pages=1, quiet=True, refresh=a.refresh)
            rec = next((r for r in doc["records"]
                        if (r.get("componentModelEn") or "").strip().upper()
                        == mpn.upper()), None)
            if rec is None:
                rec = next((r for r in doc["records"]
                            if (r.get("componentCode") or "") == lcsc), None)
            row = dict(refs=refs, mpn=mpn, lcsc=lcsc, qty=qty,
                       need5=qty * FIRST_FIVE,
                       fetched_utc=doc.get("fetched_utc"),
                       mode=("refresh" if doc.get("fetched_utc", "")
                             >= run_utc else "replay"))
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

    fetched = sorted(r["fetched_utc"] for r in rows if r.get("fetched_utc"))
    modes = sorted({r["mode"] for r in rows})
    report = dict(
        schema=2, decision=a.decision,
        run_utc=run_utc,
        refresh_requested=bool(a.refresh),
        modes=modes,
        oldest_fetch_utc=fetched[0] if fetched else None,
        newest_fetch_utc=fetched[-1] if fetched else None,
        freshness=("LIVE: every row was fetched in this run"
                   if modes == ["refresh"] else
                   "REPLAY / CACHED: rows were read from the archive at the "
                   "fetched_utc each carries -- NOT live; a fresh re-sweep "
                   "remains a procurement gate"),
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
    print("lines %d   short/unknown %d   modes %s   fetched %s .. %s -> %s"
          % (len(rows), len(set(short)), modes, report["oldest_fetch_utc"],
             report["newest_fetch_utc"], a.out))
    for m in sorted(set(short)):
        r = next(x for x in rows if x["mpn"] == m)
        print("  %-28s %-10s need %-4s stock %s %s"
              % (m, r["lcsc"], r["need5"], r["stock"], r["no_buy"] or ""))


if __name__ == "__main__":
    main()
