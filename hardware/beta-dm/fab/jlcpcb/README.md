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

## Before uploading

`C24` must be fitted as Murata **`GRM188R61E106KA73D`** — the PCB's internal
`F.Fab` text still reads the superseded `22uF 25V X7R` because the board is
byte-frozen. That text reaches no manufacturing layer and no assembler-facing
file. See [`../BETA-DM-FINAL-DESIGN-RELEASE.md`](../BETA-DM-FINAL-DESIGN-RELEASE.md) §1.6.

**Upload only. Stop on the component-matching page for CTO review. Do not
approve component matches and do not order.**
