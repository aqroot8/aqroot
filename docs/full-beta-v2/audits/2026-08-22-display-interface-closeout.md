# AQROOT Full Beta v2 — Display and FPC Interface Closeout

Date: 2026-08-22
Task: **FBV2-DISP-001**
Repository HEAD at audit: `6525ec7`
Scope: **documentation only.** No KiCad, PCB, firmware or fabrication file was created or modified. `hardware/beta-v2/` was not created.

---

## 0. Sources

| # | source | weight |
|---|---|---|
| **D1** | Chenghao **CH350HV40A-CT** product specification PDF (`chenghaolcd.com`, "3.5 inch 320x480 IPS TFT Display Module with Capacitive Touch Panel") | **Primary vendor document**, retrieved and text-extracted |
| **D2** | Chenghao **CH280QV10-CT** listing data (made-in-china / chenghaolcd) | Vendor listing, **not a full spec PDF** |
| **D3** | ILI9488 datasheet + multiple independent driver/library sources on the SPI colour-depth limitation | Corroborated across a datasheet mirror and several implementations |
| **D4** | `hardware/beta/mechanical/reports/PHASE-1-MECHANICAL-AUDIT.md` (read only) | **Measured** — Beta-DM display keepout 50 × 69 mm |
| **D5** | `01 - Hardware Core.md` | J1 = Hirose FH69-50S-0.5SH, footprint VERIFIED_VENDOR_EXACT |

---

## 1. CTO rulings recorded

| ruling | recorded as |
|---|---|
| Battery envelope **LOCKED** at 60 × 75 × 8.0 mm, ~2500–3000 mAh | **D-071** |
| Display size target **3.5 inch** | **D-072** |
| **Do not blindly reuse** CH280QV10-CT or J1 FH69-50S-0.5SH | **D-073** |

---

## 2. The candidate — CH350HV40A-CT, verified from the vendor document

| parameter | value | source |
|---|---|---|
| Model | **CH350HV40A-CT** | D1 |
| Size / type | 3.5 in, **IPS**, transmissive, normally black | D1 |
| Resolution | **320 × 480** | D1 |
| **TFT driver IC** | **ILI9488** | D1 |
| **Module outline** | **56.54 (W) × 84.96 (H) × 3.97 (T) mm** | D1 |
| Active area | **48.96 × 73.44 mm** | D1 |
| Dot pitch | 0.153 × 0.153 mm | D1 |
| Luminance / contrast | 300 cd/m², 800:1 | D1 |
| Viewing angle | 80/80/80/80 | D1 |
| **FPC pin count** | **50 pins** | D1 |
| **FPC pin pitch** | **"0.3 ~ 0.4 mm"** | D1 |
| Input voltage | 3.2 V | D1 |
| **Backlight** | **6 LED parallel**, white | D1 |
| Interfaces | 4-line 8-bit SPI, 3-line 9-bit SPI, 8080 8/9/16/18-bit, SPI+RGB 16/18-bit | D1 |
| Touch | Capacitive (or resistive, optional) | D1 |
| Temperature | −20…+70 °C operating | D1 |

### 2.1 Physical fit — PASS

| check | requirement | actual | verdict |
|---|---|---|---|
| Module envelope | ≤ 60 × 90 mm | **56.54 × 84.96** | **PASS** |
| Thickness | ≤ 4.5 mm | **3.97** | **PASS** |
| Width in cavity (75 mm) | — | 56.54, **9.2 mm each side** | **PASS** |
| Height in cavity (155 mm) | — | 84.96, leaves **70 mm** for the control area | **PASS** |
| Display Z column | 23 mm budget | 12.9 mm (was 11.8 with the 2.9 mm assumption) | **PASS**, large margin |
| Battery envelope conflict | — | **None.** The battery sits behind the PCB; the display is in front of it | **PASS** |

**D-071's battery envelope survives the 3.5″ ruling unchanged.** The larger display
consumes front area, not rear volume, and the rear is where the battery lives.

---

## 3. Four defects that prevent locking this part

Each is a documentation or architecture problem, not an opinion.

### 3.1 ILI9488 cannot send RGB565 over SPI — 1.5× bandwidth

This is a **controller** limitation, not a vendor one, and it is corroborated
across the datasheet and multiple independent implementations (D3):

> The ILI9488 datasheet documents 18-bit/pixel (RGB 6-6-6) for the SPI serial
> interface and 16-bit/pixel (RGB 5-6-5) only for the parallel data bus. In
> practice the serial interface accepts **3 bytes per pixel**, not 2.

