#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the LAND CHAIN contract (LAND1-LAND7).

A land pattern is right when two links both hold:

    board footprint  ==  library master  ==  manufacturer / IPC drawing

Neither link was measured before D-616.  The second was written down in
`assembly/FOOTPRINT_VERIFICATION_LEDGER.md` and never connected to the board.
The first is KiCad's own `lib_footprint_mismatch`, and on this machine it had
NEVER RUN: the stock footprint libraries are installed but no global
`fp-lib-table` was ever written, so every non-project footprint reported
`lib_footprint_issues` -- *"the current configuration does not include the
footprint library 'Resistor_SMD'"* -- 199 of them, which is exactly the count
this repository has carried as an INHERITED DRC class since before the maze
router existed.  A land that KiCad could not open the master for is a land
nothing has ever compared.

    LAND1  every board footprint names a library that RESOLVES, and that
           library holds a footprint of that name
    LAND2  every board footprint is pad-identical to its master -- position,
           size, shape and corner ratios, drill, pad type, layer set, rotation,
           offset, die length and every local mask/paste override, to the nm
    LAND3  the comparison is NOT VACUOUS: a one-micron perturbation of a named
           reference is detected
    LAND4  KiCad's OWN check agrees, run with the libraries resolved: zero
           `lib_footprint_issues`, and every `lib_footprint_mismatch` it does
           report is DECLARED in the index by reference, with what differs and
           why -- KiCad's comparison is wider than the land, so the gate names
           the difference rather than suppressing the class
    LAND5  the citation index covers EXACTLY the board's distinct footprint
           identities -- none missing, no dead rows -- and every tier it uses
           is one the index defines
    LAND6  every identity is written into the normative ledger, and every
           `2_OPEN` identity is marked OPEN there rather than quietly passing
    LAND7  NO identity is `2_OPEN` at all, and the rows that say a drawing was
           read can prove it: every tier-1 and tier-2A row cites a `drawing`;
           every tier-1 row records its `confirmed` figures here UNLESS it is
           named in `confirmed_in_this_index_pending`, whose figures are in the
           ledger's own prose -- and that list is an EQUALITY, so it may shrink
           and a new row may not join it; and every `drawing_file` a row names
           is present in the repository and hashes to its recorded sha256

LAND6 is why the index cannot be a rubber stamp: deleting a ledger row breaks
the gate, and an identity whose drawing was not read has to say so in the file
a reviewer reads.

LAND7 is why closing the last open one is not a promise.  Until D-762 the
gate COUNTED open items and passed anyway -- `open_items` was a field in the
report, not a clause -- so `Connector_JST:JST_SH_SM04B-SRSS-TB` (`J8`, the
Qwiic / STEMMA QT port) stood OPEN for 146 decisions while every run printed
PASS.  And the tier string alone was the whole claim: flipping `2_OPEN` to
`1` without opening a PDF would have satisfied every clause LAND1-LAND6.  So a
tier-1 row now has to carry the document AND the figures, and a tier-2A row at
least the document.  D-762 read JST's own `eSH.pdf`, confirmed all eight
figures of the side-entry land, and the tier is `1` because the drawing is in
the repository under `vendor/JST/` with its sha256 in the index -- not because
a string was edited.

The same pass found the WEAKEST citation on the board and it was not the open
one.  `AQROOT_Beta:Ebyte_E22-900M22S` -- the 915 MHz LoRa module -- had stood
at tier 1 since B-03 on the strength of the words *"Ebyte manufacturer drawing,
archived"*: no document, no revision, no figure.  `AQROOT_Beta:Ebyte_E07-400M10S`
said *"user manual ch. 3"*, and the file actually archived beside it is a
TEST-BOARD SCHEMATIC, not a mechanical drawing.  And the two modules SHARE one
land geometry, so a single wrong figure would have taken out both radios.  Both
vendor manuals are now read, archived and hash-pinned, and they agree figure
for figure.

    python3 hardware/demo/manufacturing/checks/land_parity_contract.py \
        [-o REPORT.json] [--skip-drc]
