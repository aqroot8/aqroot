# -*- coding: utf-8 -*-
"""FBV2-P2-002P sections 3-7 -- the D-261 chain: D9, then the cluster, then R75.

D-261 authorises ONE new lever and it is a bounded physical relocation of D9.
Nothing electrical changes: same part, same footprint, same net, same polarity,
same topology.  The lever exists because FBV2-P2-002O closed the geometry:

    R75 at rot 0/180 needs        7.75 mm of corridor
    available at cluster +0.50    6.80 mm
    window opens at cluster +0.75 ~0.10 mm wide
    and at +0.75, D9 overlaps R77 by 0.170 mm

So the chain is strictly ordered and each link is measured before the next is
attempted: move D9 the least that makes cluster +0.75 legal; move the rigid
cluster; find R75 inside the corridor that opens; then route.

THE LIMITS ARE DERIVED FROM COPPER, NOT TYPED IN.  Section 7 gives the expected
window as roughly 4.075 < R75.x < 4.175 and then says to derive it from real
geometry rather than treat those numbers as truth - so the search computes the
courtyard and pad extents itself and reports what it finds.  If the real window
disagrees with the estimate, the real window wins and the disagreement is the
finding.
"""
import json
import math
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import place_search_002f as PS
import place_cluster_002o as CL
import path_role_util as RU
import qrouter as QR
import battery_route_plan as PL
import sixlayer as SIX
import pcbnew

N = PL.N
CP, CT_W, CT_S = 200000, 300000, 200000
CLUSTER = CL.CLUSTER
MOVE = CLUSTER + ['R75', 'D9']
EDGE_CLR = CL.EDGE_CLR
KELVIN_MAX = 10.0
KELVIN_MISMATCH = 5.0

# THE CORRIDOR HAS TO FIT THE TRUNK, NOT JUST THE PAD.
#
# The first D-261 chain found a legal R75 window at x 4.075..4.150 with D9 moved
# only 0.200 mm, and the screen then rejected `BAT_PROTECTED_P R75.2 -> D9.1`
# with `copper_edge_clearance 0.5000 mm; actual 0.4125 mm`.  The pad cleared the
# edge; the 1.50 mm TRUNK that has to leave that pad did not.  A 1.50 mm track
# centred on R75.2 needs 0.500 + 0.750 = 1.250 mm of room, so R75.2's CENTRE
# must sit at least 1.250 mm from the edge - 0.063 mm more than the +0.75 mm
# window can give.  Cluster +1.00 opens it, D9 has to move further to free that,
# and that extra displacement is exactly what it buys.
W_TRUNK_BPP = PL.W_TRUNK_BPP / 1e6
TRUNK_EDGE = EDGE_CLR + W_TRUNK_BPP / 2.0
WANT_CDX = 1.00


def d(a, b_):
    return math.hypot(a[0] - b_[0], a[1] - b_[1])


def legal(M, ref, x, y, rot, fixed_r, extra=()):
    return CL.court_ok(M, ref, x, y, rot, fixed_r, extra)


