#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: does an OFF-CENTRE LAUNCH plus a LAYER HOP close
the island pairs that a FLAT off-centre connect refuses?

D-633 built the off-centre launch and measured exactly what it was worth: it
opens TWENTY-NINE lands, four of them at or above their own class floor, and
then hands every one of them to a CORRIDOR that refuses.  Its own verdict was
that the next primitive is the HOP -- "the exact stub, a barrel at the first
via site the STUB can reach, the haul on a far layer" -- because both corridor
instruments this board owns had the same gap.  `qrouter.connect_role` is exact
at the escape and FLAT: one layer, no via, so it can only offer the lane the
pocket is already congested with.  `qrouter.connect_hop` has the barrel but
escapes from the pad CENTRE and cannot be given an anchor, so it refuses at
precisely the lands the off-centre launch opened.

`maze3d.offcentre_hop` is the composition, and this screen is its measurement.

WHAT IT ASKS.  For one net: `maze3d.net_islands` for the copper that already
joins its lands, then, for every ORDERED PAIR of islands, the `--pairs`
nearest pad-to-pad combinations, each over a descending trunk-width ladder.
At every rung BOTH instruments are asked on the SAME board state and the
answers are diffed, so the report never says "the hop closed it" without also
saying whether the flat connect closed it too.  That A/B is the product: the
hop may only ever ADD closures, and a rung where both close is a rung where
the barrel bought nothing and the flat route is the better copper.

PAIRS THAT SHARE NO OUTER LAYER ARE ASKED FOR THE FIRST TIME.  The flat
instruments report `NOT_COPLANAR` and stop -- "this instrument lays no via".
The hop lays two, or one when an end is already on the haul layer, so a pair
whose lands live on opposite faces is a question again.

WHAT A RESULT MEANS, AND WHAT IT DOES NOT.  A closure here is a LICENCE
QUESTION, never copper: every trial is laid on the live `QBoard`, proved by
`maze3d.verify_laid` -- exact analytic clearance against real obstacle shapes,
the `.kicad_dru` overlay and every drilled hole, never a lattice -- and then
REVERTED.  `QBoard` does not see ZONE fill, so a corridor this reports may
still cross a foreign pour, and only the full-board gate promotes.  A trunk
below the net's class floor, or a barrel below the board's `min_via_diameter`,
is copper this board licenses nowhere until a rule says so.

    python3 screen_offcentre_hop.py NET [NET ...] [--board B]
        [--widths nm,nm,...] [--pairs N] [--max-gap-mm F] [--far F,B,I2,I3]
        [--via DIA,DRILL] [--stub-floor NM] [--grid N] [--no-flat] [-o OUT]
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
    """Descending, in the 0.050 mm steps `QBoard.escape` itself walks, with
    the floor always the last rung."""
    out, w = [], int(top_nm)
    while w > floor_nm:
        out.append(w)
        w -= 50000
    out.append(int(floor_nm))
    return sorted(set(out), reverse=True)


