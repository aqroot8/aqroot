# -*- coding: utf-8 -*-
"""FBV2-P2-002Z / D-272 -- THE BOUNDED WESTERN-MARGIN PLACEMENT SEARCH.

The CTO ruling that frames this task: D-271 stopped at an OWNER label, but a
bounded component-placement decision inside locked topology and product
requirements is CTO authority.  Before any F.Cu high-current via bridge or the
2.29x long B.Cu route, investigate the LEAST-INVASIVE placement ECO that widens
the western margin enough for the current-carrying BAT_SENSE path, U18 8/8 and
the short BPP trunk to COEXIST.

This file is the ANALYTIC PREFILTER, not the arbiter.  The arbiter is the full
deterministic routing prefix (route_battery_block.py + AQROOT_PLACE_JSON), which
is expensive (~9 min/run); this file is cheap (~seconds) and its only job is to
rank hundreds of candidate poses so only the few that plausibly reach 8/8 with a
short, non-bulging BAT_SENSE path and a live trunk corridor are spent on a real
routing run.  Every candidate reuses place_search_002f's Model (real courtyards
and pad geometry from pcbnew) and PathGrid (courtyard-level Dijkstra, so a length
is what a track must walk, not what a ruler says).

WHAT IT MODELS THAT place_search_002f DID NOT.  002F scored U18's Kelvin taps and
the trunk.  The D-271 blocker is neither: it is the CURRENT-CARRYING BAT_SENSE
path Q3.6 -> R75.1, an 18.200 mm diagonal wall (6.75,62.45)->(2.80,66.40) that
seals U18.7.  So this model lays that path FIRST (as the driver does, D-266 s5),
as a 1.00 mm obstacle, THEN runs the U18 8-pin fanout on top of it, THEN the
1.50 mm trunk -- exactly the order and the interaction that decide 8/8.

CARDINALITY HIERARCHY (brief section 3), stop at the first cardinality with a
fully-successful candidate:
  a. one functional component among U18, R75, Q3;
  b. U18 + the minimum directly-coupled divider parts;
  c. rigid clusters U18+R76..R83, then R75+U18+R76..R83;
  d. only if needed, a bounded Q3/R75/U18 protection subcluster.
J4/F1/Q2 and the accepted monotonic chain are NOT moved without measured
necessity; TP17 and C58 are FIXED (brief section 4).

    python place_search_002z.py            # score all families, write candidates
    python place_search_002z.py --family a # one family only
"""
import os, sys, json, math, time, itertools
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import place_search_002f as PS
import path_role_util as RU
import pcbnew

N = '/01_POWER_TREE/'
WORK = os.path.join(SP, 'w')
OUT = os.path.join(SP, 'place_002z')
if not os.path.isdir(OUT):
    os.makedirs(OUT)

# ---- widths (nm) and half-inflations (mm) --------------------------------
CLEAR = 0.20                                   # western-margin clearance, mm
def infl(w_nm):
    return w_nm / 2e6 + CLEAR / 2.0

W_SENSE_CUR = 1000000     # BAT_SENSE current path, 1.00 mm (D-270: frozen role)
W_TRUNK = 1500000         # BPP trunk target 1.50 mm
W_TRUNK_FLOOR = 1200000   # BPP trunk floor 1.20 mm
U18MIN = {'1': 200000, '2': 150000, '3': 150000, '6': 150000, '7': 150000,
          '8': 200000, '9': 200000, '10': 150000}
U18TARGET = {'1': 'R77.1', '2': 'R79.2', '3': 'R77.2', '6': 'R80.2',
             '7': 'R81.2', '8': 'R75.2', '9': 'R75.1', '10': 'R76.1'}
# fanout order: the plan / slack order place_search_002f.fanout uses.
FAN_ORDER = ['9', '8', '1', '7', '3', '2', '10', '6']

