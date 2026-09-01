# -*- coding: utf-8 -*-
"""D-382: enumerate explicit XGPIO9 via sites after the D-380 prefix.

Scratch only. Build the seven proven replacement routes, enumerate each
XGPIO9 endpoint independently on In2/In3, and join only distinct reservable
site pairs. The authoritative PCB is never edited.
"""
import hashlib, json, os, shutil, sys
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

OUT = os.path.join(SP, "u3_xgpio9_viasite_enum_084.json")
SCRATCH = os.path.join(SP, "w", "U3_XGPIO9_VIASITE_ENUM_084")
RANKS = range(4)
SEPARATION = 500000


def build_prefix(tag, allowed):
    pcb, removed = D367.prepare(tag, allowed, (0.0, -0.5))
    pair = D367.reserve_pair(pcb)
    qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    routes = []
    for group, layer in (("XGPIO5_INNER", "I3"), ("XGPIO4_INNER", "I2"),
                         ("XGPIO2_INNER_PILOT", "I3"), ("XGPIO3_INNER", "I3")):
        rec = D371.route_inner(qb, group, layer); routes.append(rec)
        if not rec["ok"]: break
    x1 = D377.route_xgpio1(qb) if len(routes) == 4 and all(x["ok"] for x in routes) else {"ok":False,"reason":"PREFIX_FAILED"}
    x0 = D372.route_inner(qb, "XGPIO0_INNER", "I2") if x1["ok"] else {"ok":False,"reason":"XGPIO1_FAILED"}
    x8 = D380.route_xgpio8(qb) if x0["ok"] else {"ok":False,"reason":"XGPIO0_FAILED"}
    qb.save(pcb)
    return pcb, removed, pair, routes, x1, x0, x8


def reserve(qb, net, pad, other, near, inner, rank, group):
    return QR.reserve_escape(qb, net, pad, group["width"], group["clr_pad"],
        group["clr_trk"], near=near, far=inner,
        via_dia=group["via_dia"], via_drill=group["via_drill"],
        target=(other["x"], other["y"]), site_index=rank,
        site_separation=SEPARATION)


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH, "rb").read()).hexdigest()
    baseline, _ = RU.drc(IR.AUTH, "u3x9enum_base", SCRATCH)
    base = pcbnew.LoadBoard(IR.AUTH)
    boundary, _ = D362.boundary(base); allowed = boundary & D362.copper(base)
    seed, removed, pair, routes, x1, x0, x8 = build_prefix("seed", allowed)
    prefix_ok = (len(pair) == 2 and all(x["ok"] for x in pair)
                 and len(routes) == 4 and all(x["ok"] for x in routes)
                 and x1["ok"] and x0["ok"] and x8["ok"])
    group = dict(IR.GROUPS["XGPIO9"])
    probe = QR.QBoard(seed); IR.inject_existing_via_obstacles(probe)
    net = IR.resolve_nets(probe, group)[group["nets"][0]]
    pads = {p["ref"]:p for p in IR.physical_net_pads(probe, net)}
    pa, pb = pads["R60.1"], pads["U3.14"]
    isolated, attempts, distinct = [], [], set()

    for inner in ("I2", "I3"):
        for endpoint, pad, other, near in (("R60.1",pa,pb,"F"),("U3.14",pb,pa,"B")):
            for rank in RANKS:
                trial = QR.QBoard(seed); IR.inject_existing_via_obstacles(trial)
                rec = reserve(trial,net,pad,other,near,inner,rank,group) if prefix_ok else {"ok":False,"reason":"PREFIX_FAILED"}
                isolated.append({"inner":inner,"endpoint":endpoint,"rank":rank,"reservation":rec})

        for order in (("R60.1","U3.14"),("U3.14","R60.1")):
            for first_rank in RANKS:
                for second_rank in RANKS:
                    trial = QR.QBoard(seed); IR.inject_existing_via_obstacles(trial)
                    spec = {"R60.1":(pa,pb,"F"), "U3.14":(pb,pa,"B")}
                    p,o,n = spec[order[0]]
                    first = reserve(trial,net,p,o,n,inner,first_rank,group) if prefix_ok else {"ok":False,"reason":"PREFIX_FAILED"}
                    second = {"ok":False,"reason":"FIRST_FAILED"}
                    join = {"ok":False,"reason":"RESERVATION_FAILED"}
                    if first.get("ok"):
                        p,o,n = spec[order[1]]
                        second = reserve(trial,net,p,o,n,inner,second_rank,group)
                    reserved = {order[0]: tuple(first.get("via", ())),
                                order[1]: tuple(second.get("via", ()))}
                    key = (inner, reserved["R60.1"], reserved["U3.14"])
                    is_new_pair = first.get("ok") and second.get("ok") and key not in distinct
                    if is_new_pair:
                        distinct.add(key)
                        join = QR.join_reserved(trial,net,first["via"],second["via"],
                            group["width"],group["clr_pad"],group["clr_trk"],layer=inner)
                    attempts.append({"inner":inner,"order":list(order),
                        "first_rank":first_rank,"second_rank":second_rank,
                        "first_reservation":first,"second_reservation":second,
                        "distinct_pair":bool(is_new_pair),"join":join})

    prefix_drc, details = RU.drc(seed, "u3x9enum_prefix", SCRATCH)
    worse = {k:[baseline.get(k,0),prefix_drc.get(k,0)]
             for k in sorted(set(baseline)|set(prefix_drc))
             if k != "unconnected_items" and prefix_drc.get(k,0)>baseline.get(k,0)}
    endpoint_sites = {}
    for inner in ("I2","I3"):
        for endpoint in ("R60.1","U3.14"):
            vals = {tuple(x["reservation"].get("via",())) for x in isolated
                    if x["inner"]==inner and x["endpoint"]==endpoint and x["reservation"].get("ok")}
            endpoint_sites[inner+":"+endpoint] = [list(x) for x in sorted(vals)]
    wins = [x for x in attempts if x["join"].get("ok")]
    ev = {"schema_version":1,"decision":"D-382","source_decision":"D-381",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"D380_prefix_XGPIO9_independent_explicit_viasite_enumeration",
          "site_separation_mm":SEPARATION/1e6,"ranks_tested":list(RANKS),
          "baseline_drc":dict(baseline),"prefix_drc":dict(prefix_drc),
          "prefix_drc_worse":worse,"prefix_drc_worse_details":{k:sorted(details[k]) for k in worse},
          "removed_boundary_exact":removed==allowed,"pair_routes":pair,"prefix_routes":routes,
          "xgpio1_ranked_route":x1,"xgpio0_route":x0,"xgpio8_ranked_route":x8,
          "prefix_ok":prefix_ok,"isolated_endpoint_attempts":isolated,
          "endpoint_sites":endpoint_sites,"ordered_pair_attempt_count":len(attempts),
          "distinct_via_pairs":len(distinct),"route_wins":len(wins),"attempts":attempts,
          "promotion_candidate":False,
          "conclusion":"XGPIO9_distinct_viasite_route_found_needs_transaction_replay" if wins else
                       "XGPIO9_explicit_viasite_enumeration_characterized"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"sites",endpoint_sites,"pairs",len(distinct),
          "wins",len(wins),"auth unchanged",ev["authoritative_unchanged"])
    return 0


if __name__ == "__main__": sys.exit(main())
