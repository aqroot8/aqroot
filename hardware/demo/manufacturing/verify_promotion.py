#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- re-prove a promotion from the two board files ALONE.

`route_maze_batch.py` gates its own candidate before it writes it.  That is
necessary but it is not independent: the same process that proposed the copper
decided it was legal.  This module re-derives every promotion property a second
time, from the committed board and the promoted board, without reading the
driver's scratch tree, its ledger or its evidence JSON:

  * NO pre-existing track or via was moved or removed -- or, with `--evicted`,
    every removal lies on a net the promotion NAMED as ripped up, and KiCad's
    own unconnected-item count did not rise, which is the independent half of
    the driver's clause 4: a rip-up that stranded anything shows up here even
    though this module never reads a ledger;
  * every ADDED object lies on one of the nets the promotion claimed;
  * every added track meets the width the caller asserts -- or, if it is
    narrower, is a DRU-LICENSED pad-escape neck: at least the necking minimum
    AND lying wholly inside one of the courtyards the `.kicad_dru` rule names,
    proved with the same `maze3d.Neck` the router was confined by;
  * every added via meets the drill and annular-ring floors it asserts -- or,
    with `--bridge`, is a DRU-LICENSED POUR BRIDGE: a barrel whose whole
    footprint lies inside a rule area the `.kicad_dru` names for its net, and
    which meets every minimum that rule states;
  * the rule-area inventory -- BOARD-LEVEL AND FOOTPRINT-EMBEDDED, which
    before D-617 meant board-level only, so the largest rule area on this board
    was never audited here at all -- changed by exactly the licence areas the
    caller asserts, none was lost, every added one forbids nothing, and every
    area whose COPPER LAYER SET GREW is named by `--rule-area-widened` and
    changed in no other way;
  * the zone inventory changed by exactly the pours the caller asserts, and no
    surviving zone's net, layer, outline or fill parameters changed;
  * real KiCad `--refill-zones --save-board --severity-all --schematic-parity`
    DRC on the promoted board reports only the inherited classes, with ZERO
    attributable violations -- and it is run with the footprint libraries
    ACTUALLY RESOLVED, which before D-616 they never were: KiCad's stock
    libraries are installed on this machine but no global `fp-lib-table` was
    ever written, so 199 footprints reported "the current configuration does
    not include the footprint library ..." and KiCad never once opened the
    master of a land on this board.  `stage()` now writes the project's table
    PLUS the table KiCad itself ships, so `lib_footprint_mismatch` is a live
    class here instead of an unaskable one;
  * schematic parity is ACTUALLY ASKED -- the whole `.kicad_sch` hierarchy is
    staged beside the board, which it was not before D-613 -- and reports no
    error-severity entry and no warning class or count beyond the recorded
    `INHERITED_PARITY` baseline;
  * the promoted board is fill-stable -- a second refill changes nothing;
  * NO OUTER POUR'S PAD PARTITION GOT FINER -- `checks/pour_partition_contract.py`
    PP1-PP4 run on the same two staged cells (D-623).  This is the check whose
    absence let D-619's severed 12.461 mm2 `GND` fragment read 14/14 here: every
    other property in this list is TRUE of a board whose pour has been cut in
    half, and it took a person reading island areas by hand to see it;
  * the retained safety rules are still live text in the `.kicad_dru`.

It is read-only with respect to `hardware/demo/kicad/aqroot-demo/`: both boards
and every schematic sheet it inspects are copies in a temporary directory.
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

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
SUFFIXES = (".kicad_pcb", ".kicad_dru", ".kicad_pro")
# CLAUSE 15 (D-623): the pour-partition contract, re-asked HERE.
POUR_PARTITION = Path(__file__).with_name("checks") / "pour_partition_contract.py"

# The report classes this board carries that no promotion is answerable for.
# `lib_footprint_issues` was 199 and is now ZERO -- it was never a property of
# the board at all, only of an unconfigured library table (D-616), and it is
# deliberately NOT listed here any more: if it ever returns, the libraries have
# stopped resolving and every land check in this repository has gone vacuous
# again, which must fail loudly rather than pass quietly.
# `lib_footprint_mismatch` was 1 and is now ZERO -- D-617 gave `U1`'s
# footprint-embedded ESP32-S3-WROOM-1 ANTENNA KEEP-OUT the `*.Cu` its own
# master writes, and moved the copper that was standing on `In3.Cu` inside it.
# It is deliberately NOT listed here any more, for the same reason
# `lib_footprint_issues` is not: if it returns, a board footprint has drifted
# from the library it was ruled against and that must fail loudly.
INHERITED = {"hole_clearance": 5, "solder_mask_bridge": 1}

