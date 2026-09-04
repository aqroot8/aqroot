#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- gated batch driver for the whole-board all-layer maze router.

`maze3d.route_net` is a PROPOSER.  This module is the AUTHORITY: it never lets
proposed copper touch `hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb`
unless every gate below passes on a scratch copy.

    1. the authoritative board is byte-identical before and after the run
       (and again immediately before a `--promote` write);
    2. every net is routed at its OWN netclass width / via / clearance, raised
       where the project DRU imposes a stricter routed minimum, and restricted
       to the layers the DRU allows that netclass;
    3. real KiCad `--refill-zones --save-board --severity-all
       --schematic-parity` DRC on the scratch board reports NO violation
       outside the three inherited classes, and the inherited class counts do
       not grow;
    4. the fitted-pad routing ledger shows the whole board's retained open
       edges strictly DECREASE and no other net regress -- measured after the
       optional `--repair-planes` stitch and its own second refill and DRC, so
       a pour a signal track split is given the barrel that re-bonds it before
       the verdict, and is still a refusal if that barrel does not exist;
    5. every pre-existing track/via signature still exists, and every ADDED
       object is on a net that SUCCEEDED -- copper is added, never moved or
       removed, and every failed net's revert is proven rather than assumed;
    6. with `--plane`, the candidate's zone inventory differs from the
       authority's by exactly ONE added zone, on the requested net and layer,
       and no existing zone's net, layer, outline or fill parameters changed.

Failing any gate the run is characterization: it prints its evidence, writes no
candidate, and leaves the authoritative board untouched.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from screen_inner_plane import insert_zone, zone_sexpr

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
LEDGER = ROOT / "hardware/demo/manufacturing/routing_ledger.py"

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

# Inherited DRC classes: present on the accepted board before any Demo routing
# and not attributable to it.  Their counts are pinned, not merely ignored.
INHERITED = {"lib_footprint_issues": 199, "hole_clearance": 5,
             "solder_mask_bridge": 1}

# Per-netclass routing contract taken from `aqroot-Beta-v2.kicad_dru`, because a
# netclass width/clearance is a DEFAULT and several DRU rules are stricter or
# forbid layers outright.  `layers=None` means "every routable layer".
#   width    -- max(netclass track width, DRU track_width min)
#   clr      -- max(netclass clearance,  DRU routed clearance min)
#   layers   -- routable layers the DRU permits for the class
#   drill    -- DRU `hole_size` min for a via on the class ("POWER-class vias
#               use the 0.40 mm drill"); a request may never go under it
DRU_CLASS = {
    "Default":      dict(clr=200000, layers=None),
    "I2C":          dict(clr=200000, layers=None),
    "I2S":          dict(clr=200000, layers=None),
    "NFC_RX":       dict(clr=200000, layers=None),
    "NFC_OSC":      dict(clr=200000, layers=None),
    "GND":          dict(clr=200000, layers=None),
    "SPK_OUT":      dict(width=250000, clr=200000, layers=("F", "B")),
    "LED_BOOST":    dict(clr=300000, layers=None),
    "SWITCH_NODE":  dict(width=400000, clr=300000, layers=("F", "B")),
    "SYS_MAIN":     dict(width=500000, clr=250000, drill=400000, layers=None),
    "ACC_3V3":      dict(width=350000, clr=250000, drill=400000, layers=None),
    "ACC_5V":       dict(width=400000, clr=250000, drill=400000, layers=None),
    "VBUS_CHG":     dict(width=350000, clr=250000, drill=400000, layers=None),
    "NFC_5V_PA":    dict(width=350000, clr=250000, drill=400000, layers=None),
    "P3V3":         dict(width=400000, clr=200000, drill=400000, layers=None),
    "BAT_MAIN":     dict(width=600000, clr=300000, drill=400000, layers=None),
    "NFC_RF":       dict(clr=200000, layers=None),
    "USB_D":        dict(clr=200000, layers=("F", "B")),
}

