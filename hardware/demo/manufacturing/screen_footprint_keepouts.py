#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- does a footprint's OWN keep-out still cover the whole stackup?

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

This module asks.  For every footprint-embedded rule area it compares the
board's copper-layer set against the MASTER's, and where the board's is
narrower it MEASURES what is actually on the unprotected layers inside the
on-board part of the region: filled pour area, track endpoints, via barrels.
An unprotected layer that happens to be empty is a latent trap; an unprotected
layer with copper on it is a defect that has already happened.

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
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    import screen_land_parity as S

    libs, _proj, share = S.resolve_libraries()
    board = pcbnew.LoadBoard(str(BOARD))
    board_cu = [board.GetLayerName(l) for l in board.GetEnabledLayers().CuStack()]
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, True)

    areas = []
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
            b_cu = [board.GetLayerName(l) for l in z.GetLayerSet().Seq()
                    if board.GetLayerName(l).endswith(".Cu")]
            m_cu = ([pcbnew.LayerName(l) for l in mzones[i].GetLayerSet().Seq()
                     if pcbnew.LayerName(l).endswith(".Cu")]
                    if i < len(mzones) else [])
            # The master is written against KiCad's full 32-layer space; what it
            # MEANS is "every copper layer this board has".
            master_is_all_copper = len(m_cu) >= len(board_cu)
            unprotected = ([l for l in board_cu if l not in b_cu]
                           if master_is_all_copper else [])

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
                "ref": fp.GetReference(), "identity": "%s:%s" % (nick, name),
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

    report = {"schema": 1, "kicad_share": str(share) if share else None,
              "board_copper_layers": board_cu,
              "footprint_rule_areas": len(areas),
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
