# AQROOT Full Beta v2 — Expansion ecosystem proposal

**Status: APPROVED AND IMPLEMENTED 2026-08-24 at FBV2-EXP-002 (D-237 ... D-242).**
This document is now the RECORD OF THE PROPOSAL, not a live proposal. Where it differs from
what was built, the built design wins: the owner approved the direction with **one pin-order
correction**, so **ORDER-A below is SUPERSEDED BY ORDER-B** (D-240), which is safe under
180 degree reversal as well as against a one-position shift. E-1 through E-6 were all taken;
**E-2's predicted ~5 % capacity penalty did NOT materialise** -- both credible cells are
50 mm wide, so the 57 mm limit binds neither (D-239). The built account is
[`../audits/2026-08-24-expansion-and-refloorplan-implementation.md`](../audits/2026-08-24-expansion-and-refloorplan-implementation.md).
Created 2026-08-24 at **FBV2-EXP-001**. Repository HEAD at task start: `24032a5`.

> ~~**NOTHING IN THIS DOCUMENT IS IMPLEMENTED.**~~ **IT IS NOW ALL IMPLEMENTED (FBV2-EXP-002).**
> `J5` is a 1 × 24 socket, `J8` Qwiic exists, `BOOT` has moved and the board is 72 × 148 mm.
> **D-081 / D-083 / D-093 / D-097 are SUPERSEDED IN THEIR PHYSICAL HALF by D-237 / D-240** — the
> electrical architecture they lock is untouched. Still zero routing.

Evidence and measurements: [`../audits/2026-08-24-expansion-compatibility-audit.md`](../audits/2026-08-24-expansion-compatibility-audit.md).

---

## 1. What is proposed

Replace the **presentation** of the community expansion port — not its electronics — with a
community-standard interface:

| element | proposal |
|---|---|
| **Main expansion** | **one 1 × 24, 2.54 mm right-angle FEMALE receptacle**, vertical along the right wall, one contact per line, ordinary 0.64 mm square male posts / Dupont-compatible |
| **I²C accessories** | **one JST SH 1.0 mm 4-pin Qwiic / STEMMA QT connector**, on the *protected external* I²C segment |
| **`BOOT`** | moves off the right wall to the **bottom edge**, recessed, tool-access only |
| **`POWER`** | **stays on the right wall**, below the Qwiic connector |
| **Everything electrical behind the connector** | **unchanged** — same series resistors, same TVS arrays, same TCA4307, same load switches, same boost, same FLT handling |

**No proprietary connector. No hub. No mux. No Grove, mikroBUS, Arduino shield socket or Pi
header.** The only new product capability is a standard GPIO presentation plus Qwiic.

---

## 2. The condition attached to it — and it is not small

**The 1 × 24 interface does not fit the current 70 × 148 mm floorplan.** This is measured, not
estimated:

> A right-angle THT socket puts its solder tails **≈ 6.5–6.9 mm inboard of its own mating face**
> (Sullins 1-row RA drawing 10493). For the mating face to reach the right wall, the tail row lands
> at x ≈ 63.5, which is **inside the battery envelope** (X 6.00 … 66.00), and
> `BATTERY_SHADOW` forbids any through-hole lead there.
>
> **Requirement: (board right edge − battery right edge) ≥ 7.83 mm. Today it is 4.00 mm.
> Shortfall 3.83 mm.**
>
> Above the battery the right wall offers only **41.00 mm** (Y 98.5 … 139.5, bounded by the IR
> receiver). A 1 × 24 body is **61.47 mm**. The largest socket that fits there is a **1 × 15**, and
> that leaves nothing for the Qwiic connector or the power switch.

**Therefore this proposal requires, and is conditional on, two owner rulings:**

| # | change | cost | note |
|---|---|---|---|
| **E-1** | **PCB 70.0 → 72.0 mm wide** | none to the enclosure | 72 × 152 is **already the documented `FBV2_PCB_MAX_MM`**; the 80 × 160 × 23 shell and the 75 × 155 cavity are unchanged. Board-to-wall falls 2.5 → 1.5 mm, which still meets the ≥ 1.5 mm rule |
| **E-2** | **battery 60 → 57 mm wide** (75 mm and 8.0 mm unchanged) | **≈ −5 % capacity**, ~2375–2850 mAh | supersedes part of **D-071**. This is the whole price of the interface |

