# AQROOT Beta DM — exact DNP list, with the electrical evidence

Measured on the Beta-DM copy of `0f53205`. Every "is it shared?" question was
answered from the exported netlist and the landed PCB copper, not from the
schematic sheet a part happens to be drawn on.

Three population classes are used, and the difference matters:

| class | meaning |
|---|---|
| **DNP** | the part has no function on DM and must not be fitted |
| **DNP-ELIGIBLE / KEEP** | dedicated to a DNP block, but sits between two live rails (typically +3V3–GND) where fitting it is harmless and mildly useful. Recommendation: **fit it**, to avoid BOM churn and keep the Final restoration trivial |
| **KEEP** | required on DM |

---

## 1. U9 ST25R3916 — bus-safety audit (mandatory)

### 1.1 What actually reaches U9 in copper

| U9 pin | function | net | copper state on the board |
|---|---|---|---|
| 30 | SCLK | `/SPI_B_SCK` | **connected** — F.Cu track lands on the pad |
| 31 | MOSI | `/SPI_B_MOSI` | **connected** — F.Cu track lands on the pad |
| 32 | MISO (tri-state) | `/SPI_B_MISO` | **connected** — F.Cu track lands on the pad |
| 1 | VDD_IO | `+3V3` | **connected** — 0.15 mm E6 neck (`E6_U9_1`, 0.160 mm local clearance) |
| 29 | BSS (SPI slave select) | `/NFC_CS_N` | **NO COPPER. 0 tracks, 0 vias on the whole net.** |
| 27 | IRQ | `/NFC_IRQ` | no copper |
| 8 / 10 | VDD / VDD_TX | `/NFC_5V_PA_PENDING` | rail is 5-rats unrouted; boost enable never asserted |

### 1.2 Is there a guaranteed CS pull-up?

**In the schematic, yes. On the board, no.**

`R29` (10 k) is drawn from `+3V3` to `/NFC_CS_N`. But `/NFC_CS_N` carries
**zero track segments and zero vias**: it has three pads (R29.2, U1.17, U9.29)
and two ratsnest lines. `R29.1` has its `+3V3` escape landed (that escape is why
`E6_R29_1_CLR` / `E6_R29_1_WIDTH` exist and why the R29 B3 trunk fills the F.Cu
gap at x=10.0), but `R29.2` goes nowhere. **The pull-up is not electrically
connected to U9 pin 29.**

### 1.3 What happens during MCU reset?

ESP32-S3 `IO9` is high-Z through reset and until firmware configures it. Because
`/NFC_CS_N` has no copper, U9 pin 29 is an **unterminated CMOS input on a
3.3 V-powered IO ring**, in reset and in normal operation alike. Its level is
indeterminate and can float across the input threshold.

### 1.4 Can U9 ever drive MISO without controlled CS?

Yes, and this is the decisive finding. `VDD_IO` is powered from `+3V3`, so U9's
output drivers are alive. `MISO` (pin 32, tri-state) sits on the **shared SPI-B
bus with U7 (CC1101) and U8 (SX1262)** — both DM must-work radios. With SS
floating there is no guarantee U9 keeps MISO in high-Z, so a populated U9 is a
credible contention source on the one bus the flagship LoRa demo depends on.

A second, independent objection: U9 has `VDD_IO` present while `VDD` and
`VDD_TX` are unpowered. That is outside the ST25R3916 supply-sequence envelope
and is not a configuration we should ship on a demo unit.

A third: even in the most charitable reading (an undocumented internal SS
pull-up holding the device deselected), a populated U9 has **no CS, no IRQ and
no VDD** in copper — firmware cannot enumerate it, reset it or use it.
Populating it buys nothing and risks the bus.

### 1.5 Disposition

> **U9: DNP. Unconditional.** No electrical evidence exists that would make
> population safe; the evidence points the other way.

### 1.6 Parts that become unnecessary when U9 is DNP

Sole-purpose U9 support — **DNP** (each sits on a U9-output net that does not
exist without U9, so populated they would be floating):

