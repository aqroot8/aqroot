# -*- coding: utf-8 -*-
"""D-384: attribute U3.14 obstacles and screen minimum-scope R7 geometry.

Scratch only.  Rebuild the sole D-383 viable seven-route prefix, retain every
laid prefix item, and translate only adjacent R7 through a bounded local set.
For each pose, enumerate U3.14 sites on In2/In3, measure accepted pad-pair
casualties, and run real KiCad DRC.  The authoritative PCB is never edited.
"""
import hashlib, json, os, re, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import u3_cutthrough_064 as D362
import u3_r58_impact_replay_069 as D367
import u3_xgpio9_layer_permute_085 as D383

OUT = os.path.join(SP, "u3_xgpio9_r7_cluster_086.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO9_R7_CLUSTER_086")
OFFSETS = ((0.0, 0.0), (-0.25, 0.0), (-0.50, 0.0), (-0.75, 0.0),
           (-1.00, 0.0), (0.25, 0.0), (0.0, -0.25), (0.0, 0.25),
           (-0.50, -0.25), (-0.50, 0.25))


def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()


def accepted_pairs(board, ref):
    board.BuildConnectivity(); cc = board.GetConnectivity(); out = set()
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        for q in cc.GetConnectedItems(p):
            if q.GetClass() == "PAD" and q.GetParentFootprint() != fp:
                out.add(tuple(sorted((pad_ref(p), pad_ref(q)))))
    return out


def move_ref(path, ref, dx, dy):
    b = pcbnew.LoadBoard(path); fp = b.FindFootprintByReference(ref)
    p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x + round(dx * 1e6),
                                  p.y + round(dy * 1e6)))
    b.Save(path)


def blockers(attempts):
    counts = {}
    for a in attempts:
        why = a.get("reservation", {}).get("why", "")
        for tag, n in re.findall(r"([^,;]+?) \(x(\d+)\)", why.split("blocked by ")[-1]):
            counts[tag.strip()] = max(counts.get(tag.strip(), 0), int(n))
    return counts


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    baseline_drc, _ = RU.drc(IR.AUTH, "u3x9r7_base", SCRATCH)
    base = pcbnew.LoadBoard(IR.AUTH)
    boundary, _ = D362.boundary(base); allowed = boundary & D362.copper(base)
    seed, prefix = D383.build_prefix("seed", allowed, "I3", "I2")
    seed_pairs = accepted_pairs(pcbnew.LoadBoard(seed), "R7")
    rows = []
    for dx, dy in OFFSETS:
        tag = "r7_%+d_%+d" % (round(dx * 1000), round(dy * 1000))
        candidate_dir = os.path.join(SCRATCH, tag)
        os.makedirs(candidate_dir)
        path = os.path.join(candidate_dir, RU.PCBNAME)
        shutil.copyfile(seed, path)
        stem = os.path.splitext(RU.PCBNAME)[0]
        for name in (stem+".kicad_dru", stem+".kicad_pro",
                     "fp-lib-table", "sym-lib-table"):
            src = os.path.join(RU.AUTH_DIR, name)
            if os.path.exists(src): shutil.copyfile(src, os.path.join(candidate_dir, name))
        libs = os.path.join(RU.AUTH_DIR, "libraries")
        if os.path.isdir(libs):
            os.symlink(libs, os.path.join(candidate_dir, "libraries"),
                       target_is_directory=True)
        if dx or dy: move_ref(path, "R7", dx, dy)
        attempts, sites = D383.probe_sites(path, prefix["ok"])
        moved = pcbnew.LoadBoard(path)
        broken = sorted(seed_pairs - accepted_pairs(moved, "R7"))
        drc, _ = RU.drc(path, "u3x9r7_" + tag, SCRATCH)
        worse = {k:[baseline_drc.get(k,0), drc.get(k,0)]
                 for k in sorted(set(baseline_drc)|set(drc))
                 if k != "unconnected_items" and drc.get(k,0)>baseline_drc.get(k,0)}
        rows.append({"r7_offset_mm":[dx,dy], "u3_14_sites":sites,
                     "u3_14_attempts":attempts,
                     "obstacle_attribution":blockers(attempts),
                     "broken_accepted_pairs":broken,
                     "broken_accepted_pair_count":len(broken),
                     "drc":dict(drc), "drc_worse_than_authority":worse,
                     "exposes_site":any(sites.values())})
        print(tag, sites, "broken", len(broken), "worse", worse)
    wins = [x for x in rows if x["exposes_site"]]
    min_broken = min((x["broken_accepted_pair_count"] for x in wins), default=None)
    ev = {"schema_version":1, "decision":"D-384", "source_decision":"D-383",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"D383_prefix_R7_only_bounded_translation_then_U3P14_site_enumeration",
          "moved_footprints":["R7"], "offsets_tested_mm":[list(x) for x in OFFSETS],
          "baseline_drc":dict(baseline_drc), "prefix":prefix,
          "baseline_r7_accepted_pairs":sorted(seed_pairs), "candidates":rows,
          "site_exposing_candidates":len(wins),
          "minimum_broken_accepted_pairs_among_wins":min_broken,
          "promotion_candidate":False,
          "conclusion":("R7_only_geometry_exposes_U3P14_site_needs_complete_R7_XGPIO9_replay"
                        if wins else "R7_only_minimum_scope_geometry_closed")}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT", ev["conclusion"], "wins", len(wins), "min broken", min_broken,
          "auth unchanged", ev["authoritative_unchanged"])


if __name__ == "__main__": main()
