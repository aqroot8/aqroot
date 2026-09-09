#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: DO THE BOARD'S TWO LAUNCHERS AGREE ABOUT THIS LAND?

This tool chain has TWO ways to start a route off a pad and they are not the
same function:

  `maze3d.pad_escapes`   the LATTICE launcher.  `QBoard.escape` casts rays from
                         the pad centre, `_pocket_escapes` floods the pad core,
                         and -- only where both are empty -- `offcentre_escapes`
                         is asked.  Every candidate must be a free cell of the
                         WHOLE-BOARD raster.  **`route_join` uses this, so the
                         GATE uses this**, and `src_escapes` / `dst_escapes` in
                         a `route_maze_batch.py` report are counts of ITS
                         answer.

  `maze3d.offcentre_route`  the EXACT launcher (D-634).  It never calls
                         `pad_escapes`; it opens an exact board coordinate with
                         `point_terminals` and proves the stub with
                         `verify_laid`.  Its own docstring says the thing
                         `route_join` "could never do is START".

  `screen_evicted_corridor.py`, `screen_net_tap.py`, `screen_relay_wall.py`
  and `screen_lane_geometry.py` all drive the SECOND one.  A `NO_LEGAL_ESCAPE`
  in any of their reports is therefore a statement about the EXACT launcher,
  and a reader who takes it as "the gate cannot start here" may be reading a
  refusal the gate does not make.

This screen puts BOTH questions to the same land, on the same `Field`, at the
same width and pitch, and reports whether they agree.

    python3 screen_launcher_parity.py NET --land REF.PIN --to REF.PIN \
        [--pitch 100000,50000] -o OUT.json

`--to` names the pad the launch is aimed at, because both launchers take a
direction hint and a launch is not a property of a pad alone.  The board is
never written and its sha256 is re-read at exit.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

import qrouter as qr                                          # noqa: E402
import incremental_router as ir                               # noqa: E402
import maze3d as mz                                           # noqa: E402
from route_maze_batch import (net_contract,                   # noqa: E402
                              reserved_inner_planes, permitted_layers)

AUTHORITY = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
M = 1000000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("net")
    ap.add_argument("--board", type=Path, default=AUTHORITY)
    ap.add_argument("--land", action="append", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--pitch", default="100000,50000")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    for suffix in (".kicad_dru", ".kicad_pro"):
        if not a.board.with_suffix(suffix).is_file():
            raise SystemExit("--board %s has no %s beside it"
                             % (a.board, suffix))
    before = hashlib.sha256(a.board.read_bytes()).hexdigest()
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    c = net_contract(qb.b, a.net)
    far = list(permitted_layers(qb.routable, c["layers"], reserved, a.net))
    pads = {p["ref"]: p for isl in mz.net_islands(qb, a.net) for p in isl}
    for ref in list(a.land) + [a.dst]:
        if ref not in pads:
            raise SystemExit("%s is not a pad of %s" % (ref, a.net))
    dst = pads[a.dst]

    rows, disagreements = [], 0
    for ref in a.land:
        pad = pads[ref]
        for G in [int(x) for x in a.pitch.split(",")]:
            f = mz.Field(qb, a.net, c["width"], c["clr_pad"], c["clr"],
                         c["via_dia"], c["via_drill"], G=G, layers=far)
            f.offcentre = True
            t0 = time.time()
            lat = mz.pad_escapes(qb, f, pad, (dst["x"], dst["y"]), limit=8)
            t1 = time.time()
            m = qb.mark()
            try:
                r = mz.offcentre_route(qb, f, pad, dst, G=G)
            finally:
                qb.revert(m)
            agree = bool(lat) == (r.get("reason") != "NO_LEGAL_ESCAPE")
            disagreements += 0 if agree else 1
            rows.append(dict(
                land=ref, to=a.dst, grid_nm=G, width_nm=c["width"],
                lattice_escapes=len(lat),
                lattice_at=[[e["layer"], round(e["x"] / M, 4),
                             round(e["y"] / M, 4), round(e["w"] / M, 4)]
                            for e in lat[:8]],
                lattice_seconds=round(t1 - t0, 2),
                exact_ok=bool(r.get("ok")), exact_reason=r.get("reason"),
                exact_why=r.get("why"), exact_mm=r.get("mm"),
                exact_seconds=round(time.time() - t1, 2),
                agree=agree))
            print(" %-9s G=%-7d lattice=%-2d exact=%s %s  %s"
                  % (ref, G, len(lat), r.get("ok"), r.get("reason"),
                     "AGREE" if agree else "DISAGREE"), flush=True)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(
        schema=1, board=str(a.board), board_sha256=before,
        authoritative_unchanged=(before == after),
        board_is_authority=(a.board.resolve() == AUTHORITY.resolve()),
        net=a.net, contract={k: v for k, v in c.items()
                             if k != "trunk_floor"}, far=far,
        question=("does `maze3d.pad_escapes` -- the launcher `route_join` and "
                  "therefore the GATE uses -- agree with "
                  "`maze3d.offcentre_route`, the launcher every corridor, tap, "
                  "relay and lane screen drives, about whether this land can "
                  "START"),
        method=("read-only; both launchers are handed the SAME `Field` object "
                "at the SAME width and pitch, the exact one's copper is "
                "reverted, and the board's sha256 is re-read at exit"),
        disagreements=disagreements, rows=rows)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print("disagreements: %d of %d" % (disagreements, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