| | 2.8″ 240×320, ILI9341 RGB565 | 3.5″ 320×480, **ILI9488 RGB666** | 3.5″ 320×480, **ST7796S RGB565** |
|---|---|---|---|
| Pixels | 76,800 | 153,600 | 153,600 |
| Bytes per full frame | 153,600 | **460,800** | **307,200** |
| Full frame @ 40 MHz | 31 ms (32 fps) | **92 ms (11 fps)** | 61 ms (16 fps) |
| Full frame @ 80 MHz | 15 ms | **46 ms (22 fps)** | **31 ms (33 fps)** |

**An ST7796S-class controller costs 33% less bus traffic for the same panel.**
On a bus that is already shared with the microSD card, that is not a rounding
error.

### 3.2 The FPC pitch is stated as a **range**

D1 gives **"Pin pitch: 0.3 ~ 0.4 mm."** A connector pitch is not a range — it is
0.3 mm, or 0.4 mm, or 0.5 mm. A specification that cannot state its own pitch
cannot be designed against, and it directly violates the standing no-respin
policy (D-049), which requires **"no dependence on undocumented pin pitch."**

**This single line is the reason the display MPN cannot be locked today.**

### 3.3 The module thickness is internally inconsistent

The same document states **3.97 mm** in the parameter table and **2.4 mm** in the
Quick Detail section. Most likely one is the TFT-only stack and the other the full
module with CTP, but the document does not say which. The mechanical spec uses
the larger figure.

### 3.4 The touch controller is not identified

D1 says "Capacitive / Resistive Touch Panel (Optional)" and never names the CTP
IC. AQROOT needs an **I²C** touch controller with a known address and a known
reset/interrupt contract — the FT6236 on the 2.8″ part was a known quantity at
0x38, and the reserved-address table depends on knowing it.

---

## 4. Was the old J1 actually compatible with CH280QV10-CT?

### VERDICT: **UNPROVEN.**

| item | evidence |
|---|---|
| J1 fitted | **Hirose FH69-50S-0.5SH**, 50-pin, **0.5 mm pitch**, footprint VERIFIED_VENDOR_EXACT (D5) |
| CH280QV10-CT outline | 50.0 × 69.2 × 4.0 mm, active 43.2 × 57.6, ILI9341, **FT6236** CTP, 50-pin (D2) |
| Beta-DM measured keepout | **50 × 69 mm** (D4) — corroborates the outline exactly |
| **CH280QV10-CT FPC pitch** | **NOT STATED in any source obtained** |

**No document available to this audit states the 2.8″ module's FPC pitch.** The
Phase-1 mechanical audit independently recorded the same gap: *"Exact
CH280QV10-CT panel outline, thickness, active area, and FPC bend stack are not
archived locally."*

So the honest answer is neither YES nor NO. **The connector was selected without
a display FPC drawing on file**, and it has never been proven to mate. The
footprint is verified against the *Hirose* drawing — which proves the connector
footprint is right, and proves nothing about the display.

**The CTO's suspicion is well founded**, and this audit strengthens it: the
successor part in the same family quotes 0.3–0.4 mm, not 0.5 mm. If the family
convention is sub-0.5 mm, the 2.8″ part may never have mated either.

---

## 5. ESP32-S3 / SPI verdict — **PASS**

### 5.1 No bus merge and no radio change is required

- **SPI-A** carries display + microSD. **SPI-B** carries CC1101 + SX1262 + NFC.
  The 3.5″ panel touches **only SPI-A**. The radio architecture is untouched.
- **SPI-A sits on the ESP32-S3 FSPI IO_MUX pins.** The measured map is
  `SPI_A_MOSI` = GPIO11, `SPI_A_SCK` = GPIO12, `SPI_A_MISO` = GPIO13,
  `DISP_CS` = GPIO10 — these are exactly the FSPI IO_MUX assignments.
  **That matters:** IO_MUX-routed SPI reaches **80 MHz**, whereas GPIO-matrix
  routing is limited to ~40 MHz. The display bus already has the fast path.
- At 80 MHz with an ST7796S-class controller, a full 320×480 RGB565 frame is
  **~31 ms** — the same as the 2.8″ panel at 40 MHz today. **The user experience
  does not regress.**

### 5.2 Why this is comfortable for AQROOT's actual UI

The brief is explicit: menus, touch UI, graphs, logs, status screens — **not**
high-frame-rate video. With LVGL dirty-rectangle rendering, full-screen writes
occur only on screen transitions; ordinary interaction repaints small regions.
The N16R8's **8 MB PSRAM** comfortably holds a full 307 kB frame buffer plus
double-buffering.

### 5.3 The one real contention to manage

Display refresh and microSD share SPI-A, and the 3.5″ panel **doubles the pixel
count**, so it doubles the contention. This was already an open Beta-DM item
(*"this shared-bus config was NOT tested in Alpha — validate on Beta"*). It is a
firmware scheduling matter — hold the idle device's CS high, mutex the bus, avoid
simultaneous DMA — not an architecture change.

