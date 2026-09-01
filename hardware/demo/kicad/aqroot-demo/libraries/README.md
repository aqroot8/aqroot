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
| Display module, ILI9341 + FT6236 | `ILI9341_FT6236_MODULE_PLACEHOLDER` | **none — deliberately unassigned** |
| Sub-GHz radio, CC1101 | `CC1101_RADIO_PLACEHOLDER` | **none — deliberately unassigned** |
| LoRa / sub-GHz module, SX1262 | `SX1262_MODULE_PLACEHOLDER` | **none — deliberately unassigned** |
| NFC reader front-end, ST25R3916 | `ST25R3916_NFC_PLACEHOLDER` | **none — deliberately unassigned** |

See [TSAL6200](#tsal6200--recommended-kicad-symbol-and-footprint) for why that part
deliberately has no custom library entry.

Four entries are **functional schematic placeholders** — they exist so their nets can
be drawn and ERC-checked before the physical implementation is chosen, and all are
excluded from the board (`on_board no`) because none has a footprint:

* [`ILI9341_FT6236_MODULE_PLACEHOLDER`](#symbol--ili9341_ft6236_module_placeholder)
* [`CC1101_RADIO_PLACEHOLDER`](#symbol--cc1101_radio_placeholder)
* [`SX1262_MODULE_PLACEHOLDER`](#symbol--sx1262_module_placeholder)
* [`ST25R3916_NFC_PLACEHOLDER`](#symbol--st25r3916_nfc_placeholder)

The last three are all **SPI Bus B** devices, sharing `SPI_B_SCK` / `SPI_B_MOSI` /
`SPI_B_MISO` with a chip select each.

> ### ⚠ Both radio implementations were SELECTED on 2026-08-07 — body graphics updated, fields still `TBD`
>
> | Radio | Decision | Closes |
> |---|---|---|
> | Sub-GHz CC1101 | **Ebyte E07-400M10S** — a module, **not** a bare IC | the module-vs-bare-IC question |
> | LoRa SX1262 | **Ebyte E22-900M22S** | the E22-vs-Core1262 question |
>
> See *Radio modules LOCKED* in [[05 - Design Decisions Log]] and
> [[12 - RF and Antenna Plan v0.1]].
>
> **Partially reconciled.** The **body graphic text** in both placeholder symbols has been
> rewritten to state the locked modules, in `AQROOT_Beta.kicad_sym` **and** in the matching
> `lib_symbols` cache inside `04_spi_b_radios_nfc.kicad_sch` — the two were edited together
> and verified identical, so the schematic's cached copy does not desync from the library.
>
> **Still NOT reconciled — these remain true descriptions of the symbols:** `TBD`
> manufacturer/MPN, `Datasheet` fields unchanged (CC1101 still points at TI's product page,
> SX1262 still blank), **no footprint**, and **`on_board no`**. Pin numbering is still the
> logical 1–8 / 1–10 placeholder order and **will** change. Statements below about *which*
> radio part AQROOT uses are now stale as decisions; statements about **fields, footprints,
> pins and `on_board`** remain accurate. See
> [Verification before manufacture](#verification-before-manufacture).
>
> **Nothing here unblocks routing.** The footprints still do not exist; they must be built
> from the Ebyte land-pattern drawings first, and `on_board` must stay `no` until they are.

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

### ILI9341_FT6236_MODULE_PLACEHOLDER

**No source of authority — deliberately.** No module has been selected, so there is
no datasheet, drawing or vendor document behind this symbol, and none was
substituted. It is derived only from AQROOT's own functional requirement (an
ILI9341 SPI LCD plus an FT6236 capacitive touch controller) and from the net names
already fixed in `11 - Beta Pin Map v0.2.md`. Nothing physical is claimed — see
[what the symbol does not claim](#what-this-symbol-deliberately-does-not-claim).

### CC1101_RADIO_PLACEHOLDER

**No source of authority for anything physical — deliberately.** The symbol's
`Datasheet` field points at TI's **product page**
(<https://www.ti.com/product/CC1101>) rather than a package datasheet, and that is a
deliberate distinction: the page identifies *which transceiver silicon* AQROOT
targets, without asserting that AQROOT uses the bare IC. The
[bare-IC-versus-module question is open](#the-central-open-question-module-or-bare-ic),
so **no** pin numbering, package, crystal, RF matching network, balun, filtering or
antenna interface was taken from that document or from anywhere else. The pins are
derived only from AQROOT's own SPI Bus B assignments in
`11 - Beta Pin Map v0.2.md`.

> **RESOLVED 2026-08-07 — module path, `E07-400M10S`.** The bare-IC path is dead, so the
> `Datasheet` field's careful silence about packaging has served its purpose: per the
> [rule below](#why-the-datasheet-field-does-not-imply-a-bare-ic), it should now be replaced
> with **Ebyte's E07-400M10S module document**, not TI's CC1101 datasheet. That is a symbol
> edit and has not been made. Everything above still describes the symbol as it stands.

### SX1262_MODULE_PLACEHOLDER

**No source of authority, and deliberately no datasheet reference at all.** The
`Datasheet` field is **blank** — unlike the CC1101 placeholder, which cites TI's
product page. The difference is deliberate: AQROOT uses a **certified SX1262
module**, not the bare Semtech IC, so linking Semtech's SX1262 silicon datasheet
would point at the wrong thing and invite exactly the bare-IC reading this symbol
must not carry. The module vendor is not chosen, so there is no vendor document to
cite either. Pin intent comes only from AQROOT's own SPI Bus B and expander
assignments in `11 - Beta Pin Map v0.2.md` §3 and §7.

> **RESOLVED 2026-08-07 — `E22-900M22S`.** A vendor document now exists to cite, so the
> reason the `Datasheet` field is blank has expired. It should be set to **Ebyte's
> E22-900M22S module document** — still never Semtech's SX1262 silicon datasheet, since the
> bare-IC reading this symbol must not carry is unchanged. Symbol edit, not yet made.

### ST25R3916_NFC_PLACEHOLDER

**The silicon is decided; nothing physical is.** The `Datasheet` field points at ST's
official **product page** (<https://www.st.com/en/nfc/st25r3916.html>), and
`Manufacturer`/`MPN` carry `STMicroelectronics` / `ST25R3916` — unlike the other
placeholders, the part itself is chosen, so recording it is honest and useful for
costing. What is **not** taken from ST, or from anywhere else, is any physical
detail: no package variant, no pin numbering, no crystal or reference network, no
decoupling scheme, no RF output or receiver network, no antenna. The MPN deliberately
carries **no package suffix**, because the package has not been selected. Pins are
derived from AQROOT's own SPI Bus B assignments in `11 - Beta Pin Map v0.2.md` §3
and the supply split recorded in §3's NFC level note.

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

## Symbol — `ILI9341_FT6236_MODULE_PLACEHOLDER`

| Field | Value |
|---|---|
| Reference prefix | `J` |
| Value | `ILI9341_FT6236_MODULE_PLACEHOLDER` |
| Footprint | **blank — deliberately unassigned** |
| Manufacturer | `TBD` |
| MPN | `TBD` |
| Description | Functional placeholder for AQROOT Beta 2.8-inch ILI9341 SPI LCD with FT6236 capacitive touch |
| Datasheet | **blank** — the exact module is not selected, so there is no datasheet to cite. The pin intent is documented here and in `11 - Beta Pin Map v0.2.md`. |

> **This symbol is a functional schematic placeholder only.** It exists so the
> display and touch nets can be drawn, named and ERC-checked before the physical
> module is chosen. It is **not** a part, **not** a connector, and **not** ready
> for layout.

### What this symbol deliberately does *not* claim

Nothing about the physical module was known when this symbol was written, and
nothing was invented to fill the gap. The symbol contains **no**:

* connector type, series, or manufacturer;
* connector pin count, pin numbering, or pin order;
* flex-cable / FPC / FFC pinout or pitch;
* module outline, dimensions, mounting holes or keep-outs;
* backlight electrical interface (drive current, LED string voltage, whether
  `LCD_BL_CTL` is a logic enable or a PWM input into an on-module driver);
* supply interface details (whether the module has its own regulator, its inrush,
  or its decoupling);
* level-shifting or on-module pull-up arrangement.

Every one of these is **unresolved** and must be settled against the selected
module before layout.

### Pin table

The **symbol pin numbers are logical indices, not connector pin numbers.** KiCad
requires every pin to carry a number, so pins are numbered 1–13 in the order below
purely to keep the symbol valid and its netlist stable. To make sure they are never
misread as a connector pinout, **pin numbers are hidden** in the symbol
(`(pin_numbers (hide yes))`). When the real module is selected, renumber to the
actual connector pinout — expect the numbers below to change.

| Symbol pin | Pin name | Electrical type | Intended AQROOT net |
|---|---|---|---|
| 1 | `VCC_3V3` | Power input | `+3V3` |
| 2 | `GND` | Power input | `GND` |
| 3 | `LCD_SCK` | Input | `SPI_A_SCK` |
| 4 | `LCD_MOSI` | Input | `SPI_A_MOSI` |
| 5 | `LCD_MISO` | Tri-state | `SPI_A_MISO` |
| 6 | `LCD_CS_N` | Input | `DISP_CS_N` |
| 7 | `LCD_DC` | Input | `DISP_DC` |
| 8 | `LCD_RST_N` | Input | `DISP_RST_N` |
| 9 | `LCD_BL_CTL` | Input | `DISP_BL_CTL` |
| 10 | `CTP_SDA` | Bidirectional | `I2C_SDA_INT` |
| 11 | `CTP_SCL` | Input | `I2C_SCL_INT` |
| 12 | `CTP_RST_N` | Input | `TOUCH_RST_N` |
| 13 | `CTP_INT_N` | Output | **no connect** — AQROOT polls the FT6236 |

All 13 pins are **visible**; there are no hidden pins. The **symbol encodes no
AQROOT net names** — the names above are functional pin names, and the net column
is documentation only. See
[Display module](#display-module--ili9341--ft6236-placeholder) for the wiring intent.

### Pin grouping in the symbol

| Group | Side | Pins |
|---|---|---|
| Supply | top | `VCC_3V3` |
| Ground | bottom | `GND` |
| LCD SPI + control | left | `LCD_SCK`, `LCD_MOSI`, `LCD_MISO`, `LCD_CS_N`, `LCD_DC`, `LCD_RST_N`, `LCD_BL_CTL` |
| Touch I²C + reset + interrupt | right | `CTP_SDA`, `CTP_SCL`, `CTP_RST_N`, `CTP_INT_N` |

The body carries a visible four-line graphic note:

```
FUNCTIONAL PLACEHOLDER
EXACT MODULE / CONNECTOR PENDING
DO NOT ASSIGN FOOTPRINT
DO NOT ROUTE
```

Pins are drawn with the plain `line` graphic style. Active-low pins are **not**
drawn with inversion bubbles — the `_N` suffix already carries the polarity, and
doubling it up reads as a double negative.

### Electrical type interpretations

| Pin | Choice | Why |
|---|---|---|
| `LCD_MISO` | **Tri-state**, not Output | SPI Bus A is shared with the microSD socket. Tri-state is the conservative KiCad type for a bus-attached slave output: it will not raise a false ERC output-conflict on the shared `SPI_A_MISO` net, whereas Output would. Same reasoning as `OSDO` on the BMI270. |
| `CTP_SDA` | **Bidirectional** | I²C data is genuinely bidirectional. |
| `CTP_SCL` | **Input** | The FT6236 is an I²C slave and never drives the clock; it has no documented clock-stretch behaviour that would need Bidirectional. |
| `CTP_INT_N` | **Output** | An interrupt line the module drives. Typed Output even though AQROOT does not use it, so that ERC flags any accidental attempt to drive it from the MCU side. |
| `LCD_BL_CTL` | **Input** | Typed as a logic input into the module. **This is an assumption of convenience, not a fact** — if the selected module exposes a raw backlight LED anode/cathode pair instead of a logic enable, this pin is wrong and the symbol must change. Flagged again in [what this symbol does not claim](#what-this-symbol-deliberately-does-not-claim). |

### Symbol flags

| Flag | Value | Why |
|---|---|---|
| `on_board` | **`no`** | With no footprint, this symbol must not reach the PCB. `on_board no` makes KiCad exclude it from the board, so "Update PCB from Schematic" cannot silently pull in a footprint-less part or invite routing. Flip to `yes` at the same time the real footprint is assigned. |
| `in_bom` | `yes` | The display module is a real purchased assembly. It stays in the BOM with `Manufacturer`/`MPN` = `TBD`, which is exactly the visibility this open item needs. |
| `exclude_from_sim` | `yes` | There is no simulation model for a placeholder. |
| `pin_numbers` | hidden | See [Pin table](#pin-table-2). |

**No footprint was created and none is assigned.** There is no
`AQROOT_Beta.pretty` entry for this part, and the symbol carries no `ki_fp_filters`
property — a footprint filter would imply a package family had been chosen, and
none has.

---

## Symbol — `CC1101_RADIO_PLACEHOLDER`

| Field | Value |
|---|---|
| Reference prefix | `U` |
| Value | `CC1101_RADIO_PLACEHOLDER` |
| Footprint | **blank — deliberately unassigned** |
| Manufacturer | `TBD` |
| MPN | `TBD` |
| Description | Functional placeholder for AQROOT built-in CC1101 sub-GHz radio |
| Datasheet | <https://www.ti.com/product/CC1101> — TI's **product page**, cited only to identify the target transceiver silicon. See [below](#why-the-datasheet-field-does-not-imply-a-bare-ic). |

> **This symbol is a functional schematic placeholder only.** It exists so the
> radio's SPI Bus B nets can be drawn, named and ERC-checked before the physical
> implementation is chosen. It is **not** a part, **not** a package, and **not**
> ready for layout.

**AQROOT Beta ships two radios: the CC1101 (sub-GHz) *and* the SX1262, together on
shared SPI Bus B.** This placeholder covers the CC1101 only. The SX1262 is a separate
subsystem with its own CS, `BUSY`, `DIO1` and reset lines and is not represented here.
Both radios sit on the same bus, so the CS discipline in
`11 - Beta Pin Map v0.2.md` §3 applies to both.

### The central open question: module or bare IC

**It is not yet decided whether AQROOT uses a certified CC1101 module or a bare
CC1101 IC**, and this symbol deliberately does not answer that. The two paths pull
in completely different board content:

| Path | What the main board must then carry |
|---|---|
| **Certified / pre-built module** | A module land pattern and keep-out, a defined module supply and control interface, and the module's own antenna interface. RF matching, crystal and filtering are inside the module. Certification may carry over. |
| **Bare CC1101 IC** | The IC package land pattern, **plus** the crystal and its loading, **plus** the RF matching / balun network, **plus** band filtering, **plus** an antenna interface — all of which must be designed, laid out under RF constraints, and certified from scratch. |

Until that decision is made, **nothing physical about this subsystem can be drawn**,
which is exactly why this symbol has no footprint and is excluded from the board.

> **CLOSED 2026-08-07 — the module path was chosen: Ebyte `E07-400M10S`.**
>
> The right-hand column of the table above is now void: the crystal and its loading, the RF
> matching / balun network, the band filtering and the antenna interface are all **inside the
> module** and none of them appears on the AQROOT main board. The 433 MHz antenna plugs onto
> the module's own IPEX port, so `CC1101_RF_TBD` does not terminate on our copper at all —
> see [[12 - RF and Antenna Plan v0.1]] §4.
>
> "Certification may carry over" in the left column is the one claim that does **not** simply
> transfer: the Beta antenna is not the module's stock antenna, and modifying a certified
> module's RF section can void its approval. Treat it as an open cert question, not a benefit
> already banked.
>
> **This unblocks drawing the subsystem; it does not mean it is drawn.** The symbol still has
> no footprint and is still `on_board no`. A real land pattern must be built from Ebyte's
> E07-400M10S drawing before anything physical is committed.

### What this symbol deliberately does *not* claim

The symbol contains **no**:

* choice between module and bare IC — see [above](#the-central-open-question-module-or-bare-ic);
* IC package or module land pattern, dimensions, keep-out or mounting;
* module or IC pin numbering, pin count, or pin order;
* crystal, load capacitors, or reference-frequency assumption;
* RF matching network, balun, or filtering topology or values;
* antenna connector type, series, or manufacturer, and no trace-antenna geometry;
* impedance target or RF stack-up assumption;
* operating band or regional band plan;
* supply decoupling or regulator arrangement.

Every one of these is **unresolved**.

### Why the `Datasheet` field does not imply a bare IC

The field is set to TI's product page, **not** to the CC1101 datasheet PDF and not to
any package drawing. The distinction is the point: the product page names the
transceiver AQROOT targets — which is genuinely decided — while a package datasheet
would be the authority for pin numbering and a land pattern, neither of which AQROOT
has committed to. Nothing was copied from TI into this symbol. If the module path is
chosen, replace this field with the module vendor's document; if the bare-IC path is
chosen, replace it with the CC1101 datasheet at that point, when the pinout it
specifies actually applies.

### Pin table

The **symbol pin numbers are logical indices, not IC or module pin numbers.** KiCad
requires every pin to carry a number, so pins are numbered 1–8 in the order below
purely to keep the symbol valid and its netlist stable. To make sure they are never
misread as a real pinout, **pin numbers are hidden** in the symbol
(`(pin_numbers (hide yes))`). Expect them all to change when the implementation is
selected.

| Logical pin | Name | Electrical type | Intended AQROOT net |
|---|---|---|---|
| 1 | `VCC_3V3` | Power input | `+3V3` |
| 2 | `GND` | Power input | `GND` |
| 3 | `SCK` | Input | `SPI_B_SCK` |
| 4 | `MOSI` | Input | `SPI_B_MOSI` |
| 5 | `MISO` | Tri-state | `SPI_B_MISO` |
| 6 | `CS_N` | Input | `CC1101_CS_N` |
| 7 | `GDO0` | Output | `CC1101_GDO0` |
| 8 | `RF_ANT` | Passive | `CC1101_RF_TBD` |

All 8 pins are **visible**; there are no hidden pins. The **symbol encodes no AQROOT
net names** — the names above are functional pin names, and the net column is
documentation only. See [Sub-GHz radio](#sub-ghz-radio--cc1101-placeholder) for the
wiring intent.

**`GDO2` is intentionally omitted.** It is not an oversight and not a pin that was
forgotten: `11 - Beta Pin Map v0.2.md` §3 records it as *"(removed) — optional;
dropped to free GPIO16"*. Adding it to this symbol would reintroduce a signal the pin
map has already spent, so it is absent. If a future firmware need brings it back, it
must go through the pin map first, not through this library.

### Pin grouping in the symbol

| Group | Side | Pins |
|---|---|---|
| Supply | top | `VCC_3V3` |
| Ground | bottom | `GND` |
| SPI + control | left | `SCK`, `MOSI`, `MISO`, `CS_N`, `GDO0` |
| RF | right | `RF_ANT` |

Keeping `RF_ANT` alone on the opposite side from the digital pins is deliberate — it
mirrors how the RF path must be kept away from the digital section in layout, and it
makes an accidental digital-to-RF connection visually obvious in the schematic.

The body carries a visible five-line graphic, **rewritten 2026-08-07** for the module lock:

```
FUNCTIONAL PLACEHOLDER
MODULE LOCKED: EBYTE E07-400M10S
NOT A BARE IC - ANTENNA ON MODULE IPEX
NO FOOTPRINT
DO NOT ROUTE
```

Pins use the plain `line` graphic style. `CS_N` is **not** drawn with an inversion
bubble — the `_N` suffix already carries the polarity.

### Electrical type interpretations

| Pin | Choice | Why |
|---|---|---|
| `MISO` | **Tri-state**, not Output | SPI Bus B is shared with the SX1262 and NFC. Tri-state is the conservative KiCad type for a bus-attached slave output: it will not raise a false ERC output-conflict on the shared `SPI_B_MISO` net, whereas Output would. Same reasoning as `OSDO` on the BMI270. |
| `CS_N` | **Input** | Chip select driven by the MCU. Requires an external pull-up — see [the wiring section](#sub-ghz-radio--cc1101-placeholder). |
| `GDO0` | **Output** | Driven by the radio; typed Output so ERC flags any attempt to drive it from the MCU side. |
| `RF_ANT` | **Passive** | The correct type for an RF port. It is not a logic signal, has no direction, and Passive is the only type that will not produce meaningless ERC results. It says nothing about impedance, band, or what sits on the other side. |
| `VCC_3V3` | **Power input** | Typed as a supply input to the subsystem regardless of which implementation path is chosen. |

### Symbol flags

| Flag | Value | Why |
|---|---|---|
| `on_board` | **`no`** | With no footprint, this symbol must not reach the PCB. `on_board no` makes KiCad exclude it from the board, so "Update PCB from Schematic" cannot pull in a footprint-less part or invite routing an RF net that has no defined impedance. Flip to `yes` only when the real footprint is assigned. |
| `in_bom` | **`yes`** | Required and deliberate. The radio is a **required subsystem that is still unresolved**, and it must stay visible in the BOM as `TBD`/`TBD` so it cannot be quietly forgotten during costing or procurement. |
| `exclude_from_sim` | `yes` | There is no simulation model for a placeholder. |
| `pin_numbers` | hidden | See [Pin table](#pin-table-3). |

**No footprint was created and none is assigned.** There is no `AQROOT_Beta.pretty`
entry for this part, and the symbol carries no `ki_fp_filters` property — a footprint
filter would imply a package family had been chosen, and none has.

> **Do not create a "generic CC1101 module" footprint to unblock layout.** There is
> no such thing as a generic CC1101 module land pattern: module vendors differ in
> outline, pad pitch, pad count, castellation arrangement, keep-out and antenna
> position, and a bare IC shares none of it. A placeholder footprint would be a
> fabricated dimension presented as a real one, it would silently become the thing
> the board is laid out around, and the RF keep-out it implies would be wrong.
> Resolve the implementation instead.
>
> **Still binding after the 2026-08-07 lock.** The implementation is now resolved
> (**E07-400M10S**), which means the correct footprint is obtainable — it does **not** mean
> a generic one became acceptable. Build the land pattern from Ebyte's E07-400M10S drawing,
> and do not reuse the SX1262 module's: the two modules differ in outline, pad pitch and pad
> count.

---

## Symbol — `SX1262_MODULE_PLACEHOLDER`

| Field | Value |
|---|---|
| Reference prefix | `U` |
| Value | `SX1262_MODULE_PLACEHOLDER` |
| Footprint | **blank — deliberately unassigned** |
| Manufacturer | `TBD` |
| MPN | `TBD` |
| Description | Functional placeholder for AQROOT built-in certified SX1262 LoRa/sub-GHz module |
| Datasheet | **blank** — see [why](#sx1262_module_placeholder) |

> **This symbol is a functional schematic placeholder only.** It exists so the
> SX1262's SPI Bus B nets can be drawn, named and ERC-checked before the certified
> module is chosen. It is **not** a part, **not** a package, and **not** ready for
> layout.

This is the **second** of AQROOT Beta's two radios. The CC1101 is the other; see
[`CC1101_RADIO_PLACEHOLDER`](#symbol--cc1101_radio_placeholder). Both sit on shared
SPI Bus B with the NFC controller, each with its own chip select.

### This is a module, not an IC

**Do not model a bare SX1262 IC.** AQROOT ships a **certified module** — that part of
the decision *is* settled, and it is the reason this symbol exists in this shape:

* A certified module carries its own crystal/TCXO, RF matching, filtering and
  (usually) its antenna interface. None of that appears on the AQROOT main board, so
  none of it belongs in this symbol.
* The certification carries over, which is the whole point of choosing a module.
* A bare-IC symbol would have a package pinout, RF ports, `DIO2`/`DIO3`, `DCC`/`VREG`
  and crystal pins — every one of which would be wrong here and would invite someone
  to lay out an RF front end AQROOT is not building.

The open question is **which** certified module, not module-versus-IC. That is the
difference from the CC1101 placeholder, where
[both paths are still live](#the-central-open-question-module-or-bare-ic).

### Module selection: Ebyte E22 vs Waveshare Core1262

~~**Unresolved.**~~ **RESOLVED 2026-08-07: Ebyte `E22-900M22S`.** Waveshare Core1262 is
not selected.

The original entry, kept because it explains why the symbol looks the way it does: *the two
candidates under consideration are the Ebyte E22 family and the Waveshare Core1262 family.
They are named here as the open question, and are deliberately not committed to anywhere in
the symbol — no vendor, no part number, no `MPN`, no footprint filter. They differ in
outline, pad arrangement, supply requirements and antenna interface, so choosing between
them changes the board.*

That last sentence is now the actionable part: the board content follows the **E22-900M22S**
specifically. Take outline, pad arrangement, supply requirement and antenna interface from
Ebyte's E22-900M22S document — **not from the E22 family in general**, which spans several
different modules. The symbol still carries no vendor, part number or `MPN`; setting them is
an outstanding symbol edit.

### What the SX1262 symbol deliberately does *not* claim

The symbol contains **no**:

* module vendor, family or part number;
* module land pattern, outline, dimensions, keep-out or mounting;
* module pin numbering, pin count or pin order;
* module supply voltage or current requirement — **module voltage requirements are
  unresolved**, and `VCC_3V3` is the AQROOT-side intent, not a verified module spec;
* crystal, TCXO or reference-frequency assumption (module-internal);
* RF matching, filtering or balun topology (module-internal);
* RF connector type, antenna interface, or trace-antenna geometry;
* operating band or regional band plan;
* `DIO2` / `DIO3` — see [Pin table](#pin-table-4).

### Pin table

The **symbol pin numbers are logical indices, not module pin numbers.** KiCad requires
every pin to carry a number, so pins are numbered 1–10 in the order below purely to
keep the symbol valid and its netlist stable. **Pin numbers are hidden**
(`(pin_numbers (hide yes))`) so they cannot be misread as a module pinout. Expect them
all to change once the module is selected.

| Logical pin | Name | Electrical type | Intended AQROOT net |
|---|---|---|---|
| 1 | `VCC_3V3` | Power input | `+3V3` |
| 2 | `GND` | Power input | `GND` |
| 3 | `SCK` | Input | `SPI_B_SCK` |
| 4 | `MOSI` | Input | `SPI_B_MOSI` |
| 5 | `MISO` | Tri-state | `SPI_B_MISO` |
| 6 | `CS_N` | Input | `SX1262_CS_N` |
| 7 | `BUSY` | Output | `SX1262_BUSY` |
| 8 | `DIO1` | Output | `SX1262_DIO1` |
| 9 | `RESET_N` | Input | `SX1262_RST_N` |
| 10 | `RF_ANT` | Passive | `SX1262_RF_TBD` |

All 10 pins are **visible**; there are no hidden pins. The **symbol encodes no AQROOT
net names** — the names above are functional pin names, and the net column is
documentation only. See [LoRa radio](#lora--sub-ghz-radio--sx1262-placeholder) for the
wiring intent.

**`DIO2` and `DIO3` are intentionally omitted.** Neither is assigned in the **locked**
Beta pin map — §3 lists only `SX1262 CS` (GPIO17), `DIO1` (GPIO18), `BUSY` (GPIO8) and
`RST`. Adding them here would create schematic pins with nowhere to go and would
invite spending GPIOs the pin map has already allocated. On many SX1262 modules
`DIO2` is an internal TX/RX switch control and `DIO3` an internal TCXO supply, both
handled inside the module — another reason they do not belong on a module-level
symbol. If either is ever needed, it goes through the pin map first, not this library.

### Pin grouping in the symbol

| Group | Side | Pins |
|---|---|---|
| Supply | top | `VCC_3V3` |
| Ground | bottom | `GND` |
| SPI + control | left | `SCK`, `MOSI`, `MISO`, `CS_N`, `BUSY`, `DIO1`, `RESET_N` |
| RF | right | `RF_ANT` |

As with the CC1101 placeholder, `RF_ANT` sits alone on the opposite side from the
digital pins — it mirrors the layout separation and makes an accidental digital-to-RF
connection visually obvious.

The body carries a visible six-line graphic, **rewritten 2026-08-07** for the module lock:

```
FUNCTIONAL PLACEHOLDER
MODULE LOCKED: EBYTE E22-900M22S
ANTENNA ON MODULE IPEX PORT
FOOTPRINT PENDING - FROM EBYTE DRAWING
NO FOOTPRINT
DO NOT ROUTE
```

> The previous lines 2–4 read `EXACT CERTIFIED MODULE PENDING` /
> `EBYTE E22 VS WAVESHARE CORE1262 UNRESOLVED` / `RF / ANTENNA INTERFACE PENDING`. All three
> were superseded by the lock. **`NO FOOTPRINT` and `DO NOT ROUTE` were deliberately kept** —
> they are still true, and remain the operative instruction until a real land pattern exists.
>
> The identical rewrite was applied to the `lib_symbols` cache in
> `04_spi_b_radios_nfc.kicad_sch` in the same commit. **Never edit one without the other:** a
> cache that disagrees with the library makes KiCad report the symbol as changed against its
> source. Text and positions were diffed after editing and confirmed identical.

Pins use the plain `line` graphic style. `CS_N` and `RESET_N` are **not** drawn with
inversion bubbles — the `_N` suffix already carries the polarity.

### Electrical type interpretations

| Pin | Choice | Why |
|---|---|---|
| `MISO` | **Tri-state**, not Output | SPI Bus B is shared with the CC1101 and NFC. Tri-state is the conservative KiCad type for a bus-attached slave output: it will not raise a false ERC output-conflict on `SPI_B_MISO`, whereas Output would. |
| `BUSY` | **Output** | Driven by the module to signal it is processing a command. Typed Output so ERC flags any attempt to drive it from the MCU side. |
| `DIO1` | **Output** | The module's interrupt line to the MCU. Typed Output for the same reason. |
| `RESET_N` | **Input** | Active-low reset driven into the module — from the expander, not a native GPIO. See [the wiring section](#lora--sub-ghz-radio--sx1262-placeholder). |
| `CS_N` | **Input** | Chip select driven by the MCU. Requires an external 10k pull-up — see below. |
| `RF_ANT` | **Passive** | The correct type for an RF port: no direction, not a logic signal, and the only type that will not produce meaningless ERC results. It says nothing about impedance, band, or what sits on the other side. |
| `VCC_3V3` | **Power input** | AQROOT-side intent. The module's actual supply requirement is unresolved. |

### Symbol flags

| Flag | Value | Why |
|---|---|---|
| `on_board` | **`no`** | With no footprint, this symbol must not reach the PCB. `on_board no` makes KiCad exclude it from the board, so "Update PCB from Schematic" cannot pull in a footprint-less part or invite routing an RF net with no defined impedance. Flip to `yes` only when the real footprint is assigned. |
| `in_bom` | **`yes`** | The module is a **required subsystem that is still unresolved**. It stays visible in the BOM as `TBD`/`TBD` so it cannot be quietly forgotten during costing or procurement. |
| `exclude_from_sim` | `yes` | There is no simulation model for a placeholder. |
| `pin_numbers` | hidden | See [Pin table](#pin-table-4). |

**No footprint was created and none is assigned.** There is no `AQROOT_Beta.pretty`
entry for this part, and the symbol carries no `ki_fp_filters` property — a footprint
filter would imply a module family had been chosen, and none has.

> **Do not create a generic SX1262 module footprint.** There is no generic land
> pattern: the E22 and Core1262 families differ in outline, pad pitch, pad count,
> castellation arrangement, keep-out and antenna position. A placeholder footprint
> would be a fabricated dimension presented as a real one, it would become the thing
> the board is laid out around, and its RF keep-out would be wrong. Select the module
> instead.
>
> **Still binding after the 2026-08-07 lock.** The module is now selected
> (**E22-900M22S**), so the correct land pattern is obtainable — that does not license a
> generic one. Take it from Ebyte's E22-900M22S drawing specifically, **not** from another
> E22-family module and **not** from the E07-400M10S.

---

## Symbol — `ST25R3916_NFC_PLACEHOLDER`

| Field | Value |
|---|---|
| Reference prefix | `U` |
| Value | `ST25R3916_NFC_PLACEHOLDER` |
| Footprint | **blank — deliberately unassigned** |
| Manufacturer | STMicroelectronics |
| MPN | `ST25R3916` — **no package suffix**, because the package is not selected |
| Description | Functional placeholder for AQROOT built-in ST25R3916 NFC/RFID reader front-end |
| Datasheet | <https://www.st.com/en/nfc/st25r3916.html> — ST's official product page |

> **PACKAGE RESOLVED 2026-08-07 — `ST25R3916-AQET`.** The reason the `MPN` field above
> carries no suffix ("because the package is not selected") has expired: the package IS now
> selected. The field itself is **unchanged and still reads `ST25R3916`** — updating it is
> part of the footprint work, not the decision, so this table continues to describe the
> symbol exactly as it stands. See *NFC package LOCKED: ST25R3916-AQET* in
> [[05 - Design Decisions Log]].
>
> **Nothing else about this symbol changed.** Still no footprint, still `on_board no`,
> logical pins 1–15 still placeholders that **will** change. The architecture is a
> **discrete** ST25R3916 with an ST reference-derived tuned PCB loop — unlike the two
> sub-GHz radios, its RF front end, matching network and antenna are all AQROOT board
> content, so `NFC_RFO1/RFO2/RFI1/RFI2_TBD` and `NFC_XIN/XOUT_TBD` remain parked and
> **DO NOT ROUTE** still stands.

> **This symbol is functional only.** It exists so the NFC subsystem's SPI, IRQ,
> supply and RF nets can be drawn, named and ERC-checked before the physical
> implementation is designed. It **must not** be read as implying a package pinout,
> package variant, matching network, crystal / reference implementation, antenna
> geometry, or power-stage topology.

This is the **third device on SPI Bus B**, alongside
[`CC1101_RADIO_PLACEHOLDER`](#symbol--cc1101_radio_placeholder) and
[`SX1262_MODULE_PLACEHOLDER`](#symbol--sx1262_module_placeholder).

### Three supplies, and why they are separate pins

The ST25R3916 does **not** run from one rail in AQROOT, and the split is a decision
already recorded in `11 - Beta Pin Map v0.2.md` §3, not an invention here:

| Pin | Rail | Why it is its own pin |
|---|---|---|
| `VDD_IO_3V3` | 3.3 V | Digital I/O supply. **Kept at 3.3 V so the SPI lines stay 3.3 V — no level shifter is needed** on the shared bus. This is the whole reason the I/O supply is broken out separately. |
| `VDD_DIG_3V3` | 3.3 V | Digital core supply, also 3.3 V. |
| `VDD_PA_5V` | **switched 5 V** | Analog / PA transmit rail. **Only this rail is boosted to 5 V**, for RF range and headroom. |

Modelling them as one pin would erase the constraint that makes the design work.
The pin map is explicit: *"boost ONLY the ST25R3916 analog/PA rail to 5V. Keep its
digital I/O supply (VDD_IO) at 3.3V so the SPI lines stay 3.3V — no level shifter
needed on the shared bus."*

The 5 V rail is **switched** — see
[the wiring section](#nfc-reader--st25r3916-placeholder) for `NFC_5V_EN` and why the
boost IC is still unresolved.

### What the ST25R3916 symbol deliberately does *not* claim

The symbol contains **no**:

* package variant, package outline, dimensions, keep-out or land pattern;
* pin numbering, pin count or pin order — the logical indices are not ST's;
* crystal, reference oscillator, load capacitors or clock topology — `XIN`/`XOUT` are
  bare functional ports;
* RF output network, receiver network, EMC filtering or matching component values;
* loop antenna, PCB coil, flex coil, turns count or antenna geometry;
* power-stage topology — no boost IC, no load switch, no inductor, no decoupling
  quantities;
* operating-mode, field-strength or range assumption.

Every one of these is **unresolved**.

**Do not model the X-NUCLEO-NFC06A1 board.** ST's evaluation board is a reference
design with its own matching network, antenna and component choices; copying it would
import a whole set of physical decisions AQROOT has not made and cannot verify against
its own enclosure and coil. It is not referenced anywhere in this symbol.

### Pin table

The **symbol pin numbers are logical indices, not ST's package pin numbers.** KiCad
requires every pin to carry a number, so pins are numbered 1–15 in the order below
purely to keep the symbol valid and its netlist stable. **Pin numbers are hidden**
(`(pin_numbers (hide yes))`) so they cannot be misread as a real pinout. Expect them
all to change once the package is selected.

| Logical pin | Name | Electrical type | Intended AQROOT net |
|---|---|---|---|
| 1 | `VDD_IO_3V3` | Power input | `+3V3` |
| 2 | `VDD_DIG_3V3` | Power input | `+3V3` |
| 3 | `VDD_PA_5V` | Power input | `NFC_5V_PA_PENDING` |
| 4 | `GND` | Power input | `GND` |
| 5 | `SCK` | Input | `SPI_B_SCK` |
| 6 | `MOSI` | Input | `SPI_B_MOSI` |
| 7 | `MISO` | Tri-state | `SPI_B_MISO` |
| 8 | `CS_N` | Input | `NFC_CS_N` |
| 9 | `IRQ` | Output | `NFC_IRQ` |
| 10 | `RFO1` | Passive | `NFC_RFO1_TBD` |
| 11 | `RFO2` | Passive | `NFC_RFO2_TBD` |
| 12 | `RFI1` | Passive | `NFC_RFI1_TBD` |
| 13 | `RFI2` | Passive | `NFC_RFI2_TBD` |
| 14 | `XIN` | Passive | `NFC_XIN_TBD` |
| 15 | `XOUT` | Passive | `NFC_XOUT_TBD` |

All 15 pins are **visible**; there are no hidden pins. The **symbol encodes no AQROOT
net names** — the names above are functional pin names, and the net column is
documentation only. Every RF and clock net carries a `_TBD` suffix because the network
on the other side of each of those pins does not exist yet.

### Pin grouping in the symbol

| Group | Side | Pins |
|---|---|---|
| Supplies | top | `VDD_IO_3V3`, `VDD_DIG_3V3`, `VDD_PA_5V` |
| Ground | bottom | `GND` |
| SPI + interrupt | left | `SCK`, `MOSI`, `MISO`, `CS_N`, `IRQ` |
| RF + clock | right | `RFO1`, `RFO2`, `RFI1`, `RFI2`, `XIN`, `XOUT` |

Digital on the left, RF and clock on the right, with a visible gap between the RF
group and the crystal group. As with the two radio placeholders, the separation
mirrors the layout discipline and makes an accidental digital-to-RF connection obvious
in the schematic.

The body carries a visible six-line graphic warning:

```
FUNCTIONAL PLACEHOLDER
ST25R3916 PACKAGE / SUPPORT NETWORK PENDING
NFC MATCHING / COIL / CLOCK IMPLEMENTATION PENDING
SWITCHED 5V PA RAIL REQUIRED
NO FOOTPRINT
DO NOT ROUTE
```

Pins use the plain `line` graphic style. `CS_N` is **not** drawn with an inversion
bubble — the `_N` suffix already carries the polarity.

### Electrical type interpretations

| Pin | Choice | Why |
|---|---|---|
| `MISO` | **Tri-state**, not Output | SPI Bus B is shared with the CC1101 and SX1262. Tri-state is the conservative KiCad type for a bus-attached slave output: it will not raise a false ERC output-conflict on `SPI_B_MISO`, whereas Output would. |
| `CS_N` | **Input** | Chip select driven by the MCU. Requires an external 10k pull-up — see [the wiring section](#nfc-reader--st25r3916-placeholder). |
| `IRQ` | **Output** | Driven by the reader. Typed Output so ERC flags any attempt to drive it from the MCU side. Note it is **not** typed active-low: ST25R3916 IRQ is active-high, so no `_N` suffix and no inversion bubble. |
| `RFO1`, `RFO2`, `RFI1`, `RFI2` | **Passive** | The correct type for RF ports: no direction, not logic signals, and the only type that will not produce meaningless ERC results. Naming them as two output and two input ports reflects the device's functional structure — it does **not** specify a differential drive topology, an impedance, or any matching arrangement. |
| `XIN`, `XOUT` | **Passive** | Crystal / reference-clock ports. Passive because whatever lands here is a passive network. The symbol takes no position on frequency, crystal-versus-external-clock, or load capacitance. |
| `VDD_IO_3V3`, `VDD_DIG_3V3`, `VDD_PA_5V` | **Power input** | Three separate supply inputs — see [Three supplies](#three-supplies-and-why-they-are-separate-pins). |

### Symbol flags

| Flag | Value | Why |
|---|---|---|
| `on_board` | **`no`** | With no footprint, this symbol must not reach the PCB. `on_board no` makes KiCad exclude it from the board, so "Update PCB from Schematic" cannot pull in a footprint-less part or invite routing an RF or antenna net that has no defined network behind it. Flip to `yes` only when the real footprint is assigned. |
| `in_bom` | **`yes`** | NFC is a **required subsystem** and a headline AQROOT feature. It stays in the BOM — here with a real `Manufacturer`/`MPN`, since the silicon *is* chosen even though the package is not. |
| `exclude_from_sim` | `yes` | There is no simulation model for a placeholder. |
| `pin_numbers` | hidden | See [Pin table](#pin-table-5). |

**No footprint was created and none is assigned.** There is no `AQROOT_Beta.pretty`
entry for this part, and the symbol carries no `ki_fp_filters` property — a footprint
filter would imply a package variant had been chosen, and none has.

> **Do not create or assign a footprint, and do not invent a PCB or flex coil or a
> matching network.** An NFC antenna is not a footprint you can approximate: the coil
> geometry, the matching values and the enclosure are one coupled design problem, and
> a fabricated placeholder would become the thing the board is laid out around while
> being wrong in every dimension that matters. The same applies to the RF output and
> receiver networks. Resolve the implementation instead.

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

### Display module — ILI9341 + FT6236 (placeholder)

**Documentation only, and provisional.** None of this is encoded in the symbol.
Because the module is not selected, this table records *intent* — it is the wiring
to reconcile against the real module, not a wiring that has been validated.

| Symbol pin | AQROOT net | Note |
|---|---|---|
| `VCC_3V3` | `+3V3` | Supply interface unresolved — see the caveats below. |
| `GND` | `GND` | |
| `LCD_SCK` | `SPI_A_SCK` | SPI Bus A, shared with the microSD socket. |
| `LCD_MOSI` | `SPI_A_MOSI` | |
| `LCD_MISO` | `SPI_A_MISO` | Shared bus — hence the Tri-state pin type. |
| `LCD_CS_N` | `DISP_CS_N` | Display chip select. |
| `LCD_DC` | `DISP_DC` | Data/command select. |
| `LCD_RST_N` | `DISP_RST_N` | On the U60 expander, port **P04** (per `11 - Beta Pin Map v0.2.md`), not a native GPIO. |
| `LCD_BL_CTL` | `DISP_BL_CTL` | Backlight control. Interface type unresolved. |
| `CTP_SDA` | `I2C_SDA_INT` | Internal I²C bus. |
| `CTP_SCL` | `I2C_SCL_INT` | Internal I²C bus. |
| `CTP_RST_N` | `TOUCH_RST_N` | On the U60 expander, port **P00**. |
| `CTP_INT_N` | **no connect** | AQROOT **polls** the FT6236, so the interrupt is unused. Place a `no_connect` flag on this pin in the schematic so ERC stays clean and the intent is explicit. |

**FT6236 I²C address: expected `0x38`.** It shares `I2C_SDA_INT` / `I2C_SCL_INT`
with the other internal-bus devices, so confirm `0x38` does not collide before the
bus is frozen.

Bus pull-ups on `I2C_SDA_INT` / `I2C_SCL_INT` are a **bus-level** concern, as with
the IMU. Many display modules carry their own touch-bus pull-ups — check the
selected module and do not end up with two sets in parallel.

**There is no second microSD interface here.** AQROOT's microSD socket is a
**separate** part on the same SPI Bus A. Nothing about card detect, `SD_CS_N` or the
socket belongs in this symbol, even if the module you eventually buy happens to
carry an SD slot on its own carrier PCB — if it does, leave that slot unpopulated
and unwired rather than absorbing it into this placeholder.

#### Still unresolved — must be closed before routing

| Open item | Consequence if left open |
|---|---|
| Exact module (vendor, part, revision) | Everything below depends on it. |
| Connector type and pin numbering | The symbol's logical pins 1–13 are placeholders and **will** change. |
| Backlight interface | Determines whether `LCD_BL_CTL` stays a logic input, and whether a driver/current-limit network is needed on the main board. |
| Supply interface | Determines whether `+3V3` feeds the module directly, what inrush to expect, and where decoupling belongs. |
| Physical footprint, outline and mounting | No footprint exists; the board cannot be laid out around the display until it does. |
| Logic level of the touch and SPI pins | Determines whether level shifting is required. |

**This placeholder must be replaced, or reconciled pin-for-pin against the selected
module, before PCB routing begins.** Until then the symbol's `on_board no` flag
keeps it off the board.

### Sub-GHz radio — CC1101 (placeholder)

**Documentation only, and provisional.** None of this is encoded in the symbol.
Because the implementation is not selected, this table records *intent* — the wiring
to reconcile against the real module or IC, not a wiring that has been validated.

| Symbol pin | AQROOT net | Note |
|---|---|---|
| `VCC_3V3` | `+3V3` | Decoupling and supply arrangement unresolved — they depend on the implementation path. |
| `GND` | `GND` | |
| `SCK` | `SPI_B_SCK` | SPI Bus B, shared with the SX1262 and NFC. |
| `MOSI` | `SPI_B_MOSI` | |
| `MISO` | `SPI_B_MISO` | Shared bus — hence the Tri-state pin type. |
| `CS_N` | `CC1101_CS_N` | ESP32-S3 **GPIO7** per `11 - Beta Pin Map v0.2.md` §3. **Requires a hardware pull-up to `+3V3`** — see below. |
| `GDO0` | `CC1101_GDO0` | ESP32-S3 **GPIO15**. Primary data / IRQ line. |
| `RF_ANT` | `CC1101_RF_TBD` | Placeholder net name. It is deliberately named `_TBD` because the RF path on the other side of this pin does not exist yet. |

#### `CC1101_CS_N` needs a hardware pull-up

`11 - Beta Pin Map v0.2.md` §3 requires a **hardware pull-up on every CS line** on
this bus, and `CC1101_CS_N` is no exception: **fit a pull-up resistor to `+3V3`**.
Three radios/peripherals share SPI Bus B, so a CS line that floats during reset,
power sequencing or firmware upload can let a device decide it has been selected and
drive `SPI_B_MISO` against another. The pull-up holds it deselected until firmware
takes control. The resistor is a **board-level part on the main board** — it belongs
in the schematic, not in this placeholder symbol, and it is needed on **both**
implementation paths.

#### Both radios ship together

**AQROOT Beta ships the CC1101 and the SX1262 together.** They are separate parts on
the shared SPI Bus B, each with its own CS. This placeholder is the CC1101 only —
resolving it does not resolve the SX1262, and the two radios' RF paths, antennas and
certification are separate problems. Coexistence (bus arbitration, and RF isolation
between the two chains) has to be handled at board level once both implementations
are known.

#### Still unresolved — must be closed before routing

| Open item | Consequence if left open |
|---|---|
| **Module or bare IC** | Determines every item below. See [the central open question](#the-central-open-question-module-or-bare-ic). |
| Package / module land pattern and keep-out | No footprint exists; the board cannot be laid out around the radio. |
| Pin numbering | The symbol's logical pins 1–8 are placeholders and **will** change. |
| Crystal and loading *(bare-IC path only)* | Frequency accuracy; a module supplies its own. |
| RF matching network / balun *(bare-IC path only)* | The `RF_ANT` net has no defined impedance until this exists. |
| Band filtering and operating band | Band plan, harmonics, and regional compliance. |
| Antenna interface | Whether `CC1101_RF_TBD` terminates in a connector, a trace antenna, or a module-internal antenna. |
| Certification path | A certified module may carry over; a bare IC will not. |
| RF stack-up and impedance target | Cannot route a controlled-impedance RF trace without it. |

**No PCB routing and no footprint assignment until the exact implementation is
selected.** Until then the symbol's `on_board no` flag keeps it off the board. In
particular, **do not create a placeholder or "generic" CC1101 module footprint** to
work around this — see [the warning above](#symbol--cc1101_radio_placeholder).

### LoRa / sub-GHz radio — SX1262 (placeholder)

**Documentation only, and provisional.** None of this is encoded in the symbol.
Because the certified module is not selected, this table records *intent* — the wiring
to reconcile against the real module, not a wiring that has been validated.

| Symbol pin | AQROOT net | Note |
|---|---|---|
| `VCC_3V3` | `+3V3` | **Module voltage requirements unresolved.** Confirm against the selected module before relying on this. |
| `GND` | `GND` | |
| `SCK` | `SPI_B_SCK` | SPI Bus B, shared with the CC1101 and NFC. |
| `MOSI` | `SPI_B_MOSI` | |
| `MISO` | `SPI_B_MISO` | Shared bus — hence the Tri-state pin type. |
| `CS_N` | `SX1262_CS_N` | ESP32-S3 **GPIO17** per `11 - Beta Pin Map v0.2.md` §3. **Requires a 10k hardware pull-up to `+3V3`** — see below. |
| `BUSY` | `SX1262_BUSY` | ESP32-S3 **GPIO8**. |
| `DIO1` | `SX1262_DIO1` | ESP32-S3 **GPIO18**. Primary interrupt line. |
| `RESET_N` | `SX1262_RST_N` | **From the expander, not a native GPIO** — U60 **P01**. See below. |
| `RF_ANT` | `SX1262_RF_TBD` | Placeholder net name, deliberately `_TBD`: the RF path on the other side of this pin does not exist yet. |

#### `SX1262_CS_N` needs a 10k pull-up to `+3V3`

**Fit a 10k pull-up resistor from `SX1262_CS_N` to `+3V3`.** §3 of the pin map requires
a hardware pull-up on every chip select on this bus, and 10k is the value the pin map
standardises on. Three devices share SPI Bus B, so a CS line left floating during
reset, power sequencing or firmware upload can let a device decide it has been
selected and drive `SPI_B_MISO` against another. The pull-up holds the module
deselected until firmware takes control. This resistor is a **board-level part on the
AQROOT main board** — it belongs in the schematic, not in this placeholder symbol.

#### `SX1262_RST_N` comes from the expander, and is held asserted at power-up

`SX1262_RST_N` is driven by **U60 port P01**, a TCA9535 expander output — not a native
ESP32 GPIO. (§7 of the pin map: reset moved off GPIO3 so that pin carries the BMI270
interrupt alone.) That creates a power-up ordering problem the board already solves:

* The TCA9535 has **no internal pull-ups at all**, and its outputs are not driven
  until firmware has configured the expander over I²C. Between power-up and that
  moment, P01 floats.
* The **existing external 100k pull-down** on this net is what covers the gap: it
  **holds the SX1262 reset asserted** until firmware configures U60 and deliberately
  releases it. The pin map records P01's mandatory power-up safe state as
  *"pull to RESET-ASSERTED"*.
* **Do not remove or re-purpose that pull-down**, and do not add a competing pull-up.
  It is the only thing keeping the radio in a defined state during early boot.

#### Still unresolved — must be closed before routing

| Open item | Consequence if left open |
|---|---|
| ~~**Which certified module — Ebyte E22 or Waveshare Core1262**~~ | **CLOSED 2026-08-07 — `E22-900M22S`.** Every item below is now answerable from one document. |
| Module voltage requirements | Whether `+3V3` is correct, and what supply/decoupling the board must provide. **Take from the E22-900M22S datasheet — do not assume 3V3 because the net is named `VCC_3V3`.** |
| Module land pattern, outline and keep-out | No footprint exists; the board cannot be laid out around the radio. **Now obtainable from the Ebyte drawing — still must be built.** |
| Module pin numbering | The symbol's logical pins 1–10 are placeholders and **will** change. |
| RF connector / antenna interface | ~~Whether `SX1262_RF_TBD` terminates in a connector, a trace antenna, or a module-internal antenna.~~ **Answered: the module's own IPEX/u.FL port, with a Taoglas FXP890 plugging onto it. `SX1262_RF_TBD` does not reach our copper.** Confirm the ordered variant is IPEX and not stamp-hole. |
| RF matching | ~~Module-internal on both candidates, but confirm against the selected part.~~ **Module-internal on the E22-900M22S. No board-level 915 MHz matching network.** |
| Operating band and regional band plan | Band selection and compliance. **Open — and see the cert caveat: the Beta antenna is not the module's stock antenna.** |
| Coexistence with the CC1101 | Two sub-GHz chains on one handheld — bus arbitration plus RF isolation. **Both implementations are now known (E22-900M22S + E07-400M10S), so this is resolvable.** Note that board-level harmonic filtering is no longer available as a mitigation — there is no board RF path to filter on. |

~~**Do not route until the exact certified module is selected**~~ — that condition is met.
**Do not route until a real land pattern exists**, and **do not create a generic module
footprint** to get started. Until then the symbol's `on_board no` flag keeps it off the
board, and it must stay `no`.

### NFC reader — ST25R3916 (placeholder)

**Documentation only, and provisional.** None of this is encoded in the symbol.
Because the package and every support network are unresolved, this table records
*intent* — the wiring to reconcile against the real implementation, not a wiring that
has been validated.

| Symbol pin | AQROOT net | Note |
|---|---|---|
| `VDD_IO_3V3` | `+3V3` | **Stays at 3.3 V.** This is what keeps the SPI lines at 3.3 V — see below. |
| `VDD_DIG_3V3` | `+3V3` | Digital core, also 3.3 V. |
| `VDD_PA_5V` | `NFC_5V_PA_PENDING` | The **switched 5 V** PA/analog rail. Net name is deliberately `_PENDING`: the rail's source does not exist yet. |
| `GND` | `GND` | |
| `SCK` | `SPI_B_SCK` | SPI Bus B, shared with the CC1101 and SX1262. |
| `MOSI` | `SPI_B_MOSI` | |
| `MISO` | `SPI_B_MISO` | Shared bus — hence the Tri-state pin type. |
| `CS_N` | `NFC_CS_N` | ESP32-S3 **GPIO9** per `11 - Beta Pin Map v0.2.md` §3. **Requires a 10k hardware pull-up to `+3V3`** — see below. |
| `IRQ` | `NFC_IRQ` | ESP32-S3 **GPIO38**. Keep it — ST's RFAL driver stack is IRQ-driven, not polled. |
| `RFO1` | `NFC_RFO1_TBD` | RF output port. Network unresolved. |
| `RFO2` | `NFC_RFO2_TBD` | RF output port. Network unresolved. |
| `RFI1` | `NFC_RFI1_TBD` | Receiver input port. Network unresolved. |
| `RFI2` | `NFC_RFI2_TBD` | Receiver input port. Network unresolved. |
| `XIN` | `NFC_XIN_TBD` | Reference-clock port. Network unresolved. |
| `XOUT` | `NFC_XOUT_TBD` | Reference-clock port. Network unresolved. |

#### `NFC_CS_N` needs a 10k pull-up to `+3V3`

**Fit a 10k pull-up resistor from `NFC_CS_N` to `+3V3`.** §3 of the pin map requires a
hardware pull-up on every chip select on this bus, and 10k is the standard value
there. With three devices on SPI Bus B, a CS line floating during reset, power
sequencing or firmware upload can let a device decide it has been selected and drive
`SPI_B_MISO` against another. The pull-up holds the reader deselected until firmware
takes control. This resistor is a **board-level part on the AQROOT main board** — it
belongs in the schematic, not in this placeholder symbol.

#### No SPI level shifter is required

`VDD_IO` stays at **3.3 V**, so the reader's SPI pins are 3.3 V logic and sit directly
on the shared bus with no translation. **Only the PA/analog rail is boosted.** The pin
map states this as a requirement and adds: *"Confirm VDD_IO is tied to 3V3 in the
schematic."* Treat that as a checklist item — if `VDD_IO` ever drifts to 5 V, the
whole shared bus needs level shifting and the design changes shape.

#### The 5 V PA rail: required, switched, and its source unresolved

* The **PA / analog transmit rail requires the switched 5 V rail.** The chip does
  operate at 3.3 V — Alpha proved SPI comms there — but 5 V on the PA rail is what
  buys RF range and headroom, which is the reason the rail exists.
* It is **switched, not always-on**: `NFC_5V_EN` is controlled by **U60 port P02**,
  whose mandatory power-up safe state in the pin map is *"pull to **OFF**"*. The boost
  must be off at power-up and stay off while NFC is idle, both for current draw and so
  a floating expander output cannot momentarily enable it before firmware configures
  U60.
* **The exact 5 V boost IC is unresolved.** No part, topology, inductor or feedback
  network is chosen, which is why `NFC_5V_PA_PENDING` is a placeholder net rather than
  a real rail name. Nothing about the power stage belongs in this symbol.

#### NFC as the third SPI Bus B device is first validated on Beta

Alpha tested **two** radios sharing this bus, with NFC on its own dedicated pins.
**Three devices on one bus is new in Beta.** The pin map is explicit that the CS
discipline *"generalizes, but validate on Beta"*. Treat the shared-bus behaviour with
all three devices — CS discipline, per-device SPI frequency and mode, mutex, and
recovery if a device fails while holding MISO — as **unvalidated** until Beta bring-up
proves it.

#### Still unresolved — must be closed before routing

| Open item | Consequence if left open |
|---|---|
| ST25R3916 **package variant** | No footprint exists; the board cannot be laid out around the reader. The symbol's logical pins 1–15 **will** change. |
| Crystal / reference network | `XIN`/`XOUT` have nothing on the other side. |
| Decoupling scheme and quantities | Supply integrity on three separate rails. |
| RF output network (`RFO1`/`RFO2`) | The transmit path does not exist. |
| Receiver network (`RFI1`/`RFI2`) | The receive path does not exist. |
| Loop antenna and matching values | Coil geometry, matching and enclosure are one coupled problem — see the warning above. |
| 5 V boost IC and load switch | `NFC_5V_PA_PENDING` has no source. |
| Three-device SPI Bus B behaviour | Unvalidated until Beta bring-up. |

**Do not route until the implementation is selected**, and **do not create a footprint
or invent a coil or matching network** to get started. Until then the symbol's
`on_board no` flag keeps it off the board.

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
| `AQROOT_Beta:CC1101_RADIO_PLACEHOLDER` | *(none)* |
| `AQROOT_Beta:ILI9341_FT6236_MODULE_PLACEHOLDER` | *(none)* |
| `AQROOT_Beta:ST25R3916_NFC_PLACEHOLDER` | *(none)* |
| `AQROOT_Beta:SX1262_MODULE_PLACEHOLDER` | *(none)* |
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

- [ ] Open `AQROOT_Beta.kicad_sym` in the Symbol Editor — confirm **all six** of
      `BMI270`, `TSOP38238`, `ILI9341_FT6236_MODULE_PLACEHOLDER`,
      `CC1101_RADIO_PLACEHOLDER`, `SX1262_MODULE_PLACEHOLDER` and
      `ST25R3916_NFC_PLACEHOLDER` load, and run the symbol checker on each. All four
      placeholders are expected to report a missing footprint; that is the intended
      state, not a defect.
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
- [ ] **Blocking for layout:** select the actual display module, then reconcile
      `ILI9341_FT6236_MODULE_PLACEHOLDER` against it — renumber the pins to the real
      connector pinout, create and assign a footprint, resolve the backlight and
      supply interfaces, and set `on_board` back to `yes`. Do not route the display
      area until this is closed.
- [ ] Confirm the FT6236's `0x38` I²C address does not collide with another device
      on `I2C_SDA_INT` / `I2C_SCL_INT`.
- [x] ~~**Blocking for layout:** decide **module or bare CC1101 IC**~~ — **DONE 2026-08-07:
      module, `E07-400M10S`.** The crystal / RF matching / filtering / antenna sub-tasks are
      void with it (all module-internal).
- [ ] **Blocking for layout:** reconcile `CC1101_RADIO_PLACEHOLDER` against the
      **E07-400M10S** — set Manufacturer/MPN off `TBD`, repoint `Datasheet` from TI's
      product page to Ebyte's module document, renumber the pins to the real module pinout,
      build and assign a footprint from the Ebyte land-pattern drawing, confirm the module's
      supply requirement, resolve `CC1101_RF_TBD` (it terminates at the module's IPEX port,
      not on our copper), and set `on_board` back to `yes`. Do not route the RF area until
      this is closed, and do not substitute a generic module footprint to get started.
- [ ] Confirm the hardware pull-up to `+3V3` on `CC1101_CS_N` is present in the
      schematic, along with the pull-ups on the other SPI Bus B chip selects.
- [x] ~~**Blocking for layout:** select the certified SX1262 module (**Ebyte E22** or
      **Waveshare Core1262**)~~ — **DONE 2026-08-07: `E22-900M22S`.**
- [ ] **Blocking for layout:** reconcile `SX1262_MODULE_PLACEHOLDER` against the
      **E22-900M22S** — set Manufacturer/MPN off `TBD`, set the blank `Datasheet` to Ebyte's
      module document (never Semtech's silicon datasheet), renumber the pins to the real
      module pinout, confirm the module's supply requirement against `+3V3`, build and assign
      a footprint from the Ebyte land-pattern drawing, resolve `SX1262_RF_TBD` (it terminates
      at the module's IPEX port), and set `on_board` back to `yes`. Do not route the RF area
      until this is closed, and do not substitute a generic module footprint.
      **(The body graphic text is already done — 2026-08-07, symbol + cache together.)**
- [ ] **Verify the antenna interface before ordering either module.** Ebyte sells IPEX and
      stamp-hole variants under closely-related part numbers. Everything above assumes IPEX;
      a stamp-hole variant would force a board-level antenna interface and RF routing.
- [ ] **Cert question, not yet answered.** Both modules' pre-certification is the reason they
      were chosen, but the Beta antennas are not their stock antennas, and modifying a
      certified module's RF section can void the approval. Confirm with the cert lab before
      treating the pre-cert as banked.
- [x] ~~**Stale text outside this library:** the `04_spi_b_radios_nfc` sheet still displays
      `EXACT CERTIFIED MODULE PENDING` / `EBYTE E22 VS WAVESHARE CORE1262 UNRESOLVED`.~~
      **DONE 2026-08-07** — both the sheet annotations and the sheet's `lib_symbols` cache
      were updated, the latter in lockstep with `AQROOT_Beta.kicad_sym`.
- [ ] Confirm the **10k pull-up to `+3V3` on `SX1262_CS_N`** is in the schematic, and
      that the **existing 100k pull-down holding `SX1262_RST_N` asserted** is still
      present and not competing with any added pull-up.
- [ ] **Blocking for layout:** select the ST25R3916 package and design its support
      networks, then reconcile `ST25R3916_NFC_PLACEHOLDER` against them — renumber the
      pins to ST's real pinout, create and assign a footprint, resolve the crystal /
      reference network, decoupling, RF output and receiver networks, the loop antenna
      and its matching, and the 5 V boost IC behind `NFC_5V_PA_PENDING`; then set
      `on_board` back to `yes`. Do not route the NFC area until this is closed, and do
      not invent a coil or matching network to get started.
- [ ] Confirm the **10k pull-up to `+3V3` on `NFC_CS_N`** is in the schematic.
- [ ] **Confirm `VDD_IO` is tied to 3V3, not 5 V** — this is what keeps SPI Bus B at
      3.3 V and removes the need for a level shifter. Confirm only the PA/analog rail
      is boosted, and that `NFC_5V_EN` (U60 P02) is pulled to **OFF** at power-up.
- [ ] Validate **NFC as the third device on SPI Bus B** during Beta bring-up — Alpha
      only tested two radios sharing this bus, with NFC on dedicated pins.
