#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- diff two PAIR-SWEEP artifacts and say exactly which island
pairs changed verdict, and which did not.

WHY THIS IS A TRACKED DRIVER.  `screen_offcentre_hop.py` answers a question of
the form "over this net set, at these widths, on these layers, which open
island pairs close?"  Every interesting use of it is an A/B: one arm is the
board as it stands and the other changes exactly one thing -- a far layer, a
width ladder, a barrel ladder, an instrument.  The finding is never the arm; it
is the DIFF, and a diff computed by eye or by a throwaway one-liner is a diff
that is computed differently every time.

WHAT IT PROVES.  Both arms must have been run against the SAME board `sha256`
-- otherwise the diff is measuring copper, not the lever -- and that is checked
and refused rather than assumed.  Every pair present in either arm is reported
in exactly one of four classes:

    GAINED     refused in the base arm, CLOSES in the test arm
    LOST       closed in the base arm, refuses in the test arm.  A lever is
               supposed to be add-only; a LOST pair is a red flag and is
               reported first
    MOVED      closed in both, at a different width or over different layers
    SAME       identical verdict, identical width, identical layer sequence

`SAME` is counted and not listed: the count is the control, and an A/B whose
control collapses is an A/B that changed more than the one thing it named.

    python3 checks/pair_sweep_diff.py --base A.json [--base A2.json ...]
        --test B.json [--test B2.json ...] [--label NAME] [-o OUT]
"""
import argparse
import json
import sys
from pathlib import Path


def load(paths):
    """Flatten a shard set into {(net, a, b): verdict} plus the board sha the
    whole set agrees on.  Shards are how a sweep is parallelised, so a shard
    set is one arm and disagreement inside it is an error, not a diff."""
    out, shas, nets = {}, set(), []
    for p in paths:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        shas.add(d["board_sha256"])
        if not d.get("authoritative_unchanged", False):
            raise SystemExit("%s: board moved under the run" % p)
        for n in d["nets"]:
            nets.append(n["net"])
            for q in n["pairs"]:
                key = (n["net"], q["a"], q["b"])
                if key in out:
                    raise SystemExit("duplicate pair %s across shards" % (key,))
                out[key] = dict(
                    gap_mm=q["gap_mm"], closed_at=q.get("closed_at"),
                    reason=q.get("reason"),
                    layers=q.get("hop_layers"), vias=q.get("vias"),
                    width_licensed=q.get("licensed_unconditionally"),
                    far=n.get("far"), netclass=n.get("netclass"),
                    dru_floor=n.get("dru_floor"))
    if len(shas) != 1:
        raise SystemExit("shards disagree on board_sha256: %s" % sorted(shas))
    return out, shas.pop(), nets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", action="append", required=True)
    ap.add_argument("--test", action="append", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    base, bsha, bnets = load(a.base)
    test, tsha, tnets = load(a.test)
    if bsha != tsha:
        raise SystemExit("arms were run on DIFFERENT boards: %s vs %s"
                         % (bsha, tsha))

    rows, counts = [], {"GAINED": 0, "LOST": 0, "MOVED": 0, "SAME": 0,
                        "BASE_ONLY": 0, "TEST_ONLY": 0}
    for key in sorted(set(base) | set(test)):
        b, t = base.get(key), test.get(key)
        if b is None or t is None:
            k = "TEST_ONLY" if b is None else "BASE_ONLY"
        elif bool(b["closed_at"]) != bool(t["closed_at"]):
            k = "GAINED" if t["closed_at"] else "LOST"
        elif b["closed_at"] and (b["closed_at"] != t["closed_at"]
                                 or b["layers"] != t["layers"]):
            k = "MOVED"
        else:
            k = "SAME"
        counts[k] += 1
        if k != "SAME":
            rows.append(dict(net=key[0], a=key[1], b=key[2], klass=k,
                             gap_mm=(t or b)["gap_mm"],
                             base=b, test=t))

    order = {"LOST": 0, "GAINED": 1, "MOVED": 2, "BASE_ONLY": 3,
             "TEST_ONLY": 4}
    rows.sort(key=lambda r: (order[r["klass"]], r["net"], r["a"], r["b"]))
    for r in rows:
        t = r["test"] or {}
        print(" %-9s %-34s %-8s %-8s %7.3f mm  %s -> %s"
              % (r["klass"], r["net"], r["a"], r["b"], r["gap_mm"],
                 (r["base"] or {}).get("reason") or "CLOSED",
                 ("closed@%.3f mm %s" % (t["closed_at"] / 1e6,
                                         "->".join(t["layers"] or []))
                  if t.get("closed_at") else t.get("reason"))),
              file=sys.stderr, flush=True)
    print(" %s" % "  ".join("%s=%d" % (k, v) for k, v in sorted(counts.items())
                            if v), file=sys.stderr, flush=True)

    doc = dict(schema=1, label=a.label, board_sha256=bsha,
               base=[str(x) for x in a.base], test=[str(x) for x in a.test],
               base_nets=sorted(set(bnets)), test_nets=sorted(set(tnets)),
               question=("which island pairs changed verdict between two "
                         "pair sweeps run on the SAME board"),
               method=("both arms flattened to (net, land, land) -> verdict; "
                       "both must record authoritative_unchanged and the same "
                       "board sha256, which is refused rather than assumed.  "
                       "SAME is counted and not listed: it is the control"),
               counts=counts, changed=rows)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 1 if counts["LOST"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
