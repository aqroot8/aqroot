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
| D-018 | **Physical BOOT must remain electrically real.** The final actuator is hidden/recessed, but the circuit is not weakened, gated or made conditional on any other subsystem's state. | 2026-08-22 |

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
| D-026 | **Carry forward the audit recommendations to evaluate** speaker EMI filtering, speaker current / brownout impact, gain configuration, and the mechanical speaker cavity. | 2026-08-22 |

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
| D-033 | **IR TX and IR RX are mandatory Full Beta v2 features and must be POPULATED in the first Full Beta v2 fabrication.** No DNP. | 2026-08-22 |
| D-034 | Powering a stronger IR TX pulse from `SYS` rather than loading the `+3V3` logic rail is a **DESIGN DIRECTION, not a final resistor/current lock.** | 2026-08-22 |

---

## 5a. NFC

| # | decision | date |
|---|---|---|
| D-035 | **NFC is mandatory in the FIRST Full Beta v2 fabrication. No DNP showcase shortcut.** | 2026-08-22 |
| D-036 | Intended direction: digital/core supplies coherent with the 3.3 V logic domain; boost only the transmitter/PA rail that actually requires it. **Exact pin-to-rail assignment NOT locked until verified against the official ST datasheet.** Crystal, matching network and antenna must all be real designs before fabrication; **no `*_TBD` dangling NFC nets may remain at release.** | 2026-08-22 |

> **⚠ VERIFICATION OVERTURNED THE SUPPLY-SPLIT PART OF D-036 (2026-08-22, FBV2-ARCH-001).**
> ST25R3916 datasheet **DS12484 Rev 3**, p. 39, states plainly: *"VDD and VDD_TX
> must be connected to the same power supply."* Table 118 caps **VDD − VDD_TX at
> ±0.3 V absolute maximum**; Table 119 caps it at **±0.2 V operating**. On this
> part the core supply is VDD and the transmitter supply is VDD_TX, so the
> requested 3.3 V / 5 V split would place **1.7 V** across that pair — **5.7× the
> absolute maximum** — and would damage the device.
>
> **The as-built schematic (VDD + VDD_TX both on the boosted rail, VDD_IO on
> `+3V3`) is CORRECT.** VDD_IO is genuinely independent (1.65–5.5 V, level
> shifters). D-036's *intent* — supplies that stay coherent — is preserved by a
> different route and is now tracked as **P-10**. The clause requiring datasheet
> verification before locking did its job.

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
| D-046 | **C2 is the PROVISIONAL architecture direction**: 10 independent TCA9535 XGPIO, 2 independent native ESP32 GPIO, external I²C SDA/SCL, WAKE/ATTN, switched accessory +3V3, permanent +3V3, and sufficient GND (3 in the C2 proposal). | 2026-08-22 |
| D-047 | **Do not pursue "14 GPIO-capable pins"** if it requires merging SPI-A and SPI-B, exposing unsafe boot-strapping pins, duplicating physical pins onto the same GPIO, or degrading core product functionality. **Protocol capability outranks marketing pin count.** | 2026-08-22 |
| D-048 | **C2 is NOT electrically frozen** until the native-GPIO reclaim is independently verified. | 2026-08-22 |

> **Verification result against D-048 (2026-08-22, FBV2-ARCH-001).** The reclaim as
> proposed — `NATIVE_B` = GPIO18, freed by moving `NFC_IRQ` to GPIO46 — **FAILED**
> and must not be built: a latched-high NFC IRQ would block Joint Download Boot
> and make ROM-download recovery conditional on NFC state, violating D-015.
> A substitute **PASSES with circuit conditions**: move `DISP_BL_CTL` to GPIO46
> and expose **GPIO47** as `NATIVE_B`. C2's shape (10 + 2 + I²C + WAKE + 2 rails +
> 3 GND = 20) is unchanged. See
> [`audits/2026-08-22-architecture-verification.md`](audits/2026-08-22-architecture-verification.md) §B.
> **Still not frozen** — the substitution is a recommendation, not a lock.

---

## 7. I2C

| # | decision | date |
|---|---|---|
| D-050 | **External I2C remains desired.** | 2026-08-22 |
| D-051 | **It must not be connected directly in a way that lets a bad accessory take down the internal I2C bus.** The internal bus carries touch, the IMU, the fuel gauge and both GPIO expanders — i.e. the button cluster and every internal control signal. | 2026-08-22 |
| D-052 | **Buffer/isolation and backfeed behaviour must be verified before architecture lock.** Specifically: powered-off high-impedance on the external side, and no back-powering of the accessory side through I/O or protection diodes. | 2026-08-22 |

---

## 7a. Removed and retired architecture

| # | decision | date |
|---|---|---|
| D-037 | **REMOVE the dangling `RGB_R/G/B_CTL` architecture.** There is no approved Full Beta v2 RGB status-light product feature. **Do not add an LED merely because these nets existed.** Free the corresponding expander resources. *(Closes P-05.)* | 2026-08-22 |
| D-038 | **Retire the orphaned dedicated `ROOTPROBE_IRQ_READY_N` architecture.** KEEP the useful FAST_IO / native expansion capability. Future RootProbe and community accessories use the normal WAKE/ATTN mechanism rather than consuming a dedicated IRQ. *(Closes P-06.)* | 2026-08-22 |

