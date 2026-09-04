#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what does the ESCAPE-RELIEF DOCTRINE buy?

D-606.  After D-604 and D-605 the three pour-owning nets still own 30 of the
board's 68 retained open edges, and the failure is now ONE failure repeated:

  * `maze3d.stitch_pad` asks the PAD to launch a full-width escape.  D-604
    swept every rung the netclass and the `.kicad_dru` FLOORS allow and closed
    0 of 15 on `+3V3` and 0 of 9 on `GND`.
  * `maze3d.join_islands` asks a cell of the cluster's OWN FILLED POUR to be
    the terminal.  D-605 re-ran it on the promoted board and got 0 of 32,
    because 23 of those clusters own NO filled pour copper at all -- they are
    bare lands, and a bare land is not a two-dimensional conductor.

Both primitives are denied by the same contract: a 0.250 mm LGA land or a
0.350 mm SOT land cannot launch a 0.400 mm P3V3 track, and a 0.650 mm P3V3
barrel does not fit in the pocket around it.

THE BOARD ALREADY OWNS THE ANSWER AND HAS NEVER SPENT IT.  `FBV2_P2_ROUTING_PLAN.md`
section 17 carries the E6 escape-relief doctrine forward as CTO standing law and
records it as "NOT yet instantiated": ONE RULE AREA PER PAD, named for that pad,
`enclosedByArea()` never `intersectsArea()`, created only when a MEASURED need
appears.  The `.kicad_dru` already instantiates the same shape for VIAS in
sixteen `FINE_ESC_*` areas (D-257: 0.35 mm diameter, 0.075 mm ring, 0.20 mm
hole) and for WIDTH inside ten named power courtyards (0.20 mm).

This screen measures the need.  It offers `maze3d.stitch_pad` -- the promoter's
own primitive, through the promoter's own `Field` -- a RELIEF CONTRACT built
only from numbers this board's rule file already licenses somewhere:

      width 0.200 mm     the pad-escape necking rule's own minimum
      clearance 0.200 mm the BAT tap areas' own local fine-pitch minimum
      barrel 0.35/0.20   the D-257 FINE_ESC_* escape-via geometry

and reports, per orphan land, whether it opens, which of the two levers opened
it, how long the sub-class-width copper is, and the bounding box that copper
would need a relief area to enclose.  Nothing new is invented; what is measured
is whether the doctrine, spent, closes edges.

NOTHING IS WRITTEN.  Every trial is laid, proved by `verify_laid` and REVERTED.
A rung reported here is a licence to author a rule and spend a gate run, not a
promise: the full-board gate remains the only thing that promotes copper.
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# Every number below appears in this board's own `.kicad_dru` already.
RELIEF_WIDTH = 200000        # "Pad-escape necking - width, fine-pitch power packages"
RELIEF_CLR = 200000          # "... - clearance ..." and the BAT_*_TAP_* local rules
RELIEF_VIA_DIA = 350000      # D-257 FINE_ESC_* via_diameter
RELIEF_VIA_DRILL = 200000    # D-257 FINE_ESC_* hole_size
RELIEF_ANNULAR = 75000       # D-257 FINE_ESC_* annular_width


