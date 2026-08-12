---
tags: [bom, cost, budget]
---

# BOM and Cost Tracker

## Stage 1 — bare-minimum dev-board prototype (breakouts/devkits, hand-wired)

| Part | Est. cost (USD) |
|---|---|
| ESP32-S3 DevKitC-1 (N16R8) | $8-12 |
| 2.8" IPS ILI9341 capacitive-touch SPI module (FT6236 @ 0x38) | $12-20 (sourcing resolved — Elecrow / LCDwiki class) |
| ST25R3916 NFC — X-NUCLEO-NFC06A1 eval board *(Beta production part is the bare **ST25R3916-AQET**, UFQFPN32 — see the physical-capture table below)* | $25-35 |
| CC1101 sub-GHz module (433MHz, e.g. blue 433M V2.0) *(Beta production part **LOCKED: Ebyte **E07-400M10S** — see below)* | $3-8 |
| SX1262 certified LoRa breakout (e.g. Ebyte E22 / Waveshare Core1262) *(Beta production part **LOCKED: Ebyte **E22-900M22S** — see below)* | $10-20 |
| BMI270 6-axis IMU breakout (SparkFun Qwiic) | $3-8 |
| ICS-43434 I2S MEMS mic breakout | $5-8 |
| MAX98357A I2S Class-D amp breakout | $5-8 |
| Small 4/8ohm speaker (~1-2W) | $2-5 |
| **TI TCA9535PWR** I2C GPIO expander **x2** — U60 @ 0x20 internal + U61 @ 0x21 community header (PW / TSSOP-24 / 0.65mm) | $2-6 (bare ICs; **no validated breakout — see note**) |
| TPS63020 buck-boost 3.3V breakout (production P/N: TPS63020DSJR, DSJ) — **architecture LOCKED**; support parts below | $8-12 |
| L1 inductor **LOCKED**: Coilcraft **XFL4020-152MEC**, 1.5µH ±20%, DCR ~14.4mΩ typ / ~15.8mΩ max, Isat ~4.1/4.4/4.6 A at 10/20/30% L loss, ~2.1mm max height, shielded molded — **LCSC C3033018** | $1-3 |
| TPS63020 feedback + config resistors **LOCKED**: `R_FB_TOP` 1M 1%, `R_FB_BOTTOM` 180k 1%, `R_PG_PULLUP` 1M, `R_EN_PULLDOWN` 100k, `R_PS_DEFAULT` 0R (**`R_EN_BYPASS` 0R = DNP**) | <$1 |
| TPS63020 capacitors — **VALUES LOCKED, EXACT MPNs PENDING**: `C_VINA` 100nF X7R; **CIN** 2×10µF 10V+ X7R; **COUT** 4×22µF 10V X7R **1206** (provisional MPN Murata GRM31CR71A226ME15L). See note below. | $1-4 **(provisional)** |
| MAX17048 fuel gauge — **Beta part MAX17048G+T10** (ADI, 8-pin 2×2mm TDFN/LFCSP; prefer **G** over the **X** WLP for assembly/inspection). I²C **0x36**, no sense resistor. **Protected-side placement only.** Breakout deferred — validate on Beta | $5-10 |
| NFC 5V boost **LOCKED**: TI **TPS61023DRLR**, DRL / SOT563 6-pin (1.2×1.6mm) — **not a generic SOT-23**. Plus `L_NFC_BOOST` ~1µH shielded low-DCR, `C_NFC_BOOST_IN`/`C_NFC_BOOST_OUT`, FB divider — **all values from the TI 5V reference/EVM, MPNs provisional** | $1-4 **(provisional)** |
| Physical hard-off slide switch (SPST maintained, TH mounting tabs preferred) — **MPN provisional pending Field Slate mechanical review**, footprint must match a real candidate | $0.30-1 |
| LiPo 2000mAh | $8-14 |
| **BQ25185DLHR** charger + power-path — TI, **DLH / WSON-10**, 2.2 x 2.0 mm, 0.4 mm pitch, exposed thermal pad. Footprint `Package_DFN_QFN:Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm` (KiCad stock, derived from TI DLH0010A) | $5-10 |
| **Reverse-polarity protection — NO FINAL P/N CLAIMED (parked)**. *Provisional only:* ADI **LTC4368-1** controller (MSOP / 3×3 DFN) + **2x AO3400A-class** N-channel FETs (AOS AO3400A, LCSC C20917, SOT-23) + sense resistor, UV/OV divider, timer/inrush parts and gate clamp — **all values and P/Ns unselected**. See note below. | $2-6 **(provisional estimate — not a quote)** |
| IR: TSOP38238 receiver + TSAL6200 940nm emitter + low-side MOSFET driver stage | $2-6 |
| 7x tactile buttons (D-pad up/down/left/right + A/B + Home) + physical power switch | $2-5 |
| I2C bus buffer/isolator or bus switch (external header protection) — part TBD | $1-3 |
| Accessory-rail load switch (driven by ACC_PWR_EN) — part TBD | $0.50-2 |
| USB-C breakout, wiring, protoboard | $5-10 |
| USB-C receptacle **(Beta-locked family)**: GCT **USB4105**, 16-contact USB 2.0 Type-C, top-mount horizontal, SMD contacts + TH shell stakes. Candidate **USB4105-GF-A-120** — **exact suffix pending PCB-thickness / shell-stake confirmation** | $1-3 |
| USB ESD array **LOCKED**: ST **USBLC6-2SC6**, SOT-23-6 — data clamp + VBUS clamp reference (**not** a series pass part) | $0.30-1 |
| USB passives: `R_CC1_RD` + `R_CC2_RD` **2× 5.1k 1%** (independent Rd); `R_USB_DN_SER` + `R_USB_DP_SER` 2× 22R; `C_USB_VBUS` 4.7µF 10V+ X7R; `R_USB_SHIELD_LINK` 0R. **DNP:** `C_USB_DP_EMC` = **C22** + `C_USB_DN_EMC` = **C21**, 100 pF — **DNP — data pin NC in Beta; rework-only tuning option** (no populated Beta MPN assigned); `R_USB_SHIELD_BLEED` 1M | <$1 |
| 3D print filament (own Kobra S1) | $3-8 |
| **Total per unit** | **~$110-200** |

