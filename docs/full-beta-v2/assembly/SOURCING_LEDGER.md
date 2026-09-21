# AQROOT Full Beta v2 — sourcing ledger

**Status: SUPERSEDED FOR ASSEMBLY ROUTING by**
[`FIRST_FIVE_ASSEMBLY_PLAN.md`](FIRST_FIVE_ASSEMBLY_PLAN.md) **(FBV2-S2-002, B-71 closed).**
That file carries the live LCSC/JLC state, the A–F class for every part and the consignment
plan. **This file remains normative for the sourcing *evidence* behind each MPN.**

**Status: NORMATIVE for the first five boards.** Generated 2026-08-23 at FBV2-S2-001 from the
schematic, not from a spreadsheet. Authority: [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md).

**D-096 applies throughout: a part number configured from an ordering scheme is a hypothesis, not
a selection, until a live manufacturer or distributor record confirms lifecycle and stock.**

> **UPDATED 2026-08-24 (FBV2-P1-002).** The 915 MHz pigtail is re-selected — see the `CBA-UFLSMA20IP` row in §2 and **D-223**. **No on-board MPN changed.**

**46 unique MPNs across 322 schematic components. Every active and every connector now carries an
exact MPN — 0 missing** (six were added at FBV2-S2-001, see §4).

> **UPDATED 2026-08-23 (FBV2-S2-002).** **65 `LCSC` fields have been written into the schematic**, so the BOM is now exportable directly. **Three MPN strings were corrected**: `J6` → `B2B-PH-K-S(LF)(SN)` and `J7` → `BM02B-ACHSS-GAN-ETF(LF)(SN)` — in both cases the bare order code resolves to a **zero-stock** LCSC listing while the plating-suffixed string is abundantly stocked — and `L2`/`L4` were normalised to one spelling of "Würth". **`L5`/`L6` gained an MPN for the first time** (Murata `LQW18AN39NG80D`, B-70). **Six substitution traps** found while doing this are listed in [`FIRST_FIVE_ASSEMBLY_PLAN.md`](FIRST_FIVE_ASSEMBLY_PLAN.md) §8 **and are recorded in the schematic symbols themselves**.

---

## 1. Classification

| class | meaning |
|---|---|
| **A** | JLC/LCSC **BASIC** |
| **B** | JLC/LCSC **EXTENDED** |
| **C** | JLC orderable but a special / manual process |
| **D** | manufacturer or distributor orderable, **not** a JLC assembly part |
| **E** | off-board / mechanical / cable / antenna / speaker / battery |
| **F** | DNP on the first build |
| **G** | **sourcing BLOCKER** |

---

## 2. D-096-VERIFIED — live listing seen, with evidence

