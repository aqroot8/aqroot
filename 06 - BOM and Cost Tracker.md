---
tags: [bom, cost, budget]
---

# BOM and Cost Tracker

## Stage 1 — bare-minimum dev-board prototype (breakouts/devkits, hand-wired)

| Part | Est. cost (USD) |
|---|---|
| ESP32-S3 DevKitC-1 (N16R8) | $8-12 |
| 2.8" IPS ILI9341 capacitive-touch SPI module (FT6236 @ 0x38) | $12-20 (sourcing resolved — Elecrow / LCDwiki class) |
| ST25R3916 NFC — X-NUCLEO-NFC06A1 eval board | $25-35 |
| CC1101 sub-GHz module (433MHz, e.g. blue 433M V2.0) | $3-8 |
| SX1262 certified LoRa breakout (e.g. Ebyte E22 / Waveshare Core1262) | $10-20 |
| BMI270 6-axis IMU breakout (SparkFun Qwiic) | $3-8 |
| ICS-43434 I2S MEMS mic breakout | $5-8 |
| MAX98357A I2S Class-D amp breakout | $5-8 |
| Small 4/8ohm speaker (~1-2W) | $2-5 |
| **TI TCA9535PWR** I2C GPIO expander **x2** — U60 @ 0x20 internal + U61 @ 0x21 community header (PW / TSSOP-24 / 0.65mm) | $2-6 (bare ICs; **no validated breakout — see note**) |
| TPS63020 buck-boost 3.3V breakout (production P/N: TPS63020DSJR) | $8-12 |
| MAX17048 fuel gauge breakout (deferred — validate on Beta) | $5-10 |
| LiPo 2000mAh | $8-14 |
| bq25185 charger + power-path board | $5-10 |
| **Reverse-polarity protection — NO FINAL P/N CLAIMED (parked)**. *Provisional only:* ADI **LTC4368-1** controller (MSOP / 3×3 DFN) + **2x AO3400A-class** N-channel FETs (AOS AO3400A, LCSC C20917, SOT-23) + sense resistor, UV/OV divider, timer/inrush parts and gate clamp — **all values and P/Ns unselected**. See note below. | $2-6 **(provisional estimate — not a quote)** |
| IR: TSOP38238 receiver + TSAL6200 940nm emitter + low-side MOSFET driver stage | $2-6 |
| 7x tactile buttons (D-pad up/down/left/right + A/B + Home) + physical power switch | $2-5 |
| I2C bus buffer/isolator or bus switch (external header protection) — part TBD | $1-3 |
| Accessory-rail load switch (driven by ACC_PWR_EN) — part TBD | $0.50-2 |
| USB-C breakout, wiring, protoboard | $5-10 |
| 3D print filament (own Kobra S1) | $3-8 |
| **Total per unit** | **~$110-200** |

> **Reverse-polarity protection note (2026-07-30) — no final part number is claimed.** The
> topology is **PARKED**: high-side only, battery negative tied to system GND. The **leading
> candidate is provisional only** — ADI **LTC4368-1** (active back-to-back N-FET controller,
> ~2.5–60 V, ~80 µA Iq, forward/reverse sense ~±50 mV) driving **two series back-to-back
> N-channel AO3400A-class** FETs (AOS AO3400A, LCSC C20917, SOT-23, 30 V, ~48 mΩ @ Vgs 2.5 V,
> Vgs max ±12 V). **AO3401A (LCSC C15127)** remains a valid building block *if* a PMOS variant
> is chosen; a single PMOS alone is rejected as a final solution. **Do not order these as
> final.** The sense resistor, UV/OV divider (3.0–4.2 V), timer/inrush parts, gate clamp and
> package are all unselected, and the cost line above is a placeholder estimate rather than a
> quote. **Final topology lock belongs to the professional power/DFM pre-fabrication review**,
> which must run the LTC4368 LTspice charge-path case and obtain ADI vendor/FAE confirmation.
> **No PCB routing or fabrication release until that gate closes.** See
> [[05 - Design Decisions Log]].

> **GPIO expander note (2026-07-27):** the expander was changed from the MCP23017 to the **TI
> TCA9535PWR** (see [[05 - Design Decisions Log]]). The MCP23017 breakout that was bought and
> bench-tested during Alpha is **no longer the design part** — that spend is sunk, and the board
> is still useful for I2C-architecture work, but it validates nothing about the TCA9535. The
> TCA9535PWR is **TSSOP-24 only in this package**, so Stage 1 hand-wiring needs either a
> TSSOP-24 breakout adapter board or a TCA9535 module; budget a few dollars for adapters. **This
> part is datasheet-trusted and unvalidated — its first hardware confirmation is on Beta.**

> Cost went UP vs the original ~$65-130 estimate, for three deliberate reasons: the
> dual-radio base adds a CC1101, the NFC part moved from a ~$10 PN532 breakout to a ~$30
> X-NUCLEO ST25R3916 eval board (the validated part), and the power tree gained a separate
> TPS63020 regulator. Partly offset by the ILI9341 display coming in under the AMOLED
> estimate. The X-NUCLEO board is an Alpha/prototype cost only — production uses a bare
> ST25R3916 + matching network, which is far cheaper.

Budget 2-4 units at this stage if sending prototypes to reviewers ahead of a Kickstarter
launch (~$110-200 each).

## Stage 2 — custom PCB prototype (small batch, later stage, not v1)

Small JLCPCB run (~5 boards), 4-layer, with JLCPCB assembly service for SMD parts:
estimated $150-350 for the batch, depending on final BOM and how much you hand-solder
yourself (headers, connectors, battery wiring) to reduce assembly fees.

## Prototype-to-production strategy
Plan: prove core functionality (NFC read, sub-GHz scan, IR blast, LoRa, UI navigation) on
Stage 1 dev-board prototypes for the Kickstarter campaign, then finish the final custom PCB,
certified antenna tuning, and manufacturable enclosure during the funded production phase.
This is standard practice for hardware campaigns.

IMPORTANT: only demo features that actually work on the prototype. Kickstarter's rules and
general reputational risk both require not presenting non-functional concepts as working
features. If a feature isn't working yet, label it "in development," don't demo it as if
it works.

## Open item
- Total prototype budget ceiling: not yet set by [YOUR NAME] — fill in once decided.
