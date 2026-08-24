# FBV2-P2-000 — Full Beta v2 pre-routing entry audit

**Date:** 2026-08-24 · **Task:** FBV2-P2-000 — pre-routing entry gate and routing strategy freeze
**Repository HEAD at start:** `853139a` (FBV2-P1-002)
**Result: FBV2-P2 ENTRY GATE = FAIL, on one criterion of thirteen.**
**No percentage is earned. Overall Full Beta v2 stays at 74 %.**

> **ZERO ROUTING WAS PERFORMED.** No track, no signal via, no electrical copper pour was created.
> 499 unrouted connections, unchanged. The only PCB edit is one board-level rule area.

---

## 1. Preflight

| check | result |
|---|---|
| `git status` | clean except the two long-standing untracked paths |
| Local `master` | `853139a` |
| `origin/master` | `853139a` — **in sync, no local-only commits** |
| Staged / uncommitted tracked work | **none** |
| Expected untracked | `hardware/beta-dm/fab/AQROOT-Beta-DM-Gerbers-aa64c16.zip`, `hardware/beta/mechanical/` — **left untouched** |
| PCB | 70.000 × 148.000 mm, 323 footprints (321 schematic + 2 bosses), **0 tracks, 0 vias, 0 non-rule-area zones** |
| Schematic ERC | **0 errors / 27 warnings** |
| PCB DRC | **47 violations**, 499 unconnected |

Nothing was discarded. Nothing was recovered.

---

## 2. The retention ruling — CLOSED

The open escalation from FBV2-P1-002 (D-226) is closed as directed. **Two currently legal M2
through-board screws are ACCEPTABLE and the architecture is LOCKED.** Recorded as **D-232**.

No major component moved to obtain a third screw. The battery was not reduced, the display was
not moved, the SMA was not relocated. Retention is completed by four elements, three of which
are enclosure features and need no PCB holes:

| element | requirement met |
|---|---|
| **A. Moulded edge-capture rails** | constrain lateral PCB movement. Continuous on the **right** and **bottom** edges; **segmented on the left** to clear the 433 flex (Y 1.5 … 48.5) and the coax channel's western excursion (Y ≈ 112 … 137) |
| **B. Four rear non-metallic support ribs** | `RIB_R1` · `RIB_R2` · `RIB_R3` · `RIB_B1`, all verified component-free including through-hole leads. `RIB_R2` (Y 45 … 64) is directly behind the A/B control area; `RIB_B1` and `RIB_R1` bracket the D-pad region. **All four are outside `BATTERY_SHADOW`, so no support compresses the LiPo.** All four are non-metallic and all four are far outside the Ø58 NFC metal exclusion |
| **C. The two M2 screws** | `BOSS1` doc (40.000, 12.000), `BOSS2` doc (59.000, 145.000), Ø4.5 keep-out, Ø2.2 NPTH |
| **D. `J5` backing / load-path structure** | the `COMM_RECESS` backing boss carries the ≈ 33 N average insertion load (peak higher) **into the enclosure, not into the PCB solder joints** (D-097, M-10) |

**USB and microSD insertion loads do not depend only on the M2 screws.** `J3` and `J2` both sit
on the bottom edge, which carries a **continuous** edge-capture rail; `BOSS1` at (40.0, 12.0) sits
between them, 12 mm above that edge. The rail takes the insertion reaction along its whole length
and the screw is a secondary path, not the primary one.

A third M2 may be added later **only** if enclosure CAD produces a legal location without
sacrificing existing geometry. The four routes to one that D-226 listed — narrower battery,
narrower display, SMA off the top-left, or ~1.4 mm of board to the edge — are **all declined**.

**Stale mechanical-spec entries corrected in the same pass:** §4.2 still read *"Count: 6 × M2"*,
and the machine-readable block still read `FBV2_BOSSES: 3 x M2 ... PARTIAL (D-216, target 6)` and
`FBV2_915_PIGTAIL: 095-902-568-100 (100 mm) LOCKED (D-218) - DOES NOT REACH`. All three were
superseded by decisions already taken (D-226, D-223) and are now correct.