def land_census(qb, mz, ctx, pad, islands, c, far, ladder, G, span, limit,
                stub_floor, memo, field=None, pocket_grid=100000):
    """Is this ONE land HOP-READY, and if not, WHICH of the three things
    a hop needs does it lack?

    A hop needs three things and they fail independently: a LAUNCH (a legal
    stub off the land's own copper), REACH (board the launch can actually walk
    to at the trunk width), and a BARREL (a site inside that reach which
    clears EVERY layer of the stack and every drilled hole).  Asking a pair
    answers all three at once and reports only the first that failed, per
    ordered pair, per width rung, per far layer -- which is both slow and
    ambiguous.  This asks the land alone.

    `reach_mm2` is the measurement the pair-level report cannot produce and it
    is the one that explains this board: an escape may be perfectly legal and
    land inside a POCKET of a couple of square millimetres, and no barrel
    ladder and no far layer can help a launch that cannot walk anywhere.
    """
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    other = min((p for isl in islands for p in isl
                 if p["ref"] != pad["ref"]),
                key=lambda p: (p["x"] - pad["x"]) ** 2
                + (p["y"] - pad["y"]) ** 2)
    rec = dict(ref=pad["ref"],
               xy=(round(pad["x"] / 1e6, 4), round(pad["y"] / 1e6, 4)),
               layers="".join(L for L in ("F", "B") if pad[L]),
               near=[], verdict="NO_LAUNCH", why=None)
    _ = field
    sl = mz_ladder(c["width"], min(stub_floor, c["width"]))
    for nl in ("F", "B"):
        if not pad.get(nl):
            continue
        cands, sw, why = mz._hop_launch(qb, ctx, pad, other, nl, c["width"],
                                        sl, G, ox, oy, memo, limit,
                                        mz.OFFCENTRE_REACH_MM,
                                        mz.OFFCENTRE_ANCHOR_FRACS,
                                        mz.OFFCENTRE_DIR_STEP_DEG)
        n = dict(layer=nl, launched=bool(cands), stub_width=(sw if cands
                                                             else None),
                 centre=(bool(cands[0].get("centre")) if cands else None),
                 why=(None if cands else why), reach_cells=None,
                 reach_mm2=None, barrels=[])
        if cands:
            cand = cands[0]
            # CAN A WAVEFRONT LEAVE THIS LANDING?  Exact geometry decides
            # whether the stub is legal; it does not decide whether the 3D
            # corridor can START there, and on this board that is the
            # operative wall.  `/WAKE_INT_N` `U2.1 -> U3.1` returns NO_PATH in
            # ZERO seconds because every lattice cell beside the landing is
            # blocked and the seed set is a single island.
            if field is not None:
                leave = mz._lattice_leavable(field, nl)
                n["lattice_leavable"] = (
                    None if leave is None else
                    bool(any(leave(x["x"], x["y"]) for x in cands)))
            n["landing"] = (round(cand["x"] / 1e6, 4),
                            round(cand["y"] / 1e6, 4))
            reg = qb.free_region(nl, ctx.net, c["width"], c["clr_pad"],
                                 c["clr"], G, (cand["x"], cand["y"]),
                                 cand["x"] - span, cand["y"] - span,
                                 cand["x"] + span, cand["y"] + span)
            if reg is not None:
                cells = int(reg[0].sum())
                n["reach_cells"] = cells
                n["reach_mm2"] = round(cells * (G / 1e6) ** 2, 4)
            for L in far:
                if L == nl:
                    n["barrels"].append(dict(far=L, none_needed=True))
                    continue
                bar, pocket = None, None
                for cand2 in cands:
                    sites = mz._hop_sites(qb, ctx, nl, L, cand2, c["width"],
                                          ladder, G, span, 96, 1)
                    if sites:
                        bar = sites[0]
                        break
                if bar is not None:
                    # THE POCKET IS THE MEASUREMENT THE BARREL ALONE CANNOT
                    # MAKE.  A legal barrel that lands in a two-square-
                    # millimetre island of the haul layer is not a hop, it is
                    # a trap, and `In2.Cu` on this board is a field of 790
                    # through barrels cut into exactly such islands.
                    # BOARD-WIDE AND THEREFORE COARSE.  The pocket is only
                    # meaningful measured over the WHOLE layer -- a bounded
                    # window would report its own edge as the pocket's -- and
                    # at 0.025 mm that is 28 million cells per barrel.  The
                    # coarser lattice has a LARGER guard band and so reports a
                    # SMALLER pocket: the number is a lower bound, which is
                    # the safe direction for a figure whose only use is to say
                    # a barrel is trapped.
                    pg = pocket_grid
                    reg = qb.free_region(L, ctx.net, c["width"], c["clr_pad"],
                                         c["clr"], pg, (bar[0], bar[1]),
                                         qb.ex0, qb.ey0, qb.ex1, qb.ey1)
                    if reg is not None:
                        pocket = round(int(reg[0].sum()) * (pg / 1e6) ** 2, 3)
                n["barrels"].append(dict(
                    far=L, none_needed=False,
                    ok=bar is not None,
                    dia=(bar[2] if bar else None),
                    drill=(bar[3] if bar else None),
                    pocket_mm2=pocket,
                    xy=(None if bar is None else (round(bar[0] / 1e6, 4),
                                                  round(bar[1] / 1e6, 4))),
                    walk_mm=(None if bar is None else
                             round(math.hypot(bar[0] - cands[0]["x"],
                                              bar[1] - cands[0]["y"]) / 1e6,
                                   4))))
        rec["near"].append(n)
    launched = [n for n in rec["near"] if n["launched"]]
    hops = [b for n in launched for b in n["barrels"] if b.get("ok")]
    flat = [b for n in launched for b in n["barrels"] if b.get("none_needed")]
    if not launched:
        rec["verdict"] = "NO_LAUNCH"
        rec["why"] = (rec["near"][0]["why"] if rec["near"] else
                      "%s is on no outer layer" % pad["ref"])
    elif not any(n.get("lattice_leavable", True) for n in launched):
        # The land launches, the barrel exists, and the 3D wavefront cannot
        # take a single step from where the stub lands.  That is a DIFFERENT
        # wall from either, and it is the one this board mostly has.
        rec["verdict"] = "LATTICE_TRAPPED"
        rec["why"] = ("launches on %s and every lattice cell beside every "
                      "landing is blocked, so no wavefront can start there"
                      % "/".join(n["layer"] for n in launched))
    elif hops:
        # HOP_READY means a barrel to a layer this land is NOT on.  A land
        # that merely sits on a haul layer is not hop-ready, it is FLAT_ONLY:
        # it can be one END of a hop whose OTHER end changes layer, and it can
        # never change layer itself.  Collapsing the two is how a census
        # reports a wall as an opening.
        rec["verdict"] = "HOP_READY"
        rec["why"] = "barrel %s" % ", ".join(
            "%s %.2f mm at %.2f mm walk into %s mm2"
            % (b["far"], b["dia"] / 1e6, b["walk_mm"], b["pocket_mm2"])
            for b in hops[:3])
    elif flat:
        rec["verdict"] = "FLAT_ONLY"
        rec["why"] = ("launches on %s, which is itself a haul layer, and no "
                      "rung of the ladder reaches a barrel to any other"
                      % "/".join(n["layer"] for n in launched))
    else:
        rec["verdict"] = "NO_BARREL"
        rec["why"] = ("launches on %s into %s mm2 of reachable board and no "
                      "rung of the ladder clears every layer there"
                      % ("/".join(n["layer"] for n in launched),
                         "/".join(str(n["reach_mm2"]) for n in launched)))
    return rec


