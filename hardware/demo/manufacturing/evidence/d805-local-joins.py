import sys, json
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import importlib; hr = importlib.import_module("d805-local-router")
import pcbnew
Router = hr.Router

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
MM = 1_000_000

# 1. the stale session's temporary router fence must not ship
for z in list(b.Zones()):
    if z.GetZoneName() == "D805_TMP_ROUTER_FENCE":
        b.Delete(z)


def kill(pred):
    for t in list(b.GetTracks()):
        if pred(t):
            b.Delete(t)


def near(p, x, y, e=0.002):
    return abs(p.x / MM - x) < e and abs(p.y / MM - y) < e


# dead stubs left by the D-805 rip (each a remnant pointing into the old J3 copper)
kill(lambda t: t.GetNetname() == "/SPI_B_SCK" and t.GetClass() == "PCB_VIA" and near(t.GetPosition(), 51.6, 145.0))
kill(lambda t: t.GetNetname() == "/I2S_LRCLK" and t.GetClass() == "PCB_TRACK" and near(t.GetStart(), 32.9, 140.4) and near(t.GetEnd(), 37.4, 144.7))

PRE = {t.m_Uuid.AsString() for t in b.GetTracks()}
r = Router(b, (26.0, 128.0, 62.0, 150.6))
F, I2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
jobs = [
    ("/01_POWER_TREE/USB_VBUS_RAW", 0.5, 0.25, 0.8, 0.4, [(B, (35.55, 141.75))], [(B, (40.6, 143.645))], [B], False),
    ("Net-(J3-CC1)", 0.2, 0.2, 0.6, 0.3, [(F, (34.845, 145.368))], [(F, (41.75, 143.645))], None, True),
    ("Net-(J3-CC2)", 0.2, 0.2, 0.6, 0.3, [(F, (34.381, 143.002))], [(F, (44.75, 143.645))], None, True),
    ("/I2C_SDA_INT", 0.2, 0.2, 0.6, 0.3, [(I2, (39.2, 138.8))], [(I2, (52.1, 143.95))], None, True),
    ("/WAKE_INT_N", 0.2, 0.2, 0.6, 0.3, [(I2, (35.6, 143.925))], [(I2, (46.05, 140.15))], None, True),
    ("/I2S_LRCLK", 0.2, 0.2, 0.6, 0.3, [(I2, (31.8, 141.0))], [(I2, (52.6, 146.6))], None, True),
]
only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
rep = {}
for net, w, clr, vd, vdr, s, g, layers, av in jobs:
    if only and net not in only:
        continue
    path = r.route(net, w, clr, vd, vdr, s, g, layers=layers, allow_via=av)
    if path is None:
        print("NO_PATH", net); rep[net] = None; continue
    added = r.commit(path, net, w, vd, vdr)
    rep[net] = added
    print("OK", net, len(added), added)
b.Save(dst)
json.dump(rep, open(dst + ".joins.json", "w"), indent=1, default=str)

# --- post: snap track ends that sit inside a same-net via (not at its centre) to the centre
b2 = b
vias = [t for t in b2.GetTracks() if t.GetClass() == "PCB_VIA"]
added_xy = set()
for net, a in rep.items():
    if not a: continue
SEGS = {(t.GetLayer(), t.GetNetCode(), tuple(sorted([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)])))
        for t in b2.GetTracks() if t.GetClass() == "PCB_TRACK"}
for t in list(b2.GetTracks()):
    if t.GetClass() != "PCB_TRACK": continue
    if t.m_Uuid.AsString() in PRE: continue
    for endname in ("Start", "End"):
        p = getattr(t, "Get" + endname)()
        for v in vias:
            if v.GetNetCode() != t.GetNetCode(): continue
            c = v.GetPosition()
            d = (p - c).EuclideanNorm()
            key = (t.GetLayer(), t.GetNetCode(), tuple(sorted([(p.x, p.y), (c.x, c.y)])))
            if 0 < d < v.GetWidth(pcbnew.F_Cu) // 2 and key not in SEGS:
                SEGS.add(key)
                n = pcbnew.PCB_TRACK(b2); n.SetStart(p); n.SetEnd(c); n.SetWidth(t.GetWidth()); n.SetLayer(t.GetLayer()); n.SetNet(t.GetNet()); b2.Add(n)
                print("snap", t.GetNetname(), b2.GetLayerName(t.GetLayer()), p.x/MM, p.y/MM, "->", c.x/MM, c.y/MM)
# the WAKE_INT_N barrel at the old stub end now joins only In2 copper: the tracks meet at its centre without it
kill(lambda t: t.GetNetname() == "/WAKE_INT_N" and t.GetClass() == "PCB_VIA" and near(t.GetPosition(), 35.6, 143.925))
# the I2S_LRCLK In2 remnant of the D-804 stub (its continuation was removed above)
kill(lambda t: t.GetNetname() == "/I2S_LRCLK" and t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.In2_Cu and near(t.GetStart(), 31.8, 141.0) and near(t.GetEnd(), 32.9, 140.4))
b2.Save(dst)
