# FBV2-S1-003 — Full Beta v2 display, touch, backlight and microSD migration

**Task:** FBV2-S1-003.
**Date:** 2026-08-23.
**Repository HEAD at task start:** `b24a4ab` (FBV2-S1-002).
**Scope:** `hardware/beta-v2/` — `R111` on sheet `02` per CTO ruling, and sheet
`03_SPI_A_DISPLAY_SD`. Sheets `04`–`09` were **not** modified. The PCB was **not** touched.
`hardware/beta-dm/`, `hardware/beta/` and `hardware/beta/mechanical/` were **not** touched.

---

## 0. Result

| gate | verdict |
|---|---|
| **FBV2-S1-DISPLAY-SD** (task gate) | **PASS** |
| **FBV2-S1** (programme gate) | **STILL OPEN — 3 of 9 sheets** |

**ERC: 4 errors → 4 errors. The error set is byte-identical to after FBV2-S1-002.**
Total violations 63 → 64: two `isolated_pin_label` warnings added for the new
`TOUCH_INT_N` crossing, one removed because `SD_CARD_DETECT_TBD` ceased to exist.

**The headline finding is in §2: the inherited `J1` symbol would have produced a dead
display on two independent counts.**

---

## 1. R111 fitted — GPIO45 closed

CTO ruling: `R111` **FIT, 10 kΩ, `GPIO45_VDDSPI_STRAP` → GND**.

Implemented: `(dnp yes)` → `(dnp no)`, value `10k DNP` → `10k`, and the sheet-02 strap note
rewritten to record that VDD_SPI is now held LOW **deterministically** rather than by the
chip's internal pull-down alone.

| requirement | state |
|---|---|
| Keep a test point on the GPIO45 strap | **`TP1` retained** on `GPIO45_VDDSPI_STRAP` |
| No capacitance on the strap net | **none** — the net is `U1.26` + `TP1` + `R111` only |
| Do not reuse GPIO45 for a peripheral | **not reused** — no peripheral touches it |
| Deterministic LOW reset state | **`R111` 10 kΩ to GND.** Against the chip's ~45 kΩ internal pull the node sits at ≤ 0.6 V even in the worst case, so VDD_SPI selects **3.3 V** for the WROOM-1's flash and PSRAM regardless of the internal pull's state |

**The pending `R111` decision is closed.**

---

## 2. The display symbol was wrong, and would have been dead on arrival

The inherited `J1` used the symbol `CH280QV10_CT_50P` — the **2.8-inch** panel's pin table —
while its Value and Footprint fields already said `FH69-50S-0.5SH`. Pin count and connector
matched, so nothing looked wrong. The pin **functions** did not match.

Comparing the archived `ER-TFT035IPS-6_Datasheet` Rev 2.0 §4.1 table against the old symbol:

| panel pin | old symbol (CH280QV10-CT) | **ER-TFT035IPS-6** | consequence if built |
|---|---|---|---|
| **1** | LEDK | **LEDA** | |
| **2** | LED-A1 | **LEDK** | |
| **3** | LED-A2 | **LEDK** | **backlight reverse-biased — no light** |
| 4, 5 | LED-A3, LED-A4 | **NC** | anodes driven into NC pins |
| 6 | IM0 (was tied GND) | **NC** | — |
| 7, 8, 9 | IM1, IM2, IM3 | **IM0, IM1, IM2** | by luck all three were already `+3V3`, giving the required `1 1 1` |
| **36** | WR_RS → `DISP_DC` | **WRX (SCL)** | |
| **37** | RS_SCL → `SPI_A_SCK` | **D/CX** | **serial clock and data/command swapped — the panel never receives a valid command** |
| 39 | TE (unused) | TE | — |
| 46 | CTP_IRQ (unused) | **CTP IRQ** | touch interrupt not represented at all |
| 47 | CTP_RES | CTP RST | — |

**Two independent dead-on-arrival faults**: the backlight anode and cathode reversed, and
the SPI clock and D/C lines swapped. Neither is visible from a pin count, a connector MPN or
an ERC run. This is exactly why the task forbade inferring pin numbers from the old part.

