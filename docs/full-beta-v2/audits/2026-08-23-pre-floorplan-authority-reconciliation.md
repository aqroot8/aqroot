# FBV2-MECH-002 — pre-floorplan authority reconciliation and final procurement sign-offs

**Date:** 2026-08-23
**Task:** FBV2-MECH-002
**Gate:** none. **This task earns NO progress.** Full Beta v2 remains **68 %**; **FBV2-S2 = PASS** is unchanged.
**Starting SHA:** `75fdad5d04f2cf5fa70ecef8e7a8d8fa66485909` — matches the expected HEAD.
**Scope:** two CTO-approved procurement substitutions, one assembly-routing re-run, a full
contradiction sweep of the authoritative mechanical specification, and a compact P1 handoff.
**The PCB was not opened, not edited and not regenerated.**

---

## 0. Preflight

| check | result |
|---|---|
| `git status` | clean except two **untracked** paths, both pre-existing and unrelated (see below) |
| local `master` | `75fdad5` |
| `origin/master` | `75fdad5` — **in sync, no divergence** |
| staged changes | none |
| uncommitted tracked changes | none |
| local-only commits | none |
| prior work needing recovery | **none was lost.** Two untracked artefacts were found and **left exactly as they were**: `hardware/beta-dm/fab/AQROOT-Beta-DM-Gerbers-aa64c16.zip` (a generated fab archive) and `hardware/beta/mechanical/` (nine Phase-1 FreeCAD/STEP reference files, dated 2026-08-15). **`hardware/beta/` is the FROZEN Beta tree and this task had no authority to add it to version control**, so nothing was staged. Flagged for a task that owns that tree. |

**Recorded starting SHA: `75fdad5`.**

---

## 1. F1 — Littelfuse `0466005.NR` → `0466005.NRHF`

**APPROVED BY THE CTO. ADOPTED. D-210.**

### 1.1 Live verification (D-096), 2026-08-23

Read live from the JLCPCB parts API (`selectSmtComponentList`):

| LCSC | MPN | manufacturer | package | spec | JLC class | stock |
|---|---|---|---|---|---|---|
| **`C57525`** | **`0466005.NRHF`** | Littelfuse | **1206** | −55…+90 °C, **32 V / 32 V**, **50 A** interrupting, **5 A**, surface-mount fuse, disposable | **EXTENDED** | **29,328** |
| `C187597` | `0466005.NR` | Littelfuse | 1206 | *character-for-character identical spec string* | EXTENDED | **0** |

**The two LCSC records carry the same electrical specification string.** That is the substantive
finding: the distributor's own parametric data does not distinguish them electrically at all. The
difference is the **`HF` halogen-free ordering option** on the same Littelfuse **466 / Nano2**
family — a materials-declaration variant, not a different fuse.

### 1.2 What changed and what did not

| item | before | after |
|---|---|---|
| MPN | `0466005.NR` | **`0466005.NRHF`** |
| LCSC | `C187597` (stock 0) | **`C57525`** (stock 29,328) |
| Manufacturer | Littelfuse | Littelfuse *(unchanged)* |
| Footprint | `Fuse:Fuse_1206_3216Metric` | **unchanged** |
| Value / rating | 5 A one-shot 1206 | **unchanged** |
| Connectivity | `BAT_CONNECTOR_P` ↔ `BAT_RAW` | **unchanged — not one net, pin or wire touched** |
| Assembly route | **class C — consign** | **class B — JLC-sourced, machine-placed** |

**This is a procurement / order-code improvement, not an electrical redesign.** `F1` remains the
catastrophic/harness backstop that FBV2-PWR-002 specified; the PTC rejection stands.

---

## 2. D10 / D11 / D12 — Nexperia `BAT54WS,115` → Diodes Inc `BAT54WS-7-F`

**APPROVED BY THE CTO. ADOPTED. D-211.**

### 2.1 The "series pair" claim was wrong, and it was wrong in the schematic too

The prior sourcing note — written at FBV2-S2-002, carried in
`FIRST_FIVE_ASSEMBLY_PLAN.md` §5 and §8, in `CHANGELOG.md`, in `PROGRESS.md`, in **D-206**, and
**inside the `D10`/`D11`/`D12` symbols themselves** — asserted:

> *"`BAT54W` is a single diode; `BAT54WS` is a series pair. Different device."*

