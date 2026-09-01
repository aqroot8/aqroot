# -*- coding: utf-8 -*-
"""D-373: extend complete-branch inner replay through XGPIO1.

Scratch only.  At D-367's selected U3/R58 layout, reserve XGPIO6/XGPIO7,
replace XGPIO5 on In3, XGPIO4 on In2, XGPIO2 on In3, and XGPIO3 on In3 using
the mechanisms proven by D-369 through D-372, then replace the complete
XGPIO1 branch with the same mechanism.  In2 and In3 are screened independently
for XGPIO1.  Remaining accepted U3 branches are restored exactly and attached
only after all five replacements close.  The authoritative PCB
is never edited.
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
import u3_xgpio2_inner_replay_073 as D371
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_xgpio1_inner_replay_075.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO1_INNER_REPLAY_075")
X1_LAYERS = ("I2", "I3")


def restore_except_replaced(pcb, allowed):
    wanted = collections.Counter({s: n for s, n in allowed.items()
                                  if s[1] not in ("/XGPIO1", "/XGPIO2", "/XGPIO3", "/XGPIO4", "/XGPIO5")})
    source, board = pcbnew.LoadBoard(IR.AUTH), pcbnew.LoadBoard(pcb)
    done = collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if done[s] < wanted[s]:
            board.Add(item.Duplicate()); done[s] += 1
    board.Save(pcb)
    return wanted, done


def route_inner(qb, group_name, inner):
    group = dict(IR.GROUPS[group_name])
    group["inner_long_haul_plan"] = dict(group["inner_long_haul_plan"])
    group["inner_long_haul_plan"]["inner"] = [inner]
    nf = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = IR.physical_net_pads(qb, nf)
    try:
        rec = IR.route_inner_long_haul_plan(qb, nf, pads, group)
        edges = [{"a": a["ref"], "b": b["ref"], "kind": kind,
                  "ok": bool(result.get("ok")), "reason": result.get("reason"),
                  "inner": layer, "via_xy": result.get("via_xy", [])}
                 for a, b, kind, result, layer in rec]
        return {"ok": bool(edges) and all(x["ok"] for x in edges), "edges": edges}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__ + ": " + str(exc)}


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = D362.copper(base)
    base_pairs = D362.connected_pairs(base); allowed, branches = D362.boundary(base)
    baseline, _ = RU.drc(IR.AUTH, "u3x1inner_base", SCRATCH)
    boundaries = {net: sum(n for s, n in allowed.items() if s[1] == net)
                  for net in ("/XGPIO1", "/XGPIO2", "/XGPIO3", "/XGPIO4", "/XGPIO5")}
    attempts = []
    for x1_inner in X1_LAYERS:
        pcb, removed = D367.prepare("x1_" + x1_inner.lower(), allowed, (0.0, -0.5))
        pair = D367.reserve_pair(pcb)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        pair_ok = len(pair) == 2 and all(x["ok"] for x in pair)
        x5 = D371.route_inner(qb, "XGPIO5_INNER", "I3") if pair_ok else {"ok": False, "error": "pair_not_reserved"}
        x4 = D371.route_inner(qb, "XGPIO4_INNER", "I2") if x5["ok"] else {"ok": False, "error": "xgpio5_not_closed"}
        x2 = (D371.route_inner(qb, "XGPIO2_INNER_PILOT", "I3") if x4["ok"]
              else {"ok": False, "error": "xgpio4_not_closed"})
        x3 = (route_inner(qb, "XGPIO3_INNER", "I3") if x2["ok"]
              else {"ok": False, "error": "xgpio2_not_closed"})
        x1 = (route_inner(qb, "XGPIO1_INNER", x1_inner) if x3["ok"]
              else {"ok": False, "error": "xgpio3_not_closed"})
        qb.save(pcb)
        wanted = restored = collections.Counter(); attachments = []
        if x1["ok"]:
            wanted, restored = restore_except_replaced(pcb, allowed)
            qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
            for net in D364.SCHEDULE[5:]:
                attachments.append(D364.attach_terminal(qb, net, branches[net]["u3_pad"],
                                                         branches[net]["width"]))
                if not attachments[-1]["ok"]: break
            if len(attachments) == len(D364.SCHEDULE)-5 and all(x["ok"] for x in attachments):
                attachments.append(D364.attach_terminal(qb, "/XGPIO7_HDR", "R58.2", 200000))
        IR.refill_planes(qb.b); qb.save(pcb)
        result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
        missing, added = base_cu-result_cu, result_cu-base_cu
        forbidden_missing = missing-allowed
        targets = set(branches) | {"/XGPIO6", "/XGPIO7", "/XGPIO7_HDR"}
        forbidden_added = [s for s in added.elements() if s[1] not in targets]
        broken = sorted(base_pairs-D362.connected_pairs(result))
        opens = {n: D363.open_edges(result, n) for n in sorted(targets)}
        drc, details = RU.drc(pcb, "u3x1inner_"+x1_inner.lower(), SCRATCH)
        worse = {k:[baseline.get(k,0), drc.get(k,0)] for k in sorted(set(baseline)|set(drc))
                 if k != "unconnected_items" and drc.get(k,0) > baseline.get(k,0)}
        closed = (removed == allowed and x5["ok"] and x4["ok"] and x2["ok"] and x3["ok"] and x1["ok"]
                  and restored == wanted and len(attachments) == len(D364.SCHEDULE)-4
                  and all(x["ok"] for x in attachments) and not forbidden_missing
                  and not forbidden_added and not broken and all(v == 0 for v in opens.values())
                  and not worse and drc.get("unconnected_items",0) <= baseline.get("unconnected_items",0))
        row = {"xgpio1_inner_layer": x1_inner, "xgpio3_inner_layer": "I3", "xgpio4_inner_layer": "I2",
               "xgpio5_inner_layer": "I3", "pair_routes": pair,
               "xgpio5_route": x5, "xgpio4_route": x4,
               "xgpio2_route": x2, "xgpio3_route": x3, "xgpio1_route": x1,
               "replaced_boundary_items": boundaries,
               "remaining_restored_items": sum(restored.values()),
               "terminal_attachments": attachments,
               "first_remaining_failure": next((x for x in attachments if not x["ok"]), None),
               "forbidden_missing_count": sum(forbidden_missing.values()),
               "forbidden_added_count": len(forbidden_added), "accepted_pairs_broken": broken,
               "open_edges_after": opens, "drc_after": dict(drc), "drc_worse": worse,
               # KiCad does not guarantee violation report order.  Sort the
               # human-readable details so identical geometry emits identical
               # durable evidence across reruns.
               "drc_worse_details": {k: sorted(details[k]) for k in worse},
               "closed_candidate": bool(closed)}
        attempts.append(row)
        print(x1_inner, "x5", x5["ok"], "x4", x4["ok"], "x2", x2["ok"], "x3", x3["ok"], "x1", x1["ok"],
              "attachments", len(attachments),
              "first", row["first_remaining_failure"] and row["first_remaining_failure"]["net"],
              "drc+", sum(v[1]-v[0] for v in worse.values()), "closed", closed)
    wins = [x for x in attempts if x["closed_candidate"]]
    ev = {"schema_version":1, "decision":"D-373", "source_decision":"D-372",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"complete_XGPIO5_In3_XGPIO4_In2_XGPIO2_In3_XGPIO3_In3_then_complete_XGPIO1_inner_branch_replacement",
          "selected_layout":{"u3_rotation_deg":180,"u3_offset_mm":[0.0,0.5],"r58_offset_mm":[0.0,-0.5]},
          "baseline_drc":dict(baseline), "attempts":attempts,
          "xgpio1_mechanism_wins":sum(1 for x in attempts if x["xgpio1_route"]["ok"]),
          "transaction_candidates":len(wins), "promotion_candidate":False,
          "conclusion":"closed_U3_transaction_candidate" if wins else "XGPIO1_inner_replacement_characterized"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"x1 wins",ev["xgpio1_mechanism_wins"],
          "transaction wins",len(wins),"auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