# `(rule "Via annular ring floor") (constraint annular_width (min 0.125mm))`.
ANNULAR_MIN = 125000

# --------------------------------------------------------------------------- #
# INNER PLANES ARE NOT SIGNAL LAYERS ANY MORE
# --------------------------------------------------------------------------- #
# `qrouter.ROUTABLE` calls the six-layer stack `F, B, In2, In3` -- In1 and In4
# are the solid GND references and were never routable.  That was the truth of
# this board until D-580 poured `+3V3` on `In3.Cu`.  It is not the truth now.
#
# The first `--partial` run measured the consequence rather than arguing it: a
# nine-island `/I2C_SCL_INT` proposal closed five edges and took FOUR of its
# five joins across `In3`, and the gate refused the whole run because `+3V3`
# REGRESSED -- foreign copper on a plane layer is a SLOT through that plane,
# and a slot long enough separates pads the pour used to bond.  D-580 predicted
# exactly this refusal in writing; this is it happening.
#
# The connectivity regression is only the visible half.  A track laid through a
# power plane also breaks the return path of every signal that crosses the slot
# and lengthens the PDN loop the plane exists to shorten, and neither of those
# shows up in a ledger at all.  So a layer that carries an INNER pour is
# reserved to the net that owns it, and the maze routes foreign nets on the
# three layers this board actually has left: `F`, `B` and `In2`.
#
# OUTER pours are deliberately NOT reserved.  The `+3V3` pour on `F.Cu` and the
# `GND` pour on `B.Cu` are fill-in copper on layers whose job is signal routing
# -- they flow around whatever is routed and were poured knowing it.  Reserving
# them would leave this board one signal layer, which is not a rule, it is a
# shutdown.  The no-net-regressed gate clause still governs them, so an outer
# pour that a run actually severs is still refused, and refused on the same
# evidence that produced this rule.
INNER = {"In1.Cu": "I1", "In2.Cu": "I2", "In3.Cu": "I3", "In4.Cu": "I4"}


def reserved_inner_planes(board):
    """Short names of the inner layers a filled pour owns, mapped to its nets.

    Read from the BOARD, not transcribed: pour one more inner plane tomorrow
    and the router reserves it on the next run with no edit here.
    """
    out = {}
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsFilled():
            continue
        for layer in z.GetLayerSet().Seq():
            name = board.GetLayerName(layer)
            if name in INNER:
                out.setdefault(INNER[name], set()).add(z.GetNetname())
    return out


def permitted_layers(routable, contract_layers, reserved, net):
    """The layers this net may lay copper on, after plane reservation.

    A net that OWNS a plane still routes on it -- its own copper is not a slot
    through the plane, it is more of the same plane -- so the reservation is
    per (layer, net) and never a blanket layer ban.
    """
    allowed = tuple(contract_layers or routable)
    keep = tuple(L for L in allowed
                 if net in reserved.get(L, ()) or L not in reserved)
    return keep or allowed