With E-1 and E-2 the margin is **+1.17 mm** and the right wall carries the 1 × 24 header, the Qwiic
connector and the power switch with ~15.9 mm of gap to distribute.

**If the owner declines E-2, the 24-line side header cannot be delivered in this enclosure and
`J5` stays as it is.** There is no third answer: the left wall is the 433 flex and the mandatory
915 coax channel, the bottom edge is USB-C / microSD / both radio modules, and the top edge is the
IR pair, the barrier and the SMA.

---

## 3. Connectors

### 3.1 Main expansion — 1 × 24 right-angle female

**Baseline: Samtec `SSQ-124-02-G-S-RA`** (gold; `-L-` 10 µin, `-F-` gold flash and `-T-` tin are
the other plating codes; `-22-` is the low-insertion-force lead style).

| property | value | source |
|---|---|---|
| Series | SSQ, `.025"` square-post socket, **2.54 mm pitch** | Samtec SSW/SSQ datasheet |
| Positions per row | **01 thru 50** — 24 is a standard configuration | same |
| Row option | `-S-` = **single row** | same |
| Tail option | `-RA` = **right angle**, available with `-S` | same |
| Body length | **N × 2.54 + 0.51 = 61.47 mm** | same |
| Pin span (1 → 24) | **58.42 mm** | 23 × 2.54 |
| Socket-axis height above PCB | lead style **−02 → 2.54 mm**, −03 → 7.62 mm, −04 → 12.45 mm | same |
| Insertion depth | **3.68 … 6.35 mm** | same |
| Mates | **.025" (0.635 mm) square post** — the standard male header / Dupont post | same |
| Current | **6.3 A per pin** (2 pins powered) | same |
| Voltage | 465 VAC / 655 VDC | same |
| Temperature | −55 … +125 °C with gold | same |
| Durability | **100 cycles** at 10 µin Au | same |

**Why Samtec:** it is **the same manufacturer as the current `J5`** (`BCS-112-S-D-HE`), so the
account, the lead-time behaviour and the small-quantity policy are already known to the programme.

**Second source, verified and NOT baselined:** Sullins **`PPTC241LGBN-RC`** (tin) /
**`PPPC241LGBN-RC`** (gold) — `xPxCxx1LGBN-RC` is confirmed as *"HEADER FEMALE, 2.54 mm CC, 1 ROW,
RA"*, 3 A, 250 VAC, −40 … +105 °C, Ø1.02 mm recommended hole, mates the standard 2.54 mm male
series. **But DigiKey shows the non-RC variant obsolete with 0 stock, and the 19-way sibling
`PPTC191LGBN-RC` is factory-order only: 1,000-piece minimum, 11-week lead.** Under **D-096** that
is a procurement risk, not a baseline. It is recorded as a drawing-verified geometric reference,
which is what supplied the 6.53 mm body-depth figure this proposal turns on.

### 3.2 Qwiic / STEMMA QT

**`JST SM04B-SRSS-TB(LF)(SN)`** — SH series, **1.0 mm pitch**, 4 circuits, **side-entry**,
surface mount. Body **6.0 mm** wide × 4.25 mm deep. 1.0 A, 50 V, −25 … +85 °C, 20 mΩ contact
resistance. This is the exact part the Qwiic and STEMMA QT ecosystems standardised on, so every
Qwiic and every STEMMA QT cable mates it.

**Pin order (the ecosystem standard, not a choice):**

| pin | signal | cable colour |
|---|---|---|
| 1 | **GND** | black |
| 2 | **3.3 V** | red |
| 3 | **SDA** | blue |
| 4 | **SCL** | yellow |

---

## 4. Where it attaches — and why there is nothing to add

The external I²C segment already exists and is already protected:

```
I2C_SCL_INT / I2C_SDA_INT
   → U16 TCA4307 (VCC = ACC_3V3_SW, EN = ACC_PWR_EN)
   → EXT_SCL_BUF / EXT_SDA_BUF   (1.5 k pull-ups R50 / R49 to ACC_3V3_SW)
   → R47 / R48  22 Ω series
   → EXT_SCL / EXT_SDA           (D2 TPD4E1B06 TVS clamps here)
   → J5.2 / J5.6
```

