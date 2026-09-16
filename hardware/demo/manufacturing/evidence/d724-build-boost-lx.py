#!/usr/bin/env python3
"""D-724 -- the TPS61023's switch node reaches its inductor.

SYS POUR 2 is an UNFED island that covers U21 entirely and therefore displaces
the B GND PLANE from U21.4, the converter's ground pin.  That is why U21.4's
ground is a 1.9 mm B.Cu haul east -- and that haul is the ONLY thing in
ACC_5V_LX's corridor.  Trim the pour off the east column, the ground plane
fills to the pin, the haul becomes redundant, and the corridor opens.
"""
import sys, json
import pcbnew
BRD = sys.argv[1]; LOG = {}
def E(t): return frozenset({(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)})
def nm(v): return int(round(v * 1e6))
b = pcbnew.LoadBoard(BRD)

# 1. SYS POUR 2 retreats from U21's east column so the GND plane can reach U21.4.
#    L4.1 (x 57.225..58.205) and U21.3 (x 56.749..57.425) stay inside it.
z = [z for z in b.Zones() if z.GetZoneName().endswith("BQ25185_SYS POUR 2")][0]
o = z.Outline()
pts = [(o.COutline(0).CPoint(i).x, o.COutline(0).CPoint(i).y)
       for i in range(o.COutline(0).PointCount())]
new = pcbnew.SHAPE_POLY_SET(); new.NewOutline()
for (x, y) in pts:
    new.Append(min(x, nm(57.75)), y)
z.SetOutline(new)
LOG["pour2_outline_was"] = [(x/1e6, y/1e6) for x, y in pts]
LOG["pour2_outline_now"] = [(57.75 if x/1e6 > 57.75 else x/1e6, y/1e6) for x, y in pts]

# 2. U21.4's 1.9 mm ground haul is now redundant with the B GND PLANE it was
#    standing in for.  It is also the whole of ACC_5V_LX's corridor.
KILL = [((58.700, 39.375), (60.600, 38.425)),   # GND haul from U21.4 (x2)
        ((58.5125, 40.400), (59.0225, 40.400)),  # ACC_5V_RAW neck, level with SW
        ((59.0225, 40.400), (60.085, 40.475))]   # ACC_5V_RAW to C65.1
def near(t, a, b_, tol=3000):
    s, e = t.GetStart(), t.GetEnd()
    for (p, q) in ((s, e), (e, s)):
        if abs(p.x-nm(a[0]))<=tol and abs(p.y-nm(a[1]))<=tol \
           and abs(q.x-nm(b_[0]))<=tol and abs(q.y-nm(b_[1]))<=tol: return True
    return False
n, killed = 0, []
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T: continue
    for (a, b_) in KILL:
        if near(t, a, b_):
            killed.append([t.GetNetname().split("/")[-1],
                           t.GetStart().x/1e6, t.GetStart().y/1e6,
                           t.GetEnd().x/1e6, t.GetEnd().y/1e6])
            b.RemoveNative(t); n += 1; break
LOG["tracks_removed"] = n; LOG["killed"] = killed

# 3. C65 steps 0.250 mm EAST.  U21.4's pad corner and C65.1's are 0.755 mm
#    apart and a 0.400 mm SWITCH_NODE needs 0.800 mm; the step makes it 0.999.
c65 = b.FindFootprintByReference("C65")
p = c65.GetPosition(); c65.SetPosition(pcbnew.VECTOR2I(p.x + nm(0.250), p.y))
LOG["C65"] = [p.x/1e6, p.y/1e6, "->", (p.x+nm(0.250))/1e6, p.y/1e6]
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T: continue
    for getter, setter in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
        q = getter()
        if any(abs(q.x-nm(cx))<=3000 and abs(q.y-nm(cy))<=3000
               for (cx, cy) in ((60.085, 40.475), (61.985, 40.475))):
            setter(pcbnew.VECTOR2I(q.x + nm(0.250), q.y))

def trk(net, x0, y0, x1, y1, w, layer=pcbnew.B_Cu):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(nm(x0), nm(y0))); t.SetEnd(pcbnew.VECTOR2I(nm(x1), nm(y1)))
    t.SetWidth(nm(w)); t.SetLayer(layer); t.SetNet(b.FindNet(net)); b.Add(t)

