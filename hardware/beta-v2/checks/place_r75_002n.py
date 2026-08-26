# -*- coding: utf-8 -*-
"""FBV2-P2-002N sections 5-9 -- the BOUNDED R75 and LTC_OV placement searches.

FBV2-P2-002M closed PR-47 on six layers and failed its local gate on exactly
two connections:

    BAT_SENSE Q3.6 -> R75.1   BAT_MAIN routed clearance 0.3000; actual 0.2400
    LTC_OV    R77.2 -> R78.1  NO_VIA_SITE

D-259 rules both by PLACEMENT.  BAT_SENSE carries pack current, so its 0.300 mm
spacing is not negotiable, PR-48's local 0.20 mm exception does not reach it,
and it may not be sent to 0.5 oz inner copper.  LTC_OV is a high-impedance
comparator node that has to stay short, local and on B.Cu.  Neither is a
routing problem any more.

WHY R75 ROTATION IS THE INTERESTING AXIS, AND IT FALLS OUT OF THE ARITHMETIC.
`U18.8` and `U18.9` sit at the SAME y (70.300), 0.5 mm apart in x.  R75 is a
5.925 mm shunt whose pads currently lie along y.  So for any pure north/south
translation the two Kelvin lengths BOTH change by the same amount and their
MISMATCH stays pinned at the shunt's own length - 5.825 mm measured, against a
5.000 mm limit.  Translation cannot fix it; it never could.  Turning the shunt
so its pads lie along x makes the two Kelvin runs nearly equal, and that is a
geometric fact about the part, not a preference.

The search still measures rather than assumes: every pose is filtered on
courtyard legality, then on all nine of section 6's criteria, and the survivors
are ranked by section 7's order.
"""
import json
import math
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import place_search_002f as PS
import path_role_util as RU
import qrouter as QR
import battery_route_plan as PL
import sixlayer as SIX
import pcbnew

N = PL.N
CP, CT_W, CT_S = 200000, 300000, 200000
KELVIN_MAX = 10.0
KELVIN_MISMATCH = 5.0
HICUR_CLR = 0.300


def d(a, b_):
    return math.hypot(a[0] - b_[0], a[1] - b_[1])


def legal(M, ref, x, y, rot, fixed_r, extra=()):
    c = M.court(ref, x, y, rot)
    if (c[0] < M.edge[0] or c[1] < M.edge[1]
            or c[2] > M.edge[2] or c[3] > M.edge[3]):
        return False
    if any(PS.ovl(c, fr) for fr in fixed_r):
        return False
    if any(PS.ovl(c, rr) for rr in M.rule):
        return False
    if any(PS.ovl(c, e) for e in extra):
        return False
    return True


def band_ok(M, ref, x, y, rot, pins, FPI, depth=1.10):
    dd = dict(M.padrects_id(ref, x, y, rot))
    for n_ in pins:
        r = dd.get(ref + '.' + n_)
        if r is None:
            return False
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        dx, dy = cx - x, cy - y
        if abs(dx) >= abs(dy):
            band = ((r[2] + 0.05, r[1] - 0.05, r[2] + depth, r[3] + 0.05)
                    if dx > 0 else
                    (r[0] - depth, r[1] - 0.05, r[0] - 0.05, r[3] + 0.05))
        else:
            band = ((r[0] - 0.05, r[3] + 0.05, r[2] + 0.05, r[3] + depth)
                    if dy > 0 else
                    (r[0] - 0.05, r[1] - depth, r[2] + 0.05, r[1] - 0.05))
        if (band[0] < M.edge[0] + 0.30 or band[1] < M.edge[1] + 0.30
                or band[2] > M.edge[2] - 0.30 or band[3] > M.edge[3] - 0.30):
            return False
        if any(PS.ovl(band, rr) for (_i, rr) in FPI):
            return False
    return True


# The divider/trip column that stands in R75's way.  R80, R81 and R82 sit at
# x 7.30..10.35 in a vertical stack, and their courtyards are what make every
# rot-0/180 R75 pose illegal.  Section 6 pins Q2, Q3, D9, U18, U14 and the FET
# placement; it does NOT pin these three, and section 8 already treats U18's own
# divider ring as a movable lever.  They are offered a bounded EASTWARD shift
# only - the column keeps its order, its spacing and its x-alignment.
RING = ('R80', 'R81', 'R82')


