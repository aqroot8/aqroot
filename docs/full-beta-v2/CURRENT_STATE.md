# AQROOT Full Beta v2 — CURRENT STATE (durable checkpoint)

> Checkpoint/index only. Authority precedence: **CTO_DECISIONS.md > accepted
> audits/engineering evidence > CURRENT_STATE.md > summaries/transcripts/session
> memory.** If this file conflicts with higher-authority evidence, repair this file.

## 1. Authoritative HEAD
- **FBV2-P2-003Y / D-299 (this checkpoint):** a governed **CTO ACCEPT + COMMIT + overall-run FAIL + HANDOFF**
  — the D-298 U19 CAPACITY lever's **full-authority gate COMPLETED** and it is a **GENUINE +2** connected-set
  gain (NOT the D-296 swap): vs the D-297 003W baseline (conn 70) connections **70→72**, and the connected-set
  diff GAINED **exactly 2** — `N_BATDIV R89.2→U19.6` and `REC_BAT_LOW (node)→U19.7` (both SIG, F.Cu, 2 vias,
  board-legal 0.60/0.30) — with **LOST 0**; `LTC4368_FAULT_N` detours CLEANLY (`R82.1→Q9.1` 77.567 mm, not the
  terminal wall); final DRC **identical** to 003W, no sub-0.50 non-fine via. So `AQROOT_U19CAP` is **ACCEPTED and
  COMMITTED** (banked env-gated / **OFF by default**, byte-identical when unset, pinned by **G14**). **Copper is
  NOT promoted** — full Phase-A still FAILs, the terminal wall newly ADVANCING **past the whole U19 field** to
  `LTC_GATE U18.10→Q3.4` (candidate join paths **DRC-gate-rejected** by the frozen **D-249** BPP 1.20 mm
  trunk-width and **D-269** BAT_MAIN 0.300 mm clearance rules — actual 0.20 mm / 0.2803 mm; NOT `NO_PATH`). The
  gate artifact is `checks/w/phaseA_003t_full_003y2_u19cap.json` (secs 1463.2, judged by `w/judge_003y2.py`); the
  shared `phaseA_journal.json` was restored byte-identical to HEAD and no process remains. **Readiness/progress
  UNCHANGED; autonomy CONTINUES** (no owner decision). Next: **FBV2-P2-003Z** — the `LTC_GATE U18.10→Q3.4` join
  corridor lever (§5). This checkpoint is written in the D-299 commit; a fresh session must confirm the live tip
  with `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-003X / D-298 (prior checkpoint):** a governed **CTO IMPLEMENT + SCREEN + HANDOFF** — the
  bounded U19 CAPACITY lever (`AQROOT_U19CAP`: reserve the U19.7/U19.6 shared east escape lane so
  `LTC4368_FAULT_N` detours, and close `REC_BAT_LOW U19.7` before `N_BATDIV U19.6`) is implemented
  env-gated / **OFF by default**, pinned by regression **G14**, and **screened DRC-clean** on the real
  003W full-run board (both boxed U19 pins escape SIMULTANEOUSLY onto bare In3/In2 with the only
  board-legal 0.65/0.40 via — a capacity ADD, categorically distinct from the refuted D-296 swap).
  **Copper is NOT promoted** — the ~22-min full-authority gate (net +2 vs swap; FAULT_N clean detour)
  has not run (exceeds the ACP cap; may not be backgrounded). Source is left **uncommitted** (docs
  committed) per the 003X discipline; **autonomy CONTINUES** (no owner decision raised). Next:
  **FBV2-P2-003Y** executes the gate (§5).
- **FBV2-P2-003W / D-297 milestone commit (prior checkpoint):** a governed **ACCEPT of a
  SECONDARY lever + a governed FAIL of the overall Phase-A run** (source + docs + probe commit);
  **autonomy CONTINUES** (a normal Phase-A FAIL is not a stop reason; no owner decision raised).
  003W implemented the D-295/D-296 SECONDARY lever — an env-gated (`AQROOT_U18BPP_JOIN`, **OFF by
  default**) override that completes the `BAT_PROTECTED_P U18.8 → R75.2` reserve **JOIN on In3**
  instead of the severed In2 lane — as a +25/−1-line change to `checks/route_battery_block.py`, pinned
  by a **G13** regression contract in `checks/router_regression.py` and the measured-record probe
  `checks/u18_i3_join_probe_003w.py`. **The wall (D-294/295):** at the direction-2 placement
  `t_a_r77e15n10_r79e15n10` the two 0.35/0.20 **THROUGH** reserve vias land at `R75.2`(2.800,66.800)
  and `U18.8`(7.200,66.500) on In2, and their In2 JOIN is `NO_PATH` — a `BAT_RAW` 0.600 mm
  current-path wall runs vertically on In2 at x≈6.4→6.65 (y 50.45→70.40), severing the west→east
  lane. **The lever:** the reserve vias are THROUGH vias (copper on every layer), so the join is
  electrically identical on In2 or In3; **In3.Cu is a routable six-layer signal layer**
  (`ROUTABLE[6]=('F','B','I2','I3')`) that is **EMPTY across the whole corridor** on the real
  full-run board (2 In3 tracks board-wide, none here; no In3 pour — only the In1/In4 GND planes), so
  `AQROOT_U18BPP_JOIN=I3` completes the ONE branch on In3 with **NO new via, NO DRU/floor change, NO
  topology change**; unset → the join stays on `va[2]` (In2), byte-identical to every prior run. **The
  probe** (on the actual full-run routed board, throwaway copy): In2 join `NO_PATH`, In3 join **ok
  4.410 mm**, real KiCad DRC **ZERO new classes**, `via_dangling` **1→0**. **The full authority gate**
  (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`, secs 1272.5) vs the D-294 baseline
  `w/phaseA_003t_full_e15n10cto.json`: connections **69→70** (+1), skipped-already-connected **98→99**
  (+1 — one downstream `BAT_PROTECTED_P` pad now found already-joined on the closed net; a positive
  sign, not a loss), ratsnest **708/−73 → 707/−74**, journal **72→73** (+1: `JOIN U18.8→R75.2` layer
  **I3**, 4.410 mm, **0 vias**), DRC `via_dangling` **1→0** with **no new class**
  (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1,
  unconnected_items:499}`), terminal fatal wall **UNCHANGED** (`REC_BAT_LOW U19.7→(node)
  NO_LEGAL_ESCAPE`, `N_BATDIV U19.6` next-in-line). **The decisive diff is a STRICT PURE GAIN:** the
  entire journal delta is **exactly one added JOIN entry with NOTHING lost** — the categorical
  opposite of D-296's 1-for-1 swap; the In3 join takes routing capacity from **no other net** (In3 is
  unused), so no casualty is possible and none occurs. **Ruling:** the SECONDARY lever is a genuine,
  board-legal, verified net gain — **ACCEPTED** and retained env-gated/OFF-by-default in tracked
  source (byte-identical when unset), pinned by G13 + the probe. **But copper is NOT promoted:**
  Phase-A copper promotes only on a full-authority PASS (D-286), and the run still FAILs on the
  unchanged saturated U19 field — so the authoritative board stays six layers / 0 tracks / 0 vias and
  **readiness/progress DO NOT move.** D-297 **banks** the U18.8 closure in source: once the U19 field
  is separately enlarged, this lever (ON) yields the U18.8 join for free (no new via, no new DRC).
  **No copper, no placement, no rule, no floor, no topology/footprint/outline change; no DRC absorbed;
  no promotion.** `/home/aqroot8/.aqroot-autopilot-stop` is ABSENT; autonomy continues with
  **FBV2-P2-003X** (§5) — a bounded U19 capacity lever for the simultaneous `REC_BAT_LOW U19.7` +
  `N_BATDIV U19.6` closure. Prior milestone: `27f9790` (D-296, 003V PRIMARY reservation family
  refuted). This checkpoint is written in the same commit; a fresh session must confirm the live tip
  with `git rev-parse HEAD` and `git rev-parse origin/master`.
- **Prior FBV2-P2-003V / D-296 milestone:** a governed **FAIL / primary-family refutation** commit
  (docs only); **autonomy CONTINUES**. 003V implemented the D-295 PRIMARY lever — an env-gated
  (`AQROOT_U19_RESV`, OFF by default) reservation of `REC_BAT_LOW U19.7`'s B.Cu escape scored toward
  Q7.1 — and full-gate-ran it twice. **RESV (0.35/0.20)** is behaviourally identical to D-294 (the
  corridor-less sub-minimum via is rejected on `via_diameter`/`annular_width`, the reservation is
  dropped, the run falls through unchanged; connected-set diff EMPTY both ways). **RESV2 (0.60/0.30
  board-legal)** FIRES and CLOSES U19.7 (rung self-corrects to the ordinary Default 0.60/0.30) — but
  it is a bounded **ordering trade**: conn 69 / skip 98 / ratsnest 708/−73 all unchanged, DRC
  identical, the terminal wall merely MOVES to `N_BATDIV U19.6`. **The decisive diff (D-294→RESV2) is
  a strict 1-for-1 swap:** GAINED `REC_BAT_LOW U19.7→Q7.1`, LOST `REF_POL TP24.1→U19.2`, count 68→68 —
  the U19 field is capacity-saturated, so reserving U19.7's lane only chooses which neighbour is
  abandoned. Positive finding recorded (the mechanism is REAL, U19.7 closable in principle,
  board-legal) but a swap is not a net gain, so per D-286 nothing promotes copper. **The
  `AQROOT_U19_RESV` source WIP was RETIRED** via an exact reverse patch (`git apply -R`; worktree blob
  `bba62d35…` = `HEAD:checks/route_battery_block.py`, `git grep U19_RESV` no match). No source/copper/
  placement/rule change survived; no DRC absorbed; no promotion. Prior milestone: `a2e27fc` (D-295).
- **Prior FBV2-P2-003U / D-295 milestone:** a governed **characterization / NO-PROGRESS + HANDOFF**
  commit (docs only); autonomy CONTINUES. 003U proved both D-294 walls are FULL-RUN-EMERGENT
  ordering/congestion casualties and NO cheap vehicle judges either at the direction-2 placement. The
  PRIMARY (`REC_BAT_LOW U19.7`) was diagnosed EXACTLY and shown REDUCIBLE-in-principle (it escaped
  cleanly in 003O as `U19.7→Q7.1` F.Cu 14.907 mm; direction-2's +2-connection congestion **swapped
  `VREC_VCC`'s two segments' layers** — `U19.8→C60.1` went B.Cu(0 via)→F.Cu(2 via) — so U19.8's
  pad-escape now occupies the F lane immediately south of U19.7 that carried U19.7 in 003O; `U19.8`
  ×26 the dominant blocker; U19.7 is a greedy-tightest-first casualty and, as a `(node)` join,
  ineligible for the D-278 inner hop guarded `and not node`). The SECONDARY (U18.8 I2 join corridor)
  is a full-congestion I2 pinch. The ~22-min governing gate cannot run foreground under the ACP
  10-min cap, so 003U delivered a precise CTO handoff. No source/copper/placement/rule change; no DRC
  absorbed; no promotion. Prior milestone: `36662db` (D-294).
- **HEAD == origin/master:** yes (committed and pushed at milestone closeout).
- **Prior milestones (full detail in §4 and CTO_DECISIONS):** `27f9790` D-296 (003V) PRIMARY
  reservation family refuted / WIP retired; `a2e27fc` D-295 (003U) two-walls characterization +
  handoff; `36662db` D-294 (003T) direction-2 executed / full gate FAIL; `9c708f3` D-293 owner
  approval of direction 2.

## 2. Mission
- Deliver Full Beta v2 to **READY FOR JLCPCB** — a fabricable, assembly-ready
  authoritative board with all governing routing / DRC / ERC / connectivity / safety
  gates passing and the final JLCPCB deliverables generated and reviewed.
- Terminal condition: **READY FOR JLCPCB**.

## 3. Current phase / gate
- **Phase P2 — battery/power-block Phase-A routing**, specifically completing a full Phase-A run at
  the D-293 direction-2 placement `t_a_r77e15n10_r79e15n10` with `BAT_PROTECTED_P` closed.
- **Current fabrication blocker (updated by D-299).** Direction-2 (D-294) plus the three accepted
  bounded levers (D-297 U18.8 In3-join, D-298 U19CAP) have resolved the west/BAT_RAW, U18.8 **and** the
  saturated U19 dead-cell field; **the SINGLE remaining Phase-A fabrication blocker is now `LTC_GATE
  U18.10→Q3.4`** — the LTC4368 gate-drive JOIN bridging the `U18.10` F.Cu escape cluster to the `Q3.4`
  B.Cu gate cluster. This is **NOT** `NO_PATH`/`NO_LEGAL_ESCAPE`: candidate paths ARE found but the
  per-connection `gate()` rejects every one for **two FROZEN owner rules** — **D-249** `BAT_PROTECTED_P`
  1.20 mm trunk width (candidate narrows to 0.20 mm inside the western-margin BPP trunk region) and
  **D-269** `BAT_MAIN` routed clearance 0.300 mm (candidate at 0.2803 mm, only ~19.7 µm short). A
  full-run-emergent congestion/corridor pinch on a flexible low-current control net, bounded and
  reducible in principle within CTO scope (the join has slack; the D-269 miss is ~20 µm). Status of the
  prior walls (all now closed under the full gate):
  - **U18.8 (`BAT_PROTECTED_P`) — CLOSED IN PRINCIPLE, banked (D-297).** The In3 reserve-JOIN lever
    is an ACCEPTED, board-legal +1 net gain (`U18.8→R75.2` on In3, 4.410 mm, 0 vias, `via_dangling`
    cleared, no new DRC). It is retained OFF-by-default in source and turns ON in the 003X full run;
    it is NOT yet promoted because the full run still fails on U19.
  - **REF_POL R87.2 F-corridor wall — PAST under direction-2** (+2 connections vs 003O); re-verify
    downstream on a full PASS.
  - **U19 dead-cell field — CLOSED under the full gate (D-299), lever committed.** D-296 proved a
    single-pin reservation only SWAPS the casualty; D-298 built the capacity ADD (`AQROOT_U19CAP`:
    reserve the U19.7/U19.6 shared east lane so `LTC4368_FAULT_N` detours + close U19.7 before U19.6);
    the FBV2-P2-003Y full-authority gate confirmed a **genuine +2** (both `REC_BAT_LOW U19.7` and
    `N_BATDIV U19.6` close, LOST 0, board-legal 0.60/0.30 vias, FAULT_N clean, DRC identical). ACCEPTED
    and COMMITTED env-gated / OFF-by-default (G14); re-verify downstream on a full PASS.
  - **`LTC_GATE U18.10→Q3.4` — the new terminal blocker (D-299).** Candidate paths DRC-gate-rejected by
    the frozen D-249 (BPP 1.20 mm trunk width) and D-269 (BAT_MAIN 0.300 mm clearance) rules; a bounded
    corridor/ordering lever within CTO scope (FBV2-P2-003Z, §5).
  - **BAT_RAW R89.1/R86.2 divider taps** — a capacity symptom, not a width lever; re-verify on a full
    PASS.

## 4. Last accepted milestone
- **Task:** FBV2-P2-003Y · **Decision:** **D-299** · **Result:** THE D-298 U19 CAPACITY LEVER'S
  FULL-AUTHORITY GATE COMPLETED AND IT IS A **GENUINE +2** CONNECTED-SET GAIN (NOT THE D-296 SWAP) — SO
  `AQROOT_U19CAP` IS **ACCEPTED AND COMMITTED** (banked env-gated / OFF-by-default, byte-identical when
  unset, pinned by **G14**); BUT COPPER IS NOT PROMOTED BECAUSE FULL PHASE-A STILL FAILs, THE TERMINAL
  WALL NEWLY ADVANCING PAST THE WHOLE U19 FIELD TO `LTC_GATE U18.10→Q3.4`, SO READINESS/PROGRESS DO NOT
  MOVE. The governing foreground run `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 bash w/run_003t_full.sh
  003y2_u19cap …` → `checks/w/phaseA_003t_full_003y2_u19cap.json` (secs 1463.2, driver exited clean;
  shared `phaseA_journal.json` restored byte-identical to HEAD; no process remains), judged by
  `checks/w/judge_003y2.py`. vs the D-297 003W baseline `w/phaseA_003t_full_003w_u18bpp_i3.json` (conn
  70): connections **70→72**, skipped **99→101**, ratsnest **707/−74→705/−76**, journal **73→75**; the
  connected-set diff GAINED **exactly 2** — `N_BATDIV R89.2→U19.6` and `REC_BAT_LOW (node)→U19.7` (both
  SIG, F.Cu, 2 vias, board-legal 0.60/0.30) — and LOST 0 (`U19.7` 15.621 mm, `U19.6` 9.52 mm). Both
  boxed U19 pins close SIMULTANEOUSLY for a strict +2 with nothing lost — the categorical opposite of
  D-296's 1-for-1 swap. `LTC4368_FAULT_N` DETOURS CLEANLY (all three branches on B.Cu; `R82.1→Q9.1`
  77.567 mm; not the terminal wall). Final DRC histogram IDENTICAL to 003W (`{hole_clearance:5,
  lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}`, no new
  class/increase); no sub-0.50 non-fine via (run via diameters 0.35/0.60/0.65/0.80). The new terminal
  wall `LTC_GATE U18.10→Q3.4` is candidate-paths-found-but-DRC-gate-rejected by the frozen D-249 (BPP
  1.20 mm, actual 0.20) and D-269 (BAT_MAIN 0.300 mm, actual 0.2803) rules — a bounded reducible
  corridor/ordering wall within CTO scope. A governed CTO ACCEPT + COMMIT + overall-run FAIL, NOT an
  owner decision (no floor relaxed, no frozen part moved, no DRU change); autonomy CONTINUES; no
  copper/placement/rule/floor/topology change, no DRC absorbed, no promotion, D-275 and D-277..D-298
  preserved. Tests: `router_regression.py` ALL PASS incl. **G14** (lever OFF by default → byte-identical;
  `AQROOT_U19CAP` activates; reserved-lane geometry spans U19.7/U19.6; hooks scoped to the U19 east lane
  + REC_BAT_LOW-before-N_BATDIV). Evidence of record: audit
  [`audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md`](audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md);
  committed source (`checks/route_battery_block.py` `AQROOT_U19CAP` lever, `checks/router_regression.py`
  G14); gitignored full-gate artifact (`checks/w/phaseA_003t_full_003y2_u19cap.json`, `w/judge_003y2.py`).
- **Prior milestone — FBV2-P2-003W · Decision:** **D-297** · **Result:** THE SECONDARY U18.8 I2-JOIN LEVER
  (the D-295/D-296 HANDOFF) COMPLETES `BAT_PROTECTED_P U18.8→R75.2` ON In3 FOR A **GENUINE +1
  CONNECTED-SET GAIN** — A PURE JOIN WITH NO CASUALTY, NO NEW VIA, NO NEW DRC CLASS, AND THE LONE
  `via_dangling` CLEARED — SO IT IS **ACCEPTED** AND RETAINED ENV-GATED / OFF-BY-DEFAULT IN TRACKED
  SOURCE; BUT COPPER IS NOT PROMOTED (THE FULL RUN STILL FAILs ON THE SATURATED U19 FIELD), SO
  READINESS/PROGRESS DO NOT MOVE. The reserve vias are THROUGH vias, so the join is electrically
  identical on In2/In3; In3.Cu is a routable six-layer signal layer (`ROUTABLE[6]=('F','B','I2','I3')`)
  EMPTY across the whole corridor (only In1/In4 GND pours), so `AQROOT_U18BPP_JOIN=I3` completes the
  ONE branch on In3 within D-257/D-266 mechanics. Probe (on the actual full-run routed board): In2
  `NO_PATH`, In3 **ok 4.410 mm**, real KiCad DRC ZERO new classes, `via_dangling` 1→0. Full gate
  (`w/phaseA_003t_full_003w_u18bpp_i3.json`, secs 1272.5) vs the D-294 baseline
  `w/phaseA_003t_full_e15n10cto.json`: connections **69→70**, skipped-already-connected **98→99**,
  ratsnest **708/−73→707/−74**, journal **72→73** (+1 `JOIN U18.8→R75.2` I3 4.410 mm 0 vias),
  `via_dangling` **1→0** with no new DRC class, terminal fatal wall UNCHANGED (`REC_BAT_LOW U19.7`,
  `N_BATDIV U19.6` next). The entire journal delta is EXACTLY one added JOIN with NOTHING lost — the
  opposite of D-296's swap; the In3 join takes capacity from no other net (In3 unused). A governed CTO
  ACCEPT + overall-run FAIL, NOT an owner decision (no floor relaxed, no frozen part moved, direction-2
  not exhausted); autonomy CONTINUES; no copper/placement/rule/floor/topology change, no DRC absorbed,
  no promotion, D-275 and D-277..D-296 preserved. Tests: `router_regression.py` ALL PASS incl. new
  **G13** (In3 routable; lever OFF by default → byte-identical; `=I3` activates; non-I2/I3 never
  activates; override scoped to exactly `BAT_PROTECTED_P U18.8→R75.2`); `u18_i3_join_probe_003w.py`
  ALL PASS. Evidence of record: audit
  [`audits/2026-08-30-p2-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md`](audits/2026-08-30-p2-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md);
  committed source (`checks/route_battery_block.py`, `checks/router_regression.py` G13,
  `checks/u18_i3_join_probe_003w.py`); gitignored scratch (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`,
  `w/FULL003T_e15n10cto/`, `w/TEST003W_PROBE/`, `w/run_003t_full.sh`,
  `w/cand_003t/t_a_r77e15n10_r79e15n10.json`).
