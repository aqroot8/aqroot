# FBV2-S2-001 — Pre-placement release audit

**Task:** whole-schematic / BOM / footprint / procurement / assembly release audit before PCB
placement. **Date:** 2026-08-23. **Starting SHA: `b1b6c65`** (working tree clean, local `master`
identical to `origin/master`; the only untracked paths were the two present since 2026-08-20/21,
neither touched).

> ## VERDICT: **FBV2-S2 = FAIL — on two of the fourteen exit criteria.**
>
> **The audit did its job.** It found a **fabrication-blocking defect that would have produced a
> board with a complete NFC antenna and no NFC chip**, corrected it, and closed nine stale
> register entries. Everything else on the gate passes: ERC has zero errors, every active and
> connector now carries an exact MPN, every DNP is explained, every rail is continuous, every
> strap is intact and the PCB is untouched.
>
> **What fails:** eight critical footprints are traceable to a vendor part but **have not been
> read against a manufacturer drawing**, and the **JLC/LCSC assembly classification cannot be
> completed** because only 7 of 46 unique MPNs carry an LCSC code. Both are fabrication-release
> blockers. **Neither blocks PCB placement.**

---

## 1. THE FINDING — NFC was still marked DNP

`U9` **ST25R3916-AQET** and its twelve mandatory supply-decoupling capacitors (`C19`, `C45`–`C55`)
were inherited from Beta-DM marked **DNP**, against two standing decisions:

> **D-035:** *"NFC is mandatory in the FIRST Full Beta v2 fabrication. **No DNP showcase
> shortcut.**"*
> **D-055:** *"**NFC must be FITTED and functional on the first fabrication.**"*

Everything around it was already FITTED — the 27.12 MHz crystal `Y1`, the complete differential
matching network `C69`–`C80` / `L5` / `L6` / `R114`–`R117`, the antenna connector `J7`, the SPI
wiring, the `NFC_SUPPLY` 3.3 V selector `R106`. **The first five boards would have been built with
a finished 13.56 MHz front end and no NFC chip on it.**

All thirteen parts are now **FIT**. Twelve of them are mandatory supply decoupling in DS12484 —
`NFC_SUPPLY`, `VDD_D`, `VDD_A`, `VDD_RF`, `VDD_AM` and `AGDC` — not options.

**This is the seventh consecutive sheet on which an inherited `DNP` was load-bearing.** Sheets 06,
07, 08 and 09 each carried one; this one survived four migrations because sheet 04's *own*
migration (FBV2-S1-004/4B/4C) was about the antenna and the matching network, and nobody re-read
the population state of the IC underneath it.

**Six `U9` pins remain deliberately unconnected** — `CSO`, `EXT_LM`, `AAT_A`, `AAT_B`, `CSI`,
`MCU_CLK`. Capacitive sensing, external load modulation, antenna auto-tuning and the MCU clock
output are optional features this product does not use, and each carries a recorded ERC exclusion.

---

## 2. O-7 — CLOSED as Option A

**`R49` = `R50` = 1.5 kΩ, locked.** Community external I²C contract, to appear in accessory
documentation:

> **400 kHz: total external bus capacitance ≤ 200 pF. 100 kHz: ≤ 400 pF.**

**Not changed to 1.0 kΩ merely to extend the 400 kHz capacitance claim.** NXP **UM10204** treats a
simple resistor pull-up as the normal Fast-mode solution **up to 200 pF**, and prescribes a
current-source or switched-resistor arrangement above it. AQROOT does not need that complexity for
a hobby-accessory port. Retained unchanged: **TCA4307DGKR**, the 1.5 kΩ external pull-ups, the
**22 Ω** series elements and the **100 kHz fallback**.

---

## 3. Open-item register reconciliation

**Nine entries were stale.** They were carried as open only because historical text existed.

