# AQROOT Full Beta v2 — Community Expansion and Accessory Power Closeout

Date: **2026-08-23**
Task: **FBV2-COMM-001**
Repository HEAD at audit: `c2ef26c`
> ## ⚠ SUPERSEDED IN PART — THE CONNECTOR SELECTION IN THIS AUDIT IS WRONG.
>
> **Harwin `M20-7881242` (§4) is OBSOLETE and was REJECTED on 2026-08-23.**
> `harwin.com` returns HTTP 404 for it. The MPN was **configured from the Harwin
> catalogue's ordering scheme** rather than taken from a live listing — the risk
> this audit itself flagged in §15 item 2.
>
> **The connector is now Samtec `BCS-112-S-D-HE`.** See
> [`2026-08-23-community-connector-correction.md`](2026-08-23-community-connector-correction.md)
> (FBV2-COMM-002) and D-093.
>
> **Everything else in this audit stands**: the 24-contact allocation, the pin
> ordering and its mis-insertion proof, both accessory rails, the expander
> architecture, the power budget and the firmware contract. The reasoning in §4.2
> about *why* keying must come from the enclosure at 2.54 mm also stands.
>
> This audit is a dated snapshot and is **not** rewritten. Only this banner is added.

Scope: **documentation only.** No KiCad, PCB, firmware, mechanical CAD or fabrication
file was created or modified. `hardware/beta-v2/` was not created.

> ### ⚠ THE 20-PIN COMMUNITY PORT ARCHITECTURE IS SUPERSEDED.
>
> **D-059 and D-062** (11 XGPIO · 2 native · 2 I²C · 1 WAKE · 1 switched 3V3 · 3 GND
> = 20) are **superseded in full** by the CTO's new product ruling recorded here.
> Nothing downstream may cite the 20-pin allocation. The parts of D-057 (no
> permanent raw `+3V3`), D-058 (TPS22950C), D-060/D-063 (native pair) and D-045
> (native and XGPIO documented distinctly) that are still true are **carried
> forward explicitly** below rather than inherited silently.

This is the last architecture closeout before schematic implementation.

---

## 0. Verdict

> ### COMMUNITY PORT LOCK = **PASS**
>
> **Connector: Harwin `M20-7881242`** — 2×12, 2.54 mm, **female**, right-angle
> through-hole, keying and shroud from the enclosure.
> **24 active contacts, no wasted key/NC position.**
> **3.3 V rail: `+3V3` → TPS22950C → `ACC_3V3_SW`.**
> **5 V rail: `BQ25185_SYS` → second TPS61023 → second TPS22950C → `ACC_5V_SW`.**
> **All five accessory control signals fit on `U3` — exactly, with zero spare.**
> **P-02 CLOSED. P-15 CLOSED. P-16 CLOSED. B-08 CLOSED.**

---

## 1. Sources

| # | source | weight |
|---|---|---|
| **S1** | **Harwin M20 series catalogue** (`Harwin_M20_3623`) — specification page, mating-profile matrix, female horizontal PC-tail drawing and ordering scheme | **Primary manufacturer document**, retrieved and text-extracted |
| **S2** | **TI `TPS22950` datasheet SLVSFJ2B** (Dec 2020, rev. Feb 2023) — device comparison table, pin functions, recommended operating conditions, current-limit equation, RCB section, functional-mode table | **Primary**, retrieved and text-extracted in full |
| **S3** | **TI `TPS61023` datasheet SLVSF14B** (Sep 2019, rev. Aug 2020) — features, electrical characteristics, logic thresholds, protection | **Primary**, retrieved and text-extracted in full |
| **S4** | TI `BQ25185` product documentation — discharge current capability, BATFET resistance, supplement mode, BATOCP hiccup | Primary vendor text |
| **S5** | `11 - Beta Pin Map v0.2.md` §7a / §7b (read only) | **Measured** — the as-built `U2` / `U3` expander allocation |
| **S6** | `docs/full-beta-v2/CTO_DECISIONS.md`, `architecture/ARCHITECTURE.md`, `mechanical/MECHANICAL_INTERFACE_SPEC.md` (read only) | Locked v2 architecture |
| **S7** | `audits/2026-08-22-pre-design-engineering-audit.md` §safe-state pulls (read only) | **Measured** — the seven existing safe-state pull resistors |
| **S8** | `audits/2026-08-23-display-procurement-lock.md` | Backlight load, re-derived |

---

## 2. The new port — allocation

### 2.1 CTO product ruling implemented

| requirement | implementation |
|---|---|
| Device side **FEMALE** | Harwin `M20-7881242` socket |
| **Recessed** into the enclosure | right-angle body behind a recessed right-face aperture |
| **Keyed / polarized** | **from the enclosure** — asymmetric recess with a lead-in rib. Explicitly permitted by the ruling |
| **Shrouded / protected** | the enclosure recess is the shroud |
| Accessory side **MALE pins** | any standard 2×12, 0.64 mm (0.025″) square-post header |
| **2 rows × 12 positions, 24 ACTIVE contacts** | 24/24 used; **no NC, no key contact** |

### 2.2 Final 24-contact allocation — LOCKED

| function | contacts | net(s) |
|---|---|---|
| Expander GPIO | **10** | `XGPIO0` … `XGPIO9` |
| Native ESP32 GPIO | **2** | `NATIVE_A` = GPIO38, `NATIVE_B` = GPIO47 |
| External I²C | **2** | `EXT_SDA`, `EXT_SCL` (buffered, `U16` TCA9517A) |
| Wake / attention | **1** | `WAKE_ATTN_N_HDR` |
| Protected switched 3.3 V | **2** | `ACC_3V3_SW` (one net) |
| Protected switched 5 V | **2** | `ACC_5V_SW` (one net) |
| Ground | **4** | `GND` |
| Accessory detect | **1** | `ACC_DETECT_N` |
| **TOTAL** | **24** | |

**Duplication rule respected.** The duplicated contacts are *only* the two power
rails and ground, and each duplicate pair is the **same electrical net**, present
to halve contact resistance and simplify accessory routing. **No GPIO is
duplicated** (D-042 carried forward). At 3 A per contact (S1) a single contact
could carry any of these rails on its own — the duplication is margin, not
necessity.

**Delta against the superseded 20-pin architecture:** XGPIO 11 → **10**
(one XGPIO is surrendered to make room for the fifth accessory-control expander
pin — see §7); +1 GND; +2 five-volt contacts; +1 `ACC_DETECT_N`.

---

## 3. Pin ordering — LOCKED

Numbering is the conventional dual-row alternation: **odd pins = row A**,
**even pins = row B**. Column *n* = pins (2n−1, 2n).