### Resolution

A new project-library symbol **`ER-TFT035IPS-6_50P`** was authored with the vendor's pin
table taken verbatim, deliberately keeping the **same pin geometry** as the old symbol so
that the migration is a pin-function change and not a redraw:

```
1 LEDA   2 LEDK   3 LEDK   4-6 NC   7 IM0   8 IM1   9 IM2   10 RESET
11 VSYNC 12 HSYNC 13 DOTCLK 14 DE   15-32 DB17..DB0
33 SDO   34 SDA   35 RD    36 WRX_SCL   37 DCX   38 CSX   39 TE
40 VDDI  41 VDDI  42 VCI   43 GND
44 CTP_SCL   45 CTP_SDA   46 CTP_IRQ   47 CTP_RST   48-50 GND
```

The `CH280QV10_CT_50P` symbol is **retained in the library** (Beta-DM still uses it) but is
removed from sheet `03`'s cached `lib_symbols`.

### Measured result

```
/SPI_A_SCK        J1.36[WRX_SCL]  J2.5[CLK]  U1.20[IO12]
/DISP_DC          J1.37[DCX]      U1.22[IO14]
/03_.../LED_A     J1.1[LEDA]      R70.2 R71.2 R72.2 R73.2
/03_.../LED_K     J1.2[LEDK]  J1.3[LEDK]  R69.1  U17.3[FB]
```

Panel pins 4, 5 and 6 carry explicit no-connect markers. `IM0/IM1/IM2` = `+3V3` = `1 1 1`
selects 4-wire 8-bit serial and consumes **no GPIO**. RGB-mode pins (11–14) and DB17–DB0 stay
grounded, `RD` stays at VDDI, `TE` stays open — all per the vendor's own tie-off guidance.

**The PO must name both parts explicitly: `ER-TFT035IPS-6` (display) and `ER-TPC035-6`
(touch). The vendor's CST340 touch variant is NOT authorised** — the FT6236 address, the
touch driver and the `TOUCH_RST_N` enumeration pulse are all locked around FT6236, and a
controller substitution is a new engineering review, not a purchasing choice.

---

## 3. `J1` footprint audit

Measured directly from `libraries/AQROOT_Beta.pretty/Hirose_FH69-50S-0.5SH.kicad_mod`:

| check | requirement (Hirose `FH69-50S-0.5SH`) | measured | verdict |
|---|---|---|---|
| Signal pad count | 50 | **50** | **PASS** |
| Pitch | 0.50 mm | **0.500 mm exactly, no drift across all 49 gaps** | **PASS** |
| Contact-area width (C) | 24.5 mm | **24.500 mm** end-to-end | **PASS** |
| Pad size | 0.300 × 1.230 mm | **0.300 × 1.230 mm** | **PASS** |
| Contact numbering | 1…50 monotonic along the row | **monotonic, 1 at one end, 50 at the other** | **PASS** |
| Mechanical hold-downs | present | **2 pads, 0.36 × 4.25 mm at x = ±14.365 mm** | **PASS** |
| FPC insertion direction | right-angle, horizontal entry | hold-downs and body sit to one side of the contact row, so the tail enters from the opposite side — **coherent and self-consistent** | **PASS** |
| Contact side | FH69 accepts **top and bottom**; the panel tail is **bottom** | part property, archived from the Hirose drawing | **PASS** |
| Latch orientation | back-flip ZIF, back-lock | part property, archived | **PASS** |
| 0.30 mm tail | connector 0.30 ± 0.05 mm; panel 0.30 ± 0.03 mm | the panel is the tighter tolerance | **PASS** |

**Verdict: PASS on every measurable pad-geometry parameter.**

### What this audit does NOT claim

* **The per-footprint pad-overlap assertion against the Hirose recommended-PCB-layout drawing
  was not run.** That is FBV2-S2 (**B-29**), and it applies to every project footprint.
