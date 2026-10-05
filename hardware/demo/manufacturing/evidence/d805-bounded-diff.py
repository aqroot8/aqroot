#!/usr/bin/env python3
"""D-805 bounded diff: the D-804 board (git HEAD 466a5058) vs the D-805 board.

    python3 evidence/d805-bounded-diff.py PRE.kicad_pcb POST.kicad_pcb

Reports every footprint whose pose / fpid / value / pad set changed, every
track/via signature only on one side (with its bounding window), zone and
rule-area outline changes, the Edge.Cuts change, the board bbox, and the
pad->net identity of every footprint.
"""
import sys
import pcbnew

MM = 1e6
WINDOWS = {"J3": (34.0, 136.0, 54.0, 151.0), "J2": (4.0, 127.0, 25.0, 151.0),
           "SW9": (62.0, 83.0, 77.0, 100.0),
           # the bottom band between the two connectors: J3-side joins that start
           # west of the J3 window and the SPI_B_SCK In2 run that spans J2 -> J3
           "J2_J3_BAND": (4.0, 136.0, 54.0, 151.0)}


def fps(b):
    out = {}
    for f in b.GetFootprints():
        pads = sorted((p.GetNumber(), p.GetNetname()) for p in f.Pads())
        out[f.GetReference()] = dict(
            pose=(round(f.GetPosition().x / MM, 4), round(f.GetPosition().y / MM, 4),
                  round(f.GetOrientationDegrees(), 4), b.GetLayerName(f.GetLayer())),
            fpid=f.GetFPIDAsString(), value=f.GetValue(), pads=pads,
            graphics=len(list(f.GraphicalItems())))
    return out


def copper(b):
    s = {}
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            k = ("PCB_VIA", t.GetNetname(), round(t.GetPosition().x / MM, 4), round(t.GetPosition().y / MM, 4),
                 t.GetWidth(pcbnew.F_Cu) / MM, t.GetDrill() / MM)
        else:
            a, c = sorted([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)])
            k = ("PCB_TRACK", b.GetLayerName(t.GetLayer()), t.GetNetname(), round(a[0] / MM, 4), round(a[1] / MM, 4),
                 round(c[0] / MM, 4), round(c[1] / MM, 4), t.GetWidth() / MM)
        s[k] = s.get(k, 0) + 1
    return s


def zones(b):
    out = {}
    for z in b.Zones():
        key = (str(z.GetZoneName()), str(z.GetNetname()), z.GetIsRuleArea(),
               tuple(b.GetLayerName(l) for l in z.GetLayerSet().CuStack()))
        o = z.Outline()
        pts = tuple((o.CVertex(i).x, o.CVertex(i).y) for i in range(o.TotalVertices()))
        out.setdefault(key, []).append(pts)
    return {k: sorted(v) for k, v in out.items()}


def edges(b):
    return sorted((d.GetShape(), d.GetStart().x, d.GetStart().y, d.GetEnd().x, d.GetEnd().y)
                  for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts)


def window(k):
    if k[0] == "PCB_VIA":
        pts = [(k[2], k[3])]
    else:
        pts = [(k[3], k[4]), (k[5], k[6])]
    for ref, w in WINDOWS.items():
        if all(w[0] <= x <= w[2] and w[1] <= y <= w[3] for x, y in pts):
            return ref
    return "OUTSIDE"


def main():
    pre, post = pcbnew.LoadBoard(sys.argv[1]), pcbnew.LoadBoard(sys.argv[2])
    A, B = fps(pre), fps(post)
    print("footprints", len(A), len(B), "refs only804", sorted(set(A) - set(B)), "only805", sorted(set(B) - set(A)))
    for r in sorted(set(A) & set(B)):
        a, b = A[r], B[r]
        d = {k: (a[k], b[k]) for k in ("pose", "fpid", "value", "pads", "graphics") if a[k] != b[k]}
        if d:
            print(r, d)
    pad_net_identity = all(A[r]["pads"] == B[r]["pads"] for r in set(A) & set(B))
    print("pad->net identity on every footprint", pad_net_identity)
    ca, cb = copper(pre), copper(post)
    print("tracks/vias", sum(ca.values()), sum(cb.values()))
    gone = sorted(k for k in ca if k not in cb)
    new = sorted(k for k in cb if k not in ca)
    for lbl, ks in (("only804", gone), ("only805", new)):
        by = {}
        for k in ks:
            by.setdefault(window(k), []).append(k)
        print(lbl, len(ks), {w: len(v) for w, v in sorted(by.items())})
        for w, v in sorted(by.items()):
            for k in v:
                print("  ", w, k)
    za, zb = zones(pre), zones(post)
    changed = sorted(k for k in set(za) | set(zb) if za.get(k) != zb.get(k))
    print("zones", sum(len(v) for v in za.values()), sum(len(v) for v in zb.values()), "changed", changed)
    ea, eb = edges(pre), edges(post)
    print("edge cuts items", len(ea), len(eb), "identical", ea == eb)
    for b, lbl in ((pre, "D-804"), (post, "D-805")):
        bb = b.GetBoardEdgesBoundingBox()
        print("bbox", lbl, bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM,
              "(includes the 0.050 mm Edge.Cuts stroke)")
    print("copper layers", pre.GetCopperLayerCount(), post.GetCopperLayerCount(),
          "thickness_nm", pre.GetDesignSettings().GetBoardThickness(), post.GetDesignSettings().GetBoardThickness())


if __name__ == "__main__":
    main()
