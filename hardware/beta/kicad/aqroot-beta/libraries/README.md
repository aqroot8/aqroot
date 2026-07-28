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

> `sym-lib-table` and `fp-lib-table` are **deliberately not modified**. Register the
> library manually in KiCad — see [Registering the library](#registering-the-library).

---

## Source of authority

Everything in this library is derived from a single document:

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

### Firmware note

The BMI270 requires a multi-kilobyte configuration blob to be uploaded after
power-up before accel/gyro data is valid. Register-level access alone will not
produce motion data. This is a firmware concern, recorded here only because it
routinely surprises people probing a correctly wired part.

---

## Registering the library

`sym-lib-table` and `fp-lib-table` are intentionally untouched. Register manually:

**Symbols** — *Preferences → Manage Symbol Libraries → Project Specific Libraries → +*

| Field | Value |
|---|---|
| Nickname | `AQROOT_Beta` |
| Library Path | `${KIPRJMOD}/libraries/AQROOT_Beta.kicad_sym` |
| Library Format | KiCad |

**Footprints** — *Preferences → Manage Footprint Libraries → Project Specific Libraries → +*

| Field | Value |
|---|---|
| Nickname | `AQROOT_Beta` |
| Library Path | `${KIPRJMOD}/libraries/AQROOT_Beta.pretty` |
| Library Format | KiCad |

Using the same nickname for both is what makes the symbol's
`AQROOT_Beta:Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270` footprint field resolve.

---

## Verification before manufacture

This library was built from the datasheet without KiCad installed on the
authoring machine, so the following have **not** been run and should be done
before committing to fabrication:

- [ ] Open `AQROOT_Beta.kicad_sym` in the Symbol Editor — confirm it loads and run
      the symbol checker.
- [ ] Open the footprint in the Footprint Editor and run the footprint checker.
- [ ] Overlay the footprint against §8.3 at 1:1 print scale.
- [ ] Confirm pad 1 lands at the upper left with the part oriented as in §7.1's
      top view.
- [ ] Confirm the board's global solder-mask expansion suits a 0.25 mm-wide land
      with your fab.
