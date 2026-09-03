#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- whole-board, ALL-LAYER maze router (framework).

WHY THIS EXISTS
---------------
Every Demo routing harness written between D-4xx and D-577 joins two reserved
endpoints by ENUMERATING a hand-authored corridor family on ONE declared signal
layer: direct, x-then-y, y-then-x, a 4 mm spine lattice, one or two spines, and
in the mixed variants a single transition via placed by brute force.  Those
families are large (D-503 rejected 27,232 corridors; D-504 rejected 184,320 leg
combinations) but they are also *shallow*: an L-shape or a two-spine staircase
cannot walk around an obstacle it does not already straddle, and the layer is
fixed before the search begins.  The recorded result is a long run of `NO_PATH`
decisions on a board whose inner layers are, measurably, almost empty:

    free space, 0.20 mm track / 0.20 mm clearance, 0.05 mm lattice
      F.Cu   75.7 % free, largest connected free region 1.82 M cells
      In2.Cu 81.2 % free, largest connected free region 3.15 M cells
      In3.Cu 89.7 % free, largest connected free region 3.37 M cells
      B.Cu   71.1 % free, largest connected free region 2.36 M cells

A corridor family that fails on a board with 3.37 M contiguous free cells on
In3 is reporting a limitation of the SEARCH, not a capacity wall in the COPPER.

WHAT THIS DOES
--------------
One reusable primitive, `route_join`, that searches the whole board on every
routable layer at once:

  * blocked grids are built per routable layer by `QBoard.grid` -- the SAME
    rasteriser, the SAME per-obstacle `margin()`, the SAME 0.75-cell guard band
    that the accepted single-layer harnesses use.  No clearance is relaxed.
  * a via-legality grid is built by rasterising, on EVERY copper layer of the
    stack (including the In1/In4 GND references and the layers a through barrel
    merely passes), a disc of the via diameter, plus an explicit hole-to-hole
    test against every foreign hole.  A via is admitted only where all six
    layers and the drill rule admit it.
  * a single breadth-first wavefront runs over the (layer, x, y) lattice.  In
    plane it is the 8-connected no-corner-cutting wavefront already qualified in
    `qrouter.wave`.  Between planes it adds a through-via move at a cost of
    `via_cost_mm` of run, delivered through a delayed frontier so the cost is
    honoured exactly rather than approximated.
  * it is MULTI-SOURCE and MULTI-TARGET: every legal escape of every pad in the
    source island seeds the search, and every legal escape of every pad in the
    target island terminates it.  The router picks the pair, and the layer, and
    the via count -- none of them is declared in advance.
  * the descended path is split into per-layer runs and each run is smoothed by
    `QBoard.smooth` against the SAME blocked grid it was found on, so no
    straightened segment is straightened through an obstacle.

Nothing here writes to the authoritative board.  `route_join` emits into the
caller's scratch `QBoard` and is fully revertible through `QBoard.mark()` /
`QBoard.revert()`, exactly like every accepted primitive in `qrouter`.

CONTRACTS PRESERVED
-------------------
  * `qrouter.py` and `incremental_router.py` are NOT modified.  Every existing
    G-contract fixture and every accepted route stays byte-identical.
  * copper is only ADDED; this module never removes or edits an existing track,
    via or pad.
  * emitted geometry is integer nanometres on the search lattice, so segment
    endpoints are exact and shared (PR-5A).
  * In1.Cu and In4.Cu are never routed on -- `ROUTABLE[6]` is taken from
    `qrouter`, not restated here.
  * the real zone-refilled schematic-parity KiCad DRC in the calling gate stays
    the authority for legality.  This module is a *proposer*.
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "hardware/beta-v2/checks"))
import qrouter as qr            # noqa: E402
import incremental_router as ir  # noqa: E402


# Hole-to-hole is a fabrication rule, not a copper rule, so it is not visible to
# `QBoard.grid`.  0.25 mm is the figure `incremental_router._clears_existing_vias`
# already applies to accepted barrels; using the same number keeps one answer.
HOLE_CLR = 250000

