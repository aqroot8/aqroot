# -*- coding: utf-8 -*-
"""FBV2-P2-002C PHASE A -- the whole battery / protection block on ONE
project-faithful scratch copy, routed by PATH ROLE.

Nothing here touches the authoritative board.
"""
import os, sys, json, math, time
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import path_role_dru as DRU
import battery_route_plan as PL
import qrouter as QR
import pcbnew

WORK = os.path.join(SP, "w")
if not os.path.isdir(WORK):
    os.makedirs(WORK)
N = PL.N
CP, CT_W, CT_S = 200000, 300000, 200000
WIDE = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                 'BAT_SENSE', 'BAT_PROTECTED_P'))
AREAS = ['BAT_PROT_TAP_U18', 'BAT_PROT_TAP_U14', 'BAT_PROT_ESCAPE_U11',
         'BAT_SENSE_KELVIN', 'BAT_RAW_TAP_U18']
STUBAREAS = ['BAT_STUB_%d' % k for k in range(10)]
FLOOR = {N + 'BAT_CONNECTOR_P': 600000, N + 'BAT_RAW': 600000,
         N + 'BAT_MID': 600000, N + 'BAT_SENSE': 600000,
         N + 'BAT_PROTECTED_P': 1200000}


def mst(pads):
    refs = list(pads)
    if len(refs) < 2:
        return []
    inside, out = {refs[0]}, []
    while len(inside) < len(refs):
        best = None
        for a in inside:
            for b in refs:
                if b in inside:
                    continue
                d = math.hypot(pads[a]['x'] - pads[b]['x'], pads[a]['y'] - pads[b]['y'])
                if best is None or d < best[0]:
                    best = (d, a, b)
        out.append((best[1], best[2]))
        inside.add(best[2])
    return out


def connected(pcb, a, b):
    bd = pcbnew.LoadBoard(pcb)
    bd.BuildConnectivity()
    cn = bd.GetConnectivity()
    pads = {}
    for f in bd.GetFootprints():
        for p in f.Pads():
            pads[f.GetReference() + '.' + p.GetNumber()] = p
    pa, pb = pads.get(a), pads.get(b)
    if pa is None or pb is None:
        return False
    s = {str(i.m_Uuid.AsString()) for i in cn.GetConnectedItems(pa)}
    return str(pb.m_Uuid.AsString()) in s


