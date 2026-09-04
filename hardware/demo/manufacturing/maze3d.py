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

import re
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
# PAD-ESCAPE NECKING -- the board's own rule, finally used
# ---------------------------------------------------------------------------
# `maze3d` routes ONE width per net, board-wide, taken from the netclass and
# raised by the `.kicad_dru` class floor.  `pad_escapes` therefore asks
# `QBoard.escape` for a stub that is never narrower than the trunk
# (`trunk_w == rule_min == field.width`), and `_pocket_escapes` rasterises its
# local window at that same width.  On a fine-pitch power package that is the
# wrong question: `BQ25185_SYS` is an 0.80 mm rail whose pads on `U12`, `U13`
# and `U21` are 0.30 mm wide on 0.50 mm pitch, so NO 0.80 mm stub leaves them
# in any direction and the router reports the pad enclosed.
#
# The project `.kicad_dru` already anticipated exactly this and carries, as the
# LAST matching `track_width` rule for those nets:
#
#     (rule "Pad-escape necking - width, fine-pitch power packages"
#         (constraint track_width (min 0.20mm))
#         (condition "A.intersectsCourtyard('U11') || ... || A.intersectsCourtyard('U9')"))
#
# The rule is read from the board's own `.kicad_dru` here rather than
# transcribed, so the router and the DRC cannot drift apart about which
# packages may neck and how far.
#
# THREE THINGS KEEP THIS A FANOUT AND NOT A WAIVER.
#
#   * LAST RESORT.  A necked candidate is offered for a (pad, layer) ONLY when
#     the full-width escape set for that pad and layer is EMPTY.  Every pad
#     that escapes today escapes the same way at the same width, so the lever
#     cannot perturb an accepted route; with `neck=None` the module is
#     byte-identical.
#   * CONFINED, THEN BOUNDED.  KiCad evaluates `A.intersectsCourtyard` per TRACK
#     OBJECT, and a smoothed escape is several of them.  A stub that leaves the
#     courtyard therefore stops being licensed at the segment that leaves: the
#     first whole-board run measured a 1.262 mm neck out of `U9.10` with
#     0.764 mm outside `U9` and the real DRC returned three `track_width`
#     errors against the P3V3 0.40 mm outer floor, one per stray segment.  So
#     the escape raster is MASKED to the named courtyards and any polyline that
#     still strays is refused -- containment is the condition under which the
#     board's own rule applies, not a stylistic preference.  A LENGTH bound
#     rides on top: a necked stub may be at most `Neck.max_nm` long (1.5 mm by
#     default), which is what stops a large courtyard such as `U9`'s from
#     becoming a corridor.  The strayed length is still measured and reported
#     with every escape; it is now always 0.0, and a number that must be zero
#     is worth printing.
#   * PROVED AT ITS OWN WIDTH.  `_stub_legal` before emission and `verify_laid`
#     after it both measure the ACTUAL width of the segment, so a necked stub is
#     re-proved against the full routed clearance for 0.20 mm copper and the
#     trunk is still re-proved for 0.80 mm copper.  Nothing is exempted.
#
# The trunk itself never necks.  `_pocket_escapes` terminates only on a cell the
# WHOLE-BOARD FULL-WIDTH lattice already calls free, so the wavefront leaves the
# neck endpoint at the contract width.  Electrically that is the textbook
# fine-pitch fanout: a sub-millimetre neck bonded at both ends to wide copper,
# ~2.5 mOhm/mm at 1 oz, whose IR drop and self-heating at the BQ25185's 1 A
# ceiling are negligible against the pad it starts in -- which is itself only
# 0.30 mm wide and carries the same current whatever the trace does.
NECK_MAX_MM = 1.5               # default bound on ONE necked stub


class Neck(object):
    """The board's pad-escape necking allowance, read from its `.kicad_dru`.

    CONFINEMENT IS NOT OPTIONAL, AND THE BOARD SAID SO IN DRC.

    The first cut of this class treated courtyard containment as a MEASUREMENT
    reported beside the escape, on the reading that `A.intersectsCourtyard`
    matches any track that touches the courtyard at all.  A whole-board run
    then produced a 1.262 mm necked stub out of `U9.10` of which 0.764 mm lay
    outside `U9`, and the real KiCad DRC returned THREE `track_width` errors
    against "P3V3 minimum width on the outer layers" -- one per 0.25 mm
    segment at (32.05, 26.8) on B.Cu.

    The reason is that KiCad evaluates a rule per TRACK OBJECT, not per
    polyline: a smoothed escape is several segments, and a segment that lies
    wholly outside every named courtyard does not intersect one, so the
    necking rule stops matching and the next-strongest `track_width` rule --
    the netclass floor -- wins.  Containment is therefore the condition under
    which the board's own rule licences the neck, and this class enforces it:
    the local escape raster is MASKED to the named courtyards, and any
    polyline that still strays is refused.  The measurement is kept and
    reported, now always 0.0, because a number that must be zero is worth
    printing.

    Membership is one vectorised even-odd test over the courtyard outlines,
    used for BOTH the raster mask and the polyline measurement, so the search
    and the proof cannot disagree about where a courtyard is.  Its boundary
    counts as OUTSIDE, which is the conservative direction: KiCad matches a
    track whose copper merely touches the courtyard, so a centreline held
    strictly inside is a subset of what the rule allows.
    """

    def __init__(self, min_w, refs, polys, max_nm):
        self.min_w, self.refs, self.max_nm = min_w, tuple(refs), max_nm
        self.polys = polys
        self.outlines = []          # (xs, ys, bbox) per closed outline
        for poly in polys.values():
            for k in range(poly.OutlineCount()):
                ch = poly.Outline(k)
                n = ch.PointCount()
                if n < 3:
                    continue
                xs = np.empty(n, dtype=float)
                ys = np.empty(n, dtype=float)
                for t in range(n):
                    p = ch.CPoint(t)
                    xs[t], ys[t] = float(p.x), float(p.y)
                self.outlines.append(
                    (xs, ys, (xs.min(), ys.min(), xs.max(), ys.max())))

    def width_for(self, pad):
        """The narrowest width this pad may launch at, or None if it may not."""
        return self.min_w if self.contains(pad['x'], pad['y']) else None

    def contains(self, x, y):
        return bool(self.mask(np.array([[float(x)]]),
                              np.array([[float(y)]]))[0, 0])

    def mask(self, X, Y):
        """Which of these points lie strictly inside a named courtyard."""
        X = np.asarray(X, dtype=float)
        Y = np.asarray(Y, dtype=float)
        res = np.zeros(X.shape, dtype=bool)
        for xs, ys, (bx0, by0, bx1, by1) in self.outlines:
            if (X.max() < bx0 or X.min() > bx1 or
                    Y.max() < by0 or Y.min() > by1):
                continue
            hit = np.zeros(X.shape, dtype=bool)
            x2, y2 = np.roll(xs, -1), np.roll(ys, -1)
            for a in range(len(xs)):
                xa, ya, xb, yb = xs[a], ys[a], x2[a], y2[a]
                if ya == yb:
                    continue
                span = (ya > Y) != (yb > Y)
                if not span.any():
                    continue
                xint = xa + (Y - ya) * (xb - xa) / (yb - ya)
                hit ^= span & (X < xint)
            res |= hit
        return res

    def outside(self, pts, step=25000):
        """Length of this polyline, in nm, that lies OUTSIDE every named courtyard.

        Sampled at 0.025 mm, a quarter of the finest lattice the escape search
        uses, so a segment cannot leave and re-enter between two samples at any
        scale a courtyard is drawn at.  The raster mask already keeps the
        wavefront inside; this catches the one thing a per-cell mask cannot --
        a straight segment between two inside cells that bulges out across a
        re-entrant courtyard edge -- and it is a GATE, not a note: a polyline
        that strays at all is refused.
        """
        total = 0.0
        for a, b in zip(pts, pts[1:]):
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            if d == 0:
                continue
            n = max(1, int(math.ceil(d / step)))
            t = (np.arange(n) + 0.5) / float(n)
            xs = a[0] + (b[0] - a[0]) * t
            ys = a[1] + (b[1] - a[1]) * t
            total += float(np.count_nonzero(~self.mask(xs, ys))) * d / n
        return total


