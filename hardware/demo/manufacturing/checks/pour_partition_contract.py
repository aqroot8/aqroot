#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- an outer pour's PAD PARTITION may not get finer unnoticed.

D-619 refused a `/04_SPI_B_RADIOS_NFC/NFC_VDD_A` route that closed an edge,
regressed nothing and drew ZERO attributable DRC, because its 4.4 mm `B.Cu`
wall up the west side of `U9` severed the `GND` pour and left `C45.2`,
`C51.2` and `C53.2` on a 12.461 mm2 fragment.  Every instrument on this board
passed that route:

    verify_promotion.py   counts OBJECTS, and nothing was removed
    routing_ledger.py     counts EDGES, and `GND` stayed at 4
    kicad-cli drc         reports UNCONNECTED ITEMS, and there were none --
                          the fragment keeps three of its own through barrels
    pour_bond_guard.py    reserves narrow bonds it can FIND, and before the
                          cut there was no neck there to find

It was caught by a person reading island areas, once, by hand.  This file is
that reading, made mechanical, so the next one is caught by the gate.

WHAT IS MEASURED.  For every filled OUTER pour, each pad of the pour's net is
resolved to the island that CONTAINS it -- by geometry, never by ordinal, for
the reason `pour_bond_contract.py` P2 already records: one new island
renumbers every ordinal above it.  That gives a PARTITION of the pour's pads.
The claim is then a claim about the partition and not about a count:

  PP1  WELL FORMED, AND THE BAR IS THE TRANSACTION.  Every pad of a
       pour-owning net that sits on that pour's layer is resolved to an island
       of it.  Some never are and always were not: a net owning a BOUNDED pour
       has lands outside that pour's outline by construction, and this board
       has 20 of them (19 `BQ25185_SYS`, plus `GND` `MK1.4`).  Asserting zero
       would be asserting a different board.  The claim is therefore that the
       transaction introduces NO NEW unresolved pad -- a pad that resolved
       before and resolves nowhere after has had its pour taken away, which is
       the same injury PP2 measures arriving by a different road.

  PP2  A SPLIT PAD PAIR IS EITHER PRICED OR REFUSED.  Two pads that shared an
       island BEFORE and do not share one AFTER is exactly the injury: copper
       that used to join two lands does not.  Detecting it is strictly stronger
       than an island COUNT, which moves for harmless reasons -- a pour growing
       a new sliver, a zone refilled around a via -- and weaker than a copper
       diff, which moves for every route.  D-628 then admits ONE kind of split
       and only against a number: every fragment it creates must be `BONDED` by
       PP3, and the conductor replacing the severed copper -- the barrels into
       the reserved plane AND the fragment's own copper out to each pad, priced
       at the bottleneck of that series chain -- must carry at least the design
       current this board publishes for that pour's net in `.kicad_dru`
       section 5.  A net the table does not price is refused, which is where
       `GND` lands.  The clause carries its own non-vacuity controls and they
       run on every board, split or not.  See THE PP2 AMPACITY CLAUSE below.

  PP3  A SPLIT IS PRICED, NOT ONLY NAMED.  For every new fragment, what does
       it still have?  Each pad's own through barrels are resolved into the
       net's filled zones on the RESERVED INNER PLANES, because that is the
       bond a severed outer fragment actually keeps.  A fragment whose every
       pad keeps a barrel into a full-board reference plane is `BONDED`; one
       with a pad that keeps nothing is `STRANDED`, and STRANDED is the
       hard refusal -- it is the D-584 orphan, the failure mode the pour was
       poured to avoid.

  PP4  NON-VACUITY.  Deleting the fragment's barrels must turn every `BONDED`
       verdict into `STRANDED`.  A clause that cannot fail is not a clause.
       A fragment PP3 has already condemned is SKIPPED and named
       (`condemned_fragments_skipped`, D-625): it is `STRANDED` with its
       barrels in and `STRANDED` without them, so it cannot flip, and counting
       that as a failed knife reads as "PP4 broke" when the operative refusal
       is PP3.  When that leaves nothing to probe, the whole-pour probe below
       runs instead, so PP4 is still proved and can still fail.

WHY `BONDED` IS NOT A FAILURE, STATED HONESTLY.  D-619 treated any severance
as an injury.  D-622 measured the two sides of that trade for the first time
and they are not close: the `C45` pocket's `B.Cu` geodesic back to the main
island is **32.001 mm** the long way round the west of `U9`, while each of its
three pads sits within a millimetre of its own through barrel into the SAME
9450.2 mm2 `In1.Cu` and `In4.Cu` `GND` reference planes -- `In4` one prepreg
below `B.Cu`.  Severing a 32 mm outer detour off pads that each own a barrel
into two solid reference planes is not a return-path injury; it is what those
barrels are for.  So this contract does not forbid severance.  It forbids
severance that STRANDS, and it makes every other severance state its price.

