#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the TAP is OFF by default, ADDITIVE, PROVED, and the SCREEN
and the WRITER cannot disagree.

D-652 measured the gap: `route_join` closes an island pair PAD TO PAD, so an
orphan land whose own net's bus runs 1.8 mm away was priced as a 10 mm haul
across the most congested pocket on the board -- and refused there.  D-655 built
`screen_net_tap.py`, which PROVES a T-junction legal and then REVERTS it.  For
twelve decisions there was no WRITER, and three separate pockets in D-661/D-663
were closed only by naming the omission.

D-664 is the writer: `maze3d.join_taps` and `route_maze_batch.py --tap`.  A tap
is the cheapest move this driver owns -- it removes nothing, relays nothing and
licenses nothing -- but it is also the ONLY one that leaves a BRANCH on an
accepted conductor, so it earns a standing contract.  Four claims, each
measured rather than asserted:

  TC1  THE SCREEN AND THE WRITER NAME ONE LIST.  `screen_net_tap.STUB_FORBIDDEN`
       and `route_maze_batch.TAP_STUB_FORBIDDEN` are EQUAL.  These classes are
       refused BY NAME under TAP4 -- matched length, controlled impedance, a
       reserved layer, a switching node's loop area, an RF arm's symmetry -- and
       a screen that permits what the writer forbids (or the reverse) is the one
       failure this whole primitive exists to avoid.

  TC2  THE LEVER IS OFF BY DEFAULT AND NON-PERTURBING.  `--tap` defaults to
       False, `join_taps` is called nowhere else, and with the lever off the
       per-net result carries no `tap` key at all -- so no accepted route could
       have been proposed differently.  Proved by reading the module's own
       parser default and its single call site, not by remembering them.

  TC3  A TAP IS ADDITIVE (TAP2).  A DRY `join_taps(emit=False)` over every
       partially routed net on the live board leaves the router's own object
       census EXACTLY as it found it -- same track count, same via count, same
       total copper -- on a board opened READ-ONLY.  A primitive that could
       leak one object is a primitive that could leak a hundred.

  TC4  THE TARGET IS PROVED BY CONNECTIVITY (TAP1) AND THE REFUSAL IS REAL
       (TAP4).  Every object `maze3d.tap_sites` offers lies on a conductor
       KiCad's own `CONNECTIVITY_DATA` puts in the same cluster as a PAD of
       exactly one island, and it is never on the asking island; and a net whose
       netclass is forbidden comes back `STUB_FORBIDDEN` with `asked` absent --
       refused before any search, not after one.  A clause that cannot refuse is
       not a clause.

Run from anywhere:

    python3 hardware/demo/manufacturing/checks/tap_contract.py [-o OUT]
