#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: which open-edge pads are ENCLOSED, and by whose copper?

Every whole-board maze failure on this board is one of two shapes.  `NO_PATH`
means the corridor is congested and a better search might still find one.
`NO_LEGAL_ESCAPE` means something much harder: the terminal cannot launch AT
ALL, so no amount of searching helps and the net is dead until the geometry
around the pad changes.

The router reports which nets fail.  It does not report WHY a terminal is
enclosed, and that difference decides what the next framework must be:

  * enclosed by PADS only        -- a placement/package wall.  No routing lever
                                    opens it; the footprint or the placement
                                    has to change, or the net is NC by scope.
  * enclosed by a foreign TRACK  -- a RIP-UP candidate.  Copper this project
                                    laid earlier is standing in the doorway of
                                    a pad it did not know it would need, which
                                    is an ordinary, reversible routing mistake
                                    and not a fabrication wall.

This script spends no copper and writes no board.  For every pad that owns an
open edge it asks `maze3d.pad_escapes` -- the SAME primitive the router uses,
at the net's own contract width and clearance -- and for every pad that comes
back empty it then runs a DELETION EXPERIMENT: for each foreign net with copper
in the pad's neighbourhood, that net's local segments are removed from the
obstacle set, the lattice is rebuilt and the escape question is asked again.
A net whose removal turns 0 escapes into N is named, with N, as the blocker.

Removing the segments is done on the in-memory obstacle model only.  The board
file is opened read-only and never written.
"""

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

WINDOW = 2000000        # nm: how far around a pad counts as "the doorway"


def neighbourhood(qb, pad, layers, win=WINDOW):
    """Foreign copper within `win` of this pad, split by net and kind."""
    px, py = pad["x"], pad["y"]
    by_net = {}
    for L in layers:
        for s in qb.shapes[L]:
            if s.net == pad["net"] or s.net is None:
                continue
            x0, y0, x1, y1 = s.bbox(0)
            if x1 < px - win or x0 > px + win or y1 < py - win or y0 > py + win:
                continue
            rec = by_net.setdefault(s.net, dict(pads=0, tracks=0, layers=set()))
            rec["layers"].add(L)
            rec["tracks" if s.tag == "track" else "pads"] += 1
    return by_net


def try_without(qb, field, pad, net_to_drop, layers, limit):
    """Escapes this pad would have if `net_to_drop`'s TRACKS were not there.

    Only tracks are dropped, never pads: a pad is where a part is soldered and
    cannot be moved by a router, so pretending it is absent would report an
    opening that no rip-up could ever deliver.
    """
    import maze3d as mz
    saved = {}
    for L in layers:
        keep = [s for s in qb.shapes[L]
                if not (s.net == net_to_drop and s.tag == "track")]
        if len(keep) != len(qb.shapes[L]):
            saved[L] = qb.shapes[L]
            qb.shapes[L] = keep
    if not saved:
        return None
    try:
        qb._obs_cache = None
        field.rebuild_blk()
        return mz.pad_escapes(qb, field, pad, None, limit)
    finally:
        for L, orig in saved.items():
            qb.shapes[L] = orig
        qb._obs_cache = None
        field.rebuild_blk()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--nets", nargs="*", help="restrict to these nets")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import net_contract
    import subprocess

    ledger = json.loads(subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "routing_ledger.py"),
         "--board", str(a.board)], check=True, capture_output=True, text=True).stdout)
    open_nets = [r["net"] for r in ledger["nets"] if r["open_edges"] > 0]
    if a.nets:
        open_nets = [n for n in open_nets if n in a.nets]

    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    nk = mz.neck_rule(qb)

    nets_out, enclosed_total, pads_total = [], 0, 0
    for net in open_nets:
        c = net_contract(qb.b, net)
        field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=100000,
                         layers=c["layers"], neck=nk)
        layers = field.layers
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        main = max(islands, key=len)
        rec = dict(net=net, netclass=c["netclass"],
                   width_mm=round(c["width"] / 1e6, 3),
                   clr_mm=round(c["clr"] / 1e6, 3),
                   islands=len(islands), pads=[])
        for g in islands:
            for p in g:
                pads_total += 1
                esc = mz.pad_escapes(qb, field, p, None, a.limit)
                pr = dict(ref=p["ref"], x=round(p["x"] / 1e6, 3),
                          y=round(p["y"] / 1e6, 3),
                          on_main_island=(g is main),
                          escapes=len(esc),
                          layers=sorted({e["layer"] for e in esc}))
                if not esc:
                    enclosed_total += 1
                    nb = neighbourhood(qb, p, layers)
                    pr["neighbourhood"] = {
                        k: dict(pads=v["pads"], tracks=v["tracks"],
                                layers=sorted(v["layers"]))
                        for k, v in sorted(nb.items())}
                    openers = []
                    for foreign in sorted(nb):
                        if not nb[foreign]["tracks"]:
                            continue
                        got = try_without(qb, field, p, foreign, layers, a.limit)
                        if got:
                            openers.append(dict(
                                rip_up_net=foreign, escapes_gained=len(got),
                                layers=sorted({e["layer"] for e in got})))
                    pr["ripup_openers"] = openers
                    pr["verdict"] = ("RIPUP_CANDIDATE" if openers
                                     else "PLACEMENT_WALL")
                rec["pads"].append(pr)
            # only the enclosed ones matter for the summary, but every pad is
            # reported: an escape count of 1 is a near-wall worth seeing too.
        nets_out.append(rec)
        print("  %-46s %2d islands" % (net, len(islands)),
              file=sys.stderr, flush=True)

    ripup = [(r["net"], p) for r in nets_out for p in r["pads"]
             if p.get("verdict") == "RIPUP_CANDIDATE"]
    wall = [(r["net"], p) for r in nets_out for p in r["pads"]
            if p.get("verdict") == "PLACEMENT_WALL"]
    out = dict(schema=1, board=str(a.board),
               board_sha256=ledger["board_sha256"],
               summary=dict(open_nets=len(nets_out), pads_examined=pads_total,
                            enclosed_pads=enclosed_total,
                            ripup_candidates=len(ripup),
                            placement_walls=len(wall),
                            ripup=[dict(net=n, pad=p["ref"],
                                        openers=p["ripup_openers"])
                                   for n, p in ripup],
                            walls=[dict(net=n, pad=p["ref"],
                                        x=p["x"], y=p["y"])
                                   for n, p in wall]),
               nets=nets_out)
    text = json.dumps(out, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
