---
tags: [hardware, core-components]
---

# Hardware Core (always built in, no separate purchase)

| Subsystem | Part | Sourcing (final PCB) | Prototype sourcing | Notes |
|---|---|---|---|---|
| Compute | ESP32-S3-WROOM-1 (N16R8) | Bare module on custom PCB | DevKitC-1 devkit | 16MB flash, 8MB PSRAM, native USB flash/debug |
| Display | 2.8" IPS LCD, ILI9341 + FT6236 capacitive touch @ 0x38 | Panel module, standard 4-wire SPI | Same — Alpha-validated part | 240x320. AMOLED (RM69090) is a Kickstarter STRETCH GOAL board revision, not the baseline |
| NFC/RFID | ST25R3916 | Bare IC + tuned antenna matching network | X-NUCLEO-NFC06A1 eval board | SPI interface (not I2C). Alpha-validated (IC-ID 0x2A). Needs 3V3 + a switched 5V PA rail for full RF TX |
| Radio — sub-GHz | CC1101 | Module/bare IC on shared SPI Bus B | Blue 433M V2.0 CC1101 board | DUAL-RADIO: ships alongside the SX1262, not instead of it. OOK/ASK/FSK capture + replay |
| Radio — LoRa + sub-GHz | SX1262 | Certified breakout module (e.g. Ebyte E22 series) — PERMANENT, not bare IC | Waveshare Core1262 | Bare IC skipped even for final design: multi-band RF matching is high-risk, and certified modules carry FCC/CE pre-certification needed if this ever reaches other people's hands |
| IR | IR LED + phototransistor receiver | Discrete parts | Same | Universal remote TX/RX |
| Sensors | 6-axis IMU — BMI270 | Bare IC | SparkFun BMI270 Qwiic breakout | I2C 0x68, Alpha-validated (accel/gyro functional). Accel + gyro only — no magnetometer, since nothing in the feature set uses compass heading and it adds calibration complexity for no gain |
| Audio | ICS-43434 I2S MEMS mic + MAX98357A I2S Class-D amp + 4/8ohm speaker | — | Breakouts | Digital I2S chosen over analog for simpler ESP32-S3 interfacing. ICS-43434 chosen over INMP441 (discontinued). Bench validation pending |
| Wireless | Wi-Fi + Bluetooth | Native to ESP32-S3 | Native | No extra chip needed |
| Power | LiPo 2000mAh | — | — | ~12-15hr active, ~2wk standby (see [[13 - Power Budget and Battery Runtime v0.1]]). 2500-3000mAh open if enclosure volume allows |
| 3.3V rail | TI TPS63020 buck-boost | — | Breakout module | Separate part — the bq25185 SYS output is NOT a clean 3.3V rail. 2A capacity, ~2x headroom |
| Charge mgmt | bq25185 (linear charger + power-path) | — | bq25185 breakout | Device stays usable while charging. REVERSE-POLARITY PROTECTION REQUIRED at the battery input. Start Beta at ~500mA charge current pending enclosure thermal testing |
| Fuel gauge | MAX17048 | — | — | Battery percentage for UI |
| USB-C | — | — | — | Power + native USB flashing/serial |
| Buttons | 1x hardware boot/recovery button + 1x physical power switch | — | — | Touchscreen-only input needs a hardware fallback for bricked firmware |
| Status | RGB LED | — | — | At-a-glance state without waking the screen |
| Storage | microSD slot | — | — | Kept in core — cheap, small, genuinely useful for capture/log storage |
| Expansion | GPIO header | ~7 slow GPIO, 3.3V logic only | — | Off the MCP23017 expander. NOT 12 — the MCP23017 has 14 bidirectional + 2 output-only pins, and internal control signals consume most of them (see [[11 - Beta Pin Map v0.2]] §7). No 5V passthrough |
| Expansion | RootProbe connector | Footprint reserved | — | High-speed coprocessor accessory interface, Phase 2. Distinct from the slow GPIO header above — see [[14 - RootProbe Interface v0.1]] |

> [!note] Radio coexistence
> Both radios and Wi-Fi/BT share the device: firmware enforces that only ONE radio
> TRANSMITS at a time (multiple may receive simultaneously). CC1101 and SX1262 share
> SPI Bus B with CS discipline — validated on Alpha hardware, see
> [[09 - Alpha Pin Bus Map]] and [[Alpha-Tests/HARDWARE-NOTES]].

## Antenna placement
Per [[12 - RF and Antenna Plan v0.1]] and the [[15 - Enclosure Field Slate v3]] zoning:
- Wi-Fi/BLE 2.4GHz: ESP32-S3 module onboard PCB antenna, upper-RIGHT crown (keep-out only)
- LoRa 915MHz: internal FPC antenna, upper-LEFT sidewall / crown edge
- Sub-GHz 433MHz: electrically-shortened antenna in the RF crown (top-LEFT, max volume);
  optional screw-on external whip via U.FL/SMA, stowed in the side holder
- NFC (ST25R3916): internal flat coil, read window on the BACK face of the device — no
  metal behind the loop
