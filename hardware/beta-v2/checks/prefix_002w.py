# -*- coding: utf-8 -*-
"""FBV2-P2-002Y -- THE PINNED, SELF-DESCRIBING 002W-PREFIX REGRESSION.

FBV2-P2-002X could not reproduce the "002W 8/8" qualification prefix
(`probe_002w_W3.json`, targets `111111111`, U18 8/8) and every recipe it guessed
landed at U18 6/8 or 7/8.  FBV2-P2-002Y found out why, and it is a
reproducibility defect, not a router defect:

  1. THE RECIPE WAS NEVER PINNED.  No committed file stated the exact flags,
     order and placement that produce the governed prefix, so each task guessed
     and studied a different board.  This file IS that missing statement.

  2. THE PLACEMENT TRAP.  The scratch board `RU.fresh` copies is the AUTHORITATIVE
     six-layer board; `AQROOT_ECO_002F=1` silently swaps in a placement that
     differs in NINE parts (U18 and R76..R83).  FBV2-P2-002X's own attempts were
     run on the ECO board.  `AQROOT_EXPECT_PLACEMENT=AUTHORITATIVE` in RECIPE
     below makes the driver REFUSE TO ROUTE on the wrong placement.

  3. THE SITE IS DETERMINISTIC AND FORCED.  On the AUTHORITATIVE board this recipe
     reserves `U18.8` at (3.000, 71.600) EVERY time -- at 002T, 002U and HEAD
     alike, on both the scored and the nearest-exit attempt, and it is the ONLY
     escape/via candidate the pad has at that point in the schedule (measured:
     `SEAL-DBG U18.8 ... seals=NONE`).  There is no (3.750, 71.600) alternative
     on this board.  The "002T-proven (3.750, 71.600)" site belongs to a board
     with a materially different western margin -- `BAT_SENSE Q3.6->R75.1`
     routes 13.532 mm there and 18.200 mm here, `R75.2`'s reserved via lands at
     (1.200, 65.700) there and (2.800, 63.200) here -- and that board is NOT
     produced by the committed code with ANY constructible recipe.  So D-269's
     clearance change is NOT the cause (002T/002U code give (3.000) too), and the
     site is not the true blocker: at reservation time (3.000, 71.600) seals no
     sibling.  `U18.7` is sealed later, cumulatively, by the current-carrying
     BAT_SENSE diagonal wall (6.75, 62.45)->(2.80, 66.40) -- the same
     current-role blocker FBV2-P2-002X named, now proven on a reproducible board.

WHAT THIS REGRESSION DOES.  It runs the ONE pinned recipe and checks two gates:

  * DETERMINISM (exit 2 on failure) -- the board must reproduce its pinned
    manifest: the AUTHORITATIVE placement, the U18.8 (3.000, 71.600) via, the
    18.200 mm sense path, U18 6/8 with U18.7/U18.8 open.  If this drifts, the
    harness or the recipe changed and a future task is again studying a
    DIFFERENT board -- which is exactly the failure 002Y exists to prevent.

  * GOVERNED GOAL (exit 1 on failure) -- the governed prefix requires U18 8/8
    with U18.8 NOT at the blocking site (3.000, 71.600).  This is UNMET on the
    reproducible board and is the documented FBV2-P2-002Y reproduction gap.  It
    fails, by design and by the brief: "it must fail when U18.8 lands at the
    blocking site or U18 drops below 8/8."

    python prefix_002w.py            # validate against prefix_002w_manifest.json
    python prefix_002w.py --bless    # (re)write the manifest from this run
"""
import os, sys, re, json, subprocess

SP = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(SP, 'prefix_002w_manifest.json')

# THE PINNED RECIPE.  This is the whole point of the file: identical inputs,
# stated once, so identical outputs.  AQROOT_EXPECT_PLACEMENT is the guard that
# stops a run from silently using the ECO placement.
RECIPE = {
    'AQROOT_D256': 'GSQ',
    'AQROOT_Q3_POFV': '1',
    'AQROOT_D266': '1',
    'AQROOT_D267': 'F1',
    'AQROOT_TRUNK_LAST': '1',
    'AQROOT_U18_ORDER': '6,10,7,1,3,2',
    'AQROOT_EXPECT_PLACEMENT': 'AUTHORITATIVE',
    'AQROOT_LOCAL': 'D256',
    'AQROOT_PROBE_PASS1': '1',
    'AQROOT_PROBE_OUT': 'probe_002w_prefix.json',
    'AQROOT_SCRATCH': 'W002W',
}

BLOCKING_SITE = [3.000, 71.600]      # the U18.8 via that seals U18.7's margin
GOVERNED_U18 = 8                      # the governed prefix is 8 of 8


def run_driver():
    env = dict(os.environ)
    env.update(RECIPE)
    p = subprocess.run([sys.executable, '-u',
                        os.path.join(SP, 'route_battery_block.py')],
                       cwd=SP, env=env, capture_output=True, text=True)
    return p.stdout + '\n' + p.stderr