# D-613: `--schematic-parity` was never actually ASKED.  `stage()` copied the
# board, the rules and the project into a temporary directory and left the nine
# `.kicad_sch` files behind, so KiCad found no schematic beside the board it was
# handed and reported an empty parity list -- and `schematic_parity_clean` had
# read TRUE on every promotion this repository has ever gated.  The schematics
# are staged now and the answer is 249 entries, EVERY ONE a warning and not one
# an error: 199 symbol/footprint text-field differences, 48 attribute or
# library-nickname differences (46 of them the test-point BOM flag the
# fabrication package review found independently), and BOSS1/BOSS2, which are
# board-only mounting bosses with no symbol.  This is the baseline that must not
# GROW; the check is no longer "clean", it is "within baseline and error-free".
# D-616 TIGHTENED the second number.  `J5` and `J8` carried a BARE footprint
# name and no library at all on the board, so KiCad reported a nickname
# mismatch against symbols that DID name a library -- and, worse, those two
# lands had no master to be compared against at all.  Both now name their
# library, both are pad-identical to it, and the baseline drops 48 -> 46.
INHERITED_PARITY = {"footprint_symbol_field_mismatch": 199,
                    "footprint_symbol_mismatch": 46,
                    "extra_footprint": 2}

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
        schematic_parity=parity_summary(report.get("schematic_parity", [])),
        unconnected_items=len(report.get("unconnected_items", [])))


def parity_summary(entries):
    """Schematic-parity entries by type and by severity.

    An `error` is a fabrication blocker -- a footprint with no symbol, a net
    that does not match.  A `warning` here is a metadata divergence between the
    symbol and the footprint.  The gate must distinguish them; counting the
    list was what made the vacuous answer look like a passing one.
    """
    counts, severities = {}, {}
    for entry in entries:
        counts[entry["type"]] = counts.get(entry["type"], 0) + 1
        sev = entry.get("severity", "unknown")
        severities[sev] = severities.get(sev, 0) + 1
    return dict(total=len(entries), counts=counts, severities=severities,
                errors=[e for e in entries
                        if e.get("severity") not in ("warning", "ignore")])


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


