# AQROOT Full Beta v2 — FBV2-P2 power routing

**Status: IN PROGRESS. FBV2-P2-001 = FAIL.** Created 2026-08-24 at **FBV2-P2-001**.
Pre-routing checkpoint: tag **`beta-v2-p2-entry-pass`** → `faa0c91`.

> **UPDATED 2026-08-25 at FBV2-P2-002F. FAIL — BUT THE PLACEMENT QUESTION PR-25 ASKED IS ANSWERED,
> AND THE AUTHORITATIVE BOARD IS UNTOUCHED.** Phase A did not complete, so Phase B never ran;
> `aqroot-Beta-v2.kicad_pcb` is byte-identical to `24f6611` — zero tracks, zero signal vias — and
> **the placement ECO is NOT applied to it** (§23: never commit an unproven placement).
>
> FBV2-P2-002E's fifteen open connections were not a router failure: nine returned
> `NO_LEGAL_ESCAPE` at 0 s, before pathfinding was attempted. This task moved the geometry.
>
> **`U18` rotated 90 → 180 and moved (3.000, 72.400) → (8.000, 65.250)**, from a measured search —
> 13 284 poses, 2 490 clearing collision and the §4 Kelvin envelope, 1 331 keeping both Kelvin
> branches ≤ 10 mm with a legal 1.50 mm trunk, 20 fully scored — with the winner re-confirmed by
> **routing all eight pins with the real router** against the real trunk, chain and flare. The
> R76…R83 divider *wall* is gone: each part is now placed **by the `U18` pin it serves**.
>
> | §4 target | 002E | 002F |
> |---|---|---|
> | `U18` signal-pad escapes | **6 of 8** (7 at best) | **8 of 8, and all eight route** |
> | `R75.1 → U18.9` Kelvin | 3.179 mm | **5.254 mm** |
> | `R75.2 → U18.8` Kelvin | **23.799 mm** | **7.708 mm** |
> | Kelvin mismatch ≤ 5 mm | **20.620 mm** | **2.454 mm** |
> | `U18.1` VIN ≤ 10 mm | **32.204 mm** | **1.850 mm** |
> | `U14.2` branch ≤ 15 mm | **31.228 mm** | **6.387 mm**, `U14` did not move |
> | worst megohm dead-cell node | **64.01 mm** | **18.43 mm** |
> | `BAT_PROTECTED_P` trunk | 20.416 mm @ 1.50, 0 vias | **17.625 mm @ 1.50, 0 vias** |
> | connections on one scratch board | 60 | **70** |
> | ratsnest | 781 → 718 (−63) | **781 → 709 (−72)** |
> | in-scope nets fully connected | — | **23 of 29** |
>
> **`Q3_CS` closes with ZERO vias.** §5's authorised layer drop was measured and **not taken**: four
> variants of the same prefix show CS-before-gate closes all twelve at Q3 on B.Cu, that moving Q3
> 1 mm loses **both** CS nets, and that the authorised drop cannot even start because `Q3.3` has no
> B.Cu escape left once the gate has routed. The price is 2.188 mm on one gate link. **`LTC_GATE`,
> which 002E left in two pieces, is one connected component.**
>
> **Why it still fails: §14 allows no partial pass.** Six nets are in two islands and four of them
> are a single stranded pad — `R80.1`, `U19.2`, `U19.3` — plus the `{TP15, U14.2, U14.3}` MAX17048
> island (**PR-34**). `U19.2`/`U19.3` are a U19 placement question of exactly the kind PR-25
> answered for U18.
>
> **Four harness rulings, none board-specific:** PR-30 (tie-break on ways-out), PR-31 (a partner
> must sit on the side its pin faces, or the route wraps the package), PR-32 (re-measure before
> every fine-pitch pin), PR-33 (U19 is a fine-pitch field too). And the lesson under all of them:
> **an escape proof measures a 0.5 mm stub and a connection is a route** — four placements passed
> the §12 gate, simultaneity test included, and then failed Phase A.
>
> **B-34 stays open.** Scratch pack-current copper ≈ 64.9 mΩ, essentially unchanged from 002E — the
> ECO cost the load path nothing. ≈ 97 mV / 146 mW at 1.5 A; ≈ 114 mV / 199 mW at 1.75 A, excluding
> F1, Q2/Q3 R_DS(on), the BQ25185 BATFET, contact resistance and temperature rise.
>
> Full detail: [`audits/2026-08-25-p2-battery-placement-eco.md`](../audits/2026-08-25-p2-battery-placement-eco.md).

