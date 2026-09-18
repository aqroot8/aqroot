# AQROOT Full Beta v2 — DEVICE SPECIFICATION (authoritative current-product index)

> **This is the authoritative current-product spec/index for what AQROOT Full Beta
> v2 physically and electrically IS.** It exists so that CTO, Claude, documentation,
> enclosure/CAD work, renders, website copy, Kickstarter material and future
> sessions do not invent, inherit stale, or misrepresent AQROOT specifications.
>
> **Authority precedence (repair this file when higher authority changes):**
> `CTO_DECISIONS.md` > current accepted schematic/PCB + accepted audits >
> `DEVICE_SPEC.md` > older architecture notes / summaries / transcripts.
>
> **PUBLIC-CLAIM SAFETY.** Before producing/approving renders, product diagrams,
> website/Kickstarter/crowdfunding copy, spec sheets, enclosure or industrial-design
> briefs, do **not** publicly claim a dimension, battery capacity, storage limit,
> antenna count, connector, protocol, frequency, feature or internal component unless
> it is marked **MARKETING-SAFE** here. If a desired claim is absent or **UNRESOLVED**,
> verify it first or omit it. Manufacturer-specific electrical/physical claims must be
> based on the exact selected MPN and its accepted evidence, not generic family knowledge.
>
> **Label key:** LOCKED · FITTED · DNP · TUNE / FIRST-ARTICLE TUNE · CAD-TO-VERIFY ·
> TBD / UNRESOLVED · INTERNAL · EXTERNAL · MARKETING-SAFE · ENGINEERING-ONLY.
>
> **Established:** 2026-08-30 (FBV2-P2-004A / D-301, at a safe committed milestone
> boundary). **Grounded in** the accepted schematic (9 functional sheets under
> `hardware/beta-v2/kicad/aqroot-beta-v2/`), the assembly BOM / population matrix,
> the mechanical interface spec, the I²C registry, and accepted audits. Where a
> repository value is not authoritative it is marked UNRESOLVED — no value is invented
> to fill a table.

---

## 0a. AQROOT **DEMO** DELTA — READ THIS BEFORE ANY KICKSTARTER CLAIM (D-743, 2026-09-18)

> **THIS DOCUMENT DESCRIBES FULL BETA v2, THE PRODUCTION DESIGN.  THE BOARD BEING
> FABRICATED AND DEMONSTRATED FOR KICKSTARTER IS AQROOT *DEMO*, WHICH IS DERIVED
> FROM IT AND IS NOT IDENTICAL.**  `AQROOT_DEMO_SCOPE.md` is explicit: *"Do not
> claim that an electrically unimplemented Demo connector pin is functional"*, and
> production capabilities may be described as *planned/final-production* only when
> clearly distinguished from the prototype actually being shown.  Every row below
> is a place where copy written from this document alone would overstate the unit
> in the demonstrator's hand.  Demo evidence lives under `hardware/demo/`.

| capability | Full Beta v2 (this document) | **AQROOT Demo as fabricated** | ruling |
|---|---|---|---|
| Community Port expansion GPIO | 10 public `XGPIO0`–`XGPIO9` | **TWO — `XGPIO4` and `XGPIO5` only.**  `J5.9`–`J5.12` and `J5.15`–`J5.18` are **electrically NC** | Demo scope; `routing_ledger.py` `APPROVED_NC` |
| GPIO expanders | three PCAL9535A — `U2`, `U3`, `U23` | **two.  `U23` is REMOVED** | Demo scope |
| NFC 5 V PA boost `U13` | fitted (§6.3 of this document still says FITTED — **that row is wrong even for Demo**) | **DNP.  NFC runs from the 3.3 V path** | Demo scope "Already unnecessary / DNP" |
| Charger status decode | `STAT1` + `STAT2` both landed, full four-state decode | **`STAT2` (`U11.3`) UNCONNECTED.**  `STAT1` LOW = fault is directly observed; charging-versus-complete is an INFERENCE | owner decision 2026-09-17, D-742 |
| Charge current / input limit | not previously fixed anywhere | **`ICHG` 769 mA (`R37` 390 Ω), input limit 1100 mA (`R36` 13 kΩ), `VBATREG` 4.2 V** | D-743 |
| Charging source | not previously stated | **charge from a 1 A or better USB source.**  A 500 mA-class port charges more slowly and will not complete a cycle inside the charger's 360 min safety timer | D-743 |
| Speaker `LS1` | on the BOM | **OFF-BOARD**, 152 mm flying leads (`aqroot-Demo-OFF-BOARD.csv`) | fab package |
| Battery capacity | 2500–3000 mAh envelope | **2500 mAh first-five pack SELECTED: Adafruit Product 328**, protected 1S LiPo with genuine JST-PH. Supplier-linked 785060 specification permits ≤2C discharge (5 A for 2500 mAh); CTO-BAT-01 contract requires ≥2.675 A against the live D-753 2.229 A board envelope plus 20 % margin | CTO-BAT-01 |

> Everything else in the Demo — ESP32-S3, 16 MB flash / 8 MB PSRAM, the 3.5-inch
> touchscreen, D-pad and A/B, power switch, recessed BOOT, RGB indicator, Wi-Fi,
> BLE, 433 MHz with its internal antenna, 915 MHz LoRa with its external antenna,
> NFC with its internal antenna, IR transmit and receive, speaker, microphone,
> BMI270, microSD, USB-C data and charging, battery, charger, the battery-safety
> architecture, the fuel gauge, the physical 1×24 Community Port with its GND
> contacts, 3.3 V accessory power, one usable 5 V accessory output, software
> switched 3.3 V and 5 V, SDA, SCL, both native GPIO and Accessory Detect, and the
> Qwiic / STEMMA QT connector — **is retained and is fabricated on the Demo board.**

---

## 0. Product summary (MARKETING-SAFE unless a row says otherwise)

AQROOT Full Beta v2 is a portable, battery-powered, multi-radio wireless / RF /
NFC exploration and automation handheld built around an **ESP32-S3** SoC with a
**3.5-inch capacitive touch display**, **four radios** (Wi-Fi + Bluetooth LE,
433 MHz, 915 MHz LoRa, 13.56 MHz NFC), an **IR transmit/receive** pair, **audio in
and out**, a **6-axis IMU**, a **microSD** slot, **USB-C**, and a **24-line community
expansion port** plus a **Qwiic / STEMMA QT** accessory connector. It runs from a
single-cell Li-ion battery with USB-C charging and a reverse-/over-voltage protection
front end.

- **Form factor:** portrait handheld. **PCB 77 × 148 × 1.6 mm maximum, 6-layer**
  — the profile is STEPPED: 72.000 mm wide except an east bump to `x = 77.000`
  between `y = 70.500` and `y = 104.005` (REVISED D-709 under owner authority
  D-703 option 2; ~~72 × 148~~ superseded).  **Enclosure 85 × 160 × 23 mm**
  external (REVISED D-709, width only, under owner approval D-707; ~~80 × 160 ×
  23~~ superseded — a 77 mm board does not enter an 80 mm shell at the ≥ 1.5 mm
  wall gap).  **Section 12 is the dimension authority and this summary now
  agrees with it.**
