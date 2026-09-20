# AQROOT Full Beta v2 — first-five assembly plan (B-71)

**Status: NORMATIVE.** Created 2026-08-23 at **FBV2-S2-002**, closing **B-71**.
**AMENDED 2026-08-23 at FBV2-MECH-002 (D-210 / D-211): two substitutions were SIGNED OFF and ADOPTED,
and a factual error about `BAT54WS` was corrected.** See
[`../audits/2026-08-23-pre-floorplan-authority-reconciliation.md`](../audits/2026-08-23-pre-floorplan-authority-reconciliation.md).

> **CORRECTION — `BAT54WS` IS NOT A SERIES PAIR.** This file previously said so in §5 and §8. It is
> wrong: **SOD-323 is a two-terminal package**, every `BAT54WS` in the LCSC library from every
> manufacturer is catalogued **"1 Independent"**, and `D10`/`D11`/`D12` are each **one** two-pin
> `Device:D_Schottky` on a two-pad `Diode_SMD:D_SOD-323`. **The design was never wrong** — only this
> note was. Nexperia `BAT54W,115` remains correctly rejected, but **because it is a SOT-323 (SC-70)
> part — a FOOTPRINT mismatch — not because of diode count.**

> **This is not a requirement that every part be available from LCSC.** It is a requirement that
> **every part has an explicit first-five assembly plan.** A part that cannot be bought from LCSC
> is not a problem; a part with no stated route to the board is.

**Every LCSC/JLC figure below was read live on 2026-08-23 through the JLCPCB parts API**
(`selectSmtComponentList`), under **D-096**. **Stock is a snapshot, not a guarantee** — re-check
immediately before ordering, because six of the shortfalls below are single- or low-double-digit
quantities that will move.

---

## 1. The classes

| class | meaning | route to the board |
|---|---|---|
| **A** | JLC **Basic** library, in stock | machine-placed, no placement fee |
| **B** | JLC **Extended**, stock ≥ 2 × first-five need | machine-placed |
| **C** | JLC **Extended**, **stock short of the first-five need** | **buy from a broadline distributor and CONSIGN to JLC** — stays machine-placed |
| **D** | **not in the LCSC/JLC library at all** | consign, or adopt a **documented** equivalent after sign-off |
| **E** | through-hole / mechanically manual **by construction** | hand-soldered after reflow |
| **F** | **off-board** — never placed on this PCB | see [`OFF_BOARD_BOM.md`](OFF_BOARD_BOM.md) |

**Class C is the important one.** It exists so that a stock shortfall never turns into a
hand-assembly decision. **Consignment keeps fine-pitch parts on the machine.**

---

## 2. Class A — JLC Basic

| part | ref | LCSC | stock |
|---|---|---|---|
| `2N7002` | `Q10` | `C8545` | 2,334,365 |
| `AO3401A` | `Q5` | `C15127` | 538,825 |
| generic 0402 / 0603 / 0805 R and C | 127 R, 80 C | Basic library | abundant |

The 207 anonymous passives are the bulk of the placement count and are entirely Basic. **They were
deliberately not consolidated** — value consolidation before a layout exists optimises the wrong
thing, and that decision stands from FBV2-S2-001.

---

## 3. Class B — JLC Extended, comfortably in stock

