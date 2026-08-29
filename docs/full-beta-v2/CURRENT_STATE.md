# AQROOT Full Beta v2 — CURRENT STATE (durable checkpoint)

> Checkpoint/index only. Authority precedence: **CTO_DECISIONS.md > accepted
> audits/engineering evidence > CURRENT_STATE.md > summaries/transcripts/session
> memory.** If this file conflicts with higher-authority evidence, repair this file.

## 1. Authoritative HEAD
- **FBV2-P2-003N / D-287 milestone commit:** the closeout commit that adds
  `checks/screen_003n.py` (the D-286 candidate screen + the bridge-connectivity probe/
  regression) and these governing-doc updates — the full direction-1 screen exhausted +
  all three survivors refuted at the entry-array dangling defect. Prior milestone:
  `f80f126` (FBV2-P2-003M / D-286). This checkpoint is written in the same commit; a
  fresh session must confirm the live tip with `git rev-parse HEAD` and
  `git rev-parse origin/master`.
- **HEAD == origin/master:** yes (committed and pushed at milestone closeout).

## 2. Mission
- Deliver Full Beta v2 to **READY FOR JLCPCB** — a fabricable, assembly-ready
  authoritative board with all governing routing / DRC / ERC / connectivity / safety
  gates passing and the final JLCPCB deliverables generated and reviewed.
- Terminal condition: **READY FOR JLCPCB**.

## 3. Current phase / gate
- **Phase P2 — battery/power-block Phase-A routing**, specifically closing
  **`BAT_PROTECTED_P`** (the last-mile high-current protection net) via the proven
  D-275 forced-south bridge, integrated into a full Phase-A run.
- **Current fabrication blocker:** no viable LTC4368-block candidate placement that
  (a) is short-free at the bare-placement level and (b) lets the LTC sense pins escape,
  while relieving the western BPP trunk. The designated candidate `c3_00` is now
  measured invalid (D-286).

## 4. Last accepted milestone
- **Task:** FBV2-P2-003N · **Decision:** **D-287** · **Result:** DIRECTION-1 CANDIDATE
  SPACE EXHAUSTED (27/27) + ALL THREE HARD-GATE SURVIVORS REFUTED AT A PLACEMENT-
  INDEPENDENT BRIDGE ENTRY-ARRAY DANGLING-VIA DEFECT — CTO ENGINEERING FAIL, NO OWNER
  DECISION, NO PROMOTION.
- The D-286 screen (`checks/screen_003n.py`, real full-placement DRC + real `qb.escape`)
  rejected 24 of 27 candidates at bare placement; only `b1_r75rot`, `b1_r75rotN`,
  `b1_q3rot` pass every zero-copper hard gate and all required U18 escapes. A cheap
  CTO-authorized **bridge-connectivity probe** (`screen_003n.py --bridge`, validated
  against the b1_r75rot full-run control) then refuted **all three**: the D-275 south
  bridge lays a full-width disjoint lane to C36.1 but its **ENTRY array on R75.2** is
  bussed on F.Cu with **no symmetric B.Cu tie-stub**, so the entry vias land ~0.5–1.15 mm
  north of R75.2's B.Cu pad and dangle on one layer — `via_dangling 4 / 4 / 2` (a genuine
  electrical fault, never absorbed). The EXIT array does NOT dangle (it lays an explicit
  B.Cu tie-stub). This is a **bridge-implementation defect independent of placement**, not
  a placement wall — the charter's "narrower CTO technical lever" — so **direction-2 is
  NOT yet the sole option and this is NOT an owner decision**. Earlier "the D-275 bridge
  PASSED" claims (003K/L/M) were GEOMETRIC passes never electrically gated. No copper, no
  placement promoted.
- **Prior milestone — FBV2-P2-003M / D-286:** HARNESS CORRECTION PASS + `c3_00` RECIPE
  MEASURED FAIL (no authoritative promotion).
