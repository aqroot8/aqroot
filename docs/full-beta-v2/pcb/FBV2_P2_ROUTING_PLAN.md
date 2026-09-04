# AQROOT Full Beta v2 — FBV2-P2 routing plan

**Status: NORMATIVE for FBV2-P2.** Created 2026-08-24 at **FBV2-P2-000**, the P2 entry gate.
Authority: [`../CTO_DECISIONS.md`](../CTO_DECISIONS.md),
[`FBV2_P1_FLOORPLAN.md`](FBV2_P1_FLOORPLAN.md), [`FBV2_P1_KEEPOUTS.md`](FBV2_P1_KEEPOUTS.md),
[`FBV2_P2_NETCLASS_LEDGER.csv`](FBV2_P2_NETCLASS_LEDGER.csv).

> **NO SIGNAL ROUTING EXISTS AND NONE WAS PERFORMED.** Zero tracks, zero signal vias, zero
> electrical copper pours. 499 unrouted connections is the correct state. This document is the
> rule set routing will be judged against; it is not routing.

> **ROUTING STATUS 2026-08-24 (FBV2-P2-001): the In1.Cu GND reference plane EXISTS and is
> validated — one zone, one island, net GND, 93.3 % of the board — but the POWER TREE IS NOT
> ROUTED.** The attempt produced 505 DRC violations and was reverted; **the board carries zero
> tracks and zero signal vias.** F.Cu / B.Cu pours remain the LAST step of P2, after signals.
> Everything in this plan stands unchanged; what it needs is an obstacle-aware router. See
> [`FBV2_P2_POWER_ROUTING.md`](FBV2_P2_POWER_ROUTING.md) and
> [`../audits/2026-08-24-p2-power-routing.md`](../audits/2026-08-24-p2-power-routing.md).
> **One correction from that attempt: `BAT_PROTECTED_P` should be routed at 1.50 mm, not the
> ledger's 1.00 mm target — at ≈ 71 mm it is 69 % of the whole protection path's copper
> resistance (PR-2, pending a ruling).**
>
> **GATE RESULT: FBV2-P2 ENTRY = PASS (re-issued 2026-08-24 at FBV2-EXP-002).** PM-1, PM-2,
> PM-3 and PT-1 are all **CLOSED**, so **no electrically required placement move remains**. The
> board is now **72.000 x 148.000 mm**, `J5` is a **1 x 24** socket and `J8` **Qwiic** is new;
> every rule, netclass, layer, ground, via, thermal, bus and escape decision below is unchanged
> and still valid. **Community escape on the new connector: 23 inter-pad gaps x 3 usable layers =
> 69 crossings against the 66 the 2 x 12 offered, the 7.87 mm dead band is gone and both ends of
> the row are open** -- which is why the retired `HEADER RESERVED` / `J5_SELF_FANOUT` rules were
> not re-created. Superseded gate result below.
>
> ~~**GATE RESULT: FBV2-P2 ENTRY = FAIL, ON ONE CRITERION.**~~ Every rule, netclass, layer, ground,
> via, thermal, bus and escape question below is **closed**. What is not closed is §25's
> requirement that *"no electrically required placement move remains"*. **Three remain, all
> newly measured here, none of them fixable by routing: PM-1, PM-2 and PM-3 (§5).** They are
> escalated, not designed around. Routing must not begin until they are ruled on.

All coordinates use the **P1 doc datum**: origin lower-left, X → right, Y → **up**, millimetres.
`Y_kicad = 148.000 − Y_doc`.

---

## 1. What this task changed

| file | change |
|---|---|
| `aqroot-Beta-v2.kicad_dru` | **rebuilt.** 71 inherited rules → **64 v2 rules.** 22 Beta-DM rules retired with a written reason each; 19 new v2 rules written. The file now carries a full **retirement register** in its own header |
| `aqroot-Beta-v2.kicad_pro` | **14 netclasses → 18**; 62 patterns → **57**. Four dead netclasses retired, four new ones added, and **three patterns that matched nothing were repaired** |
| `aqroot-Beta-v2.kicad_pcb` | **one addition:** a board-level rule area named `WROOM ANTENNA KEEPOUT`. No component moved, no track, no via, no pour |
| `checks/dru_probe.py` | **new.** Asserts every rule reference and every netclass pattern still resolves. This is what stops P2-O5 recurring |
| `checks/p1_regression.py` | one stale label corrected: the support-region line printed `RIB_B2`, which does not exist. The authoritative set is `RIB_R1 RIB_R2 RIB_R3 RIB_B1` |

**Measured effect on DRC: 47 violations → 26.** All 21 `clearance` violations closed, and closed
by naming the vendor land pattern that causes them — not by weakening any routing clearance
anywhere. ERC unchanged at **0 errors / 27 warnings**. Unrouted unchanged at **499**.

---

## 2. The rules that were inert, and why it mattered

`.kicad_dru` was the Beta-DM file, carried across by the fork. It referenced **39 rule areas**.
**All 39 had been deleted by the FBV2-P1 PCB rebuild.**

KiCad's `intersectsArea()` and `enclosedByArea()` return **false** for an unknown name. They do
not warn and they do not error. So **22 of the 71 rules evaluated to "condition never true"** and
DRC reported a clean result against protection that no longer existed. That is the whole of
P2-O5, and it is worse than the entry in `FBV2_P1_FLOORPLAN.md` §16 implied: it was not only the
E5/E6 pockets. It was **every RF band rule, every corridor rule, the header reservation and the
ESP32 antenna rule as well.**

The ESP32 antenna was never actually unprotected — the `U1` footprint carries its own embedded
rule area with every keepout flag set, and that has always been live. But the *file* said the
antenna was protected by a named area that did not exist, and nothing in the toolchain could tell
the difference. `checks/dru_probe.py` now can.

### 2.1 Retirement summary

The full register, with the reasoning for each, is in the `.kicad_dru` header. In brief:

| id | retired | why |
|---|---|---|
| **R1** | `915 KEEPOUT` / `433 KEEPOUT` bands (5 rules) | **premise gone.** Neither sub-GHz radiator is on or over the v2 PCB — 915 is an external whip on an SMA fed by shielded RG-178 (D-223), 433 is a flex bonded to the **left cavity wall**, perpendicular to the board |
| **R2** | E5 corridors and E4 lanes (8 rules) | premise gone with R1. No band splits the board, so In2 needs no corridor and the USB pair needs no In2 excursion |
| **R3** | E2 button escapes (netclass + area terms) | premise gone with R1. No v2 button is in any RF band |
| **R4** | 17 E6 pad-escape pockets | **objects gone and the measurements do not transfer.** Every one was measured against a landed Beta-DM route on a 74 × 155 board. v2 is 70 × 148, placed differently, and unrouted |
| **R5** | `HEADER RESERVED` + `J5_SELF_FANOUT` | object and premise gone. v2's `J5` is a right-edge connector with both ends open, not a bottom-edge field in an 8.5 mm strip |
| **R6** | netclass `E5_CROSSING` (18 patterns) | retired with R2; the class carried Default values, so no net's parameters changed |
| **R7** | netclass `RF_DO_NOT_ROUTE` | **matched zero nets.** `U7.21` / `U8.21` are **netless** on this board — a netless pad cannot carry a track, which is a stronger guarantee than the rule was |
| **R8** | netclass `RF_DEFERRED_NFC` | **premise reversed, and the rule was actively misleading.** The NFC front end was fully designed at FBV2-S1-004B/004C and **must be routed**. Replaced by a real NFC rule set |
| **R9** | `USB_VBUS_RAW` escape-via geometry | net exists, justification does not — it was one Beta-DM via site at a `C20` that now sits elsewhere |
| **R10** | `FP-D6` land pattern | object gone. v2 has `D2 D3 D4 D5`, not `D3`–`D6` |

**Nothing was retired for convenience.** Where a retired rule's intent survives, it is re-expressed
against current objects (ESP32 keepout, switch nodes, USB, NFC). Where a retired rule's intent
genuinely died with the Beta-DM geometry, that is stated as a finding rather than papered over.

### 2.2 The one residual R1 leaves behind

The retired 433 band protected the board **from** an antenna lying over it. Full Beta v2 has the
opposite problem, smaller and newly identified:

> **P2-R1 — ROUTING-STAGE ITEM.** `ANT433_REGION` is doc X −2.400 … −0.200, Y 1.500 … 48.500 —
> **0.2 mm outboard of the left board edge**, over 47 mm of it. Board copper in that band is a
> potential **aggressor into** the flex. The detuning question is separate, belongs to the
> enclosure, and the programme has already accepted the hidden-flex range compromise
> (*"433 MHz hidden = expected range compromise, acceptable for Beta demo"*).
> The aggressor question is real and enforceable: keep switch nodes, the Class-D output and the
> IR pulse path out of doc X 0 … 3.0, Y 1.5 … 48.5.
> **It is deliberately NOT instantiated as a rule area yet**, because `L3`, `Q5` and `D9` occupy
> that band today and **PM-1 changes exactly which parts are there.** Create the area after PM-1
> lands, not before — a rule that contradicts the placement on the day it is written is worse
> than no rule.

