#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: HOW WIDE A CONDUCTOR DOES THIS LAND'S CHANNEL
ADMIT, AND WHICH TWO OBJECTS BIND IT?

Every width instrument this project owns answers a YES/NO at ONE width.
`screen_escape_class.py` asks whether a land launches at its class width.
`screen_escape_pocket.py` ladders the LATTICE and reports the pocket AREA.
`--escape-floor` (D-630) and `--trunk-floor` (D-662) each offer ONE lower
width and report whether the answer moved.  D-670 ran the floor ladder over
the seven `NO_ESCAPE_AT_ANY_PITCH` nets and 0 of 35 lands changed verdict, and
concluded PAD-GEOMETRY WALLS, NOT WIDTH WALLS.  That reading is right and it
is not actionable, because it does not say WHAT geometry, HOW SHORT the
channel falls, or WHICH object is on each side of it.

This screen answers those three, in exact geometry and with no lattice:

  LADDER      the land is offered `maze3d.pad_escapes` -- the router's own
              launch, pocket and off-centre sources -- at a descending width
              ladder, and the WIDEST width that yields an escape is recorded.
              This is a ROUTER answer, so it cannot disagree with the gate.
  CHANNEL     the land's exit corridor is the strip that runs OUTWARD from the
              pad along the land's own lead axis.  Walking outward in 0.025 mm
              steps, at every station the copper on the land's own layer is
              projected ACROSS the strip and the free gap CONTAINING THE PAD'S
              CENTRELINE is measured -- a wider gap on the far side of a
              neighbour is not reachable from this land and is not counted.
              Three readings come back and they answer different questions:
              `row` is the narrowest station INSIDE the land's own extent,
              which is the package's own pitch and is a LAND-PATTERN figure;
              `pinch` is the narrowest station anywhere in the window; and
              `profile` reads the channel at 0.00/0.25/0.50/1.00/1.50/2.00 mm
              past the land's outer edge, so a reader can see WHERE it closes.
              Every `at_mm` is measured from that outer edge and is NEGATIVE
              inside the land.  `admits_mm` is the gap less the clearance each
              side is owed -- `clr_pad` where a pad stands there, the routed
              clearance where copper does.
  DEFICIT     against that pinch stand four widths this board can license:
              the netclass width the gate routes at, the `.kicad_dru` class
              MINIMUM `--trunk-floor` descends to, the 0.200 mm section-9
              pad-escape necking minimum where the land is inside one of the
              named courtyards, and `.kicad_pro` `min_track_width`.  The
              verdict names the WEAKEST lever that would open the land, or
              says that none of them would.

WHY THE VERDICT MATTERS.  `NO_ESCAPE_AT_ANY_PITCH` is four different walls and
they have four different owners:

  LAUNCHES_AT_CLASS   the land is not a width wall at all; go and look at the
                      corridor (`screen_evicted_corridor.py`)
  CLASS_FLOOR_OPENS   `--trunk-floor` reaches it and D-662 already priced the
                      descent by IPC-2221B
  NECK_OPENS          `--neck` reaches it: the land sits inside a courtyard
                      section 9 names and the launch admits 0.200 mm
  LICENCE_ONLY        the launch admits copper NARROWER than anything the
                      board licenses there.  This is the D-610 doctrine's
                      shape -- a `PAD_ESCAPE_RUN_<REF>_<PIN>` rule area,
                      declared before the router moves and priced by
                      `audit_bond_ampacity.py`.  Before spending one, ask
                      `checks/leaf_land_contract.py` what the land IS: a
                      SUPPLY_PORT is a chip's own supply pin and LL4 leaves
                      the rail bar standing over it
  ..._UNPRICED        the same two, where IPC-2221B at this board's copper
                      says the narrow rung does NOT carry the current
                      `.kicad_dru` section 5 publishes for that class.  A
                      geometric opening is not an admission and the suffix is
                      how this screen refuses to put an unpayable move at the
                      top of the next decision's work list
  PACKAGE_PITCH_WALL  the pinch is made by two pads OF THE LAND'S OWN
                      FOOTPRINT.  No router flag, no eviction, no lattice and
                      no rule area reaches this one: the binder is the vendor
                      land pattern, so the only levers are a PART CHANGE or a
                      REFLOORPLAN, and saying so by name stops the next
                      decision spending a router flag on it
  NO_CHANNEL          nothing leaves at any width this screen asked

    python3 screen_fanout_channel.py                       # every open net
    python3 screen_fanout_channel.py --net /NFC_SUPPLY -o OUT.json
    python3 screen_fanout_channel.py --land U9.10 --land U16.3