> **UPDATED 2026-08-25 at FBV2-P2-002E. STILL NOT ROUTED, BUT THE BLOCK IS CLOSE AND WHAT IS LEFT
> IS PLACEMENT.** Phase A reached **60 connections coexisting on one scratch board with zero new
> DRC violations of any class at every step, ratsnest 781 → 718 (−63)** — the previous best was
> 27 and −32. **Phase A did not complete, so Phase B was not run and the authoritative board is
> byte-identical to `e09eb35`: zero tracks, zero signal vias.**
>
> **What is now measured on real copper:**
>
> | path | routed | width | vias | layer |
> |---|---|---|---|---|
> | `BAT_CONNECTOR_P` `J4.1 → F1.1` | 9.871 mm | 1.00 mm | 0 | B.Cu |
> | `BAT_RAW` load `F1.2 → Q2.8 → Q2.7` | 7.996 mm | 1.00 / 0.80 mm | 0 | B.Cu |
> | `BAT_MID` `Q2.5 → Q2.6 → Q3.8 → Q3.7` | 18.106 mm | 1.00 / 0.80 mm | 0 | B.Cu |
> | `BAT_SENSE` load `Q3.5 → Q3.6 → R75.1` | 17.553 mm | **1.00 mm** | 2 | B.Cu + F.Cu |
> | `BAT_SENSE` Kelvin `R75.1 → U18.9` | 3.179 mm | 0.20 mm | 0 | B.Cu |
> | `BAT_PROTECTED_P` Kelvin `R75.2 → U18.8` | 23.799 mm | 0.20 mm | 0 | B.Cu |
> | `BAT_PROTECTED_P` trunk `R75.2 → D9.1` | 20.416 mm | **1.50 mm (TARGET)** | **0** | B.Cu |
> | `BAT_PROTECTED_P` `U11.2 → D9.1` incl. flare | 73.615 mm | 1.50 mm | **0** | B.Cu |
> | `BAT_RAW` VIN tap `U18.1 → R77.1` | 32.204 mm | 0.20 mm | 0 | B.Cu |
> | `U14.2 → TP15.1` (MAX17048) | 31.228 mm | 0.15 mm | 0 | B.Cu |
> | `C59.1 → F1.2` | 3.407 mm | 0.60 mm | 0 | B.Cu |
> | `C58.1 → D9.1` | 4.557 mm | **1.50 mm** | 0 | B.Cu |
> | `LTC_GATE` `TP17.1` stub | **5.741 mm** | 0.25 mm | 0 | B.Cu |
>
> **`U11.2` escape, re-measured:** 0.20 mm neck **0.575 mm** long (cap 0.75 mm), strictly monotonic
> flare 0.30 → 0.40 → 0.60 → 0.80 → 1.00 → 1.20 → 1.50, **no via, no thermal relief**,
> **4.214 mΩ**, sub-1.20 mm length **4.737 mm against §5's 5.25 mm cap — inside it**.
>
> **R75 Kelvin mismatch 20.620 mm** (3.179 vs 23.799), both from the correct R75 pad, both
> current-free — the direct cost of routing the trunk before the pin field, which is what §8
> requires and what buys the 1.50 mm trunk.
>
> **Trunk-first is load-bearing.** With U18's pin field routed first, a 0.20 mm sense tap landing
> on `R75.2` takes the trunk's only escape from that pad and `R75.2 → D9.1` returns
> `NO_LEGAL_ESCAPE` at 0 s. Copper on this board only accumulates, so no later pass recovers it.
>
> **15 connections remain open and nine failed `NO_LEGAL_ESCAPE` at 0 s** — the pad cannot emit a
> legal track at any width on any layer. `LTC_GATE` finishes in two pieces
> (`{U18.10,R76.1,TP17.1}` ‖ `{Q2.2,Q2.4,Q3.2,Q3.4}`), so **`U18.10 → Q3.4` is the connection to
> beat**. **U18 escapes 6 of its 8 signal pins here, 7 at best across four orderings**, because the
> whole north row shares one ~2.2 mm corridor between the package (x ≤ 4.83) and the
> R76/R77/R78/R79 divider wall (x ≥ 7.00). That is **PR-25** and it needs a placement ruling.
> Full account:
> [`../audits/2026-08-25-p2-battery-authoritative-route.md`](../audits/2026-08-25-p2-battery-authoritative-route.md).

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

