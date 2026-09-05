#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: which open edges close with NO ESCAPE AT ALL?

D-631.  Every router on this board escapes first.  `QBoard.escape` refuses any
launch point where the TRUNK width is not legal, so a land whose only legal
copper is the strip BETWEEN it and its same-net neighbour has no launch point,
and `route_join`, `stitch_pad`, `route_net` and `qrouter.connect_role` all
report `NO LEGAL ESCAPE` on a pair that needs no escape.

`maze3d.pad_bridge` is the lateral twin of `bridge_islands`: ONE straight track,
BOTH ENDPOINTS INSIDE THE LANDS, no escape, no via, proved by the promoter's own
exact-geometry `verify_laid` rather than by any lattice.

    +3V3  U4.2 -> U4.3   BMI270 LGA-14, 0.500 mm pitch, 0.025 mm land gap
      connect_role   0.600 mm  NO LEGAL ESCAPE (blocked by U4.1 x58)
      connect_role   0.400 mm  NO LEGAL ESCAPE (blocked by U4.1 x60)
      connect_role   0.300 mm  OK, 2.174 mm of detour
      pad_bridge     0.400 mm  OK, 0.200 mm, zero attributable KiCad DRC

This screen offers that primitive to every cross-island land pair of every open
retained net and reports what closes.  Its output is the work-list for
`route_maze_batch.py --bridge-pads`.

WHAT IS MEASURED, NOT ASSUMED

  * THE CONTRACT IS THE GATE'S -- `net_contract`, `permitted_layers`,
    `reserved_inner_planes` and the `DRU_CLASS` floors, exactly as
    `route_maze_batch.propose` assembles them, with the guard honoured.
  * NO RUNG IS PROPOSED THAT THE BOARD FORBIDS.  The width ladder runs from the
    netclass contract down to `max(board min_track_width, DRU_CLASS width)` and
    NO FURTHER.  A bridge is ordinary rail copper; it is never a licensed neck,
    and this screen cannot propose one.
  * THE PROOF IS EXACT.  `maze3d.verify_laid` against real obstacle shapes, the
    `.kicad_dru` overlay and the pour-bond guard -- never a raster.
  * EACH PAIR IS ITS OWN REVERTED TRANSACTION unless `--chain`, which merges as
    it goes exactly as the promoter's `bridge_net_pads` does.
  * NOTHING IS WRITTEN.
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
    ap.add_argument("nets", nargs="*",
                    help="default = every retained net with an open edge")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--guard", type=Path)
    ap.add_argument("--max-mm", type=float, default=3.0,
                    help="centre-to-centre bound on ONE bridge")
    ap.add_argument("--grid", type=int, default=100000,
                    help="lattice for the Field only; the bridge proof is exact")
    ap.add_argument("--chain", action="store_true",
                    help="merge as you go, as the promoter's bridge_net_pads "
                         "does, instead of testing every pair independently")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, BOARD_TRACK_MIN)
    from routing_ledger import generate as ledger_build

    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)

    nets = list(a.nets)
    ledger = None
    if not nets:
        ledger = ledger_build(a.board)
        nets = sorted(n["net"] for n in ledger["nets"] if n["open_edges"])

    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)

    out, total = [], 0
    for net in nets:
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        floor = max(BOARD_TRACK_MIN,
                    DRU_CLASS.get(c["netclass"], {}).get("width", 0))
        widths = sorted({c["width"], max(floor, min(c["width"], floor))},
                        reverse=True)
        field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=a.grid, layers=layers,
                         neck=mz.neck_rule(qb),
                         guard=guard_for(spec, net) if spec else None)
        t0 = time.time()
        if a.chain:
            # The promoter's own routine merges as it goes and LAYS COPPER.
            # One mark around the whole net puts the board back, so the next
            # net is still judged against the authoritative one and this screen
            # remains read-only.
            m = qb.mark()
            r = mz.bridge_net_pads(qb, net, field, widths, max_mm=a.max_mm)
            qb.revert(m)
            rec = dict(net=net, netclass=c["netclass"], widths=widths,
                       chain=True, seconds=round(time.time() - t0, 1),
                       **{k: v for k, v in r.items() if k != "net"})
        else:
            islands = mz.net_islands(qb, net)
            bridges, failures = [], []
            for i, A in enumerate(islands):
                for B in islands[i + 1:]:
                    for p in A:
                        for q in B:
                            gap = ((p['x'] - q['x']) ** 2
                                   + (p['y'] - q['y']) ** 2) ** 0.5
                            if gap > a.max_mm * qr.MM:
                                continue
                            m = qb.mark()
                            j = mz.pad_bridge(qb, field, p, q, widths)
                            qb.revert(m)
                            row = dict(a=p['ref'], b=q['ref'],
                                       gap_mm=round(gap / 1e6, 3),
                                       **{k: v for k, v in j.items()
                                          if k not in ('ok', 'pads')})
                            (bridges if j.get("ok") else failures).append(row)
            rec = dict(net=net, netclass=c["netclass"], widths=widths,
                       chain=False, islands=len(islands),
                       bridged=len(bridges), bridges=bridges,
                       failures=failures[:60],
                       seconds=round(time.time() - t0, 1))
        total += rec.get("bridged", 0)
        if rec.get("bridged") or rec.get("failures") or rec.get("bridges"):
            print("  %-34s %-10s widths=%s -> %d bridge(s)%s"
                  % (net[-34:], c["netclass"],
                     "/".join("%.3f" % (w / 1e6) for w in widths),
                     rec.get("bridged", 0),
                     "".join("  %s-%s %.3f mm @%.3f on %s"
                             % (x["a"], x["b"], x["mm"], x["width"] / 1e6,
                                x["layer"])
                             for x in (rec.get("bridges") or []))),
                  file=sys.stderr, flush=True)
        out.append(rec)
        del field

    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha, grid=a.grid,
        max_mm=a.max_mm, chain=bool(a.chain),
        guard=str(a.guard) if a.guard else None,
        guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                      if a.guard else None),
        bridges_found=total,
        question=("which open edges close with a STRAIGHT TRACK BETWEEN TWO "
                  "LANDS and no escape at all -- the case every escape-first "
                  "router on this board reports as NO LEGAL ESCAPE"),
        method=("read-only; maze3d.pad_bridge at the netclass width and the "
                ".kicad_dru class floor and no narrower, endpoints inside the "
                "lands by the inscribed-diamond test, proved by the promoter's "
                "own exact-geometry maze3d.verify_laid, every trial reverted"),
        nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
