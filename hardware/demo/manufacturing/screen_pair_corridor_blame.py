#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: ONE pair, the OFF-CENTRE launch, and the
containment bound.

`screen_corridor_blockers.py` asks this question for every pair of a net with
`route_join`'s CENTRE-ANCHORED launch.  On `/I2C_SCL_INT` that is fifteen pairs,
and the two that matter launch only OFF CENTRE -- `screen_offcentre_hop.py
--route` gets `U2.22` off its land in 0.763 mm and `U3.22` in 1.138 mm where
`route_join` reports one escape and `screen_lattice_exact_route.py` reports
none -- so the generic screen prices a search those pairs do not use.

This asks the SAME question with the SAME discipline -- `Without` and
`corridor_nets` imported from that screen, so only ROUTED copper is dropped,
only copper WHOLLY INSIDE the window, restored in `__exit__`, board never
written -- for ONE pair with `maze3d.offcentre_route`.

  Q1  UPPER BOUND: every foreign net's routed copper in the window, at once.
      Still NO_PATH => no containment-bounded rip-up on these layers opens it,
      and the per-net sweep is skipped as it is in the generic screen.
  Q2  Each foreign net alone.
  Q3  REVERSE-GREEDY minimisation of the OPEN set: offer each member BACK once
      and keep it out only if the corridor closes without it.  That is D-646's
      discipline and also the only affordable shape -- forward greedy asks
      O(n^2) whole-board wavefronts and this board charges minutes for each.

`--ban NET` (repeatable) is D-641's CUT-SET RETRY brought to this screen.  A
banned net is kept out of the pool entirely: it is never dropped by Q1, never
asked in Q2 and never offered to Q3, so every answer the run gives is an answer
that DOES NOT TOUCH IT.  The question it exists for is the one this board keeps
arriving at -- `/ACC_5V_SW_EN` is PROTECTED copper and opening a corridor by
evicting it is an OWNER decision, so "does an opening exist that leaves it
alone?" has to be askable without a human reading a net list.  Without `--ban`
the run is byte-identical to every one before it.

`--max-mm X` is the OTHER half of that, and the bus edge is what bought it.
Q2 and Q3 minimise the number of NETS and say nothing about the route the
opening buys, so on `/I2C_SCL_INT` `U3.22 <-> U4.13` -- a 10.784 mm gap that
Q1's own upper bound opens in **14.306 mm on `B.Cu` with ZERO vias** -- the
screen reported `GND alone OPENS 108.135 mm, 13 vias` and stopped, because one
admissible net had opened it and Q3 only runs when none has.  A 108 mm haul
across thirteen layer changes for a 10.8 mm gap is not a transaction anybody
would promote; it is `ok: true` and nothing else.  With `--max-mm`, an opening
counts only if it also comes in under the bound, so "opened" means "opened into
something worth executing" and Q3 is owed whenever nothing does.  Q1's own `mm`
is the natural yardstick and the report always carries it.

`--per-object` is Q4, and it exists because a REPORT and a TRANSACTION do not
speak the same language.  Q1-Q3 answer in NETS, which is the unit a human reads
and the unit `--evict` licenses; `--detour-spec` licenses per OBJECT SIGNATURE,
and the gap between the two is what this board keeps paying for.  D-654's answer
for `/I2C_SDA_INT` was "the minimal set is {`/I2C_SCL_INT`, `GND`}", and taking
that literally means `--evict /I2C_SCL_INT` -- which on this board is 84 objects
and 178.9 mm, the WHOLE net, because the eviction window is the requested net's
own pad bbox and `/I2C_SCL_INT` spans the board.  The measurement never claimed
that much copper was in the way.  So Q4 re-runs the same reverse-greedy over the
OBJECTS of the minimal set and reports what is left in `--detour-spec` shape.

