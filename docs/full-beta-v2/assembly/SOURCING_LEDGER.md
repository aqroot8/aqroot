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
| **TPS22950CDDCR** | `U20`, `U22` | **B/D** | TI product page 2026-08-23: **ACTIVE**, DDC SOT-23-THN 6-pin |
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

These are not speculative part numbers; each is an exact, well-known order code already recorded
in the schematic. **They must each be confirmed against a live listing at BOM lock (D-096) and
each needs an LCSC code or an explicit external-purchase decision.**

`ESP32-S3-WROOM-1-N16R8` · `PCAL9535APW,118` (×3) · `BQ25185DLHR` · `TPS63020DSJR` ·
`TPS61023DRLR` (×2) · `MAX17048G+T10` · `LTC4368IDD-1#PBF` · `TLV7032DDFR` · `TPS61169DCKR` ·
`MAX98357AETE+T` · `BMI270` · `USBLC6-2SC6` · `TPD4E1B06DRLR` (×4) · `NTMD4820NR2G` (×2) ·
`AO3400A` · `AO3401A` · `2N7002` · `BSS138LT1G` (×5) · `PMEG2010AEH,115` ·
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
