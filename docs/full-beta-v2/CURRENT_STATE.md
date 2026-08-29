# AQROOT Full Beta v2 — CURRENT STATE (durable checkpoint)

> Checkpoint/index only. Authority precedence: **CTO_DECISIONS.md > accepted
> audits/engineering evidence > CURRENT_STATE.md > summaries/transcripts/session
> memory.** If this file conflicts with higher-authority evidence, repair this file.

## 1. Authoritative HEAD
- **FBV2-P2-003S / D-292 milestone commit (this checkpoint):** a governed **evidence /
  NO-PROGRESS** commit that **RE-RAISES ONE OWNER DECISION.** 003S executed the
  owner-approved (D-291) bounded LTC4368/R75 placement micro-ECO as a cheap, in-scope
  screen (real-DRC bare-placement gate + a fast, `D256`-faithful **`AQROOT_LOCAL=R80`**
  co-closure vehicle) and **screened the bounded U18/R75 space to EXHAUSTION: no bounded
  placement LEGALLY co-closes the U18 escape field.** Baseline (b1_r75rot) = conn 19, DRC
  clean, U18.8 the sole open pad (the D-290 clash). Every candidate is ≤ conn 19: EAST
  translation and R75-south-alone are neutral (U18.8 stays open); NORTH does open a legal
  inner-I2 via for U18.8 (the sought "second escape" exists) but the same rigid move breaks
  the OTHER edge — U18.7 (0.25<0.30) at small north, the east `BAT_RAW`/`LTC_UV`/`LTC_OV`
  current-path pins (0.275–0.296 < 0.300) at larger north; the R75-south align breaks the
  U18.9 Kelvin. The ONLY candidate to reach PHASE A COMPLETE (`s_ne0707`) does so **only by
  absorbing a 0.1248 mm `BAT_RAW`↔`BAT_PROTECTED_P` D-269 breach (41 % of the floor)** and
  is DISQUALIFIED. **Root cause, sharper than D-290:** U18 (LTC4368, MSOP-10, 0.5 mm pitch)
  carries a current-path net on BOTH edges — `BAT_PROTECTED_P` (U18.8, west) and `BAT_RAW`
  (U18.1, east) — so a rigid translation only re-selects which edge breaches the 0.300 mm
  D-269 floor, and R75 is boxed on all four sides (Q3 south ≤0.55 mm, board edge west, U18
  courtyard east, R80/R81 north). **No source, no copper, no placement, no rule change; no
  DRC absorbed; no promotion.** The bounded U18/R75 space the policy named is exhausted, so
  closing `BAT_PROTECTED_P` (U18.8) required an owner direction. **D-293 now approves
  direction 2**: bounded LTC4368-block spread / escape-target relocation, with every floor
  preserved and D-290 remaining closed. Prior milestone:
  `951d7bf` (D-291 owner approval). This checkpoint is written in the same commit; a fresh
  session must confirm the live tip with `git rev-parse HEAD` and `git rev-parse
  origin/master`.
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
  (blocker U18.10 ×25). **D-291 authorized the bounded LTC4368/R75 placement micro-ECO, but
  D-292 (003S) screened it to EXHAUSTION — no bounded U18/R75 delta legally co-closes the
  U18 field (the wall is a both-edges current-path footprint geometry: `BAT_PROTECTED_P`
  U18.8 west and `BAT_RAW` U18.1 east), so closing U18.8 is again an OWNER decision (§8).** The terminal **REF_POL R87.2→(node) NO_PATH** is
  (per D-289) **F.Cu routing capacity** (N_POL 6.36 mm F.Cu saturates its corridor), narrowest
  lever = D-279-class N_POL F.Cu inner offload — but it is downstream of the U18 placement
  micro-ECO. Remaining Phase-A blockers in fabrication-blocker order: (1) **U18.8's escape —
  owner-approved bounded placement work**; (2) the REF_POL R87 F-corridor capacity
  (CTO-scope, blocked behind (1)); (3) the BAT_RAW R89.1/R86.2 divider taps (true NO_PATH /
  other-branch width, a capacity symptom not a width lever).

## 4. Last accepted milestone
- **Task:** FBV2-P2-003S · **Decision:** **D-292** · **Result:** THE OWNER-APPROVED
  BOUNDED LTC4368/R75 PLACEMENT MICRO-ECO (D-291) IS SCREENED TO EXHAUSTION — NO BOUNDED
  U18/R75 PLACEMENT LEGALLY CO-CLOSES THE U18 ESCAPE FIELD (baseline conn 19 with U18.8
  legally open is the max legal state; every move ≤19, trading the casualty among U18.8 /
  U18.7 / the east `BAT_RAW`/`LTC_UV`/`LTC_OV` current-path pins / the U18.9 Kelvin; the one
  candidate to reach PHASE A COMPLETE, `s_ne0707`, does so ONLY by absorbing a 0.1248 mm
  `BAT_RAW`↔`BAT_PROTECTED_P` D-269 breach and is DISQUALIFIED). Root cause sharper than
  D-290: U18 carries a current-path net on BOTH edges (`BAT_PROTECTED_P` U18.8 west /
  `BAT_RAW` U18.1 east) at a rigid 0.5 mm pitch, so a translation only re-selects which
  edge breaches 0.300 mm D-269, and R75 is boxed on all four sides. A governed CTO **FAIL**
  that re-raises the OWNER decision; no source/copper/placement/rule change, no DRC
  absorbed, no promotion, D-275 and D-277..D-291 preserved. Evidence of record: audit
  [`audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md`](audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md);
  scratch gitignored (`checks/w/cand_003s/`, `screen_003s_results.json`,
  `phaseA_003s_*.json`, `log_003s_*.txt`, `drc_ne0707_check.json`).
