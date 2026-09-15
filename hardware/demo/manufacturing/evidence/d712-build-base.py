r"""D-712 -- build the U12-pocket candidate base from the authority.

THREE EDITS, and they are all about ONE 0.900 mm band.

U12 (TPS63020) sits 0.505 mm north of the WROOM ANTENNA KEEPOUT, which
forbids tracks, vias, pads AND zone fill on every layer for x >= 64.500,
y >= 104.000.  Its SOUTH pad row is at y 102.800 (bottom edge 103.100), so
everything that row needs -- U12.12 (EN), U12.13 (PS/SYNC) and the
/01_POWER_TREE/BQ25185_SYS pour's only path to U12.10 and U12.11, the
converter's two VIN pins -- has to fit between y 103.100 and y 104.000.
Today it does not: VIN is an ISLAND on the authority and the board does not
power its own 3.3 V rail through the pour.

  1. THE U2 CHANNEL SWAP (D-711's ECO, PCB half)      -- see d712-apply-pcb-pad-swap.py
  2. THE PS/SYNC STRAP, brought home.  R42 is a 0R tying U12.13 to GND and it
     is placed at (16.665, 120.335) -- FIFTY MILLIMETRES west of the pin --
     with TP14 at (40.500, 124.500) on the way.  The haul crosses the C24/C26
     gate, which D-649 measured as a SINGLE-FILE corridor that the SYS pour
     and this net cannot share.  A 0R to GND and a direct tie to GND are the
     same circuit, so U12.13 is tied to U12's own GND pad, 0.610 mm away, and
     R42 and TP14 come off the board.
  3. NET-(SW9-A)'s U12 DETOUR.  U12.12's escape ran 0.850 mm south, through a
     0.600/0.300 barrel whose antipad covers U12.11, then 3.058 mm EAST across
     U12.10 and twenty more millimetres round the east of the board to TP13.1
     -- all of it inside the SYS pour.  screen_pour_cut_blame names it the
     minimal cut.  It comes out; the run re-lays the net.

Usage:  python3 evidence/d712-build-base.py <SRC_PROJECT_DIR> <DEST_DIR>
"""
import shutil
import sys
from pathlib import Path

import pcbnew

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
DST.mkdir(parents=True, exist_ok=True)
for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_prl"):
    shutil.copy(SRC / ("aqroot-Beta-v2" + suf), DST / ("aqroot-Beta-v2" + suf))
BRD = DST / "aqroot-Beta-v2.kicad_pcb"

# ---- 1. the U2 channel swap, in text, before pcbnew ever sees the file -----
sys.argv = ["x", str(BRD)]
exec(compile((Path(__file__).parent / "d712-apply-pcb-pad-swap.py").read_text(),
             "d712-apply-pcb-pad-swap.py", "exec"), {"__name__": "__main__"})

b = pcbnew.LoadBoard(str(BRD))


def key(p):
    return (round(p.x / 1e6, 4), round(p.y / 1e6, 4))


def drop(pred, why):
    doomed = [t for t in b.GetTracks() if pred(t)]
    for t in doomed:
        b.RemoveNative(t)
    print("  -%-3d %s" % (len(doomed), why))
    return len(doomed)


def mk_track(net, layer, a, c, w=200000):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(int(a[0] * 1e6), int(a[1] * 1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(c[0] * 1e6), int(c[1] * 1e6)))
    t.SetWidth(w)
    t.SetLayer(b.GetLayerID(layer))
    t.SetNet(net)
    b.Add(t)
    print("  +TRK %-6s %-7s (%.3f,%.3f)->(%.3f,%.3f)"
          % (net.GetNetname(), layer, a[0], a[1], c[0], c[1]))


# ---- 2. the PS/SYNC strap ---------------------------------------------------
print("2. PS/SYNC strap -> U12's own GND pad")
assert drop(lambda t: t.GetNetname() == "Net-(U12-PS_SYNC)", "Net-(U12-PS_SYNC) copper") == 33
gnd = b.FindNet("GND")
u12 = b.FindFootprintByReference("U12")
pad13 = next(p for p in u12.Pads() if p.GetNumber() == "13")
assert key(pad13.GetPosition()) == (65.6, 102.8)
pad13.SetNet(gnd)
print("  U12.13 net Net-(U12-PS_SYNC) -> GND")
# U12.13's land (y 102.500..103.100) to U12.15, the thermal pad (y ..102.190):
# 0.610 mm at x 65.600, which is 0.280 mm off U12.12's and U12.14's lands
# against the 0.200 mm this package's own pad-escape necking rule asks for.
mk_track(gnd, "B.Cu", (65.6, 102.8), (65.6, 102.19))
for ref in ("R42", "TP14"):
    fp = b.FindFootprintByReference(ref)
    b.Remove(fp)
    print("  removed footprint", ref)

# ---- 3. Net-(SW9-A)'s U12 detour -------------------------------------------
print("3. Net-(SW9-A) out of U12's VIN corridor")
BAND_TRK = {("B.Cu", frozenset({(66.1, 102.8), (66.1, 103.65)})),
            ("B.Cu", frozenset({(66.1, 103.65), (66.35, 103.65)})),
            ("In2.Cu", frozenset({(66.35, 103.65), (66.2, 101.4)}))}
LOOP = [((66.1, 103.65), (69.15, 103.425)), ((69.15, 103.425), (71.375, 100.975)),
        ((71.375, 100.975), (71.05, 95.1)), ((71.05, 95.1), (69.9, 94.05)),
        ((69.9, 94.05), (69.475, 94.05)), ((69.475, 94.05), (69.175, 93.75)),
        ((69.175, 93.75), (69.175, 92.925)), ((69.175, 92.925), (69.15, 92.8)),
        ((69.15, 92.8), (69.65, 92.275)), ((69.65, 92.275), (68.225, 90.825)),
        ((68.225, 90.825), (65.5, 93.0))]
LOOP_TRK = {("B.Cu", frozenset({a, c})) for a, c in LOOP}


def sw9a(t):
    if t.GetNetname() != "Net-(SW9-A)":
        return False
    if t.Type() == pcbnew.PCB_VIA_T:
        return key(t.GetPosition()) == (66.35, 103.65)
    k = (b.GetLayerName(t.GetLayer()), frozenset({key(t.GetStart()), key(t.GetEnd())}))
    return k in BAND_TRK or k in LOOP_TRK


assert drop(sw9a, "Net-(SW9-A) band + east loop") == 4 + 1 + 11

b.BuildConnectivity()
pcbnew.SaveBoard(str(BRD), b)
print("wrote", BRD)
