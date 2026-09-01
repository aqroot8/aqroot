# -*- coding: utf-8 -*-
"""D-392: minimum-cardinality U3.18 blocking-via subset ranking.

Scratch only. Rebuild the D-391 withdrawn seed, identify the eight nearby
transaction vias deterministically, and test subsets in cardinality/lexical
order. Stop after the first cardinality that exposes a U3.18 site so the next
iteration can relocate/replay the smallest proven blocking set. The
authoritative PCB is never edited.
"""
import gc, hashlib, itertools, json, os, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import u3_acc_en_inner_replay_088 as D386
import u3_collision_branch_withdrawal_090 as D388
import u3_p18_obstacle_attribution_093 as D391

OUT = os.path.join(SP, "u3_p18_via_subset_rank_094.json")
SCRATCH = os.path.join(SP, "w", "U3_P18_VIA_SUBSET_RANK_094")
NETS = {"/ACC_POWER_FAULT_N", "/ACC_DETECT_N"}


def nearby_vias(path):
    b = pcbnew.LoadBoard(path)
    pad = next(x for x in b.FindFootprintByReference("U3").Pads()
               if x.GetNumber() == "18")
    pp = pad.GetPosition(); rows = []
    for item in b.GetTracks():
        if item.GetClass() != "PCB_VIA":
            continue
        pos = item.GetPosition()
        if (pos.x-pp.x)**2 + (pos.y-pp.y)**2 <= D391.RADIUS**2:
            rows.append({"net": item.GetNetname(), "x": pos.x, "y": pos.y,
                         "position_mm": [pos.x/1e6, pos.y/1e6]})
    out = sorted(rows, key=lambda x: (x["net"], x["x"], x["y"]))
    del item, pad, b
    gc.collect()
    return out


def remove_subset(source, target, subset):
    shutil.copy2(source, target)
    keys = {(x["net"], x["x"], x["y"]) for x in subset}
    b = pcbnew.LoadBoard(target); removed = []
    for item in list(b.GetTracks()):
        if item.GetClass() != "PCB_VIA":
            continue
        p = item.GetPosition(); key = (item.GetNetname(), p.x, p.y)
        if key in keys:
            removed.append(key); b.Remove(item)
    if len(removed) != len(keys):
        raise RuntimeError("subset via identity mismatch")
    b.Save(target)
    del item, b
    gc.collect()


def probe_isolated(path, result_path):
    prefix, attempts, sites = D391.probe(path)
    rec = {"prefix_ok": all(x["ok"] for x in prefix), "sites": sites,
           "obstacle_attribution": D391.blockers(attempts)}
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, sort_keys=True)


def remove_isolated(source, target, subset_path):
    """Perform the sole logical board-load phase in a fresh pcbnew process."""
    subset = json.load(open(subset_path, encoding="utf-8"))
    remove_subset(source, target, subset)


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
    seed = os.path.join(SCRATCH, "withdrawn_seed.kicad_pcb")
    D388.withdraw(winner["candidate_pcb"], seed, NETS)
    vias = nearby_vias(seed)
    if len(vias) != 8:
        raise RuntimeError("expected eight D-391 local vias, got %d" % len(vias))

    rows = []; winning_size = None
    for size in range(1, len(vias) + 1):
        for index, combo in enumerate(itertools.combinations(vias, size)):
            tag = "k%d_%03d" % (size, index)
            path = os.path.join(SCRATCH, tag + ".kicad_pcb")
            subset_path = os.path.join(SCRATCH, tag + "_subset.json")
            with open(subset_path, "w", encoding="utf-8") as f:
                json.dump(combo, f, sort_keys=True)
            result_path = os.path.join(SCRATCH, tag + ".json")
            subprocess.run([sys.executable, __file__, "--remove", seed, path,
                            subset_path], env=env, check=True)
            subprocess.run([sys.executable, __file__, "--probe", path, result_path],
                           env=env, check=True)
            rec = json.load(open(result_path, encoding="utf-8"))
            sites = rec["sites"]
            exposed = any(sites.values())
            rows.append({"case": tag, "cardinality": size,
                         "removed_vias": [{k: x[k] for k in ("net", "position_mm")}
                                          for x in combo],
                         "prefix_ok": rec["prefix_ok"],
                         "sites": sites,
                         "site_count": sum(len(x) for x in sites.values()),
                         "obstacle_attribution": rec["obstacle_attribution"],
                         "exposes_site": exposed})
            print(tag, [x["net"] for x in combo], sites)
        if any(x["exposes_site"] for x in rows if x["cardinality"] == size):
            winning_size = size
            break

    winners = [x for x in rows if x["exposes_site"]]
    ev = {"schema_version": 1, "decision": "D-392", "source_decision": "D-391",
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "minimum_cardinality_local_transaction_via_withdrawal_rank",
          "candidate_vias": [{k: x[k] for k in ("net", "position_mm")} for x in vias],
          "subsets_tested": len(rows), "minimum_exposing_cardinality": winning_size,
          "winning_subsets": winners, "cases": rows, "promotion_candidate": False,
          "conclusion": ("MINIMUM_BLOCKING_VIA_SUBSET_IDENTIFIED" if winners else
                         "NO_PROPER_BLOCKING_VIA_SUBSET_EXPOSES_U3P18")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "k", winning_size,
          "wins", len(winners), "auth", ev["authoritative_unchanged"])


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--probe":
        probe_isolated(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 5 and sys.argv[1] == "--remove":
        remove_isolated(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        main()
