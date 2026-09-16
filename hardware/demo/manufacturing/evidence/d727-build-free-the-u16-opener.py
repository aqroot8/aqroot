#!/usr/bin/env python3
"""D-727 STAGE 1 -- empty the U16 west pocket by spending its measured opener.

D-715 measured this pocket three ways and D-721 four more: `U16`'s west column
carries THREE conductors -- `/ACC_PWR_EN`, `EXT_SCL_BUF`, `/I2C_SCL_INT` --
and every request order closes exactly TWO.  `evidence/d715-blame-u16-2.json`
is the measurement that names the way out: with all eleven foreign nets
dropped the loser routes in 7.508 mm with ZERO vias (so it is a CORRIDOR, not
a package), and THREE single nets open it alone.  One of them is
`/09_COMMUNITY_HEADER/WAKE_GATE_S`.

`WAKE_GATE_S` is a three-pad net that already lives on In3 for its two long
hauls (R66.1 at y = 15.0, Q10.2 at y = 116.7, R63.2 at y = 57.7).  What stands
in `U16`'s pocket is one B.Cu detour -- (58.200,56.300) -> (58.500,55.800) ->
(58.300,52.500) -> (54.300,48.100) -> (54.900,46.700) -- that carries R63.2
south-west to the barrel where it joins In3 anyway.  It comes out; the net is
re-laid by the maze, which already has In3 licensed for it.
"""
import sys, json
import pcbnew
SRC, DST = sys.argv[1], sys.argv[2]
LOG = {"removed": []}
def nm(v): return int(round(v*1e6))
b = pcbnew.LoadBoard(SRC)
KILL_TRK = {}
WHOLE = ["/09_COMMUNITY_HEADER/WAKE_GATE_S"]
KILL_VIA = {"/09_COMMUNITY_HEADER/WAKE_GATE_S": [(54.900,46.700)]}
TOL=4000
for t in list(b.GetTracks()):
    if t.GetNetname() in WHOLE:
        s_,e_=t.GetStart(),t.GetEnd()
        LOG["removed"].append([t.GetNetname(),"via" if t.Type()==pcbnew.PCB_VIA_T else "trk",
                               round(s_.x/1e6,3),round(s_.y/1e6,3),round(e_.x/1e6,3),round(e_.y/1e6,3)])
        b.RemoveNative(t); continue
    if t.Type()==pcbnew.PCB_VIA_T:
        p=t.GetStart()
        for (x,y) in KILL_VIA.get(t.GetNetname(),()):
            if abs(p.x-nm(x))<=TOL and abs(p.y-nm(y))<=TOL:
                LOG["removed"].append([t.GetNetname(),"via",round(p.x/1e6,3),round(p.y/1e6,3)])
                b.RemoveNative(t); break
        continue
    n=t.GetNetname(); s,e=t.GetStart(),t.GetEnd()
    for (x0,y0,x1,y1) in KILL_TRK.get(n,()):
        if (abs(s.x-nm(x0))<=TOL and abs(s.y-nm(y0))<=TOL and abs(e.x-nm(x1))<=TOL and abs(e.y-nm(y1))<=TOL) or \
           (abs(e.x-nm(x0))<=TOL and abs(e.y-nm(y0))<=TOL and abs(s.x-nm(x1))<=TOL and abs(s.y-nm(y1))<=TOL):
            LOG["removed"].append([n, round(s.x/1e6,3), round(s.y/1e6,3), round(e.x/1e6,3), round(e.y/1e6,3)])
            b.RemoveNative(t); break
b.Save(DST)
print(json.dumps(LOG, indent=1))
