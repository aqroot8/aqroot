#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: the LATTICE ladder, aimed at a BOND.

D-623 built a `--grid` ladder for the ROUTER and D-622 proved why one was
needed: the maze rasterises, `Field` adds a 0.75-CELL guard band on top of the
clearance, and the pitch in force is therefore part of what the proposer can
EXPRESS.  A refusal at 0.100 mm is not a property of the board.

**EVERY BOND SCREEN THIS PROJECT HAS EVER RUN USED `grid: 100000`.**
`screen_bond_stitch.py` defaults to it, D-604 through D-607 all report it, and
`/GND` `U3.12` has come back `NO_VIA_SITE -- no legal 0.60 mm barrel within
8.0 mm of any escape` in every one of them.  That sentence is a statement about
a 0.100 mm lattice, not about the pocket: `Field.via_ok` marks a site legal
only where the barrel plus `clr + 0.75*G` fits, so at 0.100 mm a 0.600 mm
barrel is being asked for 0.075 mm of guard band it does not owe, and at
0.025 mm for 0.019 mm.  Whether that difference decides `U3.12` is a
measurement nobody had taken.

So this screen asks the bond question the way D-623 taught the routing question
to be asked -- over a LADDER, bounded in cells, with the rung that ran out of
budget kept in the report:

    for a NAMED pad, over pitches x barrels, can `maze3d.stitch_pad` give it
    its own escape, its own short run and its own through barrel?

WHAT IS MEASURED, NOT ASSUMED

  * THE EMITTER IS THE PROMOTER'S.  `maze3d.bond_pads` is exactly what a gated
    `route_maze_batch.py --bond-pad` transaction runs, at the same contract and
    the same `.kicad_dru` overlay, so a cell reported BONDED here names a
    transaction the gate would actually be offered.
  * A BARREL IS PROMOTABLE OR IT IS A SCREEN RESULT, AND THE REPORT SAYS
    WHICH.  A via under board setup's `min_via_diameter` is legal on this board
    ONLY inside a `.kicad_dru` rule area that names it, `bond_pads` carries no
    licence machinery, and gate clause 6 would refuse the run.  Every rung
    carries `promotable`, computed from the board's own floors, so a finding
    can never be quoted as promotable copper it is not.
  * THE BUDGET IS COUNTED IN CELLS, for D-623's reason -- halving the pitch
    QUADRUPLES the raster -- and the first rung over it ENDS the ladder and
    STAYS IN THE REPORT marked `over_budget`.
  * THE GUARD IS HONOURED WHEN GIVEN.  Foreign tubes bind a bond exactly as
    they bind any other copper; the net's own tubes do not, because the tube IS
    its copper (`guard_for`).
  * NOTHING IS WRITTEN.  Every stitch is reverted, the board is loaded once per
    rung and dropped.  The full-board gate remains the only thing that promotes.

TWO ROADS, BECAUSE `stitch_pad` IS NOT THE ONLY ONE.  `maze3d`'s own
doctrine block above `bridge_islands` says it plainly: a stitch asks a pad to
LAUNCH -- an escape, a short run, a barrel -- and that is the only way off a
pad sitting on BARE LAMINATE and the WRONG primitive for a pad sitting on its
own piece of POUR, where the copper is already there and an island is a
two-dimensional conductor.  A pad that a pour-bond guard tube protects is by
construction the second kind.  So every rung here also asks the BRIDGE
question:

    is there a legal through-barrel site anywhere inside THIS pad's own
    filled island, and does that site land inside the net's filled copper on
    a RESERVED INNER PLANE?

which needs no escape and no run at all.  A `NO_VIA_SITE` from the stitch and
a site from the island probe are not a contradiction -- they are two different
questions, and reporting only the first is how a bondable pad reads as a wall.
The landing test is the one `pour_partition_contract.py` PP3 uses to price a
fragment, so a site reported here is a site that would make PP3 say `BONDED`.

