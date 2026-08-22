# AQROOT Full Beta v2 — Dead-Cell Recovery and Single-Fault Closeout

Date: 2026-08-22
Task: **FBV2-PWR-002**
Repository HEAD at audit: `dda5efe`
Scope: **documentation only.** No KiCad, PCB, firmware, mechanical or fabrication file was created or modified. `hardware/beta-v2/` was not created.

---

## 0. Sources

| # | document | revision | notes |
|---|---|---|---|
| **L1** | ADI **LTC4368** — *100V UV/OV and Reverse Protection Controller with Bidirectional Circuit Breaker* | doc id `4368f` | full PDF, Farnell mirror |
| **C1** | TI **TLV7031/7032/7041/7042/7034/7044** — *Small-Size, Nanopower, Low-Voltage Comparators* | ti.com | full PDF |
| S6 | TI BQ25185 | SLUSF65A | earlier task |
| S9 | TI TPS22950/C/L | SLVSFJ2B | earlier task |
| R1 | Independent review FBV2-CTO2-PWRNFC-001 | advisory | FDS6898A figures cited via R1 |

**MOSFET and fuse candidates below are named from familiarity and from R1, not
from datasheets read in this session.** Every one is marked for verification at
the procurement gate, per §10 of the brief ("do NOT claim them
fabrication-locked yet").

---

## 1. CTO rulings recorded

| ruling | recorded as |
|---|---|
| **A** — Candidate B **SELECTED**: autonomous hardware-qualified dead-cell recovery. Candidate D rejected as the normal architecture | **D-065** |
| **B** — PCAL9535APW,118 **LOCKED** for both `U2` and `U3`; NXP Rev 2 independently verified by the CTO (400 kHz, 25 mA drive, all interrupts masked at POR, mask 4Ah/4Bh, status 4Ch/4Dh, programmable pulls, input latch, all channels inputs at power-up). Do not reopen | **D-066** |
| **C** — GPIO38 + GPIO47 remain **LOCKED**; `SX1262_DIO1` to the internal PCAL9535A; pre-fab confirmation no longer blocks architecture | **D-067** |
| **D** — fuse + Schottky is **not** sufficient proof. New objective: **no single external pass-MOSFET short may cause BQ25185 BAT to exceed its negative absolute maximum** under reversed-battery + USB. **Prefer prevention/isolation over fault-clearing time** | **D-068** |

> **Ruling B closes the four facts this audit could not verify last pass**
> (pull-enable POR state, 400 kHz, output drive, Agile I/O register addresses).
> They are recorded as CTO-verified from NXP Rev 2. The land-pattern audit
> remains a separate pre-fabrication gate.

---

## 2. Candidate B — the exact dead-cell recovery circuit

### 2.1 The constraint that shapes the whole design

A recovery path must distinguish **0 V (dead cell)** from **−3 V to −4.35 V
(reversed cell)**. **No passive or self-biased switch can do this**, and the
reason is structural, not a matter of part selection:

| attempt | dead cell (0 V) | reversed cell (−3.7 V) |
|---|---|---|
| N-FET, source at `BAT_RAW`, gate from a positive rail | V_GS ≈ +3 V → **ON** ✓ | V_GS ≈ +6.7 V → **ON, harder** ✗ |
| P-FET, source at VBUS, gate pulled toward `BAT_RAW` | V_GS ≈ −4.5 V → **ON** ✓ | V_GS ≈ −8.2 V → **ON, harder** ✗ |

Any switch referenced to a positive rail turns on **harder** as the battery node
goes negative. **An active, GND-referenced comparison is therefore mandatory**,
which is exactly what ruling A's "hardware-qualified" requires.

### 2.2 The ratiometric bridge — how 0 V and negative are separated

The sensing network must feed a comparator whose input never goes negative
(comparators do not tolerate below-rail inputs), while still discriminating at
exactly 0 V. A **matched resistive bridge** does both:

```
        VBUS ──[ R_A 1M ]──┬──[ R_B 1M ]── BAT_RAW          X = (VBUS + V_BAT) / 2
                           X

        VBUS ──[ R_C 1M ]──┬──[ R_D 1M ]── GND              REF_POL = VBUS / 2
                        REF_POL
```

Trip condition `X = REF_POL` reduces to **V_BAT = 0, independent of VBUS.**
That supply-independence is the whole point of using a divided reference rather
than a bandgap: an absolute reference would drift against VBUS and reintroduce
supply dependence.

At the extremes (VBUS = 5 V): V_BAT = 0 → X = 2.50 V; V_BAT = −4.35 → X = 0.33 V;
V_BAT = +4.2 → X = 4.60 V. **X is always positive and always inside the
comparator's rail-to-rail common-mode range.** That is the reversed-battery input
protection — it is inherent in the topology, not bolted on.

**Error budget, referred to V_BAT** (×2, since dX/dV_BAT = 0.5):

| source | value (C1) | at V_BAT |
|---|---|---|
| Comparator V_IO | ±8 mV max | ±16 mV |
| Internal hysteresis V_HYS | 2 / 7 / **17 mV** | ±34 mV max |
| Resistor mismatch, 1% parts | ≈0.02 × VBUS at X | **±200 mV** ← dominant |
| Resistor mismatch, 0.1% parts | ≈0.002 × VBUS at X | ±20 mV |

**Recommendation: 0.1% thin-film for R_A–R_D**, and deliberately bias the nominal
threshold to **V_BAT = −0.1 V** by skewing R_C/R_D. Worst case the threshold then
sits between about −0.15 V and −0.05 V, so a 0 V cell **always** recovers and a
reversed cell at −3 V is **never** within 2.8 V of the threshold. 1% resistors are
acceptable if the bias is increased to −0.3 V.

### 2.3 Handoff — provided free by the LTC4368 itself

**L1, FAULT pin:** *"This high voltage open drain output is pulled low if there is
a voltage or current fault, if SHDN is low, or **if VIN has not risen above
VIN(UVLO)**."*

`FAULT` low is *exactly* the dead-cell condition, and it releases the moment the
protection controller takes over. Using it as a third series qualifier means the
handoff is decided by the element that actually knows it has taken over — no
extra comparator, no extra threshold to trim, and no possibility of the recovery
branch and the main path both being active by mistake.

A second comparator channel provides an upper bound so that an **absent** battery
does not leave the branch free-running (§2.6).

### 2.4 Complete circuit

```
                                 VBUS  (USB only — no battery-side standby cost)
                                  │
              ┌───────────────────┼──────────────────┬─────────────┐
              │                   │                  │             │
         [ R_PU 1M ]         TLV7032 VDD        [ R_A 1M ]    [ R_C/R_D ]
              │              (dual, SOT-23-8)        │        REF_POL≈VBUS/2
              │                                      X ──── [ R_B 1M ] ──── BAT_RAW
              ├──────── gate ── Q_REC (P-FET, SOT-23, default OFF)
              │                   │
              │              source = VBUS,  drain ──[ R_LIM 560R ]──▶|── BAT_RAW
              │                                                    D_REC
              │                                                   (Schottky)
              │
              └── pull-down path, a 3-input series AND:
                        │
                   Q_AND_A  ← comparator A output  (HIGH when V_BAT > −0.1 V)
                        │
                   Q_AND_B  ← comparator B output  (HIGH when V_BAT < ~2.8 V)
                        │
                   LTC4368 FAULT   (LOW only while the main path has NOT taken over)
```

`Q_REC` turns on **only** when all three are true. Any one opens → `R_PU` pulls
the gate to VBUS → `Q_REC` off. **Default state is OFF** in every unpowered,
powering-up and undefined condition.

| element | function | recommendation |
|---|---|---|
| **Supply** | VBUS, **not SYS** | With no USB the branch is dead **by construction**, and it costs **zero battery-side standby current**. This is strictly better than supplying from SYS, which is alive on battery too |
| **U_CMP** | dual comparator | **TI TLV7032** — 1.6–6.5 V, **315 nA**, rail-to-rail CM input, internal hysteresis 7 mV typ, **no phase reversal when overdriven**, push-pull, **SOT-23-8 leaded** |
| **Reference** | ratiometric dividers off VBUS | Never a bandgap — see §2.2 |
| **Q_REC** | recovery switch | P-channel, SOT-23. Source at VBUS so the comparator's 0–VBUS swing drives it directly with no level shift |
| **D_REC** | series Schottky, cathode toward `BAT_RAW` | **Two jobs.** (1) Blocks battery→VBUS: without it, a P-FET body diode would drain the pack through `R_LIM` whenever USB is absent. (2) Makes the branch strictly unidirectional under every fault |
| **R_LIM** | recovery current | **560 Ω** → ~8 mA at V_BAT = 0. See §3 |
| **R_PU** | gate pull-up to VBUS | 1 MΩ. Guarantees default OFF |
| **Q_AND_A / Q_AND_B** | series AND | Two small N-FETs (e.g. a dual in SOT-363). Series, so **either one opening disables recovery** |
| **FAULT tie-in** | third qualifier | Zero extra parts — the pull-down path simply terminates at `FAULT` instead of GND |

**Firmware role: observation only.** A `BAT_RAW` divider (≥100 kΩ series plus a
Schottky clamp to GND, so a negative node clamps at −0.3 V at microamps) lets
firmware **report** no-cell / dead-cell / reversed-cell / recovering. **It makes
no safety decision and recovery works with blank or corrupted flash**, as ruling
A requires.

### 2.5 Thresholds

| threshold | nominal | worst case | why |
|---|---|---|---|
| Polarity (comparator A) | **V_BAT = −0.1 V** | −0.15 … −0.05 V with 0.1% parts | Guarantees a 0 V cell recovers; leaves ≥2.8 V of margin to a reversed cell |
| Handoff upper bound (comparator B) | **V_BAT ≈ 2.8 V** | ≈2.66 … 2.94 V over VBUS 4.75–5.25 V | **Above** LTC4368 V_IN(UVLO) max of **2.4 V**, and **below** a healthy cell's 3.0 V floor |
| Hysteresis | 7 mV typ internal (C1) | 17 mV max | Referred to V_BAT: ±34 mV max. Prevents chatter at the polarity threshold |

The handoff window is the load-bearing number: recovery always stops **after** the
LTC4368 can take over and **before** a healthy cell would be trickled. This is
only true because the LTC4368 **UV comparator is left unused** (tied to VIN via
510 kΩ, per FBV2-PWR-001) — using UV at a cell-protection threshold would raise
the takeover point above the handoff point and break the sequence.

### 2.6 Behaviour in every state ruling A asks about

| condition | behaviour |
|---|---|
| **0 V cell, USB present** | Polarity OK, FAULT low, below handoff → **recovery ON at ~8 mA.** Cell rises; at ~2.2 V the LTC4368 closes; `FAULT` releases → **recovery OFF**; BQ25185 enters precharge, then fast charge |
| **−4.35 V reversed cell, USB present** | X ≈ 0.33 V, far below REF_POL → comparator A LOW → **recovery OFF.** LTC4368 ties GATE to negative VIN → main path blocked. Board **boots from USB**, so the fault is diagnosable |
| **Battery absent, USB present** | Recovery ON briefly; the open node charges to the ~2.8 V handoff bound, comparator B disables, node decays through the 2 MΩ bridge, re-enables. **Slow, low-duty oscillation at ≤8 mA into an open circuit — bounded and harmless.** Note the BQ25185 already runs its own no-battery limit cycle in this state (S6 §7.3.10) |
| **Pack protection MOSFET open** | Terminals read ≈0 V → recovery ON. Most 1S protectors release over-discharge latch on detecting charger voltage. ⚠ **If the specific protector requires more than ~10 mA to release, recovery will not clear it** — verify against the chosen pack; this is the one place the 8 mA choice could be too conservative |
| **USB removed during recovery** | VBUS collapses → comparator unpowered → `R_PU` has no rail, but `Q_REC` source is also at 0 V → V_GS = 0 → **OFF**. `D_REC` independently blocks any battery→VBUS path. Clean stop, **zero battery drain** |
| **USB appears with a reversed pack already inserted** | During VBUS ramp the comparator outputs are low → series AND open → `Q_REC` **OFF by default**. Once valid, comparator A holds it off. **No transient enable window** |
| **Normal cell, USB present** | FAULT released → recovery OFF regardless of the comparators |
| **Normal cell, no USB** | Branch unpowered. **Zero standby current** |

---

## 3. Recovery current

| current | R_LIM | time 2.0→2.8 V, 2000 mAh | worst single-failure current into a reversed cell | R_LIM dissipation | verdict |
|---|---|---|---|---|---|
| **1 mA** | 4.7 kΩ | ~20–40 h | ~2 mA | 5 mW | **REJECT** — recovery time is not a product behaviour |
| **5 mA** | 1 kΩ | ~2–4 h | ~9 mA | 25 mW | **Acceptable — lower bound** |
| **10 mA** | 470 Ω | ~1–2 h | ~19 mA | 47 mW | **Acceptable — upper bound** |
| **20 mA** | 220 Ω | ~30–60 min | ~41 mA | 100 mW | Marginal — fault current doubles for a modest time gain |

**RECOMMENDED RANGE: 5–10 mA. Design centre ~8 mA (R_LIM ≈ 560 Ω).**

Reasoning:

- **Deeply discharged bare-cell safety.** A Li-ion cell below ~2.0 V, and
  especially below 1.5 V, can suffer copper dissolution; recharging such a cell at
  meaningful current risks internal shorts. 8 mA is **≈0.004 C** for a 2000 mAh
  pack — an order of magnitude below the ≤0.05 C usually considered safe for
  reviving a deeply discharged cell.
- **Bounded fault.** ≤19 mA even at the 10 mA design point if a recovery component
  fails (§4).
- **It is not the charger.** The branch only has to lift the cell over the
  LTC4368's 2.2 V UVLO. The BQ25185 then does the real work at its own precharge
  and fast-charge rates.
- **Self-tapering.** Current falls as the cell rises: at 2.8 V it is already
  ~(5 − 0.3 − 2.8)/560 ≈ 3.4 mA.
- USB current draw is negligible.

**Do not lock R_LIM here.** The 5–10 mA window is the engineering conclusion; the
exact value should be set at schematic time and, per the no-respin policy (D-049),
`R_LIM` should be an **accessible tuning resistor**.

---

## 4. Dead-cell branch — single-failure analysis

"High current" is taken to mean a current capable of damaging or heating a
reversed cell. `R_LIM` bounds every case below to ≤19 mA (≈0.01 C), which is
below any Li-ion abuse threshold and comparable to parasitic drain.

| # | single failure | correct battery, USB present | **reversed battery, USB present** | USB absent (any battery) |
|---|---|---|---|---|
| 1 | **Comparator A output stuck HIGH** (says "not reversed") | No change — FAULT and B still gate correctly | ⚠ **Recovery enabled → ~13 mA into a reversed cell.** Bounded, non-hazardous, and self-annunciating (the cell never recovers; firmware reports it) | Branch unpowered — safe |
| 2 | **Comparator A output stuck LOW** | Recovery never runs → dead cell not recovered (**fails safe, loses the feature**) | Correctly blocked | Safe |
| 3 | **Comparator B stuck HIGH** | Trickle continues after handoff — but FAULT releases and disables it anyway. **No effect** | Blocked by A | Safe |
| 4 | **Comparator B stuck LOW** | Recovery never runs (fails safe) | Correctly blocked | Safe |
| 5 | **Sense resistor R_B open** | X rises to VBUS → A reads "positive" → recovery may run on a healthy cell, but FAULT gates it off. **No effect** | X rises to VBUS → A says "not reversed" → **same as failure 1, ≤13 mA.** Bounded | Safe |
| 6 | **Sense resistor R_B short** | X = V_BAT. For a healthy cell X > REF_POL → no change | X = −3.7 V → **below the comparator's negative rail.** C1 specifies **no phase reversal for overdriven inputs**, so the output stays in the correct state → **correctly blocked.** *(This is why the "no phase reversal" spec is load-bearing and why the part choice matters)* | Safe |
| 7 | **R_A open** | X = V_BAT (as failure 6) | Correctly blocked | Safe |
| 8 | **Q_REC drain-source short** | Trickle always on while USB present; FAULT-gating lost. Continuous ~1 mA into a full cell — undesirable float, not a hazard | ⚠ **~13 mA into a reversed cell.** Bounded. `D_REC` still prevents any reverse direction | **Safe** — `D_REC` blocks battery→VBUS, so no pack drain |
| 9 | **Q_REC gate short to source** | Permanently OFF → feature lost, fails safe | Correctly blocked | Safe |
| 10 | **R_LIM short** | Recovery current becomes VBUS-limited; USB source impedance and `D_REC` limit it. Charging a healthy cell hard, but FAULT gates it off | ⚠ **This is the one genuinely bad case** — an unlimited path into a reversed cell if combined with an enable. **But it requires failure 1, 8 or 10 *plus* an enable**, i.e. two failures. Alone, the comparators still block | Safe |
| 11 | **Reference (R_C/R_D) failure high** | REF_POL → VBUS → A always reads "reversed" → recovery never runs (**fails safe**) | Correctly blocked | Safe |
| 12 | **Reference failure low** | REF_POL → 0 → A always reads "not reversed" → same as failure 1 | ⚠ **≤13 mA.** Bounded | Safe |
| 13 | **Q_AND_A or Q_AND_B open** | Recovery never runs (fails safe) | Correctly blocked | Safe |
| 14 | **Q_AND_A or Q_AND_B D-S short** | The *other* series device still gates → **no effect** | **Still blocked** by the surviving series device and by comparator A | Safe |

### 4.1 Verdict, stated plainly

**Candidate B does NOT achieve absolute single-fault tolerance against every
failure.** Failures 1, 5, 8 and 12 each individually enable a recovery current
into a reversed cell.

**It does achieve the requirement as written** — *"No single failure in the
recovery branch should create a **high-current** charging path into a reversed
Li-ion cell"* — because `R_LIM` bounds every one of those cases to **≤13 mA
(~0.007 C)**, which is not a high-current path by any Li-ion safety criterion. The
consequence is graceful degradation, not a cliff edge.

**Three properties make this defensible rather than merely tolerable:**

1. **`R_LIM` is in series with every failure path.** The only failure that removes
   it (10) does not by itself enable the switch.
2. **`D_REC` makes the branch unidirectional under all faults** — no failure can
   drain the pack or back-feed VBUS.
3. **The fault is self-annunciating** — a reversed cell never recovers, and
   firmware reports it from the `BAT_RAW` ADC.

### 4.2 Redundant variation, if the CTO wants belt-and-braces

Use **both TLV7032 channels for the polarity test**, from two independent divider
pairs, in series-AND. Then failures 1, 5 and 12 are each covered by the surviving
channel, and only a common-mode failure of the shared IC defeats both.

**Cost:** the handoff upper bound is lost, so an absent battery leaves the branch
free-running against `FAULT` alone — an oscillation at ≤8 mA into an open node.
Add an RC (~100 ms) on the enable to make it slow and low-duty.

**My recommendation is the primary variant** (one polarity channel + one handoff
channel + FAULT). The residual it accepts is a bounded 13 mA into a cell that is
already fitted backwards, whereas the redundant variant trades that for a
permanent oscillation in the far more common battery-absent state.

---

## 5. Main pass path — P1 versus P2

### 5.1 Why P1 fails, precisely

Common-source N-FET pair: both source terminals tie to a floating node `S`. Body
diodes have **anode at S**, cathodes at the two drains — so with both channels off
no current can flow either way.

| single short | result |
|---|---|
| **M1 shorted** (the `BAT_RAW`-side FET) | `S` is tied to `BAT_RAW` = −3.7 V. M2's body diode (anode `S` = −3.7 V, cathode `BAT_PROT` ≈ 0 V) is **reverse biased → BLOCKED** ✓ |
| **M2 shorted** (the `BAT_PROT`-side FET) | `S` is tied to `BAT_PROT` ≈ 0 V. M1's body diode (anode `S` = 0 V, cathode `BAT_RAW` = −3.7 V) is **forward biased → CONDUCTS** ✗ |

**P1 therefore fails one of the two single-FET-short cases.** The earlier
statement that "a shorted pass FET defeats the LTC4368" was directionally right
but imprecise: it is specifically the **`BAT_PROT`-side FET** whose short is
dangerous. A 50% chance of a dangerous outcome given a single-FET short is not a
protection scheme.

### 5.2 P2 — two back-to-back stages in series

```
BAT_RAW ── M1 ═ M2 ──(mid)── M3 ═ M4 ──[ R_SENSE ]── BAT_PROTECTED_P
           stage A            stage B
```

**Any single D-S short leaves one complete back-to-back pair intact**, which
blocks both directions. The requirement in ruling D is met by **isolation**, not
by fault-clearing time — exactly the preference stated.

**A second benefit that is easy to miss:** with one FET shorted, the LTC4368's
**electronic circuit breaker still works**, because the surviving stage can still
open. Under P1 a shorted FET disables the breaker entirely.

### 5.3 Quantitative comparison

**Can one GATE output drive both stages? YES.** All four sources sit within
millivolts of each other (separated only by R_DS(on) drops), so a single GATE net
enhances all four. Confirmed constraints from L1:

| parameter | P1 (2 FETs) | P2 (4 FETs) | note |
|---|---|---|---|
| ΣC_iss (≈1.3 nF/FET) | ~2.6 nF | ~5.2 nF | doubles |
| Recommended C_GATE | 1 nF | **4.7 nF** | Raise it so the **explicit capacitor dominates ΣC_iss**, keeping inrush deterministic rather than set by a nonlinear, loosely-specified C_iss |
| C_total at GATE | ~3.6 nF | ~9.9 nF | |
| Turn-on time (35 µA, ~10 V) | ~1.0 ms | **~2.8 ms** | Both ≪ the 32 ms t_D(ON) — **no impact** |
| Turn-off time (60 mA sink) | ~0.6 µs | **~1.7 µs** | Still well inside the 8 µs L1 quotes for its worked example |
| **Inrush** = (C_OUT/C_total) × 35 µA, C_OUT 10 µF | ~97 mA | **~35 mA** | **P2 *reduces* inrush** — a bonus, not a cost |

**Series resistance and drop.** With R_SENSE = 15 mΩ:

| | P1, 18 mΩ FETs | P2, 18 mΩ FETs | **P2, 10 mΩ FETs (recommended)** |
|---|---|---|---|
| Total series R | 51 mΩ | 87 mΩ | **55 mΩ** |
| Drop @ 0.5 A | 26 mV | 44 mV | **28 mV** |
| Drop @ 1 A | 51 mV | 87 mV | **55 mV** |
| Drop @ 2 A | 102 mV | 174 mV | **110 mV** |
| Drop @ 3 A | 153 mV | 261 mV | **165 mV** |
| Dissipation @ 3 A | 0.46 W | 0.78 W | **0.50 W** |
| Per-FET @ 3 A | 162 mW | 162 mW | 90 mW |

**The R_DS(on) penalty of P2 is avoidable.** Spending the budget on ~10 mΩ duals
instead of ~18 mΩ ones makes P2's total series resistance essentially equal to
P1's. This matters directly to **P-14** (MAX17048 IR-drop compensation): P2 with
naive part selection would nearly double the uncompensable drop; P2 with the right
FETs does not.

| | P1 | P2 |
|---|---|---|
| PCB area | 1 × SOIC-8 | 2 × SOIC-8, ≈ +30 mm² with courtyard |
| BOM lines | 1 | 2 |

### 5.4 Common-mode / package-level failure — the decisive point

The brief is explicit: *"do not claim independence if two FETs are physically one
silicon/package and the dominant package failure can short both."*

Within a single dual package the two die share a leadframe, a die paddle and one
molding. A package-level event — severe overcurrent, thermal runaway, a solder or
mold-compound failure with arcing — can plausibly damage both channels together.
**Independence between the two back-to-back stages therefore cannot be claimed if
both stages live in one package.**

**Requirement: the two stages must be in SEPARATE PACKAGES.** Within a stage, a
dual is acceptable — if that stage's package fails wholesale, the other stage is
physically elsewhere and still blocks.

- **Two dual-FET packages in series (recommended).** Package-level independence
  between stages, which is the level that matters.
- **Four discrete singles.** Fully independent but ~4× the area for protection
  against a failure mode the two-package arrangement already covers.
- **A single quad package. REJECT** — it would defeat the entire purpose.

### 5.5 Selected architecture: **P2**

Two back-to-back stages, **two separate dual-FET packages**, one LTC4368-1 GATE
net, C_GATE raised to 4.7 nF, R_GATE 22 kΩ, R_SENSE 15 mΩ, FETs selected for
≈10 mΩ so the series drop matches P1.

---

## 6. Clamp reassessment

### VERDICT: **USEFUL SECONDARY PROTECTION** — not required, and no longer the mechanism protecting BAT.

Under P2, **no single fault drives `BAT_PROTECTED_P` negative.** The surviving
back-to-back stage isolates the reversed cell, so BQ25185 `BAT` never approaches
its −0.3 V limit. The clamp is therefore demoted from primary protection to a
secondary/energy device.

**The brief's objection is accepted in full.** The previous position — that a
Schottky at ≈0.8–1.0 V under a 20 A fault constituted protection for a −0.3 V
absolute maximum — was **not a valid compliance argument**, and it is withdrawn.
With P2, that argument is no longer needed, because the pin is protected by
isolation rather than by clamping.

**Retain a small Schottky** for: connector-side ESD, hot-plug undershoot
transients, and best-effort behaviour under a genuine double fault (one FET
shorted in **each** stage). Because it is no longer expected to carry a cell
short, it does **not** need a large surge rating.

**What must not be claimed:** that the clamp keeps `BAT` inside absolute maximum
under a cell short. It does not, at any realistic size. Under P2 it does not have
to.

---

## 7. Fuse reassessment

### VERDICT: **RETAINED — role changed from primary to backstop, and RESIZED UPWARD.**

With P2, the LTC4368's 3.33 A electronic breaker survives a single FET short
(§5.2), so the fuse is no longer the mechanism of first resort for anything.

| role | still justified? |
|---|---|
| Catastrophic short downstream of the FETs | **No** — the electronic breaker opens in 8 µs, and it still works with one FET shorted |
| Recovery-branch failure | **No** — bounded to ≤19 mA by `R_LIM` |
| **Connector / harness short between `BAT_RAW` and GND, upstream of the FETs** | **YES** — the LTC4368 is not in this path. Only the fuse or the pack's own protector can clear it. **This is the fuse's real remaining job** |
| Battery-pack internal short | Partly — the pack protector should act first; the fuse is a backstop if the pack is unprotected |
| Clamp fails short | **No** — that is a forward overcurrent from `BAT_PROT` to GND, which the breaker clears |
| Two FETs shorted (one per stage) | **YES** — last line of defence |

**Sizing changes as a direct consequence.** The fuse must sit **above** the
electronic breaker so it never pre-empts it:

| | previous (FBV2-PWR-001) | **revised** |
|---|---|---|
| Rating | 3 A fast-acting | **≈5 A fast-acting** |
| Rationale | primary clearing element | Must exceed the 3.33 A LTC4368 breaker and the 1–3 A operating peaks so it never nuisance-blows; it is a backstop, not the first responder |

**PTC: still REJECTED.** No new analysis changes the two disqualifiers — clearing
time in the tens-to-hundreds of milliseconds, and auto-retry that re-applies the
fault on every cycle. Nothing in P2 makes a slow, self-resetting element
appropriate here.

---

## 8. Final battery protection block

```
 ══════════════════════════ NORMAL MAIN PATH ══════════════════════════

  J4 (JST-PH 2-pin)
   pin1 ──[ F1  5A fast ]──┬── BAT_RAW ──┬──────────────────────────────┐
   pin2 ── GND             │             │                              │
                       ○ TP_BAT_RAW  ○ TP_BAT_RAW_F                     │
                        (J4 side)     (FET side — the two together      │
                                       make fuse state observable)      │
                                       │                                │
                        ┌──────────────┴───────────────┐                │
                        │   STAGE A  (package 1)       │                │
                        │      M1 ═══ M2  common src   │                │
                        └──────────────┬───────────────┘                │
                                     (mid)                              │
                        ┌──────────────┴───────────────┐                │
                        │   STAGE B  (package 2)       │                │
                        │      M3 ═══ M4  common src   │                │
                        └──────────────┬───────────────┘                │
                                       │                                │
                              ○ TP_SENSE ──[ R_SENSE 15 mΩ ]── ○ TP_VOUT│
                                                    │                   │
                                          BAT_PROTECTED_P               │
                                                    │                   │
        ┌───────────────────────────────────────────┼───────────┬───────┼────────┐
        │                                           │           │       │        │
   D_CLAMP (secondary:                          C_OUT ≥1µF  BQ25185  MAX17048    │
   ESD / transient / double-fault)                             BAT    (P-14)     │
   cathode→BAT_PROT, anode→GND                                                   │
                                                                                 │
   ┌──────────── LTC4368-1  (MSOP-10) ────────────┐                              │
   │  VIN ── BAT_RAW          VOUT ── BAT_PROT    │                              │
   │  SENSE ── stage-B output                     │                              │
   │  GATE ──[ R_GATE 22k ]──┬── all four gates   │                              │
   │                         └── C_GATE 4.7 nF    │                              │
   │  UV  ──[ 510k ]── VIN   (deliberately UNUSED)│                              │
   │  OV  ──[ divider ≈4.6 V ]                    │                              │
   │  RETRY ── GND           (latch off, fwd OC)  │                              │
   │  SHDN  ──[ R_PU ]── VIN ── ○ TP_SHDN         │                              │
   │  FAULT ──┬─○ TP_FAULT ──[ R_PU ]── +3V3      │                              │
   └──────────┼───────────────────────────────────┘                              │
              │                                                                  │
 ═════════════┼═══════════ DEAD-CELL RECOVERY PATH ═══════════════════════════════
              │  (active ONLY while FAULT is low — i.e. the main path is NOT in control)
              │
    VBUS ─────┼──┬── TLV7032 VDD ── comparator A (polarity)  ─┐
   (USB only) │  │                  comparator B (handoff)  ─┐│
              │  ├──[ R_A 1M ]──┬──[ R_B 1M ]── BAT_RAW      ││
              │  │              X (always positive)           ││
              │  ├──[ R_C/R_D ]── REF_POL ≈ VBUS/2            ││
              │  ├──[ R_E/R_F ]── REF_HANDOFF                 ││
              │  │                                            ││
              │  ├──[ R_PU 1M ]──┬── gate  Q_REC (P-FET)      ││
              │  │               │                            ││
              │  └── source ─────┘   drain ──[ R_LIM 560R ]──▶|── BAT_RAW
              │                                            D_REC
              │        3-input series AND (all must conduct):
              └────────  Q_AND_A ── Q_AND_B ── FAULT
                          (comp A)  (comp B)   (LTC4368)

    ○ TP_BAT_RAW  ○ TP_BAT_RAW_F  ○ TP_SENSE  ○ TP_VOUT
    ○ TP_GATE (bare pad — probe C affects inrush)   ○ TP_FAULT   ○ TP_SHDN
    ○ TP_RECOVERY_EN  (Q_REC gate — shows recovery state without a current probe)
```

**In-series removable link in `BAT_PROTECTED_P`** — retained from FBV2-PWR-001. A
series link only *opens* the path and cannot bypass reverse protection. A parallel
link across the FETs remains **forbidden**.

---

## 9. Candidate parts

**None are fabrication-locked.** Sourcing status is marked for verification at the
procurement gate — a discipline this programme already learned the hard way when
blind BOM regeneration destroyed eight hand-entered MPNs.

| role | candidate | mfr | package | key ratings | alternate | status |
|---|---|---|---|---|---|---|
| Protection controller | **LTC4368IMS-1#PBF** | ADI | MSOP-10, leaded | 2.5–60 V op, −40 V protection, 80 µA / 5 µA | — (no equivalent found in the R1 sweep) | **Verified from L1.** Sourcing TBV |
| Pass FETs (×2 packages) | **FDS6898A** | onsemi | SOIC-8, leaded | 20 V, 9.4 A, 18 mΩ @ V_GS 2.5 V; **independent dual** | Any independent dual N, ≤10 mΩ preferred | **Specs via R1, not read this session.** Verify. **Must NOT be a common-drain dual** — the LTC4368 has one GATE pin and needs common source |
| Comparator | **TLV7032** | TI | SOT-23-8, leaded | 1.6–6.5 V, 315 nA, RRI CM, 7 mV hyst, no phase reversal | TLV7042 (open-drain) if a wired-AND is preferred | **Verified from C1.** Sourcing TBV |
| Recovery P-FET | **AO3401A** | AOS | SOT-23 | −30 V, ~4 A, ~60 mΩ | SI2301, DMP2035U | Commonly a JLC **Basic** part — **verify** |
| AND N-FETs | **2N7002DW** (dual) | multiple | SOT-363 | 60 V, logic level | 2× 2N7002 in SOT-23 | Commonly **Basic** — verify |
| Recovery Schottky | 30–40 V, ≥100 mA | — | SOD-323/SOD-123 | Low V_F | BAT54, RB751 | Verify |
| Negative clamp | Schottky, secondary duty | — | SOD-123 | Modest surge; no longer sized for a cell short | — | Verify |
| Fuse | **≈5 A fast-acting** | — | 1206 | Above the 3.33 A breaker | — | Verify |
| Bridge/reference R | 1 MΩ **0.1%** thin film | — | 0402 | ±20 mV threshold error | 1% acceptable with a −0.3 V bias | Verify |

**Package policy honoured:** every new safety-critical part is **leaded and
inspectable** — MSOP-10, SOIC-8, SOT-23-8, SOT-23, SOT-363. **No BGA, no WLCSP,
no bottom-terminated parts** anywhere in the battery protection or recovery
circuitry.

---

## 10. FBV2-A1 gate

| criterion | status |
|---|---|
| Dead-cell recovery topology explicit | **YES** — §2, complete to component level, with thresholds, defaults, handoff and every state defined |
| Main reverse protection single-FET-short tolerant | **YES** — P2, §5. Isolation, not fault-clearing time, per ruling D |
| All power/fault states have defined safe behaviour | **YES** — 13/13, §11 and the state table |
| No additional power-tree branch remains TBD | **YES** — the recovery branch was the last one, and it is now specified |

### VERDICT: **FBV2-A1 = PASS.**

Component-value optimisation (exact R_LIM, exact FET MPN, exact fuse rating,
divider trim) moves to schematic design, which the brief explicitly permits.

**Recommended next gate: FBV2-A2 — MECHANICAL INTERFACE FREEZE.** It is the long
pole, nothing blocks it, and the internal cavity has never existed in this
repository. Schematic migration (FBV2-S1) should not start before the placement
constraints exist.

---

## 11. Fault cases — all thirteen

| # | case | behaviour | status |
|---|---|---|---|
| 1 | Normal battery, no USB | Both stages on, ~55 mΩ; recovery branch unpowered, zero standby | **OK** |
| 2 | Normal battery + USB | Charge current passes (reverse direction, −50 mV threshold); FAULT released → recovery off | **OK** |
| 3 | No battery + USB | Runs from USB; BQ25185 no-battery limit cycle, STAT2 toggles (maskable on PCAL9535A); recovery branch parks at the ~2.8 V handoff bound, slow low-duty oscillation ≤8 mA into an open node | **OK** |
| 4 | 0 V / dead battery + USB | **Recovery ON at ~8 mA** → cell rises → LTC4368 closes at ~2.2 V → FAULT releases → recovery OFF → BQ25185 precharges | **OK — solved** |
| 5 | Pack protection-open + USB | Terminals ≈0 V → recovery ON; most 1S protectors release on charger-voltage detect. ⚠ Verify the chosen pack's release current | **OK, one part-dependent caveat** |
| 6 | Reversed battery, no USB | GATE auto-tied to negative VIN; both stages block; recovery unpowered | **BLOCKED correctly** |
| 7 | Reversed battery + USB | Both stages block; comparator A holds recovery off; **board boots from USB**, fault diagnosable | **OK** |
| 8 | **One main pass FET short + reversed battery + USB** | Surviving back-to-back stage **isolates**; `BAT_PROT` never goes negative; electronic breaker still functional | **OK — requirement met by isolation** |
| 9 | **Recovery switch stuck on + reversed battery + USB** | `R_LIM` bounds to **≈13 mA (~0.007 C)**; `D_REC` keeps it unidirectional; self-annunciating | **BOUNDED — not a high-current path** |
| 10 | Battery inserted while USB present | 32 ms turn-on delay debounces; C_GATE 4.7 nF bounds inrush to ~35 mA against a 3.33 A trip | **OK** |
| 11 | **USB removed during recovery** | VBUS collapses → Q_REC source at 0 V → V_GS = 0 → OFF; `D_REC` blocks any pack drain | **OK — clean stop** |
| 12 | Accessory short | TPS22950C current limit + auto-retry + thermal shutdown; core `+3V3` holds | **OK** |
| 13 | Externally powered accessory, AQROOT off | TPS22950C RCB active while disabled; TCA9517A high-Z unpowered; no permanent raw `+3V3` pin exists | **OK** |

**13 of 13 defined. No case remains architecture-undefined.**

Carried into the schematic phase as bench/design items, **none of which changes
topology**: P-12 (now downgraded — see §12), P-14 (MAX17048 sense point),
P-15 (3V3 rail budget), P-16, P-17, P-18.

---

## 12. Corrections to previous work

| prior position | status | correction |
|---|---|---|
| *"Fuse REQUIRED, clamp REQUIRED"* as the answer to the shorted-FET case | **SUPERSEDED** | The compliance argument was invalid — a Schottky at ≈0.8–1.0 V does not protect a −0.3 V absolute maximum. **P2 replaces it with isolation.** Ruling D was right |
| *"3 A fast-acting fuse"* | **RESIZED to ≈5 A** | With P2 the fuse is a backstop, not the first responder. It must sit **above** the 3.33 A electronic breaker so it never pre-empts it |
| *"Clamp REQUIRED"* | **Downgraded to USEFUL SECONDARY** | No single fault drives `BAT_PROT` negative under P2 |
| *"A shorted pass FET defeats the LTC4368"* | **Refined** | True only for the **`BAT_PROT`-side** FET. The `BAT_RAW`-side FET shorting is already blocked by the survivor. P1 fails 1 of 2 cases, not 2 of 2 |
| **P-12** — BQ25185 survivability of a −1 V excursion | **Largely retired** | Under P2 the excursion does not occur under any single fault. It survives only as a **double-fault** consideration, no longer an architecture item |
| *Candidate B described only as "a comparator interlock"* | **Now complete** | Ratiometric bridge, thresholds, defaults, 3-input AND, FAULT handoff, failure analysis |
| *"a firmware-gated trickle"* (FBV2-ARCH-002) | **Fully superseded** | Firmware makes no safety decision; recovery works with blank flash |
| C_GATE = 1 nF | **Revised to 4.7 nF for P2** | With four FETs ΣC_iss ≈ C_GATE, so the explicit capacitor must be raised to keep inrush deterministic |

---

## Sources

- ADI **LTC4368** `4368f` — [Farnell mirror](https://www.farnell.com/datasheets/2243878.pdf) · [ADI product page](https://www.analog.com/en/products/ltc4368.html)
- TI **TLV7031/32/41/42** — [ti.com](https://www.ti.com/lit/ds/symlink/tlv7031.pdf)
- TI [BQ25185 SLUSF65A](https://www.ti.com/lit/ds/symlink/bq25185.pdf) · [TPS22950 SLVSFJ2B](https://www.ti.com/lit/gpn/tps22950)
- [Independent review FBV2-CTO2-PWRNFC-001](../reviews/2026-08-22-independent-cto-power-nfc-review.md) — advisory; source of the FDS6898A figures
