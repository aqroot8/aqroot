# -*- coding: utf-8 -*-
"""FBV2-P2-002Z / D-272 -- candidate_A: THE U18-POSE / TRUNK-LANE VACATE SWEEP.

The divider-spreading family is EXHAUSTED (c3_prefilter_report.json): cardinality
3 has exactly one analytic-meaningful lever (e10n + R79 east) and it widens the
western BPP trunk only from 0.40 to 0.80 mm on B.Cu -- below the 1.20 mm floor --
and the four supervised c3 runs confirm it: c3_e10n_r79 is the first reproducible
U18 8/8 but BAT_PROTECTED_P R75.2->U11.2 (target bit 8) is still FALSE.

The c2 aggregate proved the root cause is NOT a single obstacle: "the western BPP
trunk R75.2->D9.1 routes freely (13.12 mm at 1.50 mm) when NO fanout is laid, but
is dead at every width once the 8-pin U18 fanout is laid ... the binder is the
whole U18 fanout band saturating the board-edge-bounded west margin."  So the last
placement-scope family is NOT more dividers: it is to RELOCATE / REORIENT U18 so
its fanout band VACATES the y~72.8 east-west lane the trunk needs to climb the west
margin and run east to D9.1 (x 11-14).

This file is candidate_A: a fresh, bounded U18-pose x orientation sweep (with R75
held at its proven sense-de-bulge pose, plus a rot cross-check), scored on the
SAME graded trunk_best_w metric place_search_c3 used -- the largest B.Cu inflation
at which R75.2->D9.1 routes WITH the full 8-pin fanout laid.  We keep only fan-8
mech-clean poses and rank by widest trunk.  A minimal support move (R76/R77, the
two parts that frame the trunk's east-lane gap at D9's latitude -- NOT the
trunk-inert R78..R83 divider column) is expanded ONLY on the best fan-8 poses and
ONLY if pure R75+U18 does not already clear 1.20 mm.

Success target: a legal fan-8 pose with trunk_best_w >= 1200000 (1.20 mm),
preferably 1500000 (1.50 mm).  If the bounded exhaustive sweep finds none, placement
is exhausted and the decision escalates to candidate_B (long B.Cu / F.Cu via bridge).

    python3 place_search_c4_002z.py          # score, write c4_*.json + report
"""
import os, sys, json, math, time
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import place_search_002z as Z
import place_search_c3_002z as C3
import place_search_002f as PS
import path_role_util as RU

WORK = os.path.join(SP, 'w')
OUT = os.path.join(SP, 'place_002z')

FLOOR = 1200000       # 1.20 mm analytic trunk floor (success)
TARGET = 1500000      # 1.50 mm preferred

# R75: proven sense-de-bulge pose is (2.8, 65, 270).  We hold it there (primary)
# and cross-check the home rotation to confirm rotation is a sense lever, not a
# trunk lever.  R75 x/y are NOT swept -- 2.8 is hard against the west edge and the
# E2r east variant already proved a worse (16.9 mm) sense path.
R75_POSES = {
    'r270': (2.8, 65.0, 270),     # primary: de-bulged sense (maxx 3.25)
    'r090': (2.8, 65.0, 90),      # cross-check: home rotation
}

# U18 pose box.  Broader than family_a: we push SOUTH (vacate the lane below the
# fanout) and NORTH (vacate it above), and EAST (pull the fanout band off the west
# margin so the trunk can climb x~2.8 uncontested), on a 0.5 mm grid, all four
# orthogonal rotations.  West is the board edge, so no west translation.
U18_HOME = (3.0, 72.4, 90.0)
U18_ROTS = (0, 90, 180, 270)
U18_DX = (-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5)          # x 2.5 .. 5.5
U18_DY = (-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0)  # y 69.4..74.4

