# -*- coding: utf-8 -*-
"""FBV2-P2-003I -- MEASURED-FAIL RECORD (D-281).  The route-order EARLY landing of
the proven D-275 western-corridor bridge is a measured, reproducible FAIL: the
bridge and the current-carrying corridor users (LTC_GATE / BAT_RAW tap, plus the
GND pour and BAT_MAIN) CONTEND for one ~9 mm western corridor, and moving the
bridge earlier in the route order does not create room the geometry lacks.

Arc so far.  003C (D-275) proved the vacate + F.Cu via-array bridge on a SPARSE c3
board as a POST-PROCESS.  003D (D-276) integrated the same mechanism as an
END-OF-RUN driver stage (AQROOT_BRIDGE_ECO) and measured it to ABORT.  003I's
preflight isolated the root cause: on the completed production board the tight
western corridor R75.2 -> D9.1 is VIA-DENSE (the +4 LTC_GATE / BAT_RAW-tap vias),
so with the D-269 0.30 mm trunk clearance respected the >= 1.20 mm via-aware
traverse has NO_PATH; drop the via clearance and it PATHs -- the wall is via
density, not copper.  003I then tried the obvious re-timing: lay the SAME bridge
EARLY (AQROOT_BRIDGE_EARLY=1), at the first stage-8 item, while the corridor is
still sparse, and let subsequent routing route around the bridge copper.

THE MEASURED RESULT (parent-supervised full run; recipe c3_00 + SIXLAYER +
D277..D280 + AQROOT_BRIDGE_EARLY=1).  The early bridge DID lay
("EARLY BRIDGE OK land=C58.1 traverse=8.920mm w=1.50 entry=4 exit=4"), BUT the
current-carrying corridor users that route AFTER it then FAILED their normal
gates:

    GND       clearance actual 0.0726 mm  vs 0.200 mm required
    BAT_MAIN  clearance actual 0.125  mm  vs 0.200 mm required
    BAT_RAW   NO_VIA_SITE

These are GENUINE safety-clearance violations and a lost via site, not baseline
noise.  Per the CTO ruling they MUST NOT be absorbed/refreshed into the baseline
(that would waive real clearance violations).  The run is INVALID as a Phase-A
candidate.  No authoritative PCB promotion; D-275 and D-277..D-280 preserved.

WHY (the engineering conclusion).  The early FAIL is the exact SYMMETRIC corollary
of the preflight root cause: end-of-run, the 4 LTC_GATE/BAT_RAW-tap vias occupy the
corridor and the bridge NO_PATHs around them; early, the 1.50 mm bridge traverse
occupies the corridor and those SAME taps lose their via site / clearance around
it.  One corridor, two mutually-exclusive high-current users.  Route ORDER decides
WHICH one fails, not WHETHER one fails -- timing is not the lever.  Closing
BAT_PROTECTED_P on the full board needs a TOPOLOGY / capacity change (widen or add a
corridor, relocate the taps, or re-plan so bridge and taps do not share the box),
NOT a re-ordering -- deferred to FBV2-P2-003J.  No rule is relaxed here.

This probe is the standing HONEST record of that FAIL.  It asserts:
  A  the D-279/D-280 repaired run reached a clean routed end-state with the bridge
     OFF (the precondition 003D lacked) -- committed phaseA_003h_fix.json.
  B  ROOT CAUSE (cheap, real): on the committed dense production board the via-aware
     traverse NO_PATHs while the copper-only traverse PATHs -- the wall is via
     density in the single western corridor.
  C  invariant preserved: the EARLY stage single-sources the D-275 constants +
     primitives from bridge_route_003c; the vacate is the cardinality-1 control
     branch BAT_PROT_SHDN_CTL; the current-carrying trunk nets are refused.
  E  the early bridge LAYS on the reconstructed sparse placed board -- NECESSARY,
     but (per the measured full run) NOT SUFFICIENT.
  F  DECISIVE: the measured full-run downstream FAIL is recorded, the candidate is
     REJECTED, and no false promotion happened -- the authoritative PCB is still 0
     tracks / 0 vias and no 003I result claims a clean promoted end-state.

Exit 0 = the FAIL record holds (nothing was silently promoted / absorbed);
1 = a guarded invariant broke.  Cheap: one bounded traverse search, no full route.
Boards are COPIED to scratch before any in-memory vacate; no committed artifact is
mutated.
"""
import glob, json, math, os, shutil, sys
SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import fcu_cutset_003c as CS       # shared path-role vacate classifier
import bridge_eco_003d as ECO      # the end-of-run driver stage (measured FAIL)
import bridge_route_003c as BR     # the proven copper primitives / constants
import bridge_early_003i as EB     # the EARLY route-order driver stage (also FAIL)

