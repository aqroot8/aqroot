# AQROOT Full Beta v2 — Power / Fault State Table

**Status: MANDATORY ARTEFACT. Must be signed before schematic work begins.**

Date: 2026-08-22 (revised by FBV2-PWR-001); annotated 2026-08-23 after FBV2-S1-001
Task: FBV2-ARCH-002, revised FBV2-PWR-001
Scope: analysis only. No schematic, PCB or hardware file was created or modified
**by this document**.

> ## AQROOT DEMO DELTA — `R75` IS 10 mΩ, AND EVERY TRIP FIGURE BELOW IS A TYPICAL (D-771, 2026-09-19)
>
> **Every "3.33 A trip" in this document is `50 mV / 15 mΩ`, and both terms have
> moved.**  ADI's LTC4368 Rev C Electrical Characteristics guarantees `ΔVSENSE,F`
> — the forward overcurrent fault threshold — only as **40 / 50 / 60 mV** over the
> full operating temperature range at `VOUT = VIN`.  50 mV is a **TYPICAL**, and
> this repository had used it as a limit everywhere.  At `R75` = 15 mΩ ± 1 % the
> breaker's real band was **2.640 – 4.040 A**, which **OVERLAPPED** the
> `BQ25185`'s own `IBAT_OCP` band of **2.5625 – 3.6875 A** by 1.05 A.  `RETRY` is
> grounded here, so the LTC4368 breaker **LATCHES OFF** and is cleared only by
> toggling `SHDN`, while `IBAT_OCP` **hiccups and auto-retries** — so on an unlucky
> unit the *latching* protection fired before the *recoverable* one.
>
> **On AQROOT Demo `R75` is 10 mΩ** (Bourns `CRA2512-FZ-R010ELF`, same series,
> same 2512 land, same 3 W) and the breaker band is **3.960 / 5.000 / 6.061 A** —
> entirely above `IBAT_OCP`'s 3.6875 A maximum.
>
> **NO CASE IN THIS TABLE CHANGES ITS VERDICT, AND EVERY MARGIN IN IT IMPROVES.**
> Case 11 / F9 hot insertion: 350 mA of designed inrush against a **3.960 A**
> guaranteed minimum rather than a 3.33 A typical — **11.3× instead of 9.5×**.
> Case 10: ~35 mA against the same.  `F1` is still a 5 A backstop that must not
> pre-empt the breaker, and it does not: ordering against a one-shot fuse is a
> **time–current** result (`tp(GATE)` 3–18 µs against 5 s at 200 % of rating), not
> a threshold comparison.  The reverse threshold scales with the shunt in the same
> way: −42/−50/−58 mV gives **4.16 – 5.86 A**, far above any charge current this
> board programs (`ICHG` 769 mA).  The dated analyses below are retained verbatim
> as the primary-source record.

> ## AQROOT DEMO DELTA — `STAT2` IS NOT LANDED, AND THE SCHEMATIC'S DECODE WAS INVERTED (D-742, 2026-09-18)
>
> **This document analyses the Full Beta v2 topology, in which BOTH `BQ25185`
> status pins are landed.  On the AQROOT Demo board that is not true.**
>
> `U11.3` (`STAT2`) ships **UNCONNECTED** on AQROOT Demo by owner decision of
> 2026-09-17.  D-734 proved the land has no escape at any manufacturable width
> and D-741 re-measured the binding window as **exactly 0.100 mm** — between
> D-269's clearance to `U11.2`'s `BAT` escape and `U11.4`'s `GND` land — against
> this board's published 0.200 mm minimum width.  The window is set by the
> DLH0010A pinout (`BAT` is pin 2, `STAT2` pin 3), so it moves with neither
> placement nor rotation.  `R128` and `TP7` are retained so the signal stays
> probeable for bench work and a Rev-B respin.
>
> **THIS TABLE HAD THE DECODE RIGHT AND THE SCHEMATIC DID NOT.**  Row 189 here
> reads *"charging; `STAT1` HIGH, `STAT2` LOW"*, which matches **SLUSF65B
> (August 2026) §6.3.10 Table 6-2** exactly.  The `R127`/`R128` schematic notes
> claimed the opposite — *"`STAT1` LOW = charging; `STAT1` HIGH with `STAT2` LOW
> = fault"* — citing a "Table 7-2" that is not a status table.  D-742 corrected
> the schematic to agree with this document.  The datasheet is now in the
> repository at
> `hardware/demo/kicad/aqroot-demo/vendor/BQ25185/ti-bq25185-slusf65b-2026-08.pdf`.
>
> **What is UNCHANGED by the NC.**  Nothing in the protection architecture.
> `STAT2` is an open-drain *status* output and SLUSF65B Table 4-1 explicitly
> permits leaving it floating when unused.  Charge control, power path, `TS`
> bias, `ILIM`/`VSET`, the `LTC4368`/`Q2`/`Q3` reverse-protection stage, `F1`,
> the dead-cell recovery branch and every D-269 / D-186 requirement are
> untouched.  `STAT1` **is** routed, to `U3.P17`.
>
> **What the Demo can and cannot observe.**
>
> | `STAT1` alone | AQROOT Demo verdict |
> |---|---|
> | **LOW** | **charger FAULT — directly observed.**  Recoverable (`VIN_OVP`, `TS` HOT/COLD, `TSHUT`, system short) versus non-recoverable (`ILIM`/`ISET` short, `BATOCP`, safety-timer expiry) is **not** distinguishable |
> | **HIGH** | not faulted; **ambiguous** between *charging* and *charge complete / sleep / charge disabled* |
>
> So the Demo **keeps fault detection and loses the charging-versus-complete
> distinction** — the opposite way round from the assumption D-734 and the owner
> decision were written under, because both were working from the inverted table.
>
> **Case 3 (no battery + USB)** below says `STAT2` toggles while `STAT1` stays
> stable.  On Demo that toggle is **not observable**; `STAT1` simply stays HIGH,
> which is the same thing it does when charging or complete.
>
> **Firmware rule.**  Surface `STAT1` LOW as a charger fault.  Label any
> charging-versus-complete claim — built from `VBUS_PRESENT`, `STAT1` history,
> `MAX17048` voltage-and-SOC trend or elapsed time — as an **INFERENCE**.
>
> **Open item 4 of the unresolved list below — "No-battery `STAT2` toggle rate"
> — is CLOSED FOR DEMO as un-measurable on this revision** and is carried to
> Rev-B with the `STAT2` routing item.  Rev-B needs a charger whose `STAT2` pin
> is not adjacent to `BAT`, or a package with a land taller than 0.200 mm.


