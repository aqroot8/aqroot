# -*- coding: utf-8 -*-
"""D-393: minimum-scope XGPIO0/XGPIO1 via relocation transaction screen.

Scratch only. Rebuild the complete D-386 transaction, withdraw the two
collision branches and exactly one complete XGPIO branch, enumerate distinct
ordinary-through-via replacements for that XGPIO branch, then replay both
ACC_POWER_FAULT_N and ACC_DETECT_N. The authoritative PCB is never edited.
"""
import hashlib, json, os, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import qrouter as QR
import u3_acc_en_inner_replay_088 as D386
import u3_collision_branch_withdrawal_090 as D388
import u3_collision_branch_replay_091 as D389
import u3_collision_branch_viasite_enum_092 as D390
import u3_p18_obstacle_attribution_093 as D391
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_p18_xgpio_via_relocation_095.json")
SCRATCH = os.path.join(SP, "w", "U3_P18_XGPIO_VIA_RELOCATION_095")
# D-392 asks for a minimum-scope branch comparison, not an exhaustive branch
# via-site rank sweep.  Use the deterministic nearest replacement on each
# inner layer; only the downstream fault endpoint needs the four-rank sweep.
XGPIO_RANKS = range(1)
FAULT_RANKS = range(4)
SEPARATION = 500000
SPECS = {
    "XGPIO0": ("XGPIO0_INNER", "R51.1", "U3.4"),
    "XGPIO1": ("XGPIO1_INNER", "R52.1", "U3.5"),
}


def route_ranked(qb, name, inner, arank, brank):
    group_name, a_ref, b_ref = SPECS[name]
    group = IR.GROUPS[group_name]
    net = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = {p["ref"]: p for p in IR.physical_net_pads(qb, net)}
    a, b = pads[a_ref], pads[b_ref]
    w, cp, ct = group["width"], group["clr_pad"], group["clr_trk"]
    vd, drill = group["via_dia"], group["via_drill"]
    ra = QR.reserve_escape(qb, net, a, w, cp, ct, near="F", far=inner,
        via_dia=vd, via_drill=drill, target=(b["x"], b["y"]),
        site_index=arank, site_separation=SEPARATION)
    rb = ({"ok": False, "reason": "A_FAILED"} if not ra.get("ok") else
        QR.reserve_escape(qb, net, b, w, cp, ct, near="B", far=inner,
            via_dia=vd, via_drill=drill, target=(a["x"], a["y"]),
            site_index=brank, site_separation=SEPARATION))
    join = ({"ok": False, "reason": "RESERVATION_FAILED"} if not rb.get("ok") else
        QR.join_reserved(qb, net, ra["via"], rb["via"], w, cp, ct, layer=inner))
    return {"ok": bool(ra.get("ok") and rb.get("ok") and join.get("ok")),
            "inner": inner, "a_rank": arank, "b_rank": brank,
            "a_reservation": ra, "b_reservation": rb, "join": join}