### 2.3 Netclass patterns that matched nothing

This is the same class of silent failure, in the project file rather than the rule file, and it
had a more serious consequence.

| pattern | matched | consequence | fix |
|---|---|---|---|
| `/BAT_PROTECTED_P` | **nothing** | the v2 net is `/01_POWER_TREE/BAT_PROTECTED_P`. **The highest-current net on the board was on the 0.20 mm Default class** | `*BAT_PROTECTED_P` |
| — | — | `BAT_RAW`, `BAT_MID` and `BAT_SENSE` also carry the full pack current and were **never in any class** | added `*BAT_RAW`, `*BAT_MID`, `*BAT_SENSE` |
| `/NFC_5V_PA_PENDING` | **nothing** | same root-path defect; the `NFC_5V_PA` class captured no net at all | `*NFC_5V_PA_PENDING` |
| `*BTN_HOME_N` | **nothing** | no such net in v2 | retired with `E5_CROSSING` |
| — | — | **`ACC_5V_LX` — the `U21` boost switch node — had never been in `SWITCH_NODE`** and was routing as an ordinary 0.20 mm Default net | added `*ACC_5V_LX` |
| — | — | `ACC_5V_SW` / `ACC_5V_RAW` (0.70 A) were on Default | new `ACC_5V` class |
| — | — | `NFC_SUPPLY` (`U9` VDD/VDD_TX) was on Default | added to `P3V3` |

`ACC_3V3_SW` was also split out of `P3V3` into its own `ACC_3V3` class, so the ledger states the
rail's real current (400 mA published, 0.76 A ILIM) instead of inheriting the 1.0 A `+3V3` figure.

**Every one of the 57 surviving patterns now matches at least one board net, and `dru_probe.py`
fails the build if that ever stops being true.**

---

## 3. Stackup and layer usage — REVIEWED, RETAINED, ONE GAP RECORDED

The retained 4-layer Beta-DM stackup **remains suitable and is not changed.** The evidence for
keeping it is positive, not inertial: v2 has a 224-net design with a continuous ground
requirement for USB, NFC, four switching converters and a Class-D amplifier, and there is no
2-layer or 6-layer argument on the table.

| layer | intended use — **FROZEN AT FBV2-P2-000** |
|---|---|
| **F.Cu** | **FRONT.** Signals + components. **USB pair (exclusively), SPI-A, display and microSD escapes, community-port fanout, IR, Class-D output** |
| **In1.Cu** | **SOLID, CONTINUOUS, BOARD-WIDE GND REFERENCE. No splits, no analog island.** Enforced: no non-GND track may exist on In1 |
| **In2.Cu** | **Power distribution and SLOW control routing only.** Its only continuous reference is In1 across the **1.065 mm core**, so nothing edge-rate sensitive is permitted. **Forbidden on In2 by rule: USB, NFC transmit arms, the NFC crystal, every switch node, the Class-D output and BAT_MAIN** |
| **B.Cu** | **REAR.** Signals + components. Power stages, radios, **the entire NFC front end**, expanders, microphone |

**Fabrication:** JLCPCB **JLC04161H-7628**, 4 layer, 1.6 mm finished, 1 oz outer / 0.5 oz (H)
inner, 7628 prepreg 0.2104 mm L1→L2 and L3→L4, 1.065 mm core.

> **RECORDED GAP — the board file carries NO physical stackup object.** Neither
> `aqroot-Beta-v2.kicad_pcb` nor `.kicad_pro` declares a stackup; nor does Beta-DM's. The
> geometry above lives only in documentation, so a fabricator would build to its own default and
> **no impedance control is ordered.** This is the honest basis for §7's
> **STACKUP-TO-CONFIRM** marking. It does not block routing, because §7 shows the one
> impedance-sensitive net on this board is electrically short. It **does** belong in the DFM
> release package, and it is carried as **P2-O6**.

### 3.1 The four verifications §6 of the task asked for

| item | verdict |
|---|---|
| **USB reference-plane continuity** | **PASS.** The whole pair sits on F.Cu at doc x 41 … 59, y 1.6 … 28.8. In1 is solid throughout that footprint; the one In1 void on the board (§4.1) starts at x 63.5 |
| **ESP32 RF keepout** | **PASS, and now nameable.** Carried by the `U1` footprint's own rule area and duplicated board-level as `WROOM ANTENNA KEEPOUT` |
| **NFC region** | **PASS.** `NFC_CLEAR_D48` / `NFC_METAL_D58` are **mechanical** regions, not copper keepouts, and never were — the mechanical spec forbids screws, bosses, cans, battery, speaker and cable, not PCB copper, because the antenna's ferrite faces the PCB |
| **Switching-converter return paths** | **FAIL — see PM-1.** In1 continuity is fine; the loops are not, because the inductors are 12.5 … 45.9 mm from their ICs |
| **Class-D speaker routing** | **PASS.** `U5` → `R121`/`R122` → `J6` is 11.9 / 16.6 mm on F.Cu; `SPK_OUT` is forbidden on In2 |
| **Bottom-side modules** | **PASS.** `U7`/`U8` sit on B.Cu at the bottom edge; both stamp-antenna pads are netless; both feeds are IPEX |
| **Community-connector PTH field** | **PASS with margin — see §10.** 24 × Ø0.71 PTH block every layer, but the field is on the right edge with both ends open |

---

## 4. Ground strategy — LOCKED

**One continuous In1 GND plane. No split. No isolated analog-ground island. No exceptions
beyond the one below.**

The direction the task set is adopted verbatim and is now enforced rather than asserted:

* **In1 carries GND and nothing else** — encoded, `severity error`;
* **switching-current loops are localised by placement and routing, not by chopping ground.**
  That is precisely why PM-1 is a blocker rather than a preference: with the inductors 12.5–45.9 mm
  from their ICs there is no routing that produces a small loop, and the temptation to "fix" it
  with a ground cut must be refused;
* **outer-face GND pours** on F.Cu and B.Cu are created **last** (§14 step 17b), not first;
* **no ground copper is added in any antenna keepout** — encoded.

### 4.1 The one authorised In1 void, and what it costs

`WROOM ANTENNA KEEPOUT` removes copper on **all four layers** over doc **X 63.500 … 84.500,
Y −4.000 … 44.000** — an on-board notch of roughly **6.5 × 44 mm on the right edge.**

That notch is in the same corner as `U1`, `U11` (BQ25185), `U18` (LTC4368), `R75`, `D10`, `Q10`,
`R127` and `C2`. **Every return path in the bottom-right corner must be planned around a plane
edge, not assumed continuous.** Concretely:

* no signal may run **along** the notch edge for more than a few millimetres on F.Cu or B.Cu —
  its return has to detour around the void and the loop opens up;
* `U11`'s and `U18`'s ground references must be taken **west** of x = 63.5, not east;
* stitching vias must not be placed inside the notch (encoded).

### 4.2 Stitching policy

| where | policy |
|---|---|
| Board perimeter | continuous stitch at **≤ 7 mm** pitch. Basis: λ/20 at 1 GHz in FR4 (εr 4.4) = 143/20 = **7.15 mm** |
| Every connector GND pad (`J2` shell, `J3` shield and GND, `J4`, `J5` ×4, `J6`, `J7`) | **≥ 1 dedicated via at the pad** |
| Every ESD, converter and RF ground pin (`U10`, `D2`–`D5`, `U12`, `U13`, `U17`, `U21`, `U9`, `U5`) | **≥ 2 vias at the pad** |
| `U1` thermal pad | the **12 manufacturer Ø0.20 mm vias** already do this — do not add, do not enlarge (D-228) |
| Inside `WROOM ANTENNA KEEPOUT`, `MIC_ACOUSTIC_KEEPOUT`, `BOSS1_KEEPOUT`, `BOSS2_KEEPOUT` | **none** — encoded |
| Under the NFC loop (Ø48) | **no stitching lattice.** The pours may fill the region per the mechanical spec, but a deliberate dense via array under a 13.56 MHz loop buys nothing and is a tuning variable. Confirm at first-article NFC tuning, which is mandated anyway |

**A via is not decoration.** Every stitching via above answers a specific return path or a
specific plane discontinuity. There is no "sprinkle vias on the pour" step in this plan.