> ## Capture note — FBV2-S1-001 (2026-08-23)
>
> **The topology this table analyses is now CAPTURED**, in
> `hardware/beta-v2/kicad/aqroot-beta-v2/01_power_tree.kicad_sch`: `U18` LTC4368-1,
> `Q2`/`Q3` as the P2 pass path in two packages, `R75` 15 mΩ *(10 mΩ on AQROOT Demo since D-771)*, `F1` 5 A, `D9` secondary
> clamp, and the full Candidate-B recovery branch on `U19`. **This table remains the
> authority for behaviour** — the capture does not supersede a single case, and no case
> has been re-derived against the captured values.
>
> **Two captured values differ from the numbers analysed here and are NOT ratified:**
> `R95` = **680 R** against `R_LIM` **560 R** (recovery injection ≈ 6.9 mA rather than
> ≈ 8.4 mA — **P-20**, and it moves the wrong way against **B-26**), and the `OV` trip
> captured at **5.05 V** against the documented ≈ 4.6 V (**P-21**). **Any case whose
> outcome depends on either number must be re-checked once they are ruled on.**
>
> The one structural detail worth adding to the record: `LTC4368_FAULT_N` carries **both**
> `R81` 1 M to `+3V3` and `R82` 1 M to GND. With a dead pack there is no `+3V3`, so the
> node sits at 0 V, `Q9` is off and recovery is **enabled** — the branch does not depend
> on the rail it exists to restore.
>
> Analysis: [`../audits/2026-08-23-s1-power-tree-implementation.md`](../audits/2026-08-23-s1-power-tree-implementation.md).

> ## Revision note — FBV2-PWR-001
>
> The full **LTC4368 datasheet (`4368f`)** was obtained after this table was first
> written, and it changes two entries. Both are recorded here rather than
> silently edited:
>
> - **Case 11 / F9 (hot insertion) is no longer UNRESOLVED.** Inrush is a designed
>   parameter: `I_INRUSH = (C_OUT / C_GATE) × I_GATE(UP)` with `I_GATE(UP)` = 35 µA,
>   and the datasheet states the design inequality `I_OC,FWD > I_INRUSH + I_OUT`.
>   With C_OUT ≈ 10 µF and C_GATE = 1 nF, inrush ≈ **350 mA** against a 3.33 A
>   trip. There is also a **32 ms gate turn-on delay** (t_D(ON) 22/32/45 ms).
> - **Latch-off does not trap a corrected reversed cell.** RETRY latching applies
>   to **forward** overcurrent only; after a **reverse** current fault the part
>   reconnects automatically once VOUT falls 100 mV below VIN. The two mechanisms
>   are independent.
>
> **P-13 is CLOSED.** Case 4 (dead cell) remains the blocker. See
> [`../audits/2026-08-22-battery-protection-closeout.md`](../audits/2026-08-22-battery-protection-closeout.md).

> ## Revision note 2 — FBV2-PWR-002 · **ALL 13 CASES NOW DEFINED**
>
> The architecture changed in three ways that resolve the two remaining open
> cases. Earlier text below is **retained as the historical record** and is
> superseded by this note and by
> [`../audits/2026-08-22-dead-cell-and-single-fault-closeout.md`](../audits/2026-08-22-dead-cell-and-single-fault-closeout.md).
>
> 1. **Pass path is now P2** — two back-to-back stages in **two separate
>    packages** (4 FETs). Any single D-S short leaves one complete pair intact, so
>    a reversed cell is **isolated** rather than clamped. **Case 7/8 is solved by
>    prevention, not by fault-clearing time.**
> 2. **Dead-cell recovery exists** — an autonomous, hardware-qualified branch from
>    VBUS, gated by a ratiometric polarity comparator, a handoff comparator and the
>    LTC4368 `FAULT` pin. **Case 4 is solved.** No firmware involvement.
> 3. **Clamp demoted, fuse resized.** The clamp is **secondary** (ESD /
>    transient / double-fault) — the previous claim that a Schottky protects a
>    −0.3 V absolute maximum was **not a valid compliance argument and is
>    withdrawn**. The fuse moves **3 A → ≈5 A** because it is now a backstop that
>    must not pre-empt the 3.33 A electronic breaker.
>
> **P-12 is largely retired**: under P2 the negative excursion does not occur
> under any single fault. **All 13 cases have defined safe behaviour.**

