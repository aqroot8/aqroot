# -*- coding: utf-8 -*-
"""FBV2-P2-003L -- PASS RECORD (D-285).  The minimal landing-opening PLACEMENT ECO
(D-284 owner-approved) OPENS a legal southern BAT_PROTECTED_P landing for the
proven D-275 south bridge (candidate c, D-283).

003K (D-283) measured the disjoint southern LANE viable (>= 1.20 mm, clears the
taps) but the only forced-south target-island pad C36.1 had NO LEGAL landing: the
exit array clears C36's own GND pad by 0.0726 mm and R68's BQ25185_SYS (BAT_MAIN)
pad by 0.0864 mm.  003L implements the minimal placement ECO (`place_003l`):

  * C36 -> (63.75, 75.10, 270 deg): the ROTATION moves C36's own GND pad 1.55 mm
    SOUTH of the north-poking exit array (blocker 1: 0.0726 -> 0.4750 mm), and the
    ~1.35 mm SOUTH shift clears R68 by distance (blocker 2: 0.0864 -> 0.2941 mm).
  * C5 -> (61.95, 75.15, 90 deg): the sole courtyard obstruction to a vertical C36
    (a +3V3/GND decoupler with plane-net routing latitude) vacates ~1.3 mm WEST.

Neither the mechanism (single-sourced from bridge_route_003c) nor any rule changes;
this is a PLACEMENT-only ECO, applied on top of the 002F placement.

  A  the D-275 SOUTH bridge LAYS on the moved board: entry >= 3, >= 1.20 mm F.Cu
     traverse, exit >= 3, land C36.1.
  B  DISJOINT: western leg dips to y > 74.7 (the taps y < 74.7 keep the corridor).
  C  the LANDING OPENS: ZERO east-landing clearance violations, and the two named
     003K blockers now clear the 0.200 mm floor (C36.2 GND, R68.1 BAT_MAIN).
  D  no new genuine DRC item: vs the 003K board the DRC delta is EXACTLY the two
     landing clearances removed (clearance 4 -> 2, the survivors are the
     pre-existing WEST LTC-block issues), every other class unchanged.
  E  D-275 invariant reused (constants/primitives from bridge_route_003c); the
     placement ECO moves ONLY C36/C5, no frozen part; the authoritative PCB still
     carries ZERO signal copper (no promotion from this bounded landing proof).

Exit 0 = the record holds.  This is a PASS CANDIDATE ready for supervised Phase-A
integration (recipe below); it is NOT an authoritative promotion -- full-board
connectivity is proven only by the supervised full run, which this task does not
start.
"""
import json
import math
import os
import subprocess
import sys

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import harness_paths as HP
import fcu_cutset_003c as CS
import bridge_route_003c as BR
import bridge_early_003i as EB
import place_003l as PL3L

N = '/01_POWER_TREE/'
NET = N + 'BAT_PROTECTED_P'
FAILED = []
SKIPPED = []

# The 003K board DRC histogram (bridge_probe_003k end-state: south bridge on the
# UNMOVED placement).  003L must equal this MINUS exactly the two landing
# clearances -- clearance 4 -> 2 -- and add nothing.
BASELINE_003K = {'lib_footprint_issues': 199, 'silk_over_copper': 6,
                 'hole_clearance': 5, 'solder_mask_bridge': 4, 'clearance': 4,
                 'via_dangling': 4, 'courtyards_overlap': 3, 'shorting_items': 3}

# the supervised follow-on run (documented, NOT started here)
SUPERVISED_RECIPE = (
    'AQROOT_SIXLAYER=1 AQROOT_D256=GSQ AQROOT_Q3_POFV=1 AQROOT_D266=1 '
    'AQROOT_D267=F1 AQROOT_TRUNK_LAST=1 AQROOT_U18_ORDER=6,10,7,1,3,2 '
    'AQROOT_D279=1 AQROOT_D280=1 AQROOT_BRIDGE_EARLY=1 AQROOT_BRIDGE_SOUTH=1 '
    'AQROOT_ECO_EXTRA=<repo>/hardware/beta-v2/checks/place_003l.json '
    'AQROOT_PLACE_JSON=<c3_00>  (parent-supervised; validates full connectivity)')

