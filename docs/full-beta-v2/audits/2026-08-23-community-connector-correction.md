# AQROOT Full Beta v2 — Community Connector Correction and Final Lock

Date: **2026-08-23**
Task: **FBV2-COMM-002**
Repository HEAD at audit: `d96d152`
Scope: **documentation only.** No KiCad, PCB, firmware, mechanical CAD or fabrication
file was created or modified. `hardware/beta-v2/` was not created.

Corrects [`2026-08-23-community-expansion-closeout.md`](2026-08-23-community-expansion-closeout.md)
(FBV2-COMM-001). **Only the connector selection changes.** The 24-contact
allocation, the pin ordering, the two accessory rails, the expander architecture
and the firmware contract all stand.

---

## 0. Verdict

> ### CONNECTOR LOCK = **PASS**
>
> **Harwin `M20-7881242` is REJECTED and removed from every living document.**
>
> **Locked: Samtec `BCS-112-S-D-HE`** — .100 in / 2.54 mm, 2 × 12, 24-contact
> female Tiger Claw™ dual-beam receptacle, **horizontal (right-angle) entry**,
> through-hole, **30 µin gold** contact plating.
>
> **Cost-down alternate, footprint- and body-identical: `BCS-112-L-D-HE`**
> (10 µin gold) — a **plating-only** substitution with no board change.
>
> **Pin ordering unchanged. Electrical architecture unchanged.**
> **Z-stack improves from 22.30 mm to 19.53 mm of the 23.0 mm budget.**

---

## 1. Sources

| # | source | weight |
|---|---|---|
| **S1** | **Samtec `BCS-112-L-D-HE` and `BCS-112-S-D-HE` product records** (samtec.com) — description, orientation, stock, OEM price breaks, similar-part table, compliance | **Primary manufacturer data**, retrieved |
| **S2** | **Samtec BCS series catalogue page** (`suddendocs.samtec.com/catalog_english/bcs.pdf`) — part-number decoder, materials, temperature, voltage, current rating, insertion depth | **Primary**, retrieved and text-extracted |
| **S3** | **Samtec BCS series print `BCS-1XX-XXX-X-XX-XXX` Rev CK**, 3 sheets — body geometry per entry style, notes, tolerances | **Primary**, retrieved and text-extracted |
| **S4** | **Samtec BCS recommended PCB layout `BCS-1XX-XXX-X-XX-XXX FOOTPRINT` Rev B**, sheet 3 (FIG 3, `D-HE`) | **Primary**, retrieved and text-extracted |
| **S5** | **Samtec test report 187544 Rev 1** — BCS/TSM design qualification, 10 µin vs 30 µin gold, durability step | **Primary**, retrieved |
| **S6** | **Samtec `bcs_elp.pdf`** — E.L.P. extended-durability pointer (2 500 cycles, 30 µin gold, by similarity to SSM/TSM) | **Primary**, retrieved |
| **S7** | **Samtec TSW/HTSW catalogue page** — lead-style chart, mating post lengths, BCS-mated current and voltage ratings | **Primary**, retrieved and text-extracted |
| **S8** | Digi-Key catalogue record for a BCS-112 part — lifecycle **Active**, 4.6 A/contact, plating, insulation height, voltage | Distributor, authoritative for lifecycle |
| **S9** | harwin.com product page for `M20-7881242` | **HTTP 404** — see §2 |
| **S10** | `audits/2026-08-23-community-expansion-closeout.md`, `CTO_DECISIONS.md`, `mechanical/MECHANICAL_INTERFACE_SPEC.md` (read only) | Locked v2 architecture |

---

## 2. The rejection, recorded plainly

The CTO's lifecycle finding stands and is corroborated: **`https://www.harwin.com/products/M20-7881242` returns HTTP 404** — the part number does not resolve to a live Harwin catalogue item.

**This was a foreseen failure mode, and it was flagged.** FBV2-COMM-001 §15
"Honest limitations" item 2 stated verbatim:

> *"`M20-7881242` was constructed from the catalogue's ordering scheme
> (`M20-78` + `8` for double row + `12` contacts per row + `42` for gold+tin) and
> from the confirmed existence of neighbouring codes. **It should be verified
> against a live distributor listing before the BOM is issued.**"*

The lesson is recorded rather than glossed: **a part number derived from an
ordering scheme is a hypothesis, not a selection.** From this point on, every
connector, and every part whose MPN is configured rather than catalogued, must be
confirmed against a live manufacturer or distributor record showing lifecycle
status and stock **before** it is written into a locked document. That rule is
added to the audit discipline as **D-096**.