def parse(out):
    d = {}
    d['placement_asserted'] = 'PLACEMENT ASSERTED: AUTHORITATIVE' in out
    m = re.search(r'RESERVED BAT_PROTECTED_P\s+U18\.8\s+->\s+R75\.2.*?'
                  r'(shortest|nearest) vias.*?U18\.8\(([\d.]+),([\d.]+)\)', out)
    if m:
        d['u18_8_attempt'] = m.group(1)
        d['u18_8_via_mm'] = [round(float(m.group(2)), 3),
                             round(float(m.group(3)), 3)]
    m = re.search(r'RESERVED BAT_SENSE\s+U18\.9\s+->\s+R75\.1.*?'
                  r'U18\.9\(([\d.]+),([\d.]+)\)', out)
    if m:
        d['u18_9_via_mm'] = [round(float(m.group(1)), 3),
                             round(float(m.group(2)), 3)]
    m = re.search(r'BAT_SENSE\s+Q3\.6\s+->\s+R75\.1\s+([\d.]+) mm', out)
    if m:
        d['bat_sense_q36_r751_mm'] = round(float(m.group(1)), 3)
    m = re.search(r'PR-40 PROBE\s+targets (\d+)\s+U18 (\d+)/8', out)
    if m:
        d['targets'] = m.group(1)
        d['u18_connected'] = int(m.group(2))
    m = re.search(r'open U18 pins?:\s*([^\n]+)', out)
    if m and 'none' not in m.group(1).lower():
        d['u18_open'] = [s.strip() for s in m.group(1).split(',') if s.strip()]
    else:
        d['u18_open'] = []
    return d


def main():
    bless = '--bless' in sys.argv
    print('FBV2-P2-002Y  PINNED 002W-PREFIX REGRESSION')
    print('  recipe: ' + ' '.join('%s=%s' % kv for kv in sorted(RECIPE.items())
                                   if kv[0] not in ('AQROOT_PROBE_OUT',
                                                    'AQROOT_SCRATCH')))
    print('  running the driver (LOCAL=D256 prefix) ...')
    got = parse(run_driver())
    print('  measured: %s' % json.dumps(got, sort_keys=True))

    if bless:
        man = {
            'task': 'FBV2-P2-002Y',
            'recipe': RECIPE,
            'placement': 'AUTHORITATIVE',
            'deterministic': got,
            'governed_goal': {
                'u18_connected': GOVERNED_U18,
                'u18_8_via_forbidden_mm': BLOCKING_SITE,
                'kelvin_A_mm': 7.644, 'kelvin_B_mm': 9.927,
                'kelvin_mismatch_mm': 2.283,
            },
            'status': ('REPRODUCTION GAP: the governed 8/8 prefix is NOT '
                       'reproducible from committed code; this manifest pins '
                       'the deterministic 6/8 board so every task studies it.'),
        }
        json.dump(man, open(MANIFEST, 'w'), indent=1, sort_keys=True)
        print('  BLESSED -> %s' % os.path.basename(MANIFEST))
        return 0

    man = json.load(open(MANIFEST))
    det = man['deterministic']

    # ---- GATE 1: DETERMINISM (a drift here means a DIFFERENT board) ----------
    drift = []
    if not got.get('placement_asserted'):
        drift.append('placement was not AUTHORITATIVE-asserted')
    for k in ('u18_8_via_mm', 'u18_9_via_mm', 'bat_sense_q36_r751_mm',
              'u18_connected', 'targets', 'u18_open'):
        if got.get(k) != det.get(k):
            drift.append('%s: got %s, manifest %s' % (k, got.get(k), det.get(k)))
    print('=' * 70)
    if drift:
        print('DETERMINISM: **FAIL** -- this is NOT the pinned board:')
        for x in drift:
            print('   %s' % x)
        print('PREFIX 002W REGRESSION: FAIL (determinism drift, exit 2)')
        return 2
    print('DETERMINISM: PASS -- board matches the pinned manifest exactly')

    # ---- GATE 2: GOVERNED GOAL (the documented, expected-failing gap) --------
    gov = []
    if got.get('u18_connected', 0) < GOVERNED_U18:
        gov.append('U18 %d/8 (governed 8/8); open %s'
                   % (got.get('u18_connected'), got.get('u18_open')))
    if got.get('u18_8_via_mm') == BLOCKING_SITE:
        gov.append('U18.8 reserved at the blocking site %s' % BLOCKING_SITE)
    if gov:
        print('GOVERNED GOAL: **FAIL** -- the documented 002Y reproduction gap:')
        for x in gov:
            print('   %s' % x)
        print('   the western margin is oversubscribed by the current-carrying')
        print('   BAT_SENSE diagonal (6.75,62.45)->(2.80,66.40); U18.7 is its')
        print('   casualty.  No legal reservation site or low-current offload')
        print('   opens 8/8 on this board.  See D-271.')
        print('PREFIX 002W REGRESSION: FAIL (governed gap, exit 1)')
        return 1
    print('GOVERNED GOAL: PASS -- U18 8/8, U18.8 off the blocking site')
    print('PREFIX 002W REGRESSION: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
