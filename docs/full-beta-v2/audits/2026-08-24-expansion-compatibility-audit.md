# FBV2-EXP-001 — Expansion ecosystem compatibility and pre-routing architecture audit

**Date:** 2026-08-24 · **Task:** FBV2-EXP-001 — audit / feasibility only
**Repository HEAD at start:** `24032a5` (FBV2-P2-000)
**Result: AUDIT = PASS.** Every question in the brief is answered from measurement or from a
manufacturer document. **The recommendation is CONDITIONAL and requires an owner ruling.**
**No percentage change. Overall Full Beta v2 stays 74 %.**

> **NO AUTHORITATIVE HARDWARE WAS CHANGED.** `J5` unchanged, schematic connectivity unchanged,
> PCB byte-identical (blob `22c03150…`, equal to `HEAD`), no Qwiic added, `BOOT` and `POWER`
> not moved, no PM part moved, outline unchanged, zero tracks.

Proposal document: [`../architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md`](../architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md).

---

## 1. Headline

The product intent is achievable and the electronics need no architectural change — **but the
interface does not fit the current floorplan, and the shortfall is paid in battery width.**

> **Measured requirement: (board right edge − battery right edge) ≥ 7.83 mm.
> Today it is 4.00 mm. Shortfall 3.83 mm.**

That single number governs the whole audit, so it is derived first.

---

## 2. Why a right-angle 24-way socket cannot cross the battery band

A right-angle through-hole socket's **solder tails sit inboard of its own mating face**. From the
Sullins 1-row right-angle female drawing (`xPxCxx1LGBN-RC`, drawing 10493): overall body
**8.50 ± 0.15 mm**, body width 2.58 mm, tail 3.15 mm below the board, recommended hole
**Ø1.02 mm at 2.54 mm**, and a tail-row-to-mating-face depth of **≈ 6.5–6.9 mm**. That depth is not
a vendor quirk — the socket must swallow a 6 mm male pin (Samtec states insertion depth
**3.68 … 6.35 mm**), so no 2.54 mm right-angle socket that accepts a standard post can be much
shallower.

Constraints on the tail-row X coordinate:

| constraint | expression | value |
|---|---|---|
| Tails must clear the battery envelope (`BATTERY_SHADOW` X 6.00 … 66.00 forbids **any** through-hole lead) | `t ≥ 66.0 + 0.5 clearance + 0.8 pad radius` | **t ≥ 67.30** |
| Mating face must reach the wall, i.e. sit at or inboard of the board edge | `t + 6.53 ≤ 70.0` | **t ≤ 63.47** |

**Contradiction: 3.83 mm.** Tested variants:

| scenario | tail-row window | verdict |
|---|---|---|
| Current 70 mm board, face flush with the edge | [67.30 … 63.47] | **SHORT by 3.83 mm** |
| Current board, face overhangs into the 2.5 mm wall gap | [67.30 … 65.47] | **SHORT by 1.83 mm** |
| Board grown to the documented max 72 mm, battery unchanged | [67.30 … 66.47] | **SHORT by 0.83 mm** |
| Board 70 mm, **battery 60 → 56 mm** | [63.30 … 63.47] | **FITS** |
| **Board 72 mm + battery 60 → 57 mm** | margin **+1.17 mm** | **FITS — recommended** |
| Board 72 mm, hypothetical 5.00 mm-deep socket | [67.30 … 68.00] | fits, but **no such socket exists** for a 6 mm post |

**The right wall ABOVE the battery**, where the lead restriction does not apply, offers
**Y 98.5 … 139.5 = 41.00 mm** (bounded below by the battery and above by the `U6` IR-receiver
optical corner). Body lengths: 1×12 = 30.99, **1×15 = 38.61 (largest that fits)**, 1×16 = 41.15,
1×24 = **61.47**. Even a 1×15 would leave nothing for the Qwiic connector or the power switch.

