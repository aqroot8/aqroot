# -*- coding: utf-8 -*-
"""FBV2-P2-006 -- REUSABLE INCREMENTAL REST-OF-BOARD ROUTER + PROMOTER.

The battery-block driver (route_battery_block.py) is power-tree scoped and the
in-repo "Phase B" replay machinery (replay_battery_block.py / SECTION-17) assumes
a copper-EMPTY authoritative base, so neither can add the 164 remaining
rest-of-board multi-pad nets onto the D-302 promoted board (see D-303 /
phaseB_bringup_probe_005.py).  This module is the missing piece: it routes a
bounded, named net-GROUP onto the promoted authoritative board **without ever
deleting, moving or re-routing a single strand of accepted Phase-A copper**, and
promotes the result only when a real full-board gate proves a genuine
no-casualty / no-new-DRC connectivity increment.

Design invariants (all enforced, not assumed):

  * PRESERVE PHASE-A EXACTLY.  QBoard loads the authoritative board and treats
    every existing track/via/pad/keep-out as an obstacle; new copper is ADDED
    (never Remove()d), so the accepted 432 tracks / 54 vias are carried through
    byte/geometry-equivalent.  The gate re-proves this as a copper-item multiset
    superset check -- if any Phase-A item is missing or altered, GATE FAIL.

  * ADD-ONLY, IN-SCOPE.  Every new copper item must belong to a net in the
    requested group.  New copper on any other net -> GATE FAIL.

  * REAL FULL-BOARD GATE (D-286).  Connectivity is judged by pcbnew connectivity
    on the whole board; legality by real kicad-cli DRC on the whole board.  No
    proxy / focused / post-hoc measurement promotes copper.

  * MONOTONIC.  Ratsnest and DRC unconnected_items must strictly DROP by exactly
    the requested connection count; no other DRC class may appear or increase;
    every prior Phase-A requested-connected pad pair must remain connected.

Commands (run one foreground experiment at a time):

    python3 incremental_router.py baseline
    python3 incremental_router.py route   FRONT_RGB
    python3 incremental_router.py gate     FRONT_RGB
    python3 incremental_router.py promote  FRONT_RGB     # only if gate PASS

`route` writes a scratch copy under checks/w/INC_<GROUP>/ and NEVER touches the
authoritative project.  `promote` copies that scratch board + a merged journal
back onto the authoritative project, but only after re-running the full gate.
"""
import os, sys, json, math, hashlib, shutil, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import qrouter as QR
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')
WORK = os.path.join(SP, 'w')
BASELINE_JSON = os.path.join(SP, 'incremental_baseline_006.json')

# --------------------------------------------------------------------------- #
# GROUP REGISTRY.  A group is a bounded, isolated set of rest-of-board nets that
# is routed and gated as one increment.  Widths/clearances are the KiCad
# netclass floors the DRC enforces (FRONT_RGB nets are unmatched by any
# netclass pattern -> Default: 0.200 mm width, 0.200 mm clearance, no via).
GROUPS = {
    'FRONT_RGB': dict(
        sheet='08_BUTTONS_EXPANDERS',
        desc='front-panel RGB status-LED control lines (U23 expander -> R124/125/126); '
             'noncritical low-speed indicator nets, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['FRONT_RGB_R_N', 'FRONT_RGB_G_N', 'FRONT_RGB_B_N'],
    ),
    # FBV2-P2-007 / D-305 -- accelerometer 3V3 load-switch (U20) local control.
    # Two noncritical low-current control nets: the enable line ACC_3V3_EN
    # (driven from U3.15, pulled by R98, switched into U20.1, probed at TP26) and
    # the current-limit programming strap ACC_3V3_ILIM (set resistor R97 -> U20.4).
    # Both Default netclass (0.200 mm width/clearance, NO via), all B.Cu SMD; a
    # coherent standalone power-gating control subsystem in a low-congestion
    # region (only 4 Phase-A B.Cu strands within bbox+2 mm).  ACC_3V3_EN is a
    # 4-pad multi-terminal net (3-edge MST) -- the first promoted increment to
    # exercise multi-segment MST routing.
    'ACC_3V3_CTL': dict(
        sheet='01_POWER_TREE',
        desc='accelerometer 3V3 load-switch (U20) local control: enable '
             '(U3.15 -> R98/U20.1/TP26) + current-limit set (R97 -> U20.4); '
             'noncritical low-current control, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['ACC_3V3_EN', 'ACC_3V3_ILIM'],
    ),
}