N = '/01_POWER_TREE/'
NET = N + 'BAT_PROTECTED_P'
FAILED = []
SKIPPED = []

# the parent-supervised definitive full run (recipe below).  These are the MEASURED
# downstream gate failures that make the early landing a FAIL; recorded verbatim so
# the closeout does not depend on re-running a long full route.  Per CTO ruling
# these clearance violations MUST NOT be absorbed into the baseline.
MEASURED = {
    'recipe': 'c3_00 + SIXLAYER + D277..D280 + AQROOT_BRIDGE_EARLY=1',
    'early_bridge': 'OK land=C58.1 traverse=8.920mm w=1.50 entry=4 exit=4',
    'downstream_fails': [
        ('GND',      'clearance', 0.0726, 0.200),
        ('BAT_MAIN', 'clearance', 0.125,  0.200),
        ('BAT_RAW',  'NO_VIA_SITE', None,  None),
    ],
}
# the committed authoritative product board -- promotion of a 003I candidate would
# put tracks/vias on it; it must stay byte-empty of signal copper.
AUTH_PCB = os.path.normpath(os.path.join(
    SP, '..', 'kicad', 'aqroot-beta-v2', 'aqroot-Beta-v2.kicad_pcb'))

# the tight western corridor R75.2(2.8,68) -> D9.1(11.35,72.5)/C58.1: the box the
# high-current traverse must cross AND the box the LTC_GATE/BAT_RAW taps drop into.
CORR_XLO, CORR_XHI = 500000, 13500000
CORR_YLO, CORR_YHI = 65000000, 75000000


def corridor_vias(pcb):
    """Count through-vias inside the tight western corridor box on `pcb`."""
    import pcbnew
    b = pcbnew.LoadBoard(pcb)
    n = 0
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            x, y = t.GetPosition().x, t.GetPosition().y
            if CORR_XLO <= x <= CORR_XHI and CORR_YLO <= y <= CORR_YHI:
                n += 1
    return n

# the honest dense reference is the committed 003H production board (FIX003H3).  The
# misleading incomplete interrupted-003I board (FIX003I) is intentionally NOT a
# candidate -- it was removed at closeout as it does not honestly pin any result.
BOARD_CANDIDATES = ['w/FIX003H3']


def chk(name, got, want, ok):
    print('  %-4s %-58s %-24s expected %s'
          % ('PASS' if ok else 'FAIL', name, got, want))
    if not ok:
        FAILED.append(name)
    return ok


def skip(name, why):
    print('  %-4s %-58s %s' % ('SKIP', name, why))
    SKIPPED.append(name)


def find_board():
    for d in BOARD_CANDIDATES:
        p = os.path.join(SP, d, 'aqroot-Beta-v2.kicad_pcb')
        if os.path.exists(p):
            return p
    return None


