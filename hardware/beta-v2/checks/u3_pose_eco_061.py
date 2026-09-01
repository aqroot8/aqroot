# -*- coding: utf-8 -*-
"""D-359: bounded scratch-only orthogonal U3 pose/refloorplan screen.

D-341 exhausted translations without changing U3's west-edge endpoint geometry.
This screen tries the materially different orthogonal rotations, with a small
cardinal translation set, and routes XGPIO6/XGPIO7 as one coherent transaction
in both orders.  It records accepted-copper casualties and real KiCad DRC; the
authoritative board is never edited and no candidate is promoted here.
"""
import hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u3_pose_eco_061.json")
SCRATCH = os.path.join(SP, "w", "U3_POSE_ECO_061")
CANDIDATES = [(a, dx, dy) for a in (90, 180, 270)
              for dx, dy in ((0, 0), (-.5, 0), (.5, 0), (0, -.5), (0, .5))]
ORDERS = (("XGPIO6_INNER", "XGPIO7_INNER"),
          ("XGPIO7_INNER", "XGPIO6_INNER"))

def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()

def connected_u3_pairs(board):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    u3 = board.FindFootprintByReference("U3"); out = set()
    for p in u3.Pads():
        for q in cc.GetConnectedItems(p):
            if q.GetClass() == "PAD" and q.GetParentFootprint() != u3:
                out.add(tuple(sorted((pad_ref(p), pad_ref(q)))))
    return out

def nearby(board, radius_mm=7.0):
    u3 = board.FindFootprintByReference("U3"); p = u3.GetPosition(); rows = []
    for f in board.GetFootprints():
        if f == u3: continue
        q = f.GetPosition(); d = ((q.x-p.x)**2 + (q.y-p.y)**2)**.5 / 1e6
        if d <= radius_mm: rows.append((round(d, 3), f.GetReference()))
    return [r for _, r in sorted(rows)]

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

def route_order(pcb, order):
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb); rows = []
    for name in order:
        group = IR.GROUPS[name]; nf = IR.resolve_nets(qb, group)[group["nets"][0]]
        pads = IR.physical_net_pads(qb, nf)
        try:
            rec = IR.route_inner_long_haul_plan(qb, nf, pads, group)
            edge = [{"a":x[0]["ref"], "b":x[1]["ref"], "kind":x[2],
                     "ok":bool(x[3].get("ok")), "reason":x[3].get("reason"),
                     "inner":x[4]} for x in rec]
            ok = bool(edge) and all(x["ok"] for x in edge)
            rows.append({"group":name, "ok":ok, "edges":edge})
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
    base = pcbnew.LoadBoard(IR.AUTH); pairs = connected_u3_pairs(base)
    base_drc, _ = RU.drc(IR.AUTH, "u3pose_base", SCRATCH)
    angle0 = base.FindFootprintByReference("U3").GetOrientationDegrees(); rows = []
    for angle, dx, dy in CANDIDATES:
        tag = "r%d_%+d_%+d" % (angle, round(dx*1000), round(dy*1000))
        posed = project_copy(tag); b = pcbnew.LoadBoard(posed)
        u = b.FindFootprintByReference("U3"); p = u.GetPosition()
        u.SetOrientationDegrees(angle0 + angle)
        u.SetPosition(pcbnew.VECTOR2I(p.x+round(dx*1e6), p.y+round(dy*1e6))); b.Save(posed)
        broken = sorted(pairs-connected_u3_pairs(pcbnew.LoadBoard(posed)))
        attempts = []
        for n, order in enumerate(ORDERS):
            trial = project_copy(tag+"_o%d" % n); shutil.copyfile(posed, trial)
            attempts.append(route_order(trial, order))
        dc, _ = RU.drc(posed, "u3pose_"+tag, SCRATCH)
        delta = {k:dc.get(k,0)-base_drc.get(k,0) for k in sorted(set(dc)|set(base_drc))
                 if dc.get(k,0) != base_drc.get(k,0)}
        win = any(x["ok"] for x in attempts)
        rows.append({"rotation_deg":angle, "offset_mm":[dx,dy],
                     "broken_accepted_pairs":broken, "broken_count":len(broken),
                     "routing_orders":attempts, "placement_drc":dict(dc),
                     "drc_delta":delta, "geometric_pair_candidate":win})
        print(tag, "pair", win, "broken", len(broken), "delta", delta)
    wins = [r for r in rows if r["geometric_pair_candidate"]]
    ev = {"schema_version":1, "decision":"D-359",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "baseline_orientation_deg":angle0, "baseline_drc":dict(base_drc),
          "baseline_u3_accepted_pairs":sorted(pairs), "local_neighbor_cluster_7mm":nearby(base),
          "candidates":rows, "geometric_pair_candidates":len(wins),
          "conclusion":"pose_candidate_requires_accepted_copper_impact_map" if wins
                       else "orthogonal_u3_pose_space_exhausted"}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "wins", len(wins), "auth unchanged", ev["authoritative_unchanged"])

if __name__ == "__main__": main()