- **Prior milestone — FBV2-P2-003V · Decision:** **D-296** · **Result:** THE PRIMARY U19.7
  ESCAPE-RESERVATION LEVER (the D-295 handoff) FIRES AND CLOSES U19.7 WITH A BOARD-LEGAL 0.60/0.30
  VIA, BUT IT IS A BOUNDED ORDERING TRADE WITH NO CONNECTED-SET PROGRESS — IT MERELY CHOOSES WHICH PIN
  OF THE SATURATED U19 FIELD IS THE CASUALTY (RESV2 GAINED `REC_BAT_LOW U19.7→Q7.1`, LOST `REF_POL
  TP24.1→U19.2`; conn 69/skip 98/ratsnest 708/−73 all unchanged; DRC identical; wall moves U19.7→U19.6;
  requested-connected 68→68). RESV (0.35/0.20) is behaviourally identical to D-294 (illegal
  sub-minimum via dropped; diff EMPTY both ways). REJECTED for production; the `AQROOT_U19_RESV` source
  WIP RETIRED via exact reverse patch (worktree blob `bba62d35…` = `HEAD:checks/route_battery_block.py`;
  `git grep U19_RESV` no match). Positive finding preserved (mechanism real, U19.7 closable in
  principle, board-legal). A governed FAIL, NOT an owner decision; autonomy CONTINUES; no
  source/copper/placement/rule change, no DRC absorbed, no promotion, D-275 and D-277..D-295 preserved.
  Evidence of record: audit
  [`audits/2026-08-30-p2-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md`](audits/2026-08-30-p2-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md);
  gitignored evidence (`checks/w/phaseA_003t_full_003v_u19resv.json`, `…_u19resv2.json`,
  `w/FULL003T_003v_u19resv*/`, `w/TEST003V_U19RESV/`).
