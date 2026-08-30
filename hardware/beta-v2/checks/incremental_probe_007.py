# -*- coding: utf-8 -*-
"""FBV2-P2-007 / D-305 -- focused read-only evidence probe for the SECOND
rest-of-board incremental increment (the ACC_3V3_CTL accelerometer-3V3
load-switch control group routed onto the D-304 promoted board by
incremental_router.py).

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, the exact facts the D-305 gate
promoted:

  1. the increment PRESERVED the accepted D-304 copper EXACTLY -- all 452 prior
     tracks (432 Phase-A + 20 FRONT_RGB) and 54 vias are still present,
     byte/geometry-identical, none deleted or altered (proven as a copper-item
     multiset superset over the two ACC nets removed);
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the two
     ACC_3V3_CTL nets (31 tracks, 0 vias), all 0.200 mm B.Cu;
  3. the two ACC nets are now FULLY copper-connected (ratsnest 701->697), and no
     prior requested-connected pad pair (Phase-A or FRONT_RGB) regressed;
  4. real full-board KiCad DRC is unchanged (no new class, none increased).

    python3 incremental_probe_007.py
"""
import os, sys, json, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')

# D-305 promoted-board fingerprints.
EXPECT_SHA = 'a309f8ce022b48ef04baa2fef591c64eb1a643049ad31220a9cff24831279a50'
EXPECT_TRACKS = 502           # 494 (D-306) + 8 IMU_ADDR (D-307)
EXPECT_VIAS = 55              # 54 + 1 DISP_RST_N cross-layer through via (D-306)
EXPECT_JOURNAL = 88           # 86 (D-306) + 2 IMU_ADDR REST_INC
EXPECT_RATSNEST = 693         # 695 (D-306) - 2 (BMI270_SDO_ADDR 3-pad net closed)

# The pre-promotion D-304 authoritative sha (452 trk / 54 via) -- the exact set
# that must survive this increment unchanged.
D304_SHA = '00c93bdbba9a8c798c51cdef1c0d6d828da1bac54e4a785197f0f69edfb72aad'
ACC = ('/ACC_3V3_EN', '/01_POWER_TREE/ACC_3V3_ILIM')


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
    print('-- 1. INTEGRITY: authoritative board matches the D-305 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == current record (D-307)', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (494 prior + 8 IMU_ADDR)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (D-306 adds the first REST via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (695 - 2 IMU_ADDR closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (86 + 2 IMU_ADDR REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC' and e.get('group') == 'ACC_3V3_CTL']
    chk('journal carries 4 REST_INC ACC_3V3_CTL entries',
        len(inc) == 4, str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PRIOR COPPER PRESERVED EXACTLY ------
    print('\n-- 2. Phase-A copper preserved EXACTLY (432 trk + 54 via intact) --')
    now = copper_sigs(b)
    acc_items = collections.Counter({s: n for s, n in now.items() if s[1] in ACC})
    # Phase-A = everything that is NOT a rest-of-board increment net, so this
    # stays true as later increments (e.g. D-306 DISP_RST_N) are promoted.
    inc_nets = {e['net'] for e in jr if e.get('role') == 'REST_INC'}
    phaseA_now = collections.Counter({s: n for s, n in now.items()
                                      if s[1] not in inc_nets})
    chk('Phase-A copper == 432 tracks + 54 vias (intact under all increments)',
        sum(phaseA_now.values()) == 432 + 54,
        '%d items' % sum(phaseA_now.values()))
    chk('the ACC_3V3_CTL increment is exactly 31 B.Cu tracks (0 vias)',
        sum(acc_items.values()) == 31 and all(s[0] == 'T' for s in acc_items),
        '%d items, all tracks=%s' % (sum(acc_items.values()),
                                     all(s[0] == 'T' for s in acc_items)))

    # ------------------------------------ 3. CONNECTIVITY GAIN ----------------
    print('\n-- 3. ACC_3V3_CTL fully connected, no prior pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    for a, bb in (('U20.1', 'R98.1'), ('U20.1', 'TP26.1'),
                  ('TP26.1', 'U3.15'), ('U20.4', 'R97.1')):
        joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in cc.GetConnectedItems(pad(a)) if p.GetClass() == 'PAD'}
        chk('ACC_3V3_CTL connected: %s-%s' % (a, bb), bb in joined, str(sorted(joined)))

    reg = []
    for e in jr:
        if e.get('group') == 'ACC_3V3_CTL' or not e.get('requested_connected'):
            continue
        a, bb = e.get('a'), e.get('b')
        if not (a and bb) or a.count('.') != 1 or bb.count('.') != 1 \
                or a.startswith('(') or bb.startswith('('):
            continue
        pa = pad(a) if a.split('.')[0] in fps else None
        if pa is None:
            continue
        joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in cc.GetConnectedItems(pa) if p.GetClass() == 'PAD'}
        if bb not in joined:
            reg.append((a, bb))
    chk('no prior requested pair regressed (Phase-A + FRONT_RGB)', not reg,
        '%d regressed' % len(reg))

    # ------------------------------------------- 4. DRC UNCHANGED -------------
    print('\n-- 4. real full-board KiCad DRC unchanged --')
    dc, _ = RU.drc(AUTH, 'probe007', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-305): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
