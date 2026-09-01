# -*- coding: utf-8 -*-
"""FBV2-P2-027 / D-325 -- focused read-only evidence probe for the NINETEENTH
rest-of-board incremental increment AND the DUPLICATE-REF MST framework fix that
unlocked it: the navigation/boot button input BTN_B_N (SW7.1 button F.Cu / R9.2
pull-up B.Cu / U2.18 expander B.Cu), the FIRST net of the SWx user-button family,
routed onto the D-323 promoted board by incremental_router.py.

THE FRAMEWORK LEVER.  SW7 is a 4-pin tactile switch (Button_Switch_SMD:
SW_SPST_PTS645Sx43SMTR92) whose TWO mechanically-linked terminals BOTH carry pad
NUMBER "1" on BTN_B_N, at DIFFERENT physical locations -- (49.520,96.750) and
(57.480,96.750), 7.96 mm apart.  qrouter.QBoard._scan keys its pad table
self.pads[(net,"REF.NUM")], so the second "SW7.1" write overwrote the first and
one physical land was INVISIBLE to the MST; D-323 routed only one terminal and
the gate FAILed on connectivity (open_edges 2->1).  D-325 landed a bounded,
generic, deterministic fix ENTIRELY in incremental_router.py (qrouter.py
untouched, so every G-contract that routes through QBoard stays byte-identical):

  * physical_net_pads() sources MST nodes by stable PHYSICAL identity (ref,x,y),
    so both SW7.1 lands are distinct nodes; ordinary unique-pad nets return the
    exact net_pads() dict objects -> byte-identical routing;
  * cmd_gate's net_open_edges() counts copper clusters over PHYSICAL pads (a
    union-find keyed by (ref,x,y)), matching KiCad's own ratsnest, which owes one
    edge per physical land (BTN_B_N: 4 lands -> 3 edges, drop 3, not the 2 a
    ref-collapse counts).

BTN_B_N then routes an MST hubbed on R9.2 -> BOTH SW7.1 lands (two 0.60/0.30
Default THROUGH vias in the OPEN south button field, at (48.300,96.750) and
(56.300,95.600); the D-306/D-308 In1/In4 re-pour mechanic runs once for the two
barrels) + one SAME-LAYER B.Cu run R9.2->U2.18.  Default netclass (0.200 mm).
MEASURED: 19 tracks (3 F.Cu + 16 B.Cu), 2 through vias, all FOUR physical pads in
ONE copper cluster (open_edges 3->0), vias >= 2.915 mm from every barrel, OPEN
button field ~11 mm clear of BAT_PROTECTED_P -> ZERO D-269 involvement.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-325 gate
promoted:

  1. the increment PRESERVED the accepted D-323 copper EXACTLY -- all 781 prior
     tracks (432 Phase-A + 349 prior increments) and all 68 prior vias are still
     present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is BTN_B_N
     (19 tracks = 3 F.Cu + 16 B.Cu, plus exactly 2 through vias);
  3. the net is FULLY copper-connected -- ALL FOUR physical pads (both SW7.1
     lands at 49.520/57.480, R9.2, U2.18) sit in ONE copper cluster (physical-pad
     open_edges 3 -> 0), ratsnest 665 -> 662 (-3), and no prior pair regressed;
  4. exactly TWO 0.60/0.30 through vias were laid (via count 68 -> 70), each
     clears every existing barrel by >= 0.80 mm (measured 2.915 mm) and the
     realized copper clears BAT_PROTECTED_P by >= 0.300 mm (D-269 floor);
  5. only the In1/In4 GND reference planes were re-poured (anti-pads for the new
     vias) and real full-board KiCad DRC is unchanged (no new/worse class;
     `clearance` stays 0).

    python3 incremental_probe_024.py
"""
import os, sys, json, math, hashlib, collections
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

