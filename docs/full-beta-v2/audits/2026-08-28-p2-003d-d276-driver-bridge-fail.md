# FBV2-P2-003D — D-276: the driver-integrated vacate + F.Cu bridge is a MEASURED REPRODUCIBLE FAIL; 003C/D-275 stands as the fixed proven solution for 003E

**Date:** 2026-08-28 · **Task:** FBV2-P2-003D · **Starting HEAD:** `b3a7e65`
**Verdict:** **MEASURED REPRODUCIBLE FAIL — 003D does not pass production /
full-driver promotion.** D-275 (003C) proved the western-corridor vacate + F.Cu
via-array bridge as a **post-process of a hand-staged reproduced c3 board** and
named the next task: integrate that mechanism into the production Phase-A driver
and drive it through a **full 2-pass Phase-A route** (the D-271 reproducibility
discipline). 003D did exactly that integration — and the full-driver route
**reproducibly fails**. On a board produced by the production driver
(`route_battery_block.py`, guarded by `AQROOT_BRIDGE_ECO`), two things are true
and reproduce across independent passes:

1. **Phase A fails earlier, at the U19 recovery-comparator block:**
   `N_POL U19.3→(node) (SIG) : NO_LEGAL_ESCAPE : U19.3: NO LEGAL ESCAPE at
   ≥ 0.150 mm; blocked by board_edge (×23), U19.4 (×16), U19.2 (×12), U19.6 (×8)`.
2. **The integrated 003C-style vacate-then-bridge ECO aborts:**
   `ECO ABORT: no ≥ 1.20 mm F.Cu traverse corridor` (the vacate runs — 6 F.Cu
   tracks moved, 48 existing vias seen — but on the *full production board* there
   is no ≥ 1.20 mm F.Cu lane to bridge, unlike the hand-staged 003C board).

**003C / D-275 is NOT invalidated.** Its post-processed, reproducible
`BAT_PROTECTED_P` closure remains proven evidence and is the **fixed solution to
preserve into 003E**. 003D establishes that the *full production driver* does not
yet reach the state in which that proven closure can be applied — the board fails
upstream at U19.3, and the western F.Cu corridor is not open on the driver's own
routed board. **This is engineering, not an OWNER decision.** The authoritative
PCB is left **untouched — six copper layers, 0 signal tracks, 0 signal vias**.

---

## 1. The decisive measurement, reproduced

Three full driver results were recorded and retained as evidence:

| result | ECO? | Phase-A `fail` | bridge ECO | conn | skip | ratsnest | Δ |
|---|---|---|---|---|---|---|---|
| `phaseA_003d.json` | no | N_POL U19.3→(node) NO_LEGAL_ESCAPE | (none) | 68 | 91 | 710 | −71 |
| `phaseA_003d_ecoC.json` | yes | N_POL U19.3→(node) NO_LEGAL_ESCAPE | `ok:false` — no ≥ 1.20 mm F.Cu traverse corridor | 68 | 91 | 710 | −71 |
| `phaseA_003d_ecoD.json` | yes | N_POL U19.3→(node) NO_LEGAL_ESCAPE | `ok:false` — no ≥ 1.20 mm F.Cu traverse corridor | 68 | 91 | 710 | −71 |

- **DRC (all three, identical to the authoritative baseline):**
  `hole_clearance 5 / lib_footprint_issues 199 / solder_mask_bridge 1 /
  unconnected_items 499`.
- **Blockers on U19.3 (ecoC and ecoD identical):** `board_edge ×23, U19.4 ×16,
  U19.2 ×12, U19.6 ×8` at the ≥ 0.150 mm escape.
- **bridge_eco (ecoC/ecoD identical):** `vacated 6`, `existing_vias 48`,
  `traverse.ok false`, `fail "no ≥ 1.20 mm F.Cu traverse corridor"`.

**2-pass determinism (the D-271 discipline applied to the FAIL).** `ecoC` and
`ecoD` are not byte-identical files — they differ only in per-net wall-clock
`secs` jitter (e.g. 1.6 vs 1.7 s on individual nets). Every **decisive**
measurement is identical: the Phase-A `fail` string, `connections`, `skipped`,
`ratsnest`, `ratsnest_delta`, the DRC histogram, and the bridge-ECO abort. The
terminal lines of both logs agree exactly:

```
  ECO ABORT: no >= 1.20 mm F.Cu traverse corridor
BRIDGE ECO FAIL -- no >= 1.20 mm F.Cu traverse corridor
PHASE A: FAIL -- N_POL U19.3->(node) (SIG) : NO_LEGAL_ESCAPE : U19.3: NO LEGAL
  ESCAPE at >= 0.150 mm; blocked by board_edge (x23), U19.4 (x16), U19.2 (x12),
  U19.6 (x8)
```

