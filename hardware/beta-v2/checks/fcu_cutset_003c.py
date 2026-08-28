# -*- coding: utf-8 -*-
"""FBV2-P2-003C / D-275 -- the WESTERN-CORRIDOR F.Cu VACATE study, BY PATH ROLE.

D-274 (FBV2-P2-003B) proved the bounded BAT_PROTECTED_P F.Cu via bridge fails at
the 1.20 mm floor for ONE reason: no >= 1.20 mm F.Cu corridor exists from R75.2's
entry-array site to the eastern node / D9 island, because three NAMED control /
low-current F.Cu crossings box the western margin -- the LTC_GATE vertical near
x = 5.75, the BAT_PROT_SHDN_CTL diagonal, and a BAT_RAW divider run near
y = 72.45, with LTC_GATE_RC and FAULT_N vias between them.  The D-274 ruling
named the next task: a BOUNDED CONTROL-NET VACATE ECO to open a >= 1.20 mm F.Cu
lane, then route the bridge.

This is the instrumentation that requirement 2/3/6 of the task asks for.  It
models a VACATE of an individual routed F.Cu BRANCH (a connected component of one
candidate net's F.Cu copper), NEVER a whole net and NEVER inner-layer / current-
carrying copper, and re-measures whether the bridge corridor opens.  It is the
analytic prefilter; the real offload + bridge run plus KiCad DRC/connectivity is
the proof.  It lays no copper and mutates no board.

Candidate universe (requirement 3): F.Cu branches of the LOW-CURRENT control nets
(LTC_GATE, LTC_GATE_RC, LTC_SHDN, LTC4368_FAULT_N, BAT_PROT_SHDN_CTL) and the
bounded microamp BAT_RAW divider bridges (megohm parts, D-270 precedent).  The
current-carrying trunk / rails and the BAT_PROTECTED_P destination copper are
REFUSED as candidates, loudly.

    python fcu_cutset_003c.py [board.kicad_pcb]
"""
import os, sys, math, time, json, itertools
from collections import deque
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import numpy as np
import qrouter as QR
import battery_route_plan as PL

N = PL.N
NET = N + 'BAT_PROTECTED_P'
CP, CTW = 200000, 300000            # pad clr 0.20, trunk track clr 0.30 (D-269)
DIA, DRILL = 800000, 400000         # 0.80/0.40 POWER-class through via
G = 50000
W_TRUNK, W_FLOOR = 1500000, 1200000

# --- path-role classification, identical shape to offload_probe_002x ----------
CONTROL_NETS = frozenset(N + n for n in (
    'LTC_OV', 'LTC_UV', 'LTC_SHDN', 'LTC4368_FAULT_N',
    'LTC_GATE', 'LTC_GATE_RC', 'BAT_PROT_SHDN_CTL'))
# The D-270 low-current BAT_RAW divider bridges/links -- megohm taps, microamp.
BATRAW_LOWI = frozenset((
    ('BAT_RAW', 'R80.1', 'Q2.7'),      # divider top -> battery node bridge
    ('BAT_RAW', 'D12.1', 'R77.1'),     # dead-cell diode -> divider bridge
    ('BAT_RAW', 'R79.1', 'R80.1'),     # divider link
    ('BAT_RAW', 'R77.1', 'R79.1'),     # divider link
    ('BAT_RAW', 'U18.1', 'R77.1'),     # LTC4368 VIN sense tap
))
# Never a candidate: the current-carrying trunk and the high-current rails.  The
# BAT_PROTECTED_P copper east of the margin is the bridge DESTINATION, not a cut.
CURRENT_NETS = frozenset(N + n for n in (
    'BAT_PROTECTED_P', 'BAT_SENSE', 'BAT_MID', 'BAT_CONNECTOR_P'))

# The corridor window: from R75.2 (x~2.8) to the node's west edge and a little
# beyond, spanning the full latitude band R75.2 can reach.  A branch whose F.Cu
# copper never enters it cannot be in the bridge corridor.
WIN_X0, WIN_X1 = 1.5e6, 42e6
WIN_Y0, WIN_Y1 = 58e6, 84e6


def sig(s):
    if not hasattr(s, 'x0'):
        return None
    return (int(s.x0), int(s.y0), int(s.x1), int(s.y1))


def in_window(x, y):
    return WIN_X0 <= x <= WIN_X1 and WIN_Y0 <= y <= WIN_Y1


