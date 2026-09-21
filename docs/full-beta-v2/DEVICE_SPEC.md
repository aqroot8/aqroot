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
| Panel (off-board) | EastRising **ER-TFT035IPS-6**, 3.5″ IPS TFT, **ILI9488** controller.  **SUPPLY LIMIT, D-788: `VCI` and `IOVCC` are −0.3 … +3.3 V ABSOLUTE MAXIMUM and 2.5 … 3.3 V / 1.65 … 3.3 V operating (ILI9488 Table 41 and §17.2, archived `vendor/ILITEK/`).  3.3 V is the ceiling on the whole `+3V3` rail and `demo_feature_contract` F6 enforces it.** | LOCKED · FITTED · INTERNAL (off-board module) · MARKETING-SAFE (3.5″ display) | `assembly/OFF_BOARD_BOM.md`; ARCHITECTURE.md; CTO_DECISIONS D-788 |
| Resolution | **320 × 480** | LOCKED · MARKETING-SAFE | OFF_BOARD_BOM.md; ARCHITECTURE.md |
| Display driver | **ILI9488** (COG) | LOCKED (per ARCH/BOM & D-074…D-078) | ARCHITECTURE.md; OFF_BOARD_BOM.md — see conflict note |
| Interface | 4-wire **SPI** (SPI-A bus) | LOCKED | `03_spi_a_display_sd.kicad_sch` |
| On-board FPC connector | `J1` **Hirose FH69-50S-0.5SH** (50-pin, 0.5 mm) | FITTED · **MACHINE-PLACED** (D-206/D-207; placement preview still mandatory) | `03_spi_a_display_sd.kicad_sch:J1`; current assembly plan |
| Tail **pin-1 end** | **RIGHT-hand end viewed from the display face, tail down** — and `J1` pin 1 is the right-hand end of its row (`x = 44.910`, `F.Cu`). **Pin 1 meets pin 1; no mirror** | **RESOLVED at D-754** from the vendor outline drawing | `evidence/d754-display-tail-orientation.json` |
| Touch panel | EastRising **ER-TPC035-6** capacitive | LOCKED · FITTED · INTERNAL | OFF_BOARD_BOM.md |
| Touch controller | **FocalTech FT6236** @ I²C **0x38** | LOCKED (interface); **silicon identity CAD-TO-VERIFY** | `architecture/I2C_ADDRESS_REGISTRY.md`; ARCHITECTURE.md |
| Backlight driver | `U17` **TPS61169DCKR** (WLED boost) | FITTED | `03_spi_a_display_sd.kicad_sch:U17` |
| Backlight **true-off disconnect** | `Q11` **Vishay SQ2364EES-T1_BE3** (LCSC C5758702, **60 V**) in the panel cathode return, gate on its OWN net `BL_DISC_G` | FITTED (added D-750, re-controlled D-752, **re-rated D-780**) | `03_spi_a_display_sd.kicad_sch:Q11`; D-750; D-752; D-780 |
| Backlight disconnect **gate hold** | `D14` **1N4148WS** (LCSC C2128) + `C85` **1 µF** + `R132` 220 k — nominal RC 220 ms; release proof uses **147 ms** worst retained τ including tolerance/DC-bias allowance | FITTED (D-752, C85 resized D-779) | `03_spi_a_display_sd.kicad_sch:D14/R132/C85`; D-752; D-779; D-780 |
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
> **D-752 STRUCTURAL REPAIR, UPDATED THROUGH D-784.** `Q11`'s gate is on its own
> `/03_SPI_A_DISPLAY_SD/BL_DISC_G` net. `D14` charges **C85 = 1 µF** from
> `DISP_BL_CTL`; `R132 = 220 kΩ` discharges it. D-779 enlarged C85 tenfold, so
> the old D-752 `100 nF` / `τ = 22 ms` figures are historical and MUST NOT be
> used. The current nominal RC is **220 ms**; the release proof uses a **147 ms
> worst retained τ** after tolerance/DC-bias allowance. D-780 then replaced the
> AO3422 with Vishay `SQ2364EES-T1_BE3`, whose guaranteed `RDS(on)` point at
> `VGS = 1.5 V` closes the conduction proof without threshold/transconductance
> extrapolation. D-784 **primes `DISP_BL_CTL` at 100% for a microsecond-timed 3.0 ms
> before low-duty PWM** (the acceptance minimum remains 2 ms), so the 1 µF hold
> capacitor is charged before dimming without relying on scheduler-tick timing.
> `F5` gates the exact fitted Q11/C85/R132/D14 identities and timing; first-five
> `Q11-TEMP-01` still measures startup, PWM, reset and true-off at 0/25/40 °C.
> The safety invariant remains: the cathode disconnect must stay enhanced until
> TPS61169 has ceased switching; firmware brightness control is not allowed to
> momentarily create an open-LED fault.
>
> **AND THE SILICON ITSELF WAS STILL UNDER-RATED, UNTIL D-766.**  Everything
> above is about SEQUENCING, and the sentence *"the `AO3400A` is a 30 V part"*
> sat in this document, in `CTO_DECISIONS.md` and in the schematic note for four
> decisions **with a 30 V part still fitted**.  This board's own `.kicad_dru`
> publishes the ceiling for that node in its own words — *"an open-LED fault
> puts up to **39 V** on `LED_BOOST`"* — so `Q11` was rated **30 % below a limit
> this repository prints for its own drain node**.  The sequencing argument is
> sound, but a single-component failure re-creates the forbidden state: an
> unfitted `C85`, an open `D14` or a shorted `R132` each put the gate back on
> `CTRL`'s instantaneous level.  **A protection element must survive the fault
> it exists to prevent.**
>
> **D-780 SUPERSEDES THE AO3422 CONDUCTION ARGUMENT.**  D-779 corrected the
> extracted-datasheet unit error (`VGS(th)` is specified at **250 µA**, not
> 250 mA) but still had to bridge an unpublished AO3422 conduction band with
> typical transconductance.  That is not a production guarantee.  `Q11` is now
> **Vishay `SQ2364EES-T1_BE3`**, same SOT-23 and same 1=G / 2=S / 3=D pinout,
> with **60 V `VDS`** against the board's 39 V fault ceiling and a published
> **`RDS(on)` MAX 0.245 Ω at `VGS = 1.5 V`, `ID = 2 A`**.
>
> **D-789 / D788-11 + `R8-N06` RE-DERIVES THE HELD GATE AND CHANGES `D14`.**  This
> paragraph carried **`VGS = 2.396 V`, 0.896 V above** the conduction point and an
> **≈62 ms** envelope.  **Both were 3.3 V-rail numbers** and D-788 moved the rail down
> to keep the ILI9488 panel inside its own absolute maximum — the hand-carried-constant
> failure Round-8 raised as D788-11.  The held gate is **DERIVED** now, by
> `demo_feature_contract` F5, as `VOH(MIN) − VF(D14)` evaluated at the rail's own
> heavy-load minimum: Espressif's ratiometric `0.8 × VDD` gives **2.455526 V**, less the
> diode's LOWEST published forward maximum plus a declared 2 mV/K allowance to the 0 °C
> prototype endpoint.
>
> **At the D-788 rail the `1N4148WS` no longer qualifies.**  Its lowest published forward
> maximum is **715 mV at `IF` = 1 mA**, which lands `VGS` at **1.486526 V — 13.5 mV BELOW**
> the 0.245 Ω row above, and there is no lower-current row to bound it with.  **`D14` is
> therefore a Diodes Incorporated `BAT54WS-7-F`**: `VFM` ≤ **240 mV at `IF` = 0.1 mA**,
> which is *below* the ~9 µA this node actually draws and rises monotonically with `IF`,
> so it is a **guaranteed bound and not an extrapolation**.
>
> **AQROOT therefore holds `VGS = 1.961526 V`, 461.5 mV above** the characterized low-gate
> point.  With `C85 = 1 µF` the worst retained envelope stays inside the published
> conduction region for **20.74 ms** and the gate cannot open at all before **59.37 ms**,
> against the TPS61169's **2.5 ms max** shutdown — an ordering margin of **23.7×**.
> `BAT54WS-7-F` is the **same MPN, LCSC code and SOD-323 land this board already fits at
> `D10`/`D11`/`D12`**, so no new part, feeder, footprint or copper is added.
>
> **AND THE SCHOTTKY IMPROVES TRUE-OFF RATHER THAN THREATENING IT.**  D-752 rejected a
> Schottky on the grounds that its reverse leakage would hold the gate up.  **That
> argument's sign is wrong:** pin 1 of the symbol is `K` and the board wires it to
> `BL_DISC_G`, so the **cathode is on the gate**; in the true-off state `CTRL` is driven
> low, `D14` is reverse-biased and its leakage flows **out of** the gate.  The only
> current that can hold the gate up is `Q11`'s own `IGSS` ≤ 100 nA, which across `R132`
> is **22.2 mV** against a `VGS(th)` **minimum** of 0.46 V — **20.7×**.
>
> F5 directly gates every one of these facts, computes the Schottky's reverse leakage as
> a constant-current term beside `R132`'s exponential, and carries four negative controls
> — including one that puts the D-779 AO3422 back and one that **refuses a silicon diode
> in the charge path at this rail**.
>
> The 1.5 V `RDS(on)` row is specified at **25 °C unless otherwise noted**.
> For the first five prototypes AQROOT therefore makes no unsupported all-temp
> low-gate claim: assembly acceptance `Q11-TEMP-01` requires backlight operation
> and true-off validation at **0 °C, 25 °C and 40 °C**.  `Q11` is a reworkable
> SOT-23 and failure blocks the affected prototype from Demo use.  This is a
> first-article qualification residual, not a hidden production guarantee.
>
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
- **915 antenna:** ~~the `U8` schematic package note and a stale ARCHITECTURE row name an
  internal `Taoglas FXP890.07.0100C` flex.~~ **CORRECTED at D-769 — both now name the locked
  selection.** The locked selection (CTO D-198) is the **EXTERNAL SMA `Taoglas TI.92.2113`**
  dipole on a top-panel bulkhead, reached through the module IPEX, a `CBA-UFLSMA20IP` pigtail
  and the top-panel SMA(F) bulkhead. `F7` refuses the retired name returning.
