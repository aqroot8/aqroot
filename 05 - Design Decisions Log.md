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
