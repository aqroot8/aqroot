#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- WHICH OF THE FOUR WALLS REFUSES THIS RELAY?  (D-667)

A `--detour-spec` relay that comes back `NO_PATH` has said almost nothing.  Four
different facts produce that word and they call for four different next moves:

    the BUDGET      `max_mm` is too tight              -> state a bigger one
    the TERMINAL    a reservation covers a fixed end   -> D-667 terminal lift
    the LANE        the reservation closes the corridor-> narrow it, or drop it
    the COPPER      there is no second path at all     -> stop relaying; evict

D-666 spent five gate arms and a wrong diagnosis on the difference.  It raised
`/WAKE_INT_N`'s two relay budgets to 15.0 and 12.0 mm against 5.136 and
2.428 mm of removed copper and concluded "the lane is the constraint, not the
allowance", which is true and is not the reading: both goal cells lay inside the
reservation, on all three of its layers, with ZERO of 24 free neighbours -- the
wave had a seed and nowhere to go, and no budget can matter then.

THIS SCREEN ASKS ALL FOUR AT ONCE, in about ten seconds a relay.  It rebuilds
the exact board the gate's relay pass sees -- the authority with the spec's
units removed and NOTHING yet laid -- and runs `maze3d.route_points` four times
per relay with `emit=False`, so it lays, proves and reverts and cannot disagree
with the gate about what is legal.  It writes no board and promotes nothing.

    nolane ok, lane NO_PATH        -> the reservation.  Narrow it per-layer, or
                                      route the protected net FIRST and drop it.
    lane NO_PATH, budget NO_PATH   -> not the allowance.  Do not raise max_mm.
    nolift != lane                 -> a fixed end is inside the reservation.
    nolane NO_PATH                 -> the copper.  A relay cannot answer this
                                      question; ask for the NET (--evict-whole).

A `nolane` answer at the OLD length with ZERO vias is the loudest result here:
it means the router put the chain back where it was, so that chain has exactly
one path in that pocket and a reservation over it is unsatisfiable by
construction.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--spec", type=Path, required=True,
                    help="the --detour-spec whose relays are in question")
    ap.add_argument("--guard", type=Path,
                    help="the --guard the gate was given; without one only the "
                         "`nolane` arm has meaning and the other three repeat it")
    ap.add_argument("--grid", type=int, default=50000,
                    help="lattice pitch in nm; a NO_PATH is a statement about a "
                         "PITCH as much as about a board (D-651)")
    ap.add_argument("--wide-mm", type=float, default=40.0,
                    help="the budget the `budget`/`nolane`/`nolift` arms are "
                         "given, to separate an allowance from a wall")
    ap.add_argument("--via-cost-mm", type=float, default=1.5)
    ap.add_argument("--net", action="append", default=[], metavar="NET",
                    help="ask only these relays (default: every relay in the "
                         "spec)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    sys.path.insert(0, str(HERE))
    import maze3d as mz
    import qrouter as qr
    import incremental_router as ir
    from route_maze_batch import (guard_for, terminal_lift, net_contract,
                                  permitted_layers, reserved_inner_planes,
                                  detour_layers, sha256_file)

    guard_doc = json.loads(a.guard.read_text()) if a.guard else {"guards": []}

    tmp = Path(tempfile.mkdtemp(prefix="relay-wall-"))
    try:
        for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_prl"):
            src = a.board.with_suffix(suf)
            if src.exists():
                shutil.copy2(src, tmp / src.name)
        path = tmp / a.board.name
        # THE REMOVAL RUNS IN A SEPARATE PROCESS, exactly as the gate runs it:
        # this KiCad build's SWIG bindings hand back an untyped object from any
        # LoadBoard that follows an in-process load-and-save, which is why
        # `route_maze_batch.detour_apply` is reachable as its own invocation.
        rep = tmp / "detour.json"
        subprocess.run([sys.executable, str(HERE / "route_maze_batch.py"),
                        "--detour-apply", str(path),
                        "--detour-spec", str(a.spec),
                        "--detour-report", str(rep)],
                       check=True, stdout=subprocess.DEVNULL)
        plan = json.loads(rep.read_text())

        import pcbnew
        ref = pcbnew.LoadBoard(str(path))
        reserved = reserved_inner_planes(ref)
        contracts = {d["net"]: net_contract(ref, d["net"], None)
                     for d in plan["detours"]}
        del ref
        qb = qr.QBoard(str(path))
        ir.inject_existing_via_obstacles(qb)
        for n, c in contracts.items():
            c["layers"] = permitted_layers(qb.routable, c["layers"], reserved, n)

        out = dict(schema=1, board=str(a.board),
                   board_sha256=sha256_file(a.board), grid_nm=a.grid,
                   wide_mm=a.wide_mm, spec=str(a.spec),
                   guard=(str(a.guard) if a.guard else None),
                   removed=plan.get("removed"), relays=[])
        for d in plan["detours"]:
            if not d.get("relay", True):
                continue
            if a.net and d["net"] not in a.net:
                continue
            net, c = d["net"], contracts[d["net"]]
            g = guard_for(guard_doc, net)
            gfree, lift = terminal_lift(
                g, d["lkey"], (tuple(d["a_nm"]), tuple(d["b_nm"])),
                d["width_nm"], a.grid)
            layers, _own = detour_layers(c["layers"], d["lkey"], False)
            rec = dict(net=net, layer=d["layer"], was_mm=d["mm"],
                       spec_max_mm=d.get("max_mm"), terminal_lift=lift,
                       a_mm=[round(v / 1e6, 4) for v in d["a_nm"]],
                       b_mm=[round(v / 1e6, 4) for v in d["b_nm"]], arms={})
            for tag, use_guard, use_lift, mm in (
                    ("lane",   True,  True,  d.get("max_mm", 0.0)),
                    ("budget", True,  True,  a.wide_mm),
                    ("nolane", False, False, a.wide_mm),
                    ("nolift", True,  False, a.wide_mm)):
                t0 = time.time()
                f = mz.Field(qb, net, d["width_nm"], c["clr_pad"], c["clr"],
                             c["via_dia"], c["via_drill"], G=a.grid,
                             layers=layers,
                             guard=(g if use_guard else None),
                             guard_free=(gfree if (use_guard and use_lift)
                                         else None))
                r = mz.route_points(qb, f, tuple(d["a_nm"]), tuple(d["b_nm"]),
                                    d["lkey"], via_cost_mm=a.via_cost_mm,
                                    emit=False, max_mm=mm)
                r.pop("mark", None)
                rec["arms"][tag] = dict(
                    max_mm=mm, ok=bool(r.get("ok")), reason=r.get("reason"),
                    mm=round(r.get("mm", 0.0), 3), vias=r.get("vias", 0),
                    layers=r.get("layers"), via_xy=r.get("via_xy"),
                    seconds=round(time.time() - t0, 1))
                print("  %-22s %-7s %-14s %7.3f mm %d via %5.1f s"
                      % (net, tag, ("ok" if r.get("ok") else r.get("reason")),
                         r.get("mm", 0.0), r.get("vias", 0),
                         time.time() - t0), file=sys.stderr, flush=True)
            out["relays"].append(rec)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    text = json.dumps(out, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
