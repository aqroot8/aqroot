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
| `TPD4E1B06DRLR` | `D2`, `D4`, `D5` — **not `D3`, which is DNP** (D-790 / D789-A07 corrected this row: it read `D2`–`D5` and over-counted the need by five pieces) | `C1972953` | 2,176 | 15 |
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
> Every row below is a **fresh live sweep of all 123 assembly lines** taken on
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
| ~~**`NTMD4820NR2G`** onsemi~~ → **`AO4800`** Alpha & Omega Semiconductor | `Q2,Q3` | ~~`C905372`~~ → `C17098` | ~~**0**~~ → **5 347** | 10 | **+5 337** | **RETIRED at D-790 / D789-A01** for an electrical reason as well as a stock one; the AOS line covers the need |
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
| **D-789 RETIRES THE ACC_3V3_SW REINFORCEMENT LEAD** — there is NO manual accessory-voltage conductor on this board | *(none)* | **0 conductors, 0 hand joints** | **D-789 / D788-07 + D788-08 + D788-09 + D788-16.**  D-787 introduced a manual accessory-voltage reinforcement; D-788 reduced it to ONE dimensioned `TP12.1` → `J5.3` lead.  Round-8 raised four independent findings against that lead and every one is a property of the conductor rather than of its description: a tinned tip that cannot fit a 1.00 mm pad; an insertion into a through-hole already filled by J5's 0.635 mm square tail (0.898 mm diagonal in a 1.02 mm drill); a route starting inside `BATTERY_SHADOW` and crossing `RIB_R3` against the record's own 1.0 mm clearances; and a ≤ 25 mΩ acceptance that cannot be measured because the board's own copper stays in parallel with it.  **It bought 70 mV of published minimum on ONE of two duplicated contacts and it is gone.**  `TP12`/`TP25` remain as test points; **nothing is soldered to them.**  The Community Port now publishes **≥ 2.84 V unconditionally** and **2.982890 V fully mated** at the full 400 mA — see [`ACC_3V3_REINFORCEMENT.json`](ACC_3V3_REINFORCEMENT.json).  A dedicated accessory regulator is the REV-B fix the owner already approved deferring. |

**FIVE through-hole references per board require manual post-reflow work: `J4`, `J5`, `J6`, `D1`, `U6`.  D-789 removes the one non-reference manual operation D-788 had added** — the `TP12.1` → `J5.3` accessory-voltage reinforcement lead (D788-07/08/09/16) — **so the manual work per board is back to the five references and nothing else.** `J4` is a wire pigtail rather than a fitted connector. `J4`, `D1` and `U6` have NORMATIVE trim/forming requirements, and D-782 additionally freezes J4 rear strain relief using DOWSIL 3145 plus the Micro-Lock service-loop/housing-only disconnect rules in `BATTERY_HARNESS.json`.

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

## 7c. D-789 — the complete live sourcing sweep and consignment plan

*(This section was numbered `7b` through D-788, which collided with the
transient-acceptance section below — `R8-N04`, corrected here.)*

**Every one of the 123 assembly lines was re-queried through the D-096 JLCPCB
parts API on 2026-09-21** and archived at
`hardware/demo/manufacturing/evidence/d789-sourcing-sweep.json`, so the plan
REPLAYS rather than re-queries.  **It was 124 lines through D-788**; `D14`'s
`1N4148WS` line disappeared at D-789 when `D14` became the `BAT54WS-7-F` that
`D10`/`D11`/`D12` already carry (D788-11), so that line is now one row of
quantity four.  The ten short lines are unchanged.

