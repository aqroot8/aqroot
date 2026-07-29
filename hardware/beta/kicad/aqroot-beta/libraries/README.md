# AQROOT Beta — project KiCad library

Project-specific symbol and footprint library for the AQROOT Beta main board.

```
libraries/
├── AQROOT_Beta.kicad_sym          symbols
├── AQROOT_Beta.pretty/            footprints
│   └── Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270.kicad_mod
└── README.md                      this file
```

Intended library nickname: **`AQROOT_Beta`** (both symbol and footprint library).

> The library is **already registered** in the project's `sym-lib-table` and
> `fp-lib-table` under the nickname `AQROOT_Beta` — see
> [Registration](#registration). Nothing to do before using it.

---

## Contents

| Part | Symbol | Footprint |
|---|---|---|
| Bosch Sensortec BMI270 | `BMI270` | `Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270` |
| Vishay TSOP38238 | `TSOP38238` | `Vishay_TSOP382xx_Minicast_3Pin_P2.54mm` |
| Vishay TSAL6200 | *(none — use stock `Device:LED`)* | *(none — use stock `LED_THT:LED_D5.0mm`)* |

See [TSAL6200](#tsal6200--recommended-kicad-symbol-and-footprint) for why that part
deliberately has no custom library entry.

---

## Source of authority

### BMI270

The BMI270 symbol and footprint are derived from a single document:

| | |
|---|---|
| Document | **BMI270 Datasheet** |
| Document number | **BST-BMI270-DS000-08** |
| Revision | 1.6 |
| Release date | March 2026 |
| Publisher | Bosch Sensortec GmbH |
| URL | <https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf> |

Sections used:

| Section | Used for |
|---|---|
| §6.2 Table 17, §6.3 | Primary interface mapping, protocol selection (CSB strap) |
| §6.5 | I²C address and SDO address strap |
| §7.1 Table 22 | Pin numbers, pin names, I/O types, interface assignment |
| §7.2.3 | I²C connection diagram, decoupling recommendation |
| §8.1 | Package outline dimensions, metallized pad detail |
| §8.3 | Landing pattern recommendation |

### TSOP38238 and TSAL6200

| | TSOP38238 | TSAL6200 |
|---|---|---|
| Document | IR Receiver Modules for Remote Control Systems | High Power Infrared Emitting Diode, 940 nm |
| Covers | TSOP382.., TSOP384.. | TSAL6200 |
| Document number | **82491** | **81010** |
| Revision | **Rev. 2.1, 27-May-2025** | **Rev. 2.4, 13-Mar-2014** |
| Package drawing | 6.550-5263.01-4, issue 12, 16.04.10 | 6.544-5259.06-4, issue 6, 19.05.09 |
| URL | <https://www.vishay.com/docs/82491/tsop382.pdf> | <https://www.vishay.com/docs/81010/tsal6200.pdf> |

Supporting Vishay documents consulted (not used for any dimension): **80121**
"Marking on IR Receiver Modules" rev. 3.7, and **81638** "Minicast IR Receiver
Packaging Options". Neither adds pin-orientation data beyond the datasheet.

### Provenance rule

**No SnapEDA / SnapMagic, Ultra Librarian, Octopart, vendor-portal or community
library was used as a design authority**, and none was consulted to fill gaps.
Every number below traces to one of the sections above.

§8.1 and §8.3 are raster images inside the PDF with no extractable text. The
dimension callouts were read directly from the rendered drawings, and the pad
geometry was additionally recovered by measuring the drawing's own vector/raster
geometry and calibrating against its labelled 3.0 mm and 2.5 mm body dimensions.
The reconstructed footprint agrees with the drawing to a worst-case **19 µm**
(all pad *positions* within 8 µm), against Bosch's stated pad tolerance of
±50 µm. See [Footprint derivation](#footprint-derivation).

---

## Symbol — `BMI270`

| Field | Value |
|---|---|
| Reference prefix | `U` |
| Value | `BMI270` |
| Footprint | `AQROOT_Beta:Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270` |
| Manufacturer | Bosch Sensortec |
| MPN | BMI270 |
| Description | 6-axis IMU, I2C/SPI, 14-pin LGA, 2.5 x 3.0 mm |
| Datasheet | Bosch URL above |

All **14 physical package pins appear exactly once**. There are **no hidden power
pins** — `VDD`, `VDDIO`, `GND` and `GNDIO` are visible pins that must be wired
explicitly in the schematic.

The package has **no centre pad, no exposed pad and no thermal pad**. §8.1
"BOTTOM VIEW" shows 14 peripheral terminals only. The small metallized
0.250 × 0.090 mm feature at the pin-1 corner in §8.1 is a **pin-1 index marking,
not an electrical terminal** — Bosch's §8.3 landing pattern draws it in grey
(marker) rather than red (copper land) and specifies no land for it. It is
therefore **not** a pad in this footprint and **not** a pin in this symbol.

### Pin table

| Physical pin | Bosch pin name | Symbol pin name | Electrical type | Notes |
|---|---|---|---|---|
| 1 | SDO | `SDO` | Bidirectional | Table 22 "Digital I/O". SPI-4W serial data **output**, *and* I²C address bit-0 select **input**. Multiplexed — deliberately **not** typed as Output. |
| 2 | ASDx | `ASDx` | Bidirectional | Table 22 "Digital I/O", secondary interface. Aux I²C SDA (open-drain) or OIS SDI. |
| 3 | ASCx | `ASCx` | Bidirectional | Table 22 "Digital I/O", secondary interface. Aux I²C SCL (push-pull out) or OIS SCK (in). Multiplexed direction. |
| 4 | INT1 | `INT1` | Bidirectional | Table 22 "Digital I/O". Interrupt output, but §7.1 note \* allows configuration as **input** for external FIFO data sync. Not typed as Output. |
| 5 | VDDIO | `VDDIO` | Power input | Digital I/O supply, 1.2 … 3.6 V. |
| 6 | GNDIO | `GNDIO` | Power input | Ground for I/O. |
| 7 | GND | `GND` | Power input | Ground for digital & analog. |
| 8 | VDD | `VDD` | Power input | Analog & digital supply, 1.71 … 3.6 V. |
| 9 | INT2 | `INT2` | Bidirectional | Table 22 "Digital I/O". Same reasoning as INT1. |
| 10 | OCSB | `OCSB` | Input | Table 22 "Digital in". OIS interface chip select. |
| 11 | OSDO | `OSDO` | Tri-state | Table 22 "Digital out". OIS SPI slave data output. See [interpretation note](#electrical-type-interpretations). |
| 12 | CSB | `CSB` | Input | Table 22 "Digital in". SPI chip select; strapped to VDDIO to select I²C. Has an internal 75/100/140 kΩ pull-up to VDDIO (Table 18). |
| 13 | SCx | `SCx` | Input | Table 22 "Digital in". SPI SCK / I²C SCL. |
| 14 | SDx | `SDx` | Bidirectional | Table 22 "Digital I/O". I²C SDA, SPI-4W SDI, SPI-3W SDA. |

Pin names are **Bosch's names verbatim** from Table 22 (`SDx`/`SCx`/`ASDx`/`ASCx`
retain Bosch's lower-case `x` placeholder). The symbol encodes **no AQROOT net
names** — see [AQROOT connection intent](#aqroot-connection-intent) for those.

### Pin grouping in the symbol

| Group | Side | Pins |
|---|---|---|
| Power | top | `VDD` (8), `VDDIO` (5) |
| Ground | bottom | `GND` (7), `GNDIO` (6) |
| Primary interface | left, upper | `SDx` (14), `SCx` (13), `CSB` (12), `SDO` (1) |
| Interrupts | left, lower | `INT1` (4), `INT2` (9) |
| Auxiliary interface | right, upper | `ASDx` (2), `ASCx` (3) |
| OIS / secondary interface | right, lower | `OCSB` (10), `OSDO` (11) |

`SDO` is grouped with the primary interface because that is its primary-interface
role (Table 17 lists it under the primary interface mapping); its secondary role
is the I²C address strap, which is also a primary-interface concern.

`ASDx`/`ASCx` are shared between the auxiliary I²C master interface and the OIS
SPI interface — Bosch documents them as one multiplexed pin pair, so they appear
once, in the auxiliary group.

### Electrical type interpretations

Two choices are interpretations rather than verbatim datasheet statements. Both
are recorded here so they can be reviewed:

1. **`OSDO` (pin 11) typed Tri-state, not Output.** Table 22 says "Digital out".
   It is the data output of the OIS **SPI slave**, enabled by `OCSB`. Tri-state
   is the conservative KiCad type for a bus-attached slave output: it will not
   raise a false ERC output-conflict if the net is shared, whereas Output would.
   The datasheet does not explicitly use the words "high impedance" for this pin.
2. **`ASCx` (pin 3) typed Bidirectional.** In aux-master mode §7.1 note \*\* says
   it "operates in push/pull-mode" (an output); in OIS mode it is `OIS SCK`
   (an input). Bidirectional is the only type that is not wrong in one of the two
   documented modes.

Everything else follows Table 22's I/O Type column directly.

---

## Footprint — `Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270`

The footprint **was created**, because §8.3 gives a complete landing pattern:
pad size, pad pitch, and both in-plane locating dimensions are all explicitly
labelled, and §8.1 independently confirms the pad sizes and the pitch.

Name follows the datasheet's own description of the part — "compact standard size
LGA mold package, 14 pins, footprint 2.5x3.0mm², height 0.83mm" — so `2.5x3.0mm`
is E × D. In the KiCad footprint's own orientation the body is **3.0 mm in X and
2.5 mm in Y**.

### Package-view convention

* The footprint is drawn in **top view**, which is KiCad's required convention
  (looking down at the board, `F.Cu` toward the viewer).
* Bosch's §8.3 landing pattern is itself already drawn in top view: its pad
  ordering (1–4 down the left, 5–7 left-to-right along the bottom, 8–11 up the
  right, 12–14 right-to-left along the top) matches the §7.1 **"Pin-out top
  view"** diagram exactly, and is the mirror of the §7.1 "Pin-out bottom view".
  Land patterns are PCB copper, so this is expected. **No mirroring was applied.**
* **Pin 1 is at the upper left**, at X = −1.1625 mm, Y = −0.75 mm.
* Pin numbering runs **counter-clockwise** as viewed from the top, which is the
  standard convention and matches Bosch's drawings.
* Pin 1 is marked on `F.SilkS` (L-shaped corner mark outside the body at the
  upper-left) and on `F.Fab` (0.5 mm chamfer on the upper-left corner of the
  body outline).

### Pad table

Origin is the package centre, i.e. the intersection of the two dash-dot
centrelines in §8.3. Units mm.

| Pad | X | Y | Size (X × Y) | Shape | Layers |
|---|---|---|---|---|---|
| 1 | −1.1625 | −0.75 | 0.475 × 0.25 | rect | F.Cu, F.Mask, F.Paste |
| 2 | −1.1625 | −0.25 | 0.475 × 0.25 | rect | F.Cu, F.Mask, F.Paste |
| 3 | −1.1625 | 0.25 | 0.475 × 0.25 | rect | F.Cu, F.Mask, F.Paste |
| 4 | −1.1625 | 0.75 | 0.475 × 0.25 | rect | F.Cu, F.Mask, F.Paste |
| 5 | −0.5 | 0.9125 | 0.25 × 0.475 | rect | F.Cu, F.Mask, F.Paste |
| 6 | 0 | 0.9125 | 0.25 × 0.475 | rect | F.Cu, F.Mask, F.Paste |
| 7 | 0.5 | 0.9125 | 0.25 × 0.475 | rect | F.Cu, F.Mask, F.Paste |
| 8 | 1.1625 | 0.75 | 0.475 × 0.25 | rect | F.Cu, F.Mask, F.Paste |
| 9 | 1.1625 | 0.25 | 0.475 × 0.25 | rect | F.Cu, F.Mask, F.Paste |
| 10 | 1.1625 | −0.25 | 0.475 × 0.25 | rect | F.Cu, F.Mask, F.Paste |
| 11 | 1.1625 | −0.75 | 0.475 × 0.25 | rect | F.Cu, F.Mask, F.Paste |
| 12 | 0.5 | −0.9125 | 0.25 × 0.475 | rect | F.Cu, F.Mask, F.Paste |
| 13 | 0 | −0.9125 | 0.25 × 0.475 | rect | F.Cu, F.Mask, F.Paste |
| 14 | −0.5 | −0.9125 | 0.25 × 0.475 | rect | F.Cu, F.Mask, F.Paste |

### Footprint derivation

Every coordinate above comes from a labelled dimension:

| Datasheet value | Where | How it is used |
|---|---|---|
| **0.475** | §8.3, dimensioned across pad 11; §8.1 metallized pad detail | Pad long dimension |
| **0.25** | §8.3, dimensioned down pad 11; §8.1 metallized pad detail | Pad short dimension |
| **0.5** | §8.3, pad 1 centre → pad 2 centre; §8.1 `e = 0.50 BSC` | Pad pitch, both columns and both rows |
| **0.925** | §8.3, vertical centreline → **inner edge** of the side-column pads | Side pad centre X = ±(0.925 + 0.475/2) = **±1.1625** |
| **0.675** | §8.3, horizontal centreline → **outer-facing top edge** of the bottom-row pads | Row pad centre Y = ±(0.675 + 0.475/2) = **±0.9125** |
| **3.0** | §8.3 overall; §8.1 `D` nom 3.00 | Body outline X, `F.Fab` |
| **2.5** | §8.3 overall; §8.1 `E` nom 2.50 | Body outline Y, `F.Fab` |
| **0.250 × 0.475** and **0.475 × 0.250** | §8.1 metallized pad detail | Independent confirmation that the row pads are the side pads rotated 90° |

Two consistency checks that the reconstruction passes:

* The pad field is symmetric about both centrelines, and the outermost pad edge
  sits **0.1 mm inside the body outline on all four sides** (X: 1.1625 + 0.2375 =
  1.4 vs D/2 = 1.5; Y: 0.9125 + 0.2375 = 1.15 vs E/2 = 1.25).
* The row pitch of 0.5 mm implied by pads 5/6/7 at X = −0.5, 0, +0.5 matches
  §8.1 `D1 = 1.00 BSC` (pad 14 centre to pad 12 centre) and `e = 0.50 BSC`.

Note that §8.3 draws the landing pads at exactly the §8.1 **metallized pad**
dimensions — Bosch specifies **no land expansion or reduction** relative to the
package terminals.

### Engineering choices not specified by Bosch

The datasheet gives no courtyard, silkscreen, solder-mask or solder-paste data.
These are the footprint's own choices, flagged so they are not mistaken for
datasheet values:

| Item | Value | Rationale |
|---|---|---|
| `F.CrtYd` | rectangle ±1.75 × ±1.50 mm, 0.05 mm line | Nominal body outline + 0.25 mm, IPC-7351 "nominal" density courtyard excess. Also clears the §8.1 **maximum** body (D max 3.05, E max 2.55) by ≥0.225 mm. |
| Solder mask | **no per-pad override** | Bosch specifies none. The pads inherit the board's global mask expansion so the stackup stays under one setting. Do not add a local override without a fab-driven reason. |
| Solder paste | **no per-pad override** — 1:1 apertures | Bosch specifies none. LGA terminals of 0.475 × 0.25 mm at 0.1 mm standoff (`A1` nom 0.13) are conventionally pasted 1:1; reduce only if your assembler asks. |
| `F.SilkS` | pin-1 corner mark only | The pads reach to within 0.1 mm of the body outline, so a silk body outline cannot be drawn without violating silk-to-mask clearance. Only the pin-1 mark is placed, outside the body. |
| `F.Fab` chamfer | 0.5 mm, upper-left | Standard KiCad pin-1 indication. |
| Pad shape | `rect` | §8.3 draws plain rectangles with square corners. |

**No 3D model is referenced.** Bosch does not publish a STEP/WRL model in this
datasheet and none was invented. The footprint has no `model` block; add one
later if a model is obtained from an authoritative source.

Format note: the files are written with symbol format `20241209` and footprint
format `20241229`. KiCad 10 reads these natively and will migrate them to its own
format version the first time you save from the library editors.

---

## Symbol — `TSOP38238`

| Field | Value |
|---|---|
| Reference prefix | `U` |
| Value | `TSOP38238` |
| Footprint | `AQROOT_Beta:Vishay_TSOP382xx_Minicast_3Pin_P2.54mm` |
| Manufacturer | Vishay |
| MPN | TSOP38238 |
| Description | 38 kHz IR remote-control receiver module |
| Datasheet | <https://www.vishay.com/docs/82491/tsop382.pdf> |

All **3 physical pins appear exactly once**, with **no hidden pins**. Pin names are
Vishay's verbatim from the "MECHANICAL DATA / Pinning" statement: `1 = OUT, 2 = GND,
3 = VS`.

### Pin table

| Physical pin | Vishay name | Symbol name | Electrical type | Notes |
|---|---|---|---|---|
| 1 | OUT | `OUT` | Open collector | Demodulated, **active-low** output. The BLOCK DIAGRAM shows an NPN with its collector on pin 1, emitter to pin 2, and an internal **30 kΩ pull-up to VS**. Open collector is the exact KiCad type: it can pull low but only weakly pulls high, and it will not raise a false ERC output conflict if wire-OR'd. |
| 2 | GND | `GND` | Power input | Ground. |
| 3 | VS | `VS` | Power input | Supply, 2.0 V to 5.5 V. |

Symbol layout: `VS` on top, `GND` on the bottom, `OUT` on the right. The symbol
encodes **no AQROOT net names**.

---

## Footprint — `Vishay_TSOP382xx_Minicast_3Pin_P2.54mm`

The footprint **was created**. The Vishay drawing gives the body envelope, the lead
pitch and the lead cross-section, which is everything a 3-lead inline through-hole
land pattern needs.

Named for the package family rather than the single part: drawing 6.550-5263.01-4
covers the whole TSOP382../TSOP384.. Minicast range, so the same footprint serves
any TSOP382xx/TSOP384xx. `P2.54mm` records the pitch explicitly.

### Package-view convention

* The footprint is drawn in **top view**, as KiCad requires — looking down at the
  board with the part standing upright on it, `F.Cu` toward the viewer.
* In this top view the **lens/dome faces −Y** and the **flat marking face faces +Y**.
* **Pin 1 (OUT) is at −X (left)**, pin 2 (GND) at the centre, pin 3 (VS) at +X.
* Equivalent statement in Vishay's own terms: viewed from the **front — the lens
  side — with the leads pointing down, the pins read 1‑2‑3 left to right**, i.e.
  OUT on the left. Viewed from the **rear (marking) side** they read 3‑2‑1.

The only pin-numbered figure Vishay publishes is the isometric on page 2; the
orthographic package drawing on page 7 carries no pin numbers, and docs 80121 and
81638 add none. Rather than eyeball the isometric, the orientation was derived from
the drawing's vector geometry: the three projected axes are at 30°, 150° and
vertical, the pin 1→3 label axis lies on the 30° axis, the leads on the 150° axis and
the dome on the vertical axis, and the visible faces place the viewer in the
(+width, +lead, +lens) octant. For a standard isometric from that octant the axes in
counter-clockwise screen order are a cyclic permutation of a right-handed triad,
which fixes the handedness and hence the pin-1 side. See
[Reproducing the orientation check](#reproducing-the-orientation-check).

### Pad table

| Pad | X | Y | Drill | Pad size | Shape | Layers |
|---|---|---|---|---|---|---|
| 1 (OUT) | −2.54 | 0 | Ø1.1 | Ø1.8 | rect | \*.Cu, \*.Mask |
| 2 (GND) | 0 | 0 | Ø1.1 | Ø1.8 | circle | \*.Cu, \*.Mask |
| 3 (VS) | 2.54 | 0 | Ø1.1 | Ø1.8 | circle | \*.Cu, \*.Mask |

Pad 1 is rectangular — the standard KiCad pin-1 indication in copper.

### Which numbers are Vishay's, and which are allowances

Straight from document 82491 (drawing 6.550-5263.01-4):

| Value | Meaning |
|---|---|
| **2.54 nom.** | Lead pitch → pads at X = −2.54, 0, +2.54 |
| **5** | Body width → F.Fab X = ±2.5 |
| **4.8** | Body depth incl. dome → F.Fab spans Y = +1.4 … −3.4 |
| **2.8** | Depth of the rectangular block before the dome → block front face at Y = −1.4 |
| **R 2** and **(4)** | Dome radius, and its 4 mm span (= 2R) → dome arc from (−2, −1.4) through (0, −3.4) to (2, −1.4) |
| **1.2 ± 0.2** | Rear face → **rear edge** of the lead. With the 0.5 max lead thickness this puts the lead *centre* 1.4 mm from the rear face, which is where the pad row sits |
| **0.7 max** | Lead width |
| **0.5 max** | Lead thickness |
| **6.95 ± 0.3** | Body height above the seating plane (not represented in a 2D footprint) |

Derived, **not** Vishay values — ordinary manufacturing allowances:

| Item | Value | Basis |
|---|---|---|
| Drill | **Ø1.1 mm** | Worst-case lead diagonal √(0.7² + 0.5²) = 0.86 mm, plus 0.25 mm IPC-7251 nominal-density lead-to-hole clearance |
| Pad diameter | **Ø1.8 mm** | Drill + 0.7 mm → 0.35 mm annular ring. Leaves 0.74 mm copper gap between adjacent pads at 2.54 pitch |
| `F.CrtYd` | X ±3.75, Y −3.65 … +1.75 | Body-and-pad extents + 0.25 mm |
| `F.SilkS` | Body outline offset 0.15 mm outward, broken either side of the pads | Keeps silk off pad copper |
| `F.Fab` chamfer | 0.6 mm on the rear-left corner | Pin-1 indication |

The lead row is **centred on the 5 mm body width** — confirmed by measuring the
drawing's vector geometry, where the body edges sit at ±2.50 and the outer lead
centres at ±2.54, i.e. the outer leads are flush with (0.04 mm proud of) the body
sides.

**No 3D model is referenced.** Vishay publishes none in this datasheet and none was
invented.

### Reproducing the orientation check

Both Vishay drawings are pure vector art (no raster), so the derivation above is
reproducible. Extract the page-2 isometric line segments, histogram their directions
weighted by length, and you get exactly three axes — 150° (the leads, dominant
because of the six long lead lines), 30° and 90°. The pin labels `1`, `2`, `3` sit at
(85.8, 222.6), (97.4, 228.8) and (108.8, 236.2) in PDF points, so the 1→3 axis is
atan2(13.6, 23.0) = 30.6° — the 30° axis. That is the whole input to the handedness
argument.

---

## TSAL6200 — recommended KiCad symbol and footprint

**No custom symbol or footprint was created for the TSAL6200, and none is needed.**

### Recommendation

| | Use |
|---|---|
| Symbol | **`Device:LED`** — set Value to `TSAL6200`, and add `Manufacturer` = Vishay, `MPN` = TSAL6200 |
| Footprint | **`LED_THT:LED_D5.0mm`** |

### Why the generic symbol is sufficient

The TSAL6200 is a two-terminal emitting diode. `Device:LED` has exactly two pins,
`K` (1) and `A` (2), which is unambiguous — there is no third terminal, no polarity
convention to get wrong, and nothing the generic symbol could misrepresent. Creating
a custom symbol would add a maintenance burden and a second place for the pin
mapping to drift, with no gain. Setting Value/MPN removes any BOM ambiguity.

The one thing to be aware of: `Device:LED` draws a *visible-light* LED glyph. That is
cosmetic. If you want the schematic to read unmistakably as an emitter, add a text
note on the IR sheet rather than forking the symbol.

### Package and polarity, from document 81010

| Item | Value |
|---|---|
| Package form | **T-1¾** (5 mm) |
| Body diameter | **Ø5 ± 0.15** |
| Rim/flange diameter | Ø5.8 ± 0.15 |
| Lead spacing | **2.54 nom.** |
| Lead cross-section | **0.5 +0.15/−0.05 mm square** |
| Dome | R 2.49 (sphere) |
| Body height | 8.7 ± 0.3; total length 34.3 ± 0.55 |
| Polarity | The package-dimensions top view labels the two leads **`A` (anode) and `C` (cathode)**, and the cathode side carries the **flat** on the rim. Cathode is also the **shorter** lead. |

`LED_D5.0mm` is a Ø5.0 mm body at 2.54 mm pitch, which matches the drawing.

### One thing to verify in your KiCad install

KiCad was not available on the machine that authored this library, so
`LED_THT:LED_D5.0mm` could not be opened and measured. Check its **drill diameter**
before fabrication:

* worst-case TSAL6200 lead is 0.65 mm square → diagonal **0.92 mm**;
* the stock footprint is expected to use a 0.9 mm drill, which is marginally under
  that worst case.

If it is 0.9 mm, either accept it (real leads are ~0.5 mm square and 0.9 mm is the
long-standing convention for 5 mm LEDs) or copy the footprint into
`AQROOT_Beta.pretty` and open the drill to **1.0 mm**. Do not change the stock
library in place. Nothing else about the stock footprint needs review.

---

## AQROOT connection intent

**This section is documentation only.** None of it is encoded in the symbol — the
symbol carries Bosch pin names and nothing project-specific, so it stays reusable.
Wire the following in the schematic sheet, not in the library.

Target configuration: **bare BMI270 IC, primary interface I²C, slave address 0x68**
(matches the Alpha-validated behaviour).

### Power

| Bosch pin | AQROOT net | Note |
|---|---|---|
| 8 `VDD` | `+3V3` | 100 nF decoupling to `GND`, close to pin 8 (§7.2 recommendation) |
| 5 `VDDIO` | `+3V3` | 100 nF decoupling to `GND`, close to pin 5 (§7.2 recommendation) |
| 7 `GND` | `GND` | |
| 6 `GNDIO` | `GND` | |

Both supplies are within range at 3.3 V (`VDD` 1.71–3.6 V, `VDDIO` 1.2–3.6 V).
§6.3 notes power-on reset only completes once **both** rails are established, so
tying them to the same rail removes any protocol-detection sequencing risk.

### Primary I²C

| Bosch pin | AQROOT net |
|---|---|
| 14 `SDx` | `I2C_SDA_INT` |
| 13 `SCx` | `I2C_SCL_INT` |

Bus pull-ups are a **bus-level** concern on the shared internal I²C bus, not a
per-device one — do not add a second set of pull-ups at the IMU.

### Required straps

These two are **not optional** for the intended configuration:

| Bosch pin | Strap | Why |
|---|---|---|
| 12 `CSB` | **tie hard to `+3V3` (VDDIO)** | §6.3: the protocol is auto-selected from CSB behaviour after power-up; "For using I2C, it is recommended to hard-wire the CSB line to VDDIO." Any rising edge on CSB after power-up switches the part to SPI until the next reset. Table 17 lists `VDDIO` as the I²C connection for pin 12. |
| 1 `SDO` | **tie to `GND`** | §6.5: "The default I²C address of the device is 0b1101000 (**0x68**). It is used if the SDO pin is pulled to 'GND'." Pulling SDO to VDDIO instead selects 0x69. Table 17: "GND for default I2C addr." |

Leaving `CSB` floating is possible in principle (internal 75–140 kΩ pull-up to
VDDIO, §7.1 note \*\*\*\*) but Bosch explicitly does **not** recommend it. Strap it.

Do not leave `SDO` floating — the address would be undefined.

### Interrupts

| Bosch pin | AQROOT net | Note |
|---|---|---|
| 4 `INT1` | `BMI270_INT1_RAW` → series **100–470 Ω** → `BMI270_INT1_STRAP` / ESP32 `GPIO3` | Series resistor is an AQROOT requirement, not a Bosch one: `GPIO3` is an ESP32-S3 strapping pin sampled at reset, and the IMU can assert INT1 asynchronously. The resistor limits contention current so the strap can still be held by the board. Configure INT1 open-drain in the IMU where the required interrupt mode allows it. |
| 9 `INT2` | **unused — leave unconnected (DNC)** | §7.1 note \*: "If INT1 and/or INT2 are not used, please do not connect them (DNC)." Do not tie to a rail. Route to a test point only if a second interrupt is later assigned. |

### Auxiliary and OIS interfaces — unused

Both secondary interfaces are unused in AQROOT Beta, but they are **not
"don't care"** — Bosch constrains the allowed idle states:

| Bosch pin | Required state when unused | Authority |
|---|---|---|
| 2 `ASDx` | Tie to `+3V3` (VDDIO) **or** leave unconnected. **Must NOT be tied to GND.** | §7.1 note \*\* |
| 3 `ASCx` | Tie to `+3V3` (VDDIO) **or** leave unconnected. **Must NOT be tied to GND.** | §7.1 note \*\* |
| 10 `OCSB` | Leave unconnected (DNC). May be tied to `GND` **only if** `IF_CONF.ois_en = 0`. | §7.1 note \*\*\* |
| 11 `OSDO` | Leave unconnected (DNC). May be tied to `GND` **only if** `IF_CONF.ois_en = 0`. | §7.1 note \*\*\* |

Recommended for AQROOT: tie `ASDx` and `ASCx` to `+3V3`, and leave `OCSB` and
`OSDO` unconnected. That satisfies every note above without depending on a
firmware register value being correct at power-up.

Add `no_connect` flags in the schematic on `INT2`, `OCSB` and `OSDO` so ERC stays
clean and the intent is explicit.

---

### IR receiver — TSOP38238

| Vishay pin | AQROOT net | Note |
|---|---|---|
| 3 `VS` | `+3V3` **through local supply filtering** | Well within the 2.0–5.5 V range. Vishay's application circuit shows a series **R1** and shunt **C1** at VS, noting they are "recommended in case there are strong ripple or spikes on the supply line" — which is exactly the case here, since the IR **emitter** pulses hundreds of mA off the same board. Fit the RC. |
| 2 `GND` | `GND` | |
| 1 `OUT` | `IR_RX_GPIO44` | Active low, open collector with an internal 30 kΩ pull-up to VS. No external pull-up is required. GPIO44 is U0RXD — an input at boot — so ROM boot-log traffic on the UART cannot be driven into this output. |

**Placement is a schematic-and-layout requirement, not a wiring one:** keep the
receiver **physically separated from the TSAL6200 and outside the emitter's direct
emission cone**. The TSOP has AGC and will happily desensitise itself, or latch on
its own board-coupled reflection, if it can see the emitter. Separation plus the VS
RC filter are the two mitigations.

### IR emitter — TSAL6200

Driven **only** through a low-side N-channel MOSFET — never directly from a GPIO.

```
GPIO16 ──[ gate series R ]──┬── MOSFET gate
                            │
                        [ gate pull-down R ]
                            │
                           GND

MOSFET source ── GND
MOSFET drain  ── TSAL6200 cathode (K)
TSAL6200 anode (A) ──[ current-limit R ]── IR LED supply rail
```

| Net | Connection |
|---|---|
| `IR_TX_GPIO16` | → gate series resistor → MOSFET gate |
| gate | → pull-down resistor → `GND` (float protection during reset / power sequencing) |
| MOSFET source | `GND` |
| MOSFET drain | TSAL6200 **cathode** |
| TSAL6200 **anode** | → current-limit resistor → selected IR LED supply rail |

**Deliberately not chosen in this task, and deliberately not encoded anywhere in the
library:** the MOSFET part, the gate series and pull-down resistor values, the
current-limit resistor value, the IR LED supply rail, and the pulse current. Those
are a driver-design decision that depends on the target range and duty cycle.

Note the polarity direction: the MOSFET switches the **cathode**, so the LED's anode
sits at the supply and the `Device:LED` symbol's pin 1 (`K`) goes to the drain.

### Firmware note

The BMI270 requires a multi-kilobyte configuration blob to be uploaded after
power-up before accel/gyro data is valid. Register-level access alone will not
produce motion data. This is a firmware concern, recorded here only because it
routinely surprises people probing a correctly wired part.

---

## Registration

The library is registered in the **project-specific** tables, both under the
nickname `AQROOT_Beta`:

| File | Entry |
|---|---|
| `../sym-lib-table` | `(lib (name "AQROOT_Beta")(type "KiCad")(uri "${KIPRJMOD}/libraries/AQROOT_Beta.kicad_sym")…)` |
| `../fp-lib-table` | `(lib (name "AQROOT_Beta")(type "KiCad")(uri "${KIPRJMOD}/libraries/AQROOT_Beta.pretty")…)` |

`${KIPRJMOD}` resolves to the directory holding `aqroot-Beta.kicad_pro`, so both
paths are relative to the project and the repository stays portable — no absolute
paths, and no dependency on any one machine's KiCad configuration.

Using the same nickname for both tables is what makes each symbol's `Footprint`
field resolve — `AQROOT_Beta:Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270` and
`AQROOT_Beta:Vishay_TSOP382xx_Minicast_3Pin_P2.54mm`.

Project-specific tables are read **in addition to** your global tables, so this
adds `AQROOT_Beta` without hiding any stock KiCad library. If you happen to have a
*global* library already nicknamed `AQROOT_Beta`, KiCad will report a nickname
collision — rename the global one, not this project entry.

Contents exposed by the nickname:

| Symbols | Footprints |
|---|---|
| `AQROOT_Beta:BMI270` | `AQROOT_Beta:Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270` |
| `AQROOT_Beta:TSOP38238` | `AQROOT_Beta:Vishay_TSOP382xx_Minicast_3Pin_P2.54mm` |

Note that the library tables are deliberately **not** covered by the repository's
`.gitattributes` `-text` rule (which applies only to `*.kicad_*` files), so they
follow Git's normal end-of-line handling. That is intentional — see the comments in
`.gitattributes`.

---

## Verification before manufacture

This library was built from the datasheet without KiCad installed on the
authoring machine, so the following have **not** been run and should be done
before committing to fabrication:

- [ ] Open `AQROOT_Beta.kicad_sym` in the Symbol Editor — confirm **both** `BMI270`
      and `TSOP38238` load, and run the symbol checker on each.
- [ ] Open **both** footprints in the Footprint Editor and run the footprint checker.
- [ ] Confirm `LED_THT:LED_D5.0mm` drill vs the TSAL6200 lead — see
      [TSAL6200](#one-thing-to-verify-in-your-kicad-install).
- [ ] Confirm the TSOP38238 lens direction on the PCB matches `−Y` in the footprint,
      and that the emitter is outside its cone.
- [ ] Overlay the footprint against §8.3 at 1:1 print scale.
- [ ] Confirm pad 1 lands at the upper left with the part oriented as in §7.1's
      top view.
- [ ] Confirm the board's global solder-mask expansion suits a 0.25 mm-wide land
      with your fab.
