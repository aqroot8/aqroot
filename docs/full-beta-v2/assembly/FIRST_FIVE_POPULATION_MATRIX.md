# AQROOT Full Beta v2 — first-five population matrix

**Status: NORMATIVE for the first five boards.** Generated 2026-08-23 at FBV2-S2-001 from a
`kicad-cli` netlist/schematic extraction of `hardware/beta-v2/kicad/aqroot-beta-v2/`, not from a
spreadsheet. **Regenerate it the same way before quoting it.**
Authority: [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md) outranks this file.

~~322 schematic components · 306 FITTED · 16 DNP · 1 off-board (`LS1`) · 47 test points~~ *(the FBV2-S2-001 beta-v2 count — HISTORICAL, superseded)*.

> **D-800 RE-DERIVED FROM THE DEMO SCHEMATIC (`hardware/demo/kicad/aqroot-demo/`), Round-19 full review:**
> **314 schematic symbols · 298 not DNP · 16 DNP**; of the 298, `LS1` is off-board, `J4` is the manual battery-harness
> connector (`BATTERY_HARNESS.json`), and 45 are non-purchased test points.
> The DNP set below is unchanged and exact.  **This matrix is a SUMMARY: the purchasing and placement
> authority is the generated fab package** (`aqroot-Demo-BOM-assembly.csv`, `-DO-NOT-POPULATE.csv`,
> `-pos-fitted.csv`), and F12 now scans this file for stale values.  D-800 corrected two resistor values
> here that had been carried since beta-v2: `R97` is **1.87 kΩ** and `R101` is **2.43 kΩ**.

> **RE-CHECKED 2026-08-23 (FBV2-S2-002). The counts are unchanged — but eight of the sixteen DNP parts still carried NO RECORDED REASON, and all eight now do (D-208).**
>
> - **`U13`, `L2`, `R44`, `R45`, `C34`, `C35`** are the **NFC 5 V boost branch** — TPS61023 + 1 µH + feedback divider + output caps producing `NFC_5V_PA_PENDING` from `BQ25185_SYS`. **DNP is correct**: D-055/D-056 select `NFC_SUPPLY` = `+3V3` through `R106` (fitted), and `R107` (DNP) is the mutually exclusive 5 V link. **The branch is preserved, not abandoned** — a D-049 no-respin escape if the 3.3 V field measures short. **Never fit `R106` and `R107` together.** Traced through the netlist and confirmed **not** to be an inherited Beta-DM oversight.
> - **`R119`** is the BMI270 alternate-address strap. `R118` (fitted, 0 Ω to GND) holds `BMI270_SDO_ADDR` low so the IMU answers at **0x68**. **`R118` and `R119` are mutually exclusive — fitting both shorts `+3V3` to GND through two 0 Ω links.**
> - **`R112`** links display `SDO` to the shared `SPI_A_MISO`, DNP so the panel cannot drive the bus the microSD reads on. Fitting it is a bring-up provision and **must not** be done while **MX-8** is relied on.
>
> **The design now has zero DNP parts without a recorded reason.** For the route each FITTED part takes to the board, see [`FIRST_FIVE_ASSEMBLY_PLAN.md`](FIRST_FIVE_ASSEMBLY_PLAN.md).

---

## 1. The rule this file exists to enforce

> **A `DNP` inherited from Beta-DM describes what was populated on that reduced build, not what
> the Full Beta v2 architecture requires.** Six of the nine migrated sheets carried a
> load-bearing inherited `DNP`. Every one of them would have shipped a dead subsystem.

**FBV2-S2-001 found the seventh and worst.**

---

## 2. THE FINDING — NFC was still DNP

| ref | was | now | why |
|---|---|---|---|
| **`U9` ST25R3916-AQET** | **DNP** | **FIT** | **D-035: *"NFC is mandatory in the FIRST Full Beta v2 fabrication. No DNP showcase shortcut."* D-055: *"NFC must be FITTED and functional on the first fabrication."*** |
| `C19`, `C55` | DNP | **FIT** | `NFC_SUPPLY` decoupling |
| `C45`, `C46` | DNP | **FIT** | `VDD_D` decoupling |
| `C47`, `C48` | DNP | **FIT** | `VDD_A` decoupling |
| `C49`, `C50` | DNP | **FIT** | `VDD_RF` decoupling |
| `C51`, `C52` | DNP | **FIT** | `VDD_AM` decoupling |
| `C53`, `C54` | DNP | **FIT** | `AGDC` decoupling |

