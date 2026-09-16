import sys, json
import pcbnew
BRD=sys.argv[1]; DROP_ACC = len(sys.argv)>2 and sys.argv[2]=='drop_acc'
b=pcbnew.LoadBoard(BRD)
n=m=0
for t in list(b.GetTracks()):
    nn=t.GetNetname()
    if nn=='/09_COMMUNITY_HEADER/EXT_SCL_BUF': b.RemoveNative(t); n+=1
    elif DROP_ACC and nn=='/ACC_PWR_EN': b.RemoveNative(t); m+=1
net=b.FindNet('/01_POWER_TREE/BQ25185_SYS')
for x0,y0,x1,y1,w in [(57.300,38.050,57.000,38.500,0.500),
                      (57.000,38.500,57.000,39.400,0.500)]:
    t=pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(int(x0*1e6),int(y0*1e6))); t.SetEnd(pcbnew.VECTOR2I(int(x1*1e6),int(y1*1e6)))
    t.SetWidth(int(w*1e6)); t.SetLayer(pcbnew.B_Cu); t.SetNet(net); b.Add(t)
b.Save(BRD)
b=pcbnew.LoadBoard(BRD); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(BRD)
print(json.dumps({"ext_scl_buf_removed":n,"acc_pwr_en_removed":m,"sys_track":"L4.1->U21.3 0.500mm"}))
