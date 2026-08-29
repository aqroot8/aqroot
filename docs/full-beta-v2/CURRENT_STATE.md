# AQROOT Full Beta v2 — CURRENT STATE (durable checkpoint)

> Checkpoint/index only. Authority precedence: **CTO_DECISIONS.md > accepted
> audits/engineering evidence > CURRENT_STATE.md > summaries/transcripts/session
> memory.** If this file conflicts with higher-authority evidence, repair this file.

## 1. Authoritative HEAD
- **FBV2-P2-003O / D-288 milestone commit:** the closeout commit that fixes the D-275
  south-bridge ENTRY-array two-layer tie in the bridge code (`bridge_route_003c.py`
  rotation-aware in-pad `scan_entry_sites` + `bridge_early_003i.py` entry B.Cu tie-stub),
  adds the non-vacuous D-288 `entry_tie_regression` to `screen_003n.py`, pins the
  natural-completion CTO full-run evidence `checks/phaseA_003o_b1_r75rot_cto.json`, and
  makes these governing-doc updates — the entry-tie fix is proven `via_dangling`-clean but
  the overall Phase-A run still FAILs on new downstream blockers (U18.8 escape / REF_POL
  R87 corridor / BAT_RAW divider width). Prior milestone: `9172470` (FBV2-P2-003N /
  D-287). This checkpoint is written in the same commit; a fresh session must confirm the
  live tip with `git rev-parse HEAD` and `git rev-parse origin/master`.
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
- **Current fabrication blocker (updated by D-288):** the D-275 south bridge is now
  proven electrically connected (the D-287 entry-array dangling is FIXED), and on the best
  survivor `b1_r75rot` the `BAT_PROTECTED_P` island closes R75.2 through
  C36/C25/C58/D9/U11/U14/TP15. The remaining Phase-A blockers, in true fabrication-blocker
  order, are: (1) **U18.8's `BAT_PROTECTED_P` escape** (`NO_VIA_SITE` on B at 0.65/0.35 mm
  + a BAT_MAIN routed-clearance reservation reject) — the one open trunk pad; (2) the
  terminal **`REF_POL R87.2 / R88.1→R87.2`** F-corridor NO_PATH at 0.150 mm; (3) the
  **`BAT_RAW R89.1/R86.2` divider-tap width** vs the BAT_MAIN 0.60 mm rule. All are bounded
  CTO-scope technical work.

## 4. Last accepted milestone
- **Task:** FBV2-P2-003O · **Decision:** **D-288** · **Result:** THE D-275 SOUTH-BRIDGE
  ENTRY-ARRAY TWO-LAYER TIE IS FIXED (`via_dangling`-CLEAN, PROVEN BY A NON-VACUOUS
  REGRESSION + A NATURAL-COMPLETION CTO FULL RUN) — BUT THE OVERALL PHASE-A RUN STILL FAILs
  ON NEW DOWNSTREAM BLOCKERS. BRIDGE-CODE FIX + REGRESSION ACCEPTED/COMMITTED, NO
  PROGRESS/READINESS CHANGE, CTO ENGINEERING FAIL, NO OWNER DECISION, NO PROMOTION.
