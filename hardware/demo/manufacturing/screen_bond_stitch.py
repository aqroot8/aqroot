#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: which guarded pad can own its bond outright?

`screen_bond_redundancy.py` (D-599) asked an ISLAND question -- how many legal
barrel sites lie inside a guarded island's filled copper -- and answered it in
the thousands.  That answer is not the one the board needs, and D-599's own
reasoning says why: a foreign track SPLITS an island, so a barrel dropped
somewhere inside it lands on one side of the cut and every pad on the other side
is orphaned exactly as before.  Redundancy that survives the cut has to hang off
the PAD.

So this screen asks the pad question instead:

    for every pad a pour-bond guard tube protects, can `maze3d.stitch_pad`
    give that pad its own escape, its own short run and its own through
    barrel down to the same net's inner-layer plane?

A pad that can is a pad whose connection stops depending on pour copper at all,
and the tube that was protecting it stops being load-bearing.  A pad that cannot
-- `pour_bond_guard.py`'s own `NO_ESCAPE` class, and the pads whose window holds
no legal barrel -- keeps its guard, and the honest total is reported both ways.

WHAT IS MEASURED, NOT ASSUMED

  * THE EMITTER IS THE PROMOTER'S.  `maze3d.bond_pads` is what a gated
    `route_maze_batch.py --bond-pad` transaction runs, so a pad reported
    BONDABLE here is one the gate would be offered, at the same contract, the
    same `.kicad_dru` overlay and the same `verify_laid` proof.
  * THE GUARD IS HONOURED.  Foreign tubes bind the stitch exactly as they bind
    any other copper; the net's own tubes do not, because the tube IS its
    copper.
  * NOTHING IS WRITTEN.  The board is loaded, mutated in memory and dropped.
    The full-board gate remains the only thing that promotes copper.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def guard_anchor_pads(spec):
    """{net: [pad ref, ...]} -- every pad end of every live tube, in order."""
    out, seen = {}, set()
    for g in spec.get("guards", ()):
        if not g.get("ok"):
            continue
        for e in g["ends"]:
            if e == "via" or "." not in e:
                continue
            key = (g["net"], e)
            if key in seen:
                continue
            seen.add(key)
            out.setdefault(g["net"], []).append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--guard", type=Path, required=True)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--max-mm", type=float, default=8.0)
    ap.add_argument("--net", action="append", default=[],
                    help="restrict to these pour nets")
    ap.add_argument("--bonded-from", type=Path, action="append", default=[],
                    help="a route_maze_batch.py run report: the pads it "
                         "actually BONDED are counted free without being "
                         "re-stitched.  Repeatable; this is how a promoted "
                         "transaction's own record, rather than a re-derivation "
                         "of it, decides which tubes are already retired")
    ap.add_argument("--emit-guard", type=Path,
                    help="write the input guard spec with every RETIRABLE tube "
                         "removed -- the spec a run that also carries the "
                         "matching --bond-pad set should be given")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for)

    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = json.loads(a.guard.read_text())
    want = guard_anchor_pads(spec)
    if a.net:
        want = {k: v for k, v in want.items() if k in set(a.net)}

    # A pad a PROMOTED transaction already bonded is free, and asking the
    # emitter about it again would only propose a SECOND barrel.  The record is
    # the gate's own report, so this is provenance and not an assertion.
    already = {}
    for path in a.bonded_from:
        run = json.loads(path.read_text())
        for det in ((run.get("bonds") or {}).get("detail") or ()):
            for b in det.get("bonds", ()):
                already.setdefault(det["net"], set()).add(b["pad"])
    for net in list(want):
        want[net] = [r for r in want[net] if r not in already.get(net, ())]

    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)

    nets = []
    for net in sorted(want):
        c = net_contract(qb.b, net)
        if not c["known_class"]:
            nets.append(dict(net=net, ok=False, reason="UNKNOWN_NETCLASS"))
            continue
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        field = mz.Field(qb, net, c["width"], c["clr"], c["clr"],
                         c["via_dia"], c["via_drill"], G=a.grid,
                         layers=layers, guard=guard_for(spec, net))
        r = mz.bond_pads(qb, net, field, want[net], max_mm=a.max_mm)
        r["contract"] = {k: c[k] for k in ("netclass", "width", "clr",
                                           "via_dia", "via_drill")}
        nets.append(r)
        for b in r["bonds"]:
            print("  BOND   %-8s %-10s %s mm  via %s"
                  % (net, b["pad"], b["mm"], b["via_xy"]),
                  file=sys.stderr, flush=True)
        for f in r["failures"]:
            print("  WALL   %-8s %-10s %-18s %s"
                  % (net, f.get("pad"), f.get("reason"),
                     str(f.get("why"))[:70]), file=sys.stderr, flush=True)

    bondable = {r["net"]: sorted(b["pad"] for b in r.get("bonds", ()))
                for r in nets if r.get("bonds")}
    free_pads = {n: sorted(set(bondable.get(n, ())) | already.get(n, set()))
                 for n in set(bondable) | set(already)}
    # A tube is RETIRABLE when BOTH its ends stop depending on pour copper: a
    # pad end that bonds, or a `via` end, which is already a barrel.
    def free(net, end):
        return end == "via" or end in set(free_pads.get(net, ()))
    tubes = [g for g in spec.get("guards", ()) if g.get("ok")]
    retirable = [g for g in tubes if all(free(g["net"], e) for e in g["ends"])]
    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        guard=str(a.guard),
        guard_sha256=hashlib.sha256(a.guard.read_bytes()).hexdigest(),
        grid=a.grid, max_mm=a.max_mm,
        summary=dict(
            pads_requested=sum(len(v) for v in want.values()),
            pads_bondable=sum(len(v) for v in bondable.values()),
            pads_already_bonded=sum(len(v) for v in already.values()),
            tubes=len(tubes), tubes_retirable=len(retirable)),
        bondable_pads=bondable,
        already_bonded_pads={k: sorted(v) for k, v in already.items()},
        bonded_from=[str(x) for x in a.bonded_from],
        retirable_tubes=[dict(net=g["net"], lkey=g["lkey"], zone=g["zone"],
                              island=g["island"], ends=g["ends"])
                         for g in retirable],
        nets=nets)
    if a.emit_guard:
        drop = {(g["net"], g["zone"], g["island"], tuple(g["ends"]))
                for g in retirable}
        out = dict(spec)
        out["guards"] = [g for g in spec.get("guards", ())
                         if (g.get("ok") and
                             (g["net"], g["zone"], g["island"],
                              tuple(g["ends"])) in drop) is False]
        live = [g for g in out["guards"] if g.get("ok")]
        out["summary"] = dict(spec.get("summary", {}), guards=len(live),
                              mm=round(sum(g["mm"] for g in live), 3),
                              points=sum(len(g["points"]) for g in live))
        out["retired_tubes"] = doc["retirable_tubes"]
        out["derived_from"] = dict(guard=str(a.guard),
                                   guard_sha256=doc["guard_sha256"],
                                   screen=str(a.out) if a.out else None,
                                   bonded_from=doc["bonded_from"])
        out["retirement"] = (
            "A tube is dropped here when BOTH its ends stop depending on pour "
            "copper -- a pad a promoted transaction already bonded, or one this "
            "screen proved `maze3d.bond_pads` can bond.  BOTH ends, never one: "
            "dropping an edge whose far end is still pour-dependent would "
            "strand that end, and because the guard's tubes are a SPANNING TREE "
            "over the island's pads, the both-ends rule leaves every "
            "still-dependent pad joined by GUARDED tubes to a component whose "
            "boundary pad is bonded.  The guard has always been a PRE-FILTER "
            "and never the authority: gate clause 4 measures whole-board open "
            "edges after the real refill and after --repair-planes.  Feed this "
            "spec ONLY to a run that also carries the matching --bond-pad set, "
            "or to one measured on a board that already carries those bonds.")
        a.emit_guard.write_text(
            json.dumps(out, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8")

    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
