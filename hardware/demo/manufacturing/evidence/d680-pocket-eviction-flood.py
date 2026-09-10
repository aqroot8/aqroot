#!/usr/bin/env python3
"""READ-ONLY: with THESE nets' routed copper held out of a WINDOW, does the
U21/L4 boost pocket reach the BQ25185_SYS trunk at the SYS_MAIN width?

Same flood as probe_pocket.py, under screen_corridor_blockers.Without, so the
eviction it reports is the eviction `route_maze_batch --evict` executes."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path("/home/aqroot8/aqroot-demo/hardware/demo/manufacturing")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "hardware/beta-v2/checks"))
import qrouter as qr, maze3d as mz, incremental_router as ir
from route_maze_batch import net_contract, permitted_layers, reserved_inner_planes
from screen_corridor_blockers import Without

BOARD = HERE.parent / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET = "/01_POWER_TREE/BQ25185_SYS"
G, MM = 25000, qr.MM
WIN = (48.0, 16.0, 64.0, 46.0)
qb = qr.QBoard(str(BOARD))
ir.inject_existing_via_obstacles(qb)
res = reserved_inner_planes(qb.b)
c = net_contract(qb.b, NET)
lays = [L for L in permitted_layers(qb.routable, c["layers"], res, NET)]
OUTER = [L for L in lays if L in ("F", "B")]
TARGETS = [(52.000, 36.700, "F", "trunk vertex F.Cu"),
           (56.000, 20.100, "B", "trunk B.Cu near L2"),
           (47.100, 31.500, "F", "trunk F.Cu SW")]


def flood(f, i0, j0, sl):
    free = {L: ~f.blk[L][sl] for L in OUTER}
    via = f.via_ok[sl]
    seen = {L: np.zeros_like(free[L]) for L in OUTER}
    si, sj = f.cell(int(57.715 * MM), int(36.200 * MM))
    si, sj = si - i0, sj - j0
    if not free["B"][sj, si]:
        return None, None
    seen["B"][sj, si] = True
    cur = {L: seen[L].copy() for L in OUTER}
    for _ in range(20000):
        moved = False
        nxt = {L: mz._shift_or(cur[L], free[L]) & free[L] & ~seen[L] for L in OUTER}
        for L in OUTER:
            for M in OUTER:
                if L != M:
                    nxt[M] |= (seen[L] | nxt[L]) & via & free[M] & ~seen[M]
        for L in OUTER:
            if nxt[L].any():
                moved = True
                seen[L] |= nxt[L]
            cur[L] = nxt[L]
        if not moved:
            break
    return seen, free


def ask(nets, box, w_mm, tag):
    w = int(round(w_mm * MM))
    if nets:
        f0 = mz.Field(qb, NET, w, c["clr_pad"], c["clr"], c["via_dia"],
                      c["via_drill"], G=G, layers=lays)
        ctx = Without(qb, f0, nets, tuple(int(round(v * MM)) for v in box))
    else:
        ctx = None
    if ctx is not None:
        ctx.__enter__()
    try:
        f = mz.Field(qb, NET, w, c["clr_pad"], c["clr"], c["via_dia"],
                     c["via_drill"], G=G, layers=lays)
        i0, j0 = f.cell(int(WIN[0] * MM), int(WIN[1] * MM))
        i1, j1 = f.cell(int(WIN[2] * MM), int(WIN[3] * MM))
        sl = (slice(j0, j1 + 1), slice(i0, i1 + 1))
        seen, free = flood(f, i0, j0, sl)
        out = dict(tag=tag, width_mm=w_mm, nets=nets, box=box)
        if seen is None:
            out["verdict"] = "SEED_BLOCKED"
            return out
        out["cells"] = {L: int(seen[L].sum()) for L in OUTER}
        hits = []
        for (tx, ty, L, nm) in TARGETS:
            i, j = f.cell(int(tx * MM), int(ty * MM))
            i, j = i - i0, j - j0
            if 0 <= j < seen[L].shape[0] and 0 <= i < seen[L].shape[1]:
                hits.append("%s=%s" % (nm, "REACHED" if seen[L][j, i]
                                       else ("free" if free[L][j, i] else "blocked")))
        out["targets"] = hits
        out["verdict"] = "OPEN" if any("REACHED" in h for h in hits) else "SEALED"
        return out
    finally:
        if ctx is not None:
            ctx.__exit__(None, None, None)


if __name__ == "__main__":
    BOX = [54.0, 30.0, 58.6, 40.5]
    FB, BUF, SCL = ("/01_POWER_TREE/ACC_5V_FB",
                    "/09_COMMUNITY_HEADER/EXT_SCL_BUF",
                    "/09_COMMUNITY_HEADER/EXT_SCL")
    SMALL = [55.5, 32.0, 58.0, 39.5]
    CASES = [
        ([], BOX, "control"),
        ([FB], BOX, "FB"),
        ([BUF], BOX, "BUF"),
        ([SCL], BOX, "SCL"),
        ([FB, BUF], BOX, "FB+BUF"),
        ([FB, SCL], BOX, "FB+SCL"),
        ([BUF, SCL], BOX, "BUF+SCL"),
        ([FB, BUF, SCL], BOX, "FB+BUF+SCL"),
        ([FB, BUF], SMALL, "FB+BUF small window"),
        ([FB, BUF, SCL], SMALL, "FB+BUF+SCL small window"),
    ]
    res_out = []
    for w in (0.800,):
        for nets, box, tag in CASES:
            r = ask(nets, box, w, tag)
            print("%.3f %-28s %-12s %s" % (w, tag, r["verdict"],
                                           " ".join(r.get("targets", []))), flush=True)
            res_out.append(r)
    Path("w/d680/evict-flood.json").write_text(json.dumps(res_out, indent=1) + "\n")