| part | ref | LCSC | stock | need (5 boards) |
|---|---|---|---|---|
| `ESP32-S3-WROOM-1-N16R8` | `U1` | `C2913202` | 53,139 | 5 |
| `MAX98357AETE+T` | `U5` | `C910544` | 18,844 | 5 |
| `E07-400M10S` | `U7` | `C2965513` | 803 | 5 |
| `E22-900M22S` | `U8` | `C411293` | **24** | 5 |
| `USBLC6-2SC6` | `U10` | `C7519` | 41,662 | 5 |
| `BQ25185DLHR` | `U11` | `C19725033` | 671 | 5 |
| `TPS63020DSJR` | `U12` | `C15483` | 7,952 | 5 |
| `TPS61023DRLR` | `U21` (`U13` **DNP**) | `C919459` | 7,872 | **5** |
| `MAX17048G+T10` | `U14` | `C2682616` | 15,822 | 5 |
| `TCA4307DGKR` | `U16` | `C880333` | 4,181 | 5 |
| `TPS61169DCKR` | `U17` | `C71045` | 4,405 | 5 |
| `TPS22950CQDDCRQ1` (TPS22950-Q1, **D-765**) | `U20`, `U22` | `C17349276` | 4,050 | 10 |
| `BMI270` | `U4` | `C2836813` | 12,840 | 5 |
| `TPD4E1B06DRLR` | `D2`–`D5` | `C1972953` | 2,176 | 20 |
| `PMEG2010AEH,115` | `D9` | `C110921` | 32,772 | 5 |
| `MHPA3528RGBCT` | `D13` | `C409779` | 70,369 | 5 |
| `BSS138LT1G` | `Q4`, `Q6`–`Q9` | `C82045` | 762,522 | 25 |
| `GRM188R61E106KA73D` | `C24`, `C26` | `C344022` | 675,039 | 10 |
| `XFL4020-152MEC` | `L1` | `C3033018` | 20,020 | 5 |
| `XFL4020-472MEC` | `L3` | `C5156236` | 1,987 | 5 |
| `LQW18AN39NG80D` | `L5`, `L6` | `C2042966` | 270 | 10 |
| `PTS645SM43SMTR92LFS` | `SW1`–`SW7` | `C221880` | 8,432 | 35 |
| `JS102011SAQN` | `SW9` | `C221660` | 931 | 5 |
| `USB4105-GF-A-120` | `J3` | `C5184243` | 2,454 | 5 |
| `5025700893` | `J2` | `C429846` | 11,005 | 5 |
| `BM02B-ACHSS-GAN-ETF(LF)(SN)` | `J7` | `C5118738` | 16,260 | 5 |
| `TXM27.12M0004322DBBDO00T` | `Y1` | `C362365` | 3,421 | 5 |
| `FH69-50S-0.5SH` | `J1` | JLC library, no public LCSC code | **1,072** | 5 |
| **`0466005.NRHF`** Littelfuse | `F1` | **`C57525`** | **29,328** | 5 |
| **`BAT54WS-7-F`** Diodes Incorporated | `D10`–`D12` | **`C124205`** | **46,819** | **15** |

**`F1` and `D10`–`D12` moved into class B at FBV2-MECH-002.** Both substitutions were CTO-approved,
verified live under D-096 and adopted: `F1` → **`0466005.NRHF`** (`C57525`, the halogen-free ordering
option of the same Littelfuse 466 / Nano2 5 A 32 V 1206 fuse, same footprint, same electrical function)
and `D10`–`D12` → **`BAT54WS-7-F`** (`C124205`, single independent 30 V / 100 mA / 600 mA-surge SOD-323
Schottky — the topology the design actually uses). **Both are JLC EXTENDED, in stock, machine-placed.
Neither needs consignment. Class D is now EMPTY.**

**`J1` moved.** FBV2-S2-001 recorded the display connector as manual assembly. That ruling came
from **B-47** — there is no drop-in second source — but it does not follow that JLC cannot place
it. **JLC carries the genuine Hirose `FH69-50S-0.5SH` with 1,072 in stock.** `J1` is
**machine-placed**, and the single-source risk stays exactly what D-194 says it is.

**D-764 corrects a category error that survived D-763:** catalog availability does not turn a
through-hole part into an SMT placement. `U6`, `J4` and `J6` were still listed in Class B even
though Class E requires manual work after reflow. **D-781 further changes J4 itself:** no JST-PH
board header is fitted. The existing J4 PTH pair is a manual 26-AWG pigtail land feeding a
2-circuit Molex Micro-Lock Plus detachable harness. `J6` remains the genuine JST PH header
`C131337`; do not buy or install `C131337` at J4. The exact J4 wire/housing/terminal identities
and acceptance tests are frozen in `BATTERY_HARNESS.json`. Current `J5` is
`SSQ-124-02-G-S-RA / C3323671` and is Class E only.

---

## 4. Class C — in the library, but stock is short of the build

**These are the parts that decide whether this build succeeds.** Every one is bought from a
broadline distributor and **consigned to JLC**, so it stays machine-placed.

