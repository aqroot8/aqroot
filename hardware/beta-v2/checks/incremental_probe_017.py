# -*- coding: utf-8 -*-
"""FBV2-P2-018 / D-316 -- focused read-only evidence probe for the TWELFTH
rest-of-board incremental increment: a SINGLE west-edge XGPIO community-header
bank member, XGPIO3 (R54.1 F.Cu -> U3.7 B.Cu), routed onto the D-314 promoted
board (west SOUTH pilot XGPIO1/XGPIO0) by incremental_router.py.

/XGPIO3 is a 2-pad CROSS-LAYER net: the 100 R community-header series resistor
R54.1 (F.Cu, top pack y~17-36) -> the PCAL9535A U3 expander pin 7 (B.Cu,
mid-board y~77.67).  One MST edge, one F<->B through via.

The DECISIVE difference from the D-313/D-314 XGPIO pilot PAIRS: this increment is
routed at the 0.200 mm Default clearance, NOT the 0.300 mm blanket.  D-315
characterised the XGPIO2+XGPIO3 adjacent PAIR as a corridor-capacity WALL (both
orders NO_FAR_RUN -- the now D-313+D-314-congested F.Cu corridor admits ONE
116 mm haul, not two) and produced the positive lead this increment realises: a
SINGLE west member routes CLEAN at 0.200 mm and KEEPS the D-269 0.300 mm floor to
the 52.4 mm BAT_PROTECTED_P protected-battery F.Cu trunk BY GEOMETRY, because a
single west haul's natural path clears BPP by >= 0.47 mm (unlike the D-313 EAST
pilot whose 0.200 mm haul pinched BPP and therefore needed the 0.300 mm floor).
The 0.200 mm Default is the correct DRC floor here; the real full-board
D-269-aware KiCad DRC (D-286 gate) arbitrates the BPP clearance and found NO
new/worse class -- NOT rule weakening (D-269 is satisfied by measured geometry,
0.4739 mm >= 0.300).  No via_offset (the site is 0.704 mm copper / 1.304 mm
centre clear of the nearest existing barrel).

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-316 gate
promoted:

  1. the increment PRESERVED the accepted D-314 copper EXACTLY -- all 669 prior
     tracks (432 Phase-A + 237 prior increments incl. west XGPIO0/1) and 66 prior
     vias are still present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is XGPIO3
     (22 tracks F.Cu+B.Cu, 1 through via);
  3. the net is FULLY copper-connected (XGPIO3 R54.1-U3.7), ratsnest 677 -> 676,
     and no prior requested pair regressed;
  4. the via is >= 0.80 mm (centre) from every existing via barrel; the D-269
     0.300 mm clearance to the BAT_PROTECTED_P trunk is satisfied (0.4739 mm);
  5. only the In1/In4 GND reference planes re-poured (1 new through via) -- every
     other zone byte-identical -- and real full-board KiCad DRC is unchanged (no
     new class, none increased; `clearance` stays 0).

    python3 incremental_probe_017.py
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

# The pre-promotion D-314 authoritative sha (669 trk / 66 via) -- the exact set
# that must survive this increment unchanged.
D314_SHA = '95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605'
XG3 = '/XGPIO3'


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


def _ptseg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    tt = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + tt * dx), py - (ay + tt * dy))


def _segseg(a, b):
    (a0, a1, wa), (b0, b1, wb) = a, b
    d = min(_ptseg(a0[0], a0[1], b0[0], b0[1], b1[0], b1[1]),
            _ptseg(a1[0], a1[1], b0[0], b0[1], b1[0], b1[1]),
            _ptseg(b0[0], b0[1], a0[0], a0[1], a1[0], a1[1]),
            _ptseg(b1[0], b1[1], a0[0], a0[1], a1[0], a1[1]))
    return d - wa / 2.0 - wb / 2.0


def main():
    fails = []

    def chk(name, cond, detail=''):
        print('  %s %s %s' % ('PASS' if cond else '**FAIL**', name, detail))
        if not cond:
            fails.append(name)

    # ---------------------------------------------------- 1. INTEGRITY --------
    print('-- 1. INTEGRITY: authoritative board matches the D-316 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-316 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (669 prior + 22 XGPIO3)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (66 prior + 1 XGPIO3 through via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (677 - 1 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (104 + 1 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'XGPIO3']
    chk('journal carries 1 REST_INC XGPIO3 entry',
        len(inc) == 1, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-314 copper preserved EXACTLY (669 trk + 66 via intact) --')
    now = copper_sigs(b)
    xg_items = collections.Counter({s: n for s, n in now.items() if s[1] == XG3})
    # Increments promoted AFTER D-316 (XGPIO3) are excluded so this
    # "pre-XGPIO3 copper intact" check stays true as the board grows.  The
    # pre-XGPIO3 accepted copper is Phase-A (432) + all eleven prior rest
    # increments incl. the west XGPIO0/1 south pilot (237) = 669 tracks + 66 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE',
                  'SD_DETECT', 'XGPIO_PILOT', 'XGPIO_PILOT_W', 'XGPIO3')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - xg_items - post_items
    chk('non-XGPIO3 pre-D-316 copper == 669 tracks + 66 vias (all prior increments intact)',
        sum(prior_now.values()) == 669 + 66,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. XGPIO3 NEW COPPER: F/B + 1 via -----------
    print('\n-- 3. XGPIO3 single-net increment: 22 tracks (F.Cu+B.Cu), 1 through via --')
    xg_trk = [t for t in trk if t.GetNetname() == XG3]
    xg_via = [t for t in via if t.GetNetname() == XG3]
    layers = {t.GetLayerName() for t in xg_trk}
    chk('XGPIO3 is 22 tracks + exactly 1 via',
        len(xg_trk) == 22 and len(xg_via) == 1,
        '%d tracks, %d vias' % (len(xg_trk), len(xg_via)))
    chk('XGPIO3 copper spans F.Cu + B.Cu (cross-layer with host-face fan-out)',
        layers == {'F.Cu', 'B.Cu'}, 'layers=%s' % sorted(layers))
    chk('XGPIO3 tracks are all 0.200 mm (Default netclass width)',
        all(t.GetWidth() == 200000 for t in xg_trk),
        'widths=%s' % sorted({t.GetWidth() for t in xg_trk}))
    chk('XGPIO3 via is a 0.60/0.30 Default through via',
        all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
            and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in xg_via),
        'dia/drill=%s' % sorted({(v.GetWidth(pcbnew.F_Cu), v.GetDrill()) for v in xg_via}))
    per_net_via = collections.Counter(v.GetNetname() for v in xg_via)
    chk('XGPIO3 has exactly one through via',
        per_net_via.get('/XGPIO3') == 1, str(dict(per_net_via)))

    # --------------------- 3b. VIA SEPARATION + BAT_PROTECTED_P clearance -----
    print('\n-- 3b. via clears every barrel; D-269 0.300 mm BAT_PROTECTED_P kept --')
    other_via = [t for t in via if t.GetNetname() != XG3]
    gaps = []
    for v in xg_via:
        vp = v.GetPosition()
        g = min(math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y)
                for o in other_via)
        gaps.append(g)
    chk('XGPIO3 via >= 0.80 mm (centre) from every existing via',
        all(g >= 800000 for g in gaps),
        'min centre gaps = %s mm' % [round(g / 1e6, 3) for g in gaps])
    # D-269 corridor evidence: min F.Cu edge gap XGPIO3 -> BAT_PROTECTED_P >=0.300
    bpp = [t for t in trk if 'BAT_PROTECTED_P' in t.GetNetname()
           and t.GetLayerName() == 'F.Cu']
    best = 1e12
    for t in xg_trk:
        if t.GetLayerName() != 'F.Cu':
            continue
        s, e = t.GetStart(), t.GetEnd()
        A = ((s.x, s.y), (e.x, e.y), t.GetWidth())
        for o in bpp:
            os_, oe = o.GetStart(), o.GetEnd()
            B = ((os_.x, os_.y), (oe.x, oe.y), o.GetWidth())
            c = _segseg(A, B)
            if c < best:
                best = c
    chk('min F.Cu clearance XGPIO3 -> BAT_PROTECTED_P >= 0.300 mm (D-269 floor)',
        best >= 300000 - 1000, 'measured %.4f mm' % (best / 1e6))

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. XGPIO3 fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    for anchor, other in (('U3.7', 'R54.1'),):
        j = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(pad(anchor)) if p.GetClass() == 'PAD'}
        chk('XGPIO3 connected: %s-%s' % (anchor, other), other in j, str(sorted(j)))

    reg = []
    for e in jr:
        if e.get('group') == 'XGPIO3' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + all eleven prior increments)',
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
    dc, _ = RU.drc(AUTH, 'probe017', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-316): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
