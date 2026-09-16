#!/usr/bin/env python3
"""D-725 STAGE 2 -- the SYS feed, and the TPS61023 boost block it enables."""
import sys, json
import pcbnew
SRC, DST = sys.argv[1], sys.argv[2]
LOG = {}
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(SRC)
LAY = {"F": pcbnew.F_Cu, "In2": pcbnew.In2_Cu, "In3": pcbnew.In3_Cu, "B": pcbnew.B_Cu}
def net(sfx):
    for n in b.GetNetsByName().keys():
        if str(n) == sfx or str(n).endswith("/" + sfx): return str(n)
    raise SystemExit("no net " + sfx)
def kill(pairs, tol=4000):
    out=[]
    for t in list(b.GetTracks()):
        if t.Type()==pcbnew.PCB_VIA_T: continue
        s,e=t.GetStart(),t.GetEnd()
        for (a,c) in pairs:
            for (p,q) in ((s,e),(e,s)):
                if abs(p.x-nm(a[0]))<=tol and abs(p.y-nm(a[1]))<=tol \
                   and abs(q.x-nm(c[0]))<=tol and abs(q.y-nm(c[1]))<=tol:
                    out.append([t.GetNetname().split("/")[-1],round(s.x/1e6,3),round(s.y/1e6,3),
                                round(e.x/1e6,3),round(e.y/1e6,3)]); b.RemoveNative(t); break
            else: continue
            break
    return out
def trk(n,x0,y0,x1,y1,w,l="B"):
    t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(nm(x0),nm(y0)))
    t.SetEnd(pcbnew.VECTOR2I(nm(x1),nm(y1))); t.SetWidth(nm(w)); t.SetLayer(LAY[l])
    t.SetNet(b.FindNet(n)); b.Add(t)
