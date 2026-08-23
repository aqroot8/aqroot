# AQROOT Full Beta v2 — Architecture Snapshot

Date: 2026-08-23 (NFC matching closeout, FBV2-S1-004C)
Status: **PRE-FREEZE.** This is a snapshot of intended architecture, not a
locked design. Nothing here authorizes a schematic or PCB edit.

**Four blocks are no longer intent.** As of 2026-08-23 the **power tree**, the
**MCU core**, the **display / touch / microSD** sheet and the **radios / NFC** sheet are
CAPTURED in `01_power_tree.kicad_sch`, `02_mcu_core.kicad_sch`,
`03_spi_a_display_sd.kicad_sch` and `04_spi_b_radios_nfc.kicad_sch`
(FBV2-S1-001 … FBV2-S1-004). Every other block on this page is still intent only, and
the PCB is untouched.

> **RF architecture locked 2026-08-23 (D-118).** 433 MHz is an **internal** Taoglas
> `FXP450.07.0100C` flex on the `U7` IPEX socket; 915 MHz is **external**, `U8` IPEX to a
> pigtail to a **top-panel SMA female bulkhead**. **Neither band has a board RF trace, a
> matching network, an RF switch or a diplexer.** This supersedes the internal-FXP890 plan
> for 915 MHz in `12 - RF and Antenna Plan v0.1`.
>
> **NFC stopped being a placeholder.** A real 27.12 MHz crystal and a real differential
> matching topology exist (D-123 / D-124), with every value labelled `TUNE` because they
> cannot be finalised without a measured antenna. **Zero `*_TBD` nets remain in the
> project.**
>
> **NFC IC and antenna LOCKED 2026-08-23 (D-126 … D-128).** `ST25R3916-AQET`, non-B
> (**P-17 closed**). Antenna: **Taoglas `FXC.46.52.0075X.A.dg`** — 13.56 MHz, 46 mm
> circular flex, 0.27 mm with integrated ferrite, 3M peel-and-stick, 75 mm 28 AWG twisted
> pair, ACH(F) — **off the main PCB** (**B-53 closed**), landing on **`J7` JST
> `BM02B-ACHSS-GAN-ETF`** whose `ACHR-02V-S` mate is the antenna's own housing, so the
> antenna is **replaceable without soldering**. **B-06 is closed**: NFC is no longer
> undesigned, only untuned.
>
> **Antenna variant corrected 2026-08-23 (D-131): the locked part is the `.B.dg` REVERSE
> FERRITE version.** It bonds **adhesive-side to the inner rear shell** and reads outward
> with the **ferrite facing inward** at the PCB and battery. The `.A.dg` version is for
> bonding onto a PCB or component surface and would put the ferrite between the coil and
> the tag. **First-build matching set calculated (D-133 / D-134)**: target ≈ 36 Ω
> differential derived from the NFC current budget, `Q` ≈ 25, EMC cut-off **20.1 MHz**. **An
> RFI over-drive defect was found and fixed (D-135)** — the placeholder divider would have
> put ≈ 4.4 V pk-pk on a 3.0 V rail. **Every value is a CALCULATED FIRST-BUILD VALUE, not a
> final tuned value**; final tuning happens with the shell, PCB and battery installed.

> **The display symbol was wrong until 2026-08-23.** `J1` carried the 2.8-inch panel's
> pin table while its Value already read FH69: the backlight anode and cathode were
> reversed and the SPI clock and D/C lines were swapped. Both faults were
> dead-on-arrival and invisible to ERC. See D-112.

The measured pin ledger and the full strapping-pin audit now live in
[GPIO_LEDGER.md](GPIO_LEDGER.md) and are read from the schematic, not transcribed.

Authority: [CTO_DECISIONS.md](../CTO_DECISIONS.md) outranks this document.
Measured facts come from the 2026-08-22 pre-design audit at repository HEAD
`b8b5ebdd1559083b328782f4fbbfdcce849b46d0`.

---

## COMPUTE

**ESP32-S3-WROOM-1-N16R8** (`U1`)