---

## 3. P2-O5 — and it was bigger than recorded

`FBV2_P1_FLOORPLAN.md` §16 recorded P2-O5 as *"`.kicad_dru` still references E5/E6 rule areas that
the P1 rebuild deleted."* **Measured, the true extent is:**

| | count |
|---|---|
| Rule areas referenced by `.kicad_dru` | **39** |
| Of those, present in the board | **0** |
| Rule areas actually in the board | **3** (`MIC_ACOUSTIC_KEEPOUT`, `BOSS1_KEEPOUT`, `BOSS2_KEEPOUT`) + one **unnamed** zone embedded in `U1` |
| Rules that could therefore never fire | **22 of 71** |

It was **not only** the E5/E6 pockets. It was **every** RF-band rule, **every** E5/E4 corridor
rule, the header reservation, the E2 button escapes **and the ESP32 antenna rule**.

**Why nothing caught it:** KiCad's `intersectsArea()` and `enclosedByArea()` return **false** for
an unknown area name. They do not warn and they do not error. A rule whose condition can never be
true produces no violations, which is indistinguishable from a rule that is being satisfied.

**The ESP32 antenna was never actually unprotected** — the `U1` footprint carries its own embedded
rule area with tracks, vias, pads, pours and footprints all `not_allowed` on all four copper
layers, and that has always been live. But the rule file *claimed* the protection came from a
named area that did not exist, and nothing in the toolchain could tell the difference.

### 3.1 Disposition, rule by rule

Every one of the 71 inherited rules was read, its selector resolved against the current board, and
its intent judged separately from its object. Full reasoning is in the `.kicad_dru` header's
**retirement register**; the summary:

| id | rules | disposition | reason |
|---|---|---|---|
| **R1** | 5 | **RETIRED** | 915/433 band premise gone. **Neither sub-GHz radiator is on or over the v2 PCB** — 915 is an external whip on an SMA fed by shielded RG-178 (D-223); 433 is a flex bonded to the **left cavity wall**, standing perpendicular to the board |
| **R2** | 8 | **RETIRED** | E5/E4 corridors existed only to cross the Beta-DM 915 band. No band splits the v2 board |
| **R3** | in R1 | **RETIRED** | no v2 button sits in any RF band |
| **R4** | 17 | **RETIRED** | E6 pockets were measured against a **landed Beta-DM route on a 74 × 155 board**. v2 is 70 × 148, placed differently, and unrouted. Re-creating them at Beta-DM coordinates would be fabricating evidence |
| **R5** | 1 | **RETIRED** | `HEADER RESERVED` / `J5_SELF_FANOUT`: v2's `J5` is a right-edge connector with both ends open, not a bottom-edge field in an 8.5 mm strip |
| **R6** | class | **RETIRED** | `E5_CROSSING`, 18 patterns. Carried Default values, so **no net's parameters changed** |
| **R7** | 1 | **RETIRED** | `RF_DO_NOT_ROUTE` matched **zero** nets. `U7.21` / `U8.21` are **netless** — a stronger guarantee than the rule was |
| **R8** | 1 | **RETIRED and REPLACED** | `RF_DEFERRED_NFC` was **actively misleading**: the NFC front end was fully designed at FBV2-S1-004B/004C and **must be routed** |
| **R9** | 1 | **RETIRED** | `USB_VBUS_RAW` escape-via geometry: net exists, justification does not |
| **R10** | 1 | **RETIRED** | `FP-D6` — v2 has `D2 D3 D4 D5`, not `D3`–`D6` |
| — | **49 kept** | | every one re-verified against the current board |
| — | **+19 new** | | ESP32 area rule made resolvable; layer-confinement rules; switch-node victim separations; NFC front-end rule set; four re-measured land patterns |

**Result: 71 → 64 rules, all live.**

### 3.2 The residual R1 leaves behind — NOT papered over