### 4.3 The subsystems the task named, reviewed

| subsystem | ground finding |
|---|---|
| ESP32 antenna | 4-layer void, mandatory, §4.1. The module's own RF never reaches board copper |
| 433 flex | off-board on the cavity wall. **No ground copper is removed for it**; the residual is P2-R1 (§2.2), an aggressor question |
| 915 coax / SMA | fully shielded from `U8`'s IPEX to the bulkhead. **The board carries no 915 MHz current at all.** The SMA body grounds to the enclosure, not the PCB |
| NFC Ø48 / Ø58 | mechanical regions. Copper permitted; §4.2 row 7 applies |
| USB | solid In1 under the whole pair. `U10` GND to In1 with ≥ 2 vias at the pad |
| Class-D / speaker | `SPK_P`/`SPK_N` routed as a tight pair on F.Cu with In1 beneath; the `C81`/`C82` EMI caps (DNP) must remain reworkable — see §16 item E |
| Switching regulators | In1 solid under every inductor; return via pair at each IC ground pin. **Loop area is PM-1, not a ground problem** |
| IR pulse current | loop `C12` → `R24` → `D1` → `Q1` → In1 is already local (9.28 mm). Place a via pair at `Q1` source so the return does not wander |
| Community ESD arrays | each `TPD4E1B06` GND pin gets ≥ 2 vias at the pad; the surge return must reach In1 **before** the internal net, never through it |

---

## 5. THE THREE PLACEMENT MOVES — surfaced now, not routed around

The task is explicit: *"If a placement change is required for electrically correct routing:
surface it NOW. Do not route around a bad power placement."* Three do. All three are **new
findings**, all three are **measured from the board**, and none of them existed in Beta-DM to be
carried forward — the battery-protection block and the NFC front end are **new in Full Beta v2**
and this is the first time either has been looked at with an electrical eye rather than a
mechanical one.

### PM-1 — all four switching converters have their inductor off the IC

| converter | IC (doc) | inductor (doc) | switch-node span | requirement |
|---|---|---|---|---|
| `U12` TPS63020 +3V3 buck-boost | (12.000, 96.000) | `L1` (2.994, 89.010) | **12.96 / 12.54 mm** (both LX nodes) | ≤ 5 mm |
| `U13` TPS61023 NFC 5 V | (18.000, 124.000) | `L2` (3.254, 99.261) | **28.56 mm** | ≤ 5 mm |
| `U21` TPS61023 accessory 5 V | (10.000, 124.000) | `L4` (3.442, 94.111) | **30.50 mm** | ≤ 5 mm |
| `U17` TPS61169 backlight | (48.000, 34.000) | `L3` (3.702, 37.004) | **45.90 mm** | ≤ 5 mm |

The backlight case is the worst and is worth stating in full. `BL_SW` runs `U17.1` (47.2, 33.3) →
`L3.2` (4.9, 37.0), and the **catch diode `D8` is at (50.6, 36.5) — next to the IC, 45.7 mm from
the inductor.** The boost energy loop `L3 → D8 → C44` is therefore about **76 mm around**, and it
switches at 1.2 MHz between 0 V and **up to 39 V** under the open-LED fault TI specifies. It runs
the length of the left margin, **13 mm from `MK1`**, through the band the 433 flex sits against.

**All four inductors were placed in the left-margin column at x ≈ 3 while their ICs went
elsewhere.** This is systemic, not four coincidences.

**No routing repairs it.** Loop area is a placement property. The `.kicad_dru` now carries every
switch-node rule that *is* encodable — In2 prohibition, 0.40 mm width floor, antenna and
microphone exclusion, and explicit 0.40–0.50 mm separations from I2C, USB, I2S and all three NFC
classes — and those rules will correctly permit a 45.9 mm switch node, because a rule cannot tell
a router where an inductor should have gone.

**Recommendation (CTO decision, not taken here):** move each inductor and its output capacitor to
its own IC, keeping every converter's power stage inside a ≤ 8 mm cluster. Three of the four
(`U12`, `U13`, `U21`) already have their ICs within 31 mm of their inductors in the same rear
band, so those are local moves. `U17` is the one that needs a real decision: either `L3` + `C44`
join `U17` in the bottom-right, or `U17` joins `L3` in the left margin — and the second option
walks the 39 V node **towards** the microphone and the 433 flex, so the first is preferred.

### PM-2 — the single-fault battery-protection block is dispersed over 96 mm

This block — fuse, back-to-back FETs, LTC4368-1, 15 mΩ shunt, charger, and the dead-cell recovery
comparator network — **does not exist in Beta-DM** (that is blocker B-01). It was designed at
FBV2-S1-001/002 and placed at FBV2-P1 into whatever rear pockets were free. Measured today:

| what | where | measured |
|---|---|---|
| `J4` battery connector → `F1` fuse | (63.500, 102.000) F → (62.599, 93.045) F | 9.0 mm ✔ |
| `F1` → `Q2` → `Q3` | → (52.749, 108.420) B → (52.296, 114.643) B | 18.3 + 6.2 mm ✔ |
| **`Q3` → `R75` shunt** | → (57.643, 35.865) B | **79.0 mm** ✘ |
| `R75` → `U11` BQ25185 | → (56.000, 32.000) B | 4.2 mm ✔ |
| **total high-current path** | | **≈ 116.7 mm** |

**What is actually right, and stays right:** the Kelvin sense is sound. `U18.9` (SENSE) and
`U18.8` (OUT) both land on `R75`'s two pads and `U18` is **4.2 mm** from `R75`, so the 47 mV
overcurrent measurement across the 15 mΩ shunt at the 3.125 A trip is **not** corrupted by the
long run. That is the single most safety-critical measurement in the block and it is fine.

**What is wrong:**

| net | span | what it is | why it matters |
|---|---|---|---|
| `LTC_GATE` | **95.6 mm** | LTC4368 charge-pump **GATE**, ~20 µA source, driving four FETs | a µA-impedance node that holds the battery pass FETs enhanced, run the length of the board past four switching converters. Its RC damping (`R76` 22 k at (21.8, 93.0) + `C57` 4.7 nF) is **31–45 mm from the FETs and 60–75 mm from `U18`** |
| `BAT_SENSE` | **96.5 mm** | FET source **and** 1.5 A conductor | 79 mm at 1.0 mm / 1 oz = 38.8 mΩ → **58 mV and 87 mW at 1.5 A**. The FET source reference sits 79 mm from the controller's SENSE pin |
| `LTC_OV` | 78.4 mm | 3.65 M / 442 k overvoltage divider | ~400 kΩ node carrying the **battery overvoltage trip point** |
| `LTC_UV` | 81.7 mm | 510 k / 442 k undervoltage divider | same, for undervoltage |
| `LTC_SHDN` / `LTC4368_FAULT_N` | 72.0 / 85.4 mm | 1 M nodes | shutdown and fault reporting |
| `VBRIDGE_TOP` | **90.1 mm** | `D10` (60.2, 32.0) → `R85` 2.2 M (11.6, 108.0) | dead-cell reference bridge |
| `VREF_TOP` | 80.8 mm | `D11` (51.8, 32.3) → `R87` 2.2 M (19.2, 106.3) | dead-cell reference bridge |
| `REF_HO` | 82.4 mm | `R91` 3.65 M (55.0, 44.0) ↔ `R92` 1.30 M (16.6, 84.3) ↔ `U19` (3.3, 84.5) | the two halves of one divider are **38 mm apart**, and the comparator is **52 mm** from the top resistor |

The pattern is one thing said three ways: **the block sits in three clusters** — `U18`/`R75`/`U11`
in the bottom-right (y 30–45), `Q2`/`Q3` in the top-right (y 108–115), and `U19` + `Q4`–`Q9` +
the divider network in the far-left column (x 2–25, y 64–110) — **with multi-megohm comparator
nodes and a micro-amp gate node strung between them.**

This is the network that decides whether the pack is disconnected on a fault (D-050…D-054) and
whether a deeply discharged cell gets recovery current (D-049, D-105). Its trip points are set by
0.4–3.65 MΩ dividers. **Routing cannot make a 3.65 MΩ node that crosses four switching
converters immune to coupled charge.**

**Recommendation (CTO decision, not taken here):** consolidate the protection controller with the
element it controls. Move `U18`, `R75`, the `R77`/`R78`/`R79` trip dividers and the `R80`–`R83`
network **north to the battery-entry corner** with `J4`, `F1`, `Q2` and `Q3`, and bring the `U19`
dead-cell comparator's reference partners (`D10`, `D11`, `R91`) to `U19` — or move the whole
dead-cell block to the entry corner as well. That converts **five long high-impedance nets and
two long high-current nets into one long run** (`BAT_PROTECTED_P`, entry corner → charger), which
is the only one of them that a wide trace genuinely fixes.

