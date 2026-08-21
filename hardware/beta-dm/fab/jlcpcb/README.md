# JLCPCB upload artifacts — derived, not authoritative

These two files are **format conversions** of the released Beta-DM assembly
data, produced for JLCPCB's upload forms. They are derived artifacts: if they
ever disagree with the released files, the released files win.

| file | derived from |
|---|---|
| `AQROOT-Beta-DM-JLC-BOM.csv` | [`../aqroot-Beta-DM-BOM-fitted.csv`](../aqroot-Beta-DM-BOM-fitted.csv) |
| `AQROOT-Beta-DM-JLC-CPL.csv` | [`../aqroot-Beta-DM-pos-fitted.csv`](../aqroot-Beta-DM-pos-fitted.csv) |

Both sources were byte-identical before and after generation. No PCB, DRU,
Gerber, schematic or released assembly file was touched.

## Format authority

Checked against JLCPCB's current documentation on **2026-08-21** — the KiCad
help article, verified by JLCPCB on KiCad 10.0.3, which is the version this
project uses — and against JLCPCB's **official sample BOM**,
`Sample-BOM_JLCSMT.xlsx`.

**BOM** — header row of the official sample is
`Comment | Designator | Footprint | JLCPCB Part #（optional）`. The article
states the file must have "at least" those fields, so `Manufacturer` and
`Manufacturer Part Number` are carried as extra columns; JLCPCB's uploader maps
columns on import and ignores what it does not use.

**CPL** — "JLCPCB expects these columns: Designator, Mid X, Mid Y, Rotation and
Layer. Coordinates should be in millimetres."

The official sample BOM groups designators (`R5,R6` on one row), so grouped
rows are the expected form, not a merge that hides parts. Every one of the 131
designators appears explicitly.

## What the conversion changes — and what it must not

| field | treatment |
|---|---|
| `Mid X`, `Mid Y` | **verbatim** from the released CPL, millimetres, sign included |
| `Rotation` | normalised to 0–359 — the only change is `-90 → 270`, 3 parts. Mathematically equivalent; **no physical orientation changed** |
| `Layer` | `top → Top`, `bottom → Bottom`. Capitalisation only |
| `Designator` | verbatim |
| `Comment` | the released BOM `Value`, verbatim |
| `Footprint` | KiCad library prefix dropped — `Capacitor_SMD:C_0603_1608Metric → C_0603_1608Metric`. The footprint name itself is verbatim; this is what JLCPCB's own KiCad toolkit emits |
| `JLCPCB Part #` | filled **only** for the six references whose LCSC code is recorded as vendor-verified in [`../BETA-DM-MPN-LEDGER.csv`](../BETA-DM-MPN-LEDGER.csv) — `U1`, `U2`, `U3`, `MK1`, `J4`, `C24`. Blank everywhere else. **No LCSC number was invented** |

## Scope — what is in these files

**131 physical references**, the placeable fitted set.

| excluded | why |
|---|---|
| `TP1`–`TP15` | test pads, not procurement or placement items |
| `LS1` | off-board speaker, already absent from the released fitted BOM |
| 42 DNP parts | already absent from the released fitted BOM |

146 fitted − 15 test points = **131**, matching the released CPL row count
exactly.

## Validation performed

Designator set equality between the two files (131 = 131, no BOM-only, no
CPL-only, no duplicates); zero DNP, test-point or `LS1` leakage; all 18 required
references present (`U1 U2 U3 U4 U7 U8 U10 U11 U12 U14 U17 MK1 J1 J2 J3 J4 J5
C24`) and all 11 DNP references absent (`U5 U9 U13 U15 U16 D2–D7`); `C24` reads
`10uF 25V X5R` / `GRM188R61E106KA73D` with coordinates, rotation and side
identical to the released CPL; `J5` reads `TSW-113-08-G-D-RA`; the string
`22uF 25V X7R` appears nowhere; valid UTF-8 with no byte-order mark, LF line
endings, one header row, no duplicate headers, no ragged rows, no embedded
newlines, no blank designators, no NaN or infinite coordinates, every row has a
side and a rotation.

## V4 — J1 identity corrected (2026-08-21)

**`AQROOT-Beta-DM-JLC-BOM-v4.csv` is the file to upload.**

`J1` had been carrying the identity of the **display module** rather than the
part soldered to the board. Every earlier pass searched JLC for
`CH280QV10-CT` — a ChengHao 2.8″ TFT+CTP assembly — and correctly found it
discontinued, which is why `J1` sat in manual source. J1 is actually the
**PCB-side FPC connector, Hirose `FH69-50S-0.5SH`**, and JLC stocks it:
**`C25955556`, 1,072 pcs, minimum purchase 1, $1.69.**

| class | groups |
|---|---:|
| A EXACT APPROVED | 27 |
| B SAFE GENERIC | 37 |
| C WRONG MATCH | 0 |
| D MANUAL SOURCE | 2 |
| E CTO REVIEW | 0 |

