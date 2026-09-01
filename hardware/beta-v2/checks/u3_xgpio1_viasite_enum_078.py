# -*- coding: utf-8 -*-
"""D-376: explicit reachable-via-site enumeration for XGPIO1/In3.

Scratch only.  Replays the D-373 prefix and selects materially distinct legal
sites by rank instead of indirectly biasing the nearest-site score.
"""
import hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_r58_impact_replay_069 as D367
import u3_xgpio1_waypoint_076 as D374
import u3_xgpio1_inner_replay_075 as D373
import u3_xgpio2_inner_replay_073 as D371
import u3_topology_replay_066 as D364
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_xgpio1_viasite_enum_078.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO1_VIASITE_ENUM_078")
RANKS_A = range(1)
RANKS_B = range(2)
SEPARATION = 500000
STAGES = ((.25, -8), (.25, 4), (.25, 8), (.5, -12), (.5, 4),
          (.5, 8), (.5, 12), (.75, -8), (.75, -4), (.75, 4))


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    for name in RU.NEEDED:
        src, dst = os.path.join(RU.AUTH_DIR, name), os.path.join(SCRATCH, name)
        if os.path.isdir(src): shutil.copytree(src, dst)
        else: shutil.copy2(src, dst)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    baseline, _ = RU.drc(IR.AUTH, "u3x1enum_base", SCRATCH)
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = D362.copper(base)
    base_pairs = D362.connected_pairs(base); allowed, branches = D362.boundary(base)
    prefix, removed = D367.prepare("prefix", allowed, (0.0, -0.5))
    pair = D367.reserve_pair(prefix)
    qb = QR.QBoard(prefix); IR.inject_existing_via_obstacles(qb)
    prefix_routes = []
    for group, inner in (("XGPIO5_INNER", "I3"), ("XGPIO4_INNER", "I2"),
                         ("XGPIO2_INNER_PILOT", "I3"), ("XGPIO3_INNER", "I3")):
        rec = D371.route_inner(qb, group, inner); prefix_routes.append(rec)
        if not rec["ok"]: break
    qb.save(prefix)
    group = IR.GROUPS["XGPIO1_INNER"]
    seed = QR.QBoard(prefix); IR.inject_existing_via_obstacles(seed)
    net = IR.resolve_nets(seed, group)[group["nets"][0]]
    pads = {p["ref"]: p for p in IR.physical_net_pads(seed, net)}
    plan = group["inner_long_haul_plan"]; pa, pb = pads[plan["a"]], pads[plan["b"]]
    w, cp, ct = group["width"], group["clr_pad"], group["clr_trk"]
    vd, vk = group["via_dia"], group["via_drill"]
    prefix_ok = len(prefix_routes) == 4 and all(x["ok"] for x in prefix_routes)
    attempts, pairs = [], set()
    for ai in RANKS_A:
        for bi in RANKS_B:
            pcb = os.path.join(SCRATCH, "enum_%02d_%02d.kicad_pcb" % (ai, bi))
            shutil.copy2(prefix, pcb)
            trial = QR.QBoard(pcb); IR.inject_existing_via_obstacles(trial)
            ra = rb = {"ok": False, "reason": "PREFIX_FAILED"}
            if prefix_ok:
                ra = QR.reserve_escape(trial, net, pa, w, cp, ct, near="F", far="I3",
                    via_dia=vd, via_drill=vk, target=(pb["x"], pb["y"]),
                    site_index=ai, site_separation=SEPARATION)
                if ra.get("ok"):
                    rb = QR.reserve_escape(trial, net, pb, w, cp, ct, near="B", far="I3",
                        via_dia=vd, via_drill=vk, target=(pa["x"], pa["y"]),
                        site_index=bi, site_separation=SEPARATION)
            key = (tuple(ra.get("via", ())), tuple(rb.get("via", ())))
            row = {"a_rank": ai, "b_rank": bi, "a_reservation": ra,
                   "b_reservation": rb, "joins": [], "route_win": False,
                   "closed_candidate": False}
            if ra.get("ok") and rb.get("ok") and key not in pairs:
                pairs.add(key); mark = trial.mark()
                direct = QR.join_reserved(trial, net, ra["via"], rb["via"], w, cp, ct, layer="I3")
                row["joins"].append({"kind": "direct", "result": direct})
                if not direct.get("ok"):
                    trial.revert(mark)
                    for fraction, offset in STAGES:
                        mark = trial.mark(); wp = D374.point(ra["via"], rb["via"], fraction, offset)
                        staged = D374.join_staged(trial, net, ra["via"], rb["via"], wp, w, cp, ct)
                        row["joins"].append({"kind":"staged", "fraction":fraction,
                            "offset_mm":offset, "waypoint_mm":[round(wp[0]/1e6,3),round(wp[1]/1e6,3)],
                            "result":staged})
                        if staged.get("ok"): break
                        trial.revert(mark)
                row["route_win"] = any(x["result"].get("ok") for x in row["joins"])
                if row["route_win"]:
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
                    opens = {n:D363.open_edges(result,n) for n in sorted(targets)}
                    drc, details = RU.drc(pcb, "u3x1enum_%02d_%02d"%(ai,bi), SCRATCH)
                    worse = {k:[baseline.get(k,0),drc.get(k,0)]
                             for k in sorted(set(baseline)|set(drc))
                             if k != "unconnected_items" and drc.get(k,0)>baseline.get(k,0)}
                    closed = (removed==allowed and restored==wanted
                        and len(attachments)==len(D364.SCHEDULE)-4
                        and all(x["ok"] for x in attachments) and not forbidden_missing
                        and not forbidden_added and not broken and all(v==0 for v in opens.values())
                        and not worse and drc.get("unconnected_items",0)<=baseline.get("unconnected_items",0))
                    row.update({"remaining_restored_items":sum(restored.values()),
                        "terminal_attachments":attachments,
                        "forbidden_missing_count":sum(forbidden_missing.values()),
                        "forbidden_added_count":len(forbidden_added), "accepted_pairs_broken":broken,
                        "open_edges_after":opens, "drc_after":dict(drc), "drc_worse":worse,
                        "drc_worse_details":{k:sorted(details[k]) for k in worse},
                        "closed_candidate":bool(closed)})
            attempts.append(row)
            print(ai, bi, ra.get("reason"), rb.get("reason"), key, row["route_win"])
    wins = [x for x in attempts if x["route_win"]]
    closed = [x for x in attempts if x["closed_candidate"]]
    ev = {"schema_version":1, "decision":"D-376", "source_decision":"D-375",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"XGPIO1_In3_explicit_reachable_viasite_rank_enumeration",
          "site_separation_mm":SEPARATION/1e6, "baseline_drc":dict(baseline),
          "removed_boundary_exact":removed==allowed, "pair_routes":pair,
          "prefix_routes":prefix_routes, "rank_attempts":len(attempts),
          "distinct_via_pairs":len(pairs), "route_wins":len(wins),
          "transaction_candidates":len(closed), "attempts":attempts,
          "promotion_candidate":False,
          "conclusion":"closed_U3_transaction_candidate_needs_independent_gate" if closed else
                       "XGPIO1_distinct_viasite_route_found_but_transaction_open" if wins
                       else "XGPIO1_explicit_viasite_enumeration_characterized"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"distinct",len(pairs),"wins",len(wins),
          "auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