- **Prior milestone — FBV2-P2-003U · Decision:** **D-295** · **Result:** THE TWO D-294 WALLS ARE
  FULL-RUN-EMERGENT ORDERING/CONGESTION CASUALTIES — NO CHEAP VEHICLE JUDGES EITHER AT THE DIRECTION-2
  PLACEMENT — AND THE PRIMARY (`REC_BAT_LOW U19.7`) IS DIAGNOSED EXACTLY AND SHOWN
  REDUCIBLE-IN-PRINCIPLE; THE GOVERNING ~22-min FULL GATE CANNOT RUN FOREGROUND UNDER THE ACP 10-min
  CAP, SO 003U DELIVERS A PRECISE CTO HANDOFF. A governed CTO characterization / NO-PROGRESS + HANDOFF,
  NOT an owner decision; autonomy CONTINUES; no source/copper/placement/rule change, no DRC absorbed,
  no promotion, D-275 and D-277..D-294 preserved. Evidence of record: audit
  [`audits/2026-08-30-p2-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md`](audits/2026-08-30-p2-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md).
- **Prior milestone — FBV2-P2-003T · Decision:** **D-294** · **Result:** DIRECTION 2 (D-293)
  EXECUTED — A FOCUSED MINIMUM CANDIDATE (`t_a_r77e15n10_r79e15n10`) GENUINELY EXISTS, BUT THE
  GOVERNING FULL AUTHORITY GATE FAILs, SO NO CANDIDATE IS PROMOTABLE. Direction-2 is PRODUCTIVE (+2
  connections vs 003O, `REF_POL R87.2` wall now past) but INCOMPLETE (U18.8 I2 join `NO_PATH`; new
  terminal `REC_BAT_LOW U19.7 NO_LEGAL_ESCAPE`). A governed CTO FAIL, NOT an owner decision; autonomy
  CONTINUES; no promotion, D-275 and D-277..D-293 preserved. Evidence: audit
  [`audits/2026-08-30-p2-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md`](audits/2026-08-30-p2-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md).
