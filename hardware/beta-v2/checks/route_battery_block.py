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
         'BAT_SENSE_KELVIN', 'BAT_RAW_TAP_U18',
         ] + list(DRU.TAP_CLEARANCE_AREAS)
STUBAREAS = ['BAT_STUB_%d' % k for k in range(10)]
# PR-48 / D-257: each PLANNED fine-pitch escape gets its own bounded corridor,
# so the local 0.20 mm clearance and the 0.35/0.20 (reserve 0.25/0.15) via
# geometry reach exactly one net inside exactly one escape and nothing else.
FINEAREAS = ['FINE_ESC_%d' % k for k in range(16)]
FLOOR = {N + 'BAT_CONNECTOR_P': 600000, N + 'BAT_RAW': 600000,
         N + 'BAT_MID': 600000, N + 'BAT_SENSE': 600000,
         N + 'BAT_PROTECTED_P': 1200000}

# D-256.  AQROOT_D256 names one of battery_route_plan.D256_SETS; the listed
# connections take their PLANNED F.Cu hop first instead of last.  Unset means
# the pre-D-256 behaviour exactly, so every earlier measurement is reproducible.
# PR-47 / D-258: AQROOT_Q3_POFV routes Q3_CS off the contested south row
# through a filled/capped ordinary THROUGH via-in-pad on Q3.3 and an internal
# signal layer, leaving the B.Cu slot to the gate drive.  Unset reproduces the
# pre-002M behaviour exactly.
Q3_POFV = bool(os.environ.get('AQROOT_Q3_POFV'))

# FBV2-P2-002Q section 9: route the two R75 Kelvin taps BEFORE the trunk, so
# the 1.50 mm copper cannot take the lane a measurement branch needs.  Unset
# reproduces the pre-002Q ordering exactly.
KELVIN_FIRST = bool(os.environ.get('AQROOT_KELVIN_FIRST'))

# D-263 section 14: route both Kelvin branches on the same internal signal
# layer with ordinary 0.35/0.20 through vias.  AQROOT_KELVIN_INNER names the
# layer ('I2' or 'I3'); unset leaves the pair on its pre-002R topology.
KELVIN_INNER = (os.environ.get('AQROOT_KELVIN_INNER') or '').upper()

# D-263 section 10: the high-current trunk adapts to already-proven control
# geometry instead of erasing the pin-field exits, so it is queued AFTER the
# U18 field, the Q3 row, the trip network, the Kelvin pair and BAT_SENSE.
TRUNK_LAST = bool(os.environ.get('AQROOT_TRUNK_LAST'))

# FBV2-P2-003I / D-275: EARLY (route-order) western-corridor bridge.  When set,
# the exact proven D-275 mechanism is laid mid-run, at the first stage-8 queue
# item (after the D-266 Kelvin reservation + U18 field claim their sites, before
# the LTC_GATE / BAT_RAW tap stages choke the tight R75.2->D9.1 corridor), instead
# of at end-of-run.  The 003I preflight measured the end-of-run bridge to be a
# via-density FAIL (15 corridor vias -> NO_PATH); the early stage lays it while
# the corridor is still sparse and lets subsequent routing route around it.  When
# AQROOT_BRIDGE_EARLY is set the AQROOT_BRIDGE_ECO end-of-run duplicate is
# disabled so the bridge is laid exactly once.
EARLY_BRIDGE = bool(os.environ.get('AQROOT_BRIDGE_EARLY'))

# FBV2-P2-003K / D-282 candidate (c): the DISJOINT-SUB-BOX southern bridge.  When
# AQROOT_BRIDGE_SOUTH is set the EARLY stage lays the SAME proven D-275 mechanism
# but forces the western leg of the traverse below the tap band (y > 74.7) so the
# bridge owns the spare SOUTHERN lane (y > 75) and the LTC_GATE / BAT_RAW taps +
# GND / BAT_MAIN keep the corridor (y < 74.7) -- the disjoint sub-box 003J
# localised.  It IMPLIES the early stage (the bridge is still laid exactly once, at
# the stage-8 boundary); default-inert, no effect unless the gate is set.
SOUTH_BRIDGE = bool(os.environ.get('AQROOT_BRIDGE_SOUTH'))
if SOUTH_BRIDGE:
    EARLY_BRIDGE = True

# FBV2-P2-002S sections 8-11: an EXPLICIT U18 pin-field schedule, replacing
# the measured slack ordering for that group only.
#
# `order_tight` picks whichever pin is locally tightest right now, which is the
# right heuristic when nothing better is known - and 002S knows better.  A
# bounded screen over twelve schedules found that almost every order keeps all
# six functional pins AND all seven functional nets whole, while one ('outer
# pins first') loses LTC_OV: the difference is real and the heuristic cannot
# see it, because tightness at the moment of choosing says nothing about what
# the choice costs three pins later.  AQROOT_U18_ORDER names the sequence;
# unset leaves the measured ordering exactly as it was.
U18_ORDER = [s.strip() for s in
             (os.environ.get('AQROOT_U18_ORDER') or '').split(',') if s.strip()]

# FBV2-P2-002O section 11: LTC_OV MAY NOT TAKE THE GENERIC LAYER FALLBACK
# DURING QUALIFICATION.
#
# 002N ended with `LTC_OV` reported as one connected component and the report
# was true and useless: `U18.3 -> R77.2` had gone 13.087 mm across F.Cu with two
# vias, which is exactly the long generic excursion D-256 through D-259 have
# each refused for a high-impedance comparator input.  A gate that accepts
# "connected" without asking "connected HOW" will keep producing that answer.
# With this set, LTC_OV is offered B.Cu and nothing else, so the screen either
# proves a local route or reports no route - and cannot report a false pass.
LTCOV_BCU_ONLY = bool(os.environ.get('AQROOT_LTCOV_BCU'))
# D-266 / FBV2-P2-002T: SCARCE-PAD ESCAPE RESERVATION.
#
# 002S measured three of its four failing pads still escaping at 0.20-0.25 mm
# on the FINISHED board.  They were never walled in; they lost their lane to a
# branch that had the whole board to work with.  Permuting whole-branch order
# only chooses a different casualty, which 002M-002S proved four times over.
# D-266 stops running the race: the copper that MUST leave a scarce pad is laid
# or reserved first, and the long runs are completed afterwards from copper that
# is no longer scarce.  A reservation is a neck plus one via and NOTHING else -
# it is never counted as a connection.
D266 = bool(os.environ.get('AQROOT_D266'))
D266_INNER = os.environ.get('AQROOT_D266_INNER', 'I2')
# D-297 / FBV2-P2-003W: the SECONDARY U18.8 I2-join lever.  The reserve stores
# an inner layer (D266_INNER) and JOIN completes on it, per D-266 s14 ("the same
# inner layer, which cannot fail for want of a lane").  At the D-293 direction-2
# placement that premise breaks for ONE branch only: the BAT_PROTECTED_P
# U18.8->R75.2 reserve vias land at (2.800,66.800)/(7.200,66.500) and their I2
# join is NO_PATH because a BAT_RAW 0.600 mm current-path wall runs vertically on
# I2 at x~6.4-6.65 (y 50.45-70.40), severing the west->east lane between them.
# The reserve vias are THROUGH vias (copper on every layer), and In3.Cu is a
# routable six-layer signal layer (ROUTABLE[6]) that is EMPTY across the whole
# corridor on the full-run board (only 2 In3 tracks board-wide, none here, no In3
# copper pour) - so the same branch joins cleanly on I3 with NO new via, NO DRU/
# floor change, NO topology change.  AQROOT_U18BPP_JOIN names the join layer
# ('I2'/'I3') for this ONE branch; unset -> layer=va[2] (I2), byte-identical to
# every prior run.  Screened on the real full-run board: I2 join NO_PATH, I3 join
# ok 4.410 mm, real KiCad DRC adds ZERO new classes and clears via_dangling 1->0.
U18BPP_JOIN = (os.environ.get('AQROOT_U18BPP_JOIN') or '').upper()
# D-298 / FBV2-P2-003X: the U19 CAPACITY lever - reserve the shared EAST escape
# lane so a cross-board control run detours, and close the tighter pin first.
#
# The last Phase-A blocker is the saturated U19 dead-cell field: REC_BAT_LOW
# U19.7 and N_BATDIV U19.6 (a BOTTOM SOT-23-8, east row x=3.833) both fail
# NO_LEGAL_ESCAPE.  Measured on the 003W full-run board: both pins are pad-boxed
# N/S by their neighbour pads (placement-fixed) and their only non-pad directions
# E/W are walled by control tracks -- crucially the SAME LTC4368_FAULT_N
# R82.1->Q9.1 64 mm B.Cu run walls the EAST lane of BOTH (its direct path grazes
# the U19 east column; its endpoint (4.85,28.95) sits 30 um off U19.7's east ray).
# FAULT_N is a low-current control net with ample slack: with the U19 east lane
# reserved it re-routes on B.Cu and both pins escape east + hop to a bare inner
# layer (U19.7->REC_BAT_LOW I3, U19.6->N_BATDIV I2) with the only board-legal
# via geometry (0.65/0.40, annular 0.125 -- no DRU change).  The two adjacent
# pins fit only if the TIGHTER one escapes FIRST: U19.7 before U19.6 (U19.6-first
# re-boxes U19.7 -- an intra-pair swap).  Screened DRC-clean for the U19 escapes
# (real KiCad DRC, zone-refilled: zero new classes attributable to them).
# AQROOT_U19CAP: (a) install a foreign keep-out over the U19.7/U19.6 shared east
# escape lane before routing so FAULT_N (and any early aggressor) detours; lift it
# before the closure stage; (b) close REC_BAT_LOW before N_BATDIV.  Unset -> no
# keep-out and the ordinary DEADCELL close order, byte-identical to every prior
# run.  Net +2 vs a swap is judged ONLY by the full-authority gate (D-286).
U19CAP = bool(os.environ.get('AQROOT_U19CAP'))
# The reserved lane: a B.Cu keep-out centred just east of the U19 east row,
# spanning U19.7 (y28.58) and U19.6 (y27.93).  (x0,y0,x1,y1,half-width) in nm.
U19CAP_KO = (4700000, 27550000, 4700000, 28950000, 700000)
# D-301 / FBV2-P2-004A: the LTC_GATE U18.10->Q3.4 join PATH-SHAPING lever
# (ACCEPTED, OFF by default, +1 genuine connected-set gain under the full gate).
#
# The join is a D256_FCU connect_hop (near=B escapes, through via, run on
# far=F/I2/I3) routed EARLY in section 8b.  Its greedy central far run is the
# diagonal (5.15,64.75)->(5.15,63.6)->(2.25,60.7)->(1.9,60.7); it grazes the
# BAT_SENSE 1.0 mm current-path track (2.8,62.05)-(5.4,62.05) at ~(3.59,62.04),
# so the real gate() rejects it on D-269 alone (clearance 0.2803 vs 0.300 mm,
# ~19.7 um short -- FINE_ESC legalises the D-257 via, so there is NO D-249
# track_width violation in the real path; the audit's "0.20 mm D-249" was a raw-
# connect_hop probe artifact that bypassed FINE_ESC).  connect_hop will not take
# the longer clean detour while the central corridor is offered (D-300: a pure
# re-order is a NULL op - the driver re-takes the identical central path).  So
# install a FOREIGN keep-out over the rule-violating central corridor for exactly
# this ONE join (laid before the item, LIFTED right after, on the proven
# AQROOT_U19CAP KO mechanism), forcing connect_hop onto the clean detour.
# AQROOT_LTCGATE_KO names one or more KO capsules as 'LAYER:x0,y0,x1,y1,hw;...'
# in mm (LAYER defaults to B); unset -> no keep-out, byte-identical to every
# prior run.  Net gain is judged ONLY by the full-authority gate (D-286: no post-
# hoc/final-board proxy governs).  AQROOT_LTCGATE_KO=1 uses the validated DEFAULT
# below; an explicit 'LAYER:x0,y0,x1,y1,hw;...' string overrides it.
#
# DEFAULT (FBV2-P2-004A, faithful D256 in-run screen): the noKO connect_hop far
# run is the diagonal (5.15,64.75)->(5.15,63.6)->(2.25,60.7)->(1.9,60.7); it
# grazes the BAT_SENSE 1.0 mm current-path track (2.8,62.05)-(5.4,62.05) at
# ~(3.59,62.04), so the real gate() rejects it on D-269 alone (clearance 0.2803
# vs 0.300, ~19.7 um short -- FINE_ESC legalises the D-257 via, so there is NO
# D-249 track_width violation in the real path).  A keep-out capsule sealing the
# squeeze-gap just north of that BAT_SENSE track, on each far layer, forces the
# hop to cross WEST of the track's x=2.8 end: the join then routes F.Cu
# (5.15,64.75)->(4.0,64.75)->(1.9,62.65)->(1.9,60.7), 8.556 mm, and the REAL
# run()/gate() PASSES with NO new DRC (screened faithfully at the 8b point).
LTCGATE_KO_DEFAULT = [('F',  (2600000, 62500000, 5500000, 62500000, 400000)),
                      ('I2', (2600000, 62500000, 5500000, 62500000, 400000)),
                      ('I3', (2600000, 62500000, 5500000, 62500000, 400000))]
LTCGATE_KO = []                        # list of (layer, (x0,y0,x1,y1,hw)) in nm
_ltcgate_ko_env = os.environ.get('AQROOT_LTCGATE_KO')
if _ltcgate_ko_env and _ltcgate_ko_env.strip() in ('1', 'AUTO', 'DEFAULT'):
    LTCGATE_KO = list(LTCGATE_KO_DEFAULT)
elif _ltcgate_ko_env:
    for _part in _ltcgate_ko_env.split(';'):
        _part = _part.strip()
        if not _part:
            continue
        _lay, _rest = _part.split(':', 1) if ':' in _part else ('B', _part)
        _v = [float(x) for x in _rest.split(',')]
        if len(_v) != 5:
            raise SystemExit('AQROOT_LTCGATE_KO segment needs '
                             'LAYER:x0,y0,x1,y1,hw (mm): %r' % _part)
        LTCGATE_KO.append((_lay.strip().upper(),
                           tuple(int(round(x * 1e6)) for x in _v)))
# D-267 / FBV2-P2-002U: the SAME reservation idea, one path role over.
# AQROOT_D267 names the staging family (F1/F2/F3) whose prefix of the
# clean-board trunk `D9.1` reserves before the control field runs.
D267 = os.environ.get('AQROOT_D267')