**Every other edge was tested and rejected:** the **left** wall is `ANT433_REGION` (Y 1.5 … 48.5)
and the mandatory `COAX_915_CHANNEL` (Y 24 … 110); the **bottom** edge is microSD, USB-C, both
radio modules, `J6`, `BOSS1` and the ESP32 antenna keepout; the **top** edge is the IR TX window,
the mandatory opaque barrier, the IR RX window and the SMA. Mounting the socket on the **rear**
face moves the conflict from its leads to its body and gains nothing.

---

## 3. Right-wall occupancy, measured

Front-face parts claiming the wall column (x ≥ 60.3), doc Y ascending:

| ref | Y range | note |
|---|---|---|
| `SW2` right control button | 45.56 … 52.44 | front-actuated, stays |
| `SW9` **POWER** | 64.95 … 75.05 | 10.10 mm |
| `SW1` **BOOT** | 78.91 … 89.09 | **SMD** (`SW_SPST_PTS645Sx43SMTR92`, 4 pads, 0 PTH) — easy to relocate |
| `F1` `U22` `C38` `C67` | 91.87 … 98.25 | SMD, relocatable inboard |
| `J4` battery connector | 98.66 … 104.25 | mates a cable, relocatable inboard |
| `J5` | 105.22 … 136.78 | 31.57 mm — the part being replaced |
| `C12` | 137.78 … 141.07 | SMD |
| `U6` IR RX | 141.60 … 147.09 | **fixed** — optical corner, D-229 |

**Free wall span between `SW2` and `U6` once `SW9`, `SW1`, `J4`, `F1`, `U22`, `C38`, `C67` and
`C12` are cleared: 89.16 mm.**

Required stack: 1×24 body **61.47** + Qwiic **6.00** + `SW9` **10.10** = **77.57 mm**, leaving
**11.59 mm** for three gaps and the recess ribs. It fits — *provided* the tail row can sit at
x ≈ 65, which is what §2 shows requires the battery change.

### 3.1 Answer to the brief's A–F question

| | question | answer |
|---|---|---|
| **A** | header + Qwiic + Power all fit on the right side | **NO** — not on the current floorplan |
| **B** | Power must move | **NO** — `SW9` stays on the right wall |
| **C** | BOOT must move | **YES** — to the bottom edge |
| **D** | display / `J1` must move | **NO** |
| **E** | PCB must grow | **YES — 70 → 72 mm in X**, which is the already-documented `FBV2_PCB_MAX_MM`; the 80 × 160 × 23 enclosure and the 75 × 155 cavity are **unchanged**. **And the battery must narrow 60 → 57 mm** |
| **F** | none of those are needed | **NO** |

---

## 4. Connector options, verified against manufacturer documents

### 4.1 Option A — one 1 × 24 right-angle female

**Baseline `SSQ-124-02-G-S-RA` (Samtec).** From the Samtec SSW/SSQ through-hole datasheet:
positions per row **01 thru 50**; row option **`-S` single row**; tail option **`-RA` right angle,
available with `-S`**; body length **N × 2.54 + 0.51 = 61.47 mm**; socket-axis height above the
PCB selectable by lead style (**−02 → 2.54 mm**, −03 → 7.62, −04 → 12.45); insertion depth
3.68 … 6.35 mm; mates **.025" (0.635 mm) square post**; **6.3 A per pin**; 465 VAC / 655 VDC;
−55 … +125 °C with gold; **100 mating cycles** at 10 µin Au; black LCP insulator.

**Samtec is the manufacturer of the current `J5`**, so lead time, small-quantity policy and account
are already known.

**Second source verified and deliberately NOT baselined:** Sullins **`PPTC241LGBN-RC`** / gold
`PPPC241LGBN-RC`. The family is confirmed active and the drawing is authoritative — it is the
source of the 6.53 mm depth figure this audit turns on. **But DigiKey lists the non-RC variant
obsolete at 0 stock, and the 19-way sibling `PPTC191LGBN-RC` is factory-order only: 1,000-piece
minimum, 11-week lead.** Under **D-096** that is a procurement risk. This is the third time the
programme has met a catalogue part that is not a stocked part — after the Harwin `M20-7881242`
(obsolete, D-093) and the Amphenol `095-902-568-100` (0 stock, 12-week lead, D-223) — and the
lesson is the same one.

