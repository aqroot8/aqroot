# AQROOT Full Beta v2 — Display and Connector Procurement Lock

Date: **2026-08-23** (task-assigned date; repository session date 2026-08-22)
Task: **FBV2-DISP-002**
Repository HEAD at audit: `42a5e0a`
Scope: **documentation only.** No KiCad, PCB, firmware, mechanical CAD or fabrication
file was created or modified. `hardware/beta-v2/` was not created.

Supersedes the *candidate* status recorded by
[`2026-08-22-display-interface-closeout.md`](2026-08-22-display-interface-closeout.md)
(FBV2-DISP-001). That audit's **interface requirement** stands; its leading
candidate does not.

---

## 0. Verdict

> ### FBV2-DISP-LOCK = **PASS**
>
> **Display: EastRising `ER-TFT035IPS-6` + `ER-TPC035-6`**
> **Connector: Hirose `FH69-50S-0.5SH`**
> **M-06 CLOSED. M-07 CLOSED.**
> Full Beta v2 is cleared for **FBV2-S1**, including sheet `03_spi_a_display_sd`.

Every gate condition in §9 is met from primary vendor documents, and both halves
of the mating pair are proven against **each manufacturer's own drawing** rather
than against a matching pin count.

---

## 1. Sources

| # | source | weight |
|---|---|---|
| **S1** | **`ER-TFT035IPS-6_Datasheet`, EastRising, Rev 2.0, released Aug-18-2025, 24 pp** — full 50-pin table, three outline drawings (no-TP / RTP / CTP), FPC construction, backlight table | **Primary vendor document**, retrieved and text-extracted in full |
| **S2** | EastRising `ER-TFT035IPS-6` and `ER-TPC035-6` product records (buydisplay.com) — outline dimensions, connector call-out, continuity-supply commitment, pricing tiers, stock | **Primary vendor product data** |
| **S3** | **Hirose `FH69` series catalogue** (`en_FH69_CAT`) — product specifications, recommended FPC construction, land pattern, part table | **Primary manufacturer document**, retrieved and text-extracted |
| **S4** | **Hirose `FH52` series catalogue** (`en_FH52_CAT`) — contact orientation, FPC thickness, land-pattern interchange note | **Primary manufacturer document** |
| **S5** | Digi-Key catalogue record for `FH69-50S-0.5SH` — stock, price, lifecycle, contact type | Distributor, authoritative for availability |
| **S6** | TI `TPS61169` datasheet **SNVSA40B** (already cited by the Beta-DM schematic) — `VREF`, `VOVP_SW`, switch limit | Primary, partly re-confirmed via `hardware/beta-dm/BETA-DM-BACKLIGHT-ANALYSIS.md` |
| **S7** | `hardware/beta-dm/BETA-DM-BACKLIGHT-ANALYSIS.md` (read only) | **Measured** — the as-built Beta-DM backlight topology, pin by pin |
| **S8** | `11 - Beta Pin Map v0.2.md` (read only) | **Measured** — the existing SPI-A / touch / expander assignments |
| **S9** | Riverdi `DS_RVT35HITNWC00-B` Rev 1.1, Focus LCDs `E35RG73248LW6M250-C_Spec`, Winstar `WF35UTYAIDNN0`, Raystar `RFI350U-AYW-DNN`, VIEWE `UE035HV-RB40-A118`, DisplayModule `DM-TFT35-431`, Newhaven 3.5" IPS line | Primary vendor documents for the **rejected** candidates |

Everything asserted below is traceable to one of these. Where a figure is
inferred rather than stated, it says so.

---

## 2. The market survey, and what it actually found

Eleven suppliers were examined against the hard requirements. The survey was
deliberately widened beyond Chenghao as instructed.

| supplier | best 3.5" 320x480 part found | outcome |
|---|---|---|
| **EastRising** | **`ER-TFT035IPS-6` + `ER-TPC035-6`** | **SELECTED — #1** |
| **EastRising** | `ER-TFT035-6` + `ER-TPC035-6` | **#2 fallback** — identical interface, TN optics |
| **VIEWE** | `UE035HV-RB40-A118` | **#3 fallback** — ST7365P, but **61.5 mm wide**, 1.5 mm over the envelope |
| Chenghao | `CH350HV40A-CT` | **Rejected / backup** per CTO. See §2.3 — its outline is now shown to be the same glass |
| **Riverdi** | `RVT35HITNWC00-B` | **Rejected.** 59.56 x **93.34 x 5.66 mm** (fails H and T) and a **10-LED, 14–16 V, 100 mA** backlight — ~1.5 W, and a completely new driver |
| **Focus LCDs** | `E35RG13248LW2M450-CA` (IPS) | **Rejected — End of Life.** Sibling `-C` is **NRND**, 8 pcs in stock at **US$109.13** |
| **Focus LCDs** | `E35RG73248LW6M250-C` (TN) | **Rejected.** 61.90 x 91.04 x 4.33 mm — fails W and H; needs **two** connectors (50-pin LCD + 8-pin CTP) |
| **Winstar** | `WF35UTYAIDNN0` | **Rejected.** Excellent 54.5 x 83.0 x 2.46 mm IPS / ILI9488 LCM, but **no touch variant** at this resolution; 3-line SPI only |
| **Raystar** | `RFI350U-AYW-DNN` | **Rejected.** 54.5 x 83.0 x 2.46 mm IPS / ILI9488, **without touch screen** |
| **Newhaven** | 3.5" IPS line | **Rejected.** Current 3.5" IPS parts are **640x480 MIPI DSI / HDMI**. The ESP32-S3 has no MIPI DSI |
| **DisplayModule** | `DM-TFT35-431` | **Rejected.** ST7796S, 54.58 x 83.57 x 2.18 mm — but **no touch controller documented**, US$39.90 |
| Waveshare / Elecrow / Spotpear / ProtoSupplies / Hosyond | 3.5" ST7796S + FT6336U boards | **Rejected — hobby breakout boards**, explicitly excluded by the brief |