The retired 433 band protected the board **from** an antenna over it. v2 has the opposite problem,
smaller and newly identified: `ANT433_REGION` sits **0.2 mm outboard of the left board edge** over
47 mm of it, so board copper in doc X 0 … 3.0, Y 1.5 … 48.5 is a potential **aggressor into** the
flex. Recorded as **P2-R1**, a routing-stage item. It is **deliberately not instantiated as a rule
area yet** because `L3`, `Q5` and `D9` occupy that band today and **PM-1 changes exactly which
parts are there.** A rule that contradicts placement on the day it is written is worse than no rule.

The detuning question is separate, belongs to the enclosure, and the programme has already
accepted the hidden-flex range compromise.

---

## 4. Complete design-rule audit — what the sweep found

Every item the task listed was checked. Findings, not reassurance:

| area | finding |
|---|---|
| Board clearance | 0.20 mm global, unchanged and correct |
| Track widths | see the netclass defects below |
| Via sizes | 0.30/0.60 general, 0.40/0.80 power, 0.25/0.55 thermal — all above the JLCPCB 0.15 mm floor. Unchanged |
| Differential-pair rules | one pair on the board (USB). Geometry retained, **impedance basis marked STACKUP-TO-CONFIRM** |
| USB rules | complete. Newly added: **In2 forbidden outright** |
| I2C rules | **no width or clearance constraint is appropriate**; the real constraint is a **capacitance budget** (§6). A netclass was created so switch-node separation could be encoded |
| SPI rules | none needed. Both buses are shorter in v2 than in the Beta-DM versions that were accepted |
| Power-net rules | **three patterns matched nothing.** See below |
| LED / backlight rules | retained. 0.30 mm clearance justified by the **39 V** open-LED fault, not the 4.5 V operating case |
| Antenna / RF exclusions | rebuilt. ESP32 keepout now nameable; sub-GHz bands retired with the residual recorded |
| NFC exclusions | the Ø48/Ø58 regions are **mechanical, not copper keepouts, and never were** — the spec forbids screws, bosses, cans, battery, speaker and cable, not PCB copper |
| Battery shadow | mechanical, User.2. **One thermal consequence found — PT-1** |
| Display shadow | mechanical, User.1. No routing impact |
| ESP32 antenna keepout | **it is a 6.5 × 44 mm void in In1 on the right edge**, in the same corner as `U1`, `U11`, `U18`, `R75`, `D10`. Every return path there must be planned around a plane edge |
| Community-port nets | 23 nets, all Default, correct. Escape feasibility confirmed with large margin |
| High-current accessory rails | **`ACC_5V_SW`/`ACC_5V_RAW` were on the 0.20 mm Default class.** New `ACC_5V` class created |

### 4.1 Netclass defects — the serious ones

| pattern | matched | consequence |
|---|---|---|
| `/BAT_PROTECTED_P` | **nothing** | the v2 net is `/01_POWER_TREE/BAT_PROTECTED_P`. **The highest-current net on the board — 1.5 A sustained — was on the 0.20 mm Default class.** The inherited pattern was a root-sheet path; every v2 power net lives under `/01_POWER_TREE/` |
| — | — | **`BAT_RAW`, `BAT_MID` and `BAT_SENSE` were in no class at all**, and all three carry the full pack current |
| `/NFC_5V_PA_PENDING` | **nothing** | same root-path defect. **The `NFC_5V_PA` netclass captured no net whatsoever** |
| — | — | **`ACC_5V_LX` — the `U21` boost switch node — had never been in `SWITCH_NODE`.** It was a 1.2 MHz switching node on the ordinary signal class |
| `*BTN_HOME_N` | **nothing** | no such net in v2 |
| — | — | `NFC_SUPPLY` (`U9` VDD/VDD_TX) was on Default |

**14 classes → 18; 62 patterns → 57. Every surviving pattern now matches at least one board net.**
`ACC_3V3_SW` was split out of `P3V3` into its own class so the ledger states the rail's real
current (400 mA published / 0.76 A ILIM) instead of inheriting the 1.0 A `+3V3` figure.
`E5_CROSSING`, `E2_BUTTON_ESCAPE`, `RF_DO_NOT_ROUTE` and `RF_DEFERRED_NFC` were retired; all four
carried Default values or matched nothing, so **no net's electrical parameters were weakened**.

