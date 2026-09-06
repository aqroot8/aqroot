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

import collections
import os
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


# --------------------------------------------------------------------------- #
# THE OBSTACLE MODEL IS THE BOARD, OR IT IS NOT A MODEL                 D-645
# --------------------------------------------------------------------------- #
# `qrouter.QBoard._scan` walks `board.GetTracks()` and keeps an object only
# when `t.GetClass() == 'PCB_TRACK'`.  In this KiCad build a through via is a
# `PCB_VIA` -- a DIFFERENT class string -- so every via already on the board is
# skipped: its copper on all six layers and its drilled hole alike.  On the
# D-644 authority that is 799 barrels and 799 drills the proposer cannot see,
# against 3261 tracks and 56 pad holes it can
# (`checks/obstacle_model_contract.py`, `OM1`/`OM2`).
#
# `QBoard.via` -- the emitter, three hundred lines below the scanner -- already
# states what a via IS: copper on every `self.cu` layer plus one `via/hole`.
# This is that same statement applied to the vias the board ALREADY carries, so
# the scanner and the emitter finally agree, and it is deliberately written as
# the emitter's own three lines rather than as a new model of a barrel.
#
# WHY IT IS ENV-GATED AND OFF.  Turning it on can only ADD obstacles, so it can
# only make the search STRICTER: a route that closes today may stop closing,
# and every measurement this board has recorded -- every `NO_PATH`, every
# `NO_VIA_SITE`, every corridor screen -- was taken without it.  Unset
# reproduces all of them byte for byte, which is the same discipline
# `AQROOT_OFFCENTRE_LAUNCH` and `qrouter`'s `AQROOT_D280` are held to.
#
# WHAT IT DOES NOT CHANGE.  A refusal measured WITHOUT the gate is still a
# refusal: the real board can only be harder than the model, never easier.  What
# it changes is the value of a PROPOSAL -- copper laid against the blind model
# may be illegal against a barrel it never saw, and until now the only thing
# that has ever caught that is the gate's own real KiCad DRC on the refilled
# candidate.  On the D-644 board that backstop has held: zero `clearance`
# violations, and all five `hole_clearance` ones are vendor pad-to-NPTH pairs
# inside `MK1` and `J3` that predate every route.  The debt is LATENT and this
# is what stops it being assumed.
SCAN_BOARD_VIAS = 'AQROOT_SCAN_BOARD_VIAS'


def _pcbnew():
    """`pcbnew` is imported lazily everywhere else in this file; same here."""
    import pcbnew
    return pcbnew


def board_via_scan_on(force=None):
    """The EFFECTIVE state of the board-via scan -- the one source of truth.

    D-646.  While the gate was OFF by default, `bool(os.environ.get(...))` was
    the same answer and three files read it that way.  The moment the default
    moved, that expression started reporting the OPPOSITE of what the model
    does, and it did so silently: `obstacle_model_contract`'s OM1/OM2 read
    7972/7972 and 855/855 -- perfect parity -- while its own OM4 control still
    expected the blind model's deltas and failed the contract on a board that
    had just proved it right.  A default is not a fact about the environment.
    """
    if force is not None:
        return bool(force)
    val = os.environ.get(SCAN_BOARD_VIAS)
    return True if val is None else val not in ("", "0")


def ensure_board_vias(qb, force=None):
    """Put the board's OWN vias into `qb`'s obstacle model.  Idempotent.

    Returns the number of barrels added -- 0 when the gate is unset, when this
    `QBoard` has already been repaired, or when the scanner one day does it
    itself.  Never removes anything and never touches copper: `qb.shapes` and
    `qb.holes` are the two lists every instrument reads, and this appends to
    them exactly what `QBoard.via` appends for a barrel it lays.
    """
    # D-646.  THE DEFAULT IS NOW ON, AND THE GATE THAT MOVED IT IS NAMED.
    # D-645 built this repair env-gated OFF and stated its own condition for
    # flipping it in one sentence: "the next promoting transaction spends the
    # gate and moves the default with it."  D-646 is that transaction -- the
    # `+3V3` `{U4.2,U4.3}` closure was proposed, gated and PROMOTED with
    # `AQROOT_SCAN_BOARD_VIAS=1`, thirteen of thirteen clauses PASS, real
    # KiCad DRC unchanged (five inherited `hole_clearance`, zero `clearance`)
    # -- so from here the model IS the board unless a caller says otherwise.
    # `AQROOT_SCAN_BOARD_VIAS=0` restores the blind model exactly, which is
    # what every pre-D-646 measurement in `evidence/` was taken against and
    # what an A/B against one of them must be run with.
    on = board_via_scan_on(force)
    if not on or getattr(qb, '_aqroot_board_vias', None) is not None:
        return 0
    n = 0
    for t in qb.b.GetTracks():
        if t.GetClass() != 'PCB_VIA':
            continue
        x, y = int(t.GetStart().x), int(t.GetStart().y)
        # `PCB_VIA::GetWidth()` asserts without a layer argument in this build;
        # a THROUGH via is one diameter on every copper layer, so `F.Cu` is the
        # answer and it is the layer `QBoard.via` sets first.
        try:
            dia = float(t.GetWidth(_pcbnew().F_Cu))
        except TypeError:
            dia = float(t.GetWidth())
        drill = float(t.GetDrillValue())
        net = t.GetNetname()
        for L in qb.cu:
            qb.shapes[L].append(qr.RR(x, y, dia / 2.0, dia / 2.0, dia / 2.0,
                                      0, net, 'via'))
        qb.holes.append(qr.RR(x, y, drill / 2.0, drill / 2.0, drill / 2.0,
                              0, net, 'via/hole'))
        n += 1
    qb._aqroot_board_vias = n
    qb._obs_cache = None
    return n


class Field(object):
    """The blocked/via-legal lattice for ONE net at ONE width, whole board.

    Built once per (net, width, via) triple and reused by every join on that
    net, because the expensive part -- rasterising ~2,600 obstacle shapes onto
    six layers -- does not depend on the endpoints.
    """

    def __init__(self, qb, net, width, clr_pad, clr_trk, via_dia, via_drill,
                 G=100000, layers=None, margin_mm=2.0, neck=None, guard=None,
                 escape_floor=None):
        # D-645.  The model is the board, or it is not a model.  ON by
        # default since D-646 spent a promoting gate on it; idempotent per
        # `QBoard`, and `AQROOT_SCAN_BOARD_VIAS=0` reproduces every
        # pre-D-646 `Field` byte for byte.
        ensure_board_vias(qb)
        self.qb, self.net, self.G = qb, net, G
        # OFF unless the caller hands in a `Neck`.  Nothing below reads it
        # except `pad_escapes`, and only for a pad that has NO full-width
        # escape at all, so a `Field` built without one is byte-identical.
        self.neck = neck
        # POUR-BOND GUARD.  `guard` is {layer: [(x, y, keepout_nm), ...]} --
        # the tubes `pour_bond_guard.py` proved are the ONLY copper joining a
        # pad to its pour, on a layer this net may route on.  OFF unless the
        # caller hands one in, and a `Field` built without one is
        # byte-identical: `_guard_masks` returns {} and every consumer below
        # is keyed on membership, never on a False array.
        self.guard = guard or {}
        self.width, self.clr_pad, self.clr_trk = width, clr_pad, clr_trk
        # ESCAPE FLOOR -- D-630.  `QBoard.escape` takes a TRUNK width and a
        # RULE MINIMUM as two arguments and walks a descending width ladder
        # between them, keeping the WIDEST rung that fits and refusing any
        # launch point where the TRUNK width is not also legal
        # (`trunk cannot start here`).  This file has always passed
        # `field.width` for BOTH, which collapses that ladder to a single rung
        # -- so a land that cannot launch its netclass width has been reported
        # `NO LEGAL ESCAPE` without the router ever asking for a width the
        # board itself publishes as legal.
        #
        # `.kicad_dru` section 5 states a `min` and an `opt` for every power
        # class; the `.kicad_pcb` netclass carries the `opt`, and
        # `net_contract` takes `max()` of the two, so the router routes at the
        # OPTIMUM and treats it as a floor.  `DRU_CLASS` already records the
        # real `min` for every class that has one, and `route_maze_batch.py`
        # has carried a `width_cap` for `NFC_RF` since the first `U9` fanout
        # for exactly this reason, written out at length: "the netclass asks
        # for 0.400 mm -- the DRU's `opt` -- so `max()` made this class
        # UNLAUNCHABLE FROM THE PART IT SERVES".  That is one class's version
        # of a board-wide fact.
        #
        # OFF unless the caller hands one in, and a `Field` built without one
        # is byte-identical: the floor defaults to the trunk width, which is
        # the pair of arguments this file has always passed.  A caller may
        # only ever descend to a width the `.kicad_dru` PUBLISHES for that
        # class -- never to board setup's `min_track_width` -- so the lever
        # cannot propose copper KiCad's own DRC would refuse, and a class the
        # DRU does not price (`GND` and every signal class) does not move.
        self.escape_floor = min(width, escape_floor or width)
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
        # D-633.  OFF by default and therefore a proven no-op: `pad_escapes`
        # consults the off-centre source ONLY for a (pad, layer) whose ordinary
        # candidate set is EMPTY, and only when this is set.  A land that
        # launches today launches identically, on every instrument.
        #
        # ENV-GATED, like `AQROOT_D280` in `qrouter`, because
        # `route_maze_batch` re-invokes ITSELF as a subprocess: an environment
        # gate crosses that boundary with no new flag on either side, and a
        # caller that wants the lever for one field only still just assigns
        # `field.offcentre = True`.  Unset reproduces every run this board has
        # ever made, byte for byte.
        self.offcentre = bool(os.environ.get('AQROOT_OFFCENTRE_LAUNCH'))
        self.blk = {}
        self._guard = self._guard_masks()
        self.rebuild_blk()
        self.via_ok = self._via_grid()
        # A through via is copper on EVERY layer, so a barrel dropped anywhere
        # inside a guarded tube slots that tube exactly as a track would.  The
        # guard is therefore ANDed out of the via lattice once, here: `via_ok`
        # is built once and only ever narrowed afterwards (`forbid_via`), so
        # one application holds for the life of the Field.
        #
        # AND IT IS THE BARREL'S OWN MASK, NOT THE TRACK'S -- D-610.  This used
        # to reuse `self._guard`, whose radius carries `self.width / 2`.  A
        # 0.65 mm barrel is more than three times as wide as a 0.20 mm track
        # and its antipad is on EVERY layer, so the track mask let a barrel
        # sit where its own copper cannot fit.  MEASURED: with the `U12.1`
        # bond tube in force at a 0.275 mm keepout, the `U12` `VOUT` relief
        # planted a 0.65 mm barrel 0.5315 mm from the tube -- clear of the
        # 0.475 mm the TRACK mask asked for, 0.0685 mm inside the 0.600 mm the
        # BARREL owes -- KiCad's refill ate the tube, and `BQ25185_SYS`
        # `U12.1` came away on a 0.473 mm2 island of its own.  That is the
        # clause-4 regression that refused D-609 and D-610's first two runs.
        for m in self._guard_masks(width=self.via_dia,
                                   layers=set(qb.cu)).values():
            self.via_ok &= ~m

    # -- pour-bond guard ---------------------------------------------------- #
    def _guard_masks(self, width=None, layers=None):
        """Cells this net may not take because a bond tube runs through them.

        The tube itself owes `keepout` -- its own half-width plus the zone
        clearance the pour is filled with -- and THIS net adds its own copper
        half-width and one lattice cell, the same guard band `QBoard.grid`
        widens every other obstacle by, so a straight run `QBoard.smooth`
        accepts between two clear cells cannot graze the tube either.

        `width` and `layers` default to this Field's TRACK width and the layers
        it may route on, which is the only call this method had before D-610.
        The BARREL passes its own diameter and the WHOLE stack: a through via
        is copper on every layer, so it owes a tube on `In2` exactly what it
        owes one on `B`, and it owes it at 0.65 mm rather than at 0.20 mm.
        """
        width = self.width if width is None else width
        layers = self.layers if layers is None else layers
        out = {}
        for L, pts in self.guard.items():
            if L not in layers or not pts:
                continue
            m = np.zeros((self.ny, self.nx), dtype=bool)
            for (x, y, keepout) in pts:
                R = keepout + width / 2.0 + self.G
                i0 = max(0, int(math.floor((x - R - self.ox) / self.G)))
                i1 = min(self.nx - 1, int(math.ceil((x + R - self.ox) / self.G)))
                j0 = max(0, int(math.floor((y - R - self.oy) / self.G)))
                j1 = min(self.ny - 1, int(math.ceil((y + R - self.oy) / self.G)))
                if i1 < i0 or j1 < j0:
                    continue
                X, Y = np.meshgrid(
                    (self.ox + np.arange(i0, i1 + 1) * self.G).astype(float),
                    (self.oy + np.arange(j0, j1 + 1) * self.G).astype(float))
                m[j0:j1 + 1, i0:i1 + 1] |= ((X - x) ** 2 + (Y - y) ** 2) < R * R
            if m.any():
                out[L] = m
        return out

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
            # The guard is re-applied on every rebuild, because `route_net`
            # rebuilds between MST edges and a bond that survived the first
            # edge must survive the second one too.
            if L in self._guard:
                self.blk[L] |= self._guard[L]

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


def verify_laid(qb, field, mark, blame=None):
    """Re-prove every object laid since `mark`.  None when clean.

    Returns dict(kind, ...) naming the first object that fails, so the caller
    can report WHY it reverted rather than merely that it did.

    `blame`, when a list is handed in, additionally receives the OBSTACLE
    OBJECT that failed -- the `RR`/hole this proof measured against, not a
    description of it.  D-647 published a board-wide one-object blame report
    built out of the `why` string above and stated its own limit in the same
    breath: it names the FIRST object the stroke meets, not the only one.  A
    caller that wants the WHOLE set has to hold the named object out and ask
    again, and to do that it needs the object rather than its coordinates.
    Opt-in and additive: the return value is unchanged, so every existing
    caller and every recorded artifact reads exactly as before.

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
                if blame is not None:
                    blame.append(s)
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
                    if blame is not None:
                        blame.append(s)
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
                if blame is not None:
                    blame.append(h)
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
        cands = list(qb.escape(pad, L, field.width, field.escape_floor,
                               field.clr_pad, field.clr_trk, field.G,
                               field.ox, field.oy, prefer=prefer)[:limit])
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
        # THE OFF-CENTRE LAUNCH, LAST RESORT OF ALL.  D-632 measured seven
        # lands that no ray through the pad CENTRE can leave at any width this
        # board can fabricate, and D-633 measured that four of them leave
        # happily from a point 0.04-0.19 mm off it.  Both sources above are
        # centre-anchored: `QBoard.escape` casts its ray from the centre, and
        # `_pocket_escapes` seeds its wavefront on the pad CORE, the cells at
        # least half a track width inside the land -- which on a 0.50 mm-pitch
        # package at the contract width is empty, and that emptiness is
        # exactly D-630's `LATTICE_EXACT` class.  This source is EXACT: it
        # consults no lattice, and every candidate it returns has been proved
        # by `verify_laid` before it is offered.  Offered only where the sets
        # above are empty, so it can only ADD launches, never move one.
        if not cands and getattr(field, 'offcentre', False):
            def _lattice_free(x, y, _L=L):
                # The launch has to be a cell the WHOLE-BOARD lattice already
                # calls free, because that lattice is what the trunk wavefront
                # walks; an exact proof of the stub says nothing about whether
                # the trunk can move off its end.  Handed to the search, NOT
                # applied to its answer -- see `offcentre_escapes.goal_ok`.
                i_, j_ = field.cell(x, y)
                return field.inside(i_, j_) and not field.blk[_L][j_, i_]
            cands = offcentre_escapes(qb, field, pad, L, field.width,
                                      field.G, field.ox, field.oy,
                                      prefer=prefer, limit=limit,
                                      goal_ok=_lattice_free)
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
            if c.get('offcentre_mm') is not None:
                e['offcentre'] = True
                e['offcentre_mm'] = c['offcentre_mm']
                e['base_dir'] = c['base_dir']
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

    # A REFUSAL MUST NAME A LAND ON THE ISLAND IT REFUSED -- D-630.
    # `QBoard.escape_why` is ONE attribute on the shared `QBoard`, overwritten
    # by every failing `escape()` call.  Both sides are probed before either is
    # tested, and the DESTINATION loop runs LAST, so a `NO_LEGAL_ESCAPE_SRC`
    # used to be reported with the sentence the DESTINATION pads left behind.
    # On `/NFC_SUPPLY` that printed `reason NO_LEGAL_ESCAPE_SRC`, `a [U9.10]`,
    # `pads [U9.10]` and `why "U9.8: NO LEGAL ESCAPE ..."` in one record --
    # three fields naming the source land and the human-readable one naming the
    # other island's -- and the D-626 census inherited it, so four decisions
    # recorded this net's wall against the wrong pad.  The arithmetic settles
    # which was right: `screen_land_escape_margin` puts `U9.10` at -0.150 mm
    # and `U9.8` at +0.250 mm on the same 0.600 mm contract.
    #
    # This is the same fault D-624 fixed in `lattice_advice` (`binding_pad`,
    # last write winning) and D-626 fixed in the census (`a`/`b` read off a
    # join that carries `from`/`to`): a report that looks complete and names
    # the wrong thing.  Each side's messages are now collected WHILE that side
    # is probed, so the sentence and the `pads` list cannot disagree.  This
    # changes no search and no decision -- only which land the report names.
    # The reset before each pad matters: `pad_escapes` may skip `QBoard.escape`
    # entirely -- a pad that is not on this face, or a layer this net may not
    # route on -- and would then be credited with the PREVIOUS pad's sentence.
    src, src_why = [], []
    for p in src_pads:
        qb.escape_why = []
        got = pad_escapes(qb, field, p, (cx, cy), escape_limit)
        if not got and qb.escape_why:
            src_why.append(qb.escape_why[0])
        src += got
    dst, dst_why = [], []
    for p in dst_pads:
        qb.escape_why = []
        got = pad_escapes(qb, field, p, (sx, sy), escape_limit)
        if not got and qb.escape_why:
            dst_why.append(qb.escape_why[0])
        dst += got
    if not src:
        return dict(ok=False, reason='NO_LEGAL_ESCAPE_SRC',
                    why=(src_why or ['no legal escape on the source island'])[0],
                    why_lands=src_why,
                    pads=[p['ref'] for p in src_pads])
    if not dst:
        return dict(ok=False, reason='NO_LEGAL_ESCAPE_DST',
                    why=(dst_why or ['no legal escape on the target island'])[0],
                    why_lands=dst_why,
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


def body_landing(qb, net, field, erode=0):
    """Lattice cells that lie inside the BODY cluster's OWN filled copper.

    D-608.  `stitch_pad` takes the first via-legal cell by distance and cannot
    prefer one over another, so the barrel it plants may land on an orphan
    piece of the net's pour, or on no copper of the net at all.  Both are legal
    and neither CONNECTS: D-604 spent three gate runs on `SW9.2` at every rung
    for 69 -> 69 each, and D-607 laid `R129.1`'s barrel and 0.547 mm of track
    for 59 -> 59.  This mask is what a caller hands `stitch_pad` as `land_ok`
    so the barrel it chooses is one that lands on the plane BODY.

    A through barrel is copper on EVERY layer, so a site inside the body's
    filled polygon on ANY copper layer serves -- including a reserved inner
    plane this net may not route a track on, which is how every `GND` stitch on
    this board reaches `In1`/`In4`.  The mask is therefore a union over the
    whole stack, not over `field.layers`.

    IT IS A CERTIFICATE, NOT A VETO, AND THE DIFFERENCE IS MEASURED.  The pour
    this reads is the one filled BEFORE the barrel exists, and KiCad's refill
    only ever GROWS a zone towards new copper of its own net -- so a site
    inside the body today is inside it after the refill, while a site outside
    it today may still be flooded to.  D-606's `C7.1` is exactly that case and
    is recorded in `evidence/d608-body-landing-calibration.json`: its promoted
    barrel at (60.3, 71.0) lay outside EVERY filled `+3V3` island on the board
    it was proposed on and closed its edge anyway.  So `land_ok` narrows where
    a stitch may land; a land that finds no body site is not thereby proved
    unreachable, and today's unconstrained stitch stays available.

    `erode` is offered and is NOT what this board uses: the same calibration
    shows eroding by the barrel's own radius refuses `C5.1` and `U17.5`, both
    of which are promoted copper that closed an edge.  A via whose ring pokes a
    few microns past the pour edge is bonded by the refill, so the contract is
    CENTRE-IN-COPPER.
    """
    cov_layer, _cov, size, body, labels, _isl, _own = \
        cluster_coverage(qb, net, field)
    mask = np.zeros((field.ny, field.nx), dtype=bool)
    per = {}
    for (r, L) in cov_layer:
        if r != body:
            continue
        m = _erode(cov_layer[(r, L)], erode) if erode else cov_layer[(r, L)]
        per[L] = int(m.sum())
        mask |= m
    return mask, dict(body=(labels.get(body) or [])[:8],
                      body_pads=size.get(body), erode=erode,
                      cells=per, total=int(mask.sum()))


def stitch_pad(qb, field, pad, max_mm=8.0, escape_limit=12, land_ok=None):
    """Drop ONE pad onto its net's plane: shortest escape + one through via.

    The wavefront runs in a WINDOW of `max_mm` around the escape, not over the
    whole board.  A stitch is by definition local -- if no barrel is legal
    within a few millimetres of the pad the answer is `NO_VIA_SITE`, not a
    longer walk -- and a plane-served net has hundreds of these, so the window
    is what makes the primitive affordable at that count.

    `land_ok` is an optional lattice mask the BARREL SITE must also satisfy --
    `body_landing`'s answer, so the barrel lands on the plane body rather than
    merely somewhere legal.  It narrows the landing test and nothing else, so a
    call without it is byte-identical to every stitch this board has promoted.

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
        if land_ok is not None:
            vok = vok & land_ok[j0:j1, i0:i1]
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
        if land_ok is not None:
            return dict(ok=False, reason='NO_BODY_VIA_SITE', pad=pad['ref'],
                        why='no legal %.2f mm barrel INSIDE THIS NET\'S OWN '
                            'BODY POUR within %.1f mm of any escape'
                            % (field.via_dia / 1e6, max_mm))
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
                via_xy=(round(vx / 1e6, 4), round(vy / 1e6, 4)),
                via_xy_nm=(int(vx), int(vy)))


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


