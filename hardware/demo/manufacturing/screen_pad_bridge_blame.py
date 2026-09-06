#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: the pad bridge names ONE object.  Ask it again.

D-647 read `maze3d.pad_bridge`'s `why` field board-wide and found a free
one-object blame report nobody had spent -- "19 refused with a REASON, every
one `UNPROVED_GEOMETRY` naming the coordinate and NET of a SINGLE blocking
track" -- and stated its own limit in the same breath:

    "Its limit is now stated too: it names the FIRST object the stroke meets,
     not the only one."

That limit is the whole difference between a hint and a transaction.  A pair
whose first named blocker is an ordinary signal track reads like a one-relay
closure; if the SECOND object behind it is the part's own neighbouring land,
there is no transaction at all and the relay is wasted.  Nothing in the
repository could tell those two apart without a gate run per guess.

THIS SCREEN ASKS THE QUESTION TO EXHAUSTION.  For one land pair at one rung it
holds the named object out, asks `pad_bridge` again, and keeps going until the
stroke PROVES or the loop runs out of rope.  The accumulated set is then
MINIMISED -- each member is offered back and the rung re-asked -- so what is
reported is a set no member of which can be dropped.  That is D-646's own
reverse-greedy discipline, applied to the cheapest proof on this board.

  PB1  THE PROOF IS `pad_bridge`'s OWN, UNCHANGED.  Every question is a real
       `maze3d.pad_bridge` call at ONE layer, ONE width and ONE inset, proved
       by `verify_laid` in exact geometry against real obstacle shapes and the
       `.kicad_dru` overlay.  This file contains no clearance arithmetic of its
       own and could not disagree with the promoter if it tried.

  PB2  THE LADDER IS THE GATE'S.  Widths run from the netclass contract down to
       `max(board min_track_width, DRU_CLASS width)` and NO FURTHER, exactly as
       `screen_pad_bridge.py` bounds them: a bridge is ordinary rail copper and
       this screen may not propose a licensed neck.  Layers are
       `permitted_layers`, insets are `maze3d.PAD_BRIDGE_INSETS_MM`.

  PB3  A HELD-OUT OBJECT IS CLASSIFIED, NOT COUNTED.

         PAD        a land.  A part is soldered there; no rip-up can deliver
                    its absence.  One of these in the set and the pair is a
                    PLACEMENT_WALL -- the answer is placement or a different
                    package, and no eviction, relay or licence will do.
         KEEPOUT    a rule area.  Same verdict, different owner.
         ROUTED     a track or a barrel.  This IS an executable unit: it is
                    what `--detour-spec` names and what `--evict-whole` moves.
                    Reported with its net and with whether `protected_copper`'s
                    own pattern forbids touching it at all.

  PB4  THE REPORTED SET IS MINIMAL, AND THE CERTIFICATE RIDES WITH IT.  Every
       member carries `drop_refuses: true` -- the rung was re-asked with that
       member alone put back and it refused.  A member without that flag was
       not proved necessary and says so.

  PB5  THE VERDICT IS THE CHEAPEST RUNG, AND EVERY RUNG IS REPORTED.  Cheapest
       is fewest ROUTED objects first, then widest track, then shortest stroke
       -- because a bridge that costs one relay at 0.400 mm is worth more than
       one that costs none at 0.150 mm this board would then have to license.

  PB6  IT PROPOSES NOTHING.  A `BRIDGEABLE` row is a pair `pad_bridge` already
       lays today and `screen_pad_bridge.py` already reports.  An `EVICTABLE`
       row is a WORK-LIST ENTRY: the removals it names still owe the gate its
       whole thirteen clauses, `every_detour_relaid` and `inert_removal_priced`
       included, and this screen prices neither.

WHY IT IS AFFORDABLE, WHICH IS WHY IT IS BOARD-WIDE.  `pad_bridge` never reads
a cell: `verify_laid` is analytic and the only thing a `Field` was ever handed
in for is `field.layers` and `if L not in field.blk`.  `maze3d.BridgeCtx` is
those two facts plus the five clearance numbers `verify_laid` reads, so a
question costs a bbox sweep instead of a raster and a via grid.  The whole
board -- every open net, every pair, every rung, every blame iteration -- runs
in seconds, and a `Field` remains a valid `BridgeCtx` for anyone who wants one.

Read-only.  Writes JSON; changes nothing.

    python3 screen_pad_bridge_blame.py [NET ...] [--max-mm 6] [-o OUT]