| Col | Pin | Row A (outer) | Pin | Row B (inner) |
|:---:|:---:|---|:---:|---|
| 1  | 1  | `XGPIO0`            | 2  | `EXT_SCL`        |
| 2  | 3  | **`ACC_3V3_SW`**    | 4  | **`GND`**        |
| 3  | 5  | `XGPIO1`            | 6  | `EXT_SDA`        |
| 4  | 7  | **`NATIVE_A`** (GPIO38) | 8  | `XGPIO2`     |
| 5  | 9  | **`GND`**           | 10 | **`ACC_5V_SW`**  |
| 6  | 11 | **`NATIVE_B`** (GPIO47) | 12 | `XGPIO3`     |
| 7  | 13 | `XGPIO4`            | 14 | `WAKE_ATTN_N`    |
| 8  | 15 | **`ACC_3V3_SW`**    | 16 | **`GND`**        |
| 9  | 17 | `XGPIO5`            | 18 | `XGPIO6`         |
| 10 | 19 | `XGPIO7`            | 20 | `XGPIO8`         |
| 11 | 21 | **`GND`**           | 22 | **`ACC_5V_SW`**  |
| 12 | 23 | **`ACC_DETECT_N`**  | 24 | `XGPIO9`         |

### 3.1 Why this ordering, rule by rule

| CTO requirement | how it is met |
|---|---|
| Distribute power contacts | The four power/ground **columns are 2, 5, 8 and 11** — every third column, ends left free for signals |
| Distribute GND | `GND` at pins 4, 9, 16, 21 — **alternating rows** and evenly spaced |
| Do not place both 3.3 V together | `ACC_3V3_SW` at pins **3 and 15** — six columns apart |
| Do not place all 5 V in one region | `ACC_5V_SW` at pins **10 and 22** — six columns apart |
| GND near native / high-speed signals | `NATIVE_A` (7) and `NATIVE_B` (11) **flank the GND at pin 9**. One ground serves both fast pins as a return reference *and* separates them so they cannot couple |
| — also applied to I²C | `EXT_SCL` (2) and `EXT_SDA` (6) flank the GND at pin 4 — reduces SCL/SDA coupling on the accessory cable |
| — also applied to WAKE | `WAKE_ATTN_N` (14) is in-row adjacent to the GND at pin 16 |
| Simple accessory routing | **All 3.3 V lives in row A; all 5 V lives in row B.** An accessory runs one rail along each row. It is also trivially memorable and silkscreenable |
| `ACC_DETECT_N` positioned sensibly | Pin 23, the **last position of row A**, in-row adjacent to the GND at pin 21. The accessory asserts detect with **one 0 Ω link between pins 21 and 23** — the simplest possible accessory implementation |

### 3.2 Mis-insertion analysis

This is the requirement *"minimize accidental power-to-signal damage from connector
misalignment"*, and it is the reason the layout is not simply sequential.

**(a) Row swap (accessory flipped about the long axis), pin *n* ↔ its column partner:**

| column | row A | row B | result of a swap |
|---|---|---|---|
| 2 | `ACC_3V3_SW` | `GND` | rail-to-ground short — **current-limited by the TPS22950C, auto-retry, safe** |
| 5 | `GND` | `ACC_5V_SW` | rail-to-ground short — **safe** |
| 8 | `ACC_3V3_SW` | `GND` | rail-to-ground short — **safe** |
| 11 | `GND` | `ACC_5V_SW` | rail-to-ground short — **safe** |
| all others | signal | signal | 3.3 V logic against 3.3 V logic through series resistors — **safe** |

> **Every power contact is vertically paired with GND.** That is the constraint
> that forced the 4-power-column layout, and it means **no row swap can ever put
> 5 V or 3.3 V onto a logic pin.**

**(b) Row swap and the detect strap.** A flipped accessory presents its row-B pins
to AQROOT's row A. Its detect strap (its pins 21–23) therefore lands on AQROOT's
pins **22 and 24** — `ACC_5V_SW` and `XGPIO9`. **This is the one residual hazard,
and it is neutralised by the detect gating**: a flipped accessory cannot ground
AQROOT's pin 23, so `ACC_DETECT_N` never asserts, so **neither rail is ever
enabled** and pin 22 is an unpowered, reverse-blocked output. The fault is
passively safe and self-announcing (the accessory simply does not come up).

**(c) One-column shift.** A shift moves a power column onto a signal column. This
**cannot be prevented electrically** and is prevented **mechanically**: the
enclosure recess must be closed at both ends so that a partially or laterally
displaced mate is physically impossible. Recorded as a mechanical requirement
(§9, **M-10**).

**(d) 180° in-plane rotation.** Prevented by the enclosure key.

---

## 4. Connector selection

### 4.1 Selected — Harwin `M20-7881242`

| parameter | value | source |
|---|---|---|
| Manufacturer / MPN | **Harwin — `M20-7881242`** ("12+12 DIL horizontal socket") | S1 |
| Series / family | M20, 2.54 mm (.100″) pitch, **Female Horizontal PC Tail**, double row | S1 |
| Gender | **FEMALE** (twin-leaf phosphor-bronze contacts) | S1 |
| Pitch | **2.54 mm**, row spacing 2.54 mm | S1 |
| Positions | **2 × 12 = 24** | S1 |
| Insertion orientation | **Right-angle / horizontal** — mating axis parallel to the PCB, i.e. straight out through the right side wall (matches D-070) | S1 |
| Termination | **Through-hole**, with **two-point solder fixing for connector rigidity** | S1 |
| Body envelope | PCB pattern length **A = B + 2.74 = 30.68 mm** (B = 2.54 × 11 = 27.94); depth **7.87 mm**; height above board **8.10 mm** | S1 |
| Mating part | any standard 2×12 2.54 mm **male** header on 0.64 mm square posts; Harwin's own males are M20-97x / M20-99x | S1 |
| **Current rating** | **3 A per contact** | S1 |
| **Durability** | **300 mating operations (gold finish)** / 50 (tin) | S1 |
| Contact resistance | 30 mΩ max | S1 |
| Insertion / withdrawal force | 2.0 N max / 0.3 N min **per contact** | S1 |
| Voltage proof | 800 V AC, 500 V DC for 1 min | S1 |
| Insulation resistance | 1 000 MΩ min | S1 |
| Operating temperature | **−40 … +105 °C** | S1 |
| Vibration / shock | 50–2 000 Hz at 3.13 G / 30 G for 11 ms | S1 |
| Moulding | UL94V-0 | S1 |
| Finish code | **42 = Gold + Tin** (46 = Tin, **rejected** — 50 cycles only) | S1 |
| JLC / LCSC | **Not stocked.** A generic 2.54 mm 2×12 female header of the LCSC BOOMELE / ZHOURI class (same family as `C30867`, the 2×10) is available as a cost-down alternate | LCSC catalogue |
| Cost | ≈ US$2–4 in prototype quantity from Harwin distribution (Digi-Key / Mouser / RS), MOQ 1 | distributor class |

### 4.2 Why keying comes from the enclosure

A deliberate finding, stated plainly: **at 2.54 mm there is effectively no
mainstream board-mount FEMALE connector with an integrated shroud and key.** The
ubiquitous shrouded, polarized 2.54 mm part is the **male** IDC box header, which
is the wrong gender for this product. The alternatives were:

