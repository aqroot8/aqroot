# AQROOT Full Beta v2 Progress

**Status: LIVING DASHBOARD.**

Date: 2026-08-23 (updated after FBV2-S1-004)
Repository HEAD at last update: `8556683`

---

## How percentages work here

**A percentage increases only when a gate passes.** It does not increase because
work was done, because a document was written, or because something looks close
to finished. A gate passes when its exit criterion is met and that fact is
recorded in this file with a date.

This rule exists because the programme has already been burned once by
progress that was asserted rather than measured: the enclosure reconciliation
that Field Slate v3 required was recorded as done in a commit title
("enclosure-driven PCB floorplan") while it had not happened. Percentages here
are gate-backed or they are not written.

Corollary: percentages can go **down** if a gate is later found not to have been
met.

---

## Beta-DM (preserved fallback / manufacturing baseline)

| item | status |
|---|---|
| PCB / design | **100%** |
| Fabrication | **PAUSED BEFORE PAYMENT** |
| Overall Beta-DM | **~81%** |
| Role | Preserved fallback and manufacturing baseline |

Beta-DM is not cancelled. It is the programme's insurance policy: a
design-side-complete board with DRC 0 errors and a generated fabrication package
that can be built if Full Beta v2 stalls. It must remain preserved
(CTO decision D-005).

---

## Full Beta v2

| phase | status |
|---|---|
| Requirements / product direction | **100%** |
| Pre-design audit | **100%** |
| Architecture freeze | **IN PROGRESS** |
| Schematic migration | **50%** — `01`, `02`, `03` and `04` landed; sheets `05`-`09` still Beta-DM |
| PCB placement | **0%** |
| PCB routing | **0%** |
| DFM / release | **0%** |
| Physical validation | **0%** |

### Overall Full Beta v2: **~43%**

**Raised 40% → 43% by FBV2-S1-004.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-RADIOS-NFC = PASS** (2026-08-23).

**This is the first migration task to REDUCE the project's error count.** ERC went
**4 errors → 2**, total **86 → 68**, with **zero added and eighteen removed** — and
it did so by deleting placeholder architecture, not by suppressing checks.

**Zero `*_TBD` nets remain anywhere in the project.** Sheet 04 alone retired
fourteen. NFC stopped being a promise: a real **27.12 MHz crystal** (`Y1`, LCSC
`C362365`) and a real **differential matching topology** now exist, with every value
labelled `TUNE` because they cannot be finalised without a measured antenna.

**B-41 is CLOSED** — `U9` `VDD`/`VDD_TX` finally sit on `NFC_SUPPLY`, so the 3.3 V
FIT / 5 V DNP select built in FBV2-S1-001 now drives something.

**RF architecture locked (D-118):** 433 MHz **internal** Taoglas `FXP450.07.0100C`
(mating **proven**, not assumed), 915 MHz **external** to a top-panel **SMA female**
bulkhead. Neither band puts a single millimetre of RF trace on the board.

**Two items are recommended, not locked, and need CTO sign-off:** **P-17** (keep the
non-B ST25R3916 — it is the only one of the two with a JLCPCB path) and **B-53** (NFC
antenna architecture — recommendation is a purchased flex + ferrite).

Full analysis:
[`audits/2026-08-23-s1-radios-nfc-implementation.md`](audits/2026-08-23-s1-radios-nfc-implementation.md).

<details>
<summary>Superseded — the ~40% assessment (FBV2-S1-003)</summary>

**Raised 37% → 40% by FBV2-S1-003.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-DISPLAY-SD = PASS** (2026-08-23).

**The most valuable thing this task produced is a fault it found.** The inherited
`J1` still carried the **2.8-inch panel's pin table** while its Value and Footprint
already read FH69. Against the locked `ER-TFT035IPS-6` it was wrong in **two
independent dead-on-arrival ways**: the backlight anode and cathode were reversed
(pin 1 is LEDA, not LEDK), and the SPI clock and data/command lines were swapped
(pins 36/37). **Neither is visible from a pin count, a connector MPN or an ERC
run.** A new symbol was authored with the vendor pin table verbatim.

`R111` is **FITTED** (D-111), closing the GPIO45 item. **B-43 is CLOSED with a
primary source** — the TPS61169 `CTRL` pin has a **300 kΩ internal pull-down**, so
it cannot raise the GPIO46 strap under any condition (D-116). **B-32 and B-28 are
also closed**, the latter with `R112` **DNP** rather than fitted, because the
display SDO risks the microSD to gain a feature AQROOT never uses.

**ERC: 4 errors → 4 errors, the error report byte-identical to after FBV2-S1-002.**
Total 63 → 64.

Full analysis:
[`audits/2026-08-23-s1-display-sd-implementation.md`](audits/2026-08-23-s1-display-sd-implementation.md).

</details>

<details>
<summary>Superseded — the ~37% assessment (FBV2-S1-002)</summary>

**Raised 34% → 37% by FBV2-S1-002.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-MCU-CORE = PASS** (2026-08-23).

**Three CTO pending decisions closed and a second sheet migrated.** `R95` locked at
**560 Ω** (D-105) and the LTC4368 OV trip **derived** to **4.63 V** from the
datasheet's 492.5/500/507.5 mV threshold rather than typed in (D-104). The blanket
"no scripted KiCad edits" rule is superseded by an **eight-condition** standing
process rule (D-107). `02_MCU_CORE` carries the v2 GPIO architecture:
**GPIO38 = `NATIVE_A`**, **GPIO47 = `NATIVE_B`**, **GPIO46 = `DISP_BL_CTL`** with a
dedicated strap pull-down and an isolation link, **GPIO43 withdrawn** from the
community port, and **GPIO3's missing strap pull added — B-09 CLOSED.**

**ERC: 5 errors on the Beta-DM baseline → 4. Zero new errors; `02_MCU_CORE` reports
nothing at all.** Warnings 55 → 63, all eight being root-sheet `isolated_pin_label`
entries on cross-sheet signals whose far end is an unmigrated sheet. **They were
left standing on purpose** — clearing them by adding a test point to an orphaned net
is the same anti-pattern as a `PWR_FLAG` that hides a missing driver.

**Honest accounting on B-27.** 680 Ω was not arbitrary: it was exactly the value
that produced B-27's recorded ≈ 13 mA single-fault ceiling. Locking 560 Ω raises
that ceiling to **≈ 15.9 mA nominal / ≈ 16.6 mA worst case**, and **B-27 is amended
in place rather than left reading a number that is no longer true.**

Full analysis:
[`audits/2026-08-23-s1-mcu-core-implementation.md`](audits/2026-08-23-s1-mcu-core-implementation.md).
Measured pin ledger and strap audit:
[`architecture/GPIO_LEDGER.md`](architecture/GPIO_LEDGER.md).

</details>

<details>
<summary>Superseded — the ~34% assessment (FBV2-S1-001)</summary>

**Raised 31% → 34% by FBV2-S1-001.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-POWER-TREE = PASS** (2026-08-23), on the same basis as
FBV2-DISP-LOCK and FBV2-COMM-LOCK before it.

**This is the first Full Beta v2 design-file work in the programme.**
`hardware/beta-v2/` exists, forked from Beta-DM with a **re-runnable**
byte-equivalence proof, and `01_power_tree.kicad_sch` carries the Full Beta v2
power architecture: reverse protection P2 with `U18` LTC4368-1, autonomous
dead-cell recovery, both accessory rails, the NFC no-respin source select, and
`VBUS_PRESENT` telemetry. 136 parts, all with footprints assigned. **B-01 is
closed at schematic level** — `BAT_CONNECTOR_P` is no longer a one-pad net.

