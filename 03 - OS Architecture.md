---
tags: [firmware, architecture]
---

# Custom OS Architecture

Layered stack, bottom to top:

1. **ESP32-S3 hardware** — physical SoC and peripherals
2. **ESP-IDF + FreeRTOS** — real-time OS and hardware abstraction layer (HAL)
3. **Driver abstraction layer** — one stable interface per subsystem so apps never touch
   registers directly: Display, Radio (LoRa + sub-GHz), NFC, Sensors/audio
4. **App launcher / UI shell** — built on LVGL 8.3.x (stable branch — avoiding 9.x's
   breaking API changes and thinner example coverage for this display combo)
5. **Apps** — v1 is a simple menu of flashable .bin files, selected via the UI. A full
   filesystem-based app-launcher with manifests/icons is a later-stage goal, not v1 scope.

## Radio driver
Use RadioLib (actively maintained, explicit SX1262 AND CC1101 support) as the base for the
radio driver rather than writing LoRa/FSK/OOK register-level code from scratch.

AQROOT is a DUAL-RADIO device (CC1101 + SX1262, both core). The driver layer must therefore
present a radio manager above the two chips that: shares SPI Bus B with strict CS discipline
(a floating CS on the idle radio corrupts shared MISO — validated in Alpha), and enforces
that only ONE radio TRANSMITS at a time (multiple may receive). Currently only the SX1262
half is implemented.

## Build order
1. Bootloader + display/touch driver (get something on screen first) — **implemented**
2. App-launcher shell — **implemented**
3. Radio driver via RadioLib — **partially implemented**: SX1262 done (LoRa + raw sub-GHz
   FSK); CC1101 driver and the dual-radio manager are outstanding
4. NFC driver — **needs rewrite**: implemented against PN532/I2C, but the locked part is
   the ST25R3916 over SPI (wrong chip and wrong bus)
5. Sensors/audio driver (lowest architectural risk, do last) — **implemented**

## Implementation status
All five driver layers plus the LVGL UI shell have a first working implementation, on the
**Arduino core for ESP32-S3** (ESP-IDF/FreeRTOS still underneath). Verified compiling for
real hardware and for a Wokwi simulation build; on-device validation pending hardware. See
`Firmware/` and `Firmware/README.md`. A `SIMULATION_MODE` mocks radio/NFC/audio for
hardware-free testing.

**Known gap between firmware and the locked Beta design** (tracked in
[[07 - Build TODO Tracker]]): the NFC driver targets the wrong chip and bus (PN532/I2C vs
the locked ST25R3916/SPI); there is no CC1101 driver or dual-radio manager; there is no IR
driver (the Infrared tile is a UI shell); and config.h pin assignments are still placeholder
wiring matched to the Wokwi diagram rather than [[11 - Beta Pin Map v0.2]].

## File system
LittleFS on internal flash, or FAT on microSD (microSD is kept in the core build).
