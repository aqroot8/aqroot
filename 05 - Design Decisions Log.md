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
> UPDATED: superseded by the 'Display: ILI9341 SPI for Beta, AMOLED as stretch goal'
> decision below. The 2.13 AMOLED is now a Kickstarter stretch goal, not the baseline
> Beta display.

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
- Display driver: **LovyanGFX** with a **generic ILI9341 SPI config as the actual Beta
  display driver (ILI9341 is now the baseline part; AMOLED/RM69090 is a stretch-goal board
  revision)**. The UI is written resolution-independently, so swapping in the AMOLED later
  is a driver-only change. The same ILI9341 config doubles as the Wokwi simulation panel.
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
> UPDATED: superseded by the 'Display: ILI9341 SPI for Beta, AMOLED as stretch goal'
> decision below. The 2.13 AMOLED is now a Kickstarter stretch goal, not the baseline
> Beta display.
- Prototype budget ceiling: not yet set — see Kickstarter and Review Strategy note.
- Final enclosure shape: refined slab vs PCB-as-badge vs current rendered concept.

## Display: ILI9341 SPI for Beta, AMOLED as stretch goal
Decided to ship Beta on the Alpha-validated ILI9341 2.4-2.8in IPS cap-touch (standard SPI,
FT6236 touch @ 0x38). AMOLED dropped to a Kickstarter stretch goal ('premium AMOLED
upgrade' - a board revision funded if the campaign hits ~$1M, NOT a drop-in swap since
AMOLED is QSPI). Rationale: removes the biggest technical risk (QSPI AMOLED bring-up),
saves ~$25/unit, uses proven parts, and turns a cost into a marketing asset. The dual
radios (not the screen) are the real differentiator.

## 3.3V rail regulator: TI TPS63020 buck-boost
Selected the Texas Instruments TPS63020 as the main 3.3V logic-rail regulator, fed from the
bq25185 charger's SYS output (~3.0-4.5V, battery-tracking). Rationale:
- Buck-boost (required): holds a steady 3.3V whether the LiPo is above 3.3V (full, ~4.2V) or
  below it (near-empty, ~3.0V). A plain buck would brown out with charge still in the battery.
- Capacity: delivers up to 2A continuous at 3.3V (4A switch limit) - ~2x headroom over the
  estimated worst-case continuous draw (~1A), so it's never run at its limit.
- Efficiency up to 96%, most efficient when Vin is near Vout (our ~3.7V->3.3V case) = max
  battery runtime + low heat in a sealed enclosure.
- Low quiescent current (~25uA in power-save) = minimal idle battery drain.
- Input range 1.8-5.5V; can discharge the LiPo below 2V for maximum runtime.
- Has EN (enable) and PS/SYNC (power-save select) pins - useful for firmware power control.
- Proven, well-documented TI part with reference designs + WEBENCH; good for open-hardware.
Support components (spec exactly at schematic time from TI datasheet): 1-1.5uH inductor,
2x10uF input caps, 3x22uF output caps, and (for adjustable variant) R1=180k/R3=1M to set
3.3V - OR use a fixed-3.3V sibling (e.g. TPS630250) to drop the setpoint resistors.
Prototyping: cheap TPS63020 3.3V breakout modules exist (~$10 on Amazon) for future
bench validation of the power tree.

## RF/antenna architecture + coexistence
Per-radio antenna architecture (see 12 - RF and Antenna Plan v0.1): WiFi = ESP32 module
onboard antenna (keep-out only, easiest); NFC = rear PCB/flex loop, no metal behind;
LoRa 915 = internal FPC on upper sidewall; Sub-GHz 433 = electrically-shortened antenna
in RF crown (hardest, range compromise). COEXISTENCE: only ONE radio transmits at a time
(firmware-enforced) + individual radio power-gating for battery life; multiple radios may
RX at once. Implies a 4-layer PCB for a clean ground plane. Final antenna tuning + exact
sizes are a POST-PCB step (measured on real hardware); professional RF review required
before PCB fab.

## 433 MHz antenna: external screw-on + integrated side-holder
Default: internal compromised 433 antenna (modest range, fully pocketable). Max range:
a screw-on external high-gain whip via a U.FL/SMA connector (Flipper-style). Stowage: an
integrated holder/channel on the SIDE of the device holds the external antenna when not
in use (never lost, distinctive design feature). Target antenna size ~8-14cm class; EXACT
size decided POST-PCB by measuring candidate antennas on real hardware. Cert caveat: a
user-swappable antenna may launch as an advanced accessory pending FCC review. Keep
magnets away from the NFC coil if a magnetic retention is considered.

