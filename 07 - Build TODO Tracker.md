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
- [x] ~~Confirm SX1262 certified module choice~~ — **LOCKED 2026-08-07: Ebyte E22-900M22S**
      (915 MHz), U8. Physically captured with a VERIFIED_VENDOR_EXACT footprint. **Certification
      condition honoured: RF section modification voids certification, so all RF is marked
      DO NOT ROUTE** and the antenna leaves via the module IPEX port
- [x] ~~Select the production CC1101 part/module~~ — **LOCKED 2026-08-07: Ebyte E07-400M10S**
      (433 MHz), U7. Certified module rather than a bare IC, same DO-NOT-ROUTE RF rule as the E22


## Physical schematic capture — status (updated 2026-08-08)

**Coverage: 186 components, 172 footprinted, 14 missing.** No connectors remain unfootprinted.

Closed this run (each with a verified, non-fabricated land pattern):

- [x] **J1 display interface** — Hirose **FH69-50S-0.5SH** 50-pin 0.5 mm FPC. The obsolete FCI
      62684 was dropped. Panel locked to **SPI mode II with readback (IM3:IM0 = 1110)**.
      Backlight = **TPS61169DCKR** + 4×39R ballasts + 2.55R RSET
- [x] **J2 microSD** — Molex **5025700893**, push-push with mechanical card detect.
      **Card detect captured on a named `SD_CARD_DETECT_TBD` net but deliberately NOT routed**
- [x] **U7** Ebyte **E07-400M10S** (CC1101, 433 MHz) integrated on sheet 04
- [x] **U8** Ebyte **E22-900M22S** (SX1262, 915 MHz) integrated on sheet 04
- [x] **U9** ST **ST25R3916-AQET** integrated with the 10 ST-specified decoupling caps C45-C54
- [x] **U12** TPS63020 **DSJ** footprint built
- [x] **SW9** verified vendor-exact

Still missing footprints — **`C12 C18 C19 LS1 R24 SW1`-`SW8 U14`**:

- [ ] **LS1** speaker — mechanical/vendor selection still open
- [ ] **U14** — footprint still open
- [ ] **SW1-SW8** button cluster + **R24**, **C12**, **C18/C19** — support parts pending
      selection. *(C18/C19 are the ST25R3916 external supply rails' decoupling — `+3V3`/VDD_IO
      and `NFC_5V_PA_PENDING`/VDD+VDD_TX. **Values remain placeholders because ST specifies the
      regulator-output decoupling but not these external-rail values** — nothing was force-fitted)*

**Open engineering items created by this capture:**

- [ ] **Allocate a real card-detect input, or formally accept no card detect.** J2 pin 10 is
      captured and traceable but unrouted; **no GPIO was allocated and the MCU pin map is
      unchanged.** This needs a pin-map revision or an explicit decision to drop the feature
- [ ] **Re-establish the absolute ERC baseline under ONE fixed `kicad-cli` invocation.** The
      figure of "0 real violations, 24 exclusions" quoted in earlier sessions **does not
      reproduce**; the current invocation reports 5 `label_dangling` at error severity, unchanged
      before and after the J2 work. Changes are currently being validated by **delta**, which is
      sound but is not a substitute for a trustworthy absolute number
