# FBV2-P2-001 — Power-tree routing attempt

**Date:** 2026-08-24 · **Task:** FBV2-P2-001 — route the safety-critical power tree
**Repository HEAD at start:** `faa0c91` · **Pre-routing tag:** `beta-v2-p2-entry-pass` → `faa0c91`
**Result: FBV2-P2-001 = FAIL.** The power tree is not routed.
**Overall Full Beta v2 stays 74 %. PCB routing stays 0 %.**

> **The board at this commit carries ZERO tracks and ZERO signal vias.** What it gained is the
> **In1.Cu GND reference plane** and two corrective placement passes that the routing exposed as
> prerequisites. The routing itself was attempted, produced **505 DRC violations**, and was
> **reverted rather than committed.**

---

## 1. Why this is a FAIL and not a partial pass

§28 lists thirteen exit criteria. Three are met — the tag, the In1 plane, and P1 geometry still
passing. **Ten are not, because no copper exists.** A task that was asked to route the
safety-critical battery path and did not route it has failed, and reporting it any other way would
be exactly the kind of asserted-rather-than-measured progress `PROGRESS.md` §"How percentages work
here" was written to prevent.

**No percentage is claimed and PCB routing stays at 0 %.**

---

## 2. Preflight

| check | result |
|---|---|
| Working tree | clean but for the two long-standing untracked paths |
| Local `master` / `origin/master` / HEAD | all `faa0c91` |
| Board | 72.000 × 148.000 mm |
| Tracks / signal vias / outer pours | 0 / 0 / 0 |
| DRC | **1** — the `MK1` netless-NPTH-inside-its-own-GND-ring `solder_mask_bridge` accepted at D-227 |
| ERC | **0 errors / 27 warnings** |
| Unrouted | 499 |
| Preserved untouched | `hardware/beta-dm/`, `hardware/beta/`, `hardware/beta/mechanical/`, the Beta-DM Gerber ZIP |

**The `MK1` artefact was not suppressed at any point in this task.**

---

## 3. Pre-routing checkpoint tag

**`beta-v2-p2-entry-pass`** created as an **annotated** tag on `faa0c91` and pushed:

```
Full Beta v2 — P1 PASS and P2 entry PASS, standard 1x24 + Qwiic architecture,
72x148 floorplan, PM-1/2/3/PT-1 closed, zero routing.
```

Verified on the remote: `refs/tags/beta-v2-p2-entry-pass^{}` → `faa0c91`. No pre-existing tag of
that name was moved — the only tag that existed was `beta-full-reference-v1`.

---

## 4. Documentation cleanup (§3)

**A. `PROGRESS.md` stale HEAD.** The header recorded `7515d57` (FBV2-EXP-001) when the committed
state was `faa0c91` (FBV2-EXP-002). Corrected.

**B. E-7 final disposition — CTO ruling, recorded as D-243.**

> **The battery envelope is 57 × 75 × 8.0 mm and that figure is a MAXIMUM RESERVED ENVELOPE.**
> **57 mm is NOT a minimum cell width and NOT "the lower bound of what fits."** The EXP-002 wording
> was wrong and is withdrawn. Verified 50 mm-wide cells fit and are the intended candidates —
> **PKCELL `LP785060`** and **`LP755070`**. **The envelope is NOT shrunk to 50 mm:** the unused
> 7 mm preserves alternate- and future-cell flexibility at **zero current placement cost**, since
> nothing is waiting to occupy it. **E-7 is CLOSED.**

---

## 5. The In1.Cu GND reference plane — delivered and validated

| property | value |
|---|---|
| Zones on In1 | **1** |
| **Filled islands** | **1** — a single continuous reference |
| Net | **GND** |
| Filled area | **9938.9 mm² of a 10656 mm² board = 93.3 %** |
| Pad connection | **SOLID**, no thermal relief |
| Splits / analog islands | **none** |
| Authorised void | the ESP32 antenna keep-out, cut by the existing four-layer rule area — **no hand-carved polygon, no decorative void** |
| F.Cu / B.Cu pours | **not created** — they are the last step of FBV2-P2 |

`p1_regression.py` was taught the difference between a **pour** and **routing**: the old blanket
*"0 fills"* expectation is replaced by *"0 tracks / 0 vias / 0 OUTER pours"* plus a positive check
that **In1 is exactly one GND zone of exactly one island.** A split reference is now a gate
failure instead of an invisible mistake.

---

## 6. What the routing exposed — PM-2 was closed on incomplete evidence

FBV2-EXP-002 reported PM-2 closed on the chain: `J4 → F1 → Q2 → Q3 → R75 → U18`, **30.86 mm**,
Kelvin **6.60 mm**. **That measurement was real and it is not withdrawn.**

**But it was reported as if it closed the whole of PM-2, and it did not.** The trip/gate parts and
the dead-cell reference network had been packed into regions chosen while the chain still sat in
the right column, and were never re-homed when the chain moved to the left margin. Measured on
`faa0c91`, before this task touched anything:

| net | at `faa0c91` | after correction |
|---|---|---|
| **`LTC_GATE`** — a ≈ 20 µA charge-pump node holding four pass FETs enhanced | **70.4 mm** | **29.8 mm** |
| `BAT_SENSE` | 61.4 mm | **24.3 mm** |
| `REF_POL` | 51.7 mm | **9.7 mm** |
| `REC_GATE_N` | 50.6 mm | **15.6 mm** |
| `N_POL` | 46.4 mm | **8.3 mm** |
| `LTC_OV` / `LTC_UV` | 28.2 / 15.0 mm | **8.0 / 9.1 mm** |

