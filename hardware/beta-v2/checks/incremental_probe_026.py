# -*- coding: utf-8 -*-
"""FBV2-P2-030 / D-328 focused read-only probe for BTN_RIGHT_N."""
import os, sys, json, math, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import live_fingerprint as LFP
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')
NET = '/08_BUTTONS_EXPANDERS/BTN_RIGHT_N'


def main():
    fails = []
    def chk(label, ok, detail=''):
        print('  %s %s %s' % ('PASS' if ok else '**FAIL**', label, detail))
        if not ok:
            fails.append(label)

    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    jr = json.load(open(JOURNAL, encoding='utf-8'))

    print('-- 1. authoritative D-328 fingerprint --')
    chk('sha256 pinned', sha == LFP.SHA, sha[:16])
    chk('tracks/vias pinned', len(tracks) == LFP.TRACKS and len(vias) == LFP.VIAS,
        '%d/%d' % (len(tracks), len(vias)))
    chk('layers/zones pinned', b.GetCopperLayerCount() == 6 and len(list(b.Zones())) == 41,
        '%d/%d' % (b.GetCopperLayerCount(), len(list(b.Zones()))))
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    chk('ratsnest pinned', rats == LFP.RATSNEST, str(rats))
    chk('journal pinned', len(jr) == LFP.JOURNAL_LEN, str(len(jr)))
    inc = [e for e in jr if e.get('group') == 'BTN_RIGHT_N']
    chk('three requested BTN_RIGHT_N edges journaled', len(inc) == 3,
        str([(e.get('a'), e.get('b'), e.get('layer')) for e in inc]))

    print('\n-- 2. bounded add-only copper --')
    nt = [t for t in tracks if t.GetNetname() == NET]
    nv = [v for v in vias if v.GetNetname() == NET]
    layers = collections.Counter(t.GetLayerName() for t in nt)
    chk('16 tracks: 12 F.Cu + 4 B.Cu', len(nt) == 16 and layers == {'F.Cu': 12, 'B.Cu': 4},
        str(dict(layers)))
    chk('all tracks are Default 0.200 mm', all(t.GetWidth() == 200000 for t in nt))
    chk('two ordinary 0.60/0.30 through vias', len(nv) == 2 and all(
        v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
        and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in nv),
        str([(v.GetPosition().x / 1e6, v.GetPosition().y / 1e6) for v in nv]))
    other = [v for v in vias if v.GetNetname() != NET]
    gap = min(math.hypot(v.GetPosition().x - o.GetPosition().x,
                         v.GetPosition().y - o.GetPosition().y)
              for v in nv for o in other)
    chk('both vias >=0.80 mm centre from every prior barrel', gap >= 800000,
        '%.3f mm' % (gap / 1e6))

    print('\n-- 3. all four physical pads connected; prior pairs preserved --')
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == NET]
    hub = next(p for p in pads if p.GetParentFootprint().GetReference() == 'R7')
    cc = b.GetConnectivity()
    reach = {(p.GetParentFootprint().GetReference() + '.' + p.GetNumber(),
              p.GetPosition().x, p.GetPosition().y)
             for p in cc.GetConnectedItems(hub) if p.GetClass() == 'PAD'}
    sw = [p for p in pads if p.GetParentFootprint().GetReference() == 'SW5'
          and p.GetNumber() == '1']
    connected = (len(pads) == 4 and len(sw) == 2
                 and all(('SW5.1', p.GetPosition().x, p.GetPosition().y) in reach for p in sw)
                 and any(x[0] == 'U2.16' for x in reach))
    chk('R7.2, U2.16 and BOTH SW5.1 lands form one cluster', connected,
        'pads=%d sw_lands=%d' % (len(pads), len(sw)))

    fps = {f.GetReference(): f for f in b.GetFootprints()}
    def pad(ref):
        r, num = ref.split('.')
        return next((p for p in fps[r].Pads() if p.GetNumber() == num), None)
    reg = []
    for e in jr:
        if e.get('group') == 'BTN_RIGHT_N' or not e.get('requested_connected'):
            continue
        a, z = e.get('a'), e.get('b')
        if not a or not z or a.count('.') != 1 or z.count('.') != 1 \
                or a.startswith('(') or z.startswith('('):
            continue
        pa = pad(a)
        if pa is None:
            continue
        joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in cc.GetConnectedItems(pa) if p.GetClass() == 'PAD'}
        if z not in joined:
            reg.append((a, z))
    chk('no prior requested pair regressed', not reg, str(reg[:5]))

    print('\n-- 4. real full-board DRC unchanged --')
    dc, _ = RU.drc(AUTH, 'probe026', os.path.join(SP, 'w'))
    expected = {'solder_mask_bridge': 1, 'hole_clearance': 5,
                'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('DRC histogram unchanged; clearance remains zero', dict(dc) == expected, str(dict(dc)))
    print('\nINCREMENTAL PROBE (D-328): %s (%d checks failed)'
          % ('PASS' if not fails else 'FAIL', len(fails)))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