---

## 9. Routing-order rules established by FBV2-P2-002G / 002H

These are harness rulings, not board facts, and they apply to every block that
follows — the converters included.

**PR-39 — router success must mean real connectivity.** A route counts only if
the pads that were *requested* end up in one connected component. The router's
node-retarget fallbacks are still allowed, because a retarget is often the right
topology, but one that leaves the named pad isolated is reverted and does not
count. Judge a phase on `checks/net_ledger.py`, never on the routed count.

**PR-40 — qualify on the full prefix.** Bare-board escape, simultaneous stub
escape and reduced-prefix probes have each passed a placement that then failed.
A candidate is qualified by the real driver, in the real order, against the real
copper the plan lays first. Use the cheap models only as *negative* tests: they
can rule a candidate out, never in.

**PR-41 — a WIDE net does not make every pad on it wide.** `BAT_RAW` carries the
pack current at one end and a microamp divider at the other. Net-level width
classes must yield to D-249's per-pad rulings in the closure stage, exactly as
they do in the plan.

**PR-43 — schedule by corridor scarcity, not by net role.** Role tells you how
wide a path must be; it does not tell you how contested its corridor is. A
`TAP` that is the only 21 mm link between two islands through a shared margin
must be scheduled with the trunk, not with the local taps it superficially
resembles. Before ordering a block, ask of each connection: *how many corridors
does this have, and who else wants them?*

The common thread, and the one worth carrying: **an escape proof measures a
0.5 mm stub; a connection is a route.** Every defect in this list was found by
measuring the thing itself rather than a proxy for it.

---

## 10. PR-43, measured — and what it teaches about the west margin

`FBV2-P2-002I` ran PR-43 exactly as §9 above describes it, and the ruling is
**correct but not sufficient**, which is a distinction worth keeping.

**It works.** Scheduling the two long `BAT_RAW` bridges with the chain closes
`BAT_RAW` — 11 of 12 pads in one island, `R80.1` and `D12.1` both connected —
**with no placement change at all**, and it closes `LTC_SHDN` as a side effect.

**It costs `U18` two pins**, 8 of 8 → 6 of 8, and the copper boxing them is not
`BAT_RAW`:

    U18.7    LTC_SHDN        0.500 mm      BAT_PROTECTED_P  0.500 mm
    U18.10   BAT_SENSE       0.500 mm      BAT_SENSE        0.986 mm

The bridges never touched U18's lanes. They unblocked `LTC_SHDN`, and
`LTC_SHDN`'s new route took the lane `U18.7` needed. **The failure is capacity,
not ordering.** Both schedules land on 24 of 29; the loser is simply whoever
goes last.

**The rule this adds, for the converters and every block after:** when
reordering changes *which* net fails but not *how many*, stop reordering. That
signature means the corridor is oversubscribed, and the remaining levers are
placement, a layer change, or dropping a demand — not sequence.

The west margin at x 4…10 must presently carry the 1.50 mm `BAT_PROTECTED_P`
trunk, `BAT_SENSE`, `BAT_MID`, both `BAT_RAW` bridges, `LTC_SHDN` and U18's
north row. That is the list to shorten.

PR-43 is available behind `AQROOT_PR43=1`. The default ordering keeps `U18` at
8 of 8.

---

## 11. The R80/R81 lever, measured — and why the west margin is short of layers

`FBV2-P2-002J` screened six `R80` poses and ran two full Phase A runs on the two
best. The result closes the first lever of D-255.

**Every candidate kept `R80.1` and `D12.1` connected**, so PR-43's result does
not depend on where `R80` sits. **None reached U18 8/8.** K6 alone closed both
D-255 casualties — and cost `Q3_CS`, which §12 protects, plus `LTC_GATE`.

    baseline (PR-43 off)   24/29     U18 8/8, BAT_RAW open
    baseline (PR-43 on)    24/29     U18 6/8
    K6                     20/29     both pins fixed, Q3_CS split
    K1                     22/29     both pins joined, LTC_GATE in 5 islands

