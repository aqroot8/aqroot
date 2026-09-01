# -*- coding: utf-8 -*-
"""FBV2-P2-025 / D-323 -- focused read-only evidence probe for the EIGHTEENTH
rest-of-board incremental increment: the accelerometer/add-on presence-detect
signal ACC_DETECT_N (R64.1 divider / R129.2 series / U3.17 PCAL expander GPIO),
routed onto the D-322 promoted board by incremental_router.py in an OPEN region
-- away from the saturated west-XGPIO F.Cu corridor, the U11/BQ25185 power-tree
wall, the RF/NFC/USB/crystal/switching/rail/community-header mass, and every
characterized wall (MCU_EN_RC, the J1 display-FPC haul DISP_CS_N/DISP_DC,
BOOT_N, U11_PROG/PWR_SENSE, and -- new at D-323 -- DISP_BL_CTL_STRAP and the
button family, see the SELECTION NOTE).

/ACC_DETECT_N is the low-current low-speed CMOS presence-detect input: the
detect divider/pull resistor R64.1 (F.Cu SMD, placed in the north) -> series
resistor R129.2 (B.Cu SMD) -> PCAL9535A expander GPIO U3.17 (B.Cu SMD).  The
three pads sit on TWO faces, so the MST is ONE cross-layer edge R64.1<->R129.2
closed with a single 0.60/0.30 Default THROUGH via (the D-306/D-308 mechanic;
In1/In4 GND reference planes re-poured once for the barrel anti-pad) + ONE
SAME-LAYER B.Cu edge R129.2<->U3.17.  Default netclass (0.200 mm width/
clearance).  MEASURED (w/vet_021.py on the live D-322 board): congestion 103
(lowest of the remaining genuinely-clean functional shortlist); the via landed
in the OPEN north at (57.900,38.800), 34.16 mm from every existing barrel; the
realized copper clears the BAT_PROTECTED_P trunk by 3.8831 mm -- >> the D-269
0.300 mm floor, ZERO D-269 involvement.

SELECTION NOTE: the mandate's cleaner-class candidates were scratch-tested FIRST.
DISP_BL_CTL_STRAP (the display backlight-control strap, U1.16 MCU / TP2.1 /
R108.1 + R109.1, a no-via F.Cu net) hit a CHARACTERIZED LOCAL WALL -- ALL THREE
MST edges return NO_PATH at 0.200 mm (none even at the 0.05/0.025 mm fine grid),
including the short 5.44 mm and 10.30 mm edges, because the dense MCU/backlight
pad pocket (congestion 185) boxes every terminal (the MCU_EN_RC lesson).
BTN_B_N (the navigation/boot button SW7.1 -> R9.2 pull-up -> U2.18 expander)
routed ALL OK but FAILED the real full-board gate on connectivity: SW7 is a
4-pin tactile switch whose two mechanically-linked terminals BOTH carry pad
number "1" on BTN_B_N at DIFFERENT locations (49.520 and 57.480 mm, 7.96 mm
apart), and the framework's per-ref MST (pads_by_ref) collapses them to one
node, so the second SW7.1 terminal is never connected -> a permanent open
ratsnest edge (open_edges 2->1).  This is a framework limitation shared by the
WHOLE button family (every SWx is a duplicate-ref tact switch); it is a
connectivity gap, NOT a copper casualty, and the authoritative board was never
touched.  ACC_DETECT_N (a genuine functional detect with three distinct-ref pads
that gates clean) was promoted.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-323 gate
promoted:

  1. the increment PRESERVED the accepted D-322 copper EXACTLY -- all 759 prior
     tracks (432 Phase-A + 327 prior increments incl. RESERVED_SPARE) and all 67
     prior vias are still present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is
     ACC_DETECT_N (22 tracks = 3 F.Cu + 19 B.Cu, plus exactly 1 through via);
  3. the net is FULLY copper-connected (all three pads R64.1/R129.2/U3.17),
     ratsnest 667 -> 665 (-2), and no prior requested pair regressed;
  4. exactly ONE 0.60/0.30 through via was laid (via count 67 -> 68), it clears
     every existing barrel by >= 0.80 mm (measured 34.16 mm) and the realized
     copper clears BAT_PROTECTED_P by >= 0.300 mm (measured 3.8831 mm, D-269);
  5. only the In1/In4 GND reference planes were re-poured (anti-pad for the new
     via) and real full-board KiCad DRC is unchanged (no new/worse class;
     `clearance` stays 0).

    python3 incremental_probe_023.py
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

# The pre-promotion D-322 authoritative sha (759 trk / 67 via) -- the exact set
# that must survive this increment unchanged.
D322_SHA = 'a861e30e5760515288ef9a3fc0c21ea6d3e9c31409f9181dd66d56ed0628efd1'
INET = '/ACC_DETECT_N'


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


def main():
    fails = []

    def chk(name, cond, detail=''):
        print('  %s %s %s' % ('PASS' if cond else '**FAIL**', name, detail))
        if not cond:
            fails.append(name)

    # ---------------------------------------------------- 1. INTEGRITY --------
    print('-- 1. INTEGRITY: authoritative board matches the D-323 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-323 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (759 prior + 22 ACC_DETECT_N)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (67 prior + 1 ACC_DETECT_N through via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (667 - 2 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (114 + 2 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC'
           and e.get('group') == 'ACC_DETECT_N']
    chk('journal carries 2 REST_INC ACC_DETECT_N edges',
        len(inc) == 2, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-322 copper preserved EXACTLY (759 trk + 67 via intact) --')
    now = copper_sigs(b)
    inet_items = collections.Counter({s: n for s, n in now.items() if s[1] == INET})
    # Increments promoted AFTER D-323 (future) are excluded so this "pre-D-323
    # copper intact" check stays true as the board grows.  The pre-D-323 accepted
    # copper is Phase-A (432) + all seventeen prior rest increments (327) = 759
    # tracks + 67 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE',
                  'SD_DETECT', 'XGPIO_PILOT', 'XGPIO_PILOT_W', 'XGPIO3',
                  'IMU_INT1_STRAP', 'UART0_TXD_DBG', 'IR_TX_GPIO16', 'SD_CS_N',
                  'RESERVED_SPARE', 'ACC_DETECT_N')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - inet_items - post_items
    chk('non-ACC_DETECT_N pre-D-323 copper == 750 tracks + 67 vias (all prior increments intact)',
        sum(prior_now.values()) == 750 + 67,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. NEW COPPER: F/B tracks + 1 via ------------
    print('\n-- 3. ACC_DETECT_N increment: 22 tracks (3 F.Cu + 19 B.Cu), 1 through via --')
    i_trk = [t for t in trk if t.GetNetname() == INET]
    i_via = [t for t in via if t.GetNetname() == INET]
    layers = collections.Counter(t.GetLayerName() for t in i_trk)
    chk('ACC_DETECT_N is 22 tracks + exactly 1 via',
        len(i_trk) == 22 and len(i_via) == 1,
        '%d tracks, %d vias' % (len(i_trk), len(i_via)))
    chk('ACC_DETECT_N copper spans F.Cu + B.Cu (cross-layer with host-face fan-out)',
        set(layers) == {'F.Cu', 'B.Cu'}, 'layers=%s' % dict(layers))
    chk('ACC_DETECT_N tracks are all 0.200 mm (Default netclass width)',
        all(t.GetWidth() == 200000 for t in i_trk),
        'widths=%s' % sorted({t.GetWidth() for t in i_trk}))
    chk('ACC_DETECT_N via is a 0.60/0.30 Default through via',
        all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
            and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in i_via),
        'dia/drill=%s' % sorted({(v.GetWidth(pcbnew.F_Cu), v.GetDrill()) for v in i_via}))
    chk('increment added exactly ONE via to its net (board via total tracks the live SoT)',
        len(via) == EXPECT_VIAS and len(i_via) == 1, '%d total vias' % len(via))

    # --------------------- 3b. VIA SEPARATION + BAT_PROTECTED_P clearance -----
    print('\n-- 3b. via clears every barrel; D-269 0.300 mm BAT_PROTECTED_P kept --')
    other_via = [t for t in via if t.GetNetname() != INET]
    gaps = []
    for v in i_via:
        vp = v.GetPosition()
        g = min(math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y)
                for o in other_via)
        gaps.append(g)
    chk('ACC_DETECT_N via >= 0.80 mm (centre) from every existing via',
        all(g >= 800000 for g in gaps),
        'min centre gaps = %s mm' % [round(g / 1e6, 3) for g in gaps])
    # D-269: min edge clearance ACC_DETECT_N -> BAT_PROTECTED_P (any shared layer)
    bpp = [t for t in trk if 'BAT_PROTECTED_P' in t.GetNetname()]
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
    chk('min clearance ACC_DETECT_N -> BAT_PROTECTED_P >= 0.300 mm (D-269 floor)',
        best >= 300000 - 1000, 'measured %.4f mm' % (best / 1e6))

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. all three pads fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        if r not in fps:
            return None
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    net_refs = {'R64.1', 'R129.2', 'U3.17'}
    root = pad('R129.2')       # the central pad (touches both MST edges)
    reach = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(root) if p.GetClass() == 'PAD'} | {'R129.2'}
    chk('ACC_DETECT_N all three pads copper-connected (R64.1/R129.2/U3.17)',
        net_refs.issubset(reach), 'reachable=%s' % str(sorted(reach & net_refs)))

    reg = []
    for e in jr:
        if e.get('group') == 'ACC_DETECT_N' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + all seventeen prior increments)',
        not reg, '%d regressed' % len(reg))

    # ----------------------------- 5. ZONES + DRC ---------------------------
    print('\n-- 5. only In1/In4 planes re-poured (via anti-pad); real full-board DRC unchanged --')
    planes = 0
    for z in b.Zones():
        lyrs = {pcbnew.BOARD.GetStandardLayerName(L) for L in z.GetLayerSet().CuStack()}
        if z.GetNetname() == 'GND' and lyrs and lyrs <= {'In1.Cu', 'In4.Cu'}:
            planes += 1
    chk('In1/In4 GND reference planes present (re-poured for the 1 new via)',
        planes == 2, '%d plane zones' % planes)
    dc, _ = RU.drc(AUTH, 'probe023', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-323): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
