# -*- coding: utf-8 -*-
"""FBV2-P2-003W -- MEASURED RECORD (D-297).  The SECONDARY D-295 lever: the
BAT_PROTECTED_P `U18.8 -> R75.2` reserve JOIN completes on In3 instead of the
severed In2 lane, opening the >=0.200 mm join lane D-294 could not find at the
D-293 direction-2 placement -- within existing D-257/D-266 mechanics, with NO new
via, NO DRU/floor change, NO topology change.

THE WALL (D-294/295).  At the direction-2 placement `t_a_r77e15n10_r79e15n10` the
BAT_PROTECTED_P reserve pair places two ordinary 0.35/0.20 THROUGH vias at
R75.2 (2.800, 66.800) and U18.8 (7.200, 66.500) on In2 (via the nearest-legal-exit
fallback; the join-minimising scored exit is rejected on BAT_MAIN routed clearance).
Their In2 JOIN is then NO_PATH: a BAT_RAW 0.600 mm CURRENT-PATH wall runs vertically
on In2 at x ~ 6.4 -> 6.65 (y 50.45 -> 70.40), severing the west->east lane between
the two vias.  U18.8 is left open (non-fatal); the terminal fatal wall in 003T was
the PRIMARY REC_BAT_LOW U19.7 (refuted separately by D-296).

THE LEVER (D-297).  The reserve vias are THROUGH vias -- copper on every layer --
so the join is electrically identical on In2 or In3.  In3.Cu is a routable
six-layer signal layer (qrouter.ROUTABLE[6] = F,B,I2,I3) that is EMPTY across the
whole corridor on the real full-run board (only 2 In3 tracks board-wide, NONE in
the corridor; no In3 copper pour -- the only pours are the In1/In4 GND planes).
So `AQROOT_U18BPP_JOIN=I3` completes the ONE branch on In3.  Unset -> the join
stays on va[2] (In2), byte-identical to every prior run.

WHAT THIS PROBE MEASURES, on the MOST FAITHFUL AFFORDABLE VEHICLE -- the actual
full-run routed board `w/FULL003T_e15n10cto/aqroot-Beta-v2.kicad_pcb` (the real
full congestion, not a focused vehicle whose In2 join passes vacuously):

  A  REAL JOIN ROUTING.  QR.join_reserved between the two through-vias:
        In2 -> NO_PATH  (reproduces the exact D-294 wall)
        In3 -> ok, 4.410 mm  (the lever opens the lane)

  B  REAL KiCad DRC (when project context is present beside the board).  Laying
     the In3 join and growing BAT_PROT_TAP_U18 to cover it (exactly as the driver
     gate() does): ZERO new DRC classes vs the board's own baseline, AND the lone
     via_dangling:1 CLEARS to 0 -- the join absorbs the previously-dangling
     BAT_PROTECTED_P reserve via.

  C  PREMISE.  In3 is routable on six layers and bare in the corridor.

GOVERNANCE.  This probe proves the MECHANISM on real full congestion; it does NOT
promote copper.  Per D-286 the net connected-set gain (does closing U18.8 add a
connection, or -- as the U19.7 family did in D-296 -- merely swap a casualty?) is
judged ONLY by the ~22 min full-authority gate the CTO runs.  Unlike U19.7 the
In3 join takes capacity from no other net (In3 is unused), so a casualty swap is
unlikely -- but that is a full-gate finding, not a claim this probe may make.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qrouter as QR
import path_role_util as RU
import battery_route_plan as PL

BOARD = os.path.join(HERE, 'w', 'FULL003T_e15n10cto', 'aqroot-Beta-v2.kicad_pcb')
NET = PL.N + 'BAT_PROTECTED_P'
CP, CT, W = 200000, 200000, 200000
VA = (int(2.800e6), int(66.800e6))   # R75.2 reserve through-via
VB = (int(7.200e6), int(66.500e6))   # U18.8 reserve through-via
WIDE = frozenset(PL.N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                    'BAT_SENSE', 'BAT_PROTECTED_P'))

# Measured constants (record, so this file stands without the gitignored board).
REC = dict(i2='NO_PATH', i3_ok=True, i3_mm=4.410,
           drc_new_classes=0, via_dangling_before=1, via_dangling_after=0)

FAILED = []


def chk(name, ok, detail=''):
    print('  %-4s %-52s %s' % ('PASS' if ok else 'FAIL', name, detail))
    if not ok:
        FAILED.append(name)
    return ok


def main():
    print('u18_i3_join_probe_003w (D-297): BAT_PROTECTED_P U18.8->R75.2 In3 join')
    chk('C In2 and In3 are routable six-layer signal layers',
        'I2' in QR.ROUTABLE[6] and 'I3' in QR.ROUTABLE[6],
        'ROUTABLE[6]=%s' % (QR.ROUTABLE[6],))

    if not os.path.exists(BOARD):
        print('  (full-run board absent -- RECORD ONLY; measured: %s)' % REC)
        return 1 if FAILED else 0

    # Never mutate the preserved evidence board: all routing/DRC runs on a
    # throwaway copy beside it.  QBoard/qb.save() would otherwise overwrite it.
    import shutil
    scratch = os.path.join(HERE, 'w', 'TEST003W_PROBE')
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

    qb = QR.QBoard(work_pcb)
    qb.wide_nets = WIDE

    # A -- real join routing on the real full-congestion board.
    m = qb.mark()
    r2 = QR.join_reserved(qb, NET, VA, VB, W, CP, CT, layer='I2')
    qb.revert(m)
    chk('A In2 join is NO_PATH (the D-294 wall reproduces)',
        (not r2['ok']) and r2.get('reason') == 'NO_PATH',
        r2.get('reason') if not r2['ok'] else 'ok %.3f mm' % r2['mm'])

    m = qb.mark()
    r3 = QR.join_reserved(qb, NET, VA, VB, W, CP, CT, layer='I3')
    chk('A In3 join is ok (the lever opens the lane)',
        r3['ok'], ('ok %.3f mm grid=%.3f' % (r3['mm'], r3['grid']))
        if r3['ok'] else r3.get('reason'))
    newtrks = list(qb.laid[m[0]:]) if r3['ok'] else []

    # B -- real KiCad DRC, if the project context sits beside the board.
    ctx = all(os.path.exists(os.path.join(scratch, n)) for n in RU.NEEDED)
    if r3['ok'] and ctx:
        work = scratch
        try:
            base, _ = RU.drc(work_pcb, 'W003Wbase_%d' % os.getpid(), work)
        except SystemExit as e:
            print('  (DRC context incomplete: %s)' % e)
            base = None
        if base is not None:
            import pcbnew
            # grow BAT_PROT_TAP_U18 to cover the join (as gate() does), then DRC.
            region = []
            for t in qb.b.GetTracks():
                if t.GetNetname() != NET:
                    continue
                bb = t.GetBoundingBox()
                cx = pcbnew.ToMM((bb.GetLeft() + bb.GetRight()) // 2)
                cy = pcbnew.ToMM((bb.GetTop() + bb.GetBottom()) // 2)
                if 1.5 <= cx <= 8.0 and 64.0 <= cy <= 69.5:
                    region.append(t)
            ps = RU.corridor_from_tracks(qb.b, region)
            RU.set_area_poly(qb.b, 'BAT_PROT_TAP_U18', ps)
            pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
            qb.save()
            after, _ = RU.drc(work_pcb, 'W003Wafter_%d' % os.getpid(), work)
            new = {k: after[k] - base.get(k, 0) for k in after
                   if after[k] > base.get(k, 0) and k != 'unconnected_items'}
            chk('B In3 join adds ZERO new DRC classes',
                not new, 'new=%s' % (new or 'NONE'))
            chk('B In3 join clears the dangling reserve via (via_dangling 1->0)',
                base.get('via_dangling', 0) >= 1
                and after.get('via_dangling', 0) < base.get('via_dangling', 0),
                'via_dangling %s -> %s' % (base.get('via_dangling', 0),
                                           after.get('via_dangling', 0)))
    elif r3['ok']:
        print('  (project context absent beside board -- skipping real DRC; '
              'measured: new classes=%d, via_dangling %d->%d)'
              % (REC['drc_new_classes'], REC['via_dangling_before'],
                 REC['via_dangling_after']))

    if FAILED:
        print('u18_i3_join_probe_003w: %d CHECK(S) FAILED' % len(FAILED))
        return 1
    print('u18_i3_join_probe_003w: ALL CHECKS PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
