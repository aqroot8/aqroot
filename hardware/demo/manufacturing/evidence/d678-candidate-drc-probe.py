#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D-678 -- READ-ONLY: build a candidate (remove copper, then rotate parts) on a
PRIVATE COPY, refill and DRC it with the real `kicad-cli pcb drc
--refill-zones --severity-all --schematic-parity`, and report the DRC classes
beside the /01_POWER_TREE/BQ25185_SYS pad partition and the pour outlines.
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
    out.write_text(json.dumps(dict(partition=sorted(parts),clusters=len(parts),pour=sorted(outl,reverse=True))))
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
    o=json.loads(out.read_text()); print(name,"clusters",o["clusters"],"pour",o["pour"])
    for g in o["partition"]: print("   ",g)
