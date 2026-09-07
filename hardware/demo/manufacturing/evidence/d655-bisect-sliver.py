"""D-655: WHICH of this run's two routes makes the copper sliver?  Build the
candidate with one net's NEW copper reverted, refill with the real engine, and
let KiCad answer.  Only copper the candidate has and the authority has not can
be removed, so no legacy copper is at risk."""
import sys
import pcbnew

AUTH, PATH, DROP = sys.argv[1], sys.argv[2], sys.argv[3]


def sigs(p):
    b = pcbnew.LoadBoard(p)
    s = set()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            q = t.GetPosition()
            s.add(("V", t.GetNetname(), int(q.x), int(q.y)))
        else:
            s.add(("T", t.GetNetname(), t.GetLayer(), int(t.GetStart().x),
                   int(t.GetStart().y), int(t.GetEnd().x), int(t.GetEnd().y),
                   int(t.GetWidth())))
    return s


old = sigs(AUTH)
b = pcbnew.LoadBoard(PATH)
doomed = []
for t in b.GetTracks():
    if t.GetNetname() != DROP:
        continue
    if t.GetClass() == "PCB_VIA":
        q = t.GetPosition()
        k = ("V", t.GetNetname(), int(q.x), int(q.y))
    else:
        k = ("T", t.GetNetname(), t.GetLayer(), int(t.GetStart().x),
             int(t.GetStart().y), int(t.GetEnd().x), int(t.GetEnd().y),
             int(t.GetWidth()))
    if k not in old:
        doomed.append(t)
print("removing %d NEW %s objects" % (len(doomed), DROP))
for t in doomed:
    b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PATH, b)
print("refilled and saved")
