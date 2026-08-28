# -*- coding: utf-8 -*-
"""FBV2-P2-003H -- D-280: THE FUNCTIONAL CASUALTY `N_BATDIV C61.1 -> U19.6` IS A
CO-LOCATED LANDING BARREL, NOT A PAD-GEOMETRY OR CORRIDOR BLOCKER.

003G (D-279) closed both named dead-cell escape blockers and ROTATED one
functional casualty onto `N_BATDIV C61.1 -> U19.6 NO ROUTE` (a bypass cap on the
divider-sense node, NOT a test point).  003H measured its cause and repaired it.

  CAUSE (measured).  `U19.6` is the SOT-23-8 pin hard against the west board
  edge: it has ONE useful escape lane (east, into the field).  Two N_BATDIV
  connections are co-terminal there -- `U19.6 -> R89.2` and the 46 mm cross-board
  `C61.1 -> U19.6` bypass hop -- so both want a through-via barrel at that one
  escape.  On the committed 003G BASE board they land 0.450 mm apart (two 0.20 mm
  drills), i.e. EXACTLY the 0.25 mm `min_hole_to_hole` floor, ZERO margin.  The
  fault is NOT pad geometry (U19.6 escapes freely on the empty board) and NOT a
  corridor: it is the second barrel co-locating with the first.

  DEFECT.  `connect_hop` places a hop's escape via by a fast path,
  `free_everywhere`, that checked only COPPER clearance -- which is waived for a
  via's OWN net -- and NOT hole-to-hole.  `via_site` (the fallback placement)
  DOES enforce hole-to-hole, but it is only consulted when free_everywhere fails.
  So a hop whose single-lane pad escapes straight onto a co-terminal SAME-NET
  barrel dropped a second drill on top of the first (measured: C61.1's landing
  0.035 mm from the U19.6->R89.2 via, hole edge -0.165 mm) and DRC answered
  `holes_co_located` / `hole_to_hole` every pass.  The 003G field perturbation
  is what tipped C61.1's landing onto the co-located point; the 0-margin base fit
  had no room to give.

  FIX (D-280, env-gated `AQROOT_D280`).  free_everywhere now also enforces the
  net-agnostic `min_hole_to_hole` floor for the barrel it is about to drill.  A
  co-locating site is rejected and the placement falls through to via_site, which
  finds the nearest reachable barrel that clears the floor -- the base's own
  0.45 mm landing.  The guard ADDS a rejection only: it relaxes nothing, moves no
  part, and can only relocate a co-locating via to a legal, separated site.
  Unset, it reproduces the pre-003H behaviour byte-for-byte.

  A  INTRINSIC GEOMETRY IS FINE.  U19.6 escapes on the empty authoritative
     board (>= 2 ways at 0.15 mm); the cause is the co-terminal barrel, not the
     pad.  On the committed BASE board the two N_BATDIV barrels land 0.450 mm
     apart -- the 0.25 mm hole-to-hole floor EXACTLY, zero margin.

  B  THE DEFECT REPRODUCES DETERMINISTICALLY, AND THE FIX REPAIRS IT.  With
     U19.6's sole escape barrel pre-placed, routing `C61.1 -> U19.6`:
       D-280 OFF -> the landing CO-LOCATES (hole edge < the 0.25 mm floor),
       D-280 ON  -> the landing is LEGAL (hole edge >= the floor), separated.

  C  THE FIX IS ENV-GATED.  Unset (`AQROOT_D280`) the guard is inert (the
     co-location reproduces), so every earlier measurement stands untouched.

  D  THE GUARD IS PRESENT, HOLE-TO-HOLE, AND STRICTER-ONLY.  It lives in
     connect_hop's free_everywhere, tests `min_hole_to_hole` against every hole
     (its own net included), and only ever returns False earlier -- it relaxes
     no rule, invents no via, and moves no part.

  E  THE REPAIR IS NET-POSITIVE AND CLOSES THE CASUALTY.  003G fix (D-280 off)
     does NOT route C61.1; the 003H fix (D-280 on) ROUTES `C61.1 -> U19.6`,
     connections +1, DRC histogram identical, and both D-279 named gains
     (VBRIDGE_TOP R85.1->D10.1, REF_HO R92.1<->R93.2) are preserved.

  F  003C / D-277 / D-278 / D-279 ARE UNTOUCHED (bridge_probe_003c and
     u19_escape_probe_003e/003f/003g are the guards; this probe never touches
     those decision sets).

    python3 u19_escape_probe_003h.py
"""
import json, math, os, sys
SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import qrouter as QR
import harness_paths as H
import battery_route_plan as PL

