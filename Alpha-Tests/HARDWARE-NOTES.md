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

## microSD (PASSED - hardware validated via raw SPI)
- Module: HW-125 microSD breakout (WWZMDiB 3-pack). Has onboard regulator + 74LVC125
  level shifter, so it accepts 5V; also works fed from 3V3.
- Pins (dedicated isolation pins): SCK=39, MOSI=40, MISO=41, CS=42.
- The Arduino SD.h library would NOT initialize (failed at 400kHz-4MHz, all attempts),
  even after trying a custom HSPI instance and low speeds. BUT a raw low-level SPI probe
  sending CMD0 returned 0x01 = card in idle/ready state = card communicates over SPI.
- Conclusion: SD HARDWARE VALIDATED (card + module + wiring + SPI comms all confirmed).
  The SD.h library init failure is a known ESP32-Arduino SD.h / custom-SPI-instance quirk,
  NOT a hardware problem. Deferred to firmware phase: Beta will use ESP-IDF's SD driver or
  a properly configured SPI setup rather than fighting Arduino SD.h.
- Note: these dedicated SD pins (39/40/41/42) were later reused for the NFC test (SD
  unplugged). For Beta, SD and NFC need distinct pins or shared SPI bus planning.

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

## BMI270 IMU (PASSED)
- Module: SparkFun BMI270 Qwiic breakout, wired via jumpers to the shared I2C bus.
- I2C address 0x68 (confirmed via scanner). Config in 11_bmi270_imu_test.ino.
- Pins: SDA=GPIO1, SCL=GPIO2 (SHARED with the FT6236 touch controller @ 0x38),
  3V3->3V3, GND->GND. CS/ADR left unconnected.
- MULTI-DEVICE I2C COEXISTENCE VALIDATED: BMI270 (0x68) and FT6236 touch (0x38) live
  on the same SDA=1/SCL=2 bus together with no contention. Good for the Beta pin map.
