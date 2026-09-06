#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: an open edge is not worth what it costs to route.

`routing_ledger.py` is the authority on HOW MANY edges are open and it says
nothing about WHICH ONE MATTERS.  Thirty-eight edges have been worked one at a
time, cheapest first, for eighteen decisions -- and cheapest-first is only the
right order if every edge buys the same thing.

It does not.  An open edge on a two-pin test point costs the board a test
point.  An open edge on the `I2C` land of a `PCAL9535APW` costs the board every
signal that expander carries, because an I2C GPIO expander has exactly one
control path and it is the bus.  This screen prices that difference with no
editorial map at all:

    for every open retained edge, name the PART each orphan land sits on, and
    count the OTHER nets that part carries.

  OE1  THE SET IS THE ROUTER'S, FILTERED BY THE BOARD'S OWN POPULATION.  Open
       edges, islands and lands are read from `maze3d.net_islands` over the
       authoritative board -- the same grouping the router joins and the gate
       scores.  `net_islands` has no population model and islands every pad,
       which is how D-610 found `U13.3` proposed, searched and refused after
       being paid for; so any land on a footprint the BOARD itself flags DNP is
       reported with `fitted: false` and kept OUT of every total.

  OE2  THE COUNT IS MECHANICAL.  `carries` is every distinct net on the same
       footprint, minus this one, minus the power and ground rails the part
       needs to exist at all.  Nothing is weighted and no feature is named:
       the part's own `Value` is reported so a reader can judge what those
       nets are worth without this file having an opinion.

  OE3  IT IS A PRICE, NOT A PROOF.  A part whose interface land is open is
       ELECTRICALLY UNREACHABLE only if that land is its sole control path.
       `SOLE_PATH` names the device values where that is structurally true --
       an I2C-only device has no second road -- and everything else is reported
       with the count and no claim.

    python3 screen_open_edge_cost.py [--board B] [-o OUT]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# OE2.  A part needs its rails to exist; they are not what its interface buys.
RAILS = ("GND", "+3V3", "+5V")

# OE3.  Parts whose ONLY control path is the net named.  This is a structural
# claim about the device, not a routing one: a PCAL9535A has no second road to
# its 16 IO, and a MAX17048 fuel gauge and a TCA4307 hot-swap buffer are the
# same shape.  Anything not named here is reported with a count and no claim.
SOLE_PATH = {
    "PCAL9535APW": ("/I2C_SCL_INT", "/I2C_SDA_INT"),
    "MAX17048": ("/I2C_SCL_INT", "/I2C_SDA_INT"),
    "TCA4307DGKR": ("/I2C_SCL_INT", "/I2C_SDA_INT"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import maze3d as mz

    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    board = qb.b

    by_ref = {}
    for f in board.GetFootprints():
        ref = f.GetReference()
        nets = {p.GetNetname() for p in f.Pads() if p.GetNetname()}
        by_ref[ref] = dict(value=f.GetValue(), nets=nets,
                           fitted=not bool(f.IsDNP()))

    open_nets = []
    for net in sorted({p.GetNetname() for f in board.GetFootprints()
                       for p in f.Pads() if p.GetNetname()}):
        try:
            islands = mz.net_islands(qb, net)
        except Exception:
            continue
        if len(islands) > 1:
            open_nets.append((net, islands))

    rows = []
    for net, islands in open_nets:
        body = max(islands, key=len)
        for isl in islands:
            if isl is body:
                continue
            for p in isl:
                ref = p["ref"].split(".")[0]
                info = by_ref.get(ref, dict(value="?", nets=set(),
                                            fitted=True))
                carries = sorted(n for n in info["nets"]
                                 if n != net and n not in RAILS
                                 and not n.startswith("unconnected-"))
                sole = SOLE_PATH.get(info["value"])
                rows.append(dict(
                    net=net, land=p["ref"], ref=ref, value=info["value"],
                    fitted=bool(info["fitted"]),
                    carries=len(carries), carries_nets=carries,
                    sole_path=bool(sole and net in sole),
                    at=(round(p["x"] / 1e6, 3), round(p["y"] / 1e6, 3))))
    rows.sort(key=lambda r: (-r["carries"], r["net"], r["land"]))
    fitted_rows = [r for r in rows if r["fitted"]]

    dead_parts = sorted({r["ref"] for r in fitted_rows if r["sole_path"]})
    dead_nets = sorted({n for r in fitted_rows if r["sole_path"]
                        for n in r["carries_nets"]})
    out = dict(schema=1, board=str(a.board), board_sha256=sha,
               question=("for every open retained edge, which PART does the "
                         "orphan land sit on and how many OTHER nets does that "
                         "part carry"),
               open_nets=len(open_nets),
               orphan_lands=len(fitted_rows),
               orphan_lands_unfitted=len(rows) - len(fitted_rows),
               sole_path_parts=dead_parts,
               sole_path_nets=dead_nets,
               sole_path_net_count=len(dead_nets),
               rails_excluded=list(RAILS),
               sole_path_values=sorted(SOLE_PATH),
               limits=("OE3: a count is a PRICE, not a proof; only the "
                       "sole_path rows claim the part is unreachable"),
               rows=rows)
    text = json.dumps(out, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n")
    else:
        print(text)
    print(" %d open nets, %d fitted orphan lands (%d unfitted, excluded); "
          "%d parts UNREACHABLE by their sole control path, stranding %d nets"
          % (len(open_nets), len(fitted_rows), len(rows) - len(fitted_rows),
             len(dead_parts), len(dead_nets)),
          file=sys.stderr)
    for r in fitted_rows[:14]:
        print("  %-34s %-9s %-14s carries %2d%s"
              % (r["net"], r["land"], r["value"], r["carries"],
                 "   SOLE CONTROL PATH" if r["sole_path"] else ""),
              file=sys.stderr)


if __name__ == "__main__":
    main()
