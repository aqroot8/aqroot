#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: is a land's ESCAPE POCKET sealed, or was it a raster?

D-631.  `screen_stitch_window.py` retired the 8.0 mm stitch window as the pour
block's binding constraint and left a sharper question in its place.  Every
`NO_BODY_VIA_SITE` island on this board reads `UNREACHABLE` -- no via-legal cell
of ANY kind is reachable from ANY of its escapes at ANY distance -- and the
reason is the same everywhere: the escape opens into a FREE POCKET of a few
hundred lattice cells that is sealed on its own layer.

    /01_POWER_TREE/BQ25185_SYS  C28.1      19 cells    C26.2   152
                                C27.1     166          R68.1   164
                                L4.1      429          SW9.2  1677 (206 via-legal)
                                L2.1  176085 (138810 via-legal)  <- NOT sealed
    +3V3                        R129.1     85          R39.1    72

Those are the numbers that make `UNREACHABLE` falsifiable rather than merely
disappointing: an escape into 176,085 free cells is a DISTANCE problem, and one
into 19 is a SEAL.

A SEAL AT 0.100 mm IS NOT YET A SEAL.  That is this board's most expensive
lesson, learned three times -- `BTN_DOWN_N` closed at 0.0333 mm, `EXT_SDA` at
0.025 mm, `LED_K` at 0.020 mm -- all after refusing at 0.100 mm.  A pocket whose
mouth is 0.08 mm wide is sealed on a 0.100 mm lattice and open on a 0.025 mm
one, and nothing in a cell count says which kind it is.

SO MEASURE THE POCKET IN MILLIMETRES, NOT IN CELLS.  Area is pitch-invariant:
a pocket that is genuinely sealed keeps its AREA as the lattice refines (the
cell count grows exactly as 1/G^2 and nothing else changes), and a pocket whose
seal was a rasterisation artifact GROWS in area the moment the lattice can
express its mouth.  The ratio is the verdict, and it costs one flood-fill per
(land, escape, pitch).

    area_mm2 flat across the ladder      -> SEALED.  A finer pitch buys nothing;
                                            this is placement or eviction.
    area_mm2 grows                       -> RASTER.   Ladder it; the mouth is
                                            narrower than the coarse pitch.

WHAT IS MEASURED, NOT ASSUMED

  * THE CONTRACT IS THE GATE'S -- `net_contract`, `permitted_layers`,
    `reserved_inner_planes`, `DRU_CLASS` floors, `--escape-floor`, `--guard`,
    exactly as `route_maze_batch.propose` assembles them.
  * THE POCKET IS `stitch_pad`'s OWN FREE SPACE, `~field.blk[L]`, flooded with
    `maze3d._shift_or` -- the same 8-connected dilation the stitch and the maze
    both use -- from the same `pad_escapes` launch points.
  * VIA-LEGAL CELLS INSIDE THE POCKET ARE COUNTED, because a pocket with a
    legal barrel site in it is not a wall at all whatever its size.
  * NOTHING IS WRITTEN.
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

