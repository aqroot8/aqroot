# AQROOT Beta DM — assembly DNP control

**Read this before placing a single part.** This board is a Demo Model
derivative of the full AQROOT Beta. It shares the full Beta's layout, so every
deferred function still has its footprints on the board. Several of them
**must not be fitted**, and one of them — `U9` — is a **bus-safety** matter, not
a cost or scope matter.

Authoritative source of truth: the KiCad project itself. Every part below
carries KiCad's native `dnp` flag in both the schematic and the PCB, which is
the same convention the design already used for its five pre-existing DNP parts.
The files in this directory are generated from it, not maintained by hand.

## Files in this directory

| file | what it is | use it for |
|---|---|---|
| `aqroot-Beta-DM-BOM-fitted.csv` | **the parts to buy and place** — DNP excluded | purchasing, kitting, placement |
| `aqroot-Beta-DM-BOM-full.csv` | every part, with a `DNP` column | design review, Final-product restoration |
| `aqroot-Beta-DM-DO-NOT-POPULATE.csv` | the 40 DNP refs with a reason each | assembly control / incoming check |
| `aqroot-Beta-DM-pos-fitted.csv` | **placement data, DNP excluded** | pick-and-place |
| `aqroot-Beta-DM-pos-all.csv` | placement data for every footprint | reference only — **do not feed to the machine** |
| `aqroot-Beta-DM-assembly-top.pdf` | top assembly drawing | visual check; DNP parts are **crossed out** |
| `aqroot-Beta-DM-assembly-bottom.pdf` | bottom assembly drawing (mirrored) | visual check; DNP parts are **crossed out** |

The assembly PDFs are crossed-out automatically: the project has
`crossoutdnponfab yes` and `sketchdnponfab yes`, so any part KiCad considers DNP
is drawn crossed on the fab layers. If a part looks crossed out on the drawing,
it does not go on the board.

## Regenerating

From `hardware/beta-dm/kicad/aqroot-beta-dm/`:

```
kicad-cli sch export bom  --output ../../fab/aqroot-Beta-DM-BOM-full.csv \
    --fields 'Reference,Value,Footprint,MPN,Manufacturer,${QUANTITY},${DNP}' \
    --labels 'Refs,Value,Footprint,MPN,Manufacturer,Qty,DNP' \
    --group-by 'Value,Footprint,${DNP}' aqroot-Beta-DM.kicad_sch

kicad-cli sch export bom  --output ../../fab/aqroot-Beta-DM-BOM-fitted.csv --exclude-dnp \
    --fields 'Reference,Value,Footprint,Manufacturer,MPN,${QUANTITY}' \
    --labels 'Refs,Value,Footprint,Manufacturer,MPN,Qty' \
    --group-by 'Value,Footprint' --ref-range-delimiter '' aqroot-Beta-DM.kicad_sch

kicad-cli pcb export pos --output ../../fab/aqroot-Beta-DM-pos-fitted.csv \
    --format csv --units mm --side both --exclude-dnp aqroot-Beta-DM.kicad_pcb

kicad-cli pcb export pdf --output ../../fab/aqroot-Beta-DM-assembly-top.pdf \
    --layers F.Fab,F.Silkscreen,Edge.Cuts --include-border-title --black-and-white \
    aqroot-Beta-DM.kicad_pcb
```

**These commands are the ones that actually reproduce the released files** —
verified 2026-08-21. The recipe printed here previously did not: its column
order and `LCSC` field did not match the released CSVs, and its
`--group-by` was recorded correctly but had not been used, which is how seven
**fitted** parts (`C1`, `C12`, `C18`, `C43`, `C56`, `R43`, `R46`) came to be
tagged `DNP` in the full BOM. Grouping by `${DNP}` keeps fitted and DNP
instances of the same value in separate rows and fixes that.

### Two manual post-steps

1. **`LS1` is pulled out of the fitted BOM.** It is an off-board 8 Ω speaker
   with no footprint, so it exports into the fitted BOM but must not reach the
   assembler's placement list. Remove its row and keep it in
   `aqroot-Beta-DM-OFF-BOARD.csv`. This is why the fitted BOM totals **146**
   parts while the schematic has 147 non-DNP parts.
