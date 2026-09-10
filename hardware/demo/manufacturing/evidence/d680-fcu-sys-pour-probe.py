#!/usr/bin/env python3
"""READ-ONLY probe: add an F.Cu BQ25185_SYS pour bounded to a rectangle on a
PRIVATE COPY, refill with KiCad's own filler, and report

  * whether the new F.Cu island CONTAINS the existing F.Cu trunk vertex
    (52.000, 36.700) -- i.e. it is electrically the main SYS cluster, and
  * whether it OVERLAPS the B.Cu `SYS POUR 2` island that holds L4.1/U21.3 --
    i.e. `--bridge` has a site for ONE through barrel, and
  * what it costs the +3V3 F.Cu plane.

Nothing is written outside the temp copy.
"""
import json, shutil, sys, tempfile
from pathlib import Path
import pcbnew

SRC = Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb")
NET = "/01_POWER_TREE/BQ25185_SYS"
MM = 1e6


def poly_of(z, lay):
    return z.GetFilledPolysList(lay)


def islands(sp):
    out = []
    for k in range(sp.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(sp.Outline(k))
        for h in range(sp.HoleCount(k)):
            one.AddHole(sp.Hole(k, h), 0)
        bb = one.BBox()
        out.append(dict(i=k, poly=one, area=one.Area() / 1e12,
                        bbox=[round(bb.GetLeft() / MM, 3), round(bb.GetTop() / MM, 3),
                              round(bb.GetRight() / MM, 3), round(bb.GetBottom() / MM, 3)]))
    return out


def run(rect, tag):
    tmp = Path(tempfile.mkdtemp(prefix="syspour-"))
    for ext in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        shutil.copy(SRC.with_suffix(ext), tmp / ("b" + ext))
    path = tmp / "b.kicad_pcb"
    b = pcbnew.LoadBoard(str(path))
    net = b.FindNet(NET)
    z = pcbnew.ZONE(b)
    z.SetNetCode(net.GetNetCode())
    z.SetLayer(pcbnew.F_Cu)
    z.SetZoneName("D680 F SYS BRIDGE %s" % tag)
    z.SetLocalClearance(int(round(0.25 * MM)))
    z.SetMinThickness(int(round(0.25 * MM)))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIsFilled(False)
    x0, y0, x1, y1 = rect
    ol = z.Outline()
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ch.Append(int(round(x * MM)), int(round(y * MM)))
    ch.SetClosed(True)
    ol.AddOutline(ch)
    b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

    rec = dict(tag=tag, rect=rect)
    mine = None
    for zz in b.Zones():
        if zz.GetIsRuleArea():
            continue
        nm = zz.GetZoneName()
        if nm.startswith("D680 F SYS BRIDGE"):
            mine = islands(poly_of(zz, pcbnew.F_Cu))
        if nm == "B /01_POWER_TREE/BQ25185_SYS POUR 2":
            rec["pour2"] = [dict(i=d["i"], area=round(d["area"], 3), bbox=d["bbox"])
                            for d in islands(poly_of(zz, pcbnew.B_Cu))]
            pour2 = islands(poly_of(zz, pcbnew.B_Cu))
        if nm == "F +3V3 PLANE":
            f3 = islands(poly_of(zz, pcbnew.F_Cu))
            rec["p3v3_f_islands"] = len(f3)
            rec["p3v3_f_area"] = round(sum(d["area"] for d in f3), 3)
    rec["new_islands"] = [dict(i=d["i"], area=round(d["area"], 3), bbox=d["bbox"])
                          for d in (mine or [])]
    # does a new island contain the trunk vertex?
    v = pcbnew.VECTOR2I(int(52.000 * MM), int(36.700 * MM))
    rec["holds_trunk_vertex"] = [d["i"] for d in (mine or [])
                                 if d["poly"].Contains(v, -1, 0)]
    # overlap with the B.Cu POUR 2 island (plan view)
    ov = []
    for d in (mine or []):
        for e in pour2:
            inter = pcbnew.SHAPE_POLY_SET(d["poly"])
            inter.BooleanIntersection(e["poly"])
            a = inter.Area() / 1e12
            if a > 0:
                bb = inter.BBox()
                ov.append(dict(f=d["i"], b=e["i"], mm2=round(a, 4),
                               bbox=[round(bb.GetLeft() / MM, 3), round(bb.GetTop() / MM, 3),
                                     round(bb.GetRight() / MM, 3), round(bb.GetBottom() / MM, 3)]))
    rec["overlap_with_pour2"] = ov
    # KiCad's own connectivity: is the new zone one cluster with the trunk?
    b.BuildConnectivity()
    shutil.rmtree(tmp, ignore_errors=True)
    return rec


if __name__ == "__main__":
    rects = json.loads(sys.argv[1])
    out = [run(r["rect"], r["tag"]) for r in rects]
    print(json.dumps(out, indent=1))
