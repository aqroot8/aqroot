# -*- coding: utf-8 -*-
"""D-374: bounded staged-waypoint sweep for the XGPIO1 In3 join.

Scratch only.  Replays the D-373 prefix once, reserves both XGPIO1 endpoint
escapes once, then tests deterministic line-relative In3 waypoint anchors from
an identical seed.  A route winner is subjected to the remaining branch replay,
connectivity preservation, and real KiCad DRC checks.  Authority is never edited.
"""
import collections, hashlib, json, math, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_r58_impact_replay_069 as D367
import u3_topology_replay_066 as D364
import u3_xgpio1_inner_replay_075 as D373
import u3_xgpio2_inner_replay_073 as D371
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_xgpio1_waypoint_076.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO1_WAYPOINT_076")
# (fraction along reserved-via chord, signed perpendicular offset in mm).
WAYPOINTS = tuple((f, o) for f, offsets in (
    (0.25, (-8, -4, 0, 4, 8)),
    (0.50, (-12, -8, -4, 0, 4, 8, 12)),
    (0.75, (-8, -4, 0, 4, 8)),
) for o in offsets)


def snap(v, grid=50000):
    return int(round(v / grid)) * grid


def point(va, vb, fraction, offset_mm):
    dx, dy = vb[0] - va[0], vb[1] - va[1]
    length = math.hypot(dx, dy)
    nx, ny = (-dy / length, dx / length)
    off = offset_mm * 1000000
    return (snap(va[0] + fraction * dx + nx * off),
            snap(va[1] + fraction * dy + ny * off))


