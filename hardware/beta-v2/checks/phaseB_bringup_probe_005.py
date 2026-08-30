# -*- coding: utf-8 -*-
"""FBV2-P2-005 / D-303 -- Phase-B BRING-UP probe on the first promoted
authoritative Phase-A board (HEAD 01a38a5 / D-302).

READ-ONLY.  Nothing here mutates the authoritative board, the shared journal or
any tracked file -- it only LOADS and MEASURES.  It records three things the
Phase-B bring-up established, so a fresh session does not have to re-derive them
and does not naively re-run the STALE replay machinery:

  1. INTEGRITY -- the promoted board matches the D-302 fingerprints exactly
     (sha256, 432 tracks / 54 vias / 6 layers, 77-entry journal) and every
     routed track is an in-scope power-tree net (Phase-A battery block ONLY).

  2. THE STALE PHASE-B REPLAY MACHINERY -- the two "Phase B" drivers in this
     repo predate the D-297/D-299/D-301/D-302 levers and assume a copper-EMPTY
     authoritative base, so they cannot faithfully reproduce or verify the
     promoted board:
       (a) replay_battery_block.py refuses a non-empty authoritative board
           ("authoritative board already carries N track items"); post-D-302
           the board carries 432 tracks, so it can never run again -- its
           promotion role is already fulfilled byte-identically by D-302.
       (b) route_battery_block.py SECTION 17 (AQROOT_REPLAY) drives from the
           journal but SKIPS every role=='TRUNK+ESCAPE' entry -- which is
           EXACTLY the one entry (BAT_PROTECTED_P U11.2->C36.1, w=1.5,
           reinforcement=True) that the D-302 lever added to CLOSE the terminal
           wall and define the promotion.  A replay would carry 76 of 77 items,
           dropping the wall closure, and would NOT reproduce the promoted board.

  3. THE REAL REMAINING PHASE-B -- the rest-of-board net inventory (every
     multi-pad net that is NOT in the battery-block power-tree scope, grouped by
     schematic sheet).  This is the substantive remaining routing and needs a
     NEW scoped, INCREMENTAL driver that preserves the accepted Phase-A copper.

The promotion itself is SOUND regardless of the stale replay machinery: the
authoritative board is byte-identical to a scratch produced by a GENUINE
full-authority Phase-A gate (run_003t_full.sh 004b2, DRIVER_EXIT=0, PHASE A
COMPLETE) -- a real driver in the real order, not a proxy (D-286) -- with real
KiCad DRC showing zero new copper classes and router_regression ALL PASS.

    python3 phaseB_bringup_probe_005.py
"""
import os, sys, json, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')

# Authoritative fingerprints.  This is a LIVE integrity probe: it tracks the
# current promoted board (the frozen per-milestone evidence lives in the audits).
# Updated at FBV2-P2-008 / D-306, which promoted the THIRD rest-of-board
# incremental increment (the DISP_RST_N display-reset control net) onto the
# D-305 board: 432 Phase-A + 20 FRONT_RGB + 31 ACC_3V3_CTL + 11 DISP_RST_N = 494
# tracks; the FIRST increment to add a VIA (54 -> 55, the F<->B cross-layer
# through via) and to re-pour the In1/In4 GND planes for its anti-pad; journal
# 77 + 3 + 4 + 2 REST_INC = 86.
EXPECT_SHA = '9c0586d824f92542c34fd12de1f6f8d4bdd8aaaab656c823eec40d6ae3f62259'
EXPECT_TRACKS = 494
EXPECT_VIAS = 55
EXPECT_LAYERS = 6
EXPECT_JOURNAL = 86

# Rest-of-board nets promoted as accepted incremental increments (D-304 onward).
ACCEPTED_REST = set("""FRONT_RGB_R_N FRONT_RGB_G_N FRONT_RGB_B_N
ACC_3V3_EN ACC_3V3_ILIM DISP_RST_N""".split())

N = '/01_POWER_TREE/'
SCOPE = set("""BAT_CONNECTOR_P BAT_RAW BAT_MID BAT_SENSE BAT_PROTECTED_P
LTC_GATE LTC_GATE_RC LTC_OV LTC_UV LTC_SHDN LTC4368_FAULT_N BAT_PROT_SHDN_CTL
Q2_CS Q3_CS VBRIDGE_TOP VREF_TOP REF_HO REF_POL N_POL N_BATDIV VREC_VCC
REC_GATE_N REC_POL_OK REC_AND1 REC_AND2 REC_BAT_LOW REC_FAULT_B REC_LIM_IN
REC_DIODE_IN GND""".split())


def in_scope(nm):
    s = nm[len(N):] if nm.startswith(N) else nm
    return nm.startswith(N) and s in SCOPE