- **Prior milestone — FBV2-P2-003S · Decision:** **D-292** · **Result:** THE OWNER-APPROVED BOUNDED
  LTC4368/R75 PLACEMENT MICRO-ECO (D-291) IS SCREENED TO EXHAUSTION — NO BOUNDED U18/R75 PLACEMENT
  LEGALLY CO-CLOSES THE U18 ESCAPE FIELD (a both-edges current-path footprint geometry). A governed
  CTO FAIL that re-raised the OWNER decision (resolved by D-293). Evidence: audit
  [`audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md`](audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md).
- **Prior milestones — D-290/D-289/D-288/D-287/D-286** (full detail in CTO_DECISIONS and the audits):
  D-290 the last routing-only U18 co-closure lever refuted (owner decision, resolved by D-293);
  D-289 the 003P WIP retired and U18 co-closure refuted; D-288 the D-275 south-bridge entry-array
  two-layer tie fixed (`via_dangling`-clean, electrical pass); D-287 direction-1 space exhausted
  (27/27); D-286 the gate baseline measured on the actual complete pre-copper placement (regression
  G12).

## 5. Next task — FBV2-P2-003Z (the `LTC_GATE U18.10→Q3.4` join-corridor lever)
- **Where 003Y left it (D-299).** The D-298 U19 CAPACITY lever is now a **committed, gate-validated
  +2** (banked env-gated / OFF-by-default, G14). The full-authority gate advanced the terminal wall
  **past the whole U19 field** to a new, further blocker: `LTC_GATE U18.10→Q3.4`. Copper is still NOT
  promoted (full Phase-A FAILs at this wall).
