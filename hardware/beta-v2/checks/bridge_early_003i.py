# -*- coding: utf-8 -*-
"""FBV2-P2-003I / D-275 -- the EARLY (route-order) driver stage of the western-
corridor F.Cu via-array bridge for BAT_PROTECTED_P.

003D integrated the exact D-275 mechanism as an END-OF-RUN stage
(bridge_eco_003d.apply_eco).  003I's preflight MEASURED that stage to be a via-
density FAIL: on the completed production board the tight western corridor
R75.2 -> D9.1 carries 15 through-vias (vs 11 on the proven-sparse c3 board), and
with the D-269 0.30 mm trunk clearance respected on those vias the >= 1.20 mm
via-aware traverse has NO_PATH to every BAT_PROTECTED_P landing.  The copper-only
traverse still PATHs, so the wall is via density, not copper -- the D-275 vacate
premise is intact, but the "proven timing" (bridge as a post-process of a sparse
board) does not transfer to the dense END of a full run.

This module lays the SAME proven mechanism EARLY instead: after the D-266 Kelvin
reservation and the U18 pin field have claimed their sites (the proven-sparse
configuration: the c3bridge003c board carries both the 0d reserve via at
(2.80,69.10) AND the 4 R75.2 entry-array vias), but BEFORE the LTC_GATE / BAT_RAW
tap stages inject the two BAT_RAW vias (~x7.2-7.4) and the LTC_GATE via (8.0,74.7)
that choke the corridor.  Subsequent routing then sees the real bridge copper as
an immutable, net-transparent obstacle and routes around it.

DIFFERENCES from apply_eco, and WHY they preserve the D-275 invariant exactly:

 1. LANDING ON A PAD, NOT ROUTED TRACK.  At the early point the eastern node
    track copper (nearest_on_net aim (42.4,76.4)) does not exist yet -- only the
    D9.1 west-cluster PAD (present from board load; D9.1 IS a named destination
    BAT_PROTECTED_P component).  The exit array therefore lands on the D9.1 pad
    copper directly (B.Cu stub from each exit via to the pad centre), which is
    electrically part of the correct net and is later joined onward to the node /
    U11.2 by the ordinary trunk + cap-tap + u11_escape stages.  No proxy, no
    reservation, no floating copper: the array ties to a real component pad.

 2. LIVE-QBOARD, PHANTOM-RESTORED.  apply_eco reloads the board and runs at end
    of the route, so BR.inject_vias' phantom via-obstacles are harmless.  Here we
    operate on the driver's LIVE qb mid-run, so we inject the phantoms for the
    D-269-aware traverse search, lay the bridge, then REMOVE exactly those
    phantoms again -- restoring the driver's normal via-blind obstacle model for
    every net that routes AFTER the bridge.  The real bridge tracks/vias stay in
    qb.shapes (net==BAT_PROTECTED_P, so transparent to their own net and an
    obstacle to every other) -- that is the "route around it" behaviour.

Everything else -- the cardinality-1 SHDN vacate, the 4x 0.80/0.40 entry array on
R75.2 (POFV), the >= 1.20 mm F.Cu traverse, the 4x exit array (array landing, no
single via carries pack current), the >= 3 fault-tolerant floor -- is imported
VERBATIM from bridge_route_003c (single source of truth), identical to apply_eco.
"""
import os
import pcbnew
import bridge_route_003c as BR

NET, SHDN = BR.NET, BR.SHDN
DIA, DRILL = BR.DIA, BR.DRILL
CP, CTW = BR.CP, BR.CTW
W_TRAVERSE, W_LAND = BR.W_TRAVERSE, BR.W_LAND
# west-cluster BAT_PROTECTED_P pads, present from board load, tried in order; the
# stage keeps the first that yields a full >= 1.20 mm traverse + >= 3 exit array.
# D9.1 is the trunk staging node (the D-267 reservation destination); C58.1 is the
# co-located decoupling cap.  Both are named production BAT_PROTECTED_P components
# and both are later joined onward to the mid-node / U11.2 by the ordinary stages.
LAND_REFS = ['D9.1', 'C58.1']
LAND_REF = LAND_REFS[0]

