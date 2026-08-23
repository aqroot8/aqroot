# FBV2-S1-001 — Full Beta v2 power-tree implementation and closeout

**Task:** FBV2-S1-001, resumed as **FBV2-S1-001-RESUME**.
**Date:** 2026-08-23.
**Repository HEAD at task start:** `12e653c` (*docs: correct Full Beta v2 community
connector selection*, FBV2-COMM-002).
**Scope:** `hardware/beta-v2/` only. Sheets `02`–`09` were **not** modified beyond the
embedded project name. `hardware/beta-dm/`, `hardware/beta/` and
`hardware/beta/mechanical/` were **not touched**.

This audit is written to the same standard as the rest of the programme: **every claim
below is measured from the files, not asserted.** Where something was not measured, it
says so.

---

## 0. What this task did and did not do

| | |
|---|---|
| **Did** | Finished and closed the in-flight capture of `01_power_tree.kicad_sch` for Full Beta v2 |
| **Did** | Ran ERC, exported the netlist, and audited connectivity net by net |
| **Did** | Produced the missing fork/preservation proof the FBV2-S1 exit criterion demands |
| **Did** | Corrected stale status text in the project README and on the sheet itself |
| **Did NOT** | Migrate sheets `02`–`09` to the Full Beta v2 architecture |
| **Did NOT** | Touch the PCB. `aqroot-Beta-v2.kicad_pcb` is still **bit-identical** to Beta-DM and does not match this schematic |
| **Did NOT** | Verify a single footprint against a vendor drawing — that is **FBV2-S2** |
| **Did NOT** | Lock any MPN, or claim any part is fabrication-ready |

**FBV2-S1 as a whole does NOT pass on this task.** Its exit criterion is *"`hardware/beta-v2/`
exists, forked from Beta-DM with a byte-equivalence proof, and **every** schematic change in
the migration order is landed."* One sheet of nine carries the v2 architecture. What passes
here is the **task gate FBV2-S1-POWER-TREE**, and nothing wider.

---

## 1. State found on resume

`hardware/beta-v2/` existed, untracked, forked from `hardware/beta-dm/`. The FBV2-COMM-002
commit had stated *"`hardware/beta-v2/` was not created"* — true when written, overtaken by
the work that followed it. The fork carried:

* sheets `02`–`09` and the `.kicad_pcb` / `.kicad_dru` copied verbatim;
* `01_power_tree.kicad_sch` grown from 280 KB to 580 KB with **135 new component instances**;
* `libraries/AQROOT_Beta.kicad_sym` extended with `LTC4368-1`, `TLV7032`, `TPS22950C`;
* the root sheet retitled `AQROOT Full Beta v2 Main Board`, rev `v2.0-S1-power-tree`.

**ERC at resume: 60 violations against a 58-violation Beta-DM baseline.** The delta was four
new and two legitimately removed. The four new:

| # | violation | meaning |
|---|---|---|
| 1 | `pin_not_connected` — `U11` pin 2 `BAT` @(71.12, 100.33) | the charger was never joined to the protected battery node |
| 2 | `power_pin_not_driven` — `U19` pin 8 `VCC` @(90.17, 349.25) | the recovery comparator's rail had no ERC driver |
| 3 | `unconnected_wire_endpoint` @(71.12, 100.33) | the `U11` pin-2 stub, drawn but unlabelled |
| 4 | `unconnected_wire_endpoint` @(62.23, 102.87) — **root sheet** | orphaned stub left when the `BAT_PROTECTED_P` hierarchical pin was removed |

Items 1 and 3 are one defect. Item 4 was **not** in the reported delta at resume time and was
found by this audit.

---

## 2. The two reported ERC errors — resolved

### 2.1 `U11` BQ25185 pin 2 `BAT`

The stub wire `(71.12, 100.33) → (73.66, 100.33)` already existed and was simply unlabelled;
its three neighbours (`BQ25185_SYS`, `BQ25185_STAT1`, `BQ25185_STAT2`) all carry labels at
`x = 73.66`. The fix is the missing label, not new copper.

**Fix:** label `BAT_PROTECTED_P` at `(73.66, 100.33)`.

**Verified against the locked architecture.** The FBV2-PWR-002 block diagram terminates the
protected node at *"`BQ25185` BAT"*, and the on-sheet note already read
`… -> R75 15mR -> BAT_PROTECTED_P -> BQ25185 BAT`. Measured result:

