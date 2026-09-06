#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- read-only screen: what closes a SEVERED POUR ISLAND, exactly?

WHY THIS EXISTS AND WHAT IT REPLACES.

`screen_pour_bridges.py` asks the right question and answers it on a raster.
It builds a `maze3d.Field` -- a whole-board blocked grid per routable layer --
and then, for every rung of the barrel ladder, a fresh SIX-LAYER via lattice
over the same board.  At the 0.100 mm routing pitch that is affordable and
board-wide.  At the pitch that can actually SEE a bridge site it is not:
`screen_pour_bridges.py GND --grid 25000` was killed at SEVENTY-FOUR MINUTES
having answered nothing, while the ad-hoc D-649 probe asked the same question
about the same land, over the same geometry, in two.

And the raster does not merely cost time -- IT LOSES ANSWERS.  `Field._via_grid`
inherits `QBoard.grid`'s 0.75-cell guard band, 0.075 mm a side at the routing
pitch.  `U9.16`'s legal barrel region measures 0.1375 x 0.1625 mm, so more than
half of it is eroded from each side and the board-wide screen reported NO BRIDGE
for a land that was ONE ordinary, already-licensed barrel from its own plane.
That barrel is now on the board (D-649).  A screen whose refusals are lattice
artefacts cannot be used to retire a family, and retiring families is the whole
point of a screen.

WHAT IS ASKED, PER ORPHAN CLUSTER, IN THE ORDER A CLOSURE IS CHEAPEST.

  ARM 1 -- THE BARREL.  Is there a point inside this cluster's filled copper on
  one layer AND inside another cluster's filled copper on a DIFFERENT layer, at
  which a through via of some rung of `route_maze_batch.BRIDGE_LADDER` is
  legal?  The candidate set is the EXACT intersection of the two filled
  polygons -- KiCad's own clipper over KiCad's own fill -- sampled at `--step`,
  deepest-inside-the-overlap first.  Every candidate is laid on the board,
  proved by `maze3d.verify_laid` and reverted, so the site reported is the site
  the gate would prove.

  This arm is EXPRESSIBLE ONLY WHERE THE NET OWNS COPPER ON TWO LAYERS.  A
  barrel does work only ACROSS layers, so a net whose entire pour lies on one
  layer has no barrel arm at all -- not a hard one, an ABSENT one -- and the
  screen says so by name rather than reporting a refusal that reads like a
  measurement.

  ARM 2 -- THE STROKE.  Is there ONE straight track, on the layer both islands
  share, joining a point inside this cluster's copper to a point inside
  another's?  This is `maze3d.pad_bridge`'s move made between two pieces of
  POUR instead of between two LANDS, and it honours the same ANCHOR CONTRACT
  `join_islands` states in its own preamble: each endpoint must lie at least
  `width / 2` inside its own filled copper, so the track lies WHOLLY within
  copper the board already carries and the join survives KiCad moving a pour
  edge by microns on refill.  Widths are the netclass width and the
  `.kicad_dru` class floor and NOTHING NARROWER -- a bridge is ordinary rail
  copper, never a licensed neck -- which is the ladder `--bridge-pads` already
  offers, for the same reason.

WHAT A REFUSAL MEANS HERE.  Both arms end in `maze3d.verify_laid`, so a refusal
carries the OBJECT that refused it and its measured gap, not an adjective.  A
cluster that refuses both arms at this step has no ONE-OBJECT closure, and the
next move for it is a corridor, an eviction or a placement change -- which is a
different transaction and a different screen.

