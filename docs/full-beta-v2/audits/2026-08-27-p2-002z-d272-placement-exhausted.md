# FBV2-P2-002Z — D-272: western-margin placement scope is exhausted; the first reproducible U18 8/8 does not close the BPP trunk

**Date:** 2026-08-27 · **Task:** FBV2-P2-002Z · **Starting HEAD:** `016aeee`
**Verdict:** **PLACEMENT-SCOPE CLOSEOUT.** Bounded battery-block placement was **CTO
authority (D-249…D-271), and it is now exhausted.** Across a full cardinality
ladder — one component, R75+U18, R75+U18+one divider, and a bounded-exhaustive
U18-pose vacate sweep — **no legal fan-8 placement makes the analytic western
`BAT_PROTECTED_P` trunk reach even 0.80 mm on B.Cu, and none closes target bit 8
(`BAT_PROTECTED_P R75.2→U11.2`) in a supervised run.** The task delivers the
**first reproducible U18 8/8** (`c3_e10n_r79` / `c3_00`) — accepted **as evidence
only, not promoted to placement or authoritative copper** — with bit 8 still open.
This is **not an OWNER decision.** The next technical task tests the
**reservation-dependent LONG outer B.Cu route** for `BAT_PROTECTED_P` first,
because it preserves outer 1 oz and the high-current zero-via policy; its known
**~2.29× trunk resistance / ~18.9 mW extra at 1.5 A** is an engineering tradeoff
to **verify**, not an owner escalation. The F.Cu high-current via bridge remains a
**deferred fallback, not authorized.** The authoritative PCB is unchanged — six
copper layers, **0 signal tracks, 0 signal vias.**

---

## 1. The task, the ruling, and what "exhausted" means

FBV2-P2-002Y pinned the reproduction gap and localised the blocker to the
current-carrying `BAT_SENSE` diagonal, then framed the choice as an OWNER call
(D-271). 002Z takes the one thing still inside CTO/placement authority — **can any
legal component placement, not just the frozen one, close the western margin?** —
and answers it exhaustively. The CTO ruling for this closeout:

- **Placement scope is accepted as exhausted.** Bounded placement was CTO
  authority; the ladder below spends it to its floor.
- **`c3_00` is evidence only.** It is the first reproducible U18 8/8, but its
  target bit 8 (`BAT_PROTECTED_P R75.2→U11.2`) is open. It is **NOT promoted** to
  the authoritative placement and **no authoritative copper is written.**
- **This is NOT labelled an OWNER decision.** The next technical task is a
  routing proof, not an escalation.
- **Next task: the reservation-dependent LONG B.Cu route first** — it keeps the
  trunk on outer 1 oz with zero current-carrying vias; the ~2.29× resistance /
  ~18.9 mW-at-1.5 A cost is verified there, not escalated here.
- **The F.Cu high-current via bridge is a deferred fallback, not authorized.**

## 2. The one casualty, fixed across the whole ladder

Every supervised run in this task — all card-1, card-2 and card-3 runs, including
the first reproducible U18 8/8 — leaves exactly one target open:

> **`BAT_PROTECTED_P R75.2 → U11.2`** — target bit 8 — the current-carrying
> western BPP trunk, **1.50 mm target / 1.20 mm floor, B.Cu, zero via** (the
> D-270 frozen path role).

The analytic prefilter is calibrated against the real arbiter and trusted: the
graded `trunk_best_w` metric reads the c2 base at **0.40 mm**, the c3 R79-east
winner at **0.80 mm**, and both are below the **1.20 mm floor**, exactly matching
the still-open trunk in every real run.

## 3. The cardinality ladder — baseline 6/8 to a negative 705-pose sweep

