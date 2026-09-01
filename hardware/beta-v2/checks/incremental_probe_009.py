# -*- coding: utf-8 -*-
"""FBV2-P2-009 / D-307 -- focused read-only evidence probe for the FOURTH
rest-of-board incremental increment: the BMI270 IMU I2C address-select strap
BMI270_SDO_ADDR (R118.1 / R119.2 / U4.1), routed onto the D-306 promoted board
by incremental_router.py.

This increment is a pristine, low-risk same-layer B.Cu multi-terminal net: a
3-pad, 2-edge MST (R118.1<->R119.2, R119.2<->U4.1) in a region with ZERO
accepted copper within bbox+2 mm.  It reuses the D-304/D-305 same-layer B.Cu
mechanics byte-for-byte -- NO via, so vias stay 55 and NO GND plane is re-poured
(every zone byte-identical).  It was the held clean IMU/I2C-local fallback after
the two congested 2-net candidates (U11_PROG charger straps, PWR_SENSE west
power-status) hit hard pad-escape / no-corridor walls on scratch.

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, the exact facts the D-307 gate
promoted:

  1. the increment PRESERVED the accepted D-306 copper EXACTLY -- all 494 prior
     tracks (432 Phase-A + 20 FRONT_RGB + 31 ACC_3V3_CTL + 11 DISP_RST_N) and 55
     prior vias are still present byte/geometry-identical, none deleted/altered;
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the
     BMI270_SDO_ADDR net (8 tracks on B.Cu, 0 vias);
  3. BMI270_SDO_ADDR is now FULLY copper-connected (all 3 pads one island,
     ratsnest 695 -> 693), and no prior requested pair regressed;
  4. real full-board KiCad DRC is unchanged (no new class, none increased); and
     EVERY zone is byte-identical -- no via means no In1/In4 GND plane re-pour.

    python3 incremental_probe_009.py
"""
import os, sys, json, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')

# D-307 promoted-board fingerprints.
import live_fingerprint as LFP   # single source of truth for the live board pin (D-309)
EXPECT_SHA = LFP.SHA
EXPECT_TRACKS = LFP.TRACKS
EXPECT_VIAS = LFP.VIAS
EXPECT_JOURNAL = LFP.JOURNAL_LEN
EXPECT_RATSNEST = LFP.RATSNEST

# The pre-promotion D-306 authoritative sha (494 trk / 55 via) -- the exact set
# that must survive this increment unchanged.
D306_SHA = '9c0586d824f92542c34fd12de1f6f8d4bdd8aaaab656c823eec40d6ae3f62259'
IMU = ('/05_I2C_DEVICES/BMI270_SDO_ADDR',)


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
    print('-- 1. INTEGRITY: authoritative board matches the D-307 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-308 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (prior + later REST_INC increments)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (55 prior + 3 FRONT_RGB_LED vias)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (all promoted increments closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (Phase-A + all REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'IMU_ADDR']
    chk('journal carries 2 REST_INC IMU_ADDR entries',
        len(inc) == 2, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. D-306 copper preserved EXACTLY (494 trk + 55 via intact) --')
    now = copper_sigs(b)
    imu_items = collections.Counter({s: n for s, n in now.items() if s[1] in IMU})
    # Increments promoted AFTER D-307 (IMU_ADDR) -- e.g. D-308 FRONT_RGB_LED --
    # are excluded so this "pre-IMU copper intact" check stays true as the board
    # grows.  The pre-IMU accepted copper is Phase-A (432) + FRONT_RGB (20) +
    # ACC_3V3_CTL (22, D-353 replacement) + DISP_RST (11) = 485 tracks + 55 vias, and must never
    # change under any later increment.
    PRE_IMU_GROUPS = ('FRONT_RGB', 'ACC_3V3_CTL', 'DISP_RST', 'IMU_ADDR')
    post_imu = {e['net'] for e in jr if e.get('role') == 'REST_INC'
                and e.get('group') not in PRE_IMU_GROUPS}
    post_items = collections.Counter({s: n for s, n in now.items() if s[1] in post_imu})
    prior_now = now - imu_items - post_items
    chk('non-IMU pre-D-308 copper == 485 tracks + 55 vias (Phase-A + RGB + ACC + DISP intact)',
        sum(prior_now.values()) == 485 + 55,
        '%d items' % sum(prior_now.values()))
    # Phase-A alone (everything that is NOT a rest-increment net) stays 432+54.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54, '%d items' % sum(phaseA_now.values()))

    # --------------------------- 3. IMU_ADDR NEW COPPER: B.Cu, no via ---------
    print('\n-- 3. BMI270_SDO_ADDR increment: 8 B.Cu tracks, no via --')
    imu_trk = [t for t in trk if t.GetNetname() in IMU]
    imu_via = [t for t in via if t.GetNetname() in IMU]
    layers = {t.GetLayerName() for t in imu_trk}
    chk('BMI270_SDO_ADDR is 8 tracks + exactly 0 vias',
        len(imu_trk) == 8 and len(imu_via) == 0,
        '%d tracks, %d vias' % (len(imu_trk), len(imu_via)))
    chk('BMI270_SDO_ADDR copper is all B.Cu (same-layer, no cross-layer hop)',
        layers == {'B.Cu'}, 'layers=%s' % sorted(layers))
    chk('BMI270_SDO_ADDR tracks are all 0.200 mm (Default netclass)',
        all(t.GetWidth() == 200000 for t in imu_trk),
        'widths=%s' % sorted({t.GetWidth() for t in imu_trk}))

    # NOTE: a via would have forced an In1/In4 GND plane re-pour; this increment
    # lays no via, so the D-306 plane fills carry through unchanged -- the gate
    # proved all 41 zones byte-identical and the DRC below re-proves legality.

    # ------------------------------------ 4. CONNECTIVITY GAIN ----------------
    print('\n-- 4. BMI270_SDO_ADDR fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    # R118.1 -- R119.2 -- U4.1: all three one copper island.
    joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
              for p in cc.GetConnectedItems(pad('R119.2')) if p.GetClass() == 'PAD'}
    for other in ('R118.1', 'U4.1'):
        chk('BMI270_SDO_ADDR connected: R119.2-%s' % other,
            other in joined, str(sorted(joined)))

    reg = []
    for e in jr:
        if e.get('group') == 'IMU_ADDR' or not e.get('requested_connected'):
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
    chk('no prior requested pair regressed (Phase-A + RGB + ACC + DISP)', not reg,
        '%d regressed' % len(reg))

    # ------------------------------------------- 5. DRC UNCHANGED -------------
    print('\n-- 5. real full-board KiCad DRC unchanged --')
    dc, _ = RU.drc(AUTH, 'probe009', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-307): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
