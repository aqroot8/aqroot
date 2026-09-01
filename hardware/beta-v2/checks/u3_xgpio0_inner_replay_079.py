# -*- coding: utf-8 -*-
"""D-377: extend the D-376 U3 transaction through complete XGPIO0 replay.

Scratch only.  Reproduce the four selected inner routes, reserve XGPIO1's
proven rank-(0,1) In3 endpoints and direct join, then replace the complete
XGPIO0 branch independently on In2 and In3.  Restore and attach later branches
only after XGPIO0 closes.  The authoritative PCB is never edited.
"""
import collections, hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_r58_impact_replay_069 as D367
import u3_topology_replay_066 as D364
import u3_xgpio1_viasite_enum_078 as D376
import u3_xgpio2_inner_replay_073 as D371
import u3_xgpio3_inner_replay_074 as D372
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_xgpio0_inner_replay_079.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO0_INNER_REPLAY_079")


def restore_except_replaced(pcb, allowed):
    replaced = {"/XGPIO0", "/XGPIO1", "/XGPIO2", "/XGPIO3", "/XGPIO4", "/XGPIO5"}
    wanted = collections.Counter({s:n for s,n in allowed.items() if s[1] not in replaced})
    source, board = pcbnew.LoadBoard(IR.AUTH), pcbnew.LoadBoard(pcb)
    done = collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if done[s] < wanted[s]: board.Add(item.Duplicate()); done[s] += 1
    board.Save(pcb)
    return wanted, done


