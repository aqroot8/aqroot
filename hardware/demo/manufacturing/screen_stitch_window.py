#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: is the 8.0 mm stitch window actually the wall?

D-630 measured that both pour-owning nets, given EVERY standing primitive at
once, refuse FIRST with

    NO_BODY_VIA_SITE: no legal 0.65 mm barrel INSIDE THIS NET'S OWN BODY POUR
                      within 8.0 mm of any escape

on six of `/01_POWER_TREE/BQ25185_SYS`'s islands and two of `+3V3`'s, and it
named the 8.0 mm as "a convention `stitch_pad` chose, not a figure this board
publishes anywhere" -- the pour block's binding constraint and the only one of
the board's three remaining blocks bounded by a convention rather than by a
rule or a geometry.

THAT SENTENCE NAMES THREE CONJUNCTS AND BLAMES ONE OF THEM.

`stitch_pad`'s landing test is `via_ok & land_ok` reached within `R` cells of
an escape.  A refusal can therefore mean any of

  WINDOW      a legal body site EXISTS and is further than 8.0 mm away
              -- the convention is the wall, and widening it closes the island
  UNREACHABLE no legal body site is reachable from ANY escape at any distance
              -- free space does not connect the two; a wider window buys
              nothing and the convention was never the wall
  BARREN      the net's BODY POUR owns no via-legal cell at all
              -- there is nothing to walk to; this is a POUR problem
  NO_ESCAPE   the land cannot launch, so no window applies

Widening a locality bound is cheap; widening it against `UNREACHABLE` or
`BARREN` is a fiction that would cost a gate run to discover.  So this screen
MEASURES the distance instead of assuming it: for every orphan island of every
pour-owning net it runs the SAME unbounded wavefront `stitch_pad` runs bounded,
over the SAME `Field`, from the SAME escapes, and reports the distance in
millimetres to

  * the nearest via-legal cell INSIDE THE BODY POUR   (`body_mm`)
  * the nearest via-legal cell of any kind            (`any_mm`)

`None` means "not reachable through free space at ANY distance", which is a
different fact from "far".

CORROBORATION.  Every island is then offered the promoter's own
`maze3d.stitch_pad` at a ladder of windows, `land_ok` ON, every trial reverted.
The measured distance predicts the rung at which the real primitive flips, or
the two instruments disagree and that is itself the finding.

WHAT IS MEASURED, NOT ASSUMED

  * THE CONTRACT IS THE GATE'S.  `net_contract` + `permitted_layers` +
    `reserved_inner_planes` + `DRU_CLASS` floors + `--escape-floor` +
    `--guard`, exactly as `route_maze_batch.propose` assembles them, so the
    `Field`, the escapes and the landing mask are the ones a promotion sees.
  * THE BODY MASK IS `maze3d.body_landing`, reused unchanged.
  * THE WAVEFRONT IS `stitch_pad`'s.  `_shift_or(cur, free) & free`, 8-connected,
    same `free`, same `via_ok`, same forced-free escape cell -- with the box and
    the `R` bound removed and nothing else changed.
  * NOTHING IS WRITTEN.  Every `stitch_pad` trial is reverted; the full-board
    gate remains the only thing that promotes copper.