def via(n,x,y,d,dr):
    v=pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(nm(x),nm(y)))
    v.SetWidth(nm(d)); v.SetDrill(nm(dr)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(b.FindNet(n)); v.SetIsFree(False); b.Add(v)

SYS=net("BQ25185_SYS"); LX=net("ACC_5V_LX"); RAW=net("ACC_5V_RAW"); DET=net("ACC_DETECT_N_HDR")

# ---------------------------------------------------------------- 6
# THE SYS FEED.  With the pocket emptied the F.Cu corridor from the trunk
# vertex (52.000,36.700) is 1.621 mm wide the whole way to x = 56.9, pinched
# only at its own origin by ACC_5V_RAW's barrel.  1.000 mm carries 2.19 A at
# IPC-2221B / 1 oz / dT 10 K with 11 % margin; the pair of 0.800/0.400 barrels
# carries about 4.7 A between them.
#
# U21.3 is the IC's BIAS pin, not the power path: on the TPS61023 the inductor
# current flows VIN-rail -> L4 -> SW externally, so L4.1 owes the 2.19 A and
# U21.3 owes only the controller's own supply.  It gets the SYS_MAIN class
# minimum, 0.500 mm.
trk(SYS, 52.000, 36.700, 55.000, 36.200, 1.000, "F")
trk(SYS, 55.000, 36.200, 56.000, 36.200, 1.000, "F")
via(SYS, 55.000, 36.200, 0.800, 0.400)
via(SYS, 56.000, 36.200, 0.800, 0.400)
trk(SYS, 55.000, 36.200, 57.400, 36.200, 1.000, "B")
trk(SYS, 57.150, 37.900, 57.150, 39.250, 0.500, "B")   # L4.1 south edge -> U21.3

# ---------------------------------------------------------------- 7
# SYS POUR 2 is RETIRED.  It was an unfed island whose only job was to supply
# L4.1 and U21.3; a track does that now.  Retiring it is what lets the B GND
# PLANE fill to U21.4, the converter's ground pin.
for z in list(b.Zones()):
    if z.GetZoneName().endswith("BQ25185_SYS POUR 2"):
        LOG["pour2"] = z.GetZoneName(); b.Remove(z)

# ---------------------------------------------------------------- 8
# THE BOOST BLOCK (D-724's candidate, verbatim where it still applies).
LOG["killed"] = kill([
    ((58.700,39.375),(60.600,38.425)),      # U21.4's 1.9 mm B.Cu ground haul
    ((58.5125,40.400),(59.0225,40.400)),    # ACC_5V_RAW neck, level with SW
    ((59.0225,40.400),(60.085,40.475)),
])
# Two GND stitch barrels sat UNDER C65.2's land already, and C65 steps 0.250 mm
# east over them.  A barrel inside an 0805 land wicks solder; both come out
# with their stubs, and the four stitches at (61.4,41.4), (62.0,41.7),
# (62.7,41.4) and (62.8,40.1) keep the pocket bonded.
LOG["c65_pad_vias"] = kill([((62.0,41.0),(61.9,41.0)), ((63.5,39.4),(62.0,41.0)),
                            ((63.5,39.4),(62.4,40.6))])
# R100's old GND escape is a 0.035 mm stub and a barrel under the land it just
# left; both go with the part.
LOG["r100_old_gnd"] = kill([((59.125,32.725),(59.1,32.7))])
for _t in list(b.GetTracks()):
    if _t.Type()!=pcbnew.PCB_VIA_T: continue
    for (_x,_y) in ((61.9,41.0),(62.4,40.6),(59.1,32.7)):
        if abs(_t.GetStart().x-nm(_x))<=3000 and abs(_t.GetStart().y-nm(_y))<=3000:
            b.RemoveNative(_t); break

c65 = b.FindFootprintByReference("C65")
p = c65.GetPosition(); c65.SetPosition(pcbnew.VECTOR2I(p.x+nm(0.250), p.y))
for t in list(b.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T: continue
    for g,s_ in ((t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)):
        q=g()
        if any(abs(q.x-nm(cx))<=3000 and abs(q.y-nm(cy))<=3000
               for (cx,cy) in ((60.085,40.475),(61.985,40.475))):
            s_(pcbnew.VECTOR2I(q.x+nm(0.250), q.y))
trk(RAW, 58.513, 40.500, 59.000, 40.640, 0.250)
trk(RAW, 59.000, 40.640, 59.900, 40.900, 0.400)
trk(RAW, 59.900, 40.900, 60.335, 40.475, 0.400)
trk(LX, 58.513, 39.900, 59.150, 39.900, 0.200)
trk(LX, 59.150, 39.900, 59.700, 39.200, 0.400)
trk(LX, 59.700, 39.200, 60.085, 37.800, 0.400)

# U21.4's ground: SOLID zone connection and a barrel 0.55 mm from the pad.
for pd in b.FindFootprintByReference("U21").Pads():
    if pd.GetNumber()=="4": pd.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
# TWO 0.800/0.400 POWER-class barrels in the L4.1<->L4.2 channel, the widest
# copper U21.4 can reach, plus a 0.500 mm stub.  U21.4 carries the converter's
# full 2.19 A inductor current to ground through the low-side FET, so its
# return is sized from that, not from a signal-ground stitch.
# FOUR 0.800/0.400 POWER-class barrels on 1.200 mm pitch up the whole
# L4.1<->L4.2 channel -- 8.8 A of return into the In1 and In4 GND references,
# right at the pin that carries the converter's full inductor current to
# ground through the low-side FET.  The stitch also RESERVES the channel: a
# 0.600 mm foreign barrel needs its centre in x 58.705..59.095 and 0.900 mm
# from each of these, and at this pitch no such point exists.  That matters --
# one foreign via in this channel severs U21.4 from the B GND PLANE body and
# PP2 then prices a return no fine-pitch land can satisfy.
# (the stitch itself is STAGE 3: KiCad re-assigns a via's net to whatever
#  track it lands on at SAVE time, and EXT_SDA_BUF's OLD In2 run passes
#  0.034 mm from (58.900,35.000) on the board this stage loads.)

# Two ordinary In2 signals cross the L4.1<->L4.2 channel end to end, which is
# why no GND barrel fits in it.  Both are re-laid with a minimal bow that
# rejoins the original line exactly at both ends.
def relay_in2(netname, a, c, pts, w=0.200):
    n=0
    for t in list(b.GetTracks()):
        if t.Type()==pcbnew.PCB_VIA_T or t.GetLayer()!=pcbnew.In2_Cu: continue
        if t.GetNetname()!=netname: continue
        s_,e_=t.GetStart(),t.GetEnd()
        for (p_,q_) in ((s_,e_),(e_,s_)):
            if abs(p_.x-nm(a[0]))<=3000 and abs(p_.y-nm(a[1]))<=3000 \
               and abs(q_.x-nm(c[0]))<=3000 and abs(q_.y-nm(c[1]))<=3000:
                b.RemoveNative(t); n+=1; break
    for i in range(len(pts)-1):
        trk(netname, pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1], w, "In2")
    return n
# XGPIO4 is PROTECTED COPPER and is NOT relaid: the ground stitch is
# placed north of where XGPIO4 crosses the channel instead.
# EXT_SDA_BUF's F->In2 barrel stood 0.098 mm from L4.2's land, and that
# 0.098 mm is what cut U21.4's ground off the B GND PLANE body: the zone's own
# 0.200 mm minimum thickness drops the sliver, so the converter's ground pin
# ended up on a fragment PP2 must price.  The barrel drops to 0.500/0.250 mm
# -- a size this board already carries in thirty places, at the 0.125 mm
# annular-ring floor -- and the channel's north mouth opens to 0.265 mm.
SDA = net("EXT_SDA_BUF")
for t in list(b.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T and abs(t.GetStart().x-nm(58.7))<=3000 \
       and abs(t.GetStart().y-nm(34.0))<=3000 and t.GetNetname()==SDA:
        b.RemoveNative(t)
LOG["sda_dogleg"] = kill([((59.3,34.7),(58.7,34.0))])
trk(SDA, 59.300, 34.700, 58.680, 34.000, 0.200, "F")
via(SDA, 58.680, 34.000, 0.500, 0.250)
LOG["relaid_EXT_SDA_BUF"] = relay_in2(SDA, (58.700,34.000),(60.300,40.800),
    [(58.680,34.000),(60.150,34.800),(60.150,40.800)])

# TP43's final home and its stub onto ACC_DETECT_N_HDR's own J5 run.
tp = b.FindFootprintByReference("TP43")
tp.SetPosition(pcbnew.VECTOR2I(nm(61.600), nm(43.400)))
LOG["killed_tp43_stub"] = kill([((58.8,40.2),(59.86,40.2))])
trk(DET, 61.600, 43.400, 61.600, 45.700, 0.200, "F")

# ---------------------------------------------------------------- 9
# THE FEEDBACK DIVIDER BECOMES PART OF THE CONVERTER.
#
# R99 (732k) and R100 (100k) set U21's 5 V output, and they were 6.7 mm and
# 7.6 mm from the FB pin with a 14 mm high-impedance node (88 k source
# impedance) wired across the top of the switching converter.  That node is
# also what forced ACC_5V_FB through the pocket the SYS feed needs.  Both
# resistors move onto U21's own south face; the whole node becomes 4.5 mm.
FB = net("ACC_5V_FB")
r100 = b.FindFootprintByReference("R100")
r100.SetPosition(pcbnew.VECTOR2I(nm(58.800), nm(42.500))); r100.SetOrientationDegrees(0)
r99 = b.FindFootprintByReference("R99")
r99.SetPosition(pcbnew.VECTOR2I(nm(58.800), nm(44.300))); r99.SetOrientationDegrees(180)
LOG["R100"] = [58.8, 42.5]; LOG["R99"] = [58.8, 44.3, "rot180"]
trk(FB, 57.125, 40.475, 57.500, 41.300, 0.200)          # U21.1 -> divider tap
trk(FB, 57.500, 41.300, 57.975, 42.500, 0.200)
trk(FB, 57.975, 42.500, 57.975, 44.300, 0.200)          # R100.1 -> R99.2
trk("GND", 59.625, 42.500, 59.950, 42.500, 0.300)       # R100.2's own escape
trk(RAW, 59.625, 44.300, 60.600, 43.000, 0.400)         # R99.1 -> ACC_5V_RAW
trk(RAW, 60.600, 43.000, 60.600, 41.500, 0.400)
trk(RAW, 60.600, 41.500, 60.335, 40.475, 0.400)

b.Save(DST)
for _ in range(2):
    bb=pcbnew.LoadBoard(DST); pcbnew.ZONE_FILLER(bb).Fill(bb.Zones()); bb.Save(DST)
print(json.dumps(LOG, indent=1))