**Why this is +3% and not more.** `01_POWER_TREE` is one sheet of nine, and it is
the only one carrying the v2 architecture; the other eight are byte-equivalent
copies of Beta-DM. Assigned footprints are **not verified** footprints. And the
PCB is untouched — `aqroot-Beta-v2.kicad_pcb` is still bit-identical to the
Beta-DM board and does not match this schematic.

**ERC: zero introduced.** Beta-DM baseline **58** → Beta-v2 **55**, lists diffed
rather than counted; three inherited violations retired, none added. That is
**not** "ERC clean" — 55 inherited violations remain on the unmigrated sheets and
belong to FBV2-S2.

**One locked decision had been contradicted and is corrected**: `U18` LTC4368-1
carried a **DFN-10 exposed-pad** footprint against a package policy that forbids
bottom-terminated parts anywhere in the battery-protection circuitry. Moved to
MSOP-10. **Two value deviations were found and deliberately NOT changed** — `R95`
680 R against a locked 560 R (**P-20**) and an `OV` trip of 5.05 V against a
documented ≈ 4.6 V (**P-21**). A value in a locked architecture is changed by a
ruling, not by a capture task.

Full analysis:
[`audits/2026-08-23-s1-power-tree-implementation.md`](audits/2026-08-23-s1-power-tree-implementation.md).

</details>

<details>
<summary>Superseded — the ~31% assessment (FBV2-COMM-002)</summary>

**Held at 31%.** FBV2-COMM-002 **corrected an error rather than adding progress**:
the connector locked by FBV2-COMM-001, Harwin `M20-7881242`, turned out to be
obsolete, and has been replaced by Samtec **`BCS-112-S-D-HE`**. The percentage does
not rise for repairing something that should not have been recorded as locked.

It does not fall either. Nothing that was genuinely achieved has been lost: the
24-contact allocation, the pin ordering, both accessory rails, the expander
architecture and the firmware contract all stand unchanged, and the replacement is
better on every measured axis — active and next-day stocked, a lower 5.33 mm
profile (Z spare 0.70 mm → **3.47 mm**), 4.6 A per contact, and extended-life
plating available. Three CTO opportunity rulings (O-1, O-2, O-3) were also
implemented.

**The percentage rule was applied honestly in both directions**: a correction is
not progress, and a corrected error is not a regression in what was actually built.

</details>

<details>
<summary>Superseded — the ~31% assessment as first written (FBV2-COMM-001)</summary>

**No gate in the twelve-gate table passed.** FBV2-COMM-LOCK is a *task* gate, not
one of the twelve, and it **PASSED** (2026-08-23, FBV2-COMM-001).

Raised three points. This was **the last architecture closeout before schematic
implementation**, and it earns three points for a specific reason: it closes the
final three pending CTO decisions that gated a schematic sheet — **P-02** (the
connector), **P-15** (the rail budget) and **P-16** — plus the long-standing
**B-08** WAKE-isolation defect, and it does so with a purchasable connector MPN, a
locked 24-contact pin ordering with a written mis-insertion proof, two protection
ICs verified line by line against their datasheets, and a binding firmware
mutual-exclusion contract.

It is **not** more than three because nothing was built, `hardware/beta-v2/` still
does not exist, and the design now has **zero spare expander capacity anywhere**
(B-37) — a constraint that will bite the first time a new I²C-mediated signal is
wanted.

</details>

<details>
<summary>Superseded — the ~28% assessment (FBV2-DISP-002)</summary>

**No gate in the twelve-gate table passed.** FBV2-DISP-LOCK is a *task* gate, not
one of the twelve, and it **PASSED** (2026-08-23, FBV2-DISP-002).

Raised three points, and **only** three, for a specific reason: this is the first
task in the programme that locked a **physical part with a purchasable MPN, a
mating connector proven from both manufacturers' drawings, and a driver circuit
re-derived to component values.** Everything before it was architecture on paper.
The three points are for **M-06 and M-07 closing**, which removes the last gate on
FBV2-S1 — sheet `03_spi_a_display_sd` is now unblocked and every sheet in the
migration can start.

It is **not** more than three because nothing was built: no schematic exists, no
board exists, `hardware/beta-v2/` does not exist, and the mating pair is proven on
paper rather than by a mated sample.

</details>

<details>
<summary>Superseded — the ~25% assessment (FBV2-MECH-001)</summary>

**FBV2-A2 PASSED** (2026-08-22, FBV2-MECH-001). Three of twelve gates now pass.
Every dimensional dependency that could have forced a late PCB redesign is
resolved: cavity, PCB envelope, battery, NFC/battery separation, connector exit,
antenna-vs-IR, USB/microSD, acoustics and mounting bosses.

Raised five points and **no more**. All three passed gates remain paper gates —
**no schematic exists, no PCB exists, no CAD exists**, and every mechanical figure
is TARGET (derived) rather than LOCKED (measured in CAD).

</details>

<details>
<summary>Superseded estimates</summary>

**~28%** — FBV2-DISP-002. **~25%** — FBV2-MECH-001. **~20%** — FBV2-PWR-002.
**~15%** — FBV2-PWR-001. **~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001.
**~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~20%

**FBV2-A1 PASSED** (2026-08-22, FBV2-PWR-002) — the first gate to pass since
FBV2-A0, and the largest remaining architecture unknown. All six criteria closed;
all 13 power/fault cases have defined safe behaviour; no power-tree branch remains
TBD.

Raised five points, and **deliberately not more.** Two of twelve gates have
passed and both are paper gates — no schematic exists, no board exists, and
**FBV2-A2 (mechanical) has not started**, with an internal cavity that has never
existed in this repository. Architecture certainty is not the same as progress
toward a working unit.

<details>
<summary>Superseded estimates</summary>

**~15%** — FBV2-PWR-001. **~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001.
**~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~15%

Raised from ~13% by **two points** for FBV2-PWR-001: five of the six FBV2-A1
criteria are now closed, the complete battery-protection topology is specified
element by element, and P-13 was closed outright by primary-source evidence.

**No gate passed. FBV2-A1 remains FAIL — but one CTO decision now closes it.**

<details>
<summary>Superseded estimates</summary>

**~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001. **~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~13%

Raised from ~10% by **three points** for FBV2-ARCH-002: four of the eight
FBV2-A1 criteria are now genuinely resolved, the mandatory power/fault state
table exists, and the NFC no-respin fallback is fully specified down to a
FIT/DNP matrix and a rework procedure.

**No gate passed. FBV2-A1 explicitly CANNOT PASS** — see the gate table.

<details>
<summary>Superseded estimate</summary>

**~10%** — recorded 2026-08-22 after FBV2-ARCH-001.
</details>

### Previous estimate: ~10%

Raised from ~8% by **two points only**, and only because FBV2-ARCH-001 closed
four pending CTO decisions (P-03, P-05, P-06, P-08, P-09) and verified nine
architecture facts against vendor datasheets.

**No gate passed.** FBV2-A1 is still IN PROGRESS. The estimate stays deliberately
low because the largest remaining unknowns — mechanical cavity, connector freeze,
reverse-polarity architecture, NFC supply topology — are all still upstream of
any drawing, and three of the four need a CTO decision rather than engineering
work.

---

## Gate table

