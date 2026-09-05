#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- give a footprint's OWN keep-out the WHOLE stackup, and move
the copper that was standing in it.

D-616 measured the defect and refused to close it without a route in hand.
`U1`'s footprint carries Espressif's ESP32-S3-WROOM-1 ANTENNA KEEP-OUT -- no
tracks, vias, pads, pour or footprints -- and its MASTER applies it to `*.Cu`,
every copper layer there is.  KiCad clamped `*.Cu` to the four-layer stackup
`U1` was placed on and never re-expanded it when `In3.Cu` and `In4.Cu` were
added, so the board's copy names four layers, DRC honours it exactly as
written, and **there is no violation and no way to notice except to ask.**
Inside the 330 mm2 on-board part of the region the four protected layers are
empty to 0.000 mm2 -- the proof the keep-out works -- while `In3.Cu` holds
273.697 mm2 of `+3V3` plane and `In4.Cu` 304.259 mm2 of `GND` pour, and five
track segments of two nets cross it.

This module performs the whole transaction, and the ORDER IS THE CONTRACT:

  1. THE LICENCE IS AUTHORED FIRST.  The rule area is widened to `*.Cu` on the
     scratch board BEFORE anything reads it, so `qrouter.QBoard.addko` -- which
     honours a rule area exactly as authored, per layer -- raises the keep-out
     as an OBSTACLE on `In3`/`In4` and the router is bound by the very rule
     this run is buying.  A route proposed against the old rule and blessed by
     the new one would be a route nothing ever checked.
  2. THE COPPER IS NAMED, NOT SEARCHED.  Each crossing chain is resolved to
     exactly one track per description by `route_maze_batch.detour_apply`; a
     description matching zero or many tracks stops the run.
  3. THE COPPER IS PUT BACK BY THE ROUTER, between its OWN two end
     coordinates, on the layers this plan licenses -- never by hand.
  4. THE POURS ARE JUDGED AFTER KiCad'S OWN REFILL, never before.  The carve is
     ~330 mm2 out of two planes and the only honest question -- did it island
     either of them, or strand a pad -- is answerable on the refilled board.

TWO LICENCES THIS PLAN MAY GRANT A DETOUR, both narrower than they look:

  * D-609's OWN-LAYER allowance says a track may be put back on the layer it
    ALREADY lawfully occupies even when that layer is a reserved inner plane,
    because the slot already exists.  This plan may widen that to
    `permitted + own`, and clause K6 prices it: the detour may not leave MORE
    copper on a reserved plane it does not own than it took off it.  The slot
    may move and it may shrink; it may not grow.
  * A chain whose BOTH ENDS are through vias of its own net may terminate on
    any layer that barrel spans, because a barrel is copper on every layer and
    the connection point is layer-agnostic.  Clause K5 proves the barrel is
    there and spans the layer, on the AUTHORITATIVE board, or refuses.

    python3 hardware/demo/manufacturing/apply_antenna_keepout.py \
        --plan PLAN.json [--candidate OUT.kicad_pcb] [--promote] [-o REPORT]

Dry by default: with no `--candidate` and no `--promote` it measures, prints
its evidence and writes nothing outside its work directory.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import route_maze_batch as R          # noqa: E402
import verify_promotion as V          # noqa: E402

# The DRC classes this board carries that no promotion is answerable for, read
# with the footprint libraries ACTUALLY RESOLVED -- which is what
# `verify_promotion.stage` guarantees and what makes `lib_footprint_mismatch` a
# live class rather than an unaskable one.  `lib_footprint_mismatch` is the
# baseline this transaction exists to SPEND: clause K8 requires it to FALL.
INHERITED = dict(V.INHERITED)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# child 1 -- the licence
# --------------------------------------------------------------------------- #
def all_rule_areas(board):
    """Every rule area on the board -- board-level AND footprint-embedded.

    `pcbnew.BOARD.Zones()` returns the BOARD's zones and NOT a footprint's, and
    that single fact hid four fifths of this defect for the whole life of the
    project: this board carries FIVE keep-out rule areas clamped to four of six
    copper layers, and only ONE of them lives inside a footprint.  A check that
    iterates `board.Zones()` cannot see `U1`'s; a check that iterates
    `footprint.Zones()` cannot see the other four.  This iterates both, and
    keys on the UUID because two of them share a NAME.
    """
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            out.append((None, z))
    for fp in board.GetFootprints():
        for z in fp.Zones():
            if z.GetIsRuleArea():
                out.append((fp.GetReference(), z))
    return out


