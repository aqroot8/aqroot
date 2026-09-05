#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: WHAT IS THE VIA FIELD *FOR*, AND WHAT DOES IT COST
THE ONLY SPARE SIGNAL LAYER THIS BOARD HAS?

D-634 measured the layer partition and named the via field the cause: this
board has **790 THROUGH barrels**, a through barrel is copper and a drilled
hole on EVERY layer, and `In2.Cu` -- the one inner layer the stack-up does not
give to a plane -- is cut into hundreds of pieces by them.  Its own verdict was
that the next question is bounded, read-only and worth more than anything else
on the board: *how many of the 790 are load-bearing, and how much of `In2.Cu`'s
partitioning would disappear if a MEASURED subset were retired or moved?*

This is that measurement, and it is in three parts because the answer has three
independent pieces.

## 1. WHAT EACH BARREL IS ATTACHED TO

A barrel is `TRACK_TIED` when a track endpoint of its own net lands on it, and
the LAYERS of those endpoints say what it does: two or more distinct layers and
it is a genuine LAYER CHANGE; exactly one and it is a TERMINAL DROP, whose far
end must be a pour, a plane or nothing at all.  `PAD_ONLY` sits on a same-net
land with no track; `FREE_STITCH` has neither, and is the only class this board
could retire without orphaning copper.

## 2. WHICH LAYERS IT ACTUALLY SERVES, AND WHICH IT MERELY TRANSITS

A barrel SERVES a layer when its own net has copper there AT THE BARREL: a
track endpoint, a same-net land, or a same-net FILLED ZONE polygon that
contains the barrel's centre.  Zone fill is read from KiCad's own
`GetFilledPolysList`, so plane membership is read and never modelled.

Everything between the shallowest and deepest layer it serves, it TRANSITS: it
is a hole and an annular ring there and it serves nothing.  That is the whole
finding of this screen, so it is the classification the report is built around:

    SERVES_In2      the net has copper on In2.Cu at this barrel
    TRANSITS_In2    the barrel's served span straddles In2.Cu and serves
                    nothing there -- it is a PURE OBSTACLE on the one spare
                    signal layer
    AVOIDS_In2      the served span lies entirely on one side of In2.Cu, so
                    the barrel crosses it for NO reason at all and a blind or
                    buried barrel would not

## 3. WHAT THE PARTITION WOULD BE WITHOUT THEM

The classification is only worth what it buys, so the same partition
measurement D-634 published (`screen_layer_pockets.py`: `QBoard.grid` at a real
width and clearance, then 8-connected components of the free cells) is re-run
with named SUBSETS of the barrel field withheld from the obstacle set.  The
board is never written and no scratch board is produced: `qrouter._scan`
already skips `PCB_VIA`, and `incremental_router.inject_existing_via_obstacles`
is what makes barrels visible, so withholding a subset is done by injecting
only its complement into a fresh `QBoard`.  The as-built arm injects all 790
and MUST reproduce D-634's published figures; it is the control, and a run
whose control does not match is a run whose other arms mean nothing.

    asbuilt     all 790 barrels                        (CONTROL)
    no_avoid    minus AVOIDS_In2                       (buildable TODAY)
    no_transit  minus AVOIDS_In2 and TRANSITS_In2      (the technology ceiling)
    no_vias     minus every barrel                     (the absolute ceiling)

## WHAT A NUMBER HERE DOES NOT MEAN

