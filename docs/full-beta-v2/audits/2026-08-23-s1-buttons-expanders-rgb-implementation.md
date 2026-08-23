# FBV2-S1-008 — Buttons, PCAL9535A expanders and the front RGB status light

**Task:** migrate Full Beta v2 sheet `08_buttons_expanders`, correct the sheet-07
first-build IR receiver, and add one full-RGB front-facing status light.
**Date:** 2026-08-23.
**Baseline:** remote `master` at `d894913` (FBV2-S1-007 documentation commit).
**Verdict: PASS.** ERC 42 messages / 1 error / 41 warnings — **byte-identical
violation set to the pre-task working tree, and better than the 45 / 2 / 43
baseline that stood before sheet 08 was touched at all.**

> **This task was interrupted by a session usage limit and resumed.** Section 0
> records what was recovered, what was kept, what was finished and what was
> repaired. Nothing was restarted from scratch and nothing valid was discarded.

---

## 0. Recovery record

### 0.1 What existed when the session resumed

`git log` showed local `master` exactly equal to `origin/master` at `d894913`.
**No FBV2-S1-008 work had been committed and nothing was staged.** All of it was
uncommitted working-tree change:

| path | state | verdict |
|---|---|---|
| `07_ir.kicad_sch` | modified | **VALID — kept** |
| `08_buttons_expanders.kicad_sch` | modified, +3261/−1590 | **VALID but INCOMPLETE — finished** |
| `aqroot-Beta-v2.kicad_sch` | modified, hierarchical pins re-cut | **VALID but INCOMPLETE — finished** |
| `libraries/AQROOT_Beta.kicad_sym` | +1086 lines | **VALID — kept** |
| `libraries/AQROOT_Beta.pretty/MEIHUA_MHPA3528RGBCT_PLCC4_3.5x2.8mm.kicad_mod` | untracked, new | **VALID — kept** |
| `docs/full-beta-v2/**` | **untouched** | **MISSING — written in this session** |
| `hardware/beta-dm/fab/*.zip`, `hardware/beta/mechanical/` | untracked, timestamps 2026-08-20/21 | **PRE-EXISTING, not this task — left alone** |

No PCB file, no sheet 09, no Beta-DM and no frozen Beta file was modified by the
interrupted session, and none was modified by this one.

### 0.2 What the interrupted session had already got right

This was good work and it was kept almost intact:

- **Both expanders really were converted**, not renamed. `AQROOT_Beta:PCAL9535APW`
  is a purpose-built symbol carrying the NXP datasheet URL, `MPN` =
  `PCAL9535APW,118`, an `I2C_Address` property, and a `Note` that records the
  Agile-I/O register map. The old `Interface_Expansion:TCA9535PWR` symbol is gone
  from the sheet entirely — including from the `lib_symbols` cache. The only
  remaining occurrences of the string "TCA9535" are prose inside migration notes
  explaining what was replaced and why.
- **Address straps verified correct.** `U2` A0 = A1 = A2 = GND → `0x20`.
  `U3` A0 = `+3V3`, A1 = A2 = GND → `0x21`. Both preserved.
- **HOME really is gone.** `SW8` and its pull-up `R10` were deleted, not hidden
  and not marked DNP. No `BTN_HOME_N` net exists anywhere in the design.
- **Volume buttons were not invented.**
- **`TOUCH_INT_N` and `SX1262_DIO1` were landed** on `U2` P16 / P17 with matching
  root-sheet plumbing, and the retired `RGB_R/G/B_CTL`, `ROOTPROBE_IRQ_READY_N`
  and `XGPIO10-13` hierarchical pins were removed from the root sheet.
- **The RGB part selection is sound and was verified independently in this
  session** — see §5. MPN, package, topology, stock and the resistor arithmetic
  all hold up.
- **Zero DNP on the sheet.** Nothing was blindly carried forward: buttons,
  expanders, pull resistors, the LED and its three resistors are all FITTED.

### 0.3 What was wrong or missing, and what was done about it

The interrupted session had written its own honest note into the schematic:

> *"THREE SIGNALS THE BRIEF ASKS FOR HAVE NO HOME: BQ25185_STAT1, BQ25185_STAT2,
> SD_CARD_DETECT_N … THE DEMAND LIST IS 34 WIDE AND THE HARDWARE IS 32. THIS
> NEEDS A CTO RULING."*

That diagnosis was correct and it is the substance of this task. Concretely:

| defect | resolution |
|---|---|
| `BQ25185_STAT1`, `BQ25185_STAT2`, `SD_CARD_DETECT_N` **not landed** | landed on `U2` P05/P06/P07 |
| `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_DETECT_N`, `ACC_POWER_FAULT_N` **not landed** — `U3` P12–P15 were bare `no_connect` flags | landed on `U3` P12–P15 |
| **`RESERVED_SPARE` did not exist** anywhere in the design, against D-094 | created on `U23` P03 with `R130` 100 kΩ and `TP41` |
| RGB occupied `U2` P05–P07 — the pins D-089 had reserved for charger telemetry | RGB moved to the added `U23`; **core, community and safety functions placed first** |
| the 3-pin shortfall was flagged but **not resolved** | resolved by `U23`, §4 |
| root-sheet UUIDs written with the **non-hex prefix `fb080r00-`** | repaired to `fb080d00-`; KiCad silently reassigns invalid UUIDs on save and would have destroyed pass traceability |
| no documentation of any kind | this audit plus seven updated documents |

