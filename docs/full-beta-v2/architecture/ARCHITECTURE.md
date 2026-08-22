# AQROOT Full Beta v2 — Architecture Snapshot

Date: 2026-08-22
Status: **PRE-FREEZE.** This is a snapshot of intended architecture, not a
locked design. Nothing here authorizes a schematic or PCB edit.

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

---

## USER INTERFACE

| element | implementation |
|---|---|
| **TFT / touch** | **3.5 inch 320×480 IPS + capacitive touch (D-072).** Leading candidate **CH350HV40A-CT** (56.54 × 84.96 × 3.97 mm, active 48.96 × 73.44, ILI9488, 6-LED backlight) — **MPN NOT LOCKED (M-06)**: vendor quotes pitch as a range and never names the CTP. **ST7796S-class preferred** — ILI9488 cannot send RGB565 over SPI. **`J1` is NOT locked**; compatibility of the old FH69-50S-0.5SH with the 2.8″ panel is **UNPROVEN**. Backlight via `U17` TPS61169 — `RSET` must be re-derived for 6 LEDs (M-07). |
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
   BAT_CONNECTOR_P ─X─ [ REVERSE POLARITY: DOES NOT EXIST ] ─X─ BAT_PROTECTED_P
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
                                        (NFC PA rail) TPS61023 boost ─> NFC_5V_PA
