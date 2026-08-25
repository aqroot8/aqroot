# AQROOT Full Beta v2 — FBV2-P2 power routing

**Status: IN PROGRESS. FBV2-P2-001 = FAIL.** Created 2026-08-24 at **FBV2-P2-001**.
Pre-routing checkpoint: tag **`beta-v2-p2-entry-pass`** → `faa0c91`.

> **UPDATED 2026-08-24 at FBV2-P2-002A.** The battery / protection block was attempted with a
> proper obstacle-aware router and **still is not routed**: 2 of 29 nets came out DRC-clean and
> the other 27 were reverted automatically rather than committed. **D-245 is now ruled and
> implemented**: `BAT_PROTECTED_P` gets a scoped 1.50 mm target / 1.20 mm floor, and the
> `BAT_MAIN` class is unchanged. Three named router defects and two no-path connections are
> carried in
> [`../audits/2026-08-24-p2-battery-protection-routing.md`](../audits/2026-08-24-p2-battery-protection-routing.md).
>
> **The power tree is NOT routed.** The foundation was built and validated; the routing itself was
> attempted, did not reach a DRC-clean state, and **was reverted rather than committed.** The board
> at this commit carries **zero tracks and zero signal vias** — what it gained is the **In1.Cu GND
> reference plane** and a corrective placement pass that the routing turned out to depend on.
> The honest account is in
> [`../audits/2026-08-24-p2-power-routing.md`](../audits/2026-08-24-p2-power-routing.md).

> **UPDATED 2026-08-24 at FBV2-P2-002B.** The router itself was put on trial before it was
> allowed near the battery block again, and it **passed**. All three named defects are fixed and
> proved fixed on real Full Beta v2 geometry: six of eight qualification cases route with **zero**
> new DRC violations of any class, one connected copper component after a real save and reload, no
> foreign pad in the cluster, and the ratsnest falling by exactly one edge per connection. A fourth
> defect — a missing **grid guard band**, which let a proved-clear grid path become a 0.172 mm gap
> on a 0.200 mm rule — was found and fixed during qualification.
>
> **The two cases that did not route are not router faults. They are a proved rule conflict.**
> `U18.8`, `U18.9`, `U14.2`, `U14.3` and `U11.2` cannot legally accept the widths their rules
> demand: their widest legal escapes are **0.195 mm to 0.295 mm** against floors of 0.60 mm and
> 1.20 mm. **As written, D-245 makes `BAT_PROTECTED_P` unroutable** — the 1.20 mm floor lands on the
> MAX17048's fuel-gauge sense tap and on a test point, neither of which carries any current. **This
> is surfaced for a ruling, not fixed: no rule was touched.** See **PR-7** below and
> [`../audits/2026-08-24-routing-harness-qualification.md`](../audits/2026-08-24-routing-harness-qualification.md).
>
> **`BAT_PROTECTED_P` at 1.50 mm is feasible for the traverse:** `R75.2 → U18.8 → D9.1 → C25.1`
> routes in **85.274 mm, 22 segments, B.Cu, ZERO vias**, every segment at 1.50 mm except the two
> mandatory 0.245 mm `U18.8` escapes. **`R86.2 → R89.1` and `TP15.1 → U14.2` both have legal
> routes** — 45.274 mm at 1.00 mm and 8.82 mm at 0.20 mm — so **no placement move was proposed and
> none was taken.** **Nothing was committed as copper; the board is byte-identical to `8b9efba`.**

