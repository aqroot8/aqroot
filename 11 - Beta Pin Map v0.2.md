---
tags: [hardware, beta, pinmap, schematic, v0.2.4]
status: schematic-safe-provisional
supersedes: "10 - Beta Pin Map.md"
revision: v0.2.4 (GPIO expander part change MCP23017 -> TCA9535PWR, 2026-07-27)
---

# AQROOT Beta Pin Map v0.2.4 — schematic-safe provisional

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

> **HISTORICAL SECTION — read with v0.2.4.** The v0.2.1/v0.2.2/v0.2.3 notes below record what
> changed and when, using the part and pin names that were current at the time. **The expander
> part is no longer the MCP23017 — it is the TI TCA9535PWR (U60/U61) as of v0.2.4.** Every
> `GPAn`/`GPBn` name, every `INTA`/`INTB` reference, and every MCP23017 register or
> interrupt-on-change assumption in these three revision notes is **DEAD NOMENCLATURE**. The
> authoritative maps are §7a (U60) and §7b (U61); the authoritative register set is §7c. Do not
> design from the names in this block.

**Factual corrections:**
1. **The 0x20/0x21 expander was confirmed to have 16 fully bidirectional GPIO.** The previous
   "14 bidirectional + 2 output-only" claim was WRONG for the part in use at the time, and every
   pin-budget figure that relied on it was recalculated. *(v0.2.4: this conclusion did not
   survive re-checking against current MCP23017 I2C silicon — see the v0.2.4 correction note,
   which is why the part changed. The TCA9535PWR now in use genuinely has 16 bidirectional
   I/O.)*
2. **GPIO43 = U0TXD, GPIO44 = U0RXD.** These were reversed in v0.2 §5.

**Adopted design changes:**
3. **IR TX moved GPIO43 -> GPIO16.** GPIO43 (U0TXD) carries the ROM boot log at every reset,
   which would pulse the IR LED MOSFET driver at 100-500mA on every boot. A gate pull-down
   does NOT fix this — a pull-down cannot override an actively-driven UART output. GPIO16 has
   no boot-log traffic, and RMT is not pin-locked (it routes through the GPIO matrix). IR RX
   stays on GPIO44 (U0RXD is an input at boot; boot-log edges are ignored).
4. **GPIO21 reclaimed.** Display RESET and touch RESET both moved off native GPIO21 onto the
   internal expander (reset is a slow signal, and v0.2 already inconsistently placed touch
   RESET on a different expander pin). See §6a for what GPIO21 now carries and why.
5. **Second expander added at 0x21** for the community expansion header. *(Superseded in
   v0.2.2: the header publishes 15 user GPIO, not 16 — the 16th pin is ACC_PWR_EN. The
   internal 0x20 expander carries a 7-button cluster, not 8. In v0.2.4 the 16th internal pin
   is U60 P17 = ROOTPROBE_IRQ_READY_N, a live assignment.)*
6. **External I2C isolation** required on the community header (§8a).
7. **Hybrid expansion header** — native fast pins alongside the labeled low-speed expander
   GPIO (§8b).

## v0.2.2 — pin-budget resolution (2026-07-26)

The three items v0.2.1 left open are now closed. No pin assignment from v0.2.1 changed except
where listed.

1. **GPIO21/GPIO43 swap APPROVED** (§6a). GPIO21 = expander button-wake INT; GPIO43 = header
   fast pin. Wake capability is a hard silicon constraint (RTC domain = GPIO0-21 only); the
   header fast pin is pin-number-agnostic. The constrained role takes the constrained pin.
2. **ACC_PWR_EN = the 0x21 expander's 16th pin** (§7b; **U61 P17** in v0.2.4 naming). The
   community header publishes **XGPIO0-14 (15 user GPIO)**; the 16th expander pin gates the
   switched accessory rail.
3. **Button cluster = 7 buttons, not 8** (§7a). A = select/confirm, B = back — no separate
   D-pad centre and no separate Back button. The 0x20 expander's 16th pin was
   footprint-reserved as the Phase-2 RootProbe IRQ landing pin *(v0.2.3: not "spare" — 0
   generally available; **v0.2.4: now the live assignment U60 P17 = ROOTPROBE_IRQ_READY_N**)*.
4. **RootProbe host IRQ -> expander, not native** (§9). It is a "data ready" notification, not
   a sampling signal, so expander latency is harmless.

**Native pin budget: 29 assigned, 2 reserved test pads, 0 unassigned.** *(v0.2.3: this was
stated as "0 outstanding claims", which was not yet true — RootProbe's SPI CS was still
outstanding. Closed in v0.2.3 by the GPIO43 multiplex.)*

## v0.2.3 — final pre-schematic close-out (2026-07-26)

1. **RootProbe SPI CS resolved by multiplexing GPIO43** (§9a). Net label:
   `FAST_IO / U0TXD / ROOTPROBE_CS`. Community-header fast pin OR RootProbe chip select,
   mutually exclusive, never both. **This is what genuinely closes the native budget** — the
   previous "closed" claim contradicted doc 14's standing requirement for a native CS.
2. **Connector-sheet schematic requirements recorded** (§8c): header IRQ/WAKE protection into
   GPIO21, GPIO43 header protection + honest labeling, and ACC_PWR_EN / I2C isolation
   sequencing. **Requirements to implement when drawing the connector sheet — not blockers to
   starting capture.**
3. **0x20 terminology corrected** (§7a): "15 assigned + 1 footprint-reserved = 0 generally
   available", not "exactly full" with a "spare" pin.
4. **Deep-sleep standby figure marked ESTIMATED / PENDING BETA MEASUREMENT** — see
   [[13 - Power Budget and Battery Runtime v0.1]]. Not to be published until measured.

## v0.2.4 — GPIO expander part change: MCP23017 -> TI TCA9535PWR (2026-07-27)

**CORRECTION NOTE — dated 2026-07-27. This is a part change, not a relabel.** Both I2C GPIO
expanders are now **Texas Instruments TCA9535PWR**, designated **U60** (internal) and **U61**
(external / community header). The MCP23017 is removed from the Beta design entirely.

**Why the part changed — two reasons, both binding:**

1. **The current MCP23017 I2C silicon has output-only GPA7/GPB7 limitations.** The v0.2.1
   "factual correction" that declared all 16 MCP23017 pins fully bidirectional did not survive
   re-checking against the current I2C-variant silicon. That correction is therefore itself
   corrected here. The whole point of v0.2.1 item 1 was that a pin-budget built on
   output-only pins had to be recalculated — the honest resolution is to use a part with no
   such asymmetry rather than to keep re-litigating which two pins are crippled.
2. **The community header requires all 15 exposed XGPIO to be genuinely bidirectional.** An
   accessory maker reading "XGPIO0-14, 3.3V logic" will wire an input to any one of them. Two
   output-only pins hidden inside a published 15-pin range is a latent support disaster and a
   documentation contract AQROOT cannot honour. **This reason alone forces the change** even
   if the internal expander could have tolerated the limitation.

**Honest validation status — read this before treating the part as proven:**