### 4.2 Option B — two 1 × 12 right-angle females — **REJECTED, on geometry**

Both Samtec and Sullins build a 2.54 mm socket body **N × 2.54 + 0.51 mm long**, i.e. **1.525 mm of
insulator past the end contact at each end**. Two bodies butted therefore place their end contacts
**3.050 mm apart against a required 2.540 mm pitch — a 0.510 mm interference.**

> **Two 12-way sockets cannot form a continuous 24-position 2.54 mm grid.** They must be separated
> by at least one blank position.

Consequences: no single 24-pin accessory header can ever mate the pair; the pair needs
**2 × 30.99 + 5.08 = 67.06 mm**, which is **5.59 mm MORE wall length than the 1 × 24**; two parts,
two alignments, two recesses; and it creates a **new** hazard the 1 × 24 does not have — a 12-way
accessory can be plugged into the wrong group.

**Verdict: ONE 1 × 24. Not two 1 × 12.**

### 4.3 Option 0 — retain `BCS-112-S-D-HE`

2 × 12 PTH, 30.48 × 8.13 × 5.33 mm, 24 × Ø0.71 mm in a 27.94 × 7.87 mm field, ≈ 33 N average
insertion (M-10), 100 cycles formally qualified (2,500 by similarity, B-39), manual THT for the
first five. **Fits today with room to spare.** Its weakness is not electrical — it is that
**nothing in the maker world plugs into a 7.87 mm row-spaced Samtec pattern**, which is precisely
what the owner asked to fix.

### 4.4 Qwiic / STEMMA QT

**`JST SM04B-SRSS-TB(LF)(SN)`** — SH series, **1.0 mm pitch** (confirmed from JST's own `eSH.pdf`:
*"the world's first 1.0 mm pitch crimp style"*), 4 circuits, **side-entry** shrouded header, SMT,
body **A = 3.0 mm / B = 6.0 mm**, **1.0 A**, 50 V AC/DC, −25 … +85 °C, contact resistance 20 mΩ.
Machine-placeable. Pin order **1 GND (black) · 2 3.3 V (red) · 3 SDA (blue) · 4 SCL (yellow)** —
the ecosystem standard, verified against SparkFun's Qwiic definition, and identical for Adafruit
STEMMA QT.

**Rating check:** the 3.3 V pin can source up to `U20`'s ILIM ≈ 0.76 A into a 1.0 A connector on
28 AWG cable — inside rating, and a cable short is current-limited by the load switch.

---

## 5. Where Qwiic attaches — no new components at all

The external I²C segment is already buffered, pulled up, series-limited and clamped:

```
I2C_*_INT → U16 TCA4307 (VCC = ACC_3V3_SW) → EXT_*_BUF → R47/R48 22 Ω → EXT_SCL/EXT_SDA → D2 TVS → J5
                                              ↑ R49/R50 1.5 k to ACC_3V3_SW
```

**Attach at `EXT_SCL` / `EXT_SDA`** — downstream of the 22 Ω resistors, at `D2`'s clamp node, the
same node as the main header. The Qwiic port inherits the hot-swap buffer, the pull-ups, the series
resistance and the ESD clamp and **adds nothing**. Place `D2` between the two exits.

Tapping *upstream* (on `EXT_*_BUF`) was rejected: it would give the Qwiic port no series resistance
and no TVS. A *separate* 22 Ω pair per port was rejected: it adds two parts and puts 44 Ω in series
between the two external ports.

**Power = `ACC_3V3_SW`, and this is architectural, not preferential.** `U16`'s VCC is already
`ACC_3V3_SW` and the pull-ups pull to `ACC_3V3_SW`; powering Qwiic from unswitched `+3V3` would
create a powered-device / unpowered-bus state and invite back-feeding through the device's ESD
diodes. **`ACC_5V_SW` is never exposed on Qwiic.**

**Capacitance budget:** ≤ 200 pF at 400 kHz (1.5 kΩ; strict Fast-mode figure 236 pF for
`t_r` ≤ 300 ns). On-board copper ≈ 21 mm ≈ 21 pF; connector ≈ 1 pF; a 100 mm Qwiic cable ≈ 5–10 pF;
a typical breakout ≈ 10 pF. **Three daisy-chained boards ≈ 55–75 pF — comfortably inside.**
**No mux and no repeater is required. Do not add one.**

