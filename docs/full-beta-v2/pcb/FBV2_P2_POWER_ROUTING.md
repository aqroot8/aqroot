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

## 7. Open items carried to FBV2-P2-002C

**Updated 2026-08-24 at FBV2-P2-002B.**

| # | item |
|---|---|
| **PR-1** | **CLOSED.** The obstacle-aware harness is qualified: six of eight real-geometry cases route with zero new DRC violations, correct connectivity after save/reload, and no foreign-net contact. Regression-tested by `hardware/beta-v2/checks/router_regression.py` |
| **PR-5** | **CLOSED as a router-implementation matter.** `track_dangling`, `track_width` and `shorting_items` all fixed and proved fixed; a fourth defect (grid guard band) found and fixed during qualification |
| **PR-6** | **CLOSED.** `R86.2 → R89.1` routes legally at 1.00 mm (45.274 mm, 0.025 mm local grid) and at 0.60 mm (16.848 mm); `TP15.1 → U14.2` routes legally at 0.20 mm (8.82 mm). **No placement move needed, none proposed, none taken** |
| **PR-7** | **NEEDS A CTO RULING.** `BAT_MAIN`'s 0.60 mm floor and D-245's 1.20 mm floor are **whole-net** constraints on nets that also carry zero-current sense and probe taps, and **five pads cannot legally accept them**: `U18.9` 0.245 mm vs 0.600, `U18.8` 0.245 mm vs 1.200, `U14.2`/`U14.3` 0.295 mm vs 1.200, `U11.2` 0.195 mm vs 1.200. **As written, D-245 makes `BAT_PROTECTED_P` unroutable.** No rule was touched |
| **PR-8** | **`TP34.1` is an `F.Cu`-only pad on the otherwise-`B.Cu` net `BAT_CONNECTOR_P`.** Needs a via and an `F.Cu` stub, or the test point flipped to `B.Cu`. The only face-split net in the block |
| **PR-9** | `R86.2 → R89.1` is **45.3 mm at 1.00 mm against 16.8 mm at the 0.60 mm floor** — shorter *and* lower-resistance at the narrower width (≈ 13.8 mΩ vs ≈ 22.2 mΩ). A routing decision for the next task |
| **PR-10** | **D-245 delivers about half what its arithmetic predicted.** The measured 1.50 mm traverse is **85.3 mm**, not the 71 mm placement span, and the mandatory `U18.8` neck adds **≈ 7.8 mΩ in 3.9 mm of copper**. `BAT_PROTECTED_P` as actually routable is **≈ 35.7 mΩ**, so the net gains ≈ 6 mΩ rather than ≈ 11.7 mΩ. Feeds the PR-7 ruling |
| **PR-2** | `BAT_PROTECTED_P` at 1.50 mm — **traverse feasibility demonstrated** (85.274 mm, B.Cu, zero vias); terminations blocked pending PR-7 |
| **PR-3** | **PM-2 was closed on incomplete evidence at FBV2-EXP-002.** Corrected at FBV2-P2-001; recorded so the pattern is not repeated. Status remains **placement corrected, closure pending DRC-clean routing** |
| **B-34** | **OPEN — physical validation required.** ≈ 355 mV / 532 mW at 1.5 A, ≈ 414 mV / 724 mW at 1.75 A, BATFET-dominated |
| **PR-4** | F.Cu / B.Cu ground pours and perimeter stitching remain the **last** step of FBV2-P2, after signals |