The board is never written and its sha256 is re-read at exit.
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import qrouter as qr                                          # noqa: E402
import incremental_router as ir                               # noqa: E402
import maze3d as mz                                           # noqa: E402
from route_maze_batch import (DRU_CLASS, net_contract,        # noqa: E402
                              reserved_inner_planes, permitted_layers,
                              trunk_floor_price)

AUTHORITY = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
M = 1000000
STEP = 25000                    # outward sampling pitch, nm
PROBE = 2000000                 # how far outward the channel is walked, nm
# The width ladder.  Every rung is a width this board either routes at, names
# in a rule, or could name; nothing below `min_track_width` is asked, because
# copper the board's own setup forbids is not a measurement anybody can spend.
LADDER = (800000, 600000, 500000, 400000, 350000, 300000, 250000,
          200000, 150000, 100000)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# the exit corridor
# --------------------------------------------------------------------------- #
def pad_box(pad):
    """(x0, y0, x1, y1) of a `maze3d` pad record, in nm."""
    return (pad['x'] - pad['hx'], pad['y'] - pad['hy'],
            pad['x'] + pad['hx'], pad['y'] + pad['hy'])


def outward(fp_pos, pad):
    """Unit outward axis for a land, snapped to the axis it actually leaves on.

    A peripheral package land is a LEAD, and a lead points away from the body:
    the land's LONG axis is the axis it leaves on, so a 0.750 x 0.300 mm land
    on a west row leaves west and a 0.300 x 0.750 mm land on a north row
    leaves north.  A square land, or a two-terminal chip land, has no lead, so
    the direction is taken from the footprint origin instead.  The rule that
    fired is reported, so a reader can see which one chose the axis.
    """
    x0, y0, x1, y1 = pad_box(pad)
    dx, dy = pad['x'] - fp_pos[0], pad['y'] - fp_pos[1]
    w, h = x1 - x0, y1 - y0
    if abs(w - h) > 50000:            # a lead land names its own axis
        ax, why = ('x' if w > h else 'y'), 'PAD_SHAPE'
    else:
        ax, why = ('x' if abs(dx) >= abs(dy) else 'y'), 'FOOTPRINT_ORIGIN'
    if ax == 'x':
        return ((1.0, 0.0) if dx >= 0 else (-1.0, 0.0)), 'x', why
    return ((0.0, 1.0) if dy >= 0 else (0.0, -1.0)), 'y', why


def _kind_of(s):
    tag = getattr(s, 'tag', None)
    if tag == 'track':
        return 'track', None
    if tag == 'via' or (tag or '').startswith('via'):
        return 'via', None
    return 'pad', tag