```
/01_POWER_TREE/BAT_PROTECTED_P  (10)
  C25.1  C36.1  C58.1  D9.1[K]  R75.2  TP15.1  U11.2[BAT]  U14.2[CELL]  U14.3[VDD]  U18.8[VOUT]
```

**PASS.**

### 2.2 `U19` TLV7032 pin 8 `VCC`

The electrical connection **was already correct and complete**:
`USB_VBUS_CHG → R84 100 R → VREC_VCC → U19 VCC`, decoupled by `C60` 100 nF. That matches
the locked recovery architecture (*"VBUS ── TLV7032 VDD"*) with an added 100 Ω / 100 nF
filter, which also limits fault current into the comparator. At 315 nA supply current the
100 Ω drop is ~32 nV; the filter costs nothing.

KiCad flagged it because **a power-input pin fed through a passive has no ERC driver** —
`R84` does not propagate the flag on `USB_VBUS_CHG`.

**Fix:** `PWR_FLAG` `#FLG613` on `VREC_VCC` at `(182.88, 330.2)`.

**This is not ERC suppression, and the distinction matters.** The rail is genuinely driven;
what KiCad cannot infer is that the drive arrives through a series resistor. This is the same
idiom the design already uses in three other places, all for the same reason — `#FLG0101` on
`USB_VBUS_CHG` (fed from a connector), `#FLG0102` on `BAT_PROTECTED_P`, `#FLG612` on
`BAT_RAW` (fed from `J4` through `F1`). No net was joined, split or renamed to make the error
go away, and **the netlist is byte-for-byte unchanged by this fix**:

```
/01_POWER_TREE/VREC_VCC  (3)   C60.1  R84.2  U19.8[VCC]
```

**PASS.**

### 2.3 The third defect — orphaned root stub

Removing the `BAT_PROTECTED_P` hierarchical pin from the `01_POWER_TREE` sheet symbol left a
2.54 mm wire and a `BAT_PROTECTED_P` label stranded on the **root** sheet. `BAT_PROTECTED_P`
is now correctly local to `01_POWER_TREE`; nothing outside it may reference the raw battery
node.

**Fix:** both the orphan wire and the orphan label deleted from `aqroot-Beta-v2.kicad_sch`.
This also retires an *inherited* `label_dangling` violation that Beta-DM carried.

---

## 3. ERC — before and after, against the inherited baseline

| measurement | violations |
|---|---|
| **Beta-DM baseline** (`hardware/beta-dm`, unmodified) | **58** |
| Beta-v2 at resume | 60 |
| **Beta-v2 after this task** | **55** |

The full violation lists were diffed line by line, not merely counted. Against the Beta-DM
baseline the final state is:

* **added: none.** Zero ERC violations of any kind were introduced by FBV2-S1.
* **removed: three**, all legitimately:
  * `label_dangling` @(62.23, 105.41) `BAT_PROTECTED_P` — the orphan removed in §2.3;
  * `isolated_pin_label` × 2, `BAT_CONNECTOR_P` — the label was isolated in Beta-DM because
    `BAT_CONNECTOR_P` was a **one-pad net** (`J4.1` alone, blocker **B-01**). It is now a real
    net (`J4.1`, `F1.1`, `TP34.1`).

`01_POWER_TREE` itself now reports **zero** violations.

> **This is not "ERC zero" and must never be quoted as such.** 55 inherited violations remain,
> concentrated on the root sheet (dangling and isolated labels from the unmigrated sheets) and
> on `03_SPI_A_DISPLAY_SD` (18 × `pin_to_pin`). They belong to sheets `02`–`09` and to
> **FBV2-S2**. Report: `hardware/beta-v2/reports/FBV2-S1-erc.rpt`.

---

## 4. The `R_FB_TOP 1M` net label

**What it was:** a genuine defect, and **inherited from Beta-DM — not introduced by FBV2-S1.**
It is a literal net label reading `R_FB_TOP 1M`, i.e. *"the top feedback resistor is 1 MΩ"* —
a value annotation that was placed as a **label** instead of as text. `R39` is indeed `1M 1%`,
which confirms the intent.

**What the net actually is:** the TPS63020 main `+3V3` feedback midpoint.

```
+3V3 ── R39 1M 1% ──┬── U12.3 [FB] ── (0.5 V ref)
                     └── R40 180k 1% ── GND      =>  0.5 x (1M + 180k) / 180k = 3.278 V
```