> **UPDATED 2026-08-24 at FBV2-P2-002C.** **D-249 settles the width question: WIDTH IS A PATH
> ROLE, not a property of the net name.** D-245's whole-net floor is superseded — it applied the
> 1.20 mm trunk minimum to the MAX17048 fuel-gauge tap, the LTC4368 `VOUT` sense input and a test
> point, and **as written it made `BAT_PROTECTED_P` unroutable.** The trunk floor now holds on the
> whole net and is relaxed only inside a named rule area bounding one approved branch, in a new
> **section 10b at the very end of `.kicad_dru`** — a position that is load-bearing, because in
> section 5b the pad-escape necking block silently overrode it.
>
> **`U11.2` did NOT need the authorised 0.19 mm exception.** TI's own DLH0010A land is 0.2 mm pads
> on 0.4 mm pitch, so **0.20 mm is the widest copper that can ever leave that pad — the package is
> the bottleneck, not the rule** — and JLCPCB's live capability page gives 0.09/0.09 mm on 1 oz
> multilayer. The measured escape is a **0.20 mm neck 0.575 mm long**, flaring to the 1.50 mm trunk
> over 5.079 mm, with **no via and no thermal relief**.
>
> **FBV2-P2-002C = FAIL and nothing was committed.** Phase A routed **27 connections coexisting
> DRC-clean on scratch** — the whole high-current battery path, both R75 Kelvin branches, the U11.2
> flare, the fuel-gauge and test taps and three of six LTC gate connections, ratsnest 781 → 749 —
> and then stopped at **`LTC_GATE` `Q2.2 → TP17.1`**. §19 forbids touching the authoritative board
> when Phase A fails, so **the board is byte-identical to `a52977e`: zero tracks, zero signal vias.**
>
> **B-34 recomputed from real copper is WORSE than the estimate: ≈ 392 mV / 588 mW at 1.5 A**,
> because the routed copper is ≈ 75.0 mΩ rather than the assumed ≈ 50.6 mΩ. Full account in
> [`../audits/2026-08-24-p2-battery-authoritative-route.md`](../audits/2026-08-24-p2-battery-authoritative-route.md).

---

## 1. What this task delivered

| item | state |
|---|---|
| **Pre-routing tag** | **`beta-v2-p2-entry-pass` created and pushed**, annotated, pointing exactly at `faa0c91` |
| **In1.Cu GND reference plane** | **CREATED AND VALIDATED** — one zone, **one island**, net `GND`, **9938.9 mm² of a 10656 mm² board = 93.3 %** |
| **PM-2 support-network placement** | **CORRECTED** — see §3. This was a prerequisite the routing exposed |
| **Power test-point placement** | **CORRECTED** — 29 test points re-homed beside the nets they probe |
| **Power routing** | **NOT DELIVERED.** Attempted, 505 DRC violations, reverted |
| Tracks / signal vias / outer pours | **0 / 0 / 0** |
| DRC | **1** — the `MK1` artefact accepted at D-227, still not excluded |
| ERC | **0 errors / 27 warnings**, histogram identical |

---

## 2. The In1.Cu ground plane

| property | value |
|---|---|
| Layer | **In1.Cu** |
| Net | **GND**, and In1 carries nothing else — enforced by `.kicad_dru` §2, `severity error` |
| Outline | board rectangle inset **0.5 mm**, the copper-to-edge rule |
| Pad connection | **SOLID (`ZONE_CONNECTION_FULL`)** — no thermal relief, per the fine-pitch GND ruling |
| Local clearance | 0.25 mm · min thickness 0.20 mm |
| Filled area | **9938.9 mm²** |
| **Islands** | **1** — a single continuous reference, which is the whole point |
| Splits / analog islands | **none**, by construction |
| Authorised void | the **ESP32-S3-WROOM-1 antenna keep-out**, cut automatically by the rule area that already exists on all four copper layers. **No polygon was hand-carved and no decorative void was added** |
| F.Cu / B.Cu pours | **deliberately NOT created.** They are the last step of FBV2-P2; making them now would hide return paths rather than prove them |

`p1_regression.py` was taught this: the old *"0 fills"* expectation is retired and replaced by two
checks — **zero tracks / zero vias / zero OUTER pours**, and **In1 must be exactly one GND zone of
exactly one island**. A split reference is now a gate failure rather than an invisible mistake.

---

## 3. The placement correction the routing exposed

FBV2-EXP-002 closed PM-2 **on the chain** — `J4 → F1 → Q2 → Q3 → R75 → U18`, 30.86 mm, Kelvin
6.60 mm — and that part was and remains correct.

