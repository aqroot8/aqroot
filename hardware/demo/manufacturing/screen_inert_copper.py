#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: which routed copper of a POUR-OWNING net is INERT?

D-646 found the `+3V3` / `U4` wall by asking, per OBJECT, whose copper stands in
the corridor -- and the answer was three ordinary `B.Cu` `GND` tracks that
DUPLICATE A CONNECTION THE POUR ALREADY MAKES.  Removing all three left the
board's own measurements untouched, field for field: raw ratsnest 58 -> 58,
every per-net open-edge count identical, KiCad's DRC profile identical, and
`pour_bond_guard.py` emitting the SAME 49 tubes with the same ends, islands,
areas and lengths.  They were legacy routed copper doing nothing but blocking.

That is not a property of those three tracks.  A pour-owning net on this board
carries hundreds of routed objects laid before its plane existed or beside it,
and EVERY ONE of them is a hard obstacle to every proposer here -- `maze3d`
rasterises a track and does not rasterise a zone fill, precisely because a pour
is repairable and a track is not.  So a track that the pour has since made
redundant costs the router everything and the board nothing, and until this
screen there was no way to tell one from the other except by hand.

WHAT IT ASKS, PER TRACK CHAIN, AND WHY IT IS THE RIGHT QUESTION:

  ONE FILLED ISLAND of the chain's own net, on the chain's own OUTER layer,
  must contain BOTH ENDS.  That is the connectivity claim and it is read off
  KiCad's own fill, not asserted -- if no island holds both, the copper is
  carrying a connection the pour does not.

  THE WIDEST POUR PATH between those ends must be at least as wide as the
  chain.  `pour_bond_guard.geodesic` erodes from a ceiling down and returns the
  first radius the whole path survives, so `2 * radius` is the narrowest place
  on the best conductor the pour offers.  Below the chain's own width the
  removal would be a DERATING, which is a decision somebody takes deliberately.

Three verdicts, and only the first is an offer:

  INERT           the pour already joins the ends, at least as wide.  Removable
                  under `--detour-spec` `"relay": false`, which is the SAME
                  measurement the gate re-runs as `inert_removal_priced` before
                  it will promote.
  DERATING        the pour joins the ends but NARROWER than the copper.  Not
                  refused here -- reported, with the number, because a return
                  fragment 0.05 mm short of its own netclass width is a
                  different conversation from one that is half of it.
  LOAD_BEARING    no filled island of that net on that layer holds both ends.
                  This copper is the connection.

WHAT `INERT` DOES NOT MEAN, STATED BEFORE THE NUMBER IS QUOTED.  It means the
pour joins the chain's TWO ENDS, at least as wide.  It does NOT mean the chain
is free of every other consequence, and on this board the sweep is lopsided
enough that saying so matters: the first board-wide `GND` census reads 207 of
207 `B.Cu` chains INERT, 228.523 mm, because that net's `B.Cu` pour is one
enormous body and almost nothing on it is the only path between anything.  Two
things this screen cannot see:

  * THE RETURN LOOP.  A short track from a decoupling cap to a stitching via
    buys a smaller loop AREA than the same connection taken the long way round
    a pour, and area is not width.  For a decap that matters and this screen
    does not price it.
  * THE FILL ITSELF.  Removing same-net track does not move a zone's knockouts,
    which is why the fill is stable here -- but a chain whose ends are pads of
    parts that also anchor the pour is a different question from a chain
    between two vias.

So a row here is a CANDIDATE.  D-646 removed three of them and proved those
three the whole way -- KiCad's own refill and DRC, `routing_ledger.py`, and a
`pour_bond_guard.py` re-emission that came back with the SAME 49 tubes -- and
the gate re-prices whatever is claimed before it will promote it.

NOTHING IS WRITTEN.  The board is opened read-only and its sha256 is reported.
A chain reported INERT is a licence to write a `relay: false` detour and spend
a gate run, not a promise -- the gate re-prices it on the authority and the
board's own PP1-PP4 still judges whatever the run then lays.

    python3 screen_inert_copper.py GND [--layer B.Cu] [--window x0,y0,x1,y1]
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

OUTER = ("F.Cu", "B.Cu")