**Resolution:** renamed to **`V3V3_FB`** in `hardware/beta-v2/` only. Beta-DM is frozen and
keeps the defect; it is a cosmetic naming fault there, not an electrical one. Net names must
describe nets, not component values — a name containing a space and a resistance also makes
netclass patterns and any downstream net-name matching fragile.

```
/01_POWER_TREE/V3V3_FB  (3)   R39.2  R40.1  U12.3[FB]
```

Consequence to carry into FBV2-P1: the inherited `.kicad_pcb` still contains the old net
name. That is harmless **only** because the v2 board will be re-floorplanned from scratch; it
must not be resolved by editing the Beta-DM board.

### Label audit — all 56 labels on the sheet

Every label was scanned for embedded spaces, embedded component values, near-duplicate rail
names, and isolated single-pin nets.

| check | result |
|---|---|
| labels containing a space | **1** (`R_FB_TOP 1M`) — fixed |
| labels containing a resistance/capacitance token | **1** (same) — fixed |
| labels resolving to a single-pin net on `01_POWER_TREE` | **0** |
| near-duplicate rail names | none. `ACC_5V_{RAW,SW,LX,FB,EN,ILIM}` are six distinct nodes of one rail and are correctly distinguished |
| misspelled power nets | none. `+3V3` and `GND` are the only global rails and both resolve as expected (81 and 223 pads) |

No other label was renamed. Names that are merely terse (`REF_HO`, `N_POL`, `N_BATDIV`) were
left alone — they are correct and are explained by the on-sheet notes.

---

## 5. Connectivity audit

Measured from `kicad-cli sch export netlist`, not read off the drawing.

### 5.1 Battery main path — **PASS**

```
J4.1 ── BAT_CONNECTOR_P ── F1 (5 A, 1206) ── BAT_RAW
   BAT_RAW ── Q2 [D1/D2, NTMD4820N, SOIC-8]  (stage A, common source Q2_CS)
           ── BAT_MID
           ── Q3 [D1/D2, NTMD4820N, SOIC-8]  (stage B, common source Q3_CS)
           ── BAT_SENSE ── R75 15 mR 1% 1W (2512) ── BAT_PROTECTED_P
```

| element | measured | conforms to |
|---|---|---|
| Two stages, **two packages** | `Q2` and `Q3` are separate SOIC-8 duals | D-068 / P2 |
| Common **source** pairs, not common drain | `Q2_CS` = `Q2.1`+`Q2.3`; `Q3_CS` = `Q3.1`+`Q3.3` | LTC4368 has one `GATE` pin |
| Single gate drive | `LTC_GATE` = `Q2.2`, `Q2.4`, `Q3.2`, `Q3.4`, `U18.10`, `R76`, `TP17` | — |
| Gate slew RC | `R76` 22 k → `LTC_GATE_RC` → `C57` 4.7 nF → GND | R_GATE 22 k, C_GATE 4.7 nF |
| Sense resistor between `SENSE` and `VOUT` | `U18.9` on `BAT_SENSE`, `U18.8` on `BAT_PROTECTED_P`, `R75` between | LTC4368 datasheet topology |
| `RETRY` grounded → latch-off | `U18.4` on `GND` | D-064 |
| `UV` deliberately unused | `R79` 510 k from `BAT_RAW` to `U18.2`, **no bottom leg** | datasheet: *"If unused and VIN < 80 V, connect to VIN with a 510 k resistor"* |
| `OV` divider | `R77` 4.02 M / `R78` 442 k → **5.05 V** trip (0.5 V ref) | "divider ≈ 4.6 V" — see §7 |
| `SHDN` | `R80` 1 M pull-up to `BAT_RAW`; `Q4` BSS138 pulls low; `TP19` | D-064 |
| Negative clamp, secondary duty | `D9` PMEG2010AEH, K on `BAT_PROTECTED_P`, A on `GND` | clamp demoted to secondary |
| Fuse observable from both sides | `TP34` on `BAT_CONNECTOR_P`, `TP16` on `BAT_RAW` | see §6 |

`BAT_PROTECTED_P` feeds `U11` BAT, `U14` `CELL`+`VDD` (MAX17048), `C25`/`C36`/`C58`, `D9`,
`TP15`. **Nothing bridges `BAT_CONNECTOR_P` to `BAT_PROTECTED_P` except the protection.** The
parallel link across the FETs remains forbidden and does not exist.

