#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the PLACEMENT contract (PL1-PL9).

Every gate this project owns judges COPPER.  `verify_promotion.py` reads
`BOARD.GetTracks()`; `protected_copper.py` reads the same objects on the
protected nets; `land_parity_contract.py` compares each land to its library
master.  None of them can see a FOOTPRINT MOVE, because a footprint move
changes no track, no via, no zone and no rule area -- it changes one `(at ...)`
line, and every pad on the part travels with it silently.

D-619 needed that move.  All five open `U9` NFC edges measured
`DETOURABLE` + `UNRELAYABLE`: the corridor opens whenever the crossing tracks
are cut, and the irreducible crossing net is in every case a `.kicad_dru`
SINGLE-LAYER net (`NFC_XIN`, `NFC_XOUT`, `NFC_RFO2`, all `layers_allowed =
['B']`), which has no second layer to walk around a lane on.  When the blocker
cannot move, the wall must -- and `U9.7`'s escape band was short by FIFTY
MICRONS.  So this file is the invariant that makes moving a part reviewable:

    PL1  the board holds exactly the same footprint REFERENCES it held before
    PL2  exactly the CLAIMED references moved, each by exactly the claimed
         (dx, dy) in nanometres, and every other footprint's position,
         orientation and layer are IDENTICAL
    PL3  a moved part carried its LAND PATTERN whole: same pad numbers, same
         sizes, same shapes, same offsets from the footprint origin
    PL4  no NEW footprint-bounding-box overlap was created
    PL5  NOTHING WAS STRANDED.  Every track or via endpoint that lay inside a
         moved part's pad BEFORE still lies inside that pad AFTER.  This is the
         clause that makes a move safe without re-routing: copper is absolute
         and only the part moves, so a 0.300 mm shift of a 1.400 mm pad keeps
         its tracks attached -- but only a measurement may say so.
    PL6  the screen is NOT VACUOUS: a synthetic 1 um perturbation of an
         UNCLAIMED footprint must be caught by PL2.
    PL7  A MOVED PAD SWEPT INTO NO FOREIGN COPPER.  A part that travels drags
         its LANDS across whatever is already there, and the copper does not
         move out of the way.  D-619 walked straight into this: shifting `Y1`
         0.300 mm west put `Y1.4`'s `GND` land on top of three existing
         `NFC_XIN` tracks -- two dead SHORTS and a 0.0389 mm clearance -- and
         PL1-PL6 all passed, because every endpoint was still on its own pad
         and no courtyard overlapped.  Real DRC caught it, which is the bar
         holding; this clause is the bar SAYING SO, by name, on the part that
         moved, so a placement transaction knows up front that it must ride
         with a re-route of whatever it landed on.

D-621 ADDED PL8 AND PL9, because the board needed a move PL5 refuses on
principle.  `C17` -- the 100 nF `+3V3` decoupler wedged between `L5` and `L6`
inside the `ST25R3916` front end, and the only object in the `U9` receive
channel -- had to travel 10.9 mm, and no 0.900 mm land keeps its escape
endpoint across 10.9 mm.  D-620 had already priced the alternative: an east
shift dies at `+0.675 mm` on that same endpoint.  So the move became
EXPRESSIBLE instead of forbidden -- `apply_part_shift.py --release` removes the
stranded escape WHOLE, by measured closure, and reports every removal by the
signature `verify_promotion.py --evicted` licenses -- and these are the two
clauses that keep it reviewable:

    PL8  A RELEASED PAD WAS RE-CONNECTED.  A release is only half a
         transaction: the pad is left with no escape on purpose, and the run
         that spends it owes the pad a new one.  For every `--release REF.PIN`
         this clause requires (a) that no object on the POST board still ends
         at the released coordinate -- so the copper was REMOVED, not left
         dangling in space -- and (b) that at least one POST track endpoint
         lies inside that pad.  PL5 stops treating a released endpoint as
         stranded, and only for the pads named here.
    PL9  NO BARREL ENDED UP UNDER A MOVED LAND.  D-620 measured that a `C17`
         east shift past `+0.225 mm` swallows the `GND` stitch barrel at
         `40.500, 30.200` into `C17.2`'s land.  A plated hole under a solder
         land is an assembly defect that no clearance rule reports, because the
         barrel and the pad are the same net; this clause reports it by name.

    python3 hardware/demo/manufacturing/checks/placement_contract.py \
        --ref HEAD --move Y1:-300000:0 [-o REPORT.json]
    python3 hardware/demo/manufacturing/checks/placement_contract.py \
        --ref HEAD --move C17:-7050000:8850000 --release C17.1 --release C17.2
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def stage(rev, work):
    work.mkdir(parents=True, exist_ok=True)
    target = work / BOARD.name
    if rev is None:
        target.write_bytes(BOARD.read_bytes())
    else:
        src = BOARD.relative_to(ROOT)
        target.write_bytes(subprocess.run(
            ["git", "-C", str(ROOT), "show", "%s:%s" % (rev, src)],
            capture_output=True, check=True).stdout)
    return target


