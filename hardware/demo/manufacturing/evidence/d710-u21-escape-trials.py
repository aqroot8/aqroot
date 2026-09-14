"""D-710 -- READ-ONLY: every trial `QBoard.escape` makes for U21.5, named.

The gate reports `U21.5: NO LEGAL ESCAPE at >= W mm; blocked by ...` and a
histogram.  This prints the ARITHMETIC of each trial -- the endpoint the escape
formula picks, the obstacle it meets first, the distance it has and the
distance it owes -- so the refusal can be argued with instead of taken.

Usage: d710-u21-escape-trials.py BOARD [-o OUT.json]
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "hardware/beta-v2/checks"))
import qrouter as qr, route_maze_batch as rb, incremental_router as ir
from qrouter import seg_shape_dist

B = sys.argv[1]
OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else None
qb = qr.QBoard(B); ir.inject_existing_via_obstacles(qb)
NET = "/01_POWER_TREE/ACC_5V_LX"
c = rb.net_contract(qb.b, NET, trunk_floor=True)
pad = [p for p in qb.pads.values() if p.get("ref") == "U21.5"][0]
obs = qb.obstacles("B", NET)
clr_pad, clr_trk = c["clr_pad"], c["clr"]
G = 25000


def who(s):
    for a in ("ref", "net"):
        v = getattr(s, a, None)
        if v:
            return "%s:%s" % (s.tag, v)
    return s.tag


rows = []
for w in (600000, 400000, 300000, 250000, 200000, 150000):
    for ux, uy, nm in ((1.0, 0.0, "E"), (-1.0, 0.0, "W"),
                       (0.0, -1.0, "N"), (0.0, 1.0, "S")):
        reach = pad["shape"].extent(ux, uy)
        for slack in (150000, 300000, 500000, 800000):
            ln = reach + max(clr_pad, clr_trk) + w / 2.0 + slack
            lx = int(round((pad["x"] + ux * ln) / G)) * G
            ly = int(round((pad["y"] + uy * ln) / G)) * G
            bad, got, owed = None, None, None
            for s in obs:
                mm_ = qb.margin(s, w, clr_pad, clr_trk)
                bx0, by0, bx1, by1 = s.bbox(mm_)
                if (min(pad["x"], lx) > bx1 or max(pad["x"], lx) < bx0
                        or min(pad["y"], ly) > by1 or max(pad["y"], ly) < by0):
                    continue
                d = seg_shape_dist(pad["x"], pad["y"], lx, ly, s)
                if d < mm_:
                    bad, got, owed = s, d, mm_
                    break
            rows.append(dict(width_mm=w / 1e6, dir=nm, slack_mm=slack / 1e6,
                             end_mm=[round(lx / 1e6, 4), round(ly / 1e6, 4)],
                             free=bad is None,
                             blocker=(None if bad is None else who(bad)),
                             have_mm=(None if bad is None else round(got / 1e6, 4)),
                             owe_mm=(None if bad is None else round(owed / 1e6, 4)),
                             short_mm=(None if bad is None
                                       else round((owed - got) / 1e6, 4))))
doc = dict(schema=1, board=B, net=NET, pad="U21.5",
           pad_centre_mm=[pad["x"] / 1e6, pad["y"] / 1e6],
           clr_pad_mm=clr_pad / 1e6, clr_trk_mm=clr_trk / 1e6,
           note="QBoard.escape casts its ray from the PAD CENTRE, so the "
                "segment runs down the land's spine and owes the full routed "
                "clearance to the flanking lands whatever the land's shape is",
           free=[r for r in rows if r["free"]], trials=rows)
text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
if OUT:
    OUT.write_text(text)
for r in rows:
    if r["dir"] != "E":
        continue
    print("w %.3f E slack %.3f -> (%.3f,%.3f) %s" % (
        r["width_mm"], r["slack_mm"], r["end_mm"][0], r["end_mm"][1],
        "FREE" if r["free"] else "blocked by %s, has %.4f owes %.4f (short %.4f)"
        % (r["blocker"], r["have_mm"], r["owe_mm"], r["short_mm"])))
print("free trials:", len(doc["free"]))
