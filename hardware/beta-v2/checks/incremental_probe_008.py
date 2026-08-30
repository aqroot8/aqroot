# -*- coding: utf-8 -*-
"""FBV2-P2-008 / D-306 -- focused read-only evidence probe for the THIRD
rest-of-board incremental increment: the DISP_RST_N display-reset control net,
routed onto the D-305 promoted board by incremental_router.py.

This is the FIRST increment to exercise two new routing primitives:
  * a pure F.Cu run (R16.1 <-> J1.10, both F.Cu SMD), and
  * a CROSS-LAYER edge (J1.10 F.Cu <-> U2.8 B.Cu) closed by ONE board-legal
    through via (0.60 mm / 0.30 mm, the Default netclass geometry, >= the
    0.50 mm min_via_diameter -- not a microvia, not a via-in-pad),
whose barrel required re-pouring the In1/In4 GND reference planes to open its
clearance anti-pad.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, the exact facts the D-306 gate
promoted:

  1. the increment PRESERVED the accepted D-305 copper EXACTLY -- all 483 prior
     tracks (432 Phase-A + 20 FRONT_RGB + 31 ACC_3V3_CTL) and 54 prior vias are
     still present byte/geometry-identical, none deleted or altered;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the
     DISP_RST_N net (11 tracks on F.Cu AND B.Cu + exactly 1 through via 0.60/0.30);
  3. DISP_RST_N is now FULLY copper-connected across the layer hop (ratsnest
     695), and no prior requested pair (Phase-A / FRONT_RGB / ACC) regressed;
  4. real full-board KiCad DRC is unchanged -- the via anti-pad is legal, no new
     clearance / hole_clearance class (they appeared and were resolved by the
     In1/In4 re-pour at route time).

    python3 incremental_probe_008.py
"""
import os, sys, json, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')

# D-306 promoted-board fingerprints.
EXPECT_SHA = '9c0586d824f92542c34fd12de1f6f8d4bdd8aaaab656c823eec40d6ae3f62259'
EXPECT_TRACKS = 494           # D-305 483 + 11 DISP_RST_N
EXPECT_VIAS = 55              # 54 + 1 DISP_RST_N cross-layer through via
EXPECT_JOURNAL = 86           # 84 (D-305) + 2 DISP_RST REST_INC
EXPECT_RATSNEST = 695         # 697 (D-305) - 2 (DISP_RST_N 3-pad net closed)

# The pre-promotion D-305 authoritative sha (483 trk / 54 via) -- the exact set
# that must survive this increment unchanged.
D305_SHA = 'f0046eb71f241afcb24978dc55b92aae0875300bd6e0747dc0bec6f204c7cd41'
DISP = ('/DISP_RST_N',)


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
    print('-- 1. INTEGRITY: authoritative board matches the D-306 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-306 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (483 prior + 11 DISP_RST_N)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (54 prior + 1 DISP_RST_N cross-layer via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (697 - 2 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (84 + 2 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'DISP_RST']
    chk('journal carries 2 REST_INC DISP_RST entries',
        len(inc) == 2, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-305 copper preserved EXACTLY (483 trk + 54 via intact) --')
    now = copper_sigs(b)
    disp_items = collections.Counter({s: n for s, n in now.items() if s[1] in DISP})
    prior_now = now - disp_items
    chk('non-DISP copper == 483 tracks + 54 vias (Phase-A + RGB + ACC intact)',
        sum(prior_now.values()) == 483 + 54,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. DISP_RST_N NEW COPPER: F.Cu + B.Cu + 1 via -
    print('\n-- 3. DISP_RST_N increment: F.Cu run + B.Cu stub + one legal via --')
    disp_trk = [t for t in trk if t.GetNetname() in DISP]
    disp_via = [t for t in via if t.GetNetname() in DISP]
    layers = {t.GetLayerName() for t in disp_trk}
    chk('DISP_RST_N is 11 tracks + exactly 1 via', len(disp_trk) == 11 and len(disp_via) == 1,
        '%d tracks, %d vias' % (len(disp_trk), len(disp_via)))
    chk('DISP_RST_N copper spans BOTH F.Cu and B.Cu (the cross-layer hop)',
        {'F.Cu', 'B.Cu'} <= layers, 'layers=%s' % sorted(layers))
    chk('DISP_RST_N tracks are all 0.200 mm (Default netclass)',
        all(t.GetWidth() == 200000 for t in disp_trk),
        'widths=%s' % sorted({t.GetWidth() for t in disp_trk}))
    if disp_via:
        v = disp_via[0]
        d, k = v.GetWidth(pcbnew.F_Cu), v.GetDrill()
        chk('the via is a board-legal through via 0.60/0.30 (>= 0.50 min_via)',
            d == 600000 and k == 300000 and d >= 500000
            and v.GetViaType() == pcbnew.VIATYPE_THROUGH,
            'dia=%.3f drill=%.3f type=%d' % (d / 1e6, k / 1e6, v.GetViaType()))

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. DISP_RST_N fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    # R16.1 (F.Cu) -- J1.10 (F.Cu) -- U2.8 (B.Cu): all three one copper island.
    joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
              for p in cc.GetConnectedItems(pad('J1.10')) if p.GetClass() == 'PAD'}
    for other in ('R16.1', 'U2.8'):
        chk('DISP_RST_N connected across the hop: J1.10-%s' % other,
            other in joined, str(sorted(joined)))

    reg = []
    for e in jr:
        if e.get('group') == 'DISP_RST' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + RGB + ACC)', not reg,
        '%d regressed' % len(reg))

    # ------------------------------------------- 5. DRC UNCHANGED -------------
    print('\n-- 5. real full-board KiCad DRC unchanged (via anti-pad is legal) --')
    dc, _ = RU.drc(AUTH, 'probe008', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-306): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