* **The FH52E second source is NOT claimed as a drop-in, and the footprint was NOT moved to
  the FH52E/FH12 standard land pattern.** The FBV2-DISP-002 ruling proposed that migration on
  the strength of a Hirose note that FH69 *also* fits the FH52E pattern. That note proves one
  direction only, and the task requires manufacturer drawings proving **full footprint and
  mechanical equivalence** before drop-in is claimed. Those two drawings were not placed side
  by side this session. **`J1` therefore stays on the FH69-dedicated pattern with FH69 as the
  primary first-build part**, which is unambiguously correct for the part that is fitted.
  The FH52E / JLCPCB second-source question is re-opened as **B-47** for FBV2-S2.

---

## 4. Display SPI and the SDO isolation — **DNP**

SPI-A is unchanged and is **not** merged with SPI-B: `DISP_CS_N` GPIO10, `SPI_A_MOSI`
GPIO11, `SPI_A_SCK` GPIO12, `SPI_A_MISO` GPIO13, `DISP_DC` GPIO14, `DISP_RST_N` from the
internal expander. **No new native GPIO.** The ILI9488's 18-bit / 3-byte-per-pixel SPI write
behaviour is accepted and forces no architecture change.

### The ruling asked for a FIT/DNP recommendation. It is **DNP**.

```
J1.33 SDO ──┬── TP36 (probe)
            └── R112  0R  DNP  ── SPI_A_MISO ── J2.7 (microSD DAT0), U1.21
```

| evidence | weight |
|---|---|
| The vendor datasheet says of pin 33: *"Leave the pin open when not in use."* | direct instruction |
| The datasheet does **not** specify SDO's high-impedance behaviour while `CSX` is high | the risk is unquantified, not absent |
| ILI9488 modules have a field reputation for holding SDO driven | corroborating |
| **AQROOT never reads the display.** No register readback is used | the feature bought by fitting is unused |
| **SPI-A is shared with the microSD**, which is a core feature | the feature risked by fitting is essential |

**The risk is asymmetric.** Fitting `R112` puts a core feature (microSD) at risk of bus
contention to gain a feature nothing uses. Leaving it unfitted follows the vendor's own
instruction and costs only display readback. `TP36` still observes SDO on the panel side, so
the behaviour can be characterised on the first board without fitting anything.

**`R112` = 0 Ω, DNP by default.** Fit it only if register readback is ever required, and only
after SDO release has been observed on `TP36`. This closes **B-28** with the opposite default
to the one FBV2-DISP-002 sketched, and for a reason that document did not have: it wrote
*"fit a 0 R"* before weighing which of the two features is load-bearing.

**No series resistance was added to the `SPI_A_MISO` bus itself.** The microSD `DAT0` path is
direct, exactly as validated on Beta-DM.

---

## 5. Touch

| signal | panel pin | net | state |
|---|---|---|---|
| CTP SCL | 44 | `I2C_SCL_INT` | on the internal bus |
| CTP SDA | 45 | `I2C_SDA_INT` | on the internal bus |
| **CTP IRQ** | **46** | **`TOUCH_INT_N`** | **new** — was not represented at all |
| CTP RST | 47 | `TOUCH_RST_N` | expander `U2` P00, `R12` safe-state pull |
| CTP supply / GND | via VDDI / VCI / GND on the same tail | `+3V3` / `GND` | the CTP's own VDD is not a separate FPC pin (**B-30**, informational) |

* **FT6236 at 0x38 preserved.** No address change, no second controller.
* **Safe reset state preserved** — `TOUCH_RST_N` keeps its `R12` pull and its expander pin.
* **No second I²C pull-up pair was added.** The internal bus already carries the locked
  `R19`/`R20` 4.7 kΩ pair on sheet `05`; a panel-side pair would halve the effective pull-up
  and load the bus for nothing.
* **`RESERVED_SPARE` was not consumed.** `TOUCH_INT_N` leaves sheet `03` as a hierarchical
  signal and terminates on an internal **PCAL9535A** input when sheet `08` is migrated. Which
  expander pin it takes is a sheet-`08` decision; FBV2-DISP-002 recorded that touch is
  *polled* today, so the interrupt is an improvement, not a dependency.

---

