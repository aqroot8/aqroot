# AQROOT Full Beta v2 — Battery Protection and Electrical Architecture Closeout

Date: 2026-08-22
Task: **FBV2-PWR-001**
Repository HEAD at audit: `d5b6547`
Scope: **documentation only.** No KiCad, PCB, firmware, mechanical or fabrication file was created or modified. `hardware/beta-v2/` was not created.

---

## 0. Sources

| # | document | revision | how obtained |
|---|---|---|---|
| **L1** | **ADI LTC4368** — *100V UV/OV and Reverse Protection Controller with Bidirectional Circuit Breaker* | doc id **`4368f`** | **Farnell mirror** (analog.com blocked: timeout, then ECONNRESET; Mouser/Arrow mirrors returned HTML) |
| **X1** | **Semtech SX1261/2 Data Sheet** | **`DS.SX1261-2.W.APP` Rev. 1.2, June 2019**, 111 pp. | **SparkFun CDN mirror** (semtech.com and its Salesforce CDN blocked) |
| S6 | TI BQ25185 | SLUSF65A, rev. Jan 2026 | ti.com (earlier task) |
| S8 | TI TCA9535 | SCPS201E, rev. May 2022 | ti.com (earlier task) |
| S9 | TI TPS22950/C/L | SLVSFJ2B, rev. Feb 2023 | ti.com (earlier task) |
| **P1** | NXP PCAL9535A | — | **PDF NOT OBTAINED.** NXP 404 direct and via browser render-timeout; Digi-Key 410; Mouser/LCSC/Diodes mirrors returned HTML. Evidence is NXP product-page text plus the CTO-supplied pinout. |

### Retrieval note — recorded because it bounds three verdicts

Direct fetches of nxp.com, analog.com and semtech.com PDFs are blocked from this
environment. Browser automation reached the NXP PDF but the PDF renderer timed
out on three consecutive screenshot attempts, so I stopped rather than loop.

**Two of the three blocked documents were recovered from distributor/CDN
mirrors** (Farnell for the LTC4368, SparkFun for the SX126x) and are full,
readable, primary-vendor PDFs. **The PCAL9535A was not recovered** and its
verdict is bounded accordingly in §7.

**Revision caveat on X1.** The current Semtech revision is **V2.2 (file
`60852689.DS_SX1261_2 V2-2.pdf`, 100 pp., dated 2025-04-07)** — I identified it
but could not read it. The rule quoted in §8 is from **Rev. 1.2**. The IRQ
mechanism is fundamental and is very unlikely to have changed, but **confirm
against V2.2 before fabrication**, and check the **E22-900M22S module** datasheet
in case the module re-times or buffers DIO1.

---

## 1. CTO rulings recorded

| ruling | recorded as | note |
|---|---|---|
| **A** — replace both `U2` and `U3` with **PCAL9535APW,118** (LCSC C2669683); architecture lock, not a footprint signoff; firmware changes mandatory; external safe-state resistors remain | D-061 | §7 |
| **B** — 20-pin resource architecture locked (11 XGPIO / 2 native / 2 I²C / 1 WAKE / 1 switched 3V3 / 3 GND), no raw permanent +3V3 | D-062 | unchanged from D-059 |
| **C** — preferred native pair GPIO38 + GPIO47; GPIO43 fallback only; move `SX1262_DIO1` to the **internal** PCAL9535A; `BUSY` stays native | D-063 | §8 |
| **D** — **battery-protection language correction**: fuse + Schottky clamp is a **CANDIDATE defence-in-depth topology pending exact fault-energy analysis**, not a locked decision | D-064 | §5 — **and the analysis vindicates the correction** |

> **Ruling D was the right call.** The fault-energy analysis in §5 shows the
> Schottky clamp **cannot guarantee** the BQ25185 BAT −0.3 V absolute maximum at
> realistic fault currents. Had this been recorded as "locked" it would have
> carried an unearned implication of proof. The corrected language is now the
> record.

---

## 2. LTC4368-1 complete circuit analysis

All values below are from **L1** unless marked.

### 2.1 Verified device behaviour

