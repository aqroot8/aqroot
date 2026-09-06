#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: a net's orphan land may be nearer its own TRACK
than any pad the router is allowed to aim at.

`maze3d.net_islands` groups a net's pads by the copper that already joins them,
and `route_join` then closes an island pair pad-to-pad: `src_pads` and
`dst_pads` are lists of PADS and every escape of every one of them takes part.
That is the right question for a net with no copper.  It is the WRONG question
for a net with accepted partial copper, and this board is now almost entirely
the second kind:

    /I2C_SDA_INT  U2.23   nearest PAD of the target island   10.000 mm
                          nearest COPPER of the same island   1.802 mm

The bus already runs 1.8 mm from the land.  The router has never been allowed
to see it, so for eighteen decisions this edge has been priced as a 10 mm haul
across the most congested pocket on the board.  Board-wide the gap is 16.5 mm
on `/I2S_LRCLK` `U5.14`, 9.5 mm on `/I2C_SCL_INT` `U16.3`, 8.2 mm here, and
4.5 / 4.3 mm on the two `/NFC_SUPPLY` lands.

A T-junction onto a conductor of one's own net is ordinary PCB practice and the
mechanism to express it ALREADY EXISTS in `maze3d`: `offcentre_route` accepts
an END that carries `anchor=True` and routes to that exact coordinate without
asking it to escape, because an anchor is not a pad -- it is a point already on
copper.  What was missing was a caller that builds an anchor out of the net's
OWN CONNECTED COPPER.  This screen is that caller, and nothing else.

  TAP1  THE TARGET IS PROVED BY CONNECTIVITY, NOT BY DISTANCE.  A tap point is
        accepted only if KiCad's own `CONNECTIVITY_DATA` puts the track or via
        it lies on in the same cluster as a PAD of the target island.  Copper
        of the right net that is itself orphaned is not a target; joining to it
        would close no edge and the ledger would say so afterwards.

  TAP2  NOTHING IS REMOVED AND NOTHING IS MODIFIED.  A tap only ADDS copper
        whose far end lies on a conductor this board already carries.  It is
        not an eviction, not a detour and not a relay; no existing object is
        named, moved, shortened or split.

  TAP3  THE PROOF IS `offcentre_route`'s OWN.  The launch is the exact
        off-centre stub (D-633), the haul is the whole-board 3D corridor
        (`wave3d`), and every object -- stub, run and barrel -- is re-proved by
        `maze3d.verify_laid` in exact geometry against real obstacle shapes and
        the `.kicad_dru` overlay before it is kept.  This file contains no
        clearance arithmetic of its own.  Every trial is laid on the live
        `QBoard` and REVERTED, and the board is opened read-only.

  TAP4  A TAP MAKES A STUB, SO THE NETCLASS DECIDES WHETHER IT MAY BE ASKED.
        `STUB_FORBIDDEN` classes are refused BY NAME and never searched: their
        rules are about the shape of the conductor, not about congestion, and
        an instrument that measured them anyway would be offering copper the
        board's own rules forbid.  A `.kicad_dru` section that reserves a layer
        or forbids vias for a class is the same ruling by another road.

  TAP5  IT PROPOSES NOTHING.  A `TAP_ROUTABLE` row is a work-list entry, not a
        transaction: the gate's clauses -- pour partition included -- have not
        been asked, and the copper this screen proves legal is reverted before
        the next row is measured.

    python3 screen_net_tap.py [NET ...] [--board B] [--grid N] [--max-mm F]
        [--pairs N] [--stub-forbidden CLASS,CLASS] [-o OUT]
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# TAP4.  A tap is a T-junction and a T-junction is a STUB.  These classes are
# refused by NAME, before any search: their rules govern the SHAPE of the
# conductor -- matched length, controlled impedance, a reserved layer, a
# switching node's loop area, an RF arm's symmetry -- and none of those survive
# an unbudgeted branch.  Widening this set is a rules question; narrowing it is
# an owner one.
STUB_FORBIDDEN = ("USB_D", "NFC_RF", "NFC_RX", "SWITCH_NODE", "SPK_OUT")

INNER_SHORT = {"In1.Cu": "I1", "In2.Cu": "I2", "In3.Cu": "I3", "In4.Cu": "I4"}


def _short_layer(board, layer_id):
    """The router's short name for a board layer, or None if it has none."""
    name = board.GetLayerName(layer_id)
    if name == board.GetLayerName(0):
        return "F"
    if name in INNER_SHORT:
        return INNER_SHORT[name]
    return "B" if layer_id == 31 else None