- **NFC antenna variant:** the authoritative part is the **`.B.dg` (reverse-ferrite)**
  variant (D-131); any `.A.dg` reference is superseded.

---

## 6. Power, battery, charging & protection

### 6.1 Battery & charging
| Item | Value | Label | Evidence |
|---|---|---|---|
| Cell | 1S Li-ion / LiPo pouch | LOCKED (chemistry) · INTERNAL | `01_power_tree.kicad_sch`; OFF_BOARD_BOM.md |
| Battery connection | `J4` **manual 26-AWG pigtail land** → Molex Micro-Lock Plus 2.0 (`5055700201` board-side housing); **no PCB header fitted** | FITTED MANUAL · INTERNAL | `01_power_tree.kicad_sch:J4`; `assembly/BATTERY_HARNESS.json` |
| Envelope | ≈ **2500–3000 mAh** target; cell envelope 57 × 75 × 8.0 mm MAX (D-243) | TARGET · CAD-TO-VERIFY | CTO_DECISIONS D-071/D-243; OFF_BOARD_BOM.md |
| **Exact fitted capacity** | **2500 mAh — Adafruit Product 328 selected for the first five (CTO-BAT-01).** Current supplier page specifies a protected pack with genuine JST-PH; its linked `785060` pack specification is pinned in-repo at SHA-256 `826149da…ecd3`, max pack 7.9 × 50.5 × 60.5 mm and max charge 1C. The primary pack specification §8.3.2 states discharge current **≤2C5A**; its own nominal-capacity row defines the C5 capacity as **2500 mAh**, so the derived limit is **2 × 2.5 Ah = 5.0 A**. That 5.0 A is a C-rate derivation, not a literal table row labelled “5 A max discharge.” The supplier's conservative charge recommendation is 1.2 A, above this board's 0.855 A worst programmed envelope. Incoming polarity must be meter-verified before D-781 retermination/mating. | **SELECTED · ENGINEERING-ONLY** | `assembly/SELECTED_BATTERY.json`; `checks/battery_pack_contract.py` |
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
| Current-sense resistor | `R75` **10 mΩ 1 % 3 W** (Kelvin pair to U18.8/U18.9) — Bourns **`CRA2512-FZ-R010ELF`**, LCSC `C840621`, a **CURRENT-SENSE class part at ±50 ppm/°C, 3 W** (a thick film at ±1500 ppm/°C would move the trip ~19 % over −40…+85 °C).  **D-771 MOVED IT FROM 15 mΩ** (`CRA2512-FZ-R015ELF`, `C2073490`, D-615): ADI guarantees the LTC4368 forward threshold only as **40 / 50 / 60 mV** over temperature, so 15 mΩ put the LATCHING breaker at **2.640–4.040 A**, overlapping the charger's own recoverable `IBAT_OCP` band of 2.5625–3.6875 A.  At 10 mΩ the breaker is **3.960–6.061 A**, entirely above it.  Same series, same 2512 land, same 3 W — only the resistance | FITTED | `01_power_tree.kicad_sch:R75`; CTO_DECISIONS D-771 |
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
| **ACC_3V3_SW** load switch | `U20` | TPS22950CQDDCRQ1 (TPS22950-Q1, D-765) | FITTED | `01_power_tree.kicad_sch:U20` |
| **ACC_5V_SW** load switch | `U22` | TPS22950CQDDCRQ1 (TPS22950-Q1, D-765) | FITTED | `01_power_tree.kicad_sch:U22` |
| Accessory I²C hot-swap buffer | `U16` | TCA4307DGKR | FITTED | `08/09` |

### 6.3a Accessory-power ENVELOPE (D-753, silicon corrected D-765, **budget guaranteed and protection chain ordered at D-771**) — ENGINEERING-ONLY, **bounded by hardware**