# --------------------------------------------------------------------------- #
# PAD BRIDGE -- A TRACK BETWEEN TWO LANDS WITH NO LAUNCH POINT AT ALL
# --------------------------------------------------------------------------- #
# D-631.  Every instrument on this board -- `route_join`, `stitch_pad`,
# `route_net`, `qrouter.connect_role` -- begins the same way: ESCAPE the pad to
# a LAUNCH POINT outside it, then route launch to launch.  `QBoard.escape`
# refuses any launch point where the trunk width is not legal, so a land whose
# only legal copper is the strip BETWEEN it and its neighbour has no launch
# point, and every one of those instruments reports `NO LEGAL ESCAPE` on a pair
# that needs no escape.
#
# `screen_escape_class.py` named sixteen such lands `LATTICE_EXACT` -- margin
# exactly 0.000 mm, DRC-legal at the contract width and rasterisable at NO
# pitch -- and concluded that `route_local_two_pad` was the only instrument.  It
# is not; it escapes too.  The instrument these lands want is the LATERAL twin
# of `bridge_islands`: a barrel with no escape and no track is what joins two
# pieces of pour across the stack, and a TRACK WITH NO ESCAPE, BOTH ENDS INSIDE
# THE LANDS, is what joins two lands across a gap.
#
# `+3V3` `U4.2 -> U4.3` is the case that named it.  Two 0.475 x 0.250 mm lands
# of a BMI270 LGA-14 on 0.500 mm pitch, 0.025 mm of gap between them and
# 0.500 mm to the foreign lands either side.  `connect_role` refuses at 0.600
# and at 0.400 mm and takes 2.174 mm of detour at 0.300; the bridge is
# **0.200 mm of track at the P3V3 published 0.400 mm minimum**, both endpoints
# inside the lands, and real KiCad DRC reports ZERO attributable violations.
#
# THREE THINGS ARE LOAD-BEARING.
#
#   (a) THE ENDPOINT MUST BE INSIDE THE LAND, or KiCad does not join them.
#       Containment is tested against the pad's INSCRIBED DIAMOND in its own
#       rotated frame -- |lx|/hx + |ly|/hy <= 1 -- which is inside a rectangle,
#       an oval, a rounded rectangle and a circle alike, so the test is
#       conservative for every shape this board carries and needs no per-shape
#       geometry.
#   (b) THE PROOF IS `verify_laid`, THE PROMOTER'S OWN.  Exact analytic
#       clearance against real obstacle shapes, the `.kicad_dru` overlay and any
#       pour-bond guard tube -- not a lattice.  The whole point is that the
#       lattice cannot express this, so nothing here may consult one.
#   (c) THE WIDTH LADDER NEVER GOES BELOW WHAT THE BOARD PUBLISHES.  The caller
#       hands in the widths; `route_maze_batch` hands the netclass width and the
#       `.kicad_dru` class floor and nothing narrower, exactly as `--stitch-width`
#       is clamped.  A bridge is ordinary rail copper, not a licensed neck.
#
# The INSET ladder is the only search: pulling both endpoints in from their pad
# centres TOWARD each other shortens the capsule and moves its rounded ends away
# from the foreign lands on the far sides, which is where the clearance is spent.
# Inset 0 is tried first, so a pair that needs no search is laid centre to centre.

PAD_BRIDGE_INSETS_MM = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40)


def _inside_pad(pad, t):
    """Is the point `t` nm from `pad`'s centre, along `u`, inside the land?

    `t` is a (dx, dy) offset in board nm.  Tested against the pad's INSCRIBED
    DIAMOND in the pad's own rotated frame, which is conservative for every
    shape: rect, oval, roundrect and circle all contain it.
    """
    hx, hy = float(pad.get('hx') or 0.0), float(pad.get('hy') or 0.0)
    if hx <= 0 or hy <= 0:
        return False
    ang = math.radians(float(pad.get('ang') or 0.0))
    c, s = math.cos(ang), math.sin(ang)
    lx = t[0] * c + t[1] * s
    ly = -t[0] * s + t[1] * c
    return abs(lx) / hx + abs(ly) / hy <= 1.0


def pad_bridge(qb, field, a, b, widths, layer=None,
               insets_mm=PAD_BRIDGE_INSETS_MM, blame=None):
    """ONE straight track joining two lands of the same net, no escape at all.

    Returns dict(ok, ...).  On success the track is on `qb` and the caller's
    `mark` reverts it.  `widths` is the descending ladder the caller permits and
    is never widened or narrowed here.

    `blame`, when a list is handed in, is kept in step with the refusal this
    call REPORTS: after an `UNPROVED_GEOMETRY` return it holds exactly the one
    obstacle object that rung measured against, so a caller can hold that
    object out and ask again.  It is emptied on a successful bridge, because a
    bridge that proved has no blocker.  Opt-in and additive.
    """
    layers = [layer] if layer else [L for L in ('F', 'B')
                                    if L in field.layers
                                    and a.get(L) and b.get(L)]
    dx, dy = b['x'] - a['x'], b['y'] - a['y']
    span = math.hypot(dx, dy)
    if span <= 0:
        return dict(ok=False, reason='SAME_POINT', pads=[a['ref'], b['ref']])
    ux, uy = dx / span, dy / span
    last = dict(ok=False, reason='NO_LEGAL_BRIDGE', pads=[a['ref'], b['ref']],
                why='no width and no inset on the offered ladder is legal')
    for L in layers:
        if L not in field.blk:
            continue
        for w in widths:
            for ins_mm in insets_mm:
                t = ins_mm * qr.MM
                if 2 * t >= span:
                    break
                if t and not (_inside_pad(a, (ux * t, uy * t))
                              and _inside_pad(b, (-ux * t, -uy * t))):
                    continue
                ax, ay = a['x'] + ux * t, a['y'] + uy * t
                bx, by = b['x'] - ux * t, b['y'] - uy * t
                m = qb.mark()
                qb.track(field.net, L, int(round(ax)), int(round(ay)),
                         int(round(bx)), int(round(by)), int(w))
                rung = [] if blame is not None else None
                bad = verify_laid(qb, field, m, blame=rung)
                if bad is None:
                    if blame is not None:
                        del blame[:]
                    return dict(ok=True, pads=[a['ref'], b['ref']], layer=L,
                                width=int(w), inset_mm=ins_mm,
                                mm=round((span - 2 * t) / 1e6, 4), vias=0,
                                a_xy=(round(ax / 1e6, 4), round(ay / 1e6, 4)),
                                b_xy=(round(bx / 1e6, 4), round(by / 1e6, 4)))
                qb.revert(m)
                if blame is not None:
                    blame[:] = rung
                last = dict(ok=False, reason='UNPROVED_GEOMETRY',
                            pads=[a['ref'], b['ref']], layer=L, width=int(w),
                            inset_mm=ins_mm,
                            why='%s at %s vs %s' % (bad.get('kind'),
                                                    bad.get('at'),
                                                    bad.get('against',
                                                            bad.get('why'))))
    return last


def bridge_net_pads(qb, net, field, widths, max_mm=3.0,
                    insets_mm=PAD_BRIDGE_INSETS_MM):
    """Offer `pad_bridge` to every cross-island land pair of `net`, nearest first.

    Same transaction discipline as `join_orphans`: greedy nearest pair with
    union-find over the net's own islands, each pair independent and reverted on
    its own, a laid bridge merges its two groups and the next pair sees its
    copper.  `max_mm` bounds the CENTRE-TO-CENTRE gap a bridge may span -- this
    primitive exists for lands that are touching-close, and a long straight
    track between two distant pads is a corridor question, not a bridge.
    """
    islands = net_islands(qb, net)
    if len(islands) < 2:
        return dict(ok=False, net=net, bridged=0, reason='NOTHING_TO_BRIDGE',
                    bridges=[], failures=[], declined=[], mm=0.0, vias=0)
    groups = {k: list(g) for k, g in enumerate(islands)}
    parent = {k: k for k in groups}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    pairs = []
    for ga in groups:
        for gb in groups:
            if ga >= gb:
                continue
            for p in groups[ga]:
                for q in groups[gb]:
                    pairs.append((math.hypot(p['x'] - q['x'], p['y'] - q['y']),
                                  ga, gb, p, q))
    pairs.sort(key=lambda t: (t[0], t[3]['ref'], t[4]['ref']))
    done, failed, declined = [], [], []
    for (gap, ga, gb, p, q) in pairs:
        ra, rb = find(ga), find(gb)
        if ra == rb:
            continue
        if max_mm and gap > max_mm * qr.MM:
            declined.append(dict(a=p['ref'], b=q['ref'],
                                 gap_mm=round(gap / 1e6, 3), reason='TOO_FAR'))
            continue
        m = qb.mark()
        r = pad_bridge(qb, field, p, q, widths, insets_mm=insets_mm)
        rec = dict(a=p['ref'], b=q['ref'], gap_mm=round(gap / 1e6, 3))
        if not r.get('ok'):
            qb.revert(m)
            failed.append(dict(rec, **{k: v for k, v in r.items()
                                       if k not in ('ok', 'pads')}))
            continue
        done.append(dict(rec, **{k: v for k, v in r.items()
                                 if k not in ('ok', 'pads')}))
        parent[ra] = rb
        groups[rb] = groups[ra] + groups[rb]
        field.rebuild_blk()
    return dict(ok=bool(done), net=net, bridged=len(done), bridges=done,
                failures=failed[:40], declined=declined[:40],
                declined_n=len(declined), asked=len(done) + len(failed),
                max_mm=max_mm,
                mm=round(sum(d['mm'] for d in done), 4), vias=0)


# --------------------------------------------------------------------------- #
# the OFF-CENTRE LAUNCH                                            (D-633)
# --------------------------------------------------------------------------- #
# D-632 measured SEVEN lands that refuse an escape at EVERY width down to the
# board's own 0.150 mm `min_track_width` -- `U11.9`, `U11.3`, `U9.8`, `U9.10`,
# `U21.5`, `U4.8`, `U5.2` -- and then found the reason, which is not a width at
# all: `QBoard.escape` is CENTRE-ANCHORED.  It casts a STRAIGHT segment from
# the pad's OWN CENTRE, in one of EIGHT directions fixed by the pad's
# orientation.  On a 0.500 mm-pitch package with populated neighbours no such
# ray is legal at any width this board can fabricate, which is exactly why the
# refusal does not move with width.
#
# THE PRIMITIVE THE MEASUREMENT NAMES.  A launch point does not have to be the
# pad's centre.  It has to be ON THE PAD'S OWN COPPER -- that is the only thing
# KiCad's connectivity asks -- and the segment that leaves from it has to be
# legal.  `pad_bridge` (D-631) is the ZERO-LENGTH case of this: a track between
# two lands, both endpoints inside the lands, no escape at all.  The general
# case picks the launch anywhere on the land and leaves from there.
#
# TWO FREEDOMS, AND THE EVIDENCE SAYS WHICH ONE PAID.
#
#   (a) THE ANCHOR.  Any point inside the land's INSCRIBED DIAMOND, tested
#       exactly as `pad_bridge` tests its endpoints -- |lx|/hx + |ly|/hy <= 1
#       in the pad's own rotated frame, which is inside a rect, an oval, a
#       roundrect and a circle alike, so the containment test is conservative
#       for every shape this board carries.
#   (b) THE DIRECTION.  Eight rays is a modelling choice, not a rule.  The
#       ladder walks the SAME eight first, then the 15-degree steps between
#       them, so a land that launches under `QBoard.escape` launches here
#       identically and the extra directions can only ADD answers.
#
# Every candidate is ordered CENTRE-FIRST and BASE-DIRECTION-FIRST, so the
# degenerate case reproduces `QBoard.escape` exactly, and each answer carries
# `offcentre_mm` and `base_dir` -- so a closure that needed neither freedom is
# distinguishable from one that needed one, and from one that needed both.
#
# THE PROOF IS `verify_laid`, THE PROMOTER'S OWN.  Exact analytic clearance
# against real obstacle shapes and the `.kicad_dru` overlay, never a lattice --
# the whole reason the primitive exists is that D-630's `LATTICE_EXACT` class
# is the class no lattice can express, so nothing here may consult one.  The
# cheap directional screen ahead of it uses the SAME `obs_clearance` number
# `verify_laid` will re-prove against, so the screen and the proof cannot
# disagree about WHICH rule applies.
#
# WHAT IT DOES NOT DO.  It lays no via, it never narrows below the width the
# caller hands it, and it decides no licence: a launch below a net's class
# floor is copper this board does not permit anywhere until `.kicad_dru` says
# so and `leaf_land_contract.py` says the rail current does not bind it.

OFFCENTRE_ANCHOR_FRACS = (0.0, 0.25, -0.25, 0.5, -0.5, 0.7, -0.7, 0.85, -0.85)

# HOW FAR PAST ITS OWN BOUNDARY THE STUB MAY STOP, in mm.  `QBoard.escape` has
# no such ladder: its length is FIXED at `reach + clearance + width/2 + slack`
# with the shortest slack 0.15 mm, and `reach` is the SUPPORT function.  Two
# separate charges in that formula are owed to nobody -- the clearance and the
# half-width are spent clearing the pad the stub is LEAVING, which is its own
# net and owes itself nothing.  What actually decides a landing is whether the
# copper is legal there (`verify_laid`) and whether the trunk can start there
# (`point_free`), and both are tested at every rung.
OFFCENTRE_REACH_MM = (0.025, 0.05, 0.10, 0.15, 0.25, 0.40, 0.60, 1.00)

# ...and `QBoard.escape`'s OWN nine, offered on top of the ladder above at the
# offset its formula adds, so the length set here strictly CONTAINS the length
# set the centre-anchored escape walks.  A land that launches today launches
# here, at the same point, whatever the ladder above does.
QBOARD_SLACKS_MM = (0.15, 0.30, 0.50, 0.80, 1.20, 1.80, 2.50, 3.20, 4.00)

OFFCENTRE_DIR_STEP_DEG = 15


class EscapeCtx(object):
    """The minimum a clearance proof needs to know about one net.

    `verify_laid` and `obs_clearance` read exactly five things off the object
    they are handed -- `net`, `clr_pad`, `clr_trk`, `cls`, `mycls` -- and
    nothing else.  A `Field` supplies them alongside a rasterised board it took
    seconds to build; the off-centre launch needs the five and NEVER the
    raster, so it is handed these and the two instruments stay the same
    instruments.  Duck-typed on purpose: any `Field` is already a valid
    `EscapeCtx`.
    """

    def __init__(self, qb, net, clr_pad, clr_trk, cls=None):
        self.net = net
        self.clr_pad, self.clr_trk = clr_pad, clr_trk
        self.cls = net_classes(qb) if cls is None else cls
        self.mycls = self.cls.get(net, 'Default')


class BridgeCtx(EscapeCtx):
    """`EscapeCtx` plus the two attributes `pad_bridge` reads, and NO RASTER.

    `pad_bridge` proves its one straight track with `verify_laid`, which is
    exact analytic geometry over `QBoard.obstacles`.  It touches a `Field` for
    exactly two things -- `field.layers`, to know which layers to offer, and
    `field.blk`, only ever as `if L not in field.blk`.  Neither needs a cell.

    That matters when the caller wants to ask the bridge question REPEATEDLY
    with different objects held out (D-648): a `Field` rebuild costs a full
    raster and a via grid per question, which is minutes over a board-wide
    sweep, and every cell of it would be discarded unread.  This context is the
    same five clearance facts `verify_laid` reads and a layer list, so the
    proof is bit-for-bit the proof a `Field` would have produced -- a `Field`
    remains a valid `BridgeCtx`, and nothing here may be used to propose copper
    a lattice router would then have to route around.
    """

    def __init__(self, qb, net, clr_pad, clr_trk, layers, cls=None):
        EscapeCtx.__init__(self, qb, net, clr_pad, clr_trk, cls=cls)
        self.layers = list(layers)
        self.blk = {L: None for L in self.layers}


def _on_pad(pad, x, y):
    """Is the absolute point (x, y) on this land's copper?  Exact.

    `RR.dist` is NOT a signed distance for a SHARP rectangle -- with `r == 0`
    it is `hypot(max(lx-hx,0), max(ly-hy,0))`, which is ZERO everywhere inside
    the land as well as on its edge.  Bisecting a ray exit against it therefore
    reports every sharp-cornered pad as already-left-behind, and this board is
    full of them: `U4`'s LGA lands are 0.475 x 0.250 mm with `r == 0`.  This is
    the containment test written out, in the pad's own rotated frame, and it is
    exact for rect, roundrect, oval and circle alike -- KiCad's oval is the
    stadium `r == min(hx, hy)`.
    """
    dx, dy = x - pad['x'], y - pad['y']
    a = math.radians(float(pad.get('ang') or 0.0))
    c, s_ = math.cos(a), math.sin(a)
    lx = abs(dx * c + dy * s_)
    ly = abs(-dx * s_ + dy * c)
    hx, hy = float(pad['hx']), float(pad['hy'])
    r = float(pad.get('r') or 0.0)
    if lx > hx or ly > hy:
        return False
    ihx, ihy = max(hx - r, 0.0), max(hy - r, 0.0)
    if lx <= ihx or ly <= ihy:
        return True
    return math.hypot(lx - ihx, ly - ihy) <= r


def _pad_exit(pad, ax, ay, ux, uy, hi=None):
    """Distance from (ax,ay) along (ux,uy) to the pad's own outer boundary.

    Bisection on `_on_pad`, which is the exact containment test.  With the
    anchor at the pad CENTRE and (ux,uy) an axis of the pad this returns
    `shape.extent(ux, uy)`, so the length ladder below starts where
    `QBoard.escape`'s starts.  OFF an axis it does NOT: `RR.extent` is the
    SUPPORT function -- the distance to the supporting line -- and on a
    0.475 x 0.250 mm land at 45 degrees that overshoots the true ray exit by
    0.16-0.27 mm.  That is the third freedom this primitive spends, and it is
    the one `_pocket_escapes`' own preamble predicted in prose: "the stub is
    FORCED PAST the first obstacle it could legally stop short of".
    """
    if hi is None:
        hi = 2.0 * (pad['hx'] + pad['hy'] + pad['r']) + 1000.0
    if not _on_pad(pad, ax, ay):
        return 0.0
    lo = 0.0
    for _ in range(48):
        mid = (lo + hi) / 2.0
        if _on_pad(pad, ax + ux * mid, ay + uy * mid):
            lo = mid
        else:
            hi = mid
    return hi


def _offcentre_anchors(pad, fracs=OFFCENTRE_ANCHOR_FRACS):
    """Launch anchors inside the land, CENTRE FIRST, then outward.

    Offsets are fractions of the pad's own half-extents in its own rotated
    frame, kept only where the inscribed-diamond test `pad_bridge` uses admits
    them, and returned in board nm as (dx, dy) with their distance from the
    centre so a caller can report which freedom it spent.
    """
    hx, hy = float(pad.get('hx') or 0.0), float(pad.get('hy') or 0.0)
    if hx <= 0 or hy <= 0:
        return [(0.0, 0.0, 0.0)]
    ang = math.radians(float(pad.get('ang') or 0.0))
    c, s = math.cos(ang), math.sin(ang)
    out, seen = [], set()
    for fu in fracs:
        for fv in fracs:
            if abs(fu) + abs(fv) > 1.0 + 1e-9:
                continue
            u, v = fu * hx, fv * hy
            dx, dy = u * c - v * s, u * s + v * c
            key = (int(round(dx)), int(round(dy)))
            if key in seen:
                continue
            seen.add(key)
            out.append((dx, dy, math.hypot(dx, dy)))
    out.sort(key=lambda t: (round(t[2]), t[0], t[1]))
    return out


def _offcentre_dirs(pad, prefer=None, step_deg=OFFCENTRE_DIR_STEP_DEG):
    """Ray directions, `QBoard.escape`'s EIGHT first, then the steps between.

    Each entry is (ux, uy, base) where `base` says whether the direction is one
    of the eight the centre-anchored escape already walks.  `prefer` reorders
    WITHIN each group only, so the base eight are never displaced by a better
    aimed 15-degree ray -- a land that launches today keeps launching the way
    it does today.
    """
    a = math.radians(float(pad.get('ang') or 0.0))
    base, extra, seen = [], [], set()
    for k in range(0, 360, 45):
        t = a + math.radians(k)
        base.append((math.cos(t), math.sin(t), True))
        seen.add(k % 360)
    for k in range(0, 360, max(1, int(step_deg))):
        if k % 360 in seen:
            continue
        t = a + math.radians(k)
        extra.append((math.cos(t), math.sin(t), False))
    if prefer is not None:
        n = math.hypot(prefer[0], prefer[1])
        if n > 0:
            px, py = prefer[0] / n, prefer[1] / n
            key = lambda d: -(d[0] * px + d[1] * py)
            base.sort(key=key)
            extra.sort(key=key)
    return base + extra


