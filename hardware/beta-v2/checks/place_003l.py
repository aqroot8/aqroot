# -*- coding: utf-8 -*-
"""FBV2-P2-003L / D-285 -- THE MINIMAL LANDING-OPENING PLACEMENT ECO for the
proven D-275 southern BAT_PROTECTED_P bridge (candidate c, D-283).

OWNER DECISION D-284 (2026-08-28, Alpha, ratifying the CTO call): open a LEGAL
southern BAT_PROTECTED_P landing by a bounded placement spread of the C36 / C25 /
U11 / BQ25185_SYS neighbourhood -- NOT a corridor widening, NOT a broad refloorplan.

003K (D-283) MEASURED that the disjoint southern LANE holds >= 1.20 mm and clears
the taps, but the only forced-south target-island pad (the far-east node cap
`C36.1`) has NO LEGAL landing: the exact D-275 exit array lands 0.0726 mm from
C36's own GND pad (a B.Cu stub vs pad 2) and 0.0864 mm from R68's BQ25185_SYS
(`BAT_MAIN` class) pad (an F.Cu tie vs a fixed F.Cu pad).  Two INDEPENDENT
blockers, and their fix is forced by geometry, not chosen by eye:

  BLOCKER 1  C36's own GND pad sits 1.55 mm EAST of the landing pad, on the SAME
             footprint, so the exit-array clearance to it is INVARIANT under any
             pure C36 TRANSLATION (both pads move together).  The only lever is a
             C36 ROTATION.  Rotating C36 to 270 deg (vertical, BPP pad NORTH, GND
             pad SOUTH) moves the GND pad 1.55 mm SOUTH of the north-poking exit
             array -- clearance 0.0726 -> 0.4750 mm.

  BLOCKER 2  R68's BQ25185_SYS pad (`R68` is `0R DNP`, but KiCad-connected: the
             BQ25185_SYS net carries 16 pads) sits just NORTH of the exit array.
             A vertical C36 is 3.05 mm tall, so it cannot sit far enough SOUTH to
             clear R68 without colliding C5's courtyard to the south.  The minimal
             fix moves C36 ~1.35 mm SOUTH (clearing R68 by distance: 0.0864 ->
             0.2941 mm) and RELOCATES the single courtyard obstruction, the +3V3 /
             GND decoupler C5, ~1.3 mm WEST + rotate (its plane-net decoupling role
             gives it routing latitude R68's 16-pad SYS net does not).

Both moves are STRICTLY NECESSARY and INSIDE the approved landing neighbourhood
(C5 is 1.9 mm from C36), and are recorded here rather than taken silently.  R68 is
deliberately NOT moved: it carries a real 16-pad net and has no nearby legal home,
whereas the C36 south move clears it by distance.

MEASURED on the reconstructed sparse placed board + the D-275 south bridge
(`bridge_probe_003l`): the C36.1 landing opens, the bridge lays entry 4 / >= 1.20 mm
(1.40 mm achieved) F.Cu traverse / exit 4, disjoint (ywest 82.4 mm > 74.7), and the
DRC delta vs the 003K board is EXACTLY the two landing clearances removed and
NOTHING added (clearance 4 -> 2, the two survivors are the pre-existing WEST
LTC-block issues; courtyards_overlap stays 3, every other class identical).
Governing achieved landing clearance 0.2941 mm (R68 BAT_MAIN), 47% over the
0.200 mm floor.  No rule relaxed; the 0.200 mm clearance and 0.25 mm hole-to-hole
floors are ENFORCED.  D-275 and D-277..D-283 preserved.

Applied ON TOP of the FBV2-P2-002F placement ECO (which must already be on the
board).  For the supervised full run, pass `place_003l.json` via `AQROOT_ECO_EXTRA`
alongside `AQROOT_BRIDGE_EARLY=1 AQROOT_BRIDGE_SOUTH=1` -- no driver edit is needed
(the 002J ECO_EXTRA override path already merges extra moves into the 002F ECO and
runs its collision audit over the whole set).
"""
import os
import sys
import json
import pcbnew

# ref -> (x_mm, y_mm, rot_deg, layer).  The two moves, and nothing else.
MOVES = {
    # C36 100nF: rotate to vertical (270 deg -> BPP pad 1 NORTH, GND pad 2 SOUTH)
    # and shift ~1.35 mm SOUTH.  Opens BLOCKER 1 (own GND 0.0726 -> 0.4750 mm) by
    # the rotation and BLOCKER 2 (R68 0.0864 -> 0.2941 mm) by the south distance.
    'C36': (63.75, 75.10, 270.0, 'B.Cu'),
    # C5 100nF +3V3/GND decoupler: the sole courtyard obstruction to the vertical
    # C36.  Move ~1.3 mm WEST + rotate 90 (vertical) into the gap east of U3, clear
    # of the bridge's western exit copper (C5 GND -> bridge 0.3003 mm).
    'C5': (61.95, 75.15, 90.0, 'B.Cu'),
}

