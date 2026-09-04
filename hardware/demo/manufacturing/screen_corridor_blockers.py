#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: for a `NO_PATH` net, WHOSE copper is the wall?

`screen_enclosed_pads.py` answers the TERMINAL question -- can this pad launch
at all -- and runs a deletion experiment when it cannot.  That screen is blind
to the other half of the failure space, and on this board it is now the bigger
half: a net whose pads all launch fine and whose islands still cannot see each
other.  `route_join` reports that as `NO_PATH` with a src/dst escape count, and
nothing in the repository says which copper is standing in the corridor.

The USB pair is the case that forced this.  On the single `F.Cu` layer its own
`.kicad_dru` reserves for it -- section 6, "USB 2.0 - FULL SPEED, ON F.Cu OVER
In1, NO VIAS, NO THEATRE" -- all four nets return `NO_PATH` with 4-11 legal
escapes on both sides, and the two intra-connector joins (`J3.A6`->`J3.B6`,
`J3.A7`->`J3.B7`) route on F alone in under 2 mm.  The terminals are fine.  The
corridor is full.  It is full of copper THIS PROJECT laid later, by whole-board
maze batches that had no way to know a layer was spoken for.

So this screen asks the corridor question with the same discipline the pad
screen uses:

  * it removes only ROUTED copper -- tracks and vias.  A pad is where a part is
    soldered; pretending one is absent reports an opening no rip-up can deliver.
  * it removes only copper lying WHOLLY INSIDE the corridor window, because that
    is the only copper an eviction transaction is allowed to take, and a track
    cannot be evicted piecewise.  "Rip up GND" here means the eight ground
    segments boxed in with the USB connector, never the ground net.
  * it uses the SAME `route_join` the router uses, at the net's own contract,
    in `emit=False` mode, so a corridor it calls open is one the real proposer
    would actually take.
  * it opens the board read-only and never writes it.  Every deletion is on the
    in-memory obstacle model and is restored in a `finally`.

Four questions, in escalating cost, and the verdict is whichever answers first:

  1. UPPER BOUND.  Drop EVERY foreign net's routed copper in the corridor at
     once.  Still `NO_PATH` => no CONTAINMENT-BOUNDED rip-up on these layers
     can open it, and the expensive per-net sweep is skipped.

  1b. UNBOUNDED UPPER BOUND -- asked only when 1 fails, and asked because the
     first cut of this screen got it wrong.  A containment window deliberately
     leaves a track that merely CROSSES it in place, so "1 failed" does NOT
     mean the wall is geometry: it can equally be a crossing track no
     containment-bounded transaction may take.  Question 1b therefore strips
     EVERY routed object on the permitted layers, board-wide, which is a
     diagnosis and not an executable transaction.  Still `NO_PATH` => the wall
     really is pads/placement/keep-out, reported `PLACEMENT_WALL`.  Opens =>
     `CROSSING_COPPER_WALL`: copper, but not copper this eviction contract can
     reach.  On this board that distinction is not academic -- the USB MCU-side
     pair reads `PLACEMENT_WALL` under question 1 and routes in 28.645 mm /
     32.011 mm under 1b.
  2. SINGLE.  One foreign net at a time.  Any that opens the corridor alone is
     the cheapest possible rip-up and is reported with the resulting run length.
  3. SET.  If none opens it alone, accumulate greedily -- keep the net that
     most reduces the blocked cell count along the straight corridor -- until
     the corridor opens or the candidates run out.

Only `RIPUP_SINGLE` and `RIPUP_SET` name a transaction.  `CROSSING_COPPER_WALL`
and `PLACEMENT_WALL` are both refusals; they differ in what would have to
change next -- a whole-net reroute or a refloorplan for the first, placement or
a layer contract for the second -- and reporting one as the other sends the
next iteration down the wrong road.