---

## 6. Software power control — traced pin by pin, and it already works

```
+3V3 → U20 TPS22950C  ON = ACC_3V3_EN ← U3.P15   (R98 100 k pull-down, default OFF)
                      ILIM = R97 1.5 k → ≈0.76 A typ ; FLT = pin 6 → ACC_3V3_SW
BQ25185_SYS → U21 TPS61023  EN = ACC_5V_BOOST_EN ← U3.P16  (R102 100 k pull-down)
            → ACC_5V_RAW → U22 TPS22950C  ON = ACC_5V_SW_EN ← U23.P04 (R131 100 k pull-down)
                                          ILIM = R101 1.65 k ; FLT → ACC_5V_SW
U20.6 ∥ U22.6 → ACC_POWER_FAULT_N (R103 100 k to +3V3) → U3.P18
J5 → R64 100 Ω → ACC_DETECT_N (R129 100 k to +3V3) → U3.P17          ← INPUT ONLY
```

> **`ACC_DETECT_N` reaches nothing but an expander input.** No AND gate, no interlock, no bypass
> exists between it and the three enables. **Detect gating is entirely firmware policy (MX-3).**

| requirement | verdict |
|---|---|
| Firmware can command **5 V OFF / ON**, no hardware bypass | **YES.** Two independent enables, both default OFF. **Permanent 5 V is physically impossible** |
| Firmware can command **3.3 V OFF / ON without DETECT** | **YES** |
| Manual / Bench mode — **hardware change required?** | **NO, for either rail. Firmware-only.** |
| Default OFF, ILIM, FLT, ≥ 10 ms boost settle (D-198) | **all retained, all in hardware** |
| New unsafe state | **none** — only the authority changes, from the detect contact to the user |
| Sleep / wake | unchanged. `ACC_3V3_SW` stays on during sleep (B-36); with the rail on and no accessory, `Q10`'s gate is held by `ACC_3V3_SW` and `R63` 10 k holds the contact high, so no spurious wake |
| Fault behaviour | unchanged. **B-35 carried forward: `FLT` does not assert on plain current limiting** — a partial overload stays invisible in every mode, and Bench mode makes it more likely to be met |

**Recommended DETECT policy:** NORMAL/SMART (default, DETECT required, automatic sequencing) and
MANUAL/BENCH (explicit per-rail opt-in, DETECT optional, **non-persistent** — reverts on power
cycle and on any `FLT` — with a "signal logic is 3.3 V only" warning). No protection is bypassed in
either mode.

---

## 7. Pin ordering

Three candidates were developed. Function inventory is fixed at 24: `ACC_5V_SW` ×2,
`ACC_3V3_SW` ×2, `GND` ×4, `EXT_SDA`, `EXT_SCL`, `NATIVE_A`, `NATIVE_B`, `WAKE_ATTN_N`,
`ACC_DETECT_N`, `XGPIO0`–`XGPIO9`.

| | ORDER-A **(recommended)** | ORDER-B | ORDER-C |
|---|---|---|---|
| Concept | power at both ends, I²C block at the top | all power in one block at the top | current order simply flattened to one row |
| I²C block `3V3/SDA/SCL/GND` | **pins 3-4-5-6 ✔** | pins 5-6-7-8 (two 3V3 first) | **split** — SCL at 2, SDA at 6 ✘ |
| 5 V position | **pins 1 and 24 — the two physical ends** | pins 2 and 3 | pins 10 and 22 |
| Any 5 V adjacent to a signal? | **NO** | no | **YES** — 5V(10)–N47(11) and 5V(22)–DET(23) |
| Power at the far end for long accessories | **yes** | no | yes |
| Schematic churn | pin re-map | pin re-map | **none** |

**ORDER-A, pin 1 at the top of the wall:**

