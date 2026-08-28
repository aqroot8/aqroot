# FBV2-P2-003C — D-275: the western-corridor vacate ECO + F.Cu via-array bridge is PROVEN; the BAT_PROTECTED_P trunk closes on real, reproducible copper

**Date:** 2026-08-28 · **Task:** FBV2-P2-003C · **Starting HEAD:** `1fa37e1`
**Verdict:** **PROVEN — a real-copper PASS, the first BPP trunk closure in the
D-270…D-274 arc.** D-274 disproved the bounded F.Cu high-current via bridge and
named the next task: a **bounded western-corridor control-net vacate ECO** to
open a ≥ 1.20 mm F.Cu lane, then route the bridge. 003C runs that ECO on the
reproduced c3 board and it **succeeds.** The minimum vacate set is **cardinality
1** — moving a single **low-current control branch, `BAT_PROT_SHDN_CTL`, off
F.Cu to In3** — which opens a **≥ 1.20 mm (1.40 mm achieved) F.Cu corridor from
R75.2 to the eastern BPP node** (NOT the D9 stub, so the D-274 single-via
D9→node link never carries pack current). A real **4-via / 1.40 mm F.Cu /
4-via** bridge then **closes bit 8, `BAT_PROTECTED_P R75.2 → U11.2`**: on
save/reload KiCad, **PR-40 is 9/9 (`111111111`)**, **U18 stays 8/8**, **no new
DRC violation of any class**, **no connectivity regression**, and the **ratsnest
falls by exactly 1.** This overturns the D-273/D-274 reading that the western
margin is "saturated on both outer layers" — it is saturated only while one
control branch walls the F.Cu corridor, and that branch is not current-carrying,
so path-role offload legally frees it. **This is NOT an owner decision.** The
authoritative PCB is left **untouched — six copper layers, 0 signal tracks, 0
signal vias** — because promotion to the authoritative product board requires
integrating the vacate+bridge into the Phase-A driver and promoting the c3
placement through a full 2-pass Phase-A route (the D-271 reproducibility
discipline); that is the immediate next task, and it is CTO/engineering scope.
B-34 gains ~18.9 mΩ / ~42–58 mW on the trunk.

---

## 1. The task, the ruling, and what "proven" means

D-274 closed the bounded F.Cu via bridge as a measured FAIL and framed 003C:

> "The next task is a **bounded control-net vacate ECO** — move the three named
> F.Cu control crossings out of the x 4.8…11 / y 66…73 window and re-measure the
> ≥ 1.20 mm F.Cu bridge lane."

003C is that ECO. "Proven" here is a **real routed / save-reload DRC +
connectivity fact**, not an analytic clearance: on the reproduced c3 board, after
one named low-current control branch is vacated to In3, a ≥ 1.20 mm F.Cu corridor
exists, a real via-array bridge is laid across it, and KiCad — reloading the saved
board — reports bit 8 connected, no new DRC, and no regression.

The CTO ruling (D-275):

- **The western-corridor vacate ECO + F.Cu via-array bridge is proven.** The
  minimum vacate is **cardinality 1** (`BAT_PROT_SHDN_CTL` → In3); the bridge is
  4-via entry / 1.40 mm F.Cu traverse / 4-via node landing; bit 8 closes with
  PR-40 9/9, U18 8/8, no new DRC, no regression.
