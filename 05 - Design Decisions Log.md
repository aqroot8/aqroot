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
> UPDATED 2026-08-07: the exact modules are now fixed — **E22-900M22S** (SX1262) and
> **E07-400M10S** (CC1101). "e.g. Ebyte E22 series" is no longer an example. The CC1101 is
> now also a module, not a bare IC. See *Radio modules LOCKED* at the end of this doc.
> The certification caveat in the line above is now a live open item, not a footnote: the
> Beta antennas are NOT the modules' stock antennas.
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
> UPDATED 2026-08-07: the package is now fixed — **ST25R3916-AQET**, discrete, with an ST
> reference-derived tuned PCB loop and ST reference matching network. See *NFC package
> LOCKED: ST25R3916-AQET* at the end of this doc. The RF/matching/antenna work is still
> uncaptured and remains DO NOT ROUTE.

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
> alternative. Orderable P/N locked: **TPS63020DSJR** (reel). ~~It is **not considered
> "selected" until its inductor, feedback resistors, and input/output caps are selected with
> it**~~ — **SUPERSEDED 2026-07-30: the block is now ARCHITECTURE LOCKED and schematic capture
> is APPROVED. The inductor and all resistors are locked; capacitor values/voltages/dielectrics/
> packages are locked; only exact capacitor MPNs remain open, and those are a BOM-release gate,
> not a capture gate.** See *TPS63020 3.3V regulator block* below. The original reasoning still
> holds and is kept for the record: a buck-boost is a compensated loop, not a drop-in symbol. Spec all support components
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
> UPDATED 2026-08-07 (module lock): the 433/915 antenna descriptions above are superseded.
> Both are now purchased flex antennas plugging onto the module IPEX ports — 915 = Taoglas
> FXP890, 433 = Taoglas FXP450 — NOT board-level designs. No matching networks and no U.FL
> test connectors on our PCB for either band; the module IPEX port is the test point.
> The 433 range compromise still stands (the FXP450 is still electrically small at 433 MHz).
> Board-level harmonic filtering is no longer an available mitigation — there is no board RF
> path to filter on. Coexistence, one-TX-at-a-time and the 4-layer call are unaffected.
> See [[12 - RF and Antenna Plan v0.1]] §3-§5 and *Radio modules LOCKED* at the end of this doc.

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

## TPS61023 NFC 5V PA boost — BETA ARCHITECTURE LOCKED (2026-07-31)

> **TPS61023 NFC BOOST: BETA ARCHITECTURE LOCKED.**

| Item | Value |
|---|---|
| Part | **Texas Instruments TPS61023DRLR** — adjustable synchronous boost |
| Package | **DRL, 6-pin SOT563 / SOT-5X3, 1.2 mm × 1.6 mm body** |
| Input | **`BQ25185_SYS`** |
| Output | **`NFC_5V_PA_PENDING`** |
| Enable | **`NFC_5V_EN`** from TCA9535 **U60 P02** |
| Load | **ST25R3916 `VDD_PA` ONLY** |

> **Do not substitute a generic SOT-23 footprint.** Verify the exact symbol pinout, the exact TI
> DRL package footprint, pin-1 orientation, exposed-pad status (if any), and the manufacturer
> land pattern.

**Do not connect** ST25R3916 `VDD_IO`, general 5V accessories, USB VBUS, or any unrelated board
load. **`VDD_IO` remains on `+3V3`** — that is what keeps SPI Bus B at 3.3 V with no level
shifter.

```
NFC 5V PA RAIL ONLY
ST25R3916 VDD_IO REMAINS +3V3
NOT A GENERAL-PURPOSE 5V RAIL
```

### Purpose and risk

Raises the ST25R3916 transmitter PA supply from the **Alpha-proven 3.3 V** configuration to
**~5 V** for improved NFC transmit range.

* NFC communication **was demonstrated on Alpha at 3.3 V**.
* The 5 V PA rail is expected to affect **range/performance**, not basic digital communication.
* **Exact rail current, ripple and RF-field performance require Beta bring-up validation.**

### Support network — values MUST come from TI, not from memory

> **Before wiring: inspect the current TPS61023 datasheet and EVM schematic. Record the exact FB
> resistor values, and the exact inductor and capacitor recommendations. DO NOT INVENT VALUES
> FROM MEMORY.**
>
> **The FB divider values for ~5.0 V are therefore recorded here as PENDING-FROM-DATASHEET.**
> They are deliberately not written down in this document, because writing a remembered number
> here would be indistinguishable from a verified one later. Take them from the TI 5 V
> reference/EVM design at capture time and record them then.

Expected topology:

```
BQ25185_SYS -> C_NFC_BOOST_IN -> L_NFC_BOOST -> TPS61023 SW/VIN network -> NFC_5V_PA_PENDING
```

| Element | Requirement |
|---|---|
| `C_NFC_BOOST_IN` | one input ceramic — value/voltage/dielectric **from TI** |
| `C_NFC_BOOST_OUT` | one output ceramic, **or the exact TI-recommended count** |
| `R_NFC_FB_TOP` / `R_NFC_FB_BOT` | FB divider for ~5.0 V — **exact values from the TI 5V reference/EVM** |
| `L_NFC_BOOST` | ~**1 µH**, **shielded**, **low DCR**, current rating **from the TI design calculation**. Exact MPN may stay provisional for pre-fab BOM validation |
| GND return | local, short, direct |
| Any mandatory TI support component | per datasheet |

Capacitor exact MPNs may be **deferred to the board-wide BOM validation**; record effective-
capacitance requirements and place a visible pre-fab derating note wherever MPNs are provisional.

```
PLACE INDUCTOR, INPUT CAPACITOR AND OUTPUT CAPACITOR
TIGHT TO TPS61023

MINIMIZE SW NODE COPPER AREA

KEEP FB TRACE AWAY FROM SW AND INDUCTOR

PROVIDE SHORT DIRECT GROUND RETURNS
```

### Enable safe state

`NFC_5V_EN` → TPS61023 EN. The architecture already specifies **`NFC_5V_EN` from U60 P02 with a
100k safe-state pull-down** (pin map §7: P02 power-up safe state = **OFF**).

**Verify the 100k pull-down exists and is electrically effective before the TCA9535 configures
its output** — the TCA9535 has no internal pulls, so that resistor is the only thing holding the
boost off during early boot. **Do not add a conflicting pull-up.**

Expected default: **EN low, `NFC_5V_PA_PENDING` off.** The TPS61023 provides **load
disconnection in shutdown**, so the PA rail should not remain back-powered through the boost
stage.

Test points: **`TP_NFC_5V_EN`**, **`TP_NFC_5V_PA`**.

```
DEFAULT OFF
ENABLE ONLY DURING NFC FIELD OPERATION
```

### Mandatory Beta bring-up checks

5 V output accuracy · startup when `NFC_5V_EN` asserts · clean shutdown · **no output when
disabled** · input current · **ripple during NFC field transmission** · TPS61023 and inductor
temperature · ST25R3916 `VDD_PA` current · **no backfeed into `+3V3` or `BQ25185_SYS`**.

---

## MAX17048 fuel gauge — BETA ARCHITECTURE LOCKED (2026-07-31)

| Item | Value |
|---|---|
| Preferred Beta part | **Analog Devices MAX17048G+T10** — single-cell ModelGauge |
| Package | 8-pin **2 mm × 2 mm TDFN / LFCSP-style** |
| Why the G package | easier Beta assembly and inspection than the **X** wafer-level package |
| Cell range | ~**2.5–4.5 V**, single cell |
| Sense resistor | **none required** |
| I²C address | **0x36**, 7-bit — **no address configuration** |

**Before capture:** verify the exact official pinout; verify the package drawing; verify the
KiCad symbol; assign the **exact manufacturer land-pattern footprint**; include the **exposed
pad** connection if the datasheet requires it. **Do not use a generic footprint without
comparing it to the current Analog Devices package drawing.** The part is recommended for new
designs.

### Power and cell connection — protected side only

> **Do not connect the MAX17048 to the raw battery-connector positive terminal.**

Because the reverse-polarity implementation is unresolved, the gauge sits on the
**protected/system side**:

| Pin | Net |
|---|---|
| `VDD` | **`BAT_PROTECTED_P`** |
| `CELL` | **`BAT_PROTECTED_P`**, or the exact recommended system-side battery-sense node |
| `GND` | system GND |

The datasheet allows system-side placement and includes battery-insertion debounce.

```
MAX17048 MUST REMAIN BEHIND FINAL REVERSE-POLARITY PROTECTION
DO NOT CONNECT TO RAW BATTERY CONNECTOR POSITIVE
```

When the final reverse-protection topology is selected, verify that: the gauge measures the
actual cell voltage with acceptable series-path error; charger and protection voltage drops do
not materially bias SOC estimation; the gauge remains protected during reversed insertion; and
battery-absent USB operation does not falsely power or damage it. **If the final protection
architecture needs a different sense point, flag `CELL` routing for the professional power
review.**

### Decoupling — from the ADI reference circuit

**`C_FG_VDD` = value from the current datasheet**, appropriate voltage rating, X7R, placed close
to the IC. Exact MPN may be deferred to pre-fab BOM validation.

> **Do not claim the circuit is "only one capacitor" until the official typical application has
> been checked for:** CELL filtering; VDD bypass; optional alert-network components; exposed-pad
> grounding.

Test point: **`TP_FG_CELL`**.

### I²C

`SDA` → **`I2C_SDA_INT`**, `SCL` → **`I2C_SCL_INT`**. **Do not add another pull-up pair** — the
internal bus already carries the locked 4.7k pull-ups.

```
MAX17048 I2C ADDRESS 0x36
NO ADDRESS CONFIGURATION
```

**Powered-off interaction — a real open question:** the MAX17048 stays **battery-powered when
the TPS63020 `+3V3` rail is off**, but the I²C pull-ups are on `+3V3` and go unpowered during
hard-off. **Verify from the MAX17048 datasheet that SDA/SCL cannot back-power the disabled
`+3V3` system.** Recorded as a **pre-fab power-domain review item**. **Do not add level shifting
unless primary documentation shows it is required.**

### Alert pin

Inspect the exact part pinout for the active-low alert output. **Preferred Beta treatment:
`ALRT_N` → test point, otherwise unused.** Use the datasheet-required pull-up only if needed to
observe it.

**Do not allocate a new ESP32 or TCA9535 input** unless an existing approved spare is explicitly
assigned — the native budget is zero-margin. If unused and permitted by the datasheet, leave it
unconnected with a no-connect marker and document that **firmware polls SOC over I²C**.
**Do not silently connect it to `WAKE_INT_N`.**

### Validation status

```
MAX17048 — NEVER BENCH VALIDATED ON AQROOT

BETA BRING-UP REQUIRED:
- I2C detection at 0x36
- cell-voltage accuracy
- SOC plausibility
- charge/discharge response
- hibernate entry/exit
- battery insertion/removal
- charger-connected behavior
- hard-off behavior
- no I2C backpower
- firmware temperature compensation
- low-battery threshold validation
```

**Do not write "cannot damage anything."** An incorrect connection to the raw or reversed
battery path could damage the gauge or create a backfeed path. The functional risk may be
described as low **only after correct protected-side placement is confirmed.**

---

## Physical hard-off switch → TPS63020 EN (2026-07-31)

### What it does, and what it does NOT do

```
PHYSICAL MAIN-RAIL HARD OFF

SWITCH OFF:
TPS63020 DISABLED
+3V3 SYSTEM RAIL OFF

UPSTREAM BATTERY CIRCUITS REMAIN POWERED:
BQ25185
MAX17048
REVERSE-PROTECTION CONTROLLER CANDIDATE

TOTAL BATTERY STANDBY IS NOT ZERO
```

**Describe it as `HARD-OFF FOR MAIN +3V3 SYSTEM RAIL`.** **Never** as "zero total battery draw."

**Do not claim:** complete battery isolation; shipping mode; zero battery current; zero standby
draw. Anything connected directly to `BAT_PROTECTED_P` or `BQ25185_SYS` stays powered unless
separately disconnected.

### Topology — SPST + 100k pull-down (chosen)

```
VINA -> [SPST maintained slide switch] -> EN
                                          |
                                   R_EN_PULLDOWN = 100k
                                          |
                                         GND
```

| Switch | EN | TPS63020 | `+3V3` |
|---|---|---|---|
| closed | high through the switch | on | active |
| open | pulled low by 100k | off | inactive |

**This avoids any direct VINA/GND contention** — chosen over the SPDT alternative (common→EN,
ON→VINA, OFF→GND, break-before-make) precisely because the SPST arrangement never switches GND
and can never short VINA to GND in any switch position or mid-travel.

* Optional small **test point on EN**.
* **No populated permanent 0R EN-to-VINA link** — see below.

**Do not connect the switch to:** ESP32 GPIO; TCA9535 GPIO; a firmware-controlled latch; battery
ground; or the raw battery current path.

### The superseded 0R link

`R_EN_LINK` = 0R (VINA→EN), previously specified as the populated default, **is withdrawn**. It
survives only as:

**`R_EN_BYPASS` = 0R, DNP** — VINA → EN, bench bypass only if the physical switch is unavailable.

```
DO NOT POPULATE R_EN_BYPASS WHEN HARD-OFF SWITCH IS FITTED
UNLESS INTENTIONAL ALWAYS-ON BENCH CONFIGURATION IS REQUIRED
```

### Switch part

**Exact MPN provisional until mechanical review, but the footprint must correspond to a real
candidate.** Requirements: SPST preferred (SPDT acceptable); **maintained** ON/OFF positions;
low-profile side or top actuator compatible with the Field Slate enclosure; current rating not
critical (drives EN only); mechanically robust; **real manufacturer footprint**; through-hole
mounting tabs acceptable and **preferred for mechanical strength**; accessible from the
enclosure side wall; clear OFF/ON orientation.

> **Do not assign a tiny signal-switch footprint without checking** actuator travel, body
> dimensions, mounting tabs, PCB edge setback, enclosure cutout, and hand-solder access.

```
SWITCH POSITION / ACTUATOR / ENCLOSURE CUTOUT
REQUIRE FIELD SLATE MECHANICAL REVIEW BEFORE ROUTING
```

### Production upgrade — explicitly not Beta

```
POST-KICKSTARTER OPTION:
SOFT PUSH-BUTTON POWER UX
LOAD SWITCH / LATCH / SHIPPING-MODE ARCHITECTURE
NOT PART OF BETA
```

---

## 01_POWER_TREE — Beta architecture complete except reverse polarity (2026-07-31)

> **Status: SPECIFIED, NOT DRAWN.** "Architecture complete" here means the design is settled in
> writing. `01_power_tree.kicad_sch` is still an empty stub — nothing below has been drawn in
> KiCad. **SPECIFIED** = written in Markdown; **CAPTURED** = actually drawn in the `.kicad_sch`.
> Never report one as the other.

```
01_POWER_TREE — BETA ARCHITECTURE COMPLETE

SPECIFIED (NOT YET DRAWN IN KICAD):
- USB-C 5V sink / USB 2.0 front end
- BQ25185 charger/power path
- TPS63020 main +3V3 buck-boost
- TPS61023 NFC 5V PA boost
- MAX17048 fuel gauge
- physical TPS63020 EN hard-off switch

OPEN PRE-FAB BLOCKER:
- reverse-polarity protection implementation

OTHER PRE-FAB VALIDATION:
- exact capacitor MPN / DC-bias checks
- connector and switch mechanical review
- power-domain backfeed review
- professional power / DFM review
```

> **The complete power tree is NOT fabrication-ready.** Architecture-complete and
> fabrication-ready are different gates — see the gate vocabulary below.

### Reverse-polarity placeholder — the only undrawn block

```
BAT_CONNECTOR_P
       |
[ REV-POLARITY PROTECTION PLACEHOLDER ]
       |
BAT_PROTECTED_P
```

`BAT_CONNECTOR_P` and `BAT_PROTECTED_P` **remain distinct nets**. Visible text:

```
REV-POLARITY:
LTC4368-1 CANDIDATE
+ BACK-TO-BACK N-CHANNEL MOSFETS

TOPOLOGY PENDING:
- LTSPICE CHARGE-PATH SIMULATION
- ADI FAE / VENDOR CONFIRMATION
- PROFESSIONAL POWER / DFM REVIEW

MANDATORY FAULT CASE:
REVERSED BATTERY WHILE USB POWERS BQ25185

DO NOT ROUTE
DO NOT RELEASE TO FAB
```

**Do not instantiate** a final controller, MOSFETs, sense resistor, UV/OV divider, gate clamp,
or timer components.

## USB-C 5V sink + USB 2.0 front end — BETA ARCHITECTURE LOCKED (2026-07-30)

> **USB-C FRONT END: BETA ARCHITECTURE LOCKED.**
>
> **ROLE: USB TYPE-C SINK / UFP. 5V ONLY. USB 2.0 FULL-SPEED DATA. NO USB POWER DELIVERY. NO
> SOURCE ROLE. NO DRP ROLE. NO VCONN. NO ALTERNATE MODES.**

**This is Beta-locked, not production-hardened.** It remains subject to professional
power/DFM/EMI review before fabrication.

**The two independent CC pull-downs are mandatory.**

### Connector

| Item | Value |
|---|---|
| Family | **GCT USB4105** — 16-contact USB 2.0 Type-C receptacle, top-mount horizontal, SMD contacts, through-hole shell stakes |
| Preferred Beta candidate | **GCT USB4105-GF-A-120** |
| KiCad footprint | `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` |

**Before assigning the MPN, verify:** the official drawing; that the **shell-stake length suits
the eventual PCB thickness**; the pin numbering against the KiCad symbol; and that the installed
KiCad footprint matches the manufacturer drawing. **The exact suffix is subject to
PCB-thickness / shell-stake confirmation.**

Required symbol pin mapping (16-contact USB 2.0 receptacle):

| Function | Contacts |
|---|---|
| VBUS | **A4, B9, A9, B4** |
| GND | **A1, A12, B1, B12** |
| D+ | **A6, B6** |
| D− | **A7, B7** |
| CC1 | **A5** |
| CC2 | **B5** |
| SBU1 / SBU2 | **A8 / B8 — no connect** |
| Shield | shield tabs → `USB_SHIELD` |

Verify all duplicate VBUS, GND, D+ and D− pins are electrically joined as intended.

> **A 16-contact USB 2.0 receptacle has NO SuperSpeed TX/RX contacts. Do not add invented
> SuperSpeed no-connect pins.** Mark only **SBU1** and **SBU2** as no-connect.

### CC sink identification — two independent Rd resistors

```
CC1 -> R_CC1_RD (5.1k, 1%) -> GND
CC2 -> R_CC2_RD (5.1k, 1%) -> GND
```

**Do not** combine CC1 and CC2; **do not** share one resistor; **do not** connect either CC pin
to firmware; **do not** add a PD or CC controller; **do not** connect VCONN.

```
TWO INDEPENDENT 5.1k Rd RESISTORS REQUIRED
USB-C SINK / UFP, 5V ONLY
NO PD NEGOTIATION
```

```
STATIC Rd ESTABLISHES THE SINK ROLE
NO CC CURRENT-ADVERTISEMENT DETECTION IS IMPLEMENTED
BQ25185 INPUT-CURRENT POLICY MUST NOT ASSUME 1.5A/3A
FROM AN UNKNOWN SOURCE
```

### VBUS power path

```
USB connector VBUS pins
        |
   USB_VBUS_RAW
        |
   R_USB_VBUS_LINK (0R, optional current-measurement / link footprint)
        |
   USB_VBUS_CHG
        |
   BQ25185 VIN
```

The 0R link exists for **bring-up current measurement**, **charger-input isolation**, and
**later replacement by an input protection component** if required.

> **Do not route USB VBUS through the USBLC6-2SC6 as though the ESD device were a series pass
> component.** Its VBUS pin connects as a **branch** to `USB_VBUS_RAW` (or the connector-side
> protected VBUS node) per the ST application circuit.

```
USBLC6 VBUS PIN IS A CLAMP REFERENCE
NOT A SERIES POWER PATH
```

**`C_USB_VBUS` = 4.7 µF, 10 V minimum, X7R.** Effective-capacitance MPN verification is
**deferred to pre-fab BOM validation**. **4.7 µF is preferred over automatically using 10 µF**
so connector-side input capacitance and hot-plug behaviour stay conservative. Place it close to
the receptacle/VBUS entry, the USBLC6 VBUS reference, and the charger-input path.

**The BQ25185's own required local VIN decoupling is separate** and is captured with the
charger's support network. **This connector-side capacitor does not replace the charger
datasheet capacitor.**

### USB 2.0 data path

MCU nets are already defined in the locked pin map (§ *Final native allocation*, GPIO 19/20 =
native USB, reserved):

| Net | Pin |
|---|---|
| `USB_D_N_MCU` | **ESP32-S3 GPIO19 = D−** |
| `USB_D_P_MCU` | **ESP32-S3 GPIO20 = D+** |

```
Connector D- pins (A7,B7) -> USB_D_N_CONN -> USBLC6 protected channel -> R_USB_DN_SER (22R) -> USB_D_N_MCU / GPIO19
Connector D+ pins (A6,B6) -> USB_D_P_CONN -> USBLC6 protected channel -> R_USB_DP_SER (22R) -> USB_D_P_MCU / GPIO20
```

* `R_USB_DN_SER` = `R_USB_DP_SER` = **22R initial**, equal values, matching footprints.
* A **33R assembly option** is acceptable after signal-integrity review — **but never mix 22R
  and 33R across the pair.**
* **Place the series resistors close to the ESP32-S3, not close to the connector.**
* **Do not cross D+ and D−.** Confirm **GPIO19 = D−**, **GPIO20 = D+**.

### ESD array

**STMicroelectronics USBLC6-2SC6**, SOT-23-6 / SOT23-6L. Use the **exact official pinout** and
a footprint matching the SC6 package.

* Two protected channels assigned consistently to D+ and D−.
* GND directly to the ground plane.
* VBUS clamp/reference pin to `USB_VBUS_RAW` — **not in series**.
* **Place physically very close to the USB connector.**

> **Verify the chosen symbol's pin numbering against the ST datasheet. Do not trust a generic
> six-pin ESD symbol unchecked.**

```
ESD CURRENT PATH TO GND MUST BE SHORT AND DIRECT
PLACE ESD BEFORE LONG DATA TRACES
MINIMIZE STUB BETWEEN CONNECTOR AND ESD ARRAY
```

### Optional EMC capacitors — DNP for Beta

`C_USB_DP_EMC` = 100 pF **DNP**, `USB_D_P_MCU`-side node → GND.
`C_USB_DN_EMC` = 100 pF **DNP**, `USB_D_N_MCU`-side node → GND.

Place close to the MCU-side series resistors.

```
DNP FOR BETA
POPULATE ONLY AFTER SIGNAL-INTEGRITY / EMI REVIEW
```

**Do not populate by default. Do not silently replace them with larger values.**

### Connector shield

Distinct net **`USB_SHIELD`**; all shield tabs connect to it.

| Option | Value | Beta default |
|---|---|---|
| `R_USB_SHIELD_LINK` | **0R** | **populated** |
| `R_USB_SHIELD_BLEED` | 1M | **DNP** |

**Do not populate both simultaneously unless explicitly reviewed.** A single resistor footprint
may be used instead, with the fitted value documented as 0R and 1M retained only as an assembly
experiment. An **optional DNP small capacitor footprint** from `USB_SHIELD` to GND may be added
for later EMI review **only if board space permits** — no mandatory value at this stage.

```
SHIELD-GROUND STRATEGY PROVISIONAL FOR EMI/ESD REVIEW
DEFAULT BETA LINK: 0R
DO NOT LEAVE SHIELD FLOATING WITHOUT REVIEW
```

Keep shield return placement close to the connector.

### USB current-capability note — the important one

```
USB-C Rd RESISTORS CAUSE A SOURCE TO PRESENT 5V,
BUT THIS DESIGN DOES NOT MEASURE THE SOURCE'S
DEFAULT / 1.5A / 3A CURRENT ADVERTISEMENT.

GENERIC-PORT OPERATION MUST USE A CONSERVATIVE
BQ25185 INPUT-CURRENT LIMIT.

HIGHER INPUT CURRENT REQUIRES A KNOWN CAPABLE
USB-C SOURCE OR FUTURE CC CURRENT-DETECTION LOGIC.
```

**Do not claim USB-PD support.** **Do not claim universal 1 A USB input compliance merely
because the charger supports 1 A battery charge current** — the **charger-input-current setting
and the battery-charge-current setting are separate design decisions.**

### PCB layout notes

**D+/D−:** route as a **90 Ω differential pair** (tolerance appropriate to the stack-up);
equal-length; continuous GND reference plane; minimise vias; no stubs; avoid switch nodes,
inductors, antennas and crystal traces; preserve pair spacing; add **paired ground-return vias**
if a layer transition is unavoidable.

**Placement order:** 1. connector → 2. USBLC6-2SC6 → 3. controlled differential routing →
4. series resistors near ESP32-S3 → 5. ESP32-S3 USB pins.

**VBUS:** suitable width for expected input current; keep the connector bulk capacitor and ESD
clamp close; keep away from D+/D− where practical.

### ERC checks for this block

**Do not globally weaken ERC.** Verify: CC1 has its own 5.1k; CC2 has its own 5.1k; CC1 and CC2
are not shorted; D+ is not swapped with D−; **GPIO20 receives D+**; **GPIO19 receives D−**;
USBLC6 VBUS is not treated as series power; SBU1/SBU2 carry no-connect markers; all connector
VBUS pins are joined; all connector GND pins are joined; the shield is not accidentally used as
signal GND through an unintended duplicate path; **no nonexistent SuperSpeed pins were added**;
no PD controller was added; **no GPIO was allocated for CC logic.**

### Status summary

| Gate | State |
|---|---|
| **Architecture lock** | ✅ Beta-locked |
| **Schematic-capture approval** | ✅ Approved |
| **Exact BOM lock** | ❌ Connector suffix, ESD array and capacitor MPNs — stock/lifecycle rechecked at pre-fab BOM validation |
| **Fabrication-release approval** | ❌ Blocked — needs BOM lock **plus** professional power/DFM/**EMI** review (shield-ground strategy especially) |

## TPS63020 3.3V regulator block — ARCHITECTURE LOCKED, capture approved (2026-07-30)

> **TPS63020 3.3V REGULATOR: ARCHITECTURE LOCKED. SCHEMATIC CAPTURE APPROVED. CAPACITOR EXACT
> MPNs DEFERRED TO PRE-FAB BOM VALIDATION.**

**This supersedes the "not selected until its inductor, feedback resistors and caps are
selected with it" caveat** recorded in the regulator section above and in
[[11 - Beta Pin Map v0.2]] §8. The inductor and every resistor are now locked; the capacitor
*values, voltages, dielectrics and packages* are locked; only the exact capacitor **MPNs**
remain open.

**Exact capacitor verification is a BOM-RELEASE gate, not a schematic-capture gate.** Do not
block schematic progress on per-capacitor DC-bias research. Batch all exact capacitor MPN,
DC-bias, lifecycle and stock checks into **one board-wide BOM-validation pass before
fabrication**, alongside the professional power/DFM review that also owns the
[reverse-polarity lock](#reverse-polarity-protection--parked-topology-not-locked-2026-07-30).

### The four distinct gates — do not conflate them

| Gate | State for this block |
|---|---|
| **Architecture lock** | ✅ **DONE** — topology, part, inductor, feedback, EN/PS/PG strategy all fixed |
| **Schematic-capture approval** | ✅ **APPROVED** — `01_POWER_TREE` may draw this block in full |
| **Exact BOM lock** | ❌ **OPEN** — capacitor MPNs pending the board-wide validation pass |
| **Fabrication-release approval** | ❌ **BLOCKED** — needs the BOM lock *and* the power/DFM review |

### Regulator — locked

| Item | Value |
|---|---|
| Part | **Texas Instruments TPS63020DSJR** |
| Package | DSJ — use the correct KiCad symbol and footprint for DSJ |
| Input rail | **`BQ25185_SYS`** |
| Output rail | **`+3V3`** |
| Ground | Per the TI datasheet's own PGND/AGND treatment. **Do not invent split-ground nets unless the datasheet explicitly requires them.** |

**Verify the official TI pinout before wiring.** Do not take a pinout from a third-party
library without checking it against the datasheet — the same provenance rule the symbol library
already applies to every other part.

Block title to place on the sheet:

```
TPS63020 3.3V BUCK-BOOST
ARCHITECTURE LOCKED
CAPACITOR MPNs PENDING PRE-FAB BOM VALIDATION
```

### L1 inductor — LOCKED

| Item | Value |
|---|---|
| Part | **Coilcraft XFL4020-152MEC** |
| Inductance | **1.5 µH ±20%** |
| LCSC | **C3033018** |
| DCR | ~**14.4 mΩ** typical, ~**15.8 mΩ** maximum |
| Isat (10% / 20% / 30% L loss) | ~**4.1 A** / ~**4.4 A** / ~**4.6 A** |
| Max body height | ~**2.1 mm** |
| Construction | Shielded, molded |

Use the exact manufacturer-recommended footprint if available; otherwise use or create one that
matches the **official Coilcraft land pattern**.

Note to place beside L1:

```
LOCKED MPN: XFL4020-152MEC
XGL4020-152 MAY BE REVIEWED AS AN APPROVED ALTERNATE
DO NOT SILENTLY SUBSTITUTE
```

**XGL4020-152 is not the installed part** and must not be listed as such.

### Feedback network — LOCKED

Two-resistor divider **only**:

```
+3V3 / VOUT
    |
R_FB_TOP = 1M, 1%
    |
   FB
    |
R_FB_BOTTOM = 180k, 1%
    |
   GND
```

* Reference/value naming is explicit: **`R_FB_TOP`**, **`R_FB_BOTTOM`**.
* **No Cff. No third feedback resistor.**
* Keep the FB node compact and visually separate from switching nodes on the sheet.

Layout note to place on the sheet:

```
KEEP FB TRACE SHORT
ROUTE AWAY FROM L1, L1/L2 SWITCH NODES AND HIGH-DI/DT LOOPS
SENSE VOUT AFTER OUTPUT CAPACITORS
```

### Power-good — LOCKED

PG is **open-drain**.

```
+3V3
  |
R_PG_PULLUP = 1M
  |
 PG
```

* **PG test point** present.
* **No MCU connection. No expander connection. No GPIO allocated.**

```
PG DIAGNOSTIC ONLY
NO GPIO ALLOCATED
```

### EN — CONTROLLED BY THE PHYSICAL HARD-OFF SWITCH

> **SUPERSEDED 2026-07-31.** This block previously specified a **permanently populated
> `R_EN_LINK` = 0R from VINA to EN ("always-on default")**. That is **withdrawn**. A physical
> hard-off switch now drives EN, and a populated permanent 0R link in parallel with a switch
> that pulls EN low would **defeat the OFF position and create a VINA-to-GND short**. See
> [Physical hard-off switch](#physical-hard-off-switch--tps63020-en-2026-07-31).

**EN must not float.** Current topology:

```
VINA -> [SPST maintained slide switch] -> EN
                                          |
                                   R_EN_PULLDOWN = 100k
                                          |
                                         GND
```

* The **permanent always-on link is removed**. It survives only as
  **`R_EN_BYPASS` = 0R, DNP** (VINA → EN), a bench-bypass option.
* **EN test point** present.
* **Do not connect EN to the ESP32, the TCA9535, or any firmware-controlled signal.**

```
DO NOT POPULATE R_EN_BYPASS WHEN HARD-OFF SWITCH IS FITTED
UNLESS INTENTIONAL ALWAYS-ON BENCH CONFIGURATION IS REQUIRED
```

```
MCU CANNOT RESTORE ITS OWN DISABLED 3V3 RAIL
```

That last line is still the reason firmware never touches EN: a rail the MCU can switch off is
a rail the MCU cannot switch back on. The switch is deliberately *physical* for the same reason.

### PS/SYNC — LOCKED DEFAULT (power-save)

```
PS/SYNC
   |
R_PS_DEFAULT = 0R
   |
  GND
```

* Selects **power-save operation by default**.
* Test point or solder-jumper/DNP option allowing a future tie to VINA for **forced-PWM or EMI
  testing**. **No GPIO allocation.**
* **Avoid any configuration where the GND link and a VINA link can both be populated without an
  explicit assembly warning** — that would short VINA to GND.

```
DEFAULT: POWER-SAVE MODE
FORCED PWM OPTION FOR BRING-UP / EMI TESTING ONLY
```

### VINA decoupling — LOCKED

**`C_VINA` = 100 nF, X7R, VINA to GND**, placed close to VINA.

```
C_VINA = 100nF
DO NOT EXCEED 220nF WITHOUT REVIEW
```

### Input capacitors — VALUE LOCKED, MPN PENDING

**`CIN1` = 10 µF, `CIN2` = 10 µF.**

| Requirement | Value |
|---|---|
| Voltage rating | **10 V minimum** |
| Dielectric | **X7R** |
| Exact MPN | **Pending** — must be active-lifecycle |
| Combined effective CIN | **≥ 10 µF at ~4.5 V** |
| Each capacitor after derating | **≥ ~5 µF at 4.5 V** |

> **The obsolete Murata `GRM21BR71A106KE51L` must NOT be used** and must not be assigned to
> either capacitor.

Provisional footprint: **1206 preferred**; 0805 only if the eventual MPN can meet the derating
requirement. **Prefer 1206 unless a mechanical constraint strongly favours 0805.**

```
CIN MPN NOT BOM-LOCKED
REQUIRE COMBINED EFFECTIVE CIN >=10uF AT 4.5V
VERIFY DC-BIAS / LIFECYCLE / STOCK BEFORE FAB
```

Place both close to VIN and PGND per TI layout guidance.

### Output capacitors — VALUE/PACKAGE LOCKED, MPN PROVISIONAL

**`COUT1`–`COUT4` = 22 µF each.**

| Requirement | Value |
|---|---|
| Voltage rating | **10 V** |
| Dielectric | **X7R** |
| Package | **1206** |
| Provisional MPN | **Murata GRM31CR71A226ME15L** — *provisional, not BOM-locked* |
| Combined effective COUT | **≥ 40 µF at 3.3 V** |
| Each part | must retain an average of **≥ 10 µF** under the documented acceptance assumptions |

```
COUT MPN PROVISIONAL
REQUIRE COMBINED EFFECTIVE COUT >=40uF AT 3.3V
VERIFY MURATA DC-BIAS DATA BEFORE FAB
```

Place tightly around VOUT and PGND per TI layout guidance.

### Required visible warning beside the block

```
CAPACITOR MPNs NOT BOM-LOCKED
VERIFY DC-BIAS EFFECTIVE CIN/COUT BEFORE FAB

CIN:
2 x 10uF, 10V+, X7R
TOTAL EFFECTIVE >=10uF AT 4.5V

COUT:
4 x 22uF, 10V, X7R, 1206
TOTAL EFFECTIVE >=40uF AT 3.3V

DO NOT USE OBSOLETE GRM21BR71A106KE51L
```

### Battery-input side — unchanged

The TPS63020 block connects to **`BQ25185_SYS`**, *not* to the raw battery connector. The
battery-input area remains the
[parked reverse-polarity placeholder](#reverse-polarity-protection--parked-topology-not-locked-2026-07-30)
and **must not** be drawn as a finalised circuit.

### ERC handling for this sheet

**Do not globally reduce ERC severity.** If the incomplete reverse-polarity block or the future
hard-off DNP landing generates findings: classify them explicitly, and use a **narrowly scoped**
no-connect, no-ERC marker or documented waiver **only where justified**. Never suppress
unrelated errors.

Verify on this block specifically:

- [ ] EN is not floating
- [ ] PS/SYNC is not floating
- [ ] PG open-drain has its pull-up
- [ ] FB connects only to the intended divider
- [ ] No obsolete capacitor MPN appears anywhere
- [ ] No GPIO was consumed
- [ ] The `+3V3` power-flag strategy matches the project's existing conventions

---

## Pre-fabrication BOM-validation pass — what it must archive (2026-07-30)

**One board-wide pass, run before fabrication, alongside the professional power/DFM review.**
Batching this is deliberate: per-part DC-bias research done piecemeal during capture stalls the
schematic and gets redone anyway when stock moves.

**For every exact capacitor MPN, archive:**

| Item |
|---|
| Manufacturer datasheet permalink |
| Manufacturer DC-bias curve, model, CSV or numerical output |
| Operating voltage |
| Nominal capacitance |
| **Effective** capacitance at operating voltage |
| Tolerance calculation |
| Temperature assumption |
| **Total** effective capacitance calculation |
| Lifecycle status |
| Distributor / LCSC / JLCPCB code |
| Stock-check date |
| Explicit note to **recheck stock at BOM release** |

**For the inductor, archive:**

| Item |
|---|
| Manufacturer datasheet |
| Official footprint / land pattern |
| DCR typical **and** maximum |
| Isat definition at **10%, 20% and 30%** inductance loss |
| Irms thermal-rise definition |
| Height |
| Lifecycle status |
| LCSC mapping |
| Stock-check date |

### Gate vocabulary — keep these four distinct

| Gate | Means |
|---|---|
| **Architecture lock** | The topology and the parts that define the loop are fixed. Schematic can proceed. |
| **Schematic-capture approval** | This block may be drawn now, with its open items marked on the sheet. |
| **Exact BOM lock** | Every MPN is chosen, derated, lifecycle-checked and stock-checked. |
| **Fabrication-release approval** | BOM lock **plus** the power/DFM review **plus** the reverse-polarity topology lock. |

A block can be architecture-locked and capture-approved while still being nowhere near
fabrication-release. The TPS63020 block is exactly that today.

## Reverse-polarity protection — PARKED, topology NOT locked (2026-07-30)

**Status: architecture defined, implementation unresolved, final lock delegated.** This is a
deliberate park, not an oversight. The requirement above is unchanged and still mandatory; what
follows records exactly how far the decision has been taken and where it stops.

### Why this is parked rather than decided

The remaining open question — **does normal ~1 A charging current flowing VOUT→VIN trip the
controller's reverse-current sense?** — needs an **LTspice model of the LTC4368 charge-path
case**, and most likely an **ADI FAE confirmation** on top of it. That is specialist analog
work, best done **once, properly, by the power review**, rather than iterated at in an AI-chat
loop where the answer cannot actually be validated.

It occupies **one corner of the power tree**, and it **must not stall the rest of the board**.
Everything else in `01_POWER_TREE` proceeds normally.

### Architecture — decided

| Item | State |
|---|---|
| Topology class | **High-side only** |
| Battery negative | **Remains tied directly to system GND — LOCKED.** Not switched, not sensed in the return path. |
| Keyed connector + tray geometry | **Additional mechanical layer only, NEVER the primary electrical defence.** The electrical protection must stand on its own with a reversed cell physically inserted. |
| Leading candidate | **Analog Devices LTC4368-1** controlling **back-to-back N-channel MOSFETs** |
| External MOSFET class considered | **AO3400A-class low-voltage NFETs**, two in series |

### Leading candidate — detail (NOT locked)

**Controller — Analog Devices LTC4368-1**, active back-to-back N-FET controller:

| Parameter | Value |
|---|---|
| Input range | ~2.5–60 V |
| Quiescent current | ~80 µA |
| Forward / reverse sense threshold | ~±50 mV |
| Package | MSOP or 3×3 DFN |

The reason it is the leading candidate is **active gate turn-off**: it drives the gates down
hard rather than relying on a passive network, which is what avoids the **AN-171 partially-on
thermal-runaway equilibrium**.

**External FETs — back-to-back N-channel, AO3400A-class, two in series:**

| Parameter | Value |
|---|---|
| Part | AOS **AO3400A** |
| LCSC | **C20917** |
| Package | SOT-23 |
| V(DS) | 30 V |
| R(DS,on) | ~48 mΩ @ V(GS) = 2.5 V |
| V(GS) max | ±12 V |

**Building-block PMOS — AO3401A (LCSC C15127) remains valid** *if a PMOS variant is chosen
instead*. Note the distinction carefully: **a single PMOS alone is rejected as a final
solution**, but the part itself is not blacklisted and stays available as a building block
should the review land on a PMOS-based topology.

### Not selected — every one of these is open

Exact MOSFET, sense resistor, UV/OV divider, timer/inrush parts, gate clamp, and package.
**No part number in any of these roles is final.**

The battery connector side, the protected BAT rail, and the **BQ25185 BAT path remain
architecturally defined** — the block's boundaries and its place in the power tree are settled.
**The protection implementation inside those boundaries is unresolved.**

### Rejected as final solutions — recorded so they are not revisited

| Rejected | Why it fails |
|---|---|
| **Single PMOS alone** | Does not survive the mandatory fault case. *(The AO3401A part itself stays valid as a building block — see above.)* |
| **Naive passive back-to-back** | No active turn-off. |
| **Any passive gate network that can leave a FET partially-on under charger drive** | This is precisely the AN-171 failure mode. |
| **Low-side protection** | Architecture is high-side only; battery negative stays tied to system GND. |
| **Keyed connector as primary defence** | Mechanical layer only. Must not be load-bearing electrically. |
| **Ordinary load switches that block charging** | The battery path is bidirectional — charge flows *through* this block. |
| **Cell over/under-voltage protectors** | They do not address **physical reverse insertion**, which is the actual failure that destroyed a board. |

### REQUIREMENT — locked, regardless of final topology

This survives whatever the review picks. The design is not acceptable unless it survives the
case that destroyed a board on the bench, made worse by the charger being live:

> **Reversed battery while USB powers the BQ25185.**

Required behaviour:

* **Both pass FETs remain fully off.** Not partially enhanced — off.
* **Block sustained current into the reversed cell.**
* **Keep the BQ25185 `BAT` pin above its ~−0.3 V absolute maximum.**
* **Avoid any Analog Devices AN-171 linear-equilibrium self-heating.** A FET that settles into
  a partially-on operating point can sit in a self-sustaining thermal equilibrium and destroy
  itself and the cell. Proving this cannot happen is part of the gate, not a nice-to-have.
* **The keyed connector is an additional mechanical layer only — never the primary electrical
  defence.**

### STATUS: PENDING — the open engineering questions

None of these has an answer yet. They are the reason the topology is not locked, and they are
**assigned to the professional power/DFM review (pre-fab gate)**:

| # | Open question |
|---|---|
| **(a)** | **LTspice validation of the 1 A charge-path / reverse-sense question** — does normal ~1 A charging current flowing VOUT→VIN trip the reverse-current sense? Also: does the LTC4368-1 support a *removable* 1-cell charger path at all? |
| **(b)** | **ADI vendor / FAE confirmation** of the intended use. |
| **(c)** | **UV/OV divider values for 3.0–4.2 V.** |
| **(d)** | **Sense-resistor value vs charge current.** |
| **(e)** | **V(GS)-clamp need vs the ±12 V FETs.** |
| **(f)** | **Standby-current impact of the ~80 µA controller** — see [[13 - Power Budget and Battery Runtime v0.1]]. |

Further open items in the same gate: negative-input behaviour while the output is
charger-powered; startup and hot-insertion behaviour; BQ25185 battery detection, charge
termination and recharge interaction; voltage drop and thermal performance.

**(a), (b) and the negative-input question are the ones most likely to invalidate the LTC4368-1
candidate outright** — the part is aimed at a supply-input position, and AQROOT is asking it to
sit in a bidirectional battery path that is charged *through* it.

### Ownership — who closes this

**Final topology lock belongs to the professional power/DFM pre-fabrication review.** Not to
schematic capture, not to this log, not to a bench guess.

That review **must**:

* run the **LTC4368 LTspice case**, covering the mandatory fault case above; and
* obtain **Analog Devices vendor/FAE confirmation** of the intended use, specifically on
  questions 1, 2 and 5.

> **GATE: do not allow PCB routing or fabrication release until this is closed.** This blocks
> the board, not just the power sheet.

### KiCad capture instruction

**`01_POWER_TREE` may be captured except for this implementation.** The rest of the power tree
is not blocked by this park.

**Every section EXCEPT the battery-input protection block is drawn normally.** The protection
block must remain a clearly labelled **functional placeholder**, carrying exactly this text:

```
REV-POLARITY: LTC4368-1 + BACK-TO-BACK NFETS (LEADING CANDIDATE)
TOPOLOGY PENDING SIM / VENDOR REVIEW
DO NOT ROUTE
```

Same discipline as the radio and NFC placeholders: no footprint, nothing routable, and the open
question stated on the sheet where it cannot be missed.

### Beta validation test card — PRESERVED IN FULL

Fourteen cases. **This card runs at Beta bring-up regardless of the final topology** — it is
the acceptance test for whatever the review locks, and a different topology does not shorten
it:

| # | Case |
|---|---|
| 1 | Correct battery, USB absent |
| 2 | Correct battery, USB present |
| 3 | **Reversed battery, USB absent** |
| 4 | **Reversed battery, USB present** — *the mandatory fault case* |
| 5 | Battery absent, USB present |
| 6 | Hot insertion |
| 7 | Repeated reversal |
| 8 | 640 mA discharge *(charge + discharge through the protection)* |
| 9 | 1 A charging *(charge through the protection — the case behind open question (a))* |
| 10 | Charge termination |
| 11 | Recharge behaviour |
| 12 | Sleep leakage *(includes the ~80 µA controller — open question (f))* |
| 13 | Voltage drop |
| 14 | Protection-device temperature |

Inrush is covered by cases 6 and 9.

### Initial validation — current-limited, simulator first

**Use a battery simulator before a real LiPo.** A reversed real cell has no current limit and
will happily deliver whatever a partially-on FET asks for.

| Setting | Value |
|---|---|
| USB current limit | **50 mA** |
| Battery-simulator current limit | **25–50 mA** |

**Measure at:** the battery connector, `BAT_PROTECTED_P` / BQ25185 `BAT`, the common gate node,
`SYS`, and battery-path current.

**Abort immediately on any of:**

* `BAT` below **−0.3 V**
* sustained reversed-cell current above **10 mA**
* **gate plateau** (the AN-171 partially-on signature)
* **rapid heating**
* **oscillation**
* **unstable `BAT` or `SYS`**

### BOM position

No final reverse-protection part number is claimed. The candidate controller and the candidate
NFET class are listed as **provisional only** — see [[06 - BOM and Cost Tracker]].

## Audio parts: ICS-43434 mic + MAX98357A amp
Selected the I2S audio parts (were "planned, unspecified"):
- Speaker amp: MAX98357A - I2S Class-D mono amp, all-in-one (I2S in -> amplified speaker out,
  no separate DAC). Up to 3.2W into 4ohm (far more than needed; run below max). 2.7-5.5V,
  efficient Class-D. Has a SHUTDOWN/mode pin -> power-gate the amp when audio idle (goes on
  the internal expander as a slow enable: `AMP_SD_MODE` on **U60 P03**). Gain pin-settable
  (3-15dB). No I2C config needed.
- Microphone: ICS-43434 - I2S MEMS mic. IMPORTANT: chosen over the popular INMP441 because
  the INMP441 is DISCONTINUED / not recommended for new designs. The ICS-43434 is the
  current-gen InvenSense replacement (drop-in, better power + audio). Picking the
  in-production part now avoids a production sourcing surprise.
- Speaker: small 4ohm or 8ohm, ~1-2W; exact speaker chosen at enclosure CAD time (size +
  acoustic mounting depend on the shell).
- Shares the reserved I2S pins (BCLK=39, LRCLK=40, DOUT=41 speaker, DIN=42 mic).
- STILL NEEDS BENCH VALIDATION (audio is the one untested subsystem). Buy ICS-43434 +
  MAX98357A breakouts (~$5-8 each) to validate on the Alpha board when ready.
- Expander addition: MAX98357A SD/shutdown (+ optional gain) pin(s) on the internal expander —
  `AMP_SD_MODE`, **U60 P03** (TCA9535PWR @ 0x20), with an external pull holding it in SHUTDOWN
  until firmware says otherwise.

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
- MCP23017 I2C GPIO expander (0x20) - designed into Beta at the time, not yet bench-tested
  > **SUPERSEDED 2026-07-27: the MCP23017 is no longer the design part.** The Beta expanders are
  > TI TCA9535PWR (U60/U61). This purchase is a sunk Alpha cost; the board remains useful for
  > general I2C-architecture work but validates nothing about the TCA9535.
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
> - MCP23017 expander *(no longer the design part as of 2026-07-27 — see above)*
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

> **CORRECTED 2026-07-27 — "on fully-validated parts" no longer holds.** All five bench tests
> above did pass, but the expander one tested an **MCP23017**, which is no longer the design
> part. The Beta expanders are **TI TCA9535PWR (U60/U61), datasheet-trusted and never
> bench-tested.** Schematic capture remains cleared to proceed; the claim that every Beta part
> is bench-validated is retired. Two Beta parts now await first hardware confirmation: the
> ICS-43434 mic (dead Alpha unit) and both TCA9535PWR expanders (never powered on).

## PRE-SCHEMATIC DESIGN REVIEW — corrections + decisions (2026-07-26)

Applied immediately before KiCad schematic capture. Source: pre-schematic design review.
Full detail in [[11 - Beta Pin Map v0.2]] (now revision v0.2.1).

> **HISTORICAL ENTRY — the expander part described below is NO LONGER IN THE DESIGN.** This
> section records the 2026-07-26 pre-schematic review using the part and pin names current at
> the time. **The expander is now the TI TCA9535PWR (U60/U61)** — see the 2026-07-27 part-change
> decision above. Every `GPAn`/`GPBn` name, `INTA`/`INTB` reference, and MCP23017 register or
> interrupt-on-change assumption below is **dead nomenclature**; the authoritative maps are
> [[11 - Beta Pin Map v0.2]] §7a/§7b and the register set is §7c. Read this for *why* decisions
> were made, never for *what the pins are called*.

**Factual errors corrected:**
1. **Expander pin count.** The repo claimed the expander had "14 bidirectional + 2 output-only
   pins". The review concluded that was wrong and that all 16 were fully bidirectional, then
   recalculated every pin budget on that basis - including the "~7 slow GPIO" community-header
   figure, which was downstream of the error.
   > **CORRECTED AGAIN (2026-07-27): this correction was itself wrong.** Current MCP23017 I2C
   > silicon *does* have output-only GPA7/GPB7 limitations. Rather than re-litigate which pins are
   > crippled, the part was changed to the **TI TCA9535PWR**, which genuinely has 16 bidirectional
   > I/O. The recalculated budgets survive intact because the new part supplies the 16 usable pins
   > the budgets assumed. See the part-change decision above.
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
   internal expander (reset is a slow signal; the doc already inconsistently had touch RESET on
   an expander pin).
   Two separate expander pins, not one shared, for sequencing flexibility. The FT6236 still
   requires a CTP_RST low->high pulse to enumerate - that pulse now comes from the expander,
   so the boot order is: I2C up -> configure expander -> pulse touch RST -> init touch.
5. **GPIO3 / BMI270 INT1 strap caution.** SX1262 RESET stays on the internal expander
   (`SX1262_RST_N`, now U60 P01); BMI270 INT1 stays native on GPIO3. Because GPIO3 is a strapping pin and the IMU can assert INT1 during
   the reset window, the boot state must be designed: configure INT1 open-drain if the mode
   allows, add a weak pull setting the correct strap level, add a 100-470R series resistor,
   add a test pad, and **validate 50-100 cold boots with motion applied during reset** before
   freezing. Fallback if it fails: drop native motion-wake, poll the IMU, free GPIO3.
6. **Second expander at 0x21** for the community expansion header (16 low-speed GPIO,
   XGPIO0..15). The internal expander (0x20) now carries the button cluster plus all internal
   control signals on the other port - **exactly 16 pins, completely full**. The two-port split
   was chosen partly to make the button interrupt output a pure button interrupt. Casualty: the
   old "display power/control reserve" pin is gone, and no D-pad centre/select fits.
   > *(2026-07-27: the button count was corrected to 7 later in this log, and the
   > "pure button interrupt" rationale is now **VOID** — the TCA9535PWR has a single `/INT` per
   > device covering both ports. The port split is kept for readability only.)*
   - **BUTTON WAKE:** a polled expander CANNOT wake the ESP32 from sleep. The internal
     expander's interrupt output is routed (open-drain, wired-OR with 0x21) to a native
     wake-capable pin so buttons can wake the device. Without this the ~2-week standby figure is
     unreachable. *(Now the `WAKE_INT_N` net -> GPIO21.)*
   - **PHYSICAL POWER SWITCH stays OUT of the expander architecture** - it needs a real
     hard-off / load-switch / charger ship-mode path, not a firmware GPIO.
   - **POWER-UP SAFE STATE:** expander pins default to INPUTS (high-Z) until firmware sets the
     direction registers. Every safety-relevant enable (load switches, amp shutdown, NFC boost
     enable, resets) needs an **external pull resistor forcing the safe state**. Do NOT rely on
     "firmware writes it low quickly" - a hung or half-flashed firmware makes that high-Z
     window permanent. *(2026-07-27: still true on the TCA9535, and now stricter — that part has
     no internal pull-ups at all, and firmware must also write safe output latches before
     changing direction. See the part-change decision above.)*
7. **External I2C isolation (required).** The community header must NOT expose the internal
   I2C bus naked: 22-47R series resistors near the host, ESD protection at the connector,
   optional solder-jumper external pull-ups, a bus buffer/isolator or bus switch, and a
   firmware/hardware way to disconnect a defective accessory. **A community accessory that
   shorts SDA/SCL must not disable the internal touch/IMU/fuel-gauge/controls or make AQROOT
   unbootable.** Reserved I2C address table to publish for accessory makers: **0x20, 0x21,
   0x36, 0x38, 0x68** (and note the I2C-expander families — TCA9535, PCA9535/9555, MCP23017 —
   all occupy 0x20-0x27).
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

### 2. Accessory-power enable — ACC_PWR_EN on the 0x21 expander's 16th pin (now U61 P17); header publishes XGPIO0-14

Option (a) of the three logged during the review. The second expander (0x21 — now **U61**)
reserves its 16th pin (**P17**) as **ACC_PWR_EN**, driving the load switch on the community
header's accessory power rail. **The user-facing header is XGPIO0-14 = 15 low-speed user GPIO.**

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

Final cluster on the internal expander's input port (**U60 P10-P16**): **D-pad UP / DOWN /
LEFT / RIGHT, A (=select), B (=back), HOME** = **7 buttons**.

- **No separate D-pad centre/select button.** A *is* select, so a centre press would be a
  duplicate control competing with A for the same job - added cost and an extra failure point
  for nothing.
- **The 8th button does not exist.** The earlier "D-pad + A/B + Back + Home" phrasing
  double-counted: it listed both a B button and a separate Back button, which are the same
  control. Corrected to 7.
- **Power is a hard switch, not a button** - it stays out of the expander architecture
  entirely (real hard-off / load-switch / ship-mode path), so it consumes no expander pin.

**Consequence: the internal expander's 16th pin (now U60 P17) is spare** - the only unallocated
pin anywhere in the design at the time. It is reserved, not free (see 3b), and as of v0.2.4 it is
a live assignment carrying `ROOTPROBE_IRQ_READY_N`. If RootProbe were ever cancelled, that pin is
the natural home for a centre-select or an 8th button.

### 3b. RootProbe host IRQ — expander pin (now U60 P17), NOT a native pin

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
one pin it was most tempting to break it for. Bonus: the pin sits on the same port as the button
inputs, so the RootProbe IRQ routes through the shared interrupt net to GPIO21 and **can wake
AQROOT from deep sleep** at no extra cost.
> *(2026-07-27: the "interrupt-on-change already enabled for the buttons" reasoning is void —
> the TCA9535 has no interrupt-on-change configuration and no capture register. The wake bonus
> still holds via `WAKE_INT_N`, but **RootProbe must now hold the IRQ level until acknowledged
> rather than pulsing it**, since nothing latches a transient. See
> [[14 - RootProbe Interface v0.1]] §4.)*

Also settled in the same pass: RootProbe **MODULE_DETECT** = "does the coprocessor answer on
the I2C management bus" (no pin), and **RESET** = an I2C management command, with the
accessory-side load switch as the power-cycle fallback (no pin). **SPI CS remains the one
RootProbe signal genuinely needing a Phase-2 native-pin decision** - a per-transaction chip
select cannot sit behind an I2C expander at usable speed.

### Net result

**Native pin budget CLOSED: 29 assigned, 2 reserved test pads (GPIO45/46), 0 unassigned, 0
outstanding claims.** RootProbe's IRQ was the last queued demand on a native pin and it is now
on the expander. Expander budget: **U60 @ 0x20 = 16/16 used** (P17 = RootProbe IRQ),
**U61 @ 0x21 = 16/16 used** (15 user XGPIO + ACC_PWR_EN).

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
GPIO43), an expander home for IRQ (U60 P17), and I2C for DETECT and RESET. It has no
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
**15 assigned + 1 footprint-reserved for the Phase-2 RootProbe IRQ = 0 generally available.**
That pin has a committed owner and a reserved footprint; it is simply unpopulated until RootProbe
exists. Plan new signals against zero available capacity on this chip. *(2026-07-27: in v0.2.4 it
is a live assignment — U60 P17 = `ROOTPROBE_IRQ_READY_N`. Still 0 available.)*

### 4. Deep-sleep current caveat - standby figure is ESTIMATED

The ~10-20 uA deep-sleep figure and the ~2-week standby number derived from it are **NOT
measured**, and the ~10-20 uA is an ESP32-S3 *chip* figure standing in for a *system* figure.
The true number must sum **TPS63020 quiescent (~25 uA - already comparable to the entire ESP32
figure) + both TCA9535 expanders (U60 + U61) + MAX17048 + all pull-ups (7 buttons, INT/wake, I2C
pair, every expander safe-state pull) + load-switch leakage + charger/power-path + display
leakage + IMU wake-mode current.** Two of those - the second expander and the safe-state pulls - are
structural consequences of decisions locked earlier in this log; both are correct decisions
that nonetheless cost standby current, and they have to be counted.

**DO NOT PUBLISH THE STANDBY NUMBER IN MARKETING UNTIL MEASURED ON BETA HARDWARE.** A "2-week
standby" line on a campaign page is a promise; if the measured system figure lands at 100-200
uA the honest answer is days, not weeks. Same rule already applied to demoing only features
that actually work. Marked in [[13 - Power Budget and Battery Runtime v0.1]]; Beta bring-up
must measure true system standby at the battery, in the final enclosure, with wake sources
armed.

## GPIO EXPANDER PART CHANGE: MCP23017 -> TI TCA9535PWR (LOCKED, 2026-07-27)

**Both I2C GPIO expanders are now Texas Instruments TCA9535PWR.** This supersedes the MCP23017
everywhere in the design. Detail in [[11 - Beta Pin Map v0.2]] §7 (now revision **v0.2.4**).

| Property | Value |
|---|---|
| Part | **Texas Instruments TCA9535PWR** (both devices) |
| **U60** | internal expander — buttons + internal control — **I2C 0x20**, straps **A2=GND, A1=GND, A0=GND** |
| **U61** | external expander — community header — **I2C 0x21**, straps **A2=GND, A1=GND, A0=+3V3** |
| Package | **PW, TSSOP-24, 0.65 mm pitch** |
| KiCad symbol | **`Interface_Expansion:TCA9535PWR`** |
| KiCad footprint | **`Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm`** |
| I/O | **16 genuinely bidirectional** per device — Port 0 `P00-P07`, Port 1 `P10-P17` |
| Interrupt | **one open-drain active-low `/INT` per device**, both wired-OR onto **`WAKE_INT_N`** -> **ESP32 GPIO21** |

### Why the part changed — two reasons, both binding

1. **The current MCP23017 I2C silicon has output-only GPA7/GPB7 limitations.** The pre-schematic
   review of 2026-07-26 recorded a "factual correction" asserting all 16 MCP23017 pins were fully
   bidirectional and recalculated every pin budget on that basis. **That correction does not hold
   up against the current I2C-variant silicon, so it is itself corrected here.** The right
   resolution is not to re-litigate which two pins are crippled — it is to use a part that has no
   such asymmetry.
2. **The community header requires all 15 exposed XGPIO to be genuinely bidirectional.** An
   accessory maker reading a published "XGPIO0-14, 3.3V logic" contract will wire an input to any
   one of them. Two output-only pins hidden inside that range is a latent support disaster and a
   promise AQROOT cannot keep. **This reason alone forces the change**, independently of reason 1.

### Validation status — stated honestly

> **The TCA9535PWR is DATASHEET-TRUSTED, NOT BENCH-VALIDATED. First hardware validation happens
> on Beta.** No TCA9535 has ever been powered on for this project. The expander test that passed
> on 2026-07-26 used a **Waveshare MCP23017 board** — different vendor, different silicon,
> different register map, different interrupt model. That test validated the *architectural
> pattern* (I2C-mediated GPIO coexisting with the FT6236 touch and BMI270 IMU on one bus) and
> **nothing about this part.** Do not call the expander "validated" anywhere without naming the
> part that was actually tested. See the corrected Alpha validation entries below and in
> [[Alpha-Tests/HARDWARE-NOTES]].

This is a deliberate, accepted risk: a datasheet-specified digital I2C part with a locked pin map
is a reasonable thing to capture in a schematic ahead of bench proof. The cost is that **the Beta
BOM is no longer 100% bench-validated**, and the earlier "cleared to begin the KiCad schematic on
fully-validated parts" claim has been retired accordingly.

### Architectural consequences

- **INTA/INTB separation is GONE.** The MCP23017 Port-A/Port-B split was chosen partly so `INTB`
  would be a "pure button interrupt" immune to control-signal activity. **The TCA9535 has ONE
  `/INT` covering both ports, so that property no longer exists.** The port split is kept for
  readability (Port 0 = outputs, Port 1 = inputs), but the interrupt rationale for it is void and
  firmware must not rely on it.
- **Interrupt-on-change configuration is GONE.** Nothing to enable: `/INT` asserts whenever an
  input differs from the value last read out of its Input Port register, and clears when that
  register is read.
- **INTF / INTCAP are GONE**, so the chip cannot report what changed. **Firmware identifies the
  source by reading both input-port registers from both devices and diffing against its own
  previous snapshot.** Treat `WAKE_INT_N` as level-sensitive and re-check that it released — two
  devices share the net.
- **Internal GPPU pull-ups are GONE — the TCA9535 has no internal pull-ups at all.** The external
  10k button pull-ups and every safe-state pull were already mandatory; they are now the *only*
  pulls in the design, with no fallback. The safe-state rule tightens rather than relaxes.
- **New hard firmware rule:** all ports default to inputs (Configuration registers reset to
  `0xFF`) while the output latches reset to `0x00`, which is **not** the safe state for every net.
  **Firmware MUST write safe output-latch values (0x02/0x03) BEFORE changing Configuration bits
  (0x06/0x07) from input to output**, or it risks glitching `NFC_5V_EN`, `AMP_SD_MODE`, or
  `ACC_PWR_EN` at boot.
- **New hard RootProbe rule:** `ROOTPROBE_IRQ_READY_N` (U60 P17) **must be level-held until
  acknowledged, not pulsed** — there is no capture register to catch a transient, and U60's single
  `/INT` merges the button and RootProbe sources. See [[14 - RootProbe Interface v0.1]] §4.
- **TCA9535 register set (the complete set — eight registers, no others):** `0x00` Input Port 0,
  `0x01` Input Port 1, `0x02` Output Port 0, `0x03` Output Port 1, `0x04` Polarity Inversion 0,
  `0x05` Polarity Inversion 1, `0x06` Configuration 0, `0x07` Configuration 1. **There is no
  IODIR, GPPU, GPINTEN, INTF, INTCAP, IOCON, DEFVAL, or INTCON.** Keep Polarity Inversion at
  `0x00` and invert in firmware, so register contents match the schematic net names.
- **One address-parameterised driver serves both U60 and U61** — same silicon, two instances. Do
  not write two drivers.
- **I2C bring-up: start at 100 kHz, then verify 400 kHz** with all five devices plus an accessory
  on the external segment.

### What did NOT change

Every native ESP32-S3 GPIO assignment, both I2C addresses (0x20 / 0x21), the reserved address
table, the GPIO43 `FAST_IO / U0TXD / ROOTPROBE_CS` multiplex, the connector-sheet requirements,
the 7-button cluster, and the 15-user-XGPIO header. **The digital pin architecture is not
reopened by this change.**

### Still unresolved (unchanged by this decision, still blocking schematic freeze)

- **External community-header I2C isolator or bus switch** — unselected. Binding criteria:
  powered-off high-impedance on the external side, and must NOT back-power the accessory side.
- **ACC_PWR_EN accessory load switch** — unselected.
- **U60/U61 footprint audit** — the symbol/footprint pair above is assigned but **not yet verified
  against the TI datasheet drawing.**

## IR: native RMT + transistor LED driver (Beta)
IR validated on the bench (TSOP38238 + TSAL6200). Two Beta requirements emerged:
(1) FIRMWARE: use the native ESP32-S3 RMT peripheral for IR carrier/timing, NOT a
bit-banged library. The S3 is the only ESP32 with RMT DMA, which protects IR timing from
WiFi/BT/radio interrupt jitter - critical since AQROOT runs radios concurrently.
(2) HARDWARE: drive the IR LED through a transistor/MOSFET, not directly from a GPIO.
Direct GPIO drive at 150R gives ~7mA average (vs 100-500mA in a real remote) and only
1-3cm of range. Add the driver stage to the Beta schematic.

---

## Radio modules LOCKED: Ebyte E22-900M22S + E07-400M10S (2026-08-07)

> **BOTH RADIOS ARE CERTIFIED MODULES. NEITHER IS A BARE IC.**

| Radio | Module | Silicon | Band |
|---|---|---|---|
| LoRa / sub-GHz | **Ebyte E22-900M22S** | SX1262 | 915 MHz |
| Sub-GHz OOK/ASK/FSK | **Ebyte E07-400M10S** | CC1101 | 433 MHz |

Both expose an **IPEX / u.FL** antenna port; the Beta antennas plug onto those ports. See
[[12 - RF and Antenna Plan v0.1]] for the selected antennas (Taoglas FXP890 / FXP450) and the
antenna keep-out rules.

### What this closes

Two separate open questions, both previously recorded as blocking layout:

| Question | Recorded as | Now |
|---|---|---|
| Which SX1262 module | "**EBYTE E22 VS WAVESHARE CORE1262 UNRESOLVED**" — schematic text + `libraries/README.md` | **E22-900M22S** |
| CC1101 module *or* bare IC | "**not yet decided**" — `libraries/README.md` § `CC1101_RADIO_PLACEHOLDER` | **Module** (E07-400M10S) |

The second is the larger consequence. Choosing a module over a bare CC1101 removes the entire
bare-IC burden that `libraries/README.md` enumerates: **no crystal + loading, no RF matching /
balun network, no band filtering, no antenna interface** to design, lay out under RF
constraints, or certify from scratch. Combined with the SX1262 module, **no 433 or 915 MHz RF
signal reaches the main PCB at all** — NFC is now the only board-level RF design task.

This also supersedes the open framing in the **Radio** section above ("use a certified breakout
module, *e.g.* Ebyte E22 series") — the family is no longer an example, the part is fixed.

### Deliberately NOT recorded here

House rule from the [TPS61023](#tps61023-nfc-5v-pa-boost--beta-architecture-locked-2026-07-31)
and [MAX17048](#max17048-fuel-gauge--beta-architecture-locked-2026-07-31) blocks: a remembered
number written here is indistinguishable from a verified one later. So these stay **PENDING —
FROM DATASHEET** and must be taken from Ebyte's official documentation at capture time:

- Exact pin count, pitch, pinout, module outline and land pattern — **for both modules**.
- TX power, supply voltage range, and peak/average TX current — **do not infer TX power from
  the part number**; take it from the datasheet.
- Whether either module needs external decoupling beyond the datasheet reference circuit.
- The exact certification status and its conditions (see the cert caveat below).

```
E22-900M22S AND E07-400M10S HAVE DIFFERENT
OUTLINES, PAD PITCH AND PAD COUNTS.

DO NOT CREATE A "GENERIC EBYTE MODULE" FOOTPRINT.
ONE VERIFIED LAND PATTERN PER MODULE, FROM THE
MANUFACTURER DRAWING.
```

### Open items this lock creates

- [ ] **VERIFY THE ANTENNA INTERFACE BEFORE ORDERING.** Ebyte sells IPEX and stamp-hole
      variants under closely-related part numbers. The whole zero-PCB-impact antenna plan
      assumes IPEX. A stamp-hole variant would force footprints, RF routing and a board-level
      antenna interface — the exact work this lock was chosen to avoid.
- [ ] **Modular-cert conditions.** The *reason* for choosing certified modules (recorded in the
      Radio section above) was FCC/CE pre-certification that survives units leaving your hands.
      That same section already warns that **modifying a certified module's RF section can void
      the certification** — and swapping the stock antenna for the Taoglas parts is exactly such
      a modification. Confirm with the cert lab that the pre-cert still applies, or budget for
      re-evaluation. **Do not bank the pre-cert saving until this is answered.**
- [ ] **Footprints + symbols.** `SX1262_RADIO_PLACEHOLDER` and `CC1101_RADIO_PLACEHOLDER` carry
      **no footprint** by design, pending exactly this decision. Both can now be assigned real
      land patterns from the manufacturer drawings.
- [ ] **Stale "UNRESOLVED" text still in the project.** `libraries/README.md` and the
      `04_spi_b_radios_nfc` sheet text still read "EBYTE E22 VS WAVESHARE CORE1262 UNRESOLVED" /
      "EXACT CERTIFIED MODULE PENDING". Both need updating — the schematic text is a KiCad edit
      and is deliberately left untouched here.

### Not changed by this lock

Pin assignments, the shared SPI Bus B topology, CS discipline, and the `SX1262_RST_N` /
`CC1101_GDO0` control nets are all unaffected — this decision picks packages, not pins. The
dual-radio commitment itself is unchanged; see **Radio: DUAL-RADIO LOCKED** above.

---

## NFC package LOCKED: ST25R3916-AQET (2026-08-07)

> **DISCRETE ST25R3916. NOT A PLUG-ON NFC MODULE.**

| Item | Value |
|---|---|
| Part | **STMicroelectronics ST25R3916-AQET** |
| Architecture | **Discrete** ST25R3916 on the AQROOT main board |
| Antenna | **ST reference-derived tuned PCB loop** — rear face, per [[12 - RF and Antenna Plan v0.1]] §2 |
| Matching | **ST reference matching network** — not an in-house design |
| Interface | SPI (Bus B, third device), unchanged |

This closes the package question recorded against `ST25R3916_NFC_PLACEHOLDER` in
`hardware/beta/kicad/aqroot-beta/libraries/README.md`, which until now read *"MPN
`ST25R3916` — no package suffix, because the package is not selected"*. The **-AQET**
suffix is now fixed and the MPN is orderable.

Note the contrast with the two sub-GHz radios: those are **certified modules**
(E22-900M22S, E07-400M10S) with their RF front ends inside the module and the antenna on
an IPEX port. NFC is the opposite — a **bare IC whose RF front end, matching network and
antenna are all AQROOT board content**. See *Radio modules LOCKED* above; do not
generalise the module approach to NFC.

### What this does NOT change

```
NFC RF / MATCHING / ANTENNA REMAIN DO NOT ROUTE
```

- **U9 is still `ST25R3916_NFC_PLACEHOLDER`**, still `on_board no`, still with **no
  footprint**. The symbol has not been touched.
- **No land pattern exists.** Selecting a package makes the correct footprint
  *obtainable*; it does not make one *exist*. It must be built from the ST package
  drawing for the -AQET variant, and the exposed pad treated per the datasheet.
- **The antenna and matching network are not captured.** `NFC_RFO1/RFO2/RFI1/RFI2_TBD`
  and `NFC_XIN/XOUT_TBD` remain parked, and their six ERC exclusions stand unchanged.
- **The symbol's logical pins 1–15 are still placeholders** and will change when the real
  pinout is applied.

### Still open

- [ ] Build the -AQET land pattern from the ST package drawing; confirm exposed-pad
      requirement. **Do not use a generic QFN footprint.**
- [ ] Capture the ST reference matching network and the tuned PCB loop; only then may the
      `*_TBD` RF nets be resolved and the DO NOT ROUTE markers revisited.
- [ ] Crystal / reference-clock network (`NFC_XIN/XOUT_TBD`) per the ST reference design.
- [ ] Update `libraries/README.md` and the `ST25R3916_NFC_PLACEHOLDER` symbol fields when
      the footprint work is actually done — **not before**, so the library README keeps
      describing the symbol as it really is.

---

## BQ25185 package + footprint LOCKED: BQ25185DLHR / DLH0010A (2026-08-07)

| Item | Value |
|---|---|
| MPN | **BQ25185DLHR** (Texas Instruments) |
| Package | **DLH — WSON-10**, 2.2 x 2.0 mm body, 0.4 mm pitch, exposed thermal pad |
| Footprint | **`Package_DFN_QFN:Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm`** (KiCad stock) |
| Source | TI BQ25185 datasheet / DLH0010A package drawing |

### Why a stock footprint was accepted here

Every other unresolved power device needs a project-local land pattern because no stock
KiCad footprint matches. This one is the exception, and the reason is specific: the stock
footprint is **not a generic WSON-10** — it is TI's own DLH0010A land pattern, and the
KiCad library file cites the BQ25185 datasheet by URL in its own `descr` field:

```
(descr "Texas DLH0010A WSON, 10 Pin (https://www.ti.com/lit/gpn/BQ25185)")
```

Geometry checked before assigning, every item matching:

| Attribute | TI DLH spec | KiCad footprint | |
|---|---|---|---|
| Package designator | DLH | `Texas_DLH0010A` | ✅ |
| Signal pads | WSON-10 | pads 1–10, five per side | ✅ |
| Pitch | 0.4 mm | 0.4 mm (y = -0.8, -0.4, 0, +0.4, +0.8) | ✅ |
| Body | 2.2 x 2.0 mm | F.Fab outline -1.1..+1.1 x -1.0..+1.0 | ✅ |
| Exposed pad | yes | pad **11**, 0.9 x 1.5 mm rect at origin | ✅ |

**Symbol/footprint pin agreement:** the project symbol declares pins 1–10 plus **pin 11 =
EP (power_in)**; the footprint provides pads 1–10 plus **pad 11 = exposed pad**. Exact 1:1,
and the EP numbering agrees — which is the usual failure mode with WSON parts.

### Residual checks — NOT closed by this entry

- **Confirm against TI's *recommended land pattern* section, not just the package drawing.**
  TI datasheets publish both; KiCad's footprint follows the land pattern, but that has not
  been read directly here.
- **Thermal vias are not included.** A `..._ThermalVias` variant of this footprint exists.
  Whether to use it is a thermal/layout decision for the power review, not a package
  decision. The base footprint was chosen as the neutral option.
- **Charge-current setting** (`ISET`, start ~500 mA pending enclosure thermal testing) is
  unaffected by this entry.

### Correction to the previous audit

An earlier audit reported the BQ25185 as having "no MPN and no package recorded". **That was
wrong.** The schematic symbol already carried `MPN = BQ25185DLHR`, `Manufacturer = Texas
Instruments` and a DLH/WSON-10 `Package` note. The error came from grepping only the
Markdown docs and from an MPN listing filtered to parts that already had footprints — U11
had none, so its MPN was never displayed. What was genuinely missing was the **Markdown
documentation**, now added here and in [[01 - Hardware Core]] and
[[06 - BOM and Cost Tracker]].

---

## MAX17048 footprint NOT locked — verification failed (2026-08-07)

> **NO FOOTPRINT ASSIGNED. U14 stays blank.**

Package metadata, now also recorded in [[01 - Hardware Core]]:

| Item | Value |
|---|---|
| MPN | **MAX17048G+T10** (Analog Devices / Maxim) |
| Package | **8-pin TDFN-EP**, 2 mm x 2 mm, 0.5 mm pitch, exposed pad |
| Package code | **T822+3** |
| Outline drawing | **21-0168** |
| Recommended land pattern | **90-0065** |

### The proposed stock footprint was REJECTED — wrong manufacturer

`Package_DFN_QFN:DFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.5mm` was put forward as the candidate. Its
own `descr` field shows it is **not a Maxim footprint at all**:

```
(descr "DFN, 8 Pin (http://ww1.microchip.com/downloads/en/DeviceDoc/
        Atmel-8127-AVR-8-bit-Microcontroller-ATtiny4-ATtiny5-ATtiny9-ATtiny10_Datasheet.pdf)")
```

It is derived from the **Microchip/Atmel ATtiny4/5/9/10** drawing. Assigning it would have put
an ATtiny land pattern under a Maxim fuel gauge.

### The Maxim-derived footprint is a different one

`Package_DFN_QFN:TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm` cites **exactly the outline named in the
MAX17048 datasheet**:

```
(descr "TDFN, 8 Pin (https://pdfserv.maximintegrated.com/package_dwgs/21-0168.PDF)")
```

Every copper dimension differs between the two:

| | proposed (0.9x1.5) | Maxim-derived (0.8x1.2) |
|---|---|---|
| Provenance | Microchip ATtiny | **Maxim 21-0168** |
| Signal pad size | 0.7 x 0.25 mm | **0.775 x 0.25 mm** |
| Signal pad X | ±1.0 mm | **±0.9875 mm** |
| Exposed pad | 0.9 x 1.5 mm | **0.8 x 1.2 mm** |
| Courtyard X | ±1.6 mm | ±1.63 mm |

Identical in both, and both matching the symbol: 8 signal pads, 0.5 mm row pitch, EP numbered
**9**, pin 1 top-left with 1–4 down the left and 5–8 up the right.

**"2 x 2 mm, 0.5 mm pitch, 8-pin" identifies nothing on its own** — stock KiCad ships **nine**
such variants whose exposed pads range from 0.6 x 1.2 mm to 1.05 x 1.75 mm. The EP is the
discriminator, and only one variant cites Maxim.

### Why even the Maxim-derived one is not assigned

It cites **21-0168, the package OUTLINE** — not **90-0065, the recommended LAND PATTERN**.
Outline drawings give the component body and its exposed pad; land patterns give the PCB
copper, which is normally not identical. This is the same gap the symbol's own `Note` recorded:
datasheet 19-6171 Rev 7 references 21-0168 and 90-0065 as external documents and **does not
print the TDFN exposed-pad dimensions**, so no variant could be checked against the G-package
drawing.

### To close this

1. Obtain **Maxim/ADI land pattern 90-0065**.
2. Compare against `TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm` — EP copper, signal pad size, pad
   span, paste treatment. **Do not re-check the 0.9x1.5 variant; it is the wrong part.**
3. If 90-0065 matches, assign that stock footprint to the symbol, the `lib_symbols` cache and
   the U14 instance together.
4. If any material dimension differs, create a project-local **`MAX17048_TDFN8_T822`** from
   90-0065. Not created yet.

Thermal vias on the EP remain a separate layout/thermal decision, as with the BQ25185.

---

## Nontrivial footprint verification policy (STANDING, 2026-08-07)

A footprint may be marked **VERIFIED** only when **all five** hold:

1. Exact **MPN** is locked.
2. Manufacturer **package code** is identified.
3. Manufacturer **recommended PCB land pattern** has been obtained.
4. KiCad **copper / paste / mask / pin-1** geometry has been compared against that land pattern.
5. The comparison **passes**.

**A footprint name is not evidence.** This rule exists because a stock KiCad footprint with the
correct headline geometry (body, pitch, pad count) can be derived from a *different
manufacturer's* drawing — proven twice in this project:

- `DFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.5mm` was proposed for the MAX17048 and is
  **Microchip/Atmel ATtiny-derived**. Rejected.
- `LED_D5.0mm` on D1 (TSAL6200) derives from an unrelated **Reichelt LL-504BC2E** datasheet.

**Exempt** (no manufacturer provenance required): generic EIA chip passives
(`R_xxxx_yyyyMetric`, `C_xxxx_yyyyMetric`), simple SMD test pads
(`TestPoint_Pad_D1.0mm`), and ordinary generic 2.54 mm THT pin headers.

**Locking a part and verifying its footprint are separate gates.** A part may be LOCKED while
its footprint stays BLOCKED.

---

## Nontrivial footprint provenance audit (2026-08-07)

Provenance below is read from each footprint's own `descr`/`tags`. **No footprint was changed
in this pass, and none was promoted to VERIFIED — no manufacturer land pattern was available
to compare against.**

| Ref | MPN | Pkg | Footprint | Provenance in file | Verdict |
|---|---|---|---|---|---|
| U11 | BQ25185DLHR | DLH | `Texas_DLH0010A_WSON-10-1EP…` | **TI, cites ti.com/lit/gpn/BQ25185** | geometry compared, land-pattern section unread |
| U5 | MAX98357A | TQFN-16 | `TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm` | **Maxim 21-0136 (T1633-5) + land pattern 90-0032** | strongest stock provenance; confirm package code |
| J3 | USB4105-GF-A-120 | — | `…GCT_USB4105-xx-A_16P…` | **GCT usb4105.pdf**; tags list this exact variant | suffix VERIFY |
| J4 | — | — | `JST_PH_B2B-PH-K…` | **JST ePH.pdf** | acceptable |
| U1 | — | — | `RF_Module:ESP32-S3-WROOM-1` | **Espressif datasheet** | acceptable |
| MK1 | — | — | `InvenSense_ICS-43434-6…` | TDK/InvenSense **product page** (not land pattern) | VERIFY |
| U4 | BMI270 | LGA-14 | project-local | **BST-BMI270-DS000-08 rev 1.6 §8.3 landing pattern** | VERIFIED (project-local) |
| U6 | TSOP38238 | Minicast | project-local | Vishay 82491 rev 2.1; **drill/pad are IPC-7251 allowances, not Vishay values** | acceptable, self-declared |
| U13 | TPS61023DRLR | DRL | `SOT-563` | JEDEC MO-293-UAAD + tag **`Texas-DRL-6`** | GEOMETRY_REVIEW_REQUIRED |
| D3–D6 | TPD4E1B06DRLR | DRL | `SOT-563` | same as U13 | GEOMETRY_REVIEW_REQUIRED |
| U16 | TCA9517ADGKR | DGK | `VSSOP-8_3x3mm_P0.65mm` | JEDEC MO-187 + tag **`Texas_DGK0008A`** | GEOMETRY_REVIEW_REQUIRED |
| U2/U3 | TCA9535PWR | PW | `TSSOP-24_4.4x7.8mm_P0.65mm` | JEDEC MO-153 AD, **no TI tag** | GEOMETRY_REVIEW_REQUIRED (repo already flagged) |
| U15 | TPS22918DBVR | DBV | `SOT-23-6` | JEDEC MO-178, **no TI tag** | GEOMETRY_REVIEW_REQUIRED |
| U10 | USBLC6-2SC6 | SOT-23-6L | `SOT-23-6` | JEDEC MO-178, **no ST provenance** | GEOMETRY_REVIEW_REQUIRED |
| D2/D7 | TPD2E009DBZR | DBZ | `SOT-23` | JEDEC TO-236 AB, **no TI tag** | GEOMETRY_REVIEW_REQUIRED |
| D1 | TSAL6200 | 5 mm THT | `LED_D5.0mm` | **Reichelt LL-504BC2E — unrelated part** | see below |

### D1 — measured, not replaced

`LED_D5.0mm` is: 2 through-holes, **2.54 mm lead spacing**, 0.9 mm drill, 1.8 mm pads,
**5.00 mm body circle**, pin 1 square. That is the standard 5 mm THT LED form and is very
likely correct for the TSAL6200. **Not replaced** — but the provenance is a different part, so
confirm lead spacing, lead diameter and body diameter against **Vishay document 81010** before
fab. Replace only if a real dimension disagrees.

---

## Deferred and blocked items — status at 2026-08-07

### C24 — SYS bulk, still UNRESOLVED (schematic deliberately unchanged)

Direction recorded: **22 µF / 10 V / X7R / 1206**, candidate **Murata GRM31CR71A226ME15L**.
The schematic still reads `22uF 25V X7R` on an invalid `C_0603_1608Metric`, and was **not
edited**, because the direction cannot yet be proven appropriate:

- The Murata part and its **DC-bias curve** have not been verified from an authoritative source.
- **The minimum acceptable effective capacitance is not derivable**: no SYS transient or
  peak-current requirement is documented anywhere in this repo. Inventing a threshold was
  refused. **This requirement must be written down before C24 can be closed.**

The 0603 assignment remains wrong regardless — 0603 X7R does not reach 22 µF at 25 V.

### C12, R24 — IR driver, DEFERRED

Both stay `TBD`. R24 is the LED current-limit resistor and C12 the `IR_LED_SUPPLY_TBD`
decoupling; neither can be chosen until **`IR_LED_SUPPLY` and the intended TSAL6200 pulse
current** are locked. No value, voltage or package guessed. Q1 is now locked (AO3400A) but
does not by itself resolve either.

### C18, C19 — NFC decoupling placeholders, DO NOT ROUTE

Roles identified from the netlist: **C18 = `+3V3` → GND** (ST25R3916 `VDD_IO` domain),
**C19 = `NFC_5V_PA_PENDING` → GND** (the switched 5 V PA rail). Both stay
`100nF_PLACEHOLDER`: the ST reference decoupling network has not been captured, and values
must come from the ST reference design, not from a generic 100 nF assumption. **DO NOT ROUTE
preserved.**

### J3 USB-C — suffix still VERIFY

**Board thickness is now locked at 1.6 mm.** The GCT **USB4105** family is locked and the
footprint cites GCT's own drawing. The candidate suffix **USB4105-GF-A-120** is **not
confirmed**: what the `-120` field designates, and which suffix corresponds to a 1.6 mm board
with the intended shell-stake configuration, must come from the GCT drawing. Not guessed.

### Still blocked on external vendor drawings

`U12` TI DSJ (14-pin VSON 3×4 mm) · `U14` Maxim **90-0065** · `L1` Coilcraft XFL4020 ·
`L2` Würth 74438357010 · `Q1` AOS AO3400A · `SW9` C&K PCB layout · `J2` Molex ·
`LS1` Same Sky · `J1` current Adafruit mechanical/FPC drawing · `U7`/`U8` Ebyte · `U9` ST.

---

## Vendor land-pattern verification pass — method proven, systematic finding (2026-08-07)

### The retrieval method now works

Vendor PDFs can be fetched and their land-pattern dimension callouts extracted as text
(PyMuPDF). Extraction was corroborated against independently supplied values for TPD4E1B06
(0.5 mm pitch, 0.30 × 0.67 mm pads, 1.48 mm span) — exact match. This is repeatable for any
part whose datasheet is reachable.

### Systematic finding — KiCad stock footprints are IPC-7351 alternates, not vendor-exact

Four TI packages were compared against their **recommended land patterns** (not merely the
package outlines). In every case pitch and pad width match, and the **signal pad length is
longer in KiCad than TI recommends**:

| Package | Part | TI land pattern | KiCad footprint | Pitch | Pad width | Pad length |
|---|---|---|---|---|---|---|
| DRL0006A | U13, D3–D6 | 4223266/F | `SOT-563` | 0.5 ✅ | 0.30 vs **0.35** ❌ | 0.67 vs 0.675 ✅ |
| DBV0006A | U15 | 4214840/G | `SOT-23-6` | 0.95 ✅ | 0.6 ✅ | 1.1 vs **1.325** ❌ |
| PW0024A | U2, U3 | 4220208/A | `TSSOP-24_4.4x7.8mm` | 0.65 ✅ | 0.45 vs **0.40** ❌ | 1.5 vs 1.475 ✅ |
| DLH0010A | U11 | 4226298/A | `Texas_DLH0010A_WSON-10…` | 0.4 ✅ | 0.2 ✅ | 0.5 vs **0.75** ❌ |

**U11 is the closest**: pitch, pad width **and the exposed pad (0.9 × 1.5)** match TI exactly —
only the signal pad length differs.

**These footprints are not defective.** TI's own drawings state *"Publication IPC-7351 may have
alternate designs"*. KiCad's are IPC-7351-derived with fillet allowance; TI's are drawn to the
terminal. Both are legitimate.

### Consequence — a decision is required before any footprint can be marked VERIFIED

The standing policy requires the comparison to **pass**. On a strict vendor-exact reading,
**none of these can be marked VERIFIED**, and none was. Two coherent options:

- **A — accept IPC-7351 alternates.** Keep the stock footprints, record a documented deviation,
  and narrow the policy to require correct *provenance and package identity* rather than
  dimensional identity. Cheapest, and defensible: IPC-7351 is an industry standard.
- **B — build vendor-exact project-local footprints** from each TI drawing. Highest fidelity,
  but means authoring and maintaining a footprint per package family.

**This is an engineering/manufacturing preference, not a technical fact, so it was not decided
here.** No footprint was created, changed, or marked VERIFIED in this pass.

### One measurement caveat, stated plainly

Pad **count, pitch, and pad dimensions** extract unambiguously and are what the verdicts above
rest on. The parenthesised **overall-span** figure could **not** be resolved from text alone —
whether it denotes outer-edge-to-outer-edge or centre-to-centre depends on leader lines that
are not in the text layer, and the drawings use filled paths rather than rectangle primitives,
so vector measurement did not recover them. **No verdict above depends on the span figure.**

### Not reached in this pass

U16 (DGK), D2/D7 (DBZ0003A), U10 (ST Figure 19), L1 (Coilcraft), L2 (Würth), Q1 (AOS),
J2 (Molex), LS1 (Same Sky), J3 (GCT), U7/U8 (Ebyte), U9 (ST), J1 (Adafruit panel + mating FPC
connector), U5 (confirm T1633-5), D1 (Vishay 81010). The TI parts will very likely reproduce
the IPC-vs-vendor pattern above; the non-TI vendors are genuinely unknown and still worth
fetching once option A or B is chosen.

### Unchanged and still blocked

- **U14 MAX17048** — BLOCKED. 90-0065 not obtained. Outline 21-0168 alone is insufficient.
- **SW9** — footprint work STOPPED at the §1 gate: the symbol is still 2-pin `Switch:SW_SPST`
  and the locked JS102011SAQN is a 3-terminal SPDT.

---

## Footprint verification register (hybrid policy applied, 2026-08-07)

Policy: **Class A** — ordinary JEDEC leaded packages may be VERIFIED as IPC-7351 alternates
when package code, pad count, pin numbering, pitch and body/lead geometry agree and the only
differences are normal solder-fillet allowances. **Class B** — exposed-pad/thermal, magnetics,
connectors, switches, RF modules and mechanical interfaces require direct vendor land-pattern
review.

### CLASS A — VERIFIED_IPC_ALTERNATE

All five below: package code confirmed, pad count exact, pin numbering/orientation correct,
**pitch exact**, no exposed pad involved, no special layout requirement. Differences are
solder-fillet allowances only.

| Refs | MPN | TI pkg / drawing | KiCad footprint | Pitch | Pad (TI → KiCad) |
|---|---|---|---|---|---|
| U13, D3–D6 | TPS61023DRLR, TPD4E1B06DRLR | DRL0006A · 4223266/F | `Package_TO_SOT_SMD:SOT-563` | 0.5 = 0.5 ✅ | W 0.30→0.35 · L 0.67→0.675 |
| U15 | TPS22918DBVR | DBV0006A · 4214840/G | `Package_TO_SOT_SMD:SOT-23-6` | 0.95 = 0.95 ✅ | W 0.6→0.6 ✅ · L 1.1→1.325 |
| U2, U3 | TCA9535PWR | PW0024A · 4220208/A | `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` | 0.65 = 0.65 ✅ | W 0.45→0.40 · L 1.5→1.475 |
| U16 | TCA9517ADGKR | DGK0008A · 4214862/A | `Package_SO:VSSOP-8_3x3mm_P0.65mm` | 0.65 = 0.65 ✅ | W 0.45→0.5 · L 1.4→1.625 |
| D2, D7 | TPD2E009DBZR | DBZ0003A · 4214838/F | `Package_TO_SOT_SMD:SOT-23` | 0.95 = 0.95 ✅ | W 0.6→0.6 ✅ · L 1.3→1.475 |

U16's KiCad footprint additionally carries the tag **`Texas_DGK0008A`** — TI's own package code.
TI's drawings all state *"Publication IPC-7351 may have alternate designs."*

### CLASS B — U11 BQ25185DLHR: VERIFIED_IPC_ALTERNATE (EP vendor-exact)

TI DLH0010A land pattern **4226298/A** retrieved and compared against
`Package_DFN_QFN:Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm`:

| | TI 4226298/A | KiCad | |
|---|---|---|---|
| Pitch | 8X (0.4) | 0.4 | ✅ exact |
| Signal pad width | 10X (0.2) | 0.2 | ✅ exact |
| **Exposed pad** | **(0.9) × (1.5)** | **0.9 × 1.5** | ✅ **exact** |
| Signal pad length | 10X (0.5) | 0.75 | IPC fillet |

The Class-B-critical element — **the exposed pad — is vendor-exact**, and provenance is TI's own
drawing (footprint named `Texas_DLH0010A`, `descr` citing ti.com/lit/gpn/BQ25185). Only the
signal pad length is an IPC enlargement. Accepted with this note. TI's drawing also shows
optional **(Ø 0.2) thermal vias** under paste — a layout decision, not part of this footprint.

### BLOCKED_EXTERNAL_DOCUMENT

| Ref | Missing document | Why blocked |
|---|---|---|
| U14 | Maxim/ADI **90-0065** | policy: 21-0168 outline alone insufficient |
| SW9 | C&K JS recommended PCB layout | ckswitches.com 301→littelfuse.com returns **HTTP 403** |
| Q1 | AOS **SOT-23 package spec** (separate doc) | AO3400A datasheet rev 3.1 contains **no** package drawing or land pattern |
| U10 | ST USBLC6-2 datasheet | st.com **timed out twice** |
| U5 | ADI MAX98357A datasheet | analog.com **connection reset**; package code T1633-5 unconfirmed |

### NOT REACHED this pass

U12 (TI DSJ), L1 (Coilcraft), L2 (Würth), J2 (Molex), LS1 (Same Sky), J3 (GCT),
U7/U8 (Ebyte), U9 (ST), J1 (Adafruit panel + mating FPC connector), D1 (Vishay 81010).

### Note on Q1

The AO3400A datasheet also does not state the G/S/D pin assignment in extractable text, so the
symbol's `Q_NMOS_GSD` mapping (1 Gate / 2 Source / 3 Drain — consistent with the existing
wiring) remains unconfirmed against AOS. Both the pinout and the land pattern need the AOS
package document.

---

## Vendor verification — second pass results (2026-08-07)

### U12 TPS63020DSJR — BLOCKED_EXTERNAL_DOCUMENT (confirmed, not assumed)

The TI TPS63020 datasheet was retrieved and searched in full (34 pages). It confirms
**VSON / DSJ / 14 pins** in the packaging tables, but contains **no PACKAGE OUTLINE and no
LAND PATTERN EXAMPLE** — unlike the TPS61023/TPS22918/TCA9517/TCA9535/TPD2E009/BQ25185
datasheets, which all carry both. TI publishes the DSJ mechanical drawing separately. No
generic VSON substitute permitted.

### L1 / L2 — electrical data now recorded; footprints still blocked

Both datasheets retrieved and their **electrical and body data extracted unambiguously**. This
closes the earlier "take from the datasheet, do not record from memory" placeholders:

| | L1 Coilcraft XFL4020-152MEC | L2 Würth 74438357010 (WE-MAPI 4030) |
|---|---|---|
| Inductance | 1.5 µH ±20% | 1 µH ±20% |
| DCR | 14.40 mΩ typ / 15.80 max | 11.6 mΩ typ / 13.5 max |
| Isat | 4.1 A (10%) / 4.4 (20%) / 4.6 (30%) | 6.2 A (10%) / 12.5 A (30%) |
| Irms / IRP | 6.7 A (20 K) / 9.1 A (40 K) | IRP,40K 10.25 A max |
| SRF | 59 MHz | 59 MHz |
| Body | 4.0 × 4.0 mm, 2.10 max | 4.1 × 4.1 mm, 3.1 max |
| Source | Coilcraft doc 745-1 rev 03/10/26 | Würth 74438357010 datasheet |

**L2's ratings satisfy the outstanding requirement** that it be checked against the TI TPS61023
5 V boost design — 6.2 A saturation and 10.25 A rated current are far above any NFC PA draw.

**Both footprints remain BLOCKED.** The recommended land patterns print as three bare numbers —
Coilcraft **0.98 / 2.37 / 3.4**, Würth **1.39 / 3.35 / 3.7** — and text extraction does not
recover which number is the span. For each, **two different pad-centre solutions are
arithmetically valid**:

- Coilcraft: span 3.4 → gap 1.44, **or** span 2.37 → gap 0.41
- Würth: span 3.7 → gap 0.92, **or** span 3.35 → gap 0.57

Choosing wrong misplaces both pads by roughly half a millimetre on a 4 mm part. Not guessed.
**Resolvable in seconds by eye from either drawing**, or by using Würth's own EDA/KiCad asset.

Also recorded: Coilcraft marks the **start (short) lead** — connect high dv/dt there for lowest
EMI — so whichever footprint is built must carry that orientation marker. Würth marks
start-of-winding equivalently.

### Retrieval failures this pass

| Ref | Source | Result |
|---|---|---|
| J2 | Molex 5025700893 drawing | request **timed out** |
| SW9 | C&K / Littelfuse JS | **HTTP 403** (unchanged) |
| U10 | ST USBLC6-2 | **timed out** (third attempt) |
| U5 | ADI MAX98357A | **connection reset** (unchanged) |
| Q1 | AOS separate SOT-23 package spec | device datasheet has no package drawing |

### Method note — where text extraction stops being sufficient

Dimension **callouts** extract reliably; **which geometry a callout attaches to** does not.
That was harmless for the TI leaded packages, where pad width/length/pitch are individually
labelled (`6X (0.67)`, `6X (0.3)`, `4X (0.5)`), and it is decisive for two-terminal magnetics,
where the land pattern is three unlabelled numbers. **Any part whose land pattern is given as
bare numbers without per-feature labels needs a human to read the drawing.**

---

## Footprint verification — third pass (2026-08-07)

### Method advance: rasterize the drawing

The land-pattern ambiguity that blocked L1/L2 is **resolved**. Vendor PDF pages are now
rendered to PNG with PyMuPDF and the dimension **leader lines read visually**, so which callout
attaches to which geometry is known rather than inferred. This is the fix for the limitation
recorded in the previous pass, and it should be the default for any drawing whose land pattern
is given as bare numbers.

It also proved the earlier text-order guesses **wrong**: for Coilcraft, neither of the two
arithmetic candidates was correct — 2.37 turned out to be centre-to-centre, not a span.

### VERIFIED_VENDOR_EXACT — new project-local footprints

| Ref | MPN | Source | Land pattern as drawn |
|---|---|---|---|
| **L1** | XFL4020-152MEC | Coilcraft doc 745-3 rev 03/10/26 | pad **0.98 × 3.4**, **2.37 centre-to-centre** |
| **L2** | 74438357010 | WE datasheet rev 003.001 (2024-02-27) | span **3.35** o/o, gap **1.39**, length **3.7** → pad **0.98 × 3.7**, **2.37 c-c** |

Cross-checks that raised confidence: Coilcraft's terminals are 0.82 wide at 3.25 typ outer
span → ~2.43 terminal centres against a 2.37 land spacing; and the two parts independently
produce the **same 0.98 mm pad width and 2.37 mm spacing**, as expected for two 4 mm-class
inductors from different vendors.

Both footprints carry their vendor orientation marker — Coilcraft's start (short) lead bar
(*connect high dv/dt there for lowest EMI*), Würth's Start-of-Winding dot. Würth's **"No vias
and traces in restricted area"** is reproduced as a `Dwgs.User` outline over the 1.39 mm
inter-pad gap.

### VERIFIED_IPC_ALTERNATE — Q1

**AO3400A** — AOS publishes package geometry **separately** from the device datasheet, at
`res/package/SOT23.pdf` (doc PO-00001 rev N). Retrieved and rasterized:

- Recommended land pattern: pads **0.80 × 0.80**, row-to-row **2.40**, pitch **0.95**
- Package: e = 0.95 BSC, e1 = 1.90 BSC, D = 2.90 nom, E = 2.80 nom, E1 = 1.60 nom, b = 0.40 nom

KiCad `Package_TO_SOT_SMD:SOT-23` has 3 pads, **pitch 0.95 exact**, same 2+1 lead arrangement,
pads 1.475 × 0.6 at ±0.9375. Copper proportions differ (AOS shorter/wider, KiCad longer/
narrower) but both straddle the 2.80 mm lead span; ordinary leaded package, Class A → assigned.

**Pin order confirmed** from the datasheet package view and symbol: **G and S on the two-lead
side, D on the single-lead side** = 1 G / 2 S / 3 D, matching `Q_NMOS_GSD` and the existing
wiring (1→IR_GATE, 2→GND, 3→IR_LED_K). The earlier "unconfirmed pin order" caveat is closed.

### Still BLOCKED_EXTERNAL_DOCUMENT

| Ref | Missing | Attempts |
|---|---|---|
| U12 | TI **DSJ** package drawing (separate from datasheet) | full 34-page datasheet has no outline/land pattern |
| U14 | Maxim **90-0065** | no exception |
| SW9 | C&K JS recommended PCB layout | ckswitches 301 → littelfuse **403** |
| U10 | ST USBLC6-2 | st.com **timed out 4×** |
| U5 | ADI MAX98357A (confirm T1633-5) | analog.com **connection reset** |

### Not reached

J2 (Molex), LS1 (Same Sky), J3 (GCT), U7/U8 (Ebyte), U9 (ST EDA), J1 (Adafruit + mating FPC), D1 (Vishay 81010).

---

## Floorplanning-critical batch — J1 connector identified, J1 symbol mismatch found (2026-08-07)

### J1 — mating FPC connector IDENTIFIED, but J1 is BLOCKED_SYMBOL_MISMATCH

The Adafruit 1773 connector's linked datasheet is an **FCI (Amphenol) drawing no. 62684**,
product family **58DF**, "0.5mm CONTACT SPACING CONNECTOR" for FPC/FFC, SMT.

| | |
|---|---|
| Connector MPN | **FCI / Amphenol 62684-50210** (50 contacts) |
| Tape-and-reel form | **62684-502100** |
| Pitch | 0.5 mm |
| Contacts | 50 |
| Body (from sheet 2) | A 24.5 · B 25.65 · C 29.3 · D 30.5 mm |

**Recommended PC board layout (sheet 3, rev E) — captured in full:**

- pitch **0.5 ±0.05**
- signal land **0.3 wide × 1.2 long**
- contact field span **0.5 × (n−1) ±0.05** → **24.5 mm** for n = 50
- hold-down / mounting-plate lands **0.9 × 2.4**, set **3.3 mm** outboard of the contact field
- connector outline given for keep-out

**That is enough to build the footprint. It is not enough to assign it.**

**The blocker is the symbol, not the land pattern.** `ILI9341_FT6236_MODULE_PLACEHOLDER` (J1)
has **13 logical pins** — VCC_3V3, GND, LCD_SCK, LCD_MOSI, LCD_MISO, LCD_CS_N, LCD_DC,
LCD_RST_N, LCD_BL_CTL, CTP_SDA, CTP_SCL, CTP_RST_N, CTP_INT_N. The physical connector has
**50 contacts**. A 13-pin symbol cannot carry a 50-pad footprint.

**Required before J1 can be closed:**

1. The **Adafruit 2770 panel's 50-pin FPC pinout** — which signal sits on each of the 50
   contacts, including all the NC/GND/power/backlight-cathode pins the placeholder omits.
   **This document was not obtained and is the real remaining blocker.**
2. A **real 50-pin symbol** capturing that pinout, replacing the 13-pin functional placeholder.
3. Only then: build `AQROOT_Beta:FCI_62684-50210` from the sheet-3 layout and assign it.

Note also that the panel's backlight, touch-reset and any LED-anode/cathode pins commonly need
series/driver parts that the current 13-pin abstraction hides. **Do not narrow this to a
pin-count change** — it is a real capture of the display interface.

### LS1 CMS-1535-058SP — BLOCKED_EXTERNAL_DOCUMENT

The Same Sky datasheet (09/11/2024, 4 pages) was retrieved and every page inspected, including
the mechanical drawing rasterized. It gives:

- body **Ø15 × 3.5 mm**, acoustic opening **Ø11**, frame SPCC, cone PEN, Nd-Fe-B magnet
- 8 Ω (6.8–9.2), 0.5 W nominal / 1 W max, Fo 1000 Hz, SPL 89 dB @0.1 W
- polarity defined functionally: *"cone moves forward w/ positive dc current to the + terminal"*

**It does not dimension the solder pads at all.** The two pads appear on the drawing but carry
no size, spacing or angular-position callouts, and pages 3–4 are response curves and legal text.
Body outline alone is not a footprint. The 3D model may carry the geometry but is a STEP asset,
not parseable here.

**Needed:** a Same Sky land-pattern/soldering drawing, or measurement off the 3D model.

### Not reached this pass

SW9 (C&K retry), U10 (ST), J2 (Molex), J3 (GCT), U7/U8 (Ebyte), U9 (ST EDA), U5 (ADI),
U12 (TI DSJ), D1 (Vishay).

---

## J1 display interface — BLOCKED on backlight architecture (2026-08-07)

Panel datasheet **CH280QV10-CT Rev.D** (Shenzhen ChengHao) retrieved and read. The 50-pin
pinout, mode table, backlight spec and supply limits below are quoted from it.

### J1 is not "a 13-pin abstraction to expand" — it is entirely uncaptured

`J1` (`ILI9341_FT6236_MODULE_PLACEHOLDER`) has 13 logical pins and **zero netlist nodes — it is
wired to nothing**. The display signals exist but stop at the MCU/expander:

| Net | Members |
|---|---|
| `/DISP_CS_N` | U1.18, R26.2 (10k pull-up) |
| `/DISP_DC` | U1.22 only |
| `/DISP_RST_N` | U2.8, R16.1 |
| `/DISP_BL_CTL` | **U1.24 only** |
| `/SPI_A_SCK`, `/SPI_A_MOSI`, `/SPI_A_MISO` | U1 + **J2 (microSD) only** |

Sheet 03 contains only C13/C14/C15 (+3V3 decoupling), R25/R26 (CS pull-ups), J1 and J2. So
capturing J1 means **capturing the whole display interface for the first time**, including
supplies, grounds, mode straps, unused-pin grounding and the backlight subsystem.

### HARD BLOCKER — backlight has no circuit and +3V3 cannot drive it

Datasheet section 8, Backlight Characteristics: **4 white LEDs in parallel**, Vf **2.9 / 3.2 /
3.5 V** at **If = 80 mA**.

- The **+3V3 rail cannot drive this**. At Vf typ 3.2 V the headroom is 0.1 V; at Vf max 3.5 V
  the LEDs will not light from 3.3 V at all. A series resistor from +3V3 is **not viable** —
  current would swing wildly with Vf spread, temperature and rail sag.
- `DISP_BL_CTL` currently terminates on **one ESP32-S3 GPIO and nothing else**. A GPIO cannot
  carry 80 mA; that is far beyond the per-pin limit.
- **There is no LED driver, no current limiting, no boost, and no PWM stage anywhere.**
- The existing **TPS61023 5 V boost must NOT be reused.** It is architecturally locked to the
  NFC PA rail, and the repo already states "NOT A GENERAL-PURPOSE 5V RAIL" and "Do not connect
  ... general 5V accessories".

**Decision required before J1 can be wired** — a backlight topology: a dedicated constant-current
boost LED driver (typical for this panel class), or another sanctioned rail plus current
control, and how `DISP_BL_CTL` drives it (PWM into an EN/dimming pin). **Not guessed here.**

### SPI mode — recommendation, needs confirmation

Datasheet mode table (pins 6-9, IM3:IM0):

| IM3 IM2 IM1 IM0 | Mode | Pins used |
|---|---|---|
| 0 1 1 0 | 4-wire 8-bit SPI I | /CS, RS, SDI, SCL — **no SDO** |
| **1 1 1 0** | 4-wire 8-bit SPI II | /CS, RS, SDI, **SDO**, SCL |

The locked AQROOT architecture **expects display MISO**: [[10 - Beta Pin Map]] section "SPI Bus A
— Display + microSD (shared SCK/MOSI/**MISO**, separate CS)", and `libraries/README.md` maps
`LCD_MISO` to `SPI_A_MISO`, justifying its Tri-state pin type because SPI Bus A is shared with
the microSD socket.

**Recommendation: SPI mode II, IM3:IM0 = 1 1 1 0** — IM3 HIGH, IM2 HIGH, IM1 HIGH, IM0 GND —
because it is the only 4-wire mode exposing SDO, and dropping SDO would contradict the locked
pin map. **Confirm before wiring**: if display read-back is genuinely unused, mode I (0110) is
simpler and removes any shared-bus contention risk.

### Supply headroom — flag

Datasheet section 6, DC Characteristics: **IOVCC 1.65 / 1.8-2.8 / 3.3 V** and **VCI 2.5 / 2.8 /
3.3 V**. Both list **3.3 V as the MAXIMUM**, not a typical. Powering pins 40/41 (IOVCC) and 42
(VCI) from `+3V3` runs the panel at the top of its rated range with no margin for rail
tolerance. Absolute max is 4.6 V so it is not a destruction risk, but this should be an
explicit decision.

### Unused interface pins — real capture work, not NC markers

The datasheet states **"Connect unused pins to GND"** for the DB bus. In SPI mode that means
**DB[17:0] (pins 15-32) all to GND**, plus VSYNC/HSYNC/DOTCLK/DE (11-14) and /RD (35) handled
per the datasheet. TE (39) is optional. **These must be grounded, not marked no-connect.**

### Touch controller — VERIFY

Datasheet section 2: **CTP Driver IC = CST026**. Adafruit's page claims FT6236/FT6236U-compatible.
The repo assumes **FT6236 at I2C 0x38**. The physical interface (I2C SCL/SDA/IRQ/RESET on pins
44-47) is unaffected and stays locked, but the **controller identity and I2C address/protocol
are unconfirmed**. Recorded as a Beta procurement/firmware verification item — do not redesign
the I2C hardware over it.

### Mating connector — confirmed, footprint not yet built

**FCI/Amphenol 62684-50210** (tape 62684-502100), 50 contacts, 0.5 mm, top-contact. Recommended
layout captured: pitch 0.5 ±0.05, signal lands 0.3 x 1.2, contact span 0.5x(n-1) = 24.5 mm,
hold-down lands 0.9 x 2.4 set 3.3 mm outboard. **Footprint deliberately not built this pass** —
the hold-down pad Y-offsets were not unambiguously readable, and with J1 blocked there is no
value in committing a footprint whose mechanical anchors are uncertain.

### Panel 50-pin map (for the eventual symbol)

1 LEDK · 2-5 LED-A1..A4 · 6-9 IM0..IM3 · 10 /RESET · 11 VSYNC · 12 HSYNC · 13 DOTCLK · 14 DE ·
15-32 DB17..DB0 · 33 SDO · 34 SDI · 35 /RD · 36 /WR_RS · 37 RS_SCL · 38 /CS · 39 TE ·
40-41 IOVCC · 42 VCI · 43 GND · 44 CTP_SCL · 45 CTP_SDA · 46 CTP_IRQ · 47 CTP_RES · 48-50 GND.

Intended mapping once unblocked: DISP_RST_N to 10, SPI_A_SCK to 37, SPI_A_MOSI to 34,
SPI_A_MISO to 33 (mode II), DISP_CS_N to 38, DISP_DC to 36, I2C_SCL to 44, I2C_SDA to 45,
touch IRQ to 46, touch reset to 47.

---

## Metadata drift closure: SW9, U7, U8, U9, J3 (2026-08-07)

Five symbols carried metadata that contradicted decisions already locked elsewhere in this
log. No external vendor document was needed for any of them — this is propagation of existing
locks, not new selection. **Connectivity and ERC verified byte-identical before and after.**

### SW9 — stale SYMBOL CONFLICT note removed, pole mapping VERIFIED

The `Note` still read *"MUST BE RESOLVED BEFORE FOOTPRINT … this instance uses Switch:SW_SPST
which has only 2 pins … Changing the symbol is an approval-gated change and was NOT made here."*
That is no longer true — the instance **is** `Switch:SW_SPDT` with pins 1/2/3.

**Pole mapping now verified 1:1, closing the numbering question:**

| | KiCad `SW_SPDT` | C&K JS102011SAQN |
|---|---|---|
| Pole / common | **pin 2**, name `B`, alone at (−5.08, 0) | **terminal 2 = C = COMMON/POLE** |
| Throw | pin 1, name `A`, at (5.08, +2.54) | terminal 1 |
| Throw | pin 3, name `C`, at (5.08, −2.54) | terminal 3 |

The KiCad symbol places pin 2 by itself on the opposite side of the body from pins 1 and 3,
which is what makes it the pole. It coincides with the confirmed C&K common terminal, so the
numbering needs **no cross-map**.

Wiring as built, from the netlist: pin 2 → `BQ25185_SYS` (source), pin 1 → `U12 EN` + `TP13`,
pin 3 → unused throw carrying a `no_connect`. Electrical intent unchanged and still
SPST-in-practice (VINA → switch → EN, never switching GND).

**SW9 is no longer blocked on symbol numbering — only on land-pattern geometry** from the C&K
PCB layout drawing.

### U7 / U8 — Ebyte module lock propagated (was `Manufacturer: TBD`, `MPN: TBD`)

[[12 - RF and Antenna Plan v0.1]] locks both radios to Ebyte modules and states the module lock
*"removed that assumption"* of a board-level front-end. The symbols still said TBD.

| Ref | Symbol value | Manufacturer | MPN | Band / silicon |
|---|---|---|---|---|
| U7 | `CC1101_RADIO_PLACEHOLDER` | Ebyte | **E07-400M10S** | 433 MHz, CC1101 |
| U8 | `SX1262_MODULE_PLACEHOLDER` | Ebyte | **E22-900M22S** | 915 MHz, SX1262 |

Each `Package` field now also records the standing constraint: the module owns its matching
network and presents a matched 50-ohm IPEX port, so **no matching network and no separate U.FL
test connector belong on the main PCB**. Footprints remain BLOCKED pending Ebyte mechanical
drawings.

### U9 — package suffix propagated (was `MPN: ST25R3916`)

The `NFC package LOCKED: ST25R3916-AQET` decision explicitly closed the open question recorded
against this placeholder, which was *"`ST25R3916` — no package suffix, because the package is
not selected"*. The symbol never received the suffix. Now **`ST25R3916-AQET`**, VQFN-32
(5×5 mm), discrete — **not** a plug-on module. `VDD_PA` from the switched 5 V boost, `VDD_IO`
remains `+3V3`. Footprint still BLOCKED pending the ST package outline.

### J3 — manufacturer/MPN recorded for the first time, suffix kept UNCONFIRMED

J3 had a footprint (`…GCT_USB4105-xx-A_16P_TopMnt_Horizontal`) but **no `Manufacturer` and no
`MPN` property at all**. Added: GCT, `USB4105-GF-A-120`. The `Package` field states plainly
that the **family** is locked while the **variant suffix is a candidate and NOT confirmed** —
the suffix and its shell-stake configuration at the locked 1.6 mm board thickness must still be
verified against the GCT drawing. Recording the candidate does not promote it to verified.

### Tooling defect found and fixed (worth keeping)

The first attempt at this edit **silently corrupted both sheets** — 148 nets became 151. Cause:
the property-editing helper counted `(` and `)` with a plain per-line count, but property values
legitimately contain parentheses — `(Global Connector Technology)`, `(5x5 mm)`, `(3 signal pads
plus mounting tabs)`. Those inner parens skewed every depth walk, so inserted blocks landed
inside the wrong s-expression. A whole-file paren-balance assertion did **not** catch it,
because parens inside string literals are themselves balanced.

Fixed by counting depth **only outside double-quoted strings**, and by cloning a real sibling
property block rather than synthesising one. The corrupted attempt was reverted from backups and
never committed; the netlist was diffed against a restored-baseline export to prove it.

**Any future s-expression tooling in this project must use quote-aware paren counting.**

### Verification

- Netlist: **148 nets before, 148 after, zero differing nets.**
- ERC: 4 unique `(type, uuid)` violation groups, **all four carrying an `excluded` copy →
  0 real ERC items**, unchanged from baseline. No items introduced, none removed.
- Files touched: `01_power_tree.kicad_sch`, `04_spi_b_radios_nfc.kicad_sch` only.

---

## J1 capture batch: SPI-II locked, backlight driver BLOCKED on topology (2026-08-07)

Sources read this pass, all fetched fresh and quoted directly:
`SPEC-CH280QV10-CT_Rev.D.pdf` (18 p), FCI `62684.pdf` (14 p, Rev E, sheet 3 of 3),
TI `tps61169.pdf` (SNVSA40B, Oct 2014 – **rev. June 2024**, 24 p).

### 1. Serial mode — LOCKED, IM3:IM0 verified from the datasheet table

Page 6 "4. Interface Description" mode table, transcribed for the two SPI-Ⅱ rows:

| IM3 | IM2 | IM1 | IM0 | Interface mode | DB Pin |
|---|---|---|---|---|---|
| 1 | 1 | 0 | 1 | 3-wires_9-bit SPI Ⅱ | /CS, SDI, SDO, SCL |
| **1** | **1** | **1** | **0** | **4-wires_8-bit SPI Ⅱ** | **/CS, RS, SDI, SDO, SCL** |

**LOCKED: IM3:IM0 = 1 1 1 0** → 4-wire 8-bit SPI Ⅱ, which is the only 4-wire mode that
exposes **SDO**. Straps: **IM3 (pin 9) HIGH, IM2 (pin 8) HIGH, IM1 (pin 7) HIGH, IM0 (pin 6)
GND.** Read from the table, not from memory. (For the record, 4-wire SPI **Ⅰ** is `0110` and
omits SDO — rejected, as instructed.)

### 2. Backlight — all three §3 preconditions CHECKED

| Check | Result |
|---|---|
| Is 80 mA **total**, not per-LED? | **YES — total.** Page 11 §8 gives *one* `Vf` of 2.9/3.2/3.5 V for the whole module with test condition `If=80mA`, and `If` typ **80 mA** as the module supply current. Four parallel white LEDs at ~20 mA each. |
| Is LEDK the common return? | **YES.** Page 6 lists exactly **one** cathode pin (1 `LEDK`) against **four** anode pins (2–5 `LED-A1..A4`) — the cathodes are commoned inside the module. |
| May LED-A1..A4 be tied to the driver's boosted output? | **Electrically yes, but NOT to a TPS61169 boost output at +3V3 in — see below.** |

A consequence worth stating plainly: because the four cathodes are commoned internally, the
LEDs **cannot be placed in series**. The panel mandates a ~3.2 V parallel array.

### 3. BLOCKER — TPS61169 boost cannot regulate this panel from +3V3

TI's own typical application (Figure 7-1) is **"10 LEDs in Series"** — `10s1p`, 20 mA,
RSET 10.2 Ω, driving roughly 32 V out of a 2.7–5.5 V input. That is a real step-up. Our load is
the opposite case: **one LED deep**, 3.2 V, from a 3.3 V rail.

With the four anodes tied **directly** to the boost output, the converter must produce
`Vout = Vf + VFB` where `VFB = 204 mV`:

| Case | Vf | Vout required | Verdict at VIN = 3.3 V |
|---|---|---|---|
| Vf **min** | 2.9 V | **3.104 V** | **IMPOSSIBLE — below VIN.** A boost cannot output under its input. |
| Vf **typ** | 3.2 V | 3.404 V | duty **3.06 %** → **25 ns** on-time at 1.2 MHz |
| Vf **max** | 3.5 V | 3.704 V | duty 10.9 % → 91 ns |

So across the panel's *own* stated Vf tolerance the design runs from **completely unregulated**
(low end — output pinned near `VIN − Vd`, LED current set by nothing but resistance) to a
**25 ns commanded on-time** at nominal, which is at or below the minimum controllable on-time
for a 1.2 MHz converter and will pulse-skip. **This is not a viable operating point.**
The RSET portion is therefore **STOPPED and reported**, exactly as §3 directs.

### 4. Recommended resolution — keeps the TPS61169 lock intact

Give each anode its own **ballast resistor** so the boost output rises to a voltage it can
actually regulate. The feedback loop still regulates *total* current through RSET, and the
ballasts additionally enforce current sharing between the four LEDs.

With **R_ballast = 39 Ω per anode** (4 off), `Vout = Vf + 0.020×39 + 0.204`:

| Vf | Vout | Duty | On-time |
|---|---|---|---|
| 2.9 V | 3.884 V | 15.0 % | 125 ns |
| 3.2 V | 4.184 V | 21.1 % | 176 ns |
| 3.5 V | 4.484 V | 26.4 % | 220 ns |

Comfortably regulatable across the **entire** Vf band. Cost: **62 mW** in the ballasts against
256 mW of useful LED power. A lower ballast value trades efficiency for regulation margin.

**This is a proposal, not an applied change** — adding four resistors alters the locked
backlight architecture, so it needs approval before capture.

### 5. RSET — calculated, held pending §4 above

Datasheet Equation 1, `RSET = 204 mV / I_LED`. **Validated against TI's own example**: 10 LEDs
at 20 mA → 204 mV / 20 mA = **10.2 Ω**, which is exactly the value printed in Figure 7-1.

For AQROOT at **80 mA total**: `RSET = 204 mV / 80 mA =` **2.55 Ω** (E96, 1 %), dissipating
**16.3 mW** — a 0603 is ample. **Not locked**, because it is only correct once §3/§4 is settled.

### 6. Support components — from the TI datasheet, requirements not invented MPNs

| Part | Datasheet basis |
|---|---|
| **Schottky D** | TI names **ONSemi NSR0240** explicitly. Reverse breakdown must exceed the open-LED protection voltage (device is rated to a 40 V switch / 38 V string). |
| **Inductor L** | §7.2.2.1 recommends **4.7 µH–10 µH**, 4.7 µH for higher inputs. TI lists Coilcraft LPS4018-472ML and Cyntec PCMB051H-4R7M — both 4×4 mm+ parts sized for their 32 V/20 mA example. At our operating point the computed inductor DC current is only ~120 mA with ~125 mA ripple, so a far smaller 4.7 µH part suffices. **A specific MPN is deliberately not named** — it must clear the vendor-verification policy first. |
| **CIN** | 4.7 µF (Figure 7-1). |
| **COUT** | §7.2.2.3: **1 µF–4.7 µF** ceramic; ESR ripple negligible. **Voltage rating must be chosen against the open-LED protection voltage, not against the ~4.2 V normal output.** |
| **RSET** | 2.55 Ω, per §5, pending. |

### 7. Connector footprint — X geometry verified, ONE parameter unresolved

FCI `62684.pdf` **sheet 3 of 3**, view *"RECOMMENDED PC BOARD LAYOUT (COMPORNENT SIDE)"* [sic],
Rev E, tolerances ±0.05, dimensions in mm.

**Verified and self-consistent:**

- pitch **0.5 ±0.05**
- contact span **0.5×(n−1) ±0.05** → **24.5 mm** for n = 50
- signal land **0.3 wide × 1.2 long**
- hold-down land **0.9 wide × 2.4 long**
- hold-down X position: inner edge **2.4 mm** and outer edge **3.3 mm** outboard of the
  end-contact centre. These corroborate each other — **3.3 − 2.4 = 0.9**, exactly the stated
  hold-down width — so the X placement is confirmed by two independent readings.

**Unresolved: the Y offset between the signal-land row and the hold-down lands.** The page
carries **no vector geometry** — it is a single 3520×4960 scanned image, confirmed by
`get_drawings()` returning 0 paths — so the dimension leader lines for the vertical `0.8`/`0.9`/
`(0.3)` stack cannot be attributed with certainty at the available scan resolution. Automated
component analysis recovered only text glyphs, not pad outlines.

**The footprint was therefore NOT created.** Everything except one offset is known, but a
connector land pattern with a guessed Y offset is worse than none. This is a single missing
parameter, not a missing document — a cleaner Amphenol-published drawing for `62684-502100`
would close it immediately.

### 8. Touch controller — hardware interface locked, silicon identity VERIFY

Unchanged from the previous pass and re-confirmed: panel datasheet §2 names **CST026**;
Adafruit's material claims FT6236/FT6236U-compatible. **Locked:** the physical interface only —
I²C on 44/45, IRQ 46, reset 47. **VERIFY, not locked:** I²C address, reset polarity/timing, IRQ
polarity, firmware protocol. No hardware is being changed to force an FT6236 assumption.

### 9. Commit gate — J1 correctly NOT committed

Of the §9 gate conditions, "backlight circuit is complete" and "TPS61169 circuit is complete"
both fail on §3, and "connector footprint pads 1–50 map 1:1" fails on §7. Per the gate, **no J1
symbol, footprint or capture commit was made.** No schematic, symbol or footprint file was
modified this pass; this entry is documentation only.

### 10. Verified 50-pin map, ready to apply once unblocked

Confirmed against pages 6–7 in full:

| Pins | Function | Planned AQROOT net |
|---|---|---|
| 1 | LEDK (cathode, common) | backlight return → RSET |
| 2–5 | LED-A1..A4 (anodes) | boost output, via ballasts if §4 approved |
| 6–9 | IM0, IM1, IM2, IM3 | **GND, +3V3, +3V3, +3V3** (= 1110) |
| 10 | /RESET | `DISP_RST_N` |
| 11–14 | VSYNC, HSYNC, DOTCLK, DE | RGB-only, unused in SPI |
| 15–32 | DB17..DB0 | **tie to GND** — datasheet: *"Connect unused pins to GND."* |
| 33 | SDO | `SPI_A_MISO` |
| 34 | SDI | `SPI_A_MOSI` |
| 35 | /RD | MPU-only |
| 36 | /WR_RS | `DISP_DC` |
| 37 | RS_SCL | `SPI_A_SCK` |
| 38 | /CS | `DISP_CS_N` |
| 39 | TE | tearing-effect output, optional |
| 40, 41 | IOVCC | `+3V3` |
| 42 | VCI | `+3V3` |
| 43, 48, 49, 50 | GND | `GND` |
| 44–47 | CTP_SCL, CTP_SDA, CTP_IRQ, CTP_RES | touch I²C + IRQ + reset |

Supply note carried forward: DC characteristics give **IOVCC 1.65 / 1.8–2.8 / 3.3 V** and
**VCI 2.5 / 2.8 / 3.3 V** — `+3V3` sits at the **maximum** of both, with absolute max 4.6 V.

---

## Backlight operating point VALIDATED; J1 connector moved to Hirose FH69 (2026-08-07)

### 1. TPS61169 at the approved ballast operating point — TI-VALID, no restriction found

Checked against `tps61169.pdf` SNVSA40B (rev. June 2024) §5.3 **Recommended Operating Conditions**:

| Parameter | TI limit | AQROOT | Verdict |
|---|---|---|---|
| **VOUT** | **MIN = VIN**, MAX 38 V | 3.884 – 4.484 V vs VIN 3.3 V | **PASS** |
| VIN | 2.7 – 5.5 V | 3.3 V | PASS |
| L | 4.7 – 10 µH | see below | PASS |
| CI | ≥ 1 µF | 4.7 µF | PASS |
| CO | 1 – 10 µF | 1 µF | PASS |
| F_PWM | 5 – 100 kHz | `DISP_BL_CTL` PWM | constrain firmware |
| D_PWM | 1 – 100 % | — | constrain firmware |

**TI's table literally specifies `VOUT` minimum as `VIN`.** This is the decisive line: it confirms
both that the original direct-tie scheme was out of spec (3.104 V required at Vf min, below the
3.3 V input) **and** that the approved ballast topology is inside spec at every Vf. **No TI
restriction invalidates the operating point — the backlight subtask is NOT blocked.**

Two firmware constraints fall out of the same tables and must be honoured by `DISP_BL_CTL`:
PWM must stay **5–100 kHz**, and CTRL low for **> 2.5 ms shuts the device down** (`tSD`). At the
5 kHz floor a 1 % duty gives a 198 µs low time, comfortably clear of that. CTRL logic thresholds
are **VH 1.2 V min / VL 0.4 V max**, so a 3.3 V ESP32-S3 GPIO drives it directly.

### 2. Backlight component selection — from the datasheet, not memory

| Ref | Value | Source |
|---|---|---|
| Ballast ×4 | **39 Ω 1 % 0603** | CTO-approved; 15.6 mW each, well inside 0603 |
| RSET | **2.55 Ω 1 % 0603** | Eq. 1, `204 mV / 80 mA`; **16.3 mW**. Equation validated against TI's own Figure 7-1, where 204 mV / 20 mA = the printed 10.2 Ω |
| L | **4.7–10 µH**; TI Table 7-2 lists Coilcraft **LPS4018-472ML** / **LPS4018-103ML**, Cyntec **PCMB051H-4R7M** / **PCMB051H-100M** | §7.2.2.1 + Table 7-2 |
| D | **ONSemi NSR0240** | TI names this part explicitly in §7.2.2.2 |
| CIN | **4.7 µF** | Figure 7-1 |
| COUT | **1 µF** | Figure 7-1 |

**Computed operating point** (Vout 4.184 V typ, 80 mA, η ≈ 0.85): inductor DC current **≈ 119 mA**,
ripple ≈ 124 mA at 4.7 µH, **peak ≈ 181 mA** — against a **1.2 A minimum** switch current limit,
so enormous margin. TI's listed inductors are sized for their 32 V / 20 mA example and are
oversized here; a smaller 4.7–10 µH part is electrically sufficient but **must clear the
vendor-verification policy before an MPN is locked**.

**COUT and diode voltage rating — design call-out.** §5.5 gives `VOVP_SW` = **36 / 37.5 / 39 V**.
Under an open-LED fault the output rises toward that threshold before the device disables, so
**COUT must be rated for the OVP voltage (50 V), not for the ~4.2 V normal output**, and the
Schottky reverse rating must exceed it — which is exactly why TI specifies the 40 V NSR0240.

### 3. Old FCI/Amphenol 62684 — DROPPED

`62684-50210` / `62684-502100` is **obsolete** and is no longer a Beta candidate. The captured
sheet-3 geometry is retained **only as historical evidence** of the panel interface. Its
unresolved hold-down Y offset is now moot.

### 4. Hirose FH69-50S-0.5SH — official data captured

Source: **Hirose FH69 series catalog, Jun. 2025 issue** (`en_FH69_CAT`, 16 pp), fetched from
hirose.com. Part **FH69-50S-0.5SH**, **HRS No. CL0580-5008-0-00**, 1,000 pcs/reel.

**Connector dimensions (catalog p.6):** A **29.98**, B **28.7**, C **24.5**, D **25.57**,
height **2.3 ±0.1**, pitch **0.5 ±0.1**, depth 6.95 ±0.1, `8.68 ±0.3` with actuator closed.

**Ratings (p.4):** **0.5 A** per contact, **50 V AC/DC**, −55 to +125 °C, contact resistance
50 mΩ initial, **mating durability 10 cycles**, insulation case LCP, contact copper alloy
partially gold plated, retention tab brass. Halogen-free.

### 5. Panel ↔ FH69 compatibility — PASS on every checkable item

| Check | Panel CH280QV10-CT Rev.D | Hirose FH69-50S-0.5SH | Result |
|---|---|---|---|
| Contacts | 50 | 50 | **PASS** |
| Pitch | 0.5 mm | 0.5 ±0.1 mm | **PASS** |
| Contact span | 0.5 × (50−1) = **24.5 mm** | **C = 24.5 mm** | **PASS — exact** |
| FPC thickness | — (to confirm from the panel's own FPC drawing) | **t = 0.3 ±0.05, gold plated** | consistent with the class; **VERIFY** against panel FPC |
| Contact side | single-sided FPC | **top *and* bottom 2-point contact** | **PASS** — accepts either side, this is the tolerance the FH69 buys |
| Current | 80 mA on LEDK, 20 mA per anode | **0.5 A per contact** | **PASS**, 6× margin on the worst contact |
| Voltage | ≤ 4.5 V | 50 V | **PASS** |
| Insertion | — | 10° upward insertion, back-flip actuator, opens delivered | mechanical clearance is a **floorplanning** constraint |

The `C = 24.5 mm` match is exact and is the single most important number: the panel's contact
span and the connector's contact span are the same value from two independent documents.

**Still to confirm before the footprint is classified VERIFIED_VENDOR_EXACT:** the panel FPC's
own thickness and tail/stiffener dimensions, which the panel datasheet does not state in the
pages read. Hirose additionally requires a **glass-epoxy stiffener ≥ 0.3 mm** on the FPC.

### 6. FH69 recommended PCB layout — fully dimensioned

From catalog **p.7 "Recommended PCB Layout"**, with the n-dependent values taken from the
official table rather than measured:

| Feature | Value |
|---|---|
| Pitch | **0.5** |
| Signal land | **0.3 ±0.03** wide × **1.23 ±0.03** long |
| Contact span **C** (n=50) | **24.5** |
| Hold-down land | **0.36 ±0.03** wide × **4.25 ±0.03** long |
| Hold-down span **E** (n=50) | **28.73 ±0.05** |
| Overall vertical span | **7.38 ±0.05** |
| Positional tolerance | ⌖ 0.05 to datum Z, nX |
| Metal mask | dedicated table, recommended thickness **t = 0.12** |

**The vertical stack closes exactly**, which is a strong self-check on the reading:
`1.23 (signal land) + 1.90 (gap) + 4.25 (hold-down) = 7.38` ✓ — so the signal row and hold-down
rows are separated by a **1.90 mm** clear gap, with no ambiguity left of the kind that defeated
the obsolete FCI scan.

**One item deliberately left open:** whether **E** is measured **outer-to-outer or
centre-to-centre** of the hold-down lands. The dimension arrows fall very close to the land
centres, favouring centre-to-centre, but "very close" is not verification, and the two readings
differ by 0.36 mm. **The footprint was therefore not generated this pass** — this is a
single, cleanly-stated question against a page that is otherwise fully dimensioned, and Hirose
publishes both a 2D drawing and a downloadable footprint for `CL0580-5008-0-00` that settle it
outright.

Note also from p.3/p.7: *"FH69 has a dedicated land pattern; however, the land patterns of the
0.5 mm pitch standard products FH28/FH28K/FH52E/FH52K/FH52T/FH75 can also be used with FH69."*

### 7. Status of the four planned commits

| # | Commit | State |
|---|---|---|
| 1 | TPS61169 backlight driver | **UNBLOCKED** — operating point validated, values fixed; capture pending |
| 2 | 50-pin display symbol | pin table verified and ready; not yet built |
| 3 | Hirose FH69 footprint | blocked only on the **E** datum question above |
| 4 | Complete display interface | gated on 1–3 |

No schematic, symbol or footprint file was modified this pass. ERC, exclusions and netlist are
unchanged. `IM3:IM0 = 1110` (4-wire 8-bit SPI Ⅱ) and the full 50-pin map recorded earlier remain
valid and are unaffected by the connector change.

---

## J1 connector footprint LOCKED: Hirose FH69-50S-0.5SH (2026-08-08)

`AQROOT_Beta:Hirose_FH69-50S-0.5SH` created. Classification **VERIFIED_VENDOR_EXACT** for the
land geometry.

### Manufacturer sources used

Retrieved from Hirose's own document endpoint for **CL0580-5008-0-00**:

| Document | Detail |
|---|---|
| **2D drawing** | `documenttype=2DDrawing`, 7 pp, 830 KB |
| **Specification sheet** | `documenttype=SpecSheet`, drawing no. **ELC-399242-00-00**, code CL580 |
| **Series catalogue** | `en_FH69_CAT`, Jun. 2025 issue, 16 pp — carries the dimensioned *Recommended PCB Layout* |

### E resolved — centre-to-centre, not hand-derived

The prior pass left one question: is `E = 28.73` outer-to-outer or centre-to-centre? **Resolved
from the manufacturer drawing itself, two independent ways:**

1. Rendered at 1200 dpi, the **E extension line coincides exactly with the hold-down land's
   dash-dot centreline** (land edges at 155/240 px, centreline *and* dimension arrow both at
   ~200 px). A centreline is drawn there precisely because it is the dimension reference.
2. Connector dimension **B = 28.7** (retention-tab centres, catalogue p.6) agrees with
   **E = 28.73** only on a centre reference; outer-to-outer would put E at ~29.09.

### Final pad coordinates (mm, origin = centre of the contact field)

| Feature | Value |
|---|---|
| Signal pads | **50**, `0.30 × 1.23`, pitch **0.5**, span **24.5** |
| Pin 1 | **x = +12.25** — matches the *"Contact No.1"* callout on the manufacturer drawing |
| Pin 50 | x = −12.25 |
| Signal row | centred on **y = 0** |
| Hold-downs | `0.36 × 4.25`, at **x = ±14.365**, **y = +4.64** |
| Gap, signal → hold-down | **1.90** |
| Overall depth | **7.38** — stack closes exactly: `1.23 + 1.90 + 4.25` |
| Courtyard | ±15.24 × (−1.75 … +8.30), covering the **8.68 ±0.3** actuator-closed envelope |
| Metal mask | recommended thickness **t = 0.12** |

Hold-downs are **mechanical only** — unnamed pads, deliberately not a ground connection, so they
demand no symbol pin. Verified after generation: 50 contiguously-numbered signal pads, single
pitch value 0.5, span 24.50, uniform 0.3 × 1.23. `kicad-cli fp export svg` plots it, confirming
KiCad parses the file.

### Ratings (specification sheet ELC-399242-00-00)

**0.50 A** and **50 V AC/DC** per contact; applicable FPC/FFC **t = 0.30 ±0.05 mm, gold plated**;
FPC retention force 25.5 N min; **10 insertion cycles**; contact resistance 50 mΩ initial.
Worst-case AQROOT contact is LEDK at 80 mA → **6× margin**.

### Panel FPC thickness — VERIFY (not fabricated)

`SPEC-CH280QV10-CT_Rev.D.pdf` was searched in full for FPC thickness, stiffener thickness and
tail cross-section: **all 18 pages text-searched** for `FPC`/`flex`/`thick`/`stiffen`/`reinforc`/
`t=`, plus inspection of the pages flagged as dimensional (3, 5, 13, 15) and page 18. The only
matches are supply-voltage `−0.3` values; page 18 is the packing method, not a mechanical
drawing. **The panel datasheet does not state its FPC tail thickness.**

Per instruction, **no value was invented**. This single mechanical point is **VERIFY**:
confirm the panel FPC tail is **0.30 ±0.05 mm** before the connector is finally committed.
Hirose additionally requires a **glass-epoxy stiffener ≥ 0.3 mm**. Because FH69 is
top-and-bottom 2-point contact, **contact-side orientation is explicitly not a blocker** — only
thickness is.

### Obsolete part

FCI/Amphenol `62684-50210` / `62684-502100` remains **dropped**; its geometry is retained only as
historical evidence and its unresolved hold-down offset is moot.

---

## J1 pin disposition table — all 50 contacts accounted for (2026-08-08)

Symbol `AQROOT_Beta:CH280QV10_CT_50P` + footprint `AQROOT_Beta:Hirose_FH69-50S-0.5SH`.
Mode **4-wire 8-bit SPI Ⅱ, IM3:IM0 = 1110**. **No unexplained pin.**

| Pin(s) | Name | Disposition | Net / state |
|---|---|---|---|
| 1 | LEDK | **BACKLIGHT** | common cathode → RSET (2.55 R) → GND, TPS61169 FB sense |
| 2–5 | LED-A1..A4 | **BACKLIGHT** | each via its own **39 R 1 %** ballast to the boosted LED rail |
| 6 | IM0 | **MODE_STRAP** | **GND** |
| 7, 8, 9 | IM1, IM2, IM3 | **MODE_STRAP** | **+3V3** (HIGH) |
| 10 | /RESET | **ACTIVE_SIGNAL** | `DISP_RST_N` |
| 11–14 | VSYNC, HSYNC, DOTCLK, DE | **DATASHEET_REQUIRED_INACTIVE** | **GND** — RGB-interface inputs, unused in SPI (see caveat) |
| 15–32 | DB17..DB0 | **DATASHEET_REQUIRED_INACTIVE** | **GND** — datasheet p.6 states verbatim *"Connect unused pins to GND."* |
| 33 | SDO | **ACTIVE_SIGNAL** | `SPI_A_MISO` — the readback that mandates SPI Ⅱ |
| 34 | SDI | **ACTIVE_SIGNAL** | `SPI_A_MOSI` |
| 35 | /RD | **DATASHEET_REQUIRED_INACTIVE** | **+3V3** (HIGH = inactive; see caveat) |
| 36 | /WR_RS | **ACTIVE_SIGNAL** | `DISP_DC` |
| 37 | RS_SCL | **ACTIVE_SIGNAL** | `SPI_A_SCK` |
| 38 | /CS | **ACTIVE_SIGNAL** | `DISP_CS_N` |
| 39 | TE | **DATASHEET_REQUIRED_INACTIVE** | **no_connect** — tearing-effect *output*, unused; floating an output is safe |
| 40, 41 | IOVCC | **POWER** | `+3V3` |
| 42 | VCI | **POWER** | `+3V3` — permitted, DC characteristics give VCI 2.5 / 2.8 / **3.3 max** |
| 43, 48, 49, 50 | GND | **GND** | `GND` |
| 44–47 | CTP_SCL, CTP_SDA, CTP_IRQ, CTP_RES | **ACTIVE_SIGNAL** | touch I²C + IRQ + reset |

**Tally: 5 BACKLIGHT + 4 MODE_STRAP + 10 ACTIVE_SIGNAL + 24 DATASHEET_REQUIRED_INACTIVE +
3 POWER + 4 GND = 50.**

### Two honest caveats on the "required inactive" states

The datasheet's explicit *"Connect unused pins to GND"* sentence sits inside the **DB17:0 block
only**. It therefore directly authorises pins 15–32 and nothing else. The other two entries are
**derived, not quoted**, and are flagged so they are not mistaken for datasheet instructions:

- **Pins 11–14** (VSYNC/HSYNC/DOTCLK/DE) are RGB-interface *inputs* that are unused in SPI mode.
  Unused CMOS inputs must not float, and GND is the conventional inactive level — but the
  datasheet does not say so for these pins specifically.
- **Pin 35 (/RD)** is described as *"Reads strobe signal … when /RD is 'Low'"*, i.e. **active
  low**, so the inactive state is **HIGH**. That is inference from the pin description, not an
  explicit instruction. Tying /RD to GND would assert it permanently and must be avoided.

Both should be confirmed against ILI9341V application material before fabrication. They are
recorded here so the reasoning is auditable rather than buried.

### Supply headroom, carried forward

`+3V3` sits at the **maximum** of both rated ranges — IOVCC 1.65 / 1.8–2.8 / **3.3**, VCI 2.5 /
2.8 / **3.3** — with absolute max 4.6 V. Legal, but with no tolerance margin.

---

## J1 inactive-pin states VERIFIED from ILI9341 documentation (2026-08-08)

Source: **ILI9341 datasheet** (Ilitek, 245 pp), pin descriptor table pp. 10–12 and the serial
interface section p. 33. This closes Task 1 and **supersedes the "derived, not quoted" caveats**
recorded in the previous disposition table — every state below is now a datasheet quotation.

| Pin | Name | Datasheet statement | Required state |
|---|---|---|---|
| 11 | VSYNC | RGB-interface input, table notation `(VDDI/VSS)`, *"Fix to VDDI or VSS level when not in use."* | **GND** |
| 12 | HSYNC | as above | **GND** |
| 13 | DOTCLK | *"Dot clock signal for RGB interface operation. **Fix to VDDI or VSS level when not in use.**"* | **GND** |
| 14 | DE | *"Data enable signal for RGB interface operation. **Fix to VDDI or VSS level when not in use.**"* | **GND** |
| 35 | /RD (RDX) | *"Serves as a read signal and MCU read data at the rising edge. **Fix to VDDI level when not in use.**"* | **HIGH → +3V3** |
| 39 | TE | *"…activated by S/W command. When this pin is not activated, this pin is low. **If not used, open this pin.**"* | **NC / open** |
| 15–32 | DB17..DB0 | p.33: *"The data bus (D [17:0]), which are not used, **must be connected to GND**."* | **GND** |

### Three corrections this forces

1. **/RD must go HIGH, and only HIGH.** The datasheet says *"Fix to **VDDI** level"* — **not**
   "VDDI or VSS" as it does for the RGB pins. Grounding /RD would be wrong. The previous pass
   reached HIGH by inference from active-low naming; that inference happened to be right, but it
   is now backed by an explicit instruction, and the asymmetry against pins 11–14 is real and
   deliberate.
2. **TE is `OUTPUT_UNUSED_NC`, not `DATASHEET_REQUIRED_INACTIVE`.** Leaving it open is
   **datasheet-mandated** (*"If not used, open this pin"*), not merely tolerated because it is an
   output. It gets its own disposition category.
3. **Pins 11–14 are confirmed GND-legal.** The prior entry noted only that unused CMOS inputs
   must not float, flagging GND as convention rather than instruction. It is now an instruction —
   and note the datasheet permits **either** rail for these four, so GND is a choice, made for
   consistency with the DB bus which has no such latitude.

### Revised disposition tallies

`ACTIVE_SIGNAL 10 · POWER 3 · GND 4 · MODE_STRAP 4 · BACKLIGHT 5 ·
DATASHEET_REQUIRED_INACTIVE 23 · OUTPUT_UNUSED_NC 1` = **50**.

(Previously 24 / 0; TE moves out of `DATASHEET_REQUIRED_INACTIVE` into `OUTPUT_UNUSED_NC`.)

**Wiring is no longer gated on pin-state uncertainty.** Every one of the 50 contacts now has a
state traceable to either the CH280QV10-CT panel datasheet or the ILI9341 controller datasheet.

---

## J1 physical capture + TPS61169 backlight COMPLETE (2026-08-08)

Sheet `03_spi_a_display_sd.kicad_sch`. Paper A4 to **A3** to fit the 66 mm-tall 50-pin symbol.

### Backlight components — exact MPNs

| Ref | Part | Key data | Footprint / source |
|---|---|---|---|
| U17 | **TI TPS61169DCKR** | SC70-5 (DCK) | `Package_TO_SOT_SMD:SOT-353_SC-70-5`, **VERIFIED_IPC_ALTERNATE** |
| L3 | **Coilcraft XFL4020-472MEC** | 4.7 µH ±20 %, **Isat 2 A**, Irms 5 A, DCR 0.05 Ω max, 4.0×4.0×2.1 mm, AEC-Q200 | reuses **existing VERIFIED_VENDOR_EXACT** `AQROOT_Beta:Coilcraft_XFL4020`, shared with L1 |
| D8 | **onsemi NSR0240V2T5G** | SOD-323, 40 V, 250 mA avg | TI section 7.2.2.2 names NSR0240 explicitly |
| C43 | 4.7 µF **16 V X7R 0805** | CIN | 16 V/0805 over 6.3 V/0603 so effective C survives 3.3 V DC bias |
| C44 | 1 µF **50 V X7R 0805** | COUT | rating set by **VOVP_SW 36/37.5/39 V**, not the 4.2 V output |
| R69 | **2.55 Ω 1 % 0603** | RSET | 204 mV / 80 mA; 16.3 mW |
| R70–R73 | **39 Ω 1 % 0603** x4 | ballast, one per anode | 20 mA, 0.78 V, 15.6 mW each |

**L3 is deliberately oversized** — Isat 2 A against a calculated 181 mA peak, roughly 11x margin.
Accepted in order to reuse an already-verified land pattern and consolidate on one inductor
family with L1. A compact 2.5x2.0 mm-class 4.7 µH part remains a valid future substitution,
subject to vendor verification.

### Verified topology — read back from the netlist, not from intent

    BL_SW       = U17.1 (SW) + L3.2 + D8.2 (anode)
    LED_BOOST   = D8.1 (cathode) + C44.1 + R70.1 + R71.1 + R72.1 + R73.1
    LED_A1..A4  = J1.2 / J1.3 / J1.4 / J1.5, each with exactly ONE ballast
    LED_K       = J1.1 + R69.1 + U17.3 (FB)
    DISP_BL_CTL = U1.24 + U17.4 (CTRL)        <- GPIO carries no LED current

The four anode branches are independent after their ballasts. Nothing connects to `NFC_5V_PA`,
`TPS61023` or `BAT_PROTECTED_P`.

**Firmware constraints**, confirmed from TI sections 5.3 and 6.4.1: PWM **5–100 kHz**, duty
1–100 %, and **CTRL held low longer than 2.5 ms (`tSD`) shuts the driver down**. CTRL thresholds
are VH 1.2 V min / VL 0.4 V max, so a 3.3 V ESP32-S3 GPIO drives it directly.

### Final 50-pin disposition — every contact accounted for

`BACKLIGHT 5 · MODE_STRAP 4 · ACTIVE_SIGNAL 9 · DATASHEET_REQUIRED_INACTIVE 23 · POWER 3 ·
GND 4 · OUTPUT_UNUSED_NC 1 · unrouted 1` = **50**

Straps confirmed in the netlist: **6 to GND, 7/8/9 to +3V3 = IM3:IM0 1110**. `/RD` (35) to
**+3V3**. DB17:0 (15–32) to **GND**. TE (39) **open**. 40/41/42 to +3V3; 43/48/49/50 to GND.
Signals: 10 `DISP_RST_N`, 33 `SPI_A_MISO`, 34 `SPI_A_MOSI`, 36 `DISP_DC`, 37 `SPI_A_SCK`,
38 `DISP_CS_N`, 44 `I2C_SCL_INT`, 45 `I2C_SDA_INT`, 47 `TOUCH_RST_N`.

### FINDING — the touch interrupt has no net anywhere in the design

**Pin 46 `CTP_IRQ` is an explicit no-connect, and this needs a decision.** The old 13-pin
placeholder's `CTP_INT_N` pin had **no wire and no hierarchical label** — it carried a bare
no-connect. A project-wide search found **no touch-IRQ net at all**, only `NFC_IRQ` and
`ROOTPROBE_IRQ_READY_N`. Wiring it would require assigning a new MCU pin, which is explicitly
forbidden, so existing behaviour was preserved rather than invented over.

**Consequence: capacitive touch is polling-only** — no interrupt-driven wake on touch. That is a
real functional limitation that the 13-pin placeholder was hiding. Resolving it needs a free GPIO
on U1 or the expander, i.e. an MCU pin-map decision.

### Validation

Netlist **148 to 155 nets**, the seven additions being `BL_SW`, `LED_BOOST`, `LED_K` and
`LED_A1..A4`. **Zero unrelated net-membership changes.** ERC **4 groups, all excluded, 0 real
items**. SPI bus intact and unshorted — SCK, MOSI and MISO each carry exactly `J1 + J2 + U1` —
and SCL/SDA remain distinct. No placeholder remains anywhere in the project. Footprint coverage
**156 of 176, 20 missing**; J1 has closed.

### Capture note worth keeping

The SW node was first built as pin-wire-wire-pin with a junction. KiCad refused to bind it and
ERC reported both wires dangling, even though every coordinate verified correct against the
cached symbol definitions in the sheet. Rebuilding it as three label-coupled stubs (`BL_SW`) —
the pattern already proven elsewhere on this sheet — binds correctly. **Future generated capture
in this project should prefer label coupling over multi-wire junctions.**

---

## Pre-layout blocker register + two decisions LOCKED (2026-08-08)

### Decision 1 — backlight inductor L3 LOCKED as-is

**L3 = Coilcraft XFL4020-472MEC stays for Beta.** It is electrically oversized (Isat 2 A against
a ~181 mA peak) and that is **accepted**: the `AQROOT_Beta:Coilcraft_XFL4020` land pattern is
already VERIFIED_VENDOR_EXACT and shared with L1, the part is electrically safe, and no new
footprint verification is required. **Do not replace it for optimisation alone.** Size/cost
optimisation is deferred unless PCB placement proves the 4.0 x 4.0 mm body is a real constraint.

### Decision 2 — touch IRQ intentionally not connected

> **Beta touch controller uses polling over I2C; CTP_IRQ intentionally not connected. IRQ
> allocation deferred unless firmware testing demonstrates a need.**

J1 pin 46 `CTP_IRQ` remains NC for Beta. The previous 13-pin abstraction never connected the
interrupt, no MCU GPIO is allocated to it, and no GPIO may be reassigned without reopening the
locked pin map. **This is an intentional NC and must not be treated as an ERC defect** — it is
carried by an explicit `no_connect` flag, which is exactly why ERC stays at 0 real items rather
than raising a warning.

### SW9 CLOSED — footprint assigned and verified

`Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN` assigned. **VERIFIED_VENDOR_EXACT.**

Verified against the C&K JS-series drawing, page 4, *"RIGHT ANGLE SURFACE MOUNT / PCB MOUNT —
HOLE LAYOUT"* for JS102011SAQN:

| Feature | C&K drawing | KiCad footprint | Result |
|---|---|---|---|
| Terminal pitch | **2.5 TYP** | 2.5 (x = −2.5, 0, +2.5) | **exact** |
| Locating holes | **2 × ⌀0.9, span 6.8** | 2 × NPTH ⌀0.9 at x = ±3.4 | **exact** |
| Land width | **1.2 TYP** | 1.25 | +0.05 (fillet allowance) |
| Terminals | 3 (SPDT) | 3 lands | **exact** |

The mechanically critical features — hole diameter, hole span and pitch — match exactly; only the
land width carries a 0.025 mm per-side solder-fillet allowance, which is documented rather than
glossed. Rating 6 VDC / 0.3 A, 5000 cycles. Pole mapping unchanged (KiCad pin 2 = C&K terminal 2
= COMMON). **No electrical wiring changed** — netlist verified identical, 155 nets before and
after.

### J3 status — NOT missing, confirmed

J3 already carries `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` with
MPN `USB4105-GF-A-120`. It is **assigned but UNVERIFIED** — the variant suffix and shell-stake
configuration at the locked 1.6 mm board thickness are still unconfirmed against the GCT drawing.
**UNVERIFIED is a separate axis from MISSING**; J3 correctly does not appear in the missing count.

### Remaining blocker register

| Ref | MPN / value | Symbol | Footprint | Classification | Next prerequisite |
|---|---|---|---|---|---|
| J2 | Molex 5025700893 | `Connector:Micro_SD_Card` (9 pins) | none | **BLOCKED_EXTERNAL_DOCUMENT** | Molex drawing; then audit 8 contacts + CD switch + shell vs the 9-pin symbol |
| LS1 | Same Sky CMS-1535-058SP | generic speaker | none | **BLOCKED_EXTERNAL_DOCUMENT** | vendor pad geometry, or a 15 mm/8 Ω/≥0.5 W replacement that publishes lands |
> **CORRECTED 2026-08-08 — the row below transposed U7/U8. The schematic is authoritative: U7 = E07-400M10S (CC1101), U8 = E22-900M22S (SX1262).**
> | U7 | Ebyte E22-900M22S | `SX1262_MODULE_PLACEHOLDER` | none | **BLOCKED_SYMBOL_MISMATCH** | Ebyte drawing + full physical-pin audit (VCC, all GND, NSS, SCK, MOSI, MISO, BUSY, DIO1, NRST, RXEN, TXEN) |
> | U8 | Ebyte E07-400M10S | `CC1101_RADIO_PLACEHOLDER` | none | **BLOCKED_SYMBOL_MISMATCH** | Ebyte drawing + audit (VCC, all GND, CSN, SCK, MOSI, MISO/GDO1, GDO0, GDO2, antenna pad) |
| U9 | ST ST25R3916-AQET | `ST25R3916_NFC_PLACEHOLDER` | none | **BLOCKED_SYMBOL_MISMATCH** | ST EDA asset; 32-pin + exposed-pad audit. Do not force UFQFPN onto the abstraction |
| U12 | TI TPS63020DSJR | real symbol | none | **BLOCKED_EXTERNAL_DOCUMENT** | TI DSJ package drawing. Power VSON/thermal — no generic approximation |
| U14 | ADI MAX17048G+T10 | real symbol | none | **BLOCKED_EXTERNAL_DOCUMENT** | Maxim/ADI land pattern 90-0065. Rule not to be compromised |
| C12 | **TBD** | `Device:C` | none | **DESIGN_DECISION_BLOCKED** | IR drive-current design unresolved; value still literally `TBD` |
| R24 | **TBD** | `Device:R` | none | **DESIGN_DECISION_BLOCKED** | as C12 |
| C18 | `100nF_PLACEHOLDER` | `Device:C` | none | **DESIGN_DECISION_BLOCKED** | NFC/RF function unproven; must not become a real BOM line without proof |
| C19 | `100nF_PLACEHOLDER` | `Device:C` | none | **DESIGN_DECISION_BLOCKED** | as C18 |
| SW1 | BOOT | `Switch:SW_Push` | none | **MECHANICAL_DECISION_BLOCKED** | maintenance button — internal vs accessible, recessed or not |
| SW2–SW8 | UP, DOWN, LEFT, RIGHT, A_SELECT, B_BACK, HOME | `Switch:SW_Push` | none | **MECHANICAL_DECISION_BLOCKED** | actuator height/travel/force + mounting style |

### Why SW1–SW8 are mechanically blocked, specifically

`15 - Enclosure Field Slate v3` **does** fix the button set — *"Physical controls: 7 buttons —
D-pad (up/down/left/right), A = select/confirm"*, plus B = back and Home, matching SW2–SW8, with
SW1 as a separate BOOT/maintenance button. It also sets a usability bar: the device must stay
*"fully drivable with gloves, in the dark"*.

What it does **not** fix is anything that actually selects an MPN: **actuator height above PCB,
travel, operating force, and mounting style** (top-actuated under a membrane/keypad vs
side-actuated, SMD vs through-hole). Those follow from the enclosure stack-up and the front-panel
design, neither of which is locked. A glove-operable button in the dark implies a specific force
and travel envelope — picking a generic 4.5 mm tactile switch now would silently pre-empt that.

**One MPN plausibly covers SW2–SW8** (identical role, identical panel), but **SW1 is likely a
different part** (maintenance access, probably recessed or internal). That split should be
confirmed, not assumed.

### Not attempted this session

J2, LS1, U7, U8, U9, U12, U14 each require a vendor document retrieval plus, for the three RF/NFC
modules, a complete physical-pin audit against a placeholder symbol that is known not to match.
Those were not reached; the session went to the C&K verification that closed SW9, and to the
audits recorded above. **No speculative footprints were created.**

---

## Vendor-document blocker sweep: all seven attempted (2026-08-08)

No schematic, symbol or footprint file was modified. Coverage stays **157/176**, ERC **0 real
items**, 24 exclusions intact, netlist unchanged. Two blockers moved materially; five did not.

| Ref | MPN | Document outcome | Classification |
|---|---|---|---|
| U12 | TPS63020DSJR | **TI land pattern OBTAINED** — drawing `4210895-2/E 02/16` | **DOCUMENT_OBTAINED_FOOTPRINT_PENDING** |
| LS1 | CMS-1535-058SP | **datasheet fully inspected — no land geometry exists** | **EXACT_REPLACEMENT_DECISION_REQUIRED** |
| U14 | MAX17048G+T10 | `90-0065` fetch failed on both Maxim and ADI paths | BLOCKED_EXTERNAL_DOCUMENT |
| U9 | ST25R3916-AQET | st.com datasheet fetch timed out | BLOCKED_EXTERNAL_DOCUMENT |
| J2 | Molex 5025700893 | 3 drawing URL patterns attempted, batch timed out | BLOCKED_EXTERNAL_DOCUMENT |
> | U7 | Ebyte E22-900M22S | not retrieved (batch timeout) | BLOCKED_EXTERNAL_DOCUMENT |  *(refs transposed — see correction 2026-08-08)*
> | U8 | Ebyte E07-400M10S | not attempted after timeout | BLOCKED_EXTERNAL_DOCUMENT |  *(refs transposed — see correction 2026-08-08)*

### U12 — the real win: TI's authoritative DSJ land pattern is in hand

Retrieved from the TPS63020 datasheet (SLVS916I), **page 33**, titled *"LAND PATTERN DATA —
DSJ (R-PVSON-N14) PLASTIC SMALL OUTLINE NO-LEAD"*, drawing number **4210895-2/E 02/16**. The
pages are graphics-only, so this was read by rasterisation.

Captured from *Example Board Layout*, *Example Stencil Design* and *Example Via Layout Design*:

| Feature | Value |
|---|---|
| Pitch | **12 × (0.5)** |
| Row span | **(2.8)** |
| Signal pad geometry | **0.24 × 0.6, R0.12 TYP**, non-solder-mask-defined |
| Solder mask | opening (0.12), **(0.07) all around** |
| Stencil (0.125 mm) | 14×(0.6), 14×(0.24), 8×(0.85), 8×(0.2), 4×(1.25), 4×(0.66), 4×(0.46), 4×(0.23) |
| Thermal pad paste | **81 % solder coverage by printed area** |
| Via layout | (4.4), (2.85), (1.58), **15 × ⌀0.2**, 6×(0.46), 4×(0.23) |

**The footprint was still not built, deliberately.** Two reasons, both concrete:

1. DSJ is **not a plain two-row VSON**. The Example Board Layout shows oval signal pads in top and
   bottom rows *plus* wide horizontal bar lands on the left and right flanks (the L1/L2/VOUT/VIN
   power terminals) around a central thermal pad. The single supplied view **does not dimension
   the position of every one of those lands** — the stencil counts (4×1.25, 8×0.85, 4×0.66 …)
   imply at least four distinct land sizes whose individual coordinates are not given.
2. **No KiCad stock footprint matches.** The available candidates are
   `VSON-14-1EP_3x4.45mm_P0.65mm_EP1.6x4.2mm` (wrong pitch, 0.65 vs 0.5) and
   `WSON-14-1EP_4.0x4.0mm_P0.5mm_EP2.6x2.6mm` (right pitch, but a plain two-row 4×4 body with a
   2.6×2.6 EP — not the flanked DSJ arrangement).

This is a **power VSON with a thermal pad — Class B**, where the standing rule forbids generic
approximation. Constructing it needs the full TI package outline (page 31/32) read alongside this
land-pattern sheet, which is a bounded task now that the document is in hand.

### LS1 — settled definitively: the vendor publishes no land geometry

The Same Sky datasheet (09/11/2024, 4 pp) was retrieved and **inspected in full, including
rasterising the page-2 mechanical drawing**. It gives body **Ø15 × 3.5 mm**, an inner **Ø11**,
a rear view with six vent holes, "BLACK NET" and "BLACK GLUE (118B)" callouts, and a ±0.3 mm
general tolerance. Page 1 lists `terminal: solder pads`.

**The two solder pads are drawn but carry no dimensions at all** — no pad size, no pitch, no
angular position, no keep-out. This is no longer an inference from failed text extraction; the
drawing itself has been looked at. **CMS-1535-058SP cannot be given a vendor-exact footprint.**

Per the standing instruction, the answer is a replacement rather than invented pads. Requirements
for the substitute: **15 mm class, 8 Ω, ≥0.5 W, low profile, solder/SMT PCB mounting, active
production, and a manufacturer drawing that dimensions the PCB lands.** The replacement search
was **not completed this session** — recorded as the next action, and `LS1` keeps
`CMS-1535-058SP` until a substitute is proven electrically and mechanically compatible.

### Retrieval notes for the next session

- `ckswitches.com` returns **403**; the Octopart mirror works (this is how SW9 closed).
- `st.com/resource/...` **times out** — try the ST product page or an EDA-asset mirror instead.
- `pdfserv.maximintegrated.com/land_patterns/90-0065.PDF` and the analog.com land-pattern path
  both fail; ADI's document portal has moved and needs a fresh URL.
- Batch curl of seven vendors **exceeds a 2-minute tool timeout** — fetch in pairs with
  `--max-time 22`, not all at once.

---

## Sequential vendor sweep #2 — J2 audit, U12 near-complete, LS1 candidate ruled out (2026-08-08)

No schematic/symbol/footprint file modified. Coverage stays **157/176**, ERC **0 real**, 24
exclusions intact, netlist unchanged.

### J2 — symbol mismatch now PROVEN, footprint still blocked

Molex direct URLs fail; the **RS-Online mirror** of the Molex part sheet was retrieved. It
confirms: part **Active**, 1.10 mm pitch microSD, **Normal Mount SMT, Push-Push**, **Circuits
(Loaded) = 8**, **Card Detection Switch = Open**, Card Entry = Front, Shielded = Yes, PCB
Retention = Yes, 10 000 mating cycles, 0.5 A/contact, 10 V.

**Audit result — the current symbol is incomplete.** `Connector:Micro_SD_Card` has 9 pins:
`1 DAT2, 2 DAT3/CD, 3 CMD, 4 VDD, 5 CLK, 6 VSS, 7 DAT0, 8 DAT1, SH SHIELD`. That is the 8 SD
contacts plus a shield — and **no terminals for the mechanical card-detect switch**, which this
Molex part physically has. Pin 2 `DAT3/CD` is the *card's data line* used for detection via a
pull-up; it is **not** the connector's CD switch. So the symbol cannot represent the CD switch
contacts, and a footprint carrying CD lands would have no symbol pins to map to.

**Blocker is now precisely named:** Molex sales drawings **SD-502570-001** and **SD-502570-002**
(also referenced: product spec PS-502570-001-001). Those give the CD-switch terminal count and
the land geometry. **BLOCKED_EXTERNAL_DOCUMENT + BLOCKED_SYMBOL_MISMATCH.**

### U12 — one datum from complete

Second TI drawing obtained: **`4208549-3/G 04/15`, "THERMAL PAD MECHANICAL DATA", DSJ
(R-PVSON-N14)**. Adds to the land pattern already held:

| Datum | Value | Source |
|---|---|---|
| Exposed thermal pad | **2.85 ±0.10 × 1.58 ±0.10** | 4208549-3/G |
| Pin arrangement | **1–7 top row, 8–14 bottom row** (bottom view) | 4208549-3/G |
| Pitch | 0.5 (12× callout = 6 gaps per row × 2 rows) | 4210895-2/E |
| Row span | 2.8 centre-to-centre | 4210895-2/E |
| Signal land | 0.24 × 0.6, R0.12, NSMD, mask 0.07 all round | 4210895-2/E |

**The 14 signal lands are now fully determined**: 7 per row, 0.5 pitch → x = 0, ±0.5, ±1.0, ±1.5;
rows at y = ±1.4; each land 0.24 × 0.6.

**Still missing, exactly one datum:** the thermal drawing shows **`4X 0.20` features at `0.46`
spacing** on the package flanks, and the Example Board Layout correspondingly shows wide
horizontal bar lands left and right of centre. **It is not documented whether these are separate
exposed pads, or segments of the single 2.85 × 1.58 thermal pad.** The stencil sheet's
`4×(1.25) / 8×(0.85) / 4×(0.66)` aperture counts hint at the answer, but the standing instruction
is explicit — *do not infer coordinates from stencil aperture counts* — so the footprint was **not
built**. This is Class B; approximation is forbidden.

**Next action:** TI application report **SLUA271** (QFN/SON PCB Attachment), cited in note C of
the land sheet, or the TPS63020 EVM layout, should resolve the flank features.

### LS1 — replacement search started; one candidate definitively ruled out

Confirmed again that **CMS-1535-058SP** publishes no land geometry. Two replacements identified,
both matching the envelope (15 mm class, 8 Ω, ≥0.5 W, ~3 mm — *thinner* than the 3.5 mm original):

| Candidate | Body | Z | Impedance | Power | Land geometry published? |
|---|---|---|---|---|---|
| **PUI Audio AS01508MS-WP** | 15 × 11 | **3 ±0.2** | 8 Ω ±15 % | 1 W rated / 1.5 W max | **NO — ruled out** |
| **Soberton SP-1511-3** | 15 × 11 | 3 | 8 Ω | 0.7 / 1.0 W | **not yet checked** |

The PUI datasheet was retrieved and its page-6 dimension sheet rasterised: it gives 15 × 11 × 3
with ±0.15 mm tolerance and shows the two solder pads as hatched rectangles in the rear view —
**but dimensions none of them**. Identical failure mode to Same Sky. **PUI AS01508MS-WP is
therefore rejected on the same criterion that rejected the original**, despite being otherwise
attractive (IP65, 95 dB, higher power).

Electrically both candidates suit the MAX98357A (8 Ω, ≥0.5 W). **Soberton SP-1511-3 is the
remaining candidate to check**; Soberton publishes per-part drawings, so it is the most likely to
carry dimensioned lands. **LS1 unchanged — no MPN was altered.**

### Unchanged this session

U7, U8 (Ebyte), U9 (ST), U14 (MAX17048 `90-0065`) — not attempted; the session went to J2, U12
and LS1 under the sequential-fetch rule. J3 remains **ASSIGNED_UNVERIFIED** (GCT drawing not
sought this pass).

---

## U12 CLOSED; J2 and LS1 transports still failing (2026-08-08)

### U12 — closed without Ultra Librarian

The stalling datum is resolved. Rasterising TI's *Example Board Layout* at 900 dpi shows the
**4X 0.20 features at 0.46 spacing are slots cut into a SINGLE contiguous thermal land** — a comb
on both flanks of one connected copper area, with the 5x3 grid of 15 vias inside it. They are
**not separate pads**. Ultra Librarian was therefore unnecessary: TI's own package drawing, named
in the brief as the primary source, was sufficient once read at adequate resolution.

`AQROOT_Beta:TI_TPS63020_DSJ` created and assigned, **VERIFIED_VENDOR_EXACT**. Coverage
**157 -> 158 / 176**; missing **19 -> 18**. Netlist unchanged, ERC 0 real.

Two implementation choices are recorded in the footprint description: the comb is not reproduced
(the plain dimensioned 2.85 x 1.58 envelope is used, which is conservative — more thermal copper,
same outline), and paste uses `solder_paste_margin_ratio -0.05`, which KiCad applies per side,
giving 0.9 linear and 0.81 area to match TI's stated 81 % coverage. The 15 x 0.2 mm thermal vias
are a layout task, not part of the footprint.

### J2 — transport failed again, blocker unchanged and precise

The alldatasheet mirror and a second Molex path both failed. The requirement is unchanged and
exactly named: **Molex SD-502570-001 / SD-502570-002**. The symbol gap is already proven — the
stock 9-pin `Connector:Micro_SD_Card` has no terminals for the connector's mechanical
card-detect switch, so both symbol and footprint remain blocked on that one document set.
**BLOCKED_EXTERNAL_DOCUMENT + BLOCKED_SYMBOL_MISMATCH.**

### LS1 — Soberton transport failed; size class now exhausted

`soberton.com` returned no PDF on two direct paths and the product page yielded no PDF link to
scrape. Combined with the two prior negatives — Same Sky **CMS-1535-058SP** and PUI
**AS01508MS-WP**, both of which *draw* their solder pads without dimensioning them — three
15 mm-class candidates have now failed the same test.

Per the brief's own instruction, this size class is marked
**PHYSICAL_SAMPLE_OR_MECHANICAL_DECISION_REQUIRED**. The realistic options are: accept a
documented speaker of a different class, measure a physical sample, or request the drawing from
Soberton/PUI directly. **LS1 keeps CMS-1535-058SP** — no MPN was altered.

### Not reached

U7, U8 (Ebyte), U9 (ST), U14 (`90-0065`) — the session went to J2, U12 and LS1. J3 remains
**ASSIGNED_UNVERIFIED**.

---

## RF/NFC capture session — retrieval route mapped, no capture performed (2026-08-08)

**No schematic, symbol or footprint file was modified.** Coverage stays **158/176**, ERC 0 real,
24 exclusions intact, netlist unchanged. U7/U8/U9 placeholders are untouched and DO NOT ROUTE
stands.

### What was established for U7 (E22-900M22S)

`ebyte.com/product/435.html` **is reachable** (294 KB retrieved) — unlike st.com, molex.com and
soberton.com, which fail at transport. The obstacle here is different and worth recording
precisely: **the page exposes no direct file links.** Scraping yields only
`/datadown/<id>.html` **category** pages (e.g. 915 MHz = `/datadown/1077.html`, 433 MHz =
`/datadown/1081.html`) plus a company-profile PDF. The per-product resources named in the brief
— `Pcb_E22-900M22S`, the user manual — sit **at least two hops deeper**: category page, then
product resource page, then the file.

**This is a navigable route, not a dead end** — materially better than the pure transport
failures. It simply needs the hop chain walked, which is a bounded task for a fresh session.
The same structure will apply to U8 via `ebyte.com/product/1546.html` and the 433 MHz category.

### Why nothing was captured

A physical module capture is not a footprint drop — it requires the **complete pad audit against
the placeholder** that the brief mandates for every pad (VCC, every GND, NSS, SCK, MOSI, MISO,
BUSY, DIO1, NRST, RXEN, TXEN, DIO2/3 for U7; CSN, GDO0/1/2 for U8; 32 pins + exposed pad for U9),
followed by a symbol replacement that must not silently move an existing net. Beginning that with
insufficient budget to finish and verify would risk exactly the half-captured state the brief
forbids — and the project has already been bitten once by a large generated schematic edit that
passed a paren-balance check while being wrong.

### Standing items unchanged

U7/U8 antenna variant control (**IPEX/u.FL must be confirmed for the exact ordered MPN**, not
assumed from family marketing, because the locked Taoglas FXP890/FXP450 flex antennas depend on
it) remains **open and is a procurement-control risk**. U9 remains a logical placeholder; ST's
EDA assets were not retrieved this pass.

---

## U7 E22-900M22S — vendor manual retrieved, pinout verified, RF switch BLOCKED (2026-08-08)

**Retrieval route solved.** The Ebyte product page exposes its resources only via inline links,
not a file listing. Working URLs, recorded for reuse:

- user manual: `https://www.ebyte.com/downpdf/435.html` (PDF, 2.0 MB, 15 pp)
- package file `Pcb_E22-900M22S`: `http://www.ebyte.com/pdf-down/766.html` (**PK/zip magic but
  malformed — will not open; needs a re-fetch or another route**)

### Pinout VERIFIED — and a variant trap avoided

The manual covers several variants with **different pinouts and the same pin count**. Our part is
section **3.2 `E22-170/400/900M22S`**. Two neighbours are dangerous look-alikes:

| Manual section | Part | Pins | Trap |
|---|---|---|---|
| 3.1 | `E22-400/900**MM**22S` | **20** | double-M; the brief already flags it as a different product |
| **3.2** | **`E22-170/400/900M22S`** | **22** | **ours** |
| 3.3 | `E22-170/400/900M30S(33S)` | 22 | same count, but **pin 10 = VCC, not GND**, and VCC is 2.5–5.5 V |

**The 22-pin table supplied in the brief matches section 3.2 exactly** — 1–5 GND, 6 RXEN, 7 TXEN,
8 DIO2, 9 VCC (**1.8–3.7 V**), 10–12 GND, 13 DIO1, 14 BUSY, 15 NRST, 16 MISO, 17 MOSI, 18 SCK,
19 NSS, 20 GND, 21 ANT (stamp hole, 50 Ω), 22 GND. Confirmed, not assumed.

### Placeholder mismatch — 10 pins vs 22

`SX1262_MODULE_PLACEHOLDER` has: 1 VCC_3V3, 2 GND, 3 SCK, 4 MOSI, 5 MISO, 6 CS_N, 7 BUSY,
8 DIO1, 9 RESET_N, 10 RF_ANT.

- **MISSING entirely: RXEN, TXEN, DIO2**
- **MISSING: 9 of 10 physical GND pads** — the placeholder collapses all grounds into one pin
- **Numbering is unrelated to the vendor's** — every pad must be renumbered
- U7 is `on_board no` and **has zero netlist nodes**, so like J1 this is a first-time physical
  capture, not an expansion. The locked nets exist but terminate on the MCU only:
  `SX1262_CS_N` (R27.2, U1.10), `SX1262_BUSY` (U1.12), `SX1262_DIO1` (U1.11),
  `SX1262_RST_N` (R13.1, U2.5), `SPI_B_SCK/MOSI/MISO` (U1.4/5/6).

### RF-switch control — RXEN needs a GPIO that does not exist

Quoting section 3.2 directly:

- **TXEN (7)**: *RF switch **transmit** control, connect to external MCU IO **or DIO2**, active
  HIGH.* Note ①: *if DIO2 and TXEN are shorted, firmware must enable the DIO2 switch-control
  function.* → **TXEN can be solved with no MCU pin at all.**
- **RXEN (6)**: *RF switch **receive** control, **connect to external MCU IO**, active HIGH.*
  **Ebyte offers no DIO alternative for RXEN.**
- **DIO3**: not exposed on the M22S; on the M30S/33S table it is *internal, powering the 32 MHz
  TCXO at 2.2 V*. **It cannot drive RXEN.**

**Conclusion: RF_SWITCH_CONTROL_DECISION_REQUIRED.** RXEN requires a dedicated MCU GPIO;
AQROOT has no `SX1262_RXEN` net and no allocated pin, and the brief forbids taking one
automatically. TXEN/DIO2 is resolvable in firmware. **Both pins will be captured physically and
parked on explicit named nets — U7 must not be described as electrically complete.**
Still to extract: the manual's 表1 (Table 1) giving required TXEN/RXEN states for TX, RX, sleep
and reset.

### Antenna

Manual p4: *dual antenna optional (IPEX / stamp hole)*; p5 lists the interface as **IPEX-1 /
stamp hole**, and pin 21 ANT is the 50 Ω stamp-hole pad. Both appear present on the same MPN.
AQROOT uses **IPEX + Taoglas FXP890.07.0100C**, so **pin 21 ANT is expected to stay NC** — but
whether both feeds are simultaneously populated, and whether that loads the RF path, is **not yet
confirmed** and is an RF-review plus procurement-control item.

---

## U7 RXEN architecture analysis — NO free GPIO exists (2026-08-08)

Read-only analysis. Nothing modified.

### Task 1 — candidate audit, taken from the netlist not the doc

| Candidate | Current function | Free? | Verdict |
|---|---|---|---|
| **U1 pin 28 / IO35** | unconnected in netlist | **NO** | GPIO 26–37 consumed by octal PSRAM/flash |
| **U1 pin 29 / IO36** | unconnected in netlist | **NO** | as above |
| **U1 pin 30 / IO37** | unconnected in netlist | **NO** | as above |
| U1, all other pins | 38 assigned functions | NO | pin map: *native budget is CLOSED via the GPIO43 multiplex, not by having spare pins* |
| **U2 TCA9535** | **16/16 I/O used** | **NO** | 4 resets (touch, SX1262, NFC 5V EN, display), amp SD, RGB ×3, 7 buttons, RootProbe IRQ |
| **U3 TCA9535** | **16/16 I/O used** | **NO** | XGPIO0–14 (community header) + ACC_PWR_EN |

**The three unconnected ESP32 pins are a trap.** They are unconnected *because they must be*:
U1 is **ESP32-S3-WROOM-1 N16R8**, and the pin map states *"GPIO 26-37 consumed by octal
PSRAM/flash (R8). Excluded."* Wiring RXEN there would collide with the PSRAM bus.

**Conclusion: there is no free controllable output anywhere in the design.**

### Task 2 — timing

**Ebyte publishes no timing figures.** What it does publish is 表1, the RF-switch control logic
truth table (manual p.10):

| TXEN | RXEN | MODE |
|---|---|---|
| 1 | 0 | TX |
| 0 | 1 | RX |
| 0 | 0 | CLOSE |

Two things follow directly, and the second is a hazard:

1. **0,0 = CLOSE is a defined safe state**, so a pull-down guarantees the switch is isolated at
   boot. This matters because **TCA9535 ports power up as inputs (high-Z)** — an expander-driven
   RXEN would otherwise float.
2. **1,1 is NOT in the table.** With DIO2 driving TXEN *autonomously in hardware* while RXEN is
   driven *slowly in software*, there is a real window in which the radio raises TXEN while RXEN
   is still high from a previous RX — an undefined state that points PA output into the LNA. This
   is a consequence of the locked DIO2 to TXEN decision, not an argument against it, but it
   becomes a hard firmware rule.

**Inference, flagged as inference rather than vendor data:** RXEN is a per-transition control, not
per-symbol. A 400 kHz I2C register write is roughly 200 us against LoRa airtimes of tens to
hundreds of ms, so expander latency is **acceptable for MCU-initiated transitions**. It is **not**
acceptable for autonomous radio transitions (TX-done auto-RX, RxDutyCycle, CAD-to-RX), where RXEN
would lag the hardware.

### Task 3 — recommendation

Preference 1 (native GPIO) is **impossible**; preference 2 carries the caveats above.

**Recommended: reclaim ONE XGPIO from U3 for `SX1262_RXEN`**, leaving 14 on the community header.
Rationale: the XGPIOs are the only *discretionary* allocation left in the design — every U2 line
is a button, reset or rail control, and every native pin is committed.

Required alongside it:

- **pull-down on RXEN** (TCA9535 is high-Z at power-up; 0,0 = CLOSE is the safe state)
- **firmware rule: drive RXEN low and confirm the I2C write has completed before issuing any TX
  command**, and avoid autonomous TX/RX modes, because DIO2 raises TXEN in hardware

Two alternatives, recorded but not recommended:

- **Inverter from DIO2/TXEN to RXEN** — zero GPIOs, one single-gate SC70. Produces TX (1,0) and
  RX (0,1) automatically with no software timing, and structurally *cannot* create the 1,1 hazard.
  **Cost: CLOSE becomes unreachable**, so the RX path is always connected when not transmitting —
  a sleep-current and isolation question rather than a correctness one.
- **Drop octal PSRAM (N16R8 to quad)** to free GPIO 33–37 natively. Cleanest electrically, but the
  pin map kept the full 8 MB PSRAM deliberately for the display; this reopens a locked decision.

### Task 4 — TXEN / DIO2 confirmed

The manual states DIO2 *may connect to T/R CTRL rather than an MCU IO, to control RF-switch
transmit*, with note ①: *if DIO2 and TXEN are shorted, firmware must enable the DIO2
switch-control function*. **No pull resistor is specified and none is needed** — it is a direct
SX1262 output driving a module input. Also confirmed: **DIO3 is internal**, supplying the 32 MHz
TCXO at 2.2 V, and the manual warns the driver must be configured for TCXO.

**Firmware requirement: enable SX1262 DIO2-as-RF-switch mode, or TXEN never asserts and TX fails.**

### Task 5 — antenna, unresolved

The manual describes the series as *dual-antenna optional (IPEX / stamp hole)* with pin 21 ANT as
the 50 ohm stamp hole. It does **not** state whether IPEX is populated by default on this MPN,
whether both feeds are live simultaneously, or whether a 0 R / jumper selects between them.
**Pin 21 must not be routed until that is settled**, and IPEX population is a
**procurement-control item** for the locked Taoglas FXP890 path.

### Remaining blocker

**One decision: which XGPIO to reclaim from U3, or which alternative to take.** Everything else
needed for U7 capture is now resolved, except the `Pcb_E22-900M22S` archive, which downloads with
zip magic but is malformed.

---

## U7 — vendor PCB package RECOVERED; XGPIO14 reallocation verified but not applied (2026-08-08)

### Pcb_E22-900M22S recovered — the archive was truncated, not corrupt

The earlier download was **2,035,977 bytes**; a clean re-fetch gave **3,702,298 bytes**. Both lack a
valid end-of-central-directory, so `zipfile` and `unzip` both refuse them. The contents are
nevertheless intact and were recovered by **scanning `PK\x03\x04` local file headers directly and
inflating each member with `zlib.decompress(blob, -15)`**.

Archive layout (13 local headers) — note it is a **multi-variant** archive, exactly the trap the
brief warned about:

```
Pcb_E22/E22-400M30S/...
Pcb_E22/E22-433M22S/...
Pcb_E22/E22-900M22S/E22-900M22S(1).png      1,255,303 B
Pcb_E22/E22-900M22S/E22-900M22S_Size.jpg       75,623 B
Pcb_E22/E22-900M30S/...
```

Both `E22-900M22S` members extracted with **CRC32 verified OK** against the header — so these are
authentic, complete vendor files for the exact part.

**They are drawings (PNG/JPG), not an ECAD library.** "Pcb_E22-900M22S" is a dimensioned mechanical
drawing set, so the footprint must still be constructed from it — but from vendor geometry.

### Geometry read from `E22-900M22S_Size.jpg`

| Feature | Value |
|---|---|
| Body | **14.0 ±0.1 (W) × 20.0 ±0.1 (H)** |
| Thickness | **3.00 ±0.1** |
| Pad pitch | **1.27** |
| Top inset | **2.00** (body top edge to pin 12 / pin 11 centre) |
| Bottom inset | **1.00** (body bottom edge to pin 22 / pin 1 centre) |
| Numbering | counter-clockwise: **pin 1 bottom-right**, up the right edge to 11 top-right, 12 top-left, down to **22 bottom-left** |
| Split | 11 pads per edge (1–11 right, 12–22 left) |
| **IPX connector** | **drawn and labelled on the module, lower-left of the top view** |

**Antenna finding (Task 7): the IPX/u.FL connector is shown populated on the drawing for this exact
part number**, alongside the pin-21 ANT stamp hole. This is the strongest evidence yet that the
u.FL path is native to `E22-900M22S` rather than a family-level option — but it is a *drawing*, not
a purchasing guarantee, so the **procurement requirement stands**: confirm with the supplier that
shipped units have the IPEX connector populated before ordering Beta.

**One datum still missing for the footprint:** the drawing dimensions pitch (1.27), top inset (2.00)
and bottom inset (1.00), but **does not dimension the gap between pin 19 and pin 20** (left edge) or
between pin 4 and pin 3 (right edge) — the break where the IPX connector sits. Pads 12–19 and 1–11
are regular at 1.27, and 20–22 sit at the bottom, but the group offset is not stated. The larger
`E22-900M22S(1).png` (1.25 MB, the detailed PCB drawing) has not yet been read and is the obvious
place that gap is dimensioned.

### XGPIO14 reallocation — verified, deliberately NOT applied

Confirmed against the netlist, matching the brief exactly:

- **XGPIO14 = U3 pin 19** → `R65` (100 R) → `XGPIO14_HDR` → `D6` pin 4 + `J5` pin 19
- sheet 08 `08_buttons_expanders`: hierarchical label `XGPIO14` at (186.69, 92.71)
- sheet 09 `09_community_header`: hierarchical label `XGPIO14` at (167.64, 147.32); `R65` at
  (162.56, 147.32) rot 90; labels `XGPIO14_HDR` at (156.21, 144.78) and (251.46, 132.08);
  `D6` at (143.51, 149.86)

**Why it was not applied this pass:** renaming a hierarchical label requires the matching **sheet
pin in the parent `aqroot-Beta.kicad_sch` to be renamed too**, and sheet 09's `XGPIO14` pin must be
**deleted** rather than renamed. More importantly the change is **coupled to U7 capture** — until
U7 exists, `SX1262_RXEN` terminates at the sheet-08 boundary and goes nowhere, which is the same
dangling-intermediate problem that made the J1/backlight split impossible. Applying step 1 alone
would leave the design in a worse state than not starting.

**The reallocation and the U7 capture must land in one session**, in this order: reallocate U3.19 →
`SX1262_RXEN` (parent + sheet 08), retire the sheet-09 path (delete `R65`, delete the sheet-09
hierarchical label and its parent sheet pin, rename `XGPIO14_HDR` → `RESERVED_NC`), add the 100 k
pull-down, then create and place the 22-pin symbol wired to the nets above.

### Ebyte pull-down check (Task 2 of the brief)

The manual specifies **no pull resistor on RXEN**. It gives only the truth table, in which
**0,0 = CLOSE is a defined safe state**. A 100 k pull-down is therefore consistent with vendor
documentation and contradicts nothing; it exists to hold CLOSE while the TCA9535 ports are high-Z
at power-up. **No vendor-mandated alternative value was found.**

---

## U7 — pad-group gap still unresolved; (1).png is a render, not a drawing (2026-08-08)

Nothing modified. Coverage 158/176, ERC 0 real, 24 exclusions, netlist unchanged, U7 placeholder
and XGPIO14 chain both untouched.

### Definitive negative: E22-900M22S(1).png contains no dimensions

The 1.25 MB file expected to carry the detailed PCB drawing is a **2765 x 1932 product
photograph/render** of the module top face - label, QR code, SN, and the castellations along two
edges. **It has no dimensions of any kind.** Recording this so no future session re-opens it
hoping for the missing datum.

It does add one thing: the **IPEX/u.FL connector is clearly visible and populated** on the
pictured unit, reinforcing the same finding from Size.jpg. Antenna evidence is now two
independent vendor files; the procurement check still stands because neither is a purchase
guarantee.

### The gap datum remains missing, and the measurement was rejected

`E22-900M22S_Size.jpg` is therefore the **only** dimensioned vendor drawing, and it labels body
14.0 x 20.0 x 3.00, pitch 1.27, top inset 2.00 and bottom inset 1.00 - but **not** the gap between
pins 19 and 20 (left edge) or 4 and 3 (right edge), where the IPX connector sits.

Raster measurement was attempted, as the brief permits. It was **discarded as unreliable**: the
routine located candidate body edges at x = 85 and x = 354 and derived a body width of
**12.23 mm against the labelled 14.0 mm**, proving it had registered on dimension/extension lines
rather than the body outline. Pad-cluster detection outside those edges then returned zero
clusters, confirming the mis-registration. **Numbers that fail a known-dimension sanity check were
not used**, and no footprint was built from them.

Per the standing instruction - *only proceed once all 22 pad coordinates are deterministic*, and
*do not infer the special gap from normal 1.27 mm pitch* - the footprint build correctly did not
proceed, and with it neither did the coupled symbol/capture work.

### What would actually close this

1. **Re-do the raster measurement with correct registration** - anchor on the outer body rectangle
   verified to measure 14.0 x 20.0 before trusting any derived spacing. The approach is sound; the
   implementation mis-registered.
2. Or obtain a **dimensioned PCB land drawing** rather than the size drawing - the Ebyte resource
   set may carry one under a different item, and the user manual section 3.2 figure may dimension
   it where Size.jpg does not.
3. Or derive the gap from the **IPX connector footprint position**, which is drawn to scale on
   both files, once registration is trustworthy.

Everything else for U7 is settled: pinout verified against manual section 3.2, RF-switch
architecture locked, XGPIO14 chain mapped with coordinates, pull-down justified, IPEX confirmed.

---

## CORRECTION — U7 and U8 were transposed in the blocker register (2026-08-08)

**Integration was aborted at the Task 1 baseline gate. No schematic file was modified.**

### The schematic is authoritative, and it says the opposite of the recent briefs

Read directly from `04_spi_b_radios_nfc.kicad_sch`:

| Ref | Symbol value | MPN | Silicon / band |
|---|---|---|---|
| **U7** | `CC1101_RADIO_PLACEHOLDER` | **E07-400M10S** | CC1101, 433 MHz |
| **U8** | `SX1262_MODULE_PLACEHOLDER` | **E22-900M22S** | SX1262, 915 MHz |

This matches the drift-closure entry recorded at commit `a9e8952` (log line ~2692), which assigned
those MPNs from `12 - RF and Antenna Plan`. It is corroborated by the net names: the design carries
`CC1101_CS_N` and `CC1101_GDO0` for U7, and `SX1262_CS_N`, `SX1262_BUSY`, `SX1262_DIO1`,
`SX1262_RST_N` for U8.

### The error is mine, and it is in this log

The **blocker register table (log line ~3329)** states the reverse — *"U7 | Ebyte E22-900M22S"* and
*"U8 | Ebyte E07-400M10S"*. That table was written by me and **transposed the two references**.
Every subsequent session brief was built on it, which is why the last several tasks have said
"U7 = E22-900M22S".

**The transposition never reached the schematic** — only this log and the task framing. The design
files have been internally consistent throughout.

### What would have happened had the integration proceeded

Applying the locked mapping to U7 would have:

1. placed the **E22/SX1262** symbol on the **CC1101** reference;
2. wired `SX1262_CS_N`, `SX1262_BUSY`, `SX1262_DIO1` and `SX1262_RST_N` to the **433 MHz CC1101**
   position, while `CC1101_CS_N` and `CC1101_GDO0` were left stranded;
3. left the **real SX1262 module (U8) still a placeholder**;
4. produced a netlist that passes ERC and *looks* complete while being wrong at the part level —
   the most expensive class of error to find later, since it would likely survive to fabrication.

### Corrected assignment

**The E22-900M22S integration belongs to U8, not U7.**

- **U8** ← `E22-900M22S` symbol + `AQROOT_Beta:Ebyte_E22-900M22S` footprint, RXEN/TXEN/DIO2
  architecture, 100 k pull-down, the `SX1262_*` and `SPI_B_*` nets, IPEX/Taoglas FXP890 antenna.
- **U7** remains the **E07-400M10S / CC1101** module, still a placeholder, still blocked on its own
  vendor pin audit, and carries `CC1101_CS_N` / `CC1101_GDO0`.

### The library assets from commit 3f80b62 are unaffected

Symbol `E22-900M22S` and footprint `AQROOT_Beta:Ebyte_E22-900M22S` were built from the exact
E22-900M22S vendor geometry and remain **fully valid and VERIFIED_VENDOR_EXACT**. Only the
*reference they attach to* changes. **No asset rework is required** — the 5.57 mm gap resolution,
the C411293 cross-validation and the 22-pad geometry all stand.

### Everything else in the locked architecture survives the swap

The RF-switch decision (DIO2→TXEN local, RXEN from reclaimed `XGPIO14` = U3 pin 19, 100 k
pull-down), the firmware sequence, the antenna/IPEX finding and the XGPIO14 retirement plan are all
**module-specific, not reference-specific**, and apply unchanged — to **U8**.

The XGPIO14 baseline was re-verified this session and is intact: `XGPIO14` = R65.2 + U3.19;
`XGPIO14_HDR` = D6.4 + J5.19 + R65.1. 155 nets, ERC 0 real, tree clean.

---

## U9 ST25R3916 — authoritative 33-pad table captured; footprint BLOCKED on package code (2026-08-08)

Nothing modified. 176 components, 160 footprinted, ERC 0 real, 24 exclusions, tree clean.

### Source

**ST `DS12484 Rev 3`, June 2020, ST25R3916/ST25R3917, 156 pp.** `st.com` failed transport for a
fourth consecutive session on two URL forms; the document was obtained from MikroElektronika's
mirror and verified by its own cover page (`DS12484 Rev 3`, ST title block).

### Complete physical pin table — Table 2, VFQFPN32 + thermal pad

| # | Name | Type | Function | Placeholder | Status |
|---|---|---|---|---|---|
| 1 | VDD_IO | P | Supply for peripheral comms | VDD_IO_3V3 | MATCH |
| 2 | CSO | AO | Capacitor sensor out / test out 2 | — | **MISSING** |
| 3 | VDD_D | AO | **Digital regulator OUTPUT** | VDD_DIG_3V3 | **CONFLICT** |
| 4 | XTO | AO | Crystal oscillator output | XOUT | MATCH (renamed) |
| 5 | XTI | AI/DI | Crystal oscillator input | XIN | MATCH (renamed) |
| 6 | GND_D | P | Digital ground | GND | partial |
| 7 | VDD_A | AO | **Analog regulator OUTPUT** | — | **MISSING** |
| 8 | VDD | P | External positive supply | — | **MISSING** |
| 9 | VDD_RF | AO | **Regulated driver supply OUTPUT** | — | **MISSING** |
| 10 | VDD_TX | P | External positive supply, TX part | VDD_PA_5V | likely MATCH |
| 11 | VDD_AM | AO | **Regulated AM driver supply OUTPUT** | — | **MISSING** |
| 12 | GND_DR | P | Antenna driver ground | — | **MISSING** |
| 13 | RFO1 | AO | Antenna driver output | RFO1 | MATCH |
| 14 | VDD_DR | P | Antenna driver supply **input** | — | **MISSING** |
| 15 | RFO2 | AO | Antenna driver output | RFO2 | MATCH |
| 16 | GND_DR | P | Antenna driver ground | — | **MISSING** |
| 17 | EXT_LM | AO | External load-modulation gate driver | — | **MISSING** |
| 18 | AAT_A | AO | AAT tune voltage | — | **MISSING** |
| 19 | AAT_B | AO | AAT tune voltage | — | **MISSING** |
| 20 | I2C_EN | DI | **I2C interface enable** | — | **MISSING — strap required** |
| 21 | VSS | P | Ground, die substrate | — | **MISSING** |
| 22 | RFI1 | AI | Receiver input | RFI1 | MATCH |
| 23 | RFI2 | AI | Receiver input | RFI2 | MATCH |
| 24 | AGDC | AIO | Analog reference voltage | — | **MISSING** |
| 25 | CSI | AIO | Capacitor sensor in / test out 1 | — | **MISSING** |
| 26 | GND_A | P | Analog ground | — | **MISSING** |
| 27 | IRQ | DO | Interrupt request output | IRQ | MATCH |
| 28 | MCU_CLK | DO | Clock output for MCU | — | **MISSING** |
| 29 | **BSS** | DI | **SPI enable (active low)** — the chip select | CS_N | MATCH (renamed) |
| 30 | SCLK | DI | SPI clock / I2C clock | SCK | MATCH |
| 31 | MOSI | DI | SPI data input | MOSI | MATCH |
| 32 | MISO | DO_T | SPI data out / I2C data | MISO | MATCH |
| 33 | Thermal pad | P | Exposed pad | — | **MISSING** |

**Placeholder had 15 pins against 33 physical pads — 18 absent.**

### Three findings that change the NFC work, beyond simple pin count

1. **Four pins are regulator OUTPUTS, not supply inputs.** `VDD_D` (3), `VDD_A` (7), `VDD_RF` (9)
   and `VDD_AM` (11) are typed **AO — analog output**. The placeholder modelled `VDD_D` as a 3V3
   *supply input* (`VDD_DIG_3V3`), which is **backwards**. These pins require external decoupling
   to ground and **must not be tied to a rail**. That capacitance does not exist in the design.
2. **The supply architecture has three external inputs, not two**: `VDD` (8), `VDD_TX` (10) and
   `VDD_DR` (14) — all typed **P**. The locked architecture only anticipates a 3V3 I/O rail and the
   5 V PA rail (`NFC_5V_PA_PENDING`). Which of VDD/VDD_TX/VDD_DR takes which rail is a **design
   decision that is not yet made**.
3. **`I2C_EN` (20) is a mandatory strap.** AQROOT drives this device over SPI, so the pin must be
   strapped to select SPI. The datasheet names it *"I2C interface enable"*; the required level and
   whether a resistor is needed are not yet extracted. `BSS` (29) is the SPI chip select — the name
   bears no resemblance to `CS_N`, which is worth knowing before anyone maps by name.

### FOOTPRINT BLOCKED — the package code does not match

ST's ordering scheme (§7, p.153) decodes as `ST25 R 3916 - A QW T`, where the character pair
**after** the temperature letter is the package:

- `A` = ambient −40 °C to 105 °C
- **`QW` = 32-pin VFQFPN (5 × 5 mm) with wettable flanks** — the only QFN option listed
- `T` = 4000 pcs/reel

**Our locked part is `ST25R3916-AQET`, i.e. package code `QE`, which does not appear in this
datasheet.** §6.1 documents only *"VFQFPN32 … 32-pin, 5×5 mm, 0.5 mm pitch, very thin fine pitch
quad flat no lead"*, while the project records AQET as **UFQFPN-32, 5 × 5 × 0.55 mm** — *ultra*
thin, presumably taken from ST's website rather than DS12484.

The **electrical table above is package-independent** and stands regardless: same die, same pin
numbering. But **the land pattern is not**, and substituting the VFQFPN32 drawing for a UFQFPN32
part is precisely the "adjacent package" substitution the brief forbids. **No footprint was built.**

**To close:** either confirm that `AQET`/`QE` is UFQFPN32 and obtain that package drawing (likely a
newer datasheet revision or the ST product page), or confirm AQET is in fact the VFQFPN32 part and
correct the project's package record — at which point §6.1's drawing applies directly.

### Not done

No symbol, no footprint, no integration. The pin table is captured but the symbol cannot be
finalised while three supply-architecture decisions and the `I2C_EN` strap are open, and the
footprint is blocked on the package code.

---

## U9 ST25R3916-AQET — pin table re-verified, ST decoupling extracted, VDD_DR open (2026-08-08)

Nothing modified. 176 components, 160 footprinted, ERC 0 real, 24 exclusions, tree clean.

### Pin table re-verified programmatically, not from memory

All **33 pads** were re-parsed directly out of the archived `ST25R3916_DS12484_Rev3.pdf` (Table 2,
pp. 20–21) and matched **exactly** against the table in the brief — 33/33, no discrepancies, no
gaps in the auto-parse. Types confirmed as well: `VDD_D` (3), `VDD_A` (7), `VDD_RF` (9) and
`VDD_AM` (11) are all **AO — analog output**, confirming they are regulator outputs, not supply
inputs, and that the retired placeholder's `VDD_DIG_3V3` model was inverted.

### Internal regulator decoupling — quoted from ST, not inferred

DS12484 §Application information, p.40 states verbatim:

> *"For regulators recommended blocking capacitors are **2.2 μF in parallel with 10 nF**, for pin
> **AGDC 1 μF in parallel with 10 nF** is suggested."*

and p.41, separately, for the AM regulator:

> *"It requires decoupling capacitors **(2.2 µF + 1 nF)** at VDD_AM pin."*

| Pin | Rail | Regulator function | Required decoupling |
|---|---|---|---|
| 3 | `VDD_D` | Digital supply regulator output | **2.2 µF ∥ 10 nF** |
| 7 | `VDD_A` | Analog supply regulator output | **2.2 µF ∥ 10 nF** |
| 9 | `VDD_RF` | Regulated driver supply for antenna drivers | **2.2 µF ∥ 10 nF** |
| 11 | `VDD_AM` | Regulated driver supply for AM modulation | **2.2 µF ∥ 1 nF** — note **1 nF**, not 10 nF |
| 24 | `AGDC` | Analog reference voltage | **1 µF ∥ 10 nF** |

**The VDD_AM value differs from the other three.** ST gives it its own sentence with **1 nF**
rather than the general 10 nF, so treating all four regulators identically would be wrong.

**That is 10 new capacitors** (5 pins × 2 each) that do not exist in the design. All values are
ST-specified, so none would be invented — but they are new physical components and will move the
component total.

### VDD_DR — normal-mode connection NOT yet established

The datasheet is explicit about the **bypass** case only:

> *"If a transmitter output current higher than 350 mArms is required the VDD_RF regulator cannot
> be used to supply the transmitter. **VDD_RF and VDD_DR have to be externally connected to
> VDD_TX**."*

That configuration is **excluded for Beta** by the standing lock, which is consistent — normal
internal-regulator mode is correct and no thermal review is triggered.

What the datasheet does **not** state in any passage found is what `VDD_DR` (14, antenna driver
supply **input**, type P) connects to in **normal** mode. It only notes that *"VDD_DR is used as
reference voltage, resulting in correct VDD_AM voltage"* and that *"the transmitter outputs are
driven with VDD_DR"*. The obvious reading is that `VDD_RF` (the regulator output feeding the
antenna drivers) supplies `VDD_DR` — **but that is inference, and it is the one connection that
distinguishes normal mode from the excluded bypass mode**, so it is not being guessed.

**This needs the X-NUCLEO-NFC06A1 / ST25R3916 reference schematic**, which the brief itself names
as the secondary architecture check for exactly this point.

### Confirmed and unchanged

- **Package**: `AQET` = UFQFPN-32, 5 × 5 × 0.55 mm, ACTIVE; `AQWT` = VFQFPN-32, 5 × 5 × 1 mm,
  wettable flanks, NRND. The Beta lock is correct and the AQWT land pattern must not be
  substituted. This resolves the blocker raised last session.
- **Supply mapping locked**: `VDD_IO` (1) → `+3V3`; `VDD` (8) and `VDD_TX` (10) → both to
  `NFC_5V_PA_PENDING`, sharing one external supply.
- **`I2C_EN` (20) → GND** for SPI selection.
- **`BSS` (29) is the SPI chip select** — *"SPI enable (active low)"* per Table 2 — mapping to
  `NFC_CS_N`.

### Not built

No symbol, no footprint, no integration, no capacitors added. The footprint still requires a
UFQFPN-32 source (ST-linked Ultra Librarian/SamacSys, or the exact `C5267441` EasyEDA part as
secondary), and the symbol should not be finalised while the `VDD_DR` connection is open, since it
determines whether pin 14 carries a real net or a deferred one.

---

## U9 assets — symbol built; footprint BLOCKED on a package-name conflict (2026-08-08)

Library symbol only. No sheet touched, so connectivity, ERC, exclusions and the netlist are
unchanged by construction; coverage stays 160/176 and U9 remains on the missing list.

### VDD_DR still unresolved — ST transport failed a fifth time

The X-NUCLEO-NFC06A1 schematic could not be retrieved; two ST-hosted URL forms failed. Falling
back to the archived datasheet, **Figure 11 turns out to be an internal block diagram, not an
application schematic** - it shows VDD_DR as a pin with an internal power-down clamp to VDD_TX
through a switch and 1 kohm, but **does not show any external normal-mode connection**.

So the position is unchanged and deliberately not guessed: ST states the **bypass** case
explicitly (*VDD_RF and VDD_DR have to be externally connected to VDD_TX* above 350 mArms, which
Beta excludes) but no located ST source states what feeds VDD_DR in **normal** mode.
**This does not block the symbol** - VDD_DR is typed **P (power input)** in Table 2 regardless of
what drives it - but it does block integration, since it decides whether pin 14 carries a real or
a deferred net.

### FOOTPRINT BLOCKED — the exact-part library contradicts the locked package

The exact-part EasyEDA entry was retrieved and **is genuinely the right part**: title
`ST25R3916-AQET`, LCSC `C5267441`. Its geometry is complete and self-consistent:

| Feature | Value |
|---|---|
| Pads | **33** = 32 perimeter + 1 exposed pad |
| Pitch | **0.50 mm** |
| Perimeter pad | 0.28 x 0.665 (rotated 0.665 x 0.28 on the other two sides) |
| Pad extremes | x and y both +/-2.420 mm |
| Exposed pad 33 | **3.5 x 3.5 mm** at origin |

**But its package is declared `VFQFPN-32_L5.0-W5.0-P0.50-TL-EP3.5`** - and the same string is the
3D model name. That directly contradicts the Beta lock of **UFQFPN-32, 5 x 5 x 0.55 mm**.

Under the standing discrepancy rule ST wins, so the footprint was **not** built. The conflict
cannot be arbitrated from what is in hand: **DS12484 Rev 3 documents only VFQFPN32** in section
6.1 and its ordering table lists only `QW`, so the ST datasheet has no UFQFPN32 land pattern to
check against, and the LCSC entry - while correct on the MPN - names the package the locked spec
says it is not.

Note the two families plausibly share a land pattern, differing mainly in body height (0.55 vs
1.0 mm). **That is exactly the assumption that must not be made silently for a Class B part.**

**To close:** obtain ST's UFQFPN32 package drawing for `QE` - a newer datasheet revision, the ST
product page package tab, or ST-linked Ultra Librarian/SamacSys - and compare it against the
geometry above. If it matches, the footprint can be built immediately from data already recovered.

### Symbol built and validated

`ST25R3916-AQET`, **33 pads**, names/numbers/types programmatically re-verified against the
archived DS12484 Table 2 before writing. Electrical types set deliberately: **VDD_D, VDD_A,
VDD_RF and VDD_AM are typed as outputs**, not power inputs, correcting the retired placeholder's
inverted model; VDD_IO, VDD, VDD_TX and VDD_DR are power inputs; the five grounds and the exposed
pad are power inputs. Footprint field left **empty** rather than pointing at an unverified land
pattern. `kicad-cli sym export svg` plots it. The locked supply mapping, the I2C_EN strap, the
BSS chip-select identification and all five ST decoupling pairs are recorded in the symbol Package
note for the integration session.

---

## U9 — footprint and VDD_DR both still blocked on transport (2026-08-08)

Nothing modified. 176 components, 160 footprinted, ERC 0 real, 24 exclusions, netlist unchanged,
tree clean. The committed `ST25R3916-AQET` symbol is untouched and its Footprint field remains
deliberately blank.

### Routes attempted this session, and how each failed

| Target | Route | Result |
|---|---|---|
| VDD_DR | `st.com` UM2615, two URL forms | **fail** — st.com transport, now 6 consecutive failures across 4 sessions |
| VDD_DR | ST schematic pack via `fcc.report` (ST's own filed drawing) | **403** |
| VDD_DR | same via `fccid.io`, direct and through WebFetch | **403** both |
| Footprint | ST-linked Ultra Librarian / SamacSys | **not reached** — budget went to the VDD_DR routes |

The FCC route was worth trying and remains the best non-st.com lead: the applicant on FCC ID
`YCPNFC06A1` is **STMicroelectronics SAS**, so the filed schematic is ST's own drawing rather than
a third-party redraw — it satisfies the "no random redraw" constraint. Both mirrors that host it
simply refuse automated fetches.

### Position unchanged, and deliberately so

- **VDD_DR normal-mode source: still UNRESOLVED.** ST states only the bypass case
  (*VDD_RF and VDD_DR externally tied to VDD_TX*, above 350 mA rms), which Beta excludes. No ST
  source obtained states what feeds VDD_DR in normal mode. Not inferred from pin naming.
- **Footprint: still BLOCKED.** The exact-part EasyEDA entry `C5267441` supplies complete geometry
  (32 perimeter pads + EP, 0.50 pitch, pads 0.28 x 0.665, extremes +/-2.420, EP 3.5 x 3.5) but
  declares its package **VFQFPN-32**, contradicting the locked **UFQFPN-32 5 x 5 x 0.55**. It stays
  **secondary evidence only** and was not promoted to verified.
- **AQET / AQWT distinction preserved.** No VFQFPN geometry was adopted, and nothing was
  substituted on the grounds of looking similar.

### Cheapest remaining routes, in the order I would try them

1. **ST-linked Ultra Librarian / SamacSys for `ST25R3916-AQET`** — the one primary-source footprint
   route not yet attempted. Should be first next session.
2. **ST-hosted UFQFPN32 5x5x0.55 package drawing from any other ST part** using that package, per
   the standing fallback — establishes the family land pattern, then cross-check `C5267441`.
3. **X-NUCLEO-NFC06A1 Gerbers** rather than the schematic; tracing copper from the VDD_DR pad on
   ST's own manufactured reference board is explicitly sanctioned and sidesteps the PDF mirrors.
4. A human fetch of either PDF — both are public and open fine in a browser; only automated
   retrieval is refused.

### Standing judgement

The two blockers are independent. The **footprint** needs one ST package drawing and the geometry
is otherwise already in hand. **VDD_DR** needs one connection off ST's reference design, and is the
only thing preventing the symbol from being wired — pin 14 is typed correctly either way, so the
symbol itself needs no rework whichever answer arrives.

---

## U9 — blocker is now proven ENVIRONMENTAL, not informational (2026-08-08)

Nothing modified. 176 components, 160 footprinted, ERC 0 real, 24 exclusions, netlist
unchanged, tree clean. Symbol untouched, Footprint field still blank.

### The package-family fallback was attempted and hit the same wall

The fallback route was identified correctly: ST publishes the UFQFPN32 5x5 outline **and a
recommended footprint** inside the datasheets of other current parts using that package, notably
STM32G031 and STM8L101. Those are ST-hosted documents and would satisfy the primary-source
requirement.

They cannot be retrieved here. This session added:

- STM32G031 datasheet via curl: fail
- STM8L101 datasheet via curl: fail
- a non-ST mirror for the same: fail
- STM32G031 datasheet via WebFetch: **ECONNRESET**

### The important conclusion

Across four sessions, every st.com resource path has failed - datasheet, user manual, schematic
pack, and now two unrelated STM32/STM8 datasheets - by **two independent transport mechanisms**
(curl and WebFetch), and ST's own FCC-filed schematic returns 403 from both mirrors that host it.
Non-ST mirrors worked once, for the ST25R3916 datasheet itself, which is why that document is in
the repo.

**The remaining U9 blockers are therefore not analytical - they are network reachability.** Every
open route needs one ST-hosted PDF, and this environment cannot reach st.com by any method tried.
Continuing to spend sessions on retrieval attempts has a poor expected return.

### What is actually needed - two files

1. **Any ST datasheet containing the UFQFPN32 5x5x0.55 recommended footprint** (STM32G031 and
   STM8L101 both contain it). Dropping it into vendor/ST25R3916/ closes the footprint: the
   comparison targets are already fixed - pitch 0.50, perimeter pads 0.28 x 0.665, pad-centre
   extremes +/-2.420, exposed pad 3.5 x 3.5 - so it is a direct match-or-report check against
   C5267441 and nothing further needs discovering.
2. **X-NUCLEO-NFC06A1 schematic pack or Gerber ZIP**, which settles the normal-mode VDD_DR
   connection.

Both are public and open normally in a browser; only automated retrieval is refused. With those
two files present, U9 assets close in one short session and integration can follow.

### Nothing was compromised to make progress

No VFQFPN geometry adopted, C5267441 not promoted beyond secondary, AQET/AQWT distinction intact,
no VDD_DR connection inferred from pin naming, and no bypass-mode wiring created.

---

## U9 ASSETS COMPLETE — AQET land pattern built, normal RF-regulator wiring locked (2026-08-08)

Library assets only. No sheet touched; ERC 0 real, 24 exclusions, netlist unchanged, tree clean.

### VDD_DR — normal mode LOCKED

Recorded for the integration session, from the CTO decision citing ST's X-NUCLEO-NFC06A1 schematic
and ST support ("VDD_DR is sourced via the LDO"):

```
NORMAL MODE (Beta):
  VDD_TX          -> NFC_5V_PA_PENDING          (upstream transmitter supply)
  VDD             -> NFC_5V_PA_PENDING          (same supply as VDD_TX)
  VDD_RF          <- internal VDD_RF regulator output, + 2.2uF || 10nF to GND
  VDD_DR          -> VDD_RF regulated node       <-- the previously open question
  VDD_IO          -> +3V3
  I2C_EN          -> GND                         (selects SPI)

BYPASS MODE (NOT used, NOT populated for Beta):
  VDD_RF and VDD_DR tied directly to VDD_TX
  Implemented on ST's Discovery board via jumper J206; Beta has no equivalent.
```

**No direct `VDD_DR -> VDD_TX` and no direct `VDD_RF -> VDD_TX` connection exists or will be
created.** Regulator-output decoupling queued for integration: `VDD_D` 2.2 µF ∥ 10 nF, `VDD_A`
2.2 µF ∥ 10 nF, `VDD_RF` 2.2 µF ∥ 10 nF, `VDD_AM` 2.2 µF ∥ **1 nF**, `AGDC` 1 µF ∥ 10 nF.

### Footprint built — `AQROOT_Beta:ST25R3916_AQET`

| Feature | Value | Basis |
|---|---|---|
| Perimeter lands | **32**, 0.30 × 0.75 | ST recommended land |
| Pitch | **0.50**, 8 per side at ±0.25/0.75/1.25/1.75 | ST |
| Land centres | **±2.275** (span 5.30 − land 0.75) | derived, reads back exact |
| Exposed pad 33 | **3.45 × 3.45**, F.Cu + F.Mask only | ST recommended land (pkg EP 3.50) |
| Body | 5.00 × 5.00 | ST |
| Numbering | CCW from pin 1, top of left side | ST QFN convention |

**Classification: VERIFIED_VENDOR_EXACT_PACKAGE_FAMILY.** Primary provenance is ST's UFQFPN32
5×5×0.55 recommended footprint, applicable because ST designates AQET as that package family.
**AQWT (VFQFPN 5×5×1.0, wettable flanks, NRND) geometry is not used anywhere.**

**C5267441 was deliberately not used as the source.** Its copper (0.28 × 0.665, EP 3.50) does not
match ST's recommended land (0.30 × 0.75, EP land 3.45); it is recorded as an **IPC/library
alternate**. It does corroborate pad count, pitch, body, EP location and numbering — the two agree
on everything except final copper dimensions, which is exactly why ST's values were taken.

**Paste**: ST prescribes no aperture pattern, so the EP carries a conservative 2 × 2 segmentation
of four 1.4 × 1.4 apertures on 1.8 mm centres (**65.9 %** coverage), documented in the footprint
as **assembly implementation, not manufacturer geometry**. **No thermal vias** in the footprint —
layout work, with ST's ground-the-EP recommendation recorded.

### Validation

`kicad-cli` plots footprint and symbol. **33 copper pads, contiguous 1–33, no duplicates**, plus
4 paste-only apertures correctly not counted as pads. Perimeter |x| and |y| sets both
`{0.25, 0.75, 1.25, 1.75, 2.275}`. Perimeter sizes only `0.30 × 0.75` and its rotation. EP 3.45 sq
on Cu+Mask. **Symbol pins 1–33 map 1:1 onto footprint pads 1–33.**

### Honesty note

**st.com remains unreachable from this environment** — one further attempt this session failed,
consistent with every prior attempt across four sessions via two transport mechanisms. The VDD_DR
conclusion and the ST land-pattern values are therefore held **on supplied authority and were not
independently re-verified here**. The geometry is internally coherent (span, land length and centre
positions agree), which is a consistency check, not a source check.

### U9 status

**Assets complete.** Symbol (33 pads) + footprint (32 + EP) + power model + decoupling schedule all
in place. **Ready for schematic integration**, which will add ~10 ST-specified capacitors and is
deliberately left to its own session. NFC antenna/matching remains DO NOT ROUTE.

---

## J2 Molex 5025700893 — card-detect question answered; drawing still unreachable (2026-08-08)

Nothing modified. 186 components, 171 footprinted, 15 missing, ERC 0 real, 24 exclusions, netlist
unchanged, tree clean.

### Baseline J2 map, recorded for the eventual swap

| Pin | Function | Net |
|---|---|---|
| 1 | DAT2 | `unconnected-(J2-DAT2-Pad1)` |
| 2 | DAT3/CD | `SD_CS_N` |
| 3 | CMD | `SPI_A_MOSI` |
| 4 | VDD | `+3V3` |
| 5 | CLK | `SPI_A_SCK` |
| 6 | VSS | `GND` |
| 7 | DAT0 | `SPI_A_MISO` |
| 8 | DAT1 | `unconnected-(J2-DAT1-Pad8)` |
| SH | SHIELD | `GND` |

SPI-A is shared correctly across `J1 + J2 + U1`; `SD_CS_N` carries `J2.2 + R25.2 + U1.25`. This is
1-bit SD mode with DAT1/DAT2 intentionally unconnected, as the architecture already records.

### Card-detect — answered definitively

**A project-wide net search returns NOTHING matching card-detect** (`CARD_DET`, `SD_CD`, `CD_N`,
`DETECT`). So AQROOT allocates **no MCU or expander input for a physical card-detect switch**, and
per the standing rule none may be created automatically.

That settles the first half of the CD question. The **disposition** of the two switch terminals
still cannot be fixed, because it depends on how the Molex drawing numbers and arranges them —
whether they are an isolated SPST pair, or one terminal commoned to the shell. Choosing between
"both NC" and "one grounded" without that drawing would be guessing at the connector's internals.

**Note also:** pin 2 `DAT3/CD` is presently used as `SD_CS_N`, which is correct for SPI mode — and
is a further reason the mechanical switch must not be conflated with it.

### Drawing retrieval — failed again, but one useful discovery

Attempted this session:

- `molex.com/webdocs/...`, `media.digikey.com/...`, and the `molex.com/content/dam/...`
  salesdrawing path — all fail
- `docs.rs-online.com/9fc5/...` — succeeds, but hosts only the **one-page product summary**, not
  the drawing

**Useful discovery:** a sibling RS document for Molex part `5035000993` exposes Molex's drawing
filename convention — **`<partnumber>_sd.pdf`** — confirming the target filename is
`5025700893_sd.pdf`. Every CDN host tried for that filename refused it, so the convention is known
but no reachable host serves it.

### Status unchanged

**J2 remains BLOCKED_EXTERNAL_DOCUMENT + BLOCKED_SYMBOL_MISMATCH.** Without `SD-502570-001` /
`SD-502570-002` there is no card-detect terminal numbering for the symbol and no land geometry for
the footprint, so neither asset was built and the stock `Connector:Micro_SD_Card` symbol is
untouched.

**What would close it:** the Molex sales drawing `SD-502570-001` (and `-002`), or a
manufacturer-linked ECAD model for `502570-0893` that exposes CD terminal numbering plus land
geometry. Like the ST case, this is a **retrieval** blocker, not an analysis one — the moment the
drawing is in `vendor/`, the symbol and footprint are a bounded build.

---

## J2 Molex 5025700893 — drawing OBTAINED, card-detect topology RESOLVED (2026-08-08)

Nothing modified in the design. 186 components, 171 footprinted, 15 missing, ERC 0 real, 24
exclusions, netlist unchanged, tree clean.

### The drawing is in the repo

Direct PDF/CDN retrieval fails, but AllDataSheet's HTML viewer serves the original Molex sheets as
full-resolution page images. All five pages are archived under
`vendor/Molex_5025700893/SD-502570-001_page1..5.png`.

**Identity verified from the title block, not the hosting page:**

- **MOLEX INCORPORATED**
- Document no. **SD-502570-001**, sheets **1 OF 2** and **2 OF 2**
- Title: *MICROSD CARD CONN. (P/P & NORMALSMALL TYPE)*
- MODEL NO. table lists **502570-0893** explicitly, alongside 502570-0831
- Rev **A**, EC J2009-2308, drawn 07/09/10, scale 4:1, metric, third-angle projection

### Contact assignment, from sheet 1

`Pin 1 DAT2 · Pin 2 CD/DAT3 · Pin 3 CMD · Pin 4 VDD · Pin 5 CLK · Pin 6 Vss · Pin 7 DAT0 ·
Pin 8 DAT1` — matching the current AQROOT mapping exactly, so no SD signal changes are implied.

### CARD-DETECT TOPOLOGY — resolved, and it is NOT "both NC"

Sheet 1's materials table lists two distinct parts: **⑦ DETECT LEVER** and **⑧ DETECT SWITCH**,
both copper alloy with gold contact plating. Sheet 2's recommended PCB layout then labels their
lands separately, and decisively:

> **DETECT LEVER MOUNT AREA (Vss : GROUND)**
> **DETECT SWITCH MOUNT AREA**

**So one side of the mechanical switch is committed by Molex to Vss/GROUND.** The switch is
therefore *not* an isolated floating pair — the lever land is ground, and the detect-switch land is
the single switched signal.

Sheet 1's state table completes it:

| Condition | Switch |
|---|---|
| Card inserting position | **CLOSE** |
| No card | **OPEN** |

**Consequence for Beta:** the correct representation is **DETECT LEVER land → GND** (manufacturer
intent, not a choice) and **DETECT SWITCH land → a single signal** which, with no card-detect GPIO
allocated anywhere in AQROOT, becomes an explicit named NC/TBD. Had this been guessed as "both
terminals NC", the ground land would have been left floating against the manufacturer's own
pattern.

This also confirms the switch is **active-low into ground when a card is present** — useful for
firmware if a GPIO is ever allocated.

### Recommended PCB pattern layout — sheet 2 of 2

Labelled regions: **TERMINAL MOUNT AREA** (the 8 contacts), **SHELL MOUNT AREA** (top and bottom),
**DETECT LEVER MOUNT AREA**, **DETECT SWITCH MOUNT AREA**, and a hatched **PATTERN PROHIBITION
AREA** (keep-out). General tolerance **±0.05**.

Dimensions visible on the sheet include contact **pitch 1.1**, land **0.8** wide × **1.7**, overall
**14.3** across the shell mounts, and a vertical stack of 15.9 / 15 / 10.6 / 13.35 / 14.95 / 13.15 /
8.65 / 11.15 / 7.5 / 6.55 / 4.45 / 4.25 / 2.9 / 1.5 / 1.4 / 1.15 / 0.5 / 0.25.

**The footprint was not built this session** — extracting every land coordinate from this sheet is
a careful measurement job, and it is the whole remaining task rather than a loose end.

### Status

J2 moves from **BLOCKED_EXTERNAL_DOCUMENT** to **DOCUMENT_OBTAINED_BUILD_PENDING**. Both prior
unknowns are closed: the drawing is in the repo, and the card-detect topology is manufacturer-
stated rather than assumed. What remains is a bounded build — physical symbol including the two
detect lands, then the footprint from sheet 2, then the swap preserving the SD nets recorded
earlier.

---

## J2 — Sheet 2 dimensions extracted; footprint NOT built (attribution incomplete) (2026-08-08)

Nothing modified. 186 components, 171 footprinted, 15 missing, ERC 0 real, 24 exclusions, netlist
unchanged, tree clean. Baseline J2 map re-verified unchanged.

### What sheet 2 gives, read at 430 dpi from the archived page

**Contact field — this part resolves cleanly and self-consistently:**

- contact pitch **1.1**
- contact land **0.8 wide x 1.7 tall**
- **7.7** is the contact-field span, and it checks out exactly: 7 gaps x 1.1 = **7.7**
- **4.45** locates the field from the left datum
- **14.3** is the overall span across the shell-mount lands
- shell-mount lands **1.4 wide x 1.7 tall**, one at each end

That yields a coherent reading of the eight contacts at 1.1 spacing starting 4.45 from the left
datum and ending at 12.15, with 14.3 overall - the arithmetic closes.

**Detect lands:** DETECT LEVER MOUNT AREA (Vss : GROUND) and DETECT SWITCH MOUNT AREA are both
present and separately labelled, with **1.15** and **1.5** dimensions attached to them, plus
**4.25 / 6.55 / 13.15 / 1.5 / 1.5 / 1.5** locating the detect-switch region.

**Vertical stack:** 3, 1.5, 10.6, 15, 1.15, 1.15.

**Pattern-prohibition (keep-out) region:** the dimensions carrying the note-3 triangle are
**14.95, 13.35, 13.15, 11.15, 8.65, 7.5, 2.9, 1.4, 1, 0.5, 0.5** - note 3 on sheet 1 is
*パターン禁止エリア / PATTERN PROHIBITION AREA*. These bound the no-copper region rather than any
land.

General recommended-pattern tolerance **±0.05**.

### Why the footprint was still not built

The dimension set is now *in hand*, but several values are **not yet unambiguously attributed to a
specific feature**. Specifically it is not yet certain whether **4.45 locates the first contact
centre or its edge**, and whether **14.3 is outer-to-outer or centre-to-centre of the shell-mount
lands** - a 0.7-1.4 mm difference in where every land sits. The left-hand vertical stack is also
dominated by note-3 keep-out dimensions interleaved with land dimensions on shared extension lines.

Committing a footprint on the wrong reading of those two datums would place every pad on this
connector 0.7 mm out, which is exactly the class of silent error that a pad-count or DRC check
would not catch. Consistent with how every other Class B part in this project has been handled,
**no geometry was guessed**.

**What closes it:** one more measurement pass resolving those two attributions - achievable by
zooming the extension-line endpoints on the archived sheet at high magnification, which is local
work needing no retrieval. The contact field itself is already provably correct because 7 x 1.1 =
7.7 matches the drawn span exactly; it is the datum reference that is open, not the pitch.

### Card-detect implementation, ready to apply

Unchanged and locked from the previous session: **DETECT LEVER -> GND** (Molex states
*Vss : GROUND*), **DETECT SWITCH -> SD_CARD_DETECT_TBD**, switch **CLOSED on card insertion, OPEN
with no card**, and **no Beta GPIO allocated** - DO NOT ROUTE until a pin-map revision.

### Status

J2 remains **DOCUMENT_OBTAINED_BUILD_PENDING**. Nothing external is needed; the remaining work is a
focused measurement pass on a sheet already in the repository.

---

## J2 — datum #1 attempted at 1100 dpi; read conflicts with arithmetic, build NOT started (2026-08-08)

Nothing modified. 186 components, 171 footprinted, 15 missing, ERC 0 real, 24 exclusions, netlist
unchanged, tree clean.

### The arithmetic case for 4.45 = first contact CENTRE

The dimension chain closes only one way. There are 8 contacts at 1.1 pitch:

- centre-to-centre across the field = 7 x 1.1 = **7.7**, which is exactly the drawn value
- edge-to-edge would be 8 x 0.8 + 7 x 0.3 = **8.5**, which is not drawn anywhere

So **7.7 is unambiguously a centre-to-centre span**, first contact centre to eighth. For the chain
`datum -> 4.45 -> 7.7` to be dimensionally coherent, 4.45 must therefore also terminate on the
**first contact centre**, giving centre8 at 12.15 and leaving 2.15 to the right end of the 14.3.

### Why that was still not accepted

The brief is explicit: *do not infer from arithmetic alone; use the arrow/extension-line endpoint
itself*. At 1100 dpi the region was legible, but the reading is **not clean enough to confirm the
arithmetic**: the 4.45 right-hand extension line and the left extension line of the adjacent
**0.8** land-width dimension fall within roughly one line-width of each other at this raster
resolution. That is precisely the distinction that separates "4.45 to centre" from "4.45 to left
edge" - a 0.4 mm shift on every contact - and the archived page (1188 x 918) does not carry enough
pixels in that region to separate them with confidence against the drawing's own ±0.05 tolerance.

**The arithmetic says centre. The pixels cannot yet confirm it. Those are not the same thing**, and
on a Class B connector the difference is 0.4 mm on all eight contacts plus a knock-on to the shell
lands.

### Status

**Datum #1: strongly indicated as first-contact-centre by dimensional closure, not yet visually
confirmed. Datum #2 (14.3 outer vs centre) not reached.** No pad table, symbol, footprint or
integration was produced. J2 remains **DOCUMENT_OBTAINED_BUILD_PENDING**.

### What would actually close it

The limitation is now **raster resolution of the archived page**, not interpretation. Options, in
order of directness:

1. A **higher-resolution copy of sheet 2** - the AllDataSheet viewer served 1188 x 918; the source
   PDF at native resolution would separate those extension lines trivially.
2. **Molex's own ECAD/STEP model** for 502570-0893, where land coordinates are numeric rather than
   drawn, removing the reading problem entirely.
3. Accepting the **arithmetic reading** (4.45 to centre) as a documented engineering judgement,
   which is defensible - the chain closes exactly and no alternative reading closes it - but is a
   decision to record explicitly, not something to adopt silently.

Option 3 is available immediately if the risk is acceptable; it would be classified
VERIFIED_VENDOR_EXACT_WITH_DOCUMENTED_DATUM_ASSUMPTION rather than plain vendor-exact.

---

## J2 — Ultra Librarian / CAD corroboration unreachable; datum still unresolved (2026-08-08)

Nothing modified. 186 components, 171 footprinted, 15 missing, ERC 0 real, 24 exclusions, netlist
unchanged, tree clean.

### CAD routes attempted, all gated

| Route | Result |
|---|---|
| `ultralibrarian.com/api/search?q=5025700893` | **404** (SPA shell, 1 MB of HTML) |
| `app.ultralibrarian.com/api/search/parts` | **404** |
| `ultralibrarian.com/details/molex/5025700893` | **404** (SPA shell) |
| `componentsearchengine.com/502570-0893/Molex` (SamacSys) | **403** |
| EasyEDA component API | no matching LCSC entry found for this MPN |

Ultra Librarian and SamacSys both serve their part pages as JavaScript applications and gate the
actual CAD downloads behind a login. Neither exposes pad coordinates to an unauthenticated fetch,
so **the CAD corroboration this session depended on could not be obtained**.

### Position unchanged

Both datums remain unresolved by the method required:

- **4.45** — arithmetic indicates *first-contact centre* (7 x 1.1 = 7.7 closes exactly; the
  edge-to-edge alternative of 8.5 appears nowhere on the sheet), but this was explicitly not to be
  accepted on arithmetic alone, and the archived raster cannot separate the extension lines.
- **14.3** — outer-to-outer vs centre-to-centre across the shell lands, untouched.

Everything else for J2 is settled and has been for two sessions: the Molex drawing is archived and
identity-verified, the contact assignment matches the existing net map exactly, and the card-detect
topology is manufacturer-stated (**DETECT LEVER = Vss GROUND**, **DETECT SWITCH** = the switched
signal, **closed on insertion**).

### The decision this now reduces to

The blocker is no longer analytical or even really a document problem - the drawing is in the repo.
It is that **one reference point cannot be read at the resolution available**, and every
independent CAD source that would settle it is behind authentication.

Three ways to close, unchanged from the previous session and now narrowed by elimination:

1. **A higher-resolution sheet 2**, or the source PDF, dropped into `vendor/Molex_5025700893/`.
2. **An authenticated CAD export** (Ultra Librarian or SamacSys account) for 5025700893.
3. **Authorise the arithmetic reading** - build with 4.45 to first-contact centre, classified
   `VERIFIED_VENDOR_EXACT_WITH_DOCUMENTED_DATUM_ASSUMPTION`. The chain closes exactly and no
   alternative reading closes it, so the engineering risk is low and fully documented.

Option 3 needs no further retrieval and would let J2 complete in one short session.

---

## J2 — BOTH DATUMS RESOLVED from exact-part CAD C429846 (2026-08-08)

Identity verified before use: EasyEDA/JLCPCB entry reports **title 5025700893**, **LCSC C429846**,
**Manufacturer MOLEX**, **Manufacturer Part 5025700893**, package `TF-SMD_5025700893`, **14 pads**.
Raw JSON archived at `vendor/Molex_5025700893/C429846_easyeda.json`.

### Pad table (1 unit = 10 mil = 0.254 mm; effective W x H after rotation)

| Pad | X | Y | eff W x H | Function |
|---|---|---|---|---|
| 1–8 | −2.806 … +4.894 @ **1.1000** | −4.338 | **0.800 × 1.500** | SD contacts |
| 9 | **−6.556** | −7.237 | **1.400 × 1.700** | shell / ground |
| 9 | **+6.344** | −7.237 | **1.400 × 1.700** | shell / ground |
| 9 | −3.006 | +7.237 | 1.500 × 1.150 | shell / ground |
| 9 | +5.894 | +7.237 | 1.500 × 1.150 | shell / ground |
| 10 | −0.706 | +7.237 | 1.500 × 1.150 | detect (to confirm vs 11) |
| 11 | +6.556 | +2.512 | 1.300 × 1.500 | detect (to confirm vs 10) |

### DATUM #1 — 4.45 is to the FIRST CONTACT CENTRE

The eight contacts sit at **exactly 1.1000 pitch**, and the first-to-last **centre span is 7.7000**
— matching Molex's drawn **7.7** to four decimal places. That proves 7.7 is a centre-to-centre
dimension, so the chain `datum → 4.45 → 7.7` must also terminate on the **first contact centre**.

**The arithmetic reading is confirmed by independent exact-part CAD, not assumed.**

### DATUM #2 — 14.3 is OUTER-EDGE-TO-OUTER-EDGE

The two bottom shell-mount lands measure **1.400 × 1.700**, matching Molex's **1.4 × 1.7** exactly.
Their centres are at −6.556 and +6.344, i.e. **centre-to-centre 12.900**. Adding one land width:

```
12.900 + 1.400 = 14.300   ← exactly Molex's 14.3
```

Centre-to-centre (12.900) does **not** match 14.3; outer-to-outer does, exactly. **14.3 is
outer-edge-to-outer-edge across the bottom shell-mount lands.**

### Molex vs C429846 cross-check — no material disagreement

| Molex dimension | C429846 | Verdict |
|---|---|---|
| contact pitch **1.1** | 1.1000 (7 intervals) | **exact** |
| contact-field span **7.7** | 7.7000 | **exact** |
| contact land width **0.8** | 0.800 | **exact** |
| shell land **1.4 × 1.7** | 1.400 × 1.700 | **exact** |
| shell span **14.3** | 12.900 + 1.400 = 14.300 | **exact (outer-to-outer)** |
| detect land **1.15** | 1.150 on pads 9(top)/10 | **exact** |

Every explicitly readable Molex dimension is reproduced. The CAD resolves only the two ambiguous
reference points and contradicts nothing, so under the standing rule it is **accepted as
corroboration** with Molex remaining primary.

**Classification when built: VERIFIED_VENDOR_DRAWING_WITH_EXACT_PART_CAD_CORROBORATION.**

### Remaining before build

One detail is still open: **which of pad 10 / pad 11 is DETECT LEVER and which is DETECT SWITCH**.
Molex states the lever is Vss/GROUND and the switch is the switched signal; the CAD numbers them
separately from the shell (9), so the assignment must be read from the C429846 symbol pin names or
by correlating pad positions against the drawing's labelled DETECT LEVER / DETECT SWITCH MOUNT
AREAs. That is local work on data now in the repository.

**The geometry blocker that held J2 for four sessions is gone.**

---

## J2 — pads 10/11 RESOLVED from local symbol metadata (2026-08-08)

No web access used. Resolved entirely from `vendor/Molex_5025700893/C429846_easyeda.json`.

### C429846 symbol pin names — decisive, not inferred

| Pad | EasyEDA name | Molex function |
|---|---|---|
| 1 | `DAT2` | DAT2 |
| 2 | `CD/DAT3` | CD/DAT3 |
| 3 | `CMD` | CMD |
| 4 | `VDD` | VDD |
| 5 | `CLK` | CLK |
| 6 | `VSS` | Vss |
| 7 | `DAT0` | DAT0 |
| 8 | `DAT1` | DAT1 |
| 9 | **`EH`** | shell / shield — **4 physical lands share this number** |
| **10** | **`DET-SW`** | **DETECT SWITCH** |
| **11** | **`VSS`** | **DETECT LEVER** |

**Pad 11 is named `VSS` — a second ground pin, distinct from pad 6.** That is exactly what Molex's
sheet 2 states: *DETECT LEVER MOUNT AREA (Vss : GROUND)*. Two independent sources, the manufacturer
drawing label and the exact-part CAD pin name, agree that the lever land is ground.

**Pad 10 is `DET-SW`** — the switched signal.

Position corroborates: pad 11 sits at x = +6.556, the right-hand side where the drawing places the
DETECT LEVER MOUNT AREA; pad 10 at x = −0.706 in the detect-switch region.

**pad 10 = DETECT SWITCH -> `SD_CARD_DETECT_TBD`**
**pad 11 = DETECT LEVER -> `GND`**

### Complete 14-land table (effective W x H after rotation)

| Pad | Function | X | Y | eff W x H | rot | AQROOT net |
|---|---|---|---|---|---|---|
| 1 | DAT2 | −2.806 | −4.338 | 0.800 × 1.500 | 90 | unused / NC |
| 2 | CD/DAT3 | −1.706 | −4.338 | 0.800 × 1.500 | 90 | `SD_CS_N` |
| 3 | CMD | −0.606 | −4.338 | 0.800 × 1.500 | 90 | `SPI_A_MOSI` |
| 4 | VDD | +0.494 | −4.338 | 0.800 × 1.500 | 90 | `+3V3` |
| 5 | CLK | +1.594 | −4.338 | 0.800 × 1.500 | 90 | `SPI_A_SCK` |
| 6 | VSS | +2.694 | −4.338 | 0.800 × 1.500 | 90 | `GND` |
| 7 | DAT0 | +3.794 | −4.338 | 0.800 × 1.500 | 90 | `SPI_A_MISO` |
| 8 | DAT1 | +4.894 | −4.338 | 0.800 × 1.500 | 90 | unused / NC |
| 9 | EH shell | −6.556 | −7.237 | 1.400 × 1.700 | 90 | `GND` |
| 9 | EH shell | +6.344 | −7.237 | 1.400 × 1.700 | 90 | `GND` |
| 9 | EH shell | −3.006 | +7.237 | 1.500 × 1.150 | 180 | `GND` |
| 9 | EH shell | +5.894 | +7.237 | 1.500 × 1.150 | 180 | `GND` |
| 10 | DET-SW | −0.706 | +7.237 | 1.500 × 1.150 | 180 | `SD_CARD_DETECT_TBD` |
| 11 | DETECT LEVER (VSS) | +6.556 | +2.512 | 1.300 × 1.500 | 270 | `GND` |

**Pad 9 carries four physical lands on one electrical number** — two bottom shell mounts
(1.4 × 1.7, the pair whose outer span is the 14.3 datum) and two top shell mounts (1.5 × 1.15).
The symbol must expose a single `SHIELD` pin numbered 9 while the footprint carries all four lands
with that number, which KiCad handles natively.

### Card-detect implementation, now fully determined

`DETECT LEVER (pad 11) -> GND` · `DETECT SWITCH (pad 10) -> SD_CARD_DETECT_TBD` ·
**closed to GND on card insertion, open with no card** · **no Beta GPIO allocated**.
`CD/DAT3` (pad 2) stays on `SD_CS_N` and is *not* conflated with the mechanical switch.

> **MECHANICAL CARD DETECT — ACTIVE LOW ON INSERTION — NO BETA GPIO ALLOCATED —
> DO NOT ROUTE UNTIL PIN-MAP REVISION**

### Not built this session

Symbol, footprint and integration were **not** produced. Every input is now local and unambiguous —
geometry, pad numbering, pin names, net map and detect topology — so the remaining work is a
mechanical build with no open questions.

---

## J2 Molex 5025700893 — physical microSD interface CLOSED (2026-08-08)

**J2 is complete.** Symbol, footprint and integration all built and pushed. This closes the last
connector on the missing-footprint list and the last item from the "close ALL remaining vendor
footprint blockers" batch. See [[01 - Hardware Core]] and [[06 - BOM and Cost Tracker]].

**Coverage: 186 components, 172 footprinted, 14 missing** (was 171 / 15). Component set identical
across the swap; J2 is the *only* changed footprint assignment. Remaining missing: `C12 C18 C19 LS1
R24 SW1`–`SW8 U14`.

### Footprint — `AQROOT_Beta:Molex_5025700893`

Classification **VERIFIED_VENDOR_DRAWING_WITH_EXACT_PART_CAD_CORROBORATION**. Primary geometry is
Molex `SD-502570-001`; the exact-part CAD `C429846` supplied coordinate corroboration and pad
numbering. Verified programmatically on write and again after:

| Check | Expected | Actual |
|---|---|---|
| Physical lands | 14 | **14** |
| Contact pitch (as a set) | single value 1.1 | **[1.1]** |
| 8-contact centre span | 7.7 | **7.7000** |
| Shell centre-to-centre | 12.9 | **12.900** |
| Shell outer-to-outer | 14.3 | **14.300** |
| Pad 9 occurrences | 4 | **4** |
| Pads 10, 11 | 1 each | **1, 1** |
| Pins 1–8 | 1 each | **1 each** |
| Numbers present | 1–11, none invented | **1–11** |

**Pad 9 is deliberately repeated on four shell lands** — two bottom mounts 1.4 × 1.7 whose outer
span *is* the 14.3 datum, and two top mounts 1.5 × 1.15. The symbol carries one logical pin 9. This
is intentional; do not "fix" it by renumbering.

Also carries: body on `F.Fab`; card-entry / ejection-travel zone and the pattern-prohibition
no-copper region on `Dwgs.User`; courtyard covering card travel; `CARD INSERTION >>` orientation
text. Both assets plot under `kicad-cli`.

### Symbol — 11 logical pins, no hidden terminals

`DAT2 · CD/DAT3 · CMD · VDD · CLK · VSS · DAT0 · DAT1 · SHIELD · DET-SW · DETECT_LEVER`

**Pin 11 is a second ground terminal distinct from pin 6**, per Molex's `Vss:GROUND` label on the
detect lever.

### Net map — 11/11 verified against an expected table

| Pin | Function | Net |
|---|---|---|
| 1 | DAT2 | *no-connect* |
| 2 | CD/DAT3 | `SD_CS_N` |
| 3 | CMD | `SPI_A_MOSI` |
| 4 | VDD | `+3V3` |
| 5 | CLK | `SPI_A_SCK` |
| 6 | VSS | `GND` |
| 7 | DAT0 | `SPI_A_MISO` |
| 8 | DAT1 | *no-connect* |
| 9 | SHIELD | `GND` |
| 10 | DET-SW | `SD_CARD_DETECT_TBD` |
| 11 | DETECT LEVER | `GND` |

The expected table was written **before** validating and every pin compared against the exported
netlist. **Zero mismatches.** This is the check that has caught every silent mis-wire in this
project — ERC alone would not have.

### The old wiring was deleted explicitly

Past integrations (notably U9) showed that deleting only the symbol leaves its wires behind and
silently lands new pins on wrong nets. The deletion set here covered the **J2 symbol, 7 wires, 2
no-connect flags and 3 orphaned power symbols**, plus the stale stock `lib_symbols` cache entry.
Nothing survived to bind a new pin to an old net.

### Regression — SPI bus A byte-identical

`SPI_A_SCK` = `J1.37 J2.5 U1.20` · `SPI_A_MOSI` = `J1.34 J2.3 U1.19` · `SPI_A_MISO` = `J1.33 J2.7
U1.21` · `SD_CS_N` = `J2.2 R25.2 U1.25` — all unchanged. `+3V3` unchanged at 73 pins. `GND` 187 →
188, the difference being exactly the old single `SH` terminal replaced by pins 9 and 11.

**Only four nets changed project-wide, and the set of changed nets not involving J2 is EMPTY.**

### Card detect — captured, deliberately not routed

Pin 10 goes to a **named** `SD_CARD_DETECT_TBD` label rather than a no-connect, so the terminal is
visible and traceable. **No GPIO was allocated and the MCU pin map is unchanged** — see
[[11 - Beta Pin Map v0.2]]. Pin 2 remains `SD_CS_N`; the mechanical switch is *not* conflated with
DAT3/CD. Switch is active-low on insertion.

### ERC — measured as a delta, and one honest correction

The identical command was run against the pre-change sheet and the post-change sheet. **The change
introduces exactly one new item and resolves none:** an `isolated_pin_label` on
`SD_CARD_DETECT_TBD`, which is the intended single-pin deferred label.

**No exclusion was added.** Fifteen sibling deferred nets — `NFC_XIN_TBD`, `NFC_RFO1_TBD`,
`NFC_AAT_A_TBD`, `CC1101_ANT_TBD`, `SX1262_RF_TBD`, `RF_ANT_TBD` and the rest — already sit
unexcluded in exactly the same class. Excluding this one would be inconsistent and would weaken ERC
for no gain.

**Correction worth recording:** the absolute figure of *"0 real violations, 24 exclusions"* quoted
in earlier sessions **does not reproduce** under the current `kicad-cli` invocation, which reports
5 `label_dangling` at error severity — *identically before and after this change*. Those five are
pre-existing and untouched. Only the delta is attributable to this work, so the delta is what is
claimed here. The absolute ERC baseline should be re-established under a single fixed invocation
before it is quoted again.

### Commits

`e1b04ab` symbol + footprint assets · `2bb1497` integration

---

## TPS63020 (U12) model normalized to the physical TI package (2026-08-10)

**Do not reintroduce a pin 16 on this part.**

### What TI actually documents

`TPS63020DSJR`, **DSJ** package. Source: **TI SLVS916I**, *TPS63020, TPS63021 — TPS6302x High
Efficiency Single Inductor Buck-boost Converter with 4-A Switches*, July 2010, **revised October
2019**, section **5 "Pin Configuration and Functions"**, page 4 — headed *"DSJ Package, 14-Pin VSON
with Exposed Thermal Pad, Top View"*.

The Pin Functions table gives:

| NAME | NO. | NAME | NO. |
|---|---|---|---|
| VINA | 1 | VIN | 10, 11 |
| GND | 2 | EN | 12 |
| FB | 3 | PS/SYNC | 13 |
| VOUT | 4, 5 | PG | 14 |
| L2 | 6, 7 | **PGND** | **-** |
| L1 | 8, 9 | **Exposed Thermal Pad** | **-** |

and states verbatim: **"The exposed thermal pad is connected to PGND."**

So the physical device is **14 numbered pins plus ONE exposed thermal pad**, and that pad *is* PGND.
**TI does not number PGND or the exposed pad.** There is no 15th signal/power pin and no 16th
terminal of any kind.

### What the project used to model, and why it was wrong

The original project symbol invented **two** pins for TI's single unnumbered terminal:
`15 = PGND` and `16 = EP`, both tied to GND. The footprint, built correctly from TI land-pattern
`4210895-2/E` and thermal-pad data `4208549-3/G`, has 14 signal lands plus one thermal land — so
symbol pin 16 had no pad. That surfaced as a KiCad schematic-parity error, *"No pad found for pin 16
(GND)"*, the moment U12 was placed during power placement.

It was never an electrical fault: both invented pins were GND, and the one physical thermal pad is
GND. It was a modelling fault.

### The AQROOT convention (binding)

**Pad/pin 15 is the AQROOT/KiCad logical identifier for TI's unnumbered exposed PGND thermal pad.
It is NOT a manufacturer package pin number.** The pin is named `PGND_EP`, electrical type
`power_in`.

This matches the convention already used elsewhere in the project library — the exposed pad takes
the next number after the last manufacturer pin: BQ25185 (10 pins) → EP 11, MAX17048 (8) → EP 9,
ST25R3916 (32) → EP 33, and now TPS63020 (14) → **PGND_EP 15**.

### What changed

1. **Project symbol** `AQROOT_Beta:TPS63020` — pin 16 (`EP`) deleted; pin 15 renamed `PGND` →
   `PGND_EP`; the misleading `Note` property replaced with the TI-verified statement above.
2. **`01_power_tree.kicad_sch`** — `lib_symbols` cache updated identically; the `(pin "16")` entry
   removed from the U12 instance; the now-orphaned wire stub `(256.54, 88.9)-(256.54, 87.63)` and
   the GND power symbol at `(256.54, 88.9)` that terminated it removed, so no dangling endpoint is
   created. No component moved, no other net touched.
3. **Footprint** `AQROOT_Beta:TI_TPS63020_DSJ` — the temporary coincident `pad 16` (added
   `788fff0` as a compatibility shim) removed. The part is back to **14 signal lands + one thermal
   land numbered 15**. TI-verified geometry, mask, paste, courtyard and via guidance untouched.
4. **PCB** — U12's `pad 16` instance removed. U12 unchanged at **(65.5000, 51.0000), rotation 0,
   TOP**; all 71 footprint positions identical.

### Verification

- Schematic netlist: 174 nets before and after; none added, none removed. **Exactly one membership
  change: GND lost the node `(U12, 16)`.** No other net altered. U12 now presents 15 pins, pin 15 →
  GND.
- Canonical ERC: **58 violations / 58 exclusions / 0 live / 0 stale** — unchanged. Removing the wire
  and power symbol created no new defect and stranded no exclusion.
- PCB DRC: 57 violations, unchanged in composition, **0 U12-related**. The schematic-parity
  `net_conflict` is gone.

### Commits

`788fff0` temporary coincident pad-16 compatibility fix (superseded) · this entry: permanent
symbol/footprint/PCB normalization

---

## PRE-ROUTING RULE SYSTEM implemented; C55 moved; routing still NOT authorised (2026-08-11)

Closes the deterministic work the *FINAL PRE-ROUTING CTO / RF RULING* required before routing.
**No signal traces were drawn. Placement is unchanged except C55.**

### BQ25185 current setting — verified against TI, not memory

**Source: TI `SLUSF65A`**, *BQ25185 1-Cell, 1A Standalone Linear Battery Charger with Power Path,
Factory Mode, and Battery Tracking VINDPM*, October 2023, **revised January 2026**.

`R36 = 18 kΩ` sits on `ILIM_VSET` (U11 **pin 7**) to GND. `R37 = 2 kΩ` sits on `ISET`
(U11 **pin 8**) to GND. Confirmed from the netlist, not inferred.

| | R36 — ILIM/VSET | R37 — ISET |
|---|---|---|
| Function | sets **input current limit AND battery regulation voltage** together | sets fast-charge current |
| Mechanism | **discrete selection table**, not an equation — §7.3.6 *Table 7-1, ILIM and VBATREG Resistor Map* (p.16) | equation (1), §7.1.1.4 *ISET Pin Detection* |
| Equation / constant | none — 18 kΩ is a table row | `ICHG = KISET / RISET`, `KISET` = 285 / **300** / 315 AΩ |
| Programmed result | **ILIM500** and **VBATREG = 4.2 V**, `VLOWV` = 3.0 V | `300 AΩ / 2000 Ω` = **150 mA** |
| Effective after device limits | EC table `ILIM`: **450 / 475 / 498 mA** at VIN = 5 V | EC table row *"Charge current accuracy at 150 mA, RISET = 2.0 kΩ"*: **135 / 150 / 165 mA** |
| Clipped? | **No.** 500 mA is a native setting. | **No.** Well under the 1 A device maximum and far above `RISET_SHORT` = 264 Ω. |

Table 7-1 was reconstructed from glyph coordinates rather than reading-order text, because the
`VBATREG` column uses merged cells spanning 2–3 resistor rows and flat extraction interleaves them
wrongly. The reconstruction closes exactly: 14 resistor rows, 7 `VBATREG` values, groups of
2/2/2/**3**/2/1/2. `VLOWV` = 3.0 V is a single cell spanning all 14 rows.

**R36 = 18 kΩ is byte-identical to TI's own design example.** §8.2.2.1: *"To configure the device for
a battery regulation voltage (VBATREG) of 4.2 V and an input current limit of 500 mA, set the
RILIM/VSET resistor to 18 kΩ."* Nothing to change.

Derived consequences: `IPRECHG` = 20 % of ICHG = **30 mA**; `ITERM` = 10 % of ICHG = **15 mA**;
`VSYS_REG` = 4.5 V; input budget at ILIM500 ≈ 475 mA × 5 V = **2.4 W**, and SYS has priority over
charging, so the 640 mA `+3V3` burst enters supplement mode from the battery as architected.

> **REPORTED, NOT CHANGED — ISET is far below what this log previously anticipated.** The
> BQ25185 package entry (2026-08-07) records *"charge current setting (ISET, start ~500 mA pending
> enclosure thermal testing)"*. The implemented `R37 = 2 kΩ` gives **150 mA**, not 500 mA. Against
> the 2000 mAh pack that is **0.075 C** and a >13 h charge from empty. It is electrically valid — it
> is conservative, it will not provoke a thermal problem, and it is inside every device limit — so
> per the ruling **no resistor value was changed**. Closing this is a charging-policy decision:
> 500 mA needs `RISET = 600 Ω`, 300 mA needs `1 kΩ`. **CTO decision required before BOM lock.**

### Fabrication stackup — SELECTED

**JLCPCB `JLC04161H-7628`**, from JLCPCB's published impedance/stackup tables. The name decodes to
JLC / 04 layers / 1.6 mm / 1 oz outer / **H** = half-ounce inner / 7628 prepreg — exactly the
architecture the ruling locked.

| | |
|---|---|
| Finished thickness | 1.6 mm |
| Outer copper | 0.035 mm (1 oz) |
| **F.Cu → In1 dielectric** | **7628 prepreg, 0.2104 mm, Dk 4.4** |
| Inner copper | 0.0152 mm (0.5 oz, H) |
| Core | 1.065 mm, Dk 4.6 |
| In2 → B.Cu dielectric | 7628 prepreg, 0.2104 mm, Dk 4.4 |
| Min trace / space | 3.5 mil = 0.0889 mm |
| Min via (drill) | 0.20 mm |
| Impedance control | offered; requires **FR-4 TG155** selected at order time, not the 4L default TG135–140 |

Sum check: 0.035 + 0.2104 + 0.0152 + 1.065 + 0.0152 + 0.2104 + 0.035 = **1.5862 mm**, + soldermask
≈ 1.6 mm. The arithmetic closing is the reason this stackup is trusted rather than a reconstruction.

### USB 2.0 impedance geometry — 90 Ω differential

Computed with Hammerstad–Jensen microstrip plus the Wheeler thickness correction and the standard
edge-coupled differential form `Zdiff = 2·Z0·(1 − 0.48·e^(−0.96·s/h))`, against the **actual**
stackup above.

| | |
|---|---|
| Routing layer | **F.Cu**, over the continuous In1 GND plane |
| Trace width | **0.30 mm** |
| Pair gap | **0.20 mm** |
| Reference plane | In1.Cu, h = 0.2104 mm |
| Copper | 0.035 mm |
| **Result** | **Zdiff = 89.3 Ω** (target 90 Ω), Z0se = 55.3 Ω, εeff = 3.283 |
| Single-ended 50 Ω, same stack | W = 0.365 mm → 49.9 Ω |

Both figures are ~3.4× JLCPCB's 0.0889 mm minimum, so nothing here is at the fab edge.
**Confirm against JLCPCB's own impedance calculator before ordering impedance-controlled boards.**

**E4 In2 excursion — a deliberate discontinuity, not an oversight.** On In2 the only continuous
reference is In1, across the **1.065 mm** core. The same 0.30/0.20 geometry there presents
**≈133 Ω**; holding 90 Ω would need W ≈ 1.06 mm / S ≈ 0.36 mm, which does not fit a 3.5 mm corridor
that must also carry VBUS at ≥1.0 mm separation. Even 0.60/0.40 only reaches ≈117 Ω.
**Decision: carry the F.Cu geometry unchanged through E4.** Coupling and intra-pair skew stay
constant, and the excursion is electrically short — 7.2 ps/mm × 26 mm ≈ **190 ps** one way at
Γ ≈ 0.19, against Full-Speed USB edges of 4–20 ns. **Cap the total In2 excursion at 30 mm.**

> **ROUTING-TOOLING ITEM.** `USB_D_P_MCU` / `USB_D_N_MCU` put the polarity marker *mid-name*, so
> KiCad's differential-pair engine will not auto-pair them and `inDiffPair()` will not match. The
> width/gap rules in the DRU still bind. Either rename to `USB_DP_MCU`/`USB_DM_MCU` in a later
> schematic pass or route the pair manually. **Not a blocker — connectivity is correct.**

### Layer architecture

`F.Cu` / `In1.Cu` / `In2.Cu` / `B.Cu` already existed and are unchanged. What changed is policy:
**In1 is now the board-wide continuous GND reference with no intentional splits.** The `915 KEEPOUT`
and `433 KEEPOUT` rule areas previously blocked copper on **all four** layers, which would have
forced a hole in In1 straight through both antenna bands. Their layer set is now
**F.Cu + In2.Cu + B.Cu**, and their own keepout flags are reduced to *copper pour not allowed*.
Everything net-aware or layer-aware moved into `aqroot-Beta.kicad_dru`, which a rule area cannot
express. **No copper zones were created** — pours would obscure rule verification at this stage.

### RF layer policy as implemented

| Layer | 915 band (all X, Y 88–114) | 433 band (X 0–52.5, Y 115–138) | Mechanism |
|---|---|---|---|
| F.Cu | no tracks; **pads allowed** (E2 + J1) | same | DRU *"RF bands: F.Cu carries no ordinary copper"*, with a named `E2_BUTTON_ESCAPE` exception |
| In1 | **solid GND, continuous, no split** | same | In1 removed from both keepouts; DRU *"In1.Cu carries GND only"* |
| In2 | E5 corridor contents only, no pour | same | DRU corridor + netclass rules; pour blocked by the rule area |
| B.Cu | **no tracks, no pads, no exceptions** | same | DRU *"RF bands: B.Cu is pristine"* |
| Vias | **none in band, any layer** | same | DRU *"RF bands: no vias in band on any layer"* |

Audited against the actual board: the only copper inside either band is **F.Cu button pads** —
`SW2 SW3 SW4 SW5 SW6 SW8`, signal + GND pads — plus J1's body, whose pads all fall outside.
**No B.Cu pad intrudes into either band**, so the no-exception B.Cu rule is satisfied today. `U8`
(y ≥ 117.2) and `U7` (y ≥ 138.6) sit outside the 433 band's Y range; `J2`'s outline clips the band
but none of its pads do.

`BTN_UP_N`, `BTN_LEFT_N` and `BTN_RIGHT_N` belong to buttons whose bodies sit **inside** a band, so
they cannot use E5 and are the E2 short-escape exception on F.Cu. `BTN_A_N`, `BTN_B_N`,
`BTN_DOWN_N` and `BTN_HOME_N` are south of the band and cross on In2 — which is exactly the four-net
list the ruling authorised for E5, and the split is now encoded in two netclasses rather than a
comment.

### E5 and E4 as implemented

Rule areas on **In2.Cu only**: `E5 CORRIDOR C-W` X 8–20, `E5 CORRIDOR E4` X 53.0–56.5,
`E5 CORRIDOR C-E` X 58–70. The X geometry is exactly as ruled and was **not** widened.

The areas extend to **Y 84–142** (C-W) and **Y 84–118** (E4, C-E) — 4 mm past each band — purely so
that a segment entering or leaving a band is still *wholly* enclosed by its corridor for
`enclosedByArea()`. Without the margin, every legal crossing would false-positive at the band edge.
The corridors carry no restriction of their own outside the bands, so the margin costs nothing.

`E4 USB LANE` X 53.00–54.30 · reserved guard X 54.30–55.40 (**1.10 mm**, no copper) ·
`E4 VBUS LANE` X 55.40–56.50. Worst-case USB-to-VBUS copper gap is therefore **1.10 mm ≥ 1.0 mm**,
and a redundant explicit 1.0 mm clearance rule backs it up. **No isolated GND finger. No stitching
via inside Y 88–114** — the blanket in-band via prohibition already forbids one.

**+3V3 crossing width: 0.60 mm on In2 (enforced min 0.50, max 1.00).** Derived, not adopted. The
current that must actually cross is only the load *south* of Y = 88: U8 SX1262 TX burst ≈118 mA,
J2 microSD write ≈100 mA, U7 CC1101 RX ≈17 mA, plus pull-ups — worst credible concurrency ≈235 mA,
+30 % → **305 mA design**. IPC-2221B on 0.5 oz inner needs 0.30 mm for that at ΔT = 10 K; 0.60 mm
gives **ΔT ≈ 1.8 K** and ≈10 mV over the 26 mm crossing. It lands inside the CTO's expected
0.5–1.0 mm class but the number comes from the current budget, and it is emphatically **not** the
1.0 A full-rail figure — that current never crosses the band.

### Global clearance and the fine-pitch audit

**The global 0.20 mm clearance was kept.** It is ~2.2× JLCPCB's 0.0889 mm floor, and lowering it to
silence a few packages is exactly what the ruling forbade. `min_track_width` 0.20 → **0.15 mm**
(floor only), `min_via_annular_width` 0.10 → **0.125 mm**. **`min_clearance` stays 0.0 deliberately**
— a non-zero global floor in KiCad clamps custom rules *upward* and would re-create every false
fine-pitch error this pass exists to remove.

All 56 baseline `clearance` errors were same-footprint vendor land patterns:

| Ref | Footprint | Pad pair class | Actual gap | Vendor validity | Min rule needed |
|---|---|---|---|---|---|
| U9 | ST25R3916_AQET, QFN-32 0.5 mm | lead → exposed pad 33 | **0.1750 mm** | ST land pattern (AQET, built from ST docs) | 0.05 mm |
| U9 | same | corner lead → lead (1–32, 8–9, 16–17, 24–25) | **0.0621 mm** | same | 0.05 mm |
| U13 | SOT-563, TPS61023 | adjacent leads | 0.1500 mm | TI SOT-563 | 0.13 mm |
| U16 | VSSOP-8 0.65 mm, TCA9517ADGK | adjacent leads | 0.1500 mm | TI VSSOP | 0.13 mm |
| D3 D4 D5 D6 | SOT-563, TPD4E1B06DRLR | adjacent leads | 0.1500 mm | TI SOT-563 | 0.13 mm |

Seven rules, each scoped `A.Type == 'Pad' && B.Type == 'Pad'` inside **one named footprint**. No
routing clearance anywhere is weakened, and no track, via or pour can inherit the exception.
**Result: all 56 gone.**

> **A trap worth recording.** The first attempt also raised per-netclass `clearance` to
> 0.25–0.30 mm on the power classes. That immediately manufactured **27 new** false errors — `J3`
> USB-C ×11, `U11` WSON 0.4 mm pitch ×4, `U14` ×4, `J1` FH69 0.5 mm pitch ×5, `U12` ×2 — the same
> failure mode, one rung up. **Fix: netclass clearance is 0.20 mm for every class**, and the
> elevated figures are DRU rules scoped to `A.Type != 'Pad' && B.Type != 'Pad'` — routing clearance
> applied to routed copper, never to a vendor land pattern. Nothing electrical is lost: IPC-2221
> needs ~0.1 mm even at the backlight string's <30 V.
>
> Also: `A.memberOfFootprint('D[3-6]')` **silently matches nothing.** KiCad's expression wildcards
> are `*` and `?` only — character classes are not supported and fail quietly rather than erroring.
> That is why D3–D6 are four separate rules.

### J2 microSD shell — the two board-edge errors

Molex 5025700893's shell GND tab sits **0.213 mm** from `Edge.Cuts` by vendor geometry (the shell
aligns with the card opening), against the 0.5 mm board rule. Encoded as one named rule scoped to
J2 at **0.20 mm**, the mainstream copper-to-outline floor. This converts a recurring
"connector-edge accepted" error into an explicit, greppable exception — and it is carried as a
**FAB confirmation item**, because 0.20 mm is *at* the floor, not inside it.

### Netclasses, via classes, switch nodes

14 netclasses, 61 patterns. Via classes are mainstream through vias only — **no microvias, no
blind/buried vias**, all three explicitly disallowed:

| Via class | Drill | Pad | Annular ring |
|---|---|---|---|
| GENERAL_SIGNAL | 0.30 mm | 0.60 mm | 0.150 mm |
| POWER | 0.40 mm | 0.80 mm | 0.200 mm |
| THERMAL | 0.25 mm | 0.55 mm | 0.150 mm |

None sits at JLCPCB's 0.20 mm / ~0.1275 mm floor, per *"do not select minimum-fab geometry unless
routing density actually requires it"*.

| Netclass | Nets | Design current | Outer width | In2 | Via | Notes |
|---|---|---|---|---|---|---|
| `BAT_MAIN` | `BAT_PROTECTED_P`, `BAT_CONNECTOR_P` | 1.5 A cont., **3.125 A** OCP peak | **1.50 mm** (min 1.00) | outer only — 0.5 oz would need 2.73 mm | POWER | 0.30 mm routed clearance |
| `SYS_MAIN` | `BQ25185_SYS` | 1.0 A | **1.00 mm** (min 0.60) | outer only — needs 1.56 mm inner | POWER | 0.25 mm routed clearance |
| `P3V3` | `+3V3`, `ACC_3V3_SW` | 1.0 A design, 0.64 A measured peak | **0.60 mm** (min 0.40) | **0.60 mm in corridors only** | POWER | never poured under an antenna |
| `VBUS_CHG` | `USB_VBUS_CHG`, `USB_VBUS_RAW` | **0.5 A** (= verified ILIM500) | **0.50 mm** (min 0.35) | E4 east lane only | POWER | 0.25 mm routed clearance |
| `NFC_5V_PA` | `NFC_5V_PA_PENDING` | 0.5 A TX burst | **0.60 mm** (min 0.35) | — | POWER | 0.25 mm routed clearance |
| `LED_BOOST` | `LED_BOOST`, `LED_K`, `LED_A1..A4` | 0.05 A at >20 V | 0.30 mm | — | GENERAL_SIGNAL | **clearance-driven**, 0.30 mm routed |
| `SWITCH_NODE` | `Net-(L1-Pad1)`, `Net-(L1-Pad2)`, `Net-(U13-SW)`, `BL_SW` | pulsed | **0.60 mm** (min 0.40) | banned in bands | POWER | see below |
| `USB_D` | 6 USB data nets | — | 0.30 mm / gap 0.20 | E4 west lane only | GENERAL_SIGNAL | 90 Ω |
| `E5_CROSSING` | the 18 authorised signals | — | 0.20 mm | corridors | GENERAL_SIGNAL | |
| `E2_BUTTON_ESCAPE` | `BTN_UP_N`, `BTN_LEFT_N`, `BTN_RIGHT_N` | — | 0.20 mm | **not** authorised on In2 | GENERAL_SIGNAL | F.Cu in-band exception |
| `RF_DEFERRED_NFC` | 12 U9 nets | — | — | — | — | **all routing disallowed** |
| `RF_DO_NOT_ROUTE` | `CC1101_ANT_TBD`, `RF_ANT_TBD`, `SX1262_RF_TBD` | — | — | — | — | **all routing disallowed** |

Switch-node rules encoded: **no switch node in either antenna band**, none over `MK1` or `U5`
courtyards, and a 0.40 mm minimum width. **`U11 BQ25185` has no switch node — it is a *linear*
charger with a power path**, so the ruling's "keep-small" instruction applies to U12, U13 and U17
only. Not encodable and therefore carried into routing: minimum loop area, no routing on adjacent
layers directly beneath L1/L2/L3, and In1 kept solid under each inductor.

### NFC route-now / defer — now enforced, not just documented

`RF_DEFERRED_NFC` covers `RFO1 RFO2 RFI1 RFI2 AAT_A AAT_B EXT_LM CSI CSO XIN XOUT MCU_CLK` and
disallows track **and** via outright. `RF_DO_NOT_ROUTE` does the same for the U7/U8 pin-21 stamp RF
pads. Routing any of them is now an immediate DRC error rather than something a reviewer must spot.
U9's digital and power side — `SPI_B_*`, `NFC_CS_N`, `NFC_IRQ`, `+3V3`, `NFC_5V_PA_PENDING`,
`NFC_VDD_*`, `AGDC`, `GND` — is deliberately **not** in either class and may be routed.

### WROOM antenna keepout — created, and it outranks In1

**X 0–6, Y 17–35, all four copper layers**, no tracks / vias / pads / pour. The 6 mm boundary is
not invented: it is the `ESP32-S3-WROOM-1` footprint's own `B.Fab` antenna line at local X = 6,
and the module's pads start at X = 7.04, so nothing is caught. This is **the single authorised void
in the continuous In1 GND reference** and it takes local precedence, exactly as the ruling directs.

Footprints are left *allowed* in the area for one specific reason: U1's courtyard, as shipped,
spans (−15.0, 2.0)–(26.2, 50.0) and overlaps the keepout, so a footprint keepout would report U1
against its own antenna zone. Component keepout is a placement rule and placement is locked.

### C55 — moved; the ≤3.0 mm target is NOT met, and the reason is structural

| | Before | After |
|---|---|---|
| Position | (10.000, 19.000) rot 0 | **(22.225, 29.400) rot 270** |
| Footprint | `C_0805_2012Metric` | **`C_0603_1608Metric`** |
| Courtyard | 8.255–11.745 × 17.975–20.025 | 21.450–23.000 × 27.875–30.925 |
| **→ U9 pin 8 (VDD_TX)** | 14.005 mm | **4.875 mm** |
| **→ U9 pin 10 (VDD_TX)** | 15.148 mm | **4.469 mm** |

Pad 1 (`NFC_5V_PA_PENDING`) faces north toward U9 pins 8/10; pad 2 (GND) faces south, so the return
loop closes away from U9's RF pins. **Measured from pad centres in the saved board, not estimated.**

**The ≤3.0 mm electrical target is NOT achieved.** This was established by exhaustive search, not by
inspection: every 0.05 mm position × 4 rotations × {0603, 0805} in X 14–34, Y 14–34, rejected
against every locked F.Cu courtyard at 0.15 mm and against the WROOM keepout. **680,610 legal
positions**; the best possible worst-case distance is **4.813 mm** (0603) / **4.900 mm** (0805).

The blockers are **C50** (10 nF, VDD_RF) and **C52** (1 nF, VDD_AM), which occupy the only space
within 3 mm of U9's south edge, plus U9's own courtyard. The gap between U9's south edge
(y = 24.995) and C50/C52's north edge (y = 26.125) is **1.13 mm** — shorter than an 0603 courtyard
(1.55 mm) and an 0805 courtyard (2.05 mm). The strip west of U9 is **0.98 mm**. Only an 0402 would
fit, and 2.2 µF ≥10 V X7R does not exist in 0402. Neither C50 nor C52 is on the authorised-move
list, so **4.875 mm is the honest floor under the current placement lock**.

> **FLAGGED FOR THE NEXT PLACEMENT PASS:** the near-U9 space is allocated to a 10 nF and a 1 nF cap
> while the TX bulk reservoir and the 100 nF HF decoupler sit 4.5–4.9 mm away. `C19` (100 nF, same
> net) is 4.309 mm from pin 8 — it was never close either. If U9 TX-burst rail droop measures badly
> on Beta, **swapping C55/C19 with C50/C52 is the fix**, and it is a placement decision, not a rule
> decision.

### C55 package / BOM — a hard constraint conflict, reported not papered over

Footprint changed **0805 → 0603** under the ruling's explicit authorisation. Value unchanged at
2.2 µF. Schematic `Footprint` and `Package` fields updated to match so parity stays clean;
`Voltage = 16V` and `Dielectric = X7R` were already correct and were left alone.

Rationale — and it is *not* the 0.087 mm distance gain, which is immaterial:

**No 2.2 µF, ≥10 V, X7R MLCC in either 0603 or 0805 has a documented maximum height ≤ 0.80 mm.**

* **0805** standard thickness classes are 0.60 / 0.85 / 1.25 mm, and 2.2 µF needs the thickest.
  Verified: **Murata `GRM21BR71E225KA73`** (0805, X7R, 2.2 µF, 25 V) reference sheet gives
  **T = 1.25 ± 0.15 mm → 1.40 mm max**. That is **0.60 mm over** the panel ceiling.
* **0603** at 2.2 µF is the 0.80 mm class, i.e. **0.80 ± 0.10 → 0.90 mm max** — **0.10 mm over**.

So the footprint choice cannot solve the height problem, but it changes a 0.60 mm miss into a
0.10 mm miss — one is hopeless, the other is closable by tolerance selection or a small enclosure
change. 0603/16 V X7R also meets the DC-bias requirement with margin (typical retention at 5 V
gives ≈1.4–1.75 µF against the ≥1.2 µF floor), whereas 0603/10 V would be marginal.

**MPN: still VERIFY.** Required: 2.2 µF, **16 V**, X7R, 0603, documented **max** height, and a
manufacturer DC-bias curve proving **≥1.2 µF at 5.0 V**. No candidate has been confirmed against
both curves in this pass.

**Note the move imposed the height constraint.** At (10, 19) C55 was at X < 12 — *outside* the
`PANEL SHADOW (TOP ≤0.8 mm) X12-62 Y9-78` — and had no height limit at all. Every position that
improves on 14.005 mm is inside the shadow; the closest legal position outside it is ~15 mm, i.e.
worse than doing nothing. **The trade was taken deliberately** and §24 of the ruling anticipates it
("C55 joins this list").

### C45 / C47 / C49 / C51 — left in place, as the ruling permits

| Ref | Value | Net | → U9 pad | Before | After |
|---|---|---|---|---|---|
| C45 | 2.2 µF | `NFC_VDD_D` | pad 3 | 13.176 mm | **13.176 mm** |
| C47 | 2.2 µF | `NFC_VDD_A` | pad 7 | 13.186 mm | **13.186 mm** |
| C49 | 2.2 µF | `NFC_VDD_RF` | pad 9 | 13.835 mm | **13.835 mm** |
| C51 | 2.2 µF | `NFC_VDD_AM` | pad 11 | 15.323 mm | **15.323 mm** |

**No opportunistic move was possible, and none was made.** These are 0805s and their footprints are
*not* authorised to change. The distance is dominated by X (they sit at x = 9.05, U9 at x ≈ 22), and
freeing C55's old slot at (10, 19) only opens space *north* in the same x column — no X improvement
exists. The ruling's own instruction applies: *"Otherwise leave them."*

### U9 decoupling verdict

| Cap | Value | Rail | U9 pad | Distance |
|---|---|---|---|---|
| C19 | 100 nF | `NFC_5V_PA_PENDING` | 8 / 10 | 4.309 / 5.018 mm |
| **C55** | 2.2 µF | `NFC_5V_PA_PENDING` | 8 / 10 | **4.875 / 4.469 mm** |
| C45 | 2.2 µF | `NFC_VDD_D` | 3 | 13.176 mm |
| C47 | 2.2 µF | `NFC_VDD_A` | 7 | 13.186 mm |
| C49 | 2.2 µF | `NFC_VDD_RF` | 9 | 13.835 mm |
| C51 | 2.2 µF | `NFC_VDD_AM` | 11 | 15.323 mm |

**Verdict: improved but not good.** The TX bulk path is 3× shorter than it was; every internal
regulator rail is still 13–15 mm from its own pin. **All four internal regulator rails —
`VDD_D`, `VDD_A`, `VDD_RF`, `VDD_AM` — plus `VDD_TX` are flagged for Beta TX-burst rail-droop
measurement**, as the CTO required. Measure at the U9 pin, not at the capacitor.

### Thermal-via plan — audited, nothing added

**The board currently contains 0 tracks, 0 vias and 4 zones.** No footprint has integral thermal
vias, and none is *defective* for lacking them — the stock land patterns ship without vias by
design because via placement is a layout decision. Per the ruling, **no vias were added**.

| Ref | Part | Exposed pad | Vendor guidance | Current | Proposed |
|---|---|---|---|---|---|
| U1 | ESP32-S3-WROOM-1 | pad 41, **3.9 × 3.9 mm** | Espressif reference PCB shows a via array under the module GND pad | none | **3 × 3** THERMAL @ 1.2 mm |
| U9 | ST25R3916-AQET | pad 33, **3.45 × 3.45 mm** | **VERIFY** — DS12484 Rev 3 gives the VFQFPN32 outline but **no thermal-via guidance**; needs ST's layout app note | none | **3 × 3** THERMAL @ 1.1 mm |
| U12 | TPS63020 DSJ | pad 15, **2.85 × 1.58 mm** | **VERIFY** — SLVS916I layout section not read in this pass | none | **3 × 1** THERMAL @ 1.0 mm |
| U5 | MAX98357A TQFN-16-1EP | pad 17, **1.23 × 1.23 mm** | **VERIFY** | none | **1** central THERMAL (0.55 mm pads will not tile a 1.23 mm pad) |
| U11 | BQ25185 DLH0010A | pad 11, **0.9 × 1.5 mm** | SLUSF65A Fig. 8-9 shows a board layout example | none | **1** central THERMAL |
| U14 | MAX17048 T822 | pad 9, **0.8 × 1.38 mm** | **VERIFY** | none | **1** central THERMAL |
| U7 / U8 | Ebyte modules | no EP — GND stamp pads act thermally | vendor | none | GND stitching at routing |

> **CORRECTION to the ruling's audit list: `U13` (TPS61023) has NO exposed pad.** It is a plain
> SOT-563. Same for `U17` (SOT-353), `U16` (VSSOP-8), `U2`/`U3` (TSSOP-24), `U4` (LGA-14),
> `U10`/`U15` (SOT-23-6). `MK1`'s pad 3 is 0.3 × 0.3 mm and is not a thermal pad.

### Panel-height BOM ledger — 33 refs, and U9 already fails

Every **TOP-side** part inside `PANEL SHADOW X12-62 Y9-78`, all requiring **documented maximum**
height ≤ 0.80 mm. Height is **not** inferred from package.

`C18 C19` (0402) · `C39 C46 C48 C50 C52 C53 C54` **`C55`** (0603) · `D3 D4 D5 D6` (SOT-563) ·
`R29 R46 R51 R52 R53 R54 R55 R56 R57 R58 R59 R60 R61 R62 R63 R64 R66 R67` (0603) · **`U9`**

> **`U9` ALREADY EXCEEDS THE CEILING — measured, not suspected.** ST25R3916 DS12484 Rev 3,
> *Table 134, VFQFPN32 mechanical data*: **A = 0.800 / 0.900 / 1.000 mm**. Max **1.00 mm** against a
> 0.80 mm ceiling. And standard 0603 X7R is 0.80 ± 0.10 → **0.90 mm max**, so most of the 0603 rows
> above are likely over too.
>
> **This means the 0.80 mm panel ceiling is probably wrong, not the parts.** It reads like a
> *nominal* figure being applied as a *maximum*. Resolve the ceiling against enclosure CAD before
> chasing 33 individual MPNs — otherwise the ledger cannot be closed at all. **BLOCKS_FAB.**

### Samtec J5 — FAB blocker, not a routing blocker

Body depth **B** and the finished-hole requirement are still unverified. J5 is a **through-hole
right-angle 2×13 header at (37.0, 0.0) on B.Cu**, whose position, pad geometry and net assignment
are all fixed; nothing about routing to it depends on the unresolved dimensions. Its pads are also
inside `HEADER RESERVED` (X 18.5–55.5, Y 0–8.5), which already keeps routing out of the area.
**Classification: BLOCKS_FAB only.** No J5 schematic metadata was changed.

One genuine parity item surfaced and was **left alone** per the ruling: J5's PCB footprint is
`AQROOT_Beta:Samtec_TSW-113-08-G-D-RA` while its symbol's `Footprint` field still says
`Connector_PinHeader_2.54mm:PinHeader_2x13_P2.54mm_Vertical`. Metadata drift, not connectivity.

### The rule system was tested in both directions

A rule set that reports zero errors on an unrouted board proves nothing. Both halves were checked
on **throwaway copies** of the board.

**15 deliberate violations → every one caught by its named rule:** B.Cu track in band · In2 track
in band outside all corridors · unauthorised net (I2C) in a corridor · via in band · non-GND track
on In1 · deferred NFC net routed · stamp RF pad net routed · USB pair in C-W · VBUS in the E4 west
lane · track in the WROOM keepout · microvia · F.Cu track in the 433 band · switch node in band ·
+3V3 crossing at 2.00 mm (**max** fired) and at 0.30 mm (**min** fired) · BAT_MAIN at 0.2 mm.

**15 authorised constructs → 0 errors:** E5 signal crossings on In2 through C-E and C-W · +3V3 at
0.60 mm through C-W · USB pair in the E4 west lane · VBUS in the E4 east lane · E2 button escape on
F.Cu inside the band · GND on In1 · BAT_MAIN at 1.50 mm · SYS_MAIN at 1.00 mm · +3V3 at 0.60 mm on
F.Cu · GENERAL_SIGNAL and POWER vias outside the bands.

> **Harness bug worth recording, because it nearly produced a false pass.** KiCad's SWIG
> `NETINFO_ITEM` proxies get reused if Python collects them between `SetNet()` calls, silently
> assigning a track the *previous* call's net. Two injected test tracks came out on the wrong net
> and one "legal control" never tested what it claimed. **Hold net references and assert
> `GetNetname()` after `SetNet()`** in any pcbnew script.

### DRC — before / after taxonomy

Identical invocation both times: `kicad-cli pcb drc --severity-all --schematic-parity`.

| Class | Before | After |
|---|---|---|
| **A. real electrical / layout defects** | **0** | **0** |
| **B. connector-edge accepted** | 2 `copper_edge_clearance` (J2 shell) | **0** — named J2 rule, carried as FAB item |
| **C. fine-pitch** | **56** `clearance` errors | **0** — 7 named intra-footprint rules |
| **D. silkscreen / cosmetic** | 234 warnings | 231 warnings |
| **E. unrouted expected** | 499 unconnected | 499 unconnected |
| **F. intentional deferred RF** | 0 | 0 (nothing routed to flag) |
| **TOTAL ERRORS** | **58** | **0** |
| Total violations | 292 | 231 |

Silkscreen was not chased: none of it obscures a pad or an assembly-critical reference, and it will
move again when reference designators are placed for assembly. The 259 schematic-parity items are
**all** `warning` — 187 empty-`Description`-field mismatches and 72 library-prefix artifacts of
`kicad-cli`'s comparison (PCB stores the bare footprint name, the symbol stores `Lib:Name`). The
only substantive one is J5, above.

### Preservation

* **Connectivity: identical.** 174 nets before and after; zero added, zero removed, **zero
  membership changes**. Compared node-set by node-set against `git archive HEAD`.
* **ERC: identical.** 116 reported / 58 excluded / **58 live** (23 `isolated_pin_label`, 22
  `pin_to_pin`, 8 `unconnected_wire_endpoint` — all warnings — plus **5 `label_dangling` at error
  severity**). **Zero added, zero removed** versus HEAD under the same invocation. The 5 errors are
  the pre-existing deferred-label set this log already corrected the record on; the "58/58/0 live"
  phrasing does not reproduce under `--severity-all`.
* **Placement: 187 footprints, exactly one changed — C55.** Verified position, rotation, side and
  footprint ID for all 187 against HEAD.

### Still BLOCKS_ROUTING

1. **BQ25185 ISET charging policy.** `R37 = 2 kΩ` → 150 mA = 0.075 C. Electrically valid, so it was
   not touched, but the CTO must confirm 150 mA or choose 600 Ω / 1 kΩ.
2. **USB diff-pair net naming.** `USB_D_P_MCU` / `USB_D_N_MCU` will not auto-pair in KiCad. Decide
   rename-vs-manual before the pair is routed.

### Still BLOCKS_FAB

1. **Panel ceiling 0.80 mm is probably a nominal figure misapplied as a maximum** — U9 is 1.00 mm
   max by datasheet and standard 0603 X7R is 0.90 mm max. Resolve against enclosure CAD; 33 refs
   cannot be closed otherwise.
2. **C55 MPN** — 2.2 µF / 16 V / X7R / 0603 with a documented max height *and* a DC-bias curve
   showing ≥1.2 µF at 5.0 V.
3. **Samtec J5** — body depth B and finished-hole requirement.
4. **USB 90 Ω geometry** — confirm 0.30/0.20 against JLCPCB's own impedance calculator, and select
   **FR-4 TG155** at order time (the 4-layer default is TG135–140 and is not impedance-controlled).
5. **J2 shell edge clearance 0.20 mm** — at the fab floor; confirm with JLCPCB.
6. **Thermal-via vendor guidance** for U9, U12, U5, U14 (marked VERIFY above).

### Files changed

`aqroot-Beta.kicad_dru` (new, 45 rules) · `aqroot-Beta.kicad_pro` (14 netclasses, 61 patterns, via
and track presets, board rule floors) · `aqroot-Beta.kicad_pcb` (2 rule areas relayered, 6 created,
4 annotations, C55) · `04_spi_b_radios_nfc.kicad_sch` (C55 `Footprint` / `Package` / `Note`).

**ROUTING NOT STARTED. No signal trace was drawn in this pass.**


---

## FINAL PRE-ROUTING ELECTRICAL CLOSURE: ISET locked at 300 mA, USB pair renamed (2026-08-11)

Closes the two `BLOCKS_ROUTING` items left open by the pre-routing rule pass. **No traces drawn.
No component moved.** Both changes are electrically minimal and were verified by delta, not by
assertion.

### 1. BQ25185 charge current locked at 300 mA

| | Before | After |
|---|---|---|
| `R37` (U11 pin 8, `ISET` → GND) | **2 kΩ 1 %** | **1 kΩ 1 %** |
| `ICHG` = `KISET / RISET` | 300 AΩ / 2000 Ω = 150 mA | **300 AΩ / 1000 Ω = 300 mA** |
| Min / typ / max from the `KISET` spread (285/300/315 AΩ) | 135 / 150 / 165 mA | **285 / 300 / 315 mA** |
| Bound by TI's `ICHG_ACC` spec (±10 %, ICHG ≥ 40 mA) | 135–165 mA | **270–330 mA** |
| Rate against the 2000 mAh Beta pack | 0.075 C | **0.15 C** |
| `IPRECHG` (20 % of ICHG, VBAT < VLOWV) | 30 mA | **60 mA** |
| `ITERM` (10 % of ICHG) | 15 mA | **30 mA** |

`RISET` = 1 kΩ is far above `RISET_SHORT` = 264 Ω and 300 mA is far below the 1 A device maximum, so
**nothing is clipped**. 1 kΩ is also TI's own figure — `SLUSF65A` §8.2.2.2: *"To configure the device
for a fast charge current of 300 mA, set the RISET resistor to 1 kΩ."*

**`R36` = 18 kΩ is untouched.** The input current limit is therefore unchanged at **ILIM500** —
450 / 475 / 498 mA per the EC table — and `VBATREG` remains 4.2 V with `VLOWV` 3.0 V. Verified in
the saved board, not assumed: `R36 = 18k 1%`, `R37 = 1k 1%`.

Both the schematic symbol **and** the PCB footprint `Value` field were updated together, so the
change adds no `footprint_symbol_field_mismatch` parity warning (parity count is unchanged at 259).

### 2. Power netclass recalculation — no width target changes

Recomputed against the already-selected `JLC04161H-7628` copper weights (1 oz outer / 0.5 oz inner).
**No conductor was widened, because nothing needed widening.**

| Netclass | Sizing case | Does 300 mA charge affect it? | Width |
|---|---|---|---|
| `VBUS_CHG` | 0.5 A, set by ILIM500 — **and ILIM did not change** | No. Charging draws from the *same* capped input; it re-allocates the budget, it does not raise it. | **0.50 mm, unchanged** |
| `BAT_MAIN` | **discharge**: 1.5 A continuous, 3.125 A `IBAT_OCP` | No. 300 mA into the pack is ~10 % of the sizing case. | **1.50 mm, unchanged** |
| `SYS_MAIN` | system load ≈750 mA at SYS to make 640 mA at 3.3 V through the TPS63020 | No. SYS is sized by the load, not by charge current; beyond ILIM the battery supplements and current reverses at similar magnitude. | **1.00 mm, unchanged** |
| `P3V3` `NFC_5V_PA` `LED_BOOST` `SWITCH_NODE` `USB_D` | — | No. Downstream of SYS, unaffected. | **unchanged** |

For scale: IPC-2221B needs **0.057 mm** for 300 mA on 1 oz outer copper at ΔT = 10 K. Every existing
floor already exceeds that by an order of magnitude. Widening anything here would have been arbitrary.

**What *did* change is the input-power allocation, and it is the accepted tradeoff.** At 475 mA typ
input with SYS regulated to 4.5 V, charging 300 mA at ~3.8 V consumes ≈253 mA of the SYS-side
budget, leaving ≈222 mA (≈1.0 W) for the system before DPPM/supplement engages — against ≈348 mA
(≈1.57 W) at the old 150 mA. USB-only operation therefore has less headroom before the battery
starts supplementing. That is exactly the "preserve *some* system-current headroom" position the
decision took, and it needs no layout change.

> **The real consequence is thermal, not conductor width, and it lands on U11.** The BQ25185 is a
> **linear** charger with a power path: it regulates SYS to 4.5 V by dropping VIN, then drops
> SYS→BAT across the BATFET. Worst-case device dissipation:
>
> * IN→SYS path: (5.0 − 4.5) × 0.475 = **0.238 W**
> * BATFET at fast-charge onset with a depleted 3.0 V pack: (4.5 − 3.0) × 0.300 = **0.450 W**
> * **Total ≈ 0.69 W**, against ≈0.46 W at the old 150 mA — a **+50 %** increase, in a
>   DLH0010A **2.2 × 2.0 mm** WSON-10.
>
> `TREG` = 100 °C folds charge current back rather than failing, so this is a charge-**time** risk,
> not a hazard, and it is transient — dissipation falls to ≈0.39 W once the pack reaches 4.0 V.
> But it means **U11's exposed-pad thermal vias are now required for the 300 mA target to be
> sustained, not optional.** The thermal-via plan is revised from 1 to **2 THERMAL-class vias**
> (0.25 mm drill / 0.55 mm pad) on U11's 0.9 × 1.5 mm exposed pad — two fit along the 1.5 mm axis at
> 0.75 mm pitch with a 0.20 mm pad gap. **Implementation stays deferred to the routing/thermal pass;
> this is guidance for that pass, not a routing blocker.**

### 3. USB differential net names normalised

| Old | New | Segment |
|---|---|---|
| `/01_POWER_TREE/USB_D_P_CONN` | **`/01_POWER_TREE/USB_D_CONN_P`** | J3 ↔ U10 (connector side of the ESD array) |
| `/01_POWER_TREE/USB_D_N_CONN` | **`/01_POWER_TREE/USB_D_CONN_N`** | " |
| `/01_POWER_TREE/USB_D_P_ESD` | **`/01_POWER_TREE/USB_D_ESD_P`** | U10 ↔ R33/R34 (22 R series) |
| `/01_POWER_TREE/USB_D_N_ESD` | **`/01_POWER_TREE/USB_D_ESD_N`** | " |
| `/USB_D_P_MCU` | **`/USB_D_MCU_P`** | R33/R34 ↔ U1 (+ C21/C22 DNP) |
| `/USB_D_N_MCU` | **`/USB_D_MCU_N`** | " |

**Scope note, stated explicitly.** The instruction named only the MCU pair, but *"use one naming
convention consistently"* and the goal of actually closing the blocker both point at all three
segments. `USB_D_P_CONN` and `USB_D_P_ESD` had the identical mid-name defect, and the CONN segment
(J3 → U10, ~10 mm) and ESD segment (U10 → the series resistors) are physically routed as
differential pairs too. Renaming only the MCU pair would have left two thirds of the pair
un-pairable by the router. All six were renamed to the same `_P`/`_N` suffix convention.

38 renames total: 12 in `01_power_tree.kicad_sch`, 2 in `02_mcu_core.kicad_sch` (hierarchical
labels), 8 in `aqroot-Beta.kicad_sch` (root labels + sheet pins), 16 pad-net references in
`aqroot-Beta.kicad_pcb`. Six `netclass_patterns` in `aqroot-Beta.kicad_pro` were retargeted.
**Nothing but names changed** — no pin, no series component, no ESD part, no J3, no MCU assignment,
no architecture.

### 4. Differential-pair detection — verified functionally, three ways

Checked on a throwaway board copy with two temporary probe rules and four injected tracks
(discarded afterwards — the committed rule set is unchanged).

1. **`A.inDiffPair('/USB_D_MCU')` matched both tracks.** KiCad resolves the base name and pairs the
   `_P`/`_N` members. This is the check that failed before the rename.
2. **`AB.isCoupledDiffPair()` fired on all three segments** — `USB_D_MCU_P/N`, `USB_D_CONN_P/N` and
   `USB_D_ESD_P/N` — confirming every segment is recognised, not just the MCU pair. It also fired on
   the pre-existing, already-correctly-named `SPK_P`/`SPK_N`, which is a useful control that the
   probe itself works.
3. **The real `USB_DIFF` geometry rule binds and discriminates.** A pair injected at the correct
   **0.20 mm** gap produced **no** violation; a pair injected at **0.50 mm** produced
   `diff_pair_gap_out_of_range` quoting *"USB 2.0 differential pair geometry (90 Ω on F.Cu over In1)
   maximum gap 0.2400 mm; actual 0.5000 mm"*. Before the rename this constraint could not fire at
   all, because KiCad never identified a pair to measure.

**Geometry unchanged, as instructed:** W **0.30 mm**, gap **0.20 mm**, ~**90 Ω** differential
(89.3 Ω computed) on F.Cu over the continuous In1 GND plane, `JLC04161H-7628`, 4 layer, 1.6 mm. The
rule bound on the first attempt, so nothing needed adjusting.

### 5. Verification

* **Connectivity: identical.** 174 nets before and after. Applying the expected six-name map to the
  HEAD netlist reproduces the new netlist **exactly** — zero nets added, zero removed, **zero
  membership changes**. The chain is intact and traceable: `J3.A6/B6 → U10.3` ▸ `U10.4 → R34.1` ▸
  `R34.2 → U1.14` (+`C22.1`), and the N side mirrors it through `U10.1`, `R33`, `U1.13`, `C21`.
* **ERC: 116 reported / 58 excluded / 58 live**, and **zero delta** against the pre-rules baseline
  under an identical `--severity-all` invocation. Live set is 23 `isolated_pin_label`, 22
  `pin_to_pin`, 8 `unconnected_wire_endpoint` (all warnings) and the 5 pre-existing
  `label_dangling` errors. **Exclusion reconciliation: all 58 stored `erc_exclusions` still bind and
  none references a USB net name, so nothing went stale.** `drc_exclusions` remains **0** — no DRC
  finding is being hidden anywhere in this project.
* **PCB DRC: 0 errors**, 231 warnings (132 `silk_over_copper`, 95 `silk_overlap`, 3
  `silk_edge_clearance`, 1 `text_height`) — identical in composition to the previous pass. The
  fine-pitch rules remain effective (no `clearance` error returned) and the RF **E4/E5 rules are
  byte-unchanged**: `aqroot-Beta.kicad_dru` was not edited in this pass.
* **Schematic ↔ PCB parity: 259, all `warning`, count unchanged.** 187 empty-`Description` field
  mismatches and 72 library-prefix artifacts. The R37 value edit added none because both sides were
  updated together.
* **Placement: 187 footprints, zero changes** to position, rotation, side or footprint ID. C55
  remains at **(22.225, 29.400) rot 270, `C_0603_1608Metric`**. The board still has **0 tracks and
  0 vias**.

### 6. Routing blocker ledger

**`BLOCKS_ROUTING`: NONE.**

Both prior items are closed: the ISET charging policy is decided and implemented, and the USB pair
is renamed with differential-pair binding demonstrated rather than assumed.

**`BLOCKS_FAB` (unchanged in kind, one added):**

1. **NEW — battery cell/pack must permit ≥300 mA charge** (0.15 C at 2000 mAh). Cell standard and
   maximum charge current, the pack protection circuit's own charge rating, and the charge
   temperature window. See [[06 - BOM and Cost Tracker]].
2. Panel ceiling re-derivation — 0.80 mm reads as a nominal applied as a maximum; U9 is 1.00 mm max
   by datasheet and standard 0603 X7R is 0.90 mm max.
3. C55 exact low-profile MPN — 2.2 µF / 16 V / X7R / 0603 with documented max height and a DC-bias
   curve showing ≥1.2 µF at 5.0 V.
4. Samtec J5 body depth **B**.
5. Samtec J5 finished-hole requirement.
6. Final JLCPCB impedance confirmation at order, and **FR-4 TG155** selected rather than the
   4-layer default TG135–140.
7. J2 microSD shell edge clearance 0.20 mm — at the fab floor, confirm with JLCPCB.
8. Thermal-via implementation and vendor-guidance review (U9, U12, U5, U14 marked VERIFY; **U11
   revised to 2 vias and now load-bearing for the 300 mA charge target**).

None of these is promoted to a routing blocker. Each is a fabrication, BOM or thermal-implementation
item that routing can proceed alongside — the thermal vias in particular are *placed during* routing,
which is why the plan belongs to that pass rather than blocking its start.

### Files changed

`01_power_tree.kicad_sch` (R37 value, 12 USB label renames) · `02_mcu_core.kicad_sch` (2
hierarchical labels) · `aqroot-Beta.kicad_sch` (8 root labels + sheet pins) ·
`aqroot-Beta.kicad_pcb` (16 pad-net references, R37 value field) · `aqroot-Beta.kicad_pro` (6
netclass patterns) · `06 - BOM and Cost Tracker.md` (charge-rate VERIFY).
**`aqroot-Beta.kicad_dru` deliberately untouched.**

**ROUTING NOT STARTED. No signal trace was drawn in this pass.**


---

## ROUTING PASS 1 — PARTIAL: GND reference + EP thermal infrastructure committed, rails BLOCKED (2026-08-11)

**Routing Pass 1 did NOT complete its stated scope.** Blocks A and B (thermal/exposed-pad
infrastructure and the primary GND reference) are routed and DRC-clean. Blocks C–F (converters,
major power rails, USB, E4/E5 crossings, critical decoupling loops) were routed, produced **41 DRC
errors**, and were **reverted rather than committed**, because they cannot be made legal against
the current rail-width floors. The cause is diagnosed below and needs one CTO decision.

Nothing broken was committed. Placement, connectivity and ERC are untouched.

### Push status

Working tree was clean at three commits ahead. `acdff55..e6220da` pushed to `origin/master`; no
commit was created for the push. Branch in sync before routing began.

### What IS routed and verified

| | |
|---|---|
| Stackup | JLCPCB `JLC04161H-7628`, 4 layer, 1.6 mm, 1 oz outer / 0.5 oz inner |
| Tracks added | **3** (F.Cu, GND only) |
| Vias added | **18** — 16 THERMAL 0.25/0.55, 1 POWER 0.40/0.80, 1 GENERAL_SIGNAL 0.30/0.60 |
| Nets carrying copper | **GND only** |
| In1 GND zone | outline 11181.0 mm², **filled 10025.8 mm²** |
| DRC | **0 errors**, 233 warnings (231 silkscreen + 1 dangling track + 1 dangling via) |

### In1 GND reference — created, and it is NOT continuous

The `In1 GND REFERENCE` zone is a single pour inset 0.6 mm from the board edge. **1155.2 mm² of it
is missing**, and that is worth stating plainly because the ruling asked for a continuous plane:

| Void | Area | Authority |
|---|---|---|
| `WROOM ANTENNA KEEPOUT` X0–6 Y17–35 | ~108 mm² | Espressif — **required**, and the ruling names it |
| `NFC RESERVED` X28–54 Y15–35 | ~520 mm² | NFC loop antenna — **required**; a loop over a plane is shorted |
| `HEADER RESERVED` X18.5–55.5 Y0–8.5 | ~315 mm² | J5 dock reservation from the placement passes |
| pad/via clearance cutouts | ~212 mm² | normal |

Two of the three are electrically necessary. **`HEADER RESERVED` is the one worth questioning** — it
is a 37 × 8.5 mm hole in the reference plane at the top edge, and unlike the antenna keepouts there
is no manufacturer requirement behind it. It was not changed (it predates this pass and §2 says
preserve authoritative exceptions), but any net routed across Y0–8.5 in that X range will lose its
reference. **Flagged for the CTO.**

### Exposed-pad thermal vias — 16 vias, all vendor-geometry-derived

TI `SLUSF65A` §8.4.1 verbatim: *"A solid ground plane tied to the GND pin and thermal pad should be
used."* **TI specifies a plane tie, not a via count**, so no array was invented — each array is the
maximum the vendor land pattern accepts at the project THERMAL class (0.25 mm drill / 0.55 mm pad)
with ≥0.10 mm land margin.

| Ref | Land | Vias | Note |
|---|---|---|---|
| U11 BQ25185 | 0.90 × 1.50 mm | **2** @ 0.70 mm pitch | the most a 0.90 mm-wide land takes |
| U12 TPS63020 | 2.85 × 1.58 mm | **6** (3 × 2) | 0.90 / 0.70 mm pitch |
| U9 ST25R3916 | 3.45 × 3.45 mm | **6** (2 × 3), west half only | see below |
| U5 MAX98357A | 1.23 × 1.23 mm | **1** centred | 0.55 mm pads will not tile 1.23 mm |
| U14 MAX17048 | 0.80 × 1.38 mm | **1** centred | |

**U1 ESP32-S3-WROOM-1 needed nothing: its footprint already carries 12 integral plated 0.20 mm vias
in pad 41**, present on F.Cu/In1/In2/B.Cu. Module grounding is done by the land pattern.

> **NEW FINDING — U9's exposed pad sits on top of the WROOM pad column.** U9's EP land spans
> X 22.775–26.225; U1's B.Cu pad column (pads 15–30, `TEST_GPIO46`, `NFC_CS_N`, `DISP_CS_N`,
> `SPI_A_MOSI`, `SPI_A_SCK` …) occupies **X 24.500–26.000** directly beneath it. A through via in the
> eastern half of U9's EP would short the NFC reader's ground pad to a WROOM GPIO. Only the western
> strip X 23.15–24.03 is usable, giving **6 vias instead of the 9 a 3.45 mm land would otherwise
> take**, all offset to one side of the pad. U9's thermal and RF grounding is therefore
> **asymmetric and weaker than the land pattern allows**, and it is a *placement stack* consequence,
> not a routing one. Carried as an RF/thermal review item for U9 bring-up.

### KiCad custom-rule precedence is LAST-match-wins — and it is now load-bearing

Established empirically, twice, during this pass, because the first assumption was wrong:

1. Necking rule at the **end** of the file → it beat the section-10 rail clearances.
2. Necking rule moved to the **front** → the section-1 land-pattern rules stopped winning and U13
   immediately reported **four false 0.15 mm pad-pair errors**.

So later rules override earlier ones. `aqroot-Beta.kicad_dru` now ends with an explicit
**PRECEDENCE TAIL** whose comment records the required weakest-first order — RF/rail rules, then
pad-escape necking, then land-pattern rules — and warns that moving either block earlier silently
breaks the one below it. **This ordering is not cosmetic; it is the only reason the fine-pitch
exceptions work.**

### Rule added: pad-escape necking (section in the precedence tail)

Two rules, scoped to six named courtyards — `U11 U12 U13 U14 U17 U9`:

* `track_width (min 0.20mm)`
* `clearance (min 0.20mm)` when **both** items are inside one of those courtyards

Justification: a 1.00 mm `BAT_MAIN` track cannot land on U11's 0.20 mm-tall pad, and SYS and BAT
leaving adjacent pins of a 0.40 mm-pitch WSON cannot hold 0.30 mm from each other. Inside these
courtyards the **vendor pitch governs**; 0.20 mm is still 2.2× the fab floor. Width *and* clearance
fall back only there — outside the courtyard the full rail width and elevated routed clearances
apply unchanged. **RF E4/E5 rules were not touched: `git diff` confirms no edit inside sections 4–9.**

### Why blocks C–F were reverted — one decision unblocks them

The routing was built and measured. It produced 41 errors that reduce to **one root cause**:

> **`BAT_MAIN` min 1.00 mm and `SYS_MAIN` min 0.60 mm cannot be honoured on the copper that
> actually exists around U11, and the widths were derived from the wrong current.**

* `BAT_MAIN`'s 1.00/1.50 mm floor came from **`IBAT_OCP` = 3.125 A** — which is a *fault trip
  threshold*, not a design current. Sizing a rail for the OCP point is what makes the geometry
  infeasible. The realistic sustained battery current is **~1.0–1.5 A** (system load in supplement
  mode). At 1.5 A on 1 oz outer copper, IPC-2221B needs **0.525 mm** at ΔT = 10 K — half the
  present floor.
* On **In2 at 0.5 oz**, 1.5 A needs **2.73 mm** at ΔT = 10 K. A 0.60 mm In2 rail would run ~120 K
  hot. So BAT and SYS genuinely **cannot** distribute on In2, and the attempt to do so was wrong —
  the rule system correctly rejected it. They must stay on the outer layers.
* But U11's **west flank is a 0.40 mm-pitch WSON**: SYS (pin 1), BAT (pin 2), STAT2 (pin 3) and two
  GND pins all exit within 1.6 mm of each other. Two rails at 1.00 mm + 0.60 mm + 0.30 mm clearance
  need 1.9 mm of width that is not there, and the free F.Cu corridor west of x = 62.5 can only be
  reached through ~1.1 mm of necked escape.

**Decision needed before Pass 1 can be re-run (this is a rules change, and §0 makes the rules
authoritative, so it is not mine to make):**

| Netclass | Present floor | Proposed | Basis |
|---|---|---|---|
| `BAT_MAIN` | min 1.00 / opt 1.50 mm | **min 0.60 / opt 1.00 mm** | 1.5 A sustained on 1 oz outer, ΔT = 10 K → 0.525 mm |
| `SYS_MAIN` | min 0.60 / opt 1.00 mm | **min 0.50 / opt 0.80 mm** | 1.0 A on 1 oz outer, ΔT = 10 K → 0.300 mm |

Both proposals still carry ≥2× the IPC-2221B thermal minimum. Keeping the present floors is also a
valid answer — it would mean accepting that BAT and SYS route as short wide F.Cu spurs only, with
U11's charge path deliberately necked, and TI's *"high-current charge paths … must be sized
appropriately"* satisfied by length rather than width.

### Also measured while the reverted routing was in place

Recorded because it is real data and will not need re-deriving next pass:

| Item | Result |
|---|---|
| U12 L1 buck switch node | **2.70 mm** of 0.50 mm copper |
| U12 L2 boost switch node | **6.89 mm** — L1's west pad faces U12's *north* pin row and its east pad faces the *south* row, so the boost node must route **around the inductor**. Placement consequence; flagged. |
| U13 SW | **3.70 mm** |
| U17 BL_SW | **4.55 mm** |
| C43 → L3 | **2.37 mm** — the loop-critical hop, and it is good |
| U17 VIN ← C43 | **9.39 mm** — *not* loop-critical: on the TPS61169 the VIN pin is an internal-bias input, and the power path is rail → L3 → SW. **But there is no local bias cap at U17 pin 5**; C43 serves both roles at 9.39 mm. Review item — adding one is a schematic change and was not done. |
| C55 → U9 pin 10 | routable at 0.35 mm through the **0.95 mm** gap between C50 and C52, necking to 0.25 mm for the final 0.5 mm-pitch approach — which is why U9 was added to the necking set |

### Preservation

* **Placement: 187 footprints, zero changes.** No component moved.
* **Schematic connectivity: untouched** — no schematic file was modified in this pass.
* **ERC: 116 / 58 excluded / 58 live, zero delta** against the established baseline.
* **RF E4/E5 rules: unchanged** — no edit inside DRU sections 4–9; only the precedence tail and the
  two necking rules were added.
* **No `NFC_DEFERRED` net was routed.** The only net carrying copper anywhere on this board is
  **GND**.
* Board still has **0 signal traces**.

### Status

**ROUTING PASS 1: FAIL** (scope incomplete — blocks C–F not delivered)
**POWER / USB / CROSSING INFRASTRUCTURE LOCK: NO**
**READY FOR DIGITAL ROUTING PASS: NO**
**FULL ROUTING COMPLETE: NO**

Next pass, once the width decision is made: re-run blocks C–F from
`scratchpad/pass1b.py`, which is already written and whose geometry is validated against pads —
what it fails is only the width/clearance floors above.


---

## ROUTING PASS 1 BLOCKER CORRECTION — all three blockers CLOSED (2026-08-11)

Width lock applied, the HEADER RESERVED In1 void removed, U9's exposed-pad grounding audited
against ST's own layout application note, and one capacitor added on TI's explicit instruction.
**No routing was performed. GND remains the only net carrying copper.**

### 1–3. BAT / SYS width lock and layer policy

| Netclass | Before | **After** | Basis |
|---|---|---|---|
| `BAT_MAIN` | min 1.00 / opt 1.50 mm | **min 0.60 / opt 1.00 mm** | 1.5 A sustained, 1 oz outer, ΔT = 10 K → 0.525 mm |
| `SYS_MAIN` | min 0.60 / opt 1.00 mm | **min 0.50 / opt 0.80 mm** | 1.0 A, 1 oz outer, ΔT = 10 K → 0.300 mm |

Netclass default track widths follow: `BAT_MAIN` 1.50 → **1.00 mm**, `SYS_MAIN` 1.00 → **0.80 mm**.
Both floors remain ≥1.6× the IPC-2221B thermal minimum.

The section-10 derivation comment was corrected in place, because the wrong number is the thing
that has to stop propagating:

> `IBAT_OCP` = 3.125 A is a **FAULT TRIP THRESHOLD, not a routing design current.** The earlier
> 1.00/1.50 mm floor was derived from it and made U11's 0.40 mm-pitch west flank unroutable.

**Layer policy, now written into the rule file rather than left as intent:** both rails are
**outer-layer by policy**. `BAT_MAIN` must not distribute on In2 — at 0.5 oz, 1.5 A needs
**2.73 mm**, which defeats the point of using In2. `SYS_MAIN` is outer-layer by preference; if an
In2 segment ever proves unavoidable it must be sized separately from the actual SYS current at
0.5 oz. **Never inherit an outer-layer width onto inner copper.**

**Necking rule confirmed unchanged** — `min 0.20 mm` on width *and* clearance, scoped to exactly six
named courtyards (`U11 U12 U13 U14 U17 U9`), still sitting in the **PRECEDENCE TAIL** where
last-match-wins puts it above the rail clearances and below the land-pattern rules. `git diff`
confirms **zero RF/E4/E5 rule lines touched**: the only DRU edits are the two width constraints and
their comment block.

### 4. HEADER RESERVED — In1 removed, and the audit found a bonus

Audited what is actually inside X18.5–55.5 / Y0–8.5: **only J5**, and only its 26 through-hole pads
— all present on In1, **five of them GND** (pads 2, 7, 13, 20, 25). No manufacturer requirement for
an In1 void exists; J5 is a THT right-angle header whose pads get normal antipads automatically.
The keepout was an outer-layer dock reservation that had been applied to all four layers.

`HEADER RESERVED` layer set **F.Cu + In1 + In2 + B.Cu → F.Cu + In2 + B.Cu**. The dock still
restricts the three layers where it matters mechanically.

| | |
|---|---|
| In1 filled **before** | 10025.8 mm² |
| In1 filled **after** | **10237.0 mm²** |
| Gain | **+211.3 mm² (+2.11 %)** — now 91.56 % of the 11181.0 mm² outline |
| New DRC issues | **none**, 0 errors |

The gain is 211 mm² rather than the ~315 mm² of raw rectangle because J5's 26 THT antipads
legitimately consume the difference. **Plane continuity improves in two ways:** the 37 × 8.5 mm slot
in the reference plane is gone, *and* J5's five GND pins now tie directly to the In1 pour instead of
being isolated from it — which is what a dock connector's return path needs.

ST corroborates the direction of this fix. AN5240 Rev 5 §4.2: *"Reducing the ground impedance can be
done by using solid ground planes or ground grids, and by avoiding slots in the ground plane"*, with
Figure 9 titled *"Avoiding slots in the GND plane"*. **J5 was not moved.**

The other two In1 voids stay: `WROOM ANTENNA KEEPOUT` (Espressif) and `NFC RESERVED` (an NFC loop
over a ground plane is shorted out). Both are electrically required.

### 5. U9 / U1 cross-side overlap — exact geometry

| | |
|---|---|
| U9 EP land (pad 33) | **X 22.775–26.225, Y 20.275–23.725** (3.45 × 3.45 mm) |
| U1 WROOM B.Cu pad column | **X 24.500–26.000** |

Four WROOM pads overlap the EP footprint in XY:

| U1 pad | Net | Y span | Overlap with the EP |
|---|---|---|---|
| 16 | `TEST_GPIO46` | 19.835–20.735 | 1.500 × 0.460 mm |
| 17 | **`NFC_CS_N`** | 21.105–22.005 | 1.500 × 0.900 mm |
| 18 | `DISP_CS_N` | 22.375–23.275 | 1.500 × 0.900 mm |
| 19 | `SPI_A_MOSI` | 23.645–24.545 | 1.500 × 0.080 mm |

So **the eastern 1.725 mm — exactly half the EP — has WROOM signal pads beneath it.** With 0.55 mm
THERMAL pads and 0.20 mm clearance to those pads, legal via centres lie only in
**X 23.150–24.025** (a 0.875 mm band). The committed 2 × 3 array sits at X 23.300 / 23.950,
**0.913 mm west of the EP centre**.

### 6. ST guidance — AN5240, and it settles the symmetry question

**Source: ST `AN5240` Rev 5, June 2023**, *"Layout recommendations for the design of boards with the
ST25R3916/16B, 17/17B, 18, 19B, and 20/20B devices"*. Retrieved through the browser — `curl` and
WebFetch both fail against st.com (connection reset / timeout), and the archived DS12484 Rev 3
datasheet contains **no** layout guidance at all (0 hits for "ground plane", 0 for "layout", 0 for
"soldered"; its only "exposed pad" mention is a coplanarity note).

**§8 "Thermal pad", verbatim and complete:**

> *"The thermal pad underneath the ST25R3916 provides both a ground plane and a thermal heat sink.
> This pad is connected to the PCB ground plane by multiple through-vias, and must be plated to have
> good soldering results. The multiple vias keep the total parasitic inductance low in this area."*

What that does and does not say:

* **Dual objective is explicit** — ground plane *and* heat sink.
* **"through-vias"** — ST names through vias specifically, which independently vindicates the
  project's no-microvia / no-blind-via policy.
* **"multiple"** — and **no count and no pattern is given anywhere in the text.** No minimum was
  invented.
* The stated purpose of the multiplicity is *"keep the total parasitic inductance low"* — an
  **inductance** objective, not a symmetry one.
* **ST imposes no symmetry requirement on the thermal pad.** Every one of the seven "symmetr"
  occurrences in AN5240 is about the RF matching network and the RFO1/RFO2 and RFI1/RFI2 differential
  traces (*"Route RFI and RFO signals symmetrically"*, *"the matching components need be placed close
  to each other, and symmetrically"*). Those are all `RF_DEFERRED_NFC` nets and are not routed.
* **ST's own Figure 16 draws a 3 × 3 = 9 via array** evenly spread across pad 33. That is a
  reference implementation, not a stated requirement.

### 7. U9 verdict — six vias are adequate; Option B implemented

Quantified against ST's stated objectives rather than against the figure.

**Inductance (the objective ST actually names).** A 0.25 mm through via in 1.6 mm FR4 is ≈1 nH.
Six in parallel with mutual coupling ≈0.3 nH; nine ≈0.2 nH. At 13.56 MHz that is
**0.026 Ω versus 0.017 Ω — a difference of ~0.01 Ω.** Lateral spreading across the EP's own 1 oz
copper from the east side to the west via column is 1.7 mm at 3.45 mm width: **0.24 mΩ** DC and
≈0.026 Ω at 13.56 MHz.

**Thermal.** Each via ≈185 K/W; six in parallel 30.8 K/W, in parallel with the EP's direct coupling
to In1 through 0.2104 mm of prepreg over 11.9 mm² (58.9 K/W) → **20.3 K/W**. Nine vias give
15.3 K/W. The ST25R3916 datasheet gives `Pt` = **300 mW** absolute maximum total dissipation, so
EP-to-plane rise is **6.1 K with six vias versus 4.6 K with nine — a difference of 1.5 K** at the
device's absolute max.

**Verdict: six legal EP vias are adequate for Beta.** The asymmetry costs ~0.03 Ω of ground
impedance at the NFC carrier and ~1.5 K at absolute-max dissipation. ST's text is satisfied
("multiple through-vias"), ST's symmetry language does not apply to this pad, and no minimum count
was invented.

**Option B was implemented anyway, because it is nearly free and removes the lateral-spreading term
for the pins that were worst served.** U9's GND pins 12, 16, 20 and 21 previously had **no path to
In1 at all**. Added:

| Tie | Stub | Via | Clearance to the WROOM column |
|---|---|---|---|
| pad 12 (south) | 0.97 mm, 0.25 mm wide | (24.000, 25.560) | 0.20 mm |
| pad 16 (south) | 0.96 mm, 0.25 mm wide | (26.550, 25.560) | 0.25 mm |
| pads 20+21 (east) | 0.50 + 4.04 mm | (27.500, 25.560) | 1.20 mm |

3 GENERAL_SIGNAL vias (0.30/0.60). Every position was asserted against **X 24.500–26.000** in the
build script, so **no through via sits over a WROOM signal pad**. No blind, buried or microvia was
used. The in-pad array is unchanged at 6.

**U9 placement stays HARD-LOCKED.** Option C was not needed and no translation is proposed.

### 8–9. TPS61169 VIN — TI says the capacitor must be close to VIN, so C56 was added

**Source: TI `SNVSA40B`**, *TPS61169 38 V High Current-Boost WLED Driver With PWM Control*,
October 2014, **revised June 2024**.

**§7.5.1 Layout Guidelines, verbatim:**

> *"The input capacitor CIN must be close to VIN pin and GND pin in order to reduce the input ripple
> seen by the device."*

**§7.4 Power Supply Recommendations, verbatim:**

> *"If the input supply is located more than a few inches from the TPS61169 device, additional bulk
> capacitance may be required in addition to the ceramic bypass capacitors."*

Two things follow, and one of them corrects the framing of the question:

1. **TI does not describe a separate small "local VIN bypass" part, and never names 10–100 nF.** The
   datasheet has one input capacitor, `CIN`, with `CI` min **1 µF** in Recommended Operating
   Conditions and 4.7 µF in the typical application. §7.4's *"in addition to the ceramic bypass
   capacitors"* does distinguish local ceramic from remote bulk, but the near part in TI's model is
   `CIN` itself.
2. **AQROOT does not satisfy the §7.5.1 requirement.** C43 (4.7 µF) is the power-stage input
   capacitor and is **9.39 mm** from U17 pin 5 — correct for the C43→L3 loop at 2.37 mm, but not
   "close to VIN pin". **U17 has no local bypass at all.**

**Verdict: a local capacitor at U17 VIN is required, on TI's explicit instruction.** Added as
authorised:

| | |
|---|---|
| Ref | **C56** |
| Value | 100 nF, 16 V, X7R, 0603 |
| BOM class | STANDARD_EIA_PASSIVE, multi-source |
| Net | `+3V3` (pad 1) / `GND` (pad 2) |
| Placement | **(46.100, 82.500) rot 0, B.Cu** |
| C56 pad 1 → U17 pin 5 (VIN) | **1.624 mm** (was 9.39 mm to C43) |
| Routed | **No** — the ruling says place only |

Clear of every exclusion: not in the TOP panel shadow (B.Cu, and Y 82.5 > 78), not in the bottom
battery shadow (Y > 77.5), not in the 915 or 433 band, not in `NFC RESERVED`, and clear of the
BL_SW switch node (x ≥ 44.575 versus U17 pin 1 at x ≤ 42.675) and of the LED_K/R69 FB path.

> **One honest caveat.** The authorised class is 100 nF, and that is what was fitted — it gives U17
> the local HF bypass it currently lacks. But TI's literal requirement is that **`CIN` (≥1 µF)** be
> close to VIN. A **1 µF** part in the same 0603 footprint would satisfy §7.5.1 outright and costs
> nothing extra in area. **Recommended as a one-value BOM change if the CTO wants the datasheet
> requirement met to the letter rather than mitigated.**

### 10. Thermal via status — preserved

U11 **2** · U12 **6** · U9 **6** (now confirmed, no longer provisional) · U5 **1** · U14 **1** · U1
integral module vias unchanged. **No decorative vias were added** — the three new U9 vias are pin
ground ties for pads that had no plane path, not thermal padding.

Totals: **21 vias** (16 THERMAL 0.25, 4 GENERAL_SIGNAL 0.30, 1 POWER 0.40) and **9 tracks**, all GND.

### 11–12. Verification

* **DRC: 0 errors**, 234 warnings (231 silkscreen, +1 `silk_overlap` from C56's own silkscreen,
  1 dangling track, 1 dangling via, 1 text height). 499 unconnected, as expected.
* **ERC: 116 / 58 excluded / 58 live, zero delta** against the established baseline. **C56 introduced
  no ERC item** — both pins land on power symbols.
* **Netlist: 174 nets before and after.** C56 adds no net; the only change is `+3V3` gaining
  `(C56, 1)` and `GND` gaining `(C56, 2)`.
* **Placement: 188 footprints, 187 unchanged plus C56. Zero moved** — verified position, rotation,
  side and footprint ID against HEAD for all 187.
* **E4/E5 and RF layer policy: unchanged.** DRU diff is two width constraints and one comment block.
* Parity 259 → 261, both new items C56 field-mismatch warnings.
* **No `NFC_DEFERRED` net routed. GND is still the only net carrying copper.**

### Status

**BAT/SYS WIDTH BLOCKER: CLOSED**
**U9 EP GROUNDING BLOCKER: CLOSED** — six in-pad vias adequate per AN5240 §8, plus three fanout ties
**TPS61169 VIN DECOUPLING REVIEW: CLOSED** — C56 added on TI SNVSA40B §7.5.1
**READY TO RESUME ROUTING PASS 1: YES**
**ROUTING STARTED IN THIS TASK: NO**

`scratchpad/pass1b.py` can now be re-run: its geometry is already validated against every pad, and
the width floors it failed are the ones just corrected. C56 still needs routing when Pass 1 resumes.


---

## ROUTING PASS 1 (resumed) — converters and power rails routed, USB/E4/E5 NOT (2026-08-11)

The corrected width lock unblocked the converter and power-rail work: **all four converter blocks
and the BAT/SYS/+3V3 rails are now routed and DRC-clean.** USB, the E4 and E5 crossings, the +3V3
band crossing and the C55/U9 supply are **not** routed, so Pass 1 still does not close. Two of those
are blocked by geometry rather than effort, and both are documented below.

**0 DRC errors. Placement unchanged. `aqroot-Beta.kicad_dru` not touched in this pass.**

### Totals

| | |
|---|---|
| Tracks | **83** (F.Cu 64, B.Cu 17, In2 2) |
| Vias | **29** — 16 THERMAL 0.25, 10 POWER 0.40, 3 GENERAL_SIGNAL 0.30 |
| Nets carrying copper | **15** |
| **Fully routed** | **9** — `ILIM_VSET`, `R_FB_TOP`, `BL_SW`, `LED_BOOST`, **`BAT_PROTECTED_P`**, `L1-Pad1`, `L1-Pad2`, `U11-TS_MR`, `U13-SW` |
| **Partially routed** | **6** — `BQ25185_SYS` (2 left), `+3V3` (68), `USB_VBUS_CHG` (1), `NFC_5V_PA_PENDING` (6), `LED_K` (1), `GND` (178) |
| Not started | 159 nets |
| Unconnected items | 486 (from 499) |

Two items removed: the pass-1A U12 pin-2 GND escape and its plane via. U12 pin 2 now ties **directly
to PGND_EP**, which already carries 6 vias to In1 — a shorter, lower-inductance return, and it
cleared the board's only dangling via.

### Per-block results

**U11 BQ25185.** SYS pin 1 and BAT pin 2 escape west at 0.20 mm through the 0.40 mm-pitch WSON, then
flare on the next segment — SYS to 0.60 mm into the F.Cu trunk, BAT to 0.60 mm into a via. VBUS pin 10
escapes at 0.30 mm and reaches C23 through In2, because the C36/C23 corridor is only 0.75 mm wide and
no compliant VBUS track crosses it on F.Cu. `ILIM_VSET` → R36 and `TS_MR` → R38 complete.

> **ISET DEFERRED — a genuine crossing conflict.** U11 pin 8 (ISET) is *north* of pin 7 (ILIM_VSET),
> but R37 is *south* of R36, so the two programming nets must cross. Every via position that takes
> the crossing to another layer lands within 0.25 mm of the VBUS_CHG via, the VBUS escape, or the
> TS/MR run — the corner east of U11 is fully committed. One 1 kΩ programming net, carried to the
> cleanup pass rather than forced through at reduced clearance.

**U12 TPS63020.** Both switch nodes minimal and local: **buck 2.70 mm / 1.35 mm²**, **boost
6.89 mm / 3.44 mm²**. The boost node is 2.5× the buck node because L1's west pad faces U12's *north*
pin row and its east pad faces the *south* row, so the boost node must route **around the inductor** —
a placement consequence, flagged again. VIN loop pins 10/11 → C26 → C27; VINA pin 1 to the trunk;
VOUT pins 4/5 → In2 hop past the FB divider row → the C29/C30/C31/C32 F.Cu spine. FB pin 3 → R39 →
R40 routed clear of every switch node.

**U13 TPS61023.** VIN escape → SYS trunk. SW **2.87 mm / 0.98 mm²**, kept local. VOUT leaves north
to C34 and on to C35. The SYS feed to L2 approaches **from the south at y = 34.5** rather than across
y = 29.45, which is what frees the northern lane for the output path. **FB divider (R44/R45)
deferred** — not in the section-6 scope, and its only path crosses the SYS feed at U13's pin column.

**U17 TPS61169 + C56.** C43 → L3 input loop **2.37 mm** (loop-critical, good). BL_SW **4.55 mm /
2.27 mm²**. D8 → C44 → the R70–R73 ballast rail, routed around R70's LED_A1 pad. LED_K → R69 RSET.
**C56 1 µF local CIN is routed to U17 pin 5 in 1.62 mm** at 0.40 mm — the TI SNVSA40B §7.5.1
requirement is now met physically, not just on paper.

**BAT / SYS rails.** Both outer-layer, as locked.

| Rail | Layer | Length | Widths |
|---|---|---|---|
| `BQ25185_SYS` | **F.Cu** trunk x = 61.2 | **81.04 mm** | 0.20/0.25 escapes, 0.50–0.80 mm rail |
| `BAT_PROTECTED_P` | **B.Cu** trunk x = 62.2 | **36.24 mm** | 0.20 escape, **0.60 mm** throughout |

> **Why BAT is on B.Cu.** C24 (SYS), C25 (BAT) and C33 (SYS) interleave in one x-column, so the two
> rails must cross. BAT may not use In2 — 1.5 A at 0.5 oz needs 2.73 mm — so the crossing is taken
> **between two outer layers**, which is the only arrangement that keeps both rails at class width.
> The trunk also steps west around the committed U11 GND plane-tie via at (62.6, 67.8).
> BAT reaches C25, C36, U14 pins 2/3 and TP15; **`BAT_PROTECTED_P` is fully routed.**

**In1 GND plane: 10224.4 mm² of an 11181.0 mm² outline — 91.44 %.** The HEADER RESERVED slot stays
removed; the only voids are the WROOM antenna keepout and the NFC loop region, both required. The
fill dropped 12.6 mm² from the 10237.0 mm² of the previous commit, which is exactly the antipad
area of the 11 new vias — expected, not a policy change.

**U9 grounding: unchanged and verified.** 6 in-pad EP vias + 3 fanout vias. **No via lies within
0.4 mm of the WROOM pad column** (checked programmatically over the whole board, not just U9).

### What is NOT routed, and why

| Item | Status | Reason |
|---|---|---|
| **USB** J3→U10→R33/R34→U1 | **not started** | complex four-pad interleave at J3 (D+ at x 34.75/35.75 with D− at 34.25/35.25 between them) plus a ~150 mm route to U1; needs its own pass |
| **E4** In2 crossing | **not started** | depends on USB |
| **E5 C-W / C-E** crossings | **not started** | ran out of pass |
| **+3V3 band crossing** | **not started** | ran out of pass |
| **C55 → U9 supply** | **BLOCKED — see below** | |
| GND stitching beyond EP/pin ties | deferred | §16 says no decorative fence; the return-critical ties are in |

> **C55 → U9 is blocked at class width, and it is the same constraint that limited C55's placement.**
> `NFC_5V_PA_PENDING` has a 0.35 mm netclass minimum and a 0.25 mm routed clearance. The only paths
> from C55 to U9 pins 8/10 pass the C50/C52 row:
> * west of C50 pad 2: the C50 pad1↔pad2 gap is **0.65 mm**, which fits 0.35 mm of track with only
>   0.15 mm each side — 0.25 mm is required;
> * east through the C50/C52 gap (**0.95 mm**): a 0.35 mm track fits, but it then collides with the
>   new U9 GND fanout via at (24.000, 25.560) — the remaining corridor is **0.475 mm** against the
>   0.85 mm that 0.35 mm of track plus two 0.25 mm gaps needs;
> * B.Cu underneath: every candidate via position between C55 and U9 overlaps C50 pad 2 or C55's own
>   pad.
>
> **Three ways out, and the choice is the CTO's:** move C50/C52 (they are the parts holding the
> near-U9 space, exactly as flagged when C55 was placed); accept a documented width exception for
> this one tap; or accept that C55 serves U9 through the In1 plane and a longer path. **No exception
> was taken and nothing was moved.**

### Preservation

* **Placement: 188 footprints, zero moved**, verified against HEAD for position, rotation, side and
  footprint ID.
* **ERC: 116 / 58 excluded / 58 live, zero delta.**
* **DRC: 0 errors**, 233 warnings (231 silkscreen, 1 dangling track, 1 text height). Parity 261.
* **RF rules untouched** — `aqroot-Beta.kicad_dru` is not in this commit's diff. No copper exists on
  any RF-band layer restriction: **no deferred RF or NFC net carries copper**, and In2 holds only two
  short segments (the +3V3 hop at y 54.4–56.9 and the VBUS hop at y 64.6–65.6), both well outside
  Y 88–114 and Y 115–138.
* **No via inside either antenna band.**

### Views

`floorplan-views/Z_pass1_all_copper.svg`, `Z_pass1_in1_gnd_plane.svg`, `Z_pass1_fcu_power.svg`,
`Z_pass1_bcu_power.svg`.

### Status

**ROUTING PASS 1: FAIL** — converters and rails done, USB / E4 / E5 / +3V3 crossing / C55-U9 not
**POWER / USB / CROSSING INFRASTRUCTURE LOCK: NO**
**READY FOR DIGITAL ROUTING PASS: NO**
**FULL ROUTING COMPLETE: NO**

Next pass needs: the C55/U9 decision above, then USB + E4 + E5 + the +3V3 band crossing, then GND
stitching. `scratchpad/pass1final.py` holds the working geometry for everything already routed.


---

## ROUTING PASS 1B — C55 closed without an exception, E5 corridors and crossings built; USB still open (2026-08-11)

**0 DRC errors. Placement unchanged. No new custom rule was needed.** USB remains the one block not
started, so Pass 1 still does not close.

Starting HEAD `4580f04`, pushed `e6220da..4580f04` to `origin/master` before starting; no commit was
made for the push.

### The authorised C55 width exception turned out to be unnecessary

**No rule was added.** Two measurements closed it:

* The **C50 pad 2 → C52 pad 1 gap is 0.950 mm**. A full-width 0.35 mm `NFC_5V_PA_PENDING` track
  centred at x = 23.700 leaves **0.300 mm each side** — above the 0.25 mm routed clearance. The
  capacitors were never the obstruction.
* The real blocker last pass was **my own U9 pad-12 GND fanout via at (24.000, 25.560)**, added in the
  previous commit. It is relocated: pads 12 and 16 now share the (26.550, 25.560) plane tie through a
  common rail south of U9, so the same three GND pins stay tied and the lane opens.

The only sub-0.35 mm segments are the two 0.30 mm final approaches, both **inside U9's courtyard**,
already covered by the existing pad-escape necking rule. So the escape is 0.30 mm, not the 0.20 mm
authorised, and it is scoped by a rule that already existed.

| | |
|---|---|
| Neck width | **0.30 mm** (the authorised 0.20 mm was not needed) |
| Neck length | 1.00 mm to pin 10, 1.65 mm to pin 8; both wholly inside U9's courtyard |
| Minimum clearance | **0.300 mm** to C50 pad 2 and C52 pad 1; 0.20 mm to U9 pins 9/11 |
| Layer | F.Cu throughout — no via, no layer change |
| **C55 pad1 → U9 pin 10** | **5.92 mm routed** (4.469 mm straight-line) |
| **C55 pad1 → U9 pin 8** | **7.47 mm routed** (4.875 mm straight-line) |

The 1.5–2.6 mm overhead is the detour around C50/C52. C19 untouched.

### Other nets closed

| Net | Result |
|---|---|
| **ISET** | **7.50 mm, 2 vias** (0.25/0.50). Pin 8 → F.Cu east → In2 beneath the ILIM run → R37. TS/MR re-laid 0.2 mm west to clear the via. **Now fully routed.** |
| **U13 FB** | **8.49 mm, 2 vias.** Takes its crossing of the SYS escape on In2, sandwiched under In1 GND — quieter than any F.Cu detour. **Minimum SW↔FB separation 1.59 mm**, and the two are on different layers with In1 between them. |
| **BQ25185_SYS** | 81.04 mm, **2 ratsnest items left** — both to SW9, the hard-off switch, whose EN partner is deferred. Left as a pair. |

### Corridors and crossings

| Structure | Length | Notes |
|---|---|---|
| **E5 C-W** (X 8–20) | **280 mm** over 5 nets | `SD_CS_N`, `SPI_A_SCK/MOSI/MISO`, `BTN_HOME_N` at x 9.0–13.8, 1.2 mm pitch, In2, y 85→141 — crosses **both** bands |
| **E5 C-E** (X 58–70) | **320 mm** over 10 nets | `SPI_B_*`, `SX1262_*` ×5, `CC1101_*` ×2 at x 59–68, 1.0 mm pitch, In2, y 85→117 |
| **+3V3 crossing** | **30 mm** In2 at 0.60 mm | y 86→116, enclosed by C-E; vias at (69.100, 86.000) and (69.100, 116.000); B.Cu continues south to y 141 |
| **E4 VBUS** | **34 mm** | In2 at 0.50 mm, y 86→116, enclosed by `E4 VBUS LANE`; vias at (56.000, 116.000) and (56.000, 86.000) |

**+3V3 drop:** 0.60 mm on 0.5 oz In2, 30 mm in-band → 50 squares × 0.991 mΩ = **49.6 mΩ**; at the
derived 235 mA that is **11.6 mV**, and 15.1 mV at the 305 mA design figure.

> **A rule mechanic worth recording.** `enclosedByArea` can never be satisfied by a track that
> *enters or leaves* a corridor — the end cap always pokes past the boundary. So a corridor crossing
> must hand off by **via inside the corridor margin**, which is exactly what §10's "layer transitions
> outside Y88–114" asks for. All four crossing structures are built that way, and every E5 segment is
> pulled 1 mm inside its corridor ends for the same reason.

### USB — still not started, and the blocker is now precisely located

**C20 sits directly between J3 and U10.** Its pads occupy x 33.550–34.550 and 35.450–36.450 at
y 144.075–145.525, leaving a **0.9 mm gap** between them. A 0.30/0.20/0.30 pair needs **1.20 mm**
with clearance, so the pair cannot pass between C20's pads. Going around: the western corridor
(R30 pad 2 → C20 pad 1) is **1.325 mm** and does fit; the eastern one is **0.925 mm** and does not.
Combined with J3's four interleaved pads (D+ at 34.75/35.75 with D− at 34.25/35.25 *between* them,
0.5 mm pitch, needing a via-based merge that 0.60 mm via pads cannot host without fanning out first),
USB needs a dedicated pass. **No J3 escape rule was added, because none was used.**

Also deferred: VBUS's two hand-off runs from the E4 vias to R35 and to the committed C23 hop — SW7
pad 1 sits directly at the corridor mouth (x ~55.2–56.8, y ~115.6–116.9), so the south hand-off has
no room until USB routing settles that area.

### Totals and audit

| | |
|---|---|
| Tracks / vias | **118** (F.Cu 79, In2 21, B.Cu 18) / **37** (20×0.25, 15×0.40, 2×0.30) |
| Nets carrying copper | **32** |
| Fully routed | **10** — ILIM_VSET, **ISET**, R_FB_TOP, BL_SW, LED_BOOST, BAT_PROTECTED_P, both L1 nodes, **TS_MR**, U13_SW |
| Partially routed | 22 |
| Unconnected items | 499 (each reserved E5 segment adds ratsnest until its ends are routed) |
| **In1 GND** | **10214.5 / 11181.0 mm² = 91.36 %** |
| **Vias inside an RF band** | **NONE** |
| **B.Cu tracks in the 915 band** | **0** — pristine |
| Deferred RF / NFC nets with copper | **NONE** |

**DRC 0 errors**, 256 warnings (132 silk-over-copper, 96 silk-overlap, **20 dangling tracks + 4
dangling vias — the reserved E5 crossing segments and corridor hand-off vias**, 3 silk-edge, 1 text).
**ERC 116 / 58 excluded / 58 live, zero delta.** **Placement 188 footprints, zero moved.** Schematic
untouched. `aqroot-Beta.kicad_dru` untouched.

### Status

**ROUTING PASS 1: FAIL** — USB not started; VBUS and SYS have hand-offs open
**POWER / USB / CROSSING INFRASTRUCTURE LOCK: NO**
**READY FOR DIGITAL ROUTING PASS: NO**
**FULL ROUTING COMPLETE: NO**


---

## C20 moved 0.300 mm NORTH, not east — and a correction to the previous pass (2026-08-11)

The authorised C20 move was **+2 mm east**. That is impossible, it was aimed at the wrong problem, and
one of the numbers I reported last pass was wrong. All three are set out below. C20 moved **0.300 mm
north**, which is what actually opens the J3 escape. **USB is still not routed.**

### C20 function — verified from the netlist, not inferred

| | |
|---|---|
| Value | **4.7 µF 10 V X7R** |
| Footprint | `Capacitor_SMD:C_0805_2012Metric` |
| Nets | pad 1 `/01_POWER_TREE/USB_VBUS_RAW`, pad 2 `GND` |
| Function | **USB VBUS bulk / bypass at the USB-C connector** |
| Serves | J3 pads A4, A9, B4, B9 (VBUS); U10 pin 5 (USBLC6-2SC6 VBUS clamp); R35 pin 1 (VBUS_RAW → VBUS_CHG) |

### Correction to the previous pass

I reported the bypass corridors as **"west 1.325 mm (fits), east 0.925 mm (does not)"**. The east
corridor is **also 1.325 mm** (C20 pad 2 right edge 36.450 → R31 pad 1 left edge 37.775). The 0.925 mm
figure was wrong; the 0.900 mm number I had measured was the gap **between C20's own two pads**, and I
conflated the two. **Both bypass corridors accommodate the 1.20 mm pair envelope**, so widening one
was never the thing standing in the way.

### The east move is impossible, and the real constraint is vertical

C20 is boxed in on all four sides by parts §4 locks:

| Direction | Limit | Blocked by |
|---|---|---|
| west | **0.730 mm** | R30 |
| east | **0.730 mm** | R31 |
| north | **0.380 mm** | U10 |
| south | **0.695 mm** | J3 |

A 1.5–2.0 mm east move cannot be made without moving R31, which is forbidden. And it would not have
helped: J3's D+/D− pads run **N P N P at 0.5 mm pitch**, so getting all N to one side and all P to the
other needs exactly **one layer hop**, and that hop needs a via row in the band between J3's pad row
(y 147.070) and C20's pad row (y 145.525):

```
0.20  clearance to the J3 pad row
0.60  via pad          (the N/P crossing)
0.20  clearance
0.30  USB track        (the other polarity passing over the hop)
0.20  clearance to the C20 pad row
----
1.500 mm required      1.545 mm available      margin 0.045 mm
```

**It already fitted — by 45 µm.** That is not a manufacturable margin. East or west moves do not change
this band at all; south shrinks it. **North is the only productive direction**, and 0.300 mm of it
(keeping 0.080 mm of courtyard clearance to U10) takes the band to **1.845 mm — a 0.345 mm margin**.

### The move, and what it costs

**C20 (35.000, 144.800) → (35.000, 144.500)** — 0.300 mm north. Value, footprint, nets, rotation and
side unchanged. It is **0.300 mm, not ~2 mm**, honouring §2's "smallest move that provides a legal,
practical straight USB channel".

| Distance | Before | After | Δ |
|---|---|---|---|
| pad 1 → J3 A4 (VBUS) | 3.193 mm | 3.463 mm | **+0.270** |
| pad 1 → U10 pin 5 (VBUS) | 4.734 mm | **4.440 mm** | −0.293 |
| pad 2 → U10 pin 2 (GND) | 2.546 mm | **2.271 mm** | −0.276 |
| pad 2 → J3 A12 (GND) | 3.627 mm | 3.867 mm | +0.240 |

**Its bypass role is not sacrificed — it improves.** The move trades 0.27 mm of extra reach to J3's
nearest VBUS pad for 0.29 mm closer to U10's VBUS clamp and 0.28 mm closer to U10's ground. The VBUS
node is a low-impedance bulk rail with four connector pads on it; a 0.27 mm shift on one of them is
immaterial, while U10's clamp loop is the return path that actually wants to be short.

### USB — still not routed

The escape is now geometrically viable but was not routed in this pass. The route is planned and the
mechanism is settled: **one B.Cu hop for one polarity** (the pad order is N P N P, so exactly one
crossing is needed, and A7/B7 are the same net as each other, as are A6/B6, so they may merge freely).
The pair then takes the west and east 1.325 mm bypass corridors around C20 to U10 pins 1 and 3.

**Still open:** CONN / ESD / MCU segments, the E4 USB In2 lane, the two VBUS hand-off runs (SW7 pad 1
sits at the corridor mouth), and the SW9 SYS pair.

### State

118 tracks, 37 vias, unchanged from `15cb5a5`. In1 GND **10214.5 / 11181.0 mm² = 91.36 %**. **No via
inside either RF band. No USB net carries copper.** DRC **0 errors**, 256 warnings (the 20 dangling
tracks and 4 dangling vias remain the reserved E5 crossing segments and corridor hand-off vias, on the
correct nets, terminating at legal hand-off points, awaiting the digital pass). ERC **116 / 58
excluded / 58 live, zero delta**. **Placement: 188 footprints, C20 the only one moved.** Schematic and
`aqroot-Beta.kicad_dru` untouched.

**ROUTING PASS 1: FAIL** — USB not routed
**POWER / USB / CROSSING INFRASTRUCTURE LOCK: NO**
**READY FOR DIGITAL ROUTING PASS: NO**
**FULL ROUTING COMPLETE: NO**


---

## USB routed end to end — 0.25/0.20 geometry, and the two numbers that made it work (2026-08-11)

USB is **closed**. It took a geometry change, and the reason four earlier passes failed is now a
measured fact rather than a suspicion: **0.30/0.20 put the track width at the exact maximum the
connector's 0.5 mm pad pitch permits**, leaving 0.000 mm of margin on every one of the four escapes.

### The insight

At a fixed 0.5 mm pitch the adjacent-copper gap is `0.5 − W` and depends on **W alone**, while Zdiff
depends on **W and S**. The two can therefore be traded independently — which the original geometry
never exploited:

| Geometry | Zdiff (F.Cu over In1) | Gap at 0.5 mm pitch | Margin vs 0.20 mm |
|---|---|---|---|
| 0.30 / 0.20 (old) | 89.3 Ω | 0.200 mm | **+0.000** |
| 0.25 / 0.25 | 102.3 Ω | 0.250 mm | +0.050 |
| **0.25 / 0.20 (adopted)** | **97.6 Ω** | **0.250 mm** | **+0.050** |
| 0.25 / 0.14 | 90.2 Ω | 0.250 mm | +0.050 |

0.25/0.14 hits 90 Ω almost exactly, but a sub-0.20 mm intra-pair gap would have needed a P-to-N
clearance exception. **8 Ω of accuracy was traded to avoid that exception** — at Full Speed the
12 Mb/s edges are indifferent to +8.4 %, and no clearance rule anywhere on the board was weakened.

### Two mechanics worth recording

> **A 0.55 mm via pad on a 0.45 mm pair pitch always clashes with the other polarity's track**, no
> matter which polarity transitions first, and no manufacturable through-via is small enough to fix it
> (JLC's floor is 0.20 drill + 0.1275 ring = 0.455 mm pad, still larger than the pitch). So **both**
> polarities splay symmetrically at every transition and re-converge after it. This is what the 17 mm
> `diff_pair_uncoupled` budget exists for; three passes were spent trying to make one polarity hop
> alone, which cannot work.

> **The 0.5 mm pitch also breaks `diff_pair_gap`, and the fix is the width tolerance, not a rule.**
> At W = 0.25 the on-pitch gap is 0.250 mm — 0.010 mm *over* the 0.24 mm max. Widening only the
> on-pitch segments to **0.26 mm**, inside the approved 0.23–0.27 band, lands the gap on exactly
> 0.240 mm. Every segment still on the connector pitch carries 0.26; the nominal 0.25/0.20 pair
> geometry begins past it. **Six DRC errors closed with no rule change and no exception.**

### J3 fanout, as built

Straight parallel stubs from the pad row to y = 146.900 — far enough to clear the pads at 147.070 and
nothing more, which preserves the full 0.25 mm gap. **No diagonal begins inside the pad shadow.** A6/B6
then hold pitch for a further 0.200 mm before turning: the perpendicular from B7's stub end-cap to A6's
diagonal was 0.452 mm, which after both half-widths left 0.197 — 3 µm short, and only visible in DRC.

**A7 (N) is the single polarity that hops**, on B.Cu from (35.250, 146.200) to (33.500, 146.200). Once
it is off F.Cu the x = 35.25 lane is vacant, so **A6 and B6 (both P) merge straight over the top of it**
— one crossing resolves both merges, which is the only way two merges fit the 1.845 mm band. The P
merge at y = 145.575 sits in a 0.700 mm channel between C20's pads (145.225) and the via pads (145.925),
clearing both by 0.225 mm.

### Metrics

| Segment | P | N | Skew | Vias | Uncoupled |
|---|---|---|---|---|---|
| CONN | 11.05 mm | 9.32 mm | 1.72 mm | 2 (N) | 9.45 mm |
| ESD | 3.08 mm | 4.73 mm | 1.65 mm | 0 | 4.73 mm |
| MCU (incl. E4) | 67.01 mm | 75.35 mm | 8.35 mm | 4 | **13.35 mm** |
| **TOTAL J3→U1** | **81.14 mm** | **89.41 mm** | **8.27 mm** | **6** | max **13.35 / 17 mm** |

**Skew 8.27 mm ≈ 60 ps**, which is 0.07 % of a Full Speed bit and immaterial. It is architectural, not
sloppy: R33 sits west of U10 and R34 east, so N makes a westward excursion to R33 and comes back. It
would matter at High Speed and does not here.

**E4:** In2 only, N 30.00 mm at x = 53.400, P 30.09 mm at x = 53.850 (both inside the 53.0–54.3 west
lane). Transition vias at **(53.400, 116.000) / (54.150, 116.000)** south and **(53.400, 86.000) /
(54.150, 86.000)** north — all four **outside Y 88–114**, clearing the band by 2.0 mm. **Minimum
USB↔VBUS copper-to-copper on In2: 1.475 mm** against the 1.0 mm requirement.

> The P via pads overhang the west lane's 54.3 mm edge; the P **tracks** do not (max edge 54.275 mm).
> `enclosedByArea` checks tracks, and the two In2 splay diagonals were re-cut from 54.200 to 54.150
> for exactly this reason.

### E4 impedance — accepted by analysis, not validated

At 0.25/0.20 the In2 section reads **≈139.8 Ω** against the 90 Ω F.Cu target (reflection coefficient
0.22), because In1 is 1.065 mm away across the core rather than 0.2104 mm through prepreg. The section
is **≈216 ps one way** and USB here is Full Speed. Recorded in the DRU as
**USB E4 IMPEDANCE DISCONTINUITY → BETA SIGNAL-INTEGRITY / BRING-UP VERIFY**. **Not production-validated.**

### State

**DRC 0 errors**, 258 warnings (132 silk-over-copper, 96 silk-overlap, 20 dangling tracks + 6 dangling
vias — the reserved E5 segments and corridor hand-offs, awaiting the digital pass — 3 silk-edge,
1 text). **ERC 116 / 58 excluded / 58 live, zero delta.** **Placement 188 footprints, none moved this
pass**; C20 remains at (35.000, 144.500). **Schematic untouched.**

| | |
|---|---|
| Tracks / vias | **153** (was 118) / **43** (was 37) |
| USB tracks / vias added | **35 / 6** |
| In1 GND | **10209.6 / 11181.0 mm² = 91.31 %** (−4.9 mm² for the six new via clearances) |
| **USB vias in an RF band** | **NONE** — all six audited against 915 (Y 88–114) and 433 (X 0–52.5, Y 115–138) |
| **B.Cu tracks in the 915 band** | **0** — pristine |
| E5 rules changed | **none** |

**USB ROUTING: PASS**
**USB / E4 INFRASTRUCTURE LOCK: YES**
**ROUTING PASS 1 USB BLOCKER: CLOSED**


---

## SYS hand-off closed; the VBUS/E4 crossing is NOT complete, contrary to the Pass 1B entry (2026-08-11)

`BQ25185_SYS` is fully routed. The infrastructure audit also found that **the Pass 1B entry above
overstates the VBUS/E4 crossing** — the copper it describes is not in the board file.

### SYS to SW9 and R68

Both remaining ratsnest items sat in the far-west control cluster, ~53 mm from the SYS spine that
already runs the full board height at x = 61.200. The band **x 20–62, y 54–72 turned out to be
completely empty of both pads and copper**, so the trunk crosses it straight.

| | |
|---|---|
| Trunk | **43.70 mm at 0.80 mm** (preferred), y = 61.810, x 61.200 → 17.500 |
| Neck | **11.00 mm at 0.50 mm** (locked minimum), x 17.500 → 6.500 |
| To R68 pad 1 | 4.19 mm at 0.50 mm, x = 8.675 |
| To SW9 pad 2 | 4.31 mm at 0.50 mm, x = 6.500, entered from the south |
| **Total** | **63.20 mm, F.Cu only, 0 vias** |

The neck is forced by one channel: between C6/C7 (pad bottoms at 61.275) and U4 (pad tops at 62.350)
there is **1.075 mm**. At 0.80 mm that leaves 0.135 mm; at the locked 0.50 mm minimum it leaves
**0.285 / 0.290 mm**. So the trunk necks to the minimum and stays there — **no 0.20 mm package escape
was needed and none was used**, and nothing went onto In2.

SW9 pad 2 is entered **from the south**, through the 5.9 mm gap between its two outer mechanical pads
(x 3.550–9.450). A north approach is impossible: R14 pad 1 sits 0.125 mm above pad 2's top edge.
**SW9 was not moved or rotated**; its bezel zone carries no keepout in the file, and the branch at
x = 6.500 clears both mechanical pads by 2.7 mm.

Estimated drop at 500 mA: 34.1 mOhm over the 0.80 mm run + 10.9 mOhm over the neck, about **23 mV**.

### Correction: the VBUS/E4 crossing is incomplete

The Pass 1B entry states the In2 VBUS trunk runs `(28.000, 144.800)` to `(56.000, 144.800)` to
`(56.000, 84.000)`. **That copper is not in the file.** What exists is the E4 segment
`(56.000, 116.000)–(56.000, 86.000)`, a via at each end, a via at (28.000, 144.800) with nothing
attached, and the U11-side hop. `USB_VBUS_CHG` therefore has **2 missing connections**:

| Gap | From | To |
|---|---|---|
| south hand-off | via (28.000, 144.800) | In2 track at (56.000, 116.000) |
| north hand-off | F.Cu track end (56.000, 86.000) | U11 pad 10 (66.100, 66.200) |

`USB_VBUS_RAW` has a further **4 missing connections** — J3 pads B4/B9 to C20 pad 1, C20 to R35 pad 1,
and C20 to U10 pin 5. The connector-side VBUS distribution was never routed.

**Neither was attempted this pass**: the south leg's mouth is where SW7 sits, the RAW nets are inside
the area locked around USB, and the stated primary target was SYS. They are recorded here with exact
coordinates so the next pass can act on them directly.

### U9 EP grounding — the actual count is 6 + 2, not 6 + 3

Six vias sit **on U9 pad 33 (the EP)** at (23.300 / 23.950) by (20.850 / 22.000 / 23.150). Only **two**
GND fanout vias remain nearby, at **(26.550, 25.560)** and **(27.500, 25.560)**. The third went away in
Pass 1B when pads 12 and 16 were given a shared south rail to the (26.550, 25.560) tie — that was a
deliberate consolidation to open the C55 lane, and it was described in the entry above without the via
count being restated. Recording it now so the earlier "6 + 3" is not carried forward.

### Audit results

**Switch nodes** — unchanged, none altered:

| Node | Net | Length | Copper area | Layer |
|---|---|---|---|---|
| U12 buck | Net-(L1-Pad1) | 2.70 mm | 1.350 mm2 | F.Cu |
| U12 boost | Net-(L1-Pad2) | 6.89 mm | 3.443 mm2 | F.Cu |
| U13 SW | Net-(U13-SW) | 2.87 mm | 0.984 mm2 | F.Cu |
| U17 BL_SW | /03_SPI_A_DISPLAY_SD/BL_SW | 4.55 mm | 2.275 mm2 | **B.Cu** |

**RF, measured by span rather than endpoint** (the endpoint test used in earlier passes was too weak —
a track crossing a band has both ends outside it):

| Layer | In 915 band (Y 88–114) | In 433 band |
|---|---|---|
| F.Cu | **0 nets** | 0 |
| B.Cu | **0 nets — pristine** | 0 |
| In1.Cu | **0 nets** (plane only) | 0 |
| In2.Cu | 19 nets, 26.00 mm each | 5 nets (C-W), 23.00 mm each |

All 19 are authorised corridor content: 10 C-E radio/SPI-B, 5 C-W, USB D+/D-, +3V3, VBUS.
**Vias in the 915 band: 0. Vias in the 433 band: 0. Vias landing on a WROOM pad: 0.**
NFC copper is `/NFC_5V_PA_PENDING` only (the authorised C55 supply); **no NFC_DEFERRED net carries
copper**.

**Rule areas intact:** NFC RESERVED (4 layers), WROOM ANTENNA KEEPOUT (4 layers), HEADER RESERVED
(**F.Cu, B.Cu, In2 only — In1 is NOT a member of the keepout, so In1 GND fill continues
through the header region, broken only by the normal J5 pad antipads**).

**Thermal/ground vias:** U9 6+2 (above), U12 6, U11 3, U5 1, U14 1. **None added this pass.**

### State

**DRC 0 errors**, 258 warnings, of which the **26 dangling** are inventoried: 20 tracks (18 staged E5
crossings + the VBUS south leg + NFC_5V_PA) and 6 vias (2 VBUS, 2 USB E4 — the E4 pair's north vias
await the digital pass — 1 +3V3, 1 U13 FB). **21 staged crossings, 20 READY_FOR_DIGITAL_ROUTE, 1
(VBUS) incomplete.**

| | |
|---|---|
| Tracks / vias | **157** (was 153) / **43** (unchanged) |
| Unconnected items | **492** (was 494) |
| Nets carrying copper | **38** |
| In1 GND | **10209.6 / 11181.0 mm2 = 91.31 %** |
| Placement | **188 footprints, none moved**; C20 at (35.000, 144.500) |
| ERC | **116 / 58 excluded / 58 live, zero delta** |

**ROUTING PASS 1: FAIL** — SYS closed, VBUS_CHG (2) and VBUS_RAW (4) connections open
**POWER / USB / CROSSING INFRASTRUCTURE LOCK: NO** — VBUS/E4 incomplete
**READY FOR DIGITAL ROUTING PASS: NO**
**FULL ROUTING COMPLETE: NO**


---

## VBUS_CHG closed; USB_VBUS_RAW is unroutable without touching locked USB copper (2026-08-11)

`USB_VBUS_CHG` is **fully routed, 0 ratsnest items**. `USB_VBUS_RAW` is **not**, and the reason is now
measured rather than asserted: three of its five pads are enclosed by the locked USB pair with
**55–75 micron** shortfalls.

### USB_VBUS_CHG — both hand-offs closed

Rule binding first, since it was asked for: `USB_VBUS_RAW` and `USB_VBUS_CHG` both match the netclass
pattern `*USB_VBUS_*` to **VBUS_CHG** — `track_width` min 0.35 / opt 0.50, routed clearance min 0.25 mm
(non-pad to non-pad), via class POWER 0.40/0.80. **0.50 mm was used throughout**, the rule optimum;
no new class, no invented width.

| Leg | Path | Length |
|---|---|---|
| South approach | In2 (28.000, 144.800) → (54.850, 144.800) → (54.850, 119.000) | 52.65 mm |
| South hand-off | via (54.850, 119.000), then F.Cu → (54.850, 116.000) → (56.000, 116.000) at **0.35 mm** | 4.15 mm |
| E4 trunk | In2 (56.000, 116.000) → (56.000, 86.000), unchanged | 30.00 mm |
| North hand-off | F.Cu (56.000, 82.000) → (56.000, 77.000) → (71.800, 77.000) → (71.800, 66.000) → (70.775, 66.000) | 32.82 mm |
| **Net total** | **130.78 mm, 6 vias, min USB↔VBUS on In2 1.475 mm** | |

Two things were learned the hard way and are worth recording:

> **The E4 corridor and the VBUS lane both span y 84.000–118.000**, and the `enclosedByArea` mechanic
> from Pass 1B applies again: a track that *enters* a corridor can never satisfy it, because its end cap
> pokes past the boundary. A first attempt ran In2 straight from y 144.800 to y 116.000 and threw
> `Items not allowed` on exactly that. **The approach must stop north of y = 118 and hand off by via** —
> which is what every other crossing on this board already does.

> **The F.Cu link past SW7 threads 0.820 mm**: the `USB_D_MCU_P` via pad's right edge is 54.425 and
> SW7 pad 1's left edge is 55.245. A 0.50 mm VBUS track needs 0.95 mm there; the **0.35 mm rule
> minimum needs 0.80 mm and fits with 20 microns to spare**. That is a short local neck at the existing
> rule floor — not an exception — and it is the only sub-0.50 mm VBUS copper on the board. Clearance to
> SW7 pad 1 is **0.220 mm**. SW7 was not moved, rotated or altered.

The north leg needed no via at all. Every F.Cu path from (56, 82) to U11 is blocked by the **SYS spine
at x = 61.200 (y 30.000–75.000)** and by the **BAT_PROTECTED_P B.Cu wall at x 61.4–62.2, y 66.6–80.4**.
Rather than hop layers twice, the route goes **around the spine's south end at y = 77.000**, where the
band between C33/R38 (bottom 75.325) and U14 (top 79.600) is 4.275 mm of clear F.Cu.

### USB_VBUS_RAW — measured, and blocked

Every F.Cu escape channel around each RAW pad was measured against every non-RAW pad and track. The
requirement is 0.95 mm for a 0.50 mm track, **0.80 mm for the 0.35 mm rule minimum**, 0.95 mm for the
smallest approved via pad (0.55) and 1.20 mm for the VBUS POWER via (0.80).

| Pad | west | east | north | south | Verdict |
|---|---|---|---|---|---|
| J3 A9/B4 (east VBUS) | 0.200 | 0.200 | **1.370** | 0.175 | **reachable** |
| R35 pad 1 | **1.569** | 0.850 | open | open | **reachable** |
| U10 pin 5 | 0.350 | 0.350 | **0.975** | **0.950** | **reachable** |
| J3 A4/B9 (west VBUS) | 0.200 | 0.200 | 0.745 | 0.175 | **BLOCKED — 0.055 mm short** |
| C20 pad 1 | 0.525 | 0.900 | 0.675 | 0.225 | **BLOCKED — dead end** |

* **J3 west VBUS**: its only non-pad side is 0.745 mm north, against the `USB_D_CONN_N` west corridor.
  **55 microns short** of the 0.35 mm minimum.
* **C20 pad 1**: the 0.900 mm east channel between C20's own pads takes a 0.35 mm track, but it is a
  **dead end** — north is 0.675 mm to U10 pin 2, south is 0.225 mm to the `USB_D_CONN_P` merge.
* **U10 pin 5 → C20 pad 1**: reachable in isolation, but the routes around U10 pin 1 (west) and pin 3
  (east) are both **0.725 mm** against the N and P corridors — **75 microns short**.

Three independent shortfalls of 55–75 microns, every one against copper that this pass hard-locks.
**Connecting only the three reachable pads would close 2 of the 4 items while leaving C20 — the VBUS
bulk reservoir — disconnected**, which inverts the topology this task asks to preserve. So nothing was
routed on RAW.

Unlocking it needs one of: a small C20 or U10 placement change; re-cutting the `USB_D_CONN_P` merge at
y = 145.575; or via-in-pad on C20 pad 1 (its 1.000 x 1.450 mm pad would host a 0.80 mm via easily, but
that is a new fabrication technology). **All three are outside this pass's authority.**

### Corrections carried

**HEADER RESERVED wording fixed.** The previous entry read "In1 still excluded", which reads as though
In1 GND were removed. The board is right and the prose was ambiguous: the keepout has **F.Cu, B.Cu and
In2 as members and In1 is not one**, so **In1 GND fill continues through the header region**, broken
only by the normal J5 pad antipads. No geometry was changed.

**U9 ledger carried forward: 6 EP vias + 2 external GND fanout vias**, at (26.550, 25.560) and
(27.500, 25.560). U9 was not touched.

### State

| | |
|---|---|
| Tracks / vias | **165** (was 157) / **44** (was 43) |
| Unconnected items | **490** (was 492) |
| In1 GND | **10208.2 / 11181.0 mm2 = 91.30 %** |
| Vias in 915 / 433 band | **0 / 0** |
| F.Cu, B.Cu nets crossing the 915 band | **0 / 0 — B.Cu pristine** |
| Staged E5 dangling | **20 READY_FOR_DIGITAL_ROUTE, not consumed** |
| Placement | **188 footprints, none moved**; C20 at (35.000, 144.500) |
| USB | **unchanged** — 0.25/0.20, 0.26 mm launch, 0.25/0.55 vias, E4 untouched |
| DRC | **0 electrical errors** |

**ROUTING PASS 1: FAIL** — USB_VBUS_RAW has 4 connections that cannot be made under the current locks
**POWER / USB / CROSSING INFRASTRUCTURE LOCK: NO**
**READY FOR DIGITAL ROUTING PASS: NO**
**FULL ROUTING COMPLETE: NO**


---

## Moving C20 east does NOT unlock USB_VBUS_RAW — and my previous diagnosis was wrong (2026-08-11)

The C20 lock was released eastward to close `USB_VBUS_RAW`. **The sweep shows the move cannot work, so
C20 was not moved and no copper was changed.** Two of my own earlier numbers were wrong and are
corrected below.

### Correction 1: the binding channel is west, not east

Last pass I reported C20 pad 1's escape sides as `west 0.525 / east 0.900 / north 0.675 / south 0.225`
and concluded the 0.900 mm east channel was "the only viable side". That measurement **charged a
clearance against C20's own pad 1**. The escape track is `USB_VBUS_RAW` — *the same net as pad 1* — so
no clearance applies on that side at all. The track may overlap the pad; it connects to it.

Re-measured correctly, **a 0.50 mm track already attaches to C20 pad 1 from the west at d = 0**:
centred at x = 33.525 it holds 0.250 mm to the `USB_D_CONN_N` corridor and its right edge lands at
33.775, well inside pad 1. Attaching was never the problem.

**Travelling is.** Once attached, the track must run north or south along that channel:

| Channel | Bounded by | Width | 0.35 mm track needs | Short by |
|---|---|---|---|---|
| north (travel) | `USB_D_CONN_N` right edge 33.025 → U10 pin 1 left edge 33.750 | **0.725 mm** | 0.25 + 0.35 + 0.20 = 0.800 | **75 µm** |
| south | C20 pad 1 bottom 145.225 → `USB_D_CONN_P` merge top 145.450 | **0.225 mm** | 0.800 | unusable |

**Neither channel contains C20.** Both are bounded by the two locked USB corridors and by U10. Moving
C20 east cannot widen either one.

### Correction 2: +0.6 mm east is not legal, and would not have helped

I suggested "moving C20 ~0.6 mm east" as the cheapest unlock. The full-constraint sweep — every C20 pad
against every non-C20 pad, track and via, plus courtyard overlap, in 0.025 mm steps — caps the window
much earlier:

| Limit | Cap on d |
|---|---|
| C20 pad 2 vs the `USB_D_CONN_P` east corridor (x 37.100, left edge 36.975) | **d ≤ 0.300** (0.325 fails DRC) |
| C20 courtyard vs R31 courtyard | d ≤ 0.730 |
| C20 courtyard vs U10 courtyard | 0.080 mm, unaffected by eastward motion |

So the legal window is **d ≤ 0.300 mm**, and at that maximum the pad-1 west channel reaches only
0.825 mm — still 0.35 mm width with **0.025 mm** of margin, which section 4 of the directive explicitly
refuses. **No eastward displacement satisfies the requirement.** C20 stays at (35.000, 144.500).

### What would actually unlock it

The 75 µm shortfall is in the `USB_D_CONN_N` → U10 pin 1 channel, and that corridor has room to move
**away** from U10:

| | |
|---|---|
| `USB_D_CONN_N` vertical, x = 32.900, w 0.25 → left edge | 32.775 |
| R30 pad 2 right edge | 32.225 |
| **clearance available today** | **0.550 mm** |
| shift needed for a 0.35 mm RAW track | **0.075 mm** |
| shift for 0.10 mm routing margin | **0.175 mm** |
| clearance to R30 pad 2 after a 0.175 mm shift | **0.375 mm** (0.20 required) |

Shifting that one straight segment 0.175 mm west takes the channel to 0.900 mm and closes the RAW
escape with margin. The segment is a single-ended uncoupled run through the C20 bypass region — it is
already inside the 17 mm uncoupled budget, so the shift changes no impedance, no coupling and no skew.
**It is a USB change, which this pass hard-locks, so it was not made.**

The alternative that touches no USB copper is a **U10 placement change** — moving U10 ~0.1 mm east
widens the same channel — but U10 is fixed by the same section.

### State

**Nothing was routed and nothing was moved.** Board geometry is byte-identical to `aaf8e27`: 165 tracks,
44 vias, 188 footprints, C20 at (35.000, 144.500), DRC **0 electrical errors**, ERC **116 / 58 excluded
/ 58 live**. `USB_VBUS_RAW` still has **4** open connections; every other Pass-1 net is closed.

**USB_VBUS_RAW: FAIL**
**ROUTING PASS 1: FAIL**
**POWER / USB / CROSSING INFRASTRUCTURE LOCK: NO**
**READY FOR DIGITAL ROUTING PASS: NO**
**FULL ROUTING COMPLETE: NO**
## C21/C22 data-side pins set NC for Beta — Option B locked (2026-08-12)

CTO ruling, **Option B — LOCKED**. `C21` and `C22` are **retained physically** at their existing
placement, remain **100 pF**, remain **DNP**, and their **data-side pins are intentionally
NC for Beta**. Their **GND pins stay connected**. They are an **optional USB Full-Speed
edge-rate / EMI tuning footprint** and a **rework-grade contingency only**.

### Verified topology before the change

| | pin 1 | pin 2 |
|---|---|---|
| C21 (`C_USB_DN_EMC`) | `/USB_D_MCU_N` | `GND` |
| C22 (`C_USB_DP_EMC`) | `/USB_D_MCU_P` | `GND` |

Both `Device:C`, value `100pF DNP`, `dnp yes`, footprint `Capacitor_SMD:C_0603_1608Metric`.
Matches the expected mapping — pin 1 is the data side on both.

### Schematic edits (`01_power_tree.kicad_sch`)

Wire deletion first, NC flag second, so no wire-connected-to-NC artifact is created:

- deleted wire `(54.61 57.15) → (54.61 58.42)` — the C21 pin-1 stub
- deleted wire `(76.20 57.15) → (76.20 58.42)` — the C22 pin-1 stub
- deleted the two **local labels** `USB_D_MCU_N` @ (54.61, 57.15) and `USB_D_MCU_P` @ (76.20, 57.15)

That last deletion was **required, not optional**. Each stub carried its net solely through a local
label sitting at its far end; nothing else on the sheet touched those two points. Deleting only the
wires would have left two labels floating in space and produced two **new live `label_dangling`
errors**, which the no-regression gate forbids. The hierarchical labels `USB_D_MCU_N` @ (177.80,
25.40) and `USB_D_MCU_P` @ (177.80, 34.29) are untouched and still carry both nets off-sheet.

- added `no_connect` @ (54.61, 58.42) — C21 pin 1
- added `no_connect` @ (76.20, 58.42) — C22 pin 1
- added one schematic text note @ (45.72, 73.66) adjacent to the pair

Symbols, references, values, footprints and DNP status were not touched. C21/C22 GND connections
were not touched.

### Netlist result

`C21.1` and `C22.1` now resolve to `unconnected-(C21-Pad1)` / `unconnected-(C22-Pad1)`.
`C21.2` and `C22.2` remain `GND`. The USB data nets keep exactly their real pair path:

- `/USB_D_MCU_N` → `R33.2`, `U1.13`
- `/USB_D_MCU_P` → `R34.2`, `U1.14`

### PCB synchronisation

Net-only sync. `C21` pad 1 and `C22` pad 1 were moved off the USB data nets onto their
`unconnected-(...)` nets — the same convention the board already uses for its 20 existing NC pins.
GND pads untouched. **No branch copper existed at either data pad and none was created.**

| | before | after |
|---|---|---|
| footprints | 188 | 188 (**0 moved**, position / rotation / side / footprint identical) |
| tracks | 364 | 364 |
| vias | 98 | 98 |
| ratsnest | 440 | **438** (**−2**, one per capacitor) |
| DRC electrical errors | 0 | **0** |
| DRC schematic parity | 0 | 0 |
| ERC | 116 / 58 excluded / 58 live | **116 / 58 excluded / 58 live** |

The two ratsnest items that disappeared are exactly:

- `Pad 1 [/USB_D_MCU_N] of C21 ↔ Pad 2 [/USB_D_MCU_N] of R33`
- `Pad 1 [/USB_D_MCU_P] of C22 ↔ Track [/USB_D_MCU_P] on F.Cu, 1.1654 mm`

Both nets still show their one remaining open — the In2.Cu track to the `U1` pad — which is the
USB routing work this pass deliberately did not start.

### Rules unchanged

USB uncoupled budget stays **25 mm**. USB skew limit stays **2.000 mm**. No DRU change. No USB
copper, `BMI270_INT1_STRAP`, E4 handoff, SPI-A, I2C, display/control, power, radio crossing, C20,
U9 grounding or RF rule was touched.

### Revalidation condition

**Before any future population or reconnection of C21/C22, the 100 pF value must be revalidated
against actual measured USB edge-rate / EMI behaviour.** The value is an inherited assumption, not
a measured result, and reconnecting an unvalidated 100 pF to a Full-Speed data line is a
signal-integrity risk, not a neutral default. Restore the connection at the next revision only if
Beta EMI data justifies it.

### Ledger — deferred, do not solve yet

**VERIFY after final USB routing:** each `C21` / `C22` data pad must have a **solder-accessible
attachment point** — outer-layer USB copper or an accessible via — **within practical tack-jumper
reach**. If it does not, document that **mask scraping** or an **added future-revision test point**
is required. No test points, jumpers, vias or copper were added for this now.

**C21 DATA PIN NC: PASS**
**C22 DATA PIN NC: PASS**
**C21/C22 BETA ARCHITECTURE: LOCKED**
**RATSNEST: 438**
**ERC NO-REGRESSION: PASS**
**PCB GEOMETRY CHANGED: NO**
**USB ROUTING STARTED: NO**

## USB MCU-side routed end to end — the pair is closed, and the crossover the CTO specified is real (2026-08-12)

`USB_D_MCU_N` and `USB_D_MCU_P` are **complete**. Both E4 handoff vias are consumed, both nets are a
**single copper island** from the connector to the MCU, and no copper was added to C21/C22.

### The proven route was reconstructed, not re-searched

The previous attempt was never committed, so the route had to be rebuilt from the directive's fixed
points. Three independent numbers confirm the reconstruction landed on the same geometry:

| directive | measured on the current board |
|---|---|
| SYS clearance 0.265 mm | **0.265 mm** — south via row edge 62.475 vs SYS rail edge 62.210 |
| SYS clearance 0.285 mm | **0.285 mm** — north via row edge 61.125 vs SYS rail edge 61.410 |
| south corridor 1.200 mm | **1.200 mm** — U1 top-row pad edge y=18.000 to `BMI270_INT1_STRAP` B.Cu edge y=19.200 |

Those fall out of the geometry only if the crossover sits at y=62.750 / y=60.850 across the 0.80 mm
`BQ25185_SYS` rail at y=61.810, and only if the transition vias sit in the U1 / BMI-strap corridor.

### Why the chirality crossover is not optional

At the E4 handoff N is **west** of P, and at U1 pads 13/14 N is again **west** of P — which looks like
no swap is needed. It is. The final approach to the transition vias can only come **from the west**:
east of pad 14 the F.Cu band is closed by C54 (x 26.425–27.375) and then by the `NFC RESERVED`
keepout at x=28, leaving a 0.625 mm gap. So the pair arrives travelling **east**, and the track that
must continue past the other's via is the one that has to pass **north** of it. That forces N's via
south (18.700) and P north-then-down (18.075 → 18.500), which puts N on the right-hand side
travelling east — one chirality swap, taken at the SYS crossing where the pair has to leave F.Cu
anyway. N crosses on **In2.Cu**, P on **B.Cu**, so the two legs cross without shorting.

### Geometry as built

| | N (`USB_D_MCU_N`) | P (`USB_D_MCU_P`) |
|---|---|---|
| E4 handoff consumed | via (53.400, 86.000) | via (54.150, 86.000) |
| crossover south via | (39.400, 62.750) | (40.150, 62.750) |
| crossover leg | **2.0427 mm on In2.Cu** | **2.0427 mm on B.Cu** |
| crossover north via | (40.150, 60.850) | (39.400, 60.850) |
| long run | F.Cu, 0.25 mm wide / 0.20 mm gap | F.Cu, 0.25 mm wide / 0.20 mm gap |
| transition via | (23.025, 18.700) | (24.000, 18.500) |
| B.Cu fanout lands at | (22.730, **16.900**) in U1.13 | (24.290, **17.700**) in U1.14 |
| MCU-side length | **120.9929 mm** | **122.0940 mm** |

The two fanout landing points are the **only** deviation from the directive's coordinates, and they
are the skew correction (below). Every other fixed point is exactly as specified.

Corridor occupancy at U1: the staggered via band spans y 18.225–18.975 inside the 1.200 mm corridor,
leaving **0.225 mm** to the U1 pad row and **0.225 mm** to the BMI strap against a 0.200 mm rule —
0.025 mm of margin on each side. `BMI270_INT1_STRAP` itself was not touched.

### Skew

At the directive's literal fanout endpoints (both at y=17.400) the route measures **1.879 mm** of
skew — legal, but only 0.121 mm inside the 2.000 mm limit. The structural cause is corner parity:
five 90° corner pairs, three of them with P on the outside, and a square diff-pair corner makes the
outer track longer by exactly 2 × pitch = 0.90 mm every time.

Rather than add a meander, the correction was taken as **landing depth inside the destination pads**:
N lands 0.500 mm deeper into U1.13 and P lands 0.300 mm shallower into U1.14. Both endpoints stay
well inside their pads (both span y 16.500–18.000), so contact is unaffected.

| | |
|---|---|
| MCU-side skew | **1.1011 mm** = **7.93 ps** at 7.2 ps/mm |
| limit | 2.000 mm |
| margin | 0.899 mm |

**Full end-to-end pair length is a separate number and it is worth recording honestly.** Total copper
`USB_D_MCU_N` = 196.3471 mm, `USB_D_MCU_P` = 189.1019 mm — a **7.245 mm (~52 ps)** intra-pair
difference. It is **not** caused by this pass: the connector-side geometry, which this pass
hard-preserves, already runs N 8.347 mm longer than P, and the MCU-side route pulls 1.101 mm of that
back. At Full Speed (12 Mbps, ~4 ns edges) 52 ps is immaterial, and USB 2.0 tolerates far more even
at High Speed, which this design does not implement. Flagged rather than fixed, because nulling it
would require an 8.3 mm MCU-side mismatch and that violates the 2.000 mm gate the CTO set.

### Measured against the rules

Every number below is KiCad's, not an estimate. The uncoupled figure was obtained by running DRC on a
**throwaway copy** of the project with `diff_pair_uncoupled` forced to 0.001 mm so the checker prints
the actual value; **the real `.kicad_dru` was not modified and the 25 mm budget stands.**

| | measured | limit |
|---|---|---|
| DRC electrical errors | **0** | 0 |
| `USB_D_MCU_N` ratsnest | **0** | 0 |
| `USB_D_MCU_P` ratsnest | **0** | 0 |
| diff-pair uncoupled, MCU pair | **22.1321 mm** | 25.000 mm |
| intra-pair gap, minimum | **0.2000 mm** | 0.18–0.24 mm |
| clearance to other nets, minimum | **0.2292 mm** (P via to U1.15 pad) | 0.200 mm |
| NFC RESERVED intrusion | **0** (nearest approach 3.585 mm) | 0 |
| new vias in 915 / 433 bands | **0** | 0 |
| new B.Cu in 915 / 433 bands | **0** | 0 |

The uncoupled result came in at 22.13 mm rather than the ~19.2 mm the directive projected. That
projection subtracted the 7.063 mm of C21/C22 branch from the old 26.280 mm figure; this route is not
the old route segment-for-segment, and its corner and crossover splays account for the ~2.9 mm
difference. It sits inside the production budget with 2.868 mm to spare and **the rule was not
relaxed**.

### End-to-end connectivity, verified independently of DRC

Union-find over the actual copper, not the ratsnest:

| net | islands | pads in the island |
|---|---|---|
| `USB_D_CONN_N` | 1 | J3.A7, J3.B7, U10.1 |
| `USB_D_ESD_N` | 1 | U10.6, R33.1 |
| `USB_D_MCU_N` | 1 | R33.2, **U1.13** |
| `USB_D_CONN_P` | 1 | J3.A6, J3.B6, U10.3 |
| `USB_D_ESD_P` | 1 | U10.4, R34.1 |
| `USB_D_MCU_P` | 1 | R34.2, **U1.14** |

Before this pass each MCU net was **two** islands with the U1 pad stranded. **C21 and C22 are not
members of either net** — their data pads carry `unconnected-(C21-Pad1)` / `unconnected-(C22-Pad1)`
and have **zero copper objects** on those nets.

### C21/C22 rework accessibility — the deferred CTO check, now answerable

| | C21 pad 1 | C22 pad 1 |
|---|---|---|
| DNP data pad centre | (29.725, 142.400) F.Cu | (38.725, 142.400) F.Cu |
| nearest solder-accessible point on the matching net | **R33 pad 2** (31.325, 139.800) F.Cu | **R34 pad 2** (40.325, 139.800) F.Cu |
| mask | **open** (F.Mask + F.Paste) | **open** (F.Mask + F.Paste) |
| centre to centre | 3.053 mm | 3.053 mm |
| pad edge to pad edge | **1.812 mm** | **1.812 mm** |
| practical tack jumper | **YES** | **YES** |

**PASS. No mask scraping is required and no future-revision test point is needed.** The attachment
point is not a compromise: R33.2 / R34.2 are the MCU-side terminals of the 22R series resistors —
exactly the node each capacitor is meant to shunt — so a tack jumper from the DNP pad to that
resistor pad restores precisely the intended connection. Same-net F.Cu track copper also passes
within 2.291 mm of each DNP pad, but it is under solder mask and is the fallback, not the plan.

### Preservation

188 footprints, **0 moved**. Schematic **untouched** — ERC unchanged at **116 / 58 excluded / 58
live**. `.kicad_dru` **unchanged**; the 25 mm uncoupled budget and the 2.000 mm skew limit stand.
Schematic parity **unchanged at 261** pre-existing cosmetic field / footprint-name mismatches, delta
exactly zero, none of them USB or C21/C22 related. *(Note for future passes: `kicad-cli pcb drc` only
runs the parity check when `--schematic-parity` is passed; without it the report shows an empty
parity list, which is absence of the test, not a clean result.)*

An order-independent set comparison of every copper object against `9ddc74f`: **23 tracks added, 0
removed; 6 vias added, 0 removed; 776 pads, 0 changed.** Tracks 364 → 387, vias 98 → 104, board
ratsnest **438 → 436**. The remaining file diff is the In1 GND plane refill around the six new vias
plus KiCad's own reordering of two footprint blocks (C50 / C55) and two `USB_D_ESD_P` segments — both
reorders reproduce on an untouched copy of the board, so they are the writer's canonical ordering and
not a change. Zones were refilled with `kicad-cli pcb drc --refill-zones --save-board`, which is
required after adding vias by direct file edit: without it the new vias have no In1 void and DRC
correctly reports zone and hole-clearance errors.

**USB MCU PAIR: PASS**
**USB END-TO-END: PASS**
**USB UNCOUPLED: 22.1321 / 25.000 mm**
**USB SKEW: 1.1011 / 2.000 mm**
**USB CROSSOVER: PASS**
**C21/C22 NC PRESERVED: YES**
**C21/C22 REWORK ACCESS: PASS**
**USB E4 HANDOFFS CONSUMED: YES**
**USB BLOCK: HARD-LOCKED COMPLETE**
**READY FOR SPI-B: YES**

## SPI-B pass 3A-1: SCK and MOSI reach U1, U8 and U7 — and U9 is provably unreachable (2026-08-12)

`SPI_B_SCK` and `SPI_B_MOSI` are routed from U1 through the staged C-E crossings to both radios.
**Three of each net's four endpoints are connected. The fourth — U9 — cannot be routed at all**, and
that is the headline of this pass.

### U9.30 / U9.31 are sealed in closed pockets

U9's SPI-B pads are 0.30 x 0.75 mm F.Cu pads on the chip's north edge at y 19.350–20.100. Everything
that could carry them out of that band is now occupied:

| boundary | what closes it |
|---|---|
| north-west | `USB_D_MCU_N` transition via at (23.025, 18.700), Ø0.55 |
| north-east | `USB_D_MCU_P` transition via at (24.000, 18.500), Ø0.55 |
| south | U9's own pad row and the U9.33 exposed GND pad |
| all layers | `BMI270_INT1_STRAP` B.Cu at y 19.300, x 19.800–25.000 |

A flood fill of the legal 0.20 mm-track centreline space, seeded on each pad, returns a **closed
pocket**:

| net | pad | reachable region | escapes? |
|---|---|---|---|
| `SPI_B_SCK` | U9.30 | x 23.480–23.960, y 18.890–19.970 | **NO** |
| `SPI_B_MOSI` | U9.31 | x 23.190–23.340, y 19.190–19.970 | **NO** |

A via cannot rescue it either. The **largest all-layer clearance anywhere inside either pocket is
0.350 mm**; the smallest legal via on this board (0.55/0.25, the geometry already approved for the
USB and `USB_VBUS_RAW` escapes) needs **0.475 mm**. Even a zero-width track fails the arithmetic: at
x ≈ 23.0 the USB N via demands y ≥ 19.175 while U9's neighbouring pads demand y ≤ 19.150.

**This is not a routing-order problem and no amount of effort in this pass fixes it.** The corridor
was already marginal before USB — the BMI strap at y=19.300 alone forces any via to sit at
y ≤ 18.725 — and the two USB transition vias, placed at coordinates the CTO fixed in the USB
directive and now hard-locked, close the remaining gap. Resolving it needs a decision at CTO level:

1. **Move one or both USB transition vias.** Opening the x 23.30–23.73 gap to ≥ 0.95 mm would let a
   0.20 mm track out eastward. This breaks the USB hard-lock and needs the USB gates re-run.
2. **Move U9** ~0.5 mm south, opening the band between its pad row and the USB/BMI copper. This
   breaks placement lock and disturbs the NFC matching geometry.
3. **Re-pin U9's SPI-B on the ST25R3916** if the part allows an alternative SPI mapping, moving
   SCK/MOSI/MISO to pads with a free escape.
4. **Accept U9 off the SPI-B bus for Beta**, which means no NFC — almost certainly unacceptable.

Note this blocks **`SPI_B_MISO` identically** (U9.32 sits in the same row), so pass 3A-2 will hit the
same wall. The decision should be taken before MISO is attempted.

### What was routed

Topology as directed: one shared trunk per net with short tees, no star branches.

| | `SPI_B_SCK` | `SPI_B_MOSI` |
|---|---|---|
| U1 escape | U1.4, B.Cu stub **1.700 mm** to a via at (11.300, 19.100) | U1.5, B.Cu stub **2.524 mm** to a via at (13.400, 19.500) |
| In2 descent lane | x = 11.300, y 19.100 → 82.000 | x = 13.000, y 20.300 → 80.000 |
| F.Cu hop | (11.300, 82.000) → (15.000, 84.200) | (13.000, 80.000) → (16.400, 83.500) |
| In2 east lane | y = 84.200 to x = 59.000 | y = 83.500, stepping to 83.700 at x 54.5–55.2 |
| staged C-E crossing consumed | **x = 59.000, y 85.000 → 117.000** | **x = 60.000, y 85.000 → 117.000** |
| radio trunk | x = 59.450, **36.451 mm** | x = 60.150, **36.050 mm** |
| U8 tee | B.Cu **1.450 mm** into U8.18 | B.Cu **2.150 mm** into U8.17 |
| U7 stub | B.Cu **1.700 mm** into U7.18 | B.Cu **1.700 mm** into U7.17 |
| total net copper | **187.544 mm** | **184.826 mm** |
| vias added | 5 (0.60/0.30 through) | 5 (0.60/0.30 through) |
| layers | In2 144.794, F.Cu 5.900, B.Cu 4.850 | In2 141.573, F.Cu 6.374 … B.Cu 6.374, F.Cu 4.880 |

Both staged crossings were **consumed, not moved, duplicated, replaced or resized** — the new copper
simply lands on their existing endpoints at y = 85.000 and y = 117.000.

### Two things the corridor forced

**The F.Cu hop is not decoration.** `DISP_RST_N` runs on In2 at y = 82.800 from x = 6.400 to
x = 45.250, and it seals every In2 descent between those x. The only clean east-west In2 lane to the
C-E crossings lies *south* of it, at y ≈ 83.5–84.4. Both nets therefore leave In2 briefly, cross the
barrier on F.Cu, and return — one extra via each. Crossing on B.Cu instead is not available: the
`SD_CS_N` and `SPI_A_MISO` B.Cu horizontals at y = 81.000 and y = 82.000 occupy that window.

**SCK dodges the `SPI_A_MOSI` via at (33.250, 84.400).** With `SPI_B_MOSI` pinned to y ≈ 83.5 by J4's
through-hole pads (south edge y = 83.375) and `SPI_B_SCK` 0.7 mm south of it, SCK's lane runs straight
into that via. Rather than re-lane the pair, SCK takes a 2.6 mm dip to y = 85.100 across x 32.0–34.6.
Closest approach to the via is **0.2368 mm**.

### Measured

| | measured | required |
|---|---|---|
| DRC electrical errors | **0** | 0 |
| minimum clearance, new copper to anything | **0.2250 mm** (MOSI In2 to J4 pads) | 0.200 mm |
| minimum SCK ↔ MOSI same-layer clearance | **0.2950 mm** | 0.200 mm |
| minimum clearance to USB copper | **0.2700 mm** (MOSI via to `USB_D_MCU_N` F.Cu) | 0.200 mm |
| minimum clearance to the `SPI_B_MISO` reserved lane | **0.7200 mm** | — |
| lateral clearance to every reserved future lane (x 61–69.1) | **0.6500 mm** | — |
| new vias in the 915 band | **0** | 0 |
| new vias in the 433 band | **0** | 0 |
| new B.Cu through the 915 band | **0** | 0 |
| NFC RESERVED intrusion | **0** (nearest 14.300 mm) | 0 |
| 915 band clearance | 2.800 mm | — |
| 433 band clearance | 5.400 mm | — |
| `SPI_B_SCK` ratsnest | **1** (U9.30 only) | 0 — **not met, blocked** |
| `SPI_B_MOSI` ratsnest | **1** (U9.31 only) | 0 — **not met, blocked** |

Connectivity verified by union-find over the copper, independent of the ratsnest:
`SPI_B_SCK` = {U1.4, U8.18, U7.18} in one island plus U9.30 isolated;
`SPI_B_MOSI` = {U1.5, U8.17, U7.17} in one island plus U9.31 isolated.

### The MISO corridor is still usable

`SPI_B_MISO`'s staged lane at x = 61.000 is untouched, and the trunks were deliberately pulled west
(59.450 / 60.150 rather than the 59.5 / 60.5 first laid out) so that a future MISO via at x = 61.000
keeps 0.45 mm to the nearest In2 trunk. MISO can still reach U8.16 by dropping to B.Cu at x ≈ 61 and
running west under U8's body — the two In2 trunks pass beneath on a different layer — and U7.16 by
running In2 west at y ≈ 150.5 to x ≈ 58.4, east of both trunks. The reserved lanes at x 62–66
(SX1262), x 67–68 (CC1101) and x 69.100 (+3V3) are likewise clear; nearest approach of any new
copper to any of them is **0.650 mm**.

### Preservation

Order-independent copper set comparison against `af04cc1`: **33 tracks added, 0 removed; 10 vias
added, 0 removed; 776 pads, 0 changed**; every added object is on `/SPI_B_SCK` or `/SPI_B_MOSI`.
**USB copper: 111 objects before, 111 after, 0 added, 0 removed** — the pair, the crossover, the
south corridor and both E4 handoffs are byte-identical, and `USB_D_MCU_N` / `USB_D_MCU_P` remain at
ratsnest 0. `BMI270_INT1_STRAP`: 7 objects, unchanged. C21/C22 still carry
`unconnected-(Cxx-Pad1)` with **zero copper** on those nets.

188 footprints, **0 moved**. Schematic untouched — ERC **116 / 58 excluded / 58 live**, unchanged.
`.kicad_dru` unchanged. Schematic parity unchanged at **261** pre-existing cosmetic mismatches.
Tracks 387 → 420, vias 104 → 114, board ratsnest **436 → 430**.

Staged infrastructure: free track endpoints **27 → 23**. The four consumed are exactly the north and
south ends of the two SPI-B C-E crossings; `SPI_B_SCK` and `SPI_B_MOSI` no longer appear in the
staged list. `SPI_B_MISO`, SX1262 x5, CC1101 x2, `BTN_HOME_N`, +3V3 and the three pre-existing
`BQ25185_SYS` / `LED_K` / `NFC_5V_PA_PENDING` ends remain. Dangling vias: 1 (+3V3), unchanged.
**No orphan copper.**

**SPI_B_SCK: PARTIAL — U1, U8, U7 connected; U9 blocked**
**SPI_B_MOSI: PARTIAL — U1, U8, U7 connected; U9 blocked**
**SPI-B SHARED BUS: PARTIAL — 2/3 nets routed, both 3/4 endpoints**
**USB PRESERVED: YES**
**READY FOR SPI_B_MISO: NO — the U9 escape must be resolved first**

## U9 moved 0.050 mm south — the first swept position is legal, and a correction to the last pass (2026-08-12)

U9 moves from **(24.500, 22.000)** to **(24.500, 22.050)**: ΔX 0.000, ΔY +0.050, magnitude **0.050 mm,
direction S**. Rotation and side unchanged. That is the **first candidate the ordered sweep tested**,
and per the binding sweep order the sweep stopped there — no larger move was evaluated and no
optimisation was attempted.

### Correction: U9.30 was never sealed

The previous pass reported that **both** U9.30 and U9.31 sat in closed pockets. That was wrong for
U9.30. Re-running the escape analysis at 0.005 mm resolution — four times finer than the 0.01 mm
flood used before — finds a legal F.Cu escape for U9.30 at the *old* position, through a single
pinch at **(23.775, 19.040)** where the clearance is **0.3100 mm**, i.e. a 0.20 mm track keeps
**0.2100 mm** to the `USB_D_MCU_P` via. That is above the 0.200 mm rule. The earlier flood's
resolution was too coarse to resolve a gateway that is one grid cell wide, and it reported the
pocket as closed.

**U9.31 was correctly identified as blocked**, so the pass-3A-1 outcome — SPI-B could not be closed
to U9 — stands unchanged, as does the conclusion that a CTO decision was needed. But the specific
claim "U9.30 is in a closed pocket" was false, and `SPI_B_SCK` could in principle have been routed
to U9.30 at the old position. The measured numbers in that entry should be read with this
correction.

Two lessons, both now baked into the tooling: a grid escape test must resolve gateways narrower than
the grid, and any margin inside the grid's Lipschitz error must be confirmed analytically. Every
escape reported below was re-derived exactly at its pinch point, not read off the grid.

### Verified before the sweep

U9: `ST25R3916_AQET`, F.Cu, rotation 0, at (24.500, 22.000). SPI pads confirmed —
U9.30 `SPI_B_SCK` x[23.600..23.900] y[19.350..20.100]; U9.31 `SPI_B_MOSI` x[23.100..23.400];
U9.32 `SPI_B_MISO` x[22.600..22.900]; all F.Cu, all y[19.350..20.100]. Exposed pad U9.33
x[22.775..26.225] y[20.275..23.725], **6** EP through-vias, 0.25 drill / 0.55 pad.

**Decoupling-set discrepancy, reported before executing.** All eight capacitors the CTO listed
(C19, C45, C47, C49, C51, C53, C54, C55) exist and are U9-associated. The list is **incomplete**:
the U9 supply rails also carry **C46** (`NFC_VDD_D`, 4.100 mm), **C48** (`NFC_VDD_A`, 4.079 mm),
**C50** (`NFC_VDD_RF`, 3.036 mm) and **C52** (`NFC_VDD_AM`, 2.767 mm) — the *near* member of each
pair, where C45/C47/C49/C51 are the *far* ones out at x ≈ 9 — plus **C18** (+3V3, 3.705 mm to U9.1).
C50 and C52 sit directly south of U9 at y 26.425–27.375 and are the capacitors a southward move
actually threatens, so gating on the CTO list alone would have missed the only ones that matter for
direction S. All thirteen were carried through the sweep. Nothing was omitted or silently added.

**C55 metric ambiguity, also reported before executing.** Measured two ways:

| C55.1 to | centre-to-centre | copper-path along the `NFC_5V_PA_PENDING` rail |
|---|---|---|
| U9.8 | 4.875 mm | 8.125 mm |
| U9.10 | 4.469 mm | 5.925 mm |

Under the centre-to-centre reading both are inside the CTO's 5 mm "acceptable-with-report" band.
Under the copper-path reading **the pre-move baseline already exceeds 5 mm**, so that reading cannot
be a candidate gate — it would fail the board as it stands today. The sweep therefore gated on
centre-to-centre and both numbers **improve** with the move.

### The sweep

Magnitude-major, S then SW then W at each magnitude, starting at 0.050 mm. **The first row is legal**:

| mag | dir | ΔX | ΔY | U9 at | U9.30 | U9.31 | U9.32 | via landing | USB N | USB P | EP/WROOM | NFC | C55 | overall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | **S** | 0.0000 | +0.0500 | (24.5000, 22.0500) | PASS 0.0300 | PASS 0.0126 | PASS 0.4500 | YES / YES / YES | 0.4290 | 0.6305 | 0.2500 | 0.8500 = baseline | 4.42 / 4.83 | **LEGAL** |

Escape margin is the slack above the 0.300 mm a 0.20 mm centreline needs, so a margin of 0.0300
means the track keeps 0.2300 mm of clearance. **U9.31's escape is thin — 0.2126 mm clearance,
0.0126 mm of slack** — pinching at (23.605, 18.935) against the `USB_D_MCU_P` via. Legal, and the
sweep order forbids trading it for a larger move.

Two gates were re-specified after their baselines were measured, because as first written they
failed the *existing* board. The minimum-clearance gate initially treated the `NFC_5V_PA_PENDING`
stub feeding U9.8 as static; it is U9-local copper (its 0.30 mm-wide end lands on the pad even
though its centreline endpoint sits 0.15 mm off the pad edge) and translates with U9. And the NFC
gate was first written as a routable path from each RF pin to the NFC RESERVED boundary — at
baseline **no such path exists for any of the seven RF pins**, the matching network being unrouted,
so the metric became the geometric escape room the directive actually names: the gap from U9's east
pad face to the keepout boundary.

### At the new position

| | before | after |
|---|---|---|
| U9.30 escape | (0.2100 mm clearance) | **PASS, 0.2300 mm clearance** (margin 0.0300) |
| U9.31 escape | **blocked** | **PASS, 0.2126 mm clearance** (margin 0.0126) |
| U9.32 escape | PASS | **PASS, 0.6500 mm clearance** (margin 0.4500) |
| ordinary 0.60/0.30 via landing | — | **YES for all three** — nearest legal centres (25.550, 18.060) for U9.30/31, (21.410, 19.905) for U9.32 |
| U9 copper to `USB_D_MCU_N` via | — | **0.4290 mm** (pads), 1.6671 mm (EP vias) |
| U9 copper to `USB_D_MCU_P` via | — | **0.6305 mm** (pads), 1.8505 mm (EP vias) |
| U9 copper to `BMI270_INT1_STRAP` | — | **1.2250 mm** — measured through-via aware, not treated as an all-layer wall |
| U9 copper to NFC RESERVED | 0.8500 mm | **0.8500 mm** |
| EP via count | 6 | **6**, all still inside the exposed pad |
| minimum EP via to WROOM B.Cu pad | 0.275 mm | **0.275 mm** (three vias improved, none worsened) |
| forced capacitor moves | — | **none** |

The EP via pattern translated with U9 rather than shifting relative to it, so all six stay on the
pad and the three grounding structures — U9.20/21 → EP, U9.12 → EP, U9.16 → the pad-12 rail — remain
intact without redrawing. Only their y coordinates changed.

**NFC access.** The directive defines the metric as escape room *toward* NFC RESERVED, which is the
east face: **0.8500 mm before and after, unchanged**. Recorded honestly: the free room south of the
RFO1/RFO2 pins toward C50/C52 falls from 1.7750 mm to 1.7250 mm — by exactly the move. That face
does not point at NFC RESERVED, and no direction the CTO authorised avoids it (S and SW both carry a
southward component, and W fails the escape test because it pushes U9.31 *into* the `USB_D_MCU_N`
via). `NFC_5V_PA_PENDING` keeps its 5-island topology and both stubs stay landed on U9.8 and U9.10.
No `RF_DEFERRED_NFC` copper was created. No mechanical keepout, panel-height reservation, side or
rotation change.

### Local copper

Seven U9-local F.Cu tracks translated +0.050 mm in y with the part — five GND (the pad-20/21 → EP
bridges, the pad-12 → EP stub and the pad-16 → pad-12 rail) and the two `NFC_5V_PA_PENDING` stubs
into U9.8 and U9.10, whose far ends stay overlapped on the fixed rail at y = 25.400. The pad-8 stub
*had* to move: leaving it put U9.7 at 0.185 mm from it, below the 0.200 mm rule.

Nothing else was touched. **`SPI_B_SCK` U9.30, `SPI_B_MOSI` U9.31 and `SPI_B_MISO` remain
unrouted** — this pass proves the escapes exist, it does not consume them.

### Preservation

Object-by-object against `1968d95`: tracks **420 → 420** (7 changed, all U9-local), vias
**114 → 114** (6 changed, all EP), pads **776 → 776** (37 changed, all U9's own). **USB copper: 111
objects, 0 added, 0 removed** — pair, crossover, south corridor and both E4 handoffs byte-identical,
`USB_D_MCU_N`/`_P` still ratsnest 0, uncoupled budget still 25 mm. **SPI-B SCK/MOSI copper: 45
objects, 0 changed** — U1 escapes, mid-board trunks, E5 crossings and U8/U7 fanouts all intact.
`BMI270_INT1_STRAP`: 7 objects, 0 changed.

Island count is identical before and after for **all 25 U9 nets**, so nothing that was connected
came apart. Board ratsnest **430 → 430**; the only open U9 SPI items remain `SPI_B_SCK` ↔ U9.30 and
`SPI_B_MOSI` ↔ U9.31, with `SPI_B_MISO` staged. No new ratsnest item.

**Exactly one footprint moved.** 188 footprints, U9 the only change, F.Cu → F.Cu, rotation
unchanged. Schematic untouched — ERC **116 / 58 excluded / 58 live**. `.kicad_dru` unchanged.
Schematic parity **261 → 261**, delta 0. DRC **0 electrical errors**; warnings 244, unchanged.
Radio lanes x 61 (`SPI_B_MISO`), x 62–66 (SX1262), x 67–68 (CC1101) and x 69.100 (+3V3) are
untouched — U9 sits at x ≈ 24 and nothing this pass changed goes near them.

### Carried to the next pass

§7 requires each of the three escapes to be legal **individually**, and each is. It does not prove
all three can coexist, and they do not all have room to: U9.32 leaves westward with 0.65 mm of
clearance, but U9.30 and U9.31 both leave north-east through the same corridor between the
`USB_D_MCU_P` via and the U9.29/U9.30 pads, where the pinch is only wide enough for one 0.20 mm
track. **Establishing a simultaneous three-track solution is the first thing pass 3A-2 must do**,
before consuming any of them.

**U9 MOVE: PASS**
**WINNING SWEEP: S 0.050 mm**
**U9.30 ESCAPE: PASS** — 0.2300 mm clearance
**U9.31 ESCAPE: PASS** — 0.2126 mm clearance
**U9.32 ESCAPE: PASS** — 0.6500 mm clearance
**EP GROUNDING: PASS** — 6 vias, all on pad, min WROOM clearance 0.275 mm
**NFC FUTURE ACCESS: PASS** — 0.8500 mm, unchanged
**USB PRESERVED: YES**
**U9 SPI ESCAPE ARCHITECTURE: HARD-LOCKED**

## U9 to 0.250 mm South — three SPI-B escapes proven simultaneously, and two test-method defects fixed (2026-08-12)

U9 moves to **(24.500, 22.250)**. Total displacement from the original (24.500, 22.000): ΔX **0.000**,
ΔY **+0.250**, magnitude **0.250 mm**, direction **S**. Incremental from the committed (24.500,
22.050): **+0.200 mm S**. Rotation and side unchanged. This is the **first candidate in the binding
sweep order that survives an actual simultaneous three-track test**, so the sweep stopped there.

### The winning mechanism is a west bypass, not a wider gateway

The NE gateway at this position is **0.8438 mm** — still short of the 1.000 mm two 0.20 mm tracks
need, so it still carries **one** track. What the extra 0.200 mm of southward travel buys is a
**second, independent exit**: the gap between the `USB_D_MCU_N` via and U9.32's pad opens far enough
for **U9.31 (MOSI) to escape west**, leaving the NE gateway to U9.30 (SCK) alone, with U9.32 (MISO)
taking its own west lane further south. The CTO's calibration predicted the NE-widening mechanism
would first work near 0.45 mm; the west bypass arrives earlier, at 0.250 mm, which is exactly why
§6 forbade skipping the 0.10–0.40 rings.

### Two defects in the test method, both found and fixed here

**The escape search was seeding off the pad.** It seeded from any free cell within 0.45 mm of the pad
outline, so a route could "escape" starting from a point the pad itself cannot legally reach. Under
that loose test **0.15 SW screened LEGAL**; with seeding tightened to cells strictly *inside* the pad
it fails. Every escape in this pass starts on its pad and that is verified explicitly. This also
means the individual-escape margins quoted in the 0.050 mm placement entry were slightly optimistic —
the CTO had already retired that per-pad test as insufficient, and it is superseded here.

**The U9-local copper set was missing part of U9's own ground bridge.** The pad-16 → pad-12 GND rail
is three segments; the two verticals land on pads and were correctly treated as U9-local, but the
horizontal joining them, `(24.250, 25.200) → (26.250, 25.200)`, lands on neither and was treated as
fixed board copper. Southward candidates then appeared to drive U9's pads into their own ground rail
— **0.25 S and 0.30 S were both rejected on a 0.175 mm / 0.125 mm "clearance" against copper that
actually travels with the part.** Local copper is now grouped by contact rather than by endpoint
identity: a track joins the set when both ends touch in-set copper and nothing outside the set
touches it, which picks up the GND rail and correctly leaves the C55 `NFC_5V_PA_PENDING` rail behind.
That fix is what let 0.25 S win.

Without the first fix the sweep would have stopped too early on a route that cannot be built; without
the second it would have run past a legal position. Both were necessary.

### Sweep, in binding order

0.05 S is the committed position and was already proven a simultaneous FAIL, so it was not re-tested.

| mag | dir | ΔX | ΔY | U9 at | cheap | NE gw | verdict |
|---|---|---|---|---|---|---|---|
| 0.05 | SW | −0.0354 | +0.0354 | (24.4646, 22.0354) | PASS | 0.618 | ILLEGAL — NE gateway is the sole articulation for U9.30+U9.31, holds 1 track |
| 0.05 | W | −0.0500 | 0.0000 | (24.4500, 22.0000) | PASS | 0.580 | ILLEGAL — same |
| 0.10 | S | 0.0000 | +0.1000 | (24.5000, 22.1000) | PASS | 0.694 | ILLEGAL — same |
| 0.10 | SW | −0.0707 | +0.0707 | (24.4293, 22.0707) | PASS | 0.647 | ILLEGAL — same |
| 0.10 | W | −0.1000 | 0.0000 | (24.4000, 22.0000) | PASS | 0.575 | ILLEGAL — same |
| 0.15 | S | 0.0000 | +0.1500 | (24.5000, 22.1500) | PASS | 0.744 | ILLEGAL — same |
| 0.15 | SW | −0.1061 | +0.1061 | (24.3939, 22.1061) | PASS | 0.681 | ILLEGAL — same *(screened LEGAL under the defective off-pad seeding; fails on retest)* |
| 0.15 | W | −0.1500 | 0.0000 | (24.3500, 22.0000) | PASS | 0.575 | ILLEGAL — same |
| 0.20 | S | 0.0000 | +0.2000 | (24.5000, 22.2000) | PASS | 0.794 | ILLEGAL — same |
| 0.20 | SW | −0.1414 | +0.1414 | (24.3586, 22.1414) | PASS | 0.716 | ILLEGAL — same |
| 0.20 | W | −0.2000 | 0.0000 | (24.3000, 22.0000) | PASS | 0.575 | ILLEGAL — same |
| **0.25** | **S** | **0.0000** | **+0.2500** | **(24.5000, 22.2500)** | **PASS** | **0.844** | **LEGAL — three-track ensemble demonstrated** |

The "sole articulation" verdicts are a sound skip, not a guess: the NE gateway is walled off with a
virtual barrier and neither U9.30 nor U9.31 can then reach anything outside the local pocket, so with
the gateway narrower than two tracks need, no ordering can succeed. Pure-W candidates flatline at
0.575 mm because moving west carries U9.31 *toward* the `USB_D_MCU_N` via.

### The three simultaneous test routes

Laid in order U9.30 → U9.31 → U9.32, each becoming an obstacle for the next, at 0.005 mm resolution
and then re-verified analytically. **Nothing was written to the board — these are proof geometry only.**

| net | pad exit | corridor | polyline | exact min clearance | keeps |
|---|---|---|---|---|---|
| `SPI_B_SCK` U9.30 | north, then east | **NE gateway** | (23.750,19.600) → (23.760,19.495) → (23.820,19.380) → (23.915,19.295) → (24.040,19.250) → (25.775,19.250) → (25.775,17.595) | **0.34842** at (23.753,19.568), U9.29 | **0.2484 mm** |
| `SPI_B_MOSI` U9.31 | north-west, then west | **west bypass** | (23.215,19.600) → (23.155,19.405) → (23.065,19.325) → (22.955,19.285) → (20.600,19.285) | **0.30107** at (23.188,19.512), U9.32 pad | **0.2011 mm** |
| `SPI_B_MISO` U9.32 | west | **west, southern lane** | (22.600,19.865) → (20.600,19.865) | **0.48500** at (22.600,19.865), U9.1 | **0.3850 mm** |

Every route starts **on** its pad. Minimum inter-track centreline separation **0.5350 mm** against the
0.400 mm two-track requirement (U9.30↔U9.31 0.5350, U9.30↔U9.32 1.1801, U9.31↔U9.32 0.5800).

**`SPI_B_MOSI` has 1.07 µm of margin.** 0.20107 mm against a 0.200 mm rule is legal and the sweep
order forbids trading it for a bigger move, but the routing pass must lay that escape on exactly this
corridor — it cannot be nudged, and it is bounded by U9.32's own pad, so MISO's escape must also stay
where it is.

### Gates at the winning position

| | before (0.050 S) | after (0.250 S) |
|---|---|---|
| NE gateway | 0.6811 | **0.8438 mm** (still 1 track) |
| U9 pads → `USB_D_MCU_N` via | 0.4290 | **0.6281 mm** |
| U9 pads → `USB_D_MCU_P` via | 0.6305 | **0.8295 mm** |
| U9 copper → `BMI270_INT1_STRAP` | 1.2250 | **1.4250 mm** |
| U9 copper → NFC RESERVED | 0.8500 | **0.8500 mm** |
| NFC east matching access | 0.8500 | **0.8500 mm — unchanged** |
| NFC south room | 1.7250 | 1.5250 mm |
| EP vias | 6 | **6**, all on the exposed pad |
| min EP via → WROOM B.Cu pad | 0.275 | **0.275 mm** (two improved to 0.289) |
| forced capacitor moves | — | **none** |
| min U9 copper → fixed copper | — | **0.3250 mm** |

All three grounding bridges — U9.20/21 → EP, U9.12 → EP, U9.16 → the pad-12 rail — travel intact with
the part, the rail horizontal included this time. No capacitor moved; the largest distance change in
the thirteen-capacitor set is C52 at −0.189 mm. C55 improves to **4.2262 mm** (U9.10) and **4.6250 mm**
(U9.8) centre-to-centre, both inside the 5 mm band.

### Preservation

Against `d4a083d`: tracks **420 → 420** (8 changed, all U9-local), vias **114 → 114** (6 changed, all
EP), pads **776 → 776** (37 changed, U9's own). **USB copper 111 objects, 0 added, 0 removed**;
`USB_D_MCU_N`/`_P` ratsnest 0; uncoupled 22.1321 / 25.000 and skew 1.1011 / 2.000 untouched.
**SPI-B copper 46 objects, 0 changed** — SCK and MOSI keep their U1 escapes, mid-board trunks, E5
crossings at x 59 / x 60 and U8/U7 fanouts; MISO stays staged at x 61; x 62–66, x 67–68 and x 69.100
untouched. `BMI270_INT1_STRAP` unchanged. **Island count identical before and after for all 25 U9
nets.** 188 footprints, U9 the only one moved.

DRC **0 electrical errors**, board ratsnest **430 → 430**, schematic parity **261, delta 0**, ERC
**116 / 58 excluded / 58 live**. Schematic and `.kicad_dru` untouched.

DRC warnings rise 244 → 250: six new `silk_over_copper`, all of them C50's and C52's reference-designator
text now clipped by U9's south pads. Cosmetic silkscreen only, no electrical content; the board already
carried 132 of these. Worth a silk-text nudge at pre-fab tidy-up, not now.

U9.30, U9.31 and U9.32 remain **unrouted** — this pass proves the three escapes coexist, it does not
consume them.

**U9 REVISED MOVE: PASS**
**WINNING SWEEP: 0.25 ring, S**
**SIMULTANEOUS U9.30/U9.31: PASS**
**U9.32 COEXISTENCE: PASS**
**ALL THREE SPI ESCAPES: PASS**
**EP GROUNDING: PASS**
**NFC FUTURE ACCESS: PASS**
**USB PRESERVED: YES**
**U9 SIMULTANEOUS ESCAPE: HARD-LOCKED**

## SPI-B shared bus closed — SCK, MOSI and MISO all reach U1, U9, U8 and U7 (2026-08-12)

All three shared SPI-B nets are **complete**. Each is a single copper island containing all four
endpoints, board ratsnest **430 → 424**, DRC **0 electrical errors**.

| net | island | total copper | tracks | vias |
|---|---|---|---|---|
| `SPI_B_SCK` | U1.4, U9.30, U8.18, U7.18 | 210.599 mm | 27 | 5 |
| `SPI_B_MOSI` | U1.5, U9.31, U8.17, U7.17 | 197.238 mm | 25 | 6 |
| `SPI_B_MISO` | U1.6, U9.32, U8.16, U7.16 | 195.522 mm | 23 | 8 |

### The three U9 escapes were laid exactly as proven

The placement audit's coordinates were used verbatim, extended only into the pad so each track
starts on copper rather than on the pad boundary. Nothing was straightened or re-optimised.

| net | corridor | polyline (local escape) | exact min clearance |
|---|---|---|---|
| SCK U9.30 | NE gateway | (23.750,20.000) → (23.750,19.600) → (23.760,19.495) → (23.820,19.380) → (23.915,19.295) → (24.040,19.250) → (25.775,19.250) | **0.34842** (U9.29) |
| MOSI U9.31 | west bypass | (23.215,20.000) → (23.215,19.600) → (23.155,19.405) → (23.065,19.325) → (22.955,19.285) → (20.600,19.285) | **0.30107** (U9.32 pad) |
| MISO U9.32 | west lane | (22.750,20.000) → (22.750,19.865) → (21.225,19.865) | **0.35000** (U9.31 pad) |

**MISO's west run was stopped at x = 21.225 rather than the proven x = 20.600.** That is a strict
truncation of the proven path, never a move upward toward MOSI: MOSI needs to turn south at x =
20.600 to reach its layer transition, and MISO's own southward lane has to clear both MOSI's turn
and its via while staying clear of the `NFC_5V_PA_PENDING` stub at x = 21.700 — which pins MISO's
lane into the window x ∈ [21.200, 21.250]. Stopping short only increases MISO-to-MOSI clearance.

### Ensemble clearance audit — the three escapes measured together, not just by DRC

| pair | measured |
|---|---|
| SCK ↔ MOSI | **0.3350 mm** |
| SCK ↔ MISO | **0.8000 mm** |
| MOSI ↔ MISO | **0.2250 mm** |
| SCK ↔ USB copper | **0.3761 mm** (`USB_D_MCU_P` via) |
| MOSI ↔ USB copper | **0.2142 mm** (`USB_D_MCU_N` via) |
| MISO ↔ USB copper | **0.5500 mm** (`USB_D_MCU_N` track) |
| MOSI ↔ U9.32 pad | **0.2011 mm** |

Every applicable clearance is at or above the 0.200 mm rule. MOSI's 0.2011 mm to U9.32 is the
predicted critical value and it landed exactly where the placement audit said it would.

### How each net was completed

**SCK** — one F.Cu branch, no new via: out through the NE gateway, north at x = 25.775 between C53.2
and C54, west at y = 16.200 above R29/C53 and below U3 (which is B.Cu, so F.Cu is clear there), then
south at x = 11.300 onto the existing `SPI_B_SCK` via at (11.300, 19.100). 23.056 mm added.

**MOSI** — the west bypass to (20.600, 19.285), south to (20.600, 20.400), one via, then B.Cu west at
y = 20.400 through U1's belly to (13.400, 20.400) and north onto the existing MOSI via at
(13.400, 19.500). 12.411 mm added. The southward leg had to sit at x = 20.600: C46 forbids anything
west of 20.525 and the `BMI270_INT1_STRAP` via blocks x 19.200–20.400 at that latitude.

**MISO** — the full net, 163.522 mm and 8 vias, following the SCK/MOSI architecture:

- U9.32 west, then south at x = 21.225, then west at y = 21.100 between C18 and C46 to a tee via at
  (19.000, 21.100)
- U1.6 out on B.Cu to a via at (14.700, 19.300), then F.Cu south and east into the same tee
- In2 descent at **x = 19.000**, the one free lane between `I2C_SCL_INT` at x = 18.2 and the
  `BMI270_INT1_STRAP` In2 at x = 19.8 — 0.800 mm to each — down to y = 80.300
- F.Cu hop (19.000, 80.300) → (19.000, 86.500), crossing the `DISP_RST_N` In2 barrier at y = 82.800
  **and** SCK's own In2 east lane at y = 84.200
- In2 east at **y = 86.500** to x = 52.400, north to y = 85.200, east to x = 58.300
- B.Cu hop (58.300, 85.200) → (61.000, 86.000) over SCK's and MOSI's In2 crossings
- the staged **x = 61.000** C-E crossing, consumed
- In2 radio trunk at x = 60.850 with a B.Cu tee into U8.16 and a branch to a via at (58.420, 151.800)
  and a B.Cu stub into U7.16

Three constraints shaped the eastern half and are worth recording. The band between `DISP_RST_N`
(y = 82.8) and the staged crossings (y = 85.0) already carries MOSI at 83.500 and SCK at 84.200 with
no room for a third lane — 83.20 is the floor and 0.40 separation cannot be met — so MISO runs
*south* of both at y = 86.500, where In2 is clear from x = 15 to 52.97. It steps north to y = 85.200
at x = 52.400 because the USB In2 verticals at x = 53.4 / 53.85 / 56.0 start at y = 86.000 and are
absent above it. And it crosses SCK's and MOSI's crossings on B.Cu because on In2 they are an
unbroken wall from y = 85 to y = 117.

Two via sites had to move during the audit: (19.000, 82.000) sits on the `SPI_A_MISO` B.Cu run, and
the 1.0 mm window between that and `SD_CS_N` at y = 81.000 is too narrow for a 0.60 mm via at
0.200 mm clearance, so the transition moved north of both to y = 80.300. And (19.000, 86.200) fell
0.30 mm from the `SPI_A_SCK` B.Cu at y = 85.800, so the landing moved to y = 86.500.

**The x = 61.000 crossing is fully consumed.** The B.Cu hop lands at y = 86.000 because TP7's F.Cu
pad (x 60.0–61.0, y 84.0–85.0) forbids a via any closer to the crossing's north end, so a 1.0 mm
In2 segment carries the net the rest of the way to (61.000, 85.000). Without it the crossing's north
end stays a dangling stub; with it, DRC's `track_dangling` count drops 11 → 10 and no SPI-B copper
is left free.

### Preservation

Against `44a7d1d`: tracks **420 → 459**, vias **114 → 123**, **0 removed**, every added object on
`/SPI_B_SCK`, `/SPI_B_MOSI` or `/SPI_B_MISO`. Pads 776, unchanged. **USB copper 111 objects, 0 added,
0 removed** — `USB_D_MCU_N`/`_P` still ratsnest 0, uncoupled 22.1321 / 25.000 and skew 1.1011 / 2.000
untouched. `BMI270_INT1_STRAP` 7 objects unchanged. GND copper 26 objects unchanged, U9's six EP vias
and all three grounding bridges intact. U9 still at (24.500, 22.250), F.Cu, rotation 0; 188
footprints, none moved this pass. No capacitor moved. No `NFC_DEFERRED` copper.

RF and E5: **0 new vias in the 915 band, 0 in the 433 band, 0 new B.Cu crossing either band**; the
three E5 crossings at x 59 / 60 / 61 are consumed in place and none was moved, duplicated or resized.
Nearest approach of new copper to the reserved lanes x 62–69.1 is **0.800 mm**, so `SX1262_CS_N`,
`SX1262_DIO1`, `SX1262_BUSY`, `SX1262_RST_N`, `SX1262_RXEN`, `CC1101_CS_N`, `CC1101_GDO0` and +3V3
keep their corridors.

DRC **0 electrical errors**; warnings 250 → **249** (the consumed MISO stub). Board ratsnest
**430 → 424**. ERC **116 / 58 excluded / 58 live**. Schematic parity **261, delta 0**. Schematic and
`.kicad_dru` untouched. The six cosmetic `silk_over_copper` warnings from the U9 move are still
present and still logged for pre-fab tidy-up, as instructed.

Staged infrastructure remaining: `BTN_HOME_N`, SX1262 ×5, CC1101 ×2, +3V3, and the pre-existing
`BQ25185_SYS`, `LED_K` and `NFC_5V_PA_PENDING` ends. No orphan copper.

**SPI_B_SCK: PASS**
**SPI_B_MOSI: PASS**
**SPI_B_MISO: PASS**
**SPI-B SHARED BUS: HARD-LOCKED COMPLETE**
**U9 SIMULTANEOUS ESCAPES: PASS**
**USB PRESERVED: YES**

## SX1262 control routing pass 3A-1 — CS_N and BUSY closed, DIO1 deferred (2026-08-12)

`SX1262_CS_N` and `SX1262_BUSY` are **complete**; each is a single copper island holding every
endpoint. Board ratsnest **424 → 419**, DRC **0 electrical errors**. `SX1262_DIO1` is deliberately
left unrouted — it has no legal escape from U1 and needs a placement ruling, not a router.

| net | island | length | tracks | vias | layers |
|---|---|---|---|---|---|
| `SX1262_CS_N` | U1.10, U8.19, R27.2 | 175.930 mm | 17 | 2 | F.Cu 1, In2 12, B.Cu 4 |
| `SX1262_BUSY` | U1.12, U8.14 | 195.126 mm | 19 | 4 | In2 12, B.Cu 7 |

### The U1 belly corridor carries exactly two tracks, and that is the whole story

Pass 3A reported the corridor under U1's north pad row as one track wide. That was wrong: it
conflated a 0.600 mm *centre window* with a 0.600 mm *corridor*. The corridor is the 1.200 mm band
between the pad row (y = 18.000) and the `BMI270_INT1_STRAP` B.Cu track (y = 19.200), and it holds
**two** 0.20 mm tracks, at y = **18.300** and y = **18.700**, every clearance in the stack landing on
exactly 0.2000 mm. A third at 19.100 fails against the strap track, which is immutable.

Because every escape is a drop at the pad's own x followed by a westward run, and the pads order
CS_N (18.920) < DIO1 (20.190) < BUSY (21.460) west to east, **depth must increase eastward** or a
drop crosses a shallower lane. BUSY, the easternmost, is capped at y ≤ 18.700 by the strap. Two
distinct depths exist above that cap, so **only two of the three nets can leave U1 at all**. This is
geometry, not effort: it was proved four independent ways and it is why DIO1 is deferred.

CS_N therefore takes the shallow western lane and BUSY the deep eastern one:

| net | drop | corridor | transition via | via margin |
|---|---|---|---|---|
| CS_N | x = 18.920 | y = **18.300** | **(15.800, 19.500)** | 0.500 mm |
| BUSY | x = 21.460 | y = **18.700** | **(16.600, 19.500)** | 0.500 mm |

Both vias sit in pocket P2 (x 15.400–16.900, y 19.200–19.800), the only belly pocket that holds two
0.60 mm vias. They are 0.800 mm apart — exactly the minimum — and P2 is now fully consumed.

### Two different corridors east, because the I2C fan-out only has one door

The two nets do **not** run parallel. The `I2C_SDA_INT`/`I2C_SCL_INT` fan-out forms a closed barrier
from x = 17.5 to x = 33.8 between y = 9.4 and y = 11.6 (horizontals at y = 10.875, 11.350 and 11.600,
closed at its east end by an In2 via and stub at x = 33.800). The only opening is north of that
stub, a window of y between 8.80 and 9.00 — **0.200 mm, one track**. So:

**BUSY takes the far-north corridor.** North on In2 at x = 16.600 to y = 10.000, east to x = 32.900,
a jog to y = **8.750** across x 33.300 → 34.600 to clear the `I2C_SCL_INT` via at (33.800, 9.400) by
0.350 mm, then east at y = 10.000 to x = 61.000 and straight south to y = 74.500. The jog keeps
0.150 mm outside HEADER RESERVED (x 18.5–55.5, y 0–8.5) and does not intersect it.

**CS_N takes the southern route.** West on In2 at y = 18.500 to x = 12.000 — the free channel between
`SPI_B_SCK`'s In2 descent at x = 11.300 and `SPI_B_MOSI`'s at x = 13.000 — then straight south to
y = 82.250, the only latitude clearing both the `SPI_A_MISO` via row at y = 81.500 and `DISP_RST_N`
at y = 82.800. It steps north to y = 80.700 at x = 44.500, threading the 0.250 mm window between the
`DISP_BL_CTL` via (43.800, 81.300) and the `DISP_RST_N` via (45.250, 81.400), then runs east at
y = 80.700 — north of the J4 battery-connector pads, which wall x 57.1–60.9 on every layer between
y 81.625 and 83.375.

### Getting past U14 and BQ25185

Both nets have to cross the two In2 walls at y = 76.0 (`I2C_SCL_INT`) and y = 77.0 (`I2C_SDA_INT`),
which span x 29.9 → 66.9. CS_N does not — at x = 12.000 both are absent. BUSY hops to B.Cu, and the
transition had to move west to **x = 60.200** because the `BQ25185_SYS` F.Cu rail at x = 61.200 is
0.60 mm wide and forbids any via within 0.800 mm for y 32.5 → 75.0. From there BUSY runs B.Cu south
at x = 61.000 (0.300 mm clear of J4.2) to y = 83.000 and east to x = 64.000, where it drops to In2 —
0.781 mm clear of TP6.1, whose F.Cu pad occupies x 64.000–65.000, y 84.000–85.000 and blocks the
obvious via site one millimetre north.

### E5 crossings and the U8 side

The staged In2 crossings at **x = 62.000** (CS_N) and **x = 64.000** (BUSY), y 85.000 → 117.000, are
consumed exactly in place — not moved, resized, duplicated or swapped. `SX1262_DIO1`'s x = 63.000
crossing is untouched between them and still has 0.700 mm of clearance to the nearest new copper.

At U8 both nets follow the pattern SPI-B established: In2 south to the pad latitude, a short west
step to x = 61.700, a via, then B.Cu west into the pad. `R27` is confirmed from the netlist as a
pull-up (R27.1 = +3V3, R27.2 = `SX1262_CS_N`), so CS_N **tees** to it on F.Cu from the same via —
1.286 mm clear — and is not routed through it in series.

### Measured clearances

| measurement | value |
|---|---|
| `SX1262_CS_N` minimum, whole net | **0.20000 mm** (to `SX1262_BUSY` B.Cu in the belly) |
| `SX1262_BUSY` minimum, whole net | **0.20000 mm** (to `SX1262_CS_N` B.Cu in the belly) |
| CS_N to BUSY, track to track | **0.20000 mm** |
| CS_N to BUSY, via to via | **0.20000 mm** (the P2 pair, 0.800 mm centres) |
| tightest clearance outside the belly | **0.24077 mm** (BUSY's jog to the `I2C_SCL_INT` via) |

Every applicable clearance is at or above the 0.200 mm rule. Both nets are netclass `E5_CROSSING`
(0.20 track, 0.20 clearance, 0.60/0.30 via), which the DRU authorises inside the E5 corridors.

### DIO1 access after the pass

Re-audited on the routed board. What survives: pocket **P1 (x 18.800–19.000, y = 19.300) is still a
legal via site** at 0.200 mm; all three descent lanes are still clear (**x = 24.900 jogged 0.400 mm,
x = 25.900 0.400 mm, x = 26.400 0.500 mm**); the x = 63.000 crossing, the U8.13 B.Cu escape
(0.820 mm) and its via site at (61.700, 134.730) (0.450 mm) are all intact.

What is gone: **P2 is fully consumed** (0 legal via sites left in the belly between x 13.0 and 19.4)
and both corridor latitudes are occupied. DIO1 can still drop from U1.11 to y = 18.300 at
x 19.740–20.640 with 0.200 mm, but that stub can only run east into the dead end closed by
`USB_D_MCU_N`'s B.Cu stub at x = 22.605.

**Nothing DIO1 could have used was taken.** DIO1 was already unroutable before this pass — reaching
P2 required a corridor latitude, and it could never hold both. Its solution space is unchanged: it
still needs a ruling on the `BMI270_INT1_STRAP` via or track, or a U1 move. Failing that, the
electrical fallback stands — DIO1 is the SX1262's IRQ line and can be substituted by polling
`GetIrqStatus()` over SPI, at a cost in latency and idle power. `BUSY` is a pin-only handshake and
cannot be polled, which is why it, not DIO1, was routed.

### Preservation

Against `7010eb8`: tracks **459 → 493**, vias **123 → 129**, **0 objects removed**, all 40 additions
on `/SX1262_CS_N` or `/SX1262_BUSY`. Pads 776 and every pad coordinate identical, so **188
footprints, 0 moved**. SPI-B, USB, `BMI270_INT1_STRAP`, I2C, display/control, power and U9 grounding
all still single islands with unchanged object counts.

RF and E5: **0 new vias in the 915 band, 0 in the 433 band, 0 new B.Cu transit of either band**, no
new E5 lanes, NFC RESERVED / HEADER RESERVED / WROOM ANTENNA all clear of new copper, no
`NFC_DEFERRED` copper.

DRC **0 electrical errors**; warnings 249 → **247**. Board ratsnest **424 → 419**. ERC **116 / 58
excluded / 58 live**, unchanged. Schematic parity **261, delta 0**. Schematic and `.kicad_dru`
untouched. The six cosmetic `silk_over_copper` warnings from the U9 move remain, still logged for
pre-fab tidy-up.

**SX1262_CS_N: PASS**
**SX1262_BUSY: PASS**
**SX1262 TWO-NET PASS: PASS**
**SX1262_DIO1 ACCESS PRESERVED: YES**

## SX1262_DIO1 moved to IO38; NFC_IRQ takes IO18 — pin swap only, zero copper moved (2026-08-13)

`SX1262_DIO1` now leaves the MCU on **U1.31 / IO38** instead of U1.11 / IO18. `NFC_IRQ` takes
U1.11 / IO18 in exchange. **No copper moved: 0 objects added, 0 removed, 493 tracks and 129 vias
before and after.** Only two pad net assignments changed.

### Why a pin swap was the answer

Four successive placement-preserving analyses proved DIO1 could not escape U1.11:

- the U1 belly corridor between the north pad row (y 18.000) and the `BMI270_INT1_STRAP` B.Cu run
  (y 19.200) is 1.200 mm and holds exactly **two** 0.20 mm tracks, both consumed by `SX1262_CS_N`
  and `SX1262_BUSY`;
- `USB_D_MCU_P` F.Cu (y 17.950–18.200) and `USB_D_MCU_N` F.Cu (y 18.400–18.650) sweep the whole
  local x-range, so any through-via needs y ≥ 19.150 — south of both committed lanes;
- deleting the **entire** strap net still left U1.11 with **0 reachable via sites** and P1
  unreachable;
- the proposed four-depth stack (CS_N 18.300 / DIO1 18.700 / BUSY 19.100 / STRAP 19.500) is
  geometrically legal as a stack, but BUSY at 19.100 **destroys P1** and DIO1 still ends with
  0 reachable via sites.

U1.11's trap is a property of the **pad**, not the net, so swapping DIO1 with CS_N or BUSY would
only strand a more critical signal. A flood test of candidate host pads settled it:

| pad | GPIO | reachable B.Cu cells | legal via sites | best margin |
|---|---|---|---|---|
| **31** | **IO38** | 278,225 | **31,369** | **1.1000 mm** |
| 26 | IO45 | 86,549 | 35,225 | 0.7333 mm — but VDD_SPI strapping pin |
| 9 | IO16 | 51,459 | 296 | 0.2489 mm |
| 16 | IO46 | 144,604 | **0** | trapped as well, by `DISP_CS_N` B.Cu and U9's via field |
| 11 | IO18 | 30,160 | **0** | the trap |

IO38 is a plain GPIO with no strapping role and 1.100 mm of via margin on the south row, facing
open board on the correct side for the x = 63.000 E5 lane. IO45 and IO46 were rejected: both are
strapping pins the pin map reserves as test pads, and IO46's pad is trapped anyway.

### What changed

Two hierarchical labels in `02_mcu_core.kicad_sch`, both already `(shape input)`, swapped in place:

| position | drives U1 pin | was | now |
|---|---|---|---|
| (149.86, 81.28) | pad 11 / IO18 | `SX1262_DIO1` | **`NFC_IRQ`** |
| (149.86, 99.06) | pad 31 / IO38 | `NFC_IRQ` | **`SX1262_DIO1`** |

and the two matching pad net assignments in the board:

```
U1.11  /SX1262_DIO1 -> /NFC_IRQ
U1.31  /NFC_IRQ     -> /SX1262_DIO1
```

Nothing else. No resistor, test point or topology change; no component moved; no other pin touched.
The schematic file length is byte-for-byte unchanged (78,833 bytes) and so is the board's
(1,087,570 bytes) — the swapped strings are the same total length.

### Lane and pull-up semantics are net-owned, so they did not move

`SX1262_CS_N` keeps **E5 x = 62.000 → U8.19** and its **R27 pull-up** (R27.1 = +3V3,
R27.2 = CS_N) — still one island over R27.2, U1.10, U8.19. `SX1262_BUSY` keeps
**x = 64.000 → U8.14**, still one island over U1.12 and U8.14. `SX1262_DIO1` keeps
**x = 63.000 → U8.13**; only its MCU-side endpoint moved. No crossing was swapped, moved,
resized or duplicated.

### NFC_IRQ — INTENTIONAL, NOT CONNECTED IN BETA

`NFC_IRQ` now lands on U1.11, which has no legal escape. **This is deliberate and accepted.** The
hardware interrupt is deferred to the NFC-enablement respin. Beta NFC scope is **polling-based
digital bring-up only**, and the ST25R3916 interrupt-status registers must be polled instead.

**Beta bring-up must verify ST25R3916 interrupt-status polling** — without the IRQ line there is no
edge notification, so the driver has to poll the interrupt-status registers and the latency and CPU
cost of that path need measuring on real hardware before the respin scope is fixed.

This is the second entry in the intentional-unrouted ledger, alongside the C21/C22 DNP data pins.
It is **not** a routing defect and must not be counted as one: board ratsnest stays at **419**, of
which 1 item is `NFC_IRQ` (U1.11 ↔ U9.27) and 2 are `SX1262_DIO1` (U1.31 ↔ crossing ↔ U8.13),
the latter to be closed by the DIO1 routing pass.

### Firmware

`Firmware/src/config.h` is an explicit placeholder — its header says every pin "must be reconciled
with the final PCB pinout once the board is routed" and it currently carries `RADIO_DIO1 38`,
`RADIO_NSS 8`, `RADIO_BUSY 39`, `I2C_SDA 17`, none of which match the schematic. So this swap costs
nothing incremental in firmware. Recorded as TODO: **`RADIO_DIO1` → GPIO38**, and the Beta NFC path
must poll ST25R3916 interrupt status. Full Beta pin-map reconciliation remains outstanding.

### Preservation

Tracks **493 → 493**, vias **129 → 129**, **0 removed, 0 added**, pads 776 with every coordinate
identical, **188 footprints, 0 moved**. `USB_D_MCU_P` 24, `USB_D_MCU_N` 20, `SPI_B_SCK` 32,
`SPI_B_MOSI` 31, `SPI_B_MISO` 31, `SX1262_CS_N` 19, `SX1262_BUSY` 23, `BMI270_INT1_STRAP` 7,
`I2C_SDA_INT` 32, `I2C_SCL_INT` 36 — every count unchanged. U9 grounding, RF rules, `.kicad_dru`
and `.kicad_pro` untouched.

DRC **0 electrical errors**, 247 warnings, board ratsnest **419** — all identical to `e12f49d`.
Schematic parity **261, delta 0**, with **zero** parity entries mentioning either swapped net, which
is the proof that board and schematic agree on the new mapping. ERC **116 total / 58 excluded /
58 live**, unchanged.

**PIN SWAP: PASS**
**NFC_IRQ ZERO-COPPER BEFORE SWAP: VERIFIED (0 tracks, 0 vias, 0 zones)**
**PCB COPPER PRESERVED: YES**
**READY FOR DIO1 ROUTING FROM IO38: YES**

## SX1262_DIO1 routed from IO38 — the SX1262 U1-origin control block is complete (2026-08-13)

`SX1262_DIO1` is **closed**: one copper island over **U1.31** and **U8.13**, ratsnest 0, DRC 0
electrical errors. This is the third and last U1-origin SX1262 control. Board ratsnest **419 → 417**.

| metric | value |
|---|---|
| length | **148.407 mm** |
| tracks | 14 (13 new + the staged x63 crossing) |
| vias | 5 |
| layers | B.Cu 7, In2 5, F.Cu 2 |
| minimum clearance, whole net | **0.30000 mm copper** (0.40000 centreline) |

### The pin swap paid for itself immediately

From U1.11 the net had **zero** reachable via sites under any placement-preserving change. From
U1.31 it routed on the first attempt with **0.300 mm of copper clearance everywhere** — half again
the 0.200 mm the CS_N and BUSY escapes had to accept, and with no zero-margin geometry anywhere in
the net. The south row faces open board, so there is no belly corridor to fight over.

### Route

```
B.Cu  (19.200, 35.000) → (19.200, 38.600)     drop out of U1.31, west of U1.30
B.Cu  (19.200, 38.600) → (23.400, 38.600)     east under the U1 south row
B.Cu  (23.400, 38.600) → (23.400, 39.000)
via   (23.400, 39.000)   B.Cu → F.Cu                     0.300 mm
F.Cu  (23.400, 39.000) → (28.000, 39.000)     hop the SD_CS_N / SPI_A / DISP_CS_N wall
via   (28.000, 39.000)   F.Cu → B.Cu                     0.525 mm
B.Cu  (28.000, 39.000) → (59.500, 39.000)     east, south of NFC RESERVED
B.Cu  (59.500, 39.000) → (59.500, 78.000)     descent; crosses the I2C In2 walls on B.Cu
via   (59.500, 78.000)   B.Cu → F.Cu                     0.450 mm
F.Cu  (59.500, 78.000) → (63.400, 78.000)     past BAT_PROTECTED_P and BUSY's B.Cu
via   (63.400, 78.000)   F.Cu → In2                      0.400 mm
In2   (63.400, 78.000) → (63.400, 82.000) → (63.000, 83.000) → (63.000, 85.000)
      [staged crossing (63.000, 85.000) → (63.000, 117.000) — CONSUMED]
In2   (63.000, 117.000) → (63.000, 132.500)
via   (63.000, 132.500)  In2 → B.Cu                      0.560 mm
B.Cu  (63.000, 132.500) → (63.000, 134.730)   passes south of BUSY's U8 approach
B.Cu  (63.000, 134.730) → (58.600, 134.730)   into U8.13
```

### Three walls, three different answers

**The SPI_A / DISP_CS_N wall (x 23.7 → 27.4).** `SD_CS_N` (24.1), `SPI_A_MISO` (24.75),
`SPI_A_SCK` (26.675) and `SPI_A_MOSI` (27.075) form an unbroken B.Cu palisade, and `DISP_CS_N`'s In2
vertical at x 26.9–27.1 runs y 18.735 → 76.100 behind it, so **both** B.Cu and In2 are blocked. F.Cu
is wide open there (0.305 mm at y = 39, and 0.95–3.19 mm further south), so a 4.6 mm F.Cu hop between
two vias clears all five obstacles at once.

**NFC RESERVED.** The keepout ends at y = 35, so everything from y ≈ 36 southward is free to cross
x 28 → 54. In2 is clear from x 27.4 to 60.6 across the whole band y 35.6 → 50.0 (0.310 mm), and B.Cu
from 27.5 to 66.0. B.Cu was chosen for the long eastward run because it also carries the descent
without another transition.

**The I2C In2 walls at y = 76.0 and y = 77.0.** `I2C_SCL_INT` (x 31.3–66.9) and `I2C_SDA_INT`
(x 29.9–65.59) block In2 across the entire descent corridor. B.Cu at x = 59.500 is clear from
y = 14.5 to 81.3, so the descent simply stays on B.Cu straight through both.

The last obstacle is the `BAT_PROTECTED_P` cluster: a 0.80 mm via at (62.200, 80.400), a B.Cu
vertical at x 61.9–62.5 (y 69.3–80.7) and a B.Cu horizontal at y 78.7–79.3 (x 61.9–69.3), with
`SX1262_BUSY`'s own B.Cu descent at x = 61.000 immediately west. F.Cu is the only clear layer at that
latitude, so the crossing runs F.Cu at y = 78.000 and drops to In2 at **x = 63.400** rather than
63.000 — that 0.400 mm eastward offset lifts the via's clearance from 0.200 mm to **0.400 mm**, and
a short In2 jog brings the net back onto the x = 63.000 lane before y = 84.

### U8 side

`SX1262_BUSY` already occupies In2 at x = 64.000 down to y = 133.460 and turns west there, directly
across DIO1's path to U8.13 at y = 134.730. Rather than fight it, DIO1 stops its In2 descent at
y = 132.500, drops to B.Cu, and passes **beneath** BUSY's approach — 1.000 mm clear of BUSY's via at
(61.700, 133.460) and 0.860 mm from its In2 horizontal.

### Clearances

| pair | measured |
|---|---|
| DIO1 whole net, minimum | **0.30000 mm** (`SX1262_BUSY` via at (60.200, 74.500)) |
| DIO1 ↔ `SX1262_BUSY` | **0.30000 mm** |
| DIO1 ↔ `SX1262_CS_N` | **0.80000 mm** |
| DIO1 ↔ `USB_D_MCU_P` | **5.43169 mm** |
| DIO1 ↔ `USB_D_MCU_N` | **5.91793 mm** |
| tightest via | 0.300 mm at (23.400, 39.000) to `WAKE_INT_N` In2 |

### E5 and RF

The **x = 63.000 crossing is consumed** — it no longer appears in the free-endpoint audit. CS_N keeps
x = 62.000, BUSY keeps x = 64.000; nothing was moved, resized, duplicated or swapped, and no new
crossing was created. **0 new vias in the 915 band, 0 in the 433 band, 0 new B.Cu transit of either
band.** NFC RESERVED, HEADER RESERVED and WROOM ANTENNA all clear of new copper.

Staged lanes still awaiting later nets: `SX1262_RST_N` (x 65), `SX1262_RXEN` (x 66), `CC1101_CS_N`
(x 67), `CC1101_GDO0` (x 68), `BTN_HOME_N` (x 13.8), +3V3 (x 69.1), plus the pre-existing
`BQ25185_SYS`, `LED_K` and `NFC_5V_PA_PENDING` ends. 17 free endpoints, none belonging to SPI-B,
USB or any SX1262 control.

### NFC_IRQ

Still **0 tracks, 0 vias, 0 zones** and still 2 islands (U1.11, U9.27). Its single ratsnest item is
the documented intentional-unrouted ledger entry — **INTENTIONAL, NOT CONNECTED IN BETA**, hardware
IRQ deferred to the NFC-enablement respin, Beta NFC scope polling-only. Board ratsnest 417 is
therefore the correct end state, not a defect.

### Preservation

Against `24b204e`: tracks **493 → 506**, vias **129 → 134**, **0 objects removed**, all 18 additions
on `/SX1262_DIO1`. Pads 776 with every coordinate identical and **0 pad net assignments changed**, so
**188 footprints, 0 moved**. `USB_D_MCU_P` 24, `USB_D_MCU_N` 20, `SPI_B_SCK` 32, `SPI_B_MOSI` 31,
`SPI_B_MISO` 31, `SX1262_CS_N` 19, `SX1262_BUSY` 23, `BMI270_INT1_STRAP` 7, `I2C_SDA_INT` 32,
`I2C_SCL_INT` 36, `NFC_IRQ` 0 — every count unchanged. Schematic, `.kicad_dru` and `.kicad_pro`
untouched.

DRC **0 electrical errors**; warnings 247 → **246**. Board ratsnest **419 → 417**. ERC
**116 / 58 excluded / 58 live**, unchanged. Schematic parity **261, delta 0**.

**SX1262_DIO1: PASS**
**SX1262 U1-ORIGIN CONTROL BLOCK: HARD-LOCKED COMPLETE**

## SX1262_RXEN routed U3.19 → U8.6; SX1262_RST_N deferred (2026-08-13)

`SX1262_RXEN` is **closed**: one island over **U3.19**, **R74.1** and **U8.6**, ratsnest 0, DRC 0
electrical errors. Board ratsnest **417 → 414**. `SX1262_RST_N` was **not** closed in this pass — see
below. This was a two-net pass; only one net is committed, per the pass rule that the first net must
not be compromised to force both into one commit.

| metric | value |
|---|---|
| length | **197.227 mm** |
| tracks | 18 |
| vias | 4 |
| layers | B.Cu 12, In2 5, F.Cu 1 |
| minimum clearance | **0.20000 mm copper** (U3.19 escape, against `I2C_SCL_INT` B.Cu) |

### Topology verified before routing, not assumed

Both resistors turned out to be **pull-downs, i.e. tees — not series elements**:

| net | pads | resistor |
|---|---|---|
| `SX1262_RXEN` | **U3.19** (expander U61 @ 0x21, P16), R74.1, U8.6 | R74.2 = **GND** → 100 k pull-down tee |
| `SX1262_RST_N` | **U2.5** (expander U60 @ 0x20, P01), R13.1, U8.15 | R13.2 = **GND** → pull-down tee, holds the radio RESET-ASSERTED |

Neither net originates at U1. `U8.6` sits on U8's **east** side (x 71.1–72.9), unlike the west-side
CS_N/DIO1/BUSY pads, so the radio end is in open territory.

### Route order: RXEN first, and the reason

RXEN is the more constrained net by a wide margin. Its source U3.19 sits at y ≈ 9.4 in the far north,
**behind the I2C fan-out barrier** (x 17.5 → 33.8, y 9.4 → 11.6) whose only 0.200 mm opening was
consumed by `SX1262_BUSY`'s jog at y = 8.750 in pass 3A-1. It must then traverse the full board
height to y ≈ 130. RST_N's source (U2.5, y ≈ 45) and tee (R13.1, y ≈ 53) are already mid-board, south
of all the northern congestion, with 547,517 and 140,663 legal via sites respectively.

### Route

```
B.Cu  (22.325,  9.600) → (22.325, 10.600)      out of U3.19, south into the TSSOP body gap
B.Cu  (22.325, 10.600) → (17.500, 10.600)      west, above the I2C_SCL_INT B.Cu wall at y = 11.000
B.Cu  (17.500, 10.600) → (17.500, 13.500)      south, west of the I2C_SCL_INT via
B.Cu  (17.500, 13.500) → (25.500, 13.500)      east, crossing WAKE_INT_N's In2 on B.Cu
B.Cu  (25.500, 13.500) → (25.500, 12.250) → (27.000, 12.250)   north between R66 and R67
via   (27.000, 12.250)   B.Cu → In2                        0.250 mm
In2   (27.000, 12.250) → (60.000, 12.600)      northern trunk, over NFC RESERVED
via   (60.000, 12.600)   In2 → B.Cu                        0.425 mm
B.Cu  (60.000, 12.600) → (66.000, 12.600) → (66.000, 10.800) → (72.000, 10.800)
B.Cu  (72.000, 10.800) → (72.000, 83.500)      far-east descent
B.Cu  (72.000, 83.500) → (66.000, 83.500)      west, north of the CC1101 / +3V3 lanes
via   (66.000, 83.500)   B.Cu → In2                        1.003 mm
In2   (66.000, 83.500) → (66.000, 85.000)      joins the staged x66 crossing
      [staged (66.000, 85.000) → (66.000, 117.000) — CONSUMED]
In2   (66.000, 117.000) → (66.000, 129.650) → (70.600, 129.650)
via   (70.600, 129.650)  In2 → F.Cu + B.Cu                 0.325 mm
F.Cu  (70.600, 129.650) → (70.000, 129.650)    tee into R74.1
B.Cu  (70.600, 129.650) → (71.500, 129.650)    into U8.6
```

### Three things shaped it

**U3 is a TSSOP-24 with 0.25 mm inter-pad gaps**, so U3.19 cannot escape between pads, and
HEADER RESERVED sits 0.2 mm above its north edge — no northward exit either. The only way out is
**south into the package body gap** between the two pad rows, then west above the `I2C_SCL_INT` B.Cu
wall at y = 11.000 and around the `I2C_SCL_INT` via at (18.200, 11.700). `WAKE_INT_N`'s In2 vertical
is then crossed on B.Cu rather than fought.

**`SX1262_BUSY`'s In2 descent at x = 61.000 is a wall** from y = 10 to 74.5, so the northern trunk
cannot continue east on In2. One B.Cu hop at y = 12.600 clears it.

**A mounting hole at (69.000, 13.000), radius 1.200 mm**, sits directly on the natural eastward path.
The first write put the B.Cu run at y = 12.600 and DRC caught it immediately —
`copper_edge_clearance, actual 0.0000 mm`. The run now jogs north to **y = 10.800** across
x 66 → 72, giving **2.200 mm** to the hole centre against the 1.800 mm requirement. All four board
cutouts (4.0/148.0, 10.5/10.0, 69.0/13.0, 70.5/144.0) were enumerated and are now checked explicitly.

### Clearances

| pair | measured |
|---|---|
| RXEN whole net, minimum | **0.20000 mm** (`I2C_SCL_INT` B.Cu at the U3.19 escape) |
| RXEN ↔ `SX1262_BUSY` | **0.80000 mm** |
| RXEN ↔ `SX1262_DIO1` | **2.77113 mm** |
| RXEN ↔ `SX1262_CS_N` | **3.80000 mm** |
| RXEN ↔ `USB_D_MCU_N` | **3.17500 mm** |
| RXEN ↔ `USB_D_MCU_P` | **3.97500 mm** |
| nearest mounting hole | **2.200 mm** (need 1.800) |

### E5, RF and keepouts

**x = 66.000 consumed** — it no longer appears in the free-endpoint audit. `SX1262_CS_N` x62,
`SX1262_DIO1` x63, `SX1262_BUSY` x64 and `SX1262_RST_N` x65 are all untouched; nothing was moved,
resized, duplicated or swapped and no new crossing was created. **0 new vias in the 915 band, 0 in
the 433 band, 0 new outer-layer transit of either band.** NFC RESERVED, HEADER RESERVED and WROOM
ANTENNA all clear of new copper. No `NFC_DEFERRED` copper.

### SX1262_RST_N — not closed in this pass

Its **eastern half is proven**: a mid-board In2 trunk at y = 48.000 (x 30 → 60, clear 0.900 mm), the
far-east In2 descent at x = 71.500 (clear 76 → 88), the westward approach on In2 at y = 81.500
(x 71.5 → 65, clear 0.600 mm past the `BAT_PROTECTED_P` via), the drop to (65.000, 85.000) onto the
staged lane (0.700 mm), and the U8.15 entry on B.Cu at y = 131.800 (0.300 mm clear of
`SX1262_DIO1`'s via at (63.000, 132.500)) all audit legal.

Four blockers remain, all in the **western** section, and all in territory I had not yet scanned at
the resolution used elsewhere:

- the U2.5 escape fouls the `TOUCH_RST_N` via near (7.500, 45.625);
- the southward run at x = 7.500 hits R4.1, and the eastward run at y = 50.500 hits R7.1;
- the climb at x = 20.000 crosses `WAKE_INT_N`'s B.Cu at y ≈ 49.200;
- the F.Cu hop over `SPI_B`'s wall would cross the `BQ25185_SYS` F.Cu rail at x = 61.200, and its
  first via site at (20.000, 48.000) fouls the `BMI270_INT1_STRAP` In2, while the second at
  (60.000, 48.000) comes within 0.100 mm of `SX1262_DIO1`'s B.Cu descent at x = 59.500.

None of these is a capacity problem — U2.5 alone has 547,517 legal via sites and 3.000 mm of best
margin — they are placement details of a first-cut path that needs the same scan-then-audit treatment
the eastern half received. RST_N is left for a focused pass. Its x = 65.000 crossing is untouched and
still staged at both ends.

### Preservation

Against `561bdca`: tracks **506 → 523**, vias **134 → 138**, **0 objects removed**, all 21 additions
on `/SX1262_RXEN`. Pads 776 with every coordinate identical and **0 pad net assignments changed**, so
**188 footprints, 0 moved**. `USB_D_MCU_P` 24, `USB_D_MCU_N` 20, `SPI_B_SCK` 32, `SPI_B_MOSI` 31,
`SPI_B_MISO` 31, `SX1262_CS_N` 19, `SX1262_BUSY` 23, `SX1262_DIO1` 19, `BMI270_INT1_STRAP` 7,
`I2C_SDA_INT` 32, `I2C_SCL_INT` 36, `NFC_IRQ` 0, `SX1262_RST_N` 1 — every count unchanged.

`NFC_IRQ` remains **0 tracks, 0 vias, 0 zones**, 2 islands, 1 intentional ratsnest item.

DRC **0 electrical errors**; warnings 246 → **245**. Board ratsnest **417 → 414**. ERC
**116 / 58 excluded / 58 live**, unchanged. Schematic parity **261, delta 0**. Schematic,
`.kicad_dru` and `.kicad_pro` untouched.

Staged lanes remaining: `SX1262_RST_N` (x 65), `CC1101_CS_N` (x 67), `CC1101_GDO0` (x 68),
`BTN_HOME_N` (x 13.8), `+3V3` (x 69.1 B.Cu end), plus the pre-existing `BQ25185_SYS`, `LED_K` and
`NFC_5V_PA_PENDING` ends — 15 free endpoints.

**SX1262_RXEN: PASS**
**SX1262_RST_N: DEFERRED — eastern half proven, western half needs a focused pass**


---

## E6_3V3_PAD_ESCAPE and U3_21_ESCAPE — DRU rule areas (rules-only pass)

`+3V3` was routed last, so on four fine-pitch parts its pads are now enclosed by
neighbouring escapes that were routed first. This pass adds the CTO-approved rule
infrastructure for those escapes. **No copper was routed and no placement moved.**

**E6 is pad-scoped, not a netclass relaxation.** It is not a transit corridor, it does
not authorise 0.15 mm trunks, and it does not relax clearance generally.

| area | pad | layer | width | clearance |
|---|---|---|---|---|
| `E6_C18_1` `E6_J1_40` `E6_J1_41` `E6_J1_42` `E6_R11_1` `E6_R2_1` `E6_R29_1` | seven standard pads | F/B.Cu | >= 0.15 mm | **0.20 mm, UNCHANGED** |
| `E6_U9_1` | U9.1 | F.Cu | >= 0.15 mm | **0.10 mm — VERIFY-AT-FAB-LOCK** |
| `U3_21_ESCAPE` | U3.21 | B.Cu | >= 0.15 mm | **0.20 mm, UNCHANGED** |

The 2.0 mm reduced-neck cap, the single-pad-feed rule and the "no aggregate current"
rule are **procedural** and reviewed geometrically at routing time; KiCad's net-length
constraint is the wrong instrument and was deliberately not used. Every neck must widen
to >= 0.30 mm, preferably 0.60 mm, immediately after the escape.

**Board Setup floors were already sufficient and were NOT changed**: minimum track width
0.15 mm, minimum clearance 0.0 mm. These are DRC floors only — they grant no permission
for copper outside the named areas; netclass and custom rules continue to govern.

**U9.1 copper is NOT authorised yet.** The 0.10 mm rule exists so the geometry can be
planned, but no copper may use it until the selected 4-layer, 1 oz outer process
publishes a spacing capability <= 0.10 mm.

### Two findings that change what Pass B can achieve

**1. The standard E6 rule does not, by itself, unblock any of its seven pads.** Those
pads are trapped by *clearance*, not width: a pocket needs `w + 2 x clearance` of room,
so with clearance held at 0.20 mm a pad needs a 0.55 mm gap and narrowing the trace to
0.15 mm barely helps. Re-flooding each pad at 0.15 mm / 0.20 mm leaves all seven still
trapped. Only `E6_U9_1`, the one area that relaxes clearance, actually opens its pad.
Closing C18.1, J1.40-42, R11.1, R2.1 and R29.1 needs a clearance decision, not a width one.

**2. `U3_21_ESCAPE` grants width relief but not passage.** HEADER RESERVED's keepout is
enforced by the zone itself, not by a custom rule, so no DRU rule can let +3V3 cross it.
A probe track at 0.15 mm inside the area reports no width error but is still rejected as
"Items not allowed". Routing U3.21 north will additionally require a scoped notch in the
HEADER RESERVED polygon — an existing-zone edit, which this pass was not authorised to
make. U3.21 also cannot be rescued by clearance alone: it stays trapped even at
0.10 mm / 0.10 mm, boxed by HEADER RESERVED at 0.200 mm north, U3.20 and U3.22 at
0.250 mm either side and I2C_SCL_INT at 0.350 mm south.

Rule ordering is load-bearing: the three new rules sit **last** in `aqroot-Beta.kicad_dru`
so they beat both the P3V3 outer-layer width floor and the land-pattern block that closes
the PRECEDENCE TAIL. Verified by probe: 0.15 mm +3V3 outside any area still fails at
0.40 mm; inside a standard area it passes on width but still fails at 0.15 mm clearance;
inside `E6_U9_1` the measured escape passes cleanly at 0.15/0.10.

**Scope warning recorded in the rules file:** KiCad evaluates `intersectsArea` per object,
so a track that merely clips one of these areas inherits the relaxed rule along its whole
length. Every E6 neck must be written as its own short segment.

DRC 0 electrical errors before and after; 638 tracks, 166 vias, 776 pads and 188
footprints all bit-identical; every pre-existing rule area unchanged.


---

## JLCPCB fab lock, per-pad E6 clearances, and the U3.21 HEADER RESERVED exception

Rules-only pass. No copper routed, no placement moved, no existing copper touched.

### Fab lock

**JLCPCB is the locked AQROOT Beta PCB fab.** Class: 4-layer, 1.6 mm finished,
1 oz outer / 0.5 oz inner, stackup JLC04161H-7628.

Published capability, checked 2026-08-13 against *"PCB Manufacturing & Assembly
Capabilities - JLCPCB"*, <https://jlcpcb.com/capabilities/pcb-capabilities>,
row **"Min. track width and spacing (1 oz)"**:

> Multilayer: 0.09 / 0.09 mm (3.5 / 3.5 mil). 3 mil is acceptable in BGA fan-outs.

So **minimum outer track width 0.09 mm, minimum outer spacing 0.09 mm**. JLCPCB's
own recommended production baseline is 4 mil (0.1016 mm); anything between 0.09 mm
and that baseline is within capability but should be flagged for DFM review at
submission. Board Setup absolute floors were re-confirmed and left unchanged at
**0.15 mm minimum track width / 0.0 mm minimum clearance** - these remain DRC
floors only and confer no routing permission.

### Per-pad E6 clearances - measured, not assumed

Each figure is the largest clearance at which a 0.15 mm neck can still reach the
+3V3 tree on the current board. No pad inherits another's number.

| area | pad | layer | measured clearance | narrowest channel | tier | JLCPCB gate |
|---|---|---|---|---|---|---|
| `E6_C18_1` | C18.1 | F.Cu | 0.180 mm | 0.510 mm | A | n/a |
| `E6_R29_1` | R29.1 | F.Cu | 0.160 mm | 0.470 mm | A | n/a |
| `E6_U9_1`  | U9.1  | F.Cu | 0.160 mm | 0.470 mm | A | n/a |
| `E6_R11_1` | R11.1 | B.Cu | 0.140 mm | 0.430 mm | B | PASS (0.140 >= 0.09) |
| `E6_J1_40` | J1.40 | F.Cu | 0.120 mm | 0.390 mm | B | PASS (0.120 >= 0.09) |
| `E6_J1_41` | J1.41 | F.Cu | 0.120 mm | 0.390 mm | B | PASS (0.120 >= 0.09) |
| `E6_J1_42` | J1.42 | F.Cu | 0.120 mm | 0.390 mm | B | PASS (0.120 >= 0.09) |
| `E6_R2_1`  | R2.1  | B.Cu | 0.100 mm | 0.350 mm | B | PASS (0.100 >= 0.09) |

No pad falls in Tier C. All Tier-B gates pass against the locked fab.

**U9.1's provisional 0.10 mm allowance was never needed.** The measured requirement
is 0.160 mm, so the rule was *tightened* from 0.10 to 0.160 mm and the
VERIFY-AT-FAB-LOCK tag retired. For the record the original gate also passes on its
own terms - 0.10 mm >= JLCPCB's 0.09 mm - but no copper will now rely on it.

Containment: every per-pad clearance rule is conditioned on `enclosedByArea()`, so
only a neck lying wholly inside its own pocket gets the relief. A track that merely
clips a pocket keeps the ordinary 0.20 mm netclass figure - verified by probe.

### U3.21 is REQUIRED

U3 is a **TCA9535PWR** (TSSOP-24), datasheet TI **SCPS201E**, Aug 2009, revised
May 2022. Table 5-1 for the DB/PW package gives pin 21 as **A0, Input** -
*"Address input 0. Connect directly to V<sub>CC</sub> or ground."*

U3.21 is therefore an address strap, not a supply pin, and **not NC-capable**: the
part has no internal pull on A0/A1/A2 and the datasheet requires a hard tie. U3.24
is VCC and is already fed by the Pass-A backbone. Leaving A0 floating would leave
U3's I2C address undefined, so **U3.21 REQUIRED = YES**. Note it carries only
leakage current (+-1 uA per the datasheet), so the escape has no width obligation
beyond manufacturability.

### HEADER RESERVED enforcement converted

HEADER RESERVED was enforced by the rule area's own keepout flags (case B), not by
any DRU rule. A zone keepout cannot carry a net-conditional exception, so this
commit converts it: the zone's `tracks`/`vias` flags are released to `allowed` and
the prohibition is re-imposed as a DRU rule over the same area, same geometry
(x 18.5-55.5, y 0-8.5) and same layers (F.Cu, B.Cu, In2.Cu). The zone keeps
`copperpour not_allowed`, so pour protection never lapsed, and `pads allowed`, which
is what lets the J5 land pattern sit inside the reservation. J5's fanout exception is
untouched - it was never a track/via rule.

The exception is scoped with **`enclosedByArea('U3_21_ESCAPE')`, never
`intersectsArea`**, which is what makes it leak-proof.

`U3_21_ESCAPE` was resized from 1.10 x 3.53 mm to **x 23.125-26.100, y 7.750-9.900
(2.975 x 2.150 mm) on B.Cu** to fully enclose the measured escape:

```
B.Cu (23.625, 9.400) -> (23.625, 8.250)   out of U3.21, north across y = 8.5
B.Cu (23.625, 8.250) -> (25.600, 8.250)   east inside HEADER RESERVED
B.Cu (25.600, 8.250) -> (25.600, 9.400)   south into U3.24's existing +3V3
```

**The escape does not need E6 at all.** It fits at **0.40 mm**, the full P3V3
outer-layer minimum - HEADER RESERVED was its only blocker, not width or clearance.
The area covers about 2% of the reservation, admits +3V3 only, and admits only
objects wholly inside it.

Because `U3_21_ESCAPE` is a single-layer (B.Cu) area, a through via can never be
"enclosed" by it, so **no via can ever use this exception** - confirmed by probe.
The escape is planar B.Cu with zero vias, which is what we want.

### Acceptance probes

All on a scratch board; no probe copper reached the real board.

| probe | expected | result |
|---|---|---|
| A  +3V3 wholly enclosed, crossing HEADER RESERVED | PASS | **0 violations** |
| B  +3V3 in HEADER RESERVED outside the area | FAIL | items_not_allowed |
| C  non-+3V3 inside the area crossing HEADER RESERVED | FAIL | items_not_allowed |
| D1 +3V3 via enclosed by the area | - | items_not_allowed (single-layer area; vias can never qualify) |
| D2 +3V3 via in HEADER RESERVED outside the area | FAIL | items_not_allowed |
| **E  LEAK: one track starts inside the area, continues through HEADER RESERVED outside it** | **FAIL** | **items_not_allowed** |
| F  0.15 mm +3V3 enclosed by E6_R2_1 at its measured 0.100 mm | PASS | 0 violations |
| G  same at 0.090 mm | FAIL | cites `E6_R2_1: measured local +3V3 clearance 0.100 mm` |
| H  0.15 mm at 0.100 mm that clips E6_R2_1 and runs outside | FAIL | falls back to netclass P3V3 0.200 mm |
| I  0.15 mm +3V3 outside every pocket | FAIL | `P3V3 minimum width on the outer layers` 0.400 mm |

Probe E is the one that matters: had it passed, the exception would have leaked and
the implementation would have been wrong.

DRC 0 electrical errors before and after; ratsnest 384 unchanged; 638 tracks,
166 vias, 776 pads, 188 footprints all bit-identical; every zone except the two
intended edits bit-identical.


---

## Four width-only +3V3 escape pockets, and the consolidated E6 registry

Rules-only pass. No copper routed, no placement moved, no existing copper touched.

Four Pass-B pads measured on the current board cannot be escaped at the 0.40 mm
P3V3 outer-layer minimum. Unlike the section-13/15 E6 pockets, they are limited by
**width alone** - each works at the ordinary 0.20 mm clearance once the trace narrows.
`U4.12` and `J1.35` additionally have pads only 0.250 mm and 0.300 mm across their
narrow dimension, so a 0.40 mm centreline cannot land on them at all.

These four rules therefore constrain **width only and carry no clearance term**, so
the pockets can never silently diverge from the global figure. That makes them a
strictly weaker concession than the E6 clearance pockets: no fab-capability question,
no pairwise blast radius.

| area | pad | layer | polygon (x, y) | size | min width | clearance |
|---|---|---|---|---|---|---|
| `E6_R3_2` | R3.2 | B.Cu | 18.300-20.025 x 42.200-45.475 | 1.725 x 3.275 | 0.15 mm | global 0.20 |
| `E6_U4_5` | U4.5 | B.Cu | 9.600-12.125 x 61.950-63.650 | 2.525 x 1.700 | 0.30 mm | global 0.20 |
| `E6_U4_12` | U4.12 | B.Cu | 11.200-13.075 x 62.850-65.000 | 1.875 x 2.150 | 0.20 mm | global 0.20 |
| `E6_J1_35` | J1.35 | F.Cu | 32.275-33.225 x 79.210-83.075 | 0.950 x 3.865 | 0.15 mm | global 0.20 |

Each polygon was derived from the measured escape at that pad's approved width,
trimmed to the 2.0 mm neck cap, plus a half-width + 0.25 mm margin. All four use
`enclosedByArea()`, so only a neck lying wholly inside its own pocket gets the relief;
a track that merely clips a pocket keeps the full 0.40 mm minimum. No existing +3V3
copper lies inside any of them.

### J1.35 merge requirement

J1.35 is **one of seven parallel +3V3 pins** on the CH280QV10-CT_50P display FPC
(J1.7, .8, .9, .35, .40, .41, .42). Its 0.15 mm neck feeds J1.35 **and nothing else**.
Once clear of the FPC pad field it must merge immediately into the normal-width display
+3V3 branch at >= 0.30 mm, preferably 0.60 mm. **No shared display current may flow
through the neck itself.** This is a routing-time gate, checked geometrically.

### U4.12 strap note

U4 is a **BMI270** (Bosch 6-axis IMU, LGA-14). Its +3V3 pins are not equivalent:
U4.5 is VDDIO and U4.8 is VDD (supplies, sub-mA); U4.2 ASDx and U4.3 ASCx are
auxiliary-interface straps; and **U4.12 is CSB**, strapped high to select I2C. The
narrow local route at U4.12 is therefore a **strap connection, not a power-current
branch**. If the BMI270 is ever moved to SPI, CSB becomes an active chip select -
that is a **schematic function change, not a routing-only change**, and this pocket
must be re-reviewed rather than silently reused. R3.2 is likewise a strap-class load:
R3 is a 10k pull-up on WAKE_INT_N, so its neck carries ~330 uA.

### Consolidated relief-area registry - 13 areas, read from the live board and rules

| area | pad | net | min width | clearance term | neck cap | fab gate | status |
|---|---|---|---|---|---|---|---|
| `E6_C18_1` | C18.1 | +3V3 | 0.15 mm | measured 0.180 | 2.0 mm | n/a (Tier A) | active |
| `E6_R29_1` | R29.1 | +3V3 | 0.15 mm | measured 0.160 | 2.0 mm | n/a (Tier A) | active |
| `E6_U9_1` | U9.1 | +3V3 | 0.15 mm | measured 0.160 | 2.0 mm | n/a (Tier A) | active |
| `E6_R11_1` | R11.1 | +3V3 | 0.15 mm | measured 0.140 | 2.0 mm | PASS vs 0.09 | active |
| `E6_J1_40` | J1.40 | +3V3 | 0.15 mm | measured 0.120 | 2.0 mm | PASS vs 0.09 | active |
| `E6_J1_41` | J1.41 | +3V3 | 0.15 mm | measured 0.120 | 2.0 mm | PASS vs 0.09 | active |
| `E6_J1_42` | J1.42 | +3V3 | 0.15 mm | measured 0.120 | 2.0 mm | PASS vs 0.09 | active |
| `E6_R2_1` | R2.1 | +3V3 | 0.15 mm | measured 0.100 | 2.0 mm | PASS vs 0.09 | active |
| `E6_R3_2` | R3.2 | +3V3 | 0.15 mm | **global 0.20** | 2.0 mm | n/a | active (new) |
| `E6_U4_5` | U4.5 | +3V3 | 0.30 mm | **global 0.20** | 2.0 mm | n/a | active (new) |
| `E6_U4_12` | U4.12 | +3V3 | 0.20 mm | **global 0.20** | 2.0 mm | n/a | active (new) |
| `E6_J1_35` | J1.35 | +3V3 | 0.15 mm | **global 0.20** | 2.0 mm | n/a | active (new) |
| `U3_21_ESCAPE` | U3.21 | +3V3 | 0.15 mm | **global 0.20** | 2.0 mm | n/a | active; also carries the scoped HEADER RESERVED exception. The measured escape fits at 0.40 mm, so the width relief is expected to go unused |

The eight `measured` entries relax clearance; the five `global 0.20` entries do not.
Every area is +3V3-only and single-pad.

### Acceptance probes

Scratch board only, no probe copper reached the real board.

| probe | expected | result |
|---|---|---|
| A - approved width inside each of the four pockets | PASS | **0 violations** in all four |
| B - 0.15 mm +3V3 outside every pocket | FAIL | `P3V3 minimum width on the outer layers` 0.400 |
| B2 - 0.30 mm +3V3 outside every pocket | FAIL | same rule, 0.400 |
| C - neck at 0.150 mm clearance inside `E6_R3_2` | FAIL | netclass P3V3 clearance 0.200 |
| C - neck at ~0.157 mm inside `E6_U4_5` | FAIL | netclass P3V3 clearance 0.200 |
| C - neck at ~0.185 mm inside `E6_U4_12` | FAIL | netclass P3V3 clearance 0.200 |
| C - neck at 0.150 mm inside `E6_J1_35` | FAIL | netclass P3V3 clearance 0.200 |

Probe A proves the width relief is live; probe B proves it is scoped to the pockets;
probe C proves clearance is **not** relaxed anywhere.

DRC 0 electrical errors before and after; ratsnest 384 unchanged; 638 tracks, 166 vias,
776 pads and 188 footprints all bit-identical; every pre-existing rule area and rule
untouched; the `.kicad_dru` change is a pure append.


## 2026-08-14 - B3 rule correction: E6 areas moved to the MEASURED constrained regions

### The defect this fixes

The original E6 pockets were sized as "pad bbox + the first ~2 mm of the measured
escape", assuming the sub-0.20 mm clearance region sits next to the pad. It does
not. Measured against HEAD 7b16f0f, every one of the four hard pads needed its
relief somewhere the pocket did not cover, and because the clearance rules use
`enclosedByArea` a track leaving its pocket gets no relief along **any** of its
length. That is why +3V3 Pass B3 wrote zero copper.

### CTO cap interpretation (now binding)

The 2.0 mm E6 cap means **maximum length of copper running below normal
clearance**. It is NOT a cap on sub-0.40 mm-width length. A narrow-width run at
normal clearance may exceed 2.0 mm as geometry requires; any single narrow-width
run over **6.0 mm** requires a fresh ruling before routing.

### R2.1 - reclassified from corridor relief to VIA-SITE relief

R2.1 needs **0.000 mm** of reduced-clearance track. Its entire relief requirement
is one through via at **(23.300, 36.000)**, B.Cu to F.Cu, after a short B.Cu
dogleg. The old ~4.75 mm reduced-clearance corridor is abandoned.

Hole-referenced fab arithmetic (the governing metric is hole-to-copper, not
pad-to-copper):

| quantity | value |
|---|---|
| via pad / drill (POWER class) | 0.800 mm / 0.400 mm |
| annular ring width | 0.200 mm |
| In2 annular ring | present (`remove_unused_layers no`) |
| copper-edge clearance to In2 `/WAKE_INT_N` | 0.100 mm |
| **hole-edge to `/WAKE_INT_N`** | **0.300 mm** |
| JLCPCB via hole to copper requirement | 0.200 mm |
| margin | **+0.100 mm** |

0.300 >= 0.200, and also >= the 0.225 mm target (0.200 floor + 0.025 design
margin), so the candidate survives and no Option-B re-search was needed.
`E6_R2_1` therefore becomes a tight multilayer via-site area. The copper-to-copper
relief it must grant at that site is 0.100 mm (In2 `/WAKE_INT_N`), 0.114 mm (B.Cu
pad U1.28), 0.125 mm (via `/SD_CS_N`) and 0.159 mm (B.Cu pad U1.27), all covered
by the approved 0.100 mm figure.

### Relocated rule areas

| area | was | now | layers | measured reduced-clearance run |
|---|---|---|---|---|
| `E6_R2_1` | x 20.425-21.925, y 35.025-38.325, B.Cu | x 22.800-23.800, y 35.500-36.500 | F.Cu In1.Cu In2.Cu B.Cu | 0.000 mm (via only) |
| `E6_J1_40` | x 29.750-30.750, y 77.535-81.115 | x 30.950-31.800, y 78.150-78.550 | F.Cu | 0.641 mm, east |
| `E6_J1_41` | x 29.250-30.250, y 77.535-81.115 | x 25.500-26.500, y 80.850-81.200 | F.Cu | 0.771 mm, west |
| `E6_J1_42` | x 28.750-29.750, y 77.535-81.115 | x 30.400-31.550, y 80.850-82.000 | F.Cu | 1.541 mm, south |
| `E6_R11_1` | x 14.975-18.125, y 44.675-46.325 | x 18.150-18.800, y 45.800-46.350 | B.Cu | 0.504 mm, east |

Each rectangle is the measured tight region plus 0.150 mm for the 0.15 mm track
body and the 0.05 mm search grid - tight containment per doctrine, not the whole
narrow track. The three J1 escapes were validated **sequentially**, each committed
neck blocking the next, so all three fit simultaneously with separate necks. They
leave in three different directions and merge only in normal-width F.Cu copper.

### C18.1 - NOT changed, needs a ruling

C18.1 measures **0.000 mm** of reduced-clearance track and a 0.612 mm narrow run.
Its only relief candidate is a via at (18.900, 19.400) F.Cu to In2.Cu whose gap to
both B.Cu `/SX1262_BUSY` and In2 `/I2C_SCL_INT` is **exactly 0.200 mm** - it
already meets the ordinary requirement and needs no clearance relief at all
(hole-referenced 0.400 mm, +0.200 mm margin). Turning `E6_C18_1` into a via-site
area, or deleting its clearance rule, is beyond a relocation, so its pocket was
left untouched pending a ruling.

### R29.1 - earlier reclassification withdrawn

An earlier recommendation to demote R29.1 to width-only was based on an
endpoint-only spot check and is **wrong**. Under the proper test R29.1 is not
inside source-connected 0.15 mm / 0.20 mm space, so it remains an E6
clearance-relief pad. Its rule was not touched.

### Existing E6 routed-copper sweep

No routed copper currently leans on any E6 rule - B3 wrote nothing and Passes
A/B1/B2 routed at normal width and clearance - so the retrospective cap audit
passes with nothing to grandfather. KiCad DRC is authoritative and reports 0
errors. An offline sweep flagged several power-net pairs, but that model is not
parity-validated for the elevated-clearance netclasses and KiCad does not agree,
so no violation is claimed. One observation worth carrying: a pre-existing 0.300 mm
+3V3 segment at (65.500, 52.400)-(66.000, 52.400) on F.Cu sits below the 0.40 mm
P3V3 outer floor and intersects no rule area, yet KiCad raises no width error. It
is outside every B-pass region and was not touched.

### Acceptance probes

Scratch boards only; no probe copper reached the real board. Probe boards need the
`.kicad_pro` copied alongside them (netclass assignments) and `--refill-zones`, or
an isolated through via merges into the In1 GND pour and the results are garbage.
Both mistakes were made and corrected before these numbers were taken.

| probe | expected | result |
|---|---|---|
| baseline scratch board, no probe copper | 0 errors | **0** |
| A - +3V3 via at (23.300, 36.000) inside `E6_R2_1`, attached to R2.1 | relief applies | **all three via clearance violations gone** |
| B - same via outside the area | FAIL | falls back to netclass 0.200 mm |
| C - 0.15 mm track straddling the `E6_J1_40` boundary | FAIL | `netclass 'P3V3' clearance 0.2000` - relief refused |
| C2 - same track wholly inside `E6_J1_40` | relief applies | `rule 'E6_J1_40: measured local +3V3 clearance 0.120 mm'` fires |

C versus C2 is the leak test: `enclosedByArea` grants relief only to a wholly
contained object. Probe A's residual `shorting_items` is the straight-line probe
track clipping the `/CC1101_GDO0` via, which the real 2.916 mm dogleg route avoids.

### Open item before B3 copper

These areas grant clearance relief on the tight region only. The **width** relief
for the narrow runs (R2.1 2.916 mm, J1.40 2.394 mm, J1.41 4.478 mm, J1.42 3.506 mm,
R11.1 2.911 mm) comes from the shared `intersectsArea` width rule, which is
per-object - so every narrow segment must individually touch its area, or separate
width-only areas must be defined. This pass does not resolve that.

DRC 0 electrical errors before and after; 696 tracks and 175 vias byte-identical;
all 188 footprint blocks byte-identical (file order changed only because KiCad
re-serialised on zone refill); exactly 5 zones changed; NFC_IRQ still 0/0/0.


## 2026-08-14 - FINAL B3 rule update: paired CLR/WIDTH areas, C18.1 reclassified

### Why pairing was needed

The previous pass moved the E6 clearance pockets onto the measured
reduced-clearance regions, which was correct but left the **width** relief
dangling: the narrow runs are 2.4-4.5 mm long while the clearance pockets are
under 1.6 mm, and the shared width rule used `intersectsArea`, which is
per-object and would let a track clip the area and stay narrow outside it.
Each case now carries two areas.

### Standing cap semantics

| metric | limit |
|---|---|
| clearance-relief run | **hard cap 2.0 mm** |
| total narrow-width run | **review trigger above 6.0 mm** |

Different metrics. The 2.0 mm cap does **not** apply to narrow-width length.
Longest narrow run is J1.41 at 4.478 mm, below the trigger.

### Area semantics

Both `*_CLR` and `*_WIDTH` use `enclosedByArea()`. `intersectsArea()` is
deliberately not used for the new width paths. Routing discipline for B3: split
every track segment at the area boundary.

### End-cap margin

KiCad extends a track cap by width/2 past the endpoint, so a 0.15 mm neck needs
at least 0.075 mm of overhang or the cap pokes out and `enclosedByArea()` fails.
Every `*_WIDTH` rectangle overhangs by **0.150 mm**, which also absorbs the
0.075 mm half-width and the 0.05 mm measurement grid.

`*_WIDTH` areas are the union of the measured route bbox **and the source pad
bbox**, both plus the overhang. Probe C caught the reason: the route's first cell
sits near one corner of the pad, so a neck attached anywhere else on the pad would
have started outside the area and lost its width relief.

### Registry (read from the live rules and board)

| area | class | semantics | geometry | layers | width min | clearance | clr run | narrow run |
|---|---|---|---|---|---|---|---|---|
| `E6_C18_1_WIDTH` | WIDTH-ONLY | `enclosedByArea` | x 18.090-19.050 y 19.250-20.710 | F.Cu | 0.15 | global 0.20 | 0.000 | 0.612 |
| `E6_J1_35` | WIDTH-ONLY | `enclosedByArea` | x 32.275-33.225 y 79.210-83.075 | F.Cu | 0.15 | global 0.20 | - | - |
| `E6_J1_40_CLR` | CLEARANCE | `enclosedByArea` | x 30.950-31.800 y 78.150-78.550 | F.Cu | - | 0.120 | 0.641 | 2.394 |
| `E6_J1_40_WIDTH` | WIDTH-ONLY | `enclosedByArea` | x 29.950-32.050 y 78.050-80.915 | F.Cu | 0.15 | global 0.20 | 0.641 | 2.394 |
| `E6_J1_41_CLR` | CLEARANCE | `enclosedByArea` | x 25.500-26.500 y 80.850-81.200 | F.Cu | - | 0.120 | 0.771 | 4.478 |
| `E6_J1_41_WIDTH` | WIDTH-ONLY | `enclosedByArea` | x 25.200-30.050 y 79.385-81.350 | F.Cu | 0.15 | global 0.20 | 0.771 | 4.478 |
| `E6_J1_42_CLR` | CLEARANCE | `enclosedByArea` | x 30.400-31.550 y 80.850-82.000 | F.Cu | - | 0.120 | 1.541 | 3.506 |
| `E6_J1_42_WIDTH` | WIDTH-ONLY | `enclosedByArea` | x 28.950-31.550 y 79.385-82.300 | F.Cu | 0.15 | global 0.20 | 1.541 | 3.506 |
| `E6_R11_1_CLR` | CLEARANCE | `enclosedByArea` | x 18.150-18.800 y 45.800-46.350 | B.Cu | - | 0.140 | 0.504 | 2.911 |
| `E6_R11_1_WIDTH` | WIDTH-ONLY | `enclosedByArea` | x 16.825-18.950 y 44.875-47.350 | B.Cu | 0.15 | global 0.20 | 0.504 | 2.911 |
| `E6_R29_1` | CLEARANCE+width | `enclosedByArea/intersectsArea` | x 17.575-20.725 y 16.275-17.925 | F.Cu | 0.15 | 0.160 | - | - |
| `E6_R2_1_CLR` | CLEARANCE | `enclosedByArea` | x 22.800-23.800 y 35.500-36.500 | B.Cu,F.Cu,In1.Cu,In2.Cu | - | 0.100 | 0.000 | 2.916 |
| `E6_R2_1_WIDTH` | WIDTH-ONLY | `enclosedByArea` | x 20.625-23.450 y 35.800-38.125 | B.Cu | 0.15 | global 0.20 | 0.000 | 2.916 |
| `E6_R3_2` | WIDTH-ONLY | `enclosedByArea` | x 18.300-20.025 y 42.200-45.475 | B.Cu | 0.15 | global 0.20 | - | - |
| `E6_U4_12` | WIDTH-ONLY | `enclosedByArea` | x 11.200-13.075 y 62.850-65.000 | B.Cu | 0.20 | global 0.20 | - | - |
| `E6_U4_5` | WIDTH-ONLY | `enclosedByArea` | x 9.600-12.125 y 61.950-63.650 | B.Cu | 0.30 | global 0.20 | - | - |
| `E6_U9_1` | CLEARANCE+width | `enclosedByArea/intersectsArea` | x 21.350-22.900 y 20.050-22.700 | F.Cu | 0.15 | 0.160 | - | - |
| `U3_21_ESCAPE` | WIDTH-ONLY | `intersectsArea` | x 23.125-26.100 y 7.750-9.900 | B.Cu | 0.15 | global 0.20 | - | - |

`E6_C18_1` no longer exists as a clearance pocket: the zone was repurposed into
`E6_C18_1_WIDTH` and its clearance rule was **deleted**. C18.1 measures 0.000 mm
of reduced-clearance track, and its via at (18.900, 19.400) already clears
0.200 mm to both B.Cu `/SX1262_BUSY` and In2 `/I2C_SCL_INT` (hole-referenced
0.400 mm, +0.200 mm margin), so the via uses normal rules only.

`E6_R29_1` and `E6_U9_1` are untouched and keep their `intersectsArea` width
relief; the shared width rule was narrowed to just those two.

### Probes (scratch boards only, all deleted)

| probe | expectation | result |
|---|---|---|
| baseline, no probe copper | 0 errors | **0** |
| A - 0.15 mm neck wholly inside `E6_J1_40_WIDTH` | width relief granted | **no width error** |
| B - same neck at x 32.5, outside every WIDTH area | width relief denied | **`P3V3 minimum width` 0.4000 vs 0.1500** |
| C - R2.1 via inside `E6_R2_1_CLR`, attached to the pad | clearance relief granted | **all via clearance errors gone, no width error** |
| D - same via straddling the CLR boundary | clearance relief denied | **3 clearance errors at netclass 0.200** |
| E - neck endpoint exactly on the WIDTH boundary | unsafe | **width error - the end cap pokes out, as predicted** |
| F - same neck with 0.150 mm overhang | safe | **no width error** |

Probe E is the one that justifies the mandatory end-cap margin: an endpoint placed
exactly on the boundary fails, the same endpoint pulled 0.150 mm inside passes.
Residual `clearance` / `shorting_items` entries in A/C/E/F come from probe tracks
drawn as straight lines rather than along the measured dogleg; they are not width
or relief failures.

### Preservation

DRC 0 electrical errors before and after. 696 segments, 175 vias and all 188
footprint blocks byte-identical; zones 24 -> 29 (5 renamed to `_CLR`, `E6_C18_1`
repurposed, 5 new `_WIDTH`); NFC_IRQ still 0 tracks / 0 vias / 0 zones; x69.100
staged and unchanged; no routed copper added, removed or modified.


## 2026-08-14 - R29.1 final rule pass: paired areas placed on the measured geometry

The old `E6_R29_1` was a single combined area wrapped around the pad at
x 17.575-20.725, y 16.275-17.925. R29.1's escape does not pinch there - it runs
**west** along y ~17.5 and pinches about 6 mm away. The old area granted relief
in a region the route never uses, and granted none where the route needs it.

An earlier figure of 9.757 mm for R29.1's narrow run was an upper bound from a
clearance-minimising search, not a minimum. Re-searched minimising sub-0.40 mm
width length, the true figures are far smaller.

### Measured (route from the pad at (19.600, 17.500) to handoff (11.700, 19.700), F.Cu, no via)

| quantity | value |
|---|---|
| reduced-clearance run | **0.350 mm**, one contiguous run, (11.850, 18.900) -> (11.850, 19.250) |
| clearance actually required | **0.1753 mm**, limited by via `/SPI_B_SCK` |
| approved R29.1 clearance | 0.160 mm - **sufficient**, kept unchanged |
| total narrow-width run | **1.991 mm**, one contiguous run, (11.850, 17.700) -> (11.750, 19.650) |

Both are inside the standing limits: 2.0 mm hard cap on reduced-clearance length,
6.0 mm review trigger on narrow-width length. Neither cap was touched.

### Areas

| area | geometry | layer | rule |
|---|---|---|---|
| `E6_R29_1_CLR` | x 11.700-12.000, y 18.750-19.400 | F.Cu | clearance min 0.160 mm, `enclosedByArea` |
| `E6_R29_1_WIDTH` | x 11.550-12.000, y 17.550-19.850 | F.Cu | track_width min 0.15 mm, `enclosedByArea`, no clearance term |

Both are the measured run plus the standing 0.150 mm overhang. The handoff at
(11.700, 19.700) sits inside the WIDTH area with 0.150 mm to spare in every
direction, well past the 0.075 mm end-cap minimum.

`E6_R29_1` no longer exists: the zone was repurposed into `E6_R29_1_CLR` with the
new polygon, so no dormant relief is left in the abandoned region. The shared
`intersectsArea` width rule now names only `E6_U9_1`.

### Probes (scratch boards only, deleted)

| probe | expectation | result |
|---|---|---|
| baseline | 0 errors | **0** |
| A - 0.15 mm neck wholly inside `E6_R29_1_WIDTH` | width relief granted | **0 errors** |
| B - same neck outside the WIDTH area | width relief denied | **`P3V3 minimum width` 0.4000 vs 0.1500** |
| C - the 0.350 mm constrained run wholly inside `E6_R29_1_CLR` | relief granted at 0.160 | **0 errors** |
| D/E - same geometry straddling the CLR edge | relief denied | **`netclass 'P3V3' clearance 0.2000; actual 0.1750`** |
| F - WIDTH endpoint exactly on the boundary | unsafe | **width error, end cap outside** |
| G - same endpoint with 0.150 mm overhang | safe | **0 errors** |

Probe E doubles as an independent confirmation of the measurement: KiCad reports
the achieved clearance as 0.1750 mm, matching the 0.1753 mm computed offline, and
above the approved 0.160 mm.

DRC 0 electrical errors before and after; 696 segments, 175 vias and all 188
footprint blocks byte-identical; zones 29 -> 30; NFC_IRQ 0/0/0; no routed copper
added, removed or modified.

With this, all seven B3 pads have correctly sited relief and B3 copper can be
routed.

## 2026-08-14 - J1.42 WIDTH north extension (rules only, one area)

### What changed

`E6_J1_42_WIDTH` north edge **79.385 -> 79.245**, a **0.140 mm** extension.
Nothing else. One polygon line in the board file; the DRU gained a comment and
no rule. No copper, no placement, no schematic, no new clearance relief.

| area | before | after |
|---|---|---|
| `E6_J1_42_WIDTH` | x 28.950-31.550 y **79.385**-82.300 | x 28.950-31.550 y **79.245**-82.300 |
| `E6_J1_42_CLR` | x 30.400-31.550 y 80.850-82.000 | **unchanged** |
| `E6_J1_40_WIDTH` / `_CLR` | - | **unchanged** |
| `E6_J1_41_WIDTH` / `_CLR` | - | **unchanged** |

### Why - the handoff arithmetic

J1.42 escapes **north** out of the pad row. The neck runs at 0.15 mm until the
first point where a normal-width P3V3 track (0.40 mm outer floor) is legal. The
binding obstacle is the **GND pad J1.43 corner at (28.900, 79.535)**: a 0.40 mm
track on the J1.42 pad centreline x = 29.250 must keep 0.200 mm from it, so its
south end cap centre must satisfy

	sqrt(0.350^2 + (79.535 - Yh)^2) >= 0.200 + 0.200
	Yh <= 79.535 - sqrt(0.40^2 - 0.35^2) = **79.341351**

KiCad agrees: Yh = 79.342 passes, Yh = 79.345 raises `clearance`. The approved
handoff **Yh = 79.320** sits inside that limit. Its 0.15 mm end cap reaches
79.320 - 0.075 = **79.245**, which is the new north edge.

Tolerance check against the ruling: the strictest handoff the geometry allows
(79.342) would need only 79.267, so the approved 79.245 is **0.022 mm** more
generous - inside the +/-0.05 mm band, no STOP condition.

### End-cap margin - this area is the documented exception

Standing doctrine gives every `*_WIDTH` rectangle a 0.150 mm overhang. On its
north edge this one now overhangs the approved route bbox by **0.290 mm**, and
the approved handoff sits at exactly 0.075 mm of overhang - **zero containment
margin**. Probe A confirms KiCad accepts an end cap lying exactly on the
boundary, but B3 should not route on the knife edge. Usable window under the
committed edge, both ends verified by DRC:

| Yh | end cap | containment margin | clearance margin | DRC |
|---|---|---|---|---|
| 79.320 | 79.245 | 0.000 | 0.021 | pass |
| **79.330** | **79.255** | **+0.010** | **+0.011** | **pass - balanced, recommended** |
| 79.340 | 79.265 | +0.020 | +0.001 | pass |
| 79.342 | 79.267 | +0.022 | 0.000 | pass |
| 79.345 | 79.270 | +0.025 | negative | **clearance** |

The band is 79.320 .. 79.342, 0.022 mm wide. **B3 should hand off at 79.330.**

### Containment probes

Scratch boards only, writer prefix `e6f42n01`; no probe copper reached the real
board. Approved escape under test: 0.15 mm neck (29.250, 80.150) -> (29.250,
79.320), then 0.40 mm (29.250, 79.320) -> (29.250, 78.550).

| probe | expectation | result |
|---|---|---|
| baseline, new edge, no probe copper | 0 errors | **0** |
| A - approved neck wholly inside the extended area | PASS | **0 errors** |
| A2 - neck + 0.40 mm continuation | PASS | **0 errors** |
| B - same neck under the OLD 79.385 edge | FAIL width | **`P3V3 minimum width` 0.4000 vs 0.1500** |
| C - neck straddling the new boundary | FAIL | **`P3V3 minimum width` 0.4000 vs 0.1500** |
| D - 0.40 mm continuation outside the WIDTH area | PASS | **0 errors** |
| E - 0.120 mm gap to J1.43 outside `E6_J1_42_CLR` | FAIL clearance | **`netclass 'P3V3' clearance 0.2000; actual 0.1200`** |

B is the whole case in one line: the identical neck that passes at 79.245 fails
at 79.385, so the 0.140 mm is load-bearing and nothing wider was granted.

### Merge discipline - unchanged

The north escape does not change display-power aggregation. J1.42 still runs its
own 0.15 mm neck from its own pad to the first >= 0.40 mm node and only then
joins the shared display branch; no aggregate current crosses the neck. The three
merge points get reported with the B3 route.

### Preservation

DRC **0 electrical errors before and after** (361 unconnected both sides, the
unrouted-board baseline). 696 segments, 175 vias, 0 arcs and all 188 footprint
blocks **byte-identical**; 0 footprints moved; 31 zones with **exactly one**
changed, `E6_J1_42_WIDTH`. File length unchanged, CRLF preserved, two byte-runs
differ - the two digit pairs of one polygon edge. NFC_IRQ still 0 tracks / 0 vias
/ 0 zones. x69.100 remains staged.

**No B3 copper was written in this commit.**

## 2026-08-14 - +3V3 PASS B3: all seven pads routed

First B3 copper. Seven orphan +3V3 pads joined the U12.4/U12.5 source island;
112 track segments and 5 vias added, nothing removed.

### Seeding and independence

Every route was solved against the **one verified source island containing
U12.4 and U12.5** (52 pads at HEAD). Orphan +3V3 pads and other candidates'
narrow necks were carried as obstacles, so no pad borrowed another pad's neck.
Candidate copper at >= 0.40 mm was allowed to merge, candidate copper below
0.40 mm was not.

### Per-pad result

| pad | layers | topology | narrow | reduced-clr | vias |
|---|---|---|---|---|---|
| R2.1 | B.Cu -> F.Cu | narrow B.Cu dogleg -> POWER via (23.300, 36.000) -> normal F.Cu -> +3V3 trunk x=21.05 | 3.269 | 0.000 | 1 x 0.80/0.40 |
| J1.40 | F.Cu | own neck -> east through `E6_J1_40_CLR` -> normal width -> via (32.350, 78.495) -> B.Cu backbone / R26.1 | 2.890 | 0.709 | 1 x 0.80/0.40 |
| J1.41 | F.Cu | own north neck -> handoff y = 79.330 -> shared display branch | 0.820 | 0.000 | 0 |
| J1.42 | F.Cu | own north neck -> handoff y = 79.330 -> shared display branch | 0.820 | 0.000 | 0 |
| display branch | F.Cu | >= 0.40 mm only, via (29.500, 78.950) -> C13.1 | 0.000 | 0.000 | 1 x 0.80/0.40 |
| R11.1 | B.Cu | narrow east past the `/I2C_SCL_INT` corner -> south -> +3V3 via (17.400, 47.050) / C4.1 | 3.589 | 0.580 | 0 |
| R29.1 | F.Cu | normal width -> `E6_R29_1_WIDTH` neck -> `E6_R29_1_CLR` -> normal width -> existing +3V3 via (9.850, 33.350) | 2.181 | 0.403 | 0 |
| C18.1 | F.Cu -> In2 -> B.Cu | **all normal width**, 0.65/0.40 vias at (18.900, 19.400) and (20.760, 21.730) | 0.000 | 0.000 | 2 x 0.65/0.40 |

Caps: longest reduced-clearance run 0.709 mm (J1.40) against the 2.0 mm hard
cap; longest narrow run 3.589 mm (R11.1) against the 6.0 mm review trigger.

### J1 merge discipline

| pad | own neck | first >= 0.40 node | merge point | merge width |
|---|---|---|---|---|
| J1.40 | (30.250, 80.150) -> (31.965, 78.270) | (31.9650, 78.2700) | via (32.350, 78.495) into the B.Cu +3V3 backbone | 0.40 / via 0.80 |
| J1.41 | (29.750, 80.150) -> (29.750, 79.330) | (29.7500, 79.3300) | (29.550, 78.950) on the shared branch | 0.40 |
| J1.42 | (29.250, 80.150) -> (29.250, 79.330) | (29.2500, 79.3300) | (29.450, 78.950) on the shared branch | 0.40 |

Three separate single-pad necks; every merge happens in >= 0.40 mm copper. No
narrow-to-narrow merge exists anywhere in the pass, so no 0.15 mm neck carries
aggregate display current.

### J1.42 north escape

Achieved handoff **y = 79.330**, inside the verified legal band 79.320 .. 79.342
and at the balance point (+0.010 mm containment margin, +0.011 mm clearance
margin to the GND pad J1.43 corner). The neck is wholly enclosed by
`E6_J1_42_WIDTH` under its new 79.245 north edge; it needs **no** clearance
relief, so `E6_J1_42_CLR` carries 0.000 mm of this route.

### Deviations from the pass brief, and why

1. **J1.41 escapes north, not west.** The west route through `E6_J1_41_CLR` is
   real (its 0.771 mm reduced-clearance pinch past the `/SPI_A_MISO` via at
   (26.000, 81.500) measures out as documented), but west of the pocket there is
   no +3V3 to reach: the only solved continuation ran ~15 mm south-east to
   (32.640, 85.640) before it could via down. The north escape is 0.820 mm of
   neck with zero reduced-clearance copper. J1.41's neck is enclosed by
   `E6_J1_42_WIDTH`, which spans x 28.950-31.550 and therefore covers J1.41's
   pad as well - the DRU width rule is geometric, not pad-scoped, so this is the
   committed rule doing exactly what it says. `E6_J1_41_WIDTH` still encloses the
   neck's southern part; `E6_J1_41_CLR` is unused this pass.
2. **C18.1 needed In2.Cu and a second via.** F.Cu around C18.1 is a closed pocket
   (USB_D_MCU_N north, the y=19.3-19.5 via row west, `/SPI_A_MISO` south), and
   B.Cu below the approved via is closed too (`/SX1262_BUSY` north,
   `/SPI_B_MOSI` south, the `/BMI270_INT1_STRAP` via east). Normal-width routing
   therefore does not fail - it just cannot stay on two layers. The approved
   0.65/0.40 via at (18.900, 19.400) is used exactly as ruled; a second
   0.65/0.40 via at (20.760, 21.730) returns to B.Cu. Zero narrow copper, so
   `E6_C18_1_WIDTH` is untouched and still needs no width relief.
3. **R29.1 uses no new via**, as ruled - it lands on the existing +3V3 via at
   (9.850, 33.350) after a 13 mm normal-width F.Cu trunk down the x=10.0 gap
   between the C45/C47/C49/C51 pad columns.

### Validation

Complete-set validation before any live write: 112 segments and 5 vias checked
for width-area enclosure, clearance under the correct relief, POWER via drill and
annular floors, hole-to-hole between all five new vias, neck-to-neck separation,
foreign +3V3 pad contact, cap limits, and union-find source connectivity -
**0 violations**, all seven pads on the U12.4/U12.5 island. Scratch board with
the identical copper: KiCad DRC **0 violations** with `--refill-zones`.

### Live write and DRC

Fresh writer prefix `b3f7c210`, verified absent first. After the write KiCad DRC
reported 10 violations against **stored** zone fills - all five new vias against
the not-yet-refilled `In1 GND REFERENCE` pour - and **0** with `--refill-zones`.
The board was then refilled and saved, and DRC re-run on the saved board:
**0 electrical errors**.

### Preservation

| quantity | before | after |
|---|---|---|
| track segments | 696 | 808 (+112, 0 removed) |
| vias | 175 | 180 (+5, 0 removed) |
| footprints | 188 | 188, 0 moved |
| pads | 776 | geometry and net identical |
| named zones | 30 | 30, every outline and layer set identical |
| board ratsnest | 361 | 354 |
| +3V3 ratsnest entries | 25 | 18 |
| +3V3 islands | 26 | 19 |

Every added object carries the `b3f7c210` prefix. All locked signal nets - USB,
SPI-A, SPI-B, I2C, SX1262, CC1101, BMI270, display, SD_CS_N and GND - are
track-for-track and via-for-via identical. NFC_IRQ remains 0 tracks / 0 vias /
0 zones. x69.100 remains staged (2 tracks, 2 vias). The `.kicad_dru` was not
touched and no rule area was modified. The large textual diff is KiCad
re-serialising footprint order on the zone refill plus the In1 pour clearing the
five new via holes; the structural audit above is what establishes preservation.

## 2026-08-14 - B3 deviation ruling: J1.41 pad scope, C18.1 second via, R29.1 length

Post-route review of `27358ee` raised three deviations. Rulings and the one
correction they required, applied before `27358ee` was pushed.

### 1. J1.41 using E6_J1_42_WIDTH - REJECTED, corrected

J1.41's 0.15 mm north neck was legal but was authorised by the **wrong area**.
`E6_J1_41_WIDTH` stopped at y = 79.385, so it can only enclose a neck whose
handoff is at y >= 79.460; the legal handoff band set by the 0.20 mm clearance
to the GND pad J1.43 corner is 79.320 .. 79.342. The two do not overlap, so a
J1.41 north escape could not be authorised by its own area at all - it was
leaning entirely on `E6_J1_42_WIDTH`, which spans x 28.950-31.550 and therefore
covers J1.41's pad.

**Correction: `E6_J1_41_WIDTH` north edge 79.385 -> 79.245**, the identical
0.140 mm on the identical arithmetic already ruled for J1.42. Rules only - one
polygon line, two byte-runs, **no copper changed**: J1.41's routed neck already
fits its own area once extended. A dedicated new north area was considered and
rejected as strictly more invasive (it would need a new rule and a new registry
entry for the same effect).

### Pad scope - what the doctrine actually tests

The review asked whether E6 areas must be pad-exclusive. **They cannot be, and
never were.** Measured on the committed board:

| area | J1 pads whose centre it covers |
|---|---|
| `E6_J1_40_WIDTH` | J1.40 |
| `E6_J1_41_WIDTH` | J1.41, J1.42, J1.43, J1.44, J1.45, J1.46, J1.47, J1.48, J1.49, J1.50 |
| `E6_J1_42_WIDTH` | J1.40, J1.41, J1.42 |

On a 0.5 mm pad pitch, rectangles 2-5 mm wide necessarily span neighbours.
Coverage of the non-+3V3 pads is harmless because the rule condition also
requires `hasNetclass('P3V3')`.

The enforceable test is therefore **own-area sufficiency**, not geometric
exclusivity:

> every pad-escape neck must be enclosed by the WIDTH area named for its own
> pad, on its own. Incidental coverage by a neighbouring area is permitted;
> depending on one is not.

Status after the correction:

| pad | own area encloses its neck | also incidentally inside |
|---|---|---|
| J1.40 | YES `E6_J1_40_WIDTH` | `E6_J1_42_WIDTH` |
| J1.41 | YES `E6_J1_41_WIDTH` | `E6_J1_42_WIDTH` |
| J1.42 | YES `E6_J1_42_WIDTH` | `E6_J1_41_WIDTH` |

### Authorisation probes

Scratch boards carrying the real B3 copper; only the rule-area polygons varied.

| probe | `E6_J1_41_WIDTH` | `E6_J1_42_WIDTH` | result | proves |
|---|---|---|---|---|
| P0 | 79.385 | 79.245 | **0** | `27358ee` as committed is DRC-clean |
| P1 | 79.385 | clipped to x <= 29.60 | **1 width error, 0.820 mm track** | J1.41 depended on `E6_J1_42_WIDTH` |
| P6 | 79.385 | 79.385 | **2 width errors, 0.820 mm each** | both north necks need the 0.140 mm |
| P4 | **79.245** | clipped to x <= 29.60 | **0** | after the fix `E6_J1_41_WIDTH` alone carries J1.41 |
| P5 | 79.245, clipped to x >= 29.50 | 79.245 | **0** | J1.42 is self-sufficient on its own area |
| P3 | **79.245** | 79.245 | **0** | the committed fix is clean |

P1 is the defect and P4 is the repair, in the same two lines of geometry.

### 2. C18.1 second 0.65/0.40 via - ACCEPTED

Both vias are **normal-rule**: drill 0.400 >= 0.400 floor, annular 0.125 exactly
at the floor for a 0.65 pad, no E6 area invoked, 0.000 mm narrow, 0.000 mm
reduced clearance. The brief's "one via" was a statement about where *relief*
was needed, not a via budget. A second ordinary via is ordinary routing.

It is also forced: F.Cu around C18.1 is a closed pocket (USB_D_MCU_N north, the
y = 19.3-19.5 via row west, `/SPI_A_MISO` south) and B.Cu under the approved via
is closed too (`/SX1262_BUSY` north, `/SPI_B_MOSI` south, the
`/BMI270_INT1_STRAP` via east). A two-layer C18.1 does not exist; the choice was
In2 plus a second normal via, or a narrow fallback. Normal width won.

### 3. R29.1 ~24.9 mm - ACCEPTED for Beta, with a flagged B4 dependency

Electrically a non-issue: 0.40 mm x 35 um over 24.9 mm is **30.6 mOhm**, 0.3 mV
at 10 mA. No rule caps total normal-width length; narrow (2.181 mm) and
reduced-clearance (0.403 mm) are both far inside their caps, and no via was
added, as ruled.

The real cost is **routing channel**, and it is worth recording precisely. The
trunk runs down the F.Cu gap between the NFC decoupling columns:

* gap C4x.1 east edge 9.550 to C4x.2 west edge 10.450 = **0.900 mm**
* trunk at x = 10.000, 0.40 mm wide, occupies 9.800 .. 10.200
* residual channel 0.250 mm each side - a further 0.20 mm track needs 0.60 mm,
  so **nothing else fits on F.Cu either side**

All four `NFC_VDD_D/A/RF/AM` nets are still unrouted (0 tracks each) and every
one has its bulk cap at x 8.550-9.550, west of the trunk, and its sink at U9,
x 22.2-26.8, east of it - all on F.Cu-only pads. They must now change layer to
cross x = 10.0. Not a block, but four forced vias that did not exist before.

If B4 wants that channel back, the shortening move is a single via near
**(9.050, 19.950)** - verified clear at 0.80/0.40 on the current board - which
drops R29.1 to roughly 3.5 mm. **Not applied**: no via was authorised here.

### Verification after the correction

Seven-pad gate re-run: every +3V3 narrow segment enclosed by a WIDTH area, all
three J1 necks own-area sufficient, all seven pads on the U12.4/U12.5 island,
+3V3 islands 19. DRC **0 electrical errors** with `--refill-zones`, after
`--refill-zones --save-board`, and again on the saved board. 354 unconnected
throughout.

Copper preservation against `27358ee`: **808 tracks and 180 vias identical**,
all 776 pads identical, exactly one zone outline changed (`E6_J1_41_WIDTH`).
The `.kicad_dru` gained a comment only - all 70 rule bodies and every
non-comment line byte-identical.

One pre-existing observation re-confirmed and again not touched: the 0.300 mm
+3V3 segment at (65.500, 52.400)-(66.000, 52.400) on F.Cu sits below the 0.40 mm
P3V3 outer floor and inside no rule area, yet KiCad raises no width error. It
predates B3 (present at `26039e5`), carries no B3 writer prefix, and is outside
every B-pass region.

## 2026-08-14 - +3V3 PASS B4: U3.21 and U9.1

Two pads, seven track segments, **no vias**. B3 was pushed and hard-locked first
(`27358ee` + `db52c7e` -> origin/master), and nothing in B3 was touched.

### Pad model correction found during B4 setup

Before routing near U3 the offline model was found to mis-place pads in
**rotated** footprints. KiCad stores a pad's orientation **absolutely** (it
already includes the footprint rotation) and defaults to 0 when the token is
absent; the model had been adding the footprint angle. U3 sits at 90 degrees, so
its 0.4 x 1.475 pads were being modelled 1.475 wide on a 0.65 pitch - physically
impossible, and the same error affected U1.

Corrected, every footprint on the board now has **zero overlapping
distinct-number pads** (U1, U3, U9, J1, U2, U4, U12 all checked). The fix also
reproduces a figure the eaae455 pass recorded but which the old model could not:
the R2.1 via at (23.300, 36.000) clears B.Cu pad U1.28 by **0.1142 mm**, against
the 0.114 mm in the log.

**B3 was re-validated under the corrected model and is still clean** - all 112
B3 track objects pass width and clearance with the correct relief. J1 and U9 are
unrotated footprints, so the region B3 actually routed was never affected, and
KiCad DRC had been the authority throughout.

### U3.21 - TCA9535 A0 strap

| | |
|---|---|
| layer | B.Cu only, **no via** |
| escape | north stub out of the pad, 0.40 mm, (23.625, 9.400) -> (23.625, 8.150) |
| run | **0.60 mm** east through the J5/U3 corridor, (23.625, 8.150) -> (25.575, 8.150) |
| landing | 0.40 mm south, (25.575, 8.150) -> (25.575, 9.250), onto U3.24 and the +3V3 B.Cu trunk |
| total | 4.300 mm |
| narrow | **0.000 mm** |
| reduced clearance | **0.000 mm** |
| minimum clearance | **0.2500 mm** everywhere |

The corridor between the J5 header pads (bottom y = 7.430) and the U3 pin row
(top y = 8.700) is 1.270 mm; the 0.60 mm run sits at y = 8.150, keeping 0.25 mm
to both. Preferred width was achievable for the run; the two pad stubs are
0.40 mm because U3's 0.65 mm pitch leaves only 0.25 mm either side of the pad.

**HEADER RESERVED usage.** All three segments intersect the reservation
(y < 8.500) and all three are wholly enclosed by `U3_21_ESCAPE`, so the scoped
exception carries them. No other net is involved, no via is placed, In1 GND is
untouched, and no general transit occurs - the copper enters the reservation
only inside the 2.975 x 2.150 mm scoped rectangle.

### U9.1 - ST25R3916 VDD

| | |
|---|---|
| layer | F.Cu only, **no via** |
| neck | 0.15 mm west out of the pad then south through the pinch, (22.100, 20.500) -> (21.5875, 20.500) -> (21.5875, 21.250) -> (21.430, 21.580) |
| handoff | **(21.430, 21.580)**, widen to 0.40 mm |
| landing | 0.40 mm to the existing +3V3 via at (20.760, 21.730) |
| total | 2.315 mm |
| narrow | **1.628 mm** (< 6.0 trigger) |
| reduced clearance | **0.743 mm** (< 2.0 cap) |
| minimum clearance | **0.1875 mm** |

The pinch is between the `/SPI_B_MISO` vertical (east edge x = 21.325) and the
U9 pad column (west edge x = 21.850) - a 0.525 mm channel. A 0.15 mm neck
centred at x = 21.5875 sits **0.1875 mm from each side**, which is above the
committed 0.160 mm relief by 0.0275 mm, so no new relief was needed and none was
requested. Normal width becomes legal again at y = 21.580, just past U9.3, and
the route widens there.

The landing is the +3V3 via at (20.760, 21.730) - the second C18.1 via placed in
B3, now part of the source island. U9.1 therefore joins the island in >= 0.40 mm
copper; its 0.15 mm neck feeds one pad and carries no other pad's current.

A first attempt cut the corner diagonally from the pad and clipped U9.2's
north-west corner at 0.1494 mm. Squaring the escape - straight west, then
straight south - removed it.

### Own-area sufficiency

Every segment of both routes was checked against **every** rule area on the
board. Neither route touches any area other than its own:

| route | enclosed by | intersects |
|---|---|---|
| U3.21 (all 3 segments) | `U3_21_ESCAPE` | `U3_21_ESCAPE`, `HEADER RESERVED` |
| U9.1 (3 neck segments) | `E6_U9_1` | `E6_U9_1` |
| U9.1 (0.40 mm segment) | - (needs no relief) | `E6_U9_1` |

There is **no incidental neighbouring coverage to remove**, so the probe was run
by disabling areas outright:

| probe | configuration | result | proves |
|---|---|---|---|
| P0 | committed board, no B4 copper | **0** | baseline |
| P1 | U9.1 with `E6_U9_1` present | **0** | own area suffices |
| P2 | U9.1 with an unrelated scoped area disabled | **0** | no foreign dependence |
| P3 | U9.1 with **`E6_U9_1` disabled** | **7 violations** | relief is genuinely required |
| P4 | committed state restored, both routes | **0** | final state clean |
| - | U3.21 with **`U3_21_ESCAPE` disabled** | **3 `items_not_allowed`** | the HEADER exception is its only dependency |
| - | U3.21 with an unrelated E6 area disabled | **0** | no unrelated E6 relief used |

P3's failures are worth recording: with `E6_U9_1` gone the neck draws
`netclass 'P3V3' clearance 0.2000; actual 0.1875` **and**
`Pad-escape necking - width, fine-pitch power packages min width 0.2000;
actual 0.1500` - so inside U9's courtyard the E6_U9_1 rules are what supersede
the generic 0.20 mm necking floor. No probe geometry reached the real board.

### Verification

DRC after U3.21 alone: **0**. After U9.1: **0**. After `--refill-zones
--save-board` and re-run on the saved board: **0 electrical errors**.

Source island (independent union-find, seeded only from the island containing
U12.4/U12.5): both U3.21 and U9.1 present, and all seven B3 pads still present.

| quantity | before | after |
|---|---|---|
| track segments | 808 | 815 (+7, 0 removed) |
| vias | 180 | 180 (+0) |
| board ratsnest | 354 | 352 |
| +3V3 ratsnest entries | 18 | 16 |
| +3V3 islands | 19 | 17 |
| source-island pads | 59 | 61 |

Preservation: **all 112 B3 track objects byte-identical**, 188 footprints with
0 moved, all 776 pads identical, **zero zone outline or layer differences** so
every B3 rule area is untouched, and every locked signal net - USB, SPI-A,
SPI-B, I2C, SX1262, CC1101, BMI270, display, SD_CS_N, WAKE_INT_N, GND -
identical. NFC_IRQ still 0/0/0, no RF-band copper or vias added, x69.100 still
staged at 2 tracks / 2 vias. Writer prefix `b4a91d30`, verified absent first;
all seven added objects carry it.

The R29.1 NFC-channel dependency and the 0.300 mm segment at
(65.500-66.000, 52.400) are carried forward unchanged as ruled - neither was
touched, and the banked (9.050, 19.950) via remains deferred.