### 2.1 The finding the CTO should read first

**No ST7796S / ST7796U 3.5" 320x480 IPS module with a capacitive touch panel, a
named touch controller and a complete public FPC specification exists from a
production supplier.** The survey found ST7796S in exactly three forms:

1. **hobby breakout boards** (Waveshare, Elecrow, Spotpear, ProtoSupplies) — excluded by the brief;
2. **touch-less industrial LCMs** (`DM-TFT35-431`) — no CTP, no CTP documentation;
3. **modules whose FPC data is ambiguous** — the exact failure mode this task exists to avoid.

Every candidate that satisfies *all* of "IPS + capacitive touch + named CTP +
published FPC pitch, thickness and contact side + current production" carries
**ILI9488**. That is not a preference, it is what the market supplies at this
size. The preference for ST7796S in FBV2-DISP-001 was correct on the engineering
merits and is **overridden by availability**, with the cost quantified below.

### 2.2 Explicit comparison — ST7796S/U versus ILI9488

| | ILI9488 (selected) | ST7796S / ST7796U (preferred, unavailable) |
|---|---|---|
| SPI colour depth | **18 bpp only — 3 bytes/pixel** | 16 bpp RGB565 — 2 bytes/pixel |
| Full 320x480 frame | **460.8 kB** | 307.2 kB |
| Full frame @ 80 MHz FSPI IO_MUX | **46 ms → 21.7 fps** | 31 ms → 32.6 fps |
| Typical LVGL dirty-rect update (quarter screen) | 11.5 ms | 7.7 ms |
| Penalty | **+50 % SPI-A traffic** | baseline |
| Available in a fully documented IPS + CTP LCM | **YES** | **NO — see §2.1** |

**The 50 % penalty is real and is accepted.** AQROOT's brief is menus, graphs,
logs and status screens, not video. 21.7 fps *full-screen* is a screen-transition
figure; ordinary interaction repaints a fraction of the panel. The N16R8's 8 MB
PSRAM holds a 460.8 kB frame buffer with room for double buffering. The contention
that matters is with microSD on the same bus, and that is a firmware scheduling
matter already on the FBV2-B2 list.

### 2.3 A by-product: D-073's ambiguity is largely explained

`ER-TFT035-6` with CTP measures **56.54 x 84.96 mm**. Chenghao's
`CH350HV40A-CT` is documented at **56.54 x 84.96 x 3.97 mm**. Those are not
similar numbers, they are the same numbers to 0.01 mm, on a part with the same
active area and the same 6-LED parallel backlight. **The two are, to a high
confidence, the same glass and the same touch panel from the same upstream
supplier**, sold by two module houses.

EastRising documents that tail as **50-pin, 0.5 mm pitch, bottom contact,
0.30 ± 0.03 mm thick**. Chenghao's *"pin pitch 0.3 ~ 0.4 mm"* is therefore very
likely a datasheet defect that conflates the FPC *thickness* (0.3 mm) and the
conductor *width* (0.35 mm) with pitch.

**This is an inference, not a proof, and it changes nothing about the ruling** —
Chenghao stays rejected because a supplier that cannot state its own pitch cannot
be designed against. It is recorded because it retires the fear behind D-073 that
the *family* uses a sub-0.5 mm pitch. It does not.

---

## 3. The selected display, verified parameter by parameter

### 3.1 Ordering identity

| item | order number | source |
|---|---|---|
| **TFT LCD module** | **`ER-TFT035IPS-6`** | S1 §1.1 |
| **Capacitive touch panel with controller** | **`ER-TPC035-6`** | S1 §1.1, S2 |
| Manufacturer | **EastRising Technology Co., Limited** (trading as BuyDisplay) | S1, S2 |
| Ordering note | the CTP is **attached by default**; it must be specified as `ER-TPC035-6` (FT6236) and **not** the alternative CST340 panel the vendor also sells for this size | S2 |

### 3.2 Full specification

| parameter | value | source |
|---|---|---|
| Diagonal / type | 3.5 in, **IPS**, transmissive | S1 §2.4, S2 |
| Resolution | **320 x 480** | S1 §2.1 |
| Dot pitch | 0.153 x 0.153 mm | S1 §2.2 |
| **TFT controller** | **ILI9488**, COG | S1 §2.3 |
| **Touch controller** | **FT6236** (FocalTech), I2C, **address 0x38** | S1 §1.1, S2, FT6236 datasheet |
| Interfaces | 8080 8/9/16-bit parallel, **3-wire 9-bit SPI**, **4-wire 8-bit SPI**, RGB | S1 §2.3, Note 1 |
| Colours / contrast / brightness | 65K/262K/16.7M · 500:1 · 300 cd/m2 | S1 §2.4 |
| Viewing angle | 80 / 80 / 80 / 80 deg | S1 §2.4 |
| Response time | 20 ms | S1 §2.3 |
| **LCM outline (no touch)** | **54.50 (W) x 83.00 (H) x 2.30 (T) mm**, FPC folded | S1 §2.2 |
| **CTP outline** | **56.54 (W) x 84.96 (H) x 1.075 (T) mm** | S2 (`ER-TPC035-6`) |
| **Assembled LCM + CTP outline** | **56.54 (W) x 84.96 (H) x 3.95 ± 0.25 (T) mm** | S1 §3.3 drawing |
| Visual area | 49.96 x 74.44 mm | S1 §2.2 |
| Active area | 48.96 x 73.44 mm | S1 §2.2 |
| **VCI** (analog) | 2.5 – **3.3** V, typ 2.8 | S1 §4.3 |
| **VDDI** (logic) | 1.65 – **3.3** V, typ 2.8 | S1 §4.3 |
| Absolute maximum VCC / IOVCC | −0.3 … **+4.6 V** | S1 §4.2 |
| **Backlight** | **6-chip parallel** white LED, single anode + common cathode | S1 §4.4 |
| Backlight Vf | **2.9 – 3.2 V** at I = 120 mA | S1 §4.4 + §3.3 drawing |
| Backlight current | **120 mA** normal, **90 mA** dimming / life point | S1 §4.4 |
| LED life | **>= 30 000 h** at 90 mA, Ta = 25 °C | S1 §4.4 |
| Operating / storage temperature | −20 … +70 °C / −30 … +80 °C | S1 §2.1 |

