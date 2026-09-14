#!/usr/bin/env python3
"""Remove every routed TRACK of one net on named copper layers (vias kept)."""
import sys, pcbnew
src, dst, net = sys.argv[1], sys.argv[2], sys.argv[3]
layers = set(sys.argv[4:])
b = pcbnew.LoadBoard(src)
doomed = [t for t in b.GetTracks()
          if t.GetClass() != 'PCB_VIA' and t.GetNetname() == net
          and b.GetLayerName(t.GetLayer()) in layers]
tot = 0.0
for t in doomed:
    s, e = t.GetStart(), t.GetEnd()
    tot += ((s.x - e.x) ** 2 + (s.y - e.y) ** 2) ** .5 / 1e6
    b.RemoveNative(t)
b.BuildConnectivity()
pcbnew.SaveBoard(dst, b)
print("removed %d tracks, %.3f mm" % (len(doomed), tot))
