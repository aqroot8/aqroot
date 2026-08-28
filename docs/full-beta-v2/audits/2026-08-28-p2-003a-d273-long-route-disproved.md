# FBV2-P2-003A — D-273: the long outer-B.Cu zero-via route is disproved; next is a bounded F.Cu high-current via bridge

**Date:** 2026-08-28 · **Task:** FBV2-P2-003A · **Starting HEAD:** `1a82652`
**Verdict:** **ROUTING-PROOF CLOSEOUT — a measured FAIL.** D-272 sent the trunk
question out of placement scope and into a bounded routing proof: test the
**reservation-dependent LONG outer-B.Cu route** for `BAT_PROTECTED_P` before any
F.Cu via bridge, because it keeps the trunk on outer 1 oz with zero
current-carrying vias. 003A runs that proof on the proven c3 board (U18 8/8,
trunk open) and it **fails**: no long outer-B.Cu **zero-via** corridor carries
`BAT_PROTECTED_P` from `R75.2` to the eastern node copper at the **1.50 mm
target or the 1.20 mm floor.** This is a **real measured FAIL** — the bounded
family probe rejects every family, and a **full-default-budget** run of the same
`connect_role` primitive the router uses for the trunk, straight to the node
copper, independently returns NO_LEGAL_ESCAPE (1.50) / NO_PATH (1.20) to every
node target. `c3_00` remains **evidence only, not promoted.** The authoritative
PCB is unchanged — six copper layers, **0 signal tracks, 0 signal vias.** **This
is NOT an owner decision;** the next technical task is a **bounded named-path
F.Cu high-current via-bridge investigation**, requiring evidence-based via-array
sizing and full safety / DRC / connectivity gates. B-34 remains open.

---

## 1. The task, the ruling, and what "disproved" means

D-272 exhausted bounded placement and framed the next step as CTO/engineering
scope, not an owner escalation:

> "The next technical task tests the reservation-dependent LONG outer B.Cu route
> for `BAT_PROTECTED_P` FIRST … its ~2.29× trunk resistance / ~18.9 mW extra at
> 1.5 A is an engineering tradeoff to VERIFY, not an owner escalation. The F.Cu
> high-current via bridge remains a DEFERRED FALLBACK, not authorized."

003A is that verification. "Disproved" here means a **routed / obstacle-aware
search fact**, not an analytic clearance: on the reproduced c3 board, no B.Cu
corridor of width ≥ 1.20 mm, zero vias, exists from `R75.2` to any point on the
existing `BAT_PROTECTED_P` node copper — going the long way round the western
control-copper mass just as much as the short way.

The CTO ruling for this closeout (D-273):

- **The long outer-B.Cu zero-via route is disproved** at target 1.50 mm and
  floor 1.20 mm. It is a measured FAIL, corroborated by the router's own search
  primitive at full budgets.
- **`c3_00` stays evidence only.** It is not promoted to the authoritative
  placement or to authoritative copper; its bit 8 (`BAT_PROTECTED_P
  R75.2→U11.2`) remains open.
- **The authoritative PCB is unchanged** — six layers, 0 signal tracks, 0 signal
  vias; no KiCad source mutated.
- **No owner escalation.** The via-policy question does not reach the owner here;
  the long-route proof was the gate, and it has now run.
- **Next task: a bounded named-path F.Cu high-current via-bridge investigation**
  — evidence-based via-array sizing (the inner layers are 0.5 oz, where 1.5 A at
  a 10 K rise needs ~2.73 mm by the board's own `.kicad_dru` arithmetic, so the
  bridge is an array, not one via) with full safety / DRC / connectivity gates.
  It is **not implemented or tested in 003A.**

---

## 2. The board under test, and its reproduction

The measurement runs on `w/c3repro003a_parent/aqroot-Beta-v2.kicad_pcb`, the
parent's reproduction of the D-272 c3 board. That board is the AUTHORITATIVE
placement plus the pinned c3 recipe `c3_00.json` (R75 `[2.8,65,270]`, U18
`[4.0,72.9,90]`, R79 east `[9.825,67.825,0]`) driven through the pinned arbiter
`run_prefix_002z.py`. The committed reproduction triple confirms it:

- `result_c3repro003a_parent.json`: `applied=true`, `asserted=true`,
  `mismatch=false`, `targets="111111101"`, `u18=8`, `u18_open=[]`, `ledger="7/29"`,
  `sense_mm=13.811`, `returncode=0`.