> ### **D-788 / R7-D787-19 — THE WHOLE TABLE IS RE-SWEPT LIVE, AND ONE ROW WAS THE WRONG PART.**
>
> The `U18` row read **`LTC4368IDD-1#PBF` / `C688397`**, which is the **DFN** part.
> The schematic, the released BOM and the PCB footprint all carry
> **`LTC4368IMS-1#TRPBF` / `C688401`**, which is the **MSOP-10**.  A consignment
> line that names a different package than the board is fitted for is a build
> stopper, and it had survived since the table was written.  **THE DFN ROW IS
> RETIRED.**
>
> Every row below is a **fresh live sweep of all 124 assembly lines** taken on
> **2026-09-20** through the D-096 JLCPCB parts API and archived under
> `hardware/demo/manufacturing/evidence/jlc-live/`.  Ten of the 124 lines do not
> cover a five-board build; those ten are the table.  **Archived counts are not
> purchasing authority — re-check immediately before the order.**

| part | ref | LCSC | live stock 2026-09-20 | need (5 boards) | shortfall | JLCPCB catalogue flag |
|---|---|---|---|---|---|---|
| **`74438357010`** Wurth Elektronik | `L4` | `C5542269` | **0** | 5 | **-5** | — |
| **`LQW18AN39NG80D`** Murata Electronics | `L5,L6` | `C2042966` | **3** | 10 | **-7** | — |
| **`DMM-4026-B-I2S-R`** JLCPCB Assembly | `MK1` | `C3171792` | **0** | 5 | **-5** | This product is no longer manufactured. |
| **`SQ2364EES-T1_BE3`** Vishay Intertech | `Q11` | `C5758702` | **0** | 5 | **-5** | — |
| **`NTMD4820NR2G`** onsemi | `Q2,Q3` | `C905372` | **0** | 10 | **-10** | This product is no longer manufactured. |
| **`LTC4368IMS-1#TRPBF`** Analog Devices | `U18` | `C688401` | **2** | 5 | **-3** | — |
| **`TLV7032DDFR`** Texas Instruments | `U19` | `C2871498` | **0** | 5 | **-5** | — |
| **`PCAL9535APW,118`** NXP Semicon | `U2,U3` | `C2669683` | **1** | 10 | **-9** | — |
| **`ST25R3916-AQET`** STMicroelectronics | `U9` | `C5267441` | **0** | 5 | **-5** | — |

> **`J5` `SSQ-124-02-G-S-RA` is ALSO a consignment line and is deliberately NOT
> in this table.**  It is a leaded through-hole part and belongs to **Class E,
> manual by construction**; listing it in a machine-placement class would send
> the assembler the wrong work instruction, which is exactly what `FAB15`
> refuses.  Its live stock, its shortfall and its catalogue flag are in the
> complete sweep at **§7b**.

**`U2`/`U3` is the headline.** Demo removed `U23`; there are **two PCAL9535A per board, ten TSSOP-24 at 0.65 mm pitch** for the first five, against **one** in the archived stock snapshot. That is precisely the case the CTO ruling
names: *"if the result would require manually installing dozens of fine-pitch parts per board,
that is NOT acceptable."* **It does not, because consignment exists.** Ten plus spares from
Digi-Key/Mouser, shipped to JLC with the order, machine-placed.

**`U9` is the one that genuinely could not be hand-built.** A UFQFPN-32 5 × 5 with an exposed pad
is not a hand-placement candidate at any skill level without a stencil and reflow. Six in stock
against a need of five is a build with **one** spare; **buy spares independently and consign.**

---

## 5. Class D — not in the LCSC/JLC library

## **CLASS D IS EMPTY as of FBV2-MECH-002.**

| part | ref | finding | plan |
|---|---|---|---|
| ~~**`BAT54WS,115`** Nexperia~~ | ~~`D10`–`D12`~~ | **RESOLVED 2026-08-23 (D-211).** The Nexperia string is not in the LCSC/JLC library, and it does not need to be: **`D10`, `D11` and `D12` are each ONE independent SOD-323 Schottky**, and **Diodes Incorporated `BAT54WS-7-F`, `C124205`, 46,819 in stock** is exactly that part. **ADOPTED after CTO sign-off** — verified electrically against the ratiometric bridge and the dead-cell recovery branch (audit §2.4, §2.5) | **Class B. JLC-sourced, machine-placed, no consignment** |

---

## 6. Class E — manual by construction