`M20-7881242` has been removed as the locked connector from `CTO_DECISIONS.md`,
`ARCHITECTURE.md`, `MECHANICAL_INTERFACE_SPEC.md`, `PROGRESS.md` and the
FBV2-COMM-001 changelog entry, and struck through in place so the history stays
readable.

---

## 3. Samtec BCS-112-x-D-HE, verified against current documentation

### 3.1 Identity and lifecycle

| parameter | value | source |
|---|---|---|
| Manufacturer | **Samtec, Inc.** | S1 |
| Series | **BCS** — Tiger Claw™ pass-through socket strip, .100 in pitch | S2 |
| Catalogue description | *".100in/2.54mm **Through Hole Dual Beam Receptacle, 24 Pin, 2 Row, Horizontal Entry**"* | **S1** |
| **Locked MPN** | **`BCS-112-S-D-HE`** — 30 µin selective gold in the contact area, matte tin on the tail | S1, S2 |
| Alternate MPN | `BCS-112-L-D-HE` — 10 µin gold, otherwise identical | S1 |
| Part-number decoder | `BCS` – `112` (12 pins per row) – `S` (30 µin Au) – `D` (double row) – `HE` (**horizontal entry**) | **S2** |
| **Lifecycle** | **ACTIVE.** Digi-Key part status *Active*; Samtec factory stock for both variants | **S1, S8** |
| **Factory stock** | `-S-D-HE`: **385 pieces ship tomorrow**. `-L-D-HE`: **1 809 pieces ship tomorrow** | **S1** |
| Distributor stock | 0 at Samtec's linked distributors; Samtec ships direct, **MOQ 1**, tube of 18 | S1 |
| **Price** | `-S`: **$7.314 @ 1**, $5.667 @ 100, $4.787 @ 500. `-L`: **$4.435 @ 1**, $3.435 @ 100 | **S1** |
| Compliance | RoHS, REACH no SVHC, halogen-free (Br/Cl per JS-709C), MSL 1, UL E111594, no known PFAS | S1 |
| Probable country of origin | Malaysia | S1 |

**Prototype sourcing: MOQ 1, direct from Samtec, shipping next day.** For five
boards the connector line is US$36.57 at the `-S` single-unit price.

### 3.2 Mechanical

| parameter | value | source |
|---|---|---|
| Positions | **2 rows × 12 = 24** | S1 |
| Pitch | **.100 in / 2.54 mm** | S2 |
| Gender | **Female** (dual-beam Tiger Claw™ socket) | S1 |
| Entry / orientation | **Horizontal — right-angle, mating axis parallel to the PCB** | **S1, S3** |
| Termination | **Through-hole** | S1 |
| **Body length** | No. of positions × 2.54 mm = **30.48 mm ± 0.20** | **S3** |
| **Body depth** (into the board from the mating face) | **.320 in = 8.13 mm** (REF; identical for `-S-HE` and `-D-HE`) | **S3** |
| **Body height above board** | **.210 in = 5.33 mm** (`-D-HE`); `-S-HE` is .110 in = 2.79 mm, i.e. exactly one row pitch less — the two figures are internally consistent and confirm which dimension is the height | **S3**, ⚠ confirm against the 3D model at FBV2-P1 |
| Insulator | Glass-filled LCP, UL94 V-0, black | S2, S3 |
| Contact | Phosphor bronze, Au or Sn over 50 µin (1.27 µm) Ni | S2 |
| Minimum pushout force | 1 lb (4.45 N) per contact | S3 note 2 |
| Packaging | Tube, 18 parts | S1 |

### 3.3 PCB tail geometry — a new footprint is required

From the recommended PCB layout, **FIG 3, `BCS-1XX-XXX-D-HE-XXX`** (S4):

| parameter | value |
|---|---|
| Hole pattern | **2 rows × 12 plated through-holes** |
| Pitch within a row | **.100 in = 2.54 mm** |
| **Row-to-row spacing** | **.310 ± .002 in = 7.87 ± 0.05 mm** |
| **Drill** | **.028 in = 0.71 mm PTH** |
| End-hole span | (12 × 2.54) − 2.54 = **27.94 mm** |