```
 1 5V    2 G     3 3V3   4 SDA   5 SCL   6 G     7 N38   8 N47
 9 X0   10 X1   11 X2   12 X3   13 X4   14 G    15 X5   16 X6
17 X7   18 X8   19 X9   20 WAKE 21 DET  22 3V3  23 G    24 5V
```

**All 24 functions retained. Nothing added, removed or merged.**

**Mis-plug analysis — the reason ORDER-A wins.** Both 5 V contacts sit at the ends with `GND` as
their only inboard neighbour, so **no 5 V pin is adjacent to any signal**. The current order has two
such adjacencies. A one-position slip from either 5 V pin lands on `GND`: a current-limited short
(`U22` ILIM ≈ 0.69 A, reverse-current blocking, thermal shutdown, `FLT`), not 5 V into a 3.3 V
input. The two residual adjacencies are benign — `3V3(3)–SDA(4)` (SDA is pulled to that same rail
anyway) and `3V3(22)–DET(21)` (reads as "no accessory"). **Two existing hazards removed, none
created.**

---

## 8. Full-header misalignment — solved by the recess, not by software

A mating 1 × 24 male body is exactly **24 × 2.54 = 60.96 mm**. A recess with an internal length of
**62.5 mm** and **both ends closed** therefore allows **≈ 1.54 mm** of lateral play — **60 % of one
pitch**, so a one-position shift is **physically impossible**. Depth ≥ 1.5 mm below the outer wall;
moulded pin-1 triangle; **red band at both ends** over the 5 V contacts. Individual Dupont access is
unaffected because the recess opening is one continuous slot at socket-face height and each 2.54 mm
jumper housing enters its own aperture. **No proprietary shroud.**

Samtec's `"XXX" = Polarized` option (a plugged position) is available as belt-and-braces, but only
on a **25th non-functional position** (`SSQ-125-…`, body 64.01 mm) so no function is lost. **Not
recommended for build 1.**

---

## 9. BOOT relocation

`SW1` is **SMD** (`SW_SPST_PTS645Sx43SMTR92`), so relocation is trivial. Measured free bottom-edge
windows on the front face for Y 0 … 10, with the ESP32 antenna keepout (X 63.5 … 70) excluded:
**X 0.00 … 6.36 (6.36 mm)** and **X 21.64 … 32.68 (11.04 mm)**.

| option | verdict |
|---|---|
| **A — bottom edge, doc ≈ (27.0, 5.0)** | **RECOMMENDED.** The 11.04 mm window between the microSD shell and the USB-C receptacle takes the ~10.2 × 6.9 mm courtyard with 0.84 mm spare, clear of `R113` and `R35`. `U7` sits on the opposite face — a shielded can, electrically irrelevant to an SMD switch on the front. The enclosure's bottom wall has a **14 mm free span (X 22 … 36)** between the `USD_APERTURE` and the `USB_APERTURE`, so a **Ø2 mm recessed tool hole at X ≈ 27** sits 5 mm from each |
| **B — lower-left side** | **REJECTED ON RF.** The lower-left wall over Y 1.5 … 48.5 *is* `ANT433_REGION` — the flex is bonded **0.2 mm outboard of the board edge** — and Y 24 … 110 is the mandatory `COAX_915_CHANNEL`. A metal actuator plus a wall aperture would sit inside the 433 flex's near field and inside the reserved coax lane, and **P2-R1 already flags board copper in exactly that band as an aggressor into the antenna** |

BOOT remains recessed, tool-accessible, not a normal user control, usable on a blank or bricked
device, and independent of firmware. **Electrical behaviour unchanged.**

---

## 10. Multi-board, 0x50 and what does not change

**Multi-board** (details in the proposal §8): A generic-Dupont, B Qwiic daisy chain, and C one
Qwiic + one GPIO board are all **fully supported by ordinary community practice**. **D — two
official full-header accessories stacked directly — is NOT recommended**: a single row has no roll
stiffness for a second tier and both boards would share every line including both rails. The safe
standard is **one full-header accessory at a time**, with a second board on Qwiic or jumper wires.
**No AQROOT hub is required and none should be built.** Address collisions are not solved by any
connector.

