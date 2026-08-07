# AQROOT Beta KiCad Project

This directory contains the canonical KiCad 10 project for the AQROOT Beta main board.

## Current design state

* Digital pin architecture: LOCKED to Beta Pin Map v0.2.4
* Schematic capture: IN PROGRESS
* PCB placement and routing: DO NOT START
* Schematic freeze: BLOCKED pending ERC, footprint audit, RF review, DFM review, and unresolved part selections

### Status vocabulary — read this before quoting any status in this file

| Term | Meaning |
|---|---|
| **SPECIFIED** | The design is written out in Markdown (this README / the Decisions Log). **Nothing has been drawn.** |
| **CAPTURED** | The block actually exists in the `.kicad_sch` file: real symbols, real wires, real nets. |

**These two are never interchangeable.** A block can be fully SPECIFIED — every part, value,
net name and layout note settled — and still be a completely empty sheet in KiCad. Do not
report a SPECIFIED block as captured, drawn, complete, or done.

### Capture status by sheet (2026-07-31)

| Sheet | Status | Notes |
|---|---|---|
| `01_POWER_TREE` | **SPECIFIED, NOT DRAWN** | `.kicad_sch` is an empty stub. Full spec below. |
| `02_MCU_CORE` | **CAPTURED** | ESP32-S3-WROOM-1, EN/BOOT networks, strap test points |
| `03_SPI_A_DISPLAY_SD` | **CAPTURED** | display placeholder + microSD, both CS pull-ups |
| `04_SPI_B_RADIOS_NFC` | **CAPTURED** | CC1101 / SX1262 / ST25R3916 placeholders, 3 CS pull-ups |
| `05_I2C_DEVICES` | **CAPTURED** | BMI270 + bus pull-ups + strap protection |
| `06_AUDIO` | **CAPTURED** | ICS-43434 + MAX98357A + differential speaker |
| `07_IR` | **CAPTURED** | TSOP38238 RX + TSAL6200 low-side NMOS TX |
| `08_BUTTONS_EXPANDERS` | **CAPTURED** | U60/U61 TCA9535PWR, 7 buttons, safe-state pulls |
| `09_COMMUNITY_HEADER` | **SPECIFIED, NOT DRAWN** | `.kicad_sch` is an empty stub. Isolator and load switch are **not even selected** — see below. |

Board-level status:

| Item | Status |
|---|---|
| PCB (`aqroot-Beta.kicad_pcb`) | **EMPTY** — no footprints, no tracks, no board outline |
| ERC | **NEVER RUN** — no report exists, `erc_exclusions` is empty |
| Footprints assigned | **7 of ~47 components** — every resistor, capacitor, switch, test point, the microSD socket and the speaker are still footprint-less |

> `09_COMMUNITY_HEADER` is **not** merely undrawn. Two of its load-bearing parts (the I2C
> isolator/bus switch and the ACC_PWR_EN load switch) have not been selected at all, so the
> sheet cannot be captured yet even in placeholder form. See *Explicit unresolved parts*.

## Locked GPIO expanders (v0.2.4, 2026-07-27)

Both I2C GPIO expanders are Texas Instruments TCA9535PWR, replacing the MCP23017.

* U60 = TCA9535PWR, I2C 0x20 (internal: buttons + control), straps A2=GND A1=GND A0=GND
* U61 = TCA9535PWR, I2C 0x21 (community header), straps A2=GND A1=GND A0=+3V3
* Package = PW, TSSOP-24, 0.65 mm pitch
* Symbol = `Interface_Expansion:TCA9535PWR`
* Footprint = `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` (NOT yet audited — see rules)
* One open-drain active-low `/INT` per device, both wired-OR onto `WAKE_INT_N` -> ESP32 GPIO21

TCA9535PWR is datasheet-trusted and receives its first hardware validation on Beta. The Alpha
bench test that passed was an MCP23017, a different part.

## Explicit unresolved parts

* ~~External community-header I2C isolator or bus switch — **UNSELECTED.**~~ **LOCKED
  2026-08-07: TI `TCA9517ADGKR`, DGK / VSSOP-8** (U16). PCA9515A is not selected.
* ~~ACC_PWR_EN accessory load switch — **UNSELECTED.**~~ **LOCKED 2026-08-07: TI
  `TPS22918DBVR`, DBV / SOT-23-6** (U15).
