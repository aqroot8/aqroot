import sys, math, pcbnew
B,NET=sys.argv[1],sys.argv[2]
x0,y0,x1,y1=map(float,sys.argv[3].split(','))
D=float(sys.argv[4]); DR=float(sys.argv[5]); TC=float(sys.argv[6]); PC=float(sys.argv[7])
b=pcbnew.LoadBoard(B)
def d_ps(px,py,a,bq):
    vx,vy=bq[0]-a[0],bq[1]-a[1]; L2=vx*vx+vy*vy
    t=0 if L2==0 else max(0,min(1,((px-a[0])*vx+(py-a[1])*vy)/L2))
    return math.hypot(px-(a[0]+t*vx),py-(a[1]+t*vy))
objs=[]; holes=[]
for t in b.GetTracks():
    if t.GetNetname()==NET: continue
    s,e=t.GetStart(),t.GetEnd()
    if t.Type()==pcbnew.PCB_VIA_T:
        objs.append((t.GetNetname(),(s.x/1e6,s.y/1e6),(s.x/1e6,s.y/1e6),t.GetWidth()/2e6,TC))
        holes.append(((s.x/1e6,s.y/1e6),t.GetDrillValue()/2e6,'via'+t.GetNetname()))
    else: objs.append((t.GetNetname(),(s.x/1e6,s.y/1e6),(e.x/1e6,e.y/1e6),t.GetWidth()/2e6,TC))
for fp in b.GetFootprints():
    for pd in fp.Pads():
        p,sz=pd.GetPosition(),pd.GetSize()
        if pd.GetNetname()!=NET:
            objs.append((f"{fp.GetReference()}.{pd.GetNumber()}",(p.x/1e6,p.y/1e6),(p.x/1e6,p.y/1e6),max(sz.x,sz.y)/2e6,PC))
        if pd.GetDrillSize().x>0:
            holes.append(((p.x/1e6,p.y/1e6),pd.GetDrillSize().x/2e6,f"hole{fp.GetReference()}.{pd.GetNumber()}"))
res=[]
yy=y0
while yy<=y1:
    xx=x0
    while xx<=x1:
        m=9e9; who=None
        for lbl,p,q,r,clr in objs:
            d=d_ps(xx,yy,p,q)-r-clr-D/2
            if d<m: m=d; who=lbl
        for (hp,hr,hl) in holes:
            d=math.hypot(xx-hp[0],yy-hp[1])-hr-0.25-DR/2
            if d<m: m=d; who=hl
        if m>0: res.append((round(m,3),round(xx,3),round(yy,3),who))
        xx+=0.05
    yy+=0.05
res.sort(reverse=True)
for r in res[:25]: print(r)
print("legal sites:",len(res))
