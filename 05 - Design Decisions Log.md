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
> UPDATED: superseded by Field Slate v3 enclosure ~122x61x23.5mm — see
> [[15 - Enclosure Field Slate v3]]. Note the original "pocket-tool, not PDA-sized"
> rationale (used to reject the 3.5in Hosyond display) no longer holds on size grounds;
> the ILI9341 decision still stands on cost + QSPI-risk grounds instead.
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
> UPDATED: superseded by the 'Radio: DUAL-RADIO LOCKED' decision below. AQROOT is NOT a
> one-chip radio design — it ships BOTH CC1101 and SX1262 as core built-in hardware.
- Sourcing decision: use a certified breakout module (e.g. Ebyte E22 series) PERMANENTLY,
  even in the final design — not bare IC. Reasoning: multi-band RF matching (roughly
  150-960MHz across sub-bands) is high engineering risk, and certified modules carry
  FCC/CE pre-certification that matters the moment units leave your hands (reviewers,
  Kickstarter backers). Note: modifying a certified module's RF section (antenna, output
  power) can void that certification — check the module's certification conditions before
  shipping units externally.
## Radio: DUAL-RADIO LOCKED (CC1101 + SX1262) — production, not just Alpha
AQROOT ships BOTH CC1101 (sub-GHz OOK/ASK/FSK capture/replay) AND SX1262 (LoRa +
sub-GHz) as core built-in hardware. Validated together in Alpha (shared SPI Bus B,
CS-discipline). This dual-radio built-in base IS the core competitive wedge (what Kode Dot
sells as paid add-ons). Beta pin map v0.2 §3 commits permanent pins to both. NOT optional,
NOT add-on, NOT Alpha-only.
- Alpha validation: both chips init on one shared SPI bus in a single program with CS
  discipline — see [[09 - Alpha Pin Bus Map]] and [[Alpha-Tests/HARDWARE-NOTES]].
- Coexistence rule: firmware radio manager guarantees only ONE radio transmits at a time
  (multiple may RX). See the RF/antenna architecture decision below.
- FIRMWARE ACTION REQUIRED: there is no CC1101 driver yet — the firmware is SX1262-only.
  A CC1101 driver plus a radio manager spanning both chips is outstanding work.

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
> UPDATED: superseded by the 'NFC part: ST25R3916 (LOCKED)' decision below. The PN532 plan
> is dead — wrong chip AND wrong bus (PN532 assumed I2C; ST25R3916 is SPI).

## NFC part: ST25R3916 (LOCKED, supersedes PN532)
NFC front-end is the ST25R3916 (X-NUCLEO-NFC06A1 in Alpha), validated over SPI (raw IC-ID
reg 0x3F = 0x2A confirmed, IC-type field 0x05). Supersedes the earlier PN532 plan entirely.
Interface is SPI (NOT I2C as the old PN532 firmware assumes). Needs BOTH 3V3 and a 5V PA
rail for full RF TX. FIRMWARE ACTION REQUIRED: the current firmware NFC driver + Adafruit
PN532 library dependency are for the wrong chip/bus and must be replaced with an ST25R3916
SPI driver (Alpha raw-SPI validation is the foundation). BOM must swap PN532 -> ST25R3916.
- Power detail: boost ONLY the analog/PA rail to 5V; keep VDD_IO at 3.3V so the shared SPI
  bus needs no level shifter. See [[11 - Beta Pin Map v0.2]] §3 and §8.
- Beta places NFC as a THIRD device on shared SPI Bus B (CS on GPIO9, IRQ on GPIO38) — a
  config not proven in Alpha (Alpha ran NFC on its own pins); validate on Beta.
- Antenna: rear PCB/flex loop with matching network — see [[12 - RF and Antenna Plan v0.1]].

## Sensors
- IMU: 6-axis (accel + gyro, e.g. BMI270) instead of true 9-axis. No magnetometer —
  nothing in the feature set uses compass heading, and magnetometers need calibration and
  are sensitive to nearby metal/radios (of which this device has several).