### 4.2 The durable fix

`hardware/beta-v2/checks/dru_probe.py` is new and is now part of the validation set. It asserts
that every `intersectsArea` / `enclosedByArea` / `memberOfFootprint` / `intersectsCourtyard` /
`hasNetclass` / `NetName ==` reference resolves against the current board and project, that no
rule name is duplicated, and that **no netclass pattern matches zero nets**. Comment lines are
stripped first, so a name that appears only in a retirement note is not treated as a live
reference.

**P2-O5 cannot recur silently.**

---

## 5. The three placement moves — the reason this gate fails

The task is explicit: *"If a placement change is required for electrically correct routing:
surface it NOW. Do not route around a bad power placement."* Three do.

All three are **new findings**, all three are **measured from the board**, and **none of them
existed in Beta-DM to be carried forward** — the battery-protection block and the NFC front end
are both new in Full Beta v2 (the Beta-DM board has no `BAT_RAW`, no `LTC_GATE`, no `BAT_SENSE`
at all; that is blocker B-01). FBV2-P1 placed them into free rear pockets and verified every
mechanical relationship by script. **Nobody had yet looked at them electrically.** That is
exactly what an entry gate is for.

### PM-1 — every switching converter has its inductor off the IC

| converter | IC (doc) | inductor (doc) | switch-node span | requirement |
|---|---|---|---|---|
| `U12` TPS63020 +3V3 | (12.000, 96.000) | `L1` (2.994, 89.010) | **12.96 / 12.54 mm** | ≤ 5 mm |
| `U13` TPS61023 NFC 5 V | (18.000, 124.000) | `L2` (3.254, 99.261) | **28.56 mm** | ≤ 5 mm |
| `U21` TPS61023 acc 5 V | (10.000, 124.000) | `L4` (3.442, 94.111) | **30.50 mm** | ≤ 5 mm |
| `U17` TPS61169 backlight | (48.000, 34.000) | `L3` (3.702, 37.004) | **45.90 mm** | ≤ 5 mm |

`BL_SW` runs `U17.1` (47.2, 33.3) → `L3.2` (4.9, 37.0), and the **catch diode `D8` sits at
(50.6, 36.5) — beside the IC, 45.7 mm from the inductor.** The boost energy loop `L3 → D8 → C44`
is therefore ≈ **76 mm around**, switching at 1.2 MHz between 0 V and **up to 39 V** on the
open-LED fault TI specifies (SNVSA40B, V_OVP_SW 36/37.5/39 V). It runs the length of the left
margin, **13 mm from `MK1`**, through the band the 433 flex sits against.

**All four inductors were placed in the left-margin column at x ≈ 3 while their ICs went
elsewhere.** Systemic, not four coincidences. **Loop area is a placement property; no routing
repairs it.**

### PM-2 — the single-fault battery-protection block is dispersed over 96 mm

| what | measured |
|---|---|
| `J4` → `F1` | 9.0 mm ✔ |
| `F1` → `Q2` → `Q3` | 18.3 + 6.2 mm ✔ |
| **`Q3` → `R75`** | **79.0 mm** ✘ |
| `R75` → `U11` | 4.2 mm ✔ |
| **total 1.5 A path** | **≈ 116.7 mm** |

**What is right and stays right:** the Kelvin sense is sound. `U18.9` (SENSE) and `U18.8` (OUT)
both land on `R75`'s pads and `U18` is 4.2 mm away, so the 47 mV measurement across the 15 mΩ
shunt at the 3.125 A trip is **not** corrupted. That is the single most safety-critical
measurement in the block.

**What is wrong** — high-impedance nodes strung the length of the board past four switching
converters:

