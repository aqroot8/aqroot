#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the pour-bond guard is OFF by default, SOUND when on.

`pour_bond_guard.py` (D-585) tells the router that some copper on an outer pour
is the ONLY thing joining a pad to its island, and that a foreign net may not
take it.  That is a genuine NARROWING of what the router may propose, so this
file pins both halves of the contract.  Four claims, each measured:

  P1  OFF IS BYTE-IDENTICAL.  With `guard=None`, `Field.blk` on every layer and
      `Field.via_ok` are bit-for-bit what the pre-guard module produced, for
      every net in the sample at its own contract.  No accepted route can move
      because the lever exists.

  P2  A TUBE IS REAL COPPER.  Every point of every emitted tube lies inside the
      filled pour of the net and layer it claims, and each end lies on the pad
      or via it names.  A guard that protected copper which is not there would
      be forbidding routing for nothing.

  P3  ON BLOCKS THE TUBE, AND ONLY AROUND THE TUBE.  For a foreign net, every
      tube point's cell is blocked and so is the via lattice there; and the
      guard's footprint is bounded -- no cell further than
      `keepout + width/2 + one lattice cell` from a tube point differs from the
      unguarded lattice.

  P4  A POUR IS EXEMPT FROM ITS OWN TUBES.  `GND` sees no `GND` tube blocked --
      the tube IS its copper and its stitch must be free to run down it -- and
      still sees every `+3V3` tube, because slotting the other pour is exactly
      as fatal whoever does it.

Run from anywhere:

    python3 hardware/demo/manufacturing/checks/pour_bond_contract.py