| ref | value | net | ST DS12484 role |
|---|---|---|---|
| C45 | 2.2 µF | `NFC_VDD_D` | regulator decoupling |
| C46 | 10 nF | `NFC_VDD_D` | regulator decoupling |
| C47 | 2.2 µF | `NFC_VDD_A` | regulator decoupling |
| C48 | 10 nF | `NFC_VDD_A` | regulator decoupling |
| C49 | 2.2 µF | `NFC_VDD_RF` | regulator decoupling |
| C50 | 10 nF | `NFC_VDD_RF` | regulator decoupling |
| C51 | 2.2 µF | `NFC_VDD_AM` | VDD_AM decoupling |
| C52 | 1 nF | `NFC_VDD_AM` | VDD_AM decoupling |
| C53 | 1 µF | `NFC_AGDC` | AGDC reference |
| C54 | 10 nF | `NFC_AGDC` | AGDC reference |

**DNP-ELIGIBLE / KEEP:**

| ref | value | net | why keep |
|---|---|---|---|
| C18 | 100 nF 0402 | `+3V3`–GND | U9 VDD_IO decoupling, but it is a bare rail decoupler; fitting it is free extra +3V3 decoupling in a congested corner |
| R29 | 10 k | `+3V3`–`NFC_CS_N` | holds the now-unused MCU `IO9` node at a defined level; its `+3V3` escape is already landed; **does not** protect U9 (no copper on the net) |

**Not touched (shared):** `SPI_B_SCK` / `MOSI` / `MISO` and their series/pull-up
parts, `R27` (SX1262 CS pull-up), `R28` (CC1101 CS pull-up), `R74` (SX1262_RXEN
pull-down) — all radio-critical, all **KEEP**.

### 1.7 The NFC 5 V PA boost — CTO ruling requested

U9 is the **only** load on `/NFC_5V_PA_PENDING`. With U9 DNP the whole boost
block has no consumer, its enable is never asserted, and the rail is already
5-rats unrouted. The block is:

| ref | part | DM recommendation |
|---|---|---|
| U13 | TPS61023 boost | **DNP** |
| L2 | 1 µH WE-MAPI 4030 | **DNP** |
| R44 | 732 k 1 % (FB top) | **DNP** |
| R45 | 100 k 1 % (FB bottom) | **DNP** |
| C34 | 22 µF 10 V X7R | **DNP** |
| C35 | 22 µF 10 V X7R | **DNP** |
| C19 | 100 nF 0402 (HF, VDD/VDD_TX) | **DNP** |
| C55 | 2.2 µF (bulk, VDD/VDD_TX) | **DNP** |
| TP9 | `NFC_5V_PA_PENDING` test point | DNP (no part) |
| R14 | 100 k `NFC_5V_EN` pull-down | follows the U13 ruling — **MUST KEEP if U13 is populated** |
| TP10 | `NFC_5V_EN` test point | follows the U13 ruling |

This was **not** named in the CTO DNP set, so it is raised rather than taken.
It is also the largest single BOM/assembly saving available to DM. C55 also
carries an open ≤0.80 mm panel-height question that DNP makes moot for DM.

---

## 2. Speaker DNP audit

Parts dedicated **solely** to speaker output:

| ref | part | class | evidence |
|---|---|---|---|
| U5 | MAX98357A | **DNP** | its only nets are `I2S_SPK_DOUT`, `AMP_SD_MODE`, `SPK_P`, `SPK_N` plus rails |
| J6 | JST-PH-2 speaker | **DNP (unpopulated)** | `SPK_P`/`SPK_N` have exactly two nodes each: U5 and J6 |
| C9 | 100 nF | DNP-ELIGIBLE / **KEEP** | U5 VDD decoupling by placement (2.195 mm from U5 VDD vs 7.787 mm from MK1 VDD); bare +3V3–GND |
| C10 | 10 µF | DNP-ELIGIBLE / **KEEP** | U5 bulk by placement; bare +3V3–GND |
| R15 | 100 k | DNP-ELIGIBLE / **KEEP** | `AMP_SD_MODE` pull-down; see §2.1 |

| ref | part | class | evidence |
|---|---|---|---|
| C8 | 100 nF | **KEEP FOR MIC** | 1.977 mm from MK1 VDD vs 8.693 mm from U5 VDD — this is the ICS-43434 decoupler |
| MK1 | ICS-43434 | **KEEP** | microphone, DM must-work |

**Not applicable:** the J6 connector-type swap. It is a Full/Final design item and
there is no remaining DM reason to touch it. Do not perform it in DM.

### 2.1 `AMP_SD_MODE` — the remaining-safety-dependency question

`R15` exists to hold `~SD_MODE` low (amplifier shut down) during the window where
the TCA9535 expander port `U2.P03` is high-Z at power-up. **With U5 DNP there is
no amplifier to mute, so that safety dependency disappears.**