- **Root cause (measured, `checks/w/phaseA_003t_full_003y2_u19cap.json`).** `LTC_GATE` is the LTC4368
  gate-drive net; its other segments are all connected (`U18.10→R76.1` on F.Cu — FINE_ESC_3, 2×
  0.35/0.20 vias; `Q3.2→Q3.4`/`Q2.2→Q2.4`/`Q3.2→Q2.2` on B.Cu). **The failing connection is the JOIN
  bridging the `U18.10` F.Cu escape cluster (north, y≈60–65) to the `Q3.4` B.Cu gate cluster (y≈59).**
  It is **NOT** `NO_PATH`/`NO_LEGAL_ESCAPE`: candidate paths ARE found, but the driver's per-connection
  `gate()` rejects every one for **two FROZEN owner rules** — **D-249** `BAT_PROTECTED_P` high-current
  trunk (min 1.20 mm; the candidate narrows to 0.20 mm where the BPP trunk-area rule applies, i.e. it
  enters the western-margin BPP trunk keep-region) and **D-269** `BAT_MAIN` routed clearance (0.300 mm;
  the candidate reaches only 0.2803 mm, ~19.7 µm short). A flexible low-current control net with slack,
  squeezed between the BPP trunk and a BAT_MAIN path — a bounded, reducible corridor/ordering pinch.
