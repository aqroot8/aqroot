# -*- coding: utf-8 -*-
"""FBV2-P2-041 / D-339 focused read-only probe for DISP_DC J1 fanout reuse."""
import os, sys, json, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import live_fingerprint as LFP
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')
NET = '/DISP_DC'

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
    chk('DISP_DC copper is 4 tracks: 2 F.Cu + 2 In2.Cu',
        len(nt) == 4 and layers == {'F.Cu': 2, 'In2.Cu': 2}, str(dict(layers)))
    chk('two ordinary 0.60/0.30 through vias', len(nv) == 2 and all(
        v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
        and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in nv))
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == NET]
    reach = set()
    if pads:
        reach = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                 for p in b.GetConnectivity().GetConnectedItems(pads[0]) if p.GetClass() == 'PAD'}
    chk('U1.22 and J1.37 connected through the inner fanout',
        len(pads) == 2 and {'U1.22', 'J1.37'} <= reach, str(reach))
    inc = [e for e in jr if e.get('group') == 'DISP_DC']
    chk('one requested fanout edge journaled', len(inc) == 1 and inc[0].get('requested_connected'))
    dc, _ = RU.drc(AUTH, 'probe028', os.path.join(SP, 'w'))
    expected = {'solder_mask_bridge': 1, 'hole_clearance': 5,
                'lib_footprint_issues': 199, 'unconnected_items': 499}
    chk('full-board DRC unchanged', dict(dc) == expected, str(dict(dc)))
    print('\nINCREMENTAL PROBE (D-339): %s (%d checks failed)' %
          ('PASS' if not fails else 'FAIL', len(fails)))
    return 0 if not fails else 1

if __name__ == '__main__':
    sys.exit(main())