# TP17 and C58 are FIXED by the brief; the monotonic chain and J4/F1/Q2 too.
FROZEN = frozenset(['J4', 'F1', 'Q2', 'D9', 'U11', 'U14', 'TP17', 'C58',
                    'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'TP34', 'C59'])


def padpos(M, ref, num, place):
    """Absolute pad position under the candidate placement (or home pose)."""
    pose = place.get(ref, M.home[ref])
    return M.pad(ref, num, pose[0], pose[1], pose[2])


def court(M, ref, place):
    pose = place.get(ref, M.home[ref])
    return M.court(ref, pose[0], pose[1], pose[2])


def mechanical_ok(M, place):
    """Courtyard collision (side-aware), board edge and rule-area audit, exactly
    the place_p2_002f.apply() predicate but as a pure function.  Returns [] if
    clean, else a list of (ref, what) collisions."""
    bad = []
    moved = set(place)
    for ref in place:
        f = M.fp[ref]
        ca = court(M, ref, place)
        # board edge (M.edge already inset 0.05 for the outline halo)
        if (ca[0] < M.edge[0] or ca[1] < M.edge[1] or
                ca[2] > M.edge[2] or ca[3] > M.edge[3]):
            bad.append((ref, 'board edge'))
        # against every OTHER footprint courtyard
        for g_ref, g in M.fp.items():
            if g_ref == ref:
                continue
            if g_ref in moved:
                cb = court(M, g_ref, place)
            else:
                cy = g.GetCourtyard(g.GetLayer())
                bb = cy.BBox() if cy.OutlineCount() else g.GetBoundingBox()
                cb = (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                      bb.GetRight() / 1e6, bb.GetBottom() / 1e6)
            if not PS.ovl(ca, cb):
                continue
            # opposite faces meet only through a hole
            if g.IsFlipped() != f.IsFlipped():
                if (not any(p.GetDrillSizeX() > 0 for p in g.Pads()) and
                        not any(p.GetDrillSizeX() > 0 for p in f.Pads())):
                    continue
            bad.append((ref, g_ref))
        # rule areas
        for rr in M.rule:
            if PS.ovl(ca, rr):
                bad.append((ref, 'ruleArea'))
    return bad


def evaluate(M, place, grid=0.25):
    """Analytic western-margin score for one candidate placement.

    Order mirrors the driver: BAT_SENSE current path first (obstacle), then the
    U18 8-pin fanout on top of it, then the trunk.  Returns a dict of measured
    quantities and a boolean `viable` (fanout 8/8, trunk present, both Kelvin
    <=10 mm) that decides whether a full-prefix run is worth spending.
    """
    PG = PS.PathGrid(0.0, 44.0, 26.0, 86.0, grid)
    moved = set(place)
    FP = M.fixed_pads(moved)               # (id, rect) for every non-moved pad
    # moved footprints contribute their pad rects at the new pose
    moved_pads = []
    for ref in place:
        moved_pads += M.padrects_id(ref, *place[ref])
    ALL = FP + moved_pads

    q36 = padpos(M, 'Q3', '6', place)
    r75_1 = padpos(M, 'R75', '1', place)
    r75_2 = padpos(M, 'R75', '2', place)
    d9_1 = padpos(M, 'D9', '1', place)

    res = dict(place={k: [round(v, 3) for v in vv] for k, vv in place.items()})

    # ---- 1. BAT_SENSE current path Q3.6 -> R75.1, laid FIRST ----------------
    b_sense = PG.build(PG.drop(ALL, {'Q3.6', 'R75.1'}), infl(W_SENSE_CUR))
    got = PG.path(b_sense, q36, r75_1, want_pts=True)
    if got is None:
        res.update(sense_mm=None, viable=False, reason='BAT_SENSE no path')
        return res
    sense_mm, sense_pts = got
    res['sense_mm'] = round(sense_mm, 3)
    # how far EAST the current path bulges -- the D-271 wall reached x=6.75
    res['sense_max_x'] = round(max(p[0] for p in sense_pts), 3)
    sense_cells = [(x - 0.15, y - 0.15, x + 0.15, y + 0.15)
                   for (x, y) in sense_pts[::2]]

    # ---- 2. U18 8-pin fanout on top of the BAT_SENSE obstacle ---------------
    laid = []
    fan_ok, lens = [], {}
    for pin in FAN_ORDER:
        tgt = U18TARGET[pin]
        tref, tnum = tgt.split('.')
        w = U18MIN[pin]
        ii = infl(w)
        a = padpos(M, 'U18', pin, place)
        b = padpos(M, tref, tnum, place)
        blk = PG.build(PG.drop(ALL, {'U18.' + pin, tgt}), ii)
        blk |= PG.build(sense_cells, ii)          # BAT_SENSE is already copper
        for pts in laid:
            blk |= PG.build([(x - 0.15, y - 0.15, x + 0.15, y + 0.15)
                             for (x, y) in pts], ii)
        g2 = PG.path(blk, a, b, want_pts=True)
        if g2 is None:
            fan_ok.append(pin + ':X')
            continue
        d, pts = g2
        lens[pin] = round(d, 2)
        laid.append(pts[::3])
        fan_ok.append(pin)
    res['fanout'] = sum(1 for k in fan_ok if not k.endswith(':X'))
    res['fanout_detail'] = fan_ok
    res['fanout_lens'] = lens
    res['open'] = [p for p in fan_ok if p.endswith(':X')]

    # ---- 3. Kelvin pair (already in fanout as pins 8, 9) --------------------
    res['k8'] = lens.get('8')
    res['k9'] = lens.get('9')
    res['kmis'] = (round(abs(lens['8'] - lens['9']), 3)
                   if '8' in lens and '9' in lens else None)

    # ---- 4. the 1.50 mm trunk R75.2 -> D9.1, with everything laid -----------
    blk_tr = PG.build(PG.drop(ALL, {'R75.2', 'D9.1'}), infl(W_TRUNK))
    blk_tr |= PG.build(sense_cells, infl(W_TRUNK))
    for pts in laid:
        blk_tr |= PG.build([(x - 0.15, y - 0.15, x + 0.15, y + 0.15)
                            for (x, y) in pts], infl(W_TRUNK))
    tr = PG.path(blk_tr, r75_2, d9_1)
    res['trunk_150'] = round(tr, 3) if tr is not None else None
    if tr is None:                                # retry at the 1.20 floor
        blk_tr2 = PG.build(PG.drop(ALL, {'R75.2', 'D9.1'}), infl(W_TRUNK_FLOOR))
        blk_tr2 |= PG.build(sense_cells, infl(W_TRUNK_FLOOR))
        for pts in laid:
            blk_tr2 |= PG.build([(x - 0.15, y - 0.15, x + 0.15, y + 0.15)
                                for (x, y) in pts], infl(W_TRUNK_FLOOR))
        tr2 = PG.path(blk_tr2, r75_2, d9_1)
        res['trunk_120'] = round(tr2, 3) if tr2 is not None else None
    else:
        res['trunk_120'] = res['trunk_150']

    res['viable'] = bool(res['fanout'] == 8 and res.get('trunk_120') is not None
                         and res['k8'] is not None and res['k9'] is not None
                         and res['k8'] <= 10.0 and res['k9'] <= 10.0)
    return res


# ===========================================================================
#  CANDIDATE FAMILIES -- cardinality-ordered
# ===========================================================================
def fam_a(M):
    """Cardinality 1: ONE of U18, R75, Q3.  Rotation x small translation on a
    0.25 mm grid.  West is bounded by the board edge, so translations are the
    directions the margin can actually give.  R75 rotation is emphasised: a
    180 deg rotation swaps R75.1 (BAT_SENSE, today the SOUTH pad against U18) to
    the NORTH pad against Q3, which is exactly where the current path enters --
    a zero-displacement reorientation that could de-bulge the sense diagonal."""
    cands = []
    # -- R75: rotation (incl. the 180 swap) + small east/north/south nudges --
    for rot in (90, 270):
        for dx in (0.0, 0.5, 1.0, 1.5, 2.0):        # east only (west = edge)
            for dy in (-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5):
                x = round(M.home['R75'][0] + dx, 3)
                y = round(M.home['R75'][1] + dy, 3)
                cands.append(('a', 'R75', {'R75': (x, y, rot)}))
    # -- U18: rotation x translation, small box around home ------------------
    for rot in (0, 90, 180, 270):
        for dx in (-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0):
            for dy in (-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0):
                x = round(M.home['U18'][0] + dx, 3)
                y = round(M.home['U18'][1] + dy, 3)
                cands.append(('a', 'U18', {'U18': (x, y, rot)}))
    # -- Q3: the chain part; only tiny nudges + rotation, measured necessity --
    for rot in (90, 270):
        for dx in (-0.5, 0.0, 0.5, 1.0):
            for dy in (-1.0, -0.5, 0.0):
                x = round(M.home['Q3'][0] + dx, 3)
                y = round(M.home['Q3'][1] + dy, 3)
                cands.append(('a', 'Q3', {'Q3': (x, y, rot)}))
    return cands


def fam_b(M):
    """Cardinality 2-4: U18 + the minimum directly-coupled divider parts whose
    pads are U18's own Kelvin/gate targets (R75 is a target for 8/9; but R75 is
    covered in family c/d).  Here: U18 + R80/R81 (the LTC_SHDN/FAULT ring pads
    U18.6/U18.7 escape to), tried because U18.7 is the sealed casualty."""
    cands = []
    for rot in (0, 90, 180, 270):
        for dx in (-0.5, 0.0, 0.5, 1.0, 1.5):
            for dy in (-1.5, -1.0, -0.5, 0.0, 0.5):
                u = (round(M.home['U18'][0] + dx, 3),
                     round(M.home['U18'][1] + dy, 3), rot)
                # R81 nudged east to give U18.7 a clearer landing
                for r81dx in (0.0, 0.5, 1.0):
                    pl = {'U18': u,
                          'R81': (round(M.home['R81'][0] + r81dx, 3),
                                  M.home['R81'][1], M.home['R81'][2])}
                    cands.append(('b', 'U18+R81', pl))
    return cands


def fam_cd(M):
    """Cardinality high: R75 reorientation + U18, and the Q3/R75/U18 protection
    subcluster.  These are only reached if a and b are dry; enumerated lazily by
    the runner.  Here we expose the two most-promising structured moves:
      - R75 rotated 180 (BAT_SENSE to the north pad) + U18 nudged to follow;
      - Q3 nudged south + R75 rotated + U18, the full protection subcluster."""
    cands = []
    for r75rot in (270,):
        for u_rot in (0, 90):
            for udx in (-0.5, 0.0, 0.5, 1.0):
                for udy in (-1.0, -0.5, 0.0, 0.5):
                    pl = {'R75': (M.home['R75'][0], M.home['R75'][1], r75rot),
                          'U18': (round(M.home['U18'][0] + udx, 3),
                                  round(M.home['U18'][1] + udy, 3), u_rot)}
                    cands.append(('cd', 'R75rot+U18', pl))
    return cands


FAMILIES = {'a': fam_a, 'b': fam_b, 'cd': fam_cd}


def run(fam_keys):
    M = PS.Model(RU.fresh(WORK, 'Z0'))
    t0 = time.time()
    all_rows = []
    for fk in fam_keys:
        cands = FAMILIES[fk](M)
        print('family %s: %d raw candidates' % (fk, len(cands)))
        sys.stdout.flush()
        mech_rej = 0
        rows = []
        for (fam, label, place) in cands:
            # frozen guard
            if any(r in FROZEN for r in place):
                continue
            bad = mechanical_ok(M, place)
            if bad:
                mech_rej += 1
                continue
            r = evaluate(M, place)
            r['family'] = fam
            r['label'] = label
            r['card'] = len(place)
            rows.append(r)
        viable = [r for r in rows if r['viable']]
        print('  %d cleared mechanical (%d rejected), %d ANALYTIC-VIABLE'
              % (len(rows), mech_rej, len(viable)))
        # rank: viable first, then fanout desc, sense short, no east bulge,
        # trunk short, low Kelvin mismatch, low displacement/rotation
        def disp(r):
            d = 0.0
            for ref, v in r['place'].items():
                h = M.home[ref]
                d += math.hypot(v[0] - h[0], v[1] - h[1])
                d += 0.5 * (abs((v[2] - h[2]) % 360.0) > 0.05)
            return d
        rows.sort(key=lambda r: (
            not r['viable'],
            -(r.get('fanout') or 0),
            r.get('sense_max_x') or 99,
            r.get('sense_mm') or 99,
            r.get('kmis') if r.get('kmis') is not None else 99,
            r.get('trunk_120') or 99,
            r['card'], disp(r)))
        for r in rows:
            r['disp'] = round(disp(r), 3)
        all_rows += rows
        # write the family report
        json.dump(rows, open(os.path.join(OUT, 'family_%s.json' % fk), 'w'),
                  indent=1)
        # print the top of each family
        for r in rows[:12]:
            print('  %-12s card=%d %s  fan=%s open=%s sense=%s maxx=%s '
                  'k8=%s k9=%s mis=%s tr150=%s tr120=%s disp=%.2f %s'
                  % (r['label'], r['card'],
                     json.dumps(r['place']), r.get('fanout'), r.get('open'),
                     r.get('sense_mm'), r.get('sense_max_x'),
                     r.get('k8'), r.get('k9'), r.get('kmis'),
                     r.get('trunk_150'), r.get('trunk_120'), r['disp'],
                     'VIABLE' if r['viable'] else ''))
        sys.stdout.flush()
    print('search done in %.1f s' % (time.time() - t0))
    return all_rows


def write_candidate(M, row, path):
    """Emit a route_battery_block AQROOT_PLACE_JSON {name, base, moves}, moves as
    [x, y, rot, layer] on top of AUTHORITATIVE, plus the fingerprint layer."""
    moves = {}
    for ref, v in row['place'].items():
        lay = M.b.GetLayerName(M.fp[ref].GetLayer())
        moves[ref] = [round(v[0], 3), round(v[1], 3), round(v[2], 1), lay]
    spec = dict(name='002Z-%s-%s' % (row['family'], row['label']),
                base='AUTHORITATIVE', moves=moves,
                analytic={k: row.get(k) for k in
                          ('fanout', 'open', 'sense_mm', 'sense_max_x',
                           'k8', 'k9', 'kmis', 'trunk_150', 'trunk_120',
                           'disp', 'card', 'viable')})
    json.dump(spec, open(path, 'w'), indent=1)
    return spec


def main():
    if '--family' in sys.argv:
        fam = sys.argv[sys.argv.index('--family') + 1]
        rows = run([fam])
    else:
        rows = run(['a', 'b', 'cd'])
    # write the top viable candidates (and, if none viable, the top by fanout)
    M = PS.Model(RU.fresh(WORK, 'Z1'))
    viable = [r for r in rows if r['viable']]
    pool = viable if viable else rows
    # de-dup by rounded pose so we do not spend a routing run on 0.25 mm twins
    seen, picks = set(), []
    for r in sorted(pool, key=lambda r: (not r['viable'], -(r.get('fanout') or 0),
                                         r.get('sense_max_x') or 99, r['card'])):
        key = tuple(sorted((k, round(v[0]), round(v[1]), round(v[2]))
                           for k, v in r['place'].items()))
        if key in seen:
            continue
        seen.add(key)
        picks.append(r)
        if len(picks) >= 12:
            break
    idx = []
    for i, r in enumerate(picks):
        p = os.path.join(OUT, 'cand_%02d.json' % i)
        spec = write_candidate(M, r, p)
        idx.append(dict(file=os.path.basename(p), **spec['analytic'],
                        label=r['label'], place=r['place']))
    json.dump(idx, open(os.path.join(OUT, 'candidates_index.json'), 'w'), indent=1)
    print('\nwrote %d candidate placement JSONs to %s' % (len(idx), OUT))
    print('viable candidates: %d' % len(viable))


if __name__ == '__main__':
    main()