* **Battery reverse-polarity protection — topology PARKED, see below**

> Both former candidates are now firm part locks. Their **footprints remain UNVERIFIED** —
> locking the part is a separate gate from comparing KiCad copper against the manufacturer
> land pattern. See *Nontrivial footprint verification policy* in [[05 - Design Decisions Log]].

## 01_POWER_TREE — sheet status note to place (2026-07-31)

**Sheet status: SPECIFIED, NOT DRAWN.** Everything below is the written design for this sheet.
`01_power_tree.kicad_sch` is currently an empty stub — none of it exists in KiCad yet. The
block below is the note to place *on the sheet once it is captured*; it is not a record that
capture happened.

```
01_POWER_TREE — BETA ARCHITECTURE COMPLETE

SPECIFIED (NOT YET DRAWN IN KICAD):
- USB-C 5V sink / USB 2.0 front end
- BQ25185 charger/power path
- TPS63020 main +3V3 buck-boost
- TPS61023 NFC 5V PA boost
- MAX17048 fuel gauge
- physical TPS63020 EN hard-off switch

OPEN PRE-FAB BLOCKER:
- reverse-polarity protection implementation

OTHER PRE-FAB VALIDATION:
- exact capacitor MPN / DC-bias checks
- connector and switch mechanical review
- power-domain backfeed review
- professional power / DFM review
```

> **Architecture-complete is not captured, and captured is not fabrication-ready.** The power
> tree is fully specified in Markdown and entirely undrawn in KiCad. Do not describe it as
> captured, drawn or complete, and do not describe it as fabrication-ready once it is drawn.

### Reverse-polarity placeholder — the one block that must STAY undrawn

(The whole of `01_POWER_TREE` is currently undrawn. The distinction here is that every other
block on the sheet is cleared to be captured as soon as someone draws it, whereas this one must
remain a labelled placeholder even after the rest of the sheet exists.)

```
BAT_CONNECTOR_P
       |
[ REV-POLARITY PROTECTION PLACEHOLDER ]
       |
BAT_PROTECTED_P
```

`BAT_CONNECTOR_P` and `BAT_PROTECTED_P` must remain **distinct nets**. Placeholder text:

```
REV-POLARITY:
LTC4368-1 CANDIDATE
+ BACK-TO-BACK N-CHANNEL MOSFETS

TOPOLOGY PENDING:
- LTSPICE CHARGE-PATH SIMULATION
- ADI FAE / VENDOR CONFIRMATION
- PROFESSIONAL POWER / DFM REVIEW

MANDATORY FAULT CASE:
REVERSED BATTERY WHILE USB POWERS BQ25185

DO NOT ROUTE
DO NOT RELEASE TO FAB
```

**Do not instantiate** a final controller, MOSFETs, sense resistor, UV/OV divider, gate clamp or
timer components.

## TPS61023 NFC 5V PA boost — BETA LOCKED, CAPTURE APPROVED (2026-07-31)

| | |
|---|---|
| Part | **TI TPS61023DRLR**, adjustable synchronous boost |
| Package | **DRL, 6-pin SOT563 / SOT-5X3, 1.2 × 1.6 mm** — **do NOT substitute a generic SOT-23 footprint** |
| Symbol / footprint | **Not selected** — verify exact symbol pinout, exact TI DRL footprint, pin-1 orientation, exposed-pad status, manufacturer land pattern |
| In / Out | `BQ25185_SYS` → `NFC_5V_PA_PENDING` |
| Enable | `NFC_5V_EN` from TCA9535 **U60 P02** (100k safe-state pull-down already in the architecture) |
| Load | **ST25R3916 `VDD_PA` ONLY** |

> **FB divider values are PENDING-FROM-DATASHEET.** Inspect the current TPS61023 datasheet and
> EVM schematic and record the exact FB resistor values, inductor and capacitor recommendations
> at capture time. **Do not invent values from memory** — that is why no numbers appear here.

