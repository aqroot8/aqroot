#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: is this pour NECK a conductor, or a DFM liability?

D-655 promoted `/I2C_SCL_INT` alone because the JOINT run -- which closed BOTH
of `U2`'s bus lands and improved the board by two edges -- was refused by ONE
gate clause: `attributable_drc`, a `copper_sliver (B.Cu)` KiCad names with an
EMPTY item list.  `evidence/d655-sliver-forensics.json` re-derived the geometry
by hand and reached a conclusion no instrument in this directory could state:

    the `/01_POWER_TREE/BQ25185_SYS` `B.Cu` pour island survives a 0.075 mm
    erosion as ONE outline and breaks into TWO at 0.100 mm -- ITS OWN NECKS ARE
    ALREADY ABOUT 0.200 mm WIDE -- so ANY 0.200 mm track with 0.200 mm
    clearance laid beside one pinches it into a sliver.  An `r 0.5 mm` reserve
    aimed at the crumb MOVED the crumb rather than removing it.

That is a statement about a POUR, and the repository had no way to make it
except once, by hand, after a 10351 s gate run had already been spent.  This
screen is that reading, made mechanical and made GENERAL, because the finding
is not about one crumb: a pour whose own necks are at the track width is a
board-wide DFM liability, and every future route through its bbox pays the
same toll.

THE QUESTION, and why an erosion ladder alone does not answer it.

`evidence/d655-sliver-locate.py` erodes and dilates to find WHERE a pour is
thin.  Thinness is not the verdict.  A 0.2 mm neck that is the ONLY copper
joining two of the pour's own pads is a CONDUCTOR -- narrow, priced by
`.kicad_dru` section 5, and not to be touched by a router or a trim.  A 0.2 mm
neck whose far side holds NO pad, NO via and NO track of the net is DEAD
COPPER: it conducts nothing, it is the acid trap the sliver check exists to
find, and removing it is a pure improvement that also gives the pocket back.

Those two necks are geometrically indistinguishable.  They differ only in what
is on the far side, so that is what this screen resolves:

  * ISLANDS.  Every filled outline of the target zone, its area and bbox, and
    the net's own PADS, VIAS and TRACK endpoints that lie inside it.  Pads are
    resolved by geometry and never by ordinal, for `pour_bond_contract.py` P2's
    reason: one new island renumbers every ordinal above it.
  * THE LADDER.  For each radius `r`, erode the island, split it into connected
    COMPONENTS, and dilate each component back by `r` on its own so a land at
    the very edge is still attributed.  An island that becomes N components at
    radius `r` has necks about `2r` wide.
  * THE VERDICT, PER COMPONENT.  `LOAD_BEARING` if the component holds a pad,
    a via or a track of the net -- copper that joins something to something.
    `DEAD` if it holds none of the three: at this radius that lobe of the pour
    is attached to the rest of the island only through a neck narrower than
    `2r`, and it conducts nothing at either end.
  * THE BOTTLENECK, BISECTED (`--bisect`).  The ladder answers at the rungs it
    is given.  The number a POWER pour is judged by is a single one: the
    NARROWEST place on the widest path joining the island's own lands.  That is
    found by bisecting the erosion radius for the largest `r` at which every
    object the island holds is still in ONE component -- `bottleneck_mm = 2r`
    -- and it is compared against `--floor-mm`, the width `.kicad_dru`
    section 5 publishes for that net.  A pour is a conductor and KiCad DRC
    never checks its width; this is the only instrument on the board that does.
  * THE NECKS THEMSELVES.  `island - dilate(erode(island))` is exactly the
    material that does not survive the radius; its pieces are reported with
    bbox and centroid so a trim, a reserve or a keep-out can NAME one.

