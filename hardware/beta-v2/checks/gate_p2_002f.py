# -*- coding: utf-8 -*-
"""FBV2-P2-002F section 12 -- THE ESCAPE-ONLY PROOF GATE.

Run against a candidate placement BEFORE a single full connection is routed.
If this fails, section 12 says stop: do not run the router, do not commit the
placement, report the failed geometry.

Every item is measured against the real qrouter obstacle model at the rule
minimum the routing plan actually asks for, and section 3C is tested
explicitly: every escape is laid SIMULTANEOUSLY and every pad must still have
one afterwards, so no escape depends on another signal already being routed.

    "<KICAD>/bin/python.exe" gate_p2_002f.py <scratch.kicad_pcb>
"""
import os, sys, json, math, time, faulthandler
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import qrouter as QR
import battery_route_plan as PL
import path_role_util as RU

N = PL.N
CP, CT_W, CT_S = 200000, 300000, 200000
WIDE = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                 'BAT_SENSE', 'BAT_PROTECTED_P'))

# ref -> (rule minimum, clearance class).  The minima are battery_route_plan's
# own ladders, not a number invented here.
NEED = {
    'U18.1': (PL.W_SENSE, CT_W), 'U18.2': (150000, CT_S),
    'U18.3': (150000, CT_S), 'U18.6': (150000, CT_S),
    'U18.7': (150000, CT_S), 'U18.8': (PL.W_SENSE, CT_W),
    'U18.9': (PL.W_SENSE, CT_W), 'U18.10': (150000, CT_S),
    'Q3.1': (150000, CT_S), 'Q3.2': (150000, CT_S),
    'Q3.3': (150000, CT_S), 'Q3.4': (150000, CT_S),
    'Q2.1': (150000, CT_S), 'Q2.2': (150000, CT_S),
    'Q2.3': (150000, CT_S), 'Q2.4': (150000, CT_S),
    'U14.2': (PL.W_U14, CT_W), 'U14.3': (PL.W_U14, CT_W),
    'U19.1': (150000, CT_S), 'U19.2': (150000, CT_S),
    'U19.3': (150000, CT_S), 'U19.5': (150000, CT_S),
    'U19.6': (150000, CT_S), 'U19.7': (150000, CT_S),
    'U19.8': (150000, CT_S),
}
# the megohm divider/reference pads of the dead-cell bridge
for _r in range(85, 97):
    for _p in ('1', '2'):
        NEED['R%d.%s' % (_r, _p)] = (150000, CT_S)
NEED['R95.1'] = (150000, CT_S)
NEED['R95.2'] = (150000, CT_S)


def pads_of(qb):
    d = {}
    for (net, ref), p in qb.pads.items():
        d[ref] = p
    return d


def esc(qb, p, w, ct):
    return qb.escape(p, 'B', w, w, CP, ct, 25000, qb.ex0, qb.ey0)