_NECK_RE = re.compile(
    r'\(rule\s+"([^"]*)"\s*\(constraint\s+track_width\s*\(min\s+'
    r'([0-9.]+)mm\)\s*\)\s*\(condition\s+"([^"]*)"\)\s*\)', re.S)


def neck_rule(qb, max_mm=NECK_MAX_MM):
    """Read the pad-escape necking allowance out of the board's `.kicad_dru`.

    Accepts ONLY a `track_width (min ...)` rule whose condition is a pure
    disjunction of `A.intersectsCourtyard('REF')` terms -- the shape of the
    pad-escape rule and of nothing else in this file.  A rule with any other
    term (a net, a class, a B-side clause) is ignored rather than guessed at, so
    a future edit that broadens the condition cannot silently broaden the
    router.  Returns None when the board carries no such rule.
    """
    dru = Path(qb.b.GetFileName()).with_suffix('.kicad_dru')
    if not dru.exists():
        return None
    text = dru.read_text(encoding='utf-8')
    best = None
    for name, mm, cond in _NECK_RE.findall(text):
        terms = [t.strip() for t in cond.split('||')]
        refs = []
        for t in terms:
            m = re.fullmatch(r"A\.intersectsCourtyard\('([^']+)'\)", t)
            if m is None:
                refs = None
                break
            refs.append(m.group(1))
        if refs:
            best = (name, int(round(float(mm) * qr.MM)), refs)   # LAST wins
    if best is None:
        return None
    _, min_w, refs = best
    polys = {}
    for f in qb.b.GetFootprints():
        ref = f.GetReference()
        if ref in refs:
            polys[ref] = f.GetCourtyard(f.GetLayer())
    if not polys:
        return None
    return Neck(min_w, refs, polys, int(round(max_mm * qr.MM)))


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
def dru_overlay(qb, net, mycls, cls, layer, width, clr_pad, clr_trk,
                ox, oy, G, nx, ny):
    """Cells blocked by a .kicad_dru clearance `QBoard.margin` cannot see.

    Everything except the clearance number -- the obstacle set, the exact
    shape distance, the 0.75-cell guard band -- is exactly what `QBoard.grid`
    does, so this can only ever ADD blocked cells to it.  An obstacle whose
    required clearance does not EXCEED the base is skipped outright, which
    keeps the overlay empty for the common net.

    It is a module function rather than a `Field` method because the pocket
    escape (`_pocket_escapes`) rasterises a SMALL window at a FINER pitch and
    owes that window exactly the same overlay: one implementation, so a lattice
    can never be built to a weaker rule than the whole-board one.
    """
    blk = np.zeros((ny, nx), dtype=bool)
    guard = G * 0.75
    for s in qb.obstacles(layer, net):
        if not s.net:
            continue                          # keep-out: no clearance concept
        kind = _kind(s)
        if kind == 'ko':
            continue
        base = clr_trk if kind == 'track' else clr_pad
        ocls = cls.get(s.net, 'Default')
        req = base
        if kind != 'pad':                     # rule (a): both sides routed
            req = max(req, CLASS_TRK_CLR.get(ocls, 0),
                      CLASS_TRK_CLR.get(mycls, 0))
        req = max(req,                        # rule (b): one side routed
                  PAIR_CLR.get((ocls, mycls), 0),
                  PAIR_CLR.get((mycls, ocls), 0))
        if req <= base:
            continue
        mm_ = width / 2.0 + req + guard
        bx0, by0, bx1, by1 = s.bbox(mm_)
        i0 = max(0, int(math.floor((bx0 - ox) / G)))
        i1 = min(nx - 1, int(math.ceil((bx1 - ox) / G)))
        j0 = max(0, int(math.floor((by0 - oy) / G)))
        j1 = min(ny - 1, int(math.ceil((by1 - oy) / G)))
        if i1 < i0 or j1 < j0:
            continue
        X, Y = np.meshgrid((ox + np.arange(i0, i1 + 1) * G).astype(float),
                           (oy + np.arange(j0, j1 + 1) * G).astype(float))
        blk[j0:j1 + 1, i0:i1 + 1] |= (s.dist_np(X, Y) < mm_)
    return blk


