#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: would a SEGMENT eviction open a barrel site?

D-602, D-603, D-605 and D-606 all end at the same named-and-unbuilt move.  Four
independent walls -- the USB connector corridor, the `U9` west channel, and the
`GND` and `BQ25185_SYS` pour residuals -- are each a foreign track lying across
copper that would otherwise be one piece, and the eviction contract this board
owns cannot take one: `--evict` removes copper WHOLLY INSIDE a corridor window
and `--evict-whole` removes a whole net board-wide.  A track that merely CROSSES
the pocket is reachable by neither, and D-602 proved on the USB pair that no
whole-net eviction of any size opens that corridor at all.

The missing unit is a SEGMENT: split a crossing track at the pocket boundary,
rip up only the portion inside, and leave the two stubs.  Before any of that is
built into the writer, this screen answers the only question that decides
whether it is worth building -- IS THE POCKET FULL OF CUTTABLE COPPER, OR IS IT
FULL OF PADS?

The family it asks about is the largest one left.  After D-606 the three
pour-owning nets still hold 25 open lands and SIXTEEN of them fail
`maze3d.stitch_pad` with `NO_VIA_SITE` -- "no legal barrel within 8.0 mm of any
escape" -- at every rung the netclass, the `.kicad_dru` floors and D-606's own
relief licence allow.  `NO_VIA_SITE` is a statement about a POCKET, and nothing
in the repository says what is standing in it.

Three questions, in escalating cost, per open land:

  1. UPPER BOUND.  Cut EVERY unprotected foreign routed track inside the stitch
     window at once and re-ask the real `stitch_pad`.  Still `NO_VIA_SITE` =>
     no segment eviction of any size opens this land, and the pocket is pads,
     placement or a foreign BARREL.  Reported `SEGMENT_WALL`, with the foreign
     vias named, because a via is a barrel through the stack and no split can
     cut one.
  2. SINGLE.  One track at a time.  A track that opens the land alone is the
     cheapest possible transaction and is reported with the run the stitch then
     takes.
  3. MINIMAL SET.  Reverse-greedy: start from "all of them cut", which question
     1 already proved opens it, then put each one BACK and keep it back whenever
     the land stays open.  What remains is minimal with respect to single-track
     addition and is re-proved open at the end.

Then the cut is SHRUNK.  Question 1 cuts over the whole 8 mm window, which is
an upper bound and not a transaction anybody should execute.  Once a barrel site
is known the required cut is a DISC around that site -- the barrel's own copper
radius plus the clearance the cut net owes it plus that track's half width -- so
the screen walks a radius ladder down from the window and reports the SMALLEST
disc that still opens the land.  That is the executable geometry.

And every surviving cut is PRICED on connectivity.  A cut that leaves the cut
net's own pads in the same number of KiCad clusters is FREE -- the two stubs are
still joined some other way, or the removed piece carried nothing -- and needs
no re-join at all.  A cut that raises the cluster count is `REJOIN_REQUIRED` and
owes a jumper around the pocket before clause 4 would ever promote it.  That
verdict is taken from KiCad's own `BuildConnectivity` on a SCRATCH COPY of the
board, never from a lattice model, because connectivity is what clause 4 counts.

D-608 ADDS `--body-landing`, AND WITHOUT IT THIS SCREEN LIES BY OMISSION.
`stitch_pad` proves a barrel is LEGAL; it never asks whether the copper under
that barrel is the plane BODY.  D-607 took this screen's `R129.1` answer to a
full gate run: the cut was made, the detour was laid, the barrel was planted at
0.65/0.40 mm exactly where this file said it would fit -- and the refilled
ledger still showed `R129.1` as a component of its own, 59 -> 59, clause 4
REFUSED.  With `--body-landing` the barrel must land inside a filled island the
BODY cluster owns, which is a certificate that KiCad's refill will bond it.
Nine of this board's remaining pour lands were re-asked that way and the answer
moved for six of them: the whole `BQ25185_SYS` residual -- eight cuttable lands
-- becomes `NO_BODY_VIA_SITE`, because that net's body owns 3.25 mm2 of copper
in total and no barrel can reach it.  Those are gate runs nobody now has to
spend.