## Beta production parts locked by physical schematic capture (2026-08-06 → 2026-08-08)

These are **real parts with verified footprints already integrated into the KiCad schematic**,
not candidates. Each carries its verification class. Costs are rough order-of-magnitude and are
**not quotes** — they still go through the pre-fab BOM-validation pass below.

| Ref | Part | Package / footprint | Verification | Est. cost (USD) |
|---|---|---|---|---|
| J1 | **Hirose FH69-50S-0.5SH** — 50-pin 0.5 mm FPC display connector | `AQROOT_Beta:Hirose_FH69-50S-0.5SH` | VERIFIED_VENDOR_EXACT | $1-3 |
| J2 | **Molex 5025700893** — microSD push-push, shielded, mechanical card detect | `AQROOT_Beta:Molex_5025700893` — 14 lands, 1.10 mm pitch, 7.7 contact span, 14.3 shell outer | VERIFIED_VENDOR_DRAWING_WITH_EXACT_PART_CAD_CORROBORATION (Molex SD-502570-001 + exact-part CAD C429846) | $0.50-2 |
| U7 | **Ebyte E07-400M10S** — CC1101 certified module, 433 MHz | `AQROOT_Beta:Ebyte_E07-400M10S` | VERIFIED_VENDOR_EXACT | $3-6 |
| U8 | **Ebyte E22-900M22S** — SX1262 certified module, 915 MHz | `AQROOT_Beta:Ebyte_E22-900M22S` | VERIFIED_VENDOR_EXACT | $6-12 |
| U9 | **ST ST25R3916-AQET** — NFC/RFID reader | `AQROOT_Beta:ST25R3916_AQET`, UFQFPN32, ST land pattern (0.30×0.75 lands, 5.30 span, 3.45×3.45 EP) | VERIFIED_VENDOR_EXACT | $4-8 |
| U12 | **TI TPS63020DSJR** buck-boost | `AQROOT_Beta:TI_TPS63020_DSJ` (DSJ, exposed pad with slots) | VERIFIED_VENDOR_EXACT | *(already costed above)* |
| — | **TI TPS61169DCKR** display-backlight LED driver | SC-70-5 / DCK | vendor symbol + footprint built | $0.30-1 |
| — | Backlight passives: **4×39R** LED-string ballasts + **2.55R** RSET | 0603 | values locked from the TI datasheet | <$1 |
| C45-C54 | **ST-specified ST25R3916 decoupling — 10 capacitors**: VDD_D 2.2µF+10nF, VDD_A 2.2µF+10nF, VDD_RF 2.2µF+10nF, VDD_AM 2.2µF+1nF, AGDC 1µF+10nF | 2.2µF = 16V X7R **0805** (not 0603, so effective capacitance survives DC bias); small values 50V X7R 0603; 1µF 16V X7R 0603 | values exactly as ST specifies, **not substituted** | $1-3 |