Read-only.  Nothing here writes a board.

    python3 checks/pour_partition_contract.py --ref HEAD [--board B] -o OUT
    python3 checks/pour_partition_contract.py --pre-board A --board B -o OUT

`--ref` reads PRE out of git, which is the right unit for auditing a promotion
after the fact.  `--pre-board` (D-623) names a PRE board FILE instead, which is
the unit `route_maze_batch.py` clause 8 needs: the two sides of a gate run are
the authoritative board on disk and the refilled candidate beside it, and
neither of those is a commit.  A board file is read against its own sidecars,
so it must sit beside them.
"""

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MANU = ROOT / "hardware/demo/manufacturing"
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
SIDECARS = ("aqroot-Beta-v2.kicad_dru", "aqroot-Beta-v2.kicad_pro",
            "aqroot-Beta-v2.kicad_prl")

sys.path.insert(0, str(MANU))


def board_at(rev, tmp):
    """The board as it stands at `rev`, with the sidecars it is read against.

    A scratch board without its `.kicad_pro` silently drops every netclass to
    Default; without its `.kicad_dru` it is judged by different rules.  Both
    matter here because the zones are read from the file, so they are copied.
    """
    out = Path(tmp) / "pre"
    out.mkdir(parents=True, exist_ok=True)
    rel = "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
    blob = subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (rev, rel)],
                          check=True, capture_output=True).stdout
    (out / "aqroot-Beta-v2.kicad_pcb").write_bytes(blob)
    for s in SIDECARS:
        (out / s).write_bytes((PROJECT / s).read_bytes())
    return out / "aqroot-Beta-v2.kicad_pcb"


def partition(path):
    """{key: {islands, pads:{ref: island}, geometry}} for every OUTER pour."""
    import pcbnew
    import pour_bond_guard as pg
    board = pcbnew.LoadBoard(str(path))
    pours = pg.read_pours(board)
    for p in pours:
        pg.assign(board, p)
    out, unresolved = {}, []
    for p in pours:
        key = "%s|%s|%s" % (p["net"], p["lkey"], p["zone"])
        pads, isl = {}, {}
        for i, e in enumerate(p["islands"]):
            isl[i] = dict(area_mm2=round(e["area_mm2"], 3),
                          pads=sorted(q["ref"] for q in e["pads"]),
                          vias=[(v["x"], v["y"]) for v in e["vias"]])
            for q in e["pads"]:
                pads[q["ref"]] = i
        out[key] = dict(net=p["net"], lkey=p["lkey"], layer=p["layer"],
                        zone_name=p["zone_name"], n_islands=len(p["islands"]),
                        pads=pads, islands=isl)
        # PP1: a pad of this net, on this layer, that landed on no island
        for fp in board.GetFootprints():
            for q in fp.Pads():
                if q.GetNetname() != p["net"]:
                    continue
                if p["layer"] not in [board.GetLayerName(l)
                                      for l in q.GetLayerSet().CuStack()]:
                    continue
                ref = "%s.%s" % (fp.GetReference(), q.GetNumber())
                if ref not in pads:
                    unresolved.append(dict(pour=key, pad=ref))
    return out, unresolved


def reserved_plane_zones(path):
    """Filled zones of each net on the RESERVED INNER planes, by net."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    import route_maze_batch as rb
    reserved = rb.reserved_inner_planes(board)
    inner = {"In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"}
    out = {}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lid in z.GetLayerSet().CuStack():
            ln = board.GetLayerName(lid)
            if ln not in inner:
                continue
            ps = z.GetFilledPolysList(lid)
            for i in range(ps.OutlineCount()):
                sub = pcbnew.SHAPE_POLY_SET()
                sub.AddOutline(ps.Outline(i))
                for h in range(ps.HoleCount(i)):
                    sub.AddHole(ps.Hole(i, h), 0)
                out.setdefault(z.GetNetname(), []).append(
                    (ln, z.GetZoneName(), sub, round(sub.Area() / 1e12, 3)))
    return out, reserved