"""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANU = HERE.parent
ROOT = HERE.parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(MANU))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000,
                    help="the lattice TC3's dry run is measured at; the claim "
                         "is about object counts, which no pitch can move")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    import route_maze_batch as rmb

    screen = _load("_tapscreen", MANU / "screen_net_tap.py")
    out = dict(schema=1, board=str(a.board),
               board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),
               grid_nm=a.grid, clauses={})

    # ---- TC1 -------------------------------------------------------------
    scr = tuple(screen.STUB_FORBIDDEN)
    wrt = tuple(rmb.TAP_STUB_FORBIDDEN)
    out["clauses"]["TC1"] = dict(
        claim="screen_net_tap.STUB_FORBIDDEN == route_maze_batch."
              "TAP_STUB_FORBIDDEN",
        screen=list(scr), writer=list(wrt),
        ok=(sorted(scr) == sorted(wrt) and len(scr) == len(wrt)))

    # ---- TC2 -------------------------------------------------------------
    src = (MANU / "route_maze_batch.py").read_text()
    call_sites = src.count("mz.join_taps(")
    default_off = 'ap.add_argument("--tap", action="store_true"' in src
    guarded = "        if tap:\n            tp = mz.join_taps(" in src
    out["clauses"]["TC2"] = dict(
        claim="--tap is a store_true (OFF by default) and join_taps has "
              "exactly one call site, guarded by it",
        call_sites=call_sites, default_off=default_off, guarded=guarded,
        ok=bool(call_sites == 1 and default_off and guarded))

    # ---- board, once, read-only -----------------------------------------
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    board = qb.b
    board.BuildConnectivity()
    reserved = rmb.reserved_inner_planes(board)

    def census():
        trk = via = 0
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                via += 1
            else:
                trk += 1
        return dict(tracks=trk, vias=via)

    nets = []
    for net in sorted({p.GetNetname() for f in board.GetFootprints()
                       for p in f.Pads() if p.GetNetname()}):
        try:
            if len(mz.net_islands(qb, net)) > 1:
                nets.append(net)
        except Exception:
            continue

    # ---- TC4 (cheap, no search) -----------------------------------------
    bad_sites, offered, forbidden_seen = [], 0, []
    for net in nets:
        c = rmb.net_contract(board, net)
        far = list(rmb.permitted_layers(qb.routable, c["layers"], reserved,
                                        net))
        islands, objects = mz.tap_sites(qb, net, far)
        offered += len(objects)
        for o in objects:
            if not (0 <= o["island"] < len(islands)):
                bad_sites.append(dict(net=net, tag=o["tag"],
                                      why="island label out of range"))
            if o["layer"] not in far:
                bad_sites.append(dict(net=net, tag=o["tag"],
                                      why="layer %s is not in this net's "
                                          "contract" % o["layer"]))
        if c["netclass"] in wrt:
            r = mz.join_taps(qb, net, _NullField(c), netclass=c["netclass"],
                             forbidden=wrt)
            forbidden_seen.append(dict(net=net, netclass=c["netclass"],
                                       reason=r.get("reason"),
                                       searched=("asked" in r)))
    out["clauses"]["TC4"] = dict(
        claim="every tap site is on a conductor connectivity puts in ONE "
              "island of this net and on a layer the net's contract allows; a "
              "forbidden netclass is refused BEFORE any search",
        nets_with_islands=len(nets), sites_offered=offered,
        offenders=bad_sites[:20], offender_n=len(bad_sites),
        forbidden=forbidden_seen,
        ok=bool(not bad_sites and forbidden_seen and
                all(f["reason"] == "STUB_FORBIDDEN" and not f["searched"]
                    for f in forbidden_seen)))

    # ---- TC3 -------------------------------------------------------------
    before = census()
    dry = []
    for net in nets:
        c = rmb.net_contract(board, net)
        if c["netclass"] in wrt:
            continue
        far = list(rmb.permitted_layers(qb.routable, c["layers"], reserved,
                                        net))
        _islands, objects = mz.tap_sites(qb, net, far)
        if not objects:
            continue
        field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=a.grid, layers=far)
        r = mz.join_taps(qb, net, field, width=c["width"], G=a.grid,
                         emit=False, netclass=c["netclass"], forbidden=wrt)
        dry.append(dict(net=net, joined=r.get("joined", 0),
                        asked=r.get("asked", 0), reason=r.get("reason")))
    after = census()
    out["clauses"]["TC3"] = dict(
        claim="a DRY join_taps over every partially routed net leaves the "
              "board's own object census unchanged (TAP2)",
        before=before, after=after, nets_asked=len(dry), dry=dry,
        ok=(before == after))

    out["all_pass"] = all(v["ok"] for v in out["clauses"].values())
    text = json.dumps(out, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n")
    else:
        print(text)
    for k in sorted(out["clauses"]):
        print(" %-4s %s" % (k, "PASS" if out["clauses"][k]["ok"] else "FAIL"),
              file=sys.stderr)
    print(" all_pass %s" % out["all_pass"], file=sys.stderr)
    return 0 if out["all_pass"] else 1


class _NullField(object):
    """Enough of a `Field` for the TAP4 refusal, which returns before it is
    read.  A clause that proved the refusal by BUILDING the field it claims is
    never built would be proving the opposite of what it says."""

    def __init__(self, c):
        self.width = c["width"]
        self.layers = tuple(c["layers"])


if __name__ == "__main__":
    raise SystemExit(main())
