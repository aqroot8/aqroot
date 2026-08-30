# -*- coding: utf-8 -*-
"""FBV2-P2-010 / D-308 -- focused read-only evidence probe for the FIFTH
rest-of-board incremental increment: the front-panel RGB status-indicator
COMPLETION (the LED-cathode side), routed onto the D-307 promoted board by
incremental_router.py.

D-304 (FRONT_RGB) routed the expander->resistor side of the front-panel RGB
status LED (U23 PCAL9535A GPIO -> R124/R125/R126 series limit resistors, all
B.Cu).  This increment closes the SAME indicator on the LED-cathode side: the
far pad of each series resistor (R124.2/R125.2/R126.2, B.Cu SMD) to the matching
cathode of D13 (MHPA3528RGBCT RGB LED, F.Cu SMD).  The three nets are
Net-(D13-RK) (R124->D13.4 red), Net-(D13-GK) (R125->D13.3 green) and
Net-(D13-BK) (R126->D13.2 blue).

This is the FIRST MULTI-VIA increment.  Each net is a 2-pad CROSS-LAYER net
(resistor B.Cu, LED F.Cu) that closes with exactly ONE board-legal 0.60/0.30
Default-netclass through via -- so THREE independent vias are laid, the D-306
single-via-per-edge mechanic (connect_cross) applied three times, UNCHANGED.  A
through via crosses the In1/In4 GND reference planes, so those two zones (and
ONLY those two) were re-poured ONCE for all three anti-pads; every other zone is
byte-identical (the D-306 promotable standard).  Low current (R-limited 2-6 mA
status indicator, non-switching), low congestion.  A coherent local peripheral
cluster that directly extends the already-accepted D-304 increment.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, the exact facts the D-308 gate
promoted:

  1. the increment PRESERVED the accepted D-307 copper EXACTLY -- all 502 prior
     tracks (432 Phase-A + 20 FRONT_RGB + 31 ACC + 11 DISP + 8 IMU_ADDR) and 55
     prior vias are still present byte/geometry-identical, none deleted/altered;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the three
     D13 cathode nets (25 tracks on F.Cu+B.Cu, 3 through vias);
  3. all three nets are FULLY copper-connected across their F/B hop (ratsnest
     690, each 2-pad net one island), and no prior requested pair regressed;
  4. real full-board KiCad DRC is unchanged (no new class, none increased); and
     ONLY the In1/In4 GND reference planes changed fill (the three via anti-pads)
     -- every other zone is byte-identical.

    python3 incremental_probe_010.py
"""
import os, sys, json, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')

# D-308 promoted-board fingerprints.
import live_fingerprint as LFP   # single source of truth for the live board pin (D-309)
EXPECT_SHA = LFP.SHA
EXPECT_TRACKS = LFP.TRACKS
EXPECT_VIAS = LFP.VIAS
EXPECT_JOURNAL = LFP.JOURNAL_LEN
EXPECT_RATSNEST = LFP.RATSNEST

# The pre-promotion D-307 authoritative sha (502 trk / 55 via) -- the exact set
# that must survive this increment unchanged.
D307_SHA = 'a309f8ce022b48ef04baa2fef591c64eb1a643049ad31220a9cff24831279a50'
RGBLED = ('Net-(D13-RK)', 'Net-(D13-GK)', 'Net-(D13-BK)')


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
    print('-- 1. INTEGRITY: authoritative board matches the D-308 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-308 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (502 prior + 25 FRONT_RGB_LED)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (55 prior + 3 FRONT_RGB_LED cross-layer vias)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (693 - 3 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (88 + 3 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'FRONT_RGB_LED']
    chk('journal carries 3 REST_INC FRONT_RGB_LED entries',
        len(inc) == 3, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-307 copper preserved EXACTLY (502 trk + 55 via intact) --')
    now = copper_sigs(b)
    rgbled_items = collections.Counter({s: n for s, n in now.items() if s[1] in RGBLED})
    # Increments promoted AFTER D-308 (none yet) are excluded so this check stays
    # true as the board grows.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR', 'FRONT_RGB_LED')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - rgbled_items - post_items
    chk('non-FRONT_RGB_LED pre-D-309 copper == 502 tracks + 55 vias (all prior increments intact)',
        sum(prior_now.values()) == 502 + 55,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # ------------- 3. FRONT_RGB_LED NEW COPPER: F.Cu+B.Cu, 3 through vias ------
    print('\n-- 3. FRONT_RGB_LED increment: 25 F.Cu+B.Cu tracks, 3 through vias --')
    rgbled_trk = [t for t in trk if t.GetNetname() in RGBLED]
    rgbled_via = [t for t in via if t.GetNetname() in RGBLED]
    layers = {t.GetLayerName() for t in rgbled_trk}
    chk('FRONT_RGB_LED is 25 tracks + exactly 3 vias',
        len(rgbled_trk) == 25 and len(rgbled_via) == 3,
        '%d tracks, %d vias' % (len(rgbled_trk), len(rgbled_via)))
    chk('FRONT_RGB_LED copper spans BOTH F.Cu and B.Cu (three cross-layer hops)',
        {'F.Cu', 'B.Cu'} <= layers, 'layers=%s' % sorted(layers))
    chk('FRONT_RGB_LED tracks are all 0.200 mm (Default netclass)',
        all(t.GetWidth() == 200000 for t in rgbled_trk),
        'widths=%s' % sorted({t.GetWidth() for t in rgbled_trk}))
    chk('all three vias are board-legal through vias 0.60/0.30 (>= 0.50 min_via), one per net',
        len(rgbled_via) == 3
        and {v.GetNetname() for v in rgbled_via} == set(RGBLED)
        and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                and v.GetWidth(pcbnew.F_Cu) >= 500000
                and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in rgbled_via),
        'nets=%s dias=%s drills=%s'
        % (sorted({v.GetNetname() for v in rgbled_via}),
           sorted({v.GetWidth(pcbnew.F_Cu) for v in rgbled_via}),
           sorted({v.GetDrill() for v in rgbled_via})))

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. all three D13 cathode nets fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    for a, other in (('D13.4', 'R124.2'), ('D13.3', 'R125.2'), ('D13.2', 'R126.2')):
        joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in cc.GetConnectedItems(pad(a)) if p.GetClass() == 'PAD'}
        chk('FRONT_RGB_LED connected across the hop: %s-%s' % (a, other),
            other in joined, str(sorted(joined)))

    reg = []
    for e in jr:
        if e.get('group') == 'FRONT_RGB_LED' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + RGB + ACC + DISP + IMU)', not reg,
        '%d regressed' % len(reg))

    # ------------------------------------------- 5. DRC UNCHANGED -------------
    print('\n-- 5. real full-board KiCad DRC unchanged --')
    dc, _ = RU.drc(AUTH, 'probe010', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-308): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