def main():
    fails = []

    def chk(name, cond, detail=''):
        print('  %s %s %s' % ('PASS' if cond else '**FAIL**', name, detail))
        if not cond:
            fails.append(name)

    # ------------------------------------------------------------- 1. INTEGRITY
    print('-- 1. INTEGRITY: promoted board matches the D-306 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == current record (D-306)', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d' % EXPECT_TRACKS, len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d' % EXPECT_VIAS, len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == %d' % EXPECT_LAYERS, b.GetCopperLayerCount() == EXPECT_LAYERS,
        str(b.GetCopperLayerCount()))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d' % EXPECT_JOURNAL, len(jr) == EXPECT_JOURNAL, str(len(jr)))

    def routable_ok(nm):
        return in_scope(nm) or nm.split('/')[-1] in ACCEPTED_REST
    oos = [t for t in trk if not routable_ok(t.GetNetname())]
    inc_trk = [t for t in trk if t.GetNetname().split('/')[-1] in ACCEPTED_REST]
    chk('every routed track is Phase-A power-tree OR an accepted rest increment',
        not oos, '%d out-of-scope; %d accepted-increment tracks' % (len(oos), len(inc_trk)))

    # --------------------------------------------- 2. STALE REPLAY MACHINERY
    print('\n-- 2. STALE PHASE-B REPLAY MACHINERY (copper-empty-base assumptions) --')
    rb = open(os.path.join(SP, 'replay_battery_block.py'), encoding='utf-8').read()
    chk('replay_battery_block.py refuses a non-empty authoritative board',
        'already carries' in rb and 'raise SystemExit' in rb,
        '(copper-empty-base guard present)')

    reinf = [e for e in jr if e.get('role') == 'TRUNK+ESCAPE']
    is_u11 = (len(reinf) == 1 and reinf[0].get('a') == 'U11.2'
              and reinf[0].get('b') == 'C36.1'
              and bool(reinf[0].get('reinforcement')))
    chk('the D-302 wall-closure entry is role TRUNK+ESCAPE (U11.2->C36.1 reinf)',
        is_u11, str([(e.get('a'), e.get('b'), e.get('role')) for e in reinf]))
    rbb = open(os.path.join(SP, 'route_battery_block.py'), encoding='utf-8').read()
    skips = "role') == 'TRUNK+ESCAPE'" in rbb and 'continue' in rbb
    newq = [e for e in jr if e.get('role') != 'TRUNK+ESCAPE']
    chk('SECTION-17 replay SKIPS TRUNK+ESCAPE -> drops the wall closure',
        skips and len(newq) == EXPECT_JOURNAL - 1,
        'replay newq=%d of %d (omits the U11 reinforcement)' % (len(newq), len(jr)))

    # ------------------------------------------- 3. REAL REMAINING PHASE-B
    print('\n-- 3. REAL REMAINING PHASE-B: rest-of-board net inventory --')
    padnets = collections.defaultdict(int)
    for f in b.GetFootprints():
        for p in f.Pads():
            nm = p.GetNetname()
            if nm:
                padnets[nm] += 1
    trk_by_net = collections.Counter(t.GetNetname() for t in trk)
    rest = [(nm, n) for nm, n in padnets.items() if n >= 2 and not in_scope(nm)]
    routed_rest = [nm for nm, n in rest if trk_by_net[nm] > 0]
    accepted_routed = [nm for nm in routed_rest if nm.split('/')[-1] in ACCEPTED_REST]
    chk('the only routed rest-of-board nets are accepted increments (D-306: FRONT_RGB + ACC_3V3_CTL + DISP_RST_N)',
        sorted(routed_rest) == sorted(accepted_routed),
        '%d rest nets, %d routed (=%d accepted), %d still unrouted'
        % (len(rest), len(routed_rest), len(accepted_routed), len(rest) - len(routed_rest)))
    sheets = collections.Counter()
    padsum = collections.Counter()
    for nm, n in rest:
        parts = nm.split('/')
        pref = parts[1] if nm.startswith('/') and len(parts) > 1 else '(top)'
        sheets[pref] += 1
        padsum[pref] += n
    inv = {pref: dict(nets=sheets[pref], pads=padsum[pref])
           for pref in sheets}
    for pref, cnt in sheets.most_common():
        print('     %-28s nets=%-4d pads=%d' % (pref, cnt, padsum[pref]))

    res = dict(
        sha256=sha, tracks=len(trk), vias=len(via),
        copper_layers=b.GetCopperLayerCount(), journal=len(jr),
        power_tree_routed_nets=len(set(t.GetNetname() for t in trk)),
        rest_of_board_nets=len(rest), rest_of_board_routed=len(routed_rest),
        rest_by_sheet=inv, fails=fails)
    json.dump(res, open(os.path.join(SP, 'phaseB_bringup_005.json'), 'w'), indent=1)
    print('\nPHASE-B BRING-UP PROBE: %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
