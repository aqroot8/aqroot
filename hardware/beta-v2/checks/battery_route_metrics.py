# -*- coding: utf-8 -*-
"""FBV2-P2-002E -- every number section 21 asks for, measured from real copper.

Usage:  battery_route_metrics.py <board.kicad_pcb>
"""
import os, sys, json, math, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import pcbnew

N = '/01_POWER_TREE/'
RSQ = 0.491                      # mOhm/square, 1 oz outer
R_VIA = 0.88                     # mOhm per 0.4 mm through via
SCOPE = set("""BAT_CONNECTOR_P BAT_RAW BAT_MID BAT_SENSE BAT_PROTECTED_P
LTC_GATE LTC_GATE_RC LTC_OV LTC_UV LTC_SHDN LTC4368_FAULT_N BAT_PROT_SHDN_CTL
Q2_CS Q3_CS VBRIDGE_TOP VREF_TOP REF_HO REF_POL N_POL N_BATDIV VREC_VCC
REC_GATE_N REC_POL_OK REC_AND1 REC_AND2 REC_BAT_LOW REC_FAULT_B REC_LIM_IN
REC_DIODE_IN GND""".split())


def seg_len(t):
    return math.hypot(t.GetEnd().x - t.GetStart().x,
                      t.GetEnd().y - t.GetStart().y) / 1e6


def load(pcb):
    b = pcbnew.LoadBoard(pcb)
    b.BuildConnectivity()
    return b


def pad_xy(b, ref):
    r, n = ref.split('.')
    for f in b.GetFootprints():
        if f.GetReference() == r:
            for p in f.Pads():
                if p.GetNumber() == n:
                    return (p.GetPosition().x, p.GetPosition().y,
                            b.GetLayerName(f.GetLayer()))
    return None


def net_tracks(b, short):
    return [t for t in b.GetTracks() if t.GetNetname() == N + short]


def net_summary(b, short):
    tr = [t for t in net_tracks(b, short) if t.GetClass() == 'PCB_TRACK']
    vi = [t for t in net_tracks(b, short) if t.GetClass() == 'PCB_VIA']
    byw = collections.defaultdict(float)
    lay = collections.Counter()
    for t in tr:
        byw[round(t.GetWidth() / 1e6, 3)] += seg_len(t)
        lay[b.GetLayerName(t.GetLayer())] += 1
    sq = sum(L / w for w, L in byw.items() if w)
    return dict(total_mm=round(sum(byw.values()), 3),
                by_width={('%.2f' % w): round(L, 3) for w, L in sorted(byw.items())},
                widths_mm=sorted(byw),
                squares=round(sq, 3),
                copper_mohm=round(sq * RSQ, 2),
                vias=len(vi), via_mohm=round(len(vi) * R_VIA, 2),
                layers=dict(lay), segments=len(tr))


# ---- shortest routed path between two pads, over the laid copper ----------
def graph(b, short):
    tr = [t for t in net_tracks(b, short)]
    adj = collections.defaultdict(list)
    for t in tr:
        if t.GetClass() == 'PCB_VIA':
            continue
        a = (t.GetStart().x, t.GetStart().y, t.GetLayer())
        c = (t.GetEnd().x, t.GetEnd().y, t.GetLayer())
        L = seg_len(t)
        adj[a].append((c, L, t))
        adj[c].append((a, L, t))
    for t in tr:
        if t.GetClass() != 'PCB_VIA':
            continue
        p = (t.GetPosition().x, t.GetPosition().y)
        ends = [k for k in adj if (k[0], k[1]) == p]
        for i in range(len(ends)):
            for j in range(i + 1, len(ends)):
                adj[ends[i]].append((ends[j], 0.0, t))
                adj[ends[j]].append((ends[i], 0.0, t))
    return adj


def nearest_node(adj, x, y):
    best = None
    for k in adj:
        d = math.hypot(k[0] - x, k[1] - y)
        if best is None or d < best[0]:
            best = (d, k)
    return best