def _seg_near(px, py, x0, y0, x1, y1):
    """Nearest point on a segment to a point, and the distance, in nm."""
    dx, dy = x1 - x0, y1 - y0
    span = float(dx * dx + dy * dy)
    t = 0.0 if span == 0.0 else max(0.0, min(1.0, ((px - x0) * dx
                                                   + (py - y0) * dy) / span))
    qx, qy = x0 + t * dx, y0 + t * dy
    return qx, qy, math.hypot(px - qx, py - qy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*",
                    help="default = every retained net with an open edge that "
                         "owns no pour")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--grid", type=int, default=50000,
                    help="the 3D corridor lattice, nm.  The LAUNCH is exact at "
                         "every value of this; only the haul is rasterised, and "
                         "a refusal carries the pitch it was refused at (D-651)")
    ap.add_argument("--max-mm", type=float, default=0.0,
                    help="skip a land whose nearest own-copper tap is further "
                         "than this (0 = no bound)")
    ap.add_argument("--pairs", type=int, default=3,
                    help="nearest tap sites offered per land, on distinct "
                         "objects")
    ap.add_argument("--stub-forbidden", default=",".join(STUB_FORBIDDEN),
                    help="netclasses refused by NAME under TAP4")
    ap.add_argument("--census", action="store_true",
                    help="MEASURE ONLY: report the pad gap and the own-copper "
                         "gap for every orphan land of every net and ask "
                         "nothing.  This is the cheap question that says which "
                         "lands are worth the expensive one")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, reserved_inner_planes,
                                  permitted_layers)

    forbidden = {x for x in a.stub_forbidden.split(",") if x}
    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    board = qb.b
    board.BuildConnectivity()
    conn = board.GetConnectivity()

    pour_nets = set()
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.IsFilled():
            pour_nets.add(z.GetNetname())

    nets = list(a.nets)
    if not nets:
        seen = []
        for net in sorted({p.GetNetname() for f in board.GetFootprints()
                           for p in f.Pads() if p.GetNetname()}):
            if net in pour_nets:
                continue
            try:
                if len(mz.net_islands(qb, net)) > 1:
                    seen.append(net)
            except Exception:
                continue
        nets = seen

    report, totals = [], {}
    for net in nets:
        t0 = time.time()
        c = net_contract(board, net)
        far = list(permitted_layers(qb.routable, c["layers"], reserved, net))
        rec = dict(net=net, netclass=c["netclass"], width=c["width"],
                   layers=far, lands=[], seconds=0.0)
        report.append(rec)
        if c["netclass"] in forbidden:
            rec["verdict"] = "STUB_FORBIDDEN"
            rec["why"] = ("TAP4: netclass %s governs the SHAPE of its "
                          "conductor; a T-junction is not asked for it"
                          % c["netclass"])
            totals["STUB_FORBIDDEN"] = totals.get("STUB_FORBIDDEN", 0) + 1
            print(" %-38s %s" % (net, rec["verdict"]), file=sys.stderr,
                  flush=True)
            continue

        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            rec["verdict"] = "CONNECTED"
            continue

        # TAP1.  Every track and via of this net, labelled with the ISLAND its
        # own cluster reaches.  A conductor whose cluster holds no pad of any
        # island is orphaned copper and is not a target.
        pad_island = {}
        for i, isl in enumerate(islands):
            for p in isl:
                pad_island[(p["ref"], int(p["x"]), int(p["y"]))] = i
        objects = []
        for tr in board.GetTracks():
            if tr.GetNetname() != net:
                continue
            owners = set()
            for item in conn.GetConnectedItems(tr):
                if item.GetClass() != "PAD":
                    continue
                fp = item.GetParentFootprint()
                if fp is None:
                    continue
                pos = item.GetPosition()
                key = (fp.GetReference() + "." + item.GetNumber(),
                       pos.x, pos.y)
                if key in pad_island:
                    owners.add(pad_island[key])
            if len(owners) != 1:
                continue
            island = owners.pop()
            if tr.GetClass() == "PCB_VIA":
                pos = tr.GetPosition()
                for layer in far:
                    objects.append(dict(island=island, kind="via", layer=layer,
                                        x0=pos.x, y0=pos.y, x1=pos.x,
                                        y1=pos.y,
                                        tag="via@%.3f,%.3f"
                                            % (pos.x / 1e6, pos.y / 1e6)))
                continue
            short = _short_layer(board, tr.GetLayer())
            if short is None or short not in far:
                continue
            s, e = tr.GetStart(), tr.GetEnd()
            objects.append(dict(island=island, kind="track", layer=short,
                                x0=s.x, y0=s.y, x1=e.x, y1=e.y,
                                tag="%s %.3f,%.3f-%.3f,%.3f"
                                    % (short, s.x / 1e6, s.y / 1e6,
                                       e.x / 1e6, e.y / 1e6)))
        rec["target_objects"] = len(objects)
        if not objects:
            rec["verdict"] = "NO_OWN_COPPER"
            continue

        field = None if a.census else mz.Field(
            qb, net, c["width"], c["clr_pad"], c["clr"],
            c["via_dia"], c["via_drill"], G=a.grid, layers=far)
        for i, isl in enumerate(islands):
            for p in isl:
                sites = []
                for o in objects:
                    if o["island"] == i:
                        continue
                    qx, qy, d = _seg_near(p["x"], p["y"], o["x0"], o["y0"],
                                          o["x1"], o["y1"])
                    sites.append((d, qx, qy, o))
                if not sites:
                    continue
                sites.sort(key=lambda t: t[0])
                nearest_pad = min(
                    (math.hypot(p["x"] - q["x"], p["y"] - q["y"])
                     for j, other in enumerate(islands) if j != i
                     for q in other), default=float("inf"))
                land = dict(land=p["ref"], island=i,
                            nearest_pad_mm=round(nearest_pad / 1e6, 4),
                            nearest_tap_mm=round(sites[0][0] / 1e6, 4),
                            tries=[])
                rec["lands"].append(land)
                land["gain_mm"] = round((nearest_pad - sites[0][0]) / 1e6, 4)
                if a.census:
                    land["verdict"] = "MEASURED"
                    totals["MEASURED"] = totals.get("MEASURED", 0) + 1
                    continue
                if a.max_mm and sites[0][0] / 1e6 > a.max_mm:
                    land["verdict"] = "OUT_OF_BOUND"
                    totals["OUT_OF_BOUND"] = totals.get("OUT_OF_BOUND", 0) + 1
                    continue
                used, verdict = set(), "NO_TAP"
                for d, qx, qy, o in sites:
                    if o["tag"] in used or len(used) >= max(1, a.pairs):
                        continue
                    used.add(o["tag"])
                    anchor = dict(ref="TAP", net=net, anchor=True,
                                  layer=o["layer"], x=int(round(qx)),
                                  y=int(round(qy)))
                    m0 = qb.mark()
                    try:
                        r = mz.offcentre_route(qb, field, p, anchor,
                                               width=c["width"], G=a.grid)
                    finally:
                        qb.revert(m0)
                    try_rec = dict(target=o["tag"], target_island=o["island"],
                                   layer=o["layer"],
                                   at=(round(qx / 1e6, 4), round(qy / 1e6, 4)),
                                   gap_mm=round(d / 1e6, 4),
                                   ok=bool(r.get("ok")),
                                   reason=r.get("reason"),
                                   why=r.get("why"),
                                   grid_nm=a.grid)
                    if r.get("ok"):
                        try_rec.update(mm=r.get("mm"), vias=r.get("vias"),
                                       layers=r.get("layers"),
                                       via_xy=r.get("via_xy"),
                                       stub_mm=r.get("stub_mm"),
                                       launches=r.get("launches"))
                        verdict = "TAP_ROUTABLE"
                    land["tries"].append(try_rec)
                    if r.get("ok"):
                        break
                land["verdict"] = verdict
                totals[verdict] = totals.get(verdict, 0) + 1
                print("  %-38s %-9s %-14s pad %7.3f  tap %7.3f  %s"
                      % (net, p["ref"], land["verdict"],
                         land["nearest_pad_mm"], land["nearest_tap_mm"],
                         (land["tries"] or [{}])[-1].get("reason") or ""),
                      file=sys.stderr, flush=True)
        # A CENSUS ASKS NOTHING, SO IT MUST READ THE SAME TWICE.  Wall clock is
        # not a property of the board; leaving it in a report that contains no
        # search would make the one thing this mode is for -- a diff against
        # the last board -- impossible to read.
        if not a.census:
            rec["seconds"] = round(time.time() - t0, 1)
        else:
            rec.pop("seconds", None)

    out = dict(schema=1, board=str(a.board), board_sha256=sha,
               grid_nm=a.grid, stub_forbidden=sorted(forbidden),
               question=("for every orphan land of every partially routed net, "
                         "is the net's OWN CONNECTED COPPER nearer than the "
                         "nearest pad the router may aim at -- and does a legal "
                         "corridor reach it"),
               method=("read-only; maze3d.offcentre_route to an anchor END "
                       "built from the target island's own connected copper, "
                       "proved by verify_laid in exact geometry and REVERTED"),
               limits=("TAP5: a TAP_ROUTABLE row is a work-list entry, not a "
                       "transaction -- no gate clause has been asked, the pour "
                       "partition least of all"),
               totals=totals, nets=report)
    text = json.dumps(out, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n")
    else:
        print(text)
    print(" totals %s" % json.dumps(totals, sort_keys=True), file=sys.stderr)


if __name__ == "__main__":
    main()
