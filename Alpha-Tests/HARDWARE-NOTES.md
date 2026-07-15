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

## SX1262 LoRa radio + DUAL-RADIO coexistence (PASSED - MAJOR MILESTONE)
- Module: Waveshare Core1262 (SX1262 LoRa Node HF, 850-930MHz, 22dBm, U.FL antenna).
- MUST attach U.FL antenna before powering/transmitting.
- Pins (shared SPI bus 2): CLK=4, MOSI=5, MISO=6 (SHARED with CC1101),
  CS=17, DIO1=18, BUSY=8, RESET=3. VCC=3V3, GND=GND.
- GOTCHA 1: MOSI/MISO were swapped at first -> code -2. Verify orientation.
- GOTCHA 2 (CRITICAL for Beta firmware): on the shared bus, the idle radio's CS
  MUST be driven HIGH (deselected) while the other radio is active. A floating CS
  on the idle radio corrupts shared MISO and causes -2. This is the core rule the
  Beta "radio manager" must enforce: only one radio selected at a time.
- BUSY pin reads 0 when the SX1262 is powered and idle (useful alive-check).
- RESET on GPIO3 (a strapping pin) works fine for the SX1262 - no issue observed.
- DUAL-RADIO TEST PASSED: both CC1101 and SX1262 init successfully on the same
  shared SPI bus in one program, with CS discipline. THE TWO-RADIO ARCHITECTURE
  IS VALIDATED ON HARDWARE. This was the biggest engineering risk in the project.

## Status
- PASSED: board/serial, I2C scan, display, touch, CC1101 radio (SPI + RF reception),
  SX1262/LoRa, dual-radio coexistence on shared SPI bus.
- NEXT: NFC, IR, microSD, IMU, power.
