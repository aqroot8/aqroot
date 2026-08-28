# -*- coding: utf-8 -*-
"""FBV2-P2-003F -- D-278 REGRESSION: the U19.8 VREC_VCC escape is a ROUTE-ORDER
CROSSING DETOUR (the D-277 crossing pin's antisocial B.Cu horseshoe), fixed by
sending that crossing pin off the outer layer with a LAYER HOP -- and R85.1 is a
DISTINCT blocker the fix neither closes nor claims to close.

D-277 (003E) cleared N_POL U19.3 and Phase A advanced to the next named blocker
`VREC_VCC U19.8 -> (node) NO_LEGAL_ESCAPE` (blockers track / U19.7 / board_edge /
U19.5), co-terminal `VBRIDGE_TOP R85.1`.  003F measured the cause and repaired
the U19.8 half.  This probe pins every load-bearing clause so a later edit cannot
silently re-open U19.8, convert the measured route-order fix into a geometry
claim, or start over-claiming that R85.1 is closed.

  A  INTRINSIC GEOMETRY IS FINE.  On the empty authoritative board U19.8 (5
     ways), R85.1 (8) and D10.1 (7) all have a legal >= 0.150 mm escape.  Cause
     (A) intrinsic pad/board-edge geometry is REFUTED for all three.

  B  THE CONTENTION IS THE D-277 CROSSING PIN'S B.Cu DETOUR.  D-277 routes
     N_POL U19.3 first (correct) and REF_POL U19.2 -- the crossing pin -- last.
     Left on B.Cu, U19.2's direct southern lane is filled by U19.3's copper, so
     its route HORSE-SHOES ~13 mm north over the top of U19 and seals U19.8
     (freedom -> 0, the D-278 fail).  The seal is real and its aggressor is the
     REF_POL detour, not U19.8's own geometry.

  C  THE FIX IS A LAYER HOP FOR THE CROSSING PIN.  Routing U19.2 by an ordinary
     0.35/0.20 through-via F.Cu hop (8.6 mm, direct) instead of the B.Cu
     horse-shoe leaves U19.8 escapable (5 ways) and it ROUTES -- and R85.1 stays
     escapable too.  The six-layer stack is exactly for a crossing.

  D  THE FIX IS SCOPED TO THE D-277 CLASS.  order_tight marks the crossing pin
     (crossings > 0, guarded by fr_a <= 1) in `hop_first_keys`; run_once tries a
     layer hop first for those keys and falls through to the ordinary B.Cu ladder
     on failure.  A pin with a second way out is never marked.

  E  R85.1 IS A DISTINCT BLOCKER, NOT CLOSED AND NOT CLAIMED.  R85.1 is boxed by
     the N_POL chain, not by the REF_POL crossing, and neither R85.1 nor its
     aggressor is single-lane -- so the D-278 predicate correctly does NOT mark
     them.  003F advances Phase A past U19.8 and leaves R85.1 / the dead-cell
     resistor-field congestion to 003G.  This clause fails if a future edit makes
     the driver pretend R85.1 is a crossing-pin case.

  F  003C IS UNTOUCHED (bridge_probe_003c is the guard; this probe never touches
     the D-275 vacate + F.Cu bridge decision set).

    python u19_escape_probe_003f.py
"""
import os, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import qrouter as QR
import harness_paths as H
import battery_route_plan as PL

N = PL.N
CP, CT = 200000, 200000
AUTH = H.project_file(H.PCBNAME)
REFPOL, NPOL = N + 'REF_POL', N + 'N_POL'
VREC, VBR = N + 'VREC_VCC', N + 'VBRIDGE_TOP'

FAIL = []


def chk(name, detail, ok):
    print('  %-4s %-62s %s' % ('OK' if ok else '**', name, detail))
    if not ok:
        FAIL.append(name)


def board():
    return QR.QBoard(AUTH)


def bynet(qb):
    d = {}
    for (net, ref), p in qb.pads.items():
        d.setdefault(net, {})[ref] = p
    return d


def freedom(qb, B, net, ref, w=150000):
    pad = B[net][ref]
    e = qb.escape(pad, 'B', w, w, CP, CT, 25000, qb.ex0, qb.ey0)
    return len(e), (qb.escape_why[0] if not e else '')


def bcu(qb, B, net, a, b):
    pa, pb = B[net][a], B[net][b]
    r = None
    for w in PL.LAD_SIG:
        r = QR.connect_role(qb, net, pa, pb, 'B', w, CP, CT)
        if r['ok']:
            break
    return r


def hop(qb, B, net, a, b):
    pa, pb = B[net][a], B[net][b]
    r = None
    for vd, vk in PL.D257_VIA_LADDER:
        for w in PL.LAD_SIG:
            r = QR.connect_hop(qb, net, pa, pb, w, CP, CT, via_dia=vd, via_drill=vk)
            if r['ok']:
                return r
    return r