> **`Q2`/`Q3` WAS A PRE-PCBA BLOCK AND D-790 CLOSED IT.**  The RETIRED
> `NTMD4820NR2G` read stock 0 and was flagged no longer manufactured (F-N01),
> **and** `R8-N01` found that it was not guaranteed to be ENHANCED at this
> board's `BAT_RAW`: the `LTC4368` guarantees 3.0 V of gate drive and that
> FET's `VGS(th)` MAXIMUM is 3.0 V, with no published `RDS(on)` row below
> `VGS` = 4.5 V.  **D-790 / D789-A01 re-selects the pair to Alpha & Omega
> `AO4800` (`C17098`)** — same SOIC-8 land, same pin function map, `VGS(th)`
> MAX **1.5 V** and a published `RDS(on)` MAX of **50 mΩ AT `VGS` = 2.5 V` —
> and `demo_feature_contract` **F10** now PROVES the four-channel model
> instead of holding it.  The paragraph below is the D-789 selection brief
> that led to it and is retained as the record of how the part was chosen.
> The eight selection requirements for the
> replacement and first-article **`C-BAT-GATE-01`** are in
> [`SOURCING_LEDGER.md`](SOURCING_LEDGER.md), and `demo_feature_contract` F10
> refuses a ledger that drops them.  **Do not pay for PCBA until this line is
> resolved.  No substitution without requalification.**  **Ten lines do not cover a five-board build.**
Nine of them are machine-placed and are in §4; `J5` is the tenth and is Class E.

| part | ref | LCSC | live stock 2026-09-20 | need (5 boards) | shortfall | JLCPCB catalogue flag | placement |
|---|---|---|---|---|---|---|---|
| **`SSQ-124-02-G-S-RA`** Samtec | `J5` | `C3323671` | **0** | 5 | **-5** | This product is no longer manufactured. Class E, manual |
| **`74438357010`** Wurth Elektronik | `L4` | `C5542269` | **0** | 5 | **-5** | — machine, consigned |
| **`LQW18AN39NG80D`** Murata Electronics | `L5,L6` | `C2042966` | **3** | 10 | **-7** | — machine, consigned |
| **`DMM-4026-B-I2S-R`** JLCPCB Assembly | `MK1` | `C3171792` | **0** | 5 | **-5** | This product is no longer manufactured. machine, consigned |
| **`SQ2364EES-T1_BE3`** Vishay Intertech | `Q11` | `C5758702` | **0** | 5 | **-5** | — machine, consigned |
| **`AO4800`** Alpha & Omega Semiconductor | `Q2,Q3` | `C17098` | **5 347** | 10 | **+5 337** | **RE-SELECTED at D-790 / D789-A01**, superseding the RETIRED `NTMD4820NR2G` / `C905372` which read 0 stock AND published no conduction row at the gate drive this circuit has.  Stock covers the need, so this line is carried for **authorised-allocation** confirmation only.  machine |
| **`LTC4368IMS-1#TRPBF`** Analog Devices | `U18` | `C688401` | **2** | 5 | **-3** | — machine, consigned |
| **`TLV7032DDFR`** Texas Instruments | `U19` | `C2871498` | **0** | 5 | **-5** | — machine, consigned |
| **`PCAL9535APW,118`** NXP Semicon | `U2,U3` | `C2669683` | **1** | 10 | **-9** | — machine, consigned |
| **`ST25R3916-AQET`** STMicroelectronics | `U9` | `C5267441` | **0** | 5 | **-5** | — machine, consigned |

**`D8` `NSR0240HT1G` is no longer on this list** — it re-swept at **5 280** in
stock against a need of 5.

**THE "NO LONGER MANUFACTURED" FLAGS ARE JLCPCB CATALOGUE FLAGS, NOT
MANUFACTURER EOL — AND THERE ARE TWO OF THEM NOW, NOT THREE.**  Samtec still
catalogues `SSQ-124-02-G-S-RA` and PUI still catalogues `DMM-4026-B-I2S-R`.
*(D-790 / Fable `D-01`: this sentence also read "and onsemi still catalogues
`NTMD4820NR2G`", which Fable reported as stale against onsemi's own page —
Round-8 found it flagged **Obsolete** there.  The point is moot: D-790 /
D789-A01 retired that part for an ELECTRICAL reason and the line is now
`AO4800`.)*  What the flag means is that **JLCPCB will not source them for
you**.  **Before PCBA
payment** each must be confirmed ACTIVE against the MANUFACTURER's own lifecycle
page and ordered from a franchised distributor.  A part that turns out to be
genuinely EOL is an escalation, not a substitution.

**NO SUBSTITUTION WITHOUT REQUALIFICATION.**  Each of these ten is a safety
part, an RF part, or a part whose exact identity a gate in this repository
binds — `F5` for `Q11`, **`F10` for `Q2`/`Q3`**, `F8` for the capacitor
population, `RF1`–`RF5` for `L5`/`L6`, `F6` for the limiter switches,
`firmware_hw_map_contract` for `U2`/`U3`.  **The `AO4800` line in particular
may NOT be filled from the VBsemi, HXY, UMW, JSMSEMI, MSKSEMI or TECH PUBLIC
rows that carry the same marking**: those are re-marked second sources and
these are the battery path's pass FETs.  An electrically or mechanically different part invalidates the
clause that qualified it.

