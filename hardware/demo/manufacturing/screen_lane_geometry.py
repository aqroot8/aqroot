#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: is there a RESERVATION GEOMETRY that both BINDS a
segment detour's relay and ADMITS it?

D-670.  `--detour-spec` moves one named chain out of a pocket and `reserve`
keeps it from coming straight back.  Two arms of D-670 spent gate runs finding
out that the obvious reservation -- a disc centred on the LAND whose pocket is
being freed -- cannot work:

    THE COPPER THAT SEALS A POCKET ENDS BESIDE IT.  That is WHY it seals it.  So
    a fixed terminal of the displaced chain is always close to the land, always
    inside the guard's `keepout + width/2 + G` reach, and `terminal_lift` --
    which is correct, and which a relay cannot route without -- then frees a
    disc centred `offset` off the guard point.  The reservation retains
    `keepout - offset` on the side that matters and NOTHING on the other.

    D-670 arm L:      keepout 2.200 mm, offset 2.128 mm -> residual 0.072 mm.
                      Relay came back 6.0177 -> 6.0187 mm: its original path.
    /SX1262_DIO1:     keepout 2.000 mm, offset 1.275 mm -> residual 0.725 mm.
                      `lane` 6.081 mm == `nolane` 6.081 mm == `budget` 6.081 mm;
                      `nolift` NO_PATH.  The lane was worth nothing and without
                      the lift the relay was impossible.

So the disc belongs on the chain's BODY, far enough from BOTH its fixed
terminals that no lift fires at all -- and THAT is a two-parameter question
(how far along the chain, how wide) with no closed form, because whether the
relay can still get past depends on the board.  This screen sweeps it.

Each rung writes a `--detour-spec`, derives its guard exactly as
`route_maze_batch.detour_guard` does, and asks `screen_relay_wall.py` -- so the
question put to each geometry is the SAME question the gate would put to it, and
the four arms (`lane`, `nolane`, `nolift`, `budget`) separate an allowance from
a wall.  A geometry is reported as:

    BINDS    the relay came back LONGER than the copper it replaced.  A lane
             that does not bind reserves nothing, whatever its radius says.
    ADMITS   the relay routed at all.  A lane that does not admit refuses the
             whole transaction, because a detour that will not route is a
             refusal by clause 5.

Only a geometry that does BOTH is worth a gate run.  On `/SX1262_DIO1` versus
`/08_BUTTONS_EXPANDERS/BTN_B_N` there is none: eight lift-free discs from 1.3 to
2.8 mm, at four offsets along a 6.081 mm chain, ALL `NO_PATH` at 30 mm of budget
across `F`/`B`/`In2` on a 0.050 mm lattice -- which proves the two nets mutually
exclusive TO THE OBJECT, not merely in two failing arms.

