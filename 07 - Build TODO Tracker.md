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
First implementation pass complete — full driver + UI stack written and verified compiling
for both the real-hardware and Wokwi simulation environments. See `Firmware/` and its
README. Real hardware still needs on-device validation once parts arrive.
- [x] Bootloader + display/touch driver bring-up on devkit — LovyanGFX + LVGL glue;
      touch is a real CST816 I2C driver; display panel is a generic ILI9341 PLACEHOLDER
      standing in for the RM69090 AMOLED until it is sourced
- [x] App-launcher shell (LVGL 8.3.x) — tile dashboard (Scan/NFC/Infrared/GPIO/Bluetooth/
      Tools) + Signal Monitor and NFC Tag panels, plus one screen per tile
- [x] Radio driver via RadioLib (SX1262) — both LoRa and raw sub-GHz FSK modes
- [x] NFC driver (breakout first) — Adafruit_PN532 real tag read + Mifare Classic block write
- [x] Sensors/audio driver — generic I2C 6-axis IMU (placeholder part) + ESP32 I2S audio

## Firmware follow-ups (post first-pass)
- [ ] Swap the placeholder ILI9341 display config for the real RM69090 AMOLED init once the
      panel is sourced (UI is resolution-independent, so this is a driver-only change)
- [ ] Lock the IMU part (BMI270 vs ICM-42670), add its library to platformio.ini, and swap
      the generic register map in sensors.cpp
- [ ] Add a real IR driver (RMT-based TX/RX) — ir_screen is currently a UI shell only
- [ ] Reconcile all placeholder pins in Firmware/src/config.h with the final PCB pinout
- [ ] On-device validation of every driver once prototype hardware is assembled

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
