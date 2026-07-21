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
| MCP23017 I2C GPIO expander breakout | $3-6 |
| TPS63020 buck-boost 3.3V breakout | $8-12 |
| MAX17048 fuel gauge breakout (deferred — validate on Beta) | $5-10 |
| LiPo 2000mAh | $8-14 |
| bq25185 charger + power-path board | $5-10 |
| IR: TSOP38238 receiver + TSAL6200 940nm emitter | $2-5 |
| USB-C breakout, wiring, protoboard | $5-10 |
| 3D print filament (own Kobra S1) | $3-8 |
| **Total per unit** | **~$110-200** |

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
