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
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="aqroot-demo-protected-"))
    before = objects(stage(a.ref, tmp / "pre"))
    after = objects(stage(None, tmp / "post"))
    import collections
    empty = collections.Counter()
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
    doc = dict(schema=1, ref=a.ref, identical=not diff,
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
