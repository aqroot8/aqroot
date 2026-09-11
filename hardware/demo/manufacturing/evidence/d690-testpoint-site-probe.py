"""Score candidate B-side sites for a 1-pad test point: min clearance to
foreign copper, courtyard overlaps (both sides, THT-safe), and hole gaps."""
import sys, math, itertools
import pcbnew
SRC="/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
MM=1e6
REF=sys.argv[1]
XS=[float(v) for v in sys.argv[2].split(",")]
YS=[float(v) for v in sys.argv[3].split(",")]
SKIP=set(sys.argv[4].split(",")) if len(sys.argv)>4 else set()
b=pcbnew.LoadBoard(SRC)
fp=b.FindFootprintByReference(REF)
mynets={p.GetNetname() for p in fp.Pads()}|{""}
pad=list(fp.Pads())[0]
sz=max(pad.GetSizeX(),pad.GetSizeY())
cy=fp.GetCourtyard(pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu).BBox()
cw,ch=cy.GetWidth(),cy.GetHeight()
obs=[]
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA":
        for L in t.GetLayerSet().CuStack(): obs.append((t.GetNetname(),{L},t.GetEffectiveShape(L)))
    else: obs.append((t.GetNetname(),{t.GetLayer()},t.GetEffectiveShape(t.GetLayer())))
for f in b.GetFootprints():
    if f.GetReference()==REF or f.GetReference() in SKIP: continue
    for p in f.Pads():
        for L in p.GetLayerSet().CuStack():
            obs.append((f.GetReference()+"."+p.GetNumber()+" "+p.GetNetname(),{L},p.GetEffectiveShape(L)))
courts=[]
for f in b.GetFootprints():
    if f.GetReference()==REF or f.GetReference() in SKIP: continue
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        c=f.GetCourtyard(lay)
        if c.OutlineCount(): courts.append((f.GetReference(),c.BBox()))
pl=set(pad.GetLayerSet().CuStack())
rows=[]
for x,y in itertools.product(XS,YS):
    px,py=int(round(x*MM)),int(round(y*MM))
    shp=pcbnew.SHAPE_RECT(pcbnew.VECTOR2I(px-int(sz//2),py-int(sz//2)),
                          int(sz),int(sz))
    worst,who=1e9,None
    for onet,ol,osh in obs:
        if onet.split(" ")[-1] in mynets or not (pl&ol): continue
        hi=int(0.60*MM)
        if not shp.Collide(osh,hi): continue
        lo=0
        while hi-lo>5000:
            mid=(lo+hi)//2
            if shp.Collide(osh,mid): hi=mid
            else: lo=mid
        if lo<worst: worst,who=lo,onet
    bb=pcbnew.BOX2I(pcbnew.VECTOR2I(px-cw//2,py-ch//2),pcbnew.VECTOR2I(cw,ch))
    clash=sorted({r for r,c in courts if bb.Intersects(c)})
    rows.append((min(worst,int(0.60*MM))/MM,x,y,who,clash))
rows.sort(reverse=True)
for w,x,y,who,cl in rows[:25]:
    print("(%6.2f,%6.2f) clr %6.4f  %-26s courts %s"%(x,y,w,who or "-", cl or "CLEAR"))