def obstacles(qb, layer, land_net, land_tag, window, oax, sign):
    """Foreign objects on `layer` whose OUTWARD extent meets `window`.

    Each entry answers `at(o) -> (p_lo, p_hi)`: the copper's extent ACROSS the
    corridor at outward station `o`, which is what a channel measurement needs
    and a bounding box cannot give.  A track is its segment inflated by w/2, a
    via and a pad their bounding box -- conservative for a round barrel and
    exact for the rectangular lands this board uses.
    """
    def O(x, y):
        return (x if oax == 'x' else y) * sign

    def P(x, y):
        return y if oax == 'x' else x

    o0w, o1w = window
    out = []
    for s in qb.shapes.get(layer, ()):
        if getattr(s, 'net', None) == land_net:
            continue
        kind, ref = _kind_of(s)
        if kind == 'pad' and ref == land_tag:
            continue
        if kind == 'track':
            ax, ay = getattr(s, 'x0', None), getattr(s, 'y0', None)
            if ax is None:
                continue
            bx, by = s.x1, s.y1
            w = getattr(s, 'w', 0) or 0
            oa, ob = O(ax, ay), O(bx, by)
            pa, pb = P(ax, ay), P(bx, by)
            lo_o, hi_o = min(oa, ob) - w / 2.0, max(oa, ob) + w / 2.0
            if hi_o < o0w or lo_o > o1w:
                continue
            out.append((kind, s.net, ref,
                        _track_at(oa, ob, pa, pb, w)))
        else:
            b = s.bbox(0)
            oo = [O(b[0], b[1]), O(b[2], b[3])]
            pp = [P(b[0], b[1]), P(b[2], b[3])]
            lo_o, hi_o = min(oo), max(oo)
            if hi_o < o0w or lo_o > o1w:
                continue
            out.append((kind, s.net, ref,
                        _box_at(lo_o, hi_o, min(pp), max(pp))))
    return out


def _track_at(oa, ob, pa, pb, w):
    lo_o, hi_o = min(oa, ob), max(oa, ob)

    def at(o):
        if o < lo_o - w / 2.0 or o > hi_o + w / 2.0:
            return None
        if abs(ob - oa) < 1:
            c0, c1 = min(pa, pb), max(pa, pb)
        else:
            t = max(0.0, min(1.0, (o - oa) / (ob - oa)))
            c0 = c1 = pa + (pb - pa) * t
        return (c0 - w / 2.0, c1 + w / 2.0)
    return at


def _box_at(o0, o1, p0, p1):
    def at(o):
        return (p0, p1) if o0 <= o <= o1 else None
    return at


def channel(qb, land_net, land_tag, pad, layer, fp_pos, clr_pad, clr_trk,
            probe=PROBE, step=STEP):
    """Walk the exit corridor outward and report the NARROWEST free gap.

    The gap measured is the one that CONTAINS the land's own centreline: a
    conductor leaving this land must start on it, so a wider gap on the far
    side of a neighbour is not reachable and is not counted.  The window starts
    at the land's NEAR edge, so the neighbours that flank the land itself are
    charged, not only what stands beyond it.
    """
    (ux, uy), oax, why = outward(fp_pos, pad)
    sign = ux if oax == 'x' else uy
    x0, y0, x1, y1 = pad_box(pad)
    if oax == 'x':
        pc = pad['y']
        near, far = (x0 * sign, x1 * sign) if sign > 0 else (-x1, -x0)
    else:
        pc = pad['x']
        near, far = (y0 * sign, y1 * sign) if sign > 0 else (-y1, -y0)
    obs = obstacles(qb, layer, land_net, land_tag, (near, far + probe),
                    oax, sign)

    def at_station(o):
        lo, hi = -1e18, 1e18
        lo_by = hi_by = None
        for kind, net, ref, at in obs:
            ext = at(o)
            if ext is None:
                continue
            q0, q1 = ext
            if q1 <= pc:
                if q1 > lo:
                    lo, lo_by = q1, (kind, net, ref)
            elif q0 >= pc:
                if q0 < hi:
                    hi, hi_by = q0, (kind, net, ref)
            else:                                   # the centreline is buried
                lo = hi = pc
                lo_by = hi_by = (kind, net, ref)
        return dict(gap=hi - lo, at=o, lo=lo, hi=hi, lo_by=lo_by, hi_by=hi_by)

    def side(by):
        return None if by is None else dict(kind=by[0], net=by[1], land=by[2])

    def owed(by):
        return clr_pad if (by and by[0] == 'pad') else clr_trk

    def report(st):
        if st is None or st['gap'] > 1e17:
            return dict(gap_mm=None, admits_mm=None,
                        at_mm=None if st is None
                        else round((st['at'] - far) / M, 4),
                        lo=None, hi=None)
        room = st['gap'] - owed(st['lo_by']) - owed(st['hi_by'])
        return dict(gap_mm=round(st['gap'] / M, 4),
                    admits_mm=round(max(0.0, room) / M, 4),
                    at_mm=round((st['at'] - far) / M, 4),
                    lo=side(st['lo_by']), hi=side(st['hi_by']),
                    clearance_lo_mm=owed(st['lo_by']) / M,
                    clearance_hi_mm=owed(st['hi_by']) / M)

    pinch = row = None
    o, stations = near, 0
    while o <= far + probe:
        st = at_station(o)
        stations += 1
        if pinch is None or st['gap'] < pinch['gap']:
            pinch = st
        # THE ROW.  Stations that lie inside the land's OWN outward extent are
        # the package's own pitch: whatever binds here is a land pattern
        # figure, not a routing one, and no router flag reaches it.
        if o <= far and (row is None or st['gap'] < row['gap']):
            row = st
        o += step
    profile = [report(at_station(min(far + int(round(d * M)), far + probe)))
               for d in (0.0, 0.25, 0.5, 1.0, 1.5, 2.0)
               if int(round(d * M)) <= probe]
    return dict(
        outward_axis=oax, outward=[ux, uy], axis_chosen_by=why,
        stations=stations, pinch=report(pinch), row=report(row),
        profile=profile)


