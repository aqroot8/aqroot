#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D-678 -- READ-ONLY: remove named copper from a PRIVATE COPY of the authority,
refill with pcbnew.ZONE_FILLER (KiCad's own filler) and report the
/01_POWER_TREE/BQ25185_SYS pad partition.  The authority is never written.
EDIT AND FILL ARE SEPARATE PROCESSES: removing a track and then filling in the
same interpreter segfaults KiCad 10.0.5 (screen_pour_cut_blame.py records the
same limit).  Driver: python3 evidence/d678-pour-cut-probe.py NAME SPEC.json
"""
import json, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo")
NET = "/01_POWER_TREE/BQ25185_SYS"

def edit():
    import pcbnew
    board, spec = sys.argv[2], Path(sys.argv[3])
    want = json.loads(spec.read_text())
    b = pcbnew.LoadBoard(board)
    def key(p): return (round(p.x/1e6,4), round(p.y/1e6,4))
    gone = []; doomed = []
    for w in want:
        hits = []
        for t in b.GetTracks():
            if t.GetNetname() != w["net"]: continue
            if w.get("via"):
                if t.GetClass()!="PCB_VIA": continue
                if key(t.GetStart())!=tuple(w["at_mm"]): continue
            else:
                if t.GetClass()!="PCB_TRACK": continue
                if b.GetLayerName(t.GetLayer())!=w["layer"]: continue
                a,c = key(t.GetStart()), key(t.GetEnd())
                if {a,c} != {tuple(w["a_mm"]),tuple(w["b_mm"])}: continue
                if abs(t.GetWidth()-int(round(w["width_mm"]*1e6)))>500: continue
            hits.append(t)
        if not hits:
            raise SystemExit("no match: %r" % w)
        gone.append((w.get("net"), len(hits), [str(t.m_Uuid.AsString()) for t in hits]))
        doomed.extend(hits)
    for t in doomed: b.Remove(t)
    b.Save(board)
    print(json.dumps(gone))
    return 0

def fill():
    import pcbnew
    board, out = sys.argv[2], Path(sys.argv[3])
    b = pcbnew.LoadBoard(board)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    b.Save(board)
    conn = b.GetConnectivity()
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()==NET and p.GetNumber():
                pads[f.GetReference()+"."+p.GetNumber()]=p
    seen, parts = set(), []
    for k,p in pads.items():
        if k in seen: continue
        grp = sorted({i.GetParentFootprint().GetReference()+"."+i.GetNumber()
                      for i in conn.GetConnectedItems(p) if i.GetClass()=="PAD"} | {k})
        grp = [g for g in grp if g in pads]
        seen |= set(grp); parts.append(sorted(grp))
    out.write_text(json.dumps(dict(partition=sorted(parts), clusters=len(parts))))
    return 0

if __name__ == "__main__":
    if sys.argv[1]=="--edit": sys.exit(edit())
    if sys.argv[1]=="--fill": sys.exit(fill())
    # driver: cut.py NAME spec.json
    name, spec = sys.argv[1], Path(sys.argv[2])
    work = HERE/name; shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    for ext in (".kicad_pcb",".kicad_pro",".kicad_dru",".kicad_prl"):
        p = SRC/("aqroot-Beta-v2"+ext)
        if p.exists(): shutil.copy(p, work/p.name)
    brd = str(work/"aqroot-Beta-v2.kicad_pcb")
    if json.loads(spec.read_text()):
        r=subprocess.run([sys.executable,__file__,"--edit",brd,str(spec)],capture_output=True,text=True)
        if r.returncode: print(r.stdout,r.stderr); sys.exit(1)
        print("removed:", [l for l in r.stdout.splitlines() if l.startswith("[")])
    out = work/"part.json"
    r=subprocess.run([sys.executable,__file__,"--fill",brd,str(out)],capture_output=True,text=True)
    if r.returncode: print(r.stdout,r.stderr); sys.exit(1)
    d=json.loads(out.read_text())
    print(name, "clusters", d["clusters"])
    for g in d["partition"]: print("   ", g)