- Mic/speaker: I2S digital, not analog — simpler ESP32-S3 interfacing.

## Power
- Battery: 1000mAh (top of the original 800-1000mAh range), given combined draw from
  AMOLED + Wi-Fi/BT + LoRa/sub-GHz radio.
> UPDATED: superseded by 2000mAh / ~12-15hr active — see
> [[13 - Power Budget and Battery Runtime v0.1]]. 2500-3000mAh is an open option if the
> Field Slate v3 enclosure volume allows.
- Charging: load-sharing IC required for final design (usable while charging) — a simple
  non-load-sharing TP4056-style module is fine for the dev-board prototype stage only.
- Target runtime: ~8 hours active use.
> UPDATED: superseded by ~12-15hr active / ~2wk standby at 2000mAh — see
> [[13 - Power Budget and Battery Runtime v0.1]].
- External battery add-on: pogo-pin dock connector (Kode Dot style).

## PCB and manufacturing
- Fab house: JLCPCB.
- Layer count: 4-layer — dedicated ground plane matters for RF cleanliness given
  SX1262 + Wi-Fi/BT coexisting on one small board.
- Assembly: JLCPCB assembly service for SMD parts (ESP32-S3 module, ST25R3916, CC1101 +
  SX1262 module footprints, passives). Hand-solder headers/connectors/battery wiring
  yourself.

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
2x10uF input caps, 3x22uF output caps, and R1=180k/R3=1M to set 3.3V.
Prototyping: cheap TPS63020 3.3V breakout modules exist (~$10 on Amazon) for future
bench validation of the power tree.
> CORRECTED (2026-07-26, pre-schematic design review): the TPS63020 **IS** the
> adjustable-output part - there is no "fixed vs adjustable" choice to make, and the earlier
> "OR use a fixed-3.3V sibling (e.g. TPS630250)" framing has been dropped as a false
> alternative. Orderable P/N locked: **TPS63020DSJR** (reel). It is **not considered
> "selected" until its inductor, feedback resistors, and input/output caps are selected with
> it** - a buck-boost is a compensated loop, not a drop-in symbol. Spec all support components
> from the TI datasheet at schematic time, and **account for ceramic capacitor DC-bias
> derating** (a nominal 22uF X5R/X7R can lose 30-60% of its capacitance at the operating
> voltage - size by effective capacitance, not the printed value).

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

> UPDATE (2026-07-24): ALL Alpha validation parts now RECEIVED. Nothing left on order:
> - ICS-43434 mic
> - MAX98357A amp
> - speaker
> - MCP23017 expander
> - TPS63020 3.3V breakout
> - IR (Bridgold TSOP38238 RX + TSAL6200 TX)
> - 2x bq25185 replacement charger boards
> All parts in hand -> the 5 remaining bench validations below have no shipping blockers.

## Alpha validation status (remaining)
All parts now present (received 2026-07-24) - no shipping blockers. The remaining bench
validations are:
- [ ] IR: TSOP38238 (RX) + TSAL6200 (TX) on native RMT pins 43/44, 38kHz carrier
- [ ] Audio: ICS-43434 + MAX98357A + speaker on I2S 39/40/41/42 (check mic L/R strap)
- [ ] MCP23017 expander on I2C 0x20 (verify GPIO in/out + interrupt)
- [ ] TPS63020: clean 3.3V under load
- [ ] Power charging path (bq25185): MEASURE board outputs + CONFIRM battery polarity vs
      board markings BEFORE connecting (this board was fried by reversed polarity before) ->
      then test charging
After these 5 pass, Alpha is COMPLETE -> clear to start the KiCad schematic on fully-
validated parts.

## PRE-SCHEMATIC DESIGN REVIEW — corrections + decisions (2026-07-26)

Applied immediately before KiCad schematic capture. Source: pre-schematic design review.
Full detail in [[11 - Beta Pin Map v0.2]] (now revision v0.2.1).