**0x50 accessory ID: fine as an OPTIONAL single-accessory convention; needs a firmware convention;
no main-PCB change.** Some ordinary Qwiic devices *do* occupy 0x50–0x57 (24Cxx-class EEPROM
breakouts), so 0x50 must be a hint requiring a magic signature, never proof. Multiple smart
accessories or a daisy chain collide — that is inherent, not a defect. Widening the reservation is
a future accessory-standard revision alongside **P-19**, not a board change.

**Impact on the `J5` electronics: none.** `R51`–`R62` 100 Ω, `R64` 100 Ω, `R66` 330 Ω, `R47`/`R48`
22 Ω, `D2`–`D5` TVS, `U16` TCA4307 with `R49`/`R50`/`R17`/`R46`, `U20`, `U21`+`L4`, `U22`, the
`R103` FLT wire-OR and all decoupling are **identical**. **The schematic change is a footprint swap
plus a pin re-map on sheet 09 only** — no net created, deleted, split or merged — plus one 4-pin
Qwiic symbol landing on four nets that already exist.

---

## 11. Interaction with PM-1 / PM-2 / PM-3 / PT-1 — and the combined sequence

| item | interaction |
|---|---|
| **PM-1** converter inductors | **None.** All four are in the left margin. The battery narrowing frees a little rear area, which helps but is not needed |
| **PM-2** battery-protection block | **STRONG CONFLICT, and it is the reason to do this once.** PM-2's recommendation is to consolidate `U18`/`R75`/the trip dividers at the battery-entry corner with `J4`/`F1`/`Q2`/`Q3` — **the same right-hand region the 1 × 24 header now wants.** Deciding them separately guarantees a second round of placement churn |
| **PM-3** NFC front end | **None directly** (x 25 … 57, Y 100 … 125). Narrowing the battery to 57 mm moves its right edge to x ≈ 63 and frees rear area at x 63 … 70 over Y 23.5 … 98.5, which *helps* PM-2 |
| **PT-1** `U11` in the battery shadow | **Helped and must be done together.** Narrowing the battery does not by itself move `U11` out of the shadow; the combined re-floorplan should relocate it to the USB end, which is also where its `VBUS` comes from |
| **P2-R1** 433 aggressor band | **Unaffected** by the right-side change; still to be instantiated after PM-1 |
| **B-34** protection-path heat | Unchanged by this audit; PM-2 remains the lever |

**Routing impact of the connector change itself: neutral.** The current `J5` blocks all four layers
over a 27.94 × 7.87 mm PTH field with **11 inter-pad gaps × 2 tracks × 3 usable layers = 66
crossings**. A 1 × 24 row on Ø1.02 mm holes has 23 gaps of ≈ 0.89 mm, each taking one 0.2 mm track:
**23 × 1 × 3 = 69 crossings.** The 7.87 mm dead band disappears; the barrier becomes **twice as
long**. Net neutral for capacity, worse for anything that wants to cross the right-hand strip —
which is exactly PM-2's cluster.

### Recommended COMBINED re-floorplan order

1. **Owner ruling on E-1 … E-6** (proposal §14). Nothing below starts without it.
2. Fix the outline (70 → 72 mm) and every mechanical reservation — battery 57 mm, NFC circles,
   coax channel, ribs, the new right-wall recess, the BOOT aperture.
3. Place the right-wall expansion stack: **1 × 24 header → Qwiic → POWER**, top to bottom; `BOOT`
   to the bottom edge.
4. **PM-2** — consolidate the battery-protection block at the battery-entry corner, resolving its
   competition with the header **here, once**.
5. **PT-1** — `U11` out of the battery shadow, to the USB end.
6. **PM-1** — each converter's inductor and output capacitor to its own IC.
7. **PM-3** — NFC front end rebuilt as a mirrored pair about the `U9` → `J7` axis.
8. **P2-R1** — instantiate the 433 aggressor rule area once the left margin is settled.
9. Re-run `p1_regression` against the new outline; re-derive every P1 metric; **re-issue FBV2-P1 as
   a gate** (the outline change invalidates the current PASS).
10. Then, and only then, FBV2-P2 routing.

---

