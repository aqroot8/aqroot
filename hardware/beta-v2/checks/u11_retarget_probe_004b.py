# -*- coding: utf-8 -*-
"""FBV2-P2-004B -- MEASURED RECORD (D-302).  The U11.2 BAT_PROTECTED_P
trunk-endpoint RETARGET lever: u11_escape's default cross-board U11.2->D9.1
>=1.20 mm B.Cu trunk has NO legal corridor (the single central channel already
holds the EARLY SOUTH BRIDGE + the R75.2 trunk -- a structural >=1.20 mm-trunk
NO_LEGAL_PATH, the D-273/274/281/282/283 class).  U11.2 is IN the east node and
already on-net with D9.1 through the bridge/R75.2 backbone, so the second
cross-board trunk is redundant: retarget the U11.2 trunk endpoint to a SHORT wide
tap into the nearest already->=1.20 mm-connected BPP node copper (C36.1, landed by
the D-275/D-288 bridge via-array + four 1.20 mm B.Cu spokes).

THE WALL (D-301/004A).  u11_escape() (route_battery_block.py) runs LAST, at queue
drain, on the fully-routed board.  It escapes D9.1 (11.350,72.500) at 1.50 mm,
flares U11.2 (66.400,78.200) 1.50->0.20 mm, then connect_role(launch->D9.1) at
1.50/1.20 mm -- a ~55 mm cross-board >=1.20 mm B.Cu trunk with no legal path, so
u11_escape returns False and the run FAILs `U11.2 escape: none exists`.

THE LEVER (D-302, FBV2-P2-004B2 no-casualty refinement).  AQROOT_U11_RETARGET=1 ->
target C36.1 (63.750,74.325) instead of D9.1.  U11.2's 0.20 mm SENSE closure is
KEPT unchanged (the 004A requested-connected key BAT_PROTECTED_P U11.2->(node)
role=SENSE is preserved -- nothing is lost), so by the time u11_escape() runs U11.2
is ALREADY on-net with the C36.1 node.  The wide C36.1 tap is therefore a
CURRENT-PATH REINFORCEMENT between already-joined points, judged by
reserve_gate(state['rn'], allow_dangle=False) -- DRC gains no class/count AND the
ratsnest is EXACTLY UNCHANGED -- not gate()'s ratsnest-fall.  Unset -> D9.1 trunk +
SENSE closure, byte-identical to every prior run.  This probe runs on the exact
final-run 004A board, which already carries the SENSE closure, so checks A/B/C
below measure precisely this reinforcement-between-already-joined-points state.

WHY THIS SAVED-BOARD SCREEN IS FAITHFUL (contrast the D-300 false proxy).  D-300's
proxy tested the EARLY (section 8b) LTC_GATE join on the FINAL board -- the wrong
board state, because the driver routes that join on a PARTIAL board.  u11_escape,
by contrast, genuinely runs LAST on this exact final board in the real run, so
running the SAME flare + connect_role geometry on the saved final-run 004A board
IS the real in-run state (the D-297 fixed-endpoint-mechanism class, not the D-300
path-choice class).

WHAT THIS PROBE MEASURES, on the exact final-run 004A board
`w/FULL003T_004a_ltcgate1/aqroot-Beta-v2.kicad_pcb`:

  A  REAL ROUTE.  escape(C36.1) + free_region + flare(U11.2) + connect_role
     (launch -> C36.1): B.Cu, 3.521 mm, min trunk width 1.500 mm.  The only
     sub-1.20 mm copper is the inherent flare neck AT the 0.20 mm-tall U11.2 pad
     (W_SENSE) -- the sanctioned BAT_PROT_ESCAPE_U11 pad-exit, identical to the
     default design; the trunk proper is >=1.20 mm.

  B  REAL KiCad DRC (project context beside the board).  Laying the retarget
     copper and growing BAT_PROT_ESCAPE_U11 to cover it (as gate() does): ZERO new
     DRC classes vs the board's own baseline (and the pre-existing track_width:1
     clears, absorbed by the wide tap + its corridor).

  C  >=1.20 mm CURRENT-PATH CONTINUITY.  KiCad connectivity: U11.2 <-> R75.2 True.
     A width-connected graph over BAT_PROTECTED_P copper (tracks >=1.20 mm joined
     through the 0.80 mm D-288 array vias) reaches from the C36.1 node through the
     1.30 mm bridge to the R75.2 escape -- so the tap lands on genuine >=1.20 mm
     current-carrying backbone, NOT a thin segment, a single fine via, or an
     accidental same-net island.

GOVERNANCE.  This probe proves the MECHANISM + current path on the real final
board; it does NOT promote copper.  Per D-286 the net gain / full PASS (does
u11_escape now return True so PHASE A PASSes?) is judged ONLY by the ~25 min
full-authority gate the CTO runs.
"""
import os
import sys
import math
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qrouter as QR
import path_role_util as RU
import battery_route_plan as PL

