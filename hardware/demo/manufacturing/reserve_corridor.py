#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- RESERVE A CORRIDOR THE ROUTER ACTUALLY HONOURS.

`aqroot-Beta-v2.kicad_dru` section 6 reserves `F.Cu` over `In1` for the USB 2.0
pair -- in WORDS.  Nothing in this tool chain ever enforced that on a router, so
every whole-board maze batch since has been free to lay copper in the lane, and
has: D-599 counted **44 foreign `F.Cu` nets holding copper inside the USB
window** and recorded the consequence, a link whose MCU half the contract note
records at 22.771 / 22.344 mm with two barrels and which today reads `NO_PATH`.
That is not a static wall, it is a TREND, and a corridor recovered and not
reserved is lost again by the next batch.

THE RESERVATION IS THE SAME OBJECT AS A POUR-BOND TUBE.  `maze3d.Field` already
takes `guard={layer: [(x, y, keepout_nm), ...]}` and re-applies it on every
`rebuild_blk`, so a lane is expressible today as points with a keep-out radius.
Exactly two things were missing and this file is one of them:

  * an EMITTER that samples a reserved centreline, and
  * an `exempt` LIST on a guard record.  `route_maze_batch.guard_for` exempts
    the single net a record names, which is right for a bond tube -- the tube is
    that pour's own copper -- and wrong for a corridor, because a corridor is
    reserved for a FAMILY.  `USB_D_CONN_N` must be as free to run down the USB
    lane as `USB_D_CONN_P` is.  That half lives in `route_maze_batch.py`.

THREE MODES.  The first two are the difference between reserving a plan and
reserving a fact; the third is for a lane that is neither -- a lane that is the
ABSENCE of foreign copper, which a pour-served rail has and a routed link never
does.

  PROSPECTIVE (default).  The centreline is the Euclidean MST over the
  CENTROIDS of the named nets' pad clusters -- the lane the link wants, drawn
  before it exists.  This is what a rip-up-and-reroute transaction needs: the
  family routes first and is exempt, the evicted nets are re-proposed after and
  are not, so they rebuild AROUND the lane instead of back through it.  A
  straight centreline is a claim, not a measurement: it can cross a pad or a
  keep-out, and a reservation the router cannot honour would simply make the
  re-proposed nets `NO_PATH`.  Clause 4 of the gate is what judges that, and it
  is why `--half-width-mm` should be the lane the pair actually owes and not a
  wish.

  RETROSPECTIVE (`--from-copper`).  The centreline is the net's OWN ROUTED
  TRACKS on the named layers -- reserve what you won.  A track already on the
  board is by construction a lane the router could take, so this mode cannot
  reserve the impossible, and it is the mode that stops the bleeding on any
  route worth keeping: emit it once after a promotion and hand it to every
  later batch as `--guard`.

  STATED (`--lane`, D-660).  The centreline is GIVEN, in millimetres, exactly
  as D-655's `--evict-window` states an eviction corridor instead of deriving
  it from a pad bounding box.  `/01_POWER_TREE/BQ25185_SYS` is why: it owns
  thirteen pads over 105 mm, so its PROSPECTIVE MST reserves lanes across the
  whole board, and it owns no track at `U11` at all, so RETROSPECTIVE reserves
  nothing there -- the lane the charger's `SYS` output needs is the space three
  FOREIGN objects occupy, and the only honest way to name it is to measure it
  and say so.  A one-point lane reserves a DISC, which is what a barrel's site
  is.

