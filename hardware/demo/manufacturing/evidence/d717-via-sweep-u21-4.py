import sys, math, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); DIA=float(sys.argv[2]); R=DIA/2.0
CLR=0.200; SWCLR=0.300
OBJ=[]
for t in b.GetTracks():
    n=t.GetNetname()
    if n=="GND": continue
    if t.Type()==pcbnew.PCB_VIA_T:
        OBJ.append(("via",n,(t.GetPosition().x/1e6,t.GetPosition().y/1e6),None,t.GetWidth()/2e6))
    else:
        OBJ.append(("trk",n,(t.GetStart().x/1e6,t.GetStart().y/1e6),(t.GetEnd().x/1e6,t.GetEnd().y/1e6),t.GetWidth()/2e6))
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname()=="GND": continue
        sz=p.GetSize(); pos=p.GetPosition()
        OBJ.append(("rect",p.GetNetname(),(pos.x/1e6,pos.y/1e6),(sz.x/2e6,sz.y/2e6),0.0))
def worst(px,py):
    w=9e9; who=None
    for kind,net,a,c,hw in OBJ:
        if kind=="rect":
            ddx=max(abs(px-a[0])-c[0],0.0); ddy=max(abs(py-a[1])-c[1],0.0)
            d=math.hypot(ddx,ddy)
        elif c is None: d=math.hypot(px-a[0],py-a[1])-hw
        else:
            dx,dy=c[0]-a[0],c[1]-a[1]; L2=dx*dx+dy*dy
            t=0 if L2==0 else max(0,min(1,((px-a[0])*dx+(py-a[1])*dy)/L2))
            d=math.hypot(px-(a[0]+t*dx),py-(a[1]+t*dy))-hw
        need=SWCLR if (net=="/01_POWER_TREE/ACC_5V_LX" and kind=="trk") else CLR
        m=d-R-need
        if m<w: w=m; who=(net,kind,round(d,4))
    return w,who
# the NEAR box: within 1.2 mm of U21.4's land (58.175..58.851, 39.225..39.575)
best=[]
x=58.0
while x<=60.1:
    y=38.0
    while y<=40.8:
        m,who=worst(x,y); best.append((round(m,4),round(x,3),round(y,3),who)); y+=0.05
    x+=0.05
best.sort(reverse=True)
print("BEST %.3f mm GND via sites in the NEAR box (58.0-60.1, 38.0-40.8):"%DIA)
for r in best[:6]: print("   margin %+.4f at (%.3f,%.3f)  binds on %s"%r)