| net | span | what it is |
|---|---|---|
| `LTC_GATE` | **95.6 mm** | LTC4368 charge-pump gate, ~20 µA source, four FETs. Its RC (`R76` 22 k + `C57` 4.7 nF) is **31–45 mm from the FETs, 60–75 mm from `U18`** |
| `BAT_SENSE` | **96.5 mm** | FET source **and** the 1.5 A conductor. 79 mm at 1.0 mm/1 oz = 38.8 mΩ → **58 mV, 87 mW at 1.5 A** |
| `LTC_OV` / `LTC_UV` | 78.4 / 81.7 mm | 3.65 M and 510 k dividers — **the battery over/undervoltage trip points** |
| `VBRIDGE_TOP` | **90.1 mm** | `D10` (60.2, 32.0) → `R85` 2.2 M (11.6, 108.0) |
| `VREF_TOP` | 80.8 mm | `D11` (51.8, 32.3) → `R87` 2.2 M (19.2, 106.3) |
| `REF_HO` | 82.4 mm | `R91` 3.65 M (55.0, 44.0) ↔ `R92` 1.30 M (16.6, 84.3): **the two halves of one divider are 38 mm apart**, and `U19` is 52 mm from the top resistor |
| `LTC_SHDN` / `LTC4368_FAULT_N` | 72.0 / 85.4 mm | 1 M nodes |

**The block sits in three clusters** — `U18`/`R75`/`U11` bottom-right (y 30–45), `Q2`/`Q3`
top-right (y 108–115), `U19` + `Q4`–`Q9` + the divider network far-left (x 2–25, y 64–110) —
with multi-megohm comparator nodes and a micro-amp gate node between them. This is the network
that decides whether the pack is disconnected on a fault (D-050…D-054) and whether a deeply
discharged cell gets recovery current (D-049, D-105). **Routing cannot make a 3.65 MΩ node that
crosses four switching converters immune to coupled charge.**

**It also feeds an open blocker.** B-34 records ≈ 0.70 W and ≈ 0.40 V in the BATFET + protection
path at 1.75 A in a sealed enclosure. The dispersal adds **≈ 0.13 W at 1.5 A / 0.18 W at 1.75 A**
on top. **D-049 and the single-fault architecture are not compromised by this finding and are not
proposed for change** — the recommendation moves parts, not topology.

### PM-3 — the NFC differential front end is not symmetric

| item | arm A | arm B |
|---|---|---|
| matching node span | `NFC_MATCH_A` **24.18 mm** | `NFC_MATCH_B` **34.21 mm** |
| EMC inductor | `L5` (31.799, 102.570) | `L6` (28.494, 122.088) — **19.8 mm apart, opposite sides of `U9`** |
| Q resistor | `R114` (47.351, 100.806) | `R115` (57.097, 103.784) |
| antenna node | 8.82 mm | 12.49 mm |
| EMC filter caps | spread over 13.6 mm | spread over 17.2 mm |
| crystal | `Y1` 6.5 mm from `U9` | **`C79`/`C80` are 13–15 mm from `Y1`, on the far side of the IC** — a ~30 mm oscillator loop |
| VDD decoupling | 5.8–9.0 mm from the pins | an RF front end wants < 2 mm |

`R_q` is 1.1 Ω per arm and network Q ≈ 21 (D-204), and the antenna is bench-tuned at first article
by standing order. **A 10 mm arm-length asymmetry is not something routing can absorb.**

### PT-1 — thermal, ranked below the three

`U11` BQ25185 sits at doc (56.000, 32.000) on B.Cu, **inside `BATTERY_SHADOW`**, ~10 mm in from
the pouch's south and east edges. It dissipates ≈ **0.65 W while charging** (5 V → 3.7 V at
500 mA) pressed against the cell it is charging, in a sealed unvented enclosure, against a
0–45 °C charge window. *"Do not rely on the battery as a heatsink"* — this is the one place the
board does. Recommendation: move `U11` to the bottom band (Y < 23.5) near `J3`, which is also
where its `VBUS` comes from. **Reliability and cell-life, not correctness — it does not by itself
block routing.**

