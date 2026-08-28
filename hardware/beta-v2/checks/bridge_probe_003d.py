# -*- coding: utf-8 -*-
"""D-276 standing probe -- THE DRIVER-INTEGRATED VACATE + F.Cu BRIDGE, a
MEASURED REPRODUCIBLE FAIL.

003C proved the western-corridor vacate + F.Cu via-array bridge as a POST-PROCESS
of a hand-staged board (bridge_probe_003c pins that mechanism).  003D integrates
the SAME mechanism as an in-line stage of the production Phase-A driver
(route_battery_block.py, guarded by AQROOT_BRIDGE_ECO -> bridge_eco_003d.apply_eco)
and runs it through a FULL 2-pass Phase-A route under the D-271 reproducibility
discipline.  D-276 ruled the outcome: on a board produced by the full production
driver route (NOT the hand-staged c3 post-process of 003C), the vacate+bridge ECO
REPRODUCIBLY ABORTS -- there is no >= 1.20 mm F.Cu traverse corridor to bridge --
and Phase A itself REPRODUCIBLY FAILS earlier at N_POL U19.3 NO_LEGAL_ESCAPE.
003D therefore FAILS production / full-driver promotion.  003C / D-275 is NOT
invalidated: its post-processed reproducible BAT_PROTECTED_P closure remains the
fixed proven evidence to preserve into 003E.

This probe pins that measured reproducible FAIL, so a later edit that silently
unwires the hook, re-implements (rather than reuses) the proven copper primitives,
weakens the D-275 constraints, or -- crucially -- causes the driver-integrated
bridge to be reported as PASSING again without a real full-gate PASS is caught:

  A  the driver hook is wired: AQROOT_BRIDGE_ECO guards a call into
     bridge_eco_003d.apply_eco, before the authoritative DRC / result write.
  B  bridge_eco_003d single-sources the proven copper primitives + D-275
     constants from bridge_route_003c (no divergent re-implementation).
  C  the vacate stays cardinality-1 / control-role only, the trunk is never on an
     inner layer, the array floor is >= 3 (the path-role classifier contract,
     shared with bridge_probe_003c).
  D  the recorded DRIVER-INTEGRATED Phase-A results (phaseA_003d_eco*.json) each
     report the D-276 measured FAIL: the bridge ECO aborts with no >= 1.20 mm F.Cu
     traverse corridor, AND Phase A fails N_POL U19.3->(node) NO_LEGAL_ESCAPE.  No
     003D result claims a promotion (no bridge_eco.ok, no closed BPP trunk) absent
     a real full-gate PASS.
  E  2-pass determinism of the FAIL: every recorded driver pass agrees on the
     decisive measurements -- Phase-A fail, connections, skipped, ratsnest(+delta),
     DRC counts, and the bridge-ECO abort (the D-271 reproducibility discipline).

Exit 0 = pass, 1 = fail.  Fast: no routing, no board mutation.
"""
import glob, json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import fcu_cutset_003c as CS       # the shared path-role vacate classifier
import bridge_eco_003d as ECO      # the driver stage under test
import bridge_route_003c as BR     # the proven copper primitives / constants

N = '/01_POWER_TREE/'
FAILED = []


def chk(name, got, want, ok):
    print('  %-4s %-58s %-22s expected %s'
          % ('PASS' if ok else 'FAIL', name, got, want))
    if not ok:
        FAILED.append(name)
    return ok