## 6. Backlight — derived from the datasheet, not copied

The TPS61169 datasheet (**SNVSA40B**, Oct 2014, revised June 2024) was retrieved and its
ELECTRICAL CHARACTERISTICS extracted:

| symbol | parameter | MIN | TYP | MAX |
|---|---|---|---|---|
| `V_REF` | feedback regulation voltage, duty = 100 % | **188** | **204** | **220** mV |
| `I_LIM` | switching MOSFET current limit | **1.2** | 1.8 | 2.4 A |
| `V_OVP_SW` | output overvoltage threshold | 36 | 37.5 | 39 V |
| `f_SW` | switching frequency | 0.75 | 1.2 | 1.5 MHz |
| `R_DS(on)` | N-channel on-resistance | — | 0.35 | 0.7 Ω |
| `V_H` / `V_L` | CTRL logic high / low | 1.2 / 0.4 V | | |
| **`R_PD`** | **CTRL pin internal pull-down** | — | **300 kΩ** | — |
| `t_SD` | CTRL low time to shutdown | — | 2.5 | ms |
| — | VIN range | 2.7 | — | 5.5 V |

### `R69` (RSET)

`R69 = V_REF / I_LED`. **`R69` = 1.87 Ω ±1 %, 0603** — an **E96 standard value**, stocked and
procurement-friendly, so no substitution is needed.

| | I_LED | per LED (6 in parallel) |
|---|---|---|
| `V_REF` min 188 mV | **100.5 mA** | 16.8 mA |
| `V_REF` typ 204 mV | **109.1 mA** | **18.2 mA** |
| `V_REF` max 220 mV | **117.6 mA** | 19.6 mA |

**The panel's rating is 120 mA maximum with a 90 mA life point.** The worst-case corner is
**117.6 mA — 2.0 % below the maximum and never above it.** Per-LED current *falls* from
Beta-DM's 20 mA to 18.2 mA typical, so LED life improves. Normal brightness is set in
firmware by PWM on `CTRL`, with the default duty chosen near the 90 mA life point; `R69` =
2.26 Ω remains a one-resistor swap for a hard 90 mA ceiling. `R69` dissipation 26 mW in an
0603 — ample.

### Ballast `R70`–`R73`

Four footprints **retained and repurposed**: all four now sit in parallel on the single
`LED_A` node. **4 × 33 Ω = 8.25 Ω.**

| | value |
|---|---|
| Ballast drop at 109.1 mA | 0.900 V |
| `LED_BOOST` worst-low (Vf 2.9 V, 100.5 mA, `V_REF` 188 mV) | **3.917 V** |
| `LED_BOOST` nominal | **4.154 V** |
| `LED_BOOST` worst-high (Vf 3.2 V, 117.6 mA, `V_REF` 220 mV) | **4.390 V** |
| `+3V3` input, ±2 % | 3.234 – 3.366 V |
| **Minimum boost ratio** | **3.917 / 3.366 = 1.16** — never leaves regulation |
| Per-resistor current / dissipation | 27.3 mA / **24.6 mW** in an 0603 rated 100 mW — **4×** |

Keeping four resistors quarters the per-part dissipation and leaves three DNP-able trim steps
(8.25 → 11.0 → 16.5 → 33 Ω) available as pure component rework.

### Margin verification

Worst case `V_out` 4.390 V, `I_out` 117.6 mA, `V_in` 3.234 V, η 0.85, `L3` 4.7 µH.

| check | figure | limit | margin |
|---|---|---|---|
| Duty cycle | 0.263 | — | comfortable |
| Average inductor current | 188 mA | — | — |
| **Peak switch current** at `f_SW` 1.2 MHz | **263 mA** | **1.2 A minimum** | **4.6×** |
| Peak switch current at `f_SW` **min 0.75 MHz** | **309 mA** | 1.2 A minimum | **3.9×** |
| **`L3`** XFL4020, 4.7 µH, I_sat ≈ 3.3 A | 309 mA peak | 3.3 A | **10.7×** — unchanged |
| **`D8`** NSR0240, 40 V SOD-323 | 118 mA average | 250 mA I_F(AV) | **2.1×** — the tightest item |
| **`C44`** 1 µF 50 V X7R | operating 4.39 V; `V_OVP_SW` 39 V worst case | 50 V | PASS |
| **`C43`** input decoupling | **4.7 µF, now marked `4.7uF 10V X5R`** | ≥ 4.7 µF X5R local to `VIN` | **PASS — closes B-32** |
| Startup | `I_LIM_Start` 0.72 A against a 309 mA steady peak; built-in soft-start | — | PASS |