---

## 6. Subsystem plans — all closed, all recorded in the routing plan

| subsystem | headline |
|---|---|
| **Stackup** | 4-layer JLC04161H-7628 **retained**, layer roles frozen and now **enforced by rule**. One gap: **the board file carries no stackup object at all** — recorded as **P2-O6**, a DFM-release item |
| **Ground** | one solid In1, no split, no analog island. **One authorised void**: the 6.5 × 44 mm ESP32 antenna notch on the right edge. Perimeter stitch ≤ 7 mm (λ/20 at 1 GHz in FR4). No stitching in any antenna, acoustic or boss keepout |
| **USB** | **Full Speed, 12 Mbit/s, ~40 mm per side, all on F.Cu, zero vias, no length matching.** Critical length is 100 mm; intrinsic skew is 2.4 mm = 17 ps against a ~1 ns budget. ESD ordering already correct. Impedance **STACKUP-TO-CONFIRM**, not a blocker |
| **SPI-A** | 3 nodes, **46.4 mm — 63 % shorter than Beta-DM's 126.5 mm.** Daisy-chain trunk, no star, no matching, no damping. `R112` DNP keeps the display off MISO. MX-8 binding |
| **SPI-B** | 4 nodes, **113.1 mm — 21 % shorter than Beta-DM's 144.0 mm.** ≤ 10 MHz. Trunk `U1 → U9 → U7 → U8`, stubs ≤ 10 mm. It is in the ringing regime, as Beta-DM's longer version was and was accepted; the lever if bring-up shows a problem is **source series damping — a schematic change needing CTO approval** |
| **I2C internal** | **HARD BUDGET `C_bus` ≤ 161 pF at 400 kHz** with 2.2 k pull-ups (300 ns / (0.847 × 2200)). ~100.7 mm of copper plus 8 devices is already close. Fallback is 100 kHz (C ≤ 537 pF), which is the bring-up target anyway. **No mux, no repeater** |
| **I2C external** | TCA4307, 1.5 k, 400 kHz max. Order: buffer → 22 R → TVS → `J5` |
| **Audio** | I2S is trivial (3.07 MHz BCLK). **The speaker output is Class-D switching, not analogue** — tight equal pair on F.Cu, In2 forbidden. `MK1`'s `MIC_DIN` escape must be checked first; that pad was trapped on Beta-DM |
| **NFC** | rules written (B.Cu only, **zero vias**, equal widths, 0.50 mm from switch nodes, tuning parts reworkable, symmetric test points). **Execution blocked on PM-3** |
| **IR** | pulse loop already local at 9.28 mm; `C12` 22 µF is the bulk reservoir 18 mm away, giving ~5 mV across the loop at 170 mA — acceptable. No action |
| **Community escape** | **FEASIBLE with large margin.** 6.570 mm inter-row channel × 27.94 mm, 11 gaps at 2 tracks each per layer, three usable layers, both ends open. **10 crossings needed, 22 available on F.Cu alone.** No nudge required |
| **Routing order** | CTO list adopted with **three documented changes**: steps 6 and 7 merged (the crystal *is* the NFC front end), and step 17 split into 17a return vias placed **with** each loop and 17b final pours last |
| **Via policy** | per class, in the plan. Zero vias on USB, NFC arms and the crystal; ≥ 2 POWER vias per layer change on every rail; **stitching intentional, never decorative**; nothing in any antenna keepout |
| **Thermal** | `U11` 0.65 W (PT-1), `U12` 0.37 W, `U13`/`U21` 0.28 W each, `U9` field-on, `Q2`/`Q3` 0.14 W, `U5` 0.08 W, `U17` 0.08 W. Exposed-pad via counts specified. **No thermal path depends on the battery** |

---

## 7. Blocker register sweep — `P2-O*`, `B-*`, `M-*`, `O-*`

