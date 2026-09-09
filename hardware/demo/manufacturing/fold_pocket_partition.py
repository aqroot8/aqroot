#!/usr/bin/env python3
"""D-670: fold the frontier pocket ladders into ONE machine-readable partition.

The ladder answers per LAND.  A decision is made per NET, and the class that
matters is the WEAKEST land on the net: a net whose every land has a barrel
site is a corridor question; a net with one NO_ESCAPE land is a placement one
however open its other end reads.  D-669's item (2) named `/SX1262_DIO1` as an
easy target off `U8.13`'s 223,208 via-legal cells and that is the OTHER end.
"""
import json
import sys
from pathlib import Path

RANK = {"NO_ESCAPE_AT_ANY_PITCH": 0, "SEALED": 1, "RASTER": 2,
        "HAS_VIA_SITE": 3}

def main(out, srcs, extra):
    ev = Path("evidence")
    lands, docs = {}, {}
    for name in srcs + extra:
        p = ev / name
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        docs[name] = d["board_sha256"]
        for n in d["nets"]:
            for l in n["lands"]:
                key = (n["net"], l["pad"])
                # a later doc (an --all-lands/--blame re-ask) supersedes an
                # earlier one for the SAME land: same board, same contract,
                # and it may carry a `blame` the first pass had no flag for.
                lands[key] = dict(
                    net=n["net"], netclass=n["netclass"],
                    has_plane=n["has_plane"], pad=l["pad"],
                    island=l["island"], verdict=l["verdict"],
                    area_min_mm2=l["area_min_mm2"],
                    area_max_mm2=l["area_max_mm2"], growth=l["growth"],
                    via_legal_max=max(r["via_legal_in_pocket"]
                                      for r in l["rungs"]),
                    escapes_finest=l["rungs"][-1]["escapes"],
                    source=name,
                    blame=(l.get("blame") or {}).get("verdict"),
                    blame_material=(l.get("blame") or {}).get(
                        "material_verdict"),
                    blame_units=[u["unit"] for u in
                                 (l.get("blame") or {}).get(
                                     "material_unit_openers",
                                     (l.get("blame") or {}).get(
                                         "single_unit_openers", []))],
                    blame_nets=[u["net"] for u in
                                (l.get("blame") or {}).get(
                                    "single_net_openers", [])])
    assert len(set(docs.values())) == 1, docs
    nets = {}
    for rec in lands.values():
        nets.setdefault(rec["net"], []).append(rec)
    rows = []
    for net in sorted(nets):
        ls = sorted(nets[net], key=lambda r: RANK[r["verdict"]])
        by = {}
        for r in ls:
            by[r["verdict"]] = by.get(r["verdict"], 0) + 1
        rows.append(dict(net=net, netclass=ls[0]["netclass"],
                         has_plane=ls[0]["has_plane"],
                         weakest_land=ls[0]["pad"],
                         net_class_of_wall=ls[0]["verdict"],
                         lands_by_class=by,
                         lands=ls))
    doc = dict(
        schema=1,
        board_sha256=next(iter(docs.values())),
        sources=docs,
        question=("for each of the fifteen OPEN retained nets, what class of "
                  "wall does its WEAKEST land carry -- and where the land is "
                  "SEALED, which foreign object opens it"),
        rule=("`net_class_of_wall` is the net's WEAKEST land, because one "
              "unlaunchable land refuses that net's completion however open "
              "its other end reads.  It is NOT the class of every EDGE: a net "
              "with four islands has an independent edge per island and each "
              "is worth one ledger edge on its own, so read `lands_by_class` "
              "and the per-land rows before choosing a target.  `/I2C_SCL_INT` "
              "is the case that forces the distinction -- weakest land `U16.3` "
              "SEALED, and `TP5.1` carries 956 via-legal cells"),
        caveat=("A POCKET VERDICT IS NECESSARY, NOT SUFFICIENT.  It answers "
                "about the LAUNCH.  D-670 proved the gap on `/ACC_PWR_EN`: the "
                "blame named ONE unit, arms A/B/D removed that unit AND its "
                "neighbour, and the net was still NO_PATH at 0.100, 0.050 and "
                "0.025 mm with 10-19 source escapes -- the pocket opened and "
                "the CORRIDOR did not"),
        counts={k: sum(1 for r in rows if r["net_class_of_wall"] == k)
                for k in RANK},
        nets=rows)
    Path(out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print(json.dumps(doc["counts"], indent=1))
    for r in rows:
        print("%-34s %-22s weakest %-8s %s" % (
            r["net"][-34:], r["net_class_of_wall"], r["weakest_land"],
            r["lands"][0]["blame"] or ""))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--ladder", action="append", required=True,
                    help="a screen_escape_pocket.py ladder report, by basename "
                         "under evidence/.  Repeatable")
    ap.add_argument("--blame", action="append", default=[],
                    help="a --blame report for the SAME board; a later doc "
                         "supersedes an earlier one for the same land, so a "
                         "re-ask that carries a blame replaces the ladder-only "
                         "row it refines.  Repeatable")
    _a = ap.parse_args()
    raise SystemExit(main(_a.out, _a.ladder, _a.blame))
