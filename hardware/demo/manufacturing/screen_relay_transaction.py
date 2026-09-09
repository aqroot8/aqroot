#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: the SIMULTANEOUS rip-up-and-relay.

D-637 closed by naming this as the first thing in five decisions whose closure
would be COPPER:

    BUILD THE SIMULTANEOUS RIP-UP-AND-RELAY -- re-propose the cut net WITH the
    opened pocket and the new stitch in ONE search.

`screen_segment_evict.py` reports four lands -- `+3V3 R39.1`, `GND C37.2`,
`GND J3.A12/B1` and `GND U9.16` -- that OPEN on a named cut and are then
refused, every one of them, by `relay_price`: the track comes out, the barrel
site appears, and the track will not go back.  Four `NO_PATH`s in a row read
like a wall, and D-637 recorded them as one.

THEY ARE NOT A WALL.  THEY ARE THE MODEL.

`relay_price` reserves the stitch by putting a KEEP-OUT DISC of the screen's
own cut radius at the barrel site, on ALL SIX copper layers, and then asks
`route_points` to put the track back between its own two ends.  On this board
the shrink ladder fails for three of the four lands, so that radius is the
8.0 mm SEARCH WINDOW -- a 16 mm hole through the whole stack -- and the
arithmetic is decisive:

    land        cut net                 r_mm   d(end A)  d(end B)
    R39.1       Net-(U11-TS_MR)         8.00      5.720     6.653
    R39.1       Net-(U11-TS_MR)         8.00      6.653     7.467
    C37.2       /ACC_DETECT_N           8.00      5.527     4.432
    C37.2       Net-(U11-TS_MR)         8.00      6.265     3.265
    J3.A12/B1   Net-(J3-CC2)            8.00      3.954     2.067
    U9.16       NFC_RFO2                2.00      1.860     0.836

EVERY ONE OF THE TWELVE ENDPOINTS IS INSIDE THE RESERVATION.  `point_terminals`
opens a terminal's own cell as a rasterisation courtesy and every neighbour of
it is guarded, so the wavefront cannot take a single step.  `NO_PATH` here is
not a statement about this board's congestion; it is a statement about a disc
that swallowed the question.

WHAT THE RESERVATION SHOULD HAVE BEEN IS THE STITCH ITSELF.  A stitch is an
escape stub, a run of `field.width` copper and one barrel -- 0.2 mm of copper
along a few millimetres and a 0.6 mm hole -- not a disc big enough to contain
the run.  The disc was a stand-in used because `relay_price` runs BEFORE
anything is laid.  This screen removes the stand-in: it LAYS THE REAL STITCH
and then relays the cut nets against it, so the relay is refused only by copper
that will actually be on the board.

    arm 0  `bare`    -- THE POSITIVE CONTROL.  Whole tracks held out and
                        NOTHING reserved and NOTHING laid, then `route_points`
                        between the chain's own two ends.  The only difference
                        between this board and the authoritative one is that
                        the track is not on it.
    arm A  `disc`    -- today's `relay_price`, reproduced verbatim: whole
                        tracks held out, an all-layer keep-out disc of radius
                        `cut_radius_mm` at the barrel site, `route_points`
                        between the same two ends, same budget.
    arm B  `stitch`  -- whole tracks held out, `maze3d.stitch_pad` LAID with
                        the same `land_ok` body certificate the measurement
                        used, then the same `route_points` between the same two
                        ends, same budget, against the real copper.
    arm C  `joint`   -- THE SIMULTANEOUS TRANSACTION.  Arm B repeated with the
                        barrel site of every stitch that stranded a relay
                        struck out of `land_ok`, so the search chooses a stitch
                        THIS BOARD CAN STILL PUT THE TRACK BACK AROUND.

EVERY ARM RUNS ON THE SAME BOARD, THE SAME `Field`, THE SAME RUNG AND THE SAME
BUDGET, and every trial is reverted, so a track that goes back in one arm and
not another differs by the reservation and by nothing else.

WHAT THE FIRST RUN MEASURED, AND IT IS NOT WHAT FIVE DECISIONS ASSUMED.  On
three of the four lands the track goes back in arm 0 AT ITS OWN LENGTH TO THE
MICRON -- `Net-(U11-TS_MR)` 4.3353 mm against 4.3353, `/ACC_DETECT_N` 5.4509
against 5.4509, `NFC_RFO2` 2.6872 against 2.6872 -- so the lattice reproduces
this board's legacy copper exactly, the pocket is not congested, and neither
the cut nor the board is the wall.  Those same three fail in arm B.  THE THING
THAT REFUSES THE RELAY IS THE STITCH'S OWN COPPER: `stitch_pad` takes the
FIRST legal barrel by distance and has no way to know it is about to strand a
track the same transaction has to put back.  That is what arm C is for.

The fourth land is different in kind and is now named: `GND J3.A12/B1`'s
`Net-(J3-CC2)` will not go back on a board where NOTHING else changed.  That is
a `LATTICE_WALL` -- a refusal of the instrument, not of the board -- and it
belongs to the grid, not to this transaction.

WHAT IS PROVED AND WHAT IS NOT.  Every piece of copper this screen lays is
proved by the promoter's own `maze3d.verify_laid` -- `stitch_pad` proves the
stub, the run and the barrel; `_emit_path` proves each relay segment including
the exact-coordinate connectors at both ends -- and a transaction whose relay
cannot be proved is reverted whole and reported failed.  The barrel is also put
through `maze3d._antipad_severs`, because a through hole is a slot in every
foreign pour it passes and D-605 paid a gate run to learn it.  What is NOT
proved here is the refill: clause 4 counts KiCad's clusters after
`--refill-zones`, and only the whole-board gate can do that.  A land reported
`TRANSACTION_CLOSES` is a licence to spend a gate run, not a promise.

NOTHING IS WRITTEN.  The authoritative board is opened once, read, and its
sha256 is re-checked at exit.
"""

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

from screen_segment_evict import (Held, chain_ends_mm, LAYER_NAME,
                                  RELIEF_WIDTH, RELIEF_CLR, RELIEF_VIA_DIA,
                                  RELIEF_VIA_DRILL)

EVIDENCE = HERE / "evidence/d637-segment-evict.json"


def find_seg(qb, rec):
    """The live `SEG` on `qb.shapes` that a cut record names.

    A cut record is geometry in mm rounded to 4 places; the obstacle model
    holds integer nm.  Matching on the rounded endpoints in either order, the
    net, the layer and the width is exact for every track this board carries,
    and a record that matches none is an error rather than a silent skip --
    a relay measured against the wrong track is worse than no measurement.
    """
    want = sorted([tuple(rec["a_mm"]), tuple(rec["b_mm"])])
    hits = []
    for s in qb.shapes[rec["layer"]]:
        if s.tag != 'track' or s.net != rec["net"]:
            continue
        got = sorted([(round(s.x0 / 1e6, 4), round(s.y0 / 1e6, 4)),
                      (round(s.x1 / 1e6, 4), round(s.y1 / 1e6, 4))])
        if got == want and abs(2 * s.hw / 1e6 - rec["width_mm"]) < 1e-6:
            hits.append(s)
    return hits


def disc_guard(site, radius, exempt):
    """`relay_price`'s reservation, verbatim: one tube per copper layer."""
    return dict(guards=[dict(ok=True, net=(exempt[0] if exempt else ""),
                             exempt=list(exempt[1:]), lkey=lk,
                             keepout_radius=int(radius),
                             points=[[int(site[0]), int(site[1])]],
                             tube="DETOUR_RESERVE_1")
                        for lk in ("F", "I1", "I2", "I3", "I4", "B")])


