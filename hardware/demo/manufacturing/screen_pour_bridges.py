#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- read-only screen: which orphan pour islands can ONE barrel join?

WHY THIS EXISTS, AND WHY THE EXISTING STITCH CANNOT ANSWER IT.

`maze3d.stitch_pad` plants an island by asking a PAD to launch: it opens the
pad's legal escapes, walks a local wavefront to the nearest legal barrel site,
lays a stub plus a run plus a via.  That is the right primitive for a pad that
sits on BARE laminate -- there is no other way off it.

It is the wrong primitive for a pad that sits on its own severed piece of POUR.
There the copper is already there.  The island is a two-dimensional conductor,
so a barrel dropped ANYWHERE inside it is bonded to every pad on it, with no
escape, no stub and no track -- and the escape search that `stitch_pad` insists
on is precisely what fails on these pads, because a fine-pitch power pad in a
0.30 mm field has no 0.60 mm launch in any direction.  D-583's stitch reported
nine such islands as `NO_VIA_SITE` / `NO_LEGAL_ESCAPE` and D-584's `--neck`
lever recovered exactly one of them; the other thirteen `+3V3` islands and nine
`GND` islands are still open, and every one of them owns copper.

So the question this file asks is not "can a pad escape" but:

    for each electrically ORPHAN cluster of a pour-owning net, is there a point
    that lies inside this cluster's copper on one layer AND inside another
    cluster's copper on a different layer, at which a through barrel is legal?

If yes, ONE via -- zero tracks, zero escapes -- merges the two clusters.

WHAT IS MEASURED, NOT ASSUMED

  * CLUSTERS COME FROM KiCad.  Pads and vias of the net are unioned through
    `GetConnectivity().GetConnectedItems()`, which is the same connectivity the
    ratsnest and `maze3d.net_islands` use, so "orphan" here means exactly what
    the promotion gate's open-edge count means.
  * ISLAND -> CLUSTER IS BY CONTAINMENT of a real pad or via of that cluster in
    the filled polygon, using KiCad's own `SHAPE_POLY_SET.Contains`.  The
    promoted board removes islands that touch no pad, so a surviving island has
    one.  An island that still cannot be attributed is reported as such rather
    than guessed at.
  * BARREL LEGALITY IS `maze3d.Field.via_ok` -- the SAME lattice the accepted
    stitch used for every promoted barrel: copper clearance on all six layers
    at the barrel diameter, the .kicad_dru netclass overlay, and hole-to-hole
    against every drill on the board including this net's own.
  * COVERAGE IS SAMPLED ON THAT LATTICE, so a site this screen reports is a
    site the router can actually take; nothing is interpolated.

This module writes nothing to `hardware/demo/kicad/aqroot-demo/` and proposes
no copper.  It is a screen, and the gate remains the authority.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import pcbnew                                            # noqa: E402
import qrouter as qr                                     # noqa: E402
import incremental_router as ir                          # noqa: E402
import maze3d as mz                                      # noqa: E402
from route_maze_batch import net_contract                # noqa: E402

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# pour geometry
# --------------------------------------------------------------------------- #
def filled_islands(board, net):
    """[(layer_name, index, SHAPE_POLY_SET, area_mm2)] for every filled island."""
    out = []
    for z in board.Zones():
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


