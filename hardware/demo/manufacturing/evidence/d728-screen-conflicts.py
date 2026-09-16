import sys, math, json, pcbnew
B,LAYERN,NET=sys.argv[1],sys.argv[2],sys.argv[3]
poly=json.load(open(sys.argv[4])); W=float(sys.argv[5]); TC=float(sys.argv[6]); PC=float(sys.argv[7])
b=pcbnew.LoadBoard(B); layer=b.GetLayerID(LAYERN)
segs=[(tuple(poly[i]),tuple(poly[i+1])) for i in range(len(poly)-1)]
def d_ps(px,py,ax,ay,bx,by):
    vx,vy=bx-ax,by-ay; L2=vx*vx+vy*vy
    t=0 if L2==0 else max(0,min(1,((px-ax)*vx+(py-ay)*vy)/L2))
    return math.hypot(px-(ax+t*vx),py-(ay+t*vy))
def _cr(o,a,bq):
    return (a[0]-o[0])*(bq[1]-o[1])-(a[1]-o[1])*(bq[0]-o[0])
def ss(p,q,r,s):
    d1=_cr(p,q,r); d2=_cr(p,q,s); d3=_cr(r,s,p); d4=_cr(r,s,q)
    if ((d1>0)!=(d2>0)) and ((d3>0)!=(d4>0)): return 0.0
    return min(d_ps(p[0],p[1],*r,*s),d_ps(q[0],q[1],*r,*s),d_ps(r[0],r[1],*p,*q),d_ps(s[0],s[1],*p,*q))
def rs(cx,cy,w,h,a,bq):
    L=math.hypot(bq[0]-a[0],bq[1]-a[1]); n=max(2,int(L/0.01)); best=9e9
    for i in range(n+1):
        t=i/n; px=a[0]+(bq[0]-a[0])*t; py=a[1]+(bq[1]-a[1])*t
        best=min(best,math.hypot(max(abs(px-cx)-w/2,0),max(abs(py-cy)-h/2,0)))
    return best
hits={}
def note(key,d,clr):
    if d<clr+W/2: hits[key]=min(hits.get(key,9e9),round(d,4))
for t in b.GetTracks():
    if t.GetNetname()==NET: continue
    s,e=t.GetStart(),t.GetEnd()
    if t.Type()==pcbnew.PCB_VIA_T:
        if not t.IsOnLayer(layer): continue
        r=t.GetWidth(layer)/2e6; p=(s.x/1e6,s.y/1e6)
        for a,bq in segs: note(('via',t.GetNetname(),round(p[0],3),round(p[1],3)), d_ps(p[0],p[1],*a,*bq)-r, TC)
    else:
        if t.GetLayer()!=layer: continue
        r=t.GetWidth()/2e6; p=(s.x/1e6,s.y/1e6); q=(e.x/1e6,e.y/1e6)
        for a,bq in segs: note(('trk',t.GetNetname(),round(p[0],3),round(p[1],3),round(q[0],3),round(q[1],3)), ss(p,q,a,bq)-r, TC)
for fp in b.GetFootprints():
    for pd in fp.Pads():
        if pd.GetNetname()==NET: continue
        p,sz=pd.GetPosition(),pd.GetSize(); w_,h_=sz.x/1e6,sz.y/1e6
        ang=abs(pd.GetOrientationDegrees())%180
        if abs(ang-90)<1: w_,h_=h_,w_
        if pd.IsOnLayer(layer):
            for a,bq in segs: note(('pad',f"{fp.GetReference()}.{pd.GetNumber()}",pd.GetNetname()), rs(p.x/1e6,p.y/1e6,w_,h_,a,bq), PC)
        if pd.GetDrillSize().x>0:
            rr=pd.GetDrillSize().x/2e6
            for a,bq in segs: note(('hole',f"{fp.GetReference()}.{pd.GetNumber()}",pd.GetNetname()), rs(p.x/1e6,p.y/1e6,0,0,a,bq)-rr, max(TC,PC))
for k,v in sorted(hits.items(), key=lambda kv: kv[1]): print(v,k)
