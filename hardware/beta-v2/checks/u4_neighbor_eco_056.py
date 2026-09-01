# -*- coding: utf-8 -*-
"""D-354: bounded scratch-only U4 neighbor-cluster ECO screen.

Change the BMI270 pose so U4.4 presents a materially different ordinary-via
escape, then retry BMI270_INT1_RAW with the accepted reserved-escape/inner-haul
framework.  The authoritative PCB is never edited.  Every candidate records
accepted U4 pad-pair casualties and real KiCad DRC deltas.
"""
import hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u4_neighbor_eco_056.json")
SCRATCH = os.path.join(SP, "w", "U4_NEIGHBOR_ECO_056")
CANDIDATES = [(a, dx, dy) for a in (0, 90, 180, 270)
              for dx, dy in ((0, 0), (-.5, 0), (.5, 0), (0, -.5), (0, .5))
              if a or dx or dy]

def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()

def connected_u4_pairs(board):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    u4 = board.FindFootprintByReference("U4"); out = set()
    for p in u4.Pads():
        for q in cc.GetConnectedItems(p):
            if q.GetClass() == "PAD" and q.GetParentFootprint() != u4:
                out.add(tuple(sorted((pad_ref(p), pad_ref(q)))))
    return out

def nearby(board, radius_mm=4.0):
    u4 = board.FindFootprintByReference("U4"); p = u4.GetPosition(); rows = []
    for f in board.GetFootprints():
        if f == u4: continue
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

def route_raw(pcb):
    group = dict(IR.GROUPS["BMI270_INT1_RAW"])
    group.update(via_dia=600000, via_drill=300000,
                 inner_long_haul_plan=dict(a="R18.1", b="U4.4",
                                           a_near="F", b_near="B",
                                           inner=["I2", "I3"]))
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    nf = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = IR.physical_net_pads(qb, nf)
    rec = IR.route_inner_long_haul_plan(qb, nf, pads, group)
    qb.save()
    rows = [{"a":x[0]["ref"], "b":x[1]["ref"], "kind":x[2],
             "ok":bool(x[3].get("ok")), "reason":x[3].get("reason"),
             "inner":x[4]} for x in rec]
    return {"ok":bool(rows) and all(x["ok"] for x in rows), "edges":rows}

def main():
    os.makedirs(SCRATCH, exist_ok=True)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); pairs = connected_u4_pairs(base)
    base_drc, _ = RU.drc(IR.AUTH, "u4eco_base", SCRATCH)
    u0 = base.FindFootprintByReference("U4"); angle0 = u0.GetOrientationDegrees()
    rows = []
    for angle, dx, dy in CANDIDATES:
        tag = "r%d_%+d_%+d" % (angle, round(dx*1000), round(dy*1000))
        pcb = project_copy(tag); b = pcbnew.LoadBoard(pcb)
        u = b.FindFootprintByReference("U4"); p = u.GetPosition()
        u.SetOrientationDegrees(angle0 + angle)
        u.SetPosition(pcbnew.VECTOR2I(p.x+round(dx*1e6), p.y+round(dy*1e6)))
        b.Save(pcb)
        broken = sorted(pairs-connected_u4_pairs(pcbnew.LoadBoard(pcb)))
        try: route = route_raw(pcb)
        except Exception as e: route = {"ok":False, "error":type(e).__name__+": "+str(e)}
        dc, _ = RU.drc(pcb, "u4eco_"+tag, SCRATCH)
        delta = {k:dc.get(k,0)-base_drc.get(k,0) for k in sorted(set(dc)|set(base_drc))
                 if dc.get(k,0) != base_drc.get(k,0)}
        win = route.get("ok",False) and not delta
        rows.append({"rotation_deg":angle, "offset_mm":[dx,dy],
                     "broken_accepted_pairs":broken, "broken_count":len(broken),
                     "route":route, "drc":dict(dc), "drc_delta":delta,
                     "geometric_candidate":win})
        print(tag, "route", route.get("ok"), "broken", len(broken), "delta", delta, "WIN", win)
    wins = [r for r in rows if r["geometric_candidate"]]
    ev = {"schema_version":1, "decision":"D-354", "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "baseline_orientation_deg":angle0, "baseline_drc":dict(base_drc),
          "baseline_u4_accepted_pairs":sorted(pairs), "local_neighbor_cluster_4mm":nearby(base),
          "candidates":rows, "geometric_candidates":len(wins),
          "conclusion":"candidate_found_requires_accepted_copper_replay" if wins else "bounded_u4_pose_space_exhausted"}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(ev, f, indent=2, sort_keys=True)
    print("RESULT", ev["conclusion"], "wins", len(wins), "auth unchanged", ev["authoritative_unchanged"])

if __name__ == "__main__": main()