- **Radios:** 4 (Wi-Fi/BLE, 433 MHz, 915 MHz LoRa, NFC). **Antennas: 4 total — 1
  external (915 MHz SMA whip), 3 internal** (Wi-Fi/BLE module PCB antenna, 433 MHz
  internal flex, NFC internal flex). MARKETING-SAFE.

---

## 1. Digital core — MCU & memory

| Item | Value | Label | Evidence |
|---|---|---|---|
| SoC / module | **Espressif ESP32-S3-WROOM-1** (`U1`) | LOCKED · FITTED · INTERNAL | `02_mcu_core.kicad_sch:U1` |
| Exact MPN | **ESP32-S3-WROOM-1-N16R8** (LCSC C2913202) | LOCKED | `02_mcu_core.kicad_sch:U1` (MPN); `architecture/ARCHITECTURE.md` |
| Flash | **16 MB** (quad) | LOCKED · MARKETING-SAFE | N16R8 variant; ARCHITECTURE.md |
| PSRAM | **8 MB octal** | LOCKED · MARKETING-SAFE | N16R8 variant; ARCHITECTURE.md |
| Radio (integrated) | Wi-Fi 802.11 b/g/n (2.4 GHz) + Bluetooth / BLE | LOCKED · MARKETING-SAFE | module datasheet; see §5 |
| Note | GPIO35/36/37 unusable (octal PSRAM), left NC | ENGINEERING-ONLY | ARCHITECTURE.md |
| BOOT strap button | `SW1` (C&K PTS645SM43SMTR92LFS) | FITTED | `02_mcu_core.kicad_sch:SW1` |

Programming/console is over the **native ESP32-S3 USB** (USB Serial/JTAG on
GPIO19/20); there is **no USB-UART bridge IC** (by design). See §9, §16.

---

## 2. Display & touch

| Item | Value | Label | Evidence |
|---|---|---|---|
| Panel (off-board) | EastRising **ER-TFT035IPS-6**, 3.5″ IPS TFT | LOCKED · FITTED · INTERNAL (off-board module) · MARKETING-SAFE (3.5″ display) | `assembly/OFF_BOARD_BOM.md`; ARCHITECTURE.md |
| Resolution | **320 × 480** | LOCKED · MARKETING-SAFE | OFF_BOARD_BOM.md; ARCHITECTURE.md |
| Display driver | **ILI9488** (COG) | LOCKED (per ARCH/BOM & D-074…D-078) | ARCHITECTURE.md; OFF_BOARD_BOM.md — see conflict note |
| Interface | 4-wire **SPI** (SPI-A bus) | LOCKED | `03_spi_a_display_sd.kicad_sch` |
| On-board FPC connector | `J1` **Hirose FH69-50S-0.5SH** (50-pin, 0.5 mm) | FITTED · MANUAL ASSEMBLY | `03_spi_a_display_sd.kicad_sch:J1` |
| Tail **pin-1 end** | **RIGHT-hand end viewed from the display face, tail down** — and `J1` pin 1 is the right-hand end of its row (`x = 44.910`, `F.Cu`). **Pin 1 meets pin 1; no mirror** | **RESOLVED at D-754** from the vendor outline drawing | `evidence/d754-display-tail-orientation.json` |
| Touch panel | EastRising **ER-TPC035-6** capacitive | LOCKED · FITTED · INTERNAL | OFF_BOARD_BOM.md |
| Touch controller | **FocalTech FT6236** @ I²C **0x38** | LOCKED (interface); **silicon identity CAD-TO-VERIFY** | `architecture/I2C_ADDRESS_REGISTRY.md`; ARCHITECTURE.md |
| Backlight driver | `U17` **TPS61169DCKR** (WLED boost) | FITTED | `03_spi_a_display_sd.kicad_sch:U17` |
| Backlight **true-off disconnect** | `Q11` **AO3400A** (LCSC C20917) in the panel cathode return, gate on its OWN net `BL_DISC_G` | FITTED (added D-750, re-controlled D-752) | `03_spi_a_display_sd.kicad_sch:Q11`; D-750 item 7; D-752 |
| Backlight disconnect **gate hold** | `D14` **1N4148WS** (LCSC C2128) + `C85` 100 nF + `R132` 220 k — charges from `DISP_BL_CTL`, decays with τ = 22 ms | FITTED (added D-752) | `03_spi_a_display_sd.kicad_sch:D14/R132/C85`; D-752 |
| Display SDO isolation | `R112` 0 Ω = **DNP** | DNP | population matrix |

> **WHY `Q11` EXISTS (D-750, external first-spin review item 7).**  TI states
> that the `TPS61169` retains a DC path from `VIN` through the inductor and
> Schottky to the LEDs in shutdown, and guarantees OFF only when the LED
> array's minimum forward voltage exceeds the maximum `VIN`.  This panel's
> backlight is **2.9–3.2 V at 120 mA** (D-079) on a **3.3 V** rail — **six diodes in
> parallel from one common `LED-A`, cathodes grouped `LED-K1`/`LED-K2` onto tail
> pins 2 and 3, read off the vendor outline drawing at D-754** — so the
> condition FAILS: solving the shutdown network converges at **≈ 25 mA**, about
> a fifth of full brightness and plainly visible in the dark.  There is no
> firmware mitigation, because `+3V3` is switched by the `SW9` slide switch.
> `Q11` is outside the regulation loop by construction (`U17`'s LED pin and
> `R69` both sit on its SOURCE), so the 109 mA setpoint and its 100.5–117.6 mA
> band are unchanged.
>
> **`Q11`'s GATE MAY NOT SHARE `U17`'s `CTRL`, AND D-752 SEPARATED THEM.**
> D-751 recorded the shared net as a safety CONSTRAINT.  **That was wrong, and
> the primary source says so.**  TI `SNVSA40B` §6.3.5: the `TPS61169` "chops up
> the internal 204 mV reference voltage at the duty cycle of the PWM signal",
> filters it, and therefore *"only the WLED DC current is modulated, which is
> often referred as analog dimming"* — **the converter keeps switching through
> every PWM low phase**, and enters shutdown only after `CTRL` has been low for
> more than `tSD`, **2.5 ms max**.  With one net driving both, every PWM low
> phase opened the LED string while `U17` regulated: `FB` collapses below the
> 30 mV open-LED threshold, `SW` ramps to `VOVP_SW` (**36 / 37.5 / 39 V**),
> §6.3.2 open-LED protection latches the part off after three switching cycles,
> and the panel cathode — `Q11`'s DRAIN — follows the anode to ≈ 36 V while
> `R69` holds the SOURCE at 0 V.  **The `AO3400A` is a 30 V part** (AOS Rev 3.1).
> Firmware already drives `ledcSetup(5000, 8)` on GPIO46, so the board would
> have latched its backlight off and over-stressed `Q11` on the first
> brightness ramp.
>
> **THE REPAIR IS STRUCTURAL, NOT PROCEDURAL (D-752).**  `Q11`'s gate moved to
> its own net `/03_SPI_A_DISPLAY_SD/BL_DISC_G`, driven by an ENVELOPE of
> `DISP_BL_CTL`: `D14` (1N4148WS) charges `C85` (100 nF) from it in
> microseconds, `R132` (220 k) discharges it with **τ = 22 ms**.  The invariant
> is waveform-independent — *`Q11` cannot open until the gate has decayed below
> `VGS(th)`, which takes at least **11.4 ms** at worst-case tolerance, and
> `U17` is guaranteed to be in shutdown by **2.5 ms***.  The converter
> therefore always stops first, for ANY `CTRL` waveform, including an
> out-of-spec PWM frequency or a firmware crash.  **Margin 4.6×**, and no
> firmware sequencing is relied upon.
>
> * **worst-case hold.**  `Vf` ≤ 0.7 V at the 12.5 µA hold current gives a
>   2.60 V gate; τ at tolerance extremes is 19.6–24.4 ms; `VGS` at 2.5 ms is
>   **2.29 V**, above the `RDS(on)` spec point.  Droop over the longest low
>   phase the part specifies (5 kHz at 1 % duty = 199 µs) is **26 mV**.
> * **turn-on.**  `C85` charges through `D14` from the GPIO in ≈ 25 µs against
>   `U17`'s **6.5 ms** soft-start, so `Q11` is fully on before the converter
>   delivers current.
> * **why silicon and not a Schottky.**  The OFF state is held by `R132`:
>   `D14`'s worst PUBLISHED reverse leakage (1 µA at 75 V; ours is 2.7 V) plus
>   the `AO3400A`'s 100 nA `IGSS` across 220 k is **0.242 V**, against
>   `VGS(th)` min **0.65 V**.  A `BAT54WS` would have rested that floor on an
>   unpublished leakage curve at temperature.
> * **cost.**  `RDS(on)` ≤ 48 mΩ at `VGS` 2.5 V is **5.2 mV** at 109 mA; the
>   109 mA setpoint and its 100.5–117.6 mA band are unchanged.
> * **mechanised.**  `checks/demo_feature_contract.py` **F5** requires the two
>   nets to be distinct, the gate net to carry exactly `Q11.1`/`D14.1`/
>   `R132.1`/`C85.1`, `D14.2` to sit with `U17.4`, both hold legs to return to
>   `GND`, and the `220k`/`100nF`/`1N4148` identities to hold — with **four
>   live negative controls**, including one that puts the shared gate back.

