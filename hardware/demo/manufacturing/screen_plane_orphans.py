#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what does a plane ORPHAN actually cost?

D-604.  A pour-served net's open edges are ISLANDS its own pour never reached,
and on this board they are the single largest family left: `GND` 12 and `+3V3`
15 of 72 retained open edges when this screen was written.  Every one of them is
one `maze3d.stitch_pad` away from closing -- an escape, a short run and one
through barrel down to the net's own plane -- so the question is not WHICH net
to route next but WHAT CONTRACT the stitch is being denied at.

THE NETCLASS WIDTH IS A DEFAULT.  THE `.kicad_dru` FLOOR IS THE RULE.

That is D-603's pad-clearance lesson in a second place.  `GND` carries a 0.30 mm
netclass width and the `.kicad_dru` imposes NO `track_width` rule on it at all,
so the board's own floor for a `GND` track is the 0.15 mm `min_track_width` in
board setup.  A 0.30 mm launch off a 0.350 mm-wide SOT-563 land at 0.5 mm pitch
does not exist; a 0.20 mm one does.  `P3V3` is the opposite case and the table
already knows it -- `DRU_CLASS["P3V3"]["width"]` is the DRU's own 0.40 mm outer
floor, so a request below it is clamped UP and the screen cannot propose copper
the board would refuse.

So this screen sweeps the two levers a stitch actually has -- the RUN WIDTH and
the BARREL -- from the netclass contract down to the floors the board states in
its own rule file, and reports, per island, the verdict at each rung.  Its
output is a `route_maze_batch.py --stitch-width / --stitch-via` transaction, or
the evidence that no legal rung opens that island.

WHAT IS MEASURED, NOT ASSUMED

  * THE EMITTER IS THE PROMOTER'S.  `maze3d.stitch_pad` through
    `maze3d.Field`, at the same `.kicad_dru` overlay, the same pad-escape neck
    rule and the same `verify_laid` proof a gated run uses.
  * NO RUNG IS PROPOSED THAT THE BOARD FORBIDS.  Widths are clamped UP to
    `DRU_CLASS[class]["width"]`, drills to `DRU_CLASS[class]["drill"]` and the
    board `min_through_hole_diameter`, diameters to `min_via_diameter` and the
    0.125 mm annular ring -- the same clamps `route_maze_batch.propose` applies.
  * EACH ISLAND IS INDEPENDENT.  Every trial is reverted, so an island that
    opens is not paid for by one that does not, and the rungs are comparable.
  * NOTHING IS WRITTEN.  The full-board gate remains the only thing that
    promotes copper.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def rungs(width, via_dia, via_drill, w_floor, v_floor, d_floor, steps):
    """(width, dia, drill) from the netclass contract down to the board floors.

    The widths are the caller's ladder clamped into [floor, netclass]; the
    barrel is offered at the netclass size and at the floor, because D-601
    measured that a barrel ladder between them buys nothing on this board.
    """
    ws = sorted({max(w_floor, min(width, w)) for w in steps} | {width, w_floor},
                reverse=True)
    vs = sorted({(via_dia, via_drill), (v_floor, d_floor)}, reverse=True)
    return [(w, vd, vdr) for w in ws for (vd, vdr) in vs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*", default=None,
                    help="pour-owning nets to sweep; default = every net that "
                         "owns a filled pour and has an orphan island")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--max-mm", type=float, default=8.0,
                    help="the stitch's own locality window, in millimetres")
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec to honour")
    ap.add_argument("--width-step", type=int, action="append", default=None,
                    metavar="NM", help="widths to try; repeatable")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN, BOARD_VIA_DIA_MIN,
                                  BOARD_HOLE_MIN, BOARD_TRACK_MIN)

    steps = tuple(a.width_step or (300000, 250000, 230000, 200000, 150000))
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    neck = mz.neck_rule(qb)
    reserved = reserved_inner_planes(qb.b)

    nets = list(a.nets)
    if not nets:
        nets = sorted(n for n in {t.GetNetname() for t in qb.b.GetTracks()}
                      | {p.GetNetname() for f in qb.b.GetFootprints()
                         for p in f.Pads()}
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
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        body = max(islands, key=len)
        orphans = [i for i in islands if i is not body]
        rec = dict(net=net, netclass=c["netclass"], orphan_islands=len(orphans),
                   body_pads=len(body), layers=list(layers),
                   contract=dict(width=c["width"], via_dia=c["via_dia"],
                                 via_drill=c["via_drill"]),
                   dru_floor=dict(width=w_floor, via_dia=v_floor,
                                  drill=d_floor),
                   rungs=[])
        for (w, vd, vdr) in rungs(c["width"], c["via_dia"], c["via_drill"],
                                  w_floor, v_floor, d_floor, steps):
            field = mz.Field(qb, net, w, c["clr_pad"], c["clr"], vd, vdr,
                             G=a.grid, layers=layers, neck=neck,
                             guard=guard_for(spec, net) if spec else None)
            opened, walls = [], []
            for island in orphans:
                hit, last = None, None
                for pad in island:
                    m = qb.mark()
                    r = mz.stitch_pad(qb, field, pad, max_mm=a.max_mm,
                                      escape_limit=12)
                    qb.revert(m)
                    last = r
                    if r.get("ok"):
                        hit = dict(pad=pad["ref"], mm=r["mm"], layer=r["layer"],
                                   via_xy=list(r["via_xy"]))
                        break
                if hit:
                    opened.append(hit)
                else:
                    walls.append(dict(island=[p["ref"] for p in island],
                                      reason=last.get("reason"),
                                      why=str(last.get("why"))[:120]))
            rec["rungs"].append(dict(
                width=w, via_dia=vd, via_drill=vdr,
                legal=bool(w >= w_floor and vd >= v_floor and vdr >= d_floor),
                opened=len(opened), islands=opened, walls=walls))
            print("  %-30s w=%.2f via=%.2f/%.2f -> %d/%d  %s"
                  % (net, w / 1e6, vd / 1e6, vdr / 1e6, len(opened),
                     len(orphans),
                     ", ".join("%s(%.2fmm)" % (o["pad"], o["mm"])
                               for o in opened)),
                  file=sys.stderr, flush=True)
        out.append(rec)

    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        grid=a.grid, max_mm=a.max_mm,
        guard=str(a.guard) if a.guard else None,
        guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                      if a.guard else None),
        question=("for every island a pour-served net's own pour never reached, "
                  "which RUN WIDTH and which BARREL -- swept from the netclass "
                  "contract down to the floors the .kicad_dru and board setup "
                  "state -- lets maze3d.stitch_pad close it"),
        method=("read-only; maze3d.stitch_pad through maze3d.Field at each "
                "rung, every trial reverted, widths and barrels clamped UP to "
                "the same DRU floors route_maze_batch.propose clamps to"),
        nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