Nothing here is a proposal to delete copper.  A barrel withheld in an arm is a
COUNTERFACTUAL, not a candidate: a terminal drop carries current to a plane and
retiring it orphans a land.  The arms price a STACK-UP question -- blind and
buried barrels are an owner decision and a fab cost -- and pricing it is the
only way that decision can be taken on evidence rather than on instinct.

    python3 screen_via_field.py [--board B] [--layers In2,B,F,In3]
        [--net NET] [--width NM] [--clearance NM] [--grid NM]
        [--arms asbuilt,no_avoid,no_transit,no_vias] [--top N] [-o OUT]
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# THE PHYSICAL STACK ORDER, WHICH IS NOT THE LAYER-ID ORDER.  KiCad numbers
# F.Cu 0 and B.Cu 2 with the inner layers above both, so "between F and B" is
# meaningless on the ids and has to be read off this sequence.  `qrouter`'s own
# short names are used so a layer named here is a layer nameable to every other
# instrument on this board.
STACK = ("F", "I1", "I2", "I3", "I4", "B")
SHORT = {"F": "F", "I1": "In1", "I2": "In2", "I3": "In3", "I4": "In4",
         "B": "B"}


def stack_ids(pcbnew):
    return {"F": pcbnew.F_Cu, "I1": pcbnew.In1_Cu, "I2": pcbnew.In2_Cu,
            "I3": pcbnew.In3_Cu, "I4": pcbnew.In4_Cu, "B": pcbnew.B_Cu}


def census(pcbnew, b, target="I2"):
    """Every PCB_VIA, what it is attached to, and which layers it serves.

    Attachment is exact and geometric: a track endpoint at the barrel's own
    centre, a same-net land the centre hits, or a same-net filled zone polygon
    that contains the centre.  None of the three is a model -- KiCad wrote all
    three -- and that matters, because the whole argument of this screen is
    that a barrel serves fewer layers than it drills.
    """
    ids = stack_ids(pcbnew)
    order = [L for L in STACK if b.IsLayerEnabled(ids[L])]
    idx = {L: i for i, L in enumerate(order)}
    ti = idx.get(target)

    zones = [z for z in b.Zones() if not z.GetIsRuleArea()]
    tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]

    ends = collections.defaultdict(list)
    for t in tracks:
        for p in (t.GetStart(), t.GetEnd()):
            ends[(t.GetNetCode(), p.x, p.y)].append(t.GetLayer())
    pads = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            pads[p.GetNetCode()].append((f.GetReference() + "." + p.GetNumber(),
                                         p))

    out = []
    for v in vias:
        pos, nc = v.GetPosition(), v.GetNetCode()
        tl = ends.get((nc, pos.x, pos.y), [])
        by_track = sorted({L for L in order if ids[L] in tl})
        by_pad, by_zone, land = [], [], None
        for L in order:
            for tag, p in pads.get(nc, []):
                if p.IsOnLayer(ids[L]) and p.HitTest(pos):
                    by_pad.append(L)
                    land = land or tag
                    break
            for z in zones:
                if (z.GetNetCode() == nc and z.IsOnLayer(ids[L])
                        and z.GetFilledPolysList(ids[L]).Collide(pos, 0)):
                    by_zone.append(L)
                    break
        served = sorted(set(by_track) | set(by_pad) | set(by_zone),
                        key=lambda L: idx[L])

        if len(by_track) >= 2:
            attach = "LAYER_CHANGE"
        elif len(by_track) == 1:
            attach = "TERMINAL_DROP"
        elif by_pad:
            attach = "PAD_ONLY"
        else:
            attach = "FREE_STITCH"

        if not served:
            role = "SERVES_NOTHING"
        elif target in served:
            role = "SERVES_%s" % SHORT[target]
        elif idx[served[0]] < ti < idx[served[-1]]:
            role = "TRANSITS_%s" % SHORT[target]
        else:
            role = "AVOIDS_%s" % SHORT[target]

        out.append(dict(
            net=v.GetNetname(), x=pos.x, y=pos.y,
            dia=v.GetWidth(), drill=v.GetDrillValue(),
            attach=attach, role=role, land=land,
            track_layers=[SHORT[L] for L in by_track],
            zone_layers=[SHORT[L] for L in by_zone],
            pad_layers=[SHORT[L] for L in by_pad],
            served=[SHORT[L] for L in served],
            span=("%s..%s" % (SHORT[served[0]], SHORT[served[-1]])
                  if served else "NONE")))
    return out, order