class Field(object):
    """The blocked/via-legal lattice for ONE net at ONE width, whole board.

    Built once per (net, width, via) triple and reused by every join on that
    net, because the expensive part -- rasterising ~2,600 obstacle shapes onto
    six layers -- does not depend on the endpoints.
    """

    def __init__(self, qb, net, width, clr_pad, clr_trk, via_dia, via_drill,
                 G=100000, layers=None, margin_mm=2.0, neck=None):
        self.qb, self.net, self.G = qb, net, G
        # OFF unless the caller hands in a `Neck`.  Nothing below reads it
        # except `pad_escapes`, and only for a pad that has NO full-width
        # escape at all, so a `Field` built without one is byte-identical.
        self.neck = neck
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
        """This Field's view of `dru_overlay` -- see the module function."""
        return dru_overlay(self.qb, self.net, self.mycls, self.cls, layer,
                           width, self.clr_pad, self.clr_trk,
                           self.ox, self.oy, self.G, self.nx, self.ny)

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
# analytic proof of emitted geometry
# --------------------------------------------------------------------------- #
# THE LATTICE PROVES CELLS.  THE BOARD CARRIES SEGMENTS.
#
# `QBoard.grid` widens every obstacle by a 0.75-cell guard band precisely so
# that the CONTINUOUS segment between two proved cells cannot reach an obstacle
# the cells themselves clear.  That is sound for a step of the wavefront, which
# is one cell long.  It is NOT sound for the output of `QBoard.smooth`, which
# replaces a staircase with a single straight run tens of cells long and
# accepts it on the evidence of `QBoard.clear_line` -- and `clear_line` samples
# the run twice per cell and ROUNDS each sample to the nearest lattice cell.
# A long, shallow diagonal therefore has its samples rounded back onto cells
# that are free while the line itself grazes a cell that is not.
#
# The first whole-board GND stitch produced exactly four of these out of 205
# islands: four 0.30 mm GND runs sitting 0.175 mm from a foreign pad on a
# 0.200 mm rule, each 0.025 mm -- a quarter of one lattice cell -- short.
#
# `verify_laid` closes the loop by re-proving every object a transaction has
# just laid ANALYTICALLY, against the same obstacle set and the same clearance
# the search was meant to honour, with no lattice and no guard band in the
# argument.  It is deliberately at least as strict as the raster: `margin()` is
# its floor and the .kicad_dru netclass overlay can only raise it.  So it can
# never admit copper the lattice would have refused, and a transaction it
# rejects is reverted whole -- the caller loses that island or that join, and
# the board never sees geometry that has not been proved as geometry.
def obs_clearance(qb, field, s, width):
    """The clearance this net owes ONE obstacle for `width` copper.

    `QBoard.margin` is the floor.  The two netclass-keyed .kicad_dru families a
    single per-net scalar cannot express -- `CLASS_TRK_CLR` and `PAIR_CLR` --
    raise it by exactly the rule `dru_overlay` rasterises, so the analytic test
    and the lattice cannot disagree about WHICH rule applies.
    """
    req = qb.margin(s, width, field.clr_pad, field.clr_trk)
    kind = _kind(s)
    if not s.net or kind == 'ko':
        return req
    base = field.clr_trk if kind == 'track' else field.clr_pad
    ocls = field.cls.get(s.net, 'Default')
    extra = base
    if kind != 'pad':                     # rule (a): both sides routed copper
        extra = max(extra, CLASS_TRK_CLR.get(ocls, 0),
                    CLASS_TRK_CLR.get(field.mycls, 0))
    extra = max(extra,                    # rule (b): one side routed copper
                PAIR_CLR.get((ocls, field.mycls), 0),
                PAIR_CLR.get((field.mycls, ocls), 0))
    return max(req, width / 2.0 + extra)


def _near(qb, field, layer, x0, y0, x1, y1, slack):
    """Obstacles on `layer` whose expanded bbox can touch this segment.

    One linear pass over the layer's shapes per verified transaction.  The
    exact test is only ever run on what survives, which is what keeps a
    per-island proof affordable at two hundred islands.
    """
    out = []
    for s in qb.obstacles(layer, field.net):
        bx0, by0, bx1, by1 = s.bbox(slack)
        if (min(x0, x1) > bx1 or max(x0, x1) < bx0 or
                min(y0, y1) > by1 or max(y0, y1) < by0):
            continue
        out.append(s)
    return out


def _lname(qb, lid):
    for k, v in qr.LNAME.items():
        if v == lid:
            return k
    return None


def verify_laid(qb, field, mark):
    """Re-prove every object laid since `mark`.  None when clean.

    Returns dict(kind, ...) naming the first object that fails, so the caller
    can report WHY it reverted rather than merely that it did.

    NOTHING IS EXEMPT.  A track segment that lies wholly inside the pad it
    leaves looks like copper the board already carries, and it was briefly
    treated as such -- but KiCad does not see it that way.  A 0.35 mm-tall pad
    on 0.50 mm pitch tolerates its 0.150 mm neighbour gap under the footprint's
    own pad-to-pad allowance, while a 0.30 mm track drawn down the middle of
    that same pad is a TRACK and owes the full 0.200 mm routed clearance, which
    at 0.175 mm it does not meet.  The first whole-board GND stitch produced
    exactly three of those, one each at `U18.4`, `U13.4` and `U21.4`, and all
    three were real DRC errors.  An island whose escape cannot be proved as a
    track is simply not stitched; the other two hundred are unaffected.
    """
    laid = qb.laid[mark[0]:]
    if not laid:
        return None
    tracks, vias = [], []
    for t in laid:
        if t.GetClass() == 'PCB_VIA':
            vias.append(t)
        else:
            tracks.append(t)

    for t in tracks:
        L = _lname(qb, t.GetLayer())
        if L is None:
            return dict(kind='track', why='unmapped layer %d' % t.GetLayer())
        a, b = t.GetStart(), t.GetEnd()
        w = float(t.GetWidth())
        half = w / 2.0
        for (x, y) in ((a.x, a.y), (b.x, b.y)):
            if (x < qb.ex0 + qr.EDGE_CLR + half or
                    x > qb.ex1 - qr.EDGE_CLR - half or
                    y < qb.ey0 + qr.EDGE_CLR + half or
                    y > qb.ey1 - qr.EDGE_CLR - half):
                return dict(kind='track', layer=L, why='board edge clearance',
                            at=(round(x / 1e6, 4), round(y / 1e6, 4)))
        slack = half + max(field.clr_pad, field.clr_trk) + 500000
        for s in _near(qb, field, L, a.x, a.y, b.x, b.y, slack):
            need = obs_clearance(qb, field, s, w)
            bx0, by0, bx1, by1 = s.bbox(need)
            if (min(a.x, b.x) > bx1 or max(a.x, b.x) < bx0 or
                    min(a.y, b.y) > by1 or max(a.y, b.y) < by0):
                continue
            d = qr.seg_shape_dist(a.x, a.y, b.x, b.y, s)
            if d < need:
                return dict(kind='track', layer=L,
                            at=(round(a.x / 1e6, 4), round(a.y / 1e6, 4)),
                            to=(round(b.x / 1e6, 4), round(b.y / 1e6, 4)),
                            against=(s.net or 'keep-out'), tag=s.tag,
                            gap_mm=round((d - half) / 1e6, 4),
                            need_mm=round((need - half) / 1e6, 4))

    for v in vias:
        pos = v.GetPosition()
        dia, drill = float(v.GetWidth()), float(v.GetDrill())
        for L in qb.cu:
            for s in _near(qb, field, L, pos.x, pos.y, pos.x, pos.y,
                           dia / 2.0 + max(field.clr_pad, field.clr_trk)
                           + 500000):
                need = obs_clearance(qb, field, s, dia)
                if s.dist(pos.x, pos.y) < need:
                    return dict(kind='via', layer=L,
                                at=(round(pos.x / 1e6, 4),
                                    round(pos.y / 1e6, 4)),
                                against=(s.net or 'keep-out'), tag=s.tag)
        # HOLE TO HOLE HAS NO SAME-NET EXEMPTION -- it is a drill rule.
        for h in qb.holes:
            if h.cx == pos.x and h.cy == pos.y:
                continue                  # this barrel's own hole
            need = drill / 2.0 + h.r + HOLE_CLR
            if math.hypot(h.cx - pos.x, h.cy - pos.y) < need:
                return dict(kind='via', why='hole-to-hole',
                            at=(round(pos.x / 1e6, 4), round(pos.y / 1e6, 4)),
                            against=(h.net or '?'), tag=h.tag)
    return None