def read(path):
    """Footprint pose + land pattern + pad boxes, and every track endpoint."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    fps, boxes, bynum = {}, {}, {}
    for f in board.GetFootprints():
        ref = f.GetReference()
        pos = f.GetPosition()
        lands = []
        for p in f.Pads():
            off = p.GetPosition() - pos
            lands.append((p.GetNumber(), p.GetSizeX(), p.GetSizeY(),
                          int(p.GetShape()), off.x, off.y))
        bb = f.GetBoundingBox(False, False)
        fps[ref] = dict(
            x=pos.x, y=pos.y,
            orient=round(f.GetOrientationDegrees(), 6),
            layer=board.GetLayerName(f.GetLayer()),
            lands=sorted(lands),
            bbox=(bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
        boxes[ref] = sorted(
            (p.GetBoundingBox().GetLeft(), p.GetBoundingBox().GetTop(),
             p.GetBoundingBox().GetRight(), p.GetBoundingBox().GetBottom())
            for p in f.Pads())
        for p in f.Pads():
            bb = p.GetBoundingBox()
            bynum.setdefault("%s.%s" % (ref, p.GetNumber()), []).append(
                (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
    ends, via_pts = [], []
    for t in board.GetTracks():
        pts = ([t.GetStart()] if t.GetClass() == "PCB_VIA"
               else [t.GetStart(), t.GetEnd()])
        for p in pts:
            ends.append((t.GetNetname(), p.x, p.y))
        if t.GetClass() == "PCB_VIA":
            via_pts.append((t.GetNetname(), t.GetStart().x, t.GetStart().y,
                            t.GetWidth()))
    return (fps, boxes, sorted(set(ends)), bynum, sorted(set(via_pts)))


def inside(box, x, y):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def foreign_copper_hits(path, refs, clearance_nm):
    """PL7: copper of a FOREIGN net inside a moved pad's clearance envelope."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    hits = []
    for f in board.GetFootprints():
        if f.GetReference() not in refs:
            continue
        for pad in f.Pads():
            pnet = pad.GetNetname()
            for layer in pad.GetLayerSet().CuStack():
                shape = pad.GetEffectiveShape(layer)
                for t in board.GetTracks():
                    if t.GetNetname() == pnet:
                        continue
                    if (t.GetClass() != "PCB_VIA"
                            and t.GetLayer() != layer):
                        continue
                    if not t.IsOnLayer(layer):
                        continue
                    if shape.Collide(t.GetEffectiveShape(layer), clearance_nm):
                        hits.append(dict(
                            ref="%s.%s" % (f.GetReference(), pad.GetNumber()),
                            pad_net=pnet, layer=board.GetLayerName(layer),
                            other_net=t.GetNetname(),
                            other=("via" if t.GetClass() == "PCB_VIA"
                                   else "track"),
                            at_mm=[t.GetPosition().x / 1e6,
                                   t.GetPosition().y / 1e6]))
    return hits