### 3.3 The FPC — the parameter set that failed every other candidate

| parameter | value | source |
|---|---|---|
| **Pin count** | **50** | S1 §2.1, §4.1 |
| **Pitch** | **0.50 mm** — stated as a single figure, and corroborated geometrically: 50 pins spanning **24.5 ± 0.03 mm** pin-1-to-pin-50 = 49 x 0.5 mm exactly | S1 §2.1 + §3.3 drawing |
| **Contact side** | **BOTTOM CONTACT** — stated verbatim in the specification table: *"Display Connector: 50 Pin 0.5mm Pitch Bottom Contact ZIF Connector"* | **S1 §2.1** |
| **Tail thickness** | **FPC + PI = 0.30 ± 0.03 mm** | **S1 §3.3 drawing** |
| Tail width | **25.5 ± 0.15 mm** | S1 §3.3 drawing |
| Conductor width | 0.35 ± 0.03 mm | S1 §3.3 drawing |
| Tail free length | **30 ± 0.5 mm** (CTP variant) | S1 §3.3 drawing |
| Connection type | Plug-in FPC (ZIF) | S2 |

**Nothing in that table is inferred.** Pitch, thickness and contact side are the
three facts D-049 forbids guessing, and all three are printed in the vendor's own
document.

### 3.4 Complete pin assignment (S1 §4.1, verbatim)

| pin | name | pin | name |
|---|---|---|---|
| 1 | **LEDA** — backlight anode | 33 | **SDO** (serial out) |
| 2 | **LEDK** — backlight cathode | 34 | **SDA** (serial in / bi-dir) |
| 3 | **LEDK** — backlight cathode | 35 | RD (parallel read) |
| 4–6 | NC | 36 | **WRX (SCL)** — serial clock |
| 7 | **IM0** | 37 | **D/CX** |
| 8 | **IM1** | 38 | **CSX** |
| 9 | **IM2** | 39 | TE (tearing effect out) |
| 10 | **RESET** | 40 | **VDDI** |
| 11 | VSYNC | 41 | **VDDI** |
| 12 | HSYNC | 42 | **VCI** |
| 13 | DOTCLK | 43 | GND |
| 14 | DE | 44 | **XR(X+) / SCL** — CTP I2C clock |
| 15–32 | DB17–DB0 | 45 | **YD(Y+) / SDA** — CTP I2C data |
| | | 46 | **XL(X−) / IRQ** — CTP interrupt |
| | | 47 | **YU(Y−) / RST** — CTP reset |
| | | 48–50 | GND |

**Display and touch leave the module on ONE 50-pin tail.** There is no second
connector, no second FPC and no soldered flying lead. That is a material
advantage over the Focus LCDs parts, which need a 50-pin LCD connector *and* a
separate 8-pin CTP connector.

Interface-mode strap (S1 §4.1 Note 1): **IM2 IM1 IM0 = 1 1 1 → 4-wire 8-bit
serial**, using SCL, SDA/SDO, D/CX, CSX. Pins 7–9 are tied to VDDI. **No GPIO is
consumed by the strap.**

### 3.5 The one documentation gap, stated plainly

S1 does not name which FPC pin supplies the FT6236's own VDD. Pins 44–47 carry
the CTP's SCL / SDA / IRQ / RST; the CTP's VCC and GND are drawn from the
module's own **VDDI / VCI / GND** on the same tail.

**This is immaterial to AQROOT** because VDDI, VCI and the CTP supply are all
**+3V3** in this design, so no extra pin is needed and no configuration choice
exists. It is recorded as a first-article confirmation item (**B-30**), not a
blocker.

### 3.6 Supply voltage decision

VCI and VDDI are both driven from **+3V3**. 3.3 V is the top of the datasheet's
*recommended* range (VCI 2.5–3.3 V, VDDI 1.65–3.3 V), against an absolute maximum
of 4.6 V — a 1.39x margin. The alternative, a 2.8 V LDO, would buy nothing: the
ESP32-S3 drives 3.3 V logic, so a 2.8 V panel would need level translation on six
lines, and the vendor sells the breakout variant of this same panel with a 3.3 V
supply option. **Run at +3V3. No level shifting. No new rail.**

---

## 4. Connector lock

### 4.1 Selected — Hirose `FH69-50S-0.5SH`

| parameter | value | source |
|---|---|---|
| Manufacturer / MPN | **Hirose Electric — `FH69-50S-0.5SH`** | S3 |
| Hirose part code | **CL0580-5008-0-00** | S3 part table |
| Contacts | **50** | S3 |
| Pitch | **0.50 mm** | S3 |
| **Contact position** | **TOP *and* BOTTOM** — 2-point contact on both faces. Hirose: *"Can be used with both top and bottom contacts."* | **S3, Features 1** |
| **Applicable FPC thickness** | **t = 0.30 ± 0.05 mm, gold plated** | **S3, Product Specifications** |
| Geometry | SMT, **right-angle** (horizontal FPC entry), height **2.3 mm** | S3, S5 |
| Locking | **Backflip / flip-lock ZIF**, back-lock | S3, S5 |
| Rated current / voltage | 0.5 A / 50 V AC-DC | S3 |
| Operating temperature | **−55 … +125 °C** | S3 |
| Contact finish | Gold | S5 |
| Halogen-free | Yes | S3 |
| Land pattern | dedicated FH69 pattern published; Hirose also states the **FH28 / FH28K / FH52E / FH52K / FH52T / FH75** 0.5 mm land patterns **can be used with FH69** | **S3, Recommended PCB Layout note** |
| Contact-area width, 50 pos | **24.5 mm** (C dimension) | S3 |