> ## THE PUBLISHED ACCESSORY BUDGET — D-098, and the number the hardware now GUARANTEES
>
> **`ACC_3V3_SW` = 400 mA TOTAL.  `ACC_5V_SW` = 300 mA TOTAL** for the first five
> boards.  **THE TWO DUPLICATE CONTACTS ON EACH RAIL SHARE THE RAIL LIMIT — they
> do not double it**: `ACC_5V_SW` on `J5` pin 1 + pin 24 = 300 mA combined, **not**
> 300 mA each, and `ACC_3V3_SW` on pin 3 + pin 22 = 400 mA combined.  There is one
> load switch and one current limit per rail.  Later validation targets, **only
> after measured bring-up and a CTO ruling**: 600–800 mA and 500 mA respectively.
> **This wording is D-098's own and is MANDATORY in accessory-facing
> documentation.**
>
> ## **D-789 IS THE CURRENT FIRST-FIVE ACCESSORY CONTRACT.  D-788's HIGH-SIDE CORRECTION STANDS; ITS DELIVERED NUMBERS DO NOT.**
>
> *Everything in this block from here to the `D-787 SUPERSEDES D-775` heading is
> CURRENT.  Everything after that heading is HISTORICAL: every D-787 and D-775
> figure below it — the 3.135 V connector minimum, the 3.146366 V delivered
> figure, the 28-AWG TP12→J5 reinforcement, the 68 mΩ RON and the 3.8094 V dual
> requirement — is superseded by the block above and by D-789's re-derivation,
> and is retained only to record what changed and why.*
>
> **THE FITTED DISPLAY'S ABSOLUTE MAXIMUM IS 3.3 V AND D-787's RAIL WAS ABOVE IT.**
> The `ER-TFT035IPS-6` is an ILI9488 panel.  ILI Technology's own datasheet
> (archived `vendor/ILITEK/ilitek-ili9488-v100.pdf`, sha256
> `aeb2317…1df38b`, corroborated against a second independent mirror) gives, in
> Table 41, an **ABSOLUTE MAXIMUM of −0.3 … +3.3 V** for BOTH `VCI` and
> `IOVCC`, and in section 17.2 a DC operating range of `VCI` **2.5 / 2.8 /
> 3.3 V** and `IOVCC` **1.65 / 1.8 / 3.3 V** with **`VIH` max = `IOVCC`**.
> D-787's derived power-save corner was **3.542487 V** — 242 mV over an
> absolute maximum — and its **nominal 3.308989 V was 9 mV over it**.
>
> **D-788 brings the rail inside that limit with no new component.**  `U12`'s
> `PS/SYNC` moves from `GND` to the `EN` net, so the TPS63020 runs **forced
> fixed-frequency PWM** and TI's `VFB_PS` **+5 %** power-save excursion cannot
> occur; and `R40` moves **178 kΩ → 189 kΩ** (YAGEO `RT0603BRD07189KL`,
> `C861174`, 0.1 % / 25 ppm).  `R39` is unchanged at **1.000 MΩ** Viking
> `ARG03BTC1004`.  The rail is now **3.100334 / 3.145503 / 3.191022 V** raw
> PWM, **3.069408 V** heavy-load minimum and **3.223012 V** worst case —
> **76.99 mV inside the panel's absolute maximum** and **58.78 mV over the
> ESP32-S3-WROOM-1's own 3.0 V `VDD33` minimum** after the `+3V3` plane's
> bounded distribution drop.  Display `VCI`/`IOVCC` and the MCU supply are **the
> same net**, so no display input is ever driven above its own supply.
>
> **THE SETPOINT IS CENTRED, AND THAT IS MACHINE-CHECKED (R7-N02).**  The window
> between the MCU's 3.0 V floor and the panel's 3.3 V absolute maximum is 300 mV
> and the rail's own tolerance band needs about 154 mV of it, so the setpoint
> decides how the rest is split.  `demo_feature_contract` F6 enumerates every
> purchasable E192 0.1 % value for `R40` with `R39` at 1 MΩ and requires the
> fitted one to **maximise the smaller of the two headrooms**.  `189 kΩ` gives
> **76.99 / 58.78 mV**; the first D-788 draft's `187 kΩ` gave **47.97 / 86.36 mV**
> and `191 kΩ` gives **105.40 / 31.77 mV** — both refused, because 3.3 V is a
> **damage** limit and 3.0 V is a **recoverable** one, so the larger share
> belongs under the damage limit.  Computed output ripple (**1.68 mV** peak-to-peak,
> from `SLVS916I`'s minimum oscillator frequency, `L1`'s minimum inductance and
> the declared effective local output capacitance) is charged to BOTH ends.
> **Load-transient overshoot is deliberately NOT given an analytic bound** — TI
> publishes it only as plots — and is measured at first article as
> `C-PWR-TRANSIENT-01`.
>
> ### **OWNER-APPROVED D-788 OPTION A — Community Port voltage/current contract, FROZEN AT D-789**

