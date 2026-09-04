#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: can the nets an `--evict-whole` would rip up
REBUILD themselves?

`screen_corridor_blockers.py` questions 2W and 3W name a transaction: these
whole nets go away board-wide, and the corridor opens.  What neither question
asks is the OTHER half of the contract.  Clause 4 of `route_maze_batch.py`
requires every evicted net to end the run no worse off than it started, and an
evicted net is re-proposed from nothing -- so a net whose CURRENT copper the
router can no longer reproduce at today's congestion makes the whole
transaction impossible however wide the corridor it opens.

That is not hypothetical.  D-602 measured it: the `J3 -> U10` USB corridor is
`RIPUP_WHOLE_SET` on both connector edges and `/I2C_SDA_INT` is load-bearing in
both sets -- with it excluded the entire remaining pool gone still returns
`NO_PATH`.  `/I2C_SDA_INT` has 9 pads over a 101 mm span and 2 open edges
today, and stripped whole it rebuilds to **4**.  The transaction was refused
before a single gate run was spent on it, and that is what this file is for.

METHOD, and it is deliberately the transaction's OWN unit:

  * the eviction is applied by `route_maze_batch.evict_copper` itself, on a
    scratch copy, with the same `--evict-whole` semantics and the same corridor
    windows the real run would use.  A screen that modelled the rip-up its own
    way would answer a question nobody can execute.
  * islands are then read from the STRIPPED BOARD's own KiCad connectivity, not
    from the obstacle model.  `maze3d.net_islands` calls `BuildConnectivity`,
    so a context manager that only hides obstacle shapes leaves it reporting
    the un-evicted grouping -- the first cut of this screen made exactly that
    mistake and reported `/I2C_SDA_INT` rebuilding perfectly because it never
    saw the strip at all.
  * every MST edge is measured with `emit=False`, so no edge sees the copper an
    earlier one would have laid and every net is measured as if it had the
    board to itself.

OPTIMISTIC BY CONSTRUCTION, and that is the point.  `open_after` is a LOWER
BOUND on what the real run would leave open, so `REFUSE` is reliable and `OK`
is only a licence to spend the gate run.  Nothing here writes the authoritative
board or promotes copper.
"""

import argparse
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


def centroid(group, key):
    return sum(p[key] for p in group) / float(len(group))


def measure(board_path, nets, grid, via_cost, escape_limit):
    """{net: {islands, edges, open_after}} on the board as it stands."""
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes)

    qb = qr.QBoard(str(board_path))
    ir.inject_existing_via_obstacles(qb)
    reserved = reserved_inner_planes(qb.b)
    out = {}
    for net in nets:
        c = net_contract(qb.b, net)
        layers = permitted_layers(qb.routable, c["layers"], reserved, net)
        field = mz.Field(qb, net, c["width"], c["clr"], c["clr"],
                         c["via_dia"], c["via_drill"], G=grid, layers=layers)
        islands = mz.net_islands(qb, net)
        edges = []
        for (i, j) in mz.island_mst(islands):
            src, dst = islands[i], islands[j]
            r = mz.route_join(qb, field, src, dst, escape_limit, via_cost,
                              emit=False)
            edges.append(dict(
                src=[p["ref"] for p in src], dst=[p["ref"] for p in dst],
                ok=bool(r.get("ok")), reason=r.get("reason"),
                mm=round(r.get("mm", 0.0), 3),
                direct_mm=round(math.hypot(
                    centroid(src, "x") - centroid(dst, "x"),
                    centroid(src, "y") - centroid(dst, "y")) / 1e6, 3)))
        out[net] = dict(netclass=c["netclass"], layers=list(layers),
                        islands=len(islands), edges=edges,
                        open_now=len(islands) - 1,
                        open_after=sum(1 for e in edges if not e["ok"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--net", action="append", default=[], required=True,
                    metavar="NET",
                    help="a BENEFICIARY net -- the one the corridor is being "
                         "opened for.  Repeatable; also defines the eviction "
                         "corridor windows, exactly as the real run does")
    ap.add_argument("--evict", action="append", default=[], required=True,
                    metavar="NET",
                    help="a net the transaction would rip up WHOLE and "
                         "re-propose; repeatable")
    ap.add_argument("--evict-margin-mm", type=float, default=3.0)
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--escape-limit", type=int, default=8)
    ap.add_argument("--keep", type=Path,
                    help="keep the stripped scratch board here")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import subprocess
    from route_maze_batch import sha256_file

    board_sha = sha256_file(a.board)
    tmp = Path(tempfile.mkdtemp(prefix="aqroot-demo-evict-rebuild-"))
    scratch = tmp / a.board.name
    shutil.copyfile(str(a.board), str(scratch))

    # THE REAL EVICTOR, in its own child, exactly as `gate()` invokes it.
    report = tmp / "eviction.json"
    cmd = ([sys.executable, str(HERE / "route_maze_batch.py"),
            "--evict-apply", str(scratch), "--evict-report", str(report),
            "--evict-whole", "--evict-margin-mm", str(a.evict_margin_mm)]
           + [x for n in a.evict for x in ("--evict", n)]
           + list(dict.fromkeys(a.net + a.evict)))
    subprocess.run(cmd, check=True, capture_output=True)
    eviction = json.loads(report.read_text())

    nets = list(dict.fromkeys(a.net + a.evict))
    before = measure(a.board, nets, a.grid, a.via_cost, a.escape_limit)
    after = measure(scratch, nets, a.grid, a.via_cost, a.escape_limit)

    rows, refused = [], []
    for n in nets:
        evicted = n in set(a.evict)
        row = dict(net=n, evicted=evicted,
                   open_now=before[n]["open_now"],
                   open_after=after[n]["open_after"],
                   islands_after_strip=after[n]["islands"],
                   removed=eviction["removed_by_net"].get(n, 0),
                   edges=after[n]["edges"])
        # An evicted net must come back at least as connected as it left; a
        # BENEFICIARY only has to improve.  Both are clause 4 read one net at a
        # time, and `open_after` is a lower bound, so a failure here is final.
        row["regresses"] = (row["open_after"] > row["open_now"])
        if row["regresses"]:
            refused.append(n)
        rows.append(row)

    gain = sum(r["open_now"] - r["open_after"] for r in rows)
    doc = dict(schema=1, board=str(a.board), board_sha256=board_sha,
               beneficiaries=list(a.net), evicted=sorted(set(a.evict)),
               evict_margin_mm=a.evict_margin_mm,
               removed_count=eviction["removed_count"],
               removed_by_net=eviction["removed_by_net"],
               dangling_unevictable=eviction["dangling_unevictable"],
               verdict=("REFUSE" if refused else
                        "OK" if gain > 0 else "NO_GAIN"),
               regressing_nets=refused,
               optimistic_edge_gain=gain,
               note=("open_after is measured with emit=False on a board the "
                     "real evictor stripped, so it is a LOWER BOUND on what "
                     "the gate would leave open: REFUSE is reliable, OK is a "
                     "licence to spend the gate run"),
               nets=rows)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    if a.keep:
        shutil.copyfile(str(scratch), str(a.keep))
    for r in rows:
        print("  %-40s %-9s now=%-2d after=%-2d %s"
              % (r["net"], "EVICTED" if r["evicted"] else "beneficiary",
                 r["open_now"], r["open_after"],
                 "REGRESSES" if r["regresses"] else ""),
              file=sys.stderr)
    print("  VERDICT %s  optimistic edge gain %+d"
          % (doc["verdict"], gain), file=sys.stderr)
    print(text)
    shutil.rmtree(str(tmp), ignore_errors=True)
    return 0 if doc["verdict"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