def main():
    print('D-278  U19.8 VREC_VCC ESCAPE -- CROSSING-PIN DETOUR + LAYER-HOP FIX')

    # ---- A: intrinsic geometry is fine -----------------------------------
    print('  -- A  intrinsic pad/edge geometry (empty authoritative board) --')
    qb = board(); B = bynet(qb)
    f8, why8 = freedom(qb, B, VREC, 'U19.8')
    chk('A U19.8 has a legal >= 0.150 mm escape on the empty board',
        'freedom %d %s' % (f8, why8), f8 >= 1)
    f85, _ = freedom(qb, B, VBR, 'R85.1')
    f10, _ = freedom(qb, B, VBR, 'D10.1')
    chk('A R85.1 and D10.1 (the co-terminal net) also escape on the empty board',
        'R85.1=%d D10.1=%d' % (f85, f10), f85 >= 1 and f10 >= 1)
    chk('A U19.8 is MULTI-LANE on the empty board (a victim, not the boxed class)',
        'U19.8=%d ways' % f8, f8 >= 2)

    # ---- B: the crossing pin's B.Cu detour seals U19.8 -------------------
    print('  -- B  the REF_POL U19.2 crossing detour, on B.Cu ---------------')
    qb = board(); B = bynet(qb)
    bcu(qb, B, NPOL, 'TP23.1', 'U19.3')          # D-277: U19.3 first
    r2 = bcu(qb, B, REFPOL, 'TP24.1', 'U19.2')   # crossing pin, on B.Cu
    fA, whyA = freedom(qb, B, VREC, 'U19.8')
    chk('B U19.2 on B.Cu takes an antisocial detour (>= 12 mm for a ~7.5 mm net)',
        'REF_POL ok=%s mm=%.2f' % (r2['ok'], r2['mm']), r2['ok'] and r2['mm'] >= 12.0)
    chk('B that detour SEALS U19.8 (reproduces the D-278 fail)',
        'U19.8 freedom %d' % fA, fA == 0)

    # ---- C: the layer hop for the crossing pin frees U19.8 ---------------
    print('  -- C  the fix: route the crossing pin by a LAYER HOP -----------')
    qb = board(); B = bynet(qb)
    bcu(qb, B, NPOL, 'TP23.1', 'U19.3')
    rh = hop(qb, B, REFPOL, 'TP24.1', 'U19.2')
    fC, _ = freedom(qb, B, VREC, 'U19.8')
    chk('C U19.2 hops F.Cu with 2 ordinary through vias, DIRECT (no horse-shoe)',
        'ok=%s vias=%s mm=%.2f' % (rh['ok'], rh.get('vias'), rh['mm']),
        rh['ok'] and rh.get('vias') == 2 and rh['mm'] < 12.0)
    chk('C with the crossing pin hopped, U19.8 is escapable again',
        'U19.8 freedom %d' % fC, fC >= 1)
    r8 = bcu(qb, B, VREC, 'U19.8', 'R84.2')
    f85c, _ = freedom(qb, B, VBR, 'R85.1')
    chk('C U19.8 now ROUTES', 'ok=%s mm=%.2f' % (r8['ok'], r8['mm'] or 0), r8['ok'])
    chk('C R85.1 stays escapable through the U19.8 fix (not made worse)',
        'R85.1 freedom %d' % f85c, f85c >= 1)

    # ---- D: the driver carries the scoped hop ---------------------------
    print('  -- D  the driver hop is present and scoped to the D-277 class ---')
    src = open(os.path.join(SP, 'route_battery_block.py'), encoding='utf-8').read()
    chk('D order_tight records the crossing pin in hop_first_keys',
        "'hop_first_keys.add' present", 'hop_first_keys.add' in src)
    chk('D the mark fires only in the D-277 crossing class (c > 0, fr_a <= 1)',
        "'if c > 0:' under the fr_a <= 1 guard", 'if c > 0:' in src and 'fr_a <= 1' in src)
    chk('D run_once tries a LAYER HOP first for a marked key',
        "'(net, a, b_) in hop_first_keys'",
        '(net, a, b_) in hop_first_keys' in src and 'connect_hop' in src)

    # ---- E: R85.1 is a DISTINCT blocker, not claimed --------------------
    print('  -- E  R85.1 is a distinct blocker (N_POL boxing), left to 003G ---')
    # neither R85.1 nor its N_POL aggressor edges are single-lane on the empty
    # board, so the D-278 fr_a <= 1 predicate correctly does NOT mark them: the
    # fix is scoped to the crossing class and 003F does not pretend to close it.
    qb2 = board(); B2 = bynet(qb2)
    f851, _ = freedom(qb2, B2, VBR, 'R85.1')
    f861, _ = freedom(qb2, B2, NPOL, 'R86.1')
    chk('E R85.1 and its N_POL aggressor are MULTI-LANE (outside the D-278 class)',
        'R85.1=%d R86.1=%d ways (both > 1)' % (f851, f861), f851 > 1 and f861 > 1)
    # The committed full-production result is the honest scoreboard: the D-278 fix
    # ROUTES U19.8 end-to-end, and it does NOT route R85.1 -- which 003F defers to
    # 003G rather than over-claim.  (bridge_eco is null: base config, no promotion.)
    res = os.path.join(SP, 'phaseA_003f_fix.json')
    if os.path.exists(res):
        import json
        r = json.load(open(res))
        routed = set((e['net'].split('/')[-1], e['a'], e['b']) for e in r['journal'])
        u198_ok = ('VREC_VCC', 'U19.8', 'R84.2') in routed
        r85_ok = any(k[0] == 'VBRIDGE_TOP' for k in routed)
        chk('E committed full run ROUTES VREC_VCC U19.8 (fix works in production)',
            'U19.8 routed=%s' % u198_ok, u198_ok)
        chk('E committed full run does NOT route VBRIDGE_TOP R85.1 (deferred to 003G)',
            'R85.1/VBRIDGE routed=%s' % r85_ok, not r85_ok)
        chk('E the full run applied NO ECO / no promotion (base config, bridge_eco null)',
            'bridge_eco=%s' % r.get('bridge_eco'), r.get('bridge_eco') is None)
    else:
        chk('E committed full-production result present (phaseA_003f_fix.json)',
            'missing', False)

    print('\nRESULT: %s' % ('PASS' if not FAIL else 'FAIL -> ' + ', '.join(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
