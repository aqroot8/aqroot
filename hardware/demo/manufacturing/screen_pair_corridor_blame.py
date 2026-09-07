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

AND Q3 RUNS WHENEVER NO *ADMISSIBLE* NET OPENS THE CORRIDOR ALONE.  Before
`--ban` that was the same test; with it, a corridor whose only single-net opener
is banned is exactly the corridor whose minimal SET is worth searching for, and
skipping Q3 there would report "no unprotected opening" without having looked.

THE REPORT IS WRITTEN AFTER EVERY STEP.  A probe that writes only at exit loses
a two-hour measurement to one impatient kill, and `complete` says whether the
run reached its own end.

    python3 screen_pair_corridor_blame.py NET A_REF B_REF \
        [MARGIN_MM] [GRID_NM] [OUT] [--ban NET]...
"""
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
from screen_corridor_blockers import Without, corridor_nets  # noqa: E402

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

# `--ban NET` is lifted out of `argv` BEFORE the positional read, so every
# existing invocation -- all of which are positional -- parses exactly as it
# did and the flag may sit anywhere on the line.
BANNED = []
_argv = []
_it = iter(sys.argv)
for _a in _it:
    if _a == "--ban":
        BANNED.append(next(_it))
    else:
        _argv.append(_a)
sys.argv = _argv

NET = sys.argv[1]
A_REF, B_REF = sys.argv[2], sys.argv[3]
MARGIN = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
GRID = int(sys.argv[5]) if len(sys.argv) > 5 else 50000
OUT = Path(sys.argv[6]) if len(sys.argv) > 6 else None

qb = qr.QBoard(str(BOARD))
ir.inject_existing_via_obstacles(qb)
reserved = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
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


def flush(complete=False):
    out = dict(schema=1, net=NET, a=A_REF, b=B_REF, margin_mm=MARGIN,
               grid_nm=GRID, layers=far, window_nets=list(cand),
               banned_nets=list(BANNED),
               instrument="maze3d.offcentre_route under "
                          "screen_corridor_blockers.Without",
               board=str(BOARD), seconds=round(time.time() - t0, 1),
               complete=bool(complete), rows=rows)
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if OUT:
        OUT.write_text(text)
    return out, text


base = ask()
rows.append(dict(step="BASE", ok=bool(base.get("ok")),
                 reason=base.get("reason"), why=base.get("why")))
print("BASE %s" % base.get("reason"), file=sys.stderr, flush=True)

cand = sorted(set(corridor_nets(qb, far, box, NET)) - set(BANNED))
flush()

with Without(qb, field, cand, box):
    upper = ask()
rows.append(dict(step="Q1_UPPER_BOUND", nets=list(cand),
                 ok=bool(upper.get("ok")), reason=upper.get("reason"),
                 why=upper.get("why"), mm=upper.get("mm"),
                 vias=upper.get("vias"), layers=upper.get("layers")))
flush()
print("Q1 drop ALL routed copper of %d foreign nets in the window -> %s"
      % (len(cand), ("OPENS %.3f mm, %s via" % (upper["mm"], upper["vias"]))
         if upper.get("ok") else upper.get("reason")),
      file=sys.stderr, flush=True)

opened = []
if upper.get("ok"):
    for net in cand:
        with Without(qb, field, [net], box):
            r = ask()
        rows.append(dict(step="Q2_SINGLE_NET", net=net,
                         ok=bool(r.get("ok")), reason=r.get("reason"),
                         mm=r.get("mm"), vias=r.get("vias"),
                         layers=r.get("layers")))
        if r.get("ok"):
            opened.append(net)
        flush()
        print("  Q2 %-42s -> %s"
              % (net, ("OPENS %.3f mm" % r["mm"]) if r.get("ok")
                 else r.get("reason")), file=sys.stderr, flush=True)

    # Q3 is owed whenever no ADMISSIBLE net opens the corridor alone.  With
    # `--ban` the banned nets are not in `cand` at all, so `opened` already
    # means "opened by copper this run may take" and this test needs no change
    # -- but it is worth saying, because the corridor whose only single-net
    # opener is PROTECTED is precisely the one whose minimal SET decides
    # whether an owner question exists.
    if not opened:
        keep = list(cand)
        for net in list(cand):
            trial = [x for x in keep if x != net]
            with Without(qb, field, trial, box):
                r = ask()
            if r.get("ok"):
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
                         mm=fin.get("mm"), vias=fin.get("vias"),
                         layers=fin.get("layers")))
        print("  Q3 MINIMAL SET %d nets %s -> %s"
              % (len(keep), sorted(keep),
                 ("OPENS %.3f mm" % fin["mm"]) if fin.get("ok")
                 else fin.get("reason")), file=sys.stderr, flush=True)

out, text = flush(complete=True)
if not OUT:
    sys.stdout.write(text)
print(" seconds %.1f" % (time.time() - t0), file=sys.stderr)