| Ref | Value |
|---|---|
| `U?` | TPS61023DRLR |
| `L_NFC_BOOST` | ~1 µH, **shielded**, low DCR, current rating from the TI design calculation; MPN may stay provisional |
| `C_NFC_BOOST_IN` | input ceramic — value/voltage/dielectric **from TI** |
| `C_NFC_BOOST_OUT` | output ceramic, **or the exact TI-recommended count** |
| `R_NFC_FB_TOP` / `R_NFC_FB_BOT` | FB divider for ~5.0 V — **exact values from the TI 5V reference/EVM** |
| `TP_NFC_5V_EN`, `TP_NFC_5V_PA` | test points |

**Do not connect** ST25R3916 `VDD_IO` (stays on `+3V3`), general 5V accessories, USB VBUS, or any
unrelated load.

```
NFC 5V PA RAIL ONLY
ST25R3916 VDD_IO REMAINS +3V3
NOT A GENERAL-PURPOSE 5V RAIL
```

```
DEFAULT OFF
ENABLE ONLY DURING NFC FIELD OPERATION
```

```
PLACE INDUCTOR, INPUT CAPACITOR AND OUTPUT CAPACITOR
TIGHT TO TPS61023

MINIMIZE SW NODE COPPER AREA

KEEP FB TRACE AWAY FROM SW AND INDUCTOR

PROVIDE SHORT DIRECT GROUND RETURNS
```

**ERC:** VIN is `BQ25185_SYS`; output is only `NFC_5V_PA_PENDING`; `VDD_IO` remains `+3V3`; EN is
`NFC_5V_EN`; the safe-state pull-down exists and no conflicting pull-up was added; FB is not
floating; no support capacitor or inductor omitted; symbol and DRL footprint pin numbering match.

## MAX17048 fuel gauge — BETA LOCKED, CAPTURE APPROVED (2026-07-31)

| | |
|---|---|
| Part | **ADI MAX17048G+T10** — prefer the **G** package over the **X** WLP for Beta assembly/inspection |
| Package | 8-pin 2 × 2 mm TDFN / LFCSP-style |
| Symbol / footprint | **Not selected** — verify official pinout and package drawing, assign the **exact manufacturer land pattern**, include the **exposed pad** if required |
| I²C address | **0x36**, no address configuration |
| Sense resistor | none required |

| Ref | Net |
|---|---|
| `VDD` | **`BAT_PROTECTED_P`** |
| `CELL` | **`BAT_PROTECTED_P`** or the exact recommended system-side sense node |
| `SDA` / `SCL` | `I2C_SDA_INT` / `I2C_SCL_INT` — **no second pull-up pair**, the bus already has the locked 4.7k |
| `ALRT_N` | **test point, otherwise unused**; no-connect marker if the datasheet allows. **Do not connect to `WAKE_INT_N`.** No new GPIO. |
| `C_FG_VDD` | **value from the current datasheet** — X7R, appropriate rating |
| `TP_FG_CELL` | test point |

```
MAX17048 MUST REMAIN BEHIND FINAL REVERSE-POLARITY PROTECTION
DO NOT CONNECT TO RAW BATTERY CONNECTOR POSITIVE
```

```
MAX17048 I2C ADDRESS 0x36
NO ADDRESS CONFIGURATION
```

```
MAX17048 — NEVER BENCH VALIDATED ON AQROOT

BETA BRING-UP REQUIRED:
- I2C detection at 0x36
- cell-voltage accuracy
- SOC plausibility
- charge/discharge response
- hibernate entry/exit
- battery insertion/removal
- charger-connected behavior
- hard-off behavior
- no I2C backpower
- firmware temperature compensation
- low-battery threshold validation
```

> **Do not check the "only one capacitor" assumption off** until the official typical application
> is reviewed for CELL filtering, VDD bypass, alert-network components and exposed-pad grounding.
> **Power-domain item:** the gauge stays battery-powered while `+3V3` is off, but the I²C
> pull-ups are on `+3V3`. Verify from the datasheet that SDA/SCL cannot back-power the disabled
> rail. No level shifting unless primary documentation requires it.

## Physical hard-off switch → TPS63020 EN (2026-07-31)

```
VINA -> [SPST maintained slide switch] -> EN
                                          |
                                   R_EN_PULLDOWN = 100k
                                          |
                                         GND
```

Closed → EN high → TPS63020 on → `+3V3` active. Open → 100k pulls EN low → TPS63020 off →
`+3V3` inactive. **No switch position, including mid-travel, can short VINA to GND** — which is
why SPST-plus-pull-down was chosen over the SPDT common/VINA/GND arrangement.

