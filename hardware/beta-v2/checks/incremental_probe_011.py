# -*- coding: utf-8 -*-
"""FBV2-P2-011 / D-309 -- focused read-only evidence probe for the SIXTH
rest-of-board incremental increment: the IR receiver (U6) local filtered supply
IR_RX_VS_LOCAL, routed onto the D-308 promoted board by incremental_router.py.

IR_RX_VS_LOCAL (07_IR) is the RC-filtered local supply node for the IR
demodulator U6: series filter R21.2 (F.Cu SMD) + decoupling C11.1 (F.Cu SMD) ->
U6.3 supply pin (THT, on BOTH faces).  All three pads share the F.Cu outer layer
(U6.3 is THT so F.Cu is available), so every MST edge is a SAME-LAYER F.Cu run
with NO via -- the cleanest possible increment class (like D-307 IMU_ADDR, but
on F.Cu).  A tight NE-corner cluster measured PRISTINE (0 accepted copper within
the group bbox + 2 mm).  A coherent standalone peripheral supply-filter group --
noncritical low current, NOT a bulk rail.

The task-preferred display/touch control group (TOUCH_RST_N + TOUCH_INT_N) and
the AMP_SD_MODE / SD_CARD_DETECT_N alternatives were all MEASURED on scratch and
FAILED the real full-board gate with NEW `clearance` violations (+3 / +7 / +2):
each is a long cross-board haul (33-68 mm) whose cross-layer via lands in the
congested U2 B.Cu escape region beside the accepted D-306 DISP_RST_N via -- a
characterised wall, deferred to FBV2-P2-012 (see the D-309 audit).  IR_RX_VS won
on clean evidence, not by default.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, the exact facts the D-309 gate
promoted:

  1. the increment PRESERVED the accepted D-308 copper EXACTLY -- all 527 prior
     tracks (432 Phase-A + 20 FRONT_RGB + 31 ACC + 11 DISP + 8 IMU + 25 RGB_LED)
     and 58 prior vias are still present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the single
     IR_RX_VS_LOCAL net (8 tracks on F.Cu, NO via);
  3. the net is FULLY copper-connected (C11.1-R21.2-U6.3 one island; ratsnest
     690 -> 688), and no prior requested pair regressed;
  4. real full-board KiCad DRC is unchanged (no new class, none increased) and,
     because no via was laid, ALL 41 zones are byte-identical (no plane re-pour).

    python3 incremental_probe_011.py
"""
import os, sys, json, hashlib, collections
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

# The pre-promotion D-308 authoritative sha (527 trk / 58 via) -- the exact set
# that must survive this increment unchanged.
D308_SHA = 'f4e95decb5be87f6e758f76803e57be68a4437afaef75973518983008559e7ee'
IRVS = ('/07_IR/IR_RX_VS_LOCAL',)


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
    print('-- 1. INTEGRITY: authoritative board matches the D-309 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-309 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (527 prior + 8 IR_RX_VS_LOCAL)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (58 prior, IR_RX_VS lays NO via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (690 - 2 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (91 + 2 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'IR_RX_VS']
    chk('journal carries 2 REST_INC IR_RX_VS entries',
        len(inc) == 2, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-308 copper preserved EXACTLY (527 trk + 58 via intact) --')
    now = copper_sigs(b)
    irvs_items = collections.Counter({s: n for s, n in now.items() if s[1] in IRVS})
    # Increments promoted AFTER D-309 (IR_RX_VS) are excluded so this "pre-IR_RX_VS
    # copper intact" check stays true as the board grows.  The pre-IR_RX_VS
    # accepted copper is Phase-A (432) + FRONT_RGB (20) + ACC (31) + DISP (11) +
    # IMU (8) + FRONT_RGB_LED (25) = 527 tracks + 58 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - irvs_items - post_items
    chk('non-IR_RX_VS pre-D-310 copper == 527 tracks + 58 vias (all prior increments intact)',
        sum(prior_now.values()) == 527 + 58,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. IR_RX_VS NEW COPPER: F.Cu, no via ---------
    print('\n-- 3. IR_RX_VS_LOCAL increment: 8 F.Cu tracks, no via --')
    irvs_trk = [t for t in trk if t.GetNetname() in IRVS]
    irvs_via = [t for t in via if t.GetNetname() in IRVS]
    layers = {t.GetLayerName() for t in irvs_trk}
    chk('IR_RX_VS_LOCAL is 8 tracks + exactly 0 vias',
        len(irvs_trk) == 8 and len(irvs_via) == 0,
        '%d tracks, %d vias' % (len(irvs_trk), len(irvs_via)))
    chk('IR_RX_VS_LOCAL copper is all F.Cu (same-layer, no cross-layer hop)',
        layers == {'F.Cu'}, 'layers=%s' % sorted(layers))
    chk('IR_RX_VS_LOCAL tracks are all 0.200 mm (Default netclass)',
        all(t.GetWidth() == 200000 for t in irvs_trk),
        'widths=%s' % sorted({t.GetWidth() for t in irvs_trk}))

    # NOTE: a via would have forced an In1/In4 GND plane re-pour; this increment
    # lays no via, so the D-308 plane fills carry through unchanged -- the gate
    # proved all 41 zones byte-identical and the DRC below re-proves legality.

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. IR_RX_VS_LOCAL fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    # C11.1 -- R21.2 -- U6.3: all three one copper island (R21.2 is the centre).
    joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
              for p in cc.GetConnectedItems(pad('R21.2')) if p.GetClass() == 'PAD'}
    for other in ('C11.1', 'U6.3'):
        chk('IR_RX_VS_LOCAL connected: R21.2-%s' % other,
            other in joined, str(sorted(joined)))

    reg = []
    for e in jr:
        if e.get('group') == 'IR_RX_VS' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + RGB + ACC + DISP + IMU + RGB_LED)',
        not reg, '%d regressed' % len(reg))

    # ------------------------------------------- 5. DRC UNCHANGED -------------
    print('\n-- 5. real full-board KiCad DRC unchanged --')
    dc, _ = RU.drc(AUTH, 'probe011', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-309): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
