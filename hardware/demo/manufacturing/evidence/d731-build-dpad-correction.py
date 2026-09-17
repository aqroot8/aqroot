#!/usr/bin/env python3
"""D-731 -- THE D-PAD IS WIRED ONE POSITION OUT AND THIS CORRECTS IT.

`MECHANICAL_INTERFACE_SPEC.md` 610 and `P1_FLOORPLAN_INPUTS.md` F-11 both say
the front carries a FOUR-WAY D-PAD LOWER LEFT and A + B LOWER RIGHT, and
`DEVICE_SPEC.md` 9 marks "D-pad + A/B" MARKETING-SAFE.  The board places six
identical `PTS645SM43SMTR92LFS` switches in exactly those two clusters -- a
15 mm diamond centred (13.500,115.000) and a pair at y 99.000 -- and the
mechanical ribs confirm which is which (`RIB_R1`/`RIB_B1` bracket the diamond,
`RIB_R2` bears behind the pair).  But the FUNCTIONS sit one position out
around the cycle:

    (13.500,107.500) diamond TOP     SW3  DOWN       should be UP
    (13.500,122.500) diamond BOTTOM  SW4  LEFT       should be DOWN
    ( 6.000,115.000) diamond LEFT    SW5  RIGHT      should be LEFT
    (21.000,115.000) diamond RIGHT   SW6  A_SELECT   should be RIGHT
    (64.200, 99.000) pair OUTER      SW2  UP         should be A_SELECT
    (53.500, 99.000) pair INNER      SW7  B_BACK     correct

So the top of the D-pad sends DOWN, its right-hand arm sends A, and UP is a
stray button 51 mm away beside B.  That is not a D-pad.

THE FIX IS A PURE 5-CYCLE OF POSITION AND ROTATION.  All six are the same
footprint, the four diamond switches all sit at rot 90 and the two pair
switches at rot 0, so every pad lands EXACTLY where an identical pad was:
the courtyards, the holes and the GND pad-2 lands are unchanged to the micron
and only the pad-1 net identities move.  Nothing is added to the schematic and
no firmware constant changes -- each reference keeps its own function.
"""
import sys, json, pcbnew
SRC,DST=sys.argv[1],sys.argv[2]
b=pcbnew.LoadBoard(SRC)
LOG={"moved":[], "removed":{}, "removed_mm":0.0}
TARGET = {                       # ref: (x, y, rot)  -- function to position
    "SW2": (13.500, 107.500, 90.0),   # UP       -> diamond TOP
    "SW3": (13.500, 122.500, 90.0),   # DOWN     -> diamond BOTTOM
    "SW4": ( 6.000, 115.000, 90.0),   # LEFT     -> diamond LEFT
    "SW5": (21.000, 115.000, 90.0),   # RIGHT    -> diamond RIGHT
    "SW6": (64.200,  99.000,  0.0),   # A_SELECT -> pair OUTER
}
NETS = ["/08_BUTTONS_EXPANDERS/BTN_%s_N" % n
        for n in ("UP","DOWN","LEFT","RIGHT","A")]
# 1 -- rip the five signal nets whose switch lands move
for t in list(b.GetTracks()):
    n=t.GetNetname()
    if n not in NETS: continue
    LOG["removed"][n]=LOG["removed"].get(n,0)+1
    if t.Type()!=pcbnew.PCB_VIA_T:
        s,e=t.GetStart(),t.GetEnd(); LOG["removed_mm"]+=((s.x-e.x)**2+(s.y-e.y)**2)**0.5/1e6
    b.RemoveNative(t)
LOG["removed_mm"]=round(LOG["removed_mm"],3)
# 2 -- the 5-cycle
for ref,(x,y,rot) in TARGET.items():
    f=b.FindFootprintByReference(ref); p=f.GetPosition(); r0=f.GetOrientationDegrees()
    f.SetPosition(pcbnew.VECTOR2I(int(round(x*1e6)),int(round(y*1e6))))
    f.SetOrientationDegrees(rot)
    LOG["moved"].append(dict(ref=ref, value=f.GetValue(),
                             was=[round(p.x/1e6,3),round(p.y/1e6,3),r0],
                             now=[x,y,rot]))
b.Save(DST)
print(json.dumps(LOG,indent=1))
