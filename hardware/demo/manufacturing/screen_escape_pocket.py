#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: is a land's ESCAPE POCKET sealed, or was it a raster?

D-631.  `screen_stitch_window.py` retired the 8.0 mm stitch window as the pour
block's binding constraint and left a sharper question in its place.  Every
`NO_BODY_VIA_SITE` island on this board reads `UNREACHABLE` -- no via-legal cell
of ANY kind is reachable from ANY of its escapes at ANY distance -- and the
reason is the same everywhere: the escape opens into a FREE POCKET of a few
hundred lattice cells that is sealed on its own layer.

    /01_POWER_TREE/BQ25185_SYS  C28.1      19 cells    C26.2   152
                                C27.1     166          R68.1   164
                                L4.1      429          SW9.2  1677 (206 via-legal)
                                L2.1  176085 (138810 via-legal)  <- NOT sealed
    +3V3                        R129.1     85          R39.1    72

Those are the numbers that make `UNREACHABLE` falsifiable rather than merely
disappointing: an escape into 176,085 free cells is a DISTANCE problem, and one
into 19 is a SEAL.

A SEAL AT 0.100 mm IS NOT YET A SEAL.  That is this board's most expensive
lesson, learned three times -- `BTN_DOWN_N` closed at 0.0333 mm, `EXT_SDA` at
0.025 mm, `LED_K` at 0.020 mm -- all after refusing at 0.100 mm.  A pocket whose
mouth is 0.08 mm wide is sealed on a 0.100 mm lattice and open on a 0.025 mm
one, and nothing in a cell count says which kind it is.

SO MEASURE THE POCKET IN MILLIMETRES, NOT IN CELLS.  Area is pitch-invariant:
a pocket that is genuinely sealed keeps its AREA as the lattice refines (the
cell count grows exactly as 1/G^2 and nothing else changes), and a pocket whose
seal was a rasterisation artifact GROWS in area the moment the lattice can
express its mouth.  The ratio is the verdict, and it costs one flood-fill per
(land, escape, pitch).

    area_mm2 flat across the ladder      -> SEALED.  A finer pitch buys nothing;
                                            this is placement or eviction.
    area_mm2 grows                       -> RASTER.   Ladder it; the mouth is
                                            narrower than the coarse pitch.

WHAT IS MEASURED, NOT ASSUMED

  * THE CONTRACT IS THE GATE'S -- `net_contract`, `permitted_layers`,
    `reserved_inner_planes`, `DRU_CLASS` floors, `--escape-floor`, `--guard`,
    exactly as `route_maze_batch.propose` assembles them.
  * THE POCKET IS `stitch_pad`'s OWN FREE SPACE, `~field.blk[L]`, flooded with
    `maze3d._shift_or` -- the same 8-connected dilation the stitch and the maze
    both use -- from the same `pad_escapes` launch points.
  * VIA-LEGAL CELLS INSIDE THE POCKET ARE COUNTED, because a pocket with a
    legal barrel site in it is not a wall at all whatever its size.
  * NOTHING IS WRITTEN.
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

PITCHES = (100000, 50000, 25000)

LAYER_NAME = {"F": "F.Cu", "I1": "In1.Cu", "I2": "In2.Cu", "I3": "In3.Cu",
              "I4": "In4.Cu", "B": "B.Cu"}


def _board_barrels_at(qb, net, x_nm, y_nm):
    """How many `PCB_VIA` objects THIS BOARD carries at that centre, on `net`.

    Same reason `screen_pair_corridor_blame.board_barrels_at` exists: `count`
    in a `--detour-spec` is a claim about KiCad's object list, and one
    `PCB_VIA` is fourteen router objects and two drills since D-646.  Counting
    the router's objects would emit `"count": 2` for copper the board has once
    and the applier would refuse the spec.
    """
    n = 0
    for t in qb.b.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        p = t.GetPosition()
        if int(p.x) == int(x_nm) and int(p.y) == int(y_nm):
            n += 1
    return n


