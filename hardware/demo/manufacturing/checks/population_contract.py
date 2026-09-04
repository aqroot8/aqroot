#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the BOARD must carry the SCHEMATIC's population, and nothing
else may.

D-611 measured that it does not.  Sixteen references are marked DO NOT POPULATE
in the Demo schematic and **not one** of them carries the `dnp` attribute on
the board; every footprint says `(attr smd)` or `(attr through_hole)`.  A CPL
or assembly position file generated from that board places all sixteen, because
`kicad-cli pcb export pos --exclude-dnp` reads the FOOTPRINT attribute and
there is nothing there to read.

**NOTHING THIS REPOSITORY OWNED COULD SEE IT.**  KiCad's own
`--schematic-parity` reports CLEAN on the affected board -- parity compares
nets and footprint identity, not population -- so `verify_promotion.py`'s
`schematic_parity_clean` passed on every promotion ever gated.  The router
never looks: `maze3d.net_islands` has no population model, which is why the
proposer sees PHANTOM orphan islands the gate's own ledger does not count.

Four claims, each measured against the schematic rather than asserted:

  POP1  every reference the schematic marks DNP exists on the board AND
        carries the board's `dnp` attribute;
  POP2  no reference the schematic marks FITTED carries it -- the flag must
        not have been sprayed;
  POP3  the two sets are EQUAL, so the board states the schematic's population
        exactly, neither more nor less;
  POP4  the FABRICATION consequence, measured end to end with the real tool:
        `kicad-cli pcb export pos --exclude-dnp` omits exactly the DNP
        references and retains every fitted one that has a position at all.
        This is the claim that matters -- POP1-POP3 are about a flag, POP4 is
        about what a factory would build.

The schematic is the population authority and is read through
`routing_ledger.schematic_population()`, which is the same reader the
open-edge ledger uses; this file does not invent a second one.

    python3 hardware/demo/manufacturing/checks/population_contract.py [-o OUT]
"""

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE.parent), str(ROOT / "hardware/beta-v2/checks")]

import routing_ledger as rl                                # noqa: E402
import pcbnew                                              # noqa: E402

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def board_population(path):
    b = pcbnew.LoadBoard(str(path))
    dnp, refs = set(), set()
    for fp in b.GetFootprints():
        r = fp.GetReference()
        refs.add(r)
        if fp.IsDNP():
            dnp.add(r)
    return refs, dnp


def pos_references(path, exclude_dnp):
    """References `kicad-cli` would hand a factory, as a set."""
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-pos-") as tmp:
        out = Path(tmp) / "pos.csv"
        cmd = ["kicad-cli", "pcb", "export", "pos", "--format", "csv",
               "--units", "mm", "--side", "both", "-o", str(out), str(path)]
        if exclude_dnp:
            cmd.append("--exclude-dnp")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        rows = list(csv.DictReader(out.open(newline="", encoding="utf-8-sig")))
    key = "Ref" if rows and "Ref" in rows[0] else (
        "Reference" if rows and "Reference" in rows[0] else None)
    if key is None:
        raise SystemExit("position file has no reference column: %s"
                         % (list(rows[0]) if rows else "empty"))
    return {r[key] for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    fitted, dnp = rl.schematic_population()
    refs, board_dnp = board_population(a.board)

    pop1_missing = sorted((dnp & refs) - board_dnp)
    pop1_absent = sorted(dnp - refs)
    pop2_sprayed = sorted(board_dnp & fitted)
    pop3_equal = board_dnp == (dnp & refs)

    kept = pos_references(a.board, exclude_dnp=True)
    all_pos = pos_references(a.board, exclude_dnp=False)
    pop4_placed_dnp = sorted(kept & dnp)
    pop4_dropped_fitted = sorted((all_pos & fitted) - kept)

    checks = {
        "POP1": dict(ok=not pop1_missing and not pop1_absent,
                     schematic_dnp=len(dnp),
                     board_dnp_attribute=len(board_dnp),
                     missing_flag=pop1_missing,
                     absent_from_board=pop1_absent),
        "POP2": dict(ok=not pop2_sprayed, sprayed_onto_fitted=pop2_sprayed),
        "POP3": dict(ok=pop3_equal,
                     board_only=sorted(board_dnp - dnp),
                     schematic_only=sorted((dnp & refs) - board_dnp)),
        "POP4": dict(ok=not pop4_placed_dnp and not pop4_dropped_fitted,
                     pos_rows_all=len(all_pos), pos_rows_excluding_dnp=len(kept),
                     dnp_still_placed=pop4_placed_dnp,
                     fitted_dropped=pop4_dropped_fitted),
    }
    doc = dict(schema=1, board=str(a.board),
               board_sha256=rl.sha256(a.board),
               schematic_fitted=len(fitted), schematic_dnp=sorted(dnp),
               board_dnp_attribute=sorted(board_dnp),
               checks=checks,
               verdict="PASS" if all(c["ok"] for c in checks.values())
                       else "FAIL")
    text = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        a.out.write_text(text)
    print(text)
    return 0 if doc["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