- The gate DRC/ratsnest baseline in `route_battery_block.py` was measured BEFORE the
  `AQROOT_PLACE_JSON` candidate placement (latent since 002L), so a candidate's own
  placement DRC poisoned every routing gate (first 003M attempt: `GATE_REJECTED`
  cascade, `DRIVER_EXIT=143`). The baseline is now measured on the ACTUAL complete
  pre-copper placement (after ECO + `AQROOT_ECO_EXTRA` + `AQROOT_PLACE_JSON` +
  connectivity rebuild + zone fill + save + `DRU.write` + fingerprint assert, before any
  QBoard copper). Regression **G12** pins the corrected order and proves a post-baseline
  copper violation is still surfaced. With the fix, the definitive full run
  (`DRIVER_EXIT=0`) reveals what the old ordering was hiding: `c3_00` drops U18 (LTC4368)
  onto R83/R80, giving **three genuine different-net pad shorts + two sub-0.200 mm
  clearances with zero copper** and un-escapable LTC sense pins → PHASE A FAIL
  (connections 64, ratsnest 713 −68). The D-275 south bridge laid a full-width disjoint
  lane (`land C36.1`, 72.994 mm @ 1.50 mm, entry 4/exit 4) — a GEOMETRIC pass that D-287
  later showed is NOT electrical connectivity (the entry array dangles; it was masked here
  by the c3_00 placement short). `place_003l` (D-285) is clean and preserved. No DRC
  absorbed; the placement short IS the FAIL reason.