> **Qwiic attaches at `EXT_SCL` / `EXT_SDA` — the node downstream of the 22 Ω resistors and at the
> TVS clamp, i.e. the same node as the main header.** It therefore inherits the hot-swap buffer,
> the pull-ups, the series resistance and the ESD clamp, and **adds no component at all.** `D2` is
> placed between the two exits so both are equally close to the clamp.
>
> **Qwiic power = `ACC_3V3_SW`.** This is not a preference. `U16`'s own VCC is `ACC_3V3_SW` and the
> pull-ups pull to `ACC_3V3_SW`, so powering Qwiic from unswitched `+3V3` would create a
> powered-device / unpowered-bus state.
>
> **`ACC_5V_SW` is never exposed on Qwiic.**

**Capacitance:** the external bus budget is ≤ 200 pF at 400 kHz (1.5 kΩ; the strict Fast-mode
figure is 236 pF for `t_r` ≤ 300 ns). On-board copper is ≈ 21 mm ≈ 21 pF, the connector ≈ 1 pF, a
100 mm Qwiic cable ≈ 5–10 pF and a typical Qwiic breakout ≈ 10 pF. **Three daisy-chained boards on
100 mm cables ≈ 55–75 pF — comfortably inside.** **No mux and no repeater is required, and none
should be added.**

---

## 5. Recommended 24-pin order — ORDER-A

Pin 1 at the **top** of the right wall (nearest the IR corner), reading down.

| pin | label | net | | pin | label | net |
|---|---|---|---|---|---|---|
| 1 | **5V** | `ACC_5V_SW` | | 13 | X4 | `XGPIO4_HDR` |
| 2 | **G** | `GND` | | 14 | **G** | `GND` |
| 3 | **3V3** | `ACC_3V3_SW` | | 15 | X5 | `XGPIO5_HDR` |
| 4 | **SDA** | `EXT_SDA` | | 16 | X6 | `XGPIO6_HDR` |
| 5 | **SCL** | `EXT_SCL` | | 17 | X7 | `XGPIO7_HDR` |
| 6 | **G** | `GND` | | 18 | X8 | `XGPIO8_HDR` |
| 7 | **N38** | `NATIVE_A_HDR` | | 19 | X9 | `XGPIO9_HDR` |
| 8 | **N47** | `NATIVE_B_HDR` | | 20 | **WAKE** | `WAKE_ATTN_N_HDR` |
| 9 | X0 | `XGPIO0_HDR` | | 21 | **DET** | `ACC_DETECT_N_HDR` |
| 10 | X1 | `XGPIO1_HDR` | | 22 | **3V3** | `ACC_3V3_SW` |
| 11 | X2 | `XGPIO2_HDR` | | 23 | **G** | `GND` |
| 12 | X3 | `XGPIO3_HDR` | | 24 | **5V** | `ACC_5V_SW` |

**All 24 current functions are retained.** 2 × `ACC_5V_SW`, 2 × `ACC_3V3_SW`, 4 × `GND`,
`EXT_SDA`, `EXT_SCL`, `NATIVE_A`, `NATIVE_B`, `WAKE_ATTN_N`, `ACC_DETECT_N`, `XGPIO0`–`XGPIO9`.
Nothing added, nothing removed, nothing merged.

**Why this order:**

* pins **3–4–5–6 are `3V3 / SDA / SCL / GND`** — the exact block the brief asked for, and the same
  order every maker already knows from Qwiic;
* **both 5 V contacts sit at the two physical ends of the row**, which is the strongest possible
  visual and tactile cue for "this one is different";
* **no 5 V pin is adjacent to any signal.** Each has `GND` as its only inboard neighbour. The
  current order does not have this property — today `ACC_5V_SW` sits next to `NATIVE_B` and next to
  `ACC_DETECT_N`;
* native GPIO (`N38`, `N47`) is a separate two-pin group immediately after a `GND`, never mixed
  into the `X0…X9` run;