**It also reduces an open blocker.** B-34 records ≈ 0.70 W of series loss and ≈ 0.40 V of drop in
the BATFET + protection path at 1.75 A inside a sealed enclosure. The 116.7 mm of high-current
copper adds roughly **0.13 W at 1.5 A / 0.18 W at 1.75 A** on top of that figure. PM-2 gives most
of it back.

### PM-3 — the NFC differential front end is not symmetric

The matching network was locked at FBV2-S1-004B/004C, is bench-tuned at first article by
standing order, and `R_q` is **1.1 Ω per arm** with a network Q of **≈ 21** (D-204). Measured:

| item | arm A | arm B | comment |
|---|---|---|---|
| matching node span | `NFC_MATCH_A` **24.18 mm** | `NFC_MATCH_B` **34.21 mm** | **10 mm of asymmetry before a single track is drawn** |
| EMC inductor | `L5` (31.799, 102.570) | `L6` (28.494, 122.088) | **19.8 mm apart, on OPPOSITE sides of `U9`** |
| Q resistor | `R114` (47.351, 100.806) | `R115` (57.097, 103.784) | 10.2 mm apart, 17–27 mm from `U9` |
| antenna node | `NFC_ANT_A` 8.82 mm | `NFC_ANT_B` 12.49 mm | asymmetric again |
| EMC filter caps | `C69`/`C71`/`C73` spread over **13.6 mm** | `C70`/`C72`/`C74` spread over **17.2 mm** | one filter node, three capacitors, 14–17 mm apart |
| crystal | `Y1` (36.500, 112.000), 6.5 mm from `U9` | load caps `C79` (22.7, 105.0) / `C80` (25.7, 103.1) | **the load capacitors are 13–15 mm from the crystal, on the far side of the IC.** The oscillator loop is ~30 mm around |
| supply decoupling | `C47`/`C48` at 5.8 / 5.9 mm from `U9.7` | `C50` at 9.0 mm from `U9.9` | an RF front end wants < 2 mm |

`U9`'s digital side is fine; this is entirely about the analogue front end.

**No routing repairs it.** The `.kicad_dru` now confines both arms to B.Cu, forbids **every via**
on them and on the crystal nets, sets an equal 0.40 mm target width and a 0.25 mm routed
clearance — everything that *is* encodable. A rule cannot move `L6` to sit beside `L5`.

**Recommendation (CTO decision, not taken here):** rebuild the front end as a mirrored pair about
a single axis running `U9` → `J7` — `L5`/`L6` adjacent and equidistant from RFO1/RFO2, then
`C71`/`C72`, then `R114`/`R115`, then `J7` — with the EMC capacitor triplets grouped at their own
inductor; move `C79`/`C80` to `Y1`; and pull the `NFC_VDD_*` decoupling in to under 2 mm.
Everything named here is on B.Cu inside the NFC clear region, which has room.

### PM-4 — thermal, and it composes with PM-2

`U11` BQ25185 is at doc (56.000, 32.000) on **B.Cu**, which is **inside `BATTERY_SHADOW`**
(X 6.00 … 66.00, Y 23.50 … 98.50) — about 10 mm in from the pouch's south and east edges. The
charger dissipates roughly **(5 − 3.7) × 0.5 = 0.65 W while charging**, plus its 115 mΩ BATFET
loss on discharge, and it does so **pressed against the cell it is charging**, in a sealed
enclosure, with the battery's own 0–45 °C charge window as the limit.

*"Do not rely on the battery as a heatsink"* is the task's instruction and this is the one place
the board does. **Recommendation: move `U11` out of the battery shadow into the bottom band
(Y < 23.5) near `J3`, which is also where its `VBUS` comes from — `J3` is 27 mm away today.**
This is not independent of PM-2: if the protection block consolidates at the battery-entry
corner, `U11`'s natural home is the USB end, and `BAT_PROTECTED_P` becomes the single long
high-current run the plan already expects.

Recorded as **PT-1**, ranked below PM-1/2/3: it is a reliability and cell-life item, not a
correctness one, and it does not by itself block routing.

---

## 6. Switching-converter routing plan

Applies **after** PM-1. Identical structure for all four.

| element | rule |
|---|---|
| **VIN capacitor loop** | the input capacitor's two terminals, the IC's VIN and the IC's GND form the **smallest** loop on the board. Cap within 1.5 mm of VIN; GND terminal reaches In1 through **its own via at the pad**, never a shared one |
| **Switch node** | ≥ 0.40 mm wide, **as short and as narrow-in-area as the current allows** — this is the one net where you do not widen "for margin", because area is the radiator. Outer layer only, **no via** unless individually proven |
| **Inductor** | directly at the SW pin. Nothing routes underneath it on the opposite face; In1 stays solid beneath it |
| **Output capacitor** | closes the loop back to the same GND node as the input capacitor, not to a distant plane point |
| **Feedback divider** | at the **IC**, not at the load. The FB node is a high-impedance, micro-amp node: **no via, ≤ 5 mm, and it must not run beside or beneath the switch node.** Its lower resistor's ground goes to the IC ground pin |
| **GND return** | ≥ 2 vias at the IC ground pad; ≥ 4 on `U12`'s exposed pad |
| **Copper / thermal** | `U12` ≈ 0.37 W and `U13`/`U21` ≈ 0.28 W each — spread the GND and output-node copper local to each IC. See §13 |

**Switch-node keepouts, encoded in `.kicad_dru`:**

| victim | separation | encoded |
|---|---|---|
| I2C (`I2C` class) | **0.50 mm** | ✔ |
| USB pair (`USB_D`) | **0.50 mm** | ✔ |
| NFC receive path (`NFC_RX`) | **0.50 mm** | ✔ |
| NFC transmit arms (`NFC_RF`) | **0.50 mm** | ✔ |
| NFC crystal (`NFC_OSC`) | **0.50 mm** | ✔ |
| I2S (`I2S`) | **0.40 mm** | ✔ |
| Microphone `MK1`, amplifier `U5` | courtyard exclusion | ✔ |
| ESP32 antenna | area exclusion | ✔ |
| RF module controls | covered by the `NFC_*` and courtyard rules plus the SPI-B trunk plan (§9) | partial |

`LED_BOOST` carries the same 0.50 mm separation from USB and I2C, justified by the **39 V**
open-LED fault case rather than the 4.5 V operating case.

---

## 7. USB routing plan — the short version is the correct version

**USB 2.0 FULL SPEED.** The ESP32-S3 has no High-Speed PHY. Specified rise time 4–20 ns, so the
critical length is `t_r · v / 6 = 4 ns × 150 mm/ns / 6 =` **100 mm** at the fastest permitted edge.

**Measured endpoints and path:**

```
J3.A6/B6 (41.2, 1.6)  D+  →  U10.3 (49.3, 4.3)      8.5 mm
J3.A7/B7 (41.8, 1.6)  D−  →  U10.1 (49.3, 6.2)      8.8 mm
U10.4 (51.5, 4.3)         →  R34.1 (57.6, 8.7)      7.5 mm
U10.6 (51.5, 6.2)         →  R33.1 (54.0, 8.8)      3.5 mm
R34.2 (59.2, 8.7)         →  U1.14 (45.5, 28.8)    24.3 mm
R33.2 (55.6, 8.8)         →  U1.13 (46.8, 28.8)    21.9 mm
```

| requirement | value | basis |
|---|---|---|
| Pair width / gap | **0.25 mm / 0.20 mm**, outer layers | 90 Ω target on F.Cu over In1 |
| Target differential impedance | **90 Ω** — retained as good practice, **not as a gate** | see STACKUP-TO-CONFIRM below |
| Skew target | **none imposed.** Intrinsic placement mismatch is 2.4 mm = **17 ps** against a ~1 ns Full-Speed budget | measured |
| Layer | **F.Cu, exclusively.** In2 is forbidden outright | encoded |
| Reference plane | **solid In1 under the entire run.** No plane split or void is crossed; the one In1 void starts at x 63.5 | measured |
| Via policy | **ZERO vias.** The pair never needs to change layer | measured |
| ESD placement | `U10` USBLC6-2SC6 **between `J3` and the 22 R series resistors** — the correct order. Its GND pin reaches In1 through **≥ 2 vias at the pad**; the `J3` → `U10` run stays short and direct | inspected |
| Stub avoidance | **no stub on D+ or D−.** `J3`'s A/B pin pairs are the only permitted fanout, and they are 1.0 mm apart | measured |
| Uncoupled budget | ≤ 25 mm. Actual uncoupled sections: the `J3` fanout and the `R33`/`R34` splay (**3.6 mm apart in X**) | encoded |