> **Why the radios are modules, not bare ICs.** Both are **certified** modules carrying FCC/CE
> pre-certification. Modifying the RF section **voids that certification**, which is why all RF
> on both parts is marked **DO NOT ROUTE** and antennas leave via the modules' own IPEX ports.
> The E22's RF switch is controlled by **`DIO2` → `TXEN` locally inside the module**, with
> **`RXEN` host-driven from U61 P16 (`SX1262_RXEN`)** — the reclaimed XGPIO14, with a 100k
> pull-down. No MCU pin was added; see [[11 - Beta Pin Map v0.2]] §v0.2.5.

> **Still missing footprints (14 refs, 2026-08-08):** `C12 C18 C19 LS1 R24 SW1`-`SW8 U14`.
> **No connectors remain on that list.** Coverage is **186 components, 172 footprinted**.


> **USB-C front-end note (2026-07-30) — Beta-locked, NOT production-hardened.** Role is **USB
> Type-C sink / UFP, 5V only, USB 2.0 full-speed — no PD, no source/DRP role, no VCONN, no alt
> modes.** The **GCT USB4105 family** is selected for Beta capture; the **exact suffix
> (candidate USB4105-GF-A-120) is subject to PCB-thickness / shell-stake confirmation** — verify
> the official drawing, the stake length against the final board thickness, and that the KiCad
> footprint matches the manufacturer drawing before the MPN is locked. **USBLC6-2SC6 is retained
> for ESD protection**; note its **VBUS pin is a shunt/clamp reference, never a power
> pass-through**. **Two independent 5.1k 1% Rd resistors** are mandatory — one per CC pin, never
> combined, never firmware-connected. **22R series resistors at the MCU** on D+/D−; **100pF EMC
> capacitors are DNP** for Beta and populate only after signal-integrity / EMI review.
> **C21 / C22 (2026-08-12, CTO ruling — Option B):** both remain 100 pF **DNP** and keep their
> footprints and placement, but their **data-side pins are intentionally NC in Beta** — only the
> GND pin stays connected. BOM status for both: **"DNP — data pin NC in Beta; rework-only tuning
> option."** **No populated Beta MPN is assigned.** The 100 pF value must be **revalidated
> against measured USB edge-rate / EMI behaviour** before any future population or reconnection.
> **`C_USB_VBUS` is 4.7 µF deliberately rather than 10 µF**, to keep connector-side input
> capacitance and hot-plug behaviour conservative; it does **not** replace the bq25185's own VIN
> decoupling. **No CC current-advertisement detection exists**, so the bq25185 input-current
> limit must stay conservative on a generic port — **do not claim USB-PD support, and do not
> claim universal 1 A USB input compliance just because the charger supports 1 A battery charge
> current.** The **shield-to-ground strategy (0R default, 1M bleed DNP) receives final EMI/ESD
> review**. **Connector and ESD exact stock/lifecycle must be rechecked during the pre-fab BOM
> validation pass.** See [[05 - Design Decisions Log]].

