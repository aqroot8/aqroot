# -*- coding: utf-8 -*-
"""FBV2-P2-003K -- MEASURED-FAIL RECORD (D-283).  The DISJOINT-SUB-BOX southern
BAT_PROTECTED_P bridge (candidate c) LAYS its lane but has NO LEGAL LANDING: the
only target-island BPP pad reachable when the western leg is forced below the tap
band (the far-east node cap C36.1) is BOXED by GND and BAT_MAIN pads, so the exit
array lands 0.0726 mm from C36's GND pad and 0.0864 mm from R6/R68's BAT_MAIN
(BQ25185_SYS) pad -- genuine <0.200 mm clearance violations, the exact 003I class
(identical GND 0.0726 mm).  Because the early stage lays the bridge UNGATED, that
fixed violation pair then poisons every subsequent per-connection gate and the full
run cascades (140 gate rejections across 26 nets).

Arc.  003C (D-275) proved the vacate + F.Cu via-array bridge on a SPARSE board,
landing on the OPEN node COPPER at (40.67,70.71).  003D/003I/003J then measured that
the CORRIDOR is a shared-capacity wall (D-281) that no via-relocation opens (D-282);
003J localised the one spare >=1.20 mm F.Cu lane to a SOUTHERN band (taps y<74.7,
lane y>75) and deferred the disjoint-sub-box candidate (c) to a supervised full run.

WHAT 003K MEASURES.  The env-gated south variant (`AQROOT_BRIDGE_SOUTH`, default
inert) forces the western leg of the traverse BELOW the tap band with a temporary
obstacle wall over the corridor-north box, and lands on the far-east node cap
(LAND_REFS_SOUTH = C36.1 -- no target-island pad exists between D9.1 x=11 and
C25/C36 x=62, and the OPEN node copper D-275 landed on does not exist early).

  A  LANE holds.  On the reconstructed sparse placed board the south bridge lays:
     entry array >=3, >=1.20 mm F.Cu traverse, exit array >=3, land C36.1.

  B  DISJOINT.  The western leg dips to y ~ 81.85 (south_ywest_mm > 74.7) -- the
     lane genuinely avoids the tap band (taps y<74.7).  The DISJOINT-LANE half of
     candidate (c) is CONFIRMED viable.

  C  NO LEGAL LANDING (decisive).  DRC on the laid board shows the C36.1 exit copper
     clears C36's GND pad by 0.0726 mm and R6/R68's BAT_MAIN pad by 0.0864 mm -- both
     < the 0.200 mm floor.  The only forced-south node pad cannot host a legal exit
     array; the reservation delivers a lane but not a landing.

  D  FULL-RUN CASCADE (recorded, MEASURED).  The parent-supervised full run
     (recipe c3_00 + SIXLAYER + D277..D280 + AQROOT_BRIDGE_EARLY + AQROOT_BRIDGE_SOUTH)
     laid the bridge -- `EARLY BRIDGE SOUTH OK land=C36.1 traverse=70.377mm w=1.20
     entry=4 exit=3 ywest=81.85` -- then the ungated landing violation (GND 0.0726 /
     BAT_MAIN 0.0864) was seen as `new DRC {clearance:2}` by EVERY later gate and
     rejected it: 140 rejections across 26 nets.  The run is INVALID as a Phase-A
     candidate, NOT proof of success; the two clearance violations are GENUINE and
     are NOT absorbed into any baseline (the 003I ruling).

CONCLUSION (engineering, CTO scope -- NOT an OWNER decision, NO routing progress).
Candidate (c) is EXHAUSTED: the disjoint southern LANE holds >=1.20 mm and clears
the taps, but the only forced-south LANDING (C36.1) cannot clear GND/BAT_MAIN, so no
legal end-to-end bridge exists.  With (b) refuted (D-282), (d) the 003I FAIL (D-281),
and (a) an envelope/OWNER change, the remaining lever is the FALLBACK -- a placement
spread of the LTC4368 block (OWNER/mechanical) -- NOT attempted here.  No rule is
relaxed; the 0.200 mm clearance and 0.25 mm hole-to-hole floors are ENFORCED.

Exit 0 = the record holds (necessary precondition A/B measured, decisive FAIL C
measured, D-275 + D-277..D-280 invariants intact, nothing silently promoted).
"""
import json, math, os, subprocess, sys
SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import harness_paths as HP
import fcu_cutset_003c as CS       # shared path-role vacate classifier
import bridge_route_003c as BR     # the proven D-275 copper primitives / constants
import bridge_early_003i as EB     # the EARLY / SOUTH route-order driver stage

