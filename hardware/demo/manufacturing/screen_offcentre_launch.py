#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: does an OFF-CENTRE LAUNCH open the seven lands
that refuse a centre-anchored escape at EVERY width this board can fabricate?

D-632 ran `route_local_two_pad`'s exact-geometry escapes over the whole
`LATTICE_EXACT` list on a ladder from each net's contract width down to the
board's own 0.150 mm `min_track_width`, and SEVEN lands refused at every rung:
`U11.9`, `U11.3`, `U9.8`, `U9.10`, `U21.5`, `U4.8`, `U5.2`.  A refusal that
does not move with width is not a width finding, and D-632 found what it is:
`QBoard.escape` is CENTRE-ANCHORED -- a STRAIGHT segment from the pad's OWN
CENTRE in one of EIGHT directions fixed by the pad's orientation.

`maze3d.offcentre_escapes` is the primitive that measurement names, and this
screen is the measurement.  It asks TWO questions and keeps them apart.

  LANDS.  Per land, per width rung: does the CENTRE-ANCHORED escape answer,
  and does the OFF-CENTRE launch answer?  Each off-centre answer carries
  `offcentre_mm` (how far the anchor moved off the pad centre) and `base_dir`
  (whether the ray is one of the eight `QBoard.escape` already walks), so a
  land opened by the anchor freedom is distinguishable from one opened by the
  direction freedom, and both from one that never needed either.

  PAIRS.  Per open island pair, per width rung: does `offcentre_connect`
  close it?  That routine asks the centre-anchored escape FIRST at every end,
  so a pair that closes today closes today by the same route; the off-centre
  stub is spent only where the classic escape refuses.  A `NO_PATH` here means
  both ends launched and the CORRIDOR is the wall -- a different finding, with
  a different instrument, from a land that cannot leave its own package.