N = PL.N
CP, CT = 200000, 200000
AUTH = H.project_file(H.PCBNAME)
NB = N + 'N_BATDIV'
H2H_FLOOR = 250000        # .kicad_pro min_hole_to_hole = 0.25 mm

FAIL = []


def chk(name, detail, ok):
    print('  %-4s %-66s %s' % ('OK' if ok else '**', name, detail))
    if not ok:
        FAIL.append(name)


def board():
    return QR.QBoard(AUTH)


def padof(qb, ref):
    for (net, tag), p in qb.pads.items():
        if tag == ref:
            return p
    return None


def min_edge(qb, x, y, drill):
    """Smallest hole-to-hole edge distance from a barrel of `drill` at (x, y) to
    any OTHER existing hole -- the net-agnostic manufacturing spacing."""
    best = None
    for h in qb.holes:
        d = math.hypot(h.cx - x, h.cy - y)
        if d < 1:                       # the barrel itself
            continue
        e = d - max(h.hx, h.hy) - drill / 2.0
        if best is None or e < best:
            best = e
    return best


def routed_set(path):
    r = json.load(open(path))
    return r, set((e['net'].split('/')[-1], e['a'], e['b']) for e in r['journal'])


def hop_landing(d280):
    """Deterministic, scratch-free reproduction.  Pre-place U19.6's sole east
    escape barrel (as `U19.6 -> R89.2` does), then route `C61.1 -> U19.6` and
    report where its landing barrel falls and its hole-to-hole edge."""
    if d280:
        os.environ['AQROOT_D280'] = '1'
    else:
        os.environ.pop('AQROOT_D280', None)
    qb = board()
    u196, c61 = padof(qb, 'U19.6'), padof(qb, 'C61.1')
    qb.via(NB, 4950000, 27950000, 350000, 200000)   # the co-terminal barrel
    m = qb.mark()
    r = QR.connect_hop(qb, c61['net'], c61, u196, 150000, CP, CT,
                       far=None, via_dia=350000, via_drill=200000)
    if not r['ok']:
        qb.revert(m)
        return None, None
    land = min(r['via_xy'], key=lambda v: math.hypot(v[0] - 4.95, v[1] - 27.9))
    e = min_edge(qb, land[0] * 1e6, land[1] * 1e6, 200000) / 1e6   # -> mm
    qb.revert(m)
    os.environ.pop('AQROOT_D280', None)
    return land, e