"""

import argparse
import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MANUF = ROOT / "hardware/demo/manufacturing"
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
INDEX = MANUF / "land_citations.json"
LEDGER = ROOT / "docs/full-beta-v2/assembly/FOOTPRINT_VERIFICATION_LEDGER.md"

# The reference LAND3 perturbs.  R75 is the 2512 battery current-sense resistor:
# a two-pad land whose master is a stock IPC part, so the control is as simple
# as the check can be made and still exercise the whole path.
CONTROL_REF = "R75"

sys.path.insert(0, str(MANUF))


def screen(perturb=None):
    """The one comparison, imported -- not a second copy of it."""
    import screen_land_parity as S
    rows, _libs, project_nicknames, share, _n = S.survey(perturb)
    return rows, project_nicknames, share


def kicad_drc():
    """Real KiCad DRC with the stock libraries registered, as a normal
    installation would have them."""
    tmp = Path(tempfile.mkdtemp(prefix="aqroot-land-"))
    try:
        for src in list(PROJECT.glob("*.kicad_sch")) + [
                BOARD, BOARD.with_suffix(".kicad_dru"),
                BOARD.with_suffix(".kicad_pro")]:
            shutil.copyfile(src, tmp / src.name)
        shutil.copytree(PROJECT / "libraries", tmp / "libraries")
        shutil.copyfile(PROJECT / "sym-lib-table", tmp / "sym-lib-table")
        (tmp / "fp-lib-table").write_text(resolved_fp_lib_table(),
                                          encoding="utf-8")
        out = tmp / "drc.json"
        subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones",
                        "--format", "json", "--units", "mm", "--severity-all",
                        "--schematic-parity", "-o", str(out),
                        str(tmp / BOARD.name)], capture_output=True, text=True)
        report = json.loads(out.read_text())
        counts = {}
        for v in report.get("violations", []):
            counts[v["type"]] = counts.get(v["type"], 0) + 1
        detail = [v for v in report.get("violations", [])
                  if v["type"] in ("lib_footprint_issues",
                                   "lib_footprint_mismatch")]
        return counts, detail
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def resolved_fp_lib_table():
    """The project's table PLUS the stock table KiCad itself ships."""
    import screen_land_parity as S
    libs, _proj, share = S.resolve_libraries()
    rows = "\n".join(
        '  (lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))'
        % (nick, path) for nick, path in sorted(libs.items()))
    return "(fp_lib_table\n  (version 7)\n%s\n)\n" % rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--skip-drc", action="store_true")
    a = ap.parse_args()

    rows, project_nicknames, share = screen()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    ledger = LEDGER.read_text(encoding="utf-8")

    no_master = sorted(r["ref"] for r in rows if r["verdict"] == "NO_MASTER")
    mismatch = [r for r in rows if r["verdict"] == "MISMATCH"]

    control, _, _ = screen(CONTROL_REF)
    control_row = next(r for r in control if r["ref"] == CONTROL_REF)

    board_ids = sorted({r["identity"] for r in rows})
    cited = index["identities"]
    missing = [i for i in board_ids if i not in cited]
    dead = [i for i in sorted(cited) if i not in board_ids]
    bad_tier = [i for i, e in sorted(cited.items())
                if e.get("tier") not in index["tiers"]]

    unwritten = [i for i in sorted(cited) if i not in ledger]
    open_ids = sorted(i for i, e in cited.items() if e["tier"] == "2_OPEN")
    not_marked_open = [
        i for i in open_ids
        if not any(i in line and "OPEN" in line for line in ledger.splitlines())]

    # LAND7.  A tier is a CLAIM about a document.  Make the claim carry the
    # document: a read drawing has a citation, and a tier-1 row -- the tier
    # that says "dimensions recorded" -- has the dimensions.
    uncited = sorted(i for i, e in cited.items()
                     if e["tier"] in ("1", "2A")
                     and not str(e.get("drawing", "")).strip())
    # ...and a tier-1 row records its FIGURES, either here or -- for the rows
    # that predate this index's `confirmed` block -- in the ledger prose the
    # `confirmed_in_this_index_pending` list names.  That list is an EQUALITY,
    # so it may shrink and nothing new may join it.
    pending = index.get("confirmed_in_this_index_pending", {})
    pending_ids = sorted(pending.get("identities", []))
    unconfirmed = sorted(i for i, e in cited.items()
                         if e["tier"] == "1" and not e.get("confirmed")
                         and i not in set(pending_ids))
    pending_drifted = (
        pending_ids != sorted(i for i, e in cited.items()
                              if e["tier"] == "1" and not e.get("confirmed")))
    # ...and where a tier-1 row names a file in the repository, that file must
    # BE there and hash to what the row says.  A citation to a document that
    # has been moved, replaced or rewritten is the stale-source defect class.
    filed_bad = []
    for i, e in sorted(cited.items()):
        rel = e.get("drawing_file")
        if not rel:
            continue
        f = ROOT / rel
        if not f.is_file():
            filed_bad.append([i, "MISSING", rel])
            continue
        want = e.get("drawing_sha256")
        got = __import__("hashlib").sha256(f.read_bytes()).hexdigest()
        if want and want != got:
            filed_bad.append([i, "SHA256", rel, want, got])

    drc_counts, drc_detail = ({}, []) if a.skip_drc else kicad_drc()
    declared = index.get("declared_master_divergences", {})
    mismatch_refs = sorted({
        i["description"].split()[-1]
        for v in drc_detail if v["type"] == "lib_footprint_mismatch"
        for i in v["items"]})

    checks = {
        "LAND1_every_footprint_resolves_a_master": not no_master,
        "LAND2_board_land_equals_master": not mismatch,
        "LAND3_comparison_not_vacuous":
            control_row["verdict"] == "MISMATCH",
        "LAND4_kicad_agrees": (
            a.skip_drc
            or (drc_counts.get("lib_footprint_issues", 0) == 0
                and mismatch_refs == sorted(declared))),
        "LAND5_index_covers_the_board": not missing and not dead and not bad_tier,
        "LAND6_every_identity_is_in_the_ledger":
            not unwritten and not not_marked_open,
        "LAND7_no_open_identity_and_every_read_drawing_is_cited": (
            not open_ids and not uncited and not unconfirmed
            and not pending_drifted and not filed_bad),
    }

    report = {
        "schema": 1,
        "board_sha256": __import__("hashlib").sha256(
            BOARD.read_bytes()).hexdigest(),
        "kicad_share": share,
        "footprints": len(rows),
        "distinct_identities": len(board_ids),
        "verdicts": {v: sum(1 for r in rows if r["verdict"] == v)
                     for v in sorted({r["verdict"] for r in rows})},
        "no_master": no_master,
        "mismatches": [{"ref": r["ref"], "identity": r["identity"],
                        "diffs": r["diffs"]} for r in mismatch],
        "control": {"ref": CONTROL_REF, "verdict": control_row["verdict"],
                    "diffs": control_row.get("diffs")},
        "drc_counts": drc_counts,
        "drc_land_violations": drc_detail,
        "index_missing": missing, "index_dead_rows": dead,
        "index_bad_tier": bad_tier,
        "ledger_unwritten": unwritten,
        "open_items": open_ids,
        "tier_rows_without_a_drawing": uncited,
        "tier1_rows_without_confirmed_dimensions": unconfirmed,
        "tier1_figures_in_the_ledger_not_this_index": pending_ids,
        "tier1_pending_list_drifted": pending_drifted,
        "cited_files_missing_or_changed": filed_bad,
        "declared_master_divergences": sorted(declared),
        "kicad_mismatch_refs": mismatch_refs if not a.skip_drc else None,
        "open_not_marked": not_marked_open,
        "tier_census": {t: sum(1 for r in rows
                               if cited.get(r["identity"], {}).get("tier") == t)
                        for t in index["tiers"]},
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