**Blocker B-01 is closed at schematic level.** It is not closed at board level: the PCB is
still the Beta-DM board.

### 5.2 Dead-cell recovery — **PASS**

```
USB_VBUS_CHG ──┬── R84 100R ── VREC_VCC ── U19 [VCC] TLV7032   (+ C60 100 nF)
               ├── D10 BAT54WS ── VBRIDGE_TOP ── R85 2.2M ──┬── N_POL  ── U19.3 [INA+]
               │                                  R86 2.2M ──┘  (to BAT_RAW)
               ├── D11 BAT54WS ── VREF_TOP   ── R87 2.2M ──┬── REF_POL ── U19.2 [INA-]
               │                                  R88 2.2M ──┘  (to GND)
               ├── R91 3.65M ──┬── REF_HO ── U19.5 [INB+]      (R93 22M DNP hysteresis)
               │     R92 1.30M ─┘
               ├── R89 2.2M ──┬── N_BATDIV ── U19.6 [INB-]     (+ C61)
               │     R90 2.2M ─┘
               ├── R94 1M ── REC_GATE_N ── Q5 [G] AO3401A
               ├── R96 1M ── REC_FAULT_B ── Q8 [G]
               └── Q5 [S];  Q5 [D] ── REC_LIM_IN ── R95 ── REC_DIODE_IN ── D12 ──▶ BAT_RAW
```

| requirement | measured | verdict |
|---|---|---|
| Recovery supply is **USB only** | `VREC_VCC` derives from `USB_VBUS_CHG`; nothing ties it to the pack | **PASS** |
| Polarity comparator is **ratiometric** | `INA+` = (`VBRIDGE_TOP` + `BAT_RAW`)/2, `INA−` = `VREF_TOP`/2, equal 2.2 M legs. `D10` and `D11` are matched BAT54WS, so both tops sit one identical Schottky drop below VBUS and the comparison is supply-independent, tripping at `BAT_RAW` = 0 | **PASS** |
| Schottkys also block pack drain when USB is absent | `D10`/`D11` cathodes face the bridge | **PASS** |
| Handoff comparator | `INB+` = `REF_HO` = VBUS × 1.30/(3.65+1.30) = **1.313 V**; `INB−` = `BAT_RAW`/2. `OUTB` asserts below **≈ 2.63 V** of pack — above the LTC4368 UVLO band (1.8–2.4 V), so recovery hands over **before** the main path can take control, and self-terminates once it has | **PASS** |
| Hysteresis provision | `R93` 22 M **DNP** from `OUTB` to `INB+` — a fitted-option per D-049 | **PASS** |
| Three-input **series** AND | `Q6`(pol) → `REC_AND1` → `Q7`(bat-low) → `REC_AND2` → `Q8`(fault) → GND, pulling `REC_GATE_N` down against `R94` 1 M | **PASS** |
| Active **only** while `FAULT` is low | `Q9` inverts: `LTC4368_FAULT_N` high → `Q9` on → `REC_FAULT_B` low → `Q8` off → recovery blocked | **PASS** |
| …**including when `+3V3` does not exist** | `LTC4368_FAULT_N` sits on `R81` 1 M to `+3V3` **and `R82` 1 M to GND**. With a dead pack there is no `+3V3`, so the node is held at 0 V, `Q9` is off and recovery is *enabled*. With `+3V3` present and no fault the node sits at 1.65 V, above BSS138 V_th | **PASS — and this is the load-bearing detail of the whole branch** |
| Unidirectional, current-limited injection | `Q5` [S] on VBUS, [D] → `R95` → `D12` → `BAT_RAW` | **PASS**, value deviation — §7 |
| Observability | `TP21` `REC_GATE_N`, `TP22` `REC_DIODE_IN`, `TP23` `N_POL`, `TP24` `REF_POL`, `TP18` `LTC4368_FAULT_N` | **PASS** |

All safety-critical parts in this branch are **leaded and inspectable**: SOT-23-8, SOT-23,
SOIC-8, SOT-23 P-FET, SOD-323 diodes. No BGA, WLCSP or bottom-terminated part — see §6 for the
one violation that was found and corrected.

### 5.3 `ACC_3V3` — **PASS**