Nothing was reverted wholesale. The only element deliberately *removed* from the
recovered work is the three `FRONT_RGB_*_N` local labels on `U2` P05–P07, which
moved to `U23`.

---

## 1. Sheet-07 correction — `TSOP38438` → `TSOP38238`

**O-5 is CLOSED.** FBV2-S1-007 locked the AGC4 `TSOP38438` while the same brief
listed Sony/SIRC among the protocols to receive; Vishay document 82491 Rev 2.1
says those cannot both be true.

- `U6` is now **`TSOP38238` (AGC2)** — `lib_id`, `Value`, `MPN` and `Description`
  all changed, and the on-sheet note rewritten.
- **`TSOP38438` is retained as a documented drop-in fallback.** Its symbol stays
  in `AQROOT_Beta.kicad_sym`. Both parts appear in the same Vishay parts table,
  share the Minicast body 5.0 W × 6.95 H × 4.8 D mm, the pinning
  **1 = OUT / 2 = GND / 3 = VS**, the leaded mounting and one shared electrical
  table. Reverting is a `lib_id` change and nothing else.
- Every FBV2-S1-007 calculation survives unchanged: `VS` 2.0–5.5 V,
  `ISD` 0.25 / 0.35 / 0.45 mA at 3.3 V, active-low output with a **30 kΩ internal
  pull-up** so no external pull-up exists or is needed, ±45° acceptance,
  f₀ = 38 kHz with a 3 dB bandwidth of f₀/10. The `R21` 100 Ω + `C11` 4.7 µF
  filter, its 339 Hz corner and its 41 dB of rejection at the carrier are
  untouched.

**Why AGC2 is the right first build.** The suitable-data-format table marks AGC2
*Yes* for NEC, RC5/RC6, Thomson RCA 56 kHz, Sharp, **Sony** and Mitsubishi. AGC4
is marked **No for Sony code**. The mechanism is the gap requirement: after a
burst longer than 10 cycles, AGC2 needs a gap of more than 5× the burst and
accepts 10–70 cycles per burst, while AGC4 needs more than 15× and accepts only
10–35. SIRC violates the AGC4 limit.

**What is given up.** AGC4 adds the Fig. 15 suppression of high-modulation
fluorescent-lamp interference that AGC2 (Fig. 14 only) does not have. That is the
entire cost — a fluorescent-lighting robustness margin, not a protocol.

---

## 2. PCAL9535A — verified against the primary source

The NXP datasheet was retrieved in this session and read directly:
**PCAL9535A, Rev. 2 — 23 January 2015.** Every claim the schematic makes about
the part was checked line by line; **every one reproduces.**

| item | datasheet | in the design |
|---|---|---|
| MPN / package | `PCAL9535APW` — TSSOP24, **SOT355-1**, body 4.4 mm | `PCAL9535APW,118`, `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` |
| supply | **V_DD 1.65 – 5.5 V** | `+3V3` |
| bus | Fast-mode 400 kHz, 5 V-tolerant I/O | internal I²C at 400 kHz |
| slave address | **`0 1 0 0 A2 A1 A0`** | `0x20` / `0x21` / `0x22` |
| Configuration 06h/07h | **default `FF`** — every pin a high-Z **input** | the whole safe-state argument rests on this |
| Output port 02h/03h | **default `FF`** — a pin drives **HIGH** the instant it becomes an output | no glitch on the input→output transition |
| Pull-up/pull-down enable 46h/47h | **default `00`** — internal 100 kΩ **disabled** | so a high-Z pin leaks only I_IH/I_IL |
| Pull-up/pull-down select 48h/49h | default `FF` (pull-**up** when enabled) | used for the 12 `U23` spares |
| Interrupt mask 4Ah/4Bh | **default `FF` — ALL interrupts masked** | opposite of the TCA9535; a binding firmware contract |
| Interrupt status 4Ch/4Dh | read-only, **names the changed input** | the reason three devices cost no extra traffic |
| Input latch 44h/45h | default `00` | available if a short press is ever missed |
| Output drive strength 40h–43h | default `FF` | four steps, for EMI if ever needed |
| Output port config 4Fh | default `00` | push-pull; open-drain per bank available |
| I/O sink | **25 mA per pin for direct LED drive**; abs max **50 mA** continuous per I/O, **I_SS 200 mA**, **P_tot 200 mW** | worst RGB channel 2.17 mA = **11× margin**; package 5.2 mA = **38×** |
| V_OL | ≤ 0.25 V at I_OL = 2.5 mA, V_DD = 3 V (default drive) | the RGB corner analysis uses 0.02–0.10 V and worst-case V_OL only *reduces* LED current |
| P-port leakage | **I_IH / I_IL ≤ 1 µA** | ~0.05 mcd through the LED — invisible |
| reset | **internal power-on reset; no RESET pin** | pin 1 is `INT`, open-drain |