def main():
    work = os.path.join(SP, 'w')
    base = RU.fresh(work, 'P0')
    SIX.convert(base, verbose=False)
    M = PS.Model(base)
    fixed_r = [c for (_, _, c) in M.fixed_courts(MOVE)]
    FPI = M.fixed_pads(MOVE)
    q3_6 = M.pad('Q3', '6', *M.home['Q3'][:3])
    u11_2 = M.pad('U11', '2', *M.home['U11'][:3])
    d9_home = M.home['D9'][:3]
    d9_1_home = M.pad('D9', '1', *d9_home)
    r75_home = M.home['R75'][:3]
    print('D9 home %s   D9.1 %s' % (d9_home, tuple(round(v, 3) for v in d9_1_home)))
    print('baseline high-current: R75.2->D9.1 %.3f mm   D9.1->U11.2 %.3f mm'
          % (d(M.pad('R75', '2', *r75_home), d9_1_home), d(d9_1_home, u11_2)))

    # ---- stage A: the smallest D9 move, east first --------------------------
    d9c = []
    ix = 4
    while ix <= 15:                       # +0.20 .. +0.75 in 0.05 mm steps
        for iy in (0, -1, 1, -2, 2, -4, 4, -6, 6, -8, 8):
            dx, dy = round(ix * 0.05, 3), round(iy * 0.05, 3)
            if abs(dy) > 0.4001:
                continue
            x, y = round(d9_home[0] + dx, 3), round(d9_home[1] + dy, 3)
            if legal(M, 'D9', x, y, d9_home[2], fixed_r) is None:
                continue
            d9c.append(dict(dx=dx, dy=dy, x=x, y=y, rot=d9_home[2],
                            move=round(math.hypot(dx, dy), 3)))
        ix += 1
    d9c.sort(key=lambda c: (c['move'], abs(c['dy'])))
    print('stage A: %d legal D9 poses in the bounded box' % len(d9c))

    # ---- stage B: which D9 pose frees cluster +0.75 / +1.00 -----------------
    combos = []
    for c9 in d9c:
        d9court = M.court('D9', c9['x'], c9['y'], c9['rot'])
        for cdx in (0.75, 1.00, 1.25):
            for cdy in (0.0, -0.25, 0.25):
                pose = CL.cluster_pose(M, cdx, cdy)
                cs, ok = [d9court], True
                for r, (x, y, rot) in pose.items():
                    cc = legal(M, r, x, y, rot, fixed_r, cs)
                    if cc is None:
                        ok = False
                        break
                    cs.append(cc)
                if not ok:
                    continue
                if not CL.band_ok(M, 'U18', *pose['U18'],
                                  pins=CL.U18SIG, FPI=FPI):
                    continue
                combos.append(dict(d9=c9, cdx=cdx, cdy=cdy, pose=pose, cs=cs))
        if any(c['cdx'] >= WANT_CDX for c in combos):
            break      # smallest D9 move that frees the shift actually needed
    if not combos:
        print('stage B: NO D9 pose in the bounded box frees cluster +0.75/+1.00')
        json.dump([], open(os.path.join(SP, 'd9_candidates_002p.json'), 'w'))
        return 1
    best9 = combos[0]['d9']
    print('stage B: D9 (%+.2f, %+.2f) -> (%.3f, %.3f) frees %d cluster option(s); '
          'displacement %.3f mm'
          % (best9['dx'], best9['dy'], best9['x'], best9['y'],
             len(combos), best9['move']))
    d9_1_new = M.pad('D9', '1', best9['x'], best9['y'], best9['rot'])

    # ---- stage C/D: R75 rot 0/180 in the corridor that just opened ----------
    out = []
    for cb in combos:
        u8 = M.pad('U18', '8', *cb['pose']['U18'])
        u9 = M.pad('U18', '9', *cb['pose']['U18'])
        lo, hi = None, None
        for rot in (0.0, 180.0):
            xi = 0
            while xi <= 400:               # 0.000 .. 10.000 at 0.025 mm
                x = round(xi * 0.025, 3)
                yj = -40
                while yj <= 40:            # +/-1.0 mm at 0.025 mm
                    y = round(r75_home[1] + yj * 0.025, 3)
                    if legal(M, 'R75', x, y, rot, fixed_r, cb['cs']) is None:
                        yj += 1
                        continue
                    lo = x if lo is None else min(lo, x)
                    hi = x if hi is None else max(hi, x)
                    p1 = M.pad('R75', '1', x, y, rot)
                    p2 = M.pad('R75', '2', x, y, rot)
                    # both shunt pads must admit their own trunk at the edge
                    if (min(p1[0], p2[0]) < M.edge[0] + TRUNK_EDGE
                            or max(p1[0], p2[0]) > M.edge[2] - TRUNK_EDGE
                            or min(p1[1], p2[1]) < M.edge[1] + TRUNK_EDGE
                            or max(p1[1], p2[1]) > M.edge[3] - TRUNK_EDGE):
                        yj += 1
                        continue
                    k1, k2 = d(p1, u9), d(p2, u8)
                    if max(k1, k2) > KELVIN_MAX or abs(k1 - k2) > KELVIN_MISMATCH:
                        yj += 1
                        continue
                    out.append(dict(
                        d9=best9, cdx=cb['cdx'], cdy=cb['cdy'],
                        r75=(x, y, rot),
                        kelvin=[round(k1, 3), round(k2, 3), round(abs(k1 - k2), 3)],
                        sense_mm=round(d(q3_6, p1), 3),
                        trunk_mm=round(d(p2, d9_1_new), 3)))
                    yj += 1
                xi += 1
        print('   cluster +%.2f/%+.2f: R75 rot0/180 legal x range %s'
              % (cb['cdx'], cb['cdy'],
                 ('%.3f .. %.3f' % (lo, hi)) if lo is not None else 'NONE'))
    print('stage C/D: %d (D9, cluster, R75) triples inside the Kelvin gates'
          % len(out))
    out.sort(key=lambda c: (c['kelvin'][2], c['sense_mm'] + c['trunk_mm'],
                            c['kelvin'][0] + c['kelvin'][1]))

    # ---- stage E: the real corridor probe for the connection that failed ----
    keep, seen = [], {}
    for c in out:
        k = (c['cdx'], c['cdy'], c['r75'][2])
        if seen.get(k, 0) >= 3:
            continue
        seen[k] = seen.get(k, 0) + 1
        pose = CL.cluster_pose(M, c['cdx'], c['cdy'])
        pose['R75'] = c['r75']
        pose['D9'] = (best9['x'], best9['y'], best9['rot'])
        pr = CL.bare_probe(work, 'PPRB', pose)
        c['sense_probe'] = pr
        ok = bool(pr and pr.get('ok'))
        print('   cl+%.2f/%+.2f R75 (%.3f,%.3f) rot%-4.0f kelvin %.3f/%.3f (%.3f)'
              '  Q3.6->R75.1 %s'
              % (c['cdx'], c['cdy'], c['r75'][0], c['r75'][1], c['r75'][2],
                 c['kelvin'][0], c['kelvin'][1], c['kelvin'][2],
                 ('routes %.3f mm at %.2f' % (pr['mm'], pr['w'])) if ok
                 else ('NO: %s' % (pr or {}).get('reason'))))
        sys.stdout.flush()
        if ok:
            keep.append(c)
            if len(keep) >= 8:
                break
    print('\nSERIOUS COMBINED CANDIDATES: %d' % len(keep))
    json.dump(dict(d9=best9,
                   d9_old_trunk=round(d(M.pad('R75', '2', *r75_home), d9_1_home), 3),
                   d9_old_u11=round(d(d9_1_home, u11_2), 3),
                   d9_new_u11=round(d(d9_1_new, u11_2), 3),
                   cands=keep),
              open(os.path.join(SP, 'd9_candidates_002p.json'), 'w'), indent=1)
    for k, c in enumerate(keep):
        print('  P%02d D9 (%.3f,%.3f)  cluster +%.2f/%+.2f  R75 (%.3f, %.3f) rot%.0f'
              '  kelvin %.3f/%.3f (%.3f)  sense %.3f  trunk %.3f'
              % (k, best9['x'], best9['y'], c['cdx'], c['cdy'],
                 c['r75'][0], c['r75'][1], c['r75'][2],
                 c['kelvin'][0], c['kelvin'][1], c['kelvin'][2],
                 c['sense_probe']['mm'], c['trunk_mm']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