- [ ] **Resolve the deferred `*_TBD` nets** — 16 deferred labels across NFC, CC1101 and SX1262
      (crystal, matching, AAT, antenna). These are intentionally unrouted, not oversights

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
      SX1262-only. **The parts are now locked: E07-400M10S (CC1101) and E22-900M22S (SX1262).**
      The manager must also drive **`SX1262_RXEN` (U61 P16)** for the E22 RF switch — `TXEN` is
      handled inside the module by `DIO2`, but **`RXEN` is a host responsibility via the expander**. Dual-radio is locked for production, so the manager must enforce
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
      - **PARKED (2026-07-30) — leading candidate documented, topology NOT locked.**
        High-side only; battery negative stays tied to system GND (locked). Keyed connector
        is an *additional mechanical layer only*, never the primary electrical defence.
        Leading candidate: **ADI LTC4368-1** (active back-to-back N-FET controller, ~2.5–60 V,
        ~80 µA Iq, forward/reverse sense ~±50 mV, MSOP or 3×3 DFN) + **back-to-back N-channel
        AO3400A-class** FETs, two in series (AOS AO3400A, LCSC C20917, SOT-23, 30 V,
        ~48 mΩ @ Vgs 2.5 V, Vgs max ±12 V). Active gate turn-off is what avoids the AN-171
        equilibrium. **AO3401A (LCSC C15127) remains valid as a building block** if a PMOS
        variant is chosen. Exact MOSFET, sense resistor, UV/OV divider, timer/inrush parts,
        gate clamp and package **not selected**.
      - **Rejected as final solutions — do not revisit:** single PMOS alone; naive passive
        back-to-back; any passive gate network that can leave a FET partially-on under
        charger drive; low-side protection; keyed connector as primary defence; ordinary load
        switches that block charging; cell over/under-voltage protectors that don't address
        physical reverse insertion.
      - [ ] **GATE — professional power/DFM pre-fabrication review owns the final topology
            lock.** It must run the **LTC4368 LTspice charge-path case** and obtain **ADI
            vendor/FAE confirmation**. **BLOCKS PCB routing and fabrication release for the
            whole board** — not just the power sheet.
      - [ ] Close STATUS items (a)–(f), all assigned to that review: **(a)** LTspice
            validation of the 1 A charge-path / reverse-sense question — does normal charging
            current flowing VOUT→VIN trip the reverse sense; **(b)** ADI vendor confirmation;
            **(c)** UV/OV divider values for 3.0–4.2 V; **(d)** sense-resistor value vs charge
            current; **(e)** Vgs-clamp need vs the ±12 V FETs; **(f)** standby-current impact
            of the ~80 µA controller. Plus: negative-input behaviour while output is
            charger-powered; startup and hot-insertion; BQ25185 detection / termination /
            recharge interaction; voltage drop and thermals.
      - [ ] Prove the **locked REQUIREMENT** (holds regardless of final topology) — reversed
            battery *while USB powers the BQ25185*: both pass FETs fully off, sustained
            current into the reversed cell blocked, BQ25185 `BAT` kept above its ~−0.3 V
            abs-max, and **no AN-171 linear-equilibrium self-heating**.
      - [ ] Capture `01_POWER_TREE` — **every section except the battery-input protection
            block is drawn normally**. That block stays a clearly labelled placeholder:
            `REV-POLARITY: LTC4368-1 + BACK-TO-BACK NFETS (LEADING CANDIDATE)` /
            `TOPOLOGY PENDING SIM / VENDOR REVIEW` / `DO NOT ROUTE`. The rest of the power
            tree is **not** blocked by this park.
      - [ ] Run the **14-case Beta validation card** (see [[05 - Design Decisions Log]]).
            Battery **simulator** before a real LiPo; USB limit **50 mA**, simulator limit
            **25–50 mA**. Abort on `BAT` < **−0.3 V**, sustained reversed-cell current
            > **10 mA**, gate plateau, rapid heating, oscillation, or unstable `BAT`/`SYS`.

## Pre-schematic review follow-ups (2026-07-26, must settle before/at capture)
- [x] ~~Sign off the GPIO21 / GPIO43 role swap~~ — APPROVED: GPIO21 = wake INT (RTC-capable),
      GPIO43 = header fast pin. See [[11 - Beta Pin Map v0.2]] §6a
- [x] ~~Find a pin for the switched accessory-power enable~~ — ACC_PWR_EN = **U61 P17**;
      header publishes **XGPIO0-13 (14 user GPIO)** *(v0.2.5 — was XGPIO0-14 / 15; U61 P16 was
      reclaimed as `SX1262_RXEN`)*
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

> **Candidate ≠ decision.** The part numbers below are **CTO PROPOSALS to evaluate**, recorded
> here so they are not lost. **Nothing in this section is locked.** Do not put any of these
> parts into a schematic, a BOM, or a status report as a selected part. Each must clear its
> stated criteria against the manufacturer datasheet first, and the selection must then be
> logged as a decision in [[05 - Design Decisions Log]].

- [x] ~~**Select the external community-header I2C isolator or bus switch part**~~ — **LOCKED
      2026-08-07: TI `TCA9517ADGKR` (DGK / VSSOP-8), U16.** PCA9515A not selected.
      - Historic note, kept because the criteria still gate bring-up validation:
        Neither has been checked against the two binding criteria above. Note these are
        different device classes — a level-translating buffer vs a bus repeater — so evaluating
        them is not a like-for-like price comparison; confirm which class actually delivers
        powered-off high-Z and no accessory-side back-powering before shortlisting either.