def chains(board, net, layer_name, window):
    """Maximal simple chains of this net's tracks on this layer.

    A chain is what `--detour-spec` can name: consecutive collinear-or-not
    segments meeting end to end, no tee, no via and no pad on an interior
    junction -- the same unit `route_maze_batch.chain_ends` will re-prove
    before it removes anything.  Splitting anywhere else would report a
    removal nobody may execute.
    """
    import pcbnew
    lid = board.GetLayerID(layer_name)
    segs, deg = [], {}

    def key(p):
        return (int(p.x), int(p.y))

    for t in board.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != net:
            continue
        if t.GetLayer() != lid:
            continue
        a, b = key(t.GetStart()), key(t.GetEnd())
        if window and not all(window[0] <= p[0] <= window[2]
                              and window[1] <= p[1] <= window[3]
                              for p in (a, b)):
            continue
        segs.append((a, b, int(t.GetWidth())))
        for p in (a, b):
            deg[p] = deg.get(p, 0) + 1

    # a junction is BRANCHING if anything else of this net meets it
    blocked = set()
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.GetClass() == "PCB_VIA":
            blocked.add(key(t.GetStart()))
    for f in board.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetname() != net:
                continue
            blocked.add(key(pad.GetPosition()))
    for t in board.GetTracks():
        if (t.GetClass() == "PCB_TRACK" and t.GetNetname() == net
                and t.GetLayer() != lid):
            blocked.add(key(t.GetStart()))
            blocked.add(key(t.GetEnd()))

    adj = {}
    for i, (a, b, w) in enumerate(segs):
        adj.setdefault(a, []).append(i)
        adj.setdefault(b, []).append(i)

    seen, out = set(), []
    for i, (a, b, w) in enumerate(segs):
        if i in seen:
            continue
        run, ends, width_ok = [i], [], True
        seen.add(i)
        for start in (a, b):
            node, prev = start, i
            while (deg.get(node, 0) == 2 and node not in blocked):
                nxt = [k for k in adj[node] if k != prev and k not in seen]
                if not nxt:
                    break
                prev = nxt[0]
                seen.add(prev)
                run.append(prev)
                p, q, _ = segs[prev]
                node = q if p == node else p
            ends.append(node)
        widths = {segs[k][2] for k in run}
        out.append(dict(
            tracks=[dict(layer=layer_name,
                         a_mm=[round(segs[k][0][0] / 1e6, 4),
                               round(segs[k][0][1] / 1e6, 4)],
                         b_mm=[round(segs[k][1][0] / 1e6, 4),
                               round(segs[k][1][1] / 1e6, 4)],
                         width_mm=round(segs[k][2] / 1e6, 3)) for k in run],
            n=len(run), width_nm=max(widths), one_width=(len(widths) == 1),
            a_mm=[round(ends[0][0] / 1e6, 4), round(ends[0][1] / 1e6, 4)],
            b_mm=[round(ends[1][0] / 1e6, 4), round(ends[1][1] / 1e6, 4)],
            mm=round(sum(((segs[k][1][0] - segs[k][0][0]) ** 2
                          + (segs[k][1][1] - segs[k][0][1]) ** 2) ** 0.5
                         for k in run) / 1e6, 4)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--layer", action="append", default=[],
                    help="outer copper layer; default both")
    ap.add_argument("--window", help="x0,y0,x1,y1 in mm; a chain counts only "
                                     "when BOTH endpoints of every segment "
                                     "lie inside it")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    import route_maze_batch as rmb

    win = None
    if a.window:
        win = tuple(int(round(float(v) * 1e6)) for v in a.window.split(","))
    if not a.board.exists():
        raise SystemExit("no such board: %s" % a.board)
    board = pcbnew.LoadBoard(str(a.board.resolve()))
    layers = a.layer or list(OUTER)
    # WHICH (net, layer) PAIRS EVEN OWN A FILLED POUR.  Without this every
    # chain on a layer the net has no pour on reads `LOAD_BEARING`, which is
    # TRUE and useless -- it says "the pour does not replace this" about a
    # pour that does not exist.  `GND` on this board owns `B.Cu` and no
    # `F.Cu`, so 92 of the first census's 299 chains were that sentence.
    poured = set()
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lid in z.GetLayerSet().CuStack():
            ln = board.GetLayerName(lid)
            if ln in OUTER and z.GetFilledPolysList(lid).OutlineCount():
                poured.add((z.GetNetname(), ln))
    rows = []
    for net in a.nets:
        for L in layers:
            found = chains(board, net, L, win)
            if not found:
                continue
            if (net, L) not in poured:
                rows += [dict(net=net, layer=L, verdict="NO_POUR_ON_THIS_LAYER",
                              chain_mm=c["mm"], segments=c["n"],
                              one_width=c["one_width"],
                              width_mm=round(c["width_nm"] / 1e6, 3),
                              a_mm=c["a_mm"], b_mm=c["b_mm"],
                              price=dict(ok=False,
                                         reason="NO_FILLED_POUR_OF_THIS_NET_"
                                                "ON_THIS_LAYER"),
                              tracks=c["tracks"]) for c in found]
                continue
            priced = rmb.inert_removal_price(
                a.board,
                [dict(net=net, layer=L, a_mm=c["a_mm"], b_mm=c["b_mm"],
                      was_mm=c["mm"], width_nm=c["width_nm"]) for c in found])
            for c, p in zip(found, priced):
                verdict = ("LOAD_BEARING" if (p.get("reason") or "").startswith("NO_")
                           else ("INERT" if p.get("ok") else "DERATING"))
                rows.append(dict(net=net, layer=L, verdict=verdict,
                                 chain_mm=c["mm"], segments=c["n"],
                                 one_width=c["one_width"],
                                 width_mm=round(c["width_nm"] / 1e6, 3),
                                 a_mm=c["a_mm"], b_mm=c["b_mm"],
                                 price=p, tracks=c["tracks"]))
    tally = {}
    for r in rows:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    doc = dict(schema=1, board=str(a.board),
               board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),
               nets=list(a.nets), layers=layers, window_mm=a.window,
               summary=dict(chains=len(rows), verdicts=tally,
                            inert_mm=round(sum(r["chain_mm"] for r in rows
                                               if r["verdict"] == "INERT"), 3)),
               chains=sorted(rows, key=lambda r: (-r["chain_mm"], r["net"])))
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(json.dumps(doc["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