**`D8` at 2.1× is the tightest item and is retained.** A same-footprint uprate to a 0.5 A
SOD-323 Schottky (PMEG4005EJ class) is **recommended, not required**, and is a BOM change with
no layout impact.

**The panel backlight rating is not exceeded at any corner.**

---

## 7. GPIO46 strap safety — **B-43 CLOSED**

> **`R_PD` — CTRL pin internal pull-down resistor — 300 kΩ.** TPS61169 datasheet SNVSA40B,
> ELECTRICAL CHARACTERISTICS.

This is the number FBV2-S1-002 could not retrieve, and it settles the question outright.

| requirement | verdict |
|---|---|
| **CTRL cannot force GPIO46 HIGH during strap sampling** | **PROVEN.** CTRL's only internal element is a **pull-down**. It can pull the node toward GND and nothing else — there is no internal pull-up and therefore no mechanism by which the driver can raise the strap |
| **Backlight OFF during reset** | **PROVEN.** CTRL is held below `V_L` = 0.4 V by `R108` ∥ `R_PD`; the part shuts down after `t_SD` = 2.5 ms and stays down until CTRL is toggled |
| **GPIO46 strap not weakened for backlight convenience** | With `R108` 10 kΩ on sheet `02` in parallel with the 300 kΩ internal pull-down, GPIO46 sees **9.68 kΩ to GND** — *stronger* than the strap provision alone |
| **`R109` retained** | **Yes.** Its original justification — a strap escape against an unknown CTRL pull — is now retired, but a fitted 0 Ω costs nothing and remains a general isolation and rework point |

**B-43 is closed with a primary source.**

---

## 8. microSD

The validated Beta-DM architecture is preserved. **Molex `5025700893` retained** — no
lifecycle, mechanical or electrical reason to change it was found.

| item | state |
|---|---|
| `SD_CS_N` | `J2.2` CD/DAT3 → GPIO48, with **`R25` 10 kΩ pull-up to `+3V3`** — the pull-up SD SPI mode requires on DAT3/CS |
| `SPI_A_SCK` | `J2.5` CLK |
| `SPI_A_MOSI` | `J2.3` CMD |
| `SPI_A_MISO` | `J2.7` DAT0 — **direct**, no series element |
| Supply / decoupling | `J2.4` VDD = `+3V3`, `C56` 1 µF local; `J2.6` VSS and `J2.9` SHIELD to GND |
| **Card detect** | **`SD_CARD_DETECT_N`** — see below |
| DAT1 / DAT2 (`J2.8`, `J2.1`) | **left NC**, as validated on Beta-DM. The SD spec's SPI-mode recommendation to hold them high is noted; both are accessible pads, so it can be evaluated at first article with **no board change**. Not added, to avoid churn on a densely packed sheet |
| ESD protection | none on this socket, unchanged from Beta-DM. Recorded, not changed |

### Card detect — the `*_TBD` net is gone

```
J2.11 DETECT_LEVER ── GND
J2.10 DET-SW ──┬── SD_CARD_DETECT_N ──── R113 100 k ──── +3V3
```

`SD_CARD_DETECT_TBD` was a **one-pad net**: a switch terminal with no pull and no
destination. It is now a real two-pin net with a defined idle level.

**Polarity.** `SD_CARD_DETECT_N` assumes the usual push-push convention — the switch closes
on insertion, so **LOW = card present**. The Molex drawing would not load this session (two
distributor mirrors timed out), so the convention is **assumed, not confirmed** — recorded as
**B-46**. The exposure is nil in hardware: the net terminates on a **PCAL9535A input**, so
polarity is a firmware constant. If the switch turns out to be normally closed, the fix is one
inverted comparison, never a board change.

