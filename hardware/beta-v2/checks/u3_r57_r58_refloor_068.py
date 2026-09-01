# -*- coding: utf-8 -*-
"""D-366: bounded U3/R57/R58 endpoint-cluster refloorplan screen.

Scratch only.  Hold U3 at the D-360 least-impact pose after withdrawing its
exact physical incident-copper boundary, then translate the two unrouted series
resistors on a small placement grid.  Reserve XGPIO6/XGPIO7 in both orders.
Unrelated copper is immutable; complete branch replay is deferred until the
cluster can reserve both routes.
"""
import hashlib, json, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362

OUT = os.path.join(SP, "u3_r57_r58_refloor_068.json")
SCRATCH = os.path.join(SP, "w", "U3_R57_R58_REFLOOR_068")
R57_OFFSETS = ((0, 0),)  # D-362/D-364 already prove this endpoint reserves.
R58_OFFSETS = ((0, 0), (-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5),
               (-1.0, 0), (1.0, 0), (0, -1.0), (0, 1.0))
ORDERS = D362.ORDERS


def project_copy(tag):
    D362.SCRATCH = SCRATCH
    return D362.project_copy(tag)


def move(fp, offset):
    p = fp.GetPosition(); dx, dy = offset
    fp.SetPosition(pcbnew.VECTOR2I(p.x + round(dx * 1e6),
                                  p.y + round(dy * 1e6)))


def prepare(pcb, allowed, r57off, r58off):
    removed = D362.prepare(pcb, allowed)
    board = pcbnew.LoadBoard(pcb)
    move(board.FindFootprintByReference("R57"), r57off)
    move(board.FindFootprintByReference("R58"), r58off)
    board.Save(pcb)
    return removed


def route_order(pcb, order):
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb); routes = []
    for name in order:
        routes.append(D362.route_inner(qb, name))
        if not routes[-1]["ok"]:
            break
    qb.save(pcb)
    return {"order": list(order), "routes": routes,
            "ok": len(routes) == 2 and all(x["ok"] for x in routes)}


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = D362.copper(base)
    boundary, branches = D362.boundary(base)
    # Connectivity includes synthetic zero-length pad items; transact only
    # signatures that correspond to physical tracks/vias on the board.
    allowed = boundary & base_cu
    rows = []
    for r57off in R57_OFFSETS:
        for r58off in R58_OFFSETS:
            tag = "r57_%+d_%+d_r58_%+d_%+d" % tuple(
                round(v * 1000) for v in r57off + r58off)
            attempts = []; exact = True; frozen = True
            for oi, order in enumerate(ORDERS):
                pcb = project_copy(tag + "_o%d" % oi)
                removed = prepare(pcb, allowed, r57off, r58off)
                exact &= removed == allowed
                attempts.append(route_order(pcb, order))
                missing = base_cu - D362.copper(pcbnew.LoadBoard(pcb))
                frozen &= not bool(missing - allowed)
            win = any(x["ok"] for x in attempts)
            rows.append({"r57_offset_mm": list(r57off),
                         "r58_offset_mm": list(r58off),
                         "exact_boundary_removed": exact,
                         "unrelated_copper_preserved": frozen,
                         "routing_orders": attempts,
                         "pair_route_candidate": win})
            reasons = [[r.get("error") or next(
                (e.get("reason") for e in r.get("edges", []) if not e.get("ok")),
                None) or "OK" for r in a["routes"]] for a in attempts]
            print(tag, "pair", win, "reasons", reasons)
    wins = [x for x in rows if x["pair_route_candidate"]]
    ev = {"schema_version": 1, "decision": "D-366", "source_decision": "D-365",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "exact_U3_incident_cutthrough_plus_bounded_R57_R58_translation_cluster",
          "u3_pose": {"rotation_deg": D362.POSE[0],
                      "offset_mm": list(D362.POSE[1:])},
          "r57_offset_grid_mm": [list(x) for x in R57_OFFSETS],
          "r58_offset_grid_mm": [list(x) for x in R58_OFFSETS],
          "nominal_connectivity_boundary_items": sum(boundary.values()),
          "physical_boundary_items": sum(allowed.values()),
          "branch_count": len(branches), "candidate_count": len(rows),
          "candidates": rows, "pair_route_candidates": len(wins),
          "winning_layouts": [{"r57_offset_mm": x["r57_offset_mm"],
                               "r58_offset_mm": x["r58_offset_mm"]} for x in wins],
          "frozen_signature_failures": sum(not x["unrelated_copper_preserved"] for x in rows),
          "conclusion": ("endpoint_cluster_has_pair_reservation_candidates"
                         if wins else "bounded_R57_R58_translation_cluster_exhausted")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "wins", len(wins),
          "auth unchanged", ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