WHAT IT DOES NOT CLAIM.

  * It is READ-ONLY.  It loads the board, reads `GetFilledPolysList` and writes
    nothing.  A `DEAD` verdict is a PREDICTION about a trim, never a trim: only
    a real KiCad refill and the full gate settle whether removing that lobe
    keeps PP1-PP4 and the ledger.
  * ATTRIBUTION IS BY OVERLAP, NOT BY A CENTRE POINT, and that correction is
    not cosmetic.  `screen_pour_island_map.py` asks `PointInside` of a pad's
    CENTRE and states the limit; run that way, THIS screen called `U11.1` --
    the `BQ25185`'s own `SYS` land -- a `DEAD` 0.449 mm2 island, because the
    fill around a 0.75 x 0.20 mm land carved at 0.25 mm clearance is an ANNULUS
    and the centre falls in the carve-out.  A DEAD verdict is a licence to cut
    copper, so it is taken on the object's real SHAPE: pads by
    `GetEffectivePolygon`, barrels by their annulus, tracks by their swept
    outline, each intersected with the component.  Read this beside KiCad's
    connectivity, never instead of it.
  * A component is judged by what is INSIDE it on THIS layer.  A lobe holding
    nothing here may still be doing something on another layer through a barrel
    -- so vias are counted, and a lobe with a via is never called DEAD.
  * A NECK IS ONLY A BOTTLENECK IF THERE IS NO PARALLEL PATH, and on this board
    that distinction decides which findings are real.  `GND` and `+3V3` own
    RESERVED INNER PLANES (`In1`/`In4` and `In3`), so two lands either side of a
    0.113 mm neck in the `F.Cu` pour that each keep a barrel into `In3` carry
    their current through the PLANE and not through the neck -- exactly
    `checks/plane_return_path.py`'s reading, applied to the forward path.  A
    net that owns NO plane has no such relief: `.kicad_dru` section 5 says
    `SYS_MAIN` is OUTER-LAYER BY POLICY, so a `/01_POWER_TREE/BQ25185_SYS`
    `B.Cu` neck IS the whole conductor.  The verdict therefore names which case
    it is -- `UNDER_FLOOR` where the pour is the sole conductor,
    `UNDER_FLOOR_PLANE_PARALLEL` where a reserved plane is in parallel and the
    number is advisory.
  * Erosion is `CORNER_STRATEGY_ROUND_ALL_CORNERS` at the board's own
    `max_error`, the same call `d655-sliver-locate.py` used, so the two agree.

