# -*- coding: utf-8 -*-
"""D-375: bounded target-bias/via-site sweep for the XGPIO1 In3 join.

Scratch only.  Replays the D-373 prefix, varies the target used to score each
endpoint reservation, deduplicates identical physical via pairs, then tests a
direct join and a compact line-relative staged join set for every distinct
pair.  Authority is never edited.
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
import u3_xgpio2_inner_replay_073 as D371

OUT = os.path.join(SP, "u3_xgpio1_viasite_077.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO1_VIASITE_077")
# Target offsets are deliberately larger than the endpoint pocket: target is
# only a scoring bias, not copper or a required waypoint.
A_BIASES = ((0, 0), (-8, 0), (8, 0), (0, -8), (0, 8))
B_BIASES = ((0, 0), (-4, 0), (4, 0), (0, -4), (0, 4),
            (-8, 0), (8, 0), (0, -8), (0, 8))
STAGES = ((0.25, -8), (0.25, 4), (0.25, 8),
          (0.50, -12), (0.50, 4), (0.50, 8), (0.50, 12),
          (0.75, -8), (0.75, -4), (0.75, 4))


def biased(p, bias):
    return (p["x"] + int(bias[0] * 1e6), p["y"] + int(bias[1] * 1e6))


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    baseline, _ = RU.drc(IR.AUTH, "u3x1site_base", SCRATCH)
    allowed, _ = D362.boundary(pcbnew.LoadBoard(IR.AUTH))
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
    attempts, seen = [], {}
    prefix_ok = len(prefix_routes) == 4 and all(x["ok"] for x in prefix_routes)
    for ai, ab in enumerate(A_BIASES):
        for bi, bb in enumerate(B_BIASES):
            pcb = os.path.join(SCRATCH, "site_%02d_%02d.kicad_pcb" % (ai, bi))
            shutil.copy2(prefix, pcb)
            trial = QR.QBoard(pcb); IR.inject_existing_via_obstacles(trial)
            ra = rb = {"ok": False, "reason": "PREFIX_FAILED"}
            if prefix_ok:
                ra = QR.reserve_escape(trial, net, pa, w, cp, ct, near="F", far="I3",
                                       via_dia=vd, via_drill=vk, target=biased(pb, ab))
                if ra.get("ok"):
                    rb = QR.reserve_escape(trial, net, pb, w, cp, ct, near="B", far="I3",
                                           via_dia=vd, via_drill=vk, target=biased(pa, bb))
            key = (tuple(ra.get("via", ())), tuple(rb.get("via", ())))
            row = {"a_bias_mm": list(ab), "b_bias_mm": list(bb),
                   "a_reservation": ra, "b_reservation": rb,
                   "duplicate_of": seen.get(key), "joins": [], "route_win": False}
            if ra.get("ok") and rb.get("ok") and key not in seen:
                seen[key] = [ai, bi]
                mark = trial.mark()
                direct = QR.join_reserved(trial, net, ra["via"], rb["via"], w, cp, ct, layer="I3")
                row["joins"].append({"kind": "direct", "result": direct})
                if not direct.get("ok"):
                    trial.revert(mark)
                    for fraction, offset in STAGES:
                        mark = trial.mark()
                        wp = D374.point(ra["via"], rb["via"], fraction, offset)
                        staged = D374.join_staged(trial, net, ra["via"], rb["via"], wp, w, cp, ct)
                        row["joins"].append({"kind": "staged", "fraction": fraction,
                                             "offset_mm": offset,
                                             "waypoint_mm": [round(wp[0]/1e6, 3), round(wp[1]/1e6, 3)],
                                             "result": staged})
                        if staged.get("ok"): break
                        trial.revert(mark)
                row["route_win"] = any(x["result"].get("ok") for x in row["joins"])
                if row["route_win"]: trial.save(pcb)
            attempts.append(row)
            print(ai, bi, ra.get("reason"), rb.get("reason"), key,
                  "duplicate", row["duplicate_of"], "win", row["route_win"])

    wins = [x for x in attempts if x["route_win"]]
    ev = {"schema_version": 1, "decision": "D-375", "source_decision": "D-374",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest() == auth_sha,
          "method": "XGPIO1_In3_biased_endpoint_reservation_distinct_viasite_pair_sweep",
          "selected_layout": {"u3_rotation_deg":180,"u3_offset_mm":[0.0,0.5],
                              "r58_offset_mm":[0.0,-0.5]},
          "baseline_drc": dict(baseline), "removed_boundary_exact": removed == allowed,
          "pair_routes": pair, "prefix_routes": prefix_routes,
          "bias_attempts": len(attempts), "distinct_via_pairs": len(seen),
          "route_wins": len(wins), "attempts": attempts,
          "promotion_candidate": False,
          "conclusion": "XGPIO1_distinct_viasite_route_found_needs_transaction_gate" if wins
                        else "XGPIO1_target_bias_viasite_sweep_characterized"}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "distinct", len(seen), "wins", len(wins),
          "auth unchanged", ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