WHAT A RESULT MEANS, AND WHAT IT DOES NOT.  Read-only.  Every trial is laid on
a scratch `QBoard` and REVERTED, and the board file's `sha256` is re-read at
the end and reported.  `QBoard` does not see ZONE fill, so a closure here is a
LICENCE QUESTION and never copper: KiCad's own DRC on the full-board gate is
the only thing that promotes.  A width BELOW a net's class floor is copper this
board licenses nowhere until `.kicad_dru` says so, and `leaf_land_contract.py`
decides whether the rail current binds it -- `licensed_unconditionally` in this
report is that test and nothing more.

    python3 screen_offcentre_launch.py NET [NET ...] [--board B]
        [--widths nm,nm,...] [--pairs N] [--max-gap-mm F] [--lands-only]
        [--pairs-only] [--grid N] [-o OUT]
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def ladder(top_nm, floor_nm):
    """Descending, in the 0.050 mm steps `QBoard.escape` itself walks, with the
    board's own floor always the last rung."""
    out, w = [], int(top_nm)
    while w > floor_nm:
        out.append(w)
        w -= 50000
    out.append(int(floor_nm))
    return sorted(set(out), reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--widths", default="")
    ap.add_argument("--pairs", type=int, default=2)
    ap.add_argument("--max-gap-mm", type=float, default=0.0)
    ap.add_argument("--stub-floor", type=int, default=-1,
                    help="nm.  At each TRUNK rung the off-centre stub walks its own ladder down to this floor, so the narrow width is spent on the stub and never on the haul.  -1 = the board's own min_track_width; pass the trunk width to forbid a neck entirely")
    ap.add_argument("--grid", type=int, default=25000)
    ap.add_argument("--only-lands", default="",
                    help="comma-separated pad refs; ask the LANDS question about these only.  A net with eighty pads has eighty lands and seven of them are the finding")
    ap.add_argument("--lands-only", action="store_true")
    ap.add_argument("--pairs-only", action="store_true")
    ap.add_argument("--noop-control", action="store_true",
                    help="ask NOTHING about walls; instead prove the lever is a no-op.  For every land of every named net, run maze3d.pad_escapes with field.offcentre False and True and require (a) the False answer is a PREFIX of the True answer, land for land, and (b) they differ ONLY where the False answer is EMPTY")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import net_contract, DRU_CLASS, BOARD_TRACK_MIN

    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    cls = mz.net_classes(qb)
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000

    if a.noop_control:
        from route_maze_batch import permitted_layers, reserved_inner_planes
        reserved = reserved_inner_planes(qb.b)
        neck = mz.neck_rule(qb)
        rows, bad = [], []
        for net in a.nets:
            c = net_contract(qb.b, net)
            layers = permitted_layers(qb.routable, c["layers"], reserved, net)
            field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                             c["via_dia"], c["via_drill"], G=a.grid,
                             layers=layers, neck=neck)
            for isl in mz.net_islands(qb, net):
                for p in isl:
                    field.offcentre = False
                    off = mz.pad_escapes(qb, field, p, None)
                    field.offcentre = True
                    on = mz.pad_escapes(qb, field, p, None)
                    key = lambda e: (e["layer"], e["x"], e["y"], e["w"])
                    ko, kn = [key(e) for e in off], [key(e) for e in on]
                    prefix = kn[:len(ko)] == ko
                    added = len(kn) - len(ko)
                    row = dict(net=net, pad=p["ref"], n_off=len(ko),
                               n_on=len(kn), added=added, prefix=prefix,
                               only_where_empty=(added == 0 or len(ko) == 0),
                               offcentre_used=sorted(set(
                                   "%s@%.3f" % (e["layer"], e["offcentre_mm"])
                                   for e in on if e.get("offcentre"))))
                    rows.append(row)
                    if not (row["prefix"] and row["only_where_empty"]):
                        bad.append(row)
        doc = dict(schema=1, board=str(a.board), board_sha256=sha,
                   authoritative_unchanged=(
                       sha == hashlib.sha256(a.board.read_bytes()).hexdigest()),
                   grid=a.grid, control="offcentre no-op",
                   question=("does field.offcentre=True change any launch a "
                             "land already had, or does it only ADD launches "
                             "to lands that had NONE"),
                   lands=len(rows),
                   lands_unchanged=sum(1 for r in rows if r["added"] == 0),
                   lands_opened=sum(1 for r in rows if r["added"] > 0),
                   violations=bad, ok=(not bad), rows=rows)
        text = json.dumps(doc, indent=1, sort_keys=True)
        if a.out:
            a.out.write_text(text + "\n", encoding="utf-8")
        print("noop control: %d lands, %d unchanged, %d opened, %d violations "
              "-> %s" % (len(rows), doc["lands_unchanged"],
                         doc["lands_opened"], len(bad),
                         "PASS" if doc["ok"] else "FAIL"),
              file=sys.stderr)
        return 0 if doc["ok"] else 1

    report = []
    for net in a.nets:
        c = net_contract(qb.b, net)
        floor = max(BOARD_TRACK_MIN,
                    DRU_CLASS.get(c["netclass"], {}).get("width", 0))
        rungs = ([int(x) for x in a.widths.split(",") if x] if a.widths
                 else ladder(c["width"], BOARD_TRACK_MIN))
        ctx = mz.EscapeCtx(qb, net, c["clr_pad"], c["clr"], cls=cls)
        memo = {}
        islands = mz.net_islands(qb, net)
        rec = dict(net=net, netclass=c["netclass"], contract=c["width"],
                   dru_floor=floor, board_track_min=BOARD_TRACK_MIN,
                   islands=len(islands), widths=rungs, lands=[], pairs=[])
        print("== %s  %s  contract %.3f  floor %.3f  islands %d"
              % (net, c["netclass"], c["width"] / 1e6, floor / 1e6,
                 len(islands)), file=sys.stderr, flush=True)

        if not a.pairs_only:
            want = set(x for x in a.only_lands.split(",") if x)
            for isl in islands:
                for p in isl:
                    if want and p["ref"] not in want:
                        continue
                    lr = dict(pad=p["ref"], layers=[L for L in ("F", "B")
                                                    if p.get(L)], rungs=[])
                    # WALK BOTH LADDERS TO THE END.  Stopping at the first
                    # rung EITHER answers conflates them: a land where the
                    # centre-anchored escape also answers at that width has
                    # gained nothing, and reporting it as an opening would
                    # overstate the primitive.  The two widest widths are
                    # recorded separately and the verdict is their COMPARISON.
                    for L in lr["layers"]:
                        cw_best = ow_best = None
                        for w in rungs:
                            t0 = time.time()
                            centre = (qb.escape(p, L, w, w, c["clr_pad"],
                                                c["clr"], a.grid, ox, oy)
                                      if cw_best is None else [])
                            cw = (qb.escape_why[0]
                                  if (cw_best is None and not centre) else None)
                            oc = (mz.offcentre_escapes(qb, ctx, p, L, w,
                                                       a.grid, ox, oy)
                                  if ow_best is None else [])
                            if centre and cw_best is None:
                                cw_best = w
                            if oc and ow_best is None:
                                ow_best = w
                            best = oc[0] if oc else None
                            lr["rungs"].append(dict(
                                layer=L, width=w,
                                centre=bool(centre),
                                centre_why=cw,
                                offcentre=bool(oc),
                                offcentre_why=(None if oc else
                                               mz.offcentre_escapes.why),
                                n=len(oc),
                                offcentre_mm=(best or {}).get("offcentre_mm"),
                                base_dir=(best or {}).get("base_dir"),
                                reach_mm=(best or {}).get("reach_mm"),
                                exit_mm=(best or {}).get("exit_mm"),
                                support_mm=(best or {}).get("support_mm"),
                                escape_formula=(best or {}).get("escape_formula"),
                                a_xy=(None if best is None else
                                      (round(best["ax"] / 1e6, 4),
                                       round(best["ay"] / 1e6, 4))),
                                b_xy=(None if best is None else
                                      (round(best["x"] / 1e6, 4),
                                       round(best["y"] / 1e6, 4))),
                                seconds=round(time.time() - t0, 2)))
                            if cw_best is not None and ow_best is not None:
                                break
                        lr.setdefault("centre_width", {})[L] = cw_best
                        lr.setdefault("offcentre_width", {})[L] = ow_best
                    cwid = [w for w in lr.get("centre_width", {}).values()
                            if w]
                    owid = [w for w in lr.get("offcentre_width", {}).values()
                            if w]
                    lr["best_centre"] = max(cwid) if cwid else None
                    lr["best_offcentre"] = max(owid) if owid else None
                    lr["gained"] = (lr["best_offcentre"] is not None
                                    and (lr["best_centre"] is None
                                         or lr["best_offcentre"]
                                         > lr["best_centre"]))
                    rec["lands"].append(lr)
                    hit = next((r for r in lr["rungs"]
                                if r["offcentre"]
                                and r["width"] == lr["best_offcentre"]), None)
                    if lr["gained"]:
                        msg = ("OFF-CENTRE OPENS at %.3f mm on %s (anchor "
                               "%.3f mm off centre, %s ray, reach %.3f mm "
                               "past its own edge); centre-anchored %s"
                               % (lr["best_offcentre"] / 1e6, hit["layer"],
                                  hit["offcentre_mm"],
                                  "base" if hit["base_dir"] else "new",
                                  hit["reach_mm"],
                                  ("refuses at every rung"
                                   if lr["best_centre"] is None else
                                   "only reaches %.3f mm"
                                   % (lr["best_centre"] / 1e6))))
                    elif lr["best_centre"] is not None:
                        msg = "centre escapes at %.3f mm" % (
                            lr["best_centre"] / 1e6)
                    else:
                        msg = "SEALED at every rung, centre and off-centre"
                    print("   land %-9s %s" % (p["ref"], msg),
                          file=sys.stderr, flush=True)

        if not a.lands_only:
            for i, A in enumerate(islands):
                for B in islands[i + 1:]:
                    combos = sorted(
                        ((math.hypot(p["x"] - q["x"], p["y"] - q["y"]), p, q)
                         for p in A for q in B), key=lambda t: t[0])
                    if a.max_gap_mm and combos[0][0] / 1e6 > a.max_gap_mm:
                        continue
                    for gap, p, q in combos[:max(1, a.pairs)]:
                        layers = [L for L in ("F", "B") if p[L] and q[L]]
                        if not layers:
                            rec["pairs"].append(dict(
                                a=p["ref"], b=q["ref"],
                                gap_mm=round(gap / 1e6, 4), layer=None,
                                closed_at=None, reason="NOT_COPLANAR",
                                why="%s and %s share no outer layer; this "
                                    "instrument lays no via"
                                    % (p["ref"], q["ref"]), rungs=[]))
                            continue
                        layer = layers[0]
                        trials, closed, won = [], None, None
                        for w in rungs:
                            m = qb.mark()
                            t0 = time.time()
                            sf = (BOARD_TRACK_MIN if a.stub_floor < 0
                                  else a.stub_floor)
                            r = mz.offcentre_connect(
                                qb, ctx, p, q, layer, w,
                                stub_widths=ladder(w, min(sf, w)),
                                G=a.grid, memo=memo, limit=1)
                            dt = time.time() - t0
                            qb.revert(m)
                            trials.append(dict(
                                width=w, ok=bool(r.get("ok")),
                                reason=r.get("reason"), why=r.get("why"),
                                pad=r.get("pad"),
                                mm=round(r.get("mm", 0.0), 4),
                                stub_mm=r.get("stub_mm"),
                                stub_widths=[l.get("width")
                                             for l in (r.get("launches") or [])],
                                launches=r.get("launches"),
                                profile=r.get("profile"),
                                seconds=round(dt, 2)))
                            if r.get("ok"):
                                closed, won = w, trials[-1]
                                break
                        rec["pairs"].append(dict(
                            a=p["ref"], b=q["ref"],
                            gap_mm=round(gap / 1e6, 4), layer=layer,
                            closed_at=closed,
                            licensed_unconditionally=(closed is not None
                                                      and closed >= floor),
                            launches=(won or trials[-1]).get("launches"),
                            reason=trials[-1]["reason"],
                            why=trials[-1]["why"], rungs=trials))
                        print("   pair %-9s %-9s %7.3f mm  %s"
                              % (p["ref"], q["ref"], gap / 1e6,
                                 ("CLOSES trunk %.3f mm%s%s" %
                                  (closed / 1e6,
                                   "" if closed >= floor
                                   else "  BELOW the %.3f mm class floor"
                                        % (floor / 1e6),
                                   "".join("  [%s stub %.3f mm%s]"
                                           % (l["pad"], l["width"] / 1e6,
                                              " NECKED" if l.get("necked")
                                              else "")
                                           for l in (won.get("launches")
                                                     or []))))
                                 if closed else
                                 "refused: %s" % str(trials[-1]["why"])[:96]),
                              file=sys.stderr, flush=True)
        report.append(rec)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(schema=1, board=str(a.board), board_sha256=sha,
               authoritative_unchanged=(sha == after), grid=a.grid,
               question=("does an OFF-CENTRE LAUNCH -- a stub anchored "
                         "anywhere on the land's own copper, in any of 24 "
                         "directions -- open the lands and the island pairs "
                         "that a CENTRE-ANCHORED escape refuses at every "
                         "width this board can fabricate"),
               method=("read-only; every trial laid on a scratch QBoard and "
                       "REVERTED, every candidate proved by maze3d.verify_laid "
                       "(exact analytic clearance, never a lattice); zones "
                       "invisible to QBoard, so a closure is a licence "
                       "question and never copper"),
               nets=report)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
