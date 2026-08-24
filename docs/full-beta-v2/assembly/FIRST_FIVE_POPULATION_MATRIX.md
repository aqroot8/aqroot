# AQROOT Full Beta v2 — first-five population matrix

**Status: NORMATIVE for the first five boards.** Generated 2026-08-23 at FBV2-S2-001 from a
`kicad-cli` netlist/schematic extraction of `hardware/beta-v2/kicad/aqroot-beta-v2/`, not from a
spreadsheet. **Regenerate it the same way before quoting it.**
Authority: [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md) outranks this file.

**322 schematic components · 306 FITTED · 16 DNP · 1 off-board (`LS1`) · 47 test points.**

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
| Dead-cell recovery | **FIT** — `U19`, `Q5`, `D8`, `D10`–`D12`, dividers; `R93` **DNP** hysteresis |
| Reverse-polarity path | **FIT** — `U18` LTC4368-1, `Q2`, `Q3`, `R75`, `F1` |
| Accessory 3.3 V rail | **FIT** — `U20` + `R97` 1.5 kΩ + `R98` 100 kΩ down |
| Accessory 5 V rail | **FIT** — `U21` + `L4` + `C64`–`C66` + `U22` + `R101` 1.65 kΩ + `R102`/`R131` 100 kΩ down |
| `U16` TCA4307 | **FIT** — corrected at FBV2-S1-009 (was DNP as a TCA9517A) |
| External I²C pull-ups `R49`/`R50` | **FIT at 1.5 kΩ** — corrected at FBV2-S1-009 (were 4.7 kΩ **DNP**) |
| ESD arrays `D2`–`D5` | **FIT** — corrected at FBV2-S1-009 (all were DNP) |
| Front RGB `D13` + `R124`–`R126` | **FIT** |
| Expanders `U2`, `U3`, `U23` | **FIT** |
| Buttons `SW1`–`SW7`, `SW9` | **FIT** |
| Community connector `J5` | **FIT — MANUAL / SECONDARY ASSEMBLY** (through-hole) |
| Display connector `J1` | **FIT — MANUAL ASSEMBLY** (B-47; no proven second source) |
| Battery | **OFF-BOARD** via `J4` |
| Test points `TP1`–`TP47` | **FIT** (bare pads) |

---

## 5. Assembly strategy

| strategy | parts |
|---|---|
| **SMT, automated** | everything except the two rows below |
| **MANUAL / SECONDARY** | **`J5`** Samtec BCS-112-S-D-HE — 24 × Ø0.71 mm through-hole; **`D1`** Vishay TSAL6100 — 5 mm THT LED; **`J1`** Hirose FH69-50S-0.5SH — see B-47 |
| **OFF-BOARD** | `LS1` speaker, display + touch panel, both antennas, the 915 MHz pigtail assembly, the NFC flex antenna, the battery |

> **`J5` and `J1` are deliberate manual-assembly choices, not oversights.** The CTO ruling stands:
> for five prototypes, hand-soldering a proven connector beats a speculative footprint migration.

**ESD warning for assembly:** `D13` (MEIHUA RGB) has **green and blue dice rated only 150 V HBM**
against 2000 V for red. Handle as an ESD-sensitive part.

---

## 6. Tune-at-bring-up items — NOT fabrication blockers

| item | what is measured |
|---|---|
| NFC matching `C69`–`C80`, `L5`, `L6`, `R114`–`R117` | antenna Q and tuning against the fitted flex antenna |
| `R97` / `R101` accessory `R_ILIM` | real internal worst-case rail current, then raise the published limits |
| `R93` | dead-cell handoff chatter |
| `R123` | IR range against the real optical stack |
| `C81`/`C82` | speaker EMI, only if a scan fails |
| `R49`/`R50` | measured external bus capacitance (O-7 accepted Option A: 1.5 kΩ) |
| `R110` | BMI270 `INT1` drive, fallback 47 kΩ |