2. **`aqroot-Beta-DM-DO-NOT-POPULATE.csv`** is derived from the full BOM's
   `DNP` rows with the per-part reasons in this document. After regenerating,
   check that its reference set still matches the full BOM's `DNP` set exactly
   — 42 parts across 28 rows.
3. **`C24`'s value is overridden in both CPL files.** `kicad-cli` takes the
   `Val` column from the frozen board, so a raw export writes
   `22uF 25V X7R`. After exporting, replace that one field with
   `10uF 25V X5R` in `aqroot-Beta-DM-pos-fitted.csv` and
   `aqroot-Beta-DM-pos-all.csv`. **Only the `Val` field of the `C24` row may
   change** — `Ref`, `Package`, `PosX`, `PosY`, `Rot` and `Side` are identical
   and no other row moves. Both files are one line long in `git diff`
   afterwards; if more changed, the export is wrong.

### `C24` value text — two different things

| where | reads | authority |
|---|---|---|
| PCB `F.Fab` value text | `22uF 25V X7R` | **stale metadata only** — not a manufacturing layer, board is frozen |
| CPL `Val` column (both `pos` files) | **`10uF 25V X5R`** | corrected, post-step 3 above |
| BOM + MPN ledger | **`10uF 25V X5R`, Murata `GRM188R61E106KA73D`** | **authoritative for procurement and assembly** |

The part to fit is Murata **`GRM188R61E106KA73D`, 10 µF / 25 V / X5R / 0603**.
Nothing assembler-facing carries the old value any more. The `F.Fab` text stays
stale because the PCB is byte-frozen and `F.Fab` is not exported in the copper,
mask, paste, silkscreen or drill set; it is corrected in Full-Beta, not here.
KiCad's schematic-parity check reports the board/schematic mismatch as one
WARNING (`Value (C24) doesn't match symbol value`) and it is **intentional**.

---

## 1. DO NOT POPULATE — 35 Demo Model parts

### 1.1 `U9` ST25R3916 NFC front end — **BUS SAFETY, NOT OPTIONAL**

| ref | value |
|---|---|
| **U9** | ST25R3916-AQET |
| C45 C46 | 2.2 µF / 10 nF — `NFC_VDD_D` |
| C47 C48 | 2.2 µF / 10 nF — `NFC_VDD_A` |
| C49 C50 | 2.2 µF / 10 nF — `NFC_VDD_RF` |
| C51 C52 | 2.2 µF / 1 nF — `NFC_VDD_AM` |
| C53 C54 | 1 µF / 10 nF — `NFC_AGDC` |

**Why U9 must not be fitted.** On this board `+3V3` reaches U9's `VDD_IO`, and
`SPI_B_SCK`, `SPI_B_MOSI` and `SPI_B_MISO` all land on its pads from the live
SPI-B bus — the same bus the SX1262 (LoRa) and CC1101 radios use, and the LoRa
link is the whole point of the demo. But `NFC_CS_N` carries **no copper at all**
on this board: zero tracks, zero vias. `R29` is drawn as a pull-up in the
schematic, but its far end goes nowhere, so it does not hold U9's select pin.

A fitted U9 would therefore power up with a live clock, a live MOSI, its `MISO`
driver connected to the shared bus, and a **floating chip select** — a credible
source of bus contention against both radios. Its own `VDD`/`VDD_TX` are also
unpowered, which is outside ST's supply-sequencing envelope. And with no chip
select, no interrupt and no `VDD` in copper, firmware could not talk to it even
if it were fitted. There is no upside and a real downside.

> **If a Beta DM board arrives with U9 fitted, do not power it. Quarantine it.**

C45–C54 sit on U9's own regulator outputs. Without U9 they connect to nothing.

### 1.2 NFC 5 V PA boost — no load exists