---

## CURRENT CASE SUMMARY (FBV2-PWR-002)

| # | case | behaviour | status |
|---|---|---|---|
| 1 | Normal battery, no USB | Both stages on (~55 mΩ); recovery branch unpowered, **zero standby draw** | **OK** |
| 2 | Normal battery + USB | Charge current passes (reverse direction, −50 mV threshold — the `-1` suffix); `FAULT` released → recovery off | **OK** |
| 3 | No battery + USB | Runs from USB; BQ25185 no-battery limit cycle, **STAT2 toggles** (maskable on PCAL9535A); recovery parks at the ~2.8 V handoff bound — slow, low-duty, ≤8 mA into an open node | **OK** |
| 4 | **0 V / dead battery + USB** | **Recovery ON at ~8 mA** → cell rises → LTC4368 closes at ~2.2 V → `FAULT` releases → recovery OFF → BQ25185 precharges | **OK — SOLVED** |
| 5 | Pack protection-open + USB | Terminals ≈0 V → recovery ON; most 1S protectors release on charger-voltage detect. ⚠ Verify the chosen pack's release current against 8 mA | **OK, one part-dependent caveat** |
| 6 | Reversed battery, no USB | GATE auto-tied to negative VIN; both stages block; recovery unpowered | **BLOCKED correctly** |
| 7 | Reversed battery + USB | Both stages block; comparator A holds recovery off; **board boots from USB** so the fault is diagnosable | **OK** |
| 8 | **One pass FET short + reversed battery + USB** | Surviving back-to-back stage **isolates**; `BAT_PROTECTED_P` never goes negative; the electronic breaker remains functional | **OK — SOLVED by isolation** |
| 9 | **Recovery switch stuck on + reversed battery + USB** | `R_LIM` bounds to **≈13 mA (~0.007 C)**; `D_REC` keeps the branch unidirectional; self-annunciating | **BOUNDED — not a high-current path** |
| 10 | Battery inserted while USB present | 32 ms turn-on delay debounces; C_GATE 4.7 nF bounds inrush to ~35 mA against a 3.33 A trip | **OK** |
| 11 | **USB removed during dead-cell recovery** | VBUS collapses → `Q_REC` source at 0 V → V_GS = 0 → **OFF**; `D_REC` independently blocks any pack drain | **OK — clean stop** |
| 12 | Accessory short while enabled | TPS22950-Q1 current limit + auto-retry + thermal shutdown; core `+3V3` holds | **OK** |
| 13 | Externally powered accessory, AQROOT off | TPS22950-Q1 reverse blocking active while disabled; TCA9517A high-Z when unpowered; **no permanent raw `+3V3` pin exists** | **OK** |

**13 of 13 defined. No case is architecture-undefined.**

---

---

## Purpose and reading rules

This table exists because the programme may skip Lean Beta-DM bring-up and
fabricate roughly five Full Beta v2 PCBAs directly. Every cell below is either
derived from a manufacturer document, or it is explicitly marked
**UNRESOLVED — BLOCKS SCHEMATIC LOCK**.

**A cell that cannot be filled in from a datasheet sentence is a bench
experiment, not a schematic decision.** Do not close one by reasoning about it.

### Architecture this table analyses

```
                    ┌──────────────── USB-C 5 V ── USBLC6 ── VBUS_RAW ── VBUS_CHG ──┐
                    │                                                                │
  CELL ── J4 ── [3 A FUSE] ── BAT_RAW ──┬── [SCHOTTKY CLAMP to GND]                 │
                                        │                                            │
                                        └── LTC4368-1 + FDS6898A ──── BAT_PROT ──┐   │
                                            (VIN = cell side)                    │   │
                                                                          BQ25185 BAT / IN
                                                                                 │
                                                                          BQ25185 SYS
                                                                                 │
                                                        SW9 hard switch ── TPS63020 EN
                                                                                 │
                                                                              +3V3
                                                                                 │
                                                            TPS22950-Q1 ──── ACC_3V3_SW
```

Elements marked in that diagram are **proposed**, not approved. The fuse, the
clamp and the dead-cell recovery path are the subject of §3 below and are open
CTO decisions (**P-11**, **P-12**).

### Legend

| symbol | meaning |
|---|---|
| **OK** | Behaviour is specified by a manufacturer document and is acceptable |
| **DEGRADED** | Works, but with a documented penalty the user or service may notice |
| **BLOCKED** | Deliberately prevented by a protection element working as designed |
| **UNRESOLVED** | Not derivable from any document obtained. **Blocks schematic lock.** |
| — | Not applicable in this state |

---