| gate | description | status | date |
|---|---|---|---|
| **FBV2-A0** | Pre-design audit | **PASS** | 2026-08-22 |
| **FBV2-A1** | CTO architecture decisions | **PASS** | 2026-08-22 |
| **FBV2-A2** | Mechanical interface freeze | **PASS** | 2026-08-22 |
| **FBV2-S1** | Schematic migration / rearchitecture | **IN PROGRESS — 4 of 9 sheets.** `hardware/beta-v2/` forked from Beta-DM with a re-runnable byte-equivalence proof; `01_POWER_TREE`, `02_MCU_CORE`, `03_SPI_A_DISPLAY_SD` and `04_SPI_B_RADIOS_NFC` carry the v2 architecture (FBV2-S1-001 … 004); all four task gates **PASS**. Sheets `05`-`09` are byte-equivalent Beta-DM copies and still carry the Beta-DM architecture. **The gate does not pass until every sheet in the migration order is landed.** | — |
| **FBV2-S2** | ERC + footprint audit | **NOT STARTED** | — |
| **FBV2-P1** | Floorplan / placement | **NOT STARTED** | — |
| **FBV2-P2** | Routing | **NOT STARTED** | — |
| **FBV2-D1** | DRC / DFM / fab package | **NOT STARTED** | — |
| **FBV2-F1** | Fabrication / PCBA | **NOT STARTED** | — |
| **FBV2-B1** | Safe first power-up | **NOT STARTED** | — |
| **FBV2-B2** | Subsystem validation | **NOT STARTED** | — |
| **FBV2-B3** | Full showcase validation | **NOT STARTED** | — |

### Gate exit criteria

| gate | passes when |
|---|---|
| FBV2-A0 | A read-only audit pinned to a repository HEAD exists in `audits/`. **Met 2026-08-22.** |
| FBV2-A1 | Every item in the Pending CTO Decisions table of [CTO_DECISIONS.md](CTO_DECISIONS.md) is closed into a locked `D-xxx` ruling. |
| FBV2-A2 | Internal cavity X/Y/Z, wall thickness and PCB-to-wall clearance are published, and every dimensional dependency that could force a late PCB redesign is resolved. **Met 2026-08-22** via [mechanical/MECHANICAL_INTERFACE_SPEC.md](mechanical/MECHANICAL_INTERFACE_SPEC.md). ⚠ **`tools/check_mechanical_consistency.py` still reports UNKNOWN** — it parses the Field Slate v5 block, and FBV2-MECH-001 had **no authority** to modify `tools/` or the Field Slate. Reconciling the guard is a follow-up task, not a gate condition, because the guard reads a Beta-DM-era document rather than the v2 spec. |
| FBV2-S1 | `hardware/beta-v2/` exists, forked from Beta-DM with a byte-equivalence proof, and every schematic change in the migration order is landed. **Half met 2026-08-23:** the fork and its proof exist (`hardware/beta-v2/checks/fork_equivalence.py`, `hardware/beta-v2/reports/FBV2-S1-fork-equivalence.md`); **4 of 9 sheets** are landed. |
| FBV2-S2 | 0 ERC errors, 0 schematic-parity issues, and every project-library footprint verified against a vendor drawing with a per-footprint pad-overlap assertion. |
| FBV2-P1 | Outline derived from the published cavity; all mechanical keepouts instantiated; IR TX/RX escapes proven at placement time; U3/connector cluster placed at the right-side exit. |
| FBV2-P2 | Ratsnest zero including GND; no pin-specific budget exceptions. |
| FBV2-D1 | 0 DRC errors, 0 unconnected, same-net hole-to-hole checked at warning level, POFV control regenerated, BOM/CPL diffed against the MPN ledger rather than regenerated blind. |
| FBV2-F1 | Boards and assemblies received against a confirmed production file set. |
| FBV2-B1 | `+3V3` overshoot below 3.6 V; reversed-battery-with-USB fault test passed; no smoke, no thermal runaway. |
| FBV2-B2 | Each subsystem independently demonstrated. |
| FBV2-B3 | Full showcase demonstration on real hardware. |

---

## Current blockers

Carried from the pre-design audit (2026-08-22). Each maps to a pending CTO
decision or a mandatory gate.

### Fabrication blockers — cannot release to fab

| # | blocker | evidence | owner |
|---|---|---|---|
| **B-01** | **Reverse-polarity protection does not exist.** `BAT_CONNECTOR_P` is a single-pad net (`J4.1` only). Nothing bridges it to `BAT_PROTECTED_P`. The Design Decisions Log marks the block `DO NOT ROUTE. DO NOT RELEASE TO FAB.` A board built as-is will not run from battery at all. | Measured from the PCB pad-to-net map | CTO (P-01) |
| **B-02** | **Power / self-damage gates unresolved.** Regulator overshoot, NFC boost OVP, accessory-power reverse blocking, charger thermals, RF/audio/IR brownout budget. | Audit section 12 | Engineering + CTO (D-072) |
| **B-03** | **Footprint audit not performed.** Several project-library footprints are custom or explicitly marked "intended, not verified" — TCA9535PWR, `J5` Samtec, ST25R3916, MK1 custom pad ring, Ebyte modules, Coilcraft, TPS63020, MAX17048, BMI270, Hirose FPC. | Audit section 12 item 13 | Engineering (FBV2-S2) |

### Design blockers — cannot start placement

| # | blocker | evidence | owner |
|---|---|---|---|
| **B-04** | **Internal enclosure cavity has never been published.** `INTERNAL_CAVITY_MM: not published`, `WALL_THICKNESS_MM: not published`, `PCB_FIT_STATUS: UNVERIFIED`. The v2 board outline is a derived number and cannot be derived without it. | Field Slate v5 dimension authority table | CTO (P-07) |
| **B-05** | **20-pin connector architecture not locked.** C1/C2/C3 proposed, none approved. | Audit sections 6-7 | CTO (P-02) |
| **B-06** | **NFC is undesigned, not merely unrouted.** No 27.12 MHz crystal exists in the BOM; no matching network; no antenna. 13 dangling `*_TBD` nets on U9. | Measured: 13 single-pad nets on U9 | CTO (P-03, P-04) |

### Architecture defects — must be resolved in migration

| # | defect | evidence |
|---|---|---|
| ~~**B-07**~~ | ~~NFC rail architecture defect.~~ **RETIRED 2026-08-22 — the finding was wrong.** DS12484 Rev 3 p. 39 requires VDD and VDD_TX to share one supply; Tables 118/119 cap their difference at ±0.3 V abs max / ±0.2 V operating. The as-built assignment is **correct**. The residual sequencing question is now **P-10**. | ST25R3916 DS12484 Rev 3, Tables 2 / 118 / 119 |
| **B-08** | **WAKE line has no isolation gate.** The mandated open-drain gate powered from switched accessory power was never implemented; only `R66` 330R exists. A shorted accessory pin can permanently block internal button wake. | Measured: `WAKE_ATTN_N_HDR` = `D7.1`, `J5.13`, `R66.2` |
| **B-09** | **GPIO3 has no strap-defining pull.** Required by the pin map, not implemented. Hazard currently low (the S3 ignores the GPIO3 strap unless `JTAG_SEL_ENABLE` is burned) but it leaves a CMOS input floating at reset. | Measured: `BMI270_INT1_STRAP` = `R18.2`, `TP3.1`, `U1.15` |
| **B-10** | **Zero free native GPIO.** 29 assigned + 2 strap test pads + 2 USB = 31 of 31 usable. | Measured from U1 pads |
| **B-11** | **GPIO18 / GPIO38 documentation mismatch.** The pin map states GPIO18 = SX1262 DIO1 and GPIO38 = NFC IRQ. The hardware is the reverse. | Measured from U1 pads |
| **B-12** | **Possible LoRa wake defect.** `SX1262_DIO1` on GPIO38 is not RTC-capable, so wake-on-LoRa-packet is impossible in the current pinout. | Consequence of B-11 |
| **B-13** | **RGB LED nets dangling.** `RGB_R/G/B_CTL` exist with one pad each; no LED part exists. | Measured: 3 single-pad nets |
| **B-14** | **RootProbe cannot connect.** `ROOTPROBE_IRQ_READY_N` has no header pin. | Measured: net = `R11.2`, `U2.20` |
| **B-15** | **No charge or VBUS telemetry.** `BQ25185_STAT1` reaches `TP6` only, `STAT2` reaches `TP7` only, `MAX17048_ALRT_N` reaches `TP11` only. No VBUS-present sense exists. The product cannot report charging state. | Measured from the PCB |

