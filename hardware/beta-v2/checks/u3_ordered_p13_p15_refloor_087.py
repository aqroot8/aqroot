# -*- coding: utf-8 -*-
"""D-385: ordered U3.14-first refloor of the adjacent U3.13-.15 branches.

Scratch only.  Rebuild the proven six-route prefix (through XGPIO0), reserve
and join complete XGPIO9 first, then replay XGPIO8, then restore and attach the
ACC_3V3_EN U3.15 branch.  This tests the minimum transactional endpoint-cluster
alternative identified by D-384 without moving parts or editing authority.
"""
import collections, hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_r58_impact_replay_069 as D367
import u3_topology_replay_066 as D364
import u3_xgpio0_inner_replay_079 as D377
import u3_xgpio2_inner_replay_073 as D371
import u3_xgpio3_inner_replay_074 as D372
import u3_xgpio8_viasite_enum_081 as D379
import u3_xgpio9_viasite_enum_084 as D382

OUT = os.path.join(SP, "u3_ordered_p13_p15_refloor_087.json")
SCRATCH = os.path.join(SP, "w", "U3_ORDERED_P13_P15_REFLOOR_087")
RANKS = range(4)
MAX_X9_SPECS = 2
REPLACED = {"/XGPIO0", "/XGPIO1", "/XGPIO2", "/XGPIO3", "/XGPIO4",
            "/XGPIO5", "/XGPIO8", "/XGPIO9"}


def build_six(tag, allowed):
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
    qb.save(pcb)
    ok = (removed == allowed and len(pair) == 2 and all(x["ok"] for x in pair)
          and len(routes) == 4 and all(x["ok"] for x in routes) and x1["ok"] and x0["ok"])
    return pcb, {"ok":ok, "removed_boundary_exact":removed == allowed,
        "pair_routes":pair, "prefix_routes":routes, "xgpio1_ranked_route":x1,
        "xgpio0_route":x0}


def route_ranked(qb, group_name, a_ref, b_ref, inner, a_rank, b_rank, reserve):
    group = dict(IR.GROUPS[group_name]); net = IR.resolve_nets(qb, group)[group["nets"][0]]
    pads = {p["ref"]:p for p in IR.physical_net_pads(qb, net)}
    pa, pb = pads[a_ref], pads[b_ref]
    ra = reserve(qb, net, pa, pb, "F", inner, a_rank, group)
    rb = ({"ok":False,"reason":"A_FAILED"} if not ra.get("ok") else
          reserve(qb, net, pb, pa, "B", inner, b_rank, group))
    join = ({"ok":False,"reason":"RESERVATION_FAILED"} if not rb.get("ok") else
            QR.join_reserved(qb, net, ra["via"], rb["via"], group["width"],
                             group["clr_pad"], group["clr_trk"], layer=inner))
    return {"ok":bool(ra.get("ok") and rb.get("ok") and join.get("ok")),
            "inner":inner, "a_rank":a_rank, "b_rank":b_rank,
            "a_reservation":ra, "b_reservation":rb, "join":join}