**Do not connect the switch to** ESP32 GPIO, TCA9535 GPIO, a firmware latch, battery ground, or
the raw battery current path.

**Switch part:** MPN provisional until mechanical review, **but the footprint must correspond to
a real candidate**. SPST preferred; **maintained** positions; low-profile side/top actuator;
through-hole mounting tabs preferred for strength; side-wall accessible; clear OFF/ON. **Do not
assign a tiny signal-switch footprint without checking** actuator travel, body dimensions,
mounting tabs, PCB edge setback, enclosure cutout and hand-solder access.

```
SWITCH POSITION / ACTUATOR / ENCLOSURE CUTOUT
REQUIRE FIELD SLATE MECHANICAL REVIEW BEFORE ROUTING
```

```
PHYSICAL MAIN-RAIL HARD OFF

SWITCH OFF:
TPS63020 DISABLED
+3V3 SYSTEM RAIL OFF

UPSTREAM BATTERY CIRCUITS REMAIN POWERED:
BQ25185
MAX17048
REVERSE-PROTECTION CONTROLLER CANDIDATE

TOTAL BATTERY STANDBY IS NOT ZERO
```

**Never claim** complete battery isolation, shipping mode, zero battery current or zero standby
draw. Soft push-button power UX / load-switch / latch / shipping-mode architecture is a
**post-Kickstarter option, not part of Beta**.

## USB-C 5V sink + USB 2.0 front end — BETA LOCKED, CAPTURE APPROVED (2026-07-30)

**Cleared to be drawn in `01_POWER_TREE` now.** Beta-locked, **not production-hardened** —
subject to professional power/DFM/EMI review before fabrication.

**Role: USB Type-C SINK / UFP. 5V only. USB 2.0 full-speed. NO PD, NO source role, NO DRP, NO
VCONN, NO alternate modes.**

### Connector

| | |
|---|---|
| Family | **GCT USB4105**, 16-contact USB 2.0 Type-C, top-mount horizontal, SMD contacts, TH shell stakes |
| Candidate MPN | **GCT USB4105-GF-A-120** — *verify drawing, shell-stake length vs PCB thickness, symbol pin numbering, and that the footprint matches the drawing before locking* |
| Footprint | `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` |
| Symbol | 16-pin USB 2.0 Type-C receptacle — **verify pin numbering; do not use a 24-pin SuperSpeed symbol** |

Pin mapping: VBUS = **A4, B9, A9, B4** · GND = **A1, A12, B1, B12** · D+ = **A6, B6** ·
D− = **A7, B7** · CC1 = **A5** · CC2 = **B5** · SBU1 = **A8 (NC)** · SBU2 = **B8 (NC)** ·
shield tabs → `USB_SHIELD`.

> **A 16-contact receptacle has no SuperSpeed TX/RX contacts — do not invent them.** Join all
> duplicate VBUS, GND, D+ and D− contacts. Mark **only** SBU1/SBU2 no-connect.

### Components and reference designators

| Ref | Value | Notes |
|---|---|---|
| `J?` | GCT USB4105-GF-A-120 | suffix pending |
| `R_CC1_RD` | **5.1k, 1%** | CC1 → GND |
| `R_CC2_RD` | **5.1k, 1%** | CC2 → GND — **independent; never shared, never combined, never firmware-connected** |
| `U?` | **USBLC6-2SC6** (SOT-23-6) | verify pinout against the **ST datasheet** |
| `R_USB_VBUS_LINK` | 0R | optional bring-up current-measurement / isolation link |
| `C_USB_VBUS` | **4.7 µF**, 10 V min, X7R | **deliberately 4.7 µF, not 10 µF** — keeps hot-plug inrush conservative. MPN deferred to pre-fab BOM validation |
| `R_USB_DN_SER` | **22R** | D− series, **at the MCU end** |
| `R_USB_DP_SER` | **22R** | D+ series, **at the MCU end** — equal value + matching footprint; 33R is an option after SI review, **never mixed across the pair** |
| `C_USB_DN_EMC` | 100 pF **DNP** | MCU-side node → GND |
| `C_USB_DP_EMC` | 100 pF **DNP** | MCU-side node → GND |
| `R_USB_SHIELD_LINK` | **0R, populated** | `USB_SHIELD` → GND (Beta default) |
| `R_USB_SHIELD_BLEED` | 1M, **DNP** | alternative — **do not populate both without review** |