```

| block | part | notes |
|---|---|---|
| Charger / power path | `U11` BQ25185DLHR | Linear. Thermals matter in a sealed enclosure; start at 500 mA charge current. |
| 3V3 rail | `U12` TPS63020DSJR | Buck-boost, FB 1M / 180k = 3.28 V. EN driven by the physical switch, **never firmware** — the MCU cannot restore its own disabled rail. |
| Fuel gauge | `U14` MAX17048G+T10 | On internal I2C at 0x36. ALRT reaches a test point only. |
| **Reverse polarity (main path)** | **LTC4368-1 + P2: TWO back-to-back N-FET stages in TWO SEPARATE PACKAGES** (4 FETs) + R_SENSE 15 mΩ + R_GATE 22 kΩ + **C_GATE 4.7 nF** + OV divider + RETRY→GND + SHDN pull-up to VIN + FAULT + **≈5 A backstop fuse** + secondary clamp | **Single-FET-short tolerant by isolation** (D-068 met). VIN on the **cell side**. `-1` suffix load-bearing: `-2` trips at −3 mV and blocks charging. **UV deliberately UNUSED** (510 kΩ to VIN) — using it would deepen the dead-cell lockout. Stages must not share a package: two die on one leadframe are not independent. |
| **Dead-cell recovery** | **Autonomous, hardware-qualified** (D-065). VBUS-supplied · ratiometric bridge polarity comparator (trip at V_BAT = 0, supply-independent) · handoff comparator · **LTC4368 `FAULT` as a third series qualifier** · P-FET + series Schottky · **5–10 mA** | **No firmware dependency** — works with blank/corrupted flash. Zero battery-side standby (dead by construction without USB). Bounded to ≈13 mA into a reversed cell under any single failure |
| **NFC supply** | **`+3V3` direct on the first build**, with a DNP TPS61023 boost branch behind a 0 Ω source selector | D-055 / D-056. Two mutually exclusive links; sources can never be shorted. |
| Switched accessory rail | **`TPS22950C`** | Replaces TPS22918, which has no reverse blocking, no current limit and no thermal shutdown. |

**Safe-state discipline (carry forward).** Both TCA9535 expanders power up with
all ports high-Z, so every safety-relevant control net carries an external pull
forcing the safe state. Seven exist and were verified present: touch reset,
SX1262 reset, NFC boost enable, amp shutdown, display reset, accessory power
enable, SX1262 RX enable. **Any new control signal in v2 must arrive with its
pull.**

---

## COMMUNITY EXPANSION

| item | status |
|---|---|
| Pin count | **20 pins.** CTO-locked (D-059). |
| Allocation | **11 XGPIO + 2 native + 2 I²C + 1 WAKE/ATTN + 1 switched accessory 3V3 + 3 GND = 20.** No permanent raw `+3V3` (D-057). No duplicate GPIO. |
| Native pair | **GPIO38 (`NATIVE_A`) + GPIO47 (`NATIVE_B`) — LOCKED** (D-063). GPIO43 removed from the connector (ROM UART traffic every reset) and becomes an internal debug test pad. DIO1 level-hold **confirmed** from Semtech §13.3.4. |
| Expanders | **NXP PCAL9535APW,118** replaces TCA9535PWR on **both** `U2` and `U3` (D-061). Pin-for-pin against TCA9535 PW; land-pattern audit still required pre-fab. Firmware **must** unmask interrupts explicitly — they power up masked. |
| External I2C | **Retained**, behind `U16` TCA9517A whose B-side supply is the switched accessory rail — verified high-Z when unpowered (SCPS245E). |
| Switched accessory power | **TPS22950C**, leaded SOT-23-thin: RCB, adjustable limit, short-circuit and thermal protection, 500 kΩ internal pull-down **plus a mandatory external pull-down**. R<sub>ILIM</sub> 600–800 mA recommended; not locked. |
| Mechanical | **Keyed, shrouded/polarized and recessed**, right-side exit. |
| Native vs expander | Must be documented distinctly everywhere. Expander GPIO are I2C-mediated: roughly 70 microseconds per output change at 400 kHz, with input-change latency of hundreds of microseconds and no source register. They cannot do UART, SPI, PWM, RMT/IR, 1-Wire or WS2812. |

---

## Known Architecture Defects / Open Questions

Every item below is a finding from the 2026-08-22 pre-design audit. None is
speculative; each cites what was measured.

### Blocking

| # | defect | evidence | disposition |
|---|---|---|---|
| 1 | **Reverse-polarity gap.** `BAT_CONNECTOR_P` has exactly one pad (`J4.1`). Nothing bridges it to `BAT_PROTECTED_P`. A board built as-is will not run from battery at all and has no defence against a reversed pack. | PCB pad-to-net map | Pending P-01 |
| 2 | **NFC clock / matching / antenna incomplete.** No 27.12 MHz crystal exists anywhere in the BOM. No matching network. No antenna. 13 nets on `U9` have exactly one pad: XIN, XOUT, RFO1, RFO2, RFI1, RFI2, AAT_A, AAT_B, EXT_LM, CSI, CSO, MCU_CLK. | 13 single-pad nets on `U9` | Pending P-04 |
| 3 | **Enclosure internal cavity unpublished.** `INTERNAL_CAVITY_MM: not published`. `PCB_FIT_STATUS: UNVERIFIED`. The v2 outline is a derived number and cannot be derived. | Field Slate v5 authority table | Pending P-07 |

### Architecture defects to fix in migration

| # | defect | evidence | disposition |
|---|---|---|---|
| 4 | **NFC supply sequencing.** **REVISED 2026-08-22 by datasheet verification.** The rail *assignment* is **correct**: DS12484 Rev 3 p. 39 requires VDD (pin 8) and VDD_TX (pin 10) to share one supply, capped at ±0.2 V operating, with VDD_IO (pin 1) independent at 1.65–5.5 V. The earlier "rail split" recommendation was wrong and is withdrawn. The **real** defect is sequencing: TPS61023 true load disconnect is confirmed, so with the boost off VDD = VDD_TX = 0 V while VDD_IO = 3.3 V — below the 2.4 V VDD minimum and nowhere authorised. | DS12484 Rev 3 Tables 2 / 118 / 119; SLVSF14B §7.3.2 | **Pending P-10** — N1 (3.3 V-only NFC, delete the boost) recommended |
| 5 | **Accessory power reverse blocking absent.** The accessory rail comes from a plain NMOS load switch with no reverse blocking; an accessory back-driving it pushes current through the body diode into `+3V3`, and the external I2C pull-ups referenced to that rail give a second path. | Load-switch topology + pull-up references | Fix in migration |
| 6 | **WAKE isolation missing.** The mandated open-drain gate powered from switched accessory power was never implemented. The header leg is only a 330R series resistor. A shorted accessory pin divides the wake net to roughly 0.1 V and **permanently blocks internal button wake** — the unit appears dead to its own buttons. | `WAKE_ATTN_N_HDR` = `D7.1`, `J5.13`, `R66.2` | Fix in migration |
| 7 | **GPIO3 strap definition missing.** The pin map declared a strap-defining pull mandatory. The net carries only a 220R series resistor, a test pad and the MCU pin. Hazard is currently low because the S3 ignores the GPIO3 strap unless the `JTAG_SEL_ENABLE` eFuse is burned, but it leaves a CMOS input floating at reset. | `BMI270_INT1_STRAP` = `R18.2`, `TP3.1`, `U1.15` | Fix in migration |

### Resource and documentation defects

| # | defect | evidence | disposition |
|---|---|---|---|
| 8 | **No free native GPIO.** 29 assigned + 2 strapping test pads + 2 USB = 31 of 31 usable. Zero margin. At most one additional safe native pin is reclaimable without an architectural change. | U1 pad map | Constrains P-02 |
| 9 | **GPIO18 / GPIO38 documentation mismatch.** The pin map states GPIO18 = SX1262 DIO1 and GPIO38 = NFC IRQ. The hardware is the reverse. | U1 pad map decoded against the WROOM-1 pin table | Fix docs + hardware in migration |
| 10 | **Possible LoRa wake defect.** Only GPIO0-21 are RTC GPIO on the S3. `SX1262_DIO1` sits on GPIO38, so it cannot be an `ext0`/`ext1` deep-sleep wake source — wake-on-LoRa-packet is impossible in the current pinout. | Consequence of defect 9 | Pending P-09 |
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
| Display size / envelope | **3.5 inch**; module ≤ 60 × 90 × 4.5 mm | **LOCKED** (D-072) / TARGET |
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