**Verdict: PASS.** 320×480 SPI is acceptable on this architecture, **provided an
ST7796S-class controller is chosen.** With ILI9488 it still works, at 22 fps
full-frame instead of 33.

---

## 6. Backlight power impact

| | 2.8″ CH280QV10-CT | 3.5″ CH350HV40A-CT |
|---|---|---|
| LED configuration | **4 strings**, 39R ballasts, RSET 2.55R (measured, Beta-DM) | **6 LED parallel** (D1) |
| LED count | 4 | **6 (+50%)** |
| LED current @ 20 mA each | 80 mA | **120 mA** |
| Approx. 3.3 V rail draw | ~120 mA | **~180 mA** |

**Two consequences:**

1. **Runtime.** The backlight was already the dominant continuous load (~60 mA of
   the ~100 mA browsing figure). Browsing draw rises to roughly **~130 mA**.
   **However**, D-071 raises the pack from the 2000 mAh assumed in the power budget
   to the **2500–3000 mAh** class — so net runtime is **flat to slightly better**
   (≈20 h → ≈21 h at 2750 mAh). The two rulings offset each other, which is worth
   recording because neither alone would have.
2. **The backlight driver must be re-derived.** `RSET` = 2.55R on Beta-DM sets the
   total LED current through the TPS61169's feedback sense. Six LEDs at 20 mA
   requires a different `RSET`, and **the TPS61169's switch-current capability at
   the higher total must be re-verified**. The Beta-DM anode arrangement
   (`LED_A1..A4` + `LED_K`) also assumes four accessible anodes; a six-LED panel
   may present a different pin arrangement. **Both are gated on the full pin
   table.**

---

## 7. Comparison against the incumbent

| dimension | CH280QV10-CT (2.8″) | CH350HV40A-CT (3.5″) | assessment |
|---|---|---|---|
| Electrical complexity | ILI9341 + FT6236, both known | ILI9488 + unnamed CTP | **Worse** — CTP unidentified |
| SPI bandwidth / load | 153.6 kB/frame | 460.8 kB/frame (RGB666) | **1.5–3× worse**; ST7796S would make it 2× |
| Backlight power | 4 LEDs | 6 LEDs, +50 % | **Worse**, offset by the larger battery |
| Firmware impact | Existing ILI9341 + FT6236 path | New driver, new colour depth, new CTP driver | **Moderate rework** |
| Physical fit | 50 × 69.2 × 4.0 | 56.54 × 84.96 × 3.97 | **Both fit**; 3.5″ has 1.56× the area |
| Visual / UI benefit | 240×320 | **320×480 — 2× the pixels, 1.56× the area** | **Substantially better** for graphs, logs and touch targets |
| Sourcing risk | Same vendor, same gap | Same vendor, **worse documentation** | **Worse** |

**The UI benefit is real and is the reason to proceed.** The sourcing and
documentation risk is also real and is the reason not to lock yet.

---

## 8. Recommendation

### 8.1 What to lock now

**The interface requirement**, which is what actually gates schematic work:

| requirement | value |
|---|---|
| Panel | 3.5 in, IPS, **320 × 480** |
| **Display controller** | **ST7796S / ST7796U preferred** (RGB565 over SPI). ILI9488 acceptable but costs 1.5× bus traffic |
| Display interface | 4-wire SPI, mode 0, with reset / DC / CS |
| Touch controller | **I²C**, FT6336U-class, address published, with defined RST and INT |
| Touch supply | 3.3 V |
| **FPC** | **single documented pitch**, 0.5 mm strongly preferred; documented pin count, tail thickness and contact side |
| Module envelope | ≤ 60 × 90 × 4.5 mm |
| Backlight | LED count and anode arrangement documented |

### 8.2 Leading candidate — **not locked**

**Chenghao CH350HV40A-CT** remains the leading candidate on size, fit and
availability. **Locking is conditional on obtaining the full spec PDF**
(`SPEC-CH350HV40A V0.pdf`) and confirming: single FPC pitch · full pin table ·
tail thickness · contact side · CTP part number and address · backlight pin
arrangement · the 3.97 / 2.4 mm thickness discrepancy.

**Preferred alternative if that PDF does not resolve cleanly:** any
current-production 3.5″ 320×480 IPS CTP LCM with **ST7796S + FT6336U** and a
**documented 40-pin 0.5 mm FPC**. This is the mainstream configuration for this
panel size, it is second-sourced across several vendors, and it removes both the
colour-depth penalty and the pitch ambiguity in one move.

### 8.3 Mating connector — conditional

