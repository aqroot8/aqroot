#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: can a corridor be opened by DETOURING the tracks
that cross it, and does every one of them go back?

`screen_corridor_blockers.py` asks WHOSE copper stands in a corridor and prices
two units of removal: `--evict` (copper wholly inside a window) and
`--evict-whole` (a named net's entire copper board-wide).  On the `J3 -> U10`
USB connector corridor both answers were refusals -- D-583 found the minimal
containment-bounded eviction to be `J3.A1`/`B12`'s own ground escape, and D-602
proved that **no `--evict-whole` transaction of any size opens it**, because
`/I2C_SDA_INT` is load-bearing and cannot rebuild itself.  Every one of those
verdicts named the same missing unit:

    the SEGMENT -- a track that merely CROSSES the corridor is reachable by
    neither eviction, and the honest move is to lay it again BETWEEN ITS OWN
    TWO ENDS, around the lane, so nothing is stranded.

D-607 built that unit (`route_maze_batch.py --detour-spec`) and D-607/D-617
spent it -- on POUR LANDS, where the reserved site is a DISC around a barrel,
screened by `screen_segment_evict.py`.  A corridor is the same question with a
different reservation: the site is a LANE, and the lane does not exist yet.
This screen is that instrument, and it asks the whole question rather than half
of it, because D-608 already paid for the half:

  1. SEGMENT UPPER BOUND.  Hold every crossing TRACK out -- tracks only, never
     a via and never a pad, because those are not what a detour moves.  Still
     `NO_PATH` => `SEGMENT_WALL`, and no detour transaction of any size opens
     this corridor.  The expensive questions are skipped.
  2. MINIMAL.  Reverse-greedy delta debugging over the crossing tracks, the
     same discipline `minimal_eviction` uses, re-proved at the end on the real
     `route_join`.  Every track still in the set is one whose return closes the
     corridor again.
  3. THE LANE.  With that set held out, ROUTE the edge for real and keep the
     copper, exactly as the applier will.  The reservation is then sampled off
     the path the router actually won -- D-602's `--from-copper` discipline,
     "reserve what you won", applied to a lane that does not exist yet: a
     STRAIGHT centreline is a claim about a corridor the board does not offer
     (66 of its 83 cells were already blocked for the USB pair itself), and
     this is the only other way to have real geometry to reserve.
  4. THE RELAY.  Group the cut tracks into same-net CHAINS and put each one
     back between its own two free ends with the lane in force, in spec order,
     on a board already carrying the previous detour -- `route_maze_batch.py`'s
     own `detour_layers`, `guard_for` and `maze3d.route_points`, so the screen
     and the applier cannot disagree.  A chain that will not go back REFUSES
     the corridor here, for free, instead of in a gate run that ends in
     `track_dangling` and a clause-4 regression.

THE BOUND IS MEASURED, NOT CHOSEN.  D-607 bounds a pocket detour by
`was + 2*pi*R`, the circumference of the disc it must walk around.  A lane is
not a disc: the longest a genuine detour past it can be is the walk down one
side, around an end and back, so the bound here is
`was + 2*(lane_mm + 2*pi*R)` -- and a route longer than that went somewhere
else entirely and is a reroute wearing a detour's name.  Each plan entry states
its own `max_mm` explicitly, because `route_maze_batch.detour_apply` would
otherwise default to `was + 2*pi*R_max` off the (empty) `reserve` list, and
D-617 measured that a `max_mm` is ALSO the wavefront budget: bound the length,
not the search.

Nothing here writes the board.  Its outputs are a survey, a `--detour-spec`
plan and the lane `--guard` file, so the measurement and the transaction cannot
drift apart -- `screen_segment_evict.py --plan-out`'s contract, for a corridor.

    python3 screen_corridor_detour.py NET [NET ...] \
        --plan-out PLAN.json --guard-out LANE.json -o SURVEY.json
    python3 route_maze_batch.py NET [NET ...] \
        --detour-spec PLAN.json --guard LANE.json --promote
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

from protected_copper import PROTECTED
from screen_corridor_blockers import WithoutObjects, bbox, centre

LANE_STEP_MM = 0.1          # lane sampling pitch; one lattice cell at --grid
LANE_LABEL = "USB_CORRIDOR"


def crossing_tracks(qb, layers, box, mynet):
    """Every foreign routed TRACK whose copper INTERSECTS `box` on `layers`.

    TRACKS ONLY, and that is the whole point.  `corridor_nets` counts what an
    `--evict` may take (copper wholly inside the window) and `crossing_nets`
    counts what an `--evict-whole` may take (a whole net, board-wide).  A
    detour moves ONE track and puts it back between its own two ends, so the
    candidate set is the crossing tracks and nothing else: a via cannot be
    relaid between two ends it does not have, and a pad is where a part is
    soldered.
    """
    x0, y0, x1, y1 = box
    out = []
    for L in layers:
        for s in qb.shapes[L]:
            if s.net in (None, mynet) or s.tag != "track":
                continue
            a, b, c, d = s.bbox(0)
            if c < x0 or d < y0 or a > x1 or b > y1:
                continue
            out.append((L, s))
    # Deterministic: net, then the object's own geometry.  Reverse-greedy is
    # minimal with respect to single-object addition, not globally minimum, so
    # a different order can land on a different minimal set and the answer has
    # to be reproducible.
    out.sort(key=lambda t: (t[1].net, t[0], t[1].x0, t[1].y0, t[1].x1, t[1].y1))
    return out


def minimal_tracks(qb, field, src, dst, objs, escape_limit, via_cost_mm):
    """The SMALLEST subset of crossing tracks whose absence opens the corridor.

    Reverse-greedy: the caller has proved all of them gone opens it, so try to
    PUT EACH ONE BACK and keep it back whenever the corridor survives.  Re-
    proved at the end on the real `route_join`, never on a heuristic.
    """
    import maze3d as mz
    keep = {id(s) for (_L, s) in objs}
    for (_L, s) in objs:
        trial = keep - {id(s)}
        with WithoutObjects(qb, field, trial):
            r = mz.route_join(qb, field, src, dst, escape_limit, via_cost_mm,
                              emit=False)
        if r.get("ok"):
            keep = trial
    with WithoutObjects(qb, field, keep):
        proof = mz.route_join(qb, field, src, dst, escape_limit, via_cost_mm,
                              emit=False)
    return [(L, s) for (L, s) in objs if id(s) in keep], proof


def sample_lane(segs, step_mm=LANE_STEP_MM):
    """Integer-nanometre points along the polyline the router actually won."""
    pts = []
    for (x0, y0, x1, y1) in segs:
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(math.ceil(d / (step_mm * 1e6))))
        for k in range(n + 1):
            t = k / float(n)
            pts.append((int(round(x0 + (x1 - x0) * t)),
                        int(round(y0 + (y1 - y0) * t))))
    return sorted(set(pts))