> **The TCA9535PWR is DATASHEET-TRUSTED, NOT BENCH-VALIDATED. It will receive its first
> hardware validation on Beta.** No TCA9535 has ever been powered on for this project. The
> Alpha bench test that passed on 2026-07-26 was a **Waveshare MCP23017 board** — a different
> part from a different vendor with a different register map and a different interrupt model.
> That test validated the *architectural pattern* (I2C-mediated GPIO coexisting with touch and
> the IMU on one bus) and nothing about this specific silicon. Every TCA9535-specific
> behaviour — the register set in §7c, the /INT assert-and-clear-on-read semantics, two devices
> wired-OR onto one WAKE_INT_N net, and deep-sleep wake through that net — is **unproven and
> is a Beta bring-up item.** Do not describe the expander as "validated" in any customer-facing
> or internal-status material without naming the part that was actually tested.

**What changed mechanically:**

| Aspect | Was (MCP23017) | Now (TCA9535PWR) |
|---|---|---|
| Pin naming | GPA0-7 / GPB0-7 | **P00-P07 (Port 0) / P10-P17 (Port 1)** |
| Package | — | **PW, TSSOP-24, 0.65 mm pitch** |
| KiCad symbol | — | **`Interface_Expansion:TCA9535PWR`** |
| KiCad footprint | — | **`Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm`** |
| Interrupt outputs | INTA + INTB (two, per-port) | **one open-drain active-low `/INT` per device** |
| Shared interrupt net | "GPIO21 wired-OR" | **named net `WAKE_INT_N`**, terminating at ESP32 **GPIO21** |
| Source identification | INTF / INTCAP capture registers | **firmware snapshot-compare of both input-port registers** |
| Internal pull-ups | GPPU (100k, off until configured) | **none — external pulls are the only pulls** |
| Interrupt config | GPINTEN / DEFVAL / INTCON / IOCON | **none — /INT is unconditional on any input change** |
| Direction registers | IODIRA / IODIRB | **Configuration 0 (0x06) / Configuration 1 (0x07)** |

**Consequences recorded elsewhere in this revision:**
- **§7 rewritten** around U60/U61, TCA9535 port naming, and the TCA9535 register set (new §7c).
- **INTA/INTB separation is gone.** The MCP23017 Port-A/Port-B split was chosen partly so that
  INTB could be "a pure button interrupt" with no false triggers from control-signal activity.
  **The TCA9535 has ONE /INT for both ports, so that property no longer exists** — U60's /INT
  fires on any Port 1 input change *and* on any Port 0 input change. The port split is retained
  anyway because it keeps the map readable and keeps all inputs on one port, but the interrupt
  rationale for it is void and firmware must not rely on it (§7c).
- **Interrupt-on-change configuration is gone.** There is nothing to enable; /INT asserts
  whenever an input pin's state differs from the value last read out of the Input Port register,
  and deasserts when that register is read. Firmware identifies *which* input changed by
  comparing a fresh read against its own previous snapshot (§7c).
- **Internal pull-ups are gone.** The external 10k button pull-ups and every safe-state pull
  were already mandatory and specified; they are now the *only* pulls in the design. Nothing in
  the safe-state rule relaxes — it tightens (§7a).
- **Validation-status wording corrected** in §10 and in [[Alpha-Tests/HARDWARE-NOTES]].

**Unchanged by this revision:** every native ESP32-S3 GPIO assignment (§1), both I2C addresses
(0x20 / 0x21), the reserved address table, the GPIO43 multiplex (§9a), the connector-sheet
requirements (§8c), and the 7-button cluster. **The digital pin architecture is not reopened.**

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
   generated/captured through an I2C GPIO expander of any kind. IR TX and RX both go to native pins
   driven by the ESP32-S3 RMT peripheral. **(v0.2.1: IR TX = GPIO16, IR RX = GPIO44.)**

4. **Power tree corrected.** The bq25185 is a charger with power-path, NOT a 3.3V regulator.
   A separate 3.3V buck-boost regulator is required. (See Section 4.)

5. **RootProbe re-architected as an intelligent coprocessor** (RP2040-class), not raw
   expander pins. (See Section 5.)

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

### Final native allocation (v0.2.3) — 29 assigned, 2 reserved test pads, 0 unassigned

| GPIO | Assignment | | GPIO | Assignment |
|---|---|---|---|---|
| 0 | BOOT button (native, mandatory) | | 18 | SX1262 DIO1 |
| 1 | I2C SDA | | 19/20 | native USB (reserved) |
| 2 | I2C SCL | | 21 | **`WAKE_INT_N` — U60+U61 /INT (wired-OR) / header IRQ — RTC wake** |
| 3 | BMI270 INT1 (strapping — see §6) | | 38 | NFC IRQ |
| 4 | SPI-B SCK | | 39 | I2S BCLK |
| 5 | SPI-B MOSI | | 40 | I2S LRCLK/WS |
| 6 | SPI-B MISO | | 41 | I2S DOUT (speaker) |
| 7 | CC1101 CS | | 42 | I2S DIN (mic) |
| 8 | SX1262 BUSY | | 43 | **FAST_IO / U0TXD / ROOTPROBE_CS** (muxed, §9a) |
| 9 | NFC CS | | 44 | **IR RX (U0RXD)** |
| 10 | Display CS | | 45 | reserved test pad (VDD_SPI strap) |
| 11 | SPI-A MOSI | | 46 | reserved test pad (boot-mode strap) |
| 12 | SPI-A SCK | | 47 | Display backlight |
| 13 | SPI-A MISO | | 48 | microSD CS |
| 14 | Display DC | | | |
| 15 | CC1101 GDO0 | | | |
| 16 | **IR TX (moved off GPIO43)** | | | |
| 17 | SX1262 CS | | | |

**Margin is ZERO, and every native pin is deliberately assigned — none are unallocated.**
Reclaiming GPIO21 (via expander resets) and freeing GPIO43 (via the IR TX move) exactly paid
for IR TX on GPIO16, the button-wake interrupt line, and the header's native fast pin.

**The native budget is CLOSED via the GPIO43 multiplex (§9a), not by having spare pins.** The
previous revision claimed the budget was closed while doc 14 still recorded that RootProbe
needs a native SPI CS — those two statements could not both be true. They are reconciled by
making GPIO43 a **mutually-exclusive multiplexed net**: `FAST_IO / U0TXD / ROOTPROBE_CS`. It
is the community header's fast pin when a general accessory is attached, and RootProbe's chip
select when a RootProbe module is attached. Never both at once. That gives RootProbe's CS a
genuine native home without adding a pin, and closes the contradiction rather than deferring
it. Any *new* native-pin demand must still displace an existing assignment. GPIO45/46 stay
unconnected test pads deliberately: they are the recovery margin, not a reserve to raid.

---

## 2. SPI Bus A — Display (ILI9341) + microSD (standard SPI, shared)