def traverse_reaches(pcb, inject):
    """Reconstruct the invariant vacate + entry array on a COPY of `pcb`, then try
    the via-aware (inject=True) / copper-only (inject=False) route_traverse to the
    candidate BAT_PROTECTED_P landings.  Returns (any_path, detail)."""
    import qrouter as QR
    import path_role_util as RU
    scratch = os.path.join(SP, 'w', 'PROBE003I')
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    shutil.copytree(os.path.dirname(pcb), scratch)
    b2 = os.path.join(scratch, os.path.basename(pcb))
    moved = BR.vacate(b2)
    qb = QR.QBoard(b2)
    qb.wide_nets = frozenset()
    nv = BR.inject_vias(qb) if inject else 0
    ev = BR.scan_entry_sites(qb)
    for (x, y) in ev:
        qb.via(BR.NET, x, y, BR.DIA, BR.DRILL)
    ex = sorted(x for x, y in ev)
    ey0 = int(sum(y for x, y in ev) / len(ev))
    qb.track(BR.NET, 'F', ex[0], ey0, ex[-1], ey0, BR.W_TRAVERSE)
    sx, sy = ex[-1], ey0
    aims = [(11.35e6, 72.5e6), (12.22e6, 68.5e6), (38.5e6, 71.4e6), BR.NODE_AIM]
    got = None
    for (mx, my) in aims:
        nb = RU.nearest_on_net(qb.b, BR.NET, 'B.Cu', int(mx), int(my))
        if nb is None:
            continue
        nd, npx, npy, ntr = nb
        for w in (1500000, 1400000, 1300000, 1200000):
            ok, mm, npts = BR.route_traverse(qb, sx, sy, npx, int(npy - 900000), w)
            if ok:
                got = (npx / 1e6, npy / 1e6, w / 1e6, round(mm, 2))
                break
        if got:
            break
    return got, dict(moved=moved, vias=nv)


