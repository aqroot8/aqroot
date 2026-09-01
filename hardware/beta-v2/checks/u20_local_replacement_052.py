# -*- coding: utf-8 -*-
"""D-350: bounded U20 local-control copper replacement transaction.

Scratch only unless every promotion predicate passes.  Apply the D-349 least-
impact pose, remove exactly its eight mapped EN/ILIM B.Cu segments, replay both
control nets, and route ACC_POWER_FAULT_N.  XGPIO8 and every other accepted
copper item are immutable.
"""
import collections, hashlib, json, os, shutil, sys
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import incremental_router as IR
import path_role_util as RU
import qrouter as QR

OUT = os.path.join(SP, "u20_local_replacement_052.json")
SCRATCH = os.path.join(SP, "w", "U20_LOCAL_REPLACEMENT_052")
PCB = os.path.join(SCRATCH, RU.PCBNAME)
TARGET = ("/ACC_3V3_EN", "/01_POWER_TREE/ACC_3V3_ILIM",
          "/01_POWER_TREE/ACC_POWER_FAULT_N")

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
    base_drc,_=RU.drc(IR.AUTH,"u20local_base",SCRATCH)
    impact=json.load(open(os.path.join(SP,"u20_impact_map_051.json"),encoding="utf-8"))["least_impact_candidate"]
    allowed=[]
    for x in impact["expanded_pad_envelope_copper"]:
        if x["kind"]=="track" and x["net"] in TARGET[:2]:
            ends=tuple(sorted(tuple(round(v*1e6) for v in p) for p in (x["start_mm"],x["end_mm"])))
            allowed.append(("T",x["net"],x["layer"],ends,round(x["width_mm"]*1e6)))
    b=pcbnew.LoadBoard(PCB); removed=[]
    for t in list(b.GetTracks()):
        if sig(t) in allowed:
            removed.append(sig(t)); b.RemoveNative(t)
    u=b.FindFootprintByReference("U20"); p=u.GetPosition()
    u.SetOrientationDegrees(u.GetOrientationDegrees()+180)
    u.SetPosition(pcbnew.VECTOR2I(p.x,p.y+500000)); b.Save(PCB)
    qb=QR.QBoard(PCB); IR.inject_existing_via_obstacles(qb)
    # The fault pad owns the scarce U20 escape.  Reserve it first, then replay
    # the two controls around that accepted local reservation.
    routes=route_group(qb,"ACC_POWER_FAULT_N")+route_group(qb,"ACC_3V3_CTL")
    qb.save(PCB); result=pcbnew.LoadBoard(PCB); result_cu=copper(result)
    missing=base_cu-result_cu; added=result_cu-base_cu
    forbidden_missing=missing-collections.Counter(allowed)
    forbidden_added=[s for s in added.elements() if s[1] not in TARGET]
    broken=sorted(base_pairs-connected_pairs(result))
    opens={n:open_edges(result,n) for n in TARGET}
    drc,_=RU.drc(PCB,"u20local_result",SCRATCH)
    worse={k:[base_drc.get(k,0),drc.get(k,0)] for k in sorted(set(base_drc)|set(drc)) if drc.get(k,0)>base_drc.get(k,0)}
    passed=(len(removed)==8 and collections.Counter(removed)==collections.Counter(allowed)
            and all(r["ok"] for r in routes) and not forbidden_missing and not forbidden_added
            and not broken and all(v==0 for v in opens.values()) and not worse)
    ev={"schema_version":1,"decision":"D-350","authoritative_board_sha256":auth_sha,
        "authoritative_unchanged":hashlib.sha256(open(IR.AUTH,"rb").read()).hexdigest()==auth_sha,
        "pose":{"rotation_deg":180,"offset_mm":[0,0.5]},"allowed_replacement_items":len(allowed),
        "removed_items":len(removed),"routes":routes,"missing_items_total":sum(missing.values()),
        "forbidden_missing_count":sum(forbidden_missing.values()),"forbidden_added_count":len(forbidden_added),
        "accepted_pairs_broken":broken,"open_edges_after":opens,"drc_before":dict(base_drc),
        "drc_after":dict(drc),"drc_worse":worse,"promotion_candidate":passed,
        "conclusion":"local_replacement_pass" if passed else "local_replacement_failed"}
    json.dump(ev,open(OUT,"w",encoding="utf-8"),indent=2,sort_keys=True)
    print(json.dumps(ev,indent=2,sort_keys=True)); return 0 if passed else 1

if __name__=="__main__": sys.exit(main())