Optional DNP shield→GND capacitor footprint **only if board space permits**; no mandatory value.

### Nets

`USB_VBUS_RAW` · `USB_VBUS_CHG` · `USB_D_N_CONN` · `USB_D_P_CONN` · `USB_D_N_MCU` ·
`USB_D_P_MCU` · `USB_SHIELD` · `GND`

```
VBUS pins -> USB_VBUS_RAW -> [R_USB_VBUS_LINK 0R] -> USB_VBUS_CHG -> BQ25185 VIN
                  |
                  +-- C_USB_VBUS 4.7uF
                  +-- USBLC6 VBUS pin  (BRANCH — clamp reference, NOT series)

D- (A7,B7) -> USB_D_N_CONN -> USBLC6 ch -> R_USB_DN_SER 22R -> USB_D_N_MCU -> GPIO19
D+ (A6,B6) -> USB_D_P_CONN -> USBLC6 ch -> R_USB_DP_SER 22R -> USB_D_P_MCU -> GPIO20
```

**GPIO19 = D−, GPIO20 = D+. Do not cross.** `C_USB_VBUS` does **not** replace the bq25185's own
VIN decoupling, which is captured with the charger's support network.

### Sheet notes to place

```
TWO INDEPENDENT 5.1k Rd RESISTORS REQUIRED
USB-C SINK / UFP, 5V ONLY
NO PD NEGOTIATION
```

```
STATIC Rd ESTABLISHES THE SINK ROLE
NO CC CURRENT-ADVERTISEMENT DETECTION IS IMPLEMENTED
BQ25185 INPUT-CURRENT POLICY MUST NOT ASSUME 1.5A/3A
FROM AN UNKNOWN SOURCE
```

```
USBLC6 VBUS PIN IS A CLAMP REFERENCE
NOT A SERIES POWER PATH
```

```
ESD CURRENT PATH TO GND MUST BE SHORT AND DIRECT
PLACE ESD BEFORE LONG DATA TRACES
MINIMIZE STUB BETWEEN CONNECTOR AND ESD ARRAY
```

```
DNP FOR BETA
POPULATE ONLY AFTER SIGNAL-INTEGRITY / EMI REVIEW
```

```
SHIELD-GROUND STRATEGY PROVISIONAL FOR EMI/ESD REVIEW
DEFAULT BETA LINK: 0R
DO NOT LEAVE SHIELD FLOATING WITHOUT REVIEW
```

Prominent, beside the block:

```
USB-C 5V SINK / USB 2.0 DEVICE

CC1: 5.1k TO GND
CC2: 5.1k TO GND
SEPARATE Rd RESISTORS — DO NOT COMBINE

NO PD / NO VCONN / NO SOURCE ROLE
SBU1/SBU2 NC

USBLC6-2SC6:
DATA + VBUS ESD CLAMP
VBUS PIN NOT IN SERIES

D+/D-:
22R SERIES AT MCU
100pF DNP EMC FOOTPRINTS

GENERIC USB CURRENT LIMIT MUST REMAIN CONSERVATIVE
WITHOUT CC CURRENT-ADVERTISEMENT DETECTION
```

### Layout notes

**D+/D−:** 90 Ω differential pair (tolerance per stack-up); equal length; continuous GND
reference; minimise vias; no stubs; avoid switch nodes, inductors, antennas, crystal traces;
preserve pair spacing; paired ground-return vias on any unavoidable layer change.
**Placement order:** connector → USBLC6-2SC6 → controlled differential routing → series
resistors near ESP32-S3 → ESP32-S3 USB pins.
**VBUS:** width suited to expected input current; bulk cap and ESD clamp close; keep away from
D+/D− where practical.

### ERC checks

**Do not globally weaken ERC.** CC1 and CC2 each have their own 5.1k and are not shorted; D+/D−
not swapped (**GPIO20 = D+, GPIO19 = D−**); USBLC6 VBUS not treated as series power; SBU1/SBU2
have no-connect markers; all VBUS contacts joined; all GND contacts joined; shield not used as
signal GND through an unintended duplicate path; no nonexistent SuperSpeed pins; no PD
controller; **no GPIO allocated for CC logic**.