| MPN | refs | class | evidence, dated |
|---|---|---|---|
| **SSQ-124-02-G-S-RA** | `J5` | **C** | **NEW at D-237, superseding `BCS-112-S-D-HE`. SAME MANUFACTURER**, so the account, the lead-time behaviour and the small-quantity policy are already known. Samtec SSW/SSQ through-hole datasheet: 01–50 positions per row, `-S` single row, `-RA` right angle available with `-S`, body 61.47 mm, **mates .025 in (0.635 mm) square post**, 6.3 A per pin, 465 VAC / 655 VDC, −55…+125 °C with gold, 100 mating cycles. **Through-hole → manual / secondary assembly, unchanged: one THT part replaced one THT part and the count stays at 24** |
| ~~**BCS-112-S-D-HE**~~ | ~~`J5`~~ | — | **SUPERSEDED by D-237, but the footprint is RETAINED in the library and NOT deleted**: Beta-DM still uses it and it is the fallback if D-237 is ever reversed. Samtec page 2026-08-23: ACTIVE, 385 pcs, $7.314 @1 / $5.667 @100 |
| **SM04B-SRSS-TB(LF)(SN)** | `J8` | **NEW (D-238)** | JST SH series, 1.0 mm pitch, 4 circuit, side entry, **SMT — MACHINE-PLACED, so the manual-assembly list does NOT grow** and stays at `J5` + `D1`. 1.0 A, 50 V AC/DC, −25…+85 °C, 20 mΩ contact resistance. Widely second-sourced: it is the part the entire Qwiic / STEMMA QT ecosystem standardised on |
| **TCA4307DGKR** | `U16` | **B** | LCSC **C880333** 2026-08-23: **3 248 in stock**, $2.51 @1 / $1.71 @1k |
| **ST25R3916-AQET** | `U9` | **B** | LCSC **C5267441** (D-126) — the only one of the two NFC variants with an LCSC code and therefore a JLC path |
| **MHPA3528RGBCT** | `D13` | **B** | LCSC **C409779** 2026-08-23: **69 270 in stock**, $0.1035 @500 |
| **5025700893** | `J2` | **B** | LCSC **C429846** |
| **E22-900M22S** | `U8` | **B** | LCSC **C411293** |
| **TXM27.12M0004322DBBDO00T** | `Y1` | **B** | LCSC **C362365** |
| **XFL4020-152MEC** | `L1` | **B** | LCSC **C3033018**; Coilcraft doc 745-1 rev 03/10/26 |
| ~~**TPS22950CDDCR**~~ | ~~`U20`, `U22`~~ | **B/D** | **SUPERSEDED BY D-765.** The `C` variant's own specified `ILIM` range is 0.5-3.5 A (`SLVSFJ2B` s.5) and the board programmed 0.407 A at the time (0.636 A / 0.479 A since D-771). |
| **TPS22950CQDDCRQ1** (TPS22950-Q1) | `U20`, `U22` | **B/D** | **D-765.** LCSC `C17349276`, 4 050 in stock 2026-09-18; TI orderable addendum `SLVSGP6A`: **Active / Production**, RoHS, MSL-1-260C-UNLIM, -40..125 C, marking `950Q`. Same **DDC0006A** SOT-23-THN 6-pin land pattern and pinout; `ILIM` specified **0.05-3.5 A**; AEC-Q100 grade 1. |
| ~~**CRA2512-FZ-R015ELF**~~ | ~~`R75`~~ | **B** | **SUPERSEDED BY D-771.** LCSC `C2073490`, 15 mΩ. At 15 mΩ the LTC4368's forward breaker sat at **2.640–4.040 A** over ADI's guaranteed 40/50/60 mV threshold band, which OVERLAPPED the `BQ25185`'s recoverable `IBAT_OCP` band of 2.5625–3.6875 A; `RETRY` is grounded here, so the LATCHING protection could fire before the auto-retrying one. |
| **CRA2512-FZ-R010ELF** | `R75` | **B** | **D-771.** LCSC `C840621`, BOURNS, verified live 2026-09-18 per D-096 through the JLCPCB parts API (`evidence/jlc-live/cra2512-fz-r010elf-dbf2172c.json`): **10 mΩ ±1 %**, 2512, **3 W**, **±50 ppm/°C**, −55…+170 °C, `componentLibraryType` **expand**, **10 613 in stock**. SAME Bourns `CRA2512-FZ` **current-sense** series, SAME 2512 land and SAME 3 W rating as the `-R015ELF` it replaces — **only the resistance moves**, so no footprint, no copper and no assembly step changes. Breaker band becomes **3.960 / 5.000 / 6.061 A**, entirely above `IBAT_OCP`'s 3.6875 A maximum. *Catalogue `Type` is blank on this member where it reads `Current Sense Resistor` on the 15 mΩ one; `rule_open_sourcing.py` accepts an ABSENT type against the named `CRA2512-FZ` series prefix and against the stated ±50 ppm/°C, and still refuses a stated type outside the class.* |
| ~~**0603WAF2701T5E**~~ | ~~`R97`, `R101`~~ | **A** | **SUPERSEDED BY D-771.** LCSC `C13167`, 2.7 kΩ, JLCPCB **BASIC**. It programmed 0.407 A typ, which GUARANTEES only **0.277 A** against the **400 mA / 300 mA** D-098 publishes for these two rails — a budget the board's own limiter could refuse to deliver. |
| **0603WAF1781T5E** | `R97` | **B** | **D-771.** LCSC `C22849`, UNI-ROYAL(Uniroyal Elec), verified live 2026-09-18 per D-096 (`evidence/jlc-live/0603waf1781t5e-95493b28.json`): **1.78 kΩ ±1 %**, 0603, 100 mW, ±100 ppm/°C, −55…+155 °C, `componentLibraryType` **expand**, **19 278 in stock**. SAME `0603WAF` series and SAME manufacturer as the `2701T5E` it replaces and as most of this board's 1 % resistors; same 0603 land. Programs **0.636 A typ → 0.428 A GUARANTEED**, 7.0 % over the published 400 mA. 1.78 kΩ is an **E96** value and JLCPCB lists no BASIC part at it; the extended-part fee is accepted because the E24 alternatives either fail the published-budget clause or spend the pack margin. |
| ~~**0603WAF2321T5E**~~ | ~~`R101`~~ | **B** | **SUPERSEDED BY D-773.** LCSC `C22905`, 2.32 kΩ. Chosen at D-771 against a 4.95 V boost-output *constant*; at the setpoint D-773 DERIVES from `R99`/`R100` and the `TPS61023`'s own published 580/595/610 mV `VREF` band — **4.742 / 4.950 / 5.165 V** — the limiter's worst case leaves only **0.52 %** of margin to the pack's minimum trip. |
| **0603WAF2371T5E** | `R101` | **B** | **D-773.** LCSC `C25964`, UNI-ROYAL(Uniroyal Elec), verified live 2026-09-19 per D-096 through the JLCPCB parts API (`evidence/jlc-live/0603waf2371t5e-757eecf8.json`): **2.37 kΩ ±1 %**, 0603, 100 mW, ±100 ppm/°C, −55…+155 °C, `componentLibraryType` **expand**, **11 268 in stock**. Same `0603WAF` series, same manufacturer, same 0603 land — only the resistance. Programs **0.468 A typ → 0.315 A GUARANTEED** (+4.9 % on the published 300 mA) while holding **+1.6 %** to the pack's minimum trip; it is the **E96 value nearest the centre of its legal window, 2.298–2.478 kΩ**. |
| **0603WAF2321T5E** | *(superseded)* | **B** | **D-771.** LCSC `C22905`, UNI-ROYAL(Uniroyal Elec), verified live 2026-09-18 per D-096 (`evidence/jlc-live/0603waf2321t5e-fa18111f.json`): **2.32 kΩ ±1 %**, 0603, 100 mW, ±100 ppm/°C, −55…+155 °C, `componentLibraryType` **expand**, **6 268 in stock**. Same series, same manufacturer, same 0603 land. Programs **0.479 A typ → 0.322 A GUARANTEED**, 7.4 % over the published 300 mA; it cannot go lower because the 5 V rail's worst case already sits 5.6 % under `IBAT_OCP`'s minimum. |
| ~~**AO3422**~~ | ~~`Q11`~~ | **B/D** | **SUPERSEDED D-780.** D-779 proved its 2.5 V guaranteed `RDS(on)` point sat above AQROOT's 2.396 V held `VGS`; typical `gFS` could not close that production guarantee. |
| **SQ2364EES-T1_BE3** | `Q11` | **C** | **D-780.** Vishay, LCSC `C5758702`, JLC stock **0** at the 2026-09-19 check; **buy broadline and consign**. Same SOT-23 1=G/2=S/3=D, `VDS` 60 V, `RDS(on)` ≤0.245 Ω at `VGS` 1.5 V / `ID` 2 A, `IGSS` ±100 nA. Low-gate row is a 25 °C EC point; first-five acceptance `Q11-TEMP-01` covers 0/25/40 °C and is intentionally not an all-temperature production claim. |
| **PTS645SM43SMTR92LFS** | `SW1`–`SW7` | **B** | Littelfuse/C&K PTS645 datasheet orderable table: 1.6 N ±0.3, 100 000 ops, 0.30 mm travel |
| **TSOP38238** | `U6` | **B** | Vishay doc 82491 Rev 2.1; **TSOP38438 retained as a same-footprint fallback** (D-163) |
| **74438357010** | `L4` (`L2` DNP) | **B** | Würth datasheet rev 003.001: 1 µH ±20 %, **Isat 6.2 A / 12.5 A**, RDC 11.6 mΩ |
| **E07-400M10S** | `U7` | **B** | Ebyte product description confirms the module ships with **both IPEX and stamp-hole** antenna interfaces |
| ~~**095-902-568-150** / **095-902-568-100**~~ | ~~off-board~~ | — | **SUPERSEDED 2026-08-24 by D-223.** Amphenol's 100 mm variant was ACTIVE but **0 in stock with a 12-week factory lead and no JLCPCB listing**, and the FBV2-P1 geometry showed no Amphenol length could reach while the SMA stayed top-left. Kept for history. |
| **CBA-UFLSMA20IP** | off-board | **E** | **RF Solutions, verified live 2026-08-24 under D-096.** DigiKey 14566928: **Part Status ACTIVE**, **296 in stock**, $11.58 @1 / $7.11 @vol; **200.00 mm**; **RG-178**; **50 Ω**; connector A **U.FL (UMCC) plug, right angle, free hanging**; connector B **SMA jack, panel mount, bulkhead, front-side nut**. CPC/Farnell RF00982: **IP67**, 7 in stock, £6.29 @1. Manufacturer drawing **`CBA-UFLSMAF20IP-1`** rev 1 12/11/2015 revised 03/12/2015 — *UFL Right Angle · Waterproof SMA Female Bulkhead Straight · Heatshrink · RG178 Coax cable*, **marked NOT TO SCALE and carrying no body dimensions**, so the bulkhead envelope is taken from Taoglas **SPE-24-8-198-C** for the same SMA(F)BKST interface. Routed run **138.48 mm** of 200 mm; **spare 46.52 mm** beyond the 15 mm service loop; loss ≈ 0.4 dB. **Second source at two distributors today, which the superseded Amphenol part did not have.** |
| **CAB.01034** | off-board | **E** | **FALLBACK ONLY — NOT ORDERED.** Taoglas Cable Assembly Catalog **SPE-24-8-198-C**, verified live 2026-08-24: Hirose **U.FL** → **SMA(F) bulkhead straight**, **1.32 mm micro-coax**, **250 mm**, normal polarity, 50 Ω. Selected only if the measured route exceeds 180 mm; it measures 138.48 mm. **Its drawing is the dimensional source for the SMA(F)BKST envelope** used to close B-52's floorplan half: 8.00 mm hex across flats = **Ø9.238 across corners**, hex body 3.40 ± 0.2 mm, thread 1/4-36 UNS-2A × 11.40 ± 0.2 mm, **star lock washer Ø10.2 REF**, nut HEX 8 × 1.80 ± 0.3 mm, centre pin Ø0.90 ± 0.05. |
| **FXP450.07.0100C** | off-board | **E** | Taoglas SPE-23-8-180-A; **410–470 MHz**, **I-PEX MHF1 (U.FL)**, 100 mm; stocked at DigiKey 21704215, Arrow, TTI |
| **0466005.NRHF** | `F1` | **B** | LCSC **C57525** 2026-08-23 via the JLCPCB parts API: **29,328 in stock**, JLC **Extended**, 1206, **5 A, 32 VAC / 32 VDC, 50 A interrupting**, fast acting. **Halogen-free ordering option of the same Littelfuse 466 / Nano2 family as the `0466005.NR` it replaces — identical LCSC parametric string, identical footprint. ADOPTED, D-210** |
| **BAT54WS-7-F** | `D10`–`D12` | **B** | LCSC **C124205** 2026-08-23 via the JLCPCB parts API: **46,819 in stock**, JLC **Extended**, **SOD-323**, **1 Independent**, **30 V**, **100 mA** continuous, **600 mA** surge, **V_F 1 V max @ 100 mA**, **I_R 2 µA @ 25 V**. **ADOPTED, D-211** — and see the correction below |
| **FXC.46.52.0075X.B.dg** | off-board | **E** | Taoglas SPE-24-8-104-B; **B variant locked** — adhesive / flex / ferrite, for bonding **inside** the shell (D-131) |

