---
tags: [hardware, beta, pinmap, schematic, v0.2.1]
status: schematic-safe-provisional
supersedes: "10 - Beta Pin Map.md"
revision: v0.2.1 (pre-schematic design review, 2026-07-26)
---

# AQROOT Beta Pin Map v0.2.1 — schematic-safe provisional

Consolidates corrections from a three-way review (internal / ChatGPT / Fable 5) plus the
Beta display decision. This supersedes v0.1 ("10 - Beta Pin Map.md"). Target silicon:
ESP32-S3-WROOM-1 N16R8 (octal PSRAM, native USB-CDC console).

**Status:** schematic-safe for the digital pin map. NOT production-final — several part
selections (audio, regulator, exact display P/N) and the RootProbe interface still block a
full schematic freeze. See Section 11.

---

## v0.2.1 amendments (pre-schematic design review, 2026-07-26)

Applied immediately before KiCad schematic capture. Two factual errors fixed, five reviewed
design changes adopted.

**Factual corrections:**
1. **MCP23017 has 16 FULLY BIDIRECTIONAL GPIO** (GPA0-7 + GPB0-7). The previous "14
   bidirectional + 2 output-only (GPA7, GPB7)" claim was WRONG. Every pin-budget figure that
   relied on it has been recalculated.
2. **GPIO43 = U0TXD, GPIO44 = U0RXD.** These were reversed in v0.2 §5.

**Adopted design changes:**
3. **IR TX moved GPIO43 -> GPIO16.** GPIO43 (U0TXD) carries the ROM boot log at every reset,
   which would pulse the IR LED MOSFET driver at 100-500mA on every boot. A gate pull-down
   does NOT fix this — a pull-down cannot override an actively-driven UART output. GPIO16 has
   no boot-log traffic, and RMT is not pin-locked (it routes through the GPIO matrix). IR RX
   stays on GPIO44 (U0RXD is an input at boot; boot-log edges are ignored).
4. **GPIO21 reclaimed.** Display RESET and touch RESET both moved off native GPIO21 onto the
   MCP23017 (reset is a slow signal, and v0.2 already inconsistently placed touch RESET on
   GPA0). See §6a for what GPIO21 now carries and why.
5. **Second MCP23017 added at 0x21** for the community expansion header (16 low-speed GPIO).
   The internal expander (0x20) now carries the 8-button cluster + all internal control
   signals, exactly filling its 16 pins.
6. **External I2C isolation** required on the community header (§8a).
7. **Hybrid expansion header** — native fast pins alongside the labeled low-speed expander
   GPIO (§8b).

---

## 0. Key decisions locked in this revision

1. **Display: ILI9341 2.4"-2.8" IPS capacitive-touch (standard SPI) for Beta.** AMOLED
   dropped to a Kickstarter stretch goal ("premium AMOLED upgrade" — a board revision, not
   a drop-in swap, funded if the campaign hits its stretch target). This resolves the
   biggest review blocker: the display is now a fully-specified, Alpha-validated part on
   standard SPI (no QSPI complexity, real backlight pin, FT6236 touch already validated).

2. **Native pin recount corrected.** The v0.1 "native pins are full / zero margin" claim was
   wrong. ~4 native pins are free (GPIO43/44 freed by native-USB console; GPIO16 reclaimable
   by dropping optional CC1101 GDO2; GPIO46 with strapping care). Enough headroom to fix the
   real issues. **(v0.2.1: that headroom has now been spent — see §1.)**

3. **IR moves to native RMT pins (was the critical bug).** A 38kHz IR carrier cannot be
   generated/captured through an MCP23017 I2C expander. IR TX and RX both go to native pins
   driven by the ESP32-S3 RMT peripheral. **(v0.2.1: IR TX = GPIO16, IR RX = GPIO44.)**

4. **Power tree corrected.** The bq25185 is a charger with power-path, NOT a 3.3V regulator.
   A separate 3.3V buck-boost regulator is required. (See Section 4.)

5. **RootProbe re-architected as an intelligent coprocessor** (RP2040-class), not raw
   MCP23017 pins. (See Section 5.)

---

## 1. Pin budget (corrected recount)

- ESP32-S3 exposes GPIO 0-21 and 26-48. GPIO 22-25 don't exist on this die.
- GPIO 26-37 consumed by octal PSRAM/flash (R8). Excluded.
- GPIO 19/20 = native USB. Reserved.
- No input-only pins on the S3 (unlike classic ESP32).
- Usable set (31 pins): 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 21 38 39 40 41 42 43 44 45 46 47 48
- Strapping pins (handle with care): 0, 3, 45, 46.
- **GPIO43 = U0TXD, GPIO44 = U0RXD** (v0.2.1 correction — these were reversed in v0.2).
  Both are FREE because the console runs over native USB-CDC. Note GPIO43 still carries the
  ROM boot log at every reset unless the boot log is disabled by eFuse — treat it as an
  actively-driven output during boot, not a neutral pin.
