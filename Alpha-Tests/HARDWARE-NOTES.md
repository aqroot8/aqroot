---
tags: [alpha, hardware, gotchas]
status: alpha-build
---

# AQROOT Alpha — Hardware Notes & Gotchas

Hard-won board-specific lessons from bring-up. Read before touching hardware.

## Flashing / serial (CRITICAL)
- Board: Hosyond ESP32-S3 N16R8 (clone). Has TWO USB-C ports.
- Flash AND monitor via the **native USB port** — it enumerates as **COM11** here.
- Board setting: **USB CDC On Boot = Enabled**. With this on, Serial output comes out
  the native USB port (not the CH343 UART/COM port). Monitoring the UART port only
  shows boot noise, not sketch output.
- Board settings: ESP32S3 Dev Module, Flash Size 16MB, PSRAM = OPI PSRAM.
- If upload won't start: hold BOOT, tap RST, release BOOT, then Upload. If SHA-256
  verify fails / boots old firmware: set Upload Speed to 115200 and enable
  "Erase All Flash Before Sketch Upload".
- The first board unit was flaky (SHA-256 failures); switched to a spare which flashed
  cleanly. Keep the good unit as primary.

## Display (ILI9341, 2.8" 240x320 SPI, PASSED)
- LovyanGFX library. Config in 03_display_test.ino.
- Pins: SCLK=12, MOSI=11, MISO=13, DC/RS=14, CS=10, RST=21, LED->3V3, VCC->3V3.
- GOTCHA: MOSI and SCK are easy to swap. Swapped = backlit-but-black screen. If the
  screen lights but shows nothing, check MOSI(11)/SCK(12) first.

## Touch (FT6236 @ I2C 0x38, PASSED)
- Pins: CTP_SDA=1, CTP_SCL=2, CTP_RST=21 (shared with LCD_RST), CTP_INT=42.
- GOTCHA (important): the touch chip is held asleep until CTP_RST is pulsed low->high.
  Without the reset pulse it does NOT appear on an I2C scan. Always wake it first.
- Read registers: 0x02 = touch count, 0x03-0x06 = X/Y (12-bit, mask high nibble).

## Status
- PASSED: board/serial, I2C scan, display, touch.
- NEXT: CC1101 radio, then SX1262/LoRa, NFC, IR, microSD, IMU, power.