def main():
    faulthandler.enable()
    pcb = [a for a in sys.argv[1:] if a.endswith('.kicad_pcb')]
    pcb = pcb[0] if pcb else None
    if pcb is None:
        print('usage: gate_p2_002f.py <board.kicad_pcb>')
        return 2
    qb = QR.QBoard(pcb)
    qb.wide_nets = WIDE
    P = pads_of(qb)
    rows, fails = [], []

    def chk(name, value, rule, ok):
        rows.append((name, value, rule, ok))
        mark = '' if ok is None else ('  PASS' if ok else '  **FAIL**')
        print('%-34s %-30s %-26s%s' % (name, value, rule, mark))
        if ok is False:
            fails.append(name)

    print('FBV2-P2-002F  SECTION 12 ESCAPE-ONLY PROOF GATE')
    print('board: %s' % pcb)
    print('=' * 120)

    # ------------------------------------------------ 1. per-pad legal escape
    got = {}
    for ref, (w, ct) in sorted(NEED.items()):
        p = P.get(ref)
        if p is None:
            got[ref] = None
            continue
        e = esc(qb, p, w, ct)
        got[ref] = e[0] if e else None

    u18 = ['U18.%s' % k for k in ('1', '2', '3', '6', '7', '8', '9', '10')]
    n18 = sum(1 for r in u18 if got.get(r))
    chk('U18 legal pad escapes', '%d of 8' % n18, '8 of 8 (section 3A)', n18 == 8)
    for r in u18:
        if not got.get(r):
            print('     %s: %s' % (r, '; '.join(qb.escape_why) if qb.escape_why else 'no escape'))

    chk('Q3 LTC_GATE escape (2, 4)',
        '%s / %s' % tuple('%.2f mm' % (got[k]['w'] / 1e6) if got.get(k) else 'NONE'
                          for k in ('Q3.2', 'Q3.4')),
        'both legal (section 5)', bool(got.get('Q3.2') and got.get('Q3.4')))
    chk('Q3_CS escape (1, 3)',
        '%s / %s' % tuple('%.2f mm' % (got[k]['w'] / 1e6) if got.get(k) else 'NONE'
                          for k in ('Q3.1', 'Q3.3')),
        'both legal, or a ruled via', bool(got.get('Q3.1') and got.get('Q3.3')))
    chk('Q2 gate/CS escapes (1..4)',
        '%d of 4' % sum(1 for k in ('Q2.1', 'Q2.2', 'Q2.3', 'Q2.4') if got.get(k)),
        '4 of 4', all(got.get(k) for k in ('Q2.1', 'Q2.2', 'Q2.3', 'Q2.4')))
    chk('U14.2 / U14.3 escape',
        '%s / %s' % tuple('%.3f mm' % (got[k]['w'] / 1e6) if got.get(k) else 'NONE'
                          for k in ('U14.2', 'U14.3')),
        'both legal at 0.15 mm', bool(got.get('U14.2') and got.get('U14.3')))
    comp = ['U19.%s' % k for k in ('1', '2', '3', '5', '6', '7', '8')]
    ncomp = sum(1 for r in comp if got.get(r))
    chk('comparator pins (U19)', '%d of %d' % (ncomp, len(comp)),
        'all legal', ncomp == len(comp))
    hz = [r for r in NEED if r.startswith('R') and int(r[1:].split('.')[0]) >= 85]
    nhz = sum(1 for r in hz if got.get(r))
    chk('megohm bridge pads (R85..R96)', '%d of %d' % (nhz, len(hz)),
        'all legal', nhz == len(hz))
    for r in comp + sorted(hz):
        if not got.get(r):
            print('     %s: NO LEGAL ESCAPE' % r)

    # -------------------------------- 2. R75 trunk / Kelvin coexistence
    for pad, tw, name in (('R75.2', PL.W_TRUNK_BPP, 'R75.2 trunk 1.50 + Kelvin 0.20'),
                          ('R75.1', PL.W_TRUNK_BAT, 'R75.1 trunk 1.00 + Kelvin 0.20')):
        p = P.get(pad)
        et = esc(qb, p, tw, CT_W) if p else None
        ok = False
        if et:
            m = qb.mark()
            qb.track(p['net'], 'B', p['x'], p['y'], et[0]['x'], et[0]['y'], tw)
            ek = esc(qb, p, PL.W_SENSE, CT_W)
            ok = bool(ek)
            qb.revert(m)
        chk(name, ('trunk %.2f + kelvin %s'
                   % (et[0]['w'] / 1e6, 'OK' if ok else 'NONE')) if et else 'no trunk escape',
            'both coexist (section 12)', ok)

    # ------------------------------------------------ 3. the U11.2 flare
    net = N + 'BAT_PROTECTED_P'
    m = qb.mark()
    eD = esc(qb, P['D9.1'], PL.W_TRUNK_BPP, CT_W)
    regs = {}
    if eD:
        seed = (eD[0]['x'], eD[0]['y'])
        for w in (300000, 400000, 600000, 800000, 1000000, 1200000, PL.W_TRUNK_BPP):
            regs[w] = qb.free_region('B', net, w, CP, CT_W, 50000, seed,
                                     qb.ex0 - 1000000, qb.ey0 - 1000000,
                                     qb.ex1 + 1000000, qb.ey1 + 1000000)
    f = qb.flare(net, P['U11.2'], 'B', PL.W_TRUNK_BPP, PL.W_SENSE, CP, CT_W,
                 25000, region=regs)
    qb.revert(m)
    ok_f = bool(f) and f['neck_len'] <= 0.75
    chk('U11.2 flare',
        ('%.3f mm, neck %.3f mm at 0.20' % (f['total'], f['neck_len']))
        if f else 'NONE', 'monotonic, neck <= 0.75 mm', ok_f)

    # ---------- 4. SECTION 3C: every escape laid SIMULTANEOUSLY, none lost
    m = qb.mark()
    laid = 0
    for ref, e in sorted(got.items()):
        if e is None:
            continue
        p = P[ref]
        qb.track(p['net'], 'B', p['x'], p['y'], e['x'], e['y'], e['w'])
        laid += 1
    lost = []
    for ref, e in sorted(got.items()):
        if e is None:
            continue
        if not esc(qb, P[ref], NEED[ref][0], NEED[ref][1]):
            lost.append(ref)
    qb.revert(m)
    chk('escapes laid simultaneously', '%d laid, %d lost' % (laid, len(lost)),
        '0 lost (section 3C)', not lost)
    if lost:
        print('     lost: %s' % ', '.join(lost))

    print('=' * 120)
    print('SECTION 12 GATE: %s   (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails), '' if len(fails) == 1 else 's'))
    for f_ in fails:
        print('   FAILED: %s' % f_)
    json.dump(dict(pcb=pcb, rows=rows,
                   escapes={k: (round(v['w'] / 1e6, 3) if v else None)
                            for k, v in got.items()},
                   lost=lost, fails=fails),
              open(os.path.join(SP, 'gate_002f.json'), 'w'), indent=1)
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
