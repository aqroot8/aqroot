"""Corridor opener v2: rectangular pads, per-object clearance, slack field.
S(cell) = min over objects of (dist - own_radius - required_clearance).
A trunk of width W fits where S >= W/2.
Usage: corridor2.py BOARD LAYER NET x0,y0,x1,y1 SX,SY DX,DY WIDTH TRKCLR PADCLR HARD_CSV
"""
import sys, math, heapq, json, pickle, pcbnew, numpy as np
BOARD,LAYERN,NET=sys.argv[1],sys.argv[2],sys.argv[3]
x0,y0,x1,y1=map(float,sys.argv[4].split(','))
sx,sy=map(float,sys.argv[5].split(',')); dx,dy=map(float,sys.argv[6].split(','))
W=float(sys.argv[7]); TC=float(sys.argv[8]); PC=float(sys.argv[9])
HARD=set(x for x in (sys.argv[10].split(',') if len(sys.argv)>10 else []) if x)
b=pcbnew.LoadBoard(BOARD); layer=b.GetLayerID(LAYERN)
CAP=2.5; g=0.05
nx=int((x1-x0)/g)+1; ny=int((y1-y0)/g)+1
OBJ=[]  # (netname_or_None, label, kind, geom, clr)
for t in b.GetTracks():
    if t.GetNetname()==NET: continue
    s,e=t.GetStart(),t.GetEnd()
    if t.Type()==pcbnew.PCB_VIA_T:
        if not t.IsOnLayer(layer): continue
        OBJ.append((t.GetNetname(),'via:'+t.GetNetname(),'seg',(s.x/1e6,s.y/1e6,s.x/1e6,s.y/1e6,t.GetWidth(layer)/2e6),TC))
    else:
        if t.GetLayer()!=layer: continue
        OBJ.append((t.GetNetname(),'trk:'+t.GetNetname(),'seg',(s.x/1e6,s.y/1e6,e.x/1e6,e.y/1e6,t.GetWidth()/2e6),TC))
for fp in b.GetFootprints():
    for pd in fp.Pads():
        if pd.GetNetname()==NET: continue
        p,sz=pd.GetPosition(),pd.GetSize()
        lbl=f'pad:{fp.GetReference()}.{pd.GetNumber()}'
        w_,h_=sz.x/1e6,sz.y/1e6
        ang=abs(pd.GetOrientationDegrees())%180
        if abs(ang-90)<1: w_,h_=h_,w_
        if pd.IsOnLayer(layer):
            OBJ.append((None,lbl,'rect',(p.x/1e6,p.y/1e6,w_,h_),PC))
        if pd.GetDrillSize().x>0:
            dw,dh=pd.GetDrillSize().x/1e6,pd.GetDrillSize().y/1e6
            OBJ.append((None,'hole:'+lbl,'seg',(p.x/1e6,p.y/1e6,p.x/1e6,p.y/1e6,max(dw,dh)/2.0),max(TC,PC)))
def field(free):
    S=np.full((ny,nx),CAP,np.float32); OWN=np.empty((ny,nx),object)
    for netn,lbl,kind,geom,clr in OBJ:
        if netn is not None and netn in free: continue
        if kind=='seg':
            ax,ay,bx,by,r=geom
            lox,hix=min(ax,bx)-r-clr-CAP,max(ax,bx)+r+clr+CAP
            loy,hiy=min(ay,by)-r-clr-CAP,max(ay,by)+r+clr+CAP
        else:
            cx,cy,w_,h_=geom; r=0
            lox,hix=cx-w_/2-clr-CAP,cx+w_/2+clr+CAP
            loy,hiy=cy-h_/2-clr-CAP,cy+h_/2+clr+CAP
        i0=max(0,int((lox-x0)/g)); i1=min(nx-1,int(math.ceil((hix-x0)/g)))
        j0=max(0,int((loy-y0)/g)); j1=min(ny-1,int(math.ceil((hiy-y0)/g)))
        if i1<i0 or j1<j0: continue
        xs=x0+np.arange(i0,i1+1)*g; ys=y0+np.arange(j0,j1+1)*g
        XX,YY=np.meshgrid(xs,ys)
        if kind=='seg':
            vx,vy=bx-ax,by-ay; L2=vx*vx+vy*vy
            t=np.zeros_like(XX) if L2==0 else np.clip(((XX-ax)*vx+(YY-ay)*vy)/L2,0,1)
            d=np.hypot(XX-(ax+t*vx),YY-(ay+t*vy))-r
        else:
            ddx=np.maximum(np.abs(XX-cx)-w_/2,0); ddy=np.maximum(np.abs(YY-cy)-h_/2,0)
            d=np.hypot(ddx,ddy)
        d=(d-clr).astype(np.float32)
        sub=S[j0:j1+1,i0:i1+1]; m=d<sub; sub[m]=d[m]
        o=OWN[j0:j1+1,i0:i1+1]; tup=np.empty((),object); tup[()]=(netn,lbl); o[m]=tup
    return S,OWN