"""

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

PAD = "PAD"
KEEPOUT = "KEEPOUT"
ROUTED = "ROUTED"

BRIDGEABLE = "BRIDGEABLE"
EVICTABLE = "EVICTABLE"
PLACEMENT_WALL = "PLACEMENT_WALL"
UNRESOLVED = "UNRESOLVED"


class Held(object):
    """Exactly these obstacle objects are not there, with NO raster to rebuild.

    `screen_corridor_blockers.WithoutObjects` is the same idea and it also
    calls `Field.rebuild_blk` and `Field._via_grid`, because the questions it
    serves are lattice questions.  Every question here is `verify_laid`, which
    reads `QBoard.obstacles` and never a cell, so rebuilding would burn a
    raster per blame iteration and discard every cell of it unread.  The
    memoised obstacle list IS invalidated, because that is the list the proof
    reads.
    """

    def __init__(self, qb, ids):
        self.qb, self.out = qb, set(ids)

    def __enter__(self):
        qb = self.qb
        self.shapes = {L: qb.shapes[L] for L in qb.shapes}
        self.holes = qb.holes
        for L in qb.shapes:
            qb.shapes[L] = [s for s in qb.shapes[L] if id(s) not in self.out]
        qb.holes = [h for h in qb.holes if id(h) not in self.out]
        qb._obs_cache = None
        return self

    def __exit__(self, *exc):
        self.qb.shapes.update(self.shapes)
        self.qb.holes = self.holes
        self.qb._obs_cache = None
        return False


def classify(obj):
    """PAD / KEEPOUT / ROUTED, from the obstacle's own tag.

    `QBoard._scan` tags a land with its own `REF.NUM`, a rule area `KO`, and
    routed copper `track` / `via` / `via/hole`.  Anything this file does not
    recognise is reported `UNRESOLVED` and refuses the pair, because a class it
    does not know is not a class it may call evictable.
    """
    tag = getattr(obj, "tag", None) or ""
    if tag in ("track", "via") or tag.startswith("via/"):
        return ROUTED
    if tag == "KO" or getattr(obj, "net", None) is None:
        return KEEPOUT
    if re.match(r"^[A-Za-z_]+[0-9]+\.\w+$", tag):
        return PAD
    return UNRESOLVED


def signature(obj, kind):
    d = dict(kind=kind, tag=getattr(obj, "tag", None),
             net=getattr(obj, "net", None))
    for k in ("x0", "y0", "x1", "y1", "cx", "cy", "hw", "r"):
        v = getattr(obj, k, None)
        if v is not None:
            d[k + "_mm"] = round(v / 1e6, 4)
    return d


def blame_rung(qb, ctx, A, B, layer, width, inset, cap):
    """Hold out what the bridge names, ask again, then minimise.  One rung."""
    import maze3d as mz
    held = []

    def ask(objs):
        bl = []
        m = qb.mark()
        with Held(qb, {id(o) for o in objs}):
            r = mz.pad_bridge(qb, ctx, A, B, [width], layer=layer,
                              insets_mm=(inset,), blame=bl)
        qb.revert(m)
        return r, (bl[0] if bl else None)

    for _ in range(cap + 1):
        r, obj = ask(held)
        if r.get("ok"):
            break
        if obj is None:
            return dict(ok=False, reason=r.get("reason"),
                        why=r.get("why"), blockers=[len(held)] and None,
                        n_held=len(held))
        if any(x is obj for x in held):
            return dict(ok=False, reason="REPEAT", n_held=len(held),
                        why=r.get("why"))
        held.append(obj)
    else:
        return dict(ok=False, reason="CAP", n_held=len(held))

    # PB4 -- minimise.  Offer each member back and re-ask; a member the rung
    # proves WITHOUT is not part of the answer.
    keep = list(held)
    for obj in list(held):
        trial = [o for o in keep if o is not obj]
        r, _ = ask(trial)
        if r.get("ok"):
            keep = trial
    certs = []
    for obj in keep:
        trial = [o for o in keep if o is not obj]
        r, _ = ask(trial)
        certs.append(not r.get("ok"))
    final, _ = ask(keep)
    rows = []
    for obj, cert in zip(keep, certs):
        k = classify(obj)
        rows.append(dict(signature(obj, k), drop_refuses=bool(cert)))
    return dict(ok=bool(final.get("ok")), mm=final.get("mm"),
                blockers=rows, n_held=len(keep),
                n_routed=sum(1 for r in rows if r["kind"] == ROUTED),
                n_fixed=sum(1 for r in rows if r["kind"] in (PAD, KEEPOUT)))


def verdict_of(rows):
    if not rows:
        return BRIDGEABLE
    if any(r["kind"] == UNRESOLVED for r in rows):
        return UNRESOLVED
    if any(r["kind"] in (PAD, KEEPOUT) for r in rows):
        return PLACEMENT_WALL
    return EVICTABLE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*",
                    help="default = every retained net with an open edge")
    ap.add_argument("--board", type=Path)
    ap.add_argument("--max-mm", type=float, default=6.0,
                    help="centre-to-centre bound on ONE bridge")
    ap.add_argument("--cap", type=int, default=12,
                    help="most objects one rung may name before it gives up")
    ap.add_argument("--pairs", type=int, default=24,
                    help="nearest N cross-island pairs per net")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from protected_copper import PROTECTED
    from route_maze_batch import (BOARD, net_contract, permitted_layers,
                                  reserved_inner_planes, DRU_CLASS,
                                  BOARD_TRACK_MIN)
    from routing_ledger import generate as ledger_build

    board = a.board or BOARD
    board_sha = hashlib.sha256(Path(board).read_bytes()).hexdigest()
    qb = qr.QBoard(str(board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)

    nets = list(a.nets)
    if not nets:
        led = ledger_build(board)
        nets = sorted(n["net"] for n in led["nets"] if n["open_edges"])

    out, t_all = [], time.time()
    for net in nets:
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        floor = max(BOARD_TRACK_MIN,
                    DRU_CLASS.get(c["netclass"], {}).get("width", 0))
        widths = sorted({c["width"], max(floor, min(c["width"], floor))},
                        reverse=True)
        ctx = mz.BridgeCtx(qb, net, c["clr_pad"], c["clr"], layers)
        islands = mz.net_islands(qb, net)
        pairs = []
        for i, A in enumerate(islands):
            for B in islands[i + 1:]:
                for p in A:
                    for q in B:
                        gap = ((p["x"] - q["x"]) ** 2
                               + (p["y"] - q["y"]) ** 2) ** 0.5
                        if gap <= a.max_mm * qr.MM:
                            pairs.append((gap, p, q))
        pairs.sort(key=lambda t: (t[0], t[1]["ref"], t[2]["ref"]))
        rows, t0 = [], time.time()
        for (gap, A, B) in pairs[:a.pairs]:
            best, rungs = None, []
            for L in ("F", "B"):
                if L not in ctx.layers or not A.get(L) or not B.get(L):
                    continue
                for w in widths:
                    for ins in mz.PAD_BRIDGE_INSETS_MM:
                        if 2 * ins * qr.MM >= gap:
                            break
                        r = blame_rung(qb, ctx, A, B, L, w, ins, a.cap)
                        if not r.get("ok"):
                            continue
                        v = verdict_of(r["blockers"])
                        rec = dict(layer=L, width=int(w), inset_mm=ins,
                                   verdict=v, mm=r.get("mm"),
                                   n_held=r["n_held"], n_routed=r["n_routed"],
                                   n_fixed=r["n_fixed"],
                                   blockers=r["blockers"])
                        rungs.append(dict(rec, blockers=len(r["blockers"])))
                        key = (rec["n_fixed"], rec["n_routed"], -w,
                               rec["mm"] or 0.0)
                        if best is None or key < best[0]:
                            best = (key, rec)
                        break           # this width/layer is answered
            row = dict(a=A["ref"], b=B["ref"], gap_mm=round(gap / 1e6, 3),
                       rungs=rungs)
            if best is None:
                row.update(verdict=UNRESOLVED,
                           why="no rung on the permitted ladder resolved "
                               "within --cap %d objects" % a.cap)
            else:
                rec = best[1]
                row.update(rec)
                for b in rec["blockers"]:
                    if b["kind"] == ROUTED and b.get("net"):
                        b["protected"] = bool(PROTECTED.search(b["net"]))
            rows.append(row)
        rec = dict(net=net, netclass=c["netclass"], islands=len(islands),
                   widths=[int(w) for w in widths],
                   pairs_asked=len(rows), pairs_within_max=len(pairs),
                   seconds=round(time.time() - t0, 1), pairs=rows)
        counts = {}
        for r in rows:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        rec["verdicts"] = counts
        out.append(rec)
        print("  %-36s %-10s %2d pair(s)  %s  %.1fs"
              % (net[-36:], c["netclass"], len(rows),
                 " ".join("%s=%d" % kv for kv in sorted(counts.items())),
                 rec["seconds"]), file=sys.stderr, flush=True)

    after = hashlib.sha256(Path(board).read_bytes()).hexdigest()
    tot = {}
    for r in out:
        for k, v in r["verdicts"].items():
            tot[k] = tot.get(k, 0) + v
    doc = dict(
        schema=1, board=str(board), board_sha256=board_sha,
        authoritative_unchanged=(board_sha == after),
        max_mm=a.max_mm, cap=a.cap, pairs_per_net=a.pairs,
        seconds=round(time.time() - t_all, 1),
        totals=tot,
        question=("for every cross-island land pair a straight bridge could "
                  "span, WHICH OBJECTS -- all of them, minimal, classified -- "
                  "stand in the stroke"),
        method=("read-only; maze3d.pad_bridge under maze3d.BridgeCtx at one "
                "layer/width/inset per question, the named obstacle held out "
                "and the question re-asked to exhaustion, then reverse-greedy "
                "minimisation with a drop_refuses certificate per member; "
                "every trial reverted, nothing written"),
        limits=("PB6: an EVICTABLE row is a work-list entry, not a "
                "transaction -- the gate's thirteen clauses, "
                "every_detour_relaid and inert_removal_priced included, are "
                "not asked here.  A PLACEMENT_WALL row is final for the "
                "BRIDGE only: the same land may still open by escape."),
        nets=out)
    text = json.dumps(doc, indent=1, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    print("pad-bridge blame: %s  (%.1f s)"
          % (" ".join("%s=%d" % kv for kv in sorted(tot.items())) or "nothing",
             doc["seconds"]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
