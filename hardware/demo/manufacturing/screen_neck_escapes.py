#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: is the pad-escape wall a WIDTH wall?

Every whole-board maze failure since D-578 is one of two reasons, and the
larger half is `NO_LEGAL_ESCAPE`: a pad from which no legal stub of the net's
own netclass width leaves the pad at all.  `maze3d` routes ONE width per net,
board-wide, taken from the netclass and raised by the `.kicad_dru` class floor.

The `.kicad_dru` precedence tail, however, carries

    (rule "Pad-escape necking - width, fine-pitch power packages"
        (constraint track_width (min 0.20mm))
        (condition "A.intersectsCourtyard('U11') || ... || A.intersectsCourtyard('U9')"))

which is the LAST matching rule and therefore WINS: inside those ten
courtyards the board's own rules already permit a 0.20 mm neck, whatever the
netclass says.  The router has never used it.

This script spends no copper and writes no board.  For each pad that owns an
open edge it asks `maze3d.pad_escapes` -- the SAME primitive the router uses --
at the contract width and at each candidate neck width, and reports where a
narrower stub would open a launch that the contract width cannot.  If the
answer is "nowhere", necking is not the lever and the wall is geometry, not
width; that is a useful answer too and it is recorded rather than assumed.
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# The ten courtyards the .kicad_dru width-necking rule names, verbatim.
NECK_REFS = ("U11", "U12", "U13", "U14", "U16", "U17", "U20", "U21", "U22", "U9")
NECK_MIN = 200000            # (constraint track_width (min 0.20mm))


def courtyards(board):
    """Courtyard polygons of the ten necking-rule footprints, as pcbnew SHAPE."""
    out = {}
    for f in board.GetFootprints():
        ref = f.GetReference()
        if ref in NECK_REFS:
            poly = f.GetCourtyard(f.GetLayer())
            out[ref] = poly
    return out


def in_courtyard(cy, x, y):
    """Which necking courtyards contain this point."""
    import pcbnew
    hits = []
    for ref, poly in cy.items():
        if poly.OutlineCount() and poly.Collide(pcbnew.VECTOR2I(int(x), int(y))):
            hits.append(ref)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*")
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--widths", default="250000,200000")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()

    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import net_contract

    widths = [int(w) for w in a.widths.split(",")]
    qb = qr.QBoard(str(BOARD))
    ir.inject_existing_via_obstacles(qb)
    cy = courtyards(qb.b)

    # The open pads: every physical pad of an open net that is not already in
    # the net's largest connected island.  Those are exactly the terminals a
    # further route has to launch from.
    report = []
    for net in a.nets:
        c = net_contract(qb.b, net)
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            report.append(dict(net=net, note="already connected"))
            continue
        main = max(islands, key=len)
        pads = [p for g in islands if g is not main for p in g]
        t0 = time.time()
        base = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                        c["via_dia"], c["via_drill"], G=a.grid,
                        layers=c["layers"])
        rows = []
        for p in pads:
            e0 = mz.pad_escapes(qb, base, p, None, 12)
            row = dict(pad=p["ref"], x=round(p["x"] / 1e6, 3),
                       y=round(p["y"] / 1e6, 3),
                       courtyards=in_courtyard(cy, p["x"], p["y"]),
                       escapes={str(c["width"]): len(e0)})
            rows.append(row)
        for w in widths:
            if w >= c["width"]:
                continue
            f = mz.Field(qb, net, w, c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=a.grid,
                         layers=c["layers"])
            for p, row in zip(pads, rows):
                row["escapes"][str(w)] = len(mz.pad_escapes(qb, f, p, None, 12))
        gained = [r for r in rows
                  if r["escapes"][str(c["width"])] == 0
                  and any(v > 0 for k, v in r["escapes"].items()
                          if k != str(c["width"]))]
        report.append(dict(net=net, netclass=c["netclass"], width=c["width"],
                           islands=len(islands), pads=len(pads),
                           seconds=round(time.time() - t0, 1),
                           unlocked_by_neck=[r["pad"] for r in gained],
                           rows=rows))
        print("  %-44s %d/%d pads unlocked by a neck  %.0fs"
              % (net, len(gained), len(pads), time.time() - t0),
              file=sys.stderr, flush=True)

    out = dict(schema=1, board=str(BOARD), grid=a.grid,
               neck_refs=list(NECK_REFS), neck_min=NECK_MIN,
               widths_tried=widths, nets=report)
    text = json.dumps(out, indent=1, default=str)
    if a.out:
        Path(a.out).write_text(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