## 1. Device states analysed

| axis | states |
|---|---|
| USB | absent · present |
| Battery | good (3.0–4.35 V) · absent · deeply discharged / protector open / ~0 V · reversed |
| Power state | normal enabled (SW9 closed) · hard-off (SW9 open) |
| Accessory | absent · normal · shorted · externally powered while AQROOT is off |

---

## 2. The eleven explicit cases

### Case 1 — Normal battery, no USB, SW9 closed

| node | state |
|---|---|
| `BAT_RAW` (cell connector) | 3.0–4.35 V |
| Fuse | intact |
| Schottky clamp | reverse-biased, non-conducting |
| LTC4368 | VIN above UVLO (1.8–2.4 V rising); both gates enhanced; ~80 µA operating |
| `BAT_PROT` / BQ25185 BAT | cell voltage minus I × ~51 mΩ |
| BQ25185 IN | 0 V |
| BQ25185 SYS | battery-only mode, SYS follows BAT |
| `+3V3` | 3.3 V (TPS63020 boosting from ~3.0–4.2 V) |
| `ACC_3V3_SW` | 0 V until firmware asserts ON |
| VBUS | 0 V |
| Charger | not charging (no input) |
| Boot | **OK** — normal boot |
| Reverse current allowed | none |
| Service action | none |

### Case 2 — Normal battery + USB, SW9 closed

| node | state |
|---|---|
| `BAT_RAW` | cell voltage, rising under charge |
| LTC4368 | both gates enhanced; **must pass current INTO the cell** — this is why the **-1** suffix is mandatory |
| `BAT_PROT` / BQ25185 BAT | cell voltage plus charge current × ~51 mΩ |
| BQ25185 IN | ~5 V |
| BQ25185 SYS | ~4.5 V, adapter mode |
| `+3V3` | 3.3 V |
| VBUS | 5 V |
| Charger | charging; STAT1 HIGH, STAT2 LOW |
| Boot | **OK** |
| Reverse current allowed | charge current is *forward* for the cell and *reverse* through the LTC4368's sense element. **LTC4368-2 would open here and never charge.** |
| Service action | none |

> **This case is the single most important reason the `-1` suffix is load-bearing.**
> Per the independent review: LTC4368-1 trips at ±50 mV symmetric; LTC4368-2 trips
> at −3 mV, which is ideal-diode behaviour and opens as soon as charge current
> flows. A `-2` fitted here produces a board that discharges normally and never
> charges. The suffix must appear in the schematic symbol, the BOM, the assembly
> note and the bring-up checklist.

### Case 3 — No battery + USB, SW9 closed

| node | state |
|---|---|
| `BAT_RAW` | open circuit |
| LTC4368 | VIN below UVLO → **both gates off**; the controller is unpowered from the cell side |
| `BAT_PROT` / BQ25185 BAT | capacitive node only |
| BQ25185 SYS | ~4.5 V from IN — **device runs from USB** |
| `+3V3` | 3.3 V |
| Charger | **limit cycle.** SLUSF65A §7.3.10: *"When no battery is present, the device charges the capacitor on the BAT pin and toggles between charging and charge completed states. During this condition, the STAT1 pin remains stable, while the STAT2 pin toggles between HIGH and LOW."* |
| STAT1 / STAT2 | STAT1 **HIGH stable**; STAT2 **toggles** |
| Expander `/INT` | With TCA9535: **unmaskable interrupt storm** on the shared wake net. With PCAL9535A: maskable per pin. |
| Boot | **OK**, but see below |
| Service action | none |

> **DEGRADED with TCA9535, OK with PCAL9535A.** This is the concrete case that
> justifies the expander change. **Toggle rate is UNRESOLVED** — TI publishes no
> frequency because it has none; it is set by C<sub>BAT</sub>, I<sub>CHG</sub> and
> down-slope leakage. **Measure it on the bench.**
>
> **Important consequence for Case 3 vs Case 4:** the same limit cycle fires in
> *any* condition where BAT is capacitive — including whenever the new series
> protection FETs are open. So Cases 3, 4 and 6 all present identically to
> firmware unless a separate raw-battery sense exists.

### Case 4 — Dead / ~0 V battery + USB, SW9 closed

| node | state |
|---|---|
| `BAT_RAW` | ~0 V (over-discharged cell, or protected pack whose internal protector has latched open) |
| LTC4368 | **VIN below UVLO (1.8–2.4 V rising, 2.5 V minimum operating) → both gates OFF.** Body diodes are anti-series, so **nothing flows in either direction.** |
| `BAT_PROT` / BQ25185 BAT | isolated from the cell |
| BQ25185 SYS | ~4.5 V from IN — device runs from USB |
| Charger | sees a capacitive BAT node; runs the Case-3 limit cycle. **It cannot charge the cell — there is no path to it.** |
| Boot | **OK** — runs from USB |
| Charging expectation | **BLOCKED. The pack can never be revived by this board.** |
| Service action | **REQUIRED** |