**Conflicts flagged (do not carry stale values into public copy):**
- **Display driver:** ARCHITECTURE/OFF_BOARD_BOM lock **ILI9488** (320×480); the KiCad
  symbol carries stale placeholder text (`ILI9341` / a CH280QV10 pin-table). The
  authoritative part is **ER-TFT035IPS-6 / 320×480 / ILI9488**.
- **Touch controller identity:** the interface (I²C 0x38, INT/RST) is LOCKED; the
  silicon is asserted FT6236 by ARCH/BOM but a panel datasheet names **CST026**. The
  purchase order must explicitly specify FT6236. → **CAD-TO-VERIFY / procurement-verify.**

---

## 3. Storage — microSD

| Item | Value | Label | Evidence |
|---|---|---|---|
| Slot | `J2` **Molex 5025700893** (push-push, card-detect) | FITTED · EXTERNAL (bottom edge) | `03_spi_a_display_sd.kicad_sch:J2` |
| Interface | **SPI-A**, dedicated CS on GPIO48 | LOCKED | ARCHITECTURE.md |
| Card-detect | connector pad present; `R113` 100 k pull-up, **not wired in firmware path** | ENGINEERING-ONLY | `03_...:R113`; ARCHITECTURE.md |
| Card capacity | **UNRESOLVED** — no repo doc fixes a max card size | TBD | — (do not claim a GB limit publicly) |

---

## 4. USB

| Item | Value | Label | Evidence |
|---|---|---|---|
| Connector | `J3` **GCT USB4105-GF-A-120** USB-C receptacle, USB 2.0, 16-contact | FITTED · EXTERNAL (bottom edge) · MARKETING-SAFE (USB-C) | `01_power_tree.kicad_sch:J3` |
| Data | **Native ESP32-S3 USB** (GPIO19/20, 22 Ω series); USB-CDC / USB Serial-JTAG | LOCKED | ARCHITECTURE.md |
| Role | **Sink / UFP, 5 V only** — no USB-PD, no source role, SBU1/2 NC | LOCKED · ENGINEERING-ONLY | ARCHITECTURE.md |
| ESD | `U10` **USBLC6-2SC6** | FITTED | `01_power_tree.kicad_sch:U10` |
| USB-UART bridge | **NONE** (native USB only) | LOCKED | ARCHITECTURE.md |

---

## 5. Radios & antenna architecture

**Four radios across five bands. Four antennas total: 1 EXTERNAL, 3 INTERNAL.**
By design **no 433/915 RF signal reaches the main PCB** (no board RF traces, no board
matching for the sub-GHz radios — the modules carry their own front ends and IPEX
sockets); the only on-board RF network is the 13.56 MHz NFC differential front end.

| Band | Radio (designator) | Exact MPN | Interface | Antenna | INT/EXT | Count | Label |
|---|---|---|---|---|---|---|---|
| Wi-Fi 2.4 GHz + BLE | ESP32-S3 module (`U1`) | ESP32-S3-WROOM-1-N16R8 | integrated SoC | module **onboard PCB trace antenna** | **INTERNAL** | 1 | LOCKED · FITTED · MARKETING-SAFE |
| 433 MHz | Ebyte E07 (`U7`) | **E07-400M10S** (CC1101, 410–450 MHz, +10 dBm) | SPI bus B | on-module IPEX/u.FL → **Taoglas FXP450.07.0100C** internal flex | **INTERNAL** | 1 | FITTED · MARKETING-SAFE (433 MHz) |
| 915 MHz LoRa | Ebyte E22 (`U8`) | **E22-900M22S** (SX1262, 850–930 MHz, +22 dBm) | SPI bus B | on-module IPEX → **CBA-UFLSMA20IP** pigtail → top-panel **SMA(F) bulkhead** → **Taoglas TI.92.2113** SMA(M) dipole | **EXTERNAL** | 1 | FITTED · MARKETING-SAFE (915 MHz LoRa, external antenna) |
| 13.56 MHz NFC | ST (`U9`) | **ST25R3916-AQET** (UFQFPN-32; crystal `Y1` 27.12 MHz) | SPI bus B | off-board **Taoglas FXC.46.52.0075X.B.dg** flex via `J7`, bonded to inner rear shell | **INTERNAL** (reads through rear plastic) | 1 | FITTED · MARKETING-SAFE (NFC) |

- **Antenna count: EXTERNAL = 1** (915 MHz SMA whip via top-panel bulkhead);
  **INTERNAL = 3** (Wi-Fi/BLE module PCB antenna; 433 MHz internal flex; NFC internal
  flex). **Total = 4.** MARKETING-SAFE.
- **NFC matching network** (`C69`–`C80`, `L5`/`L6` = Murata LQW18AN39NG80D 39 nH,
  `R114`–`R117`) is **TUNE / FIRST-ARTICLE TUNE** — final values pending VNA + ST
  STSW-ST25R004 (probe `TP37`/`TP38` = NFC_ANT_A/B). ENGINEERING-ONLY until tuned.
- **NFC 5 V PA boost branch is DNP** on the first build (NFC runs from +3V3 via `R106`
  FIT / `R107` DNP): `U13` boost path caps `C34`/`C35`, etc. DNP.