> **CORRECTED AT D-763.  THIS TABLE LISTED TWO PARTS AND THE BOARD HAS FIVE**,
> and it still named the `J5` part number D-738 superseded.  Counted from the
> board: five footprints carry plated through-hole **leads** — `J4`, `J5`, `J6`,
> `D1`, `U6`.  Three of the five need a specified hand operation beyond
> soldering, and **one of those is why this table matters**: `J4`'s leads land
> inside `DISPLAY_SHADOW` and must be trimmed or the display will not seat.

| part | ref | through-hole work | why |
|---|---|---|---|
| **`SSQ-124-02-G-S-RA` Samtec** (`C3323671`; ***~~`BCS-112-S-D-HE`~~ SUPERSEDED D-237/D-240, corrected D-750***) | `J5` | **24 × Ø1.02 mm PTH** | 1 × 24 right-angle community header. **Hand-solder after reflow.** The current board land is 1.60 mm pad / **1.02 mm drill** at 2.54 mm pitch; the old 0.71 mm figure belonged to the superseded BCS footprint. RA tail `(2.54) .100 in` |
| `TSAL6100` | `D1` | 2 leads | 5 mm through-hole IR emitter, `C111836`. **LEAD-FORMED 90° AND TRIMMED — [`IR_LEAD_FORMING.md`](IR_LEAD_FORMING.md), NORMATIVE** |
| `TSOP38238` (`C141632`) | `U6` | 3 leads | minicast IR receiver. **Hand-solder after reflow; LEAD-FORMED 90° AND TRIMMED — [`IR_LEAD_FORMING.md`](IR_LEAD_FORMING.md), NORMATIVE.** Was incorrectly also listed as machine-placed Class B until D-764 |
| **D-781/D-782 manual battery pigtail** — 26-AWG Molex pre-crimps `2175012101` red / `2175011101` black into housing `5055700201`; **no PCB header fitted** | **`J4`** | 2 conductors through the existing 0.75 mm nominal PTH pair, wires enter from **REAR**, solder on **FRONT** | Exact detachable harness is [`BATTERY_HARNESS.json`](BATTERY_HARNESS.json). Supplier/assembler must guarantee **≥0.70 mm finished plated-hole diameter** and prove one exact tinned lead passes freely before all five boards — no strand shaving. Cavity 1 = BAT+ / red / `J4.1`; cavity 2 = GND / black / `J4.2`. **J4-T1/T2/T3/T4 are NORMATIVE**: front conductive profile **≤0.50 mm**, both inspected joints covered with **≤0.10 mm polyimide**. Rear strain relief is now frozen to **DOWSIL 3145 RTV MIL-A-46146 gray**, applied to the insulated pigtail after joint inspection with the specified service loop; disconnect Micro-Lock by the housings only, never by pulling wires. DMM-check polarity and complete the first-article fit/pull/thermal acceptance tests. **Do not install JST `C131337` at J4.** |
| `B2B-PH-K-S(LF)(SN)` JST PH (`C131337`) | `J6` | 2 leads | SPEAKER connector, body on `F.Cu`; its leads emerge on the rear **3.5 mm clear of `BATTERY_SHADOW`**, so no trim requirement. Was missing from this table |
| **D-788 ACC_3V3_SW REINFORCEMENT LEAD** — ONE Alpha Wire `2842/19 RD005` 28 AWG PTFE conductor, `TP12.1` → `J5.3`, plus three DOWSIL 3145 anchor beads | `TP12` / `J5.3` | 1 conductor, 2 hand joints | **MISSING FROM THIS TABLE ENTIRELY UNTIL D-788 / R7-D787-11.**  D-787 introduced a manual accessory-voltage reinforcement and neither the master assembly plan nor the off-board BOM knew about it, so the operation was not in the sequence, the wire was not in purchasing and the completion record had no line for it.  The exact dimensioned route, waypoints, bend radius, anchor locations, bead size, cure time, joint profile and per-step inspection are NORMATIVE in [`ACC_3V3_REINFORCEMENT.json`](ACC_3V3_REINFORCEMENT.json).  **D-788 also removed the second conductor**: J5.22 is delivered by routed copper alone (79.0 mΩ measured), so only `J5.3` is reinforced and no pad carries two conductors.  Finished lead **≤ 25 mΩ**, value recorded per board.  **Sequence: after reflow and AOI, before enclosure close; full cure 72 h before any pull, thermal test or shipment.** |