**No connector can be selected until the display's pitch, pin count and contact
side are confirmed.** Choosing one now would repeat the exact mistake this audit
found: a connector picked without a display FPC drawing on file.

| if the display is… | candidate connector | note |
|---|---|---|
| **50-pin, 0.5 mm** | **Hirose FH69-50S-0.5SH** — already fitted on Beta-DM | The existing J1 is reusable. Contact side and tail thickness still need confirming |
| **40-pin, 0.5 mm** (preferred) | **Hirose FH12-40S-0.5SH(55)** — ZIF, bottom contact, 0.3 mm FPC | Very widely second-sourced; **verify at procurement** |
| 50-pin, 0.4 mm | Hirose FH34 / FH28 series equivalent | Requires a 0.4 mm-specific part; higher assembly risk |
| 50-pin, 0.3 mm | 0.3 mm ZIF | **Avoid** — hand rework on a 0.3 mm 50-pin tail is impractical for five prototype boards |

**Contact side (top vs bottom) must be confirmed against the display's FPC
drawing**, not assumed — it is the most common cause of a first-article display
that will not light.

---

## 9. Impact on gates and other documents

| item | impact |
|---|---|
| **FBV2-A2** | **Unchanged — still PASS.** The 3.5″ module fits the cavity with margin; the battery envelope is unaffected |
| **Mechanical spec** | `DISPLAY_ENVELOPE` updated from ≤52 × 71 × 3.0 to **≤60 × 90 × 4.5 mm**, candidate 56.54 × 84.96 × 3.97 |
| **Front layout** | Display grows from 50 × 69 to ~57 × 85 mm; **70 mm of the 155 mm cavity height remains** for D-pad, A/B and the mic aperture — ample |
| **FBV2-S1** (schematic migration) | **Can start**, with one exception: **sheet `03_spi_a_display_sd` is gated** on the display spec. Power, MCU, radios, NFC, audio, IR, buttons and the connector sheet are all unblocked |
| **FBV2-P1** (floorplan) | Front layout is now bounded, so M-01 no longer blocks placement in principle — but the **J1 footprint** does, so floorplanning should still wait |
| **Power budget** | Browsing draw ~100 → ~130 mA; offset by D-071's larger pack. Re-derive at the schematic phase |
| **M-01** | **Closed by D-072** (3.5″ ruled). Replaced by **M-06**, the display MPN/FPC gate |

---

## 10. Open items

| # | item | blocks |
|---|---|---|
| **M-06** | **Display MPN and FPC interface not locked.** Requires the full vendor spec: single pitch, pin table, tail thickness, contact side, CTP part, backlight arrangement | Schematic sheet `03_spi_a_display_sd`; J1 selection; FBV2-P1 |
| **M-07** | **Backlight driver re-derivation.** `RSET` and the TPS61169 current capability for a 6-LED panel | Display sheet |
| ~~M-01~~ | Display size | **CLOSED by D-072** |

---

## 11. Honest limitations

1. **The full CH350HV40A-CT specification PDF was not obtained.** The data above
   comes from the vendor's public product-specification document, which is
   detailed but incomplete — no pin table, no tail thickness, no contact side, no
   CTP part number.
2. **The CH280QV10-CT pitch could not be established from any source.** The
   compatibility verdict is therefore UNPROVEN, not NO. It would be equally wrong
   to assert an incompatibility as to assert compatibility.
3. **Connector MPNs are candidates, not selections**, and the Hirose part numbers
   should be verified against current Hirose documentation at procurement.
4. **The backlight arithmetic assumes 20 mA per LED**, which is typical but not
   stated in D1.

---

## Sources

- Chenghao **CH350HV40A-CT** — [product specification PDF](https://www.chenghaolcd.com/doc/19416516/3-5-inch-320x480-ips-tft-display-module-with-capacitive-touch-panel.pdf) · [product page](https://www.chenghaolcd.com/sale-19417883-cog-fpc-tft-lcd-capacitive-touchscreen-ili9488-3-5in-ctp-16-bit-rgb.html)
- Chenghao **CH280QV10-CT** — [listing](https://chenghaolcd.en.made-in-china.com/product/mfXUxqwvgQho/China-Commercial-Grade-2-8-240-320-Pixels-Capacitive-Touch-LCD-Display-with-280-CD-M2-Luminance.html)
- **ILI9488** datasheet — [mirror](https://www.elecrow.com/download/ILI9488%20Data%20Sheet_100.pdf)
- ST7796S + FT6336U 3.5″ reference configuration — [Waveshare](https://www.waveshare.com/3.5inch-capacitive-touch-lcd.htm)
- `hardware/beta/mechanical/reports/PHASE-1-MECHANICAL-AUDIT.md` (read only)
