---
tags: [hardware, core-components]
---

# Hardware Core (always built in, no separate purchase)

| Subsystem | Part | Sourcing (final PCB) | Prototype sourcing | Notes |
|---|---|---|---|---|
| Compute | ESP32-S3-WROOM-1 (N16R8) | Bare module on custom PCB | DevKitC-1 devkit | 16MB flash, 8MB PSRAM, native USB flash/debug |
| Display | 2.13" AMOLED touch | Bare panel + driver (RM69090) + touch IC (CST816-series) | Same — needs dedicated sourcing research, no mainstream breakout found yet | 502x410 resolution, higher pixel density than the 3.5" LCD alternative we rejected |
| NFC/RFID | PN532 | Bare IC + tuned antenna matching network | Elechouse/Adafruit-style breakout | Prototype with proven breakout first, move to bare IC + matching network once firmware validated |
| Radio (LoRa + sub-GHz) | SX1262 | Certified breakout module (e.g. Ebyte E22 series) — PERMANENT, not bare IC | Same certified module | Bare IC skipped even for final design: multi-band RF matching is high-risk, and certified modules carry FCC/CE pre-certification needed if this ever reaches other people's hands |
| IR | IR LED + phototransistor receiver | Discrete parts | Same | Universal remote TX/RX |
| Sensors | 6-axis IMU (e.g. BMI270 or ICM-42670) | Bare IC | Breakout | Accel + gyro only — no magnetometer, since nothing in the feature set uses compass heading and it adds calibration complexity for no gain |
| Audio | I2S digital mic + small speaker/buzzer | — | — | Digital I2S chosen over analog for simpler ESP32-S3 interfacing |
| Wireless | Wi-Fi + Bluetooth | Native to ESP32-S3 | Native | No extra chip needed |
| Power | LiPo 1000mAh | — | — | Sized for AMOLED + Wi-Fi + LoRa/sub-GHz combined draw; target ~8 hours active use |
| Charge mgmt | Load-sharing charge IC (e.g. MCP73871-class) | — | Simple TP4056-style module OK for dev-board prototype | Device stays usable while charging — matters for a workbench tool |
| Fuel gauge | MAX17048 | — | — | Battery percentage for UI |
| USB-C | — | — | — | Power + native USB flashing/serial |
| Buttons | 1x hardware boot/recovery button + 1x physical power switch | — | — | Touchscreen-only input needs a hardware fallback for bricked firmware |
| Status | RGB LED | — | — | At-a-glance state without waking the screen |
| Storage | microSD slot | — | — | Kept in core — cheap, small, genuinely useful for capture/log storage |
| Expansion | GPIO header | 12 pins, 3.3V logic only | — | No 5V passthrough — most connected modules run 3.3V natively |

> [!note] Alpha bench prototype deviations (July 2026)
> The Alpha bench build deviates from this table in two places — see
> [[09 - Alpha Pin Bus Map]]: NFC is prototyped on an ST25R3916 (X-NUCLEO-NFC06A1
> eval board, own SPI bus) instead of a PN532 breakout, and a CC1101 is wired
> alongside the SX1262 for sub-GHz work (shared SPI, one-TX-at-a-time radio manager).

## Antenna placement
- SX1262: external stub via SMA connector
- PN532 (NFC): internal flat coil, read window on the BACK face of the device