def overlaps(fps):
    refs = sorted(fps)
    out = set()
    for i, a in enumerate(refs):
        ba = fps[a]["bbox"]
        for b in refs[i + 1:]:
            bb = fps[b]["bbox"]
            if (ba[0] <= bb[2] and bb[0] <= ba[2]
                    and ba[1] <= bb[3] and bb[1] <= ba[3]):
                out.add((a, b))
    return out


def judge(pre, post, claimed, released=()):
    """claimed: {ref: (dx_nm, dy_nm)}; released: ("REF.PIN", ...).

    Returns (checks, detail).
    """
    fpre, bpre, epre, npre, _vpre = pre
    fpost, bpost, epost, npost, vpost = post

    pl1 = sorted(fpre) == sorted(fpost)

    wrong, unclaimed_moved = [], []
    for ref in sorted(set(fpre) & set(fpost)):
        a, b = fpre[ref], fpost[ref]
        d = (b["x"] - a["x"], b["y"] - a["y"])
        same_pose = (a["orient"] == b["orient"] and a["layer"] == b["layer"])
        if ref in claimed:
            if d != tuple(claimed[ref]) or not same_pose:
                wrong.append(dict(ref=ref, want=list(claimed[ref]),
                                  got=list(d), pose_same=same_pose))
        elif d != (0, 0) or not same_pose:
            unclaimed_moved.append(dict(ref=ref, delta_nm=list(d),
                                        pose_same=same_pose))
    pl2 = pl1 and not wrong and not unclaimed_moved

    pl3 = [ref for ref in claimed
           if ref in fpre and ref in fpost
           and fpre[ref]["lands"] != fpost[ref]["lands"]]

    new_overlap = sorted(overlaps(fpost) - overlaps(fpre))

    # PL5, and PL8's half of it.  An endpoint that left a moved pad is
    # STRANDED unless that pad was declared RELEASED and the object carrying
    # the endpoint is gone from the board entirely -- removed, not dangling.
    post_pts = {(x, y) for _n, x, y in epost}
    stranded, releases = [], []
    for ref in sorted(claimed):
        if ref not in bpre or ref not in bpost:
            continue
        was = [e for e in epre if any(inside(box, e[1], e[2])
                                      for box in bpre[ref])]
        for net, x, y in was:
            if any(inside(box, x, y) for box in bpost[ref]):
                continue
            pad = next((r for r in released
                        if any(inside(b, x, y) for b in npre.get(r, []))), None)
            if pad is not None and (x, y) not in post_pts:
                releases.append(dict(pad=pad, net=net,
                                     at_mm=[x / 1e6, y / 1e6],
                                     removed_from_board=True))
                continue
            stranded.append(dict(ref=ref, net=net, at_mm=[x / 1e6, y / 1e6],
                                 declared_release=pad is not None,
                                 still_on_board=(x, y) in post_pts))

    # PL8: every released pad has a NEW escape endpoint inside it.
    reconnected, orphan_pads = [], []
    for pad in sorted(set(released)):
        boxes = npost.get(pad, [])
        hits = [e for e in epost
                if any(inside(b, e[1], e[2]) for b in boxes)]
        (reconnected if hits else orphan_pads).append(
            dict(pad=pad, post_endpoints=len(hits)))

    # PL9: no barrel under a moved land.
    swallowed = []
    for ref in sorted(claimed):
        for net, x, y, dia in vpost:
            if any(inside(box, x, y) for box in bpost.get(ref, [])):
                swallowed.append(dict(ref=ref, net=net,
                                      at_mm=[x / 1e6, y / 1e6],
                                      dia_mm=dia / 1e6))

    checks = dict(
        PL1_reference_set_unchanged=pl1,
        PL2_only_claimed_parts_moved=pl2,
        PL3_land_patterns_travelled_whole=not pl3,
        PL4_no_new_courtyard_overlap=not new_overlap,
        PL5_nothing_stranded=not stranded,
        PL8_released_pads_reconnected=not orphan_pads,
        PL9_no_via_under_a_moved_land=not swallowed,
    )
    detail = dict(
        claimed={k: list(v) for k, v in sorted(claimed.items())},
        footprints_pre=len(fpre), footprints_post=len(fpost),
        references_added=sorted(set(fpost) - set(fpre)),
        references_removed=sorted(set(fpre) - set(fpost)),
        claimed_moves_wrong=wrong,
        unclaimed_footprints_moved=unclaimed_moved,
        land_patterns_changed=pl3,
        courtyard_overlaps_new=[list(p) for p in new_overlap],
        endpoints_checked=sum(
            len([e for e in epre
                 if any(inside(box, e[1], e[2]) for box in bpre.get(ref, []))])
            for ref in claimed),
        endpoints_stranded=stranded,
        released_claimed=sorted(set(released)),
        endpoints_released=releases,
        released_pads_reconnected=reconnected,
        released_pads_orphaned=orphan_pads,
        vias_under_moved_lands=swallowed,
    )
    return checks, detail


