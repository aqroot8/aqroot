# -*- coding: utf-8 -*-
"""FBV2-P2-003D / D-275 -- the PRODUCTION driver stage of the western-corridor
vacate ECO + F.Cu high-current via-array bridge for BAT_PROTECTED_P.

003C proved the mechanism on a hand-staged reproduced board (bridge_route_003c +
bridge_gates_003c: PR-40 111111101 -> 111111111, bit 8 R75.2->U11.2 CLOSED, U18
8/8, no new DRC, ratsnest -1).  That was a POST-PROCESS of a manually staged
board, NOT a full Phase-A driver PASS.  003D integrates the exact same proven
mechanism as an in-line driver stage: route_battery_block.py routes the full
board, then -- guarded by AQROOT_BRIDGE_ECO -- calls apply_eco() on its own freshly
routed board before the authoritative DRC / ratsnest / result are recorded.

The copper-laying primitives are imported VERBATIM from the committed-proven
bridge_route_003c (no re-implementation, single source of truth):

  VACATE   move the 6 F.Cu tracks of BAT_PROT_SHDN_CTL (a microamp SHDN control
           signal) to In3.Cu; its end transitions are already through vias so
           Q4.1 -B- via -In3- via -B- R83.1 continuity is preserved.
  BRIDGE   4x 0.80/0.40 through-via ENTRY array on R75.2 (POFV) + >= 1.20 mm F.Cu
           TRAVERSE across the vacated corridor + 4x through-via EXIT array on the
           eastern BPP node -- an array landing, no single via carries pack
           current.

apply_eco() operates IN PLACE on the given board and first snapshots the pre-ECO
board next to it (pre_eco.kicad_pcb) so the two-pass gate can compare pre/post
within a single driver run.  D-275 constraints are preserved exactly: cardinality-1
control vacate, the trunk never on an inner layer, the array floor >= 3.
"""
import os, math, shutil, json
import pcbnew
import qrouter as QR
import path_role_util as RU
import bridge_route_003c as BR

# proven constants, single-sourced from the 003C mechanism
NET, SHDN = BR.NET, BR.SHDN
DIA, DRILL = BR.DIA, BR.DRILL
CP, CTW = BR.CP, BR.CTW
W_TRAVERSE, W_LAND = BR.W_TRAVERSE, BR.W_LAND
NODE_AIM = BR.NODE_AIM
WIDE = frozenset(BR.N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                    'BAT_SENSE', 'BAT_PROTECTED_P'))