AND `count` COMES OFF THE BOARD, NOT OFF THE ROUTER.  `count` is D-648's claim
that KiCad carries a description N times, and since D-646 a single `PCB_VIA` is
FOURTEEN router objects and two drills -- the board-via scan and
`inject_existing_via_obstacles` both put it there.  Counting drills would emit
`"count": 2` for copper this board has exactly one of.

AND IT COUNTS A BARREL AS ONE OBJECT.  In the router's model a via is six annuli
plus a drill; in KiCad it is one `PCB_VIA` and one signature.  A minimisation
that offered those seven back one at a time would report six annuli as "not
needed" and hand over a spec that removes a hole and leaves the copper standing
-- the exact error D-653's first probe made.  Units here are PHYSICAL: one track
description with its duplicate `count`, or one whole barrel.

AND Q3 RUNS WHENEVER NO *ADMISSIBLE* NET OPENS THE CORRIDOR ALONE.  Before
`--ban` that was the same test; with it, a corridor whose only single-net opener
is banned is exactly the corridor whose minimal SET is worth searching for, and
skipping Q3 there would report "no unprotected opening" without having looked.

`--minimise-only` (D-666) skips Q2 and goes straight to Q3.  Q2 costs one
whole-board wavefront per window net and exists only so Q3 can be SKIPPED when
one net opens the corridor alone; on a pair where the opening needs many nets
at once -- `/WAKE_INT_N` `U2.1 <-> Q10.3`, where every single-net drop returns
EXACTLY the base price of 151.580 mm -- that is half the bill spent on the half
that cannot be executed.  What the flag gives up is recorded, not hidden: the
report carries `q2: "SKIPPED"` and a `Q2_SKIPPED` row, and the run no longer
proves that no single net suffices.  Default OFF.

THE REPORT IS WRITTEN AFTER EVERY STEP.  A probe that writes only at exit loses
a two-hour measurement to one impatient kill, and `complete` says whether the
run reached its own end.

    python3 screen_pair_corridor_blame.py NET A_REF B_REF \
        [MARGIN_MM] [GRID_NM] [OUT] [--ban NET]... [--per-object]
        [--max-mm X] [--minimise-only]