**It is not a behavioural drop-in and the design does not treat it as one.** The
pin-out is identical to the TCA9535 and no wire moved, but the PCAL9535A powers
up with **every interrupt masked**, which is the exact opposite of the TCA9535.
Firmware that is not changed sees **no interrupts at all**. That is recorded as a
binding contract on the sheet, in the symbol note and in `ARCHITECTURE.md`.

**Addresses.** `U2` = **0x20**, `U3` = **0x21**, unchanged. No documentation shows
a conflict: the internal bus holds 0x20, 0x21, 0x36 (MAX17048), 0x38 (FT6236),
0x68 (BMI270), with 0x50 reserved by protocol for an accessory-ID EEPROM.

**Firmware ordering trap, recorded on the sheet.** Write the **Output port
register before the Configuration register**, or the five active-low resets and
`AMP_SD_MODE` glitch to their inactive state on the write that makes them
outputs.

---

## 3. The pin budget — why two expanders are not enough

This is the load-bearing finding of the task, so the arithmetic is given in full.

**Capacity: 2 × 16 = 32 pins.**

**Committed demand: 35 signals.**

| group | count | authority |
|---|---:|---|
| safe-state control outputs — `TOUCH_RST_N`, `SX1262_RST_N`, `NFC_5V_EN`, `AMP_SD_MODE`, `DISP_RST_N` | 5 | inherited, all five carry an external pull |
| user buttons — UP, DOWN, LEFT, RIGHT, A, B | 6 | product lock |
| `TOUCH_INT_N` | 1 | FBV2-S1-003 |
| `SX1262_DIO1` | 1 | D-089 / D-108 |
| `SD_CARD_DETECT_N` | 1 | **D-117 — "its destination is an internal PCAL9535A input on sheet 08"** |
| `BQ25185_STAT1`, `BQ25185_STAT2` | 2 | **Ruling G — "preserve both"** |
| `XGPIO0-9` | 10 | **D-082 — locked at ten** |
| `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_DETECT_N`, `ACC_POWER_FAULT_N` | 4 | D-089 / D-094 |
| `SX1262_RXEN` | 1 | expander-controlled by requirement |
| `ACC_PWR_EN` | 1 | inherited; see §3.2 |
| `RESERVED_SPARE` | 1 | **D-094 — "Rev 1 must retain at least one expander resource for recovery"** |
| **front RGB** | 3 | this brief |
| **total** | **35** | |

**35 against 32.** Nothing in that list is optional, and every line is held down
by a lock that predates this task or by the brief itself.

### 3.1 Every escape route was checked and closed

- **Native GPIO.** There are none. `GPIO_LEDGER.md` measures 33 of 33 usable pins
  assigned, zero free; GPIO35/36/37 are the octal PSRAM on the N16R8 module and
  Espressif marks them unavailable. B-10 stands.
- **A WS2812/SK6812 smart LED** — the escape the brief itself names — is
  therefore **impossible**, not merely unwanted: it needs RMT on a native pin, and
  `ARCHITECTURE.md` already records that expander GPIO "cannot do UART, SPI, PWM,
  RMT/IR, 1-Wire or WS2812" at roughly 70 µs per output change.
- **Consuming `RESERVED_SPARE`** is forbidden by D-094 and by the brief's own
  checklist.
- **Dropping an XGPIO** is forbidden by D-082, which already surrendered the
  eleventh XGPIO to pay for the fifth accessory-control pin.
- **Dropping a button, a reset or a rail enable** is not a trade anyone would
  take for an indicator.
- **`MAX17048_ALRT_N` and `VBUS_PRESENT`** were already displaced — see §3.3 —
  and freeing them would have yielded 2 pins, not 3.
- **A dedicated I²C LED driver** would add a new part family, a new footprint and
  a new driver for one indicator, and the brief rules it out unless unavoidable.

### 3.2 `ACC_PWR_EN` is kept, deliberately

`ACC_PWR_EN` (`U3` P17) is inherited from Beta-DM. It drives only `U15` and `U16`
— both **DNP** — and O-4 (open, sheet 09) may retire it when the external-I²C
buffer is re-decided. **It was not retired here** because removing it would leave
two sheet-09 input pins undriven, and sheet 09 is explicitly out of scope. It is
recorded on the sheet as the pin that sheet 09 is expected to free.

### 3.3 D-089 is amended, not broken

D-089 read `U2` = 16/16 as five freed pins consumed by `BQ25185_STAT1/2`,
`MAX17048_ALRT_N`, `VBUS_PRESENT` and `SX1262_DIO1`. Two signals arrived *after*
that lock — `TOUCH_INT_N` (FBV2-S1-003) and `SD_CARD_DETECT_N` (D-117) — and both
outrank telemetry on a shipping product: one is the touchscreen, the other is
card presence.

**`MAX17048_ALRT_N` and `VBUS_PRESENT` therefore remain test-point only.** The
fuel gauge is polled over I²C regardless, and VBUS presence is inferable from the
charger STAT pair. Twelve `U23` pins are free if that is ever revisited, which
makes it a firmware-and-a-wire change rather than a respin.