def join_staged(qb, net, va, vb, wp, width, cp, ct):
    if not qb.point_free("I3", net, wp[0], wp[1], width, cp, ct, 25000):
        return {"ok": False, "reason": "WAYPOINT_BLOCKED"}
    mark = qb.mark()
    first = QR.join_reserved(qb, net, va, wp, width, cp, ct, layer="I3")
    if not first.get("ok"):
        qb.revert(mark)
        return {"ok": False, "reason": "FIRST_LEG_" + first.get("reason", "FAIL"),
                "first": first}
    second = QR.join_reserved(qb, net, wp, vb, width, cp, ct, layer="I3")
    if not second.get("ok"):
        qb.revert(mark)
        return {"ok": False, "reason": "SECOND_LEG_" + second.get("reason", "FAIL"),
                "first": first, "second": second}
    return {"ok": True, "reason": None, "first": first, "second": second,
            "mm": first["mm"] + second["mm"]}


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = D362.copper(base)
    base_pairs = D362.connected_pairs(base); allowed, branches = D362.boundary(base)
    baseline, _ = RU.drc(IR.AUTH, "u3x1wp_base", SCRATCH)

    prefix, removed = D367.prepare("prefix", allowed, (0.0, -0.5))
    pair = D367.reserve_pair(prefix)
    qb = QR.QBoard(prefix); IR.inject_existing_via_obstacles(qb)
    prefix_routes = []
    for group, inner in (("XGPIO5_INNER", "I3"), ("XGPIO4_INNER", "I2"),
                         ("XGPIO2_INNER_PILOT", "I3"), ("XGPIO3_INNER", "I3")):
        rec = D371.route_inner(qb, group, inner); prefix_routes.append(rec)
        if not rec["ok"]: break
    group = IR.GROUPS["XGPIO1_INNER"]
    net = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = {p["ref"]: p for p in IR.physical_net_pads(qb, net)}
    plan = group["inner_long_haul_plan"]; pa, pb = pads[plan["a"]], pads[plan["b"]]
    w, cp, ct = group["width"], group["clr_pad"], group["clr_trk"]
    vd, vk = group["via_dia"], group["via_drill"]
    ra = rb = {"ok": False, "reason": "PREFIX_FAILED"}
    if len(prefix_routes) == 4 and all(x["ok"] for x in prefix_routes):
        ra = QR.reserve_escape(qb, net, pa, w, cp, ct, near="F", far="I3",
                               via_dia=vd, via_drill=vk, target=(pb["x"], pb["y"]))
        if ra.get("ok"):
            rb = QR.reserve_escape(qb, net, pb, w, cp, ct, near="B", far="I3",
                                   via_dia=vd, via_drill=vk, target=(pa["x"], pa["y"]))
    qb.save(prefix)

    attempts = []
    if ra.get("ok") and rb.get("ok"):
        for index, (fraction, offset) in enumerate(WAYPOINTS):
            pcb = os.path.join(SCRATCH, "wp_%02d.kicad_pcb" % index)
            shutil.copy2(prefix, pcb)
            trial = QR.QBoard(pcb); IR.inject_existing_via_obstacles(trial)
            wp = point(ra["via"], rb["via"], fraction, offset)
            route = join_staged(trial, net, ra["via"], rb["via"], wp, w, cp, ct)
            row = {"index": index, "fraction": fraction, "offset_mm": offset,
                   "waypoint_mm": [round(wp[0]/1e6, 3), round(wp[1]/1e6, 3)],
                   "route": route, "closed_candidate": False}
            if route["ok"]:
                trial.save(pcb)
                wanted, restored = D373.restore_except_replaced(pcb, allowed)
                trial = QR.QBoard(pcb); IR.inject_existing_via_obstacles(trial)
                attachments = []
                for branch in D364.SCHEDULE[5:]:
                    attachments.append(D364.attach_terminal(
                        trial, branch, branches[branch]["u3_pad"], branches[branch]["width"]))
                    if not attachments[-1]["ok"]: break
                if len(attachments) == len(D364.SCHEDULE)-5 and all(x["ok"] for x in attachments):
                    attachments.append(D364.attach_terminal(trial, "/XGPIO7_HDR", "R58.2", 200000))
                IR.refill_planes(trial.b); trial.save(pcb)
                result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
                missing, added = base_cu-result_cu, result_cu-base_cu
                forbidden_missing = missing-allowed
                targets = set(branches) | {"/XGPIO6", "/XGPIO7", "/XGPIO7_HDR"}
                forbidden_added = [s for s in added.elements() if s[1] not in targets]
                broken = sorted(base_pairs-D362.connected_pairs(result))
                opens = {n: D363.open_edges(result, n) for n in sorted(targets)}
                drc, details = RU.drc(pcb, "u3x1wp_%02d" % index, SCRATCH)
                worse = {k:[baseline.get(k,0), drc.get(k,0)]
                         for k in sorted(set(baseline)|set(drc))
                         if k != "unconnected_items" and drc.get(k,0) > baseline.get(k,0)}
                closed = (removed == allowed and restored == wanted
                          and len(attachments) == len(D364.SCHEDULE)-4
                          and all(x["ok"] for x in attachments) and not forbidden_missing
                          and not forbidden_added and not broken and all(v == 0 for v in opens.values())
                          and not worse and drc.get("unconnected_items",0) <= baseline.get("unconnected_items",0))
                row.update({"remaining_restored_items": sum(restored.values()),
                            "terminal_attachments": attachments,
                            "forbidden_missing_count": sum(forbidden_missing.values()),
                            "forbidden_added_count": len(forbidden_added),
                            "accepted_pairs_broken": broken, "open_edges_after": opens,
                            "drc_after": dict(drc), "drc_worse": worse,
                            "drc_worse_details": {k: sorted(details[k]) for k in worse},
                            "closed_candidate": bool(closed)})
            attempts.append(row)
            print(index, fraction, offset, route["reason"], "closed", row["closed_candidate"])

    wins = [x for x in attempts if x["closed_candidate"]]
    route_wins = [x for x in attempts if x["route"]["ok"]]
    ev = {"schema_version":1, "decision":"D-374", "source_decision":"D-373",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"XGPIO1_In3_reserved_escape_line_relative_staged_waypoint_sweep",
          "selected_layout":{"u3_rotation_deg":180,"u3_offset_mm":[0.0,0.5],
                             "r58_offset_mm":[0.0,-0.5]},
          "baseline_drc":dict(baseline), "pair_routes":pair, "prefix_routes":prefix_routes,
          "xgpio1_reservations":{"a":ra,"b":rb}, "attempts":attempts,
          "waypoints_tested":len(attempts), "xgpio1_route_wins":len(route_wins),
          "transaction_candidates":len(wins), "promotion_candidate":False,
          "conclusion":"closed_U3_transaction_candidate" if wins else "XGPIO1_waypoint_sweep_characterized"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT", ev["conclusion"], "route wins", len(route_wins),
          "transaction wins", len(wins), "auth unchanged", ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