> **TPS63020 capacitor note (2026-07-30) — values locked, exact MPNs NOT BOM-locked.** The
> regulator block is **architecture-locked and capture-approved**; only the capacitor MPNs are
> open, and they are a **BOM-release gate, not a schematic-capture gate**. Do not stall the
> schematic on per-capacitor DC-bias research — it is batched into **one board-wide
> BOM-validation pass before fabrication**, run alongside the professional power/DFM review.
> **CIN:** 2 × 10 µF, 10 V minimum, X7R, active-lifecycle MPN pending; combined **effective
> CIN ≥ 10 µF at ~4.5 V**, each part retaining ~**≥ 5 µF at 4.5 V** after derating.
> **The obsolete Murata `GRM21BR71A106KE51L` must NOT be used.** Provisional footprint **1206**
> (preferred over 0805 unless a mechanical constraint forces it — 0805 only if the eventual MPN
> can still meet the derating requirement).
> **COUT:** 4 × 22 µF, 10 V, X7R, **1206**; combined **effective COUT ≥ 40 µF at 3.3 V**, each
> part averaging **≥ 10 µF** under the documented acceptance assumptions. Current MPN **Murata
> GRM31CR71A226ME15L is PROVISIONAL** — verify Murata DC-bias data before fab.
> **L1 is locked to XFL4020-152MEC.** XGL4020-152 may be *reviewed* as an approved alternate —
> **do not silently substitute**, and do not list it as the installed part.
> Everything the validation pass must archive is listed in [[05 - Design Decisions Log]] and
> [[07 - Build TODO Tracker]].

> **Reverse-polarity protection note (2026-07-30) — no final part number is claimed.** The
> topology is **PARKED**: high-side only, battery negative tied to system GND. The **leading
> candidate is provisional only** — ADI **LTC4368-1** (active back-to-back N-FET controller,
> ~2.5–60 V, ~80 µA Iq, forward/reverse sense ~±50 mV) driving **two series back-to-back
> N-channel AO3400A-class** FETs (AOS AO3400A, LCSC C20917, SOT-23, 30 V, ~48 mΩ @ Vgs 2.5 V,
> Vgs max ±12 V). **AO3401A (LCSC C15127)** remains a valid building block *if* a PMOS variant
> is chosen; a single PMOS alone is rejected as a final solution. **Do not order these as
> final.** The sense resistor, UV/OV divider (3.0–4.2 V), timer/inrush parts, gate clamp and
> package are all unselected, and the cost line above is a placeholder estimate rather than a
> quote. **Final topology lock belongs to the professional power/DFM pre-fabrication review**,
> which must run the LTC4368 LTspice charge-path case and obtain ADI vendor/FAE confirmation.
> **No PCB routing or fabrication release until that gate closes.** See
> [[05 - Design Decisions Log]].

> **GPIO expander note (2026-07-27):** the expander was changed from the MCP23017 to the **TI
> TCA9535PWR** (see [[05 - Design Decisions Log]]). The MCP23017 breakout that was bought and
> bench-tested during Alpha is **no longer the design part** — that spend is sunk, and the board
> is still useful for I2C-architecture work, but it validates nothing about the TCA9535. The
> TCA9535PWR is **TSSOP-24 only in this package**, so Stage 1 hand-wiring needs either a
> TSSOP-24 breakout adapter board or a TCA9535 module; budget a few dollars for adapters. **This
> part is datasheet-trusted and unvalidated — its first hardware confirmation is on Beta.**

