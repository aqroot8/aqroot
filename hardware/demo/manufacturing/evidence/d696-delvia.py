import pcbnew, sys
src,dst = sys.argv[1], sys.argv[2]
pts = [tuple(float(v) for v in s.split(",")) for s in sys.argv[3:]]
b = pcbnew.LoadBoard(src)
doomed=[]
for t in b.GetTracks():
    if t.GetClass()!="PCB_VIA": continue
    p=t.GetPosition()
    for x,y in pts:
        if abs(p.x/1e6-x)<0.005 and abs(p.y/1e6-y)<0.005:
            doomed.append(t); print("del via",t.GetNetname(),x,y); break
for t in doomed: b.RemoveNative(t)
b.BuildConnectivity()
pcbnew.SaveBoard(dst,b)
