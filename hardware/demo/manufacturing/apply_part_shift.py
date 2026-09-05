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

Read `--report` for the numbers.  `--apply` writes the board; without it
nothing is written and the report is a screen.

    python3 apply_part_shift.py --ref Y1 --dx-nm -300000 --report OUT.json
    python3 apply_part_shift.py --ref Y1 --dx-nm -300000 --apply --report OUT.json
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--dx-nm", type=int, default=0)
    ap.add_argument("--dy-nm", type=int, default=0)
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

    ok = not stranded and not new_overlap
    report = dict(
        schema=1, board=str(a.board), ref=a.ref,
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
