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
| **TFT / touch** | Off-board CH280QV10-CT 2.8 inch 240x320 TFT + capacitive touch, mated through `J1` Hirose FH69-50S-0.5SH 50-pin FPC. Backlight driven by `U17` TPS61169 boost. Touch is FT6236-class on internal I2C, polled. |
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
| **Reverse polarity** | **TBD — BLOCKER** | `BAT_CONNECTOR_P` is a dead single-pad net. LTC4368-1 + back-to-back N-FETs is the candidate. Pending P-01. |
| **NFC boost** | **TBD** | `U13` TPS61023 exists but the rail architecture is wrong (see defects). Pending P-03. |
| Switched accessory rail | `U15` TPS22918 | With slew-control cap and quick-output-discharge. |

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
| Pin count | **Target 20 pins** (from 26). CTO-locked. |
| Final pinout | **TBD.** C1 / C2 / C3 proposed; none approved. Pending P-02. |
| External I2C | **Retained**, behind a buffer whose B-side supply is the switched accessory rail. Part re-verification required. |
| Switched accessory power | **Retained** unless the CTO changes it. Load switch with slew control and output discharge. |
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
| 4 | **NFC rail sequencing concern.** `U9` main supply pins 8 and 10 sit on the boosted rail while pin 1 (VDD_IO) sits on `+3V3`. With the boost in its default-off state the core is unpowered while the I/O domain is at 3.3 V — a partial-power condition that typically violates the part's VDD_IO ≤ VDD rule. Also verify whether the boost truly disconnects in shutdown; most non-isolating boosts pass VIN through to VOUT, which would contradict both the default-off claim and the zero-idle-draw argument. | `U9` pads 8/10 on `NFC_5V_PA_PENDING`, pad 1 on `+3V3` | Pending P-03 |
| 5 | **Accessory power reverse blocking absent.** The accessory rail comes from a plain NMOS load switch with no reverse blocking; an accessory back-driving it pushes current through the body diode into `+3V3`, and the external I2C pull-ups referenced to that rail give a second path. | Load-switch topology + pull-up references | Fix in migration |
| 6 | **WAKE isolation missing.** The mandated open-drain gate powered from switched accessory power was never implemented. The header leg is only a 330R series resistor. A shorted accessory pin divides the wake net to roughly 0.1 V and **permanently blocks internal button wake** — the unit appears dead to its own buttons. | `WAKE_ATTN_N_HDR` = `D7.1`, `J5.13`, `R66.2` | Fix in migration |
| 7 | **GPIO3 strap definition missing.** The pin map declared a strap-defining pull mandatory. The net carries only a 220R series resistor, a test pad and the MCU pin. Hazard is currently low because the S3 ignores the GPIO3 strap unless the `JTAG_SEL_ENABLE` eFuse is burned, but it leaves a CMOS input floating at reset. | `BMI270_INT1_STRAP` = `R18.2`, `TP3.1`, `U1.15` | Fix in migration |

### Resource and documentation defects

| # | defect | evidence | disposition |
|---|---|---|---|
| 8 | **No free native GPIO.** 29 assigned + 2 strapping test pads + 2 USB = 31 of 31 usable. Zero margin. At most one additional safe native pin is reclaimable without an architectural change. | U1 pad map | Constrains P-02 |
| 9 | **GPIO18 / GPIO38 documentation mismatch.** The pin map states GPIO18 = SX1262 DIO1 and GPIO38 = NFC IRQ. The hardware is the reverse. | U1 pad map decoded against the WROOM-1 pin table | Fix docs + hardware in migration |
| 10 | **Possible LoRa wake defect.** Only GPIO0-21 are RTC GPIO on the S3. `SX1262_DIO1` sits on GPIO38, so it cannot be an `ext0`/`ext1` deep-sleep wake source — wake-on-LoRa-packet is impossible in the current pinout. | Consequence of defect 9 | Pending P-09 |
| 11 | **RGB dangling design.** `RGB_R_CTL`, `RGB_G_CTL` and `RGB_B_CTL` each have exactly one pad (`U2` P05-P07). No LED part exists in the BOM. | 3 single-pad nets | Pending P-05 |
| 12 | **RootProbe incomplete.** `ROOTPROBE_IRQ_READY_N` reaches only a pull-up and `U2` P17. It has no header pin, so RootProbe cannot connect as drawn. | Net = `R11.2`, `U2.20` | Pending P-06 |
| 13 | **No charge or VBUS telemetry.** Charger status lines and the fuel-gauge alert reach test points only; no VBUS-present sense exists. The product cannot report that it is charging. | PCB pad-to-net map | Fix in migration; use freed `U2` P16/P17 |

---

## Related documents

- [CTO_DECISIONS.md](../CTO_DECISIONS.md) — source of truth
- [PROGRESS.md](../PROGRESS.md) — gates and blockers
- [audits/2026-08-22-pre-design-engineering-audit.md](../audits/2026-08-22-pre-design-engineering-audit.md) — the measurements behind every finding here