def relief_run_proof(path, tracks, floor):
    """Which added tracks are narrower than `floor`, and are they LICENSED?

    The strict form of `neck_proof`, and the reason it exists is a
    measurement.  `neck_proof` admits a narrow segment that lies wholly inside
    a courtyard the `.kicad_dru` "Pad-escape necking" rule NAMES -- but that
    rule is written with `intersectsCourtyard`, so what KiCad actually grants
    is wider than what this file proves, and D-609 measured the gap: of eight
    narrow tracks a relief run laid, ZERO were wholly inside a courtyard, two
    merely intersected one, KiCad licensed exactly those two and flagged the
    other six.  `FBV2_P2_ROUTING_PLAN.md` section 17 clause 2 names
    `intersectsCourtyard` as the shape a relief must never lean on.

    A `PAD_ESCAPE_RUN_<REF>` area plus a `.kicad_dru` `track_width` rule naming
    that net inside it is the strict form, and it is proved here exactly as
    `bridge_proof` proves a barrel:

      * a rule area with the name the rule uses EXISTS on the promoted board;
      * the track's WHOLE FOOTPRINT -- the stadium of its centreline grown by
        half its width, including both end caps -- lies inside that area,
        proved by polygon subtraction, because `enclosedByArea` is answered
        against the copper and not against a centreline;
      * the track's net is the net the rule names;
      * the track is at least as wide as the minimum that rule states.

    Each area is asked ON ITS OWN, never as a union, which is section 17
    clause 3's own-area sufficiency: a neck may not pass by borrowing its
    neighbour's licence.
    """
    narrow = [x for x in tracks if floor and x[7] < floor]
    if not narrow:
        return True, dict(narrow_tracks=0, licensed=0, areas=[])
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
    licences = {}
    for name, cons, cond in mz.dru_rules(shim):
        m = re.fullmatch(r"A\.NetName == '([^']*)' && "
                         r"A\.enclosedByArea\('([^']*)'\)",
                         ' '.join(cond.split()))
        if not m or 'track_width' not in cons:
            continue
        licences[(m.group(1), m.group(2))] = cons['track_width']

    def stadium(x0, y0, x1, y1, w):
        """The copper of one track: its centreline grown by half its width.

        Two CIRCUMSCRIBED 64-gon caps and the rectangle between them, so the
        shape CONTAINS the copper rather than being contained by it -- the
        conservative direction for a legality claim, the same reading
        `encloses` already documents for a barrel.
        """
        poly = pcbnew.SHAPE_POLY_SET()
        n = 64
        r = w / 2.0 / math.cos(math.pi / n)
        for (cx, cy) in ((x0, y0), (x1, y1)):
            poly.NewOutline()
            for k in range(n):
                a = 2.0 * math.pi * k / n
                poly.Append(int(round(cx + r * math.cos(a))),
                            int(round(cy + r * math.sin(a))))
        L = math.hypot(x1 - x0, y1 - y0)
        if L > 0:
            ux, uy = -(y1 - y0) / L * r, (x1 - x0) / L * r
            poly.NewOutline()
            for (px, py) in ((x0 + ux, y0 + uy), (x1 + ux, y1 + uy),
                             (x1 - ux, y1 - uy), (x0 - ux, y0 - uy)):
                poly.Append(int(round(px)), int(round(py)))
        try:
            poly.Simplify()
        except TypeError:
            poly.Simplify(pcbnew.SHAPE_POLY_SET.PM_FAST)
        return poly

    def encloses(zone, shape):
        left = pcbnew.SHAPE_POLY_SET(shape)
        try:
            left.BooleanSubtract(zone.Outline())
        except TypeError:
            left.BooleanSubtract(zone.Outline(),
                                 pcbnew.SHAPE_POLY_SET.PM_FAST)
        return left.OutlineCount() == 0

    detail = dict(narrow_tracks=len(narrow), strays=[], areas=[])
    for x in narrow:
        _k, net, layer, x0, y0, x1, y1, w = x
        shape = stadium(x0, y0, x1, y1, w)
        hit = None
        for (rnet, area), minw in sorted(licences.items()):
            if rnet != net or area not in areas or w < minw:
                continue
            if any(encloses(z, shape) for z in areas[area]):
                hit = (area, minw)
                break
        if hit is None:
            detail["strays"].append(dict(net=net, layer=layer, width_nm=w,
                                         start=[x0, y0], end=[x1, y1]))
        else:
            detail["areas"].append(dict(net=net, layer=layer, width_nm=w,
                                        area=hit[0], licence_nm=hit[1],
                                        start=[x0, y0], end=[x1, y1]))
    detail["licensed"] = len(detail["areas"])
    return not detail["strays"], detail


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

    # net -> area -> {constraint: min}, from the rule text alone.  A rule area
    # licenses a BARREL only when its rules STATE all three of the constraints
    # a barrel owes.  D-610.  `cons.get(k, 0)` below reads a missing constraint
    # as a zero floor, so an area whose rules say nothing about barrels would
    # license every barrel inside it -- and D-610 built the first such area,
    # `PAD_ESCAPE_RUN_<REF>`, which grants a TRACK WIDTH and nothing else.
    # Measured: it sorts before `PAD_ESCAPE_<REF>` and licensed that
    # promotion's 0.35/0.20 barrel on a rule that never mentions a barrel.
    # Requiring all three is the same read `maze3d.area_licence` has always
    # made, and it makes the two files agree about what a licence IS.
    BARREL_CONS = ('via_diameter', 'hole_size', 'annular_width')
    licences = {}
    for name, cons, cond in mz.dru_rules(shim):
        m = re.fullmatch(r"A\.NetName == '([^']*)' && "
                         r"A\.enclosedByArea\('([^']*)'\)",
                         ' '.join(cond.split()))
        if not m:
            continue
        licences.setdefault((m.group(1), m.group(2)), {}).update(cons)
    licences = {k: v for k, v in licences.items()
                if all(c in v for c in BARREL_CONS)}

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
    """uuid -> every rule area's owner, name, layers, flags and outline.

    BOTH SCOPES, and that is a D-617 correction, not a refactor.
    `pcbnew.BOARD.Zones()` does not return a footprint's zones and a
    footprint's does not return the board's, so this gate had been auditing
    board-level rule areas ONLY -- and the single largest rule area on this
    board, `U1`'s ESP32-S3-WROOM-1 antenna keep-out, lives inside a footprint
    and was never once compared here.  Keyed by UUID because two areas on this
    board share a NAME, and the copper layer set is intersected with the
    board's own enabled stack because `(layers "*.Cu")` reads back as all
    THIRTY-TWO copper layers KiCad can name, of which this board has six.
    """
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    enabled = [board.GetLayerName(l)
               for l in board.GetEnabledLayers().CuStack()]
    subjects = [(None, z) for z in board.Zones()]
    subjects += [(f.GetReference(), z) for f in board.GetFootprints()
                 for z in f.Zones()]
    out = {}
    for owner, z in subjects:
        if not z.GetIsRuleArea():
            continue
        o = z.Outline().Outline(0)
        have = {board.GetLayerName(l) for l in z.GetLayerSet().Seq()}
        out[str(z.m_Uuid.AsString())] = (
            owner, z.GetZoneName(),
            tuple(L for L in enabled if L in have),
            bool(z.GetDoNotAllowTracks()), bool(z.GetDoNotAllowVias()),
            bool(z.GetDoNotAllowPads()),
            bool(z.GetDoNotAllowZoneFills()),
            tuple((o.CPoint(i).x, o.CPoint(i).y)
                  for i in range(o.PointCount())))
    return out