| question asked | answer | evidence |
|---|---|---|
| Operating range | **2.5 V to 60 V**. Protection range **−40 V to 100 V** | L1 Features; VIN pin description |
| VIN UVLO | **1.8 / 2.2 / 2.4 V** (min/typ/max), VIN rising | L1 EC table, `VIN(UVLO)` |
| VOUT UVLO | **1.8 / 2.2 / 2.4 V**, VOUT rising; delay **40 / 120 / 280 µs** | L1 EC table, `VOUT(UVLO)`, `tVOUT(UVLO)` |
| Reverse VIN behaviour | *"When VIN goes negative, **GATE is automatically connected to VIN**."* Block diagram: a reverse-protection switch that **"CLOSES SWITCH WHEN VIN IS NEGATIVE"** | L1 GATE pin description; Block Diagram |
| **LTC4368-1 reverse threshold** | **V_SENSE = −50 mV** | L1 SENSE pin description |
| **LTC4368-2 reverse threshold** | **V_SENSE = −3 mV** | L1 SENSE pin description |
| Forward threshold | **V_SENSE = +50 mV**, both variants | L1 Features, SENSE |
| Gate drive | Internal charge pump, **35 µA pull-up**, up to **13.1 V** enhancement. Off → GATE pulled just below the lower of VIN or VOUT | L1 GATE |
| Forward-OC response | **60 mA** GATE pull-down; *"immediately (8 µs) turned off"* in the datasheet's worked example | L1 SENSE; Applications |
| Turn-on delay | **t_D(ON) = 22 / 32 / 45 ms** | L1 EC table |
| UV comparator | **0.5 V falling**, 25 mV hysteresis, 1 µs; recovery at >0.525 V **plus the 32 ms delay**. *"If unused and VIN is less than 80 V, connect to VIN with a 510 k resistor."* | L1 UV pin |
| OV comparator | **0.5 V rising**, 25 mV hysteresis, 1 µs; recovery at <0.475 V plus 32 ms. *"Connect to GND if unused."* | L1 OV pin |
| Latch vs retry | **RETRY to GND = latch off after a FORWARD overcurrent fault.** To re-enable, **SHDN must be toggled low then high.** RETRY to a capacitor = **5.5 ms/nF** auto-retry delay | L1 RETRY, SHDN |
| Current sense | Bidirectional, single R_SENSE between SENSE and VOUT | L1 SENSE |
| **Does charger current flow normally VOUT→VIN?** | **Yes** — that is the reverse direction, and the **-1**'s −50 mV threshold is a symmetric circuit breaker, not an ideal diode. A **-2** would trip at −3 mV and block charging | L1 SENSE |
| **Can the controller operate from a deeply discharged raw battery?** | **No.** VIN is the supply pin and has a 2.2 V typ / **2.4 V max** UVLO | L1 VIN |
| **Can USB/system-side power the controller through VOUT?** | **No, not the core.** VOUT is a *sense* input. *"The GATE charge pump voltage is referenced to VOUT. It is used as the charge pump input **when VOUT is greater than approximately 5 V**."* At 1S (3.0–4.35 V) VOUT is **below 5 V**, so the pump runs from VIN. VOUT's own 2.2 V UVLO only gates the **reverse-current comparators** | L1 VOUT |
| **Inherent dead-cell recovery path?** | **None.** Below VIN UVLO both gates are off and the two body diodes are anti-series | derived from the above |

### 2.2 Two findings that change earlier conclusions

**(a) Inrush is a designed parameter, not a hazard. P-13 is RESOLVED.**

L1, Applications Information:

> *"Since the MOSFET acts like a source follower, the slew rate at VOUT equals the slew rate at GATE. Therefore, the inrush current due to the capacitance on VOUT is given by:*
> **I_INRUSH = (C_OUT / C_GATE) × I_GATE(UP)"**
>
> *"To prevent this capacitive inrush current from falsely triggering the forward overcurrent comparator, place an inrush limiting capacitor (C_GATE) on the GATE pin… This inrush current plus the output current must be less than the desired forward overcurrent threshold: **I_OC,FWD > I_INRUSH + I_OUT**"*
>
> *"R_GATE prevents C_GATE from slowing down the reverse polarity protection circuits. It also stabilizes the fast pull-down circuits and prevents chatter during fault conditions. **Set R_GATE to 22 k for most applications.**"*

The FBV2-ARCH-002 concern — that hot-insertion inrush might trip the same latch
that protects against a reversed cell — **was based on an incomplete reading.**
Inrush is set by C_GATE and is a design calculation with an explicit inequality.

**(b) Latch-off applies to FORWARD overcurrent only. Reverse faults auto-recover.**

L1: *"After a reverse current fault, the LTC4368 waits for the output to fall
100 mV below the input to reconnect power to the load"*, and *"A **forward**
overcurrent fault uses the RETRY pin to set the conditions for reconnecting
power to the load."*

So grounding RETRY for latch-off does **not** trap the board after a reversed
cell is corrected — the reverse mechanism is separate and self-recovering. This
removes the second half of the P-13 objection.

### 2.3 Proposed complete block diagram