- **Six ST25R3916 pins deliberately NC** (recorded ERC exclusions): CSO, EXT_LM,
  AAT_A, AAT_B, CSI, MCU_CLK. ENGINEERING-ONLY.

**Conflicts flagged:**
- **915 antenna:** the `U8` schematic package note and a stale ARCHITECTURE row name an
  internal `Taoglas FXP890.07.0100C` flex. This is **STALE**. The locked selection (CTO
  D-198) is the **EXTERNAL SMA `Taoglas TI.92.2113`** dipole on a top-panel bulkhead.
- **NFC antenna variant:** the authoritative part is the **`.B.dg` (reverse-ferrite)**
  variant (D-131); any `.A.dg` reference is superseded.

---

## 6. Power, battery, charging & protection

### 6.1 Battery & charging
| Item | Value | Label | Evidence |
|---|---|---|---|
| Cell | 1S Li-ion / LiPo pouch | LOCKED (chemistry) · INTERNAL | `01_power_tree.kicad_sch`; OFF_BOARD_BOM.md |
| Battery connector | `J4` **JST-PH-2** (B2B-PH-K-S(LF)(SN)) | FITTED · INTERNAL | `01_power_tree.kicad_sch:J4` |
| Envelope | ≈ **2500–3000 mAh** target; cell envelope 57 × 75 × 8.0 mm MAX (D-243) | TARGET · CAD-TO-VERIFY | CTO_DECISIONS D-071/D-243; OFF_BOARD_BOM.md |
| **Exact fitted capacity** | **2500 mAh — Adafruit Product 328 selected for the first five (CTO-BAT-01).** Current supplier page specifies a protected pack with genuine JST-PH; its linked `785060` pack specification is pinned in-repo at SHA-256 `826149da…ecd3`, max pack 7.9 × 50.5 × 60.5 mm, max charge 1C and operating discharge current ≤2C. The supplier's conservative charge recommendation is 1.2 A, above this board's 0.855 A worst programmed envelope. Incoming polarity must be meter-verified before J4 connection. | **SELECTED · ENGINEERING-ONLY** | `assembly/SELECTED_BATTERY.json`; `checks/battery_pack_contract.py` |
| Charger | `U11` **BQ25185DLHR** (1S Li-ion linear charger) | FITTED · INTERNAL | `01_power_tree.kicad_sch:U11` |
| Charge current (ICHG) | **769 mA** — `R37` 390 Ω on ISET, `ICHG = KISET / RISET` with `KISET` 300 AΩ (SLUSF65B §6.1.1.4).  Input limit **1100 mA** and `VBATREG` **4.2 V** from `R36` 13 kΩ (Table 6-1).  Full cycle ≈ 240–290 min against the part's **360 min** `tMAXCHG` safety timer | **RESOLVED at D-743** · ENGINEERING-ONLY | `01_power_tree.kicad_sch:R36,R37`; CTO_DECISIONS D-743; `evidence/d743-rail-ampacity.json` |
| Charge source requirement | **1 A or better.**  The USB-C port is a plain 5.1 kΩ Rd sink and does not read the source's Rp advertisement; a 500 mA-class port is folded back by the charger's VINDPM and will not complete a cycle inside `tMAXCHG` | MARKETING-SAFE (state it as "charge from a 1 A USB adapter") | D-743 |
| Fuel gauge | `U14` **MAX17048G+T10** @ I²C 0x36 | FITTED | `01_power_tree.kicad_sch:U14` |
| Power switch | `SW9` **JS102011SAQN** SPDT slide (hard rail off) | FITTED · EXTERNAL (right wall) | `01_power_tree.kicad_sch:SW9`; `R68` 0 Ω bypass must stay DNP |

### 6.2 Reverse-/over-/under-voltage protection front end
| Item | Value | Label | Evidence |
|---|---|---|---|
| Ideal-diode + OV/UV/reverse-current controller | `U18` **LTC4368IMS-1#TRPBF**, LCSC `C688401`, **MSOP-10** (the "-1", so it does NOT block forward charge). **D-615 corrected the order code: the schematic carried `LTC4368IDD-1#PBF`, and `DD` is DFN-10 against an MSOP-10 land — D-099 / FBV2-PWR-002 require this part to be leaded and inspectable.** | FITTED · LOCKED (safety) | `01_power_tree.kicad_sch:U18` |
| Back-to-back reverse-protection FETs | `Q2`, `Q3` **NTMD4820NR2G** (anti-series pairs) | FITTED · LOCKED (safety) | `01_power_tree.kicad_sch:Q2,Q3` |
| Current-sense resistor | `R75` **15 mΩ 1 % 1 W** (Kelvin pair to U18.8/U18.9); D-615 selected Bourns **`CRA2512-FZ-R015ELF`**, LCSC `C2073490`, a **CURRENT-SENSE class part at ±50 ppm/°C, 3 W** — a thick film at ±1500 ppm/°C would move the 3.33 A LTC4368 trip ~19 % over −40…+85 °C | FITTED | `01_power_tree.kicad_sch:R75` |
| Protected-node Schottky | `D9` **PMEG2010AEH,115** | FITTED | `01_power_tree.kicad_sch:D9` |
| Recovery / dead-cell comparator | `U19` **TLV7032DDFR** (dual) | FITTED | `01_power_tree.kicad_sch:U19` |

LTC4368-**2** was explicitly rejected (would block charge current). The reverse-polarity
provision is the LTC4368-1 + Q2/Q3 anti-series FET chain (the BQ25185 BAT pin has none).
LOCKED safety architecture — see `POWER_FAULT_STATE_TABLE.md`, the independent
power/NFC review, and CTO decisions.

### 6.3 Regulators, rails & switches
| Rail / role | Designator | MPN | Label | Evidence |
|---|---|---|---|---|
| **+3V3** main (buck-boost) | `U12` | **TPS63020DSJR** | FITTED | `01_power_tree.kicad_sch:U12` |
| ~5 V boost (NFC/LED) | `U13` | TPS61023DRLR | **DNP on AQROOT Demo** (D-743 corrected this row; it read FITTED).  NFC runs from the 3.3 V path — see §0a | `01_power_tree.kicad_sch:U13`; `aqroot-Demo-DO-NOT-POPULATE.csv` |
| **ACC_5V_RAW** ~5 V boost (accessory) | `U21` | TPS61023DRLR | FITTED | `01_power_tree.kicad_sch:U21` |
| **ACC_3V3_SW** load switch | `U20` | TPS22950CDDCR | FITTED | `01_power_tree.kicad_sch:U20` |
| **ACC_5V_SW** load switch | `U22` | TPS22950CDDCR | FITTED | `01_power_tree.kicad_sch:U22` |
| Accessory I²C hot-swap buffer | `U16` | TCA4307DGKR | FITTED | `08/09` |

### 6.3a Accessory-power ENVELOPE (D-753) — ENGINEERING-ONLY, **bounded by hardware**

**D-750 answered the external first-spin review's combined-load item with a
POLICY; D-753 replaced it with a LIMIT the silicon enforces.**  The policy read
*"firmware must not raise both accessory rails to their per-rail maxima
together"* — and this board has **no accessory current measurement**.  Firmware
can choose whether a rail is ON; it cannot know what an arbitrary external
accessory then draws.  The only thing that actually bounds an accessory is the
`TPS22950C`'s own current limit, and at the values D-750 shipped those limits
sat far ABOVE what the policy permitted.

