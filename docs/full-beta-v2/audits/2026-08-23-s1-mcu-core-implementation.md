# FBV2-S1-002 — power-tree ruling closure and Full Beta v2 MCU-core migration

**Task:** FBV2-S1-002.
**Date:** 2026-08-23.
**Repository HEAD at task start:** `8650d5a` (*docs: record the Full Beta v2 power-tree
migration*, FBV2-S1-001).
**Scope:** `hardware/beta-v2/` — the two ruled power-tree values, and sheet `02_MCU_CORE`.
Sheets `03`–`09` were **not** modified. The PCB was **not** touched.
`hardware/beta-dm/`, `hardware/beta/` and `hardware/beta/mechanical/` were **not** touched.

Companion: [`../architecture/GPIO_LEDGER.md`](../architecture/GPIO_LEDGER.md) carries the
measured pin ledger and the full strap audit. This file records the reasoning and the deltas.

---

## 0. Result

| gate | verdict |
|---|---|
| **FBV2-S1-MCU-CORE** (task gate) | **PASS** |
| **FBV2-S1** (programme gate) | **STILL OPEN — 2 of 9 sheets** |

**ERC: 5 errors (Beta-DM baseline) → 4 errors. Zero new errors. `02_MCU_CORE` reports
nothing at all.** Warnings rose 55 → 63; all eight additions are `isolated_pin_label`
warnings on the **root** sheet, every one a named transitional artifact of a cross-sheet
signal whose far end is a sheet that has not been migrated yet. See §6.

---

## 1. P-20 CLOSED — `R95` = 560 Ω

**Ruling:** lock the first-build target at **560 Ω**. Implemented: `R95` 680 R → **560 R
1% 1206**.

### Recomputed from the captured circuit

The path is `USB_VBUS_CHG` → `Q5` (AO3401A, R_DS(on) ≈ 60 mΩ) → `R95` → `D12` (BAT54WS) →
`BAT_RAW`. `Q5`'s drop at these currents is under 1 mV and is ignored below.

```
I = (V_BUS − V_f(D12) − V_BAT) / R95
```

| case | V_BUS | V_BAT | V_f | **I** |
|---|---|---|---|---|
| **nominal, fully dead pack** | 5.00 V | 0 V | 0.32 V | **8.36 mA** |
| USB low | 4.75 V | 0 V | 0.31 V | 7.93 mA |
| USB high | 5.25 V | 0 V | 0.32 V | 8.80 mA |
| with `R95` ±1 % | — | — | — | ±0.09 mA |

**Recovery current = 8.4 mA nominal, 7.9–8.9 mA over the USB range.** That is inside the
accepted 5–10 mA band and restores the ≈ 8 mA the architecture assumed, which is what
**B-26** (pack-protector release current) is measured against.

### The consequence that must be recorded, not buried

**680 Ω was not an arbitrary value.** It is exactly the value that satisfies **B-27**'s
recorded single-fault ceiling:

```
(5.00 − 0.32 + 4.2) / 680 = 13.06 mA      <- B-27's "≈13 mA"
(5.00 − 0.32 + 4.2) / 560 = 15.86 mA      <- with the ruled value
worst case (5.25 V, 4.35 V cell)          = 16.6 mA
```

**B-27's "≈13 mA" figure is therefore superseded and is restated as ≈ 15.9 mA nominal,
≈ 16.6 mA worst case.** On a 2500 mAh pack that is **0.0066 C** — still a trickle, still
far below any damage threshold, still self-annunciating, and still bounded by `R95` and
made unidirectional by `D12`. The ceiling rose by 22 %; the conclusion does not change.

The trade is explicit: **P-20 buys ~21 % more dead-cell recovery current at the price of
~22 % more single-fault current.** The CTO ruled for recovery, and B-27 is amended in
place rather than left reading a number that is no longer true.

---

## 2. P-21 CLOSED — OV trip derived, not typed

**Ruling:** target ≈ 4.6 V, derived from the datasheet threshold with standard values.

### Datasheet threshold — primary source

Obtained this session from the LTC4368 datasheet (Farnell mirror, doc `2243878`),
ELECTRICAL CHARACTERISTICS:

| symbol | parameter | MIN | TYP | MAX | units |
|---|---|---|---|---|---|
| `V_OV` | OV Input Threshold Voltage, **OV Rising** | **492.5** | **500** | **507.5** | mV |
| `V_OVHYST` | OV Input Hysteresis | 20 | 25 | 32 | mV |
| `I_LEAK` | UV, OV Leakage Current | — | ±1 | **10** | nA |

