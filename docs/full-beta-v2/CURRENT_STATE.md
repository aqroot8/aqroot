# AQROOT Full Beta v2 — CURRENT STATE (durable checkpoint)

> Checkpoint/index only. Authority precedence: **CTO_DECISIONS.md > accepted
> audits/engineering evidence > CURRENT_STATE.md > summaries/transcripts/session
> memory.** If this file conflicts with higher-authority evidence, repair this file.

## 1. Authoritative HEAD
- **FBV2-P2-003R / D-290 milestone commit (this checkpoint):** a governed **evidence /
  NO-PROGRESS** commit that **RAISES ONE OWNER DECISION.** 003R implemented and screened the
  LAST bounded routing-only U18 co-closure lever D-289 named — the **off-layer vacate of
  U18.7** (`AQROOT_VACATE=U18_7` onto In2/In3 + `AQROOT_U18_FIRST=1` reserving U18.8 alone) —
  and it is **REFUTED** (−1 regression, conn 34 vs baseline 35). The refutation is **geometric
  and exact:** the U18.7/U18.8/U18.9 3-into-one-corner contention is an irreducible
  **placement-geometry mutual-exclusion** at the 0.5 mm pad pitch vs the 0.300 mm current-path
  clearance floor (D-269) — the vacate moves U18.7's escape transition from a 0.15 mm B.Cu
  neck (0.250 mm from U18.8's reserve via) to a 0.35 mm through via (0.150 mm from it), CLOSER
  not farther, so In2 AND In3 both revert; U18.9 is an independent casualty (dominant blocker
  U18.10 ×25). No via-size/layer/direction/ordering lever rescues it without a DRU change or a
  frozen-part move. **No source, no copper, no placement, no rule change** (the D-290 WIP is
  RETIRED). This exhausts the routing-only space the policy named, so a bounded **LTC4368/R75
  placement micro-ECO became a genuine OWNER DECISION; **D-291 records Alpha's approval of
  the bounded CTO-recommended option and autonomy has resumed.** Prior milestone: `9bd7aac`
  (FBV2-P2-003Q / D-289). This checkpoint is written in
  the same commit; a fresh session must confirm the live tip with `git rev-parse HEAD` and
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
- **Current fabrication blocker (updated by D-290):** the D-275 south bridge is proven
  electrically connected (D-288) and the `BAT_PROTECTED_P` island closes R75.2 through
  C36/C25/C58/D9/U11/U14/TP15. D-290 exhausted the routing-only space for the residual
  **U18.8 escape**: the off-layer vacate of U18.7 (the last lever D-289 named) is REFUTED
  because the conflict is at the **pad-exit zone**, not the corridor — U18's west-edge pins
  are on B.Cu at a fixed 0.5 mm pitch with U18.8 physically BETWEEN U18.7's south escape and
  U18.9's north escape, so every escape (neck, inner via, via-in-pad) must exit within 0.5 mm
  of the adjacent pin's committed copper, and 0.5 mm pitch cannot host three escape
  transitions under the 0.300 mm current-path floor (D-269). The vacate makes it WORSE
  (0.35 mm via at 0.150 mm vs the 0.15 mm neck at 0.250 mm), and U18.9 is lost independently
  (blocker U18.10 ×25). **D-291 authorizes the bounded LTC4368/R75 placement micro-ECO**
  to open a second U18.8 escape. The terminal **REF_POL R87.2→(node) NO_PATH** is
  (per D-289) **F.Cu routing capacity** (N_POL 6.36 mm F.Cu saturates its corridor), narrowest
  lever = D-279-class N_POL F.Cu inner offload — but it is downstream of the U18 placement
  micro-ECO. Remaining Phase-A blockers in fabrication-blocker order: (1) **U18.8's escape —
  owner-approved bounded placement work**; (2) the REF_POL R87 F-corridor capacity
  (CTO-scope, blocked behind (1)); (3) the BAT_RAW R89.1/R86.2 divider taps (true NO_PATH /
  other-branch width, a capacity symptom not a width lever).

## 4. Last accepted milestone
- **Task:** FBV2-P2-003R · **Decision:** **D-290** · **Result:** THE LAST BOUNDED
  ROUTING-ONLY U18 CO-CLOSURE LEVER (OFF-LAYER VACATE OF U18.7) IS REFUTED ON CHEAP
  NON-VACUOUS EVIDENCE (−1 regression, conn 34 vs baseline 35), THE REFUTATION IS GEOMETRIC
  AND EXACT (the U18.7/U18.8/U18.9 3-into-one-corner contention is an irreducible
  placement-geometry mutual-exclusion at the 0.5 mm pad pitch vs the 0.300 mm current-path
  clearance floor — the vacate moves U18.7's escape transition from a 0.15 mm B.Cu neck
  0.250 mm from U18.8's reserve via to a 0.35 mm through via 0.150 mm from it, CLOSER not
  farther, so In2 and In3 both revert; U18.9 is an independent casualty, dominant blocker
  U18.10 ×25), SO NO CONCRETE LEGAL ROUTING-ONLY SITE REMAINS AND A BOUNDED LTC4368/R75
  PLACEMENT MICRO-ECO IS NOW A GENUINE OWNER DECISION; the D-290 WIP is retired, no
  source/copper/placement/rule change, D-275 and D-277..D-289 preserved. Evidence of record:
  `checks/phaseA_003r_baseline.json`, `checks/phaseA_003r_lever.json`; scratch gitignored
  (`w/log_003r_baseline.txt`, `w/log_003r_lever.txt`, `w/run_003r_*.sh`, `w/Q003R_*`). Full
  analysis:
  [`audits/2026-08-29-p2-003r-d290-off-layer-vacate-refuted-owner-decision.md`](audits/2026-08-29-p2-003r-d290-off-layer-vacate-refuted-owner-decision.md).
- **Prior milestone — FBV2-P2-003Q / D-289:** THE REJECTED 003P WIP IS
  RETIRED WITH NO PROGRESS (byte-aggregate-equivalent to 003O, a lateral U18.7↔U18.8 swap),
  the U18.7/U18.8 co-closure **reservation-ordering lever is REFUTED** (U18.8-first = conn 34
  vs baseline 35; U18.8 closes but U18.7+U18.9 open — a 3-into-one-corner placement-geometry
  mutual-exclusion where U18.8→R75.2 escapes NORTH into U18.7's only B lane with no
  alternative B via-site), and the terminal REF_POL R87.2 wall is characterized on the actual
  congested board as **F.Cu routing capacity** (N_POL 6.36 mm F.Cu saturates the R87.2→node
  corridor) with a named narrowest lawful lever (D-279-class N_POL F.Cu inner offload, no
  closure claimed). No source/copper/placement/rule change; committed D-289 supersedes the
  VOID informal 003P labels D-289/290/291; a CTO ENGINEERING FAIL, NO OWNER DECISION, NO
  PROMOTION. Evidence: gitignored `checks/w/log_003q_baseline.txt`, `log_003q_u18first.txt`,
  `refpol_wall_003q.py`. Full analysis:
  [`audits/2026-08-29-p2-003q-d289-003p-rejection-and-u18-co-closure-refuted.md`](audits/2026-08-29-p2-003q-d289-003p-rejection-and-u18-co-closure-refuted.md).
- **Prior milestone — FBV2-P2-003O / D-288:** THE D-275 SOUTH-BRIDGE
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

## 5. Next task — FBV2-P2-003S (owner-approved bounded placement micro-ECO)
- **There is NO bounded CTO routing lever left for the U18.8 escape.** 003R (D-290) refuted
  the last one (off-layer vacate of U18.7) on cheap non-vacuous evidence, and the refutation
  is geometric: the U18.7/U18.8/U18.9 3-into-one-corner contention is irreducible at the
  0.5 mm pad pitch vs the 0.300 mm current-path clearance floor (D-269). Ordering (D-289),
  off-layer vacate (D-290) and via-size are all refuted or barred; the vacate makes the
  clearance WORSE (0.150 mm via-to-via vs the 0.250 mm neck), and U18.9 is an independent
  casualty. The next move necessarily moves a part — **outside CTO scope.**
- **OWNER DECISION D-291 RESOLVED:** Alpha authorized the CTO-recommended bounded
  LTC4368/R75 placement micro-ECO (D-284/285 class) to open a *second, independent*
  U18.8 escape corridor so the three west-edge sense/control pins escape without the 0.5 mm
  pad-exit contention. Options B (accept U18.8 open — NOT fabricable) and C (direction-2
  widening / broader refloorplan) remain unapproved.
- **Downstream, still CTO-scope but BLOCKED behind the U18 decision:** extend the D-279
  offload to the `N_POL R86.1→TP23.1` F.Cu run (6.36 mm in the R87.2→node corridor) to open
  the REF_POL R87.2 corridor; validate only on a full authority run after the placement work.

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
  width) are bounded CTO-scope work, NOT an owner decision. The **0.60 mm BAT_MAIN
  minimum width** rule is a hard floor (BAT_RAW divider taps are gate-rejected against it,
  not absorbed).