**One reordering and seven placements have all landed at or below 24 of 29.**
That is the signature of a corridor short of *layers*, not of lanes: each change
chooses a different loser at constant total.

**The rule for the blocks that follow:** when a class of nets already needs vias
to exist at all — here `LTC_GATE`, `LTC4368_FAULT_N`, `LTC_SHDN` and `LTC_OV`
each carry two — stop conceding them one at a time and give the class a planned
second-layer path. Conceding vias individually redistributes the shortage;
planning the layer removes it.

### PR-44 — rule-area corridors must resolve their tracks fresh

`grow()` stored `PCB_TRACK` objects. A later `qb.revert()` frees that copper, and
the next `apply_areas()` read freed memory — a deterministic SIGSEGV that killed
two full Phase A runs at connection 28. Store UUIDs; resolve against the board.
Any harness holding KiCad object pointers across a revert has this bug.

---

## FBV2-P2-002K — D-256 answered: the layer exists, the via does not fit

The block above closes with a rule: *when a class of nets already needs vias to
exist at all, stop conceding them one at a time and give the class a planned
second-layer path.* D-256 ruled exactly that. FBV2-P2-002K executed it, and the
result is a correction to the rule rather than a confirmation of it.

**The rule is right about the shortage and silent about the price of admission.
A planned second-layer path costs a via, and a via has to land somewhere.**

### What was measured

At the FBV2-P2-002F placement — the one every verdict from 002F to 002J uses:

```
U18.10   escape 0.20 mm, ONE direction
         reachable through-via site at 0.60 / 0.55 / 0.50 / 0.45 /
                                       0.40 / 0.35 / 0.30 / 0.25 mm ... NONE
         reachable site at 0.20 mm ............................ yes, 1.20 mm out
                                     (= min_microvia_diameter, NOT a through via)

U18.7    NO LEGAL ESCAPE at 0.25, 0.20 AND 0.15 mm
         blocked by U18.8 (x25) and U18.6 (x20) - its own adjacent pads
```

`U18` is an **MSOP-10 on 0.50 mm pitch**; the board's own floor is
`min_via_diameter = 0.50 mm`. The pin field cannot hold the smallest through via
the board declares, so on this placement the excursion cannot start.

On the **authoritative** placement both pins do have reachable sites — `U18.10`
from 0.50 mm, `U18.7` from 0.60 mm — and there the planned path does everything
D-256 expected:

    LTC_GATE  U18.10 -> R76.1   8.794 mm F.Cu, 2 vias, 2 s   (was NO_PATH, 26 s)
    LTC_GATE  U18.10 -> Q3.4   15.552 mm F.Cu, 2 vias
    LTC_SHDN  U18.6  -> Q4.3   24.525 mm F.Cu, 2 vias @0.25  (was DRC-rejected)
    LTC4368_FAULT_N            all four functional pads, ONE island, on B.Cu
    LTC_GATE                   ONE ISLAND, all six functional pads
    U18                        6 of 8  ->  7 of 8

So the strategy is sound and the placement decides whether it is reachable. The
ECO adopted to fix U18's escapes is the same ECO that denies these two pins the
layer change.

### The corrected rule

**Before planning a class onto a second layer, prove the via lands.** The
question is not "is there room on the other layer" — over this margin F.Cu is
0.00 mm² occupied — but "can each pad of the class reach a legal via site from
its own escape". Those are different questions and only the second one binds.

Corollaries the harness now enforces:

- A via site must be **reachable from the escape**, not merely nearby (PR-45).
  For `U18.10` the nearest site that *existed* was 2.30 mm away on the far side
  of the copper the pin was escaping past.
- Via-site selection must respect **`min_hole_to_hole`**, a drill-to-drill rule
  no copper-clearance grid can see.
- A rule area that names a corridor must span **both outer layers**, or a ruled
  tap that takes the second layer falls outside its own corridor and is judged
  against its class floor.

### And two conflicts that are not about layers at all

- **PR-47, the Q3 south row.** `Q3_CS` owns pins 1 and 3, `LTC_GATE` owns 2 and
  4, they interleave, and there is one B.Cu slot. Measured in three orderings:
  the loser's middle pad has **no legal escape at any width on either layer**,
  so it cannot reach a via and no excursion can rescue it. This is a
  land-pattern conflict of the same class as U11.2 and U14.2/U14.3.
