# -*- coding: utf-8 -*-
"""FBV2-P2-003E -- D-277 REGRESSION: the U19.3 N_POL escape is a ROUTE-ORDER
contention, not a geometry defect, and the planar tie-break fixes it.

D-276 named `N_POL U19.3 -> (node) NO_LEGAL_ESCAPE at >= 0.150 mm` (blockers
board_edge / U19.4 / U19.2 / U19.6) as the full-driver Phase-A blocker.  003E
measured the cause and repaired it.  This probe pins every load-bearing clause
so a future edit cannot silently re-open the blocker or convert the measured
route-order fix back into a placement/geometry claim.

  A  INTRINSIC GEOMETRY IS FINE.  On the authoritative board (0 signal tracks,
     U19 at its authoritative site, unchanged by the c3 placement) U19.3 has a
     LEGAL >= 0.150 mm escape.  So cause (A) intrinsic pad/board-edge geometry
     is REFUTED: the pad can leave.

  B  THE CONTENTION IS REAL AND DIRECTIONAL.  U19.2 (REF_POL) and U19.3 (N_POL)
     are the two middle west-row pins, each with ONE lane (east).  Routing
     U19.2 -> TP24.1 FIRST seals U19.3 (freedom -> 0, the exact D-276 fail);
     routing U19.3 -> TP23.1 FIRST leaves U19.2 escapable and BOTH route.  The
     blocker is the order, and the order is asymmetric.

  C  THE FIX IS THE MEASURED PLANAR TIE-BREAK.  Among pins tied on
     (slack, ways-out) with a single lane, the one whose pad->target span
     CONTAINS a tied sibling's pad crosses it and must go LAST.  U19.2's span
     contains U19.3 (crossing 1); U19.3's span does not contain U19.2
     (crossing 0).  So the tie-break routes U19.3 first.

  D  THE FIX IS SCOPED.  A pin with a second way out (crossing term only fires
     at ways-out <= 1) is never reordered by it; the term is a no-op off the
     boxed-single-lane tie.

  E  003C IS UNTOUCHED.  The BAT_PROT_SHDN_CTL vacate + F.Cu bridge decision
     set is not referenced or altered here (bridge_probe_003c is the guard for
     that; this probe never touches it).

    python u19_escape_probe_003e.py
"""
import os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import qrouter as QR
import harness_paths as H
import battery_route_plan as PL

N = PL.N
CP, CT_S = 200000, 200000
AUTH = H.project_file(H.PCBNAME)
REFPOL, NPOL = N + 'REF_POL', N + 'N_POL'

FAIL = []


def chk(name, detail, ok):
    print('  %-4s %-60s %s' % ('OK' if ok else '**', name, detail))
    if not ok:
        FAIL.append(name)


def board():
    return QR.QBoard(AUTH)


def freedom(qb, net, ref, w=150000):
    pad = qb.pads[(net, ref)]
    e = qb.escape(pad, 'B', w, w, CP, CT_S, 25000, qb.ex0, qb.ey0)
    return len(e), (qb.escape_why[0] if not e else '')


def route(qb, net, a, b, ladder=PL.LAD_SIG):
    pa, pb = qb.pads[(net, a)], qb.pads[(net, b)]
    r = None
    for w in ladder:
        r = QR.connect_role(qb, net, pa, pb, 'B', w, CP, CT_S)
        if r['ok']:
            break
    return r


def snap(qb):
    return (len(qb.laid), {L: len(qb.shapes[L]) for L in qb.shapes})


def restore(qb, s):
    nl, shp = s
    for t in qb.laid[nl:]:
        qb.b.Remove(t)
    del qb.laid[nl:]
    for L in qb.shapes:
        del qb.shapes[L][shp[L]:]


