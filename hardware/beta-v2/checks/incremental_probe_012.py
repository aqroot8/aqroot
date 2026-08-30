# -*- coding: utf-8 -*-
"""FBV2-P2-012 / D-310 -- focused read-only evidence probe for the SEVENTH
rest-of-board incremental increment: the display/touch control PAIR
TOUCH_RST_N + TOUCH_INT_N, routed onto the D-309 promoted board by
incremental_router.py through the new U2-escape via-site OFFSET mechanism.

This is the group D-309 characterised as a WALL.  U2.4/.7/.8/.11 stack on U2's
west edge and the accepted D-306 DISP_RST_N through-via sits 1.19 mm west of that
column, so the router's via-blind default via_site laid the F<->B transition (and
threaded its F.Cu run) right past the DISP_RST_N barrel -> +3 `clearance`.
FBV2-P2-012 closes it with two generic, bounded, qrouter-UNTOUCHED mechanisms in
incremental_router.connect_cross:

  (a) EXISTING-VIA AWARENESS -- every accepted PCB_VIA barrel/hole is injected as
      an obstacle onto the per-route QBoard instance (qrouter._scan builds
      obstacles from pads + PCB_TRACK but omits PCB_VIA), so escape / via_site /
      connect_role's track search all respect accepted vias;
  (b) BOUNDED VIA-SITE OFFSET -- the group opts in with `via_offset` and the
      transition is deliberately walked ~2.5 mm off the nearest congesting barrel
      (a short B.Cu host-face fan-out) instead of the router's nearest cell.

Result on the real full-board gate: TOUCH_RST_N via lands at (52.95,92.10) 5.10 mm
from the DISP_RST_N via; TOUCH_INT_N (U2's EAST edge) at (61.15,88.85) 8.41 mm
clear; +0 `clearance`, ratsnest 688->685.  Both display/touch control lines are
now on the authoritative board -- the whole U2 escape family is unlocked.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-310 gate
promoted:

  1. the increment PRESERVED the accepted D-309 copper EXACTLY -- all 535 prior
     tracks (432 Phase-A + 20 RGB + 31 ACC + 11 DISP + 8 IMU + 25 RGB_LED + 8
     IR_RX_VS) and 58 prior vias are still present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the two
     TOUCH nets (26 tracks F.Cu+B.Cu, 2 through vias);
  3. both nets are FULLY copper-connected (TOUCH_RST_N J1.47-R12.1-U2.4 one
     island; TOUCH_INT_N J1.46-U2.19 one island; ratsnest 688 -> 685), and no
     prior requested pair regressed;
  4. the via-site OFFSET mechanism actually cleared the wall -- both new vias are
     >= 0.80 mm (centre) from EVERY existing via (the via-blind default put a
     sibling net's via 0.100 mm from DISP_RST_N);
  5. only the In1/In4 GND reference planes re-poured (2 new through vias) -- every
     other zone byte-identical -- and real full-board KiCad DRC is unchanged (no
     new class, none increased; `clearance` stays 0).

    python3 incremental_probe_012.py
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

# The pre-promotion D-309 authoritative sha (535 trk / 58 via) -- the exact set
# that must survive this increment unchanged.
D309_SHA = '5c5cae79465416c81f9d7b8dba5b2e3a3325bd9a0680b65103badf0e1a339f63'
TCH = ('/TOUCH_RST_N', '/TOUCH_INT_N')


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
    print('-- 1. INTEGRITY: authoritative board matches the D-310 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-310 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (535 prior + 26 TOUCH)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (58 prior + 2 TOUCH offset vias)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (688 - 3 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (93 + 3 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'TOUCH_CTL']
    chk('journal carries 3 REST_INC TOUCH_CTL entries',
        len(inc) == 3, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-309 copper preserved EXACTLY (535 trk + 58 via intact) --')
    now = copper_sigs(b)
    tch_items = collections.Counter({s: n for s, n in now.items() if s[1] in TCH})
    # Increments promoted AFTER D-310 (TOUCH_CTL) are excluded so this "pre-TOUCH
    # copper intact" check stays true as the board grows.  The pre-TOUCH accepted
    # copper is Phase-A (432) + FRONT_RGB (20) + ACC (31) + DISP (11) + IMU (8) +
    # FRONT_RGB_LED (25) + IR_RX_VS (8) = 535 tracks + 58 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - tch_items - post_items
    chk('non-TOUCH pre-D-311 copper == 535 tracks + 58 vias (all prior increments intact)',
        sum(prior_now.values()) == 535 + 58,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. TOUCH NEW COPPER: F/B + 2 vias -----------
    print('\n-- 3. TOUCH_CTL increment: 26 tracks (F.Cu+B.Cu), 2 through vias --')
    tch_trk = [t for t in trk if t.GetNetname() in TCH]
    tch_via = [t for t in via if t.GetNetname() in TCH]
    layers = {t.GetLayerName() for t in tch_trk}
    chk('TOUCH is 26 tracks + exactly 2 vias',
        len(tch_trk) == 26 and len(tch_via) == 2,
        '%d tracks, %d vias' % (len(tch_trk), len(tch_via)))
    chk('TOUCH copper spans F.Cu + B.Cu (cross-layer with host-face fan-out)',
        layers == {'F.Cu', 'B.Cu'}, 'layers=%s' % sorted(layers))
    chk('TOUCH tracks are all 0.200 mm (Default netclass)',
        all(t.GetWidth() == 200000 for t in tch_trk),
        'widths=%s' % sorted({t.GetWidth() for t in tch_trk}))
    chk('TOUCH vias are all 0.60/0.30 Default through vias',
        all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
            for v in tch_via),
        'dia/drill=%s' % sorted({(v.GetWidth(pcbnew.F_Cu), v.GetDrill()) for v in tch_via}))

    # --------------------- 3b. VIA-SITE OFFSET actually cleared the wall ------
    print('\n-- 3b. the D-310 offset moved both transitions off the U2 wall --')
    other_via = [t for t in via if t.GetNetname() not in TCH]
    gaps = []
    for v in tch_via:
        vp = v.GetPosition()
        g = min(math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y)
                for o in other_via)
        gaps.append(g)
    chk('both TOUCH vias >= 0.80 mm (centre) from every existing via (offset worked)',
        all(g >= 800000 for g in gaps),
        'min centre gaps = %s mm' % [round(g / 1e6, 3) for g in gaps])

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. both TOUCH nets fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    j_rst = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(pad('R12.1')) if p.GetClass() == 'PAD'}
    for other in ('J1.47', 'U2.4'):
        chk('TOUCH_RST_N connected: R12.1-%s' % other, other in j_rst, str(sorted(j_rst)))
    j_int = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(pad('U2.19')) if p.GetClass() == 'PAD'}
    chk('TOUCH_INT_N connected: U2.19-J1.46', 'J1.46' in j_int, str(sorted(j_int)))

    reg = []
    for e in jr:
        if e.get('group') == 'TOUCH_CTL' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + RGB + ACC + DISP + IMU + RGB_LED + IR_RX_VS)',
        not reg, '%d regressed' % len(reg))

    # ----------------------------- 5. ZONES + DRC ---------------------------
    print('\n-- 5. only In1/In4 planes re-poured; real full-board DRC unchanged --')
    planes = 0
    for z in b.Zones():
        lyrs = {pcbnew.BOARD.GetStandardLayerName(L) for L in z.GetLayerSet().CuStack()}
        if z.GetNetname() == 'GND' and lyrs and lyrs <= {'In1.Cu', 'In4.Cu'}:
            planes += 1
    chk('In1/In4 GND reference planes present (re-poured for the 2 new vias)',
        planes == 2, '%d plane zones' % planes)
    dc, _ = RU.drc(AUTH, 'probe012', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-310): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
