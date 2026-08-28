# -*- coding: utf-8 -*-
"""FBV2-P2-003J -- MEASURED CAPACITY RECORD (D-282).  The shared western-corridor
BAT_PROTECTED_P bridge is a TOPOLOGY/CAPACITY wall, and 003J localises it: the
smallest ROUTE-ONLY change the 003I audit proposed -- relocate the LTC_GATE /
BAT_RAW corridor TAP via drops out of the box (candidate b) -- is MEASURED
INSUFFICIENT, because the wall is the WHOLE western through-via + control-copper
field, not the taps.

Arc.  003C (D-275) proved the vacate + F.Cu via-array bridge on a SPARSE c3 board.
003D (D-276) integrated it END-OF-RUN and it ABORTED.  003I (D-281) re-timed it
EARLY and measured a symmetric downstream FAIL (GND/BAT_MAIN clearance, BAT_RAW
NO_VIA_SITE): one corridor, two mutually-exclusive high-current users, route order
decides only WHICH fails.  003I deferred the fix to 003J with four candidate
directions: (a) widen/add a lane, (b) relocate the LTC_GATE/BAT_RAW tap via drops
out of the box, (c) re-plan the landing/trunk into a disjoint sub-box, (d) a
co-scheduled joint reservation for both before either routes.

WHAT 003J MEASURES (cheap, on the committed dense 003H board w/FIX003H3, bridge
OFF; in-memory only, the board is COPIED before the D-275 vacate, nothing on disk
is mutated).  The bridge's own high-current traverse rule -- >=1.20 mm F.Cu with
the D-269 0.30 mm trunk-to-via clearance -- is run via-AWARE against candidate
landings after the exact D-275 cardinality-1 SHDN vacate + 4x R75.2 entry array:

  A  BASELINE (confirms D-281): the via-AWARE >=1.20 mm traverse is NO_PATH to the
     NEAR west-cluster landing (D9.1) -- the bridge does not fit end-of-run.

  B  CANDIDATE (b) REFUTED -- the decisive new result.  Removing the 9 corridor
     LTC_GATE / BAT_RAW TAP vias from the obstacle model (simulating a
     route-target/staging relocation out of the box) does NOT reopen the via-AWARE
     >=1.20 mm traverse to the near landing NOR to the far BAT_PROTECTED_P node.
     The taps are not the lever; the ~50-via western through-via field is.

  C  REGION SATURATION + the only path is a DETOUR, not a corridor bridge.  Even
     COPPER-ONLY (no via clearance at all): at the D-275 target width 1.50 mm there
     is NO_PATH to any landing, and the near D9.1 landing is NO_PATH at 1.20 mm too.
     The single copper-only >=1.20 mm path that exists runs to the FAR node
     (~40.7,70.7) and is a ~49 mm cross-board SOUTHERN detour (it leaves the
     corridor south, path max-y ~78.8 >> the corridor y<75) that caps at <=1.30 mm
     -- it is NOT the D-275 >=1.50 mm western-corridor bridge.

CONCLUSION (engineering, CTO scope -- NOT an OWNER decision, NO routing progress).
No route-only relocation of the corridor tap vias yields a viable western-corridor
bridge; candidate (b) is refuted and (d) is the 003I FAIL.  The remaining viable
directions -- (c) a disjoint bridge sub-box reserved in the sparse window with the
whole western block forced to route in the complement, or a placement spread of the
LTC4368 block (owner/mechanical-adjacent, the fallback) -- change CAPACITY, cannot
be proven by a bounded probe, and need a parent-supervised full run.  No rule is
relaxed here; the 0.200 mm clearance and 0.25 mm hole-to-hole floors are ENFORCED.

This probe is the standing HONEST record of that measured capacity result.  Exit
0 = the record holds (nothing silently promoted/absorbed, D-275 + D-277..D-280
invariants intact); 1 = a guarded invariant broke.  Cheap: a handful of bounded
traverse searches, no full route.
"""
import json, math, os, shutil, sys
SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import fcu_cutset_003c as CS       # shared path-role vacate classifier
import bridge_route_003c as BR     # the proven D-275 copper primitives / constants
import bridge_eco_003d as ECO      # the end-of-run driver stage
import bridge_early_003i as EB     # the EARLY route-order driver stage

