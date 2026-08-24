# AQROOT Full Beta v2 — sourcing ledger

**Status: SUPERSEDED FOR ASSEMBLY ROUTING by**
[`FIRST_FIVE_ASSEMBLY_PLAN.md`](FIRST_FIVE_ASSEMBLY_PLAN.md) **(FBV2-S2-002, B-71 closed).**
That file carries the live LCSC/JLC state, the A–F class for every part and the consignment
plan. **This file remains normative for the sourcing *evidence* behind each MPN.**

**Status: NORMATIVE for the first five boards.** Generated 2026-08-23 at FBV2-S2-001 from the
schematic, not from a spreadsheet. Authority: [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md).

**D-096 applies throughout: a part number configured from an ordering scheme is a hypothesis, not
a selection, until a live manufacturer or distributor record confirms lifecycle and stock.**

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
| **BCS-112-S-D-HE** | `J5` | **C** | Samtec product page 2026-08-23: **Part Status ACTIVE, 385 pcs ship tomorrow**, $7.314 @1 / $5.667 @100, UL E111594, MSL 1. **Through-hole → manual/secondary assembly** |
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
| **095-902-568-150** | off-board | **E** | Amphenol RF product page 2026-08-23: **Part Status ACTIVE** — AMC R/A plug → **SMA straight bulkhead jack, IP67**, RG-178, 50 Ω, **150 mm**, 6 GHz max |
| **FXP450.07.0100C** | off-board | **E** | Taoglas SPE-23-8-180-A; **410–470 MHz**, **I-PEX MHF1 (U.FL)**, 100 mm; stocked at DigiKey 21704215, Arrow, TTI |
| **FXC.46.52.0075X.B.dg** | off-board | **E** | Taoglas SPE-24-8-104-B; **B variant locked** — adhesive / flex / ferrite, for bonding **inside** the shell (D-131) |

---

## 3. CARRIED — exact MPN present, live listing NOT re-confirmed in this task

These are not speculative part numbers; each is an exact, well-known order code already recorded
in the schematic. **They must each be confirmed against a live listing at BOM lock (D-096) and
each needs an LCSC code or an explicit external-purchase decision.**

`ESP32-S3-WROOM-1-N16R8` · `PCAL9535APW,118` (×3) · `BQ25185DLHR` · `TPS63020DSJR` ·
`TPS61023DRLR` (×2) · `MAX17048G+T10` · `LTC4368IDD-1#PBF` · `TLV7032DDFR` · `TPS61169DCKR` ·
`MAX98357AETE+T` · `BMI270` · `USBLC6-2SC6` · `TPD4E1B06DRLR` (×4) · `NTMD4820NR2G` (×2) ·
`AO3400A` · `AO3401A` · `2N7002` · `BSS138LT1G` (×5) · `PMEG2010AEH,115` · `BAT54WS,115` (×3) ·
`NSR0240HT1G` · `TSAL6100` · `0466005.NR` · `USB4105-GF-A-120` · `B2B-PH-K-S(LF)(SN)` ·
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
