# -*- coding: utf-8 -*-
"""D-368: bounded local-scar replacement at the selected U3/R58 layout.

Scratch only.  Instead of replaying obsolete copper through the moved U3 pad
field, retain each incident branch outside a bounded radius of the original U3
pads and freshly connect the moved terminals to stable same-net anchors.  This
maps the minimum collision-producing scar and tests several deterministic
layer preferences.  The authoritative PCB is never edited.
"""
import collections, hashlib, json, math, os, shutil, sys

import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_r58_impact_replay_069 as D367
import u3_topology_replay_066 as D364
import u3_xgpio6_replay_065 as D363

OUT = os.path.join(SP, "u3_local_scar_replay_070.json")
SCRATCH = os.path.join(SP, "w", "U3_LOCAL_SCAR_REPLAY_070")
RADII_MM = (0.35, 0.50, 0.75, 1.00, 1.50, 2.00)
# Direct terminal-to-template attachments use pad-facing copper.  The reserved
# XGPIO pair already exercises the specialized through-via/inner-haul path;
# generic connect_role cannot legally start a physical SMT pad on an inner
# layer.
LAYER_ORDERS = (("B.Cu", "F.Cu"), ("F.Cu", "B.Cu"))
LAYER_ROLE = {"B.Cu": "B", "F.Cu": "F"}


def distance_point_segment(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay
    if dx == 0 and dy == 0:
        return math.hypot(px-ax, py-ay)
    t = max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/float(dx*dx+dy*dy)))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))


def item_distance_to_pads(item, pads):
    if isinstance(item, pcbnew.PCB_VIA):
        p = item.GetPosition(); a = (p.x, p.y); z = a
    else:
        p, q = item.GetStart(), item.GetEnd(); a = (p.x, p.y); z = (q.x, q.y)
    return min(distance_point_segment(p.x, p.y, a[0], a[1], z[0], z[1]) for p in pads)


def retained_templates(radius_mm, allowed):
    source = pcbnew.LoadBoard(IR.AUTH)
    pads = [p.GetPosition() for p in source.FindFootprintByReference("U3").Pads()]
    radius = radius_mm * 1e6
    keep, scar = collections.Counter(), collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if keep[s] + scar[s] >= allowed[s]:
            continue
        (scar if item_distance_to_pads(item, pads) <= radius else keep)[s] += 1
    return keep, scar


def restore(pcb, wanted):
    source, board = pcbnew.LoadBoard(IR.AUTH), pcbnew.LoadBoard(pcb)
    done = collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if done[s] < wanted[s]:
            board.Add(item.Duplicate()); done[s] += 1
    board.Save(pcb)
    return done