PERTURB = """
import sys
import pcbnew
path, ref = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(path)
f = [x for x in b.GetFootprints() if x.GetReference() == ref]
if len(f) != 1:
    raise SystemExit("PL6: %d footprints named %s" % (len(f), ref))
f[0].Move(pcbnew.VECTOR2I(1000, 0))
pcbnew.SaveBoard(path, b)
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD",
                    help="git revision holding the PRE-promotion board")
    ap.add_argument("--move", action="append", default=[], metavar="REF:DX:DY",
                    help="a reference this promotion claims to have MOVED, and "
                         "the exact delta in nanometres.  Repeatable")
    ap.add_argument("--release", action="append", default=[],
                    metavar="REF.PIN",
                    help="a land whose escape this promotion claims to have "
                         "RELEASED (apply_part_shift.py --release).  PL5 stops "
                         "calling its endpoint stranded, and PL8 requires the "
                         "copper to be GONE from the board and the land to "
                         "have a NEW escape.  Repeatable")
    ap.add_argument("--decoy", default=None,
                    help="reference PL6 perturbs; default is the first "
                         "footprint that is not claimed")
    ap.add_argument("--clearance-nm", type=int, default=200000,
                    help="PL7 envelope: the board's default netclass clearance")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    claimed = {}
    for spec in a.move:
        ref, dx, dy = spec.split(":")
        claimed[ref] = (int(dx), int(dy))

    sys.path.insert(0, "/usr/lib/python3/dist-packages")
    tmp = Path(tempfile.mkdtemp(prefix="aqroot-demo-placement-"))
    pre_path, post_path = stage(a.ref, tmp / "pre"), stage(None, tmp / "post")
    pre, post = read(pre_path), read(post_path)
    checks, detail = judge(pre, post, claimed, tuple(a.release))

    decoy = a.decoy or next(r for r in sorted(pre[0]) if r not in claimed)
    probe = tmp / "pl6" / BOARD.name
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_bytes(post_path.read_bytes())
    subprocess.run([sys.executable, "-c", PERTURB, str(probe), decoy],
                   check=True, capture_output=True)
    pchecks, _ = judge(pre, read(probe), claimed, tuple(a.release))
    checks["PL6_screen_is_not_vacuous"] = not pchecks["PL2_only_claimed_parts_moved"]
    detail["pl6_decoy"] = decoy

    hits = foreign_copper_hits(post_path, set(claimed), a.clearance_nm)
    checks["PL7_moved_pads_clear_foreign_copper"] = not hits
    detail["clearance_nm"] = a.clearance_nm
    detail["foreign_copper_hits"] = hits

    doc = dict(schema=2, ref=a.ref, checks=checks, detail=detail,
               verdict="PASS" if all(checks.values()) else "FAIL")
    text = json.dumps(doc, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
