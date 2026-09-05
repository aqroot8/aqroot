# AQROOT Demo — Fabrication Package

Status: **GENERATED AND REVIEWED — NOT RELEASABLE.**
One contract claim fails, and it is the BOM sourcing claim (FAB7).

The package lives in `hardware/demo/fab/`.  It is not hand-assembled: it is
produced in one command by `hardware/demo/manufacturing/export_fab_package.py`
and reviewed by `hardware/demo/manufacturing/checks/fab_package_contract.py`.
Do not edit an artifact in place — regenerate.

    python3 hardware/demo/manufacturing/export_fab_package.py
    python3 hardware/demo/manufacturing/checks/fab_package_contract.py

## Authority

    board      hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb
    sha256     c8e421aa50144fe396aedb5e226aaabeb815bd69ffaf6e04f549ded43831d103
    generator  kicad-cli 10.0.5
    release    MANIFEST.json carries the board, rule, project and schematic
               sha256, and a sha256 for every artifact

**The package is reproducible.**  KiCad stamps a creation date into Gerber and
Excellon headers, so the raw sha256 of those files changes on every run; the
manifest therefore also carries a NORMALISED sha256 with the generator's date
and version lines removed, and that one is stable run to run.  Twenty-four of
the twenty-eight artifacts are deterministic in this sense.  The four that are
not are PDFs (two assembly drawings, two drill maps), which embed a creation
date inside the document, and they are recorded as `deterministic: false`
rather than quietly excluded.

