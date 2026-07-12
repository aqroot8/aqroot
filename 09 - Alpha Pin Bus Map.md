---
tags: [hardware, alpha, pinmap, wiring]
status: alpha-build
---

# AQROOT Alpha — Pin / Bus Map

Wiring blueprint for the Alpha bench prototype. This same map becomes the Flux
schematic (each row = a net, each GPIO = a labeled pin on the ESP32-S3 symbol).

Target board: **ESP32-S3-DevKitC-1 N16R8** (bare module WROOM-1 in Beta).

## Reserved / off-limits pins (N16R8)
- GPIO 26–37 are consumed by flash/PSRAM (octal PSRAM) — DO NOT USE.
- GPIO 0, 3, 45, 46 are strapping pins. GPIO0 is fine as the BOOT button (its normal
  use); avoid the others for signals that are driven at boot.
- GPIO 19/20 = native USB. GPIO 43/44 = default UART0 serial console.

## Bus topology
- SPI bus 1 = Display + microSD (shared, separate CS)
- SPI bus 2 = CC1101 + SX1262 (shared, separate CS/IRQ/RST; firmware radio manager
  guarantees only one radio transmits at a time)
- I2C bus = capacitive touch + BMI270 IMU (shared, 4.7k pull-ups on SDA & SCL)
- NFC (ST25R3916 / X-NUCLEO) = its own SPI lines
- Single GPIO = IR TX/RX, button

## SPI Bus 1 — Display + microSD
| Signal | ESP32-S3 GPIO | Goes to |
|---|---|---|
| SCLK | GPIO12 | Display SCK + microSD SCK |
| MOSI | GPIO11 | Display SDA/MOSI + microSD MOSI |
| MISO | GPIO13 | microSD MISO (display is write-only) |
| Display CS | GPIO10 | Display CS |
| Display DC | GPIO14 | Display DC |
| Display RST | GPIO21 | Display RESET |
| Display BL | GPIO47 | Display backlight (or tie to 3V3) |
| microSD CS | GPIO48 | microSD CS |

## SPI Bus 2 — CC1101 + SX1262
| Signal | ESP32-S3 GPIO | Goes to |
|---|---|---|
| SCLK | GPIO4 | CC1101 SCK + SX1262 SCK |
| MOSI | GPIO5 | CC1101 MOSI + SX1262 MOSI |
| MISO | GPIO6 | CC1101 MISO + SX1262 MISO |
| CC1101 CS | GPIO7 | CC1101 CSN |
| CC1101 GDO0 | GPIO15 | CC1101 GDO0 (data/IRQ) |
| CC1101 GDO2 | GPIO16 | CC1101 GDO2 (optional) |
| SX1262 CS | GPIO17 | SX1262 NSS |
| SX1262 DIO1 | GPIO18 | SX1262 DIO1 (IRQ) |
| SX1262 BUSY | GPIO8 | SX1262 BUSY |
| SX1262 RST | GPIO3 | SX1262 RESET |

## I2C Bus — Touch + IMU
Add 4.7kOhm pull-ups on SDA and SCL (once, near the ESP32).
| Signal | ESP32-S3 GPIO | Goes to |
|---|---|---|
| SDA | GPIO1 | Touch SDA + BMI270 SDA |
| SCL | GPIO2 | Touch SCL + BMI270 SCL |
| Touch INT | GPIO42 | Capacitive touch interrupt |
| IMU INT | GPIO41 | BMI270 interrupt (optional) |

## NFC — ST25R3916 (X-NUCLEO-NFC06A1), own SPI
| Signal | ESP32-S3 GPIO | Goes to |
|---|---|---|
| SCLK | GPIO9 | X-NUCLEO SCK |
| MOSI | GPIO46 | X-NUCLEO MOSI |
| MISO | GPIO45 | X-NUCLEO MISO |
| NFC CS | GPIO40 | X-NUCLEO CS |
| NFC IRQ | GPIO39 | X-NUCLEO IRQ |

## Single GPIO — IR, button
| Signal | ESP32-S3 GPIO | Goes to |
|---|---|---|
| IR TX | GPIO38 | IR LED (via transistor) |
| IR RX | GPIO0 | TSOP38238 output (GPIO0 is a strapping pin — OK as input; if boot issues appear, move IR RX elsewhere) |
| Boot/recovery button | GPIO0 (onboard BOOT) | Use the DevKitC's onboard BOOT button |

## Power tree (no GPIO)
- bq25185 3V3 (buck output) -> ESP32-S3 3V3 rail + every module VCC
- bq25185 BAT -> LiPo (VERIFY POLARITY with a multimeter before connecting)
- bq25185 VU / USB-C -> charging input
- Common ground: every module GND ties together (most common breadboard mistake)

## Notes
- Wire in staged bring-up order, not all at once: DevKitC alone -> display -> touch ->
  radios -> NFC -> IR. Isolate each subsystem so any fault is traceable.
- This map is tight but fits with GPIO 26-37 excluded. No headroom for an expansion
  connector on Alpha — that is a Beta feature.
- Antennas: CC1101 ships with one; Core1262 (SX1262) uses a U.FL antenna (from the
  Heltec kit spare or a separate 915MHz U.FL). NEVER power/transmit a radio with no
  antenna attached — it can destroy the chip.
