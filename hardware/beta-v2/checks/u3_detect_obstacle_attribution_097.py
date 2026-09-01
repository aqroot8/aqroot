# -*- coding: utf-8 -*-
"""D-395: complete the fault suffix, then attribute the U3.17 detect wall.

Scratch only. Reconstruct the D-393 XGPIO0/In2 plus U3.18/In3 winner, attach
TP33.1 to TP27.1 using D-394's shortest complete suffix, replay the proven
ACC_DETECT_N prefix, and measure ordinary-through-via reachability after
bounded U3.17-neighborhood obstacle withdrawals. The authoritative PCB is
never edited.
"""
import hashlib, json, os, re, shutil, subprocess, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import qrouter as QR
import u3_p18_xgpio_via_relocation_095 as D393
import u3_collision_branch_viasite_enum_092 as D390
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_detect_obstacle_attribution_097.json")
SCRATCH = os.path.join(SP, "w", "U3_DETECT_OBSTACLE_ATTRIBUTION_097")
RADIUS = 3_000_000
RANKS = range(4)
SEPARATION = 500000
FAULT = "/ACC_POWER_FAULT_N"
DETECT = "/ACC_DETECT_N"


def blockers(records):
    out = {}
    for rec in records:
        why = rec.get("why", "")
        for tag, count in re.findall(r"([^,;]+?) \(x(\d+)\)", why.split("blocked by ")[-1]):
            out[tag.strip()] = max(out.get(tag.strip(), 0), int(count))
    return out


def complete_fault(path):
    qb = QR.QBoard(path); IR.inject_existing_via_obstacles(qb)
    group = IR.GROUPS["ACC_POWER_FAULT_N"]
    net = IR.resolve_nets(qb, group)["ACC_POWER_FAULT_N"]
    pads = {p["ref"]: p for p in IR.physical_net_pads(qb, net)}
    rec = QR.connect_role(qb, net, pads["TP33.1"], pads["TP27.1"], "B",
                          group["width"], group["clr_pad"], group["clr_trk"])
    qb.save(path)
    opens = D363.open_edges(pcbnew.LoadBoard(path), FAULT)
    return rec, opens


def remove_local(source, target, remove_vias=False, remove_tracks=False):
    shutil.copy2(source, target)
    board = pcbnew.LoadBoard(target)
    pad = next(p for p in board.FindFootprintByReference("U3").Pads()
               if p.GetNumber() == "17")
    origin = pad.GetPosition(); removed = []
    for item in list(board.GetTracks()):
        if item.GetNetname() == DETECT:
            continue
        is_via = item.GetClass() == "PCB_VIA"
        points = ([item.GetPosition()] if is_via else
                  [item.GetStart(), item.GetEnd()])
        local = min((p.x-origin.x)**2 + (p.y-origin.y)**2 for p in points) <= RADIUS**2
        selected = local and ((is_via and remove_vias) or
                              (not is_via and remove_tracks))
        if selected:
            pos = item.GetPosition() if is_via else item.GetStart()
            removed.append({"class": item.GetClass(), "net": item.GetNetname(),
                            "position_mm": [pos.x/1e6, pos.y/1e6]})
            board.Remove(item)
    board.Save(target)
    return removed


def probe(path):
    qb = QR.QBoard(path); IR.inject_existing_via_obstacles(qb)
    net, pads, prefix = D390.replay_prefix(qb, "ACC_DETECT_N")
    qb.save(path)
    group = IR.GROUPS["ACC_DETECT_N"]
    isolated = []
    for inner in ("I2", "I3"):
        for endpoint, other in (("R129.2", "U3.17"), ("U3.17", "R129.2")):
            for rank in RANKS:
                trial = QR.QBoard(path); IR.inject_existing_via_obstacles(trial)
                rec = D390.reserve(trial, net, pads[endpoint], pads[other],
                                   inner, rank, group)
                isolated.append({"inner": inner, "endpoint": endpoint,
                                 "rank": rank, "reservation": rec})
    sites = {}
    for inner in ("I2", "I3"):
        for endpoint in ("R129.2", "U3.17"):
            vals = {tuple(x["reservation"].get("via", ())) for x in isolated
                    if x["inner"] == inner and x["endpoint"] == endpoint
                    and x["reservation"].get("ok")}
            sites[inner + ":" + endpoint] = [list(x) for x in sorted(vals)]
    reservations = [x["reservation"] for x in isolated]
    return {"prefix": prefix, "prefix_ok": all(x["ok"] for x in prefix),
            "endpoint_sites": sites, "obstacle_attribution": blockers(reservations),
            "isolated_attempts": isolated}


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    prior_blob = open(D393.OUT, "rb").read()
    env = dict(os.environ); env["PYTHONHASHSEED"] = "0"
    try:
        subprocess.run([sys.executable, D393.__file__], env=env, check=True)
        prior = json.load(open(D393.OUT, encoding="utf-8"))
    finally:
        with open(D393.OUT, "wb") as f: f.write(prior_blob)
    next(x for x in prior["attempts"] if x["xgpio"] == "XGPIO0"
         and x["xgpio_route"]["inner"] == "I2" and x["fault_route"].get("ok"))
    source = os.path.join(D393.SCRATCH, "xgpio0_i2_0_0.kicad_pcb")
    seed = os.path.join(SCRATCH, "complete_fault_seed.kicad_pcb")
    shutil.copy2(source, seed)
    suffix, fault_opens = complete_fault(seed)
    xgpio_opens = D363.open_edges(pcbnew.LoadBoard(seed), "/XGPIO0")
    cases = []
    for tag, vias, tracks in (("control", False, False),
                              ("local_vias", True, False),
                              ("local_tracks", False, True),
                              ("local_vias_and_tracks", True, True)):
        path = os.path.join(SCRATCH, tag + ".kicad_pcb")
        removed = remove_local(seed, path, vias, tracks)
        result = probe(path)
        cases.append({"case": tag, "remove_local_vias": vias,
                      "remove_local_tracks": tracks, "removed_items": removed,
                      **result})
        print(tag, result["endpoint_sites"], "removed", len(removed))
    control_sites = cases[0]["endpoint_sites"]
    changed = [x for x in cases[1:] if x["endpoint_sites"] != control_sites]
    ev = {"schema_version": 1, "decision": "D-395", "source_decisions": ["D-393", "D-394"],
          "authoritative_board_sha256": auth_sha,
          "authoritative_unchanged": hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest() == auth_sha,
          "method": "shortest_fault_suffix_replay_then_U3P17_local_obstacle_class_sensitivity",
          "radius_mm": RADIUS/1e6, "ranks_tested": list(RANKS),
          "site_separation_mm": SEPARATION/1e6,
          "fault_suffix": suffix, "fault_open_edges": fault_opens,
          "xgpio0_open_edges": xgpio_opens, "cases": cases,
          "site_changing_cases": [x["case"] for x in changed],
          "promotion_candidate": False,
          "conclusion": ("LOCAL_OBSTACLE_CLASS_CHANGES_DETECT_ENDPOINT_SITES"
                         if changed else "LOCAL_OBSTACLE_CLASS_DOES_NOT_CHANGE_DETECT_ENDPOINT_SITES")}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "fault", fault_opens,
          "auth", ev["authoritative_unchanged"])


if __name__ == "__main__": main()
