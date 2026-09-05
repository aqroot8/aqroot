#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: the WIDTH at which each open island pair closes,
asked with EXACT-GEOMETRY escapes instead of a lattice.

D-630 split "UNLAUNCHABLE" into four classes and named `LATTICE_EXACT` --
margin exactly zero -- as the one class `maze3d` can never propose at ANY
pitch, because its 0.75-cell guard band strictly exceeds the room at every
lattice.  It named ONE instrument for those lands, `route_local_two_pad`, and
D-631 recorded that it had still never been aimed at the list.

This screen aims it, and it aims it as a LADDER rather than as a yes/no.
`qrouter.connect_role` escapes in EXACT GEOMETRY -- `QBoard.escape` walks eight
directions off the land and tests a straight segment against real obstacle
shapes -- and only the CORRIDOR between the two escapes is rasterised.  So for
a land whose margin is zero the escape is decidable where no lattice can decide
it, and the question stops being "does it route" and becomes "AT WHAT WIDTH",
which is the question a licence is written against.

WHAT IT ASKS.  For one net: `maze3d.net_islands` for the copper that already
joins its lands, then, for every ORDERED PAIR of islands, the `--pairs`
nearest pad-to-pad combinations, each over a descending width ladder.  A pair
stops at the first width that closes, because a wider conductor is always the
better one and the ladder is there to find the widest that works.

WHAT A RESULT MEANS, AND WHAT IT DOES NOT.  A closure here is a LICENCE
QUESTION, never copper: the run is laid on a scratch `QBoard`, proved by
nothing but the router's own clearance arithmetic, and reverted.  `QBoard` does
not see ZONE fill at all, so a corridor this reports may still cross a foreign
pour -- KiCad's own DRC on the full-board gate is the only thing that promotes.
And a width BELOW the net's class floor is copper this board does not license
anywhere until a rule says so; `leaf_land_contract.py` decides whether the rail
current binds it and `.kicad_dru` decides where it may lie.

THE REFUSAL IS THE PRODUCT.  `NO_LEGAL_ESCAPE at >= W mm` names the land AND
the obstacles that blocked it, counted; `NO_PATH` means both ends launched and
the corridor is the wall.  Those are different findings with different
instruments -- a land licence for the first, eviction or placement for the
second -- and reading them off a ladder rather than a single rung says which
one is true at which width.

    python3 screen_lattice_exact_route.py NET [NET ...] [--board B]
        [--widths nm,nm,...] [--pairs N] [--max-gap-mm F] [-o OUT]
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def ladder(top_nm, floor_nm):
    """Descending, in the 0.050 mm steps `QBoard.escape` itself walks, with
    the board's own floor always the last rung."""
    out, w = [], int(top_nm)
    while w > floor_nm:
        out.append(w)
        w -= 50000
    out.append(int(floor_nm))
    return sorted(set(out), reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--widths", default="",
                    help="comma-separated nm rungs; default is the net's own "
                         "contract width down to the board's min_track_width "
                         "in 0.050 mm steps")
    ap.add_argument("--pairs", type=int, default=2,
                    help="nearest pad-to-pad combinations to ask per island "
                         "pair")
    ap.add_argument("--max-gap-mm", type=float, default=0.0,
                    help="skip island pairs whose nearest lands are further "
                         "apart than this (0 = no bound).  A local instrument "
                         "asked about a 90 mm haul is a slow way to learn "
                         "nothing")
    ap.add_argument("--grid", type=int, default=25000,
                    help="corridor lattice, nm.  The ESCAPE is exact at every "
                         "value of this; only the corridor is rasterised")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import net_contract, DRU_CLASS, BOARD_TRACK_MIN

    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)

    report = []
    for net in a.nets:
        c = net_contract(qb.b, net)
        floor = max(BOARD_TRACK_MIN,
                    DRU_CLASS.get(c["netclass"], {}).get("width", 0))
        rungs = ([int(x) for x in a.widths.split(",") if x] if a.widths
                 else ladder(c["width"], BOARD_TRACK_MIN))
        islands = mz.net_islands(qb, net)
        body = max(islands, key=len) if islands else None
        rec = dict(net=net, netclass=c["netclass"], contract=c["width"],
                   dru_floor=floor, board_track_min=BOARD_TRACK_MIN,
                   islands=len(islands), widths=rungs, pairs=[])
        for i, A in enumerate(islands):
            for B in islands[i + 1:]:
                combos = sorted(
                    ((math.hypot(p["x"] - q["x"], p["y"] - q["y"]), p, q)
                     for p in A for q in B), key=lambda t: t[0])
                if a.max_gap_mm and combos[0][0] / 1e6 > a.max_gap_mm:
                    continue
                for gap, p, q in combos[:max(1, a.pairs)]:
                    layers = [L for L in ("F", "B") if p[L] and q[L]]
                    if not layers:
                        rec["pairs"].append(dict(
                            a=p["ref"], b=q["ref"], gap_mm=round(gap / 1e6, 4),
                            layer=None, closed_at=None,
                            reason="NOT_COPLANAR",
                            why="%s and %s share no outer layer; this "
                                "instrument lays no via" % (p["ref"], q["ref"]),
                            rungs=[]))
                        continue
                    layer = layers[0]
                    trials, closed = [], None
                    for w in rungs:
                        m = qb.mark()
                        t0 = time.time()
                        r = qr.connect_role(qb, net, p, q, layer, w,
                                            c["clr_pad"], c["clr"],
                                            G=a.grid)
                        dt = time.time() - t0
                        qb.revert(m)
                        trials.append(dict(
                            width=w, ok=bool(r.get("ok")),
                            reason=r.get("reason"), why=r.get("why"),
                            pad=r.get("pad"), mm=round(r.get("mm", 0.0), 4),
                            profile=r.get("profile"),
                            seconds=round(dt, 2)))
                        if r.get("ok"):
                            closed = w
                            break
                    rec["pairs"].append(dict(
                        a=p["ref"], b=q["ref"], gap_mm=round(gap / 1e6, 4),
                        layer=layer, closed_at=closed,
                        licensed_unconditionally=(closed is not None
                                                  and closed >= floor),
                        reason=trials[-1]["reason"], why=trials[-1]["why"],
                        rungs=trials))
                    print("  %-9s %-9s %7.3f mm  %s"
                          % (p["ref"], q["ref"], gap / 1e6,
                             ("CLOSES at %.3f mm%s" %
                              (closed / 1e6,
                               "" if closed >= floor
                               else "  BELOW the %.3f mm class floor"
                                    % (floor / 1e6)))
                             if closed else
                             "refused: %s" % str(trials[-1]["why"])[:88]),
                          file=sys.stderr, flush=True)
        report.append(rec)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(schema=1, board=str(a.board), board_sha256=sha,
               authoritative_unchanged=(sha == after), grid=a.grid,
               question=("at what WIDTH does each open island pair of this net "
                         "close, asked with qrouter.connect_role's EXACT "
                         "escapes -- the only instrument D-630's LATTICE_EXACT "
                         "class admits"),
               method=("read-only; every trial laid on a scratch QBoard and "
                       "REVERTED; zones invisible to QBoard, so a closure is a "
                       "licence question and never copper"),
               nets=report)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