- 16 MB flash, 8 MB octal PSRAM.
- GPIO35/36/37 are **unusable** on the R8 variant (octal PSRAM) and are left NC.
- Native USB on GPIO19/20 (D−/D+), each through a 22R series resistor at the MCU
  end. No PD, no CC controller — CC1/CC2 are static 5.1k pull-downs.
- Console runs over native USB-CDC, which is what frees GPIO43/44.
- **CAPTURED 2026-08-23 (FBV2-S1-002).** `GPIO38 = NATIVE_A`, `GPIO47 = NATIVE_B` —
  the only two connector contacts with a direct MCU path. `GPIO46 = DISP_BL_CTL`, with
  a dedicated 10 k strap pull-down, a 0 R isolation link to the TPS61169 `CTRL` and a
  strap test pad; GPIO46 **must** read LOW at reset or Joint Download Boot is
  unreachable. `GPIO43` is **withdrawn from the community port** and is internal UART0
  TXD only, so **UART0 is TX-only** (GPIO44 is IR RX) and ROM download recovery runs
  over the native USB Serial/JTAG, never over UART0. `GPIO3` now has its strap-defining
  10 k pull-down.
- The service interface is the **native USB Serial/JTAG**: one USB-C cable for console,
  ROM download and JTAG debug. No debug connector, no debug IC, no JTAG header.

---

## USER INTERFACE

| element | implementation |
|---|---|
| **TFT / touch** | **LOCKED (D-074…D-078).** **EastRising `ER-TFT035IPS-6`** 3.5″ IPS 320×480, **ILI9488** (COG), with **`ER-TPC035-6`** capacitive touch, **FocalTech `FT6236` @ I²C 0x38**. Assembled outline **56.54 × 84.96 × 3.95 ± 0.25 mm**, active 48.96 × 73.44 mm. **One 50-pin FPC — 0.50 mm pitch, bottom contact, 0.30 ± 0.03 mm thick, 25.5 ± 0.15 mm wide** — carries display *and* touch (touch on pins 44–47). **`J1` = Hirose `FH69-50S-0.5SH`** (top *and* bottom 2-point contact, accepts 0.30 ± 0.05 mm FPC), laid out on the **FH12/FH52E standard land pattern** so `FH52E-50S-0.5SH` (LCSC C7465440) is a drop-in second source (D-077). ST7796S was preferred and does not exist in a documented CTP module (D-078); the cost is **+50 % SPI-A traffic**, 46 ms full frame at 80 MHz. Backlight: **6 LEDs in parallel, one anode**, 2.9–3.2 V, 120 mA max / 90 mA life point — `U17` TPS61169 retained from `+3V3`, **`R69` = 1.87 R**, **`R70`–`R73` = 4 × 33 R in parallel** (D-079). |
| **D-pad** | `SW2`-`SW5` on internal expander `U2` P10-P13. |
| **A / B** | `SW6` / `SW7` on `U2` P14 / P15. |
| **Microphone** | `MK1` ICS-43434 I2S MEMS. Front opening. |
| **Speaker** | MAX98357A-style I2S Class-D into an off-board 8 ohm speaker via `J6`. Rear opening. |
| **Power** | `SW9` SPDT hard switch on the TPS63020 enable. **Not a GPIO** — a hung or unflashed firmware can still power the unit down. |
| **Hidden / recessed BOOT** | `SW1` on GPIO0 with a 10k pull-up. Circuit unchanged; actuator becomes recessed. |

**Removed for v2:** HOME (`SW8`, frees `U2` P16). Volume Up / Down are removed
from the product concept but never existed electrically.

---

## STORAGE / USB

| element | implementation |
|---|---|
| **microSD** | `J2` Molex 5025700893 on SPI-A with its own CS (GPIO48). Card-detect exists as a connector pad but is **not wired**. |
| **USB-C** | `J3` GCT USB4105-GF-A-120, 16-contact, sink/UFP, 5 V only. `U10` USBLC6-2SC6 ESD. No PD, no VCONN, no source role, SBU1/SBU2 NC. |

---

## RF

