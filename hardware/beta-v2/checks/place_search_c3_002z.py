# -*- coding: utf-8 -*-
"""FBV2-P2-002Z / D-272 -- CARDINALITY-3 ANALYTIC PREFILTER.

Cardinality 2 is DISPROVED (place_002z/cardinality2_aggregate.json): five
supervised R75+U18 runs all cap U18 at 7/8 AND all leave the SAME casualty open,
BAT_PROTECTED_P R75.2->U11.2 -- the western BPP trunk.  This file designs the
smallest justified cardinality-3 moves: R75 (sense de-bulge) + U18 (fanout) + ONE
support/divider part, targeting that one remaining casualty.

WHY A GRADED TRUNK METRIC.  place_search_002z.evaluate() reproduces the real
trunk failure exactly (trunk_120=None on all five c2 poses, matching the real
router's NO_LEGAL_ESCAPE at D9.1).  But its viability gate is BINARY at 1.20 mm on
B.Cu only, while the real arbiter can STAGE the trunk on F.Cu with vias
(route_battery_block CURRENT_ESCAPE_RESERVATION).  So a candidate whose B.Cu trunk
is infeasible at 1.20 mm but feasible at, say, 0.80 mm has meaningfully widened the
corridor and is worth a real run; one stuck below the c2 base is not.  We therefore
rank by trunk_best_w: the largest inflation at which the trunk routes WITH the full
fanout laid.  base (c2) trunk_best_w is < 0.40 (dead).

    python place_search_c3_002z.py            # score, write c3_*.json + index
"""
import os, sys, json, math, time
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import place_search_002z as Z
import place_search_002f as PS
import path_role_util as RU

WORK = os.path.join(SP, 'w')
OUT = os.path.join(SP, 'place_002z')

# the five supervised, proven cardinality-2 bases (R75+U18), spanning both U18
# casualty families (7-open west, 8-open east).  Poses are the applied/asserted
# poses from the returncode-0 runs.
C2_BASES = {
    'e10':  {'R75': (2.8, 65.0, 270), 'U18': (4.0, 72.4, 90)},   # 7/8 U18.7 open
    'e10n': {'R75': (2.8, 65.0, 270), 'U18': (4.0, 72.9, 90)},   # 7/8 U18.2 open
    'w05':  {'R75': (2.8, 65.0, 270), 'U18': (2.5, 72.4, 90)},   # 7/8 U18.8 open
    'E2r':  {'R75': (4.8, 65.0, 270), 'U18': (4.5, 72.4, 90)},   # 7/8 U18.8, sense east
}

# widths (nm) probed for the graded trunk metric, high -> low
TRUNK_WIDTHS = [1500000, 1200000, 1000000, 800000, 600000, 400000]

# candidate third parts: the support/divider resistors bounding the western
# BPP-trunk corridor.  R82/R83 are NOT U18 fanout targets (pure obstacles at
# R75.2's latitude); R80/R81 ARE targets (U18.6/U18.7) so moving them also shifts
# the fanout -- tried but flagged.  D9,Q2,F1,J4,TP17,C58 are FROZEN.
THIRD_PARTS = ['R83', 'R82', 'R81', 'R80', 'R79', 'R78']


def trunk_best_w(M, place):
    """Largest trunk inflation (nm) that routes R75.2->D9.1 with the full U18
    fanout laid on top of the BAT_SENSE current path.  None if dead even at the
    smallest probed width.  Mirrors Z.evaluate's lay order exactly."""
    PG = PS.PathGrid(0.0, 44.0, 26.0, 86.0, 0.25)
    moved = set(place)
    FP = M.fixed_pads(moved)
    mp = []
    for ref in place:
        mp += M.padrects_id(ref, *place[ref])
    ALL = FP + mp
    q36 = Z.padpos(M, 'Q3', '6', place)
    r75_1 = Z.padpos(M, 'R75', '1', place)
    r75_2 = Z.padpos(M, 'R75', '2', place)
    d9_1 = Z.padpos(M, 'D9', '1', place)
    b = PG.build(PG.drop(ALL, {'Q3.6', 'R75.1'}), Z.infl(Z.W_SENSE_CUR))
    got = PG.path(b, q36, r75_1, want_pts=True)
    if got is None:
        return None, None, None
    sense_mm, sp = got
    sense_maxx = max(p[0] for p in sp)
    sc = [(x - 0.15, y - 0.15, x + 0.15, y + 0.15) for (x, y) in sp[::2]]
    laid = []
    fan = 0
    for pin in Z.FAN_ORDER:
        tgt = Z.U18TARGET[pin]
        tref, tnum = tgt.split('.')
        ii = Z.infl(Z.U18MIN[pin])
        a = Z.padpos(M, 'U18', pin, place)
        bb = Z.padpos(M, tref, tnum, place)
        blk = PG.build(PG.drop(ALL, {'U18.' + pin, tgt}), ii)
        blk |= PG.build(sc, ii)
        for pts in laid:
            blk |= PG.build([(x - 0.15, y - 0.15, x + 0.15, y + 0.15)
                             for (x, y) in pts], ii)
        g2 = PG.path(blk, a, bb, want_pts=True)
        if g2 is None:
            continue
        laid.append(g2[1][::3])
        fan += 1
    best = None
    for w in TRUNK_WIDTHS:
        blk = PG.build(PG.drop(ALL, {'R75.2', 'D9.1'}), Z.infl(w))
        blk |= PG.build(sc, Z.infl(w))
        for pts in laid:
            blk |= PG.build([(x - 0.15, y - 0.15, x + 0.15, y + 0.15)
                             for (x, y) in pts], Z.infl(w))
        if PG.path(blk, r75_2, d9_1) is not None:
            best = w
            break
    return fan, best, round(sense_maxx, 3)