- A successful bridge-implementation fix is distinct from an overall Phase-A pass. **The
  fix (both parts in the bridge code):** (1) `bridge_route_003c.scan_entry_sites` windowed
  on R75.2's UNROTATED `hx/hy` and sorted "south-first", so for the −90°-rotated R75 pad it
  picked the NORTHERNMOST sites ~0.5–1.15 mm north of the real B.Cu pad copper (the D-287
  dangle); new `_in_pad()` transforms each candidate into the pad's OWN rotated frame and
  requires the centre inside the pad rect inset by `IN_PAD_MARGIN=0.20 mm`, scanning the
  rotation-aware AABB and sorting CENTRE-OUT; (2) `stage_bridge`/`bridge_early_003i.apply_early`
  lay an explicit B.Cu tie-stub from each entry via to R75.2's pad centre (mirror of the
  exit `_lay_landing` stub) — a two-layer tie. **The D-288 regression is NON-VACUOUS
  (`screen_003n.py --bridge --validate`, exit 0):** NEGATIVE control (the D-287 off-pad
  F.Cu-only array) MUST dangle — measured `via_dangling +4`; POSITIVE control (the real
  fixed bridge) is CONNECTED, `via_dangling == 0`, entry 4, exit 4, ywest 82.4, traverse
  1.30 mm; NO-ABSORPTION — zero new hard-class DRC vs the identical no-bridge board. **The
  natural CTO full run (`b1_r75rot`, `DRIVER_EXIT=0`, secs 1776.5, evidence
  `checks/phaseA_003o_b1_r75rot_cto.json`):** PHASE A FAIL; connections 67, skipped 99,
  ratsnest 781→708 (−73). The early south bridge now passes BOTH geometrically AND
  electrically — `land C36.1`, traverse 70.925 mm @ 1.30 mm, entry 4 @ y=67.95 GENUINELY
  INSIDE the rotated R75.2 pad, exit 4, disjoint `ywest 82.40` — with NO `via_dangling`
  cascade anywhere (the D-287 20-gate poisoning is GONE); the `BAT_PROTECTED_P` island
  CLOSES R75.2 through C36/C25/C58/D9/U11/U14/TP15. **The NEW blockers (attributed, NOT
  absorbed):** (1) `U18.8` OPEN — reservation `GATE_REJECTED` on `clearance +1` (BAT_MAIN
  routed clearance) then main-pass `NO_VIA_SITE` (no 0.65/0.35 mm via site on B); (2)
  terminal `REF_POL R87.2→(node)` NO_PATH at 0.150 mm (also `R88.1→R87.2`); (3) `BAT_RAW
  R89.1→(node)` NO_PATH at 0.600 mm and `R86.2` `GATE_REJECTED` on `track_width +4` (four
  0.20 mm BAT_RAW divider taps vs the BAT_MAIN 0.60 mm rule). Final DRC (re-verified with
  `kicad-cli`): `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1,
  track_width:1, unconnected_items:499}`; the single `track_width` item is a
  `BAT_PROTECTED_P` B.Cu track 2.4749 mm @ (65.5,76.05) at 0.2000 mm vs rule
  `BAT_PROTECTED_P high-current trunk width - D-249` (min 1.2000 mm) — a thin sense/Kelvin
  sub-branch of the trunk net, benign, SURFACED not absorbed, NOT a fab blocker. No copper,
  no placement promoted.
