#!/usr/bin/env python3
"""D-725 STAGE 1 -- prepare the accessory-boost pocket.

The pocket at (54..60, 32..41) is asked to hold, at once: a 2.19 A SYS feed
that must arrive from the WEST, three north-south ordinary signals, one F.Cu
wall that exists only to reach a TEST POINT, and the TPS61023's own switch
node.  Every previous pass tried to thread one more conductor through it.
This one EMPTIES it and then re-lays what actually has to be there.
"""
import sys, json
import pcbnew

SRC = sys.argv[1]
LOG = {}
def nm(v): return int(round(v * 1e6))
b = pcbnew.LoadBoard(SRC)
LAY = {"F": pcbnew.F_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu,
       "In3": pcbnew.In3_Cu, "In4": pcbnew.In4_Cu, "B": pcbnew.B_Cu}

def net(suffix):
    for n in b.GetNetsByName().keys():
        if str(n) == suffix or str(n).endswith("/" + suffix):
            return str(n)
    raise SystemExit("no net " + suffix)

def kill(pairs, tol=4000, layer=None):
    """Remove track segments whose endpoints match (either order)."""
    out = []
    for t in list(b.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T: continue
        if layer is not None and t.GetLayer() != layer: continue
        s, e = t.GetStart(), t.GetEnd()
        for (a, c) in pairs:
            for (p, q) in ((s, e), (e, s)):
                if abs(p.x-nm(a[0])) <= tol and abs(p.y-nm(a[1])) <= tol \
                   and abs(q.x-nm(c[0])) <= tol and abs(q.y-nm(c[1])) <= tol:
                    out.append([t.GetNetname().split("/")[-1],
                                round(s.x/1e6,3), round(s.y/1e6,3),
                                round(e.x/1e6,3), round(e.y/1e6,3)])
                    b.RemoveNative(t)
                    break
            else:
                continue
            break
    return out

def kill_via(pts, tol=4000):
    out = []
    for t in list(b.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T: continue
        s = t.GetStart()
        for p in pts:
            if abs(s.x-nm(p[0])) <= tol and abs(s.y-nm(p[1])) <= tol:
                out.append([t.GetNetname().split("/")[-1], round(s.x/1e6,3), round(s.y/1e6,3)])
                b.RemoveNative(t); break
    return out

def trk(netname, x0, y0, x1, y1, w, layer="B"):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(nm(x0), nm(y0)))
    t.SetEnd(pcbnew.VECTOR2I(nm(x1), nm(y1)))
    t.SetWidth(nm(w)); t.SetLayer(LAY[layer])
    t.SetNet(b.FindNet(netname)); b.Add(t)

def via(netname, x, y, dia, drill):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
    v.SetWidth(nm(dia)); v.SetDrill(nm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(b.FindNet(netname)); v.SetIsFree(False); b.Add(v)

def move(ref, x, y, rot=None):
    f = b.FindFootprintByReference(ref)
    p = f.GetPosition()
    f.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
    if rot is not None: f.SetOrientationDegrees(rot)
    return [round(p.x/1e6,3), round(p.y/1e6,3), "->", x, y]

DET = net("ACC_DETECT_N_HDR")
FB  = net("ACC_5V_FB")
SCL = net("EXT_SCL_BUF")
SW3 = net("ACC_3V3_SW")
BEN = net("ACC_5V_BOOST_EN")
SYS = net("BQ25185_SYS")
LX  = net("ACC_5V_LX")
RAW = net("ACC_5V_RAW")

# ---------------------------------------------------------------- 1
# ACC_DETECT_N_HDR's D5.6 -> R64.2 chain is a 28 mm F.Cu WALL across the whole
# pocket for a 17 mm straight-line connection, and its TP43 spur is a second
# wall.  All of it comes out; the router re-lays D5.6 -> R64.2 afterwards.
LOG["det_removed"] = kill([
    ((59.85,13.85),(58.975,14.75)), ((60.625,14.525),(59.85,13.85)),
    ((60.975,21.175),(60.625,14.525)), ((60.183,21.178),(60.975,21.175)),
    ((58.975,14.75),(58.925,18.15)), ((58.925,18.15),(55.875,21.225)),
    ((55.875,21.225),(55.725,29.925)), ((55.725,29.925),(55.15,30.55)),
    ((55.15,30.55),(56.0,33.525)), ((56.0,33.525),(59.675,37.2)),
    ((59.675,37.2),(59.682,38.119)),
    ((55.731,35.33),(56.4,36.0)), ((56.4,36.0),(57.55,36.0)),
    ((57.55,36.0),(58.975,37.425)), ((59.682,38.119),(58.975,37.425)),
])
# TP43 leaves the pocket and goes where a test point belongs: beside the
# signal it tests, south of R64, on copper that is already ACC_DETECT_N_HDR.
LOG["TP43"] = move("TP43", 58.8, 40.2)
trk(DET, 58.8, 40.2, 59.86, 40.2, 0.2, "F")

# ---------------------------------------------------------------- 2
# ACC_5V_FB's R100.1 -> U21.1 branch is a 12 mm loop that crosses the pocket
# twice.  Out; the router re-lays it.
LOG["fb_removed"] = kill([
    ((57.875,32.725),(58.9,31.8)), ((58.9,31.8),(57.7,30.7)),
    ((57.7,30.7),(55.6,32.9)), ((55.6,32.9),(56.2,33.6)),
    ((56.2,33.6),(56.1,36.9)), ((56.1,36.9),(57.2,38.1)),
    ((57.2,38.1),(57.3,40.8)),
])
LOG["fb_vias"] = kill_via([(56.1,36.9)])
# U21.1's 10 mm southern loop is redundant too; the feedback node is re-laid
# whole.  A boost converter's FB pin does not want a 10 mm loop past its own
# switch node.
LOG["fb_tail"] = kill([
    ((57.3,40.8),(59.5,43.0)), ((59.5,43.0),(58.4,44.1)), ((58.4,44.1),(56.8,45.3)),
    ((56.8,45.3),(57.1,44.4)), ((57.125,44.25),(57.1,44.4)), ((57.125,40.475),(57.125,44.25)),
])
LOG["fb_tail_vias"] = kill_via([(58.4,44.1),(56.8,45.3)])
# and the R100.1 -> R99.2 leg, 14 mm of divider wiring laid across the top of
# the converter: both resistors move onto U21 in stage 2.
LOG["fb_east"] = kill([
    ((57.875,32.725),(58.7,32.0)), ((58.7,32.0),(59.3,30.9)),
    ((59.3,30.9),(61.5,29.0)), ((61.5,29.0),(63.7,31.3)),
    ((63.7,31.3),(63.3,32.3)), ((63.625,33.225),(63.3,32.3)),
])
# ACC_5V_RAW's spur to R99.1 goes with it.
LOG["raw_spur"] = kill([((62.175,33.5),(61.375,34.3)),
                        ((60.95,39.425),(61.375,34.3))])
LOG["raw_spur_vias"] = kill_via([(61.375,34.3)])
# ACC_5V_BOOST_EN's barrel steps 2.5 mm further down its own 45 deg line so the
# divider's new home is clear of it.
LOG["ben_hop"] = kill([((58.4,43.0),(56.5,41.1)), ((62.5,47.1),(58.4,43.0))])
LOG["ben_hop_via"] = kill_via([(58.4,43.0)])
trk(BEN, 56.5, 41.1, 60.6, 45.2, 0.2, "F")
via(BEN, 60.6, 45.2, 0.6, 0.3)
trk(BEN, 60.6, 45.2, 62.5, 47.1, 0.2, "B")

# ---------------------------------------------------------------- 3
# EXT_SCL_BUF's B.Cu descent at x = 56.7..56.8 is the wall every SYS leg has
# hit since D-724 addendum 2.  Out; the router re-lays R47.1 -> (55.7,40.3).
LOG["scl_removed"] = kill([
    ((58.1,31.5),(57.8,31.8)), ((57.8,31.8),(56.7,32.5)),
    ((56.7,32.5),(56.8,38.3)), ((56.8,38.3),(56.2,38.9)),
    ((56.2,38.9),(55.7,40.3)),
])
LOG["scl_vias"] = kill_via([(57.8,31.8)])
# and the whole southern tail below the (55.7,40.3) barrel is redundant once
# R47.1 is re-routed to U16.2: cut back to the T at (56.075,54.85), which is
# what keeps R50.2 on the net.
LOG["scl_tail"] = kill([
    ((55.7,40.3),(55.9,42.3)), ((55.9,42.3),(60.1,49.1)), ((60.1,49.1),(56.4,52.8)),
    ((56.4,52.8),(55.8,53.5)), ((55.8,53.5),(55.9,53.6)), ((55.9,54.375),(55.9,53.6)),
    ((56.075,54.85),(55.9,54.375)),
])
LOG["scl_tail_vias"] = kill_via([(55.7,40.3),(56.4,52.8)])

# ---------------------------------------------------------------- 4
# ACC_3V3_SW IS PROTECTED COPPER (protected_copper.py guards every
# `ACC_3V3_SW*` net as retained switched accessory power).  It is NOT touched:
# the SYS feed's barrels are placed west of its In2 run instead, and XGPIO4's
# bow is shaped around it.  Its 239 mm of copper comes through this
# transaction byte-identical.

# ---------------------------------------------------------------- 4b
# R64 -- a 100R detect-signal resistor -- sits ON TOP of a 2 A switching
# converter, and its land is the reason no POWER-class barrel fits in the
# L4.1<->L4.2 channel that is U21.4's only wide ground return.  It moves out
# of the converter entirely, onto the ACC_DETECT_N_HDR run it already feeds.
LOG["R64"] = move("R64", 60.500, 46.000)
LOG["det_n_removed"] = kill([
    ((58.032,38.119),(58.05,39.05)), ((58.05,39.05),(57.9,38.9)),
    ((57.9,38.9),(57.9,38.8)), ((57.8,38.9),(57.9,38.8)),
    ((57.8,40.7),(57.8,38.9)), ((57.65,40.85),(57.8,40.7)),
    ((57.65,51.0),(57.65,40.85)), ((59.05,52.4),(57.65,51.0)),
    ((59.05,56.8),(59.05,52.4)), ((59.05,57.735),(59.05,56.8)),
])
LOG["det_hdr_stub"] = kill([((59.682,38.119),(59.675,39.05)),
                            ((59.675,39.05),(62.4,56.0))])
trk(DET, 60.792, 46.000, 62.400, 56.000, 0.200, "F")
LOG["det_n_vias"] = kill_via([(57.9,38.8)])
# R64.2 lands on ACC_DETECT_N_HDR's own J5 run; give it an explicit stub.
trk(DET, 61.325, 46.000, 60.792, 46.000, 0.200, "F")

# ---------------------------------------------------------------- 5
# ACC_5V_BOOST_EN's F.Cu V crosses the SYS approach at (53.9,35.5).  In2 is
# EMPTY there (this board has no In2 pour at all) and the net already uses In2.
LOG["ben_removed"] = kill([((49.5,31.0),(53.9,35.5)), ((53.9,35.5),(48.0,43.8))])
# there is no legal barrel anywhere along the old F.Cu run -- the NFC antenna
# feed pair owns the B.Cu underneath it -- so the dive uses the barrel the net
# ALREADY has at (53.1,27.4) and the whole F.Cu leg comes out.
LOG["ben_fcu_trim"] = kill([((53.1,27.4),(49.5,31.0))])
via(BEN, 48.0, 43.8, 0.6, 0.3)
for a, c in (((53.1,27.4),(52.9,29.0)), ((52.9,29.0),(52.3,31.5)),
             ((52.3,31.5),(50.2,33.2)), ((50.2,33.2),(48.0,43.8))):
    trk(BEN, a[0], a[1], c[0], c[1], 0.2, "In2")


b.Save(sys.argv[2])
for _ in range(2):
    bb = pcbnew.LoadBoard(sys.argv[2]); pcbnew.ZONE_FILLER(bb).Fill(bb.Zones()); bb.Save(sys.argv[2])
print(json.dumps(LOG, indent=1))