NOTHING IS WRITTEN outside the scratch directory this is pointed at.
"""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
HERE = Path(__file__).resolve().parent

# The default ladder: radii wide enough to matter on this board's 0.200 mm
# signal geometry, at offsets that walk the near half of a chain.  Paired so
# that every rung is lift-free for a chain of ordinary length -- the offset
# always exceeds the reach -- because a rung that fires a lift measures the
# lift and not the lane.
DEFAULT_RUNGS = ((1.5, 1.3), (1.8, 1.5), (2.0, 1.8), (2.2, 1.9),
                 (2.5, 2.2), (2.6, 2.4), (3.0, 2.5), (3.0, 2.8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--net", required=True,
                    help="the net whose chain is being displaced")
    ap.add_argument("--a-mm", required=True, metavar="X,Y",
                    help="the chain's FAR fixed terminal")
    ap.add_argument("--b-mm", required=True, metavar="X,Y",
                    help="the chain's NEAR fixed terminal -- the one beside "
                         "the land whose pocket is being freed.  Offsets are "
                         "measured from here")
    ap.add_argument("--layer", default="B.Cu")
    ap.add_argument("--width-mm", type=float, default=0.2)
    ap.add_argument("--count", type=int, default=1,
                    help="how many coincident copies of this description the "
                         "board carries (D-648); two duplicates are ONE "
                         "conductor and ONE obstacle")
    ap.add_argument("--exempt", action="append", default=[],
                    help="net the reservation does NOT bind -- the net the "
                         "pocket is being freed FOR.  Repeatable")
    ap.add_argument("--layers", default="B",
                    help="comma-separated guard layer keys (D-649); a "
                         "reservation made for ONE track on ONE layer is not a "
                         "barrel and need not claim all six")
    ap.add_argument("--rung", action="append", default=None, metavar="OFF:R",
                    help="one geometry as `offset_from_b:radius` in mm. "
                         "Repeatable; default is the eight-rung ladder")
    ap.add_argument("--grid", type=int, default=50000)
    ap.add_argument("--wide-mm", type=float, default=40.0)
    ap.add_argument("--relay-max-mm", type=float, default=30.0,
                    help="the budget the `lane` arm is given; generous on "
                         "purpose, so a NO_PATH is a wall and not an allowance")
    ap.add_argument("--work", type=Path, required=True,
                    help="scratch directory for the per-rung specs, guards "
                         "and relay-wall reports")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    sys.path.insert(0, str(HERE))
    from route_maze_batch import detour_guard, load_detours

    def xy(text):
        parts = [float(v) for v in text.replace(" ", "").split(",")]
        if len(parts) != 2:
            raise SystemExit("--a-mm/--b-mm want X,Y in mm (got %r)" % text)
        return tuple(parts)

    A, B = xy(a.a_mm), xy(a.b_mm)
    was = math.hypot(A[0] - B[0], A[1] - B[1])
    if was <= 0:
        raise SystemExit("the chain's two ends are the same point")
    u = ((A[0] - B[0]) / was, (A[1] - B[1]) / was)   # unit vector b -> a
    rungs = ([tuple(float(v) for v in r.split(":")) for r in a.rung]
             if a.rung else list(DEFAULT_RUNGS))
    layers = [k.strip() for k in a.layers.split(",") if k.strip()]
    a.work.mkdir(parents=True, exist_ok=True)

    rows = []
    for off, r in rungs:
        c = (round(B[0] + off * u[0], 4), round(B[1] + off * u[1], 4))
        reach = r + a.width_mm / 2.0 + a.grid / 1e6
        spec = dict(schema=1, detours=[dict(
            net=a.net, layer=a.layer, a_mm=list(A), b_mm=list(B),
            width_mm=a.width_mm, count=a.count, relay=True,
            max_mm=a.relay_max_mm)],
            reserve=[dict(x_mm=c[0], y_mm=c[1], r_mm=r, layers=layers,
                          exempt=list(a.exempt))])
        tag = "%s-%s" % (off, r)
        sp = a.work / ("lane-spec-%s.json" % tag)
        sp.write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8")
        gp = a.work / ("lane-guard-%s.json" % tag)
        gp.write_text(json.dumps(detour_guard(load_detours(str(sp))),
                                 indent=1) + "\n", encoding="utf-8")
        op = a.work / ("lane-wall-%s.json" % tag)
        subprocess.run([sys.executable, str(HERE / "screen_relay_wall.py"),
                        "--board", str(a.board), "--spec", str(sp),
                        "--guard", str(gp), "--grid", str(a.grid),
                        "--wide-mm", str(a.wide_mm), "-o", str(op)],
                       check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        d = json.loads(op.read_text())["relays"][0]
        arms = d["arms"]
        row = dict(
            offset_from_b_mm=off, r_mm=r, centre_mm=list(c),
            reach_mm=round(reach, 4),
            dist_to_b_mm=round(off, 4), dist_to_a_mm=round(was - off, 4),
            # A rung whose reach covers either fixed terminal is measuring the
            # LIFT.  Reported, never silently dropped.
            lifts=len(d.get("terminal_lift") or ()),
            lift_free=bool(off > reach and (was - off) > reach),
            lane_ok=arms["lane"]["ok"], lane_mm=arms["lane"]["mm"],
            lane_vias=arms["lane"]["vias"],
            lane_reason=arms["lane"]["reason"],
            nolane_ok=arms["nolane"]["ok"], nolane_mm=arms["nolane"]["mm"],
            nolift_ok=arms["nolift"]["ok"],
            budget_ok=arms["budget"]["ok"],
            admits=bool(arms["lane"]["ok"]),
            binds=bool(arms["lane"]["ok"]
                       and arms["lane"]["mm"] > was + a.grid / 1e6),
            report=str(op))
        row["worth_a_gate_run"] = bool(row["binds"] and row["admits"])
        rows.append(row)
        print("  off=%-4s r=%-4s reach=%.2f lifts=%d  lane %-5s %8.3f mm "
              "(%d via)  binds=%-5s admits=%s"
              % (off, r, reach, row["lifts"], row["lane_ok"], row["lane_mm"],
                 row["lane_vias"], row["binds"], row["admits"]),
              file=sys.stderr, flush=True)

    doc = dict(
        schema=1, board=str(a.board), net=a.net, layer=a.layer,
        a_mm=list(A), b_mm=list(B), was_mm=round(was, 4),
        width_mm=a.width_mm, count=a.count, exempt=list(a.exempt),
        guard_layers=layers, grid_nm=a.grid, relay_max_mm=a.relay_max_mm,
        question=("which reservation geometry BINDS this relay -- brings it "
                  "back LONGER than the copper it replaced -- without "
                  "REFUSING it, given that a disc covering either fixed "
                  "terminal is cancelled by its own terminal lift"),
        method=("read-only; one --detour-spec and one route_maze_batch."
                "detour_guard per rung, each asked through "
                "screen_relay_wall.py so the question is the gate's own"),
        rungs=len(rows),
        any_worth_a_gate_run=any(r["worth_a_gate_run"] for r in rows),
        rows=rows)
    text = json.dumps(doc, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