* the ten expander GPIO run contiguously, split once by the `GND` at pin 14;
* `WAKE` and `DET` — the two lines a *smart* accessory uses and a generic breakout does not — are
  together at 20/21, away from the general-purpose block.

**New mis-plug hazard created: none, and two existing ones are removed.** Under ORDER-A a
one-position slip from either 5 V pin lands on `GND`: a **current-limited short** (`U22` ILIM
≈ 0.69 A, reverse-current blocking, thermal shutdown, `FLT` reported), not 5 V into a 3.3 V input.
The residual adjacency `3V3(3)–SDA(4)` and `3V3(22)–DET(21)` are both benign: SDA is already pulled
to that same rail and `DET` reads "no accessory" when high.

Alternative orders considered and not recommended are in the audit §7.

---

## 6. Full-header mating safety — enclosure, not software

| feature | specification |
|---|---|
| Recess | pocket in the right wall, **internal length 62.5 mm**, ≥ 1.5 mm below the outer wall, **both ends CLOSED** |
| Effect | a mating 1 × 24 male body is exactly 24 × 2.54 = **60.96 mm**, so lateral play is **≈ 1.54 mm — 60 % of one pitch. A one-position shift is physically impossible** |
| Pin 1 | moulded triangular marker at the pin-1 end |
| 5 V marking | a **red band** at both ends of the recess, over pins 1 and 24 |
| Dupont access | **unaffected** — the recess opening is one continuous slot at socket-face height; each 2.54 mm jumper housing enters its own aperture |
| Proprietary shroud | **none required** |
| Optional belt-and-braces | Samtec's `"XXX" = Polarized` option plugs a chosen position. If ever used it must sit on a **25th, non-functional position** (`SSQ-125-…`, body 64.01 mm) so no function is lost. **Not recommended for build 1** — the closed-end recess already does the job |

**No part of this relies on software.**

---

## 7. Power control — verified, and no hardware change is needed

Traced from the board, pin by pin:

```
3.3 V:  +3V3 → U20 TPS22950C  (ON = pin 1 = ACC_3V3_EN ← U3.P15, R98 100 k pull-down)
                              (ILIM = R97 1.5 k, FLT = pin 6)  → ACC_3V3_SW
5 V:    BQ25185_SYS → U21 TPS61023 (EN = ACC_5V_BOOST_EN ← U3.P16, R102 100 k pull-down)
                    → ACC_5V_RAW
                    → U22 TPS22950C (ON = ACC_5V_SW_EN ← U23.P04, R131 100 k pull-down)
                                     (ILIM = R101 1.65 k, FLT = pin 6) → ACC_5V_SW
FLT:    U20.6 and U22.6 wire-OR → ACC_POWER_FAULT_N (R103 100 k to +3V3) → U3.P18
DETECT: J5 → R64 100 Ω → ACC_DETECT_N (R129 100 k to +3V3) → U3.P17   ** INPUT ONLY **
```

> **`ACC_DETECT_N` reaches nothing but an expander input.** There is no AND gate, no interlock and
> no hardware bypass anywhere between it and the three enables. **Detect gating is one hundred
> percent firmware policy (MX-3).**

| question | answer |
|---|---|
| Can firmware explicitly command **5 V OFF / ON** with no hardware bypass? | **YES.** Two independent enables (`U3.P16` boost, `U23.P04` load switch), both defaulting OFF through 100 k pull-downs. **No permanent 5 V is physically possible** |
| Can firmware explicitly command **3.3 V OFF / ON without `ACC_DETECT_N` asserted**? | **YES.** `ACC_3V3_EN` is an ordinary expander output; nothing gates it |
| Hardware change for a Manual / Bench mode? | **NO — for either rail** |
| Is any unsafe state created? | **No new one.** ILIM, reverse-current blocking, thermal shutdown and `FLT` are hardware and stay active in every mode. The only change is that the *user*, rather than the detect contact, authorises the rail |

### 7.1 Recommended DETECT policy

