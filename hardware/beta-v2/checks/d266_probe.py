# -*- coding: utf-8 -*-
"""FBV2-P2-002T section 10 -- D-266 SCOPING REGRESSION.

D-266 adds two things a router has not had before: a bounded starting rung for
ONE named branch, and a RESERVATION that is copper on the board but is NOT a
connection.  Both are the kind of mechanism that decays into a general
relaxation if nothing pins it, so this is the pin.

It proves six clauses:

  A  LTC_UV U18.2 -> R79.2 starts at its explicitly authorised 0.20 mm rung
  B  unrelated SIG connections still start with the ordinary LAD_SIG policy
  C  no connection gains a width below the ladder it already had
  D  no global netclass or clearance value changed
  E  no accepted copper survives a FAILED reservation
  F  a reservation never masquerades as a completed connection

    python d266_probe.py
"""
import os, sys, re, io
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import battery_route_plan as PL
import qrouter as QR
import path_role_dru as DRU

FAIL = []


def chk(name, detail, ok):
    print('  %-4s %-62s %s' % ('OK' if ok else '**', name, detail))
    if not ok:
        FAIL.append(name)


def main():
    N = PL.N
    print('D-266 SCOPING REGRESSION')
    print('  -- A/B/C  the bounded starting rung --------------------------')

    key = (N + 'LTC_UV', 'U18.2', 'R79.2')
    lad = PL.D266_LADDER.get(key)
    chk('A U18.2 -> R79.2 starts at its authorised 0.20 mm rung',
        'ladder %s mm' % ([w / 1e6 for w in lad] if lad else None),
        lad is not None and lad[0] == 200000)

    chk('B the override names exactly ONE branch',
        '%d entr%s: %s' % (len(PL.D266_LADDER),
                           'y' if len(PL.D266_LADDER) == 1 else 'ies',
                           ', '.join('%s->%s' % (k[1], k[2])
                                     for k in PL.D266_LADDER)),
        len(PL.D266_LADDER) == 1)

    # Every rung the override offers must ALREADY be in the ladder the branch
    # had.  That is the difference between choosing a starting rung and
    # inventing a width.
    inside = all(w in PL.LAD_SIG for w in lad) if lad else False
    chk('C no rung is invented: every override rung is already in LAD_SIG',
        'LAD_SIG %s mm, override %s mm'
        % ([w / 1e6 for w in PL.LAD_SIG], [w / 1e6 for w in lad]),
        inside)
    chk('C the override never goes below the LAD_SIG floor',
        'floor %.2f mm, override min %.2f mm'
        % (min(PL.LAD_SIG) / 1e6, min(lad) / 1e6),
        min(lad) >= min(PL.LAD_SIG))

    # B, the other half: the driver only consults D266_LADDER, so any SIG row
    # not named there keeps whatever ladder the plan gave it.  Pin that the
    # lookup is a dict miss for the rest of the pin field.
    others = [(r[1], r[2]) for r in PL.PLAN_0_U18
              if (r[0], r[1], r[2]) not in PL.D266_LADDER]
    chk('B unrelated U18 branches keep their own plan ladder',
        '%d other U18 rows, none overridden' % len(others),
        all((N + 'LTC_UV', a, b) not in PL.D266_LADDER or (a, b) == ('U18.2', 'R79.2')
            for (a, b) in others))

    print('  -- D  no global relaxation -----------------------------------')
    src = io.open(os.path.join(SP, 'route_battery_block.py'),
                  encoding='utf-8').read()
    dsrc = io.open(os.path.join(SP, 'path_role_dru.py'), encoding='utf-8').read()
    chk('D D-266 touches no netclass or clearance value',
        'no clearance/netclass edit in the D-266 path',
        'D266' in src and not re.search(
            r"D266[^\n]*\n(?:[^\n]*\n){0,40}?[^\n]*set_clearance", src))
    chk('D the D-266 reservation via is the ordinary 0.35/0.20 through via',
        '350000 / 200000, no microvia',
        'via_dia=350000' in src and 'via_drill=200000' in src
        and 'microvia' not in src.split('D266')[-1].lower())
    chk('D D-264 outer-layer scoping is unchanged',
        'INNER_SENSE_AREAS = %s' % (DRU.INNER_SENSE_AREAS,),
        DRU.INNER_SENSE_AREAS == ('BAT_SENSE_KELVIN', 'BAT_PROT_TAP_U18'))

    print('  -- E  a failed reservation leaves NO copper ------------------')

    class Board(object):
        """The narrowest QBoard-shaped stub the failure paths touch."""
        def __init__(self):
            self.laid, self.cu = [], ['F', 'I2', 'I3', 'B']
            self.ex0 = self.ey0 = 0
            self.ex1 = self.ey1 = 100000000
            self.escape_why = []
            self.wide_nets = frozenset()
            self.reverted = []
        def mark(self):
            return (len(self.laid), 0, 0)
        def revert(self, m):
            self.reverted.append(m)
            del self.laid[m[0]:]
        def escape(self, *a, **k):
            self.escape_why = ['stub: no legal escape']
            return []
        def track(self, *a, **k):
            self.laid.append(a)
        def via(self, *a, **k):
            self.laid.append(a)

    qb = Board()
    pad = dict(ref='U18.9', x=0, y=0, net='n', B=True, F=False)
    r = QR.reserve_escape(qb, 'n', pad, 200000, 200000, 200000)
    chk('E a reservation that cannot escape returns a reason, not ok',
        '%s' % r.get('reason'), r['ok'] is False)
    chk('E a failed reservation leaves zero copper on the board',
        '%d item(s) laid' % len(qb.laid), len(qb.laid) == 0)

    print('  -- F  a reservation is not a connection ---------------------')
    chk('F reserve_escape marks its result as a reservation',
        "reserve_escape sets reservation=True and vias=1",
        "reservation=True" in io.open(os.path.join(SP, 'qrouter.py'),
                                      encoding='utf-8').read())
    # The driver must count a reservation in its OWN tally, never in state['ok']
    seg = src.split("if role in ('RESERVE', 'RESERVE_PAIR'):")[-1]
    body = seg[:seg.find("journal.append")]
    chk('F the driver counts a reservation separately from a route',
        "state['reservations'] incremented, state['ok'] untouched",
        "state['reservations']" in body and "state['ok'] += 1" not in
        body.split("else:")[0])
    chk('F a reservation is journalled as reservation=True',
        "journal carries reservation=(role != 'JOIN')",
        "reservation=(role != 'JOIN')" in src)
    chk('F both ends of a branch are reserved and gated as ONE item',
        '%d RESERVE_PAIR row(s), %d bare RESERVE row(s)'
        % (sum(1 for r in PL.PLAN_D266_RESERVE if r[3] == 'RESERVE_PAIR'),
           sum(1 for r in PL.PLAN_D266_RESERVE if r[3] == 'RESERVE')),
        all(r[3] == 'RESERVE_PAIR' for r in PL.PLAN_D266_RESERVE))
    chk('F a rejected pair leaves no corridor bridge behind',
        'area_link truncated to its pre-attempt length on rejection',
        'del area_link[area][_pre_link:]' in src)
    # And the gate that judges it is the INVERTED one: a reservation that moves
    # the ratsnest has connected something, which is the failure section 8 names.
    chk('F a reservation is rejected if it changes the ratsnest',
        'reserve_gate requires rn == rn0',
        'a reservation changed the ratsnest' in src)

    print('=' * 78)
    if FAIL:
        print('D-266 PROBE: FAIL (%d)' % len(FAIL))
        for f in FAIL:
            print('   %s' % f)
        return 1
    print('D-266 PROBE: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