```
                            ┌─── TP_BAT_RAW ─── R_div ──► ESP32 ADC  (BAT_RAW sense,
                            │                              ≥100k series + Schottky to GND)
   CELL       ┌──────────┐  │
  (J4.1) ─────┤  FUSE F1 ├──┴─── BAT_RAW ──┬──────────────────────────┐
              │ 3A fast  │                 │                          │
              └──────────┘                 │                    ┌─────┴──────┐
   CELL─ ─────────────────── GND           │                    │ PRECHARGE  │  ◄── §4
                                           │                    │  BRANCH    │      (polarity-
                                           │                    │ (from SYS) │       qualified)
                                    ┌──────┴──────┐             └─────┬──────┘
                                    │   LTC4368-1 │                   │
                                    │   VIN       │                   │
                          UV ───────┤  (510k→VIN, │                   │
                                    │   see 2.4)  │                   │
                          OV ───────┤             │                   │
                     RETRY→GND ─────┤             │  GATE ── R_GATE 22k ──┬── C_GATE ── GND
                     SHDN ──────────┤             │                       │
                     FAULT ─────────┤             │                       │
                                    │ VOUT  SENSE │                       │
                                    └───┬─────┬───┘                       │
                                        │     │                           │
        BAT_RAW ──── M1 ═══ M2 ─────────┴─ R_SENSE ─┬─── BAT_PROTECTED_P ─┘
                  (common source, independent dual) │
                    gates ◄────────────────────────GATE
                                                    │
                                    ┌───────────────┼──────────────┬──────────────┐
                                  D_CLAMP        C_OUT ≥1µF    BQ25185 BAT    MAX17048
                                (cathode here,                                (see P-14)
                                 anode to GND)
```

### 2.4 Element-by-element recommendation

| element | recommendation | reasoning |
|---|---|---|
| **Controller** | **LTC4368-1**, MSOP-10. Suffix in symbol, BOM, assembly note and bring-up checklist | A `-2` blocks charging (−3 mV vs −50 mV) |
| **Pass element** | **Independent dual N-FET, wired common source.** Must be an *independent* dual, not a common-drain dual | The LTC4368 has a single GATE pin and needs a common-source pair |
| **R_SENSE** | **15 mΩ** → I_OC,FWD = 50 mV/15 mΩ = **3.33 A**, I_OC,REV = **−3.33 A** | Sits above the stated 1–3 A transient peak with margin |
| **R_GATE** | **22 kΩ** | L1's own recommendation; also prevents C_GATE slowing the reverse-protection path |
| **C_GATE** | **1 nF** → with C_OUT ≈ 10 µF, I_INRUSH = (10 µF/1 nF) × 35 µA ≈ **350 mA** | Satisfies I_OC,FWD (3.33 A) > I_INRUSH (0.35 A) + I_OUT with large margin |
| **UV** | **RECOMMEND UNUSED** — tie to VIN through 510 kΩ per L1 | **Setting UV at a cell-protection threshold would deepen the dead-cell lockout**: the FETs would open at the UV point rather than at 2.2 V, making recovery harder. Undervoltage cutoff belongs to the pack protector and the fuel gauge, not here |
| **OV** | **USE**, divider set ≈ 4.6 V | Protects against a failed charger driving the battery node above the cell's safe voltage. Cheap, and the BQ25185 is the only thing otherwise standing between a regulator fault and the cell |
| **RETRY** | **Ground (latch-off)** | Correct for a battery node. Only affects forward OC; reverse faults auto-recover (§2.2b) |
| **SHDN** | Tie high through a pull-up **to VIN**; any firmware control must be **open-drain pull-down only**, via a test point | ⚠ **Bootstrap hazard:** if SHDN is driven by an expander powered from `+3V3`, and `+3V3` derives from the cell through these very FETs, then pulling SHDN low with no USB kills the rail that was driving SHDN. A pull-up to VIN guarantees recovery. The 5 µA SHDN-low mode is a genuine ship mode and is worth having |
| **FAULT** | Pull-up to `+3V3`, route to a spare internal expander input, plus a test point | Open-drain; asserts on voltage fault, current fault, SHDN low, **or VIN below UVLO** — i.e. it directly reports the dead-cell lockout |
| **Fuse / clamp** | See §5 | **CANDIDATE**, per ruling D |
| **Precharge branch** | See §4 | **Not approved — the one item blocking FBV2-A1** |

---

## 3. Fault cases F1–F10

Detailed node-by-node analysis is in
[`../architecture/POWER_FAULT_STATE_TABLE.md`](../architecture/POWER_FAULT_STATE_TABLE.md).
Summary:

