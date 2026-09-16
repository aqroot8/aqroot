#!/usr/bin/env python3
"""D-729 STAGE 1 -- PM-3 executed: C47 north 0.500 mm, the two arms hand-laid.

D-729 measured the shape; this builds it.

  1. `C47` moves y 24.800 -> 24.300.  Its lands clear to y = 25.025, which
     opens the 25.375 .. 25.925 lane `RFO1` needs, and the capacitor ends up
     0.500 mm CLOSER to `U9.7`, the pin it decouples.  `NFC_VDD_A`'s barrel at
     (33.900,24.400) is already INSIDE `C47.1`'s land and stays inside.
  2. `NFC_VDD_A`'s branch to `U9.7` leaves the lane entirely: the B.Cu diagonal
     (34.050,24.800)->(34.900,25.650) and the barrel it fed are replaced by an
     In2 line from the barrel `C47.1` ALREADY has in its own land.
  3. `NFC_RFO1` is re-laid BY HAND, west-then-north-then-east around
     `VDD_DR`'s barrel site.  It is half of a differential antenna driver pair
     -- B.Cu only, no via anywhere on the net, 0.300 mm minimum -- and
     `rf_symmetry_contract` judges it on ARM LENGTH MISMATCH, which no maze
     models.  `arm_a` was 6.0744 mm against `arm_b` 8.9446 mm with a growth
     budget of 0.0, so `RFO1` may GROW up to 2.870 mm and the mismatch only
     IMPROVES.
"""
import sys, json, math
import pcbnew
SRC, DST = sys.argv[1], sys.argv[2]
LOG = {"removed": []}
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(SRC)
LAY = {"F": pcbnew.F_Cu, "In2": pcbnew.In2_Cu, "B": pcbnew.B_Cu}
def trk(n,x0,y0,x1,y1,w,l="B"):
    t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(nm(x0),nm(y0)))
    t.SetEnd(pcbnew.VECTOR2I(nm(x1),nm(y1))); t.SetWidth(nm(w)); t.SetLayer(LAY[l])
    t.SetNet(b.FindNet(n)); b.Add(t)
TOL=4000
def kill(net, pairs):
    for t in list(b.GetTracks()):
        if t.GetNetname()!=net: continue
        s_,e_=t.GetStart(),t.GetEnd()
        for (x0,y0,x1,y1) in pairs:
            if t.Type()==pcbnew.PCB_VIA_T:
                if x1 is None and abs(s_.x-nm(x0))<=TOL and abs(s_.y-nm(y0))<=TOL:
                    LOG["removed"].append([net,"via",x0,y0]); b.RemoveNative(t); break
                continue
            if x1 is None: continue
            if (abs(s_.x-nm(x0))<=TOL and abs(s_.y-nm(y0))<=TOL and abs(e_.x-nm(x1))<=TOL and abs(e_.y-nm(y1))<=TOL) or \
               (abs(e_.x-nm(x0))<=TOL and abs(e_.y-nm(y0))<=TOL and abs(s_.x-nm(x1))<=TOL and abs(s_.y-nm(y1))<=TOL):
                LOG["removed"].append([net,"trk",x0,y0,x1,y1]); b.RemoveNative(t); break

VDDAM = "/04_SPI_B_RADIOS_NFC/NFC_VDD_AM"
RFO1 = "/04_SPI_B_RADIOS_NFC/NFC_RFO1"
VDDA = "/04_SPI_B_RADIOS_NFC/NFC_VDD_A"

# 1 --------------------------------------------------------------- C47
c47 = b.FindFootprintByReference("C47")
p = c47.GetPosition(); c47.SetPosition(pcbnew.VECTOR2I(p.x, p.y - nm(0.5)))
LOG["c47"] = [round(p.x/1e6,3), round(p.y/1e6,3), round(p.y/1e6-0.5,3)]

# 2 --------------------------------------------------------------- NFC_VDD_A
kill(VDDA, [(34.050,24.800,34.900,25.650), (34.900,25.650,34.900,25.500),
            (34.900,25.500,31.575,28.800), (34.900,25.500,None,None)])
for (ax,ay,bx,by) in ((33.900,24.400,31.000,26.600),(31.000,26.600,31.000,28.300),
                      (31.000,28.300,31.575,28.800)):
    trk(VDDA, ax,ay,bx,by, 0.200, "In2")

# 3 --------------------------------------------------------------- NFC_RFO1
kill(RFO1, [(34.250,27.725,34.250,26.800), (34.250,26.800,34.825,26.225),
            (34.825,26.225,36.925,26.225), (36.925,26.225,37.725,27.025),
            (38.513,27.800,37.725,27.025)])
# The turn is at y = 26.900, not 26.800, and the east run at y = 25.600, not
# 25.700, because the maze's own barrel site for `VDD_DR` is (34.675,26.350)
# and a 0.600/0.300 `GENERAL_SIGNAL` barrel owes it 0.650 mm: at 26.800 the
# turn is 0.656 mm away and at 25.700 the east run is 0.650 mm away -- both
# legal to the micron and neither worth building.  0.045 mm and 0.100 mm of
# margin cost 0.2 mm of arm and the arm has 2.870 mm of budget.
ARM = [(34.250,27.725),(34.250,26.900),(33.800,26.450),(33.800,25.400),
       (36.400,25.400),(37.725,26.725),(37.725,27.025),(38.513,27.800)]
for i in range(len(ARM)-1):
    trk(RFO1, ARM[i][0],ARM[i][1], ARM[i+1][0],ARM[i+1][1], 0.300, "B")
LOG["arm_mm"] = round(sum(math.dist(ARM[i],ARM[i+1]) for i in range(len(ARM)-1)),4)
LOG["arm"] = ARM
# 4 ------------------------------------------------- NFC_VDD_AM out of the lane
kill(VDDAM, [(33.250,27.725,33.250,26.850), (33.250,26.850,33.125,24.100),
             (33.125,24.100,33.925,23.350), (33.925,23.350,36.275,23.350),
             (36.275,23.350,37.100,22.475)])
b.Save(DST)
print(json.dumps(LOG))