---

## 3. CARRIED — exact MPN present, live listing NOT re-confirmed in this task

> **SUPERSEDED AS A CURRENT SOURCING STATEMENT — D-788 / `R7-N05` (2026-09-20).**  This
> section records the state of an FBV2-S2-001-era task and is retained as HISTORY.  The
> authoritative current sourcing position is the **D-788 live sweep of all 124 assembly
> lines** (`evidence/d788-sourcing-sweep.json`, 2026-09-20) and the consignment table in
> [`FIRST_FIVE_ASSEMBLY_PLAN.md`](FIRST_FIVE_ASSEMBLY_PLAN.md) §18.  Two rows below were
> carried here after they had already been retired elsewhere, which is exactly the defect
> class `R7-D787-19`/`R7-D787-20` named: **`U18` is `LTC4368IMS-1#TRPBF` / `C688401`,
> MSOP-10 — the `LTC4368IDD-1#PBF` / `C688397` DFN code is RETIRED (D-615)** — and the
> board fits **TWO** `PCAL9535APW,118` (`U2`, `U3`), not three.  Read the released BOM
> `hardware/demo/fab/aqroot-Demo-BOM-full.csv` for part identity, never this list.

These are not speculative part numbers; each is an exact, well-known order code already recorded
in the schematic. **They must each be confirmed against a live listing at BOM lock (D-096) and
each needs an LCSC code or an explicit external-purchase decision.**