NOTHING IS WRITTEN.  The authoritative board is opened once, read, and its
sha256 is re-checked at exit.  Every cut lives in the in-memory obstacle model
and is restored; the connectivity price is measured on a copy in a temporary
directory.  A land reported open here is a licence to build the writer and spend
a gate run, not a promise.
"""

import argparse
import copy
import hashlib
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

from protected_copper import PROTECTED

# D-606's relief contract, verbatim, so the rung named `relief` here is the
# same one `screen_pad_escape_relief.py` measured and the `.kicad_dru` already
# licenses by name.
RELIEF_WIDTH = 200000
RELIEF_CLR = 200000
RELIEF_VIA_DIA = 350000
RELIEF_VIA_DRILL = 200000

# `qrouter`'s layer keys against the board's own copper layer names, because a
# detour spec names a layer the way KiCad does and a screen that guessed
# "I2.Cu" would emit a spec the applier is right to refuse.
LAYER_NAME = {"F": "F.Cu", "B": "B.Cu", "I1": "In1.Cu", "I2": "In2.Cu",
              "I3": "In3.Cu", "I4": "In4.Cu"}


def cut_capsule(SEG, s, cx, cy, R):
    """The portions of capsule `s` that survive a disc cut at (cx, cy, R).

    The disc is where copper must NOT be, so the cut is taken against the
    capsule's CENTRELINE at `R + s.hw`: what is left is copper of the same
    width that cannot reach inside the disc.  Returns a list of 0, 1 or 2 SEGs;
    a single-element list containing `s` itself means the disc misses it.
    """
    reff = R + s.hw
    dx, dy = float(s.x1 - s.x0), float(s.y1 - s.y0)
    l2 = dx * dx + dy * dy
    if l2 == 0.0:
        return [] if math.hypot(s.x0 - cx, s.y0 - cy) < reff else [s]
    fx, fy = float(s.x0 - cx), float(s.y0 - cy)
    b = 2.0 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - reff * reff
    disc = b * b - 4.0 * l2 * c
    if disc <= 0.0:
        return [s]
    sq = math.sqrt(disc)
    t0, t1 = (-b - sq) / (2.0 * l2), (-b + sq) / (2.0 * l2)
    if t1 <= 0.0 or t0 >= 1.0:
        return [s]
    out = []
    if t0 > 0.0:
        out.append(SEG(s.x0, s.y0, s.x0 + t0 * dx, s.y0 + t0 * dy,
                       s.hw, s.net, s.tag))
    if t1 < 1.0:
        out.append(SEG(s.x0 + t1 * dx, s.y0 + t1 * dy, s.x1, s.y1,
                       s.hw, s.net, s.tag))
    return out


class Cuts(object):
    """Context manager: exactly these tracks are cut by exactly these discs.

    `screen_corridor_blockers.WithoutObjects` holds whole objects out, which is
    the unit `--evict` licenses.  This holds out a PIECE of one, which is the
    unit that does not exist yet -- and building it here first is deliberate:
    if no land opens, the writer is never built.

    Rebuilding `Field.via_ok` also re-applies the pour-bond guard, because
    `Field.__init__` ANDs the guard out of the via lattice once and a bare
    `_via_grid()` would silently hand this net back the barrel sites a bond
    tube owns.
    """

    def __init__(self, qb, field, cuts):
        self.qb, self.field = qb, field
        self.cuts = list(cuts)          # (layer, seg, cx, cy, R)

    def __enter__(self):
        import qrouter as qr
        qb = self.qb
        self.saved = {}
        by_layer = {}
        for (L, s, cx, cy, R) in self.cuts:
            by_layer.setdefault(L, []).append((s, cx, cy, R))
        for L, items in by_layer.items():
            self.saved[L] = qb.shapes[L]
            drop = {id(s) for (s, _, _, _) in items}
            kept = [s for s in qb.shapes[L] if id(s) not in drop]
            for (s, cx, cy, R) in items:
                for piece in cut_capsule(qr.SEG, s, cx, cy, R):
                    if piece is s:
                        kept.append(s)
                    elif math.hypot(piece.x1 - piece.x0,
                                    piece.y1 - piece.y0) > 0:
                        kept.append(piece)
            qb.shapes[L] = kept
        self._refresh()
        return self

    def __exit__(self, *exc):
        for L, lst in self.saved.items():
            self.qb.shapes[L] = lst
        self._refresh()
        return False

    def _refresh(self):
        self.qb._obs_cache = None
        self.field.rebuild_blk()
        self.field.via_ok = self.field._via_grid()
        for m in self.field._guard.values():
            self.field.via_ok &= ~m


class Held(Cuts):
    """Hold WHOLE tracks out of the obstacle model, the way the applier does.

    `Cuts` removes the PIECE of a track a disc covers, which is the question
    "would a barrel fit".  The relay asks a different one: `detour_apply`
    removes each named track ENTIRELY from the board before anything is put
    back, so the board a relay is routed on has no copper of that track at all.
    Same refresh, same restore; only the geometry of the removal differs.
    """

    def __init__(self, qb, field, items):
        Cuts.__init__(self, qb, field, [])
        self.items = list(items)            # (layer, seg)

    def __enter__(self):
        qb = self.qb
        self.saved = {}
        by_layer = {}
        for (L, s) in self.items:
            by_layer.setdefault(L, []).append(s)
        for L, segs in by_layer.items():
            self.saved[L] = qb.shapes[L]
            drop = {id(x) for x in segs}
            qb.shapes[L] = [x for x in qb.shapes[L] if id(x) not in drop]
        self._refresh()
        return self

    def _refresh(self):
        # The relay builds a `Field` of its OWN for every net it puts back, so
        # this context owes only the obstacle cache.  `field` is therefore
        # allowed to be None, which `Cuts` never permits.
        self.qb._obs_cache = None
        if self.field is not None:
            Cuts._refresh(self)


def chain_ends_mm(cuts):
    """The two FREE ends of a same-net chain, in mm, or None if it is not one.

    Mirrors `route_maze_batch.chain_ends`: an endpoint shared by two members is
    an interior junction, and exactly two endpoints may be unshared.  A single
    track is its own chain and its two ends are its own.
    """
    seen = {}
    for c in cuts:
        for pt in (tuple(c["a_mm"]), tuple(c["b_mm"])):
            seen[pt] = seen.get(pt, 0) + 1
    free = sorted(pt for pt, n in seen.items() if n == 1)
    return free if len(free) == 2 else None


def relay_price(qb, grid, reserved, cuts, site, radius, exempt, spec,
                via_cost_mm=1.5, own_layer=False):
    """Would every track this land CUTS go back, between its own two ends?

    D-608, and the run that paid for it.  This screen's job used to end at "a
    barrel fits here once that track moves"; the transaction it authorises then
    has to MOVE the track, and D-608's first gate run on `GND` `C37.2` proved
    that half can fail on its own -- `/09_COMMUNITY_HEADER/TCA4307_READY` lies
    on `In3.Cu`, a plane RESERVED for `+3V3`, so it can be cut and can never be
    put back, and `/I2C_SCL_INT` found no corridor inside its own bound.  Both
    tracks came out, neither went back, four `track_dangling` warnings, retained
    open edges 59 -> 60, clause 4 REFUSED.  Nothing about that needed a gate run
    to discover.

    Every judgement here is the writer's own: `permitted_layers` for the layer,
    `maze3d.route_points` for the corridor, `detour_guard`'s disc on EVERY layer
    for the reservation, and `was + 2*pi*R` for the bound.  `emit=True` in spec
    order and one revert at the end, because the applier lays each detour on a
    board that already carries the previous one.
    """
    import qrouter as qr
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers, guard_for,
                                  detour_layers)

    by_net = {}
    for (L, seg, c) in cuts:
        by_net.setdefault(c["net"], []).append((L, seg, c))
    # The reserved disc, on every copper layer, exactly as `detour_guard`
    # writes it -- a barrel is copper through the stack and a reservation that
    # held only the outer two would let the relay tunnel under the site.
    disc = dict(guards=[dict(ok=True, net=(exempt[0] if exempt else ""),
                             exempt=list(exempt[1:]), lkey=lk,
                             keepout_radius=int(radius),
                             points=[[int(site[0]), int(site[1])]],
                             tube="DETOUR_RESERVE_1")
                        for lk in ("F", "I1", "I2", "I3", "I4", "B")])
    out, ok_all = [], True
    held = [(L, seg) for (L, seg, _c) in cuts]
    with Held(qb, None, held) as _h:
        m = qb.mark()
        for net in sorted(by_net):
            grp = by_net[net]
            recs = [c for (_L, _s, c) in grp]
            lkeys = {c["layer"] for c in recs}
            widths = {c["width_mm"] for c in recs}
            con = net_contract(qb.b, net)
            permitted = permitted_layers(qb.routable, con["layers"], reserved,
                                         net)
            was = sum(c["mm"] for c in recs)
            rec = dict(net=net, layer=sorted(lkeys), was_mm=round(was, 4),
                       max_mm=round(was + 2.0 * math.pi * radius / 1e6, 4),
                       tracks=len(recs))
            if len(lkeys) != 1 or len(widths) != 1:
                rec.update(ok=False, reason="NOT_A_CHAIN",
                           why="a chain must be ONE layer and ONE width")
                out.append(rec); ok_all = False
                continue
            lkey = sorted(lkeys)[0]
            # D-609.  The writer's own `detour_layers` decides this, so the
            # screen and the gate cannot disagree about whether a track may be
            # put back where it already is.
            layers, spent = detour_layers(permitted, lkey, own_layer)
            rec.update(layers_allowed=list(layers), own_layer=spent)
            if lkey not in layers:
                rec.update(ok=False, reason="UNDETOURABLE_LAYER",
                           why="layer %s is not in this net's contract %s -- "
                               "the track can be cut and can never be put back"
                               % (lkey, list(layers)))
                out.append(rec); ok_all = False
                continue
            ends = chain_ends_mm(recs)
            if ends is None:
                rec.update(ok=False, reason="NOT_A_CHAIN",
                           why="the cut tracks of this net do not form a "
                               "simple chain with exactly two free ends")
                out.append(rec); ok_all = False
                continue
            g = guard_for(spec, net) if spec else {}
            for lk, pts in guard_for(disc, net).items():
                g.setdefault(lk, []).extend(pts)
            width_nm = int(round(sorted(widths)[0] * 1e6))
            # The previous detour's copper is on `qb.shapes` but not in the
            # obstacle cache, and a relay that could not see it would be
            # measuring a board the applier never routes on.
            qb._obs_cache = None
            field = mz.Field(qb, net, width_nm, con["clr_pad"], con["clr"],
                             con["via_dia"], con["via_drill"], G=grid,
                             layers=layers, guard=g)
            a_nm = tuple(int(round(v * 1e6)) for v in ends[0])
            b_nm = tuple(int(round(v * 1e6)) for v in ends[1])
            r = mz.route_points(qb, field, a_nm, b_nm, lkey,
                                via_cost_mm=via_cost_mm, emit=True,
                                max_mm=rec["max_mm"])
            rec.update(ok=bool(r.get("ok")), reason=r.get("reason"),
                       why=str(r.get("why"))[:200] if r.get("why") else None,
                       mm=r.get("mm"), vias=r.get("vias"),
                       mm_by_layer=r.get("mm_by_layer"),
                       a_mm=list(ends[0]), b_mm=list(ends[1]))
            ok_all = ok_all and bool(r.get("ok"))
            out.append(rec)
        qb.revert(m)
    return dict(all_relaid=ok_all, tracks=out)


def try_island(qb, field, island, max_mm, land_ok=None):
    """Does `stitch_pad` close this island?  Every trial laid, proved, reverted.

    `stitch_pad` narrows `Field.via_ok` through `forbid_via` when it succeeds,
    so the lattice is snapshotted and restored around every trial: a screen that
    let one pad's success shrink the next pad's search would be measuring its
    own bookkeeping.
    """
    import maze3d as mz
    last = None
    for pad in island:
        keep = field.via_ok.copy()
        m = qb.mark()
        r = mz.stitch_pad(qb, field, pad, max_mm=max_mm, escape_limit=12,
                          land_ok=land_ok)
        qb.revert(m)
        field.via_ok = keep
        last = r
        if r.get("ok"):
            return r
    return last


def candidates(qb, field, island, max_mm, cap):
    """Unprotected foreign routed TRACKS whose copper enters the stitch window.

    Every copper layer, not just the routable ones: `Field._via_grid` ANDs the
    barrel test over the whole stack, so a legacy track on an inner layer denies
    a site exactly as an `F.Cu` one does.

    A pad is never a candidate -- it is where a part is soldered -- and neither
    is a via: a barrel is a hole through every layer and a split cannot cut one.
    Foreign vias in the window are reported separately so a `SEGMENT_WALL` says
    which kind of obstacle it is.
    """
    import qrouter as qr
    discs = [(p['x'], p['y'], max_mm * qr.MM) for p in island]
    segs, vias = [], []
    for L in qb.cu:
        for s in qb.shapes[L]:
            if s.net == field.net or not s.net:
                continue
            if isinstance(s, qr.SEG):
                if s.tag != 'track' or PROTECTED.search(s.net):
                    continue
                d = min(s.dist(cx, cy) for (cx, cy, _) in discs)
                near = min((s.dist(cx, cy) - R) for (cx, cy, R) in discs)
                if near < 0:
                    segs.append((d, L, s))
            elif s.tag == 'via':
                if any(s.dist(cx, cy) < R for (cx, cy, R) in discs):
                    vias.append((L, s))
    segs.sort(key=lambda t: (t[0], t[1], t[2].x0, t[2].y0, t[2].x1, t[2].y1))
    seen, out = set(), []
    for (_, L, s) in segs:
        key = (s.net, L, s.x0, s.y0, s.x1, s.y1, s.hw)
        if key in seen:
            continue
        seen.add(key)
        out.append((L, s))
        if cap and len(out) >= cap:
            break
    vseen, vout = set(), []
    for (L, s) in vias:
        key = (s.net, s.cx, s.cy)
        if key not in vseen:
            vseen.add(key)
            vout.append(dict(net=s.net, xy_mm=[round(s.cx / 1e6, 4),
                                               round(s.cy / 1e6, 4)],
                             dia_mm=round(2 * s.hx / 1e6, 3)))
    return out, vout


def seg_record(L, s):
    return dict(net=s.net, layer=L, width_mm=round(2 * s.hw / 1e6, 3),
                a_mm=[round(s.x0 / 1e6, 4), round(s.y0 / 1e6, 4)],
                b_mm=[round(s.x1 / 1e6, 4), round(s.y1 / 1e6, 4)],
                mm=round(math.hypot(s.x1 - s.x0, s.y1 - s.y0) / 1e6, 4))


def window_cuts(chosen, island, max_mm):
    """One disc per island pad, over every chosen track: question 1's offer."""
    import qrouter as qr
    R = max_mm * qr.MM
    return [(L, s, p['x'], p['y'], R) for (L, s) in chosen for p in island]