## 5. Next task
- **FBV2-P2-003O (CTO scope):** fix the D-275 south-bridge **ENTRY-array two-layer tie**
  so the entry vias are electrically connected (zero `via_dangling`), symmetric to the
  proven exit array. In `bridge_early_003i.apply_early` / `bridge_route_003c`: after the
  entry vias + F.Cu bus, add an explicit **B.Cu tie-stub from each entry via to R75.2's
  pad centre** (mirroring `_lay_landing`'s exit stub) and/or constrain `scan_entry_sites`
  to sites truly inside R75.2's B.Cu pad copper — **no rule/floor/topology/footprint/net
  change, no absorption**. Verify with `checks/screen_003n.py --bridge` that the fixed
  bridge reports `via_dangling == 0`, entry ≥ 3, exit ≥ 3, disjoint `ywest > 75`, traverse
  ≥ 1.20 mm on the best survivor **`b1_r75rot`** (disjoint 82.40, cleanest). Only when the
  probe is GREEN, take `b1_r75rot` into a parent-supervised full Phase-A run and close
  `BAT_PROTECTED_P`.
- **Why next:** the full bounded direction-1 placement space is EXHAUSTED (D-287, 27/27),
  but the three hard-gate survivors fail on a **bridge-connectivity implementation defect
  independent of placement** (the missing entry-array B.Cu tie-stub) — a narrower CTO
  lever that moves no LTC-block footprint. Direction-2 (broad LTC4368 refloorplan /
  corridor widening, OWNER/mechanical) becomes a genuine OWNER DECISION **only if** the
  entry tie proves un-fixable without relaxing a floor or moving a frozen part.

## 6. Authoritative PCB state
- **Routing/promotion:** NOT promoted. Authoritative board = **six copper layers,
  0 signal tracks, 0 signal vias**; placement untouched (C36 home 63.75,73.75,0°; U18
  home 3.0,72.4,90°). All 003N screen/probe copper lived only in gitignored scratch
  (`checks/w/screen_003n/`) and override files (`place_003l.json`, `place_002z/b1_*.json`).
- `phaseA_journal.json` restored to its committed state (driver never authoritatively
  invoked; scratch churn discarded).
- PCB routing **0 %**; overall repo progress **74 %**.

## 7. Locked invariants (reference the D-xxx rulings, not the history)
- **D-275** forced-south `BAT_PROTECTED_P` bridge geometry (lane + landing proven).
  **D-287 caveat:** the bridge's laid-and-disjoint state is a GEOMETRIC pass, NOT
  electrical connectivity — its ENTRY array (R75.2 POFV) currently dangles on one layer
  for lack of a symmetric B.Cu tie-stub; 003O must make the entry tie `via_dangling`-clean
  before any full-run promotion.
- **D-277..D-280** U19/deadcell escape + C61 landing-guard gains.
- **D-281/282/283** western-corridor route-scope fixes exhausted; **D-284 (OWNER)**
  approved landing-opening direction 1 (bounded C36/C25/U11/BQ25185_SYS spread), NOT
  direction-2 corridor widening / broad refloorplan; **D-285** `place_003l` opens the
  C36.1 landing (clean).
- **D-286** gate baseline measured on the actual complete pre-copper placement;
  candidate placements must be screened with real full-placement DRC (no analytic
  "mech-clean" substitute); a genuine placement short must be surfaced, never absorbed.
- **D-287** the bounded direction-1 placement space is EXHAUSTED (27/27); the three
  hard-gate survivors (`b1_r75rot`, `b1_r75rotN`, `b1_q3rot`) fail bridge integration on a
  placement-independent entry-array dangling-via defect; a `via_dangling` item is a
  genuine electrical fault and MUST fail (geometric bridge ≠ electrical connectivity);
  the next lever is the CTO-scope entry-tie fix (003O), NOT an owner decision.
- Rule floors ENFORCED: **0.200 mm** clearance, **0.25 mm** hole-to-hole,
  **≥1.20 mm** BPP trunk width (D-249). Six-layer stack, GND, netclasses, footprints,
  polarity, safety set — all frozen. Optional `BAT_SENSE TP20.1` (TEST) is separate and
  not a gate. Frozen `beta-full-reference-v1` untouched.

## 8. Open owner decisions
- **NONE.** (Synchronized with `/home/aqroot8/.aqroot-autopilot-stop`, which is ABSENT.)
- 003N (D-287) exhausted the direction-1 placement space but found the survivors fail on
  a **CTO-fixable bridge-connectivity defect independent of placement**, NOT a placement
  wall — so direction-2 is NOT yet the sole option and no owner decision is raised. A
  genuine OWNER DECISION arises only if the 003O entry-tie fix proves the bridge cannot be
  made `via_dangling`-clean without relaxing a rule floor or moving a frozen part, leaving
  a direction-2 LTC4368 refloorplan / corridor widening as the sole remaining option.

## 9. JLCPCB readiness
- **JLCPCB readiness ~77 %** (unchanged — a harness-correctness fix + a measured
  candidate rejection do not move the authoritative board closer to fabrication).
- **Repo progress 74 %** (governed value in PROGRESS.md).
- **What remains before fabrication:** close `BAT_PROTECTED_P` on a valid LTC-block
  placement and complete Phase-A/Phase-B production routing; full DRC/ERC/connectivity
  and regression closure on the authoritative board; RF/power/thermal/safety validation;
  BOM/footprint/polarity/DNP + assembly review; board-outline/stackup/fab-rule review;
  Gerber/drill/BOM/CPL generation and independent manufacturing-package review.

## 10. Active orchestration
- **Persistent CTO session:** `agent:main:aqroot-fbv2-cto` — sole owner of Claude
  engineering launches; receives every completion event.
- **Autopilot:** cron/systemd may only WAKE the persistent CTO; it must never launch
  Claude or become a task parent. No autopilot stop file is set (correct — this is an
  ordinary engineering FAIL with a known next task, not a stop condition).
- **Should an engineering process be active now?** Yes — FBV2-P2-003O (the entry-tie fix)
  is the known next task; autonomy continues without an owner decision.

## 11. Recovery instructions (a fresh CTO/Claude reads these, in order)
1. `docs/full-beta-v2/CTO_DECISIONS.md` — authoritative rulings (latest: **D-287**).
2. Newest audits — `audits/2026-08-29-p2-003n-d287-bridge-entry-array-dangling.md`,
   then `…-003m-d286-…`, `…-003l-d285-…`, `…-003k-d283-…`, `…-003j-d282-…`.
3. `docs/full-beta-v2/CHANGELOG.md` and `docs/full-beta-v2/PROGRESS.md` (top entries).
4. Git HEAD + recent commits; the D-287 instrument `hardware/beta-v2/checks/screen_003n.py`
   (`--validate` screen regression, `--bridge [--validate]` bridge-connectivity probe);
   the defect sites `bridge_early_003i.py` (`apply_early`/`_lay_landing`) and
   `bridge_route_003c.py` (`scan_entry_sites`).
5. Recipe + probes: `hardware/beta-v2/checks/w/log_003n_b1_r75rot.txt`,
   `w/screen_003n/results.json` + `bridge_probe.json`,
   `bridge_probe_003c/d/i/j/k/l.py`, `u19_escape_probe_003e/f/g/h.py`,
   `place_003l.json`, `place_002z/` candidate set (`b1_*`, `c3_*`, `cand_*`, `c2_*`).
- **Never** trust this checkpoint over a conflicting `CTO_DECISIONS.md`; repair this file
  if they diverge.