def rule_area_sigs(path):
    """uuid -> comparable signature, ENABLED copper layers only.

    The layer set is intersected with the board's own enabled stack because a
    zone written `(layers "*.Cu")` reads back as all THIRTY-TWO copper layers
    KiCad can name, of which this board has six.  Comparing the raw set would
    make a correct licence look like a 28-layer change.
    """
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    enabled = [board.GetLayerName(l)
               for l in board.GetEnabledLayers().CuStack()]
    out = {}
    for owner, z in all_rule_areas(board):
        o = z.Outline().Outline(0)
        have = {board.GetLayerName(l) for l in z.GetLayerSet().Seq()}
        out[str(z.m_Uuid.AsString())] = dict(
            owner=owner, name=z.GetZoneName(),
            layers=tuple(L for L in enabled if L in have),
            flags=(bool(z.GetDoNotAllowTracks()), bool(z.GetDoNotAllowVias()),
                   bool(z.GetDoNotAllowPads()), bool(z.GetDoNotAllowZoneFills()),
                   bool(z.GetDoNotAllowFootprints())),
            outline=tuple((o.CPoint(i).x, o.CPoint(i).y)
                          for i in range(o.PointCount())))
    return out, enabled


def licence_apply(path, plan):
    """Widen every named rule area's layer set, then re-read what was written.

    `pcbnew.SaveBoard` rewrites the whole file and would bury a one-token change
    in incidental reformatting, so this edits the TEXT -- and, following D-615,
    each edit must NAME the exact string it overwrites and say how many times
    that string may occur.  The post-condition is then re-read through `pcbnew`
    and checked against what the plan CLAIMED: a plan that hits the right text
    in the wrong place fails here rather than in a Gerber.

    The post-condition is a SUPERSET test, not equality.  `(layers "*.Cu")` is
    what the ESP32-S3-WROOM-1 master itself writes and it reads back as all 32
    copper layers KiCad can name; what matters is that every layer this board
    ACTUALLY HAS is protected, and that it stays protected if the stackup grows
    again -- which is the failure this whole transaction exists to repair.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    for lic in plan["licences"]:
        hits = text.count(lic["old"])
        if hits != lic.get("occurrences", 1):
            raise SystemExit("--licence %s: %r occurs %d times, plan says %d"
                             % (lic["expect_area_name"], lic["old"], hits,
                                lic.get("occurrences", 1)))
        text = text.replace(lic["old"], lic["new"])
    path.write_text(text, encoding="utf-8")

    sigs, enabled = rule_area_sigs(path)
    out = []
    for lic in plan["licences"]:
        got = sigs.get(lic["uuid"])
        rec = dict(uuid=lic["uuid"], owner=(got or {}).get("owner"),
                   name=(got or {}).get("name"),
                   layers_after=list((got or {}).get("layers", ())),
                   board_copper=list(enabled))
        rec["covers_whole_stackup"] = bool(
            got and set(enabled) <= set(got["layers"]))
        rec["name_ok"] = bool(got and got["name"] == lic["expect_area_name"]
                              and got["owner"] == lic.get("expect_owner"))
        rec["keepout"] = dict(zip(
            ("tracks", "vias", "pads", "zone_fills", "footprints"),
            (got or {}).get("flags", (None,) * 5)))
        rec["keepout_ok"] = rec["keepout"] == lic["expect_keepout"]
        rec["ok"] = bool(rec["covers_whole_stackup"] and rec["name_ok"]
                         and rec["keepout_ok"])
        out.append(rec)
    return out


# --------------------------------------------------------------------------- #
# child 2 -- put the copper back
# --------------------------------------------------------------------------- #
def route_apply(path, plan, detour):
    """Re-lay each named chain with the router, on the scratch that already
    carries the widened keep-out.  Copper is laid, never moved: the removal was
    child `--detour-apply`'s and is licensed by signature."""
    import pcbnew
    import qrouter as qr
    import maze3d as mz
    import incremental_router as ir

    # POSITIONAL, never keyed by net: a plan may name TWO chains of the SAME
    # net -- this one does, because `USB_VBUS_CHG` crosses two different
    # keep-outs -- and a dict keyed on the netname would silently route one of
    # them twice and leave the other's copper on the floor.
    chains = detour["detours"]
    if len(chains) != len(plan["detours"]):
        raise SystemExit("--route: %d chains resolved for %d planned"
                         % (len(chains), len(plan["detours"])))
    ref = pcbnew.LoadBoard(str(path))
    contracts = {d["net"]: R.net_contract(ref, d["net"]) for d in chains}
    reserved = R.reserved_inner_planes(ref)
    del ref

    qb = qr.QBoard(str(path))
    ir.inject_existing_via_obstacles(qb)
    for n, c in contracts.items():
        c["layers"] = R.permitted_layers(qb.routable, c["layers"], reserved, n)

    laid = []
    for spec, d in zip(plan["detours"], chains):
        net = spec["net"]
        if d["net"] != net:
            raise SystemExit("--route: chain %d is %s, plan says %s"
                             % (chains.index(d), d["net"], net))
        c = contracts[net]
        want = tuple(spec["layers"])
        if spec.get("own_layer", True) and d["lkey"] not in want:
            want = want + (d["lkey"],)
        t0 = time.time()
        field = mz.Field(qb, net, d["width_nm"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=plan.get("grid",
                                                                  100000),
                         layers=want)
        r = mz.route_points(qb, field, tuple(d["a_nm"]), tuple(d["b_nm"]),
                            spec["end_layer"],
                            via_cost_mm=plan.get("via_cost_mm", 1.5),
                            max_mm=float(spec.get("max_mm", 0.0)))
        r = dict(r)
        r.pop("mark", None)
        r.update(net=net, was_mm=d["mm"], width_nm=d["width_nm"],
                 lkey=d["lkey"], layers_allowed=list(want),
                 end_layer=spec["end_layer"],
                 permitted=list(c["layers"]), netclass=c["netclass"],
                 reserved_planes={k: sorted(v) for k, v in reserved.items()},
                 a_mm=[round(v / 1e6, 4) for v in d["a_nm"]],
                 b_mm=[round(v / 1e6, 4) for v in d["b_nm"]],
                 seconds=round(time.time() - t0, 1))
        if r.get("ok"):
            r["mm_by_layer"] = {k: round(v, 4)
                                for k, v in r["mm_by_layer"].items()}
            r["mm"] = round(r["mm"], 4)
        print("  %-44s %s %.3f -> %.3f mm, %s via"
              % (net, "ok" if r.get("ok") else r.get("reason"), d["mm"],
                 r.get("mm") or 0.0, r.get("vias")),
              file=sys.stderr, flush=True)
        laid.append(r)
        if not r.get("ok"):
            break
    if all(r.get("ok") for r in laid):
        pcbnew.SaveBoard(str(path), qb.b)
    return laid


# --------------------------------------------------------------------------- #
# clause K5 -- the layer a chain may terminate on
# --------------------------------------------------------------------------- #
LKEY = {"F": "F.Cu", "I1": "In1.Cu", "I2": "In2.Cu", "I3": "In3.Cu",
        "I4": "In4.Cu", "B": "B.Cu"}


def barrel_ends(path, detour, plan):
    """Does a through via of the net sit on each chain end, spanning BOTH the
    layer the chain was on and the layer this plan wants it to terminate on?

    That is the whole justification for letting a detour change layer: a barrel
    is copper on every layer it spans, so where the removed track met it is not
    a coordinate ON A LAYER, it is a coordinate ON A BARREL.  Where the plan
    asks for no change of layer the question is vacuous and the answer says so.
    """
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for spec, d in zip(plan["detours"], detour["detours"]):
        need = LKEY[spec["end_layer"]]
        was = LKEY[d["lkey"]]
        for tag, xy in (("a", d["a_nm"]), ("b", d["b_nm"])):
            rec = dict(net=spec["net"], end=tag,
                       xy=[round(v / 1e6, 4) for v in xy],
                       was_layer=was, end_layer=need)
            if need == was:
                rec.update(needed=False, ok=True, why="no change of layer")
                out.append(rec)
                continue
            hit = None
            for t in board.GetTracks():
                if t.GetClass() != "PCB_VIA" or t.GetNetname() != spec["net"]:
                    continue
                p = t.GetPosition()
                if int(p.x) == int(xy[0]) and int(p.y) == int(xy[1]):
                    hit = t
                    break
            spans = (hit is not None
                     and hit.IsOnLayer(board.GetLayerID(need))
                     and hit.IsOnLayer(board.GetLayerID(was)))
            rec.update(needed=True, via=hit is not None, ok=bool(spans),
                       via_layers=(None if hit is None else
                                   [board.GetLayerName(hit.TopLayer()),
                                    board.GetLayerName(hit.BottomLayer())]))
            out.append(rec)
    return out


# --------------------------------------------------------------------------- #
# pours, measured on the REFILLED board
# --------------------------------------------------------------------------- #
def pours(path):
    """(net, layer) -> (island count, filled area mm2) for every real pour."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = {}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lid in z.GetLayerSet().Seq():
            name = board.GetLayerName(lid)
            if not name.endswith(".Cu"):
                continue
            poly = z.GetFilledPolysList(lid)
            cur = out.setdefault("%s|%s" % (z.GetNetname(), name), [0, 0.0])
            cur[0] += poly.OutlineCount()
            cur[1] += poly.Area() / 1e12
    return {k: [v[0], round(v[1], 3)] for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--work", type=Path)
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    # internal children -- see the docstring on why each runs in its own process
    ap.add_argument("--licence-apply", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--licence-report", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--route-apply", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--detour-report", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--route-report", type=Path, help=argparse.SUPPRESS)
    a = ap.parse_args()
    plan = json.loads(a.plan.read_text())
    if plan.get("schema") != 1:
        raise SystemExit("--plan: unknown schema %r" % plan.get("schema"))

    if a.licence_apply:
        a.licence_report.write_text(
            json.dumps(licence_apply(a.licence_apply, plan), indent=1))
        return
    if a.route_apply:
        det = json.loads(a.detour_report.read_text())
        a.route_report.write_text(
            json.dumps(route_apply(a.route_apply, plan, det), indent=1))
        return

    before = sha(BOARD)
    work = Path(a.work or tempfile.mkdtemp(prefix="aqroot-antenna-ko-"))
    work.mkdir(parents=True, exist_ok=True)
    scratch = V.stage(None, work / "cand")

    # ---- K1 THE LICENCE IS AUTHORED FIRST ------------------------------- #
    lic_report = work / "licence.json"
    subprocess.run([sys.executable, __file__, "--plan", str(a.plan),
                    "--licence-apply", str(scratch),
                    "--licence-report", str(lic_report)],
                   check=True, capture_output=True, text=True)
    licence = json.loads(lic_report.read_text())

    # ---- K2 the crossing chains, named and removed ---------------------- #
    spec = work / "detour-spec.json"
    spec.write_text(json.dumps(
        dict(schema=1, reserve=[],
             detours=[dict(net=d["net"], tracks=d["tracks"],
                           max_mm=float(d.get("max_mm", 0.0)) or 1e9)
                      for d in plan["detours"]]), indent=1))
    det_report = work / "detour.json"
    subprocess.run([sys.executable, str(HERE / "route_maze_batch.py"),
                    "--detour-apply", str(scratch), "--detour-spec", str(spec),
                    "--detour-report", str(det_report)],
                   check=True, capture_output=True, text=True)
    detour = json.loads(det_report.read_text())

    # ---- K5 may these chains change layer at all? ----------------------- #
    ends = barrel_ends(BOARD, detour, plan)

    # ---- K3 put it back, with the router, under the new rule ------------ #
    route_report = work / "routed.json"
    subprocess.run([sys.executable, __file__, "--plan", str(a.plan),
                    "--route-apply", str(scratch),
                    "--detour-report", str(det_report),
                    "--route-report", str(route_report)], check=True)
    laid = json.loads(route_report.read_text())

    # ---- K7/K8/K9 the consequences, after a REAL refill ----------------- #
    drc_json = work / "drc.json"
    done = R.full_drc(scratch, drc_json)
    report = json.loads(drc_json.read_text())
    counts = {}
    for v in report.get("violations", []):
        counts[v.get("type", "unknown")] = counts.get(v.get("type"), 0) + 1
    attributable = [v for v in report.get("violations", [])
                    if v.get("type") not in INHERITED]
    inherited_ok = all(counts.get(k, 0) <= n for k, n in INHERITED.items())
    parity = report.get("schematic_parity", [])
    unconnected = len(report.get("unconnected_items", []))

    base_drc = work / "drc-base.json"
    base_cell = V.stage(None, work / "base")
    R.full_drc(base_cell, base_drc)
    base_report = json.loads(base_drc.read_text())
    base_counts = {}
    for v in base_report.get("violations", []):
        base_counts[v.get("type", "unknown")] = \
            base_counts.get(v.get("type"), 0) + 1
    base_unconnected = len(base_report.get("unconnected_items", []))
    base_parity = len(base_report.get("schematic_parity", []))

    base_ledger = R.ledger(base_cell, work / "ledger-base.json")
    after_ledger = R.ledger(scratch, work / "ledger-after.json")
    was = {r["net"]: r["open_edges"] for r in base_ledger["nets"]}
    now = {r["net"]: r["open_edges"] for r in after_ledger["nets"]}
    regressed = sorted(n for n, v in now.items() if v > was.get(n, v))
    closed = sorted(n for n in was if now.get(n, 0) < was[n])
    edges_before = base_ledger["connectivity"]["retained_open_edges"]
    edges_after = after_ledger["connectivity"]["retained_open_edges"]

    # ---- K4 nothing removed that was not named; nothing added elsewhere -- #
    base_cu, cand_cu = R.copper(base_cell), R.copper(scratch)
    licensed = set(detour.get("removed_signatures", ()))
    removed = sorted(str(k) for k in (base_cu - cand_cu))
    unlicensed = sorted(set(removed) - licensed)
    added_nets = sorted({k[1] for k in (cand_cu - base_cu)})
    claimed = sorted({d["net"] for d in plan["detours"]})
    foreign = sorted(set(added_nets) - set(claimed))

    # ---- K2 the licence changed EXACTLY the named areas, and only their
    #         LAYER SET -- no rule area gained, lost, renamed, re-shaped or
    #         given a new flag, and no POUR touched at all.
    ra_before, _ = rule_area_sigs(base_cell)
    ra_after, board_cu = rule_area_sigs(scratch)
    named = {l["uuid"] for l in plan["licences"]}
    ra_lost = sorted(set(ra_before) - set(ra_after))
    ra_added = sorted(set(ra_after) - set(ra_before))
    changed, wrong = [], []
    for uid in sorted(set(ra_before) & set(ra_after)):
        was, now_ = ra_before[uid], ra_after[uid]
        if was == now_:
            continue
        changed.append(uid)
        same_shape = all(was[k] == now_[k] for k in ("owner", "name", "flags",
                                                     "outline"))
        grew = set(was["layers"]) < set(now_["layers"])
        if uid not in named or not same_shape or not grew:
            wrong.append(dict(uuid=uid, name=was["name"], in_plan=uid in named,
                              same_shape=same_shape,
                              layers=[list(was["layers"]),
                                      list(now_["layers"])]))
    zone_before, zone_after = R.zones(base_cell), R.zones(scratch)
    zone_ok = zone_before == zone_after
    rule_area_ok = (not ra_lost and not ra_added and not wrong
                    and sorted(changed) == sorted(named))
    licence_ok = all(l["ok"] for l in licence)
    protected = {uid: list(ra_after[uid]["layers"]) for uid in sorted(named)}
    unprotected = {uid: [L for L in board_cu
                         if L not in ra_after[uid]["layers"]]
                   for uid in sorted(named)}

    # ---- K6 A DETOUR OWES A BOUND, AND THE DEFAULT BOUND IS ITSELF ------ #
    # A track put back between its own two ends should not come away longer
    # than it went in, and on this board two of the three do not: they come
    # away SHORTER.  The third cannot -- BOSS1_KEEPOUT's In3.Cu face is a new
    # obstacle and the corner walk round it is real copper -- so a plan may
    # state its own `max_mm` and OWN that judgement in writing.  What it may
    # not do is silently exceed the copper it replaced.
    bound = {}
    for spec, r in zip(plan["detours"], laid):
        bound[id(r)] = float(spec.get("max_mm") or 0.0) or r["was_mm"]
    plane_price = []
    for r in laid:
        if not r.get("ok"):
            continue
        owned = set()
        for lay, nets in (r.get("reserved_planes") or {}).items():
            if r["net"] in nets:
                owned.add(lay)
        for lay, mm in (r.get("mm_by_layer") or {}).items():
            if lay in (r.get("reserved_planes") or {}) and lay not in owned:
                took = bound[id(r)] if lay == r["lkey"] else 0.0
                plane_price.append(dict(net=r["net"], layer=LKEY[lay],
                                        removed_mm=round(r["was_mm"], 4),
                                        bound_mm=round(took, 4),
                                        laid_mm=mm, ok=bool(mm <= took + 1e-9)))
    plane_ok = all(p["ok"] for p in plane_price)

    # ---- K5/K3 verdicts ------------------------------------------------- #
    ends_ok = all(e["ok"] for e in ends)
    laid_ok = bool(laid) and all(r.get("ok") for r in laid)
    shorter = [dict(net=r["net"], was_mm=r["was_mm"], mm=r.get("mm"),
                    bound_mm=round(bound[id(r)], 4), vias=r.get("vias"),
                    ok=bool(r.get("ok") and r["mm"] <= bound[id(r)] + 1e-9))
               for r in laid]
    shorter_ok = all(s["ok"] for s in shorter)

    keepout_clean = counts.get("items_not_allowed", 0) == 0
    mismatch_fell = (counts.get("lib_footprint_mismatch", 0)
                     < base_counts.get("lib_footprint_mismatch", 0))

    pour_before, pour_after = pours(base_cell), pours(scratch)
    pour_delta = {k: dict(islands=[pour_before.get(k, [0, 0.0])[0],
                                   pour_after.get(k, [0, 0.0])[0]],
                          area_mm2=[pour_before.get(k, [0, 0.0])[1],
                                    pour_after.get(k, [0, 0.0])[1]])
                  for k in sorted(set(pour_before) | set(pour_after))
                  if pour_before.get(k) != pour_after.get(k)}

    clauses = {
        "K1_authority_unchanged": before == sha(BOARD),
        "K2_only_named_rule_areas_changed": bool(rule_area_ok and zone_ok),
        "K2_every_licence_covers_stackup": bool(licence_ok),
        "K2_no_enabled_layer_left_out": not any(unprotected.values()),
        "K3_every_chain_relaid": laid_ok,
        "K4_removals_licensed": not unlicensed,
        "K4_additions_claimed": not foreign,
        "K5_end_layer_is_a_barrel": ends_ok,
        "K6_no_foreign_plane_growth": plane_ok,
        "K6_within_length_bound": shorter_ok,
        "K7_drc_zero_attributable": not attributable,
        "K7_inherited_within_baseline": inherited_ok,
        "K7_keepout_clean": keepout_clean,
        "K8_keepout_mismatch_fell": mismatch_fell,
        "K9_no_net_regressed": not regressed,
        "K9_open_edges_not_worse": edges_after <= edges_before,
        "K9_unconnected_not_worse": unconnected <= base_unconnected,
        "K9_parity_not_worse": len(parity) <= base_parity,
    }
    ok = all(clauses.values())

    summary = dict(
        schema=1,
        plan=str(a.plan), plan_sha256=sha(a.plan),
        authoritative_board_sha256=before,
        candidate_sha256=sha(scratch),
        licences=licence,
        rule_areas_lost=ra_lost, rule_areas_added=ra_added,
        rule_areas_changed=changed, rule_areas_changed_wrongly=wrong,
        protected_layers=protected, unprotected_layers=unprotected,
        pour_zone_inventory_unchanged=zone_ok,
        detour=dict(removed_count=detour["removed_count"],
                    removed_mm=detour["removed_mm"],
                    nets=detour["nets"], chains=detour["detours"]),
        chain_ends=ends,
        routed=laid,
        length=shorter,
        reserved_plane_price=plane_price,
        preservation=dict(removed_objects=removed,
                          unlicensed_removals=unlicensed,
                          licensed_removals=len(licensed),
                          added_object_nets=added_nets,
                          foreign_added_nets=foreign,
                          claimed_nets=claimed),
        drc=dict(exit=done.returncode, types=counts, base_types=base_counts,
                 attributable=attributable,
                 unconnected=[base_unconnected, unconnected],
                 schematic_parity=[base_parity, len(parity)]),
        connectivity=dict(retained_open_edges=[edges_before, edges_after],
                          nets_improved=closed, nets_regressed=regressed),
        pours=pour_delta,
        clauses=clauses,
        promotion_candidate=ok,
    )
    if a.out:
        a.out.write_text(json.dumps(summary, indent=1, sort_keys=True,
                                    default=str))
    print(json.dumps({k: v for k, v in summary.items()
                      if k in ("clauses", "connectivity", "length",
                               "reserved_plane_price", "pours",
                               "promotion_candidate")},
                     indent=1, sort_keys=True, default=str))
    for k, v in sorted(clauses.items()):
        print("%-34s %s" % (k, "PASS" if v else "FAIL"), file=sys.stderr)
    if a.candidate and ok:
        Path(a.candidate).write_bytes(scratch.read_bytes())
    if a.promote:
        if not ok:
            raise SystemExit("refuse promotion: gate failed")
        if before != sha(BOARD):
            raise SystemExit("refuse promotion: authority changed under the run")
        BOARD.write_bytes(scratch.read_bytes())
        print("PROMOTED %s -> %s" % (before[:16], sha(BOARD)[:16]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