> **STACKUP-TO-CONFIRM.** The 90 Ω figure was computed for h = 0.2104 mm, Dk 4.4, t = 35 µm →
> W 0.30 / S 0.20 = 89.3 Ω. Two things are unconfirmed and are recorded rather than assumed:
> **(a) the board file carries no stackup object at all** (§3), so a fabricator builds to its own
> default; **(b) Dk 4.4 is not JLCPCB's published figure for 7628 prepreg.** Neither matters at
> Full Speed over 40 mm — which is exactly why this is marked and not treated as a blocker. If
> impedance control is ever ordered, re-derive W/S from the fabricator's own stackup **before**
> changing these numbers.

---

## 8. SPI-A routing plan — display and microSD

Three nodes: `U1` (56.75, 20.0), `J2` microSD (14.0, 11.2), `J1` display FPC (31.66, 52.0).

**Measured span 44.5 … 47.8 mm.** Beta-DM's was **125.2 … 128.2 mm**. **The v2 floorplan made
this bus 63 % shorter**, and Beta-DM's longer version was design-complete and DRC-clean.

| item | plan |
|---|---|
| Topology | **daisy-chain trunk `U1` → `J1` → `J2`**, not a star. `J1` is between the MCU and the card slot geographically, so the natural route is also the correct one |
| `SCK` / `MOSI` | one trunk each, branch stubs at `J1` ≤ 5 mm |
| `MISO` | `J2.7` → `U1.21`. `R112` is **DNP**, so the display is **not on MISO** on the first build — do not route a stub to `J1.33` beyond `R112`'s own pad |
| `CS` lines | `DISP_CS_N` and `SD_CS_N` are point-to-point; both have 10 kΩ pull-ups to `+3V3` (`R26`, `R25`) so **both devices are deselected through reset**. Keep each pull-up at its own device end |
| `DISP_DC` | point-to-point `U1.22` → `J1.37`, routed with `SCK` |
| Display `SDO` isolation | `DISP_SDO` = `J1.33` + `R112.1` + `TP36.1` only. **`R112` is the isolation and it must stay a real, reworkable 0402 site** — `TP36` characterises SDO without fitting anything |
| Length matching | **NONE.** At 46 mm the round-trip delay is 0.67 ns; the ILI9488's 3-byte-per-pixel writes make throughput, not clock rate, the limit |
| Series damping | **NONE added.** Three nodes, 46 mm, and one of the three is off-bus by default. Damping here would be speculative |
| Star stubs | forbidden. Trunk-and-short-branch only |
| MX-8 | **binding, and unchanged by layout.** microSD and display must not transact simultaneously. This is a firmware contract; **it is not a licence to share a track** |

---

## 9. SPI-B / radio / NFC routing plan

Four nodes across three widely separated locations: `U1` (56.75, 20.0) F, `U9` (30.0, 112.0) B,
`U7` (26.0, 12.0) B, `U8` (9.0, 12.0) B.

**Measured span 113.1 … 114.1 mm.** Beta-DM's was **143.4 … 144.0 mm** — v2 is **21 % shorter**
than a topology that shipped.

| item | plan |
|---|---|
| Clock ceiling | **≤ 10 MHz.** SX1262 16 MHz, CC1101 ≈ 6.5 MHz, ST25R3916 ≈ 10 MHz — the slowest device sets it |
| Topology | **one trunk, `U1` → `U9` → `U7` → `U8`**, following the physical order down the board. **Never a star.** Branch stubs at each device **≤ 10 mm** |
| Layer | keep `SCK`/`MOSI`/`MISO` **on the same layer through the trunk** so the three share one return path; ≤ 2 vias per net |
| Critical direct lines | `SX1262_BUSY`, `SX1262_CS_N`, `SX1262_RST_N`, `SX1262_RXEN`, `SX1262_DIO1`, `CC1101_CS_N`, `CC1101_GDO0`, `NFC_CS_N`, `NFC_IRQ` — **point-to-point, no stub, no shared segment.** `BUSY` and the two IRQ/GDO lines are the ones a hung transaction depends on |
| Signal integrity | at 10 MHz over 114 mm with three T-junctions this bus is **in the ringing regime** (round trip ≈ 1.6 ns against a ~1–2 ns ESP32 edge). It was in the same regime on Beta-DM at 144 mm and was accepted. **The trunk-not-star topology and the ≤ 10 mm stub rule are the mitigation.** If bring-up shows a problem the lever is **source series damping at `U1`** — that is a **schematic change and needs CTO approval**; it is not a routing decision and no pads for it exist |
| MX-1 | at most one of {Wi-Fi TX, LoRa TX +22 dBm, sub-GHz TX, NFC field}. Binding, and it does not reduce the bus's capacitive loading — all three devices remain on the bus regardless of CS |
| Module RF | **not routed on the motherboard, and cannot be.** `U7.21` and `U8.21` are netless; both feeds are IPEX |

---

## 10. NFC routing plan

Applies **after** PM-3. Every component is on **B.Cu**.

```
U9.13 RFO1 → L5 → C71 → R114 → J7.1        arm A
U9.15 RFO2 → L6 → C72 → R115 → J7.2        arm B
EMC filter: C69/C71/C73 on arm A, C70/C72/C74 on arm B
receive:    R116 / R117 dividers → RFI1 / RFI2
crystal:    Y1 27.12 MHz with C79 / C80
```

| requirement | rule |
|---|---|
| **Differential symmetry** | **arm A and arm B equal to within 1 mm of routed length, equal width, mirrored about the `U9` → `J7` axis.** This is the governing requirement and it is a *placement* precondition (PM-3), not a routing one |
| Shortest-path intent | each stage sits at the next; no arm doubles back past the IC |
| Via preference | **ZERO vias on `NFC_RF` and `NFC_OSC` — enforced by rule.** A via is an asymmetry and an inductance in a network whose total series resistance is 1.1 Ω per arm |
| Layer | B.Cu only; F.Cu and In2 forbidden by rule for `NFC_RF`, `NFC_OSC` and `NFC_RX` |
| Width | **0.40 mm target, 0.30 mm floor, identical on both arms.** Width here is a symmetry and loss parameter — the coil current is ~187 mA and the thermal minimum is 0.036 mm |
| Clearance | 0.25 mm routed; **0.50 mm from every switch node** — enforced |
| Ground / copper | In1 solid beneath the whole front end. **No stitching lattice under the Ø48 loop** (§4.2). No pour island is cut for the front end |
| Component ordering | RFO → EMC inductor → EMC capacitors → matching capacitor → Q resistor → connector. **Do not reorder to suit routing** — the network was solved in that order (D-134) |
| Tuning accessibility | `C71`, `C72`, `C75`, `C77`, `R114`, `R115`, `L5`, `L6` are all marked TUNE and **must remain hand-reworkable**: no part closer than 1.0 mm on the tool side, no pour flooding right up to the pad, and no component placed over them on the opposite face |
| Test points | `TP37` (`NFC_ANT_A`) and `TP38` (`NFC_ANT_B`) are the tuning probe points. Keep them **symmetric about the axis and equidistant from `J7`** — an asymmetric probe pair measures its own asymmetry |
| Crystal | `C79`/`C80` at `Y1`; oscillator loop ≤ 8 mm around; no via; the load-cap grounds return to `U9`'s ground pin |
| Off-board feed | `J7` → the flex loop is **not ordinary GPIO routing.** It is one half of a tuned differential network that continues off the board |

---

## 11. I2C routing plan

### 11.1 Internal bus — this one has a real, derived budget

10 nodes: `U1`, `U2`, `U3`, `U23`, `U4`, `U14`, `U16`, `J1` (touch), plus `R19`/`R20` and `TP4`/`TP5`.
**Measured span: SCL 100.7 mm, SDA 92.5 mm** (Beta-DM: 89.9 / 90.7 mm — v2 is ~11 mm longer
because `U23` was added).

> **HARD BUDGET: `C_bus` ≤ 161 pF at 400 kHz.**
> Derivation: I2C Fast-mode requires `t_r` ≤ 300 ns; with a 2.2 kΩ pull-up,
> `C = t_r / (0.847 · R) = 300 ns / (0.847 × 2200) =` **161 pF**.
> Eight devices at ~7 pF, plus the display FPC, plus ~100 mm of plane-referenced copper at
> ~1 pF/mm, is **already close to that number.** This is not a theoretical constraint.