def fresh_attach(qb, net, padref, width, layers):
    terminal = {p["ref"]: p for p in IR.physical_net_pads(qb, net)}.get(padref)
    trials = []
    if terminal is None:
        return {"net": net, "terminal": padref, "ok": False, "trials": [], "error": "terminal_not_resolved"}
    for layer in layers:
        hit = RU.nearest_on_net(qb.b, net, layer, terminal["x"], terminal["y"])
        if hit is None:
            trials.append({"layer": layer, "reason": "NO_ANCHOR"}); continue
        distance, x, y, track = hit
        RU.split_at(qb.b, track, x, y)
        anchor = RU.pseudo_pad(net, x, y, QR)
        result = QR.connect_role(qb, net, terminal, anchor, LAYER_ROLE[layer],
                                 width, 200000, 200000)
        trial = {"layer": layer, "anchor_mm": [x/1e6, y/1e6],
                 "distance_mm": distance/1e6, "ok": bool(result.get("ok")),
                 "reason": result.get("reason")}
        trials.append(trial)
        if trial["ok"]:
            return {"net": net, "terminal": padref, "ok": True, "trials": trials}
    return {"net": net, "terminal": padref, "ok": False, "trials": trials}


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    base = pcbnew.LoadBoard(IR.AUTH); base_cu = D362.copper(base)
    base_pairs = D362.connected_pairs(base); allowed, branches = D362.boundary(base)
    baseline, _ = RU.drc(IR.AUTH, "u3scar_base", SCRATCH)
    attempts = []
    for radius in RADII_MM:
        keep, scar = retained_templates(radius, allowed)
        for oi, layers in enumerate(LAYER_ORDERS):
            tag = "r%03d_o%d" % (round(radius*100), oi)
            pcb, removed = D367.prepare(tag, allowed, (0.0, -0.5))
            pair = D367.reserve_pair(pcb)
            restored = restore(pcb, keep)
            qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
            attachments = []
            if len(pair) == 2 and all(x["ok"] for x in pair):
                for net in D364.SCHEDULE:
                    attachments.append(fresh_attach(qb, net, branches[net]["u3_pad"],
                                                    branches[net]["width"], layers))
                    if not attachments[-1]["ok"]: break
                if len(attachments) == len(D364.SCHEDULE) and all(x["ok"] for x in attachments):
                    attachments.append(fresh_attach(qb, "/XGPIO7_HDR", "R58.2", 200000, layers))
            IR.refill_planes(qb.b); qb.save(pcb)
            result = pcbnew.LoadBoard(pcb); result_cu = D362.copper(result)
            missing, added = base_cu-result_cu, result_cu-base_cu
            forbidden_missing = missing-allowed
            targets = set(branches) | {"/XGPIO6", "/XGPIO7", "/XGPIO7_HDR"}
            forbidden_added = [s for s in added.elements() if s[1] not in targets]
            broken = sorted(base_pairs-D362.connected_pairs(result))
            opens = {n: D363.open_edges(result, n) for n in sorted(targets)}
            drc, details = RU.drc(pcb, "u3scar_"+tag, SCRATCH)
            worse = {k:[baseline.get(k,0), drc.get(k,0)] for k in sorted(set(baseline)|set(drc))
                     if k != "unconnected_items" and drc.get(k,0) > baseline.get(k,0)}
            closed = (removed == allowed and restored == keep and len(pair) == 2
                      and all(x["ok"] for x in pair)
                      and len(attachments) == len(D364.SCHEDULE)+1
                      and all(x["ok"] for x in attachments) and not forbidden_missing
                      and not forbidden_added and not broken and all(v == 0 for v in opens.values())
                      and not worse and drc.get("unconnected_items",0) <= baseline.get("unconnected_items",0))
            row = {"radius_mm": radius, "layer_order": list(layers),
                   "retained_items": sum(keep.values()), "scar_items": sum(scar.values()),
                   "pair_routes": pair, "attachments": attachments,
                   "first_failure": next((x for x in attachments if not x["ok"]), None),
                   "forbidden_missing_count": sum(forbidden_missing.values()),
                   "forbidden_added_count": len(forbidden_added), "broken_pair_count": len(broken),
                   "open_edges_after": opens, "drc_after": dict(drc), "drc_worse": worse,
                   "drc_worse_details": {k:details[k] for k in worse}, "closed_candidate": bool(closed)}
            attempts.append(row)
            print(tag, "scar", sum(scar.values()), "attach", len(attachments),
                  "first", row["first_failure"] and row["first_failure"]["net"],
                  "drc+", sum(v[1]-v[0] for v in worse.values()), "closed", closed)
    wins = [x for x in attempts if x["closed_candidate"]]
    best = min(attempts, key=lambda x:(0 if x["closed_candidate"] else 1,
              sum(v[1]-v[0] for v in x["drc_worse"].values()), x["broken_pair_count"],
              -len(x["attachments"]), x["radius_mm"], x["layer_order"]))
    ev = {"schema_version":1, "decision":"D-368", "source_decision":"D-367",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"bounded_local_scar_retention_then_fresh_multilayer_terminal_replay",
          "selected_layout":{"u3_rotation_deg":180,"u3_offset_mm":[0.0,0.5],"r58_offset_mm":[0.0,-0.5]},
          "boundary_items":sum(allowed.values()), "baseline_drc":dict(baseline),
          "attempt_count":len(attempts), "attempts":attempts, "best_attempt":best,
          "transaction_candidates":len(wins), "promotion_candidate":False,
          "conclusion":"closed_local_scar_transaction_candidate" if wins else "local_scar_replay_not_closed"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"wins",len(wins),"auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