**129 of 131 designators pinned.** Only `D8` and `J5` remain manual source.

The land was already `VERIFIED_VENDOR_EXACT` and was re-measured this pass
against the Hirose catalogue Recommended PCB Layout — signal 0.30 × 1.23 at
0.5 pitch spanning C = 24.5, hold-downs 0.36 × 4.25 at E = 28.73
centre-to-centre, depth 7.38 — every value exact. The display module now lives
in [`../aqroot-Beta-DM-OFF-BOARD.csv`](../aqroot-Beta-DM-OFF-BOARD.csv).

**`J1`'s `Comment` changed** from `CH280QV10-CT_50P` to `FH69-50S-0.5SH`, the
only V-to-V change to a comment. The frozen PCB keeps the old `F.Fab` string, so
the CPL `Val` column still reads `CH280QV10-CT_50P` for `J1` — the same class of
metadata-only divergence as `C24`, and the second of exactly two.

## V3 — CTO rulings applied, E list closed (2026-08-21)

**`AQROOT-Beta-DM-JLC-BOM-v3.csv` is the file to upload.** V1 and V2 are kept as
history. All three share identical designators, comments and footprints; only the
`JLCPCB Part #` column differs.

| class | groups |
|---|---:|
| A EXACT APPROVED | 26 |
| B SAFE GENERIC | 37 |
| C WRONG MATCH | 0 |
| D MANUAL SOURCE | 3 |
| **E CTO REVIEW** | **0** |

**128 of 131 designators are pinned.** The three that are not — `D8`, `J1`, `J5` —
are in [`JLC-MANUAL-SOURCE.csv`](JLC-MANUAL-SOURCE.csv); none has a purchasable
JLC code, so none was invented.

What changed from V2:

- **`D8`** locked to onsemi **`NSR0240HT1G`** (SOD-323). The previous
  `NSR0240V2T5G` is a SOD-523 part and never fitted the frozen land. JLC's
  `C152519` is not pinned: stock 13 against a 116-piece minimum purchase.
- **`SW1`–`SW8`** locked to one part, C&K **`PTS645SM43SMTR92LFS`** / `C221880`,
  1.6 N — the Beta-DM feel baseline, revisitable after hands-on testing.
- **`C26`/`C27`** pinned to Murata **`GRM31CR71E106KA12L`** / `C77093`,
  10 µF 25 V X7R 1206. Murata DC-bias data gives **9.000 µF at 4.5 V** per
  capacitor (−17.60 %), so 18.0 µF combined — 1.80× both floors, still 1.62× with
  tolerance and 1.38× with X7R temperature on top.
- **`R32`/`R35`/`R42`** pinned to `C21189`. TI SLUSF65A §8.2.2.1 fixes the
  BQ25185 input current limit at **500 mA** for our 18 k `R_ILIM/VSET`, and the
  UNI-ROYAL ZW jumper is rated 1 A — 2× margin on `R35`, the only power-node
  jumper of the three.

## V2 — explicit part numbers after auditing JLC's matches (2026-08-21)

`AQROOT-Beta-DM-JLC-BOM-v2.csv` supersedes V1 for upload. V1 is kept as the
unpinned baseline; designators, comments and footprints are **identical** between
them — V2 only fills the `JLCPCB Part #` column.

| file | what it is |
|---|---|
| `AQROOT-Beta-DM-JLC-BOM-v2.csv` | **upload this.** 66 rows / 131 designators, 115 pinned to an audited LCSC code |
| `AQROOT-Beta-DM-JLC-CPL.csv` | unchanged — still the correct placement file |
| `JLC-MATCH-AUDIT.csv` | every JLC auto-match, its verdict, the class, and why |
| `JLC-MANUAL-SOURCE.csv` | the 13 groups JLC cannot supply or that need a CTO decision |

**V2 dropped the `Manufacturer` and `Manufacturer Part Number` columns** and uses
exactly the four columns of JLCPCB's official sample —
`Comment, Designator, Footprint, JLCPCB Part #`. V1 carried those extras and JLC's
uploader ingested none of the part numbers, including `C24`'s: the workbook's
"Your BOM / JLCPCB Part #" column came back empty on every row. The four-column
layout removes the ambiguity. Manufacturer and MPN for every line live in
`JLC-MATCH-AUDIT.csv` and in the released BOM, which remain the authorities.

**On upload, confirm the column mapping shows `JLCPCB Part #` mapped** before
continuing — that is the step that silently failed last time.

## Before uploading

`C24` must be fitted as Murata **`GRM188R61E106KA73D`** — the PCB's internal
`F.Fab` text still reads the superseded `22uF 25V X7R` because the board is
byte-frozen. That text reaches no manufacturing layer and no assembler-facing
file. See [`../BETA-DM-FINAL-DESIGN-RELEASE.md`](../BETA-DM-FINAL-DESIGN-RELEASE.md) §1.6.

**Upload only. Stop on the component-matching page for CTO review. Do not
approve component matches and do not order.**
