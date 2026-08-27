# -*- coding: utf-8 -*-
"""FBV2-P2-002Z -- run the PINNED 002W/D-271 routing prefix on a candidate
placement and report the real gates.

This is the ARBITER the analytic place_search_002z is a prefilter for.  It uses
the EXACT pinned recipe from prefix_002w.py (so the comparison to the D-271
baseline is same-recipe, different-placement), but injects a candidate via
AQROOT_PLACE_JSON and asserts it via AQROOT_EXPECT_PLACEMENT pointing at the same
file -- the applied board and the asserted board cannot drift.

    python run_prefix_002z.py <candidate.json> <scratch_tag>

Prints the PR-40 line (U18 x/8, targets, open pins) and the BAT_SENSE current
path length, and writes a per-candidate probe JSON next to the candidate.
"""
import os, sys, re, json, subprocess

SP = os.path.dirname(os.path.abspath(__file__))

# the pinned D-271 recipe, verbatim, MINUS the placement assertion (which the
# candidate supplies) and the probe-out/scratch (which are per-candidate).
RECIPE = {
    'AQROOT_D256': 'GSQ',
    'AQROOT_Q3_POFV': '1',
    'AQROOT_D266': '1',
    'AQROOT_D267': 'F1',
    'AQROOT_TRUNK_LAST': '1',
    'AQROOT_U18_ORDER': '6,10,7,1,3,2',
    'AQROOT_LOCAL': 'D256',
    'AQROOT_PROBE_PASS1': '1',
}


def parse(out):
    d = {}
    m = re.search(r'CANDIDATE PLACEMENT APPLIED: (\S+)', out)
    d['applied'] = bool(m)
    d['asserted'] = 'PLACEMENT ASSERTED:' in out
    d['mismatch'] = 'PLACEMENT IDENTITY MISMATCH' in out
    m = re.search(r'PR-40 PROBE\s+targets (\S+)\s+U18 (\d+)/8\s+U19 (\d+)/7\s+'
                  r'ledger (\d+)/(\d+)', out)
    if m:
        d['targets'] = m.group(1)
        d['u18'] = int(m.group(2))
        d['u19'] = int(m.group(3))
        d['ledger'] = '%s/%s' % (m.group(4), m.group(5))
    m = re.search(r'open U18 pins:\s*([^\n]+)', out)
    if m:
        s = m.group(1).strip()
        d['u18_open'] = [] if s == 'none' else [x.strip() for x in s.split(',')]
    m = re.search(r'BAT_SENSE\s+Q3\.6\s+->\s+R75\.1\s+([\d.]+) mm', out)
    if m:
        d['sense_mm'] = round(float(m.group(1)), 3)
    return d


def main():
    cand = os.path.abspath(sys.argv[1])
    tag = sys.argv[2]
    env = dict(os.environ)
    env.update(RECIPE)
    env['AQROOT_PLACE_JSON'] = cand
    env['AQROOT_EXPECT_PLACEMENT'] = cand
    env['AQROOT_SCRATCH'] = tag
    probe = os.path.join(SP, 'place_002z', 'probe_%s.json' % tag)
    env['AQROOT_PROBE_OUT'] = probe
    p = subprocess.run([sys.executable, '-u',
                        os.path.join(SP, 'route_battery_block.py')],
                       cwd=SP, env=env, capture_output=True, text=True)
    out = p.stdout + '\n' + p.stderr
    # keep the full log for forensics
    log = os.path.join(SP, 'place_002z', 'log_%s.txt' % tag)
    open(log, 'w').write(out)
    got = parse(out)
    got['candidate'] = os.path.basename(cand)
    got['tag'] = tag
    got['returncode'] = p.returncode
    json.dump(got, open(os.path.join(SP, 'place_002z', 'result_%s.json' % tag),
                        'w'), indent=1)
    print('%-10s %s' % (tag, json.dumps(got, sort_keys=True)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