**The crossing to sheet `08` is deliberately not drawn yet.** `SD_CARD_DETECT_N` is a
complete, named, two-pin net local to sheet `03`. Publishing it as a hierarchical signal now
would create a root-level `label_dangling` **error** — KiCad classifies a root label whose net
has two or more pins inside a child sheet as dangling rather than isolated — and the task
forbids new errors. `TOUCH_INT_N` has only one pin behind it, so it crosses now at
warning severity. Both land on sheet `08`. The distinction is an ERC-classification artifact,
not an architectural one, and is recorded here so it is not mistaken for a design decision.

---

## 9. SPI-A bus integrity

| check | finding |
|---|---|
| **Fanout** | 3 nodes per line: MCU + display + microSD. `SPI_A_MISO` is 3 nodes only because `R112` is DNP — **fitted it would be 3 with the display added; unfitted the display is not on the bus at all** |
| **CS default states** | `DISP_CS_N` `R26` 10 kΩ and `SD_CS_N` `R25` 10 kΩ, both pulled to `+3V3`. **Both devices are deselected before the MCU drives anything**, including through reset |
| **Display SDO tri-state** | **unspecified by the vendor** — the reason `R112` is DNP (§4) |
| **microSD DAT0 tri-state** | cards release DAT0 when CS is high; standard, and the Beta-DM path is unchanged |
| **Series damping** | **none added.** With three nodes and the display currently off-bus, damping would be speculative. Damping belongs with real trace lengths, which do not exist until FBV2-P1 |
| **Maximum practical clock** | ESP32-S3 FSPI on IO_MUX pins supports 80 MHz; the ILI9488's 3-byte-per-pixel SPI writes make throughput, not clock rate, the limit. **No architecture change** |
| **Trace-length sensitivity** | flagged for FBV2-P1: display and microSD sit at opposite ends of the board, so SPI-A will be the longest shared bus on the PCB |
| **Bus muxes** | **none added.** No electrical requirement was found, and the firmware contract already forbids simultaneous display and microSD transactions |

**Verdict: passive and simple, and it stays that way.**

---

## 10. Display power and runtime

| condition | `LED_BOOST` × I | out of `U17` | from `+3V3` (η 0.85) | from the pack (η 0.90) |
|---|---|---|---|---|
| *Beta-DM, 4 LED @ 80 mA* | 4.18 V × 80 mA | 0.334 W | 119 mA | **118 mA at 3.7 V** |
| **v2 default (90 mA via PWM)** | 4.06 V × 90 mA | 0.365 W | 130 mA | **129 mA at 3.7 V** |
| **v2 maximum (109 mA)** | 4.15 V × 109 mA | 0.452 W | 161 mA | **160 mA at 3.7 V** |

Other display-side loads are small and unchanged in kind: the ILI9488 logic and the FT6236
both run from `+3V3`, and SPI-A activity at 80 MHz is bursty rather than continuous.

**The backlight is the only load this task changed: +11 mA at the pack at default
brightness.**

### Runtime confirmation — the battery target does not change

Let `I_old` be the browsing current behind the old 2.8-inch / 2000 mAh assumption. v2 draws
`I_old + 11 mA` from a **2500–3000 mAh** pack (D-071).

```
runtime ratio = (2500 / (I_old + 11)) / (2000 / I_old) = 1.25 x I_old / (I_old + 11)
```

This is **≥ 1 whenever `I_old` ≥ 44 mA** — and the Beta-DM backlight *alone* draws 118 mA, so
`I_old` exceeds that threshold by more than a factor of two. At a representative 250 mA
browsing current the ratio is **1.20 at the 2500 mAh minimum and 1.44 at 3000 mAh**.

**Runtime is equal or better at every plausible operating point, and by a wide margin. The
battery target is unchanged: 60 × 75 × 8 mm, ~2500–3000 mAh.** A full re-derivation of
`13 - Power Budget and Battery Runtime v0.1` remains a separate task — that document predates
several v2 changes and should not be patched piecemeal.