def apply_eco(pcb, snapshot=True):
    """Vacate BAT_PROT_SHDN_CTL off F.Cu and lay the F.Cu via-array bridge on the
    board at path `pcb`, in place.  Returns a result dict; rec['ok'] is True iff
    the full bridge (entry array >= 3, >= 1.20 mm traverse, exit array >= 3) laid.

    If `snapshot`, the pre-ECO board is copied to pre_eco.kicad_pcb in the same
    directory (the gate baseline)."""
    rec = {'stage': 'FBV2-P2-003D bridge ECO', 'board': pcb, 'ok': False}
    if snapshot:
        pre = os.path.join(os.path.dirname(pcb), 'pre_eco.kicad_pcb')
        shutil.copyfile(pcb, pre)
        # copy the .kicad_dru rules sibling so the snapshot is fully DRC-able
        dru = pcb[:-len('.kicad_pcb')] + '.kicad_dru'
        if os.path.exists(dru):
            shutil.copyfile(dru, pre[:-len('.kicad_pcb')] + '.kicad_dru')
        rec['pre_eco'] = pre

    # ---- VACATE (cardinality 1: the SHDN control branch off F.Cu -> In3) -----
    moved = BR.vacate(pcb)
    rec['vacated'] = moved
    print('  ECO VACATE: moved %d %s F.Cu tracks -> In3.Cu'
          % (moved, SHDN.split('/')[-1]))
    if moved == 0:
        rec['fail'] = 'no BAT_PROT_SHDN_CTL F.Cu copper to vacate'
        print('  ECO ABORT:', rec['fail'])
        return rec

    qb = QR.QBoard(pcb)
    qb.wide_nets = WIDE
    nvia = BR.inject_vias(qb)
    rec['existing_vias'] = nvia

    # ---- ENTRY ARRAY on R75.2 (POFV) -----------------------------------------
    entry_vias = BR.scan_entry_sites(qb)
    if len(entry_vias) < 3:
        rec['fail'] = 'entry array below floor 3 (%d sites)' % len(entry_vias)
        print('  ECO ABORT:', rec['fail'])
        return rec
    for (x, y) in entry_vias:
        qb.via(NET, x, y, DIA, DRILL)
    ex = sorted(x for x, y in entry_vias)
    ey0 = int(sum(y for x, y in entry_vias) / len(entry_vias))
    qb.track(NET, 'F', ex[0], ey0, ex[-1], ey0, W_TRAVERSE)
    entry_bus = (ex[-1], ey0)
    rec['entry_vias'] = [[round(x / 1e6, 3), round(y / 1e6, 3)]
                         for x, y in entry_vias]
    print('  ECO ENTRY: %d vias on R75.2 pad + %.2f mm F.Cu bus'
          % (len(entry_vias), W_TRAVERSE / 1e6))

    # ---- F.Cu TRAVERSE from entry bus to the node landing --------------------
    nb = RU.nearest_on_net(qb.b, NET, 'B.Cu', NODE_AIM[0], NODE_AIM[1])
    if nb is None:
        rec['fail'] = 'no node B.Cu copper near aim'
        print('  ECO ABORT:', rec['fail'])
        return rec
    nd, npx, npy, ntrack = nb
    exit_centroid = (npx, npy - 900000)
    wtrav = None
    for w in (1500000, 1400000, 1300000, 1200000):
        ok, mm, npts = BR.route_traverse(qb, entry_bus[0], entry_bus[1],
                                         exit_centroid[0], exit_centroid[1], w)
        if ok:
            wtrav = w
            break
    if wtrav is None:
        rec['fail'] = 'no >= 1.20 mm F.Cu traverse corridor'
        rec['traverse'] = dict(ok=False)
        print('  ECO ABORT:', rec['fail'])
        return rec
    rec['traverse'] = dict(ok=True, mm=round(mm, 3), w_mm=wtrav / 1e6, pts=npts)
    print('  ECO TRAVERSE: %.3f mm F.Cu at %.2f mm, %d pts'
          % (mm, wtrav / 1e6, npts))

    # ---- EXIT ARRAY: vias around the drop, tied to the node B.Cu copper ------
    exit_sites = [(npx - 450000, npy - 1350000), (npx + 450000, npy - 1350000),
                  (npx - 450000, npy - 450000), (npx + 450000, npy - 450000)]
    laid = 0
    for (x, y) in exit_sites:
        free = all(qb.point_free(L, NET, x, y, DIA, CP, CTW, 25000)
                   for L in qb.cu)
        if not free or not BR.hole_clear(qb, x, y):
            continue
        qb.via(NET, x, y, DIA, DRILL)
        qb.track(NET, 'F', exit_centroid[0], exit_centroid[1], x, y, W_LAND)
        qb.track(NET, 'B', x, y, npx, npy, W_LAND)
        laid += 1
    rec['exit_vias'] = laid
    print('  ECO EXIT: %d vias landed on node' % laid)
    if laid < 3:
        rec['fail'] = 'exit array below floor 3 (%d landed)' % laid
        print('  ECO ABORT:', rec['fail'])
        return rec
    RU.split_at(qb.b, ntrack, npx, npy)

    pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
    qb.save()
    rec['ok'] = True
    print('  ECO OK: vacate(%d) + entry(%d)/traverse(%.2fmm)/exit(%d) bridge laid'
          % (moved, len(entry_vias), wtrav / 1e6, laid))
    return rec


if __name__ == '__main__':
    import sys
    b = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'w', 'phaseA003d',
        'aqroot-Beta-v2.kicad_pcb')
    r = apply_eco(b)
    print(json.dumps(r, indent=1))
    raise SystemExit(0 if r.get('ok') else 1)
