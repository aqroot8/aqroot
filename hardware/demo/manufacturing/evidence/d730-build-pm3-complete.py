#!/usr/bin/env python3
"""D-730 -- PM-3 COMPLETE: C47 north 0.500 mm, all four NFC nets hand-laid.

Stage 1 is D-729's `d729-build-pm3-handlaid-arm.py` verbatim in effect.
Stage 2 closes the residual the maze refused:

  * `NFC_VDD_RF` (`U9.14`, the ST25R3916 antenna-driver supply, the board's
    one FUNCTIONAL open edge): B.Cu north out of the land in the 0.250 mm
    the two re-laid arms leave, an ORDINARY 0.600/0.300 GENERAL_SIGNAL
    barrel at (34.750,26.200), and an F.Cu run west on to the net's own
    existing F.Cu diagonal.
  * `NFC_AGDC`'s F->B barrel moves (33.300,22.900) -> (33.500,22.500), beside
    the land it already feeds.  It is ordinary copper on an ordinary net and
    it is the ONLY object standing in the 0.600 mm C53/C47 channel.
  * `NFC_VDD_AM` (`U9.11`) is re-laid down that channel, necked to the
    board's own 0.200 mm Default floor for the 3.2 mm that C47 and C53 pinch.
"""
import sys, json, math
import pcbnew

SRC, DST = sys.argv[1], sys.argv[2]
LOG = {"removed": [], "added": []}
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(SRC)
LAY = {"F": pcbnew.F_Cu, "In2": pcbnew.In2_Cu, "B": pcbnew.B_Cu}

def trk(n,x0,y0,x1,y1,w,l="B"):
    t=pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(nm(x0),nm(y0)))
    t.SetEnd(pcbnew.VECTOR2I(nm(x1),nm(y1))); t.SetWidth(nm(w)); t.SetLayer(LAY[l])
    t.SetNet(b.FindNet(n)); b.Add(t)
    LOG["added"].append([n,l,x0,y0,x1,y1,w])

def via(n,x,y,dia,drill):
    v=pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(nm(x),nm(y)))
    v.SetWidth(nm(dia)); v.SetDrill(nm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(b.FindNet(n)); b.Add(v)
    LOG["added"].append([n,"via",x,y,dia,drill])

TOL=4000
def kill(net, pairs):
    """Remove EVERY object matching each pair -- this board carries exact
    duplicate track objects and removing only the first leaves copper behind."""
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
VDDRF = "/04_SPI_B_RADIOS_NFC/NFC_VDD_RF"
RFO1  = "/04_SPI_B_RADIOS_NFC/NFC_RFO1"
VDDA  = "/04_SPI_B_RADIOS_NFC/NFC_VDD_A"
AGDC  = "/04_SPI_B_RADIOS_NFC/NFC_AGDC"

# ==================================================================== STAGE 1
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
ARM = [(34.250,27.725),(34.250,26.900),(33.800,26.450),(33.800,25.400),
       (36.400,25.400),(37.725,26.725),(37.725,27.025),(38.513,27.800)]
for i in range(len(ARM)-1):
    trk(RFO1, ARM[i][0],ARM[i][1], ARM[i+1][0],ARM[i+1][1], 0.300, "B")
LOG["arm_mm"] = round(sum(math.dist(ARM[i],ARM[i+1]) for i in range(len(ARM)-1)),4)

# 4 ------------------------------------------------- NFC_VDD_AM out of the lane
kill(VDDAM, [(33.250,27.725,33.250,26.850), (33.250,26.850,33.125,24.100),
             (33.125,24.100,33.925,23.350), (33.925,23.350,36.275,23.350),
             (36.275,23.350,37.100,22.475)])

# ==================================================================== STAGE 2
# 5 ------------------------------------------------ NFC_AGDC barrel steps aside
#   The (33.300,22.900) barrel is the ONLY object in the 0.600 mm channel
#   between C53's and C47's lands.  It moves 0.44 mm south-east, beside the
#   land it already feeds (same net -- no clearance owed to C53.1), and its
#   F.Cu diagonal re-lands on it.
kill(AGDC, [(33.300,22.900,None,None), (33.500,23.000,33.300,22.900),
            (34.000,22.750,33.500,23.000), (33.300,22.900,30.900,26.600)])
via(AGDC, 33.500, 22.500, 0.600, 0.300)
trk(AGDC, 33.500,22.500, 33.900,22.500, 0.200, "B")
trk(AGDC, 33.500,22.500, 30.900,26.600, 0.200, "F")

# 6 ------------------------------------------------------- NFC_VDD_AM re-laid
#   0.300 mm from the land down the lane RFO1 vacated, necked to the board's
#   own 0.200 mm Default floor for the C53/C47 pinch, back out at (37.100,
#   22.475) -- the node the old route already used.
AM_WIDE = [(33.250,27.725),(33.250,26.850),(33.125,24.100)]
for i in range(len(AM_WIDE)-1):
    trk(VDDAM, *AM_WIDE[i], *AM_WIDE[i+1], 0.300, "B")
AM_NECK = [(33.125,24.100),(33.125,23.275),(36.275,23.275),(37.100,22.475)]
for i in range(len(AM_NECK)-1):
    trk(VDDAM, *AM_NECK[i], *AM_NECK[i+1], 0.200, "B")

# 7 ------------------------------------------------------- NFC_VDD_RF U9.14
#   North in the 0.250 mm the two arms leave at 0.500 mm pitch, an ordinary
#   GENERAL_SIGNAL barrel in the window the arms vacate (y 26.100..26.310),
#   then F.Cu west on to the net's own existing F.Cu diagonal, which passes
#   through (33.100,26.200).
trk(VDDRF, 34.750,27.725, 34.750,26.200, 0.200, "B")
via(VDDRF, 34.750, 26.200, 0.600, 0.300)
trk(VDDRF, 34.750,26.200, 33.000,26.200, 0.200, "F")

b.Save(DST)
print(json.dumps(LOG, indent=1))