- [x] ~~**Select the ACC_PWR_EN accessory load switch part** for the accessory rail~~
      - **LOCKED 2026-08-07: TI `TPS22918DBVR` (DBV / SOT-23-6), U15.** Historic note, kept
        because these checks still gate bring-up validation. Not yet
        checked for current rating against the accessory rail budget, quiescent current
        against the standby target, controlled slew / inrush behaviour, or the discharge
        behaviour the §8c-c sequencing depends on (disconnect -> power off -> **discharge** ->
        power on -> stabilize -> reconnect -> enumerate).
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
- [x] ~~Spec TPS63020DSJR support components (inductor, feedback resistors, caps) with DC-bias
      derating accounted for~~ — **ARCHITECTURE LOCKED 2026-07-30, schematic capture APPROVED.**
      L1 = Coilcraft **XFL4020-152MEC** 1.5µH (LCSC C3033018); FB = `R_FB_TOP` 1M /
      `R_FB_BOTTOM` 180k 1%, no Cff; `C_VINA` 100nF; **physical hard-off switch** on EN + `R_EN_PULLDOWN` 100k (old `R_EN_LINK`
      0R withdrawn → `R_EN_BYPASS` 0R DNP; never firmware-driven); `R_PS_DEFAULT` 0R to GND (power-save); `R_PG_PULLUP` 1M (PG
      diagnostic-only, no GPIO). Capacitor **values/voltages/dielectrics/packages locked**;
      **exact MPNs deferred** to the pre-fab BOM pass below. See [[05 - Design Decisions Log]]
- [ ] **Pre-fab BOM-validation pass (board-wide, ONE batched pass — a BOM-release gate, NOT a
      schematic-capture gate).** Do not stall capture on per-capacitor DC-bias research. Runs
      alongside the professional power/DFM review. Must archive, for **every exact capacitor
      MPN**: datasheet permalink; manufacturer DC-bias curve/model/CSV or numerical output;
      operating voltage; nominal capacitance; **effective** capacitance at operating voltage;
      tolerance calculation; temperature assumption; **total** effective capacitance
      calculation; lifecycle status; distributor/LCSC/JLCPCB code; stock-check date; and a note
      to **recheck stock at BOM release**. For **the inductor**: datasheet; official
      footprint/land pattern; DCR typ **and** max; Isat at **10% / 20% / 30%** L loss; Irms
      thermal-rise definition; height; lifecycle; LCSC mapping; stock-check date.
      - [ ] TPS63020 CIN: 2×10µF, 10V+, X7R — combined effective **≥10µF at 4.5V**, each
            retaining ~**≥5µF at 4.5V** after derating. **Obsolete GRM21BR71A106KE51L must NOT
            be used.** Provisional footprint 1206 (prefer over 0805 unless mechanically forced).
      - [ ] TPS63020 COUT: 4×22µF, 10V, X7R, **1206** — combined effective **≥40µF at 3.3V**,
            each averaging **≥10µF** under the documented acceptance assumptions. Provisional
            MPN **Murata GRM31CR71A226ME15L** — verify Murata DC-bias data before fab.
      - [ ] Confirm L1 XFL4020-152MEC lifecycle + stock. **XGL4020-152 may be reviewed as an
            approved alternate — DO NOT SILENTLY SUBSTITUTE**, and do not list it as installed.
      - [ ] USB-C connector: confirm the **exact GCT USB4105 suffix** (candidate
            **USB4105-GF-A-120**) against the official drawing, **shell-stake length vs final
            PCB thickness**, symbol pin numbering, and that the KiCad footprint
            `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` matches the
            manufacturer drawing. Recheck stock/lifecycle.
      - [ ] USB ESD array **USBLC6-2SC6**: recheck stock/lifecycle; verify symbol pin numbering
            against the **ST datasheet** (do not trust a generic 6-pin ESD symbol).
      - [ ] `C_USB_VBUS` 4.7µF 10V+ X7R — effective-capacitance verification (kept at 4.7µF
            deliberately, not 10µF, to keep hot-plug inrush conservative).

## Power tree — final three blocks (Beta-locked 2026-07-31 — see [[05 - Design Decisions Log]])