def offcentre_escapes(qb, ctx, pad, layer, width, G, ox, oy, prefer=None,
                      trunk_w=None, limit=8, reach_mm=OFFCENTRE_REACH_MM,
                      anchor_fracs=OFFCENTRE_ANCHOR_FRACS,
                      dir_step_deg=OFFCENTRE_DIR_STEP_DEG, prove=True,
                      goal_ok=None):
    """Legal launch points for ONE terminal, anchored anywhere on its land.

    Returns a list of dicts shaped like `QBoard.escape`'s, plus `path` (the
    two-point polyline `emit_escape` already knows how to lay), `ax`/`ay` (the
    anchor, INSIDE the land), `offcentre_mm` and `base_dir`.  Empty list and a
    filled `.why` on the returned marker when nothing legal exists.

    `width` is the width of the STUB and is never lowered here.  `trunk_w`
    defaults to `width` and is the width the LANDING point must be able to
    hold, so a stub can never hand the trunk a start it cannot use.

    `goal_ok(x, y)`, when given, is an ADDITIONAL test the landing must pass,
    and it is applied INSIDE the length ladder rather than by the caller
    afterwards.  That distinction is the whole reason it exists: the ladder
    stops at the FIRST legal length per (anchor, direction), so a caller that
    filters the answer discards the direction entirely instead of asking it for
    a longer stub.  A lattice-driven caller passes its own free-cell test here
    -- a launch point has to be somewhere the wavefront can actually stand --
    and the search then walks OUT of the pocket instead of stopping inside it.
    """
    out = []
    if not pad.get(layer):
        return out
    tw = width if trunk_w is None else trunk_w
    half = width / 2.0
    reach_max = (2.0 * (pad['hx'] + pad['hy'])
                 + (max(reach_mm) + max(QBOARD_SLACKS_MM)) * qr.MM + width
                 + 2 * max(ctx.clr_pad, ctx.clr_trk) + qr.MM)
    # Every obstacle that could possibly touch any candidate, with the number
    # `verify_laid` will re-prove against, computed ONCE.
    obs = []
    for s in qb.obstacles(layer, ctx.net):
        need = obs_clearance(qb, ctx, s, width)
        bx0, by0, bx1, by1 = s.bbox(need)
        if (pad['x'] - reach_max > bx1 or pad['x'] + reach_max < bx0 or
                pad['y'] - reach_max > by1 or pad['y'] + reach_max < by0):
            continue
        obs.append((s, need))
    anchors = _offcentre_anchors(pad, anchor_fracs)
    dirs = _offcentre_dirs(pad, prefer, dir_step_deg)
    blockers = collections.Counter()
    taken = set()
    for (dx, dy, off) in anchors:
        ax, ay = pad['x'] + dx, pad['y'] + dy
        for (ux, uy, is_base) in dirs:
            exit_t = _pad_exit(pad, ax, ay, ux, uy)
            esc_off = max(ctx.clr_pad, ctx.clr_trk) + half
            lens = sorted(set(
                [int(round(exit_t + r * qr.MM)) for r in reach_mm] +
                [int(round(exit_t + esc_off + r * qr.MM))
                 for r in QBOARD_SLACKS_MM]))
            for ln in lens:
                lx = int(round((ax + ux * ln - ox) / G)) * G + ox
                ly = int(round((ay + uy * ln - oy) / G)) * G + oy
                if (lx, ly) in taken:
                    continue
                if (lx < qb.ex0 + qr.EDGE_CLR + half or
                        lx > qb.ex1 - qr.EDGE_CLR - half or
                        ly < qb.ey0 + qr.EDGE_CLR + half or
                        ly > qb.ey1 - qr.EDGE_CLR - half):
                    blockers['board_edge'] += 1
                    continue
                if _on_pad(pad, lx, ly):
                    # A landing still ON the land is not an escape at all:
                    # the trunk would start inside the pocket and `point_free`
                    # cannot say so, because a pad's own net is never one of
                    # its obstacles.  Tested with `_on_pad`, the exact
                    # containment predicate, and NOT with the inscribed diamond
                    # `_inside_pad` uses -- that test is deliberately
                    # conservative for CONTAINMENT and would be optimistic
                    # here.
                    blockers['landing still on the land'] += 1
                    continue
                bad = None
                for (s, need) in obs:
                    bx0, by0, bx1, by1 = s.bbox(need)
                    if (min(ax, lx) > bx1 or max(ax, lx) < bx0 or
                            min(ay, ly) > by1 or max(ay, ly) < by0):
                        continue
                    if qr.seg_shape_dist(ax, ay, lx, ly, s) < need:
                        bad = s
                        break
                if bad is not None:
                    blockers[bad.tag or (bad.net or 'keep-out')] += 1
                    continue
                if not qb.point_free(layer, ctx.net, lx, ly, tw,
                                     ctx.clr_pad, ctx.clr_trk, G):
                    blockers['trunk cannot start here'] += 1
                    continue
                if goal_ok is not None and not goal_ok(lx, ly):
                    blockers['landing is not a free lattice cell'] += 1
                    continue
                if prove:
                    m = qb.mark()
                    qb.track(ctx.net, layer, int(round(ax)), int(round(ay)),
                             lx, ly, int(width))
                    why = verify_laid(qb, ctx, m)
                    qb.revert(m)
                    if why is not None:
                        blockers['UNPROVED_GEOMETRY %s'
                                 % (why.get('tag') or why.get('kind'))] += 1
                        continue
                taken.add((lx, ly))
                out.append(dict(
                    x=lx, y=ly, w=int(width),
                    ln=math.hypot(lx - ax, ly - ay),
                    dir=(ux, uy), necked=(width < tw),
                    ax=int(round(ax)), ay=int(round(ay)),
                    offcentre_mm=round(off / 1e6, 4), base_dir=bool(is_base),
                    reach_mm=round((ln - exit_t) / 1e6, 4),
                    exit_mm=round(exit_t / 1e6, 4),
                    support_mm=round(pad['shape'].extent(ux, uy) / 1e6, 4),
                    escape_formula=bool(ln >= exit_t + esc_off
                                        + QBOARD_SLACKS_MM[0] * qr.MM - 1),
                    path=[(int(round(ax)), int(round(ay))), (lx, ly)]))
                break
            if len(out) >= limit:
                break
        if len(out) >= limit:
            break
    if not out:
        offcentre_escapes.why = (
            '%s: NO OFF-CENTRE LAUNCH at %.3f mm from any of %d anchors x %d '
            'directions x %d lengths; blocked by %s'
            % (pad['ref'], width / 1e6, len(anchors), len(dirs),
               len(reach_mm) + len(QBOARD_SLACKS_MM),
               ', '.join('%s (x%d)' % kv for kv in blockers.most_common(4))))
    else:
        offcentre_escapes.why = None
    return out


offcentre_escapes.why = None


def _state_key(qb):
    """A hashable name for the copper `qb` is carrying right now.

    `QBoard.mark` is already the exact answer -- it is what `revert` rewinds to
    -- but it carries a dict and is therefore unhashable.  This is that value,
    ordered, so a search result may be cached against the board state it was
    measured on and can never be served against a different one.
    """
    n, sh, nh = qb.mark()
    return (n, tuple(sorted(sh.items())), nh)


def offcentre_connect(qb, ctx, pa, pb, layer, width, stub_widths=None,
                      G=50000, fine=25000, memo=None,
                      limit=8, reach_mm=OFFCENTRE_REACH_MM,
                      anchor_fracs=OFFCENTRE_ANCHOR_FRACS,
                      dir_step_deg=OFFCENTRE_DIR_STEP_DEG):
    """Close ONE pad pair whose ends may need an OFF-CENTRE launch.

    The centre-anchored escape is asked FIRST, per end, and where it answers
    the end is handed to `qrouter.connect_role` untouched -- so a pair that
    closes today closes today, by the same route, and this primitive can only
    ADD closures.  Where it refuses, the off-centre stub is laid HERE and the
    end is handed to `connect_role` as an ANCHOR: a junction on copper this net
    already owns, which is a case `connect_role` has always had and which lays
    no second stub of its own.

    `stub_widths` is a DESCENDING ladder for the off-centre stub alone and
    defaults to `(width,)`, in which case the stub is ordinary copper at the
    trunk width and this routine licenses nothing.  Where it is narrower, the
    NARROW WIDTH IS SPENT ONLY ON THE STUB: the landing point is still required
    to hold `width`, so the trunk leaves the pocket at the contract width and
    the sub-class copper is bounded by the stub's own length.  That is the
    shape a `PAD_ESCAPE_RUN_<REF>` licence is written against, and it is the
    difference between necking a pad and derating a twelve-millimetre haul.

    On success every object is on `qb` and the caller's own `mark` reverts the
    whole transaction; on failure this function reverts what it laid.  Returns
    the `connect_role` dict plus `launches`, one record per end that needed the
    new freedom, so the evidence names WHICH land needed it and by how much.
    """
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    m0 = qb.mark()
    ends, launches, stub_mm = [], [], 0.0
    for p, other in ((pa, pb), (pb, pa)):
        if p.get('anchor'):
            ends.append(p)
            continue
        prefer = (other['x'] - p['x'], other['y'] - p['y'])
        e = qb.escape(p, layer, width, width, ctx.clr_pad, ctx.clr_trk,
                      G, ox, oy, prefer=prefer)
        if e:
            ends.append(p)                       # connect_role owns this end
            continue
        # THE SAME QUESTION IS ASKED MANY TIMES.  A trunk ladder times a stub
        # ladder times two ends asks one land the SAME question at the SAME
        # width on the SAME copper dozens of times, and a REFUSAL is the most
        # expensive answer there is -- it is the only one that walks every
        # anchor, every direction and every slack.  The cache is keyed on the
        # board state `revert` itself rewinds to, so an answer can never be
        # served against copper it was not measured on.
        oc, sw, why = [], int(width), None
        for sw in (stub_widths or (int(width),)):
            key = (p['ref'], layer, int(sw), int(width),
                   (round(prefer[0] / 1000.0), round(prefer[1] / 1000.0)),
                   _state_key(qb))
            if memo is not None and key in memo:
                oc, why = memo[key]
            else:
                oc = offcentre_escapes(qb, ctx, p, layer, sw, G, ox, oy,
                                       prefer=prefer, trunk_w=width,
                                       limit=limit, reach_mm=reach_mm,
                                       anchor_fracs=anchor_fracs,
                                       dir_step_deg=dir_step_deg)
                why = offcentre_escapes.why
                if memo is not None:
                    memo[key] = (oc, why)
            if oc:
                break
        if not oc:
            qb.revert(m0)
            return dict(ok=False, reason='NO_LEGAL_ESCAPE', pad=p['ref'],
                        why=why, launches=launches)
        c = oc[0]
        qb.track(ctx.net, layer, c['ax'], c['ay'], c['x'], c['y'], int(sw))
        stub_mm += c['ln'] / 1e6
        launches.append(dict(pad=p['ref'], layer=layer, width=int(sw),
                             trunk_width=int(width),
                             necked=bool(sw < width),
                             offcentre_mm=c['offcentre_mm'],
                             base_dir=c['base_dir'],
                             mm=round(c['ln'] / 1e6, 4),
                             a_xy=(round(c['ax'] / 1e6, 4),
                                   round(c['ay'] / 1e6, 4)),
                             b_xy=(round(c['x'] / 1e6, 4),
                                   round(c['y'] / 1e6, 4))))
        ends.append(dict(ref=p['ref'], net=p['net'], x=c['x'], y=c['y'],
                         F=p.get('F'), B=p.get('B'), anchor=True,
                         shape=p['shape'], hx=p['hx'], hy=p['hy'],
                         r=p['r'], ang=p['ang']))
    r = qr.connect_role(qb, ctx.net, ends[0], ends[1], layer, width,
                        ctx.clr_pad, ctx.clr_trk, G=G, fine=fine)
    if not r.get('ok'):
        qb.revert(m0)
        return dict(r, launches=launches)
    bad = verify_laid(qb, ctx, m0)
    if bad is not None:
        qb.revert(m0)
        return dict(ok=False, reason='UNPROVED_GEOMETRY', launches=launches,
                    why='%s at %s vs %s' % (bad.get('kind'), bad.get('at'),
                                            bad.get('against',
                                                    bad.get('why'))))
    return dict(r, launches=launches, stub_mm=round(stub_mm, 4),
                mm=round(r.get('mm', 0.0) + stub_mm, 4))


def _via_free_everywhere(qb, ctx, x, y, via_dia, via_drill, G):
    """May a THROUGH barrel of this geometry sit on this point?

    `QBoard.via_sites` clears the two layers the hop happens to be thinking
    about; a through barrel is copper on EVERY layer of the stack and a
    DRILLED HOLE besides.  This is the whole test, and it is deliberately the
    same one `verify_laid` re-proves afterwards -- `h.r` and not
    `max(h.hx, h.hy)` -- so the pre-filter and the prover can never disagree
    about which sites exist.
    """
    for L in qb.cu:
        if not qb.point_free(L, ctx.net, x, y, via_dia,
                             ctx.clr_pad, ctx.clr_trk, G):
            return False
    for h in qb.holes:
        if math.hypot(h.cx - x, h.cy - y) < via_drill / 2.0 + h.r + HOLE_CLR:
            return False
    return True


def _hop_near(pad, far, near=None):
    """The outer layer this end launches from.

    `far` FIRST when the land is already on it, because then the end needs no
    barrel at all and the hop degenerates -- correctly -- into the flat
    off-centre connect for that end.  Otherwise the layer the land is on.
    """
    if near is not None and pad.get(near):
        return near
    if far in ('F', 'B') and pad.get(far):
        return far
    for L in ('F', 'B'):
        if pad.get(L):
            return L
    return None


def _lattice_leavable(field, layer, span=2):
    """A landing test: can a WAVEFRONT actually leave this point?

    `point_terminals` opens the landing's OWN cell whether or not the raster
    calls it free -- rightly, because the 0.75-cell guard band is a
    rasterisation artefact and `verify_laid` is what decides.  But it opens
    ONLY that cell.  If every cell within `span` is blocked, the seed set is a
    single island and the wavefront dies on its first step, which is exactly
    what this board answered: `/WAKE_INT_N` `U2.1 -> U3.1` returned `NO_PATH`
    in ZERO seconds.

    So the test that belongs INSIDE the stub's length ladder is not "is the
    landing legal" -- exact geometry already settles that -- it is "is there a
    free lattice cell beside it".  Handed to `offcentre_escapes` as `goal_ok`,
    the ladder walks OUT of the pocket instead of stopping at the first legal
    landing inside it.  That is the same lesson D-633 learned for
    `pad_escapes`, applied where it can actually be spent.
    """
    blk = field.blk.get(layer)
    if blk is None:
        return None

    def ok(x, y):
        ci, cj = field.cell(x, y)
        for dj in range(-span, span + 1):
            for di in range(-span, span + 1):
                i, j = ci + di, cj + dj
                if (di or dj) and field.inside(i, j) and not blk[j, i]:
                    return True
        return False
    return ok


def _hop_launch(qb, ctx, p, other, layer, width, stub_widths, G, ox, oy,
                memo, limit, reach_mm, anchor_fracs, dir_step_deg,
                goal_ok=None):
    """Candidate launch points for ONE end, CENTRE-ANCHORED ONES FIRST.

    Returns (candidates, stub_width, why).  Each candidate carries `ax`/`ay`
    (the point on the land the stub starts at) and `x`/`y` (the landing), so
    the caller lays exactly one segment per end and never has to know which
    freedom bought it.  The centre-anchored escape is asked first and its
    answers are taken in ITS OWN ORDER, so an end that launches today launches
    today by the same ray, and this can only ADD candidates.
    """
    prefer = (other['x'] - p['x'], other['y'] - p['y'])
    e = qb.escape(p, layer, width, width, ctx.clr_pad, ctx.clr_trk,
                  G, ox, oy, prefer=prefer)
    if e:
        keep = [c for c in e[:limit]
                if goal_ok is None or goal_ok(c['x'], c['y'])]
        if keep:
            return ([dict(x=c['x'], y=c['y'], w=c['w'], ln=c['ln'],
                          ax=p['x'], ay=p['y'], offcentre_mm=0.0,
                          base_dir=True, centre=True) for c in keep],
                    int(width), None)
    why = None
    for sw in (stub_widths or (int(width),)):
        key = (p['ref'], layer, int(sw), int(width),
               (round(prefer[0] / 1000.0), round(prefer[1] / 1000.0)),
               _state_key(qb))
        if memo is not None and key in memo:
            oc, why = memo[key]
        else:
            oc = offcentre_escapes(qb, ctx, p, layer, sw, G, ox, oy,
                                   prefer=prefer, trunk_w=width, limit=limit,
                                   reach_mm=reach_mm,
                                   anchor_fracs=anchor_fracs,
                                   dir_step_deg=dir_step_deg,
                                   goal_ok=goal_ok)
            why = offcentre_escapes.why
            if memo is not None:
                memo[key] = (oc, why)
        if oc:
            return ([dict(c, centre=False) for c in oc], int(sw), None)
    return ([], int(width), why)


def _hop_sites(qb, ctx, nl, far, c, width, ladder, G, span, sites_limit,
               keep):
    """Up to `keep` acceptable barrel sites for ONE launch, nearest first.

    Returns a list of (x, y, dia, drill).  The ladder is walked WIDEST FIRST
    and the FIRST rung that yields any acceptable site wins the whole list, so
    an end never mixes barrel geometries and never spends a smaller barrel
    than the pocket actually demands.

    Two things separate this from `QBoard.via_site`, and both were measured:

      * `via_site` -- the SINGULAR -- returns the nearest reachable site that
        clears the NEAR and FAR layers, which is not the same question as "the
        nearest reachable site this BOARD will accept".  `TP6.1`
        (`/BQ25185_STAT1`) has one at (69.600, 95.750): legal on `B`, legal on
        `I2`, and 0.064 mm from a foreign `Net-(SW9-A)` track on `I3` -- a
        layer the hop was not thinking about and the drill goes straight
        through.  Taking that one answer and giving up is how a perfectly
        reachable end reports `NO_VIA_SITE`.
      * the reachable cloud is GRID-DENSE.  At 0.025 mm pitch the 256 nearest
        sites lie inside a 0.2 mm radius, so an unseparated list walks the same
        square millimetre over and over and never reaches the next opening.
        `via_sites` compacts by barrel diameter into materially distinct
        placements, still distance-ordered, so `sites_limit` buys AREA instead
        of resolution.
    """
    for (dia, drill) in ladder:
        out = []
        if _via_free_everywhere(qb, ctx, c['x'], c['y'], dia, drill, G):
            out.append((int(c['x']), int(c['y']), int(dia), int(drill)))
        for st in qb.via_sites(nl, far, ctx.net, c, width, dia,
                               ctx.clr_pad, ctx.clr_trk, G, span=span,
                               via_drill=drill, hole_clr=HOLE_CLR,
                               limit=sites_limit, separation=dia):
            if len(out) >= keep:
                break
            if (int(st[0]), int(st[1])) == (int(c['x']), int(c['y'])):
                continue
            if _via_free_everywhere(qb, ctx, st[0], st[1], dia, drill, G):
                out.append((int(st[0]), int(st[1]), int(dia), int(drill)))
        if out:
            return out
    return []


def _hop_options(qb, ctx, p, other, far, near, width, stub_widths, ladder,
                 G, ox, oy, memo, limit, span, sites_limit, keep,
                 reach_mm, anchor_fracs, dir_step_deg):
    """Every (launch, barrel) this end could take, in preference order.

    Returns (near_layer, options, refusal).  An option is a dict carrying the
    launch, the barrel site and geometry (or `None` when the land is already
    on the haul layer and needs no barrel at all), and the stub width.  NO
    COPPER IS LAID: a `QBoard`'s obstacles never include the net's own copper,
    so both ends can be planned against the same board before either commits.
    """
    nl = _hop_near(p, far, near)
    if nl is None:
        return None, [], dict(reason='NO_OUTER_LAYER',
                              why='%s is on no outer layer' % p['ref'])
    cands, sw, why = _hop_launch(qb, ctx, p, other, nl, width, stub_widths,
                                 G, ox, oy, memo, limit, reach_mm,
                                 anchor_fracs, dir_step_deg)
    if not cands:
        return nl, [], dict(reason='NO_LEGAL_ESCAPE', why=why)
    opts = []
    for c in cands:
        if nl == far:
            opts.append(dict(cand=c, sw=sw, site=None, dia=None, drill=None,
                             at=(c['x'], c['y'])))
            continue
        for (x, y, dia, drill) in _hop_sites(qb, ctx, nl, far, c, width,
                                             ladder, G, span, sites_limit,
                                             keep):
            opts.append(dict(cand=c, sw=sw, site=(x, y), dia=dia, drill=drill,
                             at=(x, y)))
    if not opts:
        return nl, [], dict(
            reason='NO_VIA_SITE',
            why='%s: no barrel of %s reachable on %s from any of %d launches '
                'that clears every layer of the stack'
                % (p['ref'], '/'.join('%.2f' % (d / 1e6) for d, _ in ladder),
                   nl, len(cands)))
    return nl, opts, None


def _hop_lay(qb, ctx, p, nl, far, opt, width, G, fine):
    """Lay ONE end's stub, its walk to the barrel site and the barrel itself.

    Returns (ok, walk_mm, why).  The caller owns the mark and the revert.
    """
    c, sw = opt['cand'], opt['sw']
    qb.track(ctx.net, nl, c['ax'], c['ay'], c['x'], c['y'], int(sw))
    if opt['site'] is None:
        return True, 0.0, None
    vx, vy = opt['site']
    wmm = 0.0
    if (vx, vy) != (c['x'], c['y']):
        w = qr.connect_role(
            qb, ctx.net,
            dict(ref=p['ref'] + '~land', net=ctx.net, x=c['x'], y=c['y'],
                 anchor=True),
            dict(ref=p['ref'] + '~barrel', net=ctx.net, x=vx, y=vy,
                 anchor=True),
            nl, width, ctx.clr_pad, ctx.clr_trk, G=G, fine=fine)
        if not w.get('ok'):
            return False, 0.0, ('%s: no %s corridor from the launch to its '
                                'barrel site' % (p['ref'], nl))
        wmm = w.get('mm', 0.0)
    qb.via(ctx.net, vx, vy, opt['dia'], opt['drill'])
    return True, wmm, None


