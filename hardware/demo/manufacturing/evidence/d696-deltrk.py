import pcbnew, sys
src,dst=sys.argv[1],sys.argv[2]
pts=[tuple(float(v) for v in s.split(",")) for s in sys.argv[3:]]
b=pcbnew.LoadBoard(src)
doomed=[]
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA": continue
    s,e=t.GetStart(),t.GetEnd()
    for x,y in pts:
        if (abs(s.x/1e6-x)<0.01 and abs(s.y/1e6-y)<0.01) or (abs(e.x/1e6-x)<0.01 and abs(e.y/1e6-y)<0.01):
            doomed.append(t); print("del trk",t.GetNetname(),round(s.x/1e6,3),round(s.y/1e6,3),'->',round(e.x/1e6,3),round(e.y/1e6,3)); break
for t in doomed: b.RemoveNative(t)
b.BuildConnectivity(); pcbnew.SaveBoard(dst,b)