| item | plan |
|---|---|
| Topology | **one trunk down the right-hand expander column** (`U23` y 47.7 → `U2` y 57.7 → `U3` y 67.7 → `U4` y 77.1 → `U16` y 94.3), with **two branches**: south to `U1` (y 11.2) and west to `J1` (x 22) and `U14` (x 27) |
| Branch lengths | each device stub **≤ 5 mm** off the trunk. The `U14` branch is the long one and should be taken from the trunk's north end, not looped |
| Layer / reference | F.Cu and In2, In1 solid beneath. Keep SCL and SDA **on the same layer and adjacent** so they share a return |
| Pull-ups | `R19`/`R20` 2.2 kΩ sit at (41.6, 27.0) / (40.8, 15.3), near `U1` — i.e. at one **end** of the trunk. Acceptable; do not add a second pair |
| Switching proximity | **≥ 0.50 mm from every switch node and from `LED_BOOST`** — enforced |
| If the budget is exceeded | two levers, in order: **(1) run 100 kHz**, where `t_r` ≤ 1000 ns gives `C ≤ 537 pF` and the margin is large — and 100 kHz is the bring-up target anyway; **(2) lower the pull-ups**, which is a **schematic change needing CTO approval**. Do **not** solve it by adding a buffer: **no mux, no repeater** (locked) |

### 11.2 External / community bus

`U16` TCA4307 → `R47`/`R48` 22 R → `D2` TVS → `J5.2` / `J5.6`. **Measured on-board span 18.3 …
21.3 mm.** 1.5 kΩ pull-ups (`R49`, `R50`) on the buffered side.

| item | plan |
|---|---|
| Budget | ≤ 200 pF at 400 kHz / ≤ 400 pF at 100 kHz **including the accessory cable**, so the on-board share must stay small — 21 mm is well inside |
| Ceiling | **400 kHz max — Fast mode, NOT 1 MHz** (SCPS270B) |
| Order | buffer → **22 R series** → **TVS** → connector. The TVS must sit **between the series resistor and `J5`**, so the surge is clamped before it reaches the resistor |
| ESD ground | `D2`'s GND pin gets ≥ 2 vias at the pad; the surge return reaches In1 **before** the internal net |
| Boundary | the community boundary is `U16`. Nothing on the accessory side of it may share copper with an internal net |
| Layer | F.Cu; In1 and In2 forbidden for the external pair |

---

## 12. Audio routing plan

**Microphone — `MK1` PUI DMM-4026-B-I2S-R, digital I2S, bottom-port through a Ø1.05 mm NPTH.**

| item | plan |
|---|---|
| I2S | `BCLK` ≈ 3.07 MHz at 48 kHz / 32-bit stereo — trivial. Route `BCLK`, `LRCLK`, `MIC_DIN` **as a group** so clock and data share one return |
| Layer | F.Cu / In2; ≤ 2 vias per net |
| Acoustic | `MIC_ACOUSTIC_KEEPOUT` is a **real rule area** — no track, via or pour on any layer, both faces. Do not route through it and do not stitch into it |
| Escape | `MK1` is at (3.000, 50.000) B.Cu with a 1.65 mm GND ring around a Ø1.05 mm NPTH. **Its `MIC_DIN` escape must be checked first**, before the surrounding area is committed — this exact pad was a trapped escape on Beta-DM |
| Switch nodes | forbidden inside `MK1`'s courtyard — enforced. Note `L3` is **13 mm away today**; PM-1 moves it |

**Speaker — `U5` MAX98357A, Class-D, `J6`, 152 mm off-board lead.**

| item | plan |
|---|---|
| The honest framing | **the output is a switching waveform, not an analogue one.** There is no analogue audio path on this board to protect |
| Routing | `U5.9`/`U5.10` → `R121`/`R122` → `J6`. **Measured 11.9 / 16.6 mm.** Route `SPK_P` and `SPK_N` as a **tight, equal-length, equal-width pair** — the differential loop is what radiates |
| Layer | **F.Cu only; In2 forbidden by rule.** In1 solid beneath |
| Edge containment | keep the pair away from the board edge and from the `J6` aperture; the 152 mm lead is the real antenna and the board should not add to what it carries |
| Separation | ≥ 20 mm from `MK1` and from the NFC front end. Measured `MK1` ↔ speaker centre-to-centre is 67.4 mm on opposite faces — comfortable |
| EMI capacitors | `C81` / `C82` 1 nF are **DNP**. Their pads must stay **reworkable**: nothing placed over them, no pour flooding the pads. See §16 item E |

---

## 13. Community-port escape — FEASIBLE, WITH LARGE MARGIN

`J5` Samtec BCS-112-S-D-HE, doc (64.900, 121.000), rotation 270°, 24 × Ø0.71 mm PTH.

**Measured geometry:**

| item | value |
|---|---|
| East pad row | x = **68.835**; pad Ø1.30 → east pad edge at 69.485, **0.515 mm** from the board edge |
| West pad row | x = **60.965**; west pad edge at 60.315 |
| **Inter-row channel** | **6.570 mm wide × 27.94 mm long** — the main escape lane |
| Vertical pad gap within a row | 2.540 − 1.300 = **1.240 mm** → at 0.20 mm clearance this passes **two 0.20 mm tracks per gap per layer** |
| Gaps available in the west row | **11**, plus the open north end (y > 135.6) and the open south end (y < 106.4) |
| Layers usable for crossing | **F.Cu, B.Cu, In2.Cu** (In1 is GND-only) |

**Demand vs capacity:**

| | value |
|---|---|
| East-row signal pads that must reach the west side | **10** (`XGPIO0`, `XGPIO1`, `XGPIO4`, `XGPIO5`, `XGPIO7`, `NATIVE_A`, `NATIVE_B`, `ACC_DETECT_N`, `ACC_3V3_SW` ×2) |
| West-row signal pads | 10, all escaping **west directly** — no crossing needed |
| GND pads (4, 9, 16, 21) | drop straight into In1 on their own barrels — **no channel demand** |
| **Crossing capacity, F.Cu alone** | 11 gaps × 2 = **22**, plus 2 free lanes at the open ends |

**Verdict: 10 crossings needed, 22 available on one layer, three layers usable, both ends open.
No placement nudge is required and no reservation area is needed.** This is the opposite of the
Beta-DM situation, where `J5` sat on the bottom edge in an 8.5 mm strip and needed a scoped
reservation plus a named fanout exception (retired as R5).

**Escape priority, highest first:** `GND` → `ACC_3V3_SW` → `ACC_5V_SW` → `NATIVE_A`/`NATIVE_B`
(GPIO38/47) → `EXT_SDA`/`EXT_SCL` → `WAKE_ATTN_N` → `ACC_DETECT_N` → `XGPIO0`–`XGPIO9`.

**Constraints that must hold on every escape:**

* **3.3 V CMOS only** on every exposed contact;
* the **100 R series resistor** (`R51`–`R64`) and the **TPD4E1B06 TVS** must both sit **between
  the internal net and `J5`** — never after the connector, never bypassed by a "shorter" route;
* the TVS ground reaches In1 **before** the internal net;
* `ACC_3V3_SW` and `ACC_5V_SW` are **load-switched rails** — route them at their class width, not
  as signals, and take each connector pin from the switch output, not daisy-chained through the
  other pin;
* `WAKE_GATE_S` / `Q10`'s orientation is load-bearing (D-187) — do not "tidy" the gate net.

---

## 14. Routing order — CTO list EVALUATED, three changes, each with a reason

| # | step | change |
|---|---|---|
| 1 | Safety-critical battery / charger path | unchanged. **Blocked on PM-2** |
| 2 | Main regulator power loops | unchanged. **Blocked on PM-1** |
| 3 | Accessory power converters | unchanged. **Blocked on PM-1** |
| 4 | Backlight converter | unchanged. **Blocked on PM-1** |
| 5 | USB differential pair | unchanged. Ready now |
| 6 | **NFC front end *and* the 27.12 MHz crystal** | **CHANGED — steps 6 and 7 merged.** The crystal is part of the NFC front end: same IC, same face, same no-via rule, same netclass block. Routing it in a separate later pass invites a via or a layer change that §10 forbids. **Blocked on PM-3** |
| 7 | *(was: critical clocks / crystals)* | merged into 6. There is no other crystal on the board |
| 8 | SPI-A | unchanged |
| 9 | SPI-B | unchanged |
| 10 | I2C | unchanged |
| 11 | I2S / Class-D | unchanged |
| 12 | IR | unchanged |
| 13 | Community connector escape | unchanged |
| 14 | Resets / straps / interrupts | unchanged |
| 15 | Ordinary GPIO | unchanged |
| 16 | Remaining low-speed nets | unchanged |
| **17a** | **Return-path stitch vias, placed WITH each loop above** | **NEW.** Each converter's and each connector's ground vias belong to *that* step, not to a sweep at the end. A return path retro-fitted after the fact is a return path nobody checked |
| **17b** | Final F.Cu / B.Cu GND pours, then perimeter stitching | unchanged in position; **split from 17a** so the two are not conflated |