def shrink(qb, field, island, chosen, max_mm, site, ladder, land_ok=None):
    """The SMALLEST single disc at `site` that still opens the land.

    Question 1's window cut is an upper bound, not a transaction: it would take
    the whole of every crossing track inside 8 mm.  What a barrel actually needs
    is a disc at its own site, so the ladder walks down and the answer is the
    first radius that still stitches -- re-proved, like everything else, on the
    real `stitch_pad`.
    """
    best = None
    for R in ladder:
        cuts = [(L, s, site[0], site[1], R) for (L, s) in chosen]
        if not any(cut_capsule(_SEG(), s, site[0], site[1], R) != [s]
                   for (L, s) in chosen):
            continue
        with Cuts(qb, field, cuts):
            r = try_island(qb, field, island, max_mm, land_ok)
        if r and r.get("ok"):
            best = (R, r)
        else:
            break
    return best


def _SEG():
    import qrouter as qr
    return qr.SEG


def connectivity_price(board_path, cuts, tmpdir):
    """What each cut costs the CUT NET, counted by KiCad's own connectivity.

    A cut is only free if the net it cuts is still in as many pieces as it was.
    That is a fill/connectivity fact, so it is measured the way clause 4
    measures it: apply the split to a COPY of the board, reload it, and ask
    `GetConnectivity` for the cluster count of that net's pads before and after.
    """
    import pcbnew
    src = Path(tmpdir) / "cut.kicad_pcb"
    shutil.copy(board_path, src)
    board = pcbnew.LoadBoard(str(src))

    def clusters(b, net):
        b.BuildConnectivity()
        conn = b.GetConnectivity()
        pads, index = [], {}
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() == net and p.GetNumber():
                    key = (f.GetReference() + '.' + p.GetNumber(),
                           p.GetPosition().x, p.GetPosition().y)
                    index[key] = p
                    pads.append(key)
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
        return len({find(k) for k in parent})

    nets = sorted({c["net"] for c in cuts})
    before = {n: clusters(board, n) for n in nets}

    removed, added = 0, 0
    for c in cuts:
        for t in list(board.GetTracks()):
            if t.GetClass() != 'PCB_TRACK' or t.GetNetname() != c["net"]:
                continue
            a = (round(t.GetStart().x / 1e6, 4), round(t.GetStart().y / 1e6, 4))
            b = (round(t.GetEnd().x / 1e6, 4), round(t.GetEnd().y / 1e6, 4))
            if sorted([a, b]) != sorted([tuple(c["a_mm"]), tuple(c["b_mm"])]):
                continue
            layer = t.GetLayer()
            width = t.GetWidth()
            netcode = t.GetNetCode()
            board.Remove(t)
            removed += 1
            for piece in c["stubs_mm"]:
                nt = pcbnew.PCB_TRACK(board)
                nt.SetStart(pcbnew.VECTOR2I(int(piece[0][0] * 1e6),
                                            int(piece[0][1] * 1e6)))
                nt.SetEnd(pcbnew.VECTOR2I(int(piece[1][0] * 1e6),
                                          int(piece[1][1] * 1e6)))
                nt.SetWidth(width)
                nt.SetLayer(layer)
                nt.SetNetCode(netcode)
                board.Add(nt)
                added += 1
            break
    pcbnew.SaveBoard(str(src), board)
    board = pcbnew.LoadBoard(str(src))
    after = {n: clusters(board, n) for n in nets}
    return dict(tracks_split=removed, stubs_left=added,
                clusters_before=before, clusters_after=after,
                free=all(after[n] <= before[n] for n in nets),
                worse={n: [before[n], after[n]] for n in nets
                       if after[n] > before[n]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--max-mm", type=float, default=8.0)
    ap.add_argument("--rung", choices=("floor", "relief"), default="floor")
    ap.add_argument("--cap", type=int, default=14,
                    help="most candidate tracks per land (nearest first)")
    ap.add_argument("--guard", type=Path)
    ap.add_argument("--body-landing", action="store_true",
                    help="D-608: a barrel counts only if it lands INSIDE this "
                         "net's own body pour.  Without it this screen "
                         "reports sites that are legal and dead -- "
                         "`R129.1` measured, routed, gated and refused")
    ap.add_argument("--no-relay", action="store_true",
                    help="skip the D-608 relay price -- would every track this "
                         "land has to CUT actually go back between its own two "
                         "ends?  A land that opens and cannot be relaid is a "
                         "gate run this screen owes nobody")
    ap.add_argument("--pad", action="append", default=[], metavar="REF.NUM",
                    help="D-609: offer ONLY these pads as a land's launch.  An "
                         "island's stitch site is decided by which of its pads "
                         "is tried first, and island membership moves whenever "
                         "a promotion joins two orphans; this names the land "
                         "instead of inheriting it.  Repeatable")
    ap.add_argument("--relay-own-layer", action="store_true",
                    help="D-609: price the relay with the OWN-LAYER allowance "
                         "-- a track being put back may be put back on the "
                         "layer it already lawfully occupies, even a reserved "
                         "inner plane, and on that ONE layer only.  This is "
                         "`route_maze_batch.py --detour-own-layer` measured "
                         "read-only; without it every legacy In3 track still "
                         "reports UNDETOURABLE_LAYER")
    ap.add_argument("--no-price", action="store_true",
                    help="skip the KiCad connectivity price (lattice only)")
    ap.add_argument("--plan-out", type=Path,
                    help="also write a `route_maze_batch.py --detour-spec` "
                         "file for every land that opened, so the measurement "
                         "and the transaction cannot drift apart.  Tracks of "
                         "the same net that this screen cut for ONE land are "
                         "emitted as a CHAIN, because that is how the applier "
                         "has to take collinear segments whose junction falls "
                         "inside the reserved disc")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN, BOARD_VIA_DIA_MIN,
                                  BOARD_HOLE_MIN, BOARD_TRACK_MIN)

    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    neck = mz.neck_rule(qb)
    reserved = reserved_inner_planes(qb.b)

    nets = list(a.nets)
    if not nets:
        nets = sorted(n for n in {z.GetNetname() for z in qb.b.Zones()
                                  if not z.GetIsRuleArea() and z.IsFilled()}
                      if n and mz.has_plane(qb, n))

    tmp = tempfile.mkdtemp(prefix="segevict-")
    out = []
    for net in nets:
        if not mz.has_plane(qb, net):
            continue
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        over = DRU_CLASS.get(c["netclass"], {})
        w_floor = max(BOARD_TRACK_MIN, over.get("width", 0))
        d_floor = max(BOARD_HOLE_MIN, over.get("drill", 0))
        v_floor = max(BOARD_VIA_DIA_MIN, d_floor + 2 * ANNULAR_MIN)
        if a.rung == "floor":
            w, clr, vd, vdr = w_floor, c["clr"], v_floor, d_floor
        else:
            w, clr, vd, vdr = (min(w_floor, RELIEF_WIDTH), RELIEF_CLR,
                               RELIEF_VIA_DIA, RELIEF_VIA_DRILL)
        field = mz.Field(qb, net, w, c["clr_pad"], clr, vd, vdr, G=a.grid,
                         layers=layers, neck=neck,
                         guard=guard_for(spec, net) if spec else None)

        # D-608.  The body mask is taken ONCE, on the uncut board, and is
        # valid under every cut this screen makes: a `Cuts` context touches
        # only the in-memory obstacle model, and the real refill after a
        # detour removes FOREIGN copper, which can only let this net's pour
        # GROW.  A site inside the body today is inside it afterwards.
        land_ok, land_info = None, None
        if a.body_landing:
            land_ok, land_info = mz.body_landing(qb, net, field)

        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        body = max(islands, key=len)
        rec = dict(net=net, netclass=c["netclass"],
                   rung=dict(name=a.rung, width=w, clr=clr, via_dia=vd,
                             via_drill=vdr,
                             needs_licence=bool(w < w_floor or clr < c["clr"]
                                                or vd < v_floor
                                                or vdr < d_floor)),
                   body_landing=land_info, lands=[])
        # The cut radius a barrel actually needs: its own copper radius plus the
        # clearance the CUT net owes routed copper.  The ladder walks down from
        # the window through that figure so the report names both the upper
        # bound and the executable disc.
        need = vd / 2.0 + max(clr, c["clr_pad"])
        ladder = [a.max_mm * qr.MM, 2000000, 1200000, 800000,
                  math.ceil(need / 1000.0) * 1000.0]
        ladder = sorted({int(r) for r in ladder}, reverse=True)

        for island in islands:
            if island is body:
                continue
            # D-609.  `try_island` takes the FIRST pad of an island that opens
            # and `stitch_pad` then takes the first legal barrel by distance,
            # so WHICH pad launches is decided by island order -- and island
            # membership moves whenever a promotion joins two orphans.  D-608
            # measured `U12.5` at a 1.136 mm stitch behind a 0.8 mm disc; the
            # same board with `U12.4` and `U12.5` merged into one island offers
            # `U12.4` first, at 3.982 mm behind an 8 mm one.  `--pad` says which
            # land of the island is being measured.  It narrows only the
            # LAUNCH: the island, the body, the cut window and the verdict are
            # unchanged, so this cannot invent a site that was not there.
            island_all = island
            if a.pad:
                island = [p for p in island_all if p["ref"] in set(a.pad)]
                if not island:
                    continue
            base = try_island(qb, field, island, a.max_mm, land_ok)
            refs = [p["ref"] for p in island]
            if base and base.get("ok"):
                rec["lands"].append(dict(land=refs, verdict="ALREADY_OPEN",
                                         stitch_mm=base["mm"]))
                continue
            if base and base.get("reason") not in ("NO_VIA_SITE",
                                                  "NO_BODY_VIA_SITE"):
                rec["lands"].append(dict(land=refs, verdict="NOT_A_POCKET",
                                         reason=base.get("reason"),
                                         why=str(base.get("why"))[:160]))
                continue
            chosen, vias = candidates(qb, field, island, a.max_mm, a.cap)
            if not chosen:
                rec["lands"].append(dict(
                    land=refs, verdict="SEGMENT_WALL", candidates=0,
                    foreign_vias=vias,
                    why="no unprotected foreign routed track enters the "
                        "%.1f mm window at all" % a.max_mm))
                print("  %-24s %-22s SEGMENT_WALL (no candidates)"
                      % (net[:24], ",".join(refs)[:22]),
                      file=sys.stderr, flush=True)
                continue
            with Cuts(qb, field, window_cuts(chosen, island, a.max_mm)):
                upper = try_island(qb, field, island, a.max_mm, land_ok)
            if not (upper and upper.get("ok")):
                rec["lands"].append(dict(
                    land=refs, verdict="SEGMENT_WALL",
                    candidates=len(chosen), foreign_vias=vias,
                    tracks=[seg_record(L, s) for (L, s) in chosen],
                    why="every unprotected foreign track inside %.1f mm cut "
                        "at once and the barrel site is still %s"
                        % (a.max_mm, (upper or {}).get("reason"))))
                print("  %-24s %-22s SEGMENT_WALL (%d tracks cut, still %s)"
                      % (net[:24], ",".join(refs)[:22], len(chosen),
                         (upper or {}).get("reason")),
                      file=sys.stderr, flush=True)
                continue

            # QUESTION 2 -- one track alone.
            single = None
            for (L, s) in chosen:
                with Cuts(qb, field, window_cuts([(L, s)], island, a.max_mm)):
                    r = try_island(qb, field, island, a.max_mm, land_ok)
                if r and r.get("ok"):
                    single = (L, s, r)
                    break
            if single is not None:
                keep = [(single[0], single[1])]
                final = single[2]
            else:
                # QUESTION 3 -- reverse-greedy minimal set.
                keep = list(chosen)
                for (L, s) in list(chosen):
                    trial = [t for t in keep if t[1] is not s]
                    if not trial:
                        continue
                    with Cuts(qb, field,
                              window_cuts(trial, island, a.max_mm)):
                        r = try_island(qb, field, island, a.max_mm, land_ok)
                    if r and r.get("ok"):
                        keep = trial
                with Cuts(qb, field, window_cuts(keep, island, a.max_mm)):
                    final = try_island(qb, field, island, a.max_mm,
                                       land_ok)
                if not (final and final.get("ok")):
                    rec["lands"].append(dict(
                        land=refs, verdict="UNSTABLE",
                        why="the minimal set did not re-prove open"))
                    continue

            site = final["via_xy_nm"]
            sh = shrink(qb, field, island, keep, a.max_mm, site, ladder,
                        land_ok)
            if sh is None:
                shape, radius, proof = "window", int(a.max_mm * qr.MM), final
                applied = window_cuts(keep, island, a.max_mm)
            else:
                shape, radius, proof = "disc", int(sh[0]), sh[1]
                applied = [(L, s, site[0], site[1], radius) for (L, s) in keep]

            # The cut a transaction would actually execute, per track: the
            # pieces that SURVIVE every disc applied to it, and how much copper
            # goes.  A track cut by more than one disc is cut by all of them.
            cuts, held = [], []
            for (L, s) in keep:
                pieces = [s]
                for (cl, cs, cx, cy, cr) in applied:
                    if cs is not s:
                        continue
                    nxt = []
                    for p in pieces:
                        nxt += cut_capsule(qr.SEG, p, cx, cy, cr)
                    pieces = nxt
                whole = math.hypot(s.x1 - s.x0, s.y1 - s.y0)
                left = sum(math.hypot(p.x1 - p.x0, p.y1 - p.y0) for p in pieces)
                d = seg_record(L, s)
                d["stubs_mm"] = [
                    [[round(p.x0 / 1e6, 4), round(p.y0 / 1e6, 4)],
                     [round(p.x1 / 1e6, 4), round(p.y1 / 1e6, 4)]]
                    for p in pieces]
                d["removed_mm"] = round((whole - left) / 1e6, 4)
                d["whole_track"] = not pieces
                cuts.append(d)
                held.append((L, s, d))
            land = dict(land=refs,
                        verdict="SEGMENT_OPENS" if single is not None
                                else "SEGMENT_SET_OPENS",
                        candidates=len(chosen), foreign_vias=vias,
                        cut_shape=shape,
                        cut_radius_mm=round(radius / 1e6, 4),
                        cuts=cuts,
                        stitch=dict(pad=proof["pad"], layer=proof["layer"],
                                    mm=proof["mm"],
                                    via_xy=list(proof["via_xy"])))
            if not a.no_price:
                land["price"] = connectivity_price(a.board, cuts, tmp)
            if not a.no_relay:
                land["relay"] = relay_price(
                    qb, a.grid, reserved, held, site, radius, [net], spec,
                    own_layer=a.relay_own_layer)
            rec["lands"].append(land)
            print("  %-24s %-22s %s  cut %d track(s) r=%.2fmm  stitch %.3fmm %s"
                  % (net[:24], ",".join(refs)[:22], land["verdict"],
                     len(cuts), radius / 1e6, proof["mm"],
                     "FREE" if land.get("price", {}).get("free") else
                     ("REJOIN" if "price" in land else ""))
                     + ("" if a.no_relay else
                        ("  RELAY-OK" if land["relay"]["all_relaid"]
                         else "  RELAY-FAIL(%s)"
                         % ",".join(sorted({t.get("reason") or "?"
                                            for t in land["relay"]["tracks"]
                                            if not t["ok"]})))),
                  file=sys.stderr, flush=True)
        out.append(rec)

    # THE PLAN IS THE MEASUREMENT, WRITTEN IN THE WRITER'S OWN GRAMMAR.  A land
    # that opened here is a transaction; typing it out by hand a second time is
    # how a measurement and the thing it authorises drift apart.  One reserve
    # disc per land at the radius this screen proved, one detour entry per net,
    # and a net cut more than once for the same land becomes a `tracks` chain
    # -- the applier proves it really is a chain, and refuses if it is a tee.
    if a.plan_out:
        plan = dict(schema=1, reserve=[], detours=[],
                    note="emitted by screen_segment_evict.py --plan-out from "
                         "board %s; each reserve disc is the radius the screen "
                         "proved opens that land, each detour is a track it "
                         "proved has to move" % board_sha[:16])
        for rec in out:
            for l in rec["lands"]:
                if not l["verdict"].startswith("SEGMENT") or "cuts" not in l:
                    continue
                plan["reserve"].append(dict(
                    x_mm=l["stitch"]["via_xy"][0], y_mm=l["stitch"]["via_xy"][1],
                    r_mm=l["cut_radius_mm"], exempt=[rec["net"]],
                    land=l["land"]))
                by_net = {}
                for c in l["cuts"]:
                    by_net.setdefault(c["net"], []).append(c)
                for net, cs in sorted(by_net.items()):
                    tracks = [dict(layer=LAYER_NAME[c["layer"]],
                                   a_mm=c["a_mm"], b_mm=c["b_mm"],
                                   width_mm=c["width_mm"]) for c in cs]
                    plan["detours"].append(
                        dict(net=net, **(tracks[0] if len(tracks) == 1
                                         else dict(tracks=tracks))))
        a.plan_out.write_text(
            json.dumps(plan, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        authoritative_unchanged=(board_sha == after),
        grid=a.grid, max_mm=a.max_mm, cap=a.cap, rung=a.rung,
        body_landing=bool(a.body_landing),
        relay_own_layer=bool(a.relay_own_layer),
        pads=list(a.pad),
        guard=str(a.guard) if a.guard else None,
        guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                      if a.guard else None),
        question=("for every open pour land that fails stitch_pad with "
                  "NO_VIA_SITE, is the pocket full of CUTTABLE foreign track "
                  "-- so that a SEGMENT eviction would open a barrel site -- "
                  "or is it full of pads and barrels no split can touch"),
        method=("read-only; foreign tracks cut in the in-memory obstacle model "
                "and re-offered to the real maze3d.stitch_pad through the "
                "promoter's own Field, verify_laid proving each, every trial "
                "reverted; the connectivity price is measured by KiCad's own "
                "BuildConnectivity on a scratch copy"),
        nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