**That is false.** Three independent lines of evidence, all checked in this task:

1. **The package cannot hold a pair.** `BAT54WS` is a **SOD-323** part. SOD-323 is a
   **two-terminal** package. A series pair needs three terminals.
2. **The distributor library agrees, unanimously.** Every `BAT54WS` in the LCSC library, from
   **eight different manufacturers**, is catalogued as **"1 Independent"** in SOD-323 — Diodes Inc
   `C124205`, Changjing `C22629`, Starsea `C168799`, Hottech `C191198`, PANJIT `C304155`,
   AnBon `C397611`, and Diodes Inc's own `BAT54WSQ-7-F` `C171824`. There is no series-pair
   `BAT54WS` anywhere in the library to substitute *for*.
3. **AQROOT's own schematic never used a pair.** `D10`, `D11` and `D12` are each one
   **`Device:D_Schottky`** symbol with exactly **two pins**, on **`Diode_SMD:D_SOD-323`**, a
   two-pad footprint. `D10` and `D11` form the ratiometric bridge as **two separate components**,
   not as two halves of one package.

**So the architecture was always three independent diodes, and `BAT54WS-7-F` matches it exactly.**
The error was confined to documentation and to a sourcing note; **no circuit was ever wrong**.

### 2.2 The real rejection criterion — and why `BAT54W,115` is still correctly rejected

The old note rejected Nexperia **`BAT54W,115`** (`C8657`) for the wrong reason. The live record
gives the right one:

> `C8657` · `BAT54W,115` · Nexperia · **`SOT-323(SC-70)`** · 1 Independent · 200 mA · 30 V · stock **5**

**`BAT54W` is also a single independent diode.** It is rejected because it is a **SOT-323 (SC-70)**
part — a **footprint mismatch** against `Diode_SMD:D_SOD-323` — and because it has **5 in stock**
against a need of 15. **Diode count was never the issue.**

**The standing criterion for any `D10`–`D12` alternate is now recorded as:**

1. **single independent diode** (not a pair, not a common-cathode dual);
2. **SOD-323** land pattern;
3. adequate **V_F / leakage / current**;
4. **matched type** across `D10` and `D11` — same MPN, ideally same reel;
5. **live sourcing** under D-096.

### 2.3 Live verification (D-096), 2026-08-23

| LCSC | MPN | manufacturer | package | electrical | JLC class | stock |
|---|---|---|---|---|---|---|
| **`C124205`** | **`BAT54WS-7-F`** | **Diodes Incorporated** | **SOD-323** | **1 Independent**, **30 V**, **100 mA** continuous, **600 mA** surge, **V_F 1 V max @ 100 mA**, **I_R 2 µA @ 25 V** | **EXTENDED** | **46,819** |

### 2.4 Electrical verification — `D10`/`D11` ratiometric bridge

Captured topology (`01_POWER_TREE`, unchanged by this task):

```
USB_VBUS_CHG ──┬── D10 ── VBRIDGE_TOP ── R85 2.2M ──┬── N_POL   ── U19.3 [INA+]
               │                          R86 2.2M ──┘  (to BAT_RAW)
               └── D11 ── VREF_TOP    ── R87 2.2M ──┬── REF_POL ── U19.2 [INA−]
                                          R88 2.2M ──┘  (to GND)
```

| check | result | verdict |
|---|---|---|
| **Forward bias current** | each leg is **2.2 M + 2.2 M = 4.4 MΩ** across ≈ 5 V → **≈ 1.1 µA**. Both diodes operate **six orders of magnitude below** the 100 mA rating | **PASS — enormous margin** |
| **Absolute V_F is not the design parameter** | `INA+ − INA− = (BAT_RAW + V_F11 − V_F10) / 2`. The **absolute drop cancels**; only the **mismatch ΔV_F** survives, and the trip point is `BAT_RAW > ΔV_F` | **PASS — the comparison is supply- and V_F-independent by construction** |
| **Matching** | `D10` and `D11` become the **same MPN from the same manufacturer**, bought on one line. That is **better** matching than the previous state, where the part was not in the library at all and would have been consigned from an unspecified source | **PASS — improved** |
| **Signal being distinguished** | reversed or absent pack drives `BAT_RAW` **volts** away from zero; a same-type ΔV_F at 1 µA is **tens of millivolts**. Margin is ~2 orders of magnitude | **PASS** |
| **Reverse blocking, USB absent** | pack drain path is `BAT_RAW → R86 → R85 → D10(reverse) → VBUS`. **The 4.4 MΩ dominates**: drain is capped at **≤ ~1 µA ≈ 8.8 mAh/year** on a 2500 mAh pack, regardless of which of the two diodes is fitted. Reverse stress ≈ 4.2 V against **30 V V_RRM** — **7× margin** | **PASS** |
| **Leakage symmetry** | `I_R` 2 µA @ 25 V applies **identically to `D10` and `D11`**, so it does not skew the ratiometric comparison | **PASS** |
| **Comparator common mode** | `INA±` sit at ≈ 2.4 V with `U19` `TLV7032` powered from `VREC_VCC` ≈ 5 V — rail-to-rail input, well inside range | **PASS (unchanged)** |

