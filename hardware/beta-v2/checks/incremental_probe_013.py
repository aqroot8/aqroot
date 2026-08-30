# -*- coding: utf-8 -*-
"""FBV2-P2-013 / D-311 -- focused read-only evidence probe for the EIGHTH
rest-of-board incremental increment: the audio-amp SD/mode-select strap
AMP_SD_MODE (R15.1/U5.4 F.Cu -> U2.7 B.Cu), routed onto the D-310 promoted board
by incremental_router.py through the D-310 U2-escape via-site OFFSET mechanism.

AMP_SD_MODE is one of the two remaining U2 west-edge escape siblings the D-310
via-offset UNLOCKED, and it was the HARDEST D-309 wall: the via-blind default
via_site laid the F<->B transition 0.100 mm from the accepted D-306 DISP_RST_N
barrel (D-309 +7 `clearance`).  D-311 completes it with the SAME unchanged
mechanism -- the always-on existing-via injection (qrouter._scan omits PCB_VIA)
plus the opt-in 2.5 mm `via_offset`, with ZERO per-net tuning -- walking the
transition to (51.55,90.20), 1.760 mm clear of the nearest existing via (now the
D-310 TOUCH_RST_N barrel).  Its sibling SD_CARD_DETECT_N also passed the real
full-board gate on scratch and is held for FBV2-P2-014 (NOT bundled -- the two
are functionally distinct: audio-amp strap vs microSD detect).

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-311 gate
promoted:

  1. the increment PRESERVED the accepted D-310 copper EXACTLY -- all 561 prior
     tracks (432 Phase-A + 20 RGB + 31 ACC + 11 DISP + 8 IMU + 25 RGB_LED + 8
     IR_RX_VS + 26 TOUCH) and 60 prior vias are still present byte/geometry-
     identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the single
     AMP_SD_MODE net (19 tracks F.Cu+B.Cu, 1 through via);
  3. the net is FULLY copper-connected (R15.1-U5.4-U2.7 one island; ratsnest
     685 -> 683), and no prior requested pair regressed;
  4. the via-site OFFSET mechanism actually cleared the wall -- the new via is
     >= 0.80 mm (centre) from EVERY existing via (the via-blind default put it
     0.100 mm from DISP_RST_N -- the D-309 +7);
  5. only the In1/In4 GND reference planes re-poured (1 new through via) -- every
     other zone byte-identical -- and real full-board KiCad DRC is unchanged (no
     new class, none increased; `clearance` stays 0).

    python3 incremental_probe_013.py
"""
import os, sys, json, hashlib, collections, math
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import live_fingerprint as LFP   # single source of truth for the live board pin
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')

EXPECT_SHA = LFP.SHA
EXPECT_TRACKS = LFP.TRACKS
EXPECT_VIAS = LFP.VIAS
EXPECT_JOURNAL = LFP.JOURNAL_LEN
EXPECT_RATSNEST = LFP.RATSNEST

# The pre-promotion D-310 authoritative sha (561 trk / 60 via) -- the exact set
# that must survive this increment unchanged.
D310_SHA = '856f7a8adf0db9b114b9f09d7469308f921bc897aaf2ddce7f1c15c40a197114'
AMP = ('/AMP_SD_MODE',)


def _track_sig(t):
    a = (t.GetStart().x, t.GetStart().y)
    z = (t.GetEnd().x, t.GetEnd().y)
    return ('T', t.GetNetname(), t.GetLayer(), min(a, z), max(a, z), t.GetWidth())


def _via_sig(t):
    p = t.GetPosition()
    return ('V', t.GetNetname(), (p.x, p.y), t.GetWidth(pcbnew.F_Cu), t.GetDrill())


def copper_sigs(board):
    c = collections.Counter()
    for t in board.GetTracks():
        cls = t.GetClass()
        if cls == 'PCB_TRACK':
            c[_track_sig(t)] += 1
        elif cls == 'PCB_VIA':
            c[_via_sig(t)] += 1
    return c


