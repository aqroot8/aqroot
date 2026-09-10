#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D-678 -- READ-ONLY: rotate/move a footprint and/or remove copper on a PRIVATE
COPY, refill, and report the /01_POWER_TREE/BQ25185_SYS pad partition.
REMOVALS RUN BEFORE THE ROTATION AND BEFORE THE SAVE, because KiCad reassigns a
track's net when a rotated pad lands on its endpoint -- which is how a GND stub
silently became SYS copper the first time this was tried.
"""
import json, shutil, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo")
NET="/01_POWER_TREE/BQ25185_SYS"
def edit():
    import pcbnew
    board,spec=sys.argv[2],Path(sys.argv[3])
    d=json.loads(spec.read_text())
    b=pcbnew.LoadBoard(board)
    def key(p): return (round(p.x/1e6,4),round(p.y/1e6,4))
    for r in d.get("rotate",[]):
        f=b.FindFootprintByReference(r["ref"])
        f.SetOrientationDegrees(f.GetOrientationDegrees()+r["deg"])
        print("rot",r["ref"],f.GetOrientationDegrees(),[(p.GetNumber(),round(p.GetPosition().x/1e6,3),round(p.GetPosition().y/1e6,3),p.GetNetname()) for p in f.Pads()])
    for m in d.get("move",[]):
        f=b.FindFootprintByReference(m["ref"])
        f.SetPosition(pcbnew.VECTOR2I(int(m["to_mm"][0]*1e6),int(m["to_mm"][1]*1e6)))
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
    b.Save(board); print("removed",len(doomed)); return 0
def fill():
    import pcbnew
    board,out=sys.argv[2],Path(sys.argv[3])
    b=pcbnew.LoadBoard(board)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity(); b.Save(board)
    conn=b.GetConnectivity(); pads={}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()==NET and p.GetNumber(): pads[f.GetReference()+"."+p.GetNumber()]=p
    seen,parts=set(),[]
    for k,p in pads.items():
        if k in seen: continue
        grp=sorted({i.GetParentFootprint().GetReference()+"."+i.GetNumber() for i in conn.GetConnectedItems(p) if i.GetClass()=="PAD"}|{k})
        grp=[g for g in grp if g in pads]; seen|=set(grp); parts.append(sorted(grp))
    out.write_text(json.dumps(dict(partition=sorted(parts),clusters=len(parts)))); return 0
if __name__=="__main__":
    if sys.argv[1]=="--edit": sys.exit(edit())
    if sys.argv[1]=="--fill": sys.exit(fill())
    name,spec=sys.argv[1],Path(sys.argv[2])
    work=HERE/name; shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    for ext in (".kicad_pcb",".kicad_pro",".kicad_dru",".kicad_prl"):
        p=SRC/("aqroot-Beta-v2"+ext)
        if p.exists(): shutil.copy(p,work/p.name)
    brd=str(work/"aqroot-Beta-v2.kicad_pcb")
    r=subprocess.run([sys.executable,__file__,"--edit",brd,str(spec)],capture_output=True,text=True)
    print("\n".join(l for l in r.stdout.splitlines() if not l.startswith("./kicad")))
    if r.returncode: print(r.stderr[-800:]); sys.exit(1)
    out=work/"part.json"
    r=subprocess.run([sys.executable,__file__,"--fill",brd,str(out)],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-800:]); sys.exit(1)
    d=json.loads(out.read_text()); print(name,"clusters",d["clusters"])
    for g in d["partition"]: print("   ",g)
