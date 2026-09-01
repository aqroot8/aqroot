# -*- coding: utf-8 -*-
"""D-363: reserve XGPIO6 then replay the complete U3 incident boundary.

Scratch only.  This is the single-variable successor to D-362: XGPIO7 remains
deferred, while the proven XGPIO6 In2 reservation is made before deterministic
replay of all routed branches incident on U3.  Unrelated copper is immutable.
"""
import hashlib, json, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362

OUT = os.path.join(SP, "u3_xgpio6_replay_065.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO6_REPLAY_065")


def open_edges(board, net):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    pads = [p for f in board.GetFootprints() for p in f.Pads()
            if p.GetNetname() == net]
    seen = set(); components = 0
    for p in pads:
        key = (D362.pref(p), p.GetPosition().x, p.GetPosition().y)
        if key in seen:
            continue
        components += 1
        reached = {(D362.pref(q), q.GetPosition().x, q.GetPosition().y)
                   for q in cc.GetConnectedItems(p) if q.GetClass() == "PAD"}
        seen |= reached | {key}
    return max(0, components - 1)


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    # D-362's copy helper deliberately owns its scratch root; redirect it for
    # this independent, reconstructible experiment.
    D362.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH)
    base_cu = D362.copper(base); base_pairs = D362.connected_pairs(base)
    allowed, branches = D362.boundary(base)
    base_drc, _ = RU.drc(IR.AUTH, "u3x6_base", SCRATCH)

    pcb = D362.project_copy("candidate")
    removed = D362.prepare(pcb, allowed)
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    xgpio6 = D362.route_inner(qb, "XGPIO6_INNER")
    replay = []
    if xgpio6["ok"]:
        for net, meta in sorted(branches.items(), key=lambda x: (x[1]["items"], x[0])):
            replay.append(D362.replay_branch(qb, net, meta))
            if not replay[-1]["ok"]:
                break
    IR.refill_planes(qb.b); qb.save(pcb)

    result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
    missing, added = base_cu - result_cu, result_cu - base_cu
    forbidden_missing = missing - allowed
    target_nets = set(branches) | {"/XGPIO6"}
    forbidden_added = [s for s in added.elements() if s[1] not in target_nets]
    broken = sorted(base_pairs - D362.connected_pairs(result))
    opens = {n: open_edges(result, n) for n in sorted(target_nets)}
    drc, _ = RU.drc(pcb, "u3x6_candidate", SCRATCH)
    worse = {k: [base_drc.get(k, 0), drc.get(k, 0)]
             for k in sorted(set(base_drc) | set(drc))
             if k != "unconnected_items" and drc.get(k, 0) > base_drc.get(k, 0)}
    closed = (removed == allowed and xgpio6["ok"]
              and len(replay) == len(branches) and all(x["ok"] for x in replay)
              and not forbidden_missing and not forbidden_added and not broken
              and all(v == 0 for v in opens.values()) and not worse
              and drc.get("unconnected_items", 0) <= base_drc.get("unconnected_items", 0))
    first_failure = next((x for x in replay if not x["ok"]), None)
    ev = {
        "schema_version": 1, "decision": "D-363", "source_decision": "D-362",
        "authoritative_board_sha256": auth_sha,
        "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
        "pose": {"rotation_deg": D362.POSE[0], "offset_mm": list(D362.POSE[1:])},
        "replacement_boundary": "complete_connectivity_components_incident_on_U3",
        "boundary_items": sum(allowed.values()), "branch_count": len(branches),
        "removed_items": sum(removed.values()), "xgpio6_route": xgpio6,
        "branch_replay": replay, "first_replay_failure": first_failure,
        "missing_items_total": sum(missing.values()),
        "added_items_total": sum(added.values()),
        "forbidden_missing_count": sum(forbidden_missing.values()),
        "forbidden_added_count": len(forbidden_added),
        "accepted_pairs_broken": broken, "open_edges_after": opens,
        "drc_before": dict(base_drc), "drc_after": dict(drc), "drc_worse": worse,
        "transaction_candidate": bool(closed), "promotion_candidate": False,
        "promotion_blocker": ("replacement_aware_authoritative_full_board_gate_not_yet_executed"
                              if closed else "complete_incident_branch_replay_not_closed"),
        "conclusion": ("closed_XGPIO6_U3_transaction_candidate" if closed
                       else "XGPIO6_reservation_or_U3_branch_replay_failed")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print(json.dumps(ev, indent=2, sort_keys=True))
    return 0 if closed else 1


if __name__ == "__main__":
    sys.exit(main())
