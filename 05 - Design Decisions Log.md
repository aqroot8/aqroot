---
tags: [decisions, log]
---

# Design Decisions Log

## Naming
- Project renamed from working title "Handheld Hacker Multi-Tool" to **AQROOT**
  (Access + Query the Root Layer).

## Form factor
- Rejected: folding clamshell design (original concept).
- Rejected: 10 "sci-fi concept art" enclosure ideas — too stylized/unrealistic to route or
  print.
- Considered: 10 realistic form factors (Flipper-style slab, M5Stack-style stacked box,
  Altoids tin cyberdeck, credit-card slim, off-the-shelf project box, Cardputer-style with
  keyboard, round wrist unit, handheld-radio with whip antenna, PCB-as-badge chassis,
  refined screwed slab).
- Current: first concept render saved (see Assets), rugged single-shell design with visible
  GPIO breakouts, D-pad, and confirm/home/back buttons.
- Manufacturing (v1 prototype): FDM 3D printing on existing Kobra S1 printer.
- Target dimensions: ~75x45x16mm, matching Kode Dot's pocket-tool scale.
- NFC read window: back face of the device.

## Display
- Considered: Hosyond 3.5" 320x480 IPS capacitive touch (ST7796U + FT6336U touch, same
  touch controller already used on the MistWake project). Rejected — 55.5x98mm module
  alone is bigger than the entire target device, would force a PDA-sized shell.
- Decision: keep 2.13" AMOLED touch (502x410) to preserve pocket scale. Sourcing this part
  is a genuinely open item — no mainstream hobbyist breakout was found during research;
  likely needs direct sourcing from a display manufacturer/distributor. Flagged as a task
  in the Build TODO Tracker.

## Radio
- Considered: CC1101 (sub-GHz only), either core or add-on.
- Decision: replaced with SX1262 — one chip covers both LoRa (mesh networking via
  Meshtastic-compatible firmware) and raw sub-GHz FSK/OOK/ASK capture/replay.
- Sourcing decision: use a certified breakout module (e.g. Ebyte E22 series) PERMANENTLY,
  even in the final design — not bare IC. Reasoning: multi-band RF matching (roughly
  150-960MHz across sub-bands) is high engineering risk, and certified modules carry
  FCC/CE pre-certification that matters the moment units leave your hands (reviewers,
  Kickstarter backers). Note: modifying a certified module's RF section (antenna, output
  power) can void that certification — check the module's certification conditions before
  shipping units externally.
- **Alpha update (July 2026):** the Alpha bench prototype wires BOTH a CC1101 and an
  SX1262 on a shared SPI bus (see [[09 - Alpha Pin Bus Map]]), with a firmware radio
  manager guaranteeing only one radio transmits at a time. This supersedes the
  "replaced with SX1262" line above for the Alpha build; whether both chips ship in the
  final design is still open.

## Core vs add-on philosophy
- Original plan pulled CC1101 out to add-on status for regional/antenna flexibility.
- Reversed after deciding to compete more directly on features: NFC, radio (LoRa+sub-GHz),
  IR, IMU, mic/speaker, and Wi-Fi/BT all moved to core. Only genuinely optional items stay
  as add-ons: external high-gain antenna, GPIO/debug breakout, external battery pack, back
  covers.

## Compute and NFC sourcing
- ESP32-S3: bare module (WROOM-1) on custom PCB for final design. Prototype first on a
  DevKitC-1 devkit to decouple firmware bring-up from PCB bring-up.
- PN532: bare IC + tuned antenna matching network for final design. Prototype first on a
  proven breakout board (Elechouse/Adafruit-style) to validate firmware before taking on
  the antenna-matching design risk.
- **Alpha update (July 2026):** the Alpha bench prototype instead uses an ST25R3916
  (X-NUCLEO-NFC06A1 eval board) on its own SPI bus — see [[09 - Alpha Pin Bus Map]].
  This differs from the PN532 plan above AND from the current firmware NFC driver
  (Adafruit_PN532 over I2C); reconcile the driver before NFC bring-up.

## Sensors
- IMU: 6-axis (accel + gyro, e.g. BMI270) instead of true 9-axis. No magnetometer —
  nothing in the feature set uses compass heading, and magnetometers need calibration and
  are sensitive to nearby metal/radios (of which this device has several).
- Mic/speaker: I2S digital, not analog — simpler ESP32-S3 interfacing.

