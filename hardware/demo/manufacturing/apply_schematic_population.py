#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- carry the SCHEMATIC's population onto the BOARD.

D-611 measured that the Demo board states no population at all: sixteen
references are DO NOT POPULATE in the schematic and not one carries the `dnp`
attribute on the board, so `kicad-cli pcb export pos --exclude-dnp` returns the
same 263 rows with the flag as without it and a factory places all sixteen.

WHY A TEXT EDIT AND NOT `pcbnew.SaveBoard`.  Saving through pcbnew rewrites the
whole file, and this board's authority is a SHA-256 that every gate compares.
A whole-file rewrite would bury a one-token change inside thousands of
incidental reformatting diffs and there would be no cheap way to prove that
nothing else moved.  This edits the `(attr ...)` token list of the named
footprints and NOTHING ELSE, and it prints every line it touched so the diff
can be read in full.

WHY NOT "UPDATE PCB FROM SCHEMATIC" EITHER.  That is the tool that SHOULD have
done this, and it may move footprints, rebuild nets and re-annotate.  On a
board whose copper is the accumulated output of six hundred gated decisions,
that is not a population fix; it is a new board.

The schematic is the authority and is read through
`routing_ledger.schematic_population()` -- the same reader the open-edge ledger
uses.  `checks/population_contract.py` proves the result, including POP4, which
runs the real `kicad-cli` and asks what a factory would be handed.

    python3 apply_schematic_population.py [--board B] [--apply] [-o OUT]

Without `--apply` it is a DRY RUN: it reports what it would change and writes
nothing.
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT / "hardware/beta-v2/checks")]

import routing_ledger as rl                                # noqa: E402

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

FOOTPRINT = re.compile(r'^\t\(footprint ')
END = re.compile(r'^\t\)\s*$')
REFERENCE = re.compile(r'^\t\t\(property "Reference" "([^"]+)"')
ATTR = re.compile(r'^(\t\t\(attr )([^)]*)(\)\s*)$')


def blocks(lines):
    """Yield (start, end, ref, attr_index, attr_tokens) per footprint block."""
    i, n = 0, len(lines)
    while i < n:
        if not FOOTPRINT.match(lines[i]):
            i += 1
            continue
        start, ref, attr_i, attr_tok = i, None, None, None
        j = i + 1
        while j < n and not END.match(lines[j]):
            m = REFERENCE.match(lines[j])
            if m and ref is None:
                ref = m.group(1)
            m = ATTR.match(lines[j])
            if m and attr_i is None:
                attr_i, attr_tok = j, m.group(2).split()
            j += 1
        yield start, j, ref, attr_i, attr_tok
        i = j + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    fitted, dnp = rl.schematic_population()
    text = a.board.read_text()
    lines = text.splitlines(keepends=True)

    added, removed, no_attr, seen = [], [], [], set()
    for start, end, ref, attr_i, attr_tok in blocks(lines):
        if ref is None:
            continue
        seen.add(ref)
        want = ref in dnp
        if attr_i is None:
            if want:
                no_attr.append(ref)
            continue
        has = "dnp" in attr_tok
        if want and not has:
            m = ATTR.match(lines[attr_i])
            lines[attr_i] = m.group(1) + " ".join(attr_tok + ["dnp"]) \
                + m.group(3)
            added.append(dict(ref=ref, line=attr_i + 1,
                              was="(attr %s)" % " ".join(attr_tok),
                              now=lines[attr_i].strip()))
        elif has and not want:
            m = ATTR.match(lines[attr_i])
            keep = [t for t in attr_tok if t != "dnp"]
            lines[attr_i] = m.group(1) + " ".join(keep) + m.group(3)
            removed.append(dict(ref=ref, line=attr_i + 1,
                                was="(attr %s)" % " ".join(attr_tok),
                                now=lines[attr_i].strip()))

    doc = dict(schema=1, board=str(a.board),
               board_sha256_before=rl.sha256(a.board),
               schematic_dnp=sorted(dnp),
               dnp_absent_from_board=sorted(dnp - seen),
               dnp_without_attr_line=sorted(no_attr),
               flags_added=added, flags_removed=removed,
               lines_changed=len(added) + len(removed),
               applied=bool(a.apply))

    if a.apply and (added or removed):
        if no_attr:
            raise SystemExit("refusing: %s carry no (attr ...) line; a token "
                             "cannot be appended to a list that is not there"
                             % no_attr)
        a.board.write_text("".join(lines))
        doc["board_sha256_after"] = rl.sha256(a.board)

    out = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        a.out.write_text(out)
    print(out)


if __name__ == "__main__":
    main()