Nothing here writes the board or promotes copper.  Output is a guard spec in
`pour_bond_guard.py`'s own shape, so `route_maze_batch.py --guard` consumes it
unchanged, and `--merge` concatenates an existing spec so a run carries the
pour-bond guard and its corridor reservations in ONE file.
"""

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

# KiCad layer name -> the key `maze3d.Field.guard` and `qrouter` use.
LKEY = {"F.Cu": "F", "B.Cu": "B", "In2.Cu": "I2", "In3.Cu": "I3"}

# Single-linkage radius for grouping a net's pads into TERMINALS.  A USB-C
# receptacle's four data lands span 1.5 mm and sit 8 mm from the ESD part they
# feed; 3 mm separates those two facts and merges neither pair of parts.
CLUSTER_MM = 3.0
# Centreline sample step.  The mask each point stamps is a disc of at least
# `keepout + width/2 + one lattice cell`, an order of magnitude wider, so this
# only has to be fine enough that two adjacent discs overlap.
STEP_MM = 0.1


def cluster(points, radius):
    """Single-linkage clusters of (x, y) points at `radius` nm."""
    todo = list(range(len(points)))
    out = []
    while todo:
        seed = todo.pop(0)
        group = [seed]
        grew = True
        while grew:
            grew = False
            for k in list(todo):
                if any(math.hypot(points[k][0] - points[g][0],
                                  points[k][1] - points[g][1]) <= radius
                       for g in group):
                    group.append(k)
                    todo.remove(k)
                    grew = True
        out.append(group)
    return out


def mst_edges(nodes):
    """Euclidean MST over (x, y) nodes -- Prim, tiny N.

    The same primitive `pour_bond_guard.mst_edges` uses, and deliberately so:
    a corridor over three terminals is a TREE, not a chain, and a chain would
    reserve a lane the link does not want.
    """
    n = len(nodes)
    if n < 2:
        return []
    used, rest, out = [0], list(range(1, n)), []
    while rest:
        best = None
        for u in used:
            for v in rest:
                d = math.hypot(nodes[u][0] - nodes[v][0],
                               nodes[u][1] - nodes[v][1])
                if best is None or d < best[0]:
                    best = (d, u, v)
        out.append((best[1], best[2]))
        used.append(best[2])
        rest.remove(best[2])
    return out


def sample(a, b, step):
    """Points every `step` nm along the segment a->b, both ends included."""
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    if d <= 0:
        return [(a[0], a[1])]
    n = max(1, int(math.ceil(d / float(step))))
    return [(a[0] + (b[0] - a[0]) * t / float(n),
             a[1] + (b[1] - a[1]) * t / float(n)) for t in range(n + 1)]


def net_pads(board, nets):
    """[(x, y, 'REF.NUM', net)] for every pad of the named nets."""
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if not p.GetNumber() or p.GetNetname() not in nets:
                continue
            pos = p.GetPosition()
            out.append((pos.x, pos.y,
                        "%s.%s" % (f.GetReference(), p.GetNumber()),
                        p.GetNetname()))
    return out


def stated(lanes, layers, step):
    """One guard record per STATED polyline -- D-660.

    D-667: A LANE MAY STATE ITS OWN LAYERS, and a lane that is a ROUTE must.
    `layers` here is the run-wide default and every lane took it, so a lane
    drawn along a route's five via points was reserved on `F.Cu`, `B.Cu` AND
    `In2.Cu` for its whole length -- 93.561 mm of reservation for a 35.342 mm
    route.  A route occupies exactly ONE layer between two of its barrels, and
    the other two are the only way a net it evicted can ever cross it: reserve
    all three and the crossing is impossible, which is what D-666 arms D and E
    measured as `NO_PATH` on both relays.  A lane entry may therefore carry its
    own layer list, and one that does not reads exactly as it did.

    THE THIRD MODE, AND THE ONE A POUR-SERVED RAIL NEEDS.  Prospective draws
    the MST over a family's pad-cluster centroids and retrospective samples the
    family's own routed tracks.  Neither can express the lane a POUR wants:
    `/01_POWER_TREE/BQ25185_SYS` owns thirteen pads spread over 105 mm, so its
    prospective MST reserves lanes across the whole board, and the lane that
    matters at `U11` is not the family's copper -- it is the ABSENCE of three
    FOREIGN objects, measured on a probe board KiCad's own `ZONE_FILLER` refills.

    So the lane is STATED in millimetres, exactly as D-655's `--evict-window`
    states an eviction corridor instead of deriving it from a pad bounding box.
    This is a RESTRICTION on foreign copper and never a licence: it reserves
    nothing to the family that the family did not already own, it writes no
    board and it relaxes no rule.  What makes a stated lane honest is that its
    coordinates are a MEASUREMENT -- name the objects the cut-blame screen
    named, and reserve where they lay.
    """
    recs = []
    for i, lane in enumerate(lanes):
        pts_mm, lane_layers = lane if isinstance(lane, tuple) else (lane, None)
        use = lane_layers or layers
        nodes = [(int(round(x * 1e6)), int(round(y * 1e6))) for (x, y) in pts_mm]
        pts, mm = [], 0.0
        if len(nodes) == 1:
            pts = [nodes[0]]
        for k in range(len(nodes) - 1):
            a, b = nodes[k], nodes[k + 1]
            mm += math.hypot(b[0] - a[0], b[1] - a[1]) / 1e6
            for p in sample(a, b, step):
                pts.append((p[0], p[1]))
        for L in use:
            recs.append(dict(lkey=LKEY[L], layer=L, mode="stated",
                             ends=["lane %d" % (i + 1),
                                   " ".join("%.4f,%.4f" % p for p in pts_mm)],
                             mm=round(mm, 3),
                             points=[[int(round(x)), int(round(y))]
                                     for (x, y) in pts]))
    return recs


def prospective(board, nets, layers, step, cluster_nm):
    """One guard record per MST edge over the family's pad-cluster centroids."""
    pads = net_pads(board, nets)
    if len(pads) < 2:
        raise SystemExit("reserve: %s own fewer than two pads on this board"
                         % ", ".join(sorted(nets)))
    groups = cluster([(p[0], p[1]) for p in pads], cluster_nm)
    nodes, labels = [], []
    for g in groups:
        nodes.append((sum(pads[k][0] for k in g) / float(len(g)),
                      sum(pads[k][1] for k in g) / float(len(g))))
        labels.append(sorted(pads[k][2] for k in g))
    recs = []
    for (u, v) in mst_edges(nodes):
        pts = sample(nodes[u], nodes[v], step)
        for L in layers:
            recs.append(dict(lkey=LKEY[L], layer=L, mode="prospective",
                             ends=[labels[u], labels[v]],
                             mm=round(math.hypot(nodes[v][0] - nodes[u][0],
                                                 nodes[v][1] - nodes[u][1])
                                      / 1e6, 3),
                             points=[[int(round(x)), int(round(y))]
                                     for (x, y) in pts]))
    return recs


