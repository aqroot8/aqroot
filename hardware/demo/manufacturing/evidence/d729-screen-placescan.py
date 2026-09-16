"""Where can REF go? scan candidate positions; reject courtyard/bbox overlap and pad collisions."""
import sys, math, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); REF=sys.argv[2]
x0,y0,x1,y1=map(float,sys.argv[3].split(','))
ANCHOR=tuple(map(float,sys.argv[4].split(','))) if len(sys.argv)>4 else None
fp=b.FindFootprintByReference(REF)
p0=fp.GetPosition(); bb=fp.GetBoundingBox(False,False)
w=(bb.GetRight()-bb.GetLeft())/1e6; h=(bb.GetBottom()-bb.GetTop())/1e6
ox=(bb.GetLeft()+bb.GetRight())/2e6 - p0.x/1e6
oy=(bb.GetTop()+bb.GetBottom())/2e6 - p0.y/1e6
others=[]
for f in b.GetFootprints():
    if f.GetReference()==REF: continue
    if f.GetLayer()!=fp.GetLayer(): continue
    q=f.GetBoundingBox(False,False)
    others.append((f.GetReference(),q.GetLeft()/1e6,q.GetTop()/1e6,q.GetRight()/1e6,q.GetBottom()/1e6))
holes=[]
for f in b.GetFootprints():
    for pd in f.Pads():
        if pd.GetDrillSize().x>0:
            pp=pd.GetPosition(); holes.append((pp.x/1e6,pp.y/1e6,pd.GetDrillSize().x/2e6))
res=[]
yy=y0
while yy<=y1:
    xx=x0
    while xx<=x1:
        L,T,R,B = xx+ox-w/2, yy+oy-h/2, xx+ox+w/2, yy+oy+h/2
        if L<0.5 or T<0.5 or R>71.5 or B>147.5: xx+=0.25; continue
        bad=None
        for (r,l2,t2,r2,b2) in others:
            if not (R<l2 or L>r2 or B<t2 or T>b2): bad=r; break
        if bad is None:
            for (hx,hy,hr) in holes:
                if L-0.3<hx<R+0.3 and T-0.3<hy<B+0.3: bad='hole'; break
        if bad is None:
            d=math.hypot(xx-ANCHOR[0],yy-ANCHOR[1]) if ANCHOR else 0
            res.append((round(d,2),round(xx,2),round(yy,2)))
        xx+=0.25
    yy+=0.25
res.sort()
for r in res[:20]: print(r)
print("free positions:",len(res))
