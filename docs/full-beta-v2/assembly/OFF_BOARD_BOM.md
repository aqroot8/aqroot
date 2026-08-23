# AQROOT Full Beta v2 — off-board BOM, first five units

**Status: NORMATIVE.** Created 2026-08-23 at FBV2-S2-001. These are the items the **PCB** BOM will
not capture reliably, because they are not placed on the board. Authority:
[`../CTO_DECISIONS.md`](../CTO_DECISIONS.md).

**Quantities are per unit; order five plus spares.**

---

## 1. Display and touch

| item | MPN | qty | notes |
|---|---|---|---|
| **3.5″ IPS TFT + capacitive touch module** | **EastRising `ER-TFT035IPS-6`** with **`ER-TPC035-6`** touch | 1 | 320 × 480, ILI9488 COG, assembled outline **56.54 × 84.96 × 3.95 ± 0.25 mm**, one **50-pin 0.50 mm bottom-contact FPC, 0.30 ± 0.03 mm thick, 25.5 ± 0.15 mm wide**, carrying display **and** touch (touch on pins 44–47) |

> **THE PURCHASE ORDER MUST EXPLICITLY REQUEST THE `FT6236` TOUCH CONTROLLER.** EastRising offers
> the module with an alternative touch controller option; the AQROOT I²C address map, the
> `TOUCH_INT_N`/`TOUCH_RST_N` wiring and the reserved address **0x38** all assume FT6236.
> **A different controller changes the address and is a silent bring-up failure.**

---

## 2. Battery

| item | spec | qty | notes |
|---|---|---|---|
| Li-ion pouch cell with JST-PH-2 lead | **60 × 75 × 8.0 mm, ≈ 2500–3000 mAh**, 1S | 1 | Envelope frozen by **D-071**; **SKU chosen at procurement (M-04)**. Must mate `J4` `B2B-PH-K-S`. **Protection-circuit-module cells are acceptable and preferred**; the board's own reverse-polarity path does not replace a cell PCM |

---

## 3. RF — 433 MHz

| item | MPN | qty | evidence |
|---|---|---|---|
| **433 MHz internal flex antenna** | **Taoglas `FXP450.07.0100C`** | 1 | Taoglas **SPE-23-8-180-A**. **410–470 MHz** (the `E07-400M10S` covers 410–450), **I-PEX MHF1 (U.FL)** connector, **100 mm** cable, 3M adhesive. Stocked DigiKey **21704215**, Arrow, TTI |

**Module interface:** the `E07-400M10S` ships with **both an IPEX connector and stamp holes**
(manufacturer product description) — **no variant selection is required**, the IPEX socket is
present on the standard part number. Mates MHF1/U.FL directly.

---

## 4. RF — 915 MHz

| item | MPN | qty | evidence |
|---|---|---|---|
| **U.FL/MHF-I → SMA female bulkhead pigtail** | **Amphenol RF `095-902-568-150`** | 1 | Amphenol RF product page 2026-08-23: **Part Status ACTIVE**. AMC right-angle plug → **SMA straight bulkhead jack, IP67**, **RG-178**, **50 Ω**, **150 mm**, **6 GHz** max, 5.34 g, RoHS (exemption 6C). Amphenol's AMC series is **"compatible with Hirose U.FL and IPEX MHF1"** |
| **915 MHz external antenna, SMA male** | **to be selected at procurement** | 1 | A standard 868/915 MHz SMA-male whip. **Not yet selected — see O-8** |

**This is ONE assembly: the pigtail and the panel bulkhead are the same orderable part, so no
separate bulkhead MPN is needed.** Loss at 915 MHz is ≈ **0.4 dB** (RG-178 ≈ 1.2 dB/m × 0.15 m
plus two interfaces) against a +22 dBm module — negligible.

**Enclosure hardware:** the SMA bulkhead ships with its own nut and washer. The panel needs a
**Ø6.5 mm** clearance hole on the **top edge, left half**, **≥ 15 mm from either IR window**
(mechanical spec §8, B-52), and **≥ 8 mm edge-to-edge between the SMA body and either IR
aperture**. The right-angle AMC plug is the correct choice for a module lying flat — it keeps the
vertical stack low.

**Module interface:** the `E22-900M22S` likewise ships with **IPEX and stamp holes**.

---

## 5. NFC

| item | MPN | qty | evidence |
|---|---|---|---|
| **13.56 MHz NFC flex antenna** | **Taoglas `FXC.46.52.0075X.B.dg`** | 1 | Taoglas **SPE-24-8-104-B**: Ø46 mm, **reverse ferrite layer**, 75 mm twisted-pair 28 AWG with **ACH(F)** connector, peel-and-stick 3M adhesive. **The B variant is LOCKED (D-131)** — adhesive / flex / ferrite, for bonding to the **inside of the shell and reading outward**. **The A variant would put the ferrite between the coil and the tag and must never be ordered** |

Mates `J7` **`BM02B-ACHSS-GAN-ETF`** on the board.

---

## 6. Audio

| item | MPN | qty | notes |
|---|---|---|---|
| **Speaker** | **PUI Audio `AS02008MR-LW152-R`** | 1 | Ø20 × 3 mm, 8 Ω, 0.5 W rated / 0.8 W max, **500–4000 Hz voice band**, **152 mm AWG#32 leads** |
| Speaker mating housing | **JST `PHR-2`** | 1 | Mates `J6` |
| Speaker crimp contacts | **JST `SPH-002T-P0.5S`** | 2 | **D-148: the speaker crimps straight in, so it is replaceable without soldering** |

---

## 7. Battery harness

| item | MPN | qty | notes |
|---|---|---|---|
| Battery mating housing | **JST `PHR-2`** | 1 | Only if the cell is supplied without a lead |
| Battery crimp contacts | **JST `SPH-002T-P0.5S`** | 2 | As above |

---

## 8. Bring-up and validation aids — not shipped with the product

| item | qty | why |
|---|---|---|
| USB-C cable, USB 2.0 data-capable | 1 | The **only** service interface: console, ROM download **and** JTAG over the native USB Serial/JTAG. **A charge-only cable will look like a dead board** |
| **Accessory reference mating header — Samtec `TSW-112-07-L-D`** or any 0.64 mm square-post 2 × 12 with a **4.34–6.35 mm** mating post | 1–2 | Required to validate the community port at all. **D-093 names `TSW-112-07-L-D` (5.84 mm post) as the reference mate** |
| microSD card | 1 | Card-detect and SPI-A validation |
| NFC test tag (ISO 14443A) | 1 | NFC bring-up |

---

## 9. Open off-board items

| # | item |
|---|---|
| **O-8** | **The 915 MHz external antenna MPN is not selected.** Everything from the module to the bulkhead is now locked and orderable; the whip on the outside is not. It is an accessory-class purchase with no board impact, but it must exist before a range test means anything |
| **M-04** | Battery SKU — envelope frozen, SKU at procurement |
| — | Enclosure-side hardware beyond the SMA nut is **mechanical CAD scope**, deliberately not listed here |
