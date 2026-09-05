#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- how much room a LAND has to launch, measured, not searched.

Every `NO_LEGAL_ESCAPE_SRC` / `NO_LEGAL_ESCAPE_DST` this project has recorded is
a router telling us something about a package AFTER a whole-board search.  The
question underneath it is arithmetic and needs no search at all:

    given a pad, a direction, a track WIDTH and the clearance that net owes a
    PAD, how much room is left over?

That number -- the MARGIN -- is what decides whether copper is buildable AND
whether a rasterising router can ever propose it, and those are two different
thresholds:

    margin <  0   the land cannot launch at this width.  KiCad would refuse it
                  and so should anything else.  D-620: `NFC_RF`'s netclass
                  width is 0.400 mm and `U9.15` is a 0.300 mm land with 0.200 mm
                  of gap on each side, so the class was never launchable from
                  the part it serves at its own netclass width.
    margin == 0   EXACTLY legal.  KiCad's DRC passes it -- the promoted
                  `NFC_RFO1` / `NFC_RFO2` arms are this case, at 0.300 mm --
                  but `maze3d` rasterises with a 0.75-cell guard band on top of
                  the clearance, so at ANY lattice pitch the required figure
                  strictly exceeds the available one and the maze can never
                  propose it.  A zero-margin land is routable ONLY by a
                  primitive that works in exact geometry (`route_local_two_pad`).
    margin >  0   ordinary; the guard band is affordable when margin > 0.75*G.

So this screen answers, before any router runs, three questions a router can
only answer expensively and one it cannot answer at all:

    WIDEST      the widest track this land can launch, per direction
    MARGIN      the slack at the width the net actually asks for
    LATTICE     the coarsest maze lattice whose guard band still fits, or
                NONE when the margin is zero and no lattice ever will

WHAT IT MEASURES, AND WHAT IT DOES NOT.  The obstacles here are PADS -- the
land pattern's own arithmetic, which is a property of the PACKAGE and does not
change when copper moves.  Routed tracks and vias around the land are the
router's business and are deliberately not counted, so a `CLEAR` verdict says
"this package can launch this width", not "this net will route today".  The two
questions are different and conflating them is what made every one of these
refusals look like a search failure.

Read-only.  It loads the board, reads each net's contract from
`route_maze_batch.net_contract` -- the same table the authority routes with, so
this can never measure a rule the router does not use -- and prints JSON.

    python3 screen_land_escape_margin.py NET [NET ...] [--pad REF.NUM] -o OUT
