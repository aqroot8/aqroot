# -*- coding: utf-8 -*-
"""D-380: replay XGPIO8 with D-379's shortest explicit In3 via pair.

Scratch only. Rebuild the D-377 six-route prefix, reserve R59.1 rank 3 and
U3.13 rank 2, join them on In3, then restore and attach later U3 branches only
while each closes. The authoritative PCB is never edited.
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
import u3_xgpio0_inner_replay_079 as D377
import u3_xgpio2_inner_replay_073 as D371
import u3_xgpio3_inner_replay_074 as D372
import u3_xgpio6_replay_065 as D363
import u3_xgpio8_viasite_enum_081 as D379

OUT = os.path.join(SP, "u3_xgpio8_transaction_replay_082.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO8_TRANSACTION_REPLAY_082")
REPLACED = {"/XGPIO0", "/XGPIO1", "/XGPIO2", "/XGPIO3", "/XGPIO4",
            "/XGPIO5", "/XGPIO8"}


def restore_later(pcb, allowed):
    wanted = collections.Counter({s:n for s,n in allowed.items() if s[1] not in REPLACED})
    source, board = pcbnew.LoadBoard(IR.AUTH), pcbnew.LoadBoard(pcb)
    done = collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if done[s] < wanted[s]:
            board.Add(item.Duplicate()); done[s] += 1
    board.Save(pcb)
    return wanted, done


def route_xgpio8(qb):
    group = dict(IR.GROUPS["XGPIO8"])
    net = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = {p["ref"]:p for p in IR.physical_net_pads(qb, net)}
    pa, pb = pads["R59.1"], pads["U3.13"]
    ra = D379.reserve(qb, net, pa, pb, "F", "I3", 3, group)
    rb = ({"ok":False,"reason":"A_FAILED"} if not ra.get("ok") else
          D379.reserve(qb, net, pb, pa, "B", "I3", 2, group))
    join = ({"ok":False,"reason":"RESERVATION_FAILED"} if not rb.get("ok") else
            QR.join_reserved(qb, net, ra["via"], rb["via"], group["width"],
                             group["clr_pad"], group["clr_trk"], layer="I3"))
    return {"ok":bool(ra.get("ok") and rb.get("ok") and join.get("ok")),
            "a_rank":3, "b_rank":2, "a_reservation":ra,
            "b_reservation":rb, "join":join}


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()
    baseline, _ = RU.drc(IR.AUTH,"u3x8txn_base",SCRATCH)
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = D362.copper(base)
    base_pairs = D362.connected_pairs(base); boundary, branches = D362.boundary(base)
    allowed = boundary & base_cu
    pcb, removed = D367.prepare("candidate", allowed, (0.0,-0.5))
    pair = D367.reserve_pair(pcb)
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    prefix = []
    for group, layer in (("XGPIO5_INNER","I3"),("XGPIO4_INNER","I2"),
                         ("XGPIO2_INNER_PILOT","I3"),("XGPIO3_INNER","I3")):
        rec = D371.route_inner(qb,group,layer); prefix.append(rec)
        if not rec["ok"]: break
    x1 = D377.route_xgpio1(qb) if len(prefix)==4 and all(x["ok"] for x in prefix) else {"ok":False,"reason":"PREFIX_FAILED"}
    x0 = D372.route_inner(qb,"XGPIO0_INNER","I2") if x1["ok"] else {"ok":False,"reason":"XGPIO1_FAILED"}
    x8 = route_xgpio8(qb) if x0["ok"] else {"ok":False,"reason":"XGPIO0_FAILED"}
    qb.save(pcb)
    wanted = restored = collections.Counter(); attachments = []
    if x8["ok"]:
        wanted, restored = restore_later(pcb,allowed)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        for branch in D364.SCHEDULE[7:]:
            attachments.append(D364.attach_terminal(qb,branch,branches[branch]["u3_pad"],branches[branch]["width"]))
            if not attachments[-1]["ok"]: break
        if len(attachments)==len(D364.SCHEDULE)-7 and all(x["ok"] for x in attachments):
            attachments.append(D364.attach_terminal(qb,"/XGPIO7_HDR","R58.2",200000))
    IR.refill_planes(qb.b); qb.save(pcb)
    result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
    missing, added = base_cu-result_cu, result_cu-base_cu
    forbidden_missing = missing-allowed
    targets = set(branches)|{"/XGPIO6","/XGPIO7","/XGPIO7_HDR"}
    forbidden_added = [s for s in added.elements() if s[1] not in targets]
    broken = sorted(base_pairs-D362.connected_pairs(result))
    opens = {n:D363.open_edges(result,n) for n in sorted(targets)}
    drc, details = RU.drc(pcb,"u3x8txn_candidate",SCRATCH)
    worse = {k:[baseline.get(k,0),drc.get(k,0)] for k in sorted(set(baseline)|set(drc))
             if k!="unconnected_items" and drc.get(k,0)>baseline.get(k,0)}
    closed = (removed==allowed and len(pair)==2 and all(x["ok"] for x in pair)
              and len(prefix)==4 and all(x["ok"] for x in prefix) and x1["ok"]
              and x0["ok"] and x8["ok"] and restored==wanted
              and len(attachments)==len(D364.SCHEDULE)-6 and all(x["ok"] for x in attachments)
              and not forbidden_missing and not forbidden_added and not broken
              and all(v==0 for v in opens.values()) and not worse
              and drc.get("unconnected_items",0)<=baseline.get("unconnected_items",0))
    ev = {"schema_version":1,"decision":"D-380","source_decision":"D-379",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"D377_prefix_then_D379_shortest_XGPIO8_In3_pair_then_terminal_schedule",
          "selected_layout":{"u3_rotation_deg":180,"u3_offset_mm":[0.0,0.5],"r58_offset_mm":[0.0,-0.5]},
          "baseline_drc":dict(baseline),"removed_boundary_exact":removed==allowed,
          "pair_routes":pair,"prefix_routes":prefix,"xgpio1_ranked_route":x1,
          "xgpio0_route":x0,"xgpio8_ranked_route":x8,
          "remaining_restored_items":sum(restored.values()),"terminal_attachments":attachments,
          "first_remaining_failure":next((x for x in attachments if not x["ok"]),None),
          "forbidden_missing_count":sum(forbidden_missing.values()),
          "forbidden_added_count":len(forbidden_added),"accepted_pairs_broken":broken,
          "open_edges_after":opens,"drc_after":dict(drc),"drc_worse":worse,
          "drc_worse_details":{k:sorted(details[k]) for k in worse},
          "transaction_candidate":bool(closed),"promotion_candidate":False,
          "conclusion":"closed_U3_transaction_candidate_needs_independent_gate" if closed else "XGPIO8_transaction_replay_characterized"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"x8",x8["ok"],"attachments",len(attachments),
          "first",ev["first_remaining_failure"] and ev["first_remaining_failure"]["net"],
          "drc+",sum(v[1]-v[0] for v in worse.values()),"auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
