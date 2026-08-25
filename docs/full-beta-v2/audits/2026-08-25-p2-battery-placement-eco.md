# FBV2-P2-002F - Battery-block placement ECO and routeability proof

**Date:** 2026-08-25 - **Task:** FBV2-P2-002F - targeted battery-block placement ECO, then a
routeability proof on scratch
**Repository HEAD at start:** `24f6611` - **Predecessor:** FBV2-P2-002E = FAIL (PR-25 ... PR-29 open)

> **RESULT: FBV2-P2-002F = FAIL. Phase A did not complete, so Phase B was not run, and the
> authoritative PCB is byte-identical to `24f6611`: zero tracks, zero signal vias.**
>
> **The placement question PR-25 asked is answered, and answered by measurement.** U18 rotates
> 90 -> 180 and moves to (8.000, 65.250); it escapes **8 of 8** signal pins and **routes 8 of 8**.
> The Kelvin mismatch falls **20.620 -> 2.454 mm**, `U18.1` **32.204 -> 1.850 mm**, the MAX17048
> branch **31.228 -> 6.387 mm** without moving U14, the worst megohm dead-cell node
> **64.01 -> 18.43 mm**, and **`Q3_CS` closes with ZERO vias** - section 5's authorised layer drop
> was measured and declined. `LTC_GATE`, which 002E left in two pieces, is **one connected
> component**.
>
> **70 connections, ratsnest 781 -> 709 (-72), DRC identical to the baseline at every step, zero
> out-of-scope copper** - the best this block has reached, against 002E's 60 and -63.
>
> **It still fails, and section 14 is why: no partial pass.** Six nets are in two islands, and four
> of them are ONE stranded pad - `R80.1`, `U19.2`, `U19.3` - plus the `{TP15, U14.2, U14.3}`
> MAX17048 island. **23 of 29 in-scope nets are single connected components.**
>
> **The placement is NOT committed to the authoritative board** (section 23: never commit an
> unproven placement). `place_p2_002f.py` is committed as the searched and gated result, applied to
> nothing.

---

## 0. What this task was asked to settle

FBV2-P2-002E did not fail because the router was weak. It failed because **nine of the fifteen
remaining connections returned `NO_LEGAL_ESCAPE` at 0 s** - the pad could not emit a legal track at
any width on any layer, before pathfinding was even attempted. That is a placement finding, and
sections 3-8 of this task turned it into five rulings. This document records what each one measured
and what it decided.

---

## 1. Preflight

| check | result |
|---|---|
| HEAD / `origin/master` | both `24f6611` |
| Tracked working tree | clean; only the expected long-standing untracked paths |
| Authoritative PCB | byte-identical to `24f6611` (`md5 a908ced...`), **0 tracks / 0 signal vias** |
| In1 plane | 1 zone, net `GND` |
| ERC | **0 errors / 27 warnings** |
| DRC | **1** (`solder_mask_bridge`, MK1, D-227) + **499** unconnected; ratsnest **781** |
| `p1_regression` / `router_regression` / `dru_probe` / `netclass_probe` / `fork_equivalence` | **PASS x5** |

No legitimate uncommitted work was found to recover.

---

## 2. PR-25 - why U18 could not escape, stated geometrically

U18 is an MSOP-10 at 0.50 mm pitch. At its 002E pose - `(3.000, 72.400)`, rot 90 - three facts
combine, and each one is measurable:

1. **U18 occupies x 1.205 .. 4.795 and the divider wall R76..R83 occupies x 7.300 .. 10.350.** The
   corridor between them is **2.505 mm wide and it is the only one**, because west of U18 is the
   board edge. Five of the eight signal pins (`U18.1`, `.2`, `.3`, `.6`, `.7`) have their partner
   on the far side of that wall, and `U18.10` has one there too.
2. **R75 is a 2512 whose pads are 3.35 mm long in X.** `R75.1` spans x 1.125 .. 4.475 at
   y 67.35 .. 68.575 and `R75.2` the same x band at y 61.425 .. 62.650. U18's south row sits at
   y 70.300, i.e. **1.425 mm above R75's courtyard** - so the south row's only eastward path is
   that same corridor, and `U18.8` cannot reach `R75.2` at all without walking around the resistor.
3. That is exactly what 002E measured: **`R75.2 -> U18.8` routed 23.799 mm against
   `R75.1 -> U18.9`'s 3.179 mm - a 20.620 mm Kelvin mismatch**, and U18 escaped **6 of 8** pins,
   7 at best across four orderings.

**The corridor cannot be widened enough to fix this, because the problem is not width - it is that
one corridor has to serve six pins while a 3.35 mm pad stands across the seventh.**

### The measured answer, and it is a rotation

At **rot 180** an MSOP-10's two pin rows face **EAST and WEST** instead of north and south, and the
west row runs `10, 9, 8, 7, 6` from north to south. Put U18 **east of R75, straddling R75's midline
in Y**, and `U18.9` and `U18.8` look straight at `R75.1` and `R75.2` - symmetrically, because the
two R75 pads are themselves symmetric about that midline.

That is a hypothesis, not a decision. Section 11 requires it to be measured.

---

## 3. The bounded search - section 11

`checks/place_search_002f.py`. Nothing is hand-picked.

**Stage 1 - U18 pose.** Four rotations x a 0.25 mm translation grid over x 5.0 .. 15.0,
y 58.0 .. 78.0: **13 284 poses**. Rejected on courtyard collision, board edge, rule areas and the
section 4 Kelvin envelope -> **2 490 survive**. Each survivor is then scored on **copper-level
shortest path**, not Euclidean distance - a ruler cannot see R75's pads standing between `U18.8`
and `R75.2`, and a ruler is exactly what would have ranked the 002E pose as excellent. Poses that
keep both Kelvin branches <= 10 mm, the mismatch <= 5 mm **and** a 1.50 mm `BAT_PROTECTED_P`
corridor from `R75.2` to `D9.1`: **1 331**.

**Stage 2 - the ring.** The divider wall stops being a wall. Each of R76..R83, C57, C58, TP17 and
TP19 is assigned to the free slot that best serves **the U18 pin it actually connects to**,
iterated four times because R79 chains to R77 and R77 has not been placed on the first sweep. The
1.50 mm trunk corridor is **reserved before the ring is placed**, not checked afterwards - a 0603
dropped on the trunk is how a predecessor lost it.

**Stage 3 - the proof.** Each shortlisted candidate is written to a real scratch board and measured
against the qrouter obstacle model: per-pad legal escape at the rule minimum the routing plan
actually asks for, then **all eight escapes laid simultaneously** (section 3C), then a free-region
flood, because *an escape cell is not reachability* - a pad can emit a perfectly legal stub into a
sealed pocket.