def path_between(b, short, refa, refb):
    """Dijkstra over the routed centrelines: length, widths used, via count."""
    adj = graph(b, short)
    if not adj:
        return None
    pa, pb = pad_xy(b, refa), pad_xy(b, refb)
    if pa is None or pb is None:
        return None
    da, sa = nearest_node(adj, pa[0], pa[1])
    db, sb = nearest_node(adj, pb[0], pb[1])
    import heapq
    dist = {sa: 0.0}
    prev = {}
    q = [(0.0, sa)]
    while q:
        d, u = heapq.heappop(q)
        if d > dist.get(u, 1e18):
            continue
        if u == sb:
            break
        for (v, L, t) in adj[u]:
            nd = d + L
            if nd < dist.get(v, 1e18) - 1e-9:
                dist[v] = nd
                prev[v] = (u, t)
                heapq.heappush(q, (nd, v))
    if sb not in dist:
        return None
    widths, vias, mm, node = set(), 0, 0.0, sb
    while node != sa:
        u, t = prev[node]
        if t.GetClass() == 'PCB_VIA':
            vias += 1
        else:
            widths.add(round(t.GetWidth() / 1e6, 3))
            mm += seg_len(t)
        node = u
    return dict(mm=round(mm, 3), widths=sorted(widths), vias=vias,
                stub_a_mm=round(da / 1e6, 3), stub_b_mm=round(db / 1e6, 3))


def total_net_span(b, short):
    """Longest routed distance between any two pads of the net."""
    adj = graph(b, short)
    refs = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == N + short:
                refs.append(f.GetReference() + '.' + p.GetNumber())
    best = (0.0, None, None)
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            r = path_between(b, short, refs[i], refs[j])
            if r and r['mm'] > best[0]:
                best = (r['mm'], refs[i], refs[j])
    return dict(mm=round(best[0], 3), a=best[1], b=best[2], pads=len(refs))


def escape_profile(b, short, ref, cap_mm=1.20):
    """Walk outward from a pad along its own copper, reporting the width
    ladder and how much copper sits below `cap_mm`."""
    adj = graph(b, short)
    p = pad_xy(b, ref)
    if p is None or not adj:
        return None
    _, s = nearest_node(adj, p[0], p[1])
    seen, order, node, prevn = set(), [], s, None
    while True:
        seen.add(node)
        nxt = None
        for (v, L, t) in adj[node]:
            if v in seen or t.GetClass() == 'PCB_VIA':
                continue
            if nxt is None or t.GetWidth() < nxt[2].GetWidth():
                nxt = (v, L, t)
        if nxt is None:
            break
        order.append((round(nxt[2].GetWidth() / 1e6, 3), round(nxt[1], 3)))
        node = nxt[0]
        if nxt[2].GetWidth() / 1e6 >= cap_mm:
            break
    below = sum(L for w, L in order if w < cap_mm)
    narrow = sum(L for w, L in order if w <= 0.201)
    sq = sum(L / w for w, L in order if w)
    return dict(profile=order, narrowest_mm=min([w for w, _ in order] or [0]),
                narrow_len_mm=round(narrow, 3),
                below_cap_mm=round(below, 3), total_mm=round(sum(L for _, L in order), 3),
                mohm=round(sq * RSQ, 3),
                monotonic=all(order[i][0] <= order[i + 1][0] for i in range(len(order) - 1)))


def gnd_near(b, ref, layer_pref=None):
    """Straight-line distance from a pad to the nearest GND pad/via copper."""
    p = pad_xy(b, ref)
    if p is None:
        return None
    best = None
    for f in b.GetFootprints():
        for q in f.Pads():
            if q.GetNetname() != N + 'GND' and q.GetNetname() != 'GND':
                continue
            d = math.hypot(q.GetPosition().x - p[0], q.GetPosition().y - p[1]) / 1e6
            if best is None or d < best[0]:
                best = (d, f.GetReference() + '.' + q.GetNumber())
    return dict(mm=round(best[0], 3), to=best[1]) if best else None