| node | measured |
|---|---|
| input | `+3V3` → `U20.2` `VIN` (TPS22950C, SOT-23-6) |
| enable | `ACC_3V3_EN` = `U20.1` `ON`, `R98` **100 k pull-down to GND** (mandatory per D-086), `TP26` |
| current limit | `ACC_3V3_ILIM` = `U20.4`, `R97` **1.5 k 1%** to GND — the value D-086 specifies (≈ 0.76 A typ) |
| output | `ACC_3V3_SW` = `U20.5` `VOUT`, `C63` 1 µF, `TP25` |
| fault | `U20.6` `FLT` (open-drain) on `ACC_POWER_FAULT_N`, `R103` 100 k pull-up to `+3V3` |
| ground | `U20.3` on `GND` |

### 5.4 `ACC_5V` — **PASS**

| node | measured |
|---|---|
| input | `BQ25185_SYS` → `U21.3` `VIN` **and** `L4.1`; `C64` 10 µF local input cap |
| switch node | `ACC_5V_LX` = `L4.2` + `U21.5` `SW`; `L4` = 1 µH, **same Wurth `74438357010` MPN as `L2`** |
| feedback | `R99` **732 k** / `R100` **100 k** → 0.6 × 8.32 = **4.99 V**. *Identical to the NFC boost divider `R44`/`R45`* |
| raw output | `ACC_5V_RAW` = `U21.6`, `C65`+`C66` 2 × 22 µF — *identical to `C34`/`C35` on the NFC boost* |
| enable | `ACC_5V_EN` drives **both** `U21.2` `EN` and `U22.1` `ON` from one net (D-089), `R102` 100 k pull-down, `TP30` |
| load switch | `U22` TPS22950C, `VIN` = `ACC_5V_RAW`, `ILIM` `R101` **1.65 k 1%** (D-087, ≈ 0.69 A typ) |
| output | `ACC_5V_SW` = `U22.5`, `C67` 1 µF, `TP29` |
| fault | `U22.6` `FLT` wire-ORed with `U20.6` onto `ACC_POWER_FAULT_N` (D-094 / O-1) |

**D-088 BOM consolidation is honoured exactly:** one boost MPN, one inductor MPN, one feedback
divider, one output-cap pair, one load-switch MPN differing only in `R_ILIM`. The 5 V rail is
sourced from `SYS`, **not** from USB `VBUS` and **not** from the NFC fallback boost — O-3
stays rejected.

### 5.5 NFC fallback power — **PASS on this sheet, INCOMPLETE across the design**

```
+3V3 ────────────── R106  0R  FIT ──┬── NFC_SUPPLY ── TP32
NFC_5V_PA_PENDING ─ R107  0R  DNP ──┘
```

| requirement | verdict |
|---|---|
| Default source is 3.3 V | **PASS** — `R106` is the FIT link |
| 5 V source available with no respin | **PASS** — `R107` is a populated-option 0 Ω footprint, no trace cut |
| Mutually exclusive | **PASS by fit state.** With only `R106` fitted there is no path between `+3V3` and the boost output |
| **No possible fitted-state short between 3V3 and 5V** | **CONDITIONAL.** Fitting *both* links shorts `+3V3` to the boost output. Nothing in copper prevents it; the exclusivity is a build rule. This is inherent to a 0 Ω source-select and is the mechanism D-049 asks for, but it must be carried as an assembly-note requirement — recorded as **B-42** |

> **`NFC_SUPPLY` has no consumer.** `U9` `VDD` and `VDD_TX` are still on
> `NFC_5V_PA_PENDING` — the Beta-DM arrangement — because they live on sheet `04`, which this
> task was not authorised to modify. **The v2 NFC supply architecture is therefore only half
> implemented.** Recorded as **B-41**; it is the first item of the sheet-`04` migration.

### 5.6 Telemetry — **PASS on this sheet, INCOMPLETE across the design**

| signal | measured | note |
|---|---|---|
| `BQ25185_STAT1` | `U11.9`, `TP6` | no expander connection yet — sheet `08` |
| `BQ25185_STAT2` | `U11.3`, `TP7` | as above |
| `VBUS_PRESENT` | `R104` 150 k / `R105` 220 k from `USB_VBUS_CHG`, `C68` 100 nF, `TP31` → **2.97 V at VBUS 5.0 V** | **raw VBUS never reaches the expander** — the requirement is met at the divider. Closes the VBUS-sense half of **B-15** at sheet level |
| `LTC4368_FAULT_N` | `U18.7`, `R81`/`R82`, `Q9`, `TP18` | consumed locally by the recovery AND; no MCU path yet |
| `ACC_POWER_FAULT_N` | `U20.6` + `U22.6` wire-OR, `R103` pull-up, `TP27`, `TP33` | D-094 / O-1 satisfied; `U3` P16 stays `RESERVED_SPARE` |