---

## 11. ERC and validation

| measurement | errors | warnings | total |
|---|---|---|---|
| Beta-DM baseline | 5 | 53 | 58 |
| after FBV2-S1-002 | 4 | 59 | 63 |
| **after this task** | **4** | 60 | **64** |

**The error report is byte-identical to after FBV2-S1-002. Zero new errors.**

| delta | classification |
|---|---|
| **+** `isolated_pin_label` × 2 — `TOUCH_INT_N`, root label and sheet-`03` hierarchical label | **transitional.** The touch interrupt is drawn; its expander input lands with sheet `08` |
| **−** `isolated_pin_label` — `SD_CARD_DETECT_TBD` | **resolved.** The one-pad `*_TBD` net is now a real two-pin net |

Sheet `03` itself carries **18 inherited `pin_to_pin` warnings** — DB17–DB0 are
`bidirectional` pins tied to a `GND` net that carries a `PWR_FLAG`. The count is unchanged
from Beta-DM. **They were deliberately not silenced:** re-typing the panel's parallel data
pins as `passive` would clear all 18 and would also make the symbol lie about the part.

**Validation run:** all ten sheets parse with balanced structure and CRLF preserved; netlist
export succeeds; `fork_equivalence.py` **PASS**; `netclass_probe.py` **PASS**.

**One consequence of the `LED_A1..A4` → `LED_A` collapse was caught by inspection rather than
by any check:** the `LED_BOOST` netclass in `aqroot-Beta-v2.kicad_pro` listed the four old
anode nets by exact name and had no entry for `LED_A`. Left alone, the new anode net would
have fallen to Default clearance at FBV2-P2 — a latent defect no current probe tests, because
`netclass_probe.py` reads the *board*, which is still Beta-DM. `/03_SPI_A_DISPLAY_SD/LED_A`
was added to the `LED_BOOST` netclass. The old patterns are retained so the probe keeps
passing against the inherited board.

---

## 12. Opportunity and simplification scan

| lens | finding | action |
|---|---|---|
| **A · cheap useful capability** | `TP36` on the panel-side SDO — the only way to characterise ILI9488 SDO release without fitting `R112` | **implemented** (diagnostic, negligible risk) |
| **B · removable obsolete Beta-DM circuitry** | Four separate anode nets for a panel with one anode; a grounded pin 6 that is NC on the new part; two placeholder "DO NOT ROUTE" notes describing an ILI9341 module that was never fitted | **removed / rewritten** |
| **C · safe DNP / rework options** | `R112` 0 Ω DNP (SDO isolation); three DNP-able ballast trim steps already present in `R70`–`R73` | **implemented / retained** |
| **D · duplicated pull-ups or filters** | **none found.** The internal I²C keeps its single locked `R19`/`R20` pair; no panel-side pair was added. `R25`/`R26` are the only CS pull-ups and each serves one device | none |
| **E · test points** | `TP36` added. No test point was removed — sheet `03` had none |
| **F · component-family consolidation** | `R70`–`R73` stay one value (4 × 33 Ω); `R112` reuses the 0 Ω 0603 already in the BOM from `R106`/`R107`/`R109`; `R113` reuses a 100 k 0603 already used elsewhere. **No new package or family was introduced on this sheet** | — |

### Items flagged, not added

* **`D8` uprate to a 0.5 A SOD-323 Schottky** (PMEG4005EJ class). 2.1× margin is the tightest
  number on the sheet. Same footprint, BOM-only change. **Recommended, not required.**
* **DAT1 / DAT2 pull-ups** on the microSD. SD-spec recommendation, Beta-DM leaves them NC,
  evaluable at first article with no board change.
* **No new user-visible or product feature was added.**

### The one item requiring a CTO decision