| Signal | GPIO | Notes |
|---|---|---|
| SCK | 12 | shared |
| MOSI | 11 | shared |
| MISO | 13 | shared |
| Display CS | 10 | |
| Display DC | 14 | |
| Display RST | — | **`DISP_RST_N` on U60 P04** (moved off native GPIO21 in v0.2.1) |
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
| **U60** — TCA9535PWR **internal** expander (buttons + control) | 0x20 | **`/INT` -> `WAKE_INT_N` -> GPIO21** (open-drain, active-low; button + RootProbe wake) |
| **U61** — TCA9535PWR **external** expander (community header) | 0x21 | **`/INT` -> `WAKE_INT_N` -> GPIO21** (open-drain, active-low, wired-OR with U60) |
| MAX17048 fuel gauge | 0x36 | poll |
| FT6236 touch | 0x38 | **poll** (frees the missing-INT issue) |
| BMI270 IMU | 0x68 | native INT1 on GPIO3 IF motion-wake needed, else poll |

**I2C bus speed — Beta bring-up rule:** **start at 100 kHz, then verify 400 kHz.** The TCA9535
is a 400 kHz Fast-mode part, but this bus carries five devices plus an externally-exposed
segment through an isolator/bus switch (§8a), and none of that has been characterised on real
Beta hardware. Bring the bus up at 100 kHz, confirm every device enumerates and both expanders
read/write cleanly, and only then raise to 400 kHz and re-verify — including with an accessory
attached on the external segment. Do not start at 400 kHz and debug downward.

**RESERVED I2C ADDRESS TABLE (publish this for accessory makers):** `0x20`, `0x21`, `0x36`,
`0x38`, `0x68` are reserved by AQROOT internals. A community accessory MUST NOT use these.
Note the TCA9535 family occupies the whole `0x20-0x27` block (as do the MCP23017/MCP23008 and
PCA9535/PCA9555 families, which share that range); an accessory carrying any expander from that
range must be strapped into `0x22-0x27` and its conflict risk documented.

- One intentional pair of I2C pull-ups (remove redundant breakout pull-ups). Size them for
  the internal bus only — external accessory pull-ups are a separate, jumper-selectable
  option at the header (§8a).
- **Touch RST:** `TOUCH_RST_N` on **U60 P00**, with `DISP_RST_N` on **U60 P04** (v0.2.1 — both
  moved off native GPIO21). Two separate expander pins rather than one shared pin, for sequencing
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
| I2S DIN (mic) | 42 (moved off strapping GPIO45) |

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
| 7-button cluster (D-pad + A + B + Home) | — | on **U60 P10-P16**, wake via U60 `/INT` -> `WAKE_INT_N` -> GPIO21 |
| Physical power switch | — | **NOT a GPIO** — hard-off path, see below |

**Strapping pins:**
- GPIO0 = BOOT button (normal use).
- GPIO3 = BMI270 INT1 (JTAG-select strap). SX1262 RESET has moved to the expander
  (`SX1262_RST_N` on U60 P01), so GPIO3 now carries the IMU interrupt alone.
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
spare: it becomes the **shared interrupt / wake line, net name `WAKE_INT_N`**.

| Role | Detail |
|---|---|
| **U60 `/INT`** (0x20) | button-cluster interrupt + RootProbe IRQ/READY — merged, single output for both ports |
| **U61 `/INT`** (0x21) | community-header accessory attention line |
| Header IRQ/READY pin | the same net, exposed on the expansion header (§8b) |

Both devices have **exactly one open-drain active-low `/INT` output**, and both are wired-OR
onto `WAKE_INT_N` with a **single pull-up on the AQROOT side**. `WAKE_INT_N` terminates at
**ESP32 GPIO21**.

**There is no INTA/INTB separation and no interrupt-source register.** The TCA9535 provides no
INTF/INTCAP equivalent, so **firmware cannot ask the chip what changed** — it must read both
Input Port registers (0x00 and 0x01) from **both** U60 and U61 and compare against its own
previous snapshot. See §7c for the required firmware contract.

**Why GPIO21 and not GPIO43 for this — APPROVED 2026-07-26:** a polled expander cannot wake
the ESP32 from sleep, so this line must be a real wake source — and on the ESP32-S3 only
**GPIO0-21 are RTC GPIO**, i.e. only they can serve as an `ext0`/`ext1` deep-sleep wake
source. GPIO43 is not RTC-capable. Since [[13 - Power Budget and Battery Runtime v0.1]]
depends on deep sleep (~10-20uA) with wake-on-button for the ~2-week standby figure, the
interrupt line has to sit on GPIO21 and the freed GPIO43 goes to the expansion header instead.

> **RESOLVED — swap approved, not an open item.** The two roles are not symmetric.
> **Wake capability is a hard electrical constraint of the silicon**: the interrupt line can
> only work on an RTC-capable pin, and GPIO21 is the only one available. The **header fast
> pin is pin-number-agnostic** — an accessory maker does not care whether the fast native pin
> on the connector is called 21 or 43, only that it is native and fast, which GPIO43 is. When
> one role is constrained and the other is not, the constrained role takes the constrained
> pin. Signed off in [[05 - Design Decisions Log]] (2026-07-26 pin-budget resolution).

### 6b. Physical power switch — deliberately OUTSIDE the GPIO architecture

The power switch is **not** an expander input and **not** a firmware GPIO. It needs a real
hard-off path: a mechanical switch driving a load-switch / charger ship-mode / battery
disconnect, so a hung or unflashed firmware can still be powered down and a shelved unit
draws effectively zero. Spec the exact topology at schematic time (candidates: charger
ship-mode entry, a latching soft-power controller, or a plain series load switch). Do not
fold this into the U60 button cluster.

---

## 7. GPIO expanders — TWO TCA9535PWR (U60 + U61) — v0.2.4

**LOCKED PART DECISION (2026-07-27).** Both I2C GPIO expanders are **Texas Instruments
TCA9535PWR**. This supersedes the MCP23017 entirely — see the v0.2.4 correction note above for
why the part changed.

| Property | Value |
|---|---|
| Part | **Texas Instruments TCA9535PWR** (both devices) |
| Designators | **U60** = internal expander, **U61** = external / community-header expander |
| Package | **PW, TSSOP-24, 0.65 mm pitch** |
| KiCad symbol | **`Interface_Expansion:TCA9535PWR`** |
| KiCad footprint | **`Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm`** |
| I/O | **16 genuinely bidirectional**, as Port 0 (`P00-P07`) + Port 1 (`P10-P17`) |
| Interrupt | **one open-drain active-low `/INT` per device**, covering both ports |
| U60 address | **0x20** — straps **A2=GND, A1=GND, A0=GND** |
| U61 address | **0x21** — straps **A2=GND, A1=GND, A0=+3V3** |
| Internal pull-ups | **NONE.** Every pull in the design is an external resistor. |

> **Footprint audit still required.** The symbol/footprint pair above is the intended
> assignment, **not a verified one** — nothing has been checked against the TI datasheet
> drawing in KiCad yet. Confirm pin numbering and body/pad geometry before the schematic
> freeze; §11 keeps this as a blocking item.

Both `/INT` outputs are wired-OR onto the shared **`WAKE_INT_N`** net with a single AQROOT-side
pull-up. `WAKE_INT_N` terminates at **ESP32 GPIO21** (§6a).

The architectural point of using two chips is unchanged from v0.2.1: the community header gets
**its own dedicated expander (U61)** rather than the leftovers of the internal one, so an
accessory can never contend with internal control signals or the button cluster.