def restore_remaining(pcb, allowed):
    wanted = collections.Counter({s:n for s,n in allowed.items() if s[1] not in REPLACED})
    source, board = pcbnew.LoadBoard(IR.AUTH), pcbnew.LoadBoard(pcb)
    done = collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if done[s] < wanted[s]: board.Add(item.Duplicate()); done[s] += 1
    board.Save(pcb)
    return wanted, done


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH; D367.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()
    baseline, _ = RU.drc(IR.AUTH,"u3ordered_base",SCRATCH)
    base = pcbnew.LoadBoard(IR.AUTH); allowed, branches = D362.boundary(base)
    allowed &= D362.copper(base)
    seed, prefix = build_six("seed", allowed)

    # Enumerate U3.14 first on the six-route prefix; only distinct successful
    # endpoint rank pairs are replayed into complete candidates.
    isolated, x9_specs = [], []
    for inner in ("I2", "I3"):
        for endpoint, near in (("R60.1","F"), ("U3.14","B")):
            qb = QR.QBoard(seed); IR.inject_existing_via_obstacles(qb)
            group = dict(IR.GROUPS["XGPIO9"]); net = IR.resolve_nets(qb,group)[group["nets"][0]]
            pads = {p["ref"]:p for p in IR.physical_net_pads(qb,net)}
            other = pads["U3.14" if endpoint == "R60.1" else "R60.1"]
            for rank in RANKS:
                trial = QR.QBoard(seed); IR.inject_existing_via_obstacles(trial)
                rec = D382.reserve(trial,net,pads[endpoint],other,near,inner,rank,group)
                isolated.append({"inner":inner,"endpoint":endpoint,"rank":rank,"reservation":rec})
        ar = sorted({x["rank"] for x in isolated if x["inner"]==inner and x["endpoint"]=="R60.1" and x["reservation"].get("ok")})
        br = sorted({x["rank"] for x in isolated if x["inner"]==inner and x["endpoint"]=="U3.14" and x["reservation"].get("ok")})
        x9_specs += [(inner,a,b) for a in ar for b in br]

    attempts = []
    # Rank-order is deterministic.  Two complete U3.14-first transactions are
    # enough to distinguish a local U3.15 replay wall without paying to rebuild
    # the identical six-route prefix for every Cartesian rank pair.
    for n, (inner, arank, brank) in enumerate(x9_specs[:MAX_X9_SPECS]):
        pcb = os.path.join(SCRATCH, "x9_%02d.kicad_pcb" % n)
        shutil.copy2(seed, pcb)
        pfx = prefix
        qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        x9 = route_ranked(qb,"XGPIO9","R60.1","U3.14",inner,arank,brank,D382.reserve)
        x8_attempts, x8 = [], {"ok":False,"reason":"XGPIO9_FAILED"}
        if x9["ok"]:
            for ai in RANKS:
                for bi in RANKS:
                    # Each rank pair needs the same post-XGPIO9 state.
                    state = os.path.join(SCRATCH,"x9state_%02d_%d_%d.kicad_pcb" % (n,ai,bi))
                    qb.save(state); trial = QR.QBoard(state); IR.inject_existing_via_obstacles(trial)
                    rec = route_ranked(trial,"XGPIO8","R59.1","U3.13","I3",ai,bi,D379.reserve)
                    x8_attempts.append(rec)
                    if rec["ok"]:
                        x8 = rec; qb = trial; pcb = state; break
                if x8.get("ok"): break
        qb.save(pcb)
        wanted = done = collections.Counter(); acc = {"ok":False,"reason":"XGPIO8_FAILED"}
        if x8.get("ok"):
            wanted, done = restore_remaining(pcb,allowed)
            qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
            acc = D364.attach_terminal(qb,"/ACC_3V3_EN",branches["/ACC_3V3_EN"]["u3_pad"],branches["/ACC_3V3_EN"]["width"])
            qb.save(pcb)
        attempts.append({"candidate_pcb":pcb,"xgpio9":x9,"xgpio8_attempts":x8_attempts,"xgpio8":x8,
                         "remaining_restored_exact":done==wanted,"acc_3v3_en":acc})
        print(n,inner,arank,brank,"x9",x9["ok"],"x8",x8.get("ok"),"acc",acc.get("ok"))

    progressed = [x for x in attempts if x["xgpio9"]["ok"]]
    closed8 = [x for x in attempts if x["xgpio8"].get("ok")]
    closed15 = [x for x in attempts if x["acc_3v3_en"].get("ok")]
    furthest_drc = {}
    if attempts:
        # Rank-pair snapshots live directly under SCRATCH and intentionally do
        # not duplicate the full KiCad project.  Put the DRC copy beside the
        # prepared seed, whose directory has the authoritative project/rules
        # context required by kicad-cli.
        drc_pcb = os.path.join(os.path.dirname(seed), "furthest.kicad_pcb")
        shutil.copy2(attempts[-1]["candidate_pcb"], drc_pcb)
        furthest_drc, _ = RU.drc(drc_pcb, "u3ordered_furthest", SCRATCH)
    ev = {"schema_version":1,"decision":"D-385","source_decision":"D-384",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"six_route_prefix_then_ordered_complete_XGPIO9_XGPIO8_ACC_3V3_EN_replay",
          "baseline_drc":dict(baseline),"prefix":prefix,"ranks_tested":list(RANKS),
          "xgpio9_isolated_attempts":isolated,"xgpio9_pair_specs":len(x9_specs),
          "xgpio9_pair_specs_screened":len(attempts),"max_xgpio9_specs":MAX_X9_SPECS,
          "attempts":attempts,"xgpio9_routes":len(progressed),"xgpio8_after_xgpio9_routes":len(closed8),
          "acc_3v3_en_after_xgpio8_routes":len(closed15),"promotion_candidate":False,
          "furthest_candidate_drc":dict(furthest_drc),
          "conclusion":("ordered_three_branch_replay_reaches_U3P15" if closed15 else
                        "ordered_XGPIO9_first_reaches_XGPIO8" if closed8 else
                        "ordered_XGPIO9_first_closes_U3P14_only" if progressed else
                        "ordered_U3P14_first_refloor_closed")}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"x9",len(progressed),"x8",len(closed8),"p15",len(closed15),"auth",ev["authoritative_unchanged"])


if __name__ == "__main__": main()
