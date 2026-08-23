# FBV2-S1-005 — Full Beta v2 I²C devices and IMU (Sheet 05)

**Task gate `FBV2-S1-I2C-IMU` = PASS.**
Date: 2026-08-23 · Scope: `05_i2c_devices.kicad_sch` only.
Sheets `06`–`09`, the PCB, mechanical CAD, firmware, Beta-DM and frozen Beta are untouched.

**ERC 46 → 45. Zero added, one removed. Errors unchanged at 2, both inherited.**

---

## 0. A correction to the reported ERC baseline

The FBV2-S1-004 / 004B / 004C narratives quote **"ERC 68"**. The stored reports do not
say that. Measured from the files themselves:

| report | messages | errors | warnings |
|---|---|---|---|
| `FBV2-S1-erc-beta-dm-baseline.rpt` | 58 | 5 | 53 |
| `FBV2-S1-erc.rpt` | 55 | 4 | 51 |
| `FBV2-S1-002-erc.rpt` | 63 | 4 | 59 |
| `FBV2-S1-003-erc.rpt` | 64 | 4 | 60 |
| `FBV2-S1-004-erc.rpt` | **46** | 2 | 44 |
| `FBV2-S1-004B-erc.rpt` | **46** | 2 | 44 |
| `FBV2-S1-004C-erc.rpt` | **46** | 2 | 44 |
| **`FBV2-S1-005-erc.rpt`** | **45** | **2** | **43** |

The **68 was a transcription error** carried forward across three tasks. The *deltas* those
tasks reported — "zero added, zero removed" — are correct and are reproducible from the
stored reports; only the absolute number was wrong. Sheet `04`'s migration genuinely took
the count from 64 to 46. This file is the corrected record.

A second trap found while re-running the gate: `kicad-cli sch erc --severity-all` also
includes **Exclusions** and reports **104** on the same unmodified design. Every count in
this programme is `--severity-error --severity-warning`, matching the stored reports'
`Report includes: Errors, Warnings` header. **Compare like with like or the gate is
meaningless.**

---

## 1. What Sheet 05 actually contained, and what it now contains

| | before | after |
|---|---|---|
| parts | 9 (`U4`, `R18`, `R19`, `R20`, `C6`, `C7`, `TP3`, `TP4`, `TP5`) | 11 (`+ R118`, `R119`) |
| I²C pull-ups | `R19` / `R20` **4.7 k** | **2.2 k** |
| BMI270 `SDO` | hard-wired to `GND` | `R118` 0 Ω **FIT** to GND, `R119` 0 Ω **DNP** to `+3V3` |
| sheet notes | 2, partly obsolete | 4, every claim datasheet-cited |
| `U4` `Note` property | none | full strap and land-pattern verification record |

Project totals: **303 components, 0 duplicate references, 0 without a footprint.**
`fork_equivalence.py` **PASS** (sheet `05` moves from `norm` to `changed`),
`netclass_probe.py` **PASS**, PCB still **bit-identical** to Beta-DM.

---

## 2. The BMI270 was re-derived, not inherited

Source: **`BST-BMI270-DS000-08`, document revision 1.6, March 2026** — fetched and text-extracted
in full (150 pages). Every strap below was checked against it rather than copied from Beta-DM.

| pin | net as drawn | datasheet requirement | verdict |
|---|---|---|---|
| 1 `SDO` | GND via `R118` | *"pulled to GND"* → `0b1101000` = **0x68**; VDDIO → 0x69 | **correct** |
| 12 `CSB` | `+3V3` | *"For using I2C, it is recommended to hard-wire the CSB line to VDDIO"* | **correct** |
| 13 `SCx` | `I2C_SCL_INT` | SCL in I²C mode | correct |
| 14 `SDx` | `I2C_SDA_INT` | SDA in I²C mode | correct |
| 2 `ASDx` | `+3V3` | *"If secondary interface is unused, ASDx and ASCx can be connected to VDDIO or left unconnected. **Do not connect to GND.**"* | **correct — and the tempting alternative is explicitly forbidden** |
| 3 `ASCx` | `+3V3` | as above | **correct** |
| 9 `INT2` | DNC | *"If INT1 and/or INT2 are not used, please do not connect them (DNC)."* | correct |
| 10 `OCSB` | DNC | OIS unused; DNC is the listed option | correct |
| 11 `OSDO` | DNC | OIS unused; DNC is the listed option | correct |
| 5 `VDDIO` / 8 `VDD` | `+3V3`, `C6` / `C7` 100 nF | *"recommended to use 100nF decoupling capacitors at pin 5 (VDDIO) and pin 8 (VDD)"* | correct |