**FIVE through-hole references per board require manual post-reflow work: `J4`, `J5`, `J6`, `D1`, `U6`, and D-788 adds ONE non-reference manual operation: the `TP12.1` → `J5.3` accessory-voltage reinforcement lead.** `J4` is a wire pigtail rather than a fitted connector. `J4`, `D1` and `U6` have NORMATIVE trim/forming requirements, and D-782 additionally freezes J4 rear strain relief using DOWSIL 3145 plus the Micro-Lock service-loop/housing-only disconnect rules in `BATTERY_HARNESS.json`.

**Also PTH but not a lead:** `J3`'s four `SH` shell stakes (GCT USB4105 is a
top-mount SMT receptacle — the stakes are mechanical anchors, pin-in-paste or
selective solder at the assembler's choice), `U1`'s pad-41 thermal vias inside
its own thermal land, and the NPTH features `BOSS1`, `BOSS2`, `SW9`'s two
locating pegs and `MK1`'s acoustic port.  **None of these passes a lead through
the board**, which is a positive declaration in `MK10`'s table, not an
omission.

---

## 7. Class F — off-board

Speaker `LS1` (`AS02008MR-LW152-R`, `C3311653`, stock 0 — consign or buy direct), display module, **Adafruit Product 328 2500 mAh protected battery (CTO-BAT-01)**, both antennas, the locked **RF Solutions `CBA-UFLSMA20IP` 200 mm U.FL/MHF1-to-SMA(F) bulkhead pigtail**, and the Taoglas `TI.92.2113` 915 MHz whip. All in [`OFF_BOARD_BOM.md`](OFF_BOARD_BOM.md). The battery is an exact first-five supplier SKU now; do not replace it by a generic `LP785060` family-name match because published current ratings vary by sold variant.

---

## 7b. D-788 — the complete live sourcing sweep and consignment plan

**Every one of the 124 assembly lines was re-queried through the D-096 JLCPCB
parts API on 2026-09-20** and archived at
`hardware/demo/manufacturing/evidence/d788-sourcing-sweep.json`, so the plan
REPLAYS rather than re-queries.  **Ten lines do not cover a five-board build.**
Nine of them are machine-placed and are in §4; `J5` is the tenth and is Class E.

| part | ref | LCSC | live stock 2026-09-20 | need (5 boards) | shortfall | JLCPCB catalogue flag | placement |
|---|---|---|---|---|---|---|---|
| **`SSQ-124-02-G-S-RA`** Samtec | `J5` | `C3323671` | **0** | 5 | **-5** | This product is no longer manufactured. Class E, manual |
| **`74438357010`** Wurth Elektronik | `L4` | `C5542269` | **0** | 5 | **-5** | — machine, consigned |
| **`LQW18AN39NG80D`** Murata Electronics | `L5,L6` | `C2042966` | **3** | 10 | **-7** | — machine, consigned |
| **`DMM-4026-B-I2S-R`** JLCPCB Assembly | `MK1` | `C3171792` | **0** | 5 | **-5** | This product is no longer manufactured. machine, consigned |
| **`SQ2364EES-T1_BE3`** Vishay Intertech | `Q11` | `C5758702` | **0** | 5 | **-5** | — machine, consigned |
| **`NTMD4820NR2G`** onsemi | `Q2,Q3` | `C905372` | **0** | 10 | **-10** | This product is no longer manufactured. machine, consigned |
| **`LTC4368IMS-1#TRPBF`** Analog Devices | `U18` | `C688401` | **2** | 5 | **-3** | — machine, consigned |
| **`TLV7032DDFR`** Texas Instruments | `U19` | `C2871498` | **0** | 5 | **-5** | — machine, consigned |
| **`PCAL9535APW,118`** NXP Semicon | `U2,U3` | `C2669683` | **1** | 10 | **-9** | — machine, consigned |
| **`ST25R3916-AQET`** STMicroelectronics | `U9` | `C5267441` | **0** | 5 | **-5** | — machine, consigned |

**`D8` `NSR0240HT1G` is no longer on this list** — it re-swept at **5 280** in
stock against a need of 5.

