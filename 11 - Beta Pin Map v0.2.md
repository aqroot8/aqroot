---
tags: [hardware, beta, pinmap, schematic, v0.2]
status: schematic-safe-provisional
supersedes: "10 - Beta Pin Map.md"
---

# AQROOT Beta Pin Map v0.2 — schematic-safe provisional

Consolidates corrections from a three-way review (internal / ChatGPT / Fable 5) plus the
Beta display decision. This supersedes v0.1 ("10 - Beta Pin Map.md"). Target silicon:
ESP32-S3-WROOM-1 N16R8 (octal PSRAM, native USB-CDC console).

**Status:** schematic-safe for the digital pin map. NOT production-final — several part
selections (audio, regulator, exact display P/N) and the RootProbe interface still block a
full schematic freeze. See Section 6.

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
   real issues.

3. **IR moves to native RMT pins (was the critical bug).** A 38kHz IR carrier cannot be
   generated/captured through an MCP23017 I2C expander. IR TX and RX both go to native pins
   driven by the ESP32-S3 RMT peripheral.

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
- GPIO 43/44 = default UART0 console, FREE because console runs over native USB-CDC.
- GPIO 39-42 = JTAG pins (usable; forfeits external JTAG, fine — debug over USB-Serial-JTAG).

---

## 2. SPI Bus A — Display (ILI9341) + microSD (standard SPI, shared)

| Signal | GPIO | Notes |
|---|---|---|
| SCK | 12 | shared |
| MOSI | 11 | shared |
| MISO | 13 | shared |
| Display CS | 10 | |
| Display DC | 14 | |
| Display RST | 21 | shared with touch RST (see below) |
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
| MCP23017 GPIO expander | 0x20 | poll |
| MAX17048 fuel gauge | 0x36 | poll |
| FT6236 touch | 0x38 | **poll** (frees the missing-INT issue) |
| BMI270 IMU | 0x68 | native INT1 on GPIO3 IF motion-wake needed, else poll |

- One intentional pair of I2C pull-ups (remove redundant breakout pull-ups).
- **Touch RST:** share GPIO21 with display RST (reset both at boot). MUST be stated
  explicitly or the FT6236 never wakes (Alpha gotcha: needs reset pulse to appear on I2C).
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

**IR (native RMT — the critical fix):**
| Signal | GPIO | Notes |
|---|---|---|
| IR TX | 43 | RMT carrier gen; U0RXD, output-safe at boot |
| IR RX | 44 | RMT capture; U0TXD, input ignores boot-log edges |

- IR TX needs: transistor/MOSFET driver + current-limit resistor.
- IR RX needs: supply filtering + physical separation from TX LED (avoid self-blinding).

---

## 6. Buttons + strapping-pin hygiene

| Signal | GPIO | Notes |
|---|---|---|
| BOOT/download button | 0 | MUST be native (ROM samples GPIO0 at reset). Not on expander. |
| BMI270 INT1 (optional) | 3 | only if motion-wake needed; add weak pull-down, validate boot |

**Strapping pins:**
- GPIO0 = BOOT button (normal use).
- GPIO3 = SX1262 RST + optional BMI270 INT (JTAG-select strap; acceptable, define idle state).
- GPIO45 = LEFT UNCONNECTED / test pad only (VDD_SPI strap — don't drive externally).
- GPIO46 = LEFT UNCONNECTED / test pad only (boot-mode + ROM logging; recovery margin).

---

## 7. MCP23017 expander — slow signals only

| Expander pin | Function | Notes |
|---|---|---|
| GPA0 | Touch RESET | slow control OK |
| GPA1 | SX1262 RESET | slow control OK (or keep native GPIO3 — see note) |
| GPA2 | NFC 5V boost enable | load-switch/boost enable |
| GPA3 | Audio amp enable/mute | if amp needs it |
| GPA4 | Display power/control reserve | |
| GPA5 | RGB red | conventional 3-channel RGB |
| GPA6 | RGB green | |
| GPA7 | RGB blue | OUTPUT-ONLY pin (fine for LED) |
| GPB0-GPB6 | Low-speed expansion GPIO | community add-on header |
| GPB7 | Spare output-only control | OUTPUT-ONLY pin |

**MCP23017 reality:** it has 14 bidirectional + 2 output-only pins (GPA7, GPB7), NOT 16
bidirectional. After internal control signals, the community expansion header is ~7 slow
GPIO, not 12. Recount the marketing claim accordingly.

**RGB LED note:** a conventional RGB LED needs 3 outputs (GPA5-7 here). A WS2812 addressable
LED needs precise timing and MUST NOT go on the expander — if you want addressable RGB, put
it on a native pin via RMT, or use an I2C RGB driver.

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
             +-- 3.3V BUCK-BOOST regulator (SEPARATE PART - required)
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
1. Low-speed community GPIO header (off the MCP23017, ~7 slow GPIO).
2. High-speed RootProbe accessory interface (board-to-board to the coprocessor).

Do NOT advertise MCP23017 pins as logic-analyzer channels.

---

## 10. Validation status (precise — corrects earlier over-claims)

**Validated in Alpha (SPI/electrical communication only):**
- ESP32 flashing + PSRAM config; ILI9341 display + FT6236 touch; CC1101 SPI + basic RF RX;
  SX1262 init; dual-radio shared-SPI operation + CS discipline; microSD CMD0 (0x01); NFC SPI
  chip-ID (0x2A / IC-type 0x05).

**NOT yet validated (product function):**
- microSD filesystem read/write under load; NFC tag read/write + RF range; IR; IMU; charger
  + power path; battery runtime; audio; RF performance in an enclosure; SD-on-shared-bus;
  NFC-as-3rd-SPI-device. (IR/IMU/power parts not yet delivered.)

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

Still blocking (must resolve before freeze):
- [ ] Select exact 3.3V buck-boost regulator part.
- [ ] Select exact I2S mic + amp/codec (may add enable/mode pins to the expander).
- [ ] Select exact ILI9341 module P/N (confirm touch controller = FT6236 @ 0x38).
- [ ] Compute full system power budget + battery capacity/runtime target.
- [ ] Design the RootProbe board-to-board electrical interface.
- [ ] Complete antenna/RF plan (4 RF systems: 2.4GHz WiFi, 433 CC1101, 915 SX1262, 13.56 NFC)
      — antenna types, dimensions, keep-outs, ground plane, coexistence, enclosure spacing.
      TREATED AS A BLOCKING GATE before PCB layout.
- [ ] ESD / external-header protection.

Validate on Beta hardware (new configs not proven in Alpha):
- [ ] SD on shared display bus.
- [ ] NFC as 3rd device on SPI Bus B.
- [ ] NFC RF range at 3.3V vs 5V-boosted.
- [ ] Charger thermals in enclosure.

---

## 12. Tool decision

**KiCad** (v8/v9) is the canonical design tool — unanimous across all three reviews. Open
source, plain-text files that diff/version in git (fits MIT + CERN-OHL-S ethos), mature
ESP32-S3 symbols/footprints, no vendor lock-in, community-forkable. Flux.ai OK for personal
exploration only; not the authoritative source for an open-hardware product.