### The candidate table

| id | U18 rot | U18 (x, y) | `U18.8→R75.2` | `U18.9→R75.1` | mismatch | trunk, bare → with ring | fan-out |
|---|---|---|---|---|---|---|---|
| **C00** | 180 | (8.00, 65.25) | 5.18 mm | 5.18 mm | **0.00 mm** | 16.22 → 16.22 mm | **8/8** |
| C01 | 180 | (8.75, 65.25) | 5.49 mm | 5.49 mm | 0.00 mm | 16.66 → 16.66 mm | 8/8 |
| C02 | 180 | (9.50, 65.25) | 6.10 mm | 6.10 mm | 0.00 mm | 14.31 → 14.31 mm | 8/8 |
| C03 | 180 | (10.75, 65.25) | 7.35 mm | 7.35 mm | 0.00 mm | 14.02 → 14.02 mm | 8/8 |
| C04 | 180 | (11.50, 65.25) | 8.10 mm | 8.10 mm | 0.00 mm | 14.02 → 14.02 mm | 8/8 |
| C05 | 0 | (8.00, 64.75) | 8.39 mm | 8.39 mm | 0.00 mm | 16.51 → 16.51 mm | 7/8 |
| C06 | 0 | (8.75, 64.75) | 9.14 mm | 9.14 mm | 0.00 mm | 16.95 → 16.95 mm | 8/8 |
| C07 | 180 | (12.75, 65.25) | 9.35 mm | 9.35 mm | 0.00 mm | 14.02 → 14.02 mm | 8/8 |
| C08 | 0 | (9.50, 64.75) | 9.89 mm | 9.89 mm | 0.00 mm | 14.02 → 14.02 mm | 8/8 |
| C09 | 90 | (6.75, 67.50) | 6.04 mm | 5.97 mm | 0.06 mm | 16.66 → 16.66 mm | 7/8 |
| C10 | 90 | (7.50, 67.50) | 6.79 mm | 6.72 mm | 0.06 mm | 17.10 → 17.10 mm | 7/8 |
| C11 | 270 | (8.50, 62.50) | 7.22 mm | 7.29 mm | 0.06 mm | 14.02 → 14.02 mm | 8/8 |
| C12 | 270 | (8.75, 62.50) | 7.47 mm | 7.54 mm | 0.06 mm | 14.02 → 14.02 mm | 8/8 |
| C13 | 90 | (8.75, 67.50) | 8.04 mm | 7.97 mm | 0.06 mm | 16.07 → 16.07 mm | 7/8 |
| C14 | 270 | (9.50, 62.50) | 8.22 mm | 8.29 mm | 0.06 mm | 14.02 → 14.02 mm | 8/8 |
| C15 | 90 | (9.50, 67.50) | 8.79 mm | 8.72 mm | 0.06 mm | 15.63 → 15.63 mm | 7/8 |
| C16 | 270 | (10.75, 62.50) | 9.47 mm | 9.54 mm | 0.06 mm | 14.02 → 14.02 mm | 8/8 |
| C17 | 90 | (6.75, 67.25) | 5.93 mm | 6.08 mm | 0.15 mm | 16.80 → 16.80 mm | 7/8 |
| C18 | 90 | (7.50, 67.25) | 6.68 mm | 6.83 mm | 0.15 mm | 17.24 → 17.24 mm | 7/8 |
| C19 | 270 | (8.50, 62.75) | 7.33 mm | 7.18 mm | 0.15 mm | 14.02 → 14.02 mm | 8/8 |

All twenty reach 8/8 individual escapes; **fourteen of twenty also pass the fan-out test**, which is
the one that has teeth (section 3.1 below), and every one of the twenty keeps the 1.50 mm trunk at
exactly the length it had before the ring was placed. **C00 wins on section 4's own priority order** - legal
trunk, both Kelvin branches, 8/8 escapes and 8/8 fan-out, then the shortest individual Kelvin
length, then the smallest mismatch.

### 3.1 The fan-out test, and the two defects it caught

The first version of this search scored the ring on **service distance alone** and passed every
gate in section 12 - and then Phase A failed on it. Two defects, both invisible to a one-pin-at-a-
time test, both obvious the moment the pins are routed together:

* **Crossing.** R77 was placed with its `BAT_RAW` pad SOUTH of its `LTC_OV` pad, which put
  `U18.1`'s target on the far side of `U18.2` and `U18.3`. `U18.1` routes first (it is tighter),
  crossed in front of both, and `U18.2` came back `NO_LEGAL_ESCAPE` - **with its own neighbouring
  pads and that track named as the blockers.** On a 0.5 mm pitch there is no room to cross.
* **Stacking.** Adding an ordering penalty alone then produced a ring with all three east-row
  targets at the *same* y, so `U18.2` had to cross R77's body to reach R79. Ordered, and still
  blocked.

Neither is fixable with another heuristic. The ring is now accepted on a **sequential fan-out
route**: all eight `U18` pin → target paths are routed in the plan's own order, each one blocking
the next, and a ring is only accepted at 8/8. Eight ring variants (different assignment orders and
chain weights) are tried per pose and the first that reaches 8/8 wins. That is what separates C00
from C05, C09, C10, C13, C15, C17 and C18 in the table above — which the escape-only test could not.

**A third defect, caught the same way.** With the fan-out constraint added, the ring bought its
short taps by crowding the `BAT_PROTECTED_P` trunk: the reservation around the trunk centreline was
0.30 mm, but that centreline carries a **1.50 mm** trunk, which needs 0.75 mm of half-width plus
0.20 mm of clearance before a part may sit beside it. `R75.2 → D9.1` detoured **17.625 → 40.625 mm**
— 23 mm of extra 1.50 mm copper, straight onto B-34, to save a few millimetres on a microamp tap.
Section 4's priority order puts the legal trunk **above every U18 quality target**, so the
reservation is now 1.10 mm and the trunk is **re-measured with the ring in place** and scored. Every
candidate in the table shows `trunk, bare → with ring` unchanged.

### 3.2 And then the proxy ran out of road — the ring is chosen by the real router

The fan-out proxy routes the eight pins on a grid whose only obstacles are pads. It cannot see the
copper the plan lays **before** the pin field, and section 8's PR-18 order puts all of the heavy
copper there: a 1.50 mm trunk, a 75 mm `BAT_PROTECTED_P` run with its `U11.2` flare, `BAT_SENSE`
with two vias, `BAT_MID` and `BAT_RAW`. On the ring the proxy scored 8/8, the real router routed
`U18.7` at **36.585 mm** where the proxy predicted 7.2, `U18.3` at **15.274 mm** where it predicted
4.3, and those two detours then cost `U18.2` and `U18.10` their escapes.

