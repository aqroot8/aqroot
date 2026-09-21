# AQROOT Full Beta v2 — off-board BOM, first five units

**Status: NORMATIVE.** Created 2026-08-23 at FBV2-S2-001. These are the items the **PCB** BOM will
not capture reliably, because they are not placed on the board. Authority:
[`../CTO_DECISIONS.md`](../CTO_DECISIONS.md).

**Quantities are per unit; order five plus spares.**

---

## 1. Display and touch

| item | MPN | qty | notes |
|---|---|---|---|
| **3.5″ IPS TFT + capacitive touch module** | **EastRising `ER-TFT035IPS-6`** with **`ER-TPC035-6`** touch | 1 | 320 × 480, ILI9488 COG, assembled outline **56.54 × 84.96 × 3.95 ± 0.25 mm**, one **50-pin 0.50 mm bottom-contact FPC, 0.30 ± 0.03 mm thick, 25.5 ± 0.15 mm wide**, carrying display **and** touch (touch on pins 44–47) |

> **THE PURCHASE ORDER MUST EXPLICITLY REQUEST THE `FT6236` TOUCH CONTROLLER.** EastRising offers
> the module with an alternative touch controller option; the AQROOT I²C address map, the
> `TOUCH_INT_N`/`TOUCH_RST_N` wiring and the reserved address **0x38** all assume FT6236.
> **A different controller changes the address and is a silent bring-up failure.**

---

## 2. Battery

| item | spec | qty | notes |
|---|---|---|---|
| **First-five LiPo pack** | **Adafruit Product 328 — 3.7 V / 2500 mAh**, genuine 2-pin JST-PH, protection circuitry | 1 | **SELECTED CTO-BAT-01.** Supplier page is the purchasing identity; its linked `785060` specification is archived at `hardware/demo/kicad/aqroot-demo/vendor/BATTERY/adafruit-328-785060-specification.pdf` (SHA-256 `826149da…ecd3`). Datasheet max pack is 7.9 × 50.5 × 60.5 mm, inside the **57 × 75 × 8.0 mm MAX** D-239/D-243 reservation, and permits discharge current ≤2C; supplier recommends ≤1.2 A charging. **Meter-verify polarity before cutting/reterminating the factory JST-PH lead into the D-781 Micro-Lock harness; do not substitute a generic LP785060 solely by family name.** |
| **D-781 detachable battery harness** | Board side: Molex `2175012101` red + `2175011101` black 26-AWG pre-crimps in `5055700201`; battery side: factory Adafruit 26-AWG leads reterminated into `2137192021` with `2137201000` male terminals | 1 | **FROZEN FOR FIRST FIVE.** Full work instruction, polarity, crimp/tool range, pull/thermal acceptance and first-article checks are in `BATTERY_HARNESS.json`. `J4` is only the manual PCB wire land; **do not fit the retired JST-PH board header.** |
| **Board-pigtail strain-relief adhesive** | **DOWSIL `3145 RTV MIL-A-46146` Adhesive/Sealant, gray** | as needed | **FROZEN D-782 PROCESS.** Non-flowing electronics RTV used to bond the insulated J4 pigtail to B.Cu after solder/profile inspection; preserve the relaxed service loop and ≥35 mm free wire from the Micro-Lock housing. Vendor TDS archived under `vendor/DOW/`; disconnect the harness by the housings, never the wires. |
| **Pack barrier sheet — D-760** | **0.5 mm compliant insulating sheet** (polyester film + closed-cell PE foam, or 3M 9448A-backed PET), cut to the `BATTERY_SHADOW` footprint **57 × 75 mm**, adhesive side to the PCB | 1 | **REQUIRED.** The rear face inside `BATTERY_SHADOW` presents a **1.90 mm** maximum component profile against the retained 1.20 mm heuristic; four 1206 bulk capacitors (`C29`-`C32`, CCTC `TCC1206X7R226K160HT`) are the hard points against the pouch.  *(D-791 / `D790-A08`: this line read **1.80 mm** on a Murata basis; the fitted parts are the CCTC 1206 at **1.90 mm** and `mechanical_keepout_contract` MK8 has ruled at 1.90 mm since D-789.)* The sheet spreads them and insulates the pack; it does not replace enclosure CAD clearance. Measured by `mechanical_keepout_contract` **MK8**. |