### 7a. U60 — internal expander @ 0x20 (buttons + internal control)

**TCA9535PWR. Address straps A2=GND, A1=GND, A0=GND.** All 16 pins are assigned; **U60 has zero
free capacity.** Plan new signals against zero availability on this chip.

**Port 0 — internal slow control outputs**

| Pin | Direction | Net | Function | Power-up safe state (external pull MANDATORY) |
|---|---|---|---|---|
| **P00** | out | `TOUCH_RST_N` | Touch RESET (FT6236) | pull to **RESET-ASSERTED** |
| **P01** | out | `SX1262_RST_N` | SX1262 RESET | pull to **RESET-ASSERTED** |
| **P02** | out | `NFC_5V_EN` | NFC 5V boost enable | pull to **OFF** |
| **P03** | out | `AMP_SD_MODE` | Audio amp shutdown/mode (MAX98357A SD) | pull to **SHUTDOWN** |
| **P04** | out | `DISP_RST_N` | Display RESET (ILI9341) | pull to **RESET-ASSERTED** |
| **P05** | out | `RGB_R_CTL` | RGB LED — red | pull to **LED-OFF** |
| **P06** | out | `RGB_G_CTL` | RGB LED — green | pull to **LED-OFF** |
| **P07** | out | `RGB_B_CTL` | RGB LED — blue | pull to **LED-OFF** |

**Port 1 — button cluster + RootProbe IRQ (all inputs)**

| Pin | Direction | Net | Function | Power-up safe state (external pull MANDATORY) |
|---|---|---|---|---|
| **P10** | in | `BTN_UP_N` | Button — D-pad UP | **10k pull-up** |
| **P11** | in | `BTN_DOWN_N` | Button — D-pad DOWN | **10k pull-up** |
| **P12** | in | `BTN_LEFT_N` | Button — D-pad LEFT | **10k pull-up** |
| **P13** | in | `BTN_RIGHT_N` | Button — D-pad RIGHT | **10k pull-up** |
| **P14** | in | `BTN_A_N` | Button — **A = SELECT/CONFIRM** | **10k pull-up** |
| **P15** | in | `BTN_B_N` | Button — **B = BACK** | **10k pull-up** |
| **P16** | in | `BTN_HOME_N` | Button — HOME | **10k pull-up** |
| **P17** | in | `ROOTPROBE_IRQ_READY_N` | RootProbe IRQ / READY (Phase 2, §9) | **10k pull-up** |

Port 0 = every internal slow control signal. Port 1 = every input. **The split is retained for
readability, but its original interrupt rationale is VOID** — see the warning below.

> **The "pure button interrupt" property NO LONGER EXISTS.** Under the MCP23017 the Port-A /
> Port-B split existed partly so that `INTB` would fire only on button activity, with no false
> triggers from control-signal writes. **The TCA9535 has ONE `/INT` for both ports.** U60's
> `/INT` responds to input-state changes on either port. In this map every Port 0 pin is an
> output and every Port 1 pin is an input, so in practice the only interrupt sources are the
> buttons and the RootProbe IRQ — but that is a property of *this assignment*, not of the
> silicon, and **firmware must not assume it.** If any Port 0 pin is ever reconfigured as an
> input, it becomes an interrupt source too.

**U60 `/INT` behaviour (open-drain, active-low, -> `WAKE_INT_N` -> GPIO21):**
- **Button and RootProbe sources are MERGED on one output.** There is no hardware distinction
  between "a button was pressed" and "RootProbe raised READY" — both pull the same `/INT` low.
- **Firmware reads BOTH input-port registers (0x00 and 0x01) and compares against the previous
  snapshot** to determine what changed. The chip does not record it (§7c).
- **`ROOTPROBE_IRQ_READY_N` MUST be LEVEL-HELD until acknowledged, not a short pulse.** This is
  a hard requirement on the RootProbe side. A brief pulse can be missed entirely: the host may
  be in deep sleep, mid-I2C-transaction, or servicing a button event, and the TCA9535 offers no
  latch or capture register to catch a transient. RootProbe must assert the line and hold it
  until AQROOT acknowledges over the I2C management link. Recorded as a RootProbe firmware
  requirement in [[14 - RootProbe Interface v0.1]] §4.

**Button scheme (resolved 2026-07-26) — 7 buttons, not 8.** Standard handheld mapping:
**D-pad navigates, A = select/confirm, B = back, Home = launcher.** There is **no separate
D-pad centre/select button** — the A button *is* select, so a centre press would be a
duplicate control competing with A for the same job. There is also no separate "Back" button
distinct from B. Power is a **hard switch, not a button** (§6b), so it consumes no expander pin.

**Button scheme (resolved 2026-07-26) — 7 buttons, not 8.** Standard handheld mapping:
**D-pad navigates, A = select/confirm, B = back, Home = launcher.** There is **no separate
D-pad centre/select button** — the A button *is* select, so a centre press would be a
duplicate control competing with A for the same job. There is also no separate "Back" button
distinct from B; the earlier "D-pad + A/B + Back + Home" phrasing double-counted it. Power is
a **hard switch, not a button** (§6b), so it consumes no expander pin.

**U60 P17 carries `ROOTPROBE_IRQ_READY_N`** (§9) — the Phase-2 RootProbe IRQ/READY line. The
pin has a committed owner; only if RootProbe were cancelled outright would it become free, at
which point it is the natural home for an 8th button or a centre-select.

- **`/INT` -> `WAKE_INT_N` -> GPIO21**, open-drain, active-low, wired-OR with U61, one pull-up.
- **There is nothing to configure to enable interrupts.** The TCA9535 has no GPINTEN, DEFVAL,
  INTCON, or IOCON equivalent — `/INT` asserts unconditionally whenever an input differs from
  the last value read out of its Input Port register, and deasserts when that register is read.
- **External 10k button pull-ups are MANDATORY, and they are the only pull-ups that exist.**
  The TCA9535 has **no internal pull-up option at all** (no GPPU equivalent), so this is no
  longer a preference over weak 100k internal pulls — it is the sole pull path. 10k is also the
  right value for a long button trace in an RF-noisy handheld.

**BUTTON WAKE (hard requirement):** a polled expander CANNOT wake the ESP32 from sleep. The
`WAKE_INT_N` -> GPIO21 line is what makes button-wake possible at all. Without it the device can
only be woken by the BOOT button or the IMU, and the ~2-week standby figure in the power budget
is unreachable. This line is not optional. **Note it is also unvalidated** — see §10.

**POWER-UP SAFE-STATE RULE (hard requirement, and it tightens under the TCA9535):** all TCA9535
ports **default to INPUTS (high-Z)** at power-up — Configuration registers 0x06/0x07 reset to
`0xFF` — and stay that way until firmware writes them. Every safety-relevant signal in the
tables above therefore needs an **external pull resistor forcing the safe state**, pulled so
that the NFC boost is off, the audio amp is in shutdown, load switches are open, the RGB LED is
dark, and all resets are held asserted, **before any firmware runs.** **Do NOT rely on "firmware
writes it low quickly."** Between power-on and the first I2C transaction there are milliseconds
of high-Z, and a hung or half-flashed firmware makes that window permanent. With no internal
pull-ups available on this part, the external resistors are the *only* thing defining the
power-up state — there is no fallback.

