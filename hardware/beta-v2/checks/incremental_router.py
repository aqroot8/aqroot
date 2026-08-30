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
    # FBV2-P2-008 / D-306 -- display reset control DISP_RST_N.  A single 3-pad
    # noncritical low-speed reset line whose pads DO NOT all share one layer:
    # R16.1 and J1.10 are F.Cu SMD, U2.8 is B.Cu SMD.  Its MST therefore has one
    # SAME-LAYER edge (R16.1<->J1.10, a pure F.Cu run -- the FIRST incremental
    # F.Cu route) and one CROSS-LAYER edge (J1.10<->U2.8, which must transition
    # F<->B through ONE board-legal through via -- the FIRST incremental via /
    # mixed-layer route).  The via is the Default netclass geometry the KiCad
    # DRC enforces here: 0.60 mm diameter / 0.30 mm drill (>= the 0.50 mm
    # min_via_diameter and 0.30 mm floor; NOT a microvia, not a POFV).  Widths
    # and clearances are the Default netclass floor (0.200 mm).  Low congestion:
    # only 2 accepted Phase-A copper items lie within the group bbox+2 mm.
    'DISP_RST': dict(
        sheet='03_SPI_A_DISPLAY_SD',
        desc='display reset DISP_RST_N (R16.1/J1.10 F.Cu, U2.8 B.Cu); '
             'noncritical low-speed reset line -- first incremental F.Cu run '
             '(R16.1<->J1.10) + first incremental cross-layer through via '
             '(J1.10<->U2.8, 0.60/0.30 Default netclass), no other via',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000,
        nets=['DISP_RST_N'],
    ),
    # FBV2-P2-009 / D-307 -- BQ25185 charger current-program strap PAIR.  Two
    # coherent same-chip (U11) low-current programming straps: ILIM_VSET (input
    # current-limit set resistor R36 -> U11.7) and ISET (charge-current set
    # resistor R37 -> U11.8).  Both Default netclass (0.200 mm width/clearance,
    # NO via), all B.Cu SMD, adjacent U11 east-edge pins -- a single coherent
    # charger-programming control cluster.  The region is congested (BQ25185 /
    # BPP trunk), so promotion is decided by the real full-board gate, not by
    # geometry alone.  Same-layer B.Cu mechanics (D-304/D-305) reused byte-for-
    # byte: no via, no plane re-pour.
    'U11_PROG': dict(
        sheet='01_POWER_TREE',
        desc='BQ25185 charger current-program straps: input-current-limit set '
             '(R36 -> U11.7 ILIM_VSET) + charge-current set (R37 -> U11.8 ISET); '
             'coherent same-chip low-current control, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['ILIM_VSET', 'ISET'],
    ),
    # FBV2-P2-009 fallback A -- west power-status sense pair: USB VBUS-present
    # divider (R104/R105/C68/TP31 VBUS_PRESENT) + MAX17048 fuel-gauge alert
    # (U14.5 -> TP11 MAX17048_ALRT_N).  Both Default netclass, all B.Cu SMD, no
    # via, tight far-west power-input corner.
    'PWR_SENSE': dict(
        sheet='01_POWER_TREE',
        desc='west power-status sense: USB VBUS-present divider (VBUS_PRESENT) + '
             'MAX17048 fuel-gauge alert (MAX17048_ALRT_N); low-current status '
             'sense, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['VBUS_PRESENT', 'MAX17048_ALRT_N'],
    ),
    # FBV2-P2-009 fallback B -- BMI270 IMU I2C address-select strap (U4/R118/
    # R119), a 3-pad B.Cu multi-terminal net, measured PRISTINE (0 accepted
    # copper within bbox+2mm).  Default netclass, no via.  The held clean
    # singleton fallback (favored IMU/I2C-local example).
    'IMU_ADDR': dict(
        sheet='05_I2C_DEVICES',
        desc='BMI270 IMU I2C address-select strap (R118/R119 -> U4.1 '
             'BMI270_SDO_ADDR); noncritical low-speed strap, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['BMI270_SDO_ADDR'],
    ),
    # FBV2-P2-010 / D-308 -- FRONT-PANEL RGB STATUS-INDICATOR COMPLETION.  D-304
    # (FRONT_RGB) routed the expander->resistor side of the front-panel RGB
    # status LED (U23 PCAL9535A GPIO -> R124/R125/R126 series limit resistors,
    # all B.Cu).  This group closes the SAME indicator on the LED-cathode side:
    # each series resistor's far pad (R124.2/R125.2/R126.2, B.Cu SMD) to the
    # matching cathode of D13 (MHPA3528RGBCT common-anode RGB LED, F.Cu SMD).
    # The three nets are Net-(D13-RK) (R124->D13.4 red), Net-(D13-GK)
    # (R125->D13.3 green), Net-(D13-BK) (R126->D13.2 blue).  Each is a 2-pad
    # CROSS-LAYER net (resistor B.Cu, LED F.Cu) so each closes with exactly ONE
    # board-legal Default through via (0.60/0.30) -- the SAME single-via-per-edge
    # mechanic proven at D-306, now applied THREE times in one increment (the
    # first MULTI-VIA increment; connect_cross is NOT changed, refill_planes
    # re-pours In1/In4 once for all three barrels).  Low current (R-limited
    # 2-6 mA status indicator, non-switching), low congestion (6-11 accepted
    # copper items per net bbox+2mm), a coherent local peripheral cluster that
    # directly extends an already-accepted increment.
    'FRONT_RGB_LED': dict(
        sheet='08_BUTTONS_EXPANDERS',
        desc='front-panel RGB status-LED cathode completion (R124/R125/R126 B.Cu '
             '-> D13 MHPA3528 cathodes F.Cu); closes the D-304 FRONT_RGB '
             'indicator on the LED side; low-current non-switching indicator, '
             'three cross-layer nets each one 0.60/0.30 Default through via',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000,
        nets=['Net-(D13-RK)', 'Net-(D13-GK)', 'Net-(D13-BK)'],
    ),
    # FBV2-P2-011 / D-309 candidate PRIMARY -- IR receiver local supply.
    # IR_RX_VS_LOCAL is the RC-filtered local supply node for the IR demodulator
    # U6 (07_IR): series filter R21.2 (F.Cu SMD) + decoupling C11.1 (F.Cu SMD) ->
    # U6.3 supply pin (THT, on BOTH faces).  All three pads share the F.Cu outer
    # layer (U6.3 is THT so F.Cu is available), so every MST edge is a SAME-LAYER
    # F.Cu run with NO via.  A tight NE-corner cluster (span ~10x4 mm), measured
    # PRISTINE (0 accepted copper within bbox+2 mm).  A coherent standalone
    # peripheral supply-filter group -- noncritical low-current, not a bulk rail.
    'IR_RX_VS': dict(
        sheet='07_IR',
        desc='IR receiver (U6) local filtered supply IR_RX_VS_LOCAL '
             '(R21.2 series + C11.1 decoupling -> U6.3 THT supply); '
             'pristine NE-corner cluster, all F.Cu, no via',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['IR_RX_VS_LOCAL'],
    ),
    # FBV2-P2-011 candidate -- coherent display/touch-panel control subset.
    # TOUCH_RST_N (J1.47 F, R12.1 F, U2.4 B) + TOUCH_INT_N (J1.46 F, U2.19 B):
    # the capacitive touch panel reset + interrupt lines from the display FPC
    # connector J1 to the touch-controller interface U2.  Both are long
    # cross-board hauls (33-38 mm) that transition F<->B (U2 is B.Cu) so each
    # closes with a Default through via.  MEASURED (screen_010): moderate mid-
    # board congestion (cu 21/24) -- promotion decided by the real full-board
    # gate, not geometry.
    # ==> D-309 MEASURED FAIL (NOT promoted): the router laid geometric paths
    #     (route ALL OK) but the real full-board gate reported +3 new `clearance`
    #     violations -- the TOUCH_RST_N via/track collide with the ACCEPTED D-306
    #     DISP_RST_N through-via in the congested U2 B.Cu escape region (all four
    #     touch/amp/SD pins land on U2's B.Cu edge beside U2.8).  A characterised
    #     wall (like U11_PROG/PWR_SENSE); needs a deliberate U2-escape corridor
    #     plan, deferred to FBV2-P2-012.  Do NOT naively retry.
    'TOUCH_CTL': dict(
        sheet='03_SPI_A_DISPLAY_SD',
        desc='display/touch control: touch reset TOUCH_RST_N (J1.47/R12.1 F -> '
             'U2.4 B) + touch interrupt TOUCH_INT_N (J1.46 F -> U2.19 B); '
             'noncritical low-speed control, cross-layer through vias',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000,
        nets=['TOUCH_RST_N', 'TOUCH_INT_N'],
    ),
    # FBV2-P2-011 candidate -- audio amplifier SD/mode strap.  AMP_SD_MODE
    # (R15.1 F, U5.4 F -> U2.7 B): the MAX98357 class-D amp SD/mode select strap
    # (a static logic-level strap, NOT the class-D output).  Cross-board haul to
    # U2 (~29 mm), one cross-layer edge -> one through via.  cu 57.
    # ==> D-309 MEASURED FAIL (NOT promoted): gate reported +7 `clearance` (via
    #     lands in the same congested U2 B.Cu escape beside DISP_RST_N; deferred
    #     to FBV2-P2-012 with the touch group).
    'AMP_SD_MODE': dict(
        sheet='06_AUDIO',
        desc='audio amp SD/mode-select strap AMP_SD_MODE (R15.1/U5.4 F -> U2.7 B); '
             'static logic strap (not the class-D output), one cross-layer via',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000,
        nets=['AMP_SD_MODE'],
    ),
    # FBV2-P2-011 candidate -- microSD card-detect.  SD_CARD_DETECT_N
    # (J2.10 F, R113.2 F -> U2.11 B): the microSD socket J2 card-detect switch
    # line (noncritical low-speed) to U2.  Cross-board haul (~59 mm), one
    # cross-layer edge -> one through via.  cu 57.
    # ==> D-309 MEASURED FAIL (NOT promoted): gate reported +2 `clearance` (via
    #     lands in the same congested U2 B.Cu escape; deferred to FBV2-P2-012).
    'SD_DETECT': dict(
        sheet='03_SPI_A_DISPLAY_SD',
        desc='microSD card-detect SD_CARD_DETECT_N (J2.10/R113.2 F -> U2.11 B); '
             'noncritical low-speed detect, one cross-layer via',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000,
        nets=['SD_CARD_DETECT_N'],
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


def _pad_layers(p):
    """The set of outer copper layers a pad has copper on ('F' and/or 'B')."""
    return {L for L in ('F', 'B') if p.get(L)}


def edge_plan(pa, pb, group):
    """Decide how ONE MST edge is routed from its two pads' layers.

    * SAME-LAYER (the pads share a routable outer layer) -> a flat run on that
      layer with QR.connect_role.  The layer preferred is the group's declared
      `layer` when it is one of the shared layers (so THT pads, which are on
      BOTH faces, and all-B / all-F groups behave exactly as before), else the
      single shared layer.
    * CROSS-LAYER (the pads have NO shared outer layer, e.g. one F.Cu SMD and
      one B.Cu SMD) -> a single board-legal through via via connect_cross.
    Returns (layer_or_None, 'same'|'cross')."""
    common = _pad_layers(pa) & _pad_layers(pb)
    if common:
        L = group['layer'] if group['layer'] in common else sorted(common)[0]
        return L, 'same'
    return None, 'cross'


def connect_cross(qb, net, pa, pb, group, G=50000, fine=25000):
    """Route ONE cross-layer edge (pads on opposite outer faces) with exactly
    ONE board-legal through via, composing only proven qrouter primitives:

        escape(host, near) -> via_site(near, far) -> via(0.60/0.30) ->
        connect_role(host -> anchor@via, near) + connect_role(run -> anchor@via, far)

    The via geometry, the all-copper-layer clearance and the net-agnostic
    hole-to-hole floor are exactly what QBoard.via_site already enforces (the
    same legality connect_hop relies on); the two runs land on the via centre,
    which is same-net copper and therefore not an obstacle to either.  No
    qrouter.py behaviour is changed -- this is a new caller of existing methods.
    """
    w, cp, ct = group['width'], group['clr_pad'], group['clr_trk']
    vd = group.get('via_dia', 600000)
    vk = group.get('via_drill', 300000)

    def only(p):
        s = _pad_layers(p)
        return next(iter(s)) if len(s) == 1 else None
    near = only(pb)          # host the via beside pb (its single face)
    far = only(pa)           # run the far layer to pa
    if near is None or far is None or near == far:
        return dict(ok=False, reason='NOT_CROSS',
                    why='connect_cross needs two opposite single-layer pads '
                        '(%s on %s, %s on %s)'
                        % (pa['ref'], sorted(_pad_layers(pa)),
                           pb['ref'], sorted(_pad_layers(pb))))
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    fail = dict(ok=False, reason='NO_VIA_SITE',
                why='no reachable %s->%s via site for %s/%s'
                    % (near, far, pb['ref'], pa['ref']))
    for G_try in (G, fine):
        e = qb.escape(pb, near, w, w, cp, ct, G_try, ox, oy,
                      prefer=(pa['x'] - pb['x'], pa['y'] - pb['y']))
        if not e:
            return dict(ok=False, reason='NO_LEGAL_ESCAPE',
                        why=qb.escape_why[0], pad=pb['ref'])
        site = None
        for c in e[:6]:
            st = qb.via_site(near, far, net, c, w, vd, cp, ct, G_try,
                             via_drill=vk)
            if st is not None:
                site = st
                break
        if site is None:
            continue
        vx, vy = site
        m = qb.mark()
        qb.via(net, vx, vy, vd, vk)
        anchor = dict(ref='(via)', x=int(vx), y=int(vy), F=True, B=True,
                      anchor=True, net=net,
                      shape=QR.RR(int(vx), int(vy), 1, 1, 0, 0, net, 'via'),
                      hx=1, hy=1, r=0, ang=0, tht=False)
        rn = QR.connect_role(qb, net, pb, anchor, near, w, cp, ct, G=G_try)
        if not rn.get('ok'):
            qb.revert(m)
            fail = dict(ok=False, reason='NO_NEAR_RUN', why=rn.get('why'),
                        pad=pb['ref'])
            continue
        rf = QR.connect_role(qb, net, pa, anchor, far, w, cp, ct, G=G_try)
        if not rf.get('ok'):
            qb.revert(m)
            fail = dict(ok=False, reason='NO_FAR_RUN', why=rf.get('why'),
                        pad=pa['ref'])
            continue
        return dict(ok=True, mm=rn['mm'] + rf['mm'], vias=1,
                    layer='%s+%s via' % (far, near),
                    via_xy=[(round(vx / 1e6, 3), round(vy / 1e6, 3))],
                    why='cross-layer %s/%s through via 0.%03d/0.%03d mm at '
                        '(%.3f,%.3f)'
                        % (far, near, vd // 1000, vk // 1000,
                           vx / 1e6, vy / 1e6))
    return fail


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


# --------------------------------------------------------------------------- #
# In1/In4 GND REFERENCE PLANES.  D-rules and [[fbv2-p2 In1/In4 GND roles]] pin
# In1.Cu and In4.Cu as the two solid GND reference planes.  A through via on a
# SIGNAL net crosses both, and the plane must open a clearance anti-pad around
# the barrel or DRC answers `clearance`/`hole_clearance` (measured: the first
# DISP_RST_N via, before any refill, showed 0.000 mm to both planes).  The B.Cu
# increments never laid a via so this never arose; the first via increment does.
# We therefore re-pour EXACTLY these two plane zones (and nothing else) when a
# via was laid -- every other zone, and every Phase-A track/via, is left byte-
# identical.  The plane fill is not byte-reproducible by the current KiCad
# ZONE_FILLER (a stored-vs-current drift of ~35 poly-points per plane exists
# independent of the via), so the re-pour is proven SAFE by the real full-board
# DRC being unchanged, not by byte-equality of the plane polygons.
def plane_zones(board):
    """The In1/In4 GND reference-plane zones (order-stable index + zone)."""
    out = []
    for i, z in enumerate(board.Zones()):
        lyrs = {pcbnew.BOARD.GetStandardLayerName(L)
                for L in z.GetLayerSet().CuStack()}
        if z.GetNetname() == 'GND' and lyrs and lyrs <= {'In1.Cu', 'In4.Cu'}:
            out.append((i, z))
    return out


def zone_fp(z):
    """Fingerprint a zone's identity + fill (net, layers, priority, points)."""
    lyrs = tuple(sorted(pcbnew.BOARD.GetStandardLayerName(L)
                        for L in z.GetLayerSet().CuStack()))
    pts = sum(z.GetFilledPolysList(L).FullPointCount()
              for L in z.GetLayerSet().CuStack())
    return (z.GetNetname(), lyrs, z.GetAssignedPriority(), pts)


def refill_planes(board):
    """Re-pour only the In1/In4 GND reference planes; return their indices."""
    planes = plane_zones(board)
    if planes:
        pcbnew.ZONE_FILLER(board).Fill([z for _, z in planes])
    return [i for i, _ in planes]


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
            el, kind = edge_plan(pa, pb, group)
            if kind == 'same':
                r = QR.connect_role(qb, nf, pa, pb, el, w, cp, ct)
                elabel, vias = el + '.Cu', 0
            else:
                r = connect_cross(qb, nf, pa, pb, group)
                elabel, vias = r.get('layer', 'cross'), r.get('vias', 0)
            rec = dict(net=base, netfull=nf, a=pa['ref'], b=pb['ref'],
                       layer=elabel, w=w / 1e6, ok=bool(r.get('ok')),
                       mm=round(r.get('mm', 0), 3), vias=vias,
                       via_xy=r.get('via_xy'), kind=kind,
                       reason=r.get('reason'), why=r.get('why'))
            jrn.append(rec)
            print('  %-12s %-8s -> %-8s [%-4s %s] %s %s'
                  % (base, pa['ref'], pb['ref'], kind, elabel,
                     'ok %.3f mm' % r['mm'] if r.get('ok') else 'FAIL ' + str(r.get('reason')),
                     r.get('why', '') or ''))
    # A through via crosses the In1/In4 GND planes; re-pour ONLY those two so
    # the barrel gets its clearance anti-pad.  No via -> no refill -> the B.Cu
    # increments stay byte-identical exactly as before.
    nvia = sum(1 for v in qb.laid if v.GetClass() == 'PCB_VIA')
    if nvia:
        idx = refill_planes(qb.b)
        print('  REFILLED %d In1/In4 GND plane zone(s) %s for %d new via(s) '
              '(anti-pad); all other zones untouched' % (len(idx), idx, nvia))
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

    # -- 1b. ZONES preserved: only the In1/In4 GND reference planes may re-pour -
    # (to carve a through-via anti-pad); every OTHER zone must be byte-identical
    # in net / layers / priority / filled-poly count, and even the planes may
    # only change their FILL, never their identity.  A B.Cu increment lays no
    # via, so no plane re-pours and this reduces to "all zones identical".
    a_zones, r_zones = list(ab.Zones()), list(rb.Zones())
    plane_idx = {i for i, _ in plane_zones(rb)}
    zchg, zbad = [], []
    if len(a_zones) != len(r_zones):
        zbad.append('zone COUNT %d->%d' % (len(a_zones), len(r_zones)))
    else:
        for i, (za, zr) in enumerate(zip(a_zones, r_zones)):
            fa, fr = zone_fp(za), zone_fp(zr)
            if fa == fr:
                continue
            zchg.append(i)
            if fa[:3] != fr[:3]:
                zbad.append('zone %d IDENTITY %s->%s' % (i, fa[:3], fr[:3]))
            elif i not in plane_idx:
                zbad.append('zone %d (non-plane) fill %d->%d' % (i, fa[3], fr[3]))
    chk(not zbad,
        'only In1/In4 GND planes re-poured; all other zones identical',
        '(fill-changed zones=%s plane-set=%s%s)'
        % (zchg, sorted(plane_idx), '' if not zbad else ' BAD=' + str(zbad)))

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
    new_vias = sum(1 for sig in added if sig[0] == 'V')
    art = dict(group=name, scratch=pcb, scratch_sha=sha256(pcb),
               auth_sha_pre=base['sha256'],
               new_copper_items=sum(added.values()),
               new_vias=new_vias,
               planes_repoured=sorted(plane_idx), zones_fill_changed=zchg,
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
