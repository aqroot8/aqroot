#!/usr/bin/env python3
"""Which island PAIRS has the all-or-nothing MST never even ASKED? -- D-626

A plane-less net is routed as ONE transaction over its MST.  The FIRST pair
that will not close fails the whole net, and every REMAINING pair of that net
is then never attempted -- so "open" in `routing_ledger.py` and "refused" in a
router report have been the same word for two different things, and this board
has been reading absences of measurement as measurements.  `--partial` runs a
per-pair transaction instead; this screen drives it over every open net and
reports what each pair actually said.

WHY IT MATTERS RIGHT NOW.  D-625 proved that a `NO_PATH` corridor refusal on
this board is a LADDER question before it is a wall -- `BTN_DOWN_N` refused at
0.100 / 0.0667 / 0.050 mm under the same 47-tube guard that admitted it at
0.0333 mm.  A pair nobody has asked cannot be laddered, so the census is the
work-list that comes BEFORE the ladder, and it pairs with
`screen_ladder_prefilter.py`, which answers the other half: an ESCAPE refusal
on a land with no legal escape at ANY pitch is the one refusal a finer lattice
provably cannot lift.

    reason NO_PATH            -> CORRIDOR.  Ladder it; D-625's lesson applies.
    reason NO_LEGAL_ESCAPE_*  -> ESCAPE.  Ask `screen_ladder_prefilter.py`
                                 whether ANY pitch can launch that land first.

TWO THINGS THIS SCREEN REFUSES TO GUESS.

**A POUR-SERVED NET IS EXCLUDED BY THE BOARD'S OWN ZONES, NOT BY ITS NAME.**
`+3V3` and `GND` are served by a plane and a stitch, not by an MST of pairs, so
`--partial` is the wrong instrument on them and running it would report a wall
the promotion path would never have hit.  A hard-coded name list would have
been wrong the moment a rail was renamed or another net acquired a pour, so the
BOARD decides: any net owning a non-rule-area zone is `POUR_SERVED` and is
skipped before a router ever starts -- which also keeps a 246-pad `GND` off the
work queue.  `/01_POWER_TREE/BQ25185_SYS` is exactly that case and a name list
would have missed it.  The router's own `routed[0]["mode"]` is read back as a
SECOND, confirming guard: a net that reaches `stitch` mode without owning a
zone is recorded rather than silently reported as a pair census.

**A CLOSED JOIN AND A FAILED ONE DO NOT NAME THEIR ENDS THE SAME WAY.**  A
failure carries `a`/`b` -- the two ISLANDS, as pad lists.  A join carries
`from`/`to` -- the two PADS it actually ran between, plus the layers and via
sites it used.  Reading `a`/`b` off a join yields `None` and prints a closed
pair with no ends, which is a report that looks complete and says nothing.
Both shapes are read here and `ends_are` names which one each row came from.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from route_maze_batch import BOARD, zones
from routing_ledger import generate as ledger_build

HERE = Path(__file__).resolve().parent


def slug(net):
    return net.strip("/").replace("/", "-").lower()


def run_partial(net, grid, work, extra):
    """One `--partial` run for one net.  Returns its report, or None."""
    out = work / ("%s.json" % slug(net))
    cmd = [sys.executable, str(HERE / "route_maze_batch.py"), net, "--partial",
           "--grid", grid, "--work", str(work / slug(net)), "--out", str(out)]
    cmd += extra
    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True)
    secs = round(time.time() - t0, 1)
    (work / ("%s.log" % slug(net))).write_text(p.stdout + p.stderr)
    if not out.exists():
        return None, secs, p.returncode
    return json.loads(out.read_text()), secs, p.returncode


def pairs_of(r):
    """Every island pair this run ASKED, closed ones first, in ask order."""
    pairs = []
    for j in r.get("joins") or []:
        pairs.append(dict(closed=True, ends_are="pads", a=j.get("from"),
                          b=j.get("to"), mm=j.get("mm"), vias=j.get("vias"),
                          layers=j.get("layers")))
    for x in r.get("failures") or []:
        pairs.append(dict(closed=False, ends_are="islands", a=x.get("a"),
                          b=x.get("b"), reason=x.get("reason"),
                          why=x.get("why"), gap_mm=x.get("gap_mm"),
                          src_escapes=x.get("src_escapes"),
                          dst_escapes=x.get("dst_escapes"),
                          kind=("CORRIDOR -- ladder it"
                                if x.get("reason") == "NO_PATH"
                                else "ESCAPE -- pre-filter it")))
    # THE MST WOULD HAVE STOPPED AT THE FIRST FAILURE.  Everything after it is
    # a pair this board has never measured, and saying so is the whole point.
    first_fail = next((i for i, p in enumerate(pairs) if not p["closed"]), None)
    for i, p in enumerate(pairs):
        p["mst_would_have_asked"] = first_fail is None or i <= first_fail
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("--grid", default="auto",
                    help="pitch passed straight to route_maze_batch.py; "
                         "`auto` (the default) is a CENSUS of which pairs are "
                         "even asked, `ladder` actually tries to close them")
    ap.add_argument("--net", action="append", default=[],
                    help="census only these nets (default: every open net "
                         "with at least --min-edges open edges)")
    # A ONE-EDGE NET HAS NOTHING TO CENSUS.  `--partial` and the all-or-nothing
    # MST ask the SAME single pair on it, so running one costs a full gate and
    # returns a row the ladder screen already has.  The bound is on the number
    # the ledger measured, not on a list of names; --min-edges 1 restores the
    # exhaustive sweep.
    ap.add_argument("--min-edges", type=int, default=2,
                    help="skip open nets with fewer than this many open edges "
                         "(default 2: a one-edge net's only pair is the one "
                         "the MST already asked)")
    ap.add_argument("--work", default="w/partial-pairs")
    ap.add_argument("-o", "--out")
    a, extra = ap.parse_known_args()

    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    led = ledger_build(Path(a.board))
    nets = a.net or [e["net"] for e in
                     sorted((e for e in led["nets"]
                             if e["open_edges"] >= a.min_edges),
                            key=lambda e: (e["open_edges"], e["span_mm"]))]
    # THE BOARD'S OWN ZONES NAME THE POUR-SERVED NETS.  Read once, before any
    # router runs, so a plane-served rail costs nothing instead of a search.
    poured = {z[0] for z in zones(Path(a.board)) if z[0]}

    rows, asked, never, pour_served = [], 0, 0, []
    for net in nets:
        if net in poured:
            pour_served.append(net)
            e = next((x for x in led["nets"] if x["net"] == net), {})
            rows.append(dict(net=net, sheet=e.get("sheet"),
                             open_edges=e.get("open_edges"),
                             span_mm=e.get("span_mm"), ran=False, pairs=[],
                             instrument="POUR_SERVED -- this net owns a zone "
                                        "on this board, so it is plane + "
                                        "stitch, not an MST of pairs; "
                                        "--partial is the wrong instrument "
                                        "and the BOARD said so, not a name "
                                        "list"))
            continue
        rep, secs, rc = run_partial(net, a.grid, work, extra)
        e = next((x for x in led["nets"] if x["net"] == net), {})
        base = dict(net=net, sheet=e.get("sheet"),
                    open_edges=e.get("open_edges"), span_mm=e.get("span_mm"),
                    wall_seconds=secs, exit_code=rc)
        if rep is None:
            rows.append(dict(base, ran=False,
                             why="no report written -- see %s.log" % slug(net)))
            continue
        r = (rep.get("routed") or [{}])[0]
        mode = r.get("mode") or ""
        if not mode.startswith("maze"):
            # THE CONFIRMING GUARD.  The zone read above should have caught
            # this net; reaching here means the board's zones and the router's
            # own choice DISAGREE, which is worth a row rather than silence.
            pour_served.append(net)
            rows.append(dict(base, ran=True, mode=mode, pairs=[],
                             instrument="POUR_SERVED_UNEXPECTED -- the router "
                                        "chose %s though this net owns no "
                                        "zone on this board; excluded, and "
                                        "the disagreement is the finding"
                                        % mode,
                             stitch_failures=r.get("failures") or []))
            continue
        ps = pairs_of(r)
        asked += sum(1 for p in ps if p["mst_would_have_asked"])
        never += sum(1 for p in ps if not p["mst_would_have_asked"])
        rows.append(dict(base, ran=True, mode=mode, instrument="MST_OF_PAIRS",
                         islands=r.get("islands"), closed=r.get("closed"),
                         ok=r.get("ok"), pairs=ps))

    corridor = [(r["net"], p) for r in rows for p in r.get("pairs") or []
                if not p["closed"] and p.get("reason") == "NO_PATH"]
    out = dict(
        schema=1, board=str(a.board), board_sha256=led["board_sha256"],
        grid=a.grid, min_open_edges=a.min_edges, what=__doc__.strip(),
        nets_probed=len(rows), pour_served=pour_served,
        pairs_total=asked + never, pairs_the_mst_would_have_asked=asked,
        pairs_never_asked_before=never,
        corridor_pairs=[dict(net=n, a=p["a"], b=p["b"], gap_mm=p.get("gap_mm"),
                             src_escapes=p.get("src_escapes"),
                             dst_escapes=p.get("dst_escapes"),
                             never_asked_before=not p["mst_would_have_asked"])
                        for n, p in corridor],
        nets=rows)
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

    for r in rows:
        print("%-34s isl=%-4s closed=%-4s %s"
              % (r["net"][:34], r.get("islands"), r.get("closed"),
                 r.get("instrument") or r.get("why") or ""))
        for p in r.get("pairs") or []:
            mm = p.get("mm") if p["closed"] else p.get("gap_mm")
            print("    %-6s %-26s <-> %-24s %-9s %-24s %s"
                  % ("CLOSED" if p["closed"] else "FAIL",
                     str(p["a"])[:26], str(p["b"])[:24],
                     "%.3f" % mm if isinstance(mm, float) else mm,
                     p.get("kind") or "", "" if p["mst_would_have_asked"]
                     else "<-- NEVER ASKED BEFORE"))
    print("\n%d nets (%d POUR_SERVED, excluded by the board's own zones), "
          "%d pairs: "
          "%d the MST would have reached, %d NEVER ASKED BEFORE.  %d are "
          "CORRIDOR (NO_PATH) refusals -- the kind D-625 proved pitch-dependent."
          % (len(rows), len(pour_served), asked + never, asked, never,
             len(corridor)))


if __name__ == "__main__":
    main()