---

## 3. RF — 433 MHz

| item | MPN | qty | evidence |
|---|---|---|---|
| **433 MHz internal flex antenna** | **Taoglas `FXP450.07.0100C`** | 1 | Taoglas **SPE-23-8-180-A**. **410–470 MHz** (the `E07-400M10S` covers 410–450), **I-PEX MHF1 (U.FL)** connector, **100 mm** cable, 3M adhesive. Stocked DigiKey **21704215**, Arrow, TTI |

**Module interface:** the `E07-400M10S` ships with **both an IPEX connector and stamp holes**
(manufacturer product description) — **no variant selection is required**, the IPEX socket is
present on the standard part number. Mates MHF1/U.FL directly.

---

## 4. RF — 915 MHz

> **Read the gain number carefully.** Taoglas markets the `TI.92.2113` as "2 dBi". The data sheet
> table says **peak gain 1.21 dBi straight and 2.14 dBi bent**, and **average gain is negative in
> both orientations** (−0.97 dB straight, −1.35 dB bent). The headline figure is the *bent-peak*.
> Budget the link with the average, not the peak.
>
> **CURRENT mating chain, end to end (D-788 / R7-D787-20):** `E22-900M22S` **I-PEX MHF1** socket →
> **RF Solutions `CBA-UFLSMA20IP`** right-angle **U.FL/MHF-I plug** → **RG-178, 200 mm** →
> **SMA female** waterproof bulkhead jack through the top panel → **SMA male** hinged connector on
> the Taoglas `TI.92.2113`. **Every interface is female-to-male in the right direction, and the
> 200 mm length is what the 138.48 mm routed run plus a 15 mm service loop is checked against —
> 46.52 mm of spare.**
>
> ***HISTORICAL, SUPERSEDED, KEPT ONLY SO THE SUPERSESSION IS VISIBLE:*** *the chain read
> "Amphenol AMC right-angle plug → RG-178 150 mm" until D-788.  That narrative described the
> Amphenol RF `095-902-568-100` assembly, which **D-223 already superseded** in the purchasing
> table below on 2026-08-24 — it was ACTIVE but 0 in stock on a 12-week factory lead.  The
> purchasing row and the prose disagreed for eight months on BOTH the manufacturer AND the
> length, and Round-7 found it.  Nothing about the RF design changes: the selected part is the
> one the table has always carried.*
>
> **Power margin:** the module transmits **+22 dBm (0.16 W)** into an antenna rated **1 W** —
> better than 6× headroom.

