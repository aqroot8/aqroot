# AQROOT Full Beta v2 — Pre-Design Engineering Audit

Date: 2026-08-22
Task: Initial read-only Full Beta v2 architecture audit
Repository HEAD at audit: b8b5ebdd1559083b328782f4fbbfdcce849b46d0

---

**Provenance.** The body below is the Claude Code engineering audit produced
immediately before task FBV2-DOC-001, reproduced verbatim from the live
conversation context. Two mechanical notes, so that "verbatim" is not
overstated:

1. The original response opened with the sentence *"Audit complete. Everything
   below is measured from the repository at the SHAs shown; nothing was
   written."* followed by a horizontal rule. That lead-in is preserved in
   [`transcripts/2026-08-22-session-01.md`](../transcripts/2026-08-22-session-01.md)
   and is omitted here only because it is a conversational frame, not audit
   content.
2. The audit's own first-level heading was `# AQROOT Full Beta v2 — Pre-Design
   Engineering Audit`, which is identical to the required title above and has
   been merged into it rather than duplicated.

No technical conclusion, number, measurement, recommendation or caveat has been
altered, shortened, softened or reordered.

---

## 1. Repository safety / status

**Two repos.** `P:\Vaults\ClaudeVault` is the Obsidian vault; `AQROOT/` inside it is a **separate git repo** (`origin https://github.com/aqroot8/aqroot.git`). All hardware work is in the inner repo.

| item | value |
|---|---|
| AQROOT branch | `master` |
| AQROOT HEAD | `b8b5ebdd1559083b328782f4fbbfdcce849b46d0` — *"Beta-DM: J1 is the Hirose FPC connector, not the display module"* |
| AQROOT `git status --short` | `?? hardware/beta-dm/fab/AQROOT-Beta-DM-Gerbers-aa64c16.zip`<br>`?? hardware/beta/mechanical/` |
| Outer vault branch / HEAD | `master` / `1a23c76ab85c3b1708aeeb0e2419194bc40a8fbe` |
| Outer vault status | ` M .claude/settings.local.json` (pre-existing at session start) |

**Protected trees — verified clean:**
- `git diff --stat beta-full-reference-v1 -- hardware/beta/` → **empty**
- `git diff --stat HEAD -- hardware/beta-dm/` → **empty**
- `hardware/beta/mechanical/` remains untracked and untouched (`freecad/`, `reference/`, `reports/`, `source-scripts/`).

**Tag `beta-full-reference-v1`** — annotated, tagger Mohamad Abdulazim, 2026-08-18, on commit `0f53205fa56b5b2a05bb065f76bac72b4f78a0c0`. Records: PCB sha256 `d001cf4b…f1d`, 188 footprints / 776 pads (703 netted) / 1517 segments / 270 vias / 41 zones / 176 nets / 12 Edge.Cuts items; DRC 0 errors, 240 warnings, 281 unconnected; ERC 58 violations (5 errors).

**Current Beta-DM source files** (`hardware/beta-dm/kicad/aqroot-beta-dm/`):

| file | role |
|---|---|
| `aqroot-Beta-DM.kicad_pro` / `.kicad_prl` | project |
| `aqroot-Beta-DM.kicad_sch` | root sheet |
| `01_power_tree` … `09_community_header.kicad_sch` | 9 hierarchical sheets |
| `aqroot-Beta-DM.kicad_pcb` | board (2.48 MB, KiCad 10 format — nets are inline `(net "NAME")`, **no net-number table**) |
| `aqroot-Beta-DM.kicad_dru` | design rules |
| `libraries/AQROOT_Beta.kicad_sym`, `libraries/AQROOT_Beta.pretty` | project symbol + footprint libs |
| `fp-lib-table`, `sym-lib-table` | `${KIPRJMOD}`-relative |

Fab package in `hardware/beta-dm/fab/` (Gerbers, BOM fitted/full, CPL, POFV control, MPN ledger, DNP control, assembly PDFs, JLC set).

---

## 2. Beta-DM subsystem inventory (measured from the PCB pad→net map)