> ### ⚠ UNRESOLVED — BLOCKS SCHEMATIC LOCK
>
> **This is a new failure mode created by adding the protection**, and the
> independent review judges it the most likely field failure in the whole Q1
> proposal. The user-visible symptom is *"my AQROOT killed the battery."*
>
> Three candidate recovery architectures are analysed in §3. **None is approved.**
> Until one is chosen, Case 4 has no defined behaviour and the power tree cannot
> be drawn. Tracked as **P-11**.
>
> **Do not invent a dead-cell solution.** The CTO instruction on this point is
> explicit and is respected here: §3 presents options and a recommendation, and
> stops.

### Case 5 — Reversed battery, no USB, SW9 closed or open

| node | state |
|---|---|
| `BAT_RAW` | **−3.0 to −4.35 V** |
| Fuse | intact (no current path to blow it) |
| Schottky clamp | **forward-biased**, holds `BAT_RAW` at roughly −0.35 V and sinks the cell's short-circuit current → **the fuse opens** |
| LTC4368 | VIN negative. ADI Rev. C: *"When VIN goes negative, the reverse VIN comparator closes the internal switch, which in turn connects the gates of the external MOSFETs to the negative VIN voltage… M2 will be turned off and no current can flow from VOUT to VIN."* **Both gates off.** |
| `BAT_PROT` / BQ25185 BAT | **0 V. Protected.** |
| BQ25185 SYS | 0 V |
| `+3V3` | 0 V |
| Boot | **BLOCKED** — device does not power on. Correct. |
| Reverse current allowed | none past the clamp/fuse |
| Service action | **REQUIRED** — fuse replacement, cell re-terminated |

> The clamp-plus-fuse pair is what converts this from "silent" to "serviceable".
> Without the fuse the clamp diode sinks cell short-circuit current indefinitely
> and becomes the failure.

### Case 6 — Reversed battery + USB, SW9 closed — **MANDATORY FAULT CASE**

| node | state |
|---|---|
| `BAT_RAW` | −3.0 to −4.35 V, clamped to ~−0.35 V by the Schottky while the fuse opens |
| Fuse | **opens** |
| LTC4368 | reverse-VIN comparator ties both gates to the negative VIN → **both FETs off**, DC blocking engaged |
| `BAT_PROT` / BQ25185 BAT | **0 V — must never go below −0.3 V** |
| BQ25185 IN | ~5 V |
| BQ25185 SYS | ~4.5 V from USB |
| `+3V3` | 3.3 V |
| Boot | **OK — the device boots and runs from USB.** This is what makes the fault diagnosable rather than silent. |
| Charging expectation | none; charger sees a capacitive/open BAT and runs the limit cycle |
| Service action | **REQUIRED** — fuse and cell |

> **Why the orientation is not an implementation detail.** The documented DC
> blocking mechanism lives on the **VIN** pin. `VIN` must be the **cell side**.
> Wire VIN to SYS instead and the mechanism never engages; protection then
> depends on the microsecond overcurrent trip, which is a race rather than a
> state.
>
> **Firmware requirement:** with a `BAT_RAW` divider to an ESP32 ADC, firmware can
> distinguish *no cell* / *dead cell* / *reversed cell* — which Cases 3, 4 and 6
> otherwise present identically. The divider needs ≥100 kΩ series plus a Schottky
> clamp to GND so a negative node clamps at −0.3 V at microamps.

### Case 7 — One reverse-protection pass MOSFET shorted + reversed battery + USB — **MANDATORY FAULT CASE**

| node | state |
|---|---|
| Failure assumed | drain-source short on one FET of the dual — **the dominant MOSFET failure mode** |
| LTC4368 | gates driven off, but **a shorted FET cannot be turned off**. The controller is defeated. |
| Path | cell → shorted FET → remaining FET's body diode → `BAT_PROT` |
| **Without fuse + clamp** | **−3.0 to −4.35 V lands directly on BQ25185 BAT.** Abs max on BAT is −0.3 V. **A DC violation by a factor of 10–14. The charger is destroyed.** |
| **With fuse + clamp** | Schottky holds `BAT_RAW` at ~−0.35 V while the 3 A fuse opens. BQ25185 BAT sees a **brief excursion to roughly −0.35 V** instead of a sustained −3.7 V. |
| Boot | OK from USB after the fuse opens |
| Service action | **REQUIRED** |

> ### This case is why the fuse and clamp are not optional
>
> The CTO requirement reads: *"must not allow a single plausible
> protection-component failure to place meaningful negative voltage onto BQ25185
> BAT without another protection mechanism clearing or limiting the fault."*
>
> **LTC4368 + FDS6898A alone does not meet that requirement.** A protection
> scheme whose single-point failure reproduces the exact fault it guards is not
> defence in depth. The fuse clears and the clamp limits. Both are required for
> the stated requirement to be true.
>
> **Residual risk, stated honestly:** the excursion is brief but not zero, and its
> duration is set by the fuse's I²t against the cell's short-circuit current.
> **Whether −0.35 V for that duration is survivable for the BQ25185 is UNRESOLVED**
> — the abs-max table gives a DC limit, not an energy limit. This is a bench
> measurement (reverse-insertion rig), not a datasheet lookup. Tracked as **P-12**.

### Case 8 — Accessory short while the switched rail is enabled