# Minimal support parts (card 3), expanded ONLY on the best fan-8 card-2 poses and
# ONLY if card-2 misses 1.20 mm.  R76 (north of the lane) and R77 (in the lane at
# y 71.5) frame the trunk's east-lane gap near D9; they are U18 fanout targets
# (pin10 / pins1,3) so moving them shifts the fanout too -- distinct from the
# proven trunk-inert R78..R83 divider spread, which is NOT re-enumerated here.
SUPPORT = ('R77', 'R76')
SUP_DX = (-0.5, 0.0, 0.5, 1.0)
SUP_DY = (-0.5, 0.0, 0.5)
TOPK_FOR_SUPPORT = 8


def disp_of(M, place):
    d = 0.0
    for ref, v in place.items():
        h = M.home[ref]
        d += math.hypot(v[0] - h[0], v[1] - h[1])
        d += 0.5 * (abs((v[2] - h[2]) % 360.0) > 0.05)
    return d


def eval_pose(M, place):
    """Full metric for one placement: mech-clean, fan-8 graded trunk width, and
    kelvin/sense from Z.evaluate.  Returns None if mech-rejected or fan<8."""
    if any(r in Z.FROZEN for r in place):
        return None
    if Z.mechanical_ok(M, place):
        return None
    fan, bw, maxx = C3.trunk_best_w(M, place)
    if fan != 8:
        return None
    ev = Z.evaluate(M, place)
    if ev.get('fanout') != 8:
        return None
    return dict(place={k: list(v) for k, v in place.items()},
                fanout=fan, trunk_best_w=bw, sense_maxx=maxx,
                sense_mm=ev.get('sense_mm'), k8=ev.get('k8'), k9=ev.get('k9'),
                kmis=ev.get('kmis'), trunk_150=ev.get('trunk_150'),
                trunk_120=ev.get('trunk_120'), disp=round(disp_of(M, place), 3))


def sweep_card2(M):
    rows, t0 = [], time.time()
    n = 0
    for rk, r75 in R75_POSES.items():
        for rot in U18_ROTS:
            for dx in U18_DX:
                for dy in U18_DY:
                    n += 1
                    u = (round(U18_HOME[0] + dx, 3),
                         round(U18_HOME[1] + dy, 3), rot)
                    place = {'R75': r75, 'U18': u}
                    r = eval_pose(M, place)
                    if r is None:
                        continue
                    r.update(card=2, r75=rk, u18_rot=rot, support=None)
                    rows.append(r)
        print('  R75 %s: %d fan-8 so far (%d poses tried, %.1fs)'
              % (rk, len(rows), n, time.time() - t0))
        sys.stdout.flush()
    return rows


def sweep_card3(M, seed_rows):
    """Expand the minimal support move on the best card-2 fan-8 poses."""
    rows, t0 = [], time.time()
    seeds = seed_rows[:TOPK_FOR_SUPPORT]
    for s in seeds:
        base = {k: tuple(v) for k, v in s['place'].items()}
        for part in SUPPORT:
            h = M.home[part]
            for dx in SUP_DX:
                for dy in SUP_DY:
                    if dx == 0.0 and dy == 0.0:
                        continue
                    place = dict(base)
                    place[part] = (round(h[0] + dx, 3), round(h[1] + dy, 3),
                                   h[2])
                    r = eval_pose(M, place)
                    if r is None:
                        continue
                    r.update(card=3, r75=s['r75'], u18_rot=s['u18_rot'],
                             support='%s(%+.1f,%+.1f)' % (part, dx, dy))
                    rows.append(r)
    print('  card-3 support expansion: %d fan-8 (%.1fs)'
          % (len(rows), time.time() - t0))
    return rows


def rank(rows):
    rows.sort(key=lambda r: (-(r['trunk_best_w'] or 0),
                             r['sense_maxx'] or 99,
                             r['card'], r['disp']))
    return rows


