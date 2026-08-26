# -*- coding: utf-8 -*-
"""FBV2-P2-002O sections 3-6 -- the JOINT rigid-cluster + R75 search.

D-260's ruling is a hypothesis about WHY 002N failed, and this script is the
experiment that tests it.

FBV2-P2-002N found a real R75 pose - (4.300, 63.500) rot 180, Kelvin
7.772 / 7.000 mm, mismatch 0.771 mm against a 5.000 mm limit - but it was only
reachable after shifting R80/R81/R82 1.0 mm east to clear the rotation, and that
shift moved BAT_MAIN copper into the LTC4368 control lanes.  Three connections
came back against `BAT_MAIN routed clearance 0.3000 mm` at 0.2750, 0.2778 and
0.2371 mm, and U18 fell from 8 of 8 to 6 of 8.

The column did not become hostile on its own.  It moved RELATIVE TO U18, and it
is that relative geometry - the divider ring sitting where U18's pins expect it -
which every 8-of-8 result since 002M has depended on.  So D-260 moves U18 WITH
the column, as one rigid body, and the offsets R76..R83 hold relative to U18 are
preserved exactly.

AND IT IS ONE SEARCH, NOT TWO.  002N proved R75 independently, proved LTC_OV
independently, and discovered only afterwards that the first destroyed U18.  Here
a candidate is a (cluster translation, R75 pose) PAIR and every filter is applied
to the pair.  A pose that cannot be measured together with the thing it breaks is
not evidence.

Stages, cheapest first:

  A  rigid cluster translations, courtyard/edge legal, U18's eight signal pins
     still banded
  B  R75 at rot 0/180 ONLY - 002N measured rot 90/270 as pinned near the
     shunt's own 5.925 mm mismatch, and spending candidates there again would
     be re-deriving a closed result - on a FINE grid, because BAT_SENSE missed
     its clearance by 0.060 mm and a 0.5 mm grid cannot see that
  C  Kelvin from the MOVED U18 pads, both branches and the mismatch
  D  a real bare-board corridor probe for `Q3.6 -> R75.1` at 1.00 mm with the
     0.300 mm high-current clearance - the exact measurement that failed
  E  rank, cap, and hand the survivors to the real six-layer prefix

No band heuristic is applied to R75: FBV2-P2-002N established that it rejects
R75's own current pose, because it asks an MSOP pin's question of a 5.925 mm
shunt with 1.5 mm pads.
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
CLUSTER = ['U18', 'R76', 'R77', 'R78', 'R79', 'R80', 'R81', 'R82', 'R83']
U18SIG = ['1', '2', '3', '6', '7', '8', '9', '10']
KELVIN_MAX = 10.0
KELVIN_MISMATCH = 5.0
W_SENSE_TRUNK = 1000000          # BAT_SENSE is a BAT_MAIN-class trunk


def d(a, b_):
    return math.hypot(a[0] - b_[0], a[1] - b_[1])


EDGE_CLR = 0.50          # board setup copper-to-edge clearance


def court_ok(M, ref, x, y, rot, fixed_r, extra=()):
    c = M.court(ref, x, y, rot)
    if (c[0] < M.edge[0] or c[1] < M.edge[1]
            or c[2] > M.edge[2] or c[3] > M.edge[3]):
        return None
    # THE PADS MUST CLEAR THE BOARD EDGE, NOT JUST FIT INSIDE THE OUTLINE.
    #
    # The first cut tested the courtyard against the outline and nothing else,
    # so it happily proposed R75 at x = 3.900 rot 180 - a pose whose west pad
    # sits 0.325 mm from the edge against a 0.500 mm board-setup clearance.  The
    # screen rejected EVERY connection from the first one onward and routed
    # nothing at all.  A filter that admits a pose the board rejects outright
    # wastes a whole screen, so the edge rule is applied here, to the pads.
    for (_ref, r) in M.padrects_id(ref, x, y, rot):
        if (r[0] < M.edge[0] + EDGE_CLR or r[1] < M.edge[1] + EDGE_CLR
                or r[2] > M.edge[2] - EDGE_CLR or r[3] > M.edge[3] - EDGE_CLR):
            return None
    if any(PS.ovl(c, fr) for fr in fixed_r):
        return None
    if any(PS.ovl(c, rr) for rr in M.rule):
        return None
    if any(PS.ovl(c, e) for e in extra):
        return None
    return c


def band_ok(M, ref, x, y, rot, pins, FPI, extra_pads=(), depth=1.10):
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
        if any(PS.ovl(band, rr) for rr in extra_pads):
            return False
    return True


def cluster_pose(M, dx, dy):
    return dict((r, (round(M.home[r][0] + dx, 3),
                     round(M.home[r][1] + dy, 3),
                     M.home[r][2])) for r in CLUSTER)


def bare_probe(work, tag, pose, sense_w=W_SENSE_TRUNK):
    """Stage D.  On a BARE six-layer board with this placement applied, can the
    connection that failed actually be routed at its own width and its own
    0.300 mm high-current clearance?

    This is the only filter here that is not arithmetic, and it is the one that
    matters: 002N's failure was 0.060 mm of clearance, which no straight-line
    distance can see.
    """
    pcb = RU.fresh(work, tag)
    SIX.convert(pcb, verbose=False)
    b = pcbnew.LoadBoard(pcb)
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    for ref, (x, y, rot) in pose.items():
        f = fp[ref]
        f.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6))))
        f.SetOrientationDegrees(rot)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(pcb)
    qb = QR.QBoard(pcb)
    qb.wide_nets = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                             'BAT_MID', 'BAT_SENSE',
                                             'BAT_PROTECTED_P'))
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(ref, p)
    a, c = pads.get('Q3.6'), pads.get('R75.1')
    if a is None or c is None:
        return None
    m = qb.mark()
    for w in PL.LAD_BAT:                 # 1.00 / 0.80 / 0.60, never below floor
        r = QR.connect_role(qb, a['net'], a, c, 'B', w, CP, CT_W)
        qb.revert(m)
        if r['ok']:
            return dict(ok=True, w=w / 1e6, mm=round(r['mm'], 3))
    return dict(ok=False, reason=r.get('reason'), why=str(r.get('why'))[:70])


def main():
    work = os.path.join(SP, 'w')
    base = RU.fresh(work, 'O0')
    SIX.convert(base, verbose=False)
    M = PS.Model(base)
    MOVE = CLUSTER + ['R75']
    fixed_r = [c for (_, _, c) in M.fixed_courts(MOVE)]
    FPI = M.fixed_pads(MOVE)
    q3_6 = M.pad('Q3', '6', *M.home['Q3'][:3])
    d9_1 = M.pad('D9', '1', *M.home['D9'][:3])

    # ---- stage A: rigid cluster translations, section 4's box --------------
    clusters = []
    dx = 0.50
    while dx <= 1.7501:
        dy = -0.75
        while dy <= 0.7501:
            pose = cluster_pose(M, dx, dy)
            cs, ok = [], True
            for r, (x, y, rot) in pose.items():
                c = court_ok(M, r, x, y, rot, fixed_r, cs)
                if c is None:
                    ok = False
                    break
                cs.append(c)
            if ok and band_ok(M, 'U18', *pose['U18'], pins=U18SIG, FPI=FPI):
                clusters.append((round(dx, 3), round(dy, 3), pose, cs))
            dy += 0.25
        dx += 0.25
    print('stage A: %d rigid cluster translations legal with all eight U18 '
          'signal pins banded' % len(clusters))

    # ---- stages B/C: R75 rot 0/180 on a FINE grid, per cluster -------------
    pairs = []
    for (dx, dy, pose, cs) in clusters:
        u8 = M.pad('U18', '8', *pose['U18'])
        u9 = M.pad('U18', '9', *pose['U18'])
        for rot in (0.0, 180.0):
            i = -10
            while i <= 10:
                j = -10
                while j <= 10:
                    x = round(4.300 + i * 0.10, 3)
                    y = round(63.500 + j * 0.10, 3)
                    if court_ok(M, 'R75', x, y, rot, fixed_r, cs) is None:
                        j += 1
                        continue
                    p1 = M.pad('R75', '1', x, y, rot)
                    p2 = M.pad('R75', '2', x, y, rot)
                    k1, k2 = d(p1, u9), d(p2, u8)
                    if max(k1, k2) > KELVIN_MAX or abs(k1 - k2) > KELVIN_MISMATCH:
                        j += 1
                        continue
                    pairs.append(dict(
                        dx=dx, dy=dy, r75=(x, y, rot),
                        kelvin=[round(k1, 3), round(k2, 3), round(abs(k1 - k2), 3)],
                        sense_mm=round(d(q3_6, p1), 3),
                        trunk_mm=round(d(p2, d9_1), 3)))
                    j += 1
                i += 1
    print('stage B/C: %d (cluster, R75) pairs inside the Kelvin gates' % len(pairs))
    # Section 7's ranking from 002N, applied to the PAIR.
    pairs.sort(key=lambda c: (c['kelvin'][2], c['sense_mm'] + c['trunk_mm'],
                              c['kelvin'][0] + c['kelvin'][1],
                              abs(c['dx']) + abs(c['dy'])))
    # keep the field diverse: at most three R75 poses per cluster translation
    seen, picked = {}, []
    for c in pairs:
        k = (c['dx'], c['dy'])
        if seen.get(k, 0) >= 3:
            continue
        seen[k] = seen.get(k, 0) + 1
        picked.append(c)
        if len(picked) >= 24:
            break

    # ---- stage D: the real corridor probe ---------------------------------
    print('stage D: bare-board BAT_SENSE corridor probe at 0.300 mm clearance, '
          'on the %d best-ranked' % len(picked))
    keep = []
    for c in picked:
        pose = cluster_pose(M, c['dx'], c['dy'])
        pose['R75'] = c['r75']
        pr = bare_probe(work, 'OPRB', pose)
        c['sense_probe'] = pr
        ok = bool(pr and pr.get('ok'))
        print('   dx%+0.2f dy%+0.2f  R75 (%.2f,%.2f) rot%-4.0f  kelvin %.3f/%.3f'
              ' (%.3f)  Q3.6->R75.1 %s'
              % (c['dx'], c['dy'], c['r75'][0], c['r75'][1], c['r75'][2],
                 c['kelvin'][0], c['kelvin'][1], c['kelvin'][2],
                 ('routes %.3f mm at %.2f' % (pr['mm'], pr['w'])) if ok
                 else ('NO: %s' % (pr or {}).get('reason'))))
        sys.stdout.flush()
        if ok:
            keep.append(c)
            if len(keep) >= 12:
                break
    print('\nSERIOUS COMBINED CANDIDATES: %d' % len(keep))
    out = os.path.join(SP, 'cluster_candidates_002o.json')
    json.dump(keep, open(out, 'w'), indent=1)
    for k, c in enumerate(keep):
        print('  K%02d cluster dx%+0.2f dy%+0.2f  R75 (%.2f, %.2f) rot%.0f  '
              'kelvin %.3f/%.3f (%.3f)  sense %.3f'
              % (k, c['dx'], c['dy'], c['r75'][0], c['r75'][1], c['r75'][2],
                 c['kelvin'][0], c['kelvin'][1], c['kelvin'][2],
                 c['sense_probe']['mm']))
    print('written: %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