def resolved_fp_lib_table():
    """The project's own nicknames PLUS the stock table KiCad itself ships.

    Without this the staged cell resolves ONE library and KiCad cannot open the
    master of any other land -- the D-616 vacuity.  The rows are not invented
    here: they come from `template/fp-lib-table` in the KiCad installation.
    """
    import screen_land_parity as S
    libs, _proj, _share = S.resolve_libraries()
    rows = "\n".join(
        '  (lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))'
        % (nick, path) for nick, path in sorted(libs.items()))
    return "(fp_lib_table\n  (version 7)\n%s\n)\n" % rows


def pour_partition_proof(pre, post, out):
    """CLAUSE 15 -- an outer pour's PAD PARTITION, re-asked INDEPENDENTLY.

    D-623 wired `checks/pour_partition_contract.py` into `route_maze_batch.py`
    as its clause 8, which is the right place for it and is NOT this place.
    That clause runs inside the process that proposed the copper, against a
    scratch tree that process built; this module exists precisely because that
    is not independent.  And the gap is not hypothetical: D-619's route severed
    a 12.461 mm2 `GND` fragment off three `C45`-pocket pads and THIS FILE
    RETURNED PASS ON ALL FOURTEEN CHECKS, because every property it measured --
    objects, widths, drills, rule areas, zones, DRC, parity, fill-stability --
    is true of a board whose pour has been cut in half.  A person caught it by
    reading island areas by hand.  The gate that re-proves a promotion from the
    two board files ALONE must be able to ask the same question of them.

    IT IS ASKED OF THE SAME TWO CELLS EVERY OTHER CLAUSE READS -- `pre` staged
    from `--ref`, `post` staged from the worktree -- so it inherits their
    project sidecars, and there is no third copy of the board to disagree with.
    `post` has been through `drc()` by the time this runs, so its zones carry
    the copper `--refill-zones --save-board` produced, which is the copper a
    fabricator gets.  `pre` is the committed board and is NOT refilled here,
    which is exact rather than approximate for one stated reason: every
    promotion this repository accepts must pass `fill_stable`, so the committed
    board's stored fill IS its refilled fill.  If that ever stops being true,
    `fill_stable` fails in the same report and the verdict is FAIL regardless
    of what this clause says.

    The `.kicad_prl` is copied in beside each board because the contract's own
    `board_at()` copies it: nothing here reads design rules out of it, and the
    point is that a hand run and this run see byte-identical inputs.

    A CLAUSE THAT COULD NOT BE ASKED IS A REFUSAL, NOT A PASS.  If the contract
    dies before writing its report, this returns False and names the reason,
    rather than letting silence read as assent.
    """
    prl = BOARD.with_suffix(".kicad_prl")
    if prl.exists():
        for cell in (pre.parent, post.parent):
            # A cell may BE the project directory -- `main()` always hands two
            # temporary cells, but the non-vacuity probe hands the replay
            # tree's own project dir as PRE, and copying a file onto itself
            # raises rather than doing nothing.
            target = Path(cell) / prl.name
            if target.resolve() != prl.resolve():
                shutil.copyfile(prl, target)
    run = subprocess.run(
        [sys.executable, str(POUR_PARTITION), "--pre-board", str(pre),
         "--board", str(post), "-o", str(out)],
        text=True, capture_output=True)
    if not Path(out).exists():
        return False, dict(ok=False, ran=False, returncode=run.returncode,
                           stderr=run.stderr[-2000:])
    doc = json.loads(Path(out).read_text())
    clauses = ("PP1", "PP2", "PP3", "PP4")
    failed = sorted(k for k in clauses if not doc["results"][k]["ok"])
    return (not failed), dict(
        ok=(not failed), ran=True, failed_clauses=failed,
        pre_board=str(pre), post_board=str(post),
        results={k: doc["results"][k]["ok"] for k in clauses},
        detail=doc["results"])