| radio | implementation | antenna |
|---|---|---|
| **Wi-Fi / BLE** | ESP32-S3-WROOM-1 module | Module onboard PCB antenna; enclosure keepout only |
| **433 MHz** | `U7` Ebyte E07-400M10S (CC1101) on SPI-B | Module IPEX; Taoglas FXP450 flex (u.FL / MHF I only) |
| **915 MHz LoRa** | `U8` Ebyte E22-900M22S (SX1262) on SPI-B | Module IPEX; Taoglas FXP890 flex (u.FL / MHF I only) |
| **NFC** | `U9` ST25R3916-AQET on SPI-B + boost — **architecture unresolved** | **Undesigned** |
| **IR TX** | `D1` TSAL6200 5 mm THT, low-side `Q1` AO3400A, RMT on GPIO16 | Top crown aperture |
| **IR RX** | `U6` TSOP38238 with supply RC filter, RMT capture on GPIO44 | Top crown aperture, optically isolated from `D1` |

**Board-level RF scope:** by design, no 433/915 RF signal reaches the main PCB —
no matching networks, no RF traces, no controlled-impedance routing. NFC is the
only board-level RF design task, and it does not yet exist.

**External antenna capability is an ADD.** No board-level RF connector exists
today. Preferred path is a u.FL pigtail from the module IPEX to a panel-mount
SMA/RP-SMA, which preserves the no-RF-on-main-PCB doctrine. Pending P-08.

---

## SENSORS

**`U4` BMI270 IMU** on internal I2C at 0x68, with INT1 through a 220R series
resistor into GPIO3 (a strapping pin) and a test pad on the net.

---

## POWER

```
USB-C 5V ─> USBLC6 ESD ─> USB_VBUS_RAW ─> [0R] ─> USB_VBUS_CHG
                                                      |
                                          BQ25185 (linear charger + power path)
                                                      |
   BAT_CONNECTOR_P ─> F1 5A ─> BAT_RAW ─> Q2 ═ Q3 ─> R75 15m ─> BAT_PROTECTED_P
             (CAPTURED, FBV2-S1-001: LTC4368-1 U18, P2, two packages;
              autonomous USB-powered dead-cell recovery on U19)
                                                      |         |
                                                      |    MAX17048 fuel gauge
                                                      |
                                              BQ25185_SYS (~4.5V)
                                                      |
                              SW9 hard switch ─> TPS63020 EN
                                                      |
                                            TPS63020 buck-boost ─> +3V3
                                                      |
                                    MCU, radios, display logic, I2C, audio, NFC VDD_IO
                                                      |
                                        (NFC PA rail) TPS61023 boost ─> NFC_5V_PA  [DNP on build 1]
                                                      |
                              BQ25185_SYS ─> TPS61023 boost 5.0V ─> TPS22950C ─> ACC_5V_SW
                              +3V3        ─> TPS22950C ─────────────────────> ACC_3V3_SW
```

