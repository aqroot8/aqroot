# -*- coding: utf-8 -*-
"""FBV2-P2-002F section 6 / PR-27 -- the dead-cell and recovery cluster.

FBV2-P2-002E left five parts of this cluster stranded in the NORTH of the board
while the comparator, its divider chain and its logic sit in the SOUTH:

    REC_DIODE_IN   64.0 mm    D12 at y 72.7, R95 at y 9.8
    N_BATDIV       52.1 mm    C61 at y 66.5, the divider at y 19..21
    VREF_TOP       48.6 mm    D11 at y 72.7, R87 at y 25.0
    VREC_VCC       47.2 mm    C60 at y 70.2, U19 at y 29.2
    VBRIDGE_TOP    23.5 mm    D10 at y 6.3,  R85 at y 28.7

Every one of those is a megohm-impedance node on a 2.2 M ratiometric bridge.
Nothing here changes a value, a device or a connection: the parts are moved to
the cluster they belong to, and D10/D11 stay two distinct two-terminal
Schottkys (section 6, and D-xxx's ratiometric pair is not reinterpreted).

Objective: per-net minimum spanning tree over the net's own pads, capped at
15 mm (target) and 20 mm (absolute).  Coordinate descent over a 0.5 mm slot
grid; nothing is hand-placed.
"""
import os, sys, math, json, time, faulthandler
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import place_search_002f as PS
import path_role_util as RU
import pcbnew

N = PS.N
NETS = ['VBRIDGE_TOP', 'VREF_TOP', 'REF_HO', 'REF_POL', 'N_POL', 'N_BATDIV',
        'VREC_VCC', 'REC_GATE_N', 'REC_POL_OK', 'REC_AND1', 'REC_AND2',
        'REC_BAT_LOW', 'REC_FAULT_B', 'REC_LIM_IN', 'REC_DIODE_IN']
MOVE = ['D10', 'D11', 'D12', 'C60', 'C61', 'R84', 'TP22']
# MINIMAL, AND THAT IS A CORRECTION.
#
# The first version of this optimiser moved twenty-two parts - the comparator
# U19 and the whole 2.2 M chain with it - and reached a worst node of 14.25 mm,
# inside section 6's 15 mm TARGET. It also made the cluster UNROUTABLE: on the
# Phase A run that followed, `REF_HO` could not reach `U19.5` from either
# `R91.2` or `R93.2`, and `VREF_TOP` took 33.3 mm of copper to cross 9.0 mm of
# air. Compacting a cluster shortens its spans and removes its channels at the
# same time, and MST span cannot see the second half of that.
#
# So the move is now confined to THE PARTS THAT WERE ACTUALLY STRANDED - the
# five that sat 40..64 mm north of the network they belong to, plus D10, which
# was 23 mm south of its own divider top, and TP22, which was 31 mm of
# `REC_DIODE_IN` all by itself. U19 and R85..R96 STAY WHERE THEY ARE, in the
# geometry FBV2-P2-002E already routed the dead-cell network in.
#
# That trades section 6's 15 mm TARGET on four nodes for its 20 mm ABSOLUTE
# MAX on all fifteen, on a placement that routes. The four are REF_HO,
# REC_BAT_LOW, REC_GATE_N and REC_LIM_IN, and every one of them is bounded by
# Q5..Q9, which this ECO is not authorised to move.
SOFT = ['USB_VBUS_CHG']
TARGET, ABSMAX = 15.0, 20.0
# the 27.12 MHz NFC oscillator and its reader: section 6 asks for distance from
# RF aggressors where practical, and a 2.2 M node beside a crystal is the
# textbook place not to put one.
AGGRESSOR = [(28.6, 30.0, 6.0), (34.0, 30.0, 6.0)]
# y stops at 30.0, and that is J4.  The battery connector occupies
# x 3.655..9.245, y 30.505..37.495, and it is a 6 mm-tall through-hole part that
# copper cannot cross.  With the region running to y 34 the optimiser put D11,
# C60 and R84 on the FAR SIDE of it - Euclidean MST said 10.25 mm for VREF_TOP
# and the router needed 39.1 mm to walk around J4.  A straight-line span metric
# cannot see a connector; keeping the cluster on its own side of one is the
# cheap way to stop it having to.
REGION = (4.5, 4.0, 25.0, 30.0)
STEP = 0.5


def netmap(M, nets=None):
    nets = NETS if nets is None else nets
    out = {}
    for f in M.b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if n.startswith(N) and n[len(N):] in nets:
                out.setdefault(n[len(N):], []).append(
                    (f.GetReference(), p.GetNumber()))
    return out


def mst(pts):
    if len(pts) < 2:
        return 0.0
    ins, out, tot = [0], list(range(1, len(pts))), 0.0
    while out:
        best = None
        for a in ins:
            for c in out:
                d = math.dist(pts[a], pts[c])
                if best is None or d < best[0]:
                    best = (d, a, c)
        tot += best[0]
        ins.append(best[2])
        out.remove(best[2])
    return tot


def spans(M, nm, place):
    out = {}
    for net, pads in nm.items():
        pts = []
        for (r, n_) in pads:
            pos = place.get(r, M.home[r])
            pts.append(M.pad(r, n_, *pos))
        out[net] = mst(pts)
    return out


