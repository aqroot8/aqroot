# AQROOT Demo — Fabrication Package

Status: **GENERATED AND REVIEWED — FAB1–FAB8 AND LAND1–LAND6 ALL PASS (D-616).**
`FAB7` closed at D-615 (BOM **100.0 % orderable, 247 of 247**).  The land
question closed at D-616: `checks/land_parity_contract.py` proves **311 of 311
board footprints are pad-identical to their library masters, to the nanometre**,
and that every one of the 49 distinct identities is ruled against a drawing in
`assembly/FOOTPRINT_VERIFICATION_LEDGER.md`.  The 199 `lib_footprint_issues`
turned out never to have been a board defect — KiCad's stock libraries were
installed but never registered, so **no land on this board had ever been
compared to its master**; registering the table KiCad ships takes them to zero.

**The package is still NOT RELEASABLE, and the reason is now a specific,
measured one: the ESP32-S3-WROOM-1 antenna keep-out protects four of the six
copper layers.**  `In3.Cu` carries 273.697 mm² of `+3V3` plane and 4 track
segments and `In4.Cu` 304.259 mm² of `GND` pour inside it.  Ledger §6.2,
instrument `screen_footprint_keepouts.py`, evidence
`evidence/d616-footprint-keepouts.json`.  One land is also still open on its
*drawing* link only: `J8`'s JST `eSH.pdf` was not re-read.

The package lives in `hardware/demo/fab/`.  It is not hand-assembled: it is
produced in one command by `hardware/demo/manufacturing/export_fab_package.py`
and reviewed by `hardware/demo/manufacturing/checks/fab_package_contract.py`.
Do not edit an artifact in place — regenerate.

    python3 hardware/demo/manufacturing/export_fab_package.py
    python3 hardware/demo/manufacturing/checks/fab_package_contract.py

The BOM's part identities are not hand-edited either.  There are two deciders
and one writer, and the set is reproducible: replaying the committed plans
against the `HEAD` schematic returns all ten sheets **and the project symbol
library** byte-identical.

`screen_bom_sourcing.py` asks whether THIS REPOSITORY already holds a reviewed
answer.  `rule_open_sourcing.py` asks a LIVE DISTRIBUTOR, which is what D-096
requires, through `jlc_live.py` — which archives every query it makes, with the
UTC minute it was read, under `evidence/jlc-live/`, and replays the archive
unless `--refresh` is given.  `apply_bom_sourcing.py` writes.

    python3 hardware/demo/manufacturing/screen_bom_sourcing.py \
        --plan PLAN.json --worklist OPEN.csv
    python3 hardware/demo/manufacturing/rule_open_sourcing.py \
        [--include-tune] [--refresh] --plan PLAN.json -o REPORT.json
    python3 hardware/demo/manufacturing/apply_bom_sourcing.py \
        --plan PLAN.json --apply

`apply_bom_sourcing.py` ADDS a missing identity freely and CORRECTS an existing
one only when the plan NAMES the exact string it is overwriting — `replaces` for
a symbol property, `text_replaces` for the two places that carry a part identity
and are not instance properties: the cached library symbol inside a sheet and
the project's own `.kicad_sym`.  Leaving those stale is how a corrected instance
gets silently un-corrected by *Update Symbols from Library*.

The LAND CHAIN is proved by three tracked tools.  `screen_land_parity.py` is the
board-to-master link, `checks/land_parity_contract.py` gates LAND1–LAND6 against
`land_citations.json` and the ledger, and `apply_footprint_identity.py` is the
only writer of a footprint's library nickname or description — it NAMES the
string it overwrites and re-reads the result through `pcbnew`, rolling back if
the board does not say what the plan claimed:

    python3 hardware/demo/manufacturing/screen_land_parity.py -o REPORT.json \
        [--worklist RESIDUAL.csv] [--perturb REF]
    python3 hardware/demo/manufacturing/checks/land_parity_contract.py -o REPORT.json
    python3 hardware/demo/manufacturing/screen_footprint_keepouts.py -o REPORT.json
    python3 hardware/demo/manufacturing/apply_footprint_identity.py \
        --plan PLAN.json [--apply]

`--perturb REF` is the negative control: it grows one pad by a micron and the
run is only trustworthy if that reference then reports MISMATCH.

And one screen asks the `C26` question of every sourced line at once, against
the distributor's own package field:

    python3 hardware/demo/manufacturing/screen_part_land_parity.py \
        -o REPORT.json --worklist SHORT.csv

It reports MATCH / MISMATCH / **UNCOMPARABLE**, and the third verdict is
deliberate: a footprint named `MAX17048_T822` names a PART, not a JEDEC body,
and counting it as a pass would be the D-611 failure again — a check that reads
TRUE because it was never asked.

