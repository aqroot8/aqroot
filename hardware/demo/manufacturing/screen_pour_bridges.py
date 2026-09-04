#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- read-only screen: which orphan pour island can ONE barrel join?

WHY THIS EXISTS, AND WHY THE STITCH CANNOT ANSWER IT.

`maze3d.stitch_pad` plants an island by asking a PAD to launch: it opens the
pad's legal escapes, walks a local wavefront to the nearest legal barrel site,
lays a stub plus a run plus a via.  That is the right primitive for a pad that
sits on BARE laminate -- there is no other way off it.

It is the wrong primitive for a pad that sits on its own severed piece of POUR.
There the copper is already there.  The island is a two-dimensional conductor,
so a barrel dropped ANYWHERE inside it is bonded to every pad on it, with no
escape, no stub and no track -- and the escape search `stitch_pad` insists on is
precisely what fails on these pads, because a fine-pitch power pad in a 0.30 mm
field has no 0.60 mm launch in any direction.

So the question this file asks is not "can a pad escape" but:

    for each electrically ORPHAN cluster of a pour-owning net, is there a point
    inside this cluster's copper on one layer AND inside another cluster's
    copper on a different layer, at which a through barrel is legal?

and, because the answer depends entirely on HOW BIG the barrel is:

    what is the COARSEST barrel that has such a point?

That second question is the one that turns the screen into a plan.  `+3V3`
`U1.2` -- the ESP32-S3 module's rail pin -- takes the full POWER-class
0.65/0.40 mm barrel with 1688 sites to spare and needs no rule exception at
all, while `GND` `U11.11/4/5` -- the BQ25185's ground and exposed pad -- has
exactly six legal cells anywhere in its island and only at 0.35/0.20 mm.  A
screen that reported one number for both would have hidden the whole decision.

WHAT IS MEASURED, NOT ASSUMED

  * THE SEARCH IS THE EMITTER'S.  `maze3d.bridge_sites` is what
    `maze3d.bridge_islands` calls, so a site reported here is the site the gate
    would lay -- there is no second implementation to drift.
  * CLUSTERS COME FROM KiCad, unioned through `GetConnectivity()`, which is the
    same connectivity the ratsnest and the promotion gate's open-edge count
    use.  "Orphan" here means exactly what an open edge means.
  * ISLAND -> CLUSTER IS BY CONTAINMENT of a real pad or via of that cluster in
    KiCad's own filled polygon, via `SHAPE_POLY_SET.Contains`.
  * BARREL LEGALITY IS `maze3d.Field.via_ok` -- copper clearance on all six
    layers at the barrel diameter, the `.kicad_dru` netclass overlay, and
    hole-to-hole against every drill on the board including this net's own.
  * THE GUARD IS HONOURED.  With `--guard`, `pour_bond_guard.py`'s tubes are
    removed from the via lattice exactly as the router removes them, so a site
    reported here is one the gate would also admit.