def route_fault(qb, seed_path):
    """Replay the proven local prefix and explicitly close TP27.1--U3.18."""
    net, pads, prefix = D390.replay_prefix(qb, "ACC_POWER_FAULT_N")
    group = IR.GROUPS["ACC_POWER_FAULT_N"]
    attempts = []
    if not all(x["ok"] for x in prefix):
        return ({"ok": False, "prefix": prefix, "attempts": attempts,
                 "reason": "PREFIX_FAILED"}, qb)
    qb.save(seed_path)
    for inner in ("I2", "I3"):
        for order in (("TP27.1", "U3.18"), ("U3.18", "TP27.1")):
            for r1 in FAULT_RANKS:
                for r2 in FAULT_RANKS:
                    trial = QR.QBoard(seed_path); IR.inject_existing_via_obstacles(trial)
                    first = D390.reserve(trial, net, pads[order[0]], pads[order[1]],
                                         inner, r1, group)
                    second = ({"ok": False, "reason": "FIRST_FAILED"} if not first.get("ok") else
                              D390.reserve(trial, net, pads[order[1]], pads[order[0]],
                                           inner, r2, group))
                    join = ({"ok": False, "reason": "RESERVATION_FAILED"} if not second.get("ok") else
                            QR.join_reserved(trial, net, first["via"], second["via"],
                                             group["width"], group["clr_pad"],
                                             group["clr_trk"], layer=inner))
                    rec = {"inner": inner, "order": list(order), "first_rank": r1,
                           "second_rank": r2, "first_reservation": first,
                           "second_reservation": second, "join": join}
                    attempts.append(rec)
                    if join.get("ok"):
                        return ({"ok": True, "prefix": prefix, "attempts": attempts,
                                 "winner": rec}, trial)
    return ({"ok": False, "prefix": prefix, "attempts": attempts,
             "reason": "NO_EXPLICIT_FAULT_JOIN"}, qb)


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    env = dict(os.environ); env["PYTHONHASHSEED"] = "0"
    prior_blob = open(D386.OUT, "rb").read()
    try:
        subprocess.run([sys.executable, D386.__file__], env=env, check=True)
        prior = json.load(open(D386.OUT, encoding="utf-8"))
    finally:
        with open(D386.OUT, "wb") as f: f.write(prior_blob)
    winner = next(x for x in prior["attempts"]
                  if x["inner"] == "I3" and x["acc_3v3_en"].get("ok"))
    attempts = []
    for name in ("XGPIO0", "XGPIO1"):
        seed = os.path.join(SCRATCH, name.lower() + "_withdrawn.kicad_pcb")
        removed = D388.withdraw(winner["candidate_pcb"], seed,
            {"/ACC_POWER_FAULT_N", "/ACC_DETECT_N", "/" + name})
        seen = set()
        for inner in ("I2", "I3"):
            for arank in XGPIO_RANKS:
                for brank in XGPIO_RANKS:
                    pcb = os.path.join(SCRATCH, "%s_%s_%d_%d.kicad_pcb" %
                                       (name.lower(), inner.lower(), arank, brank))
                    shutil.copy2(seed, pcb)
                    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
                    xroute = route_ranked(qb, name, inner, arank, brank)
                    key = (tuple(xroute["a_reservation"].get("via", ())),
                           tuple(xroute["b_reservation"].get("via", ())))
                    distinct = xroute["ok"] and key not in seen
                    if distinct: seen.add(key)
                    sites = {"I2": [], "I3": []}; prefix_ok = False
                    fault = {"ok": False, "reason": "XGPIO_NOT_DISTINCT"}
                    detect = {"ok": False, "reason": "FAULT_NOT_CLOSED"}
                    if distinct:
                        qb.save(pcb)
                        prefix, _, sites = D391.probe(pcb)
                        prefix_ok = all(x["ok"] for x in prefix)
                        if prefix_ok and any(sites.values()):
                            # D391's probe is read-only with respect to this QBoard.
                            fault, qb = route_fault(qb, pcb + ".faultseed.kicad_pcb")
                            if fault["ok"]:
                                detect = D389.route_group(qb, "ACC_DETECT_N")
                            qb.save(pcb)
                    else:
                        qb.save(pcb)
                    board = pcbnew.LoadBoard(pcb)
                    opens = {n: D363.open_edges(board, n) for n in
                             ("/" + name, "/ACC_POWER_FAULT_N", "/ACC_DETECT_N")}
                    exposes = prefix_ok and any(sites.values()) and opens["/" + name] == 0
                    complete_transaction = (exposes and fault.get("ok") and detect.get("ok")
                                            and all(v == 0 for v in opens.values()))
                    attempts.append({"xgpio": name, "removed": removed,
                        "xgpio_route": xroute, "distinct_pair": bool(distinct),
                        "fault_prefix_ok": prefix_ok, "u3p18_sites": sites,
                        "fault_route": fault, "detect_route": detect,
                        "open_edges": opens, "complete_xgpio_exposes_u3p18": bool(exposes),
                        "complete_fault_detect_transaction": bool(complete_transaction)})
                    print(name, inner, arank, brank, "x", xroute["ok"],
                          "distinct", distinct, "sites", sites, "exposes", exposes)
    complete = [x for x in attempts if x["complete_xgpio_exposes_u3p18"]]
    transactions = [x for x in attempts if x["complete_fault_detect_transaction"]]
    ev = {"schema_version": 1, "decision": "D-393", "source_decision": "D-392",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "single_complete_XGPIO_branch_relocation_then_fault_detect_transaction_replay",
          "xgpio_ranks_tested": list(XGPIO_RANKS),
          "fault_ranks_tested": list(FAULT_RANKS),
          "site_separation_mm": SEPARATION / 1e6,
          "attempts": attempts, "complete_xgpio_site_exposing_relocations": len(complete),
          "complete_fault_detect_transactions": len(transactions),
          "promotion_candidate": False,
          "conclusion": ("COMPLETE_FAULT_DETECT_TRANSACTION_FOUND_NEEDS_FULL_GATE" if transactions else
                         "COMPLETE_XGPIO_RELOCATION_EXPOSES_U3P18_BUT_TRANSACTION_BLOCKED" if complete else
                         "SINGLE_XGPIO_VIA_RELOCATION_DOES_NOT_EXPOSE_U3P18")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "winners", len(complete),
          "auth", ev["authoritative_unchanged"])


if __name__ == "__main__": main()