**What it did not close is the high-impedance network around that chain.** The trip/gate parts and
the dead-cell reference network had been packed into regions chosen while the chain still sat in
the right column, and were never re-homed when the chain moved to the left margin. Measured on
`faa0c91`:

| net | span at `faa0c91` | after this task's correction |
|---|---|---|
| `LTC_GATE` — a **≈ 20 µA charge-pump node holding four pass FETs enhanced** | **70.4 mm** | **29.8 mm** |
| `BAT_SENSE` | 61.4 mm | **24.3 mm** |
| `REF_POL` | 51.7 mm | **9.7 mm** |
| `REC_GATE_N` | 50.6 mm | **15.6 mm** |
| `LTC_OV` / `LTC_UV` | 28.2 / 15.0 mm | **8.0 / 9.1 mm** |
| `N_POL` | 46.4 mm | **8.3 mm** |

**Routing those as they stood would have knowingly built the defect PM-2 exists to prevent**, so the
support parts were moved to sit beside the chain they belong to — the trip/gate network into
X 7.3 … 13.6 / Y 72 … 100, immediately east of `U18`, `R75`, `Q3` and `Q2`; the dead-cell reference
network into the left column above `J4` and the strip beside it.

**No component value, no threshold, no topology and no net changed, and the 1.5 A chain itself did
not move.** This is escalated as the new item requiring a CTO ruling: **PM-2 was closed on
incomplete evidence at FBV2-EXP-002** — the chain metric was real, but it was reported as if it
closed the whole of PM-2.

29 power **test points** were also re-homed. A test point 50 mm from its own net is not access, it
is a stub — and on a 1.5 A net it is a stub that forces load current somewhere it should not go.
`TP34` (`BAT_CONNECTOR_P`) was 59 mm from `J4`; it is now 4.4 mm away.

---

## 4. Netclass widths this task will use — unchanged, from the ledger

No width or clearance was invented here. From
[`FBV2_P2_NETCLASS_LEDGER.csv`](FBV2_P2_NETCLASS_LEDGER.csv):

| class | target | min | clearance | layers | via policy |
|---|---|---|---|---|---|
| `BAT_MAIN` | **1.00 mm** | 0.60 | 0.30 | F.Cu / B.Cu — **In1 and In2 forbidden** | **≥ 2 POWER vias per transition** |
| `SYS_MAIN` | 0.80 | 0.50 | 0.25 | F/B (In2 only if re-sized at 0.5 oz) | ≥ 2 POWER vias |
| `P3V3` | 0.60 | 0.40 | 0.20 | F/B + In2 trunk | ≥ 2 POWER vias |
| `ACC_3V3` | 0.50 | 0.35 | 0.25 | F/B | ≥ 2 POWER vias |
| `ACC_5V` | 0.60 | 0.40 | 0.25 | F/B | ≥ 2 POWER vias |
| `VBUS_CHG` | 0.50 | 0.35 | 0.25 | F/B | ≥ 2 POWER vias |
| `NFC_5V_PA` | 0.60 | 0.35 | 0.25 | F/B | ≥ 2 POWER vias |
| `SWITCH_NODE` | 0.60 | 0.40 | 0.30 | **outer only, In2 forbidden** | **no via unless proven** |
| `LED_BOOST` | 0.30 | 0.30 | 0.30 | F/B | normal |

---

## 5. B-34 — recomputed on the corrected placement, still an ESTIMATE

The task asks for a recomputation from real copper geometry. **There is no routed copper at this
commit**, so what follows is computed from the **intended** path at the ledger's widths, and is
labelled as such. It is not a measurement and it is not a thermal test.

Intended 1 oz / 35 µm copper, ρ = 17.2 nΩ·m → **0.491 mΩ per square**:

