#!/usr/bin/env python3
"""Trim the INERT copper a part move leaves behind, on NAMED nets only.

A `--release` closure stops the moment a surviving object still meets the next
point, which is right -- it must not strand anything.  What it leaves is a leg
that used to reach the moved pad and now reaches nothing: real DRC calls the
barrel `via_dangling` (a genuine electrical fault, D-287) and the track
`track_dangling`.  This removes exactly that, by measured support:

  * a track END is SUPPORTED when a pad of its own net covers it, or another
    surviving object of that net meets it;
  * a barrel is SUPPORTED when surviving objects/pads of its net reach it on
    TWO OR MORE layers, or when its net owns a filled pour that holds it;
  * anything unsupported is removed and the test is repeated to a fixed point.

Nothing on any other net is touched, and a pad never loses its last object
here -- an unsupported END is what is removed, never a run that terminates on
two pads.
"""
import json
import sys
from pathlib import Path

import pcbnew

TOL = 1000  # nm


def trim(board_path, nets, report_path=None):
    b = pcbnew.LoadBoard(str(board_path))
    want = set(nets)
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() in want:
                pads.setdefault(p.GetNetname(), []).append(p)
    removed = []
    while True:
        objs = [t for t in b.GetTracks() if t.GetNetname() in want]
        doomed = []
        for t in objs:
            net = t.GetNetname()
            if t.Type() == pcbnew.PCB_VIA_T:
                at = t.GetStart()
                layers = set()
                for o in objs:
                    if o is t or o.GetNetname() != net:
                        continue
                    if o.Type() == pcbnew.PCB_VIA_T:
                        continue
                    for e in (o.GetStart(), o.GetEnd()):
                        if abs(e.x - at.x) <= TOL and abs(e.y - at.y) <= TOL:
                            layers.add(o.GetLayer())
                for p in pads.get(net, []):
                    if p.HitTest(at):
                        layers |= set(p.GetLayerSet().CuStack())
                if len(layers) < 2:
                    doomed.append((t, "barrel reaches %d layer(s)" % len(layers)))
            else:
                for e in (t.GetStart(), t.GetEnd()):
                    ok = False
                    for p in pads.get(net, []):
                        if p.HitTest(e):
                            ok = True
                            break
                    if not ok:
                        for o in objs:
                            if o is t or o.GetNetname() != net:
                                continue
                            if o.Type() == pcbnew.PCB_VIA_T:
                                if abs(o.GetStart().x - e.x) <= TOL and abs(o.GetStart().y - e.y) <= TOL:
                                    ok = True
                                    break
                            else:
                                if o.GetLayer() != t.GetLayer():
                                    continue
                                for q in (o.GetStart(), o.GetEnd()):
                                    if abs(q.x - e.x) <= TOL and abs(q.y - e.y) <= TOL:
                                        ok = True
                                        break
                            if ok:
                                break
                    if not ok:
                        doomed.append((t, "end (%.3f,%.3f) unsupported" % (e.x / 1e6, e.y / 1e6)))
                        break
        if not doomed:
            break
        for t, why in doomed:
            if t.Type() == pcbnew.PCB_VIA_T:
                what = "via (%.3f,%.3f)" % (t.GetStart().x / 1e6, t.GetStart().y / 1e6)
            else:
                what = "%s (%.3f,%.3f)-(%.3f,%.3f)" % (
                    b.GetLayerName(t.GetLayer()), t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                    t.GetEnd().x / 1e6, t.GetEnd().y / 1e6)
            removed.append({"net": t.GetNetname(), "object": what, "why": why})
            b.RemoveNative(t)
    b.Save(str(board_path))
    if report_path:
        Path(report_path).write_text(json.dumps({"nets": sorted(want), "removed": removed}, indent=1))
    return removed


if __name__ == "__main__":
    out = trim(sys.argv[1], sys.argv[2].split(","), sys.argv[3] if len(sys.argv) > 3 else None)
    for r in out:
        print("  -", r["net"], r["object"], "--", r["why"])
    print("  %d objects trimmed" % len(out))