# --------------------------------------------------------------------------- #
# escapes
# --------------------------------------------------------------------------- #
# A pad that reports NO LEGAL ESCAPE is very often not enclosed at all.
# `QBoard.escape` casts ONE STRAIGHT stub along eight rays and fixes its length
# at `pad extent + clearance + half-width + slack`, the shortest slack being
# 0.15 mm.  Two independent things go wrong with that in a dense pocket:
#
#   * the stub is FORCED PAST the first obstacle it could legally stop short
#     of.  `U14.7` (`I2C_SCL_INT`, a 0.50 mm-pitch WSON on the west edge) has
#     exactly one open side, east, and a foreign `BAT_PROT_SHDN_CTL` track
#     crossing 0.75 mm east of it.  A launch point 0.40 mm east clears both the
#     0.35 mm-away neighbour pads AND that track at the full 0.200 mm rule; the
#     mandatory 0.80 mm stub does not, so the pad is reported enclosed.
#   * a straight stub cannot TURN.  The way out of a pin field is usually one
#     short run and a bend, which no ray in any ray set can express.
#
# `_pocket_escapes` replaces the ray cast with a LOCAL WAVEFRONT: a few
# millimetres of board around the terminal, rasterised by the SAME
# `QBoard.grid` and the SAME `dru_overlay` at a QUARTER of the routing pitch,
# walked by the SAME 8-connected no-corner-cutting step the trunk uses, and
# terminated on any cell the WHOLE-BOARD lattice already calls free.  It hands
# the global wavefront a genuinely free seed plus the polyline that reaches it.
#
# Two things make it sound rather than merely permissive:
#
#   * the finer pitch shrinks only the RASTERISATION GUARD BAND (0.75 cell),
#     never a clearance.  At 0.100 mm a cell needs 0.375 mm from a 0.200 mm-rule
#     pad; the lane down the middle of a 0.50 mm-pitch pin field offers 0.350 mm
#     and is therefore reported blocked, though a 0.200 mm track fits it with
#     0.200 mm to spare.  At 0.025 mm the guard is 0.019 mm and the same lane is
#     correctly open.  The DRU clearance itself is untouched.
#   * the seed cells are the pad's OWN CORE -- the points at least half a track
#     width inside its own shape.  That is a CONNECTIVITY guarantee only: a
#     polyline starting there terminates inside the pad, so KiCad joins it, and
#     no separate centre stub is needed.  It is NOT a clearance licence.  Every
#     emitted segment, the first one included, is held to the full routed rule
#     by `_stub_legal` before it is chosen and by `verify_laid` after it is
#     laid; every cell after the first is a genuinely free lattice cell.
#
# This is strictly additive.  `QBoard.escape` is still asked first and its
# answers are still taken in its own order, so no route that exists today is
# changed; a pocket escape only ever ADDS a launch option.
ESCAPE_SUB = 4                  # local lattice pitch = G / ESCAPE_SUB
ESCAPE_WIN_MM = 4.0             # half-window of board around the terminal
ESCAPE_SPREAD_MM = 0.6          # keep returned launch points this far apart


def _pad_core(pad, X, Y, half):
    """Mask of window points at least `half` inside the pad's own shape.

    A track between two of these is contained in the pad's existing copper, so
    it adds no copper anywhere and cannot violate a clearance.  Rounded corners
    are handled by testing the INNER box and adding the corner radius back,
    which is exact for a roundrect and conservative for anything else.
    """
    a = math.radians(pad['ang'])
    ca, sa = math.cos(a), math.sin(a)
    ax = np.abs((X - pad['x']) * ca + (Y - pad['y']) * sa)
    ay = np.abs(-(X - pad['x']) * sa + (Y - pad['y']) * ca)
    ihx, ihy = max(pad['hx'] - pad['r'], 0.0), max(pad['hy'] - pad['r'], 0.0)
    depth = pad['r'] + np.minimum(ihx - ax, ihy - ay)
    return (ax <= ihx) & (ay <= ihy) & (depth >= half)


