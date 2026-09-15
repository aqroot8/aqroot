r"""D-712 -- the PROMOTABLE base: U2's channel swap plus U12's PS/SYNC strap.

Two edits, and neither touches Net-(SW9-A).

  1. THE U2 CHANNEL SWAP (D-711's ECO, PCB half; d712-apply-pcb-pad-swap.py).

  2. THE PS/SYNC STRAP, BROUGHT HOME.  R42 is a 0R tying U12.13 (PS/SYNC on the
     TPS63020) to GND, and it is placed at (16.665, 120.335) -- FIFTY
     MILLIMETRES west of the pin -- with TP14 at (40.500, 124.500) on the way.
     Thirty-three objects of B.Cu haul cross the whole board, and the last two
     of them lie in the C24/C26 gate, which D-649 measured as a SINGLE-FILE
     corridor that the /01_POWER_TREE/BQ25185_SYS pour and this net cannot
     share.  That is why C26.2 -- a 10 uF bulk capacitor on the system rail --
     is an ISLAND on the authority.

     A 0R to GND and a direct tie to GND are the same circuit, so U12.13 is
     tied to U12's own GND pad 0.610 mm away and R42 and TP14 come off the
     board.  MEASURED: /01_POWER_TREE/BQ25185_SYS 5 -> 4 open edges, and the
     strap stops being a 50 mm antenna on a switching converter's mode pin.

Usage:  python3 evidence/d712-build-b3.py <SRC_PROJECT_DIR> <DEST_DIR>
"""
import shutil
import sys
from pathlib import Path

import pcbnew

SRC, DST = Path(sys.argv[1]), Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_prl"):
    shutil.copy(SRC / ("aqroot-Beta-v2" + suf), DST / ("aqroot-Beta-v2" + suf))
BRD = DST / "aqroot-Beta-v2.kicad_pcb"

sys.argv = ["x", str(BRD)]
exec(compile((Path(__file__).parent / "d712-apply-pcb-pad-swap.py").read_text(),
             "d712-apply-pcb-pad-swap.py", "exec"), {"__name__": "__main__"})

b = pcbnew.LoadBoard(str(BRD))
doomed = [t for t in b.GetTracks() if t.GetNetname() == "Net-(U12-PS_SYNC)"]
assert len(doomed) == 33, len(doomed)
for t in doomed:
    b.RemoveNative(t)
print("  -33 Net-(U12-PS_SYNC) copper")

gnd = b.FindNet("GND")
u12 = b.FindFootprintByReference("U12")
pad13 = next(p for p in u12.Pads() if p.GetNumber() == "13")
assert (round(pad13.GetPosition().x / 1e6, 4),
        round(pad13.GetPosition().y / 1e6, 4)) == (65.6, 102.8)
pad13.SetNet(gnd)
print("  U12.13 net Net-(U12-PS_SYNC) -> GND")

t = pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(65600000, 102800000))
t.SetEnd(pcbnew.VECTOR2I(65600000, 102190000))
t.SetWidth(200000)
t.SetLayer(b.GetLayerID("B.Cu"))
t.SetNet(gnd)
b.Add(t)
print("  +TRK GND B.Cu (65.600,102.800)->(65.600,102.190)  U12.13 -> U12.15")

b.BuildConnectivity()
pcbnew.SaveBoard(str(BRD), b)
for ref in ("R42", "TP14"):
    b2 = pcbnew.LoadBoard(str(BRD))
    b2.RemoveNative(b2.FindFootprintByReference(ref))
    b2.BuildConnectivity()
    pcbnew.SaveBoard(str(BRD), b2)
    print("  removed footprint", ref)
print("wrote", BRD)
