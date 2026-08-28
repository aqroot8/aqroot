# -*- coding: utf-8 -*-
"""FBV2-P2-003D / D-275 -- the DRIVER-INTEGRATED gate for the vacate ECO + F.Cu
via-array bridge, run on a board produced by a FULL Phase-A route
(route_battery_block.py with AQROOT_BRIDGE_ECO), not a hand-staged post-process.

Reuses the proven 003C gate contract verbatim (bridge_gates_003c.check / jn_map /
TARGETS / U18PINS / CONTROL + RU.drc): the ECO board must, versus its pre-ECO
baseline, CLOSE bit 8 (BAT_PROTECTED_P R75.2->U11.2), keep all 9 PR-40 targets
true, U18 8/8, regress no control/sense/target net, add no new DRC class, and not
worsen the ratsnest.

    python bridge_gates_003d.py <eco_board.kicad_pcb> [<baseline_board.kicad_pcb>]

Default baseline is the pre_eco.kicad_pcb snapshot the ECO writes next to the
board.  Writes place_002z/bridge_gates_003d_<tag>.json.  Exit 0 = PASS.
"""
import os, sys, json
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import bridge_gates_003c as G      # proven check()/jn_map()/TARGETS/U18PINS/CONTROL
import path_role_util as RU

WORK = os.path.join(SP, 'w')


def verdict(base, brd, cb, cr):
    newdrc = {k: cr.get(k, 0) - cb.get(k, 0)
              for k in set(cr) | set(cb) if cr.get(k, 0) != cb.get(k, 0)}
    ctl_regressions = [k for k in brd['control']
                       if base['control'][k] and not brd['control'][k]]
    u18_regressions = [k for k in brd['u18']
                       if base['u18'][k] and not brd['u18'][k]]
    tgt_regressions = [k for k in brd['targets']
                       if base['targets'][k] and not brd['targets'][k]]
    v = dict(bit8_closed=brd['targets']['BAT_PROTECTED_P R75.2->U11.2'],
             all9_targets=all(brd['targets'].values()),
             u18_8of8=brd['u18_connected'] == 8,
             control_not_regressed=not ctl_regressions,
             u18_not_regressed=not u18_regressions,
             targets_not_regressed=not tgt_regressions,
             no_new_drc=all(x <= 0 for x in newdrc.values()),
             ratsnest_not_worse=brd['ratsnest'] <= base['ratsnest'])
    return v, newdrc, ctl_regressions


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    eco = os.path.abspath(sys.argv[1])
    base = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(eco), 'pre_eco.kicad_pcb')
    tag = os.environ.get('AQROOT_GATE_TAG',
                         os.path.basename(os.path.dirname(eco)))
    if not os.path.exists(base):
        print('bridge_gates_003d: baseline board missing:', base)
        return 2
    b = G.check(base, 'baseline ' + os.path.relpath(base, SP))
    r = G.check(eco, 'eco ' + os.path.relpath(eco, SP))
    cb, _ = RU.drc(base, 'Bd_base_%s' % tag, WORK)
    cr, _ = RU.drc(eco, 'Bd_eco_%s' % tag, WORK)
    v, newdrc, ctl_reg = verdict(b, r, cb, cr)

    print('=== FBV2-P2-003D DRIVER-INTEGRATED BRIDGE GATE (%s) ===' % tag)
    print(' PR-40 baseline:', b['targets_true'])
    print(' PR-40 eco     :', r['targets_true'])
    for k in r['targets']:
        flag = '' if r['targets'][k] == b['targets'][k] else '  <== CHANGED'
        print('   %-32s base=%s eco=%s%s'
              % (k, b['targets'][k], r['targets'][k], flag))
    print(' U18: base %d/8  eco %d/8' % (b['u18_connected'], r['u18_connected']))
    print(' control/sense regressions:', ctl_reg or 'none')
    print(' ratsnest: base %d  eco %d  (%+d)'
          % (b['ratsnest'], r['ratsnest'], r['ratsnest'] - b['ratsnest']))
    print(' DRC baseline:', dict(sorted(cb.items())))
    print(' DRC eco     :', dict(sorted(cr.items())))
    print(' new DRC classes:', newdrc or 'NONE')
    PASS = all(v.values())
    print('=== VERDICT ===')
    for k, val in v.items():
        print('  [%s] %s' % ('PASS' if val else 'FAIL', k))
    print('  OVERALL:', 'PASS' if PASS else 'FAIL')
    out = dict(tag=tag, eco=os.path.relpath(eco, SP),
               baseline=os.path.relpath(base, SP),
               pr40_baseline=b['targets_true'], pr40_eco=r['targets_true'],
               u18_base=b['u18_connected'], u18_eco=r['u18_connected'],
               ratsnest_base=b['ratsnest'], ratsnest_eco=r['ratsnest'],
               drc_baseline=dict(sorted(cb.items())),
               drc_eco=dict(sorted(cr.items())), new_drc=newdrc,
               control_regressions=ctl_reg, verdict=v, PASS=PASS)
    json.dump(out, open(os.path.join(SP, 'place_002z',
                                     'bridge_gates_003d_%s.json' % tag), 'w'),
              indent=1)
    return 0 if PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