| node | state |
|---|---|
| `ACC_3V3_SW` | shorted to GND by the accessory |
| TPS22950-Q1 | current limit engages at R<sub>ILIM</sub>-set threshold; **auto-retry**; thermal shutdown at 170 °C; `FLT` pulled low |
| `+3V3` | **holds.** The switch limits before the TPS63020's 2 A limit is reached |
| Core rail | **OK — does not collapse** |
| Expander | `FLT` on an input (recommended) lets firmware report "accessory fault" |
| Boot / operation | unaffected |
| Service action | user unplugs the accessory |

> **This case is why TPS22918 had to go.** It has no current limit and no thermal
> shutdown, so an accessory short pulled whatever the TPS63020's 2 A limit would
> deliver until something gave up — the exact self-damage case the connector
> exists to survive.
>
> **Note on the CTO's ~500 mA target:** TPS22950**C**'s adjustable I<sub>LIM</sub>
> range is **0.5 A – 3.5 A** (SLVSFJ2B §5). A 500 mA setting therefore sits at the
> **extreme bottom of the range**. The base TPS22950 goes down to 0.05 A but is
> WCSP-only, which fails the leaded-package requirement. **Recommend 600–800 mA**
> and treat 500 mA as the floor, not the target.
>
> **D-765 — THIS PARAGRAPH WAS RIGHT AND WAS NOT READ.** D-753 later programmed
> **0.407 A**, below the 500 mA this note calls *the floor*, on the `C` variant,
> citing the same `SLVSFJ2B`. The paragraph is retained verbatim above because it
> is the primary-source record. What it did not consider is the **`TPS22950-Q1`**
> (`SLVSGP6A`, orderable `TPS22950CQDDCRQ1`): specified `ILIM` **0.05–3.5 A**
> *and* **leaded** — the same `DDC0006A` SOT-23-THIN package — so it satisfies
> both constraints this note treated as mutually exclusive. `U20`/`U22` are the
> `-Q1` now, the 2.7 kΩ / 0.407 A setting is in specification, and
> `demo_feature_contract.py` **F6** refuses any `ILIM` outside the fitted part's
> own published range.
>
> **D-771 — AND THE SETTING MOVED AGAIN, THIS TIME TOWARD THIS NOTE.**  The
> 600–800 mA recommendation above was written against the `C` variant's 0.5 A
> floor, which the `-Q1` retires.  What forced the setting up instead was D-098's
> PUBLISHED budget: at 2.7 kΩ each rail **GUARANTEED only 0.277 A** against a
> published 400 mA / 300 mA.  `R97` is now **1.78 kΩ (0.636 A typ, 0.428 A
> guaranteed)** — inside this note's own 600–800 mA recommendation — and `R101`
> **2.32 kΩ (0.479 A typ, 0.322 A guaranteed)**, which is below it because the
> 5 V rail costs 1.875 A of pack current per amp delivered and its worst case
> already sits 5.6 % under `IBAT_OCP`'s minimum.  `F6` now also refuses a setting
> that does not GUARANTEE its rail's published budget, and one its converter
> cannot source.

### Case 9 — Externally powered accessory while AQROOT is off

| node | state |
|---|---|
| `ACC_3V3_SW` | driven to ~3.3 V (or higher) by the accessory |
| TPS22950-Q1 | **reverse current blocking, always active including while disabled** (SLVSGP6A §1: always-on TRUE RCB; 44 mV activation, 16 mV release, 3 µs, 38 µA reverse leakage). Comparator opens the pass FET. |
| `+3V3` | **not back-powered** |
| AQROOT | stays off. **Correct.** |
| Residual | RCB is a comparator (~44 mV / ~900 mA, ~3 µs response), **not** a back-to-back blocking pair. A back-powering accessory can push a few hundred mA for a few microseconds before it acts. Reverse leakage while off is specified at 38 µA. |
| External I²C | `U16` unpowered on its B-side → both sides high-Z (SCPS245E: *"High-impedance I²C pins when powered-off"*, and all I/Os tolerant to 5.5 V *"even when the device is unpowered"*) |
| Service action | none |

> **⚠ This case is only OK once the permanent raw `+3V3` connector pin is
> removed.** With that pin present, an externally powered accessory back-feeds the
> system rail directly, with no current limit, no reverse blocking and no fuse —
> and everything fitted on the switched pin is irrelevant. **CTO ruling C removes
> it (D-049).** Case 9 is marked OK **conditional on that removal.**
>
> **Absolute maximum on the switch is 5.5–6 V.** An accessory applying 5 V
> survives; one applying 12 V does not. Both power pins want a TVS at the
> connector.

### Case 10 — USB attached while the Power switch (SW9) is off

| node | state |
|---|---|
| SW9 | open → TPS63020 `EN` low → **`+3V3` = 0 V** |
| BQ25185 IN | ~5 V |
| BQ25185 SYS | ~4.5 V (SW9 gates the regulator enable, not SYS) |
| Charger | **charges normally** — charging does not depend on SW9 |
| `+3V3` | 0 V |
| `ACC_3V3_SW` | 0 V (source rail absent) |
| ESP32-S3 | unpowered |
| Boot | **BLOCKED by design.** Correct — SW9 is a hard-off that a hung firmware cannot override |
| Service action | none |