**Factual errors corrected:**
1. **MCP23017 pin count.** The repo claimed the MCP23017 has "14 bidirectional + 2 output-only
   pins (GPA7, GPB7)". That is WRONG - the MCP23017 has **16 FULLY BIDIRECTIONAL GPIO** (all
   of GPA0-7 and GPB0-7, direction set per-pin via IODIRA/IODIRB). There is no output-only pin
   on this part. All "output-only" notes removed and every pin budget that relied on the wrong
   number recalculated - including the "~7 slow GPIO" community-header figure, which was
   downstream of the error.
2. **GPIO43/44 UART labels.** Corrected to **GPIO43 = U0TXD, GPIO44 = U0RXD** (reversed in
   v0.2 §5).

**Design changes adopted:**
3. **IR TX moved GPIO43 -> GPIO16** (IR RX stays on GPIO44). GPIO43 is U0TXD and the ROM
   bootloader drives the boot log out of it on every reset - that would pulse the IR LED
   MOSFET driver at 100-500mA on every boot. **A gate pull-down does NOT fix this**: a
   pull-down cannot override an actively-driven push-pull UART output. GPIO16 has no boot-log
   traffic and RMT is not pin-locked (it routes through the GPIO matrix). IR TX driver stage
   specified: low-side MOSFET, gate series resistor 33-220R, gate pull-down 47-100k (float
   protection during reset/power sequencing only), LED current-limit resistor, local
   decoupling, physical TX/RX separation.
4. **GPIO21 reclaimed.** Display RESET and touch RESET both moved off native GPIO21 onto the
   MCP23017 (reset is a slow signal; the doc already inconsistently had touch RESET on GPA0).
   Two separate expander pins, not one shared, for sequencing flexibility. The FT6236 still
   requires a CTP_RST low->high pulse to enumerate - that pulse now comes from the expander,
   so the boot order is: I2C up -> configure expander -> pulse touch RST -> init touch.
5. **GPIO3 / BMI270 INT1 strap caution.** SX1262 RESET stays on MCP23017 GPA1; BMI270 INT1
   stays native on GPIO3. Because GPIO3 is a strapping pin and the IMU can assert INT1 during
   the reset window, the boot state must be designed: configure INT1 open-drain if the mode
   allows, add a weak pull setting the correct strap level, add a 100-470R series resistor,
   add a test pad, and **validate 50-100 cold boots with motion applied during reset** before
   freezing. Fallback if it fails: drop native motion-wake, poll the IMU, free GPIO3.
6. **Second MCP23017 at 0x21** for the community expansion header (16 low-speed GPIO,
   XGPIO0..15). The internal expander (0x20) now carries the 8-button cluster (D-pad + A/B +
   Back + Home on Port B) plus all internal control signals on Port A - **exactly 16 pins,
   completely full**. The Port A / Port B split is deliberate: it makes INTB a pure button
   interrupt. Casualty: the old "display power/control reserve" pin is gone, and no D-pad
   centre/select fits.
   - **BUTTON WAKE:** a polled expander CANNOT wake the ESP32 from sleep. The 0x20 INTB output
     is routed (open-drain, wired-OR with 0x21) to a native wake-capable pin so buttons can
     wake the device. Without this the ~2-week standby figure is unreachable.
   - **PHYSICAL POWER SWITCH stays OUT of the expander architecture** - it needs a real
     hard-off / load-switch / charger ship-mode path, not a firmware GPIO.
   - **POWER-UP SAFE STATE:** MCP23017 pins default to INPUTS (high-Z) until firmware writes
     IODIR. Every safety-relevant enable (load switches, amp shutdown, NFC boost enable,
     resets) needs an **external pull resistor forcing the safe state**. Do NOT rely on
     "firmware writes it low quickly" - a hung or half-flashed firmware makes that high-Z
     window permanent.