**Everything else in the CTO's order is adopted without change**, including the principle behind
it: current before signals, and the smallest, least reroutable loops first.

---

## 15. Via and layer policy

| class | via policy | enforced |
|---|---|---|
| **USB pair** | **zero vias.** In2 forbidden outright; the pair stays on F.Cu end to end | ✔ rule |
| **NFC transmit arms** | **zero vias.** F.Cu and In2 forbidden | ✔ rule |
| **NFC crystal** | **zero vias.** F.Cu and In2 forbidden | ✔ rule |
| **NFC receive** | ≤ 1 via; F.Cu forbidden | ✔ rule (layer) |
| **Switch nodes** | **no via unless individually proven.** In2 forbidden | ✔ rule (layer) |
| **Feedback nodes** | **no via.** ≤ 5 mm, at the IC | procedural |
| **High-current rails** (`BAT_MAIN`, `SYS_MAIN`, `P3V3`, `ACC_3V3`, `ACC_5V`, `VBUS_CHG`, `NFC_5V_PA`) | **≥ 2 POWER vias (0.40 mm drill) per layer change. Never a single via** | drill floor ✔ rule; count procedural |
| **`BAT_MAIN`** | outer layers only — at 0.5 oz inner, 1.5 A needs 2.73 mm | ✔ rule |
| **Class-D output** | outer layers only | ✔ rule |
| **Ordinary GPIO** | normal 0.30 mm-drill vias, unrestricted count | — |
| **Ground stitching** | **intentional, never decorative.** §4.2 lists every place a stitch via is required; nowhere else needs one | procedural |
| **Antenna keepouts** | **no via of any kind**, stitching included | ✔ rule |
| Microvia / blind / buried | **forbidden** | ✔ rule |
| Annular ring | ≥ 0.125 mm | ✔ rule |
| `U1` pad-41 thermal array | **12 × Ø0.20 mm manufacturer geometry — pinned, not waived.** Do not enlarge, do not add | ✔ rule (D-228) |

**A through via occupies every copper layer including In1.** Plan In1 keepouts and return paths
around via fields, not after them.

---

## 16. Thermal strategy

| source | dissipation | plan |
|---|---|---|
| **`U11` BQ25185** | **≈ 0.65 W charging** at 500 mA from 5 V at V_BAT 3.7, plus 115 mΩ BATFET on discharge | **the largest single source, and it is inside the battery shadow — PT-1 (§5).** Spread B.Cu copper on the GND and `SYS` pads; ≥ 4 vias to In1 on the thermal pad. **Do not treat the cell as the heatsink** |
| **`U12` TPS63020** | ≈ 0.37 W at 1 A out | exposed pad → In1 with **≥ 4 THERMAL vias (0.25 mm drill)**; spread copper on `SYS` and `+3V3` local planes |
| **`U13` / `U21` TPS61023** | ≈ 0.28 W each at 0.5 A out | SOT-563, **no thermal pad** — the GND pad and the output node *are* the heatsink. Spread copper on both |
| **`U5` MAX98357A** | ≈ 0.08 W at 0.68 W peak out, η 90 % | comfortable; ≥ 2 GND vias at the pad |
| **`U9` ST25R3916** | field-on PA dissipation | QFN-32 exposed pad → In1 with **≥ 4 vias**. This also stabilises the front end's ground reference |
| **`Q2` / `Q3` NTMD4820N** | ≈ 0.11–0.14 W total at 1.5 A | drain and source pads are the spreaders; keep the copper at the FETs |
| **`U17` TPS61169** | ≈ 0.08 W | modest; the switch-node area must stay **small**, so spread on the GND pad, not on `BL_SW` |
| **`R75` 15 mΩ 1 W 1206** | 34 mW at 1.5 A | 29× margin. No action |
| **`F1` 5 A one-shot** | negligible below trip | no action |
| **The 116.7 mm high-current path** | **+0.13 W at 1.5 A / +0.18 W at 1.75 A** | this is board dissipation created purely by PM-2's dispersal, and it lands on top of **B-34**'s ≈ 0.70 W. PM-2 gives most of it back |

**Battery interaction, stated plainly:** the enclosure is sealed and unvented. `U11` and `U18`
sit on B.Cu inside `BATTERY_SHADOW`, in contact proximity with a LiPo pouch whose charge window
is 0–45 °C, and `U11` dissipates its worst-case power **while charging that cell**. PT-1 is the
recommendation; B-34 is the open blocker it composes with. **No thermal path in this design may
depend on the battery.**

---

## 17. Escape-relief doctrine — carried forward, unchanged, and NOT yet instantiated

The 17 E6 rule areas are retired (R4) because their measurements belong to a different board.
**The doctrine that produced them is CTO standing law and survives intact.** When routing
discovers a pad that cannot be escaped at its class width or clearance:

1. **One rule area per pad**, named for that pad, created only when a **measured** need appears.
   Never a generic relaxation, never a netclass change.
2. **`enclosedByArea()`, never `intersectsArea()`.** KiCad evaluates area membership per *object*,
   so a track that merely clips a relaxed area would inherit the relaxation along its **whole
   length**. Every relief neck is written as its **own short segment**, split at the boundary.
3. **Own-area sufficiency.** Each neck must be enclosed by the area named for **its own** pad, on
   its own. Incidental coverage by a neighbouring area is permitted; **depending** on one is not.
4. **Separate the two caps — they measure different things.**
   *Reduced-**clearance** run:* **2.0 mm HARD cap.*
   *Total narrow-**width** run:* **6.0 mm REVIEW trigger** — a new ruling, not an automatic stop.
5. **Narrow-escape search doctrine.** Every sub-class-width object on the board, **including
   another pad's relief neck**, is an **obstacle, never a source**. Only ≥ 0.40 mm-class copper —
   a pad, a via, or a full-width track — may terminate a narrow escape. Same-net contact with
   another pad's neck is a **narrow-to-narrow merge and is forbidden however clean DRC looks**.
6. **Widen immediately** after escaping: ≥ 0.30 mm, preferably 0.60 mm. Single-pad feed only; no
   aggregate current; no transit.
7. **End-cap margin.** KiCad extends a track cap by width/2 past the endpoint, so a 0.15 mm neck
   needs ≥ 0.075 mm of overhang or `enclosedByArea()` fails. Overhang every `*_WIDTH` rectangle by
   **0.150 mm**.
8. **Precedence.** Relief rules go **last** in `.kicad_dru`. KiCad applies the **last** matching
   rule; moving them earlier silently disables them. The existing precedence tail comment in the
   file is load-bearing and was verified empirically on Beta-DM.

> **First instantiation — AQROOT Demo, D-606 (2026-09-04).** The doctrine above is unchanged and
> still un-instantiated on the *production* board. It was spent for the first time on the **Demo**
> PCB, where seven pour lands were opened by seven per-pad `PAD_ESCAPE_<REF>_<PIN>` areas licensing
> the 0.35/0.20 mm barrel only — no width and no clearance relief, so caps 4 and 5 never engaged.
> Two lessons transfer: (a) separate the levers when measuring, because the barrel and the width
> answer different questions and only one of them was the wall; (b) a licensed barrel that is
> **legal** is not yet one that **connects** — whether a stitch closed its land is answerable only
> after KiCad's refill, so it is a gate clause on the refilled candidate's ledger and never a
> check inside the proposer. See `CTO_DECISIONS.md` D-606.