- `probe_c3repro003a_parent.json`: `U18` 8/8; `BAT_PROTECTED_P R75.2->U11.2 =
  false` — the western BPP trunk (target bit 8) is the one open connection.
- `log_c3repro003a_parent.txt`: the arbiter's run log.

These are the same numbers D-272 recorded for `c3_e10n_r79` / `c3_00`, so the
board 003A measures is the proven-8/8, trunk-open board, reproduced — not a new
or better placement. `inspect_003a.py` re-reads it live and confirms the
geometry: `R75.2` at (2.800, 67.963), the node copper as one large B.Cu cluster
(x 38.48…66.40, L≈89.6 mm), the D9 reservation stub as a small cluster with its
free end at (10.800, 73.000), and the western BPP copper as a separate small
cluster (x 0.60…5.22).

---

## 3. Why a bounded family probe, and why it is honest

The first draft, `long_corridor_003a.py`, sampled join anchors along the whole
node copper and ran a full `connect_role` to each. Its **first east trial alone
burned > 18 min** of CPU on a single whole-board wave to a far anchor (rc130):
an un-bounded A*/wave that cannot reach its target explores the entire reachable
region, which on this board is enormous. That script is **retained** as the
documented rejected approach (it is what motivated the bounded redesign and is
named by the two scripts that replace it), but it is not the measurement.

`long_corridor_003a_bounded.py` replaces it with a **small, fixed set of
geometrically distinct LONG route families**, each an explicit waypoint chain so
every obstacle-aware search runs over a **small bounded window**. Boundedness is
enforced four ways (D-273 requirement 3): waypoints ≤ ~13 mm apart; `QR.ASTAR_BUDGET`
/ `QR.WAVE_BUDGET` capped to probe sizes; a per-hop SIGALRM wall-clock backstop
that records any residual runaway as a **TIMEOUT** (a legitimate non-PASS, never
a hang); and a coarse (0.25 mm) reachability **prefilter** that records a
`COARSE_BLOCKED` hop without ever running the fine search.

**The coverage argument (D-273 requirement 2).** Every long B.Cu corridor from
`R75.2` to the node must (a) escape the western control-copper mass and (b) cross
the single central free channel to the node. `occ_003a.py` prints the B.Cu
occupancy of the working band and shows exactly one connected central free
channel (x ≈ 13…38 mm) linking the western margin to the node's west edge; the
channel is therefore **not the discriminator** — the **escape latitude** out of
the western mass is. The mass is thinnest at three latitudes (north y≈58, mid
y≈75, south y≈83), covered by families **F1/F2/F3**; **F4** starts at the D9
reservation free end and tests whether D9's own committed exit reaches the node
the long way. East is the node, west is the board edge, so there is no fourth
macroscopically distinct family; more sampled anchors would only re-probe the one
channel — the un-bounded trap. `joins_003a.py` records the exact nearest
node-copper coordinate each family targets.

---

## 4. The measurement (bounded families)

`long_corridor_003a_bounded.json`, re-run end-to-end and reproduced
byte-identically (only the board-path string and wall-clock `dt` differ):

- **Control** — the SHORT direct `R75.2 → D9.1`: **@1.50 NO_LEGAL_ESCAPE**,
  **@1.20 NO_PATH** (a real 1.76 s fine search). This is D-272's severed-corridor
  fact, re-measured.
- **F1_north / F2_mid / F3_south / F4_resv_first — ALL FAIL at both widths.**
  - **@1.50 mm:** `R75.2` has **NO_LEGAL_ESCAPE** on B.Cu — it cannot even leave
    its own pad at 1.5 mm (blocked by board_edge, track, U18.6, U18.7). F4 (which
    starts at the reserved end, not the pad) is **COARSE_BLOCKED**.
  - **@1.20 mm:** `R75.2` escapes only ~2.7 mm to (5.5, 67.95), and the **first
    traversal out of the western mass is COARSE_BLOCKED**; F4 is COARSE_BLOCKED.

No bounded family yields a legal B.Cu long corridor: `NONE`.

---

## 5. The corroboration — full budgets, no coarse prefilter

A 0.25 mm coarse grid can **over-block** (its 0.75-cell guard inflates every
obstacle), so a `COARSE_BLOCKED` verdict, on its own, only proves no path exists
**on the coarse grid.** `long_corridor_003a_corrob.py` removes that doubt: it
runs the **same `QR.connect_role` the router uses for the trunk**, from `R75.2`
straight to four representative node-copper points (west tip, NE diagonal, SE
diagonal, centroid), at the **default FULL budgets (ASTAR=500000, WAVE=3000)**,
with **no coarse prefilter**, each trial wall-clock capped at 120 s.