def main():
    print('D-280  N_BATDIV C61.1 -> U19.6 CO-LOCATED LANDING -- HOLE-TO-HOLE GUARD')

    # ---- A: intrinsic geometry fine; the committed base barrels are 0-margin --
    print('  -- A  the cause is the co-terminal barrel, not pad geometry -------')
    qb = board()
    u196 = padof(qb, 'U19.6')
    esc = qb.escape(u196, 'B', 150000, 150000, CP, CT, 25000, qb.ex0, qb.ey0)
    chk('A U19.6 escapes on the empty authoritative board (geometry fine)',
        'ways=%d' % len(esc), len(esc) >= 2)
    base_p = os.path.join(SP, 'phaseA_003g_base.json')
    if os.path.exists(base_p):
        base, kb = routed_set(base_p)
        vias = {}
        for e in base['journal']:
            if e['net'].split('/')[-1] == 'N_BATDIV' and e.get('via_xy'):
                for v in e['via_xy']:
                    vias[(e['a'], e['b'], tuple(v))] = v
        # the two co-terminal U19.6 barrels: U19.6->R89.2 escape and C61.1 landing
        pts = [v for (a, b, _), v in vias.items()
               if abs(v[0] - 4.95) < 0.2 and 27.3 < v[1] < 28.2]
        pts = sorted(set(map(tuple, pts)))
        d = (math.hypot((pts[0][0] - pts[1][0]) * 1e6,
                        (pts[0][1] - pts[1][1]) * 1e6) if len(pts) >= 2 else 0)
        edge = (d - 200000) / 1e6 if d else 0        # two 0.20 mm drills
        chk('A the BASE lands the two N_BATDIV barrels at the hole-to-hole floor',
            'c2c=%.3f mm edge=%.4f mm (floor %.2f)'
            % (d / 1e6, edge, H2H_FLOOR / 1e6),
            len(pts) >= 2 and abs(edge - H2H_FLOOR / 1e6) < 0.02)
    else:
        chk('A committed BASE result present (phaseA_003g_base.json)',
            'missing', False)

    # ---- B/C: deterministic reproduction; D-280 off co-locates, on is legal ---
    print('  -- B/C  reproduce the co-location; the guard repairs it -----------')
    land_off, e_off = hop_landing(False)
    land_on, e_on = hop_landing(True)
    chk('B/C D-280 OFF lands C61.1 CO-LOCATED (hole edge below the floor)',
        ('edge=%+.4f mm at (%.3f,%.3f)' % (e_off, land_off[0], land_off[1])
         if land_off else 'hop failed'),
        land_off is not None and e_off < H2H_FLOOR / 1e6)
    chk('B   D-280 ON lands C61.1 LEGAL (hole edge at/above the floor)',
        ('edge=%+.4f mm at (%.3f,%.3f)' % (e_on, land_on[0], land_on[1])
         if land_on else 'hop failed'),
        land_on is not None and e_on >= H2H_FLOOR / 1e6)
    chk('C the guard is env-gated (unset reproduces the pre-003H co-location)',
        'off<floor=%s on>=floor=%s'
        % (e_off < H2H_FLOOR / 1e6, e_on >= H2H_FLOOR / 1e6),
        (e_off < H2H_FLOOR / 1e6) and (e_on >= H2H_FLOOR / 1e6))

    # ---- D: the guard is present, hole-to-hole, stricter-only -----------------
    print('  -- D  the D-280 guard in qrouter.connect_hop ----------------------')
    src = open(os.path.join(SP, 'qrouter.py'), encoding='utf-8').read()
    chk('D D-280 is env-gated (off by default -> pre-003H reproduced)',
        "AQROOT_D280", "os.environ.get('AQROOT_D280')" in src)
    chk('D the guard enforces the net-agnostic hole-to-hole floor on the barrel',
        "via_drill/2 + h2h vs every hole",
        'via_drill / 2.0 + h2h' in src and 'for hole in qb.holes' in src)
    chk('D it lives in connect_hop free_everywhere and only ADDS a rejection',
        "def free_everywhere ... return False",
        'def free_everywhere' in src
        and 'D-280: net-agnostic hole-to-hole floor' in src)

    # ---- E: full-run net-positive; the casualty closes, gains preserved -------
    print('  -- E  full-run: 003G fix (C61 lost) vs 003H fix (C61 closed) ------')
    g_p = os.path.join(SP, 'phaseA_003g_fix.json')
    h_p = os.path.join(SP, 'phaseA_003h_fix.json')
    if os.path.exists(g_p) and os.path.exists(h_p):
        gfix, kg = routed_set(g_p)
        hfix, kh = routed_set(h_p)
        cas = ('N_BATDIV', 'C61.1', 'U19.6')
        v1 = ('VBRIDGE_TOP', 'R85.1', 'D10.1')
        v2 = ('REF_HO', 'R92.1', 'R93.2')
        chk('E the 003G fix (D-280 off) does NOT route the casualty C61.1',
            'routed=%s' % (cas in kg), cas not in kg)
        chk('E the 003H fix (D-280 on) ROUTES N_BATDIV C61.1 -> U19.6',
            'routed=%s' % (cas in kh), cas in kh)
        chk('E the repair is net-positive on connections',
            'g=%d h=%d' % (gfix['connections'], hfix['connections']),
            hfix['connections'] > gfix['connections'])
        chk('E the repair does not add a DRC class (histogram identical)',
            'g=%s h=%s' % (dict(sorted(gfix['drc'].items())),
                           dict(sorted(hfix['drc'].items()))),
            dict(gfix['drc']) == dict(hfix['drc']))
        chk('E both D-279 named gains are PRESERVED (VBRIDGE_TOP, REF_HO)',
            'VBRIDGE_TOP=%s REF_HO=%s' % (v1 in kh, v2 in kh),
            v1 in kh and v2 in kh)
        chk('E the repair lays no authoritative ECO (bridge_eco null)',
            'bridge_eco=%s' % hfix.get('bridge_eco'),
            hfix.get('bridge_eco') is None)
    else:
        chk('E committed full-run results present '
            '(phaseA_003g_fix.json / phaseA_003h_fix.json)', 'missing', False)

    print('\nRESULT: %s' % ('PASS' if not FAIL else 'FAIL -> ' + ', '.join(FAIL)))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