### 2.5 Electrical verification — `D12` dead-cell recovery branch

Captured path: `Q5` [S] on `USB_VBUS_CHG`, [D] → `REC_LIM_IN` → **`R95` 560 Ω** → `REC_DIODE_IN`
→ **`D12`** → `BAT_RAW`.

| check | figure | rating | margin | verdict |
|---|---|---|---|---|
| **Recovery current, nominal** | **8.36 mA** at VBUS 5.0 V into a 0 V pack (D-105) | 100 mA continuous | **12×** | **PASS** |
| **Recovery current over 4.75–5.25 V** | **7.93 – 8.80 mA** (D-105) | 100 mA | **11×** | **PASS** |
| **D-105 recomputed with the Diodes V_F** | D-105's 8.36 mA implies **V_F ≈ 0.32 V** at ~8 mA, which is exactly where a SOD-323 BAT54-class Schottky sits. Worst-case sweep at V_F 0.25–0.50 V and VBUS 4.75–5.25 V gives **≈ 7.9 – 8.9 mA** — **still inside the accepted 5–10 mA band.** **D-105 needs no revision** | 5–10 mA band | — | **PASS** |
| **Single-fault ceiling (B-27, as amended)** | **≈ 15.9 mA nominal / ≈ 16.6 mA worst case** | **100 mA continuous** | **6×** | **PASS** |
| **Surge headroom** | 16.6 mA worst case | **600 mA** non-repetitive | **36×** | **PASS** |
| **Reverse blocking (unidirectional injection)** | pack at ≤ 4.2 V reverse across `D12` when USB is absent | **30 V V_RRM** | **7×** | **PASS** |
| **Dissipation** | ≈ 16.6 mA × ~0.4 V ≈ **7 mW** | SOD-323 class ~200 mW | **~28×** | **PASS** |
| **Package / inspectability policy** | SOD-323 remains **leaded and inspectable**; no BGA, WLCSP or bottom-terminated part enters the safety-critical branch | — | — | **PASS (unchanged)** |

### 2.6 Verdict

**NO MATERIAL ELECTRICAL MISMATCH WAS FOUND. `BAT54WS-7-F` IS LOCKED for `D10`, `D11` and `D12`.**
The substitution was not stopped. Every margin above is **wider** than the branch requires, the
ratiometric comparison is **structurally** insensitive to the parameter that changed, and the
matching situation is **improved** rather than degraded.

---

## 3. Assembly routing re-run

The JLC classification for both part numbers was **re-read live**, not assumed.

| ref | MPN | LCSC | JLC library class (live) | stock | need | old route | **new route** |
|---|---|---|---|---|---|---|---|
| `F1` | `0466005.NRHF` | `C57525` | **EXTENDED** | 29,328 | 5 | **C — consign** | **B — JLC-sourced, machine-placed** |
| `D10`–`D12` | `BAT54WS-7-F` | `C124205` | **EXTENDED** | 46,819 | 15 | **D — not in the library, consign** | **B — JLC-sourced, machine-placed** |

**Neither is JLC Basic.** Both are Extended, which is a placement-fee question, not an assembly-route
question — Extended parts are machine-placed from JLC stock.

### 3.1 Consignment / manual burden

| metric | before | after | direction |
|---|---|---|---|
| **Consigned part numbers** | **11** (10 class C + 1 class D) | **9** (9 class C + 0 class D) | **↓ 2** |
| Class D — "not in the LCSC/JLC library at all" | **1** | **0** | **class D is now EMPTY** |
| Consigned placements per board | 12 (`F1` ×1 + `D10`–`D12` ×3 + others) | **8** | **↓ 4 per board, ↓ 20 across the first five** |
| **Hand-soldered parts per board** | **2** (`J5`, `D1`) | **2** (`J5`, `D1`) | unchanged |
| Fine-pitch / QFN hand-placed | **0** | **0** | unchanged |

