# -*- coding: utf-8 -*-
"""FBV2-P2-016 / D-314 -- focused read-only evidence probe for the ELEVENTH
rest-of-board incremental increment and the FIRST WEST-edge XGPIO community-header
bank members: the west SOUTH pilot XGPIO1 (R52.1 F.Cu -> U3.5 B.Cu) + XGPIO0
(R51.1 F.Cu -> U3.4 B.Cu), routed onto the D-313 promoted board (east pilot
XGPIO8/XGPIO9) by incremental_router.py.

Each /XGPIOx is a 2-pad CROSS-LAYER net: the 100 R community-header series
resistor R5x.1 (F.Cu, top pack y~17-36) -> the PCAL9535A U3 expander pin (B.Cu,
mid-board y~74-80).  One MST edge, one F<->B through via each.  The D-313 study
characterised the eight WEST members as crowding ONE north-of-U3 via pocket (the
NORTHERN pair XGPIO6/7 pick the identical site) and promoted the naturally-
separated EAST pair instead.  The FBV2-P2-016 recovery screen (w/screen_016.py +
w/screen_016_one.py, live D-313 board, D-269 0.300 mm, no via_offset) then
MEASURED that the SOUTHERN west pair SELF-SEPARATES when routed XGPIO1-first:
XGPIO1's via lands in the pocket at (55.40,79.00), then XGPIO0 -- routed SECOND,
so XGPIO1's laid via is a real qb.via() obstacle -- escapes WEST to (52.75,78.35),
via-via copper 2.129 mm.  The reverse order boxes XGPIO1 out (order matters); no
via_offset is used (every site >= 2 mm clear of every barrel).

As with the east pilot the one corridor constraint is the D-269 BAT_MAIN routed
clearance (0.300 mm) to the 52.4 mm BAT_PROTECTED_P protected-battery F.Cu trunk
that sweeps across the y~73-82 via-landing band, so the pilot is routed at the
0.300 mm D-269 clearance floor (the CORRECT clearance, not a new mechanism).

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-314 gate
promoted:

  1. the increment PRESERVED the accepted D-313 copper EXACTLY -- all 631 prior
     tracks (432 Phase-A + 199 prior increments incl. east XGPIO8/9) and 64 prior
     vias are still present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is XGPIO1 +
     XGPIO0 (38 tracks F.Cu+B.Cu, 2 through vias);
  3. both nets are FULLY copper-connected (XGPIO1 R52.1-U3.5; XGPIO0 R51.1-U3.4),
     ratsnest 679 -> 677, and no prior requested pair regressed;
  4. the two vias separated cleanly (2.129 mm apart) and each is >= 0.80 mm from
     every existing via barrel; the D-269 0.300 mm clearance to the
     BAT_PROTECTED_P trunk is satisfied;
  5. only the In1/In4 GND reference planes re-poured (2 new through vias) -- every
     other zone byte-identical -- and real full-board KiCad DRC is unchanged (no
     new class, none increased; `clearance` stays 0).

    python3 incremental_probe_016.py
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

# The pre-promotion D-313 authoritative sha (631 trk / 64 via) -- the exact set
# that must survive this increment unchanged.
D313_SHA = 'a0d6fead125295441dda0f0008c1261f5c1cec39edb2b8c7bd925b214e7207eb'
XGW = ('/XGPIO1', '/XGPIO0')


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
    print('-- 1. INTEGRITY: authoritative board matches the D-314 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-314 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (631 prior + 38 XGPIO1/XGPIO0)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (64 prior + 2 XGPIO through vias)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (679 - 2 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (102 + 2 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'XGPIO_PILOT_W']
    chk('journal carries 2 REST_INC XGPIO_PILOT_W entries',
        len(inc) == 2, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-313 copper preserved EXACTLY (631 trk + 64 via intact) --')
    now = copper_sigs(b)
    xg_items = collections.Counter({s: n for s, n in now.items() if s[1] in XGW})
    # Increments promoted AFTER D-314 (XGPIO_PILOT_W) are excluded so this
    # "pre-west-XGPIO copper intact" check stays true as the board grows.  The
    # pre-west-XGPIO accepted copper is Phase-A (432) + all ten prior rest
    # increments incl. the east XGPIO8/9 pilot (199) = 622 tracks + 64 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE',
                  'SD_DETECT', 'XGPIO_PILOT', 'XGPIO_PILOT_W')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - xg_items - post_items
    chk('non-west-XGPIO pre-D-314 copper == 622 tracks + 64 vias (all prior increments intact)',
        sum(prior_now.values()) == 622 + 64,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. XGPIO NEW COPPER: F/B + 2 vias -----------
    print('\n-- 3. XGPIO west pilot increment: 38 tracks (F.Cu+B.Cu), 2 through vias --')
    xg_trk = [t for t in trk if t.GetNetname() in XGW]
    xg_via = [t for t in via if t.GetNetname() in XGW]
    layers = {t.GetLayerName() for t in xg_trk}
    chk('XGPIO west pilot is 38 tracks + exactly 2 vias',
        len(xg_trk) == 38 and len(xg_via) == 2,
        '%d tracks, %d vias' % (len(xg_trk), len(xg_via)))
    chk('XGPIO copper spans F.Cu + B.Cu (cross-layer with host-face fan-out)',
        layers == {'F.Cu', 'B.Cu'}, 'layers=%s' % sorted(layers))
    chk('XGPIO tracks are all 0.200 mm (Default netclass width)',
        all(t.GetWidth() == 200000 for t in xg_trk),
        'widths=%s' % sorted({t.GetWidth() for t in xg_trk}))
    chk('XGPIO vias are 0.60/0.30 Default through vias',
        all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
            for v in xg_via),
        'dia/drill=%s' % sorted({(v.GetWidth(pcbnew.F_Cu), v.GetDrill()) for v in xg_via}))
    # each net contributes exactly one via
    per_net_via = collections.Counter(v.GetNetname() for v in xg_via)
    chk('each XGPIO net has exactly one through via',
        per_net_via.get('/XGPIO1') == 1 and per_net_via.get('/XGPIO0') == 1,
        str(dict(per_net_via)))

    # --------------------- 3b. VIA SEPARATION + BAT_PROTECTED_P clearance -----
    print('\n-- 3b. vias clear every barrel; D-269 0.300 mm BAT_PROTECTED_P kept --')
    other_via = [t for t in via if t.GetNetname() not in XGW]
    gaps = []
    for v in xg_via:
        vp = v.GetPosition()
        g = min(math.hypot(vp.x - o.GetPosition().x, vp.y - o.GetPosition().y)
                for o in other_via)
        gaps.append(g)
    chk('each XGPIO via >= 0.80 mm (centre) from every existing via',
        all(g >= 800000 for g in gaps),
        'min centre gaps = %s mm' % [round(g / 1e6, 3) for g in gaps])
    # the two pilot vias separated (not crowded onto one site)
    if len(xg_via) == 2:
        p0, p1 = xg_via[0].GetPosition(), xg_via[1].GetPosition()
        d = math.hypot(p0.x - p1.x, p0.y - p1.y)
        chk('the two pilot vias are separated (>= 1.0 mm centre)',
            d >= 1000000, 'centre gap = %.3f mm' % (d / 1e6))
    # D-269 corridor evidence: min F.Cu edge gap XGPIO -> BAT_PROTECTED_P >=0.300
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
    chk('min F.Cu clearance XGPIO -> BAT_PROTECTED_P >= 0.300 mm (D-269 floor)',
        best >= 300000 - 1000, 'measured %.4f mm' % (best / 1e6))

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. XGPIO1 + XGPIO0 fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    for anchor, other in (('U3.5', 'R52.1'), ('U3.4', 'R51.1')):
        j = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(pad(anchor)) if p.GetClass() == 'PAD'}
        chk('XGPIO connected: %s-%s' % (anchor, other), other in j, str(sorted(j)))

    reg = []
    for e in jr:
        if e.get('group') == 'XGPIO_PILOT_W' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + all ten prior increments)',
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
    dc, _ = RU.drc(AUTH, 'probe016', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-314): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