## Authority

    board      hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb
    sha256     449977eac20b7644474a9f01da811d4618bb8c5e6a0fa4222ffa70aba2e69f00
    generator  kicad-cli 10.0.5
    release    MANIFEST.json carries the board, rule and project sha256, a
               sha256 for EVERY ONE OF THE TEN schematic sheets, and a sha256
               for every artifact.  The sheet hashes exist because the BOM is
               derived from the whole hierarchy: the manifest recorded only the
               ROOT sheet until D-614, whose sourcing graft changed nine child
               sheets and not one byte of the root, so the manifest would have
               certified an unchanged schematic beside a changed BOM.  FAB1
               requires all ten to match.

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

## Review — `checks/fab_package_contract.py` (ALL EIGHT PASS)

    FAB1  PROVENANCE  PASS   manifest names the authoritative board sha256
                             AND all ten schematic sheet sha256; all 28
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
    FAB7  SOURCING    PASS   247 assembly references, 247 orderable --
                             coverage 1.0000, needs_a_sourcing_decision ZERO.
                             The PASS condition was never relaxed: one
                             unquotable line and this still fails (D-615)
    FAB8  OUTLINE     PASS   the Edge.Cuts profile is the board outline to the
                             micron

## Sourcing: 100 % — and the two questions that closed it (D-615)

    FAB7  SOURCING    PASS   247 of 247 fitted references orderable
                             coverage 1.0000
                             needs_a_sourcing_decision   0 lines / 0 parts
                             pending_first_article_tune  0 lines / 0 parts

D-613 opened this at **25.9 %**.  D-614 grafted 122 identities the repository
had already audited and reached **75.3 %**, then stopped for a stated reason:
**D-096 binds** — a part number configured from an ordering scheme is a
hypothesis until a distributor record confirms lifecycle and stock.  D-615 read
that record 225 times and archived every answer.

