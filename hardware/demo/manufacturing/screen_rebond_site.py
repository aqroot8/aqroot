#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: where may a pad's PLANE BOND go, and who forbids
the rest?

D-653 built the RE-BOND primitive -- `route_maze_batch.py --detour-spec` may
now name a BARREL, remove it whole, and (with `to_mm`) put the same barrel down
somewhere else.  The primitive is the easy half.  The hard half is the question
this screen asks, and three full gate runs were spent learning that nothing on
this board asked it:

    A BOND BARREL MUST BE LEGAL ON THE BOARD THE RUN *ENDS* WITH, NOT THE ONE
    IT STARTS WITH.

`U2.21` is the `PCAL9535A`'s `A0` address strap and the only pad on `B.Cu`
`GND` island 24 (16.523 mm2).  Before the run there are 1330 legal 0.60/0.30
barrel sites in that island.  After `/I2C_SCL_INT` escapes `U2.22` -- which is
the entire point of removing the barrel -- KiCad's own refill leaves `U2.21` on
a 1.5 mm2 sliver and there are ZERO, at every diameter down to the board's
0.50 mm via floor and every pitch down to 0.025 mm.  `screen_bond_ladder.py`
already carries `--fragment-board` for exactly this shape; what it does not do
is say WHOSE copper the sliver is short of room because of, which is the only
form of the answer a transaction can act on.

So this screen reports three things about ONE pad:

  BEFORE   every legal barrel site of the pad's own net inside the pad's own
           filled island, per via rung, on the board as given.
  AFTER    the same census restricted to the BAND a `--fragment-board` leaves,
           so a site that the run's own copper is about to cut away is not
           counted as a site.
  BLAME    for each foreign net with routed copper in the window, the sites
           that appear when THAT net's copper is held out -- `WithoutObjects`,
           restored on exit, board never written -- plus the ALL_FOREIGN upper
           bound.  A net that opens sites is one `--detour-spec` from a
           re-bond; a band that opens for nobody is a placement wall and should
           be recorded as one instead of costing another gate run.

The via rungs default to the net's own netclass barrel and the smallest barrel
the board licenses OUTRIGHT (`min_via_diameter`).  Anything finer needs a
`.kicad_dru` rule area, which is a licence decision and not a screen result --
see `--escape-relief` -- so this refuses to report one as available.
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import pcbnew                                                   # noqa: E402
import qrouter as qr                                            # noqa: E402
import incremental_router as ir                                 # noqa: E402
import maze3d as mz                                             # noqa: E402
from route_maze_batch import (net_contract, reserved_inner_planes,  # noqa: E402
                              permitted_layers, BOARD_VIA_DIA_MIN,
                              sha256_file)
from screen_corridor_blockers import WithoutObjects             # noqa: E402

ROUTED = ("track", "via")


def pad_of(board, ref):
    r, n = ref.rsplit(".", 1)
    for fp in board.GetFootprints():
        if fp.GetReference() != r:
            continue
        for p in fp.Pads():
            if p.GetNumber() == n:
                return p
    raise SystemExit("screen_rebond_site: no such pad %r" % ref)


def island_of(board, net, x_nm, y_nm, layer=pcbnew.B_Cu):
    """(index, area, SHAPE_POLY_SET) of the filled island holding this point."""
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net:
            continue
        if not z.GetLayerSet().Contains(layer):
            continue
        ps = z.GetFilledPolysList(layer)
        for i in range(ps.OutlineCount()):
            sp = pcbnew.SHAPE_POLY_SET()
            sp.AddOutline(ps.Outline(i))
            if sp.Contains(pcbnew.VECTOR2I(x_nm, y_nm)):
                bb = ps.Outline(i).BBox()
                return dict(index=i, area_mm2=round(sp.Area() / 1e12, 3),
                            poly=sp, zone=z.GetZoneName(),
                            bbox_mm=[round(v / 1e6, 4) for v in
                                     (bb.GetLeft(), bb.GetTop(),
                                      bb.GetRight(), bb.GetBottom())])
    return None


def census(field, poly, band, grid, cap=8):
    """Legal barrel sites of this Field inside `poly` and inside `band`."""
    n, ex = 0, []
    x0, y0, x1, y1 = [v * 1e6 for v in band] if band else (None,) * 4
    for j in range(field.ny):
        y = field.oy + j * grid
        if band and not (y0 <= y <= y1):
            continue
        row = field.via_ok[j]
        for i in range(field.nx):
            x = field.ox + i * grid
            if band and not (x0 <= x <= x1):
                continue
            if not row[i]:
                continue
            if poly is not None and not poly.Contains(
                    pcbnew.VECTOR2I(int(x), int(y))):
                continue
            n += 1
            if len(ex) < cap:
                ex.append([round(x / 1e6, 4), round(y / 1e6, 4)])
    return n, ex