def main():
    M = PS.Model(RU.fresh(WORK, 'C4a'))
    print('U18-pose / trunk-lane vacate sweep (candidate_A)')
    t0 = time.time()
    c2 = rank(sweep_card2(M))
    best_c2 = c2[0]['trunk_best_w'] if c2 else None
    print('\ncard-2 fan-8: %d, best trunk_best_w=%s' % (len(c2), best_c2))

    c3 = []
    if not c2 or (best_c2 or 0) < FLOOR:
        print('card-2 below 1.20 mm floor -> minimal support expansion')
        c3 = sweep_card3(M, c2)

    allrows = rank(c2 + c3)
    winners = [r for r in allrows if (r['trunk_best_w'] or 0) >= FLOOR]

    print('\n=== TOP 15 (all cardinalities) ===')
    for r in allrows[:15]:
        print('  %s R75=%s U18rot=%d %s  fan=%d trunk_best_w=%s tr150=%s '
              'tr120=%s sense=%s maxx=%s k8=%s k9=%s disp=%.2f sup=%s'
              % ('C%d' % r['card'], r['r75'], r['u18_rot'],
                 json.dumps(r['place']), r['fanout'], r['trunk_best_w'],
                 r['trunk_150'], r['trunk_120'], r['sense_mm'],
                 r['sense_maxx'], r['k8'], r['k9'], r['disp'], r['support']))

    json.dump({'task': 'FBV2-P2-002Z / D-272 candidate_A U18-pose sweep',
               'floor_nm': FLOOR, 'target_nm': TARGET,
               'n_card2_fan8': len(c2), 'n_card3_fan8': len(c3),
               'best_card2_trunk_w': best_c2,
               'best_overall_trunk_w': allrows[0]['trunk_best_w'] if allrows else None,
               'n_winners_ge_floor': len(winners),
               'elapsed_s': round(time.time() - t0, 1),
               'rows': allrows},
              open(os.path.join(OUT, 'c4_prefilter.json'), 'w'), indent=1)

    # emit ranked candidate JSONs only for legal >= floor winners (dedup on pose)
    M2 = PS.Model(RU.fresh(WORK, 'C4b'))
    seen, idx = set(), []
    for r in winners:
        key = tuple(sorted((k, round(v[0], 1), round(v[1], 1), round(v[2]))
                           for k, v in r['place'].items()))
        if key in seen:
            continue
        seen.add(key)
        moves = {}
        for ref, v in r['place'].items():
            lay = M2.b.GetLayerName(M2.fp[ref].GetLayer())
            moves[ref] = [round(v[0], 3), round(v[1], 3), round(v[2], 1), lay]
        spec = dict(name='002Z-c4-%02d' % len(idx), base='AUTHORITATIVE',
                    moves=moves,
                    analytic=dict(fanout=r['fanout'],
                                  trunk_best_w=r['trunk_best_w'],
                                  trunk_150=r['trunk_150'],
                                  trunk_120=r['trunk_120'],
                                  sense_mm=r['sense_mm'],
                                  sense_maxx=r['sense_maxx'],
                                  k8=r['k8'], k9=r['k9'], kmis=r['kmis'],
                                  card=r['card'], support=r['support'],
                                  disp=r['disp'],
                                  expected_casualty='closes BAT_PROTECTED_P '
                                  'R75.2->U11.2 (analytic trunk >= 1.20 mm)'))
        p = os.path.join(OUT, 'c4_%02d.json' % len(idx))
        json.dump(spec, open(p, 'w'), indent=1)
        idx.append(dict(file='c4_%02d.json' % len(idx), **spec['analytic'],
                        place=r['place']))
        if len(idx) >= 8:
            break
    json.dump(idx, open(os.path.join(OUT, 'c4_index.json'), 'w'), indent=1)
    print('\nwrote %d >=1.20mm candidate JSONs (of %d winners)'
          % (len(idx), len(winners)))
    if not winners:
        print('NO fan-8 pose reaches the 1.20 mm floor -> placement EXHAUSTED; '
              'escalate to candidate_B (long B.Cu / F.Cu via bridge).')


if __name__ == '__main__':
    main()