### 4.2 The compatibility proof, from both drawings

This is the check the brief demands, and it is not a pin-count match.

| dimension | display FPC (S1) | connector (S3) | verdict |
|---|---|---|---|
| Contacts | 50 | 50 | **match** |
| Pitch | 0.50 mm (24.5 ± 0.03 mm over 49 spaces) | 0.50 mm (C = 24.5 mm over 50 pos) | **match, to the same 24.5 mm datum** |
| **Tail thickness** | **0.30 ± 0.03 mm** | **0.30 ± 0.05 mm required** | **match, and the display is the tighter tolerance** |
| **Contact side** | **bottom** | **top *and* bottom accepted** | **match — and the connector is side-agnostic** |
| Tail width | 25.5 ± 0.15 mm | 50-pos body accepts the standard 0.5 mm tail | **match** |
| Plating | not stated by S1 | gold plating recommended | **confirm on first article (B-31)** |

> **The single most common cause of a dead first-article display — an FPC whose
> contacts face the wrong way — cannot occur with this pair.** FH69 is the
> industry's first top-and-bottom 2-point contact design; it mates a
> bottom-contact tail and a top-contact tail equally. That property is worth more
> than the ~US$0.60 premium over a single-sided part, and it is why FH69 is
> selected over the otherwise adequate FH12 / FH52E.

### 4.3 Availability

| channel | status |
|---|---|
| Digi-Key `FH69-50S-0.5SH` | **1,907 in stock**, **US$2.16 @ 1**, **US$1.56 @ 100**, **MOQ 1**, lifecycle **Active** (S5) |
| Second source, same 0.5 mm / 50-pos class | **Hirose `FH52E-50S-0.5SH`** — 0.5 mm pitch, 2.0 mm height, **bottom contact**, front flip, **0.3 ± 0.05 mm FPC**, −40…+105 °C (S4) |
| **JLCPCB / LCSC** | **`FH52E-50S-0.5SH` = `C7465440`**, HRS, SMD-50, **Extended** part, RoHS, MSL 1 — available for JLCPCB PCBA |

`FH69-50S-0.5SH` itself was **not** found in the LCSC / JLCPCB catalogue. That is
the reason the second source matters and the reason for the land-pattern ruling
below.

### 4.4 Land-pattern ruling

Two patterns are possible and they are **not** interchangeable in both directions:

- **FH69's dedicated pattern** — what `AQROOT_Beta:Hirose_FH69-50S-0.5SH` on
  Beta-DM implements (50 pads, 0.300 x 1.230 mm, 0.5 mm pitch, measured in S7).
  FH52E does **not** fit it.
- **The FH12-horizontal / FH52E standard pattern** — signal pads 0.3 ± 0.03 mm
  wide on 0.5 ± 0.05 mm pitch (S4). Hirose states **FH69 also fits this pattern**
  (S3).

> **Ruling: lay `J1` out on the FH12-horizontal / FH52E-50S-0.5SH standard land
> pattern.** Fit **FH69-50S-0.5SH** as the primary part; **FH52E-50S-0.5SH
> (LCSC C7465440)** is then a genuine drop-in second source and a JLCPCB-assembly
> path, with **no board change**. This is exactly the D-049 posture: a
> configuration change recoverable by component substitution rather than by a
> respin.
>
> The Beta-DM FH69-dedicated footprint is **retained in the library** but is not
> the v2 footprint. Both connectors' land patterns must be re-verified with a
> per-footprint pad-overlap assertion at **FBV2-S2** (**B-29**).

---

## 5. Pinout and electrical migration into AQROOT

### 5.1 Signal map — no new native GPIO

Existing assignments are measured from S8. Panel pin numbers are from S1 §4.1.

| function | panel pin | AQROOT net | resource | change |
|---|---|---|---|---|
| SPI-A SCK | **36** WRX(SCL) | `SPI_A_SCK` | **GPIO12** (FSPI IO_MUX) | none |
| SPI-A MOSI | **34** SDA | `SPI_A_MOSI` | **GPIO11** (FSPI IO_MUX) | none |
| SPI-A MISO | **33** SDO | `SPI_A_MISO` | **GPIO13** (FSPI IO_MUX) | **fit a 0 R isolation link — see §5.3** |
| Display CS | **38** CSX | `DISP_CS_N` | **GPIO10** | none |
| Display D/C | **37** D/CX | `DISP_DC` | **GPIO14** | none |
| Display RESET | **10** RESET | `DISP_RST_N` | **expander U60 P04** | none |
| Backlight PWM | — (driver CTRL) | `DISP_BL_CTL` | **GPIO47** | none |
| Touch SCL | **44** | `I2C_SCL_INT` | **GPIO2** | none |
| Touch SDA | **45** | `I2C_SDA_INT` | **GPIO1** | none |
| Touch INT | **46** IRQ | `TOUCH_INT_N` | **polled today**; optionally a spare expander input | none |
| Touch RESET | **47** RST | `TOUCH_RST_N` | **expander U60 P00** | none |
| Interface strap | **7, 8, 9** IM0/1/2 | tie to VDDI = `+3V3` | **passive** | new, no GPIO |
| VDDI | **40, 41** | `+3V3` | rail | none |
| VCI | **42** | `+3V3` | rail | none |
| GND | **43, 48, 49, 50** | `GND` | rail | none |
| Backlight anode | **1** LEDA | `LED_A` (single net) | — | **was 4 nets `LED_A1..A4`** |
| Backlight cathode | **2, 3** LEDK | `LED_K` | — | none |
| Unused | 4–6 NC, 11–14 RGB sync, 15–32 DB17–DB0, 35 RD, 39 TE | per S1: RGB sync and DB to **GND**, RD to **VDDI**, TE **open** | passive | new |

