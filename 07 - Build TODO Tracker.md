---
tags: [tasks, tracker]
---

# Build TODO Tracker

## Sourcing
- [ ] Find and vet a real supplier for the 2.13" AMOLED touch module (RM69090 driver,
      CST816-series touch, 502x410) — no mainstream hobbyist breakout found yet
- [ ] Confirm SX1262 certified module choice (e.g. Ebyte E22 series) and check
      certification conditions (RF section modification voids certification)
- [ ] Source PN532 breakout for prototype phase

## Firmware bring-up (in build order)
- [ ] Bootloader + display/touch driver bring-up on devkit
- [ ] App-launcher shell (LVGL 8.3.x)
- [ ] Radio driver via RadioLib (SX1262)
- [ ] NFC driver (breakout first)
- [ ] Sensors/audio driver

## Hardware
- [ ] Build Stage 1 dev-board prototype (see BOM tracker)
- [ ] Validate battery runtime against ~8 hour target
- [ ] Design PN532 antenna matching network for final PCB
- [ ] Design custom PCB (4-layer, JLCPCB)

## Project/business
- [ ] Set prototype budget ceiling
- [ ] Decide how many prototype units to build for reviewer seeding
- [ ] Prepare press kit for YouTuber outreach (see Kickstarter and Review Strategy note)
- [ ] Set Kickstarter launch date and reviewer embargo date