**The board would have been built with a complete, FITTED 13.56 MHz matching network (`C69`–`C80`,
`L5`, `L6`, `R114`–`R117`), a FITTED 27.12 MHz crystal, a FITTED antenna connector `J7`, FITTED
SPI wiring — and no NFC chip.** Twelve of the thirteen parts turned on here are mandatory supply
decoupling in DS12484; none is optional.

---

## 3. Every remaining DNP, and why

**Sixteen parts are DNP and every one is now explained. There is no unexplained DNP left.**

| ref | value | classification | authority |
|---|---|---|---|
| `U13` | TPS61023 | **DNP — NFC 5 V fallback boost.** No-respin branch; the first build runs NFC from `+3V3` | D-055 / D-056 |
| `L2` | 1 µH | DNP — same branch. **Same MPN as the FITTED `L4`** | D-056 |
| `C34`, `C35` | 22 µF | DNP — same branch | D-056 |
| `R44`, `R45` | 732 k / 100 k | DNP — same branch, feedback divider | D-056 |
| `R107` | 0 Ω | **DNP — NFC supply source selector.** Mutually exclusive with `R106` 0 Ω **FIT**; the two can never be fitted together | D-055 |
| `R112` | 0 Ω | DNP — display `SDO` isolation; the panel is off SPI-A by default | D-114 |
| `R119` | 0 Ω | DNP — BMI270 `0x69` rework strap; `R118` 0 Ω is FITTED for `0x68`. **Fit one only** | D-140 |
| `R123` | 100 Ω | DNP — IR drive parallel trim, **never below 10 Ω total** with `R24` | D-157 |
| `C81`, `C82` | 1 nF | DNP — speaker EMI filter; `R121`/`R122` 0 Ω FITTED is the default | D-150 |
| `R93` | 22 M | DNP — dead-cell recovery hysteresis. **Fit only if handoff chatter is seen at bring-up** | FBV2-PWR-002 |
| **`R68`** | **0 Ω** | **DNP AND IT MUST STAY DNP.** A bypass **across `SW9`**, the hard power switch. **Fitting it wires the unit permanently ON and defeats the one provision that lets a user power down a hung or unflashed board.** Bench characterisation only | **FBV2-S2-001** |
| **`C21`, `C22`** | 100 pF | **DEAD PADS.** DNP, and **one terminal is deliberately no-connect flagged** — fitting the part alone does nothing. Reserved 0603 rework pads by the USB block, usable only by cutting a trace. **Deletion candidate at placement** | **FBV2-S2-001** |

**Mutually exclusive pairs — fit exactly one of each:**
`R106` (FIT) / `R107` (DNP) · `R118` (FIT) / `R119` (DNP).

---

## 4. Population by subsystem