| # | case | result |
|---|---|---|
| F1 | Normal battery / no USB | **OK** |
| F2 | Normal battery / USB | **OK** — charge current is the reverse direction; `-1`'s −50 mV threshold passes it |
| F3 | No battery / USB | **OK electrically.** BAT node capacitive → BQ25185 limit cycle → **STAT2 toggles** (S6 §7.3.10). Maskable on PCAL9535A |
| F4 | **Deeply discharged / protection-open / ~0 V battery / USB** | **BLOCKED — no inherent recovery.** VIN < 2.2 V UVLO → both gates off → body diodes anti-series. **This is the gate blocker (§4)** |
| F5 | Reversed battery / no USB | **BLOCKED correctly.** GATE auto-connects to negative VIN; clamp conducts; fuse clears |
| F6 | **Reversed battery / USB** | **OK** — protection engages, BAT_PROTECTED_P held near 0 V, **device still boots from USB** so the fault is diagnosable |
| F7 | **One pass FET shorted + reversed battery + USB** | **PARTIALLY MITIGATED — see §5.** The LTC4368 cannot turn off a shorted FET. Clamp + fuse bound the excursion but **do not prove** the −0.3 V abs max is respected |
| F8 | Battery inserted while USB present | **OK** — 32 ms turn-on delay debounces; C_GATE bounds inrush to ~350 mA against a 3.33 A trip |
| F9 | Battery hot-plug inrush | **OK — RESOLVED.** L1 gives the design equation; VIN is explicitly hot-swappable |
| F10 | Battery removed during USB operation | **OK** — reverts to F3. Reverse-current comparator may fire as VOUT falls; recovery is automatic once VOUT falls 100 mV below VIN |

---

## 4. Dead-cell recovery — four candidates

### 4.1 The constraint that rules out the simple answers

A precharge path must distinguish **0 V (dead cell)** from **−3.7 V (reversed
cell)**. Both present as "the node is not at a normal cell voltage", and a
single MOSFET **cannot** tell them apart:

- **N-FET, source at BAT_RAW, gate from SYS divider.** Dead cell: V_GS ≈ +3 V → ON ✓. Reversed: V_GS ≈ +6.7 V → **ON, harder** ✗
- **P-FET, source at SYS, gate pulled toward BAT_RAW.** Dead cell: V_GS ≈ −4.5 V → ON ✓. Reversed: V_GS ≈ −8.2 V → **ON, harder** ✗

In both cases a reversed cell turns the pass device **more** on. **An explicit
level-sensing element referenced to GND is therefore mandatory.** This is the
core finding of §4 and it eliminates every "just add a resistor and a FET"
proposal.

### 4.2 Candidates

| | **A — permanent resistor bypass** | **B — comparator-qualified trickle from SYS** | **C — discrete transistor polarity interlock** | **D — service-mode only** |
|---|---|---|---|---|
| Concept | Fixed ~10 kΩ permanently bridging the pass FETs | Nanopower comparator with internal reference enables a small series FET from SYS→BAT_RAW only while −0.05 V < BAT_RAW < ~2.5 V | Precharge path from SYS, gated by a bipolar interlock: a transistor whose B-E junction is forward-biased **only** when BAT_RAW goes below ≈ −0.7 V, which disables the precharge FET | No recovery path. Deeply discharged packs are replaced or revived on a bench |
| Polarity validated? | **No** | **Yes**, actively, against a GND-referenced threshold | **Yes**, by the physics of a forward-biased junction | N/A |
| 0 V pack | Recovers | **Recovers** — trickle lifts VIN over the 2.2 V UVLO, then the LTC4368 takes over | **Recovers** | Does not |
| Protection-open pack | Applies voltage, which is how most 1S protectors release over-discharge latch | **Same, and qualified** | Same | Does not |
| Reversed pack | Charges it | **Blocked — 0 A** | **Blocked** | N/A |
| Reversed pack + USB | **Charges a reversed cell** | **Blocked** | **Blocked** | N/A |
| Max current into a reversed pack | ~0.8 mA continuous | **≈ 0** (comparator input leakage) | **≈ 0** | 0 |
| Quiescent | Continuous leakage cell↔system | Comparator I_Q (sub-µA class parts exist) + divider ≈ **1–3 µA** | Divider + interlock bias ≈ **2–5 µA** | **0** |
| Component count | **1** | ~8–10 (comparator, FET, 5–6 R, C) | ~7–9 (2 transistors, FET, resistors) | **0** |
| Failure modes | — | Comparator output stuck enabled → degenerates to A, but the **series resistor bounds it to ≈450 µA**, which is harmless | Interlock transistor open → degenerates to A with the same bound | User-visible dead product |
| **Firmware required?** | No | **No** | **No** | No |
| **Works with corrupted firmware?** | Yes | **Yes** | **Yes** | Yes |
| Verdict | **REJECT** — unconditional path around a safety element; charges a reversed cell, which the CTO instruction rejects outright | **RECOMMENDED** | Viable alternative; fewer ICs, more analogue behaviour to validate | Acceptable fallback only if B and C are both judged too risky |

### 4.3 Recommendation

**Candidate B**, with a series resistor sized so that *even in the comparator's
worst failure mode* the current into a reversed cell stays at the sub-milliamp
level — i.e. the safety property degrades gracefully rather than cliff-edge.