---

## 4. `U23` — the third PCAL9535A (NEW DECISION)

**`U23` = NXP `PCAL9535APW,118` at I²C `0x22`** (A2 = 0, A1 = 1, A0 = 0).

It exists because the allocation ran out, **not** because an LED wanted a driver.

**Why this and not something else:**

| property | consequence |
|---|---|
| same MPN as `U2`/`U3` | **no new part number** to source, stock, validate or rework |
| same TSSOP-24 footprint | **no new land pattern** to audit |
| same register map | **no new firmware driver** |
| runs from `+3V3` | **no new rail**, 25 µA static |
| 16 I/O for 4 used | **B-37 is retired permanently** — 12 spare I/O where the programme has carried "zero spare" since the first audit |

**It carries the RGB and the reserved spare, and nothing else.** That is
deliberate and it is how the brief's rule *"preserve core/community/safety
functionality before RGB when assigning pins"* is satisfied **by construction**:
delete `U23`, `D13` and `R124`–`R126` and the product loses its status light and
**not one other function**. Had the RGB stayed on `U2` and the charger telemetry
moved to `U23`, deleting the new part would have cost charge state and card
detect — exactly backwards.

**It holds no interrupt source.** Every interrupt-capable input in the design
stays on `U2` or `U3`, so `U23` keeps the `FF` power-up mask and is **never read
in the interrupt path**. Adding the third device costs **zero extra I²C traffic
per event**. Its `/INT` is still wire-OR'd onto `WAKE_INT_N` so the reserved spare
can become an interrupting input by firmware alone.

**Bus loading.** The internal I²C now carries six devices. The PCAL9535A adds
C_i ≤ 6 pF per line, so the measured ≈ 85 pF becomes roughly **95 pF** and the
rise time with `R19`/`R20` = 2.2 kΩ goes from **158 ns to about 177 ns** against
the 300 ns fast-mode limit — still 41 % of budget in hand. `0x22` is free.

**The cost, stated plainly:** one TSSOP-24 (≈ 7.8 × 4.4 mm), one 0603 100 nF
(`C83`), about $0.55, and a placement obligation on a board whose enclosure fit
is already flagged. **This is a new decision and it is flagged for CTO
ratification (§11).** If it is declined, the RGB feature is what falls, and
nothing else has to move.

---

## 5. The front RGB status light

### 5.1 Part

**`D13` = MEIHUA `MHPA3528RGBCT`, LCSC `C409779`** — verified live in this
session: **in stock, 69 270 pcs, ships immediately**, $0.1697 @ 5 / $0.1035 @ 500,
manufacturer MEIHUA, package **SMD3528-4P**, **common anode**. That satisfies
D-096, the standing rule that an MPN must be confirmed against a live record.

- Body **3.50 × 2.80 × 1.85 mm**, PLCC-4, top view, **water-clear lens, 120°**.
- **Pin 1 = common anode, 2 = BLUE cathode, 3 = GREEN cathode, 4 = RED cathode.**
  This is **not** the order used by `Device:LED_ARGB` (2 = red, 4 = blue), which
  would have swapped red and blue; a dedicated symbol and footprint were built
  from the manufacturer drawing, Issue **LPDS-0001719 Rev.2, 2018-09-25**.
- Footprint `AQROOT_Beta:MEIHUA_MHPA3528RGBCT_PLCC4_3.5x2.8mm`: four
  1.20 × 0.95 mm pads, 2.00 mm between the left and right columns, 0.40 mm
  between rows, pad centres ±1.60 mm in X and ±0.675 mm in Y.
- V_F at 20 mA: R 1.7–2.3 V, G 2.7–3.3 V, B 2.7–3.4 V. I_F continuous R 50 mA,
  G/B 30 mA. I_v at 20 mA: R 715–1420, G 1120–2250, B 285–715 mcd.
- **ESD: red is 2000 V HBM but green and blue are only 150 V.** `D13` must be
  handled as an ESD-sensitive part in assembly. This is recorded in the symbol,
  the footprint description and the sheet note.

### 5.2 Topology and resistors

**One common-anode RGB LED, anode to `+3V3`, three resistors, three PCAL9535A
sink outputs.** No transistors, no driver IC, no new rail.

The three resistors are **calculated separately from the low-current Fig. 4
forward-voltage curves** — the tabulated V_F is quoted at 20 mA and is useless at
1–2 mA — and they are deliberately unequal, because the die efficiencies are
unequal:

| channel | net | resistor | V_F used | nominal | high corner | low corner |
|---|---|---|---|---:|---:|---:|
| RED | `FRONT_RGB_R_N` | **`R124` 1 kΩ** | 1.75 V | **1.50 mA** | 1.70 mA | 1.18 mA |
| GREEN | `FRONT_RGB_G_N` | **`R125` 680 Ω** | 2.55 V | **1.03 mA** | 1.32 mA | 0.57 mA |
| BLUE | `FRONT_RGB_B_N` | **`R126` 390 Ω** | 2.60 V | **1.67 mA** | 2.17 mA | 0.86 mA |
| **white (all three)** | | | | **4.20 mA** | 5.18 mA | 2.60 mA |