> Cost went UP vs the original ~$65-130 estimate, for three deliberate reasons: the
> dual-radio base adds a CC1101, the NFC part moved from a ~$10 PN532 breakout to a ~$30
> X-NUCLEO ST25R3916 eval board (the validated part), and the power tree gained a separate
> TPS63020 regulator. Partly offset by the ILI9341 display coming in under the AMOLED
> estimate. The X-NUCLEO board is an Alpha/prototype cost only — production uses a bare
> ST25R3916 + matching network, which is far cheaper.

Budget 2-4 units at this stage if sending prototypes to reviewers ahead of a Kickstarter
launch (~$110-200 each).

## Stage 2 — custom PCB prototype (small batch, later stage, not v1)

Small JLCPCB run (~5 boards), 4-layer, with JLCPCB assembly service for SMD parts:
estimated $150-350 for the batch, depending on final BOM and how much you hand-solder
yourself (headers, connectors, battery wiring) to reduce assembly fees.

## Prototype-to-production strategy
Plan: prove core functionality (NFC read, sub-GHz scan, IR blast, LoRa, UI navigation) on
Stage 1 dev-board prototypes for the Kickstarter campaign, then finish the final custom PCB,
certified antenna tuning, and manufacturable enclosure during the funded production phase.
This is standard practice for hardware campaigns.

IMPORTANT: only demo features that actually work on the prototype. Kickstarter's rules and
general reputational risk both require not presenting non-functional concepts as working
features. If a feature isn't working yet, label it "in development," don't demo it as if
it works.

## Open item
- Total prototype budget ceiling: not yet set by [YOUR NAME] — fill in once decided.

## Battery pack — charge-rate VERIFY (2026-08-11, blocks BOM lock, not routing)

`R37` was changed **2 kΩ → 1 kΩ** on the BQ25185 `ISET` pin, taking the programmed fast-charge
current from 150 mA to **300 mA typical** (285/300/315 mA from the `KISET` spread; 270–330 mA at
TI's ±10 % `ICHG_ACC` spec). `R36` = 18 kΩ is unchanged, so the input current limit stays at
**ILIM500** (450/475/498 mA) and `VBATREG` stays at 4.2 V.

**VERIFY BEFORE BOM LOCK — the cell/pack must permit ≥300 mA charge current:**

- [ ] Cell datasheet **standard** and **maximum** charge current at 2000 mAh. 300 mA is **0.15 C**,
      which is conservative for LiPo (typical standard charge is 0.5 C), but no pack MPN is locked
      yet so this is unverified rather than safe-by-assumption.
- [ ] The **pack's integrated protection circuit** charge-current rating, which is a separate
      number from the cell's and is often the lower of the two.
- [ ] Charge **temperature** window, against the enclosure's internal rise at 300 mA.

> **Related thermal consequence, carried to the routing/thermal pass.** The BQ25185 is a *linear*
> charger with a power path: it regulates SYS to 4.5 V by dropping VIN, then drops SYS→BAT across
> the BATFET. Worst-case device dissipation is **≈0.69 W** (0.238 W on IN→SYS at 475 mA + 0.450 W
> on the BATFET at 300 mA with a depleted 3.0 V pack), against ≈0.46 W at the old 150 mA — a **50 %
> increase**, in a 2.2 × 2.0 mm WSON-10. `TREG` = 100 °C folds charge current back rather than
> failing, so this is a charge-*time* risk, not a hazard. But it means **U11's exposed-pad thermal
> vias are now required for the 300 mA target to be sustained**, not optional. The thermal-via plan
> is revised from 1 to **2** THERMAL-class vias on U11's 0.9 × 1.5 mm pad. Dissipation falls to
> ≈0.39 W once the pack reaches 4.0 V, so the peak is transient and occurs exactly when a depleted
> pack is plugged in.