def _units_intersecting(qb, net, box):
    """Foreign routed copper meeting `box`, grouped into PHYSICAL units.

    A unit is one `--detour-spec` entry: a track description with every exact
    duplicate this board carries (D-648's `count`), or a whole barrel -- annuli
    AND drill together, because a spec that took only the hole would leave the
    copper standing (D-653).  Membership is INTERSECTION, which is the
    difference between this and the corridor blame: a 2 mm box around a QFN
    land contains almost nothing and is CROSSED by exactly the copper that
    seals it.
    """
    def meets(o):
        a_, b_, c_, d_ = o.bbox(0)
        return not (c_ < box[0] or a_ > box[2] or d_ < box[1] or b_ > box[3])

    units = {}
    for L in qb.shapes:
        for s_ in qb.shapes[L]:
            if s_.net in (None, net) or s_.tag not in ("track", "via"):
                continue
            if not meets(s_):
                continue
            if s_.tag == "via":
                k = ("V", s_.net, int(s_.cx), int(s_.cy))
            else:
                k = ("T", s_.net, L, int(s_.x0), int(s_.y0),
                     int(s_.x1), int(s_.y1), int(s_.hw))
            units.setdefault(k, []).append(s_)
    for h in qb.holes:
        if h.net in (None, net) or not h.tag.startswith("via"):
            continue
        if not meets(h):
            continue
        units.setdefault(("V", h.net, int(h.cx), int(h.cy)), []).append(h)
    return units


def _unit_spec(qb, k, objs):
    """One unit as the `--detour-spec` entry that would remove it."""
    if k[0] == "V":
        dia = max([2 * o.hx for o in objs if o.tag == "via"] or [0])
        drill = max([2 * o.hx for o in objs if o.tag == "via/hole"] or [0])
        return dict(kind="barrel", net=k[1], router_objects=len(objs),
                    objects=len(objs),
                    count=_board_barrels_at(qb, k[1], k[2], k[3]),
                    at_mm=[round(k[2] / 1e6, 4), round(k[3] / 1e6, 4)],
                    dia_mm=round(dia / 1e6, 4), drill_mm=round(drill / 1e6, 4))
    return dict(kind="track", net=k[1], layer=LAYER_NAME.get(k[2], k[2]),
                router_objects=len(objs), objects=len(objs), count=len(objs),
                a_mm=[round(k[3] / 1e6, 4), round(k[4] / 1e6, 4)],
                b_mm=[round(k[5] / 1e6, 4), round(k[6] / 1e6, 4)],
                width_mm=round(2 * k[7] / 1e6, 4))