def components(np, free):
    """Sizes of the 8-connected components of a boolean mask, descending.

    Lifted verbatim in behaviour from `screen_layer_pockets.py` so the two
    screens' `pieces` counts are the same number and not two names for it.
    """
    lab = np.where(free, np.arange(free.size).reshape(free.shape) + 1, 0)
    while True:
        prev = lab
        m = lab.copy()
        for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
            m = np.maximum(m, np.roll(lab, sh, axis=ax))
        for dy in (1, -1):
            for dx in (1, -1):
                m = np.maximum(m, np.roll(np.roll(lab, dy, axis=0), dx,
                                          axis=1))
        lab = np.where(free, m, 0)
        if np.array_equal(lab, prev):
            break
    ids, counts = np.unique(lab[lab > 0], return_counts=True)
    return sorted(counts.tolist(), reverse=True)


def inject(qb, QR, rows):
    """Make exactly these barrels visible to `QBoard`, item for item as
    `incremental_router.inject_existing_via_obstacles` does it -- an RR of
    copper on every Cu layer plus a drilled hole.  Withholding a barrel is
    therefore the ONLY difference between two arms, and the arm that injects
    all of them is the arm that reproduces every published figure."""
    for v in rows:
        for L in qb.cu:
            qb.shapes[L].append(QR.RR(v["x"], v["y"], v["dia"] / 2.0,
                                      v["dia"] / 2.0, v["dia"] / 2.0,
                                      0, v["net"], "via"))
        qb.holes.append(QR.RR(v["x"], v["y"], v["drill"] / 2.0,
                              v["drill"] / 2.0, v["drill"] / 2.0,
                              0, v["net"], "via/hole"))
    qb._inc_vias_injected = True
    return len(rows)