def mz_ladder(top_nm, floor_nm):
    return ladder(top_nm, floor_nm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--widths", default="")
    ap.add_argument("--pairs", type=int, default=2)
    ap.add_argument("--max-gap-mm", type=float, default=0.0)
    ap.add_argument("--far", default="",
                    help="comma-separated haul layers, in order.  Default is "
                         "the net's own permitted routable layers after plane "
                         "reservation")
    ap.add_argument("--via", default="",
                    help="semicolon-separated DIA,DRILL rungs in nm, widest "
                         "first.  Default is the net's netclass via plus "
                         "every BRIDGE_LADDER rung that still meets this "
                         "class's ordinary floors unaided")
    ap.add_argument("--stub-floor", type=int, default=-1,
                    help="narrowest off-centre stub, nm; default is the "
                         "board's own min_track_width")
    ap.add_argument("--grid", type=int, default=25000)
    ap.add_argument("--limit", type=int, default=6,
                    help="launch candidates tried per end before the end is "
                         "declared to have no reachable barrel")
    ap.add_argument("--lands", action="store_true",
                    help="HOP-READINESS CENSUS ONLY: per LAND, does it "
                         "launch, how much board can the launch reach, "
                         "and is a "
                         "whole-stack barrel reachable from it -- and at what "
                         "diameter.  No pair is asked and no corridor is "
                         "searched, so this is the cheap question that says "
                         "which pairs are worth the expensive one")
    ap.add_argument("--split-lands", action="store_true",
                    help="THE POSITIVE CONTROL.  Treat every land of the net "
                         "as its own island, so a CONNECTED net can be "
                         "asked to route from scratch.  Its existing copper "
                         "proves a corridor exists and `QBoard` cannot see "
                         "the net's own copper, so a refusal would be an "
                         "INSTRUMENT "
                         "failure and a closure is proof the instrument works")
    ap.add_argument("--route", action="store_true",
                    help="ask `maze3d.offcentre_route` -- the EXACT launch "
                         "and the FULL 3D corridor, which places its own "
                         "barrels "
                         "and changes layer mid-haul -- instead of the flat "
                         "`offcentre_hop`.  This is the strongest instrument "
                         "this board owns and the one whose refusals are "
                         "board facts rather than instrument limits")
    ap.add_argument("--field-grid", type=int, default=100000,
                    help="the 3D wavefront's own lattice, nm.  Used ONLY to "
                         "ask whether a wavefront could leave each landing")
    ap.add_argument("--span-mm", type=float, default=6.0,
                    help="how far from a launch a barrel site may be sought")
    ap.add_argument("--no-flat", action="store_true",
                    help="skip the flat offcentre_connect control (faster, "
                         "and strictly less evidence)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, DRU_CLASS, BOARD_TRACK_MIN,
                                  BRIDGE_LADDER, via_floors,
                                  reserved_inner_planes, permitted_layers)

    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)

    report = []
    for net in a.nets:
        c = net_contract(qb.b, net)
        floor = max(BOARD_TRACK_MIN,
                    DRU_CLASS.get(c["netclass"], {}).get("width", 0))
        rungs = ([int(x) for x in a.widths.split(",") if x] if a.widths
                 else ladder(c["width"], BOARD_TRACK_MIN))
        far = ([x for x in a.far.split(",") if x] if a.far
               else list(permitted_layers(qb.routable, c["layers"],
                                          reserved, net)))
        # THE BARREL LADDER IS UNLICENSED BY CONSTRUCTION, AND IT NEVER
        # STARTS ABOVE THE NETCLASS VIA.  The netclass barrel is the one this
        # board's own rules pick for this net and it is the head of the
        # ladder; below it come the FINER rungs of the driver's own
        # `BRIDGE_LADDER` that still meet this class's ORDINARY floors
        # unaided.  A rung COARSER than the netclass via is not offered: it is
        # harder to place, buys nothing electrically, and would make the hop
        # ask for room the net was never entitled to.  A rung below a
        # floor is deliberately absent: it would need a `.kicad_dru` rule area
        # naming the net, which is a licence question and not a screen's to
        # answer.
        floors = via_floors(c["netclass"])
        if a.via:
            vl = [tuple(int(x) for x in r.split(","))
                  for r in a.via.split(";")]
        else:
            head = (c["via_dia"], c["via_drill"])
            vl = [head] + sorted(
                (r for r in BRIDGE_LADDER
                 if mz._meets_floors(r[0], r[1], floors) and r[0] < head[0]),
                key=lambda r: (-r[0], -r[1]))

        ctx = mz.EscapeCtx(qb, net, c["clr_pad"], c["clr"])
        islands = mz.net_islands(qb, net)
        if a.split_lands:
            islands = [[q] for isl in islands for q in isl]
        sf = BOARD_TRACK_MIN if a.stub_floor < 0 else a.stub_floor
        rec = dict(net=net, netclass=c["netclass"], contract=c["width"],
                   dru_floor=floor, board_track_min=BOARD_TRACK_MIN,
                   far=far, via_ladder=vl, stub_floor=sf,
                   islands=len(islands), widths=rungs, lands=[], pairs=[])
        print(" %s  %d islands  far=%s  barrels %s"
              % (net, len(islands), ",".join(far),
                 " ".join("%.2f/%.2f" % (d / 1e6, k / 1e6) for d, k in vl)),
              file=sys.stderr, flush=True)
        memo = {}
        if a.lands:
            # THE CENSUS SET IS THE SET THE PAIR QUESTION WOULD ASK ABOUT --
            # the `--pairs` nearest lands of every open island pair -- and not
            # every land of the net.  On `GND` those differ by 246 to 6, and a
            # census of the 240 lands nobody is going to ask about is a slow
            # way to learn nothing.
            span = int(round(a.span_mm * 1e6))
            field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                             c["via_dia"], c["via_drill"], G=a.field_grid,
                             layers=far)
            want, seen = [], set()
            for i, A in enumerate(islands):
                for Bi in islands[i + 1:]:
                    combos = sorted(
                        ((math.hypot(u["x"] - v["x"], u["y"] - v["y"]), u, v)
                         for u in A for v in Bi), key=lambda t: t[0])
                    if a.max_gap_mm and combos[0][0] / 1e6 > a.max_gap_mm:
                        continue
                    for _, u, v in combos[:max(1, a.pairs)]:
                        for t in (u, v):
                            if t["ref"] not in seen:
                                seen.add(t["ref"])
                                want.append(t)
            if True:
                for q in want:
                    rec["lands"].append(land_census(
                        qb, mz, ctx, q, islands, c, far, vl, a.grid, span,
                        a.limit, sf, memo, field=field,
                        pocket_grid=a.field_grid))
                    lr = rec["lands"][-1]
                    print("   land %-9s %-11s %s"
                          % (q["ref"], lr["verdict"],
                             lr["why"] or ""), file=sys.stderr, flush=True)
            report.append(rec)
            continue
        for i, A in enumerate(islands):
            for B in islands[i + 1:]:
                combos = sorted(
                    ((math.hypot(p["x"] - q["x"], p["y"] - q["y"]), p, q)
                     for p in A for q in B), key=lambda t: t[0])
                if a.max_gap_mm and combos[0][0] / 1e6 > a.max_gap_mm:
                    continue
                for gap, p, q in combos[:max(1, a.pairs)]:
                    coplanar = [L for L in ("F", "B") if p[L] and q[L]]
                    trials, closed, won = [], None, None
                    if a.route:
                        for w in rungs:
                            fld = mz.Field(qb, net, w, c["clr_pad"], c["clr"],
                                           c["via_dia"], c["via_drill"],
                                           G=a.field_grid, layers=far)
                            m = qb.mark()
                            t0 = time.time()
                            r = mz.offcentre_route(
                                qb, fld, p, q, stub_widths=[w],
                                G=a.field_grid, limit=a.limit)
                            dt = time.time() - t0
                            qb.revert(m)
                            trials.append(dict(
                                width=w, ok=bool(r.get("ok")),
                                reason=r.get("reason"), why=r.get("why"),
                                pad=r.get("pad"), vias=r.get("vias"),
                                via_xy=r.get("via_xy"),
                                hop_layers=r.get("layers"),
                                mm_by_layer=r.get("mm_by_layer"),
                                terminals=r.get("terminals"),
                                mm=round(r.get("mm", 0.0), 4),
                                stub_mm=r.get("stub_mm"),
                                launches=r.get("launches"),
                                seconds=round(dt, 2)))
                            if r.get("ok"):
                                closed, won = w, trials[-1]
                                break
                        rec["pairs"].append(dict(
                            a=p["ref"], b=q["ref"],
                            gap_mm=round(gap / 1e6, 4),
                            coplanar=coplanar or None, closed_at=closed,
                            instrument="offcentre_route",
                            licensed_unconditionally=(closed is not None
                                                      and closed >= floor),
                            vias=(won or {}).get("vias"),
                            hop_layers=(won or {}).get("hop_layers"),
                            launches=(won or trials[-1]).get("launches"),
                            reason=trials[-1]["reason"],
                            why=trials[-1]["why"], rungs=trials))
                        print("   %-9s %-9s %7.3f mm  %s"
                              % (p["ref"], q["ref"], gap / 1e6,
                                 ("CLOSES trunk %.3f mm, %d via%s, %s"
                                  % (closed / 1e6, won["vias"] or 0,
                                     "" if won["vias"] == 1 else "s",
                                     "->".join(won["hop_layers"] or [])))
                                 if closed else
                                 "refused: %s %s"
                                 % (trials[-1]["reason"],
                                    str(trials[-1]["why"])[:80])),
                              file=sys.stderr, flush=True)
                        continue
                    for w in rungs:
                        sl = ladder(w, min(sf, w))
                        m = qb.mark()
                        t0 = time.time()
                        r = mz.offcentre_hop(qb, ctx, p, q, far, w,
                                             stub_widths=sl, G=a.grid,
                                             memo=memo, limit=a.limit,
                                             via_ladder=vl)
                        dt = time.time() - t0
                        qb.revert(m)
                        flat = None
                        if not a.no_flat and coplanar:
                            m = qb.mark()
                            f = mz.offcentre_connect(
                                qb, ctx, p, q, coplanar[0], w,
                                stub_widths=sl, G=a.grid, memo=memo, limit=1)
                            qb.revert(m)
                            flat = dict(ok=bool(f.get("ok")),
                                        reason=f.get("reason"),
                                        mm=round(f.get("mm", 0.0), 4))
                        trials.append(dict(
                            width=w, ok=bool(r.get("ok")),
                            reason=r.get("reason"), why=r.get("why"),
                            pad=r.get("pad"), far=r.get("far"),
                            far_tried=r.get("far_tried"),
                            vias=r.get("vias"),
                            barrels=r.get("barrels"),
                            mm=round(r.get("mm", 0.0), 4),
                            stub_mm=r.get("stub_mm"),
                            walk_mm=r.get("walk_mm"),
                            launches=r.get("launches"),
                            profile=r.get("profile"),
                            flat=flat, seconds=round(dt, 2)))
                        if r.get("ok"):
                            closed, won = w, trials[-1]
                            break
                    rec["pairs"].append(dict(
                        a=p["ref"], b=q["ref"], gap_mm=round(gap / 1e6, 4),
                        coplanar=coplanar or None, closed_at=closed,
                        licensed_unconditionally=(closed is not None
                                                  and closed >= floor),
                        hop_only=bool(
                            closed is not None and won
                            and not (won.get("flat") or {}).get("ok")),
                        vias=(won or {}).get("vias"),
                        barrels=(won or {}).get("barrels"),
                        far=(won or trials[-1]).get("far"),
                        launches=(won or trials[-1]).get("launches"),
                        reason=trials[-1]["reason"], why=trials[-1]["why"],
                        rungs=trials))
                    last = rec["pairs"][-1]
                    print("   %-9s %-9s %7.3f mm  %s"
                          % (p["ref"], q["ref"], gap / 1e6,
                             ("CLOSES trunk %.3f mm on %s, %d via%s%s%s"
                              % (closed / 1e6, last["far"], last["vias"] or 0,
                                 "" if last["vias"] == 1 else "s",
                                 "" if closed >= floor
                                 else "  BELOW the %.3f mm class floor"
                                      % (floor / 1e6),
                                 "  [HOP ONLY]" if last["hop_only"]
                                 else "  (flat closes too)"))
                             if closed else
                             "refused: %s" % str(trials[-1]["why"])[:96]),
                          file=sys.stderr, flush=True)
        report.append(rec)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(schema=1, board=str(a.board), board_sha256=sha,
               authoritative_unchanged=(sha == after), grid=a.grid,
               instrument=("offcentre_route" if a.route else "offcentre_hop"),
               split_lands=bool(a.split_lands),
               question=("does an OFF-CENTRE LAUNCH plus a LAYER HOP -- exact "
                         "stub, barrel at the first via site the stub can "
                         "reach, haul on a far layer -- close the island "
                         "pairs the FLAT off-centre connect refuses"),
               method=("read-only; every trial laid on the live QBoard, "
                       "proved by maze3d.verify_laid (exact analytic "
                       "clearance on every layer plus hole-to-hole, never a "
                       "lattice) and REVERTED; zones invisible to QBoard, so "
                       "a closure is a licence question and never copper"),
               nets=report)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