Every one of these must reach `U2`/`U3` per D-089. **None of them does yet** — all five
crossings are on sheets `08`/`09`. `B-15` therefore stays open.

### 5.7 Test points — **PASS**

19 test points on this sheet, all on the intended nets:

| TP | net | TP | net |
|---|---|---|---|
| `TP34` | `BAT_CONNECTOR_P` (J4 side of `F1`) | `TP24` | `REF_POL` |
| `TP16` | `BAT_RAW` (FET side of `F1`) | `TP25` | `ACC_3V3_SW` |
| `TP15` | `BAT_PROTECTED_P` | `TP26` | `ACC_3V3_EN` |
| `TP20` | `BAT_SENSE` | `TP27` | `ACC_POWER_FAULT_N` |
| `TP17` | `LTC_GATE` | `TP28` | `ACC_5V_RAW` |
| `TP18` | `LTC4368_FAULT_N` | `TP29` | `ACC_5V_SW` |
| `TP19` | `BAT_PROT_SHDN_CTL` | `TP30` | `ACC_5V_EN` |
| `TP21` | `REC_GATE_N` | `TP31` | `VBUS_PRESENT` |
| `TP22` | `REC_DIODE_IN` | `TP32` | `NFC_SUPPLY` |
| `TP23` | `N_POL` | `TP33` | `ACC_POWER_FAULT_N` (second probe on the wire-OR) |

`TP34` was **added by this task**. The locked block diagram calls for a test point on each
side of the fuse — *"the two together make fuse state observable"* — and only the `BAT_RAW`
side existed. Adding it also retired the two inherited `isolated_pin_label` violations on
`BAT_CONNECTOR_P` (§3).

`TP33` duplicates `TP27` electrically. It is retained deliberately: the two `FLT` pins are
wire-ORed, so a probe near each load switch is worth more during bring-up than a saved pad.

---

## 6. Package-policy violation found and corrected

**`U18` LTC4368-1 was assigned `Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm`.**

The FBV2-PWR-002 closeout is explicit:

> *"Package policy honoured: every new safety-critical part is **leaded and inspectable** —
> MSOP-10, SOIC-8, SOT-23-8, SOT-23, SOT-363. **No BGA, no WLCSP, no bottom-terminated parts**
> anywhere in the battery protection or recovery circuitry."*

A DFN-10 with an exposed pad is a bottom-terminated part. The locked candidate is
**LTC4368IMS-1#PBF, MSOP-10**. This is not a footprint-verification detail deferrable to
FBV2-S2 — it is a **package choice that contradicts a locked decision**, on the single most
safety-critical part on the board.

**Corrected to `Package_SO:MSOP-10_3x3mm_P0.5mm`**, in both `01_power_tree.kicad_sch` and the
project symbol library default. The symbol has ten pins and no exposed-pad pin, so the
no-EP MSOP-10 land pattern is the consistent choice and the netlist is unchanged.

**The footprint is still UNVERIFIED.** Correcting the package is not verifying the land
pattern; `U18` joins the FBV2-S2 list.

Every other new part was checked against the same policy and conforms: `Q2`/`Q3` SOIC-8,
`U19` SOT-23-8, `Q4`–`Q9` SOT-23, `U20`/`U22` SOT-23-6, `U21` SOT-563, `D9` SOD-123,
`D10`–`D12` SOD-323, `F1`/`R95` 1206, `R75` 2512.

---

## 7. Deviations from the locked architecture — NOT resolved by this task

These are recorded, not silently adopted and not silently "fixed". A value in a locked
architecture document is changed by a CTO ruling, not by a capture task.