| item | classification |
|---|---|
| **P2-O5** `.kicad_dru` stale areas | **P2 ENTRY BLOCKER → CLOSED** (§3). Larger than recorded: 39 areas, 22 rules |
| **P2-O1** NFC geometry cost a mounting position | **CLOSED / STALE.** Absorbed by D-232; it is a statement of fact, not an open item |
| **P2-O2** `J7` serviceability improved | **CLOSED / STALE.** An observation |
| **P2-O3** dead area reduced | **CLOSED / STALE.** An observation |
| **P2-O4** speaker lead 152 mm for a 29.3 mm run | **FIRST-ARTICLE ITEM.** Assembly cost, not electrical. Carried unchanged |
| **P2-O6** no stackup object in the board file | **NEW — DFM / FIRST-ARTICLE ITEM.** Does not block routing (§6 USB row) |
| **P2-R1** 433 flex aggressor band | **NEW — ROUTING-STAGE ITEM.** Instantiate the rule area after PM-1 |
| **PM-1 / PM-2 / PM-3** | **NEW — P2 ENTRY BLOCKERS.** The reason this gate fails |
| **PT-1** `U11` inside the battery shadow | **NEW — ROUTING-STAGE ITEM**, composes with PM-2 and B-34 |
| **B-34** 0.70 W / 0.40 V in the protection path | **ROUTING-STAGE ITEM**, and PM-2 improves it by ≈ 0.13–0.18 W |
| **B-63** microphone acoustic hole and paste pullback | **CLOSED / STALE — the register has it twice.** Closed 2026-08-23 by D-203 and rebuilt by D-227; the later table still lists it OPEN |
| **B-64** *"the PCB still carries `MK1` with the ICS-43434 footprint"* | **CLOSED / STALE.** The P1 rebuild placed the PUI footprint; verified on the board today. **Do not carry it forward** |
| **B-35** `TPS22950C` `FLT` silent on partial overload | **FIRMWARE ITEM.** No routing impact |
| **B-36** `ACC_3V3_SW` must stay live during sleep | **FIRMWARE / POLICY ITEM** |
| **B-38** 5 V boost inductor `I_sat` ≥ 3 A | **FIRST-ARTICLE / BOM ITEM.** `L4` peak is 2.19 A (D-185) |
| **B-39 / B-40 / B-29** Samtec mating cycles, row mapping, footprint | **PROCUREMENT / already verified at S2.** No routing impact |
| **B-61 / B-62** speaker availability, AWG 32 crimp | **FIRST-ARTICLE ITEMS** |
| **B-65** `+3V3` / `SYS` IR source-select link | **FIRST-ARTICLE ITEM.** Building it needs a sheet-01 edit; IR runs from `+3V3` today |
| **B-66** TSAL6100 ±10° beam ergonomics | **FIRST-ARTICLE ITEM** |
| **B-02 / B-04 / B-05 / B-09…B-16 / B-27** | **CLOSED or superseded** by the S1/S2/P1 sequence; none is a routing input |
| **M-08 / M-09 / M-11 / M-12 / M-13 / M-14** | **ENCLOSURE-CAD ITEMS.** M-12's "most constrained region" warning is **discharged** by §13's measured escape margin |
| **M-10** `J5` ≈ 33 N insertion load | **ENCLOSURE-CAD ITEM**, and part of D-232's load path |
| **O-5** IR receiver AGC4 vs Sony SIRC | **FIRST-ARTICLE ITEM, still needs a CTO ruling.** Receive-only, reverting is a `lib_id` change. **No routing impact** |
| **P-18 / P-19** I²C address reservations | **CTO / policy, low.** No routing impact |

**Two stale blockers were found and are not carried forward: B-63 and B-64.**

---

## 8. Opportunity and simplification scan

Answers in `FBV2_P2_ROUTING_PLAN.md` §18. Summary: **no feature was added and no architecture
change is proposed.** The one genuinely new routing constraint the scan produced is item **E** —
five DNP sites (`R112`, `C81`, `C82`, `R123`, `R107`) whose whole value is later rework, which
must not be flooded by a pour, covered on the opposite face, or crowded by a track. That is now a
first-route checklist line.