def main():
    t_all = time.time()
    pcb = RU.fresh(WORK, "A")
    b = pcbnew.LoadBoard(pcb)
    tp = [f for f in b.GetFootprints() if f.GetReference() == 'TP34'][0]
    if tp.GetLayer() != pcbnew.B_Cu:
        tp.Flip(tp.GetPosition(), False)
    tp34 = (round(tp.GetPosition().x / 1e6, 3), round(tp.GetPosition().y / 1e6, 3),
            b.GetLayerName(tp.GetLayer()))
    for a in AREAS + STUBAREAS:
        RU.add_named_area(b, a, 0, 0, 1000, 1000)
    b.Save(pcb)
    DRU.write(pcb, [])

    base, _ = RU.drc(pcb, "Abase", WORK)
    base_rn = RU.ratsnest(pcb)
    print("scratch baseline", dict(sorted(base.items())), "ratsnest", base_rn)

    qb = QR.QBoard(pcb)
    qb.wide_nets = WIDE
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(net, {})[ref] = p

    journal, stubs, area_box = [], [], {}
    state = dict(fail=None, rn=base_rn, done=0, skipped=0)

    def apply_areas():
        for name, bx in area_box.items():
            RU.set_area_box(qb.b, name, bx[0] - 300000, bx[1] - 300000,
                            bx[2] + 300000, bx[3] + 300000)

    def grow(area, tracks):
        bx = area_box.get(area)
        for t in tracks:
            hw = t.GetWidth() // 2
            for (x, y) in ((t.GetStart().x, t.GetStart().y),
                           (t.GetEnd().x, t.GetEnd().y)):
                nb = (x - hw, y - hw, x + hw, y + hw)
                bx = nb if bx is None else (min(bx[0], nb[0]), min(bx[1], nb[1]),
                                            max(bx[2], nb[2]), max(bx[3], nb[3]))
        area_box[area] = bx

    def gate():
        apply_areas()
        # A through via punches a hole in the In1 GND plane, so the plane has to
        # be refilled before DRC means anything.  Doing it inside the gate keeps
        # every per-connection measurement honest.
        pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
        qb.save()
        DRU.write(pcb, stubs)
        after, det = RU.drc(pcb, "A", WORK)
        d = dict((k, v - base.get(k, 0)) for k, v in after.items()
                 if v > base.get(k, 0) and k != 'unconnected_items')
        rn = RU.ratsnest(pcb)
        if d:
            return dict(ok=False, why='new DRC %s' % json.dumps(d),
                        detail={k: det[k][:3] for k in d})
        if rn >= state['rn']:
            return dict(ok=False, why='ratsnest did not fall (%d -> %d)'
                                      % (state['rn'], rn))
        state['rn'] = rn
        return dict(ok=True)

    def cluster_of(ref):
        """UUIDs of everything already electrically joined to this pad.  A tap
        must land on copper the pad is NOT already connected to, or it connects
        the net to itself and the ratsnest never moves."""
        qb.b.BuildConnectivity()
        cn = qb.b.GetConnectivity()
        for f in qb.b.GetFootprints():
            for pp in f.Pads():
                if f.GetReference() + '.' + pp.GetNumber() == ref:
                    return {str(i.m_Uuid.AsString()) for i in cn.GetConnectedItems(pp)}
        return set()

    def anchor_on(net, x, y, width, ct, skip=()):
        """Nearest point on copper this net already owns AT WHICH A TRACK OF
        `width` CAN LEGALLY START.

        A decoupling capacitor taps the NODE; it does not sit in the current
        path, and it must not be reached through the 0.20 mm package escape at
        the far end of the trunk.  Merely nearest is not enough - the nearest
        point on the trunk is often inside the pin field it just escaped."""
        LID = qb.b.GetLayerID('B.Cu')
        best = None
        for t in qb.b.GetTracks():
            if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != LID:
                continue
            if t.GetNetname() != net:
                continue
            if str(t.m_Uuid.AsString()) in skip:
                continue
            ax, ay = t.GetStart().x, t.GetStart().y
            bx, by = t.GetEnd().x, t.GetEnd().y
            L = math.hypot(bx - ax, by - ay)
            n = max(1, int(L // 100000))
            for k in range(n + 1):
                u = k / float(n)
                px, py = int(ax + u * (bx - ax)), int(ay + u * (by - ay))
                d = math.hypot(px - x, py - y)
                if best is not None and d >= best[0]:
                    continue
                if not qb.point_free('B', net, px, py, width, CP, ct, 50000):
                    continue
                best = (d, px, py, t)
        if best is None:
            return None
        d = RU.pseudo_pad(net, best[1], best[2], QR)
        d['anchor'] = True
        d['ref'] = '(node)'
        d['track'] = best[3]
        return d

    def run(net, a, b_, role, ladder, area, ct):
        if state['fail']:
            return
        pa = pads[net].get(a)
        node = (b_ == '(node)')
        skip = set()
        pb = None if node else pads[net].get(b_)
        if pa is None or (pb is None and not node):
            state['fail'] = '%s: missing pad %s/%s' % (net, a, b_)
            return
        ref = b_ if not node else {N + 'BAT_PROTECTED_P': 'R75.2',
                                   N + 'BAT_RAW': 'F1.2',
                                   N + 'BAT_SENSE': 'R75.1',
                                   N + 'BAT_MID': 'Q2.5',
                                   N + 'BAT_CONNECTOR_P': 'F1.1'}.get(net)
        if ref and connected(pcb, a, ref):
            state['skipped'] += 1
            return
        if node:
            skip = cluster_of(a)
        m = qb.mark()
        t0 = time.time()
        r, used, hop, tapped = None, None, False, node
        if role == 'TAP':
            # A shunt tap is judged on RESISTANCE, not on raw width: an 80 mm
            # detour at 1.20 mm is worse copper than a 6 mm run at 0.60 mm, and
            # it eats a corridor something else needs.  Try every rung, keep the
            # one with the fewest squares.
            best = None
            for w in ladder:
                tgt = anchor_on(net, pa['x'], pa['y'], w, ct, skip) if node else pb
                if tgt is None:
                    continue
                rr = QR.connect_role(qb, net, pa, tgt, 'B', w, CP, ct)
                qb.revert(m)
                if rr['ok']:
                    sq = rr['mm'] / (w / 1e6)
                    if best is None or sq < best[0]:
                        best = (sq, w, tgt)
            if best is not None:
                used, pb = best[1], best[2]
                r = QR.connect_role(qb, net, pa, pb, 'B', used, CP, ct)
            else:
                r = dict(ok=False, reason='NO_PATH',
                         why='no corridor at any rung for %s' % a)
        else:
            for w in ladder:
                tgt = anchor_on(net, pa['x'], pa['y'], w, ct, skip) if node else pb
                if tgt is None:
                    r = dict(ok=False, reason='NO_NODE',
                             why='no point on %s copper admits %.2f mm'
                                 % (net.split('/')[-1], w / 1e6))
                    continue
                r = QR.connect_role(qb, net, pa, tgt, 'B', w, CP, ct)
                if r['ok']:
                    used = w
                    pb = tgt
                    break
                qb.revert(m)
        # FALLBACK LADDER, widest and simplest first.  Every rung is legal
        # copper; none of them narrows below the applicable floor.
        #   1. B.Cu, pad to pad                (already tried above)
        #   2. B.Cu, pad to the nearest legal point on this net's own copper
        #   3. F.Cu with two through vias, pad to pad
        #   4. F.Cu with two through vias, pad to node
        if not r['ok'] and not node:
            skip = cluster_of(a)
            for w in ladder:
                tgt = anchor_on(net, pa['x'], pa['y'], w, ct, skip)
                if tgt is None:
                    continue
                r = QR.connect_role(qb, net, pa, tgt, 'B', w, CP, ct)
                if r['ok']:
                    used, pb, tapped = w, tgt, True
                    break
                qb.revert(m)
        if not r['ok']:
            for use_node in (False, True) if not node else (True,):
                for w in ladder:
                    if use_node and not skip:
                        skip = cluster_of(a)
                    tgt = (anchor_on(net, pa['x'], pa['y'], w, ct, skip)
                           if use_node else pb)
                    if tgt is None:
                        continue
                    vd, vk = ((600000, 300000) if role == 'SIG'
                              else (800000, 400000))
                    r = QR.connect_hop(qb, net, pa, tgt, w, CP, ct,
                                       via_dia=vd, via_drill=vk)
                    if r['ok']:
                        used, hop, pb = w, True, tgt
                        tapped = tapped or use_node
                        break
                    qb.revert(m)
                if r['ok']:
                    break
        if not r['ok']:
            qb.revert(m)
            state['fail'] = '%s %s->%s (%s) : %s : %s' % (
                net.split('/')[-1], a, b_, role, r['reason'], r.get('why', ''))
            return
        if tapped and pb is not None and pb.get('track') is not None:
            # Make the junction an EXACT shared endpoint of three tracks by
            # splitting the trunk at the tap point.  A branch end merely lying
            # inside the trunk's copper is what KiCad reports as track_dangling.
            uid = str(pb['track'].m_Uuid.AsString())
            made = RU.split_at(qb.b, pb['track'], pb['x'], pb['y'])
            if made:
                idx = [i for i, t in enumerate(qb.laid)
                       if str(t.m_Uuid.AsString()) == uid]
                if idx:
                    qb.laid[idx[0]:idx[0] + 1] = made
                else:
                    qb.laid.extend(made)
        if area:
            grow(area, qb.laid[m[0]:])
        elif used < FLOOR.get(net, 0):
            area = 'BAT_STUB_%d' % len(stubs)
            stubs.append((area, net, used / 1e6,
                          'BOUNDED SHUNT STUB %s to %s at %.2f mm'
                          % (net.split('/')[-1], b_, used / 1e6)))
            grow(area, qb.laid[m[0]:])
        g = gate()
        if not g['ok']:
            qb.revert(m)
            if stubs and stubs[-1][0] == area:
                stubs.pop()
                area_box.pop(area, None)
            state['fail'] = '%s %s->%s (%s) : %s %s' % (
                net.split('/')[-1], a, b_, role, g['why'], g.get('detail', ''))
            return
        state['done'] += 1
        journal.append(dict(net=net.split('/')[-1], a=a, b=b_, role=role,
                            mm=round(r['mm'], 3), w=used / 1e6, grid=r['grid'],
                            area=area, profile=r.get('profile'),
                            vias=r.get('vias', 0), layer=r.get('layer', 'B.Cu'),
                            secs=round(time.time() - t0, 1)))
        print("  %-5s %-18s %-8s -> %-8s %8.3f mm  w=%.2f  g=%.3f %s %.0fs"
              % (role, net.split('/')[-1], a, b_, r['mm'], used / 1e6, r['grid'],
                 ('F.Cu+2 vias' if hop else '           '), time.time() - t0))
        sys.stdout.flush()

    # ORDER NOTE.  Section 12 lists BAT_PROTECTED_P last inside group A.  Taken
    # literally that fails: the 1.00 mm BAT_MAIN copper laid first closes the
    # west margin and leaves no 1.20 mm corridor for the one connection that has
    # a hard floor and no fallback ladder.  Section 14 ranks LEGAL above every
    # other objective, so the most constrained member of group A is routed
    # first and the rest of the chain follows.  The order WITHIN the chain, and
    # the order of groups A/B/C/D/E, is otherwise exactly as section 12 gives it.
    print("--- A2. BAT_PROTECTED_P 1.50 mm trunk (most constrained, routed first) ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_A:
        if net == N + 'BAT_PROTECTED_P':
            run(net, a, b_, role, lad, area, CT_W)

    # U11.2 flared escape + the trunk approach
    if not state['fail']:
        net = N + 'BAT_PROTECTED_P'
        m = qb.mark()
        # reachability regions seeded at D9.1's own 1.50 mm launch, so the
        # flare ends where the trunk can actually leave from
        eD = qb.escape(pads[net]['D9.1'], 'B', PL.W_TRUNK_BPP, PL.W_TRUNK_BPP,
                       CP, CT_W, 50000, qb.ex0, qb.ey0)
        regs = {}
        if eD:
            seed = (eD[0]['x'], eD[0]['y'])
            for w in (300000, 400000, 600000, 800000, 1000000, 1200000,
                      PL.W_TRUNK_BPP):
                regs[w] = qb.free_region('B', net, w, CP, CT_W, 50000, seed,
                                         qb.ex0 - 1000000, qb.ey0 - 1000000,
                                         qb.ex1 + 1000000, qb.ey1 + 1000000)
        f = qb.flare(net, pads[net]['U11.2'], 'B', PL.W_TRUNK_BPP, PL.W_SENSE,
                     CP, CT_W, 25000, region=regs)
        if f is None:
            state['fail'] = 'U11.2 flared escape: none exists'
        else:
            grow('BAT_PROT_ESCAPE_U11', qb.laid[m[0]:])
            lp = dict(ref='U11.2/launch', x=f['x'], y=f['y'], F=False, B=True,
                      shape=QR.RR(f['x'], f['y'], 1, 1, 0, 0, net, 'launch'),
                      hx=1, hy=1, r=0, ang=0, net=net, tht=False)
            r = None
            for w in (PL.W_TRUNK_BPP, 1200000):
                r = QR.connect_role(qb, net, lp, pads[net]['D9.1'], 'B', w, CP, CT_W)
                if r['ok']:
                    break
            if not r['ok']:
                qb.revert(m)
                state['fail'] = 'U11.2 approach: %s %s' % (r['reason'], r.get('why', ''))
            else:
                g = gate()
                if not g['ok']:
                    qb.revert(m)
                    state['fail'] = 'U11.2 approach: %s %s' % (g['why'], g.get('detail', ''))
                else:
                    state['done'] += 1
                    journal.append(dict(net='BAT_PROTECTED_P', a='U11.2',
                                        b='D9.1', role='TRUNK+ESCAPE',
                                        mm=round(f['total'] + r['mm'], 3),
                                        w=1.5, grid=r['grid'], flare=f))
                    print("  TRUNK BAT_PROTECTED_P    U11.2    -> D9.1    "
                          "%8.3f mm  (escape %.3f mm, neck %.3f mm at 0.20)"
                          % (f['total'] + r['mm'], f['total'], f['neck_len']))

    print("--- A1b. C59, the long way out of the south-west corner ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_TIGHT:
        run(net, a, b_, role, lad, area, CT_W)

    print("--- A1a. south-west corner: U14 fuel-gauge taps and TP15 ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_SW:
        run(net, a, b_, role, lad, area, CT_W)

    print("--- A1. BAT_MAIN high-current chain ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_A:
        if net != N + 'BAT_PROTECTED_P':
            run(net, a, b_, role, lad, area, CT_W)

    print("--- A2b. decoupling capacitor taps ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_CAPS:
        run(net, a, b_, role, lad, area, CT_W)

    print("--- B. Kelvin / sense branches ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_B:
        run(net, a, b_, role, lad, area, CT_W)
    print("--- A3. microamp taps ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_TAPS:
        run(net, a, b_, role, lad, area, CT_W)
    print("--- B2. LTC4368 VIN supply tap ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_B2:
        run(net, a, b_, role, lad, area, CT_W)

    print("--- E. fuel gauge / test branches ---")
    for (net, a, b_, role, lad, area) in PL.PLAN_E:
        run(net, a, b_, role, lad, area, CT_W)
    print("--- C/D. LTC + dead-cell networks ---")
    for short in PL.SIGNAL_ORDER:
        if state['fail']:
            break
        net = N + short
        for a, b_ in mst(pads[net]):
            run(net, a, b_, 'SIG', [PL.W_SIG, 200000, 150000], None, CT_S)

    apply_areas()
    pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
    qb.save()
    DRU.write(pcb, stubs)
    after, det = RU.drc(pcb, "Afinal", WORK)
    rn = RU.ratsnest(pcb)
    res = dict(fail=state['fail'], connections=state['done'],
               skipped=state['skipped'], tp34=tp34, stubs=stubs,
               areas=dict((k, [round(v / 1e6, 3) for v in bx])
                          for k, bx in area_box.items() if bx),
               drc=dict(sorted(after.items())), baseline=dict(sorted(base.items())),
               ratsnest=rn, ratsnest_delta=rn - base_rn, journal=journal,
               secs=round(time.time() - t_all, 1))
    json.dump(res, open(os.path.join(SP, 'phaseA.json'), 'w'), indent=1)
    print("\nPHASE A:", ("FAIL -- " + state['fail']) if state['fail'] else "COMPLETE")
    print("routed", state['done'], "skipped-already-connected", state['skipped'],
          "ratsnest", rn, "(%+d)" % (rn - base_rn))
    print("DRC", dict(sorted(after.items())))
    if stubs:
        print("bounded stub exceptions:", [(s[0], s[2]) for s in stubs])


main()