**BOTH `ILIM` RESISTORS ARE NOW 2.7 kΩ** (`R97` was 1.5 kΩ, `R101` was
1.65 kΩ; LCSC `C13167`, JLCPCB BASIC).  TI `SLVSFJ2B` equation 1 —
`ILIM = 1.18 × (R[kΩ])^−1.072` — gives **0.407 A typ**, and the widest tolerance
ratio the part's own EC table publishes (0.68× / 1.32× of typ over −40…+125 °C)
brackets each rail at **0.277 A guaranteed / 0.537 A worst case**.

Modelled at the 3.0 V cell corner with the full 1.0 A internal `+3V3` load,
`U12` at 90 % and `U21` at 88 % into 4.95 V:

| state the Community Port can reach | WAS (1.5 k / 1.65 k) | NOW (2.7 k / 2.7 k) |
|---|---|---|
| 3.3 V rail alone at its limiter | 2.455 A | **1.879 A** (+27 %) |
| 5 V rail alone at its limiter | **2.930 A — TRIPS** | **2.229 A** (+13 %) |
| both rails at their GUARANTEED currents | **2.737 A — TRIPS** | **2.079 A** (+19 %) |
| both limiters in fault (double fault) | 4.162 A — past the LTC4368 | 2.886 A — charger OCP, auto-retry |

against a `BQ25185` `IBAT_OCP` **MINIMUM of 2.5625 A** (3.125 A typ ± 18 %,
`SLUSF65B`), the `LTC4368` trip at **3.33 A** (50 mV across `R75` 15 mΩ) and
`F1` at 5 A.

> **ENVELOPE.**  No state a user can reach with conforming accessories exceeds
> the pack protection's minimum trip; the worst is **2.229 A, 13 % under it**.
> A *simultaneous double limiter fault* — two accessories each in overcurrent at
> once — reaches 2.886 A, which trips the charger's own `IBAT_OCP` and
> **auto-retries**, below the `LTC4368` and far below the one-shot fuse.  Each
> rail GUARANTEES **0.277 A**, which is MORE than the superseded policy
> permitted at this corner (0.15 A at 5 V / 0.23 A at 3.3 V).
> `checks/demo_feature_contract.py` **F6** recomputes all of this from the two
> resistors the board actually carries, with four live negative controls —
> including two that put the D-750 values back.

**RESIDUAL, NAMED NOT HIDDEN.**  `.kicad_dru` section 5 sizes `BAT_MAIN` copper
for **1.5 A sustained**.  The new worst *sustained* case — both accessories at
their guaranteed current with the full internal load — is **1.69 A at 3.7 V**
and **2.08 A at the 3.0 V cutoff corner**, so it still exceeds that sizing
point at the low-battery end, on one unavoidable 5.525 mm × 0.200 mm segment:
`U11`'s `DLH0010A` pin-2 `BAT` land, which nothing wider can land on (D-269,
D-708).  The plane-coupled model this repository uses puts that segment's
ceiling at ≈ 37 K over the adjacent `In4` plane at 2.08 A (≈ 19 K at 1.5 A),
and the model explicitly ignores lateral spreading, conduction along the copper
and convection from an OUTER layer, so it is a ceiling and not a prediction.
**This is a FIRST-ARTICLE THERMAL MEASUREMENT**, not a pre-order blocker: the
electrical envelope above is closed by hardware, and D-753 moves every number in
this table DOWN from what D-750 shipped.

### 6.4 Safety floors (governing routing rules — ENGINEERING-ONLY)
- **BAT_MAIN** netclass (1.5 A design): trunk 1.00 mm, min **0.60 mm** (LOCKED).
- **BAT_PROTECTED_P (BPP)** high-current trunk **≥ 1.20 mm** (D-249, LOCKED).
- Current-path routed clearance **0.300 mm** (D-269, LOCKED).
- These are hard floors, all ENFORCED (not relaxed) in the first authoritative copper. **FBV2-P2-004B2 / D-302:** the Phase-A battery-block copper is now PROMOTED (the `U11.2` BPP trunk wall is closed by an on-net ≥1.20 mm tap to `C36.1`); the board carries 432 tracks / 54 vias / 6 layers with zero new copper DRC classes. **Phase-A copper only — the board is not yet fully routed** (Phase B pending, `FBV2-P2-005`).

---

## 7. Sensors & IMU

| Item | Value | Label | Evidence |
|---|---|---|---|
| IMU | `U4` **Bosch BMI270**, 6-axis (accel + gyro) @ I²C **0x68** | FITTED · INTERNAL · MARKETING-SAFE (6-axis IMU) | `05_i2c_devices.kicad_sch:U4`; `I2C_ADDRESS_REGISTRY.md` |
| IMU alt address | 0x69 (rework only: remove `R118` 0 Ω, fit `R119` 0 Ω to +3V3) | DNP (alt) · ENGINEERING-ONLY | I2C registry (D-140) |
| Other I²C sensors | **NONE** — `U4` is the only device on sheet 05 | — | `05_i2c_devices.kicad_sch` |

No separate light/temp/hall/magnetometer sensor is fitted. Do not claim any sensor
beyond the 6-axis IMU.

---

## 8. Audio, microphone & IR

| Item | Value | Label | Evidence |
|---|---|---|---|
| Class-D amp | `U5` **MAX98357AETE+T** (I²S in) | FITTED (was DNP in Beta-DM; FIT per D-144) | `06_audio.kicad_sch:U5` |
| Speaker (off-board) | `LS1` **PUI AS02008MR-LW152-R** (Ø20 × 3, 8 Ω 0.5 W) via `J6` JST-PH-2 | FITTED · INTERNAL | `06_audio.kicad_sch:LS1,J6`; OFF_BOARD_BOM.md |
| Microphone | `MK1` **PUI DMM-4026-B-I2S-R** (bottom-port I²S MEMS) | FITTED · INTERNAL (acoustic port) | `06_audio.kicad_sch:MK1` |
| Codec | **NONE** — direct I²S mic + amp to ESP32-S3 | LOCKED | ARCHITECTURE.md |
| IR receiver | `U6` **Vishay TSOP38238** (38 kHz) | FITTED · EXTERNAL (top window) | `07_ir.kicad_sch:U6` |
| IR emitter | `D1` **Vishay TSAL6100** (940 nm, 5 mm THT) | FITTED · MANUAL (THT) · EXTERNAL (top window) | `07_ir.kicad_sch:D1` |
| IR drive FET | `Q1` AO3400A (low-side) | FITTED | `07_ir.kicad_sch:Q1` |
| IR drive trim | `R123` 100 Ω = **DNP** | DNP | `07_ir.kicad_sch:R123` |

MARKETING-SAFE: speaker audio out, microphone in, IR transmit + receive.

---

## 9. Buttons, indicators & GPIO expanders

