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

### Overall Full Beta v2: **~10%**

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
| **FBV2-A1** | CTO architecture decisions | **IN PROGRESS** — rulings A–K recorded; P-01, P-02, P-04, P-07, P-10 still open | — |
| **FBV2-A2** | Mechanical interface freeze | **NOT STARTED — RECOMMENDED NEXT GATE** | — |
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
