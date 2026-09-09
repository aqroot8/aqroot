#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: does the CORRIDOR move when the eviction opens the
LAUNCH?

D-670 section 3 named the gap and this board has now shown it three times: a
POCKET verdict is NECESSARY, not SUFFICIENT.  `screen_escape_pocket.py --blame`
answers about the LAUNCH -- it floods from the land and reports what a rip-up
would do to the reachable AREA and to the count of via-legal cells -- and a
land whose pocket opens can still have no route.  `/ACC_PWR_EN` `U3.20` opened
and stayed `NO_PATH`; `/I2C_SCL_INT` `U16.3` opened from ZERO escapes to FIVE
and stayed `NO_PATH`.

Nothing could ask the second question without a gate run.  This does, in the
units a transaction speaks:

  ARMS   each arm names the routed objects to hold out -- by NET inside a
         stated window, or by exact OBJECT SIGNATURE -- and the pair is asked
         with exactly that set absent.  Arm `BASE` (no holds) is always run
         first, so a refusal is never mistaken for a measurement.
  PITCH  every arm is laddered over the stated pitches and STOPS at the first
         one that closes.  A `NO_PATH` is a statement about a PITCH as much as
         about a board (D-651).
  POOL   optionally, on top of an arm, drop each foreign net inside a stated
         window one at a time AND all at once.  The all-at-once rung is the
         UPPER BOUND: still `NO_PATH` and no containment-bounded rip-up in that
         window opens the corridor, whatever the pocket said.

Every trial is laid on the live QBoard by `maze3d.offcentre_route` and
reverted.  The board is never written and its sha256 is re-read at exit.

    python3 screen_evicted_corridor.py NET --from REF.PAD --to REF.PAD \
        --arms ARMS.json [--pitch 100000,50000,25000] \
        [--pool X0,Y0,X1,Y1] [--pool-grid 50000] -o OUT.json

ARMS.json:
    {"schema": 1,
     "arms": [{"name": "hub",
               "nets": ["/09_COMMUNITY_HEADER/WAKE_GATE_S"],
               "window_mm": [54.4, 51.4, 59.6, 60.0]},
              {"name": "rxen",
               "objects": [{"kind": "via", "net": "/SX1262_RXEN",
                            "at_mm": [58.7, 78.3]},
                           {"kind": "track", "net": "...", "layer": "B",
                            "a_mm": [x, y], "b_mm": [x, y]}]}]}

A `nets` + `window_mm` arm holds out exactly what `route_maze_batch.py --evict
--evict-window` would remove: a routed object of a named net whose own bounding
box is WHOLLY inside the window.  An `objects` arm holds out exactly what
`--detour-spec` would name.  The two may be combined in one arm.
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

import qrouter as qr             # noqa: E402
import incremental_router as ir  # noqa: E402
import maze3d as mz              # noqa: E402
from route_maze_batch import (net_contract, reserved_inner_planes,  # noqa: E402
                              permitted_layers)
from screen_corridor_blockers import (Without, WithoutObjects,      # noqa: E402
                                      corridor_objects)

AUTHORITY = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
M = 1000000


def nm(v):
    return int(round(float(v) * M))