This module writes nothing to `hardware/demo/kicad/aqroot-demo/` and proposes no
copper.  It is a screen, and the gate remains the authority.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import pcbnew                                            # noqa: E402
import qrouter as qr                                     # noqa: E402
import incremental_router as ir                          # noqa: E402
import maze3d as mz                                      # noqa: E402
from route_maze_batch import (net_contract, BRIDGE_LADDER,  # noqa: E402
                              via_floors, load_guard, guard_for,
                              reserved_inner_planes, permitted_layers)

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def screen_net(qb, net, contract, ladder, grid, layers=None, guard=None):
    """The coarsest rung of `ladder` that bridges each orphan cluster.

    The lattice, and therefore each cluster's pour coverage, does not depend on
    the barrel -- only `via_ok` does -- so one `Field` is built and every rung
    after the first rebuilds the via lattice alone.  That is the same shortcut
    `maze3d.bridge_islands` takes, for the same reason.
    """
    field = mz.Field(qb, net, contract['width'], contract['clr'],
                     contract['clr'], ladder[0][0], ladder[0][1], G=grid,
                     layers=layers, guard=guard)
    if not mz.has_plane(qb, net):
        return dict(net=net, plane=False)
    floors = via_floors(contract['netclass'])
    rows, seen = [], {}
    for rung, (dia, drill) in enumerate(ladder):
        if rung:
            field.via_dia, field.via_drill = dia, drill
            field.via_ok = field._via_grid()
            for m in field._guard.values():
                field.via_ok &= ~m
        for entry in mz.bridge_sites(qb, net, field):
            key = tuple(entry['cluster'])
            row = seen.get(key)
            if row is None:
                row = seen[key] = dict(cluster=entry['cluster'],
                                       pads=entry['pads'],
                                       islands=entry['islands'], rungs=[],
                                       best=None, why=entry.get('why'))
                rows.append(row)
            if entry['site'] is None:
                continue
            label = entry['cluster'][0]
            plain = mz._meets_floors(dia, drill, floors)
            lic = None if plain else mz.bridge_licence(qb, net, label)
            rung_doc = dict(via_dia=dia, via_drill=drill,
                            needs_licence=(not plain),
                            licensed=bool(plain or (
                                lic and mz._barrel_licensed(dia, drill,
                                                            floors, lic))),
                            area=(None if plain
                                  else mz.bridge_area_name(label)),
                            **{k: entry['site'][k] for k in
                               ('from_layer', 'to_layer', 'sites', 'xy_mm',
                                'to_cluster', 'to_is_body')})
            row['rungs'].append(rung_doc)
            if row['best'] is None:
                row['best'] = rung_doc
                row['why'] = None
    # `bridge_sites` phrases its refusal against the barrel IT was asked about,
    # which is one rung.  The screen asked about the whole ladder, so a cluster
    # that survived every rung is refused against the FINEST one -- otherwise
    # the evidence reads as though only the coarsest barrel had been tried.
    for row in rows:
        if row['best'] is None and row['islands']:
            row['why'] = ('no legal barrel inside this island over any other '
                          'cluster, down to %.2f/%.2f mm'
                          % (ladder[-1][0] / 1e6, ladder[-1][1] / 1e6))
    return dict(net=net, plane=True, contract=contract,
                orphans=len(rows),
                bridgeable=sum(1 for r in rows if r['best']),
                needing_licence=sum(1 for r in rows if r['best']
                                    and r['best']['needs_licence']),
                unlicensed=sorted(r['cluster'][0] for r in rows
                                  if r['best'] and not r['best']['licensed']),
                detail=rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*", default=None)
    # A screen must be runnable against a SCRATCH board as well as the
    # authoritative one: the interesting orphan is often the island a run just
    # severed, which by definition does not exist on the promoted board.
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--ladder", default=None,
                    help="comma-separated DIA:DRILL barrels in nm, COARSEST "
                         "first (default: route_maze_batch.BRIDGE_LADDER)")
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec; its tubes are removed "
                         "from the via lattice exactly as the router removes "
                         "them")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    ladder = BRIDGE_LADDER
    if a.ladder:
        ladder = tuple(tuple(int(v) for v in r.split(":"))
                       for r in a.ladder.split(","))
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    board = qb.b
    nets = a.nets or sorted({z.GetNetname() for z in board.Zones()
                             if not z.GetIsRuleArea() and z.IsFilled()
                             and z.GetNetname()})
    guard_spec = load_guard(a.guard)
    reserved = reserved_inner_planes(board)
    out = dict(schema=2, board=str(a.board), board_sha256=sha256(a.board),
               grid_nm=a.grid, ladder=[list(v) for v in ladder],
               guard=str(a.guard) if a.guard else None,
               guard_sha256=sha256(a.guard) if a.guard else None, nets=[])
    for net in nets:
        c = net_contract(board, net)
        out['nets'].append(screen_net(
            qb, net, c, ladder, a.grid,
            layers=permitted_layers(qb.routable, c['layers'], reserved, net),
            guard=guard_for(guard_spec, net) if guard_spec else None))
    text = json.dumps(out, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
