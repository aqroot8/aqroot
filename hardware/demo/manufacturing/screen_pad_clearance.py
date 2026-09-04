#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: which open edges does the PAD clearance decide?

A clearance this board owes a PAD is not the one it owes a TRACK, and
`aqroot-Beta-v2.kicad_dru` says so in its own words.  Every elevated figure in
`route_maze_batch.DRU_CLASS["clr"]` comes from a section-8 "routed clearance"
rule, and every one of those rules carries `A.Type != 'Pad' && B.Type != 'Pad'`.
The section states the intent rather than leaving it to be inferred:

    Elevated clearances below are ROUTING clearances: they are scoped so
    that vendor land patterns (J1 FH69 0.5 mm pitch, J3 USB-C, U11 WSON
    0.4 mm pitch, U12 VSON, U14 WLP) are judged against the 0.20 mm
    global figure they actually satisfy, not against a routing target.

`net_contract` used to collapse both into ONE scalar and every caller handed it
to `maze3d.Field` as BOTH `clr_pad` and `clr_trk`, so the proposer owed a PAD a
routing target the board judges at 0.20 mm.  That is not conservatism, it is a
DIFFERENT rule -- and a fine-pitch land pattern is exactly where the extra
tenths decide whether a pin can launch at all.

This screen is the instrument that priced the split and it is kept because the
question recurs: after every promotion the answer can change, and the whole
value of the lever is knowing WHICH edge it is worth spending a gate run on.

METHOD.  Read-only, on the board as it stands.  For every open retained net, or
the ones named, two `maze3d.Field`s are built that differ in `clr_pad` ALONE --
the legacy collapsed figure `clr_trk`, and the contract's own `clr_pad` (or
`--pad-clr`) -- and every island-MST edge is offered to the real
`maze3d.route_join` with `emit=False`, so no edge sees copper an earlier one
would have laid.  `--neck` additionally measures the current figure with the
`.kicad_dru` pad-escape necking rule live, because a pad that cannot launch at
full width is the other half of the same question.

OPTIMISTIC BY CONSTRUCTION, exactly as `screen_evict_rebuild.py` is: an edge
reported OK here has been proved routable ALONE on today's copper, which is a
licence to spend a gate run and nothing more.  A net whose every edge is
unchanged is a reliable REFUSAL for this lever.
"""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = HERE / "routing_ledger.py"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def centroid(group, key):
    return sum(p[key] for p in group) / float(len(group))


def edges_for(qb, mz, field, islands, via_cost, escape_limit):
    rows = []
    for (i, j) in mz.island_mst(islands):
        src, dst = islands[i], islands[j]
        r = mz.route_join(qb, field, src, dst, escape_limit, via_cost,
                          emit=False)
        rows.append(dict(
            src=[p["ref"] for p in src], dst=[p["ref"] for p in dst],
            ok=bool(r.get("ok")), reason=r.get("reason"),
            mm=round(r.get("mm", 0.0), 3),
            direct_mm=round(math.hypot(
                centroid(src, "x") - centroid(dst, "x"),
                centroid(src, "y") - centroid(dst, "y")) / 1e6, 3)))
    return rows


def open_retained_nets(board):
    led = json.loads(subprocess.run(
        [sys.executable, str(LEDGER), "--board", str(board)],
        check=True, capture_output=True, text=True).stdout)
    return [r["net"] for r in led["nets"] if r["open_edges"] > 0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--net", action="append", default=[], metavar="NET",
                    help="restrict to these nets; default is every net the "
                         "routing ledger reports with an open retained edge")
    ap.add_argument("--pad-clr", type=int, default=0, metavar="NM",
                    help="pad clearance to measure INSTEAD of the contract's "
                         "own `clr_pad` (0 = use the contract).  A figure "
                         "below the board's 0.20 mm global clearance is a "
                         "screen result and never a promotable one")
    ap.add_argument("--neck", action="store_true",
                    help="also measure the contract figure with the "
                         "`.kicad_dru` pad-escape necking rule live")
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--escape-limit", type=int, default=8)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, sha256_file)

    nets = a.net or open_retained_nets(a.board)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    nk = mz.neck_rule(qb) if a.neck else None

    out, changed = [], 0
    for net in nets:
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        want = a.pad_clr or c["clr_pad"]

        def field(clr_pad, neck=None):
            return mz.Field(qb, net, c["width"], clr_pad, c["clr"],
                            c["via_dia"], c["via_drill"], G=a.grid,
                            layers=layers, neck=neck)

        legacy = edges_for(qb, mz, field(c["clr"]), islands,
                           a.via_cost, a.escape_limit)
        split = edges_for(qb, mz, field(want), islands,
                          a.via_cost, a.escape_limit)
        rec = dict(net=net, netclass=c["netclass"],
                   width_mm=c["width"] / 1e6,
                   clr_trk_mm=c["clr"] / 1e6, pad_clr_mm=want / 1e6,
                   mst_edges=len(legacy),
                   ok_collapsed=sum(1 for e in legacy if e["ok"]),
                   ok_pad_split=sum(1 for e in split if e["ok"]),
                   reasons_collapsed=[e["reason"] for e in legacy
                                      if not e["ok"]],
                   reasons_pad_split=[e["reason"] for e in split
                                      if not e["ok"]])
        rec["changed"] = rec["ok_pad_split"] != rec["ok_collapsed"]
        rec["opened_edges"] = [
            dict(src=s["src"], dst=s["dst"], mm=s["mm"],
                 direct_mm=s["direct_mm"], was=l["reason"])
            for l, s in zip(legacy, split) if s["ok"] and not l["ok"]]
        if nk is not None:
            necked = edges_for(qb, mz, field(want, nk), islands,
                               a.via_cost, a.escape_limit)
            rec["ok_pad_split_neck"] = sum(1 for e in necked if e["ok"])
        changed += bool(rec["changed"])
        out.append(rec)
        print("  %-46s %-11s %d/%d -> %d/%d%s"
              % (net, c["netclass"], rec["ok_collapsed"], rec["mst_edges"],
                 rec["ok_pad_split"], rec["mst_edges"],
                 "   CHANGED" if rec["changed"] else ""),
              file=sys.stderr, flush=True)

    doc = dict(
        schema=1, board=str(a.board.relative_to(ROOT)),
        board_sha256=sha256_file(a.board),
        question="which open retained edges does the PAD clearance decide, "
                 "read at the .kicad_dru's own pad figure instead of the "
                 "elevated ROUTING figure the same rule scopes away from pads",
        method="read-only; per net two maze3d.Field objects differing in "
               "clr_pad ALONE, every island-MST edge offered to the real "
               "maze3d.route_join with emit=False",
        neck_measured=bool(a.neck),
        nets_measured=len(out), nets_changed=changed, nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