**OUTPUT-LATCH ORDERING RULE (hard requirement):** firmware **MUST write the safe value into the
Output Port register (0x02 / 0x03) BEFORE changing the corresponding Configuration register bit
(0x06 / 0x07) from input to output.** The Output Port registers reset to `0x00`, which is *not*
the safe state for every signal in this design — flipping a pin to output first would drive
whatever happens to be latched and could momentarily enable the NFC boost, un-mute the amp, or
release a reset. Set the latch, then set the direction. See §7c.

**Dropped earlier:** the old "display power/control reserve" pin — displaced by the button
cluster. If a separate display power-gate is genuinely needed it must displace an existing
assignment. **There is no slack on U60.**

### 7b. U61 — external expander @ 0x21 (community expansion header)

**TCA9535PWR. Address straps A2=GND, A1=GND, A0=+3V3.** Dedicated to the community header so
that an accessory can never contend with internal control signals or the button cluster.

**Port 0 — XGPIO0-7**

| Pin | Net | Function |
|---|---|---|
| **P00** | `XGPIO0` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P01** | `XGPIO1` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P02** | `XGPIO2` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P03** | `XGPIO3` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P04** | `XGPIO4` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P05** | `XGPIO5` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P06** | `XGPIO6` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P07** | `XGPIO7` | low-speed community GPIO, 3.3V logic, bidirectional |

**Port 1 — XGPIO8-14 + accessory power enable**

| Pin | Net | Function |
|---|---|---|
| **P10** | `XGPIO8` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P11** | `XGPIO9` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P12** | `XGPIO10` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P13** | `XGPIO11` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P14** | `XGPIO12` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P15** | `XGPIO13` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P16** | `XGPIO14` | low-speed community GPIO, 3.3V logic, bidirectional |
| **P17** | `ACC_PWR_EN` | switched accessory-power enable — **NOT exposed to users** |

- **15 labeled low-speed user GPIO, brought out as XGPIO0..XGPIO14.** The 16th pin (P17) is
  reserved internally as `ACC_PWR_EN`.
- **All 15 XGPIO are genuinely bidirectional** — this is the requirement that forced the part
  change (v0.2.4 reason 2). Any XGPIO may be configured as an input or an output; there is no
  crippled pin hidden in the published range.
- **`/INT` wired-OR onto `WAKE_INT_N`** (open-drain, active-low) so an accessory can request
  attention / wake the device.
- **Firmware reads both U61 input-port registers (0x00 and 0x01) to identify which XGPIO input
  changed**, comparing against its previous snapshot — same mechanism as U60 (§7c).
- Every XGPIO line gets ESD protection at the connector and should be current-limited.

**ACC_PWR_EN — resolved 2026-07-26 (option (a) of the three logged in v0.2.1).** U61 P17 drives
the load switch on the header's accessory power rail. Worth one header pin because it buys two
things nothing else provides:
1. **Power-cycle a misbehaving add-on.** Combined with the I2C bus switch (§8a), a latched-up
   or bus-jamming accessory can be fully isolated *and* de-powered from firmware, without
   asking the user to unplug anything or rebooting AQROOT.
2. **Zero idle draw when nothing is attached** — the rail stays off until an accessory is
   present and in use, which matters directly to the standby figure in
   [[13 - Power Budget and Battery Runtime v0.1]].

**15 user GPIO still exceeds Kode Dot's 14**, so the headline number survives the reservation
intact — see [[04 - Competitive Analysis]] for the caveat about not comparing GPIO counts in
the first place.

**Safe state:** `ACC_PWR_EN` needs an external pull holding the accessory rail **OFF** at
power-up, per the safe-state rule in §7a — an unpowered header is the safe default, and it
must not depend on firmware having run. It is also subject to the output-latch ordering rule:
write the OFF value to Output Port 1 before switching P17 to an output.

**Audio amp note:** the MAX98357A shutdown/mode (+ optional gain) pin(s) live on **U60 P03
(`AMP_SD_MODE`)** as slow enables — power-gate the amp when audio is idle, with the external
pull holding it in shutdown until firmware says otherwise.

**RGB LED note:** a conventional RGB LED needs 3 outputs (**U60 P05-P07**). A WS2812 addressable
LED needs precise timing and MUST NOT go on the expander — addressable RGB would need a native
RMT pin (there are none free, see §1) or an I2C RGB driver.

### 7c. TCA9535 register set + firmware contract (v0.2.4)

**Register map — this is the complete set. There are eight registers and no others.**

| Addr | Register | Reset | Notes |
|---|---|---|---|
| `0x00` | **Input Port 0** | — | Read-only. **Reading it deasserts `/INT`** for Port 0 changes. |
| `0x01` | **Input Port 1** | — | Read-only. **Reading it deasserts `/INT`** for Port 1 changes. |
| `0x02` | **Output Port 0** | `0x00` | Output latch. Write BEFORE setting direction (§7a). |
| `0x03` | **Output Port 1** | `0x00` | Output latch. Write BEFORE setting direction (§7a). |
| `0x04` | **Polarity Inversion 0** | `0x00` | Leave at `0x00`. See the active-low note below. |
| `0x05` | **Polarity Inversion 1** | `0x00` | Leave at `0x00`. See the active-low note below. |
| `0x06` | **Configuration 0** | `0xFF` | Direction: `1` = input, `0` = output. All inputs at reset. |
| `0x07` | **Configuration 1** | `0xFF` | Direction: `1` = input, `0` = output. All inputs at reset. |

**Registers that DO NOT EXIST on this part.** The MCP23017 register model is gone. There is no
`IODIRA`/`IODIRB` (use Configuration 0x06/0x07), no `GPPU` (no internal pull-ups exist at all),
no `GPINTEN`, no `INTF`, no `INTCAP`, no `IOCON`, no `DEFVAL`, and no `INTCON`. **Any firmware,
comment, or document still referencing those names is describing hardware that is not on this
board.** Interrupt-on-change is not a configurable feature here — it is the unconditional
default behaviour of the Input Port registers.

**One driver serves both U60 and U61.** The two devices are the same silicon at different
addresses, so the driver is address-parameterised: one implementation, two instances (0x20 and
0x21). Do not write two drivers, and do not special-case U61 — the only differences are the I2C
address, which pins are inputs vs outputs, and what the nets mean.

**Required interrupt-service sequence (both devices):**

1. `WAKE_INT_N` goes low (or the ESP32 wakes on it from deep sleep via `ext0`/`ext1`).
2. **Read Input Port 0 and Input Port 1 from U60, and from U61.** Both registers on both
   devices, every time — the shared net does not say which device asserted, and each device's
   single `/INT` does not say which port changed.
3. **Compare each register against the driver's previous snapshot** to derive the changed bits.
   This snapshot-compare is the *only* way to identify the source: the chip has no capture
   register. The driver owns the snapshot; it must be initialised at boot from a first read.
