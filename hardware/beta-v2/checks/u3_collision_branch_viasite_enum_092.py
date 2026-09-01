# -*- coding: utf-8 -*-
"""D-390: explicit via-site enumeration for the two blocked U3 branches.

Scratch only. Rebuild D-386, withdraw ACC_POWER_FAULT_N and ACC_DETECT_N,
replay each branch's already-proven local prefix, then enumerate ordinary
through-via sites at both endpoints of the remaining U3 edge. Test only
distinct reserved pairs on In2/In3. The authoritative PCB is never edited.
"""
import hashlib, json, os, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_acc_en_inner_replay_088 as D386
import u3_collision_branch_replay_091 as D389
import u3_collision_branch_withdrawal_090 as D388

OUT = os.path.join(SP, "u3_collision_branch_viasite_enum_092.json")
SCRATCH = os.path.join(SP, "w", "U3_COLLISION_BRANCH_VIASITE_ENUM_092")
RANKS = range(4)
SEPARATION = 500000
NETS = ("/ACC_POWER_FAULT_N", "/ACC_DETECT_N")
SPECS = {
    "ACC_POWER_FAULT_N": {
        "endpoints": ("TP27.1", "U3.18"),
        "prefix": (("R103.2", "U20.6", "same"),
                   ("U20.6", "TP27.1", "same"),
                   ("R103.2", "U22.6", "same")),
    },
    "ACC_DETECT_N": {
        "endpoints": ("R129.2", "U3.17"),
        "prefix": (("R129.2", "R64.1", "cross"),),
    },
}


def reserve(qb, net, pad, other, inner, rank, group):
    return QR.reserve_escape(
        qb, net, pad, group["width"], group["clr_pad"], group["clr_trk"],
        near="B", far=inner, via_dia=group.get("via_dia", 600000),
        via_drill=group.get("via_drill", 300000), target=(other["x"], other["y"]),
        site_index=rank, site_separation=SEPARATION)


