#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- is the ACCEPTED copper byte-identical across a promotion?

`verify_promotion.py` already proves that nothing was REMOVED and that every
ADDED object lies on a claimed net, which together imply that no unclaimed net
moved.  This file measures that implication directly for the nets the Demo
scope names as accepted and protected, because an implication is a good proof
and a measurement is a better report: the answer wanted in a decision record is
"`ACC_5V_SW_EN` still has exactly these 23 objects", not "it follows that it
must".

The protected set is read from the Demo scope, not invented here:

  * `ACC_5V_SW_EN` and `ACC_3V3_SW*`  -- switched accessory power, explicitly
    "already safely routed and must be preserved";
  * the three `FRONT_RGB_*_N` replacement nets;
  * `XGPIO4` / `XGPIO5` and their header nets -- the only expansion GPIO the
    Demo keeps public;
  * every `BAT_*` net -- the retained battery/power safety architecture that
    D-269 and D-186 govern.

Read-only: both boards are copies in a temporary directory.

    python3 hardware/demo/manufacturing/protected_copper.py --ref HEAD
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

PROTECTED = re.compile(
    r"(^|/)(ACC_5V_SW_EN|ACC_3V3_SW\w*|FRONT_RGB_[RGB]_N|XGPIO[45]"
    r"(_HDR)?|BAT_\w+)$")


def objects(path):
    """Protected-net track/via signatures, keyed by net, independent of UUID.

    A MULTISET, not a set.  This board carries a handful of exactly coincident
    duplicate objects (three of them on `BAT_PROTECTED_P` and `BAT_RAW`), and a
    set would both under-count them and hide the day one of them disappears.
    """
    import collections
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = collections.defaultdict(collections.Counter)
    for t in board.GetTracks():
        net = t.GetNetname()
        if not PROTECTED.search(net):
            continue
        if t.GetClass() == "PCB_VIA":
            sig = ("via", t.GetStart().x, t.GetStart().y, t.GetWidth(),
                   t.GetDrill())
        else:
            sig = ("trk", board.GetLayerName(t.GetLayer()),
                   t.GetStart().x, t.GetStart().y,
                   t.GetEnd().x, t.GetEnd().y, t.GetWidth())
        out[net][sig] += 1
    return dict(out)


def stage(rev, work):
    work.mkdir(parents=True, exist_ok=True)
    target = work / BOARD.name
    if rev is None:
        target.write_bytes(BOARD.read_bytes())
    else:
        src = BOARD.relative_to(ROOT)
        target.write_bytes(subprocess.run(
            ["git", "-C", str(ROOT), "show", "%s:%s" % (rev, src)],
            capture_output=True, check=True).stdout)
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD",
                    help="git revision holding the PRE-promotion board")
    # D-806.  ONE DECLARED WORD: a via that kept its position, net and drill and
    # grew to EXACTLY hole + 0.200 mm (JLCPCB's annular relationship) is not a
    # change to the protected architecture.  Only pairs listed in the
    # declaration are forgiven; `identical` still reports the strict truth and
    # `identical_except_declared` is the gate.  Control: `--control-undeclared`
    # removes one declared row and the run must FAIL.
    ap.add_argument("--declared-via-growth", type=Path, default=None)
    ap.add_argument("--control-undeclared", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="aqroot-demo-protected-"))
    before = objects(stage(a.ref, tmp / "pre"))
    after = objects(stage(None, tmp / "post"))
    import collections
    empty = collections.Counter()
    declared = []
    if a.declared_via_growth:
        dec = json.loads(a.declared_via_growth.read_text())
        declared = [v for v in dec["vias"]
                    if v["dia_to_nm"] == v["drill_nm"] + dec["rule_nm"]]
        if a.control_undeclared:
            prot = [v for v in declared if PROTECTED.search(v["net"])]
            declared = [v for v in declared if v is not (prot[0] if prot else None)]
    forgiven = []
    for v in declared:
        net = v["net"]
        if not PROTECTED.search(net):
            continue
        old = ("via", v["at_nm"][0], v["at_nm"][1], v["dia_from_nm"], v["drill_nm"])
        new = ("via", v["at_nm"][0], v["at_nm"][1], v["dia_to_nm"], v["drill_nm"])
        b, f = before.get(net, empty), after.get(net, empty)
        if b[old] >= 1 and f[new] >= 1 and b[new] < f[new] and f[old] < b[old]:
            forgiven.append(dict(net=net, at_mm=[v["at_nm"][0] / 1e6, v["at_nm"][1] / 1e6],
                                 dia_from_mm=v["dia_from_nm"] / 1e6, dia_to_mm=v["dia_to_nm"] / 1e6,
                                 drill_mm=v["drill_nm"] / 1e6))
    strict_before, strict_after = before, after
    before = {n: collections.Counter(c) for n, c in before.items()}
    after = {n: collections.Counter(c) for n, c in after.items()}
    for g in forgiven:
        x, y = int(round(g["at_mm"][0] * 1e6)), int(round(g["at_mm"][1] * 1e6))
        sig_old = ("via", x, y, int(round(g["dia_from_mm"] * 1e6)), int(round(g["drill_mm"] * 1e6)))
        sig_new = ("via", x, y, int(round(g["dia_to_mm"] * 1e6)), int(round(g["drill_mm"] * 1e6)))
        before[g["net"]][sig_old] -= 1
        before[g["net"]][sig_new] += 1
        before[g["net"]] += collections.Counter()
    strict = any(strict_before.get(n, empty) != strict_after.get(n, empty)
                 for n in set(strict_before) | set(strict_after))
    moved = sorted(set(before) | set(after))
    diff = {n: dict(before=sum(before.get(n, empty).values()),
                    after=sum(after.get(n, empty).values()),
                    lost=sum((before.get(n, empty)
                              - after.get(n, empty)).values()),
                    gained=sum((after.get(n, empty)
                                - before.get(n, empty)).values()))
            for n in moved
            if before.get(n, empty) != after.get(n, empty)}
    counts = {n: sum(after.get(n, empty).values()) for n in moved}
    doc = dict(schema=1, ref=a.ref, identical=not strict and not diff,
               identical_except_declared=not diff,
               declared_via_growth=forgiven,
               declaration=str(a.declared_via_growth) if a.declared_via_growth else None,
               control_undeclared=a.control_undeclared,
               nets=len(moved), objects=sum(counts.values()),
               differences=diff, counts=counts)
    text = json.dumps(doc, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if not diff else 1


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
    raise SystemExit(main())