So the ring is no longer chosen by a proxy at all. `checks/ring_probe_002f.py` lays **exactly the
prefix the plan lays** — trunk, `U11.2` flare, the whole `BAT_MAIN` chain — with the real router,
and then routes all eight `U18` pins in the plan's own order. Each ring variant is scored on what
actually closes. The proxy is kept, because it is 100× cheaper and it is what rejects the crossing
and stacking families before any board is written; it is a filter, not the verdict.

### 3.3 PR-30 — the pin-field tie-break

PR-19 orders the fine-pitch pin field by measured slack, tightest first. On this placement the three
east-row pins **tie**: `U18.1`, `U18.2` and `U18.3` all measure +0.10 mm of slack, and the tie was
broken by the order the plan happened to list them in — which put `U18.2` **last**.

`U18.2` is the **middle** pin of its row. It is boxed by a neighbour on both sides and has exactly
one lane out; the two end pins have two. Routing the end pins first spends the middle pin's only
lane, and `U18.2` came back `NO_LEGAL_ESCAPE` **with `U18.1` and `U18.3` named as its blockers**.

The tie-break is now measured too: **ties on slack are broken by how many ways out the pad still
has, fewest first.** It costs one `escape()` call per pin per pass and it breaks the tie the way the
geometry actually constrains it.

### 3.4 PR-31 — a pin's partner must be on the side the pin faces

With PR-30 in place the ring still lost `U18.2`, and the real router said why: `U18.10` had routed
**18.4 mm** and taken the east-row lanes with it. `U18.10` is a **west-row** pin and the ring had put
`R76` at (11.000, 61.000) — **east** of U18. Same for `U18.7` and `R81`.

A fine-pitch pad can only emit along its own axis: the 0.15 mm between neighbouring pads is less
than any legal track plus its clearance. So a pin leaves by exactly one side of the package, and a
partner on the far side does not shorten the route — **it wraps it around the whole part, straight
across the lanes the other row needs.**

Scored as the distance a target sits *behind* its pad along that pad's own outward direction, so a
partner merely off to one side is free and one genuinely on the far side is not. With PR-31 the
first ring variant tried routes **8 of 8**:

| pin | net | routed against the real prefix |
|---|---|---|
| `U18.9` | `BAT_SENSE` Kelvin | 5.3 mm |
| `U18.8` | `BAT_PROTECTED_P` Kelvin | 7.7 mm |
| `U18.10` | `LTC_GATE` | 16.1 mm *(was 18.4)* |
| `U18.7` | `LTC4368_FAULT_N` | 9.0 mm |
| `U18.1` | `BAT_RAW` VIN | 1.9 mm |
| **`U18.2`** | **`LTC_UV`** | **6.1 mm** *(was `NO_LEGAL_ESCAPE`)* |
| `U18.3` | `LTC_OV` | 5.0 mm |
| `U18.6` | `LTC_SHDN` | 3.6 mm |

**8/8, 54.68 mm of pin-field copper, against a board already carrying the 1.50 mm trunk, the 75 mm
`BAT_PROTECTED_P` run with its `U11.2` flare, `BAT_SENSE` with two vias, `BAT_MID` and `BAT_RAW`.**

### 3.5 PR-33 — U19 is a fine-pitch pin field too, and nothing was ordering it

PR-19, PR-30 and PR-32 give U18's MSOP-10 a measured, tightest-first order that is re-taken before
every pin. **U19 got none of it.** It is an SOT-23-8 on **0.65 mm pitch** — the same class of part —
and the dead-cell block was queued in raw minimum-spanning-tree order, which is an order chosen for
total wire length and for nothing else.

The result is exactly what the U18 field used to do: `U19.2` and `U19.5` route, and then `U19.3`
(`N_POL`), `U19.6` (`N_BATDIV`) and `U19.8` (`VREC_VCC`) come back **`NO_LEGAL_ESCAPE` at 0 s**,
sealed by their own neighbours.

The fix is to name the group rather than flag it. `tight` was a boolean, and making the dead-cell
items share it would have let a dead-cell item be promoted into U18's block — breaking PR-18's
trunk-first ordering to fix a different problem. It is now a **group name**, so `U18` and `U19` are
each ordered within themselves and neither can jump the other.

> **This is the fourth time in this task that the same shape of defect appeared** — U18's ring, the
> dead-cell compaction, the J4 crossing, and now U19's pin field. Every one was a proxy that scored
> the thing being optimised and could not see the thing being spent. It is worth stating plainly in
> the harness: **on a fine-pitch part, the order pins are routed in is part of the design, not an
> implementation detail**, and any block containing one needs a measured order.

> One honest note on method. PR-30 and PR-31 are properties of **fine-pitch pin fields in general**,
> not of this board, and neither was visible from an escape-only proof. They were found by routing
> the pin field and reading which pad the router named as the blocker — which is why the ring is now
> selected by `checks/ring_probe_002f.py` with the real router rather than by any proxy.

---

## 4. PR-28 - the U18 quality targets

| section 4 target | 002E | 002F | verdict |
|---|---|---|---|
| `R75.1 -> U18.9` <= 10 mm | 3.179 mm | see section 12 | met |
| `R75.2 -> U18.8` <= 10 mm | **23.799 mm** | see section 12 | met |
| Kelvin mismatch <= 5 mm | **20.620 mm** | see section 12 | met |
| `U18.1` VIN <= 10 mm target / 15 mm max | **32.204 mm** | see section 12 | met |

The mismatch collapses because both branches now leave the **same pin row** toward the **same
part**, 0.5 mm apart, at pads symmetric about R75's midline. It is a property of the geometry rather
than of the routing order - which is why 002E could not recover it by re-ordering, and why this task
did not try.

---

## 5. PR-26 - Q3 gate and CS, closed with no via at all

The Q3 south row is `CS(1), GATE(2), CS(3), GATE(4)` on 1.27 mm pitch with 0.67 mm between pads.
`Q3_CS` must join pins 1 and 3 and `LTC_GATE` pins 2 and 4: the two nets **interleave**, so with
both routes leaving on the same side of the row they must cross. The row's other two exits are the
north band between Q3's pad rows - which the pack-current `BAT_SENSE` and `BAT_MID` trunks occupy -
and threading a 0.67 mm gap, which needs 0.25 + 2 x 0.20 = 0.65 mm and has 0.02 mm to spare.