- **PR-48, D-249 relaxes width and not clearance.** `U18.1`'s ruled 0.20 mm VIN
  tap is rejected by `BAT_MAIN routed clearance` — 0.300 mm required, 0.250 mm
  actual — against PR-43's own bridge copper at `R77.1`. The U14.2/U14.3 gauge
  branches fail the same rule at 0.2347 / 0.2350 mm. A corridor that relaxes
  width for a fine tap must decide what it does about clearance too.

---

## FBV2-P2-002L — the via fits U18 and cannot reach Q3.3

002K's block closes with a corrected rule: *before planning a class onto a
second layer, prove the via lands.* 002L proved it — twice, with opposite
answers, and the difference between the two is the whole result.

### U18: the via lands, on an ordinary through via

D-257 ruled **0.35 / 0.20 preferred**, **0.25 / 0.15 absolute reserve**, and no
microvia. On the authoritative pose that is enough:

    LTC_GATE   4 x 0.35/0.20 ordinary through via
    LTC_SHDN   2 x 0.35/0.20 ordinary through via
    reserve    NEVER TAKEN

Two layer transitions per connection, no more. **The exotic-fabrication option
002K raised is not needed for U18** — which is the outcome section 18's
"prefer standard fabrication" rule is there to find.

Both ruled geometries sit under the board's global `min_via_diameter` 0.50 mm
and `min_via_annular_width` 0.125 mm, so every bounded escape corridor carries
its own `via_diameter` / `annular_width` / `hole_size` override. That was
verified before it was adopted: a 0.35/0.20 via inside a named area reports
`via_diameter` and `annular_width` without the rules, nothing with them, and no
other violation class moves.

### Q3.3: there is nowhere to land

    Q3   SOIC-8_3.9x4.9mm_P1.27mm
         pitch 1.270 mm, pads 1.950 x 0.600 mm, copper gap 0.670 mm
         south row:  1 Q3_CS   2 LTC_GATE   3 Q3_CS   4 LTC_GATE

    Q3.3  NO LEGAL ESCAPE at 0.25, 0.20 AND 0.15 mm
          blocked by Q3.2 (x27), Q3.4 (x20)

    via 0.35/0.20  all widths   NO_LEGAL_ESCAPE
    via 0.25/0.15  all widths   NO_LEGAL_ESCAPE

**A smaller via does not help a pad that cannot emit copper.** The escape comes
first and the via second; when the escape does not exist, via geometry is not
the variable. This is the same shape as `U18.7` at the 002F pose, one package
over, and it is why PR-47 leaves the routing domain entirely.

Geometry-only, a filled and capped **through** via-in-pad at 0.35/0.20 fits
inside a 0.600 mm pad with **0.125 mm of pad copper each side**, leaves the
0.670 mm pad gap untouched, and puts adjacent drills 2.540 mm apart. Feasible,
and premium — hence the decision stop.

### The rule this adds

**Width, clearance and via geometry are three separate rulings and a corridor
needs all three.** D-249 ruled width. PR-48 had to add clearance, because a
0.20 mm microamp tap that passes every width rule is still rejected by a
0.30 mm wide-net spacing rule fired by its own target pad. D-257 had to add via
geometry, because a corridor that permits a narrow track says nothing about
what may be drilled in it. A bounded corridor that states only one of the three
is a corridor that will fail for a reason nobody ruled.

And the corollary, learned the expensive way in this task: **a relaxation
applied where nothing needed relaxing is a restriction.** The first PR-48 rule
list covered two corridors that were already running legally at 0.150 mm; since
a clearance rule states a minimum and the block is written last so it wins, it
raised the floor on compliant copper and rejected every connection after it.
Relax exactly what was measured to need relaxing.

### Kelvin, and where the 002F ECO came from

The authoritative pose routes 8 of 8 and the 002F ECO pose routes 6 of 8 with
perfect Kelvin. It is tempting to read that as a straight trade, and it is not:

    authoritative   straight-line kelvin 2.440 / 8.265   mismatch 5.825
    as routed                            3.179 / 13.152  mismatch 9.973

**4.948 mm of that mismatch is a detour**, not geometry. The pose is 0.825 mm
of placement away from the limit and the rest is a branch being sent the long
way round. The lever is **R75** — held fixed "initially" — and it is one short
branch, not a re-floorplan.

---