def replay_prefix(qb, name):
    group = IR.GROUPS[name]
    net = IR.resolve_nets(qb, group)[name]
    pads = {p["ref"]: p for p in IR.physical_net_pads(qb, net)}
    rows = []
    for a, b, kind in SPECS[name]["prefix"]:
        if kind == "same":
            rec = QR.connect_role(qb, net, pads[a], pads[b], "B",
                                  group["width"], group["clr_pad"],
                                  group["clr_trk"])
        else:
            rec = IR.connect_cross(qb, net, pads[a], pads[b], group)
        rows.append({"a": a, "b": b, "kind": kind, "ok": bool(rec.get("ok")),
                     "reason": rec.get("reason"), "result": rec})
        if not rec.get("ok"):
            break
    return net, pads, rows


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    env = dict(os.environ); env["PYTHONHASHSEED"] = "0"
    prior_blob = open(D386.OUT, "rb").read()
    try:
        subprocess.run([sys.executable, D386.__file__], env=env, check=True)
        prior = json.load(open(D386.OUT, encoding="utf-8"))
    finally:
        with open(D386.OUT, "wb") as f:
            f.write(prior_blob)
    winner = next(x for x in prior["attempts"]
                  if x["inner"] == "I3" and x["acc_3v3_en"].get("ok"))
    withdrawn = RU.fresh(SCRATCH, "withdrawn_seed")
    removed = D388.withdraw(winner["candidate_pcb"], withdrawn, set(NETS))
    baseline, _ = RU.drc(IR.AUTH, "u3branch_enum_base", SCRATCH)

    branches = []
    for name in ("ACC_POWER_FAULT_N", "ACC_DETECT_N"):
        seed = RU.fresh(SCRATCH, name.lower() + "_prefix")
        shutil.copy2(withdrawn, seed)
        qb = QR.QBoard(seed); IR.inject_existing_via_obstacles(qb)
        net, pads, prefix = replay_prefix(qb, name)
        qb.save(seed)
        prefix_ok = len(prefix) == len(SPECS[name]["prefix"]) and all(x["ok"] for x in prefix)
        group = IR.GROUPS[name]
        ea, eb = SPECS[name]["endpoints"]
        isolated, attempts, distinct = [], [], set()

        for inner in ("I2", "I3"):
            for endpoint, other in ((ea, eb), (eb, ea)):
                for rank in RANKS:
                    trial = QR.QBoard(seed); IR.inject_existing_via_obstacles(trial)
                    rec = reserve(trial, net, pads[endpoint], pads[other], inner,
                                  rank, group) if prefix_ok else {"ok": False, "reason": "PREFIX_FAILED"}
                    isolated.append({"inner": inner, "endpoint": endpoint,
                                     "rank": rank, "reservation": rec})
            for order in ((ea, eb), (eb, ea)):
                for r1 in RANKS:
                    for r2 in RANKS:
                        trial = QR.QBoard(seed); IR.inject_existing_via_obstacles(trial)
                        first = reserve(trial, net, pads[order[0]], pads[order[1]],
                                        inner, r1, group) if prefix_ok else {"ok": False, "reason": "PREFIX_FAILED"}
                        second = {"ok": False, "reason": "FIRST_FAILED"}
                        if first.get("ok"):
                            second = reserve(trial, net, pads[order[1]], pads[order[0]],
                                             inner, r2, group)
                        sites = {order[0]: tuple(first.get("via", ())),
                                 order[1]: tuple(second.get("via", ()))}
                        key = (inner, sites[ea], sites[eb])
                        new = first.get("ok") and second.get("ok") and key not in distinct
                        join = {"ok": False, "reason": "RESERVATION_FAILED"}
                        if new:
                            distinct.add(key)
                            join = QR.join_reserved(trial, net, first["via"], second["via"],
                                group["width"], group["clr_pad"], group["clr_trk"], layer=inner)
                        attempts.append({"inner": inner, "order": list(order),
                            "first_rank": r1, "second_rank": r2,
                            "first_reservation": first, "second_reservation": second,
                            "distinct_pair": bool(new), "join": join})

        endpoint_sites = {}
        for inner in ("I2", "I3"):
            for endpoint in (ea, eb):
                vals = {tuple(x["reservation"].get("via", ())) for x in isolated
                        if x["inner"] == inner and x["endpoint"] == endpoint
                        and x["reservation"].get("ok")}
                endpoint_sites[inner + ":" + endpoint] = [list(x) for x in sorted(vals)]
        wins = [x for x in attempts if x["join"].get("ok")]
        drc, details = RU.drc(seed, "u3branch_enum_" + name.lower(), SCRATCH)
        worse = {k: [baseline.get(k, 0), drc.get(k, 0)]
                 for k in sorted(set(baseline) | set(drc))
                 if k != "unconnected_items" and drc.get(k, 0) > baseline.get(k, 0)}
        branches.append({"group": name, "endpoints": [ea, eb],
            "prefix_ok": prefix_ok, "prefix_routes": prefix,
            "endpoint_sites": endpoint_sites, "isolated_endpoint_attempts": isolated,
            "ordered_pair_attempt_count": len(attempts),
            "distinct_via_pairs": len(distinct), "route_wins": len(wins),
            "winning_attempts": wins, "attempts": attempts,
            "prefix_drc": dict(drc), "prefix_drc_worse": worse,
            "prefix_drc_worse_details": {k: sorted(details[k]) for k in worse}})
        print(name, "sites", endpoint_sites, "pairs", len(distinct), "wins", len(wins))

    any_wins = any(x["route_wins"] for x in branches)
    ev = {"schema_version": 1, "decision": "D-390",
          "source_decision": "D-389", "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "ordered_prefix_then_blocked_U3_edge_explicit_viasite_enumeration",
          "site_separation_mm": SEPARATION / 1e6, "ranks_tested": list(RANKS),
          "withdrawn_items": removed, "baseline_drc": dict(baseline),
          "branches": branches, "promotion_candidate": False,
          "conclusion": "DISTINCT_VIASITE_ROUTE_FOUND_NEEDS_TRANSACTION_REPLAY" if any_wins else
                        "ORDINARY_THROUGH_VIASITE_ENUMERATION_BLOCKED"}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "auth", ev["authoritative_unchanged"])


if __name__ == "__main__":
    main()
