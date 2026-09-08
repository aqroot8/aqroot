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
# THE BOND GUARD IS A PROPERTY OF THE BOARD AND MOVES WITH IT -- D-645.
# `pour_bond_contract` `P2` compares the tubes a guard NAMES against the
# islands the board CARRIES, so a guard emitted on an older authority
# describes a topology that no longer exists.  This constant sat at
# D-619 through five promotions and was still passing by luck; D-644
# dropped the `C4.2 <-> U3.12` tube and renumbered nine `+3V3` and
# seven `GND` islands, and `P2` went `FAIL islands_renumbered` on a
# board whose own guard reads `P1-P4 PASS`.  The stale question is the
# defect, not the board.  EVERY promotion that re-emits the guard must
# move this line to the guard IT emitted.
#
# D-656 FOUND THE SECOND STALENESS MODE, AND IT IS NOT RENUMBERING.  The
# `d646` guard survived D-651 through D-655 and went `FAIL` on D-656's
# board with `off_copper: 1` -- ten of the 147 sampled points of the
# `/01_POWER_TREE/BQ25185_SYS` `U12.1 <-> via` tube fall outside island 3,
# because `/I2C_SDA_INT`'s copper took 9.76 mm2 out of that pour and KiCad
# re-poured a different SHAPE.  A tube is a POLYLINE frozen at emission;
# the conductor is not.  That it is the QUESTION and not the board was
# measured three ways and recorded in D-656 section 5: every pairwise
# bottleneck inside island 3 is IDENTICAL before and after to 0.1 um
# (0.1969 / 0.2203 / 0.1969 mm), KiCad's own connectivity reports the same
# nine `BQ25185_SYS` clusters at every `min_thickness` rung either side of
# the promotion, `misplaced_ends` is EMPTY, and `PP1-PP4` and
# `verify_promotion.py`'s `pour_partition_intact` both PASS.  The guard
# re-emitted on the promoted board reads `P1-P4 PASS`, 49 tubes, ZERO
# renumbered, ZERO off copper.  The STALE guard still FAILS on that same
# board, which is this bump's own non-vacuity control.
#
# D-669 BUMPS IT AGAIN, FOR THE THIRD TIME AND THE SAME REASON, ON THE SAME
# TUBE D-619 NAMED.  `/SPI_B_SCK`'s closure re-poured the `B.Cu` `GND` plane
# around `U9`, and the D-656 spec's `GND` `U9.6 -> via` centreline -- the one
# whose 224 sampled points D-619 already watched a 0.300 mm `Y1` shift trim
# five of -- now has 7 of 226 points inside the new track's antipad.  THE BOND
# DID NOT MOVE and it was measured before the pin was touched
# (`evidence/d669-u9-6-bond-unmoved.json`): `U9.6` sits in ONE `B.Cu` `GND`
# island either side of the promotion, 2555.8463 -> 2553.5346 mm2 (-0.09 %),
# and the island's INDEX moved 18 -> 21 only because three new outlines appear
# earlier in the enumeration -- the `U7`/`U8` split `PP2` ADMITTED and priced.
# Board-wide `B.Cu` `GND` 6141.8929 -> 6110.4221 mm2.  `PP1-PP4` PASS,
# `verify_promotion.py`'s `pour_partition_intact` PASSES, `misplaced_ends` is
# EMPTY, and the guard re-emitted on the promoted board reads `P1-P4 PASS`,
# 52 tubes (three of them new, over the admitted split), ZERO off copper.  The
# STALE d656 guard still FAILS on that board, which is this bump's own
# non-vacuity control.
BOND_GUARD = "evidence/d669-pour-bond-guard-next.json"

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
    # D-645.  THE ELEVENTH, AND THE FIRST THAT IS ABOUT THE INSTRUMENT RATHER
    # THAN THE BOARD.  Every contract above asks whether the COPPER is sound;
    # this one asks whether the model the proposer routes against IS the
    # board's copper.  It belongs in this suite for the same reason the others
    # do -- `maze3d.ensure_board_vias` is read by every promoting instrument,
    # so a change to it is a change to all of them -- and it reports its own
    # `scan_gate_on`, so the suite records WHICH of the model's two states the
    # run was made in rather than leaving it to be inferred.
    ("obstacle_model", "checks/obstacle_model_contract.py", (),
     "obstacle_model-contract", "verdict"),
    # D-662.  THE TWELFTH, AND THE SECOND ABOUT THE INSTRUMENT.  `--trunk-floor`
    # lets a net route at the width `.kicad_dru` publishes as its class MINIMUM
    # instead of the netclass `opt`, so it can lay copper on every priced rail
    # on this board.  It belongs here for the reason `neck_contract` does: the
    # claim that matters is not "the lever works" but "with the lever OFF
    # `net_contract` returns what it returned before it existed", and that
    # claim has to be re-proved on every future framework change, not once.
    ("trunk_floor", "checks/trunk_floor_contract.py", (),
     "trunk_floor-contract", "all_pass"),
    # D-664.  THE THIRTEENTH, AND THE THIRD ABOUT THE INSTRUMENT.  `--tap` is
    # the first primitive on this board that leaves a BRANCH on an ALREADY
    # ACCEPTED conductor, and the ledger cannot tell a T-junction from a
    # pad-to-pad run.  It belongs here for the reason `trunk_floor` does: the
    # claim that matters is not "the lever works" but "the screen that PROVES a
    # tap and the writer that LAYS one name one list and one geometry", and
    # that claim has to be re-proved on every future framework change.
    ("tap", "checks/tap_contract.py", (), "tap-contract", "all_pass"),
    # D-666.  THE FOURTEENTH, AND THE FIRST ABOUT THE SHIPPABLE.  Every
    # contract above asks about the BOARD or about the INSTRUMENT that routes
    # against it.  None of them looks at `hardware/demo/fab` -- the Gerbers,
    # the drills, the CPL and the BOM a factory would actually receive -- and
    # so nobody noticed that it had named board `5715bf5c` since D-644 while
    # the authority moved twenty decisions to `7b2ca325`.  Measured rather than
    # asserted: `fab_package_contract.py` run against the SHIPPED package reads
    # `FAB1_provenance FAIL` and `FAB4_drill FAIL`, and FAB4 says how much --
    # the board carries 886 holes and the shipped Excellon 846, short 35
    # 0.300 mm via drills, 3 at 0.200 and 3 at 0.400.  Sending it would have
    # built a board with forty plated holes missing.
    #
    # It is the FULL review that proves that, and the full review costs minutes
    # -- a `kicad-cli` refill plus a hole-by-hole bijection -- which is why it
    # is a release activity and not a per-promotion one.  What belongs HERE is
    # the part that rots: `--provenance-only` is FAB1 alone, 0.3 s, no board
    # load, and it is the SAME `fab1()` the release review runs.  From D-666 on,
    # a promotion that moves the copper and leaves the package behind shows up
    # in this suite the same iteration, as `$.checks.FAB1_provenance.ok:
    # False vs True` -- and the fix is `export_fab_package.py`, not a comment.
    ("fab_provenance", "checks/fab_package_contract.py",
     ("--provenance-only",), "fab_provenance-contract", "verdict"),
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
    # D-664 -- THE COMPARISON HAD NOTHING TO COMPARE AGAINST, AND IT SAID SO
    # QUIETLY.  This harness diffs each contract's report against
    # `evidence/<baseline>-<name>.json`, and that file has NEVER EXISTED for any
    # prefix: every contract runs into a temporary directory that is discarded
    # when the process ends, and the only artifact this file ever wrote is its
    # OWN summary.  So the row printed `NO BASELINE`, `identical` was recorded
    # as `null`, and `all_identical` came back False -- for D-633 through D-663
    # alike.  Read as "12/12 RAN, 12/12 PASS" that is true; read as the claim
    # this file states at the top -- "a framework change that lays no copper
    # must leave every contract's REPORT byte-identical, not merely
    # still-passing" -- it was never asked once.  A passing check that never
    # posed its question is the failure mode D-654's `--ban` exists for in
    # another instrument, and it is this one's too.
    #
    # `--emit-baseline PREFIX` is the missing half: it KEEPS each contract's
    # report as `evidence/<PREFIX>-<name>.json`, which is the file the NEXT
    # decision's `--baseline PREFIX` reads.  It refuses to emit under the same
    # prefix it is diffing against, because a run that wrote its own baseline
    # and then compared with it would prove only that a file equals itself.
    ap.add_argument("--emit-baseline", default=None, metavar="PREFIX",
                    help="D-664: keep each contract's report as "
                         "evidence/PREFIX-<name>.json so the NEXT decision's "
                         "--baseline PREFIX has something real to diff; "
                         "refused when PREFIX is the baseline being compared "
                         "against")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    if a.emit_baseline and a.emit_baseline == a.baseline:
        ap.error("--emit-baseline %s is also --baseline %s: a run that wrote "
                 "its own baseline and then diffed against it would prove "
                 "only that a file equals itself" % (a.emit_baseline,
                                                     a.baseline))

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
        if a.emit_baseline:
            kept = a.evidence / ("%s-%s.json" % (a.emit_baseline, base))
            kept.write_text(out.read_text())
            row["emitted_baseline"] = kept.name
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

    doc = dict(schema=1, baseline=a.baseline,
               emitted_baseline=a.emit_baseline,
               # D-664.  A SUMMARY THAT SAYS `all_identical` WITHOUT SAYING
               # WHETHER ANYTHING WAS COMPARED IS THE DEFECT ITSELF.  These two
               # counts separate "every contract matched its baseline" from
               # "no contract had one", which the old document could not.
               contracts_compared=sum(1 for r in rows
                                      if r.get("identical") is not None),
               contracts_without_baseline=sum(1 for r in rows if r["ran"]
                                              and r.get("identical") is None),
               contracts_run=len(rows),
               question=("does this framework change move ANY standing "
                         "contract, on a board whose sha256 did not change"),
               method=("each contract re-run now and compared FIELD BY FIELD "
                       "with the artifact the baseline decision committed; "
                       "path-typed fields (board, schematic, guard, "
                       "pre_board) compare by basename because they record "
                       "the path as typed"),
               all_ran=all(r["ran"] for r in rows),
               all_identical=all(r.get("identical") is True for r in rows),
               # VACUOUS means: every contract ran and passed and NOT ONE was
               # diffed, which is what this harness reported for D-633 through
               # D-663 without ever saying so in one word.
               vacuous=bool(rows and not any(r.get("identical") is not None
                                             for r in rows)),
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