| block | part | notes |
|---|---|---|
| Charger / power path | `U11` BQ25185DLHR | Linear. Thermals matter in a sealed enclosure; start at 500 mA charge current. |
| 3V3 rail | `U12` TPS63020DSJR | Buck-boost, FB 1M / 180k = 3.28 V. EN driven by the physical switch, **never firmware** — the MCU cannot restore its own disabled rail. |
| Fuel gauge | `U14` MAX17048G+T10 | On internal I2C at 0x36. ALRT reaches a test point only. |
| **Reverse polarity (main path)** | **LTC4368-1 + P2: TWO back-to-back N-FET stages in TWO SEPARATE PACKAGES** (4 FETs) + R_SENSE 15 mΩ + R_GATE 22 kΩ + **C_GATE 4.7 nF** + OV divider + RETRY→GND + SHDN pull-up to VIN + FAULT + **≈5 A backstop fuse** + secondary clamp | **Single-FET-short tolerant by isolation** (D-068 met). VIN on the **cell side**. `-1` suffix load-bearing: `-2` trips at −3 mV and blocks charging. **UV deliberately UNUSED** (510 kΩ to VIN) — using it would deepen the dead-cell lockout. Stages must not share a package: two die on one leadframe are not independent. |
| **Dead-cell recovery** | **Autonomous, hardware-qualified** (D-065). VBUS-supplied · ratiometric bridge polarity comparator (trip at V_BAT = 0, supply-independent) · handoff comparator · **LTC4368 `FAULT` as a third series qualifier** · P-FET + series Schottky · **5–10 mA** | **No firmware dependency** — works with blank/corrupted flash. Zero battery-side standby (dead by construction without USB). Bounded to ≈13 mA into a reversed cell under any single failure |
| **NFC supply** | **`+3V3` direct on the first build**, with a DNP TPS61023 boost branch behind a 0 Ω source selector | D-055 / D-056. Two mutually exclusive links; sources can never be shorted. |
| Switched accessory rail (3.3 V) | **`TPS22950C`** | Replaces TPS22918, which has no reverse blocking, no current limit and no thermal shutdown. `VIN` 1.8-5.5 V, RCB, `ILIM` 0.5-3.5 A, auto-retry, TSD 170 C, `FLT`. `R_ILIM` 1.5 k recommended (D-086). |
| **Accessory 5 V rail (NEW)** | **`TPS61023` (2nd instance) + `TPS22950C` (2nd instance)** | `SYS` -> 5.0 V boost -> protected switch -> `ACC_5V_SW`. Separate from USB VBUS and from the NFC fallback. Loads `SYS`, **not** `+3V3` (D-087/D-088). |

**Safe-state discipline (carry forward).** Both TCA9535 expanders power up with
all ports high-Z, so every safety-relevant control net carries an external pull
forcing the safe state. Seven exist and were verified present: touch reset,
SX1262 reset, NFC boost enable, amp shutdown, display reset, accessory power
enable, SX1262 RX enable. **Any new control signal in v2 must arrive with its
pull.**

---

## COMMUNITY EXPANSION

> **The 20-pin architecture (D-059 / D-062) is SUPERSEDED.** Do not cite it.