> **The 7.87 mm row spacing is the important number.** It is *not* 2.54 mm — the
> horizontal-entry tails splay outward. **The footprint is therefore not
> interchangeable with any vertical 2×12 header pattern**, and a new project-library
> footprint must be drawn and verified with a per-footprint pad-overlap assertion
> at FBV2-S2 (**B-29**, carried forward and re-scoped).
>
> A second item for FBV2-S2: **which mating row (upper or lower) terminates in
> which PTH row must be read off the print**, not assumed. It decides whether
> AQROOT pin 1 lands in the front or rear hole row. Recorded as **B-40**.

### 3.4 Electrical

| parameter | value | source |
|---|---|---|
| **Current rating** | **4.6 A per pin** mated with TSW (5.0 A mated with TSM), 2 positions powered | **S2, S7, S8** |
| Voltage rating | **450 VAC / 636 VDC** for `-HE` mated with TSW | S2 |
| Operating temperature | **−55 °C to +125 °C** | S2, S8 |
| Contact plating | `-S` = 30 µin selective gold in the contact area, matte tin on the tail | S2 |
| Lead-free solderable | Yes | S2 |

Against our loads — 400 mA total on `ACC_3V3_SW` across two contacts (200 mA each)
and 300 mA total on `ACC_5V_SW` (150 mA each) — the contacts run at **≈ 4 % and
≈ 3 % of rating**. The duplication remains margin, not necessity.

### 3.5 Mating forces

| parameter | value | source |
|---|---|---|
| Insertion force, per contact, with a .025 in square pin | **5 oz = 1.39 N average** | Samtec series data |
| Withdrawal force, per contact | **3 oz = 0.83 N average** | Samtec series data |
| **24 contacts, total insertion** | **≈ 33.4 N average (≈ 3.4 kgf)** | derived |
| **24 contacts, total withdrawal** | **≈ 19.9 N average (≈ 2.0 kgf)** | derived |

⚠ **These are averages, not maxima.** Samtec's own mating-force note (S-series
whitepaper) explains that mating occurs in a *spreading* stage and a *sliding*
stage, and that the **peak** force occurs during spreading and exceeds the average.
The enclosure load path in §4 is therefore sized on the average with the peak
explicitly acknowledged, not on the average alone.

Even so, **33 N average is materially better than the ~48 N maximum of the
rejected Harwin part**, and the withdrawal force is low enough that accessory
retention becomes a question worth asking (§7, N-2).

### 3.6 Mating cycles — the finding that changed the plating code

This is the reason the locked MPN is **`-S`** and not the **`-L`** the CTO
proposed, and it is exactly what §2's instruction to *"verify mating-cycle /
extended-life information"* was for.

| evidence | finding |
|---|---|
| **S5** — Samtec design qualification 187544 Rev 1, BCS/TSM, *"10u″ Gold (-L)"* vs *"30u″ Gold (-S)"*, Durability/LLCR step 03 | **100 cycles for BOTH platings.** That is the formally qualified catalogue figure |
| **S6** — `bcs_elp.pdf` | *"The BCS/TSM is **Qualified by Similarity** to the SSM/TSM Series **Extended Durability Test Report (2500 Cycles, 30″ Gold)**"* |
| S1 — Samtec product-page navigation | BCS appears under **E.L.P.™ High Mating Cycle Connectors**, with a published *"BCS/TSW — Extended Durability (2,500 Cycles)"* report |

**So:**

- **10 µin gold (`-L`): 100 cycles qualified, and no extended-durability data
  applies.** That is *worse* than the rejected Harwin part's 300 gold cycles.
- **30 µin gold (`-S`): 100 cycles qualified, plus 2 500-cycle extended-durability
  data by similarity at that plating**, plus a 10-year mixed-flowing-gas result.

For a **user-swappable community port on a maker platform, mating-cycle life is a
first-order product parameter**, not a detail. The `-S` upgrade costs **US$2.88 per
board at quantity one and US$2.23 at 100** — about **US$14 across the first five
boards** — for the only plating with extended-life evidence behind it.

> **Locked: `BCS-112-S-D-HE`.** `BCS-112-L-D-HE` is retained as a **plating-only
> cost-down alternate** with an identical body and an identical footprint, usable
> with **no board change** if 100 cycles is later judged sufficient.

⚠ **Residual, recorded as B-39:** the 2 500-cycle figure is **by similarity**, and
the only figure formally qualified for BCS itself is **100 cycles**. Samtec must
be asked to confirm the rated mating-cycle count for `BCS-112-S-D-HE` before the
production run. **The design assumption for the first five boards is
"≥ 100 cycles qualified, 2 500 supported by similarity at 30 µin gold."** It is
not claimed as 2 500.