- **The lever (build ONE, env-gated OFF-by-default).** Re-site / re-order / detour the `LTC_GATE
  U18.10→Q3.4` join corridor so its path (a) stays **clear of the `BAT_PROTECTED_P` 1.20 mm trunk
  region** (route the join *around* the western-margin BPP trunk rather than through it — preserving
  D-249) and (b) opens the **0.300 mm `BAT_MAIN` clearance** (the miss is only ~20 µm — preserving
  D-269). All within existing **D-257/D-266** mechanics. OFF → byte-identical. **No DRU change, no via
  below the D-257 ladder, no D-290 re-auth, no D-249/D-269 relaxation, no topology/footprint/outline
  change.**
- **The governing run (CTO, persistent terminal, ~22 min):**
  `cd hardware/beta-v2/checks && cp phaseA_journal.json /tmp/phaseA_journal.HEAD.json &&
  AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 <lever env> bash w/run_003t_full.sh 003z_ltcgate
  w/cand_003t/t_a_r77e15n10_r79e15n10.json && cp /tmp/phaseA_journal.HEAD.json phaseA_journal.json`.
  Keep `AQROOT_U18BPP_JOIN=I3` **and** `AQROOT_U19CAP=1` **ON** (both accepted, D-297/D-299). **Judge
  by the full-run connected-set diff** vs `w/phaseA_003t_full_003y2_u19cap.json` and
  `w/phaseA_003t_full_003w_u18bpp_i3.json`: the run must close the `LTC_GATE` join for a real net gain
  with no new DRC class. **Promote copper only on a genuine full-authority Phase-A PASS** (D-286). All
  floors ENFORCED; D-290 stays closed.
- **Downstream, still CTO-scope:** on a full PASS, re-verify the (now-past) `REF_POL R87.2` F-corridor
  and the BAT_RAW R89.1/R86.2 divider taps.

## 6. Authoritative PCB state
- **Routing/promotion:** NOT promoted. Authoritative board = **six copper layers,
  0 signal tracks, 0 signal vias** (verified `sha256 2235e273…d642d7e`, byte-identical to HEAD);
  placement untouched (C36 home 63.75,73.75,0°; U18 home 3.0,72.4,90°). All 003O/003T/003W bridge/
  full-run copper lived only in gitignored scratch (`checks/w/`) and override files; the natural-run
  003O result `checks/phaseA_003o_b1_r75rot_cto.json` is committed as evidence of record, and the
  003T/003W full-authority results stay gitignored under scratch
  (`checks/w/phaseA_003t_full_e15n10cto.json`, `…003w_u18bpp_i3.json`, `FULL003T_e15n10cto/`).
- **Banked in source (D-297), NOT in copper:** the OFF-by-default `AQROOT_U18BPP_JOIN` In3-join lever
  (byte-identical when unset) closes `U18.8→R75.2` for a proven +1 gain when ON; it awaits the U19
  field closure and a full Phase-A PASS before any copper is promoted.
- **Banked in source (D-299), NOT in copper:** the OFF-by-default `AQROOT_U19CAP` U19 east-lane
  reservation + U19.7-first lever (byte-identical when unset), pinned by regression **G14** and now
  **gate-validated as a genuine +2** (FBV2-P2-003Y: closes `REC_BAT_LOW U19.7` + `N_BATDIV U19.6`, LOST
  0, board-legal 0.60/0.30 vias, FAULT_N clean, DRC identical). Source (`checks/route_battery_block.py`,
  `checks/router_regression.py`) is **COMMITTED**; it awaits the `LTC_GATE` closure and a full Phase-A
  PASS before any copper is promoted. Full-gate artifact (gitignored):
  `checks/w/phaseA_003t_full_003y2_u19cap.json`, judged by `checks/w/judge_003y2.py`.
- `phaseA_journal.json` at its committed HEAD state (driver never authoritatively invoked; the shared
  journal was backed up and restored around the full run; scratch churn discarded).
- PCB routing **0 %**; overall repo progress **74 %**.

## 7. Locked invariants (reference the D-xxx rulings, not the history)
- **D-275** forced-south `BAT_PROTECTED_P` bridge geometry (lane + landing proven). **D-288** the
  entry-array two-layer tie is FIXED (rotation-aware in-pad `scan_entry_sites` + symmetric B.Cu
  tie-stub, `via_dangling`-clean; an electrical pass, not merely geometric). The **0.60 mm BAT_MAIN
  minimum width** rule is a hard floor.
- **D-277..D-280** U19/deadcell escape + C61 landing-guard gains.
- **D-281/282/283** western-corridor route-scope fixes exhausted; **D-284 (OWNER)** approved
  landing-opening direction 1; **D-285** `place_003l` opens the C36.1 landing (clean).
- **D-286** the gate baseline is measured on the actual complete pre-copper placement; candidate
  placements must be screened with real full-placement DRC; a genuine placement short must be
  surfaced, never absorbed. **No proxy (focused vehicle / partial run) promotes copper — only a
  genuine full-authority Phase-A PASS does.** Regression G12 pins the corrected baseline order.
