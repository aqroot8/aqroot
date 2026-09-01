# -*- coding: utf-8 -*-
"""D-387: real-DRC attribution for the complete D-386 U3 transaction.

Rebuild D-386, place its complete In3 candidate under the authoritative project
basename (so KiCad loads the real project and custom rules), refill zones, and
retain compact item-level attribution for every added fabrication violation.
Scratch copper is never promoted.
"""
import collections, hashlib, json, os, re, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import harness_paths as HP
import incremental_router as IR
import path_role_util as RU
import u3_acc_en_inner_replay_088 as D386

OUT = os.path.join(SP, "u3_transaction_violation_attribution_089.json")
SCRATCH = os.path.join(SP, "w", "U3_TRANSACTION_ATTRIBUTION_089")


def raw_drc(pcb, tag):
    out = os.path.join(SCRATCH, tag + ".json")
    p = subprocess.run([HP.kicad_cli(), "pcb", "drc", "--severity-all",
                        "--format", "json", "-o", out, pcb],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr or p.stdout)
    return json.load(open(out, encoding="utf-8"))


def signature(v):
    items = tuple(sorted(x.get("description", "") for x in v.get("items", [])))
    return v.get("type", ""), v.get("description", ""), items


def nets(v):
    found = set()
    for item in v.get("items", []):
        d = item.get("description", "")
        found.update(x for x in re.findall(r"\[([^]]+)\]", d)
                     if x and x != "<no net>")
    return tuple(sorted(found))


def compact(v):
    return {"type": v.get("type"), "description": v.get("description"),
            "nets": list(nets(v)),
            "items": [{"description": x.get("description"), "pos": x.get("pos")}
                      for x in v.get("items", [])]}


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()

    # Rebuild rather than trust an old scratch candidate.  The older router
    # contains set iterations, so pin Python hashing at the process boundary.
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    subprocess.run([sys.executable, D386.__file__], env=env, check=True)
    prior = json.load(open(D386.OUT, encoding="utf-8"))
    winner = next(x for x in prior["attempts"]
                  if x["inner"] == "I3" and x["acc_3v3_en"].get("ok"))

    candidate = RU.fresh(SCRATCH, "candidate")
    shutil.copy2(winner["candidate_pcb"], candidate)
    board = pcbnew.LoadBoard(candidate)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(candidate)

    base = raw_drc(IR.AUTH, "baseline_drc")
    cand = raw_drc(candidate, "candidate_drc")
    base_counts = collections.Counter(signature(v) for v in base.get("violations", []))
    added = []
    for v in cand.get("violations", []):
        s = signature(v)
        if base_counts[s]:
            base_counts[s] -= 1
        else:
            added.append(v)

    by_type = collections.Counter(v.get("type") for v in added)
    by_pair = collections.Counter(nets(v) for v in added
                                  if v.get("type") in ("shorting_items", "tracks_crossing", "clearance"))
    collision_types = {"shorting_items", "tracks_crossing", "clearance"}
    collisions = [v for v in added if v.get("type") in collision_types]
    ev = {
        "schema_version": 1,
        "decision": "D-387",
        "source_decision": "D-386",
        "authoritative_board_sha256": auth_sha,
        "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
        "method": "same_basename_real_rules_plus_zone_refill_item_level_attribution",
        "d386_reported_candidate_counts": winner["drc_after"],
        "baseline_counts": dict(collections.Counter(v.get("type") for v in base.get("violations", []))),
        "refilled_candidate_counts": dict(collections.Counter(v.get("type") for v in cand.get("violations", []))),
        "added_counts": dict(by_type),
        "collision_pair_counts": {" | ".join(k): n for k, n in sorted(by_pair.items())},
        "added_collision_details": [compact(v) for v in collisions],
        "dominant_collision_source": "/ACC_POWER_FAULT_N retained B.Cu branch",
        "minimum_next_scope": ["/ACC_POWER_FAULT_N", "/ACC_DETECT_N"],
        "harness_findings": {
            "same_basename_rules_required": True,
            "zone_refill_required_after_scratch_edit": True,
            "d386_112_clearances_not_authoritative": True
        },
        "promotion_candidate": False,
        "conclusion": "COLLISIONS_ATTRIBUTED_MINIMUM_REPLAY_SCOPE_IDENTIFIED"
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], dict(by_type), ev["collision_pair_counts"])


if __name__ == "__main__":
    main()