RAW = "/01_POWER_TREE/ACC_5V_RAW"
LX  = "/01_POWER_TREE/ACC_5V_LX"
# ACC_5V_RAW leaves U21.6 DIVING SOUTH instead of running level, which is what
# frees 0.300 mm of SWITCH_NODE clearance beside the switch node.
trk(RAW, 58.513, 40.500, 59.000, 40.640, 0.250)
trk(RAW, 59.000, 40.640, 59.900, 40.900, 0.400)
trk(RAW, 59.900, 40.900, 60.335, 40.475, 0.400)
# U21.5 SW -> L4.2.  The 0.200 mm launch is the .kicad_dru pad-escape necking
# minimum inside U21's courtyard (56.555,38.905)-(59.045,40.895) and reaches
# 0.105 mm past it -- under the 0.153 mm U21.6's own escape already reaches.
trk(LX, 58.513, 39.900, 59.150, 39.900, 0.200)
trk(LX, 59.150, 39.900, 59.700, 39.200, 0.400)
trk(LX, 59.700, 39.200, 60.085, 37.800, 0.400)

# 6. Two ordinary inner-layer signals cross the L4.1<->L4.2 channel end to end,
#    which is why no GND barrel fits anywhere in it.  Both are re-laid with a
#    MINIMAL bow that rejoins the original line exactly at both ends.
def relay_in2(net, a, b_, pts, w=0.200):
    n = 0
    for t in list(b.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T or t.GetLayer() != pcbnew.In2_Cu: continue
        if not t.GetNetname().endswith(net): continue
        s_, e_ = t.GetStart(), t.GetEnd()
        for (p_, q_) in ((s_, e_), (e_, s_)):
            if abs(p_.x-nm(a[0]))<=3000 and abs(p_.y-nm(a[1]))<=3000 \
               and abs(q_.x-nm(b_[0]))<=3000 and abs(q_.y-nm(b_[1]))<=3000:
                b.RemoveNative(t); n += 1; break
    for i in range(len(pts)-1):
        trk(t_net[net], pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], w, pcbnew.In2_Cu)
    return n

t_net = {"XGPIO4": "/XGPIO4", "EXT_SDA_BUF": "/09_COMMUNITY_HEADER/EXT_SDA_BUF"}
for k, v in list(t_net.items()):
    if b.FindNet(v) is None:
        for nt in b.GetNetsByName().keys():
            if str(nt).endswith(k): t_net[k] = str(nt); break
LOG["relaid_XGPIO4"] = relay_in2("XGPIO4", (55.150, 22.450), (64.600, 67.650),
    [(55.150,22.450),(58.297,37.500),(59.450,38.400),(59.450,39.400),(58.861,40.200),(64.600,67.650)])
LOG["relaid_EXT_SDA_BUF"] = relay_in2("EXT_SDA_BUF", (58.700, 34.000), (60.300, 40.800),
    [(58.700,34.000),(59.450,35.500),(59.900,38.000),(59.900,39.900),(60.300,40.800)])

# 6b. R64 (100R, ACC_DETECT_N) sits in the boost converter's ground-return
#     pocket AND in the L4 channel.  It steps 0.400 mm north; nothing that
#     slow belongs between a 2 A inductor's pads.
r64 = b.FindFootprintByReference("R64")
q = r64.GetPosition(); r64.SetPosition(pcbnew.VECTOR2I(q.x, q.y - nm(0.400)))
LOG["R64"] = [q.x/1e6, q.y/1e6, "->", q.x/1e6, (q.y-nm(0.400))/1e6]
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T: continue
    for getter, setter in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
        w_ = getter()
        if any(abs(w_.x-nm(cx))<=3000 and abs(w_.y-nm(cy))<=3000
               for (cx, cy) in ((58.032, 38.119), (59.682, 38.119))):
            setter(pcbnew.VECTOR2I(w_.x, w_.y - nm(0.400)))

# 7. U21.4's ground: a 0.45 mm stub to a barrel 0.55 mm from the pad, into the
#    In1 / In4 GND references.  That is the converter ground return a 1.9 mm
#    B.Cu haul was standing in for.
# U21.4 is a switching converter's ground pin: SOLID zone connection, not a
# thermal relief, and the widest stub the pocket admits.
for _pd in b.FindFootprintByReference("U21").Pads():
    if _pd.GetNumber() == "4":
        _pd.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
trk("GND", 58.700, 39.300, 58.700, 38.780, 0.300)
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(nm(58.700), nm(38.780)))
v.SetWidth(nm(0.500)); v.SetDrill(nm(0.250))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNet(b.FindNet("GND")); b.Add(v)
LOG["gnd_barrel"] = [58.700, 38.780, 0.500, 0.250]

b.Save(BRD)
for _ in range(2):
    b = pcbnew.LoadBoard(BRD); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(BRD)
print(json.dumps(LOG, indent=1))
