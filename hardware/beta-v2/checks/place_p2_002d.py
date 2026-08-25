# -*- coding: utf-8 -*-
"""FBV2-P2-002D sections 2-4: the three approved local placement corrections.

TP17  the LTC_GATE test point, marooned east of the 0603 divider wall with no
      corridor to reach it.  Re-homed beside R76, the LTC4368 GATE resistor.
C59   1 uF 25 V on BAT_RAW.  Drawn on the protection row of the schematic
      immediately left of R75, i.e. the INPUT bulk capacitor of the LTC4368
      stage - and placed 40 mm away in the south-west corner, which needed
      44.4 mm of 0.30 mm copper to reach.  Re-homed beside F1 / Q2.
C58   1 uF 25 V on BAT_PROTECTED_P.  Same schematic row, immediately right of
      R75: the OUTPUT bulk capacitor of the same stage.  Its 25 V rating is the
      tell - C25 next to the charger is a 10 V part, so C58 belongs to the
      protection stage, not to U11.  Re-homed beside D9, on the trunk.

Nothing else moves.  The scarce 2.52 mm corridor between R75 and the resistor
wall at x = 7.30 is deliberately left empty: it fits exactly one 1.50 mm trunk
with clearance, and a part placed in it would cost the BAT_PROTECTED_P route.
"""
import os, sys, math, json
import pcbnew

MOVES = {
    # ref: (x_mm, y_mm, rotation_deg, layer)
    'TP17': (12.500, 76.000, 0.0, 'B.Cu'),
    'C59': (8.000, 41.500, 90.0, 'B.Cu'),
    'C58': (13.000, 68.500, 0.0, 'B.Cu'),
}


def courtyard(f, board):
    cy = f.GetCourtyard(f.GetLayer())
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox()
    return (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())


def overlaps(a, b, gap=0):
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or
                a[3] + gap < b[1] or b[3] + gap < a[1])


def apply(pcb, report=True):
    b = pcbnew.LoadBoard(pcb)
    old = {}
    for ref, (x, y, rot, lay) in MOVES.items():
        f = [g for g in b.GetFootprints() if g.GetReference() == ref][0]
        old[ref] = (f.GetPosition().x / 1e6, f.GetPosition().y / 1e6,
                    f.GetOrientationDegrees(), b.GetLayerName(f.GetLayer()))
        if b.GetLayerName(f.GetLayer()) != lay:
            f.Flip(f.GetPosition(), False)
        f.SetPosition(pcbnew.VECTOR2I(int(x * 1e6), int(y * 1e6)))
        f.SetOrientationDegrees(rot)
    b.BuildConnectivity()

    # collision audit: every moved part against every other footprint courtyard
    bad = []
    for ref in MOVES:
        f = [g for g in b.GetFootprints() if g.GetReference() == ref][0]
        ca = courtyard(f, b)
        for g in b.GetFootprints():
            if g.GetReference() == ref:
                continue
            cb = courtyard(g, b)
            if not overlaps(ca, cb):
                continue
            if g.GetLayer() != f.GetLayer():
                # opposite faces only conflict through the board, which a
                # courtyard does not describe - ignore unless one has a hole
                if not any(p.GetDrillSizeX() > 0 for p in g.Pads()) and \
                   not any(p.GetDrillSizeX() > 0 for p in f.Pads()):
                    continue
            bad.append((ref, g.GetReference()))
        for z in b.Zones():
            if not z.GetIsRuleArea():
                continue
            zb = z.GetBoundingBox()
            if overlaps(ca, (zb.GetLeft(), zb.GetTop(), zb.GetRight(), zb.GetBottom())):
                bad.append((ref, 'ruleArea:' + (z.GetZoneName() or '?')))
    if bad:
        raise SystemExit('PLACEMENT COLLISION: %s' % bad)

    b.Save(pcb)
    if report:
        out = {}
        for ref in MOVES:
            f = [g for g in b.GetFootprints() if g.GetReference() == ref][0]
            out[ref] = dict(old=old[ref],
                            new=(f.GetPosition().x / 1e6, f.GetPosition().y / 1e6,
                                 f.GetOrientationDegrees(),
                                 b.GetLayerName(f.GetLayer())),
                            pads=[(p.GetNumber(), p.GetNetname(),
                                   round(p.GetPosition().x / 1e6, 3),
                                   round(p.GetPosition().y / 1e6, 3))
                                  for p in f.Pads()])
        print(json.dumps(out, indent=1))
    return old


if __name__ == '__main__':
    apply(sys.argv[1])
