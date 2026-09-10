#!/usr/bin/env python3
"""READ-ONLY: LOCATE a KiCad `copper_sliver`.  KiCad reports the type with an
EMPTY items list, so this reproduces the shape the check is about -- a filled
zone region that vanishes under an OPEN (deflate then inflate) at the sliver
width -- and reports every piece that vanishes, by bbox and area, so a run that
counted two slivers can be pointed at two places."""
import sys, pcbnew

path = sys.argv[1]
d_um = float(sys.argv[2]) if len(sys.argv) > 2 else 25.0     # microns
d = int(d_um * 1000)
b = pcbnew.LoadBoard(path)
rows = []
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    for lay in z.GetLayerSet().CuStack():
        poly = z.GetFilledPolysList(lay)
        if poly.OutlineCount() == 0:
            continue
        opened = poly.CloneDropTriangulation() if hasattr(poly, "CloneDropTriangulation") else pcbnew.SHAPE_POLY_SET(poly)
        opened.Deflate(d, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 5000)
        opened.Inflate(d, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 5000)
        lost = pcbnew.SHAPE_POLY_SET(poly)
        lost.BooleanSubtract(opened)
        lost.Simplify()
        for i in range(lost.OutlineCount()):
            o = lost.Outline(i)
            pts = [(o.CPoint(k).x, o.CPoint(k).y) for k in range(o.PointCount())]
            if len(pts) < 3:
                continue
            a = 0.0
            for k in range(len(pts)):
                x1, y1 = pts[k]; x2, y2 = pts[(k + 1) % len(pts)]
                a += x1 * y2 - x2 * y1
            a = abs(a) / 2.0 / 1e12
            xs = [p[0] / 1e6 for p in pts]; ys = [p[1] / 1e6 for p in pts]
            rows.append((a, z.GetNetname(), b.GetLayerName(lay),
                         min(xs), min(ys), max(xs), max(ys)))
rows.sort(reverse=True)
print("open radius %.3f mm  pieces %d" % (d_um / 1000.0, len(rows)))
for a, net, lay, x0, y0, x1, y1 in rows[:20]:
    print("  %-22s %-6s area %9.6f mm2  bbox (%.3f,%.3f)-(%.3f,%.3f)  %.3f x %.3f"
          % (net, lay, a, x0, y0, x1, y1, x1 - x0, y1 - y0))

if len(sys.argv) > 3:
    import json
    json.dump([[round(a,7),n,l,round(x0,3),round(y0,3),round(x1,3),round(y1,3)]
               for a,n,l,x0,y0,x1,y1 in rows], open(sys.argv[3],"w"))