def barrels(path, net):
    """Through barrels of `net`: (x, y, top, bottom)."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        v = pcbnew.Cast_to_PCB_VIA(t)
        out.append((v.GetPosition().x, v.GetPosition().y,
                    board.GetLayerName(v.TopLayer()),
                    board.GetLayerName(v.BottomLayer())))
    return out


def price_fragment(path, net, frag, planes, drop_barrels=()):
    """PP3: what does every pad of this fragment still have?

    A pad is BONDED when a barrel of its own net lies inside the fragment's
    own island copper AND inside a filled zone of that net on a reserved
    inner plane.  `drop_barrels` is PP4's knife: the same measurement with
    named barrels removed must come back STRANDED.
    """
    import pcbnew
    drop = {(int(x), int(y)) for (x, y) in drop_barrels}
    keep = [b for b in frag["vias"] if (int(b[0]), int(b[1])) not in drop]
    rows = []
    for b in keep:
        pt = pcbnew.VECTOR2I(int(b[0]), int(b[1]))
        hits = [dict(layer=ln, zone=zn, area_mm2=ar)
                for (ln, zn, poly, ar) in planes.get(net, [])
                if poly.Contains(pt, -1, 0)]
        rows.append(dict(xy_mm=[round(b[0] / 1e6, 3), round(b[1] / 1e6, 3)],
                         planes=hits))
    bonded = [r for r in rows if r["planes"]]
    return dict(barrels=len(keep), barrels_into_reserved_planes=len(bonded),
                detail=rows,
                verdict="BONDED" if bonded else "STRANDED")


# --------------------------------------------------------------------------- #
# THE PP2 AMPACITY CLAUSE -- D-628
# --------------------------------------------------------------------------- #
# D-627 put a route on the table that closes TWO open edges on the display
# supply and is refused by `PP2` ALONE: `/03_SPI_A_DISPLAY_SD/LED_K` crosses the
# `+3V3` `F.Cu` pour and splits its 281.527 mm2 island into a 177.955 mm2 body
# and a 79.292 mm2 fragment carrying `J1.7` / `J1.8` / `J1.9`.  `PP1`, `PP3` and
# `PP4` all pass -- `PP3` reads `BONDED` on four through barrels into the
# 8055.907 mm2 `In3.Cu` `+3V3` plane and `PP4`'s knife flips it -- and the
# doctrine above says in its own words that this contract "does not forbid
# severance.  It forbids severance that STRANDS, and it makes every other
# severance state its price."  `PP2` was nevertheless coded `ok = not splits`,
# an unconditional refusal of ANY split, and D-625 recorded the disagreement
# without resolving it.
#
# WHAT WAS MISSING IS A PRICE IN THE UNIT A REVIEWER ACTUALLY ASKS ABOUT.
# `PP3`'s `BONDED` is a TOPOLOGICAL verdict: it would admit a fragment bonded by
# one hair-thin barrel exactly as readily as by four fat ones, so deferring
# `PP2` to `PP3` is not the answer either.  This clause is the narrower one:
#
#     PP2 admits a split when every fragment it creates is `BONDED` by PP3
#     AND the conductor that replaces the severed copper carries at least the
#     current the board itself publishes for that pour's net.
#
# THE BOND IS THE WHOLE REPLACEMENT PATH, NOT JUST THE BARRELS.  Current
# reaching a severed pad goes down the inner plane, up a barrel, and then
# THROUGH THE FRAGMENT'S OWN COPPER to the pad.  Pricing only the barrels prices
# one link of a chain.  On the D-627 fragment that distinction is the whole
# answer: four 0.400 mm barrels carry 2.311 A each and 9.244 A in parallel, but
# the fragment's own copper from those barrels to `J1.7` and `J1.9` narrows to
# 0.500 mm, which carries 1.441 A -- 6.4x less.  The bond is priced at the
# BOTTLENECK of the series chain, so the honest figure for that fragment is
# 1.441 A and not 9.244 A.  Both are measured here and both are published.
#
# THE BAR IS THE BOARD'S OWN PUBLISHED RAIL CURRENT.  `.kicad_dru` section 5 --
# "POWER RAILS - WIDTH FLOORS FROM IPC-2221B AT THE REAL COPPER" -- carries a
# per-netclass table of design currents, at the same dT = 10 K and the same
# copper this pricing uses, written years before this clause existed and used to
# derive every width floor the board is fabricated to.  It is read from the
# `.kicad_dru` beside the board under judgement, and the STRICTEST figure in
# each class's row is taken: that deliberately includes `BAT_MAIN`'s 3.125 A
# fault-trip threshold and `SYS_MAIN`'s 2.19 A local inductor peak, both of
# which the table itself excludes from its WIDTH floors.  A width floor may
# reasonably be sized on the design current; a bond that replaces copper a rail
# already relies on should be charged the largest number anyone has published
# for it.
#
# THE BAR IS ALSO A DELIBERATE OVER-CHARGE IN A SECOND WAY, STATED PLAINLY: it
# charges the fragment with the WHOLE rail's current.  The D-627 fragment holds
# three of the `+3V3` rail's eighty pads and cannot draw 1.0 A; the clause asks
# it to carry 1.0 A anyway, because apportioning a rail across its pads would be
# a model, and the whole-rail figure is a MEASUREMENT the board already ships.
#
# A NET THE TABLE DOES NOT PRICE IS REFUSED, WHICH IS WHERE `GND` LANDS.  `GND`
# is a return plane and has no published design current, so no `GND` split can
# be admitted by this clause and `PP2` behaves on `GND` exactly as it did
# before.  That is the conservative direction and it is not an accident: the
# question "how much current does a return plane fragment carry" is not answered
# by a rail table, and until it is answered `PP2` should keep saying no.  D-625's
# `BTN_DOWN_N` severance is therefore refused twice over -- `PP3` reads
# `STRANDED` and the net carries no price.
#
# THE CLAUSE CARRIES ITS OWN NON-VACUITY CONTROLS AND THEY RUN ON EVERY BOARD,
# split or no split.  `decide()` is the only place the admission is decided, so
# the controls drive the same function the verdict does, on figures read from
# this board: KiCad's own 0.200 mm `min_thickness` sliver (0.742 A) must be
# REFUSED against a 1.0 A rail, the four-barrel bond (9.244 A) must be ADMITTED,
# the same bond must be REFUSED when the verdict is `STRANDED`, it must be
# REFUSED when the net has no published current, and the bar must be located
# exactly where it claims -- admitted at equality, refused one part per million
# below it.  A control that does not behave as stated FAILS `PP2`, because a
# clause that cannot refuse is not a clause.
#
# WHAT WAS CUT IS MEASURED TOO, AS EVIDENCE RATHER THAN AS THE BAR.  The
# narrowest place on the widest path from the fragment's pads to the body's,
# inside the PRE island, is the cross-section the route removed --
# `pour_bond_guard.geodesic` is exactly that measurement and is reused here
# unchanged.  On the D-627 split it is 1.150 mm of 1 oz outer copper, 2.636 A.
# It is published because it is the first question a reviewer asks and because
# it bounds nothing: it is a property of the copper that USED to be there, and a
# geodesic that runs off its own search window under-states it.  The BAR is the
# published rail current, which no search can under-state.
DT_K = 10.0                      # the dT `.kicad_dru` section 5 is derived at
NECK_GRID = 25000                # `pour_bond_guard`'s own tube lattice, 25 um
NECK_RADIUS_CAP = 1500000        # up to a 3.0 mm-wide tube; wider is not needed
NECK_PROBE_BODY_PADS = 2         # body anchors per fragment pad for the neck
AMP_TOL = 1e-9
SECTION5 = "# 5. POWER RAILS"


def published_rail_currents(dru_path):
    """The per-netclass design currents THIS BOARD publishes, section 5.

    The table is a comment block, which is exactly why it is parsed rather than
    transcribed: a figure a reviewer can edit in the `.kicad_dru` and a figure
    this clause charges a bond against must be the same figure.  A class row
    starts at column 4 with an upper-case name; its continuation lines are
    indented further and belong to it.  Every "<n> A" and "<n> pk" figure in a
    class's own rows is collected and the LARGEST is the bar (see above).
    """
    import re
    try:
        txt = Path(dru_path).read_text(encoding="utf-8", errors="replace")
        i = txt.index(SECTION5)
    except (OSError, ValueError):
        return {}, dict(source=str(dru_path), found=False)
    tail = txt[i:]
    end = tail.find("\n(rule")
    blk = tail[:end if end > 0 else len(tail)]
    rows, cur = {}, None
    for line in blk.splitlines():
        if not line.startswith("#"):
            continue
        body = line[1:]
        m = re.match(r"^   ([A-Z][A-Z0-9_]+)\s+(\S.*)$", body)
        if m:
            cur = m.group(1)
            rows.setdefault(cur, []).append(m.group(2).strip())
        elif cur and body.startswith("     ") and body.strip():
            rows[cur].append(body.strip())
    table = {}
    for cls, lines in rows.items():
        figs = sorted({float(x) for x in re.findall(
            r"([0-9]*\.?[0-9]+)\s*(?:A\b|pk\b|peak\b)", " ".join(lines))})
        if figs:
            table[cls] = dict(amps=max(figs), figures=figs, rows=lines)
    return table, dict(source=str(dru_path), found=True,
                       sha256=hashlib.sha256(
                           Path(dru_path).read_bytes()).hexdigest(),
                       classes=sorted(table))


def decide(verdict, priced_amps, required_amps):
    """THE ADMISSION, in ONE place -- the verdict and the controls share it.

    Every refusal names itself, so a report says which of the five gates a
    split fell at rather than only that it fell.
    """
    if verdict != "BONDED":
        return False, "PP3_NOT_BONDED"
    if required_amps is None:
        return False, "NET_CARRIES_NO_PUBLISHED_CURRENT"
    if priced_amps is None:
        return False, "BOND_NOT_MEASURABLE"
    if priced_amps + AMP_TOL < required_amps:
        return False, "BOND_UNDER_PRICED"
    return True, "BOND_PRICED_AT_OR_ABOVE_THE_PUBLISHED_RAIL_CURRENT"


def decision_controls():
    """PP2's non-vacuity, driven through `decide()` on this board's figures.

    Six probes, each with the outcome it MUST produce.  The reference currents
    are the board's own: KiCad's 0.200 mm zone `min_thickness`, one P3V3-class
    0.300 mm outer track, and the four 0.400 mm barrels D-627 priced.  The bar
    itself is a synthetic 1.0 A so the expectations cannot drift with a table
    edit -- what the table is read for is the VERDICT, and what these probes
    prove is that the comparison behaves.
    """
    import audit_bond_ampacity as ab
    hair = round(ab.ampacity(ab.track_area(0.200), DT_K), 3)
    track = round(ab.ampacity(ab.track_area(0.300), DT_K), 3)
    # summed the way `bond_price` sums it -- four ROUNDED barrels, so the
    # control prints the same 9.244 A a fragment report does.
    four = round(4 * round(ab.ampacity(ab.barrel_area(0.400), DT_K), 3), 3)
    bar = 1.0
    cases = [
        ("min_thickness_sliver_refused", "BONDED", hair, bar, False),
        ("one_class_width_track_refused", "BONDED", track, bar, False),
        ("four_barrel_bond_admitted", "BONDED", four, bar, True),
        ("stranded_refused_however_priced", "STRANDED", four, bar, False),
        ("unpriced_net_refused", "BONDED", four, None, False),
        ("bar_located_one_ppm_below", "BONDED", bar * (1 - 1e-6), bar, False),
        ("bar_located_at_equality", "BONDED", bar, bar, True),
    ]
    out = []
    for name, verdict, priced, req, want in cases:
        got, why = decide(verdict, priced, req)
        out.append(dict(control=name, verdict=verdict, priced_amps=priced,
                        required_amps=req, expected=want, got=got, why=why,
                        behaved=(got == want)))
    return dict(ok=all(c["behaved"] for c in out),
                reference_amps=dict(zone_min_thickness_0p200mm=hair,
                                    outer_track_0p300mm=track,
                                    four_0p400mm_barrels=four),
                probes=out)


def pour_geometry(path):
    """The pours' actual COPPER, keyed exactly as `partition()` keys them.

    `partition()` returns only JSON-able facts on purpose.  The ampacity clause
    needs polygons, edge soups and via drills, so they are read once -- and
    only when a split exists to price, because a board with no split pays
    nothing for this clause.
    """
    import pcbnew
    import pour_bond_guard as pg
    board = pcbnew.LoadBoard(str(path))
    pours = pg.read_pours(board)
    for p in pours:
        pg.assign(board, p)
    drills = {}
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        v = pcbnew.Cast_to_PCB_VIA(t)
        drills[(int(v.GetPosition().x), int(v.GetPosition().y))] = int(v.GetDrill())
    out = {}
    for p in pours:
        key = "%s|%s|%s" % (p["net"], p["lkey"], p["zone"])
        out[key] = {i["index"]: i for i in p["islands"]}
    return out, drills


def tube_width_mm(edges, a, b):
    """The narrowest place on the WIDEST path from `a` to `b` inside `edges`.

    `pour_bond_guard.geodesic` erodes downward from the requested radius and
    returns the first radius the whole path survives, so `2 * radius` is the
    bottleneck width of the best path -- the figure a cross-section is priced
    from.  Reused unchanged: this clause introduces no new geometry primitive.
    """
    import pour_bond_guard as pg
    t = pg.geodesic(edges, (a["x"], a["y"], a["r"]), (b["x"], b["y"], b["r"]),
                    NECK_RADIUS_CAP, NECK_GRID, win_mm=3.0, grows=5)
    if not t:
        return None, None
    return 2.0 * t["radius"] / 1e6, t["mm"]


def bond_price(net, isl, planes, drills):
    """What the conductor replacing the severed copper carries, in amperes.

    A series chain: the plane -> the barrels that land in it -> the fragment's
    own copper -> each pad.  Priced at its BOTTLENECK.  A pad whose path cannot
    be measured makes the whole price `None`, which `decide()` refuses -- an
    unmeasurable bond is not a priced one.
    """
    import pcbnew
    import audit_bond_ampacity as ab
    landing = []
    for b in isl["vias"]:
        pt = pcbnew.VECTOR2I(int(b["x"]), int(b["y"]))
        if any(poly.Contains(pt, -1, 0)
               for (_l, _z, poly, _a) in planes.get(net, [])):
            landing.append(b)
    barrels, missing = [], []
    for b in landing:
        drill = drills.get((int(b["x"]), int(b["y"])))
        if drill is None:
            missing.append([b["x"] / 1e6, b["y"] / 1e6])
            continue
        area = ab.barrel_area(drill / 1e6)
        barrels.append(dict(xy_mm=[round(b["x"] / 1e6, 3), round(b["y"] / 1e6, 3)],
                            drill_mm=drill / 1e6,
                            wall_mm2=round(area, 6),
                            amps=round(ab.ampacity(area, DT_K), 3)))
    bond = round(sum(b["amps"] for b in barrels), 3) if barrels else 0.0
    inner = []
    for q in isl["pads"]:
        best_w, best_mm = None, None
        for b in landing:
            w, mm = tube_width_mm(isl["edges"], q, b)
            if w is not None and (best_w is None or w > best_w):
                best_w, best_mm = w, mm
        row = dict(pad=q["ref"], width_mm=None, mm=None, amps=None, mohm=None)
        if best_w is not None:
            area = ab.track_area(best_w)
            row.update(width_mm=round(best_w, 4), mm=round(best_mm, 3),
                       amps=round(ab.ampacity(area, DT_K), 3),
                       mohm=round(ab.resistance_mohm(best_mm, area), 3))
        inner.append(row)
    unmeasured = [r["pad"] for r in inner if r["amps"] is None]
    amps = [r["amps"] for r in inner if r["amps"] is not None]
    internal = min(amps) if amps else None
    priced = None
    if not unmeasured and not missing and barrels and internal is not None:
        priced = round(min(bond, internal), 3)
    return dict(priced_amps=priced,
                bottleneck=("FRAGMENT_COPPER" if priced is not None
                            and internal <= bond else
                            ("BARRELS" if priced is not None else None)),
                barrels_into_plane=len(barrels), bond_amps_parallel=bond,
                internal_min_amps=internal,
                internal_min_width_mm=min([r["width_mm"] for r in inner
                                           if r["width_mm"] is not None],
                                          default=None),
                barrels=barrels, internal=inner,
                unmeasurable_pads=unmeasured, barrels_without_drill=missing,
                dT_K=DT_K)


def severed_neck(pre_isl, frag_pads, body_pads):
    """The cross-section the route REMOVED -- evidence, never the bar."""
    import audit_bond_ampacity as ab
    probes, widest = [], None
    for q in frag_pads:
        for r in body_pads[:NECK_PROBE_BODY_PADS]:
            w, mm = tube_width_mm(pre_isl["edges"], q, r)
            probes.append(dict(frag_pad=q["ref"], body_pad=r["ref"],
                               width_mm=(None if w is None else round(w, 4)),
                               mm=(None if mm is None else round(mm, 3))))
            if w is not None and (widest is None or w > widest):
                widest = w
    return dict(width_mm=(None if widest is None else round(widest, 4)),
                amps=(None if widest is None else
                      round(ab.ampacity(ab.track_area(widest), DT_K), 3)),
                probes=probes,
                note="the narrowest place on the widest PRE path from the "
                     "fragment's pads to the body's; under-stated by a "
                     "geodesic that reaches its own search window, which is "
                     "why it is published and not charged")


def compare(pre_path, post_path):
    pre, pre_bad = partition(pre_path)
    post, post_bad = partition(post_path)
    planes, reserved = reserved_plane_zones(post_path)

    res = {}
    was = {(x["pour"], x["pad"]) for x in pre_bad}
    now = {(x["pour"], x["pad"]) for x in post_bad}
    new_bad = sorted(now - was)
    res["PP1"] = dict(ok=not new_bad and len(post) >= len(pre),
                      newly_unresolved=[dict(pour=k, pad=v) for k, v in new_bad],
                      unresolved_pre=len(pre_bad), unresolved_post=len(post_bad),
                      unresolved_inherited=sorted("%s %s" % (k.split("|")[0], v)
                                                  for k, v in sorted(was & now)),
                      pours_pre=len(pre), pours_post=len(post))

    splits, fragments = [], []
    for key, a in sorted(pre.items()):
        c = post.get(key)
        if c is None:
            splits.append(dict(pour=key, why="POUR_DISAPPEARED"))
            continue
        # group the PRE pads by their PRE island, then look at where they went
        groups = {}
        for ref, i in a["pads"].items():
            groups.setdefault(i, set()).add(ref)
        for i, refs in sorted(groups.items()):
            landed = {}
            for ref in refs:
                if ref in c["pads"]:
                    landed.setdefault(c["pads"][ref], set()).add(ref)
            if len(landed) <= 1:
                continue
            biggest = max(landed, key=lambda j: c["islands"][j]["area_mm2"])
            rec = dict(pour=key, net=a["net"], layer=a["layer"],
                       pre_island=i,
                       pre_area_mm2=a["islands"][i]["area_mm2"],
                       pre_pads=len(refs),
                       parts=[dict(post_island=j,
                                   area_mm2=c["islands"][j]["area_mm2"],
                                   pads=sorted(v),
                                   body=(j == biggest))
                              for j, v in sorted(landed.items())])
            splits.append(rec)
            for j, v in sorted(landed.items()):
                if j == biggest:
                    continue
                pr = price_fragment(post_path, a["net"], c["islands"][j], planes)
                fragments.append(dict(pour=key, net=a["net"], layer=a["layer"],
                                      post_island=j,
                                      area_mm2=c["islands"][j]["area_mm2"],
                                      pads=sorted(v), **pr))
    # -- PP2 ---------------------------------------------------------------- #
    # THE SPLITS ARE FOUND EXACTLY AS BEFORE; WHAT CHANGED IS THAT ONE MAY NOW
    # BE PRICED INSTEAD OF ONLY NAMED (D-628).  The controls run on every board,
    # split or not, so the clause is proved able to refuse on a run that has
    # nothing to admit.
    controls = decision_controls()
    dru = None
    for cand in (Path(post_path).with_suffix(".kicad_dru"),
                 Path(pre_path).with_suffix(".kicad_dru"),
                 PROJECT / "aqroot-Beta-v2.kicad_dru"):
        if cand.exists():
            dru = cand
            break
    table, table_src = published_rail_currents(dru) if dru else ({}, dict(
        source=None, found=False))
    priced_splits, geom, drills = [], None, None
    for rec in splits:
        if rec.get("why") == "POUR_DISAPPEARED":
            priced_splits.append(dict(pour=rec["pour"], admit=False,
                                      why="POUR_DISAPPEARED"))
            continue
        if geom is None:
            geom, drills = pour_geometry(post_path)
            pre_geom, _ = pour_geometry(pre_path)
        import pcbnew
        board = pcbnew.LoadBoard(str(post_path))
        net = rec["net"]
        n = board.FindNet(net)
        cls = n.GetNetClassName() if n else None
        row = table.get(cls)
        required = row["amps"] if row else None
        body = [p for p in rec["parts"] if p["body"]][0]
        pre_isl = pre_geom.get(rec["pour"], {}).get(rec["pre_island"])
        rows, admit = [], True
        for part in rec["parts"]:
            if part["body"]:
                continue
            isl = geom.get(rec["pour"], {}).get(part["post_island"])
            frag = next((f for f in fragments
                         if f["pour"] == rec["pour"]
                         and f["post_island"] == part["post_island"]), None)
            verdict = frag["verdict"] if frag else "STRANDED"
            if isl is None:
                rows.append(dict(post_island=part["post_island"],
                                 pads=part["pads"], admit=False,
                                 why="FRAGMENT_GEOMETRY_UNREADABLE"))
                admit = False
                continue
            price = bond_price(net, isl, planes, drills)
            ok, why = decide(verdict, price["priced_amps"], required)
            admit = admit and ok
            neck = None
            if pre_isl is not None:
                body_pads = [q for q in pre_isl["pads"]
                             if q["ref"] in body["pads"]]
                frag_pads = [q for q in pre_isl["pads"]
                             if q["ref"] in part["pads"]]
                neck = severed_neck(pre_isl, frag_pads, body_pads)
            rows.append(dict(post_island=part["post_island"],
                             pads=part["pads"],
                             area_mm2=part["area_mm2"],
                             pp3_verdict=verdict, admit=ok, why=why,
                             required_amps=required,
                             margin_x=(None if not (required and
                                                    price["priced_amps"])
                                       else round(price["priced_amps"]
                                                  / required, 3)),
                             price=price, severed_neck=neck))
        priced_splits.append(dict(
            pour=rec["pour"], net=net, netclass=cls, layer=rec["layer"],
            pre_island=rec["pre_island"], pre_area_mm2=rec["pre_area_mm2"],
            published_amps=required,
            published_figures=(row["figures"] if row else None),
            body=dict(post_island=body["post_island"],
                      area_mm2=body["area_mm2"], pads=body["pads"]),
            fragments=rows, admit=admit))
    refused = [s for s in priced_splits if not s["admit"]]
    res["PP2"] = dict(ok=(not refused) and controls["ok"] and (not splits
                                                              or bool(table)),
                      splits=splits,
                      priced=priced_splits,
                      admitted=[s["pour"] for s in priced_splits if s["admit"]],
                      refused=[dict(pour=s["pour"],
                                    why=sorted({f.get("why")
                                                for f in s.get("fragments", [])}
                                               or {s.get("why")}))
                               for s in refused],
                      published_rail_currents={
                          k: v["amps"] for k, v in sorted(table.items())},
                      published_table_source=table_src,
                      controls=controls,
                      islands={k: [pre[k]["n_islands"],
                                   post[k]["n_islands"]] for k in sorted(pre)
                               if k in post})
    res["PP3"] = dict(
        ok=all(f["verdict"] == "BONDED" for f in fragments),
        reserved_inner_planes={k: sorted(v) for k, v in reserved.items()},
        fragments=fragments)

    # -- PP4 ---------------------------------------------------------------- #
    # The knife: take every barrel away from each fragment and the verdict
    # must flip.  With nothing PROBEABLE -- no fragment at all, or every
    # fragment already condemned by PP3 -- the clause is exercised on the pour
    # the transaction DID touch, so it can still fail loudly.
    probes, condemned = [], []
    for f in fragments:
        # D-624 NAMED THIS AND D-625 TAKES IT.  PP4's knife is "every `BONDED`
        # verdict must FLIP to `STRANDED` when its barrels are stripped", and a
        # fragment PP3 has ALREADY condemned has nothing to flip: it is
        # `STRANDED` with its barrels in place and `STRANDED` without them, so
        # `all(flips)` goes false and the report reads `PP4 FAIL` beside
        # `PP3 FAIL` as though the knife itself had broken.  It had not.  The
        # fragment is skipped and NAMED here, PP3 keeps the operative refusal,
        # and -- because a run whose every fragment is condemned would
        # otherwise leave `probes` empty -- the whole-pour probe below still
        # runs and PP4 is still proved on this board.  Nothing is admitted that
        # PP3 refuses.
        if f["verdict"] != "BONDED":
            condemned.append(dict(pour=f["pour"], post_island=f["post_island"],
                                  pads=f["pads"], verdict=f["verdict"],
                                  why="PP3 has already condemned this "
                                      "fragment; a STRANDED fragment cannot "
                                      "FLIP when its barrels are stripped"))
            continue
        key = f["pour"]
        j = f["post_island"]
        frag = post[key]["islands"][j]
        cut = price_fragment(post_path, f["net"], frag, planes,
                             drop_barrels=frag["vias"])
        probes.append(dict(pour=key, post_island=j, pads=f["pads"],
                           with_barrels=f["verdict"],
                           without_barrels=cut["verdict"],
                           flips=(f["verdict"] == "BONDED"
                                  and cut["verdict"] == "STRANDED")))
    if not probes:
        # NOTHING TO PROBE IS THE GOOD OUTCOME AND IT MUST STILL BE PROVED.
        # Take
        # the largest pad-bearing island of every pour, strip its barrels and
        # require the pricing to report STRANDED, so the machinery that would
        # judge a fragment is exercised on this board even when there is none.
        for key, c in sorted(post.items()):
            cand = [(e["area_mm2"], j) for j, e in c["islands"].items()
                    if e["pads"] and e["vias"]]
            if not cand:
                continue
            # PROBE ONLY WHERE THE FLIP CAN MEAN SOMETHING.  `BQ25185_SYS`
            # owns two BOUNDED `B.Cu` pours and no reserved inner plane, so
            # its islands price STRANDED with their barrels in place and
            # STRANDED without them -- a true reading of that net and a
            # vacuous knife.  The clause is exercised where a reserved plane
            # exists to be cut off from, which on this board is `GND`
            # (`In1`/`In4`) and `+3V3` (`In3`).
            for _, j in sorted(cand, reverse=True):
                frag = c["islands"][j]
                live = price_fragment(post_path, c["net"], frag, planes)
                if live["verdict"] != "BONDED":
                    continue
                cut = price_fragment(post_path, c["net"], frag, planes,
                                     drop_barrels=frag["vias"])
                probes.append(dict(pour=key, post_island=j,
                                   pads=frag["pads"][:6],
                                   with_barrels=live["verdict"],
                                   without_barrels=cut["verdict"],
                                   flips=(cut["verdict"] == "STRANDED")))
                break
    res["PP4"] = dict(ok=bool(probes) and all(p["flips"] for p in probes),
                      probes=probes,
                      condemned_fragments_skipped=condemned)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD",
                    help="git revision holding the PRE board")
    ap.add_argument("--pre-board", type=Path,
                    help="a PRE board FILE instead of a git revision.  D-623: "
                         "the gate compares the AUTHORITATIVE board against "
                         "the refilled candidate, and neither of those is a "
                         "commit.  The file is read against its own sidecars, "
                         "so it must sit beside them")
    ap.add_argument("--board", default=str(BOARD),
                    help="the POST board (default: the authoritative one)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="aqroot-pp-") as tmp:
        pre = a.pre_board if a.pre_board else board_at(a.ref, tmp)
        res = compare(pre, Path(a.board))
    ok = all(res[k]["ok"] for k in ("PP1", "PP2", "PP3", "PP4"))
    doc = dict(schema=1, ref=(str(a.pre_board) if a.pre_board else a.ref),
               pre_board=str(a.pre_board) if a.pre_board else None,
               board=str(a.board), ok=ok, results=res)
    text = json.dumps(doc, indent=1, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for k in ("PP1", "PP2", "PP3", "PP4"):
        print("%s %s" % (k, "PASS" if res[k]["ok"] else "FAIL"))
    print("pour_partition_contract: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