- **Prior milestone — FBV2-P2-003N / D-287:** DIRECTION-1 CANDIDATE SPACE EXHAUSTED
  (27/27) + all three hard-gate survivors refuted at the (now-fixed) entry-array
  dangling-via defect; the D-286 screen rejected 24 of 27 candidates at bare placement,
  only `b1_r75rot`/`b1_r75rotN`/`b1_q3rot` survived, and the bridge-connectivity probe
  found `via_dangling 4/4/2` on all three (the missing entry B.Cu tie-stub) — a
  bridge-implementation defect independent of placement, resolved by D-288. No promotion.
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
- **FBV2-P2-003P (CTO scope), in true fabrication-blocker order** (with the bridge entry
  tie now proven, all **without relaxing any floor/rule or moving a frozen part**):
  1. **U18.8's `BAT_PROTECTED_P` escape (the last open trunk pad).** It reports
     `NO_VIA_SITE` at 0.65 mm and 0.35 mm on B and an earlier reservation `GATE_REJECTED`
     on a `BAT_MAIN routed clearance` item. Find a legal B-layer via site / escape + a
     reservation for U18.8 that keeps the 0.200 mm clearance floor and the ≥1.20 mm trunk
     width; this closes `BAT_PROTECTED_P` across all required pads.
  2. **Terminal REF_POL R87.2 / R88.1→R87.2 corridor.** NO_PATH at 0.150 mm — investigate
     the F.Cu corridor to the REF_POL node; determine whether it is congestion/ordering or
     a genuine geometric wall.
  3. **BAT_RAW R89.1 / R86.2 divider-tap width.** The four 0.20 mm divider taps trip the
     BAT_MAIN 0.60 mm rule (`track_width +4`, gate-rejected). Attribute correctly — decide
     whether they are legitimately bounded microamp exceptions (like the D-269
     `BAT_RAW_DIVIDER_TAP_*` corridor already in the run's `stubs` list) or genuine width
     failures — **without relaxing BAT_MAIN**.
- **Why next:** D-288 fixed the D-275 entry-array two-layer tie (the bridge is now
  electrically connected end-to-end) and the natural CTO full run shows the
  `BAT_PROTECTED_P` island closing seven pads; the remaining Phase-A failures are the
  above bounded, downstream blockers the entry dangling had shadowed. A genuine OWNER
  DECISION (direction-2 LTC4368 refloorplan / corridor widening) arises only if one of
  these proves un-fixable without relaxing a floor/rule or moving a frozen part.

## 6. Authoritative PCB state
- **Routing/promotion:** NOT promoted. Authoritative board = **six copper layers,
  0 signal tracks, 0 signal vias**; placement untouched (C36 home 63.75,73.75,0°; U18
  home 3.0,72.4,90°). All 003O bridge/full-run copper lived only in gitignored scratch
  (`checks/w/`) and override files (`place_003l.json`, `place_002z/b1_*.json`); the
  natural-run result `checks/phaseA_003o_b1_r75rot_cto.json` is committed as evidence of
  record (its scratch log `w/log_003o_b1_r75rot_cto.txt` stays gitignored).
- `phaseA_journal.json` restored to its committed state (driver never authoritatively
  invoked; scratch churn discarded).
- PCB routing **0 %**; overall repo progress **74 %**.

## 7. Locked invariants (reference the D-xxx rulings, not the history)
- **D-275** forced-south `BAT_PROTECTED_P` bridge geometry (lane + landing proven).
  **D-288 update (resolves the D-287 caveat):** the entry-array two-layer tie is FIXED —
  the entry vias now sit inside R75.2's rotated B.Cu pad (rotation-aware in-pad scan) AND
  carry an explicit B.Cu tie-stub symmetric to the exit array, so the bridge is
  `via_dangling`-clean both in isolation and in a natural-completion full run. The bridge
  is now an ELECTRICAL pass, not merely geometric.
- **D-277..D-280** U19/deadcell escape + C61 landing-guard gains.
- **D-281/282/283** western-corridor route-scope fixes exhausted; **D-284 (OWNER)**
  approved landing-opening direction 1 (bounded C36/C25/U11/BQ25185_SYS spread), NOT
  direction-2 corridor widening / broad refloorplan; **D-285** `place_003l` opens the
  C36.1 landing (clean).
- **D-286** gate baseline measured on the actual complete pre-copper placement;
  candidate placements must be screened with real full-placement DRC (no analytic
  "mech-clean" substitute); a genuine placement short must be surfaced, never absorbed.
- **D-287** the bounded direction-1 placement space is EXHAUSTED (27/27); the three
  hard-gate survivors (`b1_r75rot`, `b1_r75rotN`, `b1_q3rot`) failed bridge integration on
  a placement-independent entry-array dangling-via defect (resolved by D-288); a
  `via_dangling` item is a genuine electrical fault and MUST fail (geometric bridge ≠
  electrical connectivity).
- **D-288** the D-275 south-bridge entry array must sit inside R75.2's rotated B.Cu pad
  (rotation-aware in-pad `scan_entry_sites`) AND carry a symmetric B.Cu tie-stub, so it is
  two-layer / `via_dangling`-clean. The entry-tie fix is proven; the remaining
  `BAT_PROTECTED_P`/Phase-A blockers (U18.8 escape, REF_POL R87 corridor, BAT_RAW divider
  width) are bounded CTO-scope work (003P), NOT an owner decision. The **0.60 mm BAT_MAIN
  minimum width** rule is a hard floor (BAT_RAW divider taps are gate-rejected against it,
  not absorbed).
- Rule floors ENFORCED: **0.200 mm** clearance, **0.25 mm** hole-to-hole,
  **≥1.20 mm** BPP trunk width (D-249), **0.60 mm** BAT_MAIN minimum width. Six-layer
  stack, GND, netclasses, footprints, polarity, safety set — all frozen. Optional
  `BAT_SENSE TP20.1` (TEST) is separate and not a gate. Frozen `beta-full-reference-v1`
  untouched.

## 8. Open owner decisions
- **NONE.** (Synchronized with `/home/aqroot8/.aqroot-autopilot-stop`, which is ABSENT.)
- 003O (D-288) fixed the entry-tie defect (the bridge is now `via_dangling`-clean) and the
  natural full run leaves only **bounded, CTO-scope downstream blockers** — U18.8's
  `BAT_PROTECTED_P` escape, the REF_POL R87 F-corridor, and the BAT_RAW divider-tap width.
  None is a placement wall or requires relaxing a floor/rule or moving a frozen part, so no
  owner decision is raised. A genuine OWNER DECISION arises only if one of the 003P
  blockers proves un-fixable within those constraints, leaving a direction-2 LTC4368
  refloorplan / corridor widening as the sole remaining option.

## 9. JLCPCB readiness
- **JLCPCB readiness ~77 %** (unchanged — a bridge-code fix proven on scratch, with the
  authoritative board still six layers / 0 tracks / 0 vias and the full Phase-A run still
  FAILing, does not move the board closer to fabrication; only scratch evidence + tooling
  improved).
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
- **Should an engineering process be active now?** Yes — FBV2-P2-003P (close U18.8's
  `BAT_PROTECTED_P` escape, then the REF_POL R87 corridor and BAT_RAW divider-width
  attribution) is the known next task; autonomy continues without an owner decision.

## 11. Recovery instructions (a fresh CTO/Claude reads these, in order)
1. `docs/full-beta-v2/CTO_DECISIONS.md` — authoritative rulings (latest: **D-288**).
2. Newest audits — `audits/2026-08-29-p2-003o-d288-entry-tie-fix-and-full-run.md`,
   then `…-003n-d287-…`, `…-003m-d286-…`, `…-003l-d285-…`, `…-003k-d283-…`.
3. `docs/full-beta-v2/CHANGELOG.md` and `docs/full-beta-v2/PROGRESS.md` (top entries).
4. Git HEAD + recent commits; the instrument `hardware/beta-v2/checks/screen_003n.py`
   (`--validate` screen regression, `--bridge [--validate]` bridge probe + the D-288
   `entry_tie_regression`); the fixed bridge sites `bridge_early_003i.py`
   (`apply_early`/`_lay_landing`) and `bridge_route_003c.py` (`scan_entry_sites`/`_in_pad`).
5. Evidence + recipe + probes: the pinned natural-run
   `hardware/beta-v2/checks/phaseA_003o_b1_r75rot_cto.json` (+ gitignored scratch log
   `w/log_003o_b1_r75rot_cto.txt`), `w/screen_003n/results.json` + `bridge_probe.json`,
   `bridge_probe_003c/d/i/j/k/l.py`, `u19_escape_probe_003e/f/g/h.py`,
   `place_003l.json`, `place_002z/` candidate set (`b1_*`, `c3_*`, `cand_*`, `c2_*`).
- **Never** trust this checkpoint over a conflicting `CTO_DECISIONS.md`; repair this file
  if they diverge.
