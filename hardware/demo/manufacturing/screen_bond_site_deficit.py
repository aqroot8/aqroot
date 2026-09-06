#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: `NO_VIA_SITE` BY HOW MUCH?

D-625 taught this board that a bond refusal is two questions, not one: a pad
sitting on its own piece of POUR does not need to LAUNCH, it needs a BARREL
somewhere inside the copper it is already on, and `screen_bond_ladder.py` asks
both.  D-641 then priced `/09_COMMUNITY_HEADER/EXT_SDA` -> `J8.3`, the Qwiic /
STEMMA QT SDA contact, and found the whole edge resting on one word:

    U3.12 -- NO_VIA_SITE

**AND NOTHING SAID BY HOW MUCH.**  `NO_VIA_SITE` is a boolean, and a boolean
cannot be handed to a placement engineer.  "Give `U3.12` a via site" is not a
task until somebody says how much room is missing, where the least-blocked
point is, and which layer is the one that refuses -- and it cannot be CHECKED
after a part moves, because there is no number to compare.

So this screen turns the wall into a SPECIFICATION:

    for a named pad, on its own filled island -- or on the post-cut FRAGMENT a
    proposed route leaves it on -- what is the LARGEST through barrel that has
    a legal site there, and what is the DEFICIT against the board's own
    promotable via floor?

WHAT IS MEASURED, NOT ASSUMED

  * THE SITE TEST IS THE PROMOTER'S, IMPORTED AND NOT RE-DERIVED.
    `screen_bond_ladder.island_barrel` is called verbatim, so a site this
    screen counts is a site `bridge_islands` would plant, `pour_partition
    _contract.py` PP3 would call a bond, and `screen_bond_ladder.py` would
    report -- three instruments, one measurement, no drift.
  * THE FRAGMENT IS THE ONLY UNIT THAT PRICES A SEVERANCE.  D-625 measured
    that `/GND` `U3.12`'s island holds 1071 legal barrel sites at 0.025 mm and
    that ZERO of them are on `U3.12`'s side of the cut.  An island-wide count
    reads as available and is not.  `--fragment-board` is therefore how this
    screen is meant to be run whenever a route is what created the fragment.
  * THE LADDER GOES BELOW THE FLOOR ON PURPOSE, AND SAYS SO ON EVERY RUNG.
    A deficit is only meaningful if the ladder can reach the answer, so the
    diameters continue under board setup's `min_via_diameter` and
    `min_through_hole_diameter`.  Every rung carries `promotable`, computed
    from the project's own floors, and `headroom_mm` is reported twice --
    once for PROMOTABLE barrels and once for ANY barrel -- because
    "a 0.35 mm barrel would fit" and "a barrel this board may ship would fit"
    are different sentences and only the second one is copper.
  * THE BLAME IS PER LAYER AND IT IS THE VIA LATTICE'S OWN.  A through barrel
    is copper on all six layers and a hole through all of them, so
    `Field._via_grid` ANDs six masks and a hole-to-hole term.  This screen
    rebuilds those terms one at a time over the fragment's own cells and
    reports which of them is binding.  `In1.Cu` refusing an antipad and
    `B.Cu` refusing a neighbouring pin are different placement problems with
    different fixes, and `NO_VIA_SITE` says neither.
  * NOTHING IS WRITTEN.  The board file is untouched; the full-board gate
    remains the only thing that promotes copper.

    python3 screen_bond_site_deficit.py REF.NUM [REF.NUM ...]
        [--fragment-board POST.kicad_pcb] [--guard G.json] [--grid NM]
        [--dia NM ...] [-o OUT.json]