7. **External I2C isolation (required).** The community header must NOT expose the internal
   I2C bus naked: 22-47R series resistors near the host, ESD protection at the connector,
   optional solder-jumper external pull-ups, a bus buffer/isolator or bus switch, and a
   firmware/hardware way to disconnect a defective accessory. **A community accessory that
   shorts SDA/SCL must not disable the internal touch/IMU/fuel-gauge/controls or make AQROOT
   unbootable.** Reserved I2C address table to publish for accessory makers: **0x20, 0x21,
   0x36, 0x38, 0x68** (and note the MCP23017 family occupies all of 0x20-0x27).
8. **Hybrid expansion header.** Not expander-only: expose native fast pins (the reclaimed
   native GPIO + I2C SDA/SCL + an interrupt/ready line + 3.3V + switched accessory power +
   multiple grounds) alongside the 16 labeled low-speed expander GPIO. **Do NOT market it as
   "16 GPIO = Flipper's 18"** - the numbers are not the same currency; label expander pins
   clearly as low-speed. **Positioning: AQROOT competes on BUILT-IN capability** (dual radios,
   NFC, IMU, audio, IR, display all onboard), **not on exposed-pin count.** RootProbe remains
   the dedicated high-speed coprocessor interface.
9. **TPS63020 variant framing dropped** - see the corrected note in the regulator section
   above. P/N locked to TPS63020DSJR.

**IMPLEMENTATION NOTE — GPIO21 / GPIO43 role swap (needs sign-off).** The review's wording put
GPIO21 on the expansion header as the native fast pin, and separately required the expander
INT on "a native wake-capable pin". With native margin at zero, both cannot be GPIO21. On the
ESP32-S3 **only GPIO0-21 are RTC GPIO**, so only they can serve as an `ext0`/`ext1` deep-sleep
wake source - GPIO43/44 cannot. Since [[13 - Power Budget and Battery Runtime v0.1]] depends on
deep sleep with wake-on-button for the ~2-week standby figure, the wake requirement is the one
that forces a specific pin. Therefore: **GPIO21 = shared open-drain expander INT / header IRQ
(RTC-capable, wake works)**, and **GPIO43 = the header's native fast pin** (freed by the IR TX
move; as U0TXD it also gives accessories a boot-log/UART pin). Same two roles, same two pins,
assignment swapped so button-wake actually functions. Flagged for explicit sign-off before
schematic capture.

**Net native pin budget after this revision: 29 used, 2 reserved test pads (GPIO45/46), ZERO
free.** Reclaiming GPIO21 and freeing GPIO43 exactly paid for IR TX on GPIO16, the button-wake
line, and one native header pin. Any further native demand - including RootProbe's preferred
low-latency IRQ - must now displace an existing assignment.

**Left open by this review (recorded, not resolved):** the switched accessory-power enable has
no pin (0x20 is full, all 16 of 0x21 are promised to the header); the I2C bus switch/isolator
part is unselected; the physical power-switch topology is unspecified; the IR MOSFET and
resistor values are unspecified.

## PIN BUDGET RESOLUTION — the three open items closed (2026-07-26)

Closes everything the pre-schematic review left open on the pin budget. Detail in
[[11 - Beta Pin Map v0.2]] (revision v0.2.2). **The native pin budget is now CLOSED.**
> CORRECTED (2026-07-26, second design review): that closure claim was premature — RootProbe's
> SPI CS was still an outstanding requirement for a native pin. Genuinely closed in v0.2.3 by
> the GPIO43 multiplex; see the final close-out entry below.

### 1. GPIO21 / GPIO43 role swap — APPROVED, no longer an open item

**GPIO21 = expander button-wake interrupt line. GPIO43 = community-header fast pin.** The swap
made during the review is kept and signed off.

Rationale, stated plainly because it generalises: **the two roles are not symmetric.**
- **Wake capability is a hard electrical constraint of the silicon.** On the ESP32-S3 only
  GPIO0-21 are RTC GPIO, so only they can serve as an `ext0`/`ext1` deep-sleep wake source. A
  polled expander cannot wake the ESP32 at all, so the expander INT line is the *only* thing
  making button-wake possible - and GPIO21 is the only RTC-capable pin available. There is no
  alternative; the constraint decides the pin.