| # | was | now | evidence |
|---|---|---|---|
| **P-01** | Reverse-polarity architecture open | **CLOSED — STALE** | `F1` → `BAT_RAW` → `Q2` → `BAT_MID` → `Q3` → `BAT_SENSE` → `R75` 15 mΩ → `BAT_PROTECTED_P`, with `U18` LTC4368-1 driving both gates, all FITTED and measured in the netlist. **FBV2-A1 passed 2026-08-22** |
| **P-04** | NFC first-fab inclusion and antenna implementation | **CLOSED — STALE** | IC, crystal, matching network, `FXC.46.52.0075X.B.dg` antenna, `J7`, 3.3 V supply and the preserved 5 V fallback all exist — **and as of §1 the IC is actually fitted** |
| **P-14** | MAX17048 sense point | **RESOLVED — see §4** | |
| **P-18** | I²C segmentation | **CLOSED at FBV2-S1-009** (D-178) | no mux |
| **B-45** | `NATIVE_A`/`NATIVE_B` unprotected | **CLOSED — STALE** | `R61`/`R62` 100 Ω plus two `D2` TVS channels landed at FBV2-S1-009 |
| **B-46** | SD detect polarity assumed | **CLOSED — see §7** | Molex drawing |
| **B-49** | IPEX socket population unconfirmed | **CLOSED** | Ebyte's own product description: both `E07-400M10S` and `E22-900M22S` ship with **IPEX *and* stamp holes** on the standard MPN. No variant selection exists to get wrong |
| **B-51** | 915 MHz pigtail MPN not selected | **CLOSED — see §6** | Amphenol `095-902-568-150` |
| **B-53** | NFC antenna architecture undecided | **CLOSED — STALE** | Decided by **D-131**: purchased flex + ferrite, **B variant**, locked |
| **B-68** | inductor saturation | **CLOSED — see §8** | Würth data already in the schematic |
| **B-47** | FH52E second source | **RESOLVED — see §5** | both Hirose land patterns compared |
| **B-69** | boost start-up delay | **RESOLVED WITH A CORRECTION — see §9** | |

**Genuine blockers that remain** are in §14.

---

## 4. P-14 — MAX17048 sense point: **KEEP IT ON `BAT_PROTECTED_P`. NO CHANGE.**

**The gauge is not on `BAT_RAW`, and never was.** Measured from the netlist, `U14` `CELL` (pin 2)
and `VDD` (pin 3) are **both already on `BAT_PROTECTED_P`** — the fully protected node, after
*both* back-to-back FET stages **and** after the 15 mΩ sense resistor.

The CTO asked whether the cleaner node **after `P2` but before `R75`** — which is **`BAT_SENSE`** —
should be used instead. **It should not.**

**What moving would gain.** `R75` = 15 mΩ. At the 1.75 A pack worst case the drop is **26 mV**; at
a typical 300 mA idle, **4.5 mV**; during a 500 mA charge, **7.5 mV** of opposite sign. On a Li-ion
discharge curve of roughly 10 mV per SOC-% in the useful region that is **≤ 2.6 % at peak load and
< 0.5 % at typical load** — and it is load-correlated, so it is worst exactly when it matters.

**Why that is not worth taking.** `BAT_SENSE` is the **LTC4368's precision current-sense input**.
It measures `SENSE − VOUT` across `R75` to detect reverse current.

1. **Decoupling asymmetry.** The gauge needs a bypass capacitor on `VDD`. Putting one on
   `BAT_SENSE` but not on `VOUT` creates a **differential capacitance across the sense resistor**,
   which distorts the reverse-current comparator's view during fast current steps. That is a
   direct attack on the protection the whole P2 architecture exists to provide.
2. **A blind spot.** The gauge's supply current would be drawn **downstream of the FETs but
   upstream of the sense resistor**, so the LTC4368 would not see it. Small — 23 µA, worth
   0.35 µV across `R75` — but it is a hole in a protection measurement, deliberately created.
3. **Transient injection.** I²C activity and the MAX17048's quick-start would inject onto the
   sense node.

**And the gain is inside the noise anyway.** The MAX17048 is a **voltage-based ModelGauge** part;
its own SOC model error without cell characterisation is coarser than 26 mV of series drop.

