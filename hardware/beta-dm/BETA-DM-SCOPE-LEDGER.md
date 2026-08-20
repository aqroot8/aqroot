# AQROOT Beta DM — Scope Ledger

Authoritative classification of every Beta feature for the **Demo Model**.
Created against the frozen full-Beta head `0f53205` (`beta-full-reference-v1`).

> **Superseded in part by the LEAN Demo Model ruling.** J5 expansion scope is
> now governed by [BETA-DM-LEAN-SCOPE.md](BETA-DM-LEAN-SCOPE.md): four XGPIO,
> not fourteen. Rows 3, 15 and 16 below carry the Lean status. Nothing was
> removed, moved, renumbered or reclaimed — see
> [BETA-DM-LEAN-RESTORATION.md](BETA-DM-LEAN-RESTORATION.md).

**Rule that governs this file:** a DM cut is never a Final-product cut. Every row
carries a Final restoration status. If a row's Final column says `RESTORE`, the
hardware stays physically present on the DM board (no area reclaim, see §20 of the
DM ruling) and the only thing that changes is population and routing effort.

## Status vocabulary

| status | meaning |
|---|---|
| `MUST WORK` | DM demo fails without it; routed, populated, bring-up verified |
| `BASIC BRING-UP` | populated and routed; only smoke-level function required for DM |
| `DNP` | footprint present, part not populated on DM |
| `NO ROUTE` | net deliberately left unrouted on DM copper |
| `LEAN DEFER` | fitted-to-fitted net deliberately unrouted under the Lean ruling; Full Beta restores it |
| `UI/SIM` | shown in the DM UI, backed by firmware simulation, not by DM hardware |
| `FINAL ONLY` | not a DM item at all |

---

## 1. DM must-work set

| # | function | DM status | routed today | remaining DM work | Final |
|---|---|---|---|---|---|
| 1 | ESP32-S3 boot / core (U1) | MUST WORK | core rails, SPI **and `BOOT_N`** routed | none | same |
| 2 | Display + touch (SPI-A, J1) | MUST WORK | SPI_A_*, DISP_*, TOUCH_RST_N **and the whole backlight string** routed — `LED_BOOST`, `LED_K`, `LED_A1..4` all one island, 0 rats | J1 GND (**31** rats) | same |
| 3 | Battery / charging (BQ25185, MAX17048, TPS63020) | MUST WORK | rails routed; `U12-PG`, `PS_SYNC`, `U15-CT` **closed, 0 rats**; `SW9-A` switch path `SW9.1`↔`U12.12`↔`R43.1` routed | `BQ25185_STAT1/2` (2) — scratch-proven closable; `SW9-A` `TP13` (1) **LEAN DEFER**; `Net-(U15-QOD)` (1) **LEAN DEFER**, audited safe; GND | same |
| 4 | USB / programming (J3, USB_D pair) | MUST WORK | USB pair through E4, **`J3-CC1/CC2` and `J3-SHIELD` closed, 0 rats**; `U10` USBLC6-2SC6 **fitted** | J3 GND (1), U10 GND (1) | same |
| 5 | Buttons (SW2..SW9 + U2 TCA9535) | MUST WORK | E2 closed out, button ratsnest 0; `WAKE_ATTN_N_HDR` fitted path `R66.2`→`J5.13` **connected** | none — the one `WAKE_ATTN_N_HDR` line left goes to the DNP `D7` | same |
| 6 | microSD (J2) | MUST WORK | SPI_A + SD_CS_N routed | J2 GND (**7** rats) | same |
| 7 | Wi-Fi / BLE | MUST WORK | module onboard antenna, no board RF | nothing electrical; enclosure keep-out only | same |
| 8 | SX1262 915 (U8) | MUST WORK | **all** control + SPI + 3V3 routed, 0 signal rats; **U8 GND stitching complete, 0 GND rats** | flex antenna install only | same |
| 9 | 915 RF path / antenna | MUST WORK | by design **no board RF trace** | mechanical: FXP890 flex on module IPEX | same |
| 10 | AQROOT↔AQROOT LoRa | MUST WORK | depends on 1,8,9,4 | firmware | same |
| 11 | CC1101 433 (U7) | MUST WORK | **all** control + SPI + 3V3 routed, 0 signal rats; **U7 GND stitching complete, 0 GND rats** | flex antenna install only | same |
| 12 | 433 RF path / antenna | MUST WORK | by design **no board RF trace** | mechanical: FXP450 flex on module IPEX | same |
| 13 | IMU (U4 BMI270) | BASIC BRING-UP | I2C/strap routed | `U4-INT2`, `OCSB`, `OSDO` are NC by design; GND (**4**) | same |
| 14 | Microphone (MK1 ICS-43434) | MUST WORK | **LANDED** — the 3-net I2S is on the board; `I2S_MIC_DIN` one island, `I2S_BCLK`/`I2S_LRCLK` complete on the fitted circuit; **MK1 GND stitching complete, 0 GND rats** | none | same |
| 15 | J5 / F4 community header | **LEAN SCOPE: four active XGPIO + external I2C + FAST_IO + WAKE + 3V3/GND** | 19/19 escapes landed; 13 of 14 `XGPIO*_HDR` resistor→J5 paths complete; `FAST_IO_GPIO43_HDR` and `WAKE_ATTN_N_HDR` complete | **16 Lean must-work lines open** — `XGPIO4/5/6/7` (4), ext-I2C header links (2), `Net-(U16-SCLB/SDAB)` (2), `ACC_PWR_EN` (3), `ACC_3V3_SW` (3), plus `BQ25185_STAT1/2` (2) elsewhere. **15 lines LEAN DEFER** | RESTORE all 14 XGPIO |
| 16 | BOOT / programming access (SW1, R2) | MUST WORK | **`BOOT_N` routed** — Option W, 52.445 mm, one island | none | same |
| 17 | Safety / protection (ESD arrays, R27/R28/R74) | MUST WORK | pull-ups and R74 in place | none on DM — **`D2`–`D7` are all DNP**, so their branches and their GND stitching are intentionally isolated (bucket A) | RESTORE `D2`–`D7` |
| 18 | GND finalisation | MUST WORK | `In1 GND REFERENCE` plane drawn and filled, **61 GND vias**; `U7`, `U8`, `MK1`, the USB-C connector, the MCU and the pull-to-ground parts stitched | **130 GND rats** — the single largest remaining DM job; **HELD until the fitted must-work non-GND residual is zero** | same |