The features page states **"Adjustable ±1.5% Undervoltage and Overvoltage Thresholds"**,
consistent with 492.5 / 500 / 507.5 mV.

### Divider

```
V_TRIP = V_OV x (R77 + R78) / R78
```

Required ratio for 4.6 V at the 500 mV typical: 9.2. **`R78` stays 442 k 1%** and
**`R77` becomes 3.65 M 1%** (E96):

```
(3.65 M + 442 k) / 442 k = 9.2579
V_TRIP = 0.500 x 9.2579 = 4.629 V
```

**`R77` 4.02 M → 3.65 M 1%.** `3.65 M` is already carried by `R91` in the recovery
reference divider, so **this adds no BOM line** — it removes one.

### Nominal and tolerance

| quantity | value |
|---|---|
| **Nominal trip** | **4.63 V** |
| Comparator + 1 % resistor tolerance | **4.48 – 4.78 V** |
| Including the 10 nA max OV-pin leakage across `R78` (±4.4 mV at the pin) | 4.44 – 4.82 V |
| Hysteresis at the battery | 25 mV × 9.2579 = **231 mV** typ (185–296 mV) |
| **Nominal release** | **4.40 V** |

### Why this is the right target

* **Above a 4.35 V-class pack** with 129 mV of margin even at the absolute worst-case-low
  trip of 4.479 V, and 279 mV above a conventional 4.2 V pack.
* **Materially below the 5.05 V first capture** — 420 mV lower, which is the point of the
  ruling.
* **No lockout hazard.** Release is 4.40 V nominal, above a 4.35 V float, so a pack that
  never exceeds its float voltage can never be held off by hysteresis.
* Divider current at 4.2 V falls from 0.94 µA to **1.03 µA** — irrelevant beside the
  LTC4368's own 80 µA operating current.

**Recorded limitation.** The OV-pin leakage contributes ±0.9 % because `R78` is 442 kΩ.
Halving the divider to 1.82 M / 221 k would give 4.618 V with half the leakage error, at
2 µA and two new BOM values. It is a **no-respin option on the same footprints** and is
recorded as such rather than taken, because BOM consolidation is a standing programme
value and the margin is adequate as built.

---

## 3. P-22 CLOSED — scripted KiCad edits are permitted, under conditions

The blanket Beta-DM rule *"do not generate or modify KiCad schematic or PCB files
automatically"* is **superseded**. The replacement is recorded as **D-107**, a standing
engineering-process rule with eight conditions, all of which must hold.

This task was executed under it and the evidence is in this file: the edits were
deterministic and narrowly scoped (§1, §2, §4), the scripts are in source control and the
diffs are reviewable, the project parses and exports, ERC was run and diffed against a
baseline, the preservation probes were run, and the output is reconciled against the CTO
task item by item in §8.

**The rule does not license scripts to bypass engineering review.** The two datasheet
facts this task could not retrieve are recorded as blockers in §7 rather than assumed.

---

## 4. Sheet 02 — what changed

### 4.1 GPIO38 → `NATIVE_A`, GPIO47 → `NATIVE_B`

| pin | was | now |
|---|---|---|
| GPIO38 (`U1.31`) | `SX1262_DIO1` | **`NATIVE_A`**, hierarchical, bidirectional |
| GPIO47 (`U1.24`) | `DISP_BL_CTL` | **`NATIVE_B`**, hierarchical, bidirectional |

Both leave sheet `02` as the native community fast-IO signals required by D-084.
`SX1262_DIO1` **no longer reaches the MCU at all** — under D-089 it terminates on the
internal expander `U2`, which is sheet `08` and is not migrated. The root-sheet pin was
removed from the `02_MCU_CORE` symbol together with its stub and label.

### 4.2 GPIO46 → `DISP_BL_CTL`, with the strap protected

`DISP_BL_CTL` had to leave GPIO47. GPIO46 is the only pin left and it is a **strapping
pin that must read LOW at reset or Joint Download Boot becomes unreachable** — GPIO0 = 0
alone does not select download mode; GPIO46 = 0 is also required.

```
U1.16 (GPIO46) ──┬── DISP_BL_CTL_STRAP ── R109 0R FIT ── DISP_BL_CTL ── U17.4 CTRL
                 ├── R108 10k ── GND
                 └── TP2  (probe the strap directly)
```

* **`R108` 10 kΩ pull-down at the pin** — the value Espressif's hardware design guidelines
  call "a strong pull-down" against the chip's 45 kΩ internal pull.
* **`R109` 0 Ω FIT** isolates the TPS61169 `CTRL` input. If `CTRL` ever proves to source
  current, lifting one resistor guarantees the strap; the cost is a dark backlight, which
  is the safe direction. This is a D-049 no-respin escape.
