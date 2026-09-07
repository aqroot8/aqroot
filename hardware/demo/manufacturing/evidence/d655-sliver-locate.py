"""D-655 READ-ONLY: WHERE is the copper sliver?  KiCad reports the violation
with an EMPTY item list, so the geometry has to be re-derived.  A sliver is a
place a filled polygon is narrower than the board's sliver width: erode the
fill by half that width and dilate it back, and every piece that does not come
back is a sliver.  Run on BOTH boards and report only what is new."""
import sys
import pcbnew

R_NM = int(sys.argv[3]) if len(sys.argv) > 3 else 30000   # half of 0.060 mm


def slivers(path, r=R_NM):
    b = pcbnew.LoadBoard(path)
    out = []
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for lay in z.GetLayerSet().CuStack():
            ps = z.GetFilledPolysList(lay)
            if ps.OutlineCount() == 0:
                continue
            eroded = pcbnew.SHAPE_POLY_SET(ps)
            eroded.Inflate(-r, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 5000)
            eroded.Simplify()
            back = pcbnew.SHAPE_POLY_SET(eroded)
            back.Inflate(r, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 5000)
            back.Simplify()
            diff = pcbnew.SHAPE_POLY_SET(ps)
            diff.BooleanSubtract(back)
            diff.Simplify()
            for i in range(diff.OutlineCount()):
                o = diff.Outline(i)
                sp = pcbnew.SHAPE_POLY_SET()
                sp.AddOutline(o)
                a = sp.Area() / 1e12
                if a < 0.0005:            # numerical crumbs on every corner
                    continue
                bb = o.BBox()
                out.append((round(a, 5), z.GetNetname(), b.GetLayerName(lay),
                            round((bb.GetLeft() + bb.GetRight()) / 2e6, 3),
                            round((bb.GetTop() + bb.GetBottom()) / 2e6, 3),
                            round((bb.GetRight() - bb.GetLeft()) / 1e6, 3),
                            round((bb.GetBottom() - bb.GetTop()) / 1e6, 3)))
    return out


a = slivers(sys.argv[1])
b = slivers(sys.argv[2])
ka = {(x[1], x[2], x[3], x[4]) for x in a}
print("AUTHORITY residues %d   CANDIDATE residues %d   (radius %.3f mm)"
      % (len(a), len(b), R_NM / 1e6))
new = [x for x in b if (x[1], x[2], x[3], x[4]) not in ka]
print("NEW IN CANDIDATE: %d" % len(new))
for x in sorted(new, reverse=True):
    print("   area %8.5f mm2  %-28s %-7s at %8.3f,%8.3f  bbox %.3f x %.3f"
          % (x[0], x[1][:28], x[2], x[3], x[4], x[5], x[6]))