def branch_role(net, ends):
    """net = full net name; ends = set of REF.PAD tags this component touches.
    Return ('candidate'|None, reason)."""
    if net in CURRENT_NETS:
        return None, 'current-carrying / destination copper stays put'
    if net in CONTROL_NETS:
        return 'candidate', 'low-current control signal'
    if net == N + 'BAT_RAW':
        # accept a BAT_RAW component only if it clearly belongs to a whitelisted
        # microamp divider bridge/link (by the pads it touches)
        refs = {e.rsplit('.', 1)[0] for e in ends}
        for (_, a, b) in BATRAW_LOWI:
            if a.split('.')[0] in refs or b.split('.')[0] in refs:
                return 'candidate', 'bounded low-current BAT_RAW divider (D-270)'
        return None, 'BAT_RAW current-carrying node/reservoir - not low current'
    return None, 'out of western-margin scope'


def components(qb):
    """Group F.Cu track SEGs of the candidate nets into connected components
    (individual routed BRANCHES).  Two SEGs join if they share an endpoint."""
    segs = [s for s in qb.shapes['F']
            if hasattr(s, 'x0') and s.net and
            (s.net in CONTROL_NETS or s.net == N + 'BAT_RAW')]
    # union-find over shared endpoints (25 um tol), per net
    def key(x, y):
        return (round(x / 25000), round(y / 25000))
    comps = []
    for net in {s.net for s in segs}:
        ns = [s for s in segs if s.net == net]
        parent = list(range(len(ns)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def uni(i, j):
            parent[find(i)] = find(j)
        ptmap = {}
        for i, s in enumerate(ns):
            for pt in (key(s.x0, s.y0), key(s.x1, s.y1)):
                if pt in ptmap:
                    uni(i, ptmap[pt])
                ptmap[pt] = i
        groups = {}
        for i, s in enumerate(ns):
            groups.setdefault(find(i), []).append(s)
        for gi, gsegs in groups.items():
            comps.append((net, gsegs))
    return comps


def nearest_pad_refs(qb, net, gsegs):
    """Which pads of this net do the component's endpoints sit on/near?"""
    refs = set()
    pads = [p for (nn, tag), p in qb.pads.items() if nn == net]
    for s in gsegs:
        for (x, y) in ((s.x0, s.y0), (s.x1, s.y1)):
            best, bd = None, 1e18
            for p in pads:
                d = math.hypot(p['x'] - x, p['y'] - y)
                if d < bd:
                    bd, best = d, p['ref']
            if best is not None and bd < 400000:   # within 0.40 mm of a pad
                refs.add(best)
    return refs


# ---- corridor measurement (flood + full-budget A*), from bridge_feasibility ---
def flood_east(qb, sx, sy, width):
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    x0, y0, x1, y1 = qb.ex0 - 1e6, 58e6, 64e6, 96e6
    ox2 = int(round((x0 - ox) / G)) * G + ox
    oy2 = int(round((y0 - oy) / G)) * G + oy
    blk = qb.grid('F', NET, width, CP, CTW, ox2, oy2, x1, y1, G)
    si = (int((sx - ox2) // G), int((sy - oy2) // G))
    ny, nx = blk.shape
    blk[si[1], si[0]] = False
    seen = np.zeros_like(blk, bool)
    dq = deque([si]); seen[si[1], si[0]] = True
    maxx = sx
    while dq:
        i, j = dq.popleft()
        maxx = max(maxx, ox2 + i * G)
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny and not seen[b, a] and not blk[b, a]:
                seen[b, a] = True; dq.append((a, b))
    return round(maxx / 1e6, 2)


def astar(qb, sx, sy, tx, ty, width):
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    x0 = max(min(sx, tx) - 9e6, qb.ex0 - 1e6)
    y0 = max(min(sy, ty) - 9e6, qb.ey0 - 1e6)
    x1 = min(max(sx, tx) + 9e6, qb.ex1 + 1e6)
    y1 = min(max(sy, ty) + 9e6, qb.ey1 + 1e6)
    ox2 = int(round((x0 - ox) / G)) * G + ox
    oy2 = int(round((y0 - oy) / G)) * G + oy
    t0 = time.time()
    blk = qb.grid('F', NET, width, CP, CTW, ox2, oy2, x1, y1, G)
    si = (int((sx - ox2) // G), int((sy - oy2) // G))
    ti = (int((tx - ox2) // G), int((ty - oy2) // G))
    ny, nx = blk.shape
    for ii, jj in (si, ti):
        if 0 <= ii < nx and 0 <= jj < ny:
            blk[jj, ii] = False
    p = qb.search(blk, si, ti)
    return ('PATH' if p else 'NO_PATH'), round(time.time() - t0, 2)


# landing targets on the DESTINATION island: the D9-stub-tied BPP F.Cu west end
# (closest, but its D9->node link is a single via -- flagged) and the node west.
TARGETS = [('BPP_Fcu_west_11.35_71.3', 11.35e6, 71.3e6),
           ('node_west_38.5_75', 38.5e6, 75.0e6)]


def reaches(qb, sx, sy, width):
    """Does a width-wide F.Cu corridor reach ANY landing target?  Returns
    (opened_bool, per-target dict)."""
    res = {}
    opened = False
    for lab, tx, ty in TARGETS:
        r, dt = astar(qb, sx, sy, tx, ty, width)
        res[lab] = [r, dt]
        if r == 'PATH':
            opened = True
    return opened, res


def cut(qb, master_F, sigs):
    qb.shapes['F'] = ([s for s in master_F if sig(s) not in sigs]
                      if sigs else master_F)
    qb._obs_cache = None


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        SP, 'w', 'c3repro003c', 'aqroot-Beta-v2.kicad_pcb')
    t0 = time.time()
    qb = QR.QBoard(board)
    qb.wide_nets = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                             'BAT_MID', 'BAT_SENSE',
                                             'BAT_PROTECTED_P'))
    master_F = list(qb.shapes['F'])
    r = qb.pads[(NET, 'R75.2')]
    sx, sy = r['x'], r['y']

    comps = components(qb)
    cinfo, refused = {}, {}
    for idx, (net, gsegs) in enumerate(comps):
        refs = nearest_pad_refs(qb, net, gsegs)
        verdict, why = branch_role(net, refs)
        sn = net.split('/')[-1]
        # a stable label: net + sorted pad refs it touches (the routed branch)
        lab = '%s {%s}' % (sn, ','.join(sorted(refs)) if refs else '?%d' % idx)
        sigs = {sig(s) for s in gsegs}
        mm = sum(math.hypot(s.x1 - s.x0, s.y1 - s.y0) for s in gsegs) / 1e6
        # only branches whose copper enters the corridor window matter
        inwin = any(in_window((s.x0 + s.x1) / 2.0, (s.y0 + s.y1) / 2.0)
                    for s in gsegs)
        rec = dict(net=net, sigs=sigs, mm=round(mm, 3), n=len(sigs),
                   refs=sorted(refs), inwin=inwin)
        if verdict == 'candidate' and inwin:
            cinfo[lab] = rec
        else:
            refused[lab] = (why if verdict is None else 'outside corridor window')

    keys = sorted(cinfo)
    print('F.Cu VACATE STUDY 003C -- board %s' % os.path.relpath(board, SP))
    print('candidate F.Cu control/low-current branches in the corridor (%d):'
          % len(keys))
    for k in keys:
        print('  %-40s %2d seg  %7.3f mm' % (k, cinfo[k]['n'], cinfo[k]['mm']))
    if refused:
        print('refused / out of window (%d):' % len(refused))
        for k in sorted(refused):
            print('  %-40s %s' % (k, refused[k]))

    def cut_of(combo):
        s = set()
        for k in combo:
            s |= cinfo[k]['sigs']
        return s

    def opens(combo, width):
        cut(qb, master_F, cut_of(combo))
        o, res = reaches(qb, sx, sy, width)
        cut(qb, master_F, set())
        return o, res

    # baseline + flood diagnostic
    cut(qb, master_F, set())
    base_flood = {w: flood_east(qb, sx, sy, wv)
                  for w, wv in (('1.50', W_TRUNK), ('1.20', W_FLOOR))}
    base15, base15r = reaches(qb, sx, sy, W_TRUNK)
    base12, base12r = reaches(qb, sx, sy, W_FLOOR)
    print('BASELINE flood east (mm): 1.50 -> %s   1.20 -> %s'
          % (base_flood['1.50'], base_flood['1.20']))
    print('BASELINE reaches island: 1.50 -> %s   1.20 -> %s' % (base15, base12))
    sys.stdout.flush()

    # STEP 1 -- does vacating EVERY candidate open the corridor at all?
    allok15, all15r = opens(keys, W_TRUNK)
    allok12, all12r = opens(keys, W_FLOOR)
    cut(qb, master_F, cut_of(keys))
    all_flood = {w: flood_east(qb, sx, sy, wv)
                 for w, wv in (('1.50', W_TRUNK), ('1.20', W_FLOOR))}
    cut(qb, master_F, set())
    print('ALL %d vacated  flood east: 1.50 -> %s  1.20 -> %s'
          % (len(keys), all_flood['1.50'], all_flood['1.20']))
    print('ALL %d vacated  reaches island: 1.50 -> %s  1.20 -> %s'
          % (len(keys), allok15, allok12))
    print('   1.50 targets %s' % all15r)
    print('   1.20 targets %s' % all12r)
    sys.stdout.flush()

    out = dict(task='FBV2-P2-003C', board=os.path.relpath(board, SP),
               entry_mm=[round(sx / 1e6, 3), round(sy / 1e6, 3)],
               candidates={k: dict(mm=cinfo[k]['mm'], n=cinfo[k]['n'],
                                   refs=cinfo[k]['refs']) for k in keys},
               refused=refused,
               baseline=dict(flood=base_flood, reach_1_50=base15,
                             reach_1_20=base12, r15=base15r, r12=base12r),
               all_vacated=dict(flood=all_flood, reach_1_50=allok15,
                                reach_1_20=allok12, r15=all15r, r12=all12r))

    if not allok15 and not allok12:
        out['min_card'] = None
        out['finding'] = ('vacating ALL candidate F.Cu control/low-current '
                          'branches does NOT open a >=1.20 mm F.Cu corridor '
                          'to the island -- the F.Cu blocker is not the named '
                          'control copper alone')
        print('\nRESULT: no vacate set opens >= 1.20 mm.  ' + out['finding'])
        json.dump(out, open(os.path.join(SP, 'place_002z',
                                          'fcu_cutset_003c.json'), 'w'), indent=1)
        return 0

    target = W_TRUNK if allok15 else W_FLOOR
    tname = '1.50' if allok15 else '1.20'

    # STEP 2 -- greedy reduction to an irreducible minimal vacate set
    keep = list(keys)
    for k in sorted(keys, key=lambda k: -cinfo[k]['mm']):
        trial = [x for x in keep if x != k]
        if trial and opens(trial, target)[0]:
            keep = trial
    kcard = len(keep)
    m15 = opens(keep, W_TRUNK)
    m12 = opens(keep, W_FLOOR)
    print('\nGREEDY MINIMAL vacate set (%d): %s' % (kcard, keep))
    print('   opens 1.50 -> %s   1.20 -> %s' % (m15[0], m12[0]))

    # STEP 3 -- prove minimum cardinality: exhaust all smaller sets
    proven, checked, smaller = True, 0, None
    for card in range(1, kcard):
        hit = None
        n = 0
        tc = time.time()
        for combo in itertools.combinations(keys, card):
            n += 1
            if opens(combo, target)[0]:
                hit = list(combo)
                break
        checked = card
        print('  exhaustive cardinality %d: %d sets, %s (%.0fs)'
              % (card, n, 'a smaller set OPENS' if hit else 'none opens',
                 time.time() - tc))
        if hit:
            smaller, proven = hit, False
            break

    print('\nMINIMUM VACATE SET (target %s mm), cardinality %d:' % (tname, kcard))
    for k in keep:
        print('    %-40s %2d seg  %7.3f mm' % (k, cinfo[k]['n'], cinfo[k]['mm']))
    if smaller:
        print('  NOT minimum: a %d-set opens too: %s' % (len(smaller), smaller))
    elif proven:
        print('  PROVEN MINIMUM: no set of cardinality < %d opens %s mm'
              % (kcard, tname))

    out.update(dict(target=tname, minimal_set=keep, minimal_card=kcard,
                    minimal_open_1_50=m15[0], minimal_open_1_20=m12[0],
                    minimal_r15=m15[1], minimal_r12=m12[1],
                    proven_minimum=proven, checked_upto=checked,
                    smaller_hit=smaller, secs=round(time.time() - t0, 1)))
    json.dump(out, open(os.path.join(SP, 'place_002z',
                                     'fcu_cutset_003c.json'), 'w'), indent=1)
    print('\nwrote place_002z/fcu_cutset_003c.json  (%.1fs)'
          % (time.time() - t0))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