- [x] ~~Define the NFC 5V PA boost~~ — **BETA LOCKED: TI TPS61023DRLR**, DRL/SOT563 6-pin.
      `BQ25185_SYS` → `NFC_5V_PA_PENDING`, enabled by `NFC_5V_EN` (U60 P02), feeding
      **ST25R3916 `VDD_PA` only** — `VDD_IO` stays on `+3V3`.
- [ ] **Read the current TPS61023 datasheet + EVM schematic and record the exact FB divider,
      inductor and capacitor values.** They are deliberately **not** written down yet — do not
      invent them from memory. **Do not substitute a generic SOT-23 footprint** for DRL.
- [ ] Verify the **100k safe-state pull-down on `NFC_5V_EN` is electrically effective before
      the TCA9535 configures its output**, and that no conflicting pull-up was added.
- [ ] NFC boost Beta bring-up: 5V accuracy; startup on enable; clean shutdown; **no output when
      disabled**; input current; **ripple during NFC field transmission**; TPS61023 + inductor
      temperature; ST25R3916 `VDD_PA` current; **no backfeed into `+3V3` or `BQ25185_SYS`**.
- [x] ~~Select the exact fuel gauge part~~ — **MAX17048G+T10** (prefer G over the X WLP).
      I²C **0x36**, no sense resistor, **protected-side placement only**.
- [ ] Verify MAX17048 pinout/package drawing, assign the **exact ADI land pattern**, handle the
      **exposed pad**, and check the official typical application for CELL filtering, VDD bypass
      and alert-network parts before claiming "one capacitor".
- [ ] **Power-domain / backfeed review:** the MAX17048 stays battery-powered while `+3V3` is
      off, but the I²C pull-ups are on `+3V3`. **Verify SDA/SCL cannot back-power the disabled
      rail.** No level shifting unless primary documentation requires it.
- [ ] MAX17048 Beta bring-up — **never bench validated on AQROOT**: I²C detect at 0x36;
      cell-voltage accuracy; SOC plausibility; charge/discharge response; hibernate entry/exit;
      battery insertion/removal; charger-connected behaviour; hard-off behaviour; no I²C
      backpower; firmware temperature compensation; low-battery threshold.
- [x] ~~Specify the physical power-switch / hard-off topology~~ — **SPST maintained slide switch,
      VINA → switch → TPS63020 EN, with `R_EN_PULLDOWN` 100k to GND.** Chosen over SPDT because
      no switch position can short VINA to GND. **The permanent `R_EN_LINK` 0R is withdrawn** →
      `R_EN_BYPASS` 0R **DNP** (bench bypass only).
- [ ] **Field Slate mechanical review of the switch** before routing: actuator travel, body
      dimensions, mounting tabs, PCB edge setback, enclosure cutout, hand-solder access. MPN
      provisional, but the footprint must match a real candidate.
- [ ] **Do not describe hard-off as zero battery draw.** It disables the `+3V3` system rail
      only; bq25185, MAX17048 and the reverse-protection controller stay powered upstream.
      Soft push-button power UX / load switch / latch / shipping mode = **post-Kickstarter, not
      Beta**.

## USB-C front end (Beta-locked 2026-07-30 — see [[05 - Design Decisions Log]])
- [x] ~~Define the USB-C role and front-end architecture~~ — **BETA ARCHITECTURE LOCKED:**
      sink/UFP, 5V only, USB 2.0 full-speed. **No PD, no source role, no DRP, no VCONN, no alt
      modes.** Two **independent** 5.1k 1% Rd resistors; USBLC6-2SC6 ESD; 22R series at the MCU;
      100pF EMC footprints DNP; shield on its own net with a 0R default link.
- [x] ~~Route the USB differential pair end to end~~ — **CLOSED 2026-08-12. USB BLOCK
      HARD-LOCKED COMPLETE.** `USB_D_MCU_N` and `USB_D_MCU_P` are each a single copper island from
      J3 through U10 and the 22R series resistors to U1.13 / U1.14; both E4 handoff vias consumed;
      DRC **0 electrical errors**; uncoupled **22.1321 / 25.000 mm**; MCU-side skew **1.1011 /
      2.000 mm**; 0 NFC-keepout intrusion; 0 new RF-band vias or B.Cu. Chirality crossover on
      In2 (N) / B.Cu (P) at x 39.4–40.15, y 60.85–62.75. See [[05 - Design Decisions Log]].