def route_xgpio1(qb):
    group = IR.GROUPS["XGPIO1_INNER"]
    net = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = {p["ref"]:p for p in IR.physical_net_pads(qb, net)}
    plan = group["inner_long_haul_plan"]; pa, pb = pads[plan["a"]], pads[plan["b"]]
    w, cp, ct = group["width"], group["clr_pad"], group["clr_trk"]
    vd, vk = group["via_dia"], group["via_drill"]
    ra = QR.reserve_escape(qb, net, pa, w, cp, ct, near="F", far="I3",
        via_dia=vd, via_drill=vk, target=(pb["x"],pb["y"]),
        site_index=0, site_separation=D376.SEPARATION)
    rb = ({"ok":False,"reason":"A_FAILED"} if not ra.get("ok") else
        QR.reserve_escape(qb, net, pb, w, cp, ct, near="B", far="I3",
            via_dia=vd, via_drill=vk, target=(pa["x"],pa["y"]),
            site_index=1, site_separation=D376.SEPARATION))
    join = ({"ok":False,"reason":"RESERVATION_FAILED"} if not rb.get("ok") else
            QR.join_reserved(qb, net, ra["via"], rb["via"], w, cp, ct, layer="I3"))
    return {"ok":bool(ra.get("ok") and rb.get("ok") and join.get("ok")),
            "a_reservation":ra, "b_reservation":rb, "join":join}


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()
    baseline, _ = RU.drc(IR.AUTH,"u3x0inner_base",SCRATCH)
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = D362.copper(base)
    base_pairs = D362.connected_pairs(base); allowed, branches = D362.boundary(base)
    attempts = []
    for inner in ("I2", "I3"):
        pcb, removed = D367.prepare("x0_"+inner.lower(), allowed, (0.0,-0.5))
        pair = D367.reserve_pair(pcb)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        prefix = []
        for group, layer in (("XGPIO5_INNER","I3"),("XGPIO4_INNER","I2"),
                             ("XGPIO2_INNER_PILOT","I3"),("XGPIO3_INNER","I3")):
            rec = D371.route_inner(qb,group,layer); prefix.append(rec)
            if not rec["ok"]: break
        x1 = route_xgpio1(qb) if len(prefix)==4 and all(x["ok"] for x in prefix) else {"ok":False,"reason":"PREFIX_FAILED"}
        x0 = D372.route_inner(qb,"XGPIO0_INNER",inner) if x1["ok"] else {"ok":False,"reason":"XGPIO1_FAILED"}
        qb.save(pcb)
        wanted = restored = collections.Counter(); attachments = []
        if x0["ok"]:
            wanted, restored = restore_except_replaced(pcb,allowed)
            qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
            for net in D364.SCHEDULE[6:]:
                attachments.append(D364.attach_terminal(qb,net,branches[net]["u3_pad"],branches[net]["width"]))
                if not attachments[-1]["ok"]: break
            if len(attachments)==len(D364.SCHEDULE)-6 and all(x["ok"] for x in attachments):
                attachments.append(D364.attach_terminal(qb,"/XGPIO7_HDR","R58.2",200000))
        IR.refill_planes(qb.b); qb.save(pcb)
        result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
        missing, added = base_cu-result_cu, result_cu-base_cu
        forbidden_missing = missing-allowed
        targets = set(branches)|{"/XGPIO6","/XGPIO7","/XGPIO7_HDR"}
        forbidden_added = [s for s in added.elements() if s[1] not in targets]
        broken = sorted(base_pairs-D362.connected_pairs(result))
        opens = {n:D363.open_edges(result,n) for n in sorted(targets)}
        drc, details = RU.drc(pcb,"u3x0inner_"+inner.lower(),SCRATCH)
        worse = {k:[baseline.get(k,0),drc.get(k,0)] for k in sorted(set(baseline)|set(drc))
                 if k!="unconnected_items" and drc.get(k,0)>baseline.get(k,0)}
        closed = (removed==allowed and len(prefix)==4 and all(x["ok"] for x in prefix)
                  and x1["ok"] and x0["ok"] and restored==wanted
                  and len(attachments)==len(D364.SCHEDULE)-5 and all(x["ok"] for x in attachments)
                  and not forbidden_missing and not forbidden_added and not broken
                  and all(v==0 for v in opens.values()) and not worse
                  and drc.get("unconnected_items",0)<=baseline.get("unconnected_items",0))
        row = {"xgpio0_inner_layer":inner,"pair_routes":pair,"prefix_routes":prefix,
               "xgpio1_ranked_route":x1,"xgpio0_route":x0,
               "remaining_restored_items":sum(restored.values()),"terminal_attachments":attachments,
               "first_remaining_failure":next((x for x in attachments if not x["ok"]),None),
               "forbidden_missing_count":sum(forbidden_missing.values()),
               "forbidden_added_count":len(forbidden_added),"accepted_pairs_broken":broken,
               "open_edges_after":opens,"drc_after":dict(drc),"drc_worse":worse,
               "drc_worse_details":{k:sorted(details[k]) for k in worse},
               "closed_candidate":bool(closed)}
        attempts.append(row)
        print(inner,"x1",x1["ok"],"x0",x0["ok"],"attachments",len(attachments),
              "first",row["first_remaining_failure"] and row["first_remaining_failure"]["net"],
              "drc+",sum(v[1]-v[0] for v in worse.values()),"closed",closed)
    wins = [x for x in attempts if x["closed_candidate"]]
    ev = {"schema_version":1,"decision":"D-377","source_decision":"D-376",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"D376_prefix_then_complete_XGPIO0_inner_branch_replacement",
          "selected_layout":{"u3_rotation_deg":180,"u3_offset_mm":[0.0,0.5],"r58_offset_mm":[0.0,-0.5]},
          "baseline_drc":dict(baseline),"attempts":attempts,
          "xgpio0_mechanism_wins":sum(1 for x in attempts if x["xgpio0_route"]["ok"]),
          "transaction_candidates":len(wins),"promotion_candidate":False,
          "conclusion":"closed_U3_transaction_candidate_needs_independent_gate" if wins else "XGPIO0_inner_replacement_characterized"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"x0 wins",ev["xgpio0_mechanism_wins"],
          "transaction wins",len(wins),"auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