def relay_nets(qb, grid, reserved, by_net, spec, extra_guard, radius,
               own_layer, via_cost_mm=1.5, slack_mm=0.0):
    """Put every cut net back between its own two ends, in spec order.

    Shares `relay_price`'s judgements exactly -- `permitted_layers` for the
    layer, `detour_layers` for the own-layer allowance, `chain_ends_mm` for the
    terminals, `was + 2*pi*R` for the budget -- and differs in one respect
    only: `extra_guard` may be empty, in which case the only thing the relay
    must avoid is copper that is really there.
    """
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers, guard_for,
                                  detour_layers)

    out, ok_all = [], True
    for net in sorted(by_net):
        recs = [c for (_L, _s, c) in by_net[net]]
        lkeys = {c["layer"] for c in recs}
        widths = {c["width_mm"] for c in recs}
        con = net_contract(qb.b, net)
        permitted = permitted_layers(qb.routable, con["layers"], reserved, net)
        was = sum(c["mm"] for c in recs)
        rec = dict(net=net, layer=sorted(lkeys), was_mm=round(was, 4),
                   max_mm=round(was + (slack_mm if slack_mm else
                                       2.0 * math.pi * radius / 1e6), 4),
                   slack_mm=slack_mm or None, tracks=len(recs))
        if len(lkeys) != 1 or len(widths) != 1:
            rec.update(ok=False, reason="NOT_A_CHAIN",
                       why="a chain must be ONE layer and ONE width")
            out.append(rec); ok_all = False
            continue
        lkey = sorted(lkeys)[0]
        layers, spent = detour_layers(permitted, lkey, own_layer)
        rec.update(layers_allowed=list(layers), own_layer=spent)
        if lkey not in layers:
            rec.update(ok=False, reason="UNDETOURABLE_LAYER",
                       why="layer %s is not in this net's contract %s"
                           % (lkey, list(layers)))
            out.append(rec); ok_all = False
            continue
        ends = chain_ends_mm(recs)
        if ends is None:
            rec.update(ok=False, reason="NOT_A_CHAIN",
                       why="the cut tracks of this net do not form a simple "
                           "chain with exactly two free ends")
            out.append(rec); ok_all = False
            continue
        g = guard_for(spec, net) if spec else {}
        if extra_guard:
            for lk, pts in guard_for(extra_guard, net).items():
                g.setdefault(lk, []).extend(pts)
        width_nm = int(round(sorted(widths)[0] * 1e6))
        qb._obs_cache = None
        field = mz.Field(qb, net, width_nm, con["clr_pad"], con["clr"],
                         con["via_dia"], con["via_drill"], G=grid,
                         layers=layers, guard=g)
        a_nm = tuple(int(round(v * 1e6)) for v in ends[0])
        b_nm = tuple(int(round(v * 1e6)) for v in ends[1])
        r = mz.route_points(qb, field, a_nm, b_nm, lkey,
                            via_cost_mm=via_cost_mm, emit=True,
                            max_mm=rec["max_mm"])
        rec.update(ok=bool(r.get("ok")), reason=r.get("reason"),
                   why=str(r.get("why"))[:200] if r.get("why") else None,
                   mm=r.get("mm"), vias=r.get("vias"),
                   mm_by_layer=r.get("mm_by_layer"),
                   via_xy=r.get("via_xy"),
                   a_mm=list(ends[0]), b_mm=list(ends[1]))
        ok_all = ok_all and bool(r.get("ok"))
        out.append(rec)
    return ok_all, out


def stitch_geometry(qb, mark):
    """Every object laid since `mark`, as layer-keyed nm geometry.

    `qb.laid` is the promoter's own record of what it emitted, so this reads
    the transaction rather than reconstructing it.
    """
    import pcbnew
    n = mark[0]
    lkey = {}
    for k, v in (("F", pcbnew.F_Cu), ("I1", pcbnew.In1_Cu),
                 ("I2", pcbnew.In2_Cu), ("I3", pcbnew.In3_Cu),
                 ("I4", pcbnew.In4_Cu), ("B", pcbnew.B_Cu)):
        lkey[v] = k
    tracks, vias = [], []
    for t in qb.laid[n:]:
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            vias.append(dict(xy_nm=[int(p.x), int(p.y)],
                             dia_nm=int(t.GetWidth(pcbnew.F_Cu))
                             if hasattr(t, "GetDrill") else None,
                             drill_nm=int(t.GetDrill())))
        elif t.GetClass() == "PCB_TRACK":
            tracks.append(dict(lkey=lkey.get(t.GetLayer(), "?"),
                               width_nm=int(t.GetWidth()),
                               a_nm=[int(t.GetStart().x), int(t.GetStart().y)],
                               b_nm=[int(t.GetEnd().x), int(t.GetEnd().y)]))
    return dict(tracks=tracks, vias=vias)


def sever_shapes(*tagged):
    """(net, `stitch_geometry` record) pairs -> `maze3d.copper_severs` shapes.

    A barrel is copper on every layer and carries no `lkey`; a track is copper
    on exactly one and carries its own.  EVERY SHAPE CARRIES ITS OWN NET,
    because which pours a piece of copper can cut is decided by whose copper it
    is: the stitch belongs to the plane net and is invisible to that net's own
    pour, and the RELAY belongs to the cut net and is not.  D-639.
    """
    shapes = []
    for (snet, g) in tagged:
        if not g:
            continue
        for v in g.get("vias", ()):
            shapes.append(dict(kind="via", net=snet, xy=tuple(v["xy_nm"]),
                               dia=int(v.get("dia_nm") or 0)))
        for t in g.get("tracks", ()):
            shapes.append(dict(kind="seg", net=snet, a=tuple(t["a_nm"]),
                               b=tuple(t["b_nm"]), width=int(t["width_nm"]),
                               lkey=t.get("lkey")))
    return shapes


def laid_shapes(qb, mark):
    """Everything emitted since `mark`, as net-tagged `copper_severs` shapes.

    The relay can lay more than one net in one pass -- `GND C37.2` is two --
    so the net is read off each object rather than assumed from the caller.
    """
    import pcbnew
    lkey = {}
    for k, v in (("F", pcbnew.F_Cu), ("I1", pcbnew.In1_Cu),
                 ("I2", pcbnew.In2_Cu), ("I3", pcbnew.In3_Cu),
                 ("I4", pcbnew.In4_Cu), ("B", pcbnew.B_Cu)):
        lkey[v] = k
    shapes = []
    for t in qb.laid[mark[0]:]:
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            shapes.append(dict(kind="via", net=t.GetNetname(),
                               xy=(int(pos.x), int(pos.y)),
                               dia=int(t.GetWidth(pcbnew.F_Cu))))
        elif t.GetClass() == "PCB_TRACK":
            shapes.append(dict(kind="seg", net=t.GetNetname(),
                               a=(int(t.GetStart().x), int(t.GetStart().y)),
                               b=(int(t.GetEnd().x), int(t.GetEnd().y)),
                               width=int(t.GetWidth()),
                               lkey=lkey.get(t.GetLayer(), "?")))
    return shapes


def pour_nets(qb):
    """Every net that owns filled copper, in a deterministic order."""
    return sorted({z.GetNetname() for z in qb.b.Zones()
                   if not z.GetIsRuleArea() and z.IsFilled()
                   and z.GetNetname()})


