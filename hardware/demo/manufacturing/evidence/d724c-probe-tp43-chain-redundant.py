#!/usr/bin/env python3
"""PROBE: is ACC_DETECT_N_HDR's TP43 horizontal chain REDUNDANT, and does
removing it open the F.Cu crossing window at (56.1..57.2, 35..37)?

TP43 reaches R64.2 twice: once along y = 36.000 and once along the net's own
(56.000,33.525) -> (59.675,37.200) diagonal.  Replace the chain with ONE short
stub from TP43 onto that diagonal and the horizontal is free.
"""
import sys, json
import pcbnew
BRD = sys.argv[1]; LOG = {}
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(BRD)
KILL = [((55.731,35.330),(56.400,36.000)),
        ((56.400,36.000),(57.550,36.000)),
        ((57.550,36.000),(58.975,37.425)),
        ((59.681538,38.119292),(58.975,37.425))]
def near(t,a,c,tol=3000):
    s,e=t.GetStart(),t.GetEnd()
    for (p,q) in ((s,e),(e,s)):
        if abs(p.x-nm(a[0]))<=tol and abs(p.y-nm(a[1]))<=tol \
           and abs(q.x-nm(c[0]))<=tol and abs(q.y-nm(c[1]))<=tol: return True
    return False
killed=[]
for t in list(b.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T: continue
    for (a,c) in KILL:
        if near(t,a,c):
            killed.append([round(t.GetStart().x/1e6,3),round(t.GetStart().y/1e6,3),
                           round(t.GetEnd().x/1e6,3),round(t.GetEnd().y/1e6,3)])
            b.RemoveNative(t); break
LOG["removed"]=killed
# TP43 -> the net's own diagonal, one segment, F.Cu
t=pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(nm(55.731),nm(35.330)))
t.SetEnd(pcbnew.VECTOR2I(nm(56.700),nm(34.225)))
t.SetWidth(nm(0.200)); t.SetLayer(pcbnew.F_Cu)
t.SetNet(b.FindNet("/09_COMMUNITY_HEADER/ACC_DETECT_N_HDR")); b.Add(t)
b.Save(BRD)
for _ in range(2):
    b=pcbnew.LoadBoard(BRD); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(BRD)
print(json.dumps(LOG,indent=1))
