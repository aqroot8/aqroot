import pcbnew, sys
B = sys.argv[1] if len(sys.argv)>1 else "w/d720/c1/aqroot-Beta-v2.kicad_pcb"
b = pcbnew.LoadBoard(B)
ADD = [
  # net, x0,y0,x1,y1,w,layer
  ("/04_SPI_B_RADIOS_NFC/NFC_VDD_RF", 34.750, 27.725, 34.750, 26.900, 0.200, pcbnew.B_Cu),
  ("/NFC_SUPPLY",                     32.750, 27.725, 32.750, 26.900, 0.300, pcbnew.B_Cu),
]
VIAS = [
  ("/04_SPI_B_RADIOS_NFC/NFC_VDD_RF", 34.750, 26.900, 0.600, 0.300),
  ("/NFC_SUPPLY",                     32.750, 26.900, 0.600, 0.300),
]
for net,x0,y0,x1,y1,w,lay in ADD:
    t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(x0*1e6),int(y0*1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(x1*1e6),int(y1*1e6))); t.SetWidth(int(w*1e6))
    t.SetLayer(lay); t.SetNet(b.FindNet(net)); b.Add(t)
for net,x,y,d,dr in VIAS:
    v=pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(x*1e6),int(y*1e6)))
    v.SetWidth(int(d*1e6)); v.SetDrill(int(dr*1e6)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(b.FindNet(net)); b.Add(v)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(B)
print("added", len(ADD),"tracks", len(VIAS),"vias")