**This satisfies the CTO's stated preference: safety does not depend on working
application firmware.** The interlock is hardware, the qualification is
hardware, and a corrupted or absent firmware image changes nothing.

Pair it with the **`BAT_RAW` ADC divider** (≥100 kΩ series plus a Schottky clamp
to GND, so a negative node clamps at −0.3 V at microamps) so firmware can
*report* no-cell / dead-cell / reversed-cell — which F3, F4 and F6 otherwise
present identically. **The ADC is for diagnosis, not for safety.**

**Not approved. This is P-11 and it is the single item blocking FBV2-A1.**

> **Honest tradeoff, not hidden.** Candidate B adds ~10 parts and a few µA to a
> standby budget that is already unmeasured, to recover a pack that a careful
> user may never over-discharge. Candidate D costs nothing and is defensible for
> a five-unit prototype run where the operators are the engineering team. **My
> recommendation is B for the product and I would accept D for the first five
> boards** — but that is a CTO call, because it trades field-failure risk against
> first-build complexity, and only the CTO owns that.

---

## 5. Fuse and clamp — fault-energy analysis

### 5.1 Topology and orientation

| element | placement | orientation |
|---|---|---|
| **Fuse F1** | **In series with the cell positive, at J4**, before every other element | — |
| **Clamp D_CLAMP** | **Cathode on `BAT_PROTECTED_P`** (the BQ25185 BAT node), **anode to GND** | Reverse-biased in normal operation; conducts only when BAT_PROTECTED_P goes negative |

**Why the clamp goes on `BAT_PROTECTED_P`, not `BAT_RAW`.** The node whose
absolute maximum must be respected is BQ25185 `BAT`. In F7 the fault current
reaches that node through the shorted FET and the surviving FET's body diode, so
clamping upstream would leave the protected node unclamped. Clamping the
protected node puts the diode exactly where the limit applies.

**Fault current path in F7** (reversed cell, one FET shorted, USB present):
board GND (= cell **+**, because the pack is reversed) → D_CLAMP anode → cathode
→ `BAT_PROTECTED_P` → surviving FET body diode → shorted FET → `BAT_RAW` → **F1**
→ J4.1 → cell **−**. **Both the fuse and the clamp are in the same loop**, so the
clamp holds the node while the fuse clears it.

### 5.2 The energy arithmetic — and why the CTO's language correction was right

Prospective fault current is set by the cell, not by the board. A 2000 mAh 1S
pack with ~50–100 mΩ internal resistance into ~100 mΩ of loop resistance gives
roughly **20–25 A**.

| quantity | value | consequence |
|---|---|---|
| BQ25185 `BAT` absolute maximum | **−0.3 V (DC)** | S6 §6.1 |
| Schottky V_F at ~1 A | ~0.35 V | already marginal |
| **Schottky V_F at 20–25 A** | **~0.8–1.0 V** | **~3× the absolute maximum** |
| 3 A fast fuse clearing time at 25 A | well under 1 ms | |
| Let-through I²t | ≈ 25² × 1 ms ≈ **0.6 A²s** | within a typical 3 A fast fuse's clearing I²t |
| Clamp surge requirement | must survive ~25 A for <1 ms — a 3 A-class Schottky with I_FSM ≈ 100 A at 8.3 ms has ample margin **thermally** | |

**Conclusion: the clamp bounds the excursion from ≈ −3.7 V to ≈ −1 V — roughly a
4× improvement — but it does not bring the node inside the −0.3 V absolute
maximum.** Whether a ~−1 V excursion for <1 ms is survivable is **not derivable
from the datasheet**, because the −0.3 V figure is a DC rating with no stated
energy or duration term.

**This is exactly why "locked" was the wrong word and ruling D is correct.**

### 5.3 One-shot fuse versus PTC

| | **One-shot fast-acting fuse** | **Resettable PTC** |
|---|---|---|
| Clearing at 25 A | **< 1 ms** | **tens to hundreds of ms** — it heats, it does not interrupt |
| Adequate for a −0.3 V abs-max node? | Marginal but the best available | **No — far too slow.** The clamp would carry the fault for the entire trip time |
| If the pack's own protector trips first | Fuse survives; fault self-limits; good outcome | Same |
| Auto-retry behaviour | None — permanent, requires service | **Retries indefinitely**, re-applying the negative excursion to BQ25185 BAT on **every** cycle |
| Reversed-pack interaction | A reversed pack's own protector may not function at all — its VDD is reversed, violating its own −0.3 V limit — so board-level clearing must not depend on it | Same, and worse because of retry |
| Verdict | **RECOMMENDED** | **REJECT for this position** |

The retry behaviour is decisive: a PTC converts a single destructive event into a
repeating one.

### 5.4 Verdicts