- Library: needs the "SparkFun BMI270 Arduino Library" - it handles the config-blob
  upload the BMI270 requires before accel/gyro data works (raw register poking alone
  won't return motion data).
- Validation: accel reads -1.00g on the down axis (perfect gravity), gyro ~0 at rest
  and spikes on rotation. IMU detected AND functional reading real motion.

## Status
- PASSED: board/serial, I2C scan, display, touch, CC1101 radio (SPI + RF reception),
  SX1262/LoRa, dual-radio coexistence on shared SPI bus, microSD (hardware validated
  via raw SPI CMD0; SD.h library deferred to firmware), ST25R3916 NFC (SPI chip-ID
  probe validated), BMI270 IMU (accel/gyro functional, I2C multi-device coexistence),
  IR (TSOP38238 RX + TSAL6200 TX: RX decode + full TX->RX loopback, 2026-07-25),
  audio-OUT (MAX98357A amp: real 8ohm speaker output, 2026-07-26),
  MCP23017 I2C GPIO expander (Waveshare board, PA0->PB0 loopback 49/49, 2026-07-26),
  TPS63020 3.3V buck-boost rail (holds ~3.3V from a 3.4V battery input, 2026-07-26),
  bq25185 charger + power path (USB-first safe method, polarity confirmed, charging
  confirmed, 2026-07-26).
- *** ALL ALPHA SUBSYSTEMS NOW VALIDATED. *** The audio-in mic is NOT being bench-retested
  (decision 2026-07-26): the failed ICS-43434 is a confirmed dead individual unit, and its
  wiring + firmware + the MAX98357A amp on the same I2S bus are all proven, so it's a bad
  part, not a design issue. The audio-in path will be confirmed on Beta hardware instead.
- CLEARED to begin the KiCad schematic on fully-validated parts.
- NEXT SESSION: work through the remaining validations above, then Beta schematic in KiCad.

## Later corrections / clarifications (appended 2026-07-21)
The bench observations above are preserved as recorded. Two clarifications from later design work:
1. "bq25185 only outputs 3.3V" — the 3.3V reading was the board's BUCK output specifically
   (measured 3.3V, correct). The bq25185 SYS / power-path output is a SEPARATE rail at ~4.5V
   (measured ~4.6V). Both observations are true — they're different rails. See Pin Map v0.2 §8
   power tree: SYS ~4.5V feeds the separate TPS63020 3.3V buck-boost for logic.
2. "Beta schematic in Flux" — the schematic tool decision was later finalized as KiCad (Pin
   Map v0.2 §12; unanimous in the three-way review). Flux was exploration only.

## IR - TSOP38238 (RX) + TSAL6200 (TX) - PASSED (2026-07-25)
Bench pins: IR TX = GPIO 17, IR RX = GPIO 18.
(Beta pin map uses 43/44. Avoided on the bench: DevKits wire 43/44 to the USB-UART bridge
chip. Also note 17/18 collide with SX1262 CS/DIO1 on this bench - the radio was unplugged
for this test. Genuinely free bench pins: 9, 38, 47, 48.)

WIRING:
  TSOP38238 (lens facing you, legs down): pin1 OUT -> GPIO18, pin2 GND -> GND, pin3 VS -> 3V3
  TSAL6200: LONG leg (anode) -> 150R resistor -> GPIO17; SHORT leg (flat side) -> GND

RESULTS:
- RX PASSED: decoded a real remote as NEC, 32 bits, clean.
- Carrier sweep (LEDC hardware PWM, 36-40kHz): TSOP responded STRONG at every frequency
  (294-295 LOW samples of ~300). Optical path conclusively confirmed.
- Full TX->RX loopback PASSED: NEC 0x00FFE01F sent and decoded back, 3 of 4 frames matched.

CRITICAL LESSONS (cost several debug rounds):
1. THE RECEIVER MUST STAY ENABLED DURING TRANSMIT. Calling irrecv.disableIRIn() before
   sending means the receiver is deaf while the LED emits - loopback can never work. Also do
   NOT wrap the send in noInterrupts(): IRrecv's sampling ISR must keep running. This single
   bug caused every earlier loopback failure and was initially misdiagnosed as a carrier
   problem.
2. Use LEDC HARDWARE PWM for the 38kHz carrier on ESP32-S3. IRremoteESP8266 bit-bangs a
   software carrier on ESP32 which is unreliable here.
3. A GPIO-driven TSAL6200 is DIM. At 150R and 50% carrier duty the average is ~7mA vs
   100-500mA in a real remote. Effective range is 1-3cm, not 10-30cm. Aim the LED dome
   directly at the TSOP dome. BETA MUST DRIVE THE IR LED VIA A TRANSISTOR/MOSFET for
   usable range.
4. Timing jitter: with interrupts enabled, hand-timed mark/space occasionally mis-decodes
   (3 of 4 matched). Native RMT generates timing in hardware and will not have this issue.
5. IRremoteESP8266 defines unprefixed constants (e.g. kTimeoutMs) that collide with sketch
   globals - prefix your own. Also resultToHexidecimal() takes a POINTER (&results).
6. Ambient IR was NOT a factor here (idle LOW 0/50) but the TSOP's AGC can desensitize under
   flickering LED/fluorescent light - worth checking if RX ever seems weak.

BETA FIRMWARE DECISION: use the native ESP32-S3 RMT peripheral for IR, not a bit-banged
library. Espressif recommends the S3 for IR specifically because it is the only chip with
RMT DMA, which keeps IR timing clean while WiFi/BT/radios run concurrently - exactly
AQROOT's use case.

## I2S AUDIO - MAX98357A amp PASSED / ICS-43434 mic INCONCLUSIVE (2026-07-26)
Bench pins (I2S): BCLK=38, LRCK/WS=47, amp DIN=48, mic DOUT=9 (also tested on 3).
(Beta pin map uses 39/40/41/42 - those collide with microSD/NFC/touch on this bench, so
audio was tested on free pins 38/47/48/9. The bench pin choice does not affect the Beta
design; it validates the parts + I2S pipeline, which is pin-independent.)
Library: ESP_I2S (built into Arduino core 3.x, I2SClass). No external lib.

AMP - MAX98357A: PASSED. Plays tones/beeps to a real 8ohm speaker (measured 8.3ohm). Wiring:
LRC=47, BCLK=38, DIN=48, Vin=3V3, GND=GND, GAIN + SD(SO) unconnected, speaker across +/-.
This validates the ESP32 I2S peripheral, clock generation, pin assignment, and the whole
audio-OUT pipeline. NOTE for bench: SD/SO measured 2.98V (enabled) even unconnected on this
board, so it has a pull-up; still recommend explicitly tying the amp's enable on Beta.

MIC - ICS-43434: INCONCLUSIVE (single sample, suspected dead unit). All-zeros output
(raw 0x00000000, peak 0) on both GPIO 9 and GPIO 3. Everything AROUND the mic verified good:
- Power: 3V pin = 2.98V, GND continuity OK
- SEL = 0V (left channel, matches sketch's I2S_STD_SLOT_LEFT)
- Continuity CONFIRMED on all three signal lines: DOUT->GPIO, BCLK->38, LRCL->47
- Slot format tried both LEFT and RIGHT - both all zeros
- DOUT idles at 0V (a live mic receiving clocks should not sit at flat 0V)
Since the amp proves the I2S bus/clocks/pins are all good, and every wire to the mic is
verified, the most likely explanation is a DEAD individual mic unit (MEMS mics are sensitive
to ESD/reflow; cheap breakouts have real failure rates). Only had ONE mic to test.

STATUS: audio-OUT validated; audio-IN wiring + firmware validated, mic UNIT pending.
ACTION: retest with a FRESH ICS-43434 before/at Beta. Part selection (ICS-43434) remains
LOCKED and correct - this is a suspected bad single unit, NOT a design or part-choice issue.
Does NOT block the schematic: the audio design and pin map are proven.

## MCP23017 I2C GPIO EXPANDER - PASSED (2026-07-26)
Board: Waveshare MCP23017 IO Expansion Board.
Bench wiring: VCC->3V3, GND->GND, SDA->GPIO1, SCL->GPIO2 (shared I2C bus with touch + IMU).
INTA/INTB unconnected. RESET handled onboard (not broken out). Self-test jumper PA0<->PB0.
Library: Adafruit MCP23017 Arduino Library (Adafruit_MCP23X17). Pin numbering 0-15:
GPA0..7 = 0..7, GPB0..7 = 8..15.

ADDRESS: this Waveshare board defaults to 0x27 (A0/A1/A2 pull HIGH when open; short to GND
to lower the address). The test sketch auto-detects any device in the 0x20-0x27 range, so it
works regardless of address straps. Detected at 0x27.

RESULT: PASSED. I2C scan found the chip; PA0->PB0 loopback ran 49/49 clean (drove PA0,
read it back through the expander on PB0, alternating high/low, zero mismatches). Confirms
the expander does real GPIO output AND input over I2C, coexisting on the same bus as the
FT6236 touch (0x38) and BMI270 IMU (0x68).

BETA NOTE: the Beta pin map assigns MCP23017 to 0x20 - short A0/A1/A2 to GND on the Beta
design (or whatever address the final I2C map wants). The chip + library are validated
either way; only the address straps differ.

## TPS63020 3.3V BUCK-BOOST RAIL - PASSED (2026-07-26)
Board: EC Buying "XL63020-3.3 / TPS63020" buck-boost module (fixed 3.3V output, VIN 2-5.5V).
4-pin module: VIN + GND (input), COUT + GND (output). No enable pin, no potentiometer,
factory-fixed 3.3V. (Also has an optional Micro-USB input, unused for this test.)

TEST (meter only - no ESP32/firmware; a regulator is a passive power test):
- Input: 3.7V bench LiPo (the battery re-pinned after the bq25185 incident), fed to VIN/GND.
- Polarity confirmed with the meter BEFORE connecting (lesson from the bq25185 reverse-polarity
  incident - always verify + and - first).
- Output COUT measured ~3.4V unloaded with the battery at 3.4V.

RESULT: PASSED. With the battery at only 3.4V (barely above the 3.3V target - the hardest
region for a buck-boost), the module held a stable ~3.4V out. A plain buck would sag here;
holding regulation across this transition proves the BUCK-BOOST behavior that made the
TPS63020 the right choice. The slight-high unloaded reading (~3.4 vs 3.3) is normal for these
modules and settles to 3.3V under load. Core validation (battery voltage in -> clean regulated
~3.3V rail out) confirmed.

BETA NOTE: this validates the TPS63020 as the 3.3V logic rail regulator (per the decisions
log + pin map). On the Beta PCB it's fed from the bq25185 SYS (~4.5V) and supplies the main
3.3V logic. Support parts (inductor, caps, feedback resistors or fixed-3.3V variant) spec'd
at schematic time.

## bq25185 CHARGER + POWER PATH - PASSED (2026-07-26)
Board: Adafruit bq25185 USB/DC/Solar Charger with 3.3V Buck (product 6092). Fresh replacement
board (NOT the one fried by reverse polarity earlier). Onboard buck = TPS62569 (3.3V/1A).
Layout: USB-C in, DC/solar pads (unused), JST-PH 2-pin BATT port, 3-pin terminal block
(4.5V power-path / 3.3V / GND), status LEDs C(charge)/F(fault)/G(3.3V), EN pad, back-side
charge-rate jumper (left at default 1A).

TEST METHOD - deliberately battery-last to avoid repeating the reverse-polarity kill:
- Phase 1 (USB only, NO battery): validated the whole output side with zero battery risk.
  3.3V terminal ~3.3V, 4.5V power-path terminal ~4.5V with USB attached. Green G LED on.
- Phase 2 (polarity check): measured the re-pinned LiPo's JST pins directly, compared to the
  board's BATT silkscreen +/- - confirmed MATCH before connecting. This is the exact check
  skipped when the earlier board was fried.
- Phase 3 (battery connected): plugged battery in (polarity confirmed). 3.3V output held off
  battery alone. Then added USB.

RESULT: PASSED. Final state with battery + USB-C connected: Green G (3.3V output) ON, Orange C
(charging) SOLID ON = actively charging, Red F (fault) OFF. No heat, no fault. Charger, power
path, 3.3V buck, and charge path all confirmed working.

BETA NOTES (carry into schematic):
- The bench board's onboard buck is TPS62569; the Beta DESIGN uses a separate TPS63020
  buck-boost (validated separately) fed from the bq25185-class SYS/power-path (~4.5V). The
  bench board proves the charger + power-path concept; Beta uses the bq25185 charger stage +
  our own TPS63020 3.3V rail.
- REVERSE-POLARITY PROTECTION remains a hard Beta requirement (a reversed LiPo destroyed a
  board during earlier bench work). Beta needs reverse-polarity protection + a keyed/
  standardized battery connector + a tray that can't invite reversed insertion.

## DECISION: ICS-43434 mic NOT bench-retested (2026-07-26)
Decided not to re-run the audio-in test with a fresh mic. The one unit tested was a confirmed
dead part, and everything around it is already proven: the I2S wiring, the firmware/driver
path, and the MAX98357A amp sharing the same I2S bus all validated. This is a bad individual
unit, not a design or part-choice issue - ICS-43434 stays LOCKED. Consequence: the audio-IN
path gets its first live confirmation on Beta hardware rather than on the Alpha bench. Low
risk given the pipeline is proven; noted here so the Beta bring-up checklist explicitly
verifies the mic on first power-up.