> **RULING: the MAX17048 stays on `BAT_PROTECTED_P`. Safety outranks SOC accuracy, exactly as
> directed. The retained error is quantified above and is a firmware compensation opportunity —
> the gauge can subtract `I × 15 mΩ` if the charger current is known — not a hardware problem.**

**Checks performed and passed:** no sneak or back-power path (the gauge sits behind both FET
stages); the gauge's I²C cannot bypass `P2` (SCL/SDA are logic lines to the MCU, not a power
path); its decoupling is on the bulk node with `C25`/`C36`/`C58`, not on the sense node; dead-cell
recovery is unaffected (that branch works on `BAT_RAW` and the recovery FET); charge measurement
remains valid; and the node cannot exceed cell voltage in any of the thirteen fault cases because
both FET stages are anti-series.

---

## 5. B-47 — display connector: **OUTCOME B, NOT COMPATIBLE**

Both Hirose land patterns were read.

| | **FH69-50S-0.5SH** (locked) | **FH52E-50S-0.5SH** (proposed second source) |
|---|---|---|
| contact system | **top AND bottom, 2-point** | **BOTTOM contact only** |
| actuator | **back-flip** | **front flip** |
| height | 2.3 mm | 2.0 mm |
| signal land | **0.30 × 1.23** | **0.30 wide**, 0.8 land, 4.6 depth datum |
| overall layout depth | **7.38 mm** | **4.6 mm** |
| hold-downs | 0.36 × 4.25, span 28.73 c/c | different |
| FPC | t = 0.30 ± 0.05 gold | t = 0.30 ± 0.05 gold — **the only thing they share** |
| the catalogue's own statement | — | *"The recommended PCB mounting pattern for the **FH12 Series** can be used as well"* |

**They are different land patterns — 7.38 mm deep versus 4.6 mm. They cannot share pads.**

> ### DOCUMENTATION CORRECTION
> **D-077 states that `J1` is *"laid out on the FH12/FH52E standard land pattern so
> `FH52E-50S-0.5SH` (LCSC C7465440) is a drop-in second source."* THAT IS FALSE, and the two
> manufacturer drawings say so.** FH52's pattern is interchangeable with **FH12**, not with FH69.
> Placement would otherwise have proceeded believing a second source existed. **The claim is
> struck.**

**Ruling:** keep the dedicated, vendor-exact FH69 footprint. **`J1` is MANUAL ASSEMBLY for the
first five.** The CTO priority is explicit and correct: *"For five prototypes, manual placement and
soldering of a proven FH69 is preferable to a speculative footprint migration."* Beyond the land
pattern, FH52E would also give up the **two-point top-and-bottom contact** that D-076/D-077 chose
FH69 for on a 50-way flex carrying both the display and the touch panel.

---

## 6. RF interfaces — B-49, B-51 closed

**Module variants (B-49): no risk exists.** Ebyte's own product description states the
`E07-400M10S` "comes in the form of dual antennas (**IPEX/stamp hole**)" — the standard part number
carries **both**. The same is documented for the `E22-900M22S`. There is no IPEX-versus-stamp
ordering choice to get wrong.

**433 MHz:** **Taoglas `FXP450.07.0100C`** — SPE-23-8-180-A, **410–470 MHz** (the module covers
410–450), **I-PEX MHF1 (U.FL)**, 100 mm cable, adhesive. Stocked at DigiKey **21704215**, Arrow,
TTI, Symmetry.

**915 MHz (B-51 CLOSED): Amphenol RF `095-902-568-150`** — manufacturer page 2026-08-23, **Part
Status ACTIVE**: **AMC right-angle plug → SMA straight bulkhead jack, IP67**, RG-178, **50 Ω**,
**150 mm**, 6 GHz max, RoHS. Amphenol's AMC series is documented **"compatible with Hirose U.FL and
IPEX MHF1"**.