> **Does the FH52E / JLCPCB second source survive, and does `J1` move to the FH52E standard
> land pattern?** FBV2-DISP-002 ruled that it should, on the strength of a Hirose note that
> FH69 *also* fits the FH52E pattern. That proves one direction. This task was required not to
> claim drop-in without manufacturer drawings proving **full footprint and mechanical**
> equivalence, and those drawings were not obtained, so `J1` stays on the FH69-dedicated
> pattern. **The consequence is that there is currently no JLCPCB-assembly path for `J1`** —
> `FH69-50S-0.5SH` is not in the LCSC catalogue, while `FH52E-50S-0.5SH` is (`C7465440`).
> **Recommendation: obtain both Hirose recommended-PCB-layout drawings at FBV2-S2 and settle
> it there**, before placement makes the pattern expensive to change. Recorded as **B-47**.

---

## 13. Blockers

| # | blocker | status |
|---|---|---|
| ~~**B-43**~~ | TPS61169 `CTRL` internal-pull specification not retrieved | **CLOSED** — `R_PD` = **300 kΩ pull-down**, SNVSA40B. CTRL cannot raise GPIO46 (§7) |
| ~~**B-32**~~ | Confirm ≥ 4.7 µF X5R local to `U17` `VIN` | **CLOSED** — `C43` is 4.7 µF 0805 on `+3V3` at `U17.5`, now marked `4.7uF 10V X5R` |
| ~~**B-28**~~ | ILI9488 `SDO` on a shared bus | **CLOSED by `R112` DNP** (§4) — with the opposite default to the one FBV2-DISP-002 sketched, and the reasoning recorded |
| **B-46** | **microSD detect-switch polarity assumed, not confirmed.** Molex drawing would not load | **OPEN, low.** Firmware constant on a PCAL9535A input; never a board change |
| **B-47** | **FH52E second source and land-pattern migration unresolved.** No JLCPCB path for `J1` as drawn | **OPEN, medium.** Settle at FBV2-S2, before placement |
| **B-29** | `J1` land pattern verified against the vendor drawing with a pad-overlap assertion | **STILL OPEN** — pad geometry is measured (§3), the assertion is FBV2-S2 |
| **B-30** | Which FPC pin supplies FT6236 VDD is not stated | **STILL OPEN, informational.** Immaterial: VDDI, VCI and CTP VDD are all `+3V3` |
| **B-31** | Confirm FPC gold plating on the first article | **STILL OPEN** |
| **B-33** | `J1` at 2.3 mm cannot sit under the panel | **STILL OPEN** — placement constraint for FBV2-P1 |

---

## 14. What must happen next

1. **Do not start sheet `04`.**
2. Rule on **B-47** (FH52E / land pattern) — it is cheap now and expensive after placement.
3. Sheet `08` is the highest-value next migration: it consumes `TOUCH_INT_N`,
   `SD_CARD_DETECT_N`, `SX1262_DIO1` and the charger telemetry that keeps **B-15** open, and
   it is where the TCA9535 → PCAL9535A change lands.
4. FBV2-S1 cannot pass until all nine sheets carry the v2 architecture.
5. The PCB stays untouched until FBV2-P1.

---

## Sources

* `ER-TFT035IPS-6_Datasheet` Rev 2.0 §4.1 — the 50-pin table, archived verbatim in
  [`2026-08-23-display-procurement-lock.md`](2026-08-23-display-procurement-lock.md) §3.4.
* **TPS61169 datasheet SNVSA40B** (Oct 2014, rev. June 2024) — `V_REF` 188/204/220 mV,
  `I_LIM` 1.2 A min, `V_OVP_SW` 36/37.5/39 V, `f_SW` 0.75/1.2/1.5 MHz, `V_H`/`V_L` 1.2/0.4 V,
  **`R_PD` 300 kΩ**, `t_SD` 2.5 ms, VIN 2.7–5.5 V.
* `hardware/beta-v2/libraries/AQROOT_Beta.pretty/Hirose_FH69-50S-0.5SH.kicad_mod` — measured.
* `hardware/beta-v2/reports/FBV2-S1-003-erc.rpt`, `…/FBV2-S1-fork-equivalence.md`.
* [`2026-08-23-display-procurement-lock.md`](2026-08-23-display-procurement-lock.md) — the
  panel, connector and backlight lock this task implements.
