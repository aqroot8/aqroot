# -*- coding: utf-8 -*-
"""D-394: attribute D-393's remaining ACC_POWER_FAULT_N component.

Scratch only. Reconstruct D-393, prove the joined U3.18 candidate's exact pad
components, then screen direct B.Cu attachment of the isolated pad to every
pad in the joined component. The authoritative PCB is never edited.
"""
import hashlib, json, os, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import qrouter as QR
import u3_p18_xgpio_via_relocation_095 as D393
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_fault_component_attribution_096.json")
SCRATCH = os.path.join(SP, "w", "U3_FAULT_COMPONENT_ATTRIBUTION_096")
NET = "/ACC_POWER_FAULT_N"


def pref(pad):
    return "%s.%s" % (pad.GetParentFootprint().GetReference(), pad.GetNumber())


def components(board):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    pads = [p for f in board.GetFootprints() for p in f.Pads()
            if p.GetNetname() == NET]
    unseen = {(pref(p), p.GetPosition().x, p.GetPosition().y): p for p in pads}
    result = []
    while unseen:
        key, pad = next(iter(sorted(unseen.items())))
        reached = {(pref(q), q.GetPosition().x, q.GetPosition().y)
                   for q in cc.GetConnectedItems(pad) if q.GetClass() == "PAD"}
        reached.add(key)
        result.append(sorted(k[0] for k in reached))
        for k in reached:
            unseen.pop(k, None)
    return sorted(result, key=lambda x: (len(x), x))


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    prior_blob = open(D393.OUT, "rb").read()
    env = dict(os.environ); env["PYTHONHASHSEED"] = "0"
    try:
        subprocess.run([sys.executable, D393.__file__], env=env, check=True)
        prior = json.load(open(D393.OUT, encoding="utf-8"))
    finally:
        with open(D393.OUT, "wb") as f:
            f.write(prior_blob)
    winner = next(x for x in prior["attempts"]
                  if x["xgpio"] == "XGPIO0" and x["xgpio_route"]["inner"] == "I2"
                  and x["fault_route"].get("ok"))
    source = os.path.join(D393.SCRATCH, "xgpio0_i2_0_0.kicad_pcb")
    before = components(pcbnew.LoadBoard(source))
    joined = next(x for x in before if "U3.18" in x)
    isolated = next(x for x in before if len(x) == 1)
    group = IR.GROUPS["ACC_POWER_FAULT_N"]
    attempts = []
    for target in joined:
        pcb = os.path.join(SCRATCH, "tp33_to_%s.kicad_pcb" % target.replace(".", "_"))
        shutil.copy2(source, pcb)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        net = IR.resolve_nets(qb, group)["ACC_POWER_FAULT_N"]
        pads = {p["ref"]: p for p in IR.physical_net_pads(qb, net)}
        rec = QR.connect_role(qb, net, pads[isolated[0]], pads[target], "B",
                              group["width"], group["clr_pad"], group["clr_trk"])
        qb.save(pcb)
        after = components(pcbnew.LoadBoard(pcb))
        attempts.append({"from": isolated[0], "to": target, "route": rec,
                         "open_edges": D363.open_edges(pcbnew.LoadBoard(pcb), NET),
                         "components": after})
    wins = [x for x in attempts if x["route"].get("ok") and x["open_edges"] == 0]
    ev = {"schema_version": 1, "decision": "D-394", "source_decision": "D-393",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "joined_fault_component_attribution_then_isolated_pad_direct_attach_screen",
          "d393_fault_join_ok": bool(winner["fault_route"].get("ok")),
          "components_after_d393": before, "joined_component": joined,
          "isolated_component": isolated, "direct_bcu_attempts": attempts,
          "complete_direct_attachments": len(wins), "promotion_candidate": False,
          "conclusion": ("TP33_DIRECT_ATTACHMENT_CLOSES_FAULT_NEEDS_TRANSACTION_REPLAY"
                         if wins else "U3P18_JOIN_IS_CONNECTED_TP33_REMAINS_ISOLATED_DIRECT_BCU_BLOCKED")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "components", before,
          "wins", len(wins), "auth", ev["authoritative_unchanged"])


if __name__ == "__main__":
    main()