# FBV2-P2-003K / D-282 candidate (c): the DISJOINT-SUB-BOX southern bridge.  003J
# (D-282) measured that the shared western corridor (y 65-75) cannot host BOTH the
# >= 1.20 mm bridge AND the LTC_GATE / BAT_RAW taps -- the taps sit at y < 74.7 and
# the only spare >= 1.20 mm F.Cu lane is a SOUTHERN band, y > 75, DISJOINT from the
# tap cluster.  The south variant forces the western leg of the traverse BELOW the
# tap band with a temporary net-foreign obstacle wall over the corridor-north box,
# so the bridge occupies y > 74.7 in the west and the taps + GND / BAT_MAIN keep the
# corridor (y < 74.7).  The only target-island BPP pad reachable forced-south early
# is the far-east node cap C36.1 -- no target-island pad exists between D9.1 (x=11)
# and C25/C36 (x=62), so the exit array lands there and the ordinary trunk / cap
# stages join it onward.  Everything else -- the cardinality-1 SHDN vacate, the 4x
# entry array on R75.2, the >= 1.20 mm F.Cu traverse rule, the 4x exit array, the
# >= 3 fault-tolerant floor -- is the SAME proven D-275 mechanism, single-sourced
# VERBATIM from bridge_route_003c, identical to the corridor early stage.
LAND_REFS_SOUTH = ['C36.1', 'U11.2', 'C25.1']
SOUTH_WALL_NET = BR.N + '__SOUTH_BRIDGE_WALL'   # foreign net: shapes ONLY the search
SOUTH_WALL_X0, SOUTH_WALL_X1 = 4600000, 30000000   # west of the taps (x>=5.75) .. mid
SOUTH_WALL_Y0, SOUTH_WALL_Y1 = 55000000, 74700000  # corridor-north, above the y<74.7 taps
SOUTH_WALL_STEP = 300000


def _south_wall(qb):
    """Inject a TEMPORARY net-foreign obstacle over the corridor-north box so the
    F.Cu traverse search is forced BELOW the tap band (y > 74.7) in the western
    region -- the disjoint-sub-box discipline (taps y < 74.7, bridge y > 75).  The
    wall is a foreign net so it clears the bridge's own copper by margin(); it is
    removed by the caller's `finally` exactly like the injected via phantoms, so it
    never obstructs any REAL net -- it shapes only the bridge's own search.  Returns
    the number of SEGs appended PER copper layer."""
    per_layer = 0
    y = SOUTH_WALL_Y0
    while y < SOUTH_WALL_Y1:
        x = SOUTH_WALL_X0
        while x < SOUTH_WALL_X1:
            for L in qb.cu:
                qb.shapes[L].append(BR.QR.SEG(x, y, x + SOUTH_WALL_STEP, y, 150000,
                                              SOUTH_WALL_NET, 'south-wall'))
            per_layer += 1
            x += SOUTH_WALL_STEP
        y += SOUTH_WALL_STEP
    qb._obs_cache = None
    return per_layer


def _west_maxy(qb):
    """Deepest (max-y) F.Cu BAT_PROTECTED_P point in the western band (x < 30 mm) --
    evidence that the south bridge dips below the tap band into the y > 75 lane."""
    ym = 0
    for t in qb.b.GetTracks():
        if (t.GetClass() == 'PCB_TRACK' and t.GetNetname() == NET
                and t.GetLayer() == pcbnew.F_Cu):
            for p in (t.GetStart(), t.GetEnd()):
                if p.x < 30000000 and p.y > ym:
                    ym = p.y
    return round(ym / 1e6, 2)


def _vacate_live(qb):
    """Cardinality-1 vacate on the LIVE board: move any BAT_PROT_SHDN_CTL F.Cu
    track to In3.Cu.  Early in the run the SHDN control branch is usually not yet
    routed (0 tracks) -- the corridor F.Cu is simply clear -- and the bridge
    copper then stands as an obstacle so the later SHDN route stays off the
    corridor F.Cu.  When SHDN F.Cu already exists it is vacated exactly as D-275
    specifies.  Returns count moved."""
    moved = 0
    for t in qb.b.GetTracks():
        if (t.GetClass() == 'PCB_TRACK' and t.GetNetname() == SHDN
                and t.GetLayer() == pcbnew.F_Cu):
            t.SetLayer(pcbnew.In3_Cu)
            moved += 1
    return moved