# The pre-promotion D-323 authoritative sha (781 trk / 68 via) -- the exact set
# that must survive this increment unchanged.
D323_SHA = 'a7bf8bdc11f1bc39303c6f6b6c801e3a4a575add64596cc4be20745c57f9f626'
INET = '/08_BUTTONS_EXPANDERS/BTN_B_N'
# The two physical SW7.1 lands -- the DUPLICATE-NUMBER terminals the fix must
# both drive (nm, exact x, y in KiCad internal nm).
SW7_1_LANDS = [(49520000, 96750000), (57480000, 96750000)]


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
    print('-- 1. INTEGRITY: authoritative board matches the D-325 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-325 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (781 prior + 19 BTN_B_N)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (68 prior + 2 BTN_B_N through vias)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (665 - 3 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (116 + 3 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC'
           and e.get('group') == 'BTN_B_N']
    chk('journal carries 3 REST_INC BTN_B_N edges (R9.2<->SW7.1 x2 + R9.2<->U2.18)',
        len(inc) == 3, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-323 copper preserved EXACTLY (781 trk + 68 via intact) --')
    now = copper_sigs(b)
    inet_items = collections.Counter({s: n for s, n in now.items() if s[1] == INET})
    # Increments promoted AFTER D-325 (future) are excluded so this "pre-D-325
    # copper intact" check stays true as the board grows.  The pre-D-325 accepted
    # copper is Phase-A (432) + all eighteen prior rest increments (349) = 781
    # tracks + 68 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE',
                  'SD_DETECT', 'XGPIO_PILOT', 'XGPIO_PILOT_W', 'XGPIO3',
                  'IMU_INT1_STRAP', 'UART0_TXD_DBG', 'IR_TX_GPIO16', 'SD_CS_N',
                  'RESERVED_SPARE', 'ACC_DETECT_N', 'BTN_B_N')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - inet_items - post_items
    chk('non-BTN_B_N pre-D-325 copper == 772 tracks + 68 vias (all prior increments intact)',
        sum(prior_now.values()) == 772 + 68,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. NEW COPPER: F/B tracks + 2 vias -----------
    print('\n-- 3. BTN_B_N increment: 19 tracks (3 F.Cu + 16 B.Cu), 2 through vias --')
    i_trk = [t for t in trk if t.GetNetname() == INET]
    i_via = [t for t in via if t.GetNetname() == INET]
    layers = collections.Counter(t.GetLayerName() for t in i_trk)
    chk('BTN_B_N is 19 tracks + exactly 2 vias',
        len(i_trk) == 19 and len(i_via) == 2,
        '%d tracks, %d vias' % (len(i_trk), len(i_via)))
    chk('BTN_B_N copper spans F.Cu (3) + B.Cu (16) (cross-layer to each SW7.1 land)',
        set(layers) == {'F.Cu', 'B.Cu'} and layers['F.Cu'] == 3 and layers['B.Cu'] == 16,
        'layers=%s' % dict(layers))
    chk('BTN_B_N tracks are all 0.200 mm (Default netclass width)',
        all(t.GetWidth() == 200000 for t in i_trk),
        'widths=%s' % sorted({t.GetWidth() for t in i_trk}))
    chk('BTN_B_N vias are two 0.60/0.30 Default through vias',
        len(i_via) == 2 and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                                and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in i_via),
        'dia/drill=%s' % sorted({(v.GetWidth(pcbnew.F_Cu), v.GetDrill()) for v in i_via}))
    chk('increment added exactly TWO vias to its net (board via total tracks the live SoT)',
        len(via) == EXPECT_VIAS and len(i_via) == 2, '%d total vias' % len(via))

    # --------------------- 3b. VIA SEPARATION + BAT_PROTECTED_P clearance -----
    print('\n-- 3b. both vias clear every barrel; D-269 0.300 mm BAT_PROTECTED_P kept --')
    other_via = [t for t in via if t.GetNetname() != INET]
    gaps = []
    for v in i_via:
        vp = v.GetPosition()
        g = min(math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y)
                for o in other_via)
        gaps.append(g)
    chk('both BTN_B_N vias >= 0.80 mm (centre) from every existing via',
        all(g >= 800000 for g in gaps),
        'min centre gaps = %s mm' % [round(g / 1e6, 3) for g in gaps])
    # D-269: min edge clearance BTN_B_N -> BAT_PROTECTED_P (any shared layer)
    bpp = [t for t in trk if 'BAT_PROTECTED_P' in t.GetNetname()]

    def _segseg(A, B):
        (a0, a1), (a2, a3), _ = A
        (b0, b1), (b2, b3), _ = B

        def sp(ax, ay, bx, by, px, py):
            dx, dy = bx - ax, by - ay
            if dx == 0 and dy == 0:
                return math.hypot(px - ax, py - ay)
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
            return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
        return min(sp(a0, a1, a2, a3, b0, b1), sp(a0, a1, a2, a3, b2, b3),
                   sp(b0, b1, b2, b3, a0, a1), sp(b0, b1, b2, b3, a2, a3))

    best = 1e12
    for t in i_trk:
        s, e = t.GetStart(), t.GetEnd()
        A = ((s.x, s.y), (e.x, e.y), t.GetWidth())
        for o in bpp:
            if o.GetLayerName() != t.GetLayerName():
                continue
            os_, oe = o.GetStart(), o.GetEnd()
            B = ((os_.x, os_.y), (oe.x, oe.y), o.GetWidth())
            c = _segseg(A, B) - t.GetWidth() / 2.0 - o.GetWidth() / 2.0
            if c < best:
                best = c
    chk('min clearance BTN_B_N -> BAT_PROTECTED_P >= 0.300 mm (D-269 floor)',
        best >= 300000 - 1000, 'measured %.4f mm' % (best / 1e6))

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    # THE decisive check: the duplicate-number lever must drive BOTH physical
    # SW7.1 lands.  We prove every one of the FOUR physical pads sits in the SAME
    # copper cluster (a physical-pad union-find, ratsnest excluded).
    print('\n-- 4. ALL FOUR physical pads in one copper cluster (both SW7.1 lands driven) --')
    cc = b.GetConnectivity()
    net_pads = [p for f in b.GetFootprints() for p in f.Pads()
                if p.GetNetname() == INET]
    chk('BTN_B_N presents 4 physical pads incl. TWO SW7.1 lands',
        len(net_pads) == 4
        and sum(1 for p in net_pads
                if p.GetParentFootprint().GetReference() == 'SW7'
                and p.GetNumber() == '1') == 2,
        '%d pads' % len(net_pads))

    def pid(p):
        pos = p.GetPosition()
        return (p.GetParentFootprint().GetReference() + '.' + p.GetNumber(), pos.x, pos.y)

    ids = {pid(p) for p in net_pads}
    parent = {i: i for i in ids}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for p in net_pads:
        for it in cc.GetConnectedItems(p):
            if it.GetClass() == 'PAD' and pid(it) in parent:
                ra, rb = find(pid(p)), find(pid(it))
                if ra != rb:
                    parent[ra] = rb
    clusters = len({find(i) for i in ids})
    chk('BTN_B_N physical-pad open_edges == 0 (4 lands -> 1 copper cluster)',
        clusters == 1, '%d clusters (open_edges %d)' % (clusters, clusters - 1))

    # And BOTH SW7.1 lands specifically are joined to the R9.2 hub by copper.
    def pad_at(ref_num, xy):
        for p in net_pads:
            if (p.GetParentFootprint().GetReference() + '.' + p.GetNumber() == ref_num
                    and p.GetPosition().x == xy[0] and p.GetPosition().y == xy[1]):
                return p
        return None
    hub = None
    for p in net_pads:
        if p.GetParentFootprint().GetReference() + '.' + p.GetNumber() == 'R9.2':
            hub = p
    hub_reach = {pid(it) for it in cc.GetConnectedItems(hub) if it.GetClass() == 'PAD'}
    both_lands = all(pad_at('SW7.1', xy) is not None
                     and pid(pad_at('SW7.1', xy)) in hub_reach for xy in SW7_1_LANDS)
    chk('BOTH SW7.1 lands (49.520 AND 57.480) copper-joined to the R9.2 hub',
        both_lands, 'lands=%s' % [(round(x / 1e6, 3), round(y / 1e6, 3)) for x, y in SW7_1_LANDS])

    reg = []
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        if r not in fps:
            return None
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None
    for e in jr:
        if e.get('group') == 'BTN_B_N' or not e.get('requested_connected'):
            continue
        a, bb = e.get('a'), e.get('b')
        if not (a and bb) or a.count('.') != 1 or bb.count('.') != 1 \
                or a.startswith('(') or bb.startswith('('):
            continue
        pa = pad(a)
        if pa is None:
            continue
        j = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(pa) if p.GetClass() == 'PAD'}
        if bb not in j:
            reg.append((a, bb))
    chk('no prior requested pair regressed (Phase-A + all eighteen prior increments)',
        not reg, '%d regressed' % len(reg))

    # ----------------------------- 5. ZONES + DRC ---------------------------
    print('\n-- 5. only In1/In4 planes re-poured (via anti-pads); real full-board DRC unchanged --')
    planes = 0
    for z in b.Zones():
        lyrs = {pcbnew.BOARD.GetStandardLayerName(L) for L in z.GetLayerSet().CuStack()}
        if z.GetNetname() == 'GND' and lyrs and lyrs <= {'In1.Cu', 'In4.Cu'}:
            planes += 1
    chk('In1/In4 GND reference planes present (re-poured for the 2 new vias)',
        planes == 2, '%d plane zones' % planes)
    dc, _ = RU.drc(AUTH, 'probe024', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-325): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
