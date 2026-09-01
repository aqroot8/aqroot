# -*- coding: utf-8 -*-
"""D-389: fresh replay of the two dominant U3 collision branches.

Scratch only. Rebuild D-386, withdraw the complete ACC_POWER_FAULT_N and
ACC_DETECT_N branches, then replay both from their physical pads in both
orders. Exact duplicate vias are removed before a full zone refill and the
same-basename real KiCad DRC comparison.
"""
import collections, hashlib, json, os, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_acc_en_inner_replay_088 as D386
import u3_collision_branch_withdrawal_090 as D388
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_collision_branch_replay_091.json")
SCRATCH = os.path.join(SP, "w", "U3_COLLISION_BRANCH_REPLAY_091")
NETS = ("/ACC_POWER_FAULT_N", "/ACC_DETECT_N")


def route_group(qb, name):
    group = IR.GROUPS[name]
    net = IR.resolve_nets(qb, group)[name]
    pads = IR.physical_net_pads(qb, net)
    pads.sort(key=lambda p: (p["ref"], p["x"], p["y"]))
    rows = []
    for i, j in IR.mst_edges(pads):
        a, b = pads[i], pads[j]
        layer, kind = IR.edge_plan(a, b, group)
        if kind == "same":
            r = QR.connect_role(qb, net, a, b, layer, group["width"],
                                group["clr_pad"], group["clr_trk"])
        else:
            r = IR.connect_cross(qb, net, a, b, group)
        rows.append({"a": a["ref"], "b": b["ref"], "kind": kind,
                     "layer": layer, "ok": bool(r.get("ok")),
                     "reason": r.get("reason"), "via_xy": r.get("via_xy")})
        if not r.get("ok"):
            break
    return {"ok": bool(rows) and all(x["ok"] for x in rows), "edges": rows}


def dedup_vias(board):
    seen, removed = set(), []
    for item in list(board.GetTracks()):
        if item.GetClass() != "PCB_VIA":
            continue
        p = item.GetPosition()
        sig = (item.GetNetname(), p.x, p.y, item.GetWidth(pcbnew.F_Cu),
               item.GetDrill(), int(item.GetViaType()))
        if sig in seen:
            removed.append(sig)
            board.Remove(item)
        else:
            seen.add(sig)
    return removed


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    env = dict(os.environ); env["PYTHONHASHSEED"] = "0"
    # D386 regenerates its tracked historical evidence as a side effect. Keep
    # that evidence byte-stable: this characterization only needs its scratch
    # winner PCB, not a rewrite of the earlier decision record.
    prior_blob = open(D386.OUT, "rb").read()
    try:
        subprocess.run([sys.executable, D386.__file__], env=env, check=True)
        prior = json.load(open(D386.OUT, encoding="utf-8"))
    finally:
        with open(D386.OUT, "wb") as f:
            f.write(prior_blob)
    winner = next(x for x in prior["attempts"]
                  if x["inner"] == "I3" and x["acc_3v3_en"].get("ok"))
    base = D388.raw_drc(IR.AUTH, "baseline_drc")
    seed = RU.fresh(SCRATCH, "withdrawn_seed")
    removed = D388.withdraw(winner["candidate_pcb"], seed, set(NETS))

    attempts = []
    for order in (("ACC_POWER_FAULT_N", "ACC_DETECT_N"),
                  ("ACC_DETECT_N", "ACC_POWER_FAULT_N")):
        pcb = RU.fresh(SCRATCH, "then_".join(x.lower() for x in order))
        shutil.copy2(seed, pcb)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        routes = []
        for name in order:
            rec = route_group(qb, name); routes.append({"group": name, **rec})
            if not rec["ok"]: break
        qb.save(pcb)
        board = pcbnew.LoadBoard(pcb)
        duplicates = dedup_vias(board)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.Save(pcb)
        assessment = D388.assess(pcb, "_then_".join(x.lower() for x in order), base)
        opens = {n: D363.open_edges(board, n) for n in NETS}
        attempts.append({"order": list(order), "routes": routes,
                         "duplicate_vias_removed": len(duplicates),
                         "open_edges": opens, **assessment})
        print(order, "routes", [x["ok"] for x in routes], "opens", opens,
              "collisions", assessment["added_collision_count"])

    complete = [x for x in attempts if len(x["routes"]) == 2
                and all(r["ok"] for r in x["routes"])
                and all(v == 0 for v in x["open_edges"].values())]
    clean = [x for x in complete if not x["added_counts"]]
    ev = {"schema_version": 1, "decision": "D-389",
          "source_decisions": ["D-386", "D-388"],
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "complete_branch_withdrawal_then_fresh_MST_replay_order_screen",
          "withdrawn_items": removed, "attempts": attempts,
          "complete_replays": len(complete), "drc_clean_replays": len(clean),
          "promotion_candidate": False,
          "conclusion": ("FRESH_REPLAY_DRC_CLEAN" if clean else
                         "FRESH_REPLAY_COMPLETE_WITH_RESIDUALS" if complete else
                         "FRESH_REPLAY_BLOCKED")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "complete", len(complete), "clean", len(clean),
          "auth", ev["authoritative_unchanged"])


if __name__ == "__main__":
    main()