| segment | length | width | squares | R |
|---|---|---|---|---|
| `J4` → `F1` → `Q2` → `Q3` → `R75` (the PM-2 chain) | **30.9 mm** | 1.00 mm | 30.9 | **15.2 mΩ** |
| `R75` → `U11` (`BAT_PROTECTED_P`, the one long run) | **≈ 71 mm** | 1.00 mm | 71 | **34.9 mΩ** |
| 2 × POWER via pairs on that run (4 × ≈ 0.5 mΩ) | — | 0.40 drill | — | ≈ 0.5 mΩ |
| **total routed copper** | ≈ 102 mm | | | **≈ 50.6 mΩ** |
| `F1` 5 A one-shot fuse, cold | — | — | — | ≈ 25 mΩ |
| `Q2` + `Q3` NTMD4820N, two in series | — | — | — | ≈ 2 × 23 mΩ = 46 mΩ |
| **BQ25185 BATFET** | — | — | — | **115 mΩ** (datasheet, the dominant term) |

| current | copper drop | copper loss | **total path drop** | **total path loss** |
|---|---|---|---|---|
| **1.50 A** | 76 mV | 114 mW | **≈ 355 mV** | **≈ 532 mW** |
| **1.75 A** | 89 mV | 155 mW | **≈ 414 mV** | **≈ 724 mW** |

> **B-34 STATUS: OPEN — PHYSICAL VALIDATION REQUIRED.** The figure is close to the ≈ 0.70 W / ≈
> 0.40 V that B-34 originally recorded, and it is **not** clearly unsafe: the dominant 115 mΩ sits
> in `U11`'s WSON-10 with an exposed pad, `U11` is now **out of the battery shadow** with copper on
> both faces and no cell behind it, and the FET and fuse losses are spread over separate packages
> in the left margin. **But it is an estimate from an unrouted board**, so it cannot close B-34 and
> it is not claimed to. **It is also not a stop condition** — nothing here is clearly unsafe, so
> §11's escalate-and-halt did not trigger.
>
> **The one number that would change it is `BAT_PROTECTED_P`.** At 71 mm it is 69 % of the copper
> resistance on its own. Widening it from 1.00 mm to 1.50 mm would take the copper from 50.6 to
> **38.9 mΩ** and the 1.5 A loss from 114 to **88 mW**, at no cost but board area on a face that
> has it. **That is the recommendation for the next routing task**, and it is why the ledger's
> 1.00 mm figure is flagged rather than silently used.

---

## 6. Routed net list

**Empty.** No net carries copper at this commit.

The intended scope, and the boundary that was to be enforced, is unchanged and is recorded here so
the next task inherits it rather than re-deriving it:

**In scope (68 nets):** `BAT_CONNECTOR_P`, `BAT_RAW`, `BAT_MID`, `BAT_SENSE`, `BAT_PROTECTED_P`,
`BQ25185_SYS`, `+3V3`, `ACC_3V3_SW`, `ACC_5V_RAW`, `ACC_5V_SW`, `ACC_5V_LX`, `ACC_5V_FB`,
`NFC_5V_PA_PENDING`, `USB_VBUS_CHG`, `USB_VBUS_RAW`, `LED_BOOST`, `LED_A`, `LED_K`, `BL_SW`,
`Net-(L1-Pad1)`, `Net-(L1-Pad2)`, `Net-(U13-SW)`, `Net-(U13-FB)`, `V3V3_FB`, the LTC4368 network
(`LTC_GATE`, `LTC_GATE_RC`, `LTC_OV`, `LTC_UV`, `LTC_SHDN`, `LTC4368_FAULT_N`, `Q2_CS`, `Q3_CS`),
the dead-cell network (`VBRIDGE_TOP`, `VREF_TOP`, `REF_HO`, `REF_POL`, `N_POL`, `N_BATDIV`,
`VREC_VCC`, `REC_*`), charger programming (`ISET`, `ILIM_VSET`, `Net-(U11-TS_MR)`), the local
enables (`ACC_3V3_EN`, `ACC_5V_BOOST_EN`, `ACC_5V_SW_EN`, `NFC_5V_EN`, `ACC_POWER_FAULT_N`), the
ILIM straps, `VBUS_PRESENT`, the charger STAT pair, `MAX17048_ALRT_N`, `Net-(SW9-A)`,
`Net-(U12-PG)`, `Net-(U12-PS_SYNC)`, and `GND`.