def chain_of(recs):
    """The two FREE ends of a same-net chain, in mm, or None.

    `route_maze_batch.chain_ends`' own test, mirrored: an endpoint shared by
    two members is an interior junction and exactly two may be unshared.  The
    applier re-runs it against the BOARD -- vias, pads and third branches
    included -- and stops the run by name if the chain is really a tee; this is
    the cheap half, so a plan that could never be applied is never written.
    """
    deg = {}
    for c in recs:
        for pt in (tuple(c["a_mm"]), tuple(c["b_mm"])):
            deg[pt] = deg.get(pt, 0) + 1
    free = sorted(p for p, n in deg.items() if n == 1)
    inner = [p for p, n in deg.items() if n != 1]
    if len(free) != 2 or any(deg[p] != 2 for p in inner):
        return None
    return free


def seg_record(L, s):
    return dict(net=s.net, lkey=L,
                a_mm=[round(s.x0 / 1e6, 4), round(s.y0 / 1e6, 4)],
                b_mm=[round(s.x1 / 1e6, 4), round(s.y1 / 1e6, 4)],
                width_mm=round(2 * s.hw / 1e6, 4),
                mm=round(math.hypot(s.x1 - s.x0, s.y1 - s.y0) / 1e6, 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--escape-limit", type=int, default=8)
    ap.add_argument("--lane-clearance-mm", type=float, default=0.0,
                    help="clearance a FOREIGN net owes the lane's outer edge, "
                         "on top of the lane's own half-width.  0 reads the "
                         "routed net's OWN netclass clearance off the board, "
                         "which is what the router would have enforced had the "
                         "lane been real copper")
    ap.add_argument("--step-mm", type=float, default=LANE_STEP_MM)
    ap.add_argument("--max-detour-ratio", type=float, default=3.0,
                    help="ENGINEERING bound: a relay longer than this many "
                         "times its own length is a reroute wearing a "
                         "detour's name (D-607 measured /NFC_5V_EN coming "
                         "back 8.6x).  The geometric ceiling -- down one side "
                         "of the lane, round an end and back -- is reported "
                         "beside it and the SMALLER of the two binds.  0 "
                         "disables the ratio and leaves only the geometry")
    ap.add_argument("--guard", type=Path,
                    help="an existing pour_bond_guard.py spec the relay must "
                         "also honour; its records are carried into --guard-out")
    ap.add_argument("--plan-out", type=Path,
                    help="write a route_maze_batch.py --detour-spec file")
    ap.add_argument("--guard-out", type=Path,
                    help="write the lane reservation as a --guard file")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, detour_layers,
                                  guard_for, load_guard)

    # HASH AT LOAD TIME.  Every verdict below belongs to THIS bytes-object;
    # stamping the file as it is when the report is written would attribute a
    # measurement to a board it was never made on.
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()

    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    # The layer NAME a `--detour-spec` must carry is the board's own, read off
    # the board -- never a table in this file.  `detour_apply` resolves a track
    # by that string and stops rather than guessing.
    LAYER_NAME = {k: qb.b.GetLayerName(v) for k, v in
                  (("F", pcbnew.F_Cu), ("I1", pcbnew.In1_Cu),
                   ("I2", pcbnew.In2_Cu), ("I3", pcbnew.In3_Cu),
                   ("I4", pcbnew.In4_Cu), ("B", pcbnew.B_Cu))}
    reserved = reserved_inner_planes(qb.b)
    base_guard = dict(load_guard(a.guard)) if a.guard else {"guards": []}
    base_guard.setdefault("guards", [])

    family = list(dict.fromkeys(a.nets))
    lane_pts, lane_mm, lane_keepout = [], 0.0, 0
    cut_objs, plan_nets, out_nets = [], [], []
    verdict_all = "OPEN"

    # THE LANE IS WON BEFORE ANYTHING IS PUT BACK, and it is kept, because the
    # applier routes every requested net on one board: the second net of a pair
    # must see the first net's copper or the reservation is a fiction.
    mark = qb.mark()
    for net in family:
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        qb._obs_cache = None
        field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=a.grid, layers=layers)
        islands = mz.net_islands(qb, net)
        rec = dict(net=net, netclass=c["netclass"], layers=list(layers),
                   width_mm=round(c["width"] / 1e6, 3),
                   clr_mm=round(c["clr"] / 1e6, 3),
                   islands=len(islands), edges=[])
        keep = (c["width"] / 2.0
                + (a.lane_clearance_mm * 1e6 if a.lane_clearance_mm
                   else c["clr"]))
        lane_keepout = max(lane_keepout, int(round(keep)))
        for (i, j) in mz.island_mst(islands):
            src, dst = islands[i], islands[j]
            base = mz.route_join(qb, field, src, dst, a.escape_limit,
                                 a.via_cost, emit=False)
            edge = dict(src=[p["ref"] for p in src],
                        dst=[p["ref"] for p in dst],
                        direct_mm=round(math.hypot(
                            *[u - v for u, v in zip(centre(src), centre(dst))])
                            / 1e6, 3),
                        baseline=dict(ok=bool(base.get("ok")),
                                      reason=base.get("reason"),
                                      mm=round(base.get("mm") or 0.0, 3),
                                      src_escapes=base.get("src_escapes"),
                                      dst_escapes=base.get("dst_escapes")))
            if base.get("ok"):
                edge["verdict"] = "OPEN"
                rec["edges"].append(edge)
                continue

            box = bbox([src, dst])
            objs = crossing_tracks(qb, layers, box, net)
            edge["window_mm"] = [round(v / 1e6, 3) for v in box]
            edge["crossing_tracks"] = len(objs)
            by = {}
            for (L, s) in objs:
                by[s.net] = by.get(s.net, 0) + 1
            edge["crossing_by_net"] = dict(sorted(by.items()))

            # ---- 1. SEGMENT upper bound ------------------------------- #
            with WithoutObjects(qb, field, {id(s) for (_L, s) in objs}):
                top = mz.route_join(qb, field, src, dst, a.escape_limit,
                                    a.via_cost, emit=False)
            edge["all_tracks_cut"] = dict(ok=bool(top.get("ok")),
                                          reason=top.get("reason"),
                                          mm=round(top.get("mm") or 0.0, 3))
            if not top.get("ok"):
                edge["verdict"] = "SEGMENT_WALL"
                edge["why"] = ("every crossing track on the permitted layers "
                               "held out and the corridor is still NO_PATH -- "
                               "no detour transaction of any size opens it")
                rec["edges"].append(edge)
                verdict_all = "SEGMENT_WALL"
                continue

            # ---- 2. MINIMAL ------------------------------------------- #
            cut, proof = minimal_tracks(qb, field, src, dst, objs,
                                        a.escape_limit, a.via_cost)
            edge["minimal"] = dict(
                tracks=len(cut), ok=bool(proof.get("ok")),
                mm=round(proof.get("mm") or 0.0, 3),
                objects=[seg_record(L, s) for (L, s) in cut])
            # ---- 2b. IRREDUCIBLE ------------------------------------- #
            # A minimal set is minimal with respect to single-object addition
            # and no more: it says nothing about whether some OTHER set of a
            # different shape would spare a net this one names.  For each net
            # in the cut, hold out every crossing track EXCEPT that net's and
            # ask the corridor again.  Still `NO_PATH` => no cut set of ANY
            # size that spares that net opens this corridor, which is a
            # materially stronger statement than "the minimal set includes it"
            # and it is the one a placement argument needs.
            irreducible = []
            for n2 in sorted({s.net for (_L, s) in cut}):
                spare = {id(s) for (_L, s) in objs if s.net != n2}
                with WithoutObjects(qb, field, spare):
                    r2 = mz.route_join(qb, field, src, dst, a.escape_limit,
                                       a.via_cost, emit=False)
                if not r2.get("ok"):
                    irreducible.append(n2)
            edge["irreducible_nets"] = irreducible
            edge["protected"] = sorted({s.net for (_L, s) in cut
                                        if PROTECTED.search(s.net or "")})
            if edge["protected"]:
                edge["verdict"] = "PROTECTED_COPPER"
                edge["why"] = ("the minimal cut set names copper "
                               "protected_copper.py forbids touching")
                rec["edges"].append(edge)
                verdict_all = "PROTECTED_COPPER"
                continue

            # ---- 3. THE LANE ------------------------------------------ #
            with WithoutObjects(qb, field, {id(s) for (_L, s) in cut}):
                before = {L: len(qb.shapes[L]) for L in qb.shapes}
                won = mz.route_join(qb, field, src, dst, a.escape_limit,
                                    a.via_cost, emit=True)
                laid, geo = [], []
                for L in qb.shapes:
                    for s in qb.shapes[L][before[L]:]:
                        if s.tag != "track":
                            continue
                        laid.append((L, s))
                        geo.append((s.x0, s.y0, s.x1, s.y1))
            # `WithoutObjects.__exit__` restores the shape lists it saved on
            # entry, so copper emitted inside it would vanish with them.  The
            # lane is therefore carried out by VALUE and re-laid on the outer
            # board, which is also what makes the second net of a pair see it.
            for (L, s) in laid:
                qb.shapes[L].append(s)
            qb._obs_cache = None
            edge["lane"] = dict(ok=bool(won.get("ok")),
                                mm=round(won.get("mm") or 0.0, 3),
                                vias=won.get("vias"),
                                segments=len(geo))
            if not won.get("ok"):
                edge["verdict"] = "LANE_LOST"
                rec["edges"].append(edge)
                verdict_all = "LANE_LOST"
                continue
            lane_mm += won.get("mm") or 0.0
            lane_pts += sample_lane(geo, a.step_mm)
            cut_objs += cut
            edge["verdict"] = "DETOURABLE"
            rec["edges"].append(edge)
        out_nets.append(rec)
    qb.revert(mark)
    qb._obs_cache = None

    # ---- 4. THE RELAY ------------------------------------------------- #
    lane_pts = sorted(set(lane_pts))
    lane_guard = {"F": [], "I1": [], "I2": [], "I3": [], "I4": [], "B": []}
    relay = dict(all_relaid=True, chains=[])
    if cut_objs:
        # The lane is reserved on the layers the FAMILY may route on and on no
        # others.  Reserving the whole stack would be a different, larger claim
        # -- `detour_guard`'s disc has to, because a barrel is copper on every
        # layer, but a lane is a track and a foreign net is free to pass under
        # it on a layer the family may not use.  A barrel dropped in the lane
        # is still refused, because its own via mask is taken on every layer it
        # spans and the reserved one is among them.
        famlayers = set()
        for net in family:
            c = net_contract(qb.b, net)
            famlayers |= set(permitted_layers(qb.routable, c["layers"],
                                              reserved, net))
        guards = list(base_guard["guards"])
        for lk in sorted(famlayers):
            guards.append(dict(ok=True, net=family[0], exempt=family[1:],
                               lkey=lk, keepout_radius=int(lane_keepout),
                               points=[[x, y] for (x, y) in lane_pts],
                               tube=LANE_LABEL))
        lane_guard = dict(base_guard)
        lane_guard["guards"] = guards
        lane_guard["schema"] = base_guard.get("schema", 1)

        by_net = {}
        for (L, s) in cut_objs:
            by_net.setdefault(s.net, []).append(seg_record(L, s))
        # A LANE IS NOT A DISC.  D-607 bounds a pocket detour by the
        # circumference of the disc it walks around; the longest a genuine
        # detour past a LANE can be is down one side, around an end and back.
        rmax = lane_keepout / 1e6
        perim = 2.0 * (lane_mm + 2.0 * math.pi * rmax)
        from screen_segment_evict import Held
        with Held(qb, None, cut_objs):
            m = qb.mark()
            for net in sorted(by_net):
                recs = by_net[net]
                lkeys = {r["lkey"] for r in recs}
                widths = {r["width_mm"] for r in recs}
                con = net_contract(qb.b, net)
                permitted = permitted_layers(qb.routable, con["layers"],
                                             reserved, net)
                was = sum(r["mm"] for r in recs)
                geo_max = was + perim
                eng_max = (was * a.max_detour_ratio if a.max_detour_ratio
                           else geo_max)
                ch = dict(net=net, tracks=len(recs), was_mm=round(was, 4),
                          geometric_max_mm=round(geo_max, 4),
                          ratio_max_mm=round(eng_max, 4),
                          max_mm=round(geo_max, 4),
                          layer=sorted(lkeys),
                          objects=recs)
                if len(lkeys) != 1 or len(widths) != 1:
                    ch.update(ok=False, reason="NOT_A_CHAIN",
                              why="a chain must be ONE layer and ONE width")
                    relay["chains"].append(ch)
                    relay["all_relaid"] = False
                    continue
                lkey = sorted(lkeys)[0]
                layers, spent = detour_layers(permitted, lkey, False)
                ch.update(layers_allowed=list(layers), own_layer=spent)
                if lkey not in layers:
                    ch.update(ok=False, reason="UNDETOURABLE_LAYER",
                              why="layer %s is not in this net's contract %s "
                                  "-- the track can be cut and can never be "
                                  "put back" % (lkey, list(layers)))
                    relay["chains"].append(ch)
                    relay["all_relaid"] = False
                    continue
                ends = chain_of(recs)
                if ends is None:
                    ch.update(ok=False, reason="NOT_A_CHAIN",
                              why="the cut tracks of this net do not form a "
                                  "simple chain with exactly two free ends")
                    relay["chains"].append(ch)
                    relay["all_relaid"] = False
                    continue
                g = guard_for(lane_guard, net)
                qb._obs_cache = None
                field = mz.Field(qb, net, int(round(sorted(widths)[0] * 1e6)),
                                 con["clr_pad"], con["clr"], con["via_dia"],
                                 con["via_drill"], G=a.grid, layers=layers,
                                 guard=g)
                a_nm = tuple(int(round(v * 1e6)) for v in ends[0])
                b_nm = tuple(int(round(v * 1e6)) for v in ends[1])
                # A REJECTED RELAY LEAVES NO COPPER BEHIND.  `route_points`
                # emits before this loop can judge it, and the applier lays
                # each detour on a board that already carries the previous
                # one -- so a 42 mm reroute this screen is about to refuse must
                # not be an obstacle to the chain measured after it.  Measured:
                # `/SD_CS_N` reads 13.211 mm / 0 vias without the refused
                # `/I2S_LRCLK` copper in the way and 16.012 mm / 2 vias with it.
                cmark = qb.mark()
                # SEARCH AT THE GEOMETRY, JUDGE AT THE RATIO.  D-617 measured
                # that `max_mm` is ALSO the wavefront budget -- a chain that
                # refused `NO_PATH` at 62 mm routed at 49.505 mm once the
                # budget was opened -- and a via costs `via_cost_mm` of that
                # budget before it buys any distance.  Strangling the search
                # with the engineering bound therefore reports NO_PATH for
                # routes that exist: `Net-(J3-CC1)` relays in 2.359 mm with two
                # barrels and refuses inside a 3.924 mm budget.  Bound the
                # length, not the search.
                r = mz.route_points(qb, field, a_nm, b_nm, lkey,
                                    via_cost_mm=a.via_cost, emit=True,
                                    max_mm=ch["max_mm"])
                if r.get("ok") and eng_max and (r.get("mm") or 0.0) > eng_max:
                    r = dict(ok=False, reason="REROUTE_NOT_DETOUR",
                             why="relaid %.4f mm against %.4f mm of its own "
                                 "copper -- past the %.2fx bound; that is a "
                                 "reroute, not a detour"
                                 % (r.get("mm"), was, a.max_detour_ratio),
                             mm=r.get("mm"), vias=r.get("vias"),
                             mm_by_layer=r.get("mm_by_layer"))
                if not r.get("ok"):
                    qb.revert(cmark)
                    qb._obs_cache = None
                ch.update(ok=bool(r.get("ok")), reason=r.get("reason"),
                          why=str(r.get("why"))[:220] if r.get("why") else None,
                          mm=r.get("mm"), vias=r.get("vias"),
                          mm_by_layer=r.get("mm_by_layer"),
                          a_mm=list(ends[0]), b_mm=list(ends[1]))
                relay["all_relaid"] = relay["all_relaid"] and bool(r.get("ok"))
                relay["chains"].append(ch)
            qb.revert(m)
        if not relay["all_relaid"]:
            verdict_all = "UNRELAYABLE"
        elif verdict_all == "OPEN":
            verdict_all = "DETOURABLE"

    doc = dict(schema=1, board=str(a.board), board_sha256=board_sha,
               grid=a.grid, family=family,
               lane=dict(mm=round(lane_mm, 4), points=len(lane_pts),
                         keepout_nm=lane_keepout, label=LANE_LABEL),
               verdict=verdict_all, nets=out_nets, relay=relay)

    if a.plan_out and relay["chains"] and relay["all_relaid"]:
        plan = dict(schema=1,
                    note=("corridor segment eviction: the crossing tracks the "
                          "%s corridor needs moved, each laid again between "
                          "its own two ends around the lane "
                          "screen_corridor_detour.py measured.  Written "
                          "straight from the measurement so the two cannot "
                          "drift apart." % ", ".join(family)),
                    reserve=[], detours=[])
        for ch in relay["chains"]:
            plan["detours"].append(dict(
                net=ch["net"], max_mm=ch["max_mm"],
                why=("crosses the reserved %s lane; relaid %.4f -> %.4f mm, "
                     "%d via(s), inside the %.4f mm bound"
                     % (LANE_LABEL, ch["was_mm"], ch["mm"] or 0.0,
                        ch.get("vias") or 0, ch["max_mm"])),
                tracks=[dict(layer=LAYER_NAME[o["lkey"]],
                             a_mm=o["a_mm"], b_mm=o["b_mm"],
                             width_mm=o["width_mm"])
                        for o in ch["objects"]]))
        a.plan_out.write_text(json.dumps(plan, indent=1, sort_keys=True) + "\n",
                              encoding="utf-8")
        doc["plan_out"] = str(a.plan_out)
    if a.guard_out and lane_pts:
        a.guard_out.write_text(
            json.dumps(lane_guard, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
        doc["guard_out"] = str(a.guard_out)

    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