# Nets excluded from generic maze routing.  Each is a documented physics or
# governance constraint the maze proposer does not model, NOT a difficulty
# judgement: it must keep being routed by its own purpose-built harness.
EXCLUDE = {
    "/USB_D_MCU_P", "/USB_D_MCU_N",     # matched diff pair (gap/uncoupled DRU)
    "/01_POWER_TREE/USB_D_CONN_P", "/01_POWER_TREE/USB_D_CONN_N",
    "/04_SPI_B_RADIOS_NFC/NFC_RFI1",    # NFC receive arms: length/symmetry
    "/04_SPI_B_RADIOS_NFC/NFC_RFI2",
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def net_contract(board, net):
    """The width / clearance / via / layer contract for ONE net."""
    info = board.FindNet(net)
    if info is None:
        raise SystemExit("net %r is not on the board" % net)
    cls = info.GetNetClassName()
    nc = info.GetNetClassSlow()
    over = DRU_CLASS.get(cls, {})
    return dict(
        net=net, netclass=cls,
        width=max(nc.GetTrackWidth(), over.get("width", 0)),
        clr=max(nc.GetClearance(), over.get("clr", 0)),
        via_dia=nc.GetViaDiameter(), via_drill=nc.GetViaDrill(),
        layers=over.get("layers"),
        known_class=cls in DRU_CLASS,
    )


# --------------------------------------------------------------------------- #
# child: propose copper on a scratch board
# --------------------------------------------------------------------------- #
def propose(path, nets, grid, via_cost_mm, stitch_width=0, stitch_via=None,
            join_residual=False, join_max_mm=0.0, neck=False,
            neck_max_mm=0.0, partial=False, attempt_cap=0,
            split_islands=False):
    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz

    ref = pcbnew.LoadBoard(str(path))
    contracts = {n: net_contract(ref, n) for n in nets}
    reserved = reserved_inner_planes(ref)
    del ref

    qb = qr.QBoard(str(path))
    ir.inject_existing_via_obstacles(qb)
    for n, c in contracts.items():
        c["layers"] = permitted_layers(qb.routable, c["layers"], reserved, n)
        c["reserved_inner_planes"] = {k: sorted(v) for k, v in reserved.items()}
    # The pad-escape necking allowance is read from the board's own .kicad_dru,
    # so the router cannot permit a neck the DRC would refuse, nor refuse one
    # the board's rules were written to allow.  None => the router behaves
    # exactly as it did before this flag existed.
    neck_rule = mz.neck_rule(qb, neck_max_mm or mz.NECK_MAX_MM) if neck else None
    results = []
    for net in nets:
        c = contracts[net]
        if not c["known_class"]:
            results.append(dict(net=net, ok=False, reason="UNKNOWN_NETCLASS",
                                netclass=c["netclass"]))
            continue
        # A plane STITCH stub is a few tenths of a millimetre of copper from a
        # pad to a barrel directly under it, so it is governed by the .kicad_dru
        # class floor rather than by the netclass DEFAULT width, which is sized
        # for a cross-board rail run.  The override can only ever RAISE the
        # floor: it is clamped to the DRU minimum for the class and the real
        # `track_width` DRC check re-proves every emitted segment regardless.
        if stitch_width:
            c["width"] = max(stitch_width,
                             DRU_CLASS.get(c["netclass"], {}).get("width", 0))
        # Same discipline for the barrel.  The netclass via is sized for a rail
        # trunk; a stitch barrel owes only the .kicad_dru floors -- the
        # POWER-class 0.40 mm drill and the 0.125 mm annular ring -- and the
        # request is clamped UP to both, so it can never ask for a via KiCad's
        # own `hole_size` / `annular_width` checks would refuse.
        if stitch_via:
            drill = max(stitch_via[1],
                        DRU_CLASS.get(c["netclass"], {}).get("drill", 0))
            c["via_drill"] = drill
            c["via_dia"] = max(stitch_via[0], drill + 2 * ANNULAR_MIN)
        t0 = time.time()
        field = mz.Field(qb, net, c["width"], c["clr"], c["clr"],
                         c["via_dia"], c["via_drill"], G=grid,
                         layers=c["layers"], neck=neck_rule)
        # A net that owns a filled pour is completed by dropping each island
        # onto that pour, not by a pad-to-pad MST across the signal layers.
        if mz.has_plane(qb, net):
            r = mz.stitch_net(qb, net, width=c["width"], clr_pad=c["clr"],
                              clr_trk=c["clr"], via_dia=c["via_dia"],
                              via_drill=c["via_drill"], G=grid, field=field,
                              split_islands=split_islands)
            r["mode"] = "stitch-split" if split_islands else "stitch"
            # The stitch is LOCAL by construction -- one escape and one barrel
            # inside an 8 mm window.  An island it reports as unreachable may
            # still be a short ordinary run from copper that IS on the plane, so
            # the residual pass hands exactly those islands to the same
            # whole-board maze the plane-less nets use.  It runs AFTER the
            # stitch, never instead of it: a barrel straight down into the pour
            # is always the cheaper answer and keeps its priority.
            if join_residual:
                j = mz.join_residual_islands(qb, net, field,
                                             via_cost_mm=via_cost_mm,
                                             max_mm=join_max_mm)
                r["residual_join"] = j
                r["mode"] = "stitch+join"
                r["ok"] = bool(r.get("ok")) or bool(j.get("joined"))
        else:
            r = mz.route_net(qb, net, width=c["width"], clr_pad=c["clr"],
                             clr_trk=c["clr"], via_dia=c["via_dia"],
                             via_drill=c["via_drill"], G=grid,
                             via_cost_mm=via_cost_mm, field=field,
                             partial=partial, attempt_cap=attempt_cap,
                             join_max_mm=join_max_mm)
            r["mode"] = "maze+partial" if partial else "maze"
        r["seconds"] = round(time.time() - t0, 1)
        print("  %-44s %-6s %s %.0fs" % (
            net, r["mode"], "ok" if r.get("ok") else r.get("reason", "FAIL"),
            time.time() - t0), file=sys.stderr, flush=True)
        r["contract"] = {k: c[k] for k in
                         ("netclass", "width", "clr", "via_dia", "via_drill",
                          "layers", "reserved_inner_planes")}
        results.append(r)
    qb.save(str(path))
    print(json.dumps(dict(results=results), default=str))


# --------------------------------------------------------------------------- #
# authority: gate a scratch candidate
# --------------------------------------------------------------------------- #
def ledger(board, out):
    subprocess.run([sys.executable, str(LEDGER), "--board", str(board),
                    str(out)], check=True, capture_output=True, text=True)
    return json.loads(Path(out).read_text())


def zones(path):
    """A comparable signature for every non-rule-area zone on a board."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        outline = z.Outline().Outline(0)
        out.append((
            z.GetNetname(),
            tuple(board.GetLayerName(l) for l in z.GetLayerSet().Seq()),
            z.GetZoneName(),
            z.GetMinThickness(),
            z.GetLocalClearance(),
            int(z.GetIslandRemovalMode()),
            tuple((outline.CPoint(i).x, outline.CPoint(i).y)
                  for i in range(outline.PointCount())),
        ))
    return sorted(out)


def copper(path):
    import pcbnew
    import incremental_router as ir
    return ir.copper_sigs(pcbnew.LoadBoard(str(path)))


def fill_only(scratch, out):
    """Ask the real KiCad engine to FILL the zones and save the board."""
    return subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "-o", str(out), str(scratch),
    ], text=True, capture_output=True).returncode


def full_drc(scratch, out):
    """The authoritative DRC step: refill the zones, save, report everything.

    Extracted so the gate can run it AGAIN after a plane repair.  Refilling is
    the whole point: the pours the proposal perturbed are re-poured by the real
    KiCad engine, so what the ledger measures afterwards is the copper a
    fabricator would actually get, not the copper the router imagined.
    """
    return subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(out), str(scratch),
    ], text=True, capture_output=True)


def plane_nets(path):
    """Nets that own at least one filled, non-rule-area pour on this board."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    return sorted({z.GetNetname() for z in board.Zones()
                   if not z.GetIsRuleArea() and z.IsFilled()
                   and z.GetNetname()})