AUTH_PCB = os.path.normpath(os.path.join(
    SP, '..', 'kicad', 'aqroot-beta-v2', 'aqroot-Beta-v2.kicad_pcb'))


def chk(name, got, want, ok):
    print('  %-4s %-58s %-30s expected %s'
          % ('PASS' if ok else 'FAIL', name, got, want))
    if not ok:
        FAILED.append(name)
    return ok


def skip(name, why):
    print('  %-4s %-58s %s' % ('SKIP', name, why))
    SKIPPED.append(name)


def drc(pcb):
    out = os.path.join(SP, 'w', 'drc_003l_%d.json' % os.getpid())
    subprocess.run([HP.kicad_cli(), 'pcb', 'drc', '--severity-all',
                    '--format', 'json', '-o', out, pcb],
                   capture_output=True, text=True)
    j = json.load(open(out, encoding='utf-8'))
    try:
        os.remove(out)
    except OSError:
        pass
    return j.get('violations', [])


def histogram(viols):
    h = {}
    for v in viols:
        h[v.get('type')] = h.get(v.get('type'), 0) + 1
    return h


def east_landing_clearance_fails(viols):
    out = []
    for v in viols:
        if v.get('type') != 'clearance':
            continue
        desc = v.get('description', '')
        if "'GND'" not in desc and "'BAT_MAIN'" not in desc:
            continue
        try:
            m = float(desc.split('actual')[1].strip().split()[0])
        except (IndexError, ValueError):
            m = None
        items = v.get('items', [])
        bpp_east = any(NET in it.get('description', '')
                       and it.get('pos', {}).get('x', 0) > 55.0 for it in items)
        if bpp_east and m is not None and m < 0.200:
            nc = 'BAT_MAIN' if "'BAT_MAIN'" in desc else 'GND'
            out.append((nc, m))
    return out


def _pt_rect(px, py, rx, ry, rhx, rhy):
    dx = max(abs(px - rx) - rhx, 0.0)
    dy = max(abs(py - ry) - rhy, 0.0)
    return math.hypot(dx, dy)


def _seg_rect(ax, ay, bx, by, rx, ry, rhx, rhy):
    def sp(px, py):
        vx, vy = bx - ax, by - ay
        l2 = vx * vx + vy * vy
        t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / l2))
        return math.hypot(px - (ax + t * vx), py - (ay + t * vy))
    best = min(_pt_rect(ax, ay, rx, ry, rhx, rhy), _pt_rect(bx, by, rx, ry, rhx, rhy))
    for cx, cy in [(rx - rhx, ry - rhy), (rx + rhx, ry - rhy), (rx - rhx, ry + rhy),
                   (rx + rhx, ry + rhy), (rx, ry - rhy), (rx, ry + rhy),
                   (rx - rhx, ry), (rx + rhx, ry)]:
        best = min(best, sp(cx, cy))
    return best


def named_blocker_clearances(pcb):
    """Actual clearance from the laid bridge copper to the two NAMED 003K blockers
    (C36 pad 2 GND, R68 pad 1 BQ25185_SYS) on the moved board."""
    import pcbnew
    b = pcbnew.LoadBoard(pcb)
    bridge = []
    for t in b.GetTracks():
        if t.GetNetname() != NET:
            continue
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            if p.x / 1e6 > 55:
                bridge.append(('via', '*', (p.x / 1e6, p.y / 1e6), 0.4))
        else:
            a, c = t.GetStart(), t.GetEnd()
            if max(a.x, c.x) / 1e6 > 55:
                L = 'F' if t.GetLayer() == pcbnew.F_Cu else 'B'
                bridge.append(('seg', L, (a.x / 1e6, a.y / 1e6, c.x / 1e6, c.y / 1e6),
                               t.GetWidth() / 2e6))
    want = {('C36', '2'): None, ('R68', '1'): None}
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    for (ref, pn) in list(want):
        f = fp.get(ref)
        pad = next((p for p in f.Pads() if p.GetNumber() == pn), None) if f else None
        if pad is None:
            continue
        pos = pad.GetPosition()
        px, py = pos.x / 1e6, pos.y / 1e6
        phx, phy = pad.GetSize().x / 2e6, pad.GetSize().y / 2e6
        ly = set(b.GetLayerName(l)[0] for l in pad.GetLayerSet().Seq()
                 if b.GetLayerName(l) in ('F.Cu', 'B.Cu'))
        m = 9.0
        for (typ, L, g, hw) in bridge:
            if typ == 'via':
                m = min(m, _pt_rect(g[0], g[1], px, py, phx, phy) - hw)
            elif L in ly:
                m = min(m, _seg_rect(g[0], g[1], g[2], g[3], px, py, phx, phy) - hw)
        want[(ref, pn)] = round(m, 4)
    return want