| ref | value | role |
|---|---|---|
| U13 | TPS61023 | boost converter |
| L2 | 1 µH WE-MAPI 4030 | boost inductor |
| R44 R45 | 732 k / 100 k 1 % | feedback divider |
| C34 C35 | 22 µF 10 V X7R | output bulk |
| C19 | 100 nF | `NFC_5V_PA_PENDING` HF decoupling |
| C55 | 2.2 µF | `NFC_5V_PA_PENDING` bulk decoupling |

`U13`'s output `NFC_5V_PA_PENDING` has exactly one active load: `U9` pins 8 and
10. With U9 unfitted there is no load at all, the enable is never asserted, and
the rail is not fully routed. Verified: no non-NFC load exists on this rail.

`R14` (100 k pull-down on `NFC_5V_EN`) and `TP10` **stay fitted** — see §2.
`TP9` is a bare test pad on the dead rail; there is no part to fit.

### 1.3 Speaker output — deferred

| ref | value |
|---|---|
| U5 | MAX98357A Class-D amplifier |
| J6 | JST-PH-2 speaker connector |

`SPK_P` and `SPK_N` have exactly two nodes each and both are these parts.
`I2S_SPK_DOUT` and `AMP_SD_MODE` are not routed on this board.

**The microphone is unaffected and must work.** `MK1` (ICS-43434) and its
decoupling `C8` are fitted.

### 1.4 IR transmitter — deferred

| ref | value |
|---|---|
| D1 | TSAL6200 IR LED |
| Q1 | AO3400A |
| R22 | 100 R gate series |
| R23 | 100 K gate pull-down |
| R24 | 18 R LED series |

`R23` is a gate pull-down: it is only meaningful with `Q1` fitted, so the two
travel together. **If `Q1` is ever fitted, `R23` must be fitted with it.**

### 1.5 IR receiver — deferred

| ref | value |
|---|---|
| U6 | TSOP38238 |
| R21 | 100 R supply series |
| C11 | 4.7 µF supply bypass |

### 1.6 J5 community-header ESD arrays — deferred

| ref | value | protects |
|---|---|---|
| D2 | TPD2E009DBZR | `I2C_SCL_EXT_HDR`, `I2C_SDA_EXT_HDR` |
| D3 | TPD4E1B06DRLR | `XGPIO0_HDR` … `XGPIO3_HDR` |
| D4 | TPD4E1B06DRLR | `XGPIO4_HDR` … `XGPIO7_HDR` |
| D5 | TPD4E1B06DRLR | `XGPIO8_HDR` … `XGPIO11_HDR` |
| D6 | TPD4E1B06DRLR | `XGPIO12_HDR`, `XGPIO13_HDR` |
| D7 | TPD2E009DBZR | `WAKE_ATTN_N_HDR`, `FAST_IO_GPIO43_HDR` |

**Every one of these is shunt-only.** Each signal pin touches exactly one net
and pin 2 is `GND`; no signal passes *through* the device. Verified pin by pin
on the board, not assumed from the part number. Unfitting them therefore
removes protection and breaks no connection — the header still works.

They are deferred because the J5 ESD network is entirely unrouted (see
`../BETA-DM-RESIDUAL-BLOCKERS.md` §2): fitted, they would be unconnected parts
on a bench demo board. **FINAL RESTORE REQUIRED** — the Final product ships
with header ESD protection fitted and routed.

---

## 2. FITTED — parts that look droppable but are not

