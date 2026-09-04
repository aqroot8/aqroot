#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what current does this run's NARROW copper carry?

D-609 answered `FBV2_P2_ROUTING_PLAN.md` section 17 clause 4's width REVIEW
TRIGGER by hand, in prose, once.  Every relief run after it owes the same
answer, so this file is that arithmetic made reproducible: IPC-2221B at THIS
board's own copper, applied to the sub-class-width tracks a candidate adds,
plus the barrel each one feeds.

    I = k * dT^0.44 * A^0.725        A in mil^2, I in amperes
    k = 0.048 external, 0.024 internal          (IPC-2221B fig. 6-4)

THE METHOD IS SELF-CHECKED, NOT ASSERTED.  `.kicad_dru` section 5 prints its
own table -- "0.300 mm carries 1.0 A" among others -- derived independently
years before this file existed.  The run below reproduces that table first and
reports the residual; a method that cannot re-derive the board's own published
figures has no business ruling on a bond.

A BARREL IS A CONDUCTOR TOO.  Its copper is the plated wall, an annulus of
`drill` diameter and `plating` thickness, and it is compared against the neck
that feeds it -- because the question a reviewer actually asks is WHICH of the
two is the bottleneck, and on this board it has always been the neck.

    python3 audit_bond_ampacity.py AUTHORITY.kicad_pcb CANDIDATE.kicad_pcb
"""
import hashlib, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import pcbnew
from route_maze_batch import DRU_CLASS, BOARD_TRACK_MIN

# This board's stackup, transcribed from the fab notes it is ordered against.
OZ_MM = 0.0348                  # 1 oz copper, finished thickness
PLATING_MM = 0.025              # JLCPCB plated through-hole wall, minimum
MIL2_PER_MM2 = 1.0 / 0.00064516
K_EXT, K_INT = 0.048, 0.024
OUTER = {"F.Cu", "B.Cu"}


def ampacity(area_mm2, dT, external=True):
    """IPC-2221B current for a conductor of this cross-section."""
    a = area_mm2 * MIL2_PER_MM2
    return (K_EXT if external else K_INT) * (dT ** 0.44) * (a ** 0.725)


def track_area(width_mm, external=True):
    return width_mm * OZ_MM


def barrel_area(drill_mm, plating_mm=PLATING_MM):
    """Plated wall of a through hole: an annulus at the mean diameter."""
    return math.pi * (drill_mm + plating_mm) * plating_mm


def resistance_mohm(length_mm, area_mm2):
    """Copper at 20 degC: rho = 1.724e-5 ohm.mm."""
    return 1.724e-5 * length_mm / area_mm2 * 1000.0


def objects(path):
    b = pcbnew.LoadBoard(str(path))
    trk, via = {}, {}
    for t in b.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            trk[(t.GetNetname(), b.GetLayerName(t.GetLayer()),
                 int(t.GetWidth()), int(t.GetStart().x), int(t.GetStart().y),
                 int(t.GetEnd().x), int(t.GetEnd().y))] = t
        else:
            via[(t.GetNetname(), int(t.GetWidth()), int(t.GetDrill()),
                 int(t.GetPosition().x), int(t.GetPosition().y))] = t
    return b, trk, via


def main():
    auth, cand = Path(sys.argv[1]), Path(sys.argv[2])
    dT = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    ba, A, AV = objects(auth)
    bc, C, CV = objects(cand)

    # SELF-CHECK against the board's own printed table.
    table = [(0.200, None), (0.250, None), (0.300, 1.0), (0.350, None),
             (0.400, None), (0.500, 1.45), (0.600, None), (1.200, None)]
    check = [dict(width_mm=w,
                  amps=round(ampacity(track_area(w), dT), 3),
                  dru_printed=p,
                  residual=(None if p is None
                            else round(ampacity(track_area(w), dT) - p, 3)))
             for w, p in table]

    doc = dict(schema=1, authority=str(auth), candidate=str(cand),
               authority_sha256=hashlib.sha256(auth.read_bytes()).hexdigest(),
               candidate_sha256=hashlib.sha256(cand.read_bytes()).hexdigest(),
               dT_K=dT, copper_mm=OZ_MM, plating_mm=PLATING_MM,
               method_selfcheck=check, necks=[], barrels=[], nets={})

    per_net = {}
    for k in sorted(set(C) - set(A)):
        net, layer, w, x0, y0, x1, y1 = k
        cls = bc.FindNet(net).GetNetClassName()
        floor = max(BOARD_TRACK_MIN, DRU_CLASS.get(cls, {}).get("width", 0))
        if w >= floor:
            continue
        ext = layer in OUTER
        area = track_area(w / 1e6, ext)
        L = math.hypot(x1 - x0, y1 - y0) / 1e6
        row = dict(net=net, netclass=cls, layer=layer, external=ext,
                   width_mm=w / 1e6, class_floor_mm=floor / 1e6,
                   mm=round(L, 4), area_mm2=round(area, 6),
                   amps=round(ampacity(area, dT, ext), 3),
                   amps_dT20=round(ampacity(area, 20.0, ext), 3),
                   mohm=round(resistance_mohm(L, area), 3))
        doc["necks"].append(row)
        p = per_net.setdefault(net, dict(net=net, neck_mm=0.0, mohm=0.0,
                                         min_amps=None, widths=set()))
        p["neck_mm"] += L
        p["mohm"] += row["mohm"]
        p["widths"].add(row["width_mm"])
        p["min_amps"] = (row["amps"] if p["min_amps"] is None
                         else min(p["min_amps"], row["amps"]))

    for k in sorted(set(CV) - set(AV)):
        net, dia, drill, x, y = k
        area = barrel_area(drill / 1e6)
        doc["barrels"].append(dict(
            net=net, dia_mm=dia / 1e6, drill_mm=drill / 1e6,
            wall_area_mm2=round(area, 6),
            amps=round(ampacity(area, dT), 3),
            equiv_outer_track_mm=round(area / OZ_MM, 3),
            xy_mm=[round(x / 1e6, 3), round(y / 1e6, 3)]))

    for n, p in per_net.items():
        p["widths"] = sorted(p["widths"])
        p["neck_mm"] = round(p["neck_mm"], 4)
        p["mohm"] = round(p["mohm"], 3)
        # Clause 4 separates the caps: a REVIEW trigger at 6.0 mm of total
        # narrow-width run, and it is a ruling rather than an automatic stop.
        p["clause4_width_review"] = p["neck_mm"] > 6.0
        doc["nets"][n] = p
    doc["narrow_mm"] = round(sum(r["mm"] for r in doc["necks"]), 4)
    print(json.dumps(doc, indent=1, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