**The burden decreased, as expected. No part moved toward manual assembly.**

---

## 4. Mechanical authority reconciliation

`MECHANICAL_INTERFACE_SPEC.md` was read in full (575 lines) against `CTO_DECISIONS.md`, the FBV2-S1
closeouts, FBV2-S2-001, FBV2-S2-002 and the current exact parts.

### 4.1 NFC zone — CORRECTED

| location | was | now |
|---|---|---|
| dimension authority table, row 9 | **45 × 45 mm, TARGET** | **48 × 48 mm minimum clear region, LOCKED** (D-127/D-128/D-131) |
| §6.1 rear-view diagram | `45 × 45 mm` | `48 × 48 mm` |
| §6.2 rules, "NFC loop envelope" | **45 × 45 mm, TARGET** | **48 × 48 mm, LOCKED**, with `~~45 × 45~~` struck |
| §6.2 rules, "Stored antenna" margin | "*a 45 mm loop … ~15 mm of margin each side*" | "*a 48 mm clear zone … **~13.5 mm** of margin each side*" |
| machine-readable block | `FBV2_NFC_ZONE_MM: 45 x 45  TARGET` | `FBV2_NFC_ZONE_MM: 48 x 48  LOCKED` |

The **48 × 48 mm** figure was ruled at **FBV2-S1-004B** and already appeared in this document's own
NFC reservation banner. **Four places had never been updated to match it**, including the
machine-readable block a guard script would parse. No later CTO ruling supersedes 48 × 48.
**The external enclosure was not altered** — this is a keepout inside the existing cavity.

### 4.2 Display connector — CORRECTED

Removed as **current** truth, retained only where clearly superseded:

- ~~"Laid out on the **FH12 / FH52E standard land pattern**"~~
- ~~"second source `FH52E-50S-0.5SH` (LCSC C7465440)"~~
- ~~"Mating proven from both manufacturers' drawings"~~

**Current truth now stated in row 21 and in the machine-readable block:**

| statement | value |
|---|---|
| Land pattern | **dedicated FH69 pattern** |
| `FH52E-50S-0.5SH` | **NOT a drop-in, NOT a second source** — FH69 and FH52E **do not share a land pattern** (B-47 → **D-194, NOT COMPATIBLE**) |
| Architecture | **single-source connector** |
| Assembly | **genuine Hirose `FH69-50S-0.5SH` is JLC machine-placeable** — 1,072 in stock live 2026-08-23 |
| Ordering | **re-check stock before the order** |

The FBV2-S1-003 capture note further up the document already said the FH52E/FH12 migration was
**not performed**; it was correct and was left untouched as history.

### 4.3 `J1` assembly route — CORRECTED

**M-13** and the document header both said `J1` was **manual / secondary assembly**. That came from
FBV2-S2-001 and was **superseded the same day** by **D-206 / D-207**.

**Current truth: exactly TWO parts are manual per board — `J5` and `D1`. `J1` is MACHINE-PLACED.**
B-47 / D-194 is untouched and remains correct: it says there is **no drop-in second source**, which
was never a statement about whether JLC can place the genuine part.

§5's conditional *"if the JLC service cannot place this through-hole part automatically…"* about
`J5` was also resolved to current truth: **it cannot, and `J5` is class E.**

### 4.4 915 MHz SMA ↔ IR spacing — TRACED, BOTH RULES RETAINED

**This was investigated rather than resolved by preference, and the outcome is that neither figure
was stale.**

| rule | datum | first stated | latest restatement |
|---|---|---|---|
| **≥ 15 mm** | **centre-to-centre**, bulkhead hole ↔ IR window | **FBV2-MECH-001**, 2026-08-22 — §8 and row 12, written against a *generic* fitted whip shadowing the emitter cone | **M-13**, FBV2-S2-001, 2026-08-23 |
| **≥ 8 mm** | **edge-to-edge**, SMA **body** ↔ IR **aperture** | **D-120**, FBV2-S1-004, 2026-08-23, with B-52 opened | **M-13**, FBV2-S2-001, 2026-08-23 |