## 12. Recommendation matrix

Scored 0–5, higher is better.

| criterion | **0** BCS 2 × 12 | **1** one 1 × 24 + Qwiic | **2** two 1 × 12 + Qwiic |
|---|---|---|---|
| Community familiarity | 1 | **5** | 4 |
| Dupont compatibility | 1 | **5** | **5** |
| Full 24-function retention | **5** | **5** | **5** |
| Mechanical strength | **5** | 2 | 3 |
| Right-wall fit | **5** | 1 | 0 |
| Labeling | 2 | **5** | **5** |
| Misalignment safety | **5** | 4 | 3 |
| Procurement | 4 | 4 | **5** |
| Assembly | 3 | 3 | 2 |
| PCB impact | **5** | 2 | 1 |
| Enclosure impact | **5** | 3 | 2 |
| Future accessory friendliness | 2 | **5** | 3 |
| **Total** | **43** | **44** | **38** |

**RECOMMEND OPTION 1 — one 1 × 24 right-angle female plus one Qwiic connector — CONDITIONAL on
E-1 and E-2.**

The totals are close on purpose, and the reading matters: **Option 0 wins every criterion that
describes the board as it is today, and loses every criterion the owner actually asked for.**
Option 1's two weak scores are *fit* and *PCB impact*, and both are consumed by a re-floorplan that
**PM-1, PM-2, PM-3 and PT-1 already make unavoidable**. Doing the connector change at the same time
costs one outline change and 5 % of battery capacity; doing it later costs a second full placement
cycle.

**If the owner declines E-2 (the battery), Option 1 is not deliverable in this enclosure and
Option 0 stands unchanged.** Option 2 is rejected on geometry regardless.

---

## 13. Opportunity and simplification scan

| finding | |
|---|---|
| **One connector substitution that increases compatibility without losing pins** | **Found and recommended** — 24 functions retained exactly, presentation changed |
| **Existing protected I²C reused for Qwiic without another buffer** | **Found** — zero new components; `TCA4307`, pull-ups, 22 Ω and TVS all shared |
| **Firmware-only manual-power mode** | **Found and confirmed by tracing** — no hardware change for either rail |
| **Moving BOOT instead of compromising expansion layout** | **Found** — `SW1` is SMD; an 11.04 mm bottom-edge window exists with a 14 mm free enclosure span |
| **Familiar 2.54 mm hardware instead of a proprietary accessory connector** | **Found** — official accessories use an ordinary 2.54 mm male header |
| **Eliminating enclosure key complexity while keeping shift safety** | **Found** — the asymmetric upper-edge key (D-097) is no longer needed; **closed recess ends alone give 1.54 mm of play against a 2.54 mm pitch** |
| **Reducing manual parts rather than increasing them** | **Neutral, honestly** — the through-hole count stays 24 (one part instead of one part), and the Qwiic connector is **SMT and machine-placed**, so the manual-assembly list (`J5`, `D1`) does not grow |
| **Solving PM-1/2/3 in the same re-floorplan** | **Found and recommended** — §11 |
| Grove / mikroBUS / Arduino shield / Pi header / hub / mux | **None found necessary. None proposed.** |

---

## 14. Validation — authoritative hardware unchanged

| check | result |
|---|---|
| PCB blob hash vs `HEAD` | `22c03150c85dcc56fde4e47552c0f754803f0e59` = **identical** |
| Schematic connectivity | **unchanged** — no sheet opened |
| ERC | **27 violations, 0 errors** — identical |
| DRC | **26 violations, 499 unconnected** — identical |
| Tracks / signal vias / electrical pours | **0 / 0 / 0** |
| Board outline | **70.000 × 148.000 mm** — unchanged |
| Placement collisions | **0** |
| `p1_regression` | **PASS**, 0 checks failed |
| `dru_probe` / `netclass_probe` | **PASS / PASS** |
| `fork_equivalence` | **PASS** — Beta-DM and the frozen Beta tree untouched |
| `hardware/beta/mechanical/` | **untouched** (still untracked, not modified) |

**Only two files were added and three documentation files updated. No KiCad file was written.**