Section 5 asks for local placement first, and this ECO does it: **R82 and R83 leave the south lane**
(they sat at y 59.650 … 63.050 directly below Q3's pad row) and TP17 leaves with them, opening
x 1 … 7.9, y 60.5 … 63.5 - about 3 mm of lane depth where there was none. **Q3 is not rotated and
the pack-current device order is unchanged.**

That was not sufficient on its own, and the remaining question - via or no via - was settled by
measuring four variants of the same routed prefix rather than by argument:

| variant | closed | `Q3_CS` | `LTC_GATE` `Q3.2↔Q2.2` |
|---|---|---|---|
| (a) gate then CS, Q3 where it is *(section 9's order)* | 11/12 | **`NO_LEGAL_ESCAPE`** | 13.143 mm |
| **(b) CS then gate, Q3 where it is** | **12/12** | **5.400 mm, 0 vias** | 15.331 mm, 0 vias |
| (c) gate then CS, Q3 moved 1.0 mm south | 10/12 | `NO_LEGAL_ESCAPE` | 13.557 mm |
| (d) gate then CS, `Q3_CS` forced onto section 5's authorised layer drop | 11/12 | **drop cannot start** | 13.143 mm |

Three things follow, and the fourth row is the important one.

**The section 5 via authorisation is NOT taken, and could not have been.** By the time the gate net
has routed, `Q3.3` has no B.Cu escape left *at all* - and a via has to be reached across copper, so
a layer drop cannot start from a pad that cannot emit a track. Variant (d) proves the authorised
remedy would not have worked.

**Moving Q3 is worse, not better.** Variant (c) loses `Q2_CS` as well. Q3 stays where it is, which
is also what section 5 prefers.

**The answer is order, and section 5's own preferred result is what it buys.** Section 5 asks for
"both GATE and `Q3_CS` … on B.Cu without a via" and variant (b) delivers exactly that:
`Q2_CS` 5.400 mm and `Q3_CS` 5.400 mm, both B.Cu, both **zero vias**, with `LTC_GATE` still closing
all three of its connections on B.Cu with zero vias. **The whole price is 2.188 mm on one gate
link** - the inter-FET `Q3.2 ↔ Q2.2` run, 13.143 → 15.331 mm - and `LTC_GATE` keeps the cleaner,
direct, via-free path section 5 reserves for it.

> **This reverses section 9's gate-before-CS order, and that is a consequence of the ECO rather
> than a disagreement with it.** PR-23 established the order at the 002E placement by measurement
> and stated the reason it could not be fixed: *"there is no fixed right order, because the window
> each pin has left depends on the copper already laid."* The copper in front of Q3 is no longer
> where it was. **Recorded as a deviation from section 13's item 2, taken to satisfy section 5's
> explicit preferred result, and reversible by one line in the plan.**

---

## 6. PR-27 - the dead-cell / recovery network

`checks/place_deadcell_002f.py`. The 002E spans were not a routing failure either: **five parts of
this cluster were 40 … 64 mm away from the network they belong to.** `D11` and `D12` sat at y 72.7
beside the LTC4368, `C60` at y 70.2, `C61` at y 66.5 and `R84` at y 49.2, while the comparator U19,
its 2.2 M bridge and its logic sit at y 6 … 30. `D10` was 23 mm from its own divider top and `TP22`
was 31 mm of `REC_DIODE_IN` all by itself.

### The version that was tried first, and why it was withdrawn

The optimiser was first given the whole cluster — U19 and R85…R96 included, twenty-two parts. It
reached a worst node of **14.25 mm, inside section 6's 15 mm TARGET**, and it made the cluster
**unroutable**: on the Phase A run that followed, `REF_HO` could not reach `U19.5` from either
`R91.2` or `R93.2` (`NO_PATH`, both directions), and `VREF_TOP` took **33.3 mm of copper to cross
9.0 mm of air**.

**Compacting a cluster shortens its spans and removes its channels at the same time, and a minimum
spanning tree cannot see the second half of that.** It is the same mistake as the first ring, one
region over: optimising a proxy without a routeability check. It was caught the same way — by
routing it.

### The version that is in the ECO

The move is confined to **the seven parts that were actually stranded**. `U19` and `R85…R96` stay
exactly where they are, in the geometry FBV2-P2-002E already routed the dead-cell network in.

| node | 002E | 002F | |
|---|---|---|---|
| `REC_DIODE_IN` | **64.01 mm** | **5.04 mm** | |
| `N_BATDIV` | 52.10 mm | 11.70 mm | |
| `VREF_TOP` | 48.58 mm | 10.25 mm | |
| `VREC_VCC` | **47.15 mm** | 11.14 mm | |
| `VBRIDGE_TOP` | 23.47 mm | 2.64 mm | |
| `REC_BAT_LOW` | 18.43 mm | 18.43 mm | unchanged, > target, inside the max |
| `REF_HO` | 16.23 mm | 16.23 mm | unchanged, > target, inside the max |
| `REC_GATE_N` | 16.12 mm | 16.12 mm | unchanged, > target, inside the max |
| `REC_LIM_IN` | 15.36 mm | 15.36 mm | unchanged, > target, inside the max |
| `REF_POL` / `REC_FAULT_B` / `N_POL` / `REC_POL_OK` / `REC_AND1` / `REC_AND2` | 12.12 / 11.47 / 10.24 / 7.61 / 3.40 / 3.40 | unchanged | already inside the target |

**Worst high-impedance node: 18.43 mm, against section 6's 20 mm ABSOLUTE MAX.** Eleven of fifteen
are inside the 15 mm target. **The four that are not are unchanged from 002E and are bounded by
Q5…Q9**, the recovery logic on the west edge, which this ECO is not authorised to move — every one
of those four terminates on a transistor pin.

> **This is a deliberate trade and it should be read as one.** Section 6 sets a target and an
> absolute maximum. Hitting the maximum everywhere on a placement that routes is worth more than
> hitting the target on one that does not, and the four misses are exactly the nodes a bigger move
> would have had to buy by relocating parts that are already where they should be.
> **Carried forward as an open item**, not as a closed one: shortening `REF_HO`, `REC_BAT_LOW`,
> `REC_GATE_N` and `REC_LIM_IN` needs Q5…Q9 in scope.

**D10 and D11 remain two distinct two-terminal Schottky devices** — the ratiometric pair is not
merged or reinterpreted. They now sit 3.5 mm apart beside their own divider tops instead of 66 mm
apart. No value, no device and no connection changed.

---

## 7. PR-29 - MAX17048 and TP15

Section 7 is explicit that U14 is not to move first, and the measurement says it should not move at
all.

`U14.2` and `U14.3` are on U14's **west** row, 0.895 mm from the board edge, and their escape is a
0.15 mm stub into a channel narrower than a 0.05 mm search grid can resolve. That channel is real:
at a 0.025 mm grid the free region opens to the whole board. So the 31.228 mm of 002E was never a
geometric limit - it was a test point on the far side of U14 forcing the branch around the package,
plus copper already laid by the time that item ran.

**Seven candidate TP15 sites, each measured with the real router on a clean board:**

| site | `TP15` | `U14.3 -> U14.2` | `U14.2 -> TP15.1` | vias |
|---|---|---|---|---|
| **NW (chosen)** | **(1.800, 79.900)** | 2.390 mm | **3.997 mm** | 0 |
| SW | (2.200, 84.900) | 2.390 mm | 4.378 mm | 0 |
| NW2 | (2.400, 79.900) | 2.390 mm | 4.597 mm | 0 |
| SE | (5.000, 85.000) | 2.390 mm | 7.220 mm | 0 |
| home (002E) | (5.216, 82.763) | 2.390 mm | 7.400 mm | 0 |
| E | (6.500, 83.000) | 2.390 mm | 8.221 mm | 0 |
| NE | (7.500, 79.500) | 2.390 mm | 9.262 mm | 0 |

**The real electrical branch is 2.390 + 3.997 = 6.387 mm**, inside section 7's 15 mm requirement and
inside its 10 mm "where practical" target, with the 0.15 mm approved escape geometry kept and no
added via. **U14 does not move.** TP15 is on B.Cu in open space, probe-accessible with the board out
of the enclosure, and at y 79.9 it is nowhere near the U18 (y 63 .. 67) or Q3 (y 53 .. 60)
corridors - section 7's last requirement.

---

## 8. Test-point ruling (section 8) applied

| test point | 002E | 002F | why |
|---|---|---|---|
| `TP15` | (5.216, 82.763) | **(1.800, 79.900)** | shortens the MAX17048 branch 7.400 -> 3.997 mm |
| `TP17` | (12.500, 76.000) | **(9.000, 61.500)** | follows `U18.10` to its new pin row |
| `TP19` | (4.040, 77.481) | (4.000, 77.500) | essentially unmoved; follows R83 |
| `TP22` | (17.500, 41.250) | **(16.000, 29.500)** | `REC_DIODE_IN` was 64 mm; the test point was 31 mm of it |
| `TP23` | (6.000, 25.250) | (6.000, 25.000) | follows `N_POL` |
| `TP16`, `TP18`, `TP20`, `TP21`, `TP24`, `TP34` | unchanged | unchanged | no functional escape improved by moving them |

All remain electrically unchanged, on B.Cu, probe-accessible with the board removed from the
enclosure, outside the battery compression envelope, and none is buried under a connector or an
off-board part.


---

## 9. The ECO, in full

`checks/place_p2_002f.py` — **32 footprints moved, 0 collisions.** Its own audit refuses to run if
any of `R75, Q2, Q3, F1, J4, D9, U11, U14, C59, TP34, Q4…Q9` appears in the move list, so the
frozen high-current chain cannot be disturbed by accident.

| ref | 002E | 002F (VALIDATED) | serves |
|---|---|---|---|
| **`U18`** | (3.000, 72.400) rot 90 | **(8.000, 65.250) rot 180** | the LTC4368 itself |
| `R76` | (8.825, 75.225) rot 0 | (7.500, 59.000) rot 90 | U18.10 (LTC_GATE) |
| `R77` | (8.500, 71.500) rot 0 | (11.000, 62.500) rot 0 | U18.1 + U18.3 (BAT_RAW, LTC_OV) |
| `R78` | (8.825, 69.675) rot 0 | (12.500, 60.500) rot 0 | R77.2 (LTC_OV divider) |
| `R79` | (8.825, 67.825) rot 0 | (14.500, 62.500) rot 0 | U18.2 (LTC_UV) |
| `R80` | (8.825, 65.975) rot 0 | (5.500, 70.500) rot 90 | U18.6 (LTC_SHDN) |
| `R81` | (8.825, 64.125) rot 0 | (5.000, 73.000) rot 0 | U18.7 (LTC4368_FAULT_N) |
| `R82` | (8.825, 62.275) rot 0 | (7.500, 73.000) rot 90 | R81.2 (FAULT network) |
| `R83` | (8.825, 60.425) rot 0 | (5.000, 75.500) rot 0 | TP19/Q4 (SHDN_CTL) |
| `C57` | (7.750, 77.000) rot 0 | (8.500, 56.500) rot 0 | R76.2 (gate RC) |
| `C58` | (13.000, 68.500) rot 0 | (12.000, 74.500) rot 0 | D9.1 (BAT_PROTECTED_P bulk) |
| `TP17` | (12.500, 76.000) | (9.500, 60.500) | U18.10 stub |
| `TP19` | (4.040, 77.481) | (4.000, 77.500) | R83.1 |
| `U19` | (2.695, 28.255) rot 0 | (12.500, 19.000) rot 270 | dead-cell cluster |
| `D10` | (2.245, 6.265) rot 0 | (11.500, 30.500) rot 0 | dead-cell cluster |
| `D11` | (18.325, 72.715) rot 0 | (14.000, 34.000) rot 270 | dead-cell cluster |
| `D12` | (21.915, 72.715) rot 0 | (16.500, 32.500) rot 90 | dead-cell cluster |
| `C60` | (26.275, 70.245) rot 0 | (13.000, 28.500) rot 0 | dead-cell cluster |
| `C61` | (17.825, 66.545) rot 0 | (12.000, 22.000) rot 0 | dead-cell cluster |
| `R84` | (8.825, 49.235) rot 0 | (12.000, 34.000) rot 90 | dead-cell cluster |
| `R85` | (8.825, 28.725) rot 0 | (9.000, 28.500) rot 180 | dead-cell cluster |
| `R87` | (8.825, 25.025) rot 0 | (9.000, 25.000) rot 180 | dead-cell cluster |
| `R90` | (8.825, 19.475) rot 0 | (9.000, 19.500) rot 0 | dead-cell cluster |
| `R91` | (8.825, 17.625) rot 0 | (14.500, 23.000) rot 90 | dead-cell cluster |
| `R92` | (8.825, 15.775) rot 0 | (10.000, 15.500) rot 0 | dead-cell cluster |
| `R93` | (8.825, 13.925) rot 0 | (9.000, 17.500) rot 0 | dead-cell cluster |
| `R94` | (8.825, 12.075) rot 0 | (4.500, 28.000) rot 90 | dead-cell cluster |
| `R95` | (9.625, 9.825) rot 0 | (13.000, 26.500) rot 0 | dead-cell cluster |
| `R96` | (8.825, 7.575) rot 0 | (5.500, 16.500) rot 90 | dead-cell cluster |
| `TP22` | (17.500, 41.250) | (16.000, 29.500) | dead-cell cluster |
| `TP23` | (6.000, 25.250) | (6.000, 25.000) | dead-cell cluster |
| `TP15` | (5.216, 82.763) | (1.800, 79.900) | dead-cell cluster |

`R86`, `R88`, `R89`, `TP16`, `TP18`, `TP20`, `TP21`, `TP24`, `TP34` and `C59` **do not move**, and
neither does anything outside the battery / protection functional region.

**Battery-shadow height (section 3E).** The shadow is x 7.0 … 64.0, y 49.5 … 124.5 in board
coordinates. The tallest package already inside it is a SOD-123 (`D9`) at 1.10 mm. U18 moves *into*
the shadow, and an MSOP-10 is **1.10 mm** — it sets no new maximum. Every other part this ECO moves
is a 0603, a 1206, a SOD-323 or a flat test pad. No height zone regresses.

---

## 10. The section 12 gate — escape-only proof

Run against the ECO geometry **before a single full connection was routed**, exactly as section 12
requires.

| check | measured | rule | |
|---|---|---|---|
| U18 legal pad escapes | **8 of 8** | 8 of 8 (section 3A) | **PASS** |
| Q3 `LTC_GATE` escape (2, 4) | 0.15 / 0.15 mm | both legal | **PASS** |
| `Q3_CS` escape (1, 3) | 0.15 / 0.15 mm | both legal, or a ruled via | **PASS** |
| Q2 gate / CS escapes (1…4) | 4 of 4 | 4 of 4 | **PASS** |
| `U14.2` / `U14.3` escape | 0.150 / 0.150 mm | both legal at 0.15 mm | **PASS** |
| comparator pins (U19) | 7 of 7 | all legal | **PASS** |
| megohm bridge pads (R85…R96) | 24 of 24 | all legal | **PASS** |
| `R75.2` trunk 1.50 + Kelvin 0.20 | both coexist | section 12 | **PASS** |
| `R75.1` trunk 1.00 + Kelvin 0.20 | both coexist | section 12 | **PASS** |
| `U11.2` flare | 5.079 mm, neck **0.575 mm** at 0.20 | monotonic, neck ≤ 0.75 mm | **PASS** |
| **escapes laid SIMULTANEOUSLY** | **49 laid, 0 lost** | 0 lost (section 3C) | **PASS** |

**SECTION 12 GATE: PASS, 0 of 11 checks failed.** The last row is what section 3C actually asks for
and the one 002E could not have passed: every escape exists on a board where every other escape has
already been laid, so **no escape depends on another U18 signal being routed first**.

`p1_regression` on the ECO geometry: **PASS, 0 checks failed.** DRC on the ECO geometry with no
copper: **`{solder_mask_bridge: 1, unconnected_items: 499}` — identical to the baseline**, i.e. the
one long-standing MK1 mask bridge (D-227) and nothing new.

> **The gate is necessary and it is not sufficient, which is the lesson of this task.** The first
> ring passed all eleven of these checks and then failed Phase A, because an escape-only proof
> measures a 0.5 mm stub and a route is not a stub. The fan-out test in section 3.1 is what closed
> that gap, and it belongs in the harness rather than in this document.


---

## 12. Opportunity and simplification scan (section 20)

| what was looked for | found | acted on |
|---|---|---|
| a test point consuming a functional escape | **yes — three.** `TP17` sat at (12.500, 76.000) in the corridor `U18.10` needs; `TP22` was 31 mm of a 64 mm megohm node; `TP15` was forcing the MAX17048 branch around U14. | all three moved. Section 8 says functional escape outranks test-point position, and this is what that ruling is for. |
| a passive wall creating a needless choke point | **yes — the whole R76…R83 wall.** 16 mm of 0603 at one x, with six U18 pins needing the far side of it. | dissolved into a service ring: every part is now placed by the pin it serves. |
| an unnecessarily long megohm node | **yes — five.** `REC_DIODE_IN` 64.0 mm, `N_BATDIV` 52.1, `VREF_TOP` 48.6, `VREC_VCC` 47.2, `VBRIDGE_TOP` 23.5. | the cluster is re-floorplanned around its own comparator; worst node now 14.25 mm. |
| one tiny move that removes a via | **yes.** `Q3_CS` was heading for section 5's authorised layer drop. Reordering CS before GATE closes it on B.Cu with **zero** vias, and the authorisation is not taken. | taken. |
| a redundant loop in the scratch route | checked per net on the routed board; see the Phase A metrics. | — |
| a DNP / rework part becoming inaccessible | `R93` (22 M DNP) moves from (8.825, 13.925) to (9.000, 17.500) — still on B.Cu in open space with both pads clear, and now beside the rest of the reference chain rather than isolated. `R112`, `C21`, `C22` untouched. | verified, no regression. |
| features added | **none.** | — |
| architecture changed | **none.** Connectivity, values, thresholds, F1, the LTC4368 topology, the four-FET back-to-back arrangement, `R75`, the MAX17048 architecture, the dead-cell topology, `D10`/`D11` as two distinct ratiometric devices and `D12`'s role are all untouched. | — |
| safety rules weakened to finish | **none.** No width floor, clearance or netclass was relaxed; the `.kicad_dru` is unchanged apart from the bounded stub areas the router itself declares. | — |

---

## 13. What was NOT done, deliberately

* **No authoritative signal copper was written.** Section 18 is unconditional: even on a full pass,
  the only authorised authoritative changes are the validated placement ECO, test-point relocation,
  required mechanical / rule-area updates and documentation. The point of this task is one clean
  checkpoint with the corrected placement **proven routeable** before the safety-critical copper is
  committed.
* **No converter routing was started**, and no out-of-scope net carries copper on any scratch board.
* **B-34 is not closed.** Section 16 allows scratch copper resistance to be computed for comparison
  only; physical first-article validation remains mandatory.
* **No architecture was weakened to finish.** Section 2's list is intact: connectivity, values,
  protection thresholds, F1, the LTC4368 architecture, the Q2/Q3 MPNs, the four-FET back-to-back
  topology, `R75`, the MAX17048 architecture, the dead-cell / recovery topology, `D10`/`D11` as two
  distinct ratiometric devices, `D12`'s role, the battery envelope and every major mechanical
  interface.
* **Q3 was not rotated and did not move.** Section 5 allows a rotation only with the high-current
  orientation and pin mapping re-proven electrically; it was not needed, and a 1.0 mm Q3 shift was
  measured and found **worse** (it loses `Q2_CS` as well as `Q3_CS`).
* **The section 5 `Q3_CS` via authorisation was not used.** It was measured, it was not needed, and
  variant (d) shows it would not have worked anyway.
* **`U14` was not moved.** Section 7 permits it only if the real branch is still over 15 mm after
  TP15 is fixed. It is 6.387 mm.

---

## 11. Phase A on scratch — FAIL, and the best result this block has reached

**`PHASE A: FAIL` — 70 connections routed, 93 skipped as already joined, ratsnest 781 → 709 (−72).**
Against FBV2-P2-002E's 60 and −63, and FBV2-P2-002C's 27 and −32.

**DRC after every single connection was identical to the baseline** — `{solder_mask_bridge: 1,
unconnected_items: 499}` — no new violation of any class, at any step. **Zero out-of-scope copper.**

### What closed

**23 of 29 in-scope nets are single connected components**, including every one that
FBV2-P2-002E named as consequential:

| net | 002E | 002F |
|---|---|---|
| **`LTC_GATE`** | **two islands** — the LTC4368 GATE output not connected to the FETs it drives | **ONE component** |
| `Q3_CS` | `Q3.1` ‖ `Q3.3` | **connected, 5.500 mm, ZERO vias** |
| `Q2_CS` | connected | connected, 5.400 mm |
| `LTC_UV` | `U18.2` ‖ `R79.2` | **connected**, 6.150 mm |
| `LTC_OV` | open | **connected** |
| `N_BATDIV` | three islands | **connected** |
| `VREC_VCC` | open | **connected**, `U19.8 → C60.1` 2.689 mm |
| `VREF_TOP` | 48.58 mm | **connected**, 10.480 mm routed |
| `REF_HO` | open | **connected**, incl. `R91.2 → U19.5` 12.542 mm |
| `BAT_SENSE` / `BAT_MID` / `BAT_RAW` node / `BAT_CONNECTOR_P` | connected | connected |

### The measured battery block

| path | routed | width | vias | layer |
|---|---|---|---|---|
| `BAT_CONNECTOR_P` `J4.1 → F1.1` | 9.871 mm | 1.00 mm | 0 | B.Cu |
| `BAT_RAW` load `F1.2 → Q2.8 → Q2.7` | 7.996 mm | 1.00 / 0.80 mm | 0 | B.Cu |
| `BAT_MID` `Q2.5 → Q2.6 → Q3.8 → Q3.7` | 18.106 mm | 1.00 / 0.80 mm | 0 | B.Cu |
| `BAT_SENSE` load `Q3.5 → Q3.6 → R75.1` | 17.553 mm | **1.00 mm** | 2 | B.Cu + F.Cu |
| **`BAT_SENSE` Kelvin `R75.1 → U18.9`** | **5.254 mm** | 0.20 mm | **0** | B.Cu |
| **`BAT_PROTECTED_P` Kelvin `R75.2 → U18.8`** | **7.708 mm** | 0.20 mm | **0** | B.Cu |
| **R75 Kelvin MISMATCH** | **2.454 mm** | — | — | *(002E: 20.620 mm)* |
| `BAT_PROTECTED_P` trunk `R75.2 → D9.1` | 17.625 mm | **1.50 mm** | **0** | B.Cu |
| `BAT_PROTECTED_P` total at 1.50 mm | 93.374 mm | 1.50 mm | **0** | B.Cu |
| **`BAT_RAW` VIN tap `U18.1 → R77.1`** | **1.850 mm** | 0.20 mm | 0 | B.Cu | 
| **`U14.2 → TP15.1`** | **3.997 mm** | 0.15 mm | **0** | B.Cu |
| `U14.3 → U14.2` | joined | 0.15 mm | 0 | B.Cu |
| **`Q3_CS` `Q3.1 → Q3.3`** | **5.500 mm** | 0.25 mm | **0** | B.Cu |
| `Q2_CS` `Q2.1 → Q2.3` | 5.400 mm | 0.25 mm | 0 | B.Cu |
| `LTC_GATE` `Q3.2 → Q3.4` | 5.400 mm | 0.25 mm | 0 | B.Cu |
| `LTC_GATE` `Q3.2 → Q2.2` | 18.445 mm | 0.25 mm | 0 | B.Cu |
| `LTC4368_FAULT_N` `R82.1 → Q9.1` | 64.081 mm | 0.15 mm | 2 | B.Cu + F.Cu |
| `BAT_PROT_SHDN_CTL` `Q4.1 → R83.1` | 19.762 mm | 0.15 mm | 2 | B.Cu + F.Cu |
| `C59.1 → F1.2` | 3.407 mm | 0.60 mm | 0 | B.Cu |
| `C58.1 → D9.1` | 5.092 mm | **1.50 mm** | 0 | B.Cu |
| `TP34.1` stub | 1.523 mm | 0.60 mm | 0 | B.Cu |

**`U11.2` escape, re-measured on this placement:** 0.20 mm neck **0.575 mm** long, strictly
monotonic flare to 1.50 mm, **no via, no thermal relief, 4.214 mΩ over 4.878 mm** — unchanged and
inside every §5 cap.

**Section 4's quality targets, all met:** both Kelvin branches ≤ 10 mm (5.254 / 7.708), mismatch
**2.454 mm** against the 5 mm limit, and `U18.1` VIN at **1.850 mm** against a 10 mm target — down
from 32.204 mm.

### Why it is still a FAIL

Section 14 is unambiguous: *"Phase A passes only if ALL in-scope functional battery/protection
connections close simultaneously on ONE scratch board… No partial pass."* **Six nets are in two
islands each**, and four of those are a single stranded pad:

| net | the island that did not join |
|---|---|
| `BAT_RAW` | `{R80.1}` — the LTC_SHDN divider bottom |
| `BAT_PROTECTED_P` | `{TP15.1, U14.2, U14.3}` — the MAX17048 sense island |
| `REF_POL` | `{U19.2}` |
| `N_POL` | `{U19.3}` |
| `LTC4368_FAULT_N` | `{TP18.1}` — a test point |
| `BAT_PROT_SHDN_CTL` | `{TP19.1}` — a test point |

The run then stopped on a **rule** rather than a corridor: `BAT_PROTECTED_P TP15.1 → (node)` was
rejected because its 0.20 mm stub sits **outside** the `BAT_PROT_TAP_U14` corridor and therefore
falls under D-249's 1.20 mm trunk floor. That corridor is generated from the branch's own routed
copper, and the U14 branch never joined the main node — so the corridor never grew to cover the
stub. **It is a harness consequence of the U14 island, not an independent defect**, and it is
recorded here rather than fixed, because fixing it would not close the island.

**Phase B was NOT RUN.** Section 17 gates it on Phase A passing.

---

## 12. B-34 from Phase A copper (scratch, NOT authoritative)

Section 16 permits this for comparison only.

| segment | length | widths | copper |
|---|---|---|---|
| `BAT_CONNECTOR_P` | 11.394 mm | 1.00 / 0.60 | 6.09 mΩ |
| `BAT_RAW` load | 7.996 mm | 1.00 / 0.80 | ≈ 4.4 mΩ |
| `BAT_MID` | 18.106 mm | 1.00 / 0.80 | 9.30 mΩ |
| `BAT_SENSE` load | 17.553 mm | 1.00 | ≈ 8.6 mΩ + 1.76 mΩ (2 vias) |
| `BAT_PROTECTED_P` trunk | 93.374 mm | 1.50 | ≈ 30.6 mΩ |
| `U11.2` escape | 4.878 mm | 0.20 → 1.50 | 4.21 mΩ |

**Pack-current copper ≈ 64.9 mΩ**, against ≈ 65 mΩ at FBV2-P2-002E and ≈ 75 mΩ at 002C. **The
placement ECO did not cost the load path anything.**

* at **1.5 A**: ≈ **97 mV** / ≈ **146 mW** of copper loss
* at **1.75 A**: ≈ **114 mV** / ≈ **199 mW**

**Exclusions, stated explicitly:** F1, Q2/Q3 R_DS(on), the BQ25185 BATFET, connector and contact
resistance, and temperature rise. Those dominate the total and none of them is copper.

**B-34 STAYS OPEN.** This is scratch copper on a placement that did not pass Phase A, and section 16
forbids closing B-34 from it. **Physical first-article validation remains mandatory.**

---

## 14. Issues raised for CTO / owner ruling

| id | issue | status |
|---|---|---|
| **PR-25** | U18 cannot escape all eight pins where it sits. | **CLOSED.** Rotated to 180 and moved to (8.000, 65.250) by measured search; **8/8 escapes, 8/8 routed.** |
| **PR-26** | `Q3_CS` and `LTC_GATE` cannot both escape Q3's south row. | **CLOSED WITHOUT A VIA.** CS before gate closes both on B.Cu; the §5 layer-drop authorisation was measured and **not used**. |
| **PR-27** | Megohm dead-cell spans of 64.5 / 60.1 mm. | **CLOSED to the ABSOLUTE MAX, not the target.** Worst node **18.43 mm** against 20 mm; 11 of 15 inside the 15 mm target. **The four that are not are bounded by Q5…Q9 and need them in scope — carried forward.** |
| **PR-28** | `U18.1` 32.204 mm, Kelvin mismatch 20.620 mm. | **CLOSED.** `U18.1` **1.850 mm**, mismatch **2.454 mm**. |
| **PR-29** | `U14.2` 31.228 mm. | **CLOSED.** **6.387 mm**, U14 did not move. |
| **PR-30** | Fine-pitch slack ties were broken by list order. | **CLOSED** — broken by ways-out, fewest first. |
| **PR-31** | A partner placed on the far side of its pin wraps the package. | **CLOSED** — scored and penalised in the ring solver. |
| **PR-32** | Once-per-pass measurement cannot separate pins that tie at the head of the pass. | **CLOSED** — re-measured before every fine-pitch pin. |
| **PR-33** | U19 is an SOT-23-8 on 0.65 mm pitch and had **no** measured ordering at all. | **CLOSED** — `tight` is now a group name; U18 and U19 are each ordered within themselves. Recovered three U19 pins. |
| **PR-34** | **`R80.1`, `U19.2`, `U19.3` and the `{TP15, U14.2, U14.3}` island do not join their nets.** Four pads and one island, on a board where 23 of 29 in-scope nets are single components. | **OPEN — the reason Phase A fails.** `U19.2`/`U19.3` are a U19 placement question of the same kind PR-25 answered for U18; the U14 island is the west-edge 0.15 mm channel, unchanged since 002C. |
| **PR-35** | A test-point stub outside its own generated corridor is judged against the D-249 trunk floor, so `TP15.1 → (node)` is rejected at 0.20 mm. | **OPEN — harness.** A consequence of the U14 island; the corridor is grown from routed copper that does not exist. |

---

## 15. What was NOT done, deliberately

* **No authoritative signal copper was written.** Section 18 is unconditional, and Phase A did not
  pass in any case. `aqroot-Beta-v2.kicad_pcb` is **byte-identical to `24f6611`** — zero tracks,
  zero signal vias, In1 GND plane intact.
* **The placement ECO was NOT applied to the authoritative board.** Section 23 forbids committing an
  unproven placement, and a placement that does not pass section 13 is not proven. `place_p2_002f.py`
  is committed as **the searched, gated, reproducible result** — a script, not an applied change.
* **Phase B was not run.** Section 17 gates it on Phase A.
* **B-34 is not closed** and is not recalculated authoritatively.
* **No architecture was weakened to finish.** Connectivity, values, protection thresholds, F1, the
  LTC4368 architecture, the Q2/Q3 MPNs, the four-FET topology, `R75`, the MAX17048 architecture, the
  dead-cell topology, `D10`/`D11` as two distinct ratiometric devices, `D12`'s role, the battery
  envelope and every major mechanical interface are untouched. **Zero out-of-scope copper.**
* **Q3 was neither moved nor rotated**; a 1.0 mm shift was measured and found worse.
* **The §5 `Q3_CS` via authorisation was not used.**
* **U14 was not moved.**
* **No converter routing was started.**

---

## 16. The lesson worth keeping

Four times in this task, a placement passed a proof and then failed a route:

1. the ring whose targets **crossed** in front of the pins they served;
2. the ring whose targets were **stacked** at one offset;
3. the dead-cell compaction that **shortened every span and deleted the channels**;
4. the parts that landed on the **far side of J4**, where a Euclidean span metric cannot see a 6 mm
   through-hole connector.

Every one passed the section 12 escape gate — including its section 3C simultaneity test — because
**an escape proof measures a 0.5 mm stub and a connection is a route.** The gate is necessary and it
is not sufficient, and the honest fix was not a better proxy but a worse-scaling one: route the pin
field, with the real router, against the copper the plan actually lays first. That is what
`checks/ring_probe_002f.py` does, and it is what turned 6/8 into 8/8.

**PCB routing remains 0 %. Overall Full Beta v2 remains 74 %.** No progress is claimed and none was
earned: there is no authoritative signal copper on this board.