def main():
    print('D-276 DRIVER-INTEGRATED VACATE + F.Cu BRIDGE PROBE')

    # A -- the driver hook is wired and ordered correctly -----------------------
    drv = open(os.path.join(SP, 'route_battery_block.py'), encoding='utf-8').read()
    hook = ("AQROOT_BRIDGE_ECO" in drv and "bridge_eco_003d" in drv
            and "apply_eco(pcb)" in drv)
    chk('A  driver hook AQROOT_BRIDGE_ECO -> bridge_eco_003d.apply_eco',
        'wired' if hook else 'missing', 'wired', hook)
    # ordered: the ECO call is after the routed save, before the final DRC
    i_eco = drv.find('apply_eco(pcb)')
    i_drc = drv.find('RU.drc(pcb, "Afinal"')
    chk('A  ECO runs before the authoritative Afinal DRC',
        '%s' % (0 <= i_eco < i_drc), 'True', 0 <= i_eco < i_drc)

    # B -- single source of truth: ECO reuses BR primitives + constants ---------
    reuse = all(getattr(ECO, k) is getattr(BR, k)
                for k in ('NET', 'SHDN', 'DIA', 'DRILL', 'W_TRAVERSE', 'W_LAND',
                          'NODE_AIM'))
    fns = (ECO.BR.vacate is BR.vacate and ECO.BR.inject_vias is BR.inject_vias
           and ECO.BR.scan_entry_sites is BR.scan_entry_sites
           and ECO.BR.route_traverse is BR.route_traverse)
    chk('B  ECO single-sources D-275 constants from bridge_route_003c',
        'reused' if reuse else 'diverged', 'reused', reuse)
    chk('B  ECO single-sources the copper primitives (no re-impl)',
        'reused' if fns else 'diverged', 'reused', fns)
    chk('B  vacate net is the control branch BAT_PROT_SHDN_CTL',
        ECO.SHDN, N + 'BAT_PROT_SHDN_CTL', ECO.SHDN == N + 'BAT_PROT_SHDN_CTL')

    # C -- the path-role vacate contract (shared with bridge_probe_003c) --------
    ctl = CS.branch_role(N + 'BAT_PROT_SHDN_CTL', {'Q4.1', 'R83.1'})[0]
    chk('C  control BAT_PROT_SHDN_CTL IS a vacate candidate',
        '%s' % ctl, 'candidate', ctl == 'candidate')
    for badnet in ('BAT_PROTECTED_P', 'BAT_SENSE', 'BAT_MID', 'BAT_CONNECTOR_P'):
        v = CS.branch_role(N + badnet, {'X.1', 'Y.1'})[0]
        chk('C  current-carrying %s is NOT a vacate candidate' % badnet,
            '%s' % v, 'None', v is None)

    # D / E -- the recorded DRIVER-INTEGRATED Phase-A results: the D-276 measured
    # reproducible FAIL, and its 2-pass determinism -----------------------------
    ABORT = 'no >= 1.20 mm F.Cu traverse corridor'
    N_POL = 'N_POL U19.3->(node)'
    passes = sorted(glob.glob(os.path.join(SP, 'phaseA_003d_eco*.json')))
    chk('D  driver-integrated Phase-A result(s) recorded (>= 2 passes)',
        '%d found' % len(passes), '>=2', len(passes) >= 2)
    decisive = set()
    for pp in passes:
        r = json.load(open(pp))
        tag = os.path.basename(pp)
        be = r.get('bridge_eco') or {}
        # the bridge ECO reproducibly ABORTS: it ran but found no corridor
        aborted = (be.get('ok') is False and be.get('fail') == ABORT)
        chk('D  [%s] bridge ECO aborts: %r' % (tag, ABORT),
            'abort' if aborted else '%s' % be.get('fail'), 'abort', aborted)
        # Phase A itself reproducibly FAILS at the N_POL U19.3 escape
        fail = r.get('fail') or ''
        npol = fail.startswith(N_POL) and 'NO_LEGAL_ESCAPE' in fail
        chk('D  [%s] Phase A fails %s NO_LEGAL_ESCAPE' % (tag, N_POL),
            'fail' if npol else '%r' % fail[:40], 'fail', npol)
        # no 003D pass may claim a promotion (a closed BPP trunk) absent a gate PASS
        promoted = bool(be.get('ok')) or (fail == '' and be.get('bit8_closed'))
        chk('D  [%s] no false promotion (bridge_eco.ok / closed trunk)' % tag,
            'promoted' if promoted else 'none', 'none', not promoted)
        decisive.add(json.dumps({
            'fail': fail,
            'connections': r.get('connections'),
            'skipped': r.get('skipped'),
            'ratsnest': r.get('ratsnest'),
            'ratsnest_delta': r.get('ratsnest_delta'),
            'drc': r.get('drc'),
            'eco_ok': be.get('ok'),
            'eco_fail': be.get('fail'),
            'vacated': be.get('vacated'),
        }, sort_keys=True))
    chk('E  2-pass determinism: identical decisive measurements across %d pass(es)'
        % len(passes), '%d distinct' % len(decisive), '1',
        len(passes) >= 2 and len(decisive) == 1)

    print('\nD-276 DRIVER BRIDGE PROBE:',
          'PASS' if not FAILED else 'FAIL %s' % FAILED)
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