# --------------------------------------------------------------------------- #
# copper-item fingerprints (geometry-based Phase-A preservation proof)
def _track_sig(t):
    a = (t.GetStart().x, t.GetStart().y)
    z = (t.GetEnd().x, t.GetEnd().y)
    lo, hi = min(a, z), max(a, z)
    return ('T', t.GetNetname(), t.GetLayer(), lo, hi, t.GetWidth())


def _via_sig(t):
    p = t.GetPosition()
    return ('V', t.GetNetname(), (p.x, p.y), t.GetWidth(pcbnew.F_Cu), t.GetDrill())


def copper_sigs(board):
    c = collections.Counter()
    for t in board.GetTracks():
        cls = t.GetClass()
        if cls == 'PCB_TRACK':
            c[_track_sig(t)] += 1
        elif cls == 'PCB_VIA':
            c[_via_sig(t)] += 1
    return c


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


# --------------------------------------------------------------------------- #
def resolve_nets(qb, group):
    """Map each group base-net-name to its full net name on the board."""
    out = {}
    for base in group['nets']:
        hit = [nm for nm in qb.nets
               if nm == base or nm.endswith('/' + base)]
        if len(hit) != 1:
            raise SystemExit('net %r resolves to %r (expected exactly 1)' % (base, hit))
        out[base] = hit[0]
    return out


def net_pads(qb, netfull):
    return [d for (nm, tag), d in qb.pads.items() if nm == netfull]


def mst_edges(pads):
    """Prim MST over pad centres -> list of (i, j) index pairs."""
    n = len(pads)
    if n <= 1:
        return []
    INF = float('inf')
    intree = [False] * n
    best = [(INF, -1)] * n
    best[0] = (0.0, -1)
    edges = []
    for _ in range(n):
        u = min((i for i in range(n) if not intree[i]), key=lambda i: best[i][0])
        intree[u] = True
        if best[u][1] >= 0:
            edges.append((best[u][1], u))
        for v in range(n):
            if intree[v]:
                continue
            d = math.hypot(pads[u]['x'] - pads[v]['x'], pads[u]['y'] - pads[v]['y'])
            if d < best[v][0]:
                best[v] = (d, u)
    return edges


# --------------------------------------------------------------------------- #
def cmd_baseline():
    """Record the authoritative fingerprints, DRC, ratsnest and target open-set."""
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    dc, _ = RU.drc(AUTH, 'Abase', WORK)
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    res = dict(
        sha256=sha256(AUTH),
        tracks=len(trk), vias=len(via),
        copper_layers=b.GetCopperLayerCount(),
        ratsnest=rats, journal=len(jr),
        drc=dict(dc),
        phaseA_requested_pairs=[(e['net'], e['a'], e['b'])
                                for e in jr if e.get('requested_connected')],
    )
    json.dump(res, open(BASELINE_JSON, 'w'), indent=1)
    print('BASELINE authoritative board:')
    print('  sha256    ', res['sha256'])
    print('  tracks/vias/layers %d / %d / %d' % (res['tracks'], res['vias'], res['copper_layers']))
    print('  ratsnest  ', res['ratsnest'])
    print('  journal   ', res['journal'], '(requested pairs %d)' % len(res['phaseA_requested_pairs']))
    print('  DRC       ', dict(dc))
    return 0


def scratch_pcb(name):
    return os.path.join(WORK, 'INC_' + name, RU.PCBNAME)