# --------------------------------------------------------------------------- #
# the ladder
# --------------------------------------------------------------------------- #
def widest_launch(qb, net, c, far, pad, toward, ladder=LADDER, G=50000):
    rungs = []
    widest = None
    for w in ladder:
        if widest is not None:
            break
        f = mz.Field(qb, net, w, c["clr_pad"], c["clr"], c["via_dia"],
                     c["via_drill"], G=G, layers=far,
                     neck=None)
        f.offcentre = True
        t = time.time()
        try:
            e = mz.pad_escapes(qb, f, pad, toward, limit=8)
        except Exception as exc:                       # noqa: BLE001
            rungs.append(dict(width_mm=w / M, escapes=None, error=repr(exc)))
            continue
        rungs.append(dict(width_mm=w / M, escapes=len(e),
                          seconds=round(time.time() - t, 2)))
        if e:
            widest = w
    return widest, rungs


def narrow_price(netclass, width_nm, dt_k=10.0):
    """Can a conductor this narrow carry what the board publishes for its class?

    A GEOMETRIC opening is not an admission.  `--neck` and a width licence both
    put copper NARROWER than the class floor on a net, and section 5 of the
    `.kicad_dru` publishes a design current for the classes that carry one.
    The price here is the SAME pair `route_maze_batch.trunk_floor_price` and
    `PP2` charge with -- `audit_bond_ampacity` at this board's own copper,
    against `published_rail_currents` -- so a verdict cannot admit a width the
    rest of the tool chain would refuse.

    A class the table does not price returns `required=None` and `ok=None`:
    that is an OPEN QUESTION and not a pass, and the verdict says so by name.
    """
    if str(HERE / "checks") not in sys.path:
        sys.path.insert(0, str(HERE / "checks"))
    import audit_bond_ampacity as ab
    from pour_partition_contract import published_rail_currents
    table, _ = published_rail_currents(str(AUTHORITY.with_suffix(".kicad_dru")))
    required = (table.get(netclass) or {}).get("amps")
    amps = round(ab.ampacity(ab.track_area(width_nm / M), dt_k), 3)
    ok = None if required is None else (amps + 1e-9 >= required)
    return dict(width_mm=width_nm / M, amps_at_dt10=amps,
                class_required_amps=required, ok=ok,
                why=("CLASS_CARRIES_NO_PUBLISHED_CURRENT" if required is None
                     else ("PRICED_AT_THE_PUBLISHED_BAR" if ok
                           else "UNDER_PRICED")))


