import sys, pcbnew
brd, lib = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(brd)
old = b.FindFootprintByReference("J2")
new = pcbnew.FootprintLoad(lib, "Molex_5025700893")
new.SetPosition(old.GetPosition()); new.SetOrientation(old.GetOrientation())
# pads must be identical (number, position, size, shape, layers)
def pads(f): return sorted((p.GetNumber(), p.GetPosition().x, p.GetPosition().y, p.GetSize(0).x, p.GetSize(0).y, int(p.GetShape(0)), p.GetLayerSet().FmtHex()) for p in f.Pads())
assert pads(old) == pads(new), "pad geometry differs"
newitems = [g.Duplicate() for g in list(new.GraphicalItems())]
olditems = list(old.GraphicalItems())
for g in olditems:
    old.Remove(g)
for c in newitems:
    old.Add(c)
old.SetLibDescription(new.GetLibDescription())
b.Save(brd)
print("J2 graphics replaced:", len(list(old.GraphicalItems())))