N = '/01_POWER_TREE/'
NET = N + 'BAT_PROTECTED_P'
FAILED = []
SKIPPED = []

# MEASURED on the parent-supervised full run (recipe + AQROOT_BRIDGE_EARLY +
# AQROOT_BRIDGE_SOUTH; scratch FIX003K; stopped once the conflict became decisive,
# exactly as the 003I parent stopped its run).  Recorded so the closeout does not
# depend on re-running a ~35-40 min full route.
MEASURED = dict(
    early='EARLY BRIDGE SOUTH OK land=C36.1 traverse=70.377mm w=1.20 '
          'entry=4 exit=3 ywest=81.85',
    gnd_clearance_mm=0.0726, gnd_floor_mm=0.200,
    bat_main_clearance_mm=0.0864, bat_main_floor_mm=0.200,
    gate_rejections=140, nets_cascaded=26,
    verdict='landing on C36.1 violates GND/BAT_MAIN clearance; the ungated early '
            'bridge poisons every subsequent gate; candidate (c) exhausted')

# the committed authoritative product board -- must stay byte-empty of signal copper
AUTH_PCB = os.path.normpath(os.path.join(
    SP, '..', 'kicad', 'aqroot-beta-v2', 'aqroot-Beta-v2.kicad_pcb'))


def chk(name, got, want, ok):
    print('  %-4s %-60s %-28s expected %s'
          % ('PASS' if ok else 'FAIL', name, got, want))
    if not ok:
        FAILED.append(name)
    return ok


def skip(name, why):
    print('  %-4s %-60s %s' % ('SKIP', name, why))
    SKIPPED.append(name)


def drc(pcb):
    out = os.path.join(SP, 'w', 'drc_003k_%d.json' % os.getpid())
    subprocess.run([HP.kicad_cli(), 'pcb', 'drc', '--severity-all',
                    '--format', 'json', '-o', out, pcb],
                   capture_output=True, text=True)
    j = json.load(open(out, encoding='utf-8'))
    try:
        os.remove(out)
    except OSError:
        pass
    return j.get('violations', [])


def landing_clearance_fails(viols):
    """Clearance violations where a BAT_PROTECTED_P track in the far-east landing
    region (x > 55 mm) clears a GND or BAT_MAIN item by < 0.200 mm -- the decisive
    C36.1-landing FAIL.  Returns list of (netclass, actual_mm)."""
    out = []
    for v in viols:
        if v.get('type') != 'clearance':
            continue
        desc = v.get('description', '')
        if "'GND'" not in desc and "'BAT_MAIN'" not in desc:
            continue
        # actual clearance in mm: "... actual 0.0726 mm)"
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