On item **G**: after this task **57 of 224 nets are classified and 167 sit on Default, and that is
correct.** 167 ordinary GPIO, control, status and single-pad nets have no constraint and must not
be given one.

---

## 9. Validation

| check | before | after |
|---|---|---|
| PCB parses (`pcbnew`) | ✔ | ✔ |
| Schematic parses | ✔ | ✔ |
| **ERC** | 0 errors / 27 warnings | **0 errors / 27 warnings — identical violation-type histogram** |
| **DRC** | **47** violations | **26** — all 21 `clearance` closed by naming the vendor land patterns that cause them |
| DRC residue | — | 24 `silk_over_copper` + 1 `silk_edge_clearance` (**silk is a P2 finishing activity**) + 1 `solder_mask_bridge` (`MK1`, reviewed and accepted at D-227, **not excluded and not suppressed**) |
| Rules referencing missing objects | **39 areas, 22 rules** | **0** (`dru_probe.py`) |
| Netclass patterns matching nothing | **3** | **0** |
| `netclass_probe.py` | PASS | **PASS** |
| `p1_regression.py` | PASS | **PASS**, 0 checks failed |
| `fork_equivalence.py` | PASS | **PASS** — 12 inherited footprints bit-identical |
| Board dimensions | 70.000 × 148.000 | **unchanged** |
| Placement collisions | 0 | **0** |
| Unrouted | 499 | **499** |
| Signal tracks / vias / electrical pours | 0 / 0 / 0 | **0 / 0 / 0** |

---

## 10. What changed on disk

| file | change |
|---|---|
| `hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_dru` | rebuilt: 71 → **64** rules, full retirement register in the header |
| `hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_pro` | 14 → **18** netclasses, 62 → **57** patterns |
| `hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_pcb` | **one board-level rule area added**, `WROOM ANTENNA KEEPOUT`. No component moved. Written in binary; CRLF preserved throughout |
| `hardware/beta-v2/checks/dru_probe.py` | **new** |
| `hardware/beta-v2/checks/p1_regression.py` | one stale label: `RIB_B2` (does not exist) → `RIB_R3` |
| `hardware/beta-v2/reports/FBV2-P2-000-drc.rpt` / `-erc.rpt` | new baselines |
| `docs/full-beta-v2/pcb/FBV2_P2_ROUTING_PLAN.md` | **new** |
| `docs/full-beta-v2/pcb/FBV2_P2_NETCLASS_LEDGER.csv` | **new**, 19 rows |
| `docs/full-beta-v2/pcb/FBV2_P1_METRICS.txt` | regenerated; **one line changed**, which is itself evidence the board geometry is untouched |

**Beta-DM, the frozen Beta tree and `hardware/beta/mechanical/` were not modified.**

---

## 11. A note on why naming the `U1` zone was not the answer

The first attempt to make the ESP32 antenna rule resolvable was to **name the rule area already
embedded in the `U1` footprint**. That works — `pcbnew` reads the name back correctly — but it
edits the board copy of a library footprint, and DRC immediately reported
`lib_footprint_mismatch` on `U1`, a class FBV2-P1-002 had driven to zero.

**It was tested, observed, and reverted.** The board-level duplicate carries the identical
polygon `(63.5, 104) … (84.5, 152)` and identical flags, is visible in the board file, is what
lets other rules name the antenna region, and leaves the library relationship untouched. The
reasoning is recorded in `.kicad_dru` §3 so nobody re-tries the rename.

---

## 12. Gate result

**FBV2-P2 ENTRY GATE: FAIL.** Eleven of thirteen criteria pass. The two that fail are the same
fact stated twice: **an electrically required placement move remains** — three of them, PM-1,
PM-2 and PM-3.

**No percentage is earned; overall Full Beta v2 stays at 74 %.** This task was never eligible for
one: it is an entry gate, and its own instruction is that it earns no progress.

**Routing does not begin until PM-1, PM-2 and PM-3 are ruled on.** Everything else routing needs
is now written, checked, and enforced by a script that fails if it rots.
