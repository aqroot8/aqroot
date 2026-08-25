# -*- coding: utf-8 -*-
"""FBV2-P2-002F -- THE VALIDATED BATTERY-BLOCK PLACEMENT ECO.

Nothing here was chosen by eye.  Section 3 forbids it and every coordinate is
the output of a measured search:

  U18 + the divider / gate ring   place_search_002f.py   candidate C00, the
        best of 16 fully-scored survivors of 1 331 poses that cleared courtyard
        collision, the section 4 Kelvin envelope and a 1.50 mm trunk corridor.
  the dead-cell cluster           place_deadcell_002f.py
  TP15                            measured against the real router at 7 sites.

WHAT CHANGED, AND WHY (PR-25 .. PR-29)

PR-25  U18 rotated 90 -> 180 and moved (3.000, 72.400) -> (8.000, 65.250).
       At 002E's pose U18 sat at x 1.205..4.795 with R75 immediately south and
       the 0603 divider wall at x 7.300..10.350, so every north-row pin escaped
       through the same 2.505 mm corridor and R75's own 3.35 mm pads stood
       between U18.8 and its Kelvin target.  6 of 8 pins escaped, 7 at best.
       At rot 180 the two pin rows face EAST and WEST, U18 straddles R75's
       midline, and pins 8 and 9 look straight at R75.2 and R75.1.

PR-28  the divider wall stops being a wall.  R76..R83 are no longer a 16 mm
       barrier at a single x: each is placed BY THE U18 PIN IT SERVES.  That is
       what removes the shared corridor, rather than merely widening it.

PR-26  no Q3 rotation and no change to the pack-current device order.  The
       Q3-area passives R82, R83 and TP17 vacate the south lane that Q3's gate
       and CS nets have to share.

PR-27  the dead-cell / recovery cluster is re-floorplanned around its own
       comparator.  D11, D12, C60, C61 and R84 were stranded 40..64 mm north of
       the network they belong to.  Every megohm node is now inside section 6's
       15 mm TARGET - worst 14.25 mm against 64.01 mm before.

PR-29  TP15 moves to the MAX17048 sense branch instead of dictating it.

Values, devices, thresholds and connectivity are untouched, and so is the
J4 -> F1 -> Q2 -> Q3 -> R75 -> D9 -> U11.2 high-current chain: R75, Q2, Q3, F1,
J4, D9, U11 and U14 DO NOT MOVE.
"""
import os, sys, json
import pcbnew

MOVES = {
    # ---- U18 and its divider / gate ring  (PR-25, PR-28, PR-31)
    'U18': (8.000, 65.250, 180.0, 'B.Cu'),
    'R76': (7.500, 59.000, 90.0, 'B.Cu'),
    'R77': (11.000, 62.500, 0.0, 'B.Cu'),
    'R78': (12.500, 60.500, 0.0, 'B.Cu'),
    'R79': (14.500, 62.500, 0.0, 'B.Cu'),
    'R80': (5.500, 70.500, 90.0, 'B.Cu'),
    'R81': (5.000, 73.000, 0.0, 'B.Cu'),
    'R82': (7.500, 73.000, 90.0, 'B.Cu'),
    'R83': (5.000, 75.500, 0.0, 'B.Cu'),
    'C57': (8.500, 56.500, 0.0, 'B.Cu'),
    'C58': (12.000, 74.500, 0.0, 'B.Cu'),
    'TP17': (9.500, 60.500, 0.0, 'B.Cu'),
    'TP19': (4.000, 77.500, 0.0, 'B.Cu'),
    # ---- the five stranded dead-cell parts, plus D10 and TP22  (PR-27)
    'D10': (12.000, 30.000, 0.0, 'B.Cu'),
    'D11': (15.500, 30.000, 0.0, 'B.Cu'),
    'D12': (12.000, 17.000, 0.0, 'B.Cu'),
    'C60': (6.500, 28.500, 90.0, 'B.Cu'),
    'C61': (12.000, 22.000, 0.0, 'B.Cu'),
    'R84': (12.000, 28.000, 180.0, 'B.Cu'),
    'TP22': (12.500, 14.500, 0.0, 'B.Cu'),
    # ---- the MAX17048 test point  (PR-29)
    'TP15': (1.800, 79.900, 0.0, 'B.Cu'),
}

# section 9 / section 19: these must be byte-for-byte where they were.
FROZEN = ['R75', 'Q2', 'Q3', 'F1', 'J4', 'D9', 'U11', 'U14', 'C59', 'TP34',
          'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9']


def rect(f):
    cy = f.GetCourtyard(f.GetLayer())
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox()
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
            bb.GetRight() / 1e6, bb.GetBottom() / 1e6)


def ovl(a, b, gap=0.0):
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or
                a[3] + gap < b[1] or b[3] + gap < a[1])


def apply(pcb, report=True):
    b = pcbnew.LoadBoard(pcb)
    fp = {f.GetReference(): f for f in b.GetFootprints()}
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

    # ---- the frozen parts really are frozen
    frozen_bad = [r for r in FROZEN if r in MOVES]
    if frozen_bad:
        raise SystemExit('ECO would move a frozen part: %s' % frozen_bad)

    # ---- collision audit, side-aware, against EVERY footprint and rule area
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
                # opposite faces meet only through a hole
                if not any(p.GetDrillSizeX() > 0 for p in g.Pads()) and                    not any(p.GetDrillSizeX() > 0 for p in f.Pads()):
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
        raise SystemExit('PLACEMENT COLLISION: %s' % bad)

    # A footprint move changes where the In1 GND plane has to clear its pads,
    # so the plane must be refilled or every later DRC and connectivity read is
    # answering about the old geometry.
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


if __name__ == '__main__':
    apply(sys.argv[1], report='--quiet' not in sys.argv)
    print('ECO applied to %s: %d footprints moved, 0 collisions'
          % (sys.argv[1], len(MOVES)))
