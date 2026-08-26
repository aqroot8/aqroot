# -*- coding: utf-8 -*-
"""FBV2-P2-002F section 17 -- compare the Phase B replay against Phase A.

Section 17 lists what has to match: connection count, nets, connectivity,
widths, vias, DRC, metrics and the absence of out-of-scope copper.  Anything
that differs MATERIALLY is a FAIL.

    python phaseB_compare.py phaseA.json phaseB.json         <A.kicad_pcb> <B.kicad_pcb>
"""
import os, sys, json, math, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import pcbnew

N = '/01_POWER_TREE/'
SCOPE = set("""BAT_CONNECTOR_P BAT_RAW BAT_MID BAT_SENSE BAT_PROTECTED_P
LTC_GATE LTC_GATE_RC LTC_OV LTC_UV LTC_SHDN LTC4368_FAULT_N BAT_PROT_SHDN_CTL
Q2_CS Q3_CS VBRIDGE_TOP VREF_TOP REF_HO REF_POL N_POL N_BATDIV VREC_VCC
REC_GATE_N REC_POL_OK REC_AND1 REC_AND2 REC_BAT_LOW REC_FAULT_B REC_LIM_IN
REC_DIODE_IN GND""".split())


def profile(pcb):
    b = pcbnew.LoadBoard(pcb)
    b.BuildConnectivity()
    per = collections.defaultdict(lambda: collections.defaultdict(float))
    vias = collections.Counter()
    oos = collections.Counter()
    for t in b.GetTracks():
        nm = t.GetNetname()
        short = nm[len(N):] if nm.startswith(N) else nm
        if short not in SCOPE:
            oos[nm] += 1
        if t.GetClass() == 'PCB_VIA':
            vias[short] += 1
            continue
        L = math.hypot(t.GetEnd().x - t.GetStart().x,
                       t.GetEnd().y - t.GetStart().y) / 1e6
        per[short][round(t.GetWidth() / 1e6, 2)] += L
    # connectivity: how many separate clusters each in-scope net is in
    cn = b.GetConnectivity()
    pads = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            nm = p.GetNetname()
            if nm.startswith(N) and nm[len(N):] in SCOPE and nm[len(N):] != 'GND':
                pads[nm[len(N):]].append(p)
    clusters = {}
    for short, ps in pads.items():
        seen, groups = set(), 0
        for p in ps:
            u = str(p.m_Uuid.AsString())
            if u in seen:
                continue
            groups += 1
            for i in cn.GetConnectedItems(p):
                seen.add(str(i.m_Uuid.AsString()))
        clusters[short] = groups
    return dict(
        tracks=len([t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']),
        vias=sum(vias.values()),
        nets=sorted(per),
        lengths={k: round(sum(v.values()), 3) for k, v in per.items()},
        widths={k: sorted(v) for k, v in per.items()},
        vias_by_net=dict(vias),
        clusters=clusters,
        out_of_scope=dict(oos))


def main():
    ja, jb = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
    pa, pb = profile(sys.argv[3]), profile(sys.argv[4])
    fails, rows = [], []

    def chk(name, a, b, tol=None):
        if tol is None:
            ok = (a == b)
        else:
            ok = abs(a - b) <= tol
        rows.append((name, a, b, ok))
        print('%-34s A=%-26s B=%-26s %s'
              % (name, str(a)[:26], str(b)[:26], 'PASS' if ok else '**FAIL**'))
        if not ok:
            fails.append(name)

    chk('Phase A/B result', ja.get('fail'), jb.get('fail'))
    chk('connections routed', ja['connections'], jb['connections'])
    chk('routed nets', len(pa['nets']), len(pb['nets']))
    chk('net names identical', pa['nets'], pb['nets'])
    chk('track items', pa['tracks'], pb['tracks'])
    chk('vias', pa['vias'], pb['vias'])
    chk('vias per net', pa['vias_by_net'], pb['vias_by_net'])
    chk('widths per net', pa['widths'], pb['widths'])
    chk('connectivity clusters', pa['clusters'], pb['clusters'])
    chk('out-of-scope copper', pa['out_of_scope'], pb['out_of_scope'])
    chk('ratsnest', ja['ratsnest'], jb['ratsnest'])
    chk('DRC', ja['drc'], jb['drc'])
    worst = 0.0
    for k in set(pa['lengths']) | set(pb['lengths']):
        d = abs(pa['lengths'].get(k, 0) - pb['lengths'].get(k, 0))
        worst = max(worst, d)
    chk('worst per-net length delta', 0.0, round(worst, 3), 0.001)
    print('=' * 118)
    print('PHASE B REPLAY: %s   (%d check%s failed)'
          % ('PASS' if not fails else 'FAIL', len(fails), '' if len(fails) == 1 else 's'))
    for f in fails:
        print('   FAILED: %s' % f)
    json.dump(dict(rows=[(a, str(b), str(c), d) for (a, b, c, d) in rows],
                   fails=fails, A=pa, B=pb),
              open(os.path.join(SP, 'phaseB_compare.json'), 'w'), indent=1)
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