| mode | behaviour |
|---|---|
| **NORMAL / SMART ACCESSORY** — default | `ACC_DETECT_N` required. Automatic sequencing: boost EN → **≥ 10 ms** settle (D-198) → load-switch EN. `FLT` handled within 100 ms (MX-4) |
| **MANUAL / BENCH** — explicit opt-in | User enables each rail **independently and deliberately**. `DETECT` may be absent. All hardware protection active. **Non-persistent**: reverts to NORMAL on power cycle and on any `FLT`. UI must state **"signal logic is 3.3 V only"** |

**Sleep / wake:** `ACC_3V3_SW` must stay enabled during sleep for accessory wake (B-36), and that
is unchanged. With the rail on and no accessory fitted, `Q10`'s gate is held by `ACC_3V3_SW` and
`R63` 10 k holds the connector side high, so an open `WAKE` contact cannot generate a spurious wake.

**Carried forward unchanged: B-35.** `TPS22950C` `FLT` does not assert on plain current limiting —
only on thermal shutdown and reverse current. A *partial* overload stays invisible to the host in
every mode. Bench mode makes it more likely to be met, so the UI warning matters.

---

## 8. Multi-board use

| workflow | verdict |
|---|---|
| **A. Generic boards on individual Dupont leads**, sharing selected GPIO and power | **Fully supported.** This is the ordinary practice the interface exists for |
| **B. Qwiic boards daisy-chained** | **Supported** wherever the accessory board carries two Qwiic connectors, which most do. Standard Qwiic splitters and multiport boards work. **No AQROOT hub is required or should be built** |
| **C. One Qwiic board + one GPIO board at once** | **Fully supported.** The two interfaces are independent; the Qwiic connector sits below the header so its cable does not cross it |
| **D. Two official full-header accessories** | **Direct stacking is NOT recommended.** A single row has no roll stiffness for a second tier, and both boards would share every line including both rails. **The safe standard is one full-header accessory at a time; a second board uses Qwiic or jumper wires** |

**Address collisions are not solved by this or any other connector.** Two accessories with the same
fixed I²C address still collide, including at 0x50.

---

## 9. Accessory-ID EEPROM at 0x50

**Verdict: fine as an OPTIONAL single-accessory convention. It needs a firmware convention. It
needs no main-PCB change and no redesign.**

| scenario | behaviour |
|---|---|
| Ordinary Qwiic devices | Most do not use 0x50, but **some do** — 24Cxx-class EEPROM breakouts occupy 0x50–0x57. A false positive is possible |
| Multiple smart AQROOT accessories | **They collide.** 0x50 is a single-slot convention |
| Pass-through / daisy chain | Same collision |

**Firmware convention required:** probe 0x50 only as a *hint*, never as proof; require a magic
signature in the first bytes before treating the device as an AQROOT accessory ID; treat an
ambiguous or absent response as "no ID" and fall back to Manual/Bench behaviour. Widening the
reservation to 0x50–0x57 is a **future accessory-standard revision** (with P-19), not a board
change.

---

## 10. What does NOT change

Every part behind the connector is untouched:

| block | parts |
|---|---|
| GPIO series | `R51`–`R60` 100 Ω (X0–X9), `R61`/`R62` 100 Ω (natives) |
| I²C series | `R47`/`R48` 22 Ω |
| WAKE | `R66` 330 Ω, `Q10` 2N7002 gate, `R63` 10 k |
| DETECT | `R64` 100 Ω, `R129` 100 k |
| ESD | `D2`–`D5` TPD4E1B06 ×4, all sixteen exposed signal contacts |
| Hot-swap buffer | `U16` TCA4307, `R49`/`R50` 1.5 k, `R17` 100 k, `R46` 10 k |
| 3.3 V | `U20` TPS22950C, `R97`, `R98`, `C37`/`C39`/`C63` |
| 5 V | `U21` TPS61023 + `L4`, `U22` TPS22950C, `R99`–`R102`, `R131`, `C65`–`C67`, `C38` |
| FLT | `R103` 100 k wire-OR |

**The schematic change is a footprint swap plus a pin re-map on sheet 09 only.** No net is created,
deleted, split or merged; `J5`'s 24 pin-to-net assignments are re-ordered and its footprint changes.
The Qwiic connector adds one 4-pin symbol whose pins land on four nets that already exist.

---

## 11. Labelling