def out_of_scope(b):
    bad = collections.Counter()
    for t in b.GetTracks():
        nm = t.GetNetname()
        short = nm[len(N):] if nm.startswith(N) else nm
        if short not in SCOPE:
            bad[nm] += 1
    return dict(bad)


def main(pcb):
    b = load(pcb)
    tr = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vi = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    routed = sorted({t.GetNetname() for t in b.GetTracks()})
    R = dict(tracks=len(tr), vias=len(vi), routed_nets=len(routed),
             routed_net_names=routed,
             ratsnest=b.GetConnectivity().GetUnconnectedCount(True),
             out_of_scope=out_of_scope(b))
    for s in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID', 'BAT_SENSE',
              'BAT_PROTECTED_P', 'LTC_GATE'):
        R[s] = net_summary(b, s)
    R['paths'] = {
        'BAT_CONNECTOR_P J4.1->F1.1': path_between(b, 'BAT_CONNECTOR_P', 'J4.1', 'F1.1'),
        'BAT_RAW F1.2->Q2.7': path_between(b, 'BAT_RAW', 'F1.2', 'Q2.7'),
        'BAT_MID Q2.5->Q3.7': path_between(b, 'BAT_MID', 'Q2.5', 'Q3.7'),
        'BAT_SENSE Q3.5->R75.1': path_between(b, 'BAT_SENSE', 'Q3.5', 'R75.1'),
        'BAT_SENSE kelvin R75.1->U18.9': path_between(b, 'BAT_SENSE', 'R75.1', 'U18.9'),
        'BAT_PROT kelvin R75.2->U18.8': path_between(b, 'BAT_PROTECTED_P', 'R75.2', 'U18.8'),
        'BAT_PROT trunk R75.2->U11.2': path_between(b, 'BAT_PROTECTED_P', 'R75.2', 'U11.2'),
        'BAT_RAW tap U18.1->R77.1': path_between(b, 'BAT_RAW', 'U18.1', 'R77.1'),
        'U14.2 branch': path_between(b, 'BAT_PROTECTED_P', 'U14.2', 'TP15.1'),
        'U14.3 branch': path_between(b, 'BAT_PROTECTED_P', 'U14.3', 'U14.2'),
        'TP17 stub': path_between(b, 'LTC_GATE', 'TP17.1', 'R76.1'),
        'TP17->U18.10': path_between(b, 'LTC_GATE', 'TP17.1', 'U18.10'),
        'LTC_GATE U18.10->Q2.2': path_between(b, 'LTC_GATE', 'U18.10', 'Q2.2'),
        'C59 BAT_RAW': path_between(b, 'BAT_RAW', 'C59.1', 'F1.2'),
        'C58 BAT_PROTECTED_P': path_between(b, 'BAT_PROTECTED_P', 'C58.1', 'D9.1'),
    }
    R['u11_escape'] = escape_profile(b, 'BAT_PROTECTED_P', 'U11.2')
    R['gnd'] = {'C58.2': gnd_near(b, 'C58.2'), 'C59.2': gnd_near(b, 'C59.2')}
    R['deadcell'] = {}
    for s in ('VBRIDGE_TOP', 'VREF_TOP', 'REF_HO', 'REF_POL', 'N_POL', 'N_BATDIV',
              'VREC_VCC', 'REC_GATE_N', 'REC_POL_OK', 'REC_AND1', 'REC_AND2',
              'REC_BAT_LOW', 'REC_FAULT_B', 'REC_LIM_IN', 'REC_DIODE_IN'):
        R['deadcell'][s] = dict(net_summary(b, s), span=total_net_span(b, s))
    R['spans'] = {s: total_net_span(b, s) for s in
                  ('LTC_OV', 'LTC_UV', 'LTC_SHDN', 'LTC4368_FAULT_N',
                   'LTC_GATE', 'LTC_GATE_RC', 'Q2_CS', 'Q3_CS')}
    print(json.dumps(R, indent=1))
    json.dump(R, open(os.path.join(SP, 'route_metrics.json'), 'w'), indent=1)


main(sys.argv[1])