def pocket_blame(qb, mz, np, field, net, pad, G, cell_mm2, margin_mm,
                 measure):
    """WHICH foreign copper, held out, GROWS this land's escape pocket."""
    from screen_corridor_blockers import WithoutObjects

    M = 10 ** 6
    half = margin_mm * M
    x0, y0, x1, y1 = pad["x"] - half, pad["y"] - half, \
        pad["x"] + half, pad["y"] + half
    box = (x0, y0, x1, y1)
    units = _units_intersecting(qb, net, box)

    def area(objs):
        t0 = time.time()
        with WithoutObjects(qb, field, objs):
            n_es, cells, vok, lay = measure(field, pad, G)
        return dict(escapes=n_es, cells=cells,
                    area_mm2=round(cells * cell_mm2, 4),
                    via_legal_in_pocket=vok, layer=lay,
                    seconds=round(time.time() - t0, 1))

    base_es, base_cells, base_vok, base_lay = measure(field, pad, G)
    base = dict(escapes=base_es, cells=base_cells,
                area_mm2=round(base_cells * cell_mm2, 4),
                via_legal_in_pocket=base_vok, layer=base_lay)

    everything = [o for objs in units.values() for o in objs]
    rows = []
    out = dict(schema=1, grid_nm=G, margin_mm=margin_mm,
               box_mm=[round(v / M, 4) for v in box],
               base=base, units=len(units), objects=len(everything),
               nets=sorted({k[1] for k in units}), steps=rows)
    if not everything:
        out["verdict"] = "NO_FOREIGN_COPPER_IN_WINDOW"
        return out

    q1 = area(everything)
    rows.append(dict(step="Q1_ALL_OUT", **q1))
    grew = (q1["area_mm2"] > base["area_mm2"]
            or q1["via_legal_in_pocket"] > base["via_legal_in_pocket"]
            or q1["escapes"] > base["escapes"])
    if not grew:
        # THE WHOLE SEARCH IS RETIRED BY ONE FLOOD.  Every foreign object
        # within the window is gone and the land still opens into the same
        # pocket: what seals it is the land's own package, its own net, or the
        # board edge -- a PLACEMENT finding, and no `--evict` or
        # `--detour-spec` of any size touches it.
        out["verdict"] = "PLACEMENT_WALL"
        return out

    by_net = {}
    for k, objs in units.items():
        by_net.setdefault(k[1], []).extend(objs)
    for n_ in sorted(by_net):
        r = area(by_net[n_])
        rows.append(dict(step="Q2_NET_OUT", net=n_, **r))
        by_net[n_] = r

    openers = sorted(
        (n_ for n_, r in by_net.items()
         if r["area_mm2"] > base["area_mm2"]
         or r["via_legal_in_pocket"] > base["via_legal_in_pocket"]),
        key=lambda n_: (-by_net[n_]["area_mm2"], n_))
    out["single_net_openers"] = [
        dict(net=n_, area_mm2=by_net[n_]["area_mm2"],
             via_legal_in_pocket=by_net[n_]["via_legal_in_pocket"],
             escapes=by_net[n_]["escapes"]) for n_ in openers]

    # Q3 -- PER OBJECT, and only over the nets Q2 showed can matter.  A unit
    # sweep over every net in the window would price copper Q2 has already
    # proved is not the seal.
    pool = openers or sorted(by_net)
    per_unit = []
    for k in sorted(units, key=lambda k: (k[1], str(k))):
        if k[1] not in pool:
            continue
        r = area(units[k])
        spec = _unit_spec(qb, k, units[k])
        per_unit.append(dict(unit=spec, **r))
        rows.append(dict(step="Q3_UNIT_OUT", unit=spec, **r))
    per_unit.sort(key=lambda u: (-u["area_mm2"], -u["via_legal_in_pocket"]))
    out["per_unit"] = per_unit
    out["single_unit_openers"] = [
        u for u in per_unit
        if u["area_mm2"] > base["area_mm2"]
        or u["via_legal_in_pocket"] > base["via_legal_in_pocket"]]
    out["verdict"] = ("RIPUP_SINGLE_UNIT" if out["single_unit_openers"] else
                      "RIPUP_SINGLE_NET" if openers else
                      "RIPUP_SET_REQUIRED")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--guard", type=Path)
    ap.add_argument("--escape-floor", action="store_true")
    ap.add_argument("--neck", action="store_true")
    ap.add_argument("--stitch-via", default=None, metavar="DIA:DRILL")
    ap.add_argument("--escape-limit", type=int, default=12)
    ap.add_argument("--pitch", type=int, action="append", default=None)
    ap.add_argument("--orphans-only", action="store_true", default=True)
    # D-669: THE POCKET BLAME.  A SEALED verdict names no seal, and the only
    # instrument that could -- `screen_pair_corridor_blame.py` -- charges one
    # WHOLE-BOARD WAVEFRONT per candidate and takes hours.  For a land whose
    # escape opens into 0.03 mm2 that is the wrong price for the wrong
    # question: nothing a wavefront could discover about the far end matters
    # while the launch has nowhere to go.  A flood-fill costs seconds, so the
    # same reverse question -- WHICH copper, held out, GROWS this pocket -- is
    # answerable per NET and per OBJECT locally, in `--detour-spec` units.
    ap.add_argument("--blame", action="store_true",
                    help="for every land the ladder calls SEALED (or "
                         "NO_ESCAPE_AT_ANY_PITCH), name the foreign copper "
                         "whose removal GROWS the pocket -- all of it at once "
                         "(the upper bound), then each net alone, then each "
                         "physical object alone, in --detour-spec shape")
    ap.add_argument("--blame-margin-mm", type=float, default=2.0,
                    help="half-window around the land's own pad box that "
                         "bounds the blame pool (default 2.0 mm)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import numpy as np
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from screen_stitch_window import free_pocket
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN)

    pitches = tuple(sorted(set(a.pitch or PITCHES), reverse=True))
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    stitch_via = (tuple(int(v) for v in a.stitch_via.split(":"))
                  if a.stitch_via else None)

    out = []
    for net in a.nets:
        # D-669: A POCKET IS A POCKET WHETHER OR NOT THE NET OWNS A POUR.
        # This screen was written for the stitch's `NO_BODY_VIA_SITE` islands,
        # so it refused every plane-less net with `NO_PLANE` -- and the body
        # below never needed a plane: `net_islands` decomposes ANY net's copper,
        # `pad_escapes` launches off ANY land, and `free_pocket` floods
        # `~field.blk[L]` whatever fills it.  The question it answers -- does
        # this land's escape open into a pocket whose AREA holds as the lattice
        # refines (SEALED: placement or eviction) or grows (RASTER: ladder it)
        # -- is exactly the question a plane-less `NO_PATH` with one or two
        # escapes leaves open, and this board has fourteen of those.
        # `/SPI_B_SCK` `U9.30` is the one that bought it: `dst_escapes: 1`,
        # `NO_PATH` in 3.9 s, and nothing on this board could say whether that
        # single launch opens into 0.1 mm2 or into half a layer.
        # `has_plane` is now REPORTED, never a refusal.
        planed = bool(mz.has_plane(qb, net))
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        over = DRU_CLASS.get(c["netclass"], {})
        via_dia, via_drill = c["via_dia"], c["via_drill"]
        if stitch_via:
            via_drill = max(stitch_via[1], over.get("drill", 0))
            via_dia = max(stitch_via[0], via_drill + 2 * ANNULAR_MIN)
        floor = over.get("width") if a.escape_floor else None
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        body = max(islands, key=len)
        targets = [i for i in islands if i is not body]
        rec = dict(net=net, netclass=c["netclass"], has_plane=planed,
                   body=[p["ref"] for p in body], lands=[])
        per_land = {}
        def measure(field, pad, G):
            """(escapes, cells, via-legal cells, layer) of `pad`'s BEST pocket.

            Lifted out of the pitch loop unchanged so the blame below asks the
            SAME question of a board with copper held out that the ladder asked
            of the board as it stands.  A blame that measured differently from
            the verdict it is explaining would be answering about itself.
            """
            es = mz.pad_escapes(qb, field, pad, None, a.escape_limit)
            best = None
            for e in es:
                n, seen = free_pocket(mz, np, field, e)
                if n <= 0:
                    continue
                vok = int((seen & field.via_ok).sum())
                if best is None or n > best[0]:
                    best = (n, vok, e['layer'])
            return (len(es), best[0] if best else 0,
                    best[1] if best else 0, best[2] if best else None)

        for G in pitches:
            field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                             via_dia, via_drill, G=G, layers=layers,
                             neck=mz.neck_rule(qb) if a.neck else None,
                             guard=guard_for(spec, net) if spec else None,
                             escape_floor=floor)
            cell_mm2 = (G / 1e6) ** 2
            for island in targets:
                for pad in island:
                    key = pad["ref"]
                    t0 = time.time()
                    n_es, cells, vok, lay = measure(field, pad, G)
                    row = dict(grid_nm=G, escapes=n_es,
                               cells=cells,
                               area_mm2=round(cells * cell_mm2, 4),
                               via_legal_in_pocket=vok,
                               layer=lay,
                               seconds=round(time.time() - t0, 1))
                    per_land.setdefault(key, dict(
                        pad=key,
                        island=[p["ref"] for p in island],
                        rungs=[]))["rungs"].append(row)
                    print("  %-30s %-10s %.4f mm  esc=%-3d pocket=%9.3f mm2"
                          "  via-legal=%d"
                          % (net[-30:], key, G / 1e6, row["escapes"],
                             row["area_mm2"], row["via_legal_in_pocket"]),
                          file=sys.stderr, flush=True)
            del field
        for k in sorted(per_land):
            r = per_land[k]
            areas = [x["area_mm2"] for x in r["rungs"] if x["escapes"]]
            r["area_min_mm2"] = min(areas) if areas else None
            r["area_max_mm2"] = max(areas) if areas else None
            r["growth"] = (round(max(areas) / min(areas), 3)
                           if areas and min(areas) > 0 else None)
            r["verdict"] = ("NO_ESCAPE_AT_ANY_PITCH" if not areas else
                            "HAS_VIA_SITE" if any(
                                x["via_legal_in_pocket"]
                                for x in r["rungs"]) else
                            "RASTER" if r["growth"] and r["growth"] >= 2.0 else
                            "SEALED")
            rec["lands"].append(r)

        # ------------------------------------------------------------------ #
        # THE POCKET BLAME -- D-669
        #
        # The ladder above says SEALED and stops.  This says BY WHAT.  The pool
        # is every foreign routed object whose bounding box INTERSECTS a small
        # box around the land -- intersects, not contained, because the copper
        # that seals a 0.03 mm2 pocket is almost always a track PASSING the
        # land, which a containment test would never see and which
        # `--detour-spec` relays between its own two ends anyway.
        #
        # Q1  ALL of it out at once -- the UPPER BOUND.  A pocket that does not
        #     grow here is not opened by ANY local rip-up, which makes it a
        #     PLACEMENT finding and retires the whole search in one flood.
        # Q2  Each NET's objects alone.
        # Q3  Each PHYSICAL UNIT alone, emitted in `--detour-spec` shape.
        #
        # Every trial is a flood-fill, not a wavefront: seconds, not hours.
        if a.blame:
            want = [r for r in rec["lands"]
                    if r["verdict"] in ("SEALED", "NO_ESCAPE_AT_ANY_PITCH")]
            if want:
                G = min(pitches)
                cell_mm2 = (G / 1e6) ** 2
                field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                                 via_dia, via_drill, G=G, layers=layers,
                                 neck=mz.neck_rule(qb) if a.neck else None,
                                 guard=guard_for(spec, net) if spec else None,
                                 escape_floor=floor)
                pads = {p["ref"]: p for isl in islands for p in isl}
                for r in want:
                    pad = pads[r["pad"]]
                    r["blame"] = pocket_blame(
                        qb, mz, np, field, net, pad, G, cell_mm2,
                        a.blame_margin_mm, measure)
                del field
        out.append(rec)

    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        pitches=list(pitches), escape_floor=bool(a.escape_floor),
        neck=bool(a.neck),
        stitch_via=list(stitch_via) if stitch_via else None,
        guard=str(a.guard) if a.guard else None,
        guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                      if a.guard else None),
        question=("for every land whose escape opens into a free pocket, does "
                  "that pocket keep its AREA as the lattice refines -- a real "
                  "seal -- or grow, which would make it a rasterisation "
                  "artifact a finer pitch can open"),
        method=("read-only; maze3d._shift_or flood over ~field.blk[layer] from "
                "maze3d.pad_escapes launch points, at each pitch, on the same "
                "contract/guard/escape-floor route_maze_batch.propose builds; "
                "area in mm2 so the rungs are comparable"),
        nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
