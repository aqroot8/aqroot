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
Use RadioLib (actively maintained, explicit SX1262 support) as the base for the radio
driver rather than writing LoRa/FSK/OOK register-level code from scratch.

## Build order
1. Bootloader + display/touch driver (get something on screen first) — **implemented**
2. App-launcher shell — **implemented**
3. Radio (SX1262) driver via RadioLib — **implemented** (LoRa + raw sub-GHz FSK)
4. NFC driver (starting on breakout, later bare IC) — **implemented** (PN532 read + write)
5. Sensors/audio driver (lowest architectural risk, do last) — **implemented**

## Implementation status
All five driver layers plus the LVGL UI shell have a first working implementation, on the
**Arduino core for ESP32-S3** (ESP-IDF/FreeRTOS still underneath). Verified compiling for
real hardware and for a Wokwi simulation build; on-device validation pending hardware. See
`Firmware/` and `Firmware/README.md`. Final vs placeholder parts, and a `SIMULATION_MODE`
that mocks radio/NFC/audio for hardware-free testing, are documented there and in the
Design Decisions Log. Not yet built: an IR driver (the Infrared UI tile is a shell for now).

## File system
LittleFS on internal flash, or FAT on microSD (microSD is kept in the core build).