## TPS63020 3.3V block — ARCHITECTURE LOCKED, CAPTURE APPROVED (2026-07-30)

**This block is cleared to be drawn in `01_POWER_TREE` now.** Capacitor exact MPNs are a
**BOM-release gate, not a schematic-capture gate** — draw the block, mark the open items on the
sheet, and do not stall capture on per-capacitor DC-bias research.

Block title to place on the sheet:

```
TPS63020 3.3V BUCK-BOOST
ARCHITECTURE LOCKED
CAPACITOR MPNs PENDING PRE-FAB BOM VALIDATION
```

### Rails

| | Net |
|---|---|
| In | **`BQ25185_SYS`** |
| Out | **`+3V3`** |
| Ground | Per the TI datasheet's own PGND/AGND treatment. **Do not invent split-ground nets** unless the datasheet explicitly requires them. |

The block connects to `BQ25185_SYS`, **not** to the raw battery connector.

### Components and reference designators

| Ref | Value | Locked? | Notes |
|---|---|---|---|
| `U?` | **TPS63020DSJR** | ✅ | DSJ package. **Verify the official TI pinout before wiring** — do not trust a third-party symbol unchecked. |
| `L1` | **XFL4020-152MEC** 1.5 µH | ✅ | Coilcraft, LCSC **C3033018**. Use the manufacturer-recommended footprint, or one matching the **official Coilcraft land pattern**. |
| `R_FB_TOP` | 1M, 1% | ✅ | VOUT → FB |
| `R_FB_BOTTOM` | 180k, 1% | ✅ | FB → GND. **No Cff, no third resistor.** |
| `R_PG_PULLUP` | 1M | ✅ | +3V3 → PG (open-drain) |
| `SW?` | SPST maintained slide switch | ✅ | **Physical hard-off**: VINA → switch → EN |
| `R_EN_PULLDOWN` | 100k | ✅ | EN → GND, defines the OFF state |
| `R_EN_BYPASS` | 0R **DNP** | ✅ | VINA → EN, **bench bypass only** — supersedes the withdrawn `R_EN_LINK` |
| `R_PS_DEFAULT` | 0R | ✅ | PS/SYNC → GND |
| `C_VINA` | 100nF X7R | ✅ | VINA→GND, close to VINA. **Do not exceed 220nF without review.** |
| `CIN1`, `CIN2` | 10 µF each | value ✅ / **MPN ❌** | 10 V min, X7R, **1206 preferred**. Close to VIN/PGND. |
| `COUT1`–`COUT4` | 22 µF each | value ✅ / **MPN provisional** | 10 V, X7R, **1206**. Tight around VOUT/PGND. |

Test points: **PG**, **EN**. Plus a **DNP landing** on EN for the future external hard-off
controller, and a test point / solder-jumper / DNP option on PS/SYNC for forced-PWM.

### Locked defaults — and why no GPIO is consumed

```
PHYSICAL MAIN-RAIL HARD OFF
MCU CANNOT RESTORE ITS OWN DISABLED 3V3 RAIL
```

* **EN must not float.** Driven by the **physical SPST maintained hard-off switch**
  (VINA → switch → EN) with **`R_EN_PULLDOWN` 100k** to GND holding the OFF state.
  **Never connect EN to the ESP32, the TCA9535, or any firmware-controlled signal.**
* **The permanent `R_EN_LINK` 0R is WITHDRAWN** (superseded 2026-07-31). It survives only as
  **`R_EN_BYPASS` 0R, DNP**. A populated permanent link in parallel with a switch that pulls EN
  low would defeat OFF and short VINA to GND.

```
DO NOT POPULATE R_EN_BYPASS WHEN HARD-OFF SWITCH IS FITTED
UNLESS INTENTIONAL ALWAYS-ON BENCH CONFIGURATION IS REQUIRED
```
* **PS/SYNC must not float.** Tied to GND through `R_PS_DEFAULT` 0R → **power-save default**.
  Forced-PWM is a bring-up/EMI option only. **Never allow the GND link and a VINA link to be
  populated simultaneously without an explicit assembly warning** — that shorts VINA to GND.
