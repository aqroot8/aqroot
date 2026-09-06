#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what does cutting THIS piece of the return pour cost?

D-643 replaced `PP2`'s unconditional refusal of every `GND` split with a
PRICE: a return fragment must carry one track of its own netclass width
(0.995 A here), raised to any RAIL current section 5 publishes for a net on the
SAME FOOTPRINT as one of the fragment's pads -- Kirchhoff, not a model, since
the current into a part's ground pin is bounded by what its other pins carry.

That turns "can this pour be cut?" from a yes/no into a number, and a number is
only useful if it can be read BEFORE a router is spent.  This screen reads it.
For every island of every RETURN pour it reports, pad by pad, the bar that pad
would set on any fragment it lands on, and which part and rail set it.  A
router aimed at a 0.995 A island is aimed at a cheap cut; one aimed at a
3.125 A island beside the battery front end is aimed at a wall, and it costs
nothing to know which before the run.

WHAT IT DOES NOT SAY.  It does not price a fragment: a fragment's price is its
own barrels and its own copper, which do not exist until a cut does.  It says
what that price will be CHARGED AGAINST.  `pour_partition_contract.PP2` remains
the only thing that admits or refuses a split, and this screen calls the same
`return_fragment_bar` it does, so the two cannot drift.

    python3 screen_return_fragment_bar.py [--board B] [--min-pads N] [-o OUT]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "checks"))

import importlib.util


def contract():
    spec = importlib.util.spec_from_file_location(
        "pour_partition_contract", HERE / "checks/pour_partition_contract.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("--min-pads", type=int, default=2,
                    help="an island with fewer pads than this cannot be SPLIT "
                         "into two pad-bearing pieces and is not reported")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    import pcbnew
    import pour_bond_guard as pg
    m = contract()

    board_path = Path(a.board)
    dru = board_path.with_suffix(".kicad_dru")
    pro = board_path.with_suffix(".kicad_pro")
    if not dru.exists():
        dru = PROJECT / "aqroot-Beta-v2.kicad_dru"
    if not pro.exists():
        pro = PROJECT / "aqroot-Beta-v2.kicad_pro"
    table, table_src = m.published_rail_currents(dru)
    classes, class_src = m.netclass_conductors(pro)
    netclass_of, pads_by_footprint = m.board_nets_and_pads(board_path)
    planes, reserved = m.reserved_plane_zones(board_path)
    returns = m.return_nets(planes, reserved, netclass_of, table)

    board = pcbnew.LoadBoard(str(board_path))
    pours = pg.read_pours(board)
    for p in pours:
        pg.assign(board, p)

    out = []
    for p in pours:
        if p["net"] not in returns:
            continue
        cls = netclass_of.get(p["net"])
        for i, e in enumerate(p["islands"]):
            refs = sorted(q["ref"] for q in e["pads"])
            if len(refs) < a.min_pads:
                continue
            per = []
            for ref in refs:
                bar, prov = m.return_fragment_bar(
                    p["net"], cls, [ref], pads_by_footprint, netclass_of,
                    classes, table)
                per.append(dict(pad=ref, bar_amps=bar,
                                bar_from=prov["bar_from"],
                                set_by=sorted({(n["other_netclass"],
                                                n["other_net"])
                                               for n in prov["neighbour_rails"]
                                               if n["published_amps"] == bar})))
            whole, wprov = m.return_fragment_bar(
                p["net"], cls, refs, pads_by_footprint, netclass_of,
                classes, table)
            bars = [r["bar_amps"] for r in per]
            out.append(dict(
                net=p["net"], layer=p["layer"], zone=p["zone_name"],
                island=i, area_mm2=round(e["area_mm2"], 3),
                pads=refs, n_vias=len(e["vias"]),
                whole_island_bar_amps=whole,
                cheapest_pad_bar_amps=min(bars), dearest_pad_bar_amps=max(bars),
                at_the_floor=all(r["bar_from"]
                                 == "RETURN_FLOOR_ONE_NETCLASS_TRACK"
                                 for r in per),
                pads_priced=per))
    out.sort(key=lambda r: (-r["dearest_pad_bar_amps"], -r["area_mm2"]))

    doc = dict(schema=1, board=str(board_path),
               board_sha256=hashlib.sha256(board_path.read_bytes()).hexdigest(),
               return_nets=returns,
               netclass_floor={k: (classes.get(v.get("netclass")) or {})
                               .get("track_width_mm")
                               for k, v in returns.items()},
               published_rail_currents={k: v["amps"]
                                        for k, v in sorted(table.items())},
               published_table_source=table_src, netclass_source=class_src,
               min_pads=a.min_pads, islands=out,
               summary=dict(
                   islands=len(out),
                   at_the_floor=sum(1 for r in out if r["at_the_floor"]),
                   above_the_floor=sum(1 for r in out
                                       if not r["at_the_floor"]),
                   dearest=(out[0]["dearest_pad_bar_amps"] if out else None)))
    txt = json.dumps(doc, indent=2, sort_keys=True)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8")
    for r in out:
        print("%-4s island %-4d %9.3f mm2  %2d pads %2d vias  bar %6.3f A  %s"
              % (r["layer"], r["island"], r["area_mm2"], len(r["pads"]),
                 r["n_vias"], r["dearest_pad_bar_amps"],
                 "FLOOR" if r["at_the_floor"] else "NEIGHBOUR RAIL"))
    print("islands %d  at the floor %d  above it %d"
          % (doc["summary"]["islands"], doc["summary"]["at_the_floor"],
             doc["summary"]["above_the_floor"]))


if __name__ == "__main__":
    main()
