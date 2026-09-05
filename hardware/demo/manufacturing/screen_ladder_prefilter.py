#!/usr/bin/env python3
"""Which open nets can a FINER LATTICE possibly help?  Read-only. -- D-626

THE LADDER IS EXPENSIVE AND MOST OF ITS ANSWERS ARE KNOWN BEFORE IT RUNS.
D-624 laddered eight nets at 20 s to 1539 s a rung; D-626 took `BQ25185_STAT1`
all seven rungs to 0.0125 mm -- 295.8 M cells, ~7.8 GB, 83.2 s -- and it
refused with the SAME sentence on every one of them:

    U11.9: NO LEGAL ESCAPE at >= 0.200 mm

That is not a search that ran out of lattice.  `U11.9`'s widest legal escape is
narrower than its own netclass width, so the obstruction is WIDTH and a finer
pitch cannot manufacture width.  `lattice_advice` already computes exactly that
and calls it `no_lattice_at_any_pitch` -- the ladder had been re-proving, at
2.6x the finest raster this board had ever carried, a fact one read-only pass
already knew.

SO THE DISCRIMINATOR IS THE LATTICE BLOCK -- IN ONE DIRECTION ONLY, AND SAYING
SO IS THE POINT.  D-624's own counter-example is why this is a work-list and
not a verdict: `I2S_LRCLK` and `SPI_B_SCK` ALSO refused on the escape, and a
finer pitch DID unlock them, the wall moving from the pad to the corridor
between 0.0667 and 0.050 mm.  Their lands read CLEAR.  But `NFC_VDD_RF` reads
CLEAR too and refuses `NO_LEGAL_ESCAPE_DST` at every pitch from 0.0667 to
0.020 mm -- D-621 isolated its blocker to `NFC_RFO2`'s north chain, which is
COPPER, not lattice.  So:

    no_lattice_at_any_pitch true   -> the ladder provably cannot help.  The
                                      land's widest legal escape is narrower
                                      than its own netclass width; the answer
                                      is a land licence, a placement move or
                                      `route_local_two_pad`.
    no_lattice_at_any_pitch false  -> the ladder MAY help.  It is not a promise
                                      -- a legal escape can still be occupied
                                      by a neighbour's copper at every pitch.

SOUND, NOT COMPLETE, and it is the exclusion side that has to be sound.  This
filter never drops an EDGE a ladder could have reached: across every net this
project has laddered, each one whose wall MOVED with pitch reads false, and the
only two that read true -- `ACC_5V_LX` (`U21.5`, five rungs) and
`BQ25185_STAT1` (`U11.9`, seven rungs to 0.0125 mm) -- refused with the
identical sentence on every rung.  It admits edges the ladder will not help;
that costs a run, and the converse would cost a route.

AND THE UNIT OF EXCLUSION IS THE ISLAND, NOT THE NET.  The router's own words
are `NO_LEGAL_ESCAPE_SRC: no legal escape on the source ISLAND`, and a net may
hold one island nothing can launch and others that are perfectly ordinary:
`BQ25185_STAT1` is exactly that -- `U11.9` alone and unlaunchable on one
island, while `{R127.2,TP6.1}` and `{U2.9}` are a plain 18.517 mm `NO_PATH`
corridor question with twenty source escapes.  Excluding that NET would hide a
live edge behind a dead one.  So an island is excluded when EVERY one of its
pads is unlaunchable, an edge is excluded when either of its islands is, and
the ladderable remainder is counted in EDGES.  Under the all-or-nothing MST
those remainders are unreachable anyway -- the first failing pair ends the
transaction -- so a net with any excluded island is reported `--partial`, which
is the only mode that can ask its surviving edges at all.
"""
import argparse
import json
from pathlib import Path

from route_maze_batch import BOARD, lattice_advice
from routing_ledger import generate as ledger_build

