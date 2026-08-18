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
| `aqroot-Beta-DM-DO-NOT-POPULATE.csv` | the 34 DNP refs with a reason each | assembly control / incoming check |
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
    --fields 'Reference,Value,Footprint,${QUANTITY},${DNP},MPN,Manufacturer,LCSC' \
    --labels 'Refs,Value,Footprint,Qty,DNP,MPN,Manufacturer,LCSC' \
    --group-by 'Value,Footprint,${DNP}' aqroot-Beta-DM.kicad_sch

kicad-cli sch export bom  --output ../../fab/aqroot-Beta-DM-BOM-fitted.csv --exclude-dnp \
    --fields 'Reference,Value,Footprint,${QUANTITY},MPN,Manufacturer,LCSC' \
    --labels 'Refs,Value,Footprint,Qty,MPN,Manufacturer,LCSC' \
    --group-by 'Value,Footprint' aqroot-Beta-DM.kicad_sch

kicad-cli pcb export pos --output ../../fab/aqroot-Beta-DM-pos-fitted.csv \
    --format csv --units mm --side both --exclude-dnp aqroot-Beta-DM.kicad_pcb

kicad-cli pcb export pdf --output ../../fab/aqroot-Beta-DM-assembly-top.pdf \
    --layers F.Fab,F.Silkscreen,Edge.Cuts --include-border-title --black-and-white \
    aqroot-Beta-DM.kicad_pcb
```

`aqroot-Beta-DM-DO-NOT-POPULATE.csv` is derived from the full BOM with the
per-part reasons in this document.

---

## 1. DO NOT POPULATE — 29 Demo Model parts

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

---

## 2. FITTED — parts that look droppable but are not

| ref | value | why it stays |
|---|---|---|
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

## 4. Restoration

Nothing was deleted. Every DNP footprint is still on the board in its original
position, and no area was reclaimed. Restoring any function for the Final
product is a population change plus the routing of its nets — clearing the `dnp`
flag on the symbols, not re-laying out the board.

See `../BETA-DM-SCOPE-LEDGER.md` for the per-function Final restoration status
and `../BETA-DM-DNP-LIST.md` for the electrical evidence behind each cut.