Corners are the 3.234 / 3.366 V rail, the datasheet V_F spread and V_OL
0.02–0.10 V. Every channel lands inside the **1–2 mA** target and white lands
inside the **3–6 mA** target.

**Red gets the least current because it is by far the most efficient** — 1070 mcd
typ at 20 mA against 1685 for green and 500 for blue — which puts the delivered
output at roughly **80 / 87 / 42 mcd**, close enough to neutral behind a diffuser
that firmware can trim the rest with blink duty.

**Colours:** red, green, blue, cyan, magenta, yellow, white, off — all eight from
three independent sinks. **Blink is firmware-timed** over I²C; no smooth-animation
hardware is required or provided (an expander output change is ~70 µs at 400 kHz,
which is instantaneous relative to any blink a human perceives).

### 5.3 Default-OFF verdict — **PASS, by construction, with no added parts**

The question the brief asks is whether the light is dark before firmware runs. It
is, and it needs no external pull-up to be:

1. **Power-up:** Configuration 06h = `FF`, so `P00`–`P02` are **high-impedance
   inputs**. The LED's cathode path is open. The only current is the **I_IH/I_IL
   ≤ 1 µA** leakage limit — about **0.05 mcd**, which is invisible.
2. **Internal pulls are OFF:** 46h/47h = `00` at reset, so the on-die 100 kΩ
   cannot light anything either.
3. **The input→output transition cannot glitch:** Output port 02h = `FF`, so the
   pin **drives HIGH the instant it becomes an output** — the same potential as
   the anode, hence zero forward voltage.

**An external pull-up on each cathode would be three parts that do nothing.**
None is fitted.

### 5.4 Mechanical requirement (placement, not electrical)

- **Front-facing is a requirement. The exact front position is deliberately NOT
  locked** — upper bezel, lower bezel, beside the display or near the controls
  are all acceptable.
- **It is not a top-edge part.** The top crown is the IR aperture.
- **It must sit behind a diffuser or light pipe. No protruding bare LED.**
- Placement and CAD own the final position; this task fixes the electrical
  design and the part only.

---

## 6. Buttons

**Six buttons: UP, DOWN, LEFT, RIGHT, A/SELECT, B/BACK.** HOME is removed —
`SW8` and `R10` deleted, no `BTN_HOME_N` net exists. Volume Up/Down were never
electrical and are not invented. Power stays the `SW9` SPDT hard switch on the
TPS63020 enable, deliberately not a GPIO. BOOT stays `SW1` on GPIO0, electrically
unchanged, mechanically recessed.

**MPN verified against the Littelfuse/C&K PTS645 datasheet in this session.**
`PTS645SM43SMTR92LFS` is a real orderable line: **1.6 N ± 0.3 actuation** (≈163 gf,
against the ~160 gf selection target), **100 000 operations**, **0.30 +0.1/−0.15 mm
electrical travel**, 7.0 mm height, straight, round actuator, silver contacts,
gull-wing SMD. Footprint `Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92`.

- **Contact arrangement SPST, N.O., momentary** — correct for pull-up + switch to
  ground.
- **Polarity: active LOW.** 10 kΩ external pull-up to `+3V3` (`R4`–`R9`), switch
  to GND. Steady current with a button held: **0.33 mA**.
- **Why the pull-ups stay external** even though the PCAL9535A has internal
  100 kΩ ones: 100 kΩ against 1 µA of input leakage and PCB contamination is a
  weak high, and an external 10 kΩ is defined **before firmware has written a
  single register**.
- **Wetting current check (new here):** the datasheet's minimum contact rating is
  **10 µA at 1 VDC**; 0.33 mA at 3.3 V is 33× above it, so the silver contacts are
  wetted.
- **No RC debounce.** Debounce is firmware. The input is read over I²C after an
  interrupt — hundreds of microseconds of latency already — so a capacitor would
  add parts and solve nothing. The PCAL input latch (44h/45h) is available if a
  short press is ever missed.
- **B-67 (new, minor):** Littelfuse publishes **no bounce-time figure** for the
  PTS645. The earlier "≤ 5 ms" claim is not datasheet-backed. Firmware should use
  a conventional 10–20 ms debounce window; measure on the first boards.
- **Interrupt behaviour:** all six are on `U2` Port 1, interrupt-capable, masked
  at power-up by hardware default, unmasked explicitly by firmware.

---

## 7. Charger status — `BQ25185_STAT1` / `STAT2`

Both are landed, per **Ruling G**, on `U2` P05 and P06 with **10 kΩ pull-ups to
`+3V3`** (`R127`, `R128`).

**Why 10 kΩ and not the 20 kΩ Ruling G suggested.** SLUSF65A Table 5-1 gives the
permitted range as **1 kΩ – 20 kΩ** with a maximum pull-up rail of 5 V and 20 mA
sink; both values are legal. 10 kΩ is chosen for the same reason the button
pull-ups are 10 kΩ: it is a stiffer high against 1 µA of expander leakage and
against contamination, it reuses a value already dominant on the sheet, and the
0.33 mA only flows while the charger is actually holding the pin LOW.