def cell(x,y): return (int(round((y-y0)/g)), int(round((x-x0)/g)))
def search(S,OWN,half):
    FREE=S>=half; s=cell(sx,sy); t=cell(dx,dy); INF=float('inf')
    def hard(o): return o is None or o[0] is None or o[0] in HARD
    start=(s[0],s[1],0 if FREE[s] else 1)
    dist={start:(0.0 if FREE[s] else 1.0)}; pq=[(dist[start],start)]; prev={}; endst=None
    while pq:
        d,u=heapq.heappop(pq)
        if d>dist.get(u,INF)+1e-12: continue
        uj,ui,ub=u
        if (uj,ui)==t: endst=u; break
        for dj,di in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            vj,vi=uj+dj,ui+di
            if not(0<=vj<ny and 0<=vi<nx): continue
            vb=0 if FREE[vj,vi] else 1
            if vb and hard(OWN[vj,vi]): continue
            c=d+(1.4142 if dj and di else 1.0)*g*1e-4
            if vb and (not ub or OWN[vj,vi]!=OWN[uj,ui]): c+=1.0
            v=(vj,vi,vb)
            if c<dist.get(v,INF)-1e-12: dist[v]=c; prev[v]=u; heapq.heappush(pq,(c,v))
    if endst is None: return None,None
    path=[];u=endst
    while True:
        path.append(u)
        if u==start: break
        u=prev[u]
    path.reverse()
    cross=[]
    for (j,i,bf) in path:
        if bf:
            o=OWN[j,i]
            if not cross or cross[-1][0]!=o[1]: cross.append((o[1],o[0],round(x0+i*g,2),round(y0+j*g,2)))
    return cross,path
free=set(); half=W/2.0
for it in range(12):
    S,OWN=field(free)
    cross,path=search(S,OWN,half)
    if cross is None: print("NO PATH iter",it,sorted(free)); sys.exit(1)
    print(f"iter {it}: crossings={len(cross)} free={sorted(free)}")
    for c in cross: print("    ",c)
    if not cross: break
    nf=set(c[1] for c in cross if c[1])
    if nf<=free: print("STUCK"); sys.exit(1)
    free|=nf
for cand in sorted(free):
    trial=free-{cand}
    S2,O2=field(trial); c2,_=search(S2,O2,half)
    if c2 is not None and not c2: free=trial
S,OWN=field(free)
print("MINIMAL free set:",sorted(free))
np.save('/home/aqroot8/aqroot-demo/w-d726/S_final.npy',S)
pickle.dump((x0,y0,g,OWN),open('/home/aqroot8/aqroot-demo/w-d726/OWNS_final.pkl','wb'))
# widest
FREE=S>=half
best=np.full((ny,nx),-1.0,np.float32); s=cell(sx,sy); t=cell(dx,dy)
best[s]=S[s]; pq=[(-float(S[s]),s)]; prev={}
while pq:
    negw,u=heapq.heappop(pq); w=-negw
    if w<best[u]: continue
    if u==t: break
    uj,ui=u
    for dj,di in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        vj,vi=uj+dj,ui+di
        if not(0<=vj<ny and 0<=vi<nx): continue
        nw=min(w,float(S[vj,vi]))
        if nw>best[vj,vi]: best[vj,vi]=nw; prev[(vj,vi)]=u; heapq.heappush(pq,(-nw,(vj,vi)))
print("widest trunk with this free set:",round(float(best[t])*2,3),"mm")