**THE THREE "NO LONGER MANUFACTURED" FLAGS ARE JLCPCB CATALOGUE FLAGS, NOT
MANUFACTURER EOL.**  Samtec still catalogues `SSQ-124-02-G-S-RA`, PUI still
catalogues `DMM-4026-B-I2S-R` and onsemi still catalogues `NTMD4820NR2G`.  What
the flag means is that **JLCPCB will not source them for you**.  **Before PCBA
payment** each must be confirmed ACTIVE against the MANUFACTURER's own lifecycle
page and ordered from a franchised distributor.  A part that turns out to be
genuinely EOL is an escalation, not a substitution.

**NO SUBSTITUTION WITHOUT REQUALIFICATION.**  Each of these ten is a safety
part, an RF part, or a part whose exact identity a gate in this repository
binds — `F5` for `Q11`, `F8` for the capacitor population, `RF1`–`RF5` for
`L5`/`L6`, `F6` for the limiter switches, `firmware_hw_map_contract` for
`U2`/`U3`.  An electrically or mechanically different part invalidates the
clause that qualified it.

**Archived counts are not purchasing authority.  Re-check immediately before the
order.**

---

## 7a. D-780 Q11 first-five temperature acceptance — `Q11-TEMP-01`

`Q11` is now Vishay **SQ2364EES-T1_BE3**. Its 60 V rating covers the board's 39 V open-LED fault ceiling, and its published **0.245 Ω MAX at VGS = 1.5 V, ID = 2 A** gives a direct low-gate conduction point below AQROOT's held **VGS = 2.396 V**. The vendor electrical-characteristics table states **TC = 25 °C unless otherwise noted**, so that 1.5 V row is not being misrepresented as an all-temperature guarantee. For these five Kickstarter prototypes this is a **reworkable first-article qualification item, not a production-temperature claim**.

Before a first-five unit is accepted for Demo use, validate the backlight at **0 °C, 25 °C and 40 °C** after thermal soak: full-on, the normal firmware PWM range, commanded OFF for at least 30 s, and repeated ON→OFF→ON transitions. **D-784 startup rule:** from a discharged `C85`, firmware must first drive `DISP_BL_CTL` at **100% duty for at least 2 ms** before entering low-duty PWM; the released bring-up firmware uses a **3.0 ms microsecond-timed prime** to guarantee margin rather than relying on an Arduino millisecond tick delay. Do not start directly at 1% duty. Scope `DISP_BL_CTL`, **Q11 VGS**, `LED_BOOST`, Q11 VDS and LED current during startup/OFF/restart. Acceptance: no visible dropout/flicker at full-on or normal PWM, no TPS61169 open-LED latch during normal operation, commanded OFF remains dark, and restart is repeatable. Record the unit ID and result. The TPS61169 primary datasheet is archived at `hardware/demo/kicad/aqroot-demo/vendor/TI/tps61169.pdf` (SHA-256 `7d0b8ace2459a9fd22fe7145086cbad4ccb3bb43219247459313fcba75230151`). A failure blocks that unit and requires `Q11`/gate-drive rework before Demo use; it does **not** authorize widening the temperature claim.

The release gate must preserve this exact acceptance marker (`Q11-TEMP-01`) while the fitted Q11 relies on the 25 °C low-gate `RDS(on)` row.

---

## 7b. D-788 / R7-N02 `+3V3` transient acceptance — `C-PWR-TRANSIENT-01`

**THE PANEL'S 3.3 V IS AN ABSOLUTE MAXIMUM AND A SWITCHING RAIL IS NOT ONLY DC.**
`demo_feature_contract` F6 proves the `+3V3` DC regulation envelope
(**3.100334 / 3.145503 / 3.191022 V** raw PWM, **3.069405 V** heavy-load minimum,
**3.223016 V** worst case) sits inside the fitted ILI9488's **3.3 V** absolute
maximum and above the ESP32-S3-WROOM-1's own **3.0 V** `VDD33` minimum, and it
computes the **output ripple** from `SLVS916I`'s published minimum oscillator
frequency, `L1`'s own minimum inductance and the declared effective local output
capacitance.  It does **not** claim an analytic bound on **load-transient
overshoot**: TI publishes the TPS6302x load transient only as `SLVS916I`
Figures 21/22 (**50 mV/div**, 500 mA → 1500 mA, on the fixed-output TPS63021
with 4 × 22 µF), and there is no numeric overshoot row in the electrical
characteristics table.  Reading a limit off a plot axis is not primary evidence,
so the real excursion is **MEASURED HERE**.

