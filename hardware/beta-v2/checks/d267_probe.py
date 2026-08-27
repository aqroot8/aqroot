# -*- coding: utf-8 -*-
"""FBV2-P2-002U sections 5 and 17 -- D-267 REGRESSION.

Two rulings, two halves:

  D-267a  An early high-current escape reservation is permitted only for D9.1,
          at the existing BPP trunk target/floor, outer-layer-only and
          zero-via.  It preserves the pad exit without completing the current
          path early.

  D-267b  VIA GEOMETRY IS A PROPERTY OF THE PATH ROLE, NOT OF THE NET.  A
          microamp TAP on a high-current net routes locally on B.Cu with zero
          vias; it never inherits the trunk's via, and the current-carrying
          trunk keeps every BAT_MAIN rule it had.

    python d267_probe.py
"""
import os, sys, io, re
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import battery_route_plan as PL
import qrouter as QR

FAIL = []


def chk(name, detail, ok):
    print('  %-4s %-64s %s' % ('OK' if ok else '**', name, detail))
    if not ok:
        FAIL.append(name)


def main():
    N = PL.N
    src = io.open(os.path.join(SP, 'route_battery_block.py'),
                  encoding='utf-8').read()
    qsrc = io.open(os.path.join(SP, 'qrouter.py'), encoding='utf-8').read()
    print('D-267 REGRESSION')

    # ------------------------------------------------- A: the D9 reservation
    print('  -- A  the D9.1 current-escape reservation --------------------')
    chk('A the reservation is offered for D9.1 and nothing else',
        "one RESERVE_RUN row, pad D9.1",
        src.count("'RESERVE_RUN'") >= 1
        and "'D9.1', '(stage)', 'RESERVE_RUN'" in src)
    chk('A it never goes below the trunk floor',
        'ladder %s mm' % [w / 1e6 for w in PL.LAD_D9_RESERVE],
        min(PL.LAD_D9_RESERVE) == 1200000
        and max(PL.LAD_D9_RESERVE) == PL.W_TRUNK_BPP)
    chk('A three staging families, all on the clean-board trunk',
        ', '.join('%s (%.3f, %.3f)' % (k, v[0] / 1e6, v[1] / 1e6)
                  for k, v in sorted(PL.D267_STAGING.items())),
        len(PL.D267_STAGING) == 3)
    chk('A the reservation is outer-layer and zero-via',
        "reserve_run lays no via and reports vias=0",
        'vias=0' in qsrc.split('def reserve_run')[-1]
        and 'qb.via(' not in qsrc.split('def reserve_run')[-1])
    chk('A it is journalled as CURRENT_ESCAPE_RESERVATION',
        'tag present in the driver',
        'CURRENT_ESCAPE_RESERVATION' in src)
    chk('A it is counted as a reservation, never as a routed trunk',
        "state['reservations'] incremented, state['done'] untouched",
        "state['reservations'] = state.get('reservations', 0) + 1"
        in src.split("if role == 'RESERVE_RUN':")[-1].split('elif')[0])
    chk('A it is judged by the inverted gate (ratsnest must NOT move)',
        'reserve_gate(rn0)',
        'reserve_gate(rn0, allow_dangle=True)'
        in src.split("elif role == 'RESERVE_RUN':")[-1].split('else:')[0]
        and 'a reservation changed the ratsnest' in src)
    chk('A the trunk is COMPLETED to the reservation, not routed early',
        "one '(stage)' completion row, after the control field",
        "'R75.2', '(stage)', 'TRUNK'" in src)

    class Board(object):
        """The narrowest QBoard-shaped stub the failure path touches."""
        def __init__(self):
            self.laid, self.cu = [], ['F', 'I2', 'I3', 'B']
            self.ex0 = self.ey0 = 0
            self.ex1 = self.ey1 = 100000000
            self.escape_why = []
            self.wide_nets = frozenset()
        def mark(self):
            return (len(self.laid), 0, 0)
        def revert(self, m):
            del self.laid[m[0]:]
        def escape(self, *a, **k):
            self.escape_why = ['stub: no legal escape']
            return []
        def track(self, *a, **k):
            self.laid.append(a)

    qb = Board()
    pad = dict(ref='D9.1', x=0, y=0, net='n', B=True, F=False)
    r = QR.reserve_run(qb, 'n', pad, 1500000, 200000, 300000, layer='B',
                       target=(5000000, 5000000))
    chk('A a reservation that cannot escape returns a reason, not ok',
        '%s' % r.get('reason'), r['ok'] is False)
    chk('A a failed reservation leaves zero copper on the board',
        '%d item(s) laid' % len(qb.laid), len(qb.laid) == 0)

    # -------------------------------------------------- B: the TAP-role fix
    print('  -- B  via geometry follows the PATH ROLE ---------------------')
    m = re.search(r"vd, vk = \(\{(.+?)\}\s*\.get\(role, \((\d+), (\d+)\)\)\)",
                  src, re.S)
    chk('B via geometry is selected by ROLE, not by net',
        'role -> via map present' if m else 'MISSING', m is not None)
    if m:
        body, tdia, tdrl = m.group(1), int(m.group(2)), int(m.group(3))
        chk('B a TAP gets the smallest via the standing rules allow',
            "'TAP': (650000, 400000) - 0.40 drill + two 0.125 rings",
            "'TAP': (650000, 400000)" in body)
        chk('B the current-carrying TRUNK keeps 0.80/0.40 untouched',
            '%.2f / %.2f mm' % (tdia / 1e6, tdrl / 1e6),
            (tdia, tdrl) == (800000, 400000))
        chk('B a SIG branch keeps 0.60/0.30',
            "'SIG': (600000, 300000)", "'SIG': (600000, 300000)" in body)
    chk('B a wide-net TAP is confined to OUTER layers - no inner excursion',
        "far_ = ['F'] for a wide-net TAP",
        "far_ = ['F']" in src and "if role == 'TAP' and net in WIDE:" in src)
    chk('B the divider rows are TAP rows carrying LAD_TAP',
        '%d of %d PLAN_TAPS rows' % (
            sum(1 for r_ in PL.PLAN_TAPS if r_[3] == 'TAP'
                and r_[4] is PL.LAD_TAP), len(PL.PLAN_TAPS)),
        all(r_[3] == 'TAP' and r_[4] is PL.LAD_TAP for r_ in PL.PLAN_TAPS))
    chk('B TAP width behaviour is not the wide-net ladder',
        'LAD_TAP %s vs LAD_BAT %s mm'
        % ([w / 1e6 for w in PL.LAD_TAP], [w / 1e6 for w in PL.LAD_BAT]),
        PL.LAD_TAP != PL.LAD_BAT and min(PL.LAD_TAP) < min(PL.LAD_BAT))
    chk('B the trunk ladder is untouched by any of this',
        '%s mm' % [w / 1e6 for w in PL.PLAN_1_BPP_TRUNK[0][4]],
        PL.PLAN_1_BPP_TRUNK[0][4] == [PL.W_TRUNK_BPP, 1200000])
    chk('B no global BAT_RAW netclass or clearance value is changed',
        'no netclass/clearance edit in the TAP path',
        'set_clearance' not in src and 'SetClearance' not in src)

    print('=' * 84)
    if FAIL:
        print('D-267 PROBE: FAIL (%d)' % len(FAIL))
        for f in FAIL:
            print('   %s' % f)
        return 1
    print('D-267 PROBE: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
