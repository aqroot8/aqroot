#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: can a guarded pour bond be made REDUNDANT?

WHY THIS EXISTS.

`pour_bond_guard.py` finds, for each pour-owning net, the copper that is the
ONLY path joining one pad of a filled island to another -- a narrow neck of
pour, a "tube" -- and every promotion since D-585 has held those tubes clear of
every other net.  That is correct and it is expensive.  D-599 measured the
price: `Field(guard=...)` OFF vs ON over nine open retained nets differs on two
edges, and when the first of them (`/I2C_SCL_INT` `U3.22 -> U4.13`) was put
through the FULL gate without the guard it routed, closed its edge, SEVERED a
`GND` bond, could not be repaired, and was refused.  The guard was RIGHT.

So the guard is not the problem.  The SINGLE-POINT BOND is the problem, and it
has an obvious fix that nothing has tried:

    a `GND` island stranded on `B.Cu` behind a 0.15 mm neck is two layers away
    from a `GND` PLANE on `In1` and another on `In4`.  ONE through barrel
    dropped inside that island bonds it directly to both.  The neck stops being
    the only bond, the tube stops being critical, and the corridor it was
    freezing opens -- and the board gets a shorter return path and a thermal
    via it did not have, which is good practice whatever the router wanted.

This screen answers, per guarded tube, whether that barrel has anywhere to go:

    for each island a guard tube serves, how many LEGAL sites exist inside the
    island's own filled copper for a through via on the island's own net?

WHAT IS MEASURED, NOT ASSUMED

  * ISLANDS AND SITES ARE THE EMITTER'S.  `maze3d.filled_islands` and
    `maze3d.Field.via_ok` are what `bridge_islands` uses, so a site reported
    here is a site the gate would admit -- clearance on all six layers at the
    barrel diameter, the `.kicad_dru` netclass overlay, and hole-to-hole
    against every drill on the board.
  * THE GUARD IS HONOURED.  A tube's own keep-out is applied, so this never
    proposes a barrel that would itself slot the bond it is trying to make
    redundant.
  * A SITE IS NOT A PROMOTION.  This module writes nothing to
    `hardware/demo/kicad/aqroot-demo/` and the gate remains the authority.

`bridge_islands` will not do this today: it only offers a barrel to an island
whose cluster is ELECTRICALLY ORPHAN, and these islands are not orphan -- they
are connected, through exactly one fragile neck.  That is the extension this
screen sizes before anyone writes it.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--guard", type=Path, required=True,
                    help="a pour_bond_guard.py spec: the tubes to make redundant")
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--via", default="600000:300000",
                    help="DIA:DRILL in nm for the redundancy barrel")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for)

    dia, drill = (int(v) for v in a.via.split(":"))
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    spec = json.loads(a.guard.read_text())

    # Group the tubes by (zone uuid, layer, island): one island may carry
    # several.  KEYED BY ZONE, not by (net, layer) -- D-597 recorded why: a rail
    # whose lands cluster in two places owns two pours on one layer and the
    # island indices restart at 0 in each.
    tubes = {}
    for g in spec.get("guards", ()):
        if not g.get("ok"):
            continue
        tubes.setdefault((g["zone"], g["net"], g["lkey"], g["island"]),
                         []).append(g)

    # island polygon by (zone uuid, layer, outline index), read the same way
    # `pour_bond_guard.read_pours` reads it, so the index means the same thing.
    polys = {}
    for z in qb.b.Zones():
        if z.GetIsRuleArea():
            continue
        uuid = z.m_Uuid.AsString()
        for lid in z.GetLayerSet().CuStack():
            lname = qb.b.GetLayerName(lid)
            lkey = {"F.Cu": "F", "B.Cu": "B"}.get(lname)
            if lkey is None:
                continue
            ps = z.GetFilledPolysList(lid)
            for i in range(ps.OutlineCount()):
                poly = pcbnew.SHAPE_POLY_SET()
                poly.AddOutline(ps.Outline(i))
                for h in range(ps.HoleCount(i)):
                    poly.AddHole(ps.Hole(i, h), 0)
                polys[(uuid, lkey, i)] = poly

    out = []
    for net in sorted({k[1] for k in tubes}):   # key is (zone, net, lkey, island)
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        field = mz.Field(qb, net, c["width"], c["clr"], c["clr"], dia, drill,
                         G=a.grid, layers=layers, guard=guard_for(spec, net))
        for (zone, n, lkey, isl), group in sorted(tubes.items()):
            if n != net:
                continue
            poly = polys.get((zone, lkey, isl))
            sites, first = 0, None
            if poly is not None:
                bb = poly.BBox()
                i0, j0 = field.cell(bb.GetLeft(), bb.GetTop())
                i1, j1 = field.cell(bb.GetRight(), bb.GetBottom())
                for i in range(max(0, i0), min(field.nx, i1 + 1)):
                    for j in range(max(0, j0), min(field.ny, j1 + 1)):
                        if not field.via_ok[j, i]:
                            continue
                        x = field.ox + i * field.G
                        y = field.oy + j * field.G
                        if poly.Contains(pcbnew.VECTOR2I(int(x), int(y))):
                            sites += 1
                            if first is None:
                                first = (round(x / 1e6, 3), round(y / 1e6, 3))
            out.append(dict(
                net=n, layer=lkey, island=isl, zone=zone, sites=sites,
                first_site_mm=first, tubes=len(group),
                island_area_mm2=group[0]["island_area_mm2"],
                ends=sorted({e for g in group for e in g["ends"]}),
                redundant_bond_available=bool(sites)))
            print("  %-28s %s island %-3s  %5d legal %.2f mm sites  (%d tube%s)"
                  % (n, lkey, isl, sites, dia / 1e6, len(group),
                     "" if len(group) == 1 else "s"),
                  file=sys.stderr, flush=True)

    served = [r for r in out if r["redundant_bond_available"]]
    doc = dict(schema=1, board=str(a.board), board_sha256=board_sha,
               guard=str(a.guard),
               guard_sha256=hashlib.sha256(a.guard.read_bytes()).hexdigest(),
               via_dia_nm=dia, via_drill_nm=drill, grid=a.grid,
               summary=dict(islands=len(out), with_a_legal_site=len(served),
                            tubes_retirable=sum(r["tubes"] for r in served)),
               islands=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
