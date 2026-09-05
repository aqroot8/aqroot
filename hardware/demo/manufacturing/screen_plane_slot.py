#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what does a SIGNAL SLOT cost a reserved inner
PLANE -- does the plane stay one piece, and does any barrel fall off it?

WHY THIS QUESTION EXISTS NOW.  Every capacity argument on this board has read
the stack-up as F / GND / SIGNAL / +3V3 / GND / B and treated the two GND
planes as untouchable.  D-635 measured them with the same instrument that
measured the signal layers and found the opposite of what the stack-up
suggests: `In1.Cu` and `In4.Cu` are each **8635.9 mm2 free in ONE piece at
0.200 mm with the whole 790-barrel via field in place**, against `In2.Cu`'s
6524.6 mm2 in 223 pieces.  The board's largest connected routing surface by a
wide margin is a PLANE, and offering one to the hop turns refusals into
closures at the full netclass trunk width.

So the licence question is live, and it has exactly two halves.  The second
half -- what a slot costs the RETURN PATH of the traces referenced to that
plane -- is the one open modelling gap in `PP2` and is not this screen's to
answer.  The FIRST half is geometric, deterministic and answerable now:

    A SIGNAL TRACK ON A PLANE IS A SLOT.  KiCad re-pours around it, exactly as
    D-584 measured on the outer pours.  Does the plane survive as one piece,
    and does every barrel that was bonded to it stay bonded?

METHOD.  The plane's filled polygon set is read from KiCad
(`GetFilledPolysList`), the proposed run is stroked at
`width + 2 * clearance` and SUBTRACTED, and the result is re-counted:
outlines before and after, the area lost, and -- the measurement that actually
decides it -- for every same-net via and land whose centre lay inside the
plane before, whether it still lies inside the SAME outline as the plane's main
body afterwards.  A barrel that leaves the main body is the plane's version of
the orphaned pad gate clause 4 refuses whole runs for.

WHAT A PASS HERE DOES *NOT* MEAN.  It is a bound on ONE proposed geometry, not
a licence: the promotion gate re-pours the real board and `pour_partition` and
`pour_bond` are still the only things that certify a fill.  And a slot that
severs nothing can still be an EMC fault -- the return-path cost is priced
elsewhere or not at all.

    python3 screen_plane_slot.py --layer In1 --net GND
        --seg X0,Y0,X1,Y1 [--seg ...] [--width NM] [--clearance NM]
        [--from-pairs ARTIFACT.json] [--board B] [-o OUT]

`--from-pairs` reads a `screen_offcentre_hop.py` sweep and, for every pair that
CLOSED with a haul on this layer, takes the straight segment between the two
barrel sites the hop chose.  That is the WORST-CASE straight cut between the
same two points and not the meandering path the router actually found: it is
never shorter than the haul it stands for at the ends it stands for, so a
plane that survives it is not evidence about that exact path, and a plane that
does NOT survive it is a warning worth having early.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

LAYER = {"F": "F_Cu", "In1": "In1_Cu", "In2": "In2_Cu", "In3": "In3_Cu",
         "In4": "In4_Cu", "B": "B_Cu"}
SHORT = {"F": "F", "I1": "In1", "I2": "In2", "I3": "In3", "I4": "In4",
         "B": "B"}


def outlines(pcbnew, poly):
    """(index, area mm2) of every outline, largest first."""
    out = []
    for i in range(poly.OutlineCount()):
        sub = pcbnew.SHAPE_POLY_SET()
        sub.AddOutline(poly.Outline(i))
        for h in range(poly.HoleCount(i)):
            sub.AddHole(poly.Hole(i, h), 0)
        out.append((i, sub.Area() / 1e12))
    return sorted(out, key=lambda t: -t[1])


