# AQROOT Full Beta v2 — CTO Decisions

**Status: LIVING DOCUMENT. This is the current source of truth.**

When an older transcript, audit or architecture note conflicts with a ruling in
this file, **this file wins.** Superseded rulings are struck through and kept,
never deleted, so the history of the decision stays readable.

Established: 2026-08-22
Last updated: 2026-08-22

---

## 1. Project direction

| # | decision | date |
|---|---|---|
| D-001 | **Full Beta v2 is now the primary hardware design.** | 2026-08-22 |
| D-002 | **Beta-DM fabrication is PAUSED BEFORE PAYMENT.** The design-side release stands; no money has been committed. | 2026-08-22 |
| D-003 | **Full Beta v2 is derived from Beta-DM implementation knowledge** — its resolved MPNs, its validated blocks, its routing and DFM lessons. | 2026-08-22 |
| D-004 | **Frozen Full Beta (`beta-full-reference-v1`) is a feature / reference source, NOT a fabrication-ready baseline.** It is not resumed as-is. Its decisions are re-verified, not inherited. | 2026-08-22 |
| D-005 | `hardware/beta-dm/` and `hardware/beta/` remain preserved. Changes to either require explicit CTO authorization. | 2026-08-22 |

---

## 2. Features that must remain

All of the following are **locked as required product features** for Full Beta v2:

- ESP32-S3
- Wi-Fi / BLE
- Touchscreen display
- microSD
- USB-C
- Battery charging / power management / fuel gauge
- 433 MHz / sub-GHz radio
- 915 MHz LoRa radio
- IMU
- NFC
- IR TX
- IR RX
- Microphone / voice input
- Real speech / audio output
- Community expansion interface
- External antenna capability

No feature in this list may be dropped without an explicit CTO ruling recorded
in this file.

---

## 3. Control decisions

| # | decision | date |
|---|---|---|
| D-010 | **Remove HOME.** | 2026-08-22 |
| D-011 | **Volume Up and Volume Down are removed from the product concept.**<br>**Audit note:** they never existed electrically on the current PCB. `SW2`–`SW8` are UP / DOWN / LEFT / RIGHT / A / B / HOME. Volume controls existed only in enclosure planning (Field Slate v5 section 5), which must be corrected. | 2026-08-22 |
| D-012 | **Keep the D-pad.** | 2026-08-22 |
| D-013 | **Keep A and B.** | 2026-08-22 |
| D-014 | **Keep Power** (hard switch on the regulator enable, not a GPIO). | 2026-08-22 |
| D-015 | **Keep physical BOOT / recovery capability, but hide/recess it.** It stays a real, reachable switch — it is the last-resort recovery path when flash is blank or hard-bricked. | 2026-08-22 |
| D-016 | **Also provide software recovery where technically appropriate.** | 2026-08-22 |
| D-017 | **ROM download recovery and firmware/OTA recovery must never be treated as the same mechanism.** They are separate, they fail in different situations, and product/UI copy must not conflate them. See the detail below. | 2026-08-22 |

### D-017 detail — the two recovery mechanisms

**(a) ROM download mode.** Reachable from software on the ESP32-S3 by setting
the `FORCE_DOWNLOAD_BOOT` bit in `RTC_CNTL_OPTION1` followed by a *software*
reset (not a power-on reset). The native USB-Serial-JTAG peripheral also
implements a host-commanded reset-into-download-mode over the CDC control
lines. **Two hard caveats:** it needs some working code or a functional
USB-Serial-JTAG, so a blank or hard-bricked flash cannot invoke it; and if
firmware switches the native USB pins to USB-OTG (TinyUSB), the USB-Serial-JTAG
leaves the bus and the host-commanded path stops working. **That firmware
choice is therefore a hardware-recovery decision and must be locked.**

**(b) Firmware / OTA recovery.** Entirely separate and entirely software: a
factory partition plus OTA data, forced by a button combination sampled early in
boot or by an RTC-memory flag. This handles "the app is broken". It does **not**
handle "the flash is empty".

Both are required. Neither replaces the other.

---

## 4. Audio

| # | decision | date |
|---|---|---|
| D-020 | **Voice input has higher priority than voice output.** | 2026-08-22 |
| D-021 | **Keep the microphone.** (`MK1` ICS-43434, I2S MEMS — the only Beta-DM block that is fitted, fully routed and GND-stitched with zero remaining work.) | 2026-08-22 |
| D-022 | **Keep real speech output.** Intelligible speech and alerts are the requirement, not high-fidelity audio. | 2026-08-22 |
| D-023 | **Prefer the simplest technically sound speech-output implementation.** | 2026-08-22 |
| D-024 | **Current leading architecture is MAX98357A-style I2S Class-D**, unless later review disproves it. | 2026-08-22 |
| D-025 | **Do not downgrade to buzzer-only output.** | 2026-08-22 |

**Supporting audit finding (not a decision):** the ESP32-S3 has **no DAC**, so
every analog-amplifier alternative needs a PWM pin the design does not have and
gives worse intelligibility. I2S Class-D adds zero native pins and reuses the
I2S bus the microphone already requires. The audit found no materially simpler
option.

---

## 5. IR

| # | decision | date |
|---|---|---|
| D-030 | **IR is an internal core product feature.** | 2026-08-22 |
| D-031 | **Do not remove it.** | 2026-08-22 |
| D-032 | **Do not move it to an accessory.** | 2026-08-22 |

---

## 6. Community expansion