**Nothing on this sheet was wrong.** The Beta-DM straps survive a line-by-line re-derivation.
That is worth stating plainly, because the brief said *"do not blindly copy Beta-DM straps"*
and the honest outcome of not copying them is that they were already right.

### Supply and startup

`VDD` **1.71–3.6 V**, `VDDIO` **1.2–3.6 V**, both at 3.3 V here. **No sequencing constraint** —
either rail may be applied first, either may be switched off with the other live, and there is
**no minimum slew-rate constraint**. `tPO` = **2 ms** to interface-operational. After every POR
or soft reset the device sits in **suspend** and needs the **8 kB configuration-file upload**
(`INIT_CTRL` handshake, `INTERNAL_STATUS.message == 0b0001` within 20 ms) before any feature
works. ESD: 2 kV HBM.

### Current, and why that settles the sleep question

| mode | typ |
|---|---|
| A+G performance | 970 µA |
| A+G normal | 685 µA |
| A+G low power @ 25 Hz | 420 µA |
| Accel-only normal | 210 µA |
| **Accel-only low power** | **down to 4 µA** (10 µA spec'd @ 25 Hz) |
| Advanced features | **+3 µA** |
| Suspend | 3.5 µA |

**MPN.** `BMI270` is a flat orderable part, not a configured ordering scheme, so D-096 does not
bite. Bosch's own order code `0 273 017 008` is recorded in the datasheet header. LGA-14,
2.5 × 3.0 × 0.83 mm, RoHS, halogen-free, MSL 1, 260 °C peak reflow.

### One capability the brief asked for that does not exist

The brief lists *"tap / double tap if supported"*. **The BMI270 has no tap or double-tap
feature.** The word does not appear in the datasheet. Its feature set is:

> Significant motion · Any motion · Motion detect · No motion · Stationary detect ·
> Wrist wear wakeup · Wrist-worn step counter and detector · Activity change recognition ·
> Push arm down · Pivot up · Wrist jiggle · Flick in/out

So of the brief's list: **wake-on-motion ✓, significant motion ✓, orientation change ✓
(via the orientation/flat features, with axis remapping written to the config registers),
raise-to-wake ✓ (this is "wrist wear wakeup"), FIFO ✓ (2048 bytes). Tap ✗ — not supported
by this part in any configuration.** Anything tap-like has to come from firmware thresholding
raw accelerometer data, and that is a firmware question, not a hardware gap. **No hardware
change is proposed for it.**

---

## 3. Motion / wake — the GPIO3 audit, done arithmetically

`BMI270 INT1` → `R18` 220 Ω → `BMI270_INT1_STRAP` → **GPIO3** (module pin 15), with
**`R110` 10 kΩ pull-down** on sheet `02` (added by FBV2-S1-002) and `TP3` on the node.
GPIO3 is the ESP32-S3 **JTAG-source strapping pin**.

### Boot-state safety — proven, not asserted

Three measured facts close this:

1. **`INT1_IO_CTRL` resets to `0x00`.** Bit 3 is `output_en`, so **the INT1 output driver is
   disabled at power-on and after soft reset.** The pin is high-Z until firmware writes it.
2. **Firmware cannot write it early.** The device is in suspend after POR and requires the
   8 kB config upload before features or interrupts function.
3. **ESP32-S3 strap hold time `tH` = 3 ms minimum** (datasheet Table 3-2), and GPIO3's default
   configuration is **"Floating"** (Table 3-1) — it has *no* internal pull, so the level in the
   strap window is defined by `R110` **alone**.

> **The IMU physically cannot reach the strapping window.** This is a timing proof, not a
> margin argument.

### The pull direction forces the interrupt polarity — and that is a real finding

`INT1_IO_CTRL.od` selects push-pull (0) or open-drain (1); `.lvl` selects active-low (0) or
active-high (1). With **`R110` a pull-DOWN**:

- **open-drain is unusable.** An open-drain output can only pull low. Into a pull-down the
  line is low in both states and **no edge ever appears.** Configuring it that way would
  produce a silently dead interrupt that looks like a firmware bug for a week.
- **push-pull + active-high is correct and is the only correct choice.** It also happens to be
  the right polarity for the other reason below.

**GPIO3 = `RTC_GPIO3`** (ESP32-S3 Table 2-8; the chip has 22 RTC GPIOs, `GPIO0`–`GPIO21`), so
it supports **EXT0/EXT1 deep-sleep wake**, which wakes on a **high** level. Active-high into a
pull-down is exactly the arrangement EXT0/EXT1 wants, and the pull-down guarantees a defined
low while the IMU is unconfigured or the rail is settling.

> **Firmware contract, mandatory:** `INT1_IO_CTRL.od = 0` (push-pull),
> `INT1_IO_CTRL.lvl = 1` (active high), `output_en = 1`. **Open-drain is forbidden on this net.**

### B-44 CLOSED

B-44 recorded that *"the BMI270 INT pad drive current was NOT retrieved"*. It now is:
**`IOH`/`IOL` ≤ 2 mA with `VOH` ≥ 0.8 × VDDIO and `VOL` ≤ 0.2 × VDDIO** (Table 1). The load is
`R18` 220 Ω + `R110` 10 kΩ = 10.22 kΩ, so a high assertion sources **3.3 V / 10.22 kΩ = 323 µA**
— **6× inside the specified pad capability** — and GPIO3 settles at **3.23 V**, far above the
ESP32-S3 `VIH`. The `DRV` register (NVM-backed, reset `0xAA`) can raise pad strength further if
ever needed; it is not needed.

### The interrupt stays on the native GPIO

The brief asked whether to move the IMU interrupt behind a PCAL9535A. **No.** Moving it there
would put motion wake behind an I²C transaction, which cannot wake the SoC from deep sleep on
its own and would add tens of milliseconds of latency to every motion event; and `U2` is
**16/16 full** (B-37) while `U3`'s single free pin is `RESERVED_SPARE`. There is **no
boot-safety reason** to move it — the timing proof above removes the only one that was ever
offered. It stays native.

---

## 4. INT2 — evaluated, and deliberately left NC

| option | verdict |
|---|---|
| A — spare test point | **rejected** |
| B — internal PCAL9535A input | **rejected** |
| **C — nothing / NC** | **SELECTED** |

Reasons, in order of weight:

1. **Bosch instructs it.** *"If INT1 and/or INT2 are not used, please do not connect them
   (DNC)."* Option A puts a stub on a pin the manufacturer says to leave open.
2. **One pin is genuinely sufficient.** *"If just one interrupt pin is used all interrupts may
   be mapped to this interrupt pin."* The source is then read from `INT_STATUS_0` /
   `INT_STATUS_1` — one extra I²C read after wake, which the host is doing anyway.
3. **Two pins would import a constraint we do not have.** In latched mode, *"if more than one
   interrupt pin is used … all interrupts in `INT_STATUS_0` should be mapped to one interrupt
   pin and all interrupts in `INT_STATUS_1` should be the other."* Using one pin avoids that
   partition entirely.
4. **`RESERVED_SPARE` stays reserved**, per the brief's default preference and D-094.
5. **The no-respin policy is already satisfied without spending anything**: pad 9 exists on the
   land pattern. If a second interrupt is ever wanted it is a wire, which is exactly what D-049
   asks for.

**This is not surfaced as an opportunity.** The benefit — separating FIFO-watermark from motion
without an I²C read — is not worth a pin, a pad, or a departure from the manufacturer's
instruction.

---

## 5. Internal I²C pull-ups — 4.7 kΩ was marginal at 400 kHz

The internal bus, measured from the netlist (not assumed):

| node | on the bus | Cin used |
|---|---|---|
| `U1` ESP32-S3-WROOM-1 | GPIO1 / GPIO2 | 5 pF (pad + module trace) |
| `U2` expander @ 0x20 | SDA/SCL | 10 pF |
| `U3` expander @ 0x21 | SDA/SCL | 10 pF |
| `U4` BMI270 | SDx/SCx | **5 pF (datasheet `Cin`)** |
| `U14` MAX17048 | SDA/SCL | 10 pF |
| `U16` TCA9517A **A-side** | SDAA/SCLA | **13 pF (datasheet `CI`/`CIO` max)** |
| `J1` pins 44/45 → CTP through the 50-pin FPC | CTP_SDA / CTP_SCL | 18 pF (device + flex) |
| `TP4` / `TP5` | — | 2 pF |
| PCB trace | ~120 mm | 12 pF |
| | **worst case** | **≈ 85 pF** |

I²C rise time is `t_r = 0.8473 · R · C` (10 %→90 % on an RC pull-up):

| `R` | `t_r` at 85 pF | 100 kHz limit 1000 ns | 400 kHz limit 300 ns |
|---|---|---|---|
| **4.7 kΩ (as inherited)** | **338 ns** | pass | **FAIL** |
| 3.3 kΩ | 238 ns | pass | pass, 21 % margin |
| **2.2 kΩ (selected)** | **158 ns** | pass | **pass, 47 % margin** |

At a *typical* 60 pF, 4.7 kΩ gives 239 ns and passes. **That is precisely the problem: it is a
part that works on the bench and fails on the unit with the longest flex and the widest
tolerances.** The programme's own bring-up rule — 100 kHz first, then 400 kHz — would have
found it late, on hardware, as an intermittent.

**Sink-current check before recommending, as the brief required:**

```
I_sink at VOL = 0.4 V:  (3.3 - 0.4) / 2200 = 1.32 mA
```

| device | specified sink | margin at 1.32 mA |
|---|---|---|
| BMI270 | `IOL` ≤ 2 mA at `VOL` ≤ 0.2·VDDIO; `DRV` boosts pull-down in I²C mode | 1.5× |
| TCA9535 / PCAL9535A | `IOL` **6 mA** on SDA (T<sub>j</sub> ≤ 85 °C) | 4.5× |
| ESP32-S3 | ≥ 20 mA | 15× |
| I²C-bus specification minimum | 3 mA at 0.4 V | 2.3× |
| absolute floor (spec `R_min`) | (3.3 − 0.4)/3 mA = **967 Ω** | 2.2 kΩ is 2.3× above it |

**No duplicate pull-up pairs exist on this net.** `R19`/`R20` are the only ones; the netlist
confirms nothing else pulls up `I2C_SDA_INT` / `I2C_SCL_INT`. `R49`/`R50` (4.7 k, **DNP**)
belong to the *switched accessory segment* on sheet `09`, on the far side of `U16`, and are a
different net. The sheet note now says so explicitly so nobody "helpfully" adds a second pair.

**Static cost:** none at idle (the bus rests high). During low phases 2.2 kΩ draws 1.5 mA per
line versus 0.7 mA, present only while a line is actually held low — a few percent duty at
worst, and irrelevant next to the 685 µA IMU it talks to.

**One residual unknown, stated rather than buried:** whether the `ER-TPC035-6` touch flex
carries its own pull-ups is not documented in anything obtained. If it does, the parallel
combination lowers `R` further, which moves rise time in the *safe* direction but raises sink
current — still inside every device's capability even at 1 kΩ equivalent. First-article check.

---

## 6. External I²C fault containment (P-18) — audited, nothing implemented

**The most important fact about P-18 is that its threat model is not live.** On the current
board `U16` **TCA9517A is DNP**, `R49`/`R50` are **DNP**, `U15` is **DNP** and `D2`/`D3` are
**DNP**. There is no fitted external I²C path at all. Whatever is chosen at Sheet 09 migration
costs **no rework**, because nothing has been fitted or ordered.

### What the TCA9517A already gives, and it is more than it is credited with

TI SCPS245E: *"**VCCA is only used to provide the 0.3 × VCCA reference** to the A-side input
comparators and for the power-good-detect circuit. **The TCA9517A logic and all I/Os are
powered by the VCCB pin.**"*

`VCCB` = `ACC_3V3_SW`, and `EN` = `ACC_PWR_EN` — the same signal that gates the accessory load
switch. So when the accessory rail is off the buffer is **completely unpowered and high-Z on
both sides**. That is a *harder* disconnect than an I²C mux, which stays powered.

### The failure that is real, and it is not electrical

Once the accessory is powered and a broken accessory holds `SDA` or `SCL` low:

- The host can attempt the standard **9-clock bus-recovery pulse train**. That frees the common
  case — a target left mid-byte by an aborted transfer — and costs **nothing**.
- If it does not clear, the host must de-assert `ACC_PWR_EN` to disconnect the accessory. But
  **`ACC_PWR_EN` is `U3` P17 — an I²C expander output, behind the very bus that is stuck.**
  The disable control lives on the wrong side of the fault.
- `R17` 100 kΩ pulls `ACC_PWR_EN` low by default, and the expanders return their ports to
  inputs only on **their own** power-on reset — not on an MCU reset. So the escape from a hard
  short is a **`+3V3` power cycle**, not a watchdog reset.

**That is the honest state of P-18: the buffer is not the weak part; the location of its
disable control is.**

### Comparison as the brief asked

| | **A. keep TCA9517A** | **B. TCA4307-class** | **C. I²C mux / switch** |
|---|---|---|---|
| fault isolation when rail off | **excellent** — device unpowered, both sides high-Z | excellent — powered-off high-Z | good — mux still powered |
| **automatic** stuck-bus recovery | **none** | **yes** — auto-disconnect + up to 16 `SCLOUT` pulses, no host involvement | none |
| hot-plug into a live bus | **no precharge** — insertion dumps accessory C onto SDA/SCL | **1 V precharge on all SDA/SCL** | none |
| state visible to host | none | **`READY` open-drain** | via register (needs the bus) |
| solves address collision | **no** | **no** | **only by time-multiplexing** |
| control path | `EN` on `U3` P17 — behind the fault | `EN` optional; recovery is autonomous | control is behind the fault |
| added BOM | 0 | 0 net (replaces) | +1 device |
| PCB | none | **not pin-compatible** with the TCA9517A DGK pinout — re-route | new placement |
| level translation | 3.3 ↔ up to 5.5 V | single-supply only | varies |
| firmware | 9-clock recovery routine | less | mux driver + arbitration |
| sourcing | locked, in production | **must be confirmed against a live listing (D-096)** | — |

**Level translation is not a requirement**: sheet `09` states *"COMMUNITY HEADER LOGIC = 3.3 V
ONLY / NO 5 V-TOLERANCE CLAIM"*, and `VCCB` is `ACC_3V3_SW` = 3.3 V. So the TCA9517A's one
unique capability is unused, which removes the main argument for keeping it.

**No buffer of any kind solves address collision.** A collision is a protocol problem and is
solved by the address registry in §7 plus the `0x50` accessory-ID EEPROM — not by hardware. A
mux "solves" it only by never having both segments live at once, which would make touch and the
fuel gauge unreachable while an accessory transaction is in flight.

### Recommendation — flagged, not implemented

> **O-4 (NEW, requires CTO decision):** evaluate replacing `U16` with a **TCA4307-class
> hot-swap I²C buffer with stuck-bus recovery** *at Sheet 09 migration*.
>
> The case for it: the community header is a **hot-plug connector by definition**, and the
> TCA4307 is the only option that both **pre-charges on insertion** and **recovers a stuck bus
> without the host** — which is exactly the failure the TCA9517A cannot escape, because its own
> disable control sits behind the bus it protects. It costs **no rework** (everything is DNP)
> and **no net BOM** (it replaces a part).
>
> The case against it: it is **not pin-compatible**, so the `U16` area must be re-routed; the
> PCB is being redone for Beta v2 anyway, but that is an assumption about scheduling, not a
> fact about this task. The exact MPN must come from a **live listing** before anything is
> locked (D-096) — the datasheet was obtained, the availability was not.
>
> **Nothing is implemented here. `U16` remains TCA9517A on the schematic.** If the CTO declines
> O-4, the fallback is firmware-only: a 9-clock recovery routine plus the documented
> "hard short needs a `+3V3` power cycle" limitation, which is adequate for Beta v2.

---

## 7. I²C address registry

Written up separately and made normative:
**[`../architecture/I2C_ADDRESS_REGISTRY.md`](../architecture/I2C_ADDRESS_REGISTRY.md)**.

Summary of the audit: **no collision exists** among `0x20`, `0x21`, `0x36`, `0x38`, `0x68` and
the reserved `0x50`; none of them falls in the I²C reserved ranges `0x00`–`0x07` or
`0x78`–`0x7F`; and `0x50` is not used internally, as the brief requires.

**Verification status is not uniform, and the registry says which is which.** `0x20`/`0x21` and
`0x68`/`0x69` were confirmed from manufacturer datasheets *in this task*. `0x36` (MAX17048) and
`0x38` (FT6236) are **carried from earlier decisions** — every fetch of the Analog Devices and
FocalTech datasheets failed here (analog.com timed out, the Mouser mirror returned 13 kB of
HTML, focuslcds returned 403). They are almost certainly right and they are consistent across
every prior audit, but they are not datasheet-cited *by this task* and are marked accordingly.

---

## 8. Test and rework provisions

| provision | state | why |
|---|---|---|
| `TP3` on `BMI270_INT1_STRAP` | present | the strap node is directly measurable |
| `TP4` / `TP5` on SDA / SCL | present | bus probing without a fixture |
| supply test point on the IMU | **not added** | `+3V3` is already probed elsewhere; a second pad buys nothing |
| second TP on `BMI270_INT1_RAW` | **not added** | `TP3` reads the IMU state faithfully through 220 Ω; the only extra fault it would distinguish is "`R18` open", a solder defect |
| **address strap resistors** | **ADDED — `R118` / `R119`** | see below |
| alternate IMU footprint | **not added** | the brief forbids it and there is no second-source case |

### `R118` / `R119` — the one hardware addition

`SDO` was **hard-wired to GND**. Under D-049 that means the *only* escape from an address
collision at `0x68` is cutting a trace on a 0.25 mm pad. It is now:

```
+3V3 ──[ R119  0R  DNP ]──┐
                          ├── BMI270_SDO_ADDR ── U4 pin 1 (SDO)
GND  ──[ R118  0R  FIT ]──┘
```

**Fit one only** — fitting both shorts `+3V3` to GND, and the sheet note says so in capitals.
`R118` fitted gives **0x68**; moving the 0 Ω to `R119` gives **0x69**.

Why this address and not another: **`0x68` is the single most collision-prone address on a
community I²C bus.** MPU6050, MPU9250, ICM-20948 and the DS3231/DS1307 RTCs all default to it,
and those are exactly the parts a hobbyist accessory is built from. Reserving the address in a
document does not stop a $2 module from arriving at it. Two 0603 pads, one populated, convert
that from a respin into a rework — which is the entire point of D-049.

**This is a hardware addition and is called out as one.** It is within the brief's §8, which
asks for *"address/strap resistor footprints accessible"*, and it is reported in the summary
rather than slipped in.

---

## 9. Power and sleep

**The IMU stays permanently powered from `+3V3`. No load switch.**

| | always-on IMU | switched IMU supply |
|---|---|---|
| standby draw | **≈ 7–10 µA** (accel-only low power 4 µA + advanced features 3 µA; 10 µA spec'd at 25 Hz) | ~0.5–1 µA switch quiescent |
| saving | — | **≈ 9 µA** |
| wake-on-motion | **works** | **destroyed** — an unpowered IMU detects nothing |
| re-init cost on every wake | none | 8 kB config upload + ≤ 20 ms, on every resume |
| BOM / area / control pin | none | +1 load switch, +1 expander pin (and there is one spare in the whole design) |

Nine microamps is far below the ESP32-S3's own deep-sleep floor and is not measurable against
the fuel gauge, the expanders' quiescent draw or self-discharge. **Trading wake-on-motion —
the reason the IMU is on the board — for it would be a bad deal at any price.** The brief's
stated preference and the arithmetic agree.

---

## 10. Land pattern — the "DO NOT ROUTE" note is discharged

The old sheet note said *"FOOTPRINT NOT FAB-APPROVED / DO NOT ROUTE UNTIL BMI270 LAND PATTERN
IS REVIEWED."* It has now been reviewed.

§8.3 of the datasheet is a **raster drawing** — no vector geometry and no dimensions in the text
layer beyond *"Pad tolerance: ±50 µm (L, W)"*. It was rendered at 12× and the pad rectangles
measured programmatically from the pixels, calibrated on the printed **0.5 mm** column pitch
(514.2 px → 1028.3 px/mm):

| dimension | Bosch §8.3 | `Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270.kicad_mod` | |
|---|---|---|---|
| side-pad size | 0.475 × 0.25 | **0.475 × 0.25** | ✓ |
| end-pad size | 0.25 × 0.475 | **0.25 × 0.475** | ✓ |
| side-pad column x | measured ±1.1626 | **±1.1625** | ✓ |
| side-pad rows y | ±0.25, ±0.75 (0.5 pitch, symmetric) | **±0.25, ±0.75** | ✓ |
| end-pad row y | 0.675 to pad edge + 0.2375 = **0.9125** to centre | **±0.9125** | ✓ |
| end-pad x | 0, ±0.5 | **0, ±0.5** | ✓ |
| pad-4 right edge to centreline | printed **0.925** | −1.1625 + 0.2375 = **−0.925** | ✓ |
| body | 3.0 × 2.5 | F.Fab 3.0 × 2.5 | ✓ |
| pin 1 | top-left, marker | pad 1 at (−1.1625, −0.75), silk marker | ✓ |

**Every printed dimension — 0.5, 0.25, 0.475, 0.675, 0.925, 3.0, 2.5 — reproduces.** The
peripheral pin order (1–4 left, 5–7 bottom, 8–11 right, 12–14 top) matches, which is the error
that would have been fatal and silent. Pads carry `F.Cu`/`F.Mask`/`F.Paste` with default
margins; courtyard and fab outline are present.

> **The land pattern is correct. The "do not route" gate is discharged at library level.**
> Paste-aperture reduction and courtyard-clearance policy remain part of the **FBV2-S2**
> footprint audit (B-29 / B-03) — that is a house-rules question, not a Bosch-conformance one.

---

## 11. Opportunity and simplification scan

| | finding |
|---|---|
| **A. nearly-free capability** | `R118`/`R119` address strap (implemented, §8). **O-4** external-buffer upgrade (flagged, §6). |
| **B. unnecessary legacy components** | **none found.** Every part on the sheet earns its place. |
| **C. duplicated pull-ups** | **none on the internal bus** — verified from the netlist, not by inspection. Whether the touch flex adds its own is a first-article check. |
| **D. unnecessary native GPIO use** | **none.** GPIO3 is the *right* place for the IMU interrupt (§3) and is the only one that can wake the SoC from deep sleep. |
| **E. diagnostic / test opportunities** | `TP3`/`TP4`/`TP5` already cover the sheet; two further candidates evaluated and rejected (§8). |
| **F. standby-power simplification** | evaluated and rejected on the numbers (§9). |

**Exactly one item requires a CTO/user decision: O-4.** Everything else is either implemented
inside the brief's authorisation or explicitly declined with a reason.

---

## 12. Blockers

| id | state |
|---|---|
| **B-44** — BMI270 INT pad drive not retrieved | **CLOSED.** `IOH`/`IOL` ≤ 2 mA, `VOH` ≥ 0.8·VDDIO; load draws 323 µA, 6× margin. |
| **B-59** (new) | **`ER-TPC035-6` touch-flex pull-ups unknown.** If the module carries its own, the effective pull-up drops below 2.2 kΩ. Direction is safe (faster edges), sink current still inside spec even at a 1 kΩ equivalent. **First-article measurement.** |
| **B-60** (new) | **`0x36` and `0x38` are not datasheet-cited *by this task*.** Analog Devices and FocalTech fetches all failed. Both are consistent across every prior audit and are almost certainly right — but "almost certainly" is not the standard this programme uses. **Confirm by bus scan at first article.** |
| **P-18** | **UNCHANGED, and now precisely characterised** (§6). Decision deferred to Sheet 09 migration via **O-4**. |
| **B-37** | unchanged — `U2` 16/16, `U3` one `RESERVED_SPARE`, still not consumed. |
| **B-29 / B-03** | unchanged — footprint audit at FBV2-S2. The BMI270 land pattern is now one fewer item on that list. |

---

## 13. What was NOT done

No new buffer, no I²C mux, no load switch, no second interrupt pin, no alternate IMU footprint,
no supply test point, no change to `U2`/`U3` (they live on sheet `08`), no change to `R49`/`R50`
or `U16` (sheet `09`), no PCB edit, no firmware.

**One inherited discrepancy is recorded and left alone:** the schematic `Value` on `U2`/`U3`
still reads **`TCA9535PWR`** while **D-061 locked NXP `PCAL9535APW,118`**. The address base is
identical (`0100 A2A1A0` → 0x20–0x27) so nothing in this task depends on it, and both parts are
on **sheet 08**, which is not authorised here. It belongs to the Sheet 08 migration and is
flagged so it is not discovered at BOM time.
