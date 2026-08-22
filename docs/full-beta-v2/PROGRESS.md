# AQROOT Full Beta v2 Progress

**Status: LIVING DASHBOARD.**

Date: 2026-08-22
Repository HEAD at last update: `b8b5ebdd1559083b328782f4fbbfdcce849b46d0`

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

### Overall Full Beta v2: **~8%**

Conservative initial estimate. Two of twelve gates have passed, and both are
paper gates — no design file exists yet. The estimate is deliberately low
because the largest remaining unknowns (mechanical cavity, connector
architecture, NFC scope) are all still upstream of any drawing.

---

## Gate table

| gate | description | status | date |
|---|---|---|---|
| **FBV2-A0** | Pre-design audit | **PASS** | 2026-08-22 |
| **FBV2-A1** | CTO architecture decisions | **IN PROGRESS** | — |
| **FBV2-A2** | Mechanical interface freeze | **NOT STARTED** | — |
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
| **B-07** | **NFC rail architecture.** Main VDD sits on the boosted rail while VDD_IO sits at 3.3 V — a partial-power condition when the boost is off. | U9 pads 8/10 on `NFC_5V_PA_PENDING`, pad 1 on `+3V3` |
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

## Change log for this file

| date | change |
|---|---|
| 2026-08-22 | Created. FBV2-A0 recorded as PASS. Initial blocker set B-01 through B-16 imported from the pre-design audit. |