- [x] ~~Route SPI_B_SCK and SPI_B_MOSI~~ — **PARTIAL 2026-08-12.** Both nets reach **U1, U8 and U7**
      through their staged C-E crossings (x 59.000 / 60.000); DRC **0 electrical errors**; USB
      untouched. **Each net still has one open connection: U9.** See the blocker below.
- [x] ~~BLOCKER: U9's SPI-B pads have no escape~~ — **RESOLVED 2026-08-12 by CTO Option A.** U9 moved
      **0.050 mm south**, (24.500, 22.000) → (24.500, 22.050); rotation, side and every other
      footprint unchanged. All three escapes now legal for a 0.20 mm F.Cu track: **U9.30 0.2300 mm**,
      **U9.31 0.2126 mm**, **U9.32 0.6500 mm** clearance, each with an ordinary 0.60/0.30 via landing.
      USB, `BMI270_INT1_STRAP` and the SPI-B trunks untouched. *(Correction: the earlier "U9.30 is
      sealed" finding was a grid-resolution artifact — U9.30 always had a 0.2100 mm escape. U9.31
      was genuinely blocked, so the blocker itself was real.)* See [[05 - Design Decisions Log]].
- [x] ~~Prove the three U9 escapes can coexist~~ — **DONE 2026-08-12. U9 moved to (24.500, 22.250)**,
      total **0.250 mm S** from the original (24.500, 22.000). All three escapes demonstrated
      **simultaneously** with real 0.20 mm F.Cu test geometry: SCK 0.2484 mm clearance via the NE
      gateway, MOSI 0.2011 mm via a newly-opened **west bypass**, MISO 0.3850 mm on its own west lane;
      minimum inter-track separation 0.5350 mm. Test tracks were proof-only and never written.
      See [[05 - Design Decisions Log]].
- [x] ~~Lay U9's SPI-B escapes on the proven corridors~~ — **DONE 2026-08-12. SPI-B SHARED BUS
      HARD-LOCKED COMPLETE.** All three nets closed: `SPI_B_SCK`, `SPI_B_MOSI` and `SPI_B_MISO` each
      form a single island over U1, U9, U8 and U7; board ratsnest 430 → 424; DRC 0 electrical errors.
      Measured together, the three U9 escapes keep SCK↔MOSI 0.3350, MOSI↔MISO 0.2250, SCK↔MISO
      0.8000 mm, and MOSI holds **0.2011 mm** to U9.32 exactly as predicted. All three E5 crossings
      (x 59 / 60 / 61) consumed in place. See [[05 - Design Decisions Log]].
- [x] ~~Route the U1-origin SX1262 controls~~ — **DONE 2026-08-12 (pass 3A-1). `SX1262_CS_N` and
      `SX1262_BUSY` complete**, each a single island (CS_N: U1.10 + U8.19 + R27.2, 175.930 mm,
      2 vias; BUSY: U1.12 + U8.14, 195.126 mm, 4 vias). Board ratsnest 424 → 419; DRC 0 electrical
      errors. R27 confirmed a **pull-up tee**, not a series element. E5 crossings x 62.000 and
      x 64.000 consumed in place. See [[05 - Design Decisions Log]].
- [x] ~~Resolve the blocked `SX1262_DIO1` U1 escape~~ — **DONE 2026-08-13 by PIN SWAP, not routing.**
      `SX1262_DIO1` moved U1.11/IO18 → **U1.31/IO38** (1.100 mm via margin, south row);
      `NFC_IRQ` took U1.11/IO18 in exchange. Zero copper moved: 493 tracks / 129 vias before and
      after, only 2 pad net assignments changed. CS_N (E5 x62, R27 pull-up) and BUSY (E5 x64)
      untouched; DIO1 keeps E5 x63 → U8.13. See [[05 - Design Decisions Log]].
- [x] ~~Route SX1262_DIO1 from U1.31 / IO38~~ — **DONE 2026-08-13. SX1262 U1-ORIGIN CONTROL BLOCK
      HARD-LOCKED COMPLETE.** One island over U1.31 and U8.13, 148.407 mm, 14 tracks, 5 vias
      (B.Cu 7 / In2 5 / F.Cu 2); minimum clearance 0.30000 mm copper across the whole net. The x63
      E5 crossing is consumed. Board ratsnest 419 → 417; DRC 0 electrical errors. All three
      SX1262 controls (CS_N x62, DIO1 x63, BUSY x64) are now closed.
      See [[05 - Design Decisions Log]].