**It is one assembly — the pigtail and the panel bulkhead are the same orderable part, so no
separate bulkhead MPN is needed.** Loss ≈ **0.4 dB** at 915 MHz (RG-178 ≈ 1.2 dB/m over 150 mm plus
two interfaces) against a +22 dBm module. The right-angle plug keeps the vertical stack low over a
flat-lying module. **No PCB RF routing was added.**

**Still open: O-8 — the 915 MHz external whip antenna MPN is not selected.** Everything from the
module to the bulkhead is now locked; the antenna on the outside of the panel is not. It is an
accessory-class purchase with no board impact.

---

## 7. B-46 — microSD card detect: **CLOSED, and the assumption was right**

Read from the Molex sales drawing **SD-502570-001 Rev A**, sheet 1 of 2, note 4, the
*DETECT SWITCH* table:

| condition | state |
|---|---|
| **CARD INSERTING POSITION** | **CLOSE** |
| **NO CARD** | **OPEN** |

Against the circuit — `J2.11` `DETECT_LEVER` → **GND** (the drawing's own recommended pattern
labels the lever land *"Vss : GROUND"*), `J2.10` `DET-SW` → `SD_CARD_DETECT_N` with `R113` 100 kΩ
to `+3V3`:

- **card inserted → switch closed → `SD_CARD_DETECT_N` LOW**
- **no card → switch open → pull-up → HIGH**

**`LOW = card present`, exactly as D-117 assumed. No firmware correction and no hardware change.**

---

## 8. B-68 — magnetics: **CLOSED**

The data was already in the schematic and had simply never been checked against the circuit.

| ref | MPN | Isat | peak in circuit | margin |
|---|---|---|---|---|
| **`L4`** accessory boost | **74438357010** | **6.2 A** (10 % drop) / 12.5 A (30 %) | **2.19 A** at the 0.86 A worst-high current limit with `V_SYS` 3.0 V | **2.8× — B-68 CLOSED** |
| `L1` main TPS63020 | XFL4020-152MEC | 4.1 A (10 %) | ≈ **2.9 A** at 2 A out from a 3.0 V cell | **1.4× — adequate, and the tightest magnetics margin on the board** |

**Two stale "FOOTPRINT STILL BLOCKED" notes were withdrawn.** `L1` and `L2` both carried a note
saying the recommended land pattern could not be resolved from text extraction. **Both land
patterns were subsequently built from the manufacturer drawings** — Coilcraft 745-3 rev 03/10/26
and Würth rev 003.001 — with dimensions read off the leader lines. The notes were describing a
problem that had already been solved, which is exactly the kind of stale text that makes a
register untrustworthy.

**`L3` (XFL4020-472MEC, backlight) carries no ratings note and `L5`/`L6` have no MPN at all** —
see §14.

---

## 9. B-69 — boost start-up: **the 5 ms was derived against the wrong capacitance**

SLVSDK9 gives **t_SS = 700 µs typical**, and FBV2-S1-009 called the locked 5 ms wait "seven times
typical". **Reading the condition line changes that.** The 700 µs is specified at
**V_IN 2.5 V, V_OUT 5 V, C_OUT_EFF = 10 µF, no load.**

`C65` + `C66` are **2 × 22 µF 10 V X7R 0805**. At 5 V DC bias an 0805 10 V X7R typically retains
40–60 % of nominal, so **C_OUT_EFF ≈ 20 µF — about twice the datasheet condition**. Start-up is
dominated by charging that capacitance, so the scaled typical is **≈ 1.4 ms**, and the real margin
on a 5 ms wait is **≈ 3.5×, not 7×**. The datasheet publishes **no maximum** for t_SS.

> **RULING: raise the first-build wait from ≥ 5 ms to ≥ 10 ms.** It restores ~7× against the
> scaled typical, it is a firmware constant with **zero hardware cost**, and it happens once per
> accessory insertion behind an MX-4 delay that already spends 5 ms. **Measure it at first article
> and reduce it if desired.** **No PGOOD IC is added.**