PITCHES = (100000, 50000, 25000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="+")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--guard", type=Path)
    ap.add_argument("--escape-floor", action="store_true")
    ap.add_argument("--neck", action="store_true")
    ap.add_argument("--stitch-via", default=None, metavar="DIA:DRILL")
    ap.add_argument("--escape-limit", type=int, default=12)
    ap.add_argument("--pitch", type=int, action="append", default=None)
    ap.add_argument("--orphans-only", action="store_true", default=True)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import numpy as np
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from screen_stitch_window import free_pocket
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, load_guard,
                                  DRU_CLASS, ANNULAR_MIN)

    pitches = tuple(sorted(set(a.pitch or PITCHES), reverse=True))
    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    stitch_via = (tuple(int(v) for v in a.stitch_via.split(":"))
                  if a.stitch_via else None)

    out = []
    for net in a.nets:
        if not mz.has_plane(qb, net):
            out.append(dict(net=net, ok=False, reason="NO_PLANE"))
            continue
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        over = DRU_CLASS.get(c["netclass"], {})
        via_dia, via_drill = c["via_dia"], c["via_drill"]
        if stitch_via:
            via_drill = max(stitch_via[1], over.get("drill", 0))
            via_dia = max(stitch_via[0], via_drill + 2 * ANNULAR_MIN)
        floor = over.get("width") if a.escape_floor else None
        islands = mz.net_islands(qb, net)
        if len(islands) < 2:
            continue
        body = max(islands, key=len)
        targets = [i for i in islands if i is not body]
        rec = dict(net=net, netclass=c["netclass"],
                   body=[p["ref"] for p in body], lands=[])
        per_land = {}
        for G in pitches:
            field = mz.Field(qb, net, c["width"], c["clr_pad"], c["clr"],
                             via_dia, via_drill, G=G, layers=layers,
                             neck=mz.neck_rule(qb) if a.neck else None,
                             guard=guard_for(spec, net) if spec else None,
                             escape_floor=floor)
            cell_mm2 = (G / 1e6) ** 2
            for island in targets:
                for pad in island:
                    key = pad["ref"]
                    t0 = time.time()
                    es = mz.pad_escapes(qb, field, pad, None, a.escape_limit)
                    best = None
                    for e in es:
                        n, seen = free_pocket(mz, np, field, e)
                        if n <= 0:
                            continue
                        vok = int((seen & field.via_ok).sum())
                        if best is None or n > best[0]:
                            best = (n, vok, e['layer'])
                    row = dict(grid_nm=G, escapes=len(es),
                               cells=(best[0] if best else 0),
                               area_mm2=round((best[0] if best else 0)
                                              * cell_mm2, 4),
                               via_legal_in_pocket=(best[1] if best else 0),
                               layer=(best[2] if best else None),
                               seconds=round(time.time() - t0, 1))
                    per_land.setdefault(key, dict(
                        pad=key,
                        island=[p["ref"] for p in island],
                        rungs=[]))["rungs"].append(row)
                    print("  %-30s %-10s %.4f mm  esc=%-3d pocket=%9.3f mm2"
                          "  via-legal=%d"
                          % (net[-30:], key, G / 1e6, row["escapes"],
                             row["area_mm2"], row["via_legal_in_pocket"]),
                          file=sys.stderr, flush=True)
            del field
        for k in sorted(per_land):
            r = per_land[k]
            areas = [x["area_mm2"] for x in r["rungs"] if x["escapes"]]
            r["area_min_mm2"] = min(areas) if areas else None
            r["area_max_mm2"] = max(areas) if areas else None
            r["growth"] = (round(max(areas) / min(areas), 3)
                           if areas and min(areas) > 0 else None)
            r["verdict"] = ("NO_ESCAPE_AT_ANY_PITCH" if not areas else
                            "HAS_VIA_SITE" if any(
                                x["via_legal_in_pocket"]
                                for x in r["rungs"]) else
                            "RASTER" if r["growth"] and r["growth"] >= 2.0 else
                            "SEALED")
            rec["lands"].append(r)
        out.append(rec)

    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        pitches=list(pitches), escape_floor=bool(a.escape_floor),
        neck=bool(a.neck),
        stitch_via=list(stitch_via) if stitch_via else None,
        guard=str(a.guard) if a.guard else None,
        guard_sha256=(hashlib.sha256(a.guard.read_bytes()).hexdigest()
                      if a.guard else None),
        question=("for every land whose escape opens into a free pocket, does "
                  "that pocket keep its AREA as the lattice refines -- a real "
                  "seal -- or grow, which would make it a rasterisation "
                  "artifact a finer pitch can open"),
        method=("read-only; maze3d._shift_or flood over ~field.blk[layer] from "
                "maze3d.pad_escapes launch points, at each pitch, on the same "
                "contract/guard/escape-floor route_maze_batch.propose builds; "
                "area in mm2 so the rungs are comparable"),
        nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
