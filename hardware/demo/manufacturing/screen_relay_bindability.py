#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: WHAT IS A `--detour-spec`'s RESERVATION WORTH?

D-674.  A `--detour-spec` transaction has two halves that must BOTH hold:

  1. the named objects come OUT, and the pour, the corridor or the land the
     transaction is for is freed by their absence;
  2. the objects go BACK somewhere else, and a stated LANE keeps them out of
     the copper the removal freed -- because a relay is asked to put a track
     back between its OWN TWO FIXED ENDS, and absent a reservation the cheapest
     path between two fixed ends is the one the track was already on.

Nothing in this repository measured (2) before a router run.  D-663 emitted the
`C27.1 = U12.1` spec and called it *"the next transaction"*.  D-673 ran it for
the first time, nine decisions late, with the lane thinned to the stations at
least 0.60 mm from every detour's own terminal, and got `every_detour_relaid`
true and `pour_partition` false -- eight relays, no improvement.  D-674 ran it
again with the FULL lane and two of the eight came back `NO_PATH`.  Both runs
cost minutes; both answers were available in milliseconds from the spec alone.

THE ARITHMETIC.  D-667 lifts the reservation off a relay's own two ends,
because a lane that forbids them forbids the only two cells the relay may
finish on.  The lift is exactly the guard's own reach:

    reach  =  keepout + width/2 + G

so a straight relay of length `L` whose two ends are both inside the lane has

    bindable  =  max(0, L - 2 * reach)

millimetres of itself that the reservation can actually displace.  **When
`bindable` is zero the relay is GUARANTEED to return to its original geometry**
-- the lane has no cell of it left to forbid -- and the transaction is vacuous
for that object however the lane is drawn.  At this board's usual figures
(keepout 0.300 mm, width 0.200 mm, G 0.050 mm) the threshold is **0.900 mm**,
and five of the eight objects in the `C27.1` pocket are 0.100, 0.212, 0.600,
0.800 and 1.200 mm long.

`bindable` > 0 is NECESSARY and not sufficient: a bindable relay may still take
a path that crosses the freed copper elsewhere, and the router still has to
find one at all.  This screen refuses nothing and licenses nothing.  It says
which objects a lane CANNOT move, so a spec is repaired before a run, not
after.  Nothing is written and no board is loaded.
"""
import argparse
import json
import math
import sys
from pathlib import Path

DEFAULT_GRID_NM = 50000


def reach_nm(keepout_nm, width_nm, grid_nm):
    """`_guard_masks`' own formula, and `terminal_lift` uses the same one."""
    return keepout_nm + width_nm / 2.0 + grid_nm


def covering(pts, x, y, width_nm, grid_nm):
    """The guard points whose disc reaches (x, y), and the widest keepout."""
    cov = [k for (px, py, k) in pts
           if math.hypot(px - x, py - y) < reach_nm(k, width_nm, grid_nm)]
    return cov


def lane_points(spec, lkey):
    """The reserve discs that bind this layer, as (x_nm, y_nm, keepout_nm)."""
    out = []
    for d in spec.get("reserve", ()):
        if lkey not in d.get("layers", ("F", "I1", "I2", "I3", "I4", "B")):
            continue
        out.append((d["x_mm"] * 1e6, d["y_mm"] * 1e6, d["r_mm"] * 1e6))
    return out


LKEY = {"F.Cu": "F", "B.Cu": "B", "In1.Cu": "I1", "In2.Cu": "I2",
        "In3.Cu": "I3", "In4.Cu": "I4"}


