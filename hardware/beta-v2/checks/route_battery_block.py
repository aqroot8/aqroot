# -*- coding: utf-8 -*-
"""FBV2-P2-002C PHASE A -- the whole battery / protection block on ONE
project-faithful scratch copy, routed by PATH ROLE.

Nothing here touches the authoritative board.
"""
import os, sys, json, math, time, faulthandler
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


def area_stats(board, area_trk):
    out = {}
    for name, trks in area_trk.items():
        if not trks:
            continue
        ps = RU.corridor_from_tracks(board, trks)
        bb = ps.BBox()
        box = (bb.GetWidth() / 1e6) * (bb.GetHeight() / 1e6)
        out[name] = dict(area_mm2=round(ps.Area() / 1e12, 3),
                         bbox_mm=[round(bb.GetWidth() / 1e6, 2),
                                  round(bb.GetHeight() / 1e6, 2)],
                         fill_ratio=round(ps.Area() / 1e12 / box, 3) if box else 0,
                         vertices=sum(ps.Outline(i).PointCount()
                                      for i in range(ps.OutlineCount())),
                         segments=len(trks))
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
    # PR-15: a SIGSEGV used to kill the run with no Python frame at all.  Enable
    # the fault handler as well as the watchdog, so a crash names the call.
    faulthandler.enable()
    if os.environ.get('AQROOT_WATCHDOG'):
        faulthandler.dump_traceback_later(
            int(os.environ['AQROOT_WATCHDOG']), repeat=True)
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

    journal, stubs, area_trk = [], [], {}
    # PR-20.  THE BUDGET WAS STARVING THE FALLBACKS, AND THAT LOOKED LIKE A
    # NONDETERMINISTIC ROUTER.  Both fallback stages are guarded by
    # `time.time() - t0 < ITEM_BUDGET`, so when the B.Cu width ladder alone ran
    # past the budget the F.Cu hop was never attempted at all.  BAT_SENSE
    # Q3.6 -> R75.1 routed in 86 s on one run and returned NO_PATH after 167 s
    # on the next with identical copper in front of it - the only difference was
    # how busy the machine was.  Section 13 allows ten minutes per connection;
    # the budget now sits inside that, so the ladder can be slow without
    # silently deleting the topology fallbacks.
    ITEM_BUDGET = float(os.environ.get('AQROOT_ITEM_BUDGET', '420'))
    TEST_CAP = float(os.environ.get('AQROOT_TEST_CAP', '10'))    # mm, section 9

    def _ckpt(j):
        """The board is saved on every gate; the journal was only written at
        the end, so a crash threw away the record of what had been laid."""
        try:
            json.dump(j, open(os.path.join(SP, 'phaseA_journal.json'), 'w'), indent=1)
        except Exception:
            pass

    state = dict(fail=None, last=None, rn=base_rn, done=0, skipped=0)

    def apply_areas():
        """PR-11: every exception area is a CORRIDOR around its own branch
        centreline, not a bounding box.  A box around a 20 mm branch was a
        67 x 23 mm hole in the trunk rule; a corridor covers the branch copper
        plus 0.10 mm per side and nothing else."""
        for name, trks in area_trk.items():
            if trks:
                RU.set_area_poly(qb.b, name, RU.corridor_from_tracks(qb.b, trks))

    def grow(area, tracks):
        area_trk.setdefault(area, []).extend(tracks)

    def gate(verbose=False):
        tg = [time.time()]
        apply_areas()
        tg.append(time.time())
        # A through via punches a hole in the In1 GND plane, so the plane has to
        # be refilled before DRC means anything.  Doing it inside the gate keeps
        # every per-connection measurement honest.
        pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
        tg.append(time.time())
        qb.save()
        DRU.write(pcb, stubs)
        tg.append(time.time())
        after, det = RU.drc(pcb, "A", WORK)
        tg.append(time.time())
        if os.environ.get('AQROOT_GATE_TIMING'):
            print("        gate: areas %.1f  fill %.1f  save %.1f  drc %.1f"
                  % (tg[1] - tg[0], tg[2] - tg[1], tg[3] - tg[2], tg[4] - tg[3]))
            sys.stdout.flush()
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

    def joined(a, b):
        """PR-22.  CONNECTIVITY IS A PROPERTY OF THE LIVE BOARD, NOT OF THE FILE.

        The old check re-read the .kicad_pcb from disk.  gate() saves BEFORE it
        judges, so after a REJECTED connection the file still carries copper
        that has since been reverted out of memory - and the next item asked
        that file whether its two pads were already joined, was told yes, and
        was skipped.  Connections that had never been routed were being counted
        as done.  Ask the board that is actually being routed."""
        qb.b.BuildConnectivity()
        cn = qb.b.GetConnectivity()
        pp = {}
        for f in qb.b.GetFootprints():
            for q in f.Pads():
                pp[f.GetReference() + '.' + q.GetNumber()] = q
        pa_, pb_ = pp.get(a), pp.get(b)
        if pa_ is None or pb_ is None:
            return False
        s = {str(i.m_Uuid.AsString()) for i in cn.GetConnectedItems(pa_)}
        return str(pb_.m_Uuid.AsString()) in s

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
        point on the trunk is often inside the pin field it just escaped.

        Sampled at 0.5 mm and tested NEAREST-FIRST with an early exit: at
        0.1 mm with no early exit this was thousands of full obstacle scans per
        call, and it is called once per width rung on every fallback.
        """
        LID = qb.b.GetLayerID('B.Cu')
        cand = []
        for t in qb.b.GetTracks():
            if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != LID:
                continue
            if t.GetNetname() != net or str(t.m_Uuid.AsString()) in skip:
                continue
            ax, ay = t.GetStart().x, t.GetStart().y
            bx, by = t.GetEnd().x, t.GetEnd().y
            L = math.hypot(bx - ax, by - ay)
            n = max(1, int(L // 500000))
            for k in range(n + 1):
                u = k / float(n)
                px, py = int(ax + u * (bx - ax)), int(ay + u * (by - ay))
                cand.append((math.hypot(px - x, py - y), px, py, t))
        cand.sort(key=lambda c: c[0])
        for (_, px, py, t) in cand[:400]:
            if qb.point_free('B', net, px, py, width, CP, ct, 50000):
                d = RU.pseudo_pad(net, px, py, QR)
                d['anchor'] = True
                d['ref'] = '(node)'
                d['track'] = t
                return d
        return None

    def run(net, a, b_, role, ladder, area, ct, fatal=True):
        if state['fail']:
            return False
        pa = pads[net].get(a)
        node = (b_ == '(node)')
        skip = set()
        pb = None if node else pads[net].get(b_)
        if pa is None or (pb is None and not node):
            state['last'] = '%s: missing pad %s/%s' % (net, a, b_)
            if fatal:
                state['fail'] = state['last']
            return False
        # A '(node)' target means "join this pad to its own net, anywhere".
        # It is therefore already satisfied whenever the pad shares a cluster
        # with ANY other pad of the net - which is what makes a general
        # node-closure stage possible without a hand-written table of anchors.
        ref = b_ if not node else {N + 'BAT_PROTECTED_P': 'R75.2',
                                   N + 'BAT_RAW': 'F1.2',
                                   N + 'BAT_SENSE': 'R75.1',
                                   N + 'BAT_MID': 'Q2.5',
                                   N + 'BAT_CONNECTOR_P': 'F1.1'}.get(net)
        if node and ref is None:
            others = [o for o in pads.get(net, {}) if o != a]
            if any(joined(a, o) for o in others):
                state['skipped'] += 1
                return True
        if ref and joined(a, ref):
            state['skipped'] += 1
            print("  SKIP  %-18s %-8s -> %-8s  (already joined via %s)"
                  % (net.split('/')[-1], a, b_, ref))
            sys.stdout.flush()
            return True
        if node:
            skip = cluster_of(a)
        m = qb.mark()
        t0 = time.time()
        if os.environ.get('AQROOT_GATE_TIMING'):
            print("        try   %-18s %-8s -> %-8s" % (net.split('/')[-1], a, b_))
            sys.stdout.flush()
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
                if time.time() - t0 > ITEM_BUDGET and used is None and r is not None:
                    break
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
        # FALLBACKS ARE ABOUT TOPOLOGY, NOT WIDTH.  If the widest rung could
        # not find a pad-to-pad corridor, retrying every rung again through the
        # node and layer-hop paths multiplies the cost of a connection that is
        # going to be requeued anyway.  The fallbacks use the narrowest legal
        # rung only, which is the one most likely to fit.
        # PR-21: a TRUNK keeps its WIDTH across a layer change.  Dropping a
        # 1.00 mm BAT_MAIN run to 0.60 mm to buy a hop trades 4.4 mOhm of B-34
        # for two vias worth 1.8 mOhm, which is a bad trade made silently.
        # Signal and tap roles still use the narrowest rung - for them the hop
        # is about topology and the width is not carrying anything.
        hop_lad = ladder if role == 'TRUNK' else ladder[-1:]
        if not r['ok'] and not node and time.time() - t0 < ITEM_BUDGET:
            skip = cluster_of(a)
            for w in hop_lad:
                tgt = anchor_on(net, pa['x'], pa['y'], w, ct, skip)
                if tgt is None:
                    continue
                r = QR.connect_role(qb, net, pa, tgt, 'B', w, CP, ct)
                if r['ok']:
                    used, pb, tapped = w, tgt, True
                    break
                qb.revert(m)
        if not r['ok'] and time.time() - t0 < ITEM_BUDGET:
            for use_node in (False, True) if not node else (True,):
                for w in hop_lad:
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
            state['last'] = '%s %s->%s (%s) : %s : %s' % (
                net.split('/')[-1], a, b_, role, r['reason'], r.get('why', ''))
            print("  ....  %-18s %-8s -> %-8s  %-18s %.0fs"
                  % (net.split('/')[-1], a, b_, r['reason'], time.time() - t0))
            sys.stdout.flush()
            if fatal:
                state['fail'] = state['last']
            return False
        split_undo = None
        if tapped and pb is not None and pb.get('track') is not None:
            # Make the junction an EXACT shared endpoint of three tracks by
            # splitting the trunk at the tap point.  A branch end merely lying
            # inside the trunk's copper is what KiCad reports as track_dangling.
            #
            # PR-15.  THE SPLIT REWRITES qb.laid IN PLACE, AND THE MARK TAKEN
            # BEFORE IT IS AN INDEX INTO THAT LIST.  Replacing one entry with
            # two shifts everything after it by one, so a mark taken earlier
            # now points one track short - and revert() then removes a track
            # belonging to the TRUNK and leaves one of this connection's own
            # behind.  Do that twice on the same trunk and the second revert
            # calls BOARD::Remove on an item that is no longer in the list,
            # which is a SEGMENTATION FAULT, not an exception.  Shift the mark
            # with the list, and keep enough state to put the trunk back.
            orig = pb['track']
            uid = str(orig.m_Uuid.AsString())
            idx = [i for i, t in enumerate(qb.laid)
                   if str(t.m_Uuid.AsString()) == uid]
            made = RU.split_at(qb.b, orig, pb['x'], pb['y'])
            if made:
                at = idx[0] if idx else None
                if at is not None:
                    qb.laid[at:at + 1] = made
                    if m[0] > at:
                        m = (m[0] + len(made) - 1, m[1], m[2])
                else:
                    qb.laid.extend(made)
                split_undo = (orig, made, at)

        def unsplit(mm):
            """Put the trunk back exactly as it was, then the mark is valid."""
            if split_undo is None:
                return mm
            o, md, at = split_undo
            for t in md:
                qb.b.Remove(t)
            if at is not None:
                qb.laid[at:at + len(md)] = [o]
                if mm[0] > at:
                    mm = (mm[0] - (len(md) - 1), mm[1], mm[2])
            else:
                for t in md:
                    if t in qb.laid:
                        qb.laid.remove(t)
            qb.b.Add(o)
            return mm

        _pre_area = len(area_trk.get(area, [])) if area else 0
        if area:
            grow(area, qb.laid[m[0]:])
        elif used < FLOOR.get(net, 0):
            area = 'BAT_STUB_%d' % len(stubs)
            stubs.append((area, net, used / 1e6,
                          'BOUNDED SHUNT STUB %s to %s at %.2f mm'
                          % (net.split('/')[-1], b_, used / 1e6)))
            grow(area, qb.laid[m[0]:])
        # PR-16, section 9: TP17's stub is capped at 10 mm, because a 24 mm
        # run to a test point is not a stub - it is a second route on the net,
        # taking exactly the corridor section 8 reserves for functional copper.
        # The cap is TP17's alone: section 9 sets it for TP17, and section 4
        # gives the other test taps a WIDTH ruling and no length ruling.  Applied
        # to all of them it rejected TP20 at 14.7 mm against a limit nobody
        # wrote.
        cap = TEST_CAP if (role == 'TEST' and a.startswith('TP17')) else None
        if cap is not None and r['mm'] > cap:
            m = unsplit(m)
            qb.revert(m)
            state['last'] = ('%s %s->%s (TEST) : stub %.3f mm exceeds the %.1f mm cap'
                             % (net.split('/')[-1], a, b_, r['mm'], cap))
            print("  ....  %-18s %-8s -> %-8s  %-18s %.0fs"
                  % (net.split('/')[-1], a, b_, 'STUB_TOO_LONG', time.time() - t0))
            sys.stdout.flush()
            if fatal:
                state['fail'] = state['last']
            return False
        g = gate()
        if not g['ok']:
            m = unsplit(m)
            qb.revert(m)
            if area:
                area_trk[area] = area_trk.get(area, [])[:_pre_area]
            if stubs and stubs[-1][0] == area:
                stubs.pop()
                area_trk.pop(area, None)
            state['last'] = '%s %s->%s (%s) : %s %s' % (
                net.split('/')[-1], a, b_, role, g['why'], g.get('detail', ''))
            if fatal:
                state['fail'] = state['last']
            return False
        state['done'] += 1
        _ckpt(journal)
        journal.append(dict(net=net.split('/')[-1], a=a, b=b_, role=role,
                            mm=round(r['mm'], 3), w=used / 1e6, grid=r['grid'],
                            area=area, profile=r.get('profile'),
                            vias=r.get('vias', 0), layer=r.get('layer', 'B.Cu'),
                            secs=round(time.time() - t0, 1)))
        print("  %-5s %-18s %-8s -> %-8s %8.3f mm  w=%.2f  g=%.3f %s %.0fs"
              % (role, net.split('/')[-1], a, b_, r['mm'], used / 1e6, r['grid'],
                 ('F.Cu+2 vias' if hop else '           '), time.time() - t0))
        sys.stdout.flush()
        return True

    # ORDER IS A PREFERENCE, NOT A CONTRACT.
    #
    # The priority list is the section 12 order refined by what this board is
    # actually scarce in: U18's MSOP-10 pin field first - each pin has a
    # 0.325 mm escape window and no second chance - then the 1.50 mm trunk, the
    # BAT_MAIN chain, and test points last.
    #
    # But hand-tuning an order is a losing game: every fix moved the failure to
    # the next pin.  So the list is worked as a QUEUE OVER REPEATED PASSES.  A
    # connection that cannot route yet is set aside and retried once the others
    # have laid their copper, and the run only fails when an entire pass makes
    # no progress at all.  That converges on an order the board will accept
    # rather than one that was guessed.
    QUEUE = []

    def add(title, group, ct, tight=False):
        for (net, a, b_, role, lad, area) in group:
            QUEUE.append(dict(title=title, net=net, a=a, b=b_, role=role,
                              lad=lad, area=area, ct=ct, tight=tight))

    def widest_escape(pad):
        """The widest track that can still legally leave this pad RIGHT NOW,
        by binary search against the live obstacle set."""
        lo, hi, best = 50000, 1000000, 0
        while hi - lo > 5000:
            mid = ((lo + hi) // 2 // 5000) * 5000
            if qb.escape(pad, 'B', mid, mid, CP, CT_W, 25000, qb.ex0, qb.ey0):
                best, lo = mid, mid
            else:
                hi = mid
        return best

    def order_tight(queue, verbose=True):
        """PR-19.  THE PIN-FIELD ORDER IS MEASURED, NOT GUESSED.

        Three orders were tried by hand inside U18's MSOP-10 and each one simply
        moved the casualty: inner pins first lost U18.10 and U18.1 to NO_PATH,
        outer pins first lost U18.9 - the KELVIN branch section 10 makes
        mandatory - to NO_LEGAL_ESCAPE.  There is no fixed order, because the
        window each pin has left depends on the copper already laid, and that
        changes every pass.

        So measure it.  Before each pass, ask every remaining fine-pitch pin how
        wide a track can still leave it, and route the TIGHTEST FIRST.  A pin
        with 0.20 mm of window left and a 0.20 mm requirement has no slack and
        no second chance; a pin with 0.60 mm can wait.  The block keeps its
        position in the queue - this reorders WITHIN the pin field, it does not
        promote it past the trunk."""
        idx = [i for i, it in enumerate(queue) if it.get('tight')]
        if len(idx) < 2:
            return queue
        rows = []
        for i in idx:
            pad = pads.get(queue[i]['net'], {}).get(queue[i]['a'])
            w = widest_escape(pad) if pad else 0
            need = min(queue[i]['lad'])
            rows.append((w - need, w, i))
        rows.sort(key=lambda r: (r[0], r[1]))
        if verbose:
            print("      pin-field slack: " + "  ".join(
                "%s %+.2f" % (queue[i]['a'], s / 1e6) for (s, _, i) in rows))
            sys.stdout.flush()
        out = list(queue)
        for slot, (_, _, src) in zip(idx, rows):
            out[slot] = queue[src]
        return out

    # PR-18: SECTION 8's ORDER, AND THE REASON IT IS RIGHT.
    #
    # The queue used to open with U18's whole pin field, on the argument that an
    # MSOP-10 pin has a 0.325 mm escape window and no second chance.  True, but
    # it inverts the scarcity: a 0.20 mm sense tap that lands ON R75.2 takes the
    # 1.20 mm trunk's ONLY escape from that pad, and no later pass can give it
    # back because copper on this board only ever accumulates.  That is exactly
    # what happened here - `BAT_PROTECTED_P R75.2 -> D9.1` came back
    # NO_LEGAL_ESCAPE at 0 s once U18.8's tap had gone in first.
    #
    # A wide corridor cannot be recovered; a 0.20 mm one usually can.  So the
    # order is section 8's: the 1.50 mm trunk and the BAT_MAIN chain claim their
    # copper first, THEN U18's pin field, with U18.10 (the functional gate
    # output) and U18.1 first inside it per PR-17.
    add("1. BAT_PROTECTED_P trunk", PL.PLAN_1_BPP_TRUNK, CT_W)
    add("2-5. BAT_MAIN chain", PL.PLAN_2_CHAIN, CT_W)
    add("6b. U18 pin field", PL.PLAN_0_U18, CT_W, tight=True)
    # Section 9 is explicit - "Route the actual gate-drive network FIRST:
    # U18 gate control, Q2 gates, Q3 gates".  The plan had the FET sense pairs
    # first on the argument that Q*_CS is boxed between two gate pads while
    # LTC_GATE has an F.Cu hop.  On Q3 that is simply not what happens: the
    # 0.25 mm CS route threads both 0.67 mm inter-pad gaps and Q3.2 is left
    # with NO_LEGAL_ESCAPE - no width, no layer, nothing.  Q*_CS has the same
    # hop available and keeps a workable window when it goes second.
    add("8b. LTC_GATE", PL.PLAN_8_GATE, CT_S)
    add("8a. FET sense pairs", PL.PLAN_8_CS, CT_S)
    add("9. LTC trip network", PL.PLAN_9_TRIP, CT_S)
    add("BAT_RAW taps", PL.PLAN_TAPS, CT_W)
    add("10a. dead-cell divider taps", PL.PLAN_10_DEADCELL_TAPS, CT_W)
    for short in PL.DEADCELL:
        add("10b. dead-cell network",
            [(N + short, a, b_, 'SIG', PL.LAD_SIG, None)
             for a, b_ in mst(pads[N + short])], CT_S)
    add("11. fuel-gauge branches", PL.PLAN_11_GAUGE, CT_W)
    add("12. capacitor taps", PL.PLAN_12_CAPS, CT_W)
    # PR-24: CLOSE WHAT IS STILL OPEN, BEFORE THE TEST POINTS.
    #
    # The plan names ONE pad pair per connection, and when that exact pair has
    # no corridor the net stays open even though the pad may be one short tap
    # away from copper the net already owns - U18.10 -> Q3.4 failed NO_PATH
    # across the whole board while LTC_GATE copper ran within a few millimetres
    # of both.  Connectivity does not care which pair carries it.  So after the
    # named plan, every pad still not joined to its own net is offered a tap on
    # the nearest legal point of that net.  Pads already joined are skipped, so
    # this adds nothing where the plan succeeded, and it runs BEFORE section
    # 13 so a test point still cannot take a functional corridor.
    SCOPE_NETS = []
    for grp in (PL.PLAN_1_BPP_TRUNK, PL.PLAN_2_CHAIN, PL.PLAN_0_U18,
                PL.PLAN_8_CS, PL.PLAN_8_GATE, PL.PLAN_9_TRIP, PL.PLAN_TAPS,
                PL.PLAN_10_DEADCELL_TAPS, PL.PLAN_11_GAUGE, PL.PLAN_12_CAPS):
        for row in grp:
            if row[0] not in SCOPE_NETS:
                SCOPE_NETS.append(row[0])
    for short in PL.DEADCELL:
        if N + short not in SCOPE_NETS:
            SCOPE_NETS.append(N + short)
    CLOSE = []
    for nt in SCOPE_NETS:
        wide = nt in WIDE
        if nt == N + 'BAT_PROTECTED_P':
            lad = [PL.W_TRUNK_BPP, 1200000]      # never below the D-249 floor
        elif wide:
            lad = [PL.W_TRUNK_BAT, 800000, 600000]
        else:
            lad = PL.LAD_SIG
        for ref_ in sorted(pads.get(nt, {})):
            if ref_.startswith('TP'):
                continue
            CLOSE.append((nt, ref_, '(node)', 'TRUNK' if wide else 'SIG',
                          lad, None))
    add("12b. close remaining open pads", CLOSE, CT_W)

    add("13. test-point stubs", PL.PLAN_13_TEST, CT_W)

    def u11_escape():
        """The U11.2 flare is emitted with the trunk, not as a queue item: the
        trunk cannot exist without its own endpoint."""
        net = N + 'BAT_PROTECTED_P'
        m = qb.mark()
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
            qb.revert(m)
            return False
        grow('BAT_PROT_ESCAPE_U11', qb.laid[m[0]:])
        lp = dict(ref='U11.2/launch', x=f['x'], y=f['y'], F=False, B=True,
                  shape=QR.RR(f['x'], f['y'], 1, 1, 0, 0, net, 'launch'),
                  hx=1, hy=1, r=0, ang=0, net=net, tht=False, anchor=True)
        r = None
        for w in (PL.W_TRUNK_BPP, 1200000):
            r = QR.connect_role(qb, net, lp, pads[net]['D9.1'], 'B', w, CP, CT_W)
            if r['ok']:
                break
        if not r['ok'] or not gate()['ok']:
            qb.revert(m)
            area_trk.pop('BAT_PROT_ESCAPE_U11', None)
            return False
        state['done'] += 1
        journal.append(dict(net='BAT_PROTECTED_P', a='U11.2', b='D9.1',
                            role='TRUNK+ESCAPE', mm=round(f['total'] + r['mm'], 3),
                            w=1.5, grid=r['grid'], flare=f))
        print("  TRUNK BAT_PROTECTED_P    U11.2    -> D9.1    %8.3f mm  "
              "(escape %.3f mm, neck %.3f mm at 0.20)"
              % (f['total'] + r['mm'], f['total'], f['neck_len']))
        return True

    u11 = [False]
    for p_ in range(1, 7):
        before = state['done'] + state['skipped']
        print("--- pass %d: %d queued ---" % (p_, len(QUEUE)))
        sys.stdout.flush()
        # PR-23: RE-MEASURE BEFORE EVERY FINE-PITCH PIN, NOT ONCE PER PASS.
        #
        # Each routed branch changes what is left of its neighbours' windows, so
        # a slack table taken at the head of the pass is stale by the second
        # pin.  On the SOIC-8 FET rows the effect is total rather than gradual:
        # Q*_CS owns pins 1 and 3 and LTC_GATE owns 2 and 4, so a CS route
        # threading both 0.67 mm gaps SEALS the gate pad between them - Q3.2
        # went from a workable window to NO_LEGAL_ESCAPE in one connection.
        # Re-measuring in front of every tight item costs a handful of local
        # floods and picks the pin that is about to lose its last option.
        QUEUE = order_tight(QUEUE)
        rest = []
        idx_ = 0
        while idx_ < len(QUEUE):
            it = QUEUE[idx_]
            # Measured ONCE PER PASS, not before every item.  Re-sorting the
            # block mid-pass picks whichever pin is locally tightest and then
            # lays a route that closes two others: it took U18 from 7 escapes
            # of 8 down to 6.  One measurement per pass, acted on in order, is
            # the version that holds.
            idx_ += 1
            if state['fail']:
                rest.append(it)
                continue
            if not run(it['net'], it['a'], it['b'], it['role'], it['lad'],
                       it['area'], it['ct'], fatal=False):
                rest.append(it)
                continue
            # Section 8 item 6: the U11.2 escape belongs with the trunk, not at
            # the end of the pass.  The moment the trunk exists, flare into it -
            # a 1.50 mm endpoint left until last is a corridor nobody reserved.
            if (not u11[0] and not state['fail'] and it['a'] == 'R75.2'
                    and it['b'] == 'D9.1'):
                u11[0] = u11_escape()
        QUEUE = rest
        if not u11[0] and not state['fail']:
            u11[0] = u11_escape()
        if not QUEUE and u11[0]:
            break
        if state['done'] + state['skipped'] == before:
            state['fail'] = (state['last'] if QUEUE else 'U11.2 escape: none exists')
            break

    apply_areas()
    pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
    qb.save()
    DRU.write(pcb, stubs)
    after, det = RU.drc(pcb, "Afinal", WORK)
    rn = RU.ratsnest(pcb)
    res = dict(fail=state['fail'], connections=state['done'],
               skipped=state['skipped'], tp34=tp34, stubs=stubs,
               areas=area_stats(qb.b, area_trk),
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