| item | MPN | qty | evidence |
|---|---|---|---|
| **U.FL/MHF-I → SMA female bulkhead pigtail** | **RF Solutions `CBA-UFLSMA20IP`** *(supersedes Amphenol RF `095-902-568-100`, D-223)* | 1 | **Verified live 2026-08-24 under D-096.** DigiKey 14566928: **Part Status ACTIVE**, **296 in stock**, $11.58 @1 / $7.11 @vol; **200.00 mm**; **RG-178**; **50 Ω**; connector A **U.FL (UMCC) plug, RIGHT ANGLE, free hanging**; connector B **SMA jack, panel mount, bulkhead, front-side nut**. CPC/Farnell RF00982: **IP67**, 7 in stock, £6.29 @1, *“90° U.FL Plug to SMA Bulkhead Jack”*. Manufacturer drawing **`CBA-UFLSMAF20IP-1`**, rev 1 12/11/2015 revised 03/12/2015, notes: *1 UFL Right Angle · 2 Waterproof SMA Female Bulkhead Straight · 3 Heatshrink · 4 RG178 Coax cable* — **the drawing is marked NOT TO SCALE and dimensions nothing**, so the bulkhead envelope is taken from the Taoglas **SPE-24-8-198-C** drawing of the same SMA(F)BKST interface: **8.00 mm hex across flats = Ø9.238 across corners**, hex body 3.40 ± 0.2 mm, thread **1/4-36 UNS-2A × 11.40 ± 0.2 mm**, **star lock washer Ø10.2 REF**, nut HEX 8 × 1.80 ± 0.3 mm. **MECHANICAL: the FBV2-P1-002 floorplan measures a 138.48 mm routed run from `U8` to the top-panel SMA at doc (5.000, 148.000); 138.48 + 15 mm service loop = 153.48 of 200 mm, so SPARE = 46.52 mm.** **MATING: COMPATIBLE** — `E22-900M22S` carries an I-PEX MHF1 (IPEX-1) socket and Hirose U.FL / MHF1 are the same intermateable 2.0 × 2.0 mm interface; the cable end is a U.FL **plug**, the correct gender. **PROCUREMENT: this also removes a schedule risk — the superseded Amphenol part was ACTIVE but 0 in stock on a 12-week factory lead.** |
| *Fallback only — NOT ordered* | *Taoglas `CAB.01034`* | *0* | *Verified live 2026-08-24 under D-096 against the Taoglas Cable Assembly Catalog **SPE-24-8-198-C**: Hirose **U.FL** to **SMA(F) bulkhead straight**, **1.32 mm micro-coax**, **250 mm**, normal polarity, 50 Ω. **Held in reserve only**: the ruling selects the 250 mm assembly only if the measured route exceeds 180 mm, and it measures 138.48 mm. Its drawing is the dimensional source for the SMA(F)BKST envelope above.* |
| **915 MHz external antenna, SMA male** | **Taoglas `TI.92.2113`** | 1 | **LOCKED by CTO ruling, O-8 CLOSED 2026-08-23 (D-198).** Verified against Taoglas data sheet **SPE-19-8-076/A**: **ISM 915, 902–928 MHz**; **terminal-mount DIPOLE**; **hinged SMA(M)** connector as standard, so it mounts straight or right-angled; **198 ±3.3 mm × Ø13 mm**; TPEE body, **22.5 g**; 50 Ω, linear, omnidirectional; **max input power 1 W**; −40 to +85 °C. Efficiency **80.01 % straight / 73.20 % bent**. The reason it was chosen is in the data sheet in Taoglas' own words: it *"performs very well in free space, making it an ideal solution in areas where there may be no ground plane"* — AQROOT is a handheld that cannot provide the 30 × 30 cm ground plane a common monopole whip prefers |

**This is ONE assembly: the pigtail and the panel bulkhead are the same orderable part, so no
separate bulkhead MPN is needed.** Loss at 915 MHz is ≈ **0.4 dB** (RG-178 ≈ 1.2–1.5 dB/m ×
0.20 m plus two interfaces) against a +22 dBm module — negligible.

**Enclosure hardware:** the SMA bulkhead ships with its own nut and washer. The panel needs a
**Ø6.5 mm** clearance hole on the **top edge, left half — now at doc X 5.000 (D-222)**. **Two spacing rules apply and BOTH are
current** — see mechanical spec **§8.1** (authority traced at FBV2-MECH-002): **≥ 15 mm
CENTRE-TO-CENTRE** from the bulkhead hole to either IR window, **and ≥ 8 mm EDGE-TO-EDGE between the
SMA body and either IR aperture** (B-52, still **OPEN** — spacing recorded, **no CAD**). **B-52's floorplan half is now CLOSED (D-230): the body OD is Ø9.238 across the hex corners with a Ø10.2 lock-washer planar envelope, and the board achieves 47.250 mm centre-to-centre and 38.381 mm body-to-aperture against IR TX. Only an enclosure-CAD residual remains — the IP67 face O-ring seat diameter and the exact front protrusion, which RF Solutions does not dimension; the floorplan carries 1.6 mm of diametral headroom, which bounds it.** The right-angle **U.FL/MHF-I** plug on the `CBA-UFLSMA20IP` is the correct choice for a module
lying flat — it keeps the vertical stack low.  *(This sentence said "AMC plug" until D-788 /
R7-D787-20; the part is the RF Solutions assembly, not the superseded Amphenol one.)*

**Module interface:** the `E22-900M22S` likewise ships with **IPEX and stamp holes**.

---

## 5. NFC