| subsystem | first-five state |
|---|---|
| **NFC IC + decoupling** | **FIT** — corrected at FBV2-S2-001 |
| NFC 3.3 V source selector | `R106` **FIT** / `R107` **DNP** |
| NFC optional 5 V boost | **DNP** — `U13`, `L2`, `C34`, `C35`, `R44`, `R45` |
| NFC matching passives | **FIT, TUNE AT BRING-UP** — `C69`–`C80`, `L5`, `L6`, `R114`–`R117` are marked `TUNE` |
| NFC antenna | **OFF-BOARD** — Taoglas `FXC.46.52.0075X.B.dg` via `J7` |
| Display `SDO` `R112` | **DNP** |
| Display + backlight | **FIT**; panel and touch **OFF-BOARD** |
| Audio EMI `C81`/`C82` | **DNP**; `R121`/`R122` 0 Ω **FIT** |
| Speaker | **OFF-BOARD** via `J6` |
| Microphone `MK1` | **FIT** |
| IR TX + RX | **FIT** (all eight parts, corrected at FBV2-S1-007); `R123` **DNP** trim |
| Radios `U7`, `U8` | **FIT**; antennas **OFF-BOARD** |
| Dead-cell recovery | **FIT** — `U19`, `Q5`, `D8`, **`D10`–`D12` = Diodes Inc `BAT54WS-7-F` (`C124205`), each ONE independent SOD-323 Schottky (D-211)**, dividers; `R93` **DNP** hysteresis |
| Reverse-polarity path | **FIT** — `U18` LTC4368-1, `Q2`, `Q3`, `R75`, **`F1` = Littelfuse `0466005.NRHF` (`C57525`), 5 A 32 V 1206 fast-acting (D-210)** |
| Accessory 3.3 V rail | **FIT** — `U20` + `R97` 1.87 kΩ (`0603WAF1871T5E`) + `R98` 100 kΩ down |
| Accessory 5 V rail | **FIT** — `U21` + `L4` + `C64`–`C66` + `U22` + `R101` 2.43 kΩ (`0603WAF2431T5E`) + `R102`/`R131` 100 kΩ down |
| `U16` TCA4307 | **FIT** — corrected at FBV2-S1-009 (was DNP as a TCA9517A) |
| External I²C pull-ups `R49`/`R50` | **FIT at 1.5 kΩ** — corrected at FBV2-S1-009 (were 4.7 kΩ **DNP**) |
| ESD arrays `D2`–`D5` | **FIT** — corrected at FBV2-S1-009 (all were DNP) |
| Front RGB `D13` + `R124`–`R126` | **FIT** |
| Expanders `U2`, `U3` | **FIT** (there is no `U23` on the Demo schematic — D-800) |
| Buttons `SW1`–`SW7`, `SW9` | **FIT** |
| Community connector `J5` | **FIT — MANUAL / SECONDARY ASSEMBLY** (through-hole, Samtec `SSQ-124-02-G-S-RA`) |
| Display connector `J1` | **FIT — MACHINE-PLACED** (Hirose `FH69-50S-0.5SH`, in the CPL, top side; JLC carries the genuine part — see `FIRST_FIVE_ASSEMBLY_PLAN.md` §3) |
| Battery | **OFF-BOARD** via `J4` |
| Test points (45: `TP1`–`TP47` less `TP14` and `TP41`) | **FIT** (bare pads) |

---

## 5. Assembly strategy

| strategy | parts |
|---|---|
| **SMT, automated** | everything except the two rows below — including `J1` |
| **MANUAL / SECONDARY** | the five through-hole parts of `FIRST_FIVE_ASSEMBLY_PLAN.md` §6, which is the authority: **`J5`** Samtec `SSQ-124-02-G-S-RA` — 24 × Ø1.02 mm; **`D1`** Vishay TSAL6100 and **`U6`** TSOP38238 — lead-formed per `IR_LEAD_FORMING.md`; **`J6`** speaker header; **`J4`** the manual battery pigtail per `THT_LEAD_TRIM.md` / `BATTERY_HARNESS.json` *(D-800 corrected this row: it named the superseded BCS-112 and a manual `J1`, and omitted `U6`, `J6` and `J4`)* |
| **OFF-BOARD** | `LS1` speaker, display + touch panel, both antennas, the 915 MHz pigtail assembly, the NFC flex antenna, the battery |

> **`J5` is a deliberate manual-assembly choice, not an oversight.** *(`J1` was manual at FBV2-S2-001 and is
> machine-placed since; that half of this note is HISTORICAL.)*

**ESD warning for assembly:** `D13` (MEIHUA RGB) has **green and blue dice rated only 150 V HBM**
against 2000 V for red. Handle as an ESD-sensitive part.

---

## 6. Tune-at-bring-up items — NOT fabrication blockers

| item | what is measured |
|---|---|
| NFC matching `C69`–`C80`, `L5`, `L6`, `R114`–`R117` | antenna Q and tuning against the fitted flex antenna |
| ~~`R97` / `R101` accessory `R_ILIM`~~ | **NOT a tune item (D-800).** `R97` 1.87 kΩ and `R101` 2.43 kΩ are FIXED by the owner-approved 400 mA / 300 mA budgets and the D-790 protection proof; `C-ACC-ILIM-01` QUALIFIES them and no published limit is raised at bring-up |
| `R93` | dead-cell handoff chatter |
| `R123` | IR range against the real optical stack |
| `C81`/`C82` | speaker EMI, only if a scan fails |
| `R49`/`R50` | measured external bus capacitance (O-7 accepted Option A: 1.5 kΩ) |
| `R110` | BMI270 `INT1` drive, fallback 47 kΩ |