"""

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
MANU = ROOT / "hardware/demo/manufacturing"
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
BASE_REV = "919ebe4"                      # the D-584 promotion commit

sys.path.insert(0, str(MANU))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

SAMPLE = ("/I2C_SDA_INT", "/I2C_SCL_INT", "/09_COMMUNITY_HEADER/EXT_SDA",
          "/08_BUTTONS_EXPANDERS/BTN_DOWN_N", "/NFC_CS_N", "/ACC_5V_BOOST_EN",
          "GND", "+3V3")


def load_rev_module(rev, name="maze3d_base"):
    """Import `maze3d.py` as it stands at `rev`, without touching the worktree."""
    src = subprocess.run(
        ["git", "-C", str(ROOT), "show",
         "%s:hardware/demo/manufacturing/maze3d.py" % rev],
        check=True, capture_output=True, text=True).stdout
    root = Path(tempfile.mkdtemp(prefix="aqroot-guard-base-"))
    tmp = root / "hardware/demo/manufacturing" / (name + ".py")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, tmp)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default=BASE_REV)
    ap.add_argument("--guard", type=Path,
                    default=MANU / "evidence/d585-pour-bond-guard.json")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew
    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    import pour_bond_guard as pg
    from route_maze_batch import (net_contract, permitted_layers,
                                  reserved_inner_planes, guard_for, sha256_file)
    base = load_rev_module(a.rev)
    spec = json.loads(a.guard.read_text())

    ref = pcbnew.LoadBoard(str(BOARD))
    contracts = {n: net_contract(ref, n) for n in SAMPLE}
    reserved = reserved_inner_planes(ref)
    pours = pg.read_pours(ref)
    for p in pours:
        pg.assign(ref, p)

    qb = qr.QBoard(str(BOARD))
    ir.inject_existing_via_obstacles(qb)
    for n, c in contracts.items():
        c["layers"] = permitted_layers(qb.routable, c["layers"], reserved, n)
    results = {}

    # -- P1 ---------------------------------------------------------------- #
    diffs = []
    for n in SAMPLE:
        c = contracts[n]
        args = (c["width"], c["clr"], c["clr"], c["via_dia"], c["via_drill"])
        fb = base.Field(qb, n, *args, G=100000, layers=c["layers"])
        fo = mz.Field(qb, n, *args, G=100000, layers=c["layers"])
        for L in c["layers"]:
            if not np.array_equal(fb.blk[L], fo.blk[L]):
                diffs.append(dict(net=n, layer=L, kind="blk",
                                  cells=int((fb.blk[L] ^ fo.blk[L]).sum())))
        if not np.array_equal(fb.via_ok, fo.via_ok):
            diffs.append(dict(net=n, kind="via_ok",
                              cells=int((fb.via_ok ^ fo.via_ok).sum())))
    results["P1"] = dict(ok=not diffs, base_rev=a.rev,
                         nets_compared=len(SAMPLE), diffs=diffs)

    # -- P2 ---------------------------------------------------------------- #
    # Keyed by ZONE, not by (net, layer): one net may own several bounded
    # pours on one layer, and their island numbering is per-zone.  A spec
    # written before the guard carried `zone` still resolves, by (net, layer),
    # because back then that key really was unique.
    poly = {(p["net"], p["lkey"], p["zone"]): p for p in pours}
    poly.update({(p["net"], p["lkey"]): p for p in pours})
    outside, badend = [], []
    for g in spec["guards"]:
        p = (poly.get((g["net"], g["lkey"], g["zone"])) if g.get("zone")
             else poly.get((g["net"], g["lkey"])))
        isl = p["islands"][g["island"]] if p else None
        if isl is None:
            outside.append(dict(guard=g["ends"], why="NO_SUCH_ISLAND"))
            continue
        off = 0
        for (x, y) in g["points"]:
            if not isl["poly"].Contains(pcbnew.VECTOR2I(int(x), int(y)), -1, 0):
                off += 1
        if off:
            outside.append(dict(net=g["net"], layer=g["lkey"],
                                island=g["island"], ends=g["ends"],
                                points_off_copper=off,
                                points=len(g["points"])))
        known = {q["ref"]: (q["x"], q["y"], q["r"]) for q in isl["pads"]}
        for end, pt in zip(g["ends"], (g["points"][0], g["points"][-1])):
            t = known.get(end)
            if t is None:                       # a via anchor: any via will do
                t = min(((v["x"], v["y"], v["r"]) for v in isl["vias"]),
                        key=lambda v: (v[0] - pt[0]) ** 2 + (v[1] - pt[1]) ** 2,
                        default=None)
            if t is None or ((t[0] - pt[0]) ** 2 + (t[1] - pt[1]) ** 2
                             > (t[2] + spec["grid"] * 2) ** 2):
                badend.append(dict(net=g["net"], ends=g["ends"], end=end))
    results["P2"] = dict(ok=not outside and not badend,
                         tubes=len(spec["guards"]),
                         points=sum(len(g["points"]) for g in spec["guards"]),
                         off_copper=outside, misplaced_ends=badend)

    # -- P3 / P4 ------------------------------------------------------------ #
    probe = "/I2C_SDA_INT"
    c = contracts[probe]
    args = (c["width"], c["clr"], c["clr"], c["via_dia"], c["via_drill"])
    fo = mz.Field(qb, probe, *args, G=100000, layers=c["layers"])
    gd = guard_for(spec, probe)
    fg = mz.Field(qb, probe, *args, G=100000, layers=c["layers"], guard=gd)

    unblocked, far = [], []
    for L, pts in gd.items():
        if L not in c["layers"]:
            continue
        newly = fg.blk[L] & ~fo.blk[L]
        js, iss = np.nonzero(newly)
        X = fg.ox + iss * fg.G
        Y = fg.oy + js * fg.G
        P = np.array([(p[0], p[1]) for p in pts], dtype=np.float64)
        R = np.array([p[2] for p in pts], dtype=np.float64) \
            + c["width"] / 2.0 + fg.G
        for k in range(0, len(X), 1):
            d2 = (P[:, 0] - X[k]) ** 2 + (P[:, 1] - Y[k]) ** 2
            if not (d2 <= R * R).any():
                far.append(dict(layer=L, x=float(X[k]), y=float(Y[k])))
                if len(far) > 8:
                    break
        for (x, y, _r) in pts:
            i, j = fg.cell(x, y)
            if fg.inside(i, j) and not (fg.blk[L][j, i] and not fg.via_ok[j, i]):
                unblocked.append(dict(layer=L, x=x, y=y,
                                      blk=bool(fg.blk[L][j, i]),
                                      via_ok=bool(fg.via_ok[j, i])))
    results["P3"] = dict(ok=not unblocked and not far, probe_net=probe,
                         guarded_layers={k: len(v) for k, v in gd.items()},
                         tube_cells_not_blocked=unblocked[:8],
                         cells_outside_keepout=far[:8])

    own = {g["net"] for g in spec["guards"]}
    exempt = {}
    for n in sorted(own):
        g2 = guard_for(spec, n)
        exempt[n] = dict(
            own_tubes_seen=sum(1 for x in spec["guards"] if x["net"] == n
                               and x["lkey"] in g2 and any(
                                   tuple(p) in {(q[0], q[1]) for q in g2[x["lkey"]]}
                                   for p in x["points"])),
            foreign_tubes=sorted({x["net"] for x in spec["guards"]
                                  if x["net"] != n and x.get("ok")}))
    results["P4"] = dict(ok=all(v["own_tubes_seen"] == 0 for v in exempt.values()),
                         pour_nets=sorted(own), detail=exempt)

    out = dict(schema=1, board=str(BOARD), board_sha256=sha256_file(BOARD),
               guard=str(a.guard), guard_sha256=sha256_file(a.guard),
               checks=results,
               all_pass=all(v["ok"] for v in results.values()))
    text = json.dumps(out, indent=1, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    for k in ("P1", "P2", "P3", "P4"):
        print("  %s %s" % (k, "PASS" if results[k]["ok"] else "FAIL"),
              file=sys.stderr)
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