4. Dispatch: changed bits in U60 Port 1 -> button events (`BTN_*_N`) or
   `ROOTPROBE_IRQ_READY_N`; changed bits in U61 -> the corresponding `XGPIO` input event.
5. **Confirm `WAKE_INT_N` has actually released.** Because both devices share the net, a second
   device asserting while the first is being serviced keeps the line low. Re-read rather than
   assuming one pass clears it, or the driver will miss the second event and can deadlock on an
   edge-triggered handler.

**Level-vs-edge caution:** treat `WAKE_INT_N` as **level-sensitive** in firmware. The TCA9535
has no interrupt latch, so an edge-only handler on a wired-OR net is a missed-event bug waiting
to happen — this is also why `ROOTPROBE_IRQ_READY_N` must be level-held until acknowledged
(§7a).

**Active-low naming vs Polarity Inversion:** the `_N` suffixes in the maps above describe the
**electrical** convention (buttons pull low, resets assert low). **Keep Polarity Inversion
registers 0x04/0x05 at their `0x00` reset value** and invert in firmware instead. Inverting in
hardware would make the register contents disagree with the schematic net names and with every
scope trace taken during bring-up, for no benefit. If this is ever revisited, it must be
documented here first.

**I2C bring-up speed:** **100 kHz for initial Beta bring-up, then verify 400 kHz** (§4).

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
bus carries touch (0x38), the IMU (0x68), the fuel gauge (0x36) and both TCA9535 expanders
(U60 @ 0x20 / U61 @ 0x21) — i.e. the display's input path, the button cluster, and every internal control
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
| Native fast | **GPIO43 — label the net `FAST_IO / U0TXD / ROOTPROBE_CS`** (§9a). Native and fast, but it emits UART boot-log traffic at every reset, and it is the RootProbe chip select when a RootProbe is attached. Do not label it as plain "fast GPIO" |
| Native I2C | SDA + SCL, **via the isolation of §8a** |
| Interrupt | shared open-drain IRQ/READY net — **`WAKE_INT_N`** (= GPIO21, wired-OR with both expanders' `/INT`) |
| Power | 3.3V, switched accessory power (gated by ACC_PWR_EN), **multiple grounds** |
| Low-speed GPIO | **XGPIO0..XGPIO14** — 15 user pins off U61 (TCA9535PWR @ 0x21), 3.3V logic only, **all bidirectional** |

**Labeling and marketing rules (binding):**
- Label the expander pins **clearly as low-speed** on the silkscreen, in the pinout diagram,
  and in the docs. XGPIO is I2C-mediated: expect microseconds-to-milliseconds per transition,
  not MHz. They are for enables, chip selects, mode straps, LEDs, and simple sensors.
- **Do NOT market this as "15 GPIO vs Flipper's 18."** That comparison is false in kind — the
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

## 8c. Connector-sheet SCHEMATIC REQUIREMENTS (2026-07-26)

**These are implementation requirements for the community-header / connector sheet, NOT
blockers to starting schematic capture.** Start the core sheets now; satisfy these when the
connector sheet is drawn. They exist because every one of these nets leaves the board and can
be shorted, back-powered, or held low by hardware AQROOT does not control.

### a. Header IRQ / WAKE line into GPIO21 — must NOT be wired naked

GPIO21 is the button-wake interrupt. An external accessory sharing it can, if unprotected,
**hold GPIO21 low and permanently block internal button wake** — the device would appear dead
to its own buttons because of a faulty add-on. Requirements:

- **Series resistance** on the external leg, before the connector.
- **Connector-side ESD protection.**
- **Open-drain-only accessory requirement** — published as a hard rule for accessory makers.
  A push-pull accessory driver on this net is a fault, not a supported configuration.
- **A defined pull-up on the AQROOT side** (the internal wired-OR pull-up), sized so internal
  operation never depends on the accessory.
- **Gating**, so an unpowered or faulty accessory cannot hold GPIO21 low or block internal
  button wake. **Preferred implementation: an open-drain buffer/gate powered from switched
  accessory power** — when ACC_PWR_EN is off the gate is unpowered and the external leg is
  isolated by construction, so a dead accessory simply drops out of the wired-OR.
- **Label the external line "optional open-drain WAKE/ATTN input", not a general interrupt.**
  It is a request-for-attention, not a shared IRQ bus, and naming it accurately prevents
  accessory makers designing against a contract AQROOT does not offer.

### b. GPIO43 on the header — `FAST_IO / U0TXD / ROOTPROBE_CS`

- **220R-1k series resistor** on the connector leg + **connector-side ESD protection**.
- **Document that it emits UART boot-log traffic at every reset.** Accessory makers must design
  for that; an accessory that acts on every edge of this pin will misbehave at boot.
- **No direct connection to accessory power-enables or high-current drivers without gating.**
  A boot-log burst must not be able to switch a load.
- **Label it honestly as FAST_IO / U0TXD** (and ROOTPROBE_CS on the RootProbe leg) — never as
  plain "fast GPIO". The extra names are the warning.

### c. ACC_PWR_EN + I2C isolation — defined sequencing

Power and bus isolation must be sequenced, not toggled independently. **Recovery/attach order:**

1. **Disconnect** the external I2C segment (bus switch open).
2. **Accessory power OFF** (ACC_PWR_EN deasserted).
3. **Discharge** the accessory rail (bleed resistor; wait for it to actually decay).
4. **Power ON** (ACC_PWR_EN asserted).
5. **Stabilize** — wait out the rail's rise time plus the accessory's own reset/boot time.
6. **Reconnect** the external I2C segment (bus switch closed).
7. **Enumerate** the accessory over I2C.

Detach/fault handling runs the same sequence in reverse: isolate the bus *before* cutting
power, so a half-powered accessory never sits on a live bus.

**Isolator part requirements (both are selection criteria, not nice-to-haves):**
- **Must support powered-off high-impedance** on the external side — it has to stay isolating
  while the accessory rail is down, which is precisely the state in steps 1-3.
- **Must NOT back-power the accessory side** through its I/O pins or protection diodes.
  Back-powering defeats the discharge step, keeps a latched-up accessory alive, and makes the
  power-cycle useless.

---

## 9. RootProbe — re-architected (was a design conflict)

RootProbe (the flagship logic-analyzer / bus-sniffer / GPIO-tooling add-on) CANNOT be built
on I2C GPIO expander pins — I2C-mediated GPIO is far too slow for logic-analyzer sampling,
UART/SPI/I2C capture, or pulse-width measurement. That is true of the TCA9535 exactly as it was
of the MCP23017; the part change does not affect this reasoning.

**RootProbe = intelligent coprocessor module** with its own MCU (RP2040-class) handling:
high-speed capture, triggering, protocol decode, local buffering, voltage-level protection.
It talks to AQROOT over a board-to-board interface: regulated power, GND, SPI data link, I2C
management, interrupt/ready line, optional USB pair.

**Split the connector marketing into two things:**
1. Low-speed community GPIO header — **15 user XGPIO off a dedicated second expander, U61
   (TCA9535PWR @ 0x21)**, plus native I2C / IRQ / GPIO43 / power (the hybrid header, §8b).
   *(v0.2.1: was "~7 slow GPIO off the shared internal expander".)*
2. High-speed RootProbe accessory interface (board-to-board to the coprocessor).

### 9a. GPIO43 multiplex — `FAST_IO / U0TXD / ROOTPROBE_CS` (resolved 2026-07-26)

**The one signal RootProbe genuinely needed a native pin for was its SPI chip select** — a
per-transaction CS cannot sit behind an I2C expander at usable speed. With zero unassigned
native pins, that was a live contradiction: the budget could not be "closed" while a known
Phase-2 signal still required a pin that did not exist.

**Resolution: GPIO43 is a multiplexed net serving two mutually-exclusive roles.**

| Role | Active when |
|---|---|
| **FAST_IO** — community-header native fast pin | a general accessory is attached |
| **ROOTPROBE_CS** — RootProbe SPI chip select | a RootProbe module is attached |
| *(U0TXD — ROM boot-log output)* | *always, at every reset — see the caution below* |

**Mutual exclusion is a design rule, not an accident.** The net routes to both the community
header and the RootProbe connector; **only one may be populated and active at a time.**
Enforcement:
- **Firmware arbitration:** RootProbe is detected by I2C enumeration on the management bus
  (§9). When a RootProbe answers, firmware MUST treat GPIO43 as ROOTPROBE_CS and MUST NOT
  drive it as general FAST_IO, and vice versa.
- **Documented user rule:** attaching a community accessory that uses FAST_IO *and* a
  RootProbe simultaneously is unsupported. Two drivers on one net is contention.
- **Series resistance on both connector legs** (§8c, requirement b) limits the damage if a
  user does it anyway. This is damage-limiting, not a licence to support the combination.

**Boot-log consequence — RootProbe must tolerate it.** GPIO43 is U0TXD, so the ROM bootloader
drives the boot log onto this net at every reset. As ROOTPROBE_CS that means **RootProbe will
see spurious chip-select activity during AQROOT's boot.** RootProbe's own MCU must therefore
hold its SPI slave interface disabled/ignored until its firmware has initialised and the host
has spoken over the I2C management link. Record this as a RootProbe firmware requirement — it
is a direct consequence of the multiplex and it is not optional. (Same reasoning that moved IR
TX off this pin in v0.2.1: a boot-log-driven net is fine for something that can ignore it, and
unacceptable for something that acts on every edge.)

---

**RootProbe host IRQ — resolved 2026-07-26: EXPANDER pin, now `ROOTPROBE_IRQ_READY_N` on
U60 P17, not a native pin.** RootProbe does its high-speed capture locally on its own MCU; the
line crossing to AQROOT is only "data ready / trigger hit / attention." That is a notification,
not a sampling signal, and it tolerates expander latency (tens to hundreds of microseconds)
without affecting capture fidelity — the timing-critical work already happened on the
coprocessor. Putting it on U60 P17 also routes it through U60 `/INT` -> `WAKE_INT_N` -> GPIO21,
so **RootProbe can wake the device** for free. This is the "don't let a Phase-2 accessory
consume scarce native pins" principle applied to the one pin it was most tempting to break it
for. See [[14 - RootProbe Interface v0.1]] §4.

**v0.2.4 requirement — level-held, not pulsed.** Because U60's single `/INT` merges the button
and RootProbe sources and the TCA9535 has no interrupt-capture register, **RootProbe MUST hold
`ROOTPROBE_IRQ_READY_N` asserted until AQROOT acknowledges over the I2C management link.** A
short pulse can be lost outright — during deep sleep, mid-I2C-transaction, or while the driver
is servicing a button event. This replaces any earlier assumption that the expander's
interrupt-on-change hardware would latch the event; it will not, because that hardware does not
exist on this part (§7c).

Do NOT advertise expander pins as logic-analyzer channels.

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
- I2C GPIO EXPANDER — **PATTERN validated on a DIFFERENT PART. The Beta part (TCA9535PWR) is
  NOT bench-validated.** What was actually tested on 2026-07-26 was a **Waveshare MCP23017
  board** (I2C; PA0->PB0 loopback 49/49 clean; coexisting with FT6236 touch + BMI270 IMU on the
  shared bus; bench board strapped at 0x27). **The MCP23017 was removed from the design in
  v0.2.4 and replaced by the TI TCA9535PWR (U60/U61).** That bench test therefore validates the
  *architecture* — I2C-mediated GPIO working as real inputs and outputs while coexisting with
  the other bus devices — and **nothing about the TCA9535 silicon, its register map, or its
  interrupt model.** No TCA9535 has been powered on for this project. **Everything
  TCA9535-specific is a Beta bring-up item:** the §7c register set, `/INT` assert /
  clear-on-read behaviour, two devices wired-OR onto `WAKE_INT_N`, deep-sleep wake through that
  net, and the snapshot-compare source identification. The button-wake path has never been
  exercised on any part.
- TPS63020 3.3V BUCK-BOOST RAIL VALIDATED (bench-tested with a meter; held ~3.3V from a 3.4V
  battery input — buck-boost regulation confirmed in the hardest near-Vout region; 2026-07-26).
  On Beta fed from bq25185 SYS (~4.5V) per §8 power tree.
- bq25185 CHARGER + POWER PATH VALIDATED (Adafruit 6092; USB-first safe bring-up, battery
  polarity confirmed vs silkscreen before connecting, active charging confirmed — G on, C
  solid, F off; 2026-07-26). Reverse-polarity protection + keyed battery connector remain
  hard Beta requirements (§8 / power incident note). **The protection TOPOLOGY is PARKED as of
  2026-07-30** — high-side only, battery negative tied to system GND (locked); leading
  candidate ADI **LTC4368-1** + back-to-back **AO3400A-class** N-FETs, **not locked**. Final
  lock is owned by the professional power/DFM pre-fab review (LTspice charge-path case + ADI
  FAE confirmation), and that gate **blocks PCB routing and fabrication release for the whole
  board**. `01_POWER_TREE` may be captured with the battery-input protection block left as a
  marked `DO NOT ROUTE` placeholder. See [[05 - Design Decisions Log]].

> **ALPHA HARDWARE VALIDATION COMPLETE (2026-07-26):** all Alpha subsystems bench-proven *as
> built in Alpha*. The audio-in mic will NOT be bench-retested (a confirmed dead individual
> ICS-43434 unit; wiring, firmware, and the MAX98357A amp on the same I2S bus are all validated,
> so it is a bad part, not a design issue) — its first live confirmation happens on Beta
> hardware. **Cleared to begin the KiCad schematic.**
>
> **CORRECTED 2026-07-27 — "on fully-validated parts" is no longer true and has been struck.**
> The v0.2.4 expander change means the Beta BOM now contains a part that was never on the Alpha
> bench: the **TCA9535PWR is datasheet-trusted only.** Schematic capture is still cleared to
> proceed — a datasheet-specified digital part with a locked pin map is a reasonable thing to
> capture — but the blanket "every Beta part is bench-validated" claim is retired. Two Beta
> parts now await first hardware confirmation: the ICS-43434 mic (dead Alpha unit) and both
> TCA9535PWR expanders (never tested).

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
- [x] Expander pin count corrected to 16 usable; budgets recalculated. *(v0.2.4: the underlying
      claim about MCP23017 bidirectionality was itself wrong — resolved for good by changing the
      part to the TCA9535PWR, which genuinely has 16 bidirectional I/O.)*
- [x] GPIO43/44 UART labels corrected (43 = U0TXD, 44 = U0RXD).
- [x] IR TX moved off the boot-log pin -> GPIO16; driver stage fully specified.
- [x] GPIO21 reclaimed (display + touch RESET -> expander).
- [x] Button cluster given a home; second expander (0x21) added for the header.
- [x] Button-wake path defined (expander `/INT` -> `WAKE_INT_N` -> RTC-capable GPIO21).
- [x] External I2C isolation requirements recorded.
- [x] Header repositioned as a hybrid; marketing rules recorded.

Resolved 2026-07-26 (pin-budget resolution — see [[05 - Design Decisions Log]]):
- [x] **GPIO21/GPIO43 role swap APPROVED** — GPIO21 = expander button-wake INT (RTC-capable,
      hard silicon constraint), GPIO43 = header fast pin (pin-number-agnostic). §6a.
- [x] **ACC_PWR_EN = U61 P17**; header publishes XGPIO0-14 (15 user GPIO). §7b.
- [x] **No D-pad centre button** — A = select/confirm, B = back. 7 buttons; the 16th internal
      pin carries the RootProbe IRQ. §7a.
- [x] **RootProbe host IRQ -> expander pin (`ROOTPROBE_IRQ_READY_N`, U60 P17), Phase 2** — not
      a native pin. §9.

Resolved 2026-07-26 (v0.2.3 final close-out):
- [x] **RootProbe SPI CS -> GPIO43 multiplex** (`FAST_IO / U0TXD / ROOTPROBE_CS`). §9a. This
      is what genuinely closes the native budget.
- [x] 0x20 capacity wording corrected to "15 assigned + 1 footprint-reserved = 0 generally
      available". §7a. *(v0.2.4: now 16 assigned — U60 P17 = `ROOTPROBE_IRQ_READY_N` is a live
      assignment, still 0 available.)*