| ref | value | why it stays |
|---|---|---|
| **U10** | USBLC6-2SC6 | **U10 MUST FIT — SERIES USB DATA PATH.** Both USB data lines pass *through* it: `USB_D_CONN_P/N` enter on pins 3/1 and leave on pins 4/6 as `USB_D_ESD_P/N`. Unfitting it open-circuits USB. It is an ESD part, but it is **not** in the D2–D7 class and must never be added to any ESD DNP list. |
| **R14** | 100 k | `NFC_5V_EN` pull-down. Explicitly retained. If `U13` is ever fitted, this is what holds it off while the expander port is high-Z at power-up. |
| **TP10** | test point | `NFC_5V_EN` probe point. Retained. |
| **R74** | 100 k | `SX1262_RXEN` pull-down — holds the LoRa RF switch in CLOSE while the expander is high-Z. **Radio-critical.** |
| **R27 / R28** | 10 k | SX1262 / CC1101 chip-select pull-ups. **Radio-critical.** |
| **R13** | 100 k | `SX1262_RST_N` pull-up. **Radio-critical.** |
| **MK1 / C8** | ICS-43434 / 100 nF | the microphone and its decoupling. **Demo function.** |
| C18 | 100 nF | nominally U9's `VDD_IO` decoupling, but it is a plain `+3V3`–GND capacitor in a congested corner. Fitting it is free rail decoupling and carries no risk. |
| R29 | 10 k | nominally the NFC chip-select pull-up. With U9 unfitted it simply holds the otherwise-unused MCU `IO9` node at a defined level. |
| C9 / C10 | 100 nF / 10 µF | nominally U5's decoupling; both are plain `+3V3`–GND capacitors. |
| R15 | 100 k | nominally the amplifier shutdown pull-down; with U5 unfitted it keeps expander port `U2.P03` at a defined level. |
| C12 | 4.7 µF | IR-block local `+3V3` decoupling; plain `+3V3`–GND. |

These six (`C18`, `R29`, `C9`, `C10`, `R15`, `C12`) are *eligible* for DNP and
are deliberately **fitted** instead. Every one of them sits between two live
rails, so fitting costs nothing and removes a way to get the build wrong. If
you want them dropped, that is a one-line change — but it is a deliberate
decision, not an oversight.

---

## 3. Pre-existing full-Beta DNP — not a Demo Model decision

`C21`, `C22`, `R68`, `R49`, `R50` were already DNP in the full Beta and are
listed here only so they are not mistaken for DM cuts. Their disposition is a
full-Beta matter and is unchanged.

---

## 3a. LEAN-CORE additions: U15 and U16

| ref | part | reason |
|---|---|---|
| `U15` | TPS22918DBVR load switch | switched accessory rail is Lean-DM deferred; a fitted part would sit with `ON` floating, because `ACC_PWR_EN` is unrouted and `R17` is on a different island |
| `U16` | TCA9517ADGK I²C buffer | buffered external J5 I²C is Lean-DM deferred; the B side has no remaining Demo-Model function |

Both were audited against KiCad's own connectivity engine by **deleting the
footprint entirely** on a scratch copy. `+3V3`, `/I2C_SCL_INT` and
`/I2C_SDA_INT` each stay at **one island** either way, so neither part is
load-bearing for any live net and both DNPs are unconditional.

Support passives are classified individually in
[../BETA-DM-LEAN-CORE-SCOPE.md](../BETA-DM-LEAN-CORE-SCOPE.md) §4. `R17` stays
**fitted**; `C38`, `C39`, `C42`, `R46`, `R47`, `R48` are DNP-ELIGIBLE and
deliberately **kept**.

### PASTE / STENCIL REQUIREMENT — new, and it applies to every DNP footprint

**DNP footprints must receive no solder paste.** Either the stencil is cut
without their apertures, or the assembler is instructed to skip them.

This mattered less before, because the earlier DNP set sat on deferred nets.
`U15` and `U16` are the first DNP parts whose pads are adjacent to **live,
must-work** nets, so a stray solder ball on an unpopulated pad would bridge
something that matters:

| adjacency | pad-edge gap | what a bridge would short |
|---|---:|---|
| `U16.1` (`+3V3`) ↔ `U16.2` (`I2C_SCL_INT`) | **0.400 mm** | the 3.3 V rail onto the **internal I²C bus** |
| `U16.2` (`I2C_SCL_INT`) ↔ `U16.3` (`I2C_SDA_INT`) | 0.400 mm | `SCL` to `SDA` |
| `U15.1` (`+3V3`) ↔ `U15.2` (`GND`) | 0.650 mm | a short across the 3.3 V rail |

This is a fabrication-package instruction, not a design change. It must appear
in the fab notes before any board is built.

---

## 3b. LEAN GPIO LANDING — new critical fabrication feature