## FBV2-P2-002M — six layers buy the Q3 conflict, not the corridor

D-258 moved the board to six layers on the strength of 002L's measurement, and
the measurement was right about what it said and silent about what it did not.

**What six layers bought, exactly:** `Q3.3` — the pad that could not emit legal
copper in any direction at any width, on either layer, at any via size. A
filled/capped 0.35/0.20 **through** via inside its own pad and 4.626 mm on
In2.Cu closes `Q3_CS`, and the B.Cu south-row slot goes back to the gate drive:
`LTC_GATE Q3.2 → Q3.4`, **5.500 mm, zero vias**, against 002L's only available
answer of a 15.991 mm F.Cu excursion. One premium via on one pad, and the
MOSFET gate stops paying for the sense pair's geometry.

**What six layers did not buy:** the corridor. `BAT_SENSE Q3.6 → R75.1` is a
1.00 mm wide-net trunk that needs 0.30 mm to everything, and the POFV escape
needs the same few square millimetres. The trunk cannot move inward — 0.5 oz
inner copper needs 2.73 mm for 1.5 A at a 10 K rise, which is the board's own
arithmetic, and `BAT_MAIN is outer-layer only` already said so. So the two
contend on B.Cu and F.Cu exactly as before, and DRC reports
`clearance 0.3000 mm; actual 0.2400 mm`.

### The rule this adds

**Layers relieve PIN-FIELD conflicts and do nothing for CORRIDOR contention.**
A pin that cannot escape is short of somewhere to go, and another layer is
somewhere to go. A 1.00 mm trunk and a fine escape competing for the same
2 mm² are short of *area on the layers they are allowed to use*, and adding
layers they are not allowed to use changes nothing. Before buying layers for a
congestion problem, ask which of the two it is.

The corollary for scheduling: **a through via's site must be clear on every
layer, so the pad with one option must be routed before the trunk with many.**
Scheduled after the chain, the Q3.3 POFV came back `POFV_LAYER_CONFLICT on F`
— blocked by `BAT_SENSE`'s own F.Cu hop running 0.365 mm from the pad centre.
PR-18's scarcity argument, now in three dimensions.

### And a via is copper on every layer

Three defects in this task were one defect: a router that had only ever seen
two layers. Its obstacle model held two; `connect_hop` sited its vias by
checking two; and it could route to only one of the two new ones. Each was
caught by DRC on real copper — `shorting_items`, twice, from a via dropped onto
another net's inner copper.

**A via that clears the two layers you were thinking about is not a via that
clears the board.**

---

## FBV2-P2-002N — the mismatch was a property of the part, not the position

002M left two blockers. 002N solved both *individually* and neither *together*,
and the reason in each case is worth keeping.

### R75: translation could never have worked

    U18.8 and U18.9 are at the SAME y (70.300), 0.5 mm apart in x
    R75 is a 5.925 mm shunt whose pads lie along y

So for **any** pure north/south move, both Kelvin lengths change by the same
amount and their difference does not move at all. The mismatch is pinned at
very nearly the shunt's own length. Measured over ±8 mm at 0.5 mm in four
rotations: 28 poses reached the Kelvin test, **all of them rot 90/270**, best
mismatch **5.177 mm** against a 5.000 mm limit — close enough to look like a
tuning problem and structurally impossible.

Turning the shunt so its pads lie along x drops the mismatch below 1 mm. Every
rot 0/180 pose is blocked by the R80/R81/R82 courtyards at x 7.30.

**The part costing the Kelvin specification was the divider column, not R75.**
Shift that column 1.0 mm east — the measured minimum — and R75 reaches
**0.771 mm** mismatch with both branches under 8.03 mm.

**And then the column is in the control lanes.** `LTC_SHDN`, `LTC_GATE` and
`FAULT_N` are all rejected at 0.2371–0.2778 mm against `BAT_MAIN routed
clearance 0.3000 mm`, and U18 falls from 8/8 to 6/8.

### The rule this adds

**Before searching a placement, ask what the objective is a function of.** A
mismatch between two distances measured from two points that share a coordinate
is a function of the *part's own geometry*, not of where the part sits. No
amount of translation search will find what translation cannot express. One
line of arithmetic would have saved the whole ±8 mm sweep — and the sweep is
what proved the arithmetic, so it was not wasted, but it should have been the
confirmation and not the discovery.