# ---------------------------------------------------------------------------
# DRU CLEARANCES A SINGLE PER-NET SCALAR CANNOT EXPRESS
# ---------------------------------------------------------------------------
# `QBoard.margin` knows one clearance per obstacle KIND -- `clr_pad` for a pad,
# `clr_trk` for a track -- and the caller passes ONE pair of numbers for the net
# being routed.  `aqroot-Beta-v2.kicad_dru` carries two families of clearance
# rule that are keyed on the NETCLASS of the OTHER object instead, and the first
# whole-board maze batch produced a real DRC violation from each shape:
#
#   (a) "<CLASS> routed clearance":
#           A.hasNetclass(X) && A.Type != 'Pad' && B.Type != 'Pad'
#       fires when the OBSTACLE is the wide-class object, so an ordinary
#       0.20 mm signal passing a SWITCH_NODE *track* owes 0.30 mm even though
#       its own class asks for 0.20 mm.  BOTH sides must be routed copper, so a
#       PAD of the wide class is deliberately NOT bumped -- the same reading
#       `qrouter.margin` already documents at length for `wide_nets`.
#
#   (b) "<AGGRESSOR> to <VICTIM> separation":
#           A.hasNetclass(X) && B.hasNetclass(Y)
#           && (A.Type != 'Pad' || B.Type != 'Pad')
#       needs only ONE side to be routed copper.  Everything this module emits
#       is a track or a via, so the separation is owed against every object of
#       the partner class INCLUDING its pads.  A via of the I2C class parked
#       0.295 mm from L4's SWITCH_NODE pad 2 is exactly the violation the
#       pre-overlay batch produced against a 0.500 mm rule.
#
# Both tables are transcribed from the project .kicad_dru, not invented, and
# both are applied SYMMETRICALLY because KiCad evaluates a two-sided rule with
# each item taking the A role in turn.
CLASS_TRK_CLR = {
    'LED_BOOST':   300000,
    'SWITCH_NODE': 300000,
    'BAT_MAIN':    300000,
    'SYS_MAIN':    250000,
    'ACC_3V3':     250000,
    'ACC_5V':      250000,
    'VBUS_CHG':    250000,
    'NFC_5V_PA':   250000,
    'NFC_RF':      250000,
}

PAIR_CLR = {
    ('SWITCH_NODE', 'I2C'):     500000,
    ('SWITCH_NODE', 'USB_D'):   500000,
    ('SWITCH_NODE', 'NFC_RX'):  500000,
    ('SWITCH_NODE', 'NFC_RF'):  500000,
    ('SWITCH_NODE', 'NFC_OSC'): 500000,
    ('SWITCH_NODE', 'I2S'):     400000,
    ('LED_BOOST',   'USB_D'):   500000,
    ('LED_BOOST',   'I2C'):     500000,
}


def _kind(s):
    """The DRC `Type` of an obstacle shape: track, via, pad or keep-out."""
    if isinstance(s, qr.SEG):
        return 'track'
    tag = s.tag or ''
    if tag == 'KO':
        return 'ko'
    if tag in ('via', 'via/hole'):
        return 'via'
    return 'pad'                      # 'REF.NUM' and 'REF.NUM/hole'


def net_classes(qb):
    """netname -> netclass name, memoised on the board object."""
    cache = getattr(qb, '_maze_netclass', None)
    if cache is None:
        cache = {}
        for name, ni in qb.nets.items():
            try:
                cache[name] = ni.GetNetClassName()
            except Exception:
                cache[name] = 'Default'
        qb._maze_netclass = cache
    return cache


# Wavefront ceiling in lattice steps.  148 mm of board at a 0.10 mm lattice is
# 1,481 steps corner to corner; 6,000 leaves room for a route that has to walk
# most of the perimeter and still terminates a hopeless search.
WAVE_STEPS = 6000