- **D-274's three-crossing pessimism is corrected.** Only ONE branch discriminates
  the corridor, and it is a control signal, not current-carrying — so path-role
  offload (D-270's fifth property) legally moves it, and no `BAT_RAW`/`BAT_MAIN`
  inner-layer exception is created.
- **The result is reproducible from committed code.** `run_prefix_002z.py
  place_002z/c3_00.json` → the c3 board, then `bridge_route_003c.py bridge` →
  the closed board, both deterministic.
- **The authoritative product board is unchanged** — six layers, 0 signal tracks,
  0 signal vias; no KiCad source mutated. It is deliberately kept unrouted in
  this project (routing is a driver output), so "promotion" means making the
  driver reproduce the closure, which is the next task, not writing a
  script-laid board over the product artefact.
- **No owner escalation.** The vacate is a control-net re-route (D-270 class); the
  bridge is the D-274-authorised mechanism, now realised. Neither is a placement
  or protection-architecture change requiring the owner.

---

## 2. The board under test, reproduced byte-consistent with D-274

003C reproduces the pinned c3 board with `run_prefix_002z.py
place_002z/c3_00.json c3repro003c` (AUTHORITATIVE placement + pinned `c3_00.json`:
R75 `[2.8,65,270]`, U18 `[4.0,72.9,90]`, R79 east `[9.825,67.825,0]`). The
committed triple is identical to D-274's:

- `result_c3repro003c.json`: `applied=true`, `asserted=true`, `mismatch=false`,
  `targets="111111101"`, `u18=8`, `u18_open=[]`, `ledger="7/29"`,
  `sense_mm=13.811`, `returncode=0`.
- The one open target is bit 8, `BAT_PROTECTED_P R75.2→U11.2`.

---

## 3. The F.Cu vacate cut-set study — the minimum set is cardinality 1

`fcu_cutset_003c.py` → `place_002z/fcu_cutset_003c.json` is the requirement-2/3/6
instrumentation. It models the vacate of an INDIVIDUAL routed F.Cu **branch** (a
connected component of one candidate net's F.Cu copper), never a whole net and
never inner/current-carrying copper, and re-measures the bridge corridor (the
same flood + full-budget A* D-274 used). Candidate universe (requirement 3): the
F.Cu branches of the low-current control nets (`LTC_GATE`, `LTC_GATE_RC`,
`LTC_SHDN`, `LTC4368_FAULT_N`, `BAT_PROT_SHDN_CTL`) and the bounded microamp
`BAT_RAW` divider bridges. The current-carrying trunk / rails and the
`BAT_PROTECTED_P` destination copper are refused as candidates, loudly.

**Result (reproduced on two independent reproductions, c3repro003b and 003c):**

- **Baseline** (D-274 re-measured exactly): a full-width F.Cu corridor from R75.2
  floods to **x = 4.80 mm @1.20**, **4.65 mm @1.50**; **reaches the island: no.**
- **Vacating ALL 7 candidates** floods to x = 64.0 and reaches the node.
- **GREEDY MINIMAL = cardinality 1: `BAT_PROT_SHDN_CTL`.** Vacating that ONE
  branch turns the R75.2→node A* from NO_PATH to **PATH at both 1.50 and 1.20**.
  Exhaustive cardinality-0 (baseline) does not open, so **1 is the proven
  minimum.**

**Why one branch suffices, when D-274 named three.** D-274 measured the
FULL-WIDTH straight corridor, which dies at x = 4.80 (just west of the LTC_GATE
x = 5.75 vertical) and needs all three western crossings cleared to reach the D9
stub at x = 11. But `BAT_PROT_SHDN_CTL` is not a crossing — its F.Cu copper is a
**46 mm run that walls the west margin from y = 59.75 to y = 93.47** (x
1.65…12.78). Removing that wall lets R75.2 **detour north/south around** the
LTC_GATE vertical and the BAT_RAW run and reach the **open node at x = 38.5** via
the central free channel `occ_003a` identified — a landing that avoids the D9
single-via link entirely. The A* is the router's own primitive; its PATH verdict
is a real ≥ 1.20 mm corridor.

---

## 4. The real vacate + bridge (bridge_route_003c.py)

**VACATE.** `BAT_PROT_SHDN_CTL` routes `Q4.1 —B.Cu→ via(1.65,93.47) —F.Cu wall
(46 mm)→ via(8.68,59.75) —B.Cu→ R83.1`. Both end transitions are already THROUGH
vias (F↔B, so the barrel is copper on In3), so **moving the 6 F.Cu tracks to
In3.Cu preserves continuity and vacates F.Cu.** In3 is clear in the window
(In1/In4 are the GND planes, kept intact; In2 already carries the Kelvin/Q3_CS
inner copper). A control net was never barred from the inner layers (D-264 bars
only `BAT_MAIN` pack current), so this needs **no netclass rule** — it is the
D-270 offload principle applied to a control branch. Re-measured on the actual
vacated board: R75.2→node A* is **PATH at 1.50 and 1.20; flood reaches x = 64.**

**BRIDGE.** The measured mechanism, all clearing save/reload DRC:

- **ENTRY** — **4× 0.80/0.40 through vias** on R75.2's own B.Cu pad (POFV, D-258),
  scanned to be clear on every layer and hole-legal (edge gap ≥ 0.2495 mm) against
  the existing U18.8 sense via at the pad's north end, united by a 1.50 mm F.Cu
  bus. No B.Cu ties: the vias sit on the pad copper.
- **TRAVERSE** — **50.99 mm of 1.40 mm F.Cu** (1 oz outer), routed **via-aware**:
  QBoard skips `PCB_VIA`, so `bridge_route_003c.inject_vias` adds every board via
  as an all-layer obstacle at the **0.30 mm** trunk clearance the D-269 rule
  demands, and the traverse routes around them. (With strict via clearance, 1.50
  mm no longer fits — measured NO_PATH — so the ladder takes **1.40 mm**, above
  the 1.20 mm mandatory floor; the 1.50 mm target is honestly not reachable.)
- **EXIT** — **4× 0.80/0.40 through vias** landing on the node's own 1.20 mm B.Cu
  copper at (42.40, 76.40), each tied by a ≥ 1.20 mm F.Cu/B.Cu stub — an ARRAY
  landing, so **no single via carries pack current.** The node track is split at
  the landing into a real junction.

**Sizing (D-274, unchanged and regression-pinned by `via_array_probe`):** per-via
1.055 A internal/10 K; a single via and a two-via neck are REJECTED for 1.75 A;
the fault-tolerant floor is 3, the design target 4. Both transitions are 4-via,
so each tolerates a single-via fault with 3 remaining (3.17 A > 1.75 A).

---

## 5. The gates — a real save/reload PASS (bridge_gates_003c.py)

Reloaded from disk, KiCad BuildConnectivity + `pcb drc --severity-all`:

| gate | baseline c3repro003c | bridge c3bridge003c |
|---|---|---|
| PR-40 targets (A..I) | `111111101` | **`111111111`** |
| bit 8 `R75.2→U11.2` | open | **CLOSED** |
| U18 pin field | 8/8 | **8/8** |
| `BAT_PROT_SHDN_CTL Q4.1→R83.1` (vacated) | connected | **connected** |
| BAT_SENSE, LTC_GATE, LTC_OV, LTC_UV | connected | connected (no regression) |
| DRC classes | `{hole_clearance 5, lib_footprint 199, solder_mask 1, unconnected 499}` | **identical — 0 new** |
| ratsnest | 741 | **740 (−1)** |

`bridge_gates_003c.json`, **VERDICT: PASS** on every clause: bit8_closed,
all9_targets, u18_8of8, control/targets/u18 not regressed, no_new_drc,
ratsnest_not_worse. The one connection the regression check first flagged —
`Q4.1→TP19.1` — is **open on the baseline too**: TP19 is a test-point stub already
unrouted on the qualifying c3 board, not a vacate casualty (the ratsnest FELL, so
nothing was lost).

**Electricals** (`bridge_electrical_003c.json`): the 1.40 mm F.Cu traverse is
17.9 mΩ, the two 4-via arrays add 0.44 mΩ (D-274's N4 figure), **R_bridge ≈ 18.9
mΩ.** At 1.5 A: **42.5 mW, 28 mV** drop; at 1.75 A: **57.8 mW, 33 mV.** This is
the trunk's B-34 cost — real but modest, comparable to the D-267 long-route
tradeoff, except this path exists and is DRC-clean.

---

## 6. What this does and does not prove

- **Proven:** on the reproduced c3 board, vacating the single low-current
  `BAT_PROT_SHDN_CTL` branch to In3 opens a ≥ 1.20 mm F.Cu corridor R75.2→node,
  and a real 4-via/1.40 mm/4-via bridge closes bit 8 with PR-40 9/9, U18 8/8, no
  new DRC and no regression. The western margin **can** host the trunk — the
  saturation D-273/D-274 measured is relieved by one legal control-net offload.
- **NOT claimed:** this is not yet the authoritative product board. It is a
  pass-1 c3 board plus a script-laid bridge, on the c3 placement that D-272 kept
  evidence-only. Promotion (§8) requires driver integration + placement promotion
  + a full 2-pass Phase-A route. The 1.50 mm target was not reached (1.40 mm is
  the widest via-clear traverse); the 1.20 mm mandatory floor is exceeded.

---

## 7. Regression added (does not weaken any constraint)

`bridge_probe_003c.py` — the **D-275 vacate + bridge path-role contract**, real
copper + DRC + the recorded gate:

| clause | assertion | result |
|---|---|---|
| A | the vacated `BAT_PROT_SHDN_CTL` (control) on In3 | **ALLOWED** |
| B | the trunk `BAT_PROTECTED_P` on In2 | **REJECTED** (D-264) |
| C | the trunk `BAT_PROTECTED_P` on In3 | **REJECTED** (D-264) |
| D | a current-carrying role (SENSE/trunk/MID/CONNECTOR) as a vacate candidate | **REJECTED** |
| E | a control role as a vacate candidate | **candidate** |
| F | the bridge board closes bit 8, 9/9, U18 8/8, no new DRC, no regression | **PASS** |

**D-275 BRIDGE PROBE: PASS.** Via-array sizing (single/2-via rejected, ≥ 3 floor)
stays pinned by `via_array_probe`; overbroad/foreign-net corridor geometry by
`dru_probe`. No width, clearance, via, layer or connectivity rule is changed, and
no authoritative board is mutated.

---

## 8. The CTO recommendation — promote by driver integration + full Phase A

The trunk closure is proven and reproducible, but this project keeps the
authoritative product board **unrouted** (0 signal tracks/vias) and treats
routing as a driver output — precisely so the board can never drift from the code
that makes it (the D-271 lesson). Writing a script-laid bridge onto the product
board would recreate that drift. So the promotion path is:

1. **Integrate the D-275 vacate+bridge into `route_battery_block.py`** as a named
   mechanism (a `BAT_PROT_SHDN_CTL`→In3 offload set, and a
   `BAT_PROTECTED_P` F.Cu via-array bridge trunk mode), so a Phase-A run lays it.
2. **Promote the c3 placement** (R75/U18/R79 moves) to the authoritative
   placement — now justified, because c3 + bridge is a COMPLETE solution (U18 8/8
   AND bit 8 closed), which D-272 lacked when it held the placement back.
3. **Run a full 2-pass Phase-A route** with that mechanism and its final DRC, and
   promote the resulting board.

This is CTO/engineering scope. **The owner is not in the loop** — no protection
architecture, shunt/FET topology, TP17/C58 or converter decision is touched.

---

## 9. Suites, state, and the next blocker

**All suites re-run at this commit and PASS:**

- `router_regression` — **ALL CHECKS PASS** (G1–G11).
- **`bridge_probe_003c` — PASS** (new, D-275).
- `via_array_probe`, `dru_probe`, `d264_probe`, `d266_probe`, `d267_probe`,
  `d269_probe`, `d270_probe`, `netclass_probe` — all exit 0.
- `fcu_cutset_003c` — minimum vacate set cardinality 1, reproduced.
- `bridge_route_003c` / `bridge_gates_003c` — bridge laid, **gate PASS.**

**Nothing moved and nothing relaxed:** D9, U18, R75, R76…R83, Q3, the shunt, the
FETs, TP17 and C58 all frozen; `c3_00` NOT promoted; D-249, D-264, D-266, D-267,
D-269, D-270, D-271, D-272, D-273, D-274 untouched; the outer-1-oz / high-current
policy unchanged (the bridge keeps pack current on outer F.Cu + arrays, and the
only inner copper added is a control net); current-carrying `BAT_MAIN` clearance
not weakened; the authoritative PCB is six copper layers with 0 signal tracks and
0 signal vias and no KiCad source was mutated; `phaseA_journal.json` scratch churn
restored.

**U19 NOT SEARCHED**; Phase A NOT completed; Phase B NOT run; converter routing
NOT started. **B-34 to be updated** with the +18.9 mΩ / +42–58 mW bridge cost when
the closure is promoted.

**The precise next blocker:** the closure is proven on scratch but not yet in the
authoritative product board. The next technical task is the **driver-integrated,
c3-placement-promoted, full-Phase-A reproduction** of the D-275 vacate+bridge,
with its final DRC — after which PCB routing advances past 0 % for the first time.
**No authoritative progress earned yet: PCB routing stays 0 %, overall stays
74 %; but the western trunk blocker that stalled D-270…D-274 is broken.**