**Board silkscreen:** full legend beside the row — `1 5V · 2 G · 3 3V3 · 4 SDA · 5 SCL · 6 G ·
7 N38 · 8 N47 · 9 X0 … 19 X9 · 20 WAKE · 21 DET · 22 3V3 · 23 G · 24 5V` — plus a pin-1 triangle.

**Enclosure:** pin numbers **1, 6, 12, 18, 24** moulded on the recess ledge; the short function
labels printed or laser-marked at 2.54 mm pitch; a **red band at both ends** for 5 V; a moulded
pin-1 triangle.

**Two statements must appear on the product and in the documentation:**

1. **5 V is POWER ONLY. Every signal contact is 3.3 V CMOS. Do not drive any signal above 3.3 V.**
2. **`N38` / `N47` are native ESP32 GPIO (fast, interrupt-capable). `X0`–`X9` are expander GPIO
   (I²C-mediated, slow, no interrupts, no PWM).** That difference is invisible from the outside and
   is the single most likely user surprise.

---

## 12. Physical familiarity is not electrical compatibility

**What this interface genuinely gives users:**

| | verdict |
|---|---|
| Standard male Dupont jumper wires | **Yes** — 0.64 mm square post is the mating standard |
| Male-to-female jumpers to a breadboard | **Yes** |
| Generic breakout boards via jumpers | **Yes** |
| Logic analyser flying leads / probes | **Yes**, directly |
| Arduino-style jumper wiring | **Yes** |
| Plugging AQROOT into a breadboard | **No** — AQROOT is the host, not a module |

**What it does NOT give:**

> **No Arduino shield, no Raspberry Pi HAT and no Flipper Zero module becomes pin-compatible.**
> The connector is physically familiar; the pinout, the voltage domains and the protocols are
> AQROOT's. Any claim beyond "standard 2.54 mm sockets and standard Qwiic" would be false.

---

## 13. Mechanical strength, honestly

| | current `BCS-112-S-D-HE` 2 × 12 | proposed 1 × 24 |
|---|---|---|
| Tails | 24 in **two rows 7.87 mm apart**, over 27.94 mm | 24 in **one row**, over 58.42 mm |
| Resistance to **roll** (twisting about the connector's long axis — the way a leaned-on accessory loads it) | **7.87 mm couple arm** | **none** |
| Resistance to **yaw** | 27.94 mm arm | **58.42 mm arm — 2.09× better** |
| Verdict | stronger where it matters most | **weaker in roll, stronger in yaw** |

**Mitigation, non-electrical only:**

* the recess floor and its two closed ends carry the roll moment;
* a **moulded ledge** the full 62.5 mm of the recess, on which the accessory board's lower edge
  rests. No fastener, no new connector, no extra part on the PCB;
* accessory design guidance: ≤ ~40 mm deep, ≤ ~60 g; anything heavier carries its own standoff to
  the rear shell.

---

## 14. What the owner is being asked to decide

| # | decision | consequence if declined |
|---|---|---|
| **E-1** | PCB 70.0 → **72.0 mm** wide (within the already-documented 72 × 152 maximum; enclosure unchanged) | with E-2 alone the margin drops to ~0.2 mm — buildable but with no tolerance |
| **E-2** | Battery 60 → **57 mm** wide, ≈ **−5 % capacity** | **the 24-line side header cannot be delivered.** `J5` stays as the 2 × 12 |
| **E-3** | Replace `J5` `BCS-112-S-D-HE` with `SSQ-124-02-G-S-RA` + add `SM04B-SRSS-TB` | supersedes D-081 / D-083 / D-093 pin order and connector, not the electronics |
| **E-4** | Adopt **ORDER-A** pin ordering | historical order is retained; two 5 V-adjacent-to-signal hazards remain |
| **E-5** | Move `BOOT` to the bottom edge at doc ≈ (27.0, 5.0) | the right wall cannot carry header + Qwiic + power |
| **E-6** | Add the **Manual / Bench** firmware mode | firmware-only either way; no hardware consequence |

**E-1 through E-5 must be taken together or not at all**, and they must be executed in the **same**
re-floorplan as PM-1, PM-2, PM-3 and PT-1 — see the audit §11.