"""
import os
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import qrouter as qr             # noqa: E402
import incremental_router as ir  # noqa: E402
import maze3d as mz              # noqa: E402
from route_maze_batch import (net_contract, reserved_inner_planes,  # noqa: E402
                              permitted_layers)
from screen_corridor_blockers import (Without, WithoutObjects,  # noqa: E402
                                      corridor_nets)

AUTHORITY = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
BOARD = AUTHORITY

# `--ban NET` is lifted out of `argv` BEFORE the positional read, so every
# existing invocation -- all of which are positional -- parses exactly as it
# did and the flag may sit anywhere on the line.
BANNED = []
PER_OBJECT = False
MINIMISE_ONLY = False
MAX_MM = None
# D-668: `--board PATH` -- ASK THIS OF A STATED BOARD.  Everything below runs
# off ONE `QBoard`, built at import time from a hard-coded path, so this screen
# could only ever blame the authority.  That is the wrong board exactly when
# the question is interesting: a pair that survives a transaction is a pair on
# the CANDIDATE that transaction produced, and on the authority it may not even
# be open.  `/SX1262_CS_N` `R27.2 <-> U1.10` is that pair -- it exists only on
# D-667 arm J's board, where the net has been evicted whole and rebuilt short.
# The named board's `.kicad_dru` and `.kicad_pro` must sit beside it, for the
# same reason `route_maze_batch.py --board` insists: without the project every
# netclass resolves to Default and this screen's widths and clearances would be
# measured against rules the board does not have.  This screen writes nothing,
# so there is no promotion to refuse -- only a `board` field in the report,
# which it already carried and which now tells the truth.
BOARD_ARG = None
_argv = []
_it = iter(sys.argv)
for _a in _it:
    if _a == "--ban":
        BANNED.append(next(_it))
    elif _a == "--per-object":
        PER_OBJECT = True
    elif _a == "--minimise-only":
        MINIMISE_ONLY = True
    elif _a == "--max-mm":
        MAX_MM = float(next(_it))
    elif _a == "--board":
        BOARD_ARG = next(_it)
    else:
        _argv.append(_a)
sys.argv = _argv
if BOARD_ARG is not None:
    _b = Path(BOARD_ARG).resolve()
    if not _b.is_file():
        raise SystemExit("--board %s does not exist" % BOARD_ARG)
    _missing = [x for x in (".kicad_dru", ".kicad_pro")
                if not _b.with_suffix(x).is_file()]
    if _missing:
        raise SystemExit(
            "--board %s has no %s beside it: a scratch .kicad_pcb without its "
            ".kicad_pro resolves every netclass to Default, so every width, "
            "clearance and via floor this screen prices would be one the board "
            "does not carry" % (BOARD_ARG, " / ".join(_missing)))
    BOARD = _b

NET = sys.argv[1]
A_REF, B_REF = sys.argv[2], sys.argv[3]
MARGIN = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
GRID = int(sys.argv[5]) if len(sys.argv) > 5 else 50000
OUT = Path(sys.argv[6]) if len(sys.argv) > 6 else None

qb = qr.QBoard(str(BOARD))
ir.inject_existing_via_obstacles(qb)
reserved = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET, trunk_floor=bool(os.environ.get(
    "AQROOT_TRUNK_FLOOR")))
# D-690.  The screen must price the width the GATE will route at, or it blames
# the wrong corridor.  `--trunk-floor` descends a class the `.kicad_dru` prices
# and, since D-690, a NET the `.kicad_dru` prices by name; env-gated so every
# run before this one reproduces byte for byte.
far = list(permitted_layers(qb.routable, c["layers"], reserved, NET))

islands = mz.net_islands(qb, NET)
pads = {p["ref"]: p for isl in islands for p in isl}
pa, pb = pads[A_REF], pads[B_REF]
M = qr.MM
box = (min(pa["x"], pb["x"]) - MARGIN * M, min(pa["y"], pb["y"]) - MARGIN * M,
       max(pa["x"], pb["x"]) + MARGIN * M, max(pa["y"], pb["y"]) + MARGIN * M)

field = mz.Field(qb, NET, c["width"], c["clr_pad"], c["clr"],
                 c["via_dia"], c["via_drill"], G=GRID, layers=far)

t0 = time.time()
rows = []
cand = []


def ask():
    m = qb.mark()
    try:
        return mz.offcentre_route(qb, field, pa, pb, G=GRID)
    finally:
        qb.revert(m)


LAYER_NAME = {"F": "F.Cu", "I1": "In1.Cu", "I2": "In2.Cu", "I3": "In3.Cu",
              "I4": "In4.Cu", "B": "B.Cu"}


def object_units(nets):
    """The window's routed copper of `nets`, grouped into PHYSICAL units.

    A unit is what ONE `--detour-spec` entry names and what ONE licence
    signature covers: a track description together with every exact duplicate
    of it this board carries (D-648's `count`), or a whole barrel -- its
    per-layer annuli AND its drill -- because a spec that took only the hole
    would leave the copper standing (D-653).
    """
    units = {}
    # EVERY layer, not just the routable ones: `Without` -- the context manager
    # Q1-Q3 were proved under -- iterates `qb.shapes` whole, so a pool built
    # over `far` alone would start from a DIFFERENT board than the one Q3 said
    # was open, and every unit would then read REQUIRED for a reason that is
    # about this function and not about the board.
    for L in qb.shapes:
        for s_ in qb.shapes[L]:
            if s_.net not in nets or s_.tag not in ("track", "via"):
                continue
            a, b, c, d = s_.bbox(0)
            if a < box[0] or b < box[1] or c > box[2] or d > box[3]:
                continue
            if s_.tag == "via":
                k = ("V", s_.net, int(s_.cx), int(s_.cy))
            else:
                k = ("T", s_.net, L, int(s_.x0), int(s_.y0),
                     int(s_.x1), int(s_.y1), int(s_.hw))
            units.setdefault(k, []).append(s_)
    for h in qb.holes:
        if h.net not in nets or not h.tag.startswith("via"):
            continue
        a, b, c, d = h.bbox(0)
        if a < box[0] or b < box[1] or c > box[2] or d > box[3]:
            continue
        units.setdefault(("V", h.net, int(h.cx), int(h.cy)), []).append(h)
    return units


def board_barrels_at(net, x_nm, y_nm):
    """How many `PCB_VIA` objects THIS BOARD carries at that centre, on `net`.

    `count` in a `--detour-spec` is a claim about KiCad's own object list --
    "this board carries that exact description N times", D-648 -- and the
    router's object list is not that list.  A barrel is six annuli plus a drill
    to `qrouter`, and since D-646 the board-via scan and
    `incremental_router.inject_existing_via_obstacles` BOTH put it there, so
    one `PCB_VIA` reads as FOURTEEN router objects and two drills.  Counting
    the drills would emit `"count": 2` for copper that exists once, and the
    applier -- which resolves EXACTLY and by DECLARED multiplicity -- would
    refuse the spec or, worse, be handed a spec claiming copper the board has
    not got.  So the number comes off the board.
    """
    n = 0
    for t in qb.b.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        p = t.GetPosition()
        if int(p.x) == int(x_nm) and int(p.y) == int(y_nm):
            n += 1
    return n


def unit_spec(k, objs):
    """One unit as the `--detour-spec` entry that would remove it."""
    if k[0] == "V":
        dia = max([2 * o.hx for o in objs if o.tag == "via"] or [0])
        drill = max([2 * o.hx for o in objs if o.tag == "via/hole"] or [0])
        return dict(kind="barrel", net=k[1], router_objects=len(objs),
                    objects=len(objs),
                    count=board_barrels_at(k[1], k[2], k[3]),
                    at_mm=[round(k[2] / 1e6, 4), round(k[3] / 1e6, 4)],
                    dia_mm=round(dia / 1e6, 4), drill_mm=round(drill / 1e6, 4))
    return dict(kind="track", net=k[1], layer=LAYER_NAME.get(k[2], k[2]),
                router_objects=len(objs), objects=len(objs), count=len(objs),
                a_mm=[round(k[3] / 1e6, 4), round(k[4] / 1e6, 4)],
                b_mm=[round(k[5] / 1e6, 4), round(k[6] / 1e6, 4)],
                width_mm=round(2 * k[7] / 1e6, 4))


def accepts(r):
    """Did this trial OPEN the corridor into something worth executing?

    Without `--max-mm` this is exactly `ok`, so every run written before the
    flag existed reads as it did.  With it, a route that opens but costs more
    than the bound is recorded and NOT counted as an opening: the minimisation
    below is a search for a transaction, and a transaction has a price.
    """
    if not r.get("ok"):
        return False
    if MAX_MM is None:
        return True
    return r.get("mm") is not None and r["mm"] <= MAX_MM


def flush(complete=False):
    out = dict(schema=1, net=NET, a=A_REF, b=B_REF, margin_mm=MARGIN,
               grid_nm=GRID, layers=far, window_nets=list(cand),
               banned_nets=list(BANNED), max_mm=MAX_MM,
               q2="SKIPPED" if MINIMISE_ONLY else "RUN",
               instrument="maze3d.offcentre_route under "
                          "screen_corridor_blockers.Without",
               board=str(BOARD),
               # D-668: WHICH BOARD, AND IS IT THE ONE THIS REPOSITORY SHIPS.
               # A blame taken on a candidate is still a blame; it is just not
               # a statement about the authority, and the report has to say so
               # on its own without the reader recognising a path.
               board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),
               board_is_authority=bool(BOARD.resolve() == AUTHORITY.resolve()),
               seconds=round(time.time() - t0, 1),
               complete=bool(complete), rows=rows)
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if OUT:
        OUT.write_text(text)
    return out, text


# D-666.  BASE IS A PRICE, NOT A YES/NO, AND SO IS Q1's UPPER BOUND.
#
# Every run before D-666 was made on a pair whose BASE was `NO_PATH`, so `ok`
# alone said everything there was to say and the row carried no `mm`.
# `/WAKE_INT_N` `U2.1 <-> Q10.3` is the first pair whose BASE is OPEN and
# WORTHLESS: `maze3d.offcentre_route` closes it with NOTHING evicted, in
# **151.580 mm across FIFTEEN barrels** for a 25.258 mm gap, which is the same
# answer `route_join` called `TOO_LONG` in D-665 §7 and the tap census priced
# at 150.169 mm in D-665 §1.  Recorded as `ok: true, mm: absent`, that is
# indistinguishable from a corridor that needs no transaction at all.
#
# So BASE now carries its PRICE and its verdict under `--max-mm`, and the two
# degenerate shapes are named and stopped instead of swept:
#
#   * `accepts(base)` -- the corridor is already open into something worth
#     executing.  There is no blame to apportion; the answer is "lay it".
#     Sweeping 43 nets there reports "every one of them opens it alone", which
#     is true, useless, and an hour of whole-board wavefronts.
#   * `not accepts(upper)` -- Q1's OWN upper bound, every window net dropped at
#     once, is still over the bound.  No subset can beat the whole set, so no
#     containment-bounded transaction exists at this price and Q2 is skipped
#     for exactly the reason the `NO_PATH` upper bound already skipped it.
#
# Without `--max-mm`, `accepts` IS `ok` (see above), so the only behaviour that
# moves for a bound-less run is the BASE early exit -- and a bound-less run
# whose BASE is open never had a question to ask.
base = ask()
rows.append(dict(step="BASE", ok=bool(base.get("ok")),
                 accepted=accepts(base), reason=base.get("reason"),
                 why=base.get("why"), mm=base.get("mm"),
                 vias=base.get("vias"), layers=base.get("layers")))
print("BASE %s" % (("OPENS %.3f mm, %s via%s"
                    % (base["mm"], base["vias"],
                       "" if accepts(base) else "  OVER --max-mm"))
                   if base.get("ok") else base.get("reason")),
      file=sys.stderr, flush=True)

if accepts(base):
    rows.append(dict(step="VERDICT", verdict="NO_EVICTION_NEEDED",
                     why="the corridor is already open at %.3f mm within the "
                         "--max-mm bound; there is no blame to apportion"
                         % base["mm"]))
    flush(True)
    print("VERDICT NO_EVICTION_NEEDED -- lay it", file=sys.stderr, flush=True)
    sys.exit(0)

cand = sorted(set(corridor_nets(qb, far, box, NET)) - set(BANNED))
flush()

with Without(qb, field, cand, box):
    upper = ask()
rows.append(dict(step="Q1_UPPER_BOUND", nets=list(cand),
                 ok=bool(upper.get("ok")), accepted=accepts(upper),
                 reason=upper.get("reason"),
                 why=upper.get("why"), mm=upper.get("mm"),
                 vias=upper.get("vias"), layers=upper.get("layers")))
flush()
print("Q1 drop ALL routed copper of %d foreign nets in the window -> %s"
      % (len(cand), ("OPENS %.3f mm, %s via%s"
                     % (upper["mm"], upper["vias"],
                        "" if accepts(upper) else "  OVER --max-mm"))
         if upper.get("ok") else upper.get("reason")),
      file=sys.stderr, flush=True)

opened = []
minimal_nets = None
if accepts(upper):
    # D-666.  Q2 IS AN OPTIMISATION, AND ON A CONGESTED PAIR IT IS HALF THE BILL.
    #
    # Q2 asks `len(cand)` whole-board wavefronts so that Q3 can be SKIPPED when
    # one net opens the corridor alone.  On `/WAKE_INT_N` `U2.1 <-> Q10.3` that
    # is 32 probes at ~2.4 minutes each -- 77 minutes -- to learn something the
    # first three probes already made near-certain: every single-net drop
    # returns EXACTLY the BASE price, 151.580 mm, because the 29.955 mm corridor
    # needs many nets gone AT ONCE and no one of them is on the base path.
    # Q3 then costs another 77 minutes, and only Q3's answer can be executed.
    #
    # `--minimise-only` spends the budget on the half that produces the
    # transaction.  WHAT IT GIVES UP IS STATED, NOT HIDDEN: the run no longer
    # proves that no single net opens the corridor, so the report records
    # `q2: "SKIPPED"` and a `Q3_MINIMAL_SET` of one net is the only evidence
    # that a single-net opener exists.  Reverse-greedy is still a genuine
    # minimisation of the OPEN set -- it offers every member back and keeps it
    # out only if the corridor survives -- so the set it lands on is minimal in
    # the sense Q3 always meant, just not additionally certified as "and no
    # smaller singleton exists".  Default OFF: every run made before this flag
    # is byte-identical without it.
    if MINIMISE_ONLY:
        rows.append(dict(step="Q2_SKIPPED", nets=len(cand),
                         why="--minimise-only: the single-net sweep is not "
                             "asked, so this run does not prove that no one "
                             "net opens the corridor alone"))
        flush()
        print("  Q2 SKIPPED (--minimise-only), %d nets not asked" % len(cand),
              file=sys.stderr, flush=True)
    for net in ([] if MINIMISE_ONLY else cand):
        with Without(qb, field, [net], box):
            r = ask()
        rows.append(dict(step="Q2_SINGLE_NET", net=net,
                         ok=bool(r.get("ok")), accepted=accepts(r),
                         reason=r.get("reason"),
                         mm=r.get("mm"), vias=r.get("vias"),
                         layers=r.get("layers")))
        if accepts(r):
            opened.append(net)
        flush()
        print("  Q2 %-42s -> %s"
              % (net, ("OPENS %.3f mm%s" % (r["mm"], "" if accepts(r)
                                             else "  OVER --max-mm"))
                 if r.get("ok") else r.get("reason")),
              file=sys.stderr, flush=True)

    # Q3 is owed whenever no ADMISSIBLE net opens the corridor alone.  With
    # `--ban` the banned nets are not in `cand` at all, so `opened` already
    # means "opened by copper this run may take" and this test needs no change
    # -- but it is worth saying, because the corridor whose only single-net
    # opener is PROTECTED is precisely the one whose minimal SET decides
    # whether an owner question exists.
    if opened:
        # A single net opens it, so the transaction is that net's copper and
        # Q4's pool is the CHEAPEST such net's window objects.  The order of
        # `cand` is sorted, so this is deterministic.
        minimal_nets = [opened[0]]
    if not opened:
        keep = list(cand)
        for net in list(cand):
            trial = [x for x in keep if x != net]
            with Without(qb, field, trial, box):
                r = ask()
            if accepts(r):
                keep = trial
                rows.append(dict(step="Q3_DROPPED", net=net,
                                 remaining=len(keep), mm=r.get("mm")))
                print("  Q3 %-42s NOT NEEDED (%d left)" % (net, len(keep)),
                      file=sys.stderr, flush=True)
            else:
                rows.append(dict(step="Q3_REQUIRED", net=net,
                                 remaining=len(keep), reason=r.get("reason")))
                print("  Q3 %-42s REQUIRED" % net, file=sys.stderr, flush=True)
            flush()
        with Without(qb, field, keep, box):
            fin = ask()
        rows.append(dict(step="Q3_MINIMAL_SET", nets=sorted(keep),
                         n=len(keep), ok=bool(fin.get("ok")),
                         accepted=accepts(fin),
                         mm=fin.get("mm"), vias=fin.get("vias"),
                         layers=fin.get("layers")))
        if accepts(fin):
            minimal_nets = sorted(keep)
        print("  Q3 MINIMAL SET %d nets %s -> %s"
              % (len(keep), sorted(keep),
                 ("OPENS %.3f mm" % fin["mm"]) if fin.get("ok")
                 else fin.get("reason")), file=sys.stderr, flush=True)

# Q4 -- THE SAME MINIMISATION, IN THE UNIT A TRANSACTION IS WRITTEN IN.
# The set Q2/Q3 hands over is a set of NETS; `--detour-spec` licenses OBJECTS,
# and on this board the difference between the two is 178.9 mm of copper.  The
# pool is the window copper of whatever the run proved open -- the single-net
# opener when Q2 found one, otherwise Q3's minimal set -- so Q4 never asks a
# question the run has not already proved has a `yes`.
if PER_OBJECT:
    pool_nets = sorted(minimal_nets or ())
    if pool_nets:
        units = object_units(set(pool_nets))
        order = sorted(units)
        keep_out = set()
        for k in order:
            keep_out.update(id(o) for o in units[k])
        print("  Q4 pool: %d units / %d objects from %s"
              % (len(order), len(keep_out), pool_nets),
              file=sys.stderr, flush=True)
        # The pool must reproduce the state Q2/Q3 proved open, or the
        # minimisation below is measuring its own bookkeeping.  Say so and
        # stop rather than report a set of REQUIREDs that means nothing.
        with WithoutObjects(qb, field, keep_out):
            start = ask()
        rows.append(dict(step="Q4_POOL", nets=pool_nets, n_units=len(order),
                         n_objects=len(keep_out), ok=bool(start.get("ok")),
                         accepted=accepts(start),
                         reason=start.get("reason"), mm=start.get("mm")))
        kept = list(order)
        for k in (order if accepts(start) else []):
            back = {id(o) for o in units[k]}
            trial = keep_out - back
            with WithoutObjects(qb, field, trial):
                r = ask()
            spec = unit_spec(k, units[k])
            if accepts(r):
                keep_out = trial
                kept = [x for x in kept if x != k]
                rows.append(dict(step="Q4_OBJECT_RETURNED", unit=spec,
                                 remaining=len(kept), mm=r.get("mm")))
                print("  Q4 %-58s NOT NEEDED (%d left)"
                      % (json.dumps(spec.get("a_mm") or spec.get("at_mm"))
                         + " " + spec["net"], len(kept)),
                      file=sys.stderr, flush=True)
            else:
                rows.append(dict(step="Q4_OBJECT_REQUIRED", unit=spec,
                                 remaining=len(kept), reason=r.get("reason")))
                print("  Q4 %-58s REQUIRED"
                      % (json.dumps(spec.get("a_mm") or spec.get("at_mm"))
                         + " " + spec["net"]), file=sys.stderr, flush=True)
            flush()
        fin4 = start
        if accepts(start):
            with WithoutObjects(qb, field, keep_out):
                fin4 = ask()
        specs = [unit_spec(k, units[k]) for k in kept]
        rows.append(dict(step="Q4_MINIMAL_OBJECTS", units=specs,
                         n_units=len(specs), accepted=accepts(fin4),
                         n_objects=sum(u["objects"] for u in specs),
                         nets=sorted({u["net"] for u in specs}),
                         ok=bool(fin4.get("ok")), mm=fin4.get("mm"),
                         vias=fin4.get("vias"), layers=fin4.get("layers")))
        print("  Q4 MINIMAL OBJECTS %d units (%d router objects) over %s -> %s"
              % (len(specs), sum(u["objects"] for u in specs),
                 sorted({u["net"] for u in specs}),
                 ("OPENS %.3f mm" % fin4["mm"]) if fin4.get("ok")
                 else fin4.get("reason")), file=sys.stderr, flush=True)
        flush()

out, text = flush(complete=True)
if not OUT:
    sys.stdout.write(text)
print(" seconds %.1f" % (time.time() - t0), file=sys.stderr)