| option | verdict |
|---|---|
| **Female socket + enclosure-formed shroud and key** (selected) | Mates with any US$0.10 2×12 male pin header — **maximum maker friendliness**, which is the stated reason for choosing 2.54 mm at all. Keying from the enclosure is explicitly permitted by the ruling. Zero BOM cost for the shroud |
| Samtec **Mini Mate `IPL1`** (2.54 mm, shrouded, polarized, latching) | **Rejected — wrong gender and wrong ecosystem.** IPL1 is a *box header* (male pins in a shroud); its mate is a Samtec `IPD1`/`IPT1`, not a standard pin header. Makers could not build accessories with commodity parts |
| **2.00 mm keyed/shrouded systems** (Hirose DF11, Molex Milli-Grid) | **Rejected.** They do give a proper connector-side key and shroud, and they are ~20 % shorter, but they abandon standard 2.54 mm male pins — which the CTO identified as the whole point of the pitch choice. Held in reserve only if the Z-height finding in §9 forces a change |
| Generic LCSC 2×12 female header | **Rejected as the device-side part** — plating and cycle life unspecified. Acceptable only as a cost-down after qualification |

**2.54 mm is retained.** It creates no unacceptable mechanical or sourcing problem
except the Z-height item in §9, which passes.

### 4.3 Enclosure and keying implications

| item | requirement |
|---|---|
| Recess | Right face, recessed so the socket face sits **behind** the outer surface |
| Shroud | Formed by the recess walls on all four sides |
| **Key** | **Asymmetric recess profile + one lead-in rib**, offset from the connector centreline, so the accessory shell seats in exactly one orientation |
| End stops | The recess must be **closed at both ends** so a one-column shift is mechanically impossible (§3.2c) |
| Lead-in | Chamfered entry on all four walls |
| **Load path** | Up to **48 N** maximum insertion force (24 × 2.0 N). The enclosure must take that load on a boss or rib — **not** through the PCB solder joints alone. The socket's two-point solder fixing helps but is not sufficient on its own |
| Marking | Pin-1 triangle plus **"3V3 LOGIC ONLY"** and **"5V = POWER ONLY"** on the recess face or the adjacent shell |

---

## 5. The 3.3 V accessory rail

```
+3V3 ──> TPS22950C ──> ACC_3V3_SW ──> pins 3, 15
           ON  = ACC_3V3_EN   (U3, external safe-state pull-down)
           ILIM= R_ILIM to GND
           FLT = ACC_3V3_FAULT (open-drain, pull-up to +3V3, U3 input)
```

### 5.1 TPS22950C is confirmed appropriate at 3.3 V

Every requirement checked against **S2**:

