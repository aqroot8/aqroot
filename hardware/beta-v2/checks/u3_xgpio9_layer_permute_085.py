# -*- coding: utf-8 -*-
"""D-383: permute XGPIO5/XGPIO4 layers and probe XGPIO9 U3.14 escape.

Scratch only. Rebuild each of the four proven early-layer allocations, retain
only prefixes that still close all seven replacement routes, then enumerate
reachable U3.14 via sites on In2/In3. The authoritative PCB is never edited.
"""
import hashlib, itertools, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_r58_impact_replay_069 as D367
import u3_xgpio0_inner_replay_079 as D377
import u3_xgpio2_inner_replay_073 as D371
import u3_xgpio3_inner_replay_074 as D372
import u3_xgpio8_transaction_replay_082 as D380
import u3_xgpio9_viasite_enum_084 as D382

OUT = os.path.join(SP, "u3_xgpio9_layer_permute_085.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO9_LAYER_PERMUTE_085")
RANKS = range(4)


def build_prefix(tag, allowed, x5_layer, x4_layer):
    pcb, removed = D367.prepare(tag, allowed, (0.0, -0.5))
    pair = D367.reserve_pair(pcb)
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    routes = []
    for group, layer in (("XGPIO5_INNER", x5_layer),
                         ("XGPIO4_INNER", x4_layer),
                         ("XGPIO2_INNER_PILOT", "I3"),
                         ("XGPIO3_INNER", "I3")):
        rec = D371.route_inner(qb, group, layer); routes.append(rec)
        if not rec["ok"]: break
    x1 = D377.route_xgpio1(qb) if len(routes) == 4 and all(x["ok"] for x in routes) else {"ok":False,"reason":"PREFIX_FAILED"}
    x0 = D372.route_inner(qb, "XGPIO0_INNER", "I2") if x1["ok"] else {"ok":False,"reason":"XGPIO1_FAILED"}
    x8 = D380.route_xgpio8(qb) if x0["ok"] else {"ok":False,"reason":"XGPIO0_FAILED"}
    qb.save(pcb)
    ok = (removed == allowed and len(pair) == 2 and all(x["ok"] for x in pair)
          and len(routes) == 4 and all(x["ok"] for x in routes)
          and x1["ok"] and x0["ok"] and x8["ok"])
    return pcb, {"removed_boundary_exact":removed == allowed, "pair_routes":pair,
                 "prefix_routes":routes, "xgpio1_ranked_route":x1,
                 "xgpio0_route":x0, "xgpio8_ranked_route":x8, "ok":ok}


def probe_sites(seed, prefix_ok):
    probe = QR.QBoard(seed); IR.inject_existing_via_obstacles(probe)
    group = dict(IR.GROUPS["XGPIO9"])
    net = IR.resolve_nets(probe, group)[group["nets"][0]]
    pads = {p["ref"]:p for p in IR.physical_net_pads(probe, net)}
    pa, pb = pads["R60.1"], pads["U3.14"]
    attempts, sites = [], {}
    for inner in ("I2", "I3"):
        found = set()
        for rank in RANKS:
            trial = QR.QBoard(seed); IR.inject_existing_via_obstacles(trial)
            rec = (D382.reserve(trial, net, pb, pa, "B", inner, rank, group)
                   if prefix_ok else {"ok":False,"reason":"PREFIX_FAILED"})
            attempts.append({"inner":inner, "rank":rank, "reservation":rec})
            if rec.get("ok"): found.add(tuple(rec["via"]))
        sites[inner] = [list(x) for x in sorted(found)]
    return attempts, sites


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    baseline, _ = RU.drc(IR.AUTH, "u3x9perm_base", SCRATCH)
    base = pcbnew.LoadBoard(IR.AUTH)
    boundary, _ = D362.boundary(base); allowed = boundary & D362.copper(base)
    allocations = []
    for x5, x4 in itertools.product(("I2", "I3"), repeat=2):
        tag = "x5%s_x4%s" % (x5.lower(), x4.lower())
        seed, prefix = build_prefix(tag, allowed, x5, x4)
        attempts, sites = probe_sites(seed, prefix["ok"])
        drc, _ = RU.drc(seed, "u3x9perm_" + tag, SCRATCH)
        worse = {k:[baseline.get(k,0),drc.get(k,0)]
                 for k in sorted(set(baseline)|set(drc))
                 if k != "unconnected_items" and drc.get(k,0)>baseline.get(k,0)}
        allocations.append({"xgpio5_layer":x5, "xgpio4_layer":x4,
            "prefix":prefix, "u3_14_attempts":attempts, "u3_14_sites":sites,
            "prefix_drc":dict(drc), "prefix_drc_worse":worse})
    viable = [x for x in allocations if x["prefix"]["ok"]]
    exposed = [x for x in viable if any(x["u3_14_sites"].values())]
    ev = {"schema_version":1, "decision":"D-383", "source_decision":"D-382",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"four_XGPIO5_XGPIO4_inner_layer_allocations_then_U3P14_site_enumeration",
          "ranks_tested":list(RANKS), "baseline_drc":dict(baseline),
          "allocation_count":len(allocations), "viable_prefix_count":len(viable),
          "allocations_exposing_u3_14_count":len(exposed), "allocations":allocations,
          "promotion_candidate":False,
          "conclusion":("layer_permutation_exposes_XGPIO9_U3P14_site_needs_pair_join"
                        if exposed else "XGPIO5_XGPIO4_layer_permutation_closed_for_XGPIO9_escape")}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"viable",len(viable),"exposed",len(exposed),
          "sites",[(x["xgpio5_layer"],x["xgpio4_layer"],x["u3_14_sites"]) for x in viable],
          "auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