Before a first-five unit is accepted for Demo use, scope `+3V3` **at the
display's own supply pins** — `J1.40`/`J1.41` (`VDDI`/`IOVCC`) and `J1.42`
(`VCI`) — AC-coupled, ≥ 20 MHz bandwidth, ground-spring probe at the connector,
through all of:

- **accessory step**: `ACC_3V3_SW` enabled into a 400 mA load and then **hot
  disconnected** at the J5 mating interface, ten times;
- **backlight step**: `U17` commanded full-on → off → full-on, including the
  D-784 3.0 ms full-duty prime;
- **radio step**: Wi-Fi TX bursts with `U7`/`U8` idle, and the worse sub-GHz
  radio transmitting;
- **enable step**: `SW9` off → on from a discharged `+3V3`, watching `U12`
  start-up overshoot;
- each of the above at pack voltages spanning **buck, buck-boost and boost**
  operation (`≈4.15 V`, `≈3.20 V`, `≈3.05 V` at `BAT_PROTECTED_P`).

**ACCEPTANCE:** the absolute peak at `J1.40`/`J1.41`/`J1.42` must stay **below
3.300 V** with no exception, and the absolute trough at `U1.2` must stay **above
3.000 V**.  Record the peak, the trough and the unit ID.  A failure blocks that
unit; **the designed lever is `C29`–`C32`**, which are 22 µF 1206 X7R parts on
existing lands — `SLVS916I` 8.2.2.3 sets **no upper limit** on output
capacitance, so more capacitance is a **BOM value change with no PCB change**.
Do not widen the acceptance instead.

**WHY THE DIVIDER IS WHERE IT IS.**  The window between the MCU's 3.0 V floor
and the panel's 3.3 V absolute maximum is 300 mV and the rail's own tolerance
band needs ~154 mV of it, so the setpoint decides how the remainder is split.
F6 enumerates every purchasable E192 0.1 % value for `R40` with `R39` at 1 MΩ
and requires the fitted one to **maximise the smaller of the two headrooms** —
`189 kΩ` splits it **76.98 mV** under the damage limit against **69.41 mV** over
the recoverable one.  `187 kΩ` (the first D-788 draft) would have left
**47.97 mV / 96.99 mV**, and `191 kΩ` **105.36 mV / 42.46 mV**; both are refused
by that clause.  The release gate must preserve this exact acceptance marker
(`C-PWR-TRANSIENT-01`).

---

## 8. Six substitution traps found while building this table

**A loose keyword search against the JLC library returns a plausible wrong part more often than it
returns nothing.** Every one of these would have shipped silently.

| ref | intended | what a loose search returns | why it is wrong |
|---|---|---|---|
| `D10`–`D12` | ~~Nexperia `BAT54WS,115`~~ → **Diodes Inc `BAT54WS-7-F`** (D-211) | Nexperia **`BAT54W,115`** `C8657` | **CORRECTED 2026-08-23.** Both are *single independent* diodes — **`BAT54WS` is NOT a series pair**. `BAT54W,115` is wrong because it is **SOT-323 (SC-70)**, a **footprint mismatch** against `Diode_SMD:D_SOD-323`, and it has **5 in stock** against a need of 15 |
| `SW1`–`SW7` | C&K `PTS645SM43SMTR92LFS` | G-Switch **`GT-TC089A-H043-L1`** `C843623` | **Different manufacturer**, land pattern never checked against the C&K G-Type layout this footprint was built from — and it is **35 placements** |
| `D8` | onsemi `NSR0240HT1G` | FUXINSEMI **`SD103AWS`** `C915626` | **Different part number entirely** |
| `Q4`, `Q6`–`Q9` | onsemi `BSS138LT1G` | LRC **`LBSS138LT1G`** `C8490` | Different manufacturer — **and the genuine onsemi part has 762,522 in stock**, so there is no reason to accept it |
| `L2`, `L4` | Würth `74438357010` | KOHERelec **`SPM4030-1R0M`** `C2761910` | Different manufacturer's inductor in a switching regulator |
| `Q2`, `Q3` | onsemi `NTMD4820NR2G` | VBsemi **`NTMD4820NR2G-VB`** `C7525084` | Clone in the **battery reverse-polarity pass path**. The CTO ruling forbids silent substitution of power-path parts |