* **No capacitance was added.** Espressif warns against bulk C on strapping pins, and the
  `DISP_BL_CTL` net carries no filter — it never did.
* **Quantified:** GPIO46 must sit below `V_IL` = 0.825 V. With `R108` = 10 kΩ, any
  internal pull-up on `CTRL` **≥ 30 kΩ** keeps it there; ±1 µA of `CTRL` leakage moves the
  node ±10 mV.

**Recovery consequence, recorded:** if GPIO46 were ever held high at reset, ROM-download
recovery over Joint Download Boot would be unreachable and the only remaining path would
be a working application image. That is precisely why the pull-down is dedicated,
strong, at the pin, isolatable, and measurable.

### 4.3 GPIO43 withdrawn from the community port

`FAST_IO_U0TXD_ROOTPROBE_CS` is removed from sheet `02`. GPIO43 is now the local net
`UART0_TXD_DBG`, with **`TP35`**.

The connector-side remnant (`R67` 100 Ω, `D7` TVS, `J5.23`) lives on sheet `09` and was
deliberately not touched; sheet `09` is being re-architected wholesale from the 20-pin
port to the 2×12 Samtec port anyway.

**GPIO44 (U0RXD) is IR RX, so UART0 is TX-only.** That is acceptable — and only
acceptable — because ROM download recovery runs over the native **USB Serial/JTAG** on
GPIO19/20, not over UART0. Recorded so that nobody later assumes a UART download path.

### 4.4 GPIO3 — B-09 closed

`R110` 10 kΩ pull-down added at the MCU pin. GPIO3 previously had **no pull at all**: only
`R18` 220 Ω in series to the BMI270 and `TP3`. It floated at reset.

**LOW is the required level.** When `EFUSE_STRAP_JTAG_SEL` is burned, GPIO3 = 0 selects
the USB Serial/JTAG source; GPIO3 = 1 selects external JTAG on MTMS/MTDI/MTCK/MTDO, which
on this board are **GPIO39–42, the I²S bus**. External JTAG is not merely unused here — it
is unusable, so the pin has exactly one correct level.

The BMI270 cannot overpower the strap **at reset**, because `INT1` is high-impedance until
firmware enables it. After boot, `INT1` must be **push-pull, active-high**
(`INT1_IO_CTRL`: `output_en` = 1, `od` = 0, `lvl` = 1) so its idle level agrees with the
pull-down; **open-drain is incompatible with a pull-down and must not be configured.**
Driving high, the BMI270 sources 323 µA and GPIO3 reaches 3.23 V against a 2.475 V `V_IH`.

### 4.5 GPIO45 — a no-respin provision, fitted DNP

GPIO45 selects VDD_SPI: **LOW = 3.3 V**, which is what the WROOM-1's flash and PSRAM
require. It carries only `TP1` — an **exposed test pad on a floating strap pin**, held
only by the chip's internal pull-down.

**`R111` 10 kΩ pull-down added, DNP.** No electrical change, no risk, and the option
exists on the board rather than requiring a respin. Whether to fit it is a CTO call and is
the one open item this task raises — see §9.

### 4.6 Bookkeeping

* `TEST_GPIO46` → `DISP_BL_CTL_STRAP`, `TEST_GPIO45` → `GPIO45_VDDSPI_STRAP` (D-100: net
  names describe nets). `TP1`/`TP2` value fields updated to match.
* Four on-sheet notes added recording the GPIO changes and the whole strap rationale, so
  the reasoning survives on the drawing and not only in this file.

---

## 5. PCAL9535A crossings and the expander interface

Sheet `02` presents `I2C_SDA_INT`, `I2C_SCL_INT` and `WAKE_INT_N` and **nothing else** to
the expanders. All three are generic:

* `WAKE_INT_N` is the wire-OR of both expander `INT` pins with `R3` 10 kΩ pull-up. Both
  TCA9535 and **PCAL9535A** present an open-drain active-low `INT`, so the MCU-side
  interface is unchanged by the family swap.
* The I²C pair is address- and family-agnostic at the MCU.

**No TCA-specific assumption exists anywhere on sheet `02`** — no register naming, no
address strap, no part-specific pull. Verified by inspection of every label and text
object on the sheet. The `TCA9535PWR` symbols themselves are on sheet `08` and were not
touched.

**`RESERVED_SPARE` was not consumed.** Nothing on sheet `02` reaches `U3` P16.

---

## 6. ERC and parity

