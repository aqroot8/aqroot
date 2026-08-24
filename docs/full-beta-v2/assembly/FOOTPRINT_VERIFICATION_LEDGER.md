# AQROOT Full Beta v2 — footprint verification ledger

**Status: NORMATIVE.** Generated 2026-08-23 at FBV2-S2-001, **B-03 CLOSED and B-63 CLOSED 2026-08-23 at FBV2-S2-002.** This file exists because **B-03** has
stood since the pre-design audit: *"every other footprint remains unverified."*

> **A footprint is only marked VERIFIED here if a manufacturer drawing was read and its document
> number, revision and the dimensions taken from it are recorded.** A KiCad library name that
> looks right is **not** verification. That instruction is the reason this ledger has three tiers
> rather than a tick-box.

**Every footprint reference in the design resolves against a library. One symbol carries no
footprint — `LS1`, the off-board wired speaker — which is correct.**

---

## 1. TIER 1 — manufacturer-drawing verified, with citation

**23 of the 28 critical footprints — was 15; the eight promoted at FBV2-S2-002 are listed separately in §2A so the evidence is not buried.** Each carries the source document in its own `descr` field,
so the evidence travels with the library rather than living only here.

| footprint | part | drawing cited |
|---|---|---|
| `AQROOT_Beta:Hirose_FH69-50S-0.5SH` | `J1` | Hirose FH69 catalogue **Jun. 2025, en_FH69_CAT** "Recommended PCB Layout", cross-checked against spec sheet **ELC-399242-00-00**. Signal land 0.30 × 1.23, pitch 0.5, span C = 24.5; hold-down 0.36 × 4.25, E = 28.73 c/c; depth 7.38 |
| `AQROOT_Beta:Molex_5025700893` | `J2` | Molex sales drawing **SD-502570-001 Rev A** (archived locally). Pitch 1.1, contact land 0.8, 8-contact span 7.7, shell lands 1.4 × 1.7 |
| `AQROOT_Beta:Samtec_BCS-112-S-D-HE` | `J5` | Samtec **RECOMMENDED PCB LAYOUT, REVISION B, FIG 3** (`BCS-1XX-XXX-D-HE-XXX`). 2.54 in row, **7.87 ± 0.05 row-to-row**, 0.71 PTH, 27.94 pin field |
| `AQROOT_Beta:ST25R3916_AQET` | `U9` | ST **UFQFPN32 5×5×0.55 RECOMMENDED PCB LAND PATTERN**. Land 0.30 × 0.75, span 5.30, EP land 3.45 × 3.45 |
| `AQROOT_Beta:Bosch_LGA-14_2.5x3.0mm_P0.5mm_BMI270` | `U4` | **BST-BMI270-DS000-08 rev 1.6 §8.3** landing pattern, body from §8.1 |
| `AQROOT_Beta:MAX17048_T822` | `U14` | Maxim **RECOMMENDED PACKAGE LAND PATTERN, DOC 90-0065 REV. E**, mapped to package code T822+3 via the datasheet package table |
| `AQROOT_Beta:TI_TPS63020_DSJ` | `U12` | TI **4210895-2/E 02/16** land pattern + **4208549-3/G 04/15** thermal pad. Lands 0.24 × 0.60, 0.5 pitch, EP 2.85 × 1.58 |
| `AQROOT_Beta:Coilcraft_XFL4020` | `L1`, `L3` | Coilcraft **doc 745-3 rev 03/10/26** "Recommended Land Pattern". Pad 0.98 × 3.4 at 2.37 c/c |
| `AQROOT_Beta:Wurth_WE-MAPI_4030_74438357010` | `L2`, `L4` | Würth **74438357010 datasheet rev 003.001 (2024-02-27)** "Recommended Land Pattern" |
| `AQROOT_Beta:PUI_DMM-4026-B-I2S_4.0x3.0mm` | `MK1` | PUI Audio **DMM-4026-B-I2S-R Rev A, 5/26/2021** land pattern page. Six 0.60 × 0.40 pads + the GND ring around the port |
| `AQROOT_Beta:Vishay_TSOP382xx_Minicast_3Pin_P2.54mm` | `U6` | Vishay **doc 82491 rev 2.1**, drawing 6.550-5263.01-4 issue 12 |
| `AQROOT_Beta:MEIHUA_MHPA3528RGBCT_PLCC4_3.5x2.8mm` | `D13` | MEIHUA **Issue LPDS-0001719 Rev.2, 2018-09-25** recommended solder pad panel |
| `AQROOT_Beta:Ebyte_E07-400M10S` | `U7` | Ebyte E07-400M10S user manual ch. 3 |
| `AQROOT_Beta:Ebyte_E22-900M22S` | `U8` | Ebyte manufacturer drawing, archived |
| **`Package_DFN_QFN:Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm`** | **`U11` BQ25185** | **VERIFIED IN THIS TASK** against TI's own EXAMPLE BOARD LAYOUT for **DLH0010A, drawing 4226298/A 10/2020**: pads **10 × (0.2 × 0.5)**, **pitch 8 × (0.4)**, **exposed pad (0.9) × (1.5)**, overall (2.1). The library name encodes exactly those values |