| item | status |
|---|---|
| Contact count | **2 rows x 12 = 24 ACTIVE contacts.** No NC, no key contact. **LOCKED (D-081).** |
| Allocation | **10 XGPIO + 2 native + 2 I2C + 1 WAKE/ATTN + 2 switched 3.3 V + 2 switched 5 V + 4 GND + 1 `ACC_DETECT_N` = 24.** **LOCKED (D-082).** Only the rails and ground are duplicated, each one net; **no GPIO is duplicated** (D-042). No permanent raw `+3V3` (D-057). |
| **Connector** | **Samtec `BCS-112-S-D-HE`** - .100 in / 2.54 mm, 2x12, **FEMALE** Tiger Claw dual-beam receptacle, **horizontal (right-angle) entry**, through-hole, **30 uin gold**. **ACTIVE**, 385 pcs next-day from Samtec, MOQ 1, $7.31 @ 1. Body **30.48 x 8.13 x 5.33 mm**. **4.6 A/contact**, 450 VAC, -55...+125 C. Mates with any 0.64 mm square-post header whose **mating post is 4.34-6.35 mm** (reference: `TSW-112-07-L-D`, 5.84 mm post). **LOCKED (D-093).** `BCS-112-L-D-HE` (10 uin gold) is a plating-only cost-down alternate, no board change. **Harwin `M20-7881242` is REJECTED as obsolete.** |
| Keying / shroud | **From the ENCLOSURE (D-097).** Recess >= 1.5 mm deep forms the shroud; an **asymmetric rib on the upper edge only** blocks upside-down insertion; the recess is **closed at both ends** so a one-column offset is mechanically impossible; a moulded shelf and backing rib capture the body; the accessory shell bottoms on a boss so the **~33 N average insertion force** is not carried by the solder joints. The BCS polarized-position option is **not** used - it would consume a contact. |
| Footprint | **New project-library part required.** 2 x 12 PTH, **2.54 mm within a row, 7.87 +/-0.05 mm BETWEEN rows, 0.71 mm drill** (Samtec FIG 3, `BCS-1XX-XXX-D-HE`). **Not** interchangeable with a vertical 2x12 pattern (B-29). |
| Pin ordering | **LOCKED (D-084).** Odd = row A, even = row B. `1 XGPIO0 / 2 EXT_SCL / 3 ACC_3V3_SW / 4 GND / 5 XGPIO1 / 6 EXT_SDA / 7 NATIVE_A / 8 XGPIO2 / 9 GND / 10 ACC_5V_SW / 11 NATIVE_B / 12 XGPIO3 / 13 XGPIO4 / 14 WAKE_ATTN_N / 15 ACC_3V3_SW / 16 GND / 17 XGPIO5 / 18 XGPIO6 / 19 XGPIO7 / 20 XGPIO8 / 21 GND / 22 ACC_5V_SW / 23 ACC_DETECT_N / 24 XGPIO9`. |
| Mis-insertion safety | **Every power contact is vertically paired with GND**, so a row swap can only produce a current-limited rail-to-ground short - never 5 V on a logic pin. **All 3.3 V in row A, all 5 V in row B.** A one-column shift is prevented mechanically by the closed-ended recess. |
| Native pair | **GPIO38 (`NATIVE_A`) + GPIO47 (`NATIVE_B`) - LOCKED** (D-063). Both flank the GND at pin 9. |
| **Accessory detect** | `ACC_DETECT_N` (pin 23), 100 k pull-up to `+3V3`, asserted by a **single 0 Ohm link to the GND at pin 21**. **Works with both rails OFF**; **both rails are gated on it** (D-085). Also gives hot-plug interrupt/wake for free through `U3` `/INT` -> `WAKE_INT_N` -> GPIO21. |
| **3.3 V accessory rail** | `+3V3` -> **`TPS22950C`** -> `ACC_3V3_SW`. Default OFF, external 100 k pull-down mandatory, RCB, auto-retry, TSD, `FLT`. `R_ILIM` **1.5 k recommended (~0.76 A typ), not locked**; **published 400 mA continuous** on build 1 (D-086). |
| **5 V accessory rail (NEW)** | `BQ25185_SYS` -> **second `TPS61023`** at 5.0 V -> **second `TPS22950C`** -> `ACC_5V_SW`. Not USB VBUS, not the NFC fallback rail, tied to neither. `R_ILIM` **1.65 k recommended (~0.69 A typ), not locked**; **published 300 mA continuous** on build 1. Inductor 1 uH, I_sat >= 3 A (D-087). **It loads `SYS`, not `+3V3`, so it consumes none of the TPS63020's 2 A budget.** **O-3 REJECTED: no link of any kind to the NFC fallback** (D-095). |
| BOM consolidation | One `TPS22950C` MPN on both rails; `TPS61023` reused from the NFC fallback with identical passives (D-088). |
| Expanders | **NXP PCAL9535APW,118** on both `U2` and `U3` (D-061). **`U3` = 15 assigned + 1 `RESERVED_SPARE`** (D-094): `XGPIO0-9`, `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_DETECT_N`, **`ACC_POWER_FAULT_N`** (wire-OR of both `FLT`), `SX1262_RXEN`. **`U2` = 16/16, still zero spare** (B-37, half closed). |
| External I2C | **Retained**, behind `U16` TCA9517A whose B-side supply is `ACC_3V3_SW` - verified high-Z when unpowered (SCPS245E). Because that rail is now default-OFF and detect-gated, a dead accessory can no longer hang the internal bus. **Address collision remains open (P-18).** **Address `0x50` is RESERVED for an optional accessory-ID EEPROM** - protocol only, no main-board hardware, no accessory obliged to fit one (D-095). |
| **Logic safety** | **3.3 V CMOS ONLY on every signal contact.** 100 Ohm series on XGPIO and both natives, 22 Ohm on I2C, 330 Ohm on WAKE, plus a low-capacitance TVS array on the natives and I2C. **Bidirectional level translators REJECTED** (D-090). Silkscreen must say so. |
| **WAKE isolation** | N-FET pass gate between `WAKE_ATTN_N_HDR` and `WAKE_INT_N`, gate = `ACC_3V3_SW`. **Closes B-08.** Consequence: accessory wake needs the rail held up in sleep (B-36). |
| Firmware contract | **MX-1...MX-9 binding** (D-092): one high-power radio at a time, audio capped during TX, rails detect-gated and sequenced, `FLT` handled within 100 ms, low-battery cut-offs, SPI-A arbitration, interrupt masking. |
| Mechanical | **Keyed, shrouded/polarized and recessed**, right-side exit. **Z column 19.53 mm of the 23.0 mm external budget - 3.47 mm spare**, level with the control region and **no longer the sole governing column**. Insertion force **~33 N average** (peak higher); the enclosure must carry it (M-10). |
| Native vs expander | Must be documented distinctly everywhere (D-045). Expander GPIO are I2C-mediated: roughly 70 microseconds per output change at 400 kHz, input-change latency of hundreds of microseconds, no source register. They cannot do UART, SPI, PWM, RMT/IR, 1-Wire or WS2812. |