| measurement | errors | warnings | total |
|---|---|---|---|
| Beta-DM baseline | 5 | 53 | 58 |
| Beta-v2 after FBV2-S1-001 | 4 | 51 | 55 |
| **Beta-v2 after this task** | **4** | 59 | **63** |

**Errors: zero new, and one fewer than Beta-DM.** The error-only reports were diffed
line by line; the only difference from the Beta-DM baseline remains the dangling
`BAT_PROTECTED_P` root label that FBV2-S1-001 removed.

**`02_MCU_CORE` reports zero violations of any kind.**

The eight new entries are all `isolated_pin_label`, which this project configures as a
**warning**, and all are attributed to the **root** sheet. Each is a cross-sheet signal
with one end drawn and the other end waiting on a sheet migration:

| # | label | side that exists | resolved by |
|---|---|---|---|
| 1–2 | `NATIVE_A`, `NATIVE_B` | sheet `02` (root pin + hier label) | **sheet `09`** migration |
| 3–4 | `NATIVE_A`, `NATIVE_B` | hierarchical labels inside sheet `02` | **sheet `09`** migration |
| 5–6 | `SX1262_DIO1` | sheet `04` only | **sheet `08`** migration (D-089 routes it to `U2`) |
| 7–8 | `FAST_IO_U0TXD_ROOTPROBE_CS` | sheet `09` only | **sheet `09`** migration (contact is withdrawn) |

**These were deliberately not cleared.** Each could be silenced by adding a test point to
the orphaned net, and that would be the same anti-pattern as adding a `PWR_FLAG` to
silence a driver error. A transitional warning that names its own resolution is better
than a part that exists only to quiet a check.

**Parity checks run:** netlist export succeeds; every `U1` pin resolves to exactly one net;
no net name appears twice on `U1`; **277 components, 0 duplicate references, 276 with
footprints** (`LS1`, the off-board speaker, is the one without and always has been);
`fork_equivalence.py` **PASS**; `netclass_probe.py` **PASS**.

---

## 7. Blockers opened

| # | blocker | status |
|---|---|---|
| **B-43** | **TPS61169 `CTRL` internal-pull specification not retrieved.** TI's datasheet PDF text layer would not extract this session. | **OPEN, low.** The design is safe for any internal pull-up ≥ 30 kΩ and `R109` provides an isolation escape, but the number must be confirmed at FBV2-S2 |
| **B-44** | **BMI270 `INT` pad drive current not retrieved.** Bosch's datasheet PDF text layer would not extract. 323 µA into `R110` + `R18` is modest but unconfirmed. | **OPEN, low.** Fallback is `R110` → 47 kΩ (70 µA), a value change with no board change |
| **B-45** | **`NATIVE_A` / `NATIVE_B` have no ESD or series protection yet.** D-090 requires 100 Ω series on both native pins plus a low-capacitance TVS array; both belong next to the connector. | **OPEN, high.** These are the only two contacts with a direct MCU path. Sheet `09` work |
| ~~**B-09**~~ | GPIO3 has no strap-defining pull | **CLOSED** by `R110` (§4.4) |

**B-27 amended in place** — the single-fault recovery ceiling is ≈ 15.9 mA nominal /
≈ 16.6 mA worst case, not ≈ 13 mA (§1).

---

## 8. Task reconciliation

| CTO item | outcome |
|---|---|
| 1 · P-20 / P-21 / P-22 | closed — §1, §2, §3 |
| 2 · sheet 02 migrated | done, ESP32-S3-WROOM-1-N16R8 architecture otherwise preserved |
| 3A · GPIO38 = `NATIVE_A` | done, leaves the sheet hierarchically |
| 3B · GPIO47 = `NATIVE_B` | done |
| 3C · GPIO46 = `DISP_BL_CTL` | done, with dedicated pull-down, CTRL isolation link, no added capacitance, recovery consequence documented |
| 3D · GPIO43 off the community port | done — internal UART/debug only |
| 3E · `NFC_IRQ` not on GPIO46 | verified still GPIO18 |
| 4 · BOOT / recovery | audited. `SW1` retained and electrically real; recessed/hidden is a mechanical requirement, not an electrical one. No new user-facing button |
| 5 · GPIO3 strap | closed, B-09 retired |
| 6 · USB / JTAG / debug | **NO NEW DEBUG HARDWARE NEEDED.** One test pad added (`TP35`, UART0 TXD) because it is the only view of a board whose USB will not enumerate. `EN` pad considered and rejected |
| 7 · PCAL9535A crossings | verified generic; `RESERVED_SPARE` untouched |
| 8 · interrupt / wake | audited; LoRa deep-sleep wake stays out of scope; no interrupt on a boot-gating strap |
| 9 · safe-state / strap audit | [`../architecture/GPIO_LEDGER.md`](../architecture/GPIO_LEDGER.md) §3 |
| 10 · GPIO ledger | [`../architecture/GPIO_LEDGER.md`](../architecture/GPIO_LEDGER.md) §1; no duplicate assignments |
| 11 · ERC / parity | §6 |
| 12 · opportunity scan | §9 |

