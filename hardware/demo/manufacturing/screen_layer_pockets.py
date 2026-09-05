#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: how is each routable layer PARTITIONED at a given
track width, and how big are the pieces?

THE QUESTION THIS ANSWERS, AND WHY IT HAD NEVER BEEN ASKED.  The six-layer
stack-up records `In2.Cu` as a SIGNAL layer, and every capacity argument on
this board has read that as spare lane.  It is not spare in the way the
stack-up suggests, and the reason is a fact no per-net measurement can see: a
THROUGH barrel is copper on EVERY layer, so the inner layers carry the board's
ENTIRE via field whether or not anything of theirs uses it.  This board has
**790 through vias**.  On `In2.Cu` they are almost the only obstacles there
are -- 316 track segments against 790 barrels and forty-odd through-hole
lands -- and what they do is not consume area, it is CUT the layer up.

So the measurement is not "how much of the layer is free" -- that number is
large and misleading.  It is "how many PIECES is the free area in, and how big
is each", because a haul can only use the piece both of its ends land in.
This is the layer-scale form of the pocket that D-630's `LATTICE_EXACT` and
D-633's off-centre launch found at pad scale, and it is measured the same way:
`QBoard.grid` at the width and clearances a real net would use, then connected
components of the free cells.

WHAT A NUMBER MEANS.  `free_mm2` is the free AREA at this width; `pieces` is
how many connected components it falls into at this lattice; `largest_mm2` and
`largest_share` say how much of the free area the biggest piece holds.  A layer
whose free area is mostly ONE piece is a lane; a layer whose free area is in
hundreds of pieces is a minefield, and the difference decides whether a hop is
worth proposing before it is searched.

The lattice is coarser than the router's, and deliberately: a coarser guard
band OVERSTATES the partitioning, so a layer this reports as one piece really
is one piece.  Read `pieces` as an upper bound and `largest_share` as a lower
bound.

    python3 screen_layer_pockets.py [--board B] [--net NET] [--width NM]
        [--grid NM] [--layers F,B,I2,I3] [-o OUT]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def components(free):
    """Sizes of the 8-connected components of a boolean mask, descending.

    Iterative label propagation on the numpy array itself -- no scipy, and no
    per-cell Python loop over a multi-million-cell board.
    """
    lab = np.where(free, np.arange(free.size).reshape(free.shape) + 1, 0)
    while True:
        prev = lab
        m = lab.copy()
        for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
            m = np.maximum(m, np.roll(lab, sh, axis=ax))
        for dy in (1, -1):
            for dx in (1, -1):
                m = np.maximum(m, np.roll(np.roll(lab, dy, axis=0), dx,
                                          axis=1))
        lab = np.where(free, m, 0)
        if np.array_equal(lab, prev):
            break
    ids, counts = np.unique(lab[lab > 0], return_counts=True)
    return sorted(counts.tolist(), reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--net", default="/I2C_SCL_INT",
                    help="the net whose OWN copper is exempt; any net with no "
                         "copper on the inner layers gives the same answer "
                         "there, and the point of naming one is that a layer "
                         "is only ever partitioned FOR somebody")
    ap.add_argument("--width", type=int, default=200000)
    ap.add_argument("--clearance", type=int, default=200000)
    ap.add_argument("--grid", type=int, default=150000)
    ap.add_argument("--layers", default="")
    ap.add_argument("--top", type=int, default=12,
                    help="how many piece sizes to record per layer")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir

    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    layers = ([x for x in a.layers.split(",") if x] if a.layers
              else list(qb.routable))
    vias = sum(1 for s in qb.obstacles("I2", "\x00none") if s.tag == "via")

    rows = []
    for L in layers:
        blk = qb.grid(L, a.net, a.width, a.clearance, a.clearance,
                      qb.ex0, qb.ey0, qb.ex1, qb.ey1, a.grid)
        free = ~blk
        cell = (a.grid / 1e6) ** 2
        sizes = components(free)
        tot = float(sum(sizes))
        rec = dict(layer=L, cells=int(free.size),
                   free_cells=int(free.sum()),
                   free_mm2=round(float(free.sum()) * cell, 2),
                   pieces=len(sizes),
                   largest_mm2=round(sizes[0] * cell, 2) if sizes else 0.0,
                   largest_share=round(sizes[0] / tot, 4) if sizes else 0.0,
                   piece_mm2=[round(s * cell, 2) for s in sizes[:a.top]],
                   pieces_over_1mm2=sum(1 for s in sizes if s * cell >= 1.0),
                   obstacles=len(qb.obstacles(L, a.net)))
        rows.append(rec)
        print(" %-3s free %8.1f mm2 in %5d pieces; largest %8.1f mm2 "
              "(%.1f%% of free); %d obstacles"
              % (L, rec["free_mm2"], rec["pieces"], rec["largest_mm2"],
                 100.0 * rec["largest_share"], rec["obstacles"]),
              file=sys.stderr, flush=True)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(schema=1, board=str(a.board), board_sha256=sha,
               authoritative_unchanged=(sha == after),
               net=a.net, width=a.width, clearance=a.clearance, grid=a.grid,
               through_vias=vias,
               question=("how many PIECES is each routable layer's free area "
                         "in at this width, and how big is the largest -- the "
                         "layer-scale form of the pocket the pad-scale "
                         "instruments keep finding"),
               method=("read-only; QBoard.grid at the given width and "
                       "clearance, then 8-connected components of the free "
                       "cells.  The lattice is COARSER than the router's, so "
                       "`pieces` is an upper bound and `largest_share` a "
                       "lower bound; zones are invisible to QBoard, so a "
                       "filled pour neither blocks nor opens anything here"),
               layers=rows)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
