# AQROOT Full Beta v2 — CURRENT STATE (durable checkpoint)

> Checkpoint/index only. Authority precedence: **CTO_DECISIONS.md > accepted
> audits/engineering evidence > CURRENT_STATE.md > summaries/transcripts/session
> memory.** If this file conflicts with higher-authority evidence, repair this file.

## 1. Authoritative HEAD
- **FBV2-P2-003M / D-286 milestone commit:** `f80f126477476c916f1a177fd21c06c740a5909c`
  (branch `master`) — the baseline-order harness fix + c3_00 measured FAIL. This
  checkpoint file is synced by the docs commit immediately following it; a fresh session
  must confirm the live tip with `git rev-parse HEAD` and `git rev-parse origin/master`.
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
- **Task:** FBV2-P2-003M · **Decision:** **D-286** · **Result:** HARNESS CORRECTION
  PASS + `c3_00` RECIPE MEASURED FAIL (no authoritative promotion).
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
  (connections 64, ratsnest 713 −68). The D-275 south bridge itself PASSED at full width
  (`land C36.1`, 72.994 mm @ 1.50 mm, entry 4/exit 4, disjoint). `place_003l` (D-285) is
  clean and preserved. No DRC absorbed; the placement short IS the FAIL reason.

## 5. Next task
- **FBV2-P2-003N (CTO scope):** re-screen the LTC-block placement candidates
  (`c3_01/02/03`, `cand_00..11`, the c2 family) with the corrected **D-286 post-placement
  baseline DRC** — reject any candidate whose bare placement shorts different nets or
  boxes an LTC sense pin — then integrate the first genuinely short-free, routable
  candidate with `place_003l` + the proven south bridge on a parent-supervised full run.
- **Why next:** route-scope western-corridor fixes are exhausted (D-281/282/283); the
  bounded landing ECO (`place_003l`, D-285) is proven but only opens the C36.1 landing;
  the designated LTC-block placement `c3_00` is now invalid, and the corrected harness is
  exactly the instrument needed to screen alternates on real full-placement DRC.

## 6. Authoritative PCB state
- **Routing/promotion:** NOT promoted. Authoritative board = **six copper layers,
  0 signal tracks, 0 signal vias**; placement untouched (C36 home 63.75,73.75,0°; U18
  home 3.0,72.4,90°). All 003M copper/placement lived only in gitignored scratch
  (`checks/w/FIX003M`) and override files (`place_003l.json`, `place_002z/c3_00.json`).
- `phaseA_journal.json` restored to its committed state after the FAIL run.
- PCB routing **0 %**; overall repo progress **74 %**.

## 7. Locked invariants (reference the D-xxx rulings, not the history)
- **D-275** forced-south `BAT_PROTECTED_P` bridge geometry (proven in isolation; now
  also proven to lay end-to-end at 1.50 mm on the placement with a legal C36.1 landing).
- **D-277..D-280** U19/deadcell escape + C61 landing-guard gains.
- **D-281/282/283** western-corridor route-scope fixes exhausted; **D-284 (OWNER)**
  approved landing-opening direction 1 (bounded C36/C25/U11/BQ25185_SYS spread), NOT
  direction-2 corridor widening / broad refloorplan; **D-285** `place_003l` opens the
  C36.1 landing (clean).
- **D-286** gate baseline measured on the actual complete pre-copper placement;
  candidate placements must be screened with real full-placement DRC (no analytic
  "mech-clean" substitute); a genuine placement short must be surfaced, never absorbed.
- Rule floors ENFORCED: **0.200 mm** clearance, **0.25 mm** hole-to-hole,
  **≥1.20 mm** BPP trunk width (D-249). Six-layer stack, GND, netclasses, footprints,
  polarity, safety set — all frozen. Optional `BAT_SENSE TP20.1` (TEST) is separate and
  not a gate. Frozen `beta-full-reference-v1` untouched.

## 8. Open owner decisions
- **NONE.** (Synchronized with `/home/aqroot8/.aqroot-autopilot-stop`, which is ABSENT.)
- A genuine OWNER DECISION would arise only if 003N proves the entire bounded
  direction-1 candidate space yields no short-free, routable LTC-block placement,
  leaving a direction-2 LTC4368 refloorplan / corridor widening as the sole remaining
  option.

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
- **Should an engineering process be active now?** Yes — FBV2-P2-003N is the known next
  task; autonomy continues without an owner decision.

## 11. Recovery instructions (a fresh CTO/Claude reads these, in order)
1. `docs/full-beta-v2/CTO_DECISIONS.md` — authoritative rulings (latest: **D-286**).
2. Newest audits — `audits/2026-08-29-p2-003m-d286-baseline-order-and-c3_00-placement-shorts.md`,
   then `…-003l-d285-…`, `…-003k-d283-…`, `…-003j-d282-…`, `…-003i-d281-…`.
3. `docs/full-beta-v2/CHANGELOG.md` and `docs/full-beta-v2/PROGRESS.md` (top entries).
4. Git HEAD + recent commits; `hardware/beta-v2/checks/route_battery_block.py`
   (baseline order, D-286) and `router_regression.py` (G12).
5. Recipe + probes: `hardware/beta-v2/checks/w/run_003m.sh`,
   `bridge_probe_003c/d/i/j/k/l.py`, `u19_escape_probe_003e/f/g/h.py`,
   `place_003l.json`, `place_002z/` candidate set + `c3_index.json`.
- **Never** trust this checkpoint over a conflicting `CTO_DECISIONS.md`; repair this file
  if they diverge.
