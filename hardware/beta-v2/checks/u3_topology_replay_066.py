# -*- coding: utf-8 -*-
"""D-364: topology-aware U3 branch replay after reserving XGPIO6.

Scratch only.  Preserve each withdrawn branch's accepted copper topology by
restoring its exact template, then attach the moved U3 terminal to the nearest
same-net B.Cu anchor.  This deliberately retains inner hauls, vias and
multi-terminal trunks that a generic B.Cu MST discards.  Unrelated copper is
immutable.
"""
import collections, hashlib, json, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_topology_replay_066.json")
SCRATCH = os.path.join(SP, "w", "U3_TOPOLOGY_REPLAY_066")
SCHEDULE = ("/XGPIO5", "/XGPIO4", "/XGPIO2", "/XGPIO3", "/XGPIO1",
            "/XGPIO0", "/XGPIO8", "/XGPIO9", "/ACC_DETECT_N",
            "/ACC_3V3_EN", "/ACC_POWER_FAULT_N")


def restore_templates(pcb, allowed):
    source = pcbnew.LoadBoard(IR.AUTH)
    board = pcbnew.LoadBoard(pcb)
    restored = collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if restored[s] >= allowed[s]:
            continue
        board.Add(item.Duplicate())
        restored[s] += 1
    board.Save(pcb)
    return restored


def attach_terminal(qb, netname, padref, width):
    nf = netname if netname in qb.nets else None
    if nf is None:
        return {"net": netname, "ok": False, "error": "net_not_resolved"}
    pads = {p["ref"]: p for p in IR.physical_net_pads(qb, nf)}
    terminal = pads.get(padref)
    if terminal is None:
        return {"net": netname, "ok": False, "error": "terminal_not_resolved"}
    hit = RU.nearest_on_net(qb.b, netname, "B.Cu", terminal["x"], terminal["y"])
    if hit is None:
        return {"net": netname, "ok": False, "error": "no_BCu_template_anchor"}
    distance, x, y, track = hit
    RU.split_at(qb.b, track, x, y)
    anchor = RU.pseudo_pad(nf, x, y, QR)
    result = QR.connect_role(qb, nf, terminal, anchor, "B", width, 200000, 200000)
    return {"net": netname, "terminal": padref,
            "anchor_mm": [x / 1e6, y / 1e6], "anchor_distance_mm": distance / 1e6,
            "ok": bool(result.get("ok")), "reason": result.get("reason")}


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    D362.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH)
    base_cu = D362.copper(base); base_pairs = D362.connected_pairs(base)
    allowed, branches = D362.boundary(base)
    base_drc, _ = RU.drc(IR.AUTH, "u3topo_base", SCRATCH)

    pcb = D362.project_copy("candidate")
    removed = D362.prepare(pcb, allowed)
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    xgpio6 = D362.route_inner(qb, "XGPIO6_INNER")
    qb.save(pcb)

    restored = collections.Counter()
    attachments = []
    if xgpio6["ok"]:
        restored = restore_templates(pcb, allowed)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        for net in SCHEDULE:
            attachments.append(attach_terminal(qb, net, branches[net]["u3_pad"],
                                               branches[net]["width"]))
            if not attachments[-1]["ok"]:
                break
    IR.refill_planes(qb.b); qb.save(pcb)

    result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
    missing, added = base_cu - result_cu, result_cu - base_cu
    forbidden_missing = missing - allowed
    target_nets = set(branches) | {"/XGPIO6"}
    forbidden_added = [s for s in added.elements() if s[1] not in target_nets]
    broken = sorted(base_pairs - D362.connected_pairs(result))
    opens = {n: D363.open_edges(result, n) for n in sorted(target_nets)}
    drc, drc_details = RU.drc(pcb, "u3topo_candidate", SCRATCH)
    worse = {k: [base_drc.get(k, 0), drc.get(k, 0)]
             for k in sorted(set(base_drc) | set(drc))
             if k != "unconnected_items" and drc.get(k, 0) > base_drc.get(k, 0)}
    closed = (removed == allowed and restored == allowed and xgpio6["ok"]
              and len(attachments) == len(SCHEDULE) and all(x["ok"] for x in attachments)
              and not forbidden_missing and not forbidden_added and not broken
              and all(v == 0 for v in opens.values()) and not worse
              and drc.get("unconnected_items", 0) <= base_drc.get("unconnected_items", 0))
    ev = {
        "schema_version": 1, "decision": "D-364", "source_decision": "D-363",
        "authoritative_board_sha256": auth_sha,
        "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
        "pose": {"rotation_deg": D362.POSE[0], "offset_mm": list(D362.POSE[1:])},
        "method": "exact_accepted_template_restore_then_nearest_BCu_terminal_attach",
        "schedule": list(SCHEDULE), "boundary_items": sum(allowed.values()),
        "removed_items": sum(removed.values()), "restored_items": sum(restored.values()),
        "xgpio6_route": xgpio6, "terminal_attachments": attachments,
        "first_attachment_failure": next((x for x in attachments if not x["ok"]), None),
        "missing_items_total": sum(missing.values()), "added_items_total": sum(added.values()),
        "forbidden_missing_count": sum(forbidden_missing.values()),
        "forbidden_added_count": len(forbidden_added), "accepted_pairs_broken": broken,
        "open_edges_after": opens, "drc_before": dict(base_drc), "drc_after": dict(drc),
        "drc_worse": worse,
        "drc_worse_details": {k: drc_details[k] for k in worse},
        "transaction_candidate": bool(closed),
        "promotion_candidate": False,
        "promotion_blocker": ("replacement_aware_authoritative_full_board_gate_not_yet_executed"
                              if closed else "topology_aware_terminal_replay_not_closed"),
        "conclusion": ("closed_XGPIO6_U3_topology_transaction_candidate" if closed
                       else "topology_aware_U3_terminal_replay_failed")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print(json.dumps(ev, indent=2, sort_keys=True))
    return 0 if closed else 1


if __name__ == "__main__":
    sys.exit(main())