BOARD = os.path.join(HERE, 'w', 'FULL003T_004a_ltcgate1', 'aqroot-Beta-v2.kicad_pcb')
NET = PL.N + 'BAT_PROTECTED_P'
CP, CT_W = 200000, 300000
TARGET = 'C36.1'
WIDE_MIN = 1200000                      # D-249 BPP trunk floor
WIDE = frozenset(PL.N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                    'BAT_SENSE', 'BAT_PROTECTED_P'))

# Measured constants (record, so this file stands without the gitignored board).
REC = dict(route_ok=True, layer='B', mm=3.521, minw=1.500,
           drc_new_classes=0, track_width_before=1, track_width_after=0,
           u11_r75=True, wide_C36_to_R75=True, wide_component=31)

FAILED = []


def chk(name, ok, detail=''):
    print('  %-4s %-56s %s' % ('PASS' if ok else 'FAIL', name, detail))
    if not ok:
        FAILED.append(name)
    return ok


def main():
    print('u11_retarget_probe_004b (D-302): BAT_PROTECTED_P U11.2 -> C36.1 node tap')

    if not os.path.exists(BOARD):
        print('  (full-run board absent -- RECORD ONLY; measured: %s)' % REC)
        return 1 if FAILED else 0

    # Never mutate the preserved evidence board: work on a throwaway copy beside it.
    import shutil
    scratch = os.path.join(HERE, 'w', 'TEST004B_PROBE')
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch)
    src = os.path.dirname(BOARD)
    work_pcb = os.path.join(scratch, os.path.basename(BOARD))
    stem = os.path.splitext(os.path.basename(BOARD))[0]
    for n in (os.path.basename(BOARD), stem + '.kicad_dru', stem + '.kicad_pro',
              'fp-lib-table', 'sym-lib-table', 'libraries'):
        s = os.path.join(src, n)
        if os.path.exists(s):
            (shutil.copytree if os.path.isdir(s) else shutil.copy2)(
                s, os.path.join(scratch, n))

    ctx = all(os.path.exists(os.path.join(scratch, n)) for n in RU.NEEDED)
    base = None
    if ctx:
        base, _ = RU.drc(work_pcb, 'P004Bbase_%d' % os.getpid(), scratch)

    qb = QR.QBoard(work_pcb)
    qb.wide_nets = WIDE
    pads = {ref: pad for (net, ref), pad in qb.pads.items() if net == NET}

    chk('C36.1 is a BAT_PROTECTED_P node pad on the east backbone',
        TARGET in pads,
        'C36.1=(%.3f,%.3f)' % (pads[TARGET]['x'] / 1e6, pads[TARGET]['y'] / 1e6)
        if TARGET in pads else 'absent')

    # A -- real route: exactly u11_escape's geometry, retargeted to C36.1.
    m = qb.mark()
    eD = qb.escape(pads[TARGET], 'B', PL.W_TRUNK_BPP, PL.W_TRUNK_BPP,
                   CP, CT_W, 50000, qb.ex0, qb.ey0)
    regs = {}
    if eD:
        seed = (eD[0]['x'], eD[0]['y'])
        for w in (300000, 400000, 600000, 800000, 1000000, 1200000, PL.W_TRUNK_BPP):
            regs[w] = qb.free_region('B', NET, w, CP, CT_W, 50000, seed,
                                     qb.ex0 - 1000000, qb.ey0 - 1000000,
                                     qb.ex1 + 1000000, qb.ey1 + 1000000)
    f = qb.flare(NET, pads['U11.2'], 'B', PL.W_TRUNK_BPP, PL.W_SENSE,
                 CP, CT_W, 25000, region=regs)
    r = dict(ok=False, reason='NO_FLARE')
    if f is not None:
        lp = dict(ref='U11.2/launch', x=f['x'], y=f['y'], F=False, B=True,
                  shape=QR.RR(f['x'], f['y'], 1, 1, 0, 0, NET, 'launch'),
                  hx=1, hy=1, r=0, ang=0, net=NET, tht=False, anchor=True)
        for w in (PL.W_TRUNK_BPP, 1200000):
            r = QR.connect_role(qb, NET, lp, pads[TARGET], 'B', w, CP, CT_W)
            if r['ok']:
                break
    chk('A retarget routes U11.2 -> C36.1 on B.Cu at >=1.20 mm trunk width',
        bool(f) and r['ok'] and r['minw'] >= WIDE_MIN / 1e6 - 1e-6,
        ('ok %.3f mm minw=%.3f' % (r['mm'], r['minw'])) if r['ok']
        else ('flare=%s %s' % (bool(f), r.get('reason'))))
    newtrks = list(qb.laid[m[0]:]) if r['ok'] else []

    # B -- real KiCad DRC: grow BAT_PROT_ESCAPE_U11 over the new copper (gate()).
    if r['ok'] and ctx and base is not None:
        import pcbnew
        ps = RU.corridor_from_tracks(qb.b, newtrks)
        RU.set_area_poly(qb.b, 'BAT_PROT_ESCAPE_U11', ps)
        pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
        qb.save()
        after, det = RU.drc(work_pcb, 'P004Bafter_%d' % os.getpid(), scratch)
        new = {k: after[k] - base.get(k, 0) for k in after
               if after[k] > base.get(k, 0) and k != 'unconnected_items'}
        chk('B retarget adds ZERO new DRC classes', not new, 'new=%s' % (new or 'NONE'))

        # C -- >=1.20 mm current-path continuity on the routed board.
        b2 = pcbnew.LoadBoard(work_pcb)
        b2.BuildConnectivity()
        cn = b2.GetConnectivity()
        pp = {}
        for fp in b2.GetFootprints():
            for q in fp.Pads():
                pp[fp.GetReference() + '.' + q.GetNumber()] = q

        def joined(a, bb):
            s = {str(i.m_Uuid.AsString()) for i in cn.GetConnectedItems(pp[a])}
            return str(pp[bb].m_Uuid.AsString()) in s

        chk('C U11.2 is electrically joined to R75.2 (net connectivity)',
            joined('U11.2', 'R75.2'), 'U11.2<->R75.2=%s' % joined('U11.2', 'R75.2'))

        # width-connected graph over BAT_PROTECTED_P copper >=1.20 mm.  Two wide
        # tracks are joined where their endpoints coincide OR overlap within TOL
        # (abutting/overlapping wide copper is one conductor; the 1.50 mm trunk and
        # the 1.20 mm flare launch overlap with a 35 um endpoint offset).  0.80 mm
        # D-288 array vias share endpoints with the spokes, so they join too.
        TOL = 150000                       # 0.15 mm proximity merge
        pts = []                           # unique-ish endpoints of wide tracks
        edges = []                         # (i, j) same-track endpoints

        def node_id(x, y):
            for i, (px, py) in enumerate(pts):
                if math.hypot(px - x, py - y) <= TOL:
                    return i
            pts.append((x, y))
            return len(pts) - 1
        for t in b2.GetTracks():
            if t.GetNetname() != NET or t.GetClass() != 'PCB_TRACK':
                continue
            if t.GetWidth() < WIDE_MIN:
                continue
            a = node_id(t.GetStart().x, t.GetStart().y)
            c = node_id(t.GetEnd().x, t.GetEnd().y)
            edges.append((a, c))
        adj = collections.defaultdict(set)
        for a, c in edges:
            adj[a].add(c)
            adj[c].add(a)
        # proximity edges between any two nodes within TOL (overlapping copper)
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                if math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) <= TOL:
                    adj[i].add(j)
                    adj[j].add(i)
        start = node_id(pads[TARGET]['x'], pads[TARGET]['y'])
        r75 = node_id(pads['R75.2']['x'], pads['R75.2']['y'])
        launch = node_id(f['x'], f['y'])
        seen, stk = {start}, [start]
        while stk:
            u = stk.pop()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stk.append(v)
        chk('C >=1.20 mm copper links C36.1 node -> R75.2 (bridge backbone)',
            r75 in seen, 'reached=%s component=%d' % (r75 in seen, len(seen)))
        chk('C >=1.20 mm copper links C36.1 node -> the U11.2 flare launch',
            launch in seen, 'reached=%s' % (launch in seen))
    elif r['ok']:
        print('  (project context absent beside board -- skipping real DRC/continuity; '
              'measured: %s)' % REC)

    if FAILED:
        print('u11_retarget_probe_004b: %d CHECK(S) FAILED' % len(FAILED))
        return 1
    print('u11_retarget_probe_004b: ALL CHECKS PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