`ESP32-S3-WROOM-1-N16R8` · `PCAL9535APW,118` (×2, `U2`/`U3`) · `BQ25185DLHR` · `TPS63020DSJR` ·
`TPS61023DRLR` (×2) · `MAX17048G+T10` · `LTC4368IMS-1#TRPBF` (`C688401`, MSOP-10 — *the
`LTC4368IDD-1#PBF` DFN code this row carried until D-788 is RETIRED*) · `TLV7032DDFR` · `TPS61169DCKR` ·
`MAX98357AETE+T` · `BMI270` · `USBLC6-2SC6` · `TPD4E1B06DRLR` (×4) · `NTMD4820NR2G` (×2) ·
`AO3400A` (now `Q1` only — `Q11` moved through `AO3422` at D-766 and to `SQ2364EES-T1_BE3` at D-780) · `AO3401A` · `2N7002` · `BSS138LT1G` (×5) · `PMEG2010AEH,115` ·
`NSR0240HT1G` · `TSAL6100` · `USB4105-GF-A-120` · `B2B-PH-K-S(LF)(SN)` ·
`B2B-PH-K-S` · `BM02B-ACHSS-GAN-ETF` · `JS102011SAQN` · `DMM-4026-B-I2S-R` ·
`AS02008MR-LW152-R` · `FH69-50S-0.5SH` · `XFL4020-472MEC` · `GRM188R61E106KA73D`