## Power incident + reverse-polarity Beta requirement
During bench testing, a reverse-wired LiPo JST connector destroyed a bq25185 charger board
(isolated damage; battery unharmed; no validated work affected). Battery connector was
re-pinned and verified at +3.7V correct polarity. LESSON -> Beta MUST include
reverse-polarity protection at the battery input + a standardized/keyed battery connector
polarity + a battery tray that doesn't invite reversed insertion. Also validated: bq25185
board 3.3V buck output = 3.3V, power-path out = 4.6V (both measured correct before the
incident).

## Audio parts: ICS-43434 mic + MAX98357A amp
Selected the I2S audio parts (were "planned, unspecified"):
- Speaker amp: MAX98357A - I2S Class-D mono amp, all-in-one (I2S in -> amplified speaker out,
  no separate DAC). Up to 3.2W into 4ohm (far more than needed; run below max). 2.7-5.5V,
  efficient Class-D. Has a SHUTDOWN/mode pin -> power-gate the amp when audio idle (goes on
  the MCP23017 expander as a slow enable). Gain pin-settable (3-15dB). No I2C config needed.
- Microphone: ICS-43434 - I2S MEMS mic. IMPORTANT: chosen over the popular INMP441 because
  the INMP441 is DISCONTINUED / not recommended for new designs. The ICS-43434 is the
  current-gen InvenSense replacement (drop-in, better power + audio). Picking the
  in-production part now avoids a production sourcing surprise.
- Speaker: small 4ohm or 8ohm, ~1-2W; exact speaker chosen at enclosure CAD time (size +
  acoustic mounting depend on the shell).
- Shares the reserved I2S pins (BCLK=39, LRCLK=40, DOUT=41 speaker, DIN=42 mic).
- STILL NEEDS BENCH VALIDATION (audio is the one untested subsystem). Buy ICS-43434 +
  MAX98357A breakouts (~$5-8 each) to validate on the Alpha board when ready.
- Expander addition: MAX98357A SD/shutdown (+ optional gain) pin(s) on the MCP23017.

## Display module: 2.8" IPS ILI9341 capacitive SPI (verify touch = FT6236 @ 0x38)
Beta display = 2.8" IPS, ILI9341 driver, 240x320, 4-wire SPI, CAPACITIVE touch - matches the
Alpha-validated config (same driver, same LovyanGFX setup, real backlight pin confirms BL on
GPIO47). VERIFICATION REQUIRED before ordering Beta qty: confirm the exact module's touch
controller is FT6236-family at I2C 0x38 (matches Alpha code). CAUTION: many cheap ILI9341
touch modules use RESISTIVE touch (XPT2046, SPI) or a DIFFERENT capacitive chip (FT6336/GT911,
possibly different address) - must source a capacitive FT6236 @ 0x38 module, or accept a
documented alternative + adjust the touch driver. Reference modules: Elecrow / LCDwiki-class
2.8" IPS ILI9341 capacitive SPI.

## Alpha validation parts - ordered (2026-07-20)
Ordered the remaining breakouts to finish Alpha validation of the last untested subsystems:
- ICS-43434 I2S mic (audio input)
- MAX98357A I2S amp (audio output) + small 4/8ohm speaker
- MCP23017 I2C GPIO expander (0x20) - designed into Beta, not yet bench-tested
- TPS63020 buck-boost breakout (3.3V output) - validate the main 3.3V logic rail before PCB
Deferred (not needed yet): MAX17048 fuel gauge (battery-% monitoring is a convenience
feature, low-risk to validate later on the Beta board).

Already arriving separately:
- IR: Bridgold TSOP38238 (RX) + TSAL6200 (TX 940nm) - arrives ~2026-07-21
- Power: 2x bq25185 charger boards (replacements after the reverse-polarity incident) - few days

## Alpha validation status (remaining)
Once all parts arrive, the remaining Alpha validations are:
- IR (TSOP38238 + TSAL6200) on native RMT pins 43/44, 38kHz carrier - NEXT (parts tomorrow)
- Audio (ICS-43434 + MAX98357A + speaker) on I2S pins 39/40/41/42 - needs a test sketch
- MCP23017 expander on I2C - verify GPIO in/out + interrupt
- TPS63020 3.3V rail - bench-test clean 3.3V under load
- Power charging path (bq25185) - measure outputs, confirm polarity, test charging (few days)
After these, Alpha is complete for all subsystems -> ready to start the KiCad schematic on
fully-validated parts.
