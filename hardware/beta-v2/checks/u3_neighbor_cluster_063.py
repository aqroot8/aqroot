# -*- coding: utf-8 -*-
"""D-361: bounded non-rigid U3/C5/TP33 cluster screen.

Hold U3 at D-360's least-impact 180-degree/+0.5 mm north seed and move only
the two footprint-envelope neighbors through small outward offsets.  Route the
coherent XGPIO6/XGPIO7 pair in both deterministic orders, record complete
accepted pad-pair casualties and real KiCad DRC, and never edit authority.
"""
import hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u3_neighbor_cluster_063.json")
SCRATCH = os.path.join(SP, "w", "U3_NEIGHBOR_CLUSTER_063")
U3_POSE = (180, 0.0, 0.5)
C5_OFFSETS = ((0, 0), (.5, 0), (1, 0), (0, -.5), (0, -1))
TP33_OFFSETS = ((0, 0), (.5, 0), (1, 0), (0, -.5), (0, -1), (0, .5))
ORDERS = (("XGPIO6_INNER", "XGPIO7_INNER"),
          ("XGPIO7_INNER", "XGPIO6_INNER"))

def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()

def accepted_pairs(board, refs):
    board.BuildConnectivity(); cc = board.GetConnectivity(); out = set()
    for ref in refs:
        fp = board.FindFootprintByReference(ref)
        for p in fp.Pads():
            for q in cc.GetConnectedItems(p):
                if q.GetClass() == "PAD" and q.GetParentFootprint() != fp:
                    out.add(tuple(sorted((pad_ref(p), pad_ref(q)))))
    return out

def project_copy(tag):
    d = os.path.join(SCRATCH, tag)
    if os.path.exists(d): shutil.rmtree(d)
    os.makedirs(d); pcb = os.path.join(d, RU.PCBNAME)
    shutil.copyfile(IR.AUTH, pcb); stem = os.path.splitext(RU.PCBNAME)[0]
    for name in (stem+".kicad_dru", stem+".kicad_pro", "fp-lib-table", "sym-lib-table"):
        src = os.path.join(RU.AUTH_DIR, name)
        if os.path.exists(src): shutil.copyfile(src, os.path.join(d, name))
    libs = os.path.join(RU.AUTH_DIR, "libraries")
    if os.path.isdir(libs): os.symlink(libs, os.path.join(d, "libraries"), target_is_directory=True)
    return pcb

def move(fp, dx, dy):
    p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x+round(dx*1e6), p.y+round(dy*1e6)))

def pose(pcb, c5off, tpoff):
    b = pcbnew.LoadBoard(pcb); u = b.FindFootprintByReference("U3")
    u.SetOrientationDegrees(u.GetOrientationDegrees()+U3_POSE[0])
    move(u, U3_POSE[1], U3_POSE[2])
    move(b.FindFootprintByReference("C5"), *c5off)
    move(b.FindFootprintByReference("TP33"), *tpoff)
    b.Save(pcb)

def route_order(pcb, order):
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb); rows = []
    for name in order:
        group = IR.GROUPS[name]; nf = IR.resolve_nets(qb, group)[group["nets"][0]]
        pads = IR.physical_net_pads(qb, nf)
        try:
            rec = IR.route_inner_long_haul_plan(qb, nf, pads, group)
            edges = [{"a":x[0]["ref"], "b":x[1]["ref"], "kind":x[2],
                      "ok":bool(x[3].get("ok")), "reason":x[3].get("reason"),
                      "inner":x[4]} for x in rec]
            rows.append({"group":name, "ok":bool(edges) and all(x["ok"] for x in edges),
                         "edges":edges})
        except Exception as e:
            rows.append({"group":name, "ok":False,
                         "error":type(e).__name__+": "+str(e)})
        if not rows[-1]["ok"]: break
    qb.save(pcb)
    return {"order":list(order), "ok":len(rows)==2 and all(x["ok"] for x in rows),
            "routes":rows}

def main():
    os.makedirs(SCRATCH, exist_ok=True)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); refs = ("U3", "C5", "TP33")
    pairs = accepted_pairs(base, refs)
    base_drc, _ = RU.drc(IR.AUTH, "u3cluster_base", SCRATCH); rows = []
    for c5 in C5_OFFSETS:
        for tp in TP33_OFFSETS:
            tag = "c%+d_%+d_t%+d_%+d" % tuple(round(v*1000) for v in c5+tp)
            posed = project_copy(tag); pose(posed, c5, tp)
            broken = sorted(pairs-accepted_pairs(pcbnew.LoadBoard(posed), refs))
            attempts = []
            for n, order in enumerate(ORDERS):
                trial = project_copy(tag+"_o%d"%n); pose(trial, c5, tp)
                attempts.append(route_order(trial, order))
            dc, _ = RU.drc(posed, "u3cluster_"+tag, SCRATCH)
            delta = {k:dc.get(k,0)-base_drc.get(k,0) for k in sorted(set(dc)|set(base_drc))
                     if dc.get(k,0) != base_drc.get(k,0)}
            win = any(x["ok"] for x in attempts)
            rows.append({"c5_offset_mm":list(c5), "tp33_offset_mm":list(tp),
                         "broken_accepted_pairs":broken, "broken_count":len(broken),
                         "routing_orders":attempts, "placement_drc":dict(dc),
                         "drc_delta":delta, "pair_route_candidate":win})
            print(tag, "pair", win, "broken", len(broken), "delta", delta)
    wins = [x for x in rows if x["pair_route_candidate"]]
    ev = {"schema_version":1, "decision":"D-361", "source_decision":"D-360",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "u3_pose":{"rotation_deg":U3_POSE[0], "offset_mm":list(U3_POSE[1:])},
          "moved_footprints":["U3","C5","TP33"], "baseline_drc":dict(base_drc),
          "baseline_cluster_accepted_pairs":sorted(pairs), "candidates":rows,
          "pair_route_candidates":len(wins),
          "conclusion":"cluster_candidate_requires_complete_branch_replay" if wins
                       else "bounded_U3_C5_TP33_cluster_space_exhausted"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"wins",len(wins),"auth unchanged",ev["authoritative_unchanged"])

if __name__ == "__main__": main()