def cost(M, nm, place, soft=None):
    """soft is a list of (ref, pad, anchor_xy): a cheap pull toward the fixed
    part of an out-of-scope net.  A full MST over USB_VBUS_CHG is 40+ pads
    evaluated 200 000 times a round, which is what killed the first run."""
    s = spans(M, nm, place)
    c = 0.0
    if soft:
        for (r, n_, ax, ay) in soft:
            if r in place:
                px, py = M.pad(r, n_, *place[r])
                c += math.dist((px, py), (ax, ay)) * 0.05
    for net, v in s.items():
        c += v * 0.05
        if v > TARGET:
            c += (v - TARGET) ** 2
        if v > ABSMAX:
            c += 500 + (v - ABSMAX) ** 2 * 50
    for r, pos in place.items():
        for (ax, ay, ar) in AGGRESSOR:
            d = math.dist((pos[0], pos[1]), (ax, ay))
            if d < ar:
                c += (ar - d) ** 2 * 4
        # MINIMUM DISTURBANCE.  Every millimetre a part moves is a millimetre of
        # placement review, so a move has to pay for itself in span.  Without
        # this the optimiser reaches the same worst-node figure while shuffling
        # twenty-two parts that did not need to move.
        h = M.home[r]
        c += math.dist((pos[0], pos[1]), (h[0], h[1])) * 0.02
        if round(pos[2], 1) != round(h[2], 1):
            c += 0.05
    return c, s


def slots(M, ref, fixed_r):
    cand = []
    for rot in (0, 90, 180, 270):
        rect, _ = M.local(ref, rot)
        x = REGION[0]
        while x <= REGION[2] + 1e-9:
            y = REGION[1]
            while y <= REGION[3] + 1e-9:
                c = (x + rect[0], y + rect[1], x + rect[2], y + rect[3])
                if (c[0] >= M.edge[0] and c[1] >= M.edge[1] and
                        c[2] <= M.edge[2] and c[3] <= M.edge[3] and
                        not any(PS.ovl(c, fr) for fr in fixed_r) and
                        not any(PS.ovl(c, rr) for rr in M.rule)):
                    cand.append((x, y, rot, c))
                y += STEP
            x += STEP
    return cand


def solve(M, rounds=4, verbose=True):
    fixed = M.fixed_courts(MOVE)
    fixed_r = [c for (_, _, c) in fixed]
    nm = netmap(M)
    smap = netmap(M, SOFT)
    soft = []
    for net, pads in smap.items():
        fixedpts = [M.pad(r, n_, *M.home[r]) for (r, n_) in pads if r not in MOVE]
        if not fixedpts:
            continue
        ax = sum(q[0] for q in fixedpts) / len(fixedpts)
        ay = sum(q[1] for q in fixedpts) / len(fixedpts)
        for (r, n_) in pads:
            if r in MOVE:
                soft.append((r, n_, ax, ay))
    tab = {r: slots(M, r, fixed_r) for r in MOVE}
    if verbose:
        print('%d movable parts: %s'
              % (len(MOVE), ', '.join('%s=%d' % (k, len(v))
                                      for k, v in sorted(tab.items()))))
    place = {r: M.home[r] for r in MOVE}
    best_c, s0 = cost(M, nm, place, soft)
    if verbose:
        print('start cost %.2f  worst %s' % (best_c, max(s0.items(), key=lambda kv: kv[1])))
    for it in range(rounds):
        moved = False
        for ref in MOVE:
            others = [M.court(r, *place[r]) for r in MOVE if r != ref]
            cur = place[ref]
            best = (best_c, cur)
            for (x, y, rot, c) in tab[ref]:
                if any(PS.ovl(c, o) for o in others):
                    continue
                place[ref] = (x, y, rot)
                cc, _ = cost(M, nm, place, soft)
                if cc < best[0] - 1e-9:
                    best = (cc, (x, y, rot))
            place[ref] = best[1]
            if best[1] != cur:
                moved, best_c = True, best[0]
        if verbose:
            print('  round %d cost %.2f  worst %.2f' % (it + 1, best_c,
                  max(spans(M, nm, place).values())))
            sys.stdout.flush()
        json.dump({r: [round(v, 3) for v in place[r]] for r in MOVE},
                  open(os.path.join(SP, 'place_002f_deadcell.json'), 'w'), indent=1)
        if not moved:
            break
    return place, spans(M, nm, place), nm


def main():
    faulthandler.enable()
    M = PS.Model(RU.fresh(PS.WORK, 'D0'))
    nm = netmap(M)
    before = spans(M, nm, {})
    softb = spans(M, netmap(M, SOFT), {})
    place, after, _ = solve(M)
    softa = spans(M, netmap(M, SOFT), place)
    rows = []
    for net in NETS:
        rows.append((net, before[net], after[net]))
    print('\n%-14s %9s %9s' % ('net', 'before', 'after'))
    for (n_, b, a) in sorted(rows, key=lambda r: -r[1]):
        flag = '' if a <= TARGET else ('  >target' if a <= ABSMAX else '  **OVER ABSMAX**')
        print('%-14s %9.2f %9.2f%s' % (n_, b, a, flag))
    print('\nworst after: %.2f mm' % max(a for (_, _, a) in rows))
    print('\nmoves:')
    for r in MOVE:
        h, p = M.home[r], place[r]
        if (round(h[0], 3), round(h[1], 3), round(h[2], 1)) != (round(p[0], 3), round(p[1], 3), round(p[2], 1)):
            print('  %-5s (%7.3f,%7.3f,%5.1f) -> (%7.3f,%7.3f,%5.1f)'
                  % (r, h[0], h[1], h[2], p[0], p[1], p[2]))
    json.dump({r: [round(v, 3) for v in place[r]] for r in MOVE},
              open(os.path.join(SP, 'place_002f_deadcell.json'), 'w'), indent=1)
    json.dump(dict(before=before, after=after),
              open(os.path.join(SP, 'place_002f_deadcell_spans.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
