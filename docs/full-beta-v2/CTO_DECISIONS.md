# AQROOT Full Beta v2 — CTO Decisions

**Status: LIVING DOCUMENT. This is the current source of truth.**

When an older transcript, audit or architecture note conflicts with a ruling in
this file, **this file wins.** Superseded rulings are struck through and kept,
never deleted, so the history of the decision stays readable.

Established: 2026-08-22
Last updated: 2026-08-23 (FBV2-S1-004)

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
| D-085 | **`ACC_DETECT_N` CONVENTION LOCKED.** The accessory asserts detect by shorting **pin 23 to the adjacent GND at pin 21** (one 0 Ohm link); AQROOT provides a 100 k pull-up to `+3V3`. **Detection works with both accessory rails OFF**, because the pull-up and the expander run from `+3V3`. **Neither rail may be enabled unless `ACC_DETECT_N` is asserted** - which is also what makes a flipped accessory passively safe: it cannot ground pin 23, so it never receives power. | 2026-08-23 |
| D-086 | **3.3 V ACCESSORY RAIL: `+3V3` -> `TPS22950C` -> `ACC_3V3_SW`.** Verified against SLVSFJ2B: `VIN` 1.8-5.5 V, RCB **Yes**, `ILIM` 0.5-3.5 A adjustable, auto-retry, TSD 170 C, `FLT` open-drain, DDC SOT-23-thin. Default OFF with a **mandatory external 100 k pull-down** on `ON`. **`R_ILIM` = 1.5 k (approx. 0.76 A typ) RECOMMENDED, NOT fabrication-locked**; published limit **400 mA continuous** for the first five boards. | 2026-08-23 |
| D-087 | **5 V ACCESSORY RAIL (NEW): `BQ25185_SYS` -> a SECOND `TPS61023` at 5.0 V -> a SECOND `TPS22950C` -> `ACC_5V_SW`.** It is **not** USB `VBUS`, **not** the NFC fallback rail, and tied to neither; the only shared node is `SYS` on the input side. **`R_ILIM` = 1.65 k (approx. 0.69 A typ) RECOMMENDED, NOT fabrication-locked**; published limit **300 mA continuous** for the first five boards. Inductor **1 uH, I_sat >= 3 A**. | 2026-08-23 |
| D-088 | **BOM CONSOLIDATION LOCKED. One `TPS22950C` MPN on BOTH rails** - only `R_ILIM` differs. **`TPS61023` is REUSED** as the accessory boost, sharing inductor, feedback divider and capacitors with the DNP NFC fallback (D-056). One boost family and one load-switch family to validate, source, stock and rework. | 2026-08-23 |
| D-089 | **EXPANDER ALLOCATION LOCKED.** **`U3`**: `XGPIO0-9`, `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_DETECT_N`, **`ACC_POWER_FAULT_N`** and `SX1262_RXEN` = **15 assigned + 1 `RESERVED_SPARE`** *(amended 2026-08-23 by D-094 - the two `FLT` lines are wire-OR'd, freeing P16)*. **`U2` = 16/16**: the five pins freed by D-010/D-037/D-038 are exactly consumed by `BQ25185_STAT1/2`, `MAX17048_ALRT_N`, `VBUS_PRESENT` and `SX1262_DIO1`. **`U2` still has ZERO spare** (B-37, half closed). `ACC_5V_EN` drives the boost `EN` and the 5 V switch `ON` from one pin. Five new external safe-state pulls are mandatory. | 2026-08-23 |
| D-090 | **ALL COMMUNITY SIGNALS ARE 3.3 V CMOS ONLY. The 5 V power contact does NOT make any signal 5 V-tolerant.** Protection: **100 Ohm series on every XGPIO and both native pins**, 22 Ohm on the buffered I2C pair, 330 Ohm on WAKE, plus a **low-capacitance TVS array on `NATIVE_A`, `NATIVE_B`, `EXT_SDA`, `EXT_SCL`** - the natives are the only contacts with a direct path to the MCU. **Bidirectional level translators are REJECTED**: they do not protect the A-side, they add direction ambiguity on bidirectional GPIO, and they would imply 5 V logic is supported, which it is not. Silkscreen: *"COMMUNITY PORT - 3V3 LOGIC ONLY / 5V PIN IS POWER OUTPUT ONLY"*. | 2026-08-23 |
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
| ~~**P-02**~~ | ~~Freeze the 20-pin connector.~~ **CLOSED 2026-08-23 by D-081...D-085 (FBV2-COMM-001).** The 20-pin architecture is **superseded**, not frozen: the port is now **2 x 12, 24 active contacts, female device side**, connector `Harwin M20-7881242`, pin ordering locked, `U3` allocation 16/16. | closed | 2026-08-22 |
| ~~**P-03**~~ | ~~NFC core / PA rail architecture.~~ **RESOLVED — the question was mis-framed.** DS12484 Rev 3 requires VDD and VDD_TX to share one supply (±0.2 V operating). The rails cannot be split and the as-built assignment is correct. | Superseded by **P-10**. | closed 2026-08-22 |
| **B-47** | **Does the FH52E second source survive, and does `J1` move to the FH52E standard land pattern?** FBV2-DISP-002 ruled it should; FBV2-S1-003 declined to assert drop-in equivalence without both Hirose drawings. | **There is currently no JLCPCB assembly path for `J1`.** Settle at FBV2-S2, before placement makes the land pattern expensive to change. | 2026-08-23 |
| **P-04** | **NFC first-fab inclusion, and antenna implementation.** Is NFC in v2's first fabrication, or a populate-later block? The 27.12 MHz crystal, the matching network and the antenna are **undesigned**, not merely unrouted. | Gates the schematic migration schedule and the rear-half floorplan. | 2026-08-22 |
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
| **B-53** | **NFC antenna architecture: PCB loop on the main board, purchased flex + ferrite, or a daughter antenna?** | **Recommendation: flex + ferrite.** A main-board loop needs a **45 × 45 mm keepout in the ground plane on every layer** in the rear upper third, with the battery directly behind it — the highest first-board risk of the three. The schematic is neutral: whichever is chosen lands on `NFC_ANT_A`/`NFC_ANT_B` and the front end does not change. | 2026-08-23 |
| **P-17** | **ST25R3916 or ST25R3916B?** **RECOMMENDED FOR CLOSURE 2026-08-23 (FBV2-S1-004): KEEP the non-B `ST25R3916-AQET`.** Same 32-UFQFPN package; Mouser 3,243 in stock; **LCSC `C5267441` at ~$3.37 gives a JLCPCB assembly path the B does not have**, at roughly half the unit cost. The B's advantages are EMVCo PCD L1 3.2a compliance and a better AWS implementation — **AQROOT is not an EMVCo terminal**, so neither serves a stated priority, and the B's `-AQWT` variant is a stock trap (0 units, restock quoted January 2028). Switching would also require AN5768 and re-proving footprint equivalence. **Not silently locked: it touches analog waveform quality and therefore read range at the margin, so it is flagged for ratification.** | The B adds Active Wave Shaping and finer driver stepping (both recover margin at 3.3 V) but **removes capacitive sensing** on CSI/CSO, losing low-power capacitive tag detect. With AWS the VDD_AM capacitor changes to 10–50 nF. Schematic-time decision, product call. | 2026-08-22 |
| **P-18** | **Accessory I2C segmentation - buffer alone, or add a mux?** | **HALF ANSWERED 2026-08-23 (FBV2-COMM-001).** The `U16` TCA9517A B-side supply is `ACC_3V3_SW`, which is now **default OFF and detect-gated**, so a dead or absent accessory cannot hold SDA low - the *bus-hang* half is closed. **Address collision on 0x36 / 0x20-0x27 is NOT solved by a buffer** and still needs a ruling: mux, or a published reserved-address policy. | 2026-08-22 |
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
