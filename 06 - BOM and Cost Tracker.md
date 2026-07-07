---
tags: [bom, cost, budget]
---

# BOM and Cost Tracker

## Stage 1 — bare-minimum dev-board prototype (breakouts/devkits, hand-wired)

| Part | Est. cost (USD) |
|---|---|
| ESP32-S3 DevKitC-1 | $8-12 |
| 2.13" AMOLED touch module | $15-40 (unresolved sourcing — see Design Decisions Log) |
| PN532 breakout | $8-15 |
| SX1262 certified LoRa breakout (e.g. Ebyte E22) | $10-20 |
| 6-axis IMU breakout (BMI270-class) | $3-8 |
| I2S mic + small speaker | $5-10 |
| LiPo 1000mAh | $5-8 |
| Simple charge module (TP4056-class, non-load-sharing, prototype only) | $2-5 |
| IR LED + receiver | $2-5 |
| USB-C breakout, wiring, protoboard | $5-10 |
| 3D print filament (own Kobra S1) | $3-8 |
| **Total per unit** | **~$65-130** |

Budget 2-4 units at this stage if sending prototypes to reviewers ahead of a Kickstarter
launch.

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