This module writes nothing to `hardware/demo/kicad/aqroot-demo/` and proposes no
copper.  Every object it lays is reverted before the next candidate.  It is a
screen, and the gate remains the authority.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import qrouter as qr                                     # noqa: E402
import incremental_router as ir                          # noqa: E402
import maze3d as mz                                      # noqa: E402
# THE BLAME MACHINERY IS D-648's, UNCHANGED AND IMPORTED, NOT RE-IMPLEMENTED.
# `Held` removes exactly the named obstacle objects with no raster to rebuild,
# `classify` reads `QBoard._scan`'s own tag, and `verdict_of` is the same
# three-way ruling the pad-bridge frontier is published under -- so a barrel
# blocker and a stroke blocker are graded by ONE classifier and the two
# frontiers can be read side by side.
from screen_pad_bridge_blame import (Held, classify, signature,  # noqa: E402
                                     verdict_of, EVICTABLE, PLACEMENT_WALL,
                                     UNRESOLVED, BRIDGEABLE, ROUTED, PAD,
                                     KEEPOUT)
from protected_copper import PROTECTED                   # noqa: E402
from route_maze_batch import (net_contract, BRIDGE_LADDER,  # noqa: E402
                              BOARD_TRACK_MIN, DRU_CLASS, via_floors,
                              reserved_inner_planes, permitted_layers)

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def net_clusters(qb, net):
    """(islands, size, body, labels, by_cluster) with no lattice anywhere.

    The same decomposition `maze3d.cluster_coverage` performs, minus the raster
    it exists to produce: clusters from KiCad's own connectivity, islands from
    KiCad's own fill, and island -> cluster by containment of a real pad or via.
    """
    islands = mz.filled_islands(qb, net)
    roots, items = mz.pour_clusters(qb, net)
    owner = mz.island_owner(islands, roots, items)
    size = {}
    for key, r in roots.items():
        if items[key]['kind'] == 'pad':
            size[r] = size.get(r, 0) + 1
    body = max(size, key=lambda r: size[r]) if size else None
    labels = {r: sorted(k[1] for k in roots if roots[k] == r
                        and items[k]['kind'] == 'pad') for r in size}
    by_cluster = {}
    for lname, idx, poly, area in islands:
        r = owner[idx]
        if r is not None:
            by_cluster.setdefault(r, []).append((lname, idx, poly, area))
    return islands, size, body, labels, by_cluster


def blame_barrel(qb, ctx, net, xy, ladder, cap):
    """Hold out what the barrel names at ONE site, ask again, then minimise.

    D-648's loop, applied to `maze3d.exact_barrel_at` instead of to
    `maze3d.pad_bridge`.  The site is the deepest point of the overlap, which
    is the site the emitter would choose, so the set reported is the set whose
    absence would put a barrel WHERE ONE WOULD ACTUALLY GO.
    """
    held = []

    def ask(objs):
        bl = []
        with Held(qb, {id(o) for o in objs}):
            r = mz.exact_barrel_at(qb, ctx, net, xy[0], xy[1], ladder, blame=bl)
        return r, (bl[0] if bl else None)

    for _ in range(cap + 1):
        r, obj = ask(held)
        if r.get('ok'):
            break
        if obj is None:
            return dict(ok=False, reason='UNBLAMED', n_held=len(held),
                        why=r.get('why'))
        if any(x is obj for x in held):
            return dict(ok=False, reason='REPEAT', n_held=len(held))
        held.append(obj)
    else:
        return dict(ok=False, reason='CAP', n_held=len(held))
    keep = list(held)
    for obj in list(held):
        trial = [o for o in keep if o is not obj]
        if ask(trial)[0].get('ok'):
            keep = trial
    rows = []
    for obj in keep:
        trial = [o for o in keep if o is not obj]
        row = dict(signature(obj, classify(obj)),
                   drop_refuses=bool(not ask(trial)[0].get('ok')))
        # A ROUTED object is an executable unit only if this board permits it
        # to be touched at all -- the same flag the pad-bridge frontier carries.
        if row['kind'] == ROUTED and row.get('net'):
            row['protected'] = bool(PROTECTED.search(row['net']))
        rows.append(row)
    final = ask(keep)[0]
    return dict(ok=bool(final.get('ok')), site_mm=final.get('xy_mm'),
                via_dia=final.get('via_dia'), via_drill=final.get('via_drill'),
                blockers=rows, n_held=len(keep),
                n_routed=sum(1 for x in rows if x['kind'] == ROUTED),
                n_fixed=sum(1 for x in rows if x['kind'] in (PAD, KEEPOUT)),
                n_protected=sum(1 for x in rows if x.get('protected')),
                verdict=verdict_of(rows))