Resolved 2026-07-27 (v0.2.4 expander part change):
- [x] **Expander part LOCKED: TI TCA9535PWR x2, U60 @ 0x20 + U61 @ 0x21.** PW / TSSOP-24 /
      0.65 mm. Symbol `Interface_Expansion:TCA9535PWR`, footprint
      `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm`. §7.
- [x] **Output-only-pin risk eliminated** — all 15 published XGPIO are genuinely bidirectional.
- [x] **Interrupt architecture restated for single-`/INT` silicon:** both `/INT` outputs
      wired-OR onto `WAKE_INT_N` -> GPIO21; source identified by snapshot-compare, not by a
      capture register. §6a, §7c.
- [x] **TCA9535 register set documented** (0x00-0x07) and MCP23017 register assumptions removed.
      One address-parameterised driver serves both devices. §7c.

Still blocking (must resolve before freeze):
- [ ] Select the I2C bus buffer/isolator or bus switch part for the external segment (§8a).
      **Selection criteria are now binding: powered-off high-impedance, and no back-powering
      of the accessory side** (§8c-c). **Still unresolved.**
- [ ] Select the ACC_PWR_EN load switch part for the accessory rail (§7b). **Still unresolved.**
- [ ] **Footprint audit for U60/U61:** verify `Interface_Expansion:TCA9535PWR` pin numbering and
      `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` geometry against the TI datasheet drawing before
      freeze. The pair is assigned but **not yet verified** (§7).

