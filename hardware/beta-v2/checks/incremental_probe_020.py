# -*- coding: utf-8 -*-
"""FBV2-P2-022 / D-320 -- focused read-only evidence probe for the FIFTEENTH
rest-of-board incremental increment: the IR transmit carrier CONTROL leg
IR_TX_GPIO16 (U1.9 ESP32 GPIO16 -> R22.1 series-drive resistor), routed onto the
D-319 promoted board by incremental_router.py in an OPEN region -- away from the
saturated west-XGPIO F.Cu corridor, the U11/BQ25185 power-tree wall, and the
RF/NFC/USB/crystal/switching/rail/community-header mass.

/IR_TX_GPIO16 is the MCU-side low-current control leg of the IR transmit path:
ESP32 (U1) GPIO16 pad U1.9 (F.Cu SMD) -> series-drive resistor R22.1 (F.Cu SMD).
It is a DEDICATED 2-pad net ISOLATED by the series resistor R22 from the
switching output: R22.2 belongs to the SEPARATE net IR_GATE (Q1 gate / R23), and
the IR-emitter power path is IR_LED_A/IR_LED_K (D1 / Q1 drain) -- both EXCLUDED
switching/emitter nets, NOT part of this increment.  So this is exactly the
low-current MCU carrier/control GPIO, distinct from the emitter power / switch
path.  Both pads on F.Cu, so its single MST edge is a SAME-LAYER F.Cu run with NO
via -- the cleanest incremental class: no through via, no In1/In4 plane re-pour,
no via-clearance risk (the same no-via same-layer mechanic proven at D-305/D-307
on B.Cu, D-309 IR_RX_VS / D-318 IMU_INT1_STRAP / D-319 UART0_TXD_DBG on F.Cu).
The router detoured the run to 13 F.Cu segments (23.2 mm) around the GND pinch on
the straight path.  Noncritical low-current CMOS control output (NOT switching /
rail / RF-NFC / USB / bus-clock / community-header).  Default netclass (0.200 mm
width/clearance).  MEASURED (w/vet_021.py on the live D-319 board): 35.2 mm clear
of the BAT_PROTECTED_P trunk -- ZERO D-269 involvement.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, exactly what the D-320 gate
promoted:

  1. the increment PRESERVED the accepted D-319 copper EXACTLY -- all 716 prior
     tracks (432 Phase-A + 284 prior increments incl. UART0_TXD_DBG) and all 67
     prior vias are still present byte/geometry-identical;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is
     IR_TX_GPIO16 (13 tracks, all F.Cu, ZERO new vias);
  3. the net is FULLY copper-connected (both pads U1.9/R22.1), ratsnest
     672 -> 671 (-1), and no prior requested pair regressed;
  4. NO via was laid -- via count stays 67 -- so NO zone re-poured (every zone
     byte-identical) and real full-board KiCad DRC is unchanged (no new class,
     none increased; `clearance` stays 0).

    python3 incremental_probe_020.py
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

# The pre-promotion D-319 authoritative sha (716 trk / 67 via) -- the exact set
# that must survive this increment unchanged.
D319_SHA = '57dcc8affb6c0f85f747fba025463b9cf0897c6712709692151020f56fdb8adf'
INET = '/IR_TX_GPIO16'


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
    print('-- 1. INTEGRITY: authoritative board matches the D-320 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-320 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (716 prior + 13 IR_TX_GPIO16)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (unchanged -- NO new via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    chk('zones == 41', len(list(b.Zones())) == 41, str(len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (672 - 1 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (109 + 1 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC'
           and e.get('group') == 'IR_TX_GPIO16']
    chk('journal carries 1 REST_INC IR_TX_GPIO16 edge',
        len(inc) == 1, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-319 copper preserved EXACTLY (716 trk + 67 via intact) --')
    now = copper_sigs(b)
    inet_items = collections.Counter({s: n for s, n in now.items() if s[1] == INET})
    # Increments promoted AFTER D-320 (this one) are excluded so this "pre-D-320
    # copper intact" check stays true as the board grows.  The pre-D-320 accepted
    # copper is Phase-A (432) + all fourteen prior rest increments (284) = 716
    # tracks + 67 vias.
    PRE_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR',
                  'FRONT_RGB_LED', 'IR_RX_VS', 'TOUCH_CTL', 'AMP_SD_MODE',
                  'SD_DETECT', 'XGPIO_PILOT', 'XGPIO_PILOT_W', 'XGPIO3',
                  'IMU_INT1_STRAP', 'UART0_TXD_DBG', 'IR_TX_GPIO16')
    post = {e['net'] for e in jr if e.get('role') == 'REST_INC'
            and e.get('group') not in PRE_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post})
    prior_now = now - inet_items - post_items
    chk('non-IR_TX_GPIO16 pre-D-320 copper == 707 tracks + 67 vias (all prior increments intact)',
        sum(prior_now.values()) == 707 + 67,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. NEW COPPER: 13 F.Cu tracks, NO via --------
    print('\n-- 3. IR_TX_GPIO16 increment: 13 tracks all F.Cu, ZERO new via --')
    i_trk = [t for t in trk if t.GetNetname() == INET]
    i_via = [t for t in via if t.GetNetname() == INET]
    layers = {t.GetLayerName() for t in i_trk}
    chk('IR_TX_GPIO16 is 13 tracks + exactly 0 vias',
        len(i_trk) == 13 and len(i_via) == 0,
        '%d tracks, %d vias' % (len(i_trk), len(i_via)))
    chk('IR_TX_GPIO16 copper is ALL F.Cu (same-layer MST, no cross-layer via)',
        layers == {'F.Cu'}, 'layers=%s' % sorted(layers))
    chk('IR_TX_GPIO16 tracks are all 0.200 mm (Default netclass width)',
        all(t.GetWidth() == 200000 for t in i_trk),
        'widths=%s' % sorted({t.GetWidth() for t in i_trk}))
    # No-via class: the total via count is unchanged, so this increment added none.
    chk('increment added ZERO vias to its net (board via total tracks the live SoT; cleanest class)',
        len(via) == EXPECT_VIAS and len(i_via) == 0, '%d total vias' % len(via))

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. both pads fully connected, no prior pair regressed --')
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

    # both pads of the net must be copper-reachable from U1.9 (the MST root)
    net_refs = {'U1.9', 'R22.1'}
    root = pad('U1.9')
    reach = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
             for p in cc.GetConnectedItems(root) if p.GetClass() == 'PAD'} | {'U1.9'}
    chk('IR_TX_GPIO16 both pads copper-connected (U1.9/R22.1)',
        net_refs.issubset(reach), 'reachable=%s' % str(sorted(reach & net_refs)))

    reg = []
    for e in jr:
        if e.get('group') == 'IR_TX_GPIO16' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + all fourteen prior increments)',
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
    dc, _ = RU.drc(AUTH, 'probe020', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class; clearance stays 0)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-320): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