> `AMP_SD_MODE`: **DO NOT ROUTE in DM.**

Fitting R15 anyway is recommended (it keeps `U2.P03` at a defined level and
costs nothing), but it is not required and it is not a safety item on DM.

### 2.2 The routing consequence

With U5 DNP, `I2S_BCLK` and `I2S_LRCLK` no longer have to reach U5.14/U5.16.
Their only remaining sinks are MK1 and U1. This is precisely what turns the
paused 4-net Full-Beta I2S problem into the 3-net DM problem.

---

## 3. Microphone-only audio validation (mic must work with the amplifier DNP)

ICS-43434 (MK1) requirements, each checked against the netlist:

| need | net / pin | source | depends on U5 / `AMP_SD_MODE` / `SPK_DOUT` / J6? |
|---|---|---|---|
| power | MK1.5 `VDD` ← `+3V3` | main 3.3 V rail (routed, 0 rats) | **no** |
| ground | MK1.3 `GND` (+ MK1.2) | In1 GND plane | **no** (4 GND rats to stitch) |
| channel select | MK1.2 `LR` → **hard-wired to GND** | direct, left channel | **no** |
| bit clock | MK1.4 `SCK` ← `I2S_BCLK` ← U1.32 (IO39) | MCU | **no** |
| word select | MK1.1 `WS` ← `I2S_LRCLK` ← U1.33 (IO40) | MCU | **no** |
| data out | MK1.6 `SD` → `I2S_MIC_DIN` → U1.35 (IO42) | MCU | **no** |
| decoupling | C8 100 nF on `+3V3` | dedicated, kept | **no** |

`LR` is tied to GND in copper terms by the same plane every other GND pad uses —
there is no mode pin driven by U5, no shared enable, and no shared serial data
line (the mic drives `I2S_MIC_DIN`; the amplifier would have received
`I2S_SPK_DOUT`, a separate net).

> **Microphone operation is electrically independent of the amplifier. No
> dependency found. KEEP the microphone in DM.**

---

## 4. IR

| ref | part | block | DM class |
|---|---|---|---|
| U6 | TSOP38238 receiver | IR_RX | **DNP** (deferred) |
| R21 | 100 R (VS series) | IR_RX | **DNP** |
| C11 | 4.7 µF (VS bypass) | IR_RX | **DNP** |
| D1 | TSAL6200 IR LED | IR_TX | pending ruling — see the MCU-release doc |
| Q1 | AO3400A | IR_TX | pending ruling |
| R22 | 100 R gate series | IR_TX | pending ruling |
| R23 | 100 K gate pull-down | IR_TX | pending ruling (**MUST KEEP if Q1 is populated**) |
| R24 | 18 R LED series | IR_TX | pending ruling |
| C12 | 4.7 µF | IR_TX local +3V3 | pending ruling / DNP-ELIGIBLE |

`IR_RX_GPIO44` also has **no single-object escape release** at U1.36 — the only
demand in the south row for which none exists — which independently supports
deferring it.

---

## 5. Roll-up: the exact DM DNP set

**DNP (do not fit):**

```
U9  C45 C46 C47 C48 C49 C50 C51 C52 C53 C54          NFC controller + its support
U5  J6                                                speaker amplifier + connector
U6  R21 C11                                           IR receiver
U13 L2 R44 R45 C34 C35 C19 C55                        NFC 5 V PA boost  [ruling requested]
D1  Q1 R22 R23 R24 C12                                IR transmitter    [ruling requested]
```

**DNP-eligible but recommended to fit:** `C18`, `R29`, `C9`, `C10`, `R15`
(and `R14`, `TP10` follow the U13 ruling).

**Nets not routed in DM:** `I2S_SPK_DOUT`, `AMP_SD_MODE`, `SPK_P`, `SPK_N`,
`NFC_CS_N`, `NFC_IRQ`, `NFC_5V_PA_PENDING`, `NFC_5V_EN`, all `NFC_*_TBD`,
`IR_RX_GPIO44`, `IR_RX_VS_LOCAL`, `IR_GATE`, `IR_LED_A`, `IR_LED_K`
(and `IR_TX_GPIO16` if IR_TX is deferred).

**No area reclaim.** Every DNP footprint stays where it is, so Final restoration
is a population change, not a layout change.