| stage | family | evidence | best U18 | bit 8 (`R75.2→U11.2`) | analytic trunk |
|---|---|---|---|---|---|
| **baseline** | U18 authoritative pose alone (`b1_u18ctrl`) | `cardinality1_aggregate.json` | **6/8** (open U18.7, U18.8) | open | — |
| **c1** | one component: U18 \| R75 \| Q3 × rotation×translation | `cardinality1_aggregate.json` (6 poses) | **ceiling 7/8** (`b1_r75rot`) | open | — |
| **c2** | R75 + U18 | `cardinality2_aggregate.json` (5 supervised) | **ceiling 7/8** | **open — invariant in all 5** | 0.40 mm (e10n) |
| **c3** | R75 + U18 + one divider | `cardinality3_aggregate.json` (4 supervised), `c3_prefilter_report.json` | **8/8** (`c3_e10n_r79` / `c3_00`) | **open — false in all 4** | 0.80 mm (R79 east) |
| **c4** | U18-pose trunk-lane vacate sweep | `c4_prefilter.json` (705 poses) | — | — | **0.40 mm ceiling; 0 reach floor** |

**(a) Baseline 6/8.** The authoritative U18 pose alone routes 6/8; `U18.7` and
`U18.8` are both open. De-bulging the `BAT_SENSE` diagonal is a precondition to
anything better.

**(b) c1 — ceiling 7.** No single component lands all of `{U18.7, U18.8, U18.2}`.
The two casualties (pin-7 escape, pin-8 Kelvin reach) are complementary levers: an
R75 180-swap seals U18.7, an R75 nudge east seals U18.8 instead, and over-rotating
seals U18.2 and drops the ledger. The minimum viable move is therefore
cardinality 2.

**(c) c2 — ceiling 7 and the bit-8 invariant.** Five supervised R75+U18 poses all
cap at U18 7/8, and **target bit 8 is FALSE in every one**, independent of which
pin (7, 8 or 2) the fanout leaves open. Root cause, measured: the western BPP
trunk `R75.2→D9.1` routes **freely at 1.50 mm (13.12 mm) when NO fanout is laid**
but is **dead at every width down to 0.40 mm once the 8-pin U18 fanout is laid.**
The binder is the whole fanout band saturating the board-edge-bounded west margin
— a plane-saturation problem, **not a single obstacle.**

**(d) c3 — the first reproducible U18 8/8, and bit 8 still false.** Of 243 fan-8
mechanically-clean candidates the prefilter found exactly **one meaningful lever:**
base `e10n` (U18 `[4.0, 72.9, 90]`, R75 `[2.8, 65.0, 270]`) plus **R79 east**
`[9.825, 67.825, 0]`, which widens the analytic B.Cu trunk from **0.40 → 0.80 mm**.
The supervised run `c3_e10n_r79` (`c3_00`) reaches **U18 8/8 (open none), targets
`111111101`, ledger 7/29, sense 13.811 mm, returncode 0, applied+asserted true,
mismatch false** — **but target bit 8 (`BAT_PROTECTED_P R75.2→U11.2`) is FALSE.**
The 8/8 is real but knife-edge: nudging U18 west (3.5) or east (4.5) re-opens
U18.7 (runs `c3_e10n_r79w/ww/e`). The 0.80 mm corridor is real and sub-floor, and
the arbiter's F.Cu current-escape staging did not convert it into a routed trunk.

**(e) c4 — the last placement family, negative.** `place_search_c4_002z.py` is the
U18-pose vacate sweep: relocate/reorient U18 so its fanout band **vacates the
y≈72.8 east-west trunk lane**, scored on graded `trunk_best_w`, not more divider
spreading. Swept **705 poses** bounded-exhaustively over the legal fan-8 region
(616 card-2 poses: R75 {rot 270, rot 90} × U18 {4 rotations × dx 2.5..5.5 × dy
69.4..74.4, 0.5 mm grid} + 89 card-3 minimal-support poses). Result **NEGATIVE:**
`c4_prefilter.json` records **102 fan-8 mech-clean poses, `best_overall_trunk_w`
= 0.40 mm, `n_winners_ge_floor` = 0.** `trunk_best_w` is only ever 0.40 mm (50
poses) or dead (52); **zero reach 0.60 mm, let alone the 1.20 mm floor.** Fan-8
survives only in U18 rotations 90/180 at x 2.5–4.5, y 70.9–74.4 — a narrow basin
in which the fanout band always fills the west-margin lane; U18 cannot be
reoriented off the lane without losing a fanout pin, and Kelvin-B (k9) is already
tight (min 9.18 mm vs 10 mm limit). The same `trunk_best_w` code reads the c3
R79-east winner at 0.80 mm, so the 0.40 mm ceiling here is a real result, not an
under-measurement.

