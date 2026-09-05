#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- MOVE A PART, and prove the move is the only thing that moved.

D-619 measured all five open `U9` NFC edges and found ONE mechanism: every one
is `DETOURABLE` (the corridor opens when the crossing tracks are cut) and every
one is `UNRELAYABLE`, because in every case the irreducible crossing net is a
`.kicad_dru` SINGLE-LAYER net -- `NFC_XIN`, `NFC_XOUT`, `NFC_RFO2`, all
`layers_allowed = ['B']` by the contract D-596/D-603 authored to make a via
INEXPRESSIBLE.  A net with one layer and no barrel cannot walk around a lane.

So the honest move is not to route around the wall.  It is to MOVE THE WALL:
a pad-escape band that is short by microns is a PLACEMENT number, and a part
that is not a mechanical interface may be translated.  This is that unit --
deliberately the smallest one that can express it:

    * translate ONE named footprint by an exact (dx, dy) in nanometres;
    * every track/via/zone/rule-area on the board is left EXACTLY where it is,
      because copper is absolute and only the part moves.  A track that ended
      inside the pad it served still ends inside that pad when the pad is
      1.400 mm wide and the move is 0.300 mm -- and this script MEASURES that
      rather than assuming it: for every pad of the moved part it reports which
      track endpoints were inside the pad BEFORE and are still inside AFTER.
      An endpoint that would leave its pad REFUSES the move.
    * courtyard overlap against every other footprint is measured before and
      after; a move that creates one REFUSES.

D-621 ADDED THE MOVE THAT IS TOO BIG FOR THAT, because the board needed one.
`C17` -- the 100 nF `+3V3` decoupler wedged between `L5` and `L6` inside the
`ST25R3916` front end -- is the only object in the `U9` receive channel, and
D-620 priced its EAST shift at `+0.675 mm` before `C17.1`'s own escape endpoint
leaves its land.  The move that actually opens the channel is 10.9 mm, so the
escape endpoints do not survive it and the clause above refuses on principle.

    * `--release` makes the removal EXPRESSIBLE rather than silent.  The copper
      carrying a stranded endpoint is removed WHOLE, its closure is measured,
      and every removal is reported by the same signature `verify_promotion.py`
      licenses with `--evicted`.  A release may only touch a net named by
      `--release-net`, so it can never quietly rip up a net nobody reviewed,
      and it REFUSES when a removal would strand a THIRD object -- a track or
      pad of the same net still meeting a point the release is taking away.
      A released pad is left with NO escape on purpose: the transaction that
      spends this owes it a new one (`route_maze_batch.py --bond-pad`), and
      `checks/placement_contract.py` PL8 is the clause that checks it did.
      A BARREL IS NOT AN ESCAPE AND IS NOT SWEPT UP WITH ONE.  The far end of a
      released escape is usually a stitch barrel, and on this board the nets
      that carry those barrels -- `+3V3`, `GND` -- own POURS, so such a barrel
      is bonded by filled copper and does not float when its track goes.  The
      closure therefore RETAINS it and says so; a barrel that must go because
      it stands in the way of the copper this transaction is laying has to be
      named, one at a time, with `--release-via`, and is refused if any
      surviving track or pad of its net still meets it.
    * VIA-IN-PAD IS A MEASUREMENT NOW, NOT A FOOTNOTE.  D-620 recorded that a
      `C17` east shift past `+0.225 mm` swallows the `GND` stitch barrel at
      `40.500, 30.200` into `C17.2`'s land.  Any move whose destination puts a
      barrel inside a moved pad REFUSES unless `--allow-via-in-pad` says the
      author priced it, because a plated hole under a solder land is an
      assembly defect that no clearance rule reports.

