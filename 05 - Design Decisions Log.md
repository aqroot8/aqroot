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
- Version control: git repo initialized as part of initial project setup.

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
