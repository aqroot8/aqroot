#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: which orphan pour island can a JUMPER close?

D-605.  A pour-owning net's open edges are pieces of its own pour that a
foreign track has CUT, and this board's three pour-owning nets own 31 of its
69 retained open edges.  Two primitives already exist for them and both refuse:

  * `maze3d.stitch_pad` (and therefore `stitch_net` and `--join-residual`)
    asks the PAD to launch a full-width escape.  D-604 swept every legal rung
    of width and barrel and closed 0 of 15 on `+3V3` and 0 of 9 on `GND`.
  * `maze3d.bridge_islands` asks for one point inside cluster A's copper on one
    layer AND inside cluster B's on ANOTHER.  Two pieces of the SAME layer's
    pour never overlap, so it reports `NO_BRIDGE` on exactly these.

`maze3d.join_islands` is the general move both are special cases of: a JUMPER
from a cell inside one cluster's filled copper to a cell inside another's.  No
pad escape at either end, because there is nothing to escape from -- the copper
is already there.  This screen offers every orphan cluster of every pour-owning
net to that primitive with `emit=False` and reports the verdict.

WHAT IS MEASURED, NOT ASSUMED

  * THE SEARCH IS THE EMITTER'S.  `maze3d.join_islands` itself, through
    `maze3d.Field` at the same `.kicad_dru` overlay and the same pour-bond
    guard a gated run uses.  There is no second implementation to drift.
  * THE ANCHOR CONTRACT IS ENFORCED HERE TOO.  A terminal cell must sit at
    least `width/2 + one lattice cell` inside KiCad's own filled polygon, so a
    reported join is one whose ends are inside copper that is already there.
  * A FOREIGN POUR IS PROVED INTACT, NOT ASSUMED.  A jumper's through barrels
    are a hole and an antipad on every layer, so they can SPLIT another net's
    filled pour island -- D-605's first whole-board run did exactly that to
    `/01_POWER_TREE/BQ25185_SYS` and was refused.  The primitive lays each
    jumper, retakes every other pour-owning net's cluster count from KiCad's
    own connectivity, and reverts any jumper that raised one.  That proof runs
    here too, so this screen refuses in ninety seconds what the whole-board
    gate would refuse in six minutes.
  * NOTHING IS WRITTEN.  Each jumper is laid, proved and REVERTED in memory;
    the board file is untouched and the full-board gate remains the only thing
    that promotes copper.
  * `OK` IS A LICENCE TO SPEND A GATE RUN, NOT A PROMISE.  The copper of an
    earlier join is reverted before a later one is measured, so a CHAIN of
    jumpers is optimistic; `NO_PATH`, `NO_ANCHOR` and `SEVERS_FOREIGN_POUR`
    are reliable.
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--guard", type=Path)
    ap.add_argument("--max-mm", type=float, default=0.0,
                    help="cap the wavefront at this run length (0 = the "
                         "module's own WAVE_STEPS budget)")
    ap.add_argument("--via-cost-mm", type=float, default=1.5)
    ap.add_argument("--floors", action="store_true",
                    help="also measure at the .kicad_dru / board floors for "
                         "width and barrel, not only the netclass contract")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN, BOARD_VIA_DIA_MIN,
                                  BOARD_HOLE_MIN, BOARD_TRACK_MIN)

    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)

    nets = list(a.nets)
    if not nets:
        nets = sorted(n for n in {z.GetNetname() for z in qb.b.Zones()
                                  if not z.GetIsRuleArea() and z.IsFilled()}
                      if n and mz.has_plane(qb, n))

    out = []
    for net in nets:
        c = net_contract(qb.b, net)
        if not mz.has_plane(qb, net):
            out.append(dict(net=net, ok=False, reason="NO_PLANE"))
            continue
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        over = DRU_CLASS.get(c["netclass"], {})
        w_floor = max(BOARD_TRACK_MIN, over.get("width", 0))
        d_floor = max(BOARD_HOLE_MIN, over.get("drill", 0))
        v_floor = max(BOARD_VIA_DIA_MIN, d_floor + 2 * ANNULAR_MIN)
        rungs = [("netclass contract",
                  c["width"], c["via_dia"], c["via_drill"])]
        if a.floors and (w_floor, v_floor, d_floor) != (c["width"],
                                                        c["via_dia"],
                                                        c["via_drill"]):
            rungs.append(("kicad_dru / board floor",
                          w_floor, v_floor, d_floor))
        g = guard_for(spec, net) if spec else None
        rec = dict(net=net, netclass=c["netclass"], layers=list(layers),
                   guarded_layers={k: len(v) for k, v in (g or {}).items()},
                   rungs=[])
        for name, width, vdia, vdrill in rungs:
            t0 = time.time()
            field = mz.Field(qb, net, width, c["clr_pad"], c["clr"],
                             vdia, vdrill, G=a.grid, layers=layers, guard=g)
            r = mz.join_islands(qb, net, field, via_cost_mm=a.via_cost_mm,
                                max_mm=a.max_mm, emit=False)
            r["rung"] = name
            r["contract"] = dict(width=width, via_dia=vdia, via_drill=vdrill)
            r["seconds"] = round(time.time() - t0, 1)
            rec["rungs"].append(r)
            print("  %-32s %-24s joined %d / %d  %.0fs"
                  % (net[:32], name, r.get("joined", 0),
                     r.get("joined", 0) + r.get("unjoined", 0),
                     time.time() - t0), file=sys.stderr, flush=True)
        out.append(rec)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(schema=1, board=str(a.board), board_sha256=board_sha,
               authoritative_unchanged=(board_sha == after),
               grid=a.grid, max_mm=a.max_mm,
               guard=str(a.guard) if a.guard else None,
               guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                             if a.guard else None),
               method="read-only; maze3d.join_islands with emit=False, the "
                      "same Field, .kicad_dru overlay and pour-bond guard a "
                      "gated run builds",
               nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