---

## Known Architecture Defects / Open Questions

Every item below is a finding from the 2026-08-22 pre-design audit. None is
speculative; each cites what was measured.

### Blocking

| # | defect | evidence | disposition |
|---|---|---|---|
| ~~1~~ | ~~**Reverse-polarity gap.**~~ **CLOSED AT SCHEMATIC LEVEL 2026-08-23 (FBV2-S1-001).** `BAT_CONNECTOR_P` = `J4.1` + `F1.1` + `TP34.1`; the full P2 chain to `BAT_PROTECTED_P` is captured with `U18` LTC4368-1, `Q2`/`Q3` in two packages, `R75` 15 mΩ sense and `D9` secondary clamp. **NOT closed at board level** — the PCB is still bit-identical to Beta-DM. | schematic netlist, `BAT_PROTECTED_P` = 10 pads | P-01 closed by D-050…D-054; captured by FBV2-S1-001 |
| ~~2~~ | ~~**NFC clock / matching / antenna incomplete.**~~ **LARGELY CLOSED 2026-08-23 (FBV2-S1-004).** `Y1` 27.12 MHz + load caps captured; the ST differential matching and RX-divider topology captured with every value `TUNE`; `AAT_A/B`, `CSI/CSO`, `EXT_LM`, `MCU_CLK` are explicit no-connects with recorded reasons. **All 13 single-pad nets are gone.** Remaining: the antenna architecture choice (**B-53**) and the tuning values (**B-48**). | netlist: zero `*_TBD` nets | P-04 answered - NFC is fitted on the first build |
| 3 | **Enclosure internal cavity unpublished.** `INTERNAL_CAVITY_MM: not published`. `PCB_FIT_STATUS: UNVERIFIED`. The v2 outline is a derived number and cannot be derived. | Field Slate v5 authority table | Pending P-07 |

### Architecture defects to fix in migration