**The divider family is analytically exhausted too:** card-3 single (242/243 no
better than base) and card-4 divider pairs (0 reach 1.0 mm) both fail the floor;
the rigid R76..R83 column is trunk-inert and was **not** re-enumerated
(partial-column shifts are trunk-inert, full-column east mechanically rejects
against D9).

## 4. Conclusion — the western margin cannot hold all three roles at once

No legal fan-8 component placement — single, R75+U18, +divider, or U18-pose
vacate — makes the analytic western BPP trunk reach even **0.80 mm**, and none
closes `BAT_PROTECTED_P R75.2→U11.2` in a supervised run. The western margin
cannot simultaneously host **U18 8/8**, the current-carrying **`BAT_SENSE` path**,
and a **≥1.20 mm B.Cu BPP trunk**. The trunk routes at 1.50 mm only when it can
use a corridor the fanout occupies — the margin is saturated **in the plane, not
along a length.** Closing bit 8 therefore requires leaving the saturated west
margin, and that is a **routing/topology** move, taken next task — **not a
placement ECO and not, by this ruling, an owner escalation.**

## 5. The next task, and why it is a proof and not an escalation

Two routes leave the saturated plane; the CTO orders them tried in this order:

1. **LONG outer B.Cu (primary, next task).** Route `BAT_PROTECTED_P R75.2→U11.2`
   the long way on B.Cu around the west margin, reservation-dependent, **no layer
   change.** It **preserves outer 1 oz copper and the high-current zero-via
   policy** — the simplest DRC story and no F.Cu keep-out interaction. Its known
   cost is **~2.29× nominal trunk resistance / ~18.9 mW of extra dissipation at
   1.5 A** (quantified from the D-267 reservation analysis). That number is an
   **engineering tradeoff to verify on real copper next task**, not a reason to
   escalate to the owner.
2. **F.Cu high-current via bridge (deferred fallback, NOT authorized).** Via up to
   F.Cu, run the short free corridor, via back down near U11.2 with a qualified
   high-current via array. It buys room on the layer axis but requires a qualified
   via array and F.Cu keep-out review, and it touches the high-current
   zero-via policy — so it is held in reserve **only** if the long B.Cu route
   fails its resistance/DRC verification.

## 6. This explicitly supersedes D-271's owner-escalation framing

D-271 (FBV2-P2-002Y) closed by naming the western-margin oversubscription an
**OWNER call** — take a protection-architecture route, or authorise a placement
change. **002Z supersedes that framing.** The placement-change half was **CTO
authority all along**, and 002Z has now spent it to exhaustion across the full
cardinality ladder: there is no legal placement to authorise. What remains is a
**bounded routing proof (the long outer B.Cu route), which is CTO/engineering
scope**, to be run and measured before any high-current via-policy change is even
considered. The owner is **not** in the loop for the next step; the via-policy
question only reaches the owner if the long-route proof fails. D-271's "either is
an OWNER call" is therefore narrowed: **placement is closed by CTO authority, and
the immediate next action is a technical route verification, not an escalation.**

## 7. Delivered — analytic scripts, a concurrency-safe DRC fix, and a new G10 guard

- **`place_search_002z.py`, `place_search_c3_002z.py`, `place_search_c4_002z.py`**
  — the cardinality-1/2, cardinality-3, and U18-pose-vacate analytic prefilters.
  `run_prefix_002z.py` is the pinned-recipe arbiter used for the supervised runs
  (parent-supervised; not launched this step).