- **The header fast pin is pin-number-agnostic.** An accessory maker cares that the connector
  carries a native, fast, 3.3V pin - not whether it is numbered 21 or 43. GPIO43 satisfies
  every property that matters, and as U0TXD it additionally hands accessories a boot-log/UART
  pin for free.

When one role is constrained by silicon and the other is not, the constrained role takes the
constrained pin. Deep-sleep wake-on-button is load-bearing for the ~2-week standby figure in
[[13 - Power Budget and Battery Runtime v0.1]], so this is not a preference.

### 2. Accessory-power enable — ACC_PWR_EN on 0x21 GPB7; header publishes XGPIO0-14

Option (a) of the three logged during the review. The second MCP23017 (0x21) reserves its
16th pin (GPB7) as **ACC_PWR_EN**, driving the load switch on the community header's accessory
power rail. **The user-facing header is XGPIO0-14 = 15 low-speed user GPIO.**

Rationale: switched accessory power is worth one header pin because it buys two things nothing
else does -
1. **Power-cycle a misbehaving add-on.** With the I2C bus switch (pin map §8a), a latched-up or
   bus-jamming accessory can be isolated *and* de-powered from firmware, with no unplugging and
   no AQROOT reboot. Cutting the bus without cutting the power only half-solves that failure.
2. **Zero idle draw when nothing is attached**, which feeds directly into the standby budget.

**15 user GPIO still exceeds Kode Dot's 14**, so the reservation costs nothing competitively -
noting that [[04 - Competitive Analysis]] already forbids comparing GPIO counts at all, since
these are I2C-mediated low-speed pins and Flipper's/Kode Dot's are native.

ACC_PWR_EN needs an external pull holding the rail OFF at power-up, per the expander
safe-state rule (an unpowered header is the safe default and must not depend on firmware).

### 3a. Button cluster — 7 buttons; A doubles as select; NO D-pad centre

Standard handheld scheme: **D-pad navigates, A = select/confirm, B = back, Home = launcher.**

Final cluster on MCP23017 0x20 Port B: **D-pad UP / DOWN / LEFT / RIGHT, A (=select),
B (=back), HOME** = **7 buttons**.

- **No separate D-pad centre/select button.** A *is* select, so a centre press would be a
  duplicate control competing with A for the same job - added cost and an extra failure point
  for nothing.
- **The 8th button does not exist.** The earlier "D-pad + A/B + Back + Home" phrasing
  double-counted: it listed both a B button and a separate Back button, which are the same
  control. Corrected to 7.
- **Power is a hard switch, not a button** - it stays out of the expander architecture
  entirely (real hard-off / load-switch / ship-mode path), so it consumes no expander pin.

**Consequence: 0x20 GPB7 is spare** - the only unallocated pin anywhere in the design. It is
reserved, not free (see 3b). If RootProbe were ever cancelled, GPB7 is the natural home for a
centre-select or an 8th button.

### 3b. RootProbe host IRQ — expander pin (0x20 GPB7), NOT a native pin

Reserved now, wired in Phase 2 when RootProbe is actually built.

Rationale: **RootProbe does its high-speed capture locally on its own RP2040-class MCU.** The
line crossing to AQROOT is only "data ready / trigger hit / attention" - a notification, not a
sampling signal. Capture fidelity does not depend on how fast the host learns a buffer is
ready, because the timing-critical work already finished on the coprocessor and the samples sit
in RootProbe's own RAM. Expander latency (tens to hundreds of microseconds) is therefore
harmless. The earlier "IRQ/READY should ideally be a native pin for low-latency data-ready"
note in [[14 - RootProbe Interface v0.1]] is superseded - it never made the case for why low
latency mattered, and on inspection it does not.