def _pocket_escapes(qb, field, pad, layer, prefer, limit, width=None,
                    confine=None):
    """Walk one terminal out of its pocket on a local, finer lattice.

    Returns launch points that are FREE on the whole-board lattice, each with
    the `path` (an nm polyline starting at the pad centre) that reaches it.

    `width` is the width the STUB is drawn at and defaults to the trunk width.
    Passing a narrower one is the pad-escape neck: only the local raster, the
    obstacle clearances, the pad core and the analytic stub proof move to that
    width -- the GOAL TEST does not, so a launch point is still only accepted
    where the whole-board FULL-WIDTH lattice is free and the trunk therefore
    leaves the neck at the contract width.  `confine`, when given, is a `Neck`
    whose named courtyards every point of the emitted stub must lie inside; it
    masks the raster AND gates the emitted polyline, because the board's rule
    only licences the neck where the copper is.
    """
    w = field.width if width is None else width
    G, sub = field.G, ESCAPE_SUB
    g = max(1, G // sub)
    if g * sub != G:
        return []
    ci, cj = field.cell(pad['x'], pad['y'])
    r = int(math.ceil(ESCAPE_WIN_MM * qr.MM / float(G)))
    i0, i1 = max(0, ci - r), min(field.nx - 1, ci + r)
    j0, j1 = max(0, cj - r), min(field.ny - 1, cj + r)
    if i1 - i0 < 2 or j1 - j0 < 2:
        return []
    ox, oy = field.ox + i0 * G, field.oy + j0 * G
    x1, y1 = field.ox + i1 * G, field.oy + j1 * G
    nx, ny = (i1 - i0) * sub + 1, (j1 - j0) * sub + 1
    blk = (qb.grid(layer, field.net, w, field.clr_pad, field.clr_trk,
                   ox, oy, x1, y1, g)
           | dru_overlay(qb, field.net, field.mycls, field.cls, layer,
                         w, field.clr_pad, field.clr_trk,
                         ox, oy, g, nx, ny))
    if blk.shape != (ny, nx):
        return []
    # obstacles that can possibly touch this window, each with the clearance
    # `obs_clearance` says this net owes it -- the same number `verify_laid`
    # will re-prove the emitted polyline against, so the window search and the
    # final proof cannot disagree.
    obs = []
    for s in qb.obstacles(layer, field.net):
        req = obs_clearance(qb, field, s, w)
        bx0, by0, bx1, by1 = s.bbox(req)
        if bx1 < ox or bx0 > x1 or by1 < oy or by0 > y1:
            continue
        obs.append((s, req))
    X, Y = np.meshgrid((ox + np.arange(nx) * g).astype(float),
                       (oy + np.arange(ny) * g).astype(float))
    core = _pad_core(pad, X, Y, w / 2.0)
    si, sj = int(round((pad['x'] - ox) / g)), int(round((pad['y'] - oy) / g))
    if not (0 <= si < nx and 0 <= sj < ny):
        return []
    core[sj, si] = True             # the centre always anchors the connection
    free = (~blk) | core
    if confine is not None:
        # The necking rule matches only copper that meets a named courtyard, so
        # the wavefront is not merely SCORED for staying inside one -- it is
        # confined to it.  The pad's own core still anchors the stub: it is the
        # footprint's land and lies inside its own courtyard by construction,
        # and excluding it would leave the search with nowhere to start.
        free &= confine.mask(X, Y) | core

    # goal cells: whole-board lattice cells this window contains that the
    # GLOBAL grid already calls free -- the seed the trunk wavefront wants.
    goal = np.zeros((ny, nx), dtype=bool)
    goal[::sub, ::sub] = ~field.blk[layer][j0:j1 + 1, i0:i1 + 1]
    goal &= free
    goal &= ~core                   # a launch point must be OUT of the pad

    dist = np.full((ny, nx), -1, dtype=np.int32)
    cur = core & free
    dist[cur] = 0
    hits = []
    for d in range(1, (max(nx, ny) + 1) * 2):
        nxt = _shift_or(cur, free) & free & (dist < 0)
        if not nxt.any():
            break
        dist[nxt] = d
        got = nxt & goal
        if got.any():
            js, iss = np.nonzero(got)
            hits += [(d, int(a), int(b)) for a, b in zip(iss, js)]
            if len(hits) >= limit * 24:
                break
        cur = nxt
    if not hits:
        return []

    px = py = None
    if prefer is not None and math.hypot(*prefer) > 0:
        n = math.hypot(*prefer)
        px, py = prefer[0] / n, prefer[1] / n

    def rank(h):
        d, i, j = h
        if px is None:
            return (d, i, j)
        dx, dy = ox + i * g - pad['x'], oy + j * g - pad['y']
        n = math.hypot(dx, dy) or 1.0
        return (d, -(dx / n * px + dy / n * py), i, j)

    hits.sort(key=rank)
    spread = ESCAPE_SPREAD_MM * qr.MM
    out, taken = [], []
    for d, i, j in hits:
        x, y = ox + i * g, oy + j * g
        if any(math.hypot(x - a, y - b) < spread for a, b in taken):
            continue
        cells = _descend_local(dist, i, j)
        if cells is None:
            continue
        b2 = blk.copy()
        for (a, b) in (cells[0], cells[-1]):
            b2[b, a] = False
        pts = qr.simplify(qb.smooth(b2, cells), ox, oy, g)
        # `pts[0]` is a cell of the pad's OWN CORE -- at least half a track
        # width inside its shape -- so the polyline already terminates inside
        # the pad and KiCad's connectivity engine joins it there.  Do NOT
        # prepend the pad centre: that adds a segment which buys no
        # connectivity and must still clear every foreign pad in the pin field.
        if not _stub_legal(qb, field, layer, pts, pad, obs, w):
            continue
        ln = sum(math.hypot(q[0] - t[0], q[1] - t[1])
                 for t, q in zip(pts, pts[1:]))
        rec = dict(x=x, y=y, w=w, ln=ln, path=pts)
        if confine is not None:
            # A necked stub is only as legal as the rule it leans on.  Bound it
            # in length -- the hits are already shortest-first, so this refuses
            # exactly the long ones -- and REFUSE it outright if any part of the
            # continuous polyline lies outside the courtyard that licences it,
            # which the per-cell mask alone cannot rule out across a re-entrant
            # edge.  This is the check whose absence cost D-584 three real
            # `track_width` DRC errors.
            if ln > confine.max_nm:
                continue
            strayed = confine.outside(pts)
            if strayed > 0:
                continue
            rec['neck'] = True
            rec['neck_outside_mm'] = round(strayed / 1e6, 4)
        taken.append((x, y))
        out.append(rec)
        if len(out) >= limit:
            break
    return out


def _stub_legal(qb, field, layer, pts, pad, obs, width=None):
    """Re-prove an emitted pocket polyline ANALYTICALLY, segment by segment.

    The wavefront proved LATTICE CELLS clear; this proves the CONTINUOUS
    segments between them, against the same obstacle set and the same
    `QBoard.margin` that `QBoard.escape` uses on its straight stub.  EVERY
    segment is held to the full rule, including the one that starts inside the
    pad's own copper -- see `verify_laid` for why that segment is not special.
    Rejecting here rather than at emission time is what lets `_pocket_escapes`
    fall through to its next candidate instead of losing the terminal.
    """
    half = (field.width if width is None else width) / 2.0
    for a, b in zip(pts, pts[1:]):
        if a == b:
            continue
        for (x, y) in (a, b):
            if (x < qb.ex0 + qr.EDGE_CLR + half or
                    x > qb.ex1 - qr.EDGE_CLR - half or
                    y < qb.ey0 + qr.EDGE_CLR + half or
                    y > qb.ey1 - qr.EDGE_CLR - half):
                return False
        for s, req in obs:
            bx0, by0, bx1, by1 = s.bbox(req)
            if (min(a[0], b[0]) > bx1 or max(a[0], b[0]) < bx0 or
                    min(a[1], b[1]) > by1 or max(a[1], b[1]) < by0):
                continue
            if qr.seg_shape_dist(a[0], a[1], b[0], b[1], s) < req:
                return False
    return True


def _descend_local(dist, i, j):
    """Walk a local distance field downhill to a zero cell."""
    cells = [(i, j)]
    ny, nx = dist.shape
    while dist[j, i] > 0:
        want = dist[j, i] - 1
        step = None
        for (dx, dy) in D8:
            vi, vj = i + dx, j + dy
            if 0 <= vi < nx and 0 <= vj < ny and dist[vj, vi] == want:
                step = (vi, vj)
                break
        if step is None:
            return None
        i, j = step
        cells.append((i, j))
    cells.reverse()
    return cells


def emit_escape(qb, net, layer, pad, e):
    """Lay ONE escape -- a straight `QBoard.escape` stub or a pocket polyline.

    Returns the run length in nm.  A degenerate zero-length segment is never
    emitted: a launch point that rounds onto the pad centre needs no copper of
    its own, the trunk already starts inside the pad.  Every segment that IS
    emitted is proved in full by `verify_laid`; none is exempt.
    """
    pts = e.get('path') or [(pad['x'], pad['y']), (e['x'], e['y'])]
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        if a == b:
            continue
        qb.track(net, layer, a[0], a[1], b[0], b[1], e['w'])
        total += math.hypot(b[0] - a[0], b[1] - a[1])
    return total


def pad_escapes(qb, field, pad, toward, limit=8, pocket=True):
    """Legal launch points for one pad, on every outer layer it lives on.

    `QBoard.escape` is asked FIRST and its answers are kept in its own order --
    it owns PR-5B (never narrower than the rule minimum) and PR-5C (the stub is
    analytically cleared against the same obstacle set as the trunk).
    `_pocket_escapes` then ADDS the launch points a straight stub of fixed
    length cannot reach.  Returns a list of dict(layer, x, y, w, ln, pad, i, j)
    with an optional `path` polyline.
    """
    out = []
    for L in ('F', 'B'):
        if L not in field.layers or not pad.get(L):
            continue
        prefer = None
        if toward is not None:
            prefer = (toward[0] - pad['x'], toward[1] - pad['y'])
        cands = list(qb.escape(pad, L, field.width, field.width, field.clr_pad,
                               field.clr_trk, field.G, field.ox, field.oy,
                               prefer=prefer)[:limit])
        seen = set((c['x'], c['y']) for c in cands)
        if pocket:
            for c in _pocket_escapes(qb, field, pad, L, prefer, limit):
                if (c['x'], c['y']) not in seen:
                    seen.add((c['x'], c['y']))
                    cands.append(c)
        # PAD-ESCAPE NECKING, LAST RESORT ONLY.  A pad that already launches
        # at the contract width launches exactly as it did before; the neck is
        # offered only for a (pad, layer) whose full-width set is EMPTY, which
        # is the case the `.kicad_dru` rule was written for and the only case
        # in which this can change an outcome.
        if not cands and field.neck is not None:
            wn = field.neck.width_for(pad)
            if wn is not None and wn < field.width:
                cands = _pocket_escapes(qb, field, pad, L, prefer, limit,
                                        width=wn, confine=field.neck)
        for c in cands:
            i, j = field.cell(c['x'], c['y'])
            if not field.inside(i, j):
                continue
            e = dict(layer=L, x=c['x'], y=c['y'], w=c['w'],
                     ln=c['ln'], pad=pad, i=i, j=j)
            if c.get('path'):
                e['path'] = c['path']
            if c.get('neck'):
                e['neck'] = True
                e['neck_outside_mm'] = c['neck_outside_mm']
            out.append(e)
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
    total += emit_escape(qb, net, start['layer'], start['pad'], start)
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
    total += emit_escape(qb, net, finish['layer'], finish['pad'], finish)
    # THE SMOOTHER IS NOT A PROOF.  Re-prove the emitted geometry analytically
    # and drop the join whole if any segment or barrel fails; a join that
    # cannot be proved as geometry must not reach the gate as copper.
    bad = verify_laid(qb, field, m)
    if bad is not None:
        qb.revert(m)
        return dict(ok=False, reason='UNPROVED_GEOMETRY', detail=bad)
    # A necked terminal is the one thing about this join a reviewer must see
    # without opening the board, so it is reported rather than left implicit.
    necks = [dict(pad=e['pad']['ref'], layer=e['layer'],
                  width_mm=round(e['w'] / 1e6, 3),
                  stub_mm=round(e['ln'] / 1e6, 3),
                  outside_courtyard_mm=e.get('neck_outside_mm'))
             for e in (start, finish) if e.get('neck')]
    return dict(ok=True, mm=total / 1e6, vias=len(vias),
                via_xy=[(round(x / 1e6, 4), round(y / 1e6, 4)) for x, y in vias],
                layers=[k for k, _ in polylines],
                **({'necks': necks} if necks else {}),
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


# --------------------------------------------------------------------------- #
# BEST-EFFORT COMPLETION -- the atomic net is not the only honest unit
# --------------------------------------------------------------------------- #
# `route_net` is ATOMIC: one MST edge it cannot corridor reverts every edge of
# that net.  That is the right discipline for a net being routed for the FIRST
# time under its own purpose-built harness, where a half-routed rail is a
# half-designed rail and the reviewer must see the whole proposal or none of it.
#
# It is the wrong discipline for THIS board.  After D-583 the remaining 126
# retained open edges sit on 32 nets, and the D-581 whole-board batch measured
# exactly what atomicity costs: 24 of its 25 nets returned `NO_PATH` or
# `NO_LEGAL_ESCAPE_*` and therefore contributed ZERO copper -- including
# `/I2C_SCL_INT`, a NINE-island bus whose whole proposal was discarded because
# ONE terminal has no legal escape.  Eight edges were thrown away to refuse one.
#
# A partially routed net is not a broken net.  It is the ordinary mid-route
# state of every real board: the closed edges are real copper that the same
# analytic proofs, the same DRC and the same ledger accept, and the open ones
# remain exactly the ratsnest lines they already were.  Nothing regresses, and
# the pads that CAN be joined stop waiting on the pad that cannot.
#
# So the partial mode is not "atomic, relaxed".  It is a different and stronger
# search:
#
#   * KRUSKAL, NOT PRIM.  Atomic mode walks ONE spanning tree and dies on its
#     first bad edge.  Partial mode walks EVERY island pair in increasing
#     pad-gap order under a union-find, so an island whose MST partner is
#     unreachable is still offered every other island on the board.  A net only
#     stops improving when no pair is left, not when one pair fails.
#   * MERGED ENDPOINTS.  After a join succeeds the two islands are ONE island,
#     and the next attempt is handed the union of their pads -- so a component
#     that has grown offers more launch sites than either half did, which is
#     the whole reason to prefer nearest-first.
#   * DEAD-TERMINAL PRUNING.  `NO_LEGAL_ESCAPE_SRC/DST` is a property of the
#     COMPONENT, not of the pair: it means no pad in that component can leave
#     its own pocket at the contract width on any permitted layer.  Laying more
#     copper can only ever remove escapes, never create them, so once a
#     component reports it the component is retired and every remaining pair
#     that touches it is skipped unattempted.  That is what keeps a complete
#     graph affordable, and it is a proof, not a heuristic.
#   * PER-PAIR TRANSACTION.  Each attempt takes its own `qb.mark()`; a failure
#     reverts exactly that attempt.  The board the next attempt searches is the
#     board the previous SUCCESSES left, never one a failure dirtied.
#
# `partial=False` is the default and leaves `route_net` byte-identical, so
# every accepted route and every existing harness is untouched by this lever.


def _partial_join(qb, net, field, islands, escape_limit, via_cost_mm,
                  attempt_cap=0, max_mm=0.0):
    """Join as many of this net's islands as the board actually allows.

    Returns `(joins, failures, components_remaining)`.  Emitted copper stays on
    `qb`; the caller owns no rollback, because every failed attempt has already
    reverted itself.

    A CORRIDOR THAT EXISTS IS NOT AUTOMATICALLY A CORRIDOR WORTH TAKING.

    Kruskal offers every island pair, so when the nearest partner is walled off
    the search keeps widening until SOMETHING connects -- and on this board it
    finds things.  The first whole-board `--partial` run on
    `/01_POWER_TREE/BQ25185_SYS` closed two edges by spending 74.4 mm of copper
    and six barrels, of which ONE join was a 52.6 mm five-layer-change detour
    from `C24.1` to `C33.1`.  That is a legal route and a bad one: `SYS` is the
    charger's 1 A output rail, and 52 mm of 0.80 mm outer copper is roughly
    30 mOhm and some tens of nH in series with the node every downstream
    regulator references, laid across the width of a board whose outer layers
    the unrouted signal nets still need.  The atomic MST never had to say this
    because it only ever offered the SHORTEST spanning edges; Kruskal-to-
    exhaustion does, so the bound belongs here.

    `max_mm` is therefore a per-join ELECTRICAL bound, measured on the copper
    actually laid.  A join that exceeds it is reverted and reported as
    `TOO_LONG` -- reported, so the refusal is visible and the pair can be
    reconsidered deliberately, and NOT retired as dead, because the pair failed
    on length rather than on reachability and a different partner may still be
    close.  `max_mm=0` disables the bound and reproduces the unbounded search
    exactly.
    """
    n = len(islands)
    parent = list(range(n))
    members = {i: list(islands[i]) for i in range(n)}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    pairs = sorted(((_pad_gap(islands[a], islands[b]), a, b)
                    for a in range(n) for b in range(a + 1, n)),
                   key=lambda t: (t[0], t[1], t[2]))
    joins, failures, dead = [], [], set()
    comps, attempts = n, 0
    for _gap, a, b in pairs:
        if comps == 1:
            break
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if ra in dead or rb in dead:
            continue
        if attempt_cap and attempts >= attempt_cap:
            failures.append(dict(reason='ATTEMPT_CAP',
                                 why='stopped after %d join attempts on this '
                                     'net' % attempts))
            break
        attempts += 1
        m = qb.mark()
        r = route_join(qb, field, members[ra], members[rb],
                       escape_limit=escape_limit, via_cost_mm=via_cost_mm)
        r.pop('mark', None)
        if not r.get('ok'):
            qb.revert(m)
            reason = r.get('reason')
            # A component that cannot leave its own pockets is retired, not
            # retried: escapes are computed against FOREIGN copper only, and
            # this run adds copper, so the set of legal escapes is monotonically
            # non-increasing.  Re-offering it a different partner cannot change
            # the answer and would cost one whole-board wavefront to re-learn.
            if reason == 'NO_LEGAL_ESCAPE_SRC':
                dead.add(ra)
            elif reason == 'NO_LEGAL_ESCAPE_DST':
                dead.add(rb)
            failures.append(dict(
                a=[p['ref'] for p in members[ra]][:8],
                b=[p['ref'] for p in members[rb]][:8],
                gap_mm=round(_gap / 1e6, 3),
                **{k: v for k, v in r.items() if k != 'ok'}))
            continue
        if max_mm and r.get('mm', 0.0) > max_mm:
            qb.revert(m)
            failures.append(dict(
                a=[p['ref'] for p in members[ra]][:8],
                b=[p['ref'] for p in members[rb]][:8],
                gap_mm=round(_gap / 1e6, 3), reason='TOO_LONG',
                mm=round(r['mm'], 3), vias=r.get('vias'),
                layers=r.get('layers'),
                why='%.3f mm of copper exceeds the %.1f mm per-join bound'
                    % (r['mm'], max_mm)))
            continue
        parent[ra] = rb
        members[rb] = members[rb] + members[ra]
        members.pop(ra, None)
        comps -= 1
        joins.append({k: v for k, v in r.items() if k != 'ok'})
        # The join laid copper; the next attempt must search the board that
        # copper made, both as obstacle and as new same-net launch surface.
        field.rebuild_blk()
    return joins, failures, comps


def route_net(qb, net, width=200000, clr_pad=200000, clr_trk=200000,
              via_dia=600000, via_drill=300000, G=100000, via_cost_mm=1.5,
              escape_limit=8, field=None, partial=False, attempt_cap=0,
              join_max_mm=0.0):
    """Complete ONE net: island MST, then a whole-board all-layer join per edge.

    Atomic by default: any failed edge reverts every edge of this net, so the
    scratch board never carries a half-routed net into the gate.

    With `partial=True` the net is instead completed BEST-EFFORT by
    `_partial_join` -- a union-find Kruskal over every island pair, each pair in
    its own transaction, with components that cannot escape their own pockets
    retired rather than retried.  The net is reported `ok` only when it actually
    laid copper, so a net that closes nothing still adds nothing and the gate's
    "every added object is on a net that succeeded" clause is unweakened.
    """
    mark = qb.mark()
    if field is None:
        field = Field(qb, net, width, clr_pad, clr_trk, via_dia, via_drill, G)
    islands = net_islands(qb, net)
    if len(islands) < 2:
        return dict(ok=True, net=net, joins=[], already=True, mm=0.0, vias=0)
    if partial:
        joins, failures, comps = _partial_join(
            qb, net, field, islands, escape_limit, via_cost_mm, attempt_cap,
            max_mm=join_max_mm)
        if not joins:
            qb.revert(mark)
            return dict(ok=False, net=net, joins=[], failures=failures[:40],
                        islands=len(islands), closed=0, mode_partial=True,
                        reason=(failures[0].get('reason') if failures
                                else 'NO_PAIR'))
        return dict(ok=True, net=net, joins=joins, islands=len(islands),
                    closed=len(joins), remaining=comps - 1,
                    failures=failures[:40], mode_partial=True,
                    mm=round(sum(j['mm'] for j in joins), 3),
                    vias=sum(j['vias'] for j in joins))
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
    m = qb.mark()
    total = emit_escape(qb, net, L, pad, e)
    for a, b in zip(pts, pts[1:]):
        qb.track(net, L, a[0], a[1], b[0], b[1], field.width)
        total += math.hypot(b[0] - a[0], b[1] - a[1])
    vx, vy = pts[-1]
    qb.via(net, vx, vy, field.via_dia, field.via_drill)
    forbid_via(field, vx, vy)
    # Prove the stub, the run and the barrel analytically.  `stitch_net` owns
    # the revert, so this island simply reports that it could not be proved and
    # the other two hundred are unaffected.
    bad = verify_laid(qb, field, m)
    if bad is not None:
        return dict(ok=False, reason='UNPROVED_GEOMETRY', pad=pad['ref'],
                    why='%s at %s vs %s' % (bad.get('kind'), bad.get('at'),
                                            bad.get('against', bad.get('why'))),
                    detail=bad)
    return dict(ok=True, pad=pad['ref'], layer=L, mm=round(total / 1e6, 3),
                via_xy=(round(vx / 1e6, 4), round(vy / 1e6, 4)))


def _pad_gap(a, b):
    """Closest pad-to-pad distance between two islands."""
    return min(math.hypot(p['x'] - q['x'], p['y'] - q['y'])
               for p in a for q in b)


def nearest_pads(island, other, limit):
    """The `limit` pads of `other` closest to `island`.

    `route_join` opens EVERY legal escape of EVERY pad it is given, so handing
    it the whole 228-pad ground island would spend most of its time enumerating
    launches on the far side of the board.  The wavefront searches from the
    destination side, so a handful of the nearest pads is both the cheap and the
    correct seed set: a corridor that cannot reach any of them is not going to
    be found by adding a ninth one 60 mm further away.
    """
    ranked = sorted(other,
                    key=lambda q: min(math.hypot(p['x'] - q['x'],
                                                 p['y'] - q['y'])
                                      for p in island))
    return ranked[:max(1, limit)]


def join_residual_islands(qb, net, field, escape_limit=8, via_cost_mm=1.5,
                          near=8, max_mm=0.0):
    """Maze-join the islands of a plane-served net that the stitch could not plant.

    `stitch_pad` is deliberately LOCAL: one escape and one through via inside an
    8 mm window.  That is the right primitive for the two hundred islands a
    fresh pour leaves, and it is the wrong one for the handful it cannot serve
    -- a pad with no legal barrel in its window (`NO_VIA_SITE`) may still be two
    millimetres of ordinary track from a pad that is already on the plane, and
    the stitch has no way to express that.  This is that fallback: the SAME
    whole-board all-layer `route_join` the plane-less nets use, aimed at the
    net's own connected copper.

    It keeps `stitch_net`'s transaction discipline rather than `route_net`'s.
    `route_net` is atomic because a half-routed net is a broken net; here the
    net is already served by its pour, so every island is independent and one
    island that cannot reach the copper says nothing about the next.  A failed
    island is reverted on its own and reported.

    `max_mm` bounds the copper ONE island may spend, and it is an ELECTRICAL
    bound, not a tidiness one.  A plane-served island is already served by the
    pour everywhere else; what it is missing is a LOW-IMPEDANCE bond.  A
    decoupling capacitor's ground reached by a forty-millimetre detour is worse
    engineering than the same pad reached by a via, because the detour adds
    inductance exactly where the part exists to remove it -- and it spends
    outer-layer capacity the unrouted signal nets still need.  A join longer
    than the bound is therefore reverted and reported as `TOO_LONG`, with its
    length, so the refusal is visible rather than silent.  `max_mm=0` disables
    the bound.
    """
    islands = net_islands(qb, net)
    if len(islands) < 2:
        return dict(ok=True, net=net, joined=0, already=True, failures=[],
                    mm=0.0, vias=0)
    main = max(islands, key=len)
    # Nearest-first: the cheapest joins also disturb the lattice least, so the
    # ones after them see a board no more congested than it had to become.
    rest = sorted((g for g in islands if g is not main),
                  key=lambda g: _pad_gap(g, main))
    done, failed = [], []
    for island in rest:
        dst = nearest_pads(island, main, near)
        m = qb.mark()
        r = route_join(qb, field, island, dst, escape_limit=escape_limit,
                       via_cost_mm=via_cost_mm)
        r.pop('mark', None)
        if not r.get('ok'):
            qb.revert(m)
            failed.append(dict(island=[p['ref'] for p in island],
                               **{k: v for k, v in r.items() if k != 'ok'}))
            continue
        if max_mm and r.get('mm', 0.0) > max_mm:
            qb.revert(m)
            failed.append(dict(island=[p['ref'] for p in island],
                               reason='TOO_LONG', mm=round(r['mm'], 3),
                               vias=r.get('vias'), layers=r.get('layers'),
                               why='%.3f mm of copper exceeds the %.1f mm '
                                   'residual-join bound' % (r['mm'], max_mm)))
            continue
        done.append(dict(island=[p['ref'] for p in island],
                         **{k: v for k, v in r.items() if k != 'ok'}))
        # The join laid copper; the next island must see it, both as an obstacle
        # and as the reason its own corridor may now be narrower.
        field.rebuild_blk()
    return dict(ok=bool(done), net=net, joined=len(done),
                unreachable=len(failed), joins=done, failures=failed[:40],
                mm=round(sum(d['mm'] for d in done), 3),
                vias=sum(d['vias'] for d in done))


def stitch_net(qb, net, width=200000, clr_pad=200000, clr_trk=200000,
               via_dia=600000, via_drill=300000, G=100000, field=None,
               max_mm=8.0, escape_limit=12, split_islands=False):
    """Stitch every not-yet-planted island of a plane-served net to its plane.

    Unlike `route_net` this is NOT all-or-nothing: each island is an independent
    transaction, because one island that cannot reach the pour says nothing
    about the other two hundred that can.  A failed island is reverted on its
    own and reported; the successful ones stay.

    "TOUCHES A POUR" AND "IS CONNECTED" STOPPED BEING THE SAME QUESTION.

    The default predicate skips any island holding a pad that touches a zone or
    a via, and for the job this function was written for -- planting the two
    hundred islands a FRESH pour leaves -- that is exactly right: copper that
    touches the new pour is served by it, and stitching it again buys a barrel
    and nothing else.

    It stops being right the moment a foreign signal track SPLITS an existing
    pour.  KiCad re-pours around the track, the pour becomes two islands, and
    the pads stranded on the far one still touch a zone -- their own, smaller
    one -- so the default predicate skips precisely the pads that just went
    open.  The first `--repair-planes` run measured this exactly: `GND` lost an
    edge to an `/I2C_SCL_INT` track, the repair ran, and it reported the same
    nine pre-existing hard-wall islands D-583 already knew about and never
    looked at the split at all.

    `split_islands=True` therefore replaces the predicate with the question the
    repair actually asks: `net_islands` is KiCad's own connectivity, so the
    net's LARGEST component is its plane body and every other component is
    disconnected from it whatever copper it happens to sit on.  The body is
    skipped -- stitching it to itself is the redundant barrel the default
    predicate existed to prevent -- and every other island is offered the pour.

    The default is unchanged and the flag is opt-in, so D-579's, D-582's and
    D-583's stitches reproduce object for object.
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
    islands = net_islands(qb, net)
    body = max(islands, key=len) if islands else None
    for island in islands:
        if split_islands:
            if island is body:
                continue
        elif any((p['ref'], p['x'], p['y']) in planted for p in island):
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