# Parts the 003L ruling and the task brief hold frozen; a coding slip that put one
# of them in MOVES must fail loudly, exactly as place_p2_002f guards its own.
FROZEN = ['D9', 'U18', 'R75', 'R76', 'R77', 'R78', 'R79', 'R80', 'R81', 'R82',
          'R83', 'Q3', 'Q2', 'F1', 'J4', 'U11', 'U14', 'U19', 'D10', 'C58',
          'C59', 'R68']


def rect(f):
    cy = f.GetCourtyard(f.GetLayer())
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox()
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
            bb.GetRight() / 1e6, bb.GetBottom() / 1e6)


def ovl(a, b, gap=0.0):
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or
                a[3] + gap < b[1] or b[3] + gap < a[1])


def apply(pcb, report=True):
    """Move C36/C5 on `pcb` (which must already carry the 002F placement), audit
    the courtyard/edge/rule-area legality exactly as place_p2_002f does, refill the
    plane and save.  Raises SystemExit on any frozen-part or collision violation."""
    b = pcbnew.LoadBoard(pcb)
    fp = {f.GetReference(): f for f in b.GetFootprints()}

    frozen_bad = [r for r in FROZEN if r in MOVES]
    if frozen_bad:
        raise SystemExit('003L ECO would move a frozen part: %s' % frozen_bad)

    old = {}
    for ref, (x, y, rot, lay) in MOVES.items():
        f = fp[ref]
        old[ref] = (round(f.GetPosition().x / 1e6, 3),
                    round(f.GetPosition().y / 1e6, 3),
                    round(f.GetOrientationDegrees(), 1),
                    b.GetLayerName(f.GetLayer()))
        if b.GetLayerName(f.GetLayer()) != lay:
            f.Flip(f.GetPosition(), False)
        f.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6))))
        f.SetOrientationDegrees(rot)
    b.BuildConnectivity()

    bad = []
    for ref in MOVES:
        f = fp[ref]
        ca = rect(f)
        eb = b.GetBoardEdgesBoundingBox()
        if (ca[0] < eb.GetLeft() / 1e6 or ca[1] < eb.GetTop() / 1e6 or
                ca[2] > eb.GetRight() / 1e6 or ca[3] > eb.GetBottom() / 1e6):
            bad.append((ref, 'board edge'))
        for g in b.GetFootprints():
            if g.GetReference() == ref:
                continue
            cb = rect(g)
            if not ovl(ca, cb):
                continue
            if g.IsFlipped() != f.IsFlipped():
                if (not any(p.GetDrillSizeX() > 0 for p in g.Pads()) and
                        not any(p.GetDrillSizeX() > 0 for p in f.Pads())):
                    continue
            bad.append((ref, g.GetReference()))
        for z in b.Zones():
            if not z.GetIsRuleArea():
                continue
            zb = z.GetBoundingBox()
            if ovl(ca, (zb.GetLeft() / 1e6, zb.GetTop() / 1e6,
                        zb.GetRight() / 1e6, zb.GetBottom() / 1e6)):
                bad.append((ref, 'ruleArea:' + (z.GetZoneName() or '?')))
    if bad:
        raise SystemExit('003L PLACEMENT COLLISION: %s' % bad)

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(pcb)
    if report:
        out = {}
        for ref in sorted(MOVES):
            f = fp[ref]
            out[ref] = dict(old=old[ref],
                            new=(round(f.GetPosition().x / 1e6, 3),
                                 round(f.GetPosition().y / 1e6, 3),
                                 round(f.GetOrientationDegrees(), 1),
                                 b.GetLayerName(f.GetLayer())),
                            pads=[(p.GetNumber(), p.GetNetname(),
                                   round(p.GetPosition().x / 1e6, 3),
                                   round(p.GetPosition().y / 1e6, 3))
                                  for p in f.Pads()])
        print(json.dumps(out, indent=1))
    return old


def write_json(path=None):
    """Emit the ECO_EXTRA JSON the driver consumes on the supervised run."""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'place_003l.json')
    json.dump({r: list(v) for r, v in MOVES.items()}, open(path, 'w'), indent=1)
    return path


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--emit-json':
        print('wrote', write_json())
    else:
        apply(sys.argv[1], report='--quiet' not in sys.argv)
        print('003L ECO applied to %s: %d footprints moved, 0 collisions'
              % (sys.argv[1], len(MOVES)))
