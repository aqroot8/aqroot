#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: what does routing THIS net cost the pours?

D-582 and D-583 promoted pours on BOTH outer layers -- `+3V3` on `F.Cu`, `GND`
on `B.Cu` -- and their entire value was connectivity a pour delivers with no
track and no via: 12 edges each, bonded by `connect_pads` alone.  That value is
also a liability, and this screen exists because the liability is now the
dominant term in every remaining routing decision on this board.

A signal track laid across an outer layer is a SLOT through the pour that owns
it.  KiCad re-pours around the slot, the pour splits, and every pad that was
bonded ACROSS the cut goes open.  Gate clause 4 of `route_maze_batch.py` refuses
any run in which a net regresses, so one orphaned pour pad refuses the whole
transaction -- however many real edges it closed.  Measured on this board: a
`--partial` run on `/I2C_SCL_INT` + `/I2C_SDA_INT` closes ELEVEN retained open
edges (8 -> 3 and 8 -> 2) with zero attributable DRC, and is refused because it
orphans exactly four pads -- `+3V3` `J1.35`, `R19.1`, `R26.1` and `GND` `U3.12`
-- that no committed repair lever can re-bond.

So the useful question before proposing a batch is not "does this net route".
It is "does this net route WITHOUT orphaning a pour pad", and the two answers
have to be measured separately because only the second one predicts the gate.

METHOD, and why each step is the expensive one it is:

  * ONE NET PER SCRATCH BOARD.  Attribution is the whole point.  A batch tells
    you the pours broke; it does not tell you which net's copper broke them,
    and the gate refuses on the net, so that is the unit the answer must be in.
  * THE REAL KiCad FILL ENGINE, not a model of it.  `connect_pads` bonding,
    island removal and the re-pour around a new slot are KiCad's own behaviour;
    a screen that predicted them would be predicting exactly the thing it is
    supposed to measure.  Every candidate is refilled by `kicad-cli` before it
    is measured.
  * THE AUTHORITATIVE LEDGER, not a private connectivity model.  The verdict
    this screen reports has to be the same quantity gate clause 4 will compute,
    or it is not a screen for that gate.
  * NO DRC.  This is the ONE authoritative step it drops, and it is what makes
    the screen affordable enough to run per net.  A `PROMOTABLE` verdict here
    is therefore a PREDICTION, never a promotion: the full gate still has to
    run DRC, preservation and the zone inventory before any copper moves.

Verdicts:

    NO_COPPER        the proposer laid nothing -- the net did not route at all
    POUR_DAMAGE      it routed, and orphaned N pad(s) of a pour-owning net;
                     the orphans are named, because which pad it is decides
                     whether a barrel, a neck or a refloorplan is the answer
    NET_REGRESSION   it routed and regressed a PLANE-LESS net -- a hard refusal
                     with no repair, reported separately because it means
                     something different
    PROMOTABLE       it routed, closed edges, and no net regressed

Nothing here writes the authoritative board.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
LEDGER = HERE / "routing_ledger.py"
DRIVER = HERE / "route_maze_batch.py"
# The sidecars `kicad-cli` needs beside the board: the rules it must obey and
# the netclass assignments the contract is read from.  A scratch board without
# them is a different board.
SIDECARS = ("aqroot-Beta-v2.kicad_dru", "aqroot-Beta-v2.kicad_pro",
            "aqroot-Beta-v2.kicad_prl")


def ledger_of(board, out):
    subprocess.run([sys.executable, str(LEDGER), "--board", str(board),
                    str(out)], check=True, capture_output=True, text=True)
    return {n["net"]: n["open_edges"]
            for n in json.loads(Path(out).read_text())["nets"]}


def groups_of(path):
    doc = json.loads(Path(path).read_text())
    return {n["net"]: {tuple(sorted(g)) for g in n["groups"]} for n in doc["nets"]}


def refill(board):
    """Ask the REAL engine to re-pour, and save what it produced."""
    return subprocess.run(
        ["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
         "--format", "json", "--units", "mm", "-o", os.devnull, str(board)],
        text=True, capture_output=True).returncode


def orphaned_pads(before_groups, after_groups, net):
    """Pads that LEFT a group and now sit alone -- the pour pads a slot cut."""
    b = before_groups.get(net, set())
    a = after_groups.get(net, set())
    was = {p for g in b for p in g if len(g) > 1}
    now_alone = {p for g in a if len(g) == 1 for p in g}
    return sorted(was & now_alone)


