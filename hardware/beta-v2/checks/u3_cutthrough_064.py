# -*- coding: utf-8 -*-
"""D-362: exact complete-U3-branch cut-through transaction screen.

Scratch only.  Withdraw every copper item in each routed connectivity component
incident on U3, apply D-360's least-impact pose, reserve XGPIO6/XGPIO7 first in
both deterministic orders, then replay every withdrawn branch.  Copper outside
the exact connectivity-derived boundary is immutable.
"""
import collections, hashlib, json, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u3_cutthrough_064.json")
SCRATCH = os.path.join(SP, "w", "U3_CUTTHROUGH_064")
ORDERS = (("XGPIO6_INNER", "XGPIO7_INNER"),
          ("XGPIO7_INNER", "XGPIO6_INNER"))
POSE = (180, 0.0, 0.5)


def sig(t):
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        return ("V", t.GetNetname(), p.x, p.y, t.GetWidth(pcbnew.F_Cu),
                t.GetDrillValue(), int(t.GetViaType()))
    a, z = t.GetStart(), t.GetEnd()
    return ("T", t.GetNetname(), t.GetLayerName(),
            tuple(sorted(((a.x, a.y), (z.x, z.y)))), t.GetWidth())


def copper(board):
    return collections.Counter(sig(t) for t in board.GetTracks())


def pref(p):
    return p.GetParentFootprint().GetReference() + "." + p.GetNumber()


def connected_pairs(board):
    board.BuildConnectivity(); cc = board.GetConnectivity(); out = set()
    for f in board.GetFootprints():
        for p in f.Pads():
            for q in cc.GetConnectedItems(p):
                if q.GetClass() == "PAD" and q.GetParentFootprint() != f:
                    out.add(tuple(sorted((pref(p), pref(q)))))
    return out


def boundary(board):
    """Exact union of routed copper components touching a U3 pad."""
    board.BuildConnectivity(); cc = board.GetConnectivity(); allowed = collections.Counter()
    branches = {}
    for p in board.FindFootprintByReference("U3").Pads():
        items = [x for x in cc.GetConnectedItems(p) if isinstance(x, pcbnew.PCB_TRACK)]
        if not items:
            continue
        net = p.GetNetname()
        rows = collections.Counter(sig(x) for x in items)
        allowed |= rows
        widths = [x.GetWidth() for x in items if not isinstance(x, pcbnew.PCB_VIA)]
        pads = sorted({pref(x) for x in cc.GetConnectedItems(p) if x.GetClass() == "PAD"})
        branches[net] = {"u3_pad": pref(p), "pads": pads,
                         "items": sum(rows.values()),
                         "width": collections.Counter(widths).most_common(1)[0][0]}
    return allowed, branches


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


def prepare(pcb, allowed):
    board = pcbnew.LoadBoard(pcb); removed = collections.Counter()
    for t in list(board.GetTracks()):
        s = sig(t)
        if removed[s] < allowed[s]:
            removed[s] += 1; board.RemoveNative(t)
    u3 = board.FindFootprintByReference("U3"); p = u3.GetPosition()
    u3.SetOrientationDegrees(u3.GetOrientationDegrees()+POSE[0])
    u3.SetPosition(pcbnew.VECTOR2I(p.x+round(POSE[1]*1e6), p.y+round(POSE[2]*1e6)))
    board.Save(pcb)
    return removed


def route_inner(qb, name):
    g = IR.GROUPS[name]; nf = IR.resolve_nets(qb, g)[g["nets"][0]]
    pads = IR.physical_net_pads(qb, nf)
    try:
        rec = IR.route_inner_long_haul_plan(qb, nf, pads, g)
        edges = [{"a":x[0]["ref"], "b":x[1]["ref"], "kind":x[2],
                  "ok":bool(x[3].get("ok")), "reason":x[3].get("reason"),
                  "inner":x[4]} for x in rec]
        return {"group":name, "ok":bool(edges) and all(x["ok"] for x in edges), "edges":edges}
    except Exception as e:
        return {"group":name, "ok":False, "error":type(e).__name__+": "+str(e)}


