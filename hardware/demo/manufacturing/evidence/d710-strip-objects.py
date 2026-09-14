"""D-710 -- remove NAMED track/via objects from a board, by exact signature.

Usage: d710-strip-objects.py BOARD NET x0,y0,x1,y1 [LAYER]
Removes every track of NET whose BOTH endpoints (or via centre) lie inside the
window, on LAYER when given.  Prints each removal so the transaction is auditable.
"""
import sys
import pcbnew
bd, net, win = sys.argv[1], sys.argv[2], [float(v) for v in sys.argv[3].split(',')]
layer = sys.argv[4] if len(sys.argv) > 4 else None
b = pcbnew.LoadBoard(bd)
x0, y0, x1, y1 = [v * 1e6 for v in win]
def inside(p):
    return x0 <= p.x <= x1 and y0 <= p.y <= y1
gone = []
for t in list(b.GetTracks()):
    if t.GetNetname() != net:
        continue
    if t.GetClass() == "PCB_VIA":
        if not inside(t.GetPosition()):
            continue
        gone.append(("via", t.GetPosition().x / 1e6, t.GetPosition().y / 1e6))
    else:
        if layer and b.GetLayerName(t.GetLayer()) != layer:
            continue
        if not (inside(t.GetStart()) and inside(t.GetEnd())):
            continue
        gone.append(("trk", b.GetLayerName(t.GetLayer()),
                     t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                     t.GetEnd().x / 1e6, t.GetEnd().y / 1e6,
                     t.GetWidth() / 1e6))
    b.Remove(t)
b.Save(bd)
for g in gone:
    print("  removed", g)
print("removed %d objects of %s" % (len(gone), net))