def laid_geometry(qb, mark, field):
    """Bounding box and narrow-copper length of everything laid since `mark`."""
    xs, ys, narrow_nm, segs = [], [], 0.0, []
    for t in qb.laid[mark[0]:]:
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            r = t.GetWidth() / 2.0
            xs += [p.x - r, p.x + r]
            ys += [p.y - r, p.y + r]
            continue
        a, b = t.GetStart(), t.GetEnd()
        w = t.GetWidth()
        xs += [a.x - w / 2.0, a.x + w / 2.0, b.x - w / 2.0, b.x + w / 2.0]
        ys += [a.y - w / 2.0, a.y + w / 2.0, b.y - w / 2.0, b.y + w / 2.0]
        d = math.hypot(b.x - a.x, b.y - a.y)
        segs.append(dict(w=round(w / 1e6, 3),
                         a=[round(a.x / 1e6, 4), round(a.y / 1e6, 4)],
                         b=[round(b.x / 1e6, 4), round(b.y / 1e6, 4)],
                         mm=round(d / 1e6, 4)))
        if w < 400000:
            narrow_nm += d
    if not xs:
        return None
    return dict(bbox_mm=[round(min(xs) / 1e6, 4), round(min(ys) / 1e6, 4),
                         round(max(xs) / 1e6, 4), round(max(ys) / 1e6, 4)],
                narrow_mm=round(narrow_nm / 1e6, 4),
                segments=segs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--max-mm", type=float, default=8.0)
    ap.add_argument("--guard", type=Path)
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
    neck = mz.neck_rule(qb)
    reserved = reserved_inner_planes(qb.b)

    nets = list(a.nets)
    if not nets:
        nets = sorted(n for n in {z.GetNetname() for z in qb.b.Zones()
                                  if not z.GetIsRuleArea() and z.IsFilled()}
                      if n and mz.has_plane(qb, n))

    out = []
    for net in nets:
        if not mz.has_plane(qb, net):
            out.append(dict(net=net, ok=False, reason="NO_PLANE"))
            continue
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        over = DRU_CLASS.get(c["netclass"], {})
        w_floor = max(BOARD_TRACK_MIN, over.get("width", 0))
        d_floor = max(BOARD_HOLE_MIN, over.get("drill", 0))
        v_floor = max(BOARD_VIA_DIA_MIN, d_floor + 2 * ANNULAR_MIN)

        # THE LADDER IS AN ATTRIBUTION, NOT A SEARCH.  Rung 0 is exactly what
        # D-604 measured, so this screen reproduces that verdict before it
        # claims a new one; rungs 1 and 2 move ONE lever each, so a pad that
        # opens says which licence it needs; rung 3 is both.
        rungs = [
            ("0 dru floor (D-604 control)",
             w_floor, c["clr"], v_floor, d_floor),
            ("1 relief WIDTH only",
             min(w_floor, RELIEF_WIDTH), RELIEF_CLR, v_floor, d_floor),
            ("2 relief BARREL only",
             w_floor, c["clr"], RELIEF_VIA_DIA, RELIEF_VIA_DRILL),
            ("3 relief WIDTH + BARREL",
             min(w_floor, RELIEF_WIDTH), RELIEF_CLR,
             RELIEF_VIA_DIA, RELIEF_VIA_DRILL),
            # THE WIDEST COPPER THE BOARD WILL GIVE.  A relief licence is a
            # licence for a BARREL; it is not a reason to lay thinner track
            # than the netclass asks for.  This rung asks whether the same
            # lands open with the run at the full netclass width, so a
            # promoted bond is not quietly at the board floor.
            ("4 relief BARREL at netclass width",
             c["width"], c["clr"], RELIEF_VIA_DIA, RELIEF_VIA_DRILL),
        ]

        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        body = max(islands, key=len)
        orphans = [i for i in islands if i is not body]
        rec = dict(net=net, netclass=c["netclass"], layers=list(layers),
                   orphan_islands=len(orphans), body_pads=len(body),
                   contract=dict(width=c["width"], clr=c["clr"],
                                 via_dia=c["via_dia"], via_drill=c["via_drill"]),
                   dru_floor=dict(width=w_floor, via_dia=v_floor,
                                  drill=d_floor),
                   rungs=[])
        for (name, w, clr, vd, vdr) in rungs:
            field = mz.Field(qb, net, w, c["clr_pad"], clr, vd, vdr,
                             G=a.grid, layers=layers, neck=neck,
                             guard=guard_for(spec, net) if spec else None)
            opened, walls = [], []
            for island in orphans:
                hit, last = None, None
                for pad in island:
                    m = qb.mark()
                    r = mz.stitch_pad(qb, field, pad, max_mm=a.max_mm,
                                      escape_limit=12)
                    geo = laid_geometry(qb, m, field) if r.get("ok") else None
                    qb.revert(m)
                    last = r
                    if r.get("ok"):
                        hit = dict(pad=pad["ref"], mm=r["mm"], layer=r["layer"],
                                   via_xy=list(r["via_xy"]),
                                   pad_xy=[round(pad["x"] / 1e6, 4),
                                           round(pad["y"] / 1e6, 4)],
                                   geometry=geo)
                        break
                if hit:
                    opened.append(hit)
                else:
                    walls.append(dict(island=[p["ref"] for p in island],
                                      reason=last.get("reason"),
                                      why=str(last.get("why"))[:140]))
            rec["rungs"].append(dict(
                rung=name, width=w, clr=clr, via_dia=vd, via_drill=vdr,
                needs_licence=bool(w < w_floor or clr < c["clr"]
                                   or vd < v_floor or vdr < d_floor),
                opened=len(opened), islands=opened, walls=walls))
            print("  %-22s %-28s -> %d/%d  %s"
                  % (net[:22], name, len(opened), len(orphans),
                     ", ".join("%s(%.2fmm)" % (o["pad"], o["mm"])
                               for o in opened)),
                  file=sys.stderr, flush=True)
        out.append(rec)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        authoritative_unchanged=(board_sha == after),
        grid=a.grid, max_mm=a.max_mm,
        guard=str(a.guard) if a.guard else None,
        guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                      if a.guard else None),
        relief=dict(width=RELIEF_WIDTH, clr=RELIEF_CLR,
                    via_dia=RELIEF_VIA_DIA, via_drill=RELIEF_VIA_DRILL,
                    annular=RELIEF_ANNULAR,
                    provenance="every figure is already licensed by this "
                               "board's own .kicad_dru: 0.200 mm width and "
                               "clearance by the pad-escape necking rules, "
                               "0.35/0.20 mm and the 0.075 mm ring by the "
                               "sixteen D-257 FINE_ESC_* areas"),
        question=("for every orphan land of a pour-owning net, does the E6 "
                  "escape-relief doctrine of FBV2_P2_ROUTING_PLAN section 17 "
                  "-- one rule area per pad -- open it, and which lever does "
                  "the opening"),
        method=("read-only; maze3d.stitch_pad through maze3d.Field at four "
                "rungs, verify_laid proving each, every trial reverted"),
        nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