def _lay_landing(qb, entry_bus, exit_centroid, npx, npy):
    """Traverse from entry_bus to exit_centroid then lay the exit array around the
    pad (npx,npy).  Returns (ok, dict) with traverse metrics and exit count.  The
    caller marks/reverts qb around this so a partial attempt leaves no copper."""
    wtrav = None
    for w in (1500000, 1400000, 1300000, 1200000):
        ok, mm, npts = BR.route_traverse(qb, entry_bus[0], entry_bus[1],
                                         exit_centroid[0], exit_centroid[1], w)
        if ok:
            wtrav = w
            break
    if wtrav is None:
        return False, dict(traverse=dict(ok=False),
                           fail='no >= 1.20 mm F.Cu traverse corridor')
    exit_sites = [(npx - 450000, npy - 1350000), (npx + 450000, npy - 1350000),
                  (npx - 450000, npy - 450000), (npx + 450000, npy - 450000)]
    laid = 0
    for (x, y) in exit_sites:
        free = all(qb.point_free(L, NET, x, y, DIA, CP, CTW, 25000) for L in qb.cu)
        if not free or not BR.hole_clear(qb, x, y):
            continue
        qb.via(NET, x, y, DIA, DRILL)
        qb.track(NET, 'F', exit_centroid[0], exit_centroid[1], x, y, W_LAND)
        qb.track(NET, 'B', x, y, npx, npy, W_LAND)
        laid += 1
    d = dict(traverse=dict(ok=True, mm=round(mm, 3), w_mm=wtrav / 1e6, pts=npts),
             exit_vias=laid)
    if laid < 3:
        d['fail'] = 'exit array below floor 3 (%d landed)' % laid
        return False, d
    return True, d


def apply_early(qb, pads, land_refs=None, south=False):
    """Lay the exact D-275 bridge on the driver's LIVE qb, landing the exit array
    on the first `land_refs` pad that yields a full traverse + >= 3 exit array.
    `pads` is the driver's {net: {ref: pad}} map.  Returns a rec dict; rec['ok']
    is True iff the full bridge (entry array >= 3, >= 1.20 mm traverse, exit array
    >= 3) laid.  The driver's via-blind obstacle model is restored before return
    whether or not the bridge succeeded.

    `south` (FBV2-P2-003K / D-282 candidate c): force the western leg BELOW the tap
    band (y > 74.7) with a temporary obstacle wall and land on the far-east node cap
    (LAND_REFS_SOUTH) -- the disjoint-sub-box variant.  Default False reproduces the
    003I corridor bridge byte-for-byte (same land_refs, no wall)."""
    if land_refs is None:
        land_refs = LAND_REFS_SOUTH if south else LAND_REFS
    rec = {'stage': 'FBV2-P2-003%s bridge' % ('K south' if south else 'I early'),
           'ok': False, 'south': bool(south)}

    # ---- VACATE (cardinality 1) ------------------------------------------
    rec['vacated'] = _vacate_live(qb)

    # ---- inject existing vias as D-269 traverse obstacles, remembering the
    # phantom block so it can be removed again (LIVE qb must stay via-blind for
    # every net that routes after the bridge).  `south` adds a temporary wall over
    # the corridor-north box, removed with the same phantom block. -----------
    pre_sh = dict((L, len(qb.shapes[L])) for L in qb.cu)
    pre_h = len(qb.holes)
    nvia = BR.inject_vias(qb)
    rec['existing_vias'] = nvia
    nwall = _south_wall(qb) if south else 0
    try:
        # ---- ENTRY ARRAY on R75.2 (POFV) ---------------------------------
        # The entry vias are genuine POFV sites INSIDE R75.2's B.Cu pad (D-288
        # scan_entry_sites fix).  Each via is tied on TWO layers: the F.Cu bus
        # unites the via tops into the trunk, and an explicit B.Cu tie-stub from
        # each via to R75.2's pad CENTRE joins the via bottom to the pad copper --
        # the exact symmetric mirror of the exit array's _lay_landing B.Cu stub
        # (qb.track(NET,'B',...)).  Without that B.Cu tie the entry array dangled
        # on one layer (D-287); with it every entry via is >= 2-layer connected.
        r75 = pads.get(NET, {}).get('R75.2')
        rpx, rpy = int(r75['x']), int(r75['y'])
        entry_vias = BR.scan_entry_sites(qb)
        if len(entry_vias) < 3:
            rec['fail'] = 'entry array below floor 3 (%d sites)' % len(entry_vias)
            return rec
        for (x, y) in entry_vias:
            qb.via(NET, x, y, DIA, DRILL)
            if (x, y) != (rpx, rpy):
                qb.track(NET, 'B', x, y, rpx, rpy, W_LAND)
        ex = sorted(x for x, y in entry_vias)
        ey0 = int(sum(y for x, y in entry_vias) / len(entry_vias))
        qb.track(NET, 'F', ex[0], ey0, ex[-1], ey0, W_TRAVERSE)
        entry_bus = (ex[-1], ey0)
        rec['entry_vias'] = [[round(x / 1e6, 3), round(y / 1e6, 3)]
                             for x, y in entry_vias]

        # ---- LANDING: first reachable west-cluster pad (present from load) -
        m_land = qb.mark()
        tried = []
        for ref in land_refs:
            pad = pads.get(NET, {}).get(ref)
            if pad is None:
                tried.append((ref, 'absent'))
                continue
            npx, npy = int(pad['x']), int(pad['y'])
            ok, d = _lay_landing(qb, entry_bus, (npx, npy - 900000), npx, npy)
            if ok:
                rec['land'] = ref
                rec['landing'] = [round(npx / 1e6, 3), round(npy / 1e6, 3)]
                rec.update(d)
                if south:
                    rec['south_ywest_mm'] = _west_maxy(qb)
                rec['ok'] = True
                return rec
            tried.append((ref, d.get('fail')))
            qb.revert(m_land)
        rec['fail'] = 'no landing laid: %s' % tried
        rec['tried'] = tried
        return rec
    finally:
        # remove ONLY the injected phantoms (existing-via obstacles + the south
        # wall); the real bridge tracks/vias (appended after) stay as obstacles for
        # other nets.  Vias and wall are one contiguous block; holes are via-only.
        for L in qb.cu:
            del qb.shapes[L][pre_sh[L]:pre_sh[L] + nvia + nwall]
        del qb.holes[pre_h:pre_h + nvia]
        qb._obs_cache = None