| # | item | locked | captured | assessment |
|---|---|---|---|---|
| 1 | **`R95` recovery current limit** | `R_LIM` **560 R** | **680 R 1% 1206** | Injection falls from ≈ 8.4 mA to **≈ 6.9 mA** at VBUS 5.0 V into a 0 V pack. **This moves the wrong way against open blocker B-26**, which warns that a pack protector needing more than ~10 mA to release its over-discharge latch would not be revived. Opened as **P-20** |
| 2 | **Bridge/reference resistors** | 1 MΩ 0.1 %, *"1 % acceptable"* | 2.2 MΩ 1 % | **Accepted.** The comparator thresholds are set by *ratios*, and both legs of every divider are the same value and tolerance, so threshold error tracks tolerance (1 %), not absolute value. 2.2 M halves the bridge current, which is strictly better for a dead pack. No ruling needed |
| 3 | **`OV` trip** | *"divider ≈ 4.6 V"* | `R77` 4.02 M / `R78` 442 k → **5.05 V** | Above a 4.2 V pack with margin, and below the 5.5 V USB ceiling. Plausible and probably deliberate, but it is **not the documented number**. Opened as **P-21** |

None of the three is a connectivity fault, and none blocks the task gate.

---

## 8. Fork / preservation proof

The FBV2-S1 exit criterion demands a *byte-equivalence proof*. It did not exist. It does now,
and it is **re-runnable rather than transcribed**:

* `hardware/beta-v2/checks/fork_equivalence.py` — re-derives every classification from the two
  directories on disk. Exit 0 = the fork matches the declared expectation.
* `hardware/beta-v2/reports/FBV2-S1-fork-equivalence.md` — the pinned result, with full
  SHA-256 values.

Measured: **PASS**.

| claim | measured |
|---|---|
| Sheets `02`–`09` byte-equivalent after project-name normalisation **only** | 8 of 8. `aqroot-Beta-DM` and `aqroot-Beta-v2` are the same length, so the normalised comparison also proves no length drift |
| `.kicad_pcb` bit-identical to Beta-DM | **yes** — `aaa04bfbd5d69c56…` in both |
| `.kicad_dru` bit-identical | **yes** |
| `fp-lib-table`, `sym-lib-table` bit-identical | **yes** |
| All 12 project footprints bit-identical | **yes** |
| `.kicad_pro` differs by project name **only** | **yes** — no design rule, netclass or setting was altered |
| `hardware/beta-dm/` unchanged | **yes** — no tracked file modified, added, deleted or renamed |
| `hardware/beta/` unchanged | **yes** |
| `hardware/beta/mechanical/` untouched | **yes** — it appears only as a pre-existing untracked directory |

A second inherited script, `hardware/beta-v2/checks/netclass_probe.py`, had been copied
without repointing and was still testing **Beta-DM's** files from inside the v2 tree — a probe
that silently validates the wrong project is worse than no probe. Repointed to
`aqroot-Beta-v2`; still **PASS** (6 nets resolve to `LED_BOOST`, `/07_IR/IR_LED_*` do not).

---

## 9. Documentation corrected

The project README (`hardware/beta-v2/kicad/aqroot-beta-v2/README.md`) was **bit-identical to
Beta-DM's** and stated that `01_POWER_TREE` was *"SPECIFIED, NOT DRAWN"*, that its `.kicad_sch`
was *"an empty stub"*, that the PCB was *"EMPTY — no footprints, no tracks, no board outline"*,
that ERC had *"NEVER RUN"*, and that `09_COMMUNITY_HEADER` was undrawn with two unselected
parts. Every one of those was false. Corrected to the measured state, with `CAPTURED` on
sheet `01` qualified as **CAPTURED — FBV2-S1 POWER-TREE IMPLEMENTATION**, and sheets `02`–`09`
marked **CAPTURED — INHERITED, BETA-DM ARCHITECTURE** so that "captured" can never be read as
"migrated".

Two on-sheet notes were equally stale and are rewritten in place: the
`REV-POLARITY PROTECTION PLACEHOLDER` box (which forbade the very circuit now drawn) and the
`BETA CAPTURE IN PROGRESS` status box.

### One governance item

The README carries a standing Beta-DM rule: *"Do not generate or modify KiCad schematic or PCB
files automatically. KiCad files will be created manually in KiCad 10.0.3."*
**FBV2-S1 captured `01_POWER_TREE` as a scripted migration, not by hand in the GUI.** The rule
has been recorded in place, scoped and flagged as **awaiting CTO ratification or
reinstatement** — it is deliberately *not* treated as repealed by having been overtaken.
Opened as **P-22** for ruling.

---

## 10. Task gate

**FBV2-S1-POWER-TREE = PASS.**

