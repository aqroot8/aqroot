#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D-678 -- READ-ONLY: build a candidate on a PRIVATE COPY of the authority --
remove copper, ADD barrels or tracks, ROTATE or TRANSLATE footprints -- refill
and DRC it with the real `kicad-cli pcb drc --refill-zones --severity-all
--schematic-parity`, and report the DRC classes beside the
/01_POWER_TREE/BQ25185_SYS pad partition, the pour outlines, and WHICH FILLED
ISLAND OF ITS OWN NET each named land ends up sitting on.

REMOVALS RUN BEFORE THE ROTATION AND BEFORE THE SAVE, because KiCad reassigns a
track's net when a rotated pad lands on its endpoint -- which is how a GND stub
silently became SYS copper the first time this was tried.

    python3 evidence/d678-candidate-drc-probe.py NAME SPEC.json
"""
import json, shutil, subprocess, sys, collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo")
NET="/01_POWER_TREE/BQ25185_SYS"
def edit():
    import pcbnew
    board,spec=sys.argv[2],Path(sys.argv[3])
    d=json.loads(spec.read_text()); b=pcbnew.LoadBoard(board)
    def key(p): return (round(p.x/1e6,4),round(p.y/1e6,4))
    doomed=[]
    for w in d.get("remove",[]):
        hits=[]
        for t in b.GetTracks():
            if t.GetNetname()!=w["net"]: continue
            if w.get("via"):
                if t.GetClass()!="PCB_VIA" or key(t.GetStart())!=tuple(w["at_mm"]): continue
            else:
                if t.GetClass()!="PCB_TRACK": continue
                if b.GetLayerName(t.GetLayer())!=w["layer"]: continue
                if {key(t.GetStart()),key(t.GetEnd())}!={tuple(w["a_mm"]),tuple(w["b_mm"])}: continue
            hits.append(t)
        if not hits: raise SystemExit("no match %r"%w)
        doomed+=hits
    for t in doomed: b.Remove(t)
    print("removed",len(doomed))
    for r in d.get("rotate",[]):
        f=b.FindFootprintByReference(r["ref"]); f.SetOrientationDegrees(f.GetOrientationDegrees()+r["deg"])
    for m in d.get("move",[]):
        f=b.FindFootprintByReference(m["ref"])
        f.Move(pcbnew.VECTOR2I(int(round(m["dx_mm"]*1e6)),int(round(m["dy_mm"]*1e6))))
    for v in d.get("add_via",[]):
        q=pcbnew.PCB_VIA(b)
        q.SetPosition(pcbnew.VECTOR2I(int(round(v["at_mm"][0]*1e6)),int(round(v["at_mm"][1]*1e6))))
        q.SetWidth(int(round(v["dia_mm"]*1e6))); q.SetDrill(int(round(v["drill_mm"]*1e6)))
        q.SetViaType(pcbnew.VIATYPE_THROUGH)
        q.SetLayerPair(b.GetLayerID("F.Cu"), b.GetLayerID("B.Cu"))
        q.SetNetCode(b.GetNetsByName()[v["net"]].GetNetCode()); b.Add(q)
    for m in d.get("add_track",[]):
        t=pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(int(m["a_mm"][0]*1e6),int(m["a_mm"][1]*1e6)))
        t.SetEnd(pcbnew.VECTOR2I(int(m["b_mm"][0]*1e6),int(m["b_mm"][1]*1e6)))
        t.SetWidth(int(m["width_mm"]*1e6)); t.SetLayer(b.GetLayerID(m["layer"]))
        t.SetNetCode(b.GetNetsByName()[m["net"]].GetNetCode()); b.Add(t)
    b.Save(board); return 0
def report():
    import pcbnew
    board,out=sys.argv[2],Path(sys.argv[3])
    b=pcbnew.LoadBoard(board); b.BuildConnectivity()
    conn=b.GetConnectivity(); pads={}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()==NET and p.GetNumber(): pads[f.GetReference()+"."+p.GetNumber()]=p
    seen,parts=set(),[]
    for k,p in pads.items():
        if k in seen: continue
        grp=sorted({i.GetParentFootprint().GetReference()+"."+i.GetNumber() for i in conn.GetConnectedItems(p) if i.GetClass()=="PAD"}|{k})
        grp=[g for g in grp if g in pads]; seen|=set(grp); parts.append(sorted(grp))
    outl=[]
    for i in range(b.GetAreaCount()):
        z=b.GetArea(i)
        if z.GetZoneName()!="B /01_POWER_TREE/BQ25185_SYS POUR 1": continue
        sh=z.GetFilledPolysList(pcbnew.B_Cu)
        for k in range(sh.OutlineCount()):
            outl.append(round(abs(sh.Outline(k).Area())/1e12,3))
    # which filled island of its OWN net does each named land sit on?
    lands={}
    for f in b.GetFootprints():
        for p in f.Pads():
            k=f.GetReference()+"."+p.GetNumber()
            if k not in ("C27.1","C27.2","C28.2","U11.4","U11.5","U11.11","C23.1"): continue
            best=None
            for i in range(b.GetAreaCount()):
                z=b.GetArea(i)
                if z.GetIsRuleArea() or z.GetNetname()!=p.GetNetname(): continue
                for lid in z.GetLayerSet().Seq():
                    if not p.IsOnLayer(lid): continue
                    sh=z.GetFilledPolysList(lid)
                    for q in range(sh.OutlineCount()):
                        poly=pcbnew.SHAPE_POLY_SET(); poly.AddOutline(sh.Outline(q))
                        if poly.Contains(p.GetPosition()):
                            a=abs(sh.Outline(q).Area())/1e12
                            best=dict(zone=z.GetZoneName(),layer=b.GetLayerName(lid),
                                      outline=q,area_mm2=round(a,3))
            lands[k]=dict(net=p.GetNetname(),island=best)
    out.write_text(json.dumps(dict(partition=sorted(parts),clusters=len(parts),
                                   pour=sorted(outl,reverse=True),lands=lands)))
    return 0
if __name__=="__main__":
    if sys.argv[1]=="--edit": sys.exit(edit())
    if sys.argv[1]=="--report": sys.exit(report())
    name,spec=sys.argv[1],Path(sys.argv[2])
    work=HERE/name; shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    for ext in (".kicad_pcb",".kicad_pro",".kicad_dru",".kicad_prl",".kicad_sch"):
        p=SRC/("aqroot-Beta-v2"+ext)
        if p.exists(): shutil.copy(p,work/p.name)
    for p in SRC.glob("*.kicad_sch"): shutil.copy(p,work/p.name)
    brd=str(work/"aqroot-Beta-v2.kicad_pcb")
    r=subprocess.run([sys.executable,__file__,"--edit",brd,str(spec)],capture_output=True,text=True)
    print("\n".join(l for l in r.stdout.splitlines() if not l.startswith("./kicad")))
    if r.returncode: print(r.stderr[-900:]); sys.exit(1)
    drc=work/"drc.json"
    q=subprocess.run(["kicad-cli","pcb","drc","--refill-zones","--save-board","--format","json",
                      "--units","mm","--severity-all","--schematic-parity","-o",str(drc),brd],
                     capture_output=True,text=True)
    d=json.loads(drc.read_text())
    c=collections.Counter(v["type"] for v in d.get("violations",[]))
    print("drc exit",q.returncode,"types",dict(c),"unconnected",len(d.get("unconnected_items",[])),
          "parity",len(d.get("schematic_parity",[])))
    for v in d.get("violations",[]):
        if v["type"] in ("shorting_items","clearance","track_dangling","via_dangling","copper_sliver","starved_thermal","hole_clearance"):
            print("   !",v["type"],v.get("description","")[:140])
    out=work/"part.json"
    r=subprocess.run([sys.executable,__file__,"--report",brd,str(out)],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-900:]); sys.exit(1)
    o=json.loads(out.read_text()); print(name,"clusters",o["clusters"],"pour",o["pour"][:3])
    for k,v in sorted((o.get("lands") or {}).items()):
        isl=v["island"]
        print("    %-8s %-28s %s"%(k,v["net"][:28],
              "%s#%d %.3f mm2"%(isl["layer"],isl["outline"],isl["area_mm2"]) if isl else "NO ISLAND"))