### 3.7 Mating-pin compatibility — commodity headers work

| parameter | value | source |
|---|---|---|
| **Accepted mating pin** | **.025 in (0.64 mm) square post** — the standard against which BCS forces and current are specified | **S2, S7** |
| **Required engagement depth, `-HE`** | **.171 in to .250 in = 4.34 mm to 6.35 mm** | **S2, S3** |
| Board mates listed by Samtec | TSW, MTSW, HTSW, HMTSW, TSS, ZSS, DW, EW, ZW, HW, TSM, MTLW, PHT | S2 |

**Recommended accessory-side reference part: `TSW-112-07-L-D`** — 2 × 12, .100 in,
straight, .025 in square post, **lead style −07: mating post C = .230 in
(5.84 mm)**, tail B = .100 in (2.54 mm), overall A = .430 in (10.92 mm) (S7).
**5.84 mm sits squarely inside the 4.34–6.35 mm window.** A right-angle accessory
mate (`TSW-112-xx-x-D-RA`) is also supported for a coplanar arrangement.

**Commodity compatibility, stated as an accessory-builder rule:**

> An ordinary 2 × 12, 2.54 mm male pin header with **0.64 mm square posts** mates,
> provided its **mating post length is between 4.34 mm and 6.35 mm**. The common
> 6.0 mm-post header qualifies. **Extra-long-pin headers (8.13 mm / .320 in posts,
> e.g. Samtec lead styles −14, −16, −24, −42) must not be used** — they exceed the
> horizontal-entry engagement window.

That single sentence is what preserves the whole reason for choosing 2.54 mm.

### 3.8 Alternatives considered

The brief required at least two active alternatives if the primary had a serious
problem. It does not — the only issue found was the plating code, resolved within
the same part family. The alternatives are recorded anyway:

| candidate | verdict |
|---|---|
| **`BCS-112-S-D-HE`** | **SELECTED.** Active, horizontal entry, 24 contacts, commodity-pin compatible, 4.6 A/contact, extended-life plating available, MOQ 1, next-day |
| `BCS-112-L-D-HE` | **Alternate.** Identical except 10 µin gold and 100-cycle life. Zero board change |
| Samtec **`SSW-112-02-x-D-RA`** (.100 in Tiger Buy socket, right-angle) | **Viable second source, not selected.** Same pitch and gender and also accepts .025 in square posts, but a different footprint and no published extended-durability data at this configuration. Held as the fallback family if BCS availability ever changes |
| Samtec **`BCS-112-S-D-TE`** (vertical, top entry) | **Rejected on architecture.** Vertical entry contradicts D-070's right-side exit. Retained only as evidence: its 7.37 mm insulation height (S8) cross-checks the horizontal body geometry in §3.2 |
| 2.00 mm keyed/shrouded systems (Hirose DF11, Molex Milli-Grid) | **Rejected, unchanged from FBV2-COMM-001.** They abandon commodity 2.54 mm male pins |
| Any Harwin M20 horizontal DIL socket | **Rejected** — the configured part number does not resolve (§2) |

---

## 4. Enclosure keying and mechanical support — LOCKED

The connector carries **no integrated key**, deliberately: the BCS "polarized
position" option exists but consumes a contact, and the ruling requires 24 active
contacts with no wasted position. All polarization is therefore mechanical.

| requirement | locked implementation |
|---|---|
| Connector recessed into the right-side enclosure | Socket face sits **≥ 1.5 mm behind** the outer wall surface; the recess walls form the shroud on all four sides |
| **Prevents upside-down insertion** | The recess is **asymmetric in the height axis**: a **rib/step along the upper edge only**, offset from the connector centreline. The two mating rows are only 2.54 mm apart vertically, so a flipped accessory is a real hazard and the key must be unambiguous, not a chamfer |
| **Prevents one-row / one-column offset** | The recess is **closed at both ends**, with **≤ 0.3 mm** clearance to the accessory shell at each end. A lateral shift becomes mechanically impossible rather than merely unlikely |
| **Connector body mechanically supported** | A moulded **shelf under the socket body and a backing rib behind it**, so the body is captured by the enclosure rather than cantilevered on its tails |
| **Insertion load not carried by solder joints** | The accessory shell bottoms on an **enclosure boss**, not on the connector. Load path: accessory shell → recess face → boss → shell wall. Sized for the **≈ 33 N average** insertion force **with the peak explicitly above that** (§3.5) |
| Lead-in | Chamfer on all four recess walls |
| Wall aperture | **34 × 10 mm nominal**, plus the keying rib, with 0.3 mm clearance to the accessory shell |
| Marking | Pin-1 triangle; **"COMMUNITY PORT — SIGNALS 3V3 ONLY"** and **"5V PIN IS POWER OUTPUT ONLY"** |

