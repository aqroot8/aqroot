# AQROOT Full Beta v2 — first-five assembly plan (B-71)

**Status: NORMATIVE.** Created 2026-08-23 at **FBV2-S2-002**, closing **B-71**.

> **This is not a requirement that every part be available from LCSC.** It is a requirement that
> **every part has an explicit first-five assembly plan.** A part that cannot be bought from LCSC
> is not a problem; a part with no stated route to the board is.

**Every LCSC/JLC figure below was read live on 2026-08-23 through the JLCPCB parts API**
(`selectSmtComponentList`), under **D-096**. **Stock is a snapshot, not a guarantee** — re-check
immediately before ordering, because six of the shortfalls below are single- or low-double-digit
quantities that will move.

---

## 1. The classes

| class | meaning | route to the board |
|---|---|---|
| **A** | JLC **Basic** library, in stock | machine-placed, no placement fee |
| **B** | JLC **Extended**, stock ≥ 2 × first-five need | machine-placed |
| **C** | JLC **Extended**, **stock short of the first-five need** | **buy from a broadline distributor and CONSIGN to JLC** — stays machine-placed |
| **D** | **not in the LCSC/JLC library at all** | consign, or adopt a **documented** equivalent after sign-off |
| **E** | through-hole / mechanically manual **by construction** | hand-soldered after reflow |
| **F** | **off-board** — never placed on this PCB | see [`OFF_BOARD_BOM.md`](OFF_BOARD_BOM.md) |

**Class C is the important one.** It exists so that a stock shortfall never turns into a
hand-assembly decision. **Consignment keeps fine-pitch parts on the machine.**

---

## 2. Class A — JLC Basic

| part | ref | LCSC | stock |
|---|---|---|---|
| `2N7002` | `Q10` | `C8545` | 2,334,365 |
| `AO3401A` | `Q5` | `C15127` | 538,825 |
| generic 0402 / 0603 / 0805 R and C | 127 R, 80 C | Basic library | abundant |

The 207 anonymous passives are the bulk of the placement count and are entirely Basic. **They were
deliberately not consolidated** — value consolidation before a layout exists optimises the wrong
thing, and that decision stands from FBV2-S2-001.

---

## 3. Class B — JLC Extended, comfortably in stock

| part | ref | LCSC | stock | need (5 boards) |
|---|---|---|---|---|
| `ESP32-S3-WROOM-1-N16R8` | `U1` | `C2913202` | 53,139 | 5 |
| `MAX98357AETE+T` | `U5` | `C910544` | 18,844 | 5 |
| `TSOP38238` | `U6` | `C141632` | 22,529 | 5 |
| `E07-400M10S` | `U7` | `C2965513` | 803 | 5 |
| `E22-900M22S` | `U8` | `C411293` | **24** | 5 |
| `USBLC6-2SC6` | `U10` | `C7519` | 41,662 | 5 |
| `BQ25185DLHR` | `U11` | `C19725033` | 671 | 5 |
| `TPS63020DSJR` | `U12` | `C15483` | 7,952 | 5 |
| `TPS61023DRLR` | `U21` (`U13` **DNP**) | `C919459` | 7,872 | **5** |
| `MAX17048G+T10` | `U14` | `C2682616` | 15,822 | 5 |
| `TCA4307DGKR` | `U16` | `C880333` | 4,181 | 5 |
| `TPS61169DCKR` | `U17` | `C71045` | 4,405 | 5 |
| `TPS22950CDDCR` | `U20`, `U22` | `C7587833` | 241 | 10 |
| `BMI270` | `U4` | `C2836813` | 12,840 | 5 |
| `TPD4E1B06DRLR` | `D2`–`D5` | `C1972953` | 2,176 | 20 |
| `PMEG2010AEH,115` | `D9` | `C110921` | 32,772 | 5 |
| `MHPA3528RGBCT` | `D13` | `C409779` | 70,369 | 5 |
| `BSS138LT1G` | `Q4`, `Q6`–`Q9` | `C82045` | 762,522 | 25 |
| `GRM188R61E106KA73D` | `C24`, `C26` | `C344022` | 675,039 | 10 |
| `XFL4020-152MEC` | `L1` | `C3033018` | 20,020 | 5 |
| `XFL4020-472MEC` | `L3` | `C5156236` | 1,987 | 5 |
| `LQW18AN39NG80D` | `L5`, `L6` | `C2042966` | 270 | 10 |
| `PTS645SM43SMTR92LFS` | `SW1`–`SW7` | `C221880` | 8,432 | 35 |
| `JS102011SAQN` | `SW9` | `C221660` | 931 | 5 |
| `USB4105-GF-A-120` | `J3` | `C5184243` | 2,454 | 5 |
| `5025700893` | `J2` | `C429846` | 11,005 | 5 |
| `B2B-PH-K-S(LF)(SN)` | `J4`, `J6` | `C131337` | 378,913 | 10 |
| `BM02B-ACHSS-GAN-ETF(LF)(SN)` | `J7` | `C5118738` | 16,260 | 5 |
| `TXM27.12M0004322DBBDO00T` | `Y1` | `C362365` | 3,421 | 5 |
| `FH69-50S-0.5SH` | `J1` | JLC library, no public LCSC code | **1,072** | 5 |

