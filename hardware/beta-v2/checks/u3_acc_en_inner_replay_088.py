# -*- coding: utf-8 -*-
"""D-386: complete ACC_3V3_EN replacement after the D-385 ordered prefix.

Scratch only.  Rebuild the selected XGPIO9-first/XGPIO8 transaction, restore
every unaffected accepted boundary item, then replace the complete four-pad
ACC_3V3_EN branch.  U3.15-to-R98.1 uses the qualified reserved-escape inner
haul; the two local B.Cu leaves are rebuilt only after the haul closes.
"""
import collections, hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR
import u3_cutthrough_064 as D362
import u3_ordered_p13_p15_refloor_087 as D385
import u3_xgpio6_replay_065 as D363
import u3_xgpio8_viasite_enum_081 as D379
import u3_xgpio9_viasite_enum_084 as D382

OUT = os.path.join(SP, "u3_acc_en_inner_replay_088.json")
SCRATCH = os.path.join(SP, "w", "U3_ACC_EN_INNER_REPLAY_088")
REPLACED = D385.REPLACED | {"/ACC_3V3_EN"}


def restore_unaffected(pcb, allowed):
    wanted = collections.Counter({s:n for s,n in allowed.items() if s[1] not in REPLACED})
    source, board = pcbnew.LoadBoard(IR.AUTH), pcbnew.LoadBoard(pcb)
    done = collections.Counter()
    for item in source.GetTracks():
        s = D362.sig(item)
        if done[s] < wanted[s]:
            board.Add(item.Duplicate()); done[s] += 1
    board.Save(pcb)
    return wanted, done


def route_acc(qb, inner):
    group = dict(width=200000, clr_pad=200000, clr_trk=200000,
                 via_dia=600000, via_drill=300000, nets=["ACC_3V3_EN"],
                 inner_long_haul_plan=dict(a="R98.1", b="U3.15",
                     a_near="B", b_near="B", inner=[inner]))
    net = IR.resolve_nets(qb, group)["ACC_3V3_EN"]
    pads = IR.physical_net_pads(qb, net)
    try:
        rec = IR.route_inner_long_haul_plan(qb, net, pads, group)
        haul = rec[0][3]
        rows = [{"a":rec[0][0]["ref"], "b":rec[0][1]["ref"],
                 "kind":rec[0][2], "inner":rec[0][4],
                 "ok":bool(haul.get("ok")), "result":haul}]
        if not haul.get("ok"):
            return {"ok":False, "edges":rows}
        by_ref = {p["ref"]:p for p in pads}
        for ref in ("U20.1", "TP26.1"):
            r = QR.connect_role(qb, net, by_ref["R98.1"], by_ref[ref],
                                "B", 200000, 200000, 200000)
            rows.append({"a":"R98.1", "b":ref, "kind":"local-B",
                         "ok":bool(r.get("ok")), "result":r})
            if not r.get("ok"): break
        return {"ok":len(rows)==3 and all(x["ok"] for x in rows), "edges":rows}
    except Exception as exc:
        return {"ok":False, "error":type(exc).__name__+": "+str(exc)}


def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); D362.SCRATCH = SCRATCH
    auth_sha = hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()
    baseline, _ = RU.drc(IR.AUTH,"u3acc_base",SCRATCH)
    base = pcbnew.LoadBoard(IR.AUTH); allowed, _ = D362.boundary(base); allowed &= D362.copper(base)
    seed, prefix = D385.build_six("seed", allowed)
    attempts = []
    for inner in ("I2", "I3"):
        # Keep candidates beside the prepared seed project so real KiCad DRC
        # resolves the authoritative .kicad_pro/.kicad_dru and libraries.
        pcb = os.path.join(os.path.dirname(seed),"acc_"+inner.lower()+".kicad_pcb")
        shutil.copy2(seed,pcb); qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
        x9 = D385.route_ranked(qb,"XGPIO9","R60.1","U3.14","I2",0,0,D382.reserve)
        x8 = ({"ok":False,"reason":"XGPIO9_FAILED"} if not x9["ok"] else
              D385.route_ranked(qb,"XGPIO8","R59.1","U3.13","I3",1,0,D379.reserve))
        qb.save(pcb)
        wanted = done = collections.Counter(); acc = {"ok":False,"reason":"PREFIX_FAILED"}
        if x8.get("ok"):
            wanted, done = restore_unaffected(pcb,allowed)
            qb = QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
            acc = route_acc(qb,inner); qb.save(pcb)
        open_edges = D363.open_edges(pcbnew.LoadBoard(pcb), "/ACC_3V3_EN")
        drc, details = RU.drc(pcb,"u3acc_"+inner.lower(),SCRATCH)
        worse = {k:[baseline.get(k,0),drc.get(k,0)] for k in sorted(set(baseline)|set(drc))
                 if k != "unconnected_items" and drc.get(k,0)>baseline.get(k,0)}
        attempts.append({"inner":inner,"candidate_pcb":pcb,"xgpio9":x9,"xgpio8":x8,
            "unaffected_restored_exact":done==wanted,"acc_3v3_en":acc,
            "acc_3v3_en_open_edges":open_edges,
            "drc_after":dict(drc),"drc_worse":worse,
            "drc_worse_details":{k:sorted(details[k]) for k in worse}})
        print(inner,"x9",x9["ok"],"x8",x8.get("ok"),"acc",acc.get("ok"))
    wins = [x for x in attempts if x["acc_3v3_en"].get("ok")]
    ev = {"schema_version":1,"decision":"D-386","source_decision":"D-385",
          "authoritative_board_sha256":auth_sha,
          "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
          "method":"D385_ordered_prefix_then_complete_ACC_3V3_EN_inner_replacement",
          "baseline_drc":dict(baseline),"prefix":prefix,"attempts":attempts,
          "complete_acc_routes":len(wins),"promotion_candidate":False,
          "conclusion":"ACC_COMPLETE_REPLACEMENT_ROUTES" if wins else "ACC_COMPLETE_REPLACEMENT_BLOCKED"}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print("RESULT",ev["conclusion"],"wins",len(wins),"auth",ev["authoritative_unchanged"])


if __name__ == "__main__": main()