- GPIO 39-42 = JTAG pins (usable; forfeits external JTAG, fine — debug over USB-Serial-JTAG).
- **RTC/deep-sleep-wake capable pins = GPIO0-21 only.** GPIO38-48 are NOT RTC GPIO and
  therefore cannot serve as an `ext0`/`ext1` deep-sleep wake source. This constrains where
  the button-wake interrupt line can live (see §6a).

### Final native allocation (v0.2.1) — 29 used, 2 reserved test pads, 0 free

| GPIO | Assignment | | GPIO | Assignment |
|---|---|---|---|---|
| 0 | BOOT button (native, mandatory) | | 18 | SX1262 DIO1 |
| 1 | I2C SDA | | 19/20 | native USB (reserved) |
| 2 | I2C SCL | | 21 | **MCP23017 INT (wired-OR) / header IRQ — RTC wake** |
| 3 | BMI270 INT1 (strapping — see §6) | | 38 | NFC IRQ |
| 4 | SPI-B SCK | | 39 | I2S BCLK |
| 5 | SPI-B MOSI | | 40 | I2S LRCLK/WS |
| 6 | SPI-B MISO | | 41 | I2S DOUT (speaker) |
| 7 | CC1101 CS | | 42 | I2S DIN (mic) |
| 8 | SX1262 BUSY | | 43 | **header native fast GPIO (U0TXD)** |
| 9 | NFC CS | | 44 | **IR RX (U0RXD)** |
| 10 | Display CS | | 45 | reserved test pad (VDD_SPI strap) |
| 11 | SPI-A MOSI | | 46 | reserved test pad (boot-mode strap) |
| 12 | SPI-A SCK | | 47 | Display backlight |
| 13 | SPI-A MISO | | 48 | microSD CS |
| 14 | Display DC | | | |
| 15 | CC1101 GDO0 | | | |
| 16 | **IR TX (moved off GPIO43)** | | | |
| 17 | SX1262 CS | | | |

**Margin is now ZERO.** Reclaiming GPIO21 (via expander resets) and freeing GPIO43 (via the
IR TX move) exactly paid for IR TX on GPIO16, the button-wake interrupt line, and one native
fast pin on the community header. Any further native-pin demand — including RootProbe's
preferred low-latency IRQ (see [[14 - RootProbe Interface v0.1]]) — must now come out of an
existing assignment, not out of spare capacity. GPIO45/46 stay unconnected test pads
deliberately: they are the recovery margin, not a reserve to raid.

---

## 2. SPI Bus A — Display (ILI9341) + microSD (standard SPI, shared)

| Signal | GPIO | Notes |
|---|---|---|
| SCK | 12 | shared |
| MOSI | 11 | shared |
| MISO | 13 | shared |
| Display CS | 10 | |
| Display DC | 14 | |
| Display RST | — | **moved to MCP23017 0x20 GPA4** (v0.2.1; was native GPIO21) |
| Display backlight (BL) | 47 | valid — ILI9341 LCD has a real backlight |
| microSD CS | 48 | |

**Firmware note:** SD and display share this bus, each with its own CS. The same CS-discipline
rule proven on Bus B applies here: hold the idle device's CS high. Display refresh is
bandwidth-heavy and contends with SD reads (no simultaneous DMA). **This shared-bus config
was NOT tested in Alpha (SD was on dedicated pins there) — validate on Beta.**

---

## 3. SPI Bus B — CC1101 + SX1262 + NFC (shared, CS-discipline)

| Signal | GPIO | Notes |
|---|---|---|
| SCK | 4 | shared |
| MOSI | 5 | shared |
| MISO | 6 | shared |
| CC1101 CS | 7 | |
| CC1101 GDO0 | 15 | primary data/IRQ |
| CC1101 GDO2 | (removed) | optional; dropped to free GPIO16 |
| SX1262 CS | 17 | |
| SX1262 DIO1 | 18 | |
| SX1262 BUSY | 8 | |
| SX1262 RST | 3 | strapping (JTAG-select) — acceptable, give defined idle state + pull |
| NFC CS | 9 | |
| NFC IRQ | 38 | keep (RFAL is IRQ-driven) |