"""

import argparse
import collections
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# THE DIAMETER LADDER, LARGEST FIRST, IN NANOMETRES.  The first three rungs are
# `screen_bond_ladder.VIA_LADDER`'s own diameters so the two instruments meet on
# the same geometry; the rest descend past every floor this board publishes, for
# the reason in the doctrine above -- a deficit that the ladder cannot reach is
# not a deficit, it is another boolean.
DIA_LADDER = (600000, 500000, 450000, 400000, 350000, 300000,
              250000, 200000, 150000, 100000)
# THE DRILL THIS SCREEN PAIRS WITH A DIAMETER, AND WHY IT IS THE SMALLEST ONE.
# Copper exclusion is a function of the DIAMETER; hole-to-hole is a function of
# the DRILL.  This screen measures HEADROOM, so at every rung it spends the
# SMALLEST hole the project publishes (`min_through_hole_diameter`) rather than
# the widest the annular floor would allow -- a wider drill would refuse sites
# for a hole the barrel never had to have, and the deficit would be overstated.
# Below the diameter at which the 0.125 mm annular ring still fits around that
# hole, the drill becomes `dia - 2 * min_via_annular_width`, the rung is
# licence-only by construction, and a rung whose drill would reach zero ENDS
# the ladder and is reported as the ladder's own floor.  `screen_bond_ladder`'s
# clamp is still applied and still only ever RAISES.
ANNULAR_FLOOR_NOTE = ("the drill is the project's own min_through_hole_diameter "
                      "wherever the 0.125 mm annular ring fits around it, "
                      "because a wider drill would overstate the deficit")


def layer_blame(mz, qb, field, poly, dia, drill):
    """Which of the six copper layers -- or the drill -- refuses this fragment.

    `Field._via_grid` is an AND over six per-layer copper masks and one
    hole-to-hole term.  Rebuilding them separately over the fragment's own
    cells says WHICH one is binding, and how many cells each would leave.
    A cell blocked by `In1.Cu` alone is an antipad and a stackup question; a
    cell blocked by `B.Cu` alone is a neighbouring pin and a placement one.
    """
    import numpy as np
    if poly is None:
        return None
    cells = mz.poly_mask(field, poly)
    total = int(cells.sum())
    if not total:
        return dict(fragment_cells=0, note="no lattice cell falls inside "
                                           "this fragment at this pitch")
    per, free_each = {}, {}
    for L in qb.cu:
        bad = (qb.grid(L, field.net, dia, field.clr_pad, field.clr_trk,
                       field.ox, field.oy, field.x1, field.y1, field.G)
               | field.dru_overlay(L, dia))
        per[L] = bad
        free_each[L] = int((cells & ~bad).sum())
    holes = _hole_mask(np, mz, qb, field, drill)
    free_each["hole_to_hole"] = int((cells & ~holes).sum())
    # SOLE BLAME: cells that EVERY other term admits and this one alone refuses.
    sole = {}
    terms = dict(per)
    terms["hole_to_hole"] = holes
    for k in terms:
        others = np.zeros_like(cells)
        for j, m in terms.items():
            if j != k:
                others |= m
        sole[k] = int((cells & ~others & terms[k]).sum())
    # AND THE OBJECTS, BY NAME.  A layer is a place; a placement task needs a
    # THING.  For every term that SOLELY refuses cells the rest admit, the
    # obstacles within that term's own `QBoard.margin` of those cells are
    # counted, so the report can say "one `/09_COMMUNITY_HEADER/TCA4307_READY`
    # track on `In3.Cu`" instead of "In3.Cu".  Those cells are the cheapest
    # possible unlock: every other layer already admits them.
    named = {}
    for k, n in sole.items():
        if not n or k == "hole_to_hole":
            continue
        others = np.zeros_like(cells)
        for j, m in terms.items():
            if j != k:
                others |= m
        js, iss = np.nonzero(cells & ~others & terms[k])
        xs = field.ox + iss.astype(np.int64) * field.G
        ys = field.oy + js.astype(np.int64) * field.G
        obs = qb.obstacles(k, field.net)
        guard = field.G * 0.75
        hist = collections.Counter()
        for t in range(len(js)):
            x, y = float(xs[t]), float(ys[t])
            for sh in obs:
                need = qb.margin(sh, dia, field.clr_pad, field.clr_trk) + guard
                try:
                    if sh.dist(x, y) < need:
                        hist["%s|%s" % (getattr(sh, "net", None),
                                        getattr(sh, "tag", "?"))] += 1
                except Exception:
                    continue
        named[k] = dict(cells=int(n),
                        bbox_mm=[round(float(xs.min()) / 1e6, 3),
                                 round(float(ys.min()) / 1e6, 3),
                                 round(float(xs.max()) / 1e6, 3),
                                 round(float(ys.max()) / 1e6, 3)],
                        blockers=[dict(object=o, cells=c)
                                  for o, c in hist.most_common(6)])
    return dict(fragment_cells=total,
                cells_each_term_admits=free_each,
                cells_refused_by_this_term_alone=sole,
                sole_blame_objects=named,
                binding=sorted(free_each, key=lambda k: free_each[k])[0])


def _hole_mask(np, mz, qb, field, drill):
    """`_via_grid`'s hole-to-hole term, alone -- same formula, same guard band."""
    import math
    bad = np.zeros((field.ny, field.nx), dtype=bool)
    guard = field.G * 0.75
    XX = (field.ox + np.arange(field.nx) * field.G).astype(float)
    YY = (field.oy + np.arange(field.ny) * field.G).astype(float)
    for h in qb.holes:
        need = drill / 2.0 + h.r + mz.HOLE_CLR + guard
        i0 = max(0, int(math.floor((h.cx - need - field.ox) / field.G)))
        i1 = min(field.nx - 1, int(math.ceil((h.cx + need - field.ox) / field.G)))
        j0 = max(0, int(math.floor((h.cy - need - field.oy) / field.G)))
        j1 = min(field.ny - 1, int(math.ceil((h.cy + need - field.oy) / field.G)))
        if i1 < i0 or j1 < j0:
            continue
        X, Y = np.meshgrid(XX[i0:i1 + 1], YY[j0:j1 + 1])
        bad[j0:j1 + 1, i0:i1 + 1] |= (((X - h.cx) ** 2 + (Y - h.cy) ** 2)
                                      < need * need)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pads", nargs="+", metavar="REF.NUM")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--fragment-board", type=Path,
                    help="a POST board on which a proposed route has already "
                         "SEVERED this pad's island; the deficit is then "
                         "priced on the pad's OWN side of the cut, which is "
                         "the only side that bonds it")
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec to honour")
    ap.add_argument("--grid", type=int, default=25000,
                    help="lattice pitch in nm; the default is the finest rung "
                         "D-625 proved this board's bond question is "
                         "INVARIANT across, so a deficit measured here is not "
                         "a lattice artefact")
    ap.add_argument("--dia", action="append", type=int, default=[],
                    metavar="NM", help="diameter rungs instead of the built-in "
                                       "ladder, largest first")
    ap.add_argument("--blame-at", type=int, default=0, metavar="NM",
                    help="diameter the per-layer blame is taken at "
                         "(default: board setup's own min_via_diameter)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import numpy as np           # noqa: F401  (imported for the blame masks)
    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for,
                                  DRU_CLASS, ANNULAR_MIN, lattice_cells)
    from screen_bond_ladder import island_barrel, post_fragment

    sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
    from pour_partition_contract import reserved_plane_zones
    import pour_bond_guard as pg

    pro = a.board.with_suffix(".kicad_pro")
    setup = json.loads(pro.read_text())["board"]["design_settings"]["rules"]
    via_min = int(round(setup["min_via_diameter"] * 1e6))
    hole_min = int(round(setup["min_through_hole_diameter"] * 1e6))
    blame_at = a.blame_at or via_min

    planes, _reserved = reserved_plane_zones(a.board)
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = json.loads(a.guard.read_text()) if a.guard else None
    dias = list(a.dia) or list(DIA_LADDER)

    LK = {"F.Cu": "F", "B.Cu": "B", "In1.Cu": "I1", "In2.Cu": "I2",
          "In3.Cu": "I3", "In4.Cu": "I4"}
    ref = pcbnew.LoadBoard(str(a.board))
    owner, place = {}, {}
    for fp in ref.GetFootprints():
        for p in fp.Pads():
            key = "%s.%s" % (fp.GetReference(), p.GetNumber())
            if key in a.pads:
                owner[key] = p.GetNetname()
                c = p.GetCenter()
                cu = [ref.GetLayerName(l) for l in p.GetLayerSet().CuStack()]
                place[key] = dict(lkey=LK.get(cu[0] if cu else None),
                                  xy_mm=[round(c.x / 1e6, 4),
                                         round(c.y / 1e6, 4)],
                                  xy_nm=[int(c.x), int(c.y)],
                                  size_mm=[round(p.GetSizeX() / 1e6, 4),
                                           round(p.GetSizeY() / 1e6, 4)],
                                  layers=cu)
    del ref

    lat = lattice_cells(a.board, a.grid)
    results = []
    for pad_ref in a.pads:
        net = owner.get(pad_ref)
        if net is None:
            results.append(dict(pad=pad_ref, ok=False, reason="NO_SUCH_PAD"))
            continue
        qb = qr.QBoard(str(a.board))
        ir.inject_existing_via_obstacles(qb)
        reserved = reserved_inner_planes(qb.b)
        c0 = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c0["layers"], reserved, net)
        gd = guard_for(spec, net) if spec else None

        own_poly, own_area = None, None
        for lname, _idx, poly, area in mz.filled_islands(qb, net):
            if lname != place[pad_ref]["lkey"]:
                continue
            if poly.Contains(pcbnew.VECTOR2I(*place[pad_ref]["xy_nm"]), -1, 0):
                own_poly, own_area = poly, area
                break
        frag_poly, frag_area = (None, None)
        if a.fragment_board:
            frag_poly, frag_area = post_fragment(
                pcbnew, pg, a.fragment_board, net,
                place[pad_ref]["lkey"], pad_ref)

        rungs, seen, blame, ladder_floor = [], set(), None, None
        for dia in dias:
            drill = (hole_min if dia - hole_min >= 2 * ANNULAR_MIN
                     else dia - 2 * ANNULAR_MIN)
            if drill <= 0:
                # A barrel with no hole is not a barrel.  The ladder ends here
                # and SAYS SO, rather than reporting a zero-drill rung as a
                # measurement.
                ladder_floor = dict(dia_nm=dia, why="a %0.3f mm barrel cannot "
                                                    "carry a hole and the "
                                                    "0.125 mm annular ring at "
                                                    "once" % (dia / 1e6))
                break
            # The promoter's OWN clamp, so a rung can never name a barrel a
            # gated `--bond-via` would silently widen.  It only ever RAISES.
            d = max(drill, DRU_CLASS.get(c0["netclass"], {}).get("drill", 0))
            dd = max(dia, d + 2 * ANNULAR_MIN)
            if (dd, d) in seen:
                continue
            seen.add((dd, d))
            t0 = time.time()
            field = mz.Field(qb, net, c0["width"], c0["clr_pad"], c0["clr"],
                             dd, d, G=a.grid, layers=layers, guard=gd)
            isl = island_barrel(mz, pcbnew, field, own_poly, own_area,
                                place[pad_ref]["xy_nm"], planes.get(net, []),
                                frag_poly, frag_area)
            if blame is None and dd <= blame_at:
                blame = dict(at_dia_nm=dd, at_drill_nm=d,
                             fragment=layer_blame(mz, qb, field,
                                                  frag_poly or own_poly,
                                                  dd, d))
            del field
            rungs.append(dict(
                via_dia_nm=dd, via_drill_nm=d,
                via_mm=[round(dd / 1e6, 3), round(d / 1e6, 3)],
                promotable=bool(dd >= via_min and d >= hole_min
                                and dd - d >= 2 * ANNULAR_MIN),
                island_sites=isl.get("sites", 0),
                sites_in_fragment=isl.get("sites_in_fragment"),
                lands_on_reserved_plane=bool(isl.get(
                    "lands_on_reserved_planes")),
                nearest_site_mm=isl.get("nearest_mm"),
                nearest_site_xy_mm=isl.get("nearest_xy_mm"),
                fragment_site_xy_mm=(isl.get("fragment_sites_xy_mm")
                                     or [None])[0],
                reason=isl.get("reason"), seconds=round(time.time() - t0, 1)))
            print("  %-9s dia %.3f/%.3f %-13s island %5d  fragment %s"
                  % (pad_ref, dd / 1e6, d / 1e6,
                     "PROMOTABLE" if rungs[-1]["promotable"] else "licence-only",
                     rungs[-1]["island_sites"],
                     rungs[-1]["sites_in_fragment"]),
                  file=sys.stderr, flush=True)
        del qb

        # THE UNIT THE FRAGMENT IS JUDGED IN.  With a fragment board the count
        # that matters is the pad's OWN side of the cut; without one it is the
        # island, and the report says which was asked so the two can never be
        # quoted for each other.
        unit = "fragment" if frag_poly is not None else "island"
        def has(r):
            return (r["sites_in_fragment"] or 0) > 0 if unit == "fragment" \
                else r["island_sites"] > 0
        any_rung = next((r for r in rungs if has(r)), None)
        pro_rung = next((r for r in rungs if has(r) and r["promotable"]), None)
        results.append(dict(
            pad=pad_ref, net=net, unit=unit, placement=place[pad_ref],
            island_mm2=(None if own_area is None else round(own_area, 3)),
            fragment_mm2=frag_area,
            floor_mm=round(via_min / 1e6, 3),
            headroom_any_mm=(None if not any_rung
                             else round(any_rung["via_dia_nm"] / 1e6, 3)),
            headroom_promotable_mm=(None if not pro_rung else
                                    round(pro_rung["via_dia_nm"] / 1e6, 3)),
            deficit_mm=(None if not any_rung else
                         max(0.0, round((via_min - any_rung["via_dia_nm"])
                                        / 1e6, 3))),
            ladder_floor=ladder_floor,
            verdict=("BONDABLE" if pro_rung else
                     "LICENCE_WOULD_BUY_IT" if any_rung else
                     "NO_BARREL_AT_ANY_DIAMETER_ON_THIS_LADDER"),
            best_site_xy_mm=(None if not any_rung else
                             (any_rung["fragment_site_xy_mm"] if unit ==
                              "fragment" else any_rung["nearest_site_xy_mm"])),
            blame=blame, rungs=rungs))

    doc = dict(schema=1, board=str(a.board), board_sha256=board_sha,
               fragment_board=(str(a.fragment_board) if a.fragment_board
                               else None),
               fragment_board_sha256=(
                   hashlib.sha256(a.fragment_board.read_bytes()).hexdigest()
                   if a.fragment_board else None),
               guard=(str(a.guard) if a.guard else None),
               grid=a.grid, lattice=lat, dia_ladder=dias,
               drill_rule=ANNULAR_FLOOR_NOTE,
               board_floors=dict(min_via_diameter_nm=via_min,
                                 min_through_hole_diameter_nm=hole_min,
                                 annular_min_nm=ANNULAR_MIN),
               method="read-only; screen_bond_ladder.island_barrel over a "
                      "DIAMETER ladder, on the same Field, .kicad_dru overlay "
                      "and pour-bond guard a gated run builds",
               reading="`headroom_promotable_mm` is the largest barrel this "
                       "board may SHIP that has a legal site in the unit "
                       "named by `unit`; `headroom_any_mm` continues below "
                       "every published floor and is a measurement of what a "
                       "licence -- or a placement change -- would have to buy, "
                       "NOT promotable copper.  `deficit_mm` is the gap "
                       "against board setup's own min_via_diameter and is the "
                       "number a part move has to close.",
               authoritative_unchanged=(
                   hashlib.sha256(BOARD.read_bytes()).hexdigest() == board_sha
                   if a.board.resolve() == BOARD.resolve() else None),
               pads=results)
    if a.out:
        a.out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    for r in results:
        print("%-9s %-9s %s  headroom any %s / promotable %s  deficit %s mm"
              % (r.get("pad"), r.get("unit", "-"), r.get("verdict"),
                 r.get("headroom_any_mm"), r.get("headroom_promotable_mm"),
                 r.get("deficit_mm")), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