def stage(rev, work):
    """A project-faithful copy of the board at `rev` (or of the worktree).

    The footprint libraries and the symbol table are staged from the WORKTREE
    even when the board comes from `rev`: they decide only whether KiCad can
    OPEN a master, and the pre-cell's DRC is consulted for its unconnected
    count alone.
    """
    cell = Path(work)
    cell.mkdir(parents=True, exist_ok=True)
    sources = [BOARD.with_suffix(s) for s in SUFFIXES]
    # EVERY schematic sheet, not just the root: `--schematic-parity` needs the
    # whole hierarchy beside the board or it silently has nothing to compare.
    sources += sorted(BOARD.parent.glob("*.kicad_sch"))
    for src in sources:
        target = cell / src.name
        if rev is None:
            shutil.copyfile(src, target)
        else:
            rel = src.relative_to(ROOT)
            blob = subprocess.run(
                ["git", "-C", str(ROOT), "show", "%s:%s" % (rev, rel)],
                capture_output=True, check=True).stdout
            target.write_bytes(blob)
    shutil.copytree(BOARD.parent / "libraries", cell / "libraries",
                    dirs_exist_ok=True)
    shutil.copyfile(BOARD.parent / "sym-lib-table", cell / "sym-lib-table")
    (cell / "fp-lib-table").write_text(resolved_fp_lib_table(),
                                       encoding="utf-8")
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
    ap.add_argument("--evicted", action="append", default=[],
                    metavar="NET",
                    help="a net this promotion RIPPED UP.  Removals are then "
                         "legal, but only on these nets, and the board's "
                         "unconnected-item count is measured before and after "
                         "so a rip-up that stranded copper cannot pass")
    ap.add_argument("--relief-run", action="store_true",
                    help="admit an added track BELOW --track-width when it is "
                         "a .kicad_dru-licensed pad-escape RUN: its whole "
                         "copper inside a PAD_ESCAPE_RUN_<REF> rule area the "
                         "rule names, on the net the rule names, at least as "
                         "wide as the minimum that rule states.  The strict "
                         "`enclosedByArea` form of --neck, which leans on a "
                         "rule written with `intersectsCourtyard`")
    ap.add_argument("--rule-area", action="append", default=[],
                    help="name of a rule area the promotion claims to have "
                         "ADDED; repeatable, omit when none was added")
    ap.add_argument("--rule-area-widened", action="append", default=[],
                    metavar="NAME",
                    help="name -- or, for a footprint-embedded area with no "
                         "name, the OWNER's reference -- of a rule area whose "
                         "copper LAYER SET the promotion claims to have GROWN "
                         "and changed in no other way.  D-617.  Repeatable")
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
    radded = [rpost[u] for u in sorted(set(rpost) - set(rpre))]
    rlost = [rpre[u] for u in sorted(set(rpre) - set(rpost))]
    # A WIDENED rule area is neither an addition nor a loss.  D-617: five
    # keep-outs on this board named four of six copper layers because KiCad
    # clamped `*.Cu` to the stackup that existed when each was drawn, and
    # repairing that is a change to ONE field -- the copper layer set, and only
    # ever upward.  A promotion must NAME each one; anything else about a rule
    # area that moved is a change nobody reviewed.
    rwidened, rmoved = [], []
    for u in sorted(set(rpre) & set(rpost)):
        was, now = rpre[u], rpost[u]
        if was == now:
            continue
        rest_same = (was[:2] == now[:2] and was[3:] == now[3:])
        if rest_same and set(was[2]) < set(now[2]):
            rwidened.append((u, was[1] or was[0], list(was[2]), list(now[2])))
        else:
            rmoved.append((u, was[1] or was[0]))

    zpre, zpost = zone_sigs(pre), zone_sigs(post)
    zadded = [z for z in zpost if z not in zpre]
    zlost = [z for z in zpre if z not in zpost]
    zclaim = sorted((z[0], z[1][0]) for z in zadded)

    removed_nets = sorted({x[1] for x in (before - after)})
    # KiCad's own connectivity, measured on BOTH boards.  Only asked for when a
    # rip-up happened: it costs a whole extra refilled DRC pass, and with no
    # removals there is nothing it could catch that `nothing_removed` does not.
    pre_drc = drc(pre, tmp / "drc-0.json") if a.evicted else None

    first = drc(post, tmp / "drc-1.json")
    refilled = sha256_file(post)
    second = drc(post, tmp / "drc-2.json")
    fill_stable = refilled == sha256_file(post)

    # CLAUSE 15 -- D-623.  Run AFTER both DRC passes, so `post` carries the
    # refilled copper, and after `fill_stable` is known, because that is the
    # fact this clause's use of an unrefilled `pre` leans on.
    pp_ok, pp_detail = pour_partition_proof(pre, post,
                                            tmp / "pour-partition.json")

    dru = (post.with_suffix(".kicad_dru")).read_text(encoding="utf-8")
    contracts = {k: (v in dru) for k, v in DRU_CONTRACTS.items()}

    widths = sorted({x[7] for x in tracks})
    neck_ok, neck_detail = (neck_proof(post, tracks, a.track_width)
                            if a.neck else (True, None))
    run_ok, run_detail = (relief_run_proof(post, tracks, a.track_width)
                          if a.relief_run else (True, None))
    bridge_ok, bridge_detail = (bridge_proof(post, vias, a.via_drill,
                                             a.annular)
                                if a.bridge else (True, None))
    layers = sorted({x[2] for x in tracks})
    vdims = sorted({(x[4], x[5]) for x in vias})

    checks = dict(
        nothing_removed=(not removed if not a.evicted else
                         set(removed_nets) <= set(a.evicted)),
        unconnected_not_increased=(
            True if pre_drc is None
            else first["unconnected_items"] <= pre_drc["unconnected_items"]),
        added_only_on_claimed_nets=set(added_nets) <= set(nets),
        zone_inventory_as_claimed=(not zlost and zclaim == planes),
        track_width_floor_met=(not a.track_width
                               or all(w >= a.track_width for w in widths)
                               or (a.neck and neck_ok)
                               or (a.relief_run and run_ok)),
        via_drill_floor_met=(not a.via_drill
                             or all(d >= a.via_drill for _dia, d in vdims)
                             or (a.bridge and bridge_ok)),
        annular_floor_met=(all((dia - d) / 2 >= a.annular for dia, d in vdims)
                           or (a.bridge and bridge_ok)),
        rule_areas_as_claimed=(not rlost and not rmoved
                               and sorted(str(z[1]) for z in rwidened)
                               == sorted(a.rule_area_widened)
                               and sorted(z[1] for z in radded)
                               == sorted(a.rule_area)
                               and all(len(z[2]) == 6 and not any(z[3:7])
                                       for z in radded)),
        drc_zero_attributable=not first["attributable"],
        drc_inherited_within_baseline=all(
            first["counts"].get(k, 0) <= n for k, n in INHERITED.items()),
        schematic_parity_within_baseline=(
            not first["schematic_parity"]["errors"]
            and all(first["schematic_parity"]["counts"].get(k, 0) <= n
                    for k, n in INHERITED_PARITY.items())
            and not (set(first["schematic_parity"]["counts"])
                     - set(INHERITED_PARITY))),
        fill_stable=fill_stable,
        # D-623.  The fifteenth check, and the one D-619's severed pour would
        # have failed on a report that otherwise read 14/14.
        pour_partition_intact=pp_ok,
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
        removed_object_nets=removed_nets, claimed_evicted_nets=sorted(a.evicted),
        drc_pre=pre_drc,
        objects_added=len(added), added_object_nets=added_nets,
        added_tracks=len(tracks), added_vias=len(vias),
        added_track_widths_nm=widths, added_track_layers=layers,
        added_via_dia_drill_nm=[list(v) for v in vdims],
        pad_escape_neck=neck_detail, pad_escape_run=run_detail,
        pour_bridge=bridge_detail,
        rule_areas_added=radded, rule_areas_removed=rlost,
        rule_areas_widened=rwidened,
        rule_areas_otherwise_changed=rmoved,
        claimed_rule_areas=sorted(a.rule_area),
        claimed_widened_rule_areas=sorted(a.rule_area_widened),
        zones_added=zadded, zones_removed=zlost,
        drc=first, drc_second_pass=second, dru_contracts=contracts,
        pour_partition=pp_detail,
        checks=checks, verdict="PASS" if all(checks.values()) else "FAIL",
    )
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