This applies the "don't let a Phase-2 accessory consume scarce native pins" principle to the
one pin it was most tempting to break it for. Bonus: GPB7 sits on Port B, which already has
interrupt-on-change enabled for the buttons, so the RootProbe IRQ routes through INTB ->
GPIO21 and **can wake AQROOT from deep sleep** at no extra cost.

Also settled in the same pass: RootProbe **MODULE_DETECT** = "does the coprocessor answer on
the I2C management bus" (no pin), and **RESET** = an I2C management command, with the
accessory-side load switch as the power-cycle fallback (no pin). **SPI CS remains the one
RootProbe signal genuinely needing a Phase-2 native-pin decision** - a per-transaction chip
select cannot sit behind an I2C expander at usable speed.

### Net result

**Native pin budget CLOSED: 29 assigned, 2 reserved test pads (GPIO45/46), 0 unassigned, 0
outstanding claims.** RootProbe's IRQ was the last queued demand on a native pin and it is now
on the expander. Expander budget: 0x20 = 15/16 used (GPB7 reserved for RootProbe),
0x21 = 16/16 used (15 user XGPIO + ACC_PWR_EN).

## FINAL PRE-SCHEMATIC CLOSE-OUT — second design review (2026-07-26)

Closes the last open items before KiCad capture. Detail in [[11 - Beta Pin Map v0.2]]
(now v0.2.3) and [[14 - RootProbe Interface v0.1]].

### 1. RootProbe SPI CS — RESOLVED by multiplexing GPIO43

**This fixes a logical contradiction, not just an open question.** The previous entry declared
the native pin budget "closed with 0 outstanding claims" while [[14 - RootProbe Interface v0.1]]
simultaneously recorded that RootProbe still needs a native SPI chip select. Both could not be
true. Deferring CS to Phase 2 did not resolve it - it just moved the contradiction out of sight.

**Decision: GPIO43 becomes a multiplexed net labeled `FAST_IO / U0TXD / ROOTPROBE_CS`.**
- **FAST_IO** - the community header's native fast pin, when a general accessory is attached.
- **ROOTPROBE_CS** - RootProbe's SPI chip select, when a RootProbe module is attached.
- **Mutually exclusive: same physical interface, never both at once.** The net routes to both
  connectors; only one may be populated and active. Firmware arbitrates by I2C enumeration (a
  RootProbe answering on the management bus means GPIO43 is CS and must not be driven as
  FAST_IO). The simultaneous combination is documented as unsupported; series resistors on both
  connector legs limit damage if a user ignores that, but that is damage-limiting, not support.

**Why this genuinely closes the budget:** RootProbe now has a native home for CS (shared,
GPIO43), an expander home for IRQ (0x20 GPB7), and I2C for DETECT and RESET. It has no
remaining unmet pin requirement, so nothing is queued against the native budget any more. The
budget is closed **via the multiplex**, not by having spare pins - and the docs now say so
rather than claiming a clean close that was not real.

**Consequence recorded as a RootProbe FIRMWARE REQUIREMENT:** GPIO43 is U0TXD, so the AQROOT
ROM bootloader drives boot-log traffic onto this net at every reset. RootProbe will see
spurious chip-select activity while AQROOT boots, and its MCU must hold the SPI slave interface
disabled until its own firmware is up and the host has made contact over I2C. This is the same
hazard that moved IR TX off GPIO43 in v0.2.1: a boot-log-driven net is fine for something that
can ignore it, and unacceptable for something that acts on every edge.

### 2. Connector-sheet SCHEMATIC REQUIREMENTS (not blockers to starting capture)

Recorded in pin map §8c, to implement when the community-header / connector sheet is drawn.
These exist because all three nets leave the board and can be shorted, back-powered, or held
low by hardware AQROOT does not control.