The FBV2-S1-009 argument that made the number trustworthy still holds and is what makes measuring
it meaningful: **the load switch is OFF during boost start-up**, so the converter starts into a
known board capacitance, never into an unknown hot-plugged accessory.

---

## 10. Population, BOM and sourcing

Full detail: [`../assembly/FIRST_FIVE_POPULATION_MATRIX.md`](../assembly/FIRST_FIVE_POPULATION_MATRIX.md),
[`../assembly/SOURCING_LEDGER.md`](../assembly/SOURCING_LEDGER.md),
[`../assembly/OFF_BOARD_BOM.md`](../assembly/OFF_BOARD_BOM.md).

| measure | value |
|---|---|
| schematic components | **322** |
| **FITTED** | **306** (was 293 — the thirteen NFC parts) |
| **DNP** | **16** (was 29) |
| off-board on the schematic | 1 (`LS1`) |
| test points | 47 |
| unique MPNs | **46** |
| actives + connectors | 62, **all with an exact MPN — 0 missing** |
| **unexplained DNP** | **0** |

**Six MPNs were added**: `D9` → `PMEG2010AEH,115` (Nexperia) and `Q4`/`Q6`/`Q7`/`Q8`/`Q9` →
`BSS138LT1G` (onsemi). The schematic previously carried only the generic type name, which D-096
does not accept as a selection.

**Two undocumented placeholders were resolved:**

- **`R68` 0 Ω DNP is a bypass ACROSS `SW9`, the hard power switch.** Fitting it wires the unit
  permanently ON and **defeats the one provision that lets a user power down a hung or unflashed
  board** — the architecture is explicit that `SW9` is not a GPIO for exactly that reason. It
  arrived with no note at all. It is now documented as **DNP AND IT MUST STAY DNP**, bench use only.
- **`C21`/`C22` 100 pF DNP are dead pads** — one terminal is deliberately no-connect flagged, so
  fitting them does nothing. Reserved 0603 rework pads by the USB block, usable only by cutting a
  trace. Documented, and flagged as a deletion candidate at placement.

---

## 11. Electrical audits

**Cross-sheet connectivity — PASS.** Every endpoint pair in the brief's list was re-read from the
netlist, not from label spelling: display SPI-A, touch I²C and `TOUCH_INT_N`, `SD_CARD_DETECT_N`,
both radios, NFC IRQ and SPI, `BMI270_INT1_STRAP`, the I²S bus, IR TX and RX, the three-way
`WAKE_INT_N` wire-OR, `BQ25185_STAT1/2`, `ACC_POWER_FAULT_N`, `ACC_DETECT_N`, **both split 5 V
enables**, `XGPIO0`–`9`, `NATIVE_A`/`NATIVE_B` and the external I²C pair. All resolve.

**Power and ground hierarchy — PASS.** Every rail is continuous with a sane node count: `GND` 236,
`+3V3` 86, `BQ25185_SYS` 16, `ACC_3V3_SW` 14, `BAT_RAW` 12, `USB_VBUS_CHG` 11, `BAT_PROTECTED_P`
10, `USB_VBUS_RAW` 7, `ACC_5V_SW` 7, `NFC_SUPPLY` 7, `ACC_5V_RAW` 6, `LED_BOOST` 6, `BAT_SENSE` 5.

**The sheet-09 failure mode does not recur.** A scan for the same local-label text appearing on
more than one sheet — the exact way `01:ACC_3V3_SW` and `09:ACC_3V3_SW` silently became different
nets — returns **zero hits** across the whole design. **There are also zero one-pin nets.**

**All seven `PWR_FLAG`s are legitimate** and none hides a disconnected supply: `#FLG0101`
`USB_VBUS_CHG`, `#FLG0102` `BAT_PROTECTED_P`, `#FLG612` `BAT_RAW`, `#FLG613` `VREC_VCC`, `#FLG614`
`NFC_SUPPLY`, `#FLG0103` `IR_RX_VS_LOCAL`, `#FLG0105` **GND** — the design's only power-output
driver. Each sits on a net whose real source reaches it through a passive (a connector pin, a fuse,
a 0 Ω selector or a series resistor), which is precisely the case ERC needs a flag for.