**`J1` moved.** FBV2-S2-001 recorded the display connector as manual assembly. That ruling came
from **B-47** — there is no drop-in second source — but it does not follow that JLC cannot place
it. **JLC carries the genuine Hirose `FH69-50S-0.5SH` with 1,072 in stock.** `J1` is
**machine-placed**, and the single-source risk stays exactly what D-194 says it is.

---

## 4. Class C — in the library, but stock is short of the build

**These are the parts that decide whether this build succeeds.** Every one is bought from a
broadline distributor and **consigned to JLC**, so it stays machine-placed.

| part | ref | LCSC | stock | need | shortfall |
|---|---|---|---|---|---|
| **`PCAL9535APW,118`** NXP | `U2`, `U3`, `U23` | `C2669683` | **1** | **15** | **−14** |
| **`NTMD4820NR2G`** onsemi | `Q2`, `Q3` | `C905372` | **0** | 10 | −10 |
| **`TLV7032DDFR`** TI | `U19` | `C2871498` | **0** | 5 | −5 |
| **`74438357010`** Würth | `L4` (`L2` **DNP**) | `C5542269` | **0** | **5** | **−5** |
| **`0466005.NR`** Littelfuse | `F1` | `C187597` | **0** | 5 | −5 |
| **`DMM-4026-B-I2S-R`** PUI | `MK1` | `C3171792` | **0** | 5 | −5 |
| **`BCS-112-S-D-HE`** Samtec | `J5` | `C5575816` | **0** | 5 | −5 (also class E) |
| **`LTC4368IDD-1#PBF`** ADI | `U18` | `C688397` | **4** | 5 | **−1** |
| **`ST25R3916-AQET`** ST | `U9` | `C5267441` | **6** | 5 | +1 spare only |
| **`NSR0240HT1G`** onsemi | `D8` | `C152519` | **7** | 5 | +2 spare only |

**`U2`/`U3`/`U23` is the headline.** Three PCAL9535A per board is **fifteen TSSOP-24 at 0.65 mm
pitch** for the first five, against **one** in stock. That is precisely the case the CTO ruling
names: *"if the result would require manually installing dozens of fine-pitch parts per board,
that is NOT acceptable."* **It does not, because consignment exists.** Fifteen plus spares from
Digi-Key/Mouser, shipped to JLC with the order, machine-placed.

**`U9` is the one that genuinely could not be hand-built.** A UFQFPN-32 5 × 5 with an exposed pad
is not a hand-placement candidate at any skill level without a stencil and reflow. Six in stock
against a need of five is a build with **one** spare; **buy spares independently and consign.**

---

## 5. Class D — not in the LCSC/JLC library

| part | ref | finding | plan |
|---|---|---|---|
| **`BAT54WS,115`** Nexperia | `D10`–`D12` | **Not in the library at all.** A search for the string returns Nexperia **`BAT54W,115`** (`C8657`) — the **single** diode, **not the series pair** | Consign the Nexperia part **or** adopt **Diodes Inc. `BAT54WS-7-F`**, `C124205`, **46,819** in stock — same SOD-323 series-pair Schottky. **Documented, not adopted:** it needs a one-line sign-off before the order |

---

## 6. Class E — manual by construction

| part | ref | why |
|---|---|---|
| `BCS-112-S-D-HE` Samtec | `J5` | 24 × Ø0.71 mm through-hole community header. **Kept and marked manual/secondary assembly by CTO ruling at FBV2-S1-009 — the connector architecture is not compromised for SMT** |
| `TSAL6100` | `D1` | 5 mm through-hole IR emitter, `C111836`, 14,817 in stock |