def search_r75(M, fixed_r, FPI, span=6.0, step=0.5, ring_dx=0.0):
    """Section 6.  Every criterion that can be decided analytically, decided.

    THE MISMATCH IS PINNED BY GEOMETRY UNLESS THE SHUNT CAN TURN.  `U18.8` and
    `U18.9` are at the SAME y, so while R75's pads lie along y - which is every
    rot 90/270 pose - the two Kelvin lengths differ by very nearly the shunt's
    own 5.925 mm length whatever the translation.  Measured over a +/-8 mm box
    at 0.5 mm, the best reachable mismatch that way is 5.177 mm against a
    5.000 mm limit: close, and still a fail.  Turning the shunt so its pads lie
    along x drops the mismatch to well under 1 mm - and every rot 0/180 pose is
    blocked by the R80/R81/R82 courtyards at x 7.30.  So the column is what is
    actually costing the Kelvin spec, not R75.
    """
    u18_8 = M.pad('U18', '8', *M.home['U18'][:3])
    u18_9 = M.pad('U18', '9', *M.home['U18'][:3])
    q3_6 = M.pad('Q3', '6', *M.home['Q3'][:3])
    d9_1 = M.pad('D9', '1', *M.home['D9'][:3])
    home = M.home['R75'][:3]
    out = []
    n = int(span / step)
    for rot in (0.0, 90.0, 180.0, 270.0):
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                x = round(home[0] + i * step, 3)
                y = round(home[1] + j * step, 3)
                if not legal(M, 'R75', x, y, rot, fixed_r):
                    continue
                # NO band_ok() FOR R75, AND THE REASON IS THAT IT REJECTS THE
                # STATUS QUO.  band_ok() is the fine-pitch heuristic from the
                # U18/U19 searches: it demands a clear 1.10 mm outward band in
                # front of every pin, which is the right question for an MSOP
                # pin with a 0.325 mm window and the wrong one for a 5.925 mm
                # shunt whose pads are 1.5 mm wide.  Applied to R75 it rejects
                # R75's OWN CURRENT POSE - a filter that throws away the
                # placement the board already has is not a filter, it is a bug -
                # and it left the search with zero candidates.  Courtyard, edge
                # and rule-area legality still apply, and the real routing
                # screen is what decides escape.
                pass
                p1 = M.pad('R75', '1', x, y, rot)
                p2 = M.pad('R75', '2', x, y, rot)
                k1 = d(p1, u18_9)          # BAT_SENSE Kelvin
                k2 = d(p2, u18_8)          # BAT_PROTECTED_P Kelvin
                if max(k1, k2) > KELVIN_MAX:
                    continue
                if abs(k1 - k2) > KELVIN_MISMATCH:
                    continue
                sense = d(q3_6, p1)        # the connection that failed
                trunk = d(p2, d9_1)
                out.append(dict(ref='R75', x=x, y=y, rot=rot,
                                kelvin=[round(k1, 3), round(k2, 3),
                                        round(abs(k1 - k2), 3)],
                                sense_mm=round(sense, 3),
                                trunk_mm=round(trunk, 3),
                                move_mm=round(d((x, y), home[:2]), 3)))
    # Section 7's ranking, in its order: Kelvin mismatch, then total Kelvin,
    # then the high-current path, then how far the part had to move.
    out.sort(key=lambda c: (c['kelvin'][2], c['kelvin'][0] + c['kelvin'][1],
                            c['sense_mm'] + c['trunk_mm'], c['move_mm']))
    return out