ARMS = {
    # name        -> roles WITHHELD from the obstacle set
    "asbuilt":    (),
    "no_avoid":   ("AVOIDS",),
    "no_transit": ("AVOIDS", "TRANSITS"),
    "no_vias":    ("AVOIDS", "TRANSITS", "SERVES", "SERVES_NOTHING"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--target", default="I2",
                    help="the layer the census is ABOUT -- the one whose "
                         "partition the barrels are being priced against")
    ap.add_argument("--layers", default="",
                    help="layers to re-partition per arm; default is the "
                         "target alone, which is the only layer the arms "
                         "differ interestingly on and by far the cheapest")
    ap.add_argument("--net", default="/I2C_SCL_INT",
                    help="the net whose OWN copper is exempt, as "
                         "screen_layer_pockets.py names it, so the control "
                         "arm is comparable field for field")
    ap.add_argument("--width", type=int, default=200000)
    ap.add_argument("--clearance", type=int, default=200000)
    ap.add_argument("--grid", type=int, default=150000)
    ap.add_argument("--arms", default="asbuilt,no_avoid,no_transit,no_vias")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--census-only", action="store_true",
                    help="skip the partition arms; the census alone is the "
                         "cheap question and it is the one that says whether "
                         "the expensive one is worth asking")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import numpy as np
    import pcbnew
    import qrouter as QR

    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    b = pcbnew.LoadBoard(str(a.board))
    rows, order = census(pcbnew, b, a.target)
    tgt = SHORT[a.target]

    by_role = collections.Counter(v["role"] for v in rows)
    by_attach = collections.Counter(v["attach"] for v in rows)
    by_span = collections.Counter(v["span"] for v in rows)
    cross = collections.Counter()
    for v in rows:
        cross[(v["net"], v["role"], v["attach"])] += 1
    nets = collections.defaultdict(collections.Counter)
    for v in rows:
        nets[v["net"]][v["role"]] += 1

    print(" %d barrels: %s" % (len(rows), "  ".join(
        "%s=%d" % (k, n) for k, n in sorted(by_role.items()))),
        file=sys.stderr, flush=True)
    print(" attachment: %s" % "  ".join(
        "%s=%d" % (k, n) for k, n in sorted(by_attach.items())),
        file=sys.stderr, flush=True)

    arms = []
    if not a.census_only:
        layers = ([x for x in a.layers.split(",") if x] if a.layers
                  else [a.target])
        for name in [x for x in a.arms.split(",") if x]:
            withheld = ARMS[name]
            keep = [v for v in rows
                    if not any(v["role"].startswith(w) for w in withheld)]
            # A FRESH QBoard PER ARM.  `QBoard` memoises its obstacle list and
            # `inject` is add-only, so an arm that re-used the previous arm's
            # board would be measuring the union of the two.
            qb = QR.QBoard(str(a.board))
            n = inject(qb, QR, keep)
            rec = dict(arm=name, withheld=list(withheld),
                       barrels_injected=n,
                       barrels_withheld=len(rows) - n, layers=[])
            for L in layers:
                blk = qb.grid(L, a.net, a.width, a.clearance, a.clearance,
                              qb.ex0, qb.ey0, qb.ex1, qb.ey1, a.grid)
                free = ~blk
                cell = (a.grid / 1e6) ** 2
                sizes = components(np, free)
                tot = float(sum(sizes)) or 1.0
                rec["layers"].append(dict(
                    layer=SHORT.get(L, L), cells=int(free.size),
                    free_cells=int(free.sum()),
                    free_mm2=round(float(free.sum()) * cell, 2),
                    pieces=len(sizes),
                    largest_mm2=round(sizes[0] * cell, 2) if sizes else 0.0,
                    largest_share=round(sizes[0] / tot, 4) if sizes else 0.0,
                    piece_mm2=[round(s * cell, 2) for s in sizes[:a.top]],
                    pieces_over_1mm2=sum(1 for s in sizes if s * cell >= 1.0),
                    obstacles=len(qb.obstacles(L, a.net))))
                r = rec["layers"][-1]
                print("  %-10s %-4s free %8.1f mm2 in %5d pieces; largest "
                      "%8.1f mm2 (%.1f%%); %d barrels"
                      % (name, r["layer"], r["free_mm2"], r["pieces"],
                         r["largest_mm2"], 100.0 * r["largest_share"], n),
                      file=sys.stderr, flush=True)
            arms.append(rec)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(
        schema=1, board=str(a.board), board_sha256=sha,
        authoritative_unchanged=(sha == after),
        target=tgt, net=a.net, width=a.width, clearance=a.clearance,
        grid=a.grid, stack=[SHORT[L] for L in order],
        question=("what is each of this board's THROUGH barrels attached to, "
                  "which layers does it SERVE as against merely TRANSIT, and "
                  "how much of %s's partitioning would a named subset of them "
                  "account for" % tgt),
        method=("read-only; attachment and plane membership read from KiCad's "
                "own track endpoints, pad hit-tests and filled zone polygons; "
                "the partition arms are screen_layer_pockets.py's measurement "
                "with only a named subset of barrels injected into a FRESH "
                "QBoard, which is possible because qrouter._scan skips "
                "PCB_VIA and injection is what makes a barrel visible.  "
                "Withholding a barrel is a COUNTERFACTUAL and never a "
                "proposal: the board is not written and no copper moves"),
        barrels=len(rows),
        by_role=dict(sorted(by_role.items())),
        by_attach=dict(sorted(by_attach.items())),
        by_span=dict(sorted(by_span.items())),
        by_net=dict(sorted((k, dict(sorted(v.items())))
                           for k, v in nets.items())),
        role_attach=dict(sorted(
            ("%s|%s|%s" % k, n) for k, n in cross.items())),
        arms=arms,
        vias=sorted(rows, key=lambda v: (v["net"], v["x"], v["y"])))
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