**Finding: the 8 mm rule did NOT supersede the 15 mm rule.** The most recent ruling to touch this —
**M-13**, written *after* D-120 and *with the Amphenol `095-902-568-150` bulkhead already selected* —
**states both in the same sentence**. The 15 mm figure was therefore **re-asserted after** the 8 mm
rule existed, which is the opposite of stale.

**The actual defect was that neither figure said what it was measured between.** Both now carry an
explicit datum, in row 12, in §8, and in a new **§8.1 authority trace** with a consistency check:
on a ~9.5–11 mm SMA hex body and a ~Ø5.5–6.0 mm IR aperture, **8 mm edge-to-edge implies ≈ 15.5–16.5 mm
centre-to-centre**, so the two are mutually consistent and **8 mm edge-to-edge is the binding one**.

**The Amphenol body OD was NOT measured** — it is marked **CAD-TO-VERIFY**, and the recorded rule is
**satisfy whichever is larger**. **B-52 stays OPEN. No CAD was created.**

### 4.5 Other stale mechanical truth found in the §5D sweep

| topic | finding | action |
|---|---|---|
| **20-pin vs 24-pin** | §4.1 reason 2 still justified re-floorplanning partly by *"changes the connector from **26 to 20 pins**"*. The port is **24 contacts, 2 × 12 at 2.54 mm** (D-081/D-083) | **CORRECTED**, old figure marked SUPERSEDED |
| **RGB** | the same sentence said Full Beta v2 *"removes HOME **and the RGB nets**"*. A **front RGB status light `D13` was ADDED** (D-167, FBV2-S1-008) and has its own open item M-11 | **CORRECTED**, old reading marked SUPERSEDED |
| **Speaker thickness** | row 10 locks **Ø20 × 3.0 mm** and states the lock *"releases 1 mm of Z in the speaker column"* — but **§3.3 Column C still summed 4.0 mm**, giving 13.6 mm. A locked value contradicted by a derived table in the same document | **CORRECTED** → **3.0 mm**, column total **12.6 mm, 10.4 mm spare** |
| **IR receiver naming** | §2.1 height census read *"TSOP38238 / TSOP38438"* and §8 said *"The **TSOP38438** is extremely sensitive"*, as if the fallback were the fitted part. **`TSOP38238` is locked (D-160); `TSOP38438` is the same-package fallback (D-163)** | **CORRECTED** — primary named first, fallback in parentheses |
| **Microphone acoustic port face** | §7.1 and §9 put the aperture on the **FRONT enclosure face**; **M-14** says the path leaves the **PCB's BOTTOM face**. Both are true only if `MK1` sits on the copper face pointing away from the front shell — **and no floorplan has assigned that side** | **DATUM CLARIFIED** in §7.1 and **RAISED AS O-1** for CTO ruling |
| **Harwin vs Samtec** | row 11, §5, §5.1 and M-03 already record **Samtec `BCS-112-S-D-HE` LOCKED** and **Harwin `M20-7881242` REJECTED as obsolete**, consistently | **no contradiction — no change** |
| **Display dimensions / FPC** | rows 8, 19, 20, §2 and the machine-readable block are consistent at **56.54 × 84.96 × 3.95 ± 0.25 mm**, active **48.96 × 73.44**, one **50-pin 0.5 mm bottom-contact** tail | **no contradiction — no change** |
| **NFC `.A.dg` vs `.B.dg`** | the only `.A.dg` mention is the banner explaining **why the `.B.dg` was chosen**. Correct as history | **no change** |
| **433 antenna placement** | **LEFT / LOWER-SIDE, adhesive to a plastic wall, never on the PCB**, `U7` IPEX service-accessible — consistent throughout | **no contradiction**, but see **O-6** |
| **915 pigtail** | one orderable assembly, **150 mm**, right-angle AMC plug, Ø6.5 mm panel hole — consistent | **no contradiction**, but see **O-5** |
| **Buttons / HOME** | *"REMOVED and not to reappear: HOME, Volume Up, Volume Down"* is consistent with the six-switch front set | **no change** |
| **Battery** | **60 × 75 × 8.0 mm LOCKED (D-071)**, ≤ 1.2 mm under the battery, SKU deliberately TBD (M-04) — consistent | **no contradiction**, but see **O-2** |
| **PCB target / max** | **72.0 × 152.0 max**, **70.0 × 148.0 target**, 1.6 mm, **Beta-DM 74 × 155 does not fit** — consistent | **no change** |
| **Community aperture / load path** | 34 × 10 mm aperture, ≥ 1.5 mm recess, upper-edge asymmetric key, ends closed to ≤ 0.3 mm, **≈ 33 N** carried by an enclosure boss/rib (M-10) — consistent | **no change** |