def which_outline(pcbnew, poly, pt):
    for i in range(poly.OutlineCount()):
        sub = pcbnew.SHAPE_POLY_SET()
        sub.AddOutline(poly.Outline(i))
        for h in range(poly.HoleCount(i)):
            sub.AddHole(poly.Hole(i, h), 0)
        if sub.Collide(pt, 0):
            return i
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--layer", default="In1")
    ap.add_argument("--net", default="GND")
    ap.add_argument("--seg", action="append", default=[],
                    help="X0,Y0,X1,Y1 in mm")
    ap.add_argument("--from-pairs", type=Path, action="append",
                    default=[],
                    help="repeatable: one sweep SHARD each.  All the cuts named\n"
                         "across every shard are subtracted TOGETHER, because a\n"
                         "licence that admits three hauls admits them at once")
    ap.add_argument("--width", type=int, default=200000)
    ap.add_argument("--clearance", type=int, default=200000)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew

    lid = getattr(pcbnew, LAYER[a.layer])
    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    b = pcbnew.LoadBoard(str(a.board))

    segs = []
    for s in a.seg:
        x0, y0, x1, y1 = (float(v) for v in s.split(","))
        segs.append(dict(source="--seg", x0=x0, y0=y0, x1=x1, y1=y1))
    for src in a.from_pairs:
        d = json.loads(src.read_text(encoding="utf-8"))
        for n in d["nets"]:
            for q in n["pairs"]:
                if not q.get("closed_at"):
                    continue
                lay = [SHORT.get(x, x) for x in (q.get("hop_layers") or [])]
                if a.layer not in lay:
                    continue
                vs = None
                for r in q["rungs"]:
                    if r.get("ok"):
                        vs = r.get("via_xy")
                        break
                if not vs or len(vs) < 2:
                    continue
                segs.append(dict(source="%s %s<->%s" % (n["net"], q["a"],
                                                        q["b"]),
                                 x0=vs[0][0], y0=vs[0][1],
                                 x1=vs[-1][0], y1=vs[-1][1],
                                 closed_at=q["closed_at"]))

    if not segs:
        raise SystemExit("no segments: give --seg or --from-pairs")

    zones = [z for z in b.Zones()
             if not z.GetIsRuleArea() and z.GetNetname() == a.net
             and z.IsOnLayer(lid)]
    if len(zones) != 1:
        raise SystemExit("expected exactly one %s zone on %s, found %d"
                         % (a.net, a.layer, len(zones)))
    poly = pcbnew.SHAPE_POLY_SET(zones[0].GetFilledPolysList(lid))

    before = outlines(pcbnew, poly)
    # WHO IS BONDED TO THE PLANE BEFORE THE CUT.  Barrels first: on a reserved
    # plane they ARE the connection, and a barrel that leaves the main body is
    # this layer's orphaned pad.
    anchors = []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != a.net:
            continue
        p = t.GetPosition()
        i = which_outline(pcbnew, poly, p)
        if i is not None:
            anchors.append(dict(kind="via", tag="via@%.3f,%.3f"
                                % (p.x / 1e6, p.y / 1e6),
                                x=p.x, y=p.y, before=i))
    for f in b.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetname() != a.net or not pad.IsOnLayer(lid):
                continue
            p = pad.GetPosition()
            i = which_outline(pcbnew, poly, p)
            if i is not None:
                anchors.append(dict(kind="pad",
                                    tag=f.GetReference() + "." +
                                        pad.GetNumber(),
                                    x=p.x, y=p.y, before=i))

    cut = pcbnew.SHAPE_POLY_SET()
    half = a.width / 2.0 + a.clearance
    for s in segs:
        x0, y0 = int(round(s["x0"] * 1e6)), int(round(s["y0"] * 1e6))
        x1, y1 = int(round(s["x1"] * 1e6)), int(round(s["y1"] * 1e6))
        s["mm"] = round(math.hypot(x1 - x0, y1 - y0) / 1e6, 4)
        seg = pcbnew.SHAPE_POLY_SET()
        # A stroked segment: the segment's own rectangle plus a disc at each
        # end, which is the shape KiCad clears around a track.
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln * half, dx / ln * half
        ch = pcbnew.VECTOR_VECTOR2I()
        for px, py in ((x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                       (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)):
            ch.append(pcbnew.VECTOR2I(int(round(px)), int(round(py))))
        seg.AddOutline(pcbnew.SHAPE_LINE_CHAIN(ch, True))
        for cx, cy in ((x0, y0), (x1, y1)):
            circ = pcbnew.SHAPE_POLY_SET()
            pts = pcbnew.VECTOR_VECTOR2I()
            for k in range(48):
                th = 2 * math.pi * k / 48.0
                pts.append(pcbnew.VECTOR2I(
                    int(round(cx + half * math.cos(th))),
                    int(round(cy + half * math.sin(th)))))
            circ.AddOutline(pcbnew.SHAPE_LINE_CHAIN(pts, True))
            seg.BooleanAdd(circ)
        cut.BooleanAdd(seg)
    poly.BooleanSubtract(cut)

    after = outlines(pcbnew, poly)
    main = after[0][0] if after else None
    lost = []
    for an in anchors:
        i = which_outline(pcbnew, poly, pcbnew.VECTOR2I(an["x"], an["y"]))
        an["after"] = i
        if i is None or i != main:
            lost.append(an)

    a_before = sum(x[1] for x in before)
    a_after = sum(x[1] for x in after)
    ok = (not lost) and len(after) <= len(before)
    print(" %s %s: outlines %d -> %d, area %.1f -> %.1f mm2 (-%.1f), "
          "%d anchors, %d off the main body -> %s"
          % (a.net, a.layer, len(before), len(after), a_before, a_after,
             a_before - a_after, len(anchors), len(lost),
             "SURVIVES" if ok else "SEVERS"),
          file=sys.stderr, flush=True)
    for an in lost[:20]:
        print("   OFF-BODY %s (outline %s -> %s)"
              % (an["tag"], an["before"], an["after"]), file=sys.stderr)

    after_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(schema=1, board=str(a.board), board_sha256=sha,
               authoritative_unchanged=(sha == after_sha),
               layer=a.layer, net=a.net, width=a.width,
               clearance=a.clearance, verdict="SURVIVES" if ok else "SEVERS",
               question=("does a signal SLOT on a reserved inner plane leave "
                         "the plane one piece and every barrel still bonded "
                         "to its main body"),
               method=("read-only; the plane's own filled polygon set from "
                       "KiCad, minus the proposed run stroked at "
                       "width/2 + clearance with a disc at each end; anchors "
                       "are re-located by outline afterwards.  The board is "
                       "not written and no zone is refilled -- the promotion "
                       "gate's pour_partition and pour_bond remain the only "
                       "things that certify a fill"),
               from_pairs=[str(x) for x in a.from_pairs],
               segments=segs,
               outlines_before=len(before), outlines_after=len(after),
               area_before_mm2=round(a_before, 3),
               area_after_mm2=round(a_after, 3),
               area_lost_mm2=round(a_before - a_after, 3),
               main_outline=main,
               anchors=len(anchors), anchors_off_body=len(lost),
               off_body=lost)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
