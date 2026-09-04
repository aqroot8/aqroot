#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what is the WIDEST run that bonds this land?

D-609, and the run that paid for it.  `screen_pad_escape_relief.py` moves four
levers -- width, clearance, barrel, licence -- one rung at a time and reports
which combination opens a land.  This asks a narrower and sharper question of
ONE land: holding the barrel at the ordinary netclass geometry, what is the
widest RUN that reaches it, and on which layer does that run lie?

`U12.4`/`U12.5` are why it exists.  They are the `TPS63020`'s own `VOUT` pins,
the pair that makes the 3.3 V rail, and the rail had no connection to them at
all.  Every refusal the board had collected for them -- `NO_LEGAL_ESCAPE`,
`NO_VIA_SITE`, `NO_BODY_VIA_SITE`, `NO_DRU_LICENCE`, `SEGMENT_WALL` -- was
true, and none of them varied the one lever that was binding:

    0.400 mm   NO_LEGAL_ESCAPE      both pins
    0.350 mm   NO_BODY_VIA_SITE / NO_LEGAL_ESCAPE
    0.300 mm   NO_BODY_VIA_SITE / NO_LEGAL_ESCAPE
    0.250 mm   NO_BODY_VIA_SITE / NO_LEGAL_ESCAPE
    0.200 mm   BOTH pins escape, run under 4.2 mm, and plant an ORDINARY
               0.65/0.40 mm POWER barrel INSIDE the plane BODY

It runs each pad TWICE: ALONE, every trial reverted, so one pad's success
cannot spend another's barrel site; and TOGETHER, in one transaction, the way a
run would actually lay them -- because a bond that exists only when its
neighbour has not taken the site is not a redundancy, it is a coincidence.

Nothing is written.  The board's sha256 is re-checked at exit.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

DEFAULT_WIDTHS = (600000, 400000, 350000, 300000, 250000, 200000, 150000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("net")
    ap.add_argument("--pad", action="append", default=[], metavar="REF.NUM",
                    required=True,
                    help="the land to price; repeatable.  Every pad named must "
                         "lie on ONE island of the net")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--guard", type=Path)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--max-mm", type=float, default=8.0)
    ap.add_argument("--widths", default=None,
                    help="comma-separated nm ladder, widest first "
                         "(default %s)" % ",".join(str(w)
                                                   for w in DEFAULT_WIDTHS))
    ap.add_argument("--via", default=None, metavar="DIA:DRILL",
                    help="nm barrel to hold constant (default: the netclass's)")
    ap.add_argument("--no-body-landing", action="store_true",
                    help="drop D-608's body predicate -- report barrels that "
                         "are LEGAL rather than barrels that will CONNECT")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard)

    widths = (tuple(int(w) for w in a.widths.split(","))
              if a.widths else DEFAULT_WIDTHS)
    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    spec = load_guard(a.guard) if a.guard else {}
    reserved = reserved_inner_planes(qb.b)
    c = net_contract(qb.b, a.net)
    layers = permitted_layers(qb.routable, c["layers"], reserved, a.net)
    vd, vdr = ((int(v) for v in a.via.split(":")) if a.via
               else (c["via_dia"], c["via_drill"]))
    vd, vdr = int(vd), int(vdr)

    want = set(a.pad)
    islands = mz.net_islands(qb, a.net)
    mine = [isl for isl in islands if any(p["ref"] in want for p in isl)]
    if len(mine) != 1:
        raise SystemExit("the named pads lie on %d islands of %s, not one"
                         % (len(mine), a.net))
    island = [p for p in mine[0] if p["ref"] in want]
    missing = want - {p["ref"] for p in island}
    if missing:
        raise SystemExit("not lands of %s: %s" % (a.net, ", ".join(sorted(missing))))

    doc = dict(schema=1, board=str(a.board), board_sha256=sha, net=a.net,
               netclass=c["netclass"], layers=list(layers),
               via_mm=[vd / 1e6, vdr / 1e6],
               body_landing=not a.no_body_landing,
               island=[p["ref"] for p in mine[0]], pads=sorted(want),
               question="holding the barrel constant, what is the WIDEST run "
                        "that bonds these lands to the plane BODY, and on "
                        "which layer does it lie?",
               rungs=[])
    for w in widths:
        field = mz.Field(qb, a.net, w, c["clr_pad"], c["clr"], vd, vdr,
                         G=a.grid, layers=layers,
                         guard=guard_for(spec, a.net) if spec else None)
        land_ok = (None if a.no_body_landing
                   else mz.body_landing(qb, a.net, field)[0])
        row = dict(width_mm=w / 1e6, pads=[])

        def trial(pad, tag, keep_copper):
            r = mz.stitch_pad(qb, field, pad, max_mm=a.max_mm, land_ok=land_ok)
            return dict(pad=pad["ref"], pass_=tag, ok=bool(r.get("ok")),
                        reason=r.get("reason"), layer=r.get("layer"),
                        mm=r.get("mm"), via_xy=list(r.get("via_xy") or []),
                        why=str(r.get("why"))[:160] if r.get("why") else None)

        for pad in island:                       # ALONE
            saved, m = field.via_ok.copy(), qb.mark()
            row["pads"].append(trial(pad, "alone", False))
            qb.revert(m)
            field.via_ok = saved
        saved, m = field.via_ok.copy(), qb.mark()
        row["pads"] += [trial(pad, "together", True) for pad in island]
        qb.revert(m)
        field.via_ok = saved

        doc["rungs"].append(row)
        for p in row["pads"]:
            print("  %-8s %-9s %-9s %-6s %-18s %s"
                  % ("%.3f" % (w / 1e6), p["pad"], p["pass_"],
                     "OK" if p["ok"] else p["reason"],
                     ("%s %.3f mm" % (p["layer"], p["mm"])) if p["ok"] else "",
                     p["via_xy"]), file=sys.stderr, flush=True)

    doc["authoritative_unchanged"] = (
        sha == hashlib.sha256(a.board.read_bytes()).hexdigest())
    text = json.dumps(doc, indent=1, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