**Result: zero new native GPIO.** B-10 (zero free native GPIO) is unaffected. The
touch controller is the **same FT6236 at the same address 0x38** already reserved
in the I2C address table, so the touch driver, the reserved-address ruling and the
`TOUCH_RST_N` enumeration pulse all carry over unchanged.

**No new voltage rail. No level shifting.** Every panel input is 3.3 V-compatible
and every panel output swings to VDDI = 3.3 V.

**SPI-A architecture is unchanged** — display + microSD on SPI-A, radios and NFC
on SPI-B. **No bus merge.**

### 5.2 Net-level changes to sheet `03_spi_a_display_sd`

| change | reason |
|---|---|
| `LED_A1`, `LED_A2`, `LED_A3`, `LED_A4` collapse to a **single `LED_A`** | the panel has one anode pin, not four |
| `IM0/IM1/IM2` tied to `+3V3` | selects 4-wire 8-bit SPI |
| RGB-mode pins tied off per S1 | VSYNC / HSYNC / DOTCLK / DE and DB17–DB0 to GND, RD to VDDI |
| `TE` left open | not used |
| `R69`, `R70`–`R73` re-valued | §6 |
| `J1` footprint changed to the FH12 / FH52E standard pattern | §4.4 |

### 5.3 The one electrical caution — ILI9488 `SDO` on a shared bus

SPI-A is shared with microSD. S1 describes pin 33 as *"Serial Output Signal.
Leave the pin open when not in use."* The datasheet does not state the SDO
output's high-impedance behaviour while `CSX` is high, and ILI9488 modules have a
field reputation for holding SDO driven.

**Mitigation, D-049-compliant, costing one 0402 pad:** fit a **0 R series link
`R_SDO`** between panel pin 33 and `SPI_A_MISO`, with the panel side also brought
to a test point. If bring-up shows SDO contending with the microSD, the link is
removed and the display becomes write-only — which AQROOT's driver does not need
— **without a respin, a trace cut or a bodge**. Recorded as **B-28**, closed at
FBV2-B2.

---

## 6. Backlight closeout — M-07

### 6.1 What changed

| | Beta-DM (measured, S7) | Full Beta v2 (S1 §4.4) |
|---|---|---|
| LEDs | **4 in parallel**, 4 separate anodes `LED_A1..A4`, common cathode | **6 in parallel**, **one** anode, common cathode |
| Panel pins | `J1.1` K, `J1.2–5` A1–A4 | `1` LEDA, `2` + `3` LEDK |
| Vf | 2.9 – 3.4 V per LED | **2.9 – 3.2 V** |
| Rated current | 4 x 20 mA = 80 mA | **120 mA max**, **90 mA** life point |
| Ballast | `R70`–`R73` = 4 x **39 R**, one per anode | **one node** — ballasting is now a single lumped resistance |
| Sense | `R69` = **2.55 R** | must be re-derived |

### 6.2 Verdict on the driver

> ### **TPS61169DCKR (`U17`) REMAINS. No replacement architecture is needed.**

The reason is structural, not incidental: **`U17` boosts from `+3V3`, not from the
battery** (S7 §1.1 — pin 5 `VIN` = `+3V3`). A boost cannot regulate below its own
input, and a 6-LED *parallel* array sits at only ~3.0–3.2 V. Had the driver been
fed from `VSYS` (3.0–4.35 V) this panel would have forced a buck-boost or a linear
sink. Fed from a fixed 3.3 V, a modest ballast lifts the output to ~4.15 V and the
converter stays firmly in boost across every corner. **The existing topology is
the right one for this panel by construction.**

TPS61169 key parameters (S6, cross-checked against S7): `VREF` **188 / 204 /
220 mV**; switch peak current limit **1.2 A minimum**; integrated **40 V / 1.8 A**
FET; `VOVP_SW` **36 / 37.5 / 39 V**; `VIN` 2.7–5.5 V.

### 6.3 New values

**Sense resistor `R69` (the "RSET"):**

```
R69 = VREF / I_LED
```

| choice | R69 | I_LED typ | I_LED over the VREF band | per LED | note |
|---|---|---|---|---|---|
| **Selected** | **1.87 R ±1 % (E96, 0603)** | **109 mA** | **100.5 – 117.6 mA** | 18.2 mA | worst case stays **under the panel's 120 mA maximum** |
| Alternative fit | 2.26 R ±1 % | 90 mA | 83.2 – 97.3 mA | 15.0 mA | pins the design to the vendor's 30 000 h life point |
| *Beta-DM, for reference* | *2.55 R* | *80 mA* | *73.7 – 86.3 mA* | *20.0 mA* | |

**1.87 R is selected** because it makes the panel's own maximum reachable while
guaranteeing it is never exceeded — the tolerance band tops out at 117.6 mA
against a 120 mA limit. Normal brightness is then set **in firmware** by PWM on
`CTRL` (`DISP_BL_CTL`, GPIO47), with the default duty chosen to land near the
90 mA life point. `R69` = 2.26 R remains a one-resistor swap if a hard 90 mA
ceiling is preferred. Worst-case dissipation 26 mW — 0603 is ample.

**Ballast `R70`–`R73`:** the four ballast footprints are **retained and
repurposed**. All four are tied to the single `LED_A` net, in parallel:

```
R70 = R71 = R72 = R73 = 33 R   ->   R_BAL = 8.25 R
```

| | value |
|---|---|
| Ballast drop at 109 mA | 0.899 V |
| `LED_BOOST` worst-low (Vf 2.9 V, I 100.5 mA, VREF 188 mV) | **3.917 V** |
| `LED_BOOST` nominal | **4.153 V** |
| `LED_BOOST` worst-high (Vf 3.2 V, I 117.6 mA, VREF 220 mV) | **4.390 V** |
| `+3V3` input, ±2 % | 3.234 – 3.366 V |
| **Minimum boost ratio** | **3.917 / 3.366 = 1.16** — never leaves regulation |
| Current per ballast resistor | 27.3 mA |
| Dissipation per ballast resistor | **24.6 mW** in an 0603 rated 100 mW — **4x** |
| Total ballast loss | 98 mW |