### 4.1 Z-stack recheck — the connector region is no longer the governing column

| layer | FBV2-COMM-001 (Harwin) | **FBV2-COMM-002 (BCS-112-S-D-HE)** |
|---|---|---|
| Front shell | 2.00 | 2.00 |
| **Connector body above PCB** | **8.10** | **5.33** |
| PCB | 1.60 | 1.60 |
| Battery | 8.00 | 8.00 |
| Clearance | 0.60 | 0.60 |
| Rear shell | 2.00 | 2.00 |
| **Total** | **22.30 mm** | **19.53 mm** |
| **Spare against the 23.0 mm external budget** | **0.70 mm** | **3.47 mm** |

> **The connector region falls from 22.30 mm to 19.53 mm and is now level with the
> control region's 19.5 mm** — it is no longer the sole governing column. **3.47 mm
> of usable clearance is real clearance, not a rounding artefact**, which is the
> standard the ruling demanded.
>
> Further relief remains available and is not counted above: the battery is 60 mm
> wide in a 75 mm cavity, so the outer ~5 mm of each PCB edge has nothing behind
> it. Placing the socket hard against the right edge recovers most of the 8.0 mm.
>
> ⚠ The 5.33 mm figure is read from the series print's `-D-HE` view and
> cross-checked against the `-S-HE` view (which differs by exactly one 2.54 mm row
> pitch) and against the 7.37 mm vertical insulation height. **It must still be
> confirmed against the individual 3D model at FBV2-P1** (**M-09**, retained but
> downgraded from MEDIUM to LOW).

**In-plane:** body 30.48 mm along the right edge of a 148 mm PCB, 8.13 mm deep
into a 70 mm-wide PCB. It must sit **below the display band** — the display leaves
only 6.73 mm of PCB clear on each side, less than the 8.13 mm depth. Unchanged
from FBV2-COMM-001.

---

## 5. Electrical allocation — unchanged, and one expander change

### 5.1 The 24 contacts and the pin ordering are NOT changed

The BCS-112-x-D-HE has the same 2 × 12 topology with the two mating rows stacked
vertically, so **the FBV2-COMM-001 ordering (D-084) transfers unchanged**:

| Col | Pin | Row A (upper) | Pin | Row B (lower) |
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

Power and ground remain distributed across columns 2, 5, 8 and 11; every power
contact is still vertically GND-paired; all 3.3 V is in row A and all 5 V in row
B; both native pins still flank the GND at pin 9; the detect strap is still one
0 Ω link between pins 21 and 23. **The whole mis-insertion argument of
FBV2-COMM-001 §3.2 carries over intact.**

### 5.2 O-1 APPROVED — `FLT` wire-OR and a reserved spare

The two TPS22950C `FLT` outputs are open-drain, so they wire-OR natively:

```
3V3 TPS22950C FLT ──┬── ACC_POWER_FAULT_N ──[100k pull-up to +3V3]── U3 P15
5V  TPS22950C FLT ──┘
```

One pull-up, one PCAL9535A input. **`U3` P16 is freed and becomes
`RESERVED_SPARE`.**

**Revised `U3` allocation — 15 assigned + 1 reserved:**

| pin | net |
|---|---|
| P00–P07 | `XGPIO0` … `XGPIO7` |
| P10, P11 | `XGPIO8`, `XGPIO9` |
| P12 | `ACC_3V3_EN` |
| P13 | `ACC_5V_EN` |
| P14 | `ACC_DETECT_N` |
| P15 | **`ACC_POWER_FAULT_N`** (wire-OR) |
| **P16** | **`RESERVED_SPARE` — no function assigned** |
| P17 | `SX1262_RXEN` |

**`RESERVED_SPARE` implementation** (so it is genuinely usable for recovery rather
than merely unassigned): route it to an accessible **test pad** and fit a **100 kΩ
pull-up to `+3V3`**, so the pin reads a defined level, has no floating CMOS input,
and can be pressed into service by a wire and a firmware change instead of a
respin. Two parts, no board risk. **Do not assign it a function.**

**Rail attribution without a per-rail `FLT`** — the CTO's method, recorded as a
firmware rule: the two enables are independent, so on `ACC_POWER_FAULT_N`
asserting, firmware disables one rail, waits, and observes whether the fault
clears; if it does, that rail was the source. Added to the contract as **MX-5a**.

