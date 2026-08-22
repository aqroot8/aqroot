# AQROOT Full Beta v2 — CTO Decisions

**Status: LIVING DOCUMENT. This is the current source of truth.**

When an older transcript, audit or architecture note conflicts with a ruling in
this file, **this file wins.** Superseded rulings are struck through and kept,
never deleted, so the history of the decision stays readable.

Established: 2026-08-22
Last updated: 2026-08-23 (FBV2-DISP-002)

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
| D-059 | **New target: 11 × independent XGPIO · 2 × independent native ESP32 GPIO · 2 × external I²C · 1 × WAKE/ATTN · 1 × protected switched accessory 3V3 · 3 × GND = 20.** No permanent raw `+3V3`. No duplicate GPIO. | 2026-08-22 |
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
| D-062 | 20-pin resource architecture **LOCKED**: 11 XGPIO · 2 native ESP32 GPIO · 2 external I²C · 1 WAKE/ATTN · 1 protected switched accessory 3V3 · 3 GND = 20. **No raw permanent +3V3.** | 2026-08-22 |
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
| ~~**P-11**~~ | ~~Dead-cell recovery: Candidate B or Candidate D?~~ **CLOSED 2026-08-22 by D-065 — Candidate B selected**, and specified to component level in the FBV2-PWR-002 closeout. **This was the last item blocking FBV2-A1, which now PASSES.** | closed | 2026-08-22 |
| ~~superseded~~ | ~~**Dead-cell recovery: Candidate B or Candidate D?**~~ **B** — a *hardware-qualified* precharge from `SYS` to `BAT_RAW`, gated by a GND-referenced comparator interlock so a reversed cell draws ≈0 A; no firmware, works with a corrupted image; ~8–10 parts, 1–3 µA. **D** — no recovery path; deeply discharged packs are serviced. **Recommendation: B for the product, D acceptable for the first five boards.** | **THE ONLY ITEM BLOCKING FBV2-A1.** A single MOSFET cannot distinguish 0 V from −3.7 V — both turn it *more* on — so an explicit level-sensing element is mandatory and this is a genuine new power-tree branch. *(Supersedes the earlier firmware-gated proposal: the CTO prefers safety not to depend on firmware, and that is the better position.)* | 2026-08-22 |
| ~~**P-12**~~ | ~~BQ25185 BAT survivability of a brief negative excursion.~~ **LARGELY RETIRED 2026-08-22 by FBV2-PWR-002.** Under the P2 pass architecture the excursion **does not occur under any single fault**. It survives only as a double-fault consideration and is no longer an architecture item. | schematic-phase note only | 2026-08-22 |
| ~~**P-13**~~ | ~~Latch-off vs hot-insertion inrush.~~ **CLOSED 2026-08-22 by FBV2-PWR-001.** The LTC4368 datasheet gives `I_INRUSH = (C_OUT/C_GATE) × I_GATE(UP)` and the design rule `I_OC,FWD > I_INRUSH + I_OUT` — inrush is designed, ≈350 mA against a 3.33 A trip. Separately, **RETRY latch-off applies to FORWARD overcurrent only**; reverse faults reconnect automatically once VOUT falls 100 mV below VIN. Both halves of the objection fall away. | closed | 2026-08-22 |
| **P-14** | **MAX17048 sense point — cell side or protected side?** | The protection adds ~51 mΩ; at 1 A that is ~51 mV of IR drop the voltage-only gauge cannot compensate (several % SOC). Cell side avoids it but sits exposed to the reversed-cell fault. | 2026-08-22 |
| **P-15** | **3V3 rail budget under simultaneous worst case** — NFC TX + audio + LoRa + backlight + Wi-Fi against a 2 A TPS63020 with current-limit foldback. | Foldback means brownout resets and SD corruption rather than a clean fault. May force firmware mutual-exclusion. | 2026-08-22 |
| **P-16** | **Repurpose one XGPIO as `ACC_DETECT`?** Firmware currently cannot know an accessory is present before enabling the switched rail or choosing pull configurations. | Changes the published count from 11 XGPIO to 10. Free once PCAL9535A programmable pull-ups exist. **Not adopted** — ruling D specifies 11. | 2026-08-22 |
| **P-17** | **ST25R3916 or ST25R3916B?** | The B adds Active Wave Shaping and finer driver stepping (both recover margin at 3.3 V) but **removes capacitive sensing** on CSI/CSO, losing low-power capacitive tag detect. With AWS the VDD_AM capacitor changes to 10–50 nF. Schematic-time decision, product call. | 2026-08-22 |
| **P-18** | **Accessory I²C segmentation — buffer alone, or add a mux?** | An accessory holding SDA low blinds the fuel gauge **and** all XGPIO simultaneously; nothing prevents address collision on 0x36 or 0x20–0x27. | 2026-08-22 |
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
| **M-06** | D-074…D-078 | **Display and connector LOCKED.** `ER-TFT035IPS-6` + `ER-TPC035-6`, `J1` = Hirose `FH69-50S-0.5SH`, mating proven from both manufacturers' drawings. |
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