| Item | Value | Label | Evidence |
|---|---|---|---|
| User buttons (6) | `SW2`–`SW7` **PTS645SM43SMTR92LFS**: UP / DOWN / LEFT / RIGHT / A_SELECT / B_BACK | FITTED · EXTERNAL (front) · MARKETING-SAFE (D-pad + A/B) | `08_buttons_expanders.kicad_sch` |
| BOOT button | `SW1` (recovery/download strap) | FITTED · EXTERNAL (recessed, tool-only) | `02_mcu_core.kicad_sch:SW1` |
| Power slide switch | `SW9` (see §6) | FITTED · EXTERNAL (right wall) | `01_power_tree.kicad_sch:SW9` |
| RGB status LED | `D13` **MHPA3528RGBCT** (PLCC-4, driven by R124/R125/R126) | FITTED · EXTERNAL (front, diffuser/light-pipe) | `08_buttons_expanders.kicad_sch:D13` |
| GPIO expanders (3) | `U2` (0x20), `U3` (0x21), `U23` (0x22) **NXP PCAL9535APW,118** | FITTED on Full Beta v2; **`U23` REMOVED on AQROOT Demo — see §0a** | `08_...`; I2C registry |

HOME (SW8) and both Volume buttons were **REMOVED** and must not reappear. Do not
claim a HOME or Volume button.

---

## 10. Community expansion & accessory connectors

### 10.1 Community expansion port `J5` — 24-contact
| Item | Value | Label | Evidence |
|---|---|---|---|
| Connector | `J5` **1 × 24, 2.54 mm right-angle female** receptacle (Samtec **SSQ-124-02-G-S-RA**, LCSC **C3323671**, verified live 2026-09-18 per D-096; superseded the 2×12 BCS-112-S-D-HE at D-237 — **D-750 corrected the MPN/LCSC/description, which the released BOM had left on the superseded part**) | FITTED · MANUAL/SECONDARY ASSEMBLY · EXTERNAL (right edge) · MARKETING-SAFE (24-pin expansion) | `09_community_header.kicad_sch:J5`; `EXPANSION_ECOSYSTEM_PROPOSAL.md` (D-237/D-240); `evidence/jlc-live/ssq-124-02-g-s-ra-b06f80e6.json` |
| Contact count | **24** (one contact per line) | LOCKED | audit `2026-08-24-expansion-and-refloorplan-implementation.md` |
| Logic level | **3.3 V logic only**; the 5 V pins are **power output only** | LOCKED · MARKETING-SAFE (labelled on enclosure) | mechanical spec; expansion proposal |

**ORDER-B pinout (LOCKED, 180°-reversal-safe — D-240):**
```
 1 5V    2 G     3 3V3   4 SDA   5 SCL   6 G     7 N38   8 N47
 9 X0   10 X1   11 X2   12 X3   13 X4   14 X5   15 X6   16 X7
17 X8   18 X9   19 G    20 WAKE  21 DET  22 3V3  23 G    24 5V
```
Functions: 2× `ACC_5V_SW`, 2× `ACC_3V3_SW`, 4× GND, `EXT_SDA`, `EXT_SCL`,
`NATIVE_A`/GPIO38, `NATIVE_B`/GPIO47, `WAKE_ATTN_N`, `ACC_DETECT_N`, `XGPIO0`–`XGPIO9`
(the ten slow expander I/O). Per-pin current 6.3 A (2 pins powered). ENGINEERING-ONLY
detail; the capability (I²C + 2 native GPIO + 10 expander GPIO + switched 3V3/5V) is
MARKETING-SAFE.

### 10.2 Qwiic / STEMMA QT `J8`
| Item | Value | Label | Evidence |
|---|---|---|---|
| Connector | `J8` **JST SM04B-SRSS-TB(LF)(SN)** SH 1.0 mm 4-pin | FITTED · EXTERNAL (right wall) · MARKETING-SAFE (Qwiic/STEMMA QT) | `09_community_header.kicad_sch:J8` |
| Pinout | 1 GND · 2 ACC_3V3_SW · 3 EXT_SDA · 4 EXT_SCL | LOCKED | audit 2026-08-24 |
| Power | **ACC_3V3_SW only** (5 V never present on Qwiic) | LOCKED | expansion proposal |
| MPN/LCSC in schematic | **MPN WRITTEN** `SM04B-SRSS-TB(LF)(SN)` / Manufacturer `JST` (D-614, the plating-suffixed string D-096 requires); **LCSC `C160404` WRITTEN TOO** — this row said *"LCSC still absent"* until **D-762** and had been wrong since **D-615**, which §16 item 8 of this same document already recorded as CLOSED | FITTED · orderable by MPN **and** by LCSC | `09_...:J8`; `aqroot-Demo-BOM-assembly.csv` |
| Land pattern | **RULED AT D-762 against JST's own `eSH.pdf`** (p.1 *PC board layout*, **SIDE ENTRY** figure; p.3 header table for `A`), archived `vendor/JST/jst-sh-connector-eSH-2024-10.pdf` and hash-pinned. Eight figures asked for, eight exact. Was the board's **last open land identity**; `LAND7` now refuses an open one | VERIFIED | `FOOTPRINT_VERIFICATION_LEDGER` §6.1/§6.2 |
| Mating access | **SIDE ENTRY: the cable exits EAST**, out of the right wall. Courtyard reaches `x = 76.725`, **0.275 mm** inboard of the D-709 step at `x = 77.000`; rightmost land **0.825 mm** off it. Mated envelope (p.1) **6.25 deep × 2.95 tall** | CAD-TO-VERIFY (the right-wall aperture must follow the step — §12) | board `1a06b058` |

### 10.3 RootProbe / FAST_IO — RETIRED on beta-v2
- **RootProbe connector: NOT PRESENT** on the beta-v2 board — the dedicated interface
  was retired (D-038); it survives only as a reserved *Phase-2* accessory spec, with no
  reference designator and no net on this board.
- **FAST_IO (GPIO43): WITHDRAWN** from the community port (D-106). GPIO43 is now an
  internal UART0-TXD debug net only, observable at **`TP35`**.
- **Do not claim a RootProbe port or a native fast-GPIO header on the community port.**
  ENGINEERING-ONLY history; MARKETING must not reference RootProbe as a beta-v2 feature.

---

## 11. Test & recovery interfaces

- **No SWD/JTAG/UART programming header exists** (confirmed by exhaustive search).
  Programming/flashing and ROM-download recovery are over **USB-C (`J3`)** via the
  native USB Serial/JTAG (GPIO19/20), assisted by the **BOOT** button (`SW1`). LOCKED.
- **UART0 boot-log** is observable at **`TP35`** (`UART0_TXD_TEST`, GPIO43) — the only
  view of a board whose USB will not enumerate. UART0 is TX-only (GPIO44/U0RXD is IR RX).
- **Test points:** `TP1`–`TP47` (bench probes; strap tests `TP1`/`TP2`/`TP3`; I²C
  `TP4`/`TP5`; NFC antenna `TP37`/`TP38`; IR `TP39`/`TP40`; accessory-bus READY `TP44`;
  rail probes on sheet 01). ENGINEERING-ONLY.
- **No dedicated RESET/EN button** (only `SW1` BOOT + `SW9` power). `SW9` provides a
  physical main-rail hard-off for a hung board.

---

## 12. Mechanical (authoritative dimensions only)

`mechanical/MECHANICAL_INTERFACE_SPEC.md` is the declared authoritative pre-CAD
dimension source and supersedes older Enclosure Field Slate v3/v4/v5 dimensions.

