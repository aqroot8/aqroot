# -*- coding: utf-8 -*-
"""B-34 recomputed from ACTUAL routed copper (FBV2-P2-002C section 23)."""
import os, sys, json, math, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import pcbnew

RSQ = 0.491          # mOhm per square, 1 oz (35 um) outer copper
RSQ_IN = 0.982       # 0.5 oz inner
R_VIA = 0.88         # mOhm, 0.4 mm drill through 1.6 mm, 25 um plating
N = '/01_POWER_TREE/'
CHAIN = ['BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID', 'BAT_SENSE', 'BAT_PROTECTED_P']
# the pack-current path only; taps and sense branches carry no load current
TRUNK_ONLY = True


def main(pcb):
    b = pcbnew.LoadBoard(pcb)
    per = collections.defaultdict(lambda: collections.defaultdict(float))
    vias = collections.Counter()
    layers = collections.defaultdict(set)
    for t in b.GetTracks():
        n = t.GetNetname()
        if not n.startswith(N):
            continue
        short = n[len(N):]
        if t.GetClass() == 'PCB_VIA':
            vias[short] += 1
            continue
        L = math.hypot(t.GetEnd().x - t.GetStart().x,
                       t.GetEnd().y - t.GetStart().y) / 1e6
        w = t.GetWidth() / 1e6
        per[short][round(w, 3)] += L
        layers[short].add(b.GetLayerName(t.GetLayer()))
    out = {}
    for short in sorted(per):
        rows = sorted(per[short].items())
        sq = sum(L / w for w, L in rows)
        out[short] = dict(
            total_mm=round(sum(L for _, L in rows), 3),
            by_width={('%.2f' % w): round(L, 3) for w, L in rows},
            squares=round(sq, 3), copper_mohm=round(sq * RSQ, 2),
            vias=vias[short], via_mohm=round(vias[short] * R_VIA, 2),
            layers=sorted(layers[short]))
    print(json.dumps(out, indent=1))
    json.dump(out, open(os.path.join(SP, 'b34.json'), 'w'), indent=1)
    return out


if __name__ == '__main__':
    main(sys.argv[1])