Keeping four resistors instead of one is deliberate: it reuses the existing
footprint group, quarters the per-part dissipation, and leaves three DNP-able trim
steps (8.25 → 11.0 → 16.5 → 33 R) available as pure component rework.

### 6.4 Margin verification

Worst case: `Vout` 4.390 V, `Iout` 117.6 mA, `Vin` 3.234 V, eta 0.85, `L3` 4.7 uH,
`fSW` 1.2 MHz.

| check | figure | limit | margin |
|---|---|---|---|
| Duty cycle | D = 1 − 3.234/4.390 = **0.263** | — | comfortable |
| Average inductor current | **188 mA** | — | — |
| Inductor ripple | 151 mA p-p | — | — |
| **Peak switch current** | **263 mA** | **1.2 A minimum limit** | **4.6x** PASS |
| **`L3` XFL4020-472MEC** (4.7 uH, Isat ~3.3 A) | 263 mA peak | 3.3 A | **12.5x** PASS — **unchanged** |
| **`D8` NSR0240** (40 V Schottky, SOD-323) | 118 mA average, 263 mA peak | 250 mA I_F(AV) | **2.1x** PASS — **retained** |
| **`C44`** 1 uF 50 V X7R | rating set by `VOVP_SW` 39 V worst case | 50 V | **1.28x** PASS — **unchanged** |
| Output ripple | 28.6 mV p-p | — | acceptable |
| **`U17` output** in normal operation | 3.92 – 4.39 V | 38 V recommended max | PASS |