Read `--report` for the numbers.  `--apply` writes the board; without it
nothing is written and the report is a screen.

    python3 apply_part_shift.py --ref Y1 --dx-nm -300000 --report OUT.json
    python3 apply_part_shift.py --ref Y1 --dx-nm -300000 --apply --report OUT.json
    python3 apply_part_shift.py --ref C17 --dx-nm -7050000 --dy-nm 8850000 \
        --release --release-net +3V3 --release-net GND --apply --report OUT.json
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def pad_boxes(fp):
    """Axis-aligned bounding box of every pad, in nm, keyed by pad number."""
    out = {}
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        out.setdefault(p.GetNumber(), []).append(
            (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
    return out


def inside(box, x, y):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def endpoints_on(board, fp):
    """(net, x, y) track endpoints that currently land inside a pad of `fp`."""
    boxes = [b for bs in pad_boxes(fp).values() for b in bs]
    hits = []
    for t in board.GetTracks():
        pts = [t.GetStart()] if t.GetClass() == "PCB_VIA" else [t.GetStart(),
                                                                t.GetEnd()]
        for p in pts:
            if any(inside(b, p.x, p.y) for b in boxes):
                hits.append((t.GetNetname(), p.x, p.y))
    return sorted(set(hits))


def courtyard_overlaps(board, ref):
    """Pairs (ref, other) whose FOOTPRINT bounding boxes intersect."""
    fps = list(board.GetFootprints())
    me = next(f for f in fps if f.GetReference() == ref)
    mb = me.GetBoundingBox(False, False)
    out = []
    for f in fps:
        if f.GetReference() == ref:
            continue
        b = f.GetBoundingBox(False, False)
        if (mb.GetLeft() <= b.GetRight() and b.GetLeft() <= mb.GetRight()
                and mb.GetTop() <= b.GetBottom() and b.GetTop() <= mb.GetBottom()):
            out.append(f.GetReference())
    return sorted(out)


def sig(board, t):
    """The signature `verify_promotion.py` licenses a removal by."""
    if t.GetClass() == "PCB_VIA":
        return ("via", t.GetNetname(), t.GetStart().x, t.GetStart().y,
                t.GetWidth(), t.GetDrill())
    return ("trk", t.GetNetname(), board.GetLayerName(t.GetLayer()),
            t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y,
            t.GetWidth())


def pour_backed(board, via):
    """Does this barrel's net own a ZONE on a layer the barrel pierces?

    A stitch barrel on a pour-owning net is held by filled copper, not by the
    track that happened to reach it, so removing that track does not leave it
    floating.  This is the test that keeps a release from quietly de-stitching
    a plane it was never asked to touch.
    """
    span = set(via.GetLayerSet().CuStack())
    for i in range(board.GetAreaCount()):
        z = board.GetArea(i)
        if z.GetIsRuleArea() or z.GetNetname() != via.GetNetname():
            continue
        if span & set(z.GetLayerSet().CuStack()):
            return True
    return False


def release_closure(board, doomed_points, allowed_nets, named_vias=()):
    """Which objects a release must remove, and what it must NOT strand.

    `doomed_points` is the set of (net, x, y) endpoints the move takes off a
    pad.  Step one removes every track carrying one of them.  Step two removes
    a BARREL only when a removed track's own other end sat on it and nothing
    else of that net still does -- a stitch via that was never served by the
    released escape is left exactly where it is.

    Returns (removals, refusals).  `refusals` is non-empty when the closure
    would take away a point that some SURVIVING track, via or pad of the same
    net still meets: that is a tee, not an escape, and the release stops.
    """
    def key(pt):
        return (pt.x, pt.y)

    doomed = {(n, x, y) for n, x, y in doomed_points}
    tracks, vias = [], []
    for t in board.GetTracks():
        (vias if t.GetClass() == "PCB_VIA" else tracks).append(t)

    refusals_via = []
    kill = [t for t in tracks
            if (t.GetNetname(), t.GetStart().x, t.GetStart().y) in doomed
            or (t.GetNetname(), t.GetEnd().x, t.GetEnd().y) in doomed]
    killset = {id(t) for t in kill}

    # The far end of every released track: a point the release is about to
    # orphan unless a barrel there goes with it.
    far = set()
    for t in kill:
        for pt in (t.GetStart(), t.GetEnd()):
            if (t.GetNetname(), pt.x, pt.y) not in doomed:
                far.add((t.GetNetname(), pt.x, pt.y))

    kill_via, kept_via = [], []
    named = set(named_vias)
    for v in vias:
        k = (v.GetNetname(), v.GetStart().x, v.GetStart().y)
        if k not in far and k not in named:
            continue
        served = [t for t in tracks
                  if id(t) not in killset and t.GetNetname() == k[0]
                  and (key(t.GetStart()) == k[1:] or key(t.GetEnd()) == k[1:])]
        if served:
            if k in named:
                refusals_via.append(dict(
                    reason="NAMED_VIA_STILL_SERVED", net=k[0],
                    at_mm=[k[1] / 1e6, k[2] / 1e6],
                    surviving_tracks=len(served)))
            else:
                kept_via.append(dict(net=k[0], at_mm=[k[1] / 1e6, k[2] / 1e6],
                                     why="a surviving track still meets it"))
            continue
        if k not in named and pour_backed(board, v):
            kept_via.append(dict(net=k[0], at_mm=[k[1] / 1e6, k[2] / 1e6],
                                 why="pour-backed stitch barrel; not floating"))
            continue
        kill_via.append(v)
    for k in sorted(named):
        if not any((v.GetNetname(), v.GetStart().x, v.GetStart().y) == k
                   for v in vias):
            refusals_via.append(dict(reason="NAMED_VIA_NOT_FOUND", net=k[0],
                                     at_mm=[k[1] / 1e6, k[2] / 1e6]))

    killed_via_pts = {(v.GetNetname(), v.GetStart().x, v.GetStart().y)
                      for v in kill_via}

    refusals = list(refusals_via)
    for net, x, y in sorted(far - killed_via_pts):
        others = [t for t in tracks
                  if id(t) not in killset and t.GetNetname() == net
                  and (key(t.GetStart()) == (x, y) or key(t.GetEnd()) == (x, y))]
        pads = []
        for f in board.GetFootprints():
            for pad in f.Pads():
                if pad.GetNetname() != net:
                    continue
                bb = pad.GetBoundingBox()
                if inside((bb.GetLeft(), bb.GetTop(), bb.GetRight(),
                           bb.GetBottom()), x, y):
                    pads.append("%s.%s" % (f.GetReference(), pad.GetNumber()))
        if any(v["net"] == net and v["at_mm"] == [x / 1e6, y / 1e6]
               for v in kept_via):
            continue
        if others or pads:
            refusals.append(dict(reason="RELEASE_WOULD_STRAND", net=net,
                                 at_mm=[x / 1e6, y / 1e6],
                                 surviving_tracks=len(others), pads=pads))

    removals = kill + kill_via
    for t in removals:
        if t.GetNetname() not in allowed_nets:
            refusals.append(dict(reason="RELEASE_NET_NOT_DECLARED",
                                 net=t.GetNetname(),
                                 at_mm=[t.GetStart().x / 1e6,
                                        t.GetStart().y / 1e6]))
    return removals, refusals, kept_via


def vias_in_pads(board, fp):
    """Barrels whose centre lands inside a pad of `fp` -- via-in-pad."""
    boxes = [(num, b) for num, bs in pad_boxes(fp).items() for b in bs]
    out = []
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        p = t.GetStart()
        for num, b in boxes:
            if inside(b, p.x, p.y):
                out.append(dict(pad="%s.%s" % (fp.GetReference(), num),
                                net=t.GetNetname(),
                                at_mm=[p.x / 1e6, p.y / 1e6],
                                dia_mm=t.GetWidth() / 1e6))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--dx-nm", type=int, default=0)
    ap.add_argument("--dy-nm", type=int, default=0)
    ap.add_argument("--release", action="store_true",
                    help="remove the copper whose endpoint the move takes off "
                         "a pad, WHOLE and by measured closure, instead of "
                         "refusing the move.  A released pad is left with no "
                         "escape on purpose; the transaction owes it a new one")
    ap.add_argument("--release-net", action="append", default=[],
                    help="a net --release may touch.  Repeatable.  A release "
                         "that would remove copper of any other net refuses")
    ap.add_argument("--release-via", action="append", default=[],
                    metavar="NET:X,Y",
                    help="release ONE named barrel, in millimetres, even "
                         "though its net owns a pour that still holds it.  The "
                         "honest form for a stitch that stands in the way of "
                         "the copper this transaction lays.  Refused if any "
                         "SURVIVING track or pad of that net still meets it")
    ap.add_argument("--allow-via-in-pad", action="store_true",
                    help="price a move whose destination swallows a barrel "
                         "into a moved land.  D-620 measured this for C17 at "
                         "+0.225 mm; without this flag such a move refuses")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", type=Path)
    a = ap.parse_args()

    sys.path.insert(0, "/usr/lib/python3/dist-packages")
    import pcbnew

    board = pcbnew.LoadBoard(str(a.board))
    fp = next((f for f in board.GetFootprints()
               if f.GetReference() == a.ref), None)
    if fp is None:
        raise SystemExit(f"no footprint {a.ref}")

    was_pos = (fp.GetPosition().x, fp.GetPosition().y)
    was_pads = pad_boxes(fp)
    was_hits = endpoints_on(board, fp)
    was_overlap = courtyard_overlaps(board, a.ref)

    fp.Move(pcbnew.VECTOR2I(a.dx_nm, a.dy_nm))

    now_pos = (fp.GetPosition().x, fp.GetPosition().y)
    now_pads = pad_boxes(fp)
    now_boxes = [b for bs in now_pads.values() for b in bs]
    now_overlap = courtyard_overlaps(board, a.ref)

    stranded = [h for h in was_hits
                if not any(inside(b, h[1], h[2]) for b in now_boxes)]
    new_overlap = sorted(set(now_overlap) - set(was_overlap))
    swallowed = vias_in_pads(board, fp)

    named = []
    for spec in a.release_via:
        net, xy = spec.rsplit(":", 1)
        x, y = (int(round(float(v) * 1e6)) for v in xy.split(","))
        named.append((net, x, y))

    released, refusals, kept = [], [], []
    if a.release and (stranded or named):
        doomed, refusals, kept = release_closure(
            board, stranded, set(a.release_net), named)
        released = [sig(board, t) for t in doomed]
        if not refusals:
            for t in doomed:
                board.Remove(t)

    ok = (not new_overlap
          and (not stranded or (a.release and not refusals))
          and not refusals
          and (not swallowed or a.allow_via_in_pad))
    report = dict(
        schema=2, board=str(a.board), ref=a.ref,
        dx_nm=a.dx_nm, dy_nm=a.dy_nm,
        position_was_mm=[v / 1e6 for v in was_pos],
        position_now_mm=[v / 1e6 for v in now_pos],
        pads=len(was_pads),
        pad_boxes_was_mm={k: [[c / 1e6 for c in b] for b in v]
                          for k, v in sorted(was_pads.items())},
        pad_boxes_now_mm={k: [[c / 1e6 for c in b] for b in v]
                          for k, v in sorted(now_pads.items())},
        endpoints_on_pads=len(was_hits),
        endpoints_stranded=[[n, x / 1e6, y / 1e6] for n, x, y in stranded],
        release_requested=bool(a.release),
        release_nets=sorted(set(a.release_net)),
        released_objects=sorted(str(s) for s in released),
        released_count=len(released),
        release_refusals=refusals,
        release_named_vias=[[n, x / 1e6, y / 1e6] for n, x, y in named],
        release_retained_barrels=kept,
        vias_in_moved_pads=swallowed,
        via_in_pad_allowed=bool(a.allow_via_in_pad),
        courtyard_overlaps_was=was_overlap,
        courtyard_overlaps_now=now_overlap,
        courtyard_overlaps_new=new_overlap,
        applied=bool(a.apply and ok),
        verdict="PASS" if ok else "FAIL",
    )
    if a.apply and ok:
        board.Save(str(a.board))
    text = json.dumps(report, indent=2, sort_keys=True)
    if a.report:
        a.report.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