| # | defect | evidence | disposition |
|---|---|---|---|
| 4 | **NFC supply sequencing.** **REVISED 2026-08-22 by datasheet verification.** The rail *assignment* is **correct**: DS12484 Rev 3 p. 39 requires VDD (pin 8) and VDD_TX (pin 10) to share one supply, capped at ±0.2 V operating, with VDD_IO (pin 1) independent at 1.65–5.5 V. The earlier "rail split" recommendation was wrong and is withdrawn. The **real** defect is sequencing: TPS61023 true load disconnect is confirmed, so with the boost off VDD = VDD_TX = 0 V while VDD_IO = 3.3 V — below the 2.4 V VDD minimum and nowhere authorised. | DS12484 Rev 3 Tables 2 / 118 / 119; SLVSF14B §7.3.2 | **Pending P-10** — N1 (3.3 V-only NFC, delete the boost) recommended |
| 5 | **Accessory power reverse blocking absent.** The accessory rail came from a plain NMOS load switch with no reverse blocking; an accessory back-driving it pushed current through the body diode into `+3V3`, and the external I2C pull-ups referenced to that rail gave a second path. | Load-switch topology + pull-up references | **CAPTURED on the power tree 2026-08-23 (FBV2-S1-001):** both accessory rails now use `TPS22950C` (`U20`, `U22`), whose reverse-current blocking is confirmed for the C variant (D-058), with the 5 V rail fed from `SYS` through its own `TPS61023`. **The Beta-DM `TPS22918` path on sheet `09` is untouched and still carries the defect.** |
| 6 | **WAKE isolation missing.** The mandated open-drain gate powered from switched accessory power was never implemented. The header leg is only a 330R series resistor. A shorted accessory pin divides the wake net to roughly 0.1 V and **permanently blocks internal button wake** — the unit appears dead to its own buttons. | `WAKE_ATTN_N_HDR` = `D7.1`, `J5.13`, `R66.2` | Fix in migration |
| ~~7~~ | ~~**GPIO3 strap definition missing.**~~ **CLOSED 2026-08-23 by D-109 (FBV2-S1-002)** — `R110` 10 k pull-down at the MCU pin; BMI270 `INT1` bound to push-pull active-high. Original text: **GPIO3 strap definition missing.** The pin map declared a strap-defining pull mandatory. The net carries only a 220R series resistor, a test pad and the MCU pin. Hazard is currently low because the S3 ignores the GPIO3 strap unless the `JTAG_SEL_ENABLE` eFuse is burned, but it leaves a CMOS input floating at reset. | `BMI270_INT1_STRAP` = `R18.2`, `TP3.1`, `U1.15` | Fix in migration |

### Resource and documentation defects

| # | defect | evidence | disposition |
|---|---|---|---|
| 8 | **No free native GPIO.** **Re-measured 2026-08-23: 33 of 33 usable pins assigned** (GPIO35/36/37 unusable on the R8). Zero margin. At most one additional safe native pin is reclaimable without an architectural change. | U1 pad map | Constrains P-02 |
| ~~9~~ | ~~**GPIO18 / GPIO38 documentation mismatch.**~~ **RESOLVED 2026-08-23 by D-108** — GPIO38 is now `NATIVE_A` and `SX1262_DIO1` leaves the MCU entirely (it terminates on `U2`, D-089). `NFC_IRQ` stays on GPIO18. Original text: **GPIO18 / GPIO38 documentation mismatch.** The pin map states GPIO18 = SX1262 DIO1 and GPIO38 = NFC IRQ. The hardware is the reverse. | U1 pad map decoded against the WROOM-1 pin table | Fix docs + hardware in migration |
| ~~10~~ | ~~**Possible LoRa wake defect.**~~ **RETIRED** — D-041 makes LoRa deep-sleep packet wake a non-requirement, and D-108 moves `SX1262_DIO1` off the MCU altogether. Original text: **Possible LoRa wake defect.** Only GPIO0-21 are RTC GPIO on the S3. `SX1262_DIO1` sits on GPIO38, so it cannot be an `ext0`/`ext1` deep-sleep wake source — wake-on-LoRa-packet is impossible in the current pinout. | Consequence of defect 9 | Pending P-09 |
| 11 | ~~RGB dangling design.~~ | 3 single-pad nets | **RESOLVED by D-037** — architecture removed, `U2` P05–P07 freed |
| 12 | ~~RootProbe incomplete.~~ | Net = `R11.2`, `U2.20` | **RESOLVED by D-038** — dedicated IRQ retired, `U2` P17 freed |
| 14 | **`TPS22918` has no reverse-current blocking.** Its integrated body diode conducts VOUT→VIN, so a powered accessory can back-power `+3V3` through `ACC_3V3_SW`. | TPS22918 datasheet §11 | **OPEN (B-18).** Replace with a TPS22913B/C-class switch with always-active reverse-current protection |
| 15 | **`NFC_IRQ` must never be moved to GPIO46.** ST25R3916 IRQ is active-high and latches until read over SPI; the part has no reset input, so a pending IRQ survives an ESP32 reset and would block Joint Download Boot. | ESP32-S3 DS v2.2 Table 3-3; DS12484 §4.3.1 | **CLOSED as a permanent design rule (B-19)** |
| 13 | **No charge or VBUS telemetry.** Charger status lines and the fuel-gauge alert reach test points only; no VBUS-present sense exists. The product cannot report that it is charging. | PCB pad-to-net map | Fix in migration; use freed `U2` P16/P17 |