## 1a. J5 status, stated three ways

The three are not the same thing and must not be collapsed into one verdict.

| question | status | basis |
|---|---|---|
| **J5 population / active scope** | **PASS** | `J5` and every series resistor, `XGPIO` path, ext-I²C, `FAST_IO`, `WAKE`, `ACC_3V3_SW`, `+3V3` and `GND` pin is **fitted**. Nothing J5-related is DNP except the `D2`–`D7` shunt ESD arrays, already approved as DNP |
| **J5 Lean functional connectivity** | **INCOMPLETE — architecture proven, not landed** | the 16 Lean must-work lines are open; the routing architecture that closes them is in [BETA-DM-LEAN-ROUTING.md](BETA-DM-LEAN-ROUTING.md) |
| **J5 Full-Beta functional connectivity** | **DEFERRED BY RULING** | 15 further fitted-to-fitted lines are intentional Lean deferrals, every one with a restoration entry |
| **Full-Beta XGPIO preserved** | **14 / 14** | no pin renumbered, no resistor removed, no `U3` assignment changed |

**J5 must not be reported as functionally PASS while the 16 Lean joins remain.**

---

## 2. DM DNP / deferred set

| # | item | DM status | reason | Final |
|---|---|---|---|---|
| 19 | Speaker output (whole chain) | DEFER | not needed for the LoRa demo; removes the 4th I2S net | RESTORE |
| 20 | U5 MAX98357A | DNP | speaker-only | RESTORE |
| 21 | J6 speaker connector | DNP (unpopulated) | speaker-only | RESTORE |
| 22 | `I2S_SPK_DOUT` | NO ROUTE | sink (U5.1) is DNP | RESTORE |
| 23 | `SPK_P` / `SPK_N` | NO ROUTE | both ends DNP | RESTORE |
| 24 | `AMP_SD_MODE` + R15 | NO ROUTE, R15 KEEP-populated | no amplifier to mute ⇒ no safety dependency (audit §4 below) | RESTORE |
| 25 | J6 connector-type swap | NOT A DM ITEM | no DM reason to touch it | FINAL item, unchanged |
| 26 | IR_RX (U6 TSOP38238, R21, C11) | DEFER / DNP | receiver demo not in DM scope; U1.36 has **no** single-object escape release | RESTORE |
| 27 | IR_TX (D1, Q1, R22, R23, R24, C12) | **DEFER / DNP** | not routable under ordinary rules: `U1.9` has 0 escape cells and needs a **2-object** release, the cheapest being a +3V3 F.Cu bar or the SPI_B_SCK F.Cu escape bar — see [BETA-DM-RF-AND-IR.md](BETA-DM-RF-AND-IR.md) §2 | RESTORE |
| 28 | NFC physical (loop, matching, crystal) | DEFER | antenna and matching never designed; all `*_TBD` nets | RESTORE |
| 29 | U9 ST25R3916 | **DNP** | floating CS on a live shared SPI-B bus + unpowered VDD (audit §3) | RESTORE |
| 30 | U9 support passives C18, C45–C55 | DNP (C18 KEEP-populated) | U9-only (audit §3) | RESTORE |
| 31 | NFC 5 V PA boost U13 + L2 + R44 + R45 + C34 + C35 + TP9 | **DNP — CTO ruling requested** | U9 is its only load; the rail is 5-rats unrouted | RESTORE |
| 32 | R29 (NFC_CS_N pull-up) | KEEP populated | 10 k, zero risk, holds the now-unused GPIO9 defined; does **not** protect U9 (net has no copper) | keep |
| 33 | Advanced software suites | FINAL ONLY | firmware scope | FINAL |
| 34 | PCB area reclaim | FORBIDDEN ON DM | maximum restoration path, minimum churn | n/a |

