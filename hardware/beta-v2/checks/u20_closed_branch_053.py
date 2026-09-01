# -*- coding: utf-8 -*-
"""D-351: topologically closed U20 control-branch replacement screen.

Scratch only unless every promotion predicate passes.  Replace the complete
accepted ACC_3V3_EN and ACC_3V3_ILIM track branches at their pad anchors, apply
the D-349 U20 pose, reserve the fault route first, then replay both controls.
Every unrelated accepted copper signature, including XGPIO8, is immutable.
"""
import collections, hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u20_closed_branch_053.json")
SCRATCH = os.path.join(SP, "w", "U20_CLOSED_BRANCH_053")
PCB = os.path.join(SCRATCH, RU.PCBNAME)
CONTROL = ("/ACC_3V3_EN", "/01_POWER_TREE/ACC_3V3_ILIM")
TARGET = CONTROL + ("/ACC_POWER_FAULT_N",)

def sig(t):
    if t.GetClass() == "PCB_VIA":
        p=t.GetPosition(); return ("V",t.GetNetname(),p.x,p.y,t.GetWidth(pcbnew.F_Cu),t.GetDrill(),int(t.GetViaType()))
    a,z=t.GetStart(),t.GetEnd()
    return ("T",t.GetNetname(),t.GetLayerName(),tuple(sorted(((a.x,a.y),(z.x,z.y)))),t.GetWidth())

def copper(b): return collections.Counter(sig(t) for t in b.GetTracks())
def pref(p): return p.GetParentFootprint().GetReference()+"."+p.GetNumber()

def connected_pairs(b):
    b.BuildConnectivity(); cc=b.GetConnectivity(); out=set()
    for f in b.GetFootprints():
        for p in f.Pads():
            for q in cc.GetConnectedItems(p):
                if q.GetClass()=="PAD" and q.GetParentFootprint()!=f:
                    out.add(tuple(sorted((pref(p),pref(q)))))
    return out

def open_edges(b, net):
    b.BuildConnectivity(); cc=b.GetConnectivity()
    pads=[p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()==net]
    seen=set(); comps=0
    for p in pads:
        k=(pref(p),p.GetPosition().x,p.GetPosition().y)
        if k in seen: continue
        comps+=1
        reached={(pref(q),q.GetPosition().x,q.GetPosition().y) for q in cc.GetConnectedItems(p) if q.GetClass()=="PAD"}
        seen |= reached | {k}
    return max(0,comps-1)

def route_group(qb, name):
    g=IR.GROUPS[name]; nets=IR.resolve_nets(qb,g); rows=[]
    for base in g["nets"]:
        nf=nets[base]; pads=IR.physical_net_pads(qb,nf); pads.sort(key=lambda p:(p["ref"],p["x"],p["y"]))
        for i,j in IR.mst_edges(pads):
            a,b=pads[i],pads[j]
            r=QR.connect_role(qb,nf,a,b,"B",g["width"],g["clr_pad"],g["clr_trk"])
            rows.append({"net":base,"a":a["ref"],"b":b["ref"],"ok":bool(r.get("ok")),"reason":r.get("reason")})
            if not r.get("ok"): break
    return rows

def main():
    if os.path.exists(SCRATCH): shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH); shutil.copyfile(IR.AUTH,PCB)
    stem=os.path.splitext(RU.PCBNAME)[0]
    for n in (stem+".kicad_dru",stem+".kicad_pro","fp-lib-table","sym-lib-table"):
        s=os.path.join(RU.AUTH_DIR,n)
        if os.path.exists(s): shutil.copyfile(s,os.path.join(SCRATCH,n))
    lib=os.path.join(RU.AUTH_DIR,"libraries")
    if os.path.isdir(lib): os.symlink(lib,os.path.join(SCRATCH,"libraries"),target_is_directory=True)
    auth_sha=hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()
    base=pcbnew.LoadBoard(IR.AUTH); base_cu=copper(base); base_pairs=connected_pairs(base)
    base_drc,_=RU.drc(IR.AUTH,"u20closed_base",SCRATCH)
    allowed=collections.Counter(s for s in base_cu.elements() if s[0]=="T" and s[1] in CONTROL)
    b=pcbnew.LoadBoard(PCB); removed=[]
    for t in list(b.GetTracks()):
        if allowed[sig(t)] > collections.Counter(removed)[sig(t)]:
            removed.append(sig(t)); b.RemoveNative(t)
    u=b.FindFootprintByReference("U20"); p=u.GetPosition()
    u.SetOrientationDegrees(u.GetOrientationDegrees()+180)
    u.SetPosition(pcbnew.VECTOR2I(p.x,p.y+500000)); b.Save(PCB)
    qb=QR.QBoard(PCB); IR.inject_existing_via_obstacles(qb)
    # Screen the complementary reservation order to D-350.  D-350 proved that
    # controls-first fails with a cut-through eight-item boundary; this run
    # asks whether the pad-anchored boundary removes that obstruction.
    routes=route_group(qb,"ACC_3V3_CTL")+route_group(qb,"ACC_POWER_FAULT_N")
    qb.save(PCB); result=pcbnew.LoadBoard(PCB); result_cu=copper(result)
    missing=base_cu-result_cu; added=result_cu-base_cu
    forbidden_missing=missing-allowed
    forbidden_added=[s for s in added.elements() if s[1] not in TARGET]
    broken=sorted(base_pairs-connected_pairs(result))
    opens={n:open_edges(result,n) for n in TARGET}
    drc,_=RU.drc(PCB,"u20closed_result",SCRATCH)
    worse={k:[base_drc.get(k,0),drc.get(k,0)] for k in sorted(set(base_drc)|set(drc)) if drc.get(k,0)>base_drc.get(k,0)}
    passed=(collections.Counter(removed)==allowed and all(r["ok"] for r in routes)
            and not forbidden_missing and not forbidden_added and not broken
            and all(v==0 for v in opens.values()) and not worse)
    ev={"schema_version":1,"decision":"D-351","authoritative_board_sha256":auth_sha,
        "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
        "pose":{"rotation_deg":180,"offset_mm":[0,0.5]},
        "replacement_boundary":"complete_EN_ILIM_track_branches_at_pad_anchors",
        "allowed_replacement_items":sum(allowed.values()),"removed_items":len(removed),
        "routes":routes,"missing_items_total":sum(missing.values()),
        "forbidden_missing_count":sum(forbidden_missing.values()),"forbidden_added_count":len(forbidden_added),
        "accepted_pairs_broken":broken,"open_edges_after":opens,"drc_before":dict(base_drc),
        "drc_after":dict(drc),"drc_worse":worse,"transaction_candidate":passed,
        "promotion_candidate":False,
        "promotion_blocker":None if not passed else "replacement_aware_authoritative_full_board_gate_not_yet_executed",
        "conclusion":"closed_branch_transaction_candidate" if passed else "closed_branch_replacement_failed"}
    json.dump(ev,open(OUT,"w",encoding="utf-8"),indent=2,sort_keys=True)
    print(json.dumps(ev,indent=2,sort_keys=True)); return 0 if passed else 1

if __name__=="__main__": sys.exit(main())
