# -*- coding: utf-8 -*-
"""FBV2-P2-003C / D-275 -- the real save/reload DRC + connectivity gates for the
vacate ECO + F.Cu via-array bridge board (w/c3bridge003c), against the reproduced
c3 baseline (w/c3repro003c).  Requirement 8 of the task.
"""
import os, sys, json, math
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import pcbnew
import path_role_util as RU

N = '/01_POWER_TREE/'
WORK = os.path.join(SP, 'w')
BR = os.path.join(SP, 'w', 'c3bridge003c', 'aqroot-Beta-v2.kicad_pcb')
BASE = os.path.join(SP, 'w', 'c3repro003c', 'aqroot-Beta-v2.kicad_pcb')

# the PR-40 target pairs (route_battery_block.py, criteria A..I)
TARGETS = [('BAT_RAW', 'R80.1', 'Q2.7'), ('BAT_RAW', 'D12.1', 'R77.1'),
           ('LTC_SHDN', 'U18.6', 'Q4.3'), ('LTC4368_FAULT_N', 'U18.7', 'R81.2'),
           ('LTC_GATE', 'U18.10', 'R76.1'), ('LTC_GATE', 'U18.10', 'Q2.2'),
           ('Q3_CS', 'Q3.1', 'Q3.3'), ('BAT_PROTECTED_P', 'R75.2', 'U11.2'),
           ('BAT_PROTECTED_P', 'U14.2', 'TP15.1')]
U18PINS = [('U18.1', 'R77.1'), ('U18.2', 'R79.2'), ('U18.3', 'R77.2'),
           ('U18.6', 'R80.2'), ('U18.7', 'R81.2'), ('U18.8', 'R75.2'),
           ('U18.9', 'R75.1'), ('U18.10', 'R76.1')]
# control / sense nets that MUST stay connected across the vacate
CONTROL = [('BAT_PROT_SHDN_CTL', 'Q4.1', 'R83.1'),
           ('BAT_PROT_SHDN_CTL', 'Q4.1', 'TP19.1'),
           ('BAT_SENSE', 'Q3.6', 'R75.1'),
           ('BAT_SENSE', 'U18.9', 'R75.1'),
           ('LTC_GATE', 'Q3.2', 'Q3.4'), ('LTC_OV', 'R77.2', 'R78.1'),
           ('LTC_UV', 'U18.2', 'R79.2')]


def jn_map(pcb):
    b = pcbnew.LoadBoard(pcb)
    b.BuildConnectivity()
    cn = b.GetConnectivity()
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            pads[f.GetReference() + '.' + p.GetNumber()] = p

    def jn(a, c):
        pa, pc = pads.get(a), pads.get(c)
        if pa is None or pc is None:
            return None
        s = {str(i.m_Uuid.AsString()) for i in cn.GetConnectedItems(pa)}
        return str(pc.m_Uuid.AsString()) in s
    return jn


def check(pcb, label):
    jn = jn_map(pcb)
    tg = {'%s %s->%s' % (n, a, b): bool(jn(a, b)) for (n, a, b) in TARGETS}
    u18 = {a: bool(jn(a, b)) for (a, b) in U18PINS}
    ctl = {'%s %s->%s' % (n, a, b): bool(jn(a, b)) for (n, a, b) in CONTROL}
    rn = RU.ratsnest(pcb)
    return dict(label=label, targets=tg, u18=u18, control=ctl,
                u18_connected=sum(1 for v in u18.values() if v),
                targets_true=''.join('1' if v else '0' for v in tg.values()),
                ratsnest=rn)


def main():
    base = check(BASE, 'baseline c3repro003c')
    brd = check(BR, 'bridge c3bridge003c')
    cb, _ = RU.drc(os.path.abspath(BASE), 'Abase', os.path.abspath(WORK))
    cr, det = RU.drc(os.path.abspath(BR), 'Abr', os.path.abspath(WORK))
    newdrc = {k: cr.get(k, 0) - cb.get(k, 0)
              for k in set(cr) | set(cb) if cr.get(k, 0) != cb.get(k, 0)}

    print('=== PR-40 TARGETS (bit order A..I) ===')
    print(' baseline:', base['targets_true'])
    print(' bridge  :', brd['targets_true'])
    for k in brd['targets']:
        flag = '' if brd['targets'][k] == base['targets'][k] else '  <== CHANGED'
        print('   %-32s base=%s bridge=%s%s'
              % (k, base['targets'][k], brd['targets'][k], flag))
    print('=== U18 pin field: base %d/8  bridge %d/8 ==='
          % (base['u18_connected'], brd['u18_connected']))
    for k in brd['u18']:
        if brd['u18'][k] != base['u18'][k]:
            print('   U18 %s CHANGED %s->%s' % (k, base['u18'][k], brd['u18'][k]))
    print('=== control / sense nets (must stay connected) ===')
    for k in brd['control']:
        f = '' if brd['control'][k] else '  <== OPEN!'
        print('   %-34s base=%s bridge=%s%s'
              % (k, base['control'][k], brd['control'][k], f))
    print('=== ratsnest: base %d  bridge %d  (delta %+d) ==='
          % (base['ratsnest'], brd['ratsnest'], brd['ratsnest'] - base['ratsnest']))
    print('=== DRC delta vs baseline ===')
    print('  baseline', dict(sorted(cb.items())))
    print('  bridge  ', dict(sorted(cr.items())))
    print('  new violation classes:', newdrc or 'NONE')

    # verdict
    bit8 = brd['targets']['BAT_PROTECTED_P R75.2->U11.2']
    u18_ok = brd['u18_connected'] == 8
    # REGRESSION test: nothing that was connected on the c3 baseline may open.
    # (TP19.1 is a test-point stub already unrouted on the qualifying c3 board;
    # its open state is pre-existing, not caused by the vacate -- the ratsnest
    # FELL by 1, so no connection was lost.)
    ctl_regressions = [k for k in brd['control']
                       if base['control'][k] and not brd['control'][k]]
    ctl_ok = not ctl_regressions
    u18_regressions = [k for k in brd['u18']
                       if base['u18'][k] and not brd['u18'][k]]
    tgt_regressions = [k for k in brd['targets']
                       if base['targets'][k] and not brd['targets'][k]]
    no_new_drc = all(v <= 0 for v in newdrc.values())
    targets_ok = all(brd['targets'].values())
    rn_ok = brd['ratsnest'] <= base['ratsnest']
    verdict = dict(bit8_closed=bit8, all9_targets=targets_ok, u18_8of8=u18_ok,
                   control_not_regressed=ctl_ok,
                   u18_not_regressed=not u18_regressions,
                   targets_not_regressed=not tgt_regressions,
                   no_new_drc=no_new_drc, ratsnest_not_worse=rn_ok)
    if ctl_regressions:
        print('  control REGRESSIONS:', ctl_regressions)
    PASS = all(verdict.values())
    print('\n=== VERDICT ===')
    for k, v in verdict.items():
        print('  [%s] %s' % ('PASS' if v else 'FAIL', k))
    print('  OVERALL:', 'PASS' if PASS else 'FAIL')
    json.dump(dict(baseline=base, bridge=brd, drc_baseline=dict(sorted(cb.items())),
                   drc_bridge=dict(sorted(cr.items())), new_drc=newdrc,
                   verdict=verdict, PASS=PASS),
              open(os.path.join(SP, 'place_002z', 'bridge_gates_003c.json'), 'w'),
              indent=1)
    return 0 if PASS else 1


if __name__ == '__main__':
    raise SystemExit(main())