WHAT IT FOUND ON THE PAD IT WAS BUILT FOR, D-625.  `/GND` `U3.12`:
`stitch_pad` returns `NO_VIA_SITE` in ALL FIFTEEN (pitch x barrel) cells --
**INVARIANT across a 4x pitch range**, so that refusal is not a lattice
artefact -- while the same pad's own island holds 5 sites at 0.100 mm /
0.60-0.30 rising to **1071** at 0.025 mm / 0.45-0.20, every one landing in
BOTH `In1.Cu` and `In4.Cu`.  The pocket was never barren; the PRIMITIVE was
wrong.  And `sites_in_fragment` is **0 in every cell**: the cut puts every
legal barrel of that island on the OTHER pad's side, so the bond D-624 asked
for is not hard, it is EMPTY.  An island-wide site count would have reported
it as available.

    python3 screen_bond_ladder.py REF.NUM [REF.NUM ...] [--guard G.json]
        [--via DIA:DRILL ...] [--grid-cells N] [--max-mm MM] [-o OUT.json]
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

# The barrel ladder, LARGEST FIRST.  A bigger barrel is the more robust bond
# and the one that needs no licence, so it must be tried first and reported
# first; the finer rungs exist to say what a licence would BUY, which is a
# different question from what this board already grants.
#
#   0.60/0.30  the GND netclass via -- what every prior screen asked for
#   0.50/0.25  board setup's `min_via_diameter` with the 0.125 mm annular ring
#              spent exactly.  THE FINEST PROMOTABLE BARREL ON THIS BOARD.
#   0.45/0.20  D-601's licensed rung
#   0.35/0.20  the fine-pitch escape barrel the `.kicad_dru` already names in
#              six places (D-257 / D-266 / D-531)
VIA_LADDER = ((600000, 300000), (500000, 250000), (450000, 200000),
              (350000, 200000))


def post_fragment(pcbnew, pg, path, net, lkey, pad_ref):
    """The island of `net` on `lkey` that carries `pad_ref` on a POST board."""
    board = pcbnew.LoadBoard(str(path))
    for pour in pg.read_pours(board):
        if pour["net"] != net or pour["lkey"] != lkey:
            continue
        pg.assign(board, pour)
        for e in pour["islands"]:
            if pad_ref in [q["ref"] for q in e["pads"]]:
                return e["poly"], round(e["area_mm2"], 3)
    return None, None