| criterion | verdict |
|---|---|
| The two reported ERC errors resolved | **YES** (§2) |
| No other new power-tree ERC error | **YES** — zero added against the Beta-DM baseline; a third defect was found and also fixed (§3) |
| Accidental net-label issue resolved | **YES** (§4) |
| Power-tree connectivity audit passes | **YES** — battery path, recovery, `ACC_3V3`, `ACC_5V`, NFC select, telemetry, test points (§5) |
| Fork-equivalence proof exists | **YES**, re-runnable (§8) |
| README / status accurate | **YES** (§9) |
| Project parses | **YES** — all ten sheets parse, ERC and netlist export both run |
| No PCB placement or routing | **YES** — PCB bit-identical to Beta-DM |
| Beta-DM and frozen Beta untouched | **YES** (§8) |

**FBV2-S1 (the programme gate) remains OPEN.** Eight of nine sheets still carry the Beta-DM
architecture.

### Decisions recorded

**D-099** `U18` package corrected to MSOP-10 (§6). **D-100** net names describe nets, not
component values (§4). **D-101** `TP34` added on `BAT_CONNECTOR_P` (§5.7). **D-102** `PWR_FLAG`
is permitted only where a rail is genuinely driven and KiCad cannot infer it (§2.2).
**D-103** `BAT_PROTECTED_P` is local to `01_POWER_TREE` (§2.3).

### Blockers and pending decisions opened

| # | item |
|---|---|
| **B-41** | `NFC_SUPPLY` has no consumer — `U9` `VDD`/`VDD_TX` still on `NFC_5V_PA_PENDING` (sheet `04`). The v2 NFC supply architecture is half implemented |
| **B-42** | The NFC 3V3/5V source select is mutually exclusive **by fit state only**. Fitting both `R106` and `R107` shorts `+3V3` to the boost output. Needs an assembly-note and fab-drawing requirement |
| **P-20** | `R95` = 680 R against a locked 560 R — recovery injection ≈ 6.9 mA, worsening B-26. CTO ruling: keep 680 R or restore 560 R |
| **P-21** | `OV` trip captured at 5.05 V against a documented ≈ 4.6 V. Confirm or correct the number |
| **P-22** | Ratify or reinstate the "no automatic KiCad file generation" rule now that FBV2-S1 has been captured by script |

### Unchanged and still open

`B-15` (no charge/VBUS telemetry reaches the MCU — the divider exists, the crossing does not),
`B-26`, `B-27`, `B-32`, `B-34`, `B-38`, `B-03` (footprint audit — now including `U18`), and the
whole of FBV2-S2.

---

## 11. What must happen next, in order

1. **Do not start sheet `02`.** The migration order is a CTO call, and §5.5/§5.6 make the case
   that sheet `04` (NFC supply handoff) and sheets `08`/`09` (telemetry and accessory-control
   crossings) are the load-bearing ones, not `02`.
2. Rule on **P-20**, **P-21** and **P-22**.
3. Continue FBV2-S1 sheet by sheet. **FBV2-S1 cannot pass until all nine sheets carry the v2
   architecture.**
4. Only then FBV2-S2: 0 ERC errors, and every project-library footprint verified against a
   vendor drawing with a per-footprint pad-overlap assertion.
5. The PCB stays untouched until FBV2-P1, and is re-floorplanned to the published cavity —
   the Beta-DM outline was ruled **RE-FLOORPLAN REQUIRED** by FBV2-MECH-001.

---

## Sources

* `hardware/beta-v2/reports/FBV2-S1-erc.rpt` — final ERC, 55 violations.
* `hardware/beta-v2/reports/FBV2-S1-erc-beta-dm-baseline.rpt` — the 58-violation Beta-DM
  baseline the delta is measured against.
* `hardware/beta-v2/reports/FBV2-S1-erc-at-resume.rpt` — the 60-violation state on resume.
* `hardware/beta-v2/reports/FBV2-S1-fork-equivalence.md` — pinned provenance proof.
* `hardware/beta-v2/checks/fork_equivalence.py`, `hardware/beta-v2/checks/netclass_probe.py`.
* [`2026-08-22-dead-cell-and-single-fault-closeout.md`](2026-08-22-dead-cell-and-single-fault-closeout.md) — §8 block diagram, §9 candidate parts, package policy.
* [`2026-08-22-battery-protection-closeout.md`](2026-08-22-battery-protection-closeout.md) — LTC4368 UV/OV pin behaviour.
* [`2026-08-23-community-expansion-closeout.md`](2026-08-23-community-expansion-closeout.md) — D-086 … D-092.
* [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md) — D-049, D-064, D-068, D-086 … D-094.