## Power
- Battery: 1000mAh (top of the original 800-1000mAh range), given combined draw from
  AMOLED + Wi-Fi/BT + LoRa/sub-GHz radio.
- Charging: load-sharing IC required for final design (usable while charging) — a simple
  non-load-sharing TP4056-style module is fine for the dev-board prototype stage only.
- Target runtime: ~8 hours active use.
- External battery add-on: pogo-pin dock connector (Kode Dot style).

## PCB and manufacturing
- Fab house: JLCPCB.
- Layer count: 4-layer — dedicated ground plane matters for RF cleanliness given
  SX1262 + Wi-Fi/BT coexisting on one small board.
- Assembly: JLCPCB assembly service for SMD parts (ESP32-S3 module, PN532 IC, SX1262
  module footprint, passives). Hand-solder headers/connectors/battery wiring yourself.

## Firmware
- LVGL 8.3.x (stable), not 9.x, to avoid breaking API changes and thinner example coverage.
- App packaging v1: simple flashable .bin menu, not a full manifest/icon launcher (that's
  later-stage scope).
- Radio driver: built on RadioLib rather than from-scratch register-level SX1262 code.
- Version control: git repo initialized as part of initial project setup. Now pushed to a
  public GitHub repo at https://github.com/aqroot8/aqroot (account aqroot8).

### First implementation pass (full driver + UI stack)
- Framework: switched the driver/app layer from ESP-IDF to the **Arduino core for
  ESP32-S3**. Reason: mature drop-in libraries (LVGL, LovyanGFX, RadioLib, Adafruit PN532,
  I2S) instead of hand-rolled register code. FreeRTOS/ESP-IDF still run underneath — the
  Arduino core sits on top of ESP-IDF, so nothing in the layered architecture is lost.
- PlatformIO platform pinned to **espressif32@6.9.0** (Arduino 2.0.x / IDF 4.4). The 7.x
  line (Arduino 3.x / IDF 5.x) removed the legacy `driver/i2s.h` API the audio driver uses.
  Treat this as a deliberate bump-when-ready pin, not an accident.
- Display driver: **LovyanGFX** with a **generic ILI9341 SPI config as a deliberate
  placeholder** for the RM69090 AMOLED (still unsourced — see Open items). The UI is
  written resolution-independently, so swapping in the AMOLED is a driver-only change. The
  same ILI9341 config doubles as the Wokwi simulation panel.
- IMU driver: implemented as a **generic MPU-style I2C read with no external dependency**,
  rather than committing to a BMI270 library now. The exact part (BMI270 vs ICM-42670) is
  not locked, and a non-resolvable library dependency would break the build. Add the
  part-specific library and register map once the IMU is chosen.
- IR: deferred. The Infrared tile is a working UI shell only; a real RMT-based IR TX/RX
  driver is a follow-up (there is no `drivers/ir.*` yet).
- Simulation: added a **Wokwi target** gated by a `SIMULATION_MODE` compile flag. In that
  build, radio/NFC/audio return realistic mock data and four physical buttons stand in for
  the CST816 touchscreen (Wokwi has no CST816 model), so the entire UI is testable with no
  hardware. Both build environments (`esp32-s3-aqroot`, `wokwi`) are verified compiling.

## Licensing
- Firmware: MIT license.
- Hardware: CERN-OHL-S v2.
- Matches the license combination used by comparable open-source hardware projects
  (including Kode Dot).

## Open items to revisit
- 2.13" AMOLED touch module: needs real sourcing research (manufacturer/distributor,
  MOQ, single-unit availability).
- Prototype budget ceiling: not yet set — see Kickstarter and Review Strategy note.
- Final enclosure shape: refined slab vs PCB-as-badge vs current rendered concept.

## Display: ILI9341 SPI for Beta, AMOLED as stretch goal
Decided to ship Beta on the Alpha-validated ILI9341 2.4-2.8in IPS cap-touch (standard SPI,
FT6236 touch @ 0x38). AMOLED dropped to a Kickstarter stretch goal ('premium AMOLED
upgrade' - a board revision funded if the campaign hits ~$1M, NOT a drop-in swap since
AMOLED is QSPI). Rationale: removes the biggest technical risk (QSPI AMOLED bring-up),
saves ~$25/unit, uses proven parts, and turns a cost into a marketing asset. The dual
radios (not the screen) are the real differentiator.