**Two through-hole parts per board.** That is the entire manual scope.

---

## 7. Class F — off-board

Speaker `LS1` (`AS02008MR-LW152-R`, `C3311653`, stock 0 — consign or buy direct), display module,
battery pack, both antennas, the AMC→SMA pigtail and the 915 MHz whip. All in
[`OFF_BOARD_BOM.md`](OFF_BOARD_BOM.md).

---

## 8. Six substitution traps found while building this table

**A loose keyword search against the JLC library returns a plausible wrong part more often than it
returns nothing.** Every one of these would have shipped silently.

| ref | intended | what a loose search returns | why it is wrong |
|---|---|---|---|
| `D10`–`D12` | Nexperia `BAT54WS,115` | Nexperia **`BAT54W,115`** `C8657` | **`BAT54W` is a single diode; `BAT54WS` is a series pair.** Different device |
| `SW1`–`SW7` | C&K `PTS645SM43SMTR92LFS` | G-Switch **`GT-TC089A-H043-L1`** `C843623` | **Different manufacturer**, land pattern never checked against the C&K G-Type layout this footprint was built from — and it is **35 placements** |
| `D8` | onsemi `NSR0240HT1G` | FUXINSEMI **`SD103AWS`** `C915626` | **Different part number entirely** |
| `Q4`, `Q6`–`Q9` | onsemi `BSS138LT1G` | LRC **`LBSS138LT1G`** `C8490` | Different manufacturer — **and the genuine onsemi part has 762,522 in stock**, so there is no reason to accept it |
| `L2`, `L4` | Würth `74438357010` | KOHERelec **`SPM4030-1R0M`** `C2761910` | Different manufacturer's inductor in a switching regulator |
| `Q2`, `Q3` | onsemi `NTMD4820NR2G` | VBsemi **`NTMD4820NR2G-VB`** `C7525084` | Clone in the **battery reverse-polarity pass path**. The CTO ruling forbids silent substitution of power-path parts |

**Each of these is now recorded in the schematic symbol itself**, so the warning travels with the
design instead of living only in this file.

---

## 9. Two MPN strings were wrong in a way that mattered

Both were found by cross-checking the BOM against live listings rather than by reading the
schematic.

- **`J4` and `J6` are the same JST PH 2-pin header but carried two different MPN strings** — `J4`
  the `(LF)(SN)` plating suffix, `J6` the bare order code. That is **not cosmetic**: the bare code
  resolves to `C20504437` with **stock 0**, while **`B2B-PH-K-S(LF)(SN)` is `C131337` with 378,913
  in stock.** Both are now the stocked string.
- **`J7` had the same problem.** `BM02B-ACHSS-GAN-ETF` → `C20088622`, **stock 0**;
  **`BM02B-ACHSS-GAN-ETF(LF)(SN)` → `C5118738`, 16,260 in stock.** Corrected.

A BOM that produces two lines for one part, one of which cannot be filled, is a BOM that stalls at
the quote stage. **`L2`/`L4` also carried two spellings of "Würth"** and were normalised.

---

## 10. The assembly reality check

| question | answer |
|---|---|
| how many distinct MPNs? | **46** (43 after the two duplicate-string merges and one manufacturer-spelling merge) |
| how many parts machine-placed? | **all but two per board** |
| how many hand-soldered per board? | **2** — `J5` (24-pin THT) and `D1` (5 mm THT LED) |
| how many fine-pitch/QFN parts hand-placed? | **zero** |
| how many parts need consignment? | **10 (class C) + 1 (class D)** |
| DNP parts with no recorded reason | **zero** — eight were still undocumented at the start of FBV2-S2-002 and all eight now carry one |
| does the build close today? | **Yes, via consignment.** It does **not** close as a pure LCSC turnkey order |

**Do not optimise cents. Optimise first-build success.** The consignment fee on eleven part
numbers is trivial against one failed board or one wrong-part respin.

---

## 11. What this plan does **not** claim

- It does **not** claim any of these stock figures will still hold when the order is placed.
- It does **not** adopt a single substitute part. `BAT54WS-7-F` and `0466005.NRHF` are recorded as
  **candidates awaiting sign-off**, not as decisions.
- It does **not** cover the anonymous passive values, which stay unconsolidated until the layout
  exists.
