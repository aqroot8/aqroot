#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: ask every PLANE ORPHAN the stitch question with
D-634's barrel search instead of the lattice wavefront `stitch_pad` uses.

WHY THIS EXISTS.  `screen_plane_orphans.py` sweeps the two levers a stitch has
-- the run width and the barrel geometry -- and on the current board it returns
ZERO opened islands at EVERY rung for both pour-owning nets, with exactly two
refusals: `NO_LEGAL_ESCAPE` and `NO_VIA_SITE`.  D-633 built the answer to the
first (`offcentre_escapes`) and D-634 built the answer to the second
(`_hop_sites` over `QBoard.via_sites`, cleared on every layer of the stack),
and D-634 closed by naming the work: *"PUT THE BARREL CORRECTIONS INTO THE
INSTRUMENTS THAT PROMOTE -- `relief_stitch`, `stitch_pad` and `bridge_islands`
search barrels the older way."*  D-635 and D-636 each carried that forward
unchanged.

This screen is the measurement that decides whether the correction is worth
promoting.  It asks the SAME islands the SAME question through
`maze3d.offcentre_stitch`, and it reports both arms so the difference is a
number and not a claim:

    A  `maze3d.stitch_pad`        -- today's promoting primitive, unchanged
    B  `maze3d.offcentre_stitch`  -- launch by `_hop_launch`, barrel by
                                     `_hop_sites`, walk by `connect_role`

BOTH ARMS ARE RUN ON THE SAME BOARD, THE SAME FIELD AND THE SAME RUNG, and
every trial is reverted, so a land that opens in B and not in A differs by the
search and by nothing else.  Arm A is invoked exactly as
`screen_plane_orphans.py` invokes it, so its column is comparable field for
field with that artifact.

THE BARREL MUST LAND IN THE NET'S OWN BODY POUR, and that is asked twice.
`--body` (the default) requires `maze3d.in_body` to name a layer for the
barrel's centre, on KiCad's own filled polygons; `--no-body` drops the
requirement and is reported alongside, because D-608 measured that the pour
this reads is the one filled BEFORE the barrel exists and a site outside it
today may still be flooded to.  A land that opens only unconstrained is
recorded as such and is NOT called closed.

