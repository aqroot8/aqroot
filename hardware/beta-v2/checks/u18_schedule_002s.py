# -*- coding: utf-8 -*-
"""FBV2-P2-002S sections 8-11 -- the COORDINATED U18 CONTROL ESCAPE.

Three whole-block orderings have now been measured and each merely moved the
casualty: trunk-first lost `U18.2`/`U18.3`/`U18.7`, Kelvin-first lost four
control pins, controls-first lost `U18.6` and the sense pads.  Section 8 stops
asking "which global order" and asks the narrower question that actually
decides the pin field: IN WHAT ORDER DO U18's OWN PINS LEAVE?

Section 7 established the premise this rests on.  On a bare six-layer board at
the frozen placement, `U18.6` has FIVE escape directions at 0.25 mm, a reachable
via site at every ruled geometry, and routes to `R80.2` in 10.269 mm and to
`Q4.3` in 24.094 mm.  So LTC_SHDN is not intrinsically trapped - it is sealed by
control copper laid before it, and the schedule is the variable.

This screen is deliberately CHEAP: it lays only the U18 control set and its
downstream links, in a given pin order, and reports which functional nets end up
whole.  It is a SCREEN, not a qualification - no per-connection DRC gate runs
here, so the winner is re-measured on the real prefix with the gate before any
claim is made about it.
"""
import itertools
import json
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import path_role_util as RU
import qrouter as QR
import battery_route_plan as PL
import pcbnew

N = PL.N
CP, CT_S, CT_W = 200000, 200000, 300000

# The six non-Kelvin functional pins of U18's field, and what each must reach
# first.  The order of THIS list is the variable under test.
PINFIELD = {
    '1':  (N + 'BAT_RAW', 'U18.1', 'R77.1', [PL.W_SENSE]),
    '2':  (N + 'LTC_UV', 'U18.2', 'R79.2', PL.LAD_SIG),
    '3':  (N + 'LTC_OV', 'U18.3', 'R77.2', PL.LAD_SIG),
    '6':  (N + 'LTC_SHDN', 'U18.6', 'R80.2', PL.LAD_SIG),
    '7':  (N + 'LTC4368_FAULT_N', 'U18.7', 'R81.2', PL.LAD_SIG),
    '10': (N + 'LTC_GATE', 'U18.10', 'R76.1', PL.LAD_SIG),
}

# Everything downstream of the pin field, in its standing plan order.
DOWNSTREAM = [
    (N + 'Q3_CS', 'Q3.3', 'Q3.1', PL.LAD_SIG),
    (N + 'LTC_GATE', 'Q3.2', 'Q3.4', PL.LAD_SIG),
    (N + 'LTC_GATE', 'Q2.2', 'Q2.4', PL.LAD_SIG),
    (N + 'LTC_GATE', 'Q3.2', 'Q2.2', PL.LAD_SIG),
    (N + 'LTC_GATE', 'U18.10', 'Q3.4', PL.LAD_SIG),
    (N + 'LTC_OV', 'R77.2', 'R78.1', PL.LAD_SIG),
    (N + 'LTC_SHDN', 'U18.6', 'Q4.3', PL.LAD_SIG),
    (N + 'LTC4368_FAULT_N', 'R81.2', 'R82.1', PL.LAD_SIG),
    (N + 'LTC4368_FAULT_N', 'R82.1', 'Q9.1', PL.LAD_SIG),
]

# LTC_OV is the one net section 9 makes an absolute: B.Cu, zero vias.
BCU_ONLY = frozenset((N + 'LTC_OV',))

CHECK = {
    'VIN': (N + 'BAT_RAW', ('U18.1', 'R77.1')),
    'LTC_UV': (N + 'LTC_UV', ('U18.2', 'R79.2')),
    'LTC_OV': (N + 'LTC_OV', ('U18.3', 'R77.2', 'R78.1')),
    'LTC_SHDN': (N + 'LTC_SHDN', ('U18.6', 'R80.2', 'Q4.3')),
    'FAULT_N': (N + 'LTC4368_FAULT_N', ('U18.7', 'R81.2', 'R82.1', 'Q9.1')),
    'LTC_GATE': (N + 'LTC_GATE',
                 ('U18.10', 'R76.1', 'Q3.2', 'Q3.4', 'Q2.2', 'Q2.4')),
    'Q3_CS': (N + 'Q3_CS', ('Q3.1', 'Q3.3')),
}


def board(work, tag, spec):
    pcb = RU.fresh(work, tag)
    b = pcbnew.LoadBoard(pcb)
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    for r, v in spec['moves'].items():
        f = fp[r]
        f.SetPosition(pcbnew.VECTOR2I(int(round(v[0] * 1e6)),
                                      int(round(v[1] * 1e6))))
        f.SetOrientationDegrees(v[2])
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(pcb)
    qb = QR.QBoard(pcb)
    qb.wide_nets = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                             'BAT_MID', 'BAT_SENSE',
                                             'BAT_PROTECTED_P'))
    return qb


