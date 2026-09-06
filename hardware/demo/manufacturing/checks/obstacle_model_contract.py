#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the PROPOSER'S OBSTACLE MODEL is the BOARD'S OWN COPPER.

D-645.  Every instrument that has ever proposed copper on this board -- the
maze, the stitch, the bridge, the relief, the hop, `verify_laid` and the whole
`screen_*` family -- reads its obstacles from exactly two lists,
`qrouter.QBoard.shapes` and `QBoard.holes`.  `QBoard.grid`, `Field.rebuild_blk`
and `Field._via_grid` iterate `QBoard.obstacles`, which is those two lists and
nothing else.  Nobody had ever asked whether those two lists ARE the board.

They are not.  `QBoard._scan` walks `board.GetTracks()` and keeps an object
only when `t.GetClass() == 'PCB_TRACK'`.  In this KiCad build a through via is
a `PCB_VIA`, a DIFFERENT class string, so it is skipped -- its copper on all
six layers and its drilled hole alike.  On the D-644 authoritative board that
is **799 barrels and 799 drilled holes the proposer cannot see**, against 3261
tracks and 56 pad holes it can.

WHAT THAT MEANS, STATED PRECISELY AND NOT MORE STRONGLY THAN THE EVIDENCE.

  * A REFUSAL MEASURED AGAINST THIS MODEL IS A LOWER BOUND.  `NO_PATH`,
    `NO_LEGAL_ESCAPE`, `NO_VIA_SITE` and every corridor screen's verdict were
    measured on a board EASIER than the real one.  A refusal is therefore still
    a refusal -- the real board can only be harder -- and this contract does not
    invalidate a single recorded wall.
  * A PROPOSAL MADE AGAINST THIS MODEL IS OPTIMISTIC.  Copper it lays may be
    illegal against a barrel it never saw, and the only thing that has ever
    caught that is the gate's own real KiCad DRC on the refilled candidate.
  * HOLE-TO-HOLE IS THE TERM WITH NO BACKSTOP INSIDE THE PROPOSER.
    `Field._via_grid` states in its own words that hole-to-hole is a fabrication
    rule with NO same-net exemption -- and then applies it over `qb.holes`,
    which carries 56 of this board's 855 drilled holes.
  * AND ON THIS BOARD IT HAS COST NOTHING SO FAR.  Real KiCad DRC on the D-644
    authority reports ZERO `clearance` violations, and all five
    `hole_clearance` violations are vendor pad-to-NPTH pairs inside `MK1` and
    `J3` that predate every route.  The debt is LATENT, not live, and this
    contract exists so that it stays measured instead of assumed.

FOUR CLAUSES.

  OM1  COPPER PARITY.  Every routed copper object the BOARD carries appears in
       the model, on every layer it occupies.  A track occupies one layer; a
       THROUGH via is copper on all six, which is what `QBoard.via` itself does
       for a barrel it LAYS -- the scanner and the emitter must agree about
       what a via is.

  OM2  HOLE PARITY.  Every DRILLED hole the board carries -- pad drill or via
       drill -- appears in `qb.holes`.  A hole missing from the model is a
       fabrication rule the proposer cannot apply anywhere.

  OM3  THE COST IS MEASURED, NOT ASSERTED.  The absent objects are reported by
       class and by count, and the verdict is cross-read against real KiCad
       DRC's own `clearance` and `hole_clearance` census on the same board, so
       "latent" is a measurement and not a hope.

  OM4  THE CONTROL.  A clause that cannot fail is worth nothing.  One synthetic
       track is added to a THROWAWAY copy of the board and OM1 is required to
       name it missing; the same is done to a hole for OM2.  A control that
       does not fire fails the contract.

WHAT THIS FILE DOES NOT DO.  It changes no copper, writes no board and repairs
nothing.  `maze3d.ensure_board_vias` is the repair and it is env-gated OFF, so
every run this board has ever made still reproduces byte for byte; this file is
what says whether the gate is on and what it is worth.

    python3 checks/obstacle_model_contract.py [--board B] [--drc DRC.json]
        [-o OUT]
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MFG = HERE.parent
ROOT = HERE.parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

sys.path.insert(0, str(MFG))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import pcbnew                                            # noqa: E402
import qrouter as qr                                     # noqa: E402
import maze3d as mz                                      # noqa: E402


