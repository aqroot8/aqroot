#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: where does this run's SUB-CLASS-WIDTH copper lie?

D-609.  `--relief-extra-width` lets a relief stitch launch at the width the
board's own `.kicad_dru` pad-escape necking rule already grants inside the ten
fine-pitch power-package courtyards it names.  That rule is written with
`intersectsCourtyard`, and KiCad evaluates area membership PER OBJECT -- so a
track that merely clips a courtyard inherits the relaxation along its WHOLE
length.  `FBV2_P2_ROUTING_PLAN.md` section 17 clause 2 names that shape as the
thing a relief must never lean on.

Real KiCad DRC decides whether the copper is LEGAL.  This decides whether it is
legal for the reason the doctrine wants: it reports, per added track below its
class's own width floor, whether the track is WHOLLY INSIDE a named courtyard,
merely INTERSECTS one, or lies OUTSIDE every one of them.  An `OUTSIDE` track
that DRC passed is a track that passed by some other rule and owes an
explanation; an `INTERSECTS` track is the doctrine's own warning, made visible
so the next transaction can author the strict `enclosedByArea` licence instead.

D-610 ADDS THE LICENCE ITSELF.  A `PAD_ESCAPE_RUN_<REF>` rule area plus a
`.kicad_dru` `track_width` rule naming that net inside it is the strict form
clause 2 asks for, so this file now also asks the question the doctrine
actually cares about: is each narrow track WHOLLY INSIDE a run area whose rule
grants THIS net THIS width?  That verdict is `LICENSED` and it is the only one
that satisfies clause 3's own-area sufficiency -- membership is tested per
track against each area on its own, never against the union, so a neck cannot
pass by borrowing its neighbour's licence.

    python3 audit_narrow_copper.py AUTHORITY.kicad_pcb CANDIDATE.kicad_pcb
"""
import hashlib, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import pcbnew
import qrouter as qr
import maze3d as mz
from route_maze_batch import DRU_CLASS, BOARD_TRACK_MIN

auth, cand = Path(sys.argv[1]), Path(sys.argv[2])


def tracks(path):
    b = pcbnew.LoadBoard(str(path))
    out = {}
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        k = (t.GetNetname(), b.GetLayerName(t.GetLayer()), int(t.GetWidth()),
             int(t.GetStart().x), int(t.GetStart().y),
             int(t.GetEnd().x), int(t.GetEnd().y))
        out[k] = t
    return b, out


ba, A = tracks(auth)
bc, C = tracks(cand)
added = sorted(set(C) - set(A))

qb = qr.QBoard(str(cand))
neck = mz.neck_rule(qb)
courts = {}
if neck is not None:
    for ref, poly in neck.polys.items():
        courts[ref] = poly

# THE RUN AREAS THIS BOARD CARRIES, and what each one's rule actually grants.
# A rule area is not copper, so it is read straight off the candidate; the
# grant is read out of the `.kicad_dru` by the same `maze3d.width_licence` the
# router had to satisfy before it laid a micron.  An area with no rule is
# reported with `licence_nm: null` and licenses nothing.
run_areas = {}
for z in bc.Zones():
    if not z.GetIsRuleArea():
        continue
    name = z.GetZoneName()
    if not name.startswith(mz.ESCAPE_RUN_AREA_PREFIX):
        continue
    ref = name[len(mz.ESCAPE_RUN_AREA_PREFIX):].replace("_", ".", 1)
    run_areas[name] = dict(zone=z, ref=ref)

doc = dict(schema=1, authority=str(auth), candidate=str(cand),
           authority_sha256=hashlib.sha256(auth.read_bytes()).hexdigest(),
           candidate_sha256=hashlib.sha256(cand.read_bytes()).hexdigest(),
           necking_rule=(None if neck is None else
                         dict(min_width_mm=neck.min_w / 1e6,
                              courtyards=sorted(neck.refs))),
           added_tracks=len(added), narrow=[])
for k in added:
    net, layer, w, x0, y0, x1, y1 = k
    cls = bc.FindNet(net).GetNetClassName()
    floor = max(BOARD_TRACK_MIN, DRU_CLASS.get(cls, {}).get("width", 0))
    if w >= floor:
        continue
    # Sample the CENTRELINE densely; a segment is INSIDE only when every
    # sample, and both caps extended by width/2, lie in ONE courtyard.
    half = w / 2.0
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    pts = []
    n = max(2, int(L / 25000) + 1)
    for i in range(n + 1):
        s = -half + (L + 2 * half) * i / n
        pts.append((x0 + ux * s, y0 + uy * s))
    inside, hits = [], []
    for ref, poly in courts.items():
        got = [poly.Collide(pcbnew.VECTOR2I(int(px), int(py))) for px, py in pts]
        if all(got):
            inside.append(ref)
        elif any(got):
            hits.append(ref)
    # `enclosedByArea` is ALL-OR-NOTHING per object and per area, so each area
    # is asked on its own -- exactly the shape KiCad evaluates, and exactly
    # what section 17 clause 3 means by own-area sufficiency.
    licensed, area_hits = [], []
    for name, a in run_areas.items():
        got = [a["zone"].Outline().Collide(pcbnew.VECTOR2I(int(px), int(py)))
               for px, py in pts]
        if not any(got):
            continue
        lic = mz.width_licence(qb, net, a["ref"])
        if all(got) and lic is not None and lic <= w:
            licensed.append(dict(area=name, licence_mm=lic / 1e6))
        else:
            area_hits.append(dict(area=name, wholly_inside=bool(all(got)),
                                  licence_mm=(None if lic is None
                                              else lic / 1e6)))
    doc["narrow"].append(dict(
        net=net, netclass=cls, layer=layer, width_mm=w / 1e6,
        class_floor_mm=floor / 1e6, mm=round(L / 1e6, 4),
        a_mm=[round(x0 / 1e6, 4), round(y0 / 1e6, 4)],
        b_mm=[round(x1 / 1e6, 4), round(y1 / 1e6, 4)],
        verdict=("LICENSED" if licensed else
                 "INSIDE" if inside else "INTERSECTS" if hits else "OUTSIDE"),
        licensed_by=licensed, run_areas_touched=area_hits,
        wholly_inside=sorted(inside), intersects=sorted(hits)))

doc["narrow_mm"] = round(sum(d["mm"] for d in doc["narrow"]), 4)
doc["run_areas"] = sorted(run_areas)
doc["verdicts"] = {v: sum(1 for d in doc["narrow"] if d["verdict"] == v)
                   for v in ("LICENSED", "INSIDE", "INTERSECTS", "OUTSIDE")}
# The one number a reviewer needs: narrow copper that no strict licence covers.
doc["unlicensed_mm"] = round(sum(d["mm"] for d in doc["narrow"]
                                 if d["verdict"] != "LICENSED"), 4)
print(json.dumps(doc, indent=1, sort_keys=True, default=str))
