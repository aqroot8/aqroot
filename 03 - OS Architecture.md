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
1. Bootloader + display/touch driver (get something on screen first)
2. App-launcher shell
3. Radio (SX1262) driver via RadioLib
4. NFC driver (starting on breakout, later bare IC)
5. Sensors/audio driver (lowest architectural risk, do last)

## File system
LittleFS on internal flash, or FAT on microSD (microSD is kept in the core build).
