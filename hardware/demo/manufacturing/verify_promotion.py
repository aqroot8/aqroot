#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- re-prove a promotion from the two board files ALONE.

`route_maze_batch.py` gates its own candidate before it writes it.  That is
necessary but it is not independent: the same process that proposed the copper
decided it was legal.  This module re-derives every promotion property a second
time, from the committed board and the promoted board, without reading the
driver's scratch tree, its ledger or its evidence JSON:

  * NO pre-existing track or via was moved or removed;
  * every ADDED object lies on one of the nets the promotion claimed;
  * every added track meets the width the caller asserts -- or, if it is
    narrower, is a DRU-LICENSED pad-escape neck: at least the necking minimum
    AND lying wholly inside one of the courtyards the `.kicad_dru` rule names,
    proved with the same `maze3d.Neck` the router was confined by;
  * every added via meets the drill and annular-ring floors it asserts -- or,
    with `--bridge`, is a DRU-LICENSED POUR BRIDGE: a barrel whose whole
    footprint lies inside a rule area the `.kicad_dru` names for its net, and
    which meets every minimum that rule states;
  * the rule-area inventory changed by exactly the licence areas the caller
    asserts, none was lost, and every added one forbids nothing;
  * the zone inventory changed by exactly the pours the caller asserts, and no
    surviving zone's net, layer, outline or fill parameters changed;
  * real KiCad `--refill-zones --save-board --severity-all --schematic-parity`
    DRC on the promoted board reports only the inherited classes, with ZERO
    attributable violations and ZERO schematic-parity errors;
  * the promoted board is fill-stable -- a second refill changes nothing;
  * the retained safety rules are still live text in the `.kicad_dru`.

It is read-only with respect to `hardware/demo/kicad/aqroot-demo/`: both boards
it inspects are copies in a temporary directory.
"""

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
SUFFIXES = (".kicad_pcb", ".kicad_dru", ".kicad_pro")

# The three report classes this board has carried since long before the maze
# router existed; they are inherited, not attributable to any promotion.
INHERITED = {"lib_footprint_issues": 199, "hole_clearance": 5,
             "solder_mask_bridge": 1}

# Retained contracts that must still be LIVE RULE TEXT, not merely believed.
DRU_CONTRACTS = {
    "D-269_bat_main_routed_clearance": "BAT_MAIN routed clearance",
    "D-186_bat_main_class": "BAT_MAIN",
    "annular_ring_floor": "annular_width (min 0.125mm)",
    "power_via_drill_floor": "POWER-class vias use the 0.40 mm drill",
}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def objects(path):
    """Every track and via as a geometry signature, independent of its UUID."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = set()
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            out.add(("via", t.GetNetname(), t.GetStart().x, t.GetStart().y,
                     t.GetWidth(), t.GetDrill()))
        else:
            out.add(("trk", t.GetNetname(), board.GetLayerName(t.GetLayer()),
                     t.GetStart().x, t.GetStart().y,
                     t.GetEnd().x, t.GetEnd().y, t.GetWidth()))
    return out


