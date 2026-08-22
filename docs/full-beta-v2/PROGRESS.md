# AQROOT Full Beta v2 Progress

**Status: LIVING DASHBOARD.**

Date: 2026-08-22 (updated after FBV2-ARCH-001)
Repository HEAD at last update: `890db0b` (pushed to `origin/master`)

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
| Schematic migration | **0%** |
| PCB placement | **0%** |
| PCB routing | **0%** |
| DFM / release | **0%** |
| Physical validation | **0%** |

### Overall Full Beta v2: **~20%**

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
| **FBV2-A2** | Mechanical interface freeze | **NOT STARTED — NEXT GATE** | — |
| **FBV2-S1** | Schematic migration / rearchitecture | **NOT STARTED** | — |
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
| FBV2-A2 | Internal cavity X/Y/Z, wall thickness and PCB-to-wall clearance are published; `tools/check_mechanical_consistency.py` reports a real fit verdict rather than UNKNOWN. |
| FBV2-S1 | `hardware/beta-v2/` exists, forked from Beta-DM with a byte-equivalence proof, and every schematic change in the migration order is landed. |
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
| 2026-08-22 | Created. FBV2-A0 recorded as PASS. Initial blocker set B-01 through B-16 imported from the pre-design audit. |
| 2026-08-22 | FBV2-ARCH-001. Overall raised 8% → 10%; **no gate passed.** B-07 retired as incorrect. B-17/B-18/B-19 added. FBV2-A2 marked as the recommended next gate. |
| 2026-08-22 | FBV2-ARCH-002. Overall raised 10% → 13%; **no gate passed. FBV2-A1 assessed CANNOT PASS** (4 of 8 criteria). B-18 closed, B-25 closed. B-20…B-24 added. P-11…P-18 opened. Standing **NO-RESPIN RECOVERY POLICY** (D-049) established. |
| 2026-08-22 | FBV2-PWR-001. Overall raised 13% → 15%; **no gate passed. FBV2-A1 FAIL, 5 of 6 criteria closed.** D-061…D-064 recorded. **P-13 and B-24 closed** by primary-source evidence; B-22 closed. Complete battery-protection topology specified. Fuse **REQUIRED**, clamp **REQUIRED**, PTC **REJECTED**. |
| 2026-08-22 | FBV2-PWR-002. Overall raised 15% → 20%. **FBV2-A1 = PASS** — first gate since A0. D-065…D-068 recorded. Pass path changed to **P2** (4 FETs, 2 packages). Dead-cell recovery specified to component level. **P-11, P-12, B-20, B-21, B-23 closed**; B-26/B-27 opened. Clamp **demoted to secondary**, fuse **resized 3 A → ≈5 A**. Next gate: **FBV2-A2**. |