CROSS-CHECK IT AGAINST KiCad, BECAUSE THE EROSION IS A MODEL AND KiCad IS NOT.
Raise the zone's own `min_thickness`, refill with `kicad-cli pcb drc
--refill-zones --save-board`, and ask `GetConnectivity` which pads still share a
cluster.  The rung at which a pad FALLS OFF is the width of the copper that was
holding it, measured by the engine that will fill the board a fabricator gets.
D-656 ran that ladder on `B /01_POWER_TREE/BQ25185_SYS POUR 1`
(`evidence/d656-sys-neck-ampacity.json`): at 0.200 mm -- the board as it stands
-- `{C28.1, SW9.2, U12.1}` are ONE cluster; at 0.205 mm `C28.1` falls off; at
0.250 mm `U12.1` falls off `SW9.2`.  The bisect had said 0.197 mm.  The two
methods agree to a rung, and neither is the other's assumption.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

MAX_ERROR = 5000          # 0.005 mm, the board's own `rules.max_error`
CRUMB_MM2 = 0.0005        # numerical residue on every corner (d655-sliver-locate)


def _mm(v):
    return round(v / 1e6, 3)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _unit_sets(ps):
    """The connected polygons of `ps`, each as its own SHAPE_POLY_SET."""
    return [ps.UnitSet(i) for i in range(ps.OutlineCount())]


def _area(ps):
    return ps.Area() / 1e12


def _bbox(ps):
    bb = ps.BBox()
    return [_mm(bb.GetLeft()), _mm(bb.GetTop()),
            _mm(bb.GetRight()), _mm(bb.GetBottom())]


def _track_poly(t, layer):
    sp = pcbnew.SHAPE_POLY_SET()
    t.TransformShapeToPolySet(sp, layer, 0, MAX_ERROR, pcbnew.ERROR_INSIDE)
    return sp


def _overlaps(island, shape):
    """Does `shape` share any copper with `island`?  Shapes, never centres."""
    x = pcbnew.SHAPE_POLY_SET(shape)
    x.BooleanIntersection(island)
    x.Simplify()
    return x.Area() > 0


def _eroded_components(ps, r):
    """Erode by `r`, split, dilate each piece back on its own."""
    er = pcbnew.SHAPE_POLY_SET(ps)
    er.Inflate(-r, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAX_ERROR)
    er.Simplify()
    out = []
    for piece in _unit_sets(er):
        if _area(piece) < CRUMB_MM2:
            continue
        back = pcbnew.SHAPE_POLY_SET(piece)
        back.Inflate(r, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAX_ERROR)
        back.Simplify()
        back.BooleanIntersection(ps)      # never claim copper the island lacks
        back.Simplify()
        out.append(back)
    return out


def _thin_material(ps, r):
    """`island - dilate(erode(island))`: what does NOT survive radius r."""
    er = pcbnew.SHAPE_POLY_SET(ps)
    er.Inflate(-r, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAX_ERROR)
    er.Simplify()
    back = pcbnew.SHAPE_POLY_SET(er)
    back.Inflate(r, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAX_ERROR)
    back.Simplify()
    diff = pcbnew.SHAPE_POLY_SET(ps)
    diff.BooleanSubtract(back)
    diff.Simplify()
    pieces = []
    for piece in _unit_sets(diff):
        a = _area(piece)
        if a < CRUMB_MM2:
            continue
        bb = piece.BBox()
        pieces.append({
            "area_mm2": round(a, 5),
            "bbox_mm": _bbox(piece),
            "centre_mm": [_mm((bb.GetLeft() + bb.GetRight()) / 2),
                          _mm((bb.GetTop() + bb.GetBottom()) / 2)],
            "size_mm": [_mm(bb.GetRight() - bb.GetLeft()),
                        _mm(bb.GetBottom() - bb.GetTop())],
        })
    pieces.sort(key=lambda p: -p["area_mm2"])
    return pieces


def _net_objects(board, netname, layer):
    """Every PAD, VIA and TRACK end of `netname` that could sit on `layer`."""
    pads, vias, tracks = [], [], []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != netname or not pad.IsOnLayer(layer):
                continue
            pads.append(("%s.%s" % (fp.GetReference(), pad.GetNumber()),
                         pcbnew.SHAPE_POLY_SET(pad.GetEffectivePolygon(layer))))
    for t in board.GetTracks():
        if t.GetNetname() != netname:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            if t.IsOnLayer(layer):
                p = t.GetPosition()
                vias.append(("via@%.3f,%.3f" % (p.x / 1e6, p.y / 1e6),
                             _track_poly(t, layer)))
        elif t.GetLayer() == layer:
            tracks.append(("trk@%.3f,%.3f" % (t.GetStart().x / 1e6,
                                              t.GetStart().y / 1e6),
                           _track_poly(t, layer)))
    return pads, vias, tracks


def _hold(ps, items):
    return [name for name, shape in items if _overlaps(ps, shape)]


args_bisect = [False]
floor_mm = 0.0


def analyse(board_path, net_filter, layer_filter, radii, zone_filter):
    board = pcbnew.LoadBoard(str(board_path))
    report = {
        "schema": 1,
        "board": str(board_path),
        "board_sha256": _sha(board_path),
        "radii_mm": [r / 1e6 for r in radii],
        "zones": [],
    }
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        net = z.GetNetname()
        if net_filter and net_filter not in net:
            continue
        if zone_filter and zone_filter not in z.GetZoneName():
            continue
        for lay in z.GetLayerSet().CuStack():
            lname = board.GetLayerName(lay)
            if layer_filter and lname != layer_filter:
                continue
            ps = z.GetFilledPolysList(lay)
            if ps.OutlineCount() == 0:
                continue
            pads, vias, tracks = _net_objects(board, net, lay)
            # does this net own a filled zone on a RESERVED INNER plane?  If it
            # does, a neck in THIS outer pour is not the whole conductor.
            plane_layers = sorted(
                board.GetLayerName(pl)
                for other in board.Zones()
                if (not other.GetIsRuleArea()
                    and other.GetNetname() == net)
                for pl in other.GetLayerSet().CuStack()
                if (pl not in (pcbnew.F_Cu, pcbnew.B_Cu)
                    and other.GetFilledPolysList(pl).OutlineCount() > 0))
            zrep = {
                "zone": z.GetZoneName(),
                "net": net,
                "layer": lname,
                "min_thickness_mm": _mm(z.GetMinThickness()),
                "island_removal_mode": int(z.GetIslandRemovalMode()),
                "islands": [],
            }
            for i, isl in enumerate(_unit_sets(ps)):
                a = _area(isl)
                if a < CRUMB_MM2:
                    continue
                irep = {
                    "island": i,
                    "area_mm2": round(a, 4),
                    "bbox_mm": _bbox(isl),
                    "pads": _hold(isl, pads),
                    "vias": len(_hold(isl, vias)),
                    "tracks": len(_hold(isl, tracks)),
                    "ladder": [],
                }
                if args_bisect[0]:
                    held = ([it for it in pads if _overlaps(isl, it[1])]
                            + [it for it in vias if _overlaps(isl, it[1])]
                            + [it for it in tracks if _overlaps(isl, it[1])])
                    bn = bottleneck(isl, held)
                    irep["held_objects"] = len(held)
                    irep["bottleneck_mm"] = bn
                    if bn is not None and floor_mm:
                        irep["floor_mm"] = floor_mm
                        irep["plane_parallel"] = plane_layers
                        if bn >= floor_mm:
                            irep["floor_verdict"] = "OK"
                        elif plane_layers:
                            irep["floor_verdict"] = "UNDER_FLOOR_PLANE_PARALLEL"
                        else:
                            irep["floor_verdict"] = "UNDER_FLOOR"
                for r in radii:
                    comps = _eroded_components(isl, r)
                    crep = []
                    for c in comps:
                        cp = _hold(c, pads)
                        cv = _hold(c, vias)
                        ct = _hold(c, tracks)
                        crep.append({
                            "area_mm2": round(_area(c), 4),
                            "bbox_mm": _bbox(c),
                            "pads": cp,
                            "vias": len(cv),
                            "tracks": len(ct),
                            "verdict": ("LOAD_BEARING" if (cp or cv or ct)
                                        else "DEAD"),
                        })
                    crep.sort(key=lambda c: -c["area_mm2"])
                    irep["ladder"].append({
                        "r_mm": r / 1e6,
                        "neck_width_mm": round(2 * r / 1e6, 4),
                        "components": len(crep),
                        "dead_components": sum(1 for c in crep
                                               if c["verdict"] == "DEAD"),
                        "dead_area_mm2": round(sum(c["area_mm2"] for c in crep
                                                   if c["verdict"] == "DEAD"), 4),
                        "detail": crep,
                        "thin_material": _thin_material(isl, r),
                    })
                zrep["islands"].append(irep)
            zrep["islands"].sort(key=lambda x: -x["area_mm2"])
            report["zones"].append(zrep)
    return report


def bottleneck(island, items, lo=0, hi=600000, tol=2500):
    """Largest `r` at which every held object is still in ONE component.

    `bottleneck_mm = 2r`: the narrowest place on the widest path joining this
    island's own lands.  Bisection, because the ladder answers only at the
    rungs it is handed and a conductor is judged by one number.
    """
    def joined(r):
        if r <= 0:
            return True
        comps = _eroded_components(island, r)
        for c in comps:
            if len(_hold(c, items)) == len(items):
                return True
        return False

    if len(items) < 2:
        return None
    if not joined(lo + tol):
        return 0.0
    while hi - lo > tol:
        mid = (lo + hi) // 2
        if joined(mid):
            lo = mid
        else:
            hi = mid
    return round(2 * lo / 1e6, 4)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("--net", default=None,
                    help="substring of the pour's net name")
    ap.add_argument("--layer", default=None, help="exact layer name, e.g. B.Cu")
    ap.add_argument("--zone", default=None, help="substring of the zone name")
    ap.add_argument("--radii", default="0.050,0.075,0.100,0.125,0.150",
                    help="erosion radii in mm; a neck broken at r is ~2r wide")
    ap.add_argument("--top", type=int, default=6,
                    help="islands to print per zone")
    ap.add_argument("--bisect", action="store_true",
                    help="bisect each island's BOTTLENECK neck width")
    ap.add_argument("--floor-mm", type=float, default=0.0,
                    help="the width .kicad_dru section 5 publishes for this "
                         "net; a load-bearing neck under it is a conductor "
                         "the board's own rule would refuse as a track")
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    args_bisect[0] = args.bisect
    globals()["floor_mm"] = args.floor_mm

    radii = [int(round(float(x) * 1e6)) for x in args.radii.split(",") if x]
    rep = analyse(Path(args.board), args.net, args.layer, radii, args.zone)

    for z in rep["zones"]:
        print("ZONE %-38s %-24s %-6s  min_thickness %.3f mm"
              % (z["zone"][:38], z["net"][:24], z["layer"],
                 z["min_thickness_mm"]))
        for isl in z["islands"][:args.top]:
            print("  island %-3d area %9.4f mm2  bbox %s"
                  % (isl["island"], isl["area_mm2"], isl["bbox_mm"]))
            print("      holds %d pads, %d vias, %d tracks%s"
                  % (len(isl["pads"]), isl["vias"], isl["tracks"],
                     ("   " + ",".join(isl["pads"][:8])) if isl["pads"] else ""))
            if "bottleneck_mm" in isl:
                bn = isl["bottleneck_mm"]
                print("      BOTTLENECK %s over %d held object(s)   %s"
                      % ("n/a" if bn is None else "%.3f mm" % bn,
                         isl["held_objects"], isl.get("floor_verdict", "")))
            for rung in isl["ladder"]:
                flag = "" if rung["dead_components"] == 0 else \
                    "   <== %d DEAD lobe(s), %.4f mm2" % (
                        rung["dead_components"], rung["dead_area_mm2"])
                print("      neck %.3f mm -> %d component(s)%s"
                      % (rung["neck_width_mm"], rung["components"], flag))
                for c in rung["detail"]:
                    if c["verdict"] == "DEAD" or rung["components"] > 1:
                        print("          %-12s %8.4f mm2  bbox %s  pads %d vias %d trk %d"
                              % (c["verdict"], c["area_mm2"], c["bbox_mm"],
                                 len(c["pads"]), c["vias"], c["tracks"]))
        print()

    if args.json:
        Path(args.json).write_text(json.dumps(rep, indent=1, sort_keys=True))
        print("wrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
