---
tags: [tasks, tracker]
---

# Build TODO Tracker

## Sourcing
- [x] Display sourced — 2.8" IPS ILI9341 capacitive SPI (Elecrow / LCDwiki class).
      AMOLED is now a Kickstarter stretch goal, not a sourcing task.
- [~] VERIFY the exact display module's touch controller is FT6236-family @ I2C 0x38
      before ordering Beta quantity — many cheap ILI9341 modules ship resistive (XPT2046)
      or a different capacitive chip (FT6336/GT911, possibly different address)
- [ ] Confirm SX1262 certified module choice (e.g. Ebyte E22 series) and check
      certification conditions (RF section modification voids certification)
- [ ] Select the production CC1101 part/module (dual-radio base — Alpha used a generic
      blue 433M V2.0 board)

## Firmware bring-up (in build order)
First implementation pass complete — full driver + UI stack written and verified compiling
for both the real-hardware and Wokwi simulation environments. See `Firmware/` and its
README. Real hardware still needs on-device validation once parts arrive.

- [x] Bootloader + display/touch driver bring-up on devkit — LovyanGFX + LVGL glue;
      ILI9341 panel config is the REAL Beta part (not a placeholder); touch driver logic
      is FT6236-compatible
- [x] App-launcher shell (LVGL 8.3.x) — tile dashboard (Scan/NFC/Infrared/GPIO/Bluetooth/
      Tools) + Signal Monitor and NFC Tag panels, plus one screen per tile
- [x] Radio driver via RadioLib (SX1262) — both LoRa and raw sub-GHz FSK modes
- [x] NFC driver (breakout first) — Adafruit_PN532 real tag read + Mifare Classic block write
- [x] Sensors/audio driver — generic I2C 6-axis IMU (placeholder part) + ESP32 I2S audio

## Firmware follow-ups (post first-pass)

Three of these are real engineering tasks created by locked part decisions, not cleanup.
They are the outstanding firmware debt between the current code and the Beta design:

- [ ] **Replace the PN532 I2C NFC driver with an ST25R3916 SPI driver.** The current
      `drivers/nfc.cpp` + the `adafruit/Adafruit PN532` dependency in platformio.ini target
      the wrong chip AND the wrong bus. The Alpha raw-SPI validation (IC-ID 0x3F -> 0x2A) is
      the foundation; full tag read/write needs the ST RFAL library port.
- [ ] **Add a CC1101 driver + a radio manager spanning both radios.** Firmware is currently
      SX1262-only. Dual-radio is locked for production, so the manager must enforce
      one-TX-at-a-time and CS discipline across CC1101 + SX1262 on shared SPI Bus B.
- [ ] **Add a real IR driver (RMT-based TX/RX)** on native pins **TX=16 / RX=44**, 38kHz
      carrier — `ir_screen` is currently a UI shell only. (TX moved off GPIO43 in pin map
      v0.2.1: GPIO43 is U0TXD and carries the ROM boot log.) Parts in hand.
- [ ] Add the SparkFun BMI270 library to platformio.ini and swap the generic register map in
      sensors.cpp. The part is LOCKED (BMI270, Alpha-validated at 0x68) — but the BMI270
      needs a config-blob upload before accel/gyro data works, which raw register poking
      does not do.
- [ ] Add an FT6236 reset pulse to `touch_init()`. Alpha gotcha: the touch controller is held
      asleep until CTP_RST is pulsed low->high and does NOT appear on an I2C scan without it.
      **Beta: touch RST = `TOUCH_RST_N` on U60 P00, display RST = `DISP_RST_N` on U60 P04** (both
      moved off native GPIO21), so the boot order is I2C up -> configure U60 -> pulse touch RST
      -> init touch. The reset pulse is now an expander write, not a GPIO toggle.
- [ ] **Add a TCA9535 driver + button/wake handling.** **ONE address-parameterised driver serving
      both devices** — U60 @ 0x20 (buttons + internal control) and U61 @ 0x21 (external header).
      They are the same silicon; do not write two drivers. Requirements:
      - **Registers (the complete set — there are no others):** `0x00` Input Port 0, `0x01` Input
        Port 1, `0x02` Output Port 0, `0x03` Output Port 1, `0x04` Polarity Inversion 0, `0x05`
        Polarity Inversion 1, `0x06` Configuration 0, `0x07` Configuration 1.
      - **Write the safe output-latch value (0x02/0x03) BEFORE flipping any Configuration bit
        (0x06/0x07) from input to output.** Config resets to `0xFF` (all inputs) and the output
        latches reset to `0x00`, which is not the safe state for every net — set the latch first
        or risk glitching `NFC_5V_EN`, `AMP_SD_MODE`, or `ACC_PWR_EN` at boot.
      - **Source identification is snapshot-compare, not a register read.** The TCA9535 has no
        interrupt-capture register, so on every `WAKE_INT_N` assertion read both input-port
        registers from **both** devices and diff against the driver's previous snapshot.
      - **Treat `WAKE_INT_N` as level-sensitive** and re-check that it released — two devices
        share the net, so a second assertion during service keeps it low and an edge-only
        handler will miss it.
      - **Deep-sleep wake arming** on GPIO21 (`ext0`/`ext1`).
      - **NO MCP23017 register assumptions.** There is no IODIR, GPPU, GPINTEN, INTF, INTCAP,
        IOCON, DEFVAL, or INTCON on this part, and no internal pull-ups at all.
      - **Bring the I2C bus up at 100 kHz, then verify 400 kHz.**
      None of this exists yet, and **none of it has been validated on a TCA9535 — the Alpha bench
      test was an MCP23017, a different part.** See [[11 - Beta Pin Map v0.2]] §7c.