> **OK, and worth stating as a product behaviour:** the unit charges with the
> power switch off. That is the expected consumer behaviour and it falls out of
> the existing architecture for free.
>
> **Verify at bring-up:** that SYS rising with `+3V3` held at 0 V leaves no
> ESP32-S3 pin biased through a protection diode from any rail that *is* up.

### Case 11 — Battery inserted while USB is already present

| node | state |
|---|---|
| Before insertion | Case 3 — running from USB, BAT node capacitive, STAT2 toggling |
| At insertion | `BAT_RAW` steps from ~0 V to cell voltage |
| LTC4368 | VIN crosses UVLO → controller powers up → gates enhance. **Inrush:** the cell charges `BAT_PROT`'s capacitance through the FETs |
| Overcurrent | if inrush exceeds the ±50 mV sense trip (±2.5–3.3 A at 15–20 mΩ), the LTC4368 **trips** |
| Retry behaviour | **RETRY strapped for latch-off** (recommended) → a trip requires a power cycle to clear |
| Charger | limit cycle stops; normal charging begins; STAT1 HIGH, STAT2 LOW |
| Boot | **OK** |
| Service action | none expected |

> ### ⚠ UNRESOLVED — BLOCKS SCHEMATIC LOCK
>
> **[SUPERSEDED 2026-08-22 by FBV2-PWR-001 — P-13 CLOSED. Text retained as the
> historical record; the reasoning below was based on an incomplete reading of
> the LTC4368 and is no longer the position.]**
>
> **Latch-off and hot-insertion interact badly and the brief has not reconciled
> them.** Latch-off is right for a reversed cell (the board should stop, not
> chatter). But if hot-insertion inrush trips the same latch, a user who plugs the
> battery in with USB connected gets a board that appears dead until it is power
> cycled.
>
> The trip threshold, the `BAT_PROT` capacitance and the resulting inrush are all
> design values that do not exist yet, so **this cannot be resolved on paper.**
> Options are (a) size the sense resistor so inrush stays under the trip, (b) add
> series inrush limiting, or (c) accept auto-retry and lose latch-off on the
> reversed-cell case. Tracked as **P-13**.

> ### ✅ CURRENT POSITION — Case 11 is OK. P-13 CLOSED.
>
> Two facts from the LTC4368 datasheet (`4368f`) dissolve the concern:
>
> 1. **Inrush is a designed parameter.** `I_INRUSH = (C_OUT / C_GATE) × I_GATE(UP)`
>    with I_GATE(UP) = 35 µA, and the datasheet states the design inequality
>    `I_OC,FWD > I_INRUSH + I_OUT`. At C_OUT ≈ 10 µF and **C_GATE = 1 nF**, inrush
>    ≈ **350 mA** against a **3.33 A** trip (R_SENSE = 15 mΩ) — better than 9×
>    margin. The VIN pin is explicitly **hot-swappable**.
> 2. **The two mechanisms are independent.** RETRY latch-off applies to **forward**
>    overcurrent only. After a **reverse** current fault the part reconnects
>    **automatically** once VOUT falls 100 mV below VIN. Grounding RETRY therefore
>    does not trap the board once a reversed cell is corrected.
>
> A **32 ms gate turn-on delay** (t_D(ON) 22/32/45 ms) additionally debounces
> insertion. The only carry-forward is that **C_GATE must be sized in the
> schematic**, and `R_GATE = 22 kΩ` per the datasheet's recommendation.

---

## 3. Dead-cell recovery — three candidate architectures

Required because Case 4 has no defined behaviour. **None is approved.** Every
candidate below is tested against the mandatory fault: **reversed battery + USB
present**.

| | **R1 — firmware-gated trickle across the FETs** | **R2 — permanent high-value resistor across the FETs** | **R3 — no recovery; service-only** |
|---|---|---|---|
| Mechanism | ~10 kΩ in series with a small FET, from `BAT_PROT` to `BAT_RAW`, default **off**. Firmware closes it after reading a `BAT_RAW` ADC divider and confirming the node is positive and low | Fixed ~10 kΩ permanently bridging the pass FETs | Pack is replaced or externally revived |
| Current delivered | ~450 µA — enough to lift VIN over the 1.8–2.4 V UVLO and hand control back to the LTC4368 | same | — |
| Reversed cell + USB | **PASSES.** The gate is off by default, and firmware refuses to close it because the ADC reads negative (clamped to −0.3 V). Even if closed, ~450 µA into a reversed cell is harmless | **FAILS the intent.** The resistor is unconditional, so USB-side voltage is permanently applied across a reversed cell through 10 kΩ. Current is tiny, but it is *charging a reversed cell*, which the CTO instruction rejects outright | **PASSES** trivially |
| Defeats reverse protection? | No — the LTC4368 path is untouched; this is a parallel µA-scale path under firmware control | Marginally — it is a permanent leakage path around the protection | No |
| Places negative voltage on BAT? | No | No (10 kΩ limits to µA) | No |
| Standby cost | ~0 when off | continuous leakage between `BAT_PROT` and `BAT_RAW` | 0 |
| Parts | 1 small FET, 2 resistors, + ADC divider (2 R + 1 Schottky) | 1 resistor | 0 |
| Failure mode | FET short → becomes R2 | — | user-visible dead product |
| Verdict | **RECOMMENDED** | **REJECT** — unconditional path around a safety element | Acceptable fallback only if R1 is judged too complex |

