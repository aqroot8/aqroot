import sys, pcbnew
B=sys.argv[1]; X=float(sys.argv[2]); Y=float(sys.argv[3])
DIA=int(sys.argv[4]); DRL=int(sys.argv[5])
b=pcbnew.LoadBoard(B)
n=0
for t in b.GetTracks():
    if t.GetClass()!='PCB_VIA': continue
    p=t.GetStart()
    if abs(p.x-X*1e6)<1000 and abs(p.y-Y*1e6)<1000:
        print("via %s %.2f/%.2f -> %.2f/%.2f"%(t.GetNetname(),t.GetWidth()/1e6,t.GetDrill()/1e6,DIA/1e6,DRL/1e6))
        t.SetWidth(DIA); t.SetDrill(DRL); n+=1
if not n: raise SystemExit("no via at that point")
pcbnew.SaveBoard(B,b); print("saved",n)