def trial(net, args, tmproot):
    work = Path(tmproot) / net.strip("/").replace("/", "_")
    work.mkdir(parents=True, exist_ok=True)
    scratch = work / BOARD.name
    shutil.copy2(BOARD, scratch)
    for name in SIDECARS:
        src = PROJECT / name
        if src.exists():
            shutil.copy2(src, work / name)

    cmd = [sys.executable, str(DRIVER), "--propose", str(scratch),
           "--grid", str(args.grid), "--via-cost", str(args.via_cost)]
    if args.partial:
        cmd += ["--partial"]
        if args.attempt_cap:
            cmd += ["--attempt-cap", str(args.attempt_cap)]
    if args.join_max_mm:
        cmd += ["--join-max-mm", str(args.join_max_mm)]
    if args.neck:
        cmd += ["--neck", "--neck-max-mm", str(args.neck_max_mm)]
    if args.guard:
        cmd += ["--guard", str(args.guard)]
    proc = subprocess.run(cmd + [net], text=True, capture_output=True)
    if proc.returncode != 0:
        return dict(net=net, verdict="PROPOSER_ERROR",
                    error=proc.stderr.strip()[-400:])
    res = json.loads(proc.stdout)["results"][0]

    rc = refill(scratch)
    after_path = work / "ledger-after.json"
    after = ledger_of(scratch, after_path)
    after_groups = groups_of(after_path)

    delta = {n: after.get(n, 0) - args.base.get(n, 0)
             for n in set(after) | set(args.base)
             if after.get(n, 0) != args.base.get(n, 0)}
    improved = sorted(n for n, d in delta.items() if d < 0)
    regressed = sorted(n for n, d in delta.items() if d > 0)
    orphans = {n: orphaned_pads(args.base_groups, after_groups, n)
               for n in regressed}

    total_before = sum(args.base.values())
    total_after = sum(after.values())
    rec = dict(net=net, routed=bool(res.get("ok")), mode=res.get("mode"),
               reason=res.get("reason"), mm=round(res.get("mm", 0.0) or 0.0, 3),
               vias=res.get("vias"), refill_rc=rc,
               net_edges_before=args.base.get(net, 0),
               net_edges_after=after.get(net, 0),
               board_edges_before=total_before, board_edges_after=total_after,
               board_delta=total_after - total_before,
               improved=improved, regressed=regressed, orphaned_pads=orphans)
    pour = [n for n in regressed if n in args.pour_nets]
    plain = [n for n in regressed if n not in args.pour_nets]
    if not improved:
        rec["verdict"] = "NO_COPPER"
    elif plain:
        rec["verdict"] = "NET_REGRESSION"
    elif pour:
        rec["verdict"] = "POUR_DAMAGE"
    else:
        rec["verdict"] = "PROMOTABLE"
    print("  %-44s %-15s board %+d  %s" % (
        net, rec["verdict"], rec["board_delta"],
        ";".join("%s:%s" % (k.split("/")[-1], ",".join(v))
                 for k, v in orphans.items() if v)),
          file=sys.stderr, flush=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nets", nargs="*", help="default: every open retained net "
                                            "that does not own a pour")
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--via-cost", type=float, default=1.5)
    ap.add_argument("--partial", action="store_true")
    ap.add_argument("--attempt-cap", type=int, default=0)
    ap.add_argument("--join-max-mm", type=float, default=0.0)
    ap.add_argument("--neck", action="store_true")
    ap.add_argument("--neck-max-mm", type=float, default=0.0)
    ap.add_argument("--guard", type=Path,
                    help="a pour_bond_guard.py spec; the screen then measures "
                         "what a net costs the pours WITH the bond tubes held "
                         "clear, which is the question the gate will ask")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    sys.path.insert(0, str(HERE))
    from route_maze_batch import EXCLUDE, plane_nets, sha256_file

    with tempfile.TemporaryDirectory(prefix="aqroot-demo-pourdmg-") as tmp:
        base_path = Path(tmp) / "ledger-base.json"
        a.base = ledger_of(BOARD, base_path)
        a.base_groups = groups_of(base_path)
        a.pour_nets = set(plane_nets(BOARD))
        nets = a.nets or sorted(
            n for n, v in a.base.items()
            if v > 0 and n not in a.pour_nets and n not in EXCLUDE)
        print("base %d open edges; %d nets to screen; pour-owning: %s"
              % (sum(a.base.values()), len(nets), ", ".join(sorted(a.pour_nets))),
              file=sys.stderr, flush=True)
        with ThreadPoolExecutor(max_workers=a.jobs) as pool:
            out = list(pool.map(lambda n: trial(n, a, tmp), nets))

    verdicts = {}
    for r in out:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    doc = dict(schema=1, board=str(BOARD), board_sha256=sha256_file(BOARD),
               grid=a.grid, partial=bool(a.partial), neck=bool(a.neck),
               guard=str(a.guard) if a.guard else None,
               guard_sha256=sha256_file(a.guard) if a.guard else None,
               base_open_edges=sum(a.base.values()),
               pour_owning_nets=sorted(a.pour_nets),
               summary=dict(verdicts=verdicts), nets=out)
    text = json.dumps(doc, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
