import pcbnew, sys
src, dst = sys.argv[1], sys.argv[2]
nets = set(sys.argv[3:])
b = pcbnew.LoadBoard(src)
doomed = [t for t in b.GetTracks() if t.GetNetname() in nets]
print("removing", len(doomed), "objects")
for t in doomed:
    b.RemoveNative(t)
b.BuildConnectivity()
pcbnew.SaveBoard(dst, b)