**26 lines / 45 parts had no prior anywhere.**  Each candidate is read as a
PART, off the record's own parametric attributes, and gated on land, magnitude,
tolerance, ranked dielectric, node voltage (`net_gate`, unchanged), dissipation
(new, in `net_gate`'s image), vendor and stock.  The single sharpest proof of
why the record and not the name is the authority:

    R69 is 1.87 ohm       ->  UNI-ROYAL 0603WAF187KT5E   LCSC C422967
    0603WAF1873T5E        ->  187 kOhm                   LCSC C22896

One character, five orders of magnitude, two separate catalogue records.

**THE DISSIPATION GATE NEEDED NUMBERS THE BOARD DID NOT HAVE.**  `NET_MAX_DC`
grew from 17 established nodes to **48**, each naming the supply or part limit
that bounds it.  Three of them are worth reading:

* `LTC_GATE` is bounded at `VOUT` **+ 13.1 V** — from the U18 footprint's own
  description of the LTC4368 charge pump, corroborated by the NTMD4820N's V_GS
  abs max.  Nothing was guessed.
* **`R95`'s node over-bound UNDERSTATES its dissipation.**  V²/R across the
  node gives 54 mW; the single-fault case puts a reversed cell IN SERIES with
  VBUS and the real answer is 154 mW.  Ten references therefore carry an
  explicit current ruling instead.
* **`R24` and `C12`'s Value strings are looser than their own symbol notes** —
  `12R` against *"12R 1 percent"*, `22uF` against *"the part is specified X7R
  16 V in 1210"*.  Both are gated on the note, and both landed better than the
  note asked.

`R75` is gated on a part CLASS, not a number: `15mR 1% 1W` is satisfied on paper
by a thick film at ±1500 ppm/°C, which would move the LTC4368's 3.33 A trip by
19 % over −40…+85 °C.  The gate requires a current-sense / alloy part at
≤100 ppm/°C.

**THE 16 TUNE PARTS ARE BOUGHT, AND TOLD THEY ARE PROVISIONAL.**  DEVICE_SPEC
s.14 is right that no part number closes an NFC matching value — and you cannot
build a first article out of an empty position.  Each now carries a
FIRST-ARTICLE part number whose own `Note_Sourcing` says, in the schematic, that
it is expected to change after the VNA.  Two things are refused rather than
invented: the ST25R3916 tank NODE VOLTAGE (so those lines are gated on the
sheet's own 50 V C0G ruling) and the tank CURRENT (so `R114`–`R117` took the
highest-rated part their 0603 land offers, and the dissipation is a
first-article measurement).

## The safety part was ordered in the wrong package (D-615)

    board land       Package_SO:MSOP-10_3x3mm_P0.5mm
    BOM order code   LTC4368IDD-1#PBF
    live record      DFN-10-EP(3x3), body 0.75 mm   (MS variants: MSOP-10, 1.1 mm)

`DD` is DFN.  D-099 locked `LTC4368IMS-1#PBF`, MSOP-10, under FBV2-PWR-002 —
*"every new safety-critical part is leaded and inspectable … no bottom-terminated
parts"* — and corrected the FOOTPRINT while the part identity stayed DFN.  The
cached library symbol and the project `.kicad_sym` both still carried the DD
code **and** a `Package` field describing a DFN beside a `Footprint` field that
already read MSOP-10.

Corrected to **`LTC4368IMS-1#TRPBF`, LCSC `C688401`**, MSOP-10, I grade, `-1`
suffix — the tape-and-reel order code of the identical device, D-210's precedent
exactly, **not an electrical change**.  `LTC4368IMS-1#PBF` reads stock 0.

## What is still open, and it is purchasing

Nine lines sit under 10× the first-five need on the assembler's own catalogue
and five read ZERO — `J5`, `L4`, `MK1`, `U19`, `U9`, then `Q2`/`Q3` 0,
`U2`/`U3` 1, `U18` 3, `D8` 7.  Most are already CONSIGNED classes under D-206
and are bought from a broadline distributor, so a zero here is a brief to work
rather than a design defect.  The list, with the UTC minute each was read, is
`hardware/demo/manufacturing/evidence/d615-purchasing-short.csv`.

<!-- HISTORICAL — superseded by the section above -->

## Sourcing: 75.3 %, and what the remaining quarter actually is

**186 of the 247 fitted, purchased, on-board references are orderable.**  At
D-613 it was 64.  The 122 that closed were not typed in: `screen_bom_sourcing.py`
proposed them from four repo-local authorities and `apply_bom_sourcing.py`
wrote them, and the pair reproduces the result byte for byte from `HEAD`.

    EXACT_PRIOR        31 lines  114 parts   value string and land equal
    CONTAINED_PRIOR     4 lines    7 parts   a ruling, stated and checked
    REFERENCE_RULING    1 line     1 part    J8, from this project's D-238
    ---------------------------------------------------------------------
    TUNE_PENDING        8 lines   16 parts   the VALUE is not final
    NO_CANDIDATE       26 lines   45 parts   a new purchasing decision

### The rules the screen works under, and why each exists

**The reference is not the identity; the specification is.**  The beta-dm audit
rows are keyed by designator and three of them name a *different value* at the
same designator -- `R70`-`R73` are 39R there and **33R** here, `R69` is 2.55R
there and **1.87R** here, `R19`/`R20` are 4.7k there and **2.2k** here, because
D-079 re-derived the backlight against the real ER-TFT035IPS-6 panel.  A
designator-keyed graft puts a 39 ohm part on a 33 ohm land.  Nothing matches on
a designator.

**Containment is one-directional and checked.**  `EXACT_PRIOR` needs the value
string and the footprint leaf equal character for character.  Anything looser is
a ruling, and the only ruling the screen makes on its own is specification
containment: same land, equal magnitude, prior tolerance <= demanded, prior
voltage >= demanded, prior dielectric class >= demanded, prior power >=
demanded.  `10uF 10V X7R` serves a `10uF` line; a `10uF` part of unknown
dielectric never serves an X7R line.

**The rating belongs to the part, not to the line.**  Every rating, dielectric,
tolerance, capacitance and land is decoded from the approved part number --
YAGEO `CC`, Samsung `CL`, Murata `GRM`, CCTC `TCC`, UNI-ROYAL `0603WAF` -- and
then required to agree with the audit prose.  This matters: the schematic asks
`1uF 10V X7R` and the audit approved a **25 V** part, which is what makes
`C38`/`C67` legal on the 5.5 V `ACC_5V_SW` rail where a literal 10 V part would
sit at 1.8x.  The land decode is the direct guard against the `C26` defect
below: `CL21A475KAQNNNE` offered for an 0603 line is refused as *"part number is
built for land 0805"*.

**The prior's manufacturer column does not describe the approved part.**  For a
REJECTED audit row `JLC Manufacturer` names the match that was thrown out, and
sixteen of the thirty-one grafts are REJECTED rows.  The manufacturer is derived
from the approved MPN's own family and corroborated against the prose; an
uncorroborated derivation is refused.

**Every candidate is re-checked against the Demo's own nets.**  A capacitor must
be rated at least 2x the node's operating maximum *and* survive its absolute
maximum, read from the real board.  A node this repository has not established
is refused, not guessed.  `LED_BOOST` is the interesting one: ARCHITECTURE
D-079 gives six backlight LEDs in parallel at 2.9-3.2 V and 109 mA, so the node
runs at 4.3 V through `R70`-`R73` (4x33R) and the `R69` sense -- but its FAULT
ceiling is the `U17` TPS61169 open-LED OVP, which is why `C44` is a 50 V part
and a 25 V one is refused there.

**A 0 ohm link carries whatever the net carries.**  The beta-dm note closes its
current gate for `R32`, `R35` and `R42`.  The Demo has **eight** 0 ohm links;
`R121`/`R122` are in the speaker output and `R106` carries the whole NFC front
end.  Every grafted 0 ohm reference must carry a number or the line is refused:

    R35   0.500 A   BQ25185 input current limit, TI SLUSF65A 8.2.2.1 at
                    R_ILIM/VSET = 18k; the Demo's R36 IS 18k and R37 IS 1k
    R121  0.292 A   U5 MAX98357A bridge-tied from +3V3 into the 8 ohm 0.5 W
    R122  0.292 A   LS1 -- 3.3 V peak differential, 2.33 Vrms, 0.68 W; the
                    amplifier bounds it above the speaker's own rating
    R106  0.150 A   NFC field current ceiling, D-130
    R32 / R42 / R109 / R118    signal level

against the UNI-ROYAL ZW-series 0603 jumper -- 1 A continuous, 2 A overload.
Worst case 0.500 A, 2.0x.

### `J8` -- the one place a designator is the right key

`J8`'s part was chosen at **D-238** and recorded in
`docs/full-beta-v2/assembly/SOURCING_LEDGER.md`: JST **`SM04B-SRSS-TB(LF)(SN)`**,
the plating-suffixed string D-096 requires because the bare order code resolves
to a zero-stock listing.  DEVICE_SPEC s.16 item 8 listed the missing schematic
property as a known open item.  That is a per-reference ruling from this
project's own decision, and it is honoured only because the board corroborates
it -- the footprint name contains `SM04B-SRSS-TB`.  The MPN is now in the
schematic; **the LCSC code is still absent.**

### What is still open, and it is two different things

**8 lines / 16 parts are `TUNE`.**  DEVICE_SPEC s.14 records the NFC matching
network -- `C69`-`C80` and `R114`-`R117` -- as FIRST-ARTICLE TUNE, values
pending VNA and the ST STSW-ST25R004 tool.  No part number can close a line
whose value is not decided.  These close at first article, with the board in
hand, and they are not a purchasing task.

**26 lines / 45 parts need a purchasing decision.**  The brief is
`hardware/demo/manufacturing/evidence/d614-sourcing-open.csv`, one row per line
with the parsed requirement (magnitude, tolerance, voltage, dielectric, power)
and the Demo nets the part sits on.  **D-096 binds**: a part number configured
from an ordering scheme is a hypothesis, not a selection, until a live
manufacturer or distributor record confirms lifecycle and stock.

Two of the 45 carry engineering constraints this repository already recorded,
and they must reach whoever buys them:

  * **`C65`/`C66`** 22 uF 10 V X7R 0805 -- SOURCING_LEDGER **S-4 / B-69**: they
    carry no DC-bias note, and their **derated** value sets the `U21` boost
    start-up time.  Nominal capacitance is not the selection criterion.
  * **`R75`** 15 mOhm 1 % 1 W 2512 -- the battery current sense on
    `BAT_PROTECTED_P` / `BAT_SENSE`.  The screen could not even read this
    requirement until D-614: its value parser took one suffix letter, so `15mR`
    did not parse and the line came back with an empty magnitude and no power
    rating.  It now reports any value string it cannot read rather than
    emitting a blank cell.

## One part identity was wrong and has been removed

`C26` (10 uF 10 V X7R, 1206) carried LCSC `C344022`, which is `C24`'s part —
10 uF 25 V X5R in an 0603 body.  One code, two land patterns.  A factory acting
on it would have placed an 0603 part on a 1206 land at the wrong dielectric and
the wrong rating.  The code was removed at D-613, and at D-614 `C26` was given
the **right** identity from the beta-dm audit: Murata `GRM31CR71E106KA12L` /
LCSC `C77093`, 10 uF **25 V** X7R in a **1206** body, the part TI SLUSF65A
8.2.2.3 asks for on `BQ25185_SYS`.

Two claims now exist so this cannot recur silently.  FAB6 refuses one part
identity on two footprints.  And `screen_bom_sourcing.py` decodes the **land**
out of the part number itself and refuses any candidate whose land disagrees
with the line's — offering `CL21A475KAQNNNE` for an 0603 line is rejected as
*"part number is built for land 0805, the line is 0603"*, which is the same
defect caught one step earlier, before it can be written.