def resolve(qb, arm, far):
    """The routed objects this arm holds out, by net-in-window and by signature."""
    out, missing = [], []
    if arm.get("nets"):
        w = arm.get("window_mm")
        if not w:
            raise SystemExit("arm %r names nets and no window_mm: a net-level "
                             "hold with no window is a board-wide deletion, "
                             "which is not a transaction anybody can execute"
                             % arm.get("name"))
        box = tuple(nm(x) for x in w)
        out += corridor_objects(qb, far, box, None, set(arm["nets"]))
        out += [h for h in qb.holes
                if h.net in set(arm["nets"]) and h.tag.startswith("via")
                and h.bbox(0)[0] >= box[0] and h.bbox(0)[1] >= box[1]
                and h.bbox(0)[2] <= box[2] and h.bbox(0)[3] <= box[3]]
    for spec in arm.get("objects", ()):
        hits = []
        if spec["kind"] == "track":
            a = (nm(spec["a_mm"][0]), nm(spec["a_mm"][1]))
            b = (nm(spec["b_mm"][0]), nm(spec["b_mm"][1]))
            for L in qb.shapes:
                if spec.get("layer") and L != spec["layer"]:
                    continue
                for s in qb.shapes[L]:
                    if s.tag != "track" or s.net != spec["net"]:
                        continue
                    p, q = (int(s.x0), int(s.y0)), (int(s.x1), int(s.y1))
                    if (p, q) in ((a, b), (b, a)):
                        hits.append(s)
        elif spec["kind"] == "via":
            at = (nm(spec["at_mm"][0]), nm(spec["at_mm"][1]))
            for L in qb.shapes:
                for s in qb.shapes[L]:
                    if s.tag == "via" and s.net == spec["net"] \
                       and (int(s.cx), int(s.cy)) == at:
                        hits.append(s)
            for h in qb.holes:
                a_, b_, c_, d_ = h.bbox(0)
                if h.net == spec["net"] and h.tag.startswith("via") \
                   and abs((a_ + c_) // 2 - at[0]) <= 1 \
                   and abs((b_ + d_) // 2 - at[1]) <= 1:
                    hits.append(h)
        else:
            raise SystemExit("arm %r: unknown object kind %r"
                             % (arm.get("name"), spec["kind"]))
        if not hits:
            missing.append(spec)
        out += hits
    return out, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("net")
    ap.add_argument("--board", type=Path, default=AUTHORITY)
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--arms", type=Path, required=True)
    ap.add_argument("--pitch", default="100000,50000,25000")
    ap.add_argument("--pool", default=None,
                    help="X0,Y0,X1,Y1 in mm: after the LAST arm, drop each "
                         "foreign net inside this window one at a time and "
                         "then all at once, on top of that arm")
    ap.add_argument("--pool-grid", type=int, default=50000)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    for suffix in (".kicad_dru", ".kicad_pro"):
        if not a.board.with_suffix(suffix).is_file():
            raise SystemExit("--board %s has no %s beside it" % (a.board, suffix))
    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    spec = json.loads(a.arms.read_text())
    pitches = [int(x) for x in a.pitch.split(",")]

    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    c = net_contract(qb.b, a.net)
    far = list(permitted_layers(qb.routable, c["layers"], reserved, a.net))
    islands = mz.net_islands(qb, a.net)
    pads = {p["ref"]: p for isl in islands for p in isl}
    for r in (a.src, a.dst):
        if r not in pads:
            raise SystemExit("%s is not a pad of %s" % (r, a.net))
    src, dst = pads[a.src], pads[a.dst]

    def field_at(G):
        return mz.Field(qb, a.net, c["width"], c["clr_pad"], c["clr"],
                        c["via_dia"], c["via_drill"], G=G, layers=far)

    def ask(f, G):
        m = qb.mark()
        try:
            return mz.offcentre_route(qb, f, src, dst, G=G)
        finally:
            qb.revert(m)

    rows = []
    arms = [dict(name="BASE")] + list(spec.get("arms", ()))
    last = None
    for arm in arms:
        for G in pitches:
            f = field_at(G)
            objs, missing = resolve(qb, arm, far)
            if missing:
                rows.append(dict(step="ARM_OBJECT_NOT_FOUND",
                                 arm=arm["name"], missing=missing))
                print(" %-10s OBJECT NOT ON THIS BOARD: %s"
                      % (arm["name"], json.dumps(missing)), flush=True)
            t0 = time.time()
            if objs:
                with WithoutObjects(qb, f, objs):
                    r = ask(f, G)
            else:
                r = ask(f, G)
            rows.append(dict(step="ARM", arm=arm["name"], grid_nm=G,
                             held_out=len(objs), ok=bool(r.get("ok")),
                             mm=r.get("mm"), vias=r.get("vias"),
                             layers=r.get("layers"), reason=r.get("reason"),
                             why=r.get("why"),
                             seconds=round(time.time() - t0, 1)))
            print(" %-10s G=%-7d out=%-3d -> %s %s (%.0f s)"
                  % (arm["name"], G, len(objs), r.get("ok"),
                     r.get("reason") or round(r.get("mm") or 0, 3),
                     time.time() - t0), flush=True)
            if r.get("ok"):
                break
        last = arm

    if a.pool and last is not None:
        box = tuple(nm(x) for x in a.pool.split(","))
        G = a.pool_grid
        f = field_at(G)
        objs, _ = resolve(qb, last, far)
        with WithoutObjects(qb, f, objs):
            pool = sorted({s.net for L in far for s in qb.shapes[L]
                           if s.tag in ("track", "via") and s.net
                           and s.net != a.net
                           and s.bbox(0)[0] >= box[0] and s.bbox(0)[1] >= box[1]
                           and s.bbox(0)[2] <= box[2] and s.bbox(0)[3] <= box[3]})
            rows.append(dict(step="POOL", on_arm=last["name"], grid_nm=G,
                             nets=pool, box_mm=[x / M for x in box]))
            print(" POOL on %s: %d nets" % (last["name"], len(pool)), flush=True)
            for n in pool:
                t0 = time.time()
                with Without(qb, f, [n], box):
                    r = ask(f, G)
                rows.append(dict(step="POOL_DROP", on_arm=last["name"], drop=n,
                                 grid_nm=G, ok=bool(r.get("ok")),
                                 mm=r.get("mm"), vias=r.get("vias"),
                                 reason=r.get("reason"),
                                 seconds=round(time.time() - t0, 1)))
                print("  +drop %-46s -> %s %s"
                      % (n, r.get("ok"),
                         r.get("reason") or round(r.get("mm") or 0, 3)),
                      flush=True)
            t0 = time.time()
            with Without(qb, f, pool, box):
                r = ask(f, G)
            rows.append(dict(step="POOL_ALL", on_arm=last["name"], drop=pool,
                             grid_nm=G, ok=bool(r.get("ok")), mm=r.get("mm"),
                             vias=r.get("vias"), reason=r.get("reason"),
                             seconds=round(time.time() - t0, 1)))
            print("  +drop ALL AT ONCE -> %s %s"
                  % (r.get("ok"), r.get("reason") or round(r.get("mm") or 0, 3)),
                  flush=True)

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(schema=1, board=str(a.board), board_sha256=sha,
               authoritative_unchanged=(sha == after),
               board_is_authority=(a.board.resolve() == AUTHORITY.resolve()),
               net=a.net, src=a.src, dst=a.dst, far=far,
               pitches=pitches, arms=str(a.arms), arms_spec=spec,
               pool_box_mm=a.pool, pool_grid_nm=a.pool_grid,
               question=("when a rip-up opens a land's POCKET, does the "
                         "CORRIDOR move -- and at which PITCH"),
               method=("read-only; every trial laid on the live QBoard by "
                       "maze3d.offcentre_route and reverted; holds are the "
                       "same units route_maze_batch.py licenses -- a net "
                       "inside a window, or one object signature; the board's "
                       "sha256 is re-read at exit"),
               rows=rows,
               any_closed=any(r.get("ok") for r in rows
                              if r["step"] in ("ARM", "POOL_DROP", "POOL_ALL")))
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if doc["any_closed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