**Recommendation: R1**, paired with the `BAT_RAW` ADC divider — which is needed
anyway to make Cases 3, 4 and 6 distinguishable to firmware. **Not approved;
tracked as P-11.**

> **Bench requirement.** R1's premise — that ~450 µA actually lifts a real
> over-discharged pack over UVLO — is arithmetic, not a measurement. The
> reverse-insertion rig must demonstrate that the recovery trickle recovers a 0 V
> pack. Until it does, R1 is a plan, not a solution.

---

## 4. Fuse and clamp analysis

| condition | both FETs healthy | one FET shorted |
|---|---|---|
| **Normal discharge** | Fuse carries load current; clamp reverse-biased. Fuse must be rated above peak system current with margin | Same — a shorted FET is electrically invisible in normal operation |
| **Normal charging** | Fuse carries charge current; clamp reverse-biased | Same |
| **Reversed cell** | Clamp conducts, fuse opens (Case 5) | Clamp conducts, fuse opens (Case 7) — **this is the case the pair exists for** |

**Recommendation:**

| item | class | placement | rationale |
|---|---|---|---|
| **Fuse** | Fast-acting, ~3 A, in **series with the cell positive** | At the cell connector, **before** everything else | Must clear before the clamp diode is destroyed |
| **Clamp** | Schottky, cathode to the `BAT_RAW` net, anode to GND | At the cell connector, adjacent to the fuse | Low V<sub>f</sub> keeps the excursion near −0.35 V |

**Required, not optional** — Case 7 is a stated CTO requirement and is not met
without them. **Values are not locked**; the fuse rating must be derived from the
peak system current budget, and the clamp's surge rating from the fuse's I²t.

---

## 5. Summary — what blocks schematic lock

| # | unresolved item | case | tracked as |
|---|---|---|---|
| 1 | **Dead-cell recovery architecture not chosen** | 4 | **P-11** |
| 2 | **BQ25185 BAT survivability of a brief −0.35 V excursion** — abs max is a DC limit, not an energy limit | 7 | **P-12** |
| ~~3~~ | ~~Latch-off vs hot-insertion inrush interaction~~ | 11 | **P-13 — CLOSED by FBV2-PWR-001** |
| 4 | **No-battery STAT2 toggle rate** — TI publishes none; decides how urgent the expander change is | 3 | measure |
| 5 | **MAX17048 sense point** — cell side (exposed to the reversed-cell fault) vs protected side (~51 mΩ of uncompensable IR drop; ~51 mV at 1 A, several % SOC) | 1, 2 | **P-14** |
| 6 | **3V3 rail budget under simultaneous worst case** — NFC TX + audio + LoRa + backlight + Wi-Fi against a 2 A TPS63020 with foldback | all | **P-15** |

**Cases 1, 2, 5, 6, 8, 9, 10 are OK or correctly BLOCKED** under the proposed
architecture. **Cases 3, 4, 7, 11 carry unresolved items.**

---

## 6. Bench experiments this table cannot replace

Two, roughly a day and under $100, and they are the only questions here that no
datasheet can answer:

1. **Reverse-insertion rig** — LTC4368-1 + FDS6898A + BQ25185 on protoboard, cell
   deliberately reverse-wired, scope on BQ25185 BAT. Confirm: BAT never goes below
   −0.3 V for longer than the part tolerates; latch rather than retry; normal
   charging with a correct cell; predicted behaviour at a 2.0 V cell; the recovery
   trickle actually revives a 0 V pack; and **measure the no-battery STAT2 toggle
   rate** with the intended C<sub>BAT</sub>.
2. **Hot-insertion rig** — measure inrush into `BAT_PROT` at the intended
   capacitance and confirm it stays below the sense trip (Case 11 / P-13).

---

## Sources

- TI **BQ25185**, SLUSF65A (Oct 2023, rev. Jan 2026) — §7.3.10, Table 7-2, §6.1
- TI **TPS22950/C/L**, SLVSFJ2B (Dec 2020, rev. Feb 2023) — §5 Device Comparison Table, §6 Pin Functions, Features
- TI **TPS22950-Q1**, SLVSGP6A (Sep 2022, rev. Dec 2022) — §5 Pin Functions, §6.3 Recommended Operating Conditions, §6.5 EC, §8.4 Functional Modes, orderable addendum **(THE FITTED PART, D-765)**
- TI **TCA9517A**, SCPS245E (Dec 2012, rev. Oct 2025) — Features, §3, §9
- TI **TPS63020** — 2 A buck-boost
- ADI **LTC4368**, Rev. C — operating range 2.5–60 V, V<sub>IN(UVLO)</sub> 1.8–2.4 V, 80 µA operating / 5 µA shutdown, −40 V withstand, reverse-VIN gate mechanism
- onsemi **FDS6898A**, Rev. 4 — independent dual N-FET
- [Independent review FBV2-CTO2-PWRNFC-001](../reviews/2026-08-22-independent-cto-power-nfc-review.md) — advisory
