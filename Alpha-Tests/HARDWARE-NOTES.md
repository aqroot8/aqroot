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

## CC1101 Sub-GHz radio (PASSED)
- Module: blue 433M V2.0 CC1101 board, 8-pin 2x4 header, SMA antenna attached.
- Library: RadioLib. Uses a SEPARATE SPI instance (HSPI) so it does not collide with
  the display on SPI bus 1.
- Pins (SPI bus 2): SCK=4, MISO=6, MOSI=5, CS=7, GDO0=15, GDO2=16, VCC=3V3, GND=GND.
- CAUTION: VCC is 3.3V ONLY. 5V will destroy the chip.
- SPI init test PASSED (chip alive and talking).
- RF reception test PASSED: noise floor ~-87 dBm; a 433MHz car key fob press spiked
  RSSI ~40 dB above noise. Confirmed real 433MHz reception.
- Note: a US car key fob triggered on 433.92 MHz (not all US fobs are 315MHz).
- The QIACHIP kit's transmitter is a TX118SA-4 (needs power + K1-K4 pin pulled to GND
  to transmit); the RX480E is the receiver. Not needed for this test since a car fob
  worked, but available for future capture/replay work.

## Status
- PASSED: board/serial, I2C scan, display, touch, CC1101 radio (SPI + RF reception).
- NEXT: SX1262/LoRa, then NFC, IR, microSD, IMU, power.
