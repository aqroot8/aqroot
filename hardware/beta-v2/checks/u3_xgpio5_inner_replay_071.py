# -*- coding: utf-8 -*-
"""D-369: replace the complete XGPIO5 branch with a fresh inner haul.

Scratch only.  At D-367's selected U3/R58 layout, reserve XGPIO6/XGPIO7,
replace the complete two-terminal XGPIO5 branch with the qualified D-331
native-face/inner-haul mechanism, then restore and attach every remaining U3
incident branch.  In2 and In3 are screened independently so a fallback cannot
hide which layer owns the result.  The authoritative PCB is never edited.
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
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_xgpio5_inner_replay_071.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO5_INNER_REPLAY_071")
LAYERS = ("I2", "I3")


def restore_except_xgpio5(pcb, allowed):
    wanted = collections.Counter({s: n for s, n in allowed.items()
                                  if s[1] != "/XGPIO5"})
    source, board = pcbnew.LoadBoard(IR.AUTH), pcbnew.LoadBoard(pcb)
    done = collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if done[s] < wanted[s]:
            board.Add(item.Duplicate()); done[s] += 1
    board.Save(pcb)
    return wanted, done


def route_xgpio5(qb, inner):
    group = dict(IR.GROUPS["XGPIO5_INNER"])
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
    baseline, _ = RU.drc(IR.AUTH, "u3x5inner_base", SCRATCH)
    x5_boundary = collections.Counter({s: n for s, n in allowed.items()
                                       if s[1] == "/XGPIO5"})
    attempts = []
    for inner in LAYERS:
        pcb, removed = D367.prepare("inner_" + inner.lower(), allowed, (0.0, -0.5))
        pair = D367.reserve_pair(pcb)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        x5 = route_xgpio5(qb, inner) if len(pair) == 2 and all(x["ok"] for x in pair) else {"ok": False, "error": "pair_not_reserved"}
        qb.save(pcb)
        wanted = restored = collections.Counter(); attachments = []
        if x5["ok"]:
            wanted, restored = restore_except_xgpio5(pcb, allowed)
            qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
            for net in D364.SCHEDULE[1:]:
                attachments.append(D364.attach_terminal(qb, net, branches[net]["u3_pad"],
                                                         branches[net]["width"]))
                if not attachments[-1]["ok"]: break
            if len(attachments) == len(D364.SCHEDULE)-1 and all(x["ok"] for x in attachments):
                attachments.append(D364.attach_terminal(qb, "/XGPIO7_HDR", "R58.2", 200000))
        IR.refill_planes(qb.b); qb.save(pcb)
        result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
        missing, added = base_cu-result_cu, result_cu-base_cu
        forbidden_missing = missing-allowed
        targets = set(branches) | {"/XGPIO6", "/XGPIO7", "/XGPIO7_HDR"}
        forbidden_added = [s for s in added.elements() if s[1] not in targets]
        broken = sorted(base_pairs-D362.connected_pairs(result))
        opens = {n: D363.open_edges(result, n) for n in sorted(targets)}
        drc, details = RU.drc(pcb, "u3x5inner_"+inner.lower(), SCRATCH)
        worse = {k:[baseline.get(k,0), drc.get(k,0)] for k in sorted(set(baseline)|set(drc))
                 if k != "unconnected_items" and drc.get(k,0) > baseline.get(k,0)}
        closed = (removed == allowed and x5["ok"] and restored == wanted
                  and len(attachments) == len(D364.SCHEDULE)
                  and all(x["ok"] for x in attachments) and not forbidden_missing
                  and not forbidden_added and not broken and all(v == 0 for v in opens.values())
                  and not worse and drc.get("unconnected_items",0) <= baseline.get("unconnected_items",0))
        row = {"inner_layer": inner, "pair_routes": pair, "xgpio5_route": x5,
               "xgpio5_boundary_items": sum(x5_boundary.values()),
               "remaining_restored_items": sum(restored.values()),
               "terminal_attachments": attachments,
               "first_remaining_failure": next((x for x in attachments if not x["ok"]), None),
               "forbidden_missing_count": sum(forbidden_missing.values()),
               "forbidden_added_count": len(forbidden_added), "accepted_pairs_broken": broken,
               "open_edges_after": opens, "drc_after": dict(drc), "drc_worse": worse,
               "drc_worse_details": {k: details[k] for k in worse},
               "closed_candidate": bool(closed)}
        attempts.append(row)
        print(inner, "x5", x5["ok"], "attachments", len(attachments),
              "first", row["first_remaining_failure"] and row["first_remaining_failure"]["net"],
              "drc+", sum(v[1]-v[0] for v in worse.values()), "closed", closed)
    wins = [x for x in attempts if x["closed_candidate"]]
    ev = {"schema_version":1, "decision":"D-369", "source_decision":"D-368",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"complete_XGPIO5_branch_replacement_with_terminal_specific_inner_haul",
          "selected_layout":{"u3_rotation_deg":180,"u3_offset_mm":[0.0,0.5],"r58_offset_mm":[0.0,-0.5]},
          "baseline_drc":dict(baseline), "attempts":attempts,
          "xgpio5_mechanism_wins":sum(1 for x in attempts if x["xgpio5_route"]["ok"]),
          "transaction_candidates":len(wins), "promotion_candidate":False,
          "conclusion":"closed_U3_transaction_candidate" if wins else "XGPIO5_inner_replacement_characterized"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"x5 wins",ev["xgpio5_mechanism_wins"],
          "transaction wins",len(wins),"auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