---

## 4. MPNs added at FBV2-S2-001

The schematic previously carried only a generic type name on these, which D-096 does not accept
as a selection:

| ref | was | now | manufacturer |
|---|---|---|---|
| `D9` | `PMEG2010AEH` (value only) | **`PMEG2010AEH,115`** | Nexperia |
| `Q4`, `Q6`, `Q7`, `Q8`, `Q9` | `BSS138` (value only) | **`BSS138LT1G`** | onsemi |

Both are jellybeans with many pin-compatible second sources in the same package, so substitution
is a purchasing decision rather than a design change.

---

## 4.1 SUBSTITUTIONS ADOPTED AT FBV2-MECH-002 (2026-08-23)

**Two, and only two. Both CTO-approved, both verified live under D-096, both electrically verified.**

| ref | was | now | LCSC | why it is not a design change |
|---|---|---|---|---|
| `F1` | Littelfuse `0466005.NR` (`C187597`, **stock 0**) | **Littelfuse `0466005.NRHF`** | **`C57525`** (29,328) | Same **466 / Nano2** family, **5 A**, **32 VAC / 32 VDC**, **50 A interrupting**, **fast acting**, **1206**. The `HF` suffix is the manufacturer's **halogen-free ordering option**. Same footprint, same electrical function, **connectivity untouched**. D-210 |
| `D10`–`D12` | Nexperia `BAT54WS,115` (not in the JLC library) | **Diodes Incorporated `BAT54WS-7-F`** | **`C124205`** (46,819) | **One independent Schottky, 30 V, 100 mA continuous, 600 mA surge, SOD-323** — which is **the topology AQROOT actually uses**. Verified against the `D10`/`D11` ratiometric bridge (≈ 1.1 µA per leg, absolute V_F cancels, only ΔV_F survives) and the `D12` dead-cell recovery branch (16.6 mA worst case against 100 mA, **6× margin**; D-105's 5–10 mA band unchanged). D-211 |

> **CORRECTION carried into this ledger — `BAT54WS` IS NOT A SERIES PAIR.** Programme documents
> stated this from FBV2-S2-002 onward. **SOD-323 is a two-terminal package**; every `BAT54WS` in the
> LCSC library, from eight manufacturers, is catalogued **"1 Independent"**; and `D10`/`D11`/`D12`
> are each **one** two-pin `Device:D_Schottky` on a two-pad footprint. **`D10` and `D11` form the
> ratiometric matched-function pair as TWO SEPARATE COMPONENTS.** The **real** rejection criterion for
> any alternate is: single independent diode · SOD-323 land · adequate V_F / leakage / current ·
> matched type for `D10`/`D11` · live sourcing. **Nexperia `BAT54W,115` (`C8657`) stays rejected —
> because it is SOT-323 (SC-70), a FOOTPRINT mismatch, not because of diode count.**

---

## 5. OPEN SOURCING ITEMS

| # | item | severity |
|---|---|---|
| **S-1** | **Only 7 of 46 unique MPNs carry an LCSC code in the schematic.** The JLC Basic/Extended split — and therefore the assembly quote and the manual-placement list — **cannot be completed from the current metadata**. This is a **release blocker**, not a design blocker | **BLOCKER (assembly)** |
| **S-2** | `L5` / `L6` **39 nH NFC EMC inductors have no MPN at all** — they are marked `TUNE` and carry only a value and an 0603 footprint. A tuned RF inductor needs a specified part (Q, I_rms, tolerance) | **BLOCKER (RF)** |
| **S-3** | `L3` `XFL4020-472MEC` carries **no ratings note**; the backlight boost peak current is unquantified in the schematic | **minor** |
| **S-4** | `C65`/`C66` 22 µF 10 V X7R 0805 carry **no DC-bias note**, and their derated value is what sets the boost start-up time (B-69) | **minor — now recorded in B-69** |
| **S-5** | Every "CARRIED" MPN in §3 needs a live-listing confirmation at BOM lock | **BOM-lock gate** |

---

## 6. Magnetics — B-68

| ref | MPN | L | Isat | Irms | peak in circuit | margin | verdict |
|---|---|---|---|---|---|---|---|
| `L1` | XFL4020-152MEC | 1.5 µH | **4.1 A** (10 % drop) | 6.7 A (20 K) | **≈ 2.9 A** — TPS63020 at 2 A out from a 3.0 V cell | **1.4×** on Isat | **adequate — the tightest magnetics margin on the board.** Measure at first article before raising any rail limit |
| `L4` | 74438357010 | 1 µH | **6.2 A** (10 %) / 12.5 A (30 %) | IRP,40K 10.25 A | **2.19 A** — accessory boost at the 0.86 A worst-high limit, V_SYS 3.0 V | **2.8×** | **B-68 CLOSED** |
| `L2` | 74438357010 | 1 µH | as `L4` | — | DNP | — | NFC fallback branch |
| `L3` | XFL4020-472MEC | 4.7 µH | **not recorded** | not recorded | backlight boost, ≈ 1.2 A peak estimated | — | **S-3: record the ratings** |
| `L5`, `L6` | **none** | 39 nH | — | — | NFC EMC filter | — | **S-2: no MPN** |

---

## Q2 / Q3 — **PRE-PCBA BLOCKING: the battery pass pair is unbuyable AND is not guaranteed to be ON**

**D-789 / F-N01 + R8-N01.  DO NOT PAY FOR PCBA UNTIL THIS LINE IS RESOLVED.**

`Q2` and `Q3` are the back-to-back pass pair of the `LTC4368-1` battery
protection circuit: `BAT_RAW → Q2 → BAT_MID → Q3 → BAT_SENSE → R75 →
BAT_PROTECTED_P`, with both devices' gates on `LTC_GATE` and each device's two
internal channels tied source-to-source.  Four channels in series carry the
whole pack current.

### 1. The locked part is not buyable — **F-N01**

| fact | value | evidence |
|---|---|---|
| locked MPN | onsemi **`NTMD4820NR2G`** | schematic `Q2`/`Q3`, BOM |
| live JLCPCB stock | **0** | `evidence/jlc-live/ntmd4820nr2g-*.json`, 2026-09-21 |
| catalogue lifecycle | flagged no longer manufactured; Fable reports onsemi's own page as **Obsolete** | Round-8 review |
| the only same-MPN rows with stock | `-VB` (VBsemi, 45) and `-HXY` (HXY), both **re-marked second sources**, not authorised onsemi product | same record |
| authorised ten-piece allocation | **NOT VERIFIED** | Astra, Round-8 |

This repository can reach the JLCPCB catalogue and not an authorised
distributor's allocation system, so confirming genuine traceable stock is a
**purchasing action** and it is the gate.

### 2. And the fitted part is not guaranteed to be enhanced — **R8-N01, found at D-789**

This is a NEW finding, from applying D-780's own rule — *threshold is an
OFF-state boundary, not a load-current guarantee* — to the pass pair instead of
to `Q11`.

| quantity | value | primary source |
|---|---|---|
| `LTC4368` gate drive `ΔVGATE = GATE − VOUT`, **guaranteed minimum** | **3.0 V** at `VIN = 2.5 V` (4 typ, 5.5 max) | ADI LTC4368 Rev C EC table, archived `vendor/ADI/adi-ltc4368-revC-farnell-2243878.pdf`.  The next guaranteed row is `VIN = 5 V` → 7.2 V min; there is **no guaranteed row between 2.5 V and 5 V**, and this board's `BAT_RAW` lives at 3.0–4.2 V.  `ΔVGATE` is monotonically increasing in `VIN` across the three published rows, so the nearest row **at or below** `VIN` is the bound — the same discipline `F6` uses for `U20`'s `RON` and `F5` for `D14`'s `VF`. |
| source-node offset `VSOURCE − VOUT` at the 2.35 A design current | `Q3` ≈ **87 mV**, `Q2` ≈ **214 mV** | one and three channel drops at `RDS(on)` max 27 mΩ plus `R75` 10 mΩ |
| therefore worst-case `VGS` | `Q3` ≈ **2.91 V**, `Q2` ≈ **2.79 V** | derived |
| `NTMD4820N` `VGS(th)`, **MAXIMUM** | **3.0 V** (1.5 min) at `VDS = VGS`, `ID = 250 mA` | onsemi datasheet, archived `vendor/ONSEMI/onsemi-ntmd4820n-D.pdf` |
| `NTMD4820N` lowest published `RDS(on)` row | **`VGS = 4.5 V`**, 20 typ / **27 max** mΩ | same |

**So in the worst corner the guaranteed gate drive is BELOW the guaranteed
threshold, and there is no published on-resistance anywhere near it.**  On
typical parts (`VGS(th)` ≈ 2.0 V, `ΔVGATE` ≈ 4–7 V at this `VIN`) the pair is
comfortably on, which is why it has never been a symptom — and a typical is not
a release guarantee, which is the whole of D-779, D-780 and D788-11.

**Consequence if it bites:** a higher pass-pair resistance, a larger drop from
the pack and more heat in two SOIC-8s; at the extreme, a board that will not
run from the battery.  It is a FUNCTIONAL risk, not a safety one — the
`LTC4368`'s overcurrent, reverse and UV/OV protection all still act, because
they sense across `R75` and drive the gate down, neither of which depends on
how well the pair conducts.

### 3. Selection criteria for the replacement — **both findings close together**

The part has to be re-selected anyway, so R8-N01 is a criterion of that
selection rather than a separate change.  A candidate must satisfy **all** of:

| # | requirement | why |
|---|---|---|
| 1 | **dual N-channel in the SOIC-8 dual-MOSFET pinout** — 1,3 = sources, 2,4 = gates, 5,6 = D2, 7,8 = D1 | the board ties 1+3 and 2+4; **no PCB change is permitted** |
| 2 | `V(BR)DSS` ≥ **30 V** | retains the fitted part's margin |
| 3 | continuous `ID` ≥ **6 A** per channel at `TA` 25 °C in this package | above the `LTC4368`+`R75` breaker's own maximum trip and the 5 A one-shot fuse |
| 4 | **`VGS(th)` MAXIMUM ≤ 2.5 V** | so the guaranteed 2.79 V at `Q2`'s gate is above the guaranteed threshold **with margin**, which the fitted part is not |
| 5 | a **published `RDS(on)` MAXIMUM row at `VGS ≤ 2.8 V`** if one exists in the market; if none does, the shortfall is NAMED and measured at first article (below) | the honest bar.  Standard SO-8 duals publish 4.5 V and 10 V rows only, so this may be unsatisfiable — say so rather than pretend |
| 6 | four channels in series ≤ **120 mΩ** at the published `VGS = 4.5 V` maximum | keeps the pack-side drop at 2.35 A under 300 mV |
| 7 | live authorised stock ≥ **100** (5 boards × 2 parts × 10 liquidity) and a traceable lifecycle status | D-096 and `rule_open_sourcing` |
| 8 | `Ciss` such that the `LTC4368`'s 30 mA minimum fast pull-down still meets its `tD(FAST)` | the fast turn-off is the protection |

**A CANDIDATE MUST BE READ FROM ITS DATASHEET, NOT FROM A CATALOGUE ROW.**
While deriving this list, the JLCPCB attribute table advertised `YJQ3622A` as a
2-N-channel 30 V part with `VGS(th)` 1 V and 3112 in stock; its datasheet says
**single** N-channel in **DFN3.3×3.3**.  It would not have fitted the land.
That is the seventh entry in the substitution-trap table in
`FIRST_FIVE_ASSEMBLY_PLAN.md` and it is why requirement 1 is first.

### 4. First article — **`C-BAT-GATE-01`**

Whatever is fitted, on the first assembled board **measure `ΔVGATE` (GATE −
`BAT_PROTECTED_P`) and the pass-pair drop (`BAT_RAW` − `BAT_SENSE`) at 2.35 A,
at `BAT_RAW` = 4.15 V, 3.60 V and 3.05 V**, and record all six numbers.  This
is the measurement that converts requirement 5's possible shortfall from an
unknown into a bounded one.

### 5. REV-B

The architectural observation behind R8-N01 is that an `LTC4368` at a 3.0–4.2 V
`VIN` guarantees only 3.0 V of gate drive, while every standard SO-8 dual
publishes its lowest on-resistance at 4.5 V.  **The classes do not meet.**  A
REV-B that either raises the controller's supply or selects a controller with a
higher guaranteed low-`VIN` drive removes the question instead of measuring it.

---