| element | verdict | reasoning |
|---|---|---|
| **Fuse (one-shot, fast-acting, ~3 A class)** | **REQUIRED** | Without it the clamp becomes a **permanent short across a Li-ion cell** in F5/F7 — a fire hazard strictly worse than the fault it was added for. The fuse is what makes the clamp safe to fit at all |
| **Clamp (Schottky, cathode to `BAT_PROTECTED_P`, anode to GND)** | **REQUIRED** | 4× reduction in the fault excursion for one cheap part, and it is what holds the node while the fuse clears |
| **PTC in place of the fuse** | **REJECT** | Too slow, and auto-retry re-applies the fault |
| **The pair as proof that F7 is safe** | **NOT ESTABLISHED** | Residual ~−1 V for <1 ms. **P-12.** Resolve by TI confirmation in writing, or by the reverse-insertion bench rig |

**Values are not locked**, per instruction: the fuse rating must come from the
peak system current budget (P-15) and the clamp's surge rating from the chosen
fuse's let-through I²t.

---

## 6. First-five-boards debug provisions

The battery path is safety-critical, so **no parallel 0 Ω bypass across the
protection is proposed** — that would defeat exactly what is being tested.

| provision | include? | reasoning |
|---|---|---|
| **TP `BAT_RAW`** (J4 side of the fuse) | **YES** | Distinguishes "cell is bad" from "fuse is open" |
| **TP `BAT_RAW_F`** (LTC4368 VIN side of the fuse) | **YES** | The two together make fuse state observable without desoldering |
| **TP `BAT_PROTECTED_P`** | **YES** | The node the whole exercise protects |
| **TP `GATE`** | **YES, as a bare pad — not a loop** | ⚠ The charge pump sources only **35 µA**, and I_INRUSH = (C_OUT/C_GATE) × I_GATE(UP): **added probe capacitance directly changes inrush.** A pad plus a documented "probe with ≥10 MΩ / ≤10 pF" note |
| **TP `SENSE` + TP `VOUT`** | **YES, as a differential pair** | Lets the trip point be measured directly rather than inferred. Safe — both are high-impedance sense inputs |
| **TP `FAULT`** | **YES** | Open-drain; reports voltage fault, current fault, SHDN low **and VIN-below-UVLO**, i.e. it directly indicates the dead-cell lockout |
| **TP `SHDN`** | **YES** | **The latch-off recovery mechanism is "toggle SHDN low then high".** Without a test point, clearing a latched forward-OC on the bench means power-cycling the whole board |
| **Series removable link in `BAT_PROTECTED_P`** | **YES — this one is safe** | A link **in series** only *opens* the path; it cannot bypass reverse protection. It lets the charger and the protection be characterised separately. Distinct from a parallel link across the FETs, which is **forbidden** |
| **Parallel 0 Ω across the pass FETs** | **NO — forbidden** | Defeats the protection entirely |

---

## 7. PCAL9535A closeout

### VERDICT: **PASS WITH FIRMWARE CHANGES** — with one evidential bound stated plainly.

**No pin or package incompatibility was found.** The comparison, using the
CTO-supplied PCAL9535A pinout against **TCA9535 PW verified from S8 Figure 5-1**:

| pin | TCA9535 PW (S8, verified) | PCAL9535A (CTO-supplied) | match |
|---|---|---|---|
| 1 | INT | INT | ✓ |
| 2 | A1 | A1 | ✓ |
| 3 | A2 | A2 | ✓ |
| 4–11 | P00–P07 | P0_0–P0_7 | ✓ |
| 12 | GND | VSS/GND | ✓ |
| 13–20 | P10–P17 | P1_0–P1_7 | ✓ |
| 21 | A0 | A0 | ✓ |
| 22 | SCL | SCL | ✓ |
| 23 | SDA | SDA | ✓ |
| 24 | VCC | VDD | ✓ |

**Cross-checked against the board:** every `U2` and `U3` pad-to-net assignment
measured in the pre-design audit matches this table, including A0 = GND on `U2`
(0x20) and A0 = +3V3 on `U3` (0x21).

**Footprint retention in principle: YES.** Both are TSSOP24, 4.4 mm body
(NXP SOT355-1 / TI PW). **This is an architecture conclusion, not a land-pattern
signoff** — exactly as ruling A states. The land pattern must still be audited
against the current NXP package drawing before fabrication.

| item | status |
|---|---|
| All interrupts masked at POR | **Confirmed** — NXP product documentation: *"powers up with all I/O interrupts masked, which allows for a board bring-up free of spurious interrupts at power-up"* |
| Legacy PCA9535 register block retained | **Confirmed** — *"contains the PCA9535 register set of four pairs of 8-bit configuration, input, output and polarity inversion registers"* |
| Agile I/O set | **Confirmed** — programmable output drive strength, latchable inputs, programmable pull-up/pull-down, maskable interrupt, interrupt status register |
| Supply range | 1.65–5.5 V |
| **Pull enables disabled at POR** | **NOT VERIFIED from a primary source** |
| **400 kHz support** | **NOT VERIFIED from a primary source** |
| **Output drive current** | **NOT VERIFIED from a primary source** |
| **Agile I/O command byte addresses** | **NOT VERIFIED from a primary source** |