The base result (`phaseA_003d.json`, no ECO) proves the U19.3 Phase-A failure is
**upstream of and independent of** the bridge ECO: the same fail and the same
decisive counts appear with the ECO hook disabled.

## 2. Why the full-driver route fails where the 003C post-process passed

003C proved the vacate+bridge on a **hand-staged reproduced c3 board** whose
placement/route left exactly the western BPP trunk open (PR-40 bit 8) and, once
one low-current control branch (`BAT_PROT_SHDN_CTL`) was vacated to In3, a
1.40 mm F.Cu corridor from R75.2 to the eastern node. 003D runs the *full
production Phase-A driver*, which routes the whole board in its own order. On
that board:

- the driver never reaches a clean 8/8 U18 + trunk-open end state, because
  **Phase A stops earlier** — `N_POL U19.3` cannot escape its pad at ≥ 0.150 mm,
  walled by the board edge and its three neighbour comparator pins
  (U19.4/U19.2/U19.6); and
- with the ECO enabled, the vacate executes but the subsequent traverse search
  finds **no ≥ 1.20 mm F.Cu corridor** on the driver's own copper — the western
  margin is not in the open state the hand-staged 003C board presented.

So the 003C mechanism is not *wrong*; the production driver does not *arrive at
the state where it applies*. The gating problem is now **U19.3 pad escape**, a
new and distinct blocker from the D-270…D-274 western-BPP-trunk arc.

## 3. The orchestration failure — continuation/orchestration loss, not engineering, not OWNER

The 003D measurements are sound; the reason this task needed a fresh continuation
is an **orchestration/continuation loss**, recorded here so it is not repeated:

- The CTO launched the ecoC/ecoD passes with `nohup setsid … &` from a **one-shot
  turn**, then ended that turn with a normal text response — **no `sessions_yield`,
  no persistent waiter, and no completion callback registered against the child
  PIDs (274901 / 274902)**.
- The detached children **survived and finished at 04:31 UTC** and wrote their
  result JSONs correctly. But a process exit **cannot itself re-awaken an
  already-ended turn** — there was nothing listening for it.
- The separate Claude finalize ACP session had **already ended at the wait
  boundary** and likewise provided no completion event.

This was therefore a loss of continuation, **not an engineering failure and not
an OWNER decision**. (The earlier, incomplete `ecoA`/`ecoB` passes — 422 lines,
no verdict, no result JSON — were killed when ecoC/ecoD were relaunched; they are
scratch and were removed, not committed.)

**Repair discipline (recorded as the standing rule):**

- The **ACP/finalize task owns the foreground work and returns a completion
  event** when it finishes.
- The **CTO uses `sessions_yield`** at the wait boundary and **resumes from that
  completion event**, rather than ending the turn.
- **No unregistered detached child batches** — every long-running child is either
  owned by a foreground task that yields a completion event, or is tracked by a
  persistent waiter keyed to its PID.

## 4. What was delivered, and the regression

- **Driver integration (kept, env-guarded, inert by default):**
  `route_battery_block.py` gains a single `if os.environ.get('AQROOT_BRIDGE_ECO'):`
  block that, after the full route and before the authoritative DRC/ratsnest,
  calls `bridge_eco_003d.apply_eco(pcb)` and records its result under `bridge_eco`.
  With the env var unset (the default), the hook is inert and the driver behaves
  exactly as at HEAD.
- **003D helpers (evidence of the integrated mechanism):**
  `bridge_eco_003d.py` (the in-line vacate+bridge stage, single-sourcing the
  D-275 copper primitives and constants **verbatim** from `bridge_route_003c`) and
  `bridge_gates_003d.py` (the driver-integrated gate, reusing the proven 003C gate
  contract).