def sweep(M):
    rows = []
    t0 = time.time()
    # baseline: measure each c2 base trunk_best_w for reference
    base_w = {}
    for bn, base in C2_BASES.items():
        fan, bw, mx = trunk_best_w(M, base)
        base_w[bn] = bw
        print('base %-4s fan=%s trunk_best_w=%s maxx=%s'
              % (bn, fan, bw, mx))
        sys.stdout.flush()
    for bn, base in C2_BASES.items():
        for third in THIRD_PARTS:
            h = M.home[third]
            for rot in (0, 180):
                for dx in (-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0):
                    for dy in (-1.0, -0.5, 0.0, 0.5, 1.0):
                        place = dict(base)
                        place[third] = (round(h[0] + dx, 3),
                                        round(h[1] + dy, 3), rot)
                        if any(r in Z.FROZEN for r in place):
                            continue
                        if Z.mechanical_ok(M, place):
                            continue
                        fan, bw, mx = trunk_best_w(M, place)
                        if fan != 8:
                            continue
                        rows.append(dict(base=bn, third=third,
                                         pose=list(place[third]),
                                         place={k: list(v) for k, v in place.items()},
                                         fanout=fan, trunk_best_w=bw,
                                         sense_maxx=mx,
                                         base_trunk_w=base_w[bn]))
    # rank: widest trunk first (None last), then least sense bulge, then least
    # third-part displacement
    def disp(r):
        h = M.home[r['third']]
        p = r['pose']
        return (math.hypot(p[0] - h[0], p[1] - h[1])
                + 0.5 * (abs((p[2] - h[2]) % 360.0) > 0.05))
    rows.sort(key=lambda r: (-(r['trunk_best_w'] or 0),
                             r['sense_maxx'] or 99, disp(r)))
    for r in rows:
        r['third_disp'] = round(disp(r), 3)
    print('\nswept %d fan-8 mech-clean card-3 candidates in %.1fs'
          % (len(rows), time.time() - t0))
    return rows, base_w


def main():
    M = PS.Model(RU.fresh(WORK, 'C3a'))
    rows, base_w = sweep(M)
    json.dump({'base_trunk_w': base_w, 'rows': rows},
              open(os.path.join(OUT, 'c3_prefilter.json'), 'w'), indent=1)
    # a candidate is MEANINGFUL only if it widens the trunk beyond its own c2
    # base (i.e. the third part actually helps the casualty).
    meaningful = [r for r in rows
                  if r['trunk_best_w'] is not None
                  and (r['base_trunk_w'] is None
                       or r['trunk_best_w'] > r['base_trunk_w'])]
    print('meaningful (trunk widened vs base): %d' % len(meaningful))
    for r in meaningful[:15]:
        print('  base=%s 3rd=%s%s fan=%d trunk_best_w=%s (base %s) maxx=%s disp=%s'
              % (r['base'], r['third'], r['pose'], r['fanout'],
                 r['trunk_best_w'], r['base_trunk_w'], r['sense_maxx'],
                 r['third_disp']))
    # emit the top meaningful candidates as route_battery_block place JSONs
    M2 = PS.Model(RU.fresh(WORK, 'C3b'))
    seen, idx = set(), []
    for r in meaningful:
        key = (r['base'], r['third'],
               round(r['pose'][0]), round(r['pose'][1]), round(r['pose'][2]))
        if key in seen:
            continue
        seen.add(key)
        i = len(idx)
        moves = {}
        for ref, v in r['place'].items():
            lay = M2.b.GetLayerName(M2.fp[ref].GetLayer())
            moves[ref] = [round(v[0], 3), round(v[1], 3), round(v[2], 1), lay]
        spec = dict(name='002Z-c3-%s-%s' % (r['base'], r['third']),
                    base='AUTHORITATIVE', moves=moves,
                    analytic=dict(fanout=r['fanout'],
                                  trunk_best_w=r['trunk_best_w'],
                                  base_trunk_w=r['base_trunk_w'],
                                  sense_maxx=r['sense_maxx'],
                                  third_disp=r['third_disp'], card=3))
        p = os.path.join(OUT, 'c3_%02d.json' % i)
        json.dump(spec, open(p, 'w'), indent=1)
        idx.append(dict(file='c3_%02d.json' % i, **spec['analytic'],
                        base=r['base'], third=r['third'], pose=r['pose']))
        if len(idx) >= 10:
            break
    json.dump(idx, open(os.path.join(OUT, 'c3_index.json'), 'w'), indent=1)
    print('\nwrote %d cardinality-3 candidate JSONs' % len(idx))


if __name__ == '__main__':
    main()