> A rail whose maximum must stay under 3.3 V must sit nominally below 3.3 V, and
> the Community Port is switched from that rail.  **The former 3.135 V
> (3.3 V −5 %) connector minimum is unreachable at ANY current, including
> zero**: the rail's own heavy-load minimum is 3.069408 V before a single
> milliohm of delivery loss.
>
> **D-789 RE-DERIVES THE DELIVERED NUMBERS AND SUPERSEDES D-788's 2.95 V.**
> Round-8 reproduced two defects in the D-788 delivery model and both are real.
> `U20`'s `RON` was **interpolated** between two datasheet rows and called a
> bound, when nothing guarantees the curve's shape (D788-01); and the return
> network was priced with **four parallel ground contacts carrying only the
> 3.3 V rail's current**, when the published usage permits a single jumper and
> the 5 V rail's current comes back through the same contacts (D788-02).  Both
> are corrected: `RON` is now the guaranteed maximum at the nearest published
> row **at or below `U20`'s own input voltage** — the 1.8 V row's **116 mΩ**,
> which needs only that `RON` falls as `VIN` rises — and the delivery is solved
> over **every permitted wiring × load mode**.  The manual reinforcement lead
> that D-788 fitted to `J5.3` is also **retired** (D788-07/08/09/16); see
> DELIVERY below.
>
> **The guarantee is the worst permitted mode.**  Either duplicated 3.3 V
> contact used **alone**, **one** mated ground contact, and the 5 V rail also
> drawing its published 300 mA through that same ground:
>
> | condition, at the J5 mating interface | guaranteed voltage |
> |---|---|
> | no load | **3.069408 V** |
> | 400 mA, worst permitted wiring, 5 V rail also at 300 mA | **2.849642 V** |
> | 400 mA, worst permitted wiring, 3.3 V rail alone | **2.860909 V** |
> | 400 mA, **header fully mated** (both 3.3 V contacts, all four grounds), 5 V rail also at 300 mA | **2.982890 V** |
>
> **PUBLISHED MINIMUM: 2.84 V** — the worst mode, rounded DOWN onto a 10 mV
> grid.  It is **DERIVED**, not asserted: `demo_feature_contract` F6 computes it
> from the live board on every run and refuses a document that prints a
> different figure.  The **fully mated** number is published beside it as an
> explicit connection contract, and it is *better* than the 2.95 V D-788
> published with a hand-soldered conductor fitted.
>
> The unloaded rail spans **3.069408 V** to **3.223012 V**; raw PWM is
> **3.100334 / 3.145503 / 3.191022 V**.
>
> **WHAT THE PORT'S OWN SILICON NEEDS.**  The tightest published minimum supply
> voltage among the parts the BOARD powers from `ACC_3V3_SW` is `U16`
> `TCA4307DGKR` at **2.3 V** (TI `ZHCSLQ0` section 6.3, archived
> `vendor/TI/ti-tca4307-zhcslq0-DGK0008A.pdf`).  The worst delivered mode clears
> it by **549.6 mV**.
>
> **`ACC_3V3_SW` = 400 mA TOTAL and `ACC_5V_SW` = 300 mA TOTAL are UNCHANGED.**
> The owner approved **D-788 OPTION A** on 2026-09-20: the switched accessory
> rail is published as an approximately **3.15 V-class rail** using the derived
> envelope, and the exact figures were delegated to the final candidate — which
> is this one.  No promised current capability is removed. Every Qwiic/STEMMA QT
> device AQROOT has qualified operates at or below 2.7 V. A dedicated accessory
> buck-boost is deferred to **REV-B**.
>
> **MEASUREMENT PLANE.**  The guaranteed voltage is the potential between the
> `ACC_3V3_SW` contact and the `GND` contacts **at the J5 mating interface**.
> The accessory's own plug, cable and connector are outside the guarantee.
>
> **DELIVERY — THERE IS NO MANUAL CONDUCTOR ON THIS BOARD.**  Both contacts are
> delivered by routed copper alone: `J5.22` at **79.0 mΩ** measured, `J5.3` at
> **224.4 mΩ**.  D-787 added two hand-soldered 28-AWG leads, D-788 reduced that
> to one, and **D-789 removes it**: Round-8 raised four independent findings
> against the remaining lead — a tinned tip that cannot fit a 1.00 mm pad, an
> insertion into a through-hole already filled by J5's 0.635 mm square tail, a
> route starting inside `BATTERY_SHADOW` and crossing `RIB_R3`, and an
> acceptance that cannot be measured because the board's own copper stays in
> parallel with it.  It bought **70 mV** on one of two duplicated contacts.
> `TP12`/`TP25` remain as test points and **nothing is soldered to them**.  Each
> duplicated contact is qualified **alone**.
>
> ---
>
> **D-787 SUPERSEDES D-775 FOR THE CURRENT FIRST-FIVE ACCESSORY CONTRACT.**  *(**HISTORICAL**
> from here to the end of this block — every D-787 number below is superseded by the
> D-788/D-789 block above.  In particular: the **3.135 V** connector minimum is
> **unreachable at any current** and is retired; the **3.146366 V** delivered figure is
> retired; the **28-AWG TP12→J5 reinforcement leads are RETIRED** and no manual conductor
> is fitted on this board; and U20's **68 mΩ** RON is retired for a guaranteed **116 mΩ**
> at the nearest published row at or below its own input voltage.)*
> The rail budgets themselves do **not** change: `ACC_3V3_SW` remains **400 mA
> total** across J5 pins 3+22 and `ACC_5V_SW` remains **300 mA total** across
> J5 pins 1+24. What changed is the proof that the board can actually deliver
> the voltage/current contract at component corners. F6 no longer assumes +3V3
> is an ideal 3.3 V source; it derives the TPS63020 output from the fitted
> divider, value tolerance, selected-part TCR, TI's 495/500/505 mV PWM feedback
> band, line/load regulation and the +5% power-save high side.
>
> The current fitted divider is `R39` **1.000 MOhm +/-0.1%, +/-25 ppm/degC**
> (Viking Tech `ARG03BTC1004`, LCSC `C335092`) and `R40` **178 kOhm +/-0.1%,
> +/-25 ppm/degC** (Viking Tech `ARG03BTC1783`, LCSC `C2441185`). The derived
> PWM raw band is **3.261337 / 3.308989 / 3.357013 V**; the conservative
> heavy-load minimum is **3.228806 V** and the power-save high bound is
> **3.542487 V**, below the tightest 3.6 V internal-consumer ceiling.
>
> **176 kOhm was the first D-787 candidate and was rejected on AVAILABILITY,
> not electricals.** Every 176 kOhm 0603 part at 0.1% or better in the JLCPCB
> catalogue reads stock 0, including the KOA `RN73H1JTTD1763B10` that draft
> named, so it fails this project's own sourcing stock floor. 178 kOhm is the
> nearest stocked 0.1% value inside the window, and the window is narrow in
> both directions: 180 kOhm falls below the connector minimum and 174 kOhm
> exceeds the internal-consumer maximum. Both divider identities are therefore
> locked by `F7` and their temperature coefficients are keyed to the purchased
> MPN in `F6`.
>
> To remove the old long `ACC_3V3_SW` trace drop from the guaranteed first-five
> delivery path without bypassing protection, each duplicate 3.3 V Community
> Port contact receives an independent manual **28-AWG** reinforcement from
> **TP12.1 (downstream of U20)** to **J5.3** and **J5.22**. Each finished lead
> must measure **<=30 mOhm**. U20 remains in series, so its current limiter and
> OFF isolation remain authoritative. With the bounded U20->TP12 copper, U20's
> 68 mOhm maximum RON, hot-copper allowance and the <=30 mOhm lead, F6 proves
> **3.146366 V minimum at the Community Port at 400 mA**, above the **3.135 V**
> -5% minimum.
>
> `R97` remains **1.78 kOhm** and guarantees **0.4279 A** on ACC_3V3. `R101`
> is now **2.43 kOhm** (`0603WAF2431T5E`) and guarantees **0.3065 A** on
> ACC_5V while reducing its worst limiter corner to **0.6078 A**, so a
> user-reachable 5 V limiter state remains below BQ25185 IBAT_OCP minimum even
> at the corrected +3V3 high corner.
>
> `MAX17048 VCELL` remains a **loaded BAT_PROTECTED_P measurement**, not an
> open-circuit SOC threshold. Each rail alone retains the **3.50 V** policy
> floor. The corrected simultaneous full-budget requirement is **3.8094 V**,
> rounded upward to **3.85 V** on the 0.05 V firmware grid. Firmware checks
> before enable, rechecks after the load step, sheds the **5 V rail first** if
> loaded VCELL falls below 3.85 V, and fails closed on unqualified/unreadable
> gauge state. Accessory-facing documentation must say: *"400 mA on 3.3 V and
> 300 mA on 5 V are the rail limits. Using both at once requires the loaded
> protected-battery node to remain >=3.85 V after the second rail turns on;
> otherwise the 5 V accessory rail is shed while 3.3 V remains available."*
> This is deterministic load management, not a promise that every battery
> state can sustain both maxima.
>
> **D-781 SUPERSEDES D-777'S CONNECTOR RESTRICTION.**  D-777 correctly found
> that the fitted JST-PH board header was only a 2 A path, but its firmware
> workaround disabled sub-GHz TX, NFC field and IR whenever both accessory rails
> were enabled.  D-781 rejects that engineering workaround.  It keeps the
> existing J4 PTH pair as a manual 26-AWG pigtail land and moves the detachable
> interface to Molex Micro-Lock Plus 2.0.  With 26-AWG conductors on both sides,
> the frozen harness controlling rating is **2.6 A**, above the live full-feature
> modeled battery current (**2.2701 A** path-bound at the 3.85 V floor).  **The D-777 internal-feature reservation is
> retired:** sub-GHz, NFC and IR remain available with both accessory rails,
> subject only to the existing internal-TX mutual-exclusion rules. D-787 now
> enforces a **3.85 V** simultaneous 3.3 V + 5 V loaded-VCELL floor from the
> corrected power envelope; connector rating remains independently satisfied.
> Exact parts, polarity and first-article acceptance are frozen in
> `assembly/BATTERY_HARNESS.json`.
>
> **D-771 MADE IT A GUARANTEE RATHER THAN A HOPE.**  Every clause D-753 and D-765
> wrote asked whether an accessory could pull TOO MUCH; none asked whether the
> rail could DELIVER what the product promises.  At the 2.7 kΩ both rails carried,
> each limiter GUARANTEED only **0.277 A** — the board published a budget its own
> silicon could refuse to deliver, on the two contacts the Community Port exists
> for. `R97` is **1.78 kΩ** (0.636 A typ → **0.4279 A guaranteed**, +7.0%) and
> D-787 sets `R101` to **2.43 kΩ** (0.4555 A typ → **0.3065 A guaranteed**,
> +2.16%). `F6` refuses any setting that does not guarantee its published budget
> and also prices the user-reachable limiter corners against the first battery
> protection threshold.
>
> **What an accessory actually sees at the published budget** is now derived,
> not asserted: the D-787 3.3 V first-five path guarantees **3.146366 V minimum
> at 400 mA** against the 3.135 V floor, using the exact divider envelope and
> the measured/bounded TP12→J5 reinforcement. ACC_5V remains above its 4.75 V
> minimum under the existing D-773 boost/path proof.

**D-750 answered the external first-spin review's combined-load item with a
POLICY; D-753 replaced it with a LIMIT the silicon enforces.**  The policy read
*"firmware must not raise both accessory rails to their per-rail maxima
together"* — and this board has **no accessory current measurement**.  Firmware
can choose whether a rail is ON; it cannot know what an arbitrary external
accessory then draws.  The only thing that actually bounds an accessory is the
accessory limiter's own current limit, and at the values D-750 shipped those
limits sat far ABOVE what the policy permitted.