def retrospective(board, nets, layers, step):
    """One guard record per ROUTED TRACK of the family on the named layers.

    Vias are deliberately NOT sampled.  A barrel is a point on every layer and
    reserving it would keep foreign copper off five layers to protect one, which
    is a cost the reservation never agreed to pay; the track segments that reach
    it already reserve the lane that matters.
    """
    want = {LKEY[L]: L for L in layers}
    recs = []
    for t in board.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() not in nets:
            continue
        lname = board.GetLayerName(t.GetLayer())
        if lname not in want.values():
            continue
        a = (t.GetStart().x, t.GetStart().y)
        b = (t.GetEnd().x, t.GetEnd().y)
        recs.append(dict(lkey=LKEY[lname], layer=lname, mode="from-copper",
                         ends=[t.GetNetname()],
                         mm=round(math.hypot(b[0] - a[0], b[1] - a[1]) / 1e6, 3),
                         track_width=t.GetWidth(),
                         points=[[int(round(x)), int(round(y))]
                                 for (x, y) in sample(a, b, step)]))
    if not recs:
        raise SystemExit("reserve --from-copper: %s carry no routed track on "
                         "%s; there is nothing won to reserve"
                         % (", ".join(sorted(nets)), ", ".join(layers)))
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--net", action="append", default=[], required=True,
                    metavar="NET",
                    help="a net of the FAMILY the corridor is reserved for; "
                         "repeatable.  Every named net is exempt from the "
                         "reservation, which is the whole point of --exempt "
                         "existing on the record at all")
    ap.add_argument("--layer", action="append", default=[], metavar="F.Cu",
                    help="copper layer to reserve on; repeatable "
                         "(default F.Cu)")
    ap.add_argument("--half-width-mm", type=float, required=True,
                    help="half the lane the family owes itself: for a pair at "
                         "0.25 mm track and a 0.20 mm gap that is 0.35")
    ap.add_argument("--clearance-mm", type=float, default=0.20,
                    help="clearance a FOREIGN net owes the lane's outer edge; "
                         "the router adds that net's own half-width and one "
                         "lattice cell on top, exactly as it does for a "
                         "pour-bond tube")
    ap.add_argument("--from-copper", action="store_true",
                    help="RETROSPECTIVE: reserve the family's own routed "
                         "tracks instead of a straight centreline -- reserve "
                         "what you won")
    ap.add_argument("--cluster-mm", type=float, default=CLUSTER_MM,
                    help="single-linkage radius grouping pads into terminals "
                         "(prospective mode only)")
    ap.add_argument("--step-mm", type=float, default=STEP_MM)
    ap.add_argument("--exempt", action="append", default=[], metavar="NET",
                    help="an ADDITIONAL net the reservation does not bind, "
                         "beyond the --net family itself")
    ap.add_argument("--lane", action="append", default=[],
                    metavar="X0,Y0 X1,Y1 ...",
                    help="D-660: STATE the lane in millimetres as a polyline "
                         "instead of deriving it from the family's pads or "
                         "tracks; repeatable, one record per lane.  A single "
                         "point reserves a DISC, which is what a barrel's site "
                         "is.  Use it when the lane is the absence of foreign "
                         "copper rather than the presence of the family's own "
                         "-- a pour-served rail has no centreline to reserve.  "
                         "D-667: prefix `F.Cu:` (or `F.Cu+B.Cu:`) to reserve "
                         "THAT lane on those layers instead of the run-wide "
                         "--layer set.  A route occupies one layer between two "
                         "of its barrels and the other layers are the only way "
                         "a net it evicted can cross it")
    ap.add_argument("--label", default="corridor")
    ap.add_argument("--merge", type=Path,
                    help="concatenate this guard spec's records into the "
                         "output, so one --guard file carries the pour-bond "
                         "guard AND the reservations")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    sys.path.insert(0, str(HERE))
    from route_maze_batch import sha256_file

    layers = a.layer or ["F.Cu"]
    bad = [L for L in layers if L not in LKEY]
    if bad:
        ap.error("not a routable copper layer: %s" % ", ".join(bad))
    if a.from_copper and a.cluster_mm != CLUSTER_MM:
        ap.error("--cluster-mm has no meaning with --from-copper: that mode "
                 "samples real tracks, it does not group pads")
    if a.lane and a.from_copper:
        ap.error("--lane STATES the lane and --from-copper MEASURES it off the "
                 "family's own tracks; a run is one mode or the other")
    lanes = []
    for text in a.lane:
        # D-667.  A LANE MAY NAME ITS OWN LAYERS.  Everything before a `:` is a
        # layer list; without one the lane takes the run-wide --layer set and
        # this parse is the D-660 parse exactly.
        lane_layers = None
        if ":" in text:
            head, text = text.split(":", 1)
            lane_layers = [t for t in head.replace("+", " ").replace(",", " ")
                           .split() if t]
            bad_l = [L for L in lane_layers if L not in LKEY]
            if bad_l or not lane_layers:
                ap.error("--lane layer prefix %r names no routable copper "
                         "layer" % head)
        pts = []
        for tok in text.replace(",", " ").split():
            pts.append(float(tok))
        if len(pts) < 2 or len(pts) % 2:
            ap.error("--lane %r is not a list of x,y pairs in mm" % text)
        lanes.append(([(pts[i], pts[i + 1]) for i in range(0, len(pts), 2)],
                      lane_layers))

    import pcbnew
    board = pcbnew.LoadBoard(str(a.board))
    nets = set(a.net)
    missing = sorted(n for n in nets if board.FindNet(n) is None)
    if missing:
        raise SystemExit("no such net(s): %s" % ", ".join(missing))

    step = int(round(a.step_mm * 1e6))
    keepout = int(round((a.half_width_mm + a.clearance_mm) * 1e6))
    if a.lane:
        recs = stated(lanes, layers, step)
    elif a.from_copper:
        recs = retrospective(board, nets, layers, step)
    else:
        recs = prospective(board, nets, layers, step,
                           int(round(a.cluster_mm * 1e6)))

    # EVERY member of the family is exempt, and the record's `net` field is one
    # of them only because `guard_for` already skips a record whose `net` equals
    # the net being routed.  The exemption that does the work is the LIST.
    exempt = sorted(nets | set(a.exempt))
    for i, r in enumerate(recs):
        r.update(ok=True, kind="corridor", label=a.label,
                 net=exempt[0], exempt=exempt,
                 keepout_radius=keepout, index=i)

    merged, merge_src = [], None
    if a.merge:
        other = json.loads(a.merge.read_text())
        merged = list(other.get("guards", ()))
        merge_src = dict(spec=str(a.merge), sha256=sha256_file(a.merge),
                         guards=len(merged))

    doc = dict(schema=1, board=str(a.board), board_sha256=sha256_file(a.board),
               kind="corridor-reservation", label=a.label,
               mode=("stated" if a.lane else
                     "from-copper" if a.from_copper else "prospective"),
               lanes=[dict(points=pl, layers=ll or layers)
                      for (pl, ll) in lanes] or None,
               layers=layers, family=sorted(nets), exempt=exempt,
               half_width_mm=a.half_width_mm, clearance_mm=a.clearance_mm,
               keepout_radius=keepout, step_mm=a.step_mm,
               cluster_mm=(None if (a.from_copper or a.lane)
                           else a.cluster_mm),
               merged_from=merge_src,
               summary=dict(corridors=len(recs), merged_guards=len(merged),
                            mm=round(sum(r["mm"] for r in recs), 3),
                            points=sum(len(r["points"]) for r in recs)),
               guards=recs + merged)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for r in recs:
        print("  %-5s %-12s %7.3f mm  %4d pts  %s"
              % (r["lkey"], r["mode"], r["mm"], len(r["points"]),
                 " -> ".join(",".join(e) if isinstance(e, list) else str(e)
                             for e in r["ends"])),
              file=sys.stderr)
    print("  keepout radius %.3f mm; exempt: %s"
          % (keepout / 1e6, ", ".join(exempt)), file=sys.stderr)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
