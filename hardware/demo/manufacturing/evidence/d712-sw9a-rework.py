r"""D-712 -- take Net-(SW9-A)'s copper OUT of U12's north VIN corridor.

U12 is a TPS63020 whose north pad row carries VIN (pins 10 and 11, the
/01_POWER_TREE/BQ25185_SYS rail) between L1's switch node and three control
pins.  The SYS pour can only reach those two VIN pads from the NORTH, and the
band it has to do it in is 0.9 mm tall: the pad row's top edge is y 103.100
and the WROOM ANTENNA KEEPOUT -- which forbids tracks, vias, pads AND zone
fill on every layer -- starts at y 104.000 for all x >= 64.500.

What sits in that band is Net-(SW9-A): a 0.600/0.300 barrel at
(66.350, 103.650) whose antipad reaches x 66.900, and a 3.058 mm B.Cu track
running east from it straight across U12.10.  screen_pour_cut_blame
(--free U12.10=U12.1) names five objects as the MINIMAL cut and Net-(SW9-A)
as the only net that is sufficient ALONE.

THE REWORK keeps the net's topology and its layers and stays under y 104.000.
It walks the barrel WEST, behind U12.12's own pad column, and sends the east
loop down to In2 at its own far end instead of across the corridor:

    was   U12.12 -B- (66.100,103.650) -B- barrel (66.350,103.650) -I2- (66.200,101.400)
                                      \-B- (69.150,103.425) ... TP13.1 / SW9.1
    now   U12.12 -B- (66.100,103.350) -B- barrel (65.850,103.650) -I2- (66.200,101.400)
          (69.150,103.425) barrel -I2- (69.800,98.100)          ... TP13.1 / SW9.1

Usage:  python3 evidence/d712-sw9a-rework.py <board.kicad_pcb>
"""
import sys
import pcbnew

NET = "Net-(SW9-A)"
b = pcbnew.LoadBoard(sys.argv[1])
net = b.FindNet(NET)
assert net is not None, NET


def key(p):
    return (round(p.x / 1e6, 4), round(p.y / 1e6, 4))


DOOM_TRK = {
    ("B.Cu", frozenset({(66.1, 102.8), (66.1, 103.65)}), 0.2): 2,
    ("B.Cu", frozenset({(66.1, 103.65), (66.35, 103.65)}), 0.2): 1,
    ("B.Cu", frozenset({(66.1, 103.65), (69.15, 103.425)}), 0.2): 1,
    ("In2.Cu", frozenset({(66.35, 103.65), (66.2, 101.4)}), 0.2): 1,
}
DOOM_VIA = {(66.35, 103.65): 1}

seen, doomed = {}, []
for t in b.GetTracks():
    if t.GetNetname() != NET:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        k = key(t.GetPosition())
        if k in DOOM_VIA:
            seen[k] = seen.get(k, 0) + 1
            doomed.append(t)
    else:
        k = (b.GetLayerName(t.GetLayer()),
             frozenset({key(t.GetStart()), key(t.GetEnd())}),
             round(t.GetWidth() / 1e6, 4))
        if k in DOOM_TRK:
            seen[k] = seen.get(k, 0) + 1
            doomed.append(t)

for k, want in list(DOOM_TRK.items()) + list(DOOM_VIA.items()):
    assert seen.get(k, 0) == want, "%r matched %d, expected %d" % (
        k, seen.get(k, 0), want)
for t in doomed:
    b.RemoveNative(t)
print("removed", len(doomed), "objects")


def mk_track(layer, a, c, w=200000):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(int(a[0] * 1e6), int(a[1] * 1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(c[0] * 1e6), int(c[1] * 1e6)))
    t.SetWidth(w)
    t.SetLayer(b.GetLayerID(layer))
    t.SetNet(net)
    b.Add(t)
    print("  +TRK %-7s (%.3f,%.3f)->(%.3f,%.3f)" % (layer, a[0], a[1], c[0], c[1]))


def mk_via(p, dia=600000, drill=300000):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(int(p[0] * 1e6), int(p[1] * 1e6)))
    v.SetWidth(dia)
    v.SetDrill(drill)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    b.Add(v)
    print("  +VIA (%.3f,%.3f) %.3f/%.3f" % (p[0], p[1], dia / 1e6, drill / 1e6))


W = (65.850, 103.650)     # the barrel, walked west behind U12.12's column
E = (69.150, 103.425)     # the east loop's own far end
mk_track("B.Cu", (66.1, 102.8), (66.1, 103.35))
mk_track("B.Cu", (66.1, 103.35), W)
mk_via(W)
mk_track("In2.Cu", W, (66.2, 101.4))
mk_via(E)
mk_track("In2.Cu", E, (69.8, 98.1))

b.BuildConnectivity()
pcbnew.SaveBoard(sys.argv[1], b)
print("wrote", sys.argv[1])