def pour_severs(qb, mz, net, shapes, via_dia):
    """Every filled island this transaction's copper would cut in two.

    D-638 spent a full-authority gate run learning that the barrel is not the
    only pair of scissors: the 17.2 mm RELAY TRACK it emitted split `GND`'s
    `B.Cu` pour 58 -> 59 and clause `PP2` refused the run.  So the price is
    taken over the WHOLE transaction -- the stitch's stub, its run, its barrel,
    and every segment and barrel the relay itself laid -- and a barrel's own
    dia is defaulted from the field when `stitch_geometry` could not read one.

    AND IT IS TAKEN OVER EVERY POUR ON THE BOARD, NOT MERELY THE FOREIGN ONES.
    `mz._foreign_pours(qb, net)` is the right list for a BARREL the stitch
    plants, which is the plane net's own copper; it is the wrong list for the
    transaction, because the relay is the CUT net's copper and the cut net is
    not the plane net.  `GND U9.16` is exactly that shape -- a `GND` stitch
    whose relay is `NFC_RFO2`, which can slot the `GND` pour the stitch is
    aiming at.  So each pour is priced against every shape that is not its own
    net's, and a pour with nothing foreign in it is skipped for free.
    """
    shapes = [dict(s, dia=(s["dia"] or int(via_dia)))
              if s["kind"] == "via" else s for s in shapes]
    out = []
    for n in pour_nets(qb):
        mine = [s for s in shapes if s.get("net") != n]
        if not mine:
            continue
        out += [dict(pour=n, own_net=(n == net), layer=lname,
                     mm2=round(area, 2), why=why)
                for (lname, _idx, _poly, area, why)
                in mz.copper_severs(qb, n, mine)]
    return out


SPLIT_PRICE_SIDECARS = ("kicad_pro", "kicad_dru", "kicad_prl")