**`D8` is the tightest item at 2.1x** (it was 3.1x at Beta-DM's 80 mA). It is
retained. A same-footprint uprate to a 0.5 A SOD-323 Schottky (PMEG4005EJ class)
is **recommended, not required**, and is a BOM change with no layout impact.

**Input decoupling:** input ripple current rises ~47 % against Beta-DM. Confirm
>= 4.7 uF X5R local to `U17` `VIN` during schematic capture (**B-32**).

### 6.5 Power and runtime

| condition | `LED_BOOST` x I | out of `U17` | from `+3V3` (eta 0.85) | from the pack (eta 0.90 through TPS63020) |
|---|---|---|---|---|
| *Beta-DM, 4 LED @ 80 mA* | *4.18 V x 80 mA* | *0.334 W* | *0.393 W → 119 mA* | *0.437 W → **118 mA at 3.7 V*** |
| **v2 default (90 mA via PWM)** | 4.06 V x 90 mA | 0.365 W | 0.430 W → 130 mA | 0.478 W → **129 mA at 3.7 V** |
| **v2 maximum (109 mA)** | 4.15 V x 109 mA | 0.452 W | 0.532 W → 161 mA | 0.591 W → **160 mA at 3.7 V** |

**At the default brightness the backlight costs +11 mA at the pack — about +9 % —
for 1.56x the screen area and 2x the pixels.** Per-LED current actually *falls*
from 20 mA to 15 mA, which is why LED life improves rather than degrades.

This corrects FBV2-DISP-001's estimate, which assumed 6 x 20 mA = 120 mA and
predicted roughly +50 %. That estimate was made before the panel's own backlight
table was available; the real part is specified at a lower per-chip current.

Full power-budget re-derivation stays a schematic-phase task — the browsing-current
figure in `13 - Power Budget and Battery Runtime v0.1` predates several other v2
changes and should not be patched piecemeal here.

> **M-07 is CLOSED.**

---

## 7. Mechanical check

Against the FBV2-A2 spec (`mechanical/MECHANICAL_INTERFACE_SPEC.md`).

### 7.1 Envelope

| check | requirement | actual | margin | verdict |
|---|---|---|---|---|
| Module width | <= 60 mm | **56.54 mm** | 3.46 mm | **PASS** |
| Module height | <= 90 mm | **84.96 mm** | 5.04 mm | **PASS** |
| Module thickness | <= 4.5 mm | **3.95 ± 0.25 → 4.20 mm max** | 0.30 mm | **PASS** |
| Width in the 75 mm cavity | — | 56.54 → **9.23 mm each side** | — | **PASS** |
| Height in the 155 mm cavity | — | 84.96 → **70.04 mm remaining** | — | **PASS** |
| Width on the 70 mm PCB | — | 56.54 → **6.73 mm each side** | — | **PASS** |

### 7.2 Z column

| element | mm |
|---|---|
| Front bezel / cover allowance | 1.00 |
| **Display module (max tolerance)** | **4.20** |
| Air / adhesive gap to PCB | 0.50 |
| PCB | 1.60 |
| **Front stack subtotal** | **7.30** |
| Battery behind the PCB (D-071) | 8.00 |
| **Total** | **15.30** |
| **Internal cavity depth** | **18.50** |
| **Spare** | **3.20 mm** |

**PASS.**

### 7.3 FPC exit, bend and connector placement

| item | figure | note |
|---|---|---|
| Tail width | 25.5 ± 0.15 mm | centred on the panel's lower edge |
| Tail thickness | 0.30 ± 0.03 mm | |
| Tail free length | 30 ± 0.5 mm | ample for a fold behind the panel or a same-side entry |
| **Minimum bend radius** | **>= 3.0 mm** budgeted (10 x thickness, the conservative static-bend rule) | the previously reserved **6 mm bend corridor** is retained and is now known to be generous |
| Connector body length, 50 pos | ~29.98 mm | fits within the 56.54 mm panel width |
| Connector height | 2.3 mm | |
| Connector orientation | **right-angle, horizontal FPC entry** | the tail runs parallel to the board, which is what a folded-behind panel wants |
| Placement | below the display shadow, actuator facing away from the panel | required so the backflip actuator is reachable for assembly and rework |

**One placement constraint to carry into FBV2-P1:** the display-shadow component
height limit is **0.8 mm** (measured Beta-DM limit). A 2.3 mm connector **cannot**
sit under the panel. It must be placed in the 70.04 mm of cavity height below the
panel, which is also where the D-pad, A/B and the mic aperture live. There is
room, but it is a real placement coupling and it is recorded as **B-33**.

### 7.4 Controls and acoustics

70.04 mm of cavity height remains below the display for the D-pad, A, B and the
microphone aperture — identical to the figure FBV2-DISP-001 derived, because the
selected panel's glass is dimensionally the same as the candidate it replaces.
**No change to the front-face layout ruling (D-070).**

---

## 8. Procurement and no-respin risk

| risk | level | evidence and mitigation |
|---|---|---|
| **Discontinuation** | **LOW** | EastRising publishes a written commitment: *"long term continuity supply … no less than 10 years since 2023"* for `ER-TFT035IPS-6` and *"since 2015"* for `ER-TPC035-6`. No other candidate in the survey offers a written continuity term |
| **MOQ** | **LOW** | **MOQ 1**, in stock, tiered pricing from 10 pcs. Five prototype units are an ordinary order, not a sample request |
| **Documentation ambiguity** | **LOW** | 24-page datasheet Rev 2.0 (18-Aug-2025) with a complete pin table, three outline drawings, FPC construction and a backlight table, plus ILI9488 and FT6236 datasheets, a connector drawing, a STEP model and ESP32 example code. One residual gap (§3.5), immaterial to this design |
| **Connector sourcing** | **LOW** | FH69-50S-0.5SH: **Active**, 1,907 in stock at Digi-Key, MOQ 1. Second source FH52E-50S-0.5SH on the same land pattern, **available through JLCPCB as C7465440** |
| **Touch-controller substitution** | **MEDIUM** | The vendor also sells a **CST340** capacitive panel for this size. The purchase order must name **`ER-TPC035-6`** explicitly. *Partial mitigation:* the shipped datasheet covers **FT6236 / FT6336 / FT6436L / FT6436** as one family — they share **address 0x38** and the register map, so an in-family substitution is firmware-transparent |
| **Silent vendor revision** | **MEDIUM-LOW** | The datasheet itself carries revision **B, "Backlight Update", Aug-18-2025**, which proves revisions happen and that the backlight is what changes. *Mitigation:* Rev 2.0 must be **archived in-repo** and cited by revision in the MPN ledger, and the backlight table re-confirmed at PO |
| **Optical regression** | **LOW** | IPS, 80/80/80/80, 500:1, 300 cd/m2 — better than the 2.8" incumbent on every axis |
| **SPI bandwidth** | **MEDIUM, quantified** | +50 % traffic versus an ST7796S that does not exist in a usable module. See §2.2. Managed by LVGL partial refresh and CS discipline; validated at FBV2-B2 |

> **Overall procurement risk: LOW, with two MEDIUM items that are both closed by
> writing exact MPNs and a document revision onto the purchase order** rather than
> by any design change.

### 8.1 Cost

| line | 5 pcs (prototype) | 100 pcs |
|---|---|---|
| `ER-TFT035IPS-6` | US$9.34 | US$8.34 |
| `ER-TPC035-6` capacitive touch | US$6.23 | US$5.57 |
| **Display subtotal** | **US$15.57** | **US$13.91** |
| `FH69-50S-0.5SH` | US$2.16 | US$1.56 |
| **Per-unit total** | **US$17.73** | **US$15.47** |

The brief asked to prefer a slightly higher unit cost where it materially reduces
first-board respin risk. **It did not come to that** — the selected part is also
among the cheapest examined (Riverdi US$28.49, DisplayModule US$39.90, Focus
US$109.13).

---

## 9. Gate assessment — FBV2-DISP-LOCK

| # | condition | status |
|---|---|---|
| 1 | Exact display MPN chosen | **YES** — `ER-TFT035IPS-6` + `ER-TPC035-6` |
| 2 | Complete datasheet available | **YES** — Rev 2.0, 24 pp, retrieved and extracted in full |
| 3 | Exact FPC geometry known | **YES** — 50 pin · **0.50 mm** · **bottom contact** · **0.30 ± 0.03 mm** · 25.5 ± 0.15 mm wide |
| 4 | Exact touch controller known | **YES** — **FT6236**, I2C, **0x38**, with its own datasheet |
| 5 | Exact mating connector proven | **YES** — `FH69-50S-0.5SH`, proven from **both** manufacturers' drawings (§4.2), not from pin count |
| 6 | SPI architecture passes | **YES** — 4-wire SPI on the existing FSPI IO_MUX pins, **no new native GPIO**, no bus merge (§5) |
| 7 | Backlight architecture resolved | **YES** — `U17` retained, `R69` = 1.87 R, `R70`–`R73` = 4 x 33 R, all margins verified (§6) |
| 8 | Physical fit confirmed | **YES** — 56.54 x 84.96 x 4.20 max inside 60 x 90 x 4.5; 3.20 mm Z spare (§7) |
| 9 | Reasonable sourcing path | **YES** — MOQ 1, in stock, written >=10-year continuity, dual-sourced connector (§8) |

> ### **FBV2-DISP-LOCK = PASS.** **M-06 CLOSED. M-07 CLOSED.**
> **Sheet `03_spi_a_display_sd` is unblocked. FBV2-S1 has no remaining display gate.**

---

## 10. Open items created or changed

| # | item | severity | closes at |
|---|---|---|---|
| **B-28** | **ILI9488 `SDO` shared-bus behaviour unverified.** Fit a 0 R `R_SDO` isolation link + test point | LOW — mitigated by design | FBV2-B2 bench |
| **B-29** | **`J1` footprint must be redrawn** on the FH12-horizontal / FH52E standard land pattern and verified with a per-footprint pad-overlap assertion against **both** connector drawings | MEDIUM — layout work | FBV2-S2 |
| **B-30** | Which FPC pin supplies the FT6236 VDD is not stated (§3.5). Immaterial — VDDI, VCI and CTP VDD are all `+3V3` here | INFORMATIONAL | first article |
| **B-31** | Display FPC contact plating not stated by S1; Hirose recommends gold | LOW | PO / first article |
| **B-32** | Confirm >= 4.7 uF X5R input decoupling local to `U17` `VIN` (ripple current +47 %) | LOW | FBV2-S1 |
| **B-33** | **The 2.3 mm connector cannot sit in the display shadow** (0.8 mm limit). It competes for the 70.04 mm below the panel with the D-pad, A/B and the mic aperture | MEDIUM — placement coupling | FBV2-P1 |
| ~~**M-06**~~ | Display MPN and FPC interface | **CLOSED** | this audit |
| ~~**M-07**~~ | Backlight driver re-derivation | **CLOSED** | this audit |

---

## 11. Honest limitations

1. **The two drawings agree on paper. Nothing has been mated.** Paper
   compatibility that names pitch, thickness and contact side from both sides is
   the strongest pre-hardware evidence obtainable, and it is materially stronger
   than anything J1 ever had before — but it is not a mated sample. The first
   article remains the proof.
2. **The 30 000-hour LED life figure is the vendor's**, at 90 mA and 25 °C. No
   independent corroboration was sought.
3. **The efficiency figures in §6.5 use eta = 0.85 for the boost and eta = 0.90 for
   the TPS63020.** Neither was measured; both are conventional for these parts at
   these currents. The *relative* comparison to Beta-DM is more reliable than the
   absolute milliamps.
4. **`fSW` = 1.2 MHz** is used for the ripple and peak-current arithmetic. If the
   TPS61169's actual switching frequency at this operating point differs, the peak
   current moves — but at 4.6x margin the conclusion is insensitive to it.
5. **The Chenghao / EastRising same-glass conclusion in §2.3 is an inference** from
   identical outline dimensions, active area and backlight configuration. It is
   plausible and useful, and it is not proven.
6. **Focus LCDs, Winstar and Raystar were assessed from their published product
   data**, not from a sales conversation. A custom-CTP request to any of them
   could produce a compliant part; that path was not pursued because it converts a
   catalogue purchase into an NRE-bearing custom programme.
7. **No purchase was made and no vendor was contacted.** Prices and stock are as
   published at the time of the audit.

---

## Sources

- EastRising **`ER-TFT035IPS-6`** — [datasheet Rev 2.0 (PDF)](https://www.buydisplay.com/download/manual/ER-TFT035IPS-6_Datasheet.pdf) · [product record](https://www.buydisplay.com/3-5-inch-ips-320x480-tft-lcd-display-capacitive-touch-screen)
- EastRising **`ER-TPC035-6`** — [product record](https://www.buydisplay.com/3-5-inch-capacitive-touch-panel-wiith-controller-ft6236-for-320x480-dots) · [outline drawing](https://www.buydisplay.com/download/manual/ER-TPC035-6_Drawing.pdf) · [FT6236 / FT6336 / FT6436 datasheet](https://www.buydisplay.com/download/ic/FT6236-FT6336-FT6436L-FT6436_Datasheet.pdf)
- EastRising **`ER-TFT035-6`** (fallback) — [product record](https://www.buydisplay.com/serial-spi-3-5-inch-tft-lcd-module-in-320x480-optl-touchscreen-ili9488)
- **ILI9488** — [datasheet](https://www.buydisplay.com/download/ic/ILI9488.pdf)
- Hirose **`FH69`** — [series catalogue](https://www.hirose.com/en/product/document?series=FH69&documenttype=Catalog&lang=en&documentid=en_FH69_CAT) · [product page](https://www.hirose.com/en/product/p/CL0580-5008-0-00) · [Digi-Key `FH69-50S-0.5SH`](https://www.digikey.com/en/products/detail/hirose-electric-co-ltd/FH69-50S-0-5SH/23568785)
- Hirose **`FH52`** — [series catalogue](https://www.hirose.com/en/product/document?clcode=&documentid=en_FH52_CAT&documenttype=Catalog&lang=en&productname=&series=FH52) · [JLCPCB `FH52E-50S-0.5SH` = C7465440](https://jlcpcb.com/partdetail/HRS-FH52E_50S_05SH/C7465440)
- TI **`TPS61169`** — [product page / SNVSA40B](https://www.ti.com/product/TPS61169)
- Rejected candidates — Riverdi [`RVT35HITNWC00-B`](https://riverdi.com/product/rvt35hitnwc00-b) · Focus LCDs [`E35RG13248LW2M450-CA`](https://focuslcds.com/product/e35rg13248lw2m450-ca/) and [`E35RG73248LW6M250-C` spec](https://focuslcds.com/content/E35RG73248LW6M250-C_Spec.pdf) · Winstar [`WF35UTYAIDNN0`](https://www.winstar.com.tw/products/tft-lcd/ips-tft/3_5.html) · Raystar [`RFI350U-AYW-DNN`](https://www.raystar-optronics.com/3.2-3.5-3.9-tft-lcd-display/320x480-tft.html) · VIEWE [`UE035HV-RB40-A118`](https://viewedisplay.com/product/3-5-inch-320x480-ips-tft-lcd-display-module-with-capacitive-touch/) · DisplayModule [`DM-TFT35-431`](https://www.displaymodule.com/products/3-5-ips-display-320x480-spi-mcu-rgb) · Newhaven [3.5" IPS line](https://newhavendisplay.com/tft-displays/ips-displays/)
- Read only, in-repo: `hardware/beta-dm/BETA-DM-BACKLIGHT-ANALYSIS.md` · `11 - Beta Pin Map v0.2.md` · `01 - Hardware Core.md`
