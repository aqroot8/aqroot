# -*- coding: utf-8 -*-
"""D-367: rank D-366 winners and attempt exact affected-branch replay.

Scratch only.  The three pair-reserving endpoint-cluster layouts are ranked by
real KiCad DRC and accepted pad-pair impact.  The best layout is then replayed
with the exact accepted U3 templates and deterministic terminal attachments.
The R58 header-side accepted connection is explicitly included in the impact
and closure checks.  The authoritative PCB is never edited.
"""
import collections, hashlib, json, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_topology_replay_066 as D364
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_r58_impact_replay_069.json")
SCRATCH = os.path.join(SP, "w", "U3_R58_IMPACT_REPLAY_069")
WINNERS = ((0.5, 0.0), (0.0, -0.5), (0.0, -1.0))
ORDER = ("XGPIO6_INNER", "XGPIO7_INNER")


def prepare(tag, allowed, offset):
    D362.SCRATCH = SCRATCH
    pcb = D362.project_copy(tag)
    removed = D362.prepare(pcb, allowed)
    board = pcbnew.LoadBoard(pcb)
    fp = board.FindFootprintByReference("R58"); p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x + round(offset[0] * 1e6),
                                  p.y + round(offset[1] * 1e6)))
    board.Save(pcb)
    return pcb, removed


def reserve_pair(pcb):
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb); routes = []
    for name in ORDER:
        routes.append(D362.route_inner(qb, name))
        if not routes[-1]["ok"]: break
    IR.refill_planes(qb.b); qb.save(pcb)
    return routes


def drc_delta(pcb, tag, baseline):
    counts, details = RU.drc(pcb, tag, SCRATCH)
    worse = {k: [baseline.get(k, 0), counts.get(k, 0)]
             for k in sorted(set(baseline) | set(counts))
             if k != "unconnected_items" and counts.get(k, 0) > baseline.get(k, 0)}
    return dict(counts), worse, {k: details[k] for k in worse}


def attach(qb, net, padref, width):
    return D364.attach_terminal(qb, net, padref, width)


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = D362.copper(base)
    base_pairs = D362.connected_pairs(base)
    boundary, branches = D362.boundary(base)
    allowed = boundary & base_cu
    baseline_drc, _ = RU.drc(IR.AUTH, "u3r58_base", SCRATCH)
    ranked = []
    for i, off in enumerate(WINNERS):
        pcb, removed = prepare("rank_%d" % i, allowed, off)
        routes = reserve_pair(pcb)
        result = pcbnew.LoadBoard(pcb)
        broken = sorted(base_pairs - D362.connected_pairs(result))
        counts, worse, details = drc_delta(pcb, "u3r58_rank_%d" % i, baseline_drc)
        row = {"r58_offset_mm": list(off), "pair_routes": routes,
               "exact_u3_boundary_removed": removed == allowed,
               "accepted_pairs_broken": broken,
               "accepted_pairs_broken_count": len(broken),
               "drc_after": counts, "drc_worse": worse,
               "drc_worse_details": details,
               "non_unconnected_drc_increase": sum(v[1] - v[0] for v in worse.values())}
        ranked.append(row)
        print("rank", off, "broken", len(broken), "drc+", row["non_unconnected_drc_increase"])
    ranked.sort(key=lambda r: (r["non_unconnected_drc_increase"],
                               r["accepted_pairs_broken_count"],
                               abs(r["r58_offset_mm"][0]) + abs(r["r58_offset_mm"][1]),
                               r["r58_offset_mm"]))
    best = ranked[0]

    pcb, removed = prepare("replay_best", allowed, tuple(best["r58_offset_mm"]))
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb); routes = []
    for name in ORDER:
        routes.append(D362.route_inner(qb, name))
        if not routes[-1]["ok"]: break
    qb.save(pcb)
    restored = collections.Counter(); attachments = []
    if len(routes) == 2 and all(x["ok"] for x in routes):
        restored = D364.restore_templates(pcb, allowed)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        for net in D364.SCHEDULE:
            attachments.append(attach(qb, net, branches[net]["u3_pad"], branches[net]["width"]))
            if not attachments[-1]["ok"]: break
        # R58.2 is the accepted header-side terminal that moves with R58.
        if len(attachments) == len(D364.SCHEDULE) and all(x["ok"] for x in attachments):
            attachments.append(attach(qb, "/XGPIO7_HDR", "R58.2", 200000))
    IR.refill_planes(qb.b); qb.save(pcb)
    result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
    missing, added = base_cu - result_cu, result_cu - base_cu
    forbidden_missing = missing - allowed
    target_nets = set(branches) | {"/XGPIO6", "/XGPIO7", "/XGPIO7_HDR"}
    forbidden_added = [s for s in added.elements() if s[1] not in target_nets]
    broken = sorted(base_pairs - D362.connected_pairs(result))
    opens = {n: D363.open_edges(result, n) for n in sorted(target_nets)}
    counts, worse, details = drc_delta(pcb, "u3r58_replay", baseline_drc)
    closed = (removed == allowed and restored == allowed and len(routes) == 2
              and all(x["ok"] for x in routes) and len(attachments) == len(D364.SCHEDULE) + 1
              and all(x["ok"] for x in attachments) and not forbidden_missing
              and not forbidden_added and not broken and all(v == 0 for v in opens.values())
              and not worse and counts.get("unconnected_items", 0) <= baseline_drc.get("unconnected_items", 0))
    replay = {"selected_r58_offset_mm": best["r58_offset_mm"], "pair_routes": routes,
              "removed_items": sum(removed.values()), "restored_items": sum(restored.values()),
              "terminal_attachments": attachments,
              "first_attachment_failure": next((x for x in attachments if not x["ok"]), None),
              "missing_items_total": sum(missing.values()), "added_items_total": sum(added.values()),
              "forbidden_missing_count": sum(forbidden_missing.values()),
              "forbidden_added_count": len(forbidden_added), "accepted_pairs_broken": broken,
              "open_edges_after": opens, "drc_after": counts, "drc_worse": worse,
              "drc_worse_details": details, "transaction_candidate": bool(closed)}
    ev = {"schema_version": 1, "decision": "D-367", "source_decision": "D-366",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "real_DRC_accepted_pair_rank_then_exact_U3_template_and_R58_header_replay",
          "baseline_drc": dict(baseline_drc), "ranked_candidates": ranked,
          "least_impact_candidate": best, "replay": replay,
          "promotion_candidate": False,
          "promotion_blocker": ("replacement_aware_authoritative_full_board_gate_not_yet_executed"
                                if closed else "complete_affected_branch_replay_not_closed"),
          "conclusion": ("closed_U3_R58_transaction_candidate" if closed
                         else "ranked_D366_winners_replay_failed")}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "best", best["r58_offset_mm"],
          "auth unchanged", ev["authoritative_unchanged"])
    return 0 if closed else 1


if __name__ == "__main__": sys.exit(main())
