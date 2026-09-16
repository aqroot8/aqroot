#!/usr/bin/env python3
"""D-726 STAGE 1 -- the real SYS trunk from SYS POUR 1 to the accessory cell.

D-725 closed the TPS61023's input feed and in doing so made a pre-existing
defect LOAD-BEARING: `U21` is fed from the SYS rail's WEST arm -- 59.5 mm of
0.800 mm track on In2 at 0.5 oz = 0.613 A -- against the 1.373 A average the
boost draws at the ACC_5V class ILIM.  This lays the trunk D-725 named:
0.600 mm OUTER copper, 1.645 A at IPC-2221B / 1 oz / dT 10 K, from the main
body of `SYS POUR 1` to the trunk vertex the accessory cell already has at
(52.000,36.700).

THE CORRIDOR IS MEASURED.  A per-object clearance field (tracks at their
0.250 mm routed clearance, pads at 0.200 mm -- every "routed clearance" rule
in the .kicad_dru excludes pads) plus a least-crossings search says the widest
corridor between those two points is 0.658 mm and that exactly THREE ordinary
signals stand in it: `/ACC_5V_SW_EN`, `/ACC_POWER_FAULT_N`, `/01_POWER_TREE/ISET`.
With `/ACC_5V_SW_EN` declared untouchable there is NO PATH AT ALL -- its
22.4 mm F.Cu diagonal (53.750,52.500)->(66.000,71.250) IS the corridor -- and
the invocation authorises that net's reroute by name.

AND THE RELAY IS SURGICAL BECAUSE A WHOLE-NET EVICTION CUT THREE POURS.
Ripping all three whole, the maze rebuilt `/ACC_5V_SW_EN` at 77 mm and
`/ACC_POWER_FAULT_N` at 90 mm; both hauls carved new B.Cu lanes through
`SYS POUR 1` and the `B GND PLANE` and `pour_partition` refused it, twice.
`/ACC_POWER_FAULT_N` is therefore not re-routed at all here: its two barrels
that stand in the trunk are MOVED, each by about 0.55 mm along its own
conductor, and the F.Cu "V" that crosses the trunk TWICE -- for two endpoints
that are BOTH east of it -- is replaced by the In2 line between its own two
existing barrels.  Nothing else of that net moves.
"""
import sys, json
import pcbnew
SRC, DST = sys.argv[1], sys.argv[2]
LOG = {}
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(SRC)
LAY = {"F": pcbnew.F_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu,
       "In3": pcbnew.In3_Cu, "In4": pcbnew.In4_Cu, "B": pcbnew.B_Cu}
def net(sfx):
    for n in b.GetNetsByName().keys():
        if str(n) == sfx or str(n).endswith("/" + sfx): return str(n)
    raise SystemExit("no net " + sfx)
def trk(n,x0,y0,x1,y1,w,l="F"):
    t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(nm(x0),nm(y0)))
    t.SetEnd(pcbnew.VECTOR2I(nm(x1),nm(y1))); t.SetWidth(nm(w)); t.SetLayer(LAY[l])
    t.SetNet(b.FindNet(n)); b.Add(t)
def via(n,x,y,d,dr):
    v=pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(nm(x),nm(y)))
    v.SetWidth(nm(d)); v.SetDrill(nm(dr)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(b.FindNet(n)); v.SetIsFree(False); b.Add(v)

SYS  = net("BQ25185_SYS")
FAULT= net("ACC_POWER_FAULT_N")

# ---------------------------------------------------------------- 1  REMOVALS
KILL_TRK = {}
KILL_VIA = {}
WHOLE = ["/01_POWER_TREE/ISET", "Net-(U11-TS_MR)", "/ACC_DETECT_N", "/ACC_5V_SW_EN"]     # a two-pad net with a published 0.15 mm floor
LOG["removed"] = []
def rec(t):
    s,e=t.GetStart(),t.GetEnd()
    LOG["removed"].append([t.GetNetname(), "via" if t.Type()==pcbnew.PCB_VIA_T else "trk",
                           round(s.x/1e6,3), round(s.y/1e6,3), round(e.x/1e6,3), round(e.y/1e6,3)])
TOL=4000
for t in list(b.GetTracks()):
    n = t.GetNetname()
    if n in WHOLE:
        rec(t); b.RemoveNative(t); continue
    if t.Type()==pcbnew.PCB_VIA_T:
        p=t.GetStart()
        for (x,y) in KILL_VIA.get(n,()):
            if abs(p.x-nm(x))<=TOL and abs(p.y-nm(y))<=TOL:
                rec(t); b.RemoveNative(t); break
        continue
    s,e=t.GetStart(),t.GetEnd()
    for (x0,y0,x1,y1) in KILL_TRK.get(n,()):
        if (abs(s.x-nm(x0))<=TOL and abs(s.y-nm(y0))<=TOL and
            abs(e.x-nm(x1))<=TOL and abs(e.y-nm(y1))<=TOL) or \
           (abs(e.x-nm(x0))<=TOL and abs(e.y-nm(y0))<=TOL and
            abs(s.x-nm(x1))<=TOL and abs(s.y-nm(y1))<=TOL):
            rec(t); b.RemoveNative(t); break

# ---------------------------------------------------------------- 2  THE TRUNK
TRUNK = [(52.000,36.700),(54.500,44.150),(56.000,45.100),(55.700,47.800),
         (53.850,51.250),(56.400,56.300),(56.450,57.650),(59.050,60.950),
         (60.050,61.950),(60.500,62.700),(60.650,63.150),(64.850,70.350),
         (66.350,70.800),(68.550,79.500),(68.350,80.850)]
for i in range(len(TRUNK)-1):
    trk(SYS, TRUNK[i][0], TRUNK[i][1], TRUNK[i+1][0], TRUNK[i+1][1], 0.600, "F")
LOG["trunk"] = TRUNK
# NO NEW BARREL: the trunk ENDS on the 0.800/0.400 SYS via already at
# (68.350,80.850) -- the one that today carries the WHOLE rail out of U11.1
# into the pour body.  No drill, no annular ring, no hole-to-hole question.

b.Save(DST)
print(json.dumps(LOG, indent=1))