NOTHING IS WRITTEN.  The board's sha256 is re-read after the last trial and
published; the full-board gate remains the only thing that promotes copper.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def rungs(width, via_dia, via_drill, w_floor, v_floor, d_floor, steps):
    """`screen_plane_orphans.rungs`, imported rather than re-derived."""
    from screen_plane_orphans import rungs as r
    return r(width, via_dia, via_drill, w_floor, v_floor, d_floor, steps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*", default=None)
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--fine", type=int, default=25000)
    ap.add_argument("--max-mm", type=float, default=8.0,
                    help="arm A's locality window, in millimetres")
    ap.add_argument("--span", type=int, default=8000000,
                    help="arm B's barrel-search window in nm around a launch")
    ap.add_argument("--sites-limit", type=int, default=96)
    ap.add_argument("--site-options", type=int, default=24)
    ap.add_argument("--limit", type=int, default=6,
                    help="launch candidates per land")
    ap.add_argument("--width-step", type=int, action="append", default=None)
    ap.add_argument("--below-floor", type=int, action="append", default=None,
                    metavar="NM",
                    help="ALSO ask the question at widths BELOW the class's "
                         "own .kicad_dru floor.  These rungs are EVIDENCE FOR "
                         "A LICENCE AND NOT A PROPOSAL: nothing here may be "
                         "promoted without the escape-relief licence D-632 "
                         "built and the leaf-land current proof it rides on.  "
                         "Every such rung is flagged `licensed: false`")
    ap.add_argument("--skip-licensed", action="store_true",
                    help="run ONLY the --below-floor rungs.  For a barrel "
                         "sweep, where the licensed ladder has already been "
                         "measured and re-running it buys nothing")
    ap.add_argument("--below-via", type=int, default=0, metavar="NM",
                    help="barrel DIAMETER for the --below-floor rungs; "
                         "default = the class's own .kicad_dru floor.  Like "
                         "--below-floor this is EVIDENCE, not a proposal")
    ap.add_argument("--below-drill", type=int, default=0, metavar="NM",
                    help="barrel DRILL for the --below-floor rungs")
    ap.add_argument("--guard", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN, BOARD_VIA_DIA_MIN,
                                  BOARD_HOLE_MIN, BOARD_TRACK_MIN)

    steps = tuple(a.width_step or (300000, 250000, 230000, 200000, 150000))
    sha_before = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    neck = mz.neck_rule(qb)
    reserved = reserved_inner_planes(qb.b)

    nets = list(a.nets)
    if not nets:
        nets = sorted(n for n in {t.GetNetname() for t in qb.b.GetTracks()}
                      | {p.GetNetname() for f in qb.b.GetFootprints()
                         for p in f.Pads()}
                      if n and mz.has_plane(qb, n))

    out = []
    for net in nets:
        c = net_contract(qb.b, net)
        if not mz.has_plane(qb, net):
            out.append(dict(net=net, ok=False, reason="NO_PLANE"))
            continue
        layers = list(permitted_layers(qb.routable, c["layers"], reserved,
                                       net))
        over = DRU_CLASS.get(c["netclass"], {})
        w_floor = max(BOARD_TRACK_MIN, over.get("width", 0))
        d_floor = max(BOARD_HOLE_MIN, over.get("drill", 0))
        v_floor = max(BOARD_VIA_DIA_MIN, d_floor + 2 * ANNULAR_MIN)
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        body = max(islands, key=len)
        orphans = [i for i in islands if i is not body]

        # THE BODY'S OWN FILLED COPPER, EXACT.  Computed ONCE per net: it is a
        # property of the board and not of a rung.
        polys, pmeta = mz.cluster_body_polys(qb, net, body)
        # WHICH PLANE TO AIM AT IS AN OUTPUT.  Every layer the body owns
        # filled copper on, largest area first, so a stitch is offered the
        # plane the net actually has and never one it was assumed to have.
        area = {}
        for (lname, _poly, ar) in polys:
            area[lname] = area.get(lname, 0.0) + ar
        far = sorted(area, key=lambda L: -area[L])

        rec = dict(net=net, netclass=c["netclass"], orphan_islands=len(orphans),
                   body_pads=len(body), layers=layers,
                   body_pour=pmeta, far_offered=far,
                   contract=dict(width=c["width"], via_dia=c["via_dia"],
                                 via_drill=c["via_drill"]),
                   dru_floor=dict(width=w_floor, via_dia=v_floor,
                                  drill=d_floor),
                   rungs=[])
        ladder_rungs = [] if a.skip_licensed else [
            (w, vd, vdr, True) for (w, vd, vdr) in
            rungs(c["width"], c["via_dia"], c["via_drill"],
                  w_floor, v_floor, d_floor, steps)]
        for bw in sorted(set(a.below_floor or ()), reverse=True):
            bv = a.below_via or v_floor
            bd = a.below_drill or d_floor
            # LICENSED IS A PROPERTY OF EVERY GEOMETRY, NOT JUST THE TRACK.
            # A rung at the class's own width with a barrel UNDER its floor is
            # exactly as unlicensed as a narrow track, and a net whose width
            # floor is already the board minimum (`GND`, 0.150 mm) can only be
            # swept on the barrel -- so the rung is admitted here and the flag
            # tells the truth about it.
            lic = (bw >= w_floor and bv >= v_floor and bd >= d_floor)
            ladder_rungs.append((bw, bv, bd, lic))
        for (w, vd, vdr, licensed) in ladder_rungs:
            field = mz.Field(qb, net, w, c["clr_pad"], c["clr"], vd, vdr,
                             G=a.grid, layers=layers, neck=neck,
                             guard=guard_for(spec, net) if spec else None)
            ctx = mz.EscapeCtx(qb, net, c["clr_pad"], c["clr"])
            ladder = sorted({(vd, vdr), (v_floor, d_floor)}, reverse=True)
            rows = []
            for island in orphans:
                row = dict(island=[p['ref'] for p in island])
                # HOW FAR THE BODY'S OWN COPPER IS, PER LAYER.  A stitch does
                # not have to REACH the body -- a through barrel inside the
                # body's filled polygon on ANY layer is bonded by the refill --
                # so this is the distance the walk must cover before a barrel
                # can land, and it is the number that separates "the pocket is
                # sealed" from "the plane is not underneath".
                gaps = {}
                for pad in island:
                    for (lname, poly, _ar) in polys:
                        try:
                            dmm = poly.Distance(
                                __import__('pcbnew').VECTOR2I(int(pad['x']),
                                                              int(pad['y'])))
                        except Exception:
                            continue
                        key = '%s:%s' % (pad['ref'], lname)
                        if key not in gaps or dmm < gaps[key]:
                            gaps[key] = dmm
                row['body_gap_mm'] = {k: round(v / 1e6, 4)
                                      for k, v in sorted(gaps.items())}
                # ---- arm A: today's promoting primitive, unchanged --------
                hitA = None
                for pad in island:
                    m = qb.mark()
                    r = mz.stitch_pad(qb, field, pad, max_mm=a.max_mm)
                    qb.revert(m)
                    if r.get('ok'):
                        hitA = r
                        break
                    row.setdefault('A_last', dict(
                        reason=r.get('reason'), pad=r.get('pad'),
                        why=str(r.get('why'))[:200]))
                row['A'] = (dict(ok=True, pad=hitA['pad'], mm=hitA['mm'],
                                 layer=hitA['layer'], via_xy=hitA['via_xy'])
                            if hitA else dict(ok=False, **row.pop('A_last')))
                # ---- arm B: the hop's launch and the hop's barrel ----------
                for tag, use in (('B_body', polys), ('B_free', None)):
                    hitB, lastB = None, None
                    for pad in island:
                        toward = min(body, key=lambda q: math.hypot(
                            q['x'] - pad['x'], q['y'] - pad['y']))
                        m = qb.mark()
                        r = mz.offcentre_stitch(
                            qb, ctx, pad, far, w, toward, polys=use,
                            via_ladder=ladder, G=a.grid, fine=a.fine,
                            limit=a.limit, span=a.span,
                            sites_limit=a.sites_limit,
                            site_options=a.site_options)
                        qb.revert(m)
                        if r.get('ok'):
                            hitB = r
                            break
                        if lastB is None:
                            lastB = dict(reason=r.get('reason'),
                                         pad=r.get('pad'),
                                         offered=r.get('offered'),
                                         why=str(r.get('why'))[:200])
                    row[tag] = (hitB if hitB else dict(ok=False, **lastB))
                rows.append(row)
            rec['rungs'].append(dict(
                width=w, via_dia=vd, via_drill=vdr, licensed=bool(licensed),
                opened_A=sum(r['A']['ok'] for r in rows),
                opened_B_body=sum(r['B_body']['ok'] for r in rows),
                opened_B_free=sum(r['B_free']['ok'] for r in rows),
                islands=rows))
        out.append(rec)

    report = dict(
        schema=1,
        question=("does D-634's barrel search -- the hop's exact launch and "
                  "QBoard.via_sites' fine-grid reachability, cleared on every "
                  "layer of the stack -- open a plane orphan that "
                  "maze3d.stitch_pad's lattice wavefront refuses"),
        board=str(a.board), board_sha256=sha_before,
        authoritative_unchanged=(
            hashlib.sha256(a.board.read_bytes()).hexdigest() == sha_before),
        grid=a.grid, fine=a.fine, max_mm=a.max_mm, span=a.span,
        limit=a.limit, sites_limit=a.sites_limit,
        site_options=a.site_options,
        guard=str(a.guard) if a.guard else None,
        method=dict(
            A="maze3d.stitch_pad(field, pad, max_mm) -- unchanged",
            B="maze3d.offcentre_stitch(ctx, pad, far, width, toward, polys)",
            body="maze3d.in_body on KiCad's own filled polygons, centre-in-"
                 "copper, D-608's contract"),
        nets=out)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