_d256 = (os.environ.get('AQROOT_D256') or '').upper()
if _d256 and _d256 not in PL.D256_SETS:
    raise SystemExit('AQROOT_D256=%s is not one of %s'
                     % (_d256, sorted(PL.D256_SETS)))
D256_FCU = frozenset(PL.D256_SETS[_d256]) if _d256 else frozenset()

# D-279 / FBV2-P2-003G: THE ANTISOCIAL DEAD-CELL DETOUR HOPS, IT DOES NOT WALL
# ITS NEIGHBOURS.  A generalisation of D-278, measured at ROUTE time not order
# time.
#
# In the packed 0402 dead-cell field (R84-R96 / Q5-Q9, 0.65 mm pitch) a
# low-current SIG connection routed LATE finds its short direct B.Cu lane already
# full, so `connect_role` returns the only legal B.Cu path it can: a HORSESHOE
# that wraps a co-located pad.  Measured on the full baseline run,
# `N_POL R85.2 -> R86.1` (2.48 mm direct) laid a 6.23 mm B.Cu detour (2.5x) that
# boxes the co-located `VBRIDGE_TOP R85.1` pad to 0 escape, and the antisocial
# `REC_BAT_LOW Q7.1 -> R93.1` (7.47 mm direct, 23.1 mm route, 3.1x) is one of the
# routes that box `REF_HO R93.2`.  On the EMPTY board those same connections route
# DIRECT (N_POL R85.2->R86.1 = 2.52 mm) and R85.1 keeps 7 escapes, so the
# aggressor is the DETOUR, not the net.
#
# The six-layer stack exists precisely for a fan-out a single layer cannot make.
# When set, a dead-cell SIG route that came back an ANTISOCIAL DETOUR - copper
# length > D279_K x its straight-line pad distance AND > D279_MIN_MM absolute -
# is reverted and re-routed as an ORDINARY 0.35/0.20 through-via hop (D-257
# preferred, no rule relaxed) on an inner signal layer first, which runs DIRECT
# and lays no B.Cu wall.  The swap is kept ONLY if the hop is legal and strictly
# shorter; otherwise the original B.Cu route is re-laid untouched.  Adds an
# option, removes none.  Scoped to the low-current dead-cell class (never a wide/
# high-current net, never a TRUNK/TAP role, never a node target).  The default
# thresholds 2.0 / 5.0 mm are the MEASURED 003G values (they catch the 2.5x N_POL
# horseshoe and the 3.1x REC_BAT_LOW detour and nothing within 2x of its span);
# AQROOT_D279_K / _MIN_MM override them.  Unset (`AQROOT_D279`) reproduces the
# pre-003G behaviour byte-for-byte, so every earlier measurement stands.
D279 = bool(os.environ.get('AQROOT_D279'))
D279_K = float(os.environ.get('AQROOT_D279_K') or '2.0')
D279_MIN_MM = float(os.environ.get('AQROOT_D279_MIN_MM') or '5.0')

# D-270 / FBV2-P2-002X: the western-margin OFFLOAD, by path role.
# AQROOT_D270 names one of battery_route_plan.D270_SETS - the minimum set of
# bounded LOW-CURRENT branches (control signals, and the D-270 addition of
# microamp BAT_RAW divider branches on the power net) that leave B.Cu for
# In2/In3 so the high-current trunk has the corridor D-269 measured it needs.
# Unset reproduces the pre-002X behaviour exactly.  The set is a dict keyed
# (net, a, b) -> dict(layers, via), so the router offloads exactly the named
# branches and no others, and every current-carrying role is untouched.
_d270 = (os.environ.get('AQROOT_D270') or '').upper()
if _d270 and _d270 not in PL.D270_SETS:
    raise SystemExit('AQROOT_D270=%s is not one of %s'
                     % (_d270, sorted(PL.D270_SETS)))
D270_OFFLOAD = dict(PL.D270_SETS[_d270]) if _d270 else {}
D270 = bool(D270_OFFLOAD)
# D-270(a): the offloaded BAT_MAIN divider corridors are the ONLY inner-layer
# authority this ruling grants, added to the exact D-264 exclusion the two Kelvin
# sense corridors already carry.  Control-signal branches carry no area (they are
# not BAT_MAIN and In2/In3 was never barred to them); only power-net branches
# name a corridor.  Set once here so every DRU.write in the run is consistent.
DRU.INNER_OFFLOAD_AREAS = tuple(sorted(
    {spec['area'] for spec in D270_OFFLOAD.values() if spec.get('area')}))


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
    """PR-44: `area_trk` holds track UUIDs, not track objects - see
    `apply_areas`.  Resolve them against the board, and drop any whose copper a
    revert has since removed."""
    live = {}
    for t in board.GetTracks():
        live[str(t.m_Uuid.AsString())] = t
    out = {}
    for name, ids in area_trk.items():
        trks = [live[i] for i in ids if i in live]
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



def ladder_retry(ladder, attempt, on_fall=None):
    """PR-49, as a standalone rule so it can be regression-tested directly.

    `attempt(lad)` routes with the ladder it is handed and returns
    `(ok, gate_rejected_width)`:

        (True,  None)  the connection was routed AND passed every gate
        (False, w)     a rung routed geometrically at width `w` and the gate
                       rejected it; its copper has been reverted
        (False, None)  the connection failed for a reason that is not a gate
                       rejection - no corridor, no escape, no legal target

    On a gate rejection the ladder is truncated to the rungs strictly NARROWER
    than the rejected one and the attempt is repeated.  Nothing is invented:
    the rungs come from the path role's own authorised ladder, so this can
    never take a net below its standing floor.
    """
    lad = [w for w in ladder]
    while lad:
        ok, gw = attempt(lad)
        if ok:
            return True
        if gw is None:
            return False
        nxt = [w for w in lad if w < gw]
        if not nxt:
            return False
        if on_fall is not None:
            on_fall(gw, nxt[0])
        lad = nxt
    return False