**ESP32 strap and safe-state — PASS, unchanged.** GPIO0 `BOOT_N` (`R2` 10 k up + `SW1`), GPIO3
`BMI270_INT1_STRAP` (`R110` 10 k down + `R18` 220 Ω + `TP3`), GPIO45 (`R111` 10 k down + `TP1`),
GPIO46 (`R108` 10 k down + `R109` 0 Ω + `TP2`). **No peripheral was added to any strap; the
physical BOOT path is intact.** All active-low resets and enables keep their external pulls, and
the PCAL firmware contract is unchanged: **write the Output Port register BEFORE the Configuration
register**.

**USB-C sink correctness — checked for the first time:** `CC1` and `CC2` each carry a **5.1 kΩ**
Rd (`R30`, `R31`) and the shield returns through `R32` 0 Ω. Without those the port would never be
supplied by a Type-C source.

---

## 12. Footprints

Full ledger: [`../assembly/FOOTPRINT_VERIFICATION_LEDGER.md`](../assembly/FOOTPRINT_VERIFICATION_LEDGER.md).

**Every footprint reference in the design resolves against a library.** One symbol carries no
footprint — `LS1`, the off-board wired speaker — which is correct.

| tier | count | meaning |
|---|---|---|
| **1 — manufacturer-drawing verified with a cited document number and revision** | **15 of 28 critical** | 13 project-local footprints carry their source in their own `descr`; **`U11` BQ25185 was verified in this task** against TI's `DLH0010A` EXAMPLE BOARD LAYOUT, drawing **4226298/A 10/2020** — pads 10 × (0.2 × 0.5), **pitch 8 × (0.4)**, **EP (0.9) × (1.5)**; and the PCAL9535A TSSOP-24 4.4 × 7.8 P0.65 was confirmed as **SOT355-1** |
| **2 — vendor-specific stock footprint, drawing NOT read** | **8** | `ESP32-S3-WROOM-1`, GCT `USB4105-xx-A`, JST `ACH BM02B-ACHSS-GAN-ETF`, JST `PH B2B-PH-K`, `PTS645Sx43SMTR92`, `SW_SPDT_CK_JS102011SAQN`, `TQFN-16-1EP_3x3mm_EP1.23x1.23`, `Crystal_SMD_3225-4Pin` |
| **3 — generic JEDEC/IPC package** | the rest | SOT-23 family, MSOP-10, TSSOP-24, VSSOP-8, SOIC-8, SOD-123/323, chip passives, test pads |

**Tier 2 is the exit-gate failure.** The standing instruction is explicit — *"Do not mark a
footprint verified because the KiCad library name looks right"* — and these eight have not been
read against a drawing. **They do not block placement**, because pin count, pitch and package
identity are fixed, but they **must be read before fabrication release**.

Also found: **`Samtec_TSW-113-08-G-D-RA.kicad_mod` is orphaned** — the old 26-pin community header,
no longer referenced, and its own description still says *"PROVISIONAL / VERIFY_BEFORE_PLACEMENT"*.
Retained only to keep the Beta-DM fork comparison byte-clean; **it must never be selected for v2.**

**Symbol pin maps were audited separately** — a footprint can be perfect and the board still dead.
Thirteen parts re-read from the netlist against their manufacturer pin lists; **all PASS**.

---

## 13. No-respin review (D-049) and simplification scan

**No-respin provisions confirmed practical and retained:** NFC matching (all `TUNE`-marked, fitted,
0603), NFC 3.3/5 V source selection (`R106`/`R107`, mutually exclusive), IR drive (`R24` + `R123`
trim), audio EMI (`R121`/`R122` 0 Ω fitted, `C81`/`C82` DNP), accessory current limits (one 0603
each), BMI270 address (`R118`/`R119`), display SDO (`R112`), external I²C pull-ups (`R49`/`R50`),
and radio antenna serviceability (both antennas are plug-in). **No speculative fallback circuitry
was added.**