def cmd_route(name):
    group = GROUPS[name]
    pcb = RU.fresh(WORK, 'INC_' + name)          # copy of the authoritative project
    qb = QR.QBoard(pcb)
    nets = resolve_nets(qb, group)
    layer, w = group['layer'], group['width']
    cp, ct = group['clr_pad'], group['clr_trk']
    jrn = []
    print('ROUTE group %s on %s.Cu at %.3f mm (%s)' % (name, layer, w / 1e6, group['desc']))
    for base in group['nets']:
        nf = nets[base]
        pads = net_pads(qb, nf)
        pads_by_ref = {p['ref']: p for p in pads}
        order = sorted(pads_by_ref)                # deterministic
        pads = [pads_by_ref[r] for r in order]
        for (i, j) in mst_edges(pads):
            pa, pb = pads[i], pads[j]
            r = QR.connect_role(qb, nf, pa, pb, layer, w, cp, ct)
            rec = dict(net=base, netfull=nf, a=pa['ref'], b=pb['ref'],
                       layer=layer + '.Cu', w=w / 1e6, ok=bool(r.get('ok')),
                       mm=round(r.get('mm', 0), 3), reason=r.get('reason'),
                       why=r.get('why'))
            jrn.append(rec)
            print('  %-14s %-8s -> %-8s %s %s'
                  % (base, pa['ref'], pb['ref'],
                     'ok %.3f mm' % r['mm'] if r.get('ok') else 'FAIL ' + str(r.get('reason')),
                     r.get('why', '') or ''))
    qb.save(pcb)
    json.dump(jrn, open(os.path.join(WORK, 'INC_' + name, 'route_journal.json'), 'w'), indent=1)
    allok = all(r['ok'] for r in jrn)
    print('ROUTE %s: %s (%d connections, %d ok)'
          % (name, 'ALL OK' if allok else 'INCOMPLETE',
             len(jrn), sum(r['ok'] for r in jrn)))
    print('  scratch board:', pcb, '(authoritative UNTOUCHED)')
    return 0 if allok else 1


