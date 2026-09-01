# -*- coding: utf-8 -*-
"""D-347: bounded scratch-only U20 rotation/non-rigid cluster screen.

Rotate U20 so pin 6 presents a materially different escape direction, while
leaving R97/R98 free to be rejoined by the router.  Accepted EN/ILIM copper is
removed only in scratch and replayed before the six-pad fault net is attempted.
"""
import hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u20_rotation_eco_049.json")
SCRATCH = os.path.join(SP, "w", "U20_ROTATION_ECO_049")
# Orthogonal package rotations, with a small bounded translation set.  R97/R98
# deliberately remain fixed: this is the minimum non-rigid cluster change and
# lets replay determine whether either passive truly needs relocation.
CANDIDATES = [(a, dx, dy) for a in (90, 180, 270)
              for dx, dy in ((0, 0), (.5, 0), (0, -.5), (0, .5), (1, 0))]
REPLAY_NETS = ("/ACC_3V3_EN", "/01_POWER_TREE/ACC_3V3_ILIM")

def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()

def connected_pairs(board):
    board.BuildConnectivity(); cc = board.GetConnectivity(); out = set()
    for ref in ("U20", "R97", "R98"):
        for p in board.FindFootprintByReference(ref).Pads():
            for q in cc.GetConnectedItems(p):
                if q.GetClass() == "PAD" and q.GetParentFootprint() != p.GetParentFootprint():
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
    src = os.path.join(RU.AUTH_DIR, "libraries")
    if os.path.isdir(src): os.symlink(src, os.path.join(d, "libraries"), target_is_directory=True)
    return pcb

def strip_replay_copper(board):
    removed = 0
    for item in list(board.GetTracks()):
        if item.GetNetname() in REPLAY_NETS:
            board.RemoveNative(item); removed += 1
    return removed

def route_group(qb, group):
    nets = IR.resolve_nets(qb, group); rows = []
    for base in group["nets"]:
        nf = nets[base]; pads = IR.physical_net_pads(qb, nf)
        pads.sort(key=lambda p: (p["ref"], p["x"], p["y"]))
        for i, j in IR.mst_edges(pads):
            a, b = pads[i], pads[j]
            r = QR.connect_role(qb, nf, a, b, "B", group["width"],
                                group["clr_pad"], group["clr_trk"])
            rows.append({"net":base, "a":a["ref"], "b":b["ref"],
                         "ok":bool(r.get("ok")), "reason":r.get("reason")})
            if not r.get("ok"): break
    return rows

def main():
    os.makedirs(SCRATCH, exist_ok=True)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_pairs = connected_pairs(base)
    base_drc, _ = RU.drc(IR.AUTH, "u20rot_base", SCRATCH); rows = []
    u0 = base.FindFootprintByReference("U20")
    base_angle = u0.GetOrientationDegrees()
    for angle, dx, dy in CANDIDATES:
        tag = "r%d_%+d_%+d" % (angle, round(dx*1000), round(dy*1000))
        pcb = project_copy(tag); b = pcbnew.LoadBoard(pcb)
        u = b.FindFootprintByReference("U20"); p = u.GetPosition()
        u.SetOrientationDegrees(base_angle + angle)
        u.SetPosition(pcbnew.VECTOR2I(p.x+round(dx*1e6), p.y+round(dy*1e6)))
        removed = strip_replay_copper(b); b.Save(pcb)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        ctl = route_group(qb, IR.GROUPS["ACC_3V3_CTL"])
        fault = route_group(qb, IR.GROUPS["ACC_POWER_FAULT_N"])
        qb.save(pcb); routed = pcbnew.LoadBoard(pcb)
        broken = sorted(base_pairs-connected_pairs(routed))
        dc, _ = RU.drc(pcb, "u20rot_"+tag, SCRATCH)
        delta = {k:dc.get(k,0)-base_drc.get(k,0) for k in sorted(set(dc)|set(base_drc))
                 if dc.get(k,0) != base_drc.get(k,0)}
        ok = all(x["ok"] for x in ctl+fault) and not broken and not delta
        row = {"rotation_deg":angle, "offset_mm":[dx,dy], "removed_replay_items":removed,
               "control_replay":ctl, "fault_route":fault, "broken_baseline_pairs":broken,
               "drc":dict(dc), "drc_delta":delta, "promotion_candidate":ok}
        rows.append(row)
        print(tag, "ctl", all(x["ok"] for x in ctl), "fault", all(x["ok"] for x in fault),
              "broken", len(broken), "drc_delta", delta, "WIN", ok)
    wins = [r for r in rows if r["promotion_candidate"]]
    evidence = {"schema_version":1, "decision":"D-347", "authoritative_board_sha256":auth_sha,
        "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
        "baseline_orientation_deg":base_angle, "baseline_drc":dict(base_drc),
        "baseline_cluster_pairs":sorted(base_pairs), "candidates":rows,
        "promotion_candidates":len(wins),
        "conclusion":"rotation_candidate_found" if wins else "orthogonal_rotation_space_exhausted"}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(evidence, f, indent=2, sort_keys=True)
    print("RESULT", evidence["conclusion"], "wins", len(wins), "auth unchanged", evidence["authoritative_unchanged"])
    return 0

if __name__ == "__main__": sys.exit(main())