GRID_PROBE_NM = 100000          # lattice_advice reads margins, not this pitch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    led = ledger_build(Path(a.board))
    open_nets = sorted((e for e in led["nets"] if e["open_edges"] > 0),
                       key=lambda e: (e["open_edges"], e["span_mm"]))

    rows = []
    for e in open_nets:
        adv = lattice_advice(Path(a.board), [e["net"]], GRID_PROBE_NM)
        n = adv["nets"].get(e["net"], {})
        dead_lands = set(n.get("unlaunchable_lands") or [])

        # ISLAND-LEVEL ACCOUNTING.  The ledger's `groups` are the net's copper
        # islands as pad lists; the router escapes from an ISLAND, so an island
        # is dead only when EVERY pad on it is unlaunchable.  A net's open
        # edges are `islands - 1`; each edge incident to a dead island is
        # unreachable at any pitch, and the rest are the ladder's real work.
        islands = [[p.split("@")[0] for p in g] for g in e.get("groups", [])]
        dead = [i for i, g in enumerate(islands)
                if g and all(p in dead_lands for p in g)]
        live_islands = len(islands) - len(dead)
        # Edges among the live islands only; a spanning tree over `k` islands
        # has `k - 1` edges, and zero when nothing is left to join.
        ladderable_edges = max(live_islands - 1, 0)
        excluded_edges = e["open_edges"] - ladderable_edges

        rows.append(dict(
            net=e["net"], sheet=e["sheet"], open_edges=e["open_edges"],
            pads=e["pads"], span_mm=e["span_mm"],
            verdict=n.get("verdict"),
            required_lattice_mm=n.get("required_lattice_mm"),
            too_coarse=n.get("too_coarse"),
            unlaunchable_lands=sorted(dead_lands),
            no_lattice_at_any_pitch=bool(n.get("no_lattice_at_any_pitch")),
            islands=len(islands),
            dead_islands=[islands[i] for i in dead],
            ladderable_edges=ladderable_edges,
            excluded_edges=excluded_edges,
            # UNDER THE ALL-OR-NOTHING MST A SURVIVING EDGE IS STILL
            # UNREACHABLE: the first failing pair ends the whole transaction.
            needs_partial=bool(dead) and ladderable_edges > 0,
            why=("%d of %d edges sit behind island(s) with no legal escape at "
                 "ANY pitch (%s); a finer lattice cannot manufacture width -- "
                 "land licence / placement / route_local_two_pad"
                 % (excluded_edges, e["open_edges"],
                    ", ".join(sorted(dead_lands)))
                 if dead else
                 "every island has a launchable land; refinement can reach "
                 "all %d edges" % e["open_edges"])))

    out = dict(
        schema=1, board=str(a.board),
        what="D-626 -- the ladder's work-list, read-only, counted in EDGES.  "
             "`lattice_advice`'s `no_lattice_at_any_pitch` separates an escape "
             "refusal a finer pitch CAN lift from one it provably cannot; "
             "D-626 tested the invariant side to 0.0125 mm / 295.8 M cells on "
             "/BQ25185_STAT1.  Exclusion is per ISLAND, because a net may hold "
             "one island nothing can launch and others that are ordinary.",
        open_nets=len(rows),
        open_edges=sum(r["open_edges"] for r in rows),
        ladderable_nets=sum(1 for r in rows if r["ladderable_edges"]),
        ladderable_edges=sum(r["ladderable_edges"] for r in rows),
        excluded_edges=sum(r["excluded_edges"] for r in rows),
        nets_needing_partial=[r["net"] for r in rows if r["needs_partial"]],
        nets=rows)
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

    print("%-3s %-3s %-3s %-8s %-44s %-12s %s"
          % ("ed", "ldr", "exc", "partial", "net", "verdict", "unlaunchable"))
    for r in rows:
        print("%-3d %-3d %-3d %-8s %-44s %-12s %s"
              % (r["open_edges"], r["ladderable_edges"], r["excluded_edges"],
                 "PARTIAL" if r["needs_partial"] else "",
                 r["net"][:44], r["verdict"],
                 ",".join(r["unlaunchable_lands"])))
    print("\n%d open nets / %d open edges: LADDER %d edges across %d nets, "
          "EXCLUDE %d edges as lattice-invariant.  %d net(s) need --partial "
          "to reach a live edge hidden behind a dead island."
          % (out["open_nets"], out["open_edges"], out["ladderable_edges"],
             out["ladderable_nets"], out["excluded_edges"],
             len(out["nets_needing_partial"])))


if __name__ == "__main__":
    main()