def island_barrel(mz, pcbnew, field, poly, area, pad_xy_nm, planes,
                  frag_poly=None, frag_area=None):
    """THE BRIDGE QUESTION: a legal barrel INSIDE this pad's own island.

    `poly` is the pad's own filled island on the pad's own layer.  The answer
    is the cells of `field.via_ok` that lie inside it, and -- for the nearest
    one to the pad -- whether a through barrel there would land inside the
    net's filled copper on a RESERVED INNER PLANE, which is exactly the test
    `pour_partition_contract.py` PP3 applies when it prices a fragment.
    """
    import numpy as np
    if poly is None:
        return dict(ok=False, reason="NO_OWN_ISLAND")
    mask = mz.poly_mask(field, poly) & field.via_ok
    n = int(mask.sum())
    if not n:
        return dict(ok=False, reason="NO_SITE_IN_ISLAND",
                    island_mm2=round(area, 3), sites=0,
                    sites_in_fragment=(0 if frag_poly is not None else None))
    js, iss = np.nonzero(mask)
    xs = field.ox + iss.astype(np.int64) * field.G
    ys = field.oy + js.astype(np.int64) * field.G
    dx = xs - int(pad_xy_nm[0])
    dy = ys - int(pad_xy_nm[1])
    k = int(np.argmin(dx * dx + dy * dy))
    x, y = int(xs[k]), int(ys[k])
    pt = pcbnew.VECTOR2I(x, y)
    hits = [dict(layer=ln, zone=zn, area_mm2=ar)
            for (ln, zn, pl, ar) in planes if pl.Contains(pt, -1, 0)]
    out = dict(ok=bool(hits), sites=n, island_mm2=round(area, 3),
               nearest_xy_mm=[round(x / 1e6, 4), round(y / 1e6, 4)],
               nearest_mm=round(float(np.hypot(dx[k], dy[k])) / 1e6, 3),
               lands_on_reserved_planes=hits,
               sites_xy_mm=[[round(int(xs[t]) / 1e6, 3),
                             round(int(ys[t]) / 1e6, 3)]
                            for t in range(min(n, 60))],
               reason=None if hits else "SITE_LANDS_ON_NO_RESERVED_PLANE")
    if frag_poly is not None:
        inside = [t for t in range(n)
                  if frag_poly.Contains(pcbnew.VECTOR2I(int(xs[t]),
                                                        int(ys[t])), -1, 0)]
        out["fragment_mm2"] = frag_area
        out["sites_in_fragment"] = len(inside)
        out["fragment_sites_xy_mm"] = [[round(int(xs[t]) / 1e6, 3),
                                        round(int(ys[t]) / 1e6, 3)]
                                       for t in inside[:20]]
        # THE ONLY COUNT THAT PRICES THE SEVERANCE.  A site on the far side of
        # the cut bonds the pad that did not need bonding.
        out["ok"] = bool(hits) and bool(inside)
        if not inside:
            out["reason"] = "NO_SITE_ON_THIS_PAD_S_SIDE_OF_THE_CUT"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pads", nargs="+", metavar="REF.NUM")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--guard", type=Path,
                    help="a pour-bond guard spec to honour (foreign tubes "
                         "bind; the net's own do not)")
    ap.add_argument("--via", action="append", default=[], metavar="DIA:DRILL",
                    help="nm barrel rungs to try instead of the built-in "
                         "ladder, largest first")
    ap.add_argument("--grid", action="append", type=int, default=[],
                    metavar="NM", help="pitch rungs to try instead of "
                                       "route_maze_batch.LADDER_PITCHES")
    ap.add_argument("--grid-cells", type=int, default=80000000,
                    help="cell budget; the first rung over it ends the ladder "
                         "and stays in the report marked over_budget")
    ap.add_argument("--max-mm", type=float, default=8.0,
                    help="stitch_pad's own locality window")
    ap.add_argument("--fragment-board", type=Path,
                    help="a POST board on which a proposed route has already "
                         "SEVERED this pad's island.  D-624 asked for a bond "
                         "priced ON THE FRAGMENT THE ROUTE CREATES, and an "
                         "island-wide site count cannot answer that: a barrel "
                         "on the far side of the cut bonds the pad that did "
                         "NOT need it.  With this, every site is also tested "
                         "for containment in the pad's OWN post-cut fragment, "
                         "and `sites_in_fragment` is the only count that "
                         "prices the severance")
    ap.add_argument("--stop-on-promotable", action="store_true",
                    help="end a pad's ladder at the first PROMOTABLE bond")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, DRU_CLASS,
                                  ANNULAR_MIN, LADDER_PITCHES, lattice_cells)

    # Board setup's own via floor, read from the project rather than assumed.
    pro = a.board.with_suffix(".kicad_pro")
    setup = json.loads(pro.read_text())["board"]["design_settings"]["rules"]
    via_min = int(round(setup["min_via_diameter"] * 1e6))
    hole_min = int(round(setup["min_through_hole_diameter"] * 1e6))

    # THE LANDING TEST IS PP3's OWN, imported rather than re-derived: a site
    # this screen calls a bond and a site the contract calls a bond must be
    # the same site, or the screen is measuring a different board.
    sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
    from pour_partition_contract import reserved_plane_zones
    import pour_bond_guard as pg
    planes, _reserved = reserved_plane_zones(a.board)

    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = json.loads(a.guard.read_text()) if a.guard else None

    vias = [tuple(int(v) for v in s.split(":")) for s in a.via] or \
        list(VIA_LADDER)
    pitches = list(a.grid) or list(LADDER_PITCHES)

    # Which pad belongs to which net -- read off the board, never guessed.
    import pcbnew
    ref = pcbnew.LoadBoard(str(a.board))
    owner, place = {}, {}
    for fp in ref.GetFootprints():
        for p in fp.Pads():
            key = "%s.%s" % (fp.GetReference(), p.GetNumber())
            if key in a.pads:
                owner[key] = p.GetNetname()
                c = p.GetCenter()
                # THE LAYER IS THE PAD'S COPPER STACK, NOT `GetLayer()`.  On a
                # flipped footprint `GetLayer()` still reads `F.Cu` for an SMD
                # pad that is physically on `B.Cu`, and every geometric
                # question below -- which filled island contains this pad --
                # is asked on the wrong side if that is believed.
                cu = [ref.GetLayerName(l) for l in p.GetLayerSet().CuStack()]
                # `maze3d.filled_islands` keys layers by `qrouter.LNAME`
                # ("B"), not by KiCad's layer NAME ("B.Cu").  Comparing the two
                # matches nothing and reads as "this pad owns no island".
                place[key] = dict(lkey={"F.Cu": "F", "B.Cu": "B",
                                        "In1.Cu": "I1", "In2.Cu": "I2",
                                        "In3.Cu": "I3",
                                        "In4.Cu": "I4"}.get(cu[0] if cu
                                                            else None),
                                  xy_mm=[round(c.x / 1e6, 4),
                                         round(c.y / 1e6, 4)],
                                  xy_nm=[int(c.x), int(c.y)],
                                  size_mm=[round(p.GetSizeX() / 1e6, 4),
                                           round(p.GetSizeY() / 1e6, 4)],
                                  layers=cu, layer=cu[0] if cu else None)
    del ref
    missing = [p for p in a.pads if p not in owner]

    rungs = []
    for g in pitches:
        row = lattice_cells(a.board, g)
        row["over_budget"] = row["cells"] > a.grid_cells
        rungs.append(row)
        if row["over_budget"]:
            break

    results = []
    for pad_ref in a.pads:
        net = owner.get(pad_ref)
        if net is None:
            results.append(dict(pad=pad_ref, ok=False, reason="NO_SUCH_PAD"))
            continue
        cells, found = [], None
        for row in rungs:
            if row["over_budget"]:
                cells.append(dict(grid_nm=row["grid_nm"],
                                  grid_mm=row["grid_mm"], cells=row["cells"],
                                  ran=False, reason="OVER_CELL_BUDGET"))
                break
            qb = qr.QBoard(str(a.board))
            ir.inject_existing_via_obstacles(qb)
            reserved = reserved_inner_planes(qb.b)
            c0 = net_contract(qb.b, net)
            layers = permitted_layers(qb.routable, c0["layers"], reserved, net)
            gd = guard_for(spec, net) if spec else None
            # The pad's OWN filled island, resolved by geometry once per rung.
            own_poly, own_area = None, None
            for lname, _idx, poly, area in mz.filled_islands(qb, net):
                if lname != place[pad_ref]["lkey"]:
                    continue
                pt = pcbnew.VECTOR2I(int(place[pad_ref]["xy_nm"][0]),
                                     int(place[pad_ref]["xy_nm"][1]))
                if poly.Contains(pt, -1, 0):
                    own_poly, own_area = poly, area
                    break
            frag_poly, frag_area = (None, None)
            if a.fragment_board:
                frag_poly, frag_area = post_fragment(
                    pcbnew, pg, a.fragment_board, net,
                    place[pad_ref]["lkey"], pad_ref)
            seen_rungs = set()
            for dia, drill in vias:
                # THE SAME CLAMP THE PROMOTER APPLIES, so a rung here can
                # never name a barrel `route_maze_batch --bond-via` would
                # silently widen.
                d = max(drill, DRU_CLASS.get(c0["netclass"], {}).get("drill", 0))
                dd = max(dia, d + 2 * ANNULAR_MIN)
                # TWO REQUESTS THAT CLAMP TO ONE BARREL ARE ONE RUNG.  The
                # 0.125 mm annular floor takes 0.35/0.20 to 0.45/0.20, which is
                # already the rung above it; reporting it twice would read as
                # two measurements of two geometries.
                if (dd, d) in seen_rungs:
                    continue
                seen_rungs.add((dd, d))
                t0 = time.time()
                field = mz.Field(qb, net, c0["width"], c0["clr_pad"],
                                 c0["clr"], dd, d, G=row["grid_nm"],
                                 layers=layers, guard=gd)
                m = qb.mark()
                r = mz.bond_pads(qb, net, field, [pad_ref], max_mm=a.max_mm)
                qb.revert(m)
                # ASKED ON THE UNMUTATED BOARD, like the stitch: the revert is
                # above, so neither road is measured against the other's copper.
                island = island_barrel(mz, pcbnew, field, own_poly, own_area,
                                       place[pad_ref]["xy_nm"],
                                       planes.get(net, []),
                                       frag_poly, frag_area)
                del field
                bond = (r.get("bonds") or [None])[0]
                fail = (r.get("failures") or [None])[0]
                promotable = (dd >= via_min and d >= hole_min
                              and dd - d >= 2 * ANNULAR_MIN)
                cell = dict(grid_nm=row["grid_nm"], grid_mm=row["grid_mm"],
                            cells=row["cells"], ran=True,
                            via_dia_nm=dd, via_drill_nm=d,
                            via_mm=[round(dd / 1e6, 3), round(d / 1e6, 3)],
                            promotable=bool(promotable),
                            ok=bool(r.get("ok")),
                            seconds=round(time.time() - t0, 1))
                if bond:
                    cell.update(mm=bond.get("mm"), via_xy=bond.get("via_xy"),
                                escape=bond.get("escape"),
                                layer=bond.get("layer"))
                if fail:
                    cell.update(reason=fail.get("reason"),
                                why=str(fail.get("why"))[:200])
                cell["island_barrel"] = island
                cells.append(cell)
                print("  %-9s G=%.4f mm via %.2f/%.2f %-7s %s %s"
                      % (pad_ref, row["grid_mm"], dd / 1e6, d / 1e6,
                         "BOND" if cell["ok"] else "wall",
                         "PROMOTABLE" if promotable else "licence-only",
                         cell.get("reason") or ("%s mm" % cell.get("mm"))),
                      file=sys.stderr, flush=True)
                if cell["ok"] and found is None and (promotable
                                                     or not a.stop_on_promotable):
                    found = cell
                if cell["ok"] and promotable and a.stop_on_promotable:
                    break
            del qb
            if found is not None and a.stop_on_promotable \
                    and found.get("promotable"):
                break
        best = None
        won = [c for c in cells if c.get("ok")]
        promo = [c for c in won if c.get("promotable")]
        if promo:
            # COARSEST pitch, then LARGEST barrel: the cheapest search that
            # expresses the bond, and the most robust barrel it admits.
            best = sorted(promo, key=lambda c: (-c["grid_nm"],
                                                -c["via_dia_nm"]))[0]
        verdict = ("BONDABLE" if promo else
                   "LICENCE_ONLY" if won else
                   "NO_BOND_IN_BUDGET")
        results.append(dict(pad=pad_ref, net=net, placement=place[pad_ref],
                            verdict=verdict, best=best,
                            bonded_rungs=len(won),
                            promotable_rungs=len(promo), cells=cells))

    doc = dict(schema=1, board=str(a.board), board_sha256=board_sha,
               guard=str(a.guard) if a.guard else None,
               guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                             if a.guard else None),
               cell_budget=a.grid_cells, max_mm=a.max_mm,
               via_ladder=[[d, k] for d, k in vias],
               pitch_ladder=[r["grid_nm"] for r in rungs],
               board_floors=dict(min_via_diameter_nm=via_min,
                                 min_through_hole_nm=hole_min,
                                 annular_min_nm=ANNULAR_MIN),
               missing_pads=missing, pads=results,
               reading="A cell is PROMOTABLE only where the barrel clears "
                       "board setup's own min_via_diameter / "
                       "min_through_hole_diameter and the 0.125 mm annular "
                       "floor.  Anything finer is legal on this board only "
                       "inside a .kicad_dru rule area that names it, which "
                       "`bond_pads` cannot author -- so a LICENCE_ONLY verdict "
                       "is a measurement of what a licence would buy and is "
                       "NOT promotable copper.  `island_barrel` is the BRIDGE "
                       "question asked of the same pad: a legal barrel site "
                       "inside its OWN filled island, landing inside the net's "
                       "copper on a reserved inner plane -- no escape, no run.")
    out = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.out:
        a.out.write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)
    return 0 if all(r.get("verdict") == "BONDABLE" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