Routing those as they stood would have knowingly built the defect PM-2 exists to prevent, so the
support network was moved to sit beside the chain: the trip/gate parts into **X 7.3 … 13.6,
Y 72 … 100**, immediately east of `U18`, `R75`, `Q3` and `Q2`; the dead-cell reference network into
the left column above `J4` and the strip beside it.

**No component value, no threshold, no topology and no net changed. The 1.5 A chain itself did not
move.** §22 forbids significant placement moves without escalating — this is that escalation, and
it is the new item requiring a CTO ruling.

**29 power test points were also re-homed.** A test point 50 mm from its own net is not access, it
is a stub, and on a 1.5 A net it is a stub that forces load current somewhere it should not go.
`TP34` (`BAT_CONNECTOR_P`) was **59 mm** from `J4`; it is now **4.4 mm**. §22 asks specifically for
"test point forcing bad current flow", and this was it.

Both passes were re-validated: **zero side-aware courtyard collisions, zero region violations,
P1 regression PASS.**

---

## 7. Why the routing failed

A first router was written that computes a minimum spanning tree over each net's pads and draws
each edge as a direct segment on the pad's own layer. On the compact PM-1 cells that is adequate.
Across the board it is not: **it draws straight lines through other pads.**

Result on 64 nets, 263 segments and 24 vias:

| DRC class | count |
|---|---|
| `shorting_items` | **102** |
| `tracks_crossing` | **112** |
| `solder_mask_bridge` | **204** |
| `clearance` | 45 |
| `hole_clearance` / `hole_to_hole` / `holes_co_located` | 16 / 6 / 9 |
| `items_not_allowed` | 10 |
| `copper_sliver` | 1 |
| **total** | **505** |

**That is not a routing of the power tree; it is a demonstration that MST-plus-straight-lines is
the wrong instrument.** It was reverted in full. Committing it would have put 505 violations and
102 electrical shorts into the authoritative board on a task whose subject is the *safety-critical*
battery path — the single worst place in this design to leave copper nobody has verified.

**What the next task needs** is either an obstacle-aware path search (a routing grid or a
visibility graph over pads, courtyards and the existing plane), or hand-drawn per-net polylines
with per-net DRC verification after each. The scope, the widths, the layer policy and the intended
topology are all already settled and are recorded in
[`../pcb/FBV2_P2_POWER_ROUTING.md`](../pcb/FBV2_P2_POWER_ROUTING.md) so none of that has to be
re-derived.

---

## 8. B-34 — recomputed, still an estimate, still open

Computed from the **intended** geometry at ledger widths on 1 oz copper (0.491 mΩ/square), because
there is no routed copper to measure. **This is not a thermal measurement and is not presented as
one.**

| contributor | R |
|---|---|
| PM-2 chain, 30.9 mm at 1.00 mm | 15.2 mΩ |
| **`BAT_PROTECTED_P`, ≈ 71 mm at 1.00 mm** | **34.9 mΩ** |
| 4 × POWER vias | ≈ 0.5 mΩ |
| `F1` fuse, cold | ≈ 25 mΩ |
| `Q2` + `Q3` NTMD4820N in series | ≈ 46 mΩ |
| **BQ25185 BATFET** | **115 mΩ** |

| current | copper only | **total drop** | **total dissipation** |
|---|---|---|---|
| **1.50 A** | 76 mV / 114 mW | **≈ 355 mV** | **≈ 532 mW** |
| **1.75 A** | 89 mV / 155 mW | **≈ 414 mV** | **≈ 724 mW** |

**B-34: OPEN — PHYSICAL VALIDATION REQUIRED.** Nothing here is clearly unsafe, so §11's
escalate-and-halt did not trigger: the dominant 115 mΩ sits in `U11`'s WSON-10 exposed pad, `U11`
is out of the battery shadow with copper on both faces and no cell behind it, and the fuse and FET
losses are in separate packages in the left margin. But an estimate from an unrouted board cannot
close a blocker, and it is not claimed to.

**One number dominates and is worth fixing next:** `BAT_PROTECTED_P` at 71 mm is **69 % of the
copper resistance on its own**. Widening it 1.00 → 1.50 mm takes the copper from 50.6 to
**38.9 mΩ** and the 1.5 A loss from 114 to **88 mW**, at the cost of board area on a face that has
it. Carried as **PR-2**.

---

## 9. Validation at exit

| check | result |
|---|---|
| Schematic parses / PCB parses | ✔ / ✔ |
| **ERC** | **0 errors / 27 warnings**, histogram identical |
| **DRC** | **1** — the `MK1` artefact, D-227, **not suppressed** |
| Unrouted | **499**, unchanged |
| Tracks / signal vias / outer pours | **0 / 0 / 0** |
| **In1 GND** | **1 zone, 1 island, net GND, 93.3 %** |
| `p1_regression` | **PASS**, 0 checks failed |
| `dru_probe` / `netclass_probe` / `fork_equivalence` | **PASS / PASS / PASS** |
| Board outline | 72.000 × 148.000 mm |
| Placement collisions | **0** |
| Accidental out-of-scope routing | **zero** — no net is routed |
| Beta-DM / frozen Beta / `hardware/beta/mechanical/` | **untouched** |

---

## 10. Items for the next task

| # | item |
|---|---|
| **PR-1** | Route the power tree with an **obstacle-aware** router or verified hand polylines |
| **PR-2** | Widen `BAT_PROTECTED_P` to **1.50 mm** |
| **PR-3** | **PM-2 was closed on incomplete evidence at FBV2-EXP-002** — corrected here, recorded so the pattern is not repeated |
| **B-34** | OPEN — physical validation required |
| **PR-4** | F.Cu / B.Cu pours and perimeter stitching remain the **last** step of FBV2-P2 |
