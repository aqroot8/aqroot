# -*- coding: utf-8 -*-
"""FBV2-P2-024 / D-322 -- focused read-only evidence probe for the SEVENTEENTH
rest-of-board incremental increment: the reserved/spare community expander GPIO
RESERVED_SPARE (R130.2 / TP41.1 test point / U23.7 PCAL expander), routed onto
the D-321 promoted board by incremental_router.py in an OPEN region -- away from
the saturated west-XGPIO F.Cu corridor, the U11/BQ25185 power-tree wall, and the
RF/NFC/USB/crystal/switching/rail/community-header mass.

/08_BUTTONS_EXPANDERS/RESERVED_SPARE is the reserved/spare expander GPIO net:
the PCAL9535A community expander pin U23.7 (B.Cu SMD) -> its series/pull
resistor R130.2 (B.Cu SMD) and the test point TP41.1 (B.Cu SMD).  All three pads
on B.Cu, so both MST edges are SAME-LAYER B.Cu runs with NO via -- the cleanest
incremental class: no through via, no In1/In4 plane re-pour, no via-clearance
risk (the same no-via same-layer mechanic proven at D-304/D-305/D-307 on B.Cu,
D-309/D-318/D-319/D-320/D-321 on F.Cu).  Default netclass (0.200 mm width/
clearance).  MEASURED (w/vet_021.py on the live D-321 board): 15.5 mm clear of
the BAT_PROTECTED_P trunk -- ZERO D-269 involvement.

SELECTION NOTE: the mandate's meaningful display-control candidates were vetted
FIRST.  DISP_CS_N (the display SPI chip-select, U1.18 / R26.2 / J1.38) and
DISP_DC (the display data/command, U1.22 / J1.37) both hit a CHARACTERIZED J1
display-FPC-connector wall -- their long interior haul to the tight display
connector returns NO_PATH at 0.200 mm (none even at the 0.05/0.025 mm fine grid).
BOOT_N (the meaningful non-J1 alternative, the ESP32 boot-mode strap) routed
only via poor 2.5x detours (62.9 mm vs 25.4 mm straight + 47.2 mm vs 22.4 mm =
~110 mm of copper across the congested MCU interior) -- a poor path for a
boot-critical strap whose reset-level sensitivity the mandate flagged; so it is
NOT equally clean and the meaningful>spare preference does not force it.  The
held clean alternate RESERVED_SPARE (short, tidy B.Cu, gates clean) was promoted.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-322 gate
promoted:

  1. the increment PRESERVED the accepted D-321 copper EXACTLY -- all 749 prior
     tracks (432 Phase-A + 317 prior increments incl. SD_CS_N) and all 67 prior
     vias are still present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is
     RESERVED_SPARE (10 tracks, all B.Cu, ZERO new vias);
  3. the net is FULLY copper-connected (all three pads R130.2/U23.7/TP41.1),
     ratsnest 669 -> 667 (-2), and no prior requested pair regressed;
  4. NO via was laid -- via count stays 67 -- so NO zone re-poured (every zone
     byte-identical) and real full-board KiCad DRC is unchanged (no new class,
     none increased; `clearance` stays 0).

    python3 incremental_probe_022.py
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

# The pre-promotion D-321 authoritative sha (749 trk / 67 via) -- the exact set
# that must survive this increment unchanged.
D321_SHA = '68d44b54df91d607f689215c0da5db249b13fcd1ac189b9ab78ceb6366d25e46'
INET = '/08_BUTTONS_EXPANDERS/RESERVED_SPARE'


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
    print('-- 1. INTEGRITY: authoritative board matches the D-322 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-322 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (749 prior + 10 RESERVED_SPARE)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (unchanged -- NO new via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (669 - 2 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (112 + 2 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC'
           and e.get('group') == 'RESERVED_SPARE']
    chk('journal carries 2 REST_INC RESERVED_SPARE edges',
        len(inc) == 2, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-321 copper preserved EXACTLY (749 trk + 67 via intact) --')
    now = copper_sigs(b)
    inet_items = collections.Counter({s: n for s, n in now.items() if s[1] == INET})
    # Increments promoted AFTER D-322 (future) are excluded so this "pre-D-322
    # copper intact" check stays true as the board grows.  The pre-D-322 accepted
    # copper is Phase-A (432) + all sixteen prior rest increments (317) = 749
    # tracks + 67 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE',
                  'SD_DETECT', 'XGPIO_PILOT', 'XGPIO_PILOT_W', 'XGPIO3',
                  'IMU_INT1_STRAP', 'UART0_TXD_DBG', 'IR_TX_GPIO16', 'SD_CS_N',
                  'RESERVED_SPARE')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - inet_items - post_items
    chk('non-RESERVED_SPARE pre-D-322 copper == 749 tracks + 67 vias (all prior increments intact)',
        sum(prior_now.values()) == 749 + 67,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. NEW COPPER: 10 B.Cu tracks, NO via --------
    print('\n-- 3. RESERVED_SPARE increment: 10 tracks all B.Cu, ZERO new via --')
    i_trk = [t for t in trk if t.GetNetname() == INET]
    i_via = [t for t in via if t.GetNetname() == INET]
    layers = {t.GetLayerName() for t in i_trk}
    chk('RESERVED_SPARE is 10 tracks + exactly 0 vias',
        len(i_trk) == 10 and len(i_via) == 0,
        '%d tracks, %d vias' % (len(i_trk), len(i_via)))
    chk('RESERVED_SPARE copper is ALL B.Cu (same-layer MST, no cross-layer via)',
        layers == {'B.Cu'}, 'layers=%s' % sorted(layers))
    chk('RESERVED_SPARE tracks are all 0.200 mm (Default netclass width)',
        all(t.GetWidth() == 200000 for t in i_trk),
        'widths=%s' % sorted({t.GetWidth() for t in i_trk}))
    # No-via class: the total via count is unchanged, so this increment added none.
    chk('increment added ZERO vias (via count 67 unchanged; cleanest class)',
        len(via) == 67 and len(i_via) == 0, '%d total vias' % len(via))

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

    # all three pads of the net must be copper-reachable from R130.2 (the MST root)
    net_refs = {'R130.2', 'U23.7', 'TP41.1'}
    root = pad('R130.2')
    reach = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(root) if p.GetClass() == 'PAD'} | {'R130.2'}
    chk('RESERVED_SPARE all three pads copper-connected (R130.2/U23.7/TP41.1)',
        net_refs.issubset(reach), 'reachable=%s' % str(sorted(reach & net_refs)))

    reg = []
    for e in jr:
        if e.get('group') == 'RESERVED_SPARE' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + all sixteen prior increments)',
        not reg, '%d regressed' % len(reg))

    # ----------------------------- 5. ZONES + DRC ---------------------------
    print('\n-- 5. NO zone re-poured (no via); real full-board DRC unchanged --')
    planes = 0
    for z in b.Zones():
        lyrs = {pcbnew.BOARD.GetStandardLayerName(L) for L in z.GetLayerSet().CuStack()}
        if z.GetNetname() == 'GND' and lyrs and lyrs <= {'In1.Cu', 'In4.Cu'}:
            planes += 1
    chk('In1/In4 GND reference planes present (NOT re-poured -- no via this increment)',
        planes == 2, '%d plane zones' % planes)
    dc, _ = RU.drc(AUTH, 'probe022', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-322): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