| item | MPN | qty | evidence |
|---|---|---|---|
| **13.56 MHz NFC flex antenna** | **Taoglas `FXC.46.52.0075X.B.dg`** | 1 | Taoglas **SPE-24-8-104-B**: Ø46 mm, **reverse ferrite layer**, 75 mm twisted-pair 28 AWG with **ACH(F)** connector, peel-and-stick 3M adhesive. **The B variant is LOCKED (D-131)** — adhesive / flex / ferrite, for bonding to the **inside of the shell and reading outward**. **The A variant would put the ferrite between the coil and the tag and must never be ordered** |

Mates `J7` **`BM02B-ACHSS-GAN-ETF`** on the board.

---

## 6. Audio

| item | MPN | qty | notes |
|---|---|---|---|
| **Speaker** | **PUI Audio `AS02008MR-LW152-R`** | 1 | Ø20 × 3 mm, 8 Ω, 0.5 W rated / 0.8 W max, **500–4000 Hz voice band**, **152 mm AWG#32 leads** |
| Speaker mating housing | **JST `PHR-2`** | 1 | Mates `J6` |
| Speaker crimp contacts | **JST `SPH-004T-P0.5S`** (LCSC `C160351`) | 2 | **D-789 / D788-10 CORRECTS THE PART.**  D-148 through D-788 listed `SPH-002T-P0.5S`, whose published applicable wire range is **AWG #30 to #24, insulation OD 0.8–1.5 mm** (JST `ePH` catalogue, archived `vendor/JST/jst-ph-connector-ePH.pdf`, contact table).  **The fitted speaker's leads are AWG #32**, which is outside it in both dimensions — a #32 conductor in a #30–#24 barrel is an under-filled crimp with no published pull strength, and the insulation crimp cannot close on a lead thinner than 0.8 mm.  `SPH-004T-P0.5S` is the SAME PH series contact for **AWG #32 to #28, insulation OD 0.5–0.9 mm**; live stock 98 132 (`evidence/jlc-live/sph-004t-p0-5s-*.json`, 2026-09-21).  Same `PHR-2` housing, same `J6`, no board change.  **D-148's point stands: the speaker still crimps straight in and is replaceable without soldering.** |
| Speaker crimp tool | **JST `MKS-L-10`** with applicator **`APLMK SPH004-05S`**, or JST's hand tool for this contact | 1 | **D-789 / D788-10.**  The tool is part of the qualification, not an afterthought: JST's own crimping-machine table pairs `SPH-004T-P0.5S` with `MKS-L-10` / `APLMK SPH004-05S`, and pairs `AP-K2N` with the `SPH-002T` contacts instead.  A #32 lead crimped in a #30–#24 die is the exact failure this correction removes. |

---

## 7. Battery harness

**SPEAKER TERMINATION ACCEPTANCE — D-789 / D788-10.**  Before the five
speakers are crimped, **measure the insulation outer diameter of the actual
delivered lead** and record it: `SPH-004T-P0.5S` is published for 0.5–0.9 mm
and the PUI datasheet does not state the value.  A lead outside that band is a
STOP — re-select the contact, do not force it.  Then **crimp two sacrificial
contacts on a scrap length of the same lead and pull-test them to destruction**,
recording the force; the crimp is accepted only if both exceed the force the
lead's own conductor can carry, so the wire breaks before the crimp releases.
Record the measured insulation OD, the tool and die used, and both pull forces
in the first-five completion record as **`C-SPK-01`**.

**D-781 RETIRED THE JST-PH BATTERY MATING HARDWARE.** Do not buy `PHR-2` or
`SPH-004T-P0.5S` for the battery path. The exact first-five Micro-Lock Plus
wire-to-wire parts and factory pre-crimped board leads are already listed in
§2 and frozen by `BATTERY_HARNESS.json`. The JST parts in §6 are for the
**speaker J6 only** and must not be reused for J4.

---

## 7a. Accessory-voltage reinforcement lead — **RETIRED, D-789 / D788-07 + D788-08 + D788-09 + D788-16**

**THERE IS NO MANUAL REINFORCEMENT CONDUCTOR ON `ACC_3V3_SW`, AND NO WIRE TO
BUY FOR ONE.**  D-787 specified two 28 AWG leads onto one 1.00 mm pad; D-788
reduced that to one dimensioned lead from `TP12.1` to `J5.3`.  Round-8 raised
four independent findings against the remaining lead and every one of them is a
property of the conductor rather than of its description:

- the `TP12.1` joint called for **2.0 ± 0.5 mm of exposed tinned tip inside a
  1.00 mm round pad**, which cannot be built;
- the `J5.3` termination called for **inserting the tip into a through-hole
  already filled by J5's 0.635 mm square tail** — a 0.898 mm diagonal in a
  nominal 1.02 mm drill leaves 0.122 mm, and a 28 AWG conductor is 0.32 mm bare;
- the routed corridor **started inside `BATTERY_SHADOW` and crossed `RIB_R3`**
  while the record itself demanded 1.0 mm of clearance to both;
- the **≤ 25 mΩ acceptance could not be measured**, because the board's own
  routed `U20.5 → J5.3` copper stays in parallel with the lead.

**The lead bought 70 mV of published minimum on ONE of two duplicated
contacts.**  It is retired.  The Alpha Wire `2842/19 RD005` reel that existed
only for it is removed from this BOM, and so is its adhesive cure from the
critical path of every board.  `TP12` and `TP25` remain on the board as test
points for bring-up and for a future rework; **nothing is soldered to them.**

**What is published instead**, derived by `demo_feature_contract` F6 from the
live board and frozen in `DEVICE_SPEC`: the Community Port delivers
**≥ 2.81 V unconditionally** at the full published 400 mA — either duplicated
3.3 V contact used alone, one mated ground contact, and the 5 V rail also at
its 300 mA budget — and **2.917924 V with the header fully mated**, which is
better than the 2.95 V D-788 published with a hand-soldered conductor fitted.
*(D-791 / `D790-A08`: this paragraph read **2.84 V** and **2.982890 V**, which
were D-789's figures.  D-790 corrected them to 2.81 V / 2.918599 V and D-791's
corrected backlight budget moves the second to 2.917924 V.  The published
minimum on the 10 mV grid is UNCHANGED at 2.81 V.)*
The full record, including what it cost and what it bought back, is
[`ACC_3V3_REINFORCEMENT.json`](ACC_3V3_REINFORCEMENT.json).

**A dedicated Community-Port regulator is the real fix and the owner already
deferred it to REV-B.**

## 8. Bring-up and validation aids — not shipped with the product

| item | qty | why |
|---|---|---|
| USB-C cable, USB 2.0 data-capable | 1 | The **only** service interface: console, ROM download **and** JTAG over the native USB Serial/JTAG. **A charge-only cable will look like a dead board** |
| ~~Accessory reference mating header — Samtec `TSW-112-07-L-D` (2 × 12)~~ **SUPERSEDED by D-237.** **Accessory reference mating header — ANY ORDINARY 1 × 24, 2.54 mm MALE HEADER with a 0.635 mm (.025 in) SQUARE POST**, e.g. Samtec `TSW-124-07-x-S`, or 24 positions of ordinary breakaway strip | 1–2 | **The point of D-237 is that this is no longer a special part.** The socket's insertion depth is 3.68–6.35 mm, so any standard post in that range mates. **Ordinary male-to-female Dupont jumpers mate individual contacts directly and need no header at all** |
| **Qwiic / STEMMA QT cable, 100 mm, 4-conductor JST-SH 1.0 mm** | 2 | **NEW at D-238.** Any SparkFun Qwiic or Adafruit STEMMA QT cable mates `J8`; the two ecosystems are interchangeable here. Needed to exercise the I²C port at first article |
| microSD card | 1 | Card-detect and SPI-A validation |
| NFC test tag (ISO 14443A) | 1 | NFC bring-up |

---

## 9. Open off-board items

| # | item |
|---|---|
| ~~**O-8**~~ | **CLOSED 2026-08-23 (FBV2-S2-002).** Taoglas **`TI.92.2113`** locked by CTO ruling and verified live against the manufacturer data sheet. **No hardware or schematic change was required** — the panel connector is SMA **female** on the Amphenol pigtail and the antenna is SMA **male**, so the interface was already correct |
| ~~**M-04**~~ | **CLOSED CTO-BAT-01 — Adafruit Product 328 selected for first five; incoming pack must pass `battery_pack_contract.py` identity/spec envelope and polarity QC.** |
| — | Enclosure-side hardware beyond the SMA nut is **mechanical CAD scope**, deliberately not listed here |