**Charger-state interpretation (SLUSF65A Table 7-2), recorded for firmware:**

| STAT1 | STAT2 | meaning |
|---|---|---|
| LOW | — | **charging** |
| HIGH | LOW | **fault** |
| HIGH | HIGH | **one combined state**: charge complete, sleep, or charge disabled |

**STAT1 alone conveys only fault/no-fault**, which is why the earlier STAT1-only
recommendation was reversed.

**The no-battery behaviour is handled in the mask, not in copper.** SLUSF65A
§7.3.10 verbatim: *"When no battery is present, the device charges the capacitor
on the BAT pin and toggles between charging and charge completed states. During
this condition, the STAT1 pin remains stable, while the STAT2 pin toggles."*
`STAT2` therefore sits on an interrupt-capable input whose mask bit is **SET by
hardware default** — the PCAL9535A powers up with 4Ah/4Bh = `FF` — and firmware
must **leave it masked and poll**. That is precisely the capability the TCA9535
lacked and the reason D-061's family change is load-bearing rather than cosmetic.

**No separate charging LEDs are added.** The front RGB may display charge state
in firmware.

---

## 8. Transitional endpoints

| net | lands on | polarity | pull | safe state |
|---|---|---|---|---|
| `TOUCH_INT_N` | `U2` P16 | **active LOW**, FT6236 panel pin 46 | panel-side | input, interrupt-capable |
| `SD_CARD_DETECT_N` | `U2` P07 | **LOW = card present** (push-push convention, **assumed — B-46**) | `R113` 100 kΩ to `+3V3` on sheet 03 | HIGH = no card |
| `SX1262_DIO1` | `U2` P17 | active HIGH | none needed | input |
| `SX1262_BUSY` | **GPIO8, native** — unchanged | — | — | direct to the MCU, as required |
| `SX1262_RXEN` | `U3` P16 | **active HIGH** | **`R74` pull-down** | **RX path OFF through reset and any crash** — correct |

`SD_CARD_DETECT_N` polarity remains an assumption because the Molex drawing would
not load (B-46). The exposure is nil: it is a firmware constant on an expander
input, never a board change. No `*_TBD` net remains anywhere in the design.

---

## 9. Interrupt architecture

**All three `/INT` pins are open-drain and wire-OR onto `WAKE_INT_N`**, which
`R3` 10 kΩ pulls to `+3V3` and which reaches **GPIO21**.

- **The pull-up is mandatory** (datasheet) and it is what makes the line
  deterministic — inactive HIGH — before any register is written. **No floating
  interrupt.**
- **No extra native GPIO is consumed.** One pin serves three devices; GPIO21 is
  not a strapping pin, so a held interrupt cannot block ROM download.
- **Efficient changed-input discovery.** On a wake, read `4Ch/4Dh` on `U2`, then
  on `U3`. The status registers name the changed bit directly instead of forcing a
  read of every port register on every device — a capability the TCA9535 does not
  have. **`U23` is never read in the interrupt path** because it holds no
  interrupt source, so the third device costs nothing per event.
- **Initialisation contract.** `INT` clears on a read of the **input port**
  register, so firmware must read `00h/01h` after the status register or the line
  stays LOW and no further edge appears.
- **Mask policy.** Unmasked: the six buttons, `TOUCH_INT_N`, `SX1262_DIO1`,
  `SD_CARD_DETECT_N` on `U2`; `ACC_DETECT_N` and `ACC_POWER_FAULT_N` on `U3`.
  Masked: `BQ25185_STAT2` (§7) and **all ten XGPIO — this is MX-9**, so an
  accessory cannot hold the shared wake line and starve the buttons.
- **Input latch** 44h/45h available; not enabled by default.

---

## 10. The definitive `U2` / `U3` / `U23` ledger

Read from a `kicad-cli` netlist export of the working tree, not transcribed.
`safe state` is the level the net sits at from power-on until firmware writes a
register.

### `U2` — internal control and user input, **0x20**, 16/16, zero spare
Port 0 config `06h = E0h` (P00–P04 out, P05–P07 in); Port 1 config `07h = FFh`.

