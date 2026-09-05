#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: the ORPHAN-PAIR census, and the ladder under it.

D-631.  `screen_partial_pairs.py` runs the pair census that comes before the
ladder, and it EXCLUDES a pour-served net by the board's own zones -- correctly,
because `--partial` is not the instrument that completes such a net.  But the
instrument that IS -- `maze3d.join_orphans` -- carries its own bound,
`route_maze_batch.JOIN_ORPHAN_MAX_MM = 4.0`, and the bound is applied to the
PAIR GAP with a bare `continue`:

    if max_mm and gap > max_mm * qr.MM:
        continue

A pair beyond it is not asked, not refused and NOT REPORTED.  So a pour-served
net has had NO pair census of any kind, and its orphan-join report has been
reading "joined 0, 2 failures" where the real sentence was "2 asked, 34
declined without a word".

`/01_POWER_TREE/BQ25185_SYS` is the case that named it.  Nine orphan clusters,
36 pairs, and the 4.0 mm bound asked exactly TWO -- both of which had a
zero-escape island on one end, so the net's **fifteen pairs with legal escapes
at BOTH ends had never been asked at all**, the nearest of them 0.574 mm beyond
the convention.

THE CENSUS IS THE WORK-LIST; THE LADDER IS THE ANSWER.  D-625 (`BTN_DOWN_N`
0.0333 mm), D-626/D-630 (`EXT_SDA` 0.025 mm) and D-628 (`LED_K` 0.020 mm) all
closed edges that read `NO_PATH` at the 0.100 mm default, so a `NO_PATH` here
is a PITCH question until a ladder says otherwise.  This screen runs both: the
full pairwise census with an escape count on each end, then the SAME
`maze3d.route_join` `join_orphans` calls, pair by pair, over a descending pitch
ladder, every trial reverted.