def blame_stroke(qb, ctx, net, layer, a, b, widths, cap):
    """Hold out what the stroke names on ONE pair, ask again, then minimise.

    `blame_barrel`'s loop over `maze3d.exact_stroke_at`.  The two arms are
    graded by the SAME classifier and reported in the same shape, so a barrel
    blocker and a stroke blocker can be read against each other and against the
    pad-bridge frontier without a third vocabulary.
    """
    held = []

    def ask(objs):
        bl = []
        with Held(qb, {id(o) for o in objs}):
            r = mz.exact_stroke_at(qb, ctx, net, layer, a[0], a[1], b[0], b[1],
                                   widths, blame=bl)
        return r, (bl[0] if bl else None)

    for _ in range(cap + 1):
        r, obj = ask(held)
        if r.get('ok'):
            break
        if obj is None:
            return dict(ok=False, reason='UNBLAMED', n_held=len(held),
                        why=r.get('why'))
        if any(x is obj for x in held):
            return dict(ok=False, reason='REPEAT', n_held=len(held))
        held.append(obj)
    else:
        return dict(ok=False, reason='CAP', n_held=len(held))
    keep = list(held)
    for obj in list(held):
        trial = [o for o in keep if o is not obj]
        if ask(trial)[0].get('ok'):
            keep = trial
    rows = []
    for obj in keep:
        trial = [o for o in keep if o is not obj]
        row = dict(signature(obj, classify(obj)),
                   drop_refuses=bool(not ask(trial)[0].get('ok')))
        if row['kind'] == ROUTED and row.get('net'):
            row['protected'] = bool(PROTECTED.search(row['net']))
        rows.append(row)
    final = ask(keep)[0]
    return dict(ok=bool(final.get('ok')), width=final.get('width'),
                mm=final.get('mm'), a_xy=final.get('a_xy'),
                b_xy=final.get('b_xy'), blockers=rows, n_held=len(keep),
                n_routed=sum(1 for x in rows if x['kind'] == ROUTED),
                n_fixed=sum(1 for x in rows if x['kind'] in (PAD, KEEPOUT)),
                n_protected=sum(1 for x in rows if x.get('protected')),
                verdict=verdict_of(rows))


