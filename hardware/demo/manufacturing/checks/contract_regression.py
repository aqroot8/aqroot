#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- re-run every STANDING CONTRACT and diff it, FIELD BY FIELD,
against the artifacts a named prior decision committed.

WHY THIS IS A TRACKED SCRIPT AND NOT A SHELL LOOP.  `maze3d.py` is read by
every promoting instrument on this board, so a change to it is a change to all
of them EVEN WHEN IT LAYS NO COPPER.  D-633 was the first iteration to owe that
debt and it paid it by hand -- ten contracts re-run and compared by eye, the
result hand-assembled into `evidence/d633-contract-regression.json`.  Every
future framework change owes the same debt, and a debt that is paid by hand is
paid differently every time.

WHAT IT PROVES.  On a board whose `sha256` has not moved, a framework change
that lays no copper must leave every contract's REPORT byte-identical, not
merely still-passing.  "Still PASS" is the weaker claim and it is the one that
hides a moved count: D-632's `leaf_land` would still have said PASS with a
different class census behind it.  So the comparison is the whole document,
normalised only where a field records the path as TYPED rather than a property
of the board:

  * `board`, `schematic`, `guard`, `pre_board` compare by BASENAME;
  * everything else compares exactly, and the first differing JSON pointer is
    reported so the failure names the field rather than the file.

A contract whose baseline artifact does not exist is reported `ran` with no
comparison rather than silently skipped -- an absent baseline is a fact about
the evidence tree, not a pass.

    python3 checks/contract_regression.py [--baseline d633] [--only NAME ...]
        [--evidence DIR] [-o OUT]
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MFG = HERE.parent
ROOT = HERE.parents[3]
EVIDENCE = MFG / "evidence"
BOND_GUARD = "evidence/d619-pour-bond-guard-bonded.json"

# name -> (script, extra argv, baseline evidence basename WITHOUT the decision
#          prefix, verdict field).  The verdict field is read only for the
#          human-readable line; the PROOF is the field-by-field diff.
CONTRACTS = (
    ("neck", "checks/neck_contract.py", (), "neck-contract", "all_pass"),
    ("placement", "checks/placement_contract.py", (), "placement-contract",
     "verdict"),
    ("population", "checks/population_contract.py", (), "population-contract",
     "verdict"),
    ("land_parity", "checks/land_parity_contract.py", (),
     "land_parity-contract", "verdict"),
    ("keepout_stackup", "checks/keepout_stackup_contract.py", (),
     "keepout_stackup-contract", "ok"),
    ("rf_symmetry", "checks/rf_symmetry_contract.py", (),
     "rf_symmetry-contract", "verdict"),
    ("pour_partition", "checks/pour_partition_contract.py", (),
     "pour_partition-contract", "ok"),
    ("pour_bond", "checks/pour_bond_contract.py", ("--guard", BOND_GUARD),
     "pour_bond-contract", "all_pass"),
    # THE NET ORDER IS PART OF THE INVOCATION.  `leaf_land_contract` reports
    # its islands in the order the nets were named, so asking the same three
    # nets in a different order produces a document that differs field by
    # field while every verdict, count and class census is identical.  This is
    # the order D-632's committed artifact was produced with, and changing it
    # is changing the question.
    ("leaf_land", "checks/leaf_land_contract.py",
     ("--net", "+3V3", "--net", "/01_POWER_TREE/BQ25185_SYS",
      "--net", "GND"), "leaf-land-contract", "ok"),
    ("protected_copper", "protected_copper.py", (), "protected-copper",
     "identical"),
)
BY_BASENAME = ("board", "schematic", "guard", "pre_board")


def norm(doc, path=()):
    """The document with path-typed fields reduced to their basenames."""
    if isinstance(doc, dict):
        return {k: (Path(str(v)).name if k in BY_BASENAME and
                    isinstance(v, str) else norm(v, path + (k,)))
                for k, v in doc.items()}
    if isinstance(doc, list):
        return [norm(v, path + (i,)) for i, v in enumerate(doc)]
    return doc


def first_diff(a, b, path="$"):
    """The first differing JSON pointer, or None."""
    if type(a) is not type(b) and not (isinstance(a, (int, float))
                                       and isinstance(b, (int, float))):
        return "%s: %s vs %s" % (path, type(a).__name__, type(b).__name__)
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                return "%s.%s: missing in current" % (path, k)
            if k not in b:
                return "%s.%s: missing in baseline" % (path, k)
            d = first_diff(a[k], b[k], "%s.%s" % (path, k))
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return "%s: %d vs %d entries" % (path, len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, "%s[%d]" % (path, i))
            if d:
                return d
        return None
    if a != b:
        return "%s: %r vs %r" % (path, a, b)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default="d633",
                    help="decision prefix of the evidence to diff against")
    ap.add_argument("--only", action="append", default=[],
                    help="run only these contracts (repeatable)")
    ap.add_argument("--evidence", type=Path, default=EVIDENCE)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    rows, tmp = [], Path(tempfile.mkdtemp(prefix="aqroot-contract-reg-"))
    for name, script, extra, base, field in CONTRACTS:
        if a.only and name not in a.only:
            continue
        out = tmp / ("%s.json" % name)
        cmd = [sys.executable, str(MFG / script), "-o", str(out)] + list(extra)
        p = subprocess.run(cmd, cwd=str(MFG), capture_output=True, text=True)
        row = dict(contract=name, ran=out.exists(), returncode=p.returncode)
        if not out.exists():
            row["error"] = (p.stderr or p.stdout or "")[-400:]
            rows.append(row)
            print(" %-17s DID NOT RUN (rc=%d)" % (name, p.returncode),
                  file=sys.stderr, flush=True)
            continue
        cur = json.loads(out.read_text())
        row["verdict"] = cur.get(field)
        row["board_sha256"] = cur.get("board_sha256")
        ref = a.evidence / ("%s-%s.json" % (a.baseline, base))
        if not ref.exists():
            row["baseline"] = None
            row["identical"] = None
            rows.append(row)
            print(" %-17s %-6s  NO BASELINE %s"
                  % (name, str(row["verdict"]), ref.name),
                  file=sys.stderr, flush=True)
            continue
        old = json.loads(ref.read_text())
        d = first_diff(norm(cur), norm(old))
        row.update(baseline=ref.name, identical=(d is None), difference=d,
                   baseline_verdict=old.get(field))
        rows.append(row)
        print(" %-17s %-6s  %s" % (name, str(row["verdict"]),
                                   "IDENTICAL to %s" % a.baseline if d is None
                                   else "DIFFERS: %s" % d[:110]),
              file=sys.stderr, flush=True)

    doc = dict(schema=1, baseline=a.baseline, contracts_run=len(rows),
               question=("does this framework change move ANY standing "
                         "contract, on a board whose sha256 did not change"),
               method=("each contract re-run now and compared FIELD BY FIELD "
                       "with the artifact the baseline decision committed; "
                       "path-typed fields (board, schematic, guard, "
                       "pre_board) compare by basename because they record "
                       "the path as typed"),
               all_ran=all(r["ran"] for r in rows),
               all_identical=all(r.get("identical") is True for r in rows),
               contracts=rows)
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print("\n contracts %d   all_ran %s   all_identical %s"
          % (len(rows), doc["all_ran"], doc["all_identical"]),
          file=sys.stderr)
    return 0 if (doc["all_ran"] and doc["all_identical"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