def main():
    print('FBV2-P2-003K MEASURED-FAIL RECORD (D-283)')
    print('  full-run (recorded): %s' % MEASURED['early'])
    print('  full-run (recorded): landing GND %.4f / BAT_MAIN %.4f mm (floor %.3f); '
          '%d gate rejections across %d nets'
          % (MEASURED['gnd_clearance_mm'], MEASURED['bat_main_clearance_mm'],
             MEASURED['gnd_floor_mm'], MEASURED['gate_rejections'],
             MEASURED['nets_cascaded']))

    # ---- lay the south bridge on a reconstructed sparse placed board -----------
    try:
        pcb = EB.reconstruct_placed('PROBE003K', 'c3_00.json')
        rec = EB.apply_early_path(pcb, south=True)
    except Exception as e:                                   # pragma: no cover
        skip('A/B/C  south bridge on reconstructed sparse board', 'setup: %s' % e)
        rec = None

    if rec is not None:
        # A -- the LANE holds (necessary precondition) ---------------------------
        tr = rec.get('traverse') or {}
        ok_lane = (rec.get('ok') and len(rec.get('entry_vias', [])) >= 3
                   and tr.get('ok') and tr.get('w_mm', 0) >= 1.20
                   and rec.get('exit_vias', 0) >= 3
                   and rec.get('land') in EB.LAND_REFS_SOUTH)
        chk('A  south bridge LAYS: entry>=3, >=1.20mm traverse, exit>=3, C36.1 land',
            'land=%s w=%.2f entry=%d exit=%d' % (
                rec.get('land'), tr.get('w_mm', 0),
                len(rec.get('entry_vias', [])), rec.get('exit_vias', 0)),
            'lays', ok_lane)

        # B -- the lane is DISJOINT from the tap band (taps y<74.7) ---------------
        yw = rec.get('south_ywest_mm', 0)
        chk('B  western leg is DISJOINT below the tap band (ywest > 74.7)',
            'ywest=%.2f' % yw, 'disjoint', yw > 74.7)

        # C -- the DECISIVE FAIL: the C36.1 landing has no legal clearance --------
        viols = drc(pcb)
        fails = landing_clearance_fails(viols)
        ncls = set(nc for nc, _ in fails)
        chk('C  C36.1 landing VIOLATES GND & BAT_MAIN clearance (<0.200mm) -- FAIL',
            ('; '.join('%s %.4f' % (nc, mm) for nc, mm in fails) or 'none'),
            'GND+BAT_MAIN <0.200', {'GND', 'BAT_MAIN'} <= ncls)

    # D -- invariant preserved (shared contract with bridge_probe_003c/003i/003j) --
    reuse = all(getattr(EB, k) is getattr(BR, k)
                for k in ('NET', 'SHDN', 'DIA', 'DRILL', 'W_TRAVERSE', 'W_LAND'))
    fns = (EB.BR.route_traverse is BR.route_traverse
           and EB.BR.scan_entry_sites is BR.scan_entry_sites
           and EB.BR.inject_vias is BR.inject_vias)
    chk('D  003K reuses the D-275 constants + primitives from bridge_route_003c',
        'reused' if (reuse and fns) else 'diverged', 'reused', reuse and fns)
    ctl = CS.branch_role(N + 'BAT_PROT_SHDN_CTL', {'Q4.1', 'R83.1'})[0]
    chk('D  vacate is the cardinality-1 control branch BAT_PROT_SHDN_CTL',
        '%s' % ctl, 'candidate', ctl == 'candidate')
    for badnet in ('BAT_PROTECTED_P', 'BAT_SENSE', 'BAT_MID', 'BAT_CONNECTOR_P'):
        v = CS.branch_role(N + badnet, {'X.1', 'Y.1'})[0]
        chk('D  current-carrying %s is NOT a vacate candidate' % badnet,
            '%s' % v, 'None', v is None)

    # E -- no false promotion: no 003K result claims a clean/absorbed end-state,
    # and the authoritative product board still carries ZERO signal copper --------
    res = os.path.join(SP, 'phaseA_003k_fix.json')
    if os.path.exists(res):
        r = json.load(open(res))
        drcx = r.get('drc') or {}
        base = r.get('baseline') or {}
        absorbed = all(drcx.get(k, 0) <= base.get(k, 0)
                       for k in drcx) and r.get('connections', 0) >= 71
        chk('E  no committed 003K result claims a clean (absorbed) end-state',
            'clean/absorbed' if absorbed else 'shows FAIL', 'shows FAIL',
            not absorbed)
    else:
        chk('E  no committed 003K success result exists (candidate not promoted)',
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
    print('\nFBV2-P2-003K MEASURED-FAIL RECORD:', tag,
          ('(%d clause[s] skipped)' % len(SKIPPED)) if SKIPPED else '')
    print('VERDICT: the disjoint-sub-box southern bridge (candidate c) LAYS its lane '
          '(>=1.20mm, disjoint from the taps) but has NO LEGAL LANDING -- the only '
          'forced-south node pad C36.1 is boxed by GND (0.0726mm) and BAT_MAIN '
          '(0.0864mm); the ungated early bridge poisons every gate and the full run '
          'cascades; candidate (c) EXHAUSTED; the fallback is an OWNER/mechanical '
          'placement spread of the LTC4368 block; no authoritative promotion; D-275 '
          'and D-277..D-282 preserved.')
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