def chain_ends_mm(parts):
    """The two FREE ends of a same-net chain, in mm, or None if it is not one.

    The same rule `route_maze_batch.chain_ends` and
    `screen_segment_evict.chain_ends_mm` apply -- an endpoint shared by two
    members is an interior junction and exactly two may be unshared -- restated
    here on PLAN records so this screen stays what it says it is: an answer
    read off the SPEC, with no board loaded and nothing imported from the
    router.
    """
    seen = {}
    for c in parts:
        for pt in (tuple(c["a_mm"]), tuple(c["b_mm"])):
            seen[pt] = seen.get(pt, 0) + 1
    free = sorted(pt for pt, n in seen.items() if n == 1)
    return (free[0], free[1]) if len(free) == 2 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=Path,
                    help="a route_maze_batch.py --detour-spec file, with its "
                         "`reserve` list -- the same file the run is given")
    ap.add_argument("--grid", type=int, default=DEFAULT_GRID_NM,
                    help="the lattice pitch the run will use, in nm.  The lift "
                         "is one cell wider than the guard, so a coarser "
                         "lattice frees MORE of the relay (default 50000)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    spec = json.loads(a.spec.read_text(encoding="utf-8"))
    rows, vacuous, unbound = [], 0, 0
    for i, d in enumerate(spec.get("detours", ())):
        if "barrel" in d:
            rows.append(dict(index=i, net=d["net"], kind="barrel",
                             at_mm=d["barrel"]["at_mm"],
                             verdict="BARREL_NOT_RELAID",
                             why="a barrel is always `relay: false`; the gate's "
                                 "rebond_priced clause prices it and no lane "
                                 "can move it"))
            continue
        # A DETOUR MAY BE A CHAIN, AND UNTIL D-675 THIS SCREEN COULD NOT READ
        # ONE.  `screen_relay_transaction.py --plan-out` emits `tracks: [...]`
        # whenever a land's cut is more than one segment -- which is the shape
        # of `+3V3 R39.1`, the board's best candidate -- and `d["a_mm"]` then
        # raises `KeyError` and takes the whole screen down.  D-674 closed with
        # *"run this before ANY --detour-spec gate run"*; on the very next
        # transaction it could not run at all.
        #
        # `route_maze_batch.detour_apply` removes a chain WHOLE and re-lays it
        # between the chain's two FREE ends (`chain_ends`), so those two points
        # are the relay's fixed terminals and the reservation is judged against
        # them.  `L` is the STRAIGHT-LINE distance between them, not the sum of
        # the segments: the bound this screen states is on what a lane can
        # displace, and a relay whose terminals are 1.0 mm apart has 1.0 mm of
        # freedom however many bends the old copper had.  The polyline length
        # is reported beside it so a reader can see the difference.
        parts = d.get("tracks") or [d]
        lkey = LKEY.get(parts[0].get("layer", d.get("layer", "")),
                        d.get("lkey"))
        w = int(round(parts[0].get("width_mm", d.get("width_mm", 0.2)) * 1e6))
        ends = chain_ends_mm(parts)
        if ends is None:
            rows.append(dict(index=i, net=d["net"], kind="chain",
                             tracks=len(parts), verdict="NOT_A_CHAIN",
                             why="the %d named segments do not form one chain "
                                 "with exactly two free ends, so this screen "
                                 "cannot name the relay's fixed terminals"
                                 % len(parts)))
            continue
        (a_mm, b_mm) = ends
        ax, ay = (v * 1e6 for v in a_mm)
        bx, by = (v * 1e6 for v in b_mm)
        L = math.hypot(bx - ax, by - ay)
        polyline_mm = round(sum(
            math.hypot(t["b_mm"][0] - t["a_mm"][0],
                       t["b_mm"][1] - t["a_mm"][1]) for t in parts), 4)
        pts = lane_points(spec, lkey)
        ca = covering(pts, ax, ay, w, a.grid)
        cb = covering(pts, bx, by, w, a.grid)
        ra = reach_nm(max(ca), w, a.grid) if ca else 0.0
        rb = reach_nm(max(cb), w, a.grid) if cb else 0.0
        # HOW MUCH OF THE LANE TOUCHES THIS RELAY AT ALL.  A track no disc
        # reaches is not bound either -- but for the opposite reason, and a
        # reader must be able to tell the two apart.
        near = min([math.hypot(px - (ax + bx) / 2.0, py - (ay + by) / 2.0)
                    for (px, py, _k) in pts] or [float("inf")])
        bindable = max(0.0, L - ra - rb)
        if not ca and not cb and near > L / 2.0 + max(
                [reach_nm(k, w, a.grid) for (_x, _y, k) in pts] or [0.0]):
            verdict, why = "LANE_DOES_NOT_REACH", (
                "no reserve disc reaches either end or the middle of this "
                "relay; the lane cannot move it and does not need to")
            unbound += 1
        elif bindable <= 0.0:
            verdict, why = "VACUOUS_TERMINAL_LIFT", (
                "the relay is %.3f mm long and its own two D-667 terminal "
                "lifts free %.3f mm of it, so NOTHING of it is reserved and it "
                "is guaranteed to be re-laid on its original geometry"
                % (L / 1e6, (ra + rb) / 1e6))
            vacuous += 1
        else:
            verdict, why = "BINDABLE", (
                "%.3f mm of this relay's %.3f mm lies outside both terminal "
                "lifts, so the lane has something of it to forbid"
                % (bindable / 1e6, L / 1e6))
        rows.append(dict(
            index=i, net=d["net"],
            kind=("chain" if len(parts) > 1 else "track"),
            tracks=len(parts), polyline_mm=polyline_mm,
            layer=parts[0].get("layer", d.get("layer")),
            lkey=lkey, a_mm=list(a_mm), b_mm=list(b_mm),
            width_mm=round(w / 1e6, 4), length_mm=round(L / 1e6, 4),
            lift_a_mm=round(ra / 1e6, 4), lift_b_mm=round(rb / 1e6, 4),
            bindable_mm=round(bindable / 1e6, 4),
            threshold_mm=round((ra + rb) / 1e6, 4),
            lane_points_on_layer=len(pts),
            nearest_disc_to_midpoint_mm=(None if near == float("inf")
                                         else round(near / 1e6, 4)),
            verdict=verdict, why=why))

    doc = dict(
        schema=1, spec=str(a.spec), grid_nm=a.grid,
        question=("how much of each --detour-spec relay does its own stated "
                  "lane actually bind, once D-667's terminal lift has freed "
                  "the relay's two fixed ends"),
        formula="reach = keepout + width/2 + G;  bindable = max(0, L - reach_a - reach_b)",
        detours=len(rows), reserve_discs=len(spec.get("reserve", ())),
        vacuous=vacuous, lane_does_not_reach=unbound,
        verdict=("THE LANE CANNOT BIND %d OF %d RELAYS -- the transaction is "
                 "vacuous for them however it is drawn" % (vacuous, len(rows)))
        if vacuous else "every relay this lane reaches has copper it can bind",
        rows=rows)
    text = json.dumps(doc, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for r in rows:
        print("  %-28s %-9s %8s mm  bindable %8s  %s"
              % (r["net"], r.get("kind"),
                 r.get("length_mm", "-"), r.get("bindable_mm", "-"),
                 r["verdict"]), file=sys.stderr)
    print("  %d of %d relays VACUOUS_TERMINAL_LIFT at grid %.3f mm"
          % (vacuous, len(rows), a.grid / 1e6), file=sys.stderr)
    if not a.out:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