## What is in it

    gerbers/*.gbr          F.Cu In1.Cu In2.Cu In3.Cu In4.Cu B.Cu
                           F.Paste B.Paste F.Silkscreen B.Silkscreen
                           F.Mask B.Mask Edge.Cuts
    gerbers/*-job.gbrjob   KiCad's own job file, listing the same thirteen
    gerbers/*-PTH.drl      plated holes, Excellon, metric, ABSOLUTE origin
    gerbers/*-NPTH.drl     unplated holes, separate file
    gerbers/*-drl_map.pdf  drill maps
    gerbers/drill-report.txt
    aqroot-Demo-pos-all.csv      263 placements, DNP included
    aqroot-Demo-pos-fitted.csv   247 placements, --exclude-dnp
    aqroot-Demo-BOM-full.csv     every symbol, grouped, DNP column carried
    aqroot-Demo-BOM-assembly.csv 122 lines / 247 refs — the quote
    aqroot-Demo-DO-NOT-POPULATE.csv  16 refs
    aqroot-Demo-NON-PURCHASED.csv    46 refs — test points
    aqroot-Demo-OFF-BOARD.csv         1 ref — LS1, the speaker
    aqroot-Demo-assembly-top/bottom.pdf   F.Fab / B.Fab, DNP crossed out
    MANIFEST.json

The four BOM views **partition** the schematic's 310 symbols exactly once each.
That partition is the fix for a defect this package's first review found: taken
straight from `kicad-cli sch export bom`, the Demo BOM asked a supplier to
quote forty-six test points.  A `TestPoint` is a pad and a `MountingBoss` is a
hole; the board already carries KiCad's "exclude from BOM" attribute on all
forty-eight, and the exporter uses the board as the authority.  The contract
re-derives the same partition and refuses any divergence the board does not
explain.

## Board

    outline        72.000 x 148.000 mm, rectangular
    copper layers  6 — F, In1, In2, In3, In4, B
    finish         ENIG
    copper weight  outer 35 um, inner 15.2 um
    dielectrics    prepreg 7628 / FR4 core, epsilon_r 4.4
    thickness      ~1.574 mm as stacked
    vias           tented front and back

## Drill census — measured against the board, hole for hole

The contract's FAB4 claim is not that a drill file exists.  It reads both
Excellon files, converts to board coordinates, and matches the hole multiset
against `pcbnew`'s own vias and pad drills to the micron, which is the
resolution the Excellon file is written at.  **802 holes on the board, 802 in
the files, zero displaced.**

    plated           795     unplated         7
    tools             14     slots            4
    P 0.200            47    P 0.600x1.400    2    N 0.650    2
    P 0.250            11    P 0.600x1.700    2    N 0.900    2
    P 0.300           566    P 0.750          4    N 1.050    1
    P 0.400           134    P 0.900          2    N 2.200    2
                            P 1.020          24
                            P 1.100           3

**Two notes for the fabricator, neither of them a defect this repository can
close on its own.**

1. **Minimum drill is 0.200 mm.**  Forty-seven plated holes are at it: 35 are
   the D-257 fine barrels the `.kicad_dru` licenses, and 12 are the
   via-in-pad thermal array inside the ESP32-S3-WROOM-1 module's ground pad,
   which comes from the KiCad library footprint.  Those twelve sit under paste;
   if the assembler wants them plugged or tented rather than open, that is a
   process choice to state on the order, not a board change.
2. **`pad_to_mask_clearance` is 0 and footprint mask bridges are disallowed**,
   and the board carries one inherited `solder_mask_bridge` DRC report.  That
   report predates the maze router and is inside the inherited baseline.

## Review — `checks/fab_package_contract.py`

    FAB1  PROVENANCE  PASS   manifest names the authoritative sha256; all 28
                             artifacts hash as recorded; nothing unmanifested
    FAB2  FILL        PASS   the committed board is BYTE-IDENTICAL after
                             --refill-zones --save-board, so the copper these
                             Gerbers plot is the copper the gate ran DRC on
    FAB3  LAYERS      PASS   six copper Gerbers in stackup order, gbrjob
                             agrees, no shipped layer file empty
    FAB4  DRILL       PASS   802 = 802, zero displaced
    FAB5  CPL         PASS   247 fitted rows = the fitted placeable set; every
                             row's X/Y/side matches pcbnew; no DNP survives
    FAB6  BOM         PASS   the four views partition 310 symbols once each;
                             no reference in two views; no part identity on
                             two footprints
    FAB7  SOURCING    FAIL   247 assembly references, 64 orderable — 25.9 %
    FAB8  OUTLINE     PASS   the Edge.Cuts profile is the board outline to the
                             micron

## The open blocker: sourcing

**183 of the 247 fitted, purchased, on-board references, across 70 BOM lines,
carry neither a manufacturer part number nor an LCSC code.**  110 resistors,
72 capacitors and one connector.  A line a supplier cannot quote is not a
finished BOM, and this is the largest remaining item in the
`DEMO_READY_FOR_FAB` list.

`hardware/demo/manufacturing/screen_bom_sourcing.py` turns that number into a
work list by asking, for every unsourced line, whether this repository already
holds a reviewed answer — the Demo's own sourced lines, the per-line CTO audit
in `hardware/beta-dm/fab/jlcpcb/JLC-MATCH-AUDIT.csv`, and
`hardware/beta-dm/fab/BETA-DM-MPN-LEDGER.csv`.  The match rule is deliberately
brittle: value string and footprint leaf name equal character for character,
because `10uF 10V X7R` and `10uF` are not the same specification and the
beta-dm audit itself rejected two vendor matches for exactly that reason.

    EXACT_PRIOR    31 lines   114 parts     an audited decision already exists
    NEAR_MISS       0 lines     0 parts
    NO_CANDIDATE   39 lines    69 parts     27 C, 41 R, 1 J — new decisions

Grafting the 31 would take coverage from 25.9 % to about 72 %.  It is not
mechanical: each beta-dm audit note reasons about the net that part sits on
in **that** board, and the Demo's nets must be re-checked before the identity
is adopted.

## One part identity was wrong and has been removed

`C26` (10 uF 10 V X7R, 1206) carried LCSC `C344022`, which is `C24`'s part —
10 uF 25 V X5R in an 0603 body.  One code, two land patterns.  A factory acting
on it would have placed an 0603 part on a 1206 land at the wrong dielectric and
the wrong rating.  The code is removed from `C26`, which now sits honestly in
the sourcing gap above rather than carrying a wrong answer.  FAB6's
"one part identity, one footprint" claim exists so this cannot recur silently.
