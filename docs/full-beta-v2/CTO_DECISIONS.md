# AQROOT Full Beta v2 — CTO Decisions

**Status: LIVING DOCUMENT. This is the current source of truth.**

When an older transcript, audit or architecture note conflicts with a ruling in
this file, **this file wins.** Superseded rulings are struck through and kept,
never deleted, so the history of the decision stays readable.

Established: 2026-08-22
Last updated: 2026-08-24 (FBV2-P1-002)

---

## ⭐ STANDING POLICY — FIRST FIVE FULL BETA PCBAs: NO-RESPIN RECOVERY POLICY

**D-049 · Permanent requirement · established 2026-08-22 · applies to every
subsequent design decision until explicitly revoked.**

Full Beta v2 will be ordered as approximately **five assembled PCBAs**. We must
not fabricate five boards and then discover that a reasonable first-revision
architecture adjustment requires all five to be reordered.

**Full Beta v2 Revision 1 must be designed for recoverability.** Where an
important architecture choice is still reasonably uncertain, prefer:

- DNP/FIT options
- 0 Ω source-selection links
- accessible tuning passives
- test points
- preserved alternate footprints where the area/cost penalty is reasonable
- controlled hand rework

and **avoid** fallback paths that require trace cuts, bodge wires, or an entirely
new PCB revision for a predictable configuration change.

**This does NOT authorise:** unsafe redundant circuitry · mutually active power
sources · keeping every abandoned concept · compromising signal integrity ·
fallback hardware with no plausible use · weakening protection circuitry.

**Two different standards apply, and they must not be confused:**

| system class | rule |
|---|---|
| **Safety-critical power paths** (battery reverse protection) | **Do NOT create ad-hoc bypasses merely for reworkability.** Protection integrity outranks convenience. |
| **Performance-uncertain, non-safety-critical** (NFC supply, IR drive, EMI filtering, current limits) | **Design a clean first-revision fallback** where technically sensible. |

**Intent:** the first five PCBAs should maximise the probability that every major
showcase feature can be made functional through normal component rework if the
first configuration underperforms.

Reasonable configuration and performance uncertainty should be recoverable
through **planned** component rework whenever practical.

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

## 8a. Battery reverse protection (FBV2-ARCH-002)

| # | decision | date |
|---|---|---|
| D-050 | **LTC4368-1 is the preferred controller architecture**, with VIN on the cell side. | 2026-08-22 |
| D-051 | **LTC4368-2 is REJECTED** for this application: its reverse-current threshold interferes with the normal charger-to-battery current direction when VIN is on the cell side. *(Verified: −3 mV vs the -1's symmetric ±50 mV. A `-2` discharges normally and never charges.)* **The suffix must appear in the schematic symbol, the BOM, the assembly note and the bring-up checklist.** | 2026-08-22 |
| D-052 | **Bare back-to-back MOSFETs are NOT a complete solution** and must not be treated as one. *(Verified unrealisable at 1S: available V<sub>GS</sub> is 0.3–1.5 V; the P-channel variant turns hard on into a reversed cell.)* | 2026-08-22 |
| D-053 | **Mandatory fault case: REVERSED BATTERY WHILE USB POWERS THE SYSTEM.** Additionally evaluate **single pass-MOSFET short + reversed battery + USB present.** | 2026-08-22 |
| D-054 | **No single plausible protection-component failure may place meaningful negative voltage onto BQ25185 BAT** without another protection mechanism clearing or limiting the fault. | 2026-08-22 |

**Still OPEN before schematic lock** (per ruling A): exact MOSFET selection ·
sense resistor / current threshold · UV/OV divider · fuse requirement · reverse
clamp requirement · dead-cell recovery.

> **Verification result (FBV2-ARCH-002).** D-054 is **not met by LTC4368-1 +
> dual N-FET alone** — a shorted pass FET is the dominant MOSFET failure mode and
> reproduces the exact fault the protection guards. A **series fuse plus a
> Schottky clamp at the cell connector** are therefore **required**, not optional.
> Separately, the protection **creates** a new failure mode: below the LTC4368's
> 1.8–2.4 V UVLO both gates are off and the body diodes are anti-series, so a
> deeply discharged pack can never be recharged. See **P-11**, **P-12**, **P-13**
> and [`architecture/POWER_FAULT_STATE_TABLE.md`](architecture/POWER_FAULT_STATE_TABLE.md).

---

## 8b. NFC supply — default 3.3 V with a no-respin 5 V fallback (FBV2-ARCH-002)

| # | decision | date |
|---|---|---|
| D-055 | **Default first build: `NFC_SUPPLY` = `+3V3`.** ST25R3916 `VDD` = `VDD_TX` = `NFC_SUPPLY`; `VDD_IO` = `+3V3`; configure the documented 3.3 V mode (`sup3V`). **NFC must be FITTED and functional on the first fabrication.** *(Supersedes the N1/N2 choice in P-10, which is now closed.)* | 2026-08-22 |
| D-056 | **The PCB MUST preserve a practical conversion path to boosted ~5 V WITHOUT REORDERING THE PCB**, via `SYS → TPS61023 → source selector → NFC_SUPPLY`. **Hard requirement** unless a serious electrical/RF/layout penalty is proven. **Do not delete the fallback merely to save PCB area.** | 2026-08-22 |

**Hard requirements on the fallback** (all verified achievable — see the audit §G):

1. `VDD` and `VDD_TX` always tied together on `NFC_SUPPLY`.
2. `VDD_IO` remains `+3V3`.
3. The `+3V3` and boosted sources must be **mutually exclusive**.
4. It must be **impossible** under the intended BOM to short `+3V3` to the boost output.
5. First fab: 3.3 V source FITTED · 5 V activation path DNP · ST25R3916 FITTED · matching network FITTED for 3.3 V · antenna FITTED.
6. Conversion of one board requires only: moving 0 Ω links · populating DNP boost parts · changing accessible matching passives · a firmware change.
7. Conversion must **NOT** require: PCB reorder · trace cutting · bodge wiring · replacing the ST25R3916 · modifying `VDD_IO` routing.
8. Test points on `NFC_SUPPLY`, the boost output, and key NFC power/debug nodes.
9. Matching/tuning components must stay physically accessible for prototype rework.

> **Verification result.** Requirements 1–9 are all satisfiable. Two 0 Ω select
> links guarantee mutual exclusion **by construction** — exactly one is ever
> fitted, so requirement 4 holds with no BOM configuration able to violate it.
> **Pre-fit the inductor, the FB divider and both boost capacitors; keep the
> TPS61023 and the 5 V select link DNP.** Conversion is **3–9 soldering
> operations, exactly one of which is fine-pitch** (TPS61023, SOT-563, 0.5 mm) —
> practical with hot air, iron and tweezers, no BGA/QFN rework. **No serious
> penalty found: KEEP THE FALLBACK.** Full FIT/DNP matrix in the audit §G.2–G.4.
>
> **Two conditions not in the ruling and not to be lost:** do not tap
> `VDD`/`VDD_TX` straight off the 3V3 plane (ferrite/0 Ω plus substantial local
> bulk — this is the biggest risk in the 3.3 V configuration), and **re-scale the
> RFI receiver divider**, which is the most commonly missed consequence of
> dropping the supply.

---

## 8c. Community accessory power (FBV2-ARCH-002)

| # | decision | date |
|---|---|---|
| D-057 | **REMOVE the permanent raw `+3V3` pin from the public community connector.** There will be **no unprotected always-live `+3V3` tap exposed to users.** Keep one protected switched accessory rail. | 2026-08-22 |
| D-058 | **TPS22950C (leaded package) is the preferred investigation direction** for the switched rail: 3.3 V operation · default OFF · hardware pull-down on ON/EN · reverse-current blocking · adjustable current limit · short-circuit protection · thermal shutdown. Target initial limit ≈ 500 mA. **Do not lock R<sub>ILIM</sub>** until the accessory/system power budget is derived. | 2026-08-22 |

**Requirements:** an externally powered accessory must not back-power AQROOT, and
a shorted accessory must not collapse the core `+3V3` rail.

> **Verification result.** TPS22950**C** meets every requirement — SLVSFJ2B §5
> confirms **RCB = Yes** for the C variant (and **No** for the L variant, which
> must never be substituted). Package is **DDC SOT-23-thin**, leaded. Internal
> smart pull-down is 500 kΩ, **but Table 6-1 still says "Do not leave floating",
> so the external pull-down remains mandatory.**
>
> **One caveat on the 500 mA target:** the C variant's adjustable range **starts
> at 0.5 A**, so 500 mA is the extreme bottom of the range. The base TPS22950
> reaches 0.05 A but is WCSP-only and fails the leaded requirement.
> **Recommend 600–800 mA.** Also route the open-drain `FLT` output to a spare
> internal expander input — it converts an invisible fault into a UI message.

---

## 8d. Community connector — 20-pin allocation (FBV2-ARCH-002)

| # | decision | date |
|---|---|---|
| ~~D-059~~ | ~~**New target: 11 × independent XGPIO · 2 × independent native ESP32 GPIO · 2 × external I²C · 1 × WAKE/ATTN · 1 × protected switched accessory 3V3 · 3 × GND = 20.**~~ **SUPERSEDED 2026-08-23 by D-081/D-082 — the port is now 2×12 / 24 active contacts.** The *principles* survive: no permanent raw `+3V3`, no duplicate GPIO. | 2026-08-22 |
| D-060 | Native pins should preferably have **no strapping role, no ROM boot traffic**, be bidirectional high-speed GPIO, and be safe on ESP32-S3-WROOM-1-N16R8. **GPIO47 remains approved.** **GPIO43 is FALLBACK ONLY**, because U0TXD may emit ROM/boot traffic. | 2026-08-22 |

> **Verification result.** The 20-pin count is satisfied exactly. Recommended
> native pair is **GPIO38 (`NATIVE_A`) + GPIO47 (`NATIVE_B`)**, which removes
> GPIO43 from the connector entirely. GPIO38 is priority-2 unrestricted, has no
> strapping role, no boot traffic and no published power-up glitch.
> **Gated on unverified SX1262 DIO1 behaviour** — see the audit §B.2.

### Ruling E — GPIO46 (conditional)

Moving `DISP_BL_CTL` to GPIO46 remains a **conditional** option requiring: an
external hardware pull-down · the backlight driver must not pull GPIO46 high
during strap sampling · GPIO46 must remain LOW for Joint Download Boot · the safe
strap state must not depend on firmware · verify the pull structure in the chosen
backlight driver.

> **Verification result — the blocking condition is CLOSED.** The TPS61169 `CTRL`
> pin has an **internal pull-down** (TI datasheet, `R_PD`), not a pull-up, so it
> reinforces GPIO46's own weak pull-down rather than fighting it. **GPIO46 is
> cleared to host `DISP_BL_CTL`** subject to: 10 kΩ external pull-down · **no RC
> filter and no bulk capacitance on the net** · strap hold ≥ 3 ms · document that
> GPIO46 cannot retain level through deep sleep · verify per unit via the ROM
> `boot:0xNN` log (bit `0x04` is the latched GPIO46 level).

### Ruling F — Expanders

**PCAL9535A is the preferred investigation candidate to replace TCA9535.**
**Do NOT replace it yet.** Investigate replacing **both** `U2` and `U3` so AQROOT
uses one expander family. Desired: per-pin interrupt mask · interrupt status ·
input latch · programmable pulls · clean charger-status handling · clean
community-input interrupt handling.

**Critical hardware safe-state pull resistors remain EXTERNAL. Do not rely on
programmable expander pulls for safety-critical startup states.**

> **Verification result: PASS WITH SCHEMATIC/FIRMWARE CHANGES**, and **yes,
> change both.** Not "drop-in": the PCAL9535A pin table could not be retrieved
> from a primary source (three routes failed), and **firmware must change or it
> silently sees no interrupts at all** — the PCAL9535A powers up with every
> interrupt masked, the exact opposite of the TCA9535. Audit §A.

### Ruling G — Charger status

**Preserve both `STAT1` and `STAT2`.** The previous STAT1-only recommendation is
**rejected**. If PCAL9535A is adopted, use interrupt masking/status logic so the
no-battery `STAT2` behaviour does not cause repeated MCU wakeups.

> **Verification result — the ruling is correct and my earlier reading was wrong.**
> SLUSF65A §7.3.10 verbatim: *"**When no battery is present**, the device charges
> the capacitor on the BAT pin and toggles between charging and charge completed
> states. During this condition, the STAT1 pin remains stable, while the STAT2 pin
> toggles between HIGH and LOW."* Table 7-2 confirms charge-complete, sleep and
> charge-disabled are **one state with both pins HIGH**. STAT1 alone therefore
> conveys only fault/no-fault. **Pull both to `+3V3` with 20 kΩ** (datasheet range
> 1 k–20 k, maximum pull-up rail 5 V).

---

## 8e. Expander family — LOCKED (FBV2-PWR-001)

| # | decision | date |
|---|---|---|
| D-061 | **Replace BOTH `U2` and `U3` TCA9535PWR with NXP `PCAL9535APW,118`** (LCSC **C2669683**). **This is an ARCHITECTURE lock, not a fabrication footprint signoff** — the land pattern must still be audited against the current NXP package drawing before fabrication. | 2026-08-22 |

**Mandatory firmware changes** (recorded as a binding contract):

- Interrupt mask registers **power up masked** — initialise the required masks explicitly, or the device sees no interrupts at all.
- Use the **interrupt status registers** to identify the source.
- Use **input latch** selectively.
- **Do not rely on programmable pulls for critical hardware safe states.**

**External safe-state resistors on critical control outputs remain mandatory.**

> **Verification (FBV2-PWR-001): PASS WITH FIRMWARE CHANGES. No pin or package
> incompatibility found.** The CTO-supplied pinout matches TCA9535 PW verified
> from SCPS201E Figure 5-1, pin for pin, and matches every measured `U2`/`U3` pad
> on the board. Both are TSSOP24 4.4 mm body, so **footprint retention holds in
> principle.**
>
> **Evidential bound:** the PCAL9535A PDF could not be retrieved from this
> environment (NXP 404 direct and via browser; Digi-Key 410; Mouser/LCSC/Diodes
> mirrors returned HTML). Four facts — **pull enables disabled at POR, 400 kHz
> support, output drive current, and the Agile I/O command byte addresses** —
> rest on NXP product-page text rather than a page-cited datasheet read. None can
> change the architecture decision, but **all four must be closed at the
> land-pattern audit.** "All interrupts masked at POR" and "legacy PCA9535
> register block retained" are confirmed from NXP documentation.

---

## 8f. Native GPIO pair — LOCKED (FBV2-PWR-001)

| # | decision | date |
|---|---|---|
| ~~D-062~~ | ~~20-pin resource architecture **LOCKED**: 11 XGPIO · 2 native ESP32 GPIO · 2 external I²C · 1 WAKE/ATTN · 1 protected switched accessory 3V3 · 3 GND = 20.~~ **SUPERSEDED 2026-08-23 by D-082.** **No raw permanent +3V3 still holds.** | 2026-08-22 |
| D-063 | **`NATIVE_A` = GPIO38, `NATIVE_B` = GPIO47. LOCKED.** GPIO43 is fallback only. `SX1262_DIO1` moves to the **internal** PCAL9535A — never the public/community expander. **`BUSY` remains directly connected to the ESP32.** | 2026-08-22 |

> **Verification (FBV2-PWR-001): CONFIRMED — the lock condition is met.**
> Semtech SX1261/2 datasheet `DS.SX1261-2.W.APP` Rev. 1.2, §13.3.4, p. 81,
> verbatim:
>
> *"If a DIO is mapped to one single IRQ source, the DIO is cleared if the
> corresponding bit in the IRQ register is cleared. If DIO is set to 0 with
> several IRQ sources, then the DIO remains set to one until all bits mapped to
> the DIO in the IRQ register are cleared."*
>
> **DIO1 is level-held, not a pulse**, so an expander input with no capture
> register can service it safely. The condition that blocked OPTION G38 in
> FBV2-ARCH-002 is closed, and GPIO43 leaves the public connector.
>
> **Caveat:** this is Rev. 1.2 (June 2019). The current revision is **V2.2
> (2025-04-07)**, identified but not retrievable. Confirm against V2.2 and
> against the **E22-900M22S module** datasheet before fabrication.
>
> Firmware handling contract — including the **second PCAL edge when DIO1 returns
> low**, and the documented `GetIrqStatus`/`ClearIrqStatus` race — is recorded in
> the closeout audit §8.1.

---

## 8g. Battery protection — language correction (FBV2-PWR-001)

| # | decision | date |
|---|---|---|
| D-064 | **LTC4368-1 remains the PREFERRED battery-protection controller architecture.** The **fuse + Schottky clamp is a CANDIDATE defence-in-depth topology pending exact fault-energy analysis** — it is **not** locked merely because a previous audit recommended it. It may become mandatory only if the complete circuit and fault behaviour support that conclusion. | 2026-08-22 |

> **The correction was justified, and the analysis vindicates it.** At realistic
> fault currents (20–25 A from a 1S pack) a Schottky clamp sits at **≈0.8–1.0 V**,
> roughly **3× the BQ25185 `BAT` −0.3 V absolute maximum**. The clamp reduces the
> excursion from ≈−3.7 V to ≈−1 V — a 4× improvement — but **does not bring the
> node inside the absolute maximum.** Recording it as "locked" would have implied
> a proof that does not exist.
>
> **Both elements are still REQUIRED** — the fuse because without it the clamp is
> a permanent short across a Li-ion cell, the clamp because it is what holds the
> node while the fuse clears — but the **residual is named (P-12)** rather than
> assumed away. A **PTC is REJECTED** for this position: too slow, and its
> auto-retry re-applies the fault on every cycle.
>
> Full analysis, including the complete element-by-element topology, is in
> [`audits/2026-08-22-battery-protection-closeout.md`](audits/2026-08-22-battery-protection-closeout.md) §2 and §5.

---

## 8h. Dead-cell recovery and single-fault battery safety (FBV2-PWR-002)

| # | decision | date |
|---|---|---|
| D-065 | **Candidate B SELECTED: autonomous hardware-qualified dead-cell recovery.** Service-only Candidate D is **rejected** as the normal architecture. The recovery system must operate with USB present, require **no working ESP32 firmware**, work with blank/corrupted flash, identify a correctly oriented near-0 V pack, **reject a reversed pack**, provide controlled limited current, hand off automatically to the LTC4368-1/BQ25185 path, return to a low-Iq inactive state, and **not create a dangerous bypass around reverse protection.** Rationale: Full Beta v2 must behave like a product, not a bench prototype needing service after a normal deep-discharge event. | 2026-08-22 |
| D-066 | **PCAL9535APW,118 LOCKED for both `U2` and `U3`.** NXP Rev 2 independently verified by the CTO: 400 kHz Fast-mode, 25 mA output capability, all interrupts masked at POR, mask registers 4Ah/4Bh, status registers 4Ch/4Dh, programmable pull enable/selection, input latch, Agile I/O, all channels inputs at power-up. **Do not reopen** unless a footprint/procurement gate finds a concrete problem. | 2026-08-22 |
| D-067 | **GPIO38 + GPIO47 remain LOCKED.** `SX1262_DIO1` moves to the internal PCAL9535A. Pre-fab confirmation against the then-current Semtech datasheet and the exact E22 module is still required but **no longer blocks architecture.** | 2026-08-22 |
| D-068 | **New single-fault objective: no single external pass-MOSFET short may cause BQ25185 `BAT` to exceed its negative absolute maximum under the mandatory reversed-battery + USB fault. Prefer prevention/isolation over relying on fault-clearing time.** A protection circuit may **not** be declared compliant merely because a fuse clears after the IC has already exceeded absolute maximum. | 2026-08-22 |

> **D-066 closes the four facts the previous audit could not verify** — pull-enable
> POR state, 400 kHz, output drive current and the Agile I/O register addresses.
> Recorded as CTO-verified from NXP Rev 2. The **land-pattern audit remains a
> separate pre-fabrication gate.**

> **Verification result (FBV2-PWR-002): D-068 is MET, by isolation.**
>
> The pass path becomes **P2** — two back-to-back N-FET stages in series, in **two
> separate packages**. Any single drain-source short leaves one complete
> back-to-back pair intact, so a reversed cell never reaches `BAT_PROTECTED_P`.
> The single-package alternative was rejected because two die sharing one
> leadframe and molding cannot be claimed independent against a package-level
> failure.
>
> Precise finding on the old architecture: **P1 fails one of the two single-FET
> cases, not both.** A short on the `BAT_RAW`-side FET is already blocked by the
> survivor; a short on the **`BAT_PROT`-side** FET is the dangerous one.
>
> **The previous fuse + clamp compliance argument is withdrawn.** A Schottky at
> ≈0.8–1.0 V does not protect a −0.3 V absolute maximum, and ruling D was right to
> reject it. Consequences: the **clamp is demoted to USEFUL SECONDARY protection**
> (ESD, transient, double-fault) and the **fuse is resized 3 A → ≈5 A** because it
> is now a backstop that must not pre-empt the 3.33 A electronic breaker. **PTC
> remains REJECTED.**
>
> **Candidate B is specified to component level** — ratiometric bridge polarity
> detection (threshold at V_BAT = 0, supply-independent by construction), TLV7032
> dual comparator, three-input series AND terminating at the LTC4368 `FAULT` pin
> for a free hardware handoff, P-FET switch with a series Schottky, and 5–10 mA
> recovery current. Full analysis in
> [`audits/2026-08-22-dead-cell-and-single-fault-closeout.md`](audits/2026-08-22-dead-cell-and-single-fault-closeout.md).
>
> **Honest residual:** Candidate B is **not** tolerant to every single failure —
> four failures each individually enable recovery current into a reversed cell.
> It **meets the requirement as written** because `R_LIM` bounds every one to
> **≤13 mA (~0.007 C)**, which is not a high-current path. A redundant variation
> is documented; it is **not** recommended, because it trades that bounded
> residual for a permanent oscillation in the far more common battery-absent state.

---

## 8i. Mechanical interface freeze (FBV2-MECH-001)

| # | decision | date |
|---|---|---|
| D-069 | **External enclosure 80 × 160 × 23 mm (portrait). LOCKED.** External only — **not** PCB, **not** internal cavity, **not** usable volume. The Full Beta v2 PCB outline is **derived from** the mechanical architecture, never inherited. | 2026-08-22 |
| D-070 | **Six-face layout LOCKED.** Front: display/touch, D-pad, A, B, mic aperture. Top: antenna bulkhead + IR TX/RX windows. Left: antenna storage. Right: recessed keyed 20-pin connector, Power, recessed BOOT. Bottom: USB-C, microSD. Rear: NFC target, speaker opening, branding. **HOME, Volume Up and Volume Down are removed and must not reappear.** | 2026-08-22 |

> **Derived interface freeze (FBV2-MECH-001).** Authoritative pre-CAD source:
> [`mechanical/MECHANICAL_INTERFACE_SPEC.md`](mechanical/MECHANICAL_INTERFACE_SPEC.md).
>
> | key | value | status |
> |---|---|---|
> | Internal cavity | **75.0 × 155.0 × 18.5 mm** | TARGET |
> | Wall thickness | 2.0 mm | TARGET |
> | PCB max / **target** | 72.0 × 152.0 / **70.0 × 148.0 mm** | TARGET |
> | Battery envelope | **60 × 75 × 8.0 mm** (~2500–3000 mAh) | TARGET |
> | NFC zone | **45 × 45 mm**, rear upper third | TARGET |
> | Z verdict | **PASS** — 19.5 of 23.0 mm on the governing column | — |
>
> **23 mm PASSES with 3.5 mm spare, and the margin is allocated to the battery**
> rather than left as air — raising the pack from the 2000 mAh the power budget
> assumes to the 2500–3000 mAh class at no external size cost.
>
> **The Beta-DM 74 × 155 mm outline must NOT be reused.** Against a 75 × 155 mm
> cavity it leaves 1.0 mm of clearance in X and **zero in Y** — no room for the
> shell lip, six bosses, ribs or assembly access. Combined with the v2 content
> changes (20-pin connector, P2 four-FET stage, recovery branch, NFC crystal and
> matching, restored IR, new expanders), the verdict is
> **SHOULD BE RE-FLOORPLANNED WITH A DIFFERENT OUTLINE.** This is the PCB revision
> Field Slate v3 required in July and never received.
>
> **NFC and battery are separated in plan, not stacked.** The display occupies the
> front upper third, so the rear upper third is free: NFC loop there, battery in
> the rear lower two-thirds. **Zero overlap is the policy, not a mitigation.**
> Ferrite is still specified because the PCB ground pour becomes the dominant
> near-field threat once the battery is moved away. The loop grows from Beta-DM's
> measured 26 × 20 mm to 45 × 45 mm — a **3.9× area increase**, which is where the
> range lost to 3.3 V operation (D-055) is won back.

---

## 8j. Display and FPC interface (FBV2-DISP-001)

| # | decision | date |
|---|---|---|
| D-071 | **Battery envelope LOCKED: 60 x 75 x 8.0 mm, target ~2500-3000 mAh.** | 2026-08-22 |
| D-072 | **Full Beta v2 display size target is 3.5 inch.** | 2026-08-22 |
| D-073 | **Do NOT blindly reuse CH280QV10-CT or J1 FH69-50S-0.5SH.** A possible incompatibility exists between the old 50-pin display FPC geometry/pitch and the current 0.5 mm J1 connector. | 2026-08-22 |

> **Verification result (FBV2-DISP-001).** Full analysis:
> [`audits/2026-08-22-display-interface-closeout.md`](audits/2026-08-22-display-interface-closeout.md).
>
> **D-073 is well founded, and the answer is UNPROVEN rather than NO.** No source
> obtainable to this audit states the CH280QV10-CT's FPC pitch - the Phase-1
> mechanical audit independently recorded the same gap. **J1 was selected without
> a display FPC drawing on file and has never been proven to mate.** Its footprint
> is verified against the *Hirose* drawing, which proves the connector footprint is
> right and proves nothing about the display. The suspicion is strengthened by the
> successor part in the same family quoting **0.3-0.4 mm**, not 0.5 mm.
>
> **The 3.5-inch candidate CH350HV40A-CT is verified and fits, but is NOT locked.**
> 320 x 480 IPS, **ILI9488**, module **56.54 x 84.96 x 3.97 mm**, active
> 48.96 x 73.44 mm, **50 pins**, **6 LED parallel** backlight. Four defects prevent
> locking: (1) **ILI9488 cannot send RGB565 over SPI** - it takes 3 bytes/pixel,
> a 1.5x bandwidth penalty an ST7796S-class part avoids; (2) the vendor states
> **"pin pitch 0.3 ~ 0.4 mm"** - a range, which directly violates D-049's *"no
> dependence on undocumented pin pitch"*; (3) module thickness is quoted
> inconsistently as 3.97 and 2.4 mm in the same document; (4) **the touch
> controller is never named.**
>
> **What is locked instead is the interface requirement**: 3.5-inch IPS 320x480,
> **ST7796S/ST7796U preferred**, I2C CTP of the FT6336U class with a published
> address, and a **single documented FPC pitch - 0.5 mm strongly preferred**.
>
> **The mating connector cannot be selected until the display's pitch, pin count
> and contact side are confirmed.** Choosing one now would repeat exactly the
> mistake this audit found. If the panel proves 50-pin 0.5 mm the existing
> FH69-50S-0.5SH is reusable; if 40-pin 0.5 mm, Hirose FH12-40S-0.5SH(55) is the
> candidate.
>
> **D-071 survives D-072 unchanged** - the larger display consumes front area, not
> rear volume, and the battery lives behind the PCB. The two rulings also offset
> each other on power: the 6-LED backlight raises browsing draw from ~100 mA to
> ~130 mA, while the larger pack takes capacity from 2000 mAh to ~2750 mAh, leaving
> runtime **flat to slightly better**.

---

## 8k. Display, connector and backlight LOCK (FBV2-DISP-002)

| # | decision | date |
|---|---|---|
| D-074 | **DISPLAY LOCKED: EastRising `ER-TFT035IPS-6` (3.5" IPS 320x480, ILI9488, COG) with `ER-TPC035-6` capacitive touch panel (FocalTech `FT6236`, I2C, address `0x38`).** Assembled outline **56.54 x 84.96 x 3.95 ± 0.25 mm**, active area 48.96 x 73.44 mm. | 2026-08-23 |
| D-075 | **FPC INTERFACE LOCKED: one 50-pin tail, 0.50 mm pitch, BOTTOM CONTACT, tail thickness 0.30 ± 0.03 mm, tail width 25.5 ± 0.15 mm, free length 30 ± 0.5 mm.** Display **and** touch leave the module on that single tail (touch on pins 44–47). All three no-guess parameters are printed in the vendor datasheet, Rev 2.0 of 18-Aug-2025. | 2026-08-23 |
| D-076 | **`J1` LOCKED: Hirose `FH69-50S-0.5SH` (HRS CL0580-5008-0-00).** 0.5 mm pitch, 50 pos, **top *and* bottom 2-point contact**, applicable FPC **0.30 ± 0.05 mm**, 2.3 mm height, backflip ZIF, 0.5 A / 50 V, −55…+125 °C. Compatibility is proven from **both manufacturers' drawings**, not from a matching pin count. D-073's concern is resolved: the connector was never the problem, and FH69 is contact-side agnostic so the classic dead-first-article failure cannot occur. | 2026-08-23 |
| D-077 | **`J1` is laid out on the FH12-horizontal / FH52E-50S-0.5SH STANDARD land pattern, not on FH69's dedicated pattern.** Hirose states FH69 fits that pattern; doing so makes **`FH52E-50S-0.5SH` (LCSC `C7465440`, JLCPCB-orderable)** a true drop-in second source with no board change. Beta-DM's FH69-dedicated footprint is retained in the library but is not the v2 footprint. | 2026-08-23 |
| D-078 | **ILI9488 is ACCEPTED in place of the preferred ST7796S/U.** No ST7796S 3.5" 320x480 IPS module with a capacitive touch panel, a named touch controller and a complete public FPC specification exists from a production supplier — ST7796S appears only on hobby breakouts, on touch-less LCMs, or with ambiguous FPC data. The cost is quantified and bounded: **+50 % SPI-A traffic; 46 ms (21.7 fps) full-frame at 80 MHz** against 31 ms for ST7796S. Acceptable for menus, graphs, logs and status screens. | 2026-08-23 |
| D-079 | **BACKLIGHT ARCHITECTURE UNCHANGED. `U17` TPS61169DCKR REMAINS**, boosting from `+3V3` as on Beta-DM. New values: **`R69` (RSET) = 1.87 R ±1 %** → 109 mA typ, 100.5–117.6 mA over the VREF band, always under the panel's 120 mA maximum; **`R70`–`R73` = 4 x 33 R in parallel = 8.25 R** on the single `LED_A` net. `L3`, `D8` and `C44` are all retained with verified margin (switch peak 263 mA against a 1.2 A limit, **4.6x**). Normal brightness is set by PWM on `DISP_BL_CTL`. | 2026-08-23 |
| D-080 | **Panel supply is `+3V3` for both VCI and VDDI. No 2.8 V rail, no level shifting, no new native GPIO.** 3.3 V is the top of the recommended range against a 4.6 V absolute maximum (1.39x). The interface-mode strap IM2/IM1/IM0 = 1/1/1 is hard-tied to VDDI and consumes no GPIO. | 2026-08-23 |

> **Result (FBV2-DISP-002).** Full analysis:
> [`audits/2026-08-23-display-procurement-lock.md`](audits/2026-08-23-display-procurement-lock.md).
>
> **FBV2-DISP-LOCK = PASS. M-06 CLOSED. M-07 CLOSED.** Schematic sheet
> `03_spi_a_display_sd` is unblocked; FBV2-S1 has no remaining display gate.
>
> **Fallback ranking.** #1 `ER-TFT035IPS-6`. **#2 `ER-TFT035-6`** — the same
> vendor's TN sibling, dimensionally and electrically identical (56.54 x 84.96,
> ILI9488, same 50-pin 0.5 mm bottom-contact tail, same FT6236 CTP), a true
> drop-in at the cost of IPS optics. **#3 VIEWE `UE035HV-RB40-A118`** — ST7365P +
> CHSC6540, conditional only, because at **61.5 mm** it is 1.5 mm over the width
> envelope. Riverdi `RVT35HITNWC00-B`, Focus LCDs `E35RG*`, Winstar
> `WF35UTYAIDNN0`, Raystar `RFI350U-AYW-DNN`, Newhaven's 3.5" line and
> DisplayModule `DM-TFT35-431` were each evaluated and rejected on a recorded,
> evidenced ground.
>
> **The backlight is cheaper than feared.** FBV2-DISP-001 assumed 6 x 20 mA and
> predicted roughly +50 % backlight draw. The real panel is specified at
> **120 mA maximum / 90 mA life point across six chips**, so per-LED current
> *falls* from 20 mA to 15 mA. At default brightness the pack sees
> **129 mA against Beta-DM's 118 mA — about +9 %** for 1.56x the area and 2x the
> pixels.
>
> **Two MEDIUM procurement risks remain, and both are closed on the purchase
> order rather than in the design:** the vendor also sells a CST340 touch panel
> for this size, so the PO must name `ER-TPC035-6`; and the datasheet carries a
> "Backlight Update" revision, so Rev 2.0 (18-Aug-2025) must be archived in-repo
> and cited by revision in the MPN ledger.

---

## 8l. Community expansion port and accessory power — LOCKED (FBV2-COMM-001)

> ### ⚠ THE 20-PIN COMMUNITY PORT ARCHITECTURE IS SUPERSEDED.
> **D-059 and D-062 no longer describe this product.** Nothing downstream may cite
> the 20-pin allocation. What survives from sections 8c/8d and is carried forward
> explicitly: **D-042** (no duplicate GPIO), **D-045** (native and XGPIO documented
> distinctly), **D-057** (no permanent raw `+3V3`), **D-058** (TPS22950C),
> **D-060/D-063** (native pair = GPIO38 + GPIO47).

| # | decision | date |
|---|---|---|
| D-081 | **NEW COMMUNITY PORT LOCKED: 2 rows x 12 positions, 24 ACTIVE contacts, no NC and no key contact.** Device side is **FEMALE**, recessed into the enclosure; the accessory side uses **standard MALE 2.54 mm pins**. **Mechanical keying, polarization and shrouding are provided by the ENCLOSURE**, not by the connector - see D-083. | 2026-08-23 |
| D-082 | **24-CONTACT ALLOCATION LOCKED: 10 x XGPIO + 2 x native ESP32 GPIO + 2 x external I2C + 1 x WAKE/ATTN + 2 x protected switched 3.3 V + 2 x protected switched 5 V + 4 x GND + 1 x `ACC_DETECT_N` = 24.** The duplicated contacts are **only** the two rails and ground, each a single electrical net, duplicated for contact resistance and accessory routing. **No GPIO is duplicated.** XGPIO falls from 11 to **10**, and that surrendered pin is exactly what pays for the fifth accessory-control expander pin. | 2026-08-23 |
| ~~D-083~~ | ~~**CONNECTOR LOCKED: Harwin `M20-7881242`**~~ **REJECTED AND SUPERSEDED 2026-08-23 by D-093 (FBV2-COMM-002).** Current manufacturer/distributor lifecycle information shows the part is obsolete; `harwin.com/products/M20-7881242` returns **HTTP 404**. The MPN had been *configured from the catalogue ordering scheme* rather than taken from a live listing, and FBV2-COMM-001 had flagged it for exactly this verification. **It must not appear anywhere as the production connector.** | 2026-08-23 |
| D-084 | **PIN ORDERING LOCKED** (odd pins = row A, even = row B): `1 XGPIO0`, `2 EXT_SCL`, `3 ACC_3V3_SW`, `4 GND`, `5 XGPIO1`, `6 EXT_SDA`, `7 NATIVE_A (GPIO38)`, `8 XGPIO2`, `9 GND`, `10 ACC_5V_SW`, `11 NATIVE_B (GPIO47)`, `12 XGPIO3`, `13 XGPIO4`, `14 WAKE_ATTN_N`, `15 ACC_3V3_SW`, `16 GND`, `17 XGPIO5`, `18 XGPIO6`, `19 XGPIO7`, `20 XGPIO8`, `21 GND`, `22 ACC_5V_SW`, `23 ACC_DETECT_N`, `24 XGPIO9`. **Every power contact is vertically paired with GND**, so no row-swap mis-insertion can put 5 V or 3.3 V onto a logic pin. **All 3.3 V is in row A and all 5 V in row B.** Both native pins flank the GND at pin 9. | 2026-08-23 |
| D-085 | **`ACC_DETECT_N` CONVENTION LOCKED.** The accessory asserts detect by shorting **pin 23 to the adjacent GND at pin 21** (one 0 Ω link); AQROOT provides a 100 k pull-up to `+3V3`. **Detection works with both accessory rails OFF**, because the pull-up and the expander run from `+3V3`. **Neither rail may be enabled unless `ACC_DETECT_N` is asserted** - which is also what makes a flipped accessory passively safe: it cannot ground pin 23, so it never receives power. | 2026-08-23 |
| D-086 | **3.3 V ACCESSORY RAIL: `+3V3` -> `TPS22950C` -> `ACC_3V3_SW`.** Verified against SLVSFJ2B: `VIN` 1.8-5.5 V, RCB **Yes**, `ILIM` 0.5-3.5 A adjustable, auto-retry, TSD 170 C, `FLT` open-drain, DDC SOT-23-thin. Default OFF with a **mandatory external 100 k pull-down** on `ON`. **`R_ILIM` = 1.5 k (approx. 0.76 A typ) RECOMMENDED, NOT fabrication-locked**; published limit **400 mA continuous** for the first five boards. | 2026-08-23 |
| D-087 | **5 V ACCESSORY RAIL (NEW): `BQ25185_SYS` -> a SECOND `TPS61023` at 5.0 V -> a SECOND `TPS22950C` -> `ACC_5V_SW`.** It is **not** USB `VBUS`, **not** the NFC fallback rail, and tied to neither; the only shared node is `SYS` on the input side. **`R_ILIM` = 1.65 k (approx. 0.69 A typ) RECOMMENDED, NOT fabrication-locked**; published limit **300 mA continuous** for the first five boards. Inductor **1 uH, I_sat >= 3 A**. | 2026-08-23 |
| D-088 | **BOM CONSOLIDATION LOCKED. One `TPS22950C` MPN on BOTH rails** - only `R_ILIM` differs. **`TPS61023` is REUSED** as the accessory boost, sharing inductor, feedback divider and capacitors with the DNP NFC fallback (D-056). One boost family and one load-switch family to validate, source, stock and rework. | 2026-08-23 |
| D-089 | **EXPANDER ALLOCATION LOCKED.** **`U3`**: `XGPIO0-9`, `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_DETECT_N`, **`ACC_POWER_FAULT_N`** and `SX1262_RXEN` = **15 assigned + 1 `RESERVED_SPARE`** *(amended 2026-08-23 by D-094 - the two `FLT` lines are wire-OR'd, freeing P16)*. **`U2` = 16/16**: the five pins freed by D-010/D-037/D-038 are exactly consumed by `BQ25185_STAT1/2`, `MAX17048_ALRT_N`, `VBUS_PRESENT` and `SX1262_DIO1`. **`U2` still has ZERO spare** (B-37, half closed). `ACC_5V_EN` drives the boost `EN` and the 5 V switch `ON` from one pin. Five new external safe-state pulls are mandatory. | 2026-08-23 |
| D-090 | **ALL COMMUNITY SIGNALS ARE 3.3 V CMOS ONLY. The 5 V power contact does NOT make any signal 5 V-tolerant.** Protection: **100 Ω series on every XGPIO and both native pins**, 22 Ω on the buffered I2C pair, 330 Ω on WAKE, plus a **low-capacitance TVS array on `NATIVE_A`, `NATIVE_B`, `EXT_SDA`, `EXT_SCL`** - the natives are the only contacts with a direct path to the MCU. **Bidirectional level translators are REJECTED**: they do not protect the A-side, they add direction ambiguity on bidirectional GPIO, and they would imply 5 V logic is supported, which it is not. Silkscreen: *"COMMUNITY PORT - 3V3 LOGIC ONLY / 5V PIN IS POWER OUTPUT ONLY"*. | 2026-08-23 |
| D-091 | **`WAKE_ATTN_N` ISOLATION GATE - closes B-08.** A single N-channel MOSFET pass gate (2N7002 / BSS138 class) between `WAKE_ATTN_N_HDR` and `WAKE_INT_N`, **gate driven by `ACC_3V3_SW`**. With accessory power off - the default - a shorted accessory pin can no longer hold `WAKE_INT_N` low, so internal button wake can never be blocked. **Consequence:** accessory-initiated wake requires `ACC_3V3_SW` to remain enabled during sleep (B-36). | 2026-08-23 |
| D-092 | **FIRMWARE MUTUAL-EXCLUSION CONTRACT - BINDING (closes P-15).** MX-1 at most ONE of {Wi-Fi TX, LoRa TX +22 dBm, sub-GHz TX, NFC field} at a time. MX-2 speaker <= 50 % during any MX-1 transmit. MX-3 rails enabled only while `ACC_DETECT_N` is asserted. MX-4 3.3 V before 5 V by >= 5 ms, reverse on disable. MX-5 on `FLT`, disable within 100 ms, report, require user action - **do not leave the switch auto-retrying into a short**. MX-6 on detect loss, disable both within 100 ms. MX-7 disable 5 V below `V_BAT` 3.4 V and 3.3 V below 3.2 V. MX-8 microSD and display must not transact simultaneously on SPI-A. MX-9 mask `U3` XGPIO interrupts by default, unmask only detect and the two `FLT`. | 2026-08-23 |

> **Result (FBV2-COMM-001).** Full analysis:
> [`audits/2026-08-23-community-expansion-closeout.md`](audits/2026-08-23-community-expansion-closeout.md).
>
> **COMMUNITY PORT LOCK = PASS. P-02, P-15 and P-16 CLOSED. B-08 CLOSED.**
>
> **Why the published accessory limits are below the CTO's targets on build 1.**
> Nothing about the switch or the connector prevents 800 mA - the TPS22950C is a
> 3.2 A part and the contacts are rated 3 A each. **The TPS63020 does.** A *shorted*
> accessory holds the load switch at `ILIM` until thermal shutdown; stacked on the
> internal worst case, `R_ILIM` = 1.15 k (600 mA published) reaches **101 % of the
> regulator's 2 A rating** - foldback, brownout, SD corruption. At 1.5 k the same
> fault reaches **86 %**. The target is met by changing one 0603 resistor once the
> internal worst case is measured on real boards. That is D-049 applied exactly as
> intended.
>
> **A structural advantage worth recording:** because the 5 V rail is boosted from
> `SYS` rather than derived from `+3V3`, it consumes **none** of the TPS63020's 2 A
> budget. Deriving it from `+3V3` would have cost roughly 500 mA of that budget.
>
> **One honest caveat on fault visibility.** SLVSFJ2B Table 9-1: `FLT` asserts on
> **thermal shutdown and reverse current only** - an output short leaves `FLT`
> Hi-Z while the device current-limits. In practice a hard short reaches TSD within
> tens of milliseconds and is then reported, but a **partial** overload inside the
> thermal envelope is invisible to the host. Firmware must not treat `FLT` as a
> complete overcurrent indication (B-35).
>
> **The three flagged opportunities were RULED ON 2026-08-23 (FBV2-COMM-002):**
> **O-1 APPROVED** - the two `FLT` lines are wire-OR'd into `ACC_POWER_FAULT_N`
> and `U3` P16 becomes `RESERVED_SPARE` (D-094).
> **O-2 APPROVED** - external I2C address `0x50` reserved for an optional
> accessory-ID EEPROM, protocol only (D-095).
> **O-3 REJECTED** - the accessory 5 V rail stays electrically independent of the
> NFC fallback; sharing the TPS61023 *family* is the extent of the consolidation
> (D-095).

---

## 8m. Community connector CORRECTION and final lock (FBV2-COMM-002)

> ### ⚠ HARWIN `M20-7881242` IS REJECTED.
> D-083 is struck. Current lifecycle information shows the part is obsolete, and
> `harwin.com/products/M20-7881242` returns **HTTP 404**. The MPN had been
> **configured from the catalogue ordering scheme** rather than taken from a live
> listing - FBV2-COMM-001 flagged exactly that risk and it materialised. **The
> community-port ELECTRICAL architecture is unaffected and remains locked.**

| # | decision | date |
|---|---|---|
| D-093 | **CONNECTOR LOCKED: Samtec `BCS-112-S-D-HE`** - .100 in / 2.54 mm, **2 x 12 / 24 contacts**, **FEMALE** Tiger Claw dual-beam receptacle, **horizontal (right-angle) entry**, **through-hole**, **30 uin selective gold** in the contact area with matte tin on the tail. **ACTIVE**; 385 pieces ship next-day from Samtec, **MOQ 1**, $7.314 @ 1 / $5.667 @ 100. Body **30.48 (L) x 8.13 (D) x 5.33 (H) mm**. Footprint: **2 x 12 PTH, 2.54 mm within a row, 7.87 +/-0.05 mm BETWEEN rows, 0.71 mm drill** - *not* interchangeable with any vertical 2x12 pattern. **4.6 A per contact** mated with TSW, 450 VAC / 636 VDC, **-55 to +125 C**, UL E111594, halogen-free, MSL 1. **`BCS-112-L-D-HE` (10 uin gold) is a plating-only cost-down alternate with an identical body and identical footprint - no board change.** | 2026-08-23 |
| D-094 | **O-1 APPROVED. The two TPS22950C open-drain `FLT` outputs are WIRE-OR'd into `ACC_POWER_FAULT_N`** - one 100 k pull-up, one PCAL9535A input (`U3` P15). **`U3` P16 becomes `RESERVED_SPARE`: no function is assigned to it.** It is brought out to a **test pad with a 100 k pull-up** so it reads a defined level and can be pressed into service by a wire and a firmware change rather than a respin. Rev 1 must retain at least one expander resource for recovery. **Rail attribution is by controlled isolation** (MX-5a): on a fault, disable one rail and observe whether `ACC_POWER_FAULT_N` clears. | 2026-08-23 |
| D-095 | **O-2 APPROVED, O-3 REJECTED.** **External I2C address `0x50` is RESERVED** for an optional AQROOT accessory-identification EEPROM - **protocol reservation only, no main-board hardware, and no accessory is required to carry one.** It joins the reserved table with 0x38 / 0x68 / 0x36 / 0x20 / 0x21. **O-3 is REJECTED: the accessory TPS61023 5 V rail must NOT be connected to the NFC fallback** - no DNP link, no shared node beyond `SYS`. Sharing the TPS61023 *device family* is the extent of the BOM consolidation. | 2026-08-23 |
| D-096 | **STANDING PROCUREMENT RULE.** A part number **configured from an ordering scheme is a hypothesis, not a selection.** Every MPN written into a locked document must first be confirmed against a **live manufacturer or distributor record showing lifecycle status and stock**. This rule is created by the `M20-7881242` failure and applies to every subsequent selection. | 2026-08-23 |
| D-097 | **ENCLOSURE KEYING AND LOAD PATH LOCKED.** The connector carries **no integrated key** - the BCS polarized-position option exists but consumes a contact, which D-081 forbids. Instead: socket face recessed **>= 1.5 mm** behind the right wall; recess walls form the shroud; **an asymmetric rib/step on the UPPER edge only** prevents upside-down insertion (the two mating rows are only 2.54 mm apart, so the key must be unambiguous); the recess is **CLOSED AT BOTH ENDS** with <= 0.3 mm clearance so a one-column offset is mechanically impossible; a moulded **shelf and backing rib capture the connector body**; and the accessory shell bottoms on an **enclosure boss** so the **~33 N average insertion force (peak higher)** is never carried by the 24 solder joints. Wall aperture **34 x 10 mm** nominal plus the key. | 2026-08-23 |
| D-098 | **ACCESSORY LIMITS AND THE SHARED-RAIL RULE.** First five boards: **`ACC_3V3_SW` = 400 mA TOTAL**, **`ACC_5V_SW` = 300 mA TOTAL**. Later validation targets, **only after measured bring-up and a CTO ruling**: 600-800 mA and 500 mA respectively. **THE TWO DUPLICATE CONTACTS ON EACH RAIL SHARE THE RAIL LIMIT - they do not double it.** `ACC_5V` pin 10 + pin 22 = 300 mA combined, **not** 300 mA each. There is one load switch and one current limit per rail. This must appear in accessory-facing documentation in these words. | 2026-08-23 |

> **Result (FBV2-COMM-002).** Full analysis:
> [`audits/2026-08-23-community-connector-correction.md`](audits/2026-08-23-community-connector-correction.md).
>
> **CONNECTOR LOCK = PASS. The 24-contact allocation (D-082) and the pin ordering
> (D-084) are UNCHANGED** - the BCS has the same 2 x 12 topology with the mating
> rows stacked vertically, so the whole mis-insertion argument carries over intact.
>
> **Why the locked MPN is `-S` and not the `-L` the CTO proposed.** Samtec's own
> design-qualification report (187544 Rev 1) gives **100 mating cycles for BOTH**
> the 10 uin (`-L`) and 30 uin (`-S`) gold options, and the E.L.P. extended-durability
> data - **2 500 cycles** - is qualified **by similarity at 30 uin gold only**. At
> `-L` the port would be rated **100 cycles**, which is *worse* than the rejected
> Harwin part's 300. For a **user-swappable community port**, mating-cycle life is a
> first-order product parameter. The `-S` upgrade costs **$2.88 per board at
> quantity one - about $14 across the first five boards.** Same body, same
> footprint, one character of the MPN.
>
> **Residual, B-39:** the 2 500-cycle figure is **by similarity**; the only figure
> formally qualified for BCS itself is **100 cycles**. Samtec must confirm the rated
> count for `BCS-112-S-D-HE` before the production run. The design assumption for
> the first five boards is *">= 100 cycles qualified, 2 500 supported by similarity
> at 30 uin gold"* - it is **not** claimed as 2 500.
>
> **Commodity compatibility is preserved, with one rule accessory builders must
> follow.** BCS accepts standard **0.64 mm (.025 in) square posts**, and the
> horizontal-entry engagement window is **4.34 mm to 6.35 mm**. An ordinary
> 2 x 12 2.54 mm header with a ~6.0 mm post qualifies; **extra-long-pin headers
> (8.13 mm / .320 in posts) must NOT be used.** Recommended reference mate:
> **`TSW-112-07-L-D`** (5.84 mm post), or a right-angle `-RA` variant for a
> coplanar accessory.
>
> **Z-stack improves.** The connector region falls from **22.30 mm to 19.53 mm** of
> the 23.0 mm external budget - **3.47 mm of real spare** - and is no longer the
> sole governing column; it is now level with the control region's 19.5 mm.
>
> **Two NEW opportunities are FLAGGED, NOT LOCKED:** **N-1** publish an accessory
> reference design (footprint, post-length rule, detect-strap pattern, shared-rail
> current rule, board-outline template) - high value, documentation-only, but it is
> a deliverable this task was not authorized to create; **N-2** accessory retention
> - withdrawal force is only ~20 N average with no latch, so an enclosure detent or
> captive fastener is worth considering, but it is a mechanical/ergonomic trade-off
> for enclosure CAD.

---

## 8n. Power-tree capture — FBV2-S1-001 (2026-08-23)

**This section records what the first Full Beta v2 design-file work found and
changed. It does not lock anything new.** The architecture it captured was already
locked by D-050…D-068 and D-086…D-094; what follows is the delta between those
rulings and what is now in `hardware/beta-v2/kicad/aqroot-beta-v2/01_power_tree.kicad_sch`.

| # | decision | date |
|---|---|---|
| D-099 | **`U18` LTC4368-1 PACKAGE CORRECTED — `Package_SO:MSOP-10_3x3mm_P0.5mm`.** The capture had assigned `Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm`. FBV2-PWR-002 locks the package policy for the battery-protection and recovery circuitry: *"every new safety-critical part is leaded and inspectable — MSOP-10, SOIC-8, SOT-23-8, SOT-23, SOT-363. No BGA, no WLCSP, **no bottom-terminated parts**."* A DFN-10 with an exposed pad is bottom-terminated, and this is the single most safety-critical part on the board. The locked candidate is **`LTC4368IMS-1#PBF`, MSOP-10**. Corrected in both the sheet and the project symbol-library default. **The land pattern remains UNVERIFIED — correcting a package is not verifying a footprint.** | 2026-08-23 |
| D-100 | **NET NAMES DESCRIBE NETS, NOT COMPONENT VALUES.** The inherited Beta-DM net label `R_FB_TOP 1M` — a value annotation placed as a label — is renamed **`V3V3_FB`** in `hardware/beta-v2/` only; it is the TPS63020 `+3V3` feedback midpoint (`R39` 1 M / `R40` 180 k, 3.278 V). Beta-DM is frozen and keeps the defect. **Standing rule:** a net name may not contain a component value or a space. Value annotations belong in on-sheet **text**, never in a label — a name like this also makes netclass patterns and every downstream net-name match fragile. | 2026-08-23 |
| D-101 | **`TP34` ADDED ON `BAT_CONNECTOR_P`.** The FBV2-PWR-002 block diagram calls for a test point on **each** side of `F1` — *"the two together make fuse state observable"* — and only the `BAT_RAW` side existed. Adding it also made `BAT_CONNECTOR_P` a real net, retiring two inherited ERC violations. | 2026-08-23 |
| D-102 | **`PWR_FLAG` IS PERMITTED ONLY WHERE A RAIL IS GENUINELY DRIVEN AND KICAD CANNOT INFER IT** — a connector pin, a battery, or a rail reached through a passive. `#FLG613` on `VREC_VCC` qualifies: the comparator supply is VBUS through `R84` 100 R with `C60`, and ERC does not propagate a driver across a resistor. **A `PWR_FLAG` may never be used to silence an error by joining, splitting or renaming a net**, and none was. The design now carries four, all for this reason: `USB_VBUS_CHG`, `BAT_PROTECTED_P`, `BAT_RAW`, `VREC_VCC`. | 2026-08-23 |
| D-103 | **`BAT_PROTECTED_P` IS LOCAL TO `01_POWER_TREE`.** Its root-sheet hierarchical pin is removed, along with the orphaned stub and label the removal left behind. **No sheet outside the power tree may reference the raw or protected battery node.** | 2026-08-23 |

> **Result (FBV2-S1-001).** Full analysis:
> [`audits/2026-08-23-s1-power-tree-implementation.md`](audits/2026-08-23-s1-power-tree-implementation.md).
>
> **Task gate FBV2-S1-POWER-TREE = PASS. The programme gate FBV2-S1 does NOT pass** —
> it requires every sheet in the migration order, and one of nine is landed.
>
> **B-01 is closed at schematic level only.** `BAT_CONNECTOR_P` is no longer a
> one-pad net and the full P2 chain to `BAT_PROTECTED_P` exists. The PCB is
> untouched and still bit-identical to Beta-DM, so nothing is closed at board level.
>
> **ERC: 58 Beta-DM baseline → 55, zero introduced.** Not "ERC clean".
>
> **Two value deviations were found and deliberately NOT changed:** `R95` = 680 R
> against a locked 560 R (**P-20**), and an `OV` trip of 5.05 V against a documented
> ≈ 4.6 V (**P-21**). **A value in a locked architecture is changed by a ruling, not
> by a capture task.** Both are ratio-preserving observations rather than wiring
> faults, and neither blocks the task gate — but P-20 moves the wrong way against
> **B-26**, so it should be ruled on before the BOM is issued.
>
> **A standing rule was overtaken and is NOT treated as repealed.** The Beta-DM
> README says *"Do not generate or modify KiCad schematic or PCB files
> automatically. KiCad files will be created manually in KiCad 10.0.3."*
> FBV2-S1-001 captured `01_POWER_TREE` **as a scripted migration**, then verified it
> with `kicad-cli` ERC and a netlist export rather than by eye. The rule is recorded
> in place, scoped to its Beta-DM origin, and **awaits ratification or
> reinstatement** — see the pending table.

## 8o. Power-tree rulings closed and MCU core migrated — FBV2-S1-002 (2026-08-23)

| # | decision | date |
|---|---|---|
| D-104 | **LTC4368-1 OV TRIP LOCKED at 4.63 V nominal** (closes **P-21**). `R77` **4.02 M → 3.65 M 1%**, `R78` unchanged at 442 k. **Derived, not typed:** the datasheet OV threshold is **492.5 / 500 / 507.5 mV** with 20 / 25 / 32 mV hysteresis and 10 nA max pin leakage (LTC4368 datasheet, Farnell mirror `2243878`; the features page states "Adjustable ±1.5 % Undervoltage and Overvoltage Thresholds"). 0.500 V × (3.65 M + 442 k)/442 k = **4.629 V**; tolerance band **4.48 – 4.78 V**, or 4.44 – 4.82 V including worst-case pin leakage; release **4.40 V** nominal. Above a 4.35 V-class pack with 129 mV of worst-case margin, 420 mV below the 5.05 V first capture, and **no lockout hazard** because release sits above the float voltage. `3.65 M` is already carried by `R91`, so this **removes** a BOM line rather than adding one. | 2026-08-23 |
| D-105 | **`R95` RECOVERY LIMIT LOCKED at 560 Ω** (closes **P-20**). Recovery current recomputed from the captured circuit: **8.36 mA** nominal at VBUS 5.0 V into a 0 V pack, **7.93 – 8.80 mA** over 4.75 – 5.25 V, inside the accepted 5 – 10 mA band. **B-27 IS AMENDED IN PLACE, NOT LEFT STANDING:** 680 Ω was the value that produced B-27's recorded ≈ 13 mA single-fault ceiling, and 560 Ω raises it to **≈ 15.9 mA nominal / ≈ 16.6 mA worst case** — 0.0066 C on a 2500 mAh pack, still bounded by `R95`, still unidirectional through `D12`, still self-annunciating. **The trade is explicit: ~21 % more recovery current for ~22 % more single-fault current, and the CTO ruled for recovery.** | 2026-08-23 |
| D-106 | **GPIO43 IS WITHDRAWN FROM THE COMMUNITY PORT.** `FAST_IO_U0TXD_ROOTPROBE_CS` no longer leaves the MCU sheet; GPIO43 is **internal UART0 TXD / debug only**, with `TP35`. The connector-side remnant (`R67`, `D7`, `J5.23`) is sheet `09` and dies with the 20-pin port. **Consequence recorded:** GPIO44 (U0RXD) is IR RX, so **UART0 is TX-only**, and ROM download recovery is therefore via the **native USB Serial/JTAG on GPIO19/20 — never over UART0**. | 2026-08-23 |
| D-107 | **STANDING ENGINEERING-PROCESS RULE — SCRIPTED KICAD EDITS** (closes **P-22**, supersedes the blanket Beta-DM prohibition). A scripted edit of a KiCad file is permitted **only when all eight hold**: (1) deterministic; (2) narrowly scoped; (3) source-controlled and diffable; (4) the project parses and opens afterwards; (5) netlist / connectivity validation performed; (6) ERC performed and diffed against a stated baseline; (7) preservation checks performed; (8) the output reviewed against the CTO task item by item. **Scripts may not be used to bypass engineering review.** A script that cannot show all eight is not a permitted edit — it is an unreviewed change. | 2026-08-23 |
| D-108 | **NATIVE COMMUNITY PINS LOCKED: GPIO38 = `NATIVE_A`, GPIO47 = `NATIVE_B`, and GPIO46 TAKES `DISP_BL_CTL`.** `SX1262_DIO1` leaves the MCU entirely and terminates on the internal expander `U2` (D-089). **GPIO46 is a strapping pin and MUST read LOW at reset** — GPIO0 = 0 alone does not select Joint Download Boot, GPIO46 = 0 is also required — so the backlight line carries three mandatory provisions: a **dedicated `R108` 10 kΩ pull-down at the MCU pin**, an **`R109` 0 Ω FIT isolation link** to the TPS61169 `CTRL` (a D-049 no-respin escape whose failure direction is "backlight off"), and **`TP2` on the strap node** so the level is measured, not assumed. **No capacitance may be added to this net.** | 2026-08-23 |
| D-109 | **GPIO3 STRAP DEFINED — `R110` 10 kΩ PULL-DOWN** (closes **B-09**). LOW is the only correct level: with `EFUSE_STRAP_JTAG_SEL` burned, GPIO3 = 0 selects the USB Serial/JTAG source, while GPIO3 = 1 would select external JTAG on MTMS/MTDI/MTCK/MTDO = **GPIO39–42, which are the I²S bus** — external JTAG is unusable on this board. **BINDING CONFIGURATION RULE: BMI270 `INT1` must be push-pull, active-high** (`INT1_IO_CTRL`: `output_en` = 1, `od` = 0, `lvl` = 1). **Open-drain is incompatible with a pull-down and must never be configured on this pin.** The IMU cannot corrupt the strap at reset because `INT1` is high-impedance until firmware enables it. | 2026-08-23 |
| D-110 | **NO NEW DEBUG HARDWARE. The service interface is the native USB Serial/JTAG on GPIO19/20** — one USB-C cable gives console, ROM download and JTAG debug. No debug connector, no debug IC, no FTDI, no JTAG header, and **no new user-facing button**; `SW1` BOOT stays electrically real and becomes mechanically recessed. **One test pad is added: `TP35` on UART0 TXD**, because the ROM boot log is the only view of a first board whose USB will not enumerate, which is the one failure USB itself cannot diagnose. An `EN` pad was considered and **rejected** as duplicating USB-side reset. | 2026-08-23 |

> **Result (FBV2-S1-002).** Full analysis:
> [`audits/2026-08-23-s1-mcu-core-implementation.md`](audits/2026-08-23-s1-mcu-core-implementation.md);
> measured pin ledger and strap audit:
> [`architecture/GPIO_LEDGER.md`](architecture/GPIO_LEDGER.md).
>
> **Task gate FBV2-S1-MCU-CORE = PASS. The programme gate FBV2-S1 remains OPEN — 2 of 9
> sheets.**
>
> **ERC: 5 errors on the Beta-DM baseline → 4. Zero new errors. `02_MCU_CORE` reports
> nothing at all.** Warnings rose 55 → 63; all eight are root-sheet `isolated_pin_label`
> warnings on cross-sheet signals whose far end is an unmigrated sheet, and **each was
> deliberately left standing** — silencing them by adding a test point to an orphaned net
> would be the same anti-pattern as a `PWR_FLAG` that hides a missing driver.
>
> **Two datasheet facts could not be retrieved and are blockers, not assumptions:**
> **B-43** the TPS61169 `CTRL` internal pull (the design is safe for any pull-up ≥ 30 kΩ
> and `R109` is the escape) and **B-44** the BMI270 `INT` pad drive current (fallback:
> `R110` → 47 kΩ, a value change with no board change). **B-45** opened: `NATIVE_A` /
> `NATIVE_B` still have no D-090 series resistors or TVS — they are the only two contacts
> with a direct MCU path, and the protection is sheet `09` work.
>
> **One item is referred to the CTO and was deliberately not decided here: whether to fit
> `R111`**, the 10 kΩ pull-down placed **DNP** on GPIO45. GPIO45 selects VDD_SPI — LOW =
> 3.3 V — and today it is held only by the chip's internal pull-down while an exposed test
> pad sits on the net. A GPIO45 that reads HIGH at reset selects 1.8 V and the 3.3 V flash
> and PSRAM do not boot. **Recommendation: fit it.** It is DNP rather than fitted because
> changing the electrical design of a strapping pin is a CTO call, not a capture decision.

## 8p. Display, touch, backlight and microSD — FBV2-S1-003 (2026-08-23)

| # | decision | date |
|---|---|---|
| D-111 | **`R111` FITTED — 10 kΩ, `GPIO45_VDDSPI_STRAP` to GND** (closes the pending `R111` item). GPIO45 selects VDD_SPI and **LOW = 3.3 V**, which is what the WROOM-1's flash and PSRAM require; a GPIO45 that reads HIGH at reset selects 1.8 V and the module does not boot. **The internal pull-down is no longer relied on alone.** `TP1` is retained on the strap, **no capacitance** is present on the net, and GPIO45 carries **no peripheral**. | 2026-08-23 |
| D-112 | **DISPLAY SYMBOL REPLACED — `ER-TFT035IPS-6_50P`, pin table verbatim from the vendor datasheet Rev 2.0 §4.1.** The inherited `J1` still used the **2.8-inch `CH280QV10_CT_50P`** pin table while its Value and Footprint already said FH69, and it was **wrong in two dead-on-arrival ways**: panel pin 1 is **LEDA** with **LEDK on 2 and 3** (the old symbol had LEDK on 1 and four anodes on 2–5, so the backlight would have been **reverse-biased**), and pins **36/37 are WRX(SCL)/D-CX** (the old symbol had them reversed, so **the panel would never have received a valid command**). Neither fault is visible from a pin count, a connector MPN or an ERC run. **The PO must name BOTH `ER-TFT035IPS-6` and `ER-TPC035-6`; the vendor's CST340 touch variant is NOT authorised without a new engineering review** — the FT6236 address, driver and reset pulse are all locked around FT6236. | 2026-08-23 |
| D-113 | **`J1` STAYS ON THE FH69-DEDICATED LAND PATTERN, and FH52E IS NOT CLAIMED AS A DROP-IN.** FBV2-DISP-002 proposed migrating to the FH52E/FH12 standard pattern on the strength of a Hirose note that **FH69 also fits the FH52E pattern** — that proves one direction only. Full footprint **and mechanical** equivalence was not demonstrated from both manufacturers' drawings, so it is not asserted. **Primary first-build connector remains `FH69-50S-0.5SH`,** for which the drawn pattern is unambiguously correct: **measured 50 pads, 0.500 mm pitch with no drift, 24.500 mm span, 0.300 × 1.230 mm pads, 2 hold-downs.** **Consequence: there is currently no JLCPCB assembly path for `J1`** (FH69 is not in LCSC; FH52E is, as `C7465440`). **B-47** — settle at FBV2-S2, before placement makes the pattern expensive to change. | 2026-08-23 |
| D-114 | **DISPLAY `SDO` ISOLATION `R112` = 0 Ω, DNP BY DEFAULT** (closes **B-28**, with the **opposite** default to the one FBV2-DISP-002 sketched). The vendor says of pin 33 *"leave the pin open when not in use"* and does **not** specify SDO's high-Z behaviour while `CSX` is high; SPI-A is shared with the microSD. **The risk is asymmetric: fitting it puts a core feature (microSD) at risk of bus contention to gain a feature nothing uses (AQROOT never reads the display).** `TP36` observes SDO on the panel side, so the behaviour can be characterised on the first board without fitting anything. **No series resistance was added to the `SPI_A_MISO` bus itself** — the microSD `DAT0` path stays direct. | 2026-08-23 |
| D-115 | **BACKLIGHT RE-DERIVED FROM THE DATASHEET. `R69` = 1.87 Ω ±1 % (E96, stocked); `R70`–`R73` = 4 × 33 Ω in parallel = 8.25 Ω on the single `LED_A` node.** From SNVSA40B `V_REF` = 188/204/220 mV: **I_LED = 100.5 / 109.1 / 117.6 mA**, i.e. **109 mA typical and 117.6 mA worst case against the panel's 120 mA maximum** — 2.0 % of headroom, never exceeded. Per-LED current **falls** from 20 mA to 18.2 mA, so LED life improves. Peak switch current **263 mA at 1.2 MHz (4.6×) and 309 mA at the 0.75 MHz minimum (3.9×)** against the 1.2 A minimum limit. **`D8` NSR0240 at 2.1× is the tightest item and is retained**; a same-footprint 0.5 A uprate is recommended, not required. **B-32 CLOSED** — `C43` 4.7 µF X5R sits on `U17` `VIN`. | 2026-08-23 |
| D-116 | **GPIO46 STRAP SAFETY PROVEN — B-43 CLOSED.** TPS61169 SNVSA40B specifies **`R_PD`, a 300 kΩ internal pull-down on `CTRL`**, with `V_H`/`V_L` = 1.2 / 0.4 V and `t_SD` = 2.5 ms. **`CTRL`'s only internal element pulls DOWN; there is no mechanism by which the backlight driver can raise the strap.** With `R108` 10 kΩ in parallel GPIO46 sees **9.68 kΩ to GND** — stronger than the strap provision alone — and the backlight is off through reset by construction. **`R109` 0 Ω is retained**: its strap-escape justification is retired, but a fitted 0 Ω costs nothing and remains a general isolation and rework point. GPIO46 strap safety was **not** weakened for backlight convenience. | 2026-08-23 |
| D-117 | **`SD_CARD_DETECT_TBD` IS RETIRED. The signal is `SD_CARD_DETECT_N`** — `J2.10` DET-SW with **`R113` 100 kΩ to `+3V3`** and `J2.11` DETECT_LEVER grounded, so a one-pad net becomes a real two-state signal. **Its destination is an internal PCAL9535A input on sheet `08`.** Polarity assumes the usual push-push convention (switch closes on insertion, **LOW = card present**); the Molex drawing would not load, so this is **assumed, not confirmed** (**B-46**) — and the exposure is nil, because polarity is a firmware constant on an expander input, never a board change. **No `*_TBD` net remains on sheet `03`.** | 2026-08-23 |

> **Result (FBV2-S1-003).** Full analysis:
> [`audits/2026-08-23-s1-display-sd-implementation.md`](audits/2026-08-23-s1-display-sd-implementation.md).
>
> **Task gate FBV2-S1-DISPLAY-SD = PASS. The programme gate FBV2-S1 remains OPEN — 3 of 9
> sheets.**
>
> **ERC: 4 errors → 4 errors, the error report byte-identical to after FBV2-S1-002.** Total
> 63 → 64: two `isolated_pin_label` warnings added for the new `TOUCH_INT_N` crossing, one
> removed because `SD_CARD_DETECT_TBD` ceased to exist.
>
> **Touch gains an interrupt.** `CTP_IRQ` (panel pin 46) was not represented at all on
> Beta-DM; it now leaves the sheet as `TOUCH_INT_N` and lands on an internal PCAL9535A input
> with sheet `08`. FT6236 at **0x38** and the `TOUCH_RST_N` safe state are unchanged, and
> **no second I²C pull-up pair was added** — the internal bus keeps its single locked pair.
> **`RESERVED_SPARE` was not consumed.**
>
> **SPI-A stays passive and simple.** Both chip selects are pulled to `+3V3` so display and
> microSD are deselected through reset; **no bus mux and no series damping were added**, and
> damping is deferred to FBV2-P1 where real trace lengths exist. The ILI9488's 18-bit /
> 3-byte-per-pixel SPI writes are accepted with no architecture change and **no new native
> GPIO**.
>
> **The battery target is unchanged.** The backlight is the only load this task moved:
> **+11 mA at the pack** at default brightness. Runtime improves for any baseline browsing
> current above **44 mA**, and the Beta-DM backlight alone draws 118 mA — so **60 × 75 × 8 mm
> / ~2500–3000 mAh delivers equal or better runtime by a wide margin.**
>
> **One latent defect was caught by inspection rather than by any check:** the `LED_BOOST`
> netclass listed the four old anode nets by exact name and had no entry for the new single
> `LED_A`, so it would have fallen to Default clearance at FBV2-P2. `netclass_probe.py` reads
> the *board*, which is still Beta-DM, so no probe would have caught it.
> `/03_SPI_A_DISPLAY_SD/LED_A` was added to `LED_BOOST`.

## 8q. Radios and NFC — FBV2-S1-004 (2026-08-23)

| # | decision | date |
|---|---|---|
| D-118 | **RF ARCHITECTURE LOCKED. 433 MHz = INTERNAL flex; 915 MHz = EXTERNAL bulkhead.** `U7` IPEX → 100 mm coax → Taoglas `FXP450.07.0100C` against a plastic wall; `U8` IPEX → short pigtail → **top-panel SMA bulkhead**, user-changeable. **Neither band has a motherboard 50 Ω RF trace, a matching network, an RF switch or a diplexer** — both modules present their own matched 50 Ω port, so the board's RF involvement at 433/915 MHz is *zero copper*. **This supersedes the internal-FXP890 plan for 915 MHz** in `12 - RF and Antenna Plan v0.1`; 433 MHz is unchanged. **The `U7` IPEX socket must remain SERVICE-ACCESSIBLE with the shell open** — if internal 433 performance disappoints on the first units the flex unplugs and an external pigtail replaces it with **no PCB respin** (D-049). That is an FBV2-P1 placement constraint. | 2026-08-23 |
| D-119 | **433 ANTENNA VERIFIED: `FXP450.07.0100C`.** Datasheet `SPE-23-8-180-A`, verbatim: *"410-470MHz Flexible PCB Antenna with 100mm 1.37 IPEX MHFI"*; **47 × 17 × 0.28 mm**; adhesive mount; gain −0.36 / −1.57 / −0.05 dBi; **Active, 54 in stock, $5.52 @ 1, MOQ 1**. **Connector mating is PROVEN, not assumed**: the antenna terminates in **IPEX MHF I** and Ebyte's manual lists the `E07-400M10S` interface as **IPEX-1 / stamp hole** — MHF I, IPEX-1 and U.FL are one interface. No cable variant is needed. **Mechanical reservation (FBV2-P1 keepout):** plastic wall, LEFT/LOWER-SIDE region, **NOT on the PCB**, clear of the LiPo, the NFC loop and ferrite, the speaker magnet, large ground pours, metal bosses, the USB shell, the 915 bulkhead/pigtail and the IR structures. | 2026-08-23 |
| D-120 | **915 EXTERNAL INTERFACE DEFINED.** `U8` **IPEX-1/MHF-I plug** → **1.13 mm or RG-178, 100–150 mm** → **SMA FEMALE (jack) bulkhead, top panel**. **Female is deliberate**: the 915 MHz LoRa ecosystem is SMA-male antennas onto female jacks; RP-SMA is a Wi-Fi convention and would force an adapter for no benefit. Cable loss **≤ 0.3 dB** — negligible against +22 dBm. **No proprietary interface.** **The interface is locked; the assembly MPN is NOT** — under D-096 a pigtail part number must come from a live listing (B-51). **Top panel: ≥ 8 mm edge-to-edge between the SMA body and either IR aperture, and the pigtail must not cross the IR optical path** (B-52, no CAD created). | 2026-08-23 |
| D-121 | **BOTH MODULE STAMP-HOLE FEEDS ARE EXPLICIT NO-CONNECTS.** `U7.21` and `U8.21` `ANT` are the alternative 50 Ω stamp-hole pads; AQROOT feeds both modules through their IPEX sockets, so the pads stay unconnected. `CC1101_ANT_TBD`, `RF_ANT_TBD`, `CC1101_RF_TBD` and `SX1262_RF_TBD` are **retired** — the last two were orphan labels on stubs connected to nothing and were **two of the project's four ERC errors**. | 2026-08-23 |
| D-122 | **NFC SUPPLY MOVED — B-41 CLOSED.** `U9` pin 8 `VDD` and pin 10 `VDD_TX` leave the Beta-DM boost output and sit on **`NFC_SUPPLY`**; `VDD_IO` (pin 1) stays on `+3V3`. First build **`NFC_SUPPLY` = `+3V3`** through the `R106` FIT link; the `R107` DNP link remains the one-resistor, no-respin 5 V fallback. **NFC is never connected to the community 5 V rail.** **FIRMWARE MUST SET `sup3V`.** Sheet 01 received **two label changes and one `PWR_FLAG`, no component, value or topology change**: its `NFC_SUPPLY` label became hierarchical so the net can leave, and its `NFC_5V_PA_PENDING` hierarchical label became local because that net no longer needs to cross. The `PWR_FLAG` is **D-102-compliant** — the rail is genuinely `+3V3` through a 0 Ω link and KiCad cannot propagate a driver across a passive; **the netlist is unchanged by it**. | 2026-08-23 |
| D-123 | **NFC CLOCK RESOLVED. `Y1` = 27.12 MHz, 10 pF load, SMD 3225 4-pad**, with `C79`/`C80` **10 pF 50 V C0G, TUNE**. DS12484 §2.2.8: *"The quartz crystal oscillator operates with 27.12 MHz crystals."* Candidate MPN **`TXM27.12M0004322DBBDO00T`, LCSC `C362365`** — ±10 ppm, ESR 30 Ω, −40…+85 °C, **3,420 in stock, $0.078** — a JLCPCB-compatible part, and a **candidate against a live listing, not a lock** (D-096). Load-cap sizing stated openly: `C_L` = `C/2 + C_stray` gives ≈ 14 pF ideal, **ST's own NUCLEO and DISCO boards populate 10 pF**, so the design starts at 10 pF and trims — the value depends on finished-board stray capacitance that does not exist yet. | 2026-08-23 |
| D-124 | **NFC FRONT END: REAL TOPOLOGY, HONEST VALUES.** Captured per side: `RFOx → L_EMC → [C_EMC ∥ C_p to GND] → C_s → R_q → antenna`, and `antenna → C_rx_s → [C_rx_p to GND] → R_rx → RFIx`, terminating on `NFC_ANT_A`/`NFC_ANT_B` with **`TP37`/`TP38`** — the measurement points without which the network cannot be tuned at all. **Every part is 0603 and hand-reworkable; every RF capacitor is 50 V C0G** because the antenna tank swings far above the 3.3 V driver supply. Two deliberate choices: **`C_EMC` and `C_p` are two separate shunt footprints on one node** (two trim positions instead of one), and **`R_q` is fitted at 0 Ω rather than omitted** so damping is a component change and not a bodge. **ALL VALUES ARE INITIAL AND LABELLED `TUNE`** — they cannot be finalised until the antenna impedance is measured and **STSW-ST25R004** is run against it, and **AN5276 could not be retrieved this session** (B-48), so no value is presented as an ST reference figure. **Unused pins are explicit no-connects with recorded reasons:** `AAT_A`/`AAT_B` (AAT needs external varactors, and DS12484 warns against AAT with hardware wake-up), `CSI`/`CSO` (capacitive sensing unused), `EXT_LM` (internal load modulator is used), `MCU_CLK` (the ESP32-S3 has its own clocks). **No `*_TBD` net remains anywhere in the project.** | 2026-08-23 |
| D-125 | **THE NFC FIELD CURRENT HAS CHANGED RAILS, AND THE BUDGET DOES NOT YET COVER IT.** With `VDD`/`VDD_TX` on `NFC_SUPPLY` = `+3V3`, the NFC PA load moves off `BQ25185_SYS`-via-`U13` and onto the **TPS63020**, drawing proportionally more current at 3.3 V for the same field power. **`I_VDD_TX` at 3 V supply mode was not extracted this session (B-54)**, so D-092's 58–66 % TPS63020 figure **must not be quoted as including the NFC field in this form**. **MX-1 is unchanged and binding: at most ONE of {Wi-Fi TX, LoRa TX +22 dBm, sub-GHz TX, NFC field} at a time.** Firmware constraints recorded by this sheet: set `sup3V`; enable SX1262 **DIO2-as-RF-switch** or `TXEN` never asserts and TX silently fails; configure the SX1262 driver for **TCXO** (`DIO3`, 2.2 V, internal); drive all three bus-B chip selects high before init and use a bus mutex. | 2026-08-23 |

> **Result (FBV2-S1-004).** Full analysis:
> [`audits/2026-08-23-s1-radios-nfc-implementation.md`](audits/2026-08-23-s1-radios-nfc-implementation.md).
>
> **Task gate FBV2-S1-RADIOS-NFC = PASS. The programme gate FBV2-S1 remains OPEN — 4 of 9
> sheets.**
>
> **ERC: 4 errors → 2. Total 86 → 68. Zero added, eighteen removed.** This is the first
> migration task to *reduce* the project's error count, and it did so by deleting
> placeholder architecture rather than by suppressing anything.
>
> **`SX1262_DIO1` is published as a hierarchical net** for sheet `08` to land on the
> internal PCAL9535A (D-089). It no longer reaches the MCU; GPIO38 is `NATIVE_A`.
> Semtech §13.3.4 confirmed DIO1 is a level-holding, SPI-cleared IRQ, so a PCAL9535A input
> is a safe destination and a stuck-high DIO1 can no longer touch a strapping pin — which
> was the reason for moving it.
>
> **No ESD part was added on any RF interface, and that is the finding.** The 915 MHz
> bulkhead sees only the E22's own matched front end through a shielded pigtail — there is
> no board trace and no exposed IC pin. An RF TVS transparent enough not to cost link budget
> at +22 dBm is a real choice with real loss; **measure before adding**. The NFC loop is
> magnetically coupled with series capacitors as a DC block, and the module coax is internal
> and shielded.
>
> **Two items are recommended, not locked, and need CTO sign-off** — see the pending table:
> **P-17** (keep the non-B ST25R3916) and **B-53** (NFC antenna architecture; recommendation
> is a purchased flex + ferrite).

## 8r. NFC IC and antenna FINAL LOCK — FBV2-S1-004B (2026-08-23)

| # | decision | date |
|---|---|---|
| D-126 | **NFC IC LOCKED: `ST25R3916-AQET`. The B variant is NOT adopted. P-17 CLOSED.** CTO reasons as given: the non-B is active production; it **preserves capacitive low-power sensing**; AQROOT is not an EMVCo payment terminal; AWS is not worth trading sourcing simplicity and feature breadth for; and the first build already has 3.3 V operation plus a no-respin 5 V fallback. This agrees with the FBV2-S1-004 recommendation on independent grounds — the non-B is the **only one of the two with an LCSC part number (`C5267441`) and therefore a JLCPCB assembly path**, at roughly half the unit cost. **MPN metadata verified present in the schematic**, not merely in prose: `Value`, `MPN`, `Manufacturer` and `LCSC` all carry it. `U9`'s stale `Package` description — which still named `NFC_5V_PA_PENDING` and told the reader the RF and oscillator pins were "on explicit named TBD nets, DO NOT ROUTE" — is **rewritten**; both statements became false in FBV2-S1-004. | 2026-08-23 |
| D-127 | **NFC ANTENNA LOCKED: Taoglas `FXC.46.52.0075X.A.dg`, OFF-BOARD. B-53 CLOSED.** Verified verbatim from Taoglas `SPE-22-8-131-C`: *"Circular Form Factor Flexible Near Field Communications Antenna"*, **13.56 MHz**, **diameter 46 mm**, *"Thickness: 0.27 mm - FXC.46.52.0075X.A.dg - NFC with ferrite and 75mm Twisted Pair 28AWG cable with ACH(F) connector"*, *"Peel and stick 3M adhesive"*, **typical interrogation distance 40 mm**, RoHS & REACH. This **replaces the abstract 45 × 45 mm custom-antenna assumption** and closes the last architectural question on the NFC block. **The antenna does not go on the main PCB** — that is what avoids a 45 × 45 mm keepout in the ground plane of a board carrying three radios. **The electrical triple `L` = 1.09 µH, `Rs` = 1.6 Ω, `Q` ≈ 58 is used as supplied and checks out internally (`ωL/Rs` = 92.87/1.6 = 58.0 exactly), but could NOT be re-extracted** — the datasheet's electrical table is an image — so it is recorded for first-article confirmation (**B-55**), which costs nothing because the match must be re-derived from measurement anyway. | 2026-08-23 |
| D-128 | **BOARD-SIDE ANTENNA CONNECTOR: `J7` = JST `BM02B-ACHSS-GAN-ETF`.** ACH series, **2 circuits, 1.20 mm pitch, SMT, gold, 2.0 A / 50 V, −25…+85 °C, 1.4 mm high × 4.3 mm wide**; **Active, 30,004 in stock, $0.52 @ 1, MOQ 1**. **Mating is PROVEN, not assumed:** its mating housing is **`ACHR-02V-S`**, which is exactly the *"ACH(F) connector"* Taoglas fits to the `FXC.46` cable, and the antenna's 28 AWG wire is the gauge JST rates the series at. **The antenna is therefore replaceable without soldering.** KiCad's footprint is named for this exact MPN. **CORRECTION TO THE BRIEF: JST classes ACH as a TOP-ENTRY header, not right-angle** — *"the socket half is mated with the header from the vertical direction, while the wires come out from the horizontal direction"*. The part is unchanged and correct; the consequence is that **`J7` needs mating clearance above it** while the cable leaves horizontally. FBV2-P1 placement note. | 2026-08-23 |
| D-129 | **MATCHING NETWORK RE-DERIVED AGAINST THE REAL ANTENNA — AND WHAT WAS NOT.** **`R_q` 0 Ω → `1R0` is the solid number**, because it depends on the antenna alone: `Q0` = 58 is far too high for ISO14443 bandwidth, `wL/Q_target` = 92.87/26 = 3.57 Ω total, minus `Rs` 1.6 Ω leaves 2.0 Ω across two legs → **1 Ω per leg, `Q` = 25.8**. **`C_s` 100 pF → 300 pF** and **`C_p` 100 pF → 1.8 nF** follow from an L-match lifting the damped 1.8 Ω per side to an **ASSUMED 20 Ω per side driver target** — right shape and right order of magnitude, not a validated match, because AN5276 still could not be retrieved. **`L5`/`L6` and `C69`/`C70` were deliberately NOT re-derived and are now inconsistent with the network around them**: 220 nH against ~2 nF of shunt resonates near **7.6 MHz, below the 13.56 MHz carrier**. **NOBODY MAY BUILD TO THE CURRENT EMC VALUES** — the on-sheet note says so in those words, and it is **B-56**. Everything stays `TUNE`, everything is 0603 and hand-reworkable, and **switching to the 5 V fallback is a re-tune of these same passives, never a respin**. | 2026-08-23 |
| D-130 | **NFC FIELD CURRENT — CONSERVATIVE ESTIMATE, B-54 DOWNGRADED.** DS12484's current tables still would not text-extract, so this is derived and labelled as such: a 3.3 V differential square-wave driver into the assumed 40 Ω differential match delivers ≈ 0.22 W of RF; at 60–70 % driver efficiency that is 95–112 mA from `+3V3`, plus ~20–30 mA of reader-mode overhead. **Budget ≤ 150 mA from `+3V3` with the field on.** Against D-092's enforced case (1.16–1.32 A) that takes the TPS63020 to **≈ 66–74 % of 2 A** — comfortable, and **MX-1 means the NFC field is never concurrent with LoRa TX anyway**. **No simultaneous RF operation is claimed.** The datasheet figure or a bench measurement is still owed before fabrication. | 2026-08-23 |

> **Result (FBV2-S1-004B).** Full analysis:
> [`audits/2026-08-23-s1-nfc-antenna-closeout.md`](audits/2026-08-23-s1-nfc-antenna-closeout.md).
>
> **Task gate FBV2-S1-NFC-ANTENNA-LOCK = PASS.** **ERC 68 → 68 — zero added, zero removed,
> the violation lists are identical.** 301 components, 0 duplicate references, 0 without a
> footprint.
>
> **B-06 is CLOSED.** "NFC is undesigned, not merely unrouted" has been true since the
> pre-design audit. It is not true any more: crystal, matching topology, antenna, connector
> and supply all exist. What remains is *tuning*, which is a bench activity, not a design gap.
>
> **A reference collision was caught before it reached the netlist:** the new connector was
> first drawn as `J6`, which is already the speaker connector on sheet `06`. It is `J7`.
>
> **Nothing prohibited was added.** No full RF test connector, no AAT varactor network, no
> extra RF switches — no technical blocker required any of them. `TP37`/`TP38`, `TP32` and
> the `R106`/`R107` source-select links were already in place.
>
> **One item is flagged for CTO/user decision and was deliberately not changed: the ferrite
> is directional.** Taoglas catalogues an otherwise identical **reverse-ferrite** version of
> this same 46 mm antenna with the same ACH(F) cable. Which one is correct depends on which
> face bonds to the enclosure wall — the ferrite must end up between the coil and the metal
> it shields. **Zero board and schematic change either way; it is a purchasing line item** —
> but ordering the wrong orientation costs a lead time, not a rework, so it must be settled
> against the actual enclosure stack before the first antennas are ordered.

## 8s. NFC ferrite orientation and first-build matching — FBV2-S1-004C (2026-08-23)

| # | decision | date |
|---|---|---|
| D-131 | **NFC ANTENNA CORRECTED: `FXC.46.52.0075X.A.dg` is SUPERSEDED; `FXC.46.52.0075X.B.dg` is LOCKED.** Verified verbatim from Taoglas `SPE-24-8-104-B`: *"NFC Flex Antenna (46*0.3mm) with a **Reverse Ferrite Layer** and adhesive backing"*, *"13.56 MHz Antenna"*, *"Diameter: 46mm"*, *"FXC.46.52.0075X.B.dg - NFC with ferrite and 75mm Twisted Pair 28AWG cable with ACH(F) connector"*, *"Peel and stick 3M adhesive"*. Per APN-24-8-001 the variants differ **only in stack order**: **A** is *flex / ferrite / adhesive*, for bonding **onto a PCB or component surface**; **B** is *adhesive / flex / ferrite*, for bonding **to the INSIDE of the enclosure and reading through it**. **AQROOT bonds to the inner rear shell and reads outward — the B case exactly.** With the A version the ferrite would sit **between the coil and the tag**, which is the one place a flux director must never be. **Connector, cable, diameter, adhesive and interface are unchanged, so `J7` and the board are unaffected** — this is a purchasing-line change caught before antennas were ordered, which is precisely why FBV2-S1-004B flagged it. **No `…A.dg` reference remains anywhere in `hardware/beta-v2/`.** | 2026-08-23 |
| D-132 | **B-VERSION PARAMETERS ADOPTED: `La` = 1.10 µH, `Rs` = 1.50 Ω, `Q` = 60.37, `SRF` = 395 MHz.** `ωL` = 93.72 Ω at 13.56 MHz. **The published triple is coherent to ~3 %** — `Q` 60.37 with 1.10 µH implies `Rs` 1.55 Ω rather than 1.50 Ω — which is ordinary rounding between separately-published figures and is recorded rather than smoothed over; `Rs` = 1.50 Ω is used for damping because it is the resistance that physically adds to `R_q`. **The 395 MHz SRF is a large improvement on the A version's 148 MHz**, so the coil behaves as a clean inductor across the band. | 2026-08-23 |
| D-133 | **TARGET IMPEDANCE DERIVED FROM THE CURRENT BUDGET, NOT ASSUMED. The previous 20 Ω/side figure is DISCARDED.** AN5276 offers two design intents — maximum power transfer, or *"a certain current consumption"* — and AQROOT has a locked budget (D-130: ≤ 150 mA from `+3V3` with the field on, ~20–30 mA of it reader overhead), so the second intent **determines** the target: 115 mA × 3.3 V = 0.380 W in, ~65 % driver efficiency → 0.247 W RF; a differential square wave at `VDD_TX` = 3.3 V has a 2.971 V RMS fundamental, so **Z = 8.827 / 0.247 = 35.7 Ω differential**. **First-build target: Z ≈ 36 Ω differential (18 Ω per side), Q ≈ 25.** No EMVCo constraint applies, so Q is set purely by ISO/IEC 14443 bandwidth at 106 kbit/s. | 2026-08-23 |
| D-134 | **FIRST-BUILD MATCHING SET — CALCULATED, AND DELIBERATELY BIASED TO THE SAFE SIDE. B-56 CLOSED.** `R_q` **1R0 → 1R1 1%** (`Q` 62.5 → **25.3**; still the most trustworthy value on the sheet because it depends on the antenna alone). `C_s` **300 pF** per leg: the ideal is 284 pF, and **the E24 neighbours are not close in effect — 270 pF gives ≈ 16 Ω and 257 mA (over budget), 300 pF gives ≈ 68 Ω and ≈ 60 mA.** 300 pF is chosen **on purpose**: on a first board an under-driven antenna is a one-component swap while an over-driven one risks the driver and the rail, and 187 mA of coil current in a 46 mm loop is still a serviceable field. `C_p` **1.8 nF → 1.5 nF**, re-solved for the resulting match. **EMC filter `L5`/`L6` 220 nH → 39 nH and `C69`/`C70` 220 pF → 100 pF**: with the 1.6 nF total shunt that puts the cut-off at **20.1 MHz**, outside AN5276's forbidden 13–14 MHz band — **the previous pair sat at 7.6 MHz, BELOW the carrier**, and also presented 18.7 Ω of series reactance that was badly perturbing the match. **Every value remains `TUNE`, but `TUNE` now means "expected to move at first article", not "unknown": each is a CALCULATED FIRST-BUILD VALUE with its arithmetic recorded. CALCULATED FIRST-BUILD VALUE is not FINAL TUNED VALUE.** | 2026-08-23 |
| D-135 | **RFI INPUT SAFETY — A REAL DEFECT WAS FOUND AND FIXED.** At full field the first-build network puts **49.5 V pk-pk differential** across the coil, i.e. **24.8 V pk-pk per side**. **The previous 47 pF / 220 pF divider has a ratio of 0.176 and would therefore have placed ≈ 4.4 V pk-pk on `RFI1`/`RFI2` — against a 3.0 V regulated analog rail.** That is a part-stress condition, not a tuning imperfection, and it had been carried as a placeholder without ever being checked against a real antenna voltage. **New divider `C75`/`C77` 47 pF → 27 pF and `C76`/`C78` 220 pF → 620 pF**, ratio 0.0417 → **≈ 1.03 V pk-pk per side, over 3× headroom to the rail**. Purely capacitive, no DC path; it adds ≈ 26 pF of shunt at the antenna node, small against `C_p` = 1.5 nF. **No 5 V reference divider was reused blindly** — the ratio comes from this design's own antenna voltage at 3.3 V. The receiver's exact linear range could not be extracted from DS12484 (**B-58**), so §8 step 6 of the tuning plan is a **pass/fail gate**, not an optimisation. | 2026-08-23 |

> **Result (FBV2-S1-004C).** Full analysis:
> [`audits/2026-08-23-s1-nfc-matching-closeout.md`](audits/2026-08-23-s1-nfc-matching-closeout.md).
>
> **Task gate FBV2-S1-NFC-MATCHING = PASS. ERC 46 → 46, zero added, zero removed.**
> *(Corrected in FBV2-S1-005: the "68" quoted here and in FBV2-S1-004 / 004B was a
> transcription error. The stored reports say 46. The deltas were always right.)*
>
> **The 5 V fallback is preserved and was NOT tuned for.** The first-build network is a
> 3.3 V design. Moving to ~5 V later needs a firmware supply-configuration change (clear
> `sup3V`), **revalidation of matching, damping and the RFI divider** — the driver amplitude
> rises ~1.5×, so `RFI` would sit near 1.5 V pk-pk, still inside the rail but it must be
> re-checked rather than assumed — and possibly a passive retune. **It needs no PCB respin,
> no antenna replacement and no ST25R3916 replacement.**
>
> **B-48 is closed on substance, not on process.** ST's design rules were obtained and
> applied and the target is now derived rather than assumed, but **the AN5276 Rev 6 PDF
> still would not load in this environment** — st.com and the Mouser mirrors timed out and a
> direct download returned bot-protection HTML. **The `STSW-ST25R004` run against a
> *measured* antenna impedance has not been performed and is carried as B-57.**
>
> **First-article tuning is REQUIRED before any value may be called final**, and it must be
> done with the **rear shell fitted, the antenna adhered in its final position, the PCB
> installed, the battery installed and the ferrite in its final orientation** — every
> conductor and dielectric within a few centimetres is part of an inductive near-field
> antenna, so bench tuning on a bare board proves nothing about the product.
>
> **No new CTO decision is requested.** The one candidate considered — an E48 280 pF `C_s`
> to land exactly on 36 Ω instead of 68 Ω — was rejected for the first build because it
> commits to a target impedance nobody has measured yet. It is a first-article component
> choice.

## 8t. I²C devices and IMU — FBV2-S1-005 (2026-08-23)

| # | decision | date |
|---|---|---|
| D-136 | **BMI270 RE-DERIVED FROM `BST-BMI270-DS000-08` REV 1.6, NOT INHERITED FROM BETA-DM.** Every strap was checked line by line against the datasheet: `SDO`→GND = **0x68**; `CSB`→VDDIO because Bosch says *"For using I2C, it is recommended to hard-wire the CSB line to VDDIO"*; `ASDx`/`ASCx`→VDDIO with the unused secondary interface, where Bosch explicitly writes ***"Do not connect to GND"***; `INT2`/`OCSB`/`OSDO` left **DNC**, which is Bosch's own instruction for unused pins; `C6`/`C7` 100 nF at pins 5 and 8 exactly as recommended. **The honest outcome of not copying Beta-DM is that Beta-DM was already right — nothing on the sheet was wrong.** `VDD` 1.71–3.6 V, `VDDIO` 1.2–3.6 V, **no sequencing and no slew-rate constraint**, `tPO` 2 ms, FIFO 2048 B, 8 kB config upload required after every POR. **MPN `BMI270` is a flat orderable part, not a configured ordering scheme, so D-096 does not bite**; Bosch order code 0 273 017 008. **`B-44` CLOSED**: pad drive is **`IOH`/`IOL` ≤ 2 mA, `VOH` ≥ 0.8·VDDIO**. **The BMI270 has NO tap or double-tap feature in any configuration** — the word does not appear in the datasheet. Wake-on-motion, significant motion, no-motion, orientation, step counting and raise-to-wake (*"wrist wear wakeup"*) all exist; tap does not, and no hardware is proposed to compensate. | 2026-08-23 |
| D-137 | **THE MOTION INTERRUPT STAYS ON NATIVE `GPIO3`, AND THE PULL DIRECTION DICTATES THE FIRMWARE CONFIGURATION.** Boot safety is now a **timing proof, not a margin argument**: `INT1_IO_CTRL` resets to `0x00` so the output driver is **disabled** at POR; firmware cannot enable it before the 8 kB config upload; and the ESP32-S3 strap hold time is **`tH` = 3 ms minimum** with `GPIO3` defaulting to **"Floating"** (no internal pull), so `R110` alone defines the strap. **The IMU physically cannot reach the strapping window.** Consequently: **`INT1_IO_CTRL.od` = 0 (push-pull) and `.lvl` = 1 (active high) are MANDATORY. Open-drain is FORBIDDEN on this net** — an open-drain output into a pull-down never produces an edge, and the interrupt would be silently dead. `GPIO3` = `RTC_GPIO3`, so **EXT0/EXT1 deep-sleep wake works**, and active-high into a pull-down is exactly the polarity that wants. **Moving the interrupt behind a PCAL9535A is REJECTED**: it would put motion wake behind an I²C transaction that cannot wake the SoC from deep sleep, `U2` is 16/16, and the boot-safety reason that might have justified it does not exist. | 2026-08-23 |
| D-138 | **`INT2` REMAINS DNC. `RESERVED_SPARE` IS NOT CONSUMED.** Bosch instructs DNC for unused interrupt pins; *"if just one interrupt pin is used all interrupts may be mapped to this interrupt pin"*, with the source read from `INT_STATUS_0`/`INT_STATUS_1` in one extra transaction the host is making anyway; and using two pins in latched mode would import a mapping partition the design does not otherwise have. A test point on `INT2` was considered and rejected — it puts a stub on a pin the manufacturer says to leave open, for a bench-only benefit. **Pad 9 exists on the land pattern, so a future second interrupt is a wire, which is what D-049 asks for.** | 2026-08-23 |
| D-139 | **INTERNAL I²C PULL-UPS `R19`/`R20`: 4.7 kΩ → 2.2 kΩ.** The real bus was measured from the netlist — two expanders, the BMI270, the MAX17048, the TCA9517A A-side, the touch controller through the 50-pin display flex, two test points and ~120 mm of trace — giving a **worst case of ≈ 85 pF**. `t_r = 0.8473·R·C` then gives **338 ns at 4.7 kΩ, which FAILS the 300 ns fast-mode limit**, while a typical 60 pF gives 239 ns and passes. **That is the worst kind of defect: it works on the bench and fails on the unit with the longest flex.** 2.2 kΩ gives **158 ns, 47 % margin**. Sink current was checked before the change, as required: **1.32 mA at `VOL` 0.4 V**, against BMI270 2 mA, TCA9535 SDA 6 mA, the I²C-specification minimum of 3 mA, and an absolute floor of 967 Ω. **There is exactly one pull-up pair on the internal net** — `R49`/`R50` are DNP and belong to the switched accessory segment on the far side of `U16`. Bring-up remains 100 kHz then 400 kHz. | 2026-08-23 |
| D-140 | **THE BMI270 ADDRESS BECOMES STRAPPABLE: `R118` 0 Ω FITTED to GND (0x68), `R119` 0 Ω DNP to `+3V3` (0x69). FIT ONE ONLY — fitting both shorts `+3V3` to GND.** `SDO` was hard-wired to GND, so under D-049 the only escape from an address collision was cutting a trace at a 0.25 mm pad. **`0x68` is the single most collision-prone address on a community I²C bus**: MPU6050, MPU9250, ICM-20948 and the DS3231/DS1307 RTCs all default to it, and those are exactly the parts a hobbyist accessory is built from. Reserving an address in a document does not stop a $2 module from arriving at it. **Two 0603 pads, one populated, convert a respin into a rework.** This is a hardware addition and is reported as one; it sits inside the brief's instruction to keep address/strap resistor footprints accessible. | 2026-08-23 |
| D-141 | **THE IMU IS PERMANENTLY POWERED FROM `+3V3`. NO LOAD SWITCH.** Accel-only low-power mode draws **down to 4 µA** plus **≈ 3 µA** for advanced features (10 µA spec'd at 25 Hz); a load switch would save **≈ 9 µA** while **destroying wake-on-motion**, forcing an 8 kB config upload on every resume, and costing a load switch plus one of the design's last expander pins. Nine microamps is below the SoC's own deep-sleep floor and unmeasurable against self-discharge. **Trading away the reason the IMU is on the board would be a bad deal at any price.** | 2026-08-23 |
| D-142 | **`architecture/I2C_ADDRESS_REGISTRY.md` IS CREATED AND IS NORMATIVE.** It carries the full internal map (0x20, 0x21, 0x36, 0x38, 0x68, with 0x69 held in reserve), the external reservations including **`0x50`, which must never become an internal address**, the collision audit (**no collision; nothing in the I²C reserved ranges**), and the rules for accessory authors. **It also records which addresses are datasheet-cited and which are carried**: 0x20/0x21 and 0x68/0x69 were confirmed from manufacturer datasheets in this task, while **0x36 and 0x38 could not be** — every Analog Devices and FocalTech fetch failed here — and are carried under **B-60**, to be closed by a first-article bus scan rather than by editing a document. | 2026-08-23 |
| D-143 | **THE BMI270 LAND PATTERN IS VERIFIED AND THE "DO NOT ROUTE" GATE ON THIS PART IS DISCHARGED.** §8.3 of the datasheet is a raster drawing with no dimensions in the text layer, so it was rendered at 12× and the pads measured programmatically, calibrated on the printed 0.5 mm pitch. **Every printed dimension reproduces** — 0.5, 0.25, 0.475, 0.675, 0.925, 3.0 and 2.5 — as do the pad sizes (0.475 × 0.25 side, 0.25 × 0.475 end), the column at ±1.1625, the rows at ±0.9125 and, critically, **the peripheral pin order 1–4 left / 5–7 bottom / 8–11 right / 12–14 top**, which is the error that would have been fatal and silent. Paste-aperture and courtyard policy remain part of the FBV2-S2 footprint audit — a house-rules question, not a Bosch-conformance one. | 2026-08-23 |

> **Result (FBV2-S1-005).** Full analysis:
> [`audits/2026-08-23-s1-i2c-imu-implementation.md`](audits/2026-08-23-s1-i2c-imu-implementation.md).
> Registry: [`architecture/I2C_ADDRESS_REGISTRY.md`](architecture/I2C_ADDRESS_REGISTRY.md).
>
> **Task gate FBV2-S1-I2C-IMU = PASS. ERC 46 → 45: zero added, one removed** (the `SDO`
> power-output/bidirectional `pin_to_pin` warning, retired by `R118`). **Errors unchanged at 2,
> both inherited.** 303 components, 0 duplicate references, 0 without a footprint.
> `fork_equivalence.py` PASS, `netclass_probe.py` PASS, PCB still bit-identical to Beta-DM.
>
> **P-18 is UNCHANGED but is now precisely characterised, and the characterisation moves the
> problem.** `U16` TCA9517A, `R49`/`R50`, `U15` and `D2`/`D3` are **all DNP** — there is no
> fitted external I²C path at all today, so whatever is chosen at Sheet 09 migration costs no
> rework. TI's own text settles the powered-off case: *"The TCA9517A logic and all I/Os are
> powered by the `VCCB` pin"*, and `VCCB` is `ACC_3V3_SW`, so with the accessory rail off the
> buffer is **completely unpowered and high-Z on both sides** — a harder disconnect than a mux,
> which stays powered. **The real weakness is not the buffer, it is the location of its disable
> control**: `ACC_PWR_EN` is `U3` P17, an expander output sitting behind the very bus that a
> broken accessory would hold low. A 9-clock bus-recovery pulse train frees the common case for
> free; a hard short escapes only through a `+3V3` power cycle, because an MCU reset does not
> reset the expanders.
>
> ### ~~O-4~~ — **APPROVED AND CLOSED 2026-08-23 by D-176 (FBV2-S1-009): `U16` is now TI `TCA4307DGKR`, LCSC C880333, FITTED.** Original text retained:
>
> **O-4 — NEW, REQUIRES A CTO DECISION.** Evaluate replacing `U16` with a **TCA4307-class
> hot-swap I²C buffer with stuck-bus recovery**, *at Sheet 09 migration*. **For:** the community
> header is a hot-plug connector by definition, and this is the only option that both
> **pre-charges on insertion** and **recovers a stuck bus without the host** — exactly the
> failure the TCA9517A cannot escape. No rework cost, no net BOM. The TCA9517A's one unique
> capability, level translation, is unused: sheet `09` already declares *"COMMUNITY HEADER LOGIC
> = 3.3 V ONLY"* and `VCCB` is 3.3 V. **Against:** it is **not pin-compatible**, so the `U16`
> area must be re-routed, and the MPN must come from a **live listing** before any lock (D-096)
> — the datasheet was obtained, the availability was not. **Nothing is implemented; `U16`
> remains TCA9517A.** If O-4 is declined, the fallback is firmware-only and is adequate for
> Beta v2.
>
> **No buffer of any kind solves address collision.** A repeater, a hot-swap buffer and a mux
> all pass addresses through unchanged. Collision is a protocol problem, closed by D-142 and the
> `0x50` ID EEPROM — not by silicon.
>
> **One inherited discrepancy is recorded and deliberately not touched:** `U2`/`U3` still carry
> the schematic value **`TCA9535PWR`** while **D-061 locked NXP `PCAL9535APW,118`**. The address
> base is identical (`0100 A2A1A0`), so nothing here depends on it, and both parts live on
> **sheet 08**, which is not authorised in this task. It belongs to the Sheet 08 migration and is
> flagged now so it is not discovered at BOM time.

## 8u. Audio — microphone and speaker — FBV2-S1-006 (2026-08-23)

| # | decision | date |
|---|---|---|
| D-144 | **`U5` (MAX98357A) AND `J6` (SPEAKER CONNECTOR) ARRIVED FROM BETA-DM MARKED `DNP`. BOTH ARE NOW FITTED.** Nobody wrote that down — it is in the inherited file, and it means **the entire speaker output path has never been populated on any AQROOT board**, while `C9` and `C10` *were* fitted, decoupling an amplifier that was not there. The brief requires voice output and Full Beta v2 is the feature-complete design, so both become `dnp no`. **This is the third load-bearing inherited `DNP` in two tasks** (`U16`, `R49`/`R50`, `U15`, `D2`/`D3` on sheet 09 at FBV2-S1-005). **A `DNP` on a Beta-DM sheet is a statement about the reduced build, not about the architecture, and every migrated sheet must re-decide it rather than inherit it.** | 2026-08-23 |
| D-145 | **MICROPHONE LOCKED: PUI Audio `DMM-4026-B-I2S-R`, replacing the obsolete ICS-43434. IT IS NOT A DROP-IN.** The PUI part has **SEVEN pads, not six**, a 4.00 × 3.00 × 1.00 mm body and a different land pattern, so **both the symbol and the footprint are new**, built from the manufacturer drawing (Rev A, 5/26/2021) — the brief's instruction not to reuse the ICS-43434 footprint was right for a stronger reason than size. Every pin re-derived: `LR`→GND selects the **left** I²S slot; **`CONFIG`→GND is MANDATORY and has no ICS-43434 equivalent** (*Pull to ground. The state of this pin is used at power-up*); `VDD` **1.62–3.63 V** with `C8` 100 nF; `WS`/`SCK`/`SD` unchanged. **`R120` 100 kΩ pull-down on `I2S_MIC_DIN` is a DATA-SHEET REQUIREMENT, not a preference** — `SD` tri-states for the entire unused half of every frame and the inherited sheet had no pull-down at all. **NO 1.8 V RAIL IS NEEDED, and that was the single largest risk in the substitution**: the part is *rated* 1.8 V and the vendor catalogue line reads *MICROPHONE -26DB 1.8VDC*, but its operating range is 1.5–3.6 V (pin table 1.62–3.63 V), so `+3V3` and the existing decoupling are the whole supply design. 820–1000 µA normal, **5 µA sleep**, 20 ms startup, −26 dBFS, 64 dB(A) SNR, bottom port. | 2026-08-23 |
| D-146 | **THE I²S BUS RATE IS SET BY THE MICROPHONE, AND THE BRIEF'S SUGGESTED RATE CANNOT BE RUN.** The DMM-4026 needs **BCLK between 2.048 and 4.096 MHz** in normal mode and drops to sleep below 320 kHz. A 16 kHz frame gives 0.512 MHz (mono) or **1.024 MHz** (64-BCLK) — **both outside normal mode**. 32 kHz × 64 = 2.048 MHz sits exactly on the limit. **RULING: run the shared bus at 48 kHz × 64 BCLK = 3.072 MHz — the microphone's own typical and the MAX98357A's electrical-characteristics test condition — and DECIMATE TO 16 kHz IN FIRMWARE.** 16 kHz remains the right *application* rate; it is not a legal *wire* rate for this part. On the bench this would have looked like *the microphone sometimes returns silence*, which is what sleep mode looks like. **The existing I²S architecture is otherwise valid unchanged**: `BCLK` and `LRCLK` shared, `MIC_DIN` and `SPK_DOUT` separate, one ESP32-S3 controller in master full duplex, **no pin, net or GPIO change**. | 2026-08-23 |
| D-147 | **MAX98357A RETAINED — analog.com lists it `PRODUCTION` with a live 1ku price, so there is no sourcing reason to move. MPN LOCKED: `MAX98357AETE+T`** (16-pin TQFN, −40 to +85 °C, tape and reel), matching the footprint already in use; `U5` previously carried no MPN at all. **`GAIN_SLOT` CHANGED FROM GND (12 dB) TO VDD (6 dB).** Gain is referenced to a 2.1 dBV full-scale DAC output, so at 12 dB a 0 dBFS sample asks for **5.07 Vrms** while the 3.3 V rail can only deliver **2.33 Vrms** — **the top 6.8 dB of the digital range was unusable, clipped by the supply**. At 6 dB, 0 dBFS lands on the rail: the whole range is usable and the output noise floor is lower. **Maximum acoustic output is identical either way because it is rail-limited, not gain-limited.** One net, no BOM impact. **`SD_MODE` needs no series resistor**: the data sheet requires ~2 kΩ only when `VDD < VDDIO`, and here both are the same `+3V3` net, so the condition cannot arise — recorded because it is exactly the part that gets added *just in case*. `R15` 100 kΩ to GND holds shutdown through reset and boot. **FIRMWARE SAFETY RULE: never remove LRCLK while BCLK is present** — the data sheet warns of *a large DC output voltage*, which into an 8 Ω voice coil is a burnt speaker. | 2026-08-23 |
| D-148 | **SPEAKER LOCKED: PUI Audio `AS02008MR-LW152-R`.** Verified verbatim from the PUI drawing: **Ø20 ± 0.2 mm × 3 ± 0.2 mm**, **8 Ω ± 15 %**, **0.5 W rated / 0.8 W maximum**, 86 ± 3 dBA at 0.1 W / 0.1 m, 5 % max distortion, resonance 500 Hz ± 20 %, **response 500–4000 Hz**, metal housing, Mylar cone, **Nd-Fe-B magnet**, 2.4 g, −20 to +55 °C, RoHS, **152 ± 10 mm UL1571 AWG #32 leads, RED positive / BLACK negative**. **The 500–4000 Hz response is the reason to choose it, not a limitation**: the brief asked for intelligible speech and explicitly not music, and a driver that puts all of its 0.5 W into the speech band is louder where it matters than a wider-range driver of the same size. **`J6` is RETAINED** — JST `B2B-PH-K-S` is already the small common connector the brief allows; mating side **`PHR-2` + `SPH-002T-P0.5S`**, and JST's applicable wire range is **AWG #32 to #24**, so **the speaker crimps straight in and is replaceable without soldering**, the same serviceability principle as the NFC antenna (D-128). AWG #32 is the small end of that range and is carried as **B-62** for a first-article pull test rather than asserted. | 2026-08-23 |
| D-149 | **OUTPUT POWER AND THE VOLUME CEILING.** At 3.3 V into 8 Ω the rail limit is 2.33 Vrms → **0.68 W peak**, cross-checked against the data sheet's 0.93 W at 3.7 V scaled by (3.3/3.7)² = 0.74 W. At 90 % efficiency that is **≈ 230 mA from `+3V3`** at full output, plus 2.4 mA quiescent; **340 µA** in standby with BCLK stopped and **0.6 µA** in shutdown. **RECOMMENDED DEFAULT MAXIMUM SOFTWARE VOLUME: −6 dBFS → 0.17 W, ≈ 57 mA, roughly 89 dB SPL at 0.1 m**, comfortably inside the speaker's 0.5 W rating; absolute ceiling −3 dBFS for alerts. **0 dBFS must not be used continuously** — it exceeds the rated power even though it stays under the 0.8 W maximum. **No new mutual-exclusion rule is proposed**: MX-1 already covers concurrent high-power operations, and voice does not need maximum output during radio TX — at −6 dBFS it draws 57 mA. Thermally irrelevant: ~75 mW dissipated against a 1666 mW package rating. | 2026-08-23 |
| D-150 | **EMI: NOTHING FITTED, EVERYTHING RECOVERABLE.** The decisive evidence is the MAX98357A data sheet's own **Figure 14, *EMI with 12 in of Speaker Cable and No Output Filtering*** — AQROOT's lead is 152 mm, **half** that length, and the part uses edge-rate control plus spread-spectrum modulation around 330 kHz. **First build: `R121`/`R122` FITTED as 0 Ω so the speaker path is a plain wire; `C81`/`C82` 1 nF DNP.** If emissions ever need taming — AQROOT does carry 433 MHz, 915 MHz, NFC and a sensitive microphone — the recovery is a ferrite bead (600 Ω at 100 MHz class) in place of the 0 Ω plus the shunt capacitors: **four 0603 positions, one pair populated, no respin**. A 0603 0 Ω adds ~50 mΩ, i.e. 15 mV at 300 mA against 8 Ω — electrically invisible and symmetric. **PCB requirement: `SPK_P`/`SPK_N` must be routed as a tight, equal-length differential pair from `U5` to `J6` whatever is fitted** — the most effective EMI control on a filterless Class D output, and it costs nothing. | 2026-08-23 |
| D-151 | **MICROPHONE ACOUSTIC INTERFACE, MEASURED FROM THE MANUFACTURER DRAWING.** §8.3 is a raster drawing, so it was rendered and the pads measured programmatically; the geometry closes against the printed dimensions to **0.01 mm**. Pads **0.60 × 0.40 mm**, columns **±1.075 mm**, rows **0.65 mm** pitch, **pad 4 is a GND ring, ID 1.05 / OD 1.65 mm**, the port sits on the package width centreline **1.28 mm** from the nearest pad row and **1.00 mm** from the short edge, and the port in the can is **Ø0.25 ± 0.05 mm**. **It is a BOTTOM-PORT part: sound enters through a hole in the PCB, so the microphone is soldered to the face OPPOSITE the shell aperture.** PCB acoustic hole **Ø1.05 mm NPTH concentric with pad 4** (was *Ø0.8–1.0 mm* — now the manufacturer's number); no copper, mask or component inside **Ø1.65 mm**, Ø2.5 mm component keepout on the microphone side; gasket **ID ≥ 1.5 mm, OD 4–5 mm** compressed 20–30 %; tunnel **≤ 2.5 mm**; front face, bottom third; **≥ 60 mm from the speaker on opposite faces**, and **the Nd-Fe-B speaker magnet must also stay clear of the NFC zone**. `SPEAKER_ENVELOPE` tightens from *Ø20 × 4.0 mm or 15 × 11 × 3.5 mm* to the fitted **Ø20 × 3.0 mm**, releasing 1 mm of Z. | 2026-08-23 |
| D-152 | **NO HARDWARE ECHO CANCELLATION, AND ONE FREE LEVER ALREADY EXISTS.** `SD_MODE` is a **hardware mute**: driving it low puts the amplifier in shutdown with the outputs high-Z at 0.6 µA, which removes not just the audio but the amplifier's own noise floor and switching residue from the microphone's environment — strictly better than a digital mute, and free because the net already exists. **Firmware recommendations (not implemented): first firmware should be HALF-DUPLEX**, muting via `SD_MODE` while actively listening; ramp the digital data down before asserting shutdown, since the data sheet notes there is no volume ramp-down on entering shutdown; software AEC later if barge-in is wanted. Mechanical separation and a sealed microphone tunnel do the rest. | 2026-08-23 |

> **Result (FBV2-S1-006).** Full analysis:
> [`audits/2026-08-23-s1-audio-implementation.md`](audits/2026-08-23-s1-audio-implementation.md).
>
> **Task gate FBV2-S1-AUDIO = PASS. ERC 45 → 45: zero added, zero removed.** Errors unchanged
> at 2, both inherited. 308 components, 0 duplicate references, 0 without a footprint,
> 0 `*_TBD` nets. `fork_equivalence.py` PASS, `netclass_probe.py` PASS, PCB still bit-identical
> to Beta-DM.
>
> **NO NEW CTO DECISION IS REQUESTED.** Every change sits inside the brief's own instructions:
> item 2 (replace the microphone), item 5 (*verify … gain/mode strap*), item 8 (EMI recovery
> footprints) and item 1 (voice output remains required, which is what fitting `U5`/`J6`
> delivers). The things that would have been new features — a codec, a DAC, an analog chain, a
> 1.8 V rail, an acoustic wake detector, a buzzer, a headphone jack — are exactly what the
> brief forbids, and none was added.
>
> **BOM consolidation, free:** the microphone and the speaker are now both **PUI Audio** — one
> vendor, one set of distributors, one datasheet source.
>
> **B-61, B-62, B-63 and B-64 opened.** The microphone is **confirmed in live distributor
> stock** (DigiKey 2 807, Arrow 10 000, three others at 1 250). **The speaker is not**: PUI's
> product page would not render here after three attempts and Digi-Key search is bot-protected.
> Its datasheet is served live from PUI's API today, but **D-096 asks for a live listing and
> that is not one**, so it is carried as B-61 rather than called confirmed.
>
> **One probe was extended rather than silenced.** `fork_equivalence.py` asserted the `.pretty`
> directory was bit-identical to Beta-DM's, which stopped being true the moment a migrated
> sheet locked a new part. It now asserts that **every inherited footprint is still
> bit-identical and none was deleted**, and that **every addition is declared** in an
> `ADDED_FOOTPRINTS` table naming the task that added it. An undeclared footprint is still a
> failure — the check got stricter about what it actually cares about, not looser.

## 8v. Infrared — FBV2-S1-007 (2026-08-23)

| # | decision | date |
|---|---|---|
| D-153 | **THE WHOLE IR SUBSYSTEM ARRIVED FROM BETA-DM MARKED `DNP` AND IS NOW FITTED.** `U6`, `D1`, `Q1`, `R21`, `R22`, `R23`, `R24` and `C11` were all `DNP`; only `C12` was fitted — decoupling for a transmitter that was not there, the same pattern as `C9`/`C10` on sheet 06. The brief opens with *IR is a mandatory internal feature*, so all eight are fitted. **THIS IS THE FOURTH CONSECUTIVE MIGRATED SHEET WHERE AN INHERITED `DNP` WAS LOAD-BEARING** (sheet 09's `U16`/`R49`/`R50`/`U15`/`D2`/`D3`, sheet 06's `U5`/`J6`, now all of sheet 07). **It is now a rule rather than a coincidence: a `DNP` on a Beta-DM sheet describes what was populated on that reduced build, not what the architecture requires. Sheets 08 and 09 must be assumed to carry the same trap.** | 2026-08-23 |
| D-154 | **IR EMITTER LOCKED: Vishay `TSAL6100`** (doc 81009 Rev 1.8), replacing the inherited TSAL6200. 940 nm GaAlAs MQW, T-1¾ Ø5 mm leaded, **`Ie` 170 mW/sr typ at 100 mA**, **half-intensity angle ±10°**, `Φe` 40 mW, `VF` 1.35/1.6 V at 100 mA, `tr`/`tf` 15 ns. **THE TSAL6200 FALLBACK IS A PROVEN DROP-IN, NOT AN ASSUMPTION**: identical T-1¾ package and footprint, **identical `VF` 1.35/1.6 at 100 mA and identical `IFM` 200 mA**, so **`R24` does not change** — only `Ie` (170 → 72 mW/sr) and beam (±10° → ±17°) differ, and the two emit similar total power redistributed (`Ie` × φ² ≈ 17 000 vs 20 800). **The real risk in the TSAL6100 is the beam, not the power**: ±10° is narrow for a handheld pointing device, and that is exactly what the authorised fallback exists for (**B-66**, first article). | 2026-08-23 |
| D-155 | **IR PEAK CURRENT = 150 mA, AND THE RATING THAT BINDS IS `IFM`, NOT `IFSM`.** **`IFSM` = 1.5 A is a SINGLE-PULSE surge for t ≤ 5 µs and cannot justify carrier current.** The governing rating for a 38 kHz burst train is **`IFM` = 200 mA at tp/T = 0.5, tp = 100 µs** — a *longer* pulse at the same duty than a 38 kHz carrier produces, so the carrier is less stressful than the specified condition. Candidates evaluated over a standard NEC frame (≈11 % LED-on): **100 mA** = 50 % of `IFM`, 15 mW, ΔTj 3.4 K; **150 mA = 75 % of `IFM`, 25 mW, ΔTj 5.7 K — SELECTED**; **200 mA** = 100 % of `IFM`, which leaves nothing for rail, `VF` and resistor tolerance and would push the worst case past the rating; **300 mA = 150 % of `IFM` — REJECTED as out of spec** however comfortable the thermals look. **Thermally none of them is difficult** (160 mW `PV` limit, 230 K/W); the constraint is the repetitive rating and it is hard. **Range is not the constraint either** — the TSOP384xx datasheet quotes **45 m using a TSAL6200 at only 50 mA**, and the TSAL6100 at 150 mA is roughly 20× that intensity, so current buys off-axis margin rather than headline range. | 2026-08-23 |
| D-156 | **IR LED SUPPLY = `+3V3`, REVERSING THE PREVIOUS PREFERENCE FOR `SYS`.** On the regulated rail a 12 Ω resistor gives **118–170 mA across every tolerance, a 1.44 : 1 spread**. On `SYS` (≈3.2–5.0 V) a resistor sized to keep the top inside `IFM` gives **64–166 mA, a 2.6 : 1 spread — IR range would visibly shorten as the battery drains**, and the worst case sits near the rating. `+3V3` also halves the resistor dissipation. **The noise objection that motivated `SYS` is real but bounded and is answered by two facts**: `C12` holds the 38 kHz ripple to ≈ 40 mV (1.2 % of rail), and **the only device in the system whose sensitivity is specified against supply ripple at the carrier frequency — the IR receiver — already sits behind 41 dB** (D-160). Everything else on `+3V3` already lives with the audio amplifier's 230 mA peaks. **Scope, stated as fact and not as the reason:** `BQ25185_SYS` is a sheet-01-local net, so routing it here needs a sheet-01 edit this task cannot make — **had `SYS` won the analysis it would have been reported as blocked rather than quietly avoided.** The `ARCHITECTURE.md` source-select link is carried as **B-65**. | 2026-08-23 |
| D-157 | **CURRENT-LIMIT NETWORK: `R24` 18 Ω → 12 Ω 1 % 0805, plus `R123` DNP 0805 parallel trim.** `I = (3.3 − 1.50 − 0.005) / 12 = 150 mA`, with `VF` interpolated to 1.50 V at 150 mA between the datasheet's 1.35 V at 100 mA and 2.2 V at 1 A, and the AO3400A contributing ≈ 5 mV. Worst case **170 mA (85 % of `IFM`)** and **118 mA**. Dissipation 0.27 W instantaneous, ≈ 30 mW over a frame against a 125 mW 0805. **`R123` trim table, every entry inside `IFM`:** 12 Ω alone 150 mA, ‖220 Ω 158 mA, ‖100 Ω 168 mA, ‖68 Ω 176 mA, ‖47 Ω 188 mA. **NEVER BELOW 10 Ω TOTAL.** It is the first thing to reach for if the TSAL6200 fallback is fitted. Trimming *down* needs no provision — `R24` is an accessible 0805 and can be swapped. | 2026-08-23 |
| D-158 | **LOCAL RESERVOIR `C12`: 4.7 µF → 22 µF, 0805 → 1210, X7R 16 V.** Per carrier period the capacitor must supply `Q = I·D·(1−D)·T = 0.88 µC`, so ripple = 0.88 µC / C: **4.7 µF gives 218 mV (6.6 % of rail — three times too small)**, 10 µF 88 mV, **22 µF 40 mV (1.2 %)**, 47 µF 19 mV. Target is ≤ ~1.5 % of rail. **The package and voltage are specified deliberately: the requirement is ≥ 15 µF EFFECTIVE at 3.3 V DC bias**, and a 6.3 V 0805 part would derate to roughly half its marked value. The burst envelope — a 50 mA step on a millisecond timescale — is the regulator's job, not this capacitor's. | 2026-08-23 |
| D-159 | **DRIVER `Q1` AO3400A RETAINED, AND ITS OPEN PINOUT ITEM IS CLOSED.** AOS doc Rev 3.1, July 2023: the SOT-23 top and bottom views show the lone pin as **Drain** and the paired pins as **Gate** then **Source**, i.e. **1 = G, 2 = S, 3 = D** — exactly what `Transistor_FET:Q_NMOS_GSD` maps and what the inherited wiring used. `VGS(th)` 0.65/1.05/**1.45 V** so it is fully enhanced by a 3.3 V gate; `RDS(on)` < 48 mΩ at 2.5 V gives ≈ 5 mV at 150 mA; `ID` 5.7 A / `IDM` 30 A make it ~38× over-specified, and it is kept because **it is already in the design on sheet 01**. Switching at 38 kHz is a non-event: with `R22` 100 Ω the edge is under 100 ns, about 0.3 % of the carrier period, so `R22` buys gate damping and lower radiated EMI at no cost. **SAFE-OFF IS PROVEN, NOT ASSUMED: `R23` 100 kΩ with `IGSS` ≤ 100 nA holds the gate at ≤ 10 mV against a 650 mV minimum threshold — 65× margin, so there is no IR emission at boot, reset, GPIO high-impedance or a firmware crash.** **Footprint de-blocked: AOS publishes NO recommended land pattern**, so the old *needs the official AOS pattern* note asked for a document that does not exist; the IPC SOT-23 pattern applies and it becomes an ordinary FBV2-S2 item. | 2026-08-23 |
| D-160 | **RECEIVER LOCKED `TSOP38438` per the CTO, AND THE EXISTING SUPPLY FILTER IS QUANTIFIED AND KEPT.** Vishay doc 82491 Rev 2.1, 27-May-2025: TSOP382.. and TSOP384.. share **the same Minicast package, the same pinning 1 = OUT / 2 = GND / 3 = VS and the same body**, so `TSOP38238 → TSOP38438` is a **pure MPN change with no footprint impact**. `VS` **2.0–5.5 V**, `ISD` 0.35 mA typ, **output active low with an internal 30 kΩ pull-up** so no external pull-up is needed and `OUT` drives GPIO44 directly, directivity ±45°. **`R21` 100 Ω + `C11` 4.7 µF RETAINED and now justified rather than inherited**: the topology matches Vishay's application circuit exactly, Vishay prints **no values**, and ours give `fc` = 339 Hz = **41 dB at 38 kHz**. **That matters more than it looks** — datasheet Fig. 7 shows the receiver degrades from roughly **10 mV RMS of supply ripple AT THE CARRIER FREQUENCY** and doubles its threshold by ≈ 50 mV, and our own transmitter runs at exactly that frequency. 40 mV pk-pk on the rail becomes **≈ 0.1 mV RMS at `VS`, about 90× margin**. **This is what makes D-156 safe. Do not shrink `C11` for area without redoing this calculation.** | 2026-08-23 |
| D-161 | **NO NEW MUTUAL-EXCLUSION RULE FOR IR.** The transmitter draws 150 mA nominal / 170 mA worst-case peak, 50 mA averaged over a burst and **≈ 17 mA averaged over a whole NEC command**; the receiver draws 0.35 mA continuously. The same rail already carries **230 mA audio peaks**, a 60 mA NFC field and ~100 mA of backlight boost, so **IR is the smallest pulsed load on `+3V3`**. MX-1 already covers concurrent high-power radio operation and IR does not need to join it. The brief says not to create rules the power budget does not need, and it does not need one. Thermally: 30 mW in `R24`, 0.8 mW in `Q1`, 25 mW in the LED. | 2026-08-23 |
| D-162 | **SELF-BLINDING IS SOLVED MECHANICALLY, AND THE NARROWER BEAM TIGHTENS THE REQUIREMENT RATHER THAN RELAXING IT.** The electrical half — the transmitter modulating the receiver's supply at its own carrier frequency — is already answered by the 41 dB filter (D-160). Mechanically: emitter and receiver both on the top edge, **≥ 15 mm apart**, receiver **outside the LED emission cone**, **opaque optical barrier between them**, and the TX current loop kept away from the receiver supply and return. **The ±15 mm figure was written against a ±17° TSAL6200; the TSAL6100 is 2.4× brighter on axis, so stray and internally-reflected energy reaching the receiver goes UP even though the direct cone is narrower.** Firmware may additionally gate RX during local TX; none is implemented here. **Test provisions added:** `TP39` on `IR_LED_A` (LED current from the drop across `R24`, the only non-invasive way to confirm the 38 kHz peak on a built board) and `TP40` on the receiver output. | 2026-08-23 |

> **Result (FBV2-S1-007).** Full analysis:
> [`audits/2026-08-23-s1-ir-implementation.md`](audits/2026-08-23-s1-ir-implementation.md).
>
> **Task gate FBV2-S1-IR = PASS. ERC 45 → 45: zero added, zero removed.** Errors unchanged at 2,
> both inherited. 311 components, 0 duplicate references, 0 without a footprint, 0 `*_TBD` nets.
> `fork_equivalence.py` PASS, `netclass_probe.py` PASS, PCB still bit-identical to Beta-DM.
>
> ### ~~O-5~~ — **CLOSED 2026-08-23 by D-163: the CTO ruled for AGC2 (`TSOP38238`), with `TSOP38438` retained as a documented drop-in fallback.** Original text retained:
>
> **The brief §1 locks `TSOP38438`. The brief §9 lists Sony/SIRC among the protocols the hardware
> should support. Vishay's own suitable-data-format table says those two cannot both be true.**
> Verbatim from doc 82491 Rev 2.1, the AGC4 column is marked **"No" for Sony code** where the
> AGC2 `TSOP38238` is marked **"Yes"**; AGC4 is marked *"Preferred"* for NEC, RC5/RC6, Thomson
> RCA, Sharp and Mitsubishi and additionally suppresses **high-modulation fluorescent
> interference (Fig. 15)** that AGC2 does not. Vishay's framing: *"the higher the AGC, the better
> noise is suppressed, but the lower the code compatibility."* The mechanism is Fig. 8 — above
> 35 cycles/burst AGC4 collapses to ~7 % maximum envelope duty cycle and demands a gap of
> **> 15 × burst length** against AGC2's **> 5 ×**, which SIRC's long header violates.
>
> **The lock is a defensible trade, not an error — but it is a trade the CTO should make
> knowingly.** Two facts make it much smaller than it first looks: **(1) it is RECEIVE-ONLY —
> transmitting Sony/SIRC is completely unaffected**, because the transmitter is only a carrier
> and a timing pattern from the MCU; only *learning* a Sony code from an original remote is at
> risk. **(2) Reverting is a `lib_id` change and nothing else** — same package, same pinout, same
> footprint, same supply filter — and **the `TSOP38238` symbol has been deliberately retained in
> the project library** so the swap costs one line. **Implemented as locked (`TSOP38438`) pending
> the ruling.**
>
> **B-65 and B-66 opened.** B-65: the `ARCHITECTURE.md` `+3V3`/`SYS` source-select link needs a
> sheet-01 edit to publish `BQ25185_SYS` — a provision, not a fix, since `+3V3` is the
> analysed-correct choice. B-66: the TSAL6100's ±10° beam ergonomics are unvalidated and are the
> one real risk in the emitter choice; the authorised TSAL6200 fallback is a drop-in.
>
> **Nothing else was added:** no second IR LED, no external IR accessory requirement, no multiple
> emitter angles, no extra optical channels, no second receiver, no exotic carrier frequency, no
> dedicated LED-driver IC, no RF-style test connectors, no analog optical detector, no new GPIO.

## 8w. Buttons, expanders and the front RGB status light — FBV2-S1-008 (2026-08-23)

> ### ⚠ THIS TASK WAS INTERRUPTED BY A SESSION LIMIT AND RESUMED.
> Nothing was restarted and nothing valid was discarded. The interrupted session had
> converted both expanders, deleted HOME, landed `TOUCH_INT_N`/`SX1262_DIO1`, selected and
> verified the RGB part, and had written an honest note into the schematic saying the pin
> budget did not close. **That diagnosis was correct and closing it is the substance of this
> section.** Full recovery record in
> [`audits/2026-08-23-s1-buttons-expanders-rgb-implementation.md`](audits/2026-08-23-s1-buttons-expanders-rgb-implementation.md).

| # | decision | date |
|---|---|---|
| D-163 | **O-5 IS CLOSED IN FAVOUR OF AGC2. `U6` = Vishay `TSOP38238`; `TSOP38438` (AGC4) is retained as a DOCUMENTED DROP-IN FALLBACK** and its symbol stays in the project library. Both MPNs sit in the same Vishay parts table (doc 82491 Rev 2.1) sharing the Minicast body, the pinning **1 = OUT / 2 = GND / 3 = VS**, the footprint and one electrical table, so this is a pure MPN change and **every FBV2-S1-007 calculation — `R21`/`C11`, the 339 Hz corner, the 41 dB at 38 kHz, the ~90× margin — is unaffected**. AGC2 is marked *Yes* for all six listed formats **including Sony**, where AGC4 is marked **No**; the mechanism is the gap requirement (AGC2 > 5 × burst and 10–70 cycles/burst, AGC4 > 15 × and only 10–35, which SIRC violates). **What is given up is the AGC4 Fig. 15 high-modulation fluorescent suppression** — a lighting-robustness margin, not a protocol. | 2026-08-23 |
| D-164 | **BOTH EXPANDERS ARE NXP `PCAL9535APW,118` AND THE CONVERSION IS BEHAVIOURAL, NOT COSMETIC.** Verified against the primary source — **PCAL9535A Rev. 2, 23 January 2015** — retrieved and read in this session. TSSOP-24 **SOT355-1**, V_DD 1.65–5.5 V, address `0100 A2 A1 A0`, **25 mA sink per pin for direct LED drive** (abs max 50 mA/I-O, I_SS 200 mA, P_tot 200 mW), I_IH/I_IL ≤ 1 µA, internal power-on reset and **no RESET pin**. Power-up register state, on which the entire safe-state argument rests: **Configuration 06h/07h = `FF`** (all pins high-Z inputs), **Output port 02h/03h = `FF`** (a pin drives HIGH the instant it becomes an output, so no glitch), **pull enable 46h/47h = `00`** (internal 100 kΩ OFF), **interrupt mask 4Ah/4Bh = `FF`** (**all interrupts masked — the opposite of the TCA9535; unchanged firmware sees no interrupts at all**), interrupt **status** 4Ch/4Dh, input latch 44h/45h, four output drive strengths 40h–43h. **`U2` = 0x20, `U3` = 0x21, unchanged and unconflicted.** **FIRMWARE ORDERING CONTRACT: write the Output port register BEFORE the Configuration register**, or the five active-low resets and `AMP_SD_MODE` glitch to their inactive state on the write that makes them outputs. | 2026-08-23 |
| D-165 | **`U23` — A THIRD `PCAL9535APW,118` AT `0x22` IS ADDED. THE TWO-EXPANDER ALLOCATION DOES NOT CLOSE.** Capacity is 32 pins; **committed demand is 35**, and every line of it is held by a prior lock or by this brief: 5 safe-state control outputs, 6 buttons, `TOUCH_INT_N`, `SX1262_DIO1`, `SD_CARD_DETECT_N` (D-117), `BQ25185_STAT1/2` (Ruling G), 10 XGPIO (D-082), 4 accessory control/status, `SX1262_RXEN`, the inherited `ACC_PWR_EN`, `RESERVED_SPARE` (D-094) and 3 RGB. **Every escape is closed:** there is **zero free native GPIO** (GPIO35/36/37 are the octal PSRAM — B-10), which also makes the brief's own **WS2812 escape impossible** because a smart LED needs RMT on a native pin; `RESERVED_SPARE` is mandated; the ten XGPIO are locked; a dedicated LED driver is a new part family for one indicator. **`U23` adds NO new MPN, NO new footprint, NO new firmware driver and NO new rail**, costs ≈ $0.55 plus one 0603, and **retires B-37** by leaving 12 spare I/O — the first slack the programme has had. **It carries the front RGB and the reserved spare ONLY**, so declining it costs the status light and nothing else. **It holds no interrupt source**, keeps the `FF` power-up mask and is never read in the interrupt path, so the third device costs **zero extra I²C traffic per event**. Bus loading: six devices, +6 pF max per line, ≈ 85 → 95 pF, rise time **158 → ~177 ns against the 300 ns fast-mode limit**. **Raised as O-6 for ratification.** | 2026-08-23 |
| D-166 | **CORE, COMMUNITY AND SAFETY FUNCTIONS ARE PLACED BEFORE THE RGB, BY CONSTRUCTION.** The RGB and the reserved spare go on the **added** device and the charger telemetry stays on `U2`, not the reverse. Deleting `U23`, `D13` and `R124`–`R126` removes the status light and **not one other function**. Had the RGB kept `U2` P05–P07 and the telemetry moved to `U23`, declining the new part would have cost charge state and card detect. **D-089 is AMENDED, not broken:** `TOUCH_INT_N` (FBV2-S1-003) and `SD_CARD_DETECT_N` (D-117) arrived after that lock and outrank telemetry, so **`MAX17048_ALRT_N` and `VBUS_PRESENT` remain test-point only** — with twelve `U23` pins free if that is ever revisited, making it a wire and a firmware change rather than a respin. | 2026-08-23 |
| D-167 | **FRONT RGB STATUS LIGHT LOCKED: `D13` = MEIHUA `MHPA3528RGBCT`, LCSC `C409779`.** Confirmed live against the distributor record per D-096: **in stock, 69 270 pcs**, $0.1697 @ 5 / $0.1035 @ 500. **Common anode**, SMD3528-4P / PLCC-4, body **3.50 × 2.80 × 1.85 mm**, top view, water-clear, **120°**. **PIN 1 = ANODE, 2 = BLUE K, 3 = GREEN K, 4 = RED K — NOT the `Device:LED_ARGB` order (2 = red, 4 = blue), which would swap red and blue**, so a dedicated symbol and a footprint built from the manufacturer drawing (Issue LPDS-0001719 Rev.2, 2018-09-25) are used. **Topology: one common-anode LED to `+3V3`, three resistors, three PCAL9535A sink outputs on `U23` P00/P01/P02 as `FRONT_RGB_R_N` / `_G_N` / `_B_N`. No transistors, no driver IC, no new rail.** **ESD WARNING: red is 2000 V HBM but GREEN AND BLUE ARE ONLY 150 V** — `D13` must be handled as ESD-sensitive in assembly. | 2026-08-23 |
| D-168 | **THE THREE RGB RESISTORS ARE CALCULATED SEPARATELY AND ARE DELIBERATELY UNEQUAL: `R124` = 1 kΩ (RED), `R125` = 680 Ω (GREEN), `R126` = 390 Ω (BLUE).** V_F is read off the **Fig. 4 low-current curves at the operating current** — the tabulated V_F is quoted at 20 mA and is useless at 1–2 mA — giving 1.75 / 2.55 / 2.60 V, with V_OL 0.02–0.10 V. Nominal **1.50 / 1.03 / 1.67 mA**, white **4.20 mA**; corners (3.234–3.366 V rail, V_F spread, V_OL spread) **1.18–1.70 / 0.57–1.32 / 0.86–2.17 mA**, white **2.60–5.18 mA**. Every channel is inside the 1–2 mA target and white is inside the 3–6 mA target. **Red gets the LEAST current because it is the most efficient die** (1070 mcd typ at 20 mA against 1685 green and 500 blue), giving roughly **80 / 87 / 42 mcd**. Worst pin is **2.17 mA against a 25 mA sink rating — 11× margin**; the package sees 5.2 mA against 200 mA — **38×** — and ~0.35 mW against 200 mW. | 2026-08-23 |
| D-169 | **THE RGB IS DARK BY CONSTRUCTION AND NEEDS NO EXTERNAL PULL-UPS.** At power-up Configuration 06h = `FF` makes P00–P02 **high-impedance inputs**, so the cathode path is open and the only current is the **1 µA I_IH/I_IL leakage limit ≈ 0.05 mcd, which is invisible**; pull enable 46h = `00`, so the on-die 100 kΩ cannot light it either; and Output port 02h = `FF`, so the pin **drives HIGH the instant it becomes an output** — the anode potential — hence **no glitch on the input-to-output transition**. **Three external pull-ups would be three parts that do nothing and none is fitted.** Colours: red, green, blue, cyan, magenta, yellow, white, off. **Blink is firmware-timed over I²C; no smooth-animation hardware is required or provided.** | 2026-08-23 |
| D-170 | **BOTH CHARGER STATUS PINS ARE LANDED, WITH 10 kΩ PULL-UPS — a deliberate departure from Ruling G's 20 kΩ.** `BQ25185_STAT1` → `U2` P05 (`R127`), `BQ25185_STAT2` → `U2` P06 (`R128`). SLUSF65A Table 5-1 permits **1 kΩ–20 kΩ** with a 5 V maximum pull-up rail, so both values are legal; 10 kΩ is chosen for the same reason the button pull-ups are 10 kΩ — a stiffer high against 1 µA of expander leakage and PCB contamination, a value already dominant on the sheet, and the 0.33 mA flows only while the charger actually holds the pin LOW. **Decode (Table 7-2): STAT1 LOW = charging; STAT1 HIGH + STAT2 LOW = fault; both HIGH is ONE combined state covering charge-complete, sleep and charge-disabled — so STAT1 alone conveys only fault/no-fault.** **`STAT2` toggles forever when no battery is fitted (§7.3.10), so its interrupt mask bit stays SET — the PCAL9535A hardware default — and firmware polls it.** That capability is exactly what the TCA9535 lacked and is why D-061 is load-bearing. **No separate charging LEDs; the front RGB may show charge state in firmware.** | 2026-08-23 |
| D-171 | **INTERRUPT ARCHITECTURE: ONE WIRE-OR, THREE DEVICES, ONE NATIVE PIN.** All three `/INT` pins are open-drain onto `WAKE_INT_N`, pulled up by `R3` 10 kΩ to `+3V3` and landing on **GPIO21**, which is not a strapping pin. **The pull-up is mandatory and is what makes the line deterministic — inactive HIGH — before any register is written; no interrupt floats.** Discovery order on a wake: read **4Ch/4Dh on `U2`, then on `U3`**; the status registers name the changed bit directly instead of forcing a read of every port register on every device. **`U23` is never read** — it holds no interrupt source. **`INT` clears on a read of the INPUT PORT register (00h/01h), so firmware must read it after the status register or the line stays LOW and no further edge appears.** **Mask policy:** unmasked = six buttons, `TOUCH_INT_N`, `SX1262_DIO1`, `SD_CARD_DETECT_N`, `ACC_DETECT_N`, `ACC_POWER_FAULT_N`; masked = `BQ25185_STAT2` and **all ten XGPIO, which is MX-9** — an accessory must not be able to hold the shared wake line and starve the buttons. **12 unused `U23` pins stay inputs; firmware must enable their on-die pulls (46h/47h) or drive them as outputs, because floating CMOS inputs burn crowbar current.** | 2026-08-23 |
| D-172 | **THE SIX-BUTTON SET IS FINAL AND THE SWITCH IS VERIFIED.** UP, DOWN, LEFT, RIGHT, A/SELECT, B/BACK on `U2` P10–P15. **HOME is REMOVED — `SW8` and `R10` are deleted, not hidden and not DNP; no `BTN_HOME_N` net exists.** **Volume Up/Down are not invented** — they never existed electrically. Power remains the `SW9` SPDT hard switch on the TPS63020 enable, deliberately not a GPIO; BOOT remains `SW1` on GPIO0, electrically unchanged and mechanically recessed. **`PTS645SM43SMTR92LFS` confirmed a real orderable line** in the Littelfuse/C&K PTS645 datasheet: **1.6 N ± 0.3 (~163 gf), 100 000 operations, 0.30 +0.1/−0.15 mm travel, 7.0 mm, SPST N.O. momentary, silver gull-wing SMD.** Active LOW with **external 10 kΩ pull-ups** — kept external because 100 kΩ against 1 µA of leakage is a weak high and 10 kΩ is defined **before firmware writes a register** — drawing 0.33 mA when held, **33× the datasheet's 10 µA minimum wetting current**. **Firmware debounce, no RC**: the input is read over I²C after an interrupt, so a capacitor would add parts and solve nothing; the input latch 44h/45h is available if a short press is missed. **B-67 opened: Littelfuse publishes no bounce figure for the PTS645, so the earlier "≤ 5 ms" claim is not datasheet-backed — use 10–20 ms and measure.** | 2026-08-23 |
| D-173 | **THE ACCESSORY CONTROL AND STATUS ENDPOINTS ARE LANDED ON `U3` P12–P15**, which the interrupted session had left as bare `no_connect` flags: `ACC_3V3_EN` (P12), `ACC_5V_EN` (P13), `ACC_DETECT_N` (P14), `ACC_POWER_FAULT_N` (P15). **`ACC_DETECT_N`'s 100 kΩ pull-up (`R129`) is placed HERE, at the expander, not on sheet 09**, so the input has a defined level before the connector sheet is migrated and D-085's "detection works with both rails OFF" is true today; **sheet 09 adds only the connector contact and MUST NOT add a second pull-up.** It is a sheet-08-local net until then. **`ACC_PWR_EN` is KEPT on `U3` P17 even though it drives only the DNP `U15`/`U16`**: retiring it would leave two sheet-09 inputs undriven and sheet 09 is out of scope. **It is the pin O-4 is expected to free.** `RESERVED_SPARE` therefore moves from D-094's `U3` P16 to **`U23` P03, with `R130` 100 kΩ and `TP41`** — where it is stronger, because twelve further I/O sit beside it. | 2026-08-23 |
| D-174 | **SHEETS 01 AND 03 WERE TOUCHED ONLY TO PUBLISH NETS THE BRIEF REQUIRES LANDING.** Five local labels on sheet 01 (`BQ25185_STAT1`, `BQ25185_STAT2`, `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_POWER_FAULT_N`) and one on sheet 03 (`SD_CARD_DETECT_N`) were promoted to hierarchical labels, and the root sheet gained the matching sheet pins, stubs and labels. **No component, value, net topology or DNP state on either sheet was altered** — the diffs are 28 and 5 lines. Without this the brief's requirement to land STAT1/STAT2 and card detect on a PCAL input cannot be met at all, because those nets were sheet-local. | 2026-08-23 |

> **Result (FBV2-S1-008).** Full analysis:
> [`audits/2026-08-23-s1-buttons-expanders-rgb-implementation.md`](audits/2026-08-23-s1-buttons-expanders-rgb-implementation.md).
>
> **Task gate FBV2-S1-BUTTONS = PASS. ERC 42 messages / 1 error / 41 warnings — the violation
> set is IDENTICAL, line for line, to the recovered working tree, and better than the 45 / 2 / 43
> that stood before sheet 08 was touched.** Zero new errors. 319 components, 0 duplicate
> references, 0 without a footprint, 0 `*_TBD` nets, no `TCA9535PWR` in living hardware, no HOME
> electrical path, no `RGB_*_CTL` architecture restored. `fork_equivalence.py` PASS,
> `netclass_probe.py` PASS, **PCB still bit-identical to Beta-DM**. **Sheet 09 untouched.**
>
> **`RESERVED_SPARE` did not exist before this task.** D-094 has required it since 2026-08-23 and
> no sheet had implemented it. It exists now.
>
> **Repaired in passing:** six root-sheet UUIDs written with the prefix `fb080r00-`. "r" is not a
> hex digit; KiCad silently reassigns invalid UUIDs on save, which would have destroyed pass
> traceability without any visible failure.
>
> ### ~~O-6~~ — **RATIFIED AND CLOSED 2026-08-23 by D-175 (FBV2-S1-009). `U23` and the front RGB are LOCKED architecture; B-37 is retired.** Original text retained:
>
> **`U23`, a third `PCAL9535APW,118` at `0x22`, is implemented.** The arithmetic is not close:
> **35 committed signals against 32 pins**, with every line locked by D-082, D-094, D-117,
> Ruling G, the safe-state set or this brief. The brief anticipated failure and named a smart LED
> as the escape — **that escape is impossible here**, because a WS2812 needs RMT on a native GPIO
> and the ledger measures **33 of 33 usable native pins assigned, zero free** (B-10), with
> GPIO35/36/37 unavailable on the N16R8. An I²C LED driver would be a new part family for one
> indicator. A third device of the **same MPN** is the cheapest possible answer: no new part
> number, no new land pattern, no new driver, no new rail, ≈ $0.55, and **B-37 retires** with 12
> spare I/O.
>
> **The costs, stated plainly.** One TSSOP-24 (7.8 × 4.4 mm) plus one 0603 must be placed on a
> board whose enclosure fit is **already flagged as unverified**. That is the real objection, and
> it is a placement objection rather than an electrical one.
>
> **If O-6 is declined, delete `U23`, `D13`, `R124`–`R126`, `R130`, `C83` and `TP41`.** The
> product loses the front status light and the reserved spare; **no core, community or safety
> function moves**, because the allocation was built that way deliberately (D-166).
>
> **Nothing else was added:** no second indicator, no light sensor, no PWM dimming hardware, no
> smart LED, no LED driver IC, no RC debounce, no second interrupt line, no new rail, no new
> connector, no new native GPIO, and no change to the community port allocation.

---

## 8x. Community expansion port and FBV2-S1 closeout — FBV2-S1-009 (2026-08-23)

> ### ⚠ THE SCHEMATIC MIGRATION IS COMPLETE. THE BOARD IS NOT.
> All nine sheets carry the Full Beta v2 architecture and `fork_equivalence.py`'s
> "still Beta-DM" list is **empty**. **FBV2-S1 = PASS means SCHEMATIC MIGRATION COMPLETE. It does
> NOT mean fabrication ready** — no placement, no routing, no outline, no DFM, no mechanical CAD
> and no physical validation exist. Closeout:
> [`audits/2026-08-23-s1-schematic-migration-closeout.md`](audits/2026-08-23-s1-schematic-migration-closeout.md).

| # | decision | date |
|---|---|---|
| D-175 | **O-6 RATIFIED AND CLOSED. `U23`, a third NXP `PCAL9535APW,118` at `0x22`, is a LOCKED part of the Full Beta v2 architecture, and the front RGB status light stays.** The reasoning stands as recorded at D-165: **35 committed expander signals against the 32 pins on `U2` + `U3`**, with every escape closed — zero free native GPIO (B-10) makes a WS2812 impossible, D-094 mandates `RESERVED_SPARE`, D-082 locks the ten XGPIO, and a dedicated LED driver would be a new part family for one indicator. `U23` adds **no new MPN family, no new footprint, no new firmware driver and no new power rail**, and it preserves substantial no-respin spare capacity. **B-37 is RETIRED**: the programme carried "zero expander spare" from its first audit and now has eleven. | 2026-08-23 |
| D-176 | **O-4 APPROVED AND CLOSED. `U16` TCA9517A IS REPLACED BY TI `TCA4307DGKR`** (LCSC **C880333**, VSSOP DGK-8), verified live per D-096 on 2026-08-23: **3 248 in stock, ships now**, $2.51 @1 / $1.71 @1k. **It is FITTED; the TCA9517A was DNP.** WHY: the community port is inherently **hot-plug** and the external segment is **3.3 V only**, so the TCA9517A's level translation was never used while its hot-insertion and stuck-bus weaknesses were. From **SCPS270B**: the IN side is not joined to the OUT side until a **STOP or bus-idle** condition, so live insertion cannot corrupt a transfer; **1 V precharge** on all four SDA/SCL pins (`VPRE` 0.8/1.0/1.2 V); **stuck-bus recovery** — SDAOUT or SCLOUT held low for **`tSTUCKBUS` 25 ms MIN / 40 ms typ / 65 ms MAX** disconnects the bus and issues **up to 16 pulses on SCLOUT** at 5.5/8.5/14 kHz; **powered-off high-impedance I²C pins**; clock stretching, arbitration and synchronisation supported; **`fSCL` max 400 kHz — FAST MODE, NOT 1 MHz**; `ICC` 2.5 mA typ / 4.5 mA max, `ISD` 10 µA typ / 30 µA max; UVLO 2.1 V rising. `VCC` = `ACC_3V3_SW`, so with the accessory rail off the part is **unpowered and invisible to the internal bus on both sides** — the isolation is structural, not a firmware promise. `EN` = `ACC_PWR_EN`, active HIGH, **held LOW by `R17` 100 kΩ on sheet 08**, so the buffer is isolated until firmware explicitly enables it and the safe state does not rest on the PCAL reset state alone. **THE CIRCULAR DEPENDENCY IS BROKEN**: a wedged accessory no longer requires the MCU to command the expander over the very bus that is wedged. **Cost: roughly $1.20–2.00 per board more than the part it replaces.** | 2026-08-23 |
| D-177 | **ACCESSORY I²C COMPATIBILITY RULE — NORMATIVE. An accessory must NEVER hold `EXT_SDA` or `EXT_SCL` low for longer than 25 ms**, the `tSTUCKBUS` **MINIMUM** from SCPS270B. Beyond it the TCA4307 disconnects the accessory and issues up to 16 recovery clocks. **The number to design against is the minimum, not the 40 ms typical.** This forbids clock stretching beyond 25 ms and forbids slow bit-banged accessory firmware. It must appear in accessory-facing documentation. | 2026-08-23 |
| D-178 | **P-18 IS CLOSED. NO I²C MUX.** The external segment remains **one logical address space with the internal bus whenever an accessory is connected**, and that is deliberate. **The TCA4307 solves ELECTRICAL fault isolation; [`architecture/I2C_ADDRESS_REGISTRY.md`](architecture/I2C_ADDRESS_REGISTRY.md) solves ADDRESS allocation.** Putting the entire internal AQROOT bus behind a mux would add a part, add a failure mode and add a firmware dependency to protect against a problem that a published reserved-address policy already answers. **`0x50` is NOT widened to `0x50`–`0x57`; P-19 remains future protocol scope** unless a concrete multi-EEPROM need appears. | 2026-08-23 |
| D-179 | **COMMUNITY CONNECTOR FOOTPRINT VERIFIED AND BUILT.** `J5` = Samtec **`BCS-112-S-D-HE`**, re-confirmed live 2026-08-23 per D-096: **ACTIVE, 385 pieces ship tomorrow**, $7.314 @1 / $5.667 @100, UL E111594, RoHS, halogen-free, MSL 1. The land pattern is taken from the Samtec **RECOMMENDED PCB LAYOUT, REVISION B, FIG 3 = `BCS-1XX-XXX-D-HE-XXX`**: **2.54 mm within a row, ROW-TO-ROW .310 ±.002 in = 7.87 ±0.05 mm, .028 in = 0.71 mm PTH**, pin field = positions × 2.54 − 2.54 = **27.94 mm**. **A VERTICAL 2×12 PATTERN IS NOT A SUBSTITUTE** — its rows sit 2.54 mm apart. **Odd = row A, even = row B**, verified pin by pin against the netlist; pad 1 is rectangular with a silkscreen tick. Body 30.48 × 8.13 × 5.33 mm, courtyard 31.48 × 9.13 mm. **No key contact — the enclosure supplies keying (D-097).** `BCS-112-L-D-HE` remains a plating-only alternate with an identical footprint. **ASSEMBLY: if the JLC service cannot place this through-hole part automatically it becomes a MANUAL/SECONDARY assembly operation for the first five boards. The connector architecture is not compromised for SMT convenience.** | 2026-08-23 |
| D-180 | **THE 24-CONTACT ALLOCATION IS BUILT AND VERIFIED PIN BY PIN AGAINST D-084.** 24 active contacts, **no NC, no key contact, no duplicate GPIO**; only GND (×4) and the two rails (×2 each) repeat. **Every power contact is vertically paired with GND** — 3/4, 9/10, 15/16, 21/22 — so a row-swap can only make a current-limited rail-to-ground short, never 5 V on a logic pin; **all 3.3 V is in row A and all 5 V in row B**. **REQUIRED ACCESSORY-FACING WORDING, on the silkscreen and in accessory documentation:** *"COMMUNITY PORT — 3V3 LOGIC ONLY / 5V PIN IS POWER OUTPUT ONLY"* and *"The two ACC_3V3 contacts share the total 3.3 V rail limit. The two ACC_5V contacts share the total 5 V rail limit. Duplicate contacts do not multiply the available current."* | 2026-08-23 |
| D-181 | **EXTERNAL I²C PULL-UPS RE-DERIVED: `R49`/`R50` = 1.5 kΩ to `ACC_3V3_SW`, FITTED. THE INHERITED 4.7 kΩ IS REJECTED AND WAS ALSO DNP.** With `tr` = 0.8473 × R × C and a **200 pF design-point external bus** (≈ 20 pF board + 5 pF connector + ≈ 100 pF for 300 mm of cable + 50 pF module), 4.7 kΩ gives **796 ns against the 300 ns fast-mode limit — it fails 400 kHz by 2.7× and only ever worked at 100 kHz**. 1.5 kΩ gives **254 ns and PASSES FAST MODE ON THE STATIC PULL-UP ALONE**, with the TCA4307's 2–5 mA rise-time accelerator as margin rather than as the mechanism; static sink to 0.4 V is 1.93 mA, inside the 3 mA an I²C device must sink. **PUBLISHED ACCESSORY RULE: total external bus capacitance ≤ 200 pF for 400 kHz and ≤ 400 pF for the 100 kHz bring-up mode.** **100 kHz bring-up is retained and no 1 MHz claim is made.** **The internal bus is untouched: `R19`/`R20` 2.2 kΩ remain its only pull-up pair (D-139).** The **22 Ω** series elements are retained and re-justified against the buffer actually fitted: 4.4 ns of delay at 200 pF, at most 110 mV across them at the accelerator's 5 mA, and they isolate a contact short or ESD strike from the pull-up node and the buffer pin. | 2026-08-23 |
| D-182 | **`TCA4307` `READY` HANDLING LOCKED. `R46` 10 kΩ to the TCA4307's OWN `VCC` (`ACC_3V3_SW`), brought out to `TP44`, and NO PCAL PIN IS CONSUMED IN REV 1.** 10 kΩ is TI's application value and is the value the datasheet's UVLO characterisation is specified with. **It must not be pulled to `+3V3`** — that would push current into an unpowered device's pin and defeat the powered-off high-impedance property the entire isolation argument rests on. `READY` is the single best bring-up observable on the sheet: it distinguishes *rail off*, *enabled but never connected* and *connected and healthy*. Noted honestly: while `EN` is low the datasheet warns current flows from `VCC` through the pulled-down `READY` pin — 0.33 mA — but the rail is OFF by default, so the no-accessory state costs nothing. | 2026-08-23 |
| D-183 | **`ACC_DETECT_N` IS BUILT AS LOCKED, AND HOT-PLUG BOUNCE IS A FIRMWARE PROBLEM — NO RC IS ADDED.** Contact 23, asserted by the accessory shorting it to the adjacent GND at contact 21 with one 0 Ω link; **the 100 kΩ pull-up is `R129` at the expander on sheet 08 and sheet 09 adds NO second pull-up**. Detection works with both rails off, which is what makes MX-3 implementable and a flipped accessory passively safe. **`R64` 100 Ω series is ADDED**: D-090 did not list this contact, which was an inconsistency, since it is exposed and runs straight to a PCAL input. Debounce is **firmware, 20 ms assert / 20 ms de-assert**. **AN RC WOULD BE ACTIVELY HARMFUL:** the same time constant that suppresses insertion chatter also **delays removal detection**, and removal is the safety-critical edge because **MX-6 requires both rails down within 100 ms of detect loss**. A passive filter cannot be asymmetric; firmware debounce can, and costs nothing. | 2026-08-23 |
| D-184 | **3.3 V ACCESSORY RAIL `R_ILIM` RE-DERIVED AND RETAINED AT 1.5 kΩ.** SLVSFJ2B §10.2.2: **`ILIM` = 1.18 × (R_ILIM in kΩ)^−1.072**, verified against three datasheet rows, tolerance ±25 %. 1.5 kΩ → **0.764 A typ, 0.573–0.955 A**. **Re-derived against the CURRENT budget**, which has grown since FBV2-COMM-001 by the IR transmitter (**+50 mA burst average**; the 150 mA peaks are supplied by `C12` 22 µF, not by the rail) and the front RGB (+4.2 mA): internal worst case **≈ 823 mA**, so an accessory hard short puts `+3V3` at **1 778 mA = 89 % of the TPS63020's 2 A** — margin narrowed from 86 % but **no foldback and no brownout**. 1.21 kΩ would reach 102 % and 1.15 kΩ 105 %. Worst-low limit 0.573 A against the published 400 mA leaves **43 % headroom**, so a compliant accessory never trips it. **`TPS22950CDDCR` confirmed ACTIVE at TI 2026-08-23.** **PUBLISHED LIMIT: 400 mA TOTAL across BOTH 3.3 V contacts on the first five boards.** | 2026-08-23 |
| D-185 | **5 V ACCESSORY RAIL RE-DERIVED AND UNCHANGED IN ARCHITECTURE; `R_ILIM` RETAINED AT 1.65 kΩ.** `BQ25185_SYS` → `U21` **`TPS61023DRLR`** at 5.0 V → `U22` **`TPS22950CDDCR`** → `ACC_5V_SW`. **Verified from the netlist to be electrically independent of USB `VBUS` and of the NFC 5 V fallback**: `ACC_5V_RAW` touches only `U21`, `U22`, `C65`, `C66`, `R99`, `TP28`, and the NFC branch (`U13`, `L2`, `C34`, `C35`, `R44`, `R45`) remains a separate DNP branch on `NFC_5V_PA_PENDING`. Only `SYS` and the TPS61023 **device family** are shared. Setpoint `R99` 732 k / `R100` 100 k with `VREF` ≈ 0.6 V → **4.99 V**. `L4` **1 µH Würth 74438357010, FITTED**; peak inductor current at the 0.86 A worst-high limit and `V_SYS` 3.0 V is **2.19 A**, so **`I_sat` ≥ 3 A is the requirement — confirm the actual part at BOM lock (B-68)**. 1 MHz switching above `V_IN` 1.5 V; **3.7 A valley switch limit**; **true input-to-output disconnection in shutdown**; `C64` 10 µF in, `C65`+`C66` = 44 µF out; thermally ≈ 0.17 W at 300 mA in SOT-563, ≈ 34 K rise — measure. `R_ILIM` 1.65 kΩ → **0.690 A typ, 0.52–0.86 A**, giving 73 % headroom over the published limit and staying inside the boost's switch limit. **PUBLISHED LIMIT: 300 mA TOTAL across BOTH 5 V contacts on the first five boards.** | 2026-08-23 |
| D-186 | **THE 5 V ENABLES ARE SPLIT — CTO RELIABILITY REFINEMENT, IMPLEMENTED.** The single `ACC_5V_EN` is superseded by **`ACC_5V_BOOST_EN` on `U3` P13 → `U21` `EN`** and **`ACC_5V_SW_EN` on `U23` P04 → `U22` `ON`**. Both carry independent external safe-state pull-downs: `R102` 100 kΩ and the **new `R131` 100 kΩ**, plus `TP47` on the new enable. **`R131` is mandatory, not a convenience** — SLVSFJ2B specifies a 500 kΩ smart pull-down inside the part **and still requires an external one**, and the PCAL powers up high-impedance. `U23` P04 was a spare; **`U23` is now 5 used / 11 spare** plus `RESERVED_SPARE`. **POWER-UP: verify `ACC_DETECT_N` → `ACC_3V3_EN` = 1 → wait ≥ 5 ms (MX-4) → `ACC_5V_BOOST_EN` = 1 → wait ≥ 5 ms → `ACC_5V_SW_EN` = 1. POWER-DOWN exactly reversed.** Detect loss or `FLT` still forces prompt shutdown (MX-5, MX-6). **The 5 ms converter-settle delay is DERIVED: the TPS61023 soft start is 700 µs TYPICAL with NO published maximum, so the first build uses 7× typical and measures it (B-69).** **WHAT THE SPLIT BUYS:** two independent series disconnects in the 5 V path — the boost truly disconnects input from output in shutdown and the load switch adds reverse-current blocking — so a single stuck enable can no longer energise the contact; and with `U22` still off **the boost starts into a known 44 µF instead of an unknown hot-plugged accessory**, which turns the start-up time from an accessory variable into a board constant. **No PGOOD IC was added.** | 2026-08-23 |
| D-187 | **THE WAKE ISOLATION GATE EXISTS IN COPPER FOR THE FIRST TIME. B-08 IS CLOSED IN HARDWARE.** `Q10` **2N7002** between `WAKE_ATTN_N_HDR` and `WAKE_INT_N`, gate driven by `ACC_3V3_SW`, with `R63` 10 kΩ pulling the contact side to `ACC_3V3_SW` and `R66` 330 Ω in series at the contact. **ORIENTATION IS LOAD-BEARING: the SOURCE faces the connector and the DRAIN faces the internal line**, so the body diode's anode is on the accessory side and, with the rail off, an accessory pulling the contact to ground **reverse-biases it against the internal 3.3 V**. Reverse the FET and the body diode alone defeats the whole arrangement. **A shorted or hostile accessory therefore cannot hold `WAKE_INT_N` low and cannot starve the internal buttons.** `R63` **must** pull to `ACC_3V3_SW` and not `+3V3`, or the contact stays live with the rail off and B-08 re-opens from the other side. **RESIDUAL, BOUNDED AND RECORDED:** a hostile accessory *driving* the contact to 5 V with the rail off forward-biases the body diode and injects **≈ 3 mA** into `WAKE_INT_N` through `R66` — inside every clamp on the net, and the reason `R66` is 330 Ω rather than 100 Ω. **B-36 stands:** accessory-initiated wake from sleep requires `ACC_3V3_SW` to remain enabled during sleep. | 2026-08-23 |
| D-188 | **THE COMMUNITY-PORT ESD ARRAYS ARE FITTED, NOT DNP, AND ONE MPN COVERS ALL SIXTEEN PROTECTED CONTACTS.** TI **`TPD4E1B06DRLR`** (SLVSBQ8E): 4-channel bi-directional, **IEC 61000-4-2 ±12 kV contact / ±15 kV air-gap** — beyond level 4 — IEC 61000-4-5 surge 3.0 A (8/20 µs), **I/O capacitance 0.7 pF typical**, leakage 0.5 nA max, **`VRWM` ±5.5 V**, DRL/SOT-563. Four arrays cover `XGPIO0-9`, `NATIVE_A`, `NATIVE_B`, `EXT_SDA`, `EXT_SCL`, `WAKE_ATTN_N` and `ACC_DETECT_N`. **D-090 specified TVS only on the natives and the I²C pair; that under-weighted the XGPIO**, which run to a PCAL9535A whose destruction costs a board rather than a $0.55 chip — and the footprints already existed, marked DNP. **Shipping a user-accessible connector with ten unprotected signal contacts is not a defensible state**, so this is a low-risk correction applied rather than a blocker raised. **DELIBERATELY NO TVS ON EITHER POWER RAIL: `VRWM` 5.5 V against a 5.0 V nominal rail leaves no working margin**, and a clamp that close leaks and ages; the rails are protected by their bulk capacitance, the TPS22950C ratings and the current limit. **`TPD2E009DBZR` is eliminated from the BOM.** Series protection is unchanged and verified: **100 Ω on every XGPIO and both natives, 22 Ω on the I²C pair, 330 Ω on WAKE**, plus the new 100 Ω on `ACC_DETECT_N`. | 2026-08-23 |
| D-189 | **THE INHERITED SHEET-09 DEFECTS ARE RECORDED SO THEY CANNOT RETURN.** The Beta-DM community sheet carried, all of which are now deleted: a **26-pin 2×13 MALE `TSW-113-08-G-D-RA`**; **permanent raw `+3V3` on contact 1**, against D-057; **fourteen XGPIO**; `FAST_IO_GPIO43_HDR`, withdrawn by D-106; `RESERVED_NC`; **`U15` TPS22918, a second and DNP accessory 3.3 V switch feeding a sheet-local `ACC_3V3_SW` that was NOT the real rail**; and `R66` wired straight through with **no isolation FET**. **`01:ACC_3V3_SW` and `09:ACC_3V3_SW` were different nets and `01:ACC_5V_SW` reached nothing outside sheet 01 — the community port had no power at all.** **This is the SIXTH consecutive migrated sheet on which an inherited `DNP` was load-bearing** (`U16`, `R49`, `R50` and six TVS arrays): the FBV2-S1-007 finding held to the last sheet. | 2026-08-23 |
| D-190 | **FBV2-S1 IS CLOSED. ALL NINE SHEETS ARE MIGRATED AND `fork_equivalence.py`'s "still Beta-DM" LIST IS EMPTY.** Measured at closeout: **321 components, 0 duplicate references, 0 without a footprint, 224 nets, 0 `*_TBD`**; the GPIO ledger re-read from the netlist pin by pin with **33 of 33 usable native GPIO assigned and no boot-strap regression**; three PCAL addresses at 0x20/0x21/0x22; the 24-contact allocation matching D-084 exactly; **ERC 27 messages, ZERO ERRORS, 27 warnings — the design has no ERC errors for the first time in the programme.** **FBV2-S1 = PASS MEANS SCHEMATIC MIGRATION COMPLETE AND NOTHING MORE.** It does not mean fabrication ready: placement, routing, outline, DFM, footprint verification beyond the four audited parts, mechanical fit and physical validation are all still ahead. | 2026-08-23 |

> **Result (FBV2-S1-009).** Full analysis:
> [`audits/2026-08-23-s1-community-sheet09-implementation.md`](audits/2026-08-23-s1-community-sheet09-implementation.md);
> programme closeout:
> [`audits/2026-08-23-s1-schematic-migration-closeout.md`](audits/2026-08-23-s1-schematic-migration-closeout.md).
>
> **Task gate FBV2-S1-COMMUNITY = PASS. Programme gate FBV2-S1 = PASS.**
> **ERC 42 / 1 / 41 → 27 / 0 / 27:** the inherited `RESERVED_NC` **error** and all **fourteen**
> `isolated_pin_label` warnings — `XGPIO10`–`13`, `FAST_IO_U0TXD_ROOTPROBE_CS`, `NATIVE_A` and
> `NATIVE_B`, each on both the root and its child sheet — are gone. **Sheets 08 and 09 are
> individually clean.** The 27 survivors are the 18 `J1` unused-display-bus pin-type artefacts,
> the 2 BMI270 `ASDx`/`ASCx` artefacts, the MAX98357A thermal pad and 6 parked RF stubs — all
> pre-existing and all previously explained. `fork_equivalence.py` PASS, `netclass_probe.py` PASS,
> **PCB still bit-identical to Beta-DM.**
>
> **A correction worth recording.** Rebuilding sheet 09 deleted `#FLG0105`, a `PWR_FLAG` that had
> been sitting on the Beta-DM community sheet and was **the only power-output driver on the entire
> GND net**; its loss turned every GND `power_in` pin in the design undriven. It was **re-created
> on sheet 09 with the same reference and a note explaining its role.** This is not a fake power
> flag added to silence a check — it is the restoration of the check's only legitimate satisfier,
> which the rebuild had removed by accident.
>
> ### ~~O-7~~ — **CLOSED 2026-08-23 by D-191 (FBV2-S2-001): OPTION A. `R49` = `R50` = 1.5 kΩ, and the published contract is <= 200 pF at 400 kHz / <= 400 pF at 100 kHz.** Original text retained:
>
> **`R49`/`R50` are 1.5 kΩ, sized for a 200 pF external bus. That capacitance is an engineering
> estimate, not a measurement, and it is the one published figure an accessory author can violate
> without knowing.** Options: **(a)** accept 200 pF as the published ceiling for 400 kHz — what is
> implemented and documented; or **(b)** drop to 1.0 kΩ, covering 300 pF at 400 kHz for 2.9 mA of
> static sink instead of 1.9 mA. **It is one 0603 either way and the footprint is fitted**, so it
> closes on the first measured board rather than now. Raised because it is the last un-measured
> number on the sheet.
>
> **Nothing else was added:** no I²C mux, no PGOOD IC, no second connector, no RC on detect, no
> extra rails, no new product features, no new native GPIO, no firmware, and no change to the
> 24-contact allocation, the enclosure or the PCB.

---

## 8y. Pre-placement release audit — FBV2-S2-001 (2026-08-23)

> ### ⚠ FBV2-S2 = **FAIL** ON TWO OF FOURTEEN EXIT CRITERIA — AND THE AUDIT EARNED ITS KEEP.
> It found a **fabrication-blocking defect that would have produced a board with a complete NFC
> antenna, matching network and crystal — and no NFC chip** — corrected it, and closed nine stale
> register entries. What fails is **eight critical footprints not read against a manufacturer
> drawing** and an **incomplete JLC/LCSC assembly classification**. Both are fabrication-release
> blockers; **neither blocks PCB placement.** Full analysis:
> [`audits/2026-08-23-s2-preplacement-release-audit.md`](audits/2026-08-23-s2-preplacement-release-audit.md).

| # | decision | date |
|---|---|---|
| D-191 | **O-7 CLOSED AS OPTION A. `R49` = `R50` = 1.5 kΩ, LOCKED.** The community external I²C contract is **≤ 200 pF total external bus capacitance at 400 kHz and ≤ 400 pF at 100 kHz**, and it must appear in accessory-facing documentation in those terms. **NOT changed to 1.0 kΩ merely to extend the 400 kHz capacitance claim:** NXP **UM10204** treats a simple resistor pull-up as the normal Fast-mode solution **up to 200 pF** and prescribes a current-source or switched-resistor arrangement above it, and AQROOT does not need that complexity for a hobby-accessory port. **RETAINED UNCHANGED: `TCA4307DGKR`, the external 1.5 kΩ pull-ups, the 22 Ω series elements and the 100 kHz fallback.** | 2026-08-23 |
| D-192 | **NFC WAS STILL MARKED DNP AND IS NOW FITTED. THIS WAS A FABRICATION-BLOCKING DEFECT.** `U9` **ST25R3916-AQET** and its twelve mandatory supply-decoupling capacitors — `C19` and `C55` on `NFC_SUPPLY`, `C45`/`C46` on `VDD_D`, `C47`/`C48` on `VDD_A`, `C49`/`C50` on `VDD_RF`, `C51`/`C52` on `VDD_AM`, `C53`/`C54` on `AGDC` — were inherited from Beta-DM marked `DNP`, **against D-035** (*"NFC is mandatory in the FIRST Full Beta v2 fabrication. No DNP showcase shortcut"*) **and D-055** (*"NFC must be FITTED and functional on the first fabrication"*). Everything around the chip was already FITTED: the 27.12 MHz crystal, the complete differential matching network, the antenna connector and the SPI wiring. **The first five boards would have carried a finished 13.56 MHz front end with no NFC chip on it.** All thirteen parts are now FIT; none of the twelve capacitors is optional in DS12484. **THIS IS THE SEVENTH CONSECUTIVE SHEET WITH A LOAD-BEARING INHERITED `DNP`, and it survived four migrations because sheet 04's own migration was about the antenna and the matching network — nobody re-read the population state of the IC underneath.** Six `U9` pins stay deliberately unconnected — `CSO`, `EXT_LM`, `AAT_A`, `AAT_B`, `CSI`, `MCU_CLK` — all optional features this product does not use, each with a recorded ERC exclusion. | 2026-08-23 |
| D-193 | **P-14 RESOLVED: THE MAX17048 STAYS ON `BAT_PROTECTED_P`. NO HARDWARE CHANGE.** Measured from the netlist, `U14` `CELL` and `VDD` are **already on the fully protected node** — after both back-to-back FET stages and after the 15 mΩ sense resistor. **The gauge is not on `BAT_RAW` and never was.** Moving it to `BAT_SENSE` — the clean node after `P2` but before `R75` — was evaluated and **REJECTED**: `BAT_SENSE` is the **LTC4368's precision current-sense input**, and hanging a fuel gauge's `VDD` and its bypass capacitor there creates a **differential capacitance across `R75`** that distorts the reverse-current comparator during fast current steps, opens a deliberate blind spot in a protection measurement, and injects I²C and quick-start transients onto the sense node. **What it would have bought is inside the noise:** 15 mΩ costs **26 mV at the 1.75 A pack worst case, 4.5 mV at a typical 300 mA idle and 7.5 mV during a 500 mA charge**, i.e. **≤ 2.6 % SOC at peak load and < 0.5 % typical** — coarser than the MAX17048's own ModelGauge error without cell characterisation, and **compensable in firmware by subtracting I × 15 mΩ**. **SAFETY OUTRANKS SOC ACCURACY, exactly as directed.** Checked and passed: no sneak or back-power path, the gauge's I²C cannot bypass `P2`, its decoupling is on the bulk node not the sense node, dead-cell recovery is unaffected, charge measurement stays valid, and the node cannot exceed cell voltage in any fault case because both FET stages are anti-series. | 2026-08-23 |
| D-194 | **B-47 RESOLVED — OUTCOME B: THE FH52E IS NOT COMPATIBLE, AND D-077'S DROP-IN CLAIM IS STRUCK.** Both Hirose land patterns were read. **FH69-50S-0.5SH: top AND bottom 2-point contact, back-flip actuator, 2.3 mm, signal land 0.30 × 1.23, hold-down 0.36 × 4.25 at 28.73 c/c, overall layout depth 7.38 mm.** **FH52E-50S-0.5SH: BOTTOM contact only, front-flip actuator, 2.0 mm, signal land 0.30 wide with a 0.8 land and a 4.6 mm depth datum** — and the FH52 catalogue states in its own words that *"the recommended PCB mounting pattern for the **FH12 Series** can be used as well"*. **7.38 mm against 4.6 mm: they cannot share pads.** **D-077's statement that `J1` is "laid out on the FH12/FH52E standard land pattern so `FH52E-50S-0.5SH` (LCSC C7465440) is a drop-in second source" IS FALSE and is WITHDRAWN** — placement would otherwise have proceeded believing a second source existed. Beyond the pattern, FH52E also gives up the two-point top-and-bottom contact that D-076/D-077 chose FH69 for on a 50-way flex carrying display **and** touch. **RULING: keep the dedicated vendor-exact FH69 footprint; `J1` IS MANUAL ASSEMBLY FOR THE FIRST FIVE.** For five prototypes, hand-soldering a proven connector beats a speculative footprint migration. | 2026-08-23 |
| D-195 | **RADIO RF INTERFACES CLOSED. B-49 AND B-51 CLOSED.** **B-49 was never a risk:** Ebyte's own product description states the `E07-400M10S` ships "in the form of dual antennas (**IPEX/stamp hole**)", and the same holds for the `E22-900M22S` — **the standard part number carries both, so there is no variant selection to get wrong.** **433 MHz: Taoglas `FXP450.07.0100C`** (SPE-23-8-180-A) — **410–470 MHz**, **I-PEX MHF1 (U.FL)**, 100 mm, adhesive; stocked DigiKey 21704215, Arrow, TTI. **915 MHz: Amphenol RF `095-902-568-150`, LOCKED** — manufacturer page 2026-08-23, **Part Status ACTIVE**: AMC right-angle plug → **SMA straight bulkhead jack, IP67**, RG-178, **50 Ω, 150 mm**, 6 GHz; the AMC series is documented **"compatible with Hirose U.FL and IPEX MHF1"**. **IT IS ONE ASSEMBLY — pigtail and panel bulkhead in a single orderable part, so no separate bulkhead MPN exists or is needed.** Loss ≈ **0.4 dB** at 915 MHz against a +22 dBm module. The right-angle plug keeps the vertical stack low over a flat-lying module. **No PCB RF routing was added.** **O-8 OPENED: the 915 MHz external whip antenna MPN is still not selected** — accessory-class, no board impact. | 2026-08-23 |
| D-196 | **B-46 CLOSED AND THE ASSUMPTION WAS CORRECT. NO CHANGE.** Molex sales drawing **SD-502570-001 Rev A**, sheet 1 of 2, note 4, DETECT SWITCH table: **CARD INSERTING POSITION = CLOSE, NO CARD = OPEN.** With `J2.11` `DETECT_LEVER` grounded — the drawing's own recommended pattern labels that land *"Vss : GROUND"* — and `J2.10` pulled up by `R113` 100 kΩ, **card present drives `SD_CARD_DETECT_N` LOW and no card leaves it HIGH**, exactly as D-117 assumed. **No firmware polarity correction and no hardware change.** | 2026-08-23 |
| D-197 | **B-68 CLOSED, AND TWO STALE "FOOTPRINT BLOCKED" NOTES ARE WITHDRAWN.** The data was already in the schematic and had never been checked against the circuit. **`L4` (accessory boost) = Würth `74438357010`: Isat 6.2 A at the 10 % inductance-drop point, 12.5 A at 30 %, IRP,40K 10.25 A, RDC 11.6 mΩ — against a 2.19 A peak inductor current at the 0.86 A worst-high current limit with `V_SYS` at 3.0 V. 2.8× margin.** Recorded alongside it: **`L1` (main TPS63020) = Coilcraft `XFL4020-152MEC`, Isat 4.1 A against an ≈ 2.9 A peak at 2 A out from a 3.0 V cell — 1.4×, THE TIGHTEST MAGNETICS MARGIN ON THE BOARD**, to be measured at first article before any published rail limit is raised. **`L1` and `L2` both carried a "FOOTPRINT STILL BLOCKED" note claiming the recommended land pattern could not be resolved from text extraction. Both land patterns were subsequently built from the manufacturer drawings** — Coilcraft 745-3 rev 03/10/26 and Würth rev 003.001, dimensions read off the leader lines — **so the notes were describing an already-solved problem. Withdrawn.** | 2026-08-23 |
| D-198 | **B-69 RESOLVED, AND THE 5 ms WAS DERIVED AGAINST THE WRONG CAPACITANCE. THE ACCESSORY 5 V SETTLE DELAY IS RAISED TO ≥ 10 ms FOR THE FIRST BUILD.** SLVSDK9 specifies **t_SS = 700 µs typical at V_IN 2.5 V, V_OUT 5 V, C_OUT_EFF = 10 µF, no load** — and FBV2-S1-009 quoted the 700 µs without the condition line. `C65` + `C66` are **2 × 22 µF 10 V X7R 0805**, which at 5 V DC bias retain roughly 40–60 % of nominal, giving **C_OUT_EFF ≈ 20 µF — about twice the datasheet condition**. Start-up is dominated by charging that capacitance, so the scaled typical is **≈ 1.4 ms** and the real margin on a 5 ms wait is **≈ 3.5×, not 7×**; the datasheet publishes **no maximum**. **10 ms restores ~7×, costs nothing — it is a firmware constant that runs once per accessory insertion behind an MX-4 delay that already spends 5 ms — and is to be MEASURED at first article and reduced if desired. No PGOOD IC is added.** The FBV2-S1-009 argument still holds and is what makes the measurement meaningful: **the load switch is OFF during boost start-up, so the converter starts into a known board capacitance, never into an unknown hot-plugged accessory.** | 2026-08-23 |
| D-199 | **SIX MISSING MPNs ADDED AND TWO UNDOCUMENTED PLACEHOLDERS RESOLVED.** `D9` → **`PMEG2010AEH,115`** (Nexperia) and `Q4`/`Q6`/`Q7`/`Q8`/`Q9` → **`BSS138LT1G`** (onsemi); the schematic previously carried only the generic type name, which **D-096 does not accept as a selection**. **Every active and every connector in the design now carries an exact MPN — zero missing.** **`R68` is a 0 Ω DNP bypass ACROSS `SW9`, the hard power switch — fitting it wires the unit permanently ON and DEFEATS THE ONE PROVISION THAT LETS A USER POWER DOWN A HUNG OR UNFLASHED BOARD.** It arrived from Beta-DM with no note at all and is now marked **DNP AND IT MUST STAY DNP**, bench characterisation only. **`C21`/`C22` are DEAD PADS** — DNP with one terminal deliberately no-connect flagged, so fitting them does nothing; reserved 0603 rework pads by the USB block, usable only by cutting a trace. Documented, and flagged as deletion candidates at placement. **After this task there are 16 DNP parts and ZERO unexplained DNP.** | 2026-08-23 |
| D-200 | **STALE REGISTER ENTRIES CLOSED ON EVIDENCE — P-01, P-04, B-45, B-49, B-51, B-53 — AND B-03 IS THE REMAINING FOOTPRINT GATE.** **P-01 is stale:** the LTC4368-1 + dual back-to-back FET path is fully represented and measured in the netlist, and FBV2-A1 passed on 2026-08-22. **P-04 is stale:** the IC, crystal, matching network, `FXC.46.52.0075X.B.dg` antenna, `J7`, 3.3 V supply and the preserved 5 V fallback all exist — and after D-192 the IC is actually fitted. **B-45 is stale:** `R61`/`R62` 100 Ω plus two TVS channels landed at FBV2-S1-009. **B-53 is stale:** decided by D-131. **B-03 REMAINS OPEN AND IS AN EXIT-GATE FAILURE: 15 of 28 critical footprints are manufacturer-drawing verified with a cited document number and revision; EIGHT are traceable to a vendor part but have NOT been read against a drawing** — `ESP32-S3-WROOM-1`, GCT `USB4105-xx-A`, JST `ACH BM02B-ACHSS-GAN-ETF`, JST `PH B2B-PH-K`, `PTS645Sx43SMTR92`, `SW_SPDT_CK_JS102011SAQN`, the MAX98357A `TQFN-16-1EP EP1.23x1.23`, and `Crystal_SMD_3225-4Pin`. **The standing instruction forbids calling those verified because the library name looks right.** They do not block placement — pin count, pitch and package identity are fixed — but they must be read before fabrication release. **`U11` BQ25185 WAS verified in this task** against TI's `DLH0010A` EXAMPLE BOARD LAYOUT, drawing 4226298/A 10/2020: pads 10 × (0.2 × 0.5), **pitch 8 × (0.4)**, **exposed pad (0.9) × (1.5)**. **B-70 and B-71 are OPENED** — `L5`/`L6` 39 nH NFC EMC inductors have no MPN at all, and only 7 of 46 unique MPNs carry an LCSC code, so the JLC Basic/Extended split and the assembly quote cannot be produced. | 2026-08-23 |

| D-201 | **B-03 CLOSED — ALL EIGHT REMAINING FOOTPRINTS PROMOTED TO TIER 1, AND THE ONE THAT LOOKED BROKEN WAS NOT.** Every one was compared **dimension by dimension** against a retrieved manufacturer drawing; **none was promoted on the strength of its name.** ESP32-S3-WROOM-1 (Espressif v1.8 Fig. 11-1: 40 lands 1.5 × 0.9 at 1.27, row span 17.5, nine 0.9 × 0.9 paste apertures over a 3.9 × 3.9 land with 12 vias) · GCT USB4105 (span 8.64; 12 × 1.15, 4 × 0.60, 8 × 0.30 at 0.50; 2 × Ø0.65 NPTH) · JST ACH (1.2 pitch, 0.85 land, 3.5 MP span) · JST PH (2.00 ± 0.05 pitch, hole **Ø0.7 +0.1/−0** — the library's 0.75 drill sits **mid-window**) · C&K PTS645 G-Type (pads 1.55 × 1.3 at (±3.975, ±2.25) vs the library's (±3.98, ±2.25) — **exact**) · C&K JS102011SAQN · **`Y1`** (see D-202) · **`U5` MAX98357A: outline 21-0136 lists `T1633-5` EP as 1.50/1.60/1.70 while the land is 1.23 — that looked like a footprint contradicting its own citation on a thermal pad. Maxim land pattern 90-0032 Rev E dissolves it: the drawing is issued for PKG CODES [T1633-5], [T1633-5C] AND [T1633-7C] TOGETHER and specifies ONE land for all three — EP 1.23 × 1.23, pads 0.80 × 0.30, pitch 0.50, centreline span 2.85. So the land does not depend on which EP variant the part carries.** Against the library: EP **exact**, pitch **exact**, inner pad edge **exact at 1.025**, pad centre +0.0125 (inside the drawing's own ±0.02), length +0.025, width −0.05. **NO PROJECT-LOCAL FOOTPRINT WAS CREATED** — both deviations are ≤ 0.05 mm, IPC-7351B compliant and on the safe side. **The right outcome of a verification is sometimes "already correct" — but only after the drawing is read.** | 2026-08-23 |
| D-202 | **`Y1` LOCKED, NOT PROPOSED — AND ITS LAND IS EXACT.** Yajingxin **`TXM27.12M0004322DBBDO00T`**, LCSC **`C362365`, 3,421 in stock live on 2026-08-23** (D-096). Data sheet read: SMD3225-4P, **27.120000 MHz fundamental, CL 10 pF, ESR 30 Ω max, drive level 100 µW max, ±10 ppm at 25 °C, ±20 ppm over −40…+85 °C, ageing ±5 ppm/year**. **Total ±30 ppm against the ISO/IEC 14443 carrier requirement of ±516 ppm** — better than 17× margin. **Suggested Layout: pads 1.4 × 1.2, column gap 0.8, row gap 0.5 → centres (±1.10, ±0.85); `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` is 1.4 × 1.2 at (±1.10, ±0.85) — EXACT MATCH.** Netlist confirms pins 1/3 = `NFC_XOUT`/`NFC_XIN`, pins 2/4 = GND, matching the drawing's connection diagram. | 2026-08-23 |
| D-203 | **B-63 CLOSED — THE MICROPHONE ACOUSTIC PORT IS NOW DRAWN, NOT DESCRIBED.** The footprint's own `descr` said the port was *"NOT PART OF THIS FOOTPRINT … an FBV2-S2 / PCB-stage item."* **A port that lives in a sentence is a port that gets forgotten at placement.** Added: **Ø1.05 mm NPTH** concentric with pad 4 — **the diameter is NOT invented, it is the INNER DIAMETER of the manufacturer drawing's own pad-4 GND ring (ID 1.05 / OD 1.65)**, i.e. the part's own port aperture; **paste pullback** — pad 4 loses `F.Paste` entirely and gets a separate **annular aperture ID 1.25 / OD 1.65**, pulled back **0.10 mm** from the copper inner edge so solder cannot wick into the port (**the 0.10 mm is a DECLARED STENCIL CHOICE, not a drawing dimension**, and the footprint says so), ≈ 72 % coverage; **keepout** — dashed `B.Fab` circle plus a `User.Comments` legend, no copper/vias/silk/mask step on **either** face; **orientation** — bottom-port, so **the acoustic path leaves on the BOTTOM face** and the enclosure aperture belongs there, not on the component face (**M-14**). Re-loaded through KiCad's own `pcbnew` parser to confirm validity. | 2026-08-23 |
| D-204 | **B-70 CLOSED — `L5`/`L6` = MURATA `LQW18AN39NG80D`, AND THE DCR IS A FIRST-ORDER TERM.** LCSC **`C2042966`, 270 in stock**. 0603/1608 wire-wound, **39 nH ±2 % (G), Rdc 0.20 Ω max, SRF 3000 MHz min, Q 37 min, 1 A rated.** **NOT LOCKED FROM HEADLINE SPECS — checked against D-134:** (1) SRF is **74×** the 40.68 MHz third harmonic and **149×** the 20.1 MHz EMC corner, so it is a pure inductor across the band; (2) X_L = **3.32 Ω** at 13.56 MHz, the reactance D-134 already re-solved against; (3) **THE DCR IS NOT NEGLIGIBLE: `R_q` is only 1.1 Ω per arm, so 0.20 Ω max gives 1.30 Ω and the network Q falls 25.3 → ≈ 21.4, about −15 %.** That moves **further into** the safe, under-driven side D-134 deliberately chose — not a stress condition — but **the antenna MUST be bench-tuned with this exact part fitted.** **If field strength is short at first article the first lever is `R_q` 1.1 Ω → 0.9 Ω, NOT a change to 39 nH**; D-134 forbids moving `L` without re-running the whole matching calculation and that has not been done. (4) Coil current ≈ 187 mA against a 1 A rating, > 5×. | 2026-08-23 |
| D-205 | **B-54 CLOSED AS AN ALLOCATION — 100 mA FROM `+3V3` WITH THE FIELD ON, AND THE ABS-MAX WAS DELIBERATELY NOT USED.** DS12484 Rev 3 was finally retrieved through a **mikroe.com mirror** after st.com timed out repeatedly. **Table 121 (V_DD = 3.3 V): `I_PD` 0.8 µA typ / 2.5 µA max; `I_WU` 3.0 / 7.0 µA; `I_RD` 7.5 mA max; `I_AL` all active 16 typ / 23 max; `I_AL-AM` all active with AM 17 typ / 26 max; `I_AL1` single RX 11 / 16; `R_RFO` 1.7 Ω typ / 4.0 Ω max.** **Table 118's `I_VDD_LDO` = 350 mA and `I_VDD_EXT` = 500 mA are ABSOLUTE MAXIMUM RATINGS and are NOT used as operating currents.** Allocation = **`I_AL-AM` max 26 mA (IC, all blocks, AM) + ≈ 60 mA (RF driver into D-134's actual first-build network) = 86 mA → allocate 100 mA** with 16 % headroom. **This replaces D-130's ≤ 150 mA estimate and vindicates it.** **TPS63020: D-092's enforced 1.16–1.32 A becomes 1.26–1.42 A = 63–71 % of 2 A** (was 66–74 %). MX-1 still keeps the field off during LoRa TX, MX-2 still caps the speaker, and the IR emitter and RGB status light sit inside the headroom. **BINDING GUARD RAIL: D-134 records that `C_s` 300 pF → 270 pF gives ≈ 257 mA of driver current, which this allocation DOES NOT COVER. If bench tuning proposes 270 pF, the rail budget must be re-run first.** | 2026-08-23 |
| D-206 | **B-71 CLOSED — EVERY PART HAS A FIRST-FIVE ROUTE TO THE BOARD, AND SIX SUBSTITUTION TRAPS WERE CAUGHT.** All **46 unique MPNs** classified A–F in [`assembly/FIRST_FIVE_ASSEMBLY_PLAN.md`](assembly/FIRST_FIVE_ASSEMBLY_PLAN.md) against **live JLCPCB parts-API state read on 2026-08-23** (D-096); **65 `LCSC` fields written into the schematic**, so the BOM is exportable. **Two parts are JLC Basic; ten have stock short of the first-five need; one is not in the library at all.** **All are handled by CONSIGNMENT, which keeps them MACHINE-PLACED** — the sharpest case is `U2`/`U3`/`U23`, **fifteen TSSOP-24 at 0.65 mm pitch against ONE in stock**. **Two through-hole parts per board are hand-soldered (`J5`, `D1`); ZERO fine-pitch or QFN parts are hand-placed.** **`J1` IMPROVES: JLC carries the genuine Hirose `FH69-50S-0.5SH` with 1,072 in stock, so it is machine-placed after all** — B-47's single-source finding stands, but it never implied JLC could not place it. **THE TRAPS — a loose keyword search returns a plausible WRONG part more often than it returns nothing:** `BAT54W,115` for **`BAT54WS,115`** (~~single diode vs series pair~~ — **CORRECTED BY D-211: `BAT54WS` IS NOT A SERIES PAIR; the trap is real but the reason is a SOT-323 vs SOD-323 FOOTPRINT mismatch**) · G-Switch `GT-TC089A-H043-L1` for **C&K `PTS645SM43SMTR92LFS`** (35 placements) · FUXINSEMI `SD103AWS` for **onsemi `NSR0240HT1G`** · LRC `LBSS138LT1G` for **onsemi `BSS138LT1G`** (which has 762,522 in stock) · KOHERelec `SPM4030-1R0M` for **Würth `74438357010`** · a VBsemi clone for **onsemi `NTMD4820NR2G`, the battery reverse-polarity pass FETs**. **Each is now recorded in the schematic symbol itself.** ~~**NO SUBSTITUTE WAS ADOPTED** — `BAT54WS-7-F` and `0466005.NRHF` are candidates awaiting sign-off.~~ **SUPERSEDED 2026-08-23: both were signed off and adopted — D-210 and D-211.** | 2026-08-23 |
| D-207 | **TWO MPN STRINGS WERE WRONG IN A WAY THAT WOULD HAVE STALLED THE ORDER.** `J4` and `J6` are the same JST PH 2-pin header but carried **two different MPN strings** — `J4` the `(LF)(SN)` plating suffix, `J6` the bare order code. **Not cosmetic: the bare code is LCSC `C20504437` with STOCK 0, while `B2B-PH-K-S(LF)(SN)` is `C131337` with 378,913 in stock.** `J7` had the identical fault: `BM02B-ACHSS-GAN-ETF` → `C20088622`, stock 0; **`BM02B-ACHSS-GAN-ETF(LF)(SN)` → `C5118738`, 16,260**. Both normalised to the stocked string; `L2`/`L4` carried two spellings of "Würth" and were normalised too. **A BOM that produces two lines for one part, one of which cannot be filled, is a BOM that stalls at the quote stage.** | 2026-08-23 |
| D-208 | **EIGHT DNP PARTS STILL HAD NO RECORDED REASON. ALL EIGHT NOW DO; THE DESIGN HAS ZERO UNEXPLAINED DNP.** After seven consecutive sheets of load-bearing inherited `DNP`, an unexplained one is the single thing this project cannot afford to leave lying around. **`U13`, `L2`, `R44`, `R45`, `C34`, `C35` are the NFC 5 V BOOST BRANCH** — TPS61023 + 1 µH + feedback divider + output caps producing `NFC_5V_PA_PENDING` from `BQ25185_SYS`. **DNP is CORRECT**: D-055/D-056 select `NFC_SUPPLY` = `+3V3` through `R106` (fitted) and `R107` (DNP) is the mutually exclusive 5 V link. **The branch is PRESERVED, not abandoned** — a no-respin escape under D-049 if the 3.3 V field measures short. **NEVER FIT `R106` AND `R107` TOGETHER.** Traced through the netlist and confirmed **not** to be an inherited oversight. **`R119`** is the BMI270 alternate-address strap; `R118` (fitted, 0 Ω to GND) holds the strap low so the IMU answers at **0x68** — **`R118` and `R119` are mutually exclusive; fitting both shorts `+3V3` to GND through two 0 Ω links.** **`R112`** links display `SDO` to the shared `SPI_A_MISO` and is DNP so the panel **cannot** drive the bus the microSD reads on; fitting it is a bring-up provision and **must not** be done while **MX-8** is relied on. | 2026-08-23 |
| D-209 | **O-8 CLOSED — 915 MHz EXTERNAL ANTENNA LOCKED, AND THE HEADLINE GAIN IS NOT THE OPERATING GAIN.** **Taoglas `TI.92.2113`**, verified against data sheet **SPE-19-8-076/A**: **902–928 MHz**, **terminal-mount DIPOLE**, **hinged SMA(M)** as standard, **198 ±3.3 mm × Ø13 mm**, TPEE, 22.5 g, 50 Ω linear omni, **max input power 1 W**, −40…+85 °C, efficiency **80.01 % straight / 73.20 % bent**. Taoglas' own words: it *"performs very well in free space, making it an ideal solution in areas where there may be no ground plane"* — exactly the CTO's stated reason. **Every expectation in the ruling checks out.** Two things worth saying anyway: **the marketed "2 dBi" is the BENT-CONFIGURATION PEAK** — the table gives **peak 1.21 dBi straight / 2.14 dBi bent and AVERAGE gain NEGATIVE in both** (−0.97 / −1.35 dB), so **budget the link with the average**; and the mating chain is right end to end — module IPEX/MHF1 → Amphenol AMC right-angle → RG-178 150 mm → **SMA female** bulkhead → **SMA male** antenna, with **+22 dBm into a 1 W rating, better than 6×**. **No hardware or schematic change was required.** | 2026-08-23 |

| D-210 | **`F1` PROCUREMENT ALTERNATIVE APPROVED AND ADOPTED: Littelfuse `0466005.NR` -> `0466005.NRHF`, LCSC `C57525`.** Re-verified live one final time under **D-096** on 2026-08-23 through the JLCPCB parts API: **29,328 in stock, JLC EXTENDED, 1206, 5 A, 32 VAC / 32 VDC, 50 A interrupting, fast acting.** The `.NR` code (`C187597`) is **stock 0**, and **the two LCSC records carry a character-for-character identical parametric string** — the distributor's own data does not distinguish them electrically at all. The `HF` suffix is the **manufacturer's halogen-free ordering option** on the same **466 / Nano2** family. **THIS IS A PROCUREMENT / ORDER-CODE IMPROVEMENT, NOT AN ELECTRICAL REDESIGN:** same footprint (`Fuse:Fuse_1206_3216Metric`), same rating, same function, and **`F1` connectivity and footprint are UNCHANGED — not one net, pin, wire, label or junction was touched.** **Assembly consequence: `F1` moves from class C (consign) to class B (JLC-sourced, MACHINE-PLACED).** Schematic `MPN`, `LCSC` and sourcing note updated; sourcing ledger, assembly plan and population matrix updated. | 2026-08-23 |
| D-211 | **`D10`/`D11`/`D12` PROCUREMENT ALTERNATIVE APPROVED AND ADOPTED: Diodes Incorporated `BAT54WS-7-F`, LCSC `C124205` — AND THE "SERIES PAIR" SOURCING ERROR IS CORRECTED PROGRAMME-WIDE.** Verified live under D-096 on 2026-08-23: **46,819 in stock, JLC EXTENDED, SOD-323, 1 INDEPENDENT diode, 30 V, 100 mA continuous, 600 mA surge, V_F 1 V max at 100 mA, I_R 2 uA at 25 V.** **THE CORRECTION: `BAT54WS` IS NOT A SERIES PAIR, AND D-206 SAID IT WAS.** Three independent proofs: **SOD-323 is a TWO-TERMINAL package** and a series pair needs three; **every `BAT54WS` in the LCSC library, from EIGHT manufacturers, is catalogued "1 Independent"**; and **AQROOT's own schematic never used a pair** — `D10`, `D11` and `D12` are each one two-pin `Device:D_Schottky` on a two-pad `Diode_SMD:D_SOD-323`, with **`D10` and `D11` forming the ratiometric matched-function pair as TWO SEPARATE COMPONENTS**. **So `BAT54WS-7-F` matches the ACTUAL architecture exactly.** **THE REAL REJECTION CRITERION for any alternate is: correct independent-diode topology · SOD-323 footprint · adequate V_F / leakage / current · matched type for `D10`/`D11` · live sourcing.** Nexperia `BAT54W,115` (`C8657`) **stays rejected, for the right reason: it is SOT-323 (SC-70), a FOOTPRINT mismatch — NOT because of diode count**, and it has 5 in stock against a need of 15. **ELECTRICAL VERIFICATION — NO MATERIAL MISMATCH FOUND.** `D10`/`D11` bridge: each leg is 2.2 M + 2.2 M = **4.4 MΩ at ~1.1 uA**, six orders below the 100 mA rating; the comparison is `INA+ - INA- = (BAT_RAW + V_F11 - V_F10)/2`, so **the absolute drop CANCELS and only DeltaV_F survives** — the trip point is structurally V_F- and supply-independent, and matching **improves** because both diodes become the same MPN on one order line; reverse drain is capped by the 4.4 MΩ at **<= ~1 uA (~8.8 mAh/year)** against 30 V V_RRM at 4.2 V stress. `D12` recovery branch: **8.36 mA nominal / 7.93-8.80 mA over 4.75-5.25 V** and a **~16.6 mA worst-case single-fault ceiling against 100 mA continuous — 6x margin**, 36x against the 600 mA surge, ~7 mW dissipated, 7x reverse margin; **re-solving D-105 with this part's V_F gives 7.9-8.9 mA, still inside the accepted 5-10 mA band, so D-105 needs NO revision.** **Assembly consequence: class D (not in the library) -> class B (JLC-sourced, MACHINE-PLACED). CLASS D IS NOW EMPTY.** | 2026-08-23 |
| D-212 | **PRE-FLOORPLAN MECHANICAL AUTHORITY RECONCILED. `MECHANICAL_INTERFACE_SPEC.md` NOW CONTAINS NO CONFLICTING CURRENT REQUIREMENT.** Six stale contradictions were corrected and one was traced and **deliberately NOT resolved by preference**. **(1) NFC ZONE: 45 x 45 -> 48 x 48 mm MINIMUM CLEAR REGION, LOCKED.** The 48 mm figure was ruled at FBV2-S1-004B (D-127/D-128/D-131) and already appeared in this document's own NFC banner; **four places had never been updated, including the machine-readable block a guard script parses.** No enclosure external-size change. **(2) DISPLAY CONNECTOR: every current claim that `J1` uses the FH12/FH52E standard land pattern, that `FH52E` is a drop-in second source, or that mating/land-pattern equivalence was proven, is REMOVED.** Current truth: **FH69 DEDICATED footprint · FH52E NOT drop-in · SINGLE-SOURCE connector architecture · the genuine Hirose `FH69-50S-0.5SH` IS JLC machine-placeable · re-check stock before ordering** (B-47 -> D-194; D-206/D-207). **(3) `J1` IS NOT MANUAL ASSEMBLY** — M-13 and the header both said so; **exactly TWO parts are manual per board, `J5` and `D1`.** **(4) 915 SMA <-> IR SPACING: BOTH RULES ARE CURRENT — NEITHER SUPERSEDED THE OTHER.** The >=15 mm rule is FBV2-MECH-001, 2026-08-22, **centre-to-centre**, written against a generic whip shadowing the emitter cone; the >=8 mm rule is **D-120**, 2026-08-23, **edge-to-edge, SMA body to IR aperture**. **The latest ruling to touch this, M-13 (FBV2-S2-001), states BOTH IN THE SAME SENTENCE, written after D-120 existed and with the Amphenol bulkhead already selected — so 15 mm was RE-ASSERTED, not made stale.** The actual defect was that **neither figure said what it was measured between**; both now carry an explicit datum in a new **section 8.1 authority trace**. Consistency check: on a ~9.5-11 mm SMA hex body and a ~5.5-6.0 mm aperture, **8 mm edge-to-edge implies ~15.5-16.5 mm centre-to-centre**, so the two agree and **8 mm edge-to-edge is the binding one — satisfy whichever is larger.** The Amphenol body OD is **CAD-TO-VERIFY**; **B-52 stays OPEN, no CAD was created.** **(5) SPEAKER Z COLUMN: 4.0 -> 3.0 mm, total 13.6 -> 12.6 mm (10.4 spare)** — D-148 locked Ø20 x 3.0 mm and said it released 1 mm of Z, but the derived column in the same document still summed 4.0. **(6) SECTION 4.1 CONTENT LIST: "26 to 20 pins" -> 24 contacts in 2 x 12 at 2.54 mm (D-081/D-083), and "removes the RGB nets" -> a FRONT RGB STATUS LIGHT `D13` WAS ADDED (D-167).** IR receiver naming corrected to name the locked `TSOP38238` first and the `TSOP38438` as fallback. Checked and found **already consistent**: Harwin vs Samtec, display dimensions and FPC, NFC `.A.dg` vs `.B.dg`, 433 placement, 915 pigtail, buttons/HOME, battery, PCB target/max, community aperture and load path. **Companion handoff created: `mechanical/P1_FLOORPLAN_INPUTS.md`, 120 numbered constraints marked LOCKED / TARGET / CAD-TO-VERIFY, with NO invented coordinates.** **NO CAD. NO PCB CHANGE. NO ENCLOSURE CHANGE.** | 2026-08-23 |
| D-213 | **SIX PRE-FLOORPLAN BLOCKERS SURFACED FOR RULING — NOT DECIDED, NOT DESIGNED AROUND.** **O-1 MICROPHONE BOARD FACE:** the enclosure aperture is on the FRONT face while M-14 says the acoustic path leaves the PCB's BOTTOM face; both hold **only** if `MK1` sits on the copper face pointing away from the front shell, and **no floorplan has ever assigned that side.** **O-2 THE REAR FACE IS OVER-CONSTRAINED BY ~8 mm — IMPOSSIBLE SIMULTANEOUS KEEPOUTS:** rear Y needs battery **75** + NFC clear zone **48** + speaker **Ø20** + the **>=20 mm** speaker-to-loop separation = **163 mm against a 155 mm cavity**, and moving the speaker beside the battery fails too (60 mm battery in a 75.0 mm cavity leaves **7.5 mm per side** against a Ø20 driver) — **before** the 5 mm NFC metal keepout, the shell lip and the bosses. **One of {speaker-to-loop separation, speaker location or face, battery Y, NFC zone position} must give, and all four are currently recorded as binding.** **O-3 MID-SPAN BOSS vs THE GROWN NFC ZONE:** the zone grew 45 -> 48 mm with a 5 mm metal keepout, so a boss nominally at Y ~ 100 now sits on or inside its lower boundary — the zone is LOCKED, the boss is TARGET; confirm the boss may move to **Y <= ~95**. **O-4 microSD <-> USB-C SEPARATION IS NOT PHYSICALLY ACHIEVABLE:** recorded as **>=8 mm centre-to-centre**, but the bodies are ~14.0 and ~9.2 mm wide, so centres cannot be closer than **~11.6 mm**, and a rib between the apertures pushes that to **~13.6 mm** — the figure reads as an **edge-to-edge** number written into a centre-to-centre row. **O-5 UNNECESSARY 915 MHz CABLE LENGTH:** `095-902-568-150` is a **150 mm** assembly in a **155 mm** cavity needing a >=5 mm bend radius and a >=15 mm service loop while not crossing the IR path, through space already claimed by the 433 flex, the NFC pair and the battery; a shorter length in the same Amphenol series would remove a routing problem at **no electrical cost** (loss is already ~0.4 dB). **NO SUBSTITUTION IS PROPOSED — D-195 locked this MPN.** **O-6 THE INTERNAL ANTENNA STORAGE CHANNEL CANNOT HOLD THE LOCKED 915 ANTENNA:** section 8 reserves a left-wall channel *sized for the stowed whip*, but the locked whip is Taoglas **`TI.92.2113`, 198 +/-3.3 mm x Ø13 mm** and the cavity's longest internal diagonal is **~172 mm — it does not fit in any orientation**, and that same left wall is the LOCKED mount region for the 433 MHz flex. **Withdrawing the storage requirement would free the entire left wall — the largest single simplification available before floorplanning.** **Checked and found clean:** connector orientation (`J7` top-entry, `J5` horizontal, `J1` right-angle backflip), FPC bend (6 mm corridor against >=3 mm needed, 30 mm free tail), antenna cable crossing rules, and the 152 mm speaker lead. | 2026-08-23 |

| D-214 | **P1-A: PCB SIDE CONVENTION LOCKED, AND THE MICROPHONE FACE IS RESOLVED (O-1 CLOSED). `F.Cu` = FRONT / DISPLAY / BUTTON side; `B.Cu` = REAR / BATTERY side.** `MK1` PUI `DMM-4026-B-I2S-R` is placed **on B.Cu**, a bottom-port part that **listens FORWARD through the PCB**; the **Ø1.05 mm NPTH stays concentric with pad 4** (carried by the footprint itself since D-203); the **front shell aperture and gasket sit on the opposite, F.Cu side**. Implemented at (3.000, 50.000) in the P1 datum: **1.21 mm clear of the LiPo envelope**, **67.42 mm from the speaker on the opposite face** against a >= 60 mm rule, and below the display bottom edge so the gasket never meets the panel. **The apparent front-face / bottom-face contradiction was a nomenclature collision between the ENCLOSURE face and the PCB copper face, not a requirement conflict.** | 2026-08-24 |
| D-215 | **P1-B: THE REAR IS NOT OVER-CONSTRAINED. O-2 IS CLOSED AS A FALSE DIMENSIONAL CONFLICT.** The 20 mm speaker-to-loop separation must **not** be added to the stack: **if the battery lies between the NFC zone and the speaker, its own 75 mm extent already creates the separation.** Locked Y architecture, top to bottom: **NFC -> BATTERY -> SPEAKER**, occupying **48 + 75 + 20 = 143 mm inside the 155 mm cavity, leaving ~12 mm of real gaps and tolerance.** Implemented with NFC at board Y 102.0-150.0, battery Y 23.5-98.5, speaker Y 1.0-21.0: **zero NFC/battery overlap with a 3.50 mm gap**, **2.50 mm battery-to-speaker gap**, **81.00 mm from the speaker to the loop perimeter**, speaker **rear-firing in the bottom band biased lower-right**, NFC clear region a full **48 x 48**, battery **60 x 75 x 8.0 not reduced**. **No attempt was made to place the speaker beside the 60 mm battery in the 75 mm cavity.** | 2026-08-24 |
| D-216 | **MID-SPAN BOSSES: SIX M2 REMAINS THE TARGET, BUT ONLY THREE POSITIONS CLOSE ON THE 70 x 148 OUTLINE.** O-3 approved: exact Y is not locked and Y = 95 was not forced. A search over the whole board with the display, battery, NFC, speaker, 433, aperture and component keep-outs applied finds **three legal M2 positions, and only at a Ø4.5 mm keep-out rather than Ø6.0**: **BOSS1 (3.500, 44.000), BOSS2 (59.500, 145.000), BOSS3 (40.000, 12.000)**. **The reason is arithmetic, not preference:** a boss is a through-board feature, the display owns X 3.39-59.93 above Y 55, the battery owns X 6.00-66.00 from Y 23.5 to 98.5, the NFC zone owns X 0.50-48.50 above Y 102 and forbids screws outright — **so no 6 mm-wide side strip exists anywhere, and both top corners are inside the NFC zone.** No boss passes through the NFC region, the 433 flex region, the speaker cavity or the connector load path. **THREE M2 FIXINGS WILL NOT CONTROL FLEX ON A 148 mm SPAN WITH A BATTERY BEHIND IT — this is escalated, not accepted.** | 2026-08-24 |
| D-217 | **USB-C / microSD SPACING RE-BASED ON A MEASURABLE DATUM (O-4 CLOSED). The nonsensical >= 8 mm CENTRE-TO-CENTRE rule is REPLACED by >= 8 mm BODY EDGE-TO-EDGE.** Implemented against verified footprint courtyards rather than the approximate widths: microSD `J2` body X 7.00-21.00, USB-C `J3` body X 37.40-46.60, **body edge-to-edge 16.40 mm and centre-to-centre 28.00 mm** — twice the rule. microSD **left** of USB-C; USB-C **7.00 mm right of board centre**; independent shell apertures; **~22 mm of card insertion travel reserved outside the shell, clear of the USB plug envelope**; shell material between the two openings. | 2026-08-24 |
| D-218 | **915 MHz PIGTAIL SUPERSEDED: `095-902-568-150` -> Amphenol RF `095-902-568-100`, RE-VERIFIED LIVE UNDER D-096 — AND THE P1 GEOMETRY PROVES IT DOES NOT REACH.** Distributor record read live 2026-08-24: **Part Status ACTIVE**, Connector A **SMA jack, panel-mount bulkhead, front-side nut**, Connector B **U.FL (UMCC) / AMC plug, right angle, free hanging**, **RG-178, 50 Ω, 100.00 mm, 6 GHz**; IP67 carried from the series data (D-195) because the manufacturer page refuses to serve here and was not re-read. **PROCUREMENT NOTE: 0 in stock, 12-week factory lead time, no JLCPCB listing — a first-five schedule risk on its own.** **THE MECHANICAL FINDING IS THE IMPORTANT ONE.** Every part taller than ~1.2 mm is excluded from the upper half of the board — front is display shadow (F.Cu <= 0.8 mm), rear is battery (B.Cu <= 1.2 mm) then NFC clear zone (B.Cu <= 1.0 mm, no shielding cans) — and the one free strip above the battery is 16.5 mm wide and already carries `J5`'s 31.6 mm through-hole field. **A 15.89 x 21.34 x 3.5 mm radio module fits nowhere above Y ~ 55, so `U8` sits at the bottom rear and the routed run to a top-panel SMA is ~190 mm: 100 mm is SHORT BY ~90 mm and even the superseded 150 mm is SHORT BY ~40 mm.** **And length alone cannot fix it:** the SMA is locked to the top-edge LEFT half and the NFC 48 x 48 clear zone owns the whole upper-left, so any coax from the bottom either crosses the NFC zone or runs inside the 5 mm metal keep-out. **THIS IS THE ONE CRITERION THAT FAILS THE FBV2-P1 GATE.** | 2026-08-24 |
| D-219 | **INTERNAL 915 MHz WHIP STORAGE DELETED (O-6 CLOSED).** The Taoglas **`TI.92.2113`** remains **LOCKED** as the first-five external antenna, is **removable**, and is **carried separately when detached**. Every current requirement for an internal storage channel, a left-side holder sized for the stowed whip, or anything forcing the **198 +/-3.3 mm x Ø13 mm** antenna inside a cavity whose longest internal diagonal is **~172 mm**, is **DELETED from the mechanical authority**. **The antenna MPN is unchanged.** The freed LEFT internal wall is now assigned to the **433 MHz flex (board Y 1.5-48.5), its cable and service access** — which restores the D-118 *LEFT / LOWER-SIDE* placement exactly as locked, and lets the 433 lead use ~36 mm of its 100 mm length. | 2026-08-24 |
| D-220 | **FBV2-P1 FLOORPLAN BUILT; THE GATE DOES NOT PASS ON ONE CRITERION.** **Outline 70.000 x 148.000 x 1.6 mm — the TARGET, not the 72 x 152 maximum**, plain rectangle, 2.5 mm to the cavity wall in X and 3.5 mm in Y rather than the 1.5 mm minimum. **Datum: origin at the LOWER-LEFT board corner, X right, Y up; `Y_kicad = 148.000 - Y_doc`.** The board was **rebuilt from the current nine-sheet schematic**: the pre-P1 file stripped to its header, layer stack, `general` and `setup` so the design rules survive byte for byte, **all Beta-DM footprints, tracks, vias, zones and graphics removed**, then **321 footprints re-created one per schematic component** with references and exact verified footprints preserved, **224 nets over 991 pads** applied, plus the outline, **13 named mechanical regions, 4 copper rule areas and 3 M2 NPTH bosses**. **F.Cu 120 / B.Cu 201.** **ZERO placement conflicts** on a side-aware pairwise review of all 321 courtyards — no courtyard overlap, no out-of-board part, no boss intrusion, no display/battery/NFC height violation, no B.Cu part in the sealed speaker cavity, no lead protruding into the battery, NFC or speaker volume. Measured: **FPC margin 15.8 mm**, **USB/SD body gap 16.40 mm**, **IR TX-RX 15.00 mm**, **SMA-IR 39.55 mm centre and 31.05 mm edge**, **mic-speaker 67.42 mm**, **NFC 48 x 48 with zero battery overlap**. **ERC 27 / 0 errors, histogram byte-identical; schematic connectivity UNCHANGED; ZERO tracks, ZERO vias, ZERO pours; 499 unrouted connections, which is the correct P1 state.** `netclass_probe` PASS; `fork_equivalence` now reports the v2 PCB as changed, **which is the intended outcome of P1 and not a failure** — Beta-DM is confirmed untouched. **NO PROGRESS AWARDED: Full Beta v2 stays at 68 %.** | 2026-08-24 |
| D-221 | **FOUR NEW ITEMS SURFACED BY THE FLOORPLAN, NOT DECIDED.** **(1) THE DISPLAY CANNOT BE CENTRED ON THE ENCLOSURE.** `J5` needs 9.2 mm of board width on the right and cannot sit below the battery, so it must occupy Y 105-137 — beside the display band — and the panel is therefore **3.34 mm LEFT of the board and enclosure centreline**. Widening the board to 72 mm does not fix it. **This is visible on the front face.** **(2) `MK1`'s GND ring pad FAILS KiCad 10's padstack validator** — *custom pad shape must resolve to a single polygon*. The footprint is dimensionally correct (D-203) but the ring is drawn as a **stroked circle outline** rather than a filled annulus; it must be re-drawn before fabrication. **(3) The stock `ESP32-S3-WROOM-1` footprint's twelve thermal vias are 0.2 mm, below this board's 0.3 mm minimum-hole rule** — either the rule or the footprint moves at FBV2-P2. **(4) `netclass_probe` was measuring the wrong board:** its expectation listed `LED_A1`...`LED_A4`, which are **Beta-DM** net names; the Full Beta v2 schematic has **one** anode net, `/03_SPI_A_DISPLAY_SD/LED_A`, the net D-111 deliberately added to `LED_BOOST`. It only passed before because the PCB was still Beta-DM's. **The expectation is corrected to the schematic; the guard itself — `LED_BOOST` must never capture the IR transmitter nets — is unchanged and still passes.** **Also recorded as a first-article assembly instruction: `D1` and `U6` are flat-mount leaded parts whose optical axis is normal to the BOARD, so both must be FORMED 90 degrees to look out of the top panel.** | 2026-08-24 |
| D-222 | **FBV2-P1 PASSES. THE 915 MHz FEED CLOSES ON MEASURED GEOMETRY, NOT ON AN ESTIMATE.** Routed path `U8` IPEX (9.00, 16.60) → left rear channel → SMA (5.00, 148.00) = **138.48 mm including bend allowances**, minimum available bend radius **7.42 mm** against the ≥ 5 mm rule, **0.600 mm** clearance at its tightest point to the Ø58 NFC metal exclusion and **ZERO violations** against the 433 flex body, the battery, the speaker cavity, the microSD card-travel volume, the USB aperture, both IR optical regions, the IR barrier, the community recess and `J5`. **`U7` and `U8` are SWAPPED** in the bottom-rear band — the two Ebyte footprints are dimensionally identical so the swap costs **zero plan area**, and it puts the length-critical 915 module beside the only north-south cable channel on the board; the 433 flex still needs only 44 of its 100 mm. **The SMA bulkhead moves from doc x 12.000 to x 5.000**, still top panel / left half per T-2: at x = 12 the bulkhead body is inside the Ø58 exclusion **for every legal NFC centre**, and the move only IMPROVES both SMA↔IR rules. Two crossings exist and are recorded rather than engineered away: the coax passes over `MK1`'s **sealed** lid (a bottom-port MEMS mic whose acoustic path leaves the other face) and the 433 lead crosses the 915 coax once at about (4.5, 21.5) on top of `U8` — **C-6 forbids crossing a radiating ELEMENT, not another cable.** | 2026-08-24 |
| D-223 | **915 PIGTAIL RE-SELECTED: `095-902-568-100` → RF Solutions `CBA-UFLSMA20IP`, 200 mm.** The CTO's own threshold decides it: the measured installed path is **138.48 mm, comfortably ≤ 180 mm**, so the 200 mm assembly locks and the 250 mm Taoglas **`CAB.01034`** is recorded as the FALLBACK ONLY and is not used. Verified live 2026-08-24 under **D-096**: DigiKey 14566928 — **ACTIVE, 296 in stock**, 200.00 mm, **RG-178**, 50 Ω, connector A **U.FL (UMCC) plug, right angle**, connector B **SMA jack, panel-mount bulkhead, front-side nut**; CPC/Farnell RF00982 — **IP67**, 7 in stock, £6.29; manufacturer drawing `CBA-UFLSMAF20IP-1` rev 1 12/11/2015, revised 03/12/2015 — *UFL Right Angle · Waterproof SMA Female Bulkhead Straight · Heatshrink · RG178 Coax cable*. **MATING VERDICT: COMPATIBLE** — `E22-900M22S` carries an **I-PEX MHF1 (IPEX-1)** socket, Hirose **U.FL** and MHF1 are the same 2.0 × 2.0 mm intermateable interface, and the cable's connector A is a U.FL **plug**, the right gender. Far end SMA **female** onto the `TI.92.2113`'s SMA **male** — exactly the D-120 chain. **Feed loss ≈ 0.4 dB** (RG-178 ≈ 1.2–1.5 dB/m × 0.20 m plus two interfaces) against +22 dBm. **Total 200 mm, spare 46.52 mm beyond the mandated 15 mm service loop**, dressed as a shallow serpentine in the reserved `COAX_915_CHANNEL`. **THIS IS ALSO A PROCUREMENT FIX: the superseded Amphenol part was ACTIVE but 0 IN STOCK ON A 12-WEEK FACTORY LEAD (D-218); the replacement is stocked at two distributors today.** | 2026-08-24 |
| D-224 | **NFC GEOMETRY IS NOW CIRCULAR, AND THE CENTRE MOVED. CLEAR Ø48, METAL EXCLUSION Ø58, CENTRE doc (30.800, 124.500)**; the 48 × 48 square is RETAINED but **only as the placement / positioning-tolerance envelope**, never again as the metal-free shape. The centre moved **+6.30 mm in X and −1.50 mm in Y** from (24.500, 126.000), and both components are load-bearing. **+6.30 X IS THE ENTIRE 915 SOLUTION**: the cavity is 75 mm, the Ø58 exclusion is 58 mm and `J5` owns 12.1 mm, so **at most 4.9 mm of coax lane exists and only if the exclusion is pushed as far right as `J5` allows** — it now is, with the loop perimeter **5.490 mm** from `J5`'s copper against a ≥ 5 mm rule. **−1.50 Y buys the SMA its margin** (0.798 mm radial on the Ø10.2 washer, 2.400 mm to the cavity wall; at Y = 126 the bulkhead would have had to sit at x ≤ 4.31). **THE RADIAL CLEARANCE WAS NOT REDUCED**: the superseded metal keep-out was the **58 × 51 rectangle** X −4.5 … 53.5 / Y 97 … 148 and the Ø58 circle is **inscribed in it**, so only the four corners are reclaimed — exactly the instruction. **COST, STATED PLAINLY:** NFC clear ↔ battery 3.50 → **2.00 mm gap, still ZERO overlap so N-5 holds**; battery inside the Ø58 1.50 → **3.00 mm**; `J5` ↔ loop 6.86 → **5.490 mm**. **No screw, boss or shielding can is inside the Ø58, which is what the rule text forbids.** Applied to the PCB regions, the coax check, the boss search, the speaker, battery and 433 checks and every mechanical artefact. | 2026-08-24 |
| D-225 | **DISPLAY OFFSET ACCEPTED AS INTENTIONAL, AND THE DISPLAY Z STACK IS NOT SPENT.** The module sits **3.34 mm LEFT of the board centreline** and that is now recorded design intent, not a defect: the right-side community connector owns real mechanical width, forcing optical centring creates greater mechanical and Z risk, and the front industrial design can balance the left-biased panel against the right-side community-port mass. **The display was NOT raised, the PCB was NOT widened, `J5` was NOT moved for it and the enclosure width did NOT change**; the display/`J1` relationship is unchanged. **THE FBV2-P1-001 RECOMMENDATION TO RAISE THE DISPLAY SUPPORT BY ≈ 3 mm AS THE PRIMARY 915 SOLUTION IS REJECTED AND WITHDRAWN** — the circular NFC geometry closed the feed without spending any of Column A's 9.9 mm of unused Z. **Display Z stack changed: NO.** | 2026-08-24 |
| D-226 | **SIX M2 IS SUPERSEDED, AND SO IS THREE: THIS OUTLINE YIELDS TWO. ESCALATED.** `BOSS1` doc **(40.000, 12.000)**, `BOSS2` doc **(59.000, 145.000)**, both **Ø4.5 mm keep-out, Ø2.2 NPTH**. **Search result: Ø6.0 — ZERO legal sites; Ø4.5 — TWO.** The arithmetic is not a preference: a boss must clear BOTH faces, the display owns X 3.39 … 59.93 for Y 55.04 … 140.00 on the front and the battery owns X 6.00 … 66.00 for Y 23.50 … 98.50 on the rear, which leaves a **3.39 mm left sliver and a 4.00 mm right sliver, both narrower than a Ø4.5 keep-out**; only the 23.5 mm bottom band and the 8 mm top band can host a through-board screw at all, and each yields exactly one site. **BOTH of FBV2-P1-001's other positions were withdrawn FOR CAUSE**: its `BOSS1` (3.5, 44.0) is inside the mandatory 915 coax channel, and its `BOSS2` (59.5, 145.0) **overlapped the mandatory opaque IR barrier and was never legal** — corrected to (59.0, 145.0) with the barrier **widened 3.0 → 5.0 mm** to fill the whole inter-window gap, so barrier and boss are now one moulded feature. **Ø4.5 IS JUSTIFIED, NOT INFLATED: the moulded M2 boss OD is 4.0 mm, so Ø4.5 is that plus 0.25 mm per side.** Structural support is completed by the ENCLOSURE and needs no PCB holes — moulded edge-capture rails, continuous on the right and bottom edges and segmented on the left to clear the 433 flex and the coax channel; plus four rear non-metallic support ribs on reserved component-free pads **`RIB_R1` `RIB_R2` `RIB_R3` `RIB_B1`**, all verified clear of every rear component and through-hole lead, all outside the battery shadow and all far outside the Ø58. **No copper pad was created for plastic support.** **OPEN FOR CTO DECISION: a third M2 needs a battery narrower than 60 mm, a display narrower than 56.54 mm, the SMA off the top-left, or an M2 with ≈ 1.4 mm of board between the hole and the board edge. All four are CTO calls and none was taken.** | 2026-08-24 |
| D-227 | **P1-O4 CLOSED. `MK1`'s PADSTACK IS REBUILT AND KiCad 10 ACCEPTS IT — WITH ZERO CHANGE TO THE ELECTRICAL OR ACOUSTIC GEOMETRY.** Retained exactly: **Ø1.05 mm NPTH acoustic opening, GND annulus ID 1.05 / OD 1.65 from the PUI drawing, 0.10 mm paste pullback, acoustic keep-out, microphone location (3.000, 50.000)**. Only the expression changed. **Pad 4 becomes a PLAIN FILLED Ø1.65 mm CIRCULAR SMD PAD** and the concentric **non-plated** Ø1.05 mm hole drills the centre out, so the finished copper is the same annulus — a plain circle is not a custom pad at all, so the validator has nothing to reject. **NO FAKE PLATED THROUGH-HOLE WAS USED.** The paste becomes **one custom pad carrying ONE filled C-shaped polygon** — the same ID 1.25 / OD 1.65 ring with a 20° web, anchored by a Ø0.20 mm circle sitting ON the ring band so anchor and primitive are one connected region; coverage 71.6 % → **67.6 %** of the copper ring, stencil area ratio **0.71** on a 0.12 mm foil against the 0.66 release floor. **`padstack_invalid`: 2 → 0.** Library and board copies are identical. One `solder_mask_bridge` remains and is **LEFT IN PLACE, NOT EXCLUDED**: the netless NPTH sits concentrically inside its own footprint's GND ring so the two mask apertures merge, and **there is no second net inside the merged aperture** — an artefact of the exact geometry the PUI drawing specifies. | 2026-08-24 |
| D-228 | **P1-O5 RESOLVED, AND ITS PREMISE WAS FALSE. THE ESP32 THERMAL VIAS WERE NEVER IN VIOLATION.** The board's global floor is `min_through_hole_diameter` = **0.20 mm**, not 0.30, so the stock `RF_Module:ESP32-S3-WROOM-1` footprint's **twelve Ø0.20 mm drills in Ø0.60 mm pads on pad 41** raise **zero** DRC violations and always did. **The twelve errors the FBV2-P1-001 audit attributed to them were twelve `copper_edge_clearance` errors on `J5`** — fixed here by nudging `J5` 0.070 mm west, x 64.970 → 64.900, putting its copper **0.515 mm** inside the board edge against the 0.5 mm rule. **FABRICATOR CAPABILITY VERIFIED LIVE 2026-08-24**: JLCPCB multilayer minimum via hole **0.15 mm**, and the surcharge applies only to *“0.2 mm or 0.25 mm hole size with a via diameter LESS THAN 0.45 mm”* — the 0.60 mm pad is above that threshold, so **the exact manufacturer geometry is SUPPORTED on the intended JLC04161H-7628 4-layer 1.6 mm stack AT NO PREMIUM**. A **narrowly scoped** rule is added as `.kicad_dru` **section 15**, `hole_size min 0.20 max 0.20` conditioned on `A.memberOfFootprint('U1') && A.Pad_Number == '41'`. **THE GLOBAL MINIMUM IS NOT LOWERED.** The rule is a **guard, not a waiver**: if the global floor is later raised to 0.30 mm — which is right for ROUTING vias — the manufacturer's thermal array stays legal instead of being silently corrected away. | 2026-08-24 |
| D-229 | **P1-O8 DISCHARGED: THE IR 90° FORMING REQUIREMENT IS WRITTEN, AND WRITING IT FOUND A REAL FIT DEFECT.** MPNs unchanged — `D1` **`TSAL6100`**, `U6` **`TSOP38238`**. The requirement is [`assembly/IR_LEAD_FORMING.md`](assembly/IR_LEAD_FORMING.md), sourced to **Vishay doc 84892**, *Processing Instructions for Mounting of Through-Hole LEDs*, rev 28-Nov-2017 (**“minimum 2 mm clearance between the epoxy case and bending point”**, **“lead forming has to be done prior to soldering”**, **“do not bend the leads more than twice at the same point”**, no force into the epoxy case, no case touch-down on the PCB) and to the two datasheets (`TSAL6100` doc 81009: Ø5.8 ± 0.15, body **8.7 ± 0.3 mm**; `TSOP382..` doc 82491, which links Vishay's own published **“Bends and Cuts”** standard forms for the minicast). **THE DEFECT:** a formed `TSAL6100` occupies **0.6 mm bend radius + 2.0 mm mandated straight + 8.7 ± 0.3 mm body = up to 11.6 mm** in +Y from its pads. At FBV2-P1-001's Y = 143.600 **the dome would have finished 1.2 mm OUTSIDE the enclosure's external top face.** `D1` moved to **doc (50.750, 141.400)** — the northernmost position at which the dome lands on Y = 153.0, which the enclosure must provide as a clear bore 1.5 mm into the 2.5 mm top wall with the IR-transmissive insert in the outer 1.0 mm. `TP39` and `R123` each moved **1.750 mm** south to clear the new courtyard. **`U6` needs only ≈ 9.0 mm and fits unmoved.** **RECORDED CONSEQUENCE:** `D1`'s leadframe now sits **2.854 mm inside the Ø58 metal exclusion, i.e. 2.146 mm outside the Ø48 loop perimeter**. `D1` **cannot** move east — it is already at the exact X the ≥ 15 mm TX↔RX rule allows with `U6` hard against the right board edge — and cannot move north without breaking the shell. The intruding metal is two 0.5 mm leads and a reflector cup of a few mm², perpendicular to the antenna plane, in the FRONT cavity while the antenna is on the REAR shell. Recorded, not hidden. | 2026-08-24 |
| D-230 | **B-52's FLOORPLAN HALF IS CLOSED; ONLY AN ENCLOSURE-CAD RESIDUAL REMAINS.** `CBA-UFLSMA20IP`'s own drawing is **marked NOT TO SCALE and dimensions nothing** — it identifies the interface and no more. The interface it names, **SMA(F) bulkhead straight**, is fully dimensioned in **Taoglas SPE-24-8-198-C** for the same interface (the `CAB.01034` fallback's own drawing) and both agree with MIL-STD-348A: **hex 8.00 mm across flats = Ø9.238 across corners**, hex body **3.40 ± 0.2 mm** into the cavity, thread **1/4-36 UNS-2A × 11.40 ± 0.2 mm**, **star lock washer Ø10.2 REF — the governing planar envelope**, nut HEX 8 × 1.80 ± 0.3 mm, centre pin Ø0.90. **Panel hole stays Ø6.5.** With the bulkhead at doc x 5.000: **SMA ↔ IR TX 47.250 mm centre-to-centre and 38.381 mm body-to-aperture; SMA ↔ IR RX 60.750 / 51.881 mm** — both rules pass by wide margins, and the hex sits against the top wall's inner face at cavity Y 151.5, protruding inward only to Y ≈ 148.1, **above the board edge rather than over it**, so it claims no board area. **THE BODY OD IS NO LONGER UNKNOWN.** **Residual, enclosure-CAD only:** the IP67 variant's face O-ring seat diameter and exact front protrusion are not dimensioned by RF Solutions; the floorplan carries **1.6 mm of diametral headroom** (the planar envelope may grow to Ø11.8 before touching the Ø58 exclusion), which bounds it. | 2026-08-24 |
| D-231 | **P1-O6 ACCEPTED AND RE-RUN; P1-O7 GENERATES NO CHANGE.** The corrected Full Beta v2 expectation stands — **one** `/03_SPI_A_DISPLAY_SD/LED_A` net, and the Beta-DM `LED_A1`…`LED_A4` expectation is **not** restored. `netclass_probe` scans **224 board nets, 3 resolve to `LED_BOOST`** (`LED_A`, `LED_BOOST`, `LED_K`) and the actual safety guard holds: **`LED_BOOST` does not capture `/07_IR/IR_LED_A` or `/07_IR/IR_LED_K`**. **NETCLASS PROBE: PASS.** **P1-O7: no feature and no placement change was authorised or made from it.** Separately, two COLLISION-MODEL defects were corrected so the review stops lying: `U1`'s `F.CrtYd` bounding box **is the manufacturer's antenna keep-out polygon, not the module body**, and reviewing against it reports **58 false collisions** — the body X 42.90 … 63.06 / Y 9.90 … 30.10 is now used and the keep-out tested separately; and **opposite-face pairs must be tested hole-against-courtyard**, because only a lead or a hole reaches the other face — `SW9`'s two Ø0.9 mm NPTH alignment holes do not make its whole courtyard opaque to the rear. | 2026-08-24 |
| D-232 | **RETENTION IS LOCKED AT TWO M2, AND D-226'S ESCALATION IS CLOSED. TWO CURRENTLY LEGAL M2 THROUGH-BOARD SCREWS ARE ACCEPTABLE.** No major component moves to obtain a third: **the battery is not reduced, the display is not moved, the SMA is not relocated.** Mechanical retention is completed by four elements, three of which are enclosure features needing no PCB hole. **A. MOULDED EDGE-CAPTURE RAILS** constrain lateral PCB movement — continuous on the RIGHT and BOTTOM edges, segmented on the LEFT to clear the 433 flex (Y 1.5 … 48.5) and the coax channel's western excursion (Y ≈ 112 … 137). **B. FOUR REAR NON-METALLIC SUPPORT RIBS** `RIB_R1` `RIB_R2` `RIB_R3` `RIB_B1`, all verified component-free including through-hole leads: `RIB_R2` (Y 45 … 64) bears directly behind the A/B control area and `RIB_B1` + `RIB_R1` bracket the D-pad region, so **board flex under button pressure is carried by plastic, not by FR4 span**. **EVERY RIB IS OUTSIDE `BATTERY_SHADOW`, SO NO SUPPORT COMPRESSES THE LiPo**; every rib is non-metallic and all four are far outside the Ø58 NFC metal exclusion — **no metal enters the NFC exclusion.** **C. THE TWO M2 SCREWS** `BOSS1` doc (40.000, 12.000) and `BOSS2` doc (59.000, 145.000), Ø4.5 keep-out, Ø2.2 NPTH. **D. THE `J5` BACKING / LOAD-PATH STRUCTURE** — the `COMM_RECESS` backing boss carries the ≈ 33 N average insertion load (peak higher) **INTO THE ENCLOSURE, NOT INTO THE PCB SOLDER JOINTS** (D-097, M-10). **USB AND microSD INSERTION LOADS DO NOT DEPEND ONLY ON THE M2 SCREWS**: `J3` and `J2` both sit on the bottom edge, which carries a CONTINUOUS edge-capture rail, with `BOSS1` 12 mm above it — the rail takes the reaction along its whole length and the screw is a secondary path. **A THIRD M2 MAY BE ADDED LATER ONLY IF ENCLOSURE CAD PRODUCES A LEGAL LOCATION WITHOUT SACRIFICING EXISTING GEOMETRY**; D-226's four routes to one — narrower battery, narrower display, SMA off the top-left, or ≈ 1.4 mm of board to the edge — are **ALL DECLINED**. Applied to `mechanical/MECHANICAL_INTERFACE_SPEC.md` §4.2 and its machine-readable block, where three stale entries were corrected in the same pass: *"Count: 6 × M2"*, `FBV2_BOSSES: 3 x M2 ... PARTIAL (D-216, target 6)` and `FBV2_915_PIGTAIL: 095-902-568-100 (100 mm) ... DOES NOT REACH` (superseded by D-223). | 2026-08-24 |
| D-233 | **P2-O5 IS CLOSED, AND IT WAS FAR LARGER THAN IT HAD BEEN RECORDED. TWENTY-TWO OF SEVENTY-ONE RULES WERE SILENTLY INERT.** `FBV2_P1_FLOORPLAN.md` §16 recorded P2-O5 as *"`.kicad_dru` still references E5/E6 rule areas"*. **MEASURED: the file referenced THIRTY-NINE rule areas and the board contained NONE of them** — only `MIC_ACOUSTIC_KEEPOUT`, `BOSS1_KEEPOUT`, `BOSS2_KEEPOUT` and one UNNAMED zone embedded in `U1`. It was not only the E6 pockets: it was **every RF-band rule, every E5/E4 corridor rule, the header reservation, the E2 button escapes AND THE ESP32 ANTENNA RULE**. **WHY NOTHING CAUGHT IT: KiCad's `intersectsArea()` and `enclosedByArea()` return FALSE for an unknown name — they do not warn and they do not error**, so a rule whose condition can never be true produces no violations, which is indistinguishable from a rule being satisfied. **The ESP32 antenna was never actually unprotected** — the `U1` footprint carries its own embedded rule area with every keepout flag set on all four copper layers — but the FILE claimed protection from an area that did not exist. **THE RULE SET IS REBUILT: 71 → 64 rules, every one checked against the current board, with a written RETIREMENT REGISTER in the file header giving a reason for each of the 22 retirements (R1–R10).** Nothing was retired for convenience: where intent survived it was re-expressed against current objects (ESP32 keepout, switch nodes, USB, NFC); where intent died with the Beta-DM geometry that is stated as a finding. **THE E6 ESCAPE-RELIEF DOCTRINE IS NOT RETIRED** and is restated in full in `pcb/FBV2_P2_ROUTING_PLAN.md` §17 — own-area sufficiency, `enclosedByArea()` never `intersectsArea()`, the 2.0 mm HARD clearance-run cap kept separate from the 6.0 mm narrow-width REVIEW trigger, the narrow-escape search doctrine, and last-in-file precedence. **ONE BOARD EDIT ONLY:** a board-level rule area `WROOM ANTENNA KEEPOUT`, polygon and flags identical to `U1`'s embedded one. **Naming `U1`'s own zone was tried first and REVERTED** — it edits the board copy of a library footprint and immediately raised `lib_footprint_mismatch`, a class FBV2-P1-002 had driven to zero; the reasoning is recorded in the rule file so nobody re-tries it. **THE DURABLE FIX IS `hardware/beta-v2/checks/dru_probe.py`**, new and now part of the validation set: it fails if any rule reference stops resolving or any netclass pattern stops matching. **P2-O5 CANNOT RECUR SILENTLY.** **DRC 47 → 26**, all 21 `clearance` violations closed by naming the four vendor land patterns that cause them (`D2`, `U18`, `U19`, `U21` — all stock KiCad footprints at 0.1500 mm) — **no routing clearance anywhere was weakened.** | 2026-08-24 |
| D-234 | **THE NETCLASS TABLE HAD BEEN LYING SINCE THE FORK: THE HIGHEST-CURRENT NET ON THE BOARD WAS ON THE 0.20 mm DEFAULT CLASS.** The inherited `BAT_MAIN` pattern was the ROOT-SHEET path `/BAT_PROTECTED_P`, while every Full Beta v2 power net lives under `/01_POWER_TREE/`. **IT MATCHED NOTHING.** `/01_POWER_TREE/BAT_PROTECTED_P` — **1.5 A sustained** — was therefore routing at 0.20 mm, and **`BAT_RAW`, `BAT_MID` and `BAT_SENSE`, which all carry the full pack current, were in no class at all.** The same root-path defect killed `NFC_5V_PA` outright (`/NFC_5V_PA_PENDING` matched nothing, so **the class captured no net whatsoever**), and `*BTN_HOME_N` matched nothing because that net does not exist in v2. Separately, **`ACC_5V_LX` — the `U21` accessory-boost SWITCH NODE — had NEVER been in `SWITCH_NODE`** and was a 1.2 MHz switching node on the ordinary signal class; `ACC_5V_SW`/`ACC_5V_RAW` (0.70 A) and `NFC_SUPPLY` (`U9` VDD/VDD_TX) were on Default. **REPAIRED: 14 netclasses → 18, 62 patterns → 57, and EVERY surviving pattern now matches at least one board net.** Four dead classes retired — `E5_CROSSING`, `E2_BUTTON_ESCAPE`, `RF_DO_NOT_ROUTE`, `RF_DEFERRED_NFC` — all of which either matched nothing or carried Default values, so **no net's electrical parameters were weakened by a retirement.** Four added — `ACC_3V3` (split out of `P3V3` so the ledger states 400 mA published / 0.76 A ILIM instead of inheriting the 1.0 A `+3V3` figure), `ACC_5V`, the `NFC_RF`/`NFC_RX`/`NFC_OSC` set, and the selector-only `I2C`/`I2S`/`SPK_OUT` classes that make switch-node victim separations encodable at all. **57 of 224 nets are now classified and 167 sit on Default, AND THAT IS CORRECT** — 167 ordinary GPIO, control, status and single-pad nets have no constraint and must not be given one. | 2026-08-24 |
| D-235 | **THE FULL BETA v2 ROUTING STRATEGY IS FROZEN.** **STACKUP: the retained 4-layer JLCPCB `JLC04161H-7628` stack is REVIEWED AND KEPT** — the evidence is positive, not inertial, and no 2-layer or 6-layer argument exists for a 224-net design with a continuous-ground requirement for USB, NFC, four converters and a Class-D amplifier. **LAYER ROLES ARE NOW ENFORCED BY RULE, NOT ASSERTED:** F.Cu front signals and the USB pair exclusively; **In1.Cu SOLID CONTINUOUS BOARD-WIDE GND, no splits, no analog island** (`severity error`); In2.Cu power distribution and SLOW control only, because its only continuous reference is In1 across the 1.065 mm core — **USB, both NFC transmit arms, the NFC crystal, every switch node, the Class-D output and `BAT_MAIN` are all FORBIDDEN on In2**; B.Cu rear signals, power stages, radios and the whole NFC front end. **GROUND: one plane, ONE authorised void** — the ESP32 antenna keepout, a **6.5 × 44 mm notch in In1 on the RIGHT board edge over doc y 0…44**, in the same corner as `U1`, `U11`, `U18`, `R75` and `D10`, so **every return path in that corner must be planned around a plane edge, not assumed continuous.** Perimeter stitch ≤ 7 mm (λ/20 at 1 GHz in FR4 = 7.15 mm); a dedicated via at every connector GND pad; ≥ 2 at every ESD, converter and RF ground pin; **NONE inside any antenna, acoustic or boss keepout, and no stitching lattice under the NFC loop.** **Switching-current loops are localised by PLACEMENT AND ROUTING, NOT BY CHOPPING GROUND** — and the temptation PM-1 creates to cut ground around a 45.9 mm switch node is explicitly refused. **USB IS FULL SPEED AND THE SHORT ANSWER IS THE CORRECT ONE:** the ESP32-S3 has no HS PHY, so t_r 4–20 ns gives a 100 mm critical length against a MEASURED ≈ 40 mm path entirely on F.Cu over solid In1 — **no impedance control, no length matching and ZERO vias are required**, and the intrinsic placement skew is 2.4 mm = **17 ps** against a ≈ 1 ns budget. The 90 Ω geometry is retained as good practice and marked **STACKUP-TO-CONFIRM** for one honest reason: **the board file carries NO physical stackup object at all** (nor does Beta-DM's), so a fabricator would build to its own default — opened as **P2-O6**, a DFM-release item that does not block routing. **NO LENGTH-MATCHING THEATRE ANYWHERE:** SPI-A is 46.4 mm (Beta-DM 126.5, **63 % shorter**) and SPI-B is 113.1 mm (Beta-DM 144.0, **21 % shorter**), both shorter than versions already accepted, so neither gets matching or damping; **the one bus with a real derived constraint is INTERNAL I²C, at C_bus ≤ 161 pF for 400 kHz on 2.2 k pull-ups**, with 100 kHz as the recorded fallback. **19 routing classes are tabulated in `pcb/FBV2_P2_NETCLASS_LEDGER.csv`.** The CTO routing order is **adopted with three documented changes**: steps 6 and 7 merged because the 27.12 MHz crystal IS the NFC front end and routing it separately invites the via §10 forbids; and step 17 split into **17a return-path stitch vias placed WITH each loop** — a return path retro-fitted afterwards is one nobody checked — and 17b final pours last. **Two further items opened: P2-R1**, the 433 flex sits 0.2 mm outboard of the LEFT board edge over 47 mm of it so board copper there is an AGGRESSOR into it, deliberately NOT instantiated as a rule area until PM-1 settles which parts occupy that band; and **PT-1**, `U11` BQ25185 dissipating ≈ 0.65 W while charging from INSIDE `BATTERY_SHADOW`, pressed against the cell it is charging in a sealed enclosure — **no thermal path in this design may depend on the battery.** | 2026-08-24 |
| D-236 | **THREE PLACEMENT MOVES ARE ELECTRICALLY REQUIRED. THEY ARE SURFACED, NOT DECIDED, AND THEY ARE WHY FBV2-P2 ENTRY FAILS.** The instruction is explicit — *do not route around a bad power placement* — so these are escalated rather than designed around. **ALL THREE ARE NEW, ALL THREE ARE MEASURED FROM THE BOARD, AND NONE EXISTED IN BETA-DM TO BE CARRIED FORWARD**: the battery-protection block and the NFC front end are both new in Full Beta v2, FBV2-P1 placed them into free rear pockets and verified every MECHANICAL relationship by script, and **nobody had yet looked at either electrically.** **PM-1 — ALL FOUR SWITCHING CONVERTERS HAVE THEIR INDUCTOR OFF THE IC.** `U12`/`L1` **12.96 mm**, `U13`/`L2` **28.56 mm**, `U21`/`L4` **30.50 mm**, `U17`/`L3` **45.90 mm**, against a ≤ 5 mm requirement. Worst case: `BL_SW` runs `U17.1` (47.2, 33.3) → `L3.2` (4.9, 37.0) while **the catch diode `D8` sits at (50.6, 36.5), beside the IC and 45.7 mm from the inductor**, so the `L3 → D8 → C44` boost energy loop is **≈ 76 mm around**, switching at 1.2 MHz between 0 V and **up to 39 V on the open-LED fault** (TI SNVSA40B V_OVP_SW 36/37.5/39 V), down the left margin, **13 mm from `MK1`**, through the band the 433 flex sits against. **All four inductors were placed in the left-margin column at x ≈ 3 while their ICs went elsewhere — systemic, not four coincidences. LOOP AREA IS A PLACEMENT PROPERTY; NO ROUTING REPAIRS IT.** **PM-2 — THE SINGLE-FAULT BATTERY-PROTECTION BLOCK IS DISPERSED OVER 96 mm.** The 1.5 A path is `J4` → `F1` (9.0) → `Q2` → `Q3` (18.3 + 6.2) → **79.0 mm** → `R75` → `U11` (4.2) = **≈ 116.7 mm total**. **WHAT IS RIGHT AND STAYS RIGHT: the Kelvin sense is sound** — `U18.9` SENSE and `U18.8` OUT both land on `R75`'s pads with `U18` 4.2 mm away, so **the 47 mV measurement across the 15 mΩ shunt at the 3.125 A trip is NOT corrupted.** What is wrong is everything around it: **`LTC_GATE` 95.6 mm** (a ≈ 20 µA charge-pump node holding four pass FETs enhanced, its `R76`/`C57` damping 31–45 mm from the FETs and 60–75 mm from `U18`), **`BAT_SENSE` 96.5 mm** (FET source AND 1.5 A conductor — 38.8 mΩ, 58 mV, 87 mW), **`LTC_OV` 78.4 / `LTC_UV` 81.7 mm** (3.65 M and 510 k dividers carrying **the battery over/undervoltage trip points**), **`VBRIDGE_TOP` 90.1 / `VREF_TOP` 80.8 / `REF_HO` 82.4 mm** (2.2–3.65 MΩ dead-cell reference nodes; `REF_HO`'s two divider halves `R91` and `R92` are **38 mm apart** and `U19` is **52 mm** from the top resistor). The block sits in **three clusters** with multi-megohm comparator nodes and a micro-amp gate node strung between them. **ROUTING CANNOT MAKE A 3.65 MΩ NODE THAT CROSSES FOUR SWITCHING CONVERTERS IMMUNE TO COUPLED CHARGE.** **D-049 AND THE SINGLE-FAULT ARCHITECTURE ARE NOT COMPROMISED BY THIS FINDING AND NO TOPOLOGY CHANGE IS PROPOSED** — the recommendation moves parts, not circuits, and it also returns **≈ 0.13 W at 1.5 A / 0.18 W at 1.75 A** to open blocker **B-34**. **PM-3 — THE NFC DIFFERENTIAL FRONT END IS NOT SYMMETRIC.** `NFC_MATCH_A` spans **24.18 mm** against `NFC_MATCH_B` at **34.21 mm** — **10 mm of asymmetry before a single track is drawn**; `L5` and `L6` are **19.8 mm apart on OPPOSITE sides of `U9`**; the antenna nodes differ 8.82 vs 12.49 mm; each EMC filter node's three capacitors are spread over 13.6–17.2 mm; and **the crystal load caps `C79`/`C80` sit 13–15 mm from `Y1` on the far side of the IC**, giving a ≈ 30 mm oscillator loop. With **`R_q` 1.1 Ω per arm and network Q ≈ 21** (D-204) and mandatory first-article bench tuning, **a 10 mm arm-length asymmetry is not something routing can absorb.** **RECOMMENDATIONS, NONE TAKEN:** each inductor and output capacitor to its own IC inside a ≤ 8 mm cluster, with `L3` + `C44` joining `U17` rather than `U17` walking the 39 V node towards the microphone; the LTC4368 controller, shunt and trip dividers consolidated at the battery-entry corner with `J4`/`F1`/`Q2`/`Q3` so that only `BAT_PROTECTED_P` remains a long run; and the NFC front end rebuilt as a mirrored pair about a single `U9` → `J7` axis with `C79`/`C80` at `Y1`. **ROUTING DOES NOT BEGIN UNTIL PM-1, PM-2 AND PM-3 ARE RULED ON.** | 2026-08-24 |
| D-237 | **THE EXPANSION INTERFACE IS ADOPTED. `J5` BECOMES A STANDARD 1 × 24 2.54 mm FEMALE RIGHT-ANGLE SOCKET, SUPERSEDING THE 2 × 12.** Samtec **`SSQ-124-02-G-S-RA`** replaces **`BCS-112-S-D-HE`**, superseding the physical half of D-081 / D-083 / D-093 — **the same manufacturer, so the account, the lead-time behaviour and the small-quantity policy are already known.** Configuration verified against the Samtec SSW/SSQ through-hole datasheet: 01 thru 50 positions per row, `-S` SINGLE ROW, `-RA` right angle (which the datasheet lists as available with `-S`), lead style `-02` setting the socket axis 2.54 mm above the PCB, `G` = 20 µin gold; **body 61.47 mm = 24 × 2.54 + 0.51, pin span 58.42 mm, mates .025 in (0.635 mm) SQUARE POST — the ordinary male-header / Dupont standard — 6.3 A per pin, 465 VAC / 655 VDC, −55 to +125 °C, 100 mating cycles.** Hole pattern Ø1.02 mm on 2.54 mm from the Sullins 1-row right-angle recommended layout (drawing 10493), which also supplies the **6.53 mm tail-row-to-mating-face depth THE WHOLE RIGHT-WALL FIT TURNS ON**. **ALL 24 ELECTRICAL FUNCTIONS ARE RETAINED AND NOT ONE PROTECTION COMPONENT IS REMOVED**: the twelve 100 Ω GPIO series resistors, the 22 Ω I²C pair, the 330 Ω WAKE resistor, all four `TPD4E1B06` TVS arrays, `U16` TCA4307, both `TPS22950C` load switches, the `TPS61023` boost, the `R103` FLT wire-OR, the `Q10` WAKE isolation gate and the `ACC_DETECT_N` protection are all present and electrically identical. **THE SCHEMATIC CHANGE IS A FOOTPRINT SWAP PLUS A PIN RE-MAP ON SHEET 09 — no net was created, deleted, split or merged, and the netlist still resolves 224 nets.** **`Samtec_BCS-112-S-D-HE.kicad_mod` IS RETAINED IN THE LIBRARY, NOT DELETED**: Beta-DM still uses it and it is the fallback if this ruling is ever reversed. | 2026-08-24 |
| D-238 | **QWIIC / STEMMA QT IS ADDED, AND IT COSTS ZERO COMPONENTS.** `J8` = **`JST SM04B-SRSS-TB(LF)(SN)`**, SH series **1.0 mm** pitch (confirmed from JST's own `eSH.pdf`), 4 circuit, **SIDE ENTRY, SMT — machine-placed, so the manual-assembly list stays at two parts (`J5`, `D1`)**. Body 6.0 × 4.25 mm, 1.0 A, 50 V AC/DC, −25 to +85 °C, 20 mΩ contact resistance. **PIN ORDER IS THE ECOSYSTEM STANDARD, NOT A CHOICE: 1 GND, 2 3.3 V, 3 SDA, 4 SCL** — identical for SparkFun Qwiic and Adafruit STEMMA QT, so every cable in either ecosystem mates it. **IT ATTACHES AT `EXT_SDA` / `EXT_SCL`** — downstream of `U16` TCA4307 and of the `R47`/`R48` 22 Ω pair, at `D2`'s TPD4E1B06 clamp, **the same node as the header** — so it inherits the hot-swap buffer, the `R49`/`R50` 1.5 k pull-ups, the series resistance and the ESD array. **NO second buffer, NO mux, NO repeater, NO extra pull-ups and NO second TVS were added**, and none is needed: the existing clamp sits on the shared node and therefore protects both exits by construction. **POWER IS `ACC_3V3_SW` AND THAT IS ARCHITECTURAL, NOT PREFERENTIAL:** `U16`'s own VCC is already `ACC_3V3_SW` and the pull-ups pull to it, so an unswitched `+3V3` feed would create a powered-device / unpowered-bus state and invite back-feeding through an accessory's ESD diodes. **`ACC_5V_SW` IS NOT PRESENT ON `J8` AND CANNOT BE.** Capacitance re-checked on the BUILT placement: on-board copper ≈ 25 pF + connector ≈ 1 pF + a 100 mm cable ≈ 5–10 pF + a typical breakout ≈ 10 pF → **one board ≈ 40 pF, three short daisy-chained boards ≈ 60–80 pF against a ≤ 200 pF budget at 400 kHz on the 1.5 k pull-ups.** 100 kHz remains the fallback. | 2026-08-24 |
| D-239 | **THE BOARD GROWS TO 72 × 148 mm AND THE BATTERY NARROWS TO 57 × 75 × 8 mm MAXIMUM — AND THE BATTERY GATE WAS RUN BEFORE ANY FILE WAS TOUCHED.** **THE 3 mm OF CELL WIDTH IS THE ENTIRE PRICE OF THE 24-LINE SIDE HEADER**: a right-angle socket puts its tails **6.53 mm inboard of its own mating face**, so the requirement is (board right edge − cell right edge) ≥ 0.5 clearance + 0.8 pad radius + 6.53 = **7.83 mm**, against 4.00 mm on the old outline. **THE BOARD GROWS SYMMETRICALLY, +1.0 mm ON EACH SIDE**, so every part shifts +1.0 mm in X, **every part-to-part relationship is preserved exactly**, and only the two edge margins move. The 80 × 160 × 23 enclosure and the 75 × 155 cavity are **UNCHANGED**; the wall gap falls 2.5 → **1.5 mm on both sides — the ≥ 1.5 mm rule met EXACTLY, with nothing to spare.** **`ANT433_REGION` HAD TO BE RE-DERIVED RATHER THAN SHIFTED**: the old 2.2 mm reservation does not fit a 1.5 mm gap and never described anything real — the flex is **0.28 mm thick** and bonded flat to the wall — so the region is now X −1.40 … −0.60 taken from the part, with 0.6 mm of air to the board edge. **BATTERY GATE = PASS on two manufacturer-datasheet candidates**: **PKCELL `LP785060`, 7.3 × 50 × 60 mm, 2500 mAh typ / 2375 min, PCM fitted, JST-PH lead**; and **`LP755070`, 7.5 × 50 × 70 mm, 3000 mAh min / 3050 typ, PCM fitted (4.275 V ±50 mV overcharge, 2.50 V resume), AWG26 leads, 500 cycles to 80 %.** **THE CAPACITY PENALTY IS SMALLER THAN THE −5 % ESTIMATE AND IT IS HONEST TO SAY SO: the 57 mm limit does not bind either candidate — both are 50 mm wide — and `LP755070` delivers 3000 mAh, at the TOP of D-071's 2500–3000 mAh target. The envelope was always larger than the cells that fill it. The capacity target is UNCHANGED.** Measured result: tail row X 65.900, tail pad edge 65.100, **1.100 mm clear of the cell**; mating face X 72.430, **0.430 mm outboard of the board edge with 1.070 mm to the cavity wall.** | 2026-08-24 |
| D-240 | **PIN ORDER IS ORDER-B, AND IT IS SAFE UNDER 180° REVERSAL BY CONSTRUCTION.** Pin 1 at the TOP, reading down: **1 5V · 2 G · 3 3V3 · 4 SDA · 5 SCL · 6 G · 7 N38 · 8 N47 · 9–18 X0–X9 · 19 G · 20 WAKE · 21 DET · 22 3V3 · 23 G · 24 5V.** This SUPERSEDES EXP-001's ORDER-A. **VERIFIED PROGRAMMATICALLY FROM THE EXPORTED NETLIST, PIN BY PIN, AND THE REVERSAL MAP IS EXHAUSTIVE:** a full 24-pin accessory inserted 180° maps its pin *n* to AQROOT contact *25 − n*, giving **5V↔5V, GND↔GND, 3V3↔3V3 and 3.3 V logic ↔ 3.3 V logic on every remaining contact. POWER-TO-SIGNAL MAPS UNDER REVERSAL: ZERO.** No 5 V reaches a signal, no 3.3 V reaches 5 V, no GND reaches a signal. That symmetry is the whole reason ORDER-B supersedes ORDER-A, which was safe against a one-position slip but not against reversal. **THE ONE-POSITION LATERAL SHIFT REMAINS PHYSICALLY IMPOSSIBLE**: a mating male body is exactly 24 × 2.54 = **60.96 mm** and the CLOSED-END recess is **62.5 mm** internally, leaving **1.54 mm of play against a 2.54 mm pitch — 61 % of one position.** Both ends closed, moulded pin-1 triangle, red bands over pins 1 and 24. **NO PROPRIETARY SHROUD, AND D-097's ASYMMETRIC UPPER-EDGE KEY IS NO LONGER REQUIRED.** Individual Dupont access is unaffected: the recess opening is one continuous slot at socket-face height. **ACCESSORY MECHANICAL SUPPORT IS NON-ELECTRICAL ONLY** — the recess floor, the two closed ends and a moulded ledge the full 62.5 mm; the 1 × 24 has **no roll couple** where the 2 × 12 had 7.87 mm, so the enclosure carries the bending load and **not the 24 solder joints. DIRECT STACKING OF TWO FULL 1 × 24 ACCESSORIES IS NOT SUPPORTED: one full-header accessory at a time, with a second board on Qwiic or jumper wires. No AQROOT hub is required and none is built.** | 2026-08-24 |
| D-241 | **PM-1, PM-2, PM-3 AND PT-1 ARE ALL CLOSED IN ONE COMBINED RE-FLOORPLAN — TOPOLOGY UNCHANGED, ONLY POSITIONS MOVED.** **PM-1: every converter is now a complete POWER CELL, not just an inductor moved next to an IC** — IC, inductor, input capacitor, output capacitor and feedback divider packed in electrical order. **`U12`/`L1` 12.96 → 4.80 mm · `U13`/`L2` 28.56 → 4.34 mm · `U21`/`L4` 30.50 → 3.86 mm · `U17`/`L3` 45.90 → 3.79 mm**, all against a ≤ 5 mm requirement. **`D8`, the backlight catch diode that sat 45.7 mm from its own inductor, is now 3.56 mm from `U17` and adjacent to `L3` and `C44`, so the `L3 → D8 → C44` loop that switches to 39 V on an open-LED fault is a local loop instead of a 76 mm perimeter running 13 mm from the microphone.** **PM-2: the whole 1.5 A path is one monotonic column in the left margin** — `J4` → `F1` 8.59 → `Q2` 6.21 → `Q3` 7.80 → `R75` 8.26, **total 30.86 mm against 116.7 mm**, with the **Kelvin pair `R75` ↔ `U18` at 6.60 mm**. **NO FET, NO THRESHOLD, NO DIVIDER VALUE AND NO RECOVERY BRANCH WAS ALTERED; D-049 AND THE SINGLE-FAULT ARCHITECTURE ARE UNTOUCHED.** **`J4` IS THE ONE PART IN THE CHAIN THAT COULD NOT JOIN IT, AND THAT IS RECORDED RATHER THAN HIDDEN**: the left margin is also the mandatory 915 coax lane, which is a CABLE lane rather than a component keepout — the RG-178 lies over rear parts, all ≤ 2.0 mm — but `J4` is a 5.75 mm JST-PH with a mating cable and nothing can lie over it, so it sits at the top of the column at doc (7.000, 113.000), north of the coax's western excursion, 8.59 mm from `F1` and 0.7 mm clear of the cable. **PT-1 CLOSED: `U11` BQ25185 moves out of `BATTERY_SHADOW` to doc (67.500, 70.200), 3.5 mm clear of the cell's right edge**, so its ≈ 0.65 W of charging dissipation spreads into copper with no cell behind it. **B-34 RE-ESTIMATED ON THE BUILT GEOMETRY AND NOT CLAIMED AS ZERO:** at 1 oz and 1.0 mm width the protection-path copper falls from 38.8 mΩ (58 mV / 87 mW at 1.5 A) to **15.2 mΩ (23 mV / 34 mW)** — an improvement of ≈ 53 mW at 1.5 A and ≈ 72 mW at 1.75 A. **B-34 IMPROVES MATERIALLY BUT DOES NOT CLOSE**: its ≈ 0.70 W is dominated by the BQ25185 BATFET's 115 mΩ and the FET R_DS(on), which this task correctly did not change; the copper contribution falls from ≈ 17 % of the figure to ≈ 7 %. **PM-3: the NFC front end is rebuilt as an exact mirror pair about y = 118.000** — `L5`/`L6`, `C69`/`C70`, `C71`/`C72`, `R114`/`R115`, `R116`/`R117`, `C75`/`C77` all at **Δx = 0.000 mm and arm-length Δ = 0.000 mm** against a ≤ 1 mm requirement, same topology, same orientation, same stage order, `Y1` **5.40 mm** from `U9` with its load capacitors local instead of 13–15 mm away on the far side of the IC, `J7` on the axis, tuning passives in an open row and `TP37`/`TP38` symmetric. **NO LOCKED NFC COMPONENT VALUE WAS CHANGED**, Ø48 / Ø58 are unchanged at doc (31.800, 124.500) and the battery keeps zero overlap with the clear region. | 2026-08-24 |
| D-242 | **FBV2-P1 IS RE-ISSUED AND PASSES; FBV2-P2 ENTRY IS RE-RUN AND PASSES. NO PERCENTAGE IS AWARDED FOR EITHER.** The outline, the battery and `J5` all changed, so the FBV2-P1-002 pass was superseded and the gate was **re-run in full**: 72.000 × 148.000 mm, 324 footprints = 322 schematic + 2 bosses, **ZERO side-aware courtyard collisions, ZERO parts off the board**, every keepout valid, 915 coax **138.48 mm of 200 with 46.52 mm spare and a 7.42 mm minimum bend radius**, 433 lead 44.12 of 100, **NFC pair 31.23 of 75 (shortened by PM-3 from 41.73)**, speaker lead 29.31 of 152, FPC 14.94 of 29.5, microSD ↔ USB-C 14.990, NFC clear ↔ battery 2.0 mm with zero overlap, `MK1` ↔ speaker 67.424, IR TX ↔ RX 15.000, SMA washer ↔ Ø58 +0.798, and **NFC loop ↔ `J5` metal 9.155 mm, improved from 5.490**. **`J5`'s courtyard legitimately overhangs the right edge by 0.975 mm — that is what a right-angle socket is FOR — and `p1_regression.py` now tests it explicitly (`mating face ≤ 1.0 mm outboard`) instead of counting it as a part that has fallen off the board.** **`BOOT` `SW1` MOVES TO doc (28.300, 6.000) ON THE FRONT FACE**, in the measured 11.04 mm window between the microSD shell and the USB-C receptacle; it is an SMD PTS645 whose actuator faces out of the FRONT shell, so the service aperture is a **Ø2 mm recessed hole in the FRONT wall — not the bottom wall — and is therefore clear of both the card-insertion path and the USB-C plug envelope.** **LOWER-LEFT WAS NOT USED: that wall IS `ANT433_REGION` and the mandatory `COAX_915_CHANNEL`.** **POWER `SW9` STAYS ON THE RIGHT WALL** at doc (66.700, 61.500), finger-operable, electrically unchanged. **RETENTION IS STILL TWO M2** — Ø6.0 returns zero sites, Ø4.5 returns two — **widening the board did not buy a third screw and no functional geometry was sacrificed chasing one.** **DRC 26 → 1**: the single remaining violation is the `MK1` netless-NPTH-inside-its-own-GND-ring `solder_mask_bridge` reviewed and accepted at D-227, **still not excluded and not suppressed**. **ERC 0 errors / 27 warnings, histogram identical. 499 unrouted; ZERO tracks, ZERO signal vias, ZERO electrical pours.** `p1_regression`, `dru_probe`, `netclass_probe` and `fork_equivalence` all PASS. **FBV2-P2 ENTRY PASSES because PM-1, PM-2, PM-3 and PT-1 are closed and NO ELECTRICALLY REQUIRED PLACEMENT MOVE REMAINS.** Escape feasibility on the new connector: 24 holes on 2.54 mm give an 0.94 mm adjacent-pad gap, one 0.2 mm track per gap per layer, **23 gaps × 3 usable layers = 69 crossings against the 66 the old 2 × 12 offered**, the 7.87 mm dead band is gone and both ends of the row are open — **so no reservation area and no fanout exception is needed, which is why the retired `HEADER RESERVED` / `J5_SELF_FANOUT` rules were not re-created.** **NO PERCENTAGE: FBV2-P1 was RE-EARNED, not newly earned, and the gate-backed method does not pay twice for one gate; P2 entry earns none by its own terms. Overall Full Beta v2 stays ~74 %.** **ONE NEW ITEM FOR THE OWNER — E-7: the 57 mm envelope is now the LOWER bound of what fits, not a target.** Both credible cells are 50 mm wide, so **7 mm of reservation width is unused**. That is not a defect and nothing depends on it, but a future task could reclaim it for rear components or keep it as tolerance for a wider, higher-capacity cell. **Recorded, not decided.** | 2026-08-24 |
| D-243 | **E-7 CLOSED. THE BATTERY ENVELOPE IS 57 × 75 × 8.0 mm AND THAT FIGURE IS A MAXIMUM RESERVED ENVELOPE. 57 mm IS NOT A MINIMUM CELL WIDTH AND NOT “THE LOWER BOUND OF WHAT FITS” — the FBV2-EXP-002 wording was wrong and is WITHDRAWN.** Verified 50 mm-wide cells fit and are the intended candidates: **PKCELL `LP785060`** (7.3 × 50 × 60 mm, 2500 mAh typ / 2375 min, PCM fitted, JST-PH lead) and **`LP755070`** (7.5 × 50 × 70 mm, 3000 mAh min / 3050 typ, PCM fitted, 500 cycles to 80 %). **THE ENVELOPE IS NOT SHRUNK TO 50 mm.** The unused 7 mm preserves alternate- and future-cell flexibility at **ZERO current placement cost** — nothing is waiting to occupy it, so reclaiming it would buy nothing and would spend the only tolerance the design has against a different cell. **D-071's 2500–3000 mAh capacity target is UNCHANGED.** | 2026-08-24 |
| D-244 | **FBV2-P2-001 FAILS: THE POWER TREE IS NOT ROUTED, AND THE ATTEMPT WAS REVERTED RATHER THAN COMMITTED.** The pre-routing checkpoint **`beta-v2-p2-entry-pass` was created as an ANNOTATED tag on `faa0c91` and pushed**, and verified on the remote before any copper was drawn. **WHAT THIS TASK DID DELIVER: the In1.Cu GND REFERENCE PLANE** — one zone, **ONE ISLAND**, net GND, **9938.9 mm² of a 10656 mm² board = 93.3 %**, SOLID pad connection with no thermal relief, no split, no analog island, and its ONE authorised void cut automatically by the existing ESP32 antenna rule area rather than by a hand-carved polygon. **F.Cu / B.Cu pours were deliberately NOT created**: they are the last step of FBV2-P2 and making them now would hide return paths rather than prove them. **`p1_regression.py` was taught the difference between a POUR and ROUTING** — the blanket *“0 fills”* expectation is replaced by *“0 tracks / 0 vias / 0 OUTER pours”* plus a POSITIVE check that **In1 is exactly one GND zone of exactly one island**, so a split reference is now a gate failure instead of an invisible mistake. **WHAT IT ALSO FOUND, AND THIS IS THE ESCALATION: PM-2 WAS CLOSED ON INCOMPLETE EVIDENCE AT FBV2-EXP-002.** The chain metric — `J4`→`F1`→`Q2`→`Q3`→`R75`→`U18`, 30.86 mm, Kelvin 6.60 mm — was REAL and is NOT withdrawn, but it was reported as if it closed the whole of PM-2 and it did not: the trip/gate and dead-cell support parts had been packed into regions chosen while the chain still sat in the right column and were never re-homed when it moved. Measured on `faa0c91`, **`LTC_GATE` — a ≈ 20 µA charge-pump node holding four pass FETs enhanced — spanned 70.4 mm**, `BAT_SENSE` 61.4, `REF_POL` 51.7, `REC_GATE_N` 50.6, `N_POL` 46.4. **Routing those as they stood would have knowingly built the defect PM-2 exists to prevent**, so the support network was moved beside its chain: **`LTC_GATE` 70.4 → 29.8, `BAT_SENSE` 61.4 → 24.3, `REF_POL` 51.7 → 9.7, `REC_GATE_N` 50.6 → 15.6, `N_POL` 46.4 → 8.3, `LTC_OV`/`LTC_UV` 28.2/15.0 → 8.0/9.1 mm.** **NO component value, threshold, topology or net changed, and the 1.5 A chain itself did not move.** **29 POWER TEST POINTS WERE ALSO RE-HOMED** — a test point 50 mm from its own net is not access, it is a stub, and on a 1.5 A net it is a stub that forces load current somewhere it should not go; `TP34` was **59 mm** from `J4` and is now **4.4 mm**. **WHY THE ROUTING FAILED:** a minimum-spanning-tree router drawing direct pad-to-pad segments is adequate inside a compact PM-1 cell and wrong across a board — it draws straight lines through other pads. On 64 nets it produced **505 DRC violations: 102 shorting items, 112 track crossings, 204 mask bridges, 45 clearance.** **It was reverted in full. Committing 102 electrical shorts into the authoritative board, on a task whose subject is the SAFETY-CRITICAL battery path, was not an option.** The next task needs an OBSTACLE-AWARE path search or verified hand polylines; the scope, widths, layer policy and intended topology are already settled in `pcb/FBV2_P2_POWER_ROUTING.md`. **B-34 RECOMPUTED FROM THE INTENDED GEOMETRY AND LABELLED AS AN ESTIMATE, NOT A MEASUREMENT: ≈ 355 mV / 532 mW at 1.5 A and ≈ 414 mV / 724 mW at 1.75 A**, of which the BQ25185 BATFET's 115 mΩ is the dominant term and copper is only 50.6 mΩ. **NOTHING IS CLEARLY UNSAFE, so the escalate-and-halt condition did NOT trigger** — but an estimate from an unrouted board cannot close a blocker, so **B-34 stays OPEN — PHYSICAL VALIDATION REQUIRED.** **One number dominates and is the recommendation for next time: `BAT_PROTECTED_P` at ≈ 71 mm is 69 % of the copper resistance on its own; widening it 1.00 → 1.50 mm takes copper from 50.6 to 38.9 mΩ** (PR-2). **EXIT STATE: ZERO tracks, ZERO signal vias, ZERO outer pours, 499 unrouted, DRC 1 (the `MK1` artefact of D-227, NOT suppressed), ERC 0 errors / 27 warnings with an identical histogram, 0 placement collisions, `p1_regression`, `dru_probe`, `netclass_probe` and `fork_equivalence` all PASS.** **NO PERCENTAGE: PCB routing stays 0 % and overall stays 74 %. A task asked to route the safety-critical battery path that did not route it has FAILED, and reporting it otherwise would be exactly the asserted-rather-than-measured progress the percentage rules exist to prevent.** | 2026-08-24 |

| D-245 | **`BAT_PROTECTED_P` GETS A LOCAL PER-NET WIDTH OVERRIDE: TARGET 1.50 mm, MINIMUM 1.20 mm. THE `BAT_MAIN` CLASS IS NOT CHANGED.** `BAT_CONNECTOR_P`, `BAT_RAW`, `BAT_MID` and `BAT_SENSE` keep the class target of 1.00 mm and the 0.60 mm floor, because none of them carries the pack current over anything like the same distance. **The arithmetic is the whole justification:** at ≈ 71 mm `BAT_PROTECTED_P` is the ONE long run PM-2 predicted would remain and is **≈ 69 % of the entire protection path's copper resistance on its own** — **34.9 mΩ at 1.00 mm against 23.3 mΩ at 1.50 mm**, taking path copper from ≈ 50.6 to ≈ 38.9 mΩ and the 1.5 A copper loss from 114 to 88 mW. Implemented as a scoped `.kicad_dru` rule conditioned on the net name alone, and as row **A2** of `pcb/FBV2_P2_NETCLASS_LEDGER.csv`. **NECKDOWN POLICY, AND IT IS A POLICY RATHER THAN A LOOPHOLE:** a fine-pitch land pattern cannot accept a 1.50 mm — or even a 0.60 mm — track. `U18` is an MSOP-10 on 0.50 mm pitch whose pad-to-pad gap is **0.20 mm**, so a short escape neck at the pad is mechanically unavoidable and is permitted **subject to four conditions carried in the rule text itself**: shortest length that clears the package; never a traverse; exact length and minimum width DOCUMENTED PER PAD; and no thermal-relief or single-via bottleneck. **The 1.20 mm figure is the TRUNK floor, not a licence for a narrow run** — necks are measured and reported individually in `pcb/FBV2_P2_POWER_ROUTING.md`, never waived in the rule file. | 2026-08-24 |
| D-246 | **FBV2-P2-002A FAILS: THE BATTERY / PROTECTION BLOCK IS NOT ROUTED, AND AGAIN NOTHING WAS COMMITTED AS COPPER.** 27 of 29 nets could not be brought to a DRC-clean state; the two that could — `Q2_CS` and `Q3_CS`, 5.35 mm each — were reverted with the rest rather than committed as an unrepresentative fragment. **PM-2 THEREFORE DOES NOT CLOSE: its status is PLACEMENT CORRECTED (approved, retained), FINAL CLOSURE PENDING DRC-CLEAN ROUTING.** **WHAT THIS TASK DID DELIVER IS THE METHOD, and that is what the next task actually needed.** §4 forbade MST routing, batch straight pad-to-pad routing and route-all-then-DRC; what replaced them is **OBSTACLE-AWARE A* ON A 0.10 mm GRID** rebuilt per connection from the real board — every foreign pad, every track already laid, every track-forbidding rule area including the one embedded in `U1`'s own footprint, and the board edge, **each inflated by (clearance + width/2) so a legal grid path is a legal track** — plus **PAD-ESCAPE NECKING**, because a 1.00 mm `BAT_MAIN` trunk physically cannot land in `U18`'s 0.20 mm pad gaps, plus **PER-NET DRC GATING that reverts any net introducing any new violation of any class before the next net starts.** Violations never accumulate. **That refusal to keep unclean copper is precisely the behaviour FBV2-P2-001 lacked, and it worked: the board still carries ZERO tracks and ZERO signal vias.** **THREE ROUTER DEFECTS REMAIN, ALL NAMED AND ALL LOCAL:** (1) `track_dangling` on 17 nets — the escape neck and the trunk do not register as joined at the launch point, a geometry bug in the emitter rather than an electrical problem, but a dangling end must never be committed; (2) `track_width` on `BAT_MID` and `BAT_SENSE` — the neck width is derived from the pad's short dimension and on an SO-8 falls below the `BAT_MAIN` 0.60 mm floor, so **the rule is right and the router is wrong**; (3) `shorting_items` on six nets — the neck is laid without consulting the obstacle grid, so it can cross a neighbour even where the trunk cannot. **None of these is a reason to change placement, widths or topology.** **TWO CONNECTIONS HAVE NO PATH AT TRUNK WIDTH** — `R86.2 → R89.1` and `TP15.1 → U14.2`, both in the dense left-margin resistor column; they need either a finer routing grid there or a ≤ 2 mm placement nudge, **surfaced and NOT taken** per §9. **B-34 UNIT CONFUSION CORRECTED as §16 asked: the copper estimate is ≈ 50.6 mΩ, NOT 525 mΩ.** With `F1` ≈ 25 mΩ, `Q2`+`Q3` ≈ 46 mΩ and the BQ25185 BATFET's **115 mΩ**, the path is **≈ 355 mV / 532 mW at 1.5 A** and **≈ 414 mV / 724 mW at 1.75 A**; D-245 takes the copper term to ≈ 38.9 mΩ once the net is actually routed. **B-34 stays OPEN — PHYSICAL VALIDATION REQUIRED**; nothing is clearly unsafe. **EXIT STATE: ZERO tracks, ZERO signal vias, ZERO outer pours, 499 unrouted, ZERO accidental out-of-scope copper, DRC 1 (the `MK1` artefact of D-227, NOT suppressed), ERC 0 errors / 27 warnings, In1 one GND zone of one island, `p1_regression` PASS re-verifying the FBV2-P2-001 placement, `dru_probe` PASS at 65 rules, `netclass_probe` and `fork_equivalence` PASS.** **NO PERCENTAGE: PCB routing stays 0 %, overall stays 74 %.** | 2026-08-24 |
| D-247 | **FBV2-P2-002B: THE ROUTING HARNESS IS QUALIFIED. ALL THREE NAMED ROUTER DEFECTS ARE FIXED AND PROVED FIXED ON REAL FULL BETA v2 GEOMETRY, AND NO COPPER WAS COMMITTED — the authoritative PCB is byte-identical to `8b9efba`.** **THE SCRATCH-ENVIRONMENT BUG IS CLOSED FIRST, because it invalidated the previous task's numbers:** a `.kicad_pcb` copied on its own loses `.kicad_dru`, the `.kicad_pro` netclasses and `fp-lib-table`, and DRC then measures against KiCad DEFAULTS — which is where FBV2-P2-002A's phantom `clearance: 73, lib_footprint_issues: 17` came from. Every board in this task is a COMPLETE PROJECT COPY and the harness refuses to run DRC without all five context files present; authoritative and scratch baselines are both `{solder_mask_bridge: 1, unconnected_items: 499}`, identical. **PHANTOM DRC OFFSET: NONE.** **THE FIXES.** `track_dangling` had TWO causes and the coordinate one was the smaller: the emitter is now INTEGER NANOMETRES END TO END so a neck's end and a trunk's start are the SAME INTEGER, but the bigger cause was that **the old router never checked which layer a pad was on** and would start a `B.Cu` track at the centre of an `F.Cu`-only pad. `track_width` now obeys one rule — **THE ROUTING RULE MINIMUM WINS**: the escape ladder stops at the applicable floor, never derives a width from a pad's short dimension, and where nothing legal exists the pad is classified **NO LEGAL ESCAPE** and NOTHING IS EMITTED. `shorting_items` is fixed by giving the neck the SAME obstacle set as the trunk — foreign pads as true rotated rounded rectangles, tracks as capsules, every drilled hole on every layer, rule areas, board edge — checked ANALYTICALLY, so a short neck gets a stricter test than the trunk, not a weaker one. **A FOURTH DEFECT WAS FOUND THAT WAS NOT ON THE LIST:** A* proves that GRID CELLS are clear but the emitted track is a CONTINUOUS SEGMENT between them and can pass ~0.75 of a cell closer to an obstacle, which duly produced `actual 0.1718 mm` against a 0.2000 mm rule; every obstacle now carries a **0.75 × grid GUARD BAND**, and the honest price is that `R86.2 → R89.1` now needs the local 0.025 mm grid. **RESULT: six of eight qualification cases route with ZERO new DRC violations of any class, ONE connected copper component after a real save and reload, NO foreign pad in the cluster, and the ratsnest falling by EXACTLY ONE EDGE PER CONNECTION** — `Q2_CS` 5.500 mm, `Q3_CS` 5.500 mm, `BAT_MID` 24.860 mm, `LTC_GATE` 66.982 mm, `LTC_OV` 15.179 mm, `R86.2 → R89.1` 45.274 mm. **NEW SHORTS ACROSS EVERY TEST: ZERO.** **PR-5 AND PR-6 ARE CLOSED.** Regression-tested for good by `hardware/beta-v2/checks/router_regression.py` (22 assertions, six guards, ALL PASS), with the router committed beside it as `qrouter.py`. **SECTION 19 SCAN: NO NATIVE INSTALLED ROUTING MECHANISM EXISTS** — `kicad-cli pcb` has no routing subcommand, `pcbnew` exposes no scriptable PNS, `kipy` is not installed, Freerouting is not installed and would be the wrong tool anyway because Specctra DSN carries netclass width and clearance but NOT custom `.kicad_dru` rules. **KEEP THE QUALIFIED HARNESS.** **NO PERCENTAGE: PCB routing stays 0 %, overall stays 74 %.** | 2026-08-24 |
| D-248 | **OPEN — CTO RULING REQUIRED (PR-7). FIVE PADS CANNOT LEGALLY ACCEPT THE WIDTH THEIR RULES DEMAND, AND AS WRITTEN **D-245 MAKES `BAT_PROTECTED_P` UNROUTABLE**.** Bisected to 5 µm against the project's own clearances, with the closed-form arithmetic matching the measurement to the bisection step: **`U18.9` 0.245 mm against a 0.600 mm floor; `U18.8` 0.245 mm against 1.200 mm; `U14.2` and `U14.3` 0.295 mm against 1.200 mm; `U11.2` 0.195 mm against 1.200 mm.** **THE PROBLEM IS RULE SCOPE, NOT THE ROUTER AND NOT THE PLACEMENT.** `BAT_MAIN`'s 0.60 mm floor and D-245's 1.20 mm floor are written as WHOLE-NET constraints, but `BAT_SENSE` is the LTC4368's **Kelvin sense line** carrying microamps into a high-impedance input, and `BAT_PROTECTED_P` carries the full pack current AND ALSO feeds the MAX17048's fuel-gauge sense input (`U14.2`/`U14.3`) and a test point (`TP15.1`), neither of which carries any current at all. D-245's comment already anticipates a neck exception; **the rule BODY does not contain one**, so DRC enforces 1.20 mm on the fuel-gauge tap. **NOTHING IN `.kicad_dru` WAS TOUCHED** — §6 said do not invent a rule exception and §17 said do not hide it by weakening rules. **WHAT THE TRUNK ACTUALLY COSTS, MEASURED:** `R75.2 → U18.8 → D9.1 → C25.1` routes at **1.50 mm in 85.274 mm, 22 segments, B.Cu, ZERO vias**, every segment at full width except the two mandatory 0.245 mm `U18.8` escapes; past `C25.1` the charger cluster caps the trunk at 0.60 mm and `U11.2`'s own land pattern caps it at 0.195 mm. **AND D-245'S ARITHMETIC NEEDS CORRECTING:** it used the **71 mm placement span**, but the measured route is **85.3 mm** because copper goes around things, and the unavoidable `U18.8` neck adds **≈ 7.8 mΩ in 3.9 mm of copper**. `BAT_PROTECTED_P` as actually routable is **≈ 35.7 mΩ**, so the net gains **≈ 6 mΩ rather than the predicted ≈ 11.7 mΩ**. That does not argue against D-245; it argues that the neck exception, when ruled, should carry a **bounded length and a stated resistance budget** rather than being left open. **NO PLACEMENT MOVE IS PROPOSED:** `R86.2 → R89.1` routes legally at 1.00 mm (45.274 mm) and at 0.60 mm (16.848 mm), and `TP15.1 → U14.2` routes legally at 0.20 mm (8.82 mm) — moving `TP15` would not change the rule floor by one micron and `U14` was never a candidate, so the ≤ 2.0 mm allowance was NOT spent. **ALSO SURFACED (PR-8):** `TP34.1` is an **`F.Cu`-only pad on the otherwise-`B.Cu` net `BAT_CONNECTOR_P`** — the only face-split net in the block; it needs a via and an `F.Cu` stub or the test point flipped to `B.Cu`. | 2026-08-24 |
| D-249 | **WIDTH IS A PATH ROLE, NOT A PROPERTY OF THE NET NAME. THE WHOLE-NET FORM OF D-245 IS SUPERSEDED.** D-245's INTENT stands — the long high-current `BAT_PROTECTED_P` trunk is **1.50 mm target / 1.20 mm floor** — but its implementation applied that floor to every segment carrying the net name, and the same net also feeds the MAX17048 fuel-gauge sense input, the LTC4368 `VOUT` sense input and a test point. **As written it made `BAT_PROTECTED_P` UNROUTABLE.** **THE MECHANISM:** the trunk floor applies to the WHOLE net by default and is relaxed ONLY inside a named rule area bounding one approved branch, through `enclosedByArea()`, which requires the ENTIRE track to be inside. **THE AREA RULES LIVE IN A NEW SECTION 10b AT THE VERY END OF `.kicad_dru`, AND THAT POSITION IS LOAD-BEARING:** §9 of that file already records that the pad-escape necking and land-pattern blocks must come last to beat the section-5 rail widths, and these must in turn beat THOSE. Placed in 5b they were silently overridden by *Pad-escape necking — width, fine-pitch power packages*. Within 10b the rules run **widest first, narrowest last**, so where areas overlap the lower floor governs. **RULED WIDTHS:** trunk `R75 → D9 → U11.2` **1.50/1.20**; `U11.2` **0.20 mm** (TI's own DLH0010A land is 0.2 mm pads on 0.4 mm pitch — **the package is the bottleneck, not the rule**, and JLCPCB's live capability page gives 0.09/0.09 mm on 1 oz multilayer, so **the 0.19 mm exception was NOT needed**); `U18.8` **0.20**; `U18.9` Kelvin **0.20**; `TP15` **0.20**; `U14.2`/`U14.3` **0.15 mm — A DEVIATION FROM THE RULED 0.20 mm, BECAUSE 0.20 mm IS GEOMETRICALLY IMPOSSIBLE THERE BY 5 MICRONS**: `U14` sits 1.245 mm from the west edge with its pin row facing it, and a track in that strip needs its centre at x ≥ 0.500 + w/2 AND x ≤ 0.695 − w/2, solvable only for w ≤ 0.195 mm. **`U18.1` (LTC4368 `VIN`) was ALSO classified a microamp tap at 0.20 mm** — §5 did not list it, and the LTC4368 is a CONTROLLER whose pack current flows through `Q2`/`Q3`, never through the IC. | 2026-08-24 |
| D-250 | **FBV2-P2-002C FAILS: PHASE A DID NOT COMPLETE, SO PHASE B WAS NOT RUN AND THE AUTHORITATIVE PCB IS BYTE-IDENTICAL TO `a52977e` — ZERO TRACKS, ZERO SIGNAL VIAS.** **First unresolved connection: `LTC_GATE` `Q2.2 → TP17.1`.** Twenty-seven connections routed and COEXISTED cleanly on one scratch board with zero new DRC violations of any class at every step — the whole high-current battery path, both R75 Kelvin branches, the U11.2 flared escape, the fuel-gauge taps and the LTC gate drive — ratsnest 781 → 749. Then the LTC test-point stub could not be reached on either layer at any legal width down to the board's 0.15 mm minimum, and the dead-cell / recovery network was never reached. §19 says do not touch the authoritative board, so it was not touched. **MEASURED, AND THE NUMBERS ARE THE POINT:** `BAT_PROTECTED_P` trunk **94.5 mm, 1.50 mm, B.Cu, ZERO vias**; the `U11.2` escape is a **0.20 mm neck 0.575 mm long** flaring to 1.20 mm over 4.738 mm with **no via and no thermal relief**; the R75 Kelvin pair is **7.327 mm (`U18.9`) against 14.588 mm (`U18.8`), mismatch 7.261 mm**, both 0.20 mm on B.Cu with zero vias and both originating at the correct R75 pad; **the only vias in the whole attempt are 4** — two pairs, on the `BAT_SENSE` `Q3 → R75` trunk and the TP20 stub, because the west margin cannot carry both a 1.00 mm `BAT_SENSE` and a 1.20 mm `BAT_PROTECTED_P` past R75 on B.Cu alone. **B-34 RECOMPUTED FROM REAL COPPER AND IT IS WORSE THAN THE ESTIMATE: routed copper is ≈ 75.0 mΩ, not the ≈ 50.6 mΩ assumed**, giving **≈ 392 mV / 588 mW at 1.5 A** and **≈ 457 mV / 800 mW at 1.75 A**. The trunk is at its ruled width; the excess is in `BAT_MID` and `BAT_SENSE`, which the corridors forced to 0.80 mm instead of the 1.00 mm class target. **B-34 STAYS OPEN — PHYSICAL VALIDATION REQUIRED.** **PM-2 DOES NOT CLOSE**: §22 requires a DRC-clean routed block. **AND ONE HONEST WEAKNESS:** §7 asks that the construction make it IMPOSSIBLE for a long run to masquerade as a branch, and the auto-generated areas are bounding boxes of their own routes — three are tight, but the C58 tap's box is **67 × 23 mm at a 0.80 mm floor**, which is a real hole in the trunk rule. The fix is a centre-line corridor rather than a bounding box (**PR-11**). **NO PERCENTAGE: PCB routing stays 0 %, overall stays 74 %.** | 2026-08-24 |
| D-251 | **FBV2-P2-002E FAILS: PHASE A DID NOT COMPLETE, SO PHASE B WAS NOT RUN AND THE AUTHORITATIVE PCB IS BYTE-IDENTICAL TO `e09eb35` — ZERO TRACKS, ZERO SIGNAL VIAS.** **First unresolved FUNCTIONAL connection by §8's own numbering: `BAT_RAW` `R80.1 → Q2.7`** — the LTC4368 divider chain `{R77.1,R79.1,R80.1,U18.1}` never joins the raw battery node; **the most consequential is `LTC_GATE` `U18.10 → Q3.4`**, which leaves the gate net in two pieces `{U18.10,R76.1,TP17.1}` and `{Q2.2,Q2.4,Q3.2,Q3.4}` so the LTC4368 GATE output is not connected to the FETs it drives. **60 connections coexisted on ONE scratch board with ZERO new DRC violations of any class at every step, ratsnest 781 → 718 (−63), against the previous best of −32** — the whole high-current path closed end to end `J4→F1→Q2→Q3→R75→D9→U11.2`, both R75 Kelvin branches, the U11.2 flare, the MAX17048 taps, and **the dead-cell / recovery network routed for the first time**. **MEASURED:** `BAT_PROTECTED_P` trunk `R75.2→D9.1` **20.416 mm at its 1.50 mm TARGET on B.Cu with ZERO vias** (§8's trunk-first order is what buys this — with the pin field first the same pad returned NO_LEGAL_ESCAPE at 0 s); `U11.2` escape **0.20 mm neck 0.575 mm** flaring monotonically to 1.50 mm, **no via, no thermal relief, 4.214 mΩ, sub-1.20 mm length 4.737 mm against §5's 5.25 mm cap — INSIDE IT**; `BAT_SENSE` load **1.00 mm** across its F.Cu hop (PR-21 — it was silently dropping to 0.60 mm to buy the hop); TP17 stub **5.741 mm, 0 vias**, down from the 24.1 mm second-route it wanted; R75 Kelvin mismatch **20.620 mm** (3.179 vs 23.799), the direct cost of the trunk taking its corridor first. **FIVE HARNESS DEFECTS FIXED, ONE OF THEM A SEGMENTATION FAULT:** `split_at` shifted `qb.laid` under a live mark, so `revert` removed TRUNK copper and a second revert called `BOARD::Remove` on a detached item — exit 139 at `TP34.1` after 55 connections (PR-15, now guarded by `router_regression` **G7**); the item budget starved the F.Cu fallback and made the router look nondeterministic (PR-20); trunks lost width to buy a hop (PR-21); the already-connected check read a FILE that still held reverted copper and skipped connections that had never been routed (PR-22); §9's 10 mm stub cap was being applied to every test point instead of TP17 (PR-16). **15 IN-SCOPE CONNECTIONS REMAIN OPEN AND NINE OF THEM FAILED `NO_LEGAL_ESCAPE` AT 0 s** — the pad cannot emit a legal track at any width on any layer before pathfinding is even attempted. **THAT IS A PLACEMENT FINDING, NOT A ROUTER FINDING: U18 escapes 6 of its 8 signal pins here, 7 at best across four orderings, because its whole north row shares one ~2.2 mm corridor between U18 (x≤4.83) and the R76/R77/R78/R79 divider wall (x≥7.00) (PR-25).** §11 forbids weakening the architecture to finish, so nothing was dropped, re-aimed or re-valued: D10/D11 stay separate matched parts and the ratiometric topology, thresholds and values are untouched. **B-34 IS NOT RECALCULATED AUTHORITATIVELY and STAYS OPEN — physical validation required**; scratch copper is ≈ 65 mΩ (≈ 98 mV / 146 mW at 1.5 A, ≈ 114 mV / 199 mW at 1.75 A), better than 002C's ≈ 75 mΩ. **PM-2 DOES NOT CLOSE**: §16 requires a routed, clean, AUTHORITATIVE block. **Longest single route 245.9 s, none over 600 s, no watchdog intervention needed in the final run.** **NO PERCENTAGE: PCB routing stays 0 %, overall stays 74 %.** | 2026-08-25 |
| D-252 | **FBV2-P2-002F FAILS ON SECTION 14's NO-PARTIAL-PASS RULE, AND THE PLACEMENT QUESTION IT WAS SET TO ANSWER IS ANSWERED.** **The authoritative PCB is byte-identical to `24f6611` - zero tracks, zero signal vias - and THE PLACEMENT ECO IS NOT APPLIED TO IT** (section 23 forbids committing an unproven placement; `place_p2_002f.py` is committed as the searched, gated, reproducible result, applied to nothing). **PR-25 CLOSED: U18 rotates 90 -> 180 and moves (3.000, 72.400) -> (8.000, 65.250)**, chosen from a MEASURED search - 13 284 poses, 2 490 clearing collision and the section 4 Kelvin envelope, 1 331 keeping both Kelvin branches <= 10 mm with a legal 1.50 mm trunk, 20 fully scored - and the winner re-confirmed by ROUTING all eight pins with the real router against the real trunk, chain and flare. **It escapes 8 of 8 and ROUTES 8 of 8**, against 6 of 8 at 002E. The R76..R83 divider WALL is dissolved: every part is now placed BY THE U18 PIN IT SERVES. **PR-28 CLOSED: R75 Kelvin mismatch 20.620 -> 2.454 mm** (5.254 / 7.708, both <= 10 mm) **and `U18.1` VIN 32.204 -> 1.850 mm.** **PR-26 CLOSED WITHOUT A VIA: `Q3_CS` 5.500 mm on B.Cu, ZERO vias**, and section 5's authorised layer drop was MEASURED AND DECLINED - four variants of the same prefix show CS-before-gate closes all twelve at Q3, that moving Q3 1 mm loses BOTH CS nets, and that the authorised drop CANNOT EVEN START because `Q3.3` has no B.Cu escape left once the gate has routed. The whole price is 2.188 mm on one gate link, and `LTC_GATE` - which 002E left in TWO PIECES - is now ONE CONNECTED COMPONENT. **This reverses section 9's gate-before-CS order, recorded as a deliberate deviation taken to satisfy section 5's own preferred result.** **PR-29 CLOSED: MAX17048 branch 31.228 -> 6.387 mm and U14 DID NOT MOVE** - TP15 to (1.800, 79.900), chosen by measuring seven candidate sites with the real router. **PR-27 CLOSED TO THE ABSOLUTE MAX, NOT THE TARGET: worst megohm node 64.01 -> 18.43 mm** against section 6's 20 mm; `REC_DIODE_IN` 64.01 -> 7.44, `VREC_VCC` 47.15 -> 7.51, `VREF_TOP` 48.58 -> 8.15. **Eleven of fifteen are inside the 15 mm target; the four that are not are UNCHANGED from 002E and bounded by Q5..Q9, which this ECO was not authorised to move - CARRIED FORWARD, not closed.** An earlier, more aggressive version reached 14.25 mm inside the target and **made the cluster UNROUTABLE**; it was withdrawn. **MEASURED ON SCRATCH: 70 connections, ratsnest 781 -> 709 (-72)** against 002E's 60 and -63, **DRC identical to the baseline at every single step, zero out-of-scope copper, 23 of 29 in-scope nets single connected components.** Trunk **17.625 mm at its 1.50 mm target, ZERO vias**; `U11.2` neck **0.575 mm**, monotonic, no via, no thermal relief, 4.214 mOhm. **WHY IT STILL FAILS:** six nets sit in two islands and four of those are ONE STRANDED PAD - `R80.1`, `U19.2`, `U19.3` - plus the `{TP15, U14.2, U14.3}` MAX17048 island (**PR-34, OPEN**). `U19.2`/`U19.3` are a U19 placement question of exactly the kind PR-25 answered for U18. **PR-35 OPEN (harness):** a test-point stub outside its own generated corridor is judged against the D-249 trunk floor. **FOUR NEW GENERAL HARNESS RULINGS, none board-specific: PR-30** fine-pitch slack ties break on HOW MANY WAYS OUT a pad still has; **PR-31** a partner must sit on the side its pin faces or the route WRAPS the package (`U18.10` cost 18.4 mm and took `U18.2`'s only lane); **PR-32** re-measure before EVERY fine-pitch pin; **PR-33** U19 is a fine-pitch pin field too and had no measured ordering at all. **AND THE LESSON: an escape proof measures a 0.5 mm STUB and a connection is a ROUTE.** Four placements passed the section 12 gate - including its section 3C simultaneity test, 49 escapes laid at once with none lost - and then failed Phase A: crossing targets, stacked targets, a compaction that deleted its own channels, and parts on the far side of J4 where a Euclidean metric cannot see a 6 mm connector. The fix was not a better proxy but a worse-scaling one - route the pin field with the REAL router against the copper the plan lays first (`checks/ring_probe_002f.py`). **B-34 NOT CLOSED and NOT recalculated authoritatively - physical validation required**; scratch pack-current copper approximately 64.9 mOhm (approximately 97 mV / 146 mW at 1.5 A, approximately 114 mV / 199 mW at 1.75 A), excluding F1, Q2/Q3 R_DS(on), the BQ25185 BATFET, contact resistance and temperature rise. **PM-2 DOES NOT CLOSE.** **NO PERCENTAGE: PCB routing stays 0 %, overall stays 74 %.** | 2026-08-25 |
| D-253 | **FBV2-P2-002F RESUMED. STILL FAIL; the authoritative PCB is STILL byte-identical to `24f6611` and the placement ECO is STILL NOT APPLIED TO IT.** Phase A run 8: **71 connections, ratsnest 781 -> 708 (-73), DRC identical to the baseline at every step, zero out-of-scope copper, 24 of 29 in-scope nets single connected components** (was 23). **PR-37 CLOSED (and it closes PR-35): the closure stage was handing every `BAT_PROTECTED_P` pad the TRUNK ladder [1.50, 1.20], ignoring D-249's per-pad rulings**, so `U14.2`/`U14.3` - ruled 0.15 mm because 0.20 mm is geometrically impossible there by five microns - were asked for 1.20 mm on a 0.70 x 0.30 mm pad and returned NO_LEGAL_ESCAPE. The pads escape fine at 0.15 mm (measured) and the MAX17048 island sat **10.862 mm from `C58.1`**; it was never a corridor problem. `BAT_PROTECTED_P` is now ONE component. **PR-38 CLOSED: `order_tight` measured only the FIRST-NAMED pad of a connection.** U18's pin field is written pin-first so that worked; the dead-cell block is a minimum spanning tree, so `TP24.1 -> U19.2` measured a 1.0 mm test pad with THREE ways out and never looked at the SOT-23-8 pin with ONE. A connection is as tight as its tighter end. `REF_POL` closed. **PR-36 APPLIED but was not the cause** - the microamp taps now precede the two cross-board trip runs (correct by PR-18's own scarcity argument, kept). **PR-39 OPEN, AND IT IS THE MOST CONSEQUENTIAL DEFECT FOUND THIS SESSION: A CONNECTION CAN REPORT A LENGTH AND A WIDTH, AND APPEAR IN THE JOURNAL, HAVING BEEN BUILT TO A DIFFERENT ENDPOINT THAN THE ONE IT NAMES.** `TAP BAT_RAW R79.1 -> R80.1 5.276 mm` spans pads that are **12.030 mm** apart - 43.9 % of the straight line - and puts **ZERO** `BAT_RAW` track endpoints inside `R80.1`'s pad. `run()`'s node fallback silently retargets to the nearest point on the net's own copper while the printed line and the journal keep the original pad name, so a 'successful' connection laid a REDUNDANT LOOP and left the pad alone. **Section 14 must therefore be judged on CONNECTIVITY, never on the routed count, and a section 17 replay would faithfully reproduce a connection that does not exist.** **CORRECTION, RECORDED AS ONE: an interim finding that U19 does not need to move is WITHDRAWN.** It rested on all seven U19 signal pins escaping on the bare board and surviving the section 3C simultaneity test - which is precisely the inference this task has already shown to be unsound. Run 8 moved the casualty from `U19.2`/`U19.3` to `U19.3`/`U19.8`, which is PR-25's own signature. **PR-34 STANDS AS ORIGINALLY WRITTEN: U19 needs the measured placement treatment PR-25 gave U18, and so do R80/R81.** **WHAT REMAINS: three pads - `R80.1`, `U19.3`, `U19.8` - all west-margin placement**, plus two test points (`TP18.1`, `TP19.1`) which escape with 8 and 5 directions respectively and were simply never reached before the run ended. `U19.8 -> C60.1` is NO_PATH, not NO_LEGAL_ESCAPE: the pads are **2.668 mm** apart and the 0.93 mm gap between U19 and C60 is full. **B-34 unchanged and still OPEN. PM-2 does not close. NO PERCENTAGE: PCB routing stays 0 %, overall stays 74 %.** | 2026-08-25 |
| D-254 | **FBV2-P2-002G / 002H FAIL. The authoritative PCB is byte-identical to `984423c` (md5 `a908cedfa9f9410aab327d8bd55b9f45`) - zero signal tracks, zero signal vias, In1.Cu GND plane intact - and THE PLACEMENT ECO IS STILL NOT APPLIED TO IT.** Rollback tag `beta-v2-p2-battery-pre-authoritative` created at `984423c` and pushed. **PR-39 CLOSED, and it is the ruling that makes every earlier routing number re-interpretable: ROUTER SUCCESS NOW MEANS THE PADS THAT WERE REQUESTED ARE IN ONE CONNECTED COMPONENT.** `run()`'s three fallbacks could each replace the requested endpoint while the printed line, the journal and the routed count kept the original pad name; `TAP BAT_RAW R79.1 -> R80.1 5.276 mm` spanned pads **12.030 mm** apart and left **zero** `BAT_RAW` track endpoints inside `R80.1`. A retarget that does not join what was asked for is now REVERTED, prints `NOT_CONNECTED`, and does not count; the journal records requested and actual endpoints separately. Pinned by six regression cases **G8-A..G8-F, all passing**, alongside the existing G1..G7. **PR-40 RULED AND IMPLEMENTED: a candidate is NOT route-qualified by bare-board escape, by simultaneous stub escape, or by reduced-prefix routing** - each has now been wrong at least once, most sharply when a reduced-prefix probe passed C00 at U19 7/7 with `R80.1` CONNECTED and the full prefix returned `R80.1` NOT_CONNECTED, `D12.1 -> R77.1` NOT_CONNECTED and `LTC_SHDN U18.6 -> Q4.3` NO_PATH. `AQROOT_PROBE_PASS1` therefore runs the real driver in the real order and stops after pass 1; **its honest cost is about 40 minutes per candidate**, so the efficient structure is to run Phase A per candidate family and judge it by the ledger, not to probe first. **CONNECTIVITY IS THE PRIMARY TRUTH (`checks/net_ledger.py`); the routed count is a secondary metric** - 002F reported 70 and 71 connections on boards with four pads in their own islands. **PR-41 CLOSED AND VALIDATED: the closure stage was giving every `BAT_RAW` pad the BAT_MAIN trunk ladder [1.00, 0.80, 0.60] because `BAT_RAW` is a WIDE net**, so the LTC4368 divider chain - ruled 0.20 mm by D-249 and routed as TAPs everywhere else - was asked for 0.60 mm minimum. This is PR-37's defect one net over. With PR-41 applied a full Phase A produced **zero NO_LEGAL_ESCAPE board-wide**; `R80.1 -> (node)` became **NO_PATH**, which is a different and truer failure. **PR-41 IS NOT SUFFICIENT.** **PR-42 CLOSED (harness, my own defect): the joint U19+R80/R81 search carried a stray `break`, so all eight 'joint' candidates shared ONE R80/R81 pose** - only U19 was ever varied, every candidate failed `R80.1` identically, and R80's pose had never actually been searched. Fixed, it yields **six distinct R80 poses**; and because U19's box (y 8..34) and the R80/R81 box (y 56..78) are disjoint and share no net, the two are INDEPENDENT AXES and are swept separately rather than as a fake cross-product. **MEASURED, AND IT REVERSES PART OF PR-34: a bare-board flood - used strictly as a NEGATIVE test per PR-40 - shows BOTH bridges reach the battery node at 0.20 mm** (`R80.1` and `D12.1` each reach `Q2.7`, `Q2.8`, `F1.2`, `C59.1`). **The corridor EXISTS, so the failure is CONTENTION, not geometry, and no R80 pose is required to make this routable.** **PR-43 RAISED AND APPLIED, UNPROVEN: SCHEDULE BY CORRIDOR SCARCITY, NOT BY NET ROLE.** `R80.1 -> Q2.7` (21.5 mm) and `D12.1 -> R77.1` (45.5 mm) are the divider chain's only link to the battery node and their only corridor is the west margin at x 4..10, yet being `TAP` by role they were scheduled after the trunk, the chain AND U18's eight-pin field, which fill exactly that margin. They now go with the chain, by the same scarcity argument PR-18 used for the trunk; the genuinely local taps stay put. **Its Phase A was killed before reaching the first bridge, so PR-43 is UNPROVEN and is the first thing the next task should run.** **PHASE A NOT PASSED. PHASE B NOT RUN. NO MANIFEST. NO AUTHORITATIVE COPPER. `U19` still reaches 5 of 7 under the full prefix and `U19.8 -> C60.1` is NO_PATH across a 2.668 mm gap - that is the part of PR-34 that survives. B-34 REMAINS OPEN; physical first-article validation is still mandatory and no loss figure is recalculated authoritatively. NO PERCENTAGE: PCB routing stays 0 %, overall Full Beta v2 stays 74 %. No progress was earned and none is claimed.** | 2026-08-25 |
| D-255 | **FBV2-P2-002I FAILS ON SECTION 5 CASE D - A PROTECTED PATH REGRESSED - AND IT ANSWERS PR-43 IN BOTH DIRECTIONS. The authoritative PCB is byte-identical to `984423c` (md5 `a908cedfa9f9410aab327d8bd55b9f45`), zero signal tracks, zero signal vias, In1.Cu one-island GND intact, placement ECO NOT applied.** Preflight all PASS: `p1_regression`, `router_regression` (34 checks incl. G8-A..F), `dru_probe`, `netclass_probe`, `fork_equivalence`; DRC baseline 1 `solder_mask_bridge` / 499 unconnected / parity 0; ERC 0 severity-error. **PR-43 WORKS AND CLOSES `BAT_RAW` WITH NO PLACEMENT CHANGE AT ALL: 11 of its 12 pads become ONE island - `R80.1` CONNECTED, `D12.1` CONNECTED - and `LTC_SHDN`, which the full prefix had returned NO_PATH, CLOSES TOO.** It also **costs U18 two pins: 8 of 8 -> 6 of 8**, `U18.7` NO_LEGAL_ESCAPE (`LTC4368_FAULT_N`) and `U18.10` NO_PATH (`LTC_GATE`), both named in section 9. **THE DECISIVE MEASUREMENT: THE COPPER BOXING THOSE TWO PADS IS NOT `BAT_RAW`.** Within 1.2 mm of `U18.7` sit `LTC_SHDN` at 0.500 mm and `BAT_PROTECTED_P` at 0.500 mm; within 1.2 mm of `U18.10` sit `BAT_SENSE` at 0.500 and 0.986 mm. No `BAT_RAW` copper is near either. The bridges did not take U18's lanes - **they unblocked `LTC_SHDN`, whose new route then took the lane `U18.7` needed.** **So the failure is CAPACITY, not geometry, not width, and not ordering: the west margin must carry the 1.50 mm trunk, `BAT_SENSE`, `BAT_MID`, both `BAT_RAW` bridges, `LTC_SHDN` and U18's north row, and whichever contender is scheduled last is the one that fails. BOTH ORDERINGS SCORE 24 OF 29. REORDERING MOVES THE CASUALTY; IT DOES NOT REMOVE IT.** **PR-43 IS THEREFORE FLAGGED, NOT ADOPTED** (`AQROOT_PR43=1`); the default tree keeps the ordering that gives U18 8 of 8, so neither measured result is lost and the default is not silently regressed. Adopting it would trade two protected U18 pins for `BAT_RAW` and `LTC_SHDN`, and that trade is a CTO call. **WHAT IMPROVED AND MUST NOT BE LOST: Kelvin 4.464 / 4.464 mm, MISMATCH 0.000 mm** (002F: 5.254 / 7.708, 2.454) and **`U18.1` VIN 1.752 mm** (002F: 1.850). **HELD: `BAT_PROTECTED_P` 146.567 mm ONE island, ZERO vias, carrying 1.50 mm; `Q3_CS` 7.764 mm ZERO vias; `Q2_CS` 5.400 mm ZERO vias; Q3 GATE pair connected; `U11.2` neck 0.20 mm, no via; `U14` branch and `TP15` connected; zero out-of-scope copper; DRC classes identical to baseline.** **OPEN: `U18.7`, `U18.10`, `U19.3` (N_POL), and four test points `TP16.1`/`TP18.1`/`TP19.1`/`TP20.1`.** **U19 SEARCH NOT PERFORMED - section 6 requires Case C and this is Case D.** **CTO DECISION REQUIRED, three candidates: (1) move `R80`/`R81` out of U18's north lanes - R80's pose has still never been searched and six distinct poses are already generated; (2) concede one via to `LTC4368_FAULT_N` or `LTC_GATE`, which already carry two each, rather than to the zero-via `Q3_CS` / `BAT_PROTECTED_P`; (3) accept the four test points open, which does not fix `U18.7`/`U18.10`. RECOMMENDED: (1) with (2) in reserve - it needs no rule concession and the same run would answer the U19 question in the same margin.** **Phase A FAIL (24 of 29). Phase B NOT RUN. No manifest. No authoritative copper. B-34 REMAINS OPEN. NO PERCENTAGE: PCB routing stays 0 %, overall Full Beta v2 stays 74 %.** | 2026-08-26 |
| D-256 | **FBV2-P2-002J FAILS, AND IT CLOSES THE FIRST LEVER OF D-255: MOVING R80/R81 IS NOT THE ANSWER. The authoritative PCB is byte-identical to `984423c` (md5 `a908cedfa9f9410aab327d8bd55b9f45`), zero signal tracks, zero signal vias, placement ECO NOT applied.** Preflight all PASS. **A NEW AND VALIDATED INSTRUMENT: the section 5 local screen (`AQROOT_LOCAL=R80`) lays ONLY the west-margin prefix - trunk, BAT_MAIN chain, PR-43 bridges, U18 eight-pin field, 19 named connections - and reproduces D-255 EXACTLY (U18 6/8, open `U18.7` and `U18.10`, `R80.1` and `D12.1` connected) in 471 s against roughly two hours, a 15x saving.** It is sound because the copper that boxes `U18.7` is the `LTC_SHDN` `U18.6 -> R80.2` segment, which lives INSIDE the U18 pin field between two adjacent pins of the same package; it needs no cross-board copper to appear. The screen is CONSERVATIVE - it omits closure, so an open pin is not a definitive reject, but a connected pin is genuinely connected. **SIX DISTINCT R80 POSES SCREENED, PLUS THE CONTROL. `R80.1` and `D12.1` stayed CONNECTED IN EVERY ONE - the PR-43 result does not depend on the R80 pose. NO CANDIDATE REACHED 8/8.** K1/K2/K4 reach 7/8 open `U18.10`; K3 7/8 open `U18.6`; K5 5/8; **K6 (R80 8.000, 68.000 rot180; R81 5.500, 70.500 rot90) is the only one to connect BOTH D-255 casualties**, opening `U18.3` instead. **THE CASUALTY MOVES; IT DOES NOT DISAPPEAR - the D-255 signature, now reproduced across seven placements.** **TWO FULL PHASE A RUNS AND BOTH ARE WORSE THAN DOING NOTHING: K6 = 20 of 29** (`U18.7` and `U18.10` both connected, but **`Q3_CS` SPLITS `{Q3.1}|{Q3.3}`** against the explicit section 12 protection, plus `LTC_GATE` split, `BAT_RAW` 3 islands, `LTC_OV` open); **K1 = 22 of 29** (both pins joined, but **`LTC_GATE` fragments into FIVE islands** and `LTC_SHDN` splits). **The 002I baseline of 24 of 29 remains the best measured result, and across 002I and 002J EVERY intervention - one reordering and seven placements - has landed AT OR BELOW it.** **THE SECTION 10 VIA RESERVE IS NOT TRIGGERED:** it authorises a FAULT_N via only if candidates fail SOLELY because `U18.7` stays boxed, and `U18.7` turns out to be the EASY pin - five of six candidates close it. **THE SECTION 10 STOP CONDITION IS MET INSTEAD: `LTC_GATE` degrades under every R80/R81 move** (1 island at baseline, 2 at K6, 5 at K1), and section 10 forbids a via on `LTC_GATE` and orders a stop for CTO review. **U19 SEARCH NOT PERFORMED - section 9 requires an R80/R81 winner first and there is none.** **PR-44 CLOSED (general harness, and the most durable thing this task produced): `apply_areas` SEGFAULTED ON FREED MEMORY.** `grow()` stored PCB_TRACK OBJECTS in each rule area; when a later connection failed and `qb.revert()` removed its copper KiCad freed them, and the next `apply_areas()` called `GetClass()` on a dangling pointer - a hard, DETERMINISTIC SIGSEGV at connection 28 that killed two full Phase A runs outright. Storing the UUID and resolving it against the board each time fixes it; `area_stats` needed the same. **Without PR-44 no full Phase A on a placement with early reverts can complete at all.** `router_regression` ALL CHECKS PASS. **CTO DECISION REQUIRED: the margin is not short of a lane, it is short of LAYERS. Recommended lever - GIVE THE LOW-CURRENT STATUS/CONTROL CLASS (`LTC_GATE`, `LTC4368_FAULT_N`, `LTC_SHDN`, `LTC_OV`, all of which already carry vias) A PLANNED F.Cu PATH, rather than conceding one grudging via at a time. It is the only option that ADDS capacity instead of redistributing it, and it is a routing-policy change, not a placement change. Alternatives: relax the zero-via PREFERENCE on `Q3_CS` (section 12 says preferred, not required), or widen the west margin geometrically, which is a larger ECO than this task authorised.** **Phase A FAIL. Phase B NOT RUN. No manifest. No authoritative copper. B-34 REMAINS OPEN. NO PERCENTAGE: PCB routing stays 0 %, overall Full Beta v2 stays 74 %.** | 2026-08-26 |


> **Result (FBV2-P2-002C).** Full analysis:
> [`audits/2026-08-24-p2-battery-authoritative-route.md`](audits/2026-08-24-p2-battery-authoritative-route.md).
> **FBV2-P2-002C = FAIL. Phase A stopped at `LTC_GATE` `Q2.2 → TP17.1`, so Phase B never ran and
> the authoritative PCB is byte-identical to `a52977e`.** Delivered **D-249**, the path-role width
> ruling that makes `BAT_PROTECTED_P` routable at all, and 27 coexisting DRC-clean connections on
> scratch. **B-34 from real copper is ≈ 392 mV / 588 mW at 1.5 A — worse than the estimate.**
> **PCB routing stays 0 %; overall stays 74 %.**


> **Result (FBV2-P2-002B).** Full analysis:
> [`audits/2026-08-24-routing-harness-qualification.md`](audits/2026-08-24-routing-harness-qualification.md).
> **ROUTER HARNESS QUALIFICATION = PASS.** All three named defects fixed and proved fixed; a
> fourth (the grid guard band) found and fixed during qualification. **The two cases that did not
> route are a PROVED LAND-PATTERN / RULE CONFLICT on five fine-pitch pads — D-248, open for a
> ruling.** **No copper committed; the board is byte-identical to `8b9efba`. PCB routing stays
> 0 %; overall stays 74 %.**


> **Result (FBV2-P2-002A).** Full analysis:
> [`audits/2026-08-24-p2-battery-protection-routing.md`](audits/2026-08-24-p2-battery-protection-routing.md).
> **FBV2-P2-002A = FAIL. The battery / protection block is NOT routed; nothing was committed as
> copper.** Delivered: **D-245**, the scoped `BAT_PROTECTED_P` width override, and a working
> **obstacle-aware router with pad-escape necking and per-net DRC gating** that reverts anything
> unclean. **PM-2: placement corrected and approved, closure still pending.**
> **ZERO tracks, ZERO signal vias, 499 unrouted. PCB routing stays 0 %; overall stays 74 %.**

> **Result (FBV2-P2-001).** Full analysis:
> [`audits/2026-08-24-p2-power-routing.md`](audits/2026-08-24-p2-power-routing.md).
> New working document: [`pcb/FBV2_P2_POWER_ROUTING.md`](pcb/FBV2_P2_POWER_ROUTING.md).
> Pre-routing checkpoint tag **`beta-v2-p2-entry-pass` → `faa0c91`**, annotated and pushed.
> **FBV2-P2-001 = FAIL. The power tree is NOT routed and the attempt was REVERTED.**
> **Delivered: the In1.Cu GND plane (1 island, 93.3 %) and the PM-2 support / test-point
> placement corrections the routing exposed as prerequisites.**
> **ZERO tracks, ZERO signal vias, 499 unrouted. PCB routing stays 0 %; overall stays 74 %.**

> **Result (FBV2-EXP-002).** Full analysis:
> [`audits/2026-08-24-expansion-and-refloorplan-implementation.md`](audits/2026-08-24-expansion-and-refloorplan-implementation.md).
> New library part: `Samtec_SSQ-124-02-G-S-RA.kicad_mod`.
> **BATTERY PROCUREMENT GATE = PASS on two manufacturer-datasheet cells before any file was
> touched. FBV2-P1 RE-ISSUED = PASS. FBV2-P2 ENTRY = PASS. PM-1, PM-2, PM-3 and PT-1 CLOSED.**
> **NO PERCENTAGE: P1 was re-earned, not newly earned, and P2 entry earns none. Overall stays 74 %.**
> **ZERO SIGNAL ROUTING: 0 tracks, 0 signal vias, 0 electrical pours, 499 unrouted. DRC 26 -> 1.**
> **ERC 0 errors / 27 warnings, histogram identical.**

> **Result (FBV2-P2-000).** Full analysis:
> [`audits/2026-08-24-p2-entry-audit.md`](audits/2026-08-24-p2-entry-audit.md).
> New working documents: [`pcb/FBV2_P2_ROUTING_PLAN.md`](pcb/FBV2_P2_ROUTING_PLAN.md),
> [`pcb/FBV2_P2_NETCLASS_LEDGER.csv`](pcb/FBV2_P2_NETCLASS_LEDGER.csv).
> New check: `hardware/beta-v2/checks/dru_probe.py`.
> **FBV2-P2 ENTRY GATE = FAIL on one criterion of thirteen — an electrically required
> placement move remains (PM-1, PM-2, PM-3). NO PERCENTAGE IS EARNED; overall stays 74 %.**
> **ZERO ROUTING WAS PERFORMED: 0 tracks, 0 signal vias, 0 electrical pours, 499 unrouted
> unchanged. DRC 47 → 26. ERC 0 errors / 27 warnings, histogram identical.**

> **Result (FBV2-P1-001).** Full analysis:
> [`audits/2026-08-24-p1-floorplan-implementation.md`](audits/2026-08-24-p1-floorplan-implementation.md).
> New working documents: [`pcb/FBV2_P1_FLOORPLAN.md`](pcb/FBV2_P1_FLOORPLAN.md),
> [`pcb/FBV2_P1_KEEPOUTS.md`](pcb/FBV2_P1_KEEPOUTS.md),
> [`pcb/FBV2_P1_COORDINATES.csv`](pcb/FBV2_P1_COORDINATES.csv), [`pcb/review/`](pcb/review/).
> **FBV2-P1 DOES NOT PASS — the 100 mm 915 MHz pigtail does not reach. Overall stays 68 %.**

> **Result (FBV2-P1-002).** Full analysis:
> [`audits/2026-08-24-p1-floorplan-closeout.md`](audits/2026-08-24-p1-floorplan-closeout.md).
> New working document: [`assembly/IR_LEAD_FORMING.md`](assembly/IR_LEAD_FORMING.md).
> Regenerated: [`pcb/FBV2_P1_FLOORPLAN.md`](pcb/FBV2_P1_FLOORPLAN.md),
> [`pcb/FBV2_P1_KEEPOUTS.md`](pcb/FBV2_P1_KEEPOUTS.md),
> [`pcb/FBV2_P1_COORDINATES.csv`](pcb/FBV2_P1_COORDINATES.csv),
> [`pcb/FBV2_P1_METRICS.txt`](pcb/FBV2_P1_METRICS.txt), [`pcb/review/`](pcb/review/).
> **FBV2-P1 PASSES. Overall 68 % → 74 %.** **ONE ITEM ESCALATED: only two legal through-board
> M2 positions exist on this outline, not the three the task assumes — D-226.**

> **Result (FBV2-MECH-002).** Full analysis:
> [`audits/2026-08-23-pre-floorplan-authority-reconciliation.md`](audits/2026-08-23-pre-floorplan-authority-reconciliation.md).
> New working document:
> [`mechanical/P1_FLOORPLAN_INPUTS.md`](mechanical/P1_FLOORPLAN_INPUTS.md).
> **This task earned NO progress — Full Beta v2 remains 68 % and FBV2-S2 = PASS is unchanged.**
> **ERC 27 -> 27, zero errors. Netlist 224 nets / 991 nodes, IDENTICAL. The schematic diff is
> PROPERTY-ONLY. The PCB is byte-identical and still bit-identical to Beta-DM.**

> **Result (FBV2-S2-002).** Full analysis:
> [`audits/2026-08-23-s2-release-closeout.md`](audits/2026-08-23-s2-release-closeout.md).
> New working document:
> [`assembly/FIRST_FIVE_ASSEMBLY_PLAN.md`](assembly/FIRST_FIVE_ASSEMBLY_PLAN.md).
>
> **FBV2-S2 = PASS.** **ERC 27 / 0 errors / 27 — the violation-type histogram is identical to the
> FBV2-S2-001 baseline, and no warning was "cleaned".** **The schematic diff is PROPERTY-ONLY:**
> after filtering property blocks, not one wire, label, junction, symbol, pin or sheet-pin line
> changed in any of the nine sheets, so connectivity cannot have moved. **The PCB is untouched and
> still bit-identical to Beta-DM.**

> **Result (FBV2-S2-001).** Full analysis:
> [`audits/2026-08-23-s2-preplacement-release-audit.md`](audits/2026-08-23-s2-preplacement-release-audit.md).
> Working documents:
> [`assembly/FIRST_FIVE_POPULATION_MATRIX.md`](assembly/FIRST_FIVE_POPULATION_MATRIX.md) ·
> [`assembly/SOURCING_LEDGER.md`](assembly/SOURCING_LEDGER.md) ·
> [`assembly/FOOTPRINT_VERIFICATION_LEDGER.md`](assembly/FOOTPRINT_VERIFICATION_LEDGER.md) ·
> [`assembly/OFF_BOARD_BOM.md`](assembly/OFF_BOARD_BOM.md).
>
> **FBV2-S2 = FAIL on two criteria (B-03 footprints, B-71 assembly classification). Every other
> gate passes.** ERC **27 / 0 errors / 27** unchanged, 0 duplicate references, **0 unresolved
> footprint references**, 0 missing MPNs on actives and connectors, 0 orphan or one-pin nets,
> 0 `*_TBD`, **0 unexplained DNP**, and **0 same-text local labels split across sheets** — the
> sheet-09 failure mode does not recur anywhere. `fork_equivalence.py` PASS, `netclass_probe.py`
> PASS, **the PCB is untouched and still bit-identical to Beta-DM.**
>
> **No honest warning was "fixed".** No no-connect, power flag or pin-electrical-type was added or
> altered anywhere in this task. All seven `PWR_FLAG`s were individually traced to a real supply
> reaching the net through a passive.
>
> ### O-8 — NEW, REQUIRES A CTO DECISION
> **The 915 MHz external whip antenna MPN is not selected.** Everything from the module socket to
> the panel bulkhead is now locked and orderable; the antenna that screws onto the outside is not.
> It is an accessory-class purchase with **no board impact**, but a range test means nothing
> without it. Pick a standard 868/915 MHz SMA-male whip at procurement.
>
> **Nothing else was added:** no new features, no new rails, no new connectors, no speculative
> fallback circuitry, no PGOOD IC, no I²C mux, no PCB change, and no passive-value consolidation —
> that last one deliberately, because consolidating values before the layout exists optimises the
> wrong thing.

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
| ~~**P-01**~~ | ~~Reverse-polarity architecture.~~ **CLOSED 2026-08-23 by D-200 (FBV2-S2-001) - STALE.** The LTC4368-1 + dual back-to-back FET path is fully represented and measured in the netlist (`F1` -> `BAT_RAW` -> `Q2` -> `BAT_MID` -> `Q3` -> `BAT_SENSE` -> `R75` -> `BAT_PROTECTED_P`), all FITTED, and **FBV2-A1 passed on 2026-08-22**. The row survived only because historical text existed. | closed | 2026-08-22 |
| ~~**P-02**~~ | ~~Freeze the 20-pin connector.~~ **CLOSED 2026-08-23 by D-081...D-085 (FBV2-COMM-001).** The 20-pin architecture is **superseded**, not frozen: the port is now **2 x 12, 24 active contacts, female device side**, connector `Harwin M20-7881242`, pin ordering locked, `U3` allocation 16/16. | closed | 2026-08-22 |
| ~~**P-03**~~ | ~~NFC core / PA rail architecture.~~ **RESOLVED — the question was mis-framed.** DS12484 Rev 3 requires VDD and VDD_TX to share one supply (±0.2 V operating). The rails cannot be split and the as-built assignment is correct. | Superseded by **P-10**. | closed 2026-08-22 |
| **B-47** | **Does the FH52E second source survive, and does `J1` move to the FH52E standard land pattern?** FBV2-DISP-002 ruled it should; FBV2-S1-003 declined to assert drop-in equivalence without both Hirose drawings. | **There is currently no JLCPCB assembly path for `J1`.** Settle at FBV2-S2, before placement makes the land pattern expensive to change. | 2026-08-23 |
| ~~**P-04**~~ | ~~NFC first-fab inclusion, and antenna implementation.~~ **CLOSED 2026-08-23 by D-200 (FBV2-S2-001) - STALE.** The IC, the 27.12 MHz crystal, the calculated first-build matching network, the `FXC.46.52.0075X.B.dg` antenna, `J7`, the 3.3 V first-build supply and the preserved 5 V fallback all exist - and **D-192 fitted the IC, which had still been marked DNP**. | closed | 2026-08-22 |
| ~~**P-11**~~ | ~~Dead-cell recovery: Candidate B or Candidate D?~~ **CLOSED 2026-08-22 by D-065 — Candidate B selected**, and specified to component level in the FBV2-PWR-002 closeout. **This was the last item blocking FBV2-A1, which now PASSES.** | closed | 2026-08-22 |
| ~~superseded~~ | ~~**Dead-cell recovery: Candidate B or Candidate D?**~~ **B** — a *hardware-qualified* precharge from `SYS` to `BAT_RAW`, gated by a GND-referenced comparator interlock so a reversed cell draws ≈0 A; no firmware, works with a corrupted image; ~8–10 parts, 1–3 µA. **D** — no recovery path; deeply discharged packs are serviced. **Recommendation: B for the product, D acceptable for the first five boards.** | **THE ONLY ITEM BLOCKING FBV2-A1.** A single MOSFET cannot distinguish 0 V from −3.7 V — both turn it *more* on — so an explicit level-sensing element is mandatory and this is a genuine new power-tree branch. *(Supersedes the earlier firmware-gated proposal: the CTO prefers safety not to depend on firmware, and that is the better position.)* | 2026-08-22 |
| ~~**P-12**~~ | ~~BQ25185 BAT survivability of a brief negative excursion.~~ **LARGELY RETIRED 2026-08-22 by FBV2-PWR-002.** Under the P2 pass architecture the excursion **does not occur under any single fault**. It survives only as a double-fault consideration and is no longer an architecture item. | schematic-phase note only | 2026-08-22 |
| ~~**P-13**~~ | ~~Latch-off vs hot-insertion inrush.~~ **CLOSED 2026-08-22 by FBV2-PWR-001.** The LTC4368 datasheet gives `I_INRUSH = (C_OUT/C_GATE) × I_GATE(UP)` and the design rule `I_OC,FWD > I_INRUSH + I_OUT` — inrush is designed, ≈350 mA against a 3.33 A trip. Separately, **RETRY latch-off applies to FORWARD overcurrent only**; reverse faults reconnect automatically once VOUT falls 100 mV below VIN. Both halves of the objection fall away. | closed | 2026-08-22 |
| **P-14** | **MAX17048 sense point — cell side or protected side?** | The protection adds ~51 mΩ; at 1 A that is ~51 mV of IR drop the voltage-only gauge cannot compensate (several % SOC). Cell side avoids it but sits exposed to the reversed-cell fault. | 2026-08-22 |
| ~~**P-15**~~ | ~~3V3 rail budget under simultaneous worst case.~~ **CLOSED 2026-08-23 by D-092.** It does force firmware mutual exclusion, and the contract is now binding (MX-1...MX-9). Naive simultaneity reaches **85-90 %** of the TPS63020's 2 A; the enforced design case reaches **58-66 %**; an accessory hard short at the recommended `R_ILIM` reaches **86 %**. | closed | 2026-08-22 |
| ~~**P-16**~~ | ~~Repurpose one XGPIO as `ACC_DETECT`?~~ **CLOSED 2026-08-23 by D-082/D-085.** No XGPIO is repurposed: `ACC_DETECT_N` is a **dedicated connector contact (pin 23) and a dedicated `U3` input**. The published XGPIO count does fall to 10, but by CTO product ruling, not by theft. | closed | 2026-08-22 |
| ~~**P-22**~~ | ~~Ratify or reinstate the "no automatic KiCad file generation" rule.~~ **CLOSED 2026-08-23 by D-107** — superseded by an eight-condition standing rule; scripts may not bypass engineering review. |  | 2026-08-23 |
| ~~superseded~~ | ~~**Ratify or reinstate the "no automatic KiCad file generation" rule.**~~ The Beta-DM README forbids generating or modifying KiCad files automatically; FBV2-S1-001 captured `01_POWER_TREE` by script and verified it with `kicad-cli` ERC plus a netlist export. | Every remaining FBV2-S1 sheet migration depends on the answer. The rule is recorded unaltered and is **not** treated as repealed by having been overtaken. | 2026-08-23 |
| ~~**P-20**~~ | ~~`R95` recovery current limit.~~ **CLOSED 2026-08-23 by D-105 — 560 Ω locked.** Recovery 8.36 mA nominal; **B-27 amended to ≈ 15.9 mA / ≈ 16.6 mA worst case**. |  | 2026-08-23 |
| ~~superseded~~ | ~~**`R95` recovery current limit: 680 R as captured, or 560 R as locked?**~~ | Injection into a 0 V pack falls from ≈ 8.4 mA to **≈ 6.9 mA** at VBUS 5.0 V. **This moves the wrong way against B-26**, which warns that a pack protector needing more than ~10 mA to release its over-discharge latch would not be revived. Not a wiring fault; a value that must be ruled, not assumed. | 2026-08-23 |
| ~~**P-21**~~ | ~~`OV` trip.~~ **CLOSED 2026-08-23 by D-104 — 4.63 V nominal**, `R77` 3.65 M / `R78` 442 k, derived from the datasheet 500 mV ±1.5 % threshold. |  | 2026-08-23 |
| ~~superseded~~ | ~~**`OV` trip: 5.05 V as captured, or ≈ 4.6 V as documented?**~~ | Captured as `R77` 4.02 M / `R78` 442 k against the FBV2-PWR-002 diagram's *"divider ≈ 4.6 V"*. 5.05 V sits above a 4.2 V pack with margin and below the USB ceiling, so it is plausible and probably deliberate — but it is not the documented number, and the documented number is what a reviewer will check. | 2026-08-23 |
| ~~**B-53**~~ | ~~NFC antenna architecture.~~ **CLOSED 2026-08-23 by D-127 — off-board purchased flex with integrated ferrite, Taoglas `FXC.46.52.0075X.A.dg`, on a JST ACH connector.** Original text: **NFC antenna architecture: PCB loop on the main board, purchased flex + ferrite, or a daughter antenna?** | **Recommendation: flex + ferrite.** A main-board loop needs a **45 × 45 mm keepout in the ground plane on every layer** in the rear upper third, with the battery directly behind it — the highest first-board risk of the three. The schematic is neutral: whichever is chosen lands on `NFC_ANT_A`/`NFC_ANT_B` and the front end does not change. | 2026-08-23 |
| ~~**P-17**~~ | ~~ST25R3916 or ST25R3916B?~~ **CLOSED 2026-08-23 by D-126 — `ST25R3916-AQET`, non-B, LOCKED.** Original recommendation: **KEEP the non-B `ST25R3916-AQET`.** Same 32-UFQFPN package; Mouser 3,243 in stock; **LCSC `C5267441` at ~$3.37 gives a JLCPCB assembly path the B does not have**, at roughly half the unit cost. The B's advantages are EMVCo PCD L1 3.2a compliance and a better AWS implementation — **AQROOT is not an EMVCo terminal**, so neither serves a stated priority, and the B's `-AQWT` variant is a stock trap (0 units, restock quoted January 2028). Switching would also require AN5768 and re-proving footprint equivalence. **Not silently locked: it touches analog waveform quality and therefore read range at the margin, so it is flagged for ratification.** | The B adds Active Wave Shaping and finer driver stepping (both recover margin at 3.3 V) but **removes capacitive sensing** on CSI/CSO, losing low-power capacitive tag detect. With AWS the VDD_AM capacitor changes to 10–50 nF. Schematic-time decision, product call. | 2026-08-22 |
| ~~**P-18**~~ | ~~Accessory I2C segmentation - buffer alone, or add a mux?~~ **CLOSED 2026-08-23 by D-178 (FBV2-S1-009). NO MUX.** The bus-hang half was already closed by the detect-gated rail; the **TCA4307** now closes it structurally, with autonomous stuck-bus disconnect and up to 16 recovery clocks (D-176). **Address collision is not an electrical problem and a mux is the wrong tool for it**: the external segment stays one logical address space with the internal bus, and allocation is governed by the normative [`architecture/I2C_ADDRESS_REGISTRY.md`](architecture/I2C_ADDRESS_REGISTRY.md). `0x50` is NOT widened; P-19 stays future protocol scope. | closed |
| ~~**P-10**~~ | ~~NFC supply topology.~~ **N1** — run NFC entirely at 3.3 V (`sup3V` option bit; VDD range 2.4–3.6 V) and **delete** U13, L2, R44, R45, C19, C34, C35, C55; or **N2** — keep the 5 V boost and never disable it while the system is on. Created by the DS12484 finding that VDD and VDD_TX cannot be split. | With true load disconnect confirmed on the TPS61023, disabling the boost leaves VDD = 0 V while VDD_IO = 3.3 V — a state the datasheet nowhere authorises. **N1 recommended**: deletes a converter, eight parts, the OVP question and the sequencing question. Price is RF range. | 2026-08-22 |
| ~~**M-06**~~ | ~~Display MPN and FPC interface not locked.~~ **CLOSED 2026-08-23 by D-074…D-078 (FBV2-DISP-002).** `ER-TFT035IPS-6` + `ER-TPC035-6`; 50-pin, 0.5 mm, bottom contact, 0.30 ± 0.03 mm; FT6236 @ 0x38; `J1` = Hirose `FH69-50S-0.5SH`. | closed | 2026-08-22 |
| ~~**M-07**~~ | ~~Backlight driver re-derivation.~~ **CLOSED 2026-08-23 by D-079.** TPS61169 retained; `R69` = 1.87 R, `R70`–`R73` = 4 x 33 R; switch-peak margin 4.6x; `L3`/`D8`/`C44` unchanged. | closed | 2026-08-22 |
| ~~**M-01**~~ | ~~Display size / panel MPN.~~ **CLOSED 2026-08-22 by D-072 - 3.5 inch ruled.** Replaced by M-06. | closed | 2026-08-22 |
| ~~superseded~~ | ~~**Display size / panel MPN.**~~ 2.8″ CH280QV10-CT is inherited from Beta-DM, and its exact outline, thickness and FPC bend stack **are not archived locally**. A 50 × 69 mm module in an 80 × 160 front is modest — the cavity comfortably accepts **3.2″ or 3.5″**. | Does **not** block FBV2-A2 or schematic migration. **Does** block PCB floorplanning (FBV2-P1): display size sets the front layout, which sets the rear free area, which sets the NFC zone. | 2026-08-22 |
| ~~**M-02**~~ | ~~Battery capacity target.~~ **CLOSED 2026-08-22 by D-071** - 60 x 75 x 8.0 mm, ~2500-3000 mAh. | closed | 2026-08-22 |
| ~~superseded~~ | ~~**Battery capacity target.**~~ The confirmed 3.5 mm of Z margin supports an **8.0 mm** pack (~2500–3000 mAh) against the **2000 mAh** assumed in the power budget. | Either answer fits. Confirm the target, then re-derive runtime in [[13 - Power Budget and Battery Runtime v0.1]]. | 2026-08-22 |
| ~~**P-07**~~ | ~~Exact mechanical internal cavity.~~ **CLOSED 2026-08-22 by FBV2-MECH-001** — cavity derived at **75.0 × 155.0 × 18.5 mm** and recorded as TARGET in the mechanical interface spec. | closed | 2026-08-22 |
| ~~superseded~~ | ~~**Exact mechanical internal cavity.**~~ Internal cavity X/Y/Z, wall thickness and PCB-to-wall clearance have **never existed** in this repository. | Blocks the v2 outline, and therefore all placement and routing. **Now the long-pole item.** | 2026-08-22 |

### Closed since 2026-08-22

| # | closed by | outcome |
|---|---|---|
| **R111** | D-111 | **Fitted, 10 kΩ.** GPIO45 no longer relies on the internal pull-down alone to hold VDD_SPI at 3.3 V. |
| **B-28** | D-114 | **`R112` 0 Ω DNP.** The display is off SPI-A by default; `TP36` characterises SDO without fitting anything. |
| **B-32** | D-115 | **`C43` 4.7 µF X5R on `U17` `VIN`** confirmed. |
| **B-43** | D-116 | **TPS61169 `CTRL` has a 300 kΩ internal PULL-DOWN.** It cannot raise the GPIO46 strap. |
| **P-20** | D-105 | **`R95` = 560 Ω.** Recovery 8.36 mA nominal (7.93–8.80 mA). B-27's single-fault ceiling **amended to ≈ 15.9 mA**, not left reading 13 mA. |
| **P-21** | D-104 | **OV trip 4.63 V nominal**, 4.48–4.78 V, derived from the datasheet 492.5/500/507.5 mV threshold. Removes a BOM line. |
| **P-22** | D-107 | **Scripted KiCad edits permitted under eight conditions**, and never as a substitute for engineering review. |
| **P-02** | D-081...D-085 | **Community port superseded and re-locked.** 2 x 12, 24 active contacts, female device side, `Harwin M20-7881242`, pin ordering and detect convention locked. |
| **P-15** | D-092 | **Rail budget closed by a binding firmware mutual-exclusion contract** (MX-1...MX-9). |
| **P-16** | D-082 / D-085 | **`ACC_DETECT_N` is a dedicated contact and a dedicated expander pin.** No XGPIO repurposed. |
| **M-06** | D-074...D-078 | **Display and connector LOCKED.** `ER-TFT035IPS-6` + `ER-TPC035-6`, `J1` = Hirose `FH69-50S-0.5SH`, mating proven from both manufacturers' drawings. |
| **M-07** | D-079 | **Backlight LOCKED.** TPS61169 retained; `R69` 2.55 R -> **1.87 R**; `R70`–`R73` 4 x 39 R -> **4 x 33 R in parallel** on one anode. |
| **P-10** | D-055 | NFC runs at 3.3 V on the first build (was "N1"), **with** a no-respin 5 V fallback per D-056. |
| **P-01** | D-050…D-054 | Reverse-polarity **topology** chosen: LTC4368-1 + dual N-FET + fuse + clamp. Component values and dead-cell recovery remain open as P-11…P-13. |
| **P-05** | D-037 | RGB architecture removed; three expander pins freed. |
| **P-06** | D-038 | Dedicated RootProbe IRQ retired; `U2.P17` freed. |
| **P-08** | D-040 | IPEX → pigtail → bulkhead. No new main-PCB RF routing. |
| **P-09** | D-041 | LoRa deep-sleep packet wake is not a v2 requirement. |

### How a pending decision closes

A pending item closes by being moved into a numbered `D-xxx` row above, with its
date, and by an entry in [CHANGELOG.md](CHANGELOG.md). It is removed from this
table only when it has a home in the locked sections.