def verdict_for(widest, need, floor, neck_min, board_min, price):
    """The WEAKEST lever that would open this land -- and whether it is PAID.

    A narrow rung that the class's own published current refuses is reported
    `_UNPRICED`, never as an opening: D-610 spent a width licence on `+3V3`
    only after IPC-2221B priced it, and a screen that hid that step would put
    an unpayable move at the top of the next decision's work list.
    """
    if widest is None:
        return "NO_CHANNEL"
    if widest >= need:
        return "LAUNCHES_AT_CLASS"
    if floor is not None and widest >= floor:
        return "CLASS_FLOOR_OPENS"
    base = None
    if neck_min is not None and widest >= neck_min:
        base = "NECK_OPENS"
    elif widest >= board_min:
        base = "LICENCE_ONLY"
    if base is None:
        return "NO_CHANNEL"
    if price is not None and price["ok"] is False:
        return base + "_UNPRICED"
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=AUTHORITY)
    ap.add_argument("--net", action="append", default=[])
    ap.add_argument("--land", action="append", default=[],
                    help="restrict to these REF.PIN lands.  Repeatable")
    ap.add_argument("--grid", type=int, default=50000)
    ap.add_argument("--max-island", type=int, default=8,
                    help="skip the lands of an island holding more pads than "
                         "this.  An open edge is launched from the SMALL side: "
                         "a 200-land `GND` body is not a frontier and asking "
                         "it costs minutes to say so.  0 measures every land")
    ap.add_argument("--probe-mm", type=float, default=PROBE / M)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    for suffix in (".kicad_dru", ".kicad_pro"):
        if not a.board.with_suffix(suffix).is_file():
            raise SystemExit("--board %s has no %s beside it"
                             % (a.board, suffix))
    before = sha256(a.board)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    board_min = qb.b.GetDesignSettings().m_TrackMinWidth
    neck = mz.neck_rule(qb)

    fp_pos, fp_of = {}, {}
    for f in qb.b.GetFootprints():
        p = f.GetPosition()
        fp_pos[f.GetReference()] = (p.x, p.y)
        for pad in f.Pads():
            fp_of["%s.%s" % (f.GetReference(), pad.GetNumber())] = \
                f.GetReference()

    nets = a.net
    if not nets:
        nets = sorted({str(n.GetNetname()) for n in qb.b.GetNetInfo().NetsByNetcode().values()
                       if str(n.GetNetname())})
    rows, counts = [], {}
    for net in nets:
        try:
            c = net_contract(qb.b, net)
        except SystemExit:
            continue
        islands = mz.net_islands(qb, net)
        if len(islands) < 2 and not a.land:
            continue
        far = list(permitted_layers(qb.routable, c["layers"], reserved, net))
        floor = (DRU_CLASS.get(c["netclass"], {}) or {}).get("width")
        price = trunk_floor_price(c["netclass"], board_min)
        pads = [(i, p) for i, isl in enumerate(islands) for p in isl]
        skipped = 0
        if a.max_island:
            keep = {i for i, isl in enumerate(islands)
                    if len(isl) <= a.max_island}
            skipped = sum(1 for i, _ in pads if i not in keep)
            pads_asked = [(i, p) for i, p in pads if i in keep]
        else:
            pads_asked = pads
        # the toward-hint every land is offered: the nearest pad of another
        # island, which is the target `route_join` would aim at
        for i, pad in pads_asked:
            ref = pad["ref"]
            if a.land and ref not in a.land:
                continue
            others = [q for j, q in pads if j != i]
            if not others:
                continue
            tgt = min(others, key=lambda q: math.hypot(q["x"] - pad["x"],
                                                       q["y"] - pad["y"]))
            widest, rungs = widest_launch(qb, net, c, far, pad,
                                          (tgt["x"], tgt["y"]), G=a.grid)
            nk = None
            if neck is not None and neck.contains(pad["x"], pad["y"]):
                nk = neck.min_w
            narrow = (None if widest is None
                      else narrow_price(c["netclass"], widest))
            v = verdict_for(widest, c["width"], floor if price["admitted"]
                            else None, nk, board_min, narrow)
            chans = {}
            owner = fp_of.get(ref)
            for L in ("F", "B"):
                if L not in far or not pad.get(L) or owner is None:
                    continue
                ch = channel(qb, net, ref, pad, L, fp_pos[owner],
                             c["clr_pad"], c["clr"],
                             probe=int(round(a.probe_mm * M)))
                if ch:
                    chans[L] = ch
            # PACKAGE PITCH: the pinch is made by two pads OF THE LAND'S OWN
            # FOOTPRINT, and the class width does not fit between them.  No
            # router flag, no eviction and no rule area reaches this one: the
            # binder is the vendor land pattern, so the levers are a PART
            # CHANGE or a REFLOORPLAN and nothing else.
            def _own_pad(sd):
                return bool(sd and sd["kind"] == "pad" and sd["land"]
                            and sd["land"].split(".")[0] == owner)
            pitch_wall = any(
                _own_pad(ch["row"].get("lo")) and _own_pad(ch["row"].get("hi"))
                and ch["row"].get("admits_mm") is not None
                and ch["row"]["admits_mm"] * M < c["width"]
                for ch in chans.values())
            if pitch_wall and v.startswith(("LICENCE_ONLY", "NO_CHANNEL",
                                            "NECK_OPENS")):
                # The pitch wall is the STRONGER statement and it subsumes the
                # price: a width the vendor land pattern forbids cannot be
                # bought with a licence at any current.  `narrow_price` rides
                # in the row beside it so both facts survive.
                v = "PACKAGE_PITCH_WALL"
            counts[v] = counts.get(v, 0) + 1
            rows.append(dict(
                net=net, land=ref, island=i, footprint=owner,
                netclass=c["netclass"],
                netclass_width_mm=c["width"] / M,
                dru_class_floor_mm=None if floor is None else floor / M,
                class_floor_admitted=bool(price["admitted"]),
                class_floor_why=price["why"],
                neck_min_mm=None if nk is None else nk / M,
                board_min_track_mm=board_min / M,
                widest_launch_mm=None if widest is None else widest / M,
                narrow_price=narrow,
                ladder=rungs, channels=chans,
                target=tgt["ref"],
                body_lands_skipped=skipped,
                verdict=v))
            print(" %-34s %-9s widest=%-6s %s"
                  % (ref, c["netclass"],
                     "none" if widest is None else "%.3f" % (widest / M), v),
                  flush=True)

    after = sha256(a.board)
    doc = dict(
        schema=1, board=str(a.board), board_sha256=before,
        authoritative_unchanged=(before == after),
        board_is_authority=(a.board.resolve() == AUTHORITY.resolve()),
        grid_nm=a.grid, probe_mm=a.probe_mm, ladder_mm=[w / M for w in LADDER],
        max_island=a.max_island,
        question=("how wide a conductor does this land's EXIT CHANNEL admit, "
                  "which two objects bind it, and which of the widths this "
                  "board licenses would open it"),
        method=("read-only.  The ladder is the ROUTER's own "
                "`maze3d.pad_escapes` -- launch, pocket and off-centre "
                "sources -- so it cannot disagree with the gate.  The channel "
                "is EXACT geometry walked outward in %d um stations with no "
                "lattice; a track is its segment inflated by w/2, a via and a "
                "pad their bounding box.  The board's sha256 is re-read at "
                "exit" % (STEP // 1000)),
        counts=counts, rows=rows)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