---

---

## Mechanical — external product direction

**Volume Up and Volume Down are removed from the Full Beta v2 mechanical
requirements** (FBV2-ARCH-002). They never existed electrically; their presence
in Field Slate v5 §5 was an industrial-design leftover.

| face | contents |
|---|---|
| **Front** | display / touch, D-pad, A/B, microphone aperture |
| **Top** | panel antenna connector, IR TX/RX optical area |
| **Left** | antenna storage |
| **Right** | recessed/keyed 20-pin community connector, Power, hidden/recessed BOOT access if appropriate |
| **Bottom** | USB-C, microSD |
| **Rear** | NFC target, speaker opening, branding |

`hardware/beta/mechanical/` was not touched and remains untracked.

**The internal cavity is now derived (FBV2-MECH-001, gate FBV2-A2 PASS).**
Authoritative source: [`../mechanical/MECHANICAL_INTERFACE_SPEC.md`](../mechanical/MECHANICAL_INTERFACE_SPEC.md).

| key | value | status |
|---|---|---|
| External enclosure | **80 × 160 × 23 mm**, portrait | LOCKED |
| Internal cavity | **75.0 × 155.0 × 18.5 mm** | TARGET |
| PCB target | **70.0 × 148.0 mm** × 1.6 mm | TARGET |
| Battery envelope | **60 × 75 × 8.0 mm** (~2500–3000 mAh) | **LOCKED** (D-071) |
| Display size / envelope | **3.5 inch**; module ≤ 60 × 90 × 4.5 mm. Fitted part **56.54 × 84.96 × 4.20 max** | **LOCKED** (D-072, D-074) |
| Display MPN / FPC / connector | `ER-TFT035IPS-6` + `ER-TPC035-6`; 50-pin 0.5 mm bottom-contact 0.30 mm FPC; `J1` = `FH69-50S-0.5SH` | **LOCKED** (D-074…D-077) |
| NFC zone | **45 × 45 mm**, rear upper third, **zero battery overlap** | TARGET |
| Z verdict | **PASS** — 19.5 of 23.0 mm on the governing column | — |

**The Beta-DM 74 × 155 mm outline must not be reused** — it leaves zero clearance
in Y against the derived cavity. Verdict: **re-floorplan with a different
outline.**

---

## First-revision reworkability (D-049)

Rework provisions planned under the no-respin policy. Full rationale in the
reconciliation audit §H.

| class | items |
|---|---|
| **HIGH — include** | IR LED current-limit resistor · IR LED source-select link (`+3V3` vs `SYS`) · NFC matching network · TPS22950C R<sub>ILIM</sub> · speaker EMI-filter footprints · VBUS-sense divider · reverse-protection sense resistor |
| **MEDIUM — if area permits** | charger status pull-ups · RF module control pulls · strap/pull values · external antenna pigtail (already inherently reworkable) |
| **LOW — omit** | alternate footprints for major ICs · alternate expander footprint |

**Signal-integrity guard:** no rework provisions on the two native connector
pins, either SPI bus, the I²S group or the USB pair.

---

## Related documents

- [CTO_DECISIONS.md](../CTO_DECISIONS.md) — source of truth
- [PROGRESS.md](../PROGRESS.md) — gates and blockers
- [POWER_FAULT_STATE_TABLE.md](POWER_FAULT_STATE_TABLE.md) — **mandatory**, eleven fault cases
- [audits/2026-08-22-architecture-reconciliation.md](../audits/2026-08-22-architecture-reconciliation.md) — FBV2-ARCH-002
- [reviews/2026-08-22-independent-cto-power-nfc-review.md](../reviews/2026-08-22-independent-cto-power-nfc-review.md) — independent, **advisory**
- [audits/2026-08-22-pre-design-engineering-audit.md](../audits/2026-08-22-pre-design-engineering-audit.md) — the measurements behind every finding here