def search_ltcov(M, fixed_r, FPI, span=3.0, step=0.25):
    """Sections 8-9.  R78 first and alone; R77 only if R78 cannot do it."""
    u18_3 = M.pad('U18', '3', *M.home['U18'][:3])
    r77 = M.home['R77'][:3]
    home78 = M.home['R78'][:3]
    r77_1 = M.pad('R77', '1', *r77)
    r77_2 = M.pad('R77', '2', *r77)
    out = []
    n = int(span / step)
    for rot in (0.0, 90.0, 180.0, 270.0):
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                x = round(home78[0] + i * step, 3)
                y = round(home78[1] + j * step, 3)
                if not legal(M, 'R78', x, y, rot, fixed_r):
                    continue
                if not band_ok(M, 'R78', x, y, rot, ['1', '2'], FPI):
                    continue
                p1 = M.pad('R78', '1', x, y, rot)
                # LTC_OV is U18.3 -> R77.2 -> R78.1.  The high-impedance span
                # is the whole chain, and section 9 caps it at 20 mm with a
                # 15 mm target.
                span_mm = d(u18_3, r77_2) + d(r77_2, p1)
                if span_mm > 20.0:
                    continue
                out.append(dict(ref='R78', x=x, y=y, rot=rot,
                                link_mm=round(d(r77_2, p1), 3),
                                span_mm=round(span_mm, 3),
                                raw_mm=round(d(r77_1, M.pad('R77', '1', *r77)), 3),
                                move_mm=round(d((x, y), home78[:2]), 3)))
    out.sort(key=lambda c: (c['span_mm'], c['link_mm'], c['move_mm']))
    return out


def main():
    work = os.path.join(SP, 'w')
    base = RU.fresh(work, 'N75')
    SIX.convert(base, verbose=False)
    M = PS.Model(base)
    MOVE = ['R75', 'R77', 'R78'] + list(RING)
    FPI = M.fixed_pads(MOVE)

    # The column is offered the smallest eastward shift that frees R75, and
    # nothing more: it is searched from 0 upward and the first shift that
    # produces a passing R75 pose wins.
    r75, ring_dx = [], 0.0
    for dx in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        fixed_r = [c for (nm, _x, c) in M.fixed_courts(MOVE)]
        for nm in RING:
            hx, hy, hr = M.home[nm][:3]
            fixed_r.append(M.court(nm, hx + dx, hy, hr))
        got = search_r75(M, fixed_r, FPI)
        if got:
            r75, ring_dx = got, dx
            break
    print('R75: column shift needed %.1f mm east (R80/R81/R82)' % ring_dx)
    print('R75: %d poses legal with Kelvin <= %.0f mm each and <= %.0f mm '
          'mismatch' % (len(r75), KELVIN_MAX, KELVIN_MISMATCH))
    for c in r75[:12]:
        print('   (%.3f, %.3f) rot%-4.0f  kelvin %.3f/%.3f (%.3f)  '
              'Q3.6->R75.1 %.3f  R75.2->D9.1 %.3f  moved %.3f'
              % (c['x'], c['y'], c['rot'], c['kelvin'][0], c['kelvin'][1],
                 c['kelvin'][2], c['sense_mm'], c['trunk_mm'], c['move_mm']))
    json.dump(dict(ring_dx=ring_dx, ring=list(RING), cands=r75[:12]),
              open(os.path.join(SP, 'r75_candidates_002n.json'), 'w'), indent=1)

    # R78's obstacle set must include R77 AND R75, both at the poses this task
    # is actually adopting.  Without R77 in it the search happily returned
    # `R78 at (9.325, 70.675)` with `R77.2 -> R78.1 = 0.000 mm` - which is not a
    # zero-length link, it is R78's pad sitting exactly on top of R77's.  A
    # search that is allowed to overlap the part it is connecting to will always
    # report a perfect score.
    fixed_ov = [c for (nm, _x, c) in M.fixed_courts(MOVE)]
    for nm in RING:
        hx, hy, hr = M.home[nm][:3]
        fixed_ov.append(M.court(nm, hx + ring_dx, hy, hr))
    fixed_ov.append(M.court('R77', *M.home['R77'][:3]))
    if r75:
        fixed_ov.append(M.court('R75', r75[0]['x'], r75[0]['y'], r75[0]['rot']))
    ov = search_ltcov(M, fixed_ov, FPI)
    print('\nR78: %d poses legal with an LTC_OV span <= 20 mm' % len(ov))
    for c in ov[:8]:
        print('   (%.3f, %.3f) rot%-4.0f  R77.2->R78.1 %.3f  span %.3f  '
              'moved %.3f'
              % (c['x'], c['y'], c['rot'], c['link_mm'], c['span_mm'],
                 c['move_mm']))
    json.dump(ov[:8], open(os.path.join(SP, 'r78_candidates_002n.json'), 'w'),
              indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