`long_corridor_003a_corrob.json` — **all 8 trials FAIL:**

| target | @1.50 | @1.20 |
|---|---|---|
| node_west_tip | NO_LEGAL_ESCAPE (0.0 s) | NO_PATH (~53 s) |
| node_NE_diag | NO_LEGAL_ESCAPE (0.0 s) | NO_PATH (~61 s) |
| node_SE_diag | NO_LEGAL_ESCAPE (0.0 s) | NO_PATH (~61 s) |
| node_centroid | NO_LEGAL_ESCAPE (0.0 s) | NO_PATH (~0.5 s) |

The 1.20 mm trials ran **48–62 s each** and returned NO_PATH by **exhausting the
reachable region**, not by hitting the 120 s cap — a genuine full-budget "there
is no corridor," not a starved or coarse-gated one. This is the un-bounded search
the naive script attempted, aimed at four targets instead of a whole-net sample,
so it finishes in minutes. **It corroborates the bounded probe exactly:** the
COARSE_BLOCKED verdicts are real.

---

## 6. What this does and does not prove

- **Proven:** on the reproduced c3 board, no zero-via B.Cu corridor of width
  ≥ 1.20 mm joins `R75.2` to the node copper — short or long. `R75.2` is copper-
  locked deep in the western mass; the one central free channel is unreachable at
  trunk width; leaving the margin does not help because the pad cannot escape to
  the margin's free lanes in the first place. This confirms and tightens
  D-270/271/272: the western blocker is real, current-carrying copper, and the
  saturation is **in the plane**, not along a length.
- **NOT claimed:** nothing here is presented as a routed PASS. `c3_00` is not
  promoted; no authoritative copper is written; the F.Cu via bridge is **not**
  implemented or tested — that is the next task, and it needs its own via-array
  sizing and gates. The long-route resistance/thermal tradeoff (~2.29× / ~18.9 mW
  at 1.5 A) is moot because the route does not exist at any legal width.

---

## 7. Regression added (does not weaken any constraint)

The D-273 measurement rests on the search **cap** doing two things at once, so
`router_regression.py` gains **G11 — the bounded-probe search contract**, pinned
on the AUTHORITATIVE board (the c3 scratch board it measured is not committed):

1. a **tiny** budget must BOUND the search — a genuinely routable short trunk
   becomes a prompt `NO_PATH` give-up that lays **no copper** and does not raise;
2. the budget the probe actually uses (ASTAR=60000 / WAVE=1200) must **not
   fabricate a FAIL** — it still routes a trunk that routes at the full default
   budget, so a bounded-budget FAIL is a real block, not a starved search.

Both run on a short routable trunk (`Q2_CS Q2.3→Q2.1`); the module budgets are
saved and restored so no other check is perturbed. **G11 is 4/4 PASS.** No width,
clearance, via, layer or connectivity rule is changed.

---

## 8. Suites, state, and the next blocker

**All suites re-run at this commit and PASS:**

- `router_regression` — **ALL CHECKS PASS**, G1–G9 + G10 + **new G11**.
- `d264_probe`, `d266_probe`, `d267_probe`, `d269_probe`, `d270_probe`,
  `dru_probe`, `netclass_probe` — all exit 0.

**Nothing moved and nothing relaxed:** D9, U18, R75, R76…R83, Q3, the shunt, the
FETs, TP17 and C58 all frozen; `c3_00` NOT promoted; D-249, D-264, D-266, D-267,
D-269, D-270, D-271, D-272 untouched; the outer-1-oz / zero-via high-current
policy unchanged; the authoritative PCB is six copper layers with 0 signal tracks
and 0 signal vias and no KiCad source was mutated. `phaseA_journal.json` scratch
churn restored.

**U19 NOT SEARCHED**; Phase A NOT passed; Phase B NOT run; converter routing NOT
started. **B-34 REMAINS OPEN.**

**The precise next blocker:** `BAT_PROTECTED_P R75.2 → U11.2` (target bit 8) is
open, and neither the short nor the long outer-B.Cu zero-via route can close it —
the western margin cannot host U18 8/8, the `BAT_SENSE` current path and a
≥ 1.20 mm zero-via B.Cu trunk at once. The next technical task is a **bounded
named-path F.Cu high-current via-bridge investigation**: an evidence-sized via
array carrying the trunk current between B.Cu and F.Cu, proven against the
project's own thermal/current rules and DRC and connectivity gates. **No progress
earned: PCB routing stays 0 %, overall stays 74 %.**