- [ ] **`NFC_IRQ` — INTENTIONAL, NOT CONNECTED IN BETA.** It now sits on U1.11, the pad with no
      legal escape. Hardware IRQ is **deferred to the NFC-enablement respin**. Beta NFC scope is
      **polling-based digital bring-up only**. This is an intentional-unrouted ledger item, not a
      routing defect — it accounts for 1 of the 419 ratsnest items.
- [ ] **Beta bring-up: verify ST25R3916 interrupt-status polling.** With no IRQ line there is no
      edge notification; the driver must poll the interrupt-status registers. Measure latency and
      CPU cost on real hardware before fixing the respin scope.
- [ ] **Firmware: `RADIO_DIO1` → GPIO38.** `Firmware/src/config.h` is still a declared placeholder
      (`RADIO_DIO1 38`, `RADIO_NSS 8`, `RADIO_BUSY 39`, `I2C_SDA 17` — none match the schematic),
      so this costs nothing incremental. **Full Beta pin-map reconciliation against
      [[11 - Beta Pin Map v0.2]] is still outstanding**, and the Beta NFC path must poll
      ST25R3916 interrupt status rather than wait on an IRQ.
- [ ] **Pre-fab silk tidy-up: C50 and C52 reference-designator text is clipped by U9's south pads**
      (6 cosmetic `silk_over_copper` warnings introduced by the 0.250 mm U9 move). No electrical
      content; nudge the silk text when the board is otherwise final.
- [ ] **Beta bring-up: scope the USB pair.** Two accepted-by-analysis items are carried into
      bring-up rather than resolved on the board — the **E4 In2 impedance discontinuity**
      (~139.8 Ω against a 90 Ω F.Cu target) and a **7.245 mm (~52 ps) full-path intra-pair
      length difference** dominated by pre-existing connector-side geometry. Both are immaterial
      at Full Speed by analysis; **neither is production-validated.**
- [ ] **EMI / ESD review of the shield-to-ground strategy** — 0R link is the Beta default,
      1M bleed is a DNP alternative. **Do not populate both without explicit review**, and **do
      not leave the shield floating without review.**
- [ ] Signal-integrity review before changing 22R → 33R (**never mix values across the pair**)
      and before populating the 100pF EMC capacitors.
- [x] ~~C21/C22 Beta architecture~~ — **LOCKED 2026-08-12 (CTO, Option B):** both retained
      physically at 100 pF **DNP**, **data-side pins intentionally NC for Beta**, GND side
      retained, **rework-only tuning contingency**. 25 mm USB uncoupled rule and 2.0 mm skew rule
      unchanged. See [[05 - Design Decisions Log]].
- [ ] **Revalidate the 100 pF value against actual measured USB edge-rate / EMI behaviour before
      any future population or reconnection of C21/C22.** The value is an inherited assumption,
      not a measured result.
- [x] ~~VERIFY after final USB routing: C21 / C22 data-pad rework accessibility~~ — **CLOSED
      2026-08-12, PASS.** With the USB MCU-side pair routed, the nearest solder-accessible point on
      each capacitor's matching net is a **mask-open pad**, not track copper: **C21 pad 1 →
      R33 pad 2** and **C22 pad 1 → R34 pad 2**, both 3.053 mm centre-to-centre and **1.812 mm
      pad-edge to pad-edge** — trivially inside tack-jumper reach. Those are the MCU-side terminals
      of the 22R series resistors, i.e. exactly the node each capacitor is meant to shunt.
      **No mask scraping required. No future-revision test point required.** No copper was added
      for rework access. See [[05 - Design Decisions Log]].
- [ ] **Set the bq25185 input-current limit conservatively for generic ports.** There is **no CC
      current-advertisement detection** in this design — Rd only establishes the sink role. Do
      not assume 1.5A/3A from an unknown source. **The charger-input-current setting and the
      battery-charge-current setting are separate decisions.**
- [ ] Verify at capture: CC1/CC2 have separate resistors and are not shorted; **GPIO20 = D+,
      GPIO19 = D−**, not crossed; USBLC6 VBUS is a branch, not series; SBU1/SBU2 carry
      no-connect markers; all duplicate VBUS/GND/D+/D− contacts joined; **no invented SuperSpeed
      pins**; no PD controller; **no GPIO allocated for CC logic**.
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