def main():
    print('D-277  U19.3 N_POL ESCAPE -- ROUTE-ORDER CONTENTION + PLANAR FIX')

    # ---- A: intrinsic geometry is fine ------------------------------------
    print('  -- A  intrinsic pad/edge geometry (empty authoritative board) --')
    qb = board()
    f3, why3 = freedom(qb, NPOL, 'U19.3')
    chk('A U19.3 has a legal >= 0.150 mm escape on the empty board',
        'freedom %d %s' % (f3, why3), f3 >= 1)
    f2, _ = freedom(qb, REFPOL, 'U19.2')
    chk('A U19.2 (its contending sibling) also escapes on the empty board',
        'freedom %d' % f2, f2 >= 1)
    chk('A both middle west-row pins are SINGLE-LANE (the boxed class)',
        'U19.2=%d U19.3=%d way(s)' % (f2, f3), f2 == 1 and f3 == 1)

    # ---- B: the contention is real and directional ------------------------
    print('  -- B  the route-order contention, measured both ways -----------')
    qb = board()
    r = route(qb, REFPOL, 'TP24.1', 'U19.2')
    fA, whyA = freedom(qb, NPOL, 'U19.3')
    chk('B routing U19.2 FIRST seals U19.3 (reproduces D-276)',
        'REF_POL ok=%s -> U19.3 freedom %d' % (r['ok'], fA), r['ok'] and fA == 0)
    chk('B the seal names U19.2 as a blocker (the D-276 signature)',
        whyA[:70], 'U19.2' in whyA and 'board_edge' in whyA)

    qb = board()
    r1 = route(qb, NPOL, 'TP23.1', 'U19.3')
    fB, _ = freedom(qb, REFPOL, 'U19.2')
    r2 = route(qb, REFPOL, 'TP24.1', 'U19.2')
    chk('B routing U19.3 FIRST leaves U19.2 escapable',
        'N_POL ok=%s -> U19.2 freedom %d' % (r1['ok'], fB), r1['ok'] and fB >= 1)
    chk('B in the swapped order BOTH connections route',
        'N_POL ok=%s  REF_POL ok=%s' % (r1['ok'], r2['ok']), r1['ok'] and r2['ok'])

    # ---- C: the planar tie-break selects the non-crossing pin first -------
    print('  -- C  the planar (pad->target span) tie-break -------------------')
    qb = board()

    def span_contains(net_a, pin_a, tgt_a, net_b, pin_b):
        pa = qb.pads[(net_a, pin_a)]
        ta = qb.pads[(net_a, tgt_a)]
        pb = qb.pads[(net_b, pin_b)]
        x0, x1 = sorted((pa['x'], ta['x']))
        y0, y1 = sorted((pa['y'], ta['y']))
        return x0 <= pb['x'] <= x1 and y0 <= pb['y'] <= y1

    u2_crosses_u3 = span_contains(REFPOL, 'U19.2', 'TP24.1', NPOL, 'U19.3')
    u3_crosses_u2 = span_contains(NPOL, 'U19.3', 'TP23.1', REFPOL, 'U19.2')
    chk('C U19.2 pad->target span CONTAINS U19.3 (it must cross -> last)',
        'contains=%s' % u2_crosses_u3, u2_crosses_u3)
    chk('C U19.3 pad->target span does NOT contain U19.2 (crosses none -> first)',
        'contains=%s' % u3_crosses_u2, not u3_crosses_u2)

    # a lookahead cross-check: the geometric prediction agrees with actually
    # laying each candidate and counting sealed siblings.
    qb = board()
    s = snap(qb)
    route(qb, REFPOL, 'TP24.1', 'U19.2')
    sealed_by_u2 = freedom(qb, NPOL, 'U19.3')[0] == 0
    restore(qb, s)
    route(qb, NPOL, 'TP23.1', 'U19.3')
    sealed_by_u3 = freedom(qb, REFPOL, 'U19.2')[0] == 0
    restore(qb, s)
    chk('C lookahead agrees: U19.2 seals a sibling, U19.3 seals none',
        'u2_seals=%s u3_seals=%s' % (sealed_by_u2, sealed_by_u3),
        sealed_by_u2 and not sealed_by_u3)

    # ---- D: the source carries the scoped tie-break, off by ways-out > 1 ---
    print('  -- D  the driver tie-break is present and scoped ---------------')
    src = open(os.path.join(SP, 'route_battery_block.py'), encoding='utf-8').read()
    chk('D route_battery_block carries the D-277 planar tie-break',
        'crossings computed in order_tight', 'crossings' in src
        and 'PLANAR TIE-BREAK' in src)
    chk('D the crossing term only fires at ways-out <= 1 (scoped, no-op else)',
        "guarded by 'fr_a <= 1'", 'fr_a <= 1' in src)
    chk('D the tie-break is the LAST sort key (settles only exact ties)',
        'crossings[r[3]] appended to the sort key',
        'r[0], r[1], r[2], crossings[r[3]]' in src)

    print('\nRESULT: %s' % ('PASS' if not FAIL else 'FAIL -> ' + ', '.join(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