def screen_cluster(qb, ctx, net, contract, r, size, body, labels, by_cluster,
                   ladder, widths, step, pairs, blame_cap=0):
    """Both arms for ONE orphan cluster, barrel first."""
    mine = by_cluster.get(r, [])
    out = dict(cluster=labels[r], pads=size[r],
               islands=[dict(layer=l, mm2=round(a, 4)) for l, _i, _p, a in mine])
    if not mine:
        out['barrel'] = dict(ok=False, reason='NO_ISLAND',
                             why='this cluster owns no filled pour island, so '
                                 'neither arm of this screen is its move')
        out['stroke'] = dict(ok=False, reason='NO_ISLAND')
        return out
    targets = sorted(by_cluster, key=lambda t: (t != body, -size.get(t, 0),
                                                str(labels.get(t, ''))))
    floors = via_floors(contract['netclass'])

    # -- ARM 1: the barrel ------------------------------------------------- #
    # EVERY OVERLAP IS ASKED, LARGEST FIRST.  A cluster may face several other
    # clusters on several layers, and the first overlap found is not the one
    # most likely to hold a barrel -- the BIGGEST is, because a barrel needs
    # room and a 0.001 mm2 shard is nine candidate centres while a 0.077 mm2
    # one is five hundred.  Stopping at the first refusal, which is what a
    # `barrel or got` guard does, would report a shard's refusal as the
    # cluster's answer and never ask the region that could have closed it.
    regions = []
    for tgt in targets:
        if tgt == r:
            continue
        for (la, _ia, pa, _aa) in mine:
            for (lb, _ib, pb, _ab) in by_cluster[tgt]:
                if lb == la:
                    continue            # a barrel does work only ACROSS layers
                region = mz.poly_overlap(pa, pb)
                if region is not None:
                    regions.append((region.Area(), str(labels.get(tgt, '')),
                                    la, lb, tgt, region))
    regions.sort(key=lambda t: (-t[0], t[1], t[2], t[3]))
    barrel, overlaps = None, len(regions)
    for (_area, _lbl, la, lb, tgt, region) in regions:
        got = mz.exact_barrel(qb, ctx, net, region, ladder, step)
        got.update(from_layer=la, to_layer=lb,
                   to_cluster=labels.get(tgt, [])[:4],
                   to_is_body=bool(tgt == body),
                   overlap_mm2=round(region.Area() / 1e12, 6))
        if got['ok']:
            plain = mz._meets_floors(got['via_dia'], got['via_drill'], floors)
            lic = None if plain else mz.bridge_licence(
                qb, net, labels[r][0] if labels[r] else None)
            got['needs_licence'] = not plain
            got['area'] = (None if plain
                           else mz.bridge_area_name(
                               labels[r][0] if labels[r] else None))
            got['licensed'] = bool(plain or mz._barrel_licensed(
                got['via_dia'], got['via_drill'], floors, lic))
            barrel = got
            break
        if barrel is None:
            barrel = got
    if barrel is None:
        barrel = dict(ok=False, reason='ARM_NOT_EXPRESSIBLE',
                      why="no other cluster of this net owns filled copper on "
                          "another layer over this island, so no through "
                          "barrel joins anything at ANY drill or lattice")
    barrel['overlaps'] = overlaps
    if (blame_cap and not barrel.get('ok') and barrel.get('site')):
        barrel['blame'] = blame_barrel(qb, ctx, net, barrel['site'], ladder,
                                       blame_cap)
    out['barrel'] = barrel

    # -- ARM 2: the stroke ------------------------------------------------- #
    # NEAREST FIRST, and that ordering is not cosmetic.  The barrel arm is
    # ordered body-first because a barrel to the plane body is the shorter
    # claim to review; a STRAIGHT track is bounded by how far apart the two
    # pieces are, so asking a 9 mm pair before a 0.7 mm one reports `TOO_FAR`
    # for a cluster whose real answer is a measured refusal one millimetre
    # away.  Merging ANY two clusters closes exactly one open edge --
    # `join_islands` says so in its own preamble -- so nearest is also the
    # cheapest closure, not merely the cheapest question.
    pairs_by_gap = []
    for tgt in targets:
        if tgt == r:
            continue
        for (la, _ia, pa, _aa) in mine:
            for (lb, _ib, pb, _ab) in by_cluster[tgt]:
                if lb != la:
                    continue
                g = mz.poly_gap(pa, pb, step * 4)
                if g is None:
                    continue
                pairs_by_gap.append((g[0], str(labels.get(tgt, '')), tgt, la,
                                     pa, pb))
    pairs_by_gap.sort(key=lambda t: (t[0], t[1]))
    stroke = None
    for (gap, _lbl, tgt, la, pa, pb) in pairs_by_gap:
        got = mz.exact_island_stroke(qb, ctx, net, la, pa, pb, widths, step,
                                     pairs=pairs)
        got.update(to_cluster=labels.get(tgt, [])[:4],
                   to_is_body=bool(tgt == body),
                   gap_mm=round(gap / 1e6, 4))
        if got['ok']:
            stroke = got
            break
        if stroke is None:
            stroke = got
        if got.get('reason') == 'TOO_FAR':
            break               # sorted by gap: every later pair is further
    if (blame_cap and stroke and not stroke.get('ok')
            and stroke.get('a') and stroke.get('b')):
        stroke['blame'] = blame_stroke(qb, ctx, net, stroke['layer'],
                                       stroke['a'], stroke['b'], widths,
                                       blame_cap)
    out['stroke'] = stroke or dict(ok=False, reason='NO_SAME_LAYER_TARGET',
                                   why='no other cluster of this net owns '
                                       'filled copper on a layer this island '
                                       'shares')
    return out