def clusters(board, net):
    """Union-find over this net's pads and vias, using KiCad connectivity.

    Returns (roots, items) where `items[key] = dict(kind, x, y, layers)` and
    `roots[key]` is the cluster representative.  Zone-mediated connections are
    included because that is what `GetConnectedItems` reports.
    """
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    items, handles = {}, {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net or not p.GetNumber():
                continue
            pos = p.GetPosition()
            key = ('P', f.GetReference() + '.' + p.GetNumber(), pos.x, pos.y)
            items[key] = dict(kind='pad', x=pos.x, y=pos.y,
                              layers=tuple(L for L, lid in qr.LNAME.items()
                                           if p.IsOnLayer(lid)))
            handles[key] = p
    for t in board.GetTracks():
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
            cls = it.GetClass()
            if cls not in ('PAD', 'PCB_VIA'):
                continue
            pos = it.GetPosition()
            for other in bykey.get((pos.x, pos.y), ()):
                ra, rb = find(key), find(other)
                if ra != rb:
                    parent[ra] = rb
    return {k: find(k) for k in items}, items


def attribute(islands, roots, items):
    """island index -> cluster root, by containment of a pad or via of it."""
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


# --------------------------------------------------------------------------- #
# the screen
# --------------------------------------------------------------------------- #
def rings(poly):
    """Every closed ring of a one-outline SHAPE_POLY_SET, holes included.

    Returned as (xs, ys) float arrays so the even-odd test below is one
    vectorised pass.  Holes are ordinary rings: under the even-odd rule a point
    inside outline-and-hole is crossed twice and falls out, which is exactly
    the containment KiCad's own `Contains` reports, so the raster and the
    board agree about where the copper is without a second code path.
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


def coverage(field, poly):
    """Boolean lattice mask of the cells whose centre lies inside `poly`.

    Rasterised with the same even-odd crossing test `maze3d.Neck.mask` uses on
    courtyards, restricted to the island's bounding box.  A per-cell call into
    `SHAPE_POLY_SET.Contains` is the obvious implementation and is unusable
    here: the largest `+3V3` island alone covers ~400,000 lattice cells.
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
    for xs, ys in rings(poly):
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


def screen_net(qb, board, net, contract, grid):
    islands = filled_islands(board, net)
    if not islands:
        return dict(net=net, plane=False)
    roots, items = clusters(board, net)
    owner = attribute(islands, roots, items)

    size = {}
    for key, r in roots.items():
        if items[key]['kind'] == 'pad':
            size[r] = size.get(r, 0) + 1
    body = max(size, key=lambda r: size[r]) if size else None

    field = mz.Field(qb, net, contract['width'], contract['clr'],
                     contract['clr'], contract['via_dia'],
                     contract['via_drill'], grid)

    # per-cluster coverage, unioned over layers, plus per (cluster, layer)
    cov, cov_layer = {}, {}
    for lname, idx, poly, area in islands:
        r = owner[idx]
        if r is None:
            continue
        m = coverage(field, poly)
        cov_layer.setdefault((r, lname), np.zeros((field.ny, field.nx),
                                                  dtype=bool))
        cov_layer[(r, lname)] |= m
        cov.setdefault(r, np.zeros((field.ny, field.nx), dtype=bool))
        cov[r] |= m

    def label(r):
        return sorted(k[1] for k in roots if roots[k] == r
                      and items[k]['kind'] == 'pad')

    report = []
    for r in sorted(size, key=lambda r: (-size[r], str(label(r)))):
        if r == body:
            continue
        entry = dict(cluster=label(r), pads=size[r],
                     islands=[dict(layer=l, mm2=round(a, 2))
                              for l, i, _p, a in islands if owner[i] == r],
                     bridge=None)
        mine = cov.get(r)
        if mine is not None and mine.any():
            # A through barrel merges every cluster whose copper covers the
            # site on ANY layer, so a site inside MY copper on one layer and
            # inside ANOTHER cluster's copper on a different layer is a join.
            for tgt in sorted(cov, key=lambda t: (t != body, -size.get(t, 0))):
                if tgt == r:
                    continue
                # different LAYER is what makes the barrel do work
                hit = None
                for (cr, cl), cm in cov_layer.items():
                    if cr != r:
                        continue
                    for (tr, tl), tm in cov_layer.items():
                        if tr != tgt or tl == cl:
                            continue
                        cand = cm & tm & field.via_ok
                        if cand.any():
                            js, iss = np.nonzero(cand)
                            x, y = field.point(int(iss[0]), int(js[0]))
                            hit = dict(from_layer=cl, to_layer=tl,
                                       sites=int(cand.sum()),
                                       xy=[round(x / 1e6, 4),
                                           round(y / 1e6, 4)],
                                       to_cluster=label(tgt)[:4],
                                       to_is_body=bool(tgt == body))
                            break
                    if hit:
                        break
                if hit:
                    entry['bridge'] = hit
                    break
            if entry['bridge'] is None:
                entry['why'] = 'no legal %.2f mm barrel inside this island ' \
                               'over any other cluster' % (
                                   contract['via_dia'] / 1e6)
        else:
            entry['why'] = 'cluster owns no filled pour island'
        report.append(entry)

    return dict(net=net, plane=True, contract=contract,
                clusters=len(size), body_pads=size.get(body, 0),
                orphans=len(report), bridgeable=sum(
                    1 for e in report if e['bridge']),
                detail=report)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*", default=None)
    # A screen must be runnable against a SCRATCH board as well as the
    # authoritative one: the interesting orphan is often the island a run just
    # severed, which by definition does not exist on the promoted board.
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    board_path = a.board
    qb = qr.QBoard(str(board_path))
    ir.inject_existing_via_obstacles(qb)
    board = qb.b

    nets = a.nets or sorted({z.GetNetname() for z in board.Zones()
                             if not z.GetIsRuleArea() and z.IsFilled()
                             and z.GetNetname()})
    out = dict(schema=1, board=str(board_path), board_sha256=sha256(board_path),
               grid_nm=a.grid, nets=[])
    for net in nets:
        out['nets'].append(screen_net(qb, board, net,
                                      net_contract(board, net), a.grid))
    text = json.dumps(out, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