**B-37 is downgraded**: `U3` now holds **one** spare expander pin. `U2` remains
16/16 with zero spare — that half of B-37 stands.

### 5.3 O-2 APPROVED — external I²C address 0x50 reserved

**`0x50` on the external (accessory) I²C segment is reserved for an optional
AQROOT accessory-identification EEPROM.** This is a **protocol reservation only**:

- **No hardware is added to the main board.**
- **No accessory is required to fit an EEPROM.** Accessories without one are fully
  supported and must not be penalised.
- Official AQROOT modules may use it for accessory type, hardware revision,
  capability flags and manufacturer/vendor ID.
- It joins the reserved-address table alongside `0x38` (touch), `0x68` (IMU),
  `0x36` (fuel gauge) and `0x20`/`0x21` (expanders). Community accessories must
  not squat any of them.

⚠ **One thing to be aware of, flagged not locked:** the 24Cxx EEPROM family
occupies **`0x50`–`0x57`** depending on its A0–A2 straps. Reserving `0x50` alone
means an AQROOT ID EEPROM must strap **A0 = A1 = A2 = 0**, and it leaves
`0x51`–`0x57` unreserved and therefore available to third-party accessories that
may also fit 24Cxx parts. If multi-EEPROM accessories ever appear, the reservation
may need to widen. Recorded as **P-19**, an extension of the still-open P-18
address-collision question.

### 5.4 O-3 REJECTED — recorded

**The accessory TPS61023 5 V rail is NOT connected to the NFC fallback.** No DNP
link, no shared node beyond `SYS`. The two remain electrically independent, as
D-056 intended. **Using the same TPS61023 device family is the extent of the BOM
consolidation.** The DNP 0 Ω link proposed as O-1/O-3 in FBV2-COMM-001 is struck.

---

## 6. Accessory power limits — restated with the sharing rule

| rail | **initial public / firmware limit** | hardware `R_ILIM` (recommended, not locked) | later validation target |
|---|---|---|---|
| `ACC_3V3_SW` | **400 mA total** | 1.5 kΩ → ≈ 0.76 A typ | **600–800 mA** if system and thermal bring-up passes |
| `ACC_5V_SW` | **300 mA total** | 1.65 kΩ → ≈ 0.69 A typ | **500 mA** if system and thermal bring-up passes |

> ### The duplicate contacts SHARE the rail limit. They do not double it.
>
> **`ACC_5V_SW` pin 10 + `ACC_5V_SW` pin 22 = 300 mA combined, NOT 300 mA each.**
> **`ACC_3V3_SW` pin 3 + `ACC_3V3_SW` pin 15 = 400 mA combined, NOT 400 mA each.**
>
> There is one load switch per rail and one current limit per rail. The second
> contact halves contact resistance and eases accessory routing; it adds no
> current budget. This must appear in the accessory-facing documentation in
> exactly these terms, because it is the single most likely thing for an accessory
> designer to get wrong.

Per-contact loading at the initial limits is 200 mA (3.3 V) and 150 mA (5 V)
against a **4.6 A** contact rating — a margin of more than 20×.

**Limits do not rise automatically.** Raising either one requires measured bring-up
data and a CTO ruling; the hardware change is one 0603 resistor per rail.

---

## 7. Final opportunity and simplification scan

Only two new items clear the "high value, low-to-moderate effort" bar. **Neither is
locked.**

| # | opportunity | value | effort | why it is not locked here |
|---|---|---|---|---|
| **N-1** | **Publish an accessory reference design**: the 2 × 12 header footprint, the 4.34–6.35 mm post-length rule, the detect-strap pattern (pins 21–23), the 3.3 V-only signal rule, the shared-rail current rule, and a board-outline template that fits the enclosure recess | **HIGH.** It is the difference between a documented platform and a pinout table. It also front-loads the exact mistakes an accessory builder would otherwise make: wrong post length, doubled current assumption, 5 V on a signal pin | **LOW** — documentation only, no main-board cost | It is a **deliverable**, and creating it is outside this task's authorization. **CTO call on whether to schedule it before or after FBV2-S1** |
| **N-2** | **Accessory retention.** Withdrawal force is only ≈ 20 N average and there is no latch. An accessory could be pulled out by its own cable or by pocket movement | **MEDIUM-HIGH** for field use | **LOW-to-MODERATE** — an enclosure-moulded friction detent or a captive fastener boss; no electrical change | It is a **mechanical/product decision** with an ergonomic trade-off (retention versus one-handed removal), and it belongs to enclosure CAD rather than to this closeout. **CTO / mechanical call** |