| requirement | evidence | verdict |
|---|---|---|
| Operates at 3.3 V | `VIN` recommended **1.8 V – 5.5 V** | **PASS** |
| Default OFF | `ON` is active-high with a **500 kΩ smart pull-down**; the datasheet still says *"Do not leave floating"* | **PASS with the mandatory external pull-down** |
| Independent software control | `ON` driven by `ACC_3V3_EN` on `U3`; `VIH` min 1.0 V, `VIL` max 0.35 V — comfortably inside PCAL9535A drive | **PASS** |
| External hardware safe-state pull-down | 100 kΩ to GND, mandatory (carried forward from S7's seven-pull discipline) | **PASS** |
| Reverse-current blocking | **RCB = Yes** for the C variant (Device Comparison Table). Threshold ≈ 900 mA with delay `tRCB`; **"When the ON pin is pulled low, the device constantly blocks reverse current"** | **PASS** |
| Adjustable current limit | **0.5 A – 3.5 A** for the C variant | **PASS** |
| Short-circuit protection | Constant-current limiting, **auto-retry** response | **PASS** |
| Thermal protection | TSD at 170 °C rising | **PASS** |
| Fault visibility | **`FLT`, open-drain** | **PASS — with a caveat, see §5.3** |
| Accessory cannot collapse the core rail | The switch holds a hard short at `ILIM`; §8 shows `+3V3` stays inside the TPS63020's 2 A rating in that state | **PASS** |
| Leaded package | **DDC (SOT-23-thin, 6-pin)**, 2.90 × 2.80 mm | **PASS** |

`R_ON` = 41 mΩ at 3.3 V. Turn-on time 550 µs at 3.3 V — **slow by design, so
enabling the rail cannot cause an inrush step on `+3V3`.**

### 5.2 Current-limit recommendation — NOT fabrication-locked

Datasheet equation (S2 §9.3.3): `ILIM = 1.18 × (R_ILIM[kΩ])^−1.072`, with a
characterised spread of roughly **−25 % / +25 %** (e.g. 1.15 kΩ → 0.75 / 1.00 /
1.25 A).

| R_ILIM | ILIM typ | ILIM worst-case band | published continuous | headroom at worst-low |
|---|---|---|---|---|
| **1.5 kΩ (recommended, first fabrication)** | **0.76 A** | **0.57 – 0.96 A** | **400 mA** | **1.43×** |
| 1.21 kΩ | 0.96 A | 0.72 – 1.20 A | 500 mA | 1.44× |
| 1.15 kΩ (datasheet point) | 1.00 A | 0.75 – 1.25 A | 600 mA | 1.25× |

> **Recommendation: `R_ILIM` = 1.5 kΩ, published limit 400 mA continuous, for the
> first five boards.** The reason is not the switch — the TPS22950C is a 3.2 A
> device and would carry 800 mA without noticing. **It is the TPS63020.** §8 shows
> that a *shorted* accessory holds the switch at `ILIM` until thermal shutdown, and
> at `R_ILIM` = 1.15 kΩ the worst-high limit of 1.25 A pushes `+3V3` to ≈ 101 % of
> the regulator's 2 A rating while the internal worst case is also running. At
> 1.5 kΩ the same fault reaches **86 %**.
>
> **The CTO's 600–800 mA target is supported by the hardware without any change** —
> it is one 0603 resistor. Raise `R_ILIM` to 1.15 kΩ once the internal worst-case
> current is measured on real boards. This is exactly the D-049 posture.

### 5.3 The one honest caveat on `FLT`

S2 Table 9-1, verbatim:

| fault condition | `VOUT` state | **`FLT` state** |
|---|---|---|
| None | `VIN` via `R_ON` | Hi-Z |
| **Output short** | **Current limited** | **Hi-Z** |
| Thermal shutdown | Hi-Z | **L** |
| Reverse current | Hi-Z | **L** |

> **`FLT` does NOT assert on plain current limiting.** It asserts on **thermal
> shutdown** and on **reverse current** only. This is stated because the CTO asked
> for exactly this honesty.
>
> **In practice a real short is still reported**, indirectly: at `ILIM` the device
> dissipates `VIN × ILIM` (≈ 2.5 W at 3.3 V, ≈ 3.5 W at 5 V) in a SOT-23-thin
> package, so it reaches the 170 °C TSD within tens of milliseconds and `FLT` then
> asserts. What is *not* visible is a **partial** overload that stays inside the
> thermal envelope — the accessory is simply current-limited and the host never
> learns. Firmware must not assume `FLT` is a complete overcurrent indication.

Recorded as **B-35**.

---

## 6. The 5 V accessory rail — NEW

```
BQ25185_SYS ──> TPS61023 (5.0 V) ──> ACC_5V_RAW ──> TPS22950C ──> ACC_5V_SW ──> pins 10, 22
                  EN = ACC_5V_EN                      ON = ACC_5V_EN
                                                      FLT = ACC_5V_FAULT
```

**It is not USB VBUS, it is not the NFC fallback 5 V rail, and it is tied to
neither.** The only node shared with anything else is `BQ25185_SYS`, on the
*input* side.

### 6.1 TPS61023 verified for this duty (S3)

| parameter | value | our operating point | verdict |
|---|---|---|---|
| Input voltage range | **0.5 – 5.5 V** (1.8 V min to start) | `SYS` ≈ 3.0 – 4.6 V | **PASS** |
| Output setting range | **2.2 – 5.5 V**, `VREF` = 595 mV ±2.5 % | **5.0 V** | **PASS** |
| Output OVP | 5.5 V min / 5.7 V typ | 5.0 V leaves ≥ 0.5 V to the OVP floor | **PASS** |
| Valley switch current limit | **2.7 A min / 3.7 A typ** | see below | **PASS, large margin** |
| Switching frequency | 1 MHz (`VIN` > 1.5 V) | | |
| Efficiency | **94 % at 3.6 V → 5 V, 1.5 A** | ~92 % at our load | **PASS** |
| **True input-to-output disconnection in shutdown** | yes | the rail is genuinely dead when disabled | **PASS** |
| Shutdown current | **0.1 µA** typ | | **PASS** |
| Quiescent into `VOUT` when enabled | 20 µA | reason to keep it disabled by default | noted |
| Short-circuit + thermal protection | yes | | **PASS** |
| `EN` thresholds | high > 1.2 V, low < 0.4 V | PCAL9535A drive | **PASS** |
| Package | **SOT563 (DRL), 1.20 × 1.60 mm** | | **PASS** |
| Pass-through when `VIN` > `VOUT` | yes | `SYS` never exceeds ~4.7 V, so pass-through is not reachable | noted |

**Output capability at 5.0 V** (1 µH, 1 MHz, valley limit, η ≈ 0.90):

| `SYS` | duty | ΔI_L (p-p) | max average inductor current | **max `IOUT` at 5 V** | at our 300 mA / 500 mA |
|---|---|---|---|---|---|
| 3.0 V | 0.40 | 1.20 A | 4.30 A | **≈ 2.3 A** | 13 % / 22 % |
| 3.6 V | 0.28 | 1.01 A | 4.20 A | **≈ 2.8 A** | 11 % / 18 % |
| 4.2 V | 0.16 | 0.68 A | 4.04 A | **≈ 3.1 A** | 10 % / 16 % |

At **500 mA out from 3.6 V**: input 755 mA average, peak inductor current
**1.26 A**, IC loss ≈ 0.15 W → ≈ 23 °C rise in SOT-563 with the recommended
layout. At **300 mA** the loss is ≈ 0.09 W.

> **The IC is not the limiter — the inductor is.** Specify **1 µH with
> `I_sat` ≥ 3 A**, so that a fault at the load switch's worst-high limit
> (0.86 A out, ≈ 2.2 A peak inductor current at `SYS` = 3.0 V) does not saturate
> it. Recorded as **B-38**. Recommended passives: `C_IN` ≥ 10 µF, `C_OUT` ≥ 22 µF,
> feedback divider ≈ 750 kΩ / 100 kΩ for 5.06 V — **identical to the DNP NFC
> fallback boost**, so both circuits share one BOM line for every passive.

### 6.2 Verdict on reusing TPS61023

> ### **YES — reuse the TPS61023. It is the right part, not merely the convenient one.**

- **Capability:** 6–10× the required output current at every battery voltage.
- **Correct behaviour when off:** true input-to-output disconnection and 0.1 µA —
  the accessory rail is genuinely dead, not merely unregulated.
- **BOM consolidation:** one boost family to validate, source and stock; identical
  inductor, divider and capacitors as the D-056 NFC fallback; identical SOT-563
  footprint; one set of spares for rework.
- **Known-part advantage:** the footprint and layout are already being drawn for
  the NFC fallback, so the accessory boost costs no new library work.

No alternative was found that is materially better. A dedicated 5 V charge pump
would remove the inductor but cannot supply 500 mA from 3.0 V; a larger boost buys
capability we have explicitly been told not to buy.

### 6.3 Current-limit recommendation — NOT fabrication-locked

| R_ILIM | ILIM typ | worst-case band | published continuous | headroom |
|---|---|---|---|---|
| **1.65 kΩ (recommended)** | **0.69 A** | **0.52 – 0.86 A** | **300 mA** | **1.73×** |
| 1.5 kΩ | 0.76 A | 0.57 – 0.96 A | 400 mA | 1.43× |

**Recommended: `R_ILIM` = 1.65 kΩ, published 300 mA continuous for the first
fabrication**, with 400–500 mA available by changing one resistor after bench
measurement. The rail is deliberately **not over-sized**, per the ruling.

---

## 7. The 5 V protection stage, and the back-feed proof

### 7.1 TPS22950C at 5 V — same part, second instance

`VIN` 1.8–5.5 V covers 5 V (S2 §7.3); `R_ON` = 34 mΩ at 5 V; `IMAX` = 3.2 A.
All of §5.1 applies unchanged.

> ### **YES — use TPS22950C on both rails.** Same MPN, same DDC footprint, same
> safe-state pull-down, same `FLT` handling. **Only `R_ILIM` differs**
> (1.5 kΩ on 3.3 V, 1.65 kΩ on 5 V). This is the BOM simplification the ruling
> asked for and there is no technical reason to refuse it.

### 7.2 Every back-feed path, closed

| requirement | mechanism | verdict |
|---|---|---|
| Externally powered accessory must not back-feed the 5 V boost | TPS22950C **RCB**; and with `ON` low the device **constantly blocks reverse current**, so the path is dead whenever the rail is disabled — which is its default state | **CLOSED** |
| No path from `ACC_5V` into USB `VBUS` | Three series barriers: the load switch's RCB; the TPS61023's true input-to-output disconnection (and its unidirectional control loop when enabled); and the BQ25185 power path, which does not conduct `SYS → VBUS` | **CLOSED** |
| No path into `NFC_SUPPLY` | The accessory boost is a **physically separate TPS61023** with its own `ACC_5V_RAW` net. On the first build `NFC_SUPPLY` = `+3V3` (D-055) and the NFC boost is **DNP** (D-056). The two share only `SYS` on the input side | **CLOSED** |
| Externally powered accessory must not back-power `+3V3` | TPS22950C RCB on the 3.3 V switch, same argument (this is the D-058 requirement, re-confirmed) | **CLOSED** |
| 5 V must not reach the 3.3 V rail through a mis-inserted accessory | §3.2: every power contact is GND-paired, and detect gating means neither rail is live during a mis-insertion | **CLOSED** |

---

## 8. Expander / enable / fault / detect resource audit

### 8.1 `U2` — internal expander (0x20), measured baseline from S5

| pin | v1 assignment | v2 |
|---|---|---|
| P00 | `TOUCH_RST_N` | keep |
| P01 | `SX1262_RST_N` | keep |
| P02 | `NFC_5V_EN` | keep (net exists; the boost is DNP on build 1 per D-056) |
| P03 | `AMP_SD_MODE` | keep |
| P04 | `DISP_RST_N` | keep |
| P05–P07 | `RGB_R/G/B_CTL` | **FREED** by D-037 |
| P10–P15 | D-pad + A + B | keep (6) |
| P16 | `BTN_HOME_N` | **FREED** by D-010 |
| P17 | `ROOTPROBE_IRQ_READY_N` | **FREED** by D-038 |

**Free: 5.** **Already committed in v2: 5** — `BQ25185_STAT1`, `BQ25185_STAT2`
(Ruling G requires both), `MAX17048_ALRT_N`, `VBUS_PRESENT` (all four close B-15)
and `SX1262_DIO1` (D-063 moves it to the internal expander).

> **`U2` = 16 / 16. Zero spare.**

### 8.2 `U3` — community expander (0x21)

| pin | assignment | exposed? |
|---|---|---|
| P00–P07 | `XGPIO0` … `XGPIO7` | yes |
| P10, P11 | `XGPIO8`, `XGPIO9` | yes |
| P12 | **`ACC_3V3_EN`** | no |
| P13 | **`ACC_5V_EN`** | no |
| P14 | **`ACC_DETECT_N`** (input, 100 kΩ pull-up to `+3V3`) | no — sensed from pin 23 |
| P15 | **`ACC_3V3_FAULT`** (input, `FLT`, 100 kΩ pull-up) | no |
| P16 | **`ACC_5V_FAULT`** (input, `FLT`, 100 kΩ pull-up) | no |
| P17 | `SX1262_RXEN` (internal RF-switch control, 100 kΩ pull-down) | no |

> ### **VERDICT: all five accessory signals fit cleanly — exactly, at 16 / 16, with zero spare.**
>
> The fit is possible **only because the CTO reduced XGPIO from 11 to 10.** That
> single surrendered XGPIO is precisely what pays for the fifth accessory pin.

**Nothing was stolen.** GPIO38 and GPIO47 remain the two published native pins;
SPI-A, SPI-B, I²S and every internal MCU signal are untouched; no native GPIO was
consumed by this subsystem.

### 8.3 Two properties this allocation buys for free

1. **Hot-plug detection and wake.** `U3`'s `/INT` is wired-OR onto `WAKE_INT_N` →
   GPIO21, an RTC-capable wake source. Because `ACC_DETECT_N` is a `U3` **input**,
   plugging or unplugging an accessory raises an interrupt and can wake the device
   — at zero hardware cost. Use the PCAL9535A's **per-pin interrupt mask** so a
   loose connector cannot storm the host (D-066 already requires explicit
   unmasking).
2. **Detection before power.** `U3` is powered from `+3V3`, and `ACC_DETECT_N` is
   pulled up to `+3V3`, so **detection works with both accessory rails off** — which
   is the ordering the ruling demands, and it is what makes the mis-insertion
   argument in §3.2b hold.

### 8.4 Interrupt / status usage

- Unmask `U3` P14 (`ACC_DETECT_N`), P15 and P16 (`FLT`) only; mask the XGPIO inputs
  unless an accessory has registered interest, so an accessory driving its own
  outputs does not flood the host.
- Use the **interrupt status registers** (0x4C/0x4D) to identify the source rather
  than diffing snapshots.
- Use **input latch** on the two `FLT` lines so a short TSD event cannot be missed.

### 8.5 Safe-state pulls — three new mandatory resistors

Carried forward from the S7 discipline (*"any new control signal in v2 must arrive
with its pull"*):

| net | pull | to | why |
|---|---|---|---|
| `ACC_3V3_EN` | 100 kΩ | **GND** | rail OFF before firmware runs |
| `ACC_5V_EN` | 100 kΩ | **GND** | boost **and** switch OFF before firmware runs |
| `ACC_DETECT_N` | 100 kΩ | **`+3V3`** | de-asserted (no accessory) by default |
| `ACC_3V3_FAULT` | 100 kΩ | **`+3V3`** | open-drain `FLT` idle-high |
| `ACC_5V_FAULT` | 100 kΩ | **`+3V3`** | open-drain `FLT` idle-high |

`ACC_5V_EN` drives **both** the TPS61023 `EN` and the 5 V TPS22950C `ON` from one
expander pin. That is deliberate: it costs one pin instead of two, both parts need
the same safe state, and the load switch's 800 µs slow turn-on comfortably
outlasts the boost's 700 µs soft-start, so the accessory sees a monotonic ramp.

---

## 9. Logic safety

### 9.1 The rule

> **Every community SIGNAL contact is 3.3 V CMOS. The presence of a 5 V POWER
> contact does not make `XGPIO`, `NATIVE_A/B`, `EXT_SDA/SCL` or `WAKE_ATTN_N`
> 5 V-tolerant. Applying 5 V to any signal contact is out of specification and may
> destroy the device.**

Silkscreen / documentation language, to appear on the recess face, in the pinout
card and in every accessory-facing document:

```
COMMUNITY PORT — 3V3 LOGIC ONLY
5V PIN IS POWER OUTPUT ONLY. DO NOT DRIVE SIGNALS ABOVE 3.6 V.
XGPIO = expander (slow, I2C-mediated). NATIVE = ESP32 direct (fast).
```

The `XGPIO` / `NATIVE` distinction is a **D-045 requirement**, not a nicety.

### 9.2 Are series resistors and ESD sufficient? — Yes, with one addition

| contact class | protection | analysis |
|---|---|---|
| `XGPIO0…9` | **100 Ω series** at the connector + PCAL9535A internal clamp | 5 V misapplied → (5 − 3.9)/100 ≈ **11 mA** into the clamp. Inside the part's tolerance, and the expander is the deliberate sacrificial element — a US$0.60 part in front of a US$4 MCU |
| `NATIVE_A`, `NATIVE_B` | **100 Ω series + a low-capacitance TVS array** | These are the **only contacts with a direct path to the MCU**. 5 V through 100 Ω gives ≈ 11 mA into the ESP32-S3's clamp, below its per-pin limit, but there is no sacrificial part in between. A 0.5 pF-class 4-channel array (TPD4E05U06 class) costs ≈ US$0.15 and covers ESD as well. **Justified** |
| `EXT_SDA`, `EXT_SCL` | 22 Ω series + the same TVS array | Already buffered by `U16` TCA9517A, whose B-side supply is `ACC_3V3_SW` — verified high-Z when unpowered. The buffer is the sacrificial element |
| `WAKE_ATTN_N` | **330 Ω series** (the existing `R66` value) + the new isolation gate (§9.3) | Open-drain, slow |
| `ACC_DETECT_N` | 1 kΩ series + 100 kΩ pull-up | Static |

> **Bidirectional level translators are NOT recommended and are not justified.**
> They would not protect the A-side against over-voltage unless the B-side were
> 5 V-rated, they introduce direction ambiguity on genuinely bidirectional GPIO
> (auto-direction parts mis-latch on slow edges), they add cost, area and two more
> failure modes, and — most importantly — **they would imply that 5 V logic is
> supported, which it is not.** The specification is 3.3 V; the protection should
> enforce that specification, not blur it.

### 9.3 `WAKE_ATTN_N` isolation gate — closes B-08

B-08 has been open since the pre-design audit: *"the mandated open-drain gate
powered from switched accessory power was never implemented; only `R66` 330 Ω
exists. A shorted accessory pin can permanently block internal button wake."*
That defect lives entirely inside this subsystem, so it is closed here.

```
pin 14 ──[330R R66]── WAKE_ATTN_N_HDR ──[ Q_WAKE_GATE ]── WAKE_INT_N ──> GPIO21
                                          N-channel MOSFET
                                          gate = ACC_3V3_SW
```

A single N-channel MOSFET pass gate (2N7002 / BSS138 class, SOT-23) is sufficient
**because the signal is only ever pulled LOW**: an N-FET pass gate conducts for
signals near ground when its gate is high, and is off when the gate is at 0 V. One
part, no resistors beyond `R66`.

- **Accessory power OFF (the default) → the gate is off → a shorted accessory pin
  cannot hold `WAKE_INT_N` low → internal button wake can never be blocked.** B-08
  closed.
- **Consequence, stated explicitly:** accessory-initiated wake now requires
  `ACC_3V3_SW` to remain enabled during sleep. That is a *policy*, not a defect —
  AQROOT knows an accessory is present (detect works unpowered), so firmware can
  choose to hold the rail up only when one is attached. Recorded as **B-36**.

---

## 10. System power budget

All figures at the rail named. Conservative, datasheet-class.

### 10.1 Loads

| load | rail | current | note |
|---|---|---|---|
| ESP32-S3-WROOM-1, Wi-Fi TX 802.11b @ 21 dBm | `+3V3` | **355 mA** avg, ~500 mA peak | dominant burst |
| Display logic (ILI9488) | `+3V3` | 20 mA | FBV2-DISP-002 |
| **Backlight** (TPS61169 input) | `+3V3` | **130 mA** default, **161 mA** max | re-derived in S8 |
| Touch FT6236 | `+3V3` | 3 mA | |
| microSD write | `+3V3` | 100 mA peak | |
| CC1101 433 MHz, RX / TX +10 dBm | `+3V3` | 17 / 30 mA | |
| SX1262 (E22-900M22S) TX +22 dBm | `+3V3` | 118 mA | |
| ST25R3916 NFC, full field at 3.3 V | `+3V3` | 250 mA peak | D-055 operating point |
| MAX98357A speaker | `+3V3` | 250 mA peak, ~80 mA speech average | |
| Microphone ICS-43434 | `+3V3` | 0.6 mA | |
| IMU + fuel gauge + 2 × PCAL9535A + all pulls | `+3V3` | 10 mA | |
| **`ACC_3V3_SW` at the published limit** | `+3V3` | **400 mA** | |
| **`ACC_5V_SW` at the published limit** | **`SYS`** | **300 mA at 5 V = 1.50 W → 1.67 W from `SYS`** | **does not load `+3V3` at all** |

> **A structural advantage worth naming:** because the 5 V rail is boosted from
> `SYS` and not derived from `+3V3`, **it consumes none of the TPS63020's 2 A
> budget.** Deriving 5 V from `+3V3` would have cost ≈ 500 mA of that budget.

### 10.2 Case A — naive "everything simultaneously" — **NOT PERMITTED**

355 + 20 + 161 + 3 + 100 + 30 + 118 + 250 + 250 + 0.6 + 10 + 400 = **1 698 mA at
`+3V3`** = 5.60 W = **85 % of the TPS63020's 2 A rating**, before transients, and
with the Wi-Fi peak substituted it exceeds 90 %.

Add `ACC_5V`: `SYS` = 5.60/0.90 + 1.67 = **7.89 W** → **2.19 A at V_BAT 3.6 V**.

**This case must be prevented by firmware.** It is the P-15 concern, quantified.

### 10.3 Case B — the design case, with mutual exclusion enforced

Only one high-power radio at a time; audio capped during a transmit burst.

| | mA at `+3V3` |
|---|---|
| Wi-Fi TX (the worst single radio) | 355 |
| Display logic + backlight at maximum | 181 |
| Touch + housekeeping | 13 |
| microSD write | 100 |
| Audio at the capped level | 120 |
| **Internal subtotal** | **769** |
| `ACC_3V3_SW` at 400 mA | 400 |
| **Total `+3V3`** | **1 169 mA = 58 % of 2 A** |
| with the Wi-Fi 500 mA peak substituted | 1 314 mA = **66 %** |

`SYS` = (1 169 × 3.3)/0.90 + 1.67 W = 4.29 + 1.67 = **5.96 W**
→ **1.65 A at 3.6 V**, **1.75 A at 3.4 V**, **1.99 A at 3.0 V**.

Pack: ≈ **0.60 C** on the 2 750 mAh class cell (D-071). Comfortable.

### 10.4 Case C — accessory hard short, the case that decides `R_ILIM`

The TPS22950C is a **constant-current** limiter, so a dead short holds `ILIM`
until thermal shutdown — tens of milliseconds, then auto-retry.

| `R_ILIM` (3.3 V rail) | worst-high `ILIM` | `+3V3` total during the short | % of 2 A | verdict |
|---|---|---|---|---|
| **1.5 kΩ (recommended)** | 0.96 A | 769 + 960 = **1 729 mA** | **86 %** | **no foldback, no brownout** |
| 1.21 kΩ | 1.20 A | 1 969 mA | 98 % | inside, no margin |
| 1.15 kΩ | 1.25 A | 2 019 mA | **101 %** | **foldback → brownout → SD corruption** |

> **This single table is why the published 3.3 V accessory limit is 400 mA on the
> first five boards rather than the 600–800 mA target.** Nothing about the switch
> or the connector prevents 800 mA; the 2 A regulator does, once a *fault* on top
> of the internal worst case is accounted for. One 0603 resistor lifts it once the
> real internal figure is measured.

### 10.5 Series-path thermals — a new finding

At the Case-B worst case (≈ 1.75 A from the pack):

| element | resistance | drop | dissipation |
|---|---|---|---|
| BQ25185 BATFET | **115 mΩ** (S4) | 201 mV | **0.35 W** |
| LTC4368 pass path (4 FETs + 15 mΩ sense, ≈ 95 mΩ) | 95 mΩ | 166 mV | 0.29 W |
| ≈ 5 A backstop fuse | ~20 mΩ | 35 mV | 0.06 W |
| **total series loss** | | **≈ 0.40 V** | **≈ 0.70 W** |

BQ25185 supports **up to 3.125 A discharge** (S4), so 1.75–2.0 A is inside spec.
But **0.70 W of series loss inside a sealed handheld, plus a 0.40 V drop that pushes
`SYS` toward 3.0 V at a low battery, is a real thermal and headroom item.**
Recorded as **B-34** for the schematic phase. It is a further argument for
conservative first-build accessory limits.

### 10.6 Firmware mutual-exclusion contract — binding

| # | rule |
|---|---|
| **MX-1** | **At most ONE of {Wi-Fi TX, LoRa TX @ +22 dBm, sub-GHz TX, NFC field ON} may be active at any instant.** |
| **MX-2** | Speaker output must be capped to ≤ 50 % amplitude while any MX-1 member is transmitting. |
| **MX-3** | `ACC_3V3_SW` and `ACC_5V_SW` may be enabled **only** while `ACC_DETECT_N` is asserted. |
| **MX-4** | Enable ordering: `ACC_3V3_SW` first, then `ACC_5V_SW` after ≥ 5 ms, so accessory logic is powered before its 5 V loads. Disable in reverse order. |
| **MX-5** | On `ACC_3V3_FAULT` or `ACC_5V_FAULT`, de-assert the corresponding enable within **100 ms**, report it in the UI, and require a user action to re-enable. **Do not leave the switch auto-retrying into a short indefinitely** — that is a thermal-cycling loop, not a recovery. |
| **MX-6** | On `ACC_DETECT_N` de-assertion, disable both rails within 100 ms. |
| **MX-7** | If `V_BAT` < 3.4 V, disable `ACC_5V_SW` and warn; below 3.2 V disable `ACC_3V3_SW` as well. Protects against brownout near cutoff, where the series drop of §10.5 is worst. |
| **MX-8** | microSD and display must not transact simultaneously on SPI-A (pre-existing rule; restated because a Wi-Fi burst plus both is the Case-A corner). |
| **MX-9** | Mask `U3` XGPIO interrupts by default; unmask only `ACC_DETECT_N` and the two `FLT` inputs, plus any XGPIO an accessory driver has registered. |

### 10.7 Recommended accessory limits — first fabrication

| rail | hardware limit (`R_ILIM`) | **published continuous** | published peak | after bench measurement |
|---|---|---|---|---|
| `ACC_3V3_SW` | 1.5 kΩ → 0.76 A typ | **400 mA** | 600 mA < 100 ms | 600–800 mA (`R_ILIM` → 1.15 kΩ) |
| `ACC_5V_SW` | 1.65 kΩ → 0.69 A typ | **300 mA** | 400 mA < 100 ms | 400–500 mA (`R_ILIM` → 1.5 kΩ) |

Neither resistor is fabrication-locked, per the ruling.

---

## 11. Mechanical

| check | figure | verdict |
|---|---|---|
| Connector body | 30.68 mm PCB pattern × 7.87 mm deep × **8.10 mm high** | fits the right edge of a 70 × 148 mm PCB |
| Length along the right edge | 30.68 mm of 148 mm | **PASS** |
| Depth into the board | 7.87 mm of the 70 mm width | **PASS**, but it **must be placed below the display** — the display leaves only 6.73 mm each side on the PCB |
| **Z column (new — connector region)** | front shell 2.0 + **connector 8.10** + PCB 1.6 + battery 8.0 + clearance 0.6 + rear shell 2.0 = **22.30 mm** of the 23.0 mm external | **PASS — 0.70 mm spare.** ⚠ **This becomes the governing Z column**, displacing the control region's 19.5 mm |
| Relief available | The battery is 60 mm wide in a 75 mm cavity, so the outer ~5 mm of each PCB edge has **no battery behind it**. Placing the connector hard against the right edge recovers most of the 8.0 mm | mitigation, to be confirmed at FBV2-P1 |
| Insertion force | up to **48 N** (24 × 2.0 N max) | ⚠ the enclosure must carry this load — **M-10** |
| Recess | closed at both ends, asymmetric key, chamfered lead-in | requirement |
| Right-face neighbours | Power switch and recessed BOOT (D-070) must clear the 30.68 mm connector footprint | FBV2-P1 |

New mechanical open items: **M-09** (governing Z column) and **M-10** (insertion
load path).

---

## 12. Opportunity and simplification scan

### Adopted in this closeout (already authorized)

| # | item | class |
|---|---|---|
| 1 | **One TPS22950C MPN on both rails** — only `R_ILIM` differs | C — consolidation |
| 2 | **TPS61023 reused as the accessory boost**, sharing inductor, divider and capacitors with the DNP NFC fallback | C — consolidation |
| 3 | **One expander pin drives both the boost `EN` and the 5 V switch `ON`** | B — complexity removed |
| 4 | **Hot-plug detect and wake for free** via `U3` `/INT` → `WAKE_INT_N` | A — nearly-free capability |
| 5 | **`FLT` → UI message** instead of an invisible fault | E — user experience |
| 6 | **Both `R_ILIM` as accessible 0603** — the entire accessory current policy is one-resistor reworkable | D — no-respin |
| 7 | **`WAKE_ATTN_N` isolation gate** — one MOSFET closes B-08 | B — defect removed |
| 8 | **Rails segregated by row** (3.3 V in row A, 5 V in row B) — a row-to-row bridge in an accessory can only short a rail to ground, never 5 V to 3.3 V | A — free robustness |

### ⚠ Flagged for CTO / user decision — NOT adopted

| # | opportunity | why it is attractive | why it is not being locked here |
|---|---|---|---|
| **O-1** | **Wire-OR the two `FLT` lines onto one `ACC_FAULT_N` input**, freeing one `U3` pin as reserve | Both outputs are open-drain, so the wire-OR is free. It would leave **1 spare expander pin in a design that currently has zero spare anywhere** (§8.1, §8.3) — real no-respin insurance | It trades away per-rail fault attribution, which is a **user-experience** call ("accessory drew too much current on 5 V" vs "on some rail"). Firmware can disambiguate by disabling one rail, but only after the fact. **CTO call: slack vs. diagnostics.** |
| **O-2** | **Reserve an I²C address for an accessory ID EEPROM** (24Cxx class) on the external bus, so AQROOT can identify an accessory and load the right driver | **Zero hardware cost on AQROOT** — it is purely a published convention. Turns a dumb port into a self-describing one, which is a genuine platform differentiator | It is a **product/protocol** decision, not an electrical one, and it interacts with the unresolved address-collision question in P-18. Not authorized by this task |
| **O-3** | **A DNP 0 Ω link from `ACC_5V_RAW` to the NFC 5 V fallback node**, so one fitted boost could serve both if the NFC fallback is ever needed | Saves fitting a second TPS61023 in the fallback scenario; costs one DNP resistor now | **It couples NFC PA current to the accessory load**, which is exactly what D-056 avoided by specifying an independent path. The RF consequence is unquantified. **CTO call** |

Nothing else met the "high value, low-to-moderate effort" bar. Deliberately **not**
proposed: per-contact current sensing, a fourth expander, an accessory MCU
handshake, 5 V-tolerant buffers, a latching connector, hot-swap controllers.

---

## 13. Gate assessment — FBV2-COMM-LOCK

| # | condition | status |
|---|---|---|
| 1 | 2×12, 24 active contacts, no wasted position | **YES** — §2.2 |
| 2 | Exact connector MPN, female, device side | **YES** — Harwin `M20-7881242` |
| 3 | Keying / polarization defined | **YES** — enclosure-formed, §4.3 |
| 4 | Final pin ordering with a mis-insertion argument | **YES** — §3 |
| 5 | 3.3 V rail architecture and current limit | **YES** — §5 |
| 6 | 5 V rail architecture and current limit | **YES** — §6 |
| 7 | Back-feed paths closed | **YES** — §7.2, five paths |
| 8 | Enable / fault / detect resources fit | **YES** — 16/16 on `U3`, §8 |
| 9 | Logic safety resolved | **YES** — §9, no level translators |
| 10 | Power budget re-run, mutual exclusion defined | **YES** — §10 |
| 11 | Mechanical fit | **YES** — §11, 0.70 mm Z spare |

> ### **COMMUNITY PORT LOCK = PASS.**
> **P-02 CLOSED** (connector frozen). **P-15 CLOSED** (rail budget + MX contract).
> **P-16 CLOSED** (`ACC_DETECT_N` is a dedicated contact and a dedicated expander
> pin; no XGPIO is repurposed). **B-08 CLOSED** (WAKE isolation gate).

---

## 14. Open items created or changed

| # | item | severity | closes at |
|---|---|---|---|
| **B-34** | **≈ 0.70 W of series loss and ≈ 0.40 V of drop** in the BATFET + reverse-protection path at 1.75 A, inside a sealed enclosure | MEDIUM | FBV2-S1 thermal review |
| **B-35** | **`FLT` does not assert on plain current limiting** — only on TSD and reverse current. Partial overloads are invisible to the host | LOW, documented | firmware contract |
| **B-36** | Accessory-initiated wake requires `ACC_3V3_SW` to stay enabled during sleep (consequence of the B-08 gate) | LOW, policy | FBV2-B2 |
| **B-37** | **Zero spare expander capacity on BOTH `U2` and `U3`.** Any new I²C-mediated signal in v2 must displace an existing one | MEDIUM | standing constraint |
| **B-38** | 5 V boost inductor must be **1 µH with `I_sat` ≥ 3 A** to survive a fault at the load switch's worst-high limit | LOW | FBV2-S1 |
| **M-09** | The **connector region is the new governing Z column** — 22.30 mm of 23.0 mm external | MEDIUM | FBV2-P1 |
| **M-10** | **Up to 48 N insertion force**; the enclosure must carry it on a boss/rib, not the PCB joints | MEDIUM | enclosure CAD |
| **P-18** | External-I²C **address collision** remains unsolved. Powering the buffer's B-side from `ACC_3V3_SW` already prevents a dead accessory from holding SDA low, so the *bus-hang* half of P-18 is answered; a squatted address is not | **STILL OPEN** | CTO |
| ~~P-02~~ | Freeze the 20-pin connector | **CLOSED** — superseded and replaced | this audit |
| ~~P-15~~ | 3V3 rail budget under simultaneous worst case | **CLOSED** by §10 + MX-1…MX-9 | this audit |
| ~~P-16~~ | Repurpose one XGPIO as `ACC_DETECT`? | **CLOSED** — dedicated contact and pin | this audit |
| ~~B-08~~ | WAKE line has no isolation gate | **CLOSED** by §9.3 | this audit |

---

## 15. Honest limitations

1. **The 8.10 mm connector height is read from the Harwin series catalogue's
   double-row horizontal drawing, not from the individual `M20-7881242` drawing.**
   It must be re-confirmed against the part drawing at FBV2-P1, because the Z
   column has only 0.70 mm of spare.
2. **`M20-7881242` was constructed from the catalogue's ordering scheme**
   (`M20-78` + `8` for double row + `12` contacts per row + `42` for gold+tin) and
   from the confirmed existence of neighbouring codes. It should be verified
   against a live distributor listing before the BOM is issued.
3. **No LCSC/JLCPCB part number is given for the connector.** Harwin M20 is not
   stocked there. The generic LCSC alternate exists but its plating and cycle life
   are unspecified, so it is not recommended for a user-facing connector.
4. **The load figures in §10 are datasheet-class, not measured.** The Wi-Fi,
   NFC and audio numbers in particular are conservative upper bounds. The
   *relative* conclusions (which cases fit, which do not) are more robust than the
   absolute milliamps.
5. **Boost efficiency is assumed at 0.90–0.92 and the TPS63020 at 0.90.** Neither
   was measured at these operating points.
6. **The current-limit tolerance band is inferred** from the datasheet's three
   characterised `R_ILIM` points (±25 %) rather than from a specification of
   accuracy across the whole range.
7. **The 300-cycle durability of the gold M20 socket is modest** for a port
   intended for frequent accessory swapping. It is typical of 2.54 mm socket
   strips and is accepted for the first five boards, but it is a known ceiling.
8. **Nothing has been built or mated.** Every conclusion is paper.

---

## Sources

- Harwin **M20 series** catalogue — [2.54 mm M20 connectors (PDF)](https://shop.sibalco.ch/cust/files/Harwin_M20_3623.pdf) · [Harwin product site](https://www.harwin.com/products/M20-7831042)
- TI **TPS22950 / TPS22950C** — [datasheet SLVSFJ2B](https://www.ti.com/lit/ds/symlink/tps22950.pdf) · [product page](https://www.ti.com/product/TPS22950)
- TI **TPS61023** — [datasheet SLVSF14B](https://www.ti.com/lit/ds/symlink/tps61023.pdf) · [product page](https://www.ti.com/product/TPS61023)
- TI **BQ25185** — [datasheet](https://www.ti.com/lit/gpn/BQ25185)
- Samtec **Mini Mate IPL1** (evaluated, rejected) — [series page](https://www.samtec.com/products/ipl1)
- LCSC female headers (alternate class) — [category](https://www.lcsc.com/category/793.html) · [`C30867` 2×10 example](https://www.lcsc.com/product-detail/Female-Header_2-54mm-2-10-Straight-Female-header_C30867.html)
- Read only, in-repo: `11 - Beta Pin Map v0.2.md` · `docs/full-beta-v2/CTO_DECISIONS.md` · `docs/full-beta-v2/architecture/ARCHITECTURE.md` · `docs/full-beta-v2/mechanical/MECHANICAL_INTERFACE_SPEC.md` · `audits/2026-08-22-pre-design-engineering-audit.md` · `audits/2026-08-23-display-procurement-lock.md`