| pin | net | dir | polarity | external pull | power-up safe state | IRQ | community |
|---|---|---|---|---|---|---|---|
| P00 | `TOUCH_RST_N` | out | active LOW | `R12` 100 k **down** | reset **asserted** | n/a | no |
| P01 | `SX1262_RST_N` | out | active LOW | `R13` 100 k **down** | reset **asserted** | n/a | no |
| P02 | `NFC_5V_EN` | out | active HIGH | `R14` 100 k **down** | boost **off** | n/a | no |
| P03 | `AMP_SD_MODE` | out | active HIGH | `R15` 100 k **down** | amp **shut down**, 0.6 µA, speaker muted | n/a | no |
| P04 | `DISP_RST_N` | out | active LOW | `R16` 100 k **down** | reset **asserted** | n/a | no |
| P05 | `BQ25185_STAT1` | in | active LOW = charging | **`R127` 10 k up** | HIGH | yes, **unmasked** | no |
| P06 | `BQ25185_STAT2` | in | LOW with STAT1 high = fault | **`R128` 10 k up** | HIGH | yes, **MASKED** (toggles with no battery) | no |
| P07 | `SD_CARD_DETECT_N` | in | LOW = card present (B-46) | `R113` 100 k up, sheet 03 | HIGH = no card | yes, unmasked | no |
| P10 | `BTN_UP_N` | in | active LOW | `R4` 10 k up | HIGH | yes, unmasked | no |
| P11 | `BTN_DOWN_N` | in | active LOW | `R5` 10 k up | HIGH | yes, unmasked | no |
| P12 | `BTN_LEFT_N` | in | active LOW | `R6` 10 k up | HIGH | yes, unmasked | no |
| P13 | `BTN_RIGHT_N` | in | active LOW | `R7` 10 k up | HIGH | yes, unmasked | no |
| P14 | `BTN_A_N` | in | active LOW | `R8` 10 k up | HIGH | yes, unmasked | no |
| P15 | `BTN_B_N` | in | active LOW | `R9` 10 k up | HIGH | yes, unmasked | no |
| P16 | `TOUCH_INT_N` | in | active LOW | panel side | HIGH | yes, unmasked | no |
| P17 | `SX1262_DIO1` | in | active HIGH | none | LOW | yes, unmasked | no |

### `U3` — community and accessory, **0x21**, 16/16, zero spare

| pin | net | dir | polarity | external pull | power-up safe state | IRQ | community |
|---|---|---|---|---|---|---|---|
| P00 | `XGPIO0` | XGPIO | n/a | 100 Ω series at the connector (sheet 09) | high-Z input | **masked (MX-9)** | **YES** |
| P01 | `XGPIO1` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P02 | `XGPIO2` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P03 | `XGPIO3` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P04 | `XGPIO4` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P05 | `XGPIO5` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P06 | `XGPIO6` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P07 | `XGPIO7` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P10 | `XGPIO8` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P11 | `XGPIO9` | XGPIO | n/a | as above | high-Z input | masked | **YES** |
| P12 | `ACC_3V3_EN` | out | active HIGH | `R98` 100 k **down**, sheet 01 | **rail OFF** | n/a | no (control) |
| P13 | `ACC_5V_EN` | out | active HIGH | `R102` 100 k **down**, sheet 01 | **rail OFF** (drives boost `EN` **and** switch `ON`) | n/a | no (control) |
| P14 | `ACC_DETECT_N` | in | LOW = accessory present | **`R129` 100 k up, on this sheet** | HIGH = absent | yes, unmasked | status |
| P15 | `ACC_POWER_FAULT_N` | in | active LOW, wire-OR of both `FLT` | `R103` 100 k up, sheet 01 | HIGH = no fault | yes, unmasked | status |
| P16 | `SX1262_RXEN` | out | active HIGH | `R74` **down**, sheet 04 | **RX off** | n/a | no |
| P17 | `ACC_PWR_EN` | out | active HIGH | `R17` 100 k **down** | off; drives DNP `U15`/`U16` only — sheet-09 retirement candidate (O-4) | n/a | no |

### `U23` — status light and reserve, **0x22**, 4/16, **12 spare**

| pin | net | dir | polarity | external pull | power-up safe state | IRQ | community |
|---|---|---|---|---|---|---|---|
| P00 | `FRONT_RGB_R_N` | out (sink) | LOW = lit | none needed | **high-Z → LED OFF** | masked | no |
| P01 | `FRONT_RGB_G_N` | out (sink) | LOW = lit | none needed | **high-Z → LED OFF** | masked | no |
| P02 | `FRONT_RGB_B_N` | out (sink) | LOW = lit | none needed | **high-Z → LED OFF** | masked | no |
| P03 | `RESERVED_SPARE` | reserve | n/a | **`R130` 100 k up + `TP41`** | HIGH, defined | masked | no |
| P04–P07, P10–P17 | — | spare | n/a | on-die 100 kΩ, firmware-enabled | high-Z input | masked | no |

**Firmware contract for the 12 spares:** enable the internal pulls (46h/47h) or
drive them as outputs. Floating CMOS inputs burn crowbar current. This is a
firmware change, not a board change — the PCAL carries the resistors on die.

### Community architecture, preserved exactly

10 XGPIO · 2 native (**GPIO38 `NATIVE_A`, GPIO47 `NATIVE_B`** — untouched here) ·
2 external I²C · 1 WAKE/ATTN · 2 `ACC_3V3_SW` · 2 `ACC_5V_SW` · 4 GND ·
1 `ACC_DETECT_N` = **24 contacts.** Sheet 09 is **not** implemented in this task;
only the sheet-08 control and status endpoints are in scope.

**`ACC_DETECT_N` is a sheet-08-local net for now.** Its 100 kΩ pull-up (`R129`) is
placed at the expander so the input has a defined level before the connector sheet
exists. **Sheet 09 promotes the label and adds the connector contact — and must
NOT add a second pull-up.**