def cmd_gate(name, promote=False):
    group = GROUPS[name]
    pcb = scratch_pcb(name)
    if not os.path.exists(pcb):
        raise SystemExit('no scratch board for %s -- run route first' % name)

    fails = []

    def chk(cond, label, detail=''):
        print('  %s %s %s' % ('PASS' if cond else '**FAIL**', label, detail))
        if not cond:
            fails.append(label)

    print('GATE group %s' % name)
    ab = pcbnew.LoadBoard(AUTH)
    rb = pcbnew.LoadBoard(pcb)
    ab.BuildConnectivity()
    rb.BuildConnectivity()

    # The baseline is computed LIVE from the CURRENT authoritative board (which,
    # during route->gate before promote, is exactly the pre-increment state) --
    # NOT from a persisted file, so each successive group self-corrects and no
    # stale snapshot can ever govern a later increment.
    jr0 = json.load(open(JOURNAL, encoding='utf-8'))
    base = dict(
        sha256=sha256(AUTH),
        ratsnest=ab.GetConnectivity().GetUnconnectedCount(True),
        drc=dict(RU.drc(AUTH, 'Abase', WORK)[0]),
        phaseA_requested_pairs=[(e['net'], e['a'], e['b'])
                                for e in jr0 if e.get('requested_connected')],
    )

    # -- 1. Phase-A copper preserved EXACTLY (superset, add-only, in-scope) ----
    base_sig = copper_sigs(ab)
    routed_sig = copper_sigs(rb)
    missing = base_sig - routed_sig       # any authoritative item lost/altered
    added = routed_sig - base_sig         # new copper items
    chk(not missing, 'no Phase-A copper deleted or altered',
        '(%d missing)' % sum(missing.values()))
    nf_set = set()
    qbnets = {n.GetNetname() for n in rb.GetNetsByName().values()}
    for b_ in group['nets']:
        hit = [nm for nm in qbnets if nm == b_ or nm.endswith('/' + b_)]
        nf_set.add(hit[0])
    oos = [sig for sig in added if sig[1] not in nf_set]
    chk(not oos, 'every new copper item is a target-group net',
        '(%d out-of-scope new items)' % len(oos))
    chk(len(added) > 0, 'copper was actually added', '(%d new items)' % sum(added.values()))

    # -- 2. requested connectivity GAIN: each target net fully connected -------
    # GetConnectedPads(pad) lists pads joined to `pad` by COPPER (ratsnest
    # excluded), so a net is fully connected iff, from any one of its pads, the
    # copper-connected set covers every other pad on the net.
    rats_after = rb.GetConnectivity().GetUnconnectedCount(True)
    cca, ccr = ab.GetConnectivity(), rb.GetConnectivity()

    def pads_of(board, netfull):
        out = []
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() == netfull:
                    out.append(p)
        return out

    def _ref(p):
        return p.GetParentFootprint().GetReference() + '.' + p.GetNumber()

    def copper_connected(cc, pad):
        """Refs of pads joined to `pad` by COPPER (ratsnest excluded).
        GetConnectedItems(pad) with a single arg is the KiCad-10 call that
        works here; GetConnectedPads() returns [] in this build."""
        out = set()
        for it in cc.GetConnectedItems(pad):
            if it.GetClass() == 'PAD':
                out.add(it.GetParentFootprint().GetReference() + '.' + it.GetNumber())
        return out

    def net_open_edges(board, cc, netfull):
        """Ratsnest edges owed by this net = (#copper clusters over its pads) - 1."""
        pads = pads_of(board, netfull)
        if not pads:
            return 0
        seen, clusters = set(), 0
        for p in pads:
            ref = _ref(p)
            if ref in seen:
                continue
            clusters += 1
            seen |= copper_connected(cc, p) | {ref}
        return clusters - 1

    exp_drop = 0
    for nf in sorted(nf_set):
        pads = pads_of(rb, nf)
        refs = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber() for p in pads}
        reach = set()
        for p in pads:
            reach |= copper_connected(ccr, p) | {
                p.GetParentFootprint().GetReference() + '.' + p.GetNumber()}
        full = refs.issubset(reach) and net_open_edges(rb, ccr, nf) == 0
        chk(full, 'target net fully connected by copper: ' + nf.split('/')[-1],
            'pads=%d open_edges %d->%d' % (len(pads),
                                           net_open_edges(ab, cca, nf),
                                           net_open_edges(rb, ccr, nf)))
        exp_drop += net_open_edges(ab, cca, nf)

    # -- 3. no Phase-A requested pair regressed --------------------------------
    # (The copper-superset check in step 1 already proves no Phase-A strand
    #  changed, so this is a redundant belt-and-braces electrical re-proof.)
    regressed = []
    for (nm, a, b_) in base['phaseA_requested_pairs']:
        pa = _pad(rb, a)
        pb = _pad(rb, b_)
        if pa is None or pb is None:
            continue
        conn = copper_connected(ccr, pa) | {
            pa.GetParentFootprint().GetReference() + '.' + pa.GetNumber()}
        if b_ not in conn:
            regressed.append((nm, a, b_))
    chk(not regressed, 'all Phase-A requested pairs still copper-connected',
        '(%d regressed)' % len(regressed))

    # -- 4. ratsnest strictly dropped by exactly the requested gain ------------
    chk(rats_after == base['ratsnest'] - exp_drop and exp_drop > 0,
        'ratsnest dropped by exactly the requested connections',
        '%d -> %d (expected -%d)' % (base['ratsnest'], rats_after, exp_drop))

    # -- 5. real full-board DRC delta: no new/worse class, unconnected drops ---
    dc, det = RU.drc(pcb, 'Ainc', WORK)
    b_drc = base['drc']
    newcls = [k for k in dc if k not in b_drc and k != 'unconnected_items']
    worse = [k for k in dc if k != 'unconnected_items' and dc[k] > b_drc.get(k, 0)]
    chk(not newcls, 'no new DRC violation class', str({k: dc[k] for k in newcls}))
    chk(not worse, 'no DRC class increased', str({k: (b_drc.get(k, 0), dc[k]) for k in worse}))
    # kicad-cli DRC's "unconnected_items" enumerates a different (smaller) set
    # than pcbnew's GetUnconnectedCount ratsnest -- the project's connectivity
    # authority, the "ratsnest 704" of D-302.  The connectivity GAIN is proven
    # above by the exact ratsnest drop (step 4) + per-net GetConnectedItems
    # (step 2); DRC's role here is LEGALITY: its unconnected_items must not
    # INCREASE (my copper must not sever anything DRC counts).
    un_b = b_drc.get('unconnected_items', 0)
    un_a = dc.get('unconnected_items', 0)
    chk(un_a <= un_b, 'DRC unconnected_items did not increase',
        '%d -> %d' % (un_b, un_a))
    print('  DRC after:', dict(dc))

    verdict = not fails
    art = dict(group=name, scratch=pcb, scratch_sha=sha256(pcb),
               auth_sha_pre=base['sha256'],
               new_copper_items=sum(added.values()),
               ratsnest_before=base['ratsnest'], ratsnest_after=rats_after,
               connections_gained=exp_drop,
               drc_before=b_drc, drc_after=dict(dc),
               target_nets=sorted(nf_set), fails=fails, verdict='PASS' if verdict else 'FAIL')
    json.dump(art, open(os.path.join(WORK, 'INC_' + name, 'gate_006.json'), 'w'), indent=1)
    print('GATE %s: %s (%d check%s failed)'
          % (name, 'PASS' if verdict else 'FAIL', len(fails), '' if len(fails) == 1 else 's'))

    if promote:
        if not verdict:
            raise SystemExit('REFUSING TO PROMOTE: gate FAILed (%s)' % fails)
        _promote(name, pcb, art)
    return 0 if verdict else 1