def apply_early_path(pcb, land_refs=None, fill=True, south=False):
    """Standalone driver-free entry point: build a QBoard on `pcb`, lay the early
    bridge, fill zones and save.  For preflight tests on a reconstructed placed /
    sparse board.  Returns the rec dict."""
    import qrouter as QR
    qb = QR.QBoard(pcb)
    qb.wide_nets = frozenset(BR.N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                                'BAT_MID', 'BAT_SENSE',
                                                'BAT_PROTECTED_P'))
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(net, {})[ref] = p
    rec = apply_early(qb, pads, land_refs, south=south)
    if rec.get('ok') and fill:
        pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
        qb.save()
    rec['board'] = pcb
    return rec


def reconstruct_placed(dst_tag, place_json='c3_00.json'):
    """Rebuild the driver's PLACED, PRE-ROUTE board (six-layer + the `place_json`
    candidate placement) exactly as route_battery_block.main() lines 262-333 do,
    without routing a single net -- the sparsest corridor state, the upper bound on
    the early-bridge window.  Single source for the 003I preflight's placed board,
    used by the probe.  Returns the pcb path."""
    import os, json
    import route_battery_block as RB
    import path_role_util as RU
    import path_role_dru as DRU
    import sixlayer as SIX
    import place_p2_002f as ECO
    SPc = os.path.dirname(os.path.abspath(__file__))
    pcb = RU.fresh(RB.WORK, dst_tag)
    SIX.convert(pcb)
    ECO.apply(pcb, report=False)
    spec = json.load(open(os.path.join(SPc, 'place_002z', place_json)))
    bb = pcbnew.LoadBoard(pcb)
    fp = {f.GetReference(): f for f in bb.GetFootprints()}
    for r, v in spec.get('moves', {}).items():
        f = fp[r]
        if len(v) > 3 and bb.GetLayerName(f.GetLayer()) != v[3]:
            f.Flip(f.GetPosition(), False)
        f.SetPosition(pcbnew.VECTOR2I(int(round(v[0] * 1e6)), int(round(v[1] * 1e6))))
        f.SetOrientationDegrees(v[2])
    bb.BuildConnectivity()
    pcbnew.ZONE_FILLER(bb).Fill(bb.Zones())
    bb.Save(pcb)
    b = pcbnew.LoadBoard(pcb)
    for a in RB.AREAS + RB.STUBAREAS + RB.FINEAREAS:
        RU.add_named_area(b, a, 0, 0, 1000, 1000)
    b.Save(pcb)
    DRU.write(pcb, [])
    return pcb


if __name__ == '__main__':
    import sys, json
    b = sys.argv[1]
    args = sys.argv[2:]
    south = 'south' in args
    lands = [a for a in args if a != 'south'] or None
    r = apply_early_path(b, lands, south=south)
    print(json.dumps(r, indent=1))
    raise SystemExit(0 if r.get('ok') else 1)