Deliberately **not** proposed: the BCS polarized-position option (consumes a
contact, forbidden), a latching connector family (loses commodity pins), per-contact
current sensing, a third expander, 5 V-tolerant buffers, an accessory MCU
handshake.

---

## 8. Signal safety — unchanged, restated

All connector signal pins remain **3.3 V CMOS only**. **5 V availability on pins 10
and 22 does not imply 5 V-tolerant GPIO anywhere.** Retained from D-090 without
change:

- 100 Ω series on every `XGPIO` and both native pins; 22 Ω on the buffered I²C
  pair; 330 Ω on `WAKE_ATTN_N`.
- A low-capacitance TVS array on `NATIVE_A`, `NATIVE_B`, `EXT_SDA`, `EXT_SCL` — the
  natives are the only contacts with a direct path to the MCU.
- External I²C buffered by `U16` TCA9517A, B-side supplied from `ACC_3V3_SW`.
- `WAKE_ATTN_N` isolated by the N-FET pass gate gated on `ACC_3V3_SW` (D-091).
- **No bidirectional level translators.**
- Silkscreen requirement: **`SIGNALS 3V3 ONLY`** must appear at the connector.

---

## 9. Gate assessment — FBV2-COMM-LOCK (re-issued)

| # | condition | status |
|---|---|---|
| 1 | Obsolete part removed from every living document | **YES** — §2 |
| 2 | Replacement is an **active**, stocked, prototype-orderable part | **YES** — Active, 385 pcs next-day, MOQ 1 |
| 3 | 2 × 12, 24 contacts, female, 2.54 mm, horizontal entry, through-hole | **YES** — §3.1, §3.2 |
| 4 | Body dimensions and PCB tail geometry documented | **YES** — §3.2, §3.3 (row spacing 7.87 mm, 0.71 mm PTH) |
| 5 | Compatible with commodity 0.64 mm square male pins | **YES**, with a stated 4.34–6.35 mm post-length window — §3.7 |
| 6 | Current, contact resistance class, forces, cycle life documented | **YES** — §3.4, §3.5, §3.6, with the cycle-life residual recorded as B-39 |
| 7 | Enclosure keying and load path locked | **YES** — §4 |
| 8 | Z-stack rechecked with real clearance | **YES** — 19.53 mm of 23.0, **3.47 mm spare** — §4.1 |
| 9 | 24-contact allocation and pin ordering preserved | **YES** — §5.1, unchanged |
| 10 | O-1 / O-2 / O-3 implemented as ruled | **YES** — §5.2, §5.3, §5.4 |
| 11 | Accessory limits and the shared-rail rule recorded | **YES** — §6 |

> ### **CONNECTOR LOCK = PASS.**

---

## 10. Open items created or changed

| # | item | severity | closes at |
|---|---|---|---|
| **B-39** | **Mating-cycle rating unconfirmed.** Only **100 cycles** is formally qualified for BCS; the **2 500-cycle** figure is E.L.P. data **by similarity** at 30 µin gold. Confirm the rated count for `BCS-112-S-D-HE` with Samtec before the production run | **MEDIUM** | procurement / pre-production |
| **B-40** | Which mating row (upper / lower) terminates in which PTH row of the 7.87 mm pattern must be read off the Samtec print, not assumed | LOW | FBV2-S2 |
| **B-29** | `J1`/`J5` footprint must be drawn to the **`BCS-1XX-XXX-D-HE` FIG 3** pattern — 2 × 12, 2.54 mm within a row, **7.87 mm between rows**, **0.71 mm PTH** — and verified with a per-footprint pad-overlap assertion | MEDIUM, **re-scoped** | FBV2-S2 |
| **M-09** | Confirm the 5.33 mm body height against the individual Samtec 3D model | **LOW** (was MEDIUM) | FBV2-P1 |
| **M-10** | Insertion load path — now **≈ 33 N average** (was ≈ 48 N max), peak above average. Enclosure boss still required | **LOW-MEDIUM** (was MEDIUM) | enclosure CAD |
| **B-37** | Zero spare expander capacity | **HALF CLOSED** — `U3` now holds **one** `RESERVED_SPARE` (O-1). **`U2` remains 16/16 with zero spare** |
| **P-19** | The 24Cxx family spans `0x50`–`0x57`; only `0x50` is reserved. May need widening if multi-EEPROM accessories appear | LOW | CTO, with P-18 |
| ~~O-1~~ | Wire-OR the `FLT` lines | **APPROVED and implemented** (D-094) |
| ~~O-2~~ | Accessory-ID EEPROM address | **APPROVED and implemented** (D-095) |
| ~~O-3~~ | Share the accessory boost with the NFC fallback | **REJECTED and struck** (D-095) |