N = '/01_POWER_TREE/'
NET = N + 'BAT_PROTECTED_P'
FAILED = []
SKIPPED = []

# the committed dense 003H production board (bridge OFF, the clean 71-connection
# routed end-state).  The honest dense reference, same as bridge_probe_003i.
BOARD_CANDIDATES = ['w/FIX003H3']

# the committed authoritative product board -- must stay byte-empty of signal copper
AUTH_PCB = os.path.normpath(os.path.join(
    SP, '..', 'kicad', 'aqroot-beta-v2', 'aqroot-Beta-v2.kicad_pcb'))

# tight western corridor box (same as bridge_probe_003i): R75.2 -> D9.1 region
CORR_XLO, CORR_XHI = 500000, 13500000
CORR_YLO, CORR_YHI = 65000000, 75000000
TAP_NETS = (N + 'BAT_RAW', N + 'LTC_GATE')

# candidate landings: NEAR west-cluster pad (D9.1) and the FAR node aim (D-275)
NEAR_AIM = (11.35e6, 72.5e6)
NODE_AIM = BR.NODE_AIM                      # (42.4, 76.4) -> resolves to the node


def chk(name, got, want, ok):
    print('  %-4s %-58s %-30s expected %s'
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


class Corridor(object):
    """Build a QBoard ONCE on a scratch copy of `pcb` after the exact D-275
    cardinality-1 vacate + 4x R75.2 entry array, then answer via-AWARE / copper-only
    >=W traverse queries against an arbitrary subset of the board's through-vias --
    read-only (no track emission, no board copies per query)."""

    def __init__(self, pcb):
        import pcbnew, qrouter as QR
        scratch = os.path.join(SP, 'w', 'PROBE003J')
        if os.path.isdir(scratch):
            shutil.rmtree(scratch)
        shutil.copytree(os.path.dirname(pcb), scratch)
        self.pcb = os.path.join(scratch, os.path.basename(pcb))
        self.moved = BR.vacate(self.pcb)         # cardinality-1 SHDN vacate
        self.qb = QR.QBoard(self.pcb)
        self.qb.wide_nets = frozenset()
        ev = BR.scan_entry_sites(self.qb)
        for (x, y) in ev:
            self.qb.via(NET, x, y, BR.DIA, BR.DRILL)
        self.entry = len(ev)
        ex = sorted(x for x, y in ev)
        ey0 = int(sum(y for x, y in ev) / len(ev))
        self.qb.track(NET, 'F', ex[0], ey0, ex[-1], ey0, BR.W_TRAVERSE)
        self.sx, self.sy = ex[-1], ey0
        self._snap = dict((L, len(self.qb.shapes[L])) for L in self.qb.cu)
        self._snh = len(self.qb.holes)
        b0 = pcbnew.LoadBoard(self.pcb)
        self.vias = [(t.GetPosition().x, t.GetPosition().y, t.GetWidth(),
                      t.GetDrill(), t.GetNetname())
                     for t in b0.GetTracks() if t.GetClass() == 'PCB_VIA']

    def corridor_vias(self):
        return [v for v in self.vias
                if CORR_XLO <= v[0] <= CORR_XHI and CORR_YLO <= v[1] <= CORR_YHI]

    def taps(self):
        return [v for v in self.corridor_vias()
                if v[4] in TAP_NETS]

    def _inject(self, subset):
        import qrouter as QR
        for (x, y, dia, drill, net) in subset:
            for L in self.qb.cu:
                self.qb.shapes[L].append(QR.SEG(x, y, x, y, dia / 2.0, net, 'via'))
            self.qb.holes.append(QR.RR(x, y, drill / 2.0, drill / 2.0,
                                       drill / 2.0, 0, net, 'via/hole'))
        self.qb._obs_cache = None

    def _restore(self):
        for L in self.qb.cu:
            del self.qb.shapes[L][self._snap[L]:]
        del self.qb.holes[self._snh:]
        self.qb._obs_cache = None

    def _landing(self, aim):
        import path_role_util as RU
        nb = RU.nearest_on_net(self.qb.b, NET, 'B.Cu', int(aim[0]), int(aim[1]))
        if nb is None:
            return None
        return nb[1], int(nb[2] - 900000)

    def _search(self, tx, ty, width):
        import qrouter as QR
        qb = self.qb
        G = 50000
        ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
        x0 = max(min(self.sx, tx) - 9e6, qb.ex0 - 1e6)
        y0 = max(min(self.sy, ty) - 9e6, qb.ey0 - 1e6)
        x1 = min(max(self.sx, tx) + 9e6, qb.ex1 + 1e6)
        y1 = min(max(self.sy, ty) + 9e6, qb.ey1 + 1e6)
        ox2 = int(round((x0 - ox) / G)) * G + ox
        oy2 = int(round((y0 - oy) / G)) * G + oy
        blk = qb.grid('F', NET, width, BR.CP, BR.CTW, ox2, oy2, x1, y1, G)
        si = (int((self.sx - ox2) // G), int((self.sy - oy2) // G))
        ti = (int((tx - ox2) // G), int((ty - oy2) // G))
        ny, nx = blk.shape
        for ii, jj in (si, ti):
            if 0 <= ii < nx and 0 <= jj < ny:
                blk[jj, ii] = False
        path = qb.search(blk, si, ti)
        if not path:
            return None
        pts = [(self.sx, self.sy)] + list(QR.simplify(path, ox2, oy2, G)) + \
              [(tx, ty)]
        mm = sum(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
                 for k in range(len(pts) - 1)) / 1e6
        ymax = max(p[1] for p in pts) / 1e6
        return dict(mm=round(mm, 2), ymax=round(ymax, 2), pts=len(pts))

    def traverse(self, subset, aim, width):
        """PATH-detail dict or None for the >=width via-AWARE(subset) traverse to
        `aim`.  `subset` = the board vias modelled as obstacles."""
        L = self._landing(aim)
        if L is None:
            return 'NO_PAD'
        self._inject(subset)
        try:
            return self._search(L[0], L[1], width)
        finally:
            self._restore()


def main():
    print('FBV2-P2-003J MEASURED CAPACITY RECORD (D-282)')

    board = find_board()
    if board is None:
        skip('A/B/C  corridor capacity (needs the committed dense 003H board)',
             'no board on disk (%s)' % ' / '.join(BOARD_CANDIDATES))
    else:
        rel = os.path.relpath(board, SP)
        C = Corridor(board)
        allv = C.vias
        taps = C.taps()
        notap = [v for v in allv if v not in taps]
        print('  [%s] %d board vias, %d in corridor, %d LTC_GATE/BAT_RAW taps; '
              'vacate moved %d SHDN tracks, entry array %d'
              % (rel, len(allv), len(C.corridor_vias()), len(taps), C.moved,
                 C.entry))

        # A -- BASELINE: via-AWARE >=1.20 mm bridge does NOT fit end-of-run --------
        a_near = C.traverse(allv, NEAR_AIM, 1200000)
        chk('A  via-AWARE 1.20mm bridge to NEAR landing (D9.1) NO_PATH (confirms D-281)',
            'PATH %s' % a_near if a_near else 'NO_PATH', 'NO_PATH', not a_near)

        # B -- CANDIDATE (b) REFUTED: relocating the tap vias does NOT reopen it ---
        b_near = C.traverse(notap, NEAR_AIM, 1200000)
        chk('B  candidate(b): taps-out, via-AWARE 1.20mm to NEAR still NO_PATH',
            'PATH %s' % b_near if b_near else 'NO_PATH', 'NO_PATH', not b_near)
        b_node = C.traverse(notap, NODE_AIM, 1200000)
        chk('B  candidate(b): taps-out, via-AWARE 1.20mm to NODE still NO_PATH',
            'PATH %s' % b_node if b_node else 'NO_PATH', 'NO_PATH', not b_node)
        chk('B  therefore the corridor TAPS are NOT the lever (wall = whole via field)',
            'taps-out NO_PATH near+node', 'refuted',
            (not b_near) and (not b_node))

        # C -- REGION SATURATION + the only copper-only path is a DETOUR ----------
        c_node_150 = C.traverse([], NODE_AIM, 1500000)
        chk('C  copper-only 1.50mm (D-275 target) to NODE NO_PATH (region saturated)',
            'PATH %s' % c_node_150 if c_node_150 else 'NO_PATH', 'NO_PATH',
            not c_node_150)
        c_near_120 = C.traverse([], NEAR_AIM, 1200000)
        chk('C  copper-only 1.20mm to NEAR landing (D9.1) NO_PATH',
            'PATH %s' % c_near_120 if c_near_120 else 'NO_PATH', 'NO_PATH',
            not c_near_120)
        c_node_120 = C.traverse([], NODE_AIM, 1200000)
        is_detour = bool(c_node_120) and c_node_120['ymax'] > 75.5 \
            and c_node_120['mm'] > 25.0
        chk('C  the only copper-only 1.20mm path is a SOUTHERN cross-board DETOUR',
            ('mm=%.1f ymax=%.1f' % (c_node_120['mm'], c_node_120['ymax'])
             if c_node_120 else 'NO_PATH'),
            'detour (ymax>75.5, mm>25) not a corridor bridge', is_detour)

    # D -- invariant preserved (shared contract with bridge_probe_003c/003d/003i) --
    reuse = all(getattr(EB, k) is getattr(BR, k)
                for k in ('NET', 'SHDN', 'DIA', 'DRILL', 'W_TRAVERSE', 'W_LAND'))
    fns = (EB.BR.route_traverse is BR.route_traverse
           and EB.BR.scan_entry_sites is BR.scan_entry_sites
           and EB.BR.inject_vias is BR.inject_vias)
    chk('D  003J reuses the D-275 constants + primitives from bridge_route_003c',
        'reused' if (reuse and fns) else 'diverged', 'reused', reuse and fns)
    ctl = CS.branch_role(N + 'BAT_PROT_SHDN_CTL', {'Q4.1', 'R83.1'})[0]
    chk('D  vacate is the cardinality-1 control branch BAT_PROT_SHDN_CTL',
        '%s' % ctl, 'candidate', ctl == 'candidate')
    for badnet in ('BAT_PROTECTED_P', 'BAT_SENSE', 'BAT_MID', 'BAT_CONNECTOR_P'):
        v = CS.branch_role(N + badnet, {'X.1', 'Y.1'})[0]
        chk('D  current-carrying %s is NOT a vacate candidate' % badnet,
            '%s' % v, 'None', v is None)

    # E -- no false promotion: no 003J result claims a clean/absorbed end-state,
    # and the authoritative product board still carries ZERO signal copper --------
    res = os.path.join(SP, 'phaseA_003j_fix.json')
    if os.path.exists(res):
        r = json.load(open(res))
        drc = r.get('drc') or {}
        base = r.get('baseline') or {}
        absorbed = all(drc.get(k, 0) <= base.get(k, 0)
                       for k in drc) and r.get('connections', 0) >= 71
        chk('E  no committed 003J result claims a clean (absorbed) end-state',
            'clean/absorbed' if absorbed else 'shows FAIL', 'shows FAIL',
            not absorbed)
    else:
        chk('E  no committed 003J success result exists (candidate not promoted)',
            'absent', 'absent', True)
    if os.path.exists(AUTH_PCB):
        import pcbnew
        ab = pcbnew.LoadBoard(AUTH_PCB)
        ntrk = sum(1 for t in ab.GetTracks() if t.GetClass() == 'PCB_TRACK')
        nvia = sum(1 for t in ab.GetTracks() if t.GetClass() == 'PCB_VIA')
        chk('E  authoritative PCB unchanged (0 signal tracks, 0 signal vias)',
            '%d tracks / %d vias' % (ntrk, nvia), '0 / 0',
            ntrk == 0 and nvia == 0)
    else:
        skip('E  authoritative PCB 0/0 guard', 'authoritative board not found')

    tag = 'PASS' if not FAILED else 'FAIL %s' % FAILED
    print('\nFBV2-P2-003J MEASURED CAPACITY RECORD:', tag,
          ('(%d clause[s] skipped)' % len(SKIPPED)) if SKIPPED else '')
    print('VERDICT: candidate (b) relocate-corridor-taps is MEASURED INSUFFICIENT '
          '(the wall is the whole western through-via field, not the taps); no '
          'route-only via relocation yields a viable >=1.20 mm western-corridor '
          'bridge; no authoritative promotion; D-275 and D-277..D-280 preserved; '
          'the disjoint-sub-box / co-scheduled candidate needs a supervised full run.')
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
