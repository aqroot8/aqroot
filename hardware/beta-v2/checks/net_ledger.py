# -*- coding: utf-8 -*-
"""FBV2-P2-002G section 5 -- CONNECTIVITY IS THE PRIMARY TRUTH.

A routed-connection count is a secondary metric.  FBV2-P2-002F reported 70 and
71 "connections" on boards where four pads were sitting in their own islands,
because the router's node fallback retargeted silently (PR-39).  Phase
completion is judged HERE instead: every in-scope net must be ONE connected
copper component, measured on a board that has been SAVED AND RELOADED.

    "<KICAD>/bin/python.exe" net_ledger.py <board.kicad_pcb> [out.json]
"""
import os, sys, json, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import pcbnew

N = '/01_POWER_TREE/'

# The battery / protection block's in-scope nets.  GND is excluded: it is the
# In1.Cu plane, not routed copper, and it is audited separately.
SCOPE = """BAT_CONNECTOR_P BAT_RAW BAT_MID BAT_SENSE BAT_PROTECTED_P
LTC_GATE LTC_GATE_RC LTC_OV LTC_UV LTC_SHDN LTC4368_FAULT_N BAT_PROT_SHDN_CTL
Q2_CS Q3_CS VBRIDGE_TOP VREF_TOP REF_HO REF_POL N_POL N_BATDIV VREC_VCC
REC_GATE_N REC_POL_OK REC_AND1 REC_AND2 REC_BAT_LOW REC_FAULT_B REC_LIM_IN
REC_DIODE_IN""".split()


def ledger(pcb, refill=False):
    """Per-net connectivity, from a freshly loaded board."""
    b = pcbnew.LoadBoard(os.path.abspath(pcb))
    if refill:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    cn = b.GetConnectivity()
    pads = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            nm = p.GetNetname()
            if nm.startswith(N) and nm[len(N):] in SCOPE:
                pads[nm[len(N):]].append((f.GetReference() + '.' + p.GetNumber(), p))

    out, ok, tot = {}, 0, 0
    for short in SCOPE:
        ps = pads.get(short, [])
        if len(ps) < 2:
            out[short] = dict(pads=len(ps), islands=len(ps), connected=True,
                              groups=[[r for r, _ in ps]], note='single pad')
            continue
        tot += 1
        seen, groups = set(), []
        for (ref, p) in ps:
            if ref in seen:
                continue
            grp = {str(i.m_Uuid.AsString()) for i in cn.GetConnectedItems(p)}
            members = sorted(r for (r, q) in ps
                             if str(q.m_Uuid.AsString()) in grp)
            for mm in members:
                seen.add(mm)
            groups.append(members)
        conn = (len(groups) == 1)
        if conn:
            ok += 1
        out[short] = dict(pads=len(ps), islands=len(groups), connected=conn,
                          groups=groups)

    tr = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vi = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    oos = collections.Counter()
    for t in b.GetTracks():
        nm = t.GetNetname()
        short = nm[len(N):] if nm.startswith(N) else nm
        if short not in SCOPE and short != 'GND':
            oos[nm] += 1
    return dict(pcb=os.path.abspath(pcb), nets=out,
                connected=ok, total=tot, tracks=len(tr), vias=len(vi),
                out_of_scope=dict(oos))


def main():
    args = [a for a in sys.argv[1:]]
    pcb = [a for a in args if a.endswith('.kicad_pcb')]
    if not pcb:
        print('usage: net_ledger.py <board.kicad_pcb> [out.json]')
        return 2
    r = ledger(pcb[0], refill='--refill' in args)
    for short in SCOPE:
        v = r['nets'][short]
        if v.get('note'):
            continue
        mark = 'OK ' if v['connected'] else '** '
        print('%s%-18s %2d pads  %d island%s%s'
              % (mark, short, v['pads'], v['islands'],
                 '' if v['islands'] == 1 else 's',
                 '' if v['connected'] else
                 '   ' + ' | '.join('{%s}' % ','.join(g) for g in v['groups'])))
    print('=' * 96)
    print('IN-SCOPE NETS FULLY CONNECTED: %d of %d   tracks %d  vias %d  '
          'out-of-scope nets %d'
          % (r['connected'], r['total'], r['tracks'], r['vias'],
             len(r['out_of_scope'])))
    out = [a for a in args if a.endswith('.json')]
    if out:
        json.dump(r, open(out[0], 'w'), indent=1)
    return 0 if r['connected'] == r['total'] else 1


if __name__ == '__main__':
    sys.exit(main())
