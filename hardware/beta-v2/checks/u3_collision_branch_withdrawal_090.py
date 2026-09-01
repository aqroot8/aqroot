# -*- coding: utf-8 -*-
"""D-388: withdraw dominant retained branches from the D-386 transaction.

Scratch only.  Rebuild the proven complete D-386 In3 transaction, then remove
the complete accepted ACC_POWER_FAULT_N branch.  If ACC_DETECT_N still causes
collisions, also remove its complete branch in a second candidate.  Each board
uses the authoritative project basename, refilled zones, real KiCad DRC, and
exact baseline subtraction.
"""
import collections, hashlib, json, os, re, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import harness_paths as HP
import incremental_router as IR
import path_role_util as RU
import u3_acc_en_inner_replay_088 as D386

OUT = os.path.join(SP, "u3_collision_branch_withdrawal_090.json")
SCRATCH = os.path.join(SP, "w", "U3_COLLISION_BRANCH_WITHDRAWAL_090")
COLLISION_TYPES = {"shorting_items", "tracks_crossing", "clearance"}


def raw_drc(pcb, tag):
    out = os.path.join(SCRATCH, tag + ".json")
    p = subprocess.run([HP.kicad_cli(), "pcb", "drc", "--severity-all",
                        "--format", "json", "-o", out, pcb],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr or p.stdout)
    with open(out, encoding="utf-8") as f:
        return json.load(f)


def signature(v):
    items = tuple(sorted(x.get("description", "") for x in v.get("items", [])))
    return v.get("type", ""), v.get("description", ""), items


def nets(v):
    found = set()
    for item in v.get("items", []):
        found.update(x for x in re.findall(r"\[([^]]+)\]", item.get("description", ""))
                     if x and x != "<no net>")
    return tuple(sorted(found))


def added_violations(base, candidate):
    counts = collections.Counter(signature(v) for v in base.get("violations", []))
    added = []
    for v in candidate.get("violations", []):
        sig = signature(v)
        if counts[sig]:
            counts[sig] -= 1
        else:
            added.append(v)
    return added


def withdraw(source, target, net_names):
    result_path = target + ".withdraw.json"
    p = subprocess.run([sys.executable, __file__, "--withdraw", source, target,
                        result_path, *sorted(net_names)], capture_output=True, text=True)
    if p.returncode or not os.path.exists(target) or not os.path.exists(result_path):
        raise RuntimeError("withdraw helper failed: " + (p.stderr or p.stdout))
    with open(result_path, encoding="utf-8") as f:
        return json.load(f)


def withdraw_child(source, target, result_path, net_names):
    shutil.copy2(source, target)
    board = pcbnew.LoadBoard(target)
    removed = collections.Counter()
    wanted = set(net_names)
    for item in list(board.GetTracks()):
        name = item.GetNetname()
        if name in wanted:
            removed[(name, type(item).__name__)] += 1
            board.Remove(item)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(target)
    result = {" | ".join(k): n for k, n in sorted(removed.items())}
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True)
    print(json.dumps(result, sort_keys=True))


def assess(pcb, tag, base):
    raw = raw_drc(pcb, tag)
    added = added_violations(base, raw)
    collisions = [v for v in added if v.get("type") in COLLISION_TYPES]
    pairs = collections.Counter(nets(v) for v in collisions)
    return {
        "pcb": pcb,
        "drc_counts": dict(collections.Counter(v.get("type") for v in raw.get("violations", []))),
        "added_counts": dict(collections.Counter(v.get("type") for v in added)),
        "added_collision_count": len(collisions),
        "collision_pair_counts": {" | ".join(k): n for k, n in sorted(pairs.items())},
        "added_collision_types": dict(collections.Counter(v.get("type") for v in collisions)),
    }


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()

    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    subprocess.run([sys.executable, D386.__file__], env=env, check=True)
    prior = json.load(open(D386.OUT, encoding="utf-8"))
    winner = next(x for x in prior["attempts"]
                  if x["inner"] == "I3" and x["acc_3v3_en"].get("ok"))

    base = raw_drc(IR.AUTH, "baseline_drc")
    seed = RU.fresh(SCRATCH, "seed")
    shutil.copy2(winner["candidate_pcb"], seed)
    board = pcbnew.LoadBoard(seed)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(seed)
    seed_result = assess(seed, "seed_drc", base)

    fault = RU.fresh(SCRATCH, "fault_withdrawn")
    fault_removed = withdraw(seed, fault, {"/ACC_POWER_FAULT_N"})
    fault_result = assess(fault, "fault_withdrawn_drc", base)

    detect_pairs = {k: n for k, n in fault_result["collision_pair_counts"].items()
                    if "/ACC_DETECT_N" in k}
    both_result = None
    both_removed = {}
    if detect_pairs:
        both = RU.fresh(SCRATCH, "fault_detect_withdrawn")
        both_removed = withdraw(fault, both, {"/ACC_DETECT_N"})
        both_result = assess(both, "fault_detect_withdrawn_drc", base)

    final = both_result or fault_result
    ev = {
        "schema_version": 1,
        "decision": "D-388",
        "source_decisions": ["D-386", "D-387"],
        "authoritative_board_sha256": auth_sha,
        "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
        "method": "complete_retained_branch_withdrawal_same_basename_real_rules_zone_refill",
        "seed": seed_result,
        "fault_withdrawal": {"removed": fault_removed, **fault_result},
        "detect_collisions_remained_after_fault_withdrawal": detect_pairs,
        "fault_plus_detect_withdrawal": None if both_result is None else {"removed": both_removed, **both_result},
        "promotion_candidate": False,
        "conclusion": ("DOMINANT_RETAINED_BRANCH_COLLISIONS_REMOVED"
                       if final["added_collision_count"] < seed_result["added_collision_count"]
                       else "BRANCH_WITHDRAWAL_DID_NOT_REDUCE_COLLISIONS"),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "seed", seed_result["added_collision_count"],
          "fault", fault_result["added_collision_count"],
          "both", None if both_result is None else both_result["added_collision_count"],
          "auth", ev["authoritative_unchanged"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--withdraw":
        withdraw_child(sys.argv[2], sys.argv[3], sys.argv[4], set(sys.argv[5:]))
    else:
        main()