def objects_of(qb, net, win):
    out = []
    for L in qb.shapes:
        for s in qb.shapes[L]:
            if s.net != net or getattr(s, "tag", "") not in ROUTED:
                continue
            a, b, c, d = s.bbox(0)
            if (a < win[0] * 1e6 or b < win[1] * 1e6
                    or c > win[2] * 1e6 or d > win[3] * 1e6):
                continue
            out.append(s)
    for h in qb.holes:
        if h.net != net or not h.tag.startswith("via"):
            continue
        a, b, c, d = h.bbox(0)
        if (a < win[0] * 1e6 or b < win[1] * 1e6
                or c > win[2] * 1e6 or d > win[3] * 1e6):
            continue
        out.append(h)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pad", help="REF.NUM whose plane bond is being moved")
    ap.add_argument("--board", default=str(
        ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"),
        help="the board the barrel would be laid ON -- normally the "
             "authoritative one, or a --detour-apply'd scratch")
    ap.add_argument("--fragment-board", help="a POST board on which this run's "
                    "own copper has already been laid and the zones REFILLED. "
                    "The pad's island THERE is the band every site is also "
                    "required to fall inside, because that is the copper the "
                    "pad will actually be able to reach")
    ap.add_argument("--grid", type=int, default=25000)
    ap.add_argument("--via", action="append", default=[],
                    metavar="DIA:DRILL", help="nm rungs instead of the "
                    "default (netclass barrel, then the board's own "
                    "min_via_diameter); repeatable, widest first")
    ap.add_argument("--window", default=None,
                    help="x0,y0,x1,y1 in mm for the BLAME pass; default is the "
                         "pad's island bbox grown by --window-margin")
    ap.add_argument("--window-margin", type=float, default=2.0)
    ap.add_argument("--no-blame", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    t0 = time.time()
    board = pcbnew.LoadBoard(a.board)
    pad = pad_of(board, a.pad)
    net = pad.GetNetname()
    pos = pad.GetPosition()
    isl = island_of(board, net, pos.x, pos.y)
    if isl is None:
        raise SystemExit("screen_rebond_site: %s (%s) sits in no filled "
                         "B.Cu island of its own net on %s"
                         % (a.pad, net, a.board))

    band = None
    frag = None
    if a.fragment_board:
        fb = pcbnew.LoadBoard(a.fragment_board)
        frag = island_of(fb, net, pos.x, pos.y)
        if frag is None:
            raise SystemExit("screen_rebond_site: on the fragment board %s "
                             "sits in NO filled island at all -- the run "
                             "stranded it outright" % a.pad)
        band = frag["bbox_mm"]

    qb = qr.QBoard(a.board)
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    base = net_contract(qb.b, net)
    far = list(permitted_layers(qb.routable, base["layers"], reserved, net))
    rungs = ([tuple(int(v) for v in q.split(":")) for q in a.via]
             or [(base["via_dia"], base["via_drill"]),
                 (BOARD_VIA_DIA_MIN, BOARD_VIA_DIA_MIN // 2)])

    if a.window:
        win = [float(v) for v in a.window.split(",")]
    else:
        m = a.window_margin
        win = [isl["bbox_mm"][0] - m, isl["bbox_mm"][1] - m,
               isl["bbox_mm"][2] + m, isl["bbox_mm"][3] + m]

    cands = sorted({s.net for L in qb.shapes for s in qb.shapes[L]
                    if getattr(s, "tag", "") in ROUTED and s.net not in ("", net)
                    and win[0] * 1e6 <= s.bbox(0)[0] and s.bbox(0)[2] <= win[2] * 1e6
                    and win[1] * 1e6 <= s.bbox(0)[1] and s.bbox(0)[3] <= win[3] * 1e6})

    rows = []
    for dia, drill in rungs:
        licensed = dia >= BOARD_VIA_DIA_MIN
        field = mz.Field(qb, net, base["width"], base["clr_pad"], base["clr"],
                         dia, drill, G=a.grid, layers=far)
        n_all, ex_all = census(field, isl["poly"], None, a.grid)
        rec = dict(via_mm=[dia / 1e6, drill / 1e6], licensed_outright=licensed,
                   sites_in_island=n_all, examples=ex_all)
        if band is not None:
            n_b, ex_b = census(field, isl["poly"], band, a.grid)
            rec.update(sites_in_fragment_band=n_b, band_examples=ex_b)
        rows.append(rec)
        print("%.2f/%.2f  island %d sites%s"
              % (dia / 1e6, drill / 1e6, n_all,
                 ("  fragment band %d" % rec.get("sites_in_fragment_band", 0))
                 if band else ""), file=sys.stderr, flush=True)

        if a.no_blame or band is None or rec.get("sites_in_fragment_band"):
            continue
        blame = []
        allobjs = []
        for foreign in cands:
            objs = objects_of(qb, foreign, win)
            if not objs:
                continue
            allobjs += objs
            with WithoutObjects(qb, field, [id(o) for o in objs]):
                n, ex = census(field, isl["poly"], band, a.grid)
            blame.append(dict(net=foreign, objects=len(objs), sites=n,
                              examples=ex))
            if n:
                print("    %-42s -%d objects -> %d sites %s"
                      % (foreign, len(objs), n, ex[:3]),
                      file=sys.stderr, flush=True)
        with WithoutObjects(qb, field, [id(o) for o in allobjs]):
            n, ex = census(field, isl["poly"], band, a.grid)
        print("    %-42s -%d objects -> %d sites"
              % ("ALL FOREIGN", len(allobjs), n), file=sys.stderr, flush=True)
        rec["blame"] = sorted(blame, key=lambda r: (-r["sites"], r["net"]))
        rec["all_foreign"] = dict(objects=len(allobjs), sites=n, examples=ex)

    doc = dict(schema=1, pad=a.pad, net=net, board=a.board,
               board_sha256=sha256_file(Path(a.board)),
               fragment_board=a.fragment_board,
               fragment_board_sha256=(sha256_file(Path(a.fragment_board))
                                      if a.fragment_board else None),
               grid_nm=a.grid, layers=far, window_mm=win,
               island=dict(index=isl["index"], area_mm2=isl["area_mm2"],
                           zone=isl["zone"], bbox_mm=isl["bbox_mm"]),
               fragment=(dict(index=frag["index"], area_mm2=frag["area_mm2"],
                              bbox_mm=frag["bbox_mm"]) if frag else None),
               rungs=rows, seconds=round(time.time() - t0, 1))
    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    if a.out:
        a.out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