| block | parts | state |
|---|---|---|
| MCU | **U1 ESP32-S3-WROOM-1-N16R8**, R1/C1 (EN), R2 10k + SW1 (BOOT), TP1/TP2 (GPIO45/46) | fitted, routed |
| Display + touch | **J1 Hirose FH69-50S-0.5SH** 50-pin FPC → off-board **CH280QV10-CT** 2.8″ 240×320 TFT+CTP; **U17 TPS61169** backlight boost (L3 4.7 µH, D8 NSR0240, R69 2.55R, LED_A1..4/LED_K) | fitted, routed |
| microSD | **J2 Molex 5025700893**, SPI-A + `SD_CS_N`; `SD_CARD_DETECT_TBD` (J2.10) **dangling** | fitted |
| USB-C | **J3 GCT USB4105-GF-A-120**, **U10 USBLC6-2SC6**, R30/R31 5.1k Rd, R32 shield, R33/R34 22R series, R35 0R VBUS link, C23 | fitted, routed |
| Charger / power path | **U11 BQ25185DLHR** (R36 18k ILIM_VSET, R37 1k ISET, R38 10k TS_MR) | fitted |
| Fuel gauge | **U14 MAX17048G+T10** on I²C, ALRT → **TP11 only** | fitted |
| 3V3 rail | **U12 TPS63020DSJR** buck-boost, L1 XFL4020-152MEC, FB R39 1M / R40 180k (→3.28 V), C29-C32 4×22 µF, EN from **SW9 JS102011SAQN** hard switch, R43 100k, R68 0R **DNP** bypass, PG→R41 1M (diagnostic only) | fitted, routed |
| Battery | **J4 JST B2B-PH-K** — **J4.1 is a single-pad net `BAT_CONNECTOR_P`** | see §12 |
| Expander (internal) | **U2 TCA9535PWR @ 0x20** — P00-P07 control, P10-P16 buttons, P17 RootProbe IRQ | fitted, routed |
| Expander (external) | **U3 TCA9535PWR @ 0x21** — XGPIO0-13, P16 `SX1262_RXEN`, P17 `ACC_PWR_EN` | fitted, routed |
| Buttons | SW2-SW8 PTS645SM43SMTR92LFS = UP/DOWN/LEFT/RIGHT/A/B/**HOME**; R4-R10 10k pull-ups | fitted, routed |
| IMU | **U4 BMI270**, R18 220R series into GPIO3, TP3 | fitted |
| 433 MHz | **U7 E07-400M10S** (CC1101), CS/GDO0/SPI-B; `CC1101_ANT_TBD` = module IPEX | fitted, routed |
| 915 MHz LoRa | **U8 E22-900M22S** (SX1262), CS/BUSY/DIO1/RST/RXEN/DIO2_TXEN; `RF_ANT_TBD` = module IPEX | fitted, routed |
| Microphone | **MK1 ICS-43434** I²S, `I2S_BCLK`/`I2S_LRCLK`/`I2S_MIC_DIN` | **fitted, routed, MUST-WORK** |
| Community header | **J5 Samtec TSW-113-08-G-D-RA** 2×13, R51-R64 100R XGPIO series, R47/R48 22R ext-I²C, R66 330R WAKE, R67 470R FAST_IO, **U15 TPS22918 DNP**, **U16 TCA9517A DNP**, D2-D7 ESD **all DNP** | 19/19 escapes routed |
| Audio out | **U5 MAX98357A DNP**, **J6 DNP**, LS1 off-board 8Ω | DNP |
| IR | **D1 TSAL6200 DNP** (5 mm THT), **Q1 AO3400A DNP**, R22 gate, R23 100k, **R24 18R to +3V3**, C12; **U6 TSOP38238 DNP**, R21 100R + C11 4.7 µF | DNP, unrouted |
| NFC | **U9 ST25R3916-AQET DNP**, **U13 TPS61023 DNP** + L2 + R44/R45 + C34/C35 | DNP, 13 dangling `*_TBD` nets |

**Measured net totals:** 176 unique nets on pads — exactly matching the tag. **20 nets carry only one pad** (dangling): the 13 NFC `*_TBD` nets, `RGB_R/G/B_CTL`, `BAT_CONNECTOR_P`, `SD_CARD_DETECT_TBD`, `CC1101_ANT_TBD`, `RF_ANT_TBD`, `RESERVED_NC`.

---

## 3. Frozen Full Beta subsystem inventory

Full Beta and Beta-DM are the **same board, byte-identical at fork**. The delta is population + routing, not topology. Full Beta = Beta-DM with the DNP set restored:

| restored on Full Beta | parts |
|---|---|
| Speaker chain | U5 MAX98357A, J6, LS1 |
| IR TX | D1, Q1, R22, R23, R24, C12 |
| IR RX | U6, R21, C11 |
| NFC front end | U9 + C18/C45-C55 |
| NFC 5 V PA boost | U13, L2, R44, R45, C19, C34, C35, C55 |
| External I²C buffer | U16 TCA9517ADGKR |
| Switched accessory rail | U15 TPS22918DBVR |
| Connector ESD | D2, D7 (TPD2E009DBZR), D3-D6 (TPD4E1B06DRLR) |
| Ext-I²C pull-ups | R49, R50 4.7k (to `ACC_3V3_SW`) |
| Misc | C11, C19, C21/C22, C34/C35, C45-C55, R21-R24, R44/R45 |

**Full Beta was never fully validated either.** Its own freeze recorded 281 unconnected items and 58 ERC violations. Treat it as a *feature reference*, not a working design — which is exactly the strategy directive, and the audit confirms it was the right call.

---

## 4. Full Beta v2 delta matrix

| # | item | disposition | note |
|---|---|---|---|
| 1 | ESP32-S3-WROOM-1-N16R8 | **KEEP** | unchanged |
| 2 | Wi-Fi/BLE (module antenna) | **KEEP** | enclosure keepout only |
| 3 | Display + touch (J1 FPC + CH280QV10-CT) | **KEEP** | re-verify FT6236 addr on production module |
| 4 | microSD (J2) | **KEEP** | consider ADDing card-detect to a spare expander pin |
| 5 | USB-C sink front end | **KEEP** | unchanged; add VBUS-present sense (§12) |
| 6 | BQ25185 + MAX17048 + TPS63020 | **KEEP** | ADD charge-status telemetry (§5) |
| 7 | Reverse-polarity protection | **ADD — BLOCKER** | never drawn; `BAT_CONNECTOR_P` is a dead net |
| 8 | 433 MHz E07-400M10S | **KEEP** | |
| 9 | 915 MHz E22-900M22S | **KEEP** | |
| 10 | External antenna capability | **ADD** | no board RF connector exists today (§10/§13) |
| 11 | IMU BMI270 | **KEEP / MODIFY** | add the missing GPIO3 strap-defining pull |
| 12 | NFC ST25R3916 + boost | **MODIFY + ADD** | rail architecture defect, no crystal, no antenna (§11) |
| 13 | IR TX + IR RX | **KEEP (restore)** | stays internal; raise drive current, move off +3V3 (§10) |
| 14 | Microphone ICS-43434 | **KEEP unchanged** | best-validated block in the design |
| 15 | Speaker MAX98357A + J6 | **KEEP (restore)** | add output EMI filter (§9) |
| 16 | Community header J5 | **MODIFY** | 26 → 20 pins, keyed/shrouded (§6/§7) |
| 17 | External I²C via TCA9517A | **KEEP topology / RE-VERIFY part** | partial-power-down behaviour unproven (§8) |
| 18 | Switched accessory rail TPS22918 | **KEEP** | add reverse-blocking (§12) |
| 19 | Connector ESD D2-D7 | **KEEP (restore)** | ADD protection on `+3V3` and `ACC_3V3_SW` pins |
| 20 | Volume Up / Volume Down buttons | **N/A — DO NOT EXIST** | see below |
| 21 | Home button (SW8, U2.P16) | **REMOVE** | frees one U2 pin |
| 22 | D-pad (SW2-SW5), A (SW6), B (SW7) | **KEEP** | |
| 23 | Power switch SW9 (hard EN switch) | **KEEP** | correct architecture, not a GPIO |
| 24 | BOOT SW1 | **KEEP / MODIFY** | same circuit, recessed actuator (§18) |
| 25 | RGB LED (`RGB_R/G/B_CTL`) | **ADD or DELETE** | nets exist, **no LED part exists** — 3 dangling ERC errors |
| 26 | RootProbe IRQ (U2.P17) | **REMOVE or COMPLETE** | pull-up + expander pin only; **no J5 pin** — cannot connect |
| 27 | Board outline 155 × 74 | **MODIFY** | must be re-floorplanned against a published cavity (§13) |

> **Correction to the brief:** there are **no Volume Up/Down buttons in the hardware**. `SW2-SW8` are UP/DOWN/LEFT/RIGHT/A/B/HOME. "Volume +, Volume −, Power" appears only in *Enclosure Field Slate v5 §5* as an industrial-design leftover with no electrical counterpart. The only physical control actually removed by the CTO lock is **HOME**. The Field Slate right-side layout text should be corrected.

---

## 5. MCU / GPIO resource audit

Measured directly from `U1` pads on the board, decoded against the WROOM-1 pin table:

| GPIO | net | GPIO | net |
|---|---|---|---|
| 0 | `BOOT_N` | 18 | **`NFC_IRQ`** |
| 1 | `I2C_SDA_INT` | 19/20 | USB D−/D+ |
| 2 | `I2C_SCL_INT` | 21 | `WAKE_INT_N` (RTC wake) |
| 3 | `BMI270_INT1_STRAP` | 35/36/37 | **unusable** (octal PSRAM, N16R8) |
| 4/5/6 | SPI-B SCK/MOSI/MISO | 38 | **`SX1262_DIO1`** |
| 7 | `CC1101_CS_N` | 39/40 | I²S BCLK / LRCLK |
| 8 | `SX1262_BUSY` | 41 | `I2S_SPK_DOUT` |
| 9 | `NFC_CS_N` | 42 | `I2S_MIC_DIN` |
| 10 | `DISP_CS_N` | 43 | `FAST_IO_U0TXD_ROOTPROBE_CS` |
| 11/12/13 | SPI-A MOSI/SCK/MISO | 44 | `IR_RX_GPIO44` |
| 14 | `DISP_DC` | 45 | `TEST_GPIO45` (TP1, strap) |
| 15 | `CC1101_GDO0` | 46 | `TEST_GPIO46` (TP2, strap) |
| 16 | `IR_TX_GPIO16` | 47 | `DISP_BL_CTL` |
| 17 | `SX1262_CS_N` | 48 | `SD_CS_N` |

**29 assigned + 2 strap test pads + 2 USB = 31 of 31 usable. Free native GPIO: ZERO.** This is measured, not quoted.

**Doc/schematic parity defect (new finding).** `11 - Beta Pin Map v0.2.md` §1 states GPIO18 = SX1262 DIO1 and GPIO38 = NFC IRQ. **The hardware is the reverse.** Electrically harmless today, but it has a real consequence: **only GPIO0-21 are RTC GPIO on the S3**, so `SX1262_DIO1` on GPIO38 **cannot be an `ext0`/`ext1` deep-sleep wake source**. Wake-on-LoRa-packet is therefore impossible in the current pinout. If v2 wants it, DIO1 must move to an RTC pin.

**Expander capability and its limits.**
- U2 @ 0x20 (internal): 16/16 used. After removing HOME → **P16 free**. `ROOTPROBE_IRQ_READY_N` (P17) connects only to a pull-up and U2 — it has no J5 pin, so **P17 is also effectively free** unless RootProbe is completed.
- U3 @ 0x21 (external): 14 XGPIO + `SX1262_RXEN` (P16, internal) + `ACC_PWR_EN` (P17, internal).
- **XGPIO speed, stated honestly:** a TCA9535 output change is one 3-byte I²C write ≈ 27 bits. At 400 kHz that is ~70 µs plus stack overhead — a practical ceiling around **5-10 kHz toggle**, with jitter set by I²C arbitration against touch, IMU and fuel-gauge traffic. An input change is only observable after `/INT` asserts and firmware reads both Input Port registers of both devices — **~100-300 µs latency, and the chip has no INTF/INTCAP, so the source is not recorded**. XGPIO cannot do UART, SPI, PWM, RMT/IR, 1-Wire, WS2812, or any bit-banged protocol. They are enables, chip selects, mode straps, LEDs and slow sensors.
- **The two expanders are on the same I²C bus as touch, IMU and fuel gauge.** External-segment isolation (U16) is what keeps an accessory from taking the UI down.

**Realistic native reclaim options, ranked:**

| # | reclaim | frees | risk |
|---|---|---|---|
| A | Move `NFC_IRQ` → GPIO46 (idles **low**, matching the required boot-strap level), freeing **GPIO18** (clean, RTC-capable) | 1 | **Low-medium** — needs a 50-100 boot validation and TP2 already exists to scope it |
| B | Drop native IMU motion-wake, poll BMI270 → frees **GPIO3** | 1 | Medium — GPIO3 is the JTAG-select strap; exposing it on a user connector is a boot-integrity hazard |
| C | Expose GPIO45 directly | 1 | **Reject** — VDD_SPI strap; an accessory pulling it high can make the module unbootable |
| D | Merge SPI-A and SPI-B onto one bus | 3 | **High** — display refresh would contend with LoRa/NFC timing on a showcase demo |

**Conclusion: at most 1 additional safe native pin (option A) without an architectural change.** Four native header pins is only reachable via option D.

---

## 6. Three candidate 20-pin community connector architectures

Baseline for comparison — the current F4 26-pin map (verified against `J5` pads): `+3V3`×1, `GND`×5, `XGPIO0-13`×14, `WAKE_ATTN_N`, `I2C_SDA/SCL_EXT`, `ACC_3V3_SW`, `FAST_IO`, `RESERVED_NC` = 26.

### C1 — Expander-Max (zero native reclaim)

| pin | signal | pin | signal |
|---|---|---|---|
| 1 | `+3V3` | 11 | `XGPIO8` |
| 2 | `GND` | 12 | `XGPIO9` |
| 3 | `XGPIO0` | 13 | `XGPIO10` |
| 4 | `XGPIO1` | 14 | `XGPIO11` |
| 5 | `XGPIO2` | 15 | `I2C_SDA_EXT` |
| 6 | `XGPIO3` | 16 | `I2C_SCL_EXT` |
| 7 | `XGPIO4` | 17 | `WAKE_ATTN_N` |
| 8 | `XGPIO5` | 18 | `FAST_IO` (GPIO43) |
| 9 | `XGPIO6` | 19 | `ACC_3V3_SW` |
| 10 | `XGPIO7` | 20 | `GND` |

**13 GPIO-capable** (12 slow + 1 native). Native reclaim: **0**. Lowest risk, closest to the "~14" headline. Weakness: only one native pin, and it is the noisy boot-log/`ROOTPROBE_CS` multiplexed one — so no accessory UART, no SPI-with-real-CS, no RMT.

### C2 — Balanced, two true native pins (recommended)

| pin | signal | pin | signal |
|---|---|---|---|
| 1 | `+3V3` | 11 | `XGPIO8` |
| 2 | `GND` | 12 | `XGPIO9` |
| 3 | `XGPIO0` | 13 | **`NATIVE_A`** = GPIO43 (`FAST_IO/U0TXD/ROOTPROBE_CS`) |
| 4 | `XGPIO1` | 14 | **`GND`** |
| 5 | `XGPIO2` | 15 | **`NATIVE_B`** = GPIO18 (reclaimed, RTC-capable) |
| 6 | `XGPIO3` | 16 | `I2C_SDA_EXT` |
| 7 | `XGPIO4` | 17 | `I2C_SCL_EXT` |
| 8 | `XGPIO5` | 18 | `WAKE_ATTN_N` |
| 9 | `XGPIO6` | 19 | `ACC_3V3_SW` |
| 10 | `XGPIO7` | 20 | `GND` |

**12 GPIO-capable** (10 slow + 2 native), 3 grounds, one ground adjacent to each native pin. Native reclaim: **1** (option A). Enables a genuine accessory **UART** (43 = TX, 18 = RX), a genuine **SPI** (native CS on 43 + XGPIO for the rest), **RMT/PWM/1-Wire/WS2812** on 18, and a **second RTC wake source**.

### C3 — CTO straw man, 4 native + 10 XGPIO

`+3V3`, `ACC_3V3_SW`, 2×`GND`, `SDA`, `SCL`, `WAKE`, 4× native, 10× XGPIO = 20. **14 GPIO-capable.**

**Cost, measured:** requires **3** native reclaims. Only reachable by merging SPI-A and SPI-B (option D, 3 pins) or by exposing two strapping pins (GPIO3 + GPIO45/46). Both put a showcase prototype at risk — a bus merge makes display refresh contend with LoRa/NFC on the demo's flagship feature, and strapping pins on a user connector mean a third-party accessory can make the unit unbootable.

---

## 7. Recommended connector architecture

**Recommend C2.** Reasoning:

1. **The 14-signal target cannot be met honestly.** 14 GPIO-capable pins in 20 requires 3 native reclaims that do not exist. C1 gets to 13, but only by making 12 of them expander pins.
2. **A native pin is not worth "one XGPIO" — it is worth a protocol class.** Two natives buy UART, SPI, PWM, RMT/IR and addressable-LED support. Two extra XGPIO buy two more slow enables. For a community expansion interface, the protocol classes are the product.
3. **Every pin has independent capability** — no physical pin is duplicated onto an internal GPIO, per the CTO rule. `NATIVE_A` and `NATIVE_B` are distinct silicon pins; all 10 XGPIO are distinct U3 pins; SDA/SCL are the real buffered bus.
4. **Three grounds, positioned.** The F4 study found the 26-pin map was ground-poor in columns c5-c9. At 20 pins with two natives, grounds at 2/14/20 place a return adjacent to `NATIVE_A` (13-14 pair) and near `ACC_3V3_SW` (19-20 pair), fixing the F4 weakness rather than inheriting it.
5. **Fallback is defined.** If the GPIO18/GPIO46 reclaim fails its boot-strap validation gate, fall back to C1 with no other change — pin 15 becomes `XGPIO10`. The connector count and mechanical design are unaffected.

**Freed U3 capacity (XGPIO10-13, 4 pins) must be left as NC with defined pulls** — do **not** repurpose them for internal signals. U3's whole architectural value is that an accessory can never contend with internal control. Use the freed **U2.P16** (HOME) and **U2.P17** (orphaned RootProbe IRQ) for internal needs instead — the natural claimants are `BQ25185_STAT1` and `BQ25185_STAT2`, which today reach only test points.

**Not locking the connector.** Recommend the mechanical requirement be captured now as: **20-pin, keyed, shrouded, polarised, recessed, right-side exit**. The present `J5` is an unkeyed 0.1″ 2×13 pin header — mis-insertion by one row places `+3V3` on a signal pin. That is an electrical safety requirement, not styling.

---

## 8. External I²C architecture recommendation

**Keep external I²C. Keep the buffered topology. Re-verify the part.**

Internal I²C devices measured on `I2C_SDA_INT`/`I2C_SCL_INT`: **U2** TCA9535 @0x20, **U3** TCA9535 @0x21, **U4** BMI270 @0x68, **U14** MAX17048 @0x36, plus the display module's **FT6236** @0x38 via J1. Pull-ups R19/R20 4.7k. That bus carries the buttons, every internal control signal, the touch input path and the fuel gauge — it must survive a hostile accessory.

The implemented topology is correct and should be carried forward:

```
+3V3 ──> U16 TCA9517A ──> R47/R48 22R ──> J5 (SDA/SCL_EXT) ──> D2 ESD
   VCCA │ EN=ACC_PWR_EN │ VCCB = ACC_3V3_SW
                                 └── R49/R50 4.7k pull-ups referenced to ACC_3V3_SW
+3V3 ──> U15 TPS22918 (CT=C39 slew, QOD=R46 discharge) ──> ACC_3V3_SW
```

This is right for three reasons that a direct connection would not give: the B-side supply *is* the accessory rail, so pull-ups die with accessory power; `EN` is tied to `ACC_PWR_EN`, so bus isolation and power gating cannot drift apart; and the TPS22918's quick-output-discharge implements the §8c step-3 bleed.

**Two open items:**

1. **Verify TCA9517A partial-power-down behaviour against the datasheet.** The design's own selection criteria (§8c) demand "powered-off high-impedance on the external side" and "must not back-power the accessory side through I/O or protection diodes." The TCA9517A does not advertise an I<sub>off</sub>/partial-power-down spec the way TCA9617B-class parts do. If it back-feeds `ACC_3V3_SW` through its B-side I/O, the discharge step is defeated and a latched-up accessory stays alive. **This is a part-selection gate, not a layout detail.**
2. **`ACC_3V3_SW` has no reverse-blocking.** TPS22918 is a plain NMOS load switch; an accessory that back-drives the rail pushes current through the body diode into `+3V3`, and R49/R50 give it a second path onto the external bus. Add either an ideal-diode/reverse-blocking load switch or a series Schottky plus a TVS at the connector.

**Do not connect external SDA/SCL directly.** With five internal devices including the button expander, a shorted accessory line makes the device appear dead to its own buttons.

---

## 9. Audio input / output recommendation

**Input — keep exactly as built.** `MK1 ICS-43434` is a digital I²S MEMS mic: no analog front end, no bias network, no codec, 24-bit, and it is the **only Beta-DM block that is fitted, fully routed and GND-stitched with zero remaining work**. Carry it forward unchanged, footprint included (it is a custom pad — a 0.3 mm signal pad inside a 1.625 mm GND ring; do not re-derive it).

**Output — MAX98357A is already the simplest sensible implementation. Keep it.** The alternatives were checked against this specific silicon:

| alternative | verdict |
|---|---|
| PWM + RC filter + analog Class-D (PAM8302 etc.) | **Worse.** The ESP32-S3 has **no DAC** (unlike ESP32 classic). Needs a native PWM pin — none free — plus filter parts, and gives worse intelligibility. |
| External I²S DAC + separate amplifier | **Worse.** Two chips instead of one, no benefit at speech bandwidth. |
| Buzzer / piezo | **Excluded by the CTO, and correctly.** Cannot produce speech, and still needs a native timer pin. |
| MAX98357A | **Simplest.** One chip: I²S in, filterless Class-D BTL out. Reuses the I²S bus the mic already requires, adds **zero native pins**, and its shutdown is already a slow enable on U2.P03 with an external safe-state pull-down (R15, verified present). |

**Full-duplex note:** mic and amp share `I2S_BCLK`/`I2S_LRCLK` on one ESP32-S3 I²S controller. That works, but it forces **one sample rate and one bit width for capture and playback simultaneously**. 16 kHz / 16-bit satisfies both voice input and speech output — lock that as a firmware contract.

**Three v2 requirements:**
1. **Add an output EMI filter.** Filterless Class-D running unshielded `SPK_P`/`SPK_N` to an off-board speaker, next to a 433/915 MHz radio and an NFC loop, is an EMI liability. There is currently **no snubber or LC filter** on those nets (C52 is NFC `VDD_AM` decoupling, R24 is the IR LED resistor — neither is an audio part). Add ferrite beads + shunt caps at J6, and route `SPK_P/SPK_N` as a tight differential pair away from the RF and NFC zones.
2. **Confirm the GAIN_SLOT strap.** U5 pins 5/6/12/13 are unconnected — the floating-GAIN default is 9 dB. Fine, but verify it is the intent and that it is the correct pin, not an omission.
3. **Budget the amp's current.** At 3.3 V into 8 Ω BTL, peak output current ≈ 410 mA on the same `+3V3` rail as the MCU and radios. Include it in the brownout gate (§12).

**Power rail choice is right.** Running the amp from `+3V3` rather than SYS caps output at ~0.5-0.7 W into 8 Ω — plenty for intelligible speech and alerts, which is the stated requirement, and it keeps a Class-D switcher off the battery rail.

---

## 10. IR reintegration requirements

IR stays internal. The parts are already placed and the nets already exist; three things must change.

**a. The routing blockers are placement artifacts and must be designed away, not solved again.** The scope ledger records `U1.9` (GPIO16, IR TX) needing a **two-object copper release** and `U1.36` (GPIO44, IR RX) having **no single-object release at all** — the hardest deferred escape in the design. Both are consequences of the frozen 155 × 74 placement. Because v2 re-floorplans (§13), **IR TX and IR RX escape routes must be a floorplan input**, not a late-stage release negotiation.

**b. Move the IR LED off the +3V3 logic rail and raise the drive.** Measured: `R24` 18R from `IR_LED_A` to **`+3V3`**, LED cathode switched by `Q1` AO3400A, gate via `R22` with `R23` 100k pull-down, `C12` 4.7 µF local. With TSAL6200 V<sub>f</sub> ≈ 1.35 V that is ≈ **108 mA** — modest for a universal remote (a few metres at best), and it puts a 38 kHz, ~108 mA pulse train directly onto the MCU/radio rail behind only 4.7 µF.
   **Recommend:** drive the LED from `BQ25185_SYS`, not `+3V3`; size the resistor for **300-1000 mA pulsed**; add local bulk (≥22 µF) at the LED/FET loop; enforce a firmware duty-cycle/thermal limit. Keep the gate pull-down and gate series resistor — GPIO16 has no boot-log traffic, which is why it was chosen, and that reasoning still holds.

**c. Keep the receiver's supply filter and separate it optically.** `R21` 100R + `C11` 4.7 µF into `IR_RX_VS_LOCAL` is correct TSOP practice — keep it. `U6` must sit outside `D1`'s emission cone with an opaque barrier between them, or the transmitter blinds the receiver.

**d. Mechanical.** `D1` is a **5 mm through-hole** LED and `U6` a THT minicast — both need real enclosure apertures on the top crown, with the IR window co-located with the RF crown per Field Slate v5. Also evaluate the TSAL6200's ±17° half-angle; a handheld remote may want a wider emitter or a second LED.

---

## 11. NFC reintegration requirements

Measured state of `U9` on the board:

| U9 pins | net | state |
|---|---|---|
| 1 | `+3V3` | connected (this is `VDD_IO` — the 3.3 V SPI domain is correct) |
| **8, 10** | `NFC_5V_PA_PENDING` | main supply pins on the **boosted** rail |
| 3, 7, 9/14, 11 | `NFC_VDD_D` / `VDD_A` / `VDD_RF` / `VDD_AM` | internal-regulator decoupling nets |
| 4, 5 | `NFC_XIN_TBD`, `NFC_XOUT_TBD` | **dangling — no crystal exists in the BOM** |
| 13, 15, 22, 23 | `RFO1/RFO2/RFI1/RFI2_TBD` | **dangling — no matching network** |
| 17, 18, 19 | `EXT_LM`, `AAT_A`, `AAT_B_TBD` | dangling |
| 2, 25, 28 | `CSO`, `CSI`, `MCU_CLK_TBD` | dangling |
| 27, 29-32 | `NFC_IRQ`, `NFC_CS_N`, SPI-B | connected |

**What must be reintroduced:**

1. **A 27.12 MHz crystal and its load caps — they do not exist anywhere in the design.** Or commit to the `NFC_MCU_CLK` path and specify the source. This is a hard blocker, not a routing task.
2. **The full antenna matching network** — EMC filter, matching, damping. `RFO1/RFO2/RFI1/RFI2/AAT_A/AAT_B` are all bare. The `RF_DEFERRED_NFC` netclass currently makes routing them a DRC error; that rule lifts only when the design exists.
3. **The four `NFC_VDD_*` decoupling nets.** Note the recorded constraint: R29.1's B3 trunk fills the F.Cu gap at x = 10.0, so these four now need vias to cross. That is a v1-placement artifact and should evaporate on re-floorplan.
4. **The boost block** — U13 TPS61023, L2 1 µH, R44/R45 divider, C34/C35, enabled by `NFC_5V_EN` (U2.P02) with R14 100k safe-state pull-down (verified present).

**VDD_IO vs PA rail — architecture defect, must be resolved before capture.**
The intent recorded in the pin map is: *"boost ONLY the analog/PA rail; keep VDD_IO at 3.3 V."* **The implementation boosts both main-supply pins (8 and 10) while VDD_IO sits at 3.3 V.** With the boost in its default-off state, the chip's core supply is at 0 V while its I/O supply is at 3.3 V — a partial-power condition that typically violates the part's VDD_IO ≤ VDD rule and injects current into VDD through the I/O domain. The Beta-DM DNP audit reached the same place from a different direction (`U9` DNP was made *unconditional* partly because "`U9` has `VDD_IO` present while `VDD` … is not").
**Recommend for v2:** feed the ST25R3916's main VDD from `+3V3` and boost **only** the transmitter/PA supply, so the digital core and I/O domains are always coherent. Verify the exact pin-to-rail assignment against the ST25R3916 datasheet before capture — the QFN-32 rail names must be confirmed from the drawing, not inferred.

**Startup / default-off state — verify the boost actually disconnects.** Most non-isolating boost converters pass V<sub>IN</sub> to V<sub>OUT</sub> through the inductor and body diode when disabled. If the TPS61023 does that, `NFC_5V_PA_PENDING` sits at roughly SYS − V<sub>f</sub> (~3.3-4.1 V) whenever the system is on — which contradicts both the "default OFF" safe-state claim and the "zero idle draw" power argument. Confirm true-shutdown/load-disconnect behaviour from the datasheet; if absent, add a series load switch or accept and document the standing rail.

**Power budget.** ST25R3916 field-on at 5 V draws on the order of 250-350 mA; through a boost from ~3.7 V SYS that is ~400-500 mA at the battery. **The existing power budget (doc 13) does not include NFC at all** — its 640 mA "heavy burst" figure predates it. Re-derive the worst-case concurrent case: NFC field-on + backlight + Wi-Fi TX.

**Antenna, enclosure and battery interference (design later, constrain now).** Rear-centre metal-free target per Field Slate v5, with **no stored antenna across it** (already locked). The real constraint is the **battery**: a LiPo pouch directly behind the loop kills Q and detunes the match. Either offset the coil from the cell footprint or add a ferrite shield layer between them. **This is a stackup and cavity decision that must be frozen before placement** (§13). Also add an OVP clamp on the boosted rail (§12).

---

## 12. Power-budget and self-damage / fault-risk review

Because physical DM bring-up may be skipped, every item below is a **gate**, not advice.

### BLOCKER — reverse-polarity protection does not exist

Measured: **`BAT_CONNECTOR_P` is a single-pad net (J4.1 only).** `U11.2` (BQ25185 BAT) and `U14.2/3` sit on `BAT_PROTECTED_P`. **Nothing bridges them.** The Design Decisions Log confirms this is deliberate and unresolved:

> `[ REV-POLARITY PROTECTION PLACEHOLDER ]` … *LTC4368-1 CANDIDATE + BACK-TO-BACK N-CHANNEL MOSFETS … MANDATORY FAULT CASE: REVERSED BATTERY WHILE USB POWERS BQ25185 … **DO NOT ROUTE. DO NOT RELEASE TO FAB.***

Consequence for v2: a board fabricated as-is **will not run from battery at all**, and has no defence against a reversed pack. **Gate: the block must be drawn, LTSPICE-simulated for the charge path, vendor-confirmed and professionally reviewed before any fab release.**

### Rail-by-rail

| # | fault class | measured state | gate for Full Beta v2 |
|---|---|---|---|
| 1 | **5 V into 3.3 V domains** | VBUS reaches only J3 → USBLC6 → R35 0R → C23 → U11 VIN. No 5 V touches logic. CC1/CC2 = 5.1k Rd only, no PD, no source role. | Confirm BQ25185 input OVP threshold from the datasheet; add a VBUS TVS if the clamp alone is relied on. **PASS by inspection, verify by measurement.** |
| 2 | **Regulator overshoot** | TPS63020 FB = 1M/180k → 3.28 V. C<sub>OUT</sub> 4×22 µF 1206, DC-bias-derated (C24's measured −52 % at 4.5 V shows how real this is). WROOM abs max 3.6 V. | **First-article gate:** scope `+3V3` turn-on overshoot with SW9 at cold start and with a hot restart; must stay under 3.6 V. |
| 3 | **USB / battery backfeed** | BQ25185 power path handles it; R68 (0R, DNP) is a deliberate switch-bypass link. | Keep R68 DNP. Verify SYS behaviour with USB present and no battery. |
| 4 | **NFC boost fault / OV** | TPS61023 FB from R44 732k / R45 100k. **No output clamp.** An open R44 drives the boost to max duty. | Add a TVS/zener clamp on `NFC_5V_PA_PENDING` sized under U9's VDD abs max. Verify shutdown pass-through (§11). |
| 5 | **Speaker amplifier faults** | MAX98357A drives an off-board speaker through J6. **No output filter, no series protection.** | Confirm the part's short-circuit and thermal-shutdown coverage for OUT+/OUT−/OUT-to-GND; add the EMI filter (§9); make the speaker harness assembly-proof. |
| 6 | **Accessory power backfeed** | `ACC_3V3_SW` from TPS22918 — **no reverse blocking**. R49/R50 give a second path onto the bus. | Add reverse-blocking or a series Schottky + TVS. **`+3V3` and `ACC_3V3_SW` header pins currently have no ESD device at all** (D2-D7 cover signals only) — add one. |
| 7 | **GPIO contention** | XGPIO 100R series (33 mA worst case — **above the TCA9535's 25 mA sink rating**); FAST_IO 470R (7 mA, good); WAKE 330R; ext-I²C 22R behind U16. | Raise XGPIO series to ≥150R so a hard short stays inside the expander's absolute-max, or accept and document. |
| 8 | **WAKE line can be held low by a faulty accessory** | **Requirement not implemented.** §8c mandates *"an open-drain buffer/gate powered from switched accessory power"* on the header's WAKE leg. Measured: `WAKE_ATTN_N_HDR` is only `R66` 330R to `WAKE_INT_N`, plus DNP ESD `D7`. With `R3` 10k pulling up, a shorted accessory pin divides `WAKE_INT_N` to ≈0.1 V and **permanently blocks internal button wake** — the unit appears dead to its own buttons. | **Implement the gate.** This is a functional-safety requirement the frozen design silently dropped. |
| 9 | **Unpowered-device signal injection** | (a) U9 VDD_IO powered with core unpowered — §11. (b) An accessory unpowered while XGPIO drive high — mitigated by series resistors + `ACC_PWR_EN` sequencing, but hardware cannot enforce firmware ordering. | Fix (a) architecturally. For (b), keep the §8c sequence as a firmware contract and publish it. |
| 10 | **Bad startup sequencing** | **Verified good.** All seven safety-relevant U2/U3 control nets have external safe-state pulls: R12 `TOUCH_RST_N`↓, R13 `SX1262_RST_N`↓, R14 `NFC_5V_EN`↓, R15 `AMP_SD_MODE`↓, R16 `DISP_RST_N`↓, R17 `ACC_PWR_EN`↓, R74 `SX1262_RXEN`↓. TCA9535 has no internal pull-ups, so these are the only defence. | Keep every one. Any new U2/U3 control signal in v2 **must** arrive with its pull. Preserve the output-latch-before-direction firmware rule. |
| 11 | **Missing strap pull** | `BMI270_INT1_STRAP` carries only R18 (220R series), TP3 and U1.15 — **no pull-up/pull-down defining the GPIO3 boot level**, which §6 declared mandatory. Hazard is currently low (the S3 ignores the GPIO3 strap unless the `JTAG_SEL_ENABLE` eFuse is burned), but it leaves a CMOS input floating at reset. | Add the pull. Configure BMI270 INT1 open-drain. Run the 50-100 cold-boot-with-motion validation before freeze. |
| 12 | **Thermal overload** | BQ25185 is **linear**: (5 V − 3.6 V) × 0.5 A ≈ 0.7 W in a 2.2 × 2 mm WSON-10, inside a sealed enclosure. | Start at ≤500 mA charge current. Raise only after enclosure thermal test. Gate on measured case temperature. |
| 13 | **Footprint / pin-mapping errors** | Several project-library footprints are custom or unverified: TCA9535PWR (symbol/footprint pair flagged "intended, not verified"), `J5` Samtec (parameterised on B = 2.54 mm, **needs vendor-drawing confirmation**), `ST25R3916_AQET`, `MK1` custom pad + GND ring, `Ebyte_E07/E22`, `Coilcraft_XFL4020`, `TI_TPS63020_DSJ`, `MAX17048_T822`, `Bosch BMI270`, `Hirose_FH69-50S`. | **Full footprint-vs-datasheet audit before layout.** Include a per-footprint pad-overlap assertion (KiCad pad angle is absolute — never add the footprint rotation). |
| 14 | **RF TX peak-current brownout** | Concurrent worst case on `+3V3`: Wi-Fi TX bursts >400 mA, SX1262 +22 dBm ≈ 120 mA, backlight ≈ 60 mA, amp peaks ≈ 410 mA, IR LED 108 mA (or 300-1000 mA if raised), NFC boost input 400-500 mA. **Doc 13's 640 mA figure excludes NFC, IR and the amp.** | Re-derive the budget with all loads. **Gate:** measure `+3V3` droop under simultaneous Wi-Fi TX + audio + backlight + NFC field-on, accounting for DC-bias-derated output caps. |
| 15 | **External connector abuse** | `J5` is an **unkeyed, unshrouded 0.1″ 2×13 pin header**. One-row mis-insertion puts `+3V3` on a signal pin. | v2 connector must be **keyed, shrouded, polarised and recessed**. Treat as an electrical requirement. |
| 16 | **No charge / VBUS telemetry** | Measured: `BQ25185_STAT1` → **TP6 only**; `STAT2` → **TP7 only**; `MAX17048_ALRT_N` → **TP11 only**. No VBUS-present sense anywhere. The product cannot report charging state or plug-in from the charger. | Route STAT1/STAT2 to the freed **U2.P16** and **U2.P17**; add a VBUS divider to a spare input. |

---

## 13. Mechanical interfaces that must be frozen before placement

**Current status is the headline risk.** From Field Slate v5's own authority table:

```
PCB_OUTLINE_MM: 155 x 74        ENCLOSURE_EXTERNAL_MM: 160 x 80 x 23
INTERNAL_CAVITY_MM: not published    WALL_THICKNESS_MM: not published
PCB_FIT_STATUS: UNVERIFIED
```

160 × 80 × 23 mm is an **external** target. The +5 mm / +6 mm nominal difference is the *entire* budget for two walls, bosses, ribs, tolerances, button mechanisms and connector clearances per axis — roughly 2.5 mm and 3.0 mm per side, which a 2 mm wall alone consumes. `tools/check_mechanical_consistency.py` correctly refuses to compute fit from external dimensions.

The root cause is recorded and must not repeat: **v3 required the envelope to drive one PCB revision, and that reconciliation was never performed.** Full Beta v2 is where it gets performed.

**Must be published and frozen before any v2 placement:**

| # | interface | why it gates placement |
|---|---|---|
| 1 | **Internal cavity X/Y/Z** and **wall thickness** | Nothing else can be checked without them |
| 2 | **PCB-to-wall clearance** and **board outline** | v2 outline is a *derived* number, not 155 × 74 inherited |
| 3 | **Mounting boss positions + keepout cylinders** | Determines routable area before, not after, routing |
| 4 | **Battery volume, position and its Z-stack** | Drives cavity depth *and* the NFC coil/shield decision |
| 5 | **NFC keepout: rear coil area, ferrite shield layer, battery offset** | Cannot be added later; it defines rear-half floorplan |
| 6 | **Speaker volume, back cavity and rear opening** | Sets J6 position and the `SPK_P/N` route away from RF |
| 7 | **Microphone port geometry + acoustic seal** | ICS-43434 is bottom-port; the front opening must align to the pad |
| 8 | **IR geometry** — 5 mm THT LED axis, TSOP window, opaque barrier | Both are THT parts on the top crown; they fix board edge geometry |
| 9 | **External antenna connector position + internal antenna keepouts** | 433/915/Wi-Fi zoning; the top crown must serve antenna and IR without conflict |
| 10 | **20-pin connector position, keying, recess depth, right-side exit** | Field Slate v5 already requires the U3/J5 cluster be placed *before routing begins* |
| 11 | **Bottom face: microSD + USB-C positions** | Connector-to-wall tolerance |
| 12 | **Front face: display window, D-pad/A/B actuators, mic opening** | Button dome stack-up sets the board's Z budget |
| 13 | **Hidden/recessed BOOT access geometry** | Tool-access hole vs. actuator |

**External antenna capability is an ADD with a design choice attached.** There is currently **no board-level RF connector, no RF trace, and no matching network** — both radios use module-mounted IPEX with hidden flex antennas (FXP450 / FXP890, u.FL / MHF I). Two paths:
- **(a) u.FL pigtail from the module IPEX to a panel-mount SMA/RP-SMA.** Preserves the "no RF on the main PCB" doctrine, adds no controlled-impedance routing, costs insertion loss and a mechanical bulkhead. **Recommended.**
- **(b) Board-level RF connector.** Requires controlled-impedance routing and matching on the main PCB — a scope the RF plan deliberately avoided. Only justify this if the industrial design demands it.

---

## 14. Carry forward from Beta-DM unchanged

These are validated, MPN-resolved and already fully routed on the DM. Do not re-derive them.

| ref | part | MPN |
|---|---|---|
| U1 | ESP32-S3-WROOM-1 | ESP32-S3-WROOM-1-N16R8 |
| MK1 | I²S MEMS mic **(and its custom footprint)** | ICS-43434 |
| U2, U3 | I²C GPIO expanders | TCA9535PWR |
| U4 | IMU | BMI270 |
| U7 | 433 MHz module | E07-400M10S |
| U8 | 915 MHz LoRa module | E22-900M22S |
| U10 | USB ESD | USBLC6-2SC6 |
| U11 | Charger + power path | BQ25185DLHR |
| U12 | 3V3 buck-boost | TPS63020DSJR |
| U14 | Fuel gauge | MAX17048G+T10 |
| U17 | Backlight boost | TPS61169DCKR |
| L1 / L3 | Inductors | XFL4020-152MEC / XFL4020-472MEC |
| C24 | SYS bulk — **DC-bias closed out**, 4.677 µF @ 4.5 V (−52.3 %), 4.21× margin | GRM188R61E106KA73D |
| J1 | 50-pin display FPC | FH69-50S-0.5SH |
| J2 | microSD | Molex 5025700893 |
| J3 | USB-C receptacle | USB4105-GF-A-120 |
| J4 | Battery | B2B-PH-K-S(LF)(SN) |
| SW2-SW7 | D-pad + A + B | PTS645SM43SMTR92LFS |
| SW9 | Power switch | JS102011SAQN |
| D8 | Backlight schottky | NSR0240HT1G |
| — | Display module | CH280QV10-CT (off-board) |
| — | Antennas | Taoglas FXP450.07.0100C / FXP890.07.0100C (**u.FL / MHF I only — MHF II does not mate**) |

Also carry forward as *methodology*, not parts: the safe-state pull discipline, the output-latch-before-direction rule, the reserved I²C address table (0x20, 0x21, 0x36, 0x38, 0x68), the POFV via-fill control, the 100 kHz→400 kHz I²C bring-up rule, and `tools/check_mechanical_consistency.py`.

---

## 15. From frozen Full Beta — require re-verification, not blind reuse

| ref | part | why |
|---|---|---|
| **U9** | ST25R3916-AQET | Rail architecture defect (VDD on the boosted rail while VDD_IO is at 3.3 V); custom footprint unverified; **no crystal exists**; 13 dangling `*_TBD` nets |
| **U13 + L2 + R44/R45 + C34/C35** | TPS61023 NFC boost | Shutdown pass-through unverified; no output OVP clamp; power budget not derived |
| **U16** | TCA9517ADGKR | Partial-power-down / no-back-power behaviour is the stated selection criterion and is **unproven for this part** |
| **U15** | TPS22918DBVR | No reverse blocking on `ACC_3V3_SW` |
| **U5 + J6 + LS1** | MAX98357A speaker chain | Topology correct; **no output EMI filter**; GAIN strap unconfirmed; peak current not in the budget; LS1 SKU still TBD |
| **D1, Q1, R22-R24, C12** | IR TX | Drive current too low and taken from `+3V3`; both escape routes were unroutable on the frozen placement |
| **U6, R21, C11** | IR RX | `U1.36` had **no single-object release**; optical isolation from D1 not designed |
| **D2-D7** | ESD arrays | Correct devices, but coverage gaps: no protection on the header's `+3V3` or `ACC_3V3_SW` |
| **R66 / WAKE leg** | 330R series only | The mandated open-drain gate was never implemented |
| **J5** | Samtec TSW-113-08-G-D-RA | Being replaced; its footprint's B = 2.54 mm parameterisation was never vendor-confirmed |
| **RGB_R/G/B_CTL** | — | Nets and U2 pins exist; **no LED part exists**; 3 dangling labels |
| **ROOTPROBE_IRQ_READY_N** | — | U2.P17 + pull-up only; **no J5 pin** — RootProbe cannot connect as drawn |
| **Reverse-polarity block** | LTC4368-1 candidate | Never drawn; explicitly marked DO NOT RELEASE TO FAB |

---

## 16. Proposed schematic migration order

Derive from Beta-DM. Each step ends with an ERC pass and a net-count diff against the previous step.

1. **Fork** `hardware/beta-dm/` → `hardware/beta-v2/`, project rename only, prove byte-equivalence exactly as the Beta-DM fork did. *(Not yet — awaiting CTO approval.)*
2. **Power tree first, because it holds the blocker.** Draw reverse-polarity protection between `BAT_CONNECTOR_P` and `BAT_PROTECTED_P`. Add `+3V3` overshoot instrumentation, VBUS-present sense, `ACC_3V3_SW` reverse blocking.
3. **MCU pin remap.** Correct the doc/schematic parity defect. Execute the GPIO18/GPIO46 reclaim (`NFC_IRQ` → GPIO46). Decide whether `SX1262_DIO1` needs an RTC pin for wake-on-LoRa. Add the GPIO3 strap-defining pull.
4. **Control-signal rebalance on U2.** Remove HOME (SW8, P16). Resolve RootProbe (P17). Land `BQ25185_STAT1`/`STAT2`. Decide RGB LED: implement or delete the three nets.
5. **NFC subsystem.** Re-architect the rails (VDD from `+3V3`, boost feeds PA only). Add the 27.12 MHz crystal + loads. Add the boost OVP clamp. Leave matching/antenna as a scheduled block, not a `*_TBD` net.
6. **Audio.** Restore U5/J6. Add the output EMI filter. Confirm the GAIN strap. Lock the 16 kHz/16-bit shared-I²S firmware contract.
7. **IR.** Restore D1/Q1/U6. Move the LED to SYS, resize for 300-1000 mA, add local bulk. Add the optical-isolation note as a mechanical constraint.
8. **New 20-pin community connector sheet** per C2. Series resistors sized (XGPIO ≥150R), ESD on every pin **including the two power pins**, the WAKE open-drain gate implemented, `NATIVE_B` given series + ESD, U3's four freed pins terminated as NC with pulls.
9. **External I²C** — carry U16/U15 forward only after the partial-power-down verification (§8); substitute the part if it fails.
10. **Footprint audit sweep** across every project-library footprint against vendor drawings, with the pad-overlap assertion.
11. **ERC to zero errors.** The five `label_dangling` errors at the Full Beta freeze must not survive; the three RGB nets are among them.

---

## 17. Proposed PCB / DFM gate sequence

| gate | exit criterion |
|---|---|
| **G0 — Mechanical freeze** | §13 items 1-13 published in the dimension authority table; `check_mechanical_consistency.py` reports a real fit verdict, not UNKNOWN |
| **G1 — Outline + floorplan** | v2 outline **derived from the published cavity**. Zone assignment: RF crown, NFC rear coil + shield + battery offset, speaker cavity, mic port, connector exits. Board-level RF connector decision (a) or (b) recorded |
| **G2 — Placement** | U3/J5 cluster at the right-side exit **before routing**; IR TX and IR RX escapes proven at placement time; NFC coil keepout instantiated; mounting bosses honoured |
| **G3 — Stackup + netclass** | 4-layer confirmed; NFC netclass rules written *before* routing, not deferred; power netclass widths re-derived (BAT_MAIN at 1.5 A cont. / 3.125 A OCP) |
| **G4 — Route** | Must-work set first; ratsnest to zero including GND; no pin-specific budget exceptions |
| **G5 — Copper closeout** | In1 reference plane continuous; F.Cu/B.Cu pours solid-connected; **fine-pitch GND closed by pours, SOLID connection — thermal relief fails here**; stitching complete |
| **G6 — DRC/ERC** | **0 DRC errors, 0 schematic-parity issues, 0 unconnected, 0 ERC errors.** Same-net hole-to-hole must be checked at **warning** level too — an error-only gate accepts drills that break out into each other |
| **G7 — Footprint/DFM** | Every footprint vs. vendor drawing; per-footprint pad-overlap assertion; POFV via-fill control regenerated (59 vias on DM); paste-vs-via-barrel audit |
| **G8 — BOM/CPL** | **Never regenerate blind** — eight MPNs previously lived only in the CSVs and were destroyed by regeneration. Diff every regenerated CSV against the MPN ledger before accepting |
| **G9 — Electrical first-article gates** | `+3V3` overshoot < 3.6 V; rail droop under Wi-Fi TX + audio + backlight + NFC; charger case temperature; 50-100 cold boots with motion applied during reset; GPIO46 boot-level scoped on TP2; reversed-battery-with-USB fault test |

---

## 18. Architecture blockers requiring CTO decision

1. **Reverse-polarity protection.** Not drawn; battery connector is a dead net; explicitly marked DO NOT RELEASE TO FAB. **Nothing ships without this.** Decision: approve the LTC4368-1 + back-to-back FET path, or name an alternative.
2. **20-pin GPIO count.** 14 GPIO-capable in 20 pins is not achievable without merging the SPI buses or exposing strapping pins. **C2 gives 12 (2 native + 10 expander); C1 gives 13 (1 native + 12 expander).** Which currency does the CTO want?
3. **NFC main-supply rail.** Move U9's VDD to `+3V3` and boost only the PA? This changes the boost's load and the power budget.
4. **NFC schedule.** The crystal, matching network and antenna are **undesigned**, not merely unrouted. Is NFC in v2's first fab, or a populated-later block?
5. **Software recovery — the honest answer.** Two mechanisms, and they are not interchangeable:
   - **(a) ROM download mode.** On the ESP32-S3 this *is* reachable from software: set the `FORCE_DOWNLOAD_BOOT` bit in `RTC_CNTL_OPTION1` and perform a **software** reset (not a power-on reset). The native USB-Serial-JTAG peripheral also implements a host-commanded reset-into-download-mode over the CDC control lines, which is how esptool flashes S3 boards with no auto-reset circuit. **Two hard caveats:** it requires *some* working code or a functional USB-Serial-JTAG — a blank or hard-bricked flash cannot invoke it; and **if firmware switches the native USB pins to USB-OTG (TinyUSB), the USB-Serial-JTAG leaves the bus and the host-commanded path stops working.** That is a firmware architecture decision with recovery consequences and must be locked. The physical GPIO0 path stays the last-resort recovery — which is why BOOT must remain a real, reachable switch, recessed rather than removed.
   - **(b) Firmware recovery / OTA recovery partition.** Entirely separate and entirely software: a factory partition plus OTA data, forced by a button combination sampled early in boot or an RTC-memory flag. This is the mechanism for "the app is broken", **not** for "the flash is empty". Recommend implementing both and never conflating them in UI copy.
   - **Hardware implication:** recovery today requires holding BOOT while toggling SW9 (which gates the TPS63020 EN, so it is a true power cycle). Both actuators must therefore be reachable in the same gesture — a mechanical requirement on the recessed BOOT access. There is **no reset button** on the design (EN has only R1/C1); adding one is optional and would consume no GPIO.
6. **RGB LED.** Implement it (U2.P05-07 already reserved and routed) or delete the three nets. It cannot stay dangling.
7. **RootProbe.** Complete it (needs a J5 pin for `ROOTPROBE_IRQ_READY_N`, which the 20-pin budget does not have — it would have to share WAKE) or retire it and reclaim U2.P17.
8. **Enclosure fit.** The internal cavity has **never existed** in this repository. Until it does, v2's outline cannot be derived and placement cannot start.
9. **External antenna path.** Pigtail-to-bulkhead (recommended) vs. board-level RF connector.
10. **DM bring-up skip.** If physical Beta-DM bring-up is skipped, gates G9, the TCA9517A partial-power-down check, the footprint audit and the reverse-polarity fault test become **fab-blocking**, not nice-to-have — because there is no earlier board on which they could fail cheaply.
11. **Field Slate v5 §5 correction.** The locked external layout still lists "Volume +, Volume −, Power" on the right side. Volume buttons have never existed electrically. The layout text needs a CTO-approved correction so the enclosure CAD is not driven by phantom controls.

---

## 19. Repository state — final

**No repository files were changed.**

```
$ cd P:\Vaults\ClaudeVault\AQROOT
$ git status --short
?? hardware/beta-dm/fab/AQROOT-Beta-DM-Gerbers-aa64c16.zip
?? hardware/beta/mechanical/
   branch: master   HEAD: b8b5ebdd1559083b328782f4fbbfdcce849b46d0

$ git diff --stat beta-full-reference-v1 -- hardware/beta/     # (empty)
$ git diff --stat HEAD -- hardware/beta-dm/                    # (empty)

$ cd P:\Vaults\ClaudeVault
$ git status --short
 M .claude/settings.local.json          # pre-existing at session start
   branch: master   HEAD: 1a23c76ab85c3b1708aeeb0e2419194bc40a8fbe
```

Identical to the state at session start. No edits, no creations, no deletions, no renames, no commits, no formatting, no KiCad writes, no cleaning of untracked files. The only files written this session were two read-only parser scripts in the session scratchpad (`u1map.py`, `netcount.py`, `whichnet.py`), outside the repository.

**Stopping here for CTO review.** The three items I would want answered before any further work are: **#1 reverse-polarity**, **#2 the 20-pin GPIO currency (C1 vs C2)**, and **#8 the internal cavity** — nothing downstream can be locked without them.
