# -*- coding: utf-8 -*-
"""D-391: bounded U3.18 endpoint-neighborhood obstacle attribution.

Scratch only. Rebuild the D-386 ordered transaction, withdraw the two known
collision branches, replay the proven ACC_POWER_FAULT_N local prefix, then
remove only classified nearby copper/vias to determine the minimum obstacle
class that can expose an ordinary U3.18 through-via escape. The authoritative
PCB is never edited.
"""
import hashlib, json, os, re, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_acc_en_inner_replay_088 as D386
import u3_collision_branch_viasite_enum_092 as D390
import u3_collision_branch_withdrawal_090 as D388

OUT = os.path.join(SP, "u3_p18_obstacle_attribution_093.json")
SCRATCH = os.path.join(SP, "w", "U3_P18_OBSTACLE_ATTRIBUTION_093")
ADJACENT = ("/ACC_5V_BOOST_EN", "/SX1262_RXEN")
RADIUS = 3_000_000


def blockers(attempts):
    out = {}
    for a in attempts:
        why = a["reservation"].get("why", "")
        for tag, count in re.findall(r"([^,;]+?) \(x(\d+)\)", why.split("blocked by ")[-1]):
            out[tag.strip()] = max(out.get(tag.strip(), 0), int(count))
    return out


def remove_classified(source, target, remove_nets=(), remove_local_vias=False):
    shutil.copy2(source, target)
    b = pcbnew.LoadBoard(target)
    p = next(x for x in b.FindFootprintByReference("U3").Pads() if x.GetNumber() == "18")
    pp = p.GetPosition(); removed = []
    for item in list(b.GetTracks()):
        net = item.GetNetname()
        is_via = item.GetClass() == "PCB_VIA"
        pos = item.GetPosition() if is_via else None
        local_via = is_via and ((pos.x-pp.x)**2 + (pos.y-pp.y)**2 <= RADIUS**2)
        if net in remove_nets or (remove_local_vias and local_via):
            removed.append({"class": item.GetClass(), "net": net,
                            "position_mm": ([pos.x/1e6, pos.y/1e6] if pos else None)})
            b.Remove(item)
    b.Save(target)
    return removed


def probe(path):
    qb = QR.QBoard(path); IR.inject_existing_via_obstacles(qb)
    net, pads, prefix = D390.replay_prefix(qb, "ACC_POWER_FAULT_N")
    qb.save(path)
    attempts = []; sites = {}
    group = IR.GROUPS["ACC_POWER_FAULT_N"]
    for inner in ("I2", "I3"):
        vals = set()
        for rank in range(4):
            trial = QR.QBoard(path); IR.inject_existing_via_obstacles(trial)
            rec = D390.reserve(trial, net, pads["U3.18"], pads["TP27.1"], inner, rank, group)
            attempts.append({"inner": inner, "rank": rank, "reservation": rec})
            if rec.get("ok"): vals.add(tuple(rec["via"]))
        sites[inner] = [list(x) for x in sorted(vals)]
    return prefix, attempts, sites


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
    winner = next(x for x in prior["attempts"] if x["inner"] == "I3" and x["acc_3v3_en"].get("ok"))
    seed = os.path.join(SCRATCH, "withdrawn_seed.kicad_pcb")
    D388.withdraw(winner["candidate_pcb"], seed,
                  {"/ACC_POWER_FAULT_N", "/ACC_DETECT_N"})
    cases = [
        ("control", (), False),
        ("adjacent_boost", (ADJACENT[0],), False),
        ("adjacent_rxen", (ADJACENT[1],), False),
        ("both_adjacent", ADJACENT, False),
        ("local_vias", (), True),
        ("both_adjacent_and_local_vias", ADJACENT, True),
    ]
    rows = []
    for tag, nets, vias in cases:
        path = os.path.join(SCRATCH, tag + ".kicad_pcb")
        removed = remove_classified(seed, path, nets, vias)
        prefix, attempts, sites = probe(path)
        rows.append({"case": tag, "removed_nets": list(nets),
                     "remove_local_vias": vias, "removed_items": removed,
                     "prefix_ok": all(x["ok"] for x in prefix),
                     "sites": sites, "obstacle_attribution": blockers(attempts),
                     "attempts": attempts})
        print(tag, sites, blockers(attempts), "removed", len(removed))
    wins = [x for x in rows if any(x["sites"].values())]
    ev = {"schema_version": 1, "decision": "D-391", "source_decision": "D-390",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "U3P18_nearby_adjacent_branch_and_local_via_withdrawal_sensitivity",
          "radius_mm": RADIUS/1e6, "cases": rows, "site_exposing_cases": len(wins),
          "promotion_candidate": False,
          "conclusion": ("MINIMUM_OBSTACLE_CLASS_EXPOSES_U3P18_SITE" if wins else
                         "ADJACENT_BRANCH_AND_LOCAL_VIA_WITHDRAWAL_DOES_NOT_EXPOSE_U3P18")}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "auth", ev["authoritative_unchanged"])


if __name__ == "__main__": main()