---

## 9. Opportunity and simplification scan

| lens | finding | action |
|---|---|---|
| **A · cheap useful capability** | `TP35` on UART0 TXD — the ROM boot log is the only diagnostic on a board whose USB does not enumerate | **implemented** (diagnostic, negligible risk) |
| **B · removable legacy complexity** | `FAST_IO_U0TXD_ROOTPROBE_CS` carried both a RootProbe chip-select role and a community fast-IO role on one debug-UART pin. Withdrawing GPIO43 removes that overload | **implemented** — it is a locked change (D-106) |
| **C · unnecessary test points** | none found. `TP1`/`TP2`/`TP3` each probe a distinct strapping pin; `TP4`/`TP5` the I²C bus. An `EN` pad was considered and **rejected** as duplicating USB-side reset | none |
| **D · missing recovery provisions** | GPIO45 is a **floating strap pin with an exposed test pad**. Nothing external defines VDD_SPI | **`R111` 10 kΩ pull-down placed DNP** — the option exists without changing the electrical design |
| **E · safe DNP / rework options** | `R109` 0 Ω FIT isolates the backlight from the GPIO46 strap; `R111` DNP defines VDD_SPI. Both are D-049-style no-respin escapes on parts already in the BOM | **implemented** |

### The one item requiring a CTO decision

> **Fit `R111`?** GPIO45 currently relies on the ESP32-S3's internal pull-down alone to
> hold VDD_SPI at 3.3 V, and an exposed test pad (`TP1`) sits on that net. The failure
> mode is not subtle: a GPIO45 that reads HIGH at reset selects VDD_SPI = 1.8 V and the
> 3.3 V flash and PSRAM do not boot. Espressif reference designs do leave GPIO45 NC, and
> the internal pull-down is documented — but this board exposes the net on a pad, and the
> datasheet's own default-configuration table could not be retrieved this session to
> confirm the internal pull.
>
> **Recommendation: FIT `R111`.** One 0603 resistor against a board that will not boot.
> It is placed DNP rather than fitted because changing the electrical design of a
> strapping pin is a CTO call, not a capture decision.

**No new product feature was added.** Everything implemented is either an already-locked
change, a purely diagnostic provision, or a DNP option.

---

## 10. What must happen next

1. **Do not start sheet `03`.**
2. Decide `R111` (§9).
3. Continue FBV2-S1. The two sheets that would clear the most transitional warnings and
   the most architecture debt are **`08`** (internal expander → PCAL9535A, `SX1262_DIO1`,
   the telemetry crossings that keep **B-15** open) and **`09`** (the 2×12 port, the
   native-pin protection that is **B-45**).
4. FBV2-S1 cannot pass until all nine sheets carry the v2 architecture.
5. The PCB stays untouched until FBV2-P1.

---

## Sources

* `hardware/beta-v2/reports/FBV2-S1-002-erc.rpt` — ERC after this task, 63 violations,
  4 errors.
* `hardware/beta-v2/reports/FBV2-S1-fork-equivalence.md` — regenerated provenance proof.
* LTC4368 datasheet, Farnell mirror doc `2243878` — OV threshold 492.5 / 500 / 507.5 mV,
  hysteresis 20 / 25 / 32 mV, UV/OV leakage 10 nA max, "Adjustable ±1.5 %".
* Espressif *ESP Hardware Design Guidelines — ESP32-S3 schematic checklist* — boot-mode
  table (SPI Boot = GPIO0 1 / GPIO46 any; Joint Download Boot = GPIO0 0 / GPIO46 0),
  strap setup ≥ 0 ms and hold ≥ 3 ms, "do not add high-value capacitors at GPIO0".
* Espressif *esptool — Boot Mode Selection, ESP32-S3* — "GPIO46 must also be either left
  unconnected/floating, or driven Low, in order to enter the serial bootloader"; 45 kΩ
  internal pull and the "10 k to GND" strong-pull recommendation.
* [`2026-08-23-s1-power-tree-implementation.md`](2026-08-23-s1-power-tree-implementation.md) — the P-20 / P-21 deviations this task closes.
* [`2026-08-22-dead-cell-and-single-fault-closeout.md`](2026-08-22-dead-cell-and-single-fault-closeout.md) — B-26, B-27, the recovery topology.