- **Prior milestone — FBV2-P2-003R / D-290 · Result:** THE LAST BOUNDED
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

## 5. Next task — FBV2-P2-003T (D-293 direction-2 execution)
- **There is NO bounded CTO routing lever AND no bounded U18/R75 placement lever left for
  the U18.8 escape.** 003R (D-290) exhausted the routing-only space; 003S (D-292) has now
  exhausted the owner-approved bounded **placement** space (D-291). No bounded U18/R75 delta
  LEGALLY co-closes the U18 escape field: the max legal state is the baseline (conn 19, U18.8
  open); every move only re-selects the casualty (U18.8 ↔ U18.7 ↔ the east `BAT_RAW`/`LTC_UV`/
  `LTC_OV` current-path pins ↔ the U18.9 Kelvin), and the one placement that reaches PHASE A
  COMPLETE (`s_ne0707`) does so ONLY by absorbing a 0.1248 mm `BAT_RAW`↔`BAT_PROTECTED_P`
  D-269 breach (disqualified).
- **Root cause (D-292, sharper than D-290):** U18 (LTC4368, MSOP-10) carries a current-path
  net on BOTH edges — `BAT_PROTECTED_P` (U18.8, west) and `BAT_RAW` (U18.1, east) — at a
  rigid 0.5 mm pitch, so a rigid translation only re-selects which edge breaches the
  0.300 mm D-269 floor, and R75 is boxed on all four sides (Q3 south ≤0.55 mm, board edge
  west, U18 courtyard east, R80/R81 north; its only motion breaks the U18.9 Kelvin).
- **D-293 OWNER DIRECTION:** execute the bounded direction-2 lever: spread the LTC4368 block
  and/or relocate the minimum escape-target set (R77/R79 east, R80/R81 north as evidence
  dictates) so `BAT_RAW` and `BAT_PROTECTED_P` escape through independent corridors. Preserve
  the D-275/D-288 bridge, enforce D-269 at 0.300 mm, do not accept U18.8 open, and do not
  re-litigate D-290. Start with a cheap real-DRC/real-router screen, then run the first legal
  candidate through the full authority gate; no promotion on proxy evidence.
- **Downstream, still CTO-scope but BLOCKED behind the U18 decision:** extend the D-279
  offload to the `N_POL R86.1→TP23.1` F.Cu run (6.36 mm in the R87.2→node corridor) to open
  the REF_POL R87.2 corridor; validate only on a full authority run after the U18 decision.

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
- **NONE. D-293 resolved the D-292 decision at 22:34 UTC.** Direction 2 is approved; the
  alternatives below are retained only as historical context and are not active options.
- **RESOLVED HISTORY — RE-RAISED by D-292 (FBV2-P2-003S).** The owner-approved bounded LTC4368/R75
  placement micro-ECO (D-291, option A) has been screened to EXHAUSTION and **cannot legally
  co-close the U18 escape field** (details §5, §1; audit D-292). Option A is therefore
  spent; D-293 selected direction 2 and autonomy resumes.
- **The decision:** how to close `BAT_PROTECTED_P` (U18.8) given that BOTH the bounded
  routing-only space (D-290) AND the bounded U18/R75 placement space (D-292) are exhausted,
  and the wall is a **both-edges current-path footprint geometry** (U18 carries
  `BAT_PROTECTED_P` west/U18.8 and `BAT_RAW` east/U18.1, each at a rigid 0.5 mm pitch bound
  by the 0.300 mm D-269 floor; R75 is boxed).
- **Options (all now OWNER-scope; engineering consequences):**
  - **C (now the narrowest remaining) — direction-2:** spread the LTC4368 block and/or
    relocate an escape target (R77/R79 east, R80/R81 north) so the two opposite-edge
    current-path nets escape into different corridors. Larger mechanical blast radius than a
    micro-ECO (was deferred at D-284); needs owner approval of the direction.
  - **D — re-authorize a routing-side lever** (the D-290-refuted+retired off-layer vacate of
    U18.7, or a U18.8 POFV / inner-first reorder) at the north placement that opens U18.8's
    inner via. This re-opens a closed CTO decision (D-290) and is a driver change, not a
    placement ECO; owner must sanction re-litigating D-290.
  - **B — accept the board with U18.8 open.** NOT fabricable (`BAT_PROTECTED_P` one trunk
    pad short of closure); listed for completeness.
- **Nothing has been changed under this decision:** no part moved, no floor relaxed, no DRC
  absorbed into the authoritative board; the authoritative PCB is untouched pending the
  owner's direction.

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
  Claude or become a task parent. D-293 resolved the owner decision; the stop file is absent
  and the persistent CTO resumes one-Claude-at-a-time engineering.
- **Should an engineering process be active now?** **Yes.** FBV2-P2-003T executes the
  D-293 bounded direction-2 screen and authority gate. The REF_POL R87.2
  F.Cu offload remains downstream CTO-scope work, blocked behind the U18 decision.

## 11. Recovery instructions (a fresh CTO/Claude reads these, in order)
1. `docs/full-beta-v2/CTO_DECISIONS.md` — authoritative rulings (latest: **D-293**, owner
   approval of bounded direction-2 LTC4368-block spread / target relocation).
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