* **PG is diagnostic only.** `PG DIAGNOSTIC ONLY / NO GPIO ALLOCATED`. No MCU, no expander.

### Sheet notes to place

Beside L1:

```
LOCKED MPN: XFL4020-152MEC
XGL4020-152 MAY BE REVIEWED AS AN APPROVED ALTERNATE
DO NOT SILENTLY SUBSTITUTE
```

Beside the FB divider (keep the FB node compact and visually clear of switching nodes):

```
KEEP FB TRACE SHORT
ROUTE AWAY FROM L1, L1/L2 SWITCH NODES AND HIGH-DI/DT LOOPS
SENSE VOUT AFTER OUTPUT CAPACITORS
```

Prominent, beside the block:

```
CAPACITOR MPNs NOT BOM-LOCKED
VERIFY DC-BIAS EFFECTIVE CIN/COUT BEFORE FAB

CIN:
2 x 10uF, 10V+, X7R
TOTAL EFFECTIVE >=10uF AT 4.5V

COUT:
4 x 22uF, 10V, X7R, 1206
TOTAL EFFECTIVE >=40uF AT 3.3V

DO NOT USE OBSOLETE GRM21BR71A106KE51L
```

### ERC handling

**Do not globally reduce ERC severity.** For findings from the incomplete reverse-polarity block
or the hard-off DNP landing: classify explicitly, and use a **narrowly scoped** no-connect,
no-ERC marker or documented waiver **only where justified**. Never suppress unrelated errors.

Check on this block: EN not floating; PS/SYNC not floating; PG pull-up present; FB connected
only to the intended divider; no obsolete capacitor MPN present; no GPIO consumed; `+3V3`
power-flag strategy consistent with existing project conventions.

## Reverse-polarity protection — PARKED (2026-07-30)

**`01_POWER_TREE` may be captured. Every section EXCEPT the battery-input protection block is
drawn normally** — this park does not stall the rest of the power tree or the board.

The battery-input protection block must remain a clearly labelled functional placeholder:

```
REV-POLARITY:
LTC4368-1 CANDIDATE + BACK-TO-BACK NFETs
TOPOLOGY PENDING SIM / ADI VENDOR / POWER-DFM REVIEW
DO NOT ROUTE
```

* **Decided and locked:** high-side only; battery negative stays tied directly to system GND.
  The keyed connector is an *additional mechanical layer only*, never the primary electrical
  defence.
* **Leading candidate, NOT locked:** ADI **LTC4368-1** active back-to-back N-FET controller
  driving two series **AO3400A-class** N-channel FETs.
* **Not selected:** exact MOSFET, sense resistor, UV/OV divider, timer/inrush parts, gate clamp
  and package. **Do not assign a footprint to this block.**
* **Rejected as final solutions:** single PMOS alone; naive passive back-to-back; any passive
  gate network that can leave a FET partially-on under charger drive; low-side protection;
  keyed connector as primary defence; ordinary load switches that block charging; cell
  over/under-voltage protectors that don't address physical reverse insertion.

> **GATE: final topology lock belongs to the professional power/DFM pre-fabrication review**,
> which must run the LTC4368 LTspice charge-path case and obtain ADI vendor/FAE confirmation.
> **No PCB routing and no fabrication release until that gate is closed** — this blocks the
> whole board, not just the power sheet.

Full record, including the locked requirement, the open questions (a)–(f), and the 14-case Beta
validation card: [[05 - Design Decisions Log]].

## Rules

* Do not generate or modify KiCad schematic or PCB files automatically.
* KiCad files will be created manually in KiCad 10.0.3.
* Do not assign unverified footprints. The U60/U61 TSSOP-24 footprint above is assigned but NOT
  yet verified against the TI datasheet drawing — audit it before freeze.
* Do not begin PCB routing until the full schematic passes review and ERC, **and until the
  power/DFM pre-fab review has locked the reverse-polarity topology** (see above).
* Preserve the authoritative GPIO assignments from Beta Pin Map v0.2.4.
* Do not reintroduce MCP23017 nomenclature (GPAn/GPBn, INTA/INTB, IODIR, GPPU, GPINTEN, INTF,
  INTCAP, IOCON, DEFVAL, INTCON). The TCA9535 register set is 0x00-0x07 only.