def screen_net(qb, net, step, pairs, ladder=None, blame_cap=0):
    contract = net_contract(qb.b, net)
    if not mz.has_plane(qb, net):
        return dict(net=net, plane=False)
    reserved = reserved_inner_planes(qb.b)
    layers = permitted_layers(qb.routable, contract['layers'], reserved, net)
    ctx = mz.BridgeCtx(qb, net, contract['clr_pad'], contract['clr'], layers)
    w_floor = max(BOARD_TRACK_MIN,
                  DRU_CLASS.get(contract['netclass'], {}).get('width', 0))
    widths = sorted({contract['width'], min(contract['width'], w_floor)},
                    reverse=True)
    islands, size, body, labels, by_cluster = net_clusters(qb, net)
    rows = []
    for r in sorted(size, key=lambda k: (-size[k], str(labels[k]))):
        if r == body:
            continue
        rows.append(screen_cluster(qb, ctx, net, contract, r, size, body,
                                   labels, by_cluster, ladder or BRIDGE_LADDER,
                                   widths, step, pairs, blame_cap=blame_cap))
    return dict(net=net, plane=True, netclass=contract['netclass'],
                layers=list(layers), widths_offered=widths,
                body=labels.get(body, []), islands=len(islands),
                clusters=len(size), orphans=len(rows),
                barrel_ok=sum(1 for x in rows if x['barrel'].get('ok')),
                stroke_ok=sum(1 for x in rows if x['stroke'].get('ok')),
                barrel_inexpressible=sum(
                    1 for x in rows
                    if x['barrel'].get('reason') == 'ARM_NOT_EXPRESSIBLE'),
                barrel_evictable=sum(
                    1 for x in rows
                    if (x['barrel'].get('blame') or {}).get('verdict')
                    == EVICTABLE),
                stroke_evictable=sum(
                    1 for x in rows
                    if (x['stroke'].get('blame') or {}).get('verdict')
                    == EVICTABLE),
                detail=rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*", default=None)
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--step", type=int, default=12500,
                    help="nm between candidate centres inside a region "
                         "(default 12500 -- HALF the finest pitch this board "
                         "screens at, which is what found U9.16's barrel)")
    ap.add_argument("--pairs", type=int, default=24,
                    help="nearest anchor pairs offered to the stroke arm per "
                         "width")
    ap.add_argument("--ladder", default=None,
                    help="comma-separated DIA:DRILL barrels in nm, COARSEST "
                         "first (default: route_maze_batch.BRIDGE_LADDER)")
    ap.add_argument("--blame", type=int, default=0, metavar="CAP",
                    help="for a barrel arm that is EXPRESSIBLE but refused, "
                         "hold the named object out at the deepest site, ask "
                         "again to exhaustion, MINIMISE the set and CLASSIFY "
                         "each member with screen_pad_bridge_blame's own "
                         "classifier (0 = off)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    ladder = BRIDGE_LADDER
    if a.ladder:
        ladder = tuple(tuple(int(v) for v in r.split(":"))
                       for r in a.ladder.split(","))
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    nets = a.nets or sorted({z.GetNetname() for z in qb.b.Zones()
                             if not z.GetIsRuleArea() and z.IsFilled()
                             and z.GetNetname()})
    out = dict(schema=1, board=str(a.board), board_sha256=sha256(a.board),
               step_nm=a.step, pairs=a.pairs,
               ladder=[list(v) for v in ladder],
               method="read-only; exact polygon overlap and maze3d.verify_laid "
                      "over QBoard.obstacles, no lattice and no Field; every "
                      "candidate object is laid, proved and reverted",
               blame_cap=a.blame,
               nets=[screen_net(qb, n, a.step, a.pairs, ladder, a.blame)
                     for n in nets])
    text = json.dumps(out, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