- **D-289** the residual U18.8 `BAT_PROTECTED_P` escape is a **placement-geometry**
  mutual-exclusion, not a routing-order defect: U18.8→R75.2 must escape NORTH into the
  single B lane U18.7→R81.2 also needs and has no alternative B via-site, so U18.7/U18.8/
  U18.9 are a 3-into-one-corner contention where reservation ordering only selects the
  casualty (the 003P sense-pair-clearance relaxation was a lateral U18.7↔U18.8 swap; the
  003Q reserve-U18.8-first lever breaks U18.7+U18.9). The terminal REF_POL R87.2 wall is
  **F.Cu routing capacity** (N_POL 6.36 mm F.Cu saturates the R87.2→node corridor), not a
  DRU rule — a width/clearance/via rule cannot manufacture an F corridor where the graph
  finds none (R89.1 is a true NO_PATH). The narrowest lawful levers are routing-capacity
  moves (off-layer vacate, D-279-class inner offload, path ordering), NOT a DRU exception.
- **D-290** the LAST bounded routing-only U18 co-closure lever — the **off-layer vacate of
  U18.7** D-289 named — is **REFUTED**, and the U18.7/U18.8/U18.9 contention is an
  **irreducible placement-geometry mutual-exclusion at the 0.5 mm pad pitch vs the 0.300 mm
  current-path clearance floor (D-269).** The conflict is at the pad-exit zone, not the
  corridor: U18.8 sits BETWEEN U18.7's south escape and U18.9's north escape, so every escape
  (neck / inner via / via-in-pad) exits within 0.5 mm of the adjacent pin's committed copper.
  Arithmetic: U18.7 neck(0.15)↔U18.8 reserve-via(0.35) = 0.250 mm (the measured DRC); the
  vacate's 0.35 mm through via ↔ U18.8's via = 0.150 mm (WORSE — In2 AND In3 both revert). A
  via ≤0.25 mm reaches the floor with zero margin and two adjacent vias need sub-0.20 mm
  (below the D-257 ladder = a DRU change, BARRED; the reserve via never buys clearance a
  legal width could not), and none reopens U18.9 (dominant blocker U18.10). In1/In4 are the
  only plane layers; In2/In3 are free signal layers, so the failure is geometry, not a plane
  or a rule. **No routing-only site remains — the U18.8 escape is an OWNER DECISION (§8).**
