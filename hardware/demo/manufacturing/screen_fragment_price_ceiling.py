#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what is the BEST price ANY barrel could buy this
fragment, and is the thing that refuses it LEGALITY or COPPER?

D-643 gave `PP2` a bar for a return fragment and D-642 gave `NO_VIA_SITE` a
number.  Between them they answer two thirds of one inequality:

    PP2 admits a split when  min(barrels in parallel,
                                 the FRAGMENT'S OWN COPPER pad -> barrel)
                             >=  the bar the board publishes for that net

`screen_bond_site_deficit.py` answers WHERE a barrel may go.  D-628/D-643
answer WHAT THE BAR IS.  Nobody had ever asked the third question -- WHAT A
BARREL THERE WOULD BE WORTH -- and on this board that omission is decisive.
`U3.12`'s `EXT_SDA` fragment takes no barrel at any diameter because ONE
`In3.Cu` signal track lies across its only pocket (D-642 sect. 3-4), and D-643
ranked relaying that track its second item on the grounds that "a barrel there
is the ONLY thing between `EXT_SDA` and the Qwiic connector".  Move the track
and the sites appear exactly as predicted -- and every one of them prices the
fragment at **0.602 A against its own 1.000 A bar**, because the fragment's own
copper necks to 0.150 mm on the way there.  The relay is a real transaction
that buys a real via site and closes NOTHING.

THE CEILING IS A PROPERTY OF THE COPPER, NOT OF THE SEARCH.  `bond_price`
takes the WIDEST path from each pad to a landing barrel and prices its
bottleneck, so for a fixed fragment the internal term is bounded by geometry
alone: no finer lattice, no smaller barrel, no eviction and no placement move
can raise it.  Sampling the fragment's own cells and pricing a hypothetical
barrel at each therefore bounds what ANY barrel could ever be worth -- and it
costs one geodesic per cell, against a gate run per guess.

SO THE SCREEN REPORTS TWO NUMBERS AND THE DIFFERENCE BETWEEN THEM IS THE
ACTIONABLE PART:

  * `ceiling_amps` -- the best price over EVERY cell of the fragment, legal or
    not.  Below the bar, the fragment is refused by its own copper and NOTHING
    a router or a placement engineer can do will admit it.
  * `best_legal_amps` -- the best price over the cells a barrel may actually
    occupy, taken from the SAME `Field.via_ok` lattice
    `screen_bond_site_deficit.py` and `screen_bond_ladder.island_barrel` count
    sites on, so the two instruments cannot disagree about what a site is.

    ceiling  <  bar                     REFUSED_BY_FRAGMENT_COPPER
                                        -- do not buy a via site; it is worthless
    best_legal < bar <= ceiling         PRICE_IS_HELD_BY_LEGALITY
                                        -- an eviction/relay/placement move CAN pay,
                                           and this names the cells worth buying
    best_legal >= bar                   PRICED_ABOVE_THE_BAR

The price and the bar are both taken from `checks/pour_partition_contract.py`
VERBATIM -- `bond_price`, `return_fragment_bar`, `decide` -- so this screen and
the contract that judges a promotion cannot drift apart.  This screen never
admits anything: `PP2` remains the only thing that admits or refuses a split.
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


def sample_cells(pcbnew, poly, step_nm):
    """Every lattice point of `poly`'s bounding box that lies inside it."""
    b = poly.BBox()
    out = []
    y = b.GetTop()
    while y <= b.GetBottom():
        x = b.GetLeft()
        while x <= b.GetRight():
            if poly.Contains(pcbnew.VECTOR2I(int(x), int(y)), -1, 0):
                out.append((int(x), int(y)))
            x += step_nm
        y += step_nm
    return out


def price_at(pp, planes, isl, drills, net, xy, drill_nm):
    """`pour_partition_contract.bond_price` with ONE hypothetical barrel."""
    x, y = int(xy[0]), int(xy[1])
    hypo = dict(isl)
    hypo["vias"] = list(isl["vias"]) + [dict(x=x, y=y, r=drill_nm // 2)]
    d2 = dict(drills)
    d2[(x, y)] = int(drill_nm)
    return pp.bond_price(net, hypo, planes, d2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pads", nargs="+", metavar="REF.NUM")
    ap.add_argument("--board", type=Path, default=BOARD,
                    help="the board the LATTICE and the obstacles are read "
                         "from -- what a barrel may legally occupy")
    ap.add_argument("--fragment-board", type=Path, required=True,
                    help="a POST board on which a proposed route has already "
                         "SEVERED this pad's island; the fragment priced is "
                         "the pad's OWN side of the cut")
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec to honour")
    ap.add_argument("--grid", type=int, default=50000,
                    help="lattice pitch in nm for the LEGALITY question")
    ap.add_argument("--step-mm", type=float, default=0.25,
                    help="sampling pitch for the CEILING question; the "
                         "legal cells are always priced exactly, whatever "
                         "this is")
    ap.add_argument("--dia", type=int, default=0, metavar="NM",
                    help="barrel diameter to price (default: board setup's "
                         "own min_via_diameter, clamped up by the net's "
                         "own .kicad_dru class drill)")
    ap.add_argument("--max-legal", type=int, default=0, metavar="N",
                    help="price at most this many legal sites (0 = all)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import numpy as np                                        # noqa: F401
    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for,
                                  DRU_CLASS, ANNULAR_MIN)
    from screen_bond_ladder import post_fragment

    sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
    import pour_partition_contract as pp

    pro = a.board.with_suffix(".kicad_pro")
    setup = json.loads(pro.read_text())["board"]["design_settings"]["rules"]
    via_min = int(round(setup["min_via_diameter"] * 1e6))
    hole_min = int(round(setup["min_through_hole_diameter"] * 1e6))

    # ---- the BAR and the FRAGMENT, both read from the POST board ---------- #
    planes, reserved = pp.reserved_plane_zones(a.fragment_board)
    geom, drills = pp.pour_geometry(a.fragment_board)
    netclass_of, pads_by_fp = pp.board_nets_and_pads(a.fragment_board)
    dru = a.fragment_board.with_suffix(".kicad_dru")
    if not dru.exists():
        dru = a.board.with_suffix(".kicad_dru")
    table, table_src = pp.published_rail_currents(dru)
    fpro = a.fragment_board.with_suffix(".kicad_pro")
    classes, class_src = pp.netclass_conductors(fpro if fpro.exists() else pro)
    returns = pp.return_nets(planes, reserved, netclass_of, table)

    LK = {"F.Cu": "F", "B.Cu": "B", "In1.Cu": "I1", "In2.Cu": "I2",
          "In3.Cu": "I3", "In4.Cu": "I4"}
    ref = pcbnew.LoadBoard(str(a.board))
    place, owner = {}, {}
    for fp in ref.GetFootprints():
        for p in fp.Pads():
            key = "%s.%s" % (fp.GetReference(), p.GetNumber())
            if key in a.pads:
                owner[key] = p.GetNetname()
                c = p.GetCenter()
                cu = [ref.GetLayerName(l) for l in p.GetLayerSet().CuStack()]
                place[key] = dict(lkey=LK.get(cu[0] if cu else None),
                                  xy_nm=[int(c.x), int(c.y)],
                                  xy_mm=[round(c.x / 1e6, 4),
                                         round(c.y / 1e6, 4)])
    del ref

    spec = json.loads(a.guard.read_text()) if a.guard else None
    step_nm = int(round(a.step_mm * 1e6))
    results = []
    for pad_ref in a.pads:
        net = owner.get(pad_ref)
        if net is None:
            results.append(dict(pad=pad_ref, ok=False, reason="NO_SUCH_PAD"))
            continue
        frag_poly, frag_area = post_fragment(pcbnew, __import__(
            "pour_bond_guard"), a.fragment_board, net,
            place[pad_ref]["lkey"], pad_ref)
        if frag_poly is None:
            results.append(dict(pad=pad_ref, ok=False,
                                reason="NO_FRAGMENT_ON_THE_POST_BOARD"))
            continue
        # the fragment as `pour_partition_contract` itself reads it -- the
        # edge soup `bond_price` measures the internal tube through
        key = next((k for k in geom
                    if k.startswith("%s|%s|" % (net, place[pad_ref]["lkey"]))),
                   None)
        isl = None
        if key is not None:
            isl = next((i for i in geom[key].values()
                        if any(q["ref"] == pad_ref for q in i["pads"])), None)
        if isl is None:
            results.append(dict(pad=pad_ref, ok=False,
                                reason="FRAGMENT_GEOMETRY_UNREADABLE"))
            continue

        # ---- the bar, exactly as `compare()` resolves it ------------------ #
        board = pcbnew.LoadBoard(str(a.fragment_board))
        n = board.FindNet(net)
        cls = n.GetNetClassName() if n else None
        del board
        row = table.get(cls)
        required, prov = (row["amps"] if row else None), None
        if required is None and net in returns:
            required, prov = pp.return_fragment_bar(
                net, cls, sorted(q["ref"] for q in isl["pads"]),
                pads_by_fp, netclass_of, classes, table)

        # ---- the barrel this screen prices ------------------------------- #
        qb = qr.QBoard(str(a.board))
        ir.inject_existing_via_obstacles(qb)
        res_planes = reserved_inner_planes(qb.b)
        c0 = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c0["layers"], res_planes, net)
        gd = guard_for(spec, net) if spec else None
        drill = max(hole_min, DRU_CLASS.get(c0["netclass"], {}).get("drill", 0))
        dia = max(a.dia or via_min, drill + 2 * ANNULAR_MIN)

        t0 = time.time()
        field = mz.Field(qb, net, c0["width"], c0["clr_pad"], c0["clr"],
                         dia, drill, G=a.grid, layers=layers, guard=gd)
        mask = mz.poly_mask(field, frag_poly) & field.via_ok
        js, iss = np.nonzero(mask)
        legal = [(int(field.ox + int(i) * field.G),
                  int(field.oy + int(j) * field.G))
                 for j, i in zip(js, iss)]
        del field
        del qb
        lattice_s = round(time.time() - t0, 1)

        # ---- price every legal cell, then sweep for the ceiling ----------- #
        def row_for(xy):
            pr = price_at(pp, planes, isl, drills, net, xy, drill)
            return dict(xy_mm=[round(xy[0] / 1e6, 3), round(xy[1] / 1e6, 3)],
                        priced_amps=pr["priced_amps"],
                        bottleneck=pr["bottleneck"],
                        bond_amps_parallel=pr["bond_amps_parallel"],
                        internal_min_amps=pr["internal_min_amps"],
                        internal_min_width_mm=pr["internal_min_width_mm"])

        t0 = time.time()
        take = legal[:a.max_legal] if a.max_legal else legal
        legal_rows = [row_for(xy) for xy in take]
        swept = sample_cells(pcbnew, frag_poly, step_nm)
        seen = {(x, y) for (x, y) in take}
        sweep_rows = list(legal_rows)
        for xy in swept:
            if xy not in seen:
                sweep_rows.append(row_for(xy))
        price_s = round(time.time() - t0, 1)

        def best(rows):
            ok = [r for r in rows if r["priced_amps"] is not None]
            return max(ok, key=lambda r: r["priced_amps"]) if ok else None

        b_legal, b_any = best(legal_rows), best(sweep_rows)
        ceiling = b_any["priced_amps"] if b_any else None
        best_legal = b_legal["priced_amps"] if b_legal else None
        if not legal:
            verdict = "NO_LEGAL_SITE_IN_THE_FRAGMENT"
        elif required is None:
            verdict = "NET_CARRIES_NO_PUBLISHED_CURRENT"
        elif best_legal is not None and best_legal + pp.AMP_TOL >= required:
            verdict = "PRICED_ABOVE_THE_BAR"
        elif ceiling is not None and ceiling + pp.AMP_TOL >= required:
            verdict = "PRICE_IS_HELD_BY_LEGALITY"
        else:
            verdict = "REFUSED_BY_FRAGMENT_COPPER"
        # the contract's OWN verdict function, on the best legal price
        pp3 = "BONDED" if legal else "STRANDED"
        admit, why = pp.decide(pp3, best_legal, required,
                               bar_source=(None if prov is None
                                           else "RETURN_FRAGMENT_BAR"))
        results.append(dict(
            pad=pad_ref, net=net, netclass=cls,
            fragment=dict(post_island=isl["index"],
                          area_mm2=round(isl["area_mm2"], 3),
                          pads=sorted(q["ref"] for q in isl["pads"]),
                          vias=len(isl["vias"])),
            barrel=dict(dia_nm=dia, drill_nm=drill,
                        mm=[round(dia / 1e6, 3), round(drill / 1e6, 3)],
                        promotable=bool(dia >= via_min and drill >= hole_min
                                        and dia - drill >= 2 * ANNULAR_MIN)),
            bar_amps=required, bar=prov,
            legal_sites=len(legal), swept_cells=len(swept),
            best_legal_amps=best_legal, best_legal_site=b_legal,
            ceiling_amps=ceiling, ceiling_site=b_any,
            margin_x=(None if not (required and best_legal)
                      else round(best_legal / required, 3)),
            ceiling_margin_x=(None if not (required and ceiling)
                              else round(ceiling / required, 3)),
            verdict=verdict, pp2_would_admit=admit, pp2_why=why,
            seconds=dict(lattice=lattice_s, pricing=price_s),
            legal_rows=legal_rows[:200]))
        r = results[-1]
        print("  %-9s bar %s A   legal sites %-4d best legal %s A   "
              "ceiling %s A   %s"
              % (pad_ref, r["bar_amps"], r["legal_sites"],
                 r["best_legal_amps"], r["ceiling_amps"], r["verdict"]),
              file=sys.stderr, flush=True)

    doc = dict(
        schema=1, board=str(a.board),
        board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),
        fragment_board=str(a.fragment_board),
        fragment_board_sha256=hashlib.sha256(
            a.fragment_board.read_bytes()).hexdigest(),
        guard=(str(a.guard) if a.guard else None),
        grid=a.grid, step_mm=a.step_mm,
        published_table_source=table_src, netclass_source=class_src,
        method="read-only; pour_partition_contract.bond_price / "
               "return_fragment_bar / decide called VERBATIM with ONE "
               "hypothetical barrel injected at each cell, over the same "
               "Field.via_ok lattice screen_bond_site_deficit.py counts "
               "sites on.  Nothing is written and no board is modified",
        reading="`ceiling_amps` is what the fragment's OWN COPPER allows and "
                "no router, licence or placement move can raise it; "
                "`best_legal_amps` is what a barrel may actually be worth "
                "today.  A gap between them is the only case in which buying "
                "a via site -- an eviction, a relay, a part shift -- can "
                "close the edge",
        pads=results)
    if a.out:
        a.out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    else:
        json.dump(doc, sys.stdout, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