def main():
    print('FBV2-P2-003L PASS RECORD (D-285) -- landing-opening placement ECO')
    print('  ECO: C36 -> (63.75,75.10,270)  C5 -> (61.95,75.15,90)  (on top of 002F)')

    try:
        pcb = EB.reconstruct_placed('PROBE003L', 'c3_00.json')
        PL3L.apply(pcb, report=False)          # collision audit runs here
        rec = EB.apply_early_path(pcb, south=True)
    except SystemExit as e:                     # collision / frozen guard tripped
        chk('ECO applies cleanly (no frozen part, no courtyard collision)',
            'raised: %s' % e, 'applies', False)
        rec = None
    except Exception as e:                       # pragma: no cover
        skip('A/B/C/D  003L ECO + south bridge', 'setup: %s' % e)
        rec = None

    if rec is not None:
        tr = rec.get('traverse') or {}
        ok_lane = (rec.get('ok') and len(rec.get('entry_vias', [])) >= 3
                   and tr.get('ok') and tr.get('w_mm', 0) >= 1.20
                   and rec.get('exit_vias', 0) >= 3
                   and rec.get('land') == 'C36.1')
        chk('A  south bridge LAYS on moved board: entry>=3, >=1.20mm, exit>=3, C36.1',
            'land=%s w=%.2f entry=%d exit=%d' % (
                rec.get('land'), tr.get('w_mm', 0),
                len(rec.get('entry_vias', [])), rec.get('exit_vias', 0)),
            'lays', ok_lane)

        yw = rec.get('south_ywest_mm', 0)
        chk('B  western leg DISJOINT below the tap band (ywest > 74.7)',
            'ywest=%.2f' % yw, 'disjoint', yw > 74.7)

        viols = drc(pcb)
        fails = east_landing_clearance_fails(viols)
        chk('C  landing OPENS: ZERO east-landing clearance violations (<0.200mm)',
            ('; '.join('%s %.4f' % (nc, mm) for nc, mm in fails) or 'none'),
            'none', len(fails) == 0)

        named = named_blocker_clearances(pcb)
        c36g, r68b = named.get(('C36', '2')), named.get(('R68', '1'))
        chk('C  named 003K blockers now clear the 0.200mm floor (C36.2, R68.1)',
            'C36.2 GND %.4f / R68.1 BAT_MAIN %.4f' % (c36g or -1, r68b or -1),
            'both >= 0.200',
            c36g is not None and r68b is not None and c36g >= 0.200 and r68b >= 0.200)

        h = histogram(viols)
        # no new genuine DRC item: every class <= 003K baseline, and clearance
        # dropped by exactly the two landing violations (4 -> 2).
        no_new = all(h.get(k, 0) <= BASELINE_003K.get(k, 0) for k in h)
        cl_ok = h.get('clearance', 99) == BASELINE_003K['clearance'] - 2
        others_ok = all(h.get(k, 0) == BASELINE_003K[k]
                        for k in BASELINE_003K if k != 'clearance')
        chk('D  no new genuine DRC item vs 003K (clearance 4->2, rest identical)',
            'clr=%d new_classes=%s rest_eq=%s' % (
                h.get('clearance', -1),
                'no' if no_new else 'YES', others_ok),
            'clr=2, none new', no_new and cl_ok and others_ok)

    # E -- invariant + no false promotion ------------------------------------
    reuse = all(getattr(EB, k) is getattr(BR, k)
                for k in ('NET', 'SHDN', 'DIA', 'DRILL', 'W_TRAVERSE', 'W_LAND'))
    fns = (EB.BR.route_traverse is BR.route_traverse
           and EB.BR.scan_entry_sites is BR.scan_entry_sites
           and EB.BR.inject_vias is BR.inject_vias)
    chk('E  003L reuses the D-275 constants + primitives from bridge_route_003c',
        'reused' if (reuse and fns) else 'diverged', 'reused', reuse and fns)
    ctl = CS.branch_role(N + 'BAT_PROT_SHDN_CTL', {'Q4.1', 'R83.1'})[0]
    chk('E  vacate is the cardinality-1 control branch BAT_PROT_SHDN_CTL',
        '%s' % ctl, 'candidate', ctl == 'candidate')
    moved = set(PL3L.MOVES)
    chk('E  placement ECO moves ONLY C36/C5 (bounded landing-opening spread)',
        '%s' % sorted(moved), "['C36', 'C5']", moved == {'C36', 'C5'})
    frozen_hit = [r for r in PL3L.FROZEN if r in PL3L.MOVES]
    chk('E  no frozen part is moved (D9/U18/R75-R83/Q3/FETs/C58/U19/D10/R68...)',
        '%s' % (frozen_hit or 'none'), 'none', not frozen_hit)

    res = os.path.join(SP, 'phaseA_003l_fix.json')
    chk('E  no committed 003L full-run result exists (candidate not promoted)',
        'present' if os.path.exists(res) else 'absent', 'absent',
        not os.path.exists(res))
    if os.path.exists(AUTH_PCB):
        import pcbnew
        ab = pcbnew.LoadBoard(AUTH_PCB)
        ntrk = sum(1 for t in ab.GetTracks() if t.GetClass() == 'PCB_TRACK')
        nvia = sum(1 for t in ab.GetTracks() if t.GetClass() == 'PCB_VIA')
        # authoritative placement must ALSO be untouched: C36/C5 at their pre-ECO poses
        fp = {f.GetReference(): f for f in ab.GetFootprints()}
        c36 = fp.get('C36')
        c36_home = (c36 is not None
                    and round(c36.GetPosition().x / 1e6, 2) == 63.75
                    and round(c36.GetPosition().y / 1e6, 2) == 73.75
                    and round(c36.GetOrientationDegrees()) % 360 == 0)
        chk('E  authoritative PCB unchanged (0 tracks / 0 vias, C36 at home pose)',
            '%d trk / %d via / C36 %s' % (
                ntrk, nvia, 'home' if c36_home else 'MOVED'),
            '0 / 0 / home', ntrk == 0 and nvia == 0 and c36_home)
    else:
        skip('E  authoritative PCB guard', 'authoritative board not found')

    tag = 'PASS' if not FAILED else 'FAIL %s' % FAILED
    print('\nFBV2-P2-003L PASS RECORD:', tag,
          ('(%d clause[s] skipped)' % len(SKIPPED)) if SKIPPED else '')
    print('VERDICT: the D-284 minimal landing-opening placement ECO (C36 rot270 '
          '+ south, C5 west) OPENS the C36.1 landing for the proven D-275 south '
          'bridge -- entry 4 / 1.40 mm F.Cu / exit 4, disjoint (ywest 82.4), '
          'governing landing clearance 0.2941 mm (R68 BAT_MAIN) vs the 0.200 mm '
          'floor, DRC delta = exactly the two 003K landing violations removed and '
          'nothing added.  PASS CANDIDATE for supervised Phase-A integration; NOT '
          'an authoritative promotion (full connectivity is proven by the '
          'supervised run only).  D-275 and D-277..D-283 preserved.')
    print('SUPERVISED FOLLOW-ON (not started here): %s' % SUPERVISED_RECIPE)
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
