#!/usr/bin/env python3
"""D-691 CONTROLS: the side-aware courtyard comparison must CHANGE the answer
for an F/B pair and must NOT change it for a same-side pair.  A relaxation that
cannot refuse is not a check; a relaxation that changes nothing is vacuous.

Read-only.  Every pair is measured on the AUTHORITY, both ways -- with the old
whole-board predicate and with the new shared-side one -- and printed side by
side.  It also proves the two files agree, because they are two copies of one
rule and the second one is the one that gets forgotten."""
import json, sys
from pathlib import Path
ROOT = Path("/home/aqroot8/aqroot-demo")
HERE = ROOT / "hardware/demo/manufacturing"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "checks"))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import pcbnew
import apply_part_shift as aps
import placement_contract as pc

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
b = pcbnew.LoadBoard(str(BOARD))
fp = {f.GetReference(): f for f in b.GetFootprints()}


def bbox(f):
    x = f.GetBoundingBox(False, False)
    return (x.GetLeft(), x.GetTop(), x.GetRight(), x.GetBottom())


def boxes_touch(a, b):
    return (a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3])


def side_of(f):
    return "B" if f.IsFlipped() else "F"


rows = []
# EVERY CONTROL IS A MOVE, because the board as it stands is legal and a legal
# board exercises neither predicate.  Each row moves ONE part to a named place
# and asks both predicates about the pair the move creates.
CASES = [
    # THE PAIR THE FIX IS FOR: a B.Cu test point under SW9, an SMD slide switch
    # whose footprint draws F.CrtYd and nothing on B.CrtYd.  Must CHANGE.
    ("TP13", (62.300, 90.800), "SW9", "B under an F.CrtYd-only part"),
    ("TP6", (70.000, 84.000), "SW9", "B under an F.CrtYd-only part"),
    ("TP7", (65.000, 87.000), "SW9", "B under an F.CrtYd-only part"),
    # SAME SIDE, AND THE OVERLAP IS REAL.  Must NOT change, and must refuse.
    ("TP13", (62.250, 96.000), "TP47", "B onto B -- a real collision"),
    ("TP6", (66.600, 101.400), "U12", "B onto B -- a real collision"),
    ("R127", (66.600, 96.600), "L1", "B onto B -- a real collision"),
    # F ONTO F, the other half of the same-side claim.  Must refuse.
    ("R120", (64.200, 99.000), "SW2", "F onto F -- a real collision"),
    ("R27", (66.700, 86.500), "SW9", "F onto F -- a real collision"),
]
for ref, (x, y), other, why in CASES:
    f, g = fp[ref], fp[other]
    keep = f.GetPosition()
    f.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6))))
    old = boxes_touch(bbox(f), bbox(g))
    sa, sb = aps._sides(f), aps._sides(g)
    new = bool(sa & sb) and old
    f.SetPosition(keep)
    rows.append(dict(moved=ref, to_mm=[x, y], against=other, why=why,
                     moved_side=side_of(f), against_side=side_of(g),
                     moved_courtyards=sorted(sa), against_courtyards=sorted(sb),
                     boxes_touch=old, old_verdict=old, new_verdict=new,
                     changed=(old != new)))

# the two implementations must agree on EVERY pair of footprints on the board
pre = pc.read(BOARD)
pc_pairs = pc.overlaps(pre[0])
disagree = []
for a in sorted(fp):
    aps_hits = set(aps.courtyard_overlaps(b, a))
    pc_hits = {y if x == a else x for (x, y) in pc_pairs if a in (x, y)}
    if aps_hits != pc_hits:
        disagree.append(dict(ref=a, apply_part_shift=sorted(aps_hits),
                             placement_contract=sorted(pc_hits)))

doc = dict(
    schema=1, decision="D-691", board=str(BOARD),
    question="does the shared-side predicate change the F/B answer, leave the "
             "same-side answer alone, and do the two implementations agree",
    controls=rows,
    changed=[r for r in rows if r["changed"]],
    unchanged_same_side=[r for r in rows if not r["changed"]],
    non_vacuous=any(r["changed"] for r in rows),
    still_refuses=any(r["new_verdict"] for r in rows),
    every_cross_side_case_changed=all(
        r["changed"] for r in rows if not (set(r["moved_courtyards"])
                                           & set(r["against_courtyards"]))),
    every_same_side_collision_still_refused=all(
        r["new_verdict"] for r in rows
        if (set(r["moved_courtyards"]) & set(r["against_courtyards"]))),
    implementations_agree=(not disagree), disagreements=disagree,
    pairs_flagged_board_wide=len(pc_pairs))
print(json.dumps(doc, indent=1, sort_keys=True))