**Also confirmed in this task:** `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` for `U2`/`U3`/`U23` is
the **SOT355-1** body the NXP PCAL9535A datasheet package table specifies, and
`Package_TO_SOT_SMD:SOT-23-6` is correct for the TI **DDC (SOT-23-THIN)** package — the
datasheet's "2.90 mm × 2.80 mm" is length × lead span, which is standard SOT-23-6.

---

## 2. TIER 2 — vendor-specific stock footprint, drawing NOT re-read

**EMPTY. B-03 CLOSED 2026-08-23 at FBV2-S2-002.**

All eight remaining Tier-2 footprints were read against a current manufacturer drawing and
compared **numerically**, dimension by dimension, to the actual KiCad footprint file. **None was
promoted on the strength of its name.** Two of the eight were expected to fail and did not; one
looked like it had failed and turned out to be the reading that was wrong. Details in §2A.

---

## 2A. B-03 closure — the eight, with the numbers

| footprint | part | drawing read | numerical result |
|---|---|---|---|
| `RF_Module:ESP32-S3-WROOM-1` | `U1` | Espressif **ESP32-S3-WROOM-1 datasheet v1.8, Figure 11-1** module dimensions and recommended PCB land pattern | **MATCH.** 40 castellated lands **1.5 × 0.9** at **1.27** pitch, row centre-to-centre **17.5**; thermal land **3.9 × 3.9** solid copper with **12** thermal vias, paste split into **nine 0.9 × 0.9 apertures spanning exactly 3.7 × 3.7**. The paste split is correct practice, not a deviation |
| `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | `J3` | GCT **USB4105 series drawing** | **MATCH.** Contact field span **8.64**; **12 × 1.15**, **4 × 0.60**, **8 × 0.30** at **0.50** pitch; **2 × Ø0.65 NPTH** locating holes; **4 × 1.00** shell lands |
| `Connector_JST:JST_ACH_BM02B-ACHSS-GAN-ETF_1x02-1MP_P1.20mm_Vertical` | `J7` | JST **ACH series** drawing | **MATCH.** Pitch **1.2**, contact land **0.85**, mounting-peg land **0.8**, peg span **3.5** |
| `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` | `J4`, `J6` | JST **PH series** drawing | **MATCH.** Pitch **2.00 ± 0.05**; hole **Ø0.7 +0.1 / −0**, so the library's **0.75** drill sits mid-window rather than at either limit |
| `Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92` | `SW1`–`SW7` | C&K **PTS645 series, SMT "G-Type" recommended layout** | **EXACT MATCH.** Layout envelope **9.5 / 6.4** in x and **5.8 / 3.2** in y gives pads **1.55 × 1.3** centred at **(±3.975, ±2.25)**; the library is **(±3.98, ±2.25)** |
| `Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN` | `SW9` | C&K **JS series** drawing — already read at FBV2-S1-007 and re-confirmed from the note carried in the `SW9` symbol | **MATCH.** Pitch **2.5 TYP**, two **Ø0.9** locating holes at **6.8** span (x = ±3.4), body **9.0 × (3.6 + 2.0)**, with a documented **1.25-vs-1.2** land fillet allowance |
| `Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm` | `U5` MAX98357A | Maxim package outline **21-0136** *and* land pattern **90-0032 Rev E** — both retrieved and read | **MATCH — and this is the one that looked wrong.** See §2B |
| `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` | `Y1` | Yajingxin **TXM27.12M0004322DBBDO00T** data sheet, *Suggested Layout* panel | **EXACT MATCH.** Pads **1.4 × 1.2**, column gap **0.8**, row gap **0.5** → centres **(±1.10, ±0.85)**; the library is **1.4 × 1.2 at (±1.10, ±0.85)**. Package **3.20 ±0.1 × 2.50 ±0.1 × 0.70 ±0.1** |

### 2B. The MAX98357A exposed pad — a contradiction that dissolved

Maxim outline **21-0136** publishes an **EXPOSED PAD VARIATIONS** table. `T1633-5` is
**1.50 / 1.60 / 1.70 mm**; `T1633-2`, `-4` and `-7C` are **0.95 / 1.10 / 1.25 mm**. The KiCad
footprint's own `descr` cites **21-0136 (T1633-5)** — the 1.60-nominal variant — while its exposed
land is **1.23 × 1.23**, which is sized for the 1.10-nominal family. On its face that is an
internally inconsistent footprint on a thermal pad, and the obvious conclusion was that a
corrected project-local footprint was needed.

**It is not inconsistent.** Maxim land pattern **90-0032 Rev E**, titled *"PACKAGE LAND PATTERN,
[T1633] 16L TQFN, 3X3 MM"*, is issued under **PKG. CODES [T1633-5], [T1633-5C] and [T1633-7C]
together** and specifies **one land for all three**: EP **1.23 × 1.23**, perimeter pads
**0.80 × 0.30**, pitch **0.50**, pad **centreline** span **2.85**, IPC-7351A, tolerance ±0.02.
Maxim deliberately recommends a land smaller than the T1633-5 exposed pad. **So the question of
which EP variant `MAX98357AETE+T` carries does not have to be answered to get the land right** —
which is fortunate, because every route to the ADI datasheet package table was blocked in this
environment.

Numerical comparison against the library file:

| dimension | 90-0032 Rev E | KiCad | delta |
|---|---|---|---|
| EP land | 1.23 × 1.23 | 1.23 × 1.23 | **0** |
| pitch | 0.50 | 0.50 | **0** |
| pad **inner** edge | 1.025 | 1.025 | **0** — EP-to-signal clearance is Maxim's own 0.410 |
| pad centre | 1.425 | 1.4375 | +0.0125 — inside the drawing's own ±0.02 |
| pad length | 0.80 | 0.825 | +0.025 toe |
| pad width | 0.30 | **0.25** | −0.05 — zero side fillet, but a 0.25 mm pad gap and a safer mask dam at 0.5 mm pitch |

**No project-local footprint was created.** Both deviations are ≤ 0.05 mm, IPC-7351B compliant,
and both fall on the safe side for a first build. EP paste is four 0.5 × 0.5 apertures over the
1.23 land — **66 % coverage**, which is correct QFN practice and not a defect. The evidence is
recorded in the `U5` symbol so it travels with the design.

---

## 2C. B-63 — the microphone acoustic footprint is now complete

`AQROOT_Beta:PUI_DMM-4026-B-I2S_4.0x3.0mm` was already Tier 1 for its **pads**, but its own
`descr` said the acoustic port was *"NOT PART OF THIS FOOTPRINT … an FBV2-S2 / PCB-stage item."*
A port that exists only as a sentence in a description is a port that gets forgotten at placement.
**It is now drawn.**

- **Acoustic hole: Ø1.05 mm NPTH**, concentric with pad 4. **The diameter is not invented** — it
  is the **inner diameter of the manufacturer drawing's own pad-4 GND ring** (ID 1.05 / OD 1.65),
  i.e. the port aperture of the part itself.
- **Paste pullback:** pad 4 no longer carries `F.Paste`. Its paste is a **separate annular
  aperture, ID 1.25 / OD 1.65** — pulled back **0.10 mm** from the copper inner edge so molten
  solder cannot wick into the port. **The 0.10 mm is a stated stencil design choice, not a drawing
  dimension**, and it is labelled as such in the footprint. Coverage ≈ **72 %** of the ring land.
- **Keepout:** a dashed `B.Fab` circle at Ø2.0 plus a `User.Comments` legend mark the region that
  must stay free of copper pours, traces, vias, silkscreen and mask steps **on both faces**.
- **Orientation:** this is a **bottom-port** microphone. It sits on the **top** of the PCB and
  listens **through** the board, so **the acoustic path leaves on the bottom face** — the
  enclosure aperture and any gasket belong on that face, not the component face. Recorded as a
  mechanical-interface constraint (**M-14**).

The edited footprint was re-loaded through KiCad's own `pcbnew` parser to confirm it is valid:
seven signal pads, one paste-only aperture, one Ø1.05 NPTH.

---

## 3. TIER 3 — generic JEDEC / IPC package, correct by package identity

`Package_TO_SOT_SMD:SOT-23` (`Q1`, `Q4`, `Q5`, `Q6`–`Q10`) · `SOT-23-6` (`U10`, `U20`, `U22`) ·
`SOT-23-8` (`U19`) · `SOT-353_SC-70-5` (`U17`) · `SOT-563` (`U13`, `U21`, `D2`–`D5`) ·
`Package_SO:MSOP-10_3x3mm_P0.5mm` (`U18`) · `SOIC-8_3.9x4.9mm_P1.27mm` (`Q2`, `Q3`) ·
`VSSOP-8_3x3mm_P0.65mm` (`U16`) · `TSSOP-24_4.4x7.8mm_P0.65mm` (`U2`, `U3`, `U23`) ·
`Diode_SMD:D_SOD-123` (`D9`), `D_SOD-323` (`D8`, `D10`–`D12`) · `Fuse:Fuse_1206_3216Metric` (`F1`) ·
`LED_THT:LED_D5.0mm` (`D1`) · `Resistor_SMD:R_0603_1608Metric` (127) ·
`Capacitor_SMD:C_0402/0603/0805` (80) · `Inductor_SMD:L_0603_1608Metric` (`L5`, `L6` — **now Murata `LQW18AN39NG80D`, B-70 closed**) ·
`TestPoint:TestPoint_Pad_D1.0mm` (47).

**Pin-level confirmations already on record:** AO3400A **1 = G / 2 = S / 3 = D** (FBV2-S1-007);
TPD4E1B06 **1 = IO1, 2 = GND, 3 = IO2, 4 = IO3, 5 = NC, 6 = IO4** (FBV2-S1-009); Q_NMOS_GSD
G/S/D for `Q10`.

---

## 4. Housekeeping

- **`libraries/AQROOT_Beta.pretty/Samtec_TSW-113-08-G-D-RA.kicad_mod` is ORPHANED** — the 26-pin
  Beta-DM community header, no longer referenced by any symbol, and its own `descr` still says
  **"PROVISIONAL / VERIFY_BEFORE_PLACEMENT"**. It is retained only so the Beta-DM fork comparison
  stays byte-clean; **it must never be selected for Full Beta v2.**
- `Molex_5025700893.kicad_mod` also exists in `hardware/beta/` and `hardware/beta-dm/`; the
  `fork_equivalence.py` probe confirms the inherited copies are bit-identical.

---

## 5. Symbol pin-map audit — separate from footprints

*A footprint can be perfect and the board still dead if the symbol pin map is wrong.*
Re-read from the netlist at FBV2-S2-001:

| part | check | result |
|---|---|---|
| `J2` microSD | against Molex SD-502570-001 pin list (1 DAT2, 2 CD/DAT3, 3 CMD, 4 VDD, 5 CLK, 6 VSS, 7 DAT0, 8 DAT1) | **PASS** — SPI mode: 2 → `SD_CS_N`, 3 → MOSI, 5 → SCK, 7 → MISO, 4 → +3V3, 6/9/11 → GND; 1 and 8 correctly unconnected |
| `J3` USB-C | 4 × VBUS, 4 × GND, D± doubled, CC1/CC2 each to a **5.1 kΩ** Rd (`R30`, `R31`), shield via `R32` 0 Ω, SBU NC | **PASS** — a sink without Rd would never be supplied |
| `U11` BQ25185 | 1 SYS, 2 BAT, 3 STAT2, 4 CE, 5 GND, 6 TS/MR, 7 ILIM_VSET, 8 ISET, 9 STAT1, 10 IN, 11 EP | **PASS** |
| `U9` ST25R3916 | 33 pins; 6 deliberately unconnected — CSO, EXT_LM, AAT_A, AAT_B, CSI, MCU_CLK | **PASS** — all six are optional features this product does not use, each with a recorded ERC exclusion |
| `U16` TCA4307 | 1 EN, 2 SCLOUT, 3 SCLIN, 4 GND, 5 READY, 6 SDAIN, 7 SDAOUT, 8 VCC; **IN side on the internal bus, OUT side on the accessory segment** | **PASS** |
| `U17` TPS61169 | 1 SW, 2 GND, 3 FB, 4 CTRL, 5 VIN | **PASS** |
| `MK1` PUI mic | 7 pads; `LR`→GND, `CONFIG`→GND, `SD`→`I2S_MIC_DIN` | **PASS** |
| `Y1` crystal | 4-pad, 1/3 signal, 2/4 GND | **PASS** |
| `U1` ESP32-S3 | all 41 pins re-read; 33 of 33 usable GPIO assigned, GPIO35/36/37 unconnected | **PASS** |
| `U2`/`U3`/`U23` | address straps 0x20 / 0x21 / 0x22 | **PASS** |
| `J5` community | all 24 contacts against D-084 | **PASS** (verified at FBV2-S1-009) |
| `D13` RGB | 1 A, 2 BK, 3 GK, 4 RK — **not** the `Device:LED_ARGB` order | **PASS** |
| `U18` LTC4368-1 | 1 VIN, 2 UV, 3 OV, 4/5 GND, 6 SHDN, 7 FAULT, 8 VOUT, 9 SENSE, 10 GATE | **PASS** |