def zone_sigs(path):
    """Every non-rule-area pour's net, layers, name, fill parameters, outline."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        o = z.Outline().Outline(0)
        out.append((z.GetNetname(),
                    tuple(board.GetLayerName(l) for l in z.GetLayerSet().Seq()),
                    z.GetZoneName(), z.GetMinThickness(), z.GetLocalClearance(),
                    int(z.GetIslandRemovalMode()), int(z.GetPadConnection()),
                    tuple((o.CPoint(i).x, o.CPoint(i).y)
                          for i in range(o.PointCount()))))
    return sorted(out)


def drc(path, out):
    """Real KiCad DRC, refilling and saving the copy it is handed."""
    subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(out), str(path),
    ], text=True, capture_output=True)
    report = json.loads(Path(out).read_text())
    counts = {}
    for v in report.get("violations", []):
        counts[v["type"]] = counts.get(v["type"], 0) + 1
    return dict(
        counts=counts,
        attributable=[v for v in report.get("violations", [])
                      if v["type"] not in INHERITED],
        schematic_parity_errors=len(report.get("schematic_parity", [])),
        unconnected_items=len(report.get("unconnected_items", [])))


def neck_proof(path, tracks, floor):
    """Which added tracks are narrower than `floor`, and are they licensed?

    A plane stitch out of a fine-pitch power package launches at the
    `.kicad_dru` "Pad-escape necking - width" minimum, not at the class floor,
    and D-594's `U9.1` barrel is the first promotion to carry one.  Asserting
    the class floor and watching it fail says nothing useful; LOWERING the
    asserted floor to the neck says nothing at all, because it would then admit
    a 0.20 mm segment anywhere on the board.

    So a narrow segment is admitted only on the terms the board's own rule
    grants it: at least the necking minimum, and lying wholly inside one of the
    courtyards that rule NAMES.  Containment is proved by `maze3d.Neck` -- the
    same class, read from the same `.kicad_dru`, that confined the search --
    and on the CONTINUOUS segment, not merely its endpoints, because KiCad
    matches a rule against the copper and a straight run between two inside
    points can still bulge across a re-entrant courtyard edge.

    Returns (ok, detail).  With no narrow track at all this is vacuously true
    and reports so, which is what every prior promotion will report.
    """
    narrow = [x for x in tracks if floor and x[7] < floor]
    if not narrow:
        return True, dict(narrow_tracks=0, licensed=0, neck=None)
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
    import pcbnew
    import maze3d as mz
    board = pcbnew.LoadBoard(str(path))

    class _Shim(object):                 # `neck_rule` reads only `qb.b`
        pass
    shim = _Shim()
    shim.b = board
    neck = mz.neck_rule(shim)
    detail = dict(narrow_tracks=len(narrow),
                  neck=(dict(min_width_nm=neck.min_w, refs=list(neck.refs))
                        if neck else None),
                  strays=[])
    if neck is None:
        return False, detail
    ok = True
    for x in narrow:
        _k, net, layer, x0, y0, x1, y1, w = x
        outside = neck.outside([(x0, y0), (x1, y1)])
        if w < neck.min_w or outside > 0:
            ok = False
            detail["strays"].append(dict(net=net, layer=layer, width_nm=w,
                                         start=[x0, y0], end=[x1, y1],
                                         outside_nm=round(outside, 1)))
    detail["licensed"] = len(narrow) - len(detail["strays"])
    return ok, detail


def bridge_proof(path, vias, drill_floor, annular_floor):
    """Which added vias are below a floor, and are they DRU-LICENSED bridges?

    A pour bridge is one through barrel dropped inside a pad's own severed
    piece of pour, where no ordinary barrel fits.  Three of them on this board
    are finer than an ordinary floor, and each is legal for exactly one reason:
    the `.kicad_dru` grants THAT NET THAT GEOMETRY inside a rule area named for
    THAT CLUSTER.  Lowering the asserted floor to match would say nothing at
    all -- it would admit a 0.20 mm drill anywhere on the board -- so a fine
    barrel is admitted here only on the board's own terms, and proved:

      * a rule area with the name the rule uses EXISTS on the promoted board;
      * the barrel's WHOLE FOOTPRINT, not merely its centre, lies inside that
        area, proved by a polygon subtraction rather than by point sampling,
        because `enclosedByArea` is answered against the copper;
      * the via's net is the net the rule names;
      * the via meets every minimum that rule states -- diameter, drill and
        annular ring alike.

    Any via that is below a floor and fails any of those is a STRAY and fails
    the check.  With no fine via at all this is vacuously true and reports so,
    which is what every prior promotion reports.
    """
    fine = [v for v in vias
            if (drill_floor and v[5] < drill_floor)
            or ((v[4] - v[5]) / 2 < annular_floor)]
    if not fine:
        return True, dict(fine_vias=0, licensed=0, areas=[])
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
    import pcbnew
    import maze3d as mz

    board = pcbnew.LoadBoard(str(path))

    class _Shim(object):                 # `dru_rules` reads only `qb.b`
        pass
    shim = _Shim()
    shim.b = board
    areas = {}
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetZoneName():
            areas.setdefault(z.GetZoneName(), []).append(z)

    # net -> area -> {constraint: min}, from the rule text alone.
    licences = {}
    for name, cons, cond in mz.dru_rules(shim):
        m = re.fullmatch(r"A\.NetName == '([^']*)' && "
                         r"A\.enclosedByArea\('([^']*)'\)",
                         ' '.join(cond.split()))
        if not m:
            continue
        licences.setdefault((m.group(1), m.group(2)), {}).update(cons)

    def encloses(zone, x, y, dia):
        """True when the whole barrel disc lies inside this rule area.

        The 64-gon is CIRCUMSCRIBED -- its radius is scaled by 1/cos(pi/n) --
        so it contains the disc rather than being contained by it.  An
        inscribed polygon would be a proof about a shape slightly smaller than
        the copper, which is the wrong direction for a legality claim.
        """
        disc = pcbnew.SHAPE_POLY_SET()
        disc.NewOutline()
        n = 64
        r = dia / 2.0 / math.cos(math.pi / n)
        for k in range(n):
            a = 2.0 * math.pi * k / n
            disc.Append(int(round(x + r * math.cos(a))),
                        int(round(y + r * math.sin(a))))
        left = pcbnew.SHAPE_POLY_SET(disc)
        try:
            left.BooleanSubtract(zone.Outline())
        except TypeError:                # older SWIG wants a fast-mode enum
            left.BooleanSubtract(zone.Outline(),
                                 pcbnew.SHAPE_POLY_SET.PM_FAST)
        return left.OutlineCount() == 0

    detail = dict(fine_vias=len(fine), strays=[], areas=[])
    for v in fine:
        _k, net, x, y, dia, drill = v
        hit = None
        for (rnet, area), cons in sorted(licences.items()):
            if rnet != net or area not in areas:
                continue
            if not any(encloses(z, x, y, dia) for z in areas[area]):
                continue
            if (dia >= cons.get('via_diameter', 0)
                    and drill >= cons.get('hole_size', 0)
                    and (dia - drill) / 2 >= cons.get('annular_width', 0)):
                hit = area
                break
        if hit is None:
            detail["strays"].append(dict(net=net, at=[x, y], dia_nm=dia,
                                         drill_nm=drill))
        else:
            detail["areas"].append(dict(net=net, area=hit, at=[x, y],
                                        dia_nm=dia, drill_nm=drill))
    detail["licensed"] = len(detail["areas"])
    return not detail["strays"], detail


def rule_area_sigs(path):
    """Every rule area's name, layers, keep-out flags and outline."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for z in board.Zones():
        if not z.GetIsRuleArea():
            continue
        o = z.Outline().Outline(0)
        out.append((z.GetZoneName(),
                    tuple(board.GetLayerName(l) for l in z.GetLayerSet().Seq()),
                    bool(z.GetDoNotAllowTracks()), bool(z.GetDoNotAllowVias()),
                    bool(z.GetDoNotAllowPads()),
                    bool(z.GetDoNotAllowZoneFills()),
                    tuple((o.CPoint(i).x, o.CPoint(i).y)
                          for i in range(o.PointCount()))))
    return sorted(out)