**CURRENT D-787: `R97` IS 1.78 kΩ AND `R101` IS 2.43 kΩ**; both were 2.7 kΩ at
D-753 (LCSC `C22849` and `C25964`, UNI-ROYAL `0603WAF1781T5E` /
`0603WAF2431T5E`, the same 0603WAF series and the same 0603 land as the parts
they replace).  TI equation 1 — `ILIM = 1.18 × (R[kΩ])^−1.072` — gives
**0.636 A** and **0.4555 A** typ, and the widest tolerance ratio the part's own EC table publishes
(0.68× / 1.32× of typ over −40…+125 °C, read off its 19.2 kΩ row) **taken over
the programming resistor's own 1 % band as well** brackets the rails at:

| rail | guaranteed | worst case | published budget (D-098) | headroom |
|---|---|---|---|---|
| `ACC_3V3_SW` (`R97` 1.78 kΩ) | **0.428 A** | 0.849 A | 400 mA | **+7.0 %** |
| `ACC_5V_SW` (`R101` **2.43 kΩ**, D-787) | **0.3065 A** | 0.6078 A | 300 mA | **+2.16 %** |

The 0.68×/1.32× ratio is the widest of the four `ILIM` rows TI publishes and is
**conservative in both directions at once** — the two rows that bracket these
settings (1.15 kΩ and 2.21 kΩ) publish 0.75–0.76× / 1.24–1.25×.

> ### THE INTERNAL `+3V3` LOAD THE ENVELOPE RUNS ON — ITEMISED AND CHECKED (D-772)
>
> Every figure in the table below is a function of the internal `+3V3` load, and
> that number had been a **hand-written `1.0`** in the contract since D-753.  It
> was LOW.  The repository's own last derivation — 823 mA, 2026-08-23 — is built
> on an FBV2-COMM-001 subtotal that contains **no NFC line at all**, because `U9`
> and its twelve decoupling capacitors were still **DNP** when it was written and
> **D-192 fitted them**; **D-205** then allocated the NFC front end **100 mA on
> `+3V3` with the field on**, and nothing added it.  The same subtotal counts
> *"the worst single radio"*, which is **not true of this board**: `U8` is an
> EXTERNAL `E22-900M22S` module on its own `+3V3` pin and nothing in hardware
> stops it transmitting while the ESP32 does.  *A rule no silicon enforces is the
> exact defect D-753 named.*
>
> | line | mA | refs | source |
> |---|---|---|---|
> | Wi-Fi / BLE TX, worst published RF condition | **355** | `U1` | ESP32-S3-WROOM-1 datasheet v1.8 Table 6-4, 802.11b 1 Mbps @20.5 dBm, **rated at 100 % duty** |
> | sub-GHz TX, the worse of the two shared-bus radios | **140** | `U7`/`U8` | Ebyte E22-M manual, 100–140 mA @22 dBm (the CC1101 is 35 mA); one TX at a time between **those two**, but **added to** the Wi-Fi line |
> | display logic + backlight at maximum | 181 | `J1`,`U17`,`L3` | FBV2-COMM-001 |
> | audio at the capped level | 120 | `U5` | FBV2-COMM-001 (the 230 mA peaks are local) |
> | microSD write | 100 | `J2` | FBV2-COMM-001 |
> | **NFC front end, field on** | **100** | `U9` | **D-205 — the line the 823 mA figure was missing** |
> | IR transmitter, burst average | 50 | `D1`,`Q1`,`R24` | D-155 (the 150 mA peaks are supplied by `C12`) |
> | touch + housekeeping | 13 | `U2`,`U3`,`U4` | FBV2-COMM-001 |
> | front RGB at white | 4.2 | `D13` | FBV2-S1-008 |
> | **TOTAL** | **1 063.2 mA** | | **was published as 1 000 mA** |
>
> **`F6` sums this table rather than asserting a constant, and reads the board's
> own `+3V3` net to prove nothing is missing from it**: every FITTED, non-passive
> consumer on the rail — twelve of them — must be named by a line, and a line all
> of whose parts have left the board is refused too.  The control that matters is
> **`f6o`: the budget with the NFC line removed**, which is the budget as it
> actually stood from D-192 until D-772.

> ### THE 5 V SETPOINT — DERIVED, NOT ASSERTED (D-773)
>
> The pack cost of `ACC_5V_SW` scales **directly** with the boost's output
> voltage, and that voltage was a constant in two places that disagreed: this
> contract carried **4.95 V** and `ARCHITECTURE.md` published **4.99 V**, *both
> derived from `VREF` = 0.6 V*.  **TI `SLVSF14B`'s EC table gives the `TPS61023`'s
> FB reference as 580 / 595 / 610 mV in PWM mode** — the typical is **595 mV**,
> not 600.  **`R99`'s own symbol note in the schematic had carried the correct
> 0.595 V all along**: the same shape as D-765, where this repository held the
> right number in a place the decision did not read.
>
> Over `R99` 732 kΩ and `R100` 100 kΩ at their own 1 % bands the real setpoint is
>
> | | min | typ | max |
> |---|---|---|---|
> | `ACC_5V_RAW` | **4.742 V** | **4.950 V** | **5.165 V** |
>
> **The envelope now runs on the maximum**, because that is what costs the most
> pack current, and the typical is reported beside it.  The same EC table carries
> `VOVP` — output over-voltage protection, **5.5 / 5.7 / 6.0 V rising** — and
> nothing had ever compared the two: a divider whose worst-case high reached the
> **minimum** OVP threshold would make a good board fault on itself.  It clears by
> **6.1 %**, and `F6` now refuses a divider that does not.
>
> **This is what moved `R101` from 2.32 kΩ to 2.37 kΩ.**  At the corrected
> setpoint, D-771's 2.32 kΩ left **0.52 %** of pack margin on the 5 V rail's
> limiter state.  2.37 kΩ is the **E96 value nearest the centre of that
> resistor's own legal window — 2.298 kΩ to 2.478 kΩ**: below 2.298 the limiter's
> worst case reaches the pack's minimum trip, above 2.478 the rail can no longer
> GUARANTEE the 300 mA D-098 publishes.  It trades delivery headroom there is
> plenty of (7.4 % → 4.9 %) for pack margin there was almost none of
> (0.52 % → 1.6 %).  **D-771's 2.32 kΩ broke no clause and is not described as
> if it had.**

**FAULT-ENVELOPE screen** — modelled at the 3.0 V BAT corner with that **1.063 A** internal `+3V3` load,
`U12` at 90 % and `U21` at 88 % into the boost's **worst-case 5.165 V setpoint**
(D-773, block below; at the 4.950 V *typical* setpoint the same rows read
2.337 / 2.470 / 2.410 / 2.351 / 3.508 A):

| state the Community Port can reach | D-750 (1.5 k / 1.65 k) | D-753/D-765 (2.7 k / 2.7 k) | D-771…D-773 (1.78 k / 2.37 k) — *HISTORICAL; D-787 fits 1.78 k / **2.43 k** and re-derives the whole table, see the D-787 block above* |
|---|---|---|---|
| 3.3 V rail alone at its limiter | 2.455 A | 1.879 A | **2.337 A** (+8.8 %) |
| 5 V rail alone at its limiter | **2.930 A — TRIPS** | 2.229 A | **2.521 A** (+1.6 %) |
| both rails at their GUARANTEED currents | **2.737 A — TRIPS** | 2.079 A | **2.438 A** (+4.8 %) |
| both rails at their PUBLISHED budgets | — | *unreachable — the limiter could refuse it* | **2.375 A** (+7.3 %) |
| both limiters in fault (double fault) | 4.162 A — past the LTC4368 | 2.886 A — **above the breaker's real 2.640 A minimum** | **3.558 A** — charger OCP, auto-retry, **10.2 % under the breaker's 3.960 A minimum** |