## 3. Feature-to-dependency contradictions checked

| claimed cut | dependency probe | result |
|---|---|---|
| U5 DNP | does the microphone need the amplifier? | **No** — audit §5 |
| U5 DNP | do `I2S_BCLK`/`I2S_LRCLK` still need to reach U5 pads? | **No** — the only remaining sinks are MK1 and U1; this is what turns the 4-net I2S problem into a 3-net one |
| `AMP_SD_MODE` NO ROUTE | is R15 a power-up safety pull-down that still matters? | **No** — it exists to mute U5 before U2 drives P03; with U5 DNP there is nothing to mute |
| U9 DNP | does anything else sit on `NFC_IRQ`, `NFC_CS_N`? | No — both are U9↔U1 only |
| U9 DNP | is `NFC_5V_PA_PENDING` shared? | Only with its own boost block (U13/C19/C34/C35/C55/R44/TP9) — no other load |
| U13 DNP | is `BQ25185_SYS` affected? | No — U13 is a load on SYS, not a source for anything else |
| IR_RX DNP | does IR_TX depend on it? | No — separate nets, separate parts |
| J5 keep | does the connector cost justify depopulating? | No — routing cost already paid, BOM saving negligible |

## 4. What is explicitly NOT deferred

- **Neither radio.** SX1262 and CC1101 are both DM must-work. Both are already
  fully routed on the signal side; only GND stitching and the flex-antenna
  install remain.
- **J5 / F4.** Keep as routed. 19/19 header escapes stay.
- **The microphone.** The reduced 3-net routing is judged practical — see
  [BETA-DM-MCU-RELEASE.md](BETA-DM-MCU-RELEASE.md).
- **The board outline.** No compaction, no area reclaim.

---

## 5. Final-product restoration ledger

Confirmed for every Demo Model cut. **No DM simplification changes Final scope.**
Nothing was deleted from the design, no footprint moved and no board area was
reclaimed, so every restoration below is a population change plus the routing of
that function's nets — never a re-layout.

| DM cut | DM disposition | **Final disposition** | what restoration costs |
|---|---|---|---|
| Speaker output (U5, J6) | DNP, `I2S_SPK_DOUT` / `AMP_SD_MODE` / `SPK_P` / `SPK_N` unrouted | **RESTORE / REQUIRED** | clear `dnp` on U5 and J6; route 4 nets. `I2S_SPK_DOUT` needs full-Beta release object #3 (`BTN_HOME_N` In2) back — the object DM eliminated. |
| IR transmitter (D1, Q1, R22, R23, R24) | DNP, `IR_TX_GPIO16` and the IR-TX local nets unrouted | **RESTORE / REQUIRED** | clear `dnp`; route. `U1.9` needs a **two-object** release: `I2C_SDA_INT` In2 (already taken by DM as R1) plus either the `+3V3` F.Cu bar at y ≈ 17.10–17.55 or the `SPI_B_SCK` F.Cu escape bar. |
| IR receiver (U6, R21, C11) | DNP, `IR_RX_GPIO44` and `IR_RX_VS_LOCAL` unrouted | **RESTORE / REQUIRED** | clear `dnp`; route. `U1.36` has **no single-object release** — this is the hardest of the deferred escapes and needs its own architecture pass. |
| NFC front end (U9 + C45–C54) | DNP for SPI-B bus safety | **RESTORE / REQUIRED** | clear `dnp`; **route `NFC_CS_N` first** — that is what makes population safe. Then `NFC_IRQ`, the four `NFC_VDD_*` rails and `NFC_AGDC`. |
| NFC loop / matching / crystal | never designed; `RF_DEFERRED_NFC` netclass makes routing a DRC error | **RESTORE WITH NFC / REQUIRED** | antenna and matching design, then lift the `RF_DEFERRED_NFC` rule. |
| NFC 5 V PA boost (U13, L2, R44, R45, C34, C35, C19, C55) | DNP — U9 is its only load | **RESTORE WITH NFC / REQUIRED** | clear `dnp`; route `NFC_5V_PA_PENDING`, `NFC_5V_EN`, `Net-(U13-FB)`, `Net-(U13-SW)`. `R14` and `TP10` are already fitted on DM, so nothing to undo there. |
| Advanced protocol suites | not on DM | **FINAL SOFTWARE** | firmware only; no hardware consequence. |
| J6 connector-type swap | not touched on DM | **FINAL DESIGN ITEM, UNCHANGED** | still open as a Full/Final decision; DM neither advanced nor foreclosed it. |
| Board area | not reclaimed | **n/a** | the DM board and the Final board share the same outline, the same placement and the same mounting holes. |

Two restoration facts worth keeping visible:

1. **DM eliminated release object #3** (`BTN_HOME_N` In2) because `I2S_SPK_DOUT`
   is not a DM demand. Restoring the speaker for Final brings that object back —
   it was not made unnecessary, only unnecessary *for DM*.
2. **DM took release R1** (`I2C_SDA_INT` In2) for `I2S_BCLK`. IR TX also needs
   R1. That is a shared prerequisite, not a conflict: with R1 already landed,
   IR TX's marginal cost drops from two release objects to one.