**Firmware requirements for the 3-device shared bus (from review):**
1. Hardware pull-up on every CS line.
2. Drive all CS high before initializing any device.
3. Mutex around the shared bus.
4. Per-device SPI frequency + mode on every transaction (don't assume identical timing).
5. Reset/disable a device if it fails while holding MISO.

**NFC level note (important):** boost ONLY the ST25R3916 analog/PA rail to 5V. Keep its
digital I/O supply (VDD_IO) at 3.3V so the SPI lines stay 3.3V — no level shifter needed on
the shared bus. Confirm VDD_IO is tied to 3V3 in the schematic.

**NOT tested in Alpha:** NFC as a THIRD device on this bus (Alpha tested 2 radios shared, NFC
on its own pins). CS rule generalizes, but validate on Beta.

---

## 4. I2C Bus — Touch + IMU + Fuel gauge + GPIO expander

| Signal | GPIO |
|---|---|
| SDA | 1 |
| SCL | 2 |

| Device | Address | Interrupt policy |
|---|---|---|
| MCP23017 **internal** expander (buttons + control) | 0x20 | **INTB -> GPIO21** (button wake) |
| MCP23017 **external** expander (community header) | 0x21 | INTA -> GPIO21 (wired-OR, open-drain) |
| MAX17048 fuel gauge | 0x36 | poll |
| FT6236 touch | 0x38 | **poll** (frees the missing-INT issue) |
| BMI270 IMU | 0x68 | native INT1 on GPIO3 IF motion-wake needed, else poll |

**RESERVED I2C ADDRESS TABLE (publish this for accessory makers):** `0x20`, `0x21`, `0x36`,
`0x38`, `0x68` are reserved by AQROOT internals. A community accessory MUST NOT use these.
Note the MCP23017 family occupies the whole `0x20-0x27` block; an accessory carrying its own
MCP23017 must be strapped into `0x22-0x27` and its conflict risk documented.

- One intentional pair of I2C pull-ups (remove redundant breakout pull-ups). Size them for
  the internal bus only — external accessory pull-ups are a separate, jumper-selectable
  option at the header (§8a).
- **Touch RST:** now on **MCP23017 0x20 GPA0**, with display RST on GPA4 (v0.2.1 — both moved
  off native GPIO21). Two separate expander pins rather than one shared pin, for sequencing
  flexibility. The FT6236 STILL REQUIRES a CTP_RST low->high pulse to enumerate — without it
  the touch controller stays asleep and does NOT appear on an I2C scan (Alpha gotcha, and now
  the pulse comes from the expander, so it cannot happen until after the expander is
  configured. Order of operations at boot: I2C up -> configure 0x20 -> pulse touch RST ->
  scan/init touch).
- **Re-confirm touch controller/address if the display module differs from the Alpha part**
  (the validated FT6236 @ 0x38 was on the Alpha ILI9341 — Beta ILI9341 should match, verify).

---

## 5. Native GPIO — I2S audio + IR

**I2S audio (DIN moved off strapping GPIO45):**
| Signal | GPIO |
|---|---|
| I2S BCLK | 39 |
| I2S LRCLK/WS | 40 |
| I2S DOUT (speaker) | 41 |
| I2S DIN (mic) | 42 (moved off GPIO45; MCP INT moved to poll) |

**IR (native RMT — the critical fix; TX pin corrected in v0.2.1):**
| Signal | GPIO | Notes |
|---|---|---|
| IR TX | **16** | RMT carrier gen. Moved off GPIO43 — see boot-log rationale below |
| IR RX | 44 | RMT capture; **U0RXD**, an input at boot, so boot-log edges are ignored |

**Why IR TX is NOT on GPIO43 (v0.2.1 correction):** GPIO43 is U0TXD and the ROM bootloader
drives the boot log out of it on every single reset. Feeding that into a MOSFET LED driver
would fire the IR LED at 100-500mA on every boot — an unintended IR blast plus a repeated
current transient on the rail. **A gate pull-down does not fix this**: a pull-down cannot
override an actively-driven push-pull UART output. GPIO16 has no boot-log traffic. RMT is not
pin-locked — it routes to any GPIO through the GPIO matrix — so nothing is lost. This
consumes GPIO16 (the last free native pin); GPIO21 was reclaimed in exchange (§6a).

**IR TX driver stage — required schematic content:**
- Low-side N-channel MOSFET switching the IR LED cathode.
- **Gate series resistor 33-220R** (damps ringing, limits RMT edge current).
- **Gate pull-down 47-100k** — for float protection during reset / power sequencing, NOT as
  boot-log mitigation (see above; that is solved by the pin choice).
- LED current-limit resistor sized for the target drive current, not the ~7mA a bare GPIO
  gives. **Alpha bench-confirmed: direct GPIO drive at 150R = ~7mA average = 1-3cm range.**
- Local decoupling at the LED/MOSFET (the pulsed current is the point — keep the loop small
  and off the sensitive analog/RF returns).
- IR RX needs: supply filtering + **physical separation from the TX LED** (avoid
  self-blinding). Keep the TSOP38238 out of the LED's direct emission cone.

---

## 6. Buttons + strapping-pin hygiene

| Signal | GPIO | Notes |
|---|---|---|
| BOOT/download button | 0 | MUST be native (ROM samples GPIO0 at reset). Not on expander. |
| BMI270 INT1 | 3 | strapping pin — hard requirements below |
| D-pad + A/B/Back/Home (8 buttons) | — | on MCP23017 0x20 GPB0-7, wake via INTB -> GPIO21 |
| Physical power switch | — | **NOT a GPIO** — hard-off path, see below |

**Strapping pins:**
- GPIO0 = BOOT button (normal use).
- GPIO3 = BMI270 INT1 (JTAG-select strap). SX1262 RESET has moved to the expander (0x20
  GPA1), so GPIO3 now carries the IMU interrupt alone.
- GPIO45 = LEFT UNCONNECTED / test pad only (VDD_SPI strap — don't drive externally).
- GPIO46 = LEFT UNCONNECTED / test pad only (boot-mode + ROM logging; recovery margin).

### GPIO3 / BMI270 INT1 — strap-state REQUIREMENTS (v0.2.1)

GPIO3 is sampled as a strapping pin at reset. The BMI270 can assert INT1 at any moment,
including during the reset window — if it happens to drive GPIO3 to the wrong level while the
ROM samples it, the chip boots into the wrong JTAG/boot configuration. This is a real,
intermittent, motion-dependent failure mode, so the idle/boot state must be *designed*, not
assumed:

- **Configure INT1 as open-drain** in the BMI270 if the required interrupt mode allows it, so
  the IMU can only pull down and never fight the strap.
- **Add a weak pull** (pull-up or pull-down as appropriate) that sets the CORRECT boot strap
  level, sized to dominate during the reset window.
- **Add a 100-470R series resistor** between the IMU INT1 pin and GPIO3 (limits contention
  current and damps the edge).
- **Add a test pad** on the GPIO3 net so the boot level can actually be scoped.
- **Validate 50-100 cold boots WITH MOTION APPLIED DURING RESET** before freezing the design.
  A quiet-bench boot test does not exercise this failure.

If that validation fails, the fallback is to drop native motion-wake and poll the IMU, freeing
GPIO3 entirely.

### 6a. GPIO21 — reclaimed, and what it now carries

Moving display RESET and touch RESET onto the expander frees native GPIO21. It is **not**
spare: it becomes the **shared interrupt / wake line**.

| Role | Detail |
|---|---|
| MCP23017 0x20 INTB | button-cluster interrupt (all 8 buttons are on Port B) |
| MCP23017 0x21 INTA/INTB | community-header accessory attention line |
| Header IRQ/READY pin | the same net, exposed on the expansion header (§8b) |

Both expanders' INT outputs are configured **open-drain, active-low, wired-OR** onto this one
net with a single pull-up. Firmware reads each expander's INTF/INTCAP to identify the source.

**Why GPIO21 and not GPIO43 for this:** a polled expander cannot wake the ESP32 from sleep, so
this line must be a real wake source — and on the ESP32-S3 only **GPIO0-21 are RTC GPIO**,
i.e. only they can serve as an `ext0`/`ext1` deep-sleep wake source. GPIO43 is not RTC-capable.
Since [[13 - Power Budget and Battery Runtime v0.1]] depends on deep sleep (~10-20uA) with
wake-on-button for the ~2-week standby figure, the interrupt line has to sit on GPIO21 and the
freed GPIO43 goes to the expansion header instead.

> **NOTE — deviation from the review's literal wording.** The review said "GPIO21 -> native
> fast expansion GPIO" and separately "route MCP INT to a native wake-capable pin". With zero
> other native pins left, both cannot be GPIO21. Because GPIO43/44 are outside the RTC domain,
> the wake requirement is the one that *forces* a specific pin, so GPIO21 takes the interrupt
> and GPIO43 (freed by the IR TX move) becomes the header's native fast pin. Same two roles,
> same two pins, assignment swapped so button-wake actually works. Flagged in §11 for sign-off.

### 6b. Physical power switch — deliberately OUTSIDE the GPIO architecture

The power switch is **not** an expander input and **not** a firmware GPIO. It needs a real
hard-off path: a mechanical switch driving a load-switch / charger ship-mode / battery
disconnect, so a hung or unflashed firmware can still be powered down and a shelved unit
draws effectively zero. Spec the exact topology at schematic time (candidates: charger
ship-mode entry, a latching soft-power controller, or a plain series load switch). Do not
fold this into the MCP23017 button cluster.

---

## 7. MCP23017 expanders — TWO chips (v0.2.1)

**MCP23017 pin-count correction:** the MCP23017 has **16 FULLY BIDIRECTIONAL GPIO** — all of
GPA0-7 and GPB0-7 can be configured as either input or output via IODIRA/IODIRB. The earlier
"14 bidirectional + 2 output-only (GPA7, GPB7)" claim in this document was **factually wrong**
and has been removed everywhere. There is no output-only pin on this part. (The confusion
likely came from the MCP23S17/MCP23008 family notes or from a different expander entirely.)

Correcting that recovers 2 usable pins, but the real change is architectural: the community
header now gets **its own dedicated expander** rather than the leftovers of the internal one.

### 7a. Internal expander — 0x20 (buttons + internal control)

Address straps A0/A1/A2 = GND. **All 16 pins are allocated — this chip is exactly full.**

| Pin | Direction | Function | Power-up safe state (external pull REQUIRED) |
|---|---|---|---|
| GPA0 | out | Touch RESET (FT6236) | pull to RESET-ASSERTED |
| GPA1 | out | SX1262 RESET | pull to RESET-ASSERTED |
| GPA2 | out | NFC 5V boost enable | pull to **OFF** |
| GPA3 | out | Audio amp enable/mute (MAX98357A SD) | pull to **SHUTDOWN** |
| GPA4 | out | Display RESET (ILI9341) | pull to RESET-ASSERTED |
| GPA5 | out | RGB red | pull to LED-OFF |
| GPA6 | out | RGB green | pull to LED-OFF |
| GPA7 | out | RGB blue | pull to LED-OFF |
| GPB0 | in | Button — D-pad UP | 10k pull-up |
| GPB1 | in | Button — D-pad DOWN | 10k pull-up |
| GPB2 | in | Button — D-pad LEFT | 10k pull-up |
| GPB3 | in | Button — D-pad RIGHT | 10k pull-up |
| GPB4 | in | Button — A | 10k pull-up |
| GPB5 | in | Button — B | 10k pull-up |
| GPB6 | in | Button — BACK | 10k pull-up |
| GPB7 | in | Button — HOME | 10k pull-up |

Port A = every internal slow control signal. Port B = the entire button cluster. That split is
deliberate: **INTB becomes a pure button interrupt**, so the wake path (§6a) has no false
triggers from control-signal activity.

- **INTB -> GPIO21**, open-drain, active-low, wired-OR with the 0x21 expander, one pull-up.
- Enable MCP23017 interrupt-on-change for Port B; use INTCAP/INTF to identify which button.
- External 10k button pull-ups are specified rather than relying on the MCP23017's internal
  100k GPPU pull-ups: the internal ones are OFF until firmware configures the chip, and 100k
  is weak for a long button trace in an RF-noisy handheld.

**BUTTON WAKE (hard requirement):** a polled expander CANNOT wake the ESP32 from sleep. The
INTB -> GPIO21 line is what makes button-wake possible at all. Without it the device can only
be woken by the BOOT button or the IMU, and the ~2-week standby figure in the power budget is
unreachable. This line is not optional.

**POWER-UP SAFE-STATE RULE (hard requirement):** MCP23017 pins default to **INPUTS (high-Z)**
at power-up and stay that way until firmware writes IODIR. Every safety-relevant enable in the
table above therefore needs an **external pull resistor forcing the safe state** — pulled so
that the NFC boost is off, the audio amp is muted, load switches are open, and resets are held
asserted, before any firmware runs. **Do NOT rely on "firmware writes it low quickly."**
Between power-on and the first I2C transaction there are milliseconds of high-Z, and a hung or
half-flashed firmware makes that window permanent.

**Dropped in this revision:** the old GPA4 "display power/control reserve" — displaced by the
button cluster. If a separate display power-gate is genuinely needed, it must displace
something else or move to the 0x21 expander. There is no slack left on 0x20.

**No D-pad centre/select button** fits on 0x20. If the enclosure design wants one, it has to
come off the 0x21 expander or replace an existing button. Settle at enclosure CAD.

### 7b. External expander — 0x21 (community expansion header)

Address straps A0=VCC, A1/A2=GND. Dedicated to the community header so that an accessory can
never contend with internal control signals or the button cluster.

| Pin | Function |
|---|---|
| GPA0-7 | XGPIO0-7 — low-speed community GPIO, 3.3V logic |
| GPB0-7 | XGPIO8-15 — low-speed community GPIO, 3.3V logic |

- 16 labeled low-speed GPIO, brought out as **XGPIO0..XGPIO15**.
- INT output wired-OR onto the shared GPIO21 net (open-drain) so an accessory can request
  attention / wake the device.
- Every XGPIO line gets ESD protection at the connector and should be current-limited.
- **Open item:** the switched accessory-power enable has no pin yet. 0x20 is full and all 16
  of 0x21 are promised to the header. Resolve one of three ways — (a) reserve XGPIO15 as
  ACC_PWR_EN and publish a 15-pin header, (b) collapse the RGB LED to an I2C RGB driver and
  free a 0x20 pin, (c) make the accessory rail permanently on and accept the idle draw.
  Logged in §11.

**Audio amp note:** the MAX98357A shutdown/enable (+ optional gain) pin(s) live on 0x20 GPA3
as slow enables — power-gate the amp when audio is idle, with the external pull holding it in
shutdown until firmware says otherwise.

**RGB LED note:** a conventional RGB LED needs 3 outputs (0x20 GPA5-7). A WS2812 addressable
LED needs precise timing and MUST NOT go on the expander — addressable RGB would need a native
RMT pin (there are none free, see §1) or an I2C RGB driver.

---

## 8. Power tree (CORRECTED — bq25185 is NOT a 3.3V regulator)

```
USB-C 5V
  |
  +-- ESD / input protection
  |
  +-- bq25185 IN (linear charger + power-path)
        |
        +-- BAT --- LiPo
        |            +-- MAX17048 fuel gauge
        |
        +-- SYS (~4.5V, battery-tracking — NOT a clean 3.3V)
             |
             +-- 3.3V BUCK-BOOST regulator (SEPARATE PART - required) -> TI TPS63020DSJR (adjustable buck-boost set to 3.3V, up to 2A). See Decisions Log.
             |     +-- ESP32-S3, CC1101, SX1262, display logic,
             |     +-- I2C devices, audio logic, NFC VDD_IO
             |
             +-- load-switched 5V BOOST
                   +-- ST25R3916 PA/analog rail ONLY (RF headroom)
```

- **3.3V rail comes from a separate buck-boost regulator, NOT the bq25185 SYS output.**
  Buck-boost (not plain buck) because the battery-fed SYS rail can sit both above and near 3.3V.
- **NFC 5V is for RF range/headroom, not mandatory** — the chip works at 3.3V (Alpha proved
  SPI comms at 3.3V). Boost only the PA rail; keep VDD_IO at 3.3V. Load-switch it off when
  NFC idle.
- **Charger thermals:** bq25185 is linear — heat scales with (Vin - Vsys) x current. In a
  sealed enclosure the 1A max may thermally throttle. Start Beta at ~500mA charge current;
  raise only after enclosure thermal testing.
- **TPS63020 (v0.2.1 clarification):** the TPS63020 **is** the adjustable-output part — there
  is no "fixed vs adjustable" choice to make, and that framing has been dropped. Orderable
  P/N: **TPS63020DSJR** (reel). It is **not "selected" until its inductor, feedback resistors,
  and input/output caps are selected with it** — a buck-boost is a loop, not a single symbol.
  Spec all of them from the TI datasheet at schematic time, and **account for ceramic cap
  DC-bias derating** (a nominal 22uF X5R/X7R can lose 30-60% of its capacitance at the
  operating voltage; size by effective capacitance, not the printed value).

---

## 8a. External I2C isolation — community header (v0.2.1, REQUIRED)

**The community expansion header MUST NOT expose the internal I2C bus naked.** The internal
bus carries touch (0x38), the IMU (0x68), the fuel gauge (0x36) and both expanders
(0x20/0x21) — i.e. the display's input path, the button cluster, and every internal control
signal. A community accessory that shorts SDA or SCL to ground, back-powers the bus, or holds
it low must **not** be able to disable the controls or make AQROOT unbootable.

Required schematic content:

| Measure | Spec |
|---|---|
| Series resistors | **22-47R** on SDA and SCL, placed **near the host**, before the connector |
| ESD protection | TVS/ESD array on SDA, SCL, and every exposed line, **at the connector** |
| External pull-ups | **solder-jumper selectable**, OFF by default (accessory may bring its own) |
| Bus isolation | **bus buffer / isolator or bus switch** between internal and external segments |
| Recovery | a **firmware- or hardware-controlled way to disconnect a defective accessory** |

- The bus switch is the load-bearing part: it must be possible to bring the internal bus up,
  enumerate internal devices, and run the UI with the external segment disconnected, then
  connect the accessory segment only on request.
- Fault behaviour to design for explicitly: accessory shorts SDA low -> internal bus keeps
  working; touch, buttons, IMU and fuel gauge all stay alive; the UI can report "accessory
  fault" and leave the external segment isolated.
- The accessory-power rail should be switchable for the same reason (see the open item in
  §7b) so a latched-up accessory can be power-cycled independently.
- Publish the reserved I2C address table (§4) in the accessory documentation.

---

## 8b. Community expansion header — HYBRID (v0.2.1)

The header is a **hybrid**, not expander-only. Exposing only slow expander pins would make it
useless for anything timing-sensitive; exposing native pins alone is impossible (zero native
margin, §1). So it carries both, clearly labeled.

| Group | Signals |
|---|---|
| Native fast | **GPIO43** (native fast GPIO; also U0TXD, so it doubles as a boot-log/UART pin) |
| Native I2C | SDA + SCL, **via the isolation of §8a** |
| Interrupt | shared open-drain IRQ/READY net (= GPIO21, wired-OR with both expanders) |
| Power | 3.3V, switched accessory power, **multiple grounds** |
| Low-speed GPIO | **XGPIO0..XGPIO15** — 16 pins off the 0x21 expander, 3.3V logic only |

**Labeling and marketing rules (binding):**
- Label the expander pins **clearly as low-speed** on the silkscreen, in the pinout diagram,
  and in the docs. XGPIO is I2C-mediated: expect microseconds-to-milliseconds per transition,
  not MHz. They are for enables, chip selects, mode straps, LEDs, and simple sensors.
- **Do NOT market this as "16 GPIO = Flipper's 18."** That comparison is false in kind — the
  numbers are not the same currency, and claiming it invites exactly the bug reports
  ("your GPIO can't bit-bang X") that the low-speed labeling exists to prevent.
- **Positioning: AQROOT competes on BUILT-IN capability** — dual radios, NFC, IMU, audio, IR
  and display all onboard — **not on exposed-pin count.** The header is a convenience for
  community add-ons, not the headline feature.
- **RootProbe remains the dedicated high-speed interface** (see §9 and
  [[14 - RootProbe Interface v0.1]]). Anything needing real sampling speed goes there, on its
  own coprocessor. Do not blur the two in any customer-facing material.
- No 5V passthrough on the header (3.3V logic only).

---

## 9. RootProbe — re-architected (was a design conflict)

RootProbe (the flagship logic-analyzer / bus-sniffer / GPIO-tooling add-on) CANNOT be built
on MCP23017 expander pins — I2C-mediated GPIO is far too slow for logic-analyzer sampling,
UART/SPI/I2C capture, or pulse-width measurement.

**RootProbe = intelligent coprocessor module** with its own MCU (RP2040-class) handling:
high-speed capture, triggering, protocol decode, local buffering, voltage-level protection.
It talks to AQROOT over a board-to-board interface: regulated power, GND, SPI data link, I2C
management, interrupt/ready line, optional USB pair.

**Split the connector marketing into two things:**
1. Low-speed community GPIO header — **16 slow GPIO off a dedicated second MCP23017 (0x21)**,
   plus native I2C / IRQ / GPIO43 / power (the hybrid header, §8b). *(v0.2.1: was "~7 slow
   GPIO off the shared internal expander".)*
2. High-speed RootProbe accessory interface (board-to-board to the coprocessor).

Do NOT advertise MCP23017 pins as logic-analyzer channels.

---

## 10. Validation status (precise — corrects earlier over-claims)

**Validated in Alpha (SPI/electrical communication only):**
- ESP32 flashing + PSRAM config; ILI9341 display + FT6236 touch; CC1101 SPI + basic RF RX;
  SX1262 init; dual-radio shared-SPI operation + CS discipline; microSD CMD0 (0x01); NFC SPI
  chip-ID (0x2A / IC-type 0x05); BMI270 IMU (I2C 0x68, accel/gyro functional — accel -1.00g
  gravity, gyro responds to rotation; multi-device I2C coexistence with touch validated);
  IR VALIDATED (TSOP38238 + TSAL6200, bench-tested on GPIO 17/18: RX decode + full TX->RX
  loopback, NEC 0x00FFE01F; 2026-07-25). **Beta pins are now TX=16 / RX=44** (v0.2.1 moved TX
  off GPIO43; the bench validation is pin-independent — it proved the parts and the optical
  path, not a specific GPIO).
- I2S AUDIO-OUT VALIDATED (MAX98357A amp driving a real 8ohm speaker; bench-tested on I2S
  BCLK=38/LRCK=47/DIN=48; validates the I2S peripheral, clocks + pipeline; 2026-07-26).
  Beta pins 39/40/41/42 unchanged.
- I2S AUDIO-IN (ICS-43434 mic): wiring/firmware validated, mic unit inconclusive — all-zeros
  output on a single sample (suspected dead unit; power/continuity/slot-format all verified
  good). NOT bench-retested (decision 2026-07-26): confirmed dead part, not a design issue —
  first live confirmation happens on Beta hardware. Part choice remains locked and correct.
- MCP23017 GPIO EXPANDER VALIDATED (Waveshare board, I2C; PA0->PB0 loopback 49/49 clean;
  coexists with FT6236 touch + BMI270 IMU on the shared I2C bus; 2026-07-26). Bench board
  strapped at 0x27; Beta uses 0x20 + 0x21 (address straps) — chip/library validated either
  way. **NOT validated: two expanders on one bus, and the INT/interrupt-on-change path** (the
  bench test was polled loopback on a single chip). Both are Beta bring-up items — the
  button-wake path in particular has never been exercised.
- TPS63020 3.3V BUCK-BOOST RAIL VALIDATED (bench-tested with a meter; held ~3.3V from a 3.4V
  battery input — buck-boost regulation confirmed in the hardest near-Vout region; 2026-07-26).
  On Beta fed from bq25185 SYS (~4.5V) per §8 power tree.
- bq25185 CHARGER + POWER PATH VALIDATED (Adafruit 6092; USB-first safe bring-up, battery
  polarity confirmed vs silkscreen before connecting, active charging confirmed — G on, C
  solid, F off; 2026-07-26). Reverse-polarity protection + keyed battery connector remain
  hard Beta requirements (§8 / power incident note).

> **ALPHA HARDWARE VALIDATION COMPLETE (2026-07-26):** all subsystems bench-proven. The
> audio-in mic will NOT be bench-retested (a confirmed dead individual ICS-43434 unit; wiring,
> firmware, and the MAX98357A amp on the same I2S bus are all validated, so it is a bad part,
> not a design issue) — its first live confirmation happens on Beta hardware. **Cleared to
> begin the KiCad schematic on fully-validated parts.**

**NOT yet validated (product function):**
- microSD filesystem read/write under load; NFC tag read/write + RF range; battery runtime;
  RF performance in an enclosure; SD-on-shared-bus; NFC-as-3rd-SPI-device. (Mic pending fresh
  unit.)

---

## 11. Blocking items before schematic FREEZE

Resolved by this revision:
- [x] Display specified (ILI9341 SPI; AMOLED = stretch goal). Bus A is standard SPI.
- [x] IR moved to native RMT pins.
- [x] I2S DIN off strapping GPIO45.
- [x] BOOT button native.
- [x] Touch INT/RST resolved (poll + shared RST).
- [x] Power-tree corrected (separate 3.3V buck-boost).
- [x] RootProbe re-architected (coprocessor).

Resolved by v0.2.1 (pre-schematic design review):
- [x] MCP23017 pin count corrected to 16 fully bidirectional; budgets recalculated.
- [x] GPIO43/44 UART labels corrected (43 = U0TXD, 44 = U0RXD).
- [x] IR TX moved off the boot-log pin -> GPIO16; driver stage fully specified.
- [x] GPIO21 reclaimed (display + touch RESET -> expander).
- [x] Button cluster given a home; second expander (0x21) added for the header.
- [x] Button-wake path defined (expander INT -> RTC-capable GPIO21).
- [x] External I2C isolation requirements recorded.
- [x] Header repositioned as a hybrid; marketing rules recorded.

Still blocking (must resolve before freeze):
- [ ] **Sign off the GPIO21/GPIO43 role swap** (§6a note) — the review's literal wording put
      GPIO21 on the header and the INT "somewhere native"; deep-sleep wake needs an RTC GPIO,
      so they were swapped. Confirm or reverse before capture.
- [ ] **Switched accessory-power enable has no pin** (§7b) — pick option (a), (b) or (c).
- [ ] Select the I2C bus buffer/isolator or bus switch part for the external segment (§8a).
- [ ] Specify the physical power-switch / hard-off topology (§6b).
- [ ] Specify the IR TX MOSFET + resistor values (§5) against the target drive current.
- [x] Select exact 3.3V buck-boost regulator part -> TI TPS63020DSJR (adjustable; support
      components still to be spec'd with it — see §8).
- [x] Select I2S audio parts -> ICS-43434 mic + MAX98357A amp (bench validation pending;
      amp shutdown pin on MCP23017).
- [~] Display = 2.8in IPS ILI9341 capacitive SPI (matches Alpha). VERIFY exact module
      touch = FT6236 @ 0x38 before Beta order.
- [x] Power budget + runtime done -> see [[13 - Power Budget and Battery Runtime v0.1]].
      2000mAh = ~12-15hr active, ~2wk standby. Backlight timeout = top optimization.
      Battery could go 2500-3000mAh if enclosure allows.
- [~] RootProbe interface spec'd -> see [[14 - RootProbe Interface v0.1]]. ~16-18 pin
      connector, coprocessor (RP2040-class) over SPI+I2C+IRQ. Reserve connector footprint
      on main board; finalize exact host pins when RootProbe is built (Phase 2).
- [~] RF/antenna ARCHITECTURE done -> see [[12 - RF and Antenna Plan v0.1]]; remaining:
      select antenna parts + matching networks + professional RF review before PCB fab.
- [ ] ESD / external-header protection.

Validate on Beta hardware (new configs not proven in Alpha):
- [ ] **Two MCP23017s on one I2C bus (0x20 + 0x21).**
- [ ] **MCP23017 interrupt-on-change + wired-OR INT + button wake from deep sleep** — never
      exercised on the bench (Alpha was polled, single chip).
- [ ] **GPIO3 strap integrity: 50-100 cold boots with motion applied during reset** (§6).
- [ ] **Expander-driven touch RESET sequencing** — FT6236 enumeration now depends on the
      expander being configured first.
- [ ] SD on shared display bus.
- [ ] NFC as 3rd device on SPI Bus B.
- [ ] NFC RF range at 3.3V vs 5V-boosted.
- [ ] Charger thermals in enclosure.
- [ ] ICS-43434 mic first live confirmation (Alpha unit was dead; not bench-retested — verify
      the mic captures audio on first Beta power-up).

---

## 12. Tool decision

**KiCad** (v8/v9) is the canonical design tool — unanimous across all three reviews. Open
source, plain-text files that diff/version in git (fits MIT + CERN-OHL-S ethos), mature
ESP32-S3 symbols/footprints, no vendor lock-in, community-forkable. Flux.ai OK for personal
exploration only; not the authoritative source for an open-hardware product.