"""

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# The ladder of locality windows offered to the real `stitch_pad`.  8.0 mm is
# the standing convention and is included so the run carries its own control.
WINDOWS = (8.0, 12.0, 16.0, 24.0, 32.0, 48.0)


def free_pocket(mz, np, field, e):
    """The whole free region of `e`'s own layer reachable from `e`.

    Returns (cells, mask).  This is the number that makes `UNREACHABLE`
    falsifiable: a land whose escape opens into 152 free cells is SEALED, and
    one that opens into 176,085 is not, and only the second kind can be a
    distance problem.  Reported as an AREA in mm2 by the caller so it is
    comparable across pitches -- a seal that is real keeps its area as the
    lattice refines, and a seal that was a rasterisation artifact does not.
    """
    L = e['layer']
    if L not in field.blk:
        return 0, None
    free = (~field.blk[L]).copy()
    si, sj = e['i'], e['j']
    if not (0 <= si < field.nx and 0 <= sj < field.ny):
        return 0, None
    free[sj, si] = True
    cur = np.zeros(free.shape, dtype=bool)
    cur[sj, si] = True
    seen = cur.copy()
    while True:
        nxt = mz._shift_or(cur, free) & free & ~seen
        if not nxt.any():
            return int(seen.sum()), seen
        seen |= nxt
        cur = nxt


def unbounded_reach(mz, np, field, e, want):
    """Cell distance from escape `e` to the nearest True cell of `want`.

    This is `stitch_pad`'s wavefront with the window removed: same 8-connected
    `_shift_or` dilation, same `free = ~blk[L]`, same forced-free start cell,
    no `R` bound and no `[j0:j1, i0:i1]` box.  Returns (cells, (i, j)) or
    (None, None) when no such cell is reachable through free space at all.
    """
    L = e['layer']
    if L not in field.blk:
        return None, None
    free = ~field.blk[L]
    si, sj = e['i'], e['j']
    if not (0 <= si < field.nx and 0 <= sj < field.ny):
        return None, None
    free = free.copy()
    free[sj, si] = True
    if want[sj, si]:
        return 0, (si, sj)
    cur = np.zeros(free.shape, dtype=bool)
    cur[sj, si] = True
    seen = cur.copy()
    d = 0
    while True:
        d += 1
        nxt = mz._shift_or(cur, free) & free & ~seen
        if not nxt.any():
            return None, None
        hit = nxt & want
        if hit.any():
            js, iss = np.nonzero(hit)
            return d, (int(iss[0]), int(js[0]))
        seen |= nxt
        cur = nxt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*", default=None,
                    help="pour-owning nets; default = every net that owns a "
                         "filled pour and has an orphan island")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec to honour")
    ap.add_argument("--escape-floor", action="store_true",
                    help="hand the escape ladder the .kicad_dru published "
                         "minimum, as route_maze_batch --escape-floor does")
    ap.add_argument("--stitch-via", default=None, metavar="DIA:DRILL",
                    help="barrel the stitch may use, clamped up to the floors")
    ap.add_argument("--escape-limit", type=int, default=12)
    ap.add_argument("--window", type=float, action="append", default=None,
                    metavar="MM", help="windows to offer stitch_pad; repeatable")
    ap.add_argument("--no-ladder", action="store_true",
                    help="measure only; skip the stitch_pad corroboration")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import numpy as np
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN)

    windows = tuple(sorted(set(a.window or WINDOWS)))
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    stitch_via = (tuple(int(v) for v in a.stitch_via.split(":"))
                  if a.stitch_via else None)

    nets = list(a.nets)
    if not nets:
        nets = sorted(n for n in {t.GetNetname() for t in qb.b.GetTracks()}
                      | {p.GetNetname() for f in qb.b.GetFootprints()
                         for p in f.Pads()}
                      if n and mz.has_plane(qb, n))

    out = []
    for net in nets:
        if not mz.has_plane(qb, net):
            out.append(dict(net=net, ok=False, reason="NO_PLANE"))
            continue
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        over = DRU_CLASS.get(c["netclass"], {})
        via_dia, via_drill = c["via_dia"], c["via_drill"]
        if stitch_via:
            via_drill = max(stitch_via[1], over.get("drill", 0))
            via_dia = max(stitch_via[0], via_drill + 2 * ANNULAR_MIN)
        floor = over.get("width") if a.escape_floor else None
        field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                         via_dia, via_drill, G=a.grid, layers=layers,
                         neck=mz.neck_rule(qb),
                         guard=guard_for(spec, net) if spec else None,
                         escape_floor=floor)
        land_ok, land_info = mz.body_landing(qb, net, field)
        body_sites = int((land_ok & field.via_ok).sum())
        any_sites = int(field.via_ok.sum())
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        body = max(islands, key=len)
        orphans = [i for i in islands if i is not body]
        rec = dict(net=net, netclass=c["netclass"],
                   contract=dict(width=c["width"], via_dia=via_dia,
                                 via_drill=via_drill,
                                 escape_floor=field.escape_floor,
                                 layers=list(layers)),
                   body_landing=land_info,
                   body_via_sites=body_sites, any_via_sites=any_sites,
                   orphan_islands=len(orphans), islands=[])
        for island in orphans:
            refs = [p['ref'] for p in island]
            t0 = time.time()
            best_body, best_any, why, escapes_n = None, None, None, 0
            for pad in island:
                es = mz.pad_escapes(qb, field, pad, None, a.escape_limit)
                if not es:
                    if why is None:
                        why = (qb.escape_why or ['no legal escape'])[0]
                    continue
                escapes_n += len(es)
                for e in es:
                    db, sb = unbounded_reach(mz, np, field,
                                             e, land_ok & field.via_ok)
                    if db is not None and (best_body is None
                                           or db < best_body[0]):
                        best_body = (db, pad['ref'], e['layer'], sb)
                    da, sa = unbounded_reach(mz, np, field, e, field.via_ok)
                    if da is not None and (best_any is None
                                           or da < best_any[0]):
                        best_any = (da, pad['ref'], e['layer'], sa)
            mm = a.grid / 1e6
            if escapes_n == 0:
                verdict = "NO_ESCAPE"
            elif body_sites == 0:
                verdict = "BARREN"
            elif best_body is None:
                verdict = "UNREACHABLE"
            elif best_body[0] * mm <= windows[0]:
                verdict = "INSIDE_STANDING_WINDOW"
            else:
                verdict = "WINDOW"

            def site(b):
                if b is None:
                    return None
                d, ref, L, (i, j) = b
                return dict(mm=round(d * mm, 3), from_pad=ref, layer=L,
                            xy=[round((field.ox + i * field.G) / 1e6, 4),
                                round((field.oy + j * field.G) / 1e6, 4)])

            isl = dict(island=refs, verdict=verdict, escapes=escapes_n,
                       body=site(best_body), any=site(best_any),
                       why=(str(why)[:160] if why else None),
                       measure_s=round(time.time() - t0, 1))
            if not a.no_ladder:
                rungs = []
                for w in windows:
                    m = qb.mark()
                    hit, last = None, None
                    for pad in island:
                        r = mz.stitch_pad(qb, field, pad, max_mm=w,
                                          escape_limit=a.escape_limit,
                                          land_ok=land_ok)
                        last = r
                        if r.get("ok"):
                            hit = r
                            break
                    qb.revert(m)
                    rungs.append(dict(
                        window_mm=w, ok=bool(hit),
                        pad=(hit or last or {}).get("pad"),
                        mm=(hit or {}).get("mm"),
                        via_xy=list(hit["via_xy"]) if hit else None,
                        reason=None if hit else (last or {}).get("reason")))
                    if hit:
                        break
                isl["ladder"] = rungs
                isl["closes_at_mm"] = next((r["window_mm"] for r in rungs
                                            if r["ok"]), None)
            rec["islands"].append(isl)
            print("  %-28s %-22s %-22s body=%s any=%s closes=%s"
                  % (net[-28:], ",".join(refs)[:22], verdict,
                     (isl["body"] or {}).get("mm"),
                     (isl["any"] or {}).get("mm"),
                     isl.get("closes_at_mm")),
                  file=sys.stderr, flush=True)
        out.append(rec)

    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha, grid=a.grid,
        windows=list(windows), escape_floor=bool(a.escape_floor),
        stitch_via=list(stitch_via) if stitch_via else None,
        guard=str(a.guard) if a.guard else None,
        guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                      if a.guard else None),
        question=("for every island NO_BODY_VIA_SITE refuses, HOW FAR is the "
                  "nearest via-legal cell inside the net's own body pour -- is "
                  "the 8.0 mm locality window the wall, or is free space simply "
                  "not connecting the escape to the pour at any distance"),
        method=("read-only; stitch_pad's own 8-connected wavefront over the "
                "same Field, same escapes, same via_ok & body_landing mask, "
                "with the window removed; corroborated by the real "
                "maze3d.stitch_pad at a ladder of windows, every trial reverted"),
        nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