WHAT IS MEASURED, NOT ASSUMED

  * THE CONTRACT IS THE GATE'S.  `net_contract` + `permitted_layers` +
    `reserved_inner_planes` + `DRU_CLASS` floors + `--escape-floor` +
    `--guard`, exactly as `route_maze_batch.propose` assembles them.
  * THE EMITTER IS `join_orphans`'s.  `route_join(qb, field, A,
    nearest_pads(A, B, near))` at the same `escape_limit` and `via_cost_mm`.
  * EACH PAIR IS INDEPENDENT AND REVERTED, so the census is comparable across
    rungs rather than order-dependent.  The promoter's own `join_orphans` is
    greedy-with-union-find and DOES lay copper as it goes; this screen
    deliberately does not, so a pair that closes here is a lower bound on what
    the driver can do, never an upper one.
  * BUDGETS ARE STATED AND ENFORCED.  Cells per rung against `--cells`, and
    seconds per rung against `--seconds`; a rung skipped for budget is
    RECORDED as `OVER_BUDGET`, never silently dropped.
  * NOTHING IS WRITTEN.  The full-board gate remains the only thing that
    promotes copper.
"""

import argparse
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# The D-623/D-626 pitch ladder, in nm.  0.100 mm is every previous run's
# default and is included so the sweep carries its own control.
PITCHES = (100000, 66667, 50000, 33333, 25000, 20000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+", help="pour-owning nets to census")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec to honour")
    ap.add_argument("--escape-floor", action="store_true")
    ap.add_argument("--neck", action="store_true")
    ap.add_argument("--stitch-via", default=None, metavar="DIA:DRILL")
    ap.add_argument("--escape-limit", type=int, default=8)
    ap.add_argument("--near", type=int, default=8)
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--pitch", type=int, action="append", default=None,
                    metavar="NM", help="pitches to ladder; repeatable")
    ap.add_argument("--max-gap-mm", type=float, default=0.0,
                    help="only ladder pairs closer than this (0 = all)")
    ap.add_argument("--cells", type=int, default=300_000_000,
                    help="memory ceiling per rung, in Field cells")
    ap.add_argument("--seconds", type=int, default=2400,
                    help="wall-clock ceiling for ONE rung, all pairs")
    ap.add_argument("--census-only", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN)

    pitches = tuple(sorted(set(a.pitch or PITCHES), reverse=True))
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    stitch_via = (tuple(int(v) for v in a.stitch_via.split(":"))
                  if a.stitch_via else None)
    neck = mz.neck_rule(qb) if a.neck else None

    out = []
    for net in a.nets:
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

        def build(G):
            return mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                            via_dia, via_drill, G=G, layers=layers, neck=neck,
                            guard=guard_for(spec, net) if spec else None,
                            escape_floor=floor)

        # Island identity is KiCad connectivity, not the lattice, so the
        # clusters and their gaps are the same at every rung and are measured
        # once.  Only the ESCAPE COUNTS depend on the pitch; they are reported
        # at the coarsest rung, which is the one every previous run used.
        islands = mz.net_islands(qb, net)
        if len(islands) < 3:
            out.append(dict(net=net, ok=False, reason="NOTHING_TO_JOIN",
                            islands=len(islands)))
            continue
        body = max(islands, key=len)
        orph = [i for i in islands if i is not body]
        names = [[p["ref"] for p in i] for i in orph]
        f0 = build(pitches[0])
        esc = []
        for isl in orph:
            n, why = 0, None
            for pad in isl:
                e = mz.pad_escapes(qb, f0, pad, None, a.escape_limit)
                n += len(e)
                if not e and why is None:
                    why = (qb.escape_why or ["no legal escape"])[0]
            esc.append(dict(escapes=n, why=str(why)[:160] if why else None))
        census = []
        for x, y in itertools.combinations(range(len(orph)), 2):
            census.append(dict(
                a=names[x], b=names[y], ia=x, ib=y,
                gap_mm=round(mz._pad_gap(orph[x], orph[y]) / 1e6, 3),
                escapes=[esc[x]["escapes"], esc[y]["escapes"]],
                both_escape=bool(esc[x]["escapes"] and esc[y]["escapes"])))
        census.sort(key=lambda r: r["gap_mm"])
        rec = dict(net=net, netclass=c["netclass"],
                   contract=dict(width=c["width"], via_dia=via_dia,
                                 via_drill=via_drill, layers=list(layers),
                                 escape_floor=f0.escape_floor),
                   body=[p["ref"] for p in body], orphan_islands=len(orph),
                   clusters=[dict(pads=names[i], **esc[i])
                             for i in range(len(orph))],
                   pairs_total=len(census),
                   pairs_both_escape=sum(1 for r in census
                                         if r["both_escape"]),
                   census=census, rungs=[])
        if a.census_only:
            out.append(rec)
            continue

        work = [r for r in census if r["both_escape"]
                and (not a.max_gap_mm or r["gap_mm"] <= a.max_gap_mm)]
        closed = {}
        for G in pitches:
            cells = 0
            t0 = time.time()
            field = None
            rows = []
            for r in work:
                key = (r["ia"], r["ib"])
                if key in closed:
                    continue
                if field is None:
                    field = build(G)
                    cells = int(field.nx) * int(field.ny) * len(field.blk)
                    if cells > a.cells:
                        rec["rungs"].append(dict(grid_nm=G, cells=cells,
                                                 reason="OVER_BUDGET",
                                                 budget_cells=a.cells,
                                                 pairs=[]))
                        field = "over"
                        break
                if time.time() - t0 > a.seconds:
                    rows.append(dict(a=r["a"], b=r["b"], gap_mm=r["gap_mm"],
                                     ok=False, reason="OVER_BUDGET"))
                    continue
                m = qb.mark()
                ts = time.time()
                j = mz.route_join(qb, field, orph[r["ia"]],
                                  mz.nearest_pads(orph[r["ia"]], orph[r["ib"]],
                                                  a.near),
                                  escape_limit=a.escape_limit,
                                  via_cost_mm=a.via_cost)
                qb.revert(m)
                row = dict(a=r["a"], b=r["b"], gap_mm=r["gap_mm"],
                           ok=bool(j.get("ok")),
                           mm=(round(j["mm"], 4) if j.get("mm") else None),
                           vias=j.get("vias"),
                           reason=(None if j.get("ok")
                                   else str(j.get("reason"))),
                           why=(None if j.get("ok")
                                else str(j.get("why"))[:160]),
                           seconds=round(time.time() - ts, 1))
                rows.append(row)
                if row["ok"]:
                    closed[key] = dict(grid_nm=G, **row)
                print("  %-24s %8.3f %-26s <-> %-26s %s %s"
                      % ("%.4f mm" % (G / 1e6), r["gap_mm"],
                         ",".join(r["a"])[:26], ",".join(r["b"])[:26],
                         "OK  %.3f mm / %s via" % (row["mm"], row["vias"])
                         if row["ok"] else "NO  " + (row["reason"] or ""),
                         "%.0fs" % row["seconds"]),
                      file=sys.stderr, flush=True)
            if field == "over":
                continue
            rec["rungs"].append(dict(grid_nm=G, cells=cells,
                                     seconds=round(time.time() - t0, 1),
                                     pairs=rows))
            del field
            if len(closed) == len(work):
                break
        rec["closed"] = [dict(a=names[k[0]], b=names[k[1]], **v)
                         for k, v in closed.items()]
        rec["closed_n"] = len(closed)
        out.append(rec)

    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        pitches=list(pitches), escape_floor=bool(a.escape_floor),
        neck=bool(a.neck),
        stitch_via=list(stitch_via) if stitch_via else None,
        guard=str(a.guard) if a.guard else None,
        guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                      if a.guard else None),
        budgets=dict(cells=a.cells, seconds=a.seconds,
                     max_gap_mm=a.max_gap_mm),
        question=("which ORPHAN-ISLAND PAIRS of a pour-served net has "
                  "join_orphans' 4.0 mm gap bound never asked, and does the "
                  "D-623 pitch ladder close any of them"),
        method=("read-only; the same maze3d.route_join join_orphans calls, "
                "same contract, same guard, every pair independent and "
                "reverted, over a descending pitch ladder with stated cell "
                "and second budgets"),
        nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
