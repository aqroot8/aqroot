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

## ST25R3916 NFC (PASSED - hardest chip in the build)
- Board: X-NUCLEO-NFC06A1 (ST Arduino shield, ST25R3916 chip). Wired to ESP32 by hand.
- SPI pins (dedicated, reused from SD test): SCK=39, MISO=41, MOSI=40, CS=42.
- Pin finding via ST manual UM2615 Table 2 + multimeter verification:
  CN5 GND = the hole with 3 pins to the board edge and 6 pins toward CN9.
  From GND toward CN9: SCK, MISO, MOSI, CS (CN5 pins 6,5,4,3 = D13,D12,D11,D10).
  CN6 power: 3V3 = 4th from left (lights PWR LED), 5V = 5th from left.
- POWER FINDING (important for Beta): board needs BOTH 3V3 and 5V. The ESP32-S3 devkit
  "5Vin" pin is input-only (measured 0.75V, not 5V) even though USB delivers 5V. Fed the
  NFC 5V pin from 3V3 instead; chip communicates fine over SPI at 3.3V. Full RF transmit
  power needs real 5V -> BETA POWER SYSTEM MUST INCLUDE A 5V BOOST for NFC RF. bq25185
  only outputs 3.3V.
- Validation: raw SPI read of IC Identity reg (0x3F) returned 0x2A. IC-type field = 0x05
  = ST25R3916 confirmed. SPI communication VALIDATED. (Full tag reading needs the ST rfal
  library port + 5V, deferred to firmware/Beta phase - same pattern as SD card.)
- Also a general pin-contention note for Beta: display + SD + 2 radios + NFC all want SPI.
  Beta pin map must plan shared SPI buses (dual-radio shared bus already proven to work).

## Status
- PASSED: board/serial, I2C scan, display, touch, CC1101 radio (SPI + RF reception),
  SX1262/LoRa, dual-radio coexistence on shared SPI bus, ST25R3916 NFC (SPI chip-ID
  probe validated).
- REMAINING (blocked on undelivered parts): IR (TSOP38238), IMU (BMI270), power (bq25185).
- NEXT SESSION: those three once parts arrive, then Beta schematic in Flux.