**Archived counts are not purchasing authority.  Re-check immediately before the
order.**

---

## 7a. D-780 Q11 first-five temperature acceptance — `Q11-TEMP-01`

`Q11` is now Vishay **SQ2364EES-T1_BE3**. Its 60 V rating covers the board's 39 V open-LED fault ceiling, and its published **0.245 Ω MAX at VGS = 1.5 V, ID = 2 A** gives a direct low-gate conduction point below AQROOT's held **VGS = 1.945526 V**. *(D-790 / D789-A08: 1.945526 V / 445.5 mV at the TPS61169's 220 mV feedback MAXIMUM; 1.961526 V used its 204 mV typical.)*

> **D-789 / D788-11 + `R8-N03` CORRECTED THE NUMBER IN THAT SENTENCE, AND THE PART THAT SETS IT.**  This section carried **2.396 V**, which was derived against the 3.3 V rail D-788 retired to keep the ILI9488 panel inside its own absolute maximum — the same hand-carried-constant failure Round-8 raised as D788-11, surviving in a second document.  The held gate is now **DERIVED** by `demo_feature_contract` F5 as `VOH(MIN) − VF(D14)` at the rail's own heavy-load minimum: `0.8 × 3.069408 V = 2.455526 V` less the diode's lowest published forward maximum plus a declared 2 mV/K cold-endpoint allowance.  **With the old `1N4148WS` that lands at `VGS` = 1.486526 V — 13.5 mV BELOW the 1.5 V conduction row above, with no lower row to bound it — so `D14` is now a `BAT54WS-7-F`** (`VF` ≤ 240 mV at `IF` = 0.1 mA, below the ~9 µA this node draws and monotone in `IF`, so it is a guaranteed bound), giving **1.945526 V — 445.5 mV inside** the published region.  *(D-790 / D789-A08 moved this 16 mV: `Q11`'s SOURCE is the TPS61169's own feedback node, so the bound is that reference's published **MAXIMUM** of 220 mV, not the 204 mV TYPICAL every derivation from D-752 to D-789 used.  A higher feedback voltage makes `VGS` smaller, so the typical was a limit in the direction that flattered the answer.  D-789 published 1.961526 V / 461.5 mV.)*  It is the same MPN, LCSC code and SOD-323 land this board already fits at `D10`/`D11`/`D12`: **no new part, no new feeder, no copper, no assembly-step change.**  The acceptance below is unchanged and still runs at 0 / 25 / 40 °C. The vendor electrical-characteristics table states **TC = 25 °C unless otherwise noted**, so that 1.5 V row is not being misrepresented as an all-temperature guarantee. For these five Kickstarter prototypes this is a **reworkable first-article qualification item, not a production-temperature claim**.

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

**D-789 / D788-18 REWROTE HOW IT IS MEASURED AND WHERE THE STEPS ARE RUN.**
Round-8 raised two defects in the D-788 procedure and both are real: an
**AC-coupled** acquisition cannot prove an **absolute** limit, because it
discards exactly the DC term the 3.300 V and 3.000 V thresholds are stated
against; and the accessory step was written to run at **3.20 V and 3.05 V** of
pack voltage, where a release image **refuses to enable an accessory rail at
all** (the derived VCELL policy refuses a FIRST accessory rail below
**3.55 V** and a SECOND below **3.65 V**).
Half the matrix was therefore unexecutable and the other half could not
support its own acceptance.

> **D-791 / `R10-N04` RE-BASED THIS SECTION ONTO THE THIRD FLOOR, AND IT IS THE
> SECOND TIME THIS PROCEDURE HAS GONE STALE THE SAME WAY.**  The sentence above
> named the now-RETIRED **3.50 V single-rail / 3.85 V dual-rail** pair, and the
> accessory step below chose its bench voltages from it.
> D-791 / `D790-A03` retired that pair because:
> the node could not hold 3.85 V at the published load, so the floors are now
> DERIVED by `demo_feature_contract` **F12** as a **triple** —
> **3.20 V retention**, **3.55 V** to enable a first rail and **3.65 V** to
> enable a second — and D-790's pair is REPLACED.  A stale floor here is worse
> than a stale sentence in a specification, because this text tells a technician
> which pack voltage to set: the old points were chosen to sit above floors that
> no longer exist.  **F12 now reads this file**, requires all three derived
> floors to appear formatted from the computed values, and refuses any unfenced
> sentence that calls some other voltage a single-rail, dual-rail or retention
> floor — so the next move of the derivation cannot leave this procedure behind.

### How it is acquired

Scope `+3V3` **at the display's own supply pins** — `J1.40`/`J1.41`
(`VDDI`/`IOVCC`) and `J1.42` (`VCI`) — and `U1.2` for the trough, with a
ground-spring probe at the connector and **≥ 20 MHz** bandwidth, using
**either**:

- **(A) DC-COUPLED, preferred.**  DC coupling, vertical range and offset set so
  the whole excursion fits on screen at the finest volts/div that keeps it
  there.  Record the probe attenuation calibration and the instrument's own
  **DC gain accuracy** from its datasheet.
- **(B) SYNCHRONISED DC BASELINE + AC DETAIL**, only if (A) cannot resolve the
  transient.  Capture the DC level of the same node with a **calibrated DMM or
  a second DC-coupled channel on the same trigger**, capture the excursion
  AC-coupled at high gain, and **add them**.

**CHARGING THE UNCERTAINTY AGAINST THE MARGIN — D-790 / D789-A06 CORRECTS THE
SIGN OF THIS SENTENCE, WHICH WAS BACKWARDS AND WOULD HAVE PASSED FAILING
UNITS.**  D-788 wrote "the measured value MINUS the stated measurement
uncertainty on the high side and PLUS it on the low side", which *relieves*
the margin instead of charging it: a 3.310 V peak with ±0.020 V of uncertainty
would have been read as 3.290 V and ACCEPTED, and a 2.990 V trough as
3.010 V.  Both are over the limit.  The acceptance is:

> **`measured peak + total uncertainty < 3.300 V`**
> **`measured trough − total uncertainty > 3.000 V`**

The uncertainty always makes the reading WORSE, never better.  Worked
boundary examples, which `demo_feature_contract` `F11` re-derives from these
numbers on every run so this table cannot drift from the rule above:

| measured | total uncertainty | judged as | verdict |
|---|---|---|---|
| peak **3.310 V** | ±0.020 V | **3.330 V** | **REFUSED** — this is the D-788 example, and it used to pass |
| peak **3.290 V** | ±0.020 V | **3.310 V** | **REFUSED** |
| peak **3.275 V** | ±0.020 V | **3.295 V** | **ACCEPTED** |
| trough **2.990 V** | ±0.020 V | **2.970 V** | **REFUSED** — the other D-788 example |
| trough **3.010 V** | ±0.020 V | **2.990 V** | **REFUSED** |
| trough **3.025 V** | ±0.020 V | **3.005 V** | **ACCEPTED** |

Record the uncertainty budget — probe attenuation tolerance, vertical gain
accuracy, offset accuracy, and for (B) the DMM accuracy and the trigger skew —
with the reading.  A reading whose uncertainty is not recorded is not a result.

### The step matrix, split by what a release image permits

**INTERNAL-ONLY STEPS — run at pack voltages spanning buck, buck-boost and
boost operation (`≈4.15 V`, `≈3.20 V`, `≈3.05 V` at `BAT_PROTECTED_P`):**

- **backlight step**: `U17` commanded full-on → off → full-on, including the
  D-784 3.0 ms full-duty prime;
- **radio step**: Wi-Fi TX bursts with `U7`/`U8` idle, and the worse sub-GHz
  radio transmitting;
- **enable step**: `SW9` off → on from a discharged `+3V3`, watching `U12`
  start-up overshoot.

**ACCESSORY STEP — run ONLY where the released firmware actually permits the
rail**, because that is the only state a user can reach.  **THE PERMISSION AND
THE RETENTION ARE JUDGED AT DIFFERENT NUMBERS, AND THE STEP HAS TO SET BOTH.**
Firmware takes the ENABLE decision from what the gauge reads *before* the rail
is switched on, and then HOLDS the rail only while the *loaded* node stays above
the retention floor.  So bring the pack to a reading above the enable floor with
the rail still OFF, then enable `ACC_3V3_SW` into a 400 mA load and **hot
disconnect** it at the J5 mating interface, ten times, at

- **`≈4.15 V`** and **`≈3.75 V`** at `BAT_PROTECTED_P` read with the accessory
  rails OFF, the 5 V rail then ALSO brought up at its published 300 mA — both
  above the **3.65 V** dual-rail floor;
- **`≈3.60 V`** read with the accessory rails OFF, the 3.3 V rail alone — above
  the **3.55 V** single-rail floor and below the dual floor, so this point also
  confirms that the 5 V rail is refused there.

At every point the LOADED node must stay above the **3.20 V** retention floor.
A rail that is authorised and then sheds is a **FAILURE of this step**, not a
property of it: each enable floor is derived to anticipate its own rail's node
step — **0.3476 V** for the first rail and **0.4537 V** for the second — exactly
so that the load a permission authorises cannot take the node below the number
that authorised it.  *(That is `R10-N01`, and this step is where it would be
seen on a bench.)*

**THE FLOORS ARE NOT A TEST INCONVENIENCE AND MAY NOT BE OVERRIDDEN TO MAKE
THIS TABLE SQUARE.**  If the worst-case accessory transient below the enable
floors is ever wanted as engineering data, it is taken with an **explicitly
bounded bench image** that is built for that purpose, is labelled as such in the
record, and **is not the release image and is never flashed to a shipped unit**.
No build that relaxes `kAccessoryRetentionFloorV`, `kAccessorySingleRailFloorV`
or `kAccessoryDualRailFloorV` may exist in the release tree;
`demo_feature_contract` **F12** refuses any of the three constants ABOVE or
BELOW what it derives — too high is the `D790-A03` defect and too low is the
obvious one — and `firmware_hw_map_contract` H6 catches an edit to them.
*(D-791 / `R10-N04`: this paragraph named only the two ENABLE constants.
`kAccessoryRetentionFloorV` is the one that decides whether an authorised rail
STAYS up, which is precisely what `R10-N01` found being decided at the wrong
number — and it was the constant the prohibition did not cover.)*

### Acceptance

The absolute peak at `J1.40`/`J1.41`/`J1.42` must stay **below 3.300 V** and
the absolute trough at `U1.2` **above 3.000 V**, both **after the measurement
uncertainty is charged against the margin — peak PLUS uncertainty under the
ceiling, trough MINUS uncertainty over the floor** (D-790 / D789-A06).  Record the peak, the trough, the
uncertainty budget, the acquisition method (A or B) and the unit ID.  A failure
blocks that unit; **the designed lever is `C29`–`C32`**, which are 22 µF 1206
X7R parts on existing lands — `SLVS916I` 8.2.2.3 sets **no upper limit** on
output capacitance, so more capacitance is a **BOM value change with no PCB
change**.  Do not widen the acceptance instead.

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

## 7d. First-article acceptance items — the complete list (`R8-N05`, D-789)

**THESE EXISTED BEFORE D-789 AND NOTHING GATHERED THEM.**  Each item was
defined in whichever document raised it, so an assembler had to find six
acceptance procedures in five files.  This table is the index; the normative
text stays where it is.

| item | what it accepts | where the procedure is | raised by |
|---|---|---|---|
| **`Q11-TEMP-01`** | backlight at 0 / 25 / 40 °C after soak, and the D-784 full-duty prime | §7a above | D-780 |
| **`C-PWR-TRANSIENT-01`** | `+3V3` peak < 3.300 V at the panel pins and trough > 3.000 V at `U1.2`, DC-coupled or synchronised DC+AC, uncertainty charged against the margin | §7b below | D-788 / R7-N02, rewritten at D788-18 |
| **`C-THERM-01`** | thermography at the 40 °C top of the declared ambient envelope, held at the **D-791 SUSTAINED REFERENCE STATE** — both published accessory budgets, the display at full brightness and **ONE sub-GHz radio transmitting** — and MEASURED against the F12 model: battery current **1.6520 A**, BQ25185 junction **89.97 °C**, enclosure internal air **53.43 °C**, and the enclosure's own **`R_SYS` = 3.2493 K/W**, which is a DECLARED allowance and is what this test exists to measure.  **ALSO record the CHARGE regime**: with an adapter attached, the input FET, the charge FET and any BATFET supplement current, and the ambient at which the internal air reaches the pouch's own 40 °C charge window — DERIVED at **30.0 °C**.  Also record the `U11.2` narrow run.  *(D-789 framed this around a JEDEC θJA referenced to the EXTERNAL ambient; `D789-A02` replaced the frame.  D-790 then declared a reference state with BOTH radios transmitting that `D790-A02`/`D790-A03` show has no stable operating point at all; D-791 replaces the state.)* | `audit_rail_ampacity.py`, `checks/demo_feature_contract.py` F12, `AQROOT_DEMO_FAB_HANDOFF.md` | D-788, re-based at D788-03, at D-790 / D789-A02, and AGAIN at D-791 / D790-A02 |
| **`C-BAT-GATE-01`** | `ΔVGATE` (GATE − `BAT_PROTECTED_P`) and pass-pair drop (`BAT_RAW` − `BAT_SENSE`) at **2.60 A** at `BAT_RAW` = 4.15 / 3.60 / 3.05 V — six numbers, on the fitted **`AO4800`**.  This is what converts the one thing NO candidate publishes — hot `RDS(on)` at `VGS` = 2.5 V — from an extrapolation into a measured bound.  **D-791 / `D790-A01` ADDS TWO MORE**: the TURN-ON TIME from `SHDN` release to full enhancement, because ADI specifies `IGATE(UP)` and `tD(ON)` only at `VIN` = 12 V and neither is a 1S condition so the datasheet does not bound it here; and the current at which `VGS(Q2)` falls to the `AO4800`'s 2.5 V row, against the DERIVED ceiling of **2.2845 A** | [`SOURCING_LEDGER.md`](SOURCING_LEDGER.md) | D-789 / `R8-N01`, part fixed at D-790 / `D789-A01` |
| **`C-DISP-01`** | the display module's own `+3V3` draw, split into **panel logic** (`J1` `VCI` + `IOVCC` + the FT6236 touch controller) and **backlight converter input** (`U17` `VIN`), at full brightness and at the rail's heavy-load minimum.  The backlight half is DERIVED — `demo_feature_contract` `F6` solves it at **233.13 mA** from published maxima plus the four DECLARED loss allowances `D790-A04` requires (diode `Vf` at the inductor PEAK, switch transition and `Coss` at the MAXIMUM switching frequency, gate drive, and core loss + hot DCR) — and the panel half is a **DECLARED 50 mA allowance**, because ILI Technology publishes Sleep-in and Deep-Standby currents and **no active-mode supply current at all** and the EastRising module specification is not obtainable here.  This test is what replaces that declaration with a measurement | `checks/demo_feature_contract.py` F6 `p3v3_internal_budget`, `AQROOT_DEMO_FAB_HANDOFF.md` | D-790 / `D789-A11` |
| **`C-SPK-01`** | delivered speaker-lead insulation OD, then two sacrificial crimps pulled to destruction | [`OFF_BOARD_BOM.md`](OFF_BOARD_BOM.md) §7 | D-789 / D788-10 |
| **`C-ADH-01`** | DOWSIL 3145 adhesion on the actual soldermask and the actual lead insulation, per lot, after the full 72 h hold | [`BATTERY_HARNESS.json`](BATTERY_HARNESS.json) | D-789 / D788-17 |
| **`C-ACC-01`** | delivered Community-Port potential at the J5 mating interface, each 3.3 V contact **alone** and with the header fully mated | [`ACC_3V3_REINFORCEMENT.json`](ACC_3V3_REINFORCEMENT.json) | D-789 / D788-02 |
| **`C-ACC-02`** | the two routed `ACC_3V3_SW` contact resistances (79.0 / 224.4 mΩ expected) | [`ACC_3V3_REINFORCEMENT.json`](ACC_3V3_REINFORCEMENT.json) | D-789 / D788-16 |
| **`C-FW-ABORT-01`** | on the assembled board, with the console: request the 1 kHz tone while `AMP_SD_MODE`'s write is made to NACK (pull the expander's I2C or hold `SDA` during the transaction), then **watch `U2.P05` and the speaker for 30 s**.  The amplifier must never energise after the aborted command — D-790 left an ON intent that the main loop's deferred retry would honour with no tone and no matching OFF.  Repeat with the display test: after a NACKed `DISP_RST_N` release, confirm the console does NOT report the panel up, and that when the release finally lands the image **re-runs the ILI9488 initialisation** before it does | `Firmware/test/test_production_image.cpp`, `checks/firmware_hw_map_contract.py` H6 | D-791 / `D790-A06` + `D790-A07` |
| **`C-WARM-IMAGE-01`** | with both accessory rails ON, force a warm MCU reset (`EN` pulse, NOT a power cycle — the PCAL9535As must stay powered) while holding the internal I2C bus down; confirm the console reports the safety state as PENDING/UNKNOWN and **never** claims the rails are off, and that the accessory latches are still physically ON.  Release the bus and confirm the loop ALONE turns both rails off and reports recovery, with no console input | `Firmware/test/test_production_image.cpp` (the same scenario, on the host), `checks/firmware_hw_map_contract.py` H6 | D-791 / `D790-A05` + Fable `V-04` |
| **J4 fit / pull / thermal** | battery pigtail hole fit, retention and thermal acceptance | [`BATTERY_HARNESS.json`](BATTERY_HARNESS.json), §6 | D-781 / D-782 |

**None of these is optional and none of them is a PCB-fabrication item.**  They
are assembly and bring-up acceptance, and they are outstanding on every one of
the first five boards.  The manufacturer's own CAM acceptance is separate again.

---

## 8. Eight substitution traps found while building this table

**A loose keyword search against the JLC library returns a plausible wrong part more often than it
returns nothing.** Every one of these would have shipped silently.

| ref | intended | what a loose search returns | why it is wrong |
|---|---|---|---|
| `D10`–`D12` | ~~Nexperia `BAT54WS,115`~~ → **Diodes Inc `BAT54WS-7-F`** (D-211) | Nexperia **`BAT54W,115`** `C8657` | **CORRECTED 2026-08-23.** Both are *single independent* diodes — **`BAT54WS` is NOT a series pair**. `BAT54W,115` is wrong because it is **SOT-323 (SC-70)**, a **footprint mismatch** against `Diode_SMD:D_SOD-323`, and it has **5 in stock** against a need of 15 |
| `SW1`–`SW7` | C&K `PTS645SM43SMTR92LFS` | G-Switch **`GT-TC089A-H043-L1`** `C843623` | **Different manufacturer**, land pattern never checked against the C&K G-Type layout this footprint was built from — and it is **35 placements** |
| `D8` | onsemi `NSR0240HT1G` | FUXINSEMI **`SD103AWS`** `C915626` | **Different part number entirely** |
| `Q4`, `Q6`–`Q9` | onsemi `BSS138LT1G` | LRC **`LBSS138LT1G`** `C8490` | Different manufacturer — **and the genuine onsemi part has 762,522 in stock**, so there is no reason to accept it |
| `L2`, `L4` | Würth `74438357010` | KOHERelec **`SPM4030-1R0M`** `C2761910` | Different manufacturer's inductor in a switching regulator |
| `Q2`, `Q3` | Alpha & Omega **`AO4800`** `C17098` *(was onsemi `NTMD4820NR2G`, RETIRED at D-790)* | the VBsemi, HXY, UMW, JSMSEMI, MSKSEMI and TECH PUBLIC rows that carry the **same `AO4800` marking**, and the old VBsemi `NTMD4820NR2G-VB` `C7525084` | Clones and re-marks in the **battery reverse-polarity pass path**. The CTO ruling forbids silent substitution of power-path parts, and D-790 / D789-A01 lists the six refused marking-alikes by name |
| `Q2`, `Q3` (again) | a genuine SOIC-8 dual N-FET replacement | JLC attribute table: **`YJQ3622A`** `C5440262` — advertised as *2 N-channel, 30 V, `VGS(th)` 1 V, 3112 in stock* | **D-789 / `R8-N01`. ITS DATASHEET SAYS SINGLE N-CHANNEL IN DFN3.3×3.3.** It would not have fitted the land, let alone the topology. The catalogue attribute row was simply wrong, which is why the `Q2`/`Q3` selection criteria put *read the datasheet, not the catalogue row* first |
| `J6` speaker crimp | JST **`SPH-004T-P0.5S`** (AWG #32–#28) | JST **`SPH-002T-P0.5S`** — same series, same housing, same catalogue page, carried in this repository from D-148 to D-788 | **D-789 / D788-10 + `R8-N02`. NOT A SEARCH RESULT — A MISREAD OF THE SOURCE.** The `ePH` catalogue's series header says *#32 to #24*; the CONTACT table says `SPH-002T-P0.5S` is **#30 to #24, OD 0.8–1.5 mm** and `SPH-004T-P0.5S` is **#32 to #28, OD 0.5–0.9 mm**. The fitted AWG #32 lead was outside the fitted contact in **both** dimensions, and the two contacts take **different crimp tooling** |

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
| how many distinct MPNs? | **105** on the released assembly BOM and **106** across the full BOM including DNP, counted from `aqroot-Demo-BOM-full.csv` and `aqroot-Demo-BOM-assembly.csv` themselves. *(D-790 / D789-A07: this row read **46 (43 after merges)**, which was the FBV2-S2-002 sourcing sweep's shortlist and never the BOM's own line count.)* |
| how many assembly lines / references? | **123 grouped lines** covering **251 fitted references**; the full BOM has **144 lines** of which **10** are DNP |
| how many parts machine-placed? | **all fitted SMT parts; Class E covers five manual references (`J4`,`J5`,`J6`,`D1`,`U6`)** |
| how many manual solder operations per board? | **5** — `J4`, `J5`, `J6`, `D1`, `U6`; J4 is a wire pigtail land, while the other four are fitted THT parts; `J4`/`D1`/`U6` also have normative trim/forming instructions |
| how many fine-pitch/QFN parts hand-placed? | **zero** |
| how many part identities need consignment? | **NINE, from the live sweep of all 123 assembly lines re-run for D-790 on 2026-09-21** (`evidence/d790-sourcing-sweep.json`): `SSQ-124-02-G-S-RA` (`J5`), `74438357010` (`L4`), `LQW18AN39NG80D` (`L5`/`L6`), `DMM-4026-B-I2S-R` (`MK1`), `SQ2364EES-T1_BE3` (`Q11`), **`LTC4368IMS-1#TRPBF` MSOP-10 `C688401`** (`U18`), `TLV7032DDFR` (`U19`), `PCAL9535APW,118` (`U2`/`U3`), `ST25R3916-AQET` (`U9`) + 0 class D.  **`AO4800` (`Q2`/`Q3`) is NO LONGER on this list** — D-790 / D789-A01 re-selected the pass pair and the AOS line re-swept at **5 347** against a need of 10 — **but it is still one of the ten exact identities that `D789-S01` requires an AUTHORISED ALLOCATION for before money is spent**, because stock in a catalogue is not an allocation and these are the battery path's pass FETs.  `NSR0240HT1G` (`D8`) is also not on this list at 5 280 in stock. **Re-check all stock immediately before order; any additional exact-source item whose live stock no longer covers first-five need also moves to consignment. Archived counts are not purchasing authority.** |
| DNP parts with no recorded reason | **zero** — eight were still undocumented at the start of FBV2-S2-002 and all eight now carry one |
| does the build close today? | **Yes, via consignment, and the D-789 PRE-PCBA BLOCK on `Q2`/`Q3` is CLOSED.** D-790 / D789-A01 re-selected the battery pass pair to Alpha & Omega **`AO4800`** (`C17098`, genuine AOS line, live stock 5 347) and `demo_feature_contract` **F10** now PROVES it rather than holding it. It does **not** close as a pure LCSC turnkey order. **Every consigned identity below still needs an authorised allocation before money is spent — that is a purchasing action this repository cannot take, and it is the remaining gate (`D789-S01`).** |

**Do not optimise cents. Optimise first-build success.** Consignment cost is trivial against one failed board or one wrong-part respin; the exact count must be recomputed from live stock at order time rather than inherited from this archived snapshot.

---

## 11. What this plan does **not** claim

- It does **not** claim any of these stock figures will still hold when the order is placed.
- ~~It does **not** adopt a single substitute part.~~ **SUPERSEDED 2026-08-23 (FBV2-MECH-002),
  and the count RESTATED at D-790 / D789-A07 — it read "the only two substitutions" long after
  the programme had adopted five.** Every part substitution this programme has
  CTO-approved, in order:
  1. **`BAT54WS-7-F`** (`C124205`) at `D10`–`D12` — D-211;
  2. **`0466005.NRHF`** (`C57525`) at `F1` — D-210;
  3. **`AO3422`** and then Vishay **`SQ2364EES-T1_BE3`** (`C5758702`) at `Q11` — D-766, D-780,
     for `VDS` margin against the open-LED clamp and then for a published low-gate conduction row;
  4. **`BAT54WS-7-F`** again at `D14` — D-789 / D788-11, because the `1N4148WS` gate hold no longer
     qualified once the rail moved down to keep the panel inside its absolute maximum;
  5. **`AO4800`** (`C17098`) at `Q2`/`Q3` — D-790 / D789-A01, because the retired
     `NTMD4820NR2G` publishes no conduction row below `VGS` = 4.5 V and a `VGS(th)`
     **MAXIMUM** of 3.0 V that the LTC4368's guaranteed gate drive cannot clear.

  Divider and limiter VALUE changes (`R39`, `R40`, `R75`, `R97`, `R101`) are not counted here:
  they are component values on the same part class, not substitutions. **No other substitution is
  authorised**, and none may be made at the assembler's discretion.
- It does **not** cover the anonymous passive values, which stay unconsolidated until the layout
  exists.