"""

import argparse
import json
import math
from pathlib import Path

import pcbnew

from route_maze_batch import BOARD, net_contract

NM = 1e6
# How far out of the land the strip is followed, BEYOND the package.  A launch
# is blocked by the lands it must walk past on the way OUT; once it is clear of
# its own footprint it is free to turn, and a longer strip would report a
# neighbouring part two millimetres away as if it were a package wall.  The
# reach is therefore measured per pad and per direction -- far enough to clear
# the footprint's own outermost land in that direction -- plus this margin.
REACH_MM = 0.25
# Candidate centreline positions are scanned at one micron across the land, so a
# reported optimum is exact to the micron rather than to a lattice.
STEP_NM = 1000
DIRS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}


def rect(pad):
    b = pad.GetBoundingBox()
    return (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom())


def rect_dist(a, b):
    """Exact distance between two axis-aligned rectangles, zero if they touch."""
    dx = max(0, b[0] - a[2], a[0] - b[2])
    dy = max(0, b[1] - a[3], a[1] - b[3])
    return math.hypot(dx, dy)


def package_reach(own, r, dkey):
    """How far this land must travel to be CLEAR OF ITS OWN PACKAGE, plus REACH."""
    dx, dy = DIRS[dkey]
    out = 0
    for o in own:
        if dx > 0:
            out = max(out, o[2] - r[2])
        elif dx < 0:
            out = max(out, r[0] - o[0])
        elif dy > 0:
            out = max(out, o[3] - r[3])
        else:
            out = max(out, r[1] - o[1])
    return max(0, out) + int(REACH_MM * NM)


def strip(r, dkey, centre, width, reach):
    """The half-strip a track of `width` occupies leaving land `r` toward `dkey`."""
    dx, dy = DIRS[dkey]
    h = width // 2
    if dx:
        y0, y1 = centre - h, centre + h
        x0 = r[2] if dx > 0 else r[0] - reach
        x1 = r[2] + reach if dx > 0 else r[0]
    else:
        x0, x1 = centre - h, centre + h
        y0 = r[3] if dy > 0 else r[1] - reach
        y1 = r[3] + reach if dy > 0 else r[1]
    return (x0, y0, x1, y1)


def centres(r, dkey, width):
    """Every centreline that still STARTS ON THE LAND, at one micron."""
    lo, hi = (r[1], r[3]) if DIRS[dkey][0] else (r[0], r[2])
    return range(lo, hi + 1, STEP_NM)


def neighbours(board, pad, net):
    """Foreign pads within reach on a layer this pad shares.

    A pad on the SAME net is not an obstacle -- running onto it is a connection,
    which is why `U4.2` and `U4.3` do not block each other and `U9.14` and
    `U9.16` do.
    """
    r = rect(pad)
    win = int((REACH_MM + 2.0) * NM)
    box = (r[0] - win, r[1] - win, r[2] + win, r[3] + win)
    out = []
    for fp in board.GetFootprints():
        for other in fp.Pads():
            if other.GetNetname() == net:
                continue
            if not any(other.IsOnLayer(ly) for ly in pad.GetLayerSet().CuStack()):
                continue
            o = rect(other)
            if rect_dist(box, o) > 0:
                continue
            out.append(("%s.%s" % (fp.GetReference(), other.GetNumber()), o))
    return out


def measure(r, dkey, width, clr, nbrs, reach):
    """Best (margin, centre, binding pad) for one land, direction and width."""
    best = None
    for c in centres(r, dkey, width):
        s = strip(r, dkey, c, width, reach)
        worst, who = None, None
        for name, o in nbrs:
            d = rect_dist(s, o) - clr
            if worst is None or d < worst:
                worst, who = d, name
        if worst is None:
            worst, who = float("inf"), None
        if best is None or worst > best[0]:
            best = (worst, c, who)
    return best


def widest(r, dkey, clr, nbrs, floor_nm, reach, ceil_nm=1000000):
    """The widest track this land can launch toward `dkey`, to five microns."""
    found = None
    w = floor_nm
    while w <= ceil_nm:
        if measure(r, dkey, w, clr, nbrs, reach)[0] < 0:
            break
        found = w
        w += 5000
    return found


def screen(board_path, nets, only_pads):
    board = pcbnew.LoadBoard(str(Path(board_path).resolve()))
    rows = []
    for net in nets:
        con = net_contract(board, net)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() != net:
                    continue
                ref = "%s.%s" % (fp.GetReference(), pad.GetNumber())
                if only_pads and ref not in only_pads:
                    continue
                r = rect(pad)
                nbrs = neighbours(board, pad, net)
                own = [rect(q) for q in fp.Pads()]
                dirs = {}
                for dkey in DIRS:
                    reach = package_reach(own, r, dkey)
                    margin, centre, who = measure(
                        r, dkey, con["width"], con["clr_pad"], nbrs, reach)
                    wide = widest(r, dkey, con["clr_pad"], nbrs,
                                  board.GetDesignSettings().m_TrackMinWidth,
                                  reach)
                    dirs[dkey] = dict(
                        reach_mm=round(reach / NM, 4),
                        margin_mm=round(margin / NM, 6),
                        centre_mm=round(centre / NM, 6),
                        binding_pad=who,
                        widest_mm=(None if wide is None else round(wide / NM, 4)),
                        # 0.75 cells of guard is what `maze3d.dru_overlay` and
                        # `qrouter.QBoard.grid` both add, so this is the coarsest
                        # lattice that still fits -- and NONE when it never will.
                        max_lattice_mm=(None if margin <= 0
                                        else round(margin / 0.75 / NM, 4)),
                    )
                best = max(dirs.values(), key=lambda d: d["margin_mm"])
                rows.append(dict(
                    pad=ref, net=net, netclass=con["netclass"],
                    width_mm=round(con["width"] / NM, 4),
                    clr_pad_mm=round(con["clr_pad"] / NM, 4),
                    land_mm=[round(v / NM, 4) for v in r],
                    directions=dirs,
                    best_margin_mm=best["margin_mm"],
                    verdict=("UNLAUNCHABLE" if best["margin_mm"] < 0 else
                             "EXACT" if best["margin_mm"] == 0 else "CLEAR"),
                ))
    return dict(schema=1, board=str(board_path), reach_mm=REACH_MM,
                step_nm=STEP_NM, pads=rows,
                summary=dict(
                    pads=len(rows),
                    unlaunchable=sum(1 for r in rows if r["verdict"] == "UNLAUNCHABLE"),
                    exact=sum(1 for r in rows if r["verdict"] == "EXACT"),
                    clear=sum(1 for r in rows if r["verdict"] == "CLEAR")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", default=BOARD)
    ap.add_argument("--pad", action="append", default=[],
                    help="restrict to these REF.NUM lands; repeatable")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    doc = screen(a.board, a.nets, set(a.pad))
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