### LTC_OV: the link you aim at is not the net you fix

R78 moved **0.354 mm** and `R77.2 → R78.1` closed. `LTC_OV` became one
component and U18 held at 8/8. And `U18.3 → R77.2` — the other half of the same
net — took **13.087 mm on F.Cu with two vias**, which is the long generic
fallback this block has been refusing since D-256.

**Fixing the link that failed does not make the net local.** A high-impedance
node has to be judged end to end, and the next lever is R77.

### Two ways a search lies to you

Both surfaced in this task and both are cheap to prevent:

- **A search allowed to overlap the part it is connecting to will always report
  a perfect score.** The first R78 sweep returned `R77.2 → R78.1 = 0.000 mm` —
  not a zero-length link, but R78's pad sitting on R77's, because R77 was in the
  movable set and so absent from the obstacle list.
- **A filter that rejects the status quo is a bug, not a filter.** The
  fine-pitch band heuristic rejected R75's own current pose and returned zero
  candidates; it is the right question for an MSOP pin with a 0.325 mm window
  and the wrong one for a 5.925 mm shunt with 1.5 mm pads.

### And one clearance that must not be tightened

`BAT_MAIN routed clearance` fires on either side of the pair, so raising
wide-net **pads** from 0.200 to 0.300 mm in the router's own margin looks
obviously right. It sealed `U18.8` and `U18.9` — the two D-249-ruled Kelvin
taps — at `NO_LEGAL_ESCAPE`. They route legally at 0.150 mm under the
pad-escape necking block, a later and more specific rule, so DRC does not demand
0.300 mm there at all.

**Over-applying a clearance is how a legal escape becomes NO_LEGAL_ESCAPE.** A
router-side margin cannot see which corridor rule governs a pair; the
per-connection DRC gate can, and it stays the authority.

---

## FBV2-P2-002O — a corridor 6.80 mm wide and a part that needs 7.75

002N's failure was read as "the divider column moved without U18". That reading
was correct: move them together and the three control-lane clearance failures
disappear. It also turned out not to matter, because the rigid cluster cannot
travel far enough, and the reason is a subtraction.

    R75 at rot 0/180 needs        7.75 mm   (2 x 3.875 mm courtyard half-width)
    corridor actually available   6.80 mm   (west edge clearance -> divider column)

    west limit                    R75.x >= 4.075
    east limit, cluster +0.50     R75.x <  3.925     <- empty
    east limit, cluster +0.75     R75.x <  4.175     <- opens, 0.100 mm wide

Cluster +0.75 mm is where **D9 overlaps R77 by 0.170 mm**. Only +0.50 mm is
legal, so the window never opens. TP17 and C58 obstruct only from +1.25 mm, so
the test-point lever — the cheap one, the one §13 exists to find — does not
apply here. **The obstruction is a functional diode in the protected path.**

The other orientation was re-measured rather than assumed: rot 90/270 bottoms
out at **5.132 mm** mismatch against 5.000 (002N: 5.177 unmoved). Routed, that
pose costs four U18 control pins, because moving R75 east far enough to improve
the mismatch puts the shunt under U18's escape corridor.

### The rule this adds

**When two constraints both bind within a tenth of a millimetre, stop searching
placements and go back to the part.** R75's 5.925 mm pad pitch is *both* the
reason rot 90/270 cannot beat 5 mm — the mismatch floors at the shunt's own
length — *and* the reason rot 0/180 needs 7.75 mm of corridor. One dimension is
generating both walls. No amount of translation, rotation or cluster
re-arrangement addresses a dimension; only a different part does.

That is a component decision and it is raised, not taken. But it is worth
noticing that four consecutive placement tasks have been trading one
sub-millimetre casualty for another around a single 5.925 mm object.

### And two ways tooling wasted a screen

- **A pose filter that checks the outline is not checking the board.** R75 at
  x = 3.900 rot 180 puts its west pad 0.325 mm from the edge against a 0.500 mm
  clearance; every connection was rejected from the first, and the screen
  produced nothing. Edge rules belong on the pads.
- **A guard that fires on `270.0` versus `-90.0` is a guard people learn to
  ignore.** Angles compare modulo 360 now. The placement-identity assertion is
  the one piece of tooling that must never cry wolf — it exists because 002K
  ran nine screens on the wrong board.