def split_price(qb, base_board, work, tag, cuts=()):
    """PRICE a foreign-pour split with the board's OWN `PP2` clause -- D-674.

    `pour_severs` below strikes out any round whose transaction cuts a filled
    island in two.  That was the right rule on the day it was written: D-638
    spent a real gate run on exactly such a round and `PP2` refused it, and a
    screen that reports a split and accepts anyway is a screen that spends gate
    runs.  **D-643 replaced that rule with a number** -- a return fragment is
    priced against the conductor the board publishes for its own ground
    (0.300 mm of netclass track, 0.995 A at this copper), raised by Kirchhoff
    at the part -- and this screen was never told.  So it has gone on refusing,
    for thirty-five decisions, splits the contract it stands in for would
    ADMIT: `+3V3 R39.1`, the TOP LEG OF THE 3.3 V REGULATOR'S FEEDBACK DIVIDER,
    is carried in the ledger as REFUSED on that ground alone.

    A SCREEN MAY NOT HOLD AN OPINION ITS OWN CONTRACT HAS RETIRED.  So the
    price is not re-derived here -- there is no second implementation of the
    bar to drift from the first.  The candidate board is written out, KiCad's
    own filler refills it, and `checks/pour_partition_contract.py` is run
    against the base board exactly as the gate runs it.  What comes back is the
    gate's answer, one clause early and for a fraction of the cost.

    D-675: AND THE BOARD PRICED IS THE BOARD THE TRANSACTION PRODUCES.
    `Held` removes a cut track from the ROUTER's obstacle model (`qb.shapes`)
    and never from the `pcbnew` BOARD, because every other arm of this screen
    reverts and needs the board back.  `qb.save()` therefore wrote a candidate
    that still carried the copper this transaction REMOVES -- authority PLUS
    the stitch, the arm and the relay, with the cut still on it.  That copper
    is a foreign object inside the pour being priced, so it can only make a
    fragment NARROWER or SMALLER than the transaction's own geometry, and a
    clause that refuses on 3.3% of a width cannot be asked on copper that is
    not there afterwards.  So `cuts` -- the same records `find_seg` resolved
    the held segments from, in mm -- are deleted from the candidate FILE by
    the refill child, one track per record, matched on net, layer, endpoints
    in either order and width.  `qb.b` is never touched: the deletion happens
    in the child process on its own `LoadBoard`, so no arm of this screen and
    no later round can see it.  A record that matches nothing is REPORTED
    (`cuts_not_removed`) rather than skipped -- a price taken on the wrong
    board is worse than no price.

    Returns the contract's own `{ok, results}` document with the candidate's
    sha256, or a record carrying `error` when the child could not be run.  It
    is NEVER a licence: `ok` false refuses the round exactly as `pour_severs`
    did, and a caller that does not ask for it (`--split-priced` off) reaches
    none of this code -- with the flag off the search is D-639's to the object
    and the artifact gains three explicit null/false keys and nothing else.
    """
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    cand = work / ("split-%s.kicad_pcb" % tag)
    # THE SIDECARS TRAVEL WITH THE BOARD.  A scratch `.kicad_pcb` without its
    # `.kicad_pro` silently drops every netclass to `Default`, and the return
    # bar is resolved THROUGH the netclass table -- so a missing project file
    # would not fail, it would answer the wrong question.
    for ext in SPLIT_PRICE_SIDECARS:
        src = base_board.with_suffix("." + ext)
        if src.exists():
            shutil.copy(src, cand.with_suffix("." + ext))
    qb.save(str(cand))
    # THE WHOLE BOARD IS READ BEFORE ANYTHING IS REMOVED.  `BOARD::Remove`
    # invalidates the track container mid-walk -- a second `GetTracks()` pass
    # after one removal hands back an untyped `SwigPyObject` and the match
    # raises -- so every track's identity is taken in ONE pass, the records
    # are matched against that snapshot, and the removals happen afterwards.
    fill = (
        "import sys, json, pcbnew\n"
        "b = pcbnew.LoadBoard(sys.argv[1])\n"
        "want = json.loads(sys.argv[2])\n"
        "seen = []\n"
        "for t in b.GetTracks():\n"
        "    if t.GetClass() == 'PCB_VIA':\n"
        "        continue\n"
        "    seen.append((t.GetNetname(),\n"
        "                 b.GetLayerName(t.GetLayer()),\n"
        "                 round(t.GetWidth() / 1e6, 6),\n"
        "                 sorted([(round(t.GetStart().x / 1e6, 4),\n"
        "                          round(t.GetStart().y / 1e6, 4)),\n"
        "                         (round(t.GetEnd().x / 1e6, 4),\n"
        "                          round(t.GetEnd().y / 1e6, 4))]),\n"
        "                 t))\n"
        "left, kill, used = [], [], set()\n"
        "for rec in want:\n"
        "    key = [rec['net'], rec['layer'], round(rec['width_mm'], 6),\n"
        "           sorted([tuple(rec['a_mm']), tuple(rec['b_mm'])])]\n"
        "    hit = None\n"
        "    for idx, row in enumerate(seen):\n"
        "        if idx in used:\n"
        "            continue\n"
        "        if list(row[:4]) == key:\n"
        "            hit = idx\n"
        "            break\n"
        "    if hit is None:\n"
        "        left.append(rec)\n"
        "    else:\n"
        "        used.add(hit)\n"
        "        kill.append(seen[hit][4])\n"
        "for t in kill:\n"
        "    b.Remove(t)\n"
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones())\n"
        "b.BuildConnectivity()\n"
        "b.Save(sys.argv[1])\n"
        "open(sys.argv[3], 'w').write(json.dumps(left))\n")
    # THE CUT RECORD TRAVELS AS THE SCREEN READ IT.  `find_seg` already proved
    # each of these resolves to exactly one live segment on the obstacle
    # model, and the child matches the same four fields on the board file, so
    # the copper removed here is the copper `Held` held out and nothing else.
    # `layer` on a cut record is the OBSTACLE MODEL's key (`B`, `I3`); the
    # child matches `pcbnew`'s own layer NAME (`B.Cu`, `In3.Cu`).  `LAYER_NAME`
    # is the one mapping this repository keeps, so the translation happens
    # here and not in a second table.
    spec = [dict(net=c["net"], layer=LAYER_NAME[c["layer"]],
                 width_mm=c["width_mm"],
                 a_mm=list(c["a_mm"]), b_mm=list(c["b_mm"])) for c in cuts]
    # THE LEFTOVERS COME BACK IN A FILE, NOT ON `stdout`.  `pcbnew` writes
    # SWIG and wxWidgets chatter to both streams, so a JSON document parsed
    # off `stdout` would be at the mercy of a memory-leak notice.
    leftover = work / ("split-%s-unremoved.json" % tag)
    r = subprocess.run([sys.executable, "-c", fill, str(cand),
                        json.dumps(spec), str(leftover)],
                       capture_output=True, text=True)
    if r.returncode:
        return dict(ok=False, error="REFILL_FAILED",
                    stderr=r.stderr[-400:])
    try:
        not_removed = json.loads(leftover.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        not_removed = None
    rep = work / ("split-%s-pp.json" % tag)
    r = subprocess.run(
        [sys.executable, str(HERE / "checks" / "pour_partition_contract.py"),
         "--pre-board", str(base_board), "--board", str(cand),
         "-o", str(rep)],
        capture_output=True, text=True)
    if not rep.exists():
        return dict(ok=False, error="CONTRACT_DID_NOT_RUN",
                    returncode=r.returncode, stderr=r.stderr[-400:])
    doc = json.loads(rep.read_text(encoding="utf-8"))
    return dict(ok=bool(doc.get("ok")),
                clause={k: doc["results"][k]["ok"]
                        for k in ("PP1", "PP2", "PP3", "PP4")
                        if k in doc.get("results", {})},
                candidate_sha256=hashlib.sha256(cand.read_bytes()).hexdigest(),
                report=str(rep),
                cuts_removed=len(spec) - (len(not_removed)
                                          if not_removed is not None
                                          else len(spec)),
                cuts_not_removed=not_removed,
                splits=doc.get("results", {}).get("PP2", {}).get("splits"),
                fragments=doc.get("results", {}).get("PP2", {}).get("fragments"))


def plant_bonds(qb, mz, net_contract, permitted_layers,
                reserved, grid, neck, spec, requests):
    """Lay the copper `route_maze_batch.py --bond-pad` would lay -- D-675.

    A `--split-priced` round is judged by `PP2`, and `PP2` prices a fragment
    at the widest tube from each of its pads to a BARREL THAT IS THERE.  On
    `+3V3 R39.1` that is the whole verdict: the `GND` east-margin ribbon the
    relay shears off holds `C27.2` and `C28.2`, the only barrel within 6 mm of
    `C28.2` sits 1.181 mm away down a wedge, and the tube to it is 0.850 mm --
    2.117 A against a 2.190 A bar, 3.3% short.  The copper AROUND `C28.2` is
    1.9 mm wide; nothing needed widening.  What was missing was a barrel in
    the wide part, and `route_maze_batch.py --bond-pad` has planted exactly
    that kind of barrel since D-591.

    So a caller that intends to run the transaction WITH a `--bond-pad` may
    say so, and the round is then priced on the board that transaction
    produces.  The bond is not re-implemented here: `maze3d.bond_pads` is the
    writer's own primitive and is called with the writer's own `Field`, so the
    site this screen prices is the site the writer will plant.  Everything is
    laid on `qb` inside the round's existing mark, so the caller's `revert`
    takes it off again with the stitch and the relay.

    This is NEVER a licence.  The barrel still has to be legal (`Field.via_ok`
    and `verify_laid` inside `stitch_pad`), the split is still priced by
    `checks/pour_partition_contract.py`, and `ok` false still refuses the
    round.  What it removes is a measurement that was never the transaction's.
    """
    from route_maze_batch import guard_for
    out = []
    for (bnet, refs) in requests:
        c = net_contract(qb.b, bnet)
        layers = permitted_layers(qb.routable, c["layers"], reserved, bnet)
        fld = mz.Field(qb, bnet, c["width"], c["clr_pad"], c["clr"],
                       c["via_dia"], c["via_drill"], G=grid, layers=layers,
                       neck=neck, guard=(guard_for(spec, bnet) if spec
                                         else None))
        r = mz.bond_pads(qb, bnet, fld, list(refs))
        out.append(dict(net=bnet, requested=list(refs),
                        bonded=r.get("bonded", 0),
                        ok=bool(r.get("ok")),
                        vias=[list(b.get("via_xy") or ()) for b in
                              (r.get("bonds") or ())],
                        mm=r.get("mm"),
                        failures=[dict(pad=f.get("pad"),
                                       reason=f.get("reason"))
                                  for f in (r.get("failures") or ())]))
    return out


def joint_search(qb, field, held, by_net, pad, land_ok, max_mm, grid,
                 reserved, spec, own_layer, via_dia, net, mz, radius,
                 tries=12, knock_mm=1.0, slack_mm=0.0,
                 priced_split=None, bond_req=(), bond_ctx=None):
    """THE SIMULTANEOUS RIP-UP-AND-RELAY, D-637's first-ranked item.

    Arm B proved that what refuses these relays is the stitch itself: the
    barrel `stitch_pad` picks is the CHEAPEST one, and the run that reaches it
    lies across the corridor the cut track has to come back through.  Neither
    half is wrong on its own; the transaction is what is over-determined.

    So the two halves are searched TOGETHER.  Each round lays a stitch, tries
    the whole relay against it, and -- if any track is stranded -- strikes that
    barrel's own neighbourhood out of `land_ok` and asks for the next one.  The
    first stitch the relay survives is a JOINT solution: one barrel that closes
    the plane land and one corridor per cut net that still fits around it.

    `land_ok` is narrowed and never widened, so this cannot invent a site
    `body_landing` refused; every round is proved by `verify_laid` inside
    `stitch_pad` and `_emit_path` exactly as arm B is; and every round is
    reverted whether it succeeded or not, so the LAST round is re-laid by the
    caller only in the report, never on the board.
    """
    import numpy as np
    mask = None if land_ok is None else land_ok.copy()
    rounds, best = [], None
    for k in range(tries):
        with Held(qb, field, held):
            m = qb.mark()
            st = mz.stitch_pad(qb, field, pad, max_mm=max_mm,
                               escape_limit=12, land_ok=mask)
            # READ THE STITCH'S GEOMETRY BEFORE THE RELAY IS LAID.  `qb.laid`
            # grows as the transaction proceeds and a reservation that
            # included the relay's OWN copper would be a keep-out over the
            # path the writer has to put that track back along -- the same
            # class of mistake as the disc, one level down.
            geom = None if not st.get("ok") else stitch_geometry(qb, m)
            if not st.get("ok"):
                rounds.append(dict(round=k + 1, stitch_ok=False,
                                   reason=st.get("reason"),
                                   why=str(st.get("why"))[:180]
                                   if st.get("why") else None))
                qb.revert(m)
                break
            # THE SAME BUDGET AS EVERY OTHER ARM.  Nothing is reserved here,
            # but the bound a detour is judged by must not move between arms
            # or the comparison stops being one.
            # THE RELAY'S OWN GEOMETRY, READ THE SAME WAY THE STITCH'S IS.
            # D-639: the relay is copper this transaction lays, so it owes the
            # same price to every foreign pour it crosses, and the only way to
            # charge it is to read the objects `_emit_path` actually emitted.
            m2 = qb.mark()
            ok_all, tracks = relay_nets(qb, grid, reserved, by_net, spec,
                                        None, radius, own_layer,
                                        slack_mm=slack_mm)
            rgeom = stitch_geometry(qb, m2) if ok_all else None
            sev = None
            if ok_all:
                sites = [(int(st["via_xy_nm"][0]), int(st["via_xy_nm"][1]))]
                for t in tracks:
                    for (vx, vy) in (t.get("via_xy") or []):
                        sites.append((int(round(vx * 1e6)),
                                      int(round(vy * 1e6))))
                sev = [dict(pour=n, layer=lname, mm2=round(area, 2), why=why)
                       for n in mz._foreign_pours(qb, net)
                       for (lname, _idx, _poly, area, why)
                       in mz._antipad_severs(qb, n, sites, via_dia)]
                psev = pour_severs(
                    qb, mz, net,
                    sever_shapes((net, geom)) + laid_shapes(qb, m2),
                    via_dia)
            else:
                psev = None
            # A STITCH WHOSE TRANSACTION SPLITS A FOREIGN POUR IS STRUCK OUT
            # EXACTLY AS ONE THAT STRANDS A RELAY IS.  D-638's gate run refused
            # the whole transaction for this and nothing else; a screen that
            # reports it and accepts anyway is a screen that spends gate runs.
            #
            # D-674: UNLESS THE CALLER ASKS FOR THE PRICE.  D-643 turned that
            # unconditional refusal into a number and this screen was never
            # told, so it has gone on refusing splits its own contract would
            # admit.  With `--split-priced` the round is put to
            # `pour_partition_contract.py` itself -- the gate's clause, not a
            # second copy of it -- and accepted only if that says PASS.  The
            # default is OFF, so every run and every artifact written before
            # this reads exactly as it did.
            price, bonds = None, None
            if ok_all and psev and priced_split is not None:
                # D-675: THE BOARD PRICED IS THE BOARD THE TRANSACTION
                # PRODUCES -- both halves of that.  The cut records travel
                # with it (`by_net` is the same mapping `find_seg` built, so
                # no geometry is re-derived), and so does any `--bond-pad`
                # the caller intends to run WITH the detour, laid here by the
                # writer's own primitive so the site cannot drift.
                if bond_req and bond_ctx is not None:
                    bonds = plant_bonds(qb, mz, bond_ctx["net_contract"],
                                        bond_ctx["permitted_layers"],
                                        bond_ctx["reserved"], grid,
                                        bond_ctx["neck"], spec, bond_req)
                price = split_price(qb, priced_split[0], priced_split[1],
                                    "%s-%d" % (priced_split[2], k + 1),
                                    cuts=[cr for v in by_net.values()
                                          for (_L, _s, cr) in v])
                good = bool(price.get("ok"))
            else:
                good = bool(ok_all and not psev)
            rounds.append(dict(
                round=k + 1, stitch_ok=True, stitch_mm=st.get("mm"),
                stitch_layer=st.get("layer"),
                via_xy=list(st.get("via_xy")), all_relaid=bool(ok_all),
                accepted=good,
                antipad_severs=sev, pour_severs=psev, split_price=price,
                split_bonds=bonds,
                relays=[dict(net=t["net"], ok=t["ok"], reason=t.get("reason"),
                             mm=t.get("mm"), vias=t.get("vias"),
                             was_mm=t.get("was_mm"))
                        for t in tracks]))
            if good:
                # THE GEOMETRY THE TRANSACTION HAS TO RESERVE.  The relay was
                # refused by the stitch's own copper, so what the writer must
                # hold clear is that copper's PATH, layer by layer -- not a
                # disc, which is the mistake this whole screen exists to
                # correct.  It is read off the objects `stitch_pad` actually
                # laid, never re-derived, so the plan and the measurement are
                # the same geometry.
                best = dict(stitch=dict(ok=True, reason=None,
                                        mm=st.get("mm"),
                                        layer=st.get("layer"),
                                        via_xy=list(st.get("via_xy")),
                                        via_xy_nm=list(st["via_xy_nm"]),
                                        why=None),
                            stitch_geometry=geom, relay_geometry=rgeom,
                            antipad_severs=sev, pour_severs=psev,
                            split_price=price, split_bonds=bonds,
                            tracks=tracks)
            qb.revert(m)
        if best is not None:
            break
        # Strike this barrel's neighbourhood out and ask for the next one.
        vx, vy = st["via_xy_nm"]
        if mask is None:
            mask = np.ones((field.ny, field.nx), dtype=bool)
        ci, cj = field.cell(vx, vy)
        r = max(1, int(round(knock_mm * 1e6 / field.G)))
        j0, j1 = max(0, cj - r), min(field.ny, cj + r + 1)
        i0, i1 = max(0, ci - r), min(field.nx, ci + r + 1)
        jj, ii = np.ogrid[j0:j1, i0:i1]
        mask[j0:j1, i0:i1] &= (((ii - ci) ** 2 + (jj - cj) ** 2) > r * r)
    out = dict(reservation="none -- the stitch and the relay are searched "
                           "TOGETHER, and a stitch that strands a relay is "
                           "struck out and retried",
               tries=tries, knockout_mm=knock_mm, slack_mm=slack_mm or None,
               rounds=rounds,
               all_relaid=best is not None,
               priced_against_foreign_pours=True,
               split_priced=priced_split is not None,
               note=None if best is not None else
                    "no barrel in %d tries left every cut net a corridor it "
                    "could take without splitting a foreign pour"
                    % len(rounds))
    if best is not None:
        out.update(best)
    else:
        # A REFUSAL MUST CARRY ITS REASON.  When no round was accepted the
        # verdict block below still reads `pour_severs`, and a `None` there
        # would read as "nothing was cut" when the truth may be "every round
        # was cut".  So the refusal carries the union of what the rounds saw.
        out.update(stitch=None, antipad_severs=None, tracks=[],
                   split_bonds=None,
                   split_price=[r["split_price"] for r in rounds
                                if r.get("split_price")] or None,
                   pour_severs=[x for r in rounds
                                for x in (r.get("pour_severs") or ())] or None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--evidence", type=Path, default=EVIDENCE,
                    help="a screen_segment_evict.py artifact; the cut this "
                         "screen relays is the one that screen measured, so "
                         "the measurement and the transaction cannot drift")
    ap.add_argument("--land", action="append", default=[], metavar="NET:REF",
                    help="only this land, e.g. '+3V3:R39.1'.  Repeatable")
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--arm", choices=("bare", "disc", "stitch", "joint",
                                      "all"), default="all")
    ap.add_argument("--joint-tries", type=int, default=12,
                    help="arm C: how many distinct barrel sites to offer")
    ap.add_argument("--relay-slack-mm", type=float, default=0.0,
                    help="cap every relay at `was + SLACK` millimetres.  The "
                         "default 0 keeps the measurement's own bound "
                         "(`was + 2*pi*R`), which is deliberately generous and "
                         "is a BUDGET, not a price: `Net-(U11-TS_MR)` closes "
                         "the `+3V3 R39.1` land inside it at 17.087 mm having "
                         "been 4.335, and that net is the charger's TS/MR "
                         "sense input.  A transaction is only worth promoting "
                         "at a slack the board can afford, so state it")
    ap.add_argument("--joint-knockout-mm", type=float, default=1.0,
                    help="arm C: radius struck out of `land_ok` around a "
                         "barrel whose stitch stranded a relay.  Small enough "
                         "that a genuinely different pocket survives, big "
                         "enough that the next site is not the same run one "
                         "cell over")
    ap.add_argument("--guard", type=Path)
    ap.add_argument("--relay-own-layer", action="store_true",
                    help="D-609's own-layer allowance, as the measurement used")
    ap.add_argument("--split-priced", action="store_true",
                    help="D-674: when this transaction SPLITS a filled island, "
                         "put the split to `checks/pour_partition_contract.py` "
                         "-- the gate's own PP1-PP4 clauses on the refilled "
                         "candidate against this base board -- instead of "
                         "striking the round out unconditionally.  D-639 wrote "
                         "that strike-out and D-643 replaced the rule behind "
                         "it with a number (a return fragment is priced at the "
                         "0.300 mm netclass conductor the board publishes for "
                         "its own ground, raised by Kirchhoff at the part), so "
                         "this screen has been refusing splits its own "
                         "contract would ADMIT.  Never a licence: the answer "
                         "is the contract's, `ok` false still refuses the "
                         "round.  With the flag OFF the search is the one D-639 "
                         "wrote, to the object, and the artifact gains exactly "
                         "three keys and nothing else -- `split_priced` false, "
                         "`split_price_work` null, and a null `split_price` on "
                         "each round that laid a stitch"
                    )
    ap.add_argument("--split-bond-pad", action="append", default=[],
                    metavar="NET:REF.NUM",
                    help="D-675: the transaction this plan will be RUN with "
                         "also plants `route_maze_batch.py --bond-pad REF.NUM` "
                         "on NET, so price the split on THAT board.  `PP2` "
                         "prices a fragment at the widest tube from each of "
                         "its pads to a barrel that IS THERE, and on `+3V3 "
                         "R39.1` the whole 3.3% deficit is one missing "
                         "barrel: the `GND` ribbon around `C28.2` is 1.9 mm "
                         "wide and the only barrel within 6 mm sits 1.181 mm "
                         "away down a 0.850 mm wedge.  The bond is laid by "
                         "`maze3d.bond_pads` -- the writer's own primitive, "
                         "the writer's own `Field` -- so the site priced here "
                         "is the site the writer plants, and it is reverted "
                         "with the rest of the round.  Requires "
                         "`--split-priced`; a plan emitted from a round that "
                         "used it CARRIES the bond, so a writer run without "
                         "it is running a different transaction.  Repeatable"
                    )
    ap.add_argument("--split-price-work", type=Path,
                    help="where --split-priced writes each candidate board and "
                         "its contract report (default: a temporary directory "
                         "discarded at exit).  State it to keep the evidence")
    ap.add_argument("--plan-out", type=Path,
                    help="write the `route_maze_batch.py --detour-spec` file "
                         "for every land whose JOINT arm closed, so the "
                         "measurement and the transaction cannot drift apart")
    ap.add_argument("--guard-out", type=Path,
                    help="write the `--guard` file that goes WITH --plan-out: "
                         "the reservation is the laid stitch's own path, one "
                         "tube per layer it occupies plus the barrel on the "
                         "whole stack, and NOT a disc.  The plan's `reserve` "
                         "list is therefore empty and each detour states its "
                         "own `max_mm`")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    # D-674.  `--split-priced` writes a candidate board per priced round.  A
    # stated directory KEEPS that evidence -- which is what a decision needs --
    # and an unstated one is a temporary directory removed at exit, so the
    # default asks the reader to store nothing.
    # `NET:REF.NUM`, grouped by net so one `Field` is built per net.
    bond_req = {}
    for item in a.split_bond_pad:
        if ":" not in item:
            raise SystemExit("--split-bond-pad wants NET:REF.NUM, got %r"
                             % item)
        bnet, bref = item.rsplit(":", 1)
        bond_req.setdefault(bnet, []).append(bref)
    bond_req = tuple((n, tuple(v)) for n, v in sorted(bond_req.items()))
    if bond_req and not a.split_priced:
        raise SystemExit("--split-bond-pad needs --split-priced: it changes "
                         "the board the SPLIT is priced on and nothing else")

    split_tmp = None
    if a.split_priced and a.split_price_work is None:
        split_tmp = tempfile.mkdtemp(prefix="aqroot-split-price-")
        split_work = Path(split_tmp)
    else:
        split_work = a.split_price_work

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN, BOARD_VIA_DIA_MIN,
                                  BOARD_HOLE_MIN, BOARD_TRACK_MIN)

    ev = json.loads(a.evidence.read_text(encoding="utf-8"))
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    if ev.get("board_sha256") != board_sha:
        print("REFUSED: the evidence was taken on board %s and this board is "
              "%s" % (ev.get("board_sha256", "?")[:16], board_sha[:16]),
              file=sys.stderr)
        return 2

    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    neck = mz.neck_rule(qb)
    reserved = reserved_inner_planes(qb.b)
    want = set(a.land)

    lands = []
    for rec in ev["nets"]:
        for l in rec["lands"]:
            if "cuts" not in l or not l["verdict"].startswith("SEGMENT"):
                continue
            key = "%s:%s" % (rec["net"], l["land"][0])
            if want and key not in want:
                continue
            lands.append((rec, l, key))

    out = []
    for (nrec, l, key) in lands:
        net = nrec["net"]
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        over = DRU_CLASS.get(c["netclass"], {})
        w_floor = max(BOARD_TRACK_MIN, over.get("width", 0))
        d_floor = max(BOARD_HOLE_MIN, over.get("drill", 0))
        v_floor = max(BOARD_VIA_DIA_MIN, d_floor + 2 * ANNULAR_MIN)
        if ev["rung"] == "floor":
            w, clr, vd, vdr = w_floor, c["clr"], v_floor, d_floor
        else:
            w, clr, vd, vdr = (min(w_floor, RELIEF_WIDTH), RELIEF_CLR,
                               RELIEF_VIA_DIA, RELIEF_VIA_DRILL)

        radius = int(round(l["cut_radius_mm"] * 1e6))
        site_mm = l["stitch"]["via_xy"]
        stitch_ref = l["stitch"]["pad"]

        # The cut, resolved against the live obstacle model ONCE.  Both arms
        # hold out exactly these objects, so they cannot differ by which
        # copper came off the board.
        held, by_net, missing = [], {}, []
        for cr in l["cuts"]:
            hits = find_seg(qb, cr)
            if len(hits) != 1:
                missing.append(dict(cut=cr, matched=len(hits)))
                continue
            held.append((cr["layer"], hits[0]))
            by_net.setdefault(cr["net"], []).append(
                (cr["layer"], hits[0], cr))
        rep = dict(land=key, net=net, netclass=c["netclass"],
                   pads=l["land"], verdict_measured=l["verdict"],
                   cut_radius_mm=l["cut_radius_mm"], site_mm=site_mm,
                   stitch_pad=stitch_ref, cut_tracks=len(l["cuts"]),
                   cut_nets=sorted(by_net), unmatched=missing,
                   ends_inside_reserve=[])
        for cr in l["cuts"]:
            for pt in (cr["a_mm"], cr["b_mm"]):
                d = math.hypot(pt[0] - site_mm[0], pt[1] - site_mm[1])
                rep["ends_inside_reserve"].append(
                    dict(net=cr["net"], xy_mm=pt, d_mm=round(d, 4),
                         inside=bool(d < l["cut_radius_mm"])))
        if missing:
            rep["error"] = "a cut record did not resolve to exactly one track"
            out.append(rep)
            continue

        # The body certificate and the plane `Field` are taken on the UNCUT
        # board, exactly as `screen_segment_evict` takes them: a `Held`
        # context touches only the obstacle model and the real refill can only
        # let this net's pour grow, so a site inside the body today is inside
        # it afterwards.
        field = mz.Field(qb, net, w, c["clr_pad"], clr, vd, vdr, G=a.grid,
                         layers=layers, neck=neck,
                         guard=guard_for(spec, net) if spec else None)
        arms_wanted = (("bare", "disc", "stitch", "joint") if a.arm == "all"
                       else (a.arm,))
        land_ok, land_info = (None, None)
        if "stitch" in arms_wanted or "joint" in arms_wanted:
            land_ok, land_info = mz.body_landing(qb, net, field)
        rep["body_landing"] = land_info

        pad = None
        for isl in mz.net_islands(qb, net):
            for p in isl:
                if p["ref"] == stitch_ref:
                    pad = p
        if pad is None:
            rep["error"] = "the stitch pad %s is not a physical pad of %s" \
                           % (stitch_ref, net)
            out.append(rep)
            continue

        arms = {}
        for arm in arms_wanted:
            if arm == "joint":
                arms[arm] = joint_search(
                    qb, field, held, by_net, pad, land_ok, ev["max_mm"],
                    a.grid, reserved, spec, a.relay_own_layer, vd, net, mz,
                    radius, tries=a.joint_tries,
                    knock_mm=a.joint_knockout_mm,
                    slack_mm=a.relay_slack_mm,
                    priced_split=(None if not a.split_priced else
                                  (a.board, split_work,
                                   "%s-%s" % (net.strip("/").replace("/", "_"),
                                              stitch_ref))),
                    bond_req=bond_req,
                    bond_ctx=dict(net_contract=net_contract,
                                  permitted_layers=permitted_layers,
                                  reserved=reserved, neck=neck))
                continue
            with Held(qb, field, held):
                m = qb.mark()
                st, guard, note = None, None, None
                if arm == "bare":
                    # THE POSITIVE CONTROL, AND IT IS THE ONE THAT DECIDES
                    # WHAT THE OTHER TWO MEAN.  Nothing is reserved and
                    # nothing is laid: the only difference between this board
                    # and the authoritative one is that this track is not on
                    # it.  A track that will not go back HERE was never
                    # refused by the stitch, by the pocket or by the disc --
                    # it is refused by the lattice, which cannot reproduce
                    # legacy copper laid at a tolerance finer than its own
                    # 0.100 mm grid and 0.75-cell guard band.  Five decisions
                    # have read that refusal as congestion.
                    pass
                elif arm == "disc":
                    # The reservation `relay_price` uses: a stand-in for copper
                    # that has not been laid.
                    guard = disc_guard([int(round(v * 1e6)) for v in site_mm],
                                       radius, [net])
                else:
                    # The copper itself.
                    st = mz.stitch_pad(qb, field, pad, max_mm=ev["max_mm"],
                                       escape_limit=12, land_ok=land_ok)
                    if not st.get("ok"):
                        note = "the stitch did not lay: %s" % st.get("reason")
                ok_all, tracks = (False, []) if note else relay_nets(
                    qb, a.grid, reserved, by_net, spec, guard, radius,
                    a.relay_own_layer, slack_mm=a.relay_slack_mm)
                # D-605's scissors: a through barrel is a slot in EVERY
                # foreign pour it passes, and the pour it damages is never
                # the one being stitched.  Every barrel this transaction
                # plants -- the stitch's and any the relay needed -- is put
                # through the same predictor `join_islands` uses.
                sev = None
                if arm == "stitch" and st and st.get("ok"):
                    sites = [(int(st["via_xy_nm"][0]),
                              int(st["via_xy_nm"][1]))]
                    for t in tracks:
                        for (vx, vy) in (t.get("via_xy") or []):
                            sites.append((int(round(vx * 1e6)),
                                          int(round(vy * 1e6))))
                    sev = [dict(pour=n, layer=lname, mm2=round(area, 2),
                                why=why)
                           for n in mz._foreign_pours(qb, net)
                           for (lname, _idx, _poly, area, why)
                           in mz._antipad_severs(qb, n, sites, vd)]
                arms[arm] = dict(
                    stitch=(dict(ok=st.get("ok"), reason=st.get("reason"),
                                 mm=st.get("mm"), layer=st.get("layer"),
                                 via_xy=list(st.get("via_xy") or []),
                                 why=str(st.get("why"))[:180]
                                 if st.get("why") else None)
                            if st is not None else None),
                    reservation=("nothing at all -- the positive control"
                                 if arm == "bare" else
                                 "all-layer keep-out disc r=%.3f mm at the "
                                 "barrel site" % (radius / 1e6)
                                 if arm == "disc" else
                                 "the laid stitch copper itself"),
                    note=note, all_relaid=bool(ok_all and not note),
                    antipad_severs=sev, tracks=tracks)
                qb.revert(m)
        rep["cut_records"] = list(l["cuts"])
        # THE RUNG THE MEASUREMENT WAS TAKEN AT, CARRIED IN THE REPORT SO THE
        # PLAN CAN CARRY IT TO THE WRITER.  D-638's gate run failed on exactly
        # this gap: the screen measured `+3V3 R39.1` at the `floor` rung
        # (0.400 mm track, 0.65/0.40 barrel) and the writer, given no rung, was
        # handed the NETCLASS by `net_contract` (0.600 / 0.800) and reported
        # `NO_BODY_VIA_SITE: no legal 0.80 mm barrel`, `stitched: 0`.
        rep["stitch_width_nm"] = int(w)
        rep["stitch_via_dia_nm"] = int(vd)
        rep["stitch_via_drill_nm"] = int(vdr)
        rep["reserve_clr_nm"] = int(max(
            [clr] + [net_contract(qb.b, n)["clr"] for n in by_net]))
        rep["arms"] = arms
        if a.arm == "all":
            Z = arms["bare"]["all_relaid"]
            A = arms["disc"]["all_relaid"]
            B = arms["stitch"]["all_relaid"]
            C = arms["joint"]["all_relaid"]
            sev = (arms["joint"].get("antipad_severs")
                   or arms["joint"].get("pour_severs")
                   or arms["stitch"].get("antipad_severs"))
            rep["verdict"] = ("TRANSACTION_CLOSES" if ((B or C) and not sev)
                              else "POUR_SEVERED" if ((B or C) and sev)
                              else "LATTICE_WALL" if not Z
                              else "JOINT_WALL")
            rep["moved_by_reservation"] = bool(B and not A)
            rep["moved_by_joint_search"] = bool(C and not B)
            # PER TRACK, because a land can be two relays and they can fail
            # for two different reasons -- `GND C37.2` is exactly that.
            per = {}
            for arm in ("bare", "disc", "stitch", "joint"):
                for t in arms[arm]["tracks"]:
                    per.setdefault(t["net"], {})[arm] = dict(
                        ok=t["ok"], reason=t.get("reason"), mm=t.get("mm"))
            rep["per_track"] = per
            rep["lattice_refuses"] = sorted(
                n for n, v in per.items() if not v.get("bare", {})["ok"])
        out.append(rep)
        print("  %-24s bare %-4s  disc %-4s  stitch %-4s  joint %-4s  %s"
              % (key[:24],
                 "OK" if arms.get("bare", {}).get("all_relaid") else "FAIL",
                 "OK" if arms.get("disc", {}).get("all_relaid") else "FAIL",
                 "OK" if arms.get("stitch", {}).get("all_relaid") else "FAIL",
                 "OK" if arms.get("joint", {}).get("all_relaid") else "FAIL",
                 rep.get("verdict", "")),
              file=sys.stderr, flush=True)

    # THE PLAN IS THE MEASUREMENT, WRITTEN IN THE WRITER'S OWN GRAMMAR.  What
    # `screen_segment_evict.py --plan-out` emits is a RESERVE DISC, and this
    # screen's whole finding is that the disc is what refuses the relay.  So
    # the plan written here carries no disc at all: the reservation is the
    # stitch's own laid copper, expressed as the per-layer tubes
    # `pour_bond_guard.py` already defines and `route_maze_batch.py --guard`
    # already consumes, and the detour states the budget the joint search
    # measured it against.
    if a.plan_out or a.guard_out:
        plan = dict(schema=1, reserve=[], detours=[],
                    note="emitted by screen_relay_transaction.py from board "
                         "%s; the reservation is NOT a disc -- see the guard "
                         "file that goes with this plan" % board_sha[:16])
        # THE RUNG TRAVELS WITH THE PLAN.  D-639.  A plan that names the
        # geometry but not the WIDTH it was measured at is half a plan, and the
        # missing half cost D-638 a full-authority gate run: `route_maze_batch`
        # took the netclass, asked for an 0.80 mm barrel where the screen had
        # proved an 0.65 mm one, and stitched nothing.  `--stitch-width` and
        # `--stitch-via` already exist and already clamp UP to the `.kicad_dru`
        # floors, so this states them and can license nothing.
        rung = dict(name=ev["rung"], per_net={}, argv=None, why=None)
        guards = []
        # D-675: A PLAN PRICED WITH A `--bond-pad` CARRIES IT.  The whole point
        # of this emitter is that the measurement and the transaction cannot
        # drift; a split priced on a board that has a bond barrel on it and a
        # writer run that plants none are two different transactions, and the
        # second one is the one `PP2` would refuse.
        bond_plan = []
        for rep in out:
            j = (rep.get("arms") or {}).get("joint") or {}
            if not j.get("all_relaid") or not j.get("stitch_geometry"):
                continue
            pnet = rep["net"]
            rung["per_net"][pnet] = dict(
                stitch_width_nm=int(rep["stitch_width_nm"]),
                stitch_via_dia_nm=int(rep["stitch_via_dia_nm"]),
                stitch_via_drill_nm=int(rep["stitch_via_drill_nm"]),
                netclass=rep["netclass"])
            clr = int(rep["reserve_clr_nm"])
            geom = j["stitch_geometry"]
            for t in geom["tracks"]:
                keep = t["width_nm"] // 2 + clr
                pts, step = [], max(1, keep)
                ax, ay = t["a_nm"]; bx, by = t["b_nm"]
                L = math.hypot(bx - ax, by - ay)
                n = max(1, int(math.ceil(L / float(step))))
                for k in range(n + 1):
                    u = k / float(n)
                    pts.append([int(round(ax + u * (bx - ax))),
                                int(round(ay + u * (by - ay)))])
                guards.append(dict(ok=True, net=pnet, exempt=[],
                                   lkey=t["lkey"], keepout_radius=int(keep),
                                   points=pts,
                                   tube="D638_STITCH_RUN_%s" % rep["land"]))
            for v in geom["vias"]:
                keep = int(rep["stitch_via_dia_nm"]) // 2 + clr
                for lk in ("F", "I1", "I2", "I3", "I4", "B"):
                    guards.append(dict(ok=True, net=pnet, exempt=[], lkey=lk,
                                       keepout_radius=int(keep),
                                       points=[v["xy_nm"]],
                                       tube="D638_STITCH_BARREL_%s"
                                            % rep["land"]))
            for t in j["tracks"]:
                cs = [c for c in rep["cut_records"] if c["net"] == t["net"]]
                entry = dict(net=t["net"], max_mm=t["max_mm"])
                parts = [dict(layer=LAYER_NAME[c["layer"]], a_mm=c["a_mm"],
                              b_mm=c["b_mm"], width_mm=c["width_mm"])
                         for c in cs]
                entry.update(parts[0] if len(parts) == 1
                             else dict(tracks=parts))
                plan["detours"].append(entry)
            for b in (j.get("split_bonds") or ()):
                for ref in b.get("requested", ()):
                    bond_plan.append(dict(net=b["net"], pad=ref))
        # ONE RUNG OR NONE.  `--stitch-width` is a RUN-WIDE lever, so a plan
        # that closed two lands of two different classes at two different rungs
        # cannot state one; it says so instead of picking, and the writer then
        # refuses rather than guessing.
        rungs = {(v["stitch_width_nm"], v["stitch_via_dia_nm"],
                  v["stitch_via_drill_nm"]) for v in rung["per_net"].values()}
        if len(rungs) == 1:
            w_nm, vd_nm, vdr_nm = rungs.pop()
            rung.update(stitch_width_nm=w_nm, stitch_via_dia_nm=vd_nm,
                        stitch_via_drill_nm=vdr_nm,
                        argv=["--stitch-width", str(w_nm),
                              "--stitch-via", "%d:%d" % (vd_nm, vdr_nm)])
        elif len(rungs) > 1:
            rung["why"] = ("this plan closes lands measured at %d DIFFERENT "
                           "rungs; --stitch-width is run-wide, so emit one "
                           "plan per rung" % len(rungs))
        else:
            rung["why"] = "no land closed, so no rung was measured"
        plan["rung"] = rung
        plan["bond_pads"] = dict(
            pads=[b["pad"] for b in bond_plan],
            detail=bond_plan,
            argv=[x for b in bond_plan for x in ("--bond-pad", b["pad"])],
            why=("this plan's split was PRICED with these bonds planted by "
                 "maze3d.bond_pads; a writer run that omits them is running a "
                 "DIFFERENT transaction and PP2 was not measured on it"
                 if bond_plan else
                 "no bond was planted; the split, if any, was priced as-is"))
        if a.plan_out:
            a.plan_out.write_text(
                json.dumps(plan, indent=2, sort_keys=True) + "\n",
                encoding="utf-8")
        if a.guard_out:
            a.guard_out.write_text(
                json.dumps(dict(schema=1, guards=guards,
                                note="the reservation a joint rip-up-and-relay "
                                     "owes: the stitch's own path, per layer, "
                                     "plus its barrel on the whole stack"),
                           indent=2, sort_keys=True) + "\n",
                encoding="utf-8")

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        authoritative_unchanged=(board_sha == after),
        evidence=str(a.evidence),
        evidence_sha256=hashlib.sha256(
            a.evidence.read_bytes()).hexdigest(),
        grid=a.grid, arm=a.arm, rung=ev["rung"], max_mm=ev["max_mm"],
        relay_own_layer=bool(a.relay_own_layer),
        relay_slack_mm=a.relay_slack_mm or None,
        split_priced=bool(a.split_priced),
        split_price_work=(str(split_work) if a.split_priced else None),
        question=("does a cut that opens a plane land go back when the "
                  "reservation is the STITCH THAT WILL BE THERE instead of an "
                  "all-layer keep-out disc big enough to swallow the relay's "
                  "own two terminals"),
        method=("read-only; the named tracks are held out of the obstacle "
                "model whole, the real maze3d.stitch_pad is laid with the same "
                "body certificate the measurement used, and each cut net is "
                "put back by maze3d.route_points between its own chain ends at "
                "the same budget -- every object proved by verify_laid, the "
                "barrel put through _antipad_severs, every trial reverted"),
        lands=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if split_tmp is not None:
        shutil.rmtree(split_tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