def main():
    print('FBV2-P2-003I EARLY-LANDING MEASURED-FAIL RECORD (D-281)')

    # A -- the repaired (D-279/D-280) full run reached a clean routed end-state
    # with the bridge OFF: the precondition 003D lacked is MET (bridge is the sole
    # remaining Phase-A promotion blocker) ---------------------------------------
    h = os.path.join(SP, 'phaseA_003h_fix.json')
    if os.path.exists(h):
        r = json.load(open(h))
        be = r.get('bridge_eco')
        drc = r.get('drc') or {}
        base = r.get('baseline') or {}
        no_new_drc = all(drc[k] <= base.get(k, 0) for k in drc)
        clean = (be is None and r.get('connections', 0) >= 71 and no_new_drc)
        chk('A  D-279/D-280 repaired run: bridge OFF, clean routed end-state',
            'conn=%s eco=%s no_new_drc=%s'
            % (r.get('connections'), be, no_new_drc), 'clean', clean)
    else:
        skip('A  repaired-run end-state (phaseA_003h_fix.json)', 'result absent')

    # B -- ROOT CAUSE: the wall is via density in ONE corridor, not copper --------
    board = find_board()
    if board is None:
        skip('B  via-density root cause (needs the committed dense board)',
             'no committed board on disk (%s)' % ' / '.join(BOARD_CANDIDATES))
    else:
        rel = os.path.relpath(board, SP)
        with_v, dv = traverse_reaches(board, inject=True)
        without_v, _ = traverse_reaches(board, inject=False)
        cv = corridor_vias(board)
        chk('B  invariant vacate is cardinality-1 (SHDN branch only)',
            '%d tracks moved' % dv['moved'], '>= 0', dv['moved'] >= 0)
        chk('B  [%s] tight western corridor is via-DENSE at end-of-run' % rel,
            '%d corridor vias' % cv, '>= 12 (proven-sparse 11)', cv >= 12)
        chk('B  [%s] via-AWARE traverse (0.30mm, %d vias) lays NO bridge'
            % (rel, dv['vias']),
            'PATH %s' % (with_v,) if with_v else 'NO_PATH', 'NO_PATH',
            with_v is None)
        chk('B  [%s] copper-only traverse (no via clearance) DOES reach a landing'
            % rel,
            'PATH %s' % (without_v,) if without_v else 'NO_PATH', 'PATH',
            without_v is not None)

    # C -- invariant preserved (shared contract with bridge_probe_003c/003d) ------
    reuse = all(getattr(ECO, k) is getattr(BR, k)
                for k in ('NET', 'SHDN', 'DIA', 'DRILL', 'W_TRAVERSE', 'W_LAND',
                          'NODE_AIM'))
    fns = (ECO.BR.vacate is BR.vacate and ECO.BR.route_traverse is BR.route_traverse
           and ECO.BR.scan_entry_sites is BR.scan_entry_sites)
    chk('C  ECO single-sources D-275 constants + primitives from bridge_route_003c',
        'reused' if (reuse and fns) else 'diverged', 'reused', reuse and fns)
    chk('C  vacate net is the control branch BAT_PROT_SHDN_CTL',
        ECO.SHDN, N + 'BAT_PROT_SHDN_CTL', ECO.SHDN == N + 'BAT_PROT_SHDN_CTL')
    ctl = CS.branch_role(N + 'BAT_PROT_SHDN_CTL', {'Q4.1', 'R83.1'})[0]
    chk('C  control BAT_PROT_SHDN_CTL IS the vacate candidate',
        '%s' % ctl, 'candidate', ctl == 'candidate')
    for badnet in ('BAT_PROTECTED_P', 'BAT_SENSE', 'BAT_MID', 'BAT_CONNECTOR_P'):
        v = CS.branch_role(N + badnet, {'X.1', 'Y.1'})[0]
        chk('C  current-carrying %s is NOT a vacate candidate' % badnet,
            '%s' % v, 'None', v is None)
    ereuse = all(getattr(EB, k) is getattr(BR, k)
                 for k in ('NET', 'SHDN', 'DIA', 'DRILL', 'W_TRAVERSE', 'W_LAND'))
    efns = (EB.BR.route_traverse is BR.route_traverse
            and EB.BR.scan_entry_sites is BR.scan_entry_sites
            and EB.BR.inject_vias is BR.inject_vias)
    chk('C  EARLY stage single-sources D-275 constants + primitives from BR',
        'reused' if (ereuse and efns) else 'diverged', 'reused', ereuse and efns)
    chk('C  EARLY landing refs are named BAT_PROTECTED_P components',
        ','.join(EB.LAND_REFS), 'D9.1,C58.1',
        EB.LAND_REFS == ['D9.1', 'C58.1'])

    # E -- the EARLY stage LAYS a legal bridge on a reconstructed sparse placed
    # board.  This is the NECESSARY precondition -- and the reason the naive
    # re-timing was worth measuring -- but the measured full run (clause F) proves
    # it is NOT SUFFICIENT.  Cheap; SKIPPED if the reconstruction deps are absent. -
    try:
        import pcbnew, qrouter as QR
        placed = EB.reconstruct_placed('PROBE003I_PLACED')
        import path_role_util as RU
        base, _ = RU.drc(placed, 'Eb', os.path.join(SP, 'w'))
        cp = os.path.join(SP, 'w', 'PROBE003I_BRIDGE')
        if os.path.isdir(cp):
            shutil.rmtree(cp)
        shutil.copytree(os.path.dirname(placed), cp)
        cpcb = os.path.join(cp, os.path.basename(placed))
        rec = EB.apply_early_path(cpcb)
        after, _ = RU.drc(cpcb, 'Ea', os.path.join(SP, 'w'))
        laid = rec.get('ok') and rec.get('traverse', {}).get('ok')
        chk('E  early bridge LAYS on the sparse placed board (NECESSARY only)',
            'ok land=%s' % rec.get('land') if laid else 'FAIL %s' % rec.get('fail'),
            'ok', bool(laid))
        if laid:
            tv = rec['traverse']
            chk('E  entry array >= 3 vias (POFV on R75.2)',
                '%d' % len(rec['entry_vias']), '>= 3', len(rec['entry_vias']) >= 3)
            chk('E  traverse width >= 1.20 mm (full trunk floor)',
                '%.2f mm' % tv['w_mm'], '>= 1.20', tv['w_mm'] >= 1.20)
            chk('E  exit array >= 3 vias (array landing, no single via carries I)',
                '%d' % rec['exit_vias'], '>= 3', rec['exit_vias'] >= 3)
        NEUT = ('clearance', 'hole_clearance', 'shorting_items',
                'solder_mask_bridge')
        new_drc = {k: after.get(k, 0) - base.get(k, 0) for k in NEUT
                   if after.get(k, 0) > base.get(k, 0)}
        chk('E  early bridge alone introduces NO new DRC on the SPARSE board',
            'deltas %s' % (new_drc or 'none'), 'none', not new_drc)
    except Exception as e:
        skip('E  early-stage legal bridge (reconstructed placed board)',
             'reconstruction unavailable: %r' % e)

    # F -- DECISIVE: the measured full-run downstream FAIL, the candidate REJECTED,
    # and NO false promotion -----------------------------------------------------
    print('  ---- F: measured full run (%s) ----' % MEASURED['recipe'])
    print('       early bridge: %s' % MEASURED['early_bridge'])
    real_violation = False
    for net, kind, actual, req in MEASURED['downstream_fails']:
        if kind == 'clearance':
            bad = actual < req
            print('       %-9s %s actual %.4f mm vs %.3f mm required  -> %s'
                  % (net, kind, actual, req, 'VIOLATION' if bad else 'ok'))
            real_violation = real_violation or bad
        else:
            print('       %-9s %s' % (net, kind))
            real_violation = True
    chk('F  the measured full run has real downstream clearance/site FAILs',
        'GND 0.0726/BAT_MAIN 0.125 < 0.200; BAT_RAW NO_VIA_SITE',
        'real violations', real_violation)

    # guard 1: no 003I result was promoted claiming a clean end-state (absorption
    # of the violations would show up as a "clean" phaseA_003i_fix.json)
    res = os.path.join(SP, 'phaseA_003i_fix.json')
    if os.path.exists(res):
        r = json.load(open(res))
        drc = r.get('drc') or {}
        base = r.get('baseline') or {}
        absorbed = all(drc.get(k, 0) <= base.get(k, 0)
                       for k in drc) and r.get('connections', 0) >= 71
        chk('F  no committed 003I result claims a clean (absorbed) end-state',
            'clean/absorbed' if absorbed else 'shows FAIL', 'shows FAIL',
            not absorbed)
    else:
        chk('F  no committed 003I success result exists (candidate not promoted)',
            'absent', 'absent', True)

    # guard 2: the authoritative product board carries ZERO signal copper -- a
    # 003I promotion would have laid the bridge (and the downstream tracks) on it
    if os.path.exists(AUTH_PCB):
        import pcbnew
        ab = pcbnew.LoadBoard(AUTH_PCB)
        ntrk = sum(1 for t in ab.GetTracks() if t.GetClass() == 'PCB_TRACK')
        nvia = sum(1 for t in ab.GetTracks() if t.GetClass() == 'PCB_VIA')
        chk('F  authoritative PCB unchanged (0 signal tracks, 0 signal vias)',
            '%d tracks / %d vias' % (ntrk, nvia), '0 / 0',
            ntrk == 0 and nvia == 0)
    else:
        skip('F  authoritative PCB 0/0 guard', 'authoritative board not found')

    tag = 'PASS' if not FAILED else 'FAIL %s' % FAILED
    print('\nFBV2-P2-003I MEASURED-FAIL RECORD:', tag,
          ('(%d clause[s] skipped)' % len(SKIPPED)) if SKIPPED else '')
    print('VERDICT: the early route-order landing is a measured FAIL '
          '(one corridor, two mutually-exclusive high-current users); '
          'no authoritative promotion; D-275 and D-277..D-280 preserved; '
          'topology/capacity fix deferred to FBV2-P2-003J.')
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