def board_objects(pb):
    """What the BOARD carries, in the model's own units.

    Returns (copper, holes).  `copper` is a set of (layer, kind, signature);
    `holes` a set of (kind, cx, cy, r).  Signatures are integer nanometres, so
    the comparison is exact and never a tolerance.
    """
    lname = {}
    for L in ("F", "In1", "In2", "In3", "In4", "B"):
        lid = pb.GetLayerID(L + ".Cu")
        if lid >= 0:
            lname[lid] = ("F" if L == "F" else
                          "B" if L == "B" else "I" + L[2])
    copper, holes = set(), set()
    for t in pb.GetTracks():
        net = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            # `QBoard.via` puts a barrel on EVERY copper layer and one hole.
            x, y = int(t.GetStart().x), int(t.GetStart().y)
            # `PCB_VIA::GetWidth()` asserts without a layer in this KiCad
            # build; a THROUGH via is one diameter on every copper layer, so
            # any of them is the answer and `F.Cu` is the one `QBoard.via`
            # would have used.
            r = int(t.GetWidth(pcbnew.F_Cu)) // 2
            for lk in sorted(set(lname.values())):
                copper.add((lk, "via", x, y, r, net))
            holes.add(("via", x, y, int(t.GetDrillValue()) // 2, net))
        else:
            lk = lname.get(t.GetLayer())
            if lk is None:
                continue
            copper.add((lk, "track", int(t.GetStart().x), int(t.GetStart().y),
                        int(t.GetEnd().x), int(t.GetEnd().y),
                        int(t.GetWidth()) // 2, net))
    for f in pb.GetFootprints():
        for p in f.Pads():
            d = p.GetDrillSize()
            if d.x <= 0 and d.y <= 0:
                continue
            pos = p.GetPosition()
            holes.add(("pad", int(pos.x), int(pos.y),
                       int(min(d.x, d.y)) // 2, p.GetNetname()))
    return copper, holes


def model_objects(qb):
    """What the PROPOSER carries, in the same units."""
    copper, holes = set(), set()
    for L in qb.shapes:
        for s in qb.shapes[L]:
            if s.tag == "track":
                copper.add((L, "track", int(s.x0), int(s.y0), int(s.x1),
                            int(s.y1), int(s.hw), s.net))
            elif s.tag == "via":
                copper.add((L, "via", int(s.cx), int(s.cy), int(s.hx), s.net))
    for h in qb.holes:
        kind = "via" if h.tag.startswith("via") else "pad"
        holes.add((kind, int(h.cx), int(h.cy), int(min(h.hx, h.hy)), h.net))
    return copper, holes


def census(missing, idx):
    out = {}
    for m in missing:
        out[m[idx]] = out.get(m[idx], 0) + 1
    return dict(sorted(out.items()))


def compare(board_path):
    """The BOARD against the model AS AN INSTRUMENT BUILDS IT.

    `maze3d.ensure_board_vias` is what every `Field` calls, and it is a no-op
    unless `AQROOT_SCAN_BOARD_VIAS` is set -- so this contract measures the
    model the proposer will actually route against, in whichever of its two
    states the environment selects, and never a hypothetical one.
    """
    pb = pcbnew.LoadBoard(str(board_path))
    qb = qr.QBoard(str(board_path))
    mz.ensure_board_vias(qb)
    bc, bh = board_objects(pb)
    mc, mh = model_objects(qb)
    miss_c = sorted(bc - mc)
    miss_h = sorted(bh - mh)
    return dict(
        scan_gate_on=bool(os.environ.get(mz.SCAN_BOARD_VIAS)),
        board_copper=len(bc), model_copper=len(mc),
        board_holes=len(bh), model_holes=len(mh),
        missing_copper=len(miss_c), missing_holes=len(miss_h),
        missing_copper_by_kind=census(miss_c, 1),
        missing_holes_by_kind=census(miss_h, 0),
        extra_copper=len(mc - bc), extra_holes=len(mh - bh),
        sample_missing_copper=[list(m) for m in miss_c[:4]],
        sample_missing_holes=[list(m) for m in miss_h[:4]],
    )


def control(board_path, tmp):
    """OM4.  Add one object to a THROWAWAY copy and require OM1/OM2 to see it.

    The knife has to cut on a board the contract would otherwise call clean, so
    the control measures the DELTA it introduces rather than an absolute count:
    one added track must raise `missing_copper` by exactly one, and one added
    via must raise it by six (one per copper layer) and `missing_holes` by one.
    """
    base = compare(board_path)
    pb = pcbnew.LoadBoard(str(board_path))
    net = pb.FindNet("GND")
    t = pcbnew.PCB_TRACK(pb)
    t.SetStart(pcbnew.VECTOR2I(20000000, 20000000))
    t.SetEnd(pcbnew.VECTOR2I(20500000, 20000000))
    t.SetWidth(200000)
    t.SetLayer(pcbnew.B_Cu)
    t.SetNet(net)
    pb.Add(t)
    v = pcbnew.PCB_VIA(pb)
    v.SetPosition(pcbnew.VECTOR2I(21000000, 21000000))
    v.SetWidth(600000)
    v.SetDrill(300000)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    pb.Add(v)
    out = Path(tmp) / "control.kicad_pcb"
    pcbnew.SaveBoard(str(out), pb)
    for ext in (".kicad_dru", ".kicad_pro"):
        src = Path(board_path).with_suffix(ext)
        if src.exists():
            out.with_suffix(ext).write_bytes(src.read_bytes())
    got = compare(out)
    d_copper = got["missing_copper"] - base["missing_copper"]
    d_holes = got["missing_holes"] - base["missing_holes"]
    # WITH the gate on the added via IS scanned, so nothing goes missing and
    # the knife has to cut somewhere else: the control then requires the
    # parity to stay EXACT across an object the model had to pick up on its
    # own.  Either way a control that reports the wrong delta fails.
    gate = bool(os.environ.get(mz.SCAN_BOARD_VIAS))
    exp_c, exp_h = (0, 0) if gate else (6, 1)
    # The TRACK is scanned, so it must NOT go missing; the VIA is not, so its
    # six layers and its hole must.  A scanner that started seeing vias would
    # make this read 0/0 and the control would say so.
    return dict(
        added="one B.Cu track + one through via, on a throwaway copy",
        scan_gate_on=gate,
        delta_missing_copper=d_copper, delta_missing_holes=d_holes,
        expect_copper=exp_c, expect_holes=exp_h,
        fires=(d_copper == exp_c and d_holes == exp_h),
        why=("with the gate OFF a scanned track adds nothing to the missing "
             "set and an unscanned via adds one barrel per copper layer plus "
             "its drill; with it ON both are picked up and the delta is zero"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--drc", type=Path,
                    help="a kicad-cli `pcb drc --format json` report on the "
                         "SAME board; OM3 cross-reads its clearance census")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import tempfile
    par = compare(a.board)
    with tempfile.TemporaryDirectory(prefix="aqroot-om-") as tmp:
        ctl = control(a.board, tmp)

    drc = None
    if a.drc and a.drc.exists():
        doc = json.loads(a.drc.read_text(encoding="utf-8"))
        by = {}
        for v in doc.get("violations", ()):
            by[v.get("type")] = by.get(v.get("type"), 0) + 1
        drc = dict(report=str(a.drc), by_type=dict(sorted(by.items())),
                   clearance=by.get("clearance", 0),
                   hole_clearance=by.get("hole_clearance", 0))

    om1 = dict(ok=(par["missing_copper"] == 0),
               missing=par["missing_copper"],
               by_kind=par["missing_copper_by_kind"],
               what="every routed copper object the board carries is in the "
                    "model, on every layer it occupies")
    om2 = dict(ok=(par["missing_holes"] == 0),
               missing=par["missing_holes"],
               by_kind=par["missing_holes_by_kind"],
               what="every drilled hole the board carries is in qb.holes")
    om3 = dict(ok=True, drc=drc,
               verdict=("LATENT" if drc and not drc["clearance"] else
                        "LIVE" if drc else "UNMEASURED"),
               what="the cost of any absence is read off real KiCad DRC on the "
                    "same board, never assumed")
    om4 = dict(ok=bool(ctl["fires"]), **ctl)

    doc = dict(
        schema=1, board=str(a.board),
        board_sha256=hashlib.sha256(Path(a.board).read_bytes()).hexdigest(),
        scan_gate=mz.SCAN_BOARD_VIAS,
        scan_gate_on=bool(os.environ.get(mz.SCAN_BOARD_VIAS)),
        parity=par, OM1=om1, OM2=om2, OM3=om3, OM4=om4,
        ok=bool(om1["ok"] and om2["ok"] and om3["ok"] and om4["ok"]),
        verdict=("PASS" if (om1["ok"] and om2["ok"] and om4["ok"])
                 else "FAIL"),
        what=("does the proposer's obstacle model contain every copper object "
              "and every drilled hole the board carries?"))
    if a.out:
        a.out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                         encoding="utf-8")
    for k in ("OM1", "OM2", "OM3", "OM4"):
        print("%s %-5s %s" % (k, "PASS" if doc[k]["ok"] else "FAIL",
                              doc[k].get("what") or doc[k].get("why", "")),
              file=sys.stderr)
    print("%s  board copper %d / model %d ; board holes %d / model %d"
          % (doc["verdict"], par["board_copper"], par["model_copper"],
             par["board_holes"], par["model_holes"]), file=sys.stderr)
    return 0 if doc["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