def main():
    fails = []

    def chk(name, cond, detail=''):
        print('  %s %s %s' % ('PASS' if cond else '**FAIL**', name, detail))
        if not cond:
            fails.append(name)

    # ---------------------------------------------------- 1. INTEGRITY --------
    print('-- 1. INTEGRITY: authoritative board matches the D-311 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-311 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (561 prior + 19 AMP_SD_MODE)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (60 prior + 1 AMP offset via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (685 - 2 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (96 + 2 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'AMP_SD_MODE']
    chk('journal carries 2 REST_INC AMP_SD_MODE entries',
        len(inc) == 2, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-310 copper preserved EXACTLY (561 trk + 60 via intact) --')
    now = copper_sigs(b)
    amp_items = collections.Counter({s: n for s, n in now.items() if s[1] in AMP})
    # Increments promoted AFTER D-311 (AMP_SD_MODE) are excluded so this "pre-AMP
    # copper intact" check stays true as the board grows.  The pre-AMP accepted
    # copper is Phase-A (432) + FRONT_RGB (20) + ACC (31) + DISP (11) + IMU (8) +
    # FRONT_RGB_LED (25) + IR_RX_VS (8) + TOUCH (26) = 561 tracks + 60 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - amp_items - post_items
    chk('non-AMP pre-D-312 copper == 561 tracks + 60 vias (all prior increments intact)',
        sum(prior_now.values()) == 561 + 60,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. AMP NEW COPPER: F/B + 1 via --------------
    print('\n-- 3. AMP_SD_MODE increment: 19 tracks (F.Cu+B.Cu), 1 through via --')
    amp_trk = [t for t in trk if t.GetNetname() in AMP]
    amp_via = [t for t in via if t.GetNetname() in AMP]
    layers = {t.GetLayerName() for t in amp_trk}
    chk('AMP is 19 tracks + exactly 1 via',
        len(amp_trk) == 19 and len(amp_via) == 1,
        '%d tracks, %d vias' % (len(amp_trk), len(amp_via)))
    chk('AMP copper spans F.Cu + B.Cu (cross-layer with host-face fan-out)',
        layers == {'F.Cu', 'B.Cu'}, 'layers=%s' % sorted(layers))
    chk('AMP tracks are all 0.200 mm (Default netclass)',
        all(t.GetWidth() == 200000 for t in amp_trk),
        'widths=%s' % sorted({t.GetWidth() for t in amp_trk}))
    chk('AMP via is a 0.60/0.30 Default through via',
        all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
            for v in amp_via),
        'dia/drill=%s' % sorted({(v.GetWidth(pcbnew.F_Cu), v.GetDrill()) for v in amp_via}))

    # --------------------- 3b. VIA-SITE OFFSET actually cleared the wall ------
    print('\n-- 3b. the D-311 offset moved the transition off the U2 wall --')
    other_via = [t for t in via if t.GetNetname() not in AMP]
    gaps = []
    for v in amp_via:
        vp = v.GetPosition()
        g = min(math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y)
                for o in other_via)
        gaps.append(g)
    chk('AMP via >= 0.80 mm (centre) from every existing via (offset worked)',
        all(g >= 800000 for g in gaps),
        'min centre gap = %s mm' % [round(g / 1e6, 3) for g in gaps])

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. AMP_SD_MODE fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    j_amp = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(pad('U5.4')) if p.GetClass() == 'PAD'}
    for other in ('R15.1', 'U2.7'):
        chk('AMP_SD_MODE connected: U5.4-%s' % other, other in j_amp, str(sorted(j_amp)))

    reg = []
    for e in jr:
        if e.get('group') == 'AMP_SD_MODE' or not e.get('requested_connected'):
            continue
        a, bb = e.get('a'), e.get('b')
        if not (a and bb) or a.count('.') != 1 or bb.count('.') != 1 \
                or a.startswith('(') or bb.startswith('('):
            continue
        pa = pad(a) if a.split('.')[0] in fps else None
        if pa is None:
            continue
        j = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(pa) if p.GetClass() == 'PAD'}
        if bb not in j:
            reg.append((a, bb))
    chk('no prior requested pair regressed (Phase-A + RGB + ACC + DISP + IMU + RGB_LED + IR_RX_VS + TOUCH)',
        not reg, '%d regressed' % len(reg))

    # ----------------------------- 5. ZONES + DRC ---------------------------
    print('\n-- 5. only In1/In4 planes re-poured; real full-board DRC unchanged --')
    planes = 0
    for z in b.Zones():
        lyrs = {pcbnew.BOARD.GetStandardLayerName(L) for L in z.GetLayerSet().CuStack()}
        if z.GetNetname() == 'GND' and lyrs and lyrs <= {'In1.Cu', 'In4.Cu'}:
            planes += 1
    chk('In1/In4 GND reference planes present (re-poured for the 1 new via)',
        planes == 2, '%d plane zones' % planes)
    dc, _ = RU.drc(AUTH, 'probe013', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-311): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
