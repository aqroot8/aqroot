# -*- coding: utf-8 -*-
"""D-348: in-place U20 rotation with exact add-only accepted-copper replay.

Unlike D-347, no accepted control copper is removed.  U20 is rotated 90 degrees
in scratch, then the existing ACC_3V3 control groups and the six-terminal fault
group are reconnected add-only.  The result is characterization evidence until
the full promotion suite accepts the placement ECO.
"""
import collections, hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u20_exact_replay_050.json")
SCRATCH = os.path.join(SP, "w", "U20_EXACT_REPLAY_050")
TARGET_NETS = ("/ACC_3V3_EN", "/01_POWER_TREE/ACC_3V3_ILIM",
               "/01_POWER_TREE/ACC_POWER_FAULT_N")
CANDIDATES = ((90, 0, 0), (90, 0, .5), (180, 0, 0),
              (180, .5, 0), (180, 0, .5), (180, 1, 0))

def sig(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        return ("V", t.GetNetname(), p.x, p.y, t.GetWidth(pcbnew.F_Cu),
                t.GetDrill(), int(t.GetViaType()))
    a, z = t.GetStart(), t.GetEnd()
    ends = tuple(sorted(((a.x, a.y), (z.x, z.y))))
    return ("T", t.GetNetname(), t.GetLayerName(), ends, t.GetWidth())

def copper(board):
    return collections.Counter(sig(t) for t in board.GetTracks())

def pad_ref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()

def pairs(board):
    board.BuildConnectivity(); cc = board.GetConnectivity(); out = set()
    for f in board.GetFootprints():
        for p in f.Pads():
            for q in cc.GetConnectedItems(p):
                if q.GetClass() == "PAD" and q.GetParentFootprint() != f:
                    out.add(tuple(sorted((pad_ref(p), pad_ref(q)))))
    return out

def open_edges(board, net):
    board.BuildConnectivity(); cc = board.GetConnectivity()
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    if not pads: return 0
    seen = set(); comps = 0
    for p in pads:
        key = pad_ref(p)
        if key in seen: continue
        comps += 1
        reached = {pad_ref(q) for q in cc.GetConnectedItems(p) if q.GetClass() == "PAD"}
        seen |= reached | {key}
    return max(0, comps - 1)

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

def route_group(qb, name):
    g = IR.GROUPS[name]; nets = IR.resolve_nets(qb, g); rows = []
    for base in g["nets"]:
        nf = nets[base]; pads = IR.physical_net_pads(qb, nf)
        pads.sort(key=lambda p: (p["ref"], p["x"], p["y"]))
        for i, j in IR.mst_edges(pads):
            a, b = pads[i], pads[j]
            r = QR.connect_role(qb, nf, a, b, "B", g["width"], g["clr_pad"], g["clr_trk"])
            rows.append({"net": base, "a": a["ref"], "b": b["ref"],
                         "ok": bool(r.get("ok")), "reason": r.get("reason")})
            if not r.get("ok"): break
    return rows

def main():
    os.makedirs(SCRATCH, exist_ok=True)
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = copper(base); base_pairs = pairs(base)
    base_drc, _ = RU.drc(IR.AUTH, "u20exact_base", os.path.dirname(SCRATCH))
    base_open = {n: open_edges(base, n) for n in TARGET_NETS}
    old_angle = base.FindFootprintByReference("U20").GetOrientationDegrees()
    rows = []
    for angle, dx, dy in CANDIDATES:
        tag = "r%d_%+d_%+d" % (angle, round(dx*1000), round(dy*1000))
        pcb = project_copy(tag); b = pcbnew.LoadBoard(pcb)
        u = b.FindFootprintByReference("U20"); p = u.GetPosition()
        u.SetOrientationDegrees(old_angle + angle)
        u.SetPosition(pcbnew.VECTOR2I(p.x+round(dx*1e6), p.y+round(dy*1e6))); b.Save(pcb)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        routes = route_group(qb, "ACC_3V3_CTL") + route_group(qb, "ACC_POWER_FAULT_N")
        qb.save(pcb); result = pcbnew.LoadBoard(pcb); result_cu = copper(result)
        missing = list((base_cu - result_cu).elements())
        broken = sorted(base_pairs - pairs(result))
        after_open = {n: open_edges(result, n) for n in TARGET_NETS}
        dc, _ = RU.drc(pcb, "u20exact_"+tag, SCRATCH)
        worse = {k: (base_drc.get(k, 0), dc.get(k, 0)) for k in sorted(set(base_drc)|set(dc))
                 if dc.get(k, 0) > base_drc.get(k, 0)}
        ok = (all(r["ok"] for r in routes) and not missing and not broken and not worse
              and all(after_open[n] == 0 for n in TARGET_NETS))
        rows.append({"rotation_deg": angle, "offset_mm": [dx, dy], "routes": routes,
            "accepted_copper_missing_count": len(missing), "accepted_pairs_broken": broken,
            "open_edges_after": after_open, "copper_items_after": sum(result_cu.values()),
            "drc_after": dict(dc), "drc_worse": worse, "promotion_candidate": ok})
        print(tag, "routes", all(r["ok"] for r in routes), "broken", len(broken),
              "worse", worse, "WIN", ok)
    wins = [r for r in rows if r["promotion_candidate"]]
    evidence = {"schema_version": 1, "decision": "D-348", "authoritative_sha256": auth_sha,
        "authoritative_unchanged": hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest() == auth_sha,
        "orientation_before_deg": old_angle, "open_edges_before": base_open,
        "copper_items_before": sum(base_cu.values()), "drc_before": dict(base_drc),
        "candidates": rows, "promotion_candidates": len(wins),
        "conclusion": "exact_add_only_candidate" if wins else "exact_add_only_replay_exhausted"}
    with open(OUT, "w", encoding="utf-8") as f: json.dump(evidence, f, indent=2, sort_keys=True)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__": sys.exit(main())