Nothing here promotes copper.  Its output is the input to a rip-up-and-reroute
transaction, which is an ordinary gated `route_maze_batch.py` run: the ripped
nets are re-proposed on the layers they should have used, and the authoritative
gate judges the whole thing on the usual no-net-regressed / DRC / preservation
clauses.
"""

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

MARGIN = 3000000        # nm: how far outside the island bbox still counts
ROUTED = ("track", "via")

# Question 1b's window: the whole plane, so containment never excludes anything.
# It exists to be DELIBERATELY unexecutable -- see the module docstring.
UNBOUNDED = (-10 ** 12, -10 ** 12, 10 ** 12, 10 ** 12)


def corridor_nets(qb, layers, box, mynet):
    """Foreign nets with EVICTABLE routed copper inside `box` on `layers`.

    `box` is the two islands' joint bounding box grown by `MARGIN`, and an
    object counts only if it lies WHOLLY inside it -- the same containment test
    `Without` removes by, so the tally a verdict reports is the tally a rip-up
    transaction would actually have to execute.  A net whose copper is nowhere
    near the corridor cannot be the wall, and testing it costs a full lattice
    rebuild, so the window is also what keeps this screen affordable.
    """
    x0, y0, x1, y1 = box
    out = {}
    for L in layers:
        for s in qb.shapes[L]:
            if s.net in (None, mynet) or s.tag not in ROUTED:
                continue
            a, b, c, d = s.bbox(0)
            if a < x0 or b < y0 or c > x1 or d > y1:
                continue
            rec = out.setdefault(s.net, dict(track=0, via=0, layers=set()))
            rec[s.tag] += 1
            rec["layers"].add(L)
    return out


class Without(object):
    """Context manager: this net-set's ROUTED copper INSIDE `box` is not there.

    The window is not a speed trick, it is the ANSWER'S UNITS.  A screen that
    silently dropped a net's copper board-wide would report "rip up GND" when
    what it actually measured was "delete every ground track on the board",
    which is not a transaction anybody can execute and not a verdict clause 5 of
    `route_maze_batch.py` would ever accept.  The eviction contract that
    consumes this report is explicit -- a removal is legal only for an object
    that "lies wholly inside the corridor the requested nets themselves define"
    -- so this screen removes exactly that set and nothing else: a routed object
    whose own bounding box is contained in `box`.

    A track that merely CROSSES the window is left in place.  It cannot be
    evicted piecewise, so pretending it is absent would report an opening no
    rip-up can deliver -- the same mistake `screen_enclosed_pads.py` refuses to
    make about pads.

    Restores the shape lists, the hole list, the obstacle cache, the blocked
    grids and -- when more than one layer is in play, so a via move exists --
    the via-legality grid.  A screen that left any of those perturbed would
    poison every later question it asks.
    """

    def __init__(self, qb, field, nets, box):
        self.qb, self.field, self.nets = qb, field, set(nets)
        self.box = box

    def _evictable(self, o):
        x0, y0, x1, y1 = self.box
        a, b, c, d = o.bbox(0)
        return a >= x0 and b >= y0 and c <= x1 and d <= y1

    def __enter__(self):
        qb = self.qb
        self.shapes = {L: qb.shapes[L] for L in qb.shapes}
        self.holes = qb.holes
        for L in qb.shapes:
            qb.shapes[L] = [s for s in qb.shapes[L]
                            if not (s.net in self.nets and s.tag in ROUTED
                                    and self._evictable(s))]
        qb.holes = [h for h in qb.holes
                    if not (h.net in self.nets and h.tag.startswith("via")
                            and self._evictable(h))]
        self._refresh()
        return self

    def __exit__(self, *exc):
        self.qb.shapes.update(self.shapes)
        self.qb.holes = self.holes
        self._refresh()
        return False

    def _refresh(self):
        self.qb._obs_cache = None
        self.field.rebuild_blk()
        if len(self.field.layers) > 1:
            self.field.via_ok = self.field._via_grid()


class WithoutObjects(object):
    """Context manager: exactly THESE routed objects are not there.

    `Without` removes by NET inside a window, which is the unit a report can be
    written in but not the unit a transaction has to execute in.  The eviction
    contract in `route_maze_batch.py` licenses a removal per OBJECT SIGNATURE,
    so the minimal-set search below has to be able to hold an arbitrary subset
    of objects out -- including one that is not a whole net.
    """

    def __init__(self, qb, field, keep_out):
        self.qb, self.field = qb, field
        self.out = set(keep_out)

    def __enter__(self):
        qb = self.qb
        self.shapes = {L: qb.shapes[L] for L in qb.shapes}
        self.holes = qb.holes
        for L in qb.shapes:
            qb.shapes[L] = [s for s in qb.shapes[L] if id(s) not in self.out]
        qb.holes = [h for h in qb.holes if id(h) not in self.out]
        self._refresh()
        return self

    def __exit__(self, *exc):
        self.qb.shapes.update(self.shapes)
        self.qb.holes = self.holes
        self._refresh()
        return False

    def _refresh(self):
        self.qb._obs_cache = None
        self.field.rebuild_blk()
        if len(self.field.layers) > 1:
            self.field.via_ok = self.field._via_grid()


def corridor_objects(qb, layers, box, mynet, nets):
    """Every evictable routed object of `nets` inside `box`, plus its hole."""
    out = []
    for L in layers:
        for s in qb.shapes[L]:
            if s.net not in nets or s.tag not in ROUTED:
                continue
            a, b, c, d = s.bbox(0)
            if a < box[0] or b < box[1] or c > box[2] or d > box[3]:
                continue
            out.append(s)
    for h in qb.holes:
        if h.net not in nets or not h.tag.startswith("via"):
            continue
        a, b, c, d = h.bbox(0)
        if a < box[0] or b < box[1] or c > box[2] or d > box[3]:
            continue
        out.append(h)
    return out


def minimal_eviction(qb, field, src, dst, objs, escape_limit, via_cost_mm):
    """The SMALLEST subset of `objs` whose absence opens the corridor.

    Reverse-greedy delta debugging: start from "all of them gone", which
    question 1 already proved opens the corridor, then try to PUT EACH ONE BACK
    and keep it back whenever the corridor survives.  What remains is minimal
    with respect to single-object addition -- every object still in the set is
    one whose return closes the corridor again -- which is the property that
    matters, because it is what makes the answer an argument rather than a
    list: you cannot evict less than this and still route.

    It is not guaranteed globally minimum (that is set cover, and this corridor
    has ten candidates, not a search space).  It is guaranteed HONEST: the
    reported set is re-proved open at the end, on the real `route_join`.
    """
    import maze3d as mz          # main() imports lazily; so does this helper
    keep = {id(o) for o in objs}
    for o in objs:
        trial = keep - {id(o)}
        with WithoutObjects(qb, field, trial):
            r = mz.route_join(qb, field, src, dst, escape_limit, via_cost_mm,
                              emit=False)
        if r.get("ok"):
            keep = trial
    with WithoutObjects(qb, field, keep):
        final = mz.route_join(qb, field, src, dst, escape_limit, via_cost_mm,
                              emit=False)
    return [o for o in objs if id(o) in keep], final


def blocked_along(field, a, b, samples=400):
    """How many sample points on the straight line a->b sit on blocked cells.

    A cheap, monotone ranking signal for the greedy accumulation in question 3.
    It is NOT a legality test -- `route_join` remains the only authority on
    whether a corridor is open -- it only decides which net to try dropping
    next, so an approximation here costs nothing but search order.
    """
    n = 0
    for t in range(samples + 1):
        f = t / float(samples)
        x = a[0] + (b[0] - a[0]) * f
        y = a[1] + (b[1] - a[1]) * f
        i, j = field.cell(x, y)
        if not field.inside(i, j):
            continue
        if all(field.blk[L][j, i] for L in field.layers):
            n += 1
    return n


def centre(island):
    return (sum(p["x"] for p in island) / float(len(island)),
            sum(p["y"] for p in island) / float(len(island)))


def bbox(islands, margin=MARGIN):
    xs = [p["x"] for g in islands for p in g]
    ys = [p["y"] for g in islands for p in g]
    return (min(xs) - margin, min(ys) - margin,
            max(xs) + margin, max(ys) + margin)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--escape-limit", type=int, default=8)
    ap.add_argument("--max-set", type=int, default=6,
                    help="greedy accumulation depth for question 3")
    ap.add_argument("--no-minimal", action="store_true",
                    help="skip the per-object minimal-eviction search that "
                         "runs when a single net's rip-up opens a corridor")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes)

    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)

    out_nets = []
    for net in a.nets:
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        field = mz.Field(qb, net, c["width"], c["clr"], c["clr"],
                         c["via_dia"], c["via_drill"], G=a.grid, layers=layers)
        islands = mz.net_islands(qb, net)
        rec = dict(net=net, netclass=c["netclass"], layers=list(layers),
                   width_mm=round(c["width"] / 1e6, 3),
                   clr_mm=round(c["clr"] / 1e6, 3),
                   islands=len(islands), edges=[])
        for (i, j) in mz.island_mst(islands):
            src, dst = islands[i], islands[j]
            base = mz.route_join(qb, field, src, dst, a.escape_limit,
                                 a.via_cost, emit=False)
            edge = dict(
                src=[p["ref"] for p in src], dst=[p["ref"] for p in dst],
                direct_mm=round(math.hypot(*[u - v for u, v in
                                             zip(centre(src), centre(dst))])
                                / 1e6, 3),
                baseline=dict(ok=bool(base.get("ok")),
                              reason=base.get("reason"),
                              mm=round(base.get("mm", 0.0), 3),
                              src_escapes=base.get("src_escapes"),
                              dst_escapes=base.get("dst_escapes")))
            if base.get("ok"):
                edge["verdict"] = "OPEN"
                rec["edges"].append(edge)
                continue

            box = bbox([src, dst])
            cand = corridor_nets(qb, layers, box, net)
            edge["corridor_nets"] = {
                k: dict(tracks=v["track"], vias=v["via"],
                        layers=sorted(v["layers"]))
                for k, v in sorted(cand.items())}

            # ---- 1. upper bound ------------------------------------------ #
            with Without(qb, field, cand.keys(), box):
                top = mz.route_join(qb, field, src, dst, a.escape_limit,
                                    a.via_cost, emit=False)
            edge["all_removed"] = dict(ok=bool(top.get("ok")),
                                       reason=top.get("reason"),
                                       mm=round(top.get("mm", 0.0), 3),
                                       nets_removed=len(cand))
            if not top.get("ok"):
                # ---- 1b. unbounded upper bound -- DIAGNOSIS ONLY ---------- #
                # Every routed object on the permitted layers, board-wide.  No
                # transaction may do this; the answer only classifies the wall.
                everywhere = {s.net for L in layers for s in qb.shapes[L]
                              if s.net not in (None, net) and s.tag in ROUTED}
                with Without(qb, field, everywhere, UNBOUNDED):
                    free = mz.route_join(qb, field, src, dst, a.escape_limit,
                                         a.via_cost, emit=False)
                edge["board_wide_stripped"] = dict(
                    ok=bool(free.get("ok")), reason=free.get("reason"),
                    mm=round(free.get("mm", 0.0), 3),
                    nets_stripped=len(everywhere), executable=False)
                edge["verdict"] = ("CROSSING_COPPER_WALL" if free.get("ok")
                                   else "PLACEMENT_WALL")
                rec["edges"].append(edge)
                print("  %-44s %s" % (net, edge["verdict"]),
                      file=sys.stderr, flush=True)
                continue

            # ---- 2. single ------------------------------------------------ #
            singles = []
            for fn in sorted(cand):
                with Without(qb, field, [fn], box):
                    r = mz.route_join(qb, field, src, dst, a.escape_limit,
                                      a.via_cost, emit=False)
                if r.get("ok"):
                    singles.append(dict(rip_up_net=fn,
                                        mm=round(r.get("mm", 0.0), 3),
                                        tracks=cand[fn]["track"],
                                        vias=cand[fn]["via"]))
            edge["single_openers"] = sorted(singles, key=lambda d: d["mm"])
            if singles:
                edge["verdict"] = "RIPUP_SINGLE"
                # NAME THE OBJECTS, not just the net.  "rip up GND" is not a
                # transaction; `route_maze_batch.py --evict` licenses removals
                # per object signature and clause 4 then makes the evicted net
                # earn its place back, so the number that decides whether the
                # trade is worth making is how FEW objects have to move.
                if not a.no_minimal:
                    cheapest = singles[0]["rip_up_net"]
                    objs = corridor_objects(qb, layers, box, net, {cheapest})
                    least, proof = minimal_eviction(
                        qb, field, src, dst, objs, a.escape_limit, a.via_cost)
                    edge["minimal_eviction"] = dict(
                        net=cheapest, candidates=len(objs), objects=len(least),
                        bbox_mm=[[round(v / 1e6, 3) for v in o.bbox(0)]
                                 for o in least],
                        tags=[o.tag for o in least],
                        reproved_ok=bool(proof.get("ok")),
                        mm=round(proof.get("mm", 0.0), 3))
                rec["edges"].append(edge)
                print("  %-44s RIPUP_SINGLE %s" % (net, singles[0]["rip_up_net"]),
                      file=sys.stderr, flush=True)
                continue

            # ---- 3. greedy set -------------------------------------------- #
            sa, sb = centre(src), centre(dst)
            chosen, rest, opened = [], sorted(cand), None
            while rest and len(chosen) < a.max_set:
                scored = []
                for fn in rest:
                    with Without(qb, field, chosen + [fn], box):
                        scored.append((blocked_along(field, sa, sb), fn))
                scored.sort()
                chosen.append(scored[0][1])
                rest.remove(scored[0][1])
                with Without(qb, field, chosen, box):
                    r = mz.route_join(qb, field, src, dst, a.escape_limit,
                                      a.via_cost, emit=False)
                if r.get("ok"):
                    opened = dict(rip_up_nets=list(chosen),
                                  mm=round(r.get("mm", 0.0), 3))
                    break
            edge["set_opener"] = opened
            edge["verdict"] = "RIPUP_SET" if opened else "NO_OPENER_FOUND"
            print("  %-44s %s" % (net, edge["verdict"]),
                  file=sys.stderr, flush=True)
            rec["edges"].append(edge)
        out_nets.append(rec)

    verdicts = {}
    for r in out_nets:
        for e in r["edges"]:
            verdicts[e["verdict"]] = verdicts.get(e["verdict"], 0) + 1
    doc = dict(schema=1, board=str(a.board),
               board_sha256=__import__("hashlib").sha256(
                   a.board.read_bytes()).hexdigest(),
               grid=a.grid, summary=dict(verdicts=verdicts), nets=out_nets)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