def offcentre_hop(qb, ctx, pa, pb, far, width, near=None, stub_widths=None,
                  G=50000, fine=25000, memo=None, limit=6, via_ladder=None,
                  via_dia=600000, via_drill=300000, span=8000000,
                  sites_limit=96, site_options=6, joint=True,
                  joint_grid=100000, joint_margin=24000000,
                  reach_mm=OFFCENTRE_REACH_MM,
                  anchor_fracs=OFFCENTRE_ANCHOR_FRACS,
                  dir_step_deg=OFFCENTRE_DIR_STEP_DEG):
    """Close ONE pad pair with an OFF-CENTRE LAUNCH and a LAYER HOP.

    D-633 measured the off-centre launch and found that it opens twenty-nine
    lands and then hands every one of them to a CORRIDOR that refuses.  All
    three corridor instruments this board owns had the same gap.
    `qrouter.connect_role` is exact at the escape but FLAT -- one layer, no
    via, so it can only ever offer the lane the pocket is already congested
    with.  `qrouter.connect_hop` has the barrel but escapes from the pad
    CENTRE and CANNOT BE GIVEN AN ANCHOR, so it refuses at precisely the lands
    the off-centre launch opened.  `route_join` has the barrel AND the layer
    change and reaches neither, because its launch is a LATTICE cell and
    D-633 proved that what refuses a lattice is the POCKET, not the pad
    centre.  This is the composition with none of those three gaps, and it is
    a composition and not a fourth router:

      * the STUB is `offcentre_escapes` -- exact analytic clearance against
        real obstacle shapes, never a lattice, and its landing is required to
        hold the TRUNK width so the haul never starts on copper it may not use;
      * the BARREL is `_hop_sites` over `QBoard.via_sites`, cleared on EVERY
        layer of the stack and against every drilled hole;
      * the WALK from the landing to that site, and the HAUL itself on `far`,
        are both `qrouter.connect_role` between two ANCHORS, which is the case
        it has always had and which lays no escape of its own.

    THE BARREL IS CHOSEN JOINTLY, AND THAT IS THE PART THE MEASUREMENT
    FORCED.  Picking each end's barrel independently -- nearest legal site to
    that end's own launch -- is what `connect_hop` does, and on this board it
    fails for a reason no near-layer measurement can see: `In2.Cu` is not an
    empty lane, it is a field of **790 through barrels** that every layer of
    the stack carries, and it is partitioned into POCKETS.  Measured on
    `/08_BUTTONS_EXPANDERS/BTN_LEFT_N`: `R6.2`'s nearest legal barrel at
    (52.800, 88.500) can reach **37.5 mm2** of `In2.Cu` and `U2.15`'s barrel
    at (56.925, 83.225) -- 4.9 mm away -- is NOT INSIDE IT.  Two perfectly
    legal barrels, one perfectly empty layer, and no corridor, because the
    barrels were chosen for their distance from the near-layer launch instead
    of for the far-layer pocket they land in.  With `joint`, the far layer is
    FLOODED from each of end A's candidate sites and end B's site is required
    to lie inside that flood, so the pair is committed only when the haul is
    reachable BY CONSTRUCTION.  `joint=False` reproduces the independent
    choice, for the A/B that proves the difference.

    `far` may be a single layer or an ordered list, in which case the first
    that closes wins and the most informative refusal is carried out.  An end
    whose land is ALREADY on `far` takes no barrel and no walk, so a pair of
    such ends is exactly `offcentre_connect` and answers identically.

    `stub_widths` is a DESCENDING ladder spent ONLY on the off-centre stub;
    the landing, the walk and the haul are all at `width`.  `via_ladder` is a
    descending list of (diameter, drill) pairs, widest first, per end.  The
    centre-anchored escape is asked FIRST at every end, so no pair that closes
    today changes.  On success every object is on `qb` and the caller's own
    `mark` reverts the whole transaction; on failure this reverts what it laid.
    """
    ladder = tuple(via_ladder or ((int(via_dia), int(via_drill)),))
    if isinstance(far, (list, tuple)):
        best, tried = None, []
        for L in far:
            r = offcentre_hop(qb, ctx, pa, pb, L, width, near=near,
                              stub_widths=stub_widths, G=G, fine=fine,
                              memo=memo, limit=limit, via_ladder=ladder,
                              span=span, sites_limit=sites_limit,
                              site_options=site_options, joint=joint,
                              joint_grid=joint_grid,
                              joint_margin=joint_margin,
                              reach_mm=reach_mm, anchor_fracs=anchor_fracs,
                              dir_step_deg=dir_step_deg)
            tried.append(dict(far=L, reason=r.get('reason'),
                              pad=r.get('pad'), why=r.get('why')))
            if r.get('ok'):
                return dict(r, far_tried=tried)
            # A land that cannot launch at all says the same thing on every
            # far layer; a corridor refusal is the layer's own answer.  Keep
            # the first, most specific reason.
            if best is None or (best.get('reason') == 'NO_PATH'
                                and r.get('reason') != 'NO_PATH'):
                best = r
        return dict(best or dict(ok=False, reason='NO_LAYER',
                                 why='no far layer offered'), far_tried=tried)

    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    plan = []
    for p, other in ((pa, pb), (pb, pa)):
        if p.get('anchor'):
            plan.append((p, None, [dict(cand=None, sw=int(width), site=None,
                                        dia=None, drill=None,
                                        at=(p['x'], p['y']))]))
            continue
        nl, opts, bad = _hop_options(qb, ctx, p, other, far, near, width,
                                     stub_widths, ladder, G, ox, oy, memo,
                                     limit, span, sites_limit, site_options,
                                     reach_mm, anchor_fracs, dir_step_deg)
        if bad is not None:
            return dict(ok=False, pad=p['ref'], far=far, launches=[], **bad)
        plan.append((p, nl, opts))

    # JOINT SELECTION.  Flood the haul layer from each of end A's candidate
    # barrels and take the first of end B's that lies inside it.  The flood is
    # the SAME `free_region` the site search itself is built on, at the trunk
    # width, so a pair that survives here has a haul by construction and
    # `connect_role` below is a formality that draws it rather than a search
    # that might fail.
    pairs, unreached, fallback = [], 0, False
    if joint:
        # THE FLOOD IS BOUNDED AND IT IS COARSE, AND BOTH ARE DELIBERATE.
        # `free_region` rasterises its whole window: at 0.025 mm over this
        # board that is 28 million cells and the pre-filter would cost more
        # than the search it is meant to save.  The window is the candidate
        # barrels' bounding box plus `joint_margin`, which is
        # `connect_role`'s OWN largest expansion, so a haul this cannot see is
        # a haul that instrument cannot see either.  The pitch is coarser, and
        # a coarser lattice has a LARGER guard band and therefore a SMALLER
        # reachable set -- the pre-filter can only ever be pessimistic, never
        # permissive.  Which is why a `joint` run that finds no shared pocket
        # still FALLS BACK to the independent nearest pair: the joint test may
        # only ADD closures, exactly as the off-centre launch may only add
        # launches.
        jg = max(int(joint_grid), int(G))
        x0 = min(o['at'][0] for pl in plan for o in pl[2]) - joint_margin
        x1 = max(o['at'][0] for pl in plan for o in pl[2]) + joint_margin
        y0 = min(o['at'][1] for pl in plan for o in pl[2]) - joint_margin
        y1 = max(o['at'][1] for pl in plan for o in pl[2]) + joint_margin
        x0, y0 = max(x0, qb.ex0), max(y0, qb.ey0)
        x1, y1 = min(x1, qb.ex1), min(y1, qb.ey1)
        for oa in plan[0][2]:
            reg = qb.free_region(far, ctx.net, width, ctx.clr_pad,
                                 ctx.clr_trk, jg, oa['at'], x0, y0, x1, y1)
            if reg is None:
                continue
            mask, rox, roy, g = reg
            for ob in plan[1][2]:
                i = int((ob['at'][0] - rox) // g)
                j = int((ob['at'][1] - roy) // g)
                if 0 <= j < mask.shape[0] and 0 <= i < mask.shape[1] \
                        and mask[j, i]:
                    pairs.append((oa, ob))
                else:
                    unreached += 1
        if not pairs:
            fallback = True
    if not pairs:
        pairs = [(plan[0][2][0], plan[1][2][0])]

    fail = None
    for (oa, ob) in pairs:
        m0 = qb.mark()
        ends, launches, barrels = [], [], []
        stub_mm = walk_mm = 0.0
        ok = True
        for (p, nl, _), opt in zip(plan, (oa, ob)):
            if opt['cand'] is None:
                ends.append(p)
                continue
            good, wmm, why = _hop_lay(qb, ctx, p, nl, far, opt, width, G, fine)
            if not good:
                fail = dict(ok=False, reason='NO_NEAR_WALK', pad=p['ref'],
                            why=why, far=far)
                ok = False
                break
            c = opt['cand']
            stub_mm += c['ln'] / 1e6
            walk_mm += wmm
            launches.append(dict(pad=p['ref'], layer=nl, width=int(opt['sw']),
                                 trunk_width=int(width),
                                 necked=bool(opt['sw'] < width),
                                 centre=bool(c.get('centre')),
                                 offcentre_mm=c['offcentre_mm'],
                                 base_dir=c['base_dir'],
                                 mm=round(c['ln'] / 1e6, 4),
                                 walk_mm=round(wmm, 4),
                                 a_xy=(round(c['ax'] / 1e6, 4),
                                       round(c['ay'] / 1e6, 4)),
                                 b_xy=(round(c['x'] / 1e6, 4),
                                       round(c['y'] / 1e6, 4)),
                                 via_dia=opt['dia'], via_drill=opt['drill'],
                                 via_xy=(None if opt['site'] is None else
                                         (round(opt['site'][0] / 1e6, 4),
                                          round(opt['site'][1] / 1e6, 4)))))
            if opt['site'] is not None:
                barrels.append(dict(xy=(round(opt['site'][0] / 1e6, 4),
                                        round(opt['site'][1] / 1e6, 4)),
                                    dia=opt['dia'], drill=opt['drill'],
                                    near=nl, far=far))
            ends.append(dict(ref=p['ref'], net=p['net'],
                             x=opt['at'][0], y=opt['at'][1],
                             F=p.get('F'), B=p.get('B'), anchor=True,
                             shape=p['shape'], hx=p['hx'], hy=p['hy'],
                             r=p['r'], ang=p['ang']))
        if not ok:
            qb.revert(m0)
            continue
        r = qr.connect_role(qb, ctx.net, ends[0], ends[1], far, width,
                            ctx.clr_pad, ctx.clr_trk, G=G, fine=fine)
        if not r.get('ok'):
            qb.revert(m0)
            fail = dict(r, launches=launches, far=far, vias=len(barrels))
            continue
        bad = verify_laid(qb, ctx, m0)
        if bad is not None:
            qb.revert(m0)
            fail = dict(ok=False, reason='UNPROVED_GEOMETRY',
                        launches=launches, far=far, vias=len(barrels),
                        why='%s at %s vs %s'
                            % (bad.get('kind'), bad.get('at'),
                               bad.get('against', bad.get('why'))))
            continue
        return dict(r, launches=launches, far=far, vias=len(barrels),
                    barrels=barrels, joint=bool(joint),
                    joint_fallback=bool(fallback), combinations=len(pairs),
                    joint_rejected=unreached,
                    stub_mm=round(stub_mm, 4), walk_mm=round(walk_mm, 4),
                    mm=round(r.get('mm', 0.0) + stub_mm + walk_mm, 4))
    return fail or dict(ok=False, reason='NO_PATH', far=far, launches=[],
                        why='no haul on %s from %s to %s' % (far, pa['ref'],
                                                             pb['ref']))

def offcentre_route(qb, field, pa, pb, width=None, stub_widths=None, G=50000,
                    memo=None, limit=6, via_cost_mm=1.5, span=2, max_mm=0.0,
                    reach_mm=OFFCENTRE_REACH_MM,
                    anchor_fracs=OFFCENTRE_ANCHOR_FRACS,
                    dir_step_deg=OFFCENTRE_DIR_STEP_DEG):
    """Close ONE pad pair with an EXACT launch and the FULL 3D corridor.

    This is the composition D-634's own measurement forced, and it is the one
    combination no instrument on this board has ever had.

    `offcentre_hop` gave the exact launch a barrel and a haul, but the haul is
    `connect_role` and `connect_role` is FLAT: it picks ONE layer, and the
    board-wide census found the wall is exactly there.  `In2.Cu` is not a spare
    lane -- a THROUGH barrel is copper on every layer, this board has 790 of
    them, and they cut the inner layers into POCKETS.  Measured on
    `/08_BUTTONS_EXPANDERS/BTN_LEFT_N`: `R6.2`'s barrel reaches 37.5 mm2 of
    `In2.Cu` and `U2.15`'s barrel, 4.9 mm away, is not inside it.  A flat haul
    cannot leave a pocket.  A 3D one can -- that is what a via is for -- and
    `wave3d` has always been able to, which is why `route_join` exists.

    What `route_join` could never do is START.  Its launch is
    `maze3d.pad_escapes`, whose candidates must be free cells of the WHOLE-BOARD
    lattice, and D-633 proved that what refuses a lattice is the POCKET the land
    sits in and not the pad's centre -- so the 29 lands the off-centre launch
    opened were opened for nothing.  `point_terminals` is the door: it takes an
    EXACT board coordinate and opens that coordinate's own cell whether or not
    the raster calls it free, on the stated ground that the 0.75-cell guard band
    is a rasterisation artefact and `verify_laid` is what decides afterwards.
    So the exact stub lands where only exact geometry can prove it legal, and
    the wavefront starts from there.

    Both ends launch on THEIR OWN outer layer, which need not be the same one --
    `route_points` requires a single terminal layer because a detour must
    arrive where the track it replaces arrived; a pair of lands has no such
    obligation, and half this board's open pairs are not coplanar at all.

    `field` is a `Field` of this net at the trunk width and is also its own
    `EscapeCtx`.  `width` defaults to the field's.  On success the copper is on
    `qb` and the caller's `mark` reverts it; on failure this reverts what it
    laid.  Every object -- stub, run and barrel alike -- is re-proved by
    `verify_laid` before it is kept.
    """
    width = int(field.width if width is None else width)
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    m0 = qb.mark()
    ends, launches, stub_mm = [], [], 0.0
    for p, other in ((pa, pb), (pb, pa)):
        if p.get('anchor'):
            ends.append((p.get('layer') or ('F' if p.get('F') else 'B'),
                         int(p['x']), int(p['y'])))
            continue
        laid = None
        for nl in ('F', 'B'):
            if not p.get(nl) or nl not in field.blk:
                continue
            cands, sw, why = _hop_launch(qb, field, p, other, nl, width,
                                         stub_widths, G, ox, oy, memo, limit,
                                         reach_mm, anchor_fracs, dir_step_deg,
                                         goal_ok=_lattice_leavable(field, nl,
                                                                   span))
            if not cands:
                laid = laid or dict(reason='NO_LEGAL_ESCAPE', pad=p['ref'],
                                    why=why)
                continue
            c = cands[0]
            qb.track(field.net, nl, c['ax'], c['ay'], c['x'], c['y'], int(sw))
            stub_mm += c['ln'] / 1e6
            launches.append(dict(pad=p['ref'], layer=nl, width=int(sw),
                                 trunk_width=width,
                                 necked=bool(sw < width),
                                 centre=bool(c.get('centre')),
                                 offcentre_mm=c['offcentre_mm'],
                                 base_dir=c['base_dir'],
                                 mm=round(c['ln'] / 1e6, 4),
                                 a_xy=(round(c['ax'] / 1e6, 4),
                                       round(c['ay'] / 1e6, 4)),
                                 b_xy=(round(c['x'] / 1e6, 4),
                                       round(c['y'] / 1e6, 4))))
            ends.append((nl, int(c['x']), int(c['y'])))
            laid = True
            break
        if laid is not True:
            qb.revert(m0)
            return dict(ok=False, launches=launches,
                        **(laid or dict(reason='NO_OUTER_LAYER',
                                        pad=p['ref'],
                                        why='%s is on no layer of this net\'s '
                                            'contract' % p['ref'])))

    (la, ax, ay), (lb, bx, by) = ends
    seeds = point_terminals(field, bx, by, lb, span)
    goals = point_terminals(field, ax, ay, la, span)
    if not seeds or not goals:
        qb.revert(m0)
        return dict(ok=False, reason='NO_TERMINAL', launches=launches,
                    why='%s or %s is not on a layer of this net\'s contract'
                        % (la, lb))
    vc = max(1, int(round(via_cost_mm * qr.MM / field.G)))
    budget = (WAVE_STEPS if not max_mm
              else max(1, int(round(max_mm * qr.MM / field.G))))
    dist, hit = wave3d(field, seeds, goals, vc, budget=budget)
    if dist is None or hit is None:
        qb.revert(m0)
        return dict(ok=False, reason='NO_PATH', launches=launches,
                    why='no all-layer corridor at %.3f mm from %s on %s to %s '
                        'on %s' % (width / 1e6, pa['ref'], la, pb['ref'], lb))
    path = descend3d(field, dist, hit, vc)
    if path is None:
        qb.revert(m0)
        return dict(ok=False, reason='NO_DESCENT', launches=launches)
    if path[0][0] != la or path[-1][0] != lb:
        qb.revert(m0)
        return dict(ok=False, reason='WRONG_TERMINAL_LAYER', launches=launches,
                    why='the corridor arrives on %s/%s, not %s/%s'
                        % (path[0][0], path[-1][0], la, lb))
    r = _emit_path(qb, field, path, field.net, head=(ax, ay), tail=(bx, by))
    if not r.get('ok'):
        qb.revert(m0)
        return dict(r, launches=launches)
    bad = verify_laid(qb, field, m0)
    if bad is not None:
        qb.revert(m0)
        return dict(ok=False, reason='UNPROVED_GEOMETRY', launches=launches,
                    why='%s at %s vs %s' % (bad.get('kind'), bad.get('at'),
                                            bad.get('against',
                                                    bad.get('why'))))
    return dict(ok=True, launches=launches, layers=r['layers'],
                mm_by_layer=r['mm_by_layer'], vias=r['vias'],
                via_xy=r['via_xy'], stub_mm=round(stub_mm, 4),
                terminals=[la, lb],
                mm=round(r['mm'] + stub_mm, 4))

def hop_net_pads(qb, net, ctx, far, width, via_ladder, stub_widths=None,
                 max_mm=0.0, G=50000, fine=25000, span=8000000, limit=6,
                 sites_limit=96, pairs=1):
    """Offer `offcentre_hop` to every cross-island land pair of `net`,
    nearest first.

    Same transaction discipline as `bridge_net_pads`: greedy nearest pair with
    union-find over the net's own islands, each pair independent and reverted
    on its own, a closed hop merges its two groups and the next pair is asked
    on a board that already carries its copper.  `pairs` bounds how many
    pad-to-pad combinations of one island pair are asked before that island
    pair is given up, because a hop is expensive and the nearest combination is
    almost always the only one worth the money.

    `max_mm` bounds the centre-to-centre gap, and unlike a bridge's bound it is
    OFF by default: a hop's whole purpose is to take a haul off a congested
    face, and the hauls that need it most are the long ones.
    """
    islands = net_islands(qb, net)
    if len(islands) < 2:
        return dict(ok=False, net=net, hopped=0, reason='NOTHING_TO_HOP',
                    hops=[], failures=[], declined=[], mm=0.0, vias=0)
    groups = {k: list(g) for k, g in enumerate(islands)}
    parent = {k: k for k in groups}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    combos = []
    for ga in groups:
        for gb in groups:
            if ga >= gb:
                continue
            near = sorted(((math.hypot(p['x'] - q['x'], p['y'] - q['y']),
                            ga, gb, p, q)
                           for p in groups[ga] for q in groups[gb]),
                          key=lambda t: (t[0], t[3]['ref'], t[4]['ref']))
            combos.extend(near[:max(1, pairs)])
    combos.sort(key=lambda t: (t[0], t[3]['ref'], t[4]['ref']))
    done, failed, declined, memo = [], [], [], {}
    for (gap, ga, gb, p, q) in combos:
        ra, rb = find(ga), find(gb)
        if ra == rb:
            continue
        if max_mm and gap > max_mm * qr.MM:
            declined.append(dict(a=p['ref'], b=q['ref'],
                                 gap_mm=round(gap / 1e6, 3), reason='TOO_FAR'))
            continue
        m = qb.mark()
        r = offcentre_hop(qb, ctx, p, q, far, width, stub_widths=stub_widths,
                          G=G, fine=fine, memo=memo, limit=limit,
                          via_ladder=via_ladder, span=span,
                          sites_limit=sites_limit)
        rec = dict(a=p['ref'], b=q['ref'], gap_mm=round(gap / 1e6, 3))
        if not r.get('ok'):
            qb.revert(m)
            failed.append(dict(rec, reason=r.get('reason'), why=r.get('why'),
                               pad=r.get('pad'),
                               far_tried=r.get('far_tried')))
            continue
        done.append(dict(rec, mm=r.get('mm'), far=r.get('far'),
                         vias=r.get('vias'), barrels=r.get('barrels'),
                         stub_mm=r.get('stub_mm'), walk_mm=r.get('walk_mm'),
                         launches=r.get('launches'), profile=r.get('profile')))
        parent[ra] = rb
        groups[rb] = groups[ra] + groups[rb]
        memo.clear()                      # the board moved; the cache did not
        if hasattr(ctx, 'rebuild_blk'):
            ctx.rebuild_blk()
    return dict(ok=bool(done), net=net, hopped=len(done), hops=done,
                failures=failed[:40], declined=declined[:40],
                declined_n=len(declined), asked=len(done) + len(failed),
                max_mm=max_mm, far=list(far) if isinstance(far, (list, tuple))
                else far,
                via_ladder=[list(v) for v in via_ladder],
                mm=round(sum(d['mm'] for d in done), 4),
                vias=sum(d['vias'] or 0 for d in done))

def join_orphans(qb, net, field, escape_limit=8, via_cost_mm=1.5, near=8,
                 max_mm=0.0):
    """Join a plane-served net's ORPHAN islands TO EACH OTHER.

    D-608.  Every move this board owns aims an orphan at the plane BODY --
    `stitch_pad` drops a barrel into the pour, `join_residual_islands` mazes to
    `main`, `join_islands` jumps between pieces of pour, `bridge_islands` drops
    a barrel through the stack.  Not one of them ever asks whether two ORPHANS
    can reach EACH OTHER, and the net's open-edge count does not care which:
    a net's islands are joined by an MST, so merging any two of them closes
    exactly one edge.

    THE CASE THAT NAMED IT IS THE WHOLE +3V3 RAIL.  `U12` is the `TPS63020`
    buck-boost, and `U12.4` and `U12.5` are its two `VOUT` pins -- 0.240 mm
    pads on 0.500 mm pitch, both open, both `NO_LEGAL_ESCAPE` toward the plane
    at the P3V3 floor, and the nearest OTHER `+3V3` pad is `R127.1`, 9.3 mm
    away.  They are 0.500 mm from one another, the run between them is legal at
    the full 0.400 mm floor with zero vias, and the converter datasheet
    requires both pins connected in any case.  Nothing but the absence of this
    function stopped it being laid.

    Same transaction discipline as `join_residual_islands`: each pair is
    independent, a failure is reverted alone, and `max_mm` is the same
    ELECTRICAL bound -- a lateral jumper between two orphans buys one edge and
    spends outer-layer capacity, so a long one is refused as `TOO_LONG` and
    reported rather than laid.  Greedy nearest-pair with union-find, so a
    merged group is offered onward as one island.
    """
    islands = net_islands(qb, net)
    if len(islands) < 3:
        return dict(ok=False, net=net, joined=0, reason='NOTHING_TO_JOIN',
                    joins=[], failures=[], mm=0.0, vias=0)
    body = max(islands, key=len)
    groups = {k: list(g) for k, g in
              enumerate(i for i in islands if i is not body)}
    parent = {k: k for k in groups}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    pairs = sorted(((_pad_gap(groups[a], groups[b]), a, b)
                    for a in groups for b in groups if a < b),
                   key=lambda t: (t[0], t[1], t[2]))
    done, failed, declined = [], [], []
    for (gap, a, b) in pairs:
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        A, B = groups[ra], groups[rb]
        # A PAIR THIS BOUND DECLINES IS RECORDED, NOT DROPPED.  D-631.  The
        # `continue` here used to be bare, so a pair beyond `max_mm` was not
        # asked, not refused and not reported -- and the caller then read
        # "joined 0, 2 failures" off a run that had DECLINED thirty-four pairs
        # without a word.  On `/01_POWER_TREE/BQ25185_SYS` the two it did ask
        # both had a zero-escape island on one end, so every pair with legal
        # escapes at BOTH ends was in the silent set, the nearest of them
        # 0.574 mm past the bound.  The bound itself is unchanged and no copper
        # moves: this list is report-only, and it is kept OUT of `failures` so
        # the 40-row cap on real refusals cannot be spent on declines.
        if max_mm and gap > max_mm * qr.MM:
            declined.append(dict(a=[p['ref'] for p in A][:8],
                                 b=[p['ref'] for p in B][:8],
                                 gap_mm=round(gap / 1e6, 3), reason='TOO_FAR',
                                 why='%.3f mm gap exceeds the %.1f mm '
                                     'orphan-join bound; NEVER ASKED'
                                     % (gap / 1e6, max_mm)))
            continue
        m = qb.mark()
        r = route_join(qb, field, A, nearest_pads(A, B, near),
                       escape_limit=escape_limit, via_cost_mm=via_cost_mm)
        r.pop('mark', None)
        rec = dict(a=[p['ref'] for p in A][:8], b=[p['ref'] for p in B][:8],
                   gap_mm=round(gap / 1e6, 3))
        if not r.get('ok'):
            qb.revert(m)
            failed.append(dict(rec, **{k: v for k, v in r.items()
                                       if k != 'ok'}))
            continue
        if max_mm and r.get('mm', 0.0) > max_mm:
            qb.revert(m)
            failed.append(dict(rec, reason='TOO_LONG', mm=round(r['mm'], 3),
                               vias=r.get('vias'),
                               why='%.3f mm of copper exceeds the %.1f mm '
                                   'orphan-join bound' % (r['mm'], max_mm)))
            continue
        done.append(dict(rec, **{k: v for k, v in r.items() if k != 'ok'}))
        # The join laid copper; the next pair must see it as an obstacle, and
        # the two groups are now one island for every pair after this.
        parent[ra] = rb
        groups[rb] = A + B
        field.rebuild_blk()
    return dict(ok=bool(done), net=net, joined=len(done),
                joins=done, failures=failed[:40],
                declined=declined[:40], declined_n=len(declined),
                asked=len(done) + len(failed), max_mm=max_mm,
                mm=round(sum(d.get('mm', 0.0) for d in done), 3),
                vias=sum(d.get('vias', 0) for d in done))


def stitch_net(qb, net, width=200000, clr_pad=200000, clr_trk=200000,
               via_dia=600000, via_drill=300000, G=100000, field=None,
               max_mm=8.0, escape_limit=12, split_islands=False,
               land_ok=None):
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
                           escape_limit=escape_limit, land_ok=land_ok)
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


# --------------------------------------------------------------------------- #
# BOND REDUNDANCY -- STITCH A PAD THAT IS ALREADY CONNECTED
# --------------------------------------------------------------------------- #
# `stitch_net` exists to connect a pad that is NOT connected, and it skips every
# pad that already touches its net's pour.  For two hundred islands of a fresh
# pour that is exactly right.  D-599 measured the case where it is exactly
# wrong.
#
# `pour_bond_guard.py` proves, for each small outer-pour island, the TUBE of
# copper that is the ONLY thing joining the pads that island bonds.  Three
# independent nets -- `/I2C_SCL_INT`, `/I2C_SDA_INT`, `BTN_DOWN_N` -- were each
# put through the full gate with that guard OFF and all three returned the same
# shape: the net closes one edge, `GND` opens one, `--repair-planes` names `GND`
# as its candidate and CANNOT re-bond it, board unchanged, run refused.  The
# guard was not costing those edges; it was correctly PREDICTING a refusal.
#
# The refusal has one root and it is not the router.  A pad whose only bond to
# its net is pour copper is a SINGLE-POINT bond, and every route that wants to
# cross the neck cuts it.  The pad does not need the neck: it is two layers away
# from the same net's PLANE on an inner layer, and one barrel of its own puts it
# there for good.  After that the pour may be cut anywhere at all and the pad is
# still connected -- by a track and a via, which are objects a fabricator builds
# and a re-pour cannot erode.
#
# So this primitive is `stitch_pad` aimed at a pad that is ALREADY connected,
# and the only thing it adds is the right to ask.  There is no new geometry, no
# new legality argument and no new proof: the escape, the run, the barrel and
# `verify_laid` are the ones every promoted stitch on this board went through.
# Each pad is its own transaction, so a pad with no legal barrel is reverted and
# reported while the rest stand.
#
# WHY PER PAD AND NOT PER ISLAND.  A single barrel dropped inside the island
# would bond the island, and an island is exactly what a foreign track SPLITS:
# the barrel lands on one side of the cut and the pads on the other side are
# orphaned just as before.  Redundancy that survives the cut has to be attached
# to the PAD.  That is also why `bridge_islands` cannot be extended to do this
# -- it answers an island question, and this is a pad question.
def bond_pads(qb, net, field, refs, max_mm=8.0, escape_limit=12):
    """Give each NAMED pad of a pour-served net its OWN stub-and-barrel bond.

    `refs` are 'REF.NUM' strings.  Returns dict(ok, bonds, failures); on success
    the copper is on `qb` and the caller's gate owns the verdict.
    """
    if not has_plane(qb, net):
        return dict(ok=False, net=net, reason='NO_PLANE', bonds=[],
                    failures=[])
    want = list(dict.fromkeys(refs))
    pads = {p['ref']: p for p in ir.physical_net_pads(qb, net)}
    done, failed = [], []
    for ref in want:
        pad = pads.get(ref)
        if pad is None:
            failed.append(dict(ok=False, pad=ref, reason='NOT_ON_NET',
                               why='%s carries no pad %s' % (net, ref)))
            continue
        m = qb.mark()
        r = stitch_pad(qb, field, pad, max_mm=max_mm,
                       escape_limit=escape_limit)
        if r.get('ok'):
            done.append(r)
        else:
            qb.revert(m)
            failed.append(r)
    return dict(ok=bool(done), net=net, requested=len(want),
                bonded=len(done), bonds=done, failures=failed,
                mm=round(sum(d['mm'] for d in done), 3), vias=len(done))


# --------------------------------------------------------------------------- #
# POUR BRIDGES -- ONE BARREL, NO TRACK, NO ESCAPE
# --------------------------------------------------------------------------- #
# `stitch_pad` asks a PAD to launch: an escape, a short run, a barrel.  That is
# the only way off a pad sitting on BARE laminate, and it is the wrong primitive
# for a pad sitting on its own SEVERED PIECE OF POUR.  There the copper is
# already there.  An island is a two-dimensional conductor, so a barrel dropped
# anywhere inside it bonds every pad on it -- with no escape, no stub and no
# track -- and the escape search `stitch_pad` insists on is precisely what fails
# on a fine-pitch power pad in a 0.30 mm field.
#
# D-594 measured the second half of that sentence and it is the reason this
# primitive exists rather than a flag on the old one.  `stitch_pad` plants the
# NEAREST legal barrel and has no notion of what its barrel LANDS ON: on `U1.2`
# it took a site that merged the cluster with the cluster's OWN In3 island and
# closed no edge at all, while the screen had already named a site 1.5 mm away
# where the same cluster's `F` copper lies over the pour BODY.  A landing rule
# is not a search heuristic here, it is the whole content of the move.
#
# So `bridge_islands` asks exactly one question per orphan cluster:
#
#     is there a point inside THIS cluster's filled copper on one layer and
#     inside ANOTHER cluster's filled copper on a DIFFERENT layer, at which a
#     through barrel is legal?
#
# and lays one via there.  Nothing else.  The geometry is read from KiCad's own
# filled polygon set, legality is `Field.via_ok` -- the same lattice every
# promoted barrel on this board was chosen from -- and the emitted via is
# re-proved by `verify_laid` like any other object.
#
# THE FINE-PITCH LICENCE IS READ FROM THE BOARD, NEVER ASSUMED.  Most of these
# clusters have no legal site at the POWER-class 0.65/0.40 mm stitch barrel and
# do have one at 0.35/0.20 mm, which this board's `.kicad_dru` already licenses
# by name in six places (D-257 / D-266 / D-531) over the same plated
# through-hole process.  `bridge_licence` will only return a geometry that the
# board's own rule text grants TO THIS NET inside a rule area named for THIS
# cluster, so the router cannot invent a drill the fabricator was never told
# about, and a bridge whose licence is missing is refused and reported.

BRIDGE_AREA_PREFIX = "POUR_BRIDGE_"

_RULE_RE = re.compile(
    r'\(rule\s+"([^"]*)"\s*((?:\(constraint[^()]*(?:\([^()]*\)[^()]*)*\)\s*)+)'
    r'\(condition\s+"([^"]*)"\)\s*\)', re.S)
_CONSTRAINT_RE = re.compile(
    r'\(constraint\s+(\w+)\s*\(min\s+([0-9.]+)mm\)')


def bridge_area_name(label):
    """The rule-area name that licenses THIS cluster's bridge barrel.

    Derived from the cluster's own first pad -- `R19.1` -> `POUR_BRIDGE_R19_1`
    -- so the name is a property of the CLUSTER and not of the site.  That is
    what lets the `.kicad_dru` rule be authored, reviewed and committed BEFORE
    the router picks a coordinate, and it is what makes the licence checkable:
    the area the transaction draws must be the area the rule names.
    """
    return BRIDGE_AREA_PREFIX + str(label).replace('.', '_')


def dru_rules(qb):
    """Every `.kicad_dru` rule as (name, {constraint: min_nm}, condition)."""
    dru = Path(qb.b.GetFileName()).with_suffix('.kicad_dru')
    if not dru.exists():
        return []
    out = []
    for name, body, cond in _RULE_RE.findall(dru.read_text(encoding='utf-8')):
        got = {}
        for c, mm in _CONSTRAINT_RE.findall(body):
            got[c] = int(round(float(mm) * qr.MM))
        out.append((name, got, cond))
    return out


def area_licence(qb, net, area):
    """The barrel this board LICENSES for `net` inside rule area `area`, or None.

    Accepts only a rule whose condition is exactly

        A.NetName == '<net>' && A.enclosedByArea('<area>')

    and only the three constraints a barrel owes: `via_diameter`,
    `annular_width` and `hole_size`.  A rule with any other term is ignored
    rather than guessed at, so broadening the rule text can never silently
    broaden the router.  Returns dict(area, via_dia, via_drill, annular, rules)
    built from the rule MINIMA, which is the smallest barrel the board admits
    there -- the request itself is clamped up to it by the caller.

    D-606 made this a function of the AREA NAME rather than of the bridge, so
    the pour bridge and the pad-escape relief read one implementation.  The
    two callers differ only in which name they ask about, which is the whole
    difference between the two moves.
    """
    want = "A.NetName == '%s' && A.enclosedByArea('%s')" % (net, area)
    got, names = {}, []
    for name, cons, cond in dru_rules(qb):
        if ' '.join(cond.split()) != want:
            continue
        for k in ('via_diameter', 'annular_width', 'hole_size'):
            if k in cons:
                got[k] = cons[k]
                names.append(name)
    if len(got) != 3:
        return None
    return dict(area=area, via_dia=got['via_diameter'],
                via_drill=got['hole_size'], annular=got['annular_width'],
                rules=sorted(set(names)))


def bridge_licence(qb, net, label):
    """The barrel this board licenses for THIS cluster's bridge, or None."""
    return area_licence(qb, net, bridge_area_name(label))


ESCAPE_AREA_PREFIX = "PAD_ESCAPE_"


def escape_area_name(ref):
    """The rule-area name that licenses THIS PAD's escape barrel.

    `C5.1` -> `PAD_ESCAPE_C5_1`.  Derived from the pad, exactly as
    `bridge_area_name` is derived from the cluster, and for the same reason:
    the name is a property of the object the doctrine names -- one rule area
    per pad -- so the `.kicad_dru` rule can be authored, reviewed and
    committed BEFORE the router picks a coordinate, and the area the
    transaction draws must be the area the rule already names.
    """
    return ESCAPE_AREA_PREFIX + str(ref).replace('.', '_')


def escape_licence(qb, net, ref):
    """The barrel this board licenses for THIS PAD's escape, or None."""
    return area_licence(qb, net, escape_area_name(ref))


ESCAPE_RUN_AREA_PREFIX = "PAD_ESCAPE_RUN_"


def escape_run_area_name(ref):
    """The rule-area name that licenses THIS PAD's escape RUN width.

    `U12.4` -> `PAD_ESCAPE_RUN_U12_4`.  A DIFFERENT object from
    `escape_area_name`, and deliberately so: D-606's `PAD_ESCAPE_<REF>` areas
    license a BARREL and license nothing about width, and D-609 measured the
    consequence -- a relief whose BARREL was ordinary and whose RUN was
    0.200 mm was refused for six real `track_width` errors, because the only
    width licence within reach was the `intersectsCourtyard` necking rule that
    `FBV2_P2_ROUTING_PLAN.md` section 17 clause 2 forbids leaning on.  The two
    names are separate so that a transaction that needs one cannot silently
    inherit the other.
    """
    return ESCAPE_RUN_AREA_PREFIX + str(ref).replace('.', '_')


_WIDTH_RULE_RE = re.compile(
    r'\(rule\s+"([^"]*)"\s*\(constraint\s+track_width\s*\(min\s+'
    r'([0-9.]+)mm\)\s*\)\s*\(condition\s+"([^"]*)"\)\s*\)', re.S)


def width_licence(qb, net, ref):
    """The narrowest TRACK this board licenses for THIS PAD's run, or None.

    Accepts only a rule whose condition is exactly

        A.NetName == '<net>' && A.enclosedByArea('PAD_ESCAPE_RUN_<REF>')

    and only a `track_width (min ...)` constraint -- the same read
    `area_licence` makes for a barrel, asked about the one geometry a barrel
    licence says nothing about.  `enclosedByArea`, never `intersectsArea`:
    KiCad evaluates membership per OBJECT, so a track that merely clipped the
    area would inherit the relaxation along its whole length, and section 17
    clause 2 names that shape by name.  Returns nm, or None when the board
    carries no such rule -- which is a REFUSAL at the caller, never a default.
    """
    want = ("A.NetName == '%s' && A.enclosedByArea('%s')"
            % (net, escape_run_area_name(ref)))
    dru = Path(qb.b.GetFileName()).with_suffix('.kicad_dru')
    if not dru.exists():
        return None
    got = None
    for name, mm, cond in _WIDTH_RULE_RE.findall(
            dru.read_text(encoding='utf-8')):
        if ' '.join(cond.split()) != want:
            continue
        got = int(round(float(mm) * qr.MM))      # LAST matching rule wins
    return got


def laid_track_bbox(qb, mark, below=0):
    """Bounding box in nm of the TRACKS laid since `mark`, caps included.

    `below` keeps only tracks narrower than that width -- the sub-class-width
    copper a width licence has to cover -- and each track is grown by its own
    half-width, which is exactly how KiCad extends a segment's end cap and is
    the whole reason section 17 clause 7 asks for an overhang at all.  Returns
    None when the run laid no such track, so a caller can tell "nothing to
    license" from "a box of zero size".
    """
    x0 = y0 = x1 = y1 = None
    for t in qb.laid[mark[0]:]:
        if t.GetClass() != 'PCB_TRACK':      # a via is a PCB_TRACK subclass
            continue
        w = int(t.GetWidth())
        if below and w >= below:
            continue
        h = w / 2.0
        a, b = t.GetStart(), t.GetEnd()
        for (px, py) in ((int(a.x), int(a.y)), (int(b.x), int(b.y))):
            lo_x, hi_x, lo_y, hi_y = px - h, px + h, py - h, py + h
            x0 = lo_x if x0 is None else min(x0, lo_x)
            y0 = lo_y if y0 is None else min(y0, lo_y)
            x1 = hi_x if x1 is None else max(x1, hi_x)
            y1 = hi_y if y1 is None else max(y1, hi_y)
    if x0 is None:
        return None
    return (x0, y0, x1, y1)


# -- pour geometry ---------------------------------------------------------- #
def filled_islands(qb, net):
    """[(layer_name, index, SHAPE_POLY_SET, area_mm2)] for every filled island.

    KiCad's own filled polygon set, one entry per (layer, outline), holes
    carried on the outline they belong to.  This is the copper a fabricator
    gets, not a re-derivation of it.
    """
    import pcbnew
    out = []
    for z in qb.b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net or not z.IsFilled():
            continue
        for lname, lid in qr.LNAME.items():
            if not z.IsOnLayer(lid):
                continue
            shape = z.GetFilledPolysList(lid)
            for i in range(shape.OutlineCount()):
                poly = pcbnew.SHAPE_POLY_SET()
                poly.AddOutline(shape.Outline(i))
                for h in range(shape.HoleCount(i)):
                    poly.AddHole(shape.Hole(i, h), 0)
                out.append((lname, len(out), poly,
                            abs(shape.Outline(i).Area()) / 1e12))
    return out


def pour_clusters(qb, net):
    """Union-find over this net's pads AND VIAS, using KiCad connectivity.

    Vias are in because a cluster's copper often reaches an inner layer only
    through one: `+3V3`'s `C3.1/R2.1/R27.1` owns an `F` island and an `In3`
    island, and only the barrel between them says so.  Returns
    (roots, items) with `items[key] = dict(kind, x, y, layers)`.
    """
    qb.b.BuildConnectivity()
    conn = qb.b.GetConnectivity()
    items, handles = {}, {}
    for f in qb.b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net or not p.GetNumber():
                continue
            pos = p.GetPosition()
            key = ('P', f.GetReference() + '.' + p.GetNumber(), pos.x, pos.y)
            items[key] = dict(kind='pad', x=pos.x, y=pos.y,
                              layers=tuple(L for L, lid in qr.LNAME.items()
                                           if p.IsOnLayer(lid)))
            handles[key] = p
    for t in qb.b.GetTracks():
        if t.GetClass() != 'PCB_VIA' or t.GetNetname() != net:
            continue
        pos = t.GetPosition()
        key = ('V', '', pos.x, pos.y)
        items[key] = dict(kind='via', x=pos.x, y=pos.y,
                          layers=tuple(L for L, lid in qr.LNAME.items()
                                       if t.IsOnLayer(lid)))
        handles[key] = t

    parent = {k: k for k in items}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    bykey = {}
    for key, h in handles.items():
        bykey.setdefault((h.GetPosition().x, h.GetPosition().y), []).append(key)
    for key, h in handles.items():
        for it in conn.GetConnectedItems(h):
            if it.GetClass() not in ('PAD', 'PCB_VIA'):
                continue
            pos = it.GetPosition()
            for other in bykey.get((pos.x, pos.y), ()):
                ra, rb = find(key), find(other)
                if ra != rb:
                    parent[ra] = rb
    return {k: find(k) for k in items}, items


def island_owner(islands, roots, items):
    """island index -> cluster root, by containment of a pad or via of it."""
    import pcbnew
    owner = {}
    for lname, idx, poly, _a in islands:
        found = None
        for key, meta in items.items():
            if lname not in meta['layers'] and meta['kind'] == 'pad':
                continue
            if poly.Contains(pcbnew.VECTOR2I(meta['x'], meta['y'])):
                found = roots[key]
                break
        owner[idx] = found
    return owner


def poly_rings(poly):
    """Every closed ring of a SHAPE_POLY_SET as (xs, ys), holes included.

    Under the even-odd rule a point inside outline-and-hole is crossed twice
    and falls out, which is exactly the containment `SHAPE_POLY_SET.Contains`
    reports -- so the raster and the board agree about where the copper is
    without a second code path.
    """
    out = []
    for k in range(poly.OutlineCount()):
        chains = [poly.Outline(k)] + [poly.Hole(k, h)
                                      for h in range(poly.HoleCount(k))]
        for ch in chains:
            n = ch.PointCount()
            if n < 3:
                continue
            xs = np.empty(n, dtype=float)
            ys = np.empty(n, dtype=float)
            for t in range(n):
                p = ch.CPoint(t)
                xs[t], ys[t] = float(p.x), float(p.y)
            out.append((xs, ys))
    return out


def poly_mask(field, poly):
    """Lattice cells whose centre lies inside `poly`.

    The same even-odd crossing test `Neck.mask` uses on courtyards, restricted
    to the polygon's bounding box.  A per-cell `SHAPE_POLY_SET.Contains` is the
    obvious implementation and is unusable: the largest `+3V3` island alone
    covers ~400,000 lattice cells.
    """
    mask = np.zeros((field.ny, field.nx), dtype=bool)
    bb = poly.BBox()
    i0 = max(0, int((bb.GetLeft() - field.ox) // field.G))
    i1 = min(field.nx - 1, int((bb.GetRight() - field.ox) // field.G) + 1)
    j0 = max(0, int((bb.GetTop() - field.oy) // field.G))
    j1 = min(field.ny - 1, int((bb.GetBottom() - field.oy) // field.G) + 1)
    if i1 < i0 or j1 < j0:
        return mask
    X, Y = np.meshgrid(field.ox + np.arange(i0, i1 + 1) * float(field.G),
                       field.oy + np.arange(j0, j1 + 1) * float(field.G))
    hit = np.zeros(X.shape, dtype=bool)
    for xs, ys in poly_rings(poly):
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
    mask[j0:j1 + 1, i0:i1 + 1] = hit
    return mask


def _deepest(mask):
    """The cell of `mask` furthest from its boundary, ties broken by (j, i).

    A bridge site is chosen for MARGIN, not for scan order.  The barrel has to
    survive KiCad's refill, which moves a pour edge by microns, and a site one
    cell inside the overlap is the one that will not.  Erosion by the full
    8-neighbourhood, on the mask's own bounding box, costs a handful of passes
    over a few thousand cells and makes the choice both robust and
    deterministic: the last non-empty erosion is the deepest core, and the
    first cell of it in row-major order is the site.
    """
    js, iss = np.nonzero(mask)
    j0, j1 = int(js.min()), int(js.max())
    i0, i1 = int(iss.min()), int(iss.max())
    cur = mask[j0:j1 + 1, i0:i1 + 1]
    while True:
        h, w = cur.shape
        pad = np.zeros((h + 2, w + 2), dtype=bool)
        pad[1:-1, 1:-1] = cur
        nxt = cur.copy()
        for dj in (0, 1, 2):
            for di in (0, 1, 2):
                nxt &= pad[dj:dj + h, di:di + w]
        if not nxt.any():
            break
        cur = nxt
    cj, ci = np.nonzero(cur)
    return int(ci[0]) + i0, int(cj[0]) + j0


def cluster_coverage(qb, net, field):
    """Per-cluster pour coverage of the lattice.

    Returns (cov_layer, cov, size, body, label) where `cov_layer[(root, L)]` is
    the mask of cells inside that cluster's filled copper on layer `L`.
    """
    islands = filled_islands(qb, net)
    roots, items = pour_clusters(qb, net)
    owner = island_owner(islands, roots, items)
    size = {}
    for key, r in roots.items():
        if items[key]['kind'] == 'pad':
            size[r] = size.get(r, 0) + 1
    body = max(size, key=lambda r: size[r]) if size else None
    cov, cov_layer = {}, {}
    for lname, idx, poly, _area in islands:
        r = owner[idx]
        if r is None:
            continue
        m = poly_mask(field, poly)
        key = (r, lname)
        if key in cov_layer:
            cov_layer[key] |= m
        else:
            cov_layer[key] = m
        if r in cov:
            cov[r] |= m
        else:
            cov[r] = m.copy()

    def label(r):
        return sorted(k[1] for k in roots if roots[k] == r
                      and items[k]['kind'] == 'pad')

    return cov_layer, cov, size, body, {r: label(r) for r in size}, islands, owner


def _bridge_pairs(cov_layer, cov, size, body, labels):
    """Per orphan cluster, the ordered (target, from_layer, to_layer) overlaps.

    Everything here is independent of the BARREL: an overlap of two clusters'
    filled copper on two different layers is a property of the pour, so it is
    computed once and every rung of the ladder is then a single AND against
    that rung's via lattice.  Clusters are ordered body-first (a bridge to the
    plane body closes an edge outright), then by size, then by name, so the
    choice is deterministic and does not depend on dict iteration order.
    """
    out = []
    for r in sorted(size, key=lambda k: (-size[k], str(labels[k]))):
        if r == body:
            continue
        mine = cov.get(r)
        if mine is None or not mine.any():
            out.append((r, []))
            continue
        pairs = []
        for tgt in sorted(cov, key=lambda t: (t != body, -size.get(t, 0),
                                              str(labels.get(t, '')))):
            if tgt == r:
                continue
            for cl in sorted(L for (cr, L) in cov_layer if cr == r):
                for tl in sorted(L for (tr, L) in cov_layer if tr == tgt):
                    if tl == cl:
                        continue      # a barrel does work only ACROSS layers
                    m = cov_layer[(r, cl)] & cov_layer[(tgt, tl)]
                    if m.any():
                        pairs.append((tgt, cl, tl, m))
        out.append((r, pairs))
    return out


def _bridge_hit(pairs, via_ok, field, labels, body):
    """The first (target, layer, layer) overlap this via lattice admits."""
    for tgt, cl, tl, m in pairs:
        cand = m & via_ok
        if not cand.any():
            continue
        i, j = _deepest(cand)
        x, y = field.point(i, j)
        return dict(from_layer=cl, to_layer=tl, sites=int(cand.sum()),
                    xy=[x, y], xy_mm=[round(x / 1e6, 4), round(y / 1e6, 4)],
                    to_cluster=labels.get(tgt, [])[:4],
                    to_is_body=bool(tgt == body))
    return None


def bridge_sites(qb, net, field):
    """Every orphan cluster of `net`, with the ONE barrel site that joins it.

    Read-only and deterministic: the screen reports exactly what the emitter
    would lay at this geometry, because both go through `_bridge_pairs` and
    `_bridge_hit`.
    """
    cov_layer, cov, size, body, labels, islands, owner = \
        cluster_coverage(qb, net, field)
    out = []
    for r, pairs in _bridge_pairs(cov_layer, cov, size, body, labels):
        entry = dict(cluster=labels[r], pads=size[r], site=None,
                     islands=[dict(layer=l, mm2=round(a, 2))
                              for l, i, _p, a in islands if owner[i] == r])
        if not pairs:
            entry['why'] = (
                'cluster owns no filled pour island'
                if r not in cov or not cov[r].any() else
                "this island overlaps no other cluster's copper on "
                "another layer")
            out.append(entry)
            continue
        entry['site'] = _bridge_hit(pairs, field.via_ok, field, labels, body)
        if entry['site'] is None:
            entry['why'] = ('no legal %.2f mm barrel inside this island over '
                            'any other cluster' % (field.via_dia / 1e6))
        out.append(entry)
    return out


def _meets_floors(dia, drill, floors):
    """True when this barrel needs no `.kicad_dru` exception at all."""
    return (dia >= floors['dia'] and drill >= floors['drill']
            and (dia - drill) / 2.0 >= floors['annular'])


def _barrel_licensed(dia, drill, floors, lic):
    """Is this barrel legal on the board's ORDINARY floors, or DRU-licensed?

    A barrel at or above every ordinary floor -- the board setup's
    `min_via_diameter` and `min_through_hole_diameter`, the unconditional
    `.kicad_dru` `Via annular ring floor`, and the POWER-class `hole_size`
    minimum where the net's class is named by it -- needs no exception and gets
    none: it is the same barrel every stitch on this board already lays.
    `floors` is handed in by the caller, which owns the transcription of those
    rules, so this can never disagree with the driver's own contract table.

    Only a barrel BELOW a floor needs the rule text, and then it must satisfy
    EVERY minimum that rule states -- diameter, drill and annular ring alike.
    """
    if _meets_floors(dia, drill, floors):
        return True
    if lic is None:
        return False
    return (dia >= lic['via_dia'] and drill >= lic['via_drill']
            and (dia - drill) / 2.0 >= lic['annular'])


def bridge_islands(qb, net, width, clr_pad, clr_trk, ladder, floors,
                   G=100000, layers=None, guard=None, licence=True):
    """Lay ONE barrel per bridgeable orphan cluster.  No track, no escape.

    `ladder` is [(via_dia, via_drill), ...] COARSEST FIRST, and each cluster
    takes the coarsest rung that has a legal site.  That ordering is the whole
    electrical content of the primitive: `U1.2` is the ESP32-S3 module's +3V3
    pin and must not be bonded by the finest barrel merely because the finest
    barrel fits everywhere.  A cluster served by an early rung is retired, so a
    later rung is only ever asked about the clusters still open.

    Each bridge is an independent transaction, like a stitch island: one that
    cannot be licensed or cannot be proved is reverted on its own and reported,
    and the others stand.  With `licence=True` -- the only mode a promotion may
    use -- a barrel below an ordinary floor is emitted only where the
    `.kicad_dru` grants THIS net THAT geometry inside the rule area named for
    THIS cluster, so the router cannot invent a drill the fabricator was never
    told about.
    """
    if not has_plane(qb, net):
        return dict(ok=False, net=net, reason='NO_PLANE')
    # The lattice, and therefore the coverage masks, do not depend on the
    # barrel; only `via_ok` does.  So the expensive rasterisation of KiCad's
    # filled polygon set happens ONCE and every rung is one AND against it.
    base = Field(qb, net, width, clr_pad, clr_trk, ladder[0][0], ladder[0][1],
                 G=G, layers=layers, guard=guard)
    cov_layer, cov, size, body, labels, islands, owner = \
        cluster_coverage(qb, net, base)
    pending = _bridge_pairs(cov_layer, cov, size, body, labels)
    done, failed, laid_xy = [], [], []
    for rung, (dia, drill) in enumerate(ladder):
        if not pending:
            break
        if rung:
            base.via_dia, base.via_drill = dia, drill
            base.via_ok = base._via_grid()
            for m in base._guard.values():
                base.via_ok &= ~m
            for (x, y) in laid_xy:
                forbid_via(base, x, y)
        still = []
        for r, pairs in pending:
            label = labels[r][0] if labels[r] else None
            hit = _bridge_hit(pairs, base.via_ok, base, labels,
                              body) if pairs else None
            if hit is None:
                still.append((r, pairs))
                continue
            plain = _meets_floors(dia, drill, floors)
            lic = None if plain else (bridge_licence(qb, net, label)
                                      if licence else None)
            if licence and not _barrel_licensed(dia, drill, floors, lic):
                failed.append(dict(cluster=labels[r], reason='NO_DRU_LICENCE',
                                   via_dia=dia, via_drill=drill,
                                   xy_mm=hit['xy_mm'],
                                   why='no .kicad_dru rule grants %s a '
                                       '%.2f/%.2f mm barrel inside %s'
                                       % (net, dia / 1e6, drill / 1e6,
                                          bridge_area_name(label))))
                continue
            x, y = hit['xy']
            m = qb.mark()
            qb.via(net, x, y, dia, drill)
            forbid_via(base, x, y)
            bad = verify_laid(qb, base, m)
            if bad is not None:
                qb.revert(m)
                failed.append(dict(cluster=labels[r],
                                   reason='UNPROVED_GEOMETRY',
                                   why='%s at %s vs %s'
                                       % (bad.get('kind'), bad.get('at'),
                                          bad.get('against', bad.get('why'))),
                                   detail=bad))
                continue
            laid_xy.append((x, y))
            done.append(dict(cluster=labels[r], pads=size[r],
                             area=(None if plain
                                   else bridge_area_name(label)),
                             needs_licence=(not plain), licence=lic,
                             via_dia=dia, via_drill=drill, rung=rung,
                             xy=[x, y], xy_mm=hit['xy_mm'],
                             from_layer=hit['from_layer'],
                             to_layer=hit['to_layer'],
                             to_cluster=hit['to_cluster'],
                             to_is_body=hit['to_is_body'],
                             sites=hit['sites'],
                             islands=[dict(layer=l, mm2=round(a, 2))
                                      for l, i, _p, a in islands
                                      if owner[i] == r]))
        pending = still
    for r, pairs in pending:
        failed.append(dict(cluster=labels[r], reason='NO_BRIDGE',
                           why=('cluster owns no filled pour island'
                                if not pairs else
                                'no legal barrel on this ladder inside this '
                                'island over any other cluster')))
    return dict(ok=bool(done), net=net, bridged=len(done),
                unbridged=len(failed), bridges=done, failures=failed[:40],
                vias=len(done), ladder=[[d, k] for d, k in ladder])


# --------------------------------------------------------------------------- #
# POUR-ISLAND JOINS -- A JUMPER BETWEEN TWO PIECES OF THE SAME POUR
# --------------------------------------------------------------------------- #
# D-605.  `bridge_islands` is the ZERO-LENGTH case of a more general move, and
# naming it that way is the whole content of this primitive.
#
# A bridge asks: is there one point inside cluster A's copper on one layer and
# inside cluster B's copper on ANOTHER layer, at which a barrel is legal?  When
# the two pieces of pour happen to lie over each other, one via joins them and
# nothing else is needed.  When they do NOT -- and on this board they usually do
# not, because a pour-owning net's islands are pieces of ONE layer's pour that a
# foreign track has cut -- the bridge has no pair to offer and reports
# `NO_BRIDGE`, even where the two pieces are seven tenths of a millimetre apart.
#
# The general move is a JUMPER: leave cluster A's copper, cross the cut, land on
# cluster B's copper.  It may take a via up and a via back down, or it may stay
# on one layer and go round the end of the cut.  A bridge is exactly the case
# where that jumper has length zero.
#
# WHY `route_join` CANNOT DO THIS, AND IT IS NOT A TUNING QUESTION.
# `route_join` seeds its wavefront from `pad_escapes` at BOTH ends, so both
# terminals must be a PAD that can launch a full-width track.  That is the right
# and only contract for a pad on bare laminate.  It is the wrong one for a pad
# sitting on its own severed piece of pour: the copper is already there, the
# island is a two-dimensional conductor, and a track that starts INSIDE it needs
# no escape at all.  The escape search is precisely what fails on these -- a
# fine-pitch power pad in a 0.30 mm field has no 0.60 mm launch in any
# direction -- so `route_join` refuses `NO_LEGAL_ESCAPE_SRC` on a join whose
# real difficulty is zero.  D-604 measured the same wall from the other side:
# `+3V3` 0 of 15 and `GND` 0 of 9 orphan islands close at ANY rung of the
# stitch ladder, because the stitch, too, insists a pad launch.
#
# THE ANCHOR CONTRACT, WHICH IS WHAT MAKES THE TERMINAL PROVABLE.
# A track laid at a cell that merely lies inside the filled polygon is not
# enough: KiCad moves a pour edge by microns on every refill, and the promoted
# board is refilled.  So an endpoint must be an ANCHOR -- a cell at least
# `width/2 + one lattice cell` INSIDE this cluster's own filled copper, found by
# eroding KiCad's own filled polygon mask.  A track of that width centred on an
# anchor lies WHOLLY within copper that is already there, so the connection is a
# geometric fact and not a fill artefact.  A cluster with no anchor at any width
# is reported `NO_ANCHOR` and nothing is laid.
#
# Everything else is the machinery every promoted join on this board went
# through: `Field` for legality, `wave3d`/`descend3d` for the corridor,
# `QBoard.smooth` + `qrouter.simplify` for the geometry, the same
# hole-to-hole proof between this join's own barrels, and `verify_laid` to
# re-prove every emitted object analytically.  A join that cannot be proved is
# reverted whole.
def _erode(mask, k):
    """`mask` eroded by `k` steps of the full 8-neighbourhood.

    The same erosion `_deepest` uses to find a bridge site with margin, run a
    fixed number of times instead of to exhaustion.  Done on the mask's own
    bounding box: a whole-board array is 400,000 cells and an island is a few
    thousand of them.
    """
    if k <= 0 or not mask.any():
        return mask
    js, iss = np.nonzero(mask)
    j0, j1 = int(js.min()), int(js.max())
    i0, i1 = int(iss.min()), int(iss.max())
    cur = mask[j0:j1 + 1, i0:i1 + 1]
    for _ in range(k):
        h, w = cur.shape
        pad = np.zeros((h + 2, w + 2), dtype=bool)
        pad[1:-1, 1:-1] = cur
        nxt = cur.copy()
        for dj in (0, 1, 2):
            for di in (0, 1, 2):
                nxt &= pad[dj:dj + h, di:di + w]
        cur = nxt
        if not cur.any():
            break
    out = np.zeros_like(mask)
    out[j0:j1 + 1, i0:i1 + 1] = cur
    return out


def island_anchors(field, cov_layer, root, width):
    """{layer: mask} of cells a `width` track may TERMINATE on for this cluster.

    An anchor owes two independent things and both are checked here: the cell
    must be legal for this net at this width (`~Field.blk`, which already
    carries the .kicad_dru overlay and the pour-bond guard), and it must be far
    enough inside this cluster's OWN filled copper that a track of that width
    centred on it cannot leave the copper.
    """
    k = int(math.ceil((width / 2.0) / float(field.G))) + 1
    out = {}
    for (r, L) in cov_layer:
        if r != root or L not in field.layers:
            continue
        m = _erode(cov_layer[(r, L)], k) & ~field.blk[L]
        if m.any():
            out[L] = m
    return out


def _cells(anchors, cap=0):
    """`{layer: mask}` as a deterministic [(layer, i, j)] list.

    With `cap`, the list is thinned by a fixed stride rather than truncated, so
    a large island is still represented across its whole extent.  The stride is
    a function of the mask alone, so two runs on the same board produce the
    same list.
    """
    out = []
    for L in sorted(anchors):
        js, iss = np.nonzero(anchors[L])
        out += [(L, int(i), int(j)) for i, j in zip(iss, js)]
    if cap and len(out) > cap:
        step = int(math.ceil(len(out) / float(cap)))
        out = out[::step]
    return out


def _emit_path(qb, field, path, net, head=None, tail=None):
    """Lay a descended path as tracks and barrels.  No escape at either end.

    Shares `route_join`'s geometry exactly -- per-layer runs, `QBoard.smooth`
    against that layer's own blocked grid, `qrouter.simplify`, the same
    hole-to-hole proof between this transaction's own barrels and the same
    `verify_laid` re-proof -- and differs from it in one respect only: the
    terminals are cells inside existing copper rather than pad escapes.

    `head` / `tail` REPLACE the first and last vertex with an EXACT board
    coordinate, which is what `route_points` needs and what a cell can never
    express.  A lattice cell is a rounding of a place; the two ends of a track
    a detour is putting back are the place itself, and landing a micron away
    from either would strand whatever met it.  The substituted vertex is not
    trusted: `verify_laid` re-proves the segment it creates against the same
    obstacle set and clearance as every other segment, and a detour whose
    connector cannot be proved is reverted whole.  Absent both arguments this
    function is byte-identical to the one `join_islands` has always called.
    """
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

    if head is not None or tail is not None:
        polylines = [(k, list(pts)) for k, pts in polylines]
        if head is not None:
            polylines[0][1][0] = (int(head[0]), int(head[1]))
        if tail is not None:
            polylines[-1][1][-1] = (int(tail[0]), int(tail[1]))
        # A one-cell path collapses to a single vertex once both ends are
        # substituted; the run it stands for is the straight segment between
        # the two exact points, and dropping it would silently emit nothing.
        if (len(polylines) == 1 and head is not None and tail is not None
                and len(polylines[0][1]) < 2):
            polylines[0] = (polylines[0][0], [(int(head[0]), int(head[1])),
                                              (int(tail[0]), int(tail[1]))])
        polylines = [(k, [p for n, p in enumerate(pts)
                          if n == 0 or p != pts[n - 1]])
                     for k, pts in polylines]

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
    if len(polylines) == 1 and len(polylines[0][1]) < 2:
        return dict(ok=False, reason='NO_OP',
                    why='the two clusters share a cell on one layer; there is '
                        'nothing to lay')
    m = qb.mark()
    total, vias = 0.0, []
    # PER-LAYER LENGTH, BECAUSE A LAYER IS NOT ALWAYS JUST A PLACE.  `layers`
    # already said WHICH layers a run touched; on a RESERVED inner plane the
    # question a caller has to answer is HOW MUCH, because foreign copper there
    # is a slot through somebody else's plane and its area is width x length.
    # Additive: every existing caller reads `mm` and `layers` unchanged.
    by_layer = {}
    prev = None
    for k, pts in polylines:
        if prev is not None:
            vx, vy = pts[0]
            qb.via(net, vx, vy, field.via_dia, field.via_drill)
            forbid_via(field, vx, vy)
            vias.append((vx, vy))
        for a, b in zip(pts, pts[1:]):
            qb.track(net, k, a[0], a[1], b[0], b[1], field.width)
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            total += d
            by_layer[k] = by_layer.get(k, 0.0) + d
        prev = k
    bad = verify_laid(qb, field, m)
    if bad is not None:
        qb.revert(m)
        return dict(ok=False, reason='UNPROVED_GEOMETRY', detail=bad)
    return dict(ok=True, mm=total / 1e6, vias=len(vias), mark=m,
                via_xy=[(round(x / 1e6, 4), round(y / 1e6, 4))
                        for x, y in vias],
                mm_by_layer={k: round(v / 1e6, 4)
                             for k, v in sorted(by_layer.items())},
                layers=[k for k, _ in polylines])


# THE BARRELS ARE SCISSORS, AND THE FIRST GATE RUN PROVED IT ON THE BOARD.
# D-605's first whole-board run closed `+3V3` `C3.1/R2.1/R27.1` with an
# `In3 -> F -> In3` jumper whose two 0.80 mm through barrels landed at
# (64.0, 98.7) and (61.7, 99.1) -- 2.34 mm apart, across the waist of
# `/01_POWER_TREE/BQ25185_SYS`'s 98 mm2 `B.Cu` pour island -- and that island
# came apart into `SW9.2` and `U12.1`.  Whole-board edges 69 -> 69, one net
# improved, one regressed, REFUSED by clause 4.
#
# A through barrel is a hole and an antipad on EVERY copper layer, so dropping
# one inside a foreign pour is a slot through that pour, exactly as a foreign
# TRACK on a plane layer is -- which is what `reserved_inner_planes` already
# exists for.  A big plane survives it: every signal via on this board passes
# through `In1` and `In4`.  A 98 mm2 island with a narrow waist does not.
#
# THE TEST HAS TO MODEL THE REFILL, AND THE OBVIOUS TEST DOES NOT.  The first
# version of this check retook every foreign pour net's cluster count from
# KiCad's own connectivity after laying the jumper, and it caught NOTHING: the
# proposer does not refill zones, so the foreign pour on the in-memory board is
# still the one that was filled before the barrel existed.  The damage is a FILL
# consequence and is invisible to connectivity until `--refill-zones` runs, which
# is precisely why the whole-board gate refills and recounts.
#
# So the predictor is GEOMETRIC and models exactly what the refill will do:
# subtract each barrel's antipad -- its own radius plus the clearance that pour
# is filled with -- from KiCad's own filled polygon, and ask whether that net's
# lands, which the intact island held together, are still in ONE piece.  If they
# are not, the jumper is reverted, the island is closed to this transaction's
# barrels, and the search is retried.  The gate remains the authority; this
# moves the refusal from a six-minute whole-board run into the search itself.
def _foreign_pours(qb, net):
    """Other nets that own a filled pour, in a deterministic order."""
    return sorted({z.GetNetname() for z in qb.b.Zones()
                   if not z.GetIsRuleArea() and z.IsFilled()
                   and z.GetNetname() and z.GetNetname() != net})


# THE ANTIPAD A REFILL ACTUALLY CUTS IS WIDER THAN THE CLEARANCE, AND THE TWO
# D-605 GATE RUNS CALIBRATE IT EXACTLY.  KiCad's fill first holds the pour
# `clearance` away from the barrel and then removes whatever neck is left that
# is thinner than the zone's `min_thickness`, so along a neck a barrel deletes
# copper out to `clearance + min_thickness`, not to `clearance`.  Measured on
# `/01_POWER_TREE/BQ25185_SYS`'s 98.38 mm2 `B.Cu` island, whose zone is filled
# at 0.25 mm clearance with 0.20 mm min thickness:
#
#   radius             run 1 (0.80 mm vias, gate REFUSED)  run 2 (0.65, PASSED)
#   dia/2 + clr        intact                              intact
#   dia/2 + clr + mt/2 intact                              intact
#   dia/2 + clr + mt   SEVERED                             intact
#
# and the real refill split that island into 87.39 + 5.74 mm2 on run 1 and left
# it whole at 95.41 mm2 on run 2.  So the last row is the model: it is the only
# one that reproduces both verdicts, and being the widest of the three it is
# also the conservative choice for a pre-filter.
def _pour_geometry(qb, net):
    """(clearance, min_thickness) the widest of `net`'s filled zones is poured
    with, read off the zones rather than transcribed."""
    clr = mt = 0
    for z in qb.b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net or not z.IsFilled():
            continue
        try:
            c = z.GetLocalClearance()
        except Exception:
            c = None
        clr = max(clr, int(c) if c else 0)
        mt = max(mt, int(z.GetMinThickness()))
    return (clr or 250000), (mt or 200000)


def _antipad_severs(qb, net, sites, via_dia):
    """Which of `net`'s filled islands would a barrel at each site cut in two?

    `sites` are (x, y) in nm.  For each island the barrels' antipads are
    subtracted from KiCad's own filled polygon and the island's own lands are
    re-located in what is left; an island whose lands end up in two or more
    surviving pieces is SEVERED.  Returns [(layer, index, poly, area, why)].
    """
    import pcbnew
    if not sites:
        return []
    clr, mt = _pour_geometry(qb, net)
    r = via_dia / 2.0 + clr + mt
    lands = [(m['x'], m['y']) for m in
             (pour_clusters(qb, net)[1]).values()]
    cut = []
    for lname, idx, poly, area in filled_islands(qb, net):
        hit = [(x, y) for (x, y) in sites
               if poly.Contains(pcbnew.VECTOR2I(int(x), int(y)))
               or poly.Collide(pcbnew.VECTOR2I(int(x), int(y)), int(r))]
        if not hit:
            continue
        mine = [(x, y) for (x, y) in lands
                if poly.Contains(pcbnew.VECTOR2I(int(x), int(y)))]
        if len(mine) < 2:
            continue
        holes = pcbnew.SHAPE_POLY_SET()
        for (x, y) in hit:
            holes.AddOutline(pcbnew.SHAPE_LINE_CHAIN(
                [pcbnew.VECTOR2I(int(x + r * math.cos(t * math.pi / 16)),
                                 int(y + r * math.sin(t * math.pi / 16)))
                 for t in range(32)], True))
        rest = pcbnew.SHAPE_POLY_SET(poly)
        rest.BooleanSubtract(holes)
        where = set()
        for (x, y) in mine:
            for k in range(rest.OutlineCount()):
                piece = pcbnew.SHAPE_POLY_SET()
                piece.AddOutline(rest.Outline(k))
                if piece.Contains(pcbnew.VECTOR2I(int(x), int(y))):
                    where.add(k)
                    break
        if len(where) > 1:
            cut.append((lname, idx, poly, area,
                        '%d land(s) of %s on this %s island end in %d separate '
                        'pieces once the %.2f mm antipad is subtracted'
                        % (len(mine), net, lname, len(where), 2 * r / 1e6)))
    return cut


def join_islands(qb, net, field, via_cost_mm=1.5, max_mm=0.0, emit=True,
                 goal_cap=3000, tries=3):
    """Join every orphan pour island of `net` to the rest of the net.

    One transaction per orphan cluster: a jumper from a cell inside that
    cluster's own filled copper to a cell inside another cluster's, with no pad
    escape at either end.  Targets are tried BODY FIRST and then by size, which
    is `_bridge_pairs`' own ordering and is deterministic.

    Merging any two clusters closes exactly one open edge, so an orphan joined
    to another orphan is worth the same as one joined to the body -- but the
    body is preferred because a jumper to the plane body is the shorter claim
    to review.  Returns dict(ok, joined, joins, failures).

    `emit=False` still LAYS each jumper, proves it and reverts it, so a screen
    and a gate cannot disagree about whether a join is legal or about whether it
    severs a foreign pour; what `emit=False` changes is only that the copper does
    not stay.  `tries` bounds the retry loop after a severance.
    """
    if not has_plane(qb, net):
        return dict(ok=False, net=net, reason='NO_PLANE', joins=[],
                    failures=[])
    cov_layer, cov, size, body, labels, _islands, _owner = \
        cluster_coverage(qb, net, field)
    if body is None or len(size) < 2:
        return dict(ok=True, net=net, joined=0, joins=[], failures=[],
                    reason='NOTHING_TO_JOIN')
    anchors = {r: island_anchors(field, cov_layer, r, field.width)
               for r in size}
    vc = max(1, int(round(via_cost_mm * qr.MM / field.G)))
    budget = (WAVE_STEPS if not max_mm
              else max(1, int(round(max_mm * qr.MM / field.G))))

    # Union-find over cluster roots, so a cluster joined earlier in this run is
    # a legal target for a later one and the anchor masks merge with it.
    parent = {r: r for r in size}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    merged = {r: dict(anchors[r]) for r in size}
    foreign = _foreign_pours(qb, net)
    done, failed = [], []
    for r in sorted(size, key=lambda k: (-size[k], str(labels[k]))):
        if find(r) == find(body):
            continue
        mine = merged[find(r)]
        if not mine:
            failed.append(dict(cluster=labels[r], pads=size[r],
                               reason='NO_ANCHOR',
                               why='no cell of this cluster\'s filled copper '
                                   'admits a %.3f mm track centred %.3f mm '
                                   'inside it'
                                   % (field.width / 1e6,
                                      field.width / 2e6 + field.G / 1e6)))
            continue
        goals = _cells(mine, goal_cap)
        laid, tgt, shut, last = None, None, [], None
        for _try in range(max(1, tries)):
            best = None
            for cand in sorted(size, key=lambda t: (find(t) != find(body),
                                                    -size.get(t, 0),
                                                    str(labels.get(t, '')))):
                if find(cand) == find(r):
                    continue
                seeds = _cells(merged[find(cand)])
                if not seeds:
                    continue
                dist, hit = wave3d(field, seeds, goals, vc, budget=budget)
                if dist is None or hit is None:
                    continue
                path = descend3d(field, dist, hit, vc)
                if path is None:
                    continue
                best = (cand, path)
                break
            if best is None:
                last = dict(reason='NO_PATH',
                            why='no all-layer corridor at %.3f mm from this '
                                'island to any other cluster of the net'
                                % (field.width / 1e6))
                break
            cand, path = best
            # THE PROOF IS THE SAME WHETHER OR NOT THE COPPER STAYS.  A dry run
            # lays the jumper, proves it, and reverts it, so a screen and a gate
            # cannot disagree about whether a join severs a foreign pour.
            got = _emit_path(qb, field, path, net)
            if not got.get('ok'):
                last = dict(reason=got.get('reason'), why=got.get('why'),
                            detail=got.get('detail'))
                break
            sites = [(round(x * 1e6), round(y * 1e6))
                     for (x, y) in got['via_xy']]
            broke = [(n,) + c for n in foreign
                     for c in _antipad_severs(qb, n, sites, field.via_dia)]
            if broke:
                qb.revert(got['mark'])
                closed = []
                for (n, lname, _idx, poly, area, why) in broke:
                    field.via_ok &= ~poly_mask(field, poly)
                    closed.append(dict(net=n, layer=lname,
                                       mm2=round(area, 2), why=why))
                shut += closed
                last = dict(reason='SEVERS_FOREIGN_POUR',
                            severed=sorted({c['net'] for c in closed}),
                            why='the jumper\'s %d barrel(s) would cut %d '
                                'filled pour island(s) of %s in two once the '
                                'antipad is subtracted; reverted and closed to '
                                'this transaction\'s barrels'
                                % (len(sites), len(closed),
                                   ', '.join(sorted({c['net']
                                                     for c in closed}))),
                            closed=closed)
                continue
            laid, tgt = got, cand
            break
        if laid is None:
            # A cluster that hit a severance and then ran out of corridor must
            # not report only the LAST reason: the island the retry closed is
            # the whole content of the finding.
            failed.append(dict(cluster=labels[r], pads=size[r],
                               tries=_try + 1, **(last or {}),
                               **({'closed_foreign_islands': shut}
                                  if shut else {})))
            continue
        rec = dict(cluster=labels[r], pads=size[r],
                   to_cluster=labels.get(find(tgt), [])[:4],
                   to_is_body=bool(find(tgt) == find(body)),
                   mm=round(laid['mm'], 3), vias=laid['vias'],
                   via_xy=laid['via_xy'], layers=laid['layers'])
        if shut:
            rec['closed_foreign_islands'] = shut
        if not emit:
            rec['dry'] = True
            qb.revert(laid['mark'])
        done.append(rec)
        ra, rb = find(r), find(tgt)
        parent[ra] = rb
        for L, m in merged[ra].items():
            merged[rb][L] = merged[rb][L] | m if L in merged[rb] else m
    return dict(ok=bool(done), net=net, joined=len(done),
                unjoined=len(failed), joins=done, failures=failed[:40],
                mm=round(sum(d['mm'] for d in done), 3),
                vias=sum(d['vias'] for d in done),
                clusters=len(size), body=labels.get(body, [])[:4])


# --------------------------------------------------------------------------- #
# THE DETOUR -- A TRACK PUT BACK BETWEEN ITS OWN TWO ENDS
# --------------------------------------------------------------------------- #
# D-602, D-603, D-605 and D-606 each end at the same named-and-unbuilt move, and
# four independent walls name it: the USB connector corridor, the `U9` west
# channel, and the `GND` and `BQ25185_SYS` pour residuals are every one of them
# a FOREIGN TRACK LYING ACROSS a pocket that would otherwise hold a barrel.  The
# eviction contract cannot take one.  `--evict` removes copper WHOLLY INSIDE a
# corridor window and `--evict-whole` removes a whole net board-wide; a track
# that merely CROSSES the pocket is reachable by neither, and D-602 proved on
# the USB pair that no whole-net eviction of ANY size opens that corridor.
#
# THE UNIT EVERY ONE OF THOSE WALLS ASKS FOR IS A SEGMENT, AND THE SEGMENT HAS
# A TRAP IN IT.  "Split the track at the pocket boundary and rip up the piece
# inside" leaves two stubs with FREE ENDS, and a free end is not a cosmetic
# matter on this board: D-580's first `--evict` transaction routed, regressed
# nothing, re-proposed its evicted net in full and was still REFUSED, for three
# `track_dangling` warnings.  So a split owes a re-join, and the re-join owes a
# terminal the lattice cannot express -- a stub end is an arbitrary coordinate,
# not a cell.
#
# A DETOUR IS THE SPLIT AND THE RE-JOIN AS ONE TRANSACTION, AND IT IS STRICTLY
# SAFER THAN EITHER HALF.  Remove the crossing track WHOLE and lay it again
# between ITS OWN TWO END COORDINATES, around a reserved disc.  Then:
#
#   * NOTHING IS EVER STRANDED.  Both endpoints keep their exact coordinates,
#     so every pad, barrel and T-junction that met that track still meets it,
#     `_supported` is preserved by construction and no `track_dangling` can
#     appear.  There are no stubs, so there is nothing to re-join afterwards.
#   * CONNECTIVITY IS PRESERVED BY CONSTRUCTION, not by measurement.  The two
#     points the old track joined are joined by the new one, so the cut net's
#     cluster count cannot move and clause 4 cannot be paid in the cut net's
#     own open edges.
#   * THE POCKET IS HELD.  The disc is handed to the detour as an ORDINARY
#     `Field` guard -- the same object `pour_bond_guard.py` writes and
#     `reserve_corridor.py` emits -- so the detour cannot simply retrace its old
#     path back through the site it was moved to free.
#   * IT IS REVERSIBLE.  A detour that will not route is reverted whole and the
#     original track is put back; nothing is promoted on a partial result.
#
# Nothing here is new in the legality argument.  `Field` for legality, `wave3d`
# / `descend3d` for the corridor, `QBoard.smooth` + `qrouter.simplify` for the
# geometry, `_emit_path` for the emission with the same hole-to-hole proof
# between this transaction's own barrels, and `verify_laid` to re-prove every
# object analytically.  What is new is one thing only: the TERMINAL is an exact
# coordinate rather than a pad escape or a cell inside a pour.
def point_terminals(field, x, y, layer, span=2):
    """Lattice cells a run may reach `(x, y)` from, nearest first.

    Free cells within `span` of the point, plus the point's OWN cell whether or
    not the raster calls it free -- `wave3d` opens its own ends for exactly the
    reason it opens a pad escape's cell, that the 0.75-cell guard band is a
    rasterisation artefact and not a rule, and `verify_laid` is what decides
    afterwards whether the connector this creates is legal.
    """
    if layer not in field.blk:
        return []
    ci, cj = field.cell(x, y)
    out, seen = [], set()
    for dj in range(-span, span + 1):
        for di in range(-span, span + 1):
            i, j = ci + di, cj + dj
            if not field.inside(i, j) or (i, j) in seen:
                continue
            if di or dj:
                if field.blk[layer][j, i]:
                    continue
            seen.add((i, j))
            px, py = field.point(i, j)
            out.append((math.hypot(px - x, py - y), i, j))
    out.sort()
    return [(layer, i, j) for (_, i, j) in out]


def route_points(qb, field, a, b, layer, via_cost_mm=1.5, emit=True, span=2,
                 max_mm=0.0):
    """Lay a run of this Field's net between two EXACT board coordinates.

    `a` and `b` are (x, y) in nm and both terminate on `layer`, because that is
    where the track being put back met whatever it met.  Returns
    dict(ok, mm, vias, ...); on success and `emit` the copper is on `qb` and the
    caller's `mark` reverts it.

    `emit=False` still lays the run, proves it and reverts it, so a screen and a
    gate cannot disagree about whether a detour is legal.
    """
    net = field.net
    seeds = point_terminals(field, b[0], b[1], layer, span)
    goals = point_terminals(field, a[0], a[1], layer, span)
    if not seeds or not goals:
        return dict(ok=False, reason='NO_TERMINAL',
                    why='layer %s is not in this net\'s contract' % layer)
    vc = max(1, int(round(via_cost_mm * qr.MM / field.G)))
    # A DETOUR IS A LOCAL MOVE AND THE BUDGET IS WHAT SAYS SO.  Without a bound
    # the wavefront will happily find a way round the whole board -- measured:
    # `/NFC_5V_EN`, 2.500 mm of track, came back at 21.418 mm -- and a track
    # that has to cross the board to get past a 0.8 mm disc has not been
    # detoured, it has been rerouted, which is a different transaction with a
    # different review.  The caller sets the bound; `route_maze_batch` derives
    # its default from the reserved disc itself.
    budget = (WAVE_STEPS if not max_mm
              else max(1, int(round(max_mm * qr.MM / field.G))))
    dist, hit = wave3d(field, seeds, goals, vc, budget=budget)
    if dist is None:
        return dict(ok=False, reason='NO_SEED')
    if hit is None:
        return dict(ok=False, reason='NO_PATH',
                    why='no all-layer corridor at %.3f mm between the two ends '
                        'of this track once the site is reserved%s'
                        % (field.width / 1e6,
                           '' if not max_mm else
                           ', inside the %.3f mm budget' % max_mm))
    path = descend3d(field, dist, hit, vc)
    if path is None:
        return dict(ok=False, reason='NO_DESCENT')
    if path[0][0] != layer or path[-1][0] != layer:
        return dict(ok=False, reason='WRONG_TERMINAL_LAYER',
                    why='a detour must arrive on %s at both ends' % layer)
    m = qb.mark()
    r = _emit_path(qb, field, path, net, head=a, tail=b)
    if not r.get('ok'):
        qb.revert(m)
        return r
    if max_mm and r['mm'] > max_mm:
        qb.revert(r['mark'])
        return dict(ok=False, reason='TOO_LONG', mm=r['mm'], max_mm=max_mm,
                    why='the detour measures %.3f mm against a %.3f mm bound; '
                        'this is a reroute, not a detour'
                        % (r['mm'], max_mm))
    if not emit:
        qb.revert(r['mark'])
        return dict(ok=True, dry=True, mm=r['mm'], vias=r['vias'],
                    layers=r['layers'], mm_by_layer=r['mm_by_layer'],
                    via_xy=r['via_xy'])
    return dict(ok=True, mm=r['mm'], vias=r['vias'], layers=r['layers'],
                mm_by_layer=r['mm_by_layer'],
                via_xy=r['via_xy'], mark=r['mark'])


# --------------------------------------------------------------------------- #
# PAD-ESCAPE RELIEF -- THE DOCTRINE THE BOARD HAS CARRIED AND NEVER SPENT
# --------------------------------------------------------------------------- #
# D-606.  After `stitch_pad`, `join_residual_islands`, `bridge_islands` and
# `join_islands`, the three pour-owning nets still owned 30 of the board's 68
# retained open edges, and the refusals had collapsed into ONE refusal:
#
#   * `stitch_pad` asks the PAD to launch, and D-604 swept every rung the
#     netclass and the `.kicad_dru` floors allow for 0 of 15 on `+3V3` and
#     0 of 9 on `GND`;
#   * `join_islands` asks a cell of the cluster's OWN FILLED POUR to be the
#     terminal, and D-605 re-ran it on the promoted board for 0 of 32 --
#     because 23 of those clusters own no filled pour copper at all.  A bare
#     land is not a two-dimensional conductor.
#
# The land is not the problem and neither is the run.  `screen_pad_escape_relief.py`
# measured the two levers separately and the answer was unambiguous: eight of
# those lands escape at the FULL width the board already allows them, and are
# refused for ONE reason each -- no legal BARREL fits in the pocket the escape
# reaches.  Not a corridor, not a width, not a pour: a via.
#
# `FBV2_P2_ROUTING_PLAN.md` section 17 has carried the answer as CTO standing
# law since FBV2-P2-000 and recorded it as NOT YET INSTANTIATED: one rule area
# per pad, named for that pad, `enclosedByArea()` never `intersectsArea()`,
# created only when a MEASURED need appears.  D-595 already built every piece
# of the machine for the POUR BRIDGE -- `area_licence` reads the rule, the
# transaction draws the area around the barrel it actually laid, gate clause 6
# audits every added area and `verify_promotion.py --bridge` re-proves each
# fine barrel by polygon subtraction.  This primitive spends that machine on
# the ESCAPE, which is the case the doctrine was written for in the first
# place.
#
# WHAT IS AND IS NOT RELIEVED, AND THE DISTINCTION IS THE WHOLE POINT.
# Only the BARREL is licensed.  The escape stub and the run are laid at the
# widest width in `widths` that opens the land -- the netclass width first and
# the board/DRU floor only if the netclass width fails -- so a relieved bond is
# never quietly thinner than an unrelieved one, and no track here is
# sub-class-width copper needing the doctrine's 2.0 mm clearance-run cap or its
# 6.0 mm narrow-width review trigger.  A relief that needed those would be a
# different claim and would have to be measured as one.
def _run_licence(qb, net, ref, width, mark, narrow_below, run_areas):
    """Is the sub-class-width run just laid for `ref` LICENSED, and where?

    Three independent questions, each a refusal of its own so the evidence
    names which one failed:

      NO_RUN_AREA_SPEC        the caller declared no rectangle for this pad,
                              so there is nothing for the transaction to draw
                              and nothing a reviewer approved;
      NO_DRU_WIDTH_LICENCE    the `.kicad_dru` grants this net no track width
                              inside `PAD_ESCAPE_RUN_<REF>`, or grants one no
                              narrower than the run actually needs;
      RUN_OUTSIDE_LICENCE_AREA
                              the copper does not fit the declared rectangle.
                              `enclosedByArea` is all-or-nothing per object,
                              so a run that strays by a micron is judged at
                              the class floor and the whole transaction is
                              refused by real DRC three minutes later.  It is
                              cheaper, and far clearer, to say so here.

    Returns dict(run_area, run_licence_nm, run_bbox) on success, or a dict
    carrying `reason`/`why`.
    """
    area = escape_run_area_name(ref)
    rect = (run_areas or {}).get(ref)
    if rect is None:
        return dict(reason='NO_RUN_AREA_SPEC', area=area,
                    why='no declared rule-area rectangle for %s; a width '
                        'licence is authored before the router runs, never '
                        'drawn around what it laid' % area)
    lic = width_licence(qb, net, ref)
    if lic is None or lic > width:
        return dict(reason='NO_DRU_WIDTH_LICENCE', area=area,
                    why='no .kicad_dru rule grants %s a %.3f mm track inside '
                        '%s (found %s)'
                        % (net, width / 1e6, area,
                           'nothing' if lic is None
                           else '%.3f mm' % (lic / 1e6)))
    box = laid_track_bbox(qb, mark, below=narrow_below)
    if box is None:
        return dict(reason='NO_NARROW_COPPER', area=area,
                    why='nothing narrower than %.3f mm was laid'
                        % (narrow_below / 1e6))
    rx0, ry0, rx1, ry1 = rect
    if not (rx0 <= box[0] and ry0 <= box[1]
            and box[2] <= rx1 and box[3] <= ry1):
        return dict(reason='RUN_OUTSIDE_LICENCE_AREA', area=area,
                    why='run copper %s mm is not enclosed by declared %s = %s mm'
                        % ([round(v / 1e6, 4) for v in box], area,
                           [round(v / 1e6, 4) for v in rect]))
    return dict(run_area=area, run_licence_nm=lic,
                run_bbox=[int(v) for v in box],
                run_rect=[int(v) for v in rect])


def relief_stitch(qb, net, widths, clr_pad, clr_trk, via_dia, via_drill,
                  floors, G=100000, layers=None, neck=None, guard=None,
                  max_mm=8.0, escape_limit=12, licence=True, land_ok=None,
                  pads=None, bonds_per_island=1, narrow_below=0,
                  run_areas=None):
    """Stitch each orphan island of a pour-owning net with a LICENSED barrel.

    `widths` is a ladder, widest first; an island served at one width is
    retired, so a later, narrower rung is only asked about what is still open
    and the transaction always takes the most copper the board will give.

    A barrel that already meets every ordinary floor needs no rule and gets
    none -- it is the same barrel `stitch_pad` lays today.  A barrel BELOW a
    floor is laid only where the `.kicad_dru` grants THIS NET THAT GEOMETRY
    inside the rule area named for THIS PAD; anything else is `NO_DRU_LICENCE`
    and is reported, never laid.  Returns dict(ok, stitched, stitches,
    failures) where each stitch names the area the transaction must draw.
    """
    if not has_plane(qb, net):
        return dict(ok=False, net=net, reason='NO_PLANE', stitches=[],
                    failures=[])
    islands = net_islands(qb, net)
    if len(islands) < 2:
        return dict(ok=True, net=net, stitched=0, stitches=[], failures=[],
                    reason='NOTHING_TO_STITCH')
    body = max(islands, key=len)
    pending = [i for i in islands if i is not body]
    plain = _meets_floors(via_dia, via_drill, floors)
    done, last, unasked = [], {}, {}
    for rung, w in enumerate(widths):
        if not pending:
            break
        field = Field(qb, net, w, clr_pad, clr_trk, via_dia, via_drill,
                      G=G, layers=layers, neck=neck, guard=guard)
        still = []
        for island in pending:
            hits = []
            for pad in island:
                if len(hits) >= max(1, bonds_per_island):
                    break
                ref = pad['ref']
                # D-609.  `pads` NAMES the lands this transaction is spending
                # its licence -- or its narrow rung -- on.  A relief is the
                # most expensive thing a run can lay, and offering the whole
                # ladder to every orphan on the board is how one land's
                # measured exception becomes twenty unmeasured ones.  None
                # means "every land", which is what every caller before this
                # one asked for and gets byte-identically.
                if pads is not None and ref not in pads:
                    # A LAND THIS TRANSACTION DID NOT ASK ABOUT HAS NOT BEEN
                    # MEASURED, AND MUST NOT BE REPORTED AS THOUGH IT HAD BEEN
                    # -- D-610 addendum.  An island whose every pad is filtered
                    # out here sets no `last` entry, so it used to fall through
                    # to the `NO_ESCAPE` default at the bottom of this function
                    # -- the same word `stitch_pad` returns when it has
                    # actually looked and found nothing.  D-610's own gate
                    # evidence carries eight `+3V3` lands that way (`U4.2`,
                    # `U4.3`, `U4.5`, `U4.8`, `U4.12`, `R129.1`, `R39.1`,
                    # `U5.2`): recorded as refusals, never tried, because
                    # `--relief-pad` named only `U12.4`/`U12.5`.  A reader
                    # pricing the next iteration off that file would have
                    # written those five `U4` lands off unmeasured.
                    #
                    # `NOT_OFFERED` says which, and names the lands.  When
                    # `pads` is None -- every caller before D-609 -- this
                    # branch cannot be reached and the output is byte-identical.
                    unasked.setdefault(id(island), set()).add(ref)
                    continue
                lic = None if plain else (escape_licence(qb, net, ref)
                                          if licence else None)
                if licence and not _barrel_licensed(via_dia, via_drill,
                                                    floors, lic):
                    last[id(island)] = dict(
                        reason='NO_DRU_LICENCE', pad=ref,
                        why='no .kicad_dru rule grants %s a %.2f/%.2f mm '
                            'barrel inside %s'
                            % (net, via_dia / 1e6, via_drill / 1e6,
                               escape_area_name(ref)))
                    continue
                m = qb.mark()
                r = stitch_pad(qb, field, pad, max_mm=max_mm,
                               escape_limit=escape_limit, land_ok=land_ok)
                # A BARREL THAT IS LEGAL IS NOT YET A BARREL THAT CONNECTS,
                # AND THE PROPOSER CANNOT TELL.  `stitch_pad` proves the
                # geometry of its via; it does not prove that the pour UNDER
                # that via is the plane BODY rather than another orphan piece
                # of the same net.  D-604 measured that on `BQ25185_SYS` --
                # `SW9.2` stitched at every rung and closed nothing, three
                # full gate runs, 69 -> 69 each -- and D-606's first run
                # repeated it on `+3V3`: `R129.1` laid a via and 0.547 mm of
                # track for zero edges.
                #
                # THE OBVIOUS CHECK HERE IS WRONG, AND IT WAS MEASURED WRONG.
                # Retaking `net_islands` after each stitch reads connectivity
                # against the pour as it was filled BEFORE the barrel existed,
                # and KiCad's refill floods a zone up to a new via of its own
                # net.  Run 2 of D-606 carried exactly that check and it
                # rejected `C7.1`, which run 1 had proved CLOSES post-refill --
                # a false negative that costs an edge, on the same reading
                # D-605 recorded for foreign pour damage.  The question is
                # answerable only after the refill, so it is answered by the
                # gate, on the refilled candidate's own ledger, in the clause
                # named `relief_lands_closed`.  A proposer that guessed here
                # would be a second opinion for the gate to disagree with.
                if r.get('ok'):
                    # A NARROW RUN IS ITS OWN LICENCE QUESTION, AND IT IS
                    # ANSWERED HERE OR THE COPPER DOES NOT EXIST.  D-609 laid
                    # a 0.200 mm run under a P3V3 0.400 mm floor with no width
                    # licence of any kind and collected six real `track_width`
                    # errors; the two segments that passed did so by
                    # `intersectsCourtyard`, the shape section 17 clause 2
                    # forbids leaning on.  `narrow_below` is the class floor;
                    # under it a run is laid ONLY where this board already
                    # grants THIS NET THAT WIDTH inside the rule area named
                    # for THIS PAD, AND the whole run fits inside the
                    # rectangle that area is declared to be.  The declaration
                    # comes from the caller's tracked spec, not from the run,
                    # so the licence is a fixed grant authored and reviewed
                    # BEFORE the router moved -- never a box drawn round
                    # whatever the router happened to lay.
                    run = None
                    if narrow_below and w < narrow_below:
                        run = _run_licence(qb, net, ref, w, m, narrow_below,
                                           run_areas)
                        if run.get('reason'):
                            qb.revert(m)
                            last[id(island)] = dict(pad=ref, **run)
                            continue
                    hit = dict(pad=ref, island=[p['ref'] for p in island],
                               width=w, rung=rung, layer=r['layer'],
                               mm=r['mm'], via_xy=list(r['via_xy']),
                               xy=list(r['via_xy_nm']),
                               via_dia=via_dia, via_drill=via_drill,
                               needs_licence=(not plain), licence=lic,
                               area=(None if plain
                                     else escape_area_name(ref)))
                    if run is not None:
                        hit.update(run)
                    hits.append(hit)
                    continue
                qb.revert(m)
                last[id(island)] = dict(reason=r.get('reason'), pad=ref,
                                        why=str(r.get('why'))[:160])
            if hits:
                done.extend(hits)
            else:
                still.append(island)
        pending = still
    failures = [dict(island=[p['ref'] for p in i],
                     **(last.get(id(i))
                        or (dict(reason='NOT_OFFERED',
                                 not_offered=sorted(unasked[id(i)]))
                            if id(i) in unasked
                            else dict(reason='NO_ESCAPE'))))
                for i in pending]
    return dict(ok=bool(done), net=net, stitched=len(done),
                unstitched=len(failures), stitches=done,
                failures=failures[:40],
                mm=round(sum(d['mm'] for d in done), 3), vias=len(done),
                widths=list(widths), via_dia=via_dia, via_drill=via_drill)


# --------------------------------------------------------------------------- #
# THE PLANE STITCH, BUILT ON THE HOP INSTEAD OF ON THE LATTICE          D-637
# --------------------------------------------------------------------------- #
# D-634 closed with "PUT THE BARREL CORRECTIONS INTO THE INSTRUMENTS THAT
# PROMOTE", D-635 and D-636 each carried it forward unchanged, and this is the
# instrument it names first.  `stitch_pad` is the primitive every pour-owning
# net's orphan islands are closed by, and it searches its barrel the older way:
#
#   * its launch is `pad_escapes`, whose off-centre source is offered ONLY when
#     the ordinary set is EMPTY and only under `AQROOT_OFFCENTRE_LAUNCH`; and
#   * its barrel is found by a WAVEFRONT ON THE FIELD LATTICE, `~field.blk[L]`,
#     inside a window of `max_mm` cells around the escape.
#
# The second is the one that matters, and the refusal it produces is MISNAMED.
# `NO_VIA_SITE` reads as a statement about barrels; it is a statement about a
# POCKET.  A land whose escape sits in a lattice pocket cannot walk to any
# via-legal cell inside the window, so the stitch reports that no barrel exists
# when what is true is that the coarse lattice cannot leave the pad -- which is
# exactly D-633's LATTICE_EXACT finding in a second place, and exactly what
# D-634 built `_hop_sites` and `QBoard.via_sites` to answer instead.
#
# So this is `stitch_pad`'s question asked with D-634's answer:
#
#   * the LAUNCH is `_hop_launch` -- the centre-anchored `QBoard.escape` FIRST
#     and in its own order, then `offcentre_escapes`, both exact and neither a
#     lattice;
#   * the BARREL is `_hop_sites` over `QBoard.via_sites`, which floods the near
#     layer at TRACK width from the launch on the FINE grid and is therefore a
#     reachability answer, then clears every layer of the stack and every
#     drilled hole through `_via_free_everywhere`;
#   * the WALK from the launch to that site is `qrouter.connect_role` between
#     two ANCHORS, the same instrument the hop uses.
#
# AND THE BARREL IS REQUIRED TO LAND IN THE NET'S OWN BODY POUR.  That is
# `body_landing`'s contract -- CENTRE-IN-COPPER, a certificate and not a veto,
# with `land_ok=None` still available -- but computed EXACTLY, on KiCad's own
# filled polygons through `filled_islands`, instead of on a rasterised mask.
# D-608's calibration is why the erode is not offered here either.
#
# NOTHING ABOVE IS EDITED.  `stitch_pad`, `stitch_net`, `relief_stitch` and
# every instrument that calls them are untouched, so every accepted run on this
# board reproduces byte for byte and this primitive is reachable only from code
# written for it.
# --------------------------------------------------------------------------- #
def cluster_body_polys(qb, net, body_island):
    """KiCad's own filled polygons that belong to `body_island`'s cluster.

    `body_island` is one of `net_islands`' pad groups -- the BODY, the group a
    stitch is trying to reach.  `pour_clusters` unions this net's pads AND
    vias by KiCad connectivity and `island_owner` attributes each filled
    outline to one of those clusters by containment, so what comes back is the
    copper a barrel may land in and be bonded to by the refill, layer by layer.

    Returns (polys, meta) with `polys` a list of (layer_name, SHAPE_POLY_SET,
    area_mm2).  An empty list means the body owns no filled copper at all,
    which is a real answer and not an error: a caller must then stitch without
    the certificate or not at all.
    """
    islands = filled_islands(qb, net)
    if not islands:
        return [], dict(filled_islands=0, body_roots=0)
    roots, items = pour_clusters(qb, net)
    owner = island_owner(islands, roots, items)
    want = set()
    for p in body_island:
        for key, meta in items.items():
            if meta['kind'] != 'pad' or key[1] != p['ref']:
                continue
            if abs(meta['x'] - p['x']) < 1000 and abs(meta['y'] - p['y']) < 1000:
                want.add(roots[key])
    out = [(lname, poly, a) for (lname, idx, poly, a) in islands
           if owner.get(idx) in want]
    per = {}
    for (lname, _poly, a) in out:
        per[lname] = round(per.get(lname, 0.0) + a, 3)
    return out, dict(filled_islands=len(islands), body_roots=len(want),
                     body_islands=len(out), area_mm2_by_layer=per)


def in_body(polys, x, y, layer=None):
    """Is (x, y) inside the body's own filled copper?  Returns the layer, or None.

    `layer=None` asks ANY layer, which is the right question for a THROUGH
    barrel: it is copper on every layer of the stack, so one containment
    suffices -- and that is how every `GND` stitch on this board reaches `In1`
    or `In4`, layers the net may not route a track on.

    `layer=NAME` asks that layer ALONE, and it is the right question when
    there is NO barrel.  A stub that merely ENDS on the plane the body pours
    on carries copper on its own layer and nowhere else, so a containment on
    some other layer bonds nothing.  Getting this wrong is not a near miss:
    the first run of `screen_plane_stitch.py` reported `C37.2` closed with a
    `B.Cu` stub whose landing was inside the body's `In1.Cu` polygon and
    inside no `B.Cu` copper at all.
    """
    import pcbnew
    pt = pcbnew.VECTOR2I(int(x), int(y))
    for (lname, poly, _a) in polys:
        if layer is not None and lname != layer:
            continue
        if poly.Contains(pt):
            return lname
    return None


def offcentre_stitch(qb, ctx, pad, far, width, toward, polys=None,
                     stub_widths=None, G=50000, fine=25000, memo=None,
                     limit=6, via_ladder=None, via_dia=600000,
                     via_drill=300000, span=8000000, sites_limit=96,
                     site_options=24, reach_mm=OFFCENTRE_REACH_MM,
                     anchor_fracs=OFFCENTRE_ANCHOR_FRACS,
                     dir_step_deg=OFFCENTRE_DIR_STEP_DEG):
    """Drop ONE orphan land onto its net's own plane: launch, walk, barrel.

    `far` is the plane layer the barrel is aimed at -- a name or an ordered
    list, first that closes wins.  `toward` is any point the launch should
    prefer (the nearest body pad); it reorders candidates and decides nothing.
    `polys` is `cluster_body_polys`' answer; when given, a barrel site is
    accepted ONLY where `in_body` names a layer, and when None the stitch is
    unconstrained exactly as `stitch_pad` without `land_ok` is.

    On success the stub, the walk and the barrel are on `qb` and the CALLER's
    own mark reverts them; on failure this reverts everything it laid.
    """
    ladder = tuple(via_ladder or ((int(via_dia), int(via_drill)),))
    if isinstance(far, (list, tuple)):
        best, tried = None, []
        for L in far:
            r = offcentre_stitch(qb, ctx, pad, L, width, toward, polys=polys,
                                 stub_widths=stub_widths, G=G, fine=fine,
                                 memo=memo, limit=limit, via_ladder=ladder,
                                 span=span, sites_limit=sites_limit,
                                 site_options=site_options, reach_mm=reach_mm,
                                 anchor_fracs=anchor_fracs,
                                 dir_step_deg=dir_step_deg)
            tried.append(dict(far=L, reason=r.get('reason'),
                              why=str(r.get('why'))[:200]))
            if r.get('ok'):
                return dict(r, far_tried=tried)
            if best is None or (best.get('reason') in ('NO_NEAR_WALK', None)
                                and r.get('reason') not in ('NO_NEAR_WALK',
                                                            None)):
                best = r
        return dict(best or dict(ok=False, reason='NO_LAYER',
                                 why='no far layer offered'), far_tried=tried)

    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    nl, opts, bad = _hop_options(qb, ctx, pad, toward, far, None, width,
                                 stub_widths, ladder, G, ox, oy, memo, limit,
                                 span, sites_limit, site_options, reach_mm,
                                 anchor_fracs, dir_step_deg)
    if bad is not None:
        return dict(ok=False, pad=pad['ref'], far=far, **bad)

    offered = len(opts)
    # CLAUSE 7 INSIDE THE PRIMITIVE.  An option with NO barrel is a bare stub
    # on `nl`, and it CONNECTS NOTHING unless its landing is inside the body's
    # own filled copper ON THAT LAYER.  Unconstrained (`polys is None`) there
    # is nothing to land in, so such an option is not a stitch at all and is
    # dropped here rather than reported as a closure: the first run of
    # `screen_plane_stitch.py` counted two of them, `C37.2` and `U9.16`, and
    # both were 1.0 mm and 0.2 mm of copper joining a pad to open board.
    if polys is None:
        opts = [o for o in opts if o['site'] is not None]
        if not opts:
            return dict(ok=False, pad=pad['ref'], far=far, offered=offered,
                        reason='NO_BARREL_NEEDED_NO_BARREL_FOUND',
                        why='%s: its land is already on %s, so an '
                            'unconstrained stitch has nothing to land in'
                            % (pad['ref'], far))
    if polys is not None:
        # `at` and NOT `site`, because a land ALREADY on the plane the body
        # pours on takes no barrel at all -- `_hop_options` reports
        # `site=None` and `at` is then the stub's own landing.  A stub that
        # lands inside the body's filled copper is bonded by the refill
        # exactly as a barrel in it is, so that case is a real closure and is
        # reported with `via_dia: null` rather than skipped.
        kept = []
        for o in opts:
            hit = in_body(polys, o['at'][0], o['at'][1],
                          layer=(None if o['site'] is not None else nl))
            if hit is not None:
                kept.append(dict(o, body_layer=hit))
        if not kept:
            return dict(ok=False, pad=pad['ref'], far=far,
                        reason='NO_BODY_VIA_SITE', offered=offered,
                        why='%s: none of %d reachable barrels on %s lands '
                            'INSIDE this net\'s own body pour'
                            % (pad['ref'], offered, nl))
        opts = kept

    fail = None
    for opt in opts:
        m = qb.mark()
        good, wmm, why = _hop_lay(qb, ctx, pad, nl, far, opt, width, G, fine)
        if not good:
            qb.revert(m)
            fail = dict(ok=False, pad=pad['ref'], far=far,
                        reason='NO_NEAR_WALK', offered=offered, why=why)
            continue
        why = verify_laid(qb, ctx, m)
        if why is not None:
            qb.revert(m)
            fail = dict(ok=False, pad=pad['ref'], far=far, offered=offered,
                        reason='UNPROVED_GEOMETRY',
                        why='%s at %s vs %s' % (why.get('kind'), why.get('at'),
                                                why.get('against',
                                                        why.get('why'))))
            continue
        c = opt['cand']
        vx, vy = opt['at']
        return dict(ok=True, pad=pad['ref'], layer=nl, far=far,
                    barrel=bool(opt['site'] is not None),
                    offered=offered,
                    body_layer=opt.get('body_layer'),
                    centre=bool(c.get('centre')),
                    offcentre_mm=c['offcentre_mm'], base_dir=c['base_dir'],
                    stub_mm=round(c['ln'] / 1e6, 4), walk_mm=round(wmm, 4),
                    mm=round(c['ln'] / 1e6 + wmm, 4),
                    width=int(width), stub_width=int(opt['sw']),
                    via_dia=opt['dia'], via_drill=opt['drill'],
                    via_xy=(round(vx / 1e6, 4), round(vy / 1e6, 4)),
                    via_xy_nm=(int(vx), int(vy)),
                    a_xy=(round(c['ax'] / 1e6, 4), round(c['ay'] / 1e6, 4)),
                    b_xy=(round(c['x'] / 1e6, 4), round(c['y'] / 1e6, 4)))
    return fail or dict(ok=False, pad=pad['ref'], far=far, offered=offered,
                        reason='NO_VIA_SITE',
                        why='%s: no barrel reachable on %s' % (pad['ref'], nl))


# ---------------------------------------------------------------------------
# D-639: A TRACK IS A SLOT IN A FOREIGN POUR EXACTLY AS A BARREL IS.
#
# `_antipad_severs` above answers "which of this foreign net's filled islands
# would a BARREL cut in two", and it is calibrated by two D-605 gate runs.  It
# is also the ONLY pour-damage question any screen on this board asks before
# spending a gate run, and D-638 paid for the gap: the joint rip-up-and-relay
# measured `antipad_severs: []` for `+3V3 R39.1`, the writer laid the very
# transaction it emitted, and clause `PP2` refused the run because the 17.2 mm
# RELAY TRACK -- not the barrel -- split `GND`'s `B.Cu` pour 58 -> 59 and
# sheared off a 21.765 mm2 fragment holding `C27.2`/`C28.2`.
#
# The physics is the same and so is the calibration.  KiCad's fill holds a pour
# `clearance` away from foreign copper and then deletes whatever neck is left
# thinner than the zone's `min_thickness`, so a track of width `w` deletes pour
# copper out to `w/2 + clearance + min_thickness` along its whole length -- the
# same third row of the D-605 table, with `dia/2` replaced by `w/2`.  The only
# difference is REACH: a through barrel is copper on every layer, a track is
# copper on exactly one.
#
# This is a NEW function and `_antipad_severs` is untouched, so every standing
# contract that calls it is byte-identical.
def _capsule(ax, ay, bx, by, r, seg=16):
    """A `SHAPE_LINE_CHAIN` capsule of radius `r` around segment a->b."""
    import pcbnew
    dx, dy = float(bx - ax), float(by - ay)
    L = math.hypot(dx, dy)
    if L <= 1.0:
        return pcbnew.SHAPE_LINE_CHAIN(
            [pcbnew.VECTOR2I(int(ax + r * math.cos(t * 2 * math.pi / (2 * seg))),
                             int(ay + r * math.sin(t * 2 * math.pi / (2 * seg))))
             for t in range(2 * seg)], True)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    pts = []
    # cap at b, swinging from +n to -n through +u
    base = math.atan2(ny, nx)
    for t in range(seg + 1):
        a = base - t * math.pi / seg
        pts.append(pcbnew.VECTOR2I(int(bx + r * math.cos(a)),
                                   int(by + r * math.sin(a))))
    # cap at a, swinging from -n to +n through -u
    base = math.atan2(-ny, -nx)
    for t in range(seg + 1):
        a = base - t * math.pi / seg
        pts.append(pcbnew.VECTOR2I(int(ax + r * math.cos(a)),
                                   int(ay + r * math.sin(a))))
    return pcbnew.SHAPE_LINE_CHAIN(pts, True)


def copper_severs(qb, net, shapes):
    """Which of `net`'s filled islands would this NEW copper cut in two?

    `net` is the FOREIGN pour-owning net being examined -- iterate
    `_foreign_pours(qb, own_net)` over it exactly as `_antipad_severs` is
    iterated.  `shapes` is a list of dicts, in nm:

        {'kind': 'via', 'xy': (x, y), 'dia': nm}                  whole stack
        {'kind': 'seg', 'a': (x, y), 'b': (x, y), 'width': nm,
         'lkey': 'B'}                                             one layer

    A shape whose `lkey` is absent or None reaches every layer, which is what a
    through barrel does.  Returns [(layer, index, poly, area_mm2, why)] in the
    same shape `_antipad_severs` returns, so a caller can concatenate the two.

    THE LAND CONVENTION IS `_antipad_severs`'s AND IS DELIBERATE.  The lands an
    island is re-located by are every pad and via of the net, tested by plain
    containment without a per-layer filter.  That can over-count -- an `F`-only
    pad sitting above a `B` island counts as one of its lands -- and the error
    is in the CONSERVATIVE direction for a pre-filter whose whole job is to
    refuse a transaction before a gate run is spent on it.  Keeping the
    convention identical also keeps this function and the calibrated one
    answering the same question about the same board.
    """
    import pcbnew
    if not shapes:
        return []
    clr, mt = _pour_geometry(qb, net)
    lands = [(m['x'], m['y']) for m in
             (pour_clusters(qb, net)[1]).values()]
    cut = []
    for lname, idx, poly, area in filled_islands(qb, net):
        holes, hit = pcbnew.SHAPE_POLY_SET(), 0
        for s in shapes:
            lk = s.get('lkey')
            if lk and lk != lname:
                continue
            if s['kind'] == 'via':
                x, y = int(s['xy'][0]), int(s['xy'][1])
                r = s['dia'] / 2.0 + clr + mt
                if not (poly.Contains(pcbnew.VECTOR2I(x, y))
                        or poly.Collide(pcbnew.VECTOR2I(x, y), int(r))):
                    continue
                holes.AddOutline(_capsule(x, y, x, y, r))
                hit += 1
            else:
                ax, ay = int(s['a'][0]), int(s['a'][1])
                bx, by = int(s['b'][0]), int(s['b'][1])
                r = s['width'] / 2.0 + clr + mt
                if not (poly.Contains(pcbnew.VECTOR2I(ax, ay))
                        or poly.Contains(pcbnew.VECTOR2I(bx, by))
                        or poly.Collide(pcbnew.SEG(pcbnew.VECTOR2I(ax, ay),
                                                   pcbnew.VECTOR2I(bx, by)),
                                        int(r))):
                    continue
                holes.AddOutline(_capsule(ax, ay, bx, by, r))
                hit += 1
        if not hit:
            continue
        mine = [(x, y) for (x, y) in lands
                if poly.Contains(pcbnew.VECTOR2I(int(x), int(y)))]
        if len(mine) < 2:
            continue
        rest = pcbnew.SHAPE_POLY_SET(poly)
        rest.BooleanSubtract(holes)
        where = set()
        for (x, y) in mine:
            for k in range(rest.OutlineCount()):
                piece = pcbnew.SHAPE_POLY_SET()
                piece.AddOutline(rest.Outline(k))
                if piece.Contains(pcbnew.VECTOR2I(int(x), int(y))):
                    where.add(k)
                    break
        if len(where) > 1:
            cut.append((lname, idx, poly, area,
                        '%d land(s) of %s on this %s island end in %d separate '
                        'pieces once %d piece(s) of new copper are subtracted '
                        'at clearance %.2f + min_thickness %.2f mm'
                        % (len(mine), net, lname, len(where), hit,
                           clr / 1e6, mt / 1e6)))
    return cut