**Each of these is now recorded in the schematic symbol itself**, so the warning travels with the
design instead of living only in this file.

---

## 9. Two MPN strings were wrong in a way that mattered

Both were found by cross-checking the BOM against live listings rather than by reading the
schematic.

- **SUPERSEDED AT D-781:** J4 and J6 once shared the JST PH header footprint/identity, but only
  **J6** now receives `B2B-PH-K-S(LF)(SN)` / `C131337`. **J4 receives no PCB header**; it is the
  manual 26-AWG Micro-Lock pigtail land defined by `BATTERY_HARNESS.json`. A BOM or work order
  that assigns `C131337` to J4 is now a release defect and is refused by the fabrication gate.
- **`J7` had the same problem.** `BM02B-ACHSS-GAN-ETF` → `C20088622`, **stock 0**;
  **`BM02B-ACHSS-GAN-ETF(LF)(SN)` → `C5118738`, 16,260 in stock.** Corrected.

A BOM that produces two lines for one part, one of which cannot be filled, is a BOM that stalls at
the quote stage. **`L2`/`L4` also carried two spellings of "Würth"** and were normalised.

---

## 10. The assembly reality check

| question | answer |
|---|---|
| how many distinct MPNs? | **46** (43 after the two duplicate-string merges and one manufacturer-spelling merge) |
| how many parts machine-placed? | **all fitted SMT parts; Class E covers five manual references (`J4`,`J5`,`J6`,`D1`,`U6`)** |
| how many manual solder operations per board? | **5** — `J4`, `J5`, `J6`, `D1`, `U6`; J4 is a wire pigtail land, while the other four are fitted THT parts; `J4`/`D1`/`U6` also have normative trim/forming instructions |
| how many fine-pitch/QFN parts hand-placed? | **zero** |
| how many part identities need consignment? | **TEN, from the D-788 live sweep of all 124 assembly lines on 2026-09-20**: `SSQ-124-02-G-S-RA` (`J5`), `74438357010` (`L4`), `LQW18AN39NG80D` (`L5`/`L6`), `DMM-4026-B-I2S-R` (`MK1`), `SQ2364EES-T1_BE3` (`Q11`), `NTMD4820NR2G` (`Q2`/`Q3`), **`LTC4368IMS-1#TRPBF` MSOP-10 `C688401`** (`U18` — *the `LTC4368IDD-1#PBF` DFN row this line carried until D-788 was the WRONG PACKAGE and is RETIRED*), `TLV7032DDFR` (`U19`), `PCAL9535APW,118` (`U2`/`U3`), `ST25R3916-AQET` (`U9`) + 0 class D. **`NSR0240HT1G` (`D8`) is NO LONGER on this list** — it re-swept at 5 280 in stock against a need of 5. **Re-check all stock immediately before order; any additional exact-source item whose live stock no longer covers first-five need also moves to consignment. Archived counts are not purchasing authority.** |
| DNP parts with no recorded reason | **zero** — eight were still undocumented at the start of FBV2-S2-002 and all eight now carry one |
| does the build close today? | **Yes, via consignment.** It does **not** close as a pure LCSC turnkey order |

**Do not optimise cents. Optimise first-build success.** Consignment cost is trivial against one failed board or one wrong-part respin; the exact count must be recomputed from live stock at order time rather than inherited from this archived snapshot.

---

## 11. What this plan does **not** claim

- It does **not** claim any of these stock figures will still hold when the order is placed.
- ~~It does **not** adopt a single substitute part.~~ **SUPERSEDED 2026-08-23 (FBV2-MECH-002).**
  **`BAT54WS-7-F` (`C124205`) and `0466005.NRHF` (`C57525`) are now CTO-APPROVED, ELECTRICALLY
  VERIFIED AND ADOPTED** — D-211 and D-210. They are the only two substitutions this programme has
  adopted, and no other substitution is authorised.
- It does **not** cover the anonymous passive values, which stay unconsolidated until the layout
  exists.
