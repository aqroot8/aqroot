#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: can a NARROW `--plane-block` box move a FORCED
plane crossing off the middle of the slot, and what does the plane pay for it?

A haul through a reserved inner plane cuts a slot in it, and every trace on the
referencing layers that CROSSES that slot pays a return detour of roughly twice
the distance from the crossing to the nearest END of the slot
(`checks/plane_return_path.py` RP2/RP4).  So where a crossing is FORCED, the
cheap answer is to move an END of the slot next to it.

`screen_plane_haul.py --plane-block` already exists for that, and D-636 spent
it as a HALF-PLANE -- forbid the plane east of the crossing so the slot must
START past it -- at every rung from x = 59.0 down to 57.0.  All `NO_PATH`, and
the decision concluded the crossing was forced and the licence cost exactly one
unpublished number.

A NARROW box BESIDE the crossing is a different question and it was never
asked.  The haul does not have to leave the plane to get past it; it only has
to go ROUND it, and going round moves both slot ends.  This sweeps that box and
prices EVERY rung with the board's own clause, because the first three boxes
tried by hand traded RP4 for RP1: the detour that shortens the return arc
closes a loop and leaves anchor-less slivers of the reference plane.

REPORTS BOTH CLAUSES FOR EVERY RUNG.  A sweep that recorded only the clause it
was aiming at would publish "RP4 PASSES at 3.314 mm" and hide that the same
copper took the plane from ONE outline to THREE.

    python3 screen_plane_block_sweep.py NET --a REF.PAD --b REF.PAD \
        --plane I4 --far F,B,I2,I4 --edge-ns 1.0 \
        --box X0,Y0,X1,Y1 [--box ...] -o OUT.json
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("net")
    ap.add_argument("--board")
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--plane", required=True,
                    help="short name of the PLANE layer the box blocks")
    ap.add_argument("--far", default=None)
    ap.add_argument("--edge-ns", type=float, required=True,
                    help="passed straight to checks/plane_return_path.py; it "
                         "has no default there by design and none here")
    ap.add_argument("--fraction", type=float, default=None)
    ap.add_argument("--box", action="append", default=[],
                    help="X0,Y0,X1,Y1 in mm. Repeatable. An EMPTY sweep asks "
                         "the unblocked haul alone, which is the base rung")
    ap.add_argument("--work", type=Path, default=Path("w/plane-blocks"))
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    a.work.mkdir(parents=True, exist_ok=True)
    rungs = [None] + list(a.box)
    rows = []
    for k, box in enumerate(rungs):
        tag = "base" if box is None else "b%02d" % (k - 1)
        hp = a.work / ("haul-%s.json" % tag)
        rp = a.work / ("rp-%s.json" % tag)
        cmd = [sys.executable, "screen_plane_haul.py", a.net,
               "--a", a.a, "--b", a.b, "-o", str(hp)]
        if a.board:
            cmd += ["--board", a.board]
        if a.far:
            cmd += ["--far", a.far]
        if box is not None:
            cmd += ["--plane-block", "%s:%s" % (a.plane, box)]
        subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True)
        if not hp.is_file():
            rows.append(dict(tag=tag, box=box, haul_ok=False,
                             reason="HAUL_DID_NOT_REPORT"))
            print(" %-5s %-34s HAUL DID NOT REPORT" % (tag, box), flush=True)
            continue
        h = json.loads(hp.read_text())
        if not h["ok"]:
            rows.append(dict(tag=tag, box=box, haul_ok=False,
                             reason=h.get("reason"), why=h.get("why")))
            print(" %-5s %-34s %s" % (tag, box, h.get("reason")), flush=True)
            continue
        pc = [sys.executable, "checks/plane_return_path.py",
              "--haul", str(hp), "--edge-ns", str(a.edge_ns), "-o", str(rp)]
        if a.fraction is not None:
            pc += ["--fraction", str(a.fraction)]
        subprocess.run(pc, cwd=str(HERE), capture_output=True, text=True)
        if not rp.is_file():
            rows.append(dict(tag=tag, box=box, haul_ok=True, priced=False,
                             mm=h["mm"], vias=h["vias_count"]))
            print(" %-5s %-34s PRICE DID NOT REPORT" % (tag, box), flush=True)
            continue
        p = json.loads(rp.read_text())
        cl = {c["clause"]: c for c in p["clauses"]}
        row = dict(tag=tag, box=box, haul_ok=True, priced=True,
                   mm=h["mm"], vias=h["vias_count"], layers=h["layers"],
                   board_sha256=h["board_sha256"],
                   authoritative_unchanged=h["authoritative_unchanged"],
                   outlines_before=cl["RP1"]["outlines_before"],
                   outlines_after=cl["RP1"]["outlines_after"],
                   area_lost_mm2=cl["RP1"]["area_lost_mm2"],
                   anchors_off_body=cl["RP1"]["anchors_off_body"],
                   crossings=cl["RP2"]["crossings"],
                   grazes=cl["RP2"]["grazes"],
                   budget_mm=cl["RP4"]["budget_mm"],
                   worst_detour_mm=cl["RP4"].get("worst_admitted_detour_mm"),
                   verdict={k: bool(v["ok"]) for k, v in cl.items()},
                   all_pass=all(v["ok"] for v in cl.values()))
        rows.append(row)
        print(" %-5s %-34s %7.3f mm  outlines %d -> %d  detour %6.3f/%0.3f  %s"
              % (tag, box, h["mm"], row["outlines_before"],
                 row["outlines_after"], row["worst_detour_mm"] or 0.0,
                 row["budget_mm"],
                 "ALL PASS" if row["all_pass"] else
                 "REFUSED " + ",".join(sorted(k for k, v
                                              in row["verdict"].items()
                                              if not v))),
              flush=True)

    doc = dict(schema=1, net=a.net, a=a.a, b=a.b, plane=a.plane, far=a.far,
               edge_ns=a.edge_ns, fraction=a.fraction,
               question=("which NARROW --plane-block box moves a FORCED plane "
                         "crossing off the middle of the slot WITHOUT "
                         "severing the plane"),
               method=("read-only; screen_plane_haul.py lays and reverts every "
                       "trial and re-reads the board's sha256, and "
                       "checks/plane_return_path.py prices the exact copper it "
                       "dumped.  BOTH clauses are recorded for every rung"),
               rungs=len(rungs), rows=rows,
               any_all_pass=any(r.get("all_pass") for r in rows))
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    print(" any_all_pass: %s" % doc["any_all_pass"], flush=True)
    return 0 if doc["any_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