### Documentation defects

| # | defect |
|---|---|
| **B-16** | Field Slate v5 section 5 still lists "Volume +, Volume −, Power" on the right side. Volume controls have never existed electrically. The locked external layout text needs a CTO-approved correction so enclosure CAD is not driven by phantom controls. |

---

### FBV2-A1 gate assessment (2026-08-22, FBV2-PWR-002) — **PASS**

| criterion | status |
|---|---|
| Dead-cell recovery topology explicit | **YES** — Candidate B specified to component level: ratiometric bridge, thresholds, defaults, 3-input AND, FAULT handoff, full failure analysis |
| Main reverse protection single-FET-short tolerant | **YES** — P2, two back-to-back stages in **two separate packages**. Isolation, not fault-clearing time |
| All power/fault states have defined safe behaviour | **YES** — 13 of 13 |
| No additional power-tree branch remains TBD | **YES** — the recovery branch was the last one |

**FBV2-A1 = PASS.** Component-value optimisation (exact `R_LIM`, FET MPN, fuse
rating, divider trim) moves to schematic design.

**Next gate: FBV2-A2 — MECHANICAL INTERFACE FREEZE.** Long pole, nothing blocks
it. **Do not start FBV2-S1 before the placement constraints exist.**

<details>
<summary>Superseded — FBV2-A1 assessment (FBV2-PWR-001, FAIL)</summary>

### FBV2-A1 gate assessment (2026-08-22, FBV2-PWR-001)

| # | criterion | status |
|---|---|---|
| 1 | PCAL9535A choice closed | **YES** — D-061; no pin/package incompatibility found |
| 2 | GPIO38/GPIO47 closed | **YES** — D-063; DIO1 level-hold confirmed verbatim from Semtech §13.3.4 |
| 3 | NFC architecture closed | **YES** — D-055/D-056 |
| 4 | Community power architecture closed | **YES** — D-057/D-058 |
| 5 | 20-pin resource architecture closed | **YES** — D-062 |
| 6 | **Reverse-protection topology complete, no major new power-tree branch TBD** | **NO — P-11** |

**Verdict: FAIL.** Criteria 1–5 are closed and the reverse-protection topology
itself is complete (controller, dual N-FET, R_SENSE 15 mΩ, R_GATE 22 kΩ,
C_GATE 1 nF, UV recommended unused, OV divider, RETRY grounded, SHDN pull-up to
VIN, FAULT, fuse, clamp). **The dead-cell recovery branch (P-11) is a new
power-tree branch and is not chosen.** Per the CTO's instruction — *"Do not pass
the gate merely because a preferred idea exists"* — the gate is not passed.

**One decision closes it.** Selecting Candidate B or Candidate D closes criterion
6; P-12 then carries into the schematic phase as a bench item, since it changes
no topology.

</details>

### Blockers added or changed by FBV2-COMM-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~D-083~~ | **Harwin `M20-7881242` REJECTED as obsolete** — `harwin.com` returns HTTP 404 for it. The MPN had been *configured from the catalogue ordering scheme*, and FBV2-COMM-001 §15 had flagged exactly that risk | **CORRECTED.** Replaced by Samtec `BCS-112-S-D-HE` (D-093) |
| **D-096** | **New standing rule:** a part number configured from an ordering scheme is a hypothesis, not a selection. Every MPN written into a locked document must first be confirmed against a live manufacturer or distributor record showing lifecycle and stock | **STANDING** |
| **B-39** | **Mating-cycle rating unconfirmed.** Only **100 cycles** is formally qualified for BCS; the **2 500-cycle** E.L.P. figure is **by similarity at 30 µin gold**. Confirm the rated count for `BCS-112-S-D-HE` with Samtec before production | **OPEN, medium.** Procurement |
| **B-40** | Which mating row terminates in which PTH row of the 7.87 mm pattern must be read off the Samtec print, not assumed | **OPEN, low.** FBV2-S2 |
| **B-29** | **Re-scoped.** The footprint must now be drawn to Samtec FIG 3 `BCS-1XX-XXX-D-HE`: 2 × 12 PTH, **2.54 mm within a row, 7.87 ± 0.05 mm between rows, 0.71 mm drill** — *not* interchangeable with any vertical 2×12 pattern | **OPEN, medium.** FBV2-S2 |
| **B-37** | Zero spare expander capacity | **HALF CLOSED by O-1.** `U3` now holds one `RESERVED_SPARE` (P16, test pad + 100 kΩ pull-up, no function assigned). **`U2` remains 16/16 with zero spare** |
| **M-09** | Connector body height | **DOWNGRADED to LOW.** Z column falls from 22.30 mm to **19.53 mm of 23.0 — 3.47 mm spare**; it is no longer the sole governing column. Confirm 5.33 mm against the Samtec 3D model at FBV2-P1 |
| **M-10** | Insertion load path | **DOWNGRADED.** ≈ **33 N average** (was ≈ 48 N max), peak higher. Enclosure boss still required (D-097) |
| **P-19** | The 24Cxx family spans `0x50`–`0x57`; only `0x50` is reserved. May need widening if multi-EEPROM accessories appear | **OPEN, low.** CTO, with P-18 |
| ~~O-1~~ | Wire-OR the `FLT` lines | **APPROVED and implemented** (D-094) |
| ~~O-2~~ | Accessory-ID EEPROM address `0x50` | **APPROVED and implemented** (D-095) |
| ~~O-3~~ | Share the accessory boost with the NFC fallback | **REJECTED and struck** (D-095) |

**Two NEW opportunities are flagged for a CTO ruling and were deliberately NOT
locked:** **N-1** publish an accessory reference design (footprint, the 4.34–6.35 mm
post-length rule, the detect-strap pattern, the shared-rail current rule, a board
template) — high value, documentation-only; **N-2** accessory retention — withdrawal
force is only ≈ 20 N average with no latch, so an enclosure detent or captive
fastener is worth considering.