---

## 11. Opportunity and simplification scan

Everything below was considered; only one item requires a decision.

**Requires a CTO/user decision — ONE item:**

> **O-6 — `U23`, a third `PCAL9535APW,118` at `0x22`, is added to the design.**
> The committed pin demand is 35 and two expanders are 32. Every alternative is
> closed: no native GPIO exists (so the brief's own WS2812 escape is impossible),
> `RESERVED_SPARE` is mandated by D-094, the ten XGPIO are locked by D-082, and a
> dedicated LED driver is a new part family for one indicator. `U23` adds **no new
> MPN, no new footprint, no new driver and no new rail**, costs ≈ $0.55 plus one
> 0603, and retires **B-37** by leaving 12 spare I/O. It carries the RGB and the
> reserved spare only, so **declining it costs the status light and nothing else.**
> The one real cost is board area on a design whose enclosure fit is already
> flagged (`aqroot-pcb-does-not-fit-enclosure`). **Ratify or decline.**

**Recorded, no decision needed:**

- **B-37 is retired** if O-6 is ratified: 12 spare expander I/O, first slack the
  programme has ever had.
- **`ACC_PWR_EN` is a free pin waiting for O-4.** If sheet 09 retires the
  TCA9517A enable, `U3` gains a spare.
- **`MAX17048_ALRT_N` and `VBUS_PRESENT` now have a home** — two of the `U23`
  spares — whenever the CTO wants telemetry rather than test points.
- **Simplification taken:** no external pull-ups on the RGB cathodes (three parts
  that would do nothing), no RC debounce on six buttons (six parts), no
  transistors on the LED, no separate charging LEDs.
- **Simplification declined:** merging `ACC_PWR_EN` into `ACC_3V3_EN` would free a
  pin but is a sheet-09 decision entangled with O-4.
- **Hygiene noted, not actioned:** `aqroot-Beta-v2.kicad_pro` still carries six
  stale `erc_exclusion_comments` referring to the retired `RGB_*_CTL` architecture
  and to `SD_CARD_DETECT` being unallocated. They suppress nothing now. Removing
  them strengthens ERC; it is a separate hygiene task.
- **Repaired in passing:** six root-sheet UUIDs written with the invalid prefix
  `fb080r00-` ("r" is not hex). KiCad silently reassigns invalid UUIDs on save.

---

## 12. Verification

| check | result |
|---|---|
| **ERC** (`--units mm`, errors + warnings, **not** `--severity-all`) | **42 messages, 1 error, 41 warnings** |
| ERC delta vs the recovered working tree | **ZERO** — identical violation set, line for line |
| ERC delta vs the pre-sheet-08 baseline 45 / 2 / 43 | **−3 messages, −1 error, −2 warnings** |
| new errors introduced | **0** |
| components | **319**, 0 duplicate references, **0 without a footprint** |
| nets | 235, **0 `*_TBD`** |
| `TCA9535PWR` in living hardware | **none** — symbol and cache entry both gone |
| `BTN_HOME_N` / HOME electrical path | **none** |
| `RGB_R/G/B_CTL` historical architecture | **not restored anywhere** |
| `fork_equivalence.py` | **PASS** — sheet 08 moved from `norm` to `changed`, RGB footprint declared |
| `netclass_probe.py` | **PASS** — 176 board nets, 6 resolve to `LED_BOOST`, IR nets still excluded |
| PCB | **bit-identical to Beta-DM**, proven by the fork probe |
| sheet 09 | **untouched** |
| `hardware/beta-dm/`, `hardware/beta/`, `hardware/beta/mechanical/` | **untouched** |

The remaining error is the inherited sheet-09 `RESERVED_NC` dangling label, which
predates this task and closes at sheet-09 migration.

**Files changed:** `07_ir.kicad_sch`, `08_buttons_expanders.kicad_sch`,
`01_power_tree.kicad_sch` (five local labels promoted to hierarchical — nothing
else), `03_spi_a_display_sd.kicad_sch` (one label promoted), the root sheet
(13 sheet pins, stub wires and labels), `libraries/AQROOT_Beta.kicad_sym`, one new
footprint, `checks/fork_equivalence.py`.

Sheets 01 and 03 were touched **only** to publish nets that the brief explicitly
requires landing on the expanders. No component, value, net topology or DNP state
on either sheet was altered.

---

## 13. Open items carried forward

| # | item |
|---|---|
| **O-6** | ratify or decline `U23` (§11) |
| **O-4** | TCA4307-class hot-swap buffer for the external I²C — sheet 09 |
| **B-46** | `SD_CARD_DETECT_N` polarity assumed, Molex drawing would not load |
| **B-67** | **new** — no published bounce time for the PTS645; use 10–20 ms in firmware and measure |
| **B-37** | retired by `U23` if O-6 is ratified |
| — | `MAX17048_ALRT_N` and `VBUS_PRESENT` remain test-point only |
| — | front RGB position deferred to placement/CAD; diffuser or light pipe mandatory |
| — | `U23` adds a TSSOP-24 to a board whose enclosure fit is unverified |

**Sheet 09 was not started.**