- **Regression — `bridge_probe_003d.py`, converted to pin the measured
  reproducible FAIL.** As first authored it presumed a *passing* driver-integrated
  gate (it required a `bridge_gates_003d_*.json` with `pr40_eco == 111111111`),
  which never existed because the ECO aborts. It is rewritten to pin the honest
  D-276 outcome:
  - **A** — the driver hook is wired and ordered before the authoritative DRC;
  - **B** — `bridge_eco_003d` single-sources the D-275 constants and copper
    primitives from `bridge_route_003c` (no divergent re-implementation);
  - **C** — the vacate stays cardinality-1 / control-role only (path-role
    classifier: `BAT_PROT_SHDN_CTL` is a candidate, the current-carrying nets are
    not);
  - **D** — each recorded `phaseA_003d_eco*.json` reports the measured FAIL (bridge
    ECO abort *and* the N_POL U19.3 NO_LEGAL_ESCAPE), and **no pass claims a
    promotion** (no `bridge_eco.ok`, no closed trunk) absent a real full-gate PASS;
  - **E** — 2-pass determinism of the FAIL: the decisive measurements are
    identical across the ≥ 2 recorded passes.
  **D-276 DRIVER BRIDGE PROBE: PASS** (it now guards against a future edit that
  silently re-reports the driver bridge as passing without a real gate).

## 5. Suites, state, and cleanliness

**All suites re-run at this commit and PASS, unregressed:**

- `router_regression` — ALL CHECKS incl. G1–G11.
- `bridge_probe_003d` (rewritten, FAIL-pinning) — PASS.
- `bridge_probe_003c` — PASS (**003C/D-275 confirmed intact and not invalidated**).
- `via_array_probe`, `d264/d266/d267/d269/d270_probe`, `dru_probe`,
  `netclass_probe` — all PASS.

**Worktree hygiene:** `phaseA_journal.json` scratch churn **restored to HEAD**
(the decisive evidence lives in the `phaseA_003d*.json` results and the ecoC/ecoD
logs, not the journal). The incomplete `log_phaseA003d_ecoA.txt` /
`ecoB.txt` scratch (no verdict, no result JSON) **removed**. The `w/` working
boards and `__pycache__` remain git-ignored. Retained committed evidence:
`phaseA_003d.json`, `phaseA_003d_ecoC.json`, `phaseA_003d_ecoD.json`, the three
`bridge_*_003d.py` helpers, and under `place_002z/`: `log_c3repro003d.txt`,
`log_phaseA003d_ecoC.txt`, `log_phaseA003d_ecoD.txt`, `probe_c3repro003d.json`,
`result_c3repro003d.json`.

**Nothing moved and nothing relaxed:** D9, U18, R75, R76…R83, Q3, the shunt, the
FETs, TP17 and C58 all frozen; `c3_00` NOT promoted; D-249, D-264, D-266, D-267,
D-269, D-270, D-271, D-272, D-273, D-274, **D-275** all untouched;
outer-1-oz / high-current policy unchanged; no safety weakening; no
topology/net change; no authoritative promotion. **U19.3 is now the named
blocker.** Phase A NOT passed; Phase B NOT run; converter routing NOT started.
B-34 remains as recorded (updated only on a real promotion). Authoritative PCB
UNCHANGED — six copper layers, 0 signal tracks, 0 signal vias, no KiCad source
mutated.

## 6. The next task — FBV2-P2-003E (defined, not started here)

**FBV2-P2-003E: a bounded investigation of the U19.3 `N_POL` NO_LEGAL_ESCAPE,
holding the proven 003C `BAT_PROTECTED_P` vacate + F.Cu 4-via bridge solution
fixed.**

- **Goal.** Determine why `N_POL U19.3→(node)` has no legal ≥ 0.150 mm pad escape
  on the full driver board, and whether a bounded, safety-preserving fix exists —
  while the D-275 western-corridor vacate + bridge remains the fixed, proven trunk
  solution (not re-litigated).
- **Distinguish the three candidate causes:**
  1. **pad-escape geometry** — U19.3 cannot leave its own pad at 0.150 mm given
     the board edge + neighbour pins (analytic pad-escape / fan-out study);
  2. **route-order / copper obstruction** — the escape is blocked only because of
     what the driver routed *before* U19, i.e. a scheduling/obstruction artifact,
     not intrinsic geometry;
  3. **minimum placement ECO** — the smallest placement nudge of U19 (and/or its
     neighbours) that restores a legal escape, if 1 and 2 are exhausted.
- **What to inspect:** U19.3, and its blockers U19.2 / U19.4 / U19.6 and the
  board edge (×23 the dominant blocker), at the recovery-comparator cluster.
- **Method:** analytic / pad-escape geometry first, then the **smallest real
  router probes**; no broad placement search.
- **Constraints (hard):** no topology or net change; no safety weakening; the
  proven 003C vacate + F.Cu 4-via bridge held fixed; **no authoritative promotion
  unless a later full gate passes.**

**No authoritative progress earned: PCB routing stays 0 %, overall stays 74 %.**
003D closes as a measured reproducible FAIL of full-driver promotion; the western
BPP trunk closure (D-275) stands; the blocker is now U19.3 pad escape.
