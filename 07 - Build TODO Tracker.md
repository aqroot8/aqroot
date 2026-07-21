---
tags: [tasks, tracker]
---

# Build TODO Tracker

## Sourcing
- [x] Display sourced — 2.8" IPS ILI9341 capacitive SPI (Elecrow / LCDwiki class).
      AMOLED is now a Kickstarter stretch goal, not a sourcing task.
- [~] VERIFY the exact display module's touch controller is FT6236-family @ I2C 0x38
      before ordering Beta quantity — many cheap ILI9341 modules ship resistive (XPT2046)
      or a different capacitive chip (FT6336/GT911, possibly different address)
- [ ] Confirm SX1262 certified module choice (e.g. Ebyte E22 series) and check
      certification conditions (RF section modification voids certification)
- [ ] Select the production CC1101 part/module (dual-radio base — Alpha used a generic
      blue 433M V2.0 board)

## Firmware bring-up (in build order)
First implementation pass complete — full driver + UI stack written and verified compiling
for both the real-hardware and Wokwi simulation environments. See `Firmware/` and its
README. Real hardware still needs on-device validation once parts arrive.

- [x] Bootloader + display/touch driver bring-up on devkit — LovyanGFX + LVGL glue;
      ILI9341 panel config is the REAL Beta part (not a placeholder); touch driver logic
      is FT6236-compatible
- [x] App-launcher shell (LVGL 8.3.x) — tile dashboard (Scan/NFC/Infrared/GPIO/Bluetooth/
      Tools) + Signal Monitor and NFC Tag panels, plus one screen per tile
- [x] Radio driver via RadioLib (SX1262) — both LoRa and raw sub-GHz FSK modes
- [x] NFC driver (breakout first) — Adafruit_PN532 real tag read + Mifare Classic block write
- [x] Sensors/audio driver — generic I2C 6-axis IMU (placeholder part) + ESP32 I2S audio

## Firmware follow-ups (post first-pass)

Three of these are real engineering tasks created by locked part decisions, not cleanup.
They are the outstanding firmware debt between the current code and the Beta design:

- [ ] **Replace the PN532 I2C NFC driver with an ST25R3916 SPI driver.** The current
      `drivers/nfc.cpp` + the `adafruit/Adafruit PN532` dependency in platformio.ini target
      the wrong chip AND the wrong bus. The Alpha raw-SPI validation (IC-ID 0x3F -> 0x2A) is
      the foundation; full tag read/write needs the ST RFAL library port.
- [ ] **Add a CC1101 driver + a radio manager spanning both radios.** Firmware is currently
      SX1262-only. Dual-radio is locked for production, so the manager must enforce
      one-TX-at-a-time and CS discipline across CC1101 + SX1262 on shared SPI Bus B.
- [ ] **Add a real IR driver (RMT-based TX/RX)** on native pins 43/44, 38kHz carrier —
      `ir_screen` is currently a UI shell only. Parts (TSOP38238 + TSAL6200) arriving
      2026-07-21.
- [ ] Add the SparkFun BMI270 library to platformio.ini and swap the generic register map in
      sensors.cpp. The part is LOCKED (BMI270, Alpha-validated at 0x68) — but the BMI270
      needs a config-blob upload before accel/gyro data works, which raw register poking
      does not do.
- [ ] Add an FT6236 reset pulse to `touch_init()`. Alpha gotcha: the touch controller is held
      asleep until CTP_RST is pulsed low->high and does NOT appear on an I2C scan without it.
      Beta shares touch RST with display RST on GPIO21.
- [ ] Reconcile Firmware/src/config.h pin assignments with [[11 - Beta Pin Map v0.2]] —
      every bus currently differs (display DC/RST, I2C on 17/18 vs 1/2, radio sharing the
      display bus, I2S on the wrong pins). Config.h is still placeholder wiring matched to
      the Wokwi diagram.
- [ ] On-device validation of every driver once prototype hardware is assembled

## Hardware
- [ ] Build Stage 1 dev-board prototype (see BOM tracker)
- [ ] Validate battery runtime against the ~12-15hr active target (2000mAh) — see
      [[13 - Power Budget and Battery Runtime v0.1]]
- [ ] Design ST25R3916 NFC antenna matching network for final PCB
- [ ] Design custom PCB (4-layer, JLCPCB)
- [ ] Reverse-polarity protection at the battery input + keyed connector + a battery tray
      that can't invite reversed insertion (from the bench incident — see
      [[05 - Design Decisions Log]])
- [ ] Remaining Alpha validation: IR, audio (ICS-43434 + MAX98357A), MCP23017 expander,
      TPS63020 3.3V rail, bq25185 charging path

## Project/business
- [ ] Set prototype budget ceiling
- [ ] Decide how many prototype units to build for reviewer seeding
- [ ] Prepare press kit for YouTuber outreach (see Kickstarter and Review Strategy note)
- [ ] Set Kickstarter launch date and reviewer embargo date