# --------------------------------------------------------------------------- #
# grids
# --------------------------------------------------------------------------- #
class Field(object):
    """The blocked/via-legal lattice for ONE net at ONE width, whole board.

    Built once per (net, width, via) triple and reused by every join on that
    net, because the expensive part -- rasterising ~2,600 obstacle shapes onto
    six layers -- does not depend on the endpoints.
    """

    def __init__(self, qb, net, width, clr_pad, clr_trk, via_dia, via_drill,
                 G=100000, layers=None, margin_mm=2.0):
        self.qb, self.net, self.G = qb, net, G
        self.width, self.clr_pad, self.clr_trk = width, clr_pad, clr_trk
        self.via_dia, self.via_drill = via_dia, via_drill
        self.layers = tuple(layers or qb.routable)
        # Origin matches the one every qrouter caller uses for `escape`, so an
        # escape point is exactly on this lattice: ox + i*G, no rounding drift.
        m = int(margin_mm * qr.MM)
        self.ox = qb.ex0 - m
        self.oy = qb.ey0 - m
        self.x1 = qb.ex1 + m
        self.y1 = qb.ey1 + m
        # Same formula `QBoard.grid` uses, so the overlay and the base grid
        # are the same array shape by construction rather than by luck.
        self.nx = int((self.x1 - self.ox) // G) + 1
        self.ny = int((self.y1 - self.oy) // G) + 1
        self.cls = net_classes(qb)
        self.mycls = self.cls.get(net, 'Default')
        self.blk = {}
        self.rebuild_blk()
        self.via_ok = self._via_grid()

    # -- blocked grids ------------------------------------------------------ #
    def rebuild_blk(self):
        """(Re)build the per-layer blocked grid, DRU overlay included.

        `route_net` refreshes this between MST edges so the next join sees the
        copper the last one laid.  It must go through here: a bare
        `QBoard.grid` would silently drop the netclass-rule overlay and the
        second edge of a net would be routed to a weaker rule than the first.
        """
        for L in self.layers:
            self.blk[L] = (self.qb.grid(L, self.net, self.width, self.clr_pad,
                                        self.clr_trk, self.ox, self.oy,
                                        self.x1, self.y1, self.G)
                           | self.dru_overlay(L, self.width))

    def dru_overlay(self, layer, width):
        """Cells blocked by a .kicad_dru clearance `QBoard.margin` cannot see.

        Everything except the clearance number -- the obstacle set, the exact
        shape distance, the 0.75-cell guard band -- is exactly what
        `QBoard.grid` does, so this can only ever ADD blocked cells to it.  An
        obstacle whose required clearance does not EXCEED the base is skipped
        outright, which keeps the overlay empty for the common net.
        """
        blk = np.zeros((self.ny, self.nx), dtype=bool)
        guard = self.G * 0.75
        for s in self.qb.obstacles(layer, self.net):
            if not s.net:
                continue                      # keep-out: no clearance concept
            kind = _kind(s)
            if kind == 'ko':
                continue
            base = self.clr_trk if kind == 'track' else self.clr_pad
            ocls = self.cls.get(s.net, 'Default')
            req = base
            if kind != 'pad':                 # rule (a): both sides routed
                req = max(req, CLASS_TRK_CLR.get(ocls, 0),
                          CLASS_TRK_CLR.get(self.mycls, 0))
            req = max(req,                    # rule (b): one side routed
                      PAIR_CLR.get((ocls, self.mycls), 0),
                      PAIR_CLR.get((self.mycls, ocls), 0))
            if req <= base:
                continue
            mm_ = width / 2.0 + req + guard
            bx0, by0, bx1, by1 = s.bbox(mm_)
            i0 = max(0, int(math.floor((bx0 - self.ox) / self.G)))
            i1 = min(self.nx - 1, int(math.ceil((bx1 - self.ox) / self.G)))
            j0 = max(0, int(math.floor((by0 - self.oy) / self.G)))
            j1 = min(self.ny - 1, int(math.ceil((by1 - self.oy) / self.G)))
            if i1 < i0 or j1 < j0:
                continue
            X, Y = np.meshgrid(
                (self.ox + np.arange(i0, i1 + 1) * self.G).astype(float),
                (self.oy + np.arange(j0, j1 + 1) * self.G).astype(float))
            blk[j0:j1 + 1, i0:i1 + 1] |= (s.dist_np(X, Y) < mm_)
        return blk

    # -- via legality ------------------------------------------------------- #
    def _via_grid(self):
        """A through via is copper on EVERY layer of the stack and a hole through
        all of them.  Admit a site only where every copper layer admits the
        barrel's copper AND every foreign hole keeps its hole-to-hole distance.

        `QBoard.grid` with `width=via_dia` gives exactly the copper test: its
        per-obstacle `margin()` is `via_dia/2 + clr_pad` against a pad or barrel
        and `via_dia/2 + clr_trk` against a track, which is the clearance a via
        of that diameter owes.  The 0.75-cell guard band applies here too.
        """
        bad = np.zeros((self.ny, self.nx), dtype=bool)
        for L in self.qb.cu:            # F, In1, In2, In3, In4, B -- all of them
            bad |= self.qb.grid(L, self.net, self.via_dia, self.clr_pad,
                                self.clr_trk, self.ox, self.oy, self.x1,
                                self.y1, self.G)
            bad |= self.dru_overlay(L, self.via_dia)
        # HOLE-TO-HOLE, SAME NET INCLUDED.  The copper test above correctly
        # ignores this net's own copper -- a track may touch its own net.  A
        # DRILL may not touch anything: `hole_to_hole` and `holes_co_located`
        # are fabrication rules with no same-net exemption, and the first
        # whole-board batch collected eleven of them, every one between two
        # barrels or a barrel and a pad drill of the SAME net.  So no hole is
        # skipped here.
        guard = self.G * 0.75
        ny, nx = bad.shape
        XX = (self.ox + np.arange(nx) * self.G).astype(float)
        YY = (self.oy + np.arange(ny) * self.G).astype(float)
        for h in self.qb.holes:
            need = self.via_drill / 2.0 + h.r + HOLE_CLR + guard
            i0 = max(0, int(math.floor((h.cx - need - self.ox) / self.G)))
            i1 = min(nx - 1, int(math.ceil((h.cx + need - self.ox) / self.G)))
            j0 = max(0, int(math.floor((h.cy - need - self.oy) / self.G)))
            j1 = min(ny - 1, int(math.ceil((h.cy + need - self.oy) / self.G)))
            if i1 < i0 or j1 < j0:
                continue
            X, Y = np.meshgrid(XX[i0:i1 + 1], YY[j0:j1 + 1])
            bad[j0:j1 + 1, i0:i1 + 1] |= (((X - h.cx) ** 2 + (Y - h.cy) ** 2)
                                          < need * need)
        return ~bad

    # -- coordinate helpers -------------------------------------------------- #
    def cell(self, x, y):
        return (int(round((x - self.ox) / self.G)),
                int(round((y - self.oy) / self.G)))

    def point(self, i, j):
        return (self.ox + i * self.G, self.oy + j * self.G)

    def inside(self, i, j):
        return 0 <= i < self.nx and 0 <= j < self.ny


# --------------------------------------------------------------------------- #
# escapes
# --------------------------------------------------------------------------- #
def pad_escapes(qb, field, pad, toward, limit=8):
    """Legal launch points for one pad, on every outer layer it lives on.

    Delegates to the accepted `QBoard.escape`, which owns PR-5B (never narrower
    than the rule minimum) and PR-5C (the stub is analytically cleared against
    the same obstacle set as the trunk).  Returns a list of
    dict(layer, x, y, w, ln, pad).
    """
    out = []
    for L in ('F', 'B'):
        if L not in field.layers or not pad.get(L):
            continue
        prefer = None
        if toward is not None:
            prefer = (toward[0] - pad['x'], toward[1] - pad['y'])
        for c in qb.escape(pad, L, field.width, field.width, field.clr_pad,
                           field.clr_trk, field.G, field.ox, field.oy,
                           prefer=prefer)[:limit]:
            i, j = field.cell(c['x'], c['y'])
            if not field.inside(i, j):
                continue
            out.append(dict(layer=L, x=c['x'], y=c['y'], w=c['w'],
                            ln=c['ln'], pad=pad, i=i, j=j))
    return out


# --------------------------------------------------------------------------- #
# the wavefront
# --------------------------------------------------------------------------- #
def _shift_or(cur, free):
    """One 8-connected wavefront step, no corner cutting (qrouter.wave)."""
    nxt = np.zeros_like(cur)
    nxt[1:, :] |= cur[:-1, :]
    nxt[:-1, :] |= cur[1:, :]
    nxt[:, 1:] |= cur[:, :-1]
    nxt[:, :-1] |= cur[:, 1:]
    dn = np.zeros_like(cur)
    dn[1:, 1:] |= cur[:-1, :-1] & free[:-1, 1:] & free[1:, :-1]
    dn[1:, :-1] |= cur[:-1, 1:] & free[:-1, :-1] & free[1:, 1:]
    dn[:-1, 1:] |= cur[1:, :-1] & free[1:, 1:] & free[:-1, :-1]
    dn[:-1, :-1] |= cur[1:, 1:] & free[1:, :-1] & free[:-1, 1:]
    return nxt | dn


def wave3d(field, seeds, goals, via_cost_cells, budget=WAVE_STEPS):
    """Breadth-first distance field over (layer, x, y) from `seeds`.

    `seeds`/`goals` are lists of (layer, i, j).  Returns (dist, reached) where
    `dist` is a dict layer -> int32 array (-1 = unreached) and `reached` is the
    first goal touched, or None.

    The via move is delayed by `via_cost_cells` wavefront steps, which is what
    makes a via cost real run length instead of being free.  Without it the
    search ping-pongs between layers and produces a via every few millimetres.
    """
    L = field.layers
    free = {k: ~field.blk[k] for k in L}
    dist = {k: np.full((field.ny, field.nx), -1, dtype=np.int32) for k in L}
    cur = {k: np.zeros((field.ny, field.nx), dtype=bool) for k in L}
    # An escape point was proved legal ANALYTICALLY by `QBoard.escape`; the
    # lattice may still call its cell blocked because of the 0.75-cell guard
    # band, which is a rasterisation artefact and not a rule.  Both ends are
    # therefore opened, exactly as `join_reserved` opens its two reserved via
    # cells before searching between them.
    ends = [e for e in list(seeds) + list(goals)
            if e[0] in free and field.inside(e[1], e[2])]
    for (k, i, j) in ends:
        free[k][j, i] = True
    goals = [g for g in goals if g[0] in free and field.inside(g[1], g[2])]
    if not goals:
        return None, None
    seeded = False
    for (k, i, j) in seeds:
        if k not in cur or not field.inside(i, j):
            continue
        cur[k][j, i] = True
        dist[k][j, i] = 0
        seeded = True
    if not seeded:
        return None, None
    for (k, i, j) in goals:
        if cur[k][j, i]:
            return dist, (k, i, j)

    # A through via joins EVERY layer at one (x, y), so one delayed frontier
    # serves all of them: a cell that re-arrives on its own layer already has a
    # smaller distance and is dropped by the `dist < 0` mask.  That turns the
    # via bookkeeping from O(layers^2) array operations per step into O(1).
    pending = {}
    d = 0
    while d < budget:
        nxt = {}
        for k in L:
            if cur[k].any():
                nxt[k] = _shift_or(cur[k], free[k]) & free[k]
            else:
                nxt[k] = np.zeros((field.ny, field.nx), dtype=bool)
        due = d + via_cost_cells
        depart = None
        for k in L:
            part = cur[k] & field.via_ok
            depart = part if depart is None else (depart | part)
        if depart is not None and depart.any():
            if due in pending:
                pending[due] |= depart
            else:
                pending[due] = depart
        d += 1
        arr = pending.pop(d, None)
        if arr is not None:
            for k in L:
                nxt[k] |= (arr & free[k] & field.via_ok)
        alive = False
        for k in L:
            nxt[k] &= (dist[k] < 0)
            if nxt[k].any():
                alive = True
                dist[k][nxt[k]] = d
        cur = nxt
        if not alive:
            if not pending:
                return dist, None
            continue
        for (k, i, j) in goals:
            if dist[k][j, i] == d:
                return dist, (k, i, j)
    return dist, None


D8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def descend3d(field, dist, start, via_cost_cells):
    """Walk the 3-D distance field downhill from `start` back to a seed.

    Returns a list of (layer, i, j) or None.  Preference order at each cell is
    (a) keep going straight in-plane, (b) any in-plane step, (c) a via.  That
    ordering is what keeps the via count at the minimum the cost already
    implies rather than merely near it.
    """
    k, i, j = start
    path = [(k, i, j)]
    guard = int(dist[k][j, i]) + 8
    last = None
    while dist[k][j, i] > 0 and guard > 0:
        guard -= 1
        want = dist[k][j, i] - 1
        best = None
        for di, (dx, dy) in enumerate(D8):
            vi, vj = i + dx, j + dy
            if not field.inside(vi, vj):
                continue
            if dist[k][vj, vi] != want:
                continue
            score = 0 if di == last else 1
            if best is None or score < best[0]:
                best = (score, di, k, vi, vj)
        if best is not None:
            _, last, k, i, j = best
            path.append((k, i, j))
            continue
        # A THROUGH via at this cell connects EVERY layer of the stack, so the
        # descent may land on whichever layer is cheapest there -- not merely on
        # the one whose distance happens to equal `d - via_cost`.  Taking the
        # MINIMUM is not just shorter, it is what makes a second hop at the same
        # cell impossible: the minimum-distance layer cannot itself have arrived
        # by via (that would need a still-smaller distance at the same cell), so
        # it always has an in-plane predecessor.  Descending to an equal-cost
        # layer instead is how the first batch emitted three co-located barrels
        # on `EXT_SCL` and a 0.000 mm hole-to-hole pair on `I2C_SDA_INT`.
        if dist[k][j, i] - via_cost_cells >= 0 and field.via_ok[j, i]:
            hop, hopd = None, None
            for k2 in field.layers:
                if k2 == k:
                    continue
                d2 = int(dist[k2][j, i])
                if d2 < 0 or d2 >= dist[k][j, i]:
                    continue
                if hopd is None or d2 < hopd:
                    hop, hopd = k2, d2
            if hop is not None:
                k = hop
                last = None
                path.append((k, i, j))
                continue
        return None
    return path if dist[k][j, i] == 0 else None


# --------------------------------------------------------------------------- #
# the primitive
# --------------------------------------------------------------------------- #
def route_join(qb, field, src_pads, dst_pads, escape_limit=8, via_cost_mm=1.5,
               emit=True):
    """Join two islands of one net with a whole-board all-layer maze route.

    `src_pads` / `dst_pads` are lists of pad dicts (from
    `incremental_router.physical_net_pads`).  EVERY legal escape of EVERY pad on
    each side takes part: the router chooses which pads, which faces, which
    layers and how many vias.

    Returns dict(ok, reason, mm, vias, layers, from, to, ...).  On success and
    `emit`, the escape stubs, the run segments and the through vias are laid on
    `qb`; the caller can undo the whole thing with the `mark` it took first.
    """
    net = field.net
    cx = sum(p['x'] for p in dst_pads) / float(len(dst_pads))
    cy = sum(p['y'] for p in dst_pads) / float(len(dst_pads))
    sx = sum(p['x'] for p in src_pads) / float(len(src_pads))
    sy = sum(p['y'] for p in src_pads) / float(len(src_pads))

    src = []
    for p in src_pads:
        src += pad_escapes(qb, field, p, (cx, cy), escape_limit)
    dst = []
    for p in dst_pads:
        dst += pad_escapes(qb, field, p, (sx, sy), escape_limit)
    if not src:
        return dict(ok=False, reason='NO_LEGAL_ESCAPE_SRC',
                    why=(qb.escape_why or ['no legal escape on the source island'])[0],
                    pads=[p['ref'] for p in src_pads])
    if not dst:
        return dict(ok=False, reason='NO_LEGAL_ESCAPE_DST',
                    why=(qb.escape_why or ['no legal escape on the target island'])[0],
                    pads=[p['ref'] for p in dst_pads])

    vc = max(1, int(round(via_cost_mm * qr.MM / field.G)))
    # Search FROM the destination escapes so the distance field can be descended
    # from whichever source escape is cheapest, mirroring `qrouter.wave`.
    dist, hit = wave3d(field,
                       [(e['layer'], e['i'], e['j']) for e in dst],
                       [(e['layer'], e['i'], e['j']) for e in src], vc)
    if dist is None:
        return dict(ok=False, reason='NO_SEED')
    if hit is None:
        return dict(ok=False, reason='NO_PATH',
                    why='no all-layer corridor at %.3f mm between the islands'
                        % (field.width / 1e6),
                    src_escapes=len(src), dst_escapes=len(dst))
    start = next(e for e in src
                 if (e['layer'], e['i'], e['j']) == hit)
    path = descend3d(field, dist, hit, vc)
    if path is None:
        return dict(ok=False, reason='NO_DESCENT')
    end_key = (path[-1][0], path[-1][1], path[-1][2])
    finish = next(e for e in dst
                  if (e['layer'], e['i'], e['j']) == end_key)

    # split into per-layer runs, smooth each against its own blocked grid
    runs = []
    for (k, i, j) in path:
        if runs and runs[-1][0] == k:
            runs[-1][1].append((i, j))
        else:
            runs.append((k, [(i, j)]))
    polylines = []
    for k, cells in runs:
        if len(cells) > 1:
            blk = field.blk[k].copy()
            for (i, j) in (cells[0], cells[-1]):
                blk[j, i] = False
            cells = qb.smooth(blk, cells)
        polylines.append((k, qr.simplify(cells, field.ox, field.oy, field.G)))

    total = 0.0
    vias = []
    if not emit:
        for k, pts in polylines:
            for a, b in zip(pts, pts[1:]):
                total += math.hypot(b[0] - a[0], b[1] - a[1])
        return dict(ok=True, dry=True, mm=total / 1e6, vias=len(polylines) - 1)

    # HOLE-TO-HOLE AMONG THIS JOIN'S OWN BARRELS.  `Field.via_ok` is built
    # once, before anything is laid, so it cannot know where the barrels of the
    # path it is about to admit will land, and hole-to-hole applies between two
    # barrels of the SAME net exactly as between strangers.  `descend3d` now
    # makes a co-located pair impossible by construction, but two barrels a few
    # cells apart remain constructible geometry, so the join PROVES the spacing
    # instead of assuming it and fails cleanly when it cannot.
    sites = [pts[0] for _, pts in polylines[1:]]
    need = field.via_drill + HOLE_CLR
    for a in range(len(sites)):
        for b in range(a + 1, len(sites)):
            gap = math.hypot(sites[a][0] - sites[b][0],
                             sites[a][1] - sites[b][1])
            if gap < need:
                return dict(ok=False, reason='NO_VIA_SPACING',
                            why='two barrels of this join are %.3f mm apart, '
                                'below the %.3f mm hole-to-hole rule'
                                % (gap / 1e6, need / 1e6))

    m = qb.mark()
    qb.track(net, start['layer'], start['pad']['x'], start['pad']['y'],
             start['x'], start['y'], start['w'])
    total += start['ln']
    prev = None
    for k, pts in polylines:
        if prev is not None:
            vx, vy = pts[0]
            qb.via(net, vx, vy, field.via_dia, field.via_drill)
            forbid_via(field, vx, vy)
            vias.append((vx, vy))
        for a, b in zip(pts, pts[1:]):
            qb.track(net, k, a[0], a[1], b[0], b[1], field.width)
            total += math.hypot(b[0] - a[0], b[1] - a[1])
        prev = k
    qb.track(net, finish['layer'], finish['pad']['x'], finish['pad']['y'],
             finish['x'], finish['y'], finish['w'])
    total += finish['ln']
    return dict(ok=True, mm=total / 1e6, vias=len(vias),
                via_xy=[(round(x / 1e6, 4), round(y / 1e6, 4)) for x, y in vias],
                layers=[k for k, _ in polylines],
                **{'from': start['pad']['ref'], 'to': finish['pad']['ref']},
                mark=m)


# --------------------------------------------------------------------------- #
# island bookkeeping
# --------------------------------------------------------------------------- #
def net_islands(qb, net):
    """Group this net's physical pads by the copper that already joins them.

    A net with accepted partial copper must be completed island-to-island, not
    pad-to-pad: routing to a pad that is already connected adds a redundant loop
    and can only make congestion worse.
    """
    pads = ir.physical_net_pads(qb, net)
    qb.b.BuildConnectivity()
    conn = qb.b.GetConnectivity()
    index = {}
    live = []
    for f in qb.b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net or not p.GetNumber():
                continue
            pos = p.GetPosition()
            index[(f.GetReference() + '.' + p.GetNumber(), pos.x, pos.y)] = p
    parent = {k: k for k in index}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for key, p in index.items():
        for item in conn.GetConnectedItems(p):
            if item.GetClass() != 'PAD':
                continue
            pos = item.GetPosition()
            other = (item.GetParentFootprint().GetReference() + '.'
                     + item.GetNumber(), pos.x, pos.y)
            if other in parent:
                ra, rb = find(key), find(other)
                if ra != rb:
                    parent[ra] = rb
    groups = {}
    for d in pads:
        key = (d['ref'], d['x'], d['y'])
        root = find(key) if key in parent else key
        groups.setdefault(root, []).append(d)
    return sorted(groups.values(),
                  key=lambda g: (min(p['ref'] for p in g), len(g)))


def island_mst(islands):
    """Prim MST over islands, weighted by the closest pad pair."""
    n = len(islands)
    if n <= 1:
        return []

    def gap(a, b):
        return min(math.hypot(p['x'] - q['x'], p['y'] - q['y'])
                   for p in islands[a] for q in islands[b])

    INF = float('inf')
    intree = [False] * n
    best = [(INF, -1)] * n
    best[0] = (0.0, -1)
    out = []
    for _ in range(n):
        u = min((i for i in range(n) if not intree[i]), key=lambda i: best[i][0])
        intree[u] = True
        if best[u][1] >= 0:
            out.append((best[u][1], u))
        for v in range(n):
            if not intree[v]:
                d = gap(u, v)
                if d < best[v][0]:
                    best[v] = (d, u)
    return out


def route_net(qb, net, width=200000, clr_pad=200000, clr_trk=200000,
              via_dia=600000, via_drill=300000, G=100000, via_cost_mm=1.5,
              escape_limit=8, field=None):
    """Complete ONE net: island MST, then a whole-board all-layer join per edge.

    Atomic: any failed edge reverts every edge of this net, so the scratch board
    never carries a half-routed net into the gate.
    """
    mark = qb.mark()
    if field is None:
        field = Field(qb, net, width, clr_pad, clr_trk, via_dia, via_drill, G)
    islands = net_islands(qb, net)
    if len(islands) < 2:
        return dict(ok=True, net=net, joins=[], already=True, mm=0.0, vias=0)
    joins = []
    for (a, b) in island_mst(islands):
        r = route_join(qb, field, islands[a], islands[b],
                       escape_limit=escape_limit, via_cost_mm=via_cost_mm)
        r.pop('mark', None)
        joins.append(r)
        if not r.get('ok'):
            qb.revert(mark)
            return dict(ok=False, net=net, joins=joins,
                        reason=r.get('reason'), islands=len(islands))
        # each completed join merges its two islands; rebuilding the grouping
        # from real connectivity keeps the MST honest for the next edge
        field.rebuild_blk()
    return dict(ok=True, net=net, joins=joins, islands=len(islands),
                mm=round(sum(j['mm'] for j in joins), 3),
                vias=sum(j['vias'] for j in joins))


# --------------------------------------------------------------------------- #
# plane stitching
# --------------------------------------------------------------------------- #
# A plane-served net (here GND, on the In1/In4 reference pours) is NOT completed
# pad-to-pad.  Its pads reach each other through the pour, so the only copper it
# needs is, per island, one short escape stub and ONE through via that lands
# inside the pour.  Routing such a net with `route_net` would lay a pad-to-pad
# MST across the whole board -- hundreds of millimetres of redundant track on the
# signal layers -- to achieve exactly the connectivity a single barrel already
# gives.  `stitch_net` is therefore the correct primitive for a net that owns a
# plane, and `route_net` for one that does not.


def has_plane(qb, net):
    """True when `net` owns at least one filled (non rule-area) zone."""
    for z in qb.b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == net and z.IsFilled():
            return True
    return False


def _on_plane(qb, conn, pad_item):
    """True when this pcbnew pad already touches its net's pour or a via."""
    for it in conn.GetConnectedItems(pad_item):
        if it.GetClass() in ('ZONE', 'PCB_VIA'):
            return True
    return False


class _Plane(object):
    """A single-layer view of a `Field`, for an in-plane stitch wavefront."""

    def __init__(self, field, layer):
        self.__dict__.update(field.__dict__)
        self.layers = (layer,)


def forbid_via(field, x, y):
    """Retire the lattice around a just-placed barrel.

    `Field.via_ok` is built ONCE, from the holes that existed when the Field was
    constructed, so it cannot know about a barrel this run has just laid.  Every
    emitted via therefore retires its own neighbourhood before the next stitch
    or the next MST edge chooses a site.  The radius is the same
    drill + HOLE_CLR + guard the Field itself uses, so one answer governs both.
    """
    need = field.via_drill + HOLE_CLR + field.G * 0.75
    i0 = max(0, int(math.floor((x - need - field.ox) / field.G)))
    i1 = min(field.nx - 1, int(math.ceil((x + need - field.ox) / field.G)))
    j0 = max(0, int(math.floor((y - need - field.oy) / field.G)))
    j1 = min(field.ny - 1, int(math.ceil((y + need - field.oy) / field.G)))
    if i1 < i0 or j1 < j0:
        return
    X, Y = np.meshgrid(field.ox + np.arange(i0, i1 + 1) * field.G,
                       field.oy + np.arange(j0, j1 + 1) * field.G)
    field.via_ok[j0:j1 + 1, i0:i1 + 1] &= ~(((X - x) ** 2 + (Y - y) ** 2)
                                            < need * need)


def stitch_pad(qb, field, pad, max_mm=8.0, escape_limit=12):
    """Drop ONE pad onto its net's plane: shortest escape + one through via.

    The wavefront runs in a WINDOW of `max_mm` around the escape, not over the
    whole board.  A stitch is by definition local -- if no barrel is legal
    within a few millimetres of the pad the answer is `NO_VIA_SITE`, not a
    longer walk -- and a plane-served net has hundreds of these, so the window
    is what makes the primitive affordable at that count.

    Returns dict(ok, ...).  On success the stub, the run and the barrel are on
    `qb`; the caller's `mark` reverts all of it.
    """
    net = field.net
    escapes = pad_escapes(qb, field, pad, None, escape_limit)
    if not escapes:
        return dict(ok=False, reason='NO_LEGAL_ESCAPE', pad=pad['ref'],
                    why=(qb.escape_why or ['no legal escape'])[0])
    R = max(1, int(round(max_mm * qr.MM / field.G)))
    best = None
    for e in escapes:
        L = e['layer']
        if L not in field.blk:
            continue
        i0 = max(0, e['i'] - R - 2)
        i1 = min(field.nx, e['i'] + R + 3)
        j0 = max(0, e['j'] - R - 2)
        j1 = min(field.ny, e['j'] + R + 3)
        free = ~field.blk[L][j0:j1, i0:i1]
        vok = field.via_ok[j0:j1, i0:i1]
        si, sj = e['i'] - i0, e['j'] - j0
        free[sj, si] = True
        if vok[sj, si]:
            if best is None or best[0] > 0:
                best = (0, e, [(e['i'], e['j'])])
            continue
        dist = np.full(free.shape, -1, dtype=np.int32)
        dist[sj, si] = 0
        cur = np.zeros(free.shape, dtype=bool)
        cur[sj, si] = True
        hit = None
        for d in range(1, R + 1):
            if best is not None and d >= best[0]:
                break
            nxt = _shift_or(cur, free) & free & (dist < 0)
            if not nxt.any():
                break
            dist[nxt] = d
            landing = nxt & vok
            if landing.any():
                js, iss = np.nonzero(landing)
                hit = (int(iss[0]), int(js[0]))
                break
            cur = nxt
        if hit is None:
            continue
        cells = [hit]
        i, j = hit
        ok = True
        while dist[j, i] > 0:
            want = dist[j, i] - 1
            step = None
            for (dx, dy) in D8:
                vi, vj = i + dx, j + dy
                if (0 <= vi < free.shape[1] and 0 <= vj < free.shape[0]
                        and dist[vj, vi] == want):
                    step = (vi, vj)
                    break
            if step is None:
                ok = False
                break
            i, j = step
            cells.append((i, j))
        if not ok:
            continue
        cells.reverse()
        cost = int(dist[hit[1], hit[0]])
        if best is None or cost < best[0]:
            best = (cost, e, [(a + i0, b + j0) for (a, b) in cells])
    if best is None:
        return dict(ok=False, reason='NO_VIA_SITE', pad=pad['ref'],
                    why='no legal %.2f mm barrel within %.1f mm of any escape'
                        % (field.via_dia / 1e6, max_mm))

    _, e, cells = best
    L = e['layer']
    if len(cells) > 1:
        blk = field.blk[L].copy()
        for (i, j) in (cells[0], cells[-1]):
            blk[j, i] = False
        cells = qb.smooth(blk, cells)
    pts = qr.simplify(cells, field.ox, field.oy, field.G)
    qb.track(net, L, pad['x'], pad['y'], e['x'], e['y'], e['w'])
    total = e['ln']
    for a, b in zip(pts, pts[1:]):
        qb.track(net, L, a[0], a[1], b[0], b[1], field.width)
        total += math.hypot(b[0] - a[0], b[1] - a[1])
    vx, vy = pts[-1]
    qb.via(net, vx, vy, field.via_dia, field.via_drill)
    forbid_via(field, vx, vy)
    return dict(ok=True, pad=pad['ref'], layer=L, mm=round(total / 1e6, 3),
                via_xy=(round(vx / 1e6, 4), round(vy / 1e6, 4)))


def stitch_net(qb, net, width=200000, clr_pad=200000, clr_trk=200000,
               via_dia=600000, via_drill=300000, G=100000, field=None,
               max_mm=8.0, escape_limit=12):
    """Stitch every not-yet-planted island of a plane-served net to its plane.

    Unlike `route_net` this is NOT all-or-nothing: each island is an independent
    transaction, because one island that cannot reach the pour says nothing
    about the other two hundred that can.  A failed island is reverted on its
    own and reported; the successful ones stay.
    """
    if not has_plane(qb, net):
        return dict(ok=False, net=net, reason='NO_PLANE')
    if field is None:
        field = Field(qb, net, width, clr_pad, clr_trk, via_dia, via_drill, G)
    qb.b.BuildConnectivity()
    conn = qb.b.GetConnectivity()
    planted = set()
    for f in qb.b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net or not p.GetNumber():
                continue
            if _on_plane(qb, conn, p):
                pos = p.GetPosition()
                planted.add((f.GetReference() + '.' + p.GetNumber(),
                             pos.x, pos.y))
    done, failed = [], []
    for island in net_islands(qb, net):
        if any((p['ref'], p['x'], p['y']) in planted for p in island):
            continue
        best = None
        for pad in island:
            m = qb.mark()
            r = stitch_pad(qb, field, pad, max_mm=max_mm,
                           escape_limit=escape_limit)
            if r.get('ok'):
                best = r
                break
            qb.revert(m)
            best = best or r
        if best.get('ok'):
            done.append(best)
        else:
            failed.append(dict(island=[p['ref'] for p in island],
                               **{k: v for k, v in best.items() if k != 'ok'}))
    return dict(ok=bool(done), net=net, stitched=len(done),
                unreachable=len(failed), failures=failed[:40],
                mm=round(sum(d['mm'] for d in done), 3), vias=len(done),
                via_xy=[d['via_xy'] for d in done])