Between them, D-037 and D-038 free **five** internal expander pins: `U2` P05, P06,
P07 (RGB) and P17 (RootProbe IRQ), plus P16 already freed by removing HOME (D-010).

---

## 7b. Charger telemetry

| # | decision | date |
|---|---|---|
| D-039 | **Investigate** using the expander pins freed by HOME removal and RootProbe IRQ retirement for `BQ25185` `STAT1` and `STAT2`. **Do not wire them yet** — verify electrical behaviour and open-drain requirements first. | 2026-08-22 |

> **Verification result (2026-08-22, FBV2-ARCH-001).** BQ25185 datasheet
> **SLUSF65A** Table 5-1: both pins are **open-drain**, pull-up **1 kΩ–20 kΩ**,
> **maximum pull-up voltage 5 V**, 20 mA sink, "can be left floating if unused".
> 10 kΩ to `+3V3` is in spec and feeding TCA9535 inputs is appropriate.
> **However** §8.3.10 / Table 7-2 record that in the charge-complete/sleep state
> **`STAT2` toggles** — which on `U2` would repeatedly assert `/INT` → `WAKE_INT_N`
> → GPIO21 and wake the MCU for as long as the unit sits on a full charger.
> **Recommendation: connect `STAT1` only** (to the freed `U2.P16`); leave `STAT2`
> on its test point; use `U2.P17` for a VBUS-present sense, which the product
> currently lacks entirely. Not implemented, per this ruling.

---

## 7c. External antenna

| # | decision | date |
|---|---|---|
| D-040 | **Prefer module RF connector / IPEX / U.FL → short RF pigtail → panel/bulkhead external antenna connector.** Do not introduce new controlled-impedance RF routing onto the main PCB unless a later mechanical/RF review proves the pigtail approach unacceptable. *(Closes P-08.)* | 2026-08-22 |

---

## 7d. LoRa deep-sleep wake

| # | decision | date |
|---|---|---|
| D-041 | **Wake-on-LoRa-packet from deep sleep is NOT a Beta v2 showcase requirement.** Do not remap core interfaces solely to make `SX1262_DIO1` RTC-wake-capable. *(Closes P-09.)* | 2026-08-22 |

> This ruling is what makes the §B connector substitution free of cost: the
> replacement native pin (GPIO47) is outside the RTC range, and nothing needs it
> to be inside, because `WAKE_ATTN_N` on GPIO21 is already the RTC-capable
> accessory wake line.

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
| **P-02** | **Freeze the 20-pin connector.** C2 is the provisional direction per D-046. Verification substituted **GPIO47** for GPIO18 as `NATIVE_B` and moved `DISP_BL_CTL` to GPIO46. Approve the substitution, or fall back to C1. | Gates the connector sheet, the `U3` pin assignment and the right-side mechanical exit. **Shape verified; identity of `NATIVE_B` awaiting approval.** | 2026-08-22 |
| ~~**P-03**~~ | ~~NFC core / PA rail architecture.~~ **RESOLVED — the question was mis-framed.** DS12484 Rev 3 requires VDD and VDD_TX to share one supply (±0.2 V operating). The rails cannot be split and the as-built assignment is correct. | Superseded by **P-10**. | closed 2026-08-22 |
| **P-04** | **NFC first-fab inclusion, and antenna implementation.** Is NFC in v2's first fabrication, or a populate-later block? The 27.12 MHz crystal, the matching network and the antenna are **undesigned**, not merely unrouted. | Gates the schematic migration schedule and the rear-half floorplan. | 2026-08-22 |
| **P-10** | **NFC supply topology.** **N1** — run NFC entirely at 3.3 V (`sup3V` option bit; VDD range 2.4–3.6 V) and **delete** U13, L2, R44, R45, C19, C34, C35, C55; or **N2** — keep the 5 V boost and never disable it while the system is on. Created by the DS12484 finding that VDD and VDD_TX cannot be split. | With true load disconnect confirmed on the TPS61023, disabling the boost leaves VDD = 0 V while VDD_IO = 3.3 V — a state the datasheet nowhere authorises. **N1 recommended**: deletes a converter, eight parts, the OVP question and the sequencing question. Price is RF range. | 2026-08-22 |
| **P-07** | **Exact mechanical internal cavity.** Internal cavity X/Y/Z, wall thickness and PCB-to-wall clearance have **never existed** in this repository. | Blocks the v2 outline, and therefore all placement and routing. **Now the long-pole item.** | 2026-08-22 |

### Closed since 2026-08-22

| # | closed by | outcome |
|---|---|---|
| **P-05** | D-037 | RGB architecture removed; three expander pins freed. |
| **P-06** | D-038 | Dedicated RootProbe IRQ retired; `U2.P17` freed. |
| **P-08** | D-040 | IPEX → pigtail → bulkhead. No new main-PCB RF routing. |
| **P-09** | D-041 | LoRa deep-sleep packet wake is not a v2 requirement. |

### How a pending decision closes

A pending item closes by being moved into a numbered `D-xxx` row above, with its
date, and by an entry in [CHANGELOG.md](CHANGELOG.md). It is removed from this
table only when it has a home in the locked sections.
