#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- does a keep-out still cover the whole stackup?

Some footprints carry a rule area inside themselves.  The ESP32-S3-WROOM-1 does:
a 48 x 21 mm keep-out over its PCB antenna that forbids tracks, vias, pads,
copper pour AND footprints, on EVERY copper layer -- that is Espressif's own
requirement, encoded by the library.

When such a footprint is placed, KiCad clamps the rule area's `*.Cu` to the
layers the board has AT THAT MOMENT.  If the stackup later grows, the rule area
does NOT grow with it.  The result is a keep-out that looks correct in the
editor, is honoured exactly as written by DRC, and silently protects fewer
layers than the part requires -- so there is no violation to report and no way
to notice except to ask.

This module asks -- OF EVERY KEEP-OUT ON THE BOARD, not just a footprint's.
D-616 asked it of footprint-embedded rule areas only and found one defect;
`pcbnew.BOARD.Zones()` does not return a footprint's zones and a footprint's
does not return the board's, so asking one question could never have found the
other four.  This board carries FIVE keep-outs and every one of them was
clamped to the same four layers: `U1`'s embedded antenna area, a BOARD-LEVEL
DUPLICATE of the same antenna region with its own uuid, both M2 mounting-boss
retention keep-outs and `MK1`'s acoustic port.

For a FOOTPRINT-embedded area the claim is compared against the MASTER's own
layer set.  For a BOARD-LEVEL area there is no master, and none is needed: a
keep-out is a statement about PHYSICS -- an antenna clearance, a moulded boss,
an acoustic port -- and physics does not stop at layer two, so a keep-out that
forbids copper on some enabled copper layers and not others is under-declared
on its face.

Where a layer is unprotected the region is MEASURED on it: filled pour area,
track endpoints, via barrels.  An unprotected layer that happens to be empty is
a latent trap; an unprotected layer with copper on it is a defect that has
already happened.

Read-only.

    python3 hardware/demo/manufacturing/screen_footprint_keepouts.py \
        [-o REPORT.json]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD,
                    help="measure a CANDIDATE instead of the authority")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    import screen_land_parity as S

    libs, _proj, share = S.resolve_libraries()
    board = pcbnew.LoadBoard(str(a.board))
    board_cu = [board.GetLayerName(l) for l in board.GetEnabledLayers().CuStack()]
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, True)

    # (owner ref or None, identity, zone, master zone or None)
    subjects = []
    for fp in board.GetFootprints():
        zones = list(fp.Zones())
        if not zones:
            continue
        fpid = fp.GetFPID()
        nick = fpid.GetLibNickname().wx_str()
        name = fpid.GetLibItemName().wx_str()
        master = (pcbnew.FootprintLoad(str(libs[nick]), name)
                  if nick in libs else None)
        mzones = list(master.Zones()) if master else []
        for i, z in enumerate(zones):
            subjects.append((fp.GetReference(), "%s:%s" % (nick, name), z,
                             mzones[i] if i < len(mzones) else None))
    for z in board.Zones():
        if z.GetIsRuleArea():
            subjects.append((None, z.GetZoneName() or "(unnamed)", z, None))

    areas = []
    if True:
        for (owner, identity, z, mzone) in subjects:
            b_cu = [board.GetLayerName(l) for l in z.GetLayerSet().Seq()
                    if board.GetLayerName(l).endswith(".Cu")]
            m_cu = ([pcbnew.LayerName(l) for l in mzone.GetLayerSet().Seq()
                     if pcbnew.LayerName(l).endswith(".Cu")]
                    if mzone is not None else [])
            # A FOOTPRINT area is judged against its MASTER: the master is
            # written against KiCad's full 32-layer space and what it MEANS is
            # "every copper layer this board has".  A BOARD-LEVEL keep-out has
            # no master and is judged against the board's own stackup, because
            # a keep-out that forbids copper on four of six layers is
            # under-declared whatever anybody wrote.
            claims_all = (len(m_cu) >= len(board_cu) if mzone is not None
                          else bool(z.GetIsRuleArea()
                                    and (z.GetDoNotAllowTracks()
                                         or z.GetDoNotAllowVias()
                                         or z.GetDoNotAllowZoneFills())))
            unprotected = ([l for l in board_cu if l not in b_cu]
                           if claims_all else [])

            region = pcbnew.SHAPE_POLY_SET(z.Outline())
            region.BooleanIntersection(outline)

            per_layer = {}
            for lname in board_cu:
                lid = board.GetLayerID(lname)
                pour = 0.0
                for pz in board.Zones():
                    if pz.GetIsRuleArea() or not pz.IsOnLayer(lid):
                        continue
                    filled = pz.GetFilledPolysList(lid)
                    if filled is None:
                        continue
                    p = pcbnew.SHAPE_POLY_SET(filled)
                    p.BooleanIntersection(region)
                    pour += p.Area() / 1e12
                trk, via, nets = 0, 0, set()
                for t in board.GetTracks():
                    if t.GetClass() == "PCB_VIA":
                        if t.IsOnLayer(lid) and region.Contains(t.GetStart()):
                            via += 1
                            nets.add(t.GetNetname())
                    elif t.GetLayer() == lid and (
                            region.Contains(t.GetStart())
                            or region.Contains(t.GetEnd())):
                        trk += 1
                        nets.add(t.GetNetname())
                per_layer[lname] = {"pour_mm2": round(pour, 3),
                                    "tracks": trk, "vias": via,
                                    "nets": sorted(nets),
                                    "protected": lname in b_cu}

            offending = {l: d for l, d in per_layer.items()
                         if l in unprotected
                         and (d["pour_mm2"] > 0 or d["tracks"] or d["vias"])}
            areas.append({
                "ref": owner, "identity": identity,
                "uuid": str(z.m_Uuid.AsString()),
                "scope": ("footprint" if owner else "board"),
                "rule_area": bool(z.GetIsRuleArea()),
                "keepout": {"tracks": z.GetDoNotAllowTracks(),
                            "vias": z.GetDoNotAllowVias(),
                            "pads": z.GetDoNotAllowPads(),
                            "copperpour": z.GetDoNotAllowZoneFills(),
                            "footprints": z.GetDoNotAllowFootprints()},
                "area_total_mm2": round(z.Outline().Area() / 1e12, 3),
                "area_on_board_mm2": round(region.Area() / 1e12, 3),
                "board_copper_layers": b_cu,
                "master_copper_layer_count": len(m_cu),
                "unprotected_board_layers": unprotected,
                "per_layer": per_layer,
                "offending_layers": sorted(offending),
                "verdict": ("DEFECT" if offending else
                            "LATENT_TRAP" if unprotected else "COVERED"),
            })

    report = {"schema": 1, "board": str(a.board),
              "kicad_share": str(share) if share else None,
              "board_copper_layers": board_cu,
              "rule_areas": len(areas),
              "footprint_rule_areas": sum(1 for x in areas
                                          if x["scope"] == "footprint"),
              "board_rule_areas": sum(1 for x in areas
                                      if x["scope"] == "board"),
              "verdicts": {v: sum(1 for x in areas if x["verdict"] == v)
                           for v in sorted({x["verdict"] for x in areas})},
              "areas": areas}
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
