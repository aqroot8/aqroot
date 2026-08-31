# -*- coding: utf-8 -*-
"""FBV2-P2-033 / D-331 focused read-only probe for XGPIO2 In2 pilot."""
import os, sys, json, math, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import live_fingerprint as LFP
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')
NET = '/XGPIO2'

def main():
    fails = []
    def chk(label, ok, detail=''):
        print('  %s %s %s' % ('PASS' if ok else '**FAIL**', label, detail))
        if not ok: fails.append(label)
    b = pcbnew.LoadBoard(AUTH); b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    sha = hashlib.sha256(open(AUTH, 'rb').read()).hexdigest()
    chk('authoritative fingerprint pinned', sha == LFP.SHA and len(trk) == LFP.TRACKS
        and len(via) == LFP.VIAS and b.GetConnectivity().GetUnconnectedCount(True) == LFP.RATSNEST
        and len(jr) == LFP.JOURNAL_LEN, sha[:16])
    nt = [t for t in trk if t.GetNetname() == NET]
    nv = [v for v in via if v.GetNetname() == NET]
    layers = collections.Counter(t.GetLayerName() for t in nt)
    chk('XGPIO2 copper is 8 tracks: 2 F.Cu + 2 In2.Cu + 4 B.Cu',
        len(nt) == 8 and layers == {'F.Cu': 2, 'In2.Cu': 2, 'B.Cu': 4}, str(dict(layers)))
    chk('two ordinary 0.60/0.30 through vias', len(nv) == 2 and all(
        v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
        and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in nv))
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == NET]
    cc = b.GetConnectivity(); reach = set()
    if pads:
        reach = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                 for p in cc.GetConnectedItems(pads[0]) if p.GetClass() == 'PAD'}
    chk('R53.1 and U3.6 connected through the inner haul',
        len(pads) == 2 and {'R53.1', 'U3.6'} <= reach, str(reach))
    inc = [e for e in jr if e.get('group') == 'XGPIO2_INNER_PILOT']
    chk('one requested pilot edge journaled', len(inc) == 1 and inc[0].get('requested_connected'))
    dc, _ = RU.drc(AUTH, 'probe027', os.path.join(SP, 'w'))
    expected = {'solder_mask_bridge': 1, 'hole_clearance': 5,
                'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('full-board DRC unchanged', dict(dc) == expected, str(dict(dc)))
    print('\nINCREMENTAL PROBE (D-331): %s (%d checks failed)' %
          ('PASS' if not fails else 'FAIL', len(fails)))
    return 0 if not fails else 1

if __name__ == '__main__':
    sys.exit(main())
