# -*- coding: utf-8 -*-
"""FBV2-P2-003G -- D-279: THE DEAD-CELL RESISTOR-FIELD CONGESTION IS AN
ANTISOCIAL B.Cu DETOUR, NOT INTRINSIC GEOMETRY AND NOT THE D-278 CROSSING PIN.

D-278 (003F) cleared VREC_VCC U19.8 and named the next two blockers, both
NO_LEGAL_ESCAPE on a FULL production run in the packed 0402 dead-cell field
(R84-R96 / Q5-Q9, 0.65 mm pitch):

    VBRIDGE_TOP R85.1 -> D10.1      boxed by N_POL
    REF_HO      R92.1 <-> R93.2     boxed by REC_GATE_N (R93.2 the sealed pad)

003G measured the cause and repaired both.  This probe pins every load-bearing
clause so a later edit cannot silently re-open a victim, convert the measured
route-order fix into a geometry claim, or forget that the repair rotates a
casualty onto N_BATDIV C61.1 (deferred to 003H, not over-claimed as closed).

  A  INTRINSIC GEOMETRY IS FINE.  On the empty authoritative board R85.1 (8),
     D10.1 (7), R92.1 (8) and R93.2 (8) all have a legal >= 0.150 mm escape.
     Cause (A) intrinsic pad/board-edge geometry is REFUTED for all four.

  B  THE AGGRESSOR IS AN ANTISOCIAL DETOUR, NOT THE NET ITSELF.  Routed DIRECT
     on the empty board the boxing connection N_POL R85.2 -> R86.1 runs ~2.5 mm
     and R85.1 stays escapable; only when the packed field fills does that same
     connection come back a 6+ mm B.Cu HORSESHOE whose copper walls R85.1 to 0.
     So the seal is the DETOUR, exactly the D-278 lesson generalised from the
     single crossing pin to any low-current dead-cell route that detours.

  C  THE COMMITTED BASELINE SEALS BOTH VICTIMS; THE D-279 FIX ROUTES BOTH.  On
     the full production baseline (D-279 off) VBRIDGE_TOP and REF_HO are BOTH
     unconnected (R85.1|D10.1, R93.2 isolated).  With D-279 on, the antisocial
     detours take an ordinary through-via layer hop (inner signal layer first,
     D-257 preferred via, no rule relaxed) and BOTH victims route.

  D  THE FIX IS SCOPED AND MEASURED AT ROUTE TIME.  run_once re-routes a B.Cu
     SIG route as a layer hop ONLY when it is a dead-cell-class net (never a
     wide/high-current net, TRUNK/TAP role, or node target) AND its copper came
     back > D279_K x the straight-line pad span AND > D279_MIN_MM.  The swap is
     kept ONLY if the hop is legal and strictly shorter.  Env-gated (AQROOT_D279)
     so the pre-003G behaviour is reproduced byte-for-byte when unset.

  E  THE REPAIR IS NET-POSITIVE AND ITS ONE CASUALTY IS TRACKED, NOT HIDDEN.
     Fix vs baseline: in-scope nets connected 23 -> 24, ratsnest one better, DRC
     histogram identical.  The coupled field rotates ONE casualty -- the
     pre-existing hyper-marginal 46 mm cross-board hop N_BATDIV C61.1 -> U19.6 --
     off B.Cu; it is a FUNCTIONAL net (not a test point) and is deferred to 003H,
     NOT claimed closed.  This clause fails if a future edit pretends C61.1 is
     fine or trades a functional connection for a test point.

  F  003C / D-277 / D-278 ARE UNTOUCHED (bridge_probe_003c and u19_escape_probe_
     003e/003f are the guards; this probe never touches those decision sets).

    python3 u19_escape_probe_003g.py
"""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import qrouter as QR
import harness_paths as H
import battery_route_plan as PL

N = PL.N
CP, CT = 200000, 200000
AUTH = H.project_file(H.PCBNAME)
VBR, REFHO, NPOL = N + 'VBRIDGE_TOP', N + 'REF_HO', N + 'N_POL'

FAIL = []


def chk(name, detail, ok):
    print('  %-4s %-64s %s' % ('OK' if ok else '**', name, detail))
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


def routed_set(path):
    r = json.load(open(path))
    return r, set((e['net'].split('/')[-1], e['a'], e['b']) for e in r['journal'])


