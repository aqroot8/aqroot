# -*- coding: utf-8 -*-
"""FBV2-P2-003A / D-273 -- FULL-BUDGET corroboration of the bounded probe.

The bounded probe (``long_corridor_003a_bounded.py``) rejects each long family
either at the R75.2 escape (1.50 mm: NO_LEGAL_ESCAPE) or at a 0.25 mm COARSE
reachability prefilter (1.20 mm: COARSE_BLOCKED) -- fast, but a coarse grid can
in principle OVER-block.  So a COARSE_BLOCKED verdict, on its own, is not proof
that no 1.20 mm corridor exists; it is only proof that none exists on the coarse
grid.

This script removes that doubt.  It runs the SAME real obstacle-aware search the
router uses for the trunk (``QR.connect_role``) from R75.2 straight to the
eastern BAT_PROTECTED_P node copper, at the DEFAULT full search budgets
(ASTAR=500000, WAVE=3000) -- no coarse prefilter, no bounded budget.  Each trial
lays real scratch copper and reverts it, under a per-trial wall-clock backstop so
a runaway is recorded as a TIMEOUT (a legitimate non-PASS), never a hang.  This
is the un-bounded search ``long_corridor_003a.py`` attempted, but aimed at only
the four representative node-copper targets instead of a whole-net sample, so it
finishes in minutes.

If every trial returns NO_LEGAL_ESCAPE / NO_PATH under full budgets, the long
outer-B.Cu zero-via route is disproved by the router's own primitive, and the
bounded probe's fast COARSE_BLOCKED verdict is corroborated -- not an artifact.

    python3 long_corridor_003a_corrob.py [board.kicad_pcb] [out.json]
"""
import os, sys, json, time, signal
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import qrouter as QR
import path_role_util as RU
import battery_route_plan as PL

NET = PL.N + 'BAT_PROTECTED_P'
CP, CT = 200000, 300000
W150, W120 = 1500000, 1200000
CAP = 120                      # per-trial wall-clock backstop, seconds

# Four representative points on the eastern node copper (cluster 1): the closest
# west tip, the NE and SE diagonal joins the families targeted, and the centroid.
TARGETS = [
    ('node_west_tip', (38475000, 80325000)),
    ('node_NE_diag',  (46156683, 72656961)),
    ('node_SE_diag',  (41547282, 83637304)),
    ('node_centroid', (58360000, 75080000)),
]


class Timeout(Exception):
    pass


signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(Timeout()))


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        SP, 'w', 'c3repro003a_parent', 'aqroot-Beta-v2.kicad_pcb')
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        SP, 'place_002z', 'long_corridor_003a_corrob.json')
    qb = QR.QBoard(board)
    qb.wide_nets = frozenset(PL.N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                             'BAT_MID', 'BAT_SENSE', 'BAT_PROTECTED_P'))
    src = qb.pads[(NET, 'R75.2')]
    print('board  %s' % board)
    print('R75.2  (%.3f, %.3f)   FULL budgets ASTAR=%d WAVE=%d  (defaults)  cap=%ds'
          % (src['x'] / 1e6, src['y'] / 1e6, QR.ASTAR_BUDGET, QR.WAVE_BUDGET, CAP))
    rec = dict(board=board, astar_budget=QR.ASTAR_BUDGET,
               wave_budget=QR.WAVE_BUDGET, cap_s=CAP, note=(
               'Real full-budget QR.connect_role from R75.2 to node copper; no '
               'coarse prefilter. NO_LEGAL_ESCAPE/NO_PATH at full budget '
               'corroborates the bounded probe COARSE_BLOCKED verdict.'),
               trials=[])
    any_ok = False
    for name, (x, y) in TARGETS:
        for w in (W150, W120):
            anchor = RU.pseudo_pad(NET, x, y, QR)
            anchor['anchor'] = True
            anchor['ref'] = '(node)'
            m = qb.mark()
            t0 = time.time()
            signal.setitimer(signal.ITIMER_REAL, CAP)
            try:
                r = QR.connect_role(qb, NET, src, anchor, 'B', w, CP, CT)
            except Timeout:
                r = dict(ok=False, reason='WALLCLOCK_TIMEOUT_%ds' % CAP)
            except Exception as e:
                r = dict(ok=False, reason='ERROR', why='%s: %s' % (type(e).__name__, e))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            qb.revert(m)
            dt = round(time.time() - t0, 1)
            ok = bool(r.get('ok'))
            any_ok = any_ok or ok
            row = dict(target=name, xy_mm=[round(x / 1e6, 3), round(y / 1e6, 3)],
                       width_mm=w / 1e6, ok=ok, reason=r.get('reason'),
                       mm=round(r.get('mm', 0) or 0, 3), dt=dt)
            rec['trials'].append(row)
            print('   %-14s @%.2f  ok=%s  %-16s mm=%.3f  %.1fs'
                  % (name, w / 1e6, ok, r.get('reason'), row['mm'], dt))
    rec['any_legal_long_corridor'] = any_ok
    json.dump(rec, open(out, 'w'), indent=1)
    print('=' * 72)
    print('ANY legal long corridor at FULL budgets: %s' % ('YES' if any_ok else 'NO'))
    print('wrote %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