- **D-287** the bounded direction-1 placement space is EXHAUSTED (27/27); a `via_dangling` item is a
  genuine electrical fault and MUST fail.
- **D-289/D-290** the residual U18.8 `BAT_PROTECTED_P` escape is a **placement-geometry
  mutual-exclusion** at the 0.5 mm pad pitch vs the 0.300 mm current-path floor (D-269); the
  routing-only co-closure space (off-layer vacate of U18.7) is REFUTED — no routing-only site
  remains, so the U18.8 escape was an OWNER decision, **RESOLVED by D-293 (direction 2 authorized).**
- **D-293 (OWNER)** authorized **direction 2** — bounded LTC4368-block spread / escape-target
  relocation (R77/R79 east, R80/R81 north) so `BAT_RAW` (U18.1 east) and `BAT_PROTECTED_P` (U18.8
  west) escape through independent corridors — without relaxing D-269 or any floor, without accepting
  U18.8 open, without re-litigating D-290.
- **D-294 (003T)** direction 2 was EXECUTED under full CTO authority: a focused minimum candidate
  exists but the full gate FAILs, so no candidate is promotable. Direction-2 is PRODUCTIVE (+2 vs
  003O, `REF_POL R87.2` now past) but INCOMPLETE. **A focused `fail=None` is VACUOUS vs the congested
  full run — judge Phase-A changes by the full-run connected-set diff, promote copper only on
  full-authority evidence.**
- **D-295 (003U)** the two D-294 walls are full-run-emergent ordering/congestion casualties and no
  cheap vehicle judges either at the direction-2 placement; the PRIMARY (`REC_BAT_LOW U19.7`) is
  reducible-in-principle (direction-2's +2-connection congestion swapped `VREC_VCC U19.8`'s pad-escape
  from B.Cu onto the F lane U19.7 needs); both bounded levers are judgeable only by the ~22-min full
  gate. The U19.7 wall is an ordering class, NOT a D-289/290/292 placement mutual-exclusion.
- **D-296 (003V)** the PRIMARY U19.7 escape-reservation family is **REFUTED**: with a board-legal
  0.60/0.30 via the reservation fires and closes U19.7, but the U19 dead-cell field is
  **capacity-saturated on F.Cu/B.Cu**, so a single-pin reservation is a bounded **ordering trade** —
  it swaps the casualty (U19.7 ⇄ U19.2, wall U19.7→U19.6), earning NO net connected-set progress. Do
  NOT re-try single-pin U19 reservation; the U19 field needs a lever that ENLARGES capacity, not one
  that re-orders it.
- **D-297 (003W)** the SECONDARY U18.8 I2-join is closed by a **capacity add, not an ordering trade**:
  the reserve vias are THROUGH vias, In3.Cu is a routable six-layer signal layer that is bare across
  this corridor, so completing `U18.8→R75.2` on In3 (`AQROOT_U18BPP_JOIN=I3`) is a **genuine +1
  connected-set gain with no casualty, no new via, no new DRC class, and clears `via_dangling`** —
  because it takes capacity from no other net. **ACCEPTED and banked env-gated/OFF-by-default in
  source; copper is NOT promoted while the full run still FAILs on the U19 field.** The general lesson:
  the bare inner signal layers In2/In3 are unused capacity in this corridor and are the correct
  vehicle for enlarging a saturated F.Cu/B.Cu field (the U19 direction for 003X).
- **D-298 (003X)** the U19 field is closable by a **capacity ADD, not a swap**: U19.6/U19.7 (BOTTOM
  SOT-23-8) are pad-boxed N/S; their shared EAST lane is walled by the same `LTC4368_FAULT_N`
  cross-board run; POFV is DRU-barred (U19.6/U19.7 lack the D-257 fine-via exception the other three
  U19 pins have), so the escape needs a clear lateral lane + the legal 0.65/0.40 via. The
  `AQROOT_U19CAP` lever **reserves the shared east lane** (FAULT_N detours) and **closes U19.7 before
  U19.6** — both then escape, screened DRC-clean. IMPLEMENTED, regression-pinned (G14), OFF-by-default.
  Categorically distinct from the refuted D-296 single-pin lateral swap.