> **Evidential bound.** The four rows above rest on NXP product-page text, not on
> a page-cited datasheet read, because the PDF could not be retrieved (§0). None
> of them can change the architecture decision — they are firmware and
> bring-up details — but **all four must be closed at the land-pattern audit**,
> which is already a required pre-fabrication gate.

**Both `U2` and `U3` should change**, per the earlier recommendation and now the
ruling. `U3` needs the interrupt mask most: ten of its inputs reach a
user-accessible connector, and on a TCA9535 any chattering accessory input
produces an unmaskable interrupt storm on the shared wake net.

---

## 8. SX1262 DIO1 closeout

### VERDICT: **CONFIRMED.** The rule is exactly as the CTO stated.

**X1, §13.3.4 `ClearIrqStatus`, p. 81, verbatim:**

> *"If a DIO is mapped to one single IRQ source, the DIO is cleared if the corresponding bit in the IRQ register is cleared. If DIO is set to 0 with several IRQ sources, then the DIO remains set to one until all bits mapped to the DIO in the IRQ register are cleared."*

And **X1 §8.3.2**: *"Any of the 3 DIOs can be selected as an output interrupt
source… DIO1 is the generic IRQ line, any interrupt can be mapped to DIO1."*

**DIO1 is level-held, not a pulse.** An expander input with no capture register
can therefore service it safely — the condition (C1) that blocked OPTION G38 in
FBV2-ARCH-002 is **closed**.

Incidental cross-check: X1 §8.3.2 also documents `SetDio2AsRfSwitchCtrl`, which
matches the existing `DIO2_TXEN` net in the design.

### 8.1 Firmware handling contract (documented, not implemented)

1. PCAL9535A `INT` asserts → MCU wakes / is interrupted.
2. Read the PCAL9535A **interrupt status register** to identify the source as the DIO1 input — one read, rather than four port reads across two devices.
3. Read the PCAL9535A **input port** to confirm the DIO1 level.
4. Service the SX1262 over SPI: `GetIrqStatus`.
5. `ClearIrqStatus` with **every** mapped IRQ bit — per §13.3.4, DIO1 stays high until all mapped bits are cleared.
6. **Account for the second PCAL edge.** DIO1 returning low is itself an input transition and will assert `INT` again. Firmware must either treat the falling edge as a no-op after confirming the SX1262 IRQ register is clear, or use the PCAL9535A's per-pin mask to suppress it.
7. Re-arm: unmask the DIO1 input if it was masked during service.
8. **`BUSY` stays directly connected to the ESP32** — it is polled tightly around every SPI transaction and must not go through I²C.

> **Known hazard worth writing into the firmware notes.** Public SX126x driver
> issue trackers document a race where an IRQ arriving between `GetIrqStatus`
> and `ClearIrqStatus` leaves DIO1 high with no new edge. With DIO1 on an
> expander this becomes an I²C-latency-widened window. **Mitigation: after
> clearing, re-read the DIO1 input level and re-service if it is still high** —
> level-driven, not edge-driven. This is a firmware contract, not a hardware
> change.

### 8.2 Result

**LOCKED: `NATIVE_A` = GPIO38, `NATIVE_B` = GPIO47.** `SX1262_DIO1` moves to an
internal PCAL9535A input. GPIO43 is released from the connector and becomes an
internal debug UART test pad.

---

## 9. FBV2-A1 gate reassessment

| # | criterion | status |
|---|---|---|
| 1 | PCAL9535A choice closed | **YES** — ruling A; no incompatibility found (§7) |
| 2 | GPIO38/GPIO47 closed | **YES** — DIO1 level-hold confirmed from primary source (§8) |
| 3 | NFC architecture closed | **YES** — D-055/D-056 |
| 4 | Community power architecture closed | **YES** — D-057/D-058 |
| 5 | 20-pin resource architecture closed | **YES** — D-059/D-062 |
| 6 | **Reverse-protection topology complete, no major new power-tree branch TBD** | **NO** |

### VERDICT: **FBV2-A1 — FAIL.** One item blocks it.

Criteria 1–5 are closed. The reverse-protection topology itself is now
**complete** — every element is specified (§2.4), and two items that previously
blocked it are resolved: **P-13 (inrush/latch) is closed** by L1's design
equation and by the finding that latch-off applies only to forward overcurrent.

**What blocks the gate is the dead-cell recovery branch (P-11).** It is a new
power-tree branch — a qualified path from `SYS` to `BAT_RAW` around the pass
FETs — and the CTO has not chosen between Candidate B (recommended) and
Candidate D (service-only). The two differ by ~10 components and by whether the
branch exists at all, which is precisely "a major new power-tree branch that is
still TBD".

