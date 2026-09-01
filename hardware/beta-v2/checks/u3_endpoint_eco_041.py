# -*- coding: utf-8 -*-
"""D-341: bounded scratch-only U3 placement-ECO impact/feasibility screen.

Translate U3 by <=1 mm on the 0.25/0.50 mm placement grid, then exercise the
proven inner-layer XGPIO6/7 plan.  Authoritative copper is never edited.  The
record explicitly counts accepted U3 pad connections broken by the move, so a
geometric win cannot be mistaken for a promotable ECO.
"""
import collections, hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import live_fingerprint as LFP
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u3_endpoint_eco_041.json")
SCRATCH = os.path.join(SP, "w", "U3_ECO_041")
NETS = ("XGPIO6_INNER", "XGPIO7_INNER")
OFFSETS = [(dx, dy) for dx, dy in
           ((-.25,0),(.25,0),(0,-.25),(0,.25),(-.5,0),(.5,0),(0,-.5),(0,.5),
            (-.5,-.5),(-.5,.5),(.5,-.5),(.5,.5),(-1,0),(1,0),(0,-1),(0,1))]

def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()

def connected_u3_pairs(board):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    u3 = board.FindFootprintByReference("U3")
    out = set()
    for p in u3.Pads():
        for q in cc.GetConnectedItems(p):
            if q.GetClass() == "PAD" and q.GetParentFootprint() != u3:
                out.add((pad_ref(p), pad_ref(q)))
    return out

def route_one(pcb, name):
    group = IR.GROUPS[name]
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    net = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = IR.physical_net_pads(qb, net)
    records = IR.route_inner_long_haul_plan(qb, net, pads, group)
    qb.save()
    ok = bool(records) and all(r[3].get("ok") for r in records)
    return {"ok":ok, "reason":None if ok else (records[-1][3].get("reason") if records else "no records")}

def project_copy(tag):
    d = os.path.join(SCRATCH, tag)
    if os.path.exists(d): shutil.rmtree(d)
    os.makedirs(d)
    pcb = os.path.join(d, RU.PCBNAME)
    shutil.copyfile(IR.AUTH, pcb)
    stem = os.path.splitext(RU.PCBNAME)[0]
    for name in (stem + ".kicad_dru", stem + ".kicad_pro", "fp-lib-table", "sym-lib-table"):
        src = os.path.join(RU.AUTH_DIR, name)
        if os.path.exists(src): shutil.copyfile(src, os.path.join(d, name))
    src = os.path.join(RU.AUTH_DIR, "libraries")
    if os.path.isdir(src): os.symlink(src, os.path.join(d, "libraries"), target_is_directory=True)
    return pcb

def main():
    os.makedirs(SCRATCH, exist_ok=True)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH)
    base_pairs = connected_u3_pairs(base)
    rows = []
    for dx, dy in OFFSETS:
        tag = "%+d_%+d" % (round(dx*1000), round(dy*1000))
        pcb = project_copy(tag)
        b = pcbnew.LoadBoard(pcb); u3 = b.FindFootprintByReference("U3")
        p = u3.GetPosition(); u3.SetPosition(pcbnew.VECTOR2I(p.x+round(dx*1e6), p.y+round(dy*1e6)))
        b.Save(pcb)
        placed = pcbnew.LoadBoard(pcb)
        after_move = connected_u3_pairs(placed)
        broken = sorted(base_pairs - after_move)
        routes = {}
        for name in NETS:
            trial = project_copy(tag + "_" + name)
            shutil.copyfile(pcb, trial)
            try:
                rec = route_one(trial, name)
                routes[name] = {"ok": bool(rec.get("ok")), "reason": rec.get("reason")}
            except Exception as e:
                routes[name] = {"ok": False, "reason": type(e).__name__ + ": " + str(e)}
        dc, _ = RU.drc(pcb, "u3eco_" + tag, SCRATCH)
        rows.append({"offset_mm":[dx,dy], "broken_accepted_pairs":broken,
                     "broken_count":len(broken), "placement_drc":dict(dc), "routes":routes})
        print(tag, "broken", len(broken), "routes", {k:v["ok"] for k,v in routes.items()},
              "drc", dict(dc))
    wins = [r for r in rows if any(v["ok"] for v in r["routes"].values())]
    evidence = {"decision":"D-341", "authoritative_board_sha256":auth_sha,
                "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
                "baseline_u3_accepted_pairs":sorted(base_pairs), "candidates":rows,
                "geometric_wins":len(wins),
                "conclusion":"candidate_found_requires_accepted_copper_replay" if wins else "bounded_translation_space_exhausted"}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(evidence, f, indent=2, sort_keys=True)
    print("RESULT", evidence["conclusion"], "wins", len(wins), "auth unchanged", evidence["authoritative_unchanged"])
    return 0

if __name__ == "__main__": sys.exit(main())