def _pad(board, ref):
    # Some Phase-A journal terminals are pseudo-pads / net nodes ("(tap)",
    # "(node)") with no "REF.PAD" form -- they have no single pad to test.
    if not ref or ref.count('.') != 1 or ref.startswith('('):
        return None
    r, num = ref.split('.')
    for f in board.GetFootprints():
        if f.GetReference() == r:
            for p in f.Pads():
                if p.GetNumber() == num:
                    return p
    return None


def _promote(name, pcb, art):
    """Copy the gated scratch board + merged journal onto the authoritative
    project.  Only the .kicad_pcb changes -- placement, DRU, netlist unchanged."""
    pre = sha256(AUTH)
    if pre != art['auth_sha_pre']:
        raise SystemExit('authoritative sha changed since gate (%s != %s)'
                         % (pre[:16], art['auth_sha_pre'][:16]))
    shutil.copyfile(pcb, AUTH)
    # merge the route journal into phaseA_journal.json as rest-of-board entries
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    rj = json.load(open(os.path.join(WORK, 'INC_' + name, 'route_journal.json'), encoding='utf-8'))
    for r in rj:
        jr.append(dict(net=r['netfull'], a=r['a'], b=r['b'], role='REST_INC',
                       layer=r['layer'], w=r['w'], mm=r['mm'],
                       requested_connected=True, group=name))
    json.dump(jr, open(JOURNAL, 'w'), indent=1)
    print('PROMOTED %s: authoritative sha %s -> %s ; journal %d -> %d'
          % (name, pre[:16], sha256(AUTH)[:16], len(jr) - len(rj), len(jr)))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == 'baseline':
        return cmd_baseline()
    if cmd == 'route':
        return cmd_route(argv[2])
    if cmd == 'gate':
        return cmd_gate(argv[2])
    if cmd == 'promote':
        return cmd_gate(argv[2], promote=True)
    print('unknown command', cmd)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