**Per the CTO's own instruction — "Do not pass the gate merely because a
preferred idea exists" — I am not passing it.**

**One decision closes this gate.** If the CTO selects B or D, criterion 6 closes
and FBV2-A1 passes, with P-12 (fault-energy survivability) carried into the
schematic phase as a bench item rather than an architecture blocker, since it
changes no topology.

---

## 10. Corrections to previous work

| prior claim | status | correction |
|---|---|---|
| *"P-13 — latch-off vs hot-insertion inrush is unreconciled, unresolvable on paper"* (FBV2-ARCH-002) | **RESOLVED, and the concern was overstated** | L1 gives I_INRUSH = (C_OUT/C_GATE) × I_GATE(UP) and the explicit inequality I_OC,FWD > I_INRUSH + I_OUT. Inrush is a designed parameter. Separately, **RETRY latch-off applies only to FORWARD overcurrent** — reverse faults auto-recover when VOUT falls 100 mV below VIN. Both halves of the objection fall away |
| *"fuse + Schottky clamp… required, not optional"* stated without energy analysis | **Corrected per ruling D** | Both remain **REQUIRED**, but the pair does **not** prove F7 safe: the clamp holds ≈ −1 V at realistic fault currents against a −0.3 V DC absolute maximum. Now recorded as a candidate defence-in-depth topology with a named residual (P-12) |
| *"a firmware-gated trickle… plus a `BAT_RAW` ADC divider"* (FBV2-ARCH-002 §E.3) | **SUPERSEDED** | The CTO prefers safety not to depend on firmware, and that is the better engineering position. Replaced by a **hardware-qualified** comparator interlock (Candidate B). The ADC divider survives, demoted to **diagnosis only** |
| *"C1 — DIO1 level-hold unverified"* | **CLOSED** | X1 §13.3.4 confirms it verbatim |
| *"PCAL9535A pin table not obtainable"* | **Still true, and now bounded** | The pinout is CTO-supplied and matches the verified TCA9535 PW table. Four secondary-sourced facts are listed in §7 and deferred to the land-pattern audit |
| LTC4368 evidence previously *"product-page only"* | **UPGRADED to primary** | Full datasheet `4368f` retrieved from the Farnell mirror |

---

## 11. Open items

| # | item | blocks |
|---|---|---|
| **P-11** | **Dead-cell recovery: Candidate B or Candidate D?** | **FBV2-A1** |
| P-12 | BQ25185 BAT survivability of a ~−1 V, <1 ms excursion in F7 | schematic-phase bench item |
| P-14 | MAX17048 sense point — cell side vs protected side | schematic |
| P-15 | 3V3 rail budget under simultaneous worst case | schematic |
| P-16 | Repurpose one XGPIO as `ACC_DETECT`? | connector sheet |
| P-17 | ST25R3916 vs ST25R3916B | NFC sheet |
| P-18 | Accessory I²C segmentation — buffer or mux | connector sheet |
| — | PCAL9535A land-pattern + four firmware facts | pre-fabrication gate |
| — | Confirm X1 rule against **V2.2** and the E22-900M22S module datasheet | pre-fabrication gate |
| ~~P-13~~ | ~~Latch-off vs inrush~~ | **CLOSED** (§2.2) |

---

## Sources

- ADI **LTC4368** datasheet `4368f` — [Farnell mirror](https://www.farnell.com/datasheets/2243878.pdf) · [ADI product page](https://www.analog.com/en/products/ltc4368.html)
- Semtech **SX1261/2** Data Sheet **DS.SX1261-2.W.APP Rev. 1.2** — [SparkFun CDN mirror](https://cdn.sparkfun.com/assets/6/b/5/1/4/SX1262_datasheet.pdf) · current revision V2.2 via [Semtech SX1262 product page](https://www.semtech.com/products/wireless-rf/lora-connect/sx1262)
- TI [BQ25185 SLUSF65A](https://www.ti.com/lit/ds/symlink/bq25185.pdf) · [TCA9535 SCPS201E](https://www.ti.com/lit/ds/symlink/tca9535.pdf) · [TPS22950 SLVSFJ2B](https://www.ti.com/lit/gpn/tps22950)
- NXP [PCAL9535A product page](https://www.nxp.com/products/interfaces/ic-spi-i3c-interface-devices/general-purpose-i-o-gpio/low-voltage-16-bit-ic-bus-i-o-port-with-interrupt-and-agile-i-o:PCAL9535A) — **PDF not retrievable from this environment**
- [Independent review FBV2-CTO2-PWRNFC-001](../reviews/2026-08-22-independent-cto-power-nfc-review.md) — advisory