**Out of scope and untouched:** USB D+/D−, SPI-A, SPI-B, the NFC antenna and matching arms, the
I²C trunks, I²S, the community GPIO, ordinary GPIO and every RF control net. **Accidental
out-of-scope routing: zero, trivially, because no net is routed.**

---

## 7. Open items carried to FBV2-P2-002D

**Updated 2026-08-24 at FBV2-P2-002C.**

| # | item |
|---|---|
| **PR-7** | **CLOSED by D-249.** Width is a path role; the trunk floor holds on the net and is relaxed only inside a bounded named area, enforced from section 10b of `.kicad_dru` |
| **PR-8** | **VALIDATED ON SCRATCH, NOT APPLIED.** `TP34` flips to B.Cu in place at (5.000, 39.000), 4.47 mm from `J4.1` and 4.99 mm from `F1.1`, and the `J4.1 → F1.1` trunk picks it up with **zero extra copper**. Phase B did not run, so the authoritative footprint is unchanged |
| **PR-9** | **CLOSED.** `R86`/`R89` are megohm divider tops, so they were reclassified as microamp taps and routed in 18.873 + 8.480 mm at 0.40–0.60 mm rather than a 45 mm 1.00 mm detour |
| **PR-10** | **CLOSED — the 1.50 mm trunk is KEPT**, as ruled. Measured, it contributes 33.58 mΩ over 94.5 mm; at the 1.00 mm class target the same route would be ≈ 46 mΩ |
| **PR-11** | **NEW. The bounded areas must be corridors, not bounding boxes.** Three are tight; the C58 tap's box is **67 × 23 mm at a 0.80 mm floor**, which is a real hole in the trunk rule. A router change, not a rule change |
| **PR-12** | **NEW. Phase A stops at `LTC_GATE` `Q2.2 → TP17.1`.** The rest of the LTC gate net and the **entire dead-cell / recovery network** are unrouted. The congestion is the left margin between `Q2`/`Q3` and the 0603 divider wall at x = 8.0 / 9.65 |
| **PR-13** | **NEW — NEEDS A RULING. `U14.2` / `U14.3` route at 0.15 mm, not the ruled 0.20 mm.** 0.20 mm is impossible there by **5 µm**: a track in the 1.245 mm strip west of `U14` needs its centre at x ≥ 0.500 + w/2 and x ≤ 0.695 − w/2, solvable only for w ≤ 0.195 mm |
| **PR-14** | **NEW — NEEDS A RULING. The `U11.2` sub-1.20 mm escape is 4.738 mm**, against §6's 1.00 mm cap. The 0.20 mm neck itself is 0.575 mm and complies; the nearest **reachable** 1.20 mm-capable point is 2.511 mm from the pad, so ≤ 1.00 mm does not exist |
| **PR-15** | **NEW. `U18.1` (LTC4368 `VIN`) was classified a microamp supply tap at 0.20 mm** on D-249's reasoning. §5 did not enumerate it |
| **PR-16** | **NEW. `C59`, a 1 µF bulk capacitor on `BAT_RAW`, needs 44.4 mm of 0.30 mm copper** to reach its net. At that length it is not a decoupling capacitor in any useful sense. A placement finding |
| **B-34** | **OPEN — physical validation required.** From real copper: ≈ 392 mV / 588 mW at 1.5 A, ≈ 457 mV / 800 mW at 1.75 A, routed copper ≈ 75.0 mΩ |
| **PM-2** | **Placement corrected and approved; closure still pending** — §22 requires a DRC-clean routed block and there is not one |
| **PR-4** | F.Cu / B.Cu ground pours and perimeter stitching remain the **last** step of FBV2-P2 |

---

## 8. Review plots

`pcb/FBV2-P2-battery-front.svg`, `-back.svg`, `-inner1.svg` are exported from the **Phase A scratch
board**, not from the authoritative board — the authoritative board has no copper on it. They show
the `BAT_PROTECTED_P` trunk and its `U11.2` flare, the R75 Kelvin pair, the `BAT_MAIN` chain, the
two F.Cu hops with their four vias, and the fuel-gauge and test branches.
