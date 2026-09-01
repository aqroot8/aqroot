# -*- coding: utf-8 -*-
"""D-365: broader U3/local-corridor refloorplan screen after exact cut-through.

D-359 screened only 0.5 mm pose changes with accepted incident copper present;
D-362 cut through that copper at only the D-360 seed.  This scratch-only screen
combines the exact 211-item incident boundary with materially larger 1.0/1.5 mm
orthogonal translations.  It reserves XGPIO6/XGPIO7 in both orders while all
unrelated copper stays frozen.  Branch replay is intentionally deferred until
a pose can reserve both routes.
"""
import hashlib, json, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362

OUT = os.path.join(SP, "u3_corridor_refloor_067.json")
SCRATCH = os.path.join(SP, "w", "U3_CORRIDOR_REFLOOR_067")
OFFSETS = tuple((dx, dy) for radius in (1.0, 1.5)
                for dx, dy in ((-radius, 0), (radius, 0), (0, -radius),
                               (0, radius), (-radius, -radius),
                               (-radius, radius), (radius, -radius),
                               (radius, radius)))
CANDIDATES = tuple((angle, dx, dy) for angle in (90, 180, 270)
                   for dx, dy in OFFSETS)
ORDERS = D362.ORDERS


def project_copy(tag):
    D362.SCRATCH = SCRATCH
    return D362.project_copy(tag)


def prepare(pcb, allowed, pose):
    board = pcbnew.LoadBoard(pcb); removed = D362.collections.Counter()
    for item in list(board.GetTracks()):
        signature = D362.sig(item)
        if removed[signature] < allowed[signature]:
            removed[signature] += 1
            board.RemoveNative(item)
    u3 = board.FindFootprintByReference("U3"); p = u3.GetPosition()
    angle, dx, dy = pose
    u3.SetOrientationDegrees(u3.GetOrientationDegrees() + angle)
    u3.SetPosition(pcbnew.VECTOR2I(p.x + round(dx * 1e6),
                                  p.y + round(dy * 1e6)))
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
    # Connectivity includes one zero-length synthetic pad item per routed U3
    # branch.  Those 12 signatures are not physical GetTracks() copper (D-364
    # likewise found 199 unique restorable items from the nominal 211-item
    # connectivity boundary), so transact only the physical intersection.
    allowed = boundary & base_cu
    rows = []
    for angle, dx, dy in CANDIDATES:
        pose = (angle, dx, dy)
        tag = "r%d_x%+d_y%+d" % (angle, round(dx*1000), round(dy*1000))
        attempts = []
        exact_removal = True
        frozen_ok = True
        for oi, order in enumerate(ORDERS):
            pcb = project_copy(tag + "_o%d" % oi)
            removed = prepare(pcb, allowed, pose)
            exact_removal &= removed == allowed
            attempts.append(route_order(pcb, order))
            result_cu = D362.copper(pcbnew.LoadBoard(pcb))
            missing = base_cu - result_cu
            frozen_ok &= not bool(missing - allowed)
        pair_ok = any(x["ok"] for x in attempts)
        rows.append({"rotation_deg": angle, "offset_mm": [dx, dy],
                     "exact_boundary_removed": exact_removal,
                     "unrelated_copper_preserved": frozen_ok,
                     "routing_orders": attempts, "pair_route_candidate": pair_ok})
        reasons = [[r.get("error") or
                    next((e.get("reason") for e in r.get("edges", [])
                          if not e.get("ok")), None) or "OK"
                    for r in a["routes"]] for a in attempts]
        print(tag, "pair", pair_ok, "reasons", reasons)
    wins = [x for x in rows if x["pair_route_candidate"]]
    ev = {"schema_version": 1, "decision": "D-365", "source_decision": "D-364",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "exact_incident_cutthrough_plus_1p0_1p5mm_orthogonal_pose_screen",
          "excluded_prior_space": "D359_0p5mm_pose_space_and_D360_D364_180deg_north_0p5mm",
          "nominal_connectivity_boundary_items": sum(boundary.values()),
          "physical_boundary_items": sum(allowed.values()),
          "branch_count": len(branches),
          "candidate_count": len(rows), "candidates": rows,
          "pair_route_candidates": len(wins),
          "winning_poses": [{"rotation_deg": x["rotation_deg"],
                             "offset_mm": x["offset_mm"]} for x in wins],
          "frozen_signature_failures": sum(not x["unrelated_copper_preserved"] for x in rows),
          "frozen_signature_note": ("Scratch routing may split accepted track signatures; "
                                    "this diagnostic is a candidate filter, not a promotion gate."),
          "conclusion": ("broader_refloorplan_has_pair_reservation_candidates"
                         if wins else "broader_1p0_1p5mm_U3_pose_space_exhausted")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "wins", len(wins),
          "auth unchanged", ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