*(the D-750 and D-753/D-765 columns are the figures those decisions published,
at the 1.0 A internal term they used; only the last column is re-based on the
1.063 A D-772 derived.)*

> ### D-775 — NORMAL D-098 CONCURRENCY IS GATED, AND THE FLOOR IS SOLVED FOR RATHER THAN CHOSEN
>
> **HISTORICAL. SUPERSEDED BY D-787 FOR EVERY NUMBER IN THIS SECTION.**  The
> METHOD below is unchanged and still current — the floor is solved for, not
> asserted — but every figure was computed against a typed 3.3 V main rail and a
> 224 mΩ routed `ACC_3V3_SW` delivery path.  D-787 derives that rail from
> `R39`/`R40` and replaces the delivery path with the measured `TP12`→`J5`
> reinforcement, which moves the derived dual requirement to **3.8094 V** and the
> enforced firmware floors to **3.50 V single / 3.85 V dual**.  Read the D-787
> block above for the current contract; the 3.7622 V / 3.80 V / 2.250 A figures
> below are D-775's and are retained as history.
>
> The table above is the **hardware fault envelope**; it is not the normal-load
> battery-sag proof.  MAX17048 `VCELL` is measured on **`BAT_PROTECTED_P`**
> (`U14.2/U14.3`), the same node as BQ25185 `BAT` (`U11.2`).  The CTO hold
> correctly found that normal 400 mA + 300 mA concurrency lacked a gate, but its
> first ~3.85 V estimate counted cell/`Q2`/`Q3`/`R75` loss upstream of the gauge
> a second time.  D-775 starts at the actual measurement node instead — and the
> floor it enforces is **DERIVED**, not asserted.  A first D-775 draft priced the
> sag from a round **0.250 Ω** path "bound with contingency" plus a flat **60 mW**
> branch allowance and then checked the margin **at** a hand-written **3.75 V**;
> that is a check, not a derivation, and nothing in the repository could say why
> the number was 3.75 rather than 3.55 or 3.95.
>
> **EVERY SERIES TERM IS NOW MEASURED OR CITED.**  `F6` re-measures four paths off
> the live board on every run — `BAT_PROTECTED_P` (`R75.2`→`U11.2`) **43.1 mΩ**,
> the `SYS`→`U21` boost trunk **183.3 mΩ**, `ACC_3V3_SW` **224.4 mΩ** and
> `ACC_5V_SW` **110.6 mΩ** — takes each at its hot resistivity (×**1.2554**, from
> copper's own 0.00393/K over a 65 K rise; the same audit's worst accepted rise on
> the `BAT_PROTECTED_P` rail is 49.6 K), adds the BQ25185 BATFET maximum
> (`SLUSF65B` `RON_BAT` = **140 mΩ**, which the EC table's own
> −40…+125 °C header already covers) with a declared **1.40×** allowance for the
> 3.5 V / 2.3 A corner TI does not publish, and adds each load switch's own
> `RON` max (`SLVSGP6A` −40…+125 °C: **68 mΩ** at 3.3 V, **54 mΩ** at 5 V).  The
> `U21` boost's input current is then taken **through** the live trunk, so its loss
> is solved rather than allowed for.
>
> **THE FLOOR IS THE ANSWER, NOT AN INPUT.**  `required_*_floor_V` is the `VCELL`
> at which the resulting battery current reaches `IBAT_OCP`'s **minimum less 10 %**,
> derived twice — once on the live resistances, once on the declared path ceilings —
> with the firmware required to satisfy the worse of the two, rounded up onto a
> 0.05 V grid:
>
> | conforming normal load | derived requirement | enforced VCELL floor | modeled battery current | margin to 2.5625 A OCP min |
> |---|---:|---:|---:|---:|
> | 3.3 V, 400 mA | 2.9516 V | **3.50 V** | **1.776 A** | **30.7 %** |
> | 5 V, 300 mA | **3.1232 V** → 3.15 | **3.50 V** | **1.908 A** | **25.6 %** |
> | both published budgets | **3.7622 V** → **3.80** | **3.80 V** | **2.250 A** | **12.2 %** |
>
> **THE DERIVATION MOVED THE FLOOR.**  3.7622 V is **above** the 3.75 V the first
> draft asserted: the draft passed only because its round 0.250 Ω and flat 60 mW
> under-counted the accessory-rail copper, the two limiter `RON`s and the
> `SYS`→`U21` trunk.  The firmware dual-rail floor is **3.80 V**.  The single-rail
> requirement is 3.1232 V, so D-766's existing **3.50 V** policy floor stands
> unchanged and well clear.  Without any floor at all, both published budgets at
> 3.50 V leave **0.4 %** of margin on the live resistances and are **negative** on
> the declared ceilings — the gate is not decorative.
>
> **HOW MUCH OF THE FLOOR IS CONVENTION.**  The zero-margin dual-rail floor is
> **3.5207 V**; the 10 % headroom is a declared design convention covering what the
> model does not itemise (pour-delivered `+3V3` distribution, efficiency below the
> conservative 90 %/88 % used, cell-to-cell spread), and it is reported beside every
> case so physics and convention stay separable.  The unpublished BATFET
> extrapolation is bounded the same way: at 3.80 V the 10 % margin survives a BATFET
> up to **1.60×** the datasheet maximum, and `IBAT_OCP`'s own minimum is not reached
> until **2.26×**.
>
> **WHAT THE USER GETS.**  Firmware permits one rail from 3.50 V, requires 3.80 V
> before a second rail is enabled, fails closed when `VCELL` is unreadable, sheds the
> **5 V rail first** if a dual-rail load falls below 3.80 V — leaving the 3.3 V rail
> its full published 400 mA — and sheds all accessory power below 3.50 V.  Only the
> **simultaneous full-budget** case is restricted; each rail individually remains
> available to 3.50 V.  `F6` parses the actual firmware constants, requires the gauge
> and charger `BAT` pins to be on `BAT_PROTECTED_P`, and refuses a live path that has
> grown past its declared ceiling.  Five destructive controls are refused: the old
> single 3.50 V dual floor, **the first draft's asserted 3.75 V**, a single-rail floor
> under its own requirement, and `BAT_PROTECTED_P` or `SYS`→`U21` copper past its
> ceiling.  `H6` adds three C++ mutations — collapsing the dual floor, failing open on
> an unreadable gauge, and losing the 5 V-first shed order.
>
against a `BQ25185` `IBAT_OCP` band of **2.5625 / 3.125 / 3.6875 A** (3.125 A typ
± 18 %, `SLUSF65B`), the `LTC4368` breaker at **3.960 / 5.000 / 6.061 A**
(40/50/60 mV guaranteed across `R75` 10 mΩ ± 1 %) and `F1` at 5 A.

> **ENVELOPE.**  No state a user can reach exceeds the FIRST trip any unit can
> have.  **The thinnest margin on this board is 2.6 %**, and it is worth naming
> exactly: it is the 5 V accessory **in overcurrent** — a FAULT, not a
> conforming load — *while every internal subsystem runs at once*: Wi-Fi TX and
> a LoRa TX and the NFC field and audio and a microSD write and the backlight at
> maximum and an IR burst, on a `BQ25185` sitting at the −18 % corner of its
> `IBAT_OCP` band, with the cell at 3.0 V.  Its consequence is an `IBAT_OCP`
> **hiccup that re-enables the BATFET** — and D-771 guaranteed that hiccup happens before
> the latching breaker on **every** unit.  At a conforming accessory load the
> margin is 8.3 %.  A *simultaneous double limiter fault* reaches 3.534 A, still
> **10.8 % below** the breaker's guaranteed minimum and below the one-shot fuse.
> `checks/demo_feature_contract.py` **F6** recomputes all of this from the two
> resistors, the two limiter part numbers, **`R75`, `U18` and the itemised
> internal budget** — the board's own values, not constants — with **twenty-three**
> live negative controls, three of which are boards this project actually
> shipped.