### Blockers added or changed by FBV2-COMM-001 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~P-02~~ | Freeze the 20-pin connector | **CLOSED** — the 20-pin architecture is **superseded**; the port is 2×12 / 24 active contacts, female, `Harwin M20-7881242` (D-081…D-085) |
| ~~P-15~~ | 3V3 rail budget under simultaneous worst case | **CLOSED** — binding mutual-exclusion contract MX-1…MX-9 (D-092) |
| ~~P-16~~ | Repurpose one XGPIO as `ACC_DETECT`? | **CLOSED** — dedicated contact (pin 23) and dedicated `U3` input (D-082/D-085) |
| ~~B-08~~ | **WAKE line has no isolation gate** — a shorted accessory pin can permanently block internal button wake | **CLOSED** — one N-FET pass gate, gate driven by `ACC_3V3_SW` (D-091) |
| **B-34** | ≈ **0.70 W of series loss and ≈ 0.40 V of drop** in the BQ25185 BATFET (115 mΩ) + reverse-protection path at 1.75 A, inside a sealed enclosure | **OPEN, medium.** FBV2-S1 thermal review |
| **B-35** | **`TPS22950C` `FLT` does not assert on plain current limiting** — only on thermal shutdown and reverse current. A hard short reaches TSD in tens of ms and is then reported; a **partial** overload is invisible to the host | **OPEN, documented.** Firmware contract |
| **B-36** | Accessory-initiated wake now requires `ACC_3V3_SW` to remain enabled during sleep — a consequence of the B-08 gate | **OPEN, policy.** FBV2-B2 |
| **B-37** | **ZERO spare expander capacity on BOTH `U2` (16/16) and `U3` (16/16).** Any new I²C-mediated signal must displace an existing one | **OPEN — standing constraint** |
| **B-38** | The 5 V boost inductor must be **1 µH with `I_sat` ≥ 3 A** to survive a fault at the load switch's worst-high limit | **OPEN, low.** FBV2-S1 |
| **M-09** | The **connector region is the new governing Z column** — 22.30 mm of 23.0 mm external, 0.70 mm spare | **OPEN.** FBV2-P1 |
| **M-10** | Up to **48 N** insertion force; the enclosure must carry it on a boss/rib | **OPEN.** Enclosure CAD |
| **P-18** | External-I²C segmentation | **HALF ANSWERED.** The bus-hang half is closed (the buffer's B-side rides `ACC_3V3_SW`, now default-OFF and detect-gated). **Address collision still needs a CTO ruling** |

**Three opportunities are flagged for a CTO ruling and were deliberately NOT
locked:** wire-OR the two `FLT` lines to recover one expander pin; reserve an I²C
address for an accessory-ID EEPROM; a DNP 0 Ω link letting the accessory boost also
serve the NFC 5 V fallback.

### Blockers added or changed by FBV2-DISP-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~M-06~~ | Display MPN and FPC interface | **CLOSED** — `ER-TFT035IPS-6` + `ER-TPC035-6`; 50-pin, 0.50 mm, **bottom contact**, 0.30 ± 0.03 mm; FT6236 @ 0x38 (D-074/D-075) |
| ~~M-07~~ | Backlight driver re-derivation | **CLOSED** — TPS61169 retained from `+3V3`; `R69` = 1.87 R, `R70`–`R73` = 4 × 33 R; switch-peak margin 4.6× (D-079) |
| **B-28** | **ILI9488 `SDO` on the shared SPI-A bus is unverified.** Mitigated by design: fit a 0 R `R_SDO` isolation link plus a test point so the display can be made write-only without a respin | **OPEN, mitigated.** Closes at FBV2-B2 |
| **B-29** | **`J1` footprint must be redrawn** on the FH12-horizontal / FH52E standard land pattern (D-077) and verified with a per-footprint pad-overlap assertion against **both** connector drawings | **OPEN.** Closes at FBV2-S2 — folds into B-03 |
| **B-30** | The datasheet does not name which FPC pin feeds the FT6236 VDD. Immaterial here — VDDI, VCI and the CTP supply are all `+3V3` | **OPEN, informational.** First article |
| **B-31** | Display FPC contact plating is not stated; Hirose recommends gold | **OPEN, low.** PO / first article |
| **B-32** | Confirm ≥ 4.7 µF X5R input decoupling local to `U17` `VIN` — input ripple current rises ~47 % | **OPEN, low.** FBV2-S1 |
| **B-33** | **The 2.3 mm `J1` cannot sit in the display shadow** (0.8 mm limit). It competes for the 70.04 mm below the panel with the D-pad, A/B and the mic aperture | **OPEN.** Placement coupling; closes at FBV2-P1 (tracked as M-08 in the mechanical spec) |

**Two MEDIUM procurement risks remain and neither is a design change:** the vendor
also sells a CST340 touch panel for this size, so the purchase order must name
`ER-TPC035-6`; and the datasheet carries a "Backlight Update" revision, so
Rev 2.0 (18-Aug-2025) must be archived in-repo and cited by revision in the MPN
ledger.

### Blockers added or changed by FBV2-PWR-002 (2026-08-22)

| # | blocker | status |
|---|---|---|
| ~~B-20~~ | Dead-cell lockout created by the reverse protection | **CLOSED** — autonomous hardware-qualified recovery branch (D-065), specified to component level. No firmware dependency |
| ~~B-21~~ | Shorted pass FET reproduces the guarded fault | **CLOSED by isolation** — P2, two stages, two packages. The old fuse+clamp compliance argument is **withdrawn as invalid** |
| ~~B-23~~ | PCAL9535A facts unverified | **CLOSED** — CTO verified NXP Rev 2 (D-066). Land-pattern audit remains a separate pre-fab gate |
| **B-26** | **Pack-protector release current.** Recovery injects ~8 mA; a 1S protector needing more than ~10 mA to release its over-discharge latch would not be revived | **OPEN — part-dependent.** Verify against the chosen pack. Does not change topology |
| **B-27** | **Recovery branch is not tolerant to every single failure** — four failures each enable current into a reversed cell | **ACCEPTED, BOUNDED.** `R_LIM` caps every case at ≈13 mA (~0.007 C); `D_REC` keeps the branch unidirectional; the fault is self-annunciating |

<details>
<summary>Superseded — FBV2-A1 gate assessment (FBV2-ARCH-002)</summary>

### FBV2-A1 gate assessment (2026-08-22, FBV2-ARCH-002)

| # | criterion | status |
|---|---|---|
| 1 | 20-pin resource architecture resolved | **YES** — 11 XGPIO + 2 native + 2 I²C + 1 WAKE + 1 switched power + 3 GND = 20 |
| 2 | Expander family resolved | **NO** — PCAL9535A pin table not retrievable from a primary source |
| 3 | Native GPIO pair resolved | **NO** — GPIO38 gated on unverified SX1262 DIO1 level-hold behaviour |
| 4 | Default NFC architecture resolved | **YES** — 3.3 V, `sup3V`, VDD = VDD_TX = `NFC_SUPPLY`, VDD_IO = `+3V3` |
| 5 | NFC no-respin fallback resolved | **YES** — FIT/DNP matrix + rework procedure complete |
| 6 | Community accessory power resolved | **YES** — TPS22950C, permanent `+3V3` pin removed |
| 7 | Battery/reverse protection resolved at topology level | **NO** — dead-cell recovery and inrush/latch interaction both change the power tree |
| 8 | No unresolved issue can change the power-tree architecture | **NO** — P-11 adds a switched path across the pass FETs plus an ADC divider |

**Closing actions:** three of the four gaps are document reads (PCAL9535A pin
table; SX126x + E22 IRQ sections). The fourth is one CTO decision (P-11) plus one
protoboard experiment (P-13).

</details>

### Blockers added or changed by FBV2-S1-004 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-41**~~ | `NFC_SUPPLY` has no consumer | **CLOSED 2026-08-23 by D-122.** `U9` `VDD`/`VDD_TX` moved off the Beta-DM boost output; the 3.3 V FIT / 5 V DNP select now drives something |
| **B-06** | NFC is undesigned, not merely unrouted | **LARGELY CLOSED.** A real 27.12 MHz crystal and a real differential matching topology exist; only the antenna choice (B-53) and the tuning values (B-48) remain |
| **B-48** | **AN5276 not retrieved** — every st.com fetch timed out. All matching and RX-divider values are **initial values** | **OPEN, high.** Run STSW-ST25R004 against a measured antenna impedance before the BOM gate. No value is presented as an ST reference figure |
| **B-49** | **IPEX socket population must be confirmed with the supplier** for the exact ordered `U7`/`U8` MPNs — Ebyte sells IPEX and stamp-hole variants under similar numbers | **OPEN, high.** The entire zero-board-RF plan collapses if stamp-hole units arrive. Hard procurement deadline |
| **B-50** | FXP450 bend radius, adhesive, ground clearance and temperature not retrieved — the datasheet is image-based beyond page 1 | **OPEN, medium.** Mechanical input for FBV2-P1 |
| **B-51** | 915 MHz pigtail assembly MPN not selected — the interface is locked, the part is not (D-096) | **OPEN, medium** |
| **B-52** | Top-panel spacing between the SMA bulkhead and the IR apertures recorded (**≥ 8 mm**, pigtail clear of the optical path) but **no CAD exists** | **OPEN, medium** |
| **B-53** | **NFC antenna architecture undecided** — main-board loop vs purchased flex + ferrite vs daughter antenna | **OPEN, high.** Recommendation: **flex + ferrite**. A main-board loop needs a 45 × 45 mm ground-plane keepout on every layer with the battery behind it |
| **B-54** | **ST25R3916 field current at 3.3 V not extracted.** The NFC PA load has moved from `SYS` to `+3V3`, so the TPS63020 budget does not yet include it | **OPEN, high.** D-092's 58-66 % figure must not be quoted as covering the NFC field in this form |

### Blockers added or changed by FBV2-S1-003 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-43**~~ | TPS61169 `CTRL` internal-pull specification not retrieved | **CLOSED 2026-08-23 by D-116.** SNVSA40B: **`R_PD` = 300 kΩ internal PULL-DOWN**, `V_H`/`V_L` 1.2/0.4 V. `CTRL` can only pull GPIO46 down — the strap is safe by construction, not merely by margin |
| ~~**B-32**~~ | Confirm ≥ 4.7 µF X5R local to `U17` `VIN` | **CLOSED** — `C43` 4.7 µF 0805 on `+3V3` at `U17.5`, marked `4.7uF 10V X5R` |
| ~~**B-28**~~ | ILI9488 `SDO` on a shared bus | **CLOSED by D-114** — `R112` 0 Ω **DNP**, `TP36` on the panel side. Opposite default to the one FBV2-DISP-002 sketched, because fitting risks the microSD to gain a feature nothing uses |
| **B-46** | **microSD detect-switch polarity assumed, not confirmed** — the Molex drawing would not load. `SD_CARD_DETECT_N` assumes switch-closes-on-insertion | **OPEN, low.** Firmware constant on a PCAL9535A input; never a board change |
| **B-47** | **FH52E second source and land-pattern migration unresolved.** Drop-in equivalence was **not** asserted without both Hirose drawings, so `J1` stays on the FH69-dedicated pattern | **OPEN, medium. There is currently no JLCPCB assembly path for `J1`.** Settle at FBV2-S2, before placement |
| **B-29** | `J1` land pattern verified with a pad-overlap assertion | **STILL OPEN, advanced.** Pad geometry measured: 50 pads, 0.500 mm pitch with no drift, 24.500 mm span, 0.300 × 1.230 mm pads, 2 hold-downs. The assertion itself is FBV2-S2 |

### Blockers added or changed by FBV2-S1-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-09**~~ | GPIO3 has no strap-defining pull; a CMOS input floats at reset | **CLOSED 2026-08-23 by D-109.** `R110` 10 kΩ pull-down at the MCU pin. LOW is the only correct level — GPIO3 = 1 would select external JTAG on GPIO39-42, which are the I²S bus. BMI270 `INT1` is bound to push-pull active-high; open-drain is forbidden on this pin |
| **B-43** | **TPS61169 `CTRL` internal-pull specification not retrieved** — TI's PDF text layer would not extract this session | **OPEN, low.** The GPIO46 strap is safe for any internal pull-up ≥ 30 kΩ with `R108` = 10 kΩ, and `R109` 0 Ω is the isolation escape. Confirm at FBV2-S2 |
| **B-44** | **BMI270 `INT` pad drive current not retrieved** — Bosch's PDF text layer would not extract. Driving `R110` + `R18` costs 323 µA | **OPEN, low.** Fallback if Bosch specifies less: `R110` → 47 kΩ (70 µA), a value change with no board change |
| **B-45** | **`NATIVE_A` / `NATIVE_B` have no protection yet.** D-090 requires 100 Ω series on both native pins plus a low-capacitance TVS array; both belong beside the connector | **OPEN, high.** These are the only two contacts with a direct MCU path. Sheet `09` work |
| **B-27** | Recovery branch is not tolerant to every single failure | **AMENDED 2026-08-23 by D-105.** The ceiling is **≈ 15.9 mA nominal / ≈ 16.6 mA worst case**, not ≈ 13 mA — 680 Ω was the value that produced the old figure. Still ~0.0066 C, still bounded, still self-annunciating |
| **B-15** | No charge or VBUS telemetry reaches the MCU | **STILL OPEN, unchanged by this task.** The crossings are sheet `08`/`09` |

### Blockers added or changed by FBV2-S1-001 (2026-08-23)

| # | blocker | status |
|---|---|---|
| **B-41** | **`NFC_SUPPLY` has no consumer.** The 3.3 V-FIT / 5 V-DNP source select exists on `01_POWER_TREE`, but `U9` `VDD` and `VDD_TX` are still on `NFC_5V_PA_PENDING` — the Beta-DM arrangement — because they live on sheet `04`, which FBV2-S1-001 was not authorised to modify | **OPEN, high.** The v2 NFC supply architecture is **half implemented**. First item of the sheet-`04` migration |
| **B-42** | **The NFC source select is mutually exclusive by FIT STATE ONLY.** Fitting both `R106` and `R107` shorts `+3V3` to the 5 V boost output. Nothing in copper prevents it | **OPEN, low.** Inherent to a 0 Ω source-select and exactly the mechanism D-049 asks for, but it must become an assembly-note and fab-drawing requirement |
| ~~**B-01**~~ | Reverse-polarity protection does not exist; `BAT_CONNECTOR_P` is a single-pad net | **CLOSED AT SCHEMATIC LEVEL 2026-08-23.** `BAT_CONNECTOR_P` = `J4.1` + `F1.1` + `TP34.1`; the full P2 chain to `BAT_PROTECTED_P` is captured. **Not closed at board level** — the PCB is still the Beta-DM board |
| **B-15** | No charge or VBUS telemetry | **STILL OPEN, advanced.** The `VBUS_PRESENT` divider (2.97 V at VBUS 5.0 V) now exists, as do `BQ25185_STAT1/2` and `ACC_POWER_FAULT_N`. **None of them crosses to `U2`/`U3` yet** — those crossings are on sheets `08`/`09` |
| **B-03** | Footprint audit not performed | **STILL OPEN, widened.** `U18` LTC4368-1 had been assigned a **DFN-10 exposed-pad** footprint against the locked *"no bottom-terminated parts"* package policy; corrected to MSOP-10. The land pattern itself is still unverified, and `U18`-`U22`, `Q2`-`Q9`, `D9`-`D12`, `F1`, `R75`, `L4` all join the FBV2-S2 list |

### Pending decisions opened by FBV2-S1-001

| # | item |
|---|---|
| **P-20** | **`R95` = 680 R against a locked `R_LIM` of 560 R.** Recovery injection falls from ≈ 8.4 mA to **≈ 6.9 mA** into a 0 V pack, moving the wrong way against **B-26**. Keep 680 R or restore 560 R |
| **P-21** | **`OV` trip captured at 5.05 V** (`R77` 4.02 M / `R78` 442 k) against a documented *"divider ≈ 4.6 V"*. Confirm the captured number or correct it |
| **P-22** | The standing *"do not generate or modify KiCad files automatically"* rule was overtaken — this capture was scripted, then verified with `kicad-cli` ERC and a netlist export. **Ratify or reinstate.** Recorded in place, not treated as repealed |

### Blockers added or changed by FBV2-PWR-001 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-20** | Dead-cell lockout created by the reverse protection | **STILL OPEN — P-11.** Now fully characterised: LTC4368 VIN UVLO 1.8/2.2/2.4 V; VOUT is a *sense* input and its charge-pump role only applies above ~5 V, so **system-side power cannot run the controller**. No inherent recovery path exists. Four candidate architectures analysed; **B recommended** |
| **B-21** | Shorted pass FET reproduces the guarded fault | **BOUNDED, not closed.** Clamp + fuse reduce the excursion from ≈−3.7 V to ≈−1 V, still ~3× the −0.3 V DC abs max. Residual is **P-12** |
| ~~B-22~~ | Latch-off vs hot-insertion inrush | **CLOSED.** Inrush is a designed parameter; latch-off applies to forward OC only |
| **B-23** | PCAL9535A pin table not obtainable from a primary source | **STILL OPEN, but no longer blocking.** Architecture locked by D-061; four secondary-sourced facts deferred to the land-pattern audit |
| ~~B-24~~ | SX1262 DIO1 level-hold unverified | **CLOSED** — confirmed verbatim from Semtech §13.3.4 (Rev. 1.2; re-confirm against V2.2 pre-fab) |

### Blockers added or changed by FBV2-ARCH-002 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-20** | **Dead-cell lockout created by the reverse protection.** Below LTC4368 UVLO (1.8–2.4 V) both gates are off and the body diodes are anti-series — a ~0 V pack can never be recharged. | **OPEN — P-11. Blocks FBV2-A1.** |
| **B-21** | **Shorted pass FET reproduces the guarded fault.** Without a fuse + Schottky clamp, −3.0 to −4.35 V lands on BQ25185 BAT against a −0.3 V abs max — a 10–14× DC violation. | **Mitigation identified** (fuse + clamp, required not optional); survivability of the residual excursion is **P-12**. |
| **B-22** | **Latch-off vs hot-insertion inrush unreconciled.** | **OPEN — P-13. Blocks FBV2-A1.** |
| **B-23** | **PCAL9535A pin table not obtainable** from a primary source (NXP 404, Digi-Key 410, Mouser HTML). | **OPEN.** Blocks criterion 2. One document read. |
| **B-24** | **SX1262 DIO1 level-hold behaviour unverified** (Semtech domain did not resolve; Mouser mirror returned HTML). | **OPEN.** Blocks criterion 3. Read the SX126x **and** E22-900M22S IRQ sections. |
| **B-25** | **Permanent raw `+3V3` connector pin** — unprotected always-live tap; defeats whatever is fitted on the switched pin. | **CLOSED by D-057** — pin removed from the 20-pin map. |
| ~~B-18~~ | TPS22918 lacks reverse-current blocking | **CLOSED by D-058** — replaced with TPS22950C (RCB confirmed for the C variant). My earlier TPS22913B/C suggestion was **wrong** — DSBGA-only and no current limit. |

### Blockers added or changed by FBV2-ARCH-001 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-17** | **NFC supply topology undecided (P-10).** With TPS61023 true load disconnect confirmed, disabling the boost leaves VDD = VDD_TX = 0 V while VDD_IO = 3.3 V — unauthorised by DS12484 Table 119 (VDD min 2.4 V). | **OPEN — CTO decision.** N1 (3.3 V-only, delete the boost) recommended. |
| **B-18** | **`TPS22918` has no reverse-current blocking.** Datasheet confirms the integrated body diode conducts VOUT→VIN. An externally powered accessory can back-power `+3V3` through `ACC_3V3_SW`. | **OPEN.** Replacement identified (TPS22913B/C class); exact MPN needs a page-cited datasheet check. |
| **B-19** | **`NFC_IRQ` must never move to GPIO46.** A latched-high IRQ would block Joint Download Boot and make ROM-download recovery conditional on NFC state. | **CLOSED as a design rule** — recorded so it cannot be reintroduced. |
| ~~B-11 / B-12~~ | GPIO18/GPIO38 documentation mismatch and LoRa wake | **Mismatch still to fix in migration.** The *wake* consequence is retired by D-041 — LoRa deep-sleep packet wake is not a v2 requirement. |
| **B-16** | Field Slate v5 §5 lists phantom Volume controls | **Still open.** Needs a CTO-approved text correction. |

**Retired by verification:** B-07 (see above). **Partially advanced:** B-03 — `U9`'s
33-pad footprint mapping is now verified correct against three independent
DS12484 tables; every other footprint remains unverified.

---

## Change log for this file

| date | change |
|---|---|
| 2026-08-23 | FBV2-S1-004. Overall raised 40% → 43%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-RADIOS-NFC = PASS**. **`04_SPI_B_RADIOS_NFC` MIGRATED.** **RF architecture locked (D-118):** 433 MHz internal Taoglas `FXP450.07.0100C` (IPEX MHF-I mating **proven** against the module's IPEX-1 socket), 915 MHz external to a top-panel **SMA female** bulkhead; **no board RF trace, matching network, switch or diplexer in either band**; the `U7` IPEX must stay service-accessible. Both module stamp-hole pins are explicit no-connects. **NFC: B-41 CLOSED** — `VDD`/`VDD_TX` moved to `NFC_SUPPLY` = `+3V3` (D-122, `sup3V` firmware requirement); **`Y1` 27.12 MHz crystal** + load caps (D-123); **real differential matching and RX-divider topology** with every value `TUNE` and two trim positions per TX leg (D-124); `AAT`, `CSI/CSO`, `EXT_LM`, `MCU_CLK` explicit no-connects with recorded reasons. **`SX1262_DIO1` published for sheet 08.** **Zero `*_TBD` nets remain in the project.** **ERC 4 errors → 2, total 86 → 68, zero added** — the first migration task to reduce the error count. **P-17 recommended for closure (keep the non-B); B-53 opened** (antenna architecture). B-48, B-49, B-50, B-51, B-52, B-54 opened. PCB untouched and still bit-identical to Beta-DM. | Overall raised 37% → 40%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-DISPLAY-SD = PASS**. **`R111` FITTED** (D-111). **`03_SPI_A_DISPLAY_SD` MIGRATED:** new `ER-TFT035IPS-6_50P` symbol with the vendor pin table verbatim, **catching two dead-on-arrival faults in the inherited `J1`** — reversed backlight anode/cathode and swapped SCL / D-CX. Touch gains `TOUCH_INT_N` (panel pin 46, previously unrepresented). Backlight re-derived: `R69` **1.87 Ω**, `R70`–`R73` **4 × 33 Ω**, I_LED **109 mA typ / 117.6 mA worst case** against a 120 mA panel maximum; peak switch current 4.6× (3.9× at f_SW min). `SD_CARD_DETECT_TBD` → **`SD_CARD_DETECT_N`** with a 100 kΩ pull-up. `R112` 0 Ω **DNP** isolates the display SDO from the shared SPI-A. **B-43, B-32, B-28 CLOSED; B-46, B-47 opened.** `/03_SPI_A_DISPLAY_SD/LED_A` added to the `LED_BOOST` netclass — a latent FBV2-P2 defect no probe would have caught. **ERC 4 errors → 4 errors, error report byte-identical.** PCB untouched and still bit-identical to Beta-DM. | Overall raised 34% → 37%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-MCU-CORE = PASS**. **P-20, P-21 and P-22 CLOSED** (D-104…D-110). `R95` locked at **560 Ω** — recovery **8.36 mA** nominal, and **B-27's ceiling amended to ≈ 15.9 mA** because 680 Ω was the value that produced its old ≈ 13 mA figure. LTC4368 **OV trip derived to 4.63 V** (`R77` 3.65 M / `R78` 442 k) from the datasheet's 492.5/500/507.5 mV threshold; **removes a BOM line**. Scripted KiCad edits permitted under an **eight-condition** standing rule. **`02_MCU_CORE` MIGRATED:** GPIO38 = `NATIVE_A`, GPIO47 = `NATIVE_B`, GPIO46 = `DISP_BL_CTL` with `R108` 10 kΩ strap pull-down + `R109` 0 Ω isolation link + `TP2`, GPIO43 withdrawn from the community port (`TP35` UART0 TXD), **GPIO3 strap closed — B-09 retired**, `R111` 10 kΩ GPIO45 pull-down placed **DNP**. **ERC 5 errors → 4, zero new; `02_MCU_CORE` clean.** B-43, B-44, B-45 opened. **NO NEW DEBUG HARDWARE** — USB Serial/JTAG is the service interface. PCB untouched and still bit-identical to Beta-DM. | Overall raised 31% → 34%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-POWER-TREE = PASS**. **First Full Beta v2 design-file work.** `hardware/beta-v2/` forked from Beta-DM with a **re-runnable** byte-equivalence proof; **`01_POWER_TREE` CAPTURED** — P2 reverse protection with `U18` LTC4368-1, autonomous dead-cell recovery, `ACC_3V3`/`ACC_5V` on one consolidated boost + load-switch BOM, NFC 3V3-FIT/5V-DNP select, `VBUS_PRESENT` telemetry, 19 test points, 136 parts. **ERC 58 baseline → 55, zero introduced** (three inherited violations retired). **B-01 closed at schematic level.** `U18` package corrected from a policy-violating DFN-10 to MSOP-10. Inherited `R_FB_TOP 1M` net label renamed `V3V3_FB`. **D-099…D-103 recorded; B-41, B-42, P-20, P-21, P-22 opened.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-22 | Created. FBV2-A0 recorded as PASS. Initial blocker set B-01 through B-16 imported from the pre-design audit. |
| 2026-08-22 | FBV2-ARCH-001. Overall raised 8% → 10%; **no gate passed.** B-07 retired as incorrect. B-17/B-18/B-19 added. FBV2-A2 marked as the recommended next gate. |
| 2026-08-22 | FBV2-ARCH-002. Overall raised 10% → 13%; **no gate passed. FBV2-A1 assessed CANNOT PASS** (4 of 8 criteria). B-18 closed, B-25 closed. B-20…B-24 added. P-11…P-18 opened. Standing **NO-RESPIN RECOVERY POLICY** (D-049) established. |
| 2026-08-22 | FBV2-PWR-001. Overall raised 13% → 15%; **no gate passed. FBV2-A1 FAIL, 5 of 6 criteria closed.** D-061…D-064 recorded. **P-13 and B-24 closed** by primary-source evidence; B-22 closed. Complete battery-protection topology specified. Fuse **REQUIRED**, clamp **REQUIRED**, PTC **REJECTED**. |
| 2026-08-22 | FBV2-DISP-001. **No gate passed — percentage holds at 25%.** D-071/D-072/D-073 recorded. Display size LOCKED at **3.5″**; battery envelope LOCKED. **Display MPN and J1 deliberately NOT locked** — old-J1 compatibility is **UNPROVEN**. ESP32-S3 SPI verdict **PASS** (FSPI IO_MUX, 80 MHz, no bus merge). M-01/M-02 closed; **M-06/M-07 opened.** |
| 2026-08-22 | FBV2-MECH-001. Overall raised 20% → 25%. **FBV2-A2 = PASS.** D-069/D-070 recorded; cavity **75.0 × 155.0 × 18.5 mm** derived; PCB target **70 × 148**; **P-07 closed**; M-01/M-02 opened. Beta-DM 74 × 155 outline ruled **RE-FLOORPLAN REQUIRED**. Next gate: **FBV2-S1**. |
| 2026-08-23 | FBV2-COMM-002. **Overall HELD at 31% — a correction is not progress.** **Harwin `M20-7881242` REJECTED as obsolete** (404 on harwin.com; the MPN had been configured from an ordering scheme, which FBV2-COMM-001 had flagged). **Connector re-locked: Samtec `BCS-112-S-D-HE`** — 2×12 female Tiger Claw, horizontal entry, through-hole, 30 µin gold, ACTIVE, 385 pcs next-day, MOQ 1, 4.6 A/contact. `-S` chosen over the proposed `-L` because Samtec qualifies **both** platings at only **100 cycles** and the **2 500-cycle** extended-life data exists **only at 30 µin gold** — +$2.88/board. **Z column improves 22.30 → 19.53 mm of 23.0 (3.47 mm spare).** Pin ordering and electrical architecture **unchanged**. **O-1 approved** (`FLT` wire-OR → `ACC_POWER_FAULT_N`, `U3` P16 = `RESERVED_SPARE`), **O-2 approved** (I²C `0x50` reserved for an accessory-ID EEPROM), **O-3 rejected**. D-093…D-098 recorded; B-39, B-40, P-19 opened; B-37, M-09, M-10 downgraded. |
| 2026-08-23 | FBV2-COMM-001. Overall raised 28% → 31%. **No gate in the twelve-gate table passed**; the task gate **FBV2-COMM-LOCK = PASS**. **The 20-pin community port is SUPERSEDED.** New port **2×12, 24 active contacts, FEMALE device side**, ~~`Harwin M20-7881242`~~ *(rejected as obsolete 2026-08-23 — see FBV2-COMM-002)*, keying and shroud from the enclosure. Pin ordering locked with every power contact GND-paired so no row swap can put 5 V on a logic pin. **New 5 V accessory rail** `SYS → TPS61023 → TPS22950C → ACC_5V_SW`, and `+3V3 → TPS22950C → ACC_3V3_SW`; **one load-switch MPN and one boost MPN across both rails**. D-081…D-092 recorded. **P-02, P-15, P-16 and B-08 CLOSED**; B-34…B-38, M-09, M-10 opened. **Zero spare expander capacity now remains anywhere.** |
| 2026-08-23 | FBV2-DISP-002. Overall raised 25% → 28%. **No gate in the twelve-gate table passed**; the task gate **FBV2-DISP-LOCK = PASS**. **Display LOCKED** — EastRising `ER-TFT035IPS-6` + `ER-TPC035-6` (ILI9488 + FT6236 @ 0x38), 56.54 × 84.96 × 3.95 mm, one 50-pin 0.50 mm **bottom-contact** 0.30 mm FPC. **`J1` LOCKED** — Hirose `FH69-50S-0.5SH`, mating proven from both manufacturers' drawings, on the FH12/FH52E land pattern for a JLC second source. **Backlight closed** — TPS61169 retained, `R69` 2.55 R → **1.87 R**, `R70`–`R73` 4 × 39 R → **4 × 33 R**. D-074…D-080 recorded. **M-06 and M-07 CLOSED**; B-28…B-33 opened. ST7796S formally rejected on availability (D-078). |
| 2026-08-22 | FBV2-PWR-002. Overall raised 15% → 20%. **FBV2-A1 = PASS** — first gate since A0. D-065…D-068 recorded. Pass path changed to **P2** (4 FETs, 2 packages). Dead-cell recovery specified to component level. **P-11, P-12, B-20, B-21, B-23 closed**; B-26/B-27 opened. Clamp **demoted to secondary**, fuse **resized 3 A → ≈5 A**. Next gate: **FBV2-A2**. |