| Item | Value | Label | Evidence |
|---|---|---|---|
| PCB outline | **77.000 × 148.000 mm maximum** — stepped: 72.000 mm wide except an east bump to **x = 77.000** between `y = 70.500` and `y = 104.005` | REVISED D-709 under owner authority D-703 option 2 (`cc9f356`) · MARKETING-SAFE (board size) | `evidence/d709-verify-promotion.json` (outline extents measured 0,0→77,148); `FBV2_SIXLAYER_STACKUP.md`; mech spec |
| PCB thickness | **1.6 mm** | LOCKED | mech spec; stackup |
| PCB stackup | **6 copper layers** (F/In1 GND/In2 sig/In3 sig/In4 GND/B), JLC06161H-7628, 1 oz outer / 0.5 oz inner, no HDI/blind/buried | LOCKED · ENGINEERING-ONLY | `FBV2_SIXLAYER_STACKUP.md` |
| Mounting holes | **2 × M2**, Ø2.2 mm NPTH, Ø4.5 mm keep-out; **BOSS1 (41.000, 12.000), BOSS2 (60.000, 145.000)** — the POST-REBASE doc datum | LOCKED (D-226/D-232, whose figures are PRE-REBASE) · **RE-BASED AND MACHINE-CHECKED (D-759, `mechanical_keepout_contract` MK2)** | `evidence/d759-mechanical-datum.json`, `evidence/d759-boss-clearance.json` |
| Enclosure external | **85 × 160 × 23 mm** (portrait) | REVISED D-709 (width only; follows the PCB outline and owner approval D-707 `ac9d333`) · MARKETING-SAFE (with rounding to CAD) | mech spec; D-709 |
| Enclosure wall | 2.0 mm nominal | TARGET · CAD-TO-VERIFY | mech spec |
| Internal cavity | 80.0 × 155.0 × 18.5 mm nominal | REVISED D-709 (width only) · TARGET · CAD-TO-VERIFY | mech spec; D-709 |
| Board→cavity clearance | **≥1.5 mm — actual MINIMUM 1.500 mm X, 3.500 mm Y** | LOCKED (rule) · **CORRECTED at D-760** | measured on board `1a06b058`: outline X 0.000 … 72.000 with the D-709 step to 77.000 between Y 70.500 … 104.005, against an 80.000 × 155.000 mm cavity placed to the locked 1.500 mm west gap. **East gap 6.500 mm at the 72 mm sections and 1.500 mm AT THE STEP.** The row read *"actual 2.5 mm X"*, which is the pre-`FBV2-EXP-002` figure from the 70 mm board and was stale by two revisions — D-239 itself says the gap *"falls 2.5 → 1.5 mm on both sides, the ≥ 1.5 mm rule met EXACTLY, with nothing to spare"* |

**Mechanical CAD authority / remaining CAD-to-verify items:**
- ~~**BOSS2 X:** spec/floorplan say **59.000**; the metrics file says 60.000 (1 mm
  discrepancy) — use 59.000 (spec is declared authority), verify in CAD.~~
  **CLOSED at D-759, and the METRICS FILE had the right one.** The 1 mm is the
  **FBV2-EXP-002 re-base**: `FBV2_P1_KEEPOUTS.md`'s own header says the board grew
  symmetrically 70.000 → 72.000 mm and that *every* section-1 X coordinate gains
  **+1.000 mm**, so D-226/D-232's (59.000, 145.000) and (40.000, 12.000) are PRE-REBASE
  figures. **The board proves the datum**: `U6` fits only the re-based `IR_RX_OPTICAL`,
  `J3` only the re-based `USB_APERTURE`, `MK1` only the re-based `MIC_ACOUSTIC`. `BOSS2`
  at 60.000 is correct and its Ø4.500 keep-out sits wholly inside the re-based
  `IR_BARRIER` (57.500 … 62.500). **`BOSS1`'s hole was the one object that never took the
  re-base** and moved +1.000 mm to 41.000 at D-759. `evidence/d759-mechanical-datum.json`.
  *(D-758 read the section-1 figures as current and moved the keep-outs and `BOSS2` the
  wrong way; that is reverted.)*
- ~~**BOOT access face/position:** conflicting right-wall vs front-bottom placements.~~
  **CLOSED D-242 / re-verified D-764:** `SW1` is on `F.Cu` at doc **(28.300, 6.000)**
  (KiCad **(28.300, 142.000)**), in the measured gap between the microSD shell and USB-C.
  The enclosure provides a **Ø2 mm recessed tool hole in the FRONT wall**, not the right or
  bottom wall.
- ~~**Power-switch position:** two slightly different coordinates.~~ **CLOSED D-242 /
  re-verified D-764:** `SW9` remains on the **RIGHT wall** at doc **(66.700, 61.500)**
  (KiCad **(66.700, 86.500)**), `F.Cu`, 90°.
- ~~**Community-port wall aperture not restated for the current 1×24 socket.**~~
  **PCB-side geometry CLOSED / enclosure execution CAD-TO-VERIFY (D-745/D-764):** current
  `J5` is `SSQ-124-02-G-S-RA`, 1×24 at 2.54 mm, with **58.420 mm pin span** and
  **61.47 mm body length**.  The body occupies board Y **8.475 … 69.945 mm** and the
  mating face is **x = 72.430 mm**.  With the current east cavity face at **x = 78.500 mm**
  there is **6.070 mm of air**, so the east wall MUST step inward over the full J5 span
  and carry the **62.5 mm closed-end recess**.  The historical **34 × 10 mm** aperture was
  for the superseded 2×12 BCS body and is **NOT CURRENT AUTHORITY**.
- Corner radii/chamfers, surface finish, texture, branding = **M-05**, not dimensioned.
- **D-709 EAST STEP (CAD-TO-VERIFY):** the 5.00 mm east bump runs `y 70.500 .. 104.005`
  only.  It is BELOW the `WROOM` antenna keep-out (starts `y = 104.005`) and BELOW `J5`'s
  mating volume (courtyard ends `y = 70.490`), so neither is touched.  **`J8` (Qwiic /
  STEMMA QT, §10.2 EXTERNAL right wall) moved +5.000 mm east with the edge and its
  relationship to that edge is unchanged** — courtyard 0.275 mm inboard, rightmost pad
  0.825 mm from the edge, before and after.  The right-wall aperture must follow the
  step, not the old flat wall.

---

## 13. Enclosure-visible controls & openings (CAD-TO-VERIFY where noted)

- **FRONT:** 3.5″ display + capacitive touch window; **D-pad (4)** + **A/B (2)**
  buttons; **RGB status light** aperture (diffuser/light-pipe, no bare LED; exact
  position not locked — M-11); **microphone** acoustic opening (Ø0.8–1.0 mm or 3–5×
  Ø0.5 mm, mesh behind); **recessed Ø2 mm BOOT/recovery tool hole** at the D-242
  front-wall location for `SW1`.
- **TOP edge:** **915 MHz SMA bulkhead** (Ø6.5 mm hole, left half); **IR TX window**
  and **IR RX window** with a **mandatory opaque IR barrier** between them (emitter↔
  receiver ≥15 mm).