> **D-771 — THE PROTECTION CHAIN WAS ORDERED AGAINST A TYPICAL.**  `F6`'s
> `double_fault_stays_inside_the_protection_chain` clause compared the double-fault
> current against **3.3333 A = 50 mV / 15 mΩ**, as though 50 mV were a limit.  ADI's
> own Rev C Electrical Characteristics guarantees `ΔVSENSE,F` only as
> **40 / 50 / 60 mV** over temperature (`VOUT = VIN`), so at `R75` = 15 mΩ ± 1 % the
> breaker's real band was **2.640–4.040 A** — which OVERLAPPED the `BQ25185`'s
> `IBAT_OCP` band of 2.5625–3.6875 A by 1.05 A.  **`RETRY` is grounded** (sheet 01,
> D-050/D-052/D-064/D-068), so this breaker **LATCHES OFF** and is cleared only by
> toggling `SHDN`, while `IBAT_OCP` hiccups. **D-779 COMPLETES THE SENTENCE**: SLUSF65B 6.3.7.3 re-enables the BATFET after `tREC_SC`, but **4 to 7 consecutive trips inside a 2 s window leave the BATFET OFF until a valid VIN is connected** — a SUSTAINED battery overcurrent is a battery-only dead stop the user clears with USB, not an indefinite retry. The D-771 ordering is unchanged; the stated consequence is.  On an unlucky unit
> the LATCHING protection fired first, and the board D-765 shipped reached 2.886 A
> in double fault — **above the breaker's own 2.640 A minimum**, so the clause was
> FALSE on the board that passed it.  At **10 mΩ** the breaker is 3.960–6.061 A,
> **entirely above** `IBAT_OCP`'s 3.6875 A maximum: the RECOVERABLE protection is
> now guaranteed to act first on **every** unit.  Ordering against `F1` is a
> TIME-CURRENT result, not a threshold comparison — `tp(GATE)` 3–18 µs against a
> 5 A fast-acting Nano2 that needs 5 s at 200 % of rating.  The hard-short row
> (`VOUT = 0 V`, 30/50/70 mV) is not the ordering row: it describes a collapsed
> output, where latching is the wanted behaviour.
>
> **AND THE CONVERTERS MUST BE ABLE TO SOURCE WHAT THE LIMITERS PERMIT** — a
> question nothing in this repository had ever asked.  `U12` `TPS63020` is rated
> **2 A for VIN > 2.5 V, VOUT = 3.3 V** (`SLVSAA7` Features) against a worst case
> of **1.063 A internal (D-772) + 0.849 A accessory = 1.912 A**, a 4.4 % margin.  `U21` `TPS61023` delivers
> **0.911 A** at this operating point by `SLVSF14B` equation 1 with `ILIM_SW` at
> its **2.7 A EC minimum**, `L4` at its −20 % corner and the boost at its
> worst-case setpoint, against a worst case of **0.6078 A** (D-787; **0.624 A** at D-773's 2.37 kΩ).  `F6` refuses a limiter its converter cannot feed — which is what
> now refuses D-750's 1.5 kΩ setting on `R97`.

> **D-765 — THE ENVELOPE WAS RIGHT AND THE SILICON COULD NOT LEGALLY HOLD IT.**
> Every number in the table above is unchanged.  What was wrong was the part.
> D-753 programmed **0.407 A typ on a `TPS22950C`**, and **section 5 of the very
> datasheet it cited (`SLVSFJ2B`, Device Comparison Table) gives the `C` variant
> an `ILIM` range of 0.5–3.5 A**.  The 0.05 A floor and the *"certified from
> 66 mA"* UL note D-753 reasoned from belong to the **base `TPS22950`, which TI
> sells only in a WCSP package this board cannot use**.  The accessory limiters
> were therefore programmed **below their own recommended operating condition**,
> where the datasheet warrants nothing — on the one element standing between a
> user's accessory and the pack.  This repository's own 2026-08-22 architecture
> reconciliation had the `C` variant's 0.5–3.5 A recorded correctly, and so did
> the schematic symbol's own description.
>
> **`U20` and `U22` are now the `TPS22950-Q1`** (`SLVSGP6A`, orderable
> **`TPS22950CQDDCRQ1`**, LCSC `C17349276`, Active/Production, 4 050 in stock),
> whose single specified `ILIM` range is **0.05–3.5 A**.  **No resistor, no
> copper and no envelope number changes.**  It is the same **`DDC0006A`** land
> pattern, the same `ON`/`VIN`/`GND`/`ILIM`/`VOUT`/`FLT` pinout, the same
> `1.18 × R^−1.072` equation with the same published EC rows, the same
> **auto-retry** overcurrent response, the same always-on **true reverse-current
> blocking** (44 mV / 3 µs / 38 µA), the same `FLT` semantics (thermal shutdown
> and reverse current only), the same **170 °C / 150 °C** thermal shutdown — and
> it is **AEC-Q100 grade 1**.  Turn-on is slower (1 037 µs vs 800 µs at 5 V),
> which only softens accessory inrush.  `IMAX` falls 3.2 A → 2.7 A, against a
> 0.537 A worst-case use *at the resistors D-765 inherited* — **0.849 A at the
> fitted ones**, still 3.2× under `IMAX`.  Prototype cost delta ≈ **US$0.03 per
> device**.  The settings also sit inside the **UL 2367** recognised window
> (66 mA–2.46 A) at 2.7 kΩ and at 1.78 kΩ / 2.37 kΩ alike, and at the CURRENTLY FITTED 1.78 kΩ / **2.43 kΩ** (D-787).  **F6 now
> refuses any limiter whose `ILIM` setting falls
> outside that part's OWN published range** over the programming resistor's
> whole tolerance band, refuses a limiter it has no published range for, and
> refuses two different limiter MPNs across the two rails.

**RESIDUAL, NAMED NOT HIDDEN — RE-DERIVED AT D-771.**  `.kicad_dru` section 5
sizes `BAT_MAIN` copper for **1.5 A sustained**, and the worst *sustained* case
exceeds that sizing point at the low-battery end, on one unavoidable
5.525 mm × 0.200 mm segment: `U11`'s `DLH0010A` pin-2 `BAT` land, which nothing
wider can land on (D-269, D-708).

| sustained state (internal `+3V3` load **1.063 A**, boost at its worst-case **5.165 V**) | at 3.7 V | at 3.0 V |
|---|---|---|
| both rails at D-098's **PUBLISHED** budget | 1.926 A | **2.375 A** |
| both rails at their **GUARANTEED** currents | 1.977 A | **2.438 A** |

D-765 printed **1.69 A / 2.08 A** here, and those were the numbers of a board
whose limiters could not deliver what the product publishes.  **THE PUBLISHED
ROW IS THE REQUIREMENT AND IT HAS NOT MOVED**: D-098 has promised 400 mA +
300 mA since 2026-08-23, which is 2.375 A at the 3.0 V corner *whatever the
`ILIM` resistors are set to* (2.274 A at the 1.0 A internal term and 4.95 V
setpoint D-771 used, before D-772 itemised the one and D-773 derived the other).  What D-771 changed is that the hardware can now
honour it; the GUARANTEED row sits 3.3 % above the PUBLISHED one because a
limiter must be set with margin to guarantee anything at all.

The plane-coupled model puts that segment's ceiling at **51.5 K** over the
adjacent `In4` plane at 2.438 A, **48.9 K** at 2.375 A and **19.5 K** at 1.5 A.
The model explicitly ignores lateral spreading, conduction along the copper and
convection from an OUTER layer — and the necked copper is **0.575 mm** long
before it tapers 0.3 / 0.4 / 0.6 / 0.8 / 1.0 / 1.2 mm, against a copper thermal
length of ≈ 2.6 mm, so both ends of the neck sink most of it.  It is a ceiling,
not a prediction.  **This is a FIRST-ARTICLE THERMAL MEASUREMENT** at the 3.0 V
corner with both accessory rails loaded — not a pre-order blocker: the
electrical envelope above is closed by hardware, no user-reachable state trips
the pack, and the alternative (leaving the limiters where D-753 left them)
publishes a budget the board can refuse to deliver.

### 6.3b Capacitor derating — the rule, applied to the parts this board FITS (D-774)

`screen_bom_sourcing.net_gate` has carried the project's rule since D-615 —
**2× the node's OPERATING maximum, AND plain survival against its ABSOLUTE
maximum** — over a 48-node voltage table.  **It runs only while proposing a part
for an UNSOURCED line, and this BOM has had none since D-615**, so the rule had
never once been applied to a part on the board.  `F8` now applies it.

**Every fitted capacitor survives its node's absolute maximum.**  Five 10 V X7R
parts on 5 V-class rails sit under the 2× *convention* and are accepted as named,
reasoned exceptions:

| ref | value | node | operating | absolute | ratio |
|---|---|---|---|---|---|
| `C20` | 4.7 µF 10 V X7R | `USB_VBUS_RAW` | 5.25 V | 5.50 V | **1.91×** |
| `C65`, `C66` | 22 µF 10 V X7R | `ACC_5V_RAW` | 5.165 V | 6.00 V | **1.94×** |
| `C38`, `C67` | 1 µF 10 V X7R | `ACC_5V_SW` | 5.165 V | 6.00 V | **1.94×** |

`C20`'s operating figure **is already a worst case** — the USB 2.0 *source
maximum*, not a 5.0 V nominal — so the convention is applied twice over; it
survives the absolute at 1.82×.  The four accessory-rail parts are measured
against D-773's **derived** 5.165 V, and the DC-bias capacitance loss the 2×
convention exists for is **already in the design**: D-186 sizes the boost output
at **44 µF NOMINAL** across `C65` + `C66` precisely because a 10 V X7R at 5 V bias
retains roughly half.  A **22 µF 16 V X7R is a 1206 part** and does not fit the
fitted 0805 land.

> **Boundary, stated.**  Ratings are read from the VALUE STRING, which **37 of
> the 76** fitted capacitors carry; the other **39** state only a capacitance and
> their rating lives in the sourced part record — that count is **pinned**.
> **Twelve** capacitors sit on nodes the table has no DC entry for: the NFC
> matching and crystal network, 50 V C0G parts on a 13.56 MHz node whose
> governing rating is **RF peak, not a DC rail voltage**.  They are reported,
> not refused.  `net_gate` still refuses a *new* part grafted onto an
> unestablished node.

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

> **NOT ON THIS LIST, AND NOT ON THIS REVISION — D-776.**  **There is no
> USB-present / charging indication.**  `/01_POWER_TREE/VBUS_PRESENT` is a
> fitted `R104` 150 kΩ / `R105` 220 kΩ divider with a `C68` filter that reaches
> **`TP31` and nothing else** — no MCU pin and no expander bit — and the
> generated firmware map's as-built limits had told firmware to infer charging
> state from exactly that signal.  Two more of the same shape are also
> unreadable: the **`LTC4368` latching FAULT output** and the **`TPS63020`
> POWER GOOD**.  What the product DOES have is what is promised above:
> state-of-charge and pack voltage from the MAX17048, and a directly observed
> charger FAULT from `STAT1` LOW.  **Do not claim a charging indicator.**  The
> Rev-B fix is measured — move `R104`/`R105`/`C68`/`TP31` beside `U3` and land on
> `U3` P06, zero BOM change; the haul from the present location is `NO_PATH` on
> all three routable layers.  The full list of probed-but-unreadable nets is
> **computed off the copper** by `gen_firmware_hw_map.py`, which refuses to emit
> if any of them is undeclared or if a declaration goes stale.

---

## 16. Known UNRESOLVED items (verify or omit before any public claim)

1. ~~**Battery fitted capacity (mAh)** — envelope 2500–3000 mAh only; SKU deferred (M-04).~~ **CLOSED at CTO-BAT-01:** first-five pack is Adafruit Product 328, 2500 mAh, protected, genuine JST-PH; exact supplier-linked battery specification and electrical/load-margin contract are pinned in `assembly/SELECTED_BATTERY.json`.
2. ~~**Charge current (ICHG)** — programmed value not fixed.~~  **CLOSED at D-743:** 769 mA from `R37` 390 Ω, input limit 1100 mA and `VBATREG` 4.2 V from `R36` 13 kΩ.  The old 1 kΩ / 18 kΩ pair programmed 300 mA against a 360 min safety timer and could not complete a charge.
3. **microSD max card capacity** — not stated.
3a. ~~**Charging / USB-attach indication** — assumed available.~~ **RESOLVED at D-776 as a LIMITATION, not a capability:** it is not available on this revision and was never promised.  `VBUS_PRESENT` reaches `TP31` only; the as-built limits had named it as a firmware input and have been corrected in the generated map, both schematic sheets and `Firmware/README.md`.  The list of unreadable signals is now derived from the copper and gated in both directions.  Rev-B fix measured (move the divider beside `U3`; zero BOM change).
4. **Touch controller silicon** — FT6236 vs CST026 (interface locked; PO must specify).
5. ~~**Display driver symbol metadata** — stale ILI9341/CH280QV10 text vs locked ILI9488.~~ **CLOSED at D-768.**  It was worse than metadata: the stale string was on the `J1` **instance**, so *"CH280QV10-CT Rev.D 2.8in 240x320 IPS TFT + CTP"* was a column in the **released BOM**, and the `ER-TFT035IPS-6_50P` symbol's own `Package` field still credited *"SPEC-CH280QV10-CT_Rev.D pages 6-7. TFT driver ILI9341V"* for a pin table D-112 had transcribed from a different datasheet — on the one connector whose pin table had already been **dead on arrival** for exactly that reason (LEDA/LEDK reversed, WRX/D-CX swapped).  The board was and is correct; every place that names the panel now says `ER-TFT035IPS-6` / ILI9488, the two retired display symbols are annotated `RETIRED -- DO NOT INSTANTIATE`, and **`F7`** asserts the locked identity in the placed symbol, its library definition **and the released BOM row**, with three live controls.
6. ~~**915 antenna doc residue** — stale FXP890 vs locked external TI.92.2113 SMA.~~ **CLOSED at D-769.**  `U8`'s `Package` field, the sheet-level module note and the `ARCHITECTURE.md` row all named the internal `Taoglas FXP890.07.0100C` flex that D-198 superseded; all three now name the **external `TI.92.2113` SMA(M) dipole** reached through the module IPEX → `CBA-UFLSMA20IP` pigtail → top-panel SMA(F) bulkhead.  **`F7`** — generalised from D-768's display clause into a registry of recorded supersessions — now refuses a retired part name anywhere in the fields of the part that replaced it, `J1` and `U8` alike, with four live controls.
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