def replay_branch(qb, netname, meta):
    # QBoard exposes resolved names through ``nets``.  D-362 never exercised
    # this path because XGPIO7 reservation failed first; keep the latent replay
    # path valid for bounded successor experiments.
    nf = netname if netname in qb.nets else None
    if nf is None:
        return {"net":netname, "ok":False, "error":"net_not_resolved"}
    pads = IR.physical_net_pads(qb, nf); pads.sort(key=lambda p:(p["ref"],p["x"],p["y"]))
    rows = []
    for i, j in IR.mst_edges(pads):
        a, b = pads[i], pads[j]
        r = QR.connect_role(qb, nf, a, b, "B", meta["width"], 200000, 200000)
        rows.append({"a":a["ref"], "b":b["ref"], "ok":bool(r.get("ok")),
                     "reason":r.get("reason")})
        if not r.get("ok"): break
    return {"net":netname, "ok":bool(rows) and all(x["ok"] for x in rows), "edges":rows}


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    auth_sha = hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = copper(base); base_pairs = connected_pairs(base)
    allowed, branches = boundary(base)
    base_drc, _ = RU.drc(IR.AUTH, "u3cut_base", SCRATCH)
    attempts = []
    for oi, order in enumerate(ORDERS):
        pcb = project_copy("order_%d" % oi); removed = prepare(pcb, allowed)
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        pair = []
        for name in order:
            pair.append(route_inner(qb, name))
            if not pair[-1]["ok"]: break
        replay = []
        if len(pair) == 2 and all(x["ok"] for x in pair):
            # Small/local branches first, preserving deterministic net-name tie break.
            for net, meta in sorted(branches.items(), key=lambda x:(x[1]["items"],x[0])):
                replay.append(replay_branch(qb, net, meta))
                if not replay[-1]["ok"]: break
        IR.refill_planes(qb.b); qb.save(pcb)
        result = pcbnew.LoadBoard(pcb); result_cu = copper(result)
        missing, added = base_cu-result_cu, result_cu-base_cu
        forbidden_missing = missing-allowed
        target_nets = set(branches) | {"/XGPIO6", "/XGPIO7"}
        forbidden_added = [s for s in added.elements() if s[1] not in target_nets]
        broken = sorted(base_pairs-connected_pairs(result))
        drc, _ = RU.drc(pcb, "u3cut_o%d"%oi, SCRATCH)
        worse = {k:[base_drc.get(k,0),drc.get(k,0)] for k in sorted(set(base_drc)|set(drc))
                 if k != "unconnected_items" and drc.get(k,0)>base_drc.get(k,0)}
        closed = (removed == allowed and len(pair)==2 and all(x["ok"] for x in pair)
                  and len(replay)==len(branches) and all(x["ok"] for x in replay)
                  and not forbidden_missing and not forbidden_added and not broken and not worse
                  and drc.get("unconnected_items",0) <= base_drc.get("unconnected_items",0))
        attempts.append({"order":list(order), "pair_routes":pair, "branch_replay":replay,
                         "removed_items":sum(removed.values()), "missing_items_total":sum(missing.values()),
                         "forbidden_missing_count":sum(forbidden_missing.values()),
                         "forbidden_added_count":len(forbidden_added), "accepted_pairs_broken":broken,
                         "drc_after":dict(drc), "drc_worse":worse, "closed_candidate":closed})
        print("order", oi, "pair", [x["ok"] for x in pair], "replay", len(replay),
              "broken", len(broken), "closed", closed)
    wins = [x for x in attempts if x["closed_candidate"]]
    ev = {"schema_version":1, "decision":"D-362", "source_decision":"D-361",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "pose":{"rotation_deg":POSE[0], "offset_mm":list(POSE[1:])},
          "replacement_boundary":"complete_connectivity_components_incident_on_U3",
          "boundary_items":sum(allowed.values()), "branch_count":len(branches),
          "branches":branches, "baseline_drc":dict(base_drc), "attempts":attempts,
          "transaction_candidates":len(wins),
          "conclusion":"closed_U3_cutthrough_candidate" if wins else "complete_U3_cutthrough_replay_failed"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