- **RIGHT wall:** **community expansion port** **62.5 mm closed-end recess** following the
  stepped board profile over the full `J5` body span (labelled "COMMUNITY PORT — 3V3 LOGIC
  ONLY / 5V PIN IS POWER OUTPUT ONLY"); **power slide switch** at `SW9`; **Qwiic / STEMMA
  QT** connector. **BOOT is NOT on this wall; it is a front-wall tool hole (D-242/D-764).**
- **BOTTOM edge:** **USB-C** opening (centred ±5 mm); **microSD** opening (reserve
  +18 mm insertion travel).
- **REAR:** **speaker grille** (≥25 % open, Ø0.8–1.0 mm holes, mesh); **NFC tap target**
  (no opening — reads through plastic; Ø48 mm clear zone, Ø58 mm metal exclusion, centre
  (30.800, 124.500)); **branding**.
- **Internal antennas (no external window):** 433 MHz flex (left/lower internal wall),
  Wi-Fi/BLE module antenna (keep-out only). The 915 MHz whip is an external screw-on
  accessory (198 mm × Ø13 mm) carried separately (internal storage channel deleted, D-219).

---

## 14. DNP / tuning / alternate-stuffing / fallback provisions (recoverability, D-049)

- **DNP (with recorded reasons):** `R112` (display SDO isolation), `R123` (IR trim),
  `C81`/`C82` (speaker EMI), `R68` (SW9 0 Ω bypass — must stay DNP), `R93` (recovery),
  NFC 5 V PA boost branch (`C34`/`C35` path, `R107`), `R119` (IMU 0x69 alt).
- **0 Ω source-selection links:** `R118`/`R119` (IMU address select), `R106`/`R107`
  (NFC supply select), `R109` (MCU strap link).
- **TUNE / FIRST-ARTICLE TUNE:** the NFC matching network (`C69`–`C80`, `L5`/`L6`,
  `R114`–`R117`) — values pending VNA/ST tool. **D-615: all 16 TUNE positions now
  carry a FIRST-ARTICLE part number so the first article can actually be bought and
  built; every one is expected to change after the VNA measurement, and each carries
  that sentence in its own `Note_Sourcing`.** The `R114`–`R117` dissipation is
  explicitly NOT established — the ST25R3916 tank current is not a number this
  repository holds — so those two lines took the highest-rated part their 0603 land
  offers and the dissipation is a first-article measurement.
- **Corrected DNP→FIT (from inherited Beta-DM):** NFC front end (`U9` + decoupling +
  `Y1` + `J7` + matching, D-035/D-055), audio out (`U5`, `J6`, D-144).

---

## 15. Firmware-visible capabilities tied to hardware (MARKETING-SAFE at capability level)

Wi-Fi + BLE; 433 MHz + 915 MHz LoRa sub-GHz TX/RX; 13.56 MHz NFC read/write; IR
transmit + receive; capacitive touch UI on a 3.5″ 320×480 display; audio playback
(speaker) + microphone capture (I²S); 6-axis motion (BMI270); microSD file storage;
USB-C data/console; battery fuel-gauge telemetry (MAX17048); a 24-line community
expansion port (I²C + 2 native GPIO + 10 expander GPIO + switched 3V3/5V) and a
Qwiic/STEMMA QT I²C accessory port; RGB status indicator.

---

## 16. Known UNRESOLVED items (verify or omit before any public claim)

1. ~~**Battery fitted capacity (mAh)** — envelope 2500–3000 mAh only; SKU deferred (M-04).~~ **CLOSED at CTO-BAT-01:** first-five pack is Adafruit Product 328, 2500 mAh, protected, genuine JST-PH; exact supplier-linked battery specification and electrical/load-margin contract are pinned in `assembly/SELECTED_BATTERY.json`.
2. ~~**Charge current (ICHG)** — programmed value not fixed.~~  **CLOSED at D-743:** 769 mA from `R37` 390 Ω, input limit 1100 mA and `VBATREG` 4.2 V from `R36` 13 kΩ.  The old 1 kΩ / 18 kΩ pair programmed 300 mA against a 360 min safety timer and could not complete a charge.
3. **microSD max card capacity** — not stated.
4. **Touch controller silicon** — FT6236 vs CST026 (interface locked; PO must specify).
5. **Display driver symbol metadata** — stale ILI9341/CH280QV10 text vs locked ILI9488.
6. **915 antenna doc residue** — stale FXP890 vs locked external TI.92.2113 SMA.
7. **Mechanical:** ~~BOSS2 X (59 vs 60),~~ **CLOSED at D-759 — it was the FBV2-EXP-002
   +1.000 mm re-base, the board is on the re-based datum, and `BOSS2` at 60.000 is right**;
   BOOT face, power-switch position, 1×24 wall aperture, corner radii — CAD-TO-VERIFY.
8. ~~**`J8` Qwiic LCSC** absent (the **MPN is now in the schematic**, D-614); **`J1`** display FPC LCSC absent.~~
   **CLOSED at D-615** — both confirmed against a live distributor record (D-096):
   `J8` = JST `SM04B-SRSS-TB(LF)(SN)`, LCSC **`C160404`**, 69 510 in stock;
   `J1` = Hirose `FH69-50S-0.5SH`, LCSC **`C25955556`**, 790 in stock.
9. **First-build purchasing, not design:** nine BOM lines sit under 10x the
   first-five need on the assembler's own catalogue and five of them read ZERO
   (`J5`, `L4`, `MK1`, `U19`, `U9`; then `Q2`/`Q3` 0, `U2`/`U3` 1, `U18` 3, `D8` 7).
   Most are already CONSIGNED classes under D-206, so this is a brief to work
   rather than a design defect — `hardware/demo/manufacturing/evidence/d615-purchasing-short.csv`.

---

## 17. Evidence index (authoritative sources for audit)

- Schematic (9 sheets): `hardware/beta-v2/kicad/aqroot-beta-v2/01_power_tree.kicad_sch`
  … `09_community_header.kicad_sch`; PCB `aqroot-Beta-v2.kicad_pcb`.
- BOM / assembly: `assembly/OFF_BOARD_BOM.md`, `FIRST_FIVE_POPULATION_MATRIX.md`,
  `SOURCING_LEDGER.md`, `FOOTPRINT_VERIFICATION_LEDGER.md`, `IR_LEAD_FORMING.md`.
- Architecture: `architecture/ARCHITECTURE.md`, `I2C_ADDRESS_REGISTRY.md`,
  `GPIO_LEDGER.md`, `POWER_FAULT_STATE_TABLE.md`, `FBV2_SIXLAYER_STACKUP.md`,
  `EXPANSION_ECOSYSTEM_PROPOSAL.md`.
- Mechanical: `mechanical/MECHANICAL_INTERFACE_SPEC.md`, `P1_FLOORPLAN_INPUTS.md`;
  `pcb/FBV2_P1_FLOORPLAN.md`, `FBV2_P1_METRICS.txt`.
- Rulings & reviews: `CTO_DECISIONS.md`, `reviews/2026-08-22-independent-cto-power-nfc-review.md`,
  and the accepted `audits/`.
- Governing routing state: `CURRENT_STATE.md` (§3 blocker), latest audit
  `audits/2026-08-30-p2-004a-d301-…-u11-trunk-wall.md`.
