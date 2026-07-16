---
tags: [hardware, beta, pinmap, schematic]
status: beta-planning
---

> **SUPERSEDED by [[11 - Beta Pin Map v0.2]]** (three-way review corrections + ILI9341
> display decision). Kept for history.

# AQROOT Beta — Master Pin Map

The complete, conflict-free pin allocation for the Beta PCB. Every subsystem has a
permanent home simultaneously (unlike Alpha, where pins were reused one test at a time).
This document feeds directly into the Flux/KiCad schematic. Validated against the
ESP32-S3-WROOM-1 N16R8 reserved pins (GPIO 26-37 consumed by octal PSRAM/flash).

## Key architecture decisions (from Alpha validation)
- Two shared SPI buses (proven to work with CS discipline in Alpha).
- SPI Bus B carries THREE devices (both radios + NFC), each with its own CS. The
  firmware radio manager MUST deselect the idle device (drive CS high) - a floating CS
  on the idle device corrupts shared MISO. This was validated on hardware in Alpha.
- An MCP23017 I2C GPIO expander (16 extra GPIO) carries all "slow" signals, freeing
  native pins for I2S audio and keeping the full N16R8 8MB PSRAM for the AMOLED.
- Power: NFC RF needs a real 5V rail (validated in Alpha - the chip talks at 3.3V but
  full RF transmit needs 5V). bq25185 only outputs 3.3V, so Beta needs a 5V boost
  converter for the NFC VDD rail.

## SPI Bus A - Display + microSD (shared SCK/MOSI/MISO, separate CS)
| Signal | GPIO |
|---|---|
| SCK | 12 |
| MOSI | 11 |
| MISO | 13 |
| Display CS | 10 |
| Display DC | 14 |
| Display RST | 21 |
| Display backlight | 47 |
| microSD CS | 48 |

## SPI Bus B - CC1101 + SX1262 + NFC (shared, CS-discipline radio manager)
| Signal | GPIO |
|---|---|
| SCK | 4 |
| MOSI | 5 |
| MISO | 6 |
| CC1101 CS | 7 |
| CC1101 GDO0 | 15 |
| CC1101 GDO2 | 16 |
| SX1262 CS | 17 |
| SX1262 DIO1 | 18 |
| SX1262 BUSY | 8 |
| SX1262 RST | 3 (strapping pin - validated OK in Alpha) |
| NFC CS | 9 |
| NFC IRQ | 38 |

## I2C Bus - Touch + IMU + Fuel gauge + GPIO expander (2 native pins)
| Device | I2C address | Notes |
|---|---|---|
| SDA | - | GPIO1 |
| SCL | - | GPIO2 |
| Touch (FT6236) | 0x38 | validated in Alpha |
| IMU (BMI270) | 0x68 | |
| Fuel gauge (MAX17048) | 0x36 | |
| MCP23017 GPIO expander | 0x20 | 16 extra GPIO |
| MCP23017 INT (optional) | - | GPIO42 |

## Native GPIO - I2S audio (needs fast native pins)
| Signal | GPIO |
|---|---|
| I2S BCLK | 39 |
| I2S LRCLK/WS | 40 |
| I2S DOUT (speaker) | 41 |
| I2S DIN (mic) | 45 (strapping - verify, or relocate) |

## MCP23017 expander - slow signals (16 GPIO: GPA0-7, GPB0-7)
| Expander pin | Function |
|---|---|
| GPA0 | IR TX (via transistor) - SEE VERIFY NOTE |
| GPA1 | IR RX (TSOP38238) |
| GPA2 | RGB status LED |
| GPA3 | Boot/recovery button (or keep on native GPIO0) |
| GPA4-7, GPB0-7 | Expansion header (12 GPIO for community add-ons) |

## Power tree
- Main 3V3 rail: ESP32-S3 + all logic + most peripherals.
- 5V BOOST CONVERTER -> NFC VDD (required for NFC RF transmit; Alpha finding).
- bq25185 charger (3.3V buck output) + LiPo + MAX17048 fuel gauge.

## Open items to verify (in Alpha, when parts arrive, or in Beta firmware)
- IR TX timing: IR transmit uses a 38kHz carrier needing precise timing. The MCP23017
  expander adds latency and MAY be too slow for IR TX. Recommendation: keep IR TX on a
  NATIVE pin, put only slow signals (IR RX, LED, button, expansion) on the expander.
  Finalize IR TX placement after the Alpha IR test (TSOP38238 not yet delivered).
- GPIO45 (I2S mic) is a strapping pin - verify it behaves as an input at boot, or
  relocate the I2S DIN.
- Confirm the AMOLED framebuffer performance with N16R8 8MB PSRAM (should be fine).

## Boot/strapping pins in use (handle with care)
- GPIO0 (boot button - normal use), GPIO3 (SX1262 RST - validated), GPIO45 (I2S mic -
  verify). Avoid driving 45/46 during boot.

## Pin budget summary
Using two shared SPI buses + one shared I2C bus + the MCP23017 expander, every subsystem
fits on the N16R8 with the full 8MB PSRAM retained and room to spare on the expander.
