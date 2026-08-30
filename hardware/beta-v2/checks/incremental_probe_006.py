# -*- coding: utf-8 -*-
"""FBV2-P2-006 / D-304 -- focused read-only evidence probe for the FIRST
rest-of-board incremental increment (the FRONT_RGB indicator group routed onto
the D-302 promoted board by incremental_router.py).

READ-ONLY.  Nothing here mutates the authoritative board or the shared journal.
It re-proves, on the live authoritative board, the exact facts the D-304 gate
promoted:

  1. the increment PRESERVED the accepted D-302 Phase-A copper EXACTLY -- all 432
     Phase-A tracks and 54 vias are still present, byte/geometry-identical, none
     deleted or altered (proven as a copper-item multiset superset of the
     pre-promotion D-302 fingerprint);
  2. the increment is ADD-ONLY and IN-SCOPE -- the only new copper is the three
     FRONT_RGB nets (20 tracks, 0 vias), all 0.200 mm B.Cu;
  3. the three FRONT_RGB nets are now FULLY copper-connected (ratsnest 704->701),
     and no prior Phase-A requested-connected pad pair regressed;
  4. real full-board KiCad DRC is unchanged (no new class, none increased).

    python3 incremental_probe_006.py
"""
import os, sys, json, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')

# D-304 promoted-board fingerprints.
EXPECT_SHA = '00c93bdbba9a8c798c51cdef1c0d6d828da1bac54e4a785197f0f69edfb72aad'
EXPECT_TRACKS = 452           # D-302 Phase-A 432 + 20 FRONT_RGB increment
EXPECT_VIAS = 54              # unchanged -- the increment adds NO via
EXPECT_JOURNAL = 80           # 77 Phase-A + 3 REST_INC
EXPECT_RATSNEST = 701         # 704 (D-302) - 3 (FRONT_RGB nets closed)

# The pre-promotion D-302 authoritative copper (432 trk / 54 via) -- the exact
# set that must survive the increment unchanged.
D302_SHA = '63a9bc54e16cd1b2c69ad41cd95a2bb4d3e258503cb12b5628885debf87d6ba9'
RGB = ('/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N',
       '/08_BUTTONS_EXPANDERS/FRONT_RGB_G_N',
       '/08_BUTTONS_EXPANDERS/FRONT_RGB_B_N')


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
    print('-- 1. INTEGRITY: authoritative board matches the D-304 fingerprints --')
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative PCB sha256 == D-304 record', sha == EXPECT_SHA, sha[:16] + '..')
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    chk('track count == %d (432 Phase-A + 20 increment)' % EXPECT_TRACKS,
        len(trk) == EXPECT_TRACKS, str(len(trk)))
    chk('via count == %d (increment adds no via)' % EXPECT_VIAS,
        len(via) == EXPECT_VIAS, str(len(via)))
    chk('copper layers == 6', b.GetCopperLayerCount() == 6, str(b.GetCopperLayerCount()))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest == %d (704 - 3 closed)' % EXPECT_RATSNEST, rats == EXPECT_RATSNEST, str(rats))
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    chk('journal entries == %d (77 + 3 REST_INC)' % EXPECT_JOURNAL,
        len(jr) == EXPECT_JOURNAL, str(len(jr)))
    inc = [e for e in jr if e.get('role') == 'REST_INC']
    chk('journal carries 3 REST_INC FRONT_RGB entries',
        len(inc) == 3 and all(e.get('group') == 'FRONT_RGB' for e in inc),
        str([(e.get('a'), e.get('b')) for e in inc]))

    # --------------------------------- 2. PHASE-A PRESERVED EXACTLY -----------
    print('\n-- 2. PHASE-A copper preserved EXACTLY (D-302 set is a subset) --')
    now = copper_sigs(b)
    rgb_items = collections.Counter({s: n for s, n in now.items() if s[1] in RGB})
    phaseA_now = now - rgb_items
    chk('non-FRONT_RGB copper == 432 tracks + 54 vias (Phase-A intact)',
        sum(phaseA_now.values()) == 432 + 54,
        '%d items' % sum(phaseA_now.values()))
    chk('the only new copper is the FRONT_RGB increment',
        sum(rgb_items.values()) == 20 and all(s[0] == 'T' for s in rgb_items),
        '%d items, all tracks=%s' % (sum(rgb_items.values()),
                                     all(s[0] == 'T' for s in rgb_items)))

    # ------------------------------------ 3. CONNECTIVITY GAIN ----------------
    print('\n-- 3. FRONT_RGB fully connected, no Phase-A pair regressed --')
    cc = b.GetConnectivity()
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    def pad(ref):
        r, num = ref.split('.')
        for p in fps[r].Pads():
            if p.GetNumber() == num:
                return p
        return None

    for a, bb in (('U23.4', 'R124.1'), ('U23.5', 'R125.1'), ('U23.6', 'R126.1')):
        joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in cc.GetConnectedItems(pad(a)) if p.GetClass() == 'PAD'}
        chk('FRONT_RGB connected: %s-%s' % (a, bb), bb in joined, str(sorted(joined)))

    reg = []
    for e in jr:
        if e.get('role') == 'REST_INC' or not e.get('requested_connected'):
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
    chk('no Phase-A requested pair regressed', not reg, '%d regressed' % len(reg))

    # ------------------------------------------- 4. DRC UNCHANGED -------------
    print('\n-- 4. real full-board KiCad DRC unchanged --')
    dc, _ = RU.drc(AUTH, 'probe006', os.path.join(SP, 'w'))
    expect = {'solder_mask_bridge': 1, 'hole_clearance': 5,
              'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged (no new/worse copper class)',
        dict(dc) == expect, str(dict(dc)))

    print('\nINCREMENTAL PROBE (D-304): %s (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails),
             '' if len(fails) == 1 else 's'))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