Unchanged and still open from FBV2-COMM-001: **B-34** (series-path thermals),
**B-35** (`FLT` semantics), **B-36** (accessory wake needs the rail in sleep),
**B-38** (5 V boost inductor `I_sat` ≥ 3 A), **P-18** (external-I²C address
collision).

---

## 11. Honest limitations

1. **The 5.33 mm body height is derived from the series print, not from a
   dimensioned individual part drawing.** Three independent cross-checks agree
   (the `-S-HE` view differs by exactly one 2.54 mm row pitch; the vertical `-D-TE`
   body width is .20 in; the vertical insulation height of 7.37 mm matches the
   .290 in print figure), but it is still a reading of a drawing. **The Z-stack
   conclusion has 3.47 mm of margin, so it survives even a 2.8 mm error** — which
   is why it is stated as a PASS rather than deferred.
2. **The insertion and withdrawal forces are Samtec series averages**, not maxima
   and not measured on this configuration. The peak per contact is higher than the
   average by an amount Samtec does not publish for BCS.
3. **The 2 500-cycle extended-durability result is by similarity to SSM/TSM**, not
   a direct BCS/TSW test at this part number. See B-39.
4. **Distributor stock is 0**; sourcing is direct from Samtec. That is normal for
   Samtec and their MOQ is 1 with next-day shipment, but it is a single channel and
   is recorded as such.
5. **No part has been ordered, mated or measured.** Everything here is paper.
6. **The Harwin rejection is corroborated by a 404, not by a formal obsolescence
   notice.** A 404 shows the configured part number does not resolve on the
   manufacturer's site; it is consistent with the CTO's lifecycle finding and with
   the part number having been configured rather than catalogued.

---

## Sources

- Samtec **`BCS-112-S-D-HE`** — [product page](https://www.samtec.com/products/bcs-112-s-d-he) · **`BCS-112-L-D-HE`** — [product page](https://www.samtec.com/products/bcs-112-l-d-he)
- Samtec **BCS series** — [catalogue page (PDF)](https://suddendocs.samtec.com/catalog_english/bcs.pdf) · [series page](https://www.samtec.com/products/bcs) · [print `BCS-1XX-XXX-X-XX-XXX`](https://suddendocs.samtec.com/prints/bcs-1xx-xxx-x-xx-xxx-mkt.pdf) · [recommended PCB layout](https://suddendocs.samtec.com/prints/bcs-1xx-xxx-x-xx-xxx%20footprint.pdf)
- Samtec test reports — [design qualification 187544 (L vs S gold)](https://suddendocs.samtec.com/testreports/187544_report_rev_1_qua.pdf) · [BCS E.L.P. extended durability](https://suddendocs.samtec.com/testreports/bcs_elp.pdf) · [SSM/TSM 2 500-cycle report](https://suddendocs.samtec.com/testreports/302828_report_rev_1_qua.pdf)
- Samtec **TSW / HTSW** (accessory-side mate) — [catalogue page (PDF)](https://suddendocs.samtec.com/catalog_english/tsw_th.pdf)
- Samtec — [E.L.P. High Mating Cycle Connectors](https://www.samtec.com/high-speed-board-to-board/high-density-arrays/elp/) · [Calculating mating and un-mating forces](https://suddendocs.samtec.com/notesandwhitepapers/mating_and_unmating_forces.pdf)
- Digi-Key — [BCS-112 lifecycle and ratings](https://www.digikey.com/en/products/detail/samtec-inc/BCS-112-L-D-PE/1100209)
- Harwin — `M20-7881242` product page returns **HTTP 404** (`https://www.harwin.com/products/M20-7881242`); [M20 series catalogue](https://shop.sibalco.ch/cust/files/Harwin_M20_3623.pdf)
- Read only, in-repo: `audits/2026-08-23-community-expansion-closeout.md` · `docs/full-beta-v2/CTO_DECISIONS.md` · `docs/full-beta-v2/architecture/ARCHITECTURE.md` · `docs/full-beta-v2/mechanical/MECHANICAL_INTERFACE_SPEC.md`