# --------------------------------------------------------------------------- #
# A POUR THAT A TRACK SPLIT IS NOT A REGRESSION.  IT IS AN UNFINISHED STITCH.
# --------------------------------------------------------------------------- #
# Gate clause 4 refuses any run in which ANY net's open-edge count grows, and it
# is right to: copper that disconnects something is not progress.  But on THIS
# board that clause had started refusing runs for a reason that is not a
# disconnection at all.
#
# After D-582 and D-583 the two outer layers carry pours -- `+3V3` on `F.Cu`,
# `GND` on `B.Cu` -- and those pours bond dozens of pads with no track and no
# via.  A foreign signal track laid across such a layer is a SLOT through the
# pour: KiCad re-pours around it, the pour splits into two islands, and every
# pad that was bonded across the cut goes open.  So a `--partial` run on
# `/I2C_SCL_INT` closed FIVE real edges, lost one to `+3V3` and one to `GND`,
# came out four edges AHEAD on the whole board -- and was refused.
#
# Refusing it is the wrong answer twice over.  It throws away five routed
# connections to avoid two that a via can restore, and it makes the outer pours
# behave like reserved planes, which D-581's rule text explicitly declined to do
# because it would leave this board one signal layer.
#
# The right answer is the one the board has been using since D-579: a pad that
# sits on its own pour island does not need a better search, it needs a BARREL
# down to the same net's copper on another layer.  `maze3d.stitch_net` is
# exactly that primitive, and after the refill the split is visible to it as an
# ordinary orphaned island -- indistinguishable from the two hundred a fresh
# pour leaves.
#
# So `--repair-planes` closes the loop inside ONE gate transaction:
#
#     propose signal copper -> real refill -> measure -> if a POUR-OWNING net
#     regressed, stitch exactly those nets on the refilled board -> real refill
#     again -> measure again, and judge the run on THAT.
#
# Three things keep this a repair and not a loophole.
#
#   * ONLY POUR-OWNING NETS ARE REPAIRED, and only ones that actually
#     regressed.  A plane-less net that a run disconnects is still a hard
#     refusal; there is no via that fixes it and no pretending otherwise.
#   * THE REPAIR IS ORDINARY GATED COPPER.  It goes through the same
#     `propose` child, the same DRU contract, the same analytic proofs, and it
#     is re-proved by a SECOND full `--severity-all --schematic-parity` DRC on
#     the refilled board.  Nothing is measured on a board that was not filled.
#   * THE VERDICT IS UNCHANGED AND UNWEAKENED.  Clause 4 still demands that no
#     net regress and that the whole board improve -- it is simply asked AFTER
#     the repair rather than in the middle of it.  A split the stitch cannot
#     close is still a regression and the run is still refused.
#
# `--repair-planes` is OFF by default, so every existing harness and every
# accepted result reproduces byte-identically without it.