> **Clause 4's width REVIEW TRIGGER, exercised for the first time — AQROOT Demo, D-609
> (2026-09-04).** `U12` is the `TPS63020` and pins 4/5 are its `VOUT`; at the P3V3 0.400 mm
> floor neither pin has a legal escape and at 0.250 mm neither reaches a barrel, so the bond
> that connects the 3.3 V rail to its own regulator exists only at **0.200 mm** — the width
> the board's own `Pad-escape necking - width, fine-pitch power packages` rule already grants
> inside `U12`'s courtyard. Two parallel bonds of 2.928 mm and 4.157 mm total 7.085 mm and
> trip the 6.0 mm trigger. **The ruling, on IPC-2221B at this board's own copper (1 oz outer,
> ΔT = 10 K, the method that reproduces §5's own table): one 0.200 mm neck carries 0.745 A,
> two in parallel 1.489 A, against a 1.0 A design current and a 0.64 A measured peak — SOUND
> AT TWO PARALLEL NECKS, THIN AT ONE.** Clause 6's "widen immediately" cannot be met here and
> is answered by redundancy instead of by width; the production answer is a placement change
> (`L1` sits 0.41 mm off `U12`'s courtyard and boxes the `VOUT` row in), recorded as a Full
> Beta v2 item. Clause 2 was also measured rather than assumed: of eight tracks the run laid,
> **zero** were wholly inside a named courtyard, two merely intersected one — and KiCad
> licensed exactly those two and flagged the other six. `intersectsCourtyard` is not a licence
> a relief may lean on, and now there is a board measurement saying so. See
> `CTO_DECISIONS.md` D-609.

> **The doctrine spent on WIDTH for the first time, and clause 4's ruling REMADE — AQROOT Demo,
> D-610 (2026-09-04).** D-606 instantiated clause 1 on the BARREL; this is clause 1 on the
> **width**, and the reason it had to exist is D-609's own measurement, now recorded as a board
> fact: an `intersectsCourtyard` rule is not a licence a relief may lean on, because KiCad
> licensed the two tracks that intersected `U12`'s courtyard and flagged the six that did not.
> `.kicad_dru` section 13 grants `+3V3` a 0.200 mm track inside **one** area,
> `PAD_ESCAPE_RUN_U12_4`, and all seven tracks of the promoted `VOUT` bond are `enclosedByArea`
> -licensed by it — clause 3's own-area sufficiency proved per track and per area, never against
> a union.
>
> **Clause 7's overhang is load-bearing and is now instrumented.** The rectangle is the run's own
> narrow-copper bounding box grown by 0.150 mm on every side, and it is **DECLARED IN A TRACKED
> SPEC BEFORE THE ROUTER RUNS** (`evidence/d610-relief-run-areas.json`) rather than drawn around
> whatever the router laid. A barrel is a point and may have its area sized from it; a run has an
> EXTENT, and an area sized from the run is a licence whose size the router chooses.
>
> **Clause 4's electrical ruling is REMADE, because its premise was a measurement artefact.**
> D-609 ruled the bond "sound at two parallel necks, thin at one" and required both. It could see
> two necks only because the pour-bond guard was letting a barrel sit inside the `BQ25185_SYS`
> `U12.1` bond tube — three defects, all measured and fixed in D-610. With the guard correct,
> exactly ONE neck exists: `U12.5` is `NO_BODY_VIA_SITE` at every rung of the width ladder
> crossed with every rung of the barrel ladder. **The ruling is therefore that ONE neck is
> promoted, knowingly derated:** 0.742 A at ΔT = 10 K against a 0.64 A measured peak (16 % margin)
> and a 1.0 A design figure that is a rail-WIDTH convention, not a load; 2.756 mm of narrow run,
> so clause 4's 6.0 mm REVIEW TRIGGER does not engage at all. `audit_bond_ampacity.py` re-derives
> §5's own printed table to within 0.9 % before ruling, and reports the barrel at 1.457 A — not
> the bottleneck. The alternative was a 3.3 V rail with no connection to the regulator that makes
> it; D-607 took the same trade at 0.150 mm on `GND` and said so. Clause 6's "widen immediately"
> still cannot be met here: the production answer remains the `L1` placement change, a Full Beta
> v2 item. See `CTO_DECISIONS.md` D-610.

---

## 18. Opportunity and simplification scan

**Surfaced, not decided. No feature was added.**

| # | question | finding |
|---|---|---|
| **A** | Can a tiny placement nudge remove a major via field? | **No — but three non-tiny ones remove far more than a via field.** PM-1, PM-2 and PM-3 each remove a class of defect that no via count would express. There is no small nudge with a large payoff on this board |
| **B** | Can one ground strategy replace unnecessary split-ground complexity? | **Already done, and it is now enforced rather than assumed.** One solid In1, no analog island, one authorised void. The temptation PM-1 creates — cutting ground to contain a 45.9 mm switch node — is explicitly refused |
| **C** | Can an existing component family simplify routing? | **Yes, and it already has.** `TPS61023` is shared between the NFC fallback and the accessory boost with identical passives (D-088), `TPS22950C` is one MPN on both rails, `PCAL9535A` is one MPN on all three expanders. Nothing further to consolidate |
| **D** | Are test points blocking critical escape channels? | **No.** 24 test points were checked against the four constrained regions — the `J5` inter-row channel, the `U9` front end, the `J1` pad field and the `U11`/`U18` corner. `TP37`/`TP38` are *inside* the NFC front end by design and must stay symmetric (§10). No test point sits in the `J5` channel |
| **E** | Are any DNP fallback components placed so badly they cannot be reworked? | **Three need protecting at routing time, none is broken today.** `R112` (display SDO isolation), `C81`/`C82` (Class-D EMI caps), `R123` (IR trim) and `R107` (NFC 5 V branch) are all DNP sites whose whole value is that they can be fitted later. **Rule for routing: no pour floods a DNP pad, nothing is placed over one on the opposite face, and no track is routed within 0.5 mm of one on the tool side** |
| **F** | Is a cable or connector route forcing an electrical compromise? | **No.** The 915 coax is fully shielded and carries no board current; the 433 lead is 44 mm of a 100 mm budget; the NFC pair is 41.7 mm of 75 mm. **The speaker lead remains 152 mm for a 29.3 mm run** — carried forward unchanged as **P2-O4**, an assembly-cost item, not an electrical one |
| **G** | Is any netclass over-engineered? | **One was under-engineered and four were fictional** — see §2.3. After this task **57 of 224 nets are classified and 167 sit on Default, which is correct**: 167 ordinary GPIO, control, status and single-pad nets have no constraint and must not be given one. **No class carries a constraint that cannot be justified from current, edge rate or a manufacturer requirement** |

---

## 19. First-route checklist

Run before the first track and again before the first pour.

- [ ] **PM-1, PM-2, PM-3 ruled on by the CTO.** Routing does not begin otherwise
- [ ] `python hardware/beta-v2/checks/dru_probe.py` → **PASS**
- [ ] `python hardware/beta-v2/checks/netclass_probe.py` → **PASS**
- [ ] `python hardware/beta-v2/checks/p1_regression.py` → **PASS**
- [ ] `python hardware/beta-v2/checks/fork_equivalence.py` → **PASS** (Beta-DM untouched)
- [ ] `kicad-cli sch erc` → **0 errors**
- [ ] `kicad-cli pcb drc` → baseline **26**, and every new violation attributable to the track just drawn
- [ ] Board outline still **70.000 × 148.000 mm**; placement collisions still **0**
- [ ] In1 carries **no** non-GND track (rule catches it; check it anyway)
- [ ] Every layer change on a `BAT_MAIN` / `SYS_MAIN` / `P3V3` / `ACC_*` net uses **≥ 2** POWER vias
- [ ] USB pair: **0 vias**, F.Cu only, In1 solid beneath, no stub
- [ ] NFC arms: **0 vias**, B.Cu only, arm lengths equal within **1 mm**
- [ ] Every switch node **≤ 5 mm** and ≥ 0.50 mm from I2C / USB / NFC
- [ ] Every feedback node **≤ 5 mm**, no via, not beside its switch node
- [ ] I2C internal: estimated `C_bus` recorded and **≤ 161 pF**, or the 100 kHz fallback recorded
- [ ] No pour, track or via within 0.5 mm of a DNP rework site (§18 E)
- [ ] No stitching via inside any antenna, acoustic or boss keepout
- [ ] Pours created **last**, after 17a return vias, never before

---

## 20. Entry-gate result against §25

| criterion | verdict |
|---|---|
| 2-M2 + rails/ribs retention ruling recorded | **PASS** — D-232 |
| `.kicad_dru` stale E5/E6 issue closed | **PASS** — and it was larger than recorded; 39 areas, 22 rules |
| All custom rules reference current objects/nets | **PASS** — `dru_probe.py`, 64 rules, 0 missing, 0 dead patterns |
| Stackup / layer strategy locked | **PASS**, with **P2-O6** recorded (no stackup object in the board file) |
| Ground strategy locked | **PASS** |
| Netclass table complete | **PASS** — 19 classes, `FBV2_P2_NETCLASS_LEDGER.csv` |
| Power-routing strategy complete | **PASS** as a *strategy*; **its execution is blocked by PM-1 and PM-2** |
| USB rule complete or explicitly stackup-gated | **PASS** — complete, and explicitly stackup-gated |
| NFC routing rule complete | **PASS** as a *rule*; **execution blocked by PM-3** |
| Community escape feasibility confirmed | **PASS** — 10 crossings needed, 22 available on one layer |
| **No electrically required placement move remains** | **FAIL — PM-1, PM-2, PM-3** |
| No P2 entry blocker remains | **FAIL** — the three above |
| Zero signal routing performed | **PASS** |

**FBV2-P2 entry gate: FAIL.** Eleven of thirteen criteria pass. The two that fail are the same
fact stated twice, and it is the fact this gate exists to find.
