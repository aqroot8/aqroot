# AQROOT Beta DM — Scope Ledger

Authoritative classification of every Beta feature for the **Demo Model**.
Created against the frozen full-Beta head `0f53205` (`beta-full-reference-v1`).

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
| `UI/SIM` | shown in the DM UI, backed by firmware simulation, not by DM hardware |
| `FINAL ONLY` | not a DM item at all |

---

## 1. DM must-work set

| # | function | DM status | routed today | remaining DM work | Final |
|---|---|---|---|---|---|
| 1 | ESP32-S3 boot / core (U1) | MUST WORK | core rails and SPI routed | `BOOT_N` (3 rats) needs release object R4 | same |
| 2 | Display + touch (SPI-A, J1) | MUST WORK | SPI_A_*, DISP_*, TOUCH_RST_N routed | backlight string `LED_A1..4`, `LED_K` (5 rats); J1 GND (55 rats) | same |
| 3 | Battery / charging (BQ25185, MAX17048, TPS63020) | MUST WORK | rails routed | `BQ25185_STAT1/2` (2), `SW9-A` (4), `U12-PG`/`PS_SYNC` (4), `U15-CT`/`QOD` (2), GND | same |
| 4 | USB / programming (J3, USB_D pair) | MUST WORK | USB pair routed through E4 | `J3-CC1/CC2` (2), `J3-SHIELD` (4), GND | same |
| 5 | Buttons (SW2..SW9 + U2 TCA9535) | MUST WORK | E2 closed out, button ratsnest 0 | none for buttons; `WAKE_ATTN_N_HDR` (1) | same |
| 6 | microSD (J2) | MUST WORK | SPI_A + SD_CS_N routed | J2 GND (9 rats) | same |
| 7 | Wi-Fi / BLE | MUST WORK | module onboard antenna, no board RF | nothing electrical; enclosure keep-out only | same |
| 8 | SX1262 915 (U8) | MUST WORK | **all** control + SPI + 3V3 routed, 0 signal rats | U8 GND (17 rats); flex antenna install | same |
| 9 | 915 RF path / antenna | MUST WORK | by design **no board RF trace** | mechanical: FXP890 flex on module IPEX | same |
| 10 | AQROOT↔AQROOT LoRa | MUST WORK | depends on 1,8,9,4 | firmware | same |
| 11 | CC1101 433 (U7) | MUST WORK | **all** control + SPI + 3V3 routed, 0 signal rats | U7 GND (15 rats); flex antenna install | same |
| 12 | 433 RF path / antenna | MUST WORK | by design **no board RF trace** | mechanical: FXP450 flex on module IPEX | same |
| 13 | IMU (U4 BMI270) | BASIC BRING-UP | I2C/strap routed | `U4-INT2`, `OCSB`, `OSDO` are NC by design; GND (6) | same |
| 14 | Microphone (MK1 ICS-43434) | MUST WORK | 0 tracks | 3-net I2S solve (see MCU release doc); MK1 GND (4) | same |
| 15 | J5 / F4 community header | MUST WORK — **KEEP AS ROUTED** | 19/19 escapes landed | `XGPIO*`↔`XGPIO*_HDR` links (14 rats), `ACC_3V3_SW` (7), ext-I2C (4) | same |
| 16 | BOOT / programming access (SW1, R2) | MUST WORK | 0 tracks | `BOOT_N` after R4 release | same |
| 17 | Safety / protection (D3..D7 ESD, R27/R28/R74) | MUST WORK | pull-ups and R74 in place | ESD-diode GND stitching | same |
| 18 | GND finalisation | MUST WORK | In1 plane filled, 27 GND vias | **164 GND rats** — the single largest remaining DM job | same |

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
| 27 | IR_TX (D1, Q1, R22, R23, R24, C12) | **NEEDS RULING** — see audit §6 | routable only behind a release; not free | RESTORE |
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