### 4.6 Machine-readable block

Added or corrected so a guard script reads current truth:

```
FBV2_DISPLAY_CONN_LAND:  FH69 DEDICATED - not FH12/FH52E   LOCKED (D-194)
FBV2_DISPLAY_CONN_2ND:   NONE - single source              LOCKED (D-194)
FBV2_DISPLAY_CONN_ASSY:  MACHINE-PLACED at JLC             LOCKED (D-206/D-207)
FBV2_NFC_ZONE_MM:        48 x 48                           LOCKED (D-127/D-128/D-131)
FBV2_SMA_IR_CENTRE_MM:   15.0 min c-c                      LOCKED (FBV2-MECH-001, restated M-13)
FBV2_SMA_IR_EDGE_MM:      8.0 min edge                     LOCKED (D-120, restated M-13)
FBV2_SPEAKER_Z_COLUMN:   12.6 of 23.0 (10.4 spare)         TARGET
FBV2_MANUAL_ASSY_REFS:   J5, D1                            LOCKED (D-206/D-207)
```

---

## 5. P1 floorplan input table

Created: [`../mechanical/P1_FLOORPLAN_INPUTS.md`](../mechanical/P1_FLOORPLAN_INPUTS.md)

**120 numbered constraints** across enclosure, PCB, front, bottom, right, top, rear, internal RF,
cables and bosses, each marked **LOCKED / TARGET / CAD-TO-VERIFY**, plus the six blocking items in
§6 below. **No coordinate is invented anywhere in it.**

---

## 6. Opportunity and simplification scan — six items for CTO ruling

**Surfaced, not decided. No design change was made for any of them. No feature was added.**

| # | item | the finding |
|---|---|---|
| **O-1** | **Microphone board-face assignment** | Front-face aperture (§7.1, §9) plus a bottom-port part listening through the board (M-14) is satisfiable **only** if `MK1` sits on the copper face pointing away from the front shell. **That side has never been assigned**, and P1 cannot place the part until it is. |
| **O-2** | **The rear face is over-constrained by ≈ 8 mm — impossible simultaneous keepouts** | Rear Y budget: battery **75** + NFC clear zone **48** + speaker **Ø20** + **≥ 20 mm** speaker-to-loop separation = **163 mm** against a **155 mm** cavity. Placing the speaker beside the battery does not help — the 60 mm battery in a 75.0 mm cavity leaves **7.5 mm per side** against a Ø20 driver. This is **before** the 5 mm NFC metal keepout, the shell lip and the bosses. **One of {speaker↔loop separation, speaker location or face, battery Y, NFC zone position} must give**, and all four are currently recorded as binding. |
| **O-3** | **Mid-span boss at Y ≈ 100 vs the grown NFC zone** | The zone grew 45 → 48 mm and carries a 5 mm metal keepout; a boss nominally at Y ≈ 100 now sits on or inside its lower boundary. The zone is **LOCKED**, the boss is **TARGET** — confirm the boss may move to **Y ≤ ~95**. |
| **O-4** | **microSD ↔ USB-C separation is not physically achievable** | Recorded as **"≥ 8 mm centre-to-centre"**. Bodies are ~**14.0** and ~**9.2 mm** wide, so centres cannot be closer than **≈ 11.6 mm**, and a rib between apertures pushes that to **≈ 13.6 mm**. The figure reads as an **edge-to-edge** number written into a centre-to-centre row. |
| **O-5** | **Unnecessary 915 MHz cable length** | `095-902-568-150` is a **150 mm** assembly in a **155 mm** cavity, needing a ≥ 5 mm bend radius and a ≥ 15 mm service loop while **not crossing the IR path**, through space already claimed by the 433 flex, the NFC pair and the battery. A shorter length in the same Amphenol series would remove a routing problem at **no electrical cost** (loss is already ≈ 0.4 dB). **No substitution is proposed** — D-195 locked this MPN and only the CTO may change it. |
| **O-6** | **The internal antenna storage channel cannot hold the locked 915 antenna** | §8 reserves a left-wall channel *"sized for the stowed whip"*. The locked whip is Taoglas **`TI.92.2113`, 198 ± 3.3 mm × Ø13 mm**; the cavity's longest internal diagonal is ≈ **172 mm**. **It does not fit in any orientation.** The same left wall is the **LOCKED** mount region for the 433 MHz flex. **Withdrawing the storage requirement would free the entire left wall** — the largest single simplification available before floorplanning. |