def main():
    # PR-15: a SIGSEGV used to kill the run with no Python frame at all.  Enable
    # the fault handler as well as the watchdog, so a crash names the call.
    faulthandler.enable()
    if os.environ.get('AQROOT_WATCHDOG'):
        faulthandler.dump_traceback_later(
            int(os.environ['AQROOT_WATCHDOG']), repeat=True)
    t_all = time.time()
    pcb = RU.fresh(WORK, os.environ.get('AQROOT_SCRATCH', 'A'))
    # D-258: AQROOT_SIXLAYER migrates the SCRATCH copy to the six-layer stack
    # before anything is routed on it.  Section 4 requires the migration to be
    # proven on scratch before the authoritative board is touched, and a screen
    # that silently routed a four-layer board while claiming six would be the
    # 002K placement error wearing a different hat.
    if os.environ.get('AQROOT_SIXLAYER'):
        import sixlayer as SIX
        SIX.convert(pcb)
    # FBV2-P2-002F.  The battery-block PLACEMENT ECO is applied to the scratch
    # copy, never to the authoritative board: section 18 does not let this task
    # write authoritative signal copper, and until Phase A passes the placement
    # is not validated either.  Without the flag this script behaves exactly as
    # it did at 002E, so the 002E result stays reproducible.
    if os.environ.get('AQROOT_ECO_002F'):
        import place_p2_002f as ECO
        # FBV2-P2-002J: AQROOT_ECO_EXTRA names a JSON file of additional or
        # replacement moves, {ref: [x, y, rot, layer]}, applied on top of the
        # 002F ECO.  Section 5 tests R80/R81 poses one local change at a time,
        # and section 7 tests U19; overriding through a file keeps the committed
        # ECO itself unedited until a pose is actually proven.
        extra = os.environ.get('AQROOT_ECO_EXTRA')
        if extra:
            import json as _j
            ov = _j.load(open(extra))
            saved = dict(ECO.MOVES)
            for r, v in ov.items():
                ECO.MOVES[r] = tuple(v)
            ECO.apply(pcb, report=False)
            print("FBV2-P2-002F ECO + %d override(s) applied to the scratch "
                  "copy: %s" % (len(ov), ', '.join(sorted(ov))))
            ECO.MOVES.clear()
            ECO.MOVES.update(saved)
        else:
            ECO.apply(pcb, report=False)
            print("FBV2-P2-002F placement ECO applied to the scratch copy: "
                  "%d footprints moved" % len(ECO.MOVES))
    b = pcbnew.LoadBoard(pcb)
    tp = [f for f in b.GetFootprints() if f.GetReference() == 'TP34'][0]
    if tp.GetLayer() != pcbnew.B_Cu:
        tp.Flip(tp.GetPosition(), False)
    tp34 = (round(tp.GetPosition().x / 1e6, 3), round(tp.GetPosition().y / 1e6, 3),
            b.GetLayerName(tp.GetLayer()))
    for a in AREAS + STUBAREAS + FINEAREAS:
        RU.add_named_area(b, a, 0, 0, 1000, 1000)
    b.Save(pcb)
    DRU.write(pcb, [])

    # FBV2-P2-002L sections 6-9: a U18 CANDIDATE placement, named by a file.
    # AQROOT_PLACE_JSON is {base, moves}: the base placement it is expressed
    # against, and the absolute poses that differ from it.  The SAME file is
    # what the fingerprint asserts against, so the thing that is applied and
    # the thing that is checked cannot drift apart - which is the whole point
    # of section 2.
    _cand = os.environ.get('AQROOT_PLACE_JSON')
    if _cand:
        _spec = json.load(open(_cand))
        _bb = pcbnew.LoadBoard(pcb)
        _fp = {f.GetReference(): f for f in _bb.GetFootprints()}
        for _r, _v in _spec.get('moves', {}).items():
            _f = _fp[_r]
            if len(_v) > 3 and _bb.GetLayerName(_f.GetLayer()) != _v[3]:
                _f.Flip(_f.GetPosition(), False)
            _f.SetPosition(pcbnew.VECTOR2I(int(round(_v[0] * 1e6)),
                                           int(round(_v[1] * 1e6))))
            _f.SetOrientationDegrees(_v[2])
        _bb.BuildConnectivity()
        pcbnew.ZONE_FILLER(_bb).Fill(_bb.Zones())
        _bb.Save(pcb)
        print('CANDIDATE PLACEMENT APPLIED: %s (base %s, %d part(s) moved)'
              % (_spec.get('name', _cand), _spec.get('base'),
                 len(_spec.get('moves', {}))))

    # FBV2-P2-002L section 2: STATE WHICH BOARD THIS IS, BEFORE ANY COPPER.
    # 002K ran nine screens on the wrong placement because nothing in a run
    # named the placement it was on.  The fingerprint is printed every time and,
    # when AQROOT_EXPECT_PLACEMENT names one, it is ASSERTED - a mismatch is a
    # fail before routing rather than a Kelvin anomaly noticed four hours later.
    import placement_fingerprint as FP
    _fp = FP.fingerprint(pcb)
    print('PLACEMENT FINGERPRINT: %s' % FP.render(_fp))
    _want = os.environ.get('AQROOT_EXPECT_PLACEMENT')
    if _want:
        FP.assert_placement(pcb, _want, label='this screen')
        print('PLACEMENT ASSERTED: %s' % _want)
    else:
        print('PLACEMENT NOT ASSERTED (set AQROOT_EXPECT_PLACEMENT to require one)')
    sys.stdout.flush()

    # FBV2-P2-003M / D-286: MEASURE THE DRC/RATSNEST BASELINE ON THE ACTUAL
    # COMPLETE STARTING GEOMETRY, NOT A PARTIAL ONE.  Until 003M this baseline
    # was taken right after the 002F ECO (+AQROOT_ECO_EXTRA) but BEFORE the
    # AQROOT_PLACE_JSON candidate placement was applied a few lines below, so the
    # candidate's own placement-derived DRC (courtyards_overlap / solder_mask_
    # bridge / shorting_items) was NOT in the comparison baseline.  Every routing
    # gate then read those placement items as brand-new copper/safety violations
    # and rejected unrelated nets (003M: a full GATE_REJECTED cascade carrying a
    # FIXED placement delta across unrelated nets, DRIVER_EXIT=143).  The
    # baseline is now taken HERE - after ECO + AQROOT_ECO_EXTRA + AQROOT_PLACE_
    # JSON application, connectivity rebuild, zone fill, board save, DRU.write and
    # the fingerprint assertion, but before any QBoard copper - so a gate delta is
    # measured strictly against the real routed starting geometry.  When no
    # candidate placement is supplied the on-disk board here is byte-identical to
    # the pre-move board, so default behaviour is unchanged.  A placement-induced
    # violation that arises AFTER this boundary (i.e. from copper) is therefore
    # still fully surfaced - it cannot be hidden by the baseline.
    base, _ = RU.drc(pcb, "Abase", WORK)
    base_rn = RU.ratsnest(pcb)
    print("scratch baseline", dict(sorted(base.items())), "ratsnest", base_rn)
    sys.stdout.flush()


    qb = QR.QBoard(pcb)
    qb.wide_nets = WIDE
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(net, {})[ref] = p

    journal, stubs, area_trk = [], [], {}
    # FBV2-P2-002X / D-270: per-branch B.Cu track attribution, so the offload
    # study can model an INDIVIDUAL routed branch's copper being cut rather than
    # a whole net.  Populated only when AQROOT_BRANCH_TRK is set, and it records
    # UUIDs (never live objects - see apply_areas / PR-44) of the B.Cu tracks a
    # single (net, a, b) connection laid.  It never changes what is routed.
    branch_trk = {}
    reserved = {}          # D-266: ref -> (x, y, layer) of an accepted exit
    area_link = {}         # D-266: area -> [(x0, y0, x1, y1, w)] not-yet copper
    # D-278 (FBV2-P2-003F): the boxed single-lane CROSSING pin escapes by a
    # LAYER HOP, not an antisocial B.Cu detour.  order_tight already identifies
    # this pin (crossings > 0 in the fr <= 1 tied class -- the D-277 term); this
    # set carries those (net, a, b) keys to run_once so the crossing pin's long
    # run leaves the outer layer instead of horse-shoeing around the sibling
    # copper and sealing an unrelated pin.  See order_tight / run_once below.
    hop_first_keys = set()
    # PR-48 / D-257: bounded fine-pitch escape corridors, one per planned
    # escape, carrying that escape's local clearance and via geometry.
    fine = []
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
        plus 0.10 mm per side and nothing else.

        PR-44 (FBV2-P2-002J): AND IT MUST RESOLVE ITS TRACKS FRESH EVERY TIME.
        `grow` used to keep the PCB_TRACK objects themselves.  When a later
        connection fails and `qb.revert()` removes its copper, KiCad frees those
        objects, and the next `apply_areas()` called GetClass() on freed memory -
        a hard SIGSEGV, deterministic, at whichever connection happened to be
        the first revert after an area had grown.  It killed two full Phase A
        runs at exactly connection 28.

        Storing the UUID instead is safe: the object is alive when `grow` reads
        it, and the board is the authority on what still exists afterwards."""
        live = {}
        for t in qb.b.GetTracks():
            live[str(t.m_Uuid.AsString())] = t
        for name, ids in area_trk.items():
            trks = [live[i] for i in ids if i in live]
            if not trks:
                continue
            ps = RU.corridor_from_tracks(qb.b, trks)
            # D-266: bridge a reserved pair's gap with the capsule its inner run
            # will occupy, so the corridor is ONE polygon.  See RU.capsule.
            for (x0, y0, x1, y1, w) in area_link.get(name, ()):
                ps.BooleanAdd(RU.capsule(x0, y0, x1, y1, w))
            ps.Simplify()
            RU.set_area_poly(qb.b, name, ps)

    def grow(area, tracks):
        area_trk.setdefault(area, []).extend(
            str(t.m_Uuid.AsString()) for t in tracks)

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
        DRU.write(pcb, stubs, fine)
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
        """PR-49.  A WIDTH LADDER IS NOT A LADDER UNTIL THE GATE HAS SPOKEN.

        `run_once` treats a rung as successful the moment `connect_role`
        returns geometrically ok, and the DRC / connectivity gate runs AFTER
        that.  So a rung that routes and is then REJECTED by the gate used to
        abandon the whole connection - the remaining rungs of an already
        authorised ladder were never tried.

        FBV2-P2-002P is the case that proves it costs real results.
        `BAT_PROTECTED_P R75.2 -> D9.1` routed at 1.50 mm, failed
        `copper_edge_clearance 0.5000 mm; actual 0.4125 mm`, and stopped -
        while `PLAN_1_BPP_TRUNK` carries `[1.50, 1.20]` precisely so the trunk
        can fall to its D-249 floor, and 1.20 mm was legal at that pose.  The
        rung that would have closed the trunk was authorised, legal, and never
        attempted.

        THIS IS NOT A WIDTH-RELAXATION MECHANISM.  It only ever walks the
        ladder the path role ALREADY had: no rung is invented, nothing goes
        below the standing floor, no netclass or clearance is touched, DRC is
        never suppressed, and the copper from a rejected rung is fully reverted
        before the next one is attempted.  If every authorised rung fails, the
        connection fails and the board is exactly as it was.
        """
        def attempt(lad):
            state.pop('gate_w', None)
            ok = run_once(net, a, b_, role, lad, area, ct, fatal=False)
            return ok, (None if ok else state.pop('gate_w', None))

        def fell(gw, nxt):
            print("  ....  %-18s %-8s -> %-8s  %-18s %.2f mm rejected, "
                  "falling to %.2f mm"
                  % (net.split('/')[-1], a, b_, 'LADDER_RETRY',
                     gw / 1e6, nxt / 1e6))
            sys.stdout.flush()

        if ladder_retry(ladder, attempt, fell):
            return True
        if fatal and not state['fail']:
            state['fail'] = state['last']
        return False

    def run_reserve(net, a, b_, role, ladder, area, ct, fatal=True):
        """D-266 sections 5-8 and 14.  RESERVE a branch's exits, or JOIN them.

        RESERVE_PAIR lays the minimum neck from BOTH ends of one branch plus an
        ordinary 0.35/0.20 through via at each, and records where those vias
        landed.  JOIN then completes the branch between them on the inner
        layer, which cannot lose a race because the scarce part is already
        spent.

        Neither may masquerade as a completed connection: a reservation is
        journalled with `reservation: True`, counted in its own tally, and
        judged by the INVERTED gate - DRC gains no class and the ratsnest must
        NOT move, because a reservation that moves it has connected something.
        """
        t0 = time.time()
        pa = pads[net].get(a)
        if pa is None:
            state['last'] = '%s: missing pad %s' % (net, a)
            if fatal:
                state['fail'] = state['last']
            return False
        m = qb.mark()
        rn0 = state['rn']
        w = ladder[0]
        r = None

        if role in ('RESERVE', 'RESERVE_PAIR'):
            # TWO ATTEMPTS, AND THE ORDER IS THE RULING: shortest branch first,
            # nearest legal exit second.
            #
            # Scoring a via site on stub + remaining distance is what brings a
            # Kelvin branch under its 10.000 mm cap.  But the shortest exit is
            # not always the legal one - measured, the scored site for `R75.2`
            # was rejected on `BAT_MAIN routed clearance`, and treating that as
            # the branch's verdict cost `U18.8` outright.  So a gate-rejected
            # scored reservation falls back to the ordinary nearest-reachable
            # site, exactly as PR-49 falls to the next authorised rung.  No new
            # geometry is invented on either attempt.
            pairs = (((a, b_), (b_, a)) if role == 'RESERVE_PAIR'
                     else ((a, b_),))
            for attempt, scored in enumerate((True, False)):
                ends, r = [], None
                _pre_fine = len(fine)
                _pre_area = len(area_trk.get(area, [])) if area else 0
                _pre_link = len(area_link.get(area, [])) if area else 0
                for (u, v) in pairs:
                    pu, pv = pads[net].get(u), pads[net].get(v)
                    if pu is None:
                        r = dict(ok=False, reason='MISSING_PAD',
                                 why='%s: no such pad' % u)
                        break
                    toward = ((pv['x'] - pu['x'], pv['y'] - pu['y'])
                              if pv is not None else None)
                    rr = QR.reserve_escape(
                        qb, net, pu, w, CP, ct, near='B', far=D266_INNER,
                        via_dia=350000, via_drill=200000, toward=toward,
                        target=((pv['x'], pv['y'])
                                if (scored and pv is not None) else None))
                    if not rr['ok']:
                        rr['pad'] = u
                        r = rr
                        break
                    ends.append((u, rr))
                if r is not None:
                    qb.revert(m)
                    if attempt == 0:
                        continue
                    break
                if area is not None:
                    # The branch's own D-249 corridor is what relaxes
                    # `BAT_MAIN minimum width` to the ruled 0.20 mm sense
                    # width; the override attached to it is what permits the
                    # 0.35/0.20 through via.  Both are needed and they are not
                    # interchangeable - moving the stub to a FINE_ESC corridor
                    # bought the via and lost the width, and all four
                    # reservations then failed `min width 0.6000 mm`.
                    if not any(f[0] == area for f in fine):
                        fine.append((area, net, 0.20, 0.35, 0.20,
                                     'D-266 %s Kelvin reservation vias'
                                     % net.split('/')[-1]))
                    if len(ends) == 2:
                        # KiCad's `enclosedByArea` honours only the FIRST
                        # outline of a rule area, so two disjoint stubs in one
                        # corridor fail together with `via_diameter`,
                        # `track_width` and `drill_out_of_range` while either
                        # alone passes.  Bridging the gap with the capsule the
                        # inner run will occupy makes the corridor ONE polygon
                        # and describes exactly the copper that is coming.
                        va, vb = ends[0][1]['via'], ends[1][1]['via']
                        area_link.setdefault(area, []).append(
                            (va[0], va[1], vb[0], vb[1], w))
                    grow(area, qb.laid[m[0]:])
                g = reserve_gate(rn0, allow_dangle=True)
                if g['ok']:
                    r = dict(ok=True, mm=sum(e[1]['mm'] for e in ends),
                             vias=sum(e[1]['vias'] for e in ends),
                             layer=ends[0][1]['layer'], ends=ends,
                             scored=scored)
                    break
                if area is not None:
                    area_trk[area] = area_trk.get(area, [])[:_pre_area]
                    if len(fine) > _pre_fine:
                        del fine[_pre_fine:]
                    if area in area_link:
                        del area_link[area][_pre_link:]
                qb.revert(m)
                r = dict(ok=False, reason='GATE_REJECTED',
                         why='%s %s' % (g['why'],
                                        json.dumps(g.get('detail', ''))[:150]))
                if attempt == 0:
                    print("  ....  %-18s %-8s -> %-8s  %-18s shortest exit "
                          "rejected, falling back to the nearest legal exit"
                          % (net.split('/')[-1], a, b_, 'RESERVE_RETRY'))
                    sys.stdout.flush()
        elif role == 'RESERVE_RUN':
            # D-267: a HIGH-CURRENT escape reservation.  Outer layer, zero
            # vias, never below the trunk floor, and it must not reach another
            # node of its own net - which the inverted gate enforces.
            stage = PL.D267_STAGING.get(D267)

            def attempt_run(lad):
                for wr in lad:
                    mm = qb.mark()
                    rr = QR.reserve_run(qb, net, pa, wr, CP, ct, layer='B',
                                        target=stage)
                    if not rr['ok']:
                        qb.revert(mm)
                        continue
                    _pf, _pa2 = len(fine), (len(area_trk.get(area, []))
                                            if area else 0)
                    if area:
                        grow(area, qb.laid[mm[0]:])
                    gg = reserve_gate(rn0, allow_dangle=True)
                    if gg['ok']:
                        rr['width'] = wr
                        return rr
                    if area:
                        area_trk[area] = area_trk.get(area, [])[:_pa2]
                    if len(fine) > _pf:
                        del fine[_pf:]
                    qb.revert(mm)
                    print("  ....  %-18s %-8s -> %-8s  %-18s %.2f mm rejected: "
                          "%s" % (net.split('/')[-1], a, b_, 'RESERVE_LADDER',
                                  wr / 1e6, gg['why'][:60]))
                    sys.stdout.flush()
                return None

            r = attempt_run(ladder) or dict(
                ok=False, reason='NO_D9_RESERVATION',
                why='%s: no legal >= %.2f mm outer reservation to staging %s'
                    % (a, ladder[-1] / 1e6, D267))
        else:
            va, vb = reserved.get(a), reserved.get(b_)
            if va is None or vb is None:
                r = dict(ok=False, reason='NO_RESERVATION',
                         why='an endpoint of %s->%s was never reserved'
                             % (a, b_))
            else:
                _pre_area = len(area_trk.get(area, [])) if area else 0
                # D-297: this ONE branch may join on a named inner layer other
                # than its reserve layer (the vias are through vias, so the join
                # is electrically identical on I2 or I3).  Default is va[2].
                jl = va[2]
                if (U18BPP_JOIN in ('I2', 'I3')
                        and net == N + 'BAT_PROTECTED_P'
                        and a == 'U18.8' and b_ == 'R75.2'):
                    jl = U18BPP_JOIN
                r = QR.join_reserved(qb, net, va[:2], vb[:2], w, CP, ct,
                                     layer=jl)
                if r['ok']:
                    if area:
                        grow(area, qb.laid[m[0]:])
                    g = gate()
                    if not g['ok']:
                        if area:
                            area_trk[area] = area_trk.get(area, [])[:_pre_area]
                        qb.revert(m)
                        r = dict(ok=False, reason='GATE_REJECTED',
                                 why='%s %s'
                                     % (g['why'],
                                        json.dumps(g.get('detail', ''))[:150]))

        if not r['ok']:
            state['last'] = '%s %s->%s (%s) : %s' % (
                net.split('/')[-1], a, b_, role, r.get('why', r['reason']))
            print("  ....  %-18s %-8s -> %-8s  %-18s %.0fs   %s"
                  % (net.split('/')[-1], a, b_, r['reason'], time.time() - t0,
                     (r.get('why') or '')[:88]))
            sys.stdout.flush()
            if fatal:
                state['fail'] = state['last']
            return False

        if role == 'RESERVE_RUN':
            reserved[a] = (r['end'][0], r['end'][1], 'B')
            state['reservations'] = state.get('reservations', 0) + 1
            absorb_reservation_dangle()
            tag = 'RESERVED'
            extra = 'CURRENT_ESCAPE_RESERVATION %s staging %s end (%.3f, %.3f)' % (
                D267, r['layer'], r['end'][0] / 1e6, r['end'][1] / 1e6)
            w = r.get('width', w)
        elif role in ('RESERVE', 'RESERVE_PAIR'):
            for (u, rr) in r['ends']:
                reserved[u] = (rr['via'][0], rr['via'][1], rr['layer'])
                state['reservations'] = state.get('reservations', 0) + 1
            absorb_reservation_dangle()
            tag = 'RESERVED'
            extra = '%s vias %s @ %s' % (
                'shortest' if r.get('scored') else 'nearest', r['layer'],
                ' '.join('%s(%.3f,%.3f)' % (u, rr['via'][0] / 1e6,
                                            rr['via'][1] / 1e6)
                         for (u, rr) in r['ends']))
        else:
            state['done'] += 1
            tag = 'JOINED'
            extra = 'inner %s' % r['layer']
        journal.append(dict(net=net, a=a, b=b_, role=role, ok=True,
                            reservation=(role != 'JOIN'),
                            mm=r['mm'], vias=r['vias'], layer=r['layer'],
                            width=w / 1e6, area=area))
        print("  %-5s %-18s %-8s -> %-8s %7.3f mm  w=%.2f  %s %d via  %.0fs"
              % (tag, net.split('/')[-1], a, b_, r['mm'], w / 1e6, extra,
                 r['vias'], time.time() - t0))
        sys.stdout.flush()
        return True

    def reserve_gate(rn0, allow_dangle=False):
        """D-266 section 8.  A RESERVATION IS JUDGED DIFFERENTLY, BECAUSE IT
        IS NOT A CONNECTION.

        gate() requires the ratsnest to FALL, which is exactly right for a
        route and exactly wrong here: a reservation joins its pad to nothing,
        so a falling ratsnest would mean the neck had wandered into another
        node of the same net - the alternate-current-path failure section 8
        forbids.  So the test inverts: DRC must gain no class, and the ratsnest
        must be UNCHANGED.  Anything else is a route wearing a reservation's
        name."""
        apply_areas()
        pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
        qb.save()
        DRU.write(pcb, stubs, fine)
        after, det = RU.drc(pcb, "A", WORK)
        d = dict((k, v - base.get(k, 0)) for k, v in after.items()
                 if v > base.get(k, 0) and k != 'unconnected_items')
        if allow_dangle:
            # A RESERVATION IS DANGLING BY CONSTRUCTION, AND ONLY UNTIL ITS
            # BRANCH IS COMPLETED.  D-266's sense reservation leaves a via with
            # nothing on the far side (`via_dangling`); D-267's current
            # reservation leaves a 1.50 mm run ending at a staging point
            # (`track_dangling`).  Both are the reservation's signature rather
            # than a defect, both are absorbed only while outstanding, and
            # section 23 still requires the FINAL board to carry neither.
            d.pop('via_dangling', None)
            d.pop('track_dangling', None)
        if d:
            return dict(ok=False, why='new DRC %s' % json.dumps(d),
                        detail={k: det[k][:3] for k in d})
        rn = RU.ratsnest(pcb)
        if rn != rn0:
            return dict(ok=False,
                        why='a reservation changed the ratsnest (%d -> %d): it '
                            'terminated into another node of its own net' % (rn0, rn))
        return dict(ok=True)

    def absorb_reservation_dangle():
        """D-266.  A RESERVED VIA IS DANGLING BY CONSTRUCTION, AND ONLY UNTIL
        ITS BRANCH IS JOINED.

        A reservation is a neck and a through via with nothing on the far side
        yet, so KiCad reports `via_dangling` - correctly.  That is the
        reservation's SIGNATURE, not a defect: section 14 joins the two vias on
        their inner layer and the class goes away.

        It has to be absorbed into the DRC baseline the moment the reservation
        is accepted, or every later connection is rejected for a violation it
        did not cause - the same failure mode as measuring a board the ECO had
        moved.  ONLY the `via_dangling` class is absorbed, only by the amount
        the reservation actually added, and section 22 still requires the FINAL
        board to carry none: absorbing it here defers the question, it does not
        answer it.
        """
        after, _ = RU.drc(pcb, "A", WORK)
        for cls in ('via_dangling', 'track_dangling'):
            n = after.get(cls, 0)
            if n > base.get(cls, 0):
                base[cls] = n
                state['dangling'] = state.get('dangling', {})
                state['dangling'][cls] = n

    def run_once(net, a, b_, role, ladder, area, ct, fatal=True):
        if state['fail']:
            return False
        # D-266: the two roles that are NOT connections.
        if role in ('RESERVE', 'RESERVE_PAIR', 'RESERVE_RUN', 'JOIN'):
            return run_reserve(net, a, b_, role, ladder, area, ct, fatal)
        pa = pads[net].get(a)
        # D-267 section 19: `(stage)` is a node target that deliberately does
        # NOT take the canonical-ref shortcut.  `BAT_PROTECTED_P`'s canonical
        # node ref IS `R75.2`, so `R75.2 -> (node)` answered "already joined
        # via R75.2" and the trunk completion was skipped outright.
        node = (b_ in ('(node)', '(stage)'))
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
        if b_ == '(stage)':
            # D-267 section 19: `(stage)` means "join this pad to the copper
            # D9.1 reserved", so the ONLY question that may skip it is whether
            # `R75.2` and `D9.1` are already one component.  The generic
            # `(node)` skip asks whether the pad has ANY company on its net -
            # and `R75.2` has plenty by this point, so the trunk completion was
            # being skipped in silence.
            ref = 'D9.1'
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
        # D-256: PLANNED F.Cu ESCAPE, TRIED FIRST RATHER THAN LAST.
        #
        # connect_hop() has always been available, but only as the last rung of
        # the fallback ladder - so a control net reached F.Cu having ALREADY
        # spent the west margin's B.Cu trying every width not to.  The lane was
        # gone by the time the hop was taken.  For the connections D-256 names
        # (see battery_route_plan.D256_SETS) the hop is now the FIRST choice,
        # widest legal rung first, so the B.Cu lane is never claimed at all.
        # A failed hop falls through to the ordinary B.Cu ladder untouched:
        # this adds capacity, it does not remove an option.
        planned_via = None
        # D-263 section 14: the Kelvin pair, on its paired internal layer.
        if KELVIN_INNER and not node and (net, a, b_) in PL.KELVIN_INNER:
            spec = PL.KELVIN_INNER[(net, a, b_)]
            vd, vk = spec['via']
            lay = KELVIN_INNER if KELVIN_INNER in ('I2', 'I3') else spec['layer']
            for w in ladder:
                rr = QR.connect_hop(qb, net, pa, pb, w, CP, ct, far=lay,
                                    via_dia=vd, via_drill=vk)
                if rr['ok']:
                    r, used, hop, planned_via = rr, w, True, (vd, vk)
                    break
                qb.revert(m)
            if r is not None and not r['ok']:
                r = None
        # PR-47: the via-in-pad escape, tried first for the ONE connection
        # D-258 authorises it for.  A failure falls through to the ordinary
        # ladder untouched - this adds an option, it removes none.
        if (r is None or not r.get('ok')) and \
                Q3_POFV and not node and (net, a, b_) in PL.POFV_Q3:
            spec = PL.POFV_Q3[(net, a, b_)]
            vd, vk = spec['via']
            for w in ladder:
                rr = QR.connect_pofv(qb, net, pa, pb, w, CP, ct,
                                     inner=spec['inner'],
                                     via_dia=vd, via_drill=vk)
                if rr['ok']:
                    r, used, hop, planned_via = rr, w, True, (vd, vk)
                    break
                qb.revert(m)
            if r is not None and not r['ok']:
                r = None
        # D-270 (FBV2-P2-002X): the western-margin OFFLOAD, tried FIRST for the
        # bounded low-current branches the CTO ruling authorises to leave the
        # outer layer - and for those branches only.  Each hops B -> In2/In3 -> B
        # on the SMALLEST via its own netclass admits (the D-267 0.65/0.40 POWER
        # via for a BAT_RAW divider tap, never the trunk's 0.80/0.40) and returns
        # locally, so the long run leaves the western B.Cu corridor while the
        # branch stays connected.  A microamp divider tap on In2/In3 is exactly
        # the path-role exception D-264 gave the two Kelvin sense corridors, one
        # net over; every CURRENT-CARRYING role is untouched and keeps its outer
        # 1 oz zero-via copper.  A failure falls through to the ordinary ladder.
        if (r is None or not r.get('ok')) and D270 and not node \
                and (net, a, b_) in D270_OFFLOAD:
            spec = D270_OFFLOAD[(net, a, b_)]
            vd, vk = spec['via']
            for lay in spec['layers']:
                for w in ladder:
                    rr = QR.connect_hop(qb, net, pa, pb, w, CP, ct, far=lay,
                                        via_dia=vd, via_drill=vk)
                    if rr['ok']:
                        r, used, hop, planned_via = rr, w, True, (vd, vk)
                        break
                    qb.revert(m)
                if r is not None and r.get('ok'):
                    break
            if r is not None and not r['ok']:
                r = None
        # D-278 (FBV2-P2-003F): THE BOXED CROSSING PIN HOPS, IT DOES NOT DETOUR.
        #
        # order_tight marks the D-277 crossing pin (the boxed single-lane pin
        # whose route must cross a tied sibling) in `hop_first_keys`.  Left on
        # B.Cu that pin routes LAST and, because the sibling copper already fills
        # its direct lane, it horse-shoes far around the package -- a 13-20 mm
        # B.Cu run for a 7-8 mm connection -- and the detour seals an unrelated
        # pin's escape (measured: REF_POL TP24.1->U19.2 laid a wall over VREC_VCC
        # U19.8 and VBRIDGE_TOP R85.1, the D-278 blocker).  The six-layer stack
        # exists precisely for a crossing: the pin takes an ORDINARY 0.35/0.20
        # through-via hop (D-257 preferred, no rule relaxed) and runs DIRECT off
        # the outer layer, so no B.Cu wall is laid and both victims stay free.
        # A failed hop falls through to the ordinary B.Cu ladder untouched -- this
        # adds an option, it removes none.  Scoped exactly to the D-277 class.
        if (r is None or not r.get('ok')) and not node \
                and (net, a, b_) in hop_first_keys:
            for (vd, vk) in PL.D257_VIA_LADDER:
                for w in ladder:
                    rr = QR.connect_hop(qb, net, pa, pb, w, CP, ct,
                                        via_dia=vd, via_drill=vk)
                    if rr['ok']:
                        r, used, hop, planned_via = rr, w, True, (vd, vk)
                        break
                    qb.revert(m)
                if r is not None and r.get('ok'):
                    break
            if r is not None and not r['ok']:
                r = None
        if r is not None and r.get('ok'):
            pass
        elif D256_FCU and not node and (net, a, b_) in D256_FCU:
            # D-257's VIA HIERARCHY, and the order is the ruling: the PREFERRED
            # 0.35/0.20 ordinary through via is tried across the whole width
            # ladder first, and the 0.25/0.15 RESERVE is reached only when the
            # preferred geometry has been MEASURED impossible.  A connection
            # never drops to the reserve to buy a corridor a legal width could
            # not have -- the reserve answers a via-geometry question only.
            override = PL.D256_VIA_FOR.get((net, a, b_))
            ladder_v = (override,) if override else PL.D257_VIA_LADDER
            for (vd, vk) in ladder_v:
                for w in ladder:
                    rr = QR.connect_hop(qb, net, pa, pb, w, CP, ct,
                                        via_dia=vd, via_drill=vk)
                    if rr['ok']:
                        r, used, hop, planned_via = rr, w, True, (vd, vk)
                        break
                    qb.revert(m)
                if r is not None and r.get('ok'):
                    break
            if r is not None and not r['ok']:
                r = None
        if r is not None and r.get('ok'):
            pass
        elif role == 'TAP':
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
        elif True:
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
        # D-279 (FBV2-P2-003G): AN ANTISOCIAL DEAD-CELL DETOUR HOPS INSTEAD OF
        # WALLING ITS NEIGHBOURS.  A B.Cu SIG route that came back a horseshoe
        # (copper > D279_K x its straight-line pad span AND > D279_MIN_MM) is the
        # one whose detour seals a co-located pad (measured: N_POL R85.2->R86.1
        # 6.2 mm/2.5x boxes VBRIDGE_TOP R85.1); re-route it as an ordinary
        # through-via hop (D-257 preferred) on an inner signal layer, running
        # direct.  The swap is kept ONLY if the hop is legal
        # AND strictly shorter; otherwise the original B.Cu is re-laid untouched.
        # Scoped to the low-current dead-cell class - never a wide/high-current
        # net, TRUNK/TAP role, node target, or a route that already hopped.
        if (D279 and r is not None and r.get('ok') and not hop and not node
                and role == 'SIG' and net not in WIDE
                and net[len(N):] in PL.DEADCELL):
            direct_mm = math.hypot(pa['x'] - pb['x'], pa['y'] - pb['y']) / 1e6
            if r['mm'] > D279_MIN_MM and r['mm'] > D279_K * max(direct_mm, 1e-3):
                bcu_mm = r['mm']
                qb.revert(m)
                rh, vv, wv = None, None, None
                # A LOCAL field detour belongs on an INNER signal layer (In2/In3,
                # 0.5 oz - a low-current signal is welcome there), leaving the
                # outer F.Cu clear for the cross-board runs that need it (e.g. a
                # 40 mm bypass-cap hop landing in this same field).  Inner is
                # tried first, F.Cu last; connect_hop's own D-258 fallback still
                # holds, so a blocked inner layer simply falls through.
                far = ['I2', 'I3', 'F'] if 'I2' in qb.routable else None
                for (vd, vk) in PL.D257_VIA_LADDER:
                    for w in ladder:
                        rr = QR.connect_hop(qb, net, pa, pb, w, CP, ct, far=far,
                                            via_dia=vd, via_drill=vk)
                        if rr['ok']:
                            rh, vv, wv = rr, (vd, vk), w
                            break
                        qb.revert(m)
                    if rh is not None:
                        break
                if rh is not None and rh['ok'] and rh['mm'] < bcu_mm:
                    print("  D-279  %-16s %-8s -> %-8s antisocial B.Cu %.1f mm "
                          "(%.1fx the %.2f mm span) -> layer hop %.1f mm, %d via"
                          % (net.split('/')[-1], a, b_, bcu_mm,
                             bcu_mm / max(direct_mm, 1e-3), direct_mm,
                             rh['mm'], rh.get('vias') or 0))
                    sys.stdout.flush()
                    r, used, hop, planned_via = rh, wv, True, vv
                else:
                    qb.revert(m)
                    for w in ladder:
                        rr = QR.connect_role(qb, net, pa, pb, 'B', w, CP, ct)
                        if rr['ok']:
                            r, used = rr, w
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
        ltcov_locked = (LTCOV_BCU_ONLY
                        and net in (N + 'LTC_OV', N + 'LTC_UV'))
        if not r['ok'] and not ltcov_locked and time.time() - t0 < ITEM_BUDGET:
            for use_node in (False, True) if not node else (True,):
                if role == 'TAP' and net in WIDE and False:
                    # D-267 section 16: A MICROAMP TAP ON A HIGH-CURRENT NET
                    # ROUTES LOCALLY ON B.Cu WITH ZERO VIAS, OR IT REPORTS.
                    #
                    # Correcting the via GEOMETRY was only half the ruling.
                    # The other half is that a divider tap has no business
                    # taking a layer excursion at all: doing so would create an
                    # inner-layer exception for `BAT_RAW` that nobody granted,
                    # which section 16 forbids in as many words.  So the hop is
                    # not offered, the full LAD_TAP ladder on B.Cu is the whole
                    # of the attempt, and a failure is a finding rather than a
                    # via.
                    break
                for w in hop_lad:
                    if use_node and not skip:
                        skip = cluster_of(a)
                    tgt = (anchor_on(net, pa['x'], pa['y'], w, ct, skip)
                           if use_node else pb)
                    if tgt is None:
                        continue
                    # D-267 sections 15-17: VIA GEOMETRY IS A PROPERTY OF
                    # THE PATH ROLE, NOT OF THE NET.
                    #
                    # A TAP is a MICROAMP path.  `R79.1 -> R80.1` is a D-249
                    # 0.20 mm divider tap everywhere in this plan, and it was
                    # being handed the 0.80/0.40 TRUNK via because its net is
                    # `BAT_RAW` and TAP fell into the same `else` as TRUNK -
                    # the same net-name-versus-path-role confusion D-249 fixed
                    # for width and D-264 fixed for layer, now for via
                    # geometry.  Measured, that is the whole of
                    # `NO_VIA_SITE: no via site of 0.80 mm reachable on B`.
                    # A TAP gets the ordinary 0.35/0.20 through via; the
                    # current-carrying TRUNK keeps 0.80/0.40 untouched.
                    vd, vk = ({'SIG': (600000, 300000),
                               'TAP': (650000, 400000),
                               'SENSE': (650000, 400000)}
                              .get(role, (800000, 400000)))
                    far_ = None
                    if role == 'TAP' and net in WIDE:
                        # D-267 section 16: OUTER LAYERS ONLY, AND NO NEW
                        # EXCEPTION OF ANY KIND.
                        #
                        # A microamp divider tap may not take an In2/In3
                        # excursion - that would be a `BAT_RAW` inner-layer
                        # exception nobody granted - and it may not take the
                        # trunk's 0.80/0.40 via either.  What is left is F.Cu,
                        # which `BAT_MAIN is outer-layer only` already permits,
                        # with the SMALLEST VIA THE STANDING RULES ALLOW ON
                        # THIS NET, which is 0.65/0.40 and NOT the trunk's
                        # 0.80/0.40.
                        #
                        # The arithmetic is the board's own, and it was reached
                        # by measurement rather than assumption: 0.35/0.20 is
                        # rejected on `via_diameter` (board minimum 0.50 mm),
                        # 0.50/0.25 on `drill_out_of_range` (rule "POWER-class
                        # vias use the 0.40 mm drill"), and 0.50/0.40 on
                        # `annular_width` (rule "Via annular ring floor",
                        # 0.125 mm) - every one of those rejections is CORRECT.
                        # 0.40 mm of drill plus two 0.125 mm rings is 0.65 mm,
                        # and that is the floor.  So the honest form of section
                        # 15's ruling is narrower than it looks: a TAP cannot
                        # be given a small via on a POWER net, because the
                        # netclass forbids it - what it CAN be given is the
                        # smallest legal one, and outer layers only.
                        # Forbidding the hop outright was measured and is
                        # WORSE than 002T - `R77.1` AND `R79.1` both fell out
                        # of the BAT_RAW island, where 002T had kept `R77.1`.
                        far_ = ['F']
                    r = QR.connect_hop(qb, net, pa, tgt, w, CP, ct,
                                       far=far_, via_dia=vd, via_drill=vk)
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
            print("  ....  %-18s %-8s -> %-8s  %-18s %.0fs   %s"
                  % (net.split('/')[-1], a, b_, r['reason'], time.time() - t0,
                     (r.get('why') or '')[:88]))
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

        # PR-48 / D-257: a planned escape that actually took the layer gets its
        # own bounded corridor, grown from the copper it just laid.  Outside
        # that corridor the escape is judged by the ordinary board rules, so a
        # fine via cannot wander and the relaxation cannot be inherited.
        _pre_fine = len(fine)
        if planned_via is not None and hop:
            if area is None and len(fine) < len(FINEAREAS):
                area = FINEAREAS[len(fine)]
                fine.append((area, net, 0.20, planned_via[0] / 1e6,
                             planned_via[1] / 1e6,
                             'D-257 %s %s->%s escape' % (net.split('/')[-1], a, b_)))
            elif area is not None:
                # THE VIA OVERRIDE HAS TO REACH THE CORRIDOR THE ROW ALREADY HAS.
                #
                # A planned escape on a row that carries its OWN D-249 area -
                # the Kelvin pair is exactly that, `BAT_SENSE_KELVIN` and
                # `BAT_PROT_TAP_U18` - got no FINE_ESC corridor, because the
                # allocation was guarded on `area is None`.  So its 0.35/0.20
                # vias had no rule permitting them and DRC answered
                # `via_diameter ... board setup constraints min 0.5000 mm;
                # actual 0.3500 mm`.  The fix is not another corridor: it is to
                # attach the via geometry to the corridor that already bounds
                # this branch.
                fine.append((area, net, 0.20, planned_via[0] / 1e6,
                             planned_via[1] / 1e6,
                             'D-263 %s %s->%s escape via'
                             % (net.split('/')[-1], a, b_)))
        _pre_area = len(area_trk.get(area, [])) if area else 0
        _pre_stub = len(stubs)
        if area in DRU.TAP_CLEARANCE_AREAS and used < FLOOR.get(net, 0):
            # D-269(a): A BOUNDED TAP CORRIDOR HAS TO CARRY ITS WIDTH ALLOWANCE
            # AS WELL AS ITS CLEARANCE EXCLUSION.
            #
            # Before D-269 the divider rows had no area, so `run_once` gave each
            # one an anonymous BAT_STUB corridor carrying the width it actually
            # used, and `BAT_MAIN minimum width` (0.60 mm) was satisfied that
            # way.  Naming the corridor for the clearance exclusion took that
            # path away and the same copper came back as
            # `track_width (rule 'BAT_MAIN minimum width' ...)` - a relaxation
            # applied where nothing needed relaxing, one property over, exactly
            # the lesson PR-48 recorded.  The corridor now registers the
            # NARROWEST width its own copper uses.
            prev = [i for i, st in enumerate(stubs) if st[0] == area]
            if prev:
                i0 = prev[0]
                if used / 1e6 < stubs[i0][2]:
                    stubs[i0] = (area, net, used / 1e6, stubs[i0][3])
            else:
                stubs.append((area, net, used / 1e6,
                              'D-269 bounded microamp TAP corridor, %s'
                              % net.split('/')[-1]))
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
        rn_before = state['rn']
        g = gate()
        if not g['ok']:
            m = unsplit(m)
            qb.revert(m)
            if area:
                area_trk[area] = area_trk.get(area, [])[:_pre_area]
            if stubs and stubs[-1][0] == area:
                stubs.pop()
                area_trk.pop(area, None)
            elif len(stubs) > _pre_stub:
                del stubs[_pre_stub:]
            if len(fine) > _pre_fine:
                del fine[_pre_fine:]
                area_trk.pop(area, None)
            state['last'] = '%s %s->%s (%s) : %s %s' % (
                net.split('/')[-1], a, b_, role, g['why'], g.get('detail', ''))
            # PR-49: tell the caller WHICH rung the gate rejected, so the next
            # narrower authorised rung can be tried instead of the connection
            # being abandoned.
            if used is not None:
                state['gate_w'] = used
            # PR-46: SAY SO.  A connection rejected by the DRC / ratsnest gate
            # used to be reverted and requeued in COMPLETE SILENCE - no line in
            # the log, no entry in the journal, nothing.  It routed, it was
            # judged, it was thrown away, and the transcript showed only that
            # the item had never been mentioned.  Reading FBV2-P2-002K's first
            # D-256 screen, three items - `LTC_GATE U18.10 -> Q3.4`,
            # `BAT_RAW U18.1 -> (node)` and `LTC_SHDN Q4.3 -> (node)` - simply
            # were not there, and "not attempted" and "attempted, routed and
            # rejected by DRC" are not the same finding at all.
            print("  ....  %-18s %-8s -> %-8s  %-18s %.0fs   %s %s"
                  % (net.split('/')[-1], a, b_, 'GATE_REJECTED',
                     time.time() - t0, g['why'][:70],
                     json.dumps(g.get('detail', ''))[:200]))
            sys.stdout.flush()
            if fatal:
                state['fail'] = state['last']
            return False
        # ------------------------------------------------------------ PR-39
        # ROUTER SUCCESS MUST MEAN REAL CONNECTIVITY BETWEEN THE REQUESTED PADS.
        #
        # `run()` has three fallbacks that may REPLACE `pb` with a point on the
        # net's own copper: the node retarget, the hop-to-node, and a '(node)'
        # request.  Every one of them kept the REQUESTED pad name in the log
        # line and in the journal while building somewhere else entirely, so
        # `BAT_RAW R79.1 -> R80.1` was reported at 5.276 mm across a 12.030 mm
        # gap, put ZERO track endpoints in R80.1, and still incremented the
        # routed count.  A Phase B replay would have reproduced it faithfully.
        #
        # A route is now SUCCESS only if, after the copper is on the board, the
        # REQUESTED start pad and the REQUESTED end pad are in the SAME
        # connectivity component.  Retargeting is allowed - it is often the
        # right topology - but only when it genuinely joins what was asked for.
        #
        # A '(node)' request has no named end, so its contract is that the pad
        # ends up joined to SOME other pad of its own net.
        act_a = '%.3f,%.3f' % (pa['x'] / 1e6, pa['y'] / 1e6)
        act_b = ('(node)@%.3f,%.3f' % (pb['x'] / 1e6, pb['y'] / 1e6)
                 if pb is not None and pb.get('anchor') else b_)
        if node:
            others = [o for o in pads.get(net, {}) if o != a]
            conn = any(joined(a, o) for o in others)
        else:
            conn = joined(a, b_)
        if not conn:
            m = unsplit(m)
            qb.revert(m)
            if area:
                area_trk[area] = area_trk.get(area, [])[:_pre_area]
            if stubs and stubs[-1][0] == area:
                stubs.pop()
                area_trk.pop(area, None)
            elif len(stubs) > _pre_stub:
                del stubs[_pre_stub:]
            if len(fine) > _pre_fine:
                del fine[_pre_fine:]
                area_trk.pop(area, None)
            state['rn'] = rn_before
            state['last'] = ('%s %s->%s (%s) : PR-39 requested pads NOT '
                             'CONNECTED after routing (actual end %s)'
                             % (net.split('/')[-1], a, b_, role, act_b))
            print("  ....  %-18s %-8s -> %-8s  %-18s %.0fs"
                  % (net.split('/')[-1], a, b_, 'NOT_CONNECTED', time.time() - t0))
            sys.stdout.flush()
            if fatal:
                state['fail'] = state['last']
            return False
        state['done'] += 1
        _ckpt(journal)
        journal.append(dict(net=net.split('/')[-1],
                            requested_a=a, requested_b=b_,
                            actual_a=act_a, actual_b=act_b,
                            retargeted=bool(pb is not None and pb.get('anchor')),
                            requested_connected=True,
                            a=a, b=b_, role=role,
                            mm=round(r['mm'], 3), w=used / 1e6, grid=r['grid'],
                            area=area, profile=r.get('profile'),
                            vias=r.get('vias', 0), layer=r.get('layer', 'B.Cu'),
                            via_dia=r.get('via_dia'), via_drill=r.get('via_drill'),
                            via_xy=r.get('via_xy'), fine_area=area if planned_via else None,
                            pofv=r.get('pofv'), pad_copper_mm=r.get('pad_copper_mm'),
                            secs=round(time.time() - t0, 1)))
        print("  %-5s %-18s %-8s -> %-8s %8.3f mm  w=%.2f  g=%.3f %s%s %.0fs"
              % (role, net.split('/')[-1], a, b_, r['mm'], used / 1e6, r['grid'],
                 ('F.Cu+2 vias' if hop else '           '),
                 ('  [via node]' if (pb is not None and pb.get('anchor')) else ''),
                 time.time() - t0))
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

    def add(title, group, ct, tight=None):
        """`tight` is now a GROUP NAME, not a flag.  PR-33: U19 is an SOT-23-8
        on 0.65 mm pitch and its pins seal each other exactly the way U18's do,
        but the dead-cell block was queued in raw MST order with no measured
        ordering at all - so `U19.3`, `U19.6` and `U19.8` came back
        NO_LEGAL_ESCAPE once `U19.2` and `U19.5` had routed.  Naming the group
        lets the same measured tightest-first ordering apply to U19 WITHOUT
        letting a dead-cell item be promoted into U18's block, which a single
        boolean would have done."""
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

    def freedom(pad, need):
        """HOW MANY WAYS OUT this pad still has at the width it needs.

        PR-30.  Slack alone ties, and the tie-break was the order the plan
        happened to list the pins in - which put U18.2, the MIDDLE pin of an
        east row, LAST of the three.  A middle pin is boxed by a neighbour on
        both sides and has one lane; an end pin has two.  Routing the end pins
        first spends the middle pin's only lane, and U18.2 came back
        NO_LEGAL_ESCAPE with U18.1 and U18.3 named as its blockers.

        Counting the directions that still work costs one escape() call and
        breaks the tie the way the geometry actually constrains it: fewest ways
        out goes first."""
        e = qb.escape(pad, 'B', need, need, CP, CT_W, 25000, qb.ex0, qb.ey0)
        return len(e)

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
        groups = {}
        for i, it in enumerate(queue):
            g = it.get('tight')
            if g:
                groups.setdefault(g, []).append(i)
        idx = []
        for g in groups:
            if len(groups[g]) >= 2:
                idx = groups[g]
                break
        if len(idx) < 2:
            return queue
        rows = []
        for i in idx:
            need = min(queue[i]['lad'])
            # PR-38.  MEASURE BOTH ENDS, NOT JUST THE FIRST-NAMED PAD.
            #
            # U18's pin field is written pin-first, so measuring `a` measured
            # the fine-pitch pin.  The dead-cell block is a minimum spanning
            # tree, and its edges come out in whatever order the MST produced:
            # `TP24.1 -> U19.2` measures TP24.1, a 1.0 mm test pad with three
            # ways out, and never looks at `U19.2` - an SOT-23-8 pin with ONE.
            # So the block routed five U19 pins first and the two tightest
            # last, which is precisely backwards, and `U19.2`/`U19.3` came back
            # NO_LEGAL_ESCAPE.  A connection is as tight as its TIGHTER END.
            cand = [queue[i]['a']]
            if queue[i]['b'] != '(node)':
                cand.append(queue[i]['b'])
            best = None
            for ref_ in cand:
                pad = pads.get(queue[i]['net'], {}).get(ref_)
                if pad is None:
                    continue
                w = widest_escape(pad)
                nd = freedom(pad, need)
                key = (w - need, nd, w, ref_)
                if best is None or key < best:
                    best = key
            if best is None:
                best = (0, 0, 0, queue[i]['a'])
            # D-277: carry the tighter pad and its target so a planar tie-break
            # can be measured below.  `other` is the far end of this connection
            # (the pad NOT chosen as the tight one); its position is where this
            # pin's route is headed.
            tref = best[3]
            oref = queue[i]['b'] if tref == queue[i]['a'] else queue[i]['a']
            tpad = pads.get(queue[i]['net'], {}).get(tref)
            opad = pads.get(queue[i]['net'], {}).get(oref)
            ppos = (tpad['x'], tpad['y']) if tpad else None
            gpos = (opad['x'], opad['y']) if opad else None
            rows.append((best[0], best[1], best[2], i, best[3], ppos, gpos))
        # D-277: PLANAR TIE-BREAK FOR MUTUALLY-BOXED SINGLE-LANE PINS.
        #
        # D-276 named `N_POL U19.3 -> (node) NO_LEGAL_ESCAPE`.  Measured
        # (003E): U19.2 and U19.3 are the two middle west-row pins of U19's
        # SOT-23-8 - each has ONE lane out (east, into the inter-row gap) and
        # both tie on EVERY existing key: slack +0.14, ways-out 1, width.  So
        # the order fell through to the queue's MST order, which routed U19.2
        # first.  But U19.2 sits NORTH of U19.3 and its target (TP24.1) is
        # SOUTH, so its route crosses south through the gap and seals U19.3's
        # only lane - N_POL then has no escape.  Routing U19.3 first (its target
        # TP23.1 does not cross U19.2) leaves BOTH escapes legal (both route).
        #
        # The tie-break is planarity, measured on live geometry: among pins
        # tied on (slack, ways-out) with a SINGLE lane, the one whose pad->target
        # span CONTAINS a tied sibling's pad must cross that sibling, so it goes
        # LAST.  This fires only on an exact (slack, ways-out<=1) tie, is a
        # no-op for every pin with a second way out, and never reorders across
        # tightness classes - it only settles the order the queue left arbitrary.
        crossings = {}
        for (sl_a, fr_a, w_a, i_a, ref_a, pa, ta) in rows:
            c = 0
            if fr_a <= 1 and pa and ta:
                x0, x1 = sorted((pa[0], ta[0]))
                y0, y1 = sorted((pa[1], ta[1]))
                for (sl_b, fr_b, w_b, i_b, ref_b, pb, tb) in rows:
                    if i_b == i_a or (sl_b, fr_b) != (sl_a, fr_a):
                        continue
                    if pb and x0 <= pb[0] <= x1 and y0 <= pb[1] <= y1:
                        c += 1
            crossings[i_a] = c
            # D-278: a boxed single-lane pin that must cross a tied sibling is
            # the one whose B.Cu route detours antisocially; record it so
            # run_once escapes it by a LAYER HOP instead.  Same predicate, same
            # scope as the D-277 tie-break -- inert for any pin with a second way
            # out or no crossing.  The key persists once seen, so the mark
            # survives the sibling being routed and removed from later slices.
            if c > 0:
                it_a = queue[i_a]
                hop_first_keys.add((it_a['net'], it_a['a'], it_a['b']))
        rows.sort(key=lambda r: (r[0], r[1], r[2], crossings[r[3]]))
        if verbose:
            print("      pin-field slack: " + "  ".join(
                "%s %+.2f/%dway" % (ref_, sl / 1e6, nd)
                for (sl, nd, _, i, ref_, _p, _g) in rows))
            sys.stdout.flush()
        out = list(queue)
        for slot, row in zip(idx, rows):
            out[slot] = queue[row[3]]
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
    # PR-47 / D-258: THE POFV ESCAPE GOES FIRST, AND IT IS THE SAME SCARCITY
    # ARGUMENT PR-18 AND PR-36 ALREADY WON.
    #
    # `Q3.3` has exactly ONE way out of this design - a filled/capped via inside
    # its own pad - and that via is a THROUGH via, so it needs its site clear on
    # all six layers, F.Cu included.  Scheduled after the chain, it was not:
    # `BAT_SENSE Q3.6 -> R75.1` had taken an F.Cu hop whose 1.00 mm track runs
    # at x 2.800 down the whole of Q3's row, 0.365 mm from `Q3.3`'s centre, and
    # the POFV came back POFV_LAYER_CONFLICT on F.  A 1.00 mm trunk has the
    # whole board to find another way; this pad has one point.  So the pad goes
    # first and the trunk routes around the result.
    if Q3_POFV:
        add("0a. Q3 south-row POFV escape (PR-47)", PL.PLAN_8_CS_POFV, CT_S)
    if KELVIN_FIRST:
        add("0b. R75 Kelvin taps, before the trunk (D-262)",
            PL.PLAN_0A_KELVIN, CT_W, tight='U18')
    # D-266 sections 5-7: THE SCARCE COPPER GOES FIRST, AND ONLY THE SCARCE
    # COPPER.  The BAT_SENSE current path is laid in full because it IS the
    # thing that gets sealed; the four Kelvin endpoints reserve a neck and a
    # via and nothing else, because their long runs are not scarce once the
    # exits exist.
    if D267:
        # D-267 section 2: the D9.1 exit is reserved BEFORE the control field
        # and BEFORE the sense copper, because it is the exit the control field
        # takes away.  This is NOT the trunk: it stops at a staging point and
        # joins nothing.
        add("0b2. D9.1 trunk exit reserved (D-267 s2)",
            [(N + 'BAT_PROTECTED_P', 'D9.1', '(stage)', 'RESERVE_RUN',
              PL.LAD_D9_RESERVE, None)], CT_W)
    if D266:
        add("0c. BAT_SENSE current path, first (D-266 s5)",
            PL.PLAN_D266_SENSE, CT_W)
        # NO `tight` HERE, AND THE REASON IS MEASURED.  order_tight() re-sorts
        # THE WHOLE REMAINDER of the queue when it meets a tight item, so
        # marking the reservations tight interleaved them with the pin field
        # and the PR-43 bridges - `U18.9` was then asked for its exit after
        # several millimetres of other copper had been laid beside it and
        # returned NO_LEGAL_ESCAPE, on a board where the same reservation
        # succeeds in isolation.  A reservation exists precisely so it does NOT
        # have to win that race; scheduling it into one defeats the mechanism.
        add("0d. scarce Kelvin exits reserved (D-266 s6-7)",
            PL.PLAN_D266_RESERVE, CT_W)
    # D-263 section 10: THE TRUNK ADAPTS TO THE CONTROL GEOMETRY, NOT THE OTHER
    # WAY ROUND.
    #
    # Two orders have failed on this placement.  Trunk-first (002Q) laid
    # 19.219 mm of 1.20 mm copper through the U18 pin field and took `U18.2`,
    # `U18.3` and `U18.7` with it - 8 of 8 became 5 of 8.  Kelvin-first was
    # worse at 4 of 8, because the taps wanted the same lanes.  The lesson is
    # not "route the sense copper earlier": the pin field has ONE exit per pin
    # and the trunk has the whole board, so the trunk goes LAST and routes
    # around geometry the pin field has already proved it needs.
    if not TRUNK_LAST:
        add("1. BAT_PROTECTED_P trunk", PL.PLAN_1_BPP_TRUNK, CT_W)
        add("2-5. BAT_MAIN chain", PL.PLAN_2_CHAIN, CT_W)
    # PR-43: the divider chain's two long links to the battery node compete for
    # the west margin and lose it to U18's pin field if they wait their turn.
    #
    # MEASURED (FBV2-P2-002I) AND NOT ADOPTED BY DEFAULT.  Scheduling them here
    # DOES close BAT_RAW - 11 of its 12 pads become one island, R80.1 and D12.1
    # both CONNECTED - and it also closes LTC_SHDN, which had been NO_PATH.  But
    # U18 falls from 8 of 8 to 6 of 8: U18.7 (LTC4368_FAULT_N) returns
    # NO_LEGAL_ESCAPE and U18.10 (LTC_GATE) returns NO_PATH, and section 9
    # protects both.  The blocking copper beside those two pads is NOT BAT_RAW -
    # it is LTC_SHDN at 0.500 mm and BAT_SENSE at 0.500 mm - so the bridges did
    # not take U18's lanes directly.  They unblocked LTC_SHDN, which then took
    # the lane U18.7 needed.  The west margin is OVERSUBSCRIBED, and reordering
    # moves the casualty rather than removing it.  Both orderings score 24 of 29.
    #
    # Left OFF so the default tree keeps the known 8-of-8 U18 result, and ON
    # behind a flag so the measurement is reproducible.  This is a CTO call.
    if os.environ.get('AQROOT_PR43'):
        add("5b. BAT_RAW long bridges (PR-43)", PL.PLAN_TAPS_BRIDGE, CT_W)
    add("6b. U18 pin field",
        [r for r in PL.PLAN_0_U18
         if not ((KELVIN_FIRST or TRUNK_LAST or D266)
                 and (r[0], r[1], r[2]) in PL.KELVIN_KEYS)],
        CT_W, tight='U18')
    # PR-26, AND IT REVERSES FBV2-P2-002E's ORDER BECAUSE THE PLACEMENT MOVED.
    #
    # Section 9 put the gate network before the FET sense pairs, and at the
    # 002E placement that was right: a CS route threading Q3's two 0.67 mm
    # inter-pad gaps sealed Q3.2 and the gate net lost a pad outright.
    #
    # After the FBV2-P2-002F placement ECO the measurement inverts, and it was
    # MEASURED, on four variants of the same prefix:
    #
    #   (a) gate then CS, Q3 where it is      11/12 - Q3_CS NO_LEGAL_ESCAPE
    #   (b) CS then gate, Q3 where it is      12/12 - EVERYTHING, ZERO VIAS
    #   (c) gate then CS, Q3 moved 1 mm south 10/12 - loses BOTH CS nets
    #   (d) gate then CS, Q3_CS forced onto
    #       section 5's authorised layer drop 11/12 - the drop cannot even
    #       start, because Q3.3 has no B.Cu escape left to reach a via from
    #
    # With (b): Q2_CS 5.400 mm and Q3_CS 5.400 mm, both B.Cu, BOTH ZERO VIAS,
    # and LTC_GATE still closes on B.Cu with zero vias on all three of its
    # connections - Q3.2 <-> Q3.4 7.794 mm, Q2.2 <-> Q2.4 7.794 mm and the
    # inter-FET link Q3.2 <-> Q2.2 at 15.331 mm against 13.143 mm.  Section 5's
    # PREFERRED RESULT is "both GATE and Q3_CS leave on B.Cu without a via",
    # and 2.188 mm on one gate link is what it costs.  The section 5 via
    # authorisation is therefore NOT taken.
    #
    # PR-23's own finding is the reason this is not a rule change: "there is no
    # fixed right order, because the window each pin has left depends on the
    # copper already laid" - and the copper in front of Q3 is not where it was.
    LOCAL = (os.environ.get('AQROOT_LOCAL') or '').upper()
    # D-256 / section 10: when the Q3_CS layer excursion is in force, the Q3
    # GATE link claims the south-row slot FIRST and the sense pair takes the
    # excursion.  See battery_route_plan.PLAN_8_GATE_Q3_FIRST for the three
    # measurements that decide it.
    # Gate-first applies only when Q3_CS is taking the excursion and the GATE
    # is NOT: if both halves of the row have a planned escape, the CS excursion
    # goes first precisely so that it leaves stubs rather than a through-run in
    # the gaps, and the gate hops over what is left.
    q3_first = ((N + 'Q3_CS', 'Q3.1', 'Q3.3') in D256_FCU
                and (N + 'LTC_GATE', 'Q3.2', 'Q3.4') not in D256_FCU)
    # PR-47 / D-258: with Q3_CS taking the via-in-pad onto an internal signal
    # layer, the B.Cu south-row slot belongs to the gate drive, so the gate
    # goes first whenever the POFV escape is in force.
    if Q3_POFV:
        q3_first = True
    if LOCAL != 'R80':
        if q3_first:
            add("8a0. LTC_GATE Q3 row, before the sense pair (D-256)",
                PL.PLAN_8_GATE_Q3_FIRST, CT_S)
        # With the POFV escape already laid at 0a, section 8a keeps only the
        # Q2 pair; re-queuing Q3_CS here would just be skipped as joined.
        add("8a. FET sense pairs",
            [r for r in PL.PLAN_8_CS if r[1].startswith('Q2')] if Q3_POFV
            else PL.PLAN_8_CS, CT_S)
        add("8b. LTC_GATE",
            [r for r in PL.PLAN_8_GATE
             if not (q3_first and (r[0], r[1], r[2])
                     == (N + 'LTC_GATE', 'Q3.2', 'Q3.4'))], CT_S)
    # PR-36: THE MICROAMP TAPS GO BEFORE THE CROSS-BOARD SIGNAL RUNS, AND IT IS
    # PR-18's ARGUMENT ONE REGION OVER.
    #
    # `R80.1` sits in a ~1 mm slot between R80's own body and R81, and the two
    # longest signal runs in the block pass either side of it: `LTC_SHDN`
    # `U18.6 -> Q4.3` (28 mm) at x 4.65..4.95 and `LTC4368_FAULT_N`
    # `R82.1 -> Q9.1` (64 mm) at x 5.8..6.8.  Both are in section 9's trip
    # network, both routed FIRST, and `R80.1` then came back NO_LEGAL_ESCAPE
    # with 42 track blockers.
    #
    # A 1 mm slot cannot be recovered; a cross-board run has the whole board to
    # find another way.  Same scarcity rule as PR-18, so the taps go first.
    if LOCAL != 'R80':
        add("BAT_RAW taps",
            PL.PLAN_TAPS_PR43 if os.environ.get('AQROOT_PR43')
            else PL.PLAN_TAPS, CT_W)
        add("9. LTC trip network", PL.PLAN_9_TRIP, CT_S)
    # FBV2-P2-002J section 5: the LOCAL qualification prefix.
    #
    # A full Phase A costs about two hours, and section 5 needs a probe that is
    # "much cheaper" while still using REAL prefix copper - PR-40 rules out any
    # geometry-only proxy.  Everything up to and including the LTC trip network
    # is exactly the copper that decides the west margin: the 1.50 mm trunk,
    # BAT_SENSE/BAT_MID, the PR-43 BAT_RAW bridges, U18's eight-pin field, the
    # FET sense pairs, LTC_GATE, the microamp taps and the two cross-board trip
    # runs (LTC_SHDN U18.6->Q4.3 and LTC4368_FAULT_N R82.1->Q9.1).
    #
    # The dead-cell network, the fuel-gauge branches, the capacitor taps, the
    # closure stage and the test points are all EAST or SOUTH of the contested
    # margin and none of them can free a lane there, so they are skipped.  This
    # is a bounded prefix, not a reduced-fidelity model: every connection it
    # does attempt is attempted by the real router in the real order.
    # AQROOT_LOCAL=R80 lays ONLY the west-margin prefix: the 1.50 mm trunk,
    # the BAT_MAIN chain, the PR-43 BAT_RAW bridges and U18's eight-pin
    # field.  That is enough, because the copper that boxed U18.7 in D-255
    # is LTC_SHDN's U18.6 -> R80.2 segment, which is IN the U18 field, laid
    # between two adjacent pins of the same package.  Everything skipped is
    # east or south of the contested margin and cannot free a lane there.
    # AQROOT_LOCAL=U19 keeps the full prefix and adds the dead-cell network,
    # which IS U19's pin field, stopping before gauge/caps/closure/test pts.
    # AQROOT_LOCAL=D256 is the FBV2-P2-002K screen and it is section 8's list
    # exactly: the 1.50 mm trunk, the BAT_MAIN chain, the PR-43 BAT_RAW
    # bridges, U18's eight-pin field (which carries both R75 Kelvin branches),
    # the Q2/Q3 sense pairs, LTC_GATE, the microamp taps and the LTC trip
    # network - LTC_SHDN and LTC4368_FAULT_N included.  It stops BEFORE the
    # dead-cell network, which is U19's pin field, east of the contested margin
    # and unable to free a lane in it.  R80 stays the narrower 002J screen.
    if TRUNK_LAST:
        # The control geometry is proved by now: U18's pin field, the Q3 row
        # and the trip network have each had first refusal on their own lanes.
        # D-266 section 14: the reserved exits are joined on their inner
        # layer AFTER the control field has had its lanes, which is the whole
        # point of having reserved them.
        if D266:
            add("9a. paired inner Kelvin, joined (D-266 s14)",
                PL.PLAN_D266_JOIN, CT_W)
        else:
            add("9b. R75 Kelvin sense pair (D-263)", PL.PLAN_0A_KELVIN, CT_W)
        add("9c. BAT_MAIN chain, after the control field", PL.PLAN_2_CHAIN, CT_W)
        # D-267 section 19: the trunk is COMPLETED to the copper D9.1
        # reserved, not to D9.1's sealed pad.  Requested-pad truth is
        # unchanged and is checked on the ledger: R75.2 and D9.1 must end up
        # in one component.
        if D267:
            add("9d. BAT_PROTECTED_P trunk completed to the D9 reservation "
                "(D-267 s19)",
                [(N + 'BAT_PROTECTED_P', 'R75.2', '(stage)', 'TRUNK',
                  PL.PLAN_1_BPP_TRUNK[0][4], None)], CT_W)
        else:
            add("9d. BAT_PROTECTED_P trunk, last (D-263)",
                PL.PLAN_1_BPP_TRUNK, CT_W)
    if LOCAL not in ('R80', 'D256'):
        add("10a. dead-cell divider taps", PL.PLAN_10_DEADCELL_TAPS, CT_W)
    for short in ([] if LOCAL in ('R80', 'D256') else PL.DEADCELL):
        # PR-33: the dead-cell block is a fine-pitch pin field too - U19 is an
        # SOT-23-8 on 0.65 mm pitch - so it gets the same measured ordering.
        add("10b. dead-cell network",
            [(N + short, a, b_, 'SIG', PL.LAD_SIG, None)
             for a, b_ in mst(pads[N + short])], CT_S, tight='U19')
    # FBV2-P2-002L section 5: the U14.2 / U14.3 fuel-gauge branches ARE PR-48
    # cases B and C, so the D256 screen has to lay them.  The capacitor taps
    # stay out - they are east of the margin and cannot free a lane in it.
    if LOCAL == 'D256':
        add("11. fuel-gauge branches", PL.PLAN_11_GAUGE, CT_W)
    if not LOCAL:
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
                PL.PLAN_8_CS, PL.PLAN_8_GATE, PL.PLAN_9_TRIP,
                PL.PLAN_TAPS_BRIDGE, PL.PLAN_TAPS,
                PL.PLAN_10_DEADCELL_TAPS, PL.PLAN_11_GAUGE, PL.PLAN_12_CAPS):
        for row in grp:
            if row[0] not in SCOPE_NETS:
                SCOPE_NETS.append(row[0])
    for short in PL.DEADCELL:
        if N + short not in SCOPE_NETS:
            SCOPE_NETS.append(N + short)
    # PR-37.  THE CLOSURE STAGE WAS ASKING RULED SENSE PADS FOR TRUNK WIDTH.
    #
    # D-249 rules these pads INDIVIDUALLY - U11.2 and U18.8/.9/.1 at 0.20 mm,
    # U14.2/U14.3 at 0.15 mm because 0.20 mm is geometrically impossible there
    # by five microns, TP15 at 0.20 mm - and each has its own named corridor
    # area in which the trunk floor is relaxed.  The closure stage ignored all
    # of that and handed every BAT_PROTECTED_P pad the trunk ladder
    # [1.50, 1.20], so `U14.2 -> (node)` and `U14.3 -> (node)` came back
    # NO_LEGAL_ESCAPE at 0 s - not because the pads cannot escape (they escape
    # at 0.15 mm, measured) but because they were asked for 1.20 mm on a
    # 0.70 x 0.30 mm pad.
    #
    # The MAX17048 island sits 10.862 mm from C58.1 on the main node. It was
    # never a corridor problem.  Same root cause as the TP15 stub being judged
    # against the D-249 trunk floor.
    # PR-41.  THE SAME DEFECT PR-37 FIXED, ONE NET OVER.
    #
    # `BAT_RAW` is a WIDE net, so the closure stage handed every one of its
    # pads the BAT_MAIN ladder [1.00, 0.80, 0.60].  But the LTC4368 divider
    # chain - R77.1, R79.1, R80.1, U18.1 - and D12.1 are MICROAMP TAPS, ruled
    # 0.20 mm by D-249 and routed as TAPs everywhere else in this plan.  Asking
    # them for 0.60 mm minimum is why `R80.1 -> (node)` returned
    # NO_LEGAL_ESCAPE: measured on the C01 board R80.1 escapes at 0.20 mm with
    # TWO directions, and is already joined to R77.1/R79.1/U18.1.
    #
    # The BAT_RAW failure was never R80's placement.  The divider chain is one
    # island and the battery node is another, and the only two plan entries
    # that bridge them - `R80.1 -> Q2.7` and `D12.1 -> R77.1` - both failed,
    # leaving the closure stage as the last chance with the wrong ladder.
    RULED = {
        'R77.1': (PL.W_TAP, None),
        'R79.1': (PL.W_TAP, None),
        'R80.1': (PL.W_TAP, None),
        'D12.1': (PL.W_TAP, None),
        'U11.2': (PL.W_SENSE, 'BAT_PROT_ESCAPE_U11'),
        'U18.8': (PL.W_SENSE, 'BAT_PROT_TAP_U18'),
        'U18.9': (PL.W_SENSE, 'BAT_SENSE_KELVIN'),
        'U18.1': (PL.W_SENSE, 'BAT_RAW_TAP_U18'),
        'TP15.1': (PL.W_SENSE, 'BAT_PROT_TAP_U14'),
        'U14.2': (PL.W_U14, 'BAT_PROT_TAP_U14'),
        'U14.3': (PL.W_U14, 'BAT_PROT_TAP_U14'),
    }
    # FBV2-P2-002K: the D256 screen closes only the nets its own prefix laid.
    # Offering a tap to the dead-cell pads would route U19's pin field, which
    # is east of the contested margin, cannot free a lane in it, and is section
    # 11 work not yet authorised at this point in the task.
    CLOSE_NETS = ([nt for nt in SCOPE_NETS if nt[len(N):] not in PL.DEADCELL]
                  if LOCAL == 'D256' else SCOPE_NETS)
    # D-298: close the tighter U19 pin first.  The DEADCELL order lists N_BATDIV
    # (U19.6) before REC_BAT_LOW (U19.7); at closure that routes U19.6 first and
    # its 0.65 mm escape via re-boxes U19.7 (the intra-pair swap).  Move
    # REC_BAT_LOW immediately ahead of N_BATDIV so U19.7 escapes first and both
    # fit.  Only reorders the two nets, and only when the lever is on.
    if U19CAP and (N + 'REC_BAT_LOW') in CLOSE_NETS and (N + 'N_BATDIV') in CLOSE_NETS:
        CLOSE_NETS = list(CLOSE_NETS)
        CLOSE_NETS.remove(N + 'REC_BAT_LOW')
        CLOSE_NETS.insert(CLOSE_NETS.index(N + 'N_BATDIV'), N + 'REC_BAT_LOW')
    CLOSE = []
    for nt in CLOSE_NETS:
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
            if ref_ in RULED:
                w_, area_ = RULED[ref_]
                # a TAP is judged on resistance across its whole ladder; a
                # ruled SENSE pad has exactly one legal width
                if w_ == PL.W_TAP:
                    CLOSE.append((nt, ref_, '(node)', 'TAP', PL.LAD_TAP, area_))
                else:
                    CLOSE.append((nt, ref_, '(node)', 'SENSE', [w_], area_))
            else:
                CLOSE.append((nt, ref_, '(node)', 'TRUNK' if wide else 'SIG',
                              lad, None))
    # The closure stage offers a tap to every still-open pad in scope, which
    # is about a hundred connections.  For the section 5 west-margin screen
    # it is skipped: a candidate judged 8/8 on the NAMED plan alone is
    # strictly better than the D-255 control, which reaches only 6/8 even
    # WITH closure.  The screen is therefore conservative, never generous.
    if LOCAL != 'R80':
        add("12b. close remaining open pads", CLOSE, CT_W)

    # PR-37, second half: TP15's own stub is ruled 0.20 mm inside
    # BAT_PROT_TAP_U14, and PLAN_13_TEST already names both.  It is listed here
    # only so the ordering is explicit.
    # Section 13 keeps the test points LAST, and the D256 screen stops before
    # them: a test point cannot free a west-margin lane and must never be the
    # reason a functional verdict changes.
    if LOCAL not in ('R80', 'D256'):
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

    # ------------------------------------------------------------- PHASE B
    # SECTION 17.  The replay must INDEPENDENTLY RECREATE the block from the
    # saved plan, on a second clean scratch copy - not copy its coordinates.
    # So it re-runs the router: same queue, same driver, same rules, but the
    # ORDER is the order Phase A actually converged on and each item is pinned
    # to the width Phase A recorded.  Reproducing the geometry that way proves
    # the result is a property of the placement, not of a lucky pass ordering.
    replay = os.environ.get('AQROOT_REPLAY')
    passes = 7
    if replay:
        jr = json.load(open(replay, encoding='utf-8'))
        if jr.get('fail'):
            raise SystemExit('PHASE A DID NOT PASS - refusing to replay: %s' % jr['fail'])
        idx = {}
        for it in QUEUE:
            idx.setdefault((it['net'].split('/')[-1], it['a'], it['b']), it)
        newq, missing = [], []
        for e in jr['journal']:
            if e.get('role') == 'TRUNK+ESCAPE':
                continue
            it = idx.get((e['net'], e['a'], e['b']))
            if it is None:
                missing.append((e['net'], e['a'], e['b']))
                continue
            it = dict(it)
            it['lad'] = [int(round(e['w'] * 1e6))]
            it['tight'] = False
            newq.append(it)
        if missing:
            raise SystemExit('replay: journal names items the plan does not: %s' % missing[:5])
        print('PHASE B REPLAY: %d journal items, plan order frozen, widths pinned'
              % len(newq))
        QUEUE = newq
        passes = 2

    if U18_ORDER:
        # Freeze the pin field into the chosen schedule and take it out of the
        # measured reordering, so the schedule under test is the one that runs.
        rank = dict((pin, i) for i, pin in enumerate(U18_ORDER))
        idxs = [i for i, it in enumerate(QUEUE) if it.get('tight') == 'U18']
        rows = sorted(idxs, key=lambda i: rank.get(
            QUEUE[i]['a'].split('.')[-1], len(rank)))
        picked = [QUEUE[i] for i in rows]
        for slot, it in zip(idxs, picked):
            QUEUE[slot] = dict(it)
            QUEUE[slot]['tight'] = None
        print('U18 SCHEDULE PINNED: %s'
              % ' '.join(QUEUE[i]['a'] for i in idxs))
        sys.stdout.flush()

    # FBV2-P2-003F: AQROOT_LOCAL=DEADCELL keeps ONLY the dead-cell network
    # (stages 10a/10b, U19's pin field), skipping the whole west-margin prefix.
    # The dead-cell block is geographically isolated (U19 at y~=29, the trunk
    # congestion at y 60-93), so this is the cheapest REAL-ROUTER reproduction
    # of the D-277 next blocker (VREC_VCC U19.8 / VBRIDGE_TOP R85.1): the same
    # driver, the same order_tight, the same run()/gate(), only the prefix that
    # cannot reach U19's escape corridor removed.  It is a bounded probe prefix
    # in exactly the class of R80/D256/U19, and is inert for every other LOCAL.
    if LOCAL == 'DEADCELL':
        QUEUE = [it for it in QUEUE if it['title'].startswith('10')]
        print('LOCAL=DEADCELL: dead-cell-only prefix, %d queued' % len(QUEUE))
        sys.stdout.flush()

    u11 = [False]
    early = [None]          # FBV2-P2-003I: the one-shot early-bridge record
    # D-298: reserve the U19.7/U19.6 shared east escape lane BEFORE any routing,
    # so the LTC4368_FAULT_N cross-board control run (and any early aggressor)
    # detours around it instead of walling both boxed pins.  Lifted just before
    # the closure stage (title '12b') so U19.7/U19.6 escape into the freed lane.
    u19cap_ko = [None]
    if U19CAP:
        x0, y0, x1, y1, hw = U19CAP_KO
        u19cap_ko[0] = QR.SEG(x0, y0, x1, y1, hw, None, 'KO')
        qb.shapes['B'].append(u19cap_ko[0])
        print('U19 CAP: reserved east escape lane KO=%s' % (U19CAP_KO,))
        sys.stdout.flush()
    for p_ in range(1, passes):
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
        if not replay:
            QUEUE = order_tight(QUEUE)
        rest = []
        idx_ = 0
        shown = [False]
        while idx_ < len(QUEUE):
            # PR-32.  RE-MEASURE BEFORE EVERY FINE-PITCH PIN, NOT ONCE A PASS.
            #
            # PR-23 measured once per pass because at the FBV2-P2-002E placement
            # re-measuring per item took U18 from 7 escapes of 8 down to 6.  At
            # the 002F placement the opposite holds, and it is not an argument -
            # `ring_probe_002f.py` re-measures before every pin and routes 8 of
            # 8 against the real trunk, chain and flare, while one measurement
            # per pass loses U18.2.  The reason is PR-30: three east-row pins
            # tie on slack AND on ways-out at the head of the pass, so a table
            # taken there cannot separate them - but after one of them routes,
            # the other two no longer tie.
            if QUEUE[idx_].get('tight'):
                QUEUE[idx_:] = order_tight(QUEUE[idx_:], verbose=not shown[0])
                shown[0] = True
            it = QUEUE[idx_]
            # D-298: lift the U19 east-lane reservation exactly once, just before
            # the closure stage runs, so U19.7/U19.6 can escape into the freed
            # lane (every U19-crossing aggressor has already routed by now).
            if (U19CAP and u19cap_ko[0] is not None
                    and str(it.get('title', '')).startswith('12b')):
                if u19cap_ko[0] in qb.shapes['B']:
                    qb.shapes['B'].remove(u19cap_ko[0])
                u19cap_ko[0] = None
                print('U19 CAP: lifted east-lane reservation for closure')
                sys.stdout.flush()
            # FBV2-P2-003I / D-275: fire the EARLY western-corridor bridge ONCE,
            # at the first stage-8 item.  order_tight only permutes the tight
            # U18/U19 fine-pitch pins, so every '0*'/'6*' reservation + U18 item
            # keeps its place ahead of the first '8*' (LTC_GATE / FET-sense) item
            # -- i.e. the bridge lands in the proven-sparse window: after the
            # D-266 Kelvin reservation and U18 field have claimed R75.2's escape
            # sites (the c3bridge003c config carries both the 0d reserve via AND
            # the 4 entry-array vias), before the LTC_GATE / BAT_RAW taps inject
            # the corridor-choking vias.  apply_early operates on the live qb and
            # restores the via-blind obstacle model, leaving only the real bridge
            # copper as an obstacle the rest of the run routes around.
            if (EARLY_BRIDGE and early[0] is None
                    and str(it.get('title', '')).startswith('8')):
                import bridge_early_003i as EB
                early[0] = EB.apply_early(qb, pads, south=SOUTH_BRIDGE)
                ok = early[0].get('ok')
                if not ok and not state['fail']:
                    state['fail'] = 'early bridge: ' + early[0].get('fail', 'unknown')
                print('EARLY BRIDGE%s %s' % (
                    ' SOUTH' if SOUTH_BRIDGE else '',
                    'OK land=%s traverse=%.3fmm w=%.2f entry=%d exit=%d%s'
                    % (early[0].get('land'), early[0]['traverse']['mm'],
                       early[0]['traverse']['w_mm'], len(early[0]['entry_vias']),
                       early[0]['exit_vias'],
                       (' ywest=%.2f' % early[0]['south_ywest_mm'])
                       if 'south_ywest_mm' in early[0] else '') if ok
                    else 'FAIL -- ' + early[0].get('fail', '?')))
                sys.stdout.flush()
            # D-266 section 9: ONE branch, ONE explicitly authorised starting
            # rung.  The ladder itself is not changed - 0.20 mm is already in
            # LAD_SIG - and no other SIG connection is touched.
            if D266:
                _lad = PL.D266_LADDER.get((it['net'], it['a'], it['b']))
                if _lad is not None and it['lad'] is not _lad:
                    print('  D-266 s9  %-16s %-8s -> %-8s starts at its '
                          'measured %.2f mm rung (was %.2f mm)'
                          % (it['net'].split('/')[-1], it['a'], it['b'],
                             _lad[0] / 1e6, it['lad'][0] / 1e6))
                    it['lad'] = _lad
            # Measured ONCE PER PASS, not before every item.  Re-sorting the
            # block mid-pass picks whichever pin is locally tightest and then
            # lays a route that closes two others: it took U18 from 7 escapes
            # of 8 down to 6.  One measurement per pass, acted on in order, is
            # the version that holds.
            idx_ += 1
            if state['fail']:
                rest.append(it)
                continue
            # FBV2-P2-004A / D-300: the LTC_GATE U18.10->Q3.4 join path-shaping
            # lever.  Install the central-lane keep-out(s) for exactly this ONE
            # join, so connect_hop detours around the D-249/D-269 central rung,
            # then LIFT them right after the item (nothing else ever sees them).
            _is_ltcgate = (it['net'] == N + 'LTC_GATE'
                           and it['a'] == 'U18.10' and it['b'] == 'Q3.4')
            _ltc_kos = []
            if _is_ltcgate and LTCGATE_KO:
                for (_lay, _geo) in LTCGATE_KO:
                    _s = QR.SEG(_geo[0], _geo[1], _geo[2], _geo[3], _geo[4],
                                None, 'KO')
                    qb.shapes.setdefault(_lay, []).append(_s)
                    _ltc_kos.append((_lay, _s))
                print('LTC_GATE KO: %d central-lane keep-out(s) installed %s'
                      % (len(_ltc_kos), LTCGATE_KO))
                sys.stdout.flush()
            _pre_laid = len(qb.laid)
            _ltc_ran = run(it['net'], it['a'], it['b'], it['role'], it['lad'],
                           it['area'], it['ct'], fatal=False)
            for (_lay, _s) in _ltc_kos:
                if _s in qb.shapes.get(_lay, []):
                    qb.shapes[_lay].remove(_s)
            if _ltc_kos:
                print('LTC_GATE KO: keep-out(s) lifted after join'); sys.stdout.flush()
            if not _ltc_ran:
                rest.append(it)
                continue
            # D-270 instrumentation: record the B.Cu copper THIS branch laid, so
            # the offload study can cut one routed branch and no other.  A failed
            # rung is fully reverted before this runs (PR-49), so qb.laid[pre:]
            # is exactly the accepted copper.  UUIDs, not objects - a later
            # revert frees the object but the board stays the authority.
            if os.environ.get('AQROOT_BRANCH_TRK'):
                bkey = '%s %s %s' % (it['net'].split('/')[-1], it['a'], it['b'])
                bt = branch_trk.setdefault(bkey, [])
                for t in qb.laid[_pre_laid:]:
                    if (t.GetClass() == 'PCB_TRACK'
                            and t.GetLayer() == pcbnew.B_Cu):
                        bt.append(str(t.m_Uuid.AsString()))
            # Section 8 item 6: the U11.2 escape belongs with the trunk, not at
            # the end of the pass.  The moment the trunk exists, flare into it -
            # a 1.50 mm endpoint left until last is a corridor nobody reserved.
            if (not u11[0] and not state['fail'] and it['a'] == 'R75.2'
                    and it['b'] == 'D9.1'):
                u11[0] = u11_escape()
        # -------------------------------------------------------------- PR-40
        # THE FULL PREFIX IS THE QUALIFICATION MODEL.
        #
        # FBV2-P2-002G qualified a placement on a REDUCED prefix and the full
        # Phase A then rejected three of its connections.  Bare-board escape,
        # simultaneous stub escape and reduced-prefix routing are all cheaper
        # than the truth and all three have now been wrong.
        #
        # AQROOT_PROBE_PASS1 stops after pass 1 and writes the per-net
        # connectivity ledger plus the named target pairs.  Pass 1 is exactly
        # the copper that exists before and around the remaining bottlenecks,
        # laid by the real driver in the real order - not a proxy for it.
        if os.environ.get('AQROOT_PROBE_PASS1'):
            apply_areas()
            pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
            qb.save()
            DRU.write(pcb, stubs, fine)
            if os.environ.get('AQROOT_BRANCH_TRK'):
                # D-270: the routed board (qb.save above) plus this map is all
                # offload_probe_002x needs to cut one branch's B.Cu and re-ask
                # the trunk.  Keyed 'NET A B', short net name, matching TARGETS.
                json.dump(branch_trk, open(os.path.join(
                    SP, os.environ.get('AQROOT_BRANCH_TRK')), 'w'), indent=1)
                print('BRANCH_TRK  %d branches, %d B.Cu tracks -> %s'
                      % (len(branch_trk), sum(len(v) for v in branch_trk.values()),
                         os.environ.get('AQROOT_BRANCH_TRK')))
                sys.stdout.flush()
            import net_ledger as NL
            lg = NL.ledger(pcb)
            # FBV2-P2-002J section 5 criteria A..H, in order.
            TARGETS = [('BAT_RAW', 'R80.1', 'Q2.7'),
                       ('BAT_RAW', 'D12.1', 'R77.1'),
                       ('LTC_SHDN', 'U18.6', 'Q4.3'),
                       ('LTC4368_FAULT_N', 'U18.7', 'R81.2'),
                       ('LTC_GATE', 'U18.10', 'R76.1'),
                       ('LTC_GATE', 'U18.10', 'Q2.2'),
                       ('Q3_CS', 'Q3.1', 'Q3.3'),
                       ('BAT_PROTECTED_P', 'R75.2', 'U11.2'),
                       ('BAT_PROTECTED_P', 'U14.2', 'TP15.1')]
            U18PINS = [('U18.1', 'R77.1'), ('U18.2', 'R79.2'),
                       ('U18.3', 'R77.2'), ('U18.6', 'R80.2'),
                       ('U18.7', 'R81.2'), ('U18.8', 'R75.2'),
                       ('U18.9', 'R75.1'), ('U18.10', 'R76.1')]
            tg = {}
            for (nt, a_, b2) in TARGETS:
                tg['%s %s->%s' % (nt, a_, b2)] = bool(joined(a_, b2))
            u19 = {}
            for n_ in ('1', '2', '3', '5', '6', '7', '8'):
                ref = 'U19.' + n_
                pd = None
                for nt2 in pads:
                    if ref in pads[nt2]:
                        pd = nt2
                        break
                others = [o for o in pads.get(pd, {}) if o != ref] if pd else []
                u19[ref] = bool(any(joined(ref, o) for o in others))
            u18 = {}
            for (a_, b2) in U18PINS:
                u18[a_] = bool(joined(a_, b2))
            res = dict(probe='PR-40 full-prefix, end of pass 1',
                       local=os.environ.get('AQROOT_LOCAL') or None,
                       routed=state['done'], skipped=state['skipped'],
                       targets=tg, u19=u19, u18=u18,
                       u18_connected=sum(1 for v in u18.values() if v),
                       u19_connected=sum(1 for v in u19.values() if v),
                       ledger_connected=lg['connected'],
                       ledger_total=lg['total'],
                       unconnected=[k for k, v in lg['nets'].items()
                                    if not v.get('connected')],
                       out_of_scope=lg['out_of_scope'])
            json.dump(res, open(os.path.join(
                SP, os.environ.get('AQROOT_PROBE_OUT', 'probe_pass1.json')),
                'w'), indent=1)
            print('PR-40 PROBE  targets %s  U18 %d/8  U19 %d/7  ledger %d/%d'
                  % (''.join('1' if v else '0' for v in tg.values()),
                     res['u18_connected'],
                     res['u19_connected'], lg['connected'], lg['total']))
            print('             open U18 pins: %s'
                  % (', '.join(k for k, v in u18.items() if not v) or 'none'))
            sys.stdout.flush()
            return

        QUEUE = rest
        if not u11[0] and not state['fail']:
            u11[0] = u11_escape()
        if not QUEUE and u11[0]:
            break
        if state['done'] + state['skipped'] == before:
            state['fail'] = (state['last'] if QUEUE else 'U11.2 escape: none exists')
            break

    # FBV2-P2-003I: guaranteed one-shot -- if no stage-8 item existed in this
    # QUEUE (e.g. a bounded LOCAL prefix), lay the early bridge now, before the
    # final fill/save, so AQROOT_BRIDGE_EARLY always lays the bridge exactly once.
    # In a full production run the loop above fires it at the stage-8 boundary and
    # this is inert.
    if EARLY_BRIDGE and early[0] is None:
        import bridge_early_003i as EB
        early[0] = EB.apply_early(qb, pads, south=SOUTH_BRIDGE)
        if not early[0].get('ok') and not state['fail']:
            state['fail'] = 'early bridge (fallback): ' + early[0].get('fail', 'unknown')
        print('EARLY BRIDGE (fallback, no stage-8 item) %s' % (
            'OK' if early[0].get('ok') else 'FAIL -- ' + early[0].get('fail', '?')))
        sys.stdout.flush()

    apply_areas()
    pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
    qb.save()
    DRU.write(pcb, stubs, fine)

    # FBV2-P2-003D / D-275: the western-corridor vacate ECO + F.Cu via-array
    # bridge for BAT_PROTECTED_P, integrated as an in-line driver stage.  The
    # full route above leaves the western BPP trunk open (PR-40 bit 8 R75.2->
    # U11.2); the proven 003C mechanism (bridge_eco_003d.apply_eco) vacates the
    # cardinality-1 SHDN control branch off F.Cu and lays the array/traverse/array
    # bridge on THIS freshly routed board, before the authoritative DRC/ratsnest.
    # FBV2-P2-003I: DISABLED when AQROOT_BRIDGE_EARLY is set -- the bridge is laid
    # once, early, above, and the end-of-run timing is the measured via-density
    # FAIL this task exists to avoid.
    eco = None
    if os.environ.get('AQROOT_BRIDGE_ECO') and not EARLY_BRIDGE:
        import bridge_eco_003d as ECO
        eco = ECO.apply_eco(pcb)
        if not eco.get('ok') and not state['fail']:
            state['fail'] = 'bridge ECO: ' + eco.get('fail', 'unknown')
        print('BRIDGE ECO', 'OK' if eco.get('ok')
              else 'FAIL -- ' + eco.get('fail', '?'))
        sys.stdout.flush()

    after, det = RU.drc(pcb, "Afinal", WORK)
    rn = RU.ratsnest(pcb)
    res = dict(fail=state['fail'], connections=state['done'],
               skipped=state['skipped'], tp34=tp34, stubs=stubs,
               areas=area_stats(qb.b, area_trk),
               drc=dict(sorted(after.items())), baseline=dict(sorted(base.items())),
               ratsnest=rn, ratsnest_delta=rn - base_rn, journal=journal,
               bridge_eco=eco, bridge_early=early[0],
               secs=round(time.time() - t_all, 1))
    json.dump(res, open(os.path.join(
        SP, os.environ.get('AQROOT_RESULT', 'phaseA.json')), 'w'), indent=1)
    print("\nPHASE A:", ("FAIL -- " + state['fail']) if state['fail'] else "COMPLETE")
    print("routed", state['done'], "skipped-already-connected", state['skipped'],
          "ratsnest", rn, "(%+d)" % (rn - base_rn))
    print("DRC", dict(sorted(after.items())))
    if stubs:
        print("bounded stub exceptions:", [(s[0], s[2]) for s in stubs])


# PR-49: guarded so `ladder_retry` can be imported and regression-tested
# without launching a two-hour routing run as a side effect of the import.
if __name__ == '__main__':
    main()
