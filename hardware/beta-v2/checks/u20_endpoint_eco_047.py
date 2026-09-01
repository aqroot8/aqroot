# -*- coding: utf-8 -*-
"""D-345: bounded scratch-only U20 placement-ECO impact/feasibility screen.

Translate U20 on the native 0.25 mm placement grid and retry the ordinary
all-B.Cu ACC_POWER_FAULT_N route.  The authoritative PCB is never edited.
For every candidate, record accepted U20 pad connections broken by the move,
nearby footprints that define the eventual replay cluster, and real KiCad DRC.
"""
import hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u20_endpoint_eco_047.json")
SCRATCH = os.path.join(SP, "w", "U20_ECO_047")
OFFSETS = [(dx, dy) for dx, dy in
           ((-.25,0),(.25,0),(0,-.25),(0,.25),(-.5,0),(.5,0),(0,-.5),(0,.5),
            (-.5,-.5),(-.5,.5),(.5,-.5),(.5,.5),(-.75,0),(.75,0),(0,-.75),(0,.75))]

def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()

def connected_u20_pairs(board):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    u20 = board.FindFootprintByReference("U20")
    out = set()
    for p in u20.Pads():
        for q in cc.GetConnectedItems(p):
            if q.GetClass() == "PAD" and q.GetParentFootprint() != u20:
                out.add((pad_ref(p), pad_ref(q)))
    return out

def nearby_footprints(board, radius_mm=4.0):
    u20 = board.FindFootprintByReference("U20"); p = u20.GetPosition()
    rows = []
    for f in board.GetFootprints():
        if f == u20: continue
        q = f.GetPosition(); d = ((q.x-p.x)**2 + (q.y-p.y)**2)**0.5 / 1e6
        if d <= radius_mm: rows.append((round(d, 3), f.GetReference()))
    return [ref for _, ref in sorted(rows)]

def route_fault(pcb):
    group = IR.GROUPS["ACC_POWER_FAULT_N"]
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    nf = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = IR.physical_net_pads(qb, nf)
    pads.sort(key=lambda x: (x["ref"], x["x"], x["y"]))
    rec = []
    for i, j in IR.mst_edges(pads):
        a, b = pads[i], pads[j]
        r = QR.connect_role(qb, nf, a, b, "B", group["width"],
                            group["clr_pad"], group["clr_trk"])
        rec.append({"a":a["ref"], "b":b["ref"], "ok":bool(r.get("ok")),
                    "reason":r.get("reason")})
        if not r.get("ok"): break
    qb.save()
    return {"ok":len(rec) == len(pads)-1 and all(x["ok"] for x in rec),
            "edges":rec}

def project_copy(tag):
    d = os.path.join(SCRATCH, tag)
    if os.path.exists(d): shutil.rmtree(d)
    os.makedirs(d)
    pcb = os.path.join(d, RU.PCBNAME); shutil.copyfile(IR.AUTH, pcb)
    stem = os.path.splitext(RU.PCBNAME)[0]
    for name in (stem+".kicad_dru", stem+".kicad_pro", "fp-lib-table", "sym-lib-table"):
        src = os.path.join(RU.AUTH_DIR, name)
        if os.path.exists(src): shutil.copyfile(src, os.path.join(d, name))
    src = os.path.join(RU.AUTH_DIR, "libraries")
    if os.path.isdir(src): os.symlink(src, os.path.join(d, "libraries"), target_is_directory=True)
    return pcb

def main():
    os.makedirs(SCRATCH, exist_ok=True)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_pairs = connected_u20_pairs(base)
    neighbors = nearby_footprints(base)
    rows = []
    for dx, dy in OFFSETS:
        tag = "%+d_%+d" % (round(dx*1000), round(dy*1000))
        pcb = project_copy(tag); b = pcbnew.LoadBoard(pcb)
        u20 = b.FindFootprintByReference("U20"); p = u20.GetPosition()
        u20.SetPosition(pcbnew.VECTOR2I(p.x+round(dx*1e6), p.y+round(dy*1e6))); b.Save(pcb)
        moved = pcbnew.LoadBoard(pcb); broken = sorted(base_pairs-connected_u20_pairs(moved))
        trial = project_copy(tag+"_route"); shutil.copyfile(pcb, trial)
        try: route = route_fault(trial)
        except Exception as e: route = {"ok":False, "error":type(e).__name__+": "+str(e)}
        dc, _ = RU.drc(pcb, "u20eco_"+tag, SCRATCH)
        row = {"offset_mm":[dx,dy], "broken_accepted_pairs":broken,
               "broken_count":len(broken), "placement_drc":dict(dc), "route":route}
        rows.append(row)
        print(tag, "broken", len(broken), "route", route.get("ok"), "drc", dict(dc))
    wins = [r for r in rows if r["route"].get("ok")]
    evidence = {"schema_version":1, "decision":"D-345",
                "authoritative_board_sha256":auth_sha,
                "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
                "baseline_u20_accepted_pairs":sorted(base_pairs),
                "local_neighbor_cluster_4mm":neighbors, "candidates":rows,
                "geometric_wins":len(wins),
                "conclusion":"candidate_found_requires_cluster_replay" if wins else "bounded_u20_translation_space_exhausted"}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(evidence, f, indent=2, sort_keys=True)
    print("RESULT", evidence["conclusion"], "wins", len(wins), "auth unchanged", evidence["authoritative_unchanged"])
    return 0

if __name__ == "__main__": sys.exit(main())
