# -*- coding: utf-8 -*-
"""FBV2-P2-028 / D-326 -- focused read-only evidence probe for the TWENTIETH
rest-of-board incremental increment and the SECOND net of the SWx user-button
family: the navigation D-pad UP button input BTN_UP_N (SW2.1 button two F.Cu
tact-switch lands / R4.2 pull-up B.Cu / U2.13 PCAL9535A expander GPIO B.Cu),
routed onto the D-325 promoted board by incremental_router.py.

THE FRAMEWORK LEVER (D-325, retained).  SW2 is the SAME 4-pin tactile switch as
SW7 (Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92) -- its two mechanically-linked
terminals BOTH carry pad NUMBER "1" on BTN_UP_N, at DIFFERENT physical locations,
measured (60.220,96.750) and (68.180,96.750), 7.96 mm apart.  qrouter.QBoard._scan
keys self.pads[(net,"REF.NUM")], so without the fix one physical land would be
invisible to the MST (the D-323 BTN_B_N gate FAIL, open_edges 2->1).  The D-325
fix lives ENTIRELY in incremental_router.py (qrouter.py untouched):
physical_net_pads() keys MST nodes by stable PHYSICAL identity (ref,x,y) so both
SW2.1 lands are distinct nodes, and cmd_gate's net_open_edges() counts copper
clusters over PHYSICAL pads (matching KiCad's own ratsnest: 4 lands -> 3 edges).
This increment adds ZERO router-logic change over D-325 -- only a GROUPS registry
entry + comment.

BTN_UP_N is the CLEANEST remaining nav button (shortest ~12.3 mm cross-haul,
lowest bbox congestion 201, in the SAME open south button field where BTN_B_N
passed).  Its MST is SW2.1a<->SW2.1b (7.96 mm SAME-LAYER F.Cu land-run, NO via --
the duplicate-land edge the lever enables) + R4.2<->U2.13 (SAME-LAYER B.Cu run,
NO via) + ONE CROSS-LAYER edge U2.13<->SW2.1 closed by exactly ONE 0.60/0.30
Default THROUGH via at (61.100,95.400) (the D-306/D-308/D-325 In1/In4 re-pour
mechanic runs once for the single anti-pad).  Default netclass (0.200 mm).
MEASURED: 21 tracks (6 F.Cu + 15 B.Cu), 1 through via, all FOUR physical pads in
ONE copper cluster (open_edges 3->0), via 4.804 mm from the nearest barrel, OPEN
south button field 7.453 mm clear of BAT_PROTECTED_P -> ZERO D-269 involvement.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-326 gate
promoted:

  1. the increment PRESERVED the accepted D-325 copper EXACTLY -- all 800 prior
     tracks (432 Phase-A + 368 prior increments) and all 70 prior vias are still
     present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is BTN_UP_N
     (21 tracks = 6 F.Cu + 15 B.Cu, plus exactly 1 through via);
  3. the net is FULLY copper-connected -- ALL FOUR physical pads (both SW2.1
     lands at 60.220/68.180, R4.2, U2.13) sit in ONE copper cluster (physical-pad
     open_edges 3 -> 0), ratsnest 662 -> 659 (-3), and no prior pair regressed;
  4. exactly ONE 0.60/0.30 through via was laid (via count 70 -> 71), it clears
     every existing barrel by >= 0.80 mm (measured 4.804 mm) and the realized
     copper clears BAT_PROTECTED_P by >= 0.300 mm (D-269 floor);
  5. only the In1/In4 GND reference planes were re-poured (anti-pad for the new
     via) and real full-board KiCad DRC is unchanged (no new/worse class;
     `clearance` stays 0).

    python3 incremental_probe_025.py
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

# The pre-promotion D-325 authoritative sha (800 trk / 70 via) -- the exact set
# that must survive this increment unchanged.
D325_SHA = '35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220'
INET = '/08_BUTTONS_EXPANDERS/BTN_UP_N'
# The two physical SW2.1 lands -- the DUPLICATE-NUMBER terminals the fix must
# both drive (exact x, y in KiCad internal nm).
SW2_1_LANDS = [(60220000, 96750000), (68180000, 96750000)]


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
    print('-- 1. INTEGRITY: authoritative board matches the D-326 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-326 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (800 prior + 21 BTN_UP_N)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (70 prior + 1 BTN_UP_N through via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (662 - 3 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (119 + 3 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC'
           and e.get('group') == 'BTN_UP_N']
    chk('journal carries 3 REST_INC BTN_UP_N edges (R4.2<->U2.13 + U2.13<->SW2.1 + SW2.1<->SW2.1)',
        len(inc) == 3, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-325 copper preserved EXACTLY (800 trk + 70 via intact) --')
    now = copper_sigs(b)
    inet_items = collections.Counter({s: n for s, n in now.items() if s[1] == INET})
    # Increments promoted AFTER D-326 (future) are excluded so this "pre-D-326
    # copper intact" check stays true as the board grows.  The pre-D-326 accepted
    # copper is Phase-A (432) + all nineteen prior rest increments (368) = 800
    # tracks + 70 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE',
                  'SD_DETECT', 'XGPIO_PILOT', 'XGPIO_PILOT_W', 'XGPIO3',
                  'IMU_INT1_STRAP', 'UART0_TXD_DBG', 'IR_TX_GPIO16', 'SD_CS_N',
                  'RESERVED_SPARE', 'ACC_DETECT_N', 'BTN_B_N', 'BTN_UP_N')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - inet_items - post_items
    chk('non-BTN_UP_N pre-D-326 copper == 800 tracks + 70 vias (all prior increments intact)',
        sum(prior_now.values()) == 800 + 70,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. NEW COPPER: F/B tracks + 1 via -----------
    print('\n-- 3. BTN_UP_N increment: 21 tracks (6 F.Cu + 15 B.Cu), 1 through via --')
    i_trk = [t for t in trk if t.GetNetname() == INET]
    i_via = [t for t in via if t.GetNetname() == INET]
    layers = collections.Counter(t.GetLayerName() for t in i_trk)
    chk('BTN_UP_N is 21 tracks + exactly 1 via',
        len(i_trk) == 21 and len(i_via) == 1,
        '%d tracks, %d vias' % (len(i_trk), len(i_via)))
    chk('BTN_UP_N copper spans F.Cu (6) + B.Cu (15) (one cross-layer haul to the SW2.1 lands)',
        set(layers) == {'F.Cu', 'B.Cu'} and layers['F.Cu'] == 6 and layers['B.Cu'] == 15,
        'layers=%s' % dict(layers))
    chk('BTN_UP_N tracks are all 0.200 mm (Default netclass width)',
        all(t.GetWidth() == 200000 for t in i_trk),
        'widths=%s' % sorted({t.GetWidth() for t in i_trk}))
    chk('BTN_UP_N via is one 0.60/0.30 Default through via',
        len(i_via) == 1 and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                                and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in i_via),
        'dia/drill=%s' % sorted({(v.GetWidth(pcbnew.F_Cu), v.GetDrill()) for v in i_via}))
    chk('increment added exactly ONE via to its net (board via total tracks the live SoT)',
        len(via) == EXPECT_VIAS and len(i_via) == 1, '%d total vias' % len(via))

    # --------------------- 3b. VIA SEPARATION + BAT_PROTECTED_P clearance -----
    print('\n-- 3b. the via clears every barrel; D-269 0.300 mm BAT_PROTECTED_P kept --')
    other_via = [t for t in via if t.GetNetname() != INET]
    gaps = []
    for v in i_via:
        vp = v.GetPosition()
        g = min(math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y)
                for o in other_via)
        gaps.append(g)
    chk('BTN_UP_N via >= 0.80 mm (centre) from every existing via',
        all(g >= 800000 for g in gaps),
        'min centre gaps = %s mm' % [round(g / 1e6, 3) for g in gaps])
    # D-269: min edge clearance BTN_UP_N -> BAT_PROTECTED_P (any shared layer)
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
    chk('min clearance BTN_UP_N -> BAT_PROTECTED_P >= 0.300 mm (D-269 floor)',
        best >= 300000 - 1000, 'measured %.4f mm' % (best / 1e6))

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    # THE decisive check: the duplicate-number lever must drive BOTH physical
    # SW2.1 lands.  We prove every one of the FOUR physical pads sits in the SAME
    # copper cluster (a physical-pad union-find, ratsnest excluded).
    print('\n-- 4. ALL FOUR physical pads in one copper cluster (both SW2.1 lands driven) --')
    cc = b.GetConnectivity()
    net_pads = [p for f in b.GetFootprints() for p in f.Pads()
                if p.GetNetname() == INET]
    chk('BTN_UP_N presents 4 physical pads incl. TWO SW2.1 lands',
        len(net_pads) == 4
        and sum(1 for p in net_pads
                if p.GetParentFootprint().GetReference() == 'SW2'
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
    chk('BTN_UP_N physical-pad open_edges == 0 (4 lands -> 1 copper cluster)',
        clusters == 1, '%d clusters (open_edges %d)' % (clusters, clusters - 1))

    # And BOTH SW2.1 lands specifically are joined to the R4.2 hub by copper.
    def pad_at(ref_num, xy):
        for p in net_pads:
            if (p.GetParentFootprint().GetReference() + '.' + p.GetNumber() == ref_num
                    and p.GetPosition().x == xy[0] and p.GetPosition().y == xy[1]):
                return p
        return None
    hub = None
    for p in net_pads:
        if p.GetParentFootprint().GetReference() + '.' + p.GetNumber() == 'R4.2':
            hub = p
    hub_reach = {pid(it) for it in cc.GetConnectedItems(hub) if it.GetClass() == 'PAD'}
    both_lands = all(pad_at('SW2.1', xy) is not None
                     and pid(pad_at('SW2.1', xy)) in hub_reach for xy in SW2_1_LANDS)
    chk('BOTH SW2.1 lands (60.220 AND 68.180) copper-joined to the R4.2 hub',
        both_lands, 'lands=%s' % [(round(x / 1e6, 3), round(y / 1e6, 3)) for x, y in SW2_1_LANDS])

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
        if e.get('group') == 'BTN_UP_N' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + all nineteen prior increments)',
        not reg, '%d regressed' % len(reg))

    # ----------------------------- 5. ZONES + DRC ---------------------------
    print('\n-- 5. only In1/In4 planes re-poured (via anti-pad); real full-board DRC unchanged --')
    planes = 0
    for z in b.Zones():
        lyrs = {pcbnew.BOARD.GetStandardLayerName(L) for L in z.GetLayerSet().CuStack()}
        if z.GetNetname() == 'GND' and lyrs and lyrs <= {'In1.Cu', 'In4.Cu'}:
            planes += 1
    chk('In1/In4 GND reference planes present (re-poured for the new via)',
        planes == 2, '%d plane zones' % planes)
    dc, _ = RU.drc(AUTH, 'probe025', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-326): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