def main():
    print('D-279  DEAD-CELL RESISTOR-FIELD CONGESTION -- ANTISOCIAL-DETOUR LAYER HOP')

    # ---- A: intrinsic geometry is fine ----------------------------------
    print('  -- A  intrinsic pad/edge geometry (empty authoritative board) --')
    qb = board(); B = bynet(qb)
    f85, why85 = freedom(qb, B, VBR, 'R85.1')
    f10, _ = freedom(qb, B, VBR, 'D10.1')
    f92, _ = freedom(qb, B, REFHO, 'R92.1')
    f93, _ = freedom(qb, B, REFHO, 'R93.2')
    chk('A R85.1 escapes on the empty board (intrinsic geometry refuted)',
        'R85.1=%d %s' % (f85, why85), f85 >= 2)
    chk('A its net-mate D10.1 also escapes', 'D10.1=%d' % f10, f10 >= 1)
    chk('A R92.1 and R93.2 escape on the empty board (refuted)',
        'R92.1=%d R93.2=%d' % (f92, f93), f92 >= 2 and f93 >= 2)

    # ---- B: the aggressor is the DETOUR, not the connection --------------
    print('  -- B  the boxing connection is harmless routed DIRECT ------------')
    qb = board(); B = bynet(qb)
    r = bcu(qb, B, NPOL, 'R85.2', 'R86.1')
    fB, _ = freedom(qb, B, VBR, 'R85.1')
    chk('B N_POL R85.2->R86.1 routes SHORT/direct on the empty board',
        'ok=%s mm=%.2f' % (r['ok'], r['mm'] or 0), r['ok'] and (r['mm'] or 0) < 4.0)
    chk('B and with it direct, R85.1 is STILL escapable (the seal is the detour)',
        'R85.1 freedom %d' % fB, fB >= 1)

    # ---- C/E: committed baseline seals both; the fix routes both ---------
    print('  -- C/E  committed full-run baseline vs D-279 fix -----------------')
    base_p = os.path.join(SP, 'phaseA_003g_base.json')
    fix_p = os.path.join(SP, 'phaseA_003g_fix.json')
    if os.path.exists(base_p) and os.path.exists(fix_p):
        base, kb = routed_set(base_p)
        fix, kf = routed_set(fix_p)
        v1 = ('VBRIDGE_TOP', 'R85.1', 'D10.1')
        v2 = ('REF_HO', 'R92.1', 'R93.2')
        chk('C baseline (D-279 off) does NOT route VBRIDGE_TOP R85.1 (the blocker)',
            'routed=%s' % (v1 in kb), v1 not in kb)
        chk('C baseline (D-279 off) does NOT route REF_HO R92.1<->R93.2',
            'routed=%s' % (v2 in kb), v2 not in kb)
        chk('C the D-279 fix ROUTES VBRIDGE_TOP R85.1->D10.1',
            'routed=%s' % (v1 in kf), v1 in kf)
        chk('C the D-279 fix ROUTES REF_HO R92.1<->R93.2',
            'routed=%s' % (v2 in kf), v2 in kf)
        chk('E the fix is net-positive on connections',
            'base=%d fix=%d' % (base['connections'], fix['connections']),
            fix['connections'] > base['connections'])
        chk('E the fix does not add a DRC class (histogram identical to baseline)',
            'base=%s fix=%s' % (dict(sorted(base['drc'].items())),
                                dict(sorted(fix['drc'].items()))),
            dict(base['drc']) == dict(fix['drc']))
        chk('E the fix lays no authoritative ECO (base config, bridge_eco null)',
            'bridge_eco=%s' % fix.get('bridge_eco'), fix.get('bridge_eco') is None)
        # the tracked casualty: N_BATDIV C61.1 rotates out, deferred to 003H
        cas = ('N_BATDIV', 'C61.1', 'U19.6')
        chk('E the tracked casualty is N_BATDIV C61.1 (functional, deferred to 003H)',
            'C61.1->U19.6 in base=%s fix=%s' % (cas in kb, cas in kf),
            cas in kb and cas not in kf)
    else:
        chk('C/E committed full-run results present '
            '(phaseA_003g_base.json / phaseA_003g_fix.json)', 'missing', False)

    # ---- D: the driver carries the scoped, measured predicate ------------
    print('  -- D  the D-279 predicate is present and scoped ------------------')
    src = open(os.path.join(SP, 'route_battery_block.py'), encoding='utf-8').read()
    chk('D D-279 is env-gated (off by default -> pre-003G reproduced)',
        "AQROOT_D279", "os.environ.get('AQROOT_D279')" in src)
    chk('D the trigger is a measured antisocial detour (ratio AND absolute)',
        "D279_K x span AND D279_MIN_MM",
        "D279_K * max(direct_mm" in src and "D279_MIN_MM" in src)
    chk('D scoped to the low-current dead-cell class (WIDE and node excluded)',
        "net not in WIDE / net[len(N):] in PL.DEADCELL",
        'net not in WIDE' in src and 'net[len(N):] in PL.DEADCELL' in src
        and "role == 'SIG'" in src)
    chk('D the hop is kept ONLY if legal and strictly shorter',
        "rh['mm'] < bcu_mm", "rh['mm'] < bcu_mm" in src)

    print('\nRESULT: %s' % ('PASS' if not FAIL else 'FAIL -> ' + ', '.join(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
