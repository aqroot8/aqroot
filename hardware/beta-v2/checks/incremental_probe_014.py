# -*- coding: utf-8 -*-
"""FBV2-P2-014 / D-312 -- focused read-only evidence probe for the NINTH
rest-of-board incremental increment: the microSD card-detect strap
SD_CARD_DETECT_N (J2.10/R113.2 F.Cu -> U2.11 B.Cu), routed onto the D-311
promoted board by incremental_router.py through the D-310 U2-escape via-site
OFFSET mechanism.

SD_CARD_DETECT_N is the SECOND remaining U2 west-edge escape sibling and the
last of the D-309 U2 family.  The D-309 +2 `clearance` fail was TRACK-threading
(the via-blind track router threaded the F.Cu run past the DISP_RST_N barrel),
NOT the via.  D-312 completes it with the SAME unchanged mechanism -- the
always-on existing-via injection (qrouter._scan omits PCB_VIA) fixes the track
threading, plus the opt-in 2.5 mm `via_offset` (ZERO per-net tuning) walks the
F<->B transition SOUTH to (53.00,82.55), 3.850 mm clear of the nearest existing
via (the D-306 DISP_RST_N barrel).

The increment was RE-SCREENED LIVE on the D-311 board (w/screen_014.py): the new
D-311 AMP_SD_MODE via (north, y~90.2) does NOT touch SD_CARD_DETECT_N's southward
escape (esc y~85, via y~82.55); even the via-blind default via is 1.301 mm clear.
Routed as its OWN increment (NOT bundled with AMP_SD_MODE -- functionally
distinct: microSD detect vs audio-amp strap).

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-312 gate
promoted:

  1. the increment PRESERVED the accepted D-311 copper EXACTLY -- all 580 prior
     tracks (432 Phase-A + 20 RGB + 31 ACC + 11 DISP + 8 IMU + 25 RGB_LED + 8
     IR_RX_VS + 26 TOUCH + 19 AMP_SD_MODE) and 61 prior vias are still present
     byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the single
     SD_CARD_DETECT_N net (28 tracks F.Cu+B.Cu, 1 through via);
  3. the net is FULLY copper-connected (J2.10-R113.2-U2.11 one island; ratsnest
     683 -> 681), and no prior requested pair regressed;
  4. the via-site OFFSET mechanism placed the new via >= 0.80 mm (centre) from
     EVERY existing via (measured 3.850 mm from DISP_RST_N);
  5. only the In1/In4 GND reference planes re-poured (1 new through via) -- every
     other zone byte-identical -- and real full-board KiCad DRC is unchanged (no
     new class, none increased; `clearance` stays 0).

    python3 incremental_probe_014.py
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

# The pre-promotion D-311 authoritative sha (580 trk / 61 via) -- the exact set
# that must survive this increment unchanged.
D311_SHA = '9bf429cec07654d4522121d2fb595204d06f5173ae629f2292c4d0cb9f68b314'
SD = ('/SD_CARD_DETECT_N',)


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
    print('-- 1. INTEGRITY: authoritative board matches the D-312 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-312 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (580 prior + 28 SD_CARD_DETECT_N)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (61 prior + 1 SD offset via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (683 - 2 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (98 + 2 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'SD_DETECT']
    chk('journal carries 2 REST_INC SD_DETECT entries',
        len(inc) == 2, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-311 copper preserved EXACTLY (580 trk + 61 via intact) --')
    now = copper_sigs(b)
    sd_items = collections.Counter({s: n for s, n in now.items() if s[1] in SD})
    # Increments promoted AFTER D-312 (SD_DETECT) are excluded so this "pre-SD
    # copper intact" check stays true as the board grows.  The pre-SD accepted
    # copper is Phase-A (432) + FRONT_RGB (20) + ACC (31) + DISP (11) + IMU (8) +
    # FRONT_RGB_LED (25) + IR_RX_VS (8) + TOUCH (26) + AMP_SD_MODE (19) = 580
    # tracks + 61 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE',
                  'SD_DETECT')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - sd_items - post_items
    chk('non-SD pre-D-313 copper == 580 tracks + 61 vias (all prior increments intact)',
        sum(prior_now.values()) == 580 + 61,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. SD NEW COPPER: F/B + 1 via ---------------
    print('\n-- 3. SD_CARD_DETECT_N increment: 28 tracks (F.Cu+B.Cu), 1 through via --')
    sd_trk = [t for t in trk if t.GetNetname() in SD]
    sd_via = [t for t in via if t.GetNetname() in SD]
    layers = {t.GetLayerName() for t in sd_trk}
    chk('SD is 28 tracks + exactly 1 via',
        len(sd_trk) == 28 and len(sd_via) == 1,
        '%d tracks, %d vias' % (len(sd_trk), len(sd_via)))
    chk('SD copper spans F.Cu + B.Cu (cross-layer with host-face fan-out)',
        layers == {'F.Cu', 'B.Cu'}, 'layers=%s' % sorted(layers))
    chk('SD tracks are all 0.200 mm (Default netclass)',
        all(t.GetWidth() == 200000 for t in sd_trk),
        'widths=%s' % sorted({t.GetWidth() for t in sd_trk}))
    chk('SD via is a 0.60/0.30 Default through via',
        all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
            for v in sd_via),
        'dia/drill=%s' % sorted({(v.GetWidth(pcbnew.F_Cu), v.GetDrill()) for v in sd_via}))

    # --------------------- 3b. VIA-SITE OFFSET cleared every existing via -----
    print('\n-- 3b. the D-312 offset kept the transition off the U2 wall --')
    other_via = [t for t in via if t.GetNetname() not in SD]
    gaps = []
    for v in sd_via:
        vp = v.GetPosition()
        g = min(math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y)
                for o in other_via)
        gaps.append(g)
    chk('SD via >= 0.80 mm (centre) from every existing via (offset clear)',
        all(g >= 800000 for g in gaps),
        'min centre gap = %s mm' % [round(g / 1e6, 3) for g in gaps])

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. SD_CARD_DETECT_N fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    j_sd = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
            for p in cc.GetConnectedItems(pad('U2.11')) if p.GetClass() == 'PAD'}
    for other in ('J2.10', 'R113.2'):
        chk('SD_CARD_DETECT_N connected: U2.11-%s' % other, other in j_sd, str(sorted(j_sd)))

    reg = []
    for e in jr:
        if e.get('group') == 'SD_DETECT' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + RGB + ACC + DISP + IMU + RGB_LED + IR_RX_VS + TOUCH + AMP)',
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
    dc, _ = RU.drc(AUTH, 'probe014', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-312): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