def stage(rev, work):
    """A project-faithful copy of the board at `rev` (or of the worktree)."""
    cell = Path(work)
    cell.mkdir(parents=True, exist_ok=True)
    for suffix in SUFFIXES:
        target = (cell / BOARD.name).with_suffix(suffix)
        if rev is None:
            shutil.copyfile(BOARD.with_suffix(suffix), target)
        else:
            src = BOARD.with_suffix(suffix).relative_to(ROOT)
            blob = subprocess.run(
                ["git", "-C", str(ROOT), "show", "%s:%s" % (rev, src)],
                capture_output=True, check=True).stdout
            target.write_bytes(blob)
    return cell / BOARD.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD",
                    help="git revision holding the PRE-promotion board")
    ap.add_argument("--nets", required=True,
                    help="comma-separated nets the promotion claimed")
    ap.add_argument("--plane", action="append", default=[],
                    help="NET:LAYER pour the promotion claims to have ADDED; "
                         "repeatable, omit when no pour was added")
    ap.add_argument("--track-width", type=int, default=0,
                    help="nm floor every added track must meet")
    ap.add_argument("--neck", action="store_true",
                    help="admit an added track BELOW --track-width when it is "
                         "a .kicad_dru-licensed pad-escape neck: at least the "
                         "rule's minimum width and wholly inside one of the "
                         "courtyards the rule names")
    ap.add_argument("--via-drill", type=int, default=0,
                    help="nm floor every added via drill must meet")
    ap.add_argument("--annular", type=int, default=125000,
                    help="nm floor every added via's annular ring must meet")
    ap.add_argument("--bridge", action="store_true",
                    help="admit an added via BELOW --via-drill or --annular "
                         "when it is a .kicad_dru-licensed POUR BRIDGE: its "
                         "whole footprint inside a rule area the rule names, "
                         "on the net the rule names, meeting every minimum "
                         "that rule states")
    ap.add_argument("--rule-area", action="append", default=[],
                    help="name of a rule area the promotion claims to have "
                         "ADDED; repeatable, omit when none was added")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    nets = [n for n in a.nets.split(",") if n]
    planes = sorted(tuple(p.split(":", 1)) for p in a.plane)

    tmp = Path(tempfile.mkdtemp(prefix="aqroot-demo-verify-"))
    pre, post = stage(a.ref, tmp / "pre"), stage(None, tmp / "post")

    before, after = objects(pre), objects(post)
    removed = sorted(str(x) for x in (before - after))
    added = sorted(after - before)
    added_nets = sorted({x[1] for x in added})
    tracks = [x for x in added if x[0] == "trk"]
    vias = [x for x in added if x[0] == "via"]

    rpre, rpost = rule_area_sigs(pre), rule_area_sigs(post)
    radded = [z for z in rpost if z not in rpre]
    rlost = [z for z in rpre if z not in rpost]

    zpre, zpost = zone_sigs(pre), zone_sigs(post)
    zadded = [z for z in zpost if z not in zpre]
    zlost = [z for z in zpre if z not in zpost]
    zclaim = sorted((z[0], z[1][0]) for z in zadded)

    first = drc(post, tmp / "drc-1.json")
    refilled = sha256_file(post)
    second = drc(post, tmp / "drc-2.json")
    fill_stable = refilled == sha256_file(post)

    dru = (post.with_suffix(".kicad_dru")).read_text(encoding="utf-8")
    contracts = {k: (v in dru) for k, v in DRU_CONTRACTS.items()}

    widths = sorted({x[7] for x in tracks})
    neck_ok, neck_detail = (neck_proof(post, tracks, a.track_width)
                            if a.neck else (True, None))
    bridge_ok, bridge_detail = (bridge_proof(post, vias, a.via_drill,
                                             a.annular)
                                if a.bridge else (True, None))
    layers = sorted({x[2] for x in tracks})
    vdims = sorted({(x[4], x[5]) for x in vias})

    checks = dict(
        nothing_removed=not removed,
        added_only_on_claimed_nets=set(added_nets) <= set(nets),
        zone_inventory_as_claimed=(not zlost and zclaim == planes),
        track_width_floor_met=(not a.track_width
                               or all(w >= a.track_width for w in widths)
                               or (a.neck and neck_ok)),
        via_drill_floor_met=(not a.via_drill
                             or all(d >= a.via_drill for _dia, d in vdims)
                             or (a.bridge and bridge_ok)),
        annular_floor_met=(all((dia - d) / 2 >= a.annular for dia, d in vdims)
                           or (a.bridge and bridge_ok)),
        rule_areas_as_claimed=(not rlost
                               and sorted(z[0] for z in radded)
                               == sorted(a.rule_area)
                               and all(len(z[1]) == 6 and not any(z[2:6])
                                       for z in radded)),
        drc_zero_attributable=not first["attributable"],
        drc_inherited_within_baseline=all(
            first["counts"].get(k, 0) <= n for k, n in INHERITED.items()),
        schematic_parity_clean=first["schematic_parity_errors"] == 0,
        fill_stable=fill_stable,
        dru_contracts_live=all(contracts.values()),
        beta_v2_untouched=not subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "hardware/beta-v2"],
            capture_output=True, text=True).stdout.strip(),
    )

    report = dict(
        schema=1, ref=a.ref, claimed_nets=nets, claimed_planes=planes,
        pre_board_sha256=sha256_file(pre),
        promoted_board_sha256=sha256_file(BOARD),
        objects_removed=len(removed), removed_sample=removed[:8],
        objects_added=len(added), added_object_nets=added_nets,
        added_tracks=len(tracks), added_vias=len(vias),
        added_track_widths_nm=widths, added_track_layers=layers,
        added_via_dia_drill_nm=[list(v) for v in vdims],
        pad_escape_neck=neck_detail, pour_bridge=bridge_detail,
        rule_areas_added=radded, rule_areas_removed=rlost,
        claimed_rule_areas=sorted(a.rule_area),
        zones_added=zadded, zones_removed=zlost,
        drc=first, drc_second_pass=second, dru_contracts=contracts,
        checks=checks, verdict="PASS" if all(checks.values()) else "FAIL",
    )
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