**Checked and found clean:** connector orientation conflicts (`J7` top-entry clearance, `J5`
horizontal entry, `J1` right-angle backflip — all consistent); FPC bend conflicts (6 mm corridor
against ≥ 3 mm needed, 30 mm free tail); antenna cable crossing rules (already explicit); speaker
lead length (152 mm to a rear-lower-right driver is adequate, not excessive).

---

## 7. Validation

| check | baseline | after | verdict |
|---|---|---|---|
| Schematic parses | 9 sheets + root | 9 sheets + root | **PASS** |
| **ERC violations** | **27** | **27** | **ZERO DELTA** |
| **ERC errors** | **0** | **0** | **ZERO DELTA** |
| ERC histogram | 21 `pin_to_pin`, 6 `unconnected_wire_endpoint` | **byte-identical histogram** | **PASS** |
| **Netlist connectivity** | **224 nets, 991 nodes** | **224 nets, 991 nodes** | **IDENTICAL — zero delta** |
| Symbol / pin changes | — | **none** | **PASS** |
| Wire / label / junction / no-connect changes | — | **none — zero such lines appear in the diff** | **PASS** |
| Schematic diff character | — | **PROPERTY-ONLY**: 4 × `Note2`, 4 × `MPN`, 1 × `LCSC` edited, 3 × `Manufacturer` edited, 3 × `LCSC` added | **PASS** |
| BOM regenerates | 140 lines | **140 lines** | **PASS** |
| `F1` BOM row | `0466005.NR` / `C187597` | **`0466005.NRHF` / `C57525` / Littelfuse** | **PASS** |
| `D10`–`D12` BOM row | `BAT54WS,115` / Nexperia / *no LCSC* | **`BAT54WS-7-F` / Diodes Incorporated / `C124205`** | **PASS** |
| `fork_equivalence.py` | PASS | **PASS** | **PASS** |
| `netclass_probe.py` | PASS (6 nets resolve to LED_BOOST) | **PASS** (6 nets) | **PASS** |
| **PCB SHA-256** | `aaa04bfbd5d69c5636da1094104081e2729f2bb7d5e07e7353f1f4eafc86a9f2` | **identical** | **BYTE-IDENTICAL, and still bit-identical to Beta-DM** |

**ERC report stored:** `hardware/beta-v2/reports/FBV2-MECH-002-erc.rpt`

### 7.1 Trees confirmed untouched

| tree | state |
|---|---|
| `hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_pcb` | **untouched, byte-identical** |
| `hardware/beta-dm/` | **untouched** |
| `hardware/beta/` (frozen Beta) | **untouched** |
| `hardware/beta/mechanical/` (mechanical source) | **untouched — read only, still untracked exactly as found** |
| all footprints and symbol libraries | **untouched** |

**The only design file modified in this task is `01_power_tree.kicad_sch`, and only its properties.**

---

## 8. A note on how the "series pair" error survived

It was written once, at FBV2-S2-002, from a **reasonable-sounding inference** — `BAT54S` *is* a
series pair, so `BAT54WS` "must be the SOD-323 version of it". The `S` in `BAT54WS` is a **package
code**, not a topology code.

It then propagated into **six places in one task**: the assembly plan §5 and §8, the changelog, the
progress log, **D-206**, and the schematic symbols. Each copy cited the others. **The design was
never wrong** — the schematic used two-pin symbols on two-pad footprints throughout — which is
precisely why nothing caught it: **the error lived only where nothing is validated by a tool.**

The check that would have caught it in one step is the one this task ran: **read the distributor's
own parametric field.** LCSC prints `1 Independent` on every one of them.

---

## 9. Progress statement

**This task earns NO progress. Full Beta v2 remains 68 %. FBV2-S2 = PASS is unchanged.**
It is a reconciliation and sign-off task, not a design phase. **FBV2-P1 has not begun and the PCB
has not been touched.**
