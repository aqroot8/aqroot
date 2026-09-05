#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- read the LIVE distributor record D-096 demands, and KEEP it.

D-096 is a standing procurement rule: *a part number configured from an
ordering scheme is a hypothesis, not a selection*, and every MPN written into a
locked document must first be confirmed against a live manufacturer or
distributor record showing lifecycle status and stock.  Every prior selection
in this repository that satisfies D-096 -- D-167, D-176, D-179, D-202, D-206,
D-210, D-211, D-223 -- was confirmed against the JLCPCB parts catalogue, which
is the right catalogue to ask because it is also the assembler.

This module does ONE thing: it asks, and it WRITES DOWN THE ANSWER.

    fetched_utc   when the record was read
    endpoint      the URL it came from
    keyword       the exact query
    records       the raw JSON rows, unaltered

The archive lives in `evidence/jlc-live/` and is committed, so the selection a
later reader inspects is the record that was actually read, not a re-query that
may have moved.  A cached query is REPLAYED unless `--refresh` is given, which
is what makes a ruling built on top of this deterministic.

    python3 jlc_live.py --query "2.2k 0603 resistor" [--pages 3] [--refresh]

An MPN or an LCSC code is itself a fine keyword; that is how a specific part is
re-confirmed rather than searched for.
"""

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / "evidence/jlc-live"

ENDPOINT = ("https://jlcpcb.com/api/overseas-pcb-order/v1"
            "/shoppingCart/smtGood/selectSmtComponentList")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
      " Chrome/125.0 Safari/537.36")
PAGE_SIZE = 25

# The rows worth keeping.  The endpoint returns image ids, sort access keys and
# highlight markup as well; none of it is evidence and all of it is noise in a
# committed file.
KEEP = ("componentCode", "componentLibraryType", "componentBrandEn",
        "componentModelEn", "componentSpecificationEn", "componentTypeEn",
        "stockCount", "describe", "attributes", "componentPrices",
        "dataManualUrl", "lcscGoodsUrl", "rohsFlag", "minPurchaseNum",
        "leastPatchNumber", "lossNumber", "erpComponentName",
        "assemblyComponentFlag", "isBuyComponent", "noBuyReason")


def slug(keyword):
    clean = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")[:48]
    return "%s-%s" % (clean, hashlib.sha256(
        keyword.encode("utf-8")).hexdigest()[:8])


def _post(keyword, page):
    body = json.dumps({"currentPage": page, "pageSize": PAGE_SIZE,
                       "keyword": keyword}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"content-type": "application/json", "user-agent": UA})
    with urllib.request.urlopen(req, timeout=90) as fh:
        return json.load(fh)


def fetch(keyword, pages=2, cache=CACHE, refresh=False, quiet=False):
    """The live record for `keyword`, read once and then replayed."""
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / ("%s.json" % slug(keyword))
    if path.exists() and not refresh:
        doc = json.loads(path.read_text())
        if doc.get("pages", 0) >= pages or doc.get("exhausted"):
            return doc

    rows, total, exhausted = [], None, False
    for page in range(1, pages + 1):
        for attempt in range(3):
            try:
                raw = _post(keyword, page)
                break
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt == 2:
                    raise SystemExit("JLCPCB query %r failed: %s"
                                     % (keyword, exc))
                time.sleep(2 * (attempt + 1))
        if raw.get("code") != 200 or not raw.get("data"):
            raise SystemExit("JLCPCB refused %r: %s"
                             % (keyword, raw.get("message")))
        info = raw["data"]["componentPageInfo"]
        total = info.get("total")
        got = info.get("list") or []
        rows.extend({k: r.get(k) for k in KEEP} for r in got)
        if len(got) < PAGE_SIZE:
            exhausted = True
            break

    doc = dict(schema=1, endpoint=ENDPOINT, keyword=keyword,
               fetched_utc=datetime.now(timezone.utc).strftime(
                   "%Y-%m-%dT%H:%M:%SZ"),
               total_matches=total, pages=pages, page_size=PAGE_SIZE,
               exhausted=exhausted, returned=len(rows), records=rows)
    path.write_text(json.dumps(doc, indent=1, sort_keys=True,
                               ensure_ascii=False) + "\n")
    if not quiet:
        print("  live: %-44s %4d rows  (%s)"
              % (keyword[:44], len(rows), path.name))
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    doc = fetch(a.query, a.pages, refresh=a.refresh)
    print("%s  total=%s returned=%s" % (doc["fetched_utc"],
                                        doc["total_matches"], doc["returned"]))
    for r in doc["records"]:
        attrs = {x["attribute_name_en"]: x["attribute_value_name"]
                 for x in (r.get("attributes") or [])}
        print("%-11s %-7s stock=%-10s %-24s %-28s %s"
              % (r["componentCode"], r["componentLibraryType"],
                 r["stockCount"], (r["componentBrandEn"] or "")[:24],
                 (r["componentModelEn"] or "")[:28], attrs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