**a. Header IRQ/WAKE into GPIO21 - must NOT be wired naked.** GPIO21 is the button-wake
interrupt; an unprotected external accessory could hold it low and **permanently block internal
button wake**, making the device look dead to its own buttons because of a faulty add-on.
Requires: series resistance, connector-side ESD, an **open-drain-only accessory requirement**
published as a hard rule, a defined pull-up on the AQROOT side, and gating so an unpowered or
faulty accessory cannot hold the line low. **Preferred: an open-drain buffer/gate powered from
switched accessory power** - with ACC_PWR_EN off the gate is unpowered and the external leg
drops out of the wired-OR by construction. **Label the external line "optional open-drain
WAKE/ATTN input", not a general interrupt** - it is a request-for-attention, and naming it
accurately stops accessory makers designing against a contract AQROOT does not offer.

**b. GPIO43 on the header.** 220R-1k series resistor + connector-side ESD. **Document that it
emits UART boot-log traffic at reset.** No direct connection to accessory power-enables or
high-current drivers without gating - a boot-log burst must not be able to switch a load.
**Label it honestly as FAST_IO / U0TXD**, never as plain "fast GPIO"; the extra names are the
warning.

**c. ACC_PWR_EN + I2C isolation sequencing.** Defined order: **disconnect external I2C segment
-> accessory power OFF -> discharge -> power ON -> stabilize -> reconnect I2C -> enumerate.**
Detach/fault runs the reverse, isolating the bus before cutting power so a half-powered
accessory never sits on a live bus. **Isolator part selection criteria (binding, not
preferences): must support powered-off high-impedance on the external side, and must NOT
back-power the accessory side.** Back-powering defeats the discharge step, keeps a latched-up
accessory alive, and makes the whole power-cycle useless.

### 3. Terminology fix - 0x20 expander capacity

"Exactly full" with a "spare" pin was misleading in both directions. Correct wording:
**15 assigned + 1 (GPB7) footprint-reserved for the Phase-2 RootProbe IRQ = 0 generally
available.** GPB7 has a committed owner and a reserved footprint; it is simply unpopulated
until RootProbe exists. Plan new signals against zero available capacity on this chip.

### 4. Deep-sleep current caveat - standby figure is ESTIMATED

The ~10-20 uA deep-sleep figure and the ~2-week standby number derived from it are **NOT
measured**, and the ~10-20 uA is an ESP32-S3 *chip* figure standing in for a *system* figure.
The true number must sum **TPS63020 quiescent (~25 uA - already comparable to the entire ESP32
figure) + both MCP23017s + MAX17048 + all pull-ups (7 buttons, INT/wake, I2C pair, every
expander safe-state pull) + load-switch leakage + charger/power-path + display leakage + IMU
wake-mode current.** Two of those - the second expander and the safe-state pulls - are
structural consequences of decisions locked earlier in this log; both are correct decisions
that nonetheless cost standby current, and they have to be counted.

**DO NOT PUBLISH THE STANDBY NUMBER IN MARKETING UNTIL MEASURED ON BETA HARDWARE.** A "2-week
standby" line on a campaign page is a promise; if the measured system figure lands at 100-200
uA the honest answer is days, not weeks. Same rule already applied to demoing only features
that actually work. Marked in [[13 - Power Budget and Battery Runtime v0.1]]; Beta bring-up
must measure true system standby at the battery, in the final enclosure, with wake sources
armed.

## IR: native RMT + transistor LED driver (Beta)
IR validated on the bench (TSOP38238 + TSAL6200). Two Beta requirements emerged:
(1) FIRMWARE: use the native ESP32-S3 RMT peripheral for IR carrier/timing, NOT a
bit-banged library. The S3 is the only ESP32 with RMT DMA, which protects IR timing from
WiFi/BT/radio interrupt jitter - critical since AQROOT runs radios concurrently.
(2) HARDWARE: drive the IR LED through a transistor/MOSFET, not directly from a GPIO.
Direct GPIO drive at 150R gives ~7mA average (vs 100-500mA in a real remote) and only
1-3cm of range. Add the driver stage to the Beta schematic.