- [ ] Reconcile Firmware/src/config.h pin assignments with [[11 - Beta Pin Map v0.2]] —
      every bus currently differs (display DC/RST, I2C on 17/18 vs 1/2, radio sharing the
      display bus, I2S on the wrong pins). Config.h is still placeholder wiring matched to
      the Wokwi diagram.
- [ ] On-device validation of every driver once prototype hardware is assembled

## Hardware
- [ ] Build Stage 1 dev-board prototype (see BOM tracker)
- [ ] Validate battery runtime against the ~12-15hr active target (2000mAh) — see
      [[13 - Power Budget and Battery Runtime v0.1]]
- [ ] Design ST25R3916 NFC antenna matching network for final PCB
- [ ] Design custom PCB (4-layer, JLCPCB)
- [ ] Reverse-polarity protection at the battery input + keyed connector + a battery tray
      that can't invite reversed insertion (from the bench incident — see
      [[05 - Design Decisions Log]])

## Pre-schematic review follow-ups (2026-07-26, must settle before/at capture)
- [x] ~~Sign off the GPIO21 / GPIO43 role swap~~ — APPROVED: GPIO21 = wake INT (RTC-capable),
      GPIO43 = header fast pin. See [[11 - Beta Pin Map v0.2]] §6a
- [x] ~~Find a pin for the switched accessory-power enable~~ — ACC_PWR_EN = **U61 P17**;
      header publishes XGPIO0-14 (15 user GPIO)
- [x] ~~D-pad centre button / RootProbe native IRQ~~ — no centre button (A = select, 7 total);
      RootProbe IRQ = `ROOTPROBE_IRQ_READY_N` on **U60 P17** (expander, Phase 2)
- [x] ~~RootProbe SPI CS needs a native pin vs "zero native pins" contradiction~~ — RESOLVED:
      GPIO43 multiplexed as `FAST_IO / U0TXD / ROOTPROBE_CS` (mutually exclusive). Native
      budget genuinely closed. See [[11 - Beta Pin Map v0.2]] §9a
- [x] ~~Select the GPIO expander part~~ — **LOCKED 2026-07-27: TI TCA9535PWR x2** (U60 @ 0x20,
      U61 @ 0x21; PW / TSSOP-24 / 0.65mm; symbol `Interface_Expansion:TCA9535PWR`, footprint
      `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm`). Replaces the MCP23017 — see
      [[05 - Design Decisions Log]]

### Explicitly UNRESOLVED part selections (both still block schematic freeze)
- [ ] **Select the external community-header I2C isolator or bus switch part** — **must support
      powered-off high-impedance and must NOT back-power the accessory side**
- [ ] **Select the ACC_PWR_EN accessory load switch part** for the accessory rail
- [ ] **Footprint audit U60/U61** — verify `Interface_Expansion:TCA9535PWR` pin numbering and the
      TSSOP-24 footprint geometry against the TI datasheet before freeze. Assigned, not verified

## Connector-sheet schematic requirements (implement when drawing that sheet, not blockers)
- [ ] Header IRQ/WAKE into GPIO21: series R, connector ESD, open-drain-only accessory rule,
      defined AQROOT-side pull-up, gating (open-drain buffer on switched accessory power).
      Label "optional open-drain WAKE/ATTN input"
- [ ] GPIO43 header leg: 220R-1k series R + ESD; document boot-log traffic; no ungated
      connection to power-enables/high-current drivers; label FAST_IO/U0TXD honestly
- [ ] ACC_PWR_EN + I2C sequencing: disconnect -> power off -> discharge -> power on ->
      stabilize -> reconnect -> enumerate (reverse on detach/fault)

## Beta bring-up measurements
- [ ] **Measure true system standby current** at the battery, in the final enclosure, deep
      sleep with wake sources armed. The ~10-20uA/~2-week figures are ESTIMATES. Do NOT
      publish a standby number in marketing until this is measured
- [ ] Specify the physical power-switch / hard-off (load-switch / ship-mode) topology
- [ ] Specify IR TX MOSFET + gate/current-limit resistor values for the target drive current
- [ ] Spec TPS63020DSJR support components (inductor, feedback resistors, caps) with DC-bias
      derating accounted for
- [ ] Add external pull resistors forcing the SAFE state on every expander-driven enable —
      **the TCA9535 has no internal pull-ups, so these are the only pulls in the design**
- [ ] Publish the reserved I2C address table (0x20, 0x21, 0x36, 0x38, 0x68) for accessory makers
- [ ] Validate GPIO3 strap integrity: 50-100 cold boots with motion applied during reset
- [ ] **FIRST-EVER hardware validation of the TCA9535PWR** (U60 + U61): basic bidirectional I/O
      on both ports, two devices at 0x20/0x21 on one bus, address straps, `/INT` +
      wired-OR `WAKE_INT_N`, button wake from deep sleep, output-latch-before-direction ordering
      (scope `NFC_5V_EN` / `AMP_SD_MODE` / `ACC_PWR_EN` for boot glitches), and I2C at 100 kHz
      then 400 kHz. **Nothing about this part has been bench-proven** — the Alpha expander test
      used an MCP23017
- [ ] Remaining Alpha-part confirmations carried into Beta: ICS-43434 mic first live capture
      (Alpha unit was dead). *(IR, audio-out, TPS63020 3.3V rail and bq25185 charging all passed
      on the Alpha bench. The Alpha "expander" pass was an MCP23017 and does NOT carry over.)*

## Project/business
- [ ] Set prototype budget ceiling
- [ ] Decide how many prototype units to build for reviewer seeding
- [ ] Prepare press kit for YouTuber outreach (see Kickstarter and Review Strategy note)
- [ ] Set Kickstarter launch date and reviewer embargo date