- **Generalized process-unique DRC transient (`path_role_util.py`).** `RU.drc()`
  wrote a fixed-name transient (`drc_Abase.json`), read it straight back, and used
  it nowhere else — but the placement SEARCH runs many `route_battery_block`
  prefixes at once on a shared `WORK`, so two concurrent same-phase runs clobbered
  the same file and one `json.load()` read a half-written file ("Unterminated
  string"), crashing that prefix at random. The transient path is now
  **process-unique (`drc_%s_%d.json % (tag, os.getpid())`) and reclaimed after the
  read.** This changes **no routing result and no single-run output** — only where
  the transient lands — so the pinned prefix stays byte-identical.
- **`router_regression.py` G10 — the guard is the collision itself.** Two
  processes call `RU.drc` with the same fixed tag on a shared `WORK` at the same
  time; both must return the exact authoritative baseline histogram and neither may
  raise. Four clauses: the source contract (path process-unique **and** reclaimed),
  the behavioural collision (both `rc==0`, no torn json), both runs read the
  authoritative baseline histogram, and no transient survives in the shared `WORK`.
  **All four PASS.**

## 8. Suites and board state

- **Starting HEAD:** `016aeee`. **Ending HEAD:** this commit.
- **Authoritative PCB:** six copper layers (JLC06161H-7628), **0 signal tracks,
  0 signal vias — unchanged and verified** (`pcbnew` load: 6 layers, 0 tracks, 0
  arcs, 0 vias; the `kicad/` tree is byte-for-byte HEAD). No placement ECO. TP17,
  C58, D9, U18, R75, R76..R83, Q3, the shunt and the protection FETs all frozen.
  No converter, no Phase B, no U19.
- **`router_regression.py` (re-run at this commit): ALL CHECKS PASS**, G1–G9 and
  the new **G10 (4/4).**
- **Standing suites PASS, unregressed** (all exit 0, re-run at this commit):
  `d264_probe`, `d266_probe`, `d267_probe`, `d269_probe`, `d270_probe`,
  `dru_probe`, `netclass_probe`.
- **`phaseA_journal.json`** scratch churn (timing deltas + a scratch `RESERVE_RUN`
  entry) **restored to HEAD** — it is a run-written journal, not evidence.
- **Evidence retained** (`checks/place_002z/`): the supervised `result_`/`log_`/
  `probe_` triples for all c1/c2/c3 runs, candidate JSONs, the three
  `cardinalityN_aggregate.json`, `c3_prefilter*`/`c4_prefilter.json`,
  `run_manifest_c3.json`, and `D272_closeout.json`. The transient `run_*.out`
  driver stdout captures (`START <epoch>` markers and duplicates of `result_*`)
  were dropped — no repo convention tracks `.out` files, and the audit evidence is
  the result/log/probe triple.

## 9. What was NOT done

D9, U18, R75, R76..R83, Q3, the shunt, the protection FETs, **TP17 and C58** all
frozen. **No placement ECO, and `c3_00` is NOT promoted** — it is carried forward
as evidence only. No signal track and no signal via written to the authoritative
board. **No long B.Cu route and no F.Cu via bridge attempted** — both are next-task
routing work; the F.Cu via bridge is not authorized. No netclass, width,
clearance, layer, via, annular or hole rule changed — 002Z adds one concurrency
fix and one regression clause and changes **no** routing result. D-249, D-264,
D-266, D-267, D-269, D-270 untouched; high-current outer-1-oz / zero-via policy
unchanged. **U19 NOT SEARCHED. Phase A NOT passed. Phase B NOT run. Converter
routing NOT started.** B-34 remains open. **No progress earned:** PCB routing
stays 0 %, overall stays 74 %.

## 10. Exact next blocker

> **`BAT_PROTECTED_P R75.2 → U11.2`** (target bit 8) — the western BPP trunk —
> is **open at ≥1.20 mm on B.Cu in the saturated west margin.** Placement cannot
> open it (proven here). **Next task: route it the long way on outer B.Cu
> (reservation-dependent, zero current-carrying vias), and verify the ~2.29×
> resistance / ~18.9 mW-at-1.5 A cost is acceptable.** If that fails, the deferred
> F.Cu high-current via bridge returns for authorization. B-34 remains open.