Schematic requirements — implement on the connector sheet, NOT blockers to starting capture:
- [ ] Header IRQ/WAKE into GPIO21: series R, connector ESD, open-drain-only accessory rule,
      defined AQROOT-side pull-up, gating (preferably an open-drain buffer powered from
      switched accessory power). Label "optional open-drain WAKE/ATTN input". §8c-a.
- [ ] GPIO43 on the header: 220R-1k series R + connector ESD; document the boot-log traffic;
      no ungated connection to power-enables or high-current drivers; label FAST_IO/U0TXD. §8c-b.
- [ ] ACC_PWR_EN + I2C isolation sequencing (disconnect -> power off -> discharge -> power on
      -> stabilize -> reconnect -> enumerate), and the reverse order on detach/fault. §8c-c.
- [ ] RootProbe firmware requirement: hold the SPI slave disabled until initialised, since
      boot-log traffic appears on ROOTPROBE_CS at every AQROOT reset. §9a.
- [ ] Specify the physical power-switch / hard-off topology (§6b).
- [ ] Specify the IR TX MOSFET + resistor values (§5) against the target drive current.
- [x] Select exact 3.3V buck-boost regulator part -> TI TPS63020DSJR (adjustable; support
      components still to be spec'd with it — see §8).
- [x] Select I2S audio parts -> ICS-43434 mic + MAX98357A amp (bench validation pending;
      amp shutdown pin = `AMP_SD_MODE` on U60 P03).
- [~] Display = 2.8in IPS ILI9341 capacitive SPI (matches Alpha). VERIFY exact module
      touch = FT6236 @ 0x38 before Beta order.
- [x] Power budget + runtime done -> see [[13 - Power Budget and Battery Runtime v0.1]].
      2000mAh = ~12-15hr active; ~2wk standby is ESTIMATED, pending Beta measurement (do not
      publish). Backlight timeout = top optimization.
      Battery could go 2500-3000mAh if enclosure allows.
- [~] RootProbe interface spec'd -> see [[14 - RootProbe Interface v0.1]]. ~16-18 pin
      connector, coprocessor (RP2040-class) over SPI+I2C+IRQ. Reserve connector footprint
      on main board; finalize exact host pins when RootProbe is built (Phase 2).
- [~] RF/antenna ARCHITECTURE done -> see [[12 - RF and Antenna Plan v0.1]]; remaining:
      select antenna parts + matching networks + professional RF review before PCB fab.
- [ ] ESD / external-header protection.

Validate on Beta hardware (new configs not proven in Alpha):
- [ ] **TCA9535PWR — FIRST HARDWARE VALIDATION OF THIS PART, full stop.** Datasheet-trusted
      only; no TCA9535 has ever been powered on for this project. Verify basic I/O in both
      directions on both ports before trusting anything downstream of it.
- [ ] **Two TCA9535s on one I2C bus (U60 @ 0x20 + U61 @ 0x21)**, including address-strap
      correctness (A0=GND vs A0=+3V3).
- [ ] **`/INT` behaviour + wired-OR `WAKE_INT_N` + button wake from deep sleep** — never
      exercised on the bench on any part. Include the two-devices-asserting-at-once case and
      confirm the driver's snapshot-compare identifies the right source.
- [ ] **Output-latch-before-direction ordering** — confirm no safety-critical signal glitches
      during expander configuration at boot (scope `NFC_5V_EN`, `AMP_SD_MODE`, `ACC_PWR_EN`).
- [ ] **I2C at 100 kHz first, then 400 kHz** — re-verify every device at the higher speed,
      including with an accessory on the external segment.
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