- **D-299 (003Y)** the D-298 lever's **full-authority gate CONFIRMED a genuine +2** (both `REC_BAT_LOW
  U19.7` and `N_BATDIV U19.6` close, LOST 0, board-legal 0.60/0.30 vias, `LTC4368_FAULT_N` detours
  clean, DRC identical) — so `AQROOT_U19CAP` is **ACCEPTED and COMMITTED** (banked OFF-by-default).
  **Copper NOT promoted** (D-286): full Phase-A still FAILs, the terminal wall newly advancing past the
  whole U19 field to **`LTC_GATE U18.10→Q3.4`** — candidate join paths found but **DRC-gate-rejected**
  by the frozen **D-249** (BPP 1.20 mm trunk, actual 0.20) and **D-269** (BAT_MAIN 0.300 mm clearance,
  actual 0.2803) rules; a bounded reducible corridor/ordering wall (FBV2-P2-003Z, §5), NOT `NO_PATH`.
- Rule floors ENFORCED: **0.200 mm** clearance, **0.25 mm** hole-to-hole, **0.300 mm** current-path
  routed clearance (D-269), **≥1.20 mm** BPP trunk width (D-249), **0.60 mm** BAT_MAIN minimum width.
  Six-layer stack, GND, netclasses, footprints, polarity, safety set — all frozen. Frozen
  `beta-full-reference-v1` untouched.

## 8. Open owner decisions
- **NONE. D-293 resolved the last owner decision (direction 2 authorized); D-294 (003T), D-295
  (003U), D-296 (003V) and D-297 (003W) each re-raised none.** Direction 2 is being executed under
  full CTO authority; the U18.8 wall is now closed in principle by the accepted D-297 In3-join lever
  (banked OFF-by-default in source), and the sole remaining Phase-A blocker — the saturated U19
  dead-cell field (`REC_BAT_LOW U19.7` + `N_BATDIV U19.6`) — is **bounded CTO-scope routing/capacity
  work, not an owner decision** (no floor relaxed, no frozen part moved, direction-2 not exhausted).
  Autonomy CONTINUES with **FBV2-P2-003X** (§5). Historical options (B accept-U18.8-open, D
  re-litigate-D-290) are retained only as context and are not active.
- **Nothing has been changed under any decision:** no part moved, no floor relaxed, no DRC absorbed
  into the authoritative board; the authoritative PCB is six layers / 0 tracks / 0 vias.

## 9. JLCPCB readiness
- **JLCPCB readiness ~77 %** (unchanged — 003W earned NO copper: it accepted a genuine +1 SECONDARY
  gain (U18.8 In3 join) and banked it OFF-by-default in source, but the full Phase-A run still FAILs
  on the U19 field, so no copper promoted; the authoritative board is still six layers / 0 tracks /
  0 vias). `/home/aqroot8/.aqroot-progress.env` unchanged (CTO owns readiness).
- **Repo progress 74 %** (governed value in PROGRESS.md).
- **What remains before fabrication:** close the U19 dead-cell field (simultaneous U19.7 + U19.6) and
  complete a full Phase-A PASS at the direction-2 placement (with the accepted D-297 U18.8 lever ON);
  promote the authoritative copper; then Phase-B production routing; full DRC/ERC/connectivity and
  regression closure on the authoritative board; RF/power/thermal/safety validation; BOM/footprint/
  polarity/DNP + assembly review; board-outline/stackup/fab-rule review; Gerber/drill/BOM/CPL
  generation and independent manufacturing-package review.

## 10. Active orchestration
- **Persistent CTO session:** `agent:main:aqroot-fbv2-cto` — sole owner of Claude engineering
  launches; receives every completion event.
- **Autopilot:** cron/systemd may only WAKE the persistent CTO; it must never launch Claude or become
  a task parent. No owner decision is open; the stop file is ABSENT and the persistent CTO continues
  one-Claude-at-a-time engineering.
- **Should an engineering process be active now?** **Yes.** FBV2-P2-003Z implements ONE bounded,
  env-gated (OFF-by-default) `LTC_GATE U18.10→Q3.4` join-corridor lever (re-site / re-order / detour the
  join clear of the `BAT_PROTECTED_P` 1.20 mm trunk region — D-249 — and open the 0.300 mm `BAT_MAIN`
  clearance — D-269), validate it against `router_regression.py` (authoritative byte-identical), then
  run the FULL authority gate (`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 <ltcgate-lever> bash
  w/run_003t_full.sh 003z_ltcgate w/cand_003t/t_a_r77e15n10_r79e15n10.json`, ~22 min, in a persistent
  terminal) and judge by the full-run connected-set diff vs `w/phaseA_003t_full_003y2_u19cap.json` and
  `w/phaseA_003t_full_003w_u18bpp_i3.json`. Promote copper only on a genuine full Phase-A PASS.

## 11. Recovery instructions (a fresh CTO/Claude reads these, in order)
1. `docs/full-beta-v2/CTO_DECISIONS.md` — authoritative rulings (latest: **D-299**, FBV2-P2-003Y the
   D-298 U19 CAPACITY lever's full-authority gate CONFIRMED a genuine +2, `AQROOT_U19CAP` ACCEPTED and
   COMMITTED OFF-by-default, copper NOT promoted while the new `LTC_GATE U18.10→Q3.4` wall FAILs;
   preceded by **D-298** (003X U19CAP implemented/screened) and **D-297** (003W U18.8 In3-join +1
   accepted)).
2. Newest audits — `audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md`,
   then `…-003x-d298-u19-capacity-east-lane-reservation-lever-screened-clean-handoff.md`,
   then `…-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md`,
   then `…-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md`,
   then `…-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md`,
   `…-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md`,
   `…-003s-d292-u18-r75-placement-microeco-exhausted.md`,
   `…-003r-d290-off-layer-vacate-refuted-owner-decision.md`, `…-003q-d289-…`, `…-003o-d288-…`.
3. `docs/full-beta-v2/CHANGELOG.md` and `docs/full-beta-v2/PROGRESS.md` (top entries).
4. Git HEAD + recent commits; the 003W instruments — the accepted D-297 lever in
   `hardware/beta-v2/checks/route_battery_block.py` (env `AQROOT_U18BPP_JOIN`, the `main()` join
   site), its **G13** contract in `checks/router_regression.py`, and the measured-record probe
   `checks/u18_i3_join_probe_003w.py`. The fixed bridge sites `bridge_early_003i.py` /
   `bridge_route_003c.py` (D-288).
5. Evidence + recipe + probes: the pinned natural-run
   `hardware/beta-v2/checks/phaseA_003o_b1_r75rot_cto.json`; the governing full recipe
   `w/run_003t_full.sh` + `w/cand_003t/t_a_r77e15n10_r79e15n10.json`; gitignored full-run results
   `w/phaseA_003t_full_e15n10cto.json` (D-294 baseline) and `w/phaseA_003t_full_003w_u18bpp_i3.json`
   (D-297); `place_003l.json`, `place_002z/` candidate set.
- **Never** trust this checkpoint over a conflicting `CTO_DECISIONS.md`; repair this file if they
  diverge.