def joined(qb, a, c):
    qb.b.BuildConnectivity()
    cn = qb.b.GetConnectivity()
    pp = {}
    for f in qb.b.GetFootprints():
        for q in f.Pads():
            pp[f.GetReference() + '.' + q.GetNumber()] = q
    if a not in pp or c not in pp:
        return False
    g = {str(i.m_Uuid.AsString()) for i in cn.GetConnectedItems(pp[a])}
    return str(pp[c].m_Uuid.AsString()) in g


def lay(qb, pads, net, a, b_, ladder):
    pa, pb = pads.get(a), pads.get(b_)
    if pa is None or pb is None:
        return False
    if joined(qb, a, b_):
        return True
    m = qb.mark()
    for w in ladder:
        r = QR.connect_role(qb, net, pa, pb, 'B', w, CP, CT_S)
        if r['ok'] and joined(qb, a, b_):
            return True
        qb.revert(m)
    if net in BCU_ONLY:
        return False                       # section 9: LTC_OV is B.Cu, no vias
    for lyr in ('I2', 'I3', 'F'):
        r = QR.connect_hop(qb, net, pa, pb, PL.LAD_SIG[0], CP, CT_S, far=lyr,
                           via_dia=350000, via_drill=200000)
        if r['ok'] and joined(qb, a, b_):
            return True
        qb.revert(m)
    return False


def screen(work, tag, spec, order):
    qb = board(work, tag, spec)
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(ref, p)
    # Q3's POFV escape goes first wherever it appears: it is the one pad in the
    # block with exactly one option in the entire design.
    sp = PL.POFV_Q3[(N + 'Q3_CS', 'Q3.3', 'Q3.1')]
    QR.connect_pofv(qb, N + 'Q3_CS', pads['Q3.3'], pads['Q3.1'],
                    PL.LAD_SIG[0], CP, CT_S, inner=sp['inner'],
                    via_dia=sp['via'][0], via_drill=sp['via'][1])
    for pin in order:
        net, a, b_, lad = PINFIELD[pin]
        lay(qb, pads, net, a, b_, lad)
    for (net, a, b_, lad) in DOWNSTREAM:
        lay(qb, pads, net, a, b_, lad)
    qb.save()
    out = {}
    for nm, (net, refs) in CHECK.items():
        out[nm] = all(joined(qb, refs[0], r) for r in refs[1:])
    out['U18'] = sum(1 for pin in PINFIELD
                     if joined(qb, PINFIELD[pin][1], PINFIELD[pin][2]))
    return out


def main():
    work = os.path.join(SP, 'w')
    spec = json.load(open(os.path.join(SP, 'cand_002p', 'Q02.json')))
    base = ['1', '2', '3', '6', '7', '10']
    # Twelve schedules, and every one of them is an argument.  Section 10 asks
    # for at least one with LTC_SHDN early, because section 7 proved SHDN is
    # sealed by its neighbours rather than trapped by geometry.
    SCHEDULES = [
        ('plan order',            ['10', '1', '7', '6', '3', '2']),
        ('SHDN first',            ['6', '10', '7', '1', '3', '2']),
        ('SHDN then GATE',        ['6', '10', '1', '7', '3', '2']),
        ('SHDN, OV, UV first',    ['6', '3', '2', '10', '7', '1']),
        ('outer pins first',      ['1', '10', '6', '7', '3', '2']),
        ('inner pins first',      ['3', '2', '7', '6', '10', '1']),
        ('trip network first',    ['6', '7', '10', '3', '2', '1']),
        ('OV first',              ['3', '6', '2', '7', '10', '1']),
        ('GATE last',             ['6', '7', '3', '2', '1', '10']),
        ('VIN last',              ['6', '10', '7', '3', '2', '1']),
        ('ascending',             base),
        ('descending',            list(reversed(base))),
    ]
    print('U18 COORDINATED CONTROL ESCAPE -- %d schedules, frozen placement'
          % len(SCHEDULES))
    print('  %-22s %-4s %s' % ('schedule', 'U18', '  '.join(sorted(CHECK))))
    best = []
    for k, (nm, order) in enumerate(SCHEDULES):
        r = screen(work, 'SCH%02d' % k, spec, order)
        line = '  '.join(('Y ' if r[c] else '. ').ljust(len(c))
                         for c in sorted(CHECK))
        print('  %-22s %d/6  %s' % (nm, r['U18'], line))
        sys.stdout.flush()
        best.append((sum(1 for c in CHECK if r[c]), r['U18'], nm, order, r))
    best.sort(reverse=True)
    print('')
    top = best[0]
    print('BEST: %s -- %d of %d functional nets whole, U18 %d/6'
          % (top[2], top[0], len(CHECK), top[1]))
    print('  order: %s' % ' '.join('U18.' + p for p in top[3]))
    json.dump(dict(schedule=top[2], order=top[3], nets=top[4]),
              open(os.path.join(SP, 'u18_schedule_002s.json'), 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