The `XGPIO5` via at **(20.400, 14.050)** sits at the board's smallest via size
**and** at its tightest solder-mask web. The web is what makes it critical.

> **Correction (GND closeout pass).** An earlier revision of this section called
> this via *"the smallest via on the board — every other via is 0.60 / 0.30 or
> larger."* That was wrong when written. The board already carried four
> 0.50 / 0.25 vias (`Net-(U13-FB)` ×2, `ISET` ×2) and thirty 0.55 / 0.25 vias.
> The GND closeout added two more 0.50 / 0.25 vias (`GND`, at (16.050, 13.700)
> and (27.400, 13.000)). The size is therefore **not** unique; the 0.125 mm mask
> web under a fitted TSSOP body is.

| | |
|---|---|
| diameter / drill | **0.50 mm / 0.25 mm** — the board's smallest size class, shared with 6 other vias |
| annular ring | **0.125 mm** — exactly the board's documented floor |
| location | beneath the `U3` TSSOP-24 body, B.Cu side |
| solder-mask web to `U3.9` paste | **0.125 mm** — the preferred figure, not the 0.100 mm floor; the tightest web on the board |

Requirements:

* **tented both sides.** It inherits the board-level
  `(tenting (front yes) (back yes))`; no per-via override exists and none may
  be added.
* the 0.125 mm web depends on **green** solder mask holding a dam at that
  width. A different mask colour or a relaxed mask process invalidates it.
* confirm the fab quotes a **0.25 mm drill** without an exception.

---

---

## 3c. FINAL COPPER CLOSEOUT — outer GND pours

The board now carries two outer-layer GND pours in addition to the In1.Cu
reference plane:

| zone | layer | outline | pad connection |
|---|---|---|---|
| `F.Cu GND POUR` | F.Cu | 0.6 mm inset from the board outline | **solid** |
| `B.Cu GND POUR` | B.Cu | same | **solid** |

Fabrication and assembly consequences:

* **Pad connection is solid, not thermal relief.** Every fitted GND
  termination on an outer layer is tied directly into the pour. This was a
  measured decision: thermal relief left 15 `starved_thermal` DRC errors,
  because the fine-pitch pockets around `U2`, `U3` and `U4` cannot fit the two
  spokes the zone requires.
* **Reflow profile note for assembly:** solid outer copper on small 0402/0603
  GND terminations is a heat-sink consideration. Use a normal profile for a
  four-layer 1.6 mm board with a full ground plane; do not treat these as
  isolated pads. No pad geometry was modified to achieve this.
* **Copper balance changed.** Both outer layers are now largely poured, where
  previously they carried only tracks. Expect the usual etch-compensation and
  a more uniform copper distribution than the earlier revision.
* **RF and reserved areas remain copper-free on every layer they name:**
  `NFC RESERVED`, `WROOM ANTENNA KEEPOUT`, `HEADER RESERVED`, `915 KEEPOUT`,
  `433 KEEPOUT` and the west off-board area. Verified against the filled
  polygons, not merely against the rule flags: deepest penetration is
  0.000000 mm.
* Minimum pour copper to the board edge is **0.600 mm**; to a mounting-hole
  edge, **0.501 mm**.

Two design-rule exceptions were **retired** in the same pass and no longer
appear in the DRU: `E6_R2_1_CLR` (0.100 mm local P3V3 clearance) and
`E6_R2_1_WIDTH` (0.15 mm P3V3 neck). All P3V3 copper now meets the ordinary
0.200 mm clearance and 0.600 mm width. **There is no longer any sub-0.200 mm
clearance exception at R2 to call out to the fabricator.**

The `XGPIO5` critical via described in §3b is unchanged by this pass.

---

## 4. Restoration

Nothing was deleted. Every DNP footprint is still on the board in its original
position, and no area was reclaimed. Restoring any function for the Final
product is a population change plus the routing of its nets — clearing the `dnp`
flag on the symbols, not re-laying out the board.

See `../BETA-DM-SCOPE-LEDGER.md` for the per-function Final restoration status
and `../BETA-DM-DNP-LIST.md` for the electrical evidence behind each cut.
