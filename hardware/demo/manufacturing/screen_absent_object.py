#!/usr/bin/env python3
"""AQROOT Demo -- PRICE A POCKET WITH THE OBSTRUCTION ABSENT.

The cheapest question to ask about a lever is the one that can kill it: *if the
thing in the way simply were not there, would anything open?*  D-620 named a
`C17` east transaction -- two escape relays, a via-in-pad bound, a `+0.675 mm`
`PL5` ceiling -- and this screen answered it in one run before a line of that
was built: with `C17` and both its escapes gone, all three open `U9`
receive-side edges STILL refuse.  **VACUOUS**, and a whole transaction saved.

It removes named footprints, named tracks and named barrels from a SCRATCH copy
so `route_maze_batch.py --propose` can be pointed at the result.  Two rules make
it safe to keep around:

  * it REFUSES to open the authoritative board, by resolved path, always;
  * every removal must be named EXACTLY and must MATCH -- a description that
    hits nothing is reported in `unmatched_*` and the verdict is `FAIL`, because
    a spec that misses is a spec written about a different board.

`--propose` WRITES its proposals to the board it is given, so a scratch is good
for exactly one run.  Rebuild it for each rung of a ladder or the second
measurement will be taken on the first one's copper.

    python3 screen_absent_object.py SCRATCH.kicad_pcb --drop-ref C17 \
        --drop-track '+3V3:38.2,30.5:38.5,30.9' --drop-via '+3V3:38.5,30.9' \
        --report OUT.json
"""
import argparse, json, sys
from pathlib import Path

AUTH = Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/"
            "aqroot-Beta-v2.kicad_pcb").resolve()

ap = argparse.ArgumentParser()
ap.add_argument("board", type=Path)
ap.add_argument("--drop-ref", action="append", default=[])
ap.add_argument("--drop-track", action="append", default=[],
                help="NET:x0,y0:x1,y1 in mm (order-insensitive)")
ap.add_argument("--drop-via", action="append", default=[], help="NET:x,y in mm")
ap.add_argument("--report", type=Path)
a = ap.parse_args()
if a.board.resolve() == AUTH:
    raise SystemExit("refusing to mutate the authoritative board")

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew

b = pcbnew.LoadBoard(str(a.board))
out = dict(board=str(a.board), dropped_refs=[], dropped_tracks=[],
           dropped_vias=[], missing=[])

for ref in a.drop_ref:
    fp = next((f for f in b.GetFootprints() if f.GetReference() == ref), None)
    if fp is None:
        out["missing"].append(ref); continue
    out["dropped_refs"].append(dict(ref=ref,
        pos_mm=[fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6],
        pads=[[p.GetNumber(), p.GetNetname()] for p in fp.Pads()]))
    b.Remove(fp)

def key(x, y):
    return (int(round(float(x) * 1e6)), int(round(float(y) * 1e6)))

want_t = set()
for s in a.drop_track:
    net, p0, p1 = s.split(":")
    A, B = key(*p0.split(",")), key(*p1.split(","))
    want_t.add((net, frozenset((A, B))))
want_v = set()
for s in a.drop_via:
    net, p0 = s.split(":")
    want_v.add((net, key(*p0.split(","))))

for t in list(b.GetTracks()):
    s, e = t.GetStart(), t.GetEnd()
    if t.GetClass() == "PCB_VIA":
        k = (t.GetNetname(), (s.x, s.y))
        if k in want_v:
            out["dropped_vias"].append(dict(net=k[0], at_mm=[s.x/1e6, s.y/1e6],
                                            dia_mm=t.GetWidth()/1e6))
            b.Remove(t); want_v.discard(k)
    else:
        k = (t.GetNetname(), frozenset(((s.x, s.y), (e.x, e.y))))
        if k in want_t:
            out["dropped_tracks"].append(dict(net=k[0],
                a_mm=[s.x/1e6, s.y/1e6], b_mm=[e.x/1e6, e.y/1e6],
                width_mm=t.GetWidth()/1e6, layer=b.GetLayerName(t.GetLayer())))
            b.Remove(t); want_t.discard(k)

out["unmatched_tracks"] = [[n, sorted(f)] for n, f in sorted(want_t)]
out["unmatched_vias"] = sorted(want_v)
b.Save(str(a.board))
out["verdict"] = ("PASS" if not out["missing"] and not want_t and not want_v
                  else "FAIL")
text = json.dumps(out, indent=2, sort_keys=True)
if a.report:
    a.report.write_text(text + "\n", encoding="utf-8")
print(text)
raise SystemExit(0 if out["verdict"] == "PASS" else 1)