| # | decision | date |
|---|---|---|
| D-040 | **Replace the old 26-pin interface with exactly 20 physical pins.** | 2026-08-22 |
| D-041 | **The connector must eventually be keyed, shrouded/polarized and recessed.** This is an electrical safety requirement, not styling: the present `J5` is an unkeyed 0.1 inch 2x13 header where one-row mis-insertion puts `+3V3` on a signal pin. | 2026-08-22 |
| D-042 | **Never duplicate two connector pins onto the same electrical GPIO merely to inflate pin count.** Every signal pin must provide independent useful electrical capability. | 2026-08-22 |
| D-043 | **The C1 / C2 / C3 connector proposals from the pre-design audit are NOT yet CTO-locked.** | 2026-08-22 |
| D-044 | **"14 GPIO-capable lines" was a target to investigate, not a requirement.** | 2026-08-22 |
| D-045 | **Native ESP32 GPIO and TCA9535 XGPIO must be documented distinctly** — in the pinout, on the silkscreen, and in all accessory-facing material. They are not the same currency. | 2026-08-22 |

---

## 7. I2C

| # | decision | date |
|---|---|---|
| D-050 | **External I2C remains desired.** | 2026-08-22 |
| D-051 | **It must not be connected directly in a way that lets a bad accessory take down the internal I2C bus.** The internal bus carries touch, the IMU, the fuel gauge and both GPIO expanders — i.e. the button cluster and every internal control signal. | 2026-08-22 |
| D-052 | **Buffer/isolation and backfeed behaviour must be verified before architecture lock.** Specifically: powered-off high-impedance on the external side, and no back-powering of the accessory side through I/O or protection diodes. | 2026-08-22 |

---

## 8. Mechanical

| # | decision | date |
|---|---|---|
| D-060 | **160 x 80 x 23 mm is an EXTERNAL enclosure target only.** | 2026-08-22 |
| D-061 | **It is NOT a PCB dimension.** | 2026-08-22 |
| D-062 | **It is NOT an internal cavity dimension.** | 2026-08-22 |
| D-063 | **Mechanical cavity / interface freeze must occur BEFORE final PCB placement and routing.** The v3 requirement that the envelope drive a PCB revision was never performed once; it will not be skipped again. | 2026-08-22 |

---

## 9. Safety

| # | decision | date |
|---|---|---|
| D-070 | **Full Beta v2 may not be released to fabrication with unresolved power / self-damage blockers.** | 2026-08-22 |
| D-071 | **Reverse-polarity protection remains a fabrication blocker until resolved.** `BAT_CONNECTOR_P` is currently a single-pad dead net; nothing bridges it to `BAT_PROTECTED_P`. | 2026-08-22 |
| D-072 | **Power / backfeed / NFC-boost / accessory-power / thermal / footprint gates are mandatory.** If physical Beta-DM bring-up is skipped, these become fab-blocking rather than nice-to-have, because there is no earlier board on which they could fail cheaply. | 2026-08-22 |

---

## Pending CTO Decisions

Open items. Nothing downstream of an item may be locked until it is decided.

| # | pending decision | why it blocks | raised |
|---|---|---|---|
| **P-01** | **Reverse-polarity architecture.** Approve the LTC4368-1 + back-to-back N-channel FET path, or name an alternative. | Fabrication blocker. A board built as-is will not run from battery at all. | 2026-08-22 |
| **P-02** | **Final 20-pin connector architecture.** C1 (13 GPIO-capable: 1 native + 12 expander), C2 (12 GPIO-capable: 2 native + 10 expander, **recommended**), or C3 (14 GPIO-capable but requires an SPI bus merge or exposing strapping pins). | Gates the connector sheet, the U3 pin assignment and the right-side mechanical exit. | 2026-08-22 |
| **P-03** | **NFC core / PA rail architecture.** Move the ST25R3916 main VDD to `+3V3` and boost only the PA, or keep the current arrangement? | Gates the NFC sheet and the power budget. Current arrangement leaves the core unpowered while VDD_IO sits at 3.3 V. | 2026-08-22 |
| **P-04** | **NFC first-fab inclusion, and antenna implementation.** Is NFC in v2's first fabrication, or a populate-later block? The 27.12 MHz crystal, the matching network and the antenna are **undesigned**, not merely unrouted. | Gates the schematic migration schedule and the rear-half floorplan. | 2026-08-22 |
| **P-05** | **RGB LED: implement or delete.** Three nets and three U2 pins exist; no LED part exists. | Three dangling ERC errors. Cannot remain in this state. | 2026-08-22 |
| **P-06** | **RootProbe: complete or retire/redefine.** `ROOTPROBE_IRQ_READY_N` reaches only a pull-up and U2.P17 — it has **no header pin**, so RootProbe cannot connect as drawn. | Retiring it frees U2.P17 for charge-status telemetry. | 2026-08-22 |
| **P-07** | **Exact mechanical internal cavity.** Internal cavity X/Y/Z, wall thickness and PCB-to-wall clearance have **never existed** in this repository. | Blocks the v2 outline, and therefore all placement and routing. | 2026-08-22 |
| **P-08** | **External antenna mechanical path.** (a) u.FL pigtail from the module IPEX to a panel-mount SMA/RP-SMA — preserves the no-RF-on-main-PCB doctrine (**recommended**); or (b) a board-level RF connector requiring controlled-impedance routing and matching. | Gates the top-crown mechanical design and the RF scope. | 2026-08-22 |
| **P-09** | **Is LoRa packet wake required?** If yes, `SX1262_DIO1` must move to an RTC-capable GPIO (0-21). It currently sits on GPIO38, which is not RTC-capable and therefore cannot serve as an `ext0`/`ext1` deep-sleep wake source. | Gates the MCU pin remap and the standby power story. | 2026-08-22 |

### How a pending decision closes

A pending item closes by being moved into a numbered `D-xxx` row above, with its
date, and by an entry in [CHANGELOG.md](CHANGELOG.md). It is removed from this
table only when it has a home in the locked sections.