**Simplification scan A–K:**

| # | looked for | found |
|---|---|---|
| A | duplicated IC families | **none** — one boost family (TPS61023 ×2 + 1 DNP), one load-switch family (TPS22950C ×2), one expander MPN (×3), one TVS MPN (×4), one switch MPN (×7) |
| B | unnecessary DNP circuitry | **`C21`/`C22` are dead pads** (§10) — deletion candidates at placement |
| C | one-off passive values | not consolidated; **deliberately deferred** — placement has not happened, and consolidating values before the layout is known optimises the wrong thing |
| D | unneeded connectors / test points | **47 test points** is a lot, but every one maps to a named bring-up measurement. **None removed** |
| E | parts replaceable by already-proven MPNs | **taken at FBV2-S1-009** — `TPD2E009DBZR` was eliminated so one TVS MPN covers all sixteen exposed contacts |
| F | hard-to-source parts with same-footprint alternates | **`TSOP38438` is a documented same-footprint fallback for `TSOP38238`**; `TSAL6200` for `TSAL6100`; `BCS-112-L-D-HE` for `-S`; `BSS138` has many second sources |
| G | manual assembly smarter than a redesign | **yes, twice** — `J1` (§5) and `J5`, both deliberate |
| H | footprints still cheap to correct | **the eight Tier-2 items** — now, before placement, is exactly when to read those drawings |

**No new product features were added, and nothing was optimised for cents.**

---

## 14. What remains

**Fabrication-release blockers**

| # | item |
|---|---|
| **B-03** | **8 of 28 critical footprints are Tier 2** — traceable but not drawing-verified (§12) |
| **B-70** *(new)* | **`L5`/`L6` 39 nH NFC EMC inductors have no MPN.** A tuned RF inductor needs a specified part — Q, I_rms, tolerance — not a value and an 0603 outline |
| **B-71** *(new)* | **Only 7 of 46 unique MPNs carry an LCSC code**, so the JLC Basic/Extended split, the assembly quote and the manual-placement list cannot be produced |
| **B-54** | **ST25R3916 field current at 3.3 V still not extracted — and this matters more now that NFC is FITTED.** The `+3V3` budget does not yet include the NFC field |
| **B-63** | Microphone acoustic hole and pad-4 paste pullback are not in the footprint |

**First-article validation items — NOT fabrication blockers**

B-48 (NFC matching values are initial; parts are fitted and marked `TUNE`) · B-60 (0x36/0x38 confirmed
by bus scan) · B-61 (speaker listing) · B-62 (AWG#32 crimp pull test) · B-66 (TSAL6100 beam
ergonomics; TSAL6200 is a drop-in) · B-59 (touch-flex pull-ups) · B-46 **closed** · B-69 **closed at
10 ms, measure and reduce** · magnetics headroom on `L1`.

**Mechanical / CAD, outside this scope:** B-50, B-52, M-04, M-08, M-11, M-12, and the unverified
enclosure fit.

**Open for the CTO:** **O-8** — the 915 MHz external whip antenna MPN.

---

## 15. Verification

| check | result |
|---|---|
| **ERC** (errors + warnings, **not** `--severity-all`) | **27 messages, 0 ERRORS, 27 warnings — unchanged** |
| new errors | **0** |
| duplicate references | **0** |
| unresolved footprint references | **0** (`LS1` is intentionally off-board) |
| missing MPN on actives/connectors | **0** — six added in this task |
| orphan nets / one-pin nets | **0** |
| `*_TBD` nets | **0** |
| unexplained DNP | **0** — 16 remain, every one documented |
| same-text local labels split across sheets | **0** |
| `fork_equivalence.py` | **PASS** |
| `netclass_probe.py` | **PASS** |
| **PCB** | **UNCHANGED — still bit-identical to Beta-DM** |

**No honest warning was "fixed".** No no-connect, power flag or pin-electrical-type was added or
altered anywhere in this task.