def gate(nets, grid, via_cost_mm, workdir, promote=False, candidate=None,
         plane=None, zone_clearance=0.25, stitch_width=0, stitch_via=None,
         join_residual=False, join_max_mm=0.0, neck=False, neck_max_mm=0.0,
         partial=False, attempt_cap=0, repair_planes=False,
         split_islands=False):
    before = sha256_file(BOARD)
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    scratch = work / BOARD.name
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(
            BOARD.with_suffix(suffix).read_bytes())

    base_ledger = ledger(BOARD, work / "ledger-before.json")

    # `--plane`: give a plane-less power net a pour, then let the ordinary
    # stitch primitive plant its islands on it.  The pour is added UNFILLED and
    # filled by the real KiCad engine; its first fill must keep every island
    # (a net that owns no copper yet has no connection for `remove` to spare),
    # and the mode is flipped back to `remove` after the stitch so the promoted
    # board carries no island that the stitch did not actually connect.
    plane_zone = None
    if plane:
        if len(nets) != 1:
            raise SystemExit("--plane routes exactly one net")
        plane_zone = dict(net=nets[0], layer=plane,
                          name="%s %s PLANE" % (plane.split(".")[0], nets[0]),
                          clearance=zone_clearance)
        insert_zone(scratch, zone_sexpr(nets[0], plane, plane_zone["name"],
                                        clearance=zone_clearance, islands=1))
        plane_zone["first_fill_exit"] = fill_only(scratch, work / "fill.json")

    def child(target_nets, use_search_levers=True):
        """Run the proposer on the scratch board for these nets."""
        cmd = [sys.executable, __file__, "--propose", str(scratch),
               "--grid", str(grid), "--via-cost", str(via_cost_mm)]
        if stitch_width:
            cmd += ["--stitch-width", str(stitch_width)]
        if stitch_via:
            cmd += ["--stitch-via", "%d:%d" % stitch_via]
        if neck:
            cmd += ["--neck", "--neck-max-mm", str(neck_max_mm)]
        # The repair is a STITCH and nothing else.  `--join-residual` and
        # `--partial` are search levers for the primary proposal; handing them
        # to the repair would let it lay whole-board tracks of its own, which is
        # a second routing run wearing a repair's name.
        #
        # `--split-islands` is ALWAYS the repair's question -- an island that
        # sits on its own severed piece of pour is exactly what the repair must
        # re-bond, and the default predicate hides it -- and is the CALLER's
        # choice for the primary proposal.  An earlier cut bound this to an
        # `else` on `if neck`, so the flag followed the necking lever instead of
        # the run: a `--neck` repair silently lost the predicate it exists for,
        # and every non-neck primary silently gained it.  Both halves are now
        # said explicitly.
        if split_islands or not use_search_levers:
            cmd += ["--split-islands"]
        if use_search_levers:
            if join_residual:
                cmd += ["--join-residual"]
            if partial:
                cmd += ["--partial", "--attempt-cap", str(attempt_cap)]
            if join_residual or partial:
                cmd += ["--join-max-mm", str(join_max_mm)]
        return json.loads(subprocess.run(
            cmd + list(target_nets), check=True, text=True,
            capture_output=True).stdout)["results"]

    routed = child(nets)

    if plane_zone:
        text = scratch.read_text(encoding="utf-8")
        marker = '(name "%s")' % plane_zone["name"]
        head, _, tail = text.partition(marker)
        tail = tail.replace("(island_removal_mode 1)",
                            "(island_removal_mode 0)", 1)
        scratch.write_text(head + marker + tail, encoding="utf-8")
        plane_zone["island_removal_restored"] = (
            "(island_removal_mode 1)" not in (head + marker + tail))

    drc_json = work / "drc.json"
    done = full_drc(scratch, drc_json)

    # ------------------------------------------------------------------ #
    # PLANE REPAIR -- see the doctrine above `gate`.
    # ------------------------------------------------------------------ #
    repair = None
    if repair_planes:
        mid = ledger(scratch, work / "ledger-mid.json")
        was = {r["net"]: r["open_edges"] for r in base_ledger["nets"]}
        now = {r["net"]: r["open_edges"] for r in mid["nets"]}
        owners = set(plane_nets(scratch))
        hurt = sorted(n for n, v in now.items()
                      if v > was.get(n, v) and n in owners)
        repair = dict(candidates=hurt,
                      pour_owning_nets=sorted(owners),
                      regressed_before_repair=sorted(
                          n for n, v in now.items() if v > was.get(n, v)),
                      retained_open_edges_before_repair=mid[
                          "connectivity"]["retained_open_edges"])
        if hurt:
            repair["routed"] = child(hurt, use_search_levers=False)
            drc_json = work / "drc-repaired.json"
            done = full_drc(scratch, drc_json)

    report = json.loads(drc_json.read_text())
    counts = {}
    for v in report.get("violations", []):
        counts[v.get("type", "unknown")] = counts.get(v.get("type"), 0) + 1
    attributable = [v for v in report.get("violations", [])
                    if v.get("type") not in INHERITED]
    inherited_ok = all(counts.get(k, 0) <= n for k, n in INHERITED.items())

    after_ledger = ledger(scratch, work / "ledger-after.json")
    before_open = {r["net"]: r["open_edges"] for r in base_ledger["nets"]}
    after_open = {r["net"]: r["open_edges"] for r in after_ledger["nets"]}
    regressed = sorted(n for n, v in after_open.items()
                       if v > before_open.get(n, v))
    closed = sorted(n for n in before_open
                    if after_open.get(n, 0) < before_open[n])
    edges_before = base_ledger["connectivity"]["retained_open_edges"]
    edges_after = after_ledger["connectivity"]["retained_open_edges"]

    zone_before, zone_after = zones(BOARD), zones(scratch)
    zone_added = [z for z in zone_after if z not in zone_before]
    zone_lost = [z for z in zone_before if z not in zone_after]
    zone_ok = (not zone_lost and len(zone_added) == (1 if plane else 0)
               and all(z[0] == nets[0] and z[1] == (plane,)
                       for z in zone_added))

    base_cu, cand_cu = copper(BOARD), copper(scratch)
    removed = sorted(str(k) for k in (base_cu - cand_cu))
    added_nets = sorted({k[1] for k in (cand_cu - base_cu)})
    # A net that fails is reverted atomically by `maze3d.route_net`, so a
    # partial batch is still promotable: the promotion set is exactly the nets
    # that succeeded.  Requiring every added object to be on a SUCCEEDED net is
    # strictly stronger than the old "requested net" test -- it proves the
    # revert of each failed net actually happened, rather than assuming it.
    # The repair lays copper too, so its successes join the promotion set --
    # otherwise clause 5 would call a stitch this gate itself asked for
    # "foreign".  Its FAILURES are not added to `failed`: a plane net the repair
    # could not fully re-bond is judged by clause 4 on the ledger, which is the
    # measurement that matters, not by whether the stitch primitive returned ok.
    repaired = [r for r in (repair or {}).get("routed", []) if r.get("ok")]
    ok_nets = sorted({r["net"] for r in routed if r.get("ok")}
                     | {r["net"] for r in repaired})
    failed = sorted(r["net"] for r in routed if not r.get("ok"))
    foreign = sorted(set(added_nets) - set(ok_nets))

    # A run must CHANGE the board, not merely survive the gate.  For a maze or
    # stitch run that means at least one net actually routed.  Under `--plane`
    # it does NOT: the pour IS the copper.  A pour that lands on pads the net
    # already reaches closes those edges with no track and no barrel at all,
    # and `edges_after < edges_before` above is the honest proof that it did.
    # Requiring a stitch as well would refuse a promotion whose whole value is
    # the plane -- which is exactly what a plane is for.
    changed = (bool(plane)
               or any(r.get("ok") and not r.get("already") for r in routed)
               or any(not r.get("already") for r in repaired))
    ok = (not attributable and inherited_ok and not regressed and not removed
          and not foreign and edges_after < edges_before and zone_ok
          and changed and before == sha256_file(BOARD))

    summary = dict(
        schema=1,
        authoritative_board_sha256=before,
        authoritative_unchanged=(before == sha256_file(BOARD)),
        requested_nets=list(nets),
        routed_nets=ok_nets,
        failed_nets=failed,
        routed=routed,
        drc_exit=done.returncode,
        drc_types=counts,
        inherited_within_baseline=inherited_ok,
        attributable_drc=attributable,
        connectivity=dict(
            retained_open_edges_before=edges_before,
            retained_open_edges_after=edges_after,
            open_retained_nets_before=base_ledger["connectivity"]["open_retained_nets"],
            open_retained_nets_after=after_ledger["connectivity"]["open_retained_nets"],
            nets_improved=closed, nets_regressed=regressed),
        plane=plane_zone,
        plane_repair=repair,
        preservation=dict(removed_objects=removed, added_object_nets=added_nets,
                          foreign_added_nets=foreign,
                          reverted_failures_clean=(not foreign),
                          zones_added=zone_added, zones_removed=zone_lost,
                          zone_inventory_ok=zone_ok),
        candidate_sha256=sha256_file(scratch),
        promotion_candidate=ok,
    )
    if candidate and ok:
        Path(candidate).write_bytes(scratch.read_bytes())
    if promote:
        if not ok:
            raise SystemExit("refuse promotion: gate failed")
        if before != sha256_file(BOARD):
            raise SystemExit("refuse promotion: authority changed under the run")
        BOARD.write_bytes(scratch.read_bytes())
        summary["promoted"] = True
        summary["promoted_sha256"] = sha256_file(BOARD)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*")
    ap.add_argument("--propose", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--plane", help="add a pour for the single named net on "
                                    "this layer, then stitch its islands")
    ap.add_argument("--zone-clearance", type=float, default=0.25)
    ap.add_argument("--stitch-width", type=int, default=0,
                    help="stub width in nm; clamped UP to the DRU class floor")
    ap.add_argument("--join-residual", action="store_true",
                    help="for a plane-served net, maze-join the islands the "
                         "local stitch reported as unreachable")
    ap.add_argument("--join-max-mm", type=float, default=0.0,
                    help="revert and report ANY single join longer than this "
                         "many millimetres of copper -- residual-island joins "
                         "and --partial joins alike; 0 disables the bound")
    ap.add_argument("--neck", action="store_true",
                    help="allow a pad with NO full-width escape to launch at "
                         "the .kicad_dru pad-escape necking minimum, for the "
                         "fine-pitch courtyards that rule names, bounded by "
                         "--neck-max-mm")
    ap.add_argument("--neck-max-mm", type=float, default=0.0,
                    help="bound on ONE necked stub in millimetres "
                         "(0 = the module default)")
    ap.add_argument("--partial", action="store_true",
                    help="complete each plane-less net BEST-EFFORT: union-find "
                         "Kruskal over every island pair, per-pair transaction, "
                         "instead of one all-or-nothing MST")
    ap.add_argument("--attempt-cap", type=int, default=0,
                    help="bound on join attempts per net under --partial "
                         "(0 = unbounded; the dead-terminal prune already "
                         "keeps the complete graph affordable)")
    ap.add_argument("--split-islands", action="store_true",
                    help="for a pour-owning net, also offer the stitch the "
                         "islands whose pads already touch a zone -- the shape "
                         "a SEVERED pour leaves; the plane repair always uses "
                         "this and needs no flag")
    ap.add_argument("--repair-planes", action="store_true",
                    help="after the refill, stitch any POUR-OWNING net whose "
                         "open edges grew, then refill and re-measure; a "
                         "signal track that slots a pour is repaired by a "
                         "barrel rather than refusing the whole run")
    ap.add_argument("--stitch-via", default=None,
                    help="DIA:DRILL in nm for stitch barrels; clamped UP to "
                         "the DRU hole-size and annular-ring floors")
    ap.add_argument("--work", default=None)
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    via = None
    if a.stitch_via:
        via = tuple(int(v) for v in a.stitch_via.split(":"))
    if a.propose:
        propose(a.propose, a.nets, a.grid, a.via_cost, a.stitch_width, via,
                a.join_residual, a.join_max_mm, a.neck, a.neck_max_mm,
                a.partial, a.attempt_cap, a.split_islands)
        return 0
    if not a.nets:
        ap.error("name at least one net")
    bad = sorted(set(a.nets) & EXCLUDE)
    if bad:
        ap.error("excluded from generic maze routing: %s" % ", ".join(bad))

    extra = dict(plane=a.plane, zone_clearance=a.zone_clearance,
                 stitch_width=a.stitch_width, stitch_via=via,
                 join_residual=a.join_residual, join_max_mm=a.join_max_mm,
                 neck=a.neck, neck_max_mm=a.neck_max_mm,
                 partial=a.partial, attempt_cap=a.attempt_cap,
                 repair_planes=a.repair_planes,
                 split_islands=a.split_islands)
    if a.work:
        summary = gate(a.nets, a.grid, a.via_cost, a.work, a.promote,
                       a.candidate, **extra)
    else:
        with tempfile.TemporaryDirectory(prefix="aqroot-demo-maze-") as tmp:
            summary = gate(a.nets, a.grid, a.via_cost, tmp, a.promote,
                           a.candidate, **extra)
    text = json.dumps(summary, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if summary["promotion_candidate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