- Rule floors ENFORCED: **0.200 mm** clearance, **0.25 mm** hole-to-hole,
  **0.300 mm** current-path routed clearance (D-269),
  **≥1.20 mm** BPP trunk width (D-249), **0.60 mm** BAT_MAIN minimum width. Six-layer
  stack, GND, netclasses, footprints, polarity, safety set — all frozen. Optional
  `BAT_SENSE TP20.1` (TEST) is separate and not a gate. Frozen `beta-full-reference-v1`
  untouched.

## 8. Open owner decisions
- **NONE.** D-291 records Alpha's approval of the bounded option-A LTC4368/R75 placement
  micro-ECO raised by D-290. The autopilot stop file is removed after this decision record
  is committed; autonomy resumes with FBV2-P2-003S.
- **The decision:** how to open a legal second escape for the U18.8 `BAT_PROTECTED_P` trunk
  pad, given that 003R exhausted the bounded routing-only space (ordering D-289, off-layer
  vacate D-290, via-size all refuted or barred) and the U18.7/U18.8/U18.9 3-into-one-corner
  contention is an irreducible placement-geometry mutual-exclusion at the 0.5 mm pad pitch vs
  the 0.300 mm current-path clearance floor. The next move necessarily moves a part.
- **Options (full engineering consequences + CTO recommendation in the stop file):**
  - **A (CTO-RECOMMENDED) — a bounded LTC4368/R75 placement micro-ECO (D-284/285 class)** that
    increases the U18 west-edge sense/control pad-exit spacing or opens a second corridor so
    all three pins escape without the 0.5 mm-pitch contention. Smallest blast radius; same
    class as the already-owner-approved D-284 spread; every floor/rule/frozen part preserved
    except the named micro-move; needs OWNER approval of the *direction* (like D-284), then a
    CTO engineering pass proves the landing + a supervised full run.
  - **B — accept the board with U18.8 open.** NOT fabricable: `BAT_PROTECTED_P` is one trunk
    pad short of closure, so Phase-A cannot pass. Rejected on its face; listed for completeness.
  - **C — direction-2 corridor widening / broader LTC4368 refloorplan.** Larger mechanical
    blast radius (was explicitly deferred at D-284 in favour of direction 1); only if A proves
    insufficient.
- **Nothing has been changed under this decision:** no part moved, no floor relaxed; the
  authoritative PCB is untouched pending the owner's direction.

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
  Claude or become a task parent. D-291 resolves the owner stop; the stop file is absent.
- **Should an engineering process be active now?** **Yes.** The persistent CTO should run
  exactly one Claude task: FBV2-P2-003S, the approved bounded placement micro-ECO screen and
  full-gate integration. The REF_POL R87.2 F.Cu offload remains downstream CTO-scope work.

## 11. Recovery instructions (a fresh CTO/Claude reads these, in order)
1. `docs/full-beta-v2/CTO_DECISIONS.md` — authoritative rulings (latest: **D-291**, owner
   approval of the bounded option-A LTC4368/R75 placement micro-ECO).
2. Newest audits — `audits/2026-08-29-p2-003r-d290-off-layer-vacate-refuted-owner-decision.md`,
   then `…-003q-d289-003p-rejection-and-u18-co-closure-refuted.md`,
   `…-003o-d288-entry-tie-fix-and-full-run.md`, `…-003n-d287-…`, `…-003m-d286-…`,
   `…-003l-d285-…`, `…-003k-d283-…`.
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
