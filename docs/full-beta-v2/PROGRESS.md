# AQROOT Full Beta v2 Progress

**Status: LIVING DASHBOARD.**

**FBV2-P2-003K (2026-08-28) - D-283 the DISJOINT-SUB-BOX southern `BAT_PROTECTED_P` bridge (candidate c) LAYS its lane but has NO LEGAL LANDING - the only forced-south target-island pad (the far-east node cap `C36.1`) is boxed by `GND` and `BAT_MAIN`, so the exit array lands 0.0726 mm from GND and 0.0864 mm from BAT_MAIN; the ungated early bridge then poisons every subsequent gate and the full run cascades (140 rejections across 26 nets); candidate (c) is EXHAUSTED and the remaining lever is the OWNER/mechanical placement-spread fallback; no authoritative promotion; D-275 and D-277..D-282 preserved.** 003J (D-282) localised the one spare >=1.20 mm F.Cu lane to a SOUTHERN band DISJOINT from the tap cluster (taps y<74.7, lane y>75) and deferred the disjoint-sub-box candidate (c) to a supervised full run. 003K implements the minimal env-gated candidate (`AQROOT_BRIDGE_SOUTH`, default inert; implies the `AQROOT_BRIDGE_EARLY` 003I stage): `bridge_early_003i.apply_early(..., south=True)` lays the SAME proven D-275 mechanism but forces the western leg BELOW the tap band with a temporary net-foreign obstacle wall over the corridor-north box (removed with the injected via phantoms, so it shapes only the bridge's own search) and lands on the far-east node cap `C36.1` (`LAND_REFS_SOUTH`); `south=False` reproduces the 003I corridor stage byte-for-byte. **The DISJOINT LANE is viable (necessary precondition holds):** on the reconstructed sparse placed board the south bridge LAYS - entry 4, >=1.20 mm F.Cu traverse, exit 3, land `C36.1`, western leg dips to `ywest=81.85 mm` (well south of the taps at y<74.7) - the half 003J could not prove on the already-dense board. **The LANDING is NOT viable (decisive FAIL):** `C36.1` is the ONLY target-island BPP pad the forced-south leg can reach (no target-island pad exists between `D9.1` x=11 and `C25/C36` x=62, and the OPEN node COPPER D-275 landed on at (40.67,70.71) does not exist early), and its neighbourhood cannot clear a >=0.200 mm exit array - DRC on the laid board shows the exit copper 0.0726 mm from `C36`'s GND pad and 0.0864 mm from `R6`/`R68`'s BAT_MAIN (`BQ25185_SYS`) pad, both < the 0.200 mm floor, the exact 003I clearance class (identical GND 0.0726 mm); the offending neighbours are FIXED pads so the FAIL reproduces on the sparse board. **The full run (parent-supervised; recipe c3_00 + SIXLAYER + D277..D280 + `AQROOT_BRIDGE_EARLY=1` + `AQROOT_BRIDGE_SOUTH=1`; scratch `FIX003K`; fingerprint identical to the 003H reference):** the early stage laid the bridge - `EARLY BRIDGE SOUTH OK land=C36.1 traverse=70.377mm w=1.20 entry=4 exit=3 ywest=81.85` - then, because the early stage lays the bridge UNGATED, the fixed landing violation (GND 0.0726 / BAT_MAIN 0.0864) was read as `new DRC {clearance:2}` by EVERY subsequent per-connection gate and rejected it: **140 gate rejections across 26 nets**; the parent STOPPED the run once decisive (as the 003I parent did), so NO `phaseA_003k_fix.json` was written - no partial board masquerades as a result; the two clearance violations are GENUINE and are NOT absorbed. **Candidate (c) is EXHAUSTED at the LANDING, not the lane;** with (b) refuted (D-282), (d) the 003I FAIL (D-281) and (a) an envelope change (OWNER), the remaining lever is the FALLBACK - a placement spread of the LTC4368 block (OWNER/mechanical), either to OPEN the landing (spread `C36/C25/U11` / the `BQ25185_SYS` neighbourhood) or to WIDEN the corridor - NOT attempted here. **Suites (all PASS):** `bridge_probe_003k` (NEW, A/B/C/D/E), `bridge_probe_003i`, `bridge_probe_003j`, `bridge_probe_003c`/`003d`, `router_regression` G1-G11 (D-280 off), `u19_escape_probe_003e/003f/003g/003h`. Authoritative PCB UNCHANGED (0 tracks / 0 vias); `phaseA_journal.json` restored to HEAD; scratch `FIX003K` gitignored; nothing moved, nothing relaxed; D-275/D-277..D-282 held byte-fixed; the optional `BAT_SENSE TP20.1` (TEST) point treated separately; no authoritative promotion. B-34 open. U19 field closed (D-277..D-280); Phase A NOT completed (D-275 BPP bridge still not integrated - route scope exhausted, OWNER fallback next); Phase B NOT run. PCB routing stays 0 %; overall stays 74 %. Next: FBV2-P2-003L (OWNER/mechanical) - a placement spread of the LTC4368 block. Full analysis: `audits/2026-08-28-p2-003k-d283-south-disjoint-bridge.md`.

**FBV2-P2-003J (2026-08-28) - D-282 the shared western-corridor `BAT_PROTECTED_P` bridge is a TOPOLOGY/CAPACITY wall, and 003J LOCALISES it - the 003I-proposed route-only fix (relocate the `LTC_GATE`/`BAT_RAW` corridor TAP via drops out of the box, candidate b) is MEASURED INSUFFICIENT, because the wall is the WHOLE western through-via + control-copper field, not the taps; the only >=1.20 mm F.Cu path that exists is a ~48 mm SOUTHERN cross-board detour capped at <=1.30 mm, not the D-275 >=1.50 mm corridor bridge; no authoritative promotion; D-275 and D-277..D-280 preserved; the disjoint-sub-box / co-scheduled candidate needs a parent-supervised full run.** 003I (D-281) measured that re-timing the D-275 bridge EARLY lays it but breaks the current-carrying corridor users downstream (`GND` 0.0726 mm, `BAT_MAIN` 0.125 mm, `BAT_RAW` NO_VIA_SITE) and deferred the topology/capacity fix to 003J with four candidate directions. 003J measures them cheaply, in-memory, on a scratch COPY of the committed dense 003H board (`w/FIX003H3`, bridge OFF, the clean 71-connection routed end-state; nothing on disk mutated, the driver never invoked, `phaseA_journal.json` untouched). **Method (`bridge_probe_003j`, NEW, read-only):** reconstruct the exact D-275 mechanism on the dense board - `BR.vacate` (cardinality-1 `BAT_PROT_SHDN_CTL` -> In3, 9 F.Cu tracks moved) + 4x 0.80/0.40 POFV entry array on R75.2 - build ONE QBoard, run the bridge's own high-current traverse rule (>=W F.Cu, D-269 0.30 mm trunk-to-via clearance) via-AWARE against candidate landings with an arbitrary SUBSET of the 56 board through-vias modelled as obstacles; all primitives/constants single-sourced VERBATIM from `bridge_route_003c`. **(A) BASELINE (confirms D-281):** via-AWARE, all 56 vias, near D9.1 landing, 1.20 mm -> NO_PATH. **(B) CANDIDATE (b) REFUTED - the decisive new result:** removing the 9 corridor `LTC_GATE`/`BAT_RAW` TAP vias from the obstacle model (a route-target/staging relocation OUT of the box) does NOT reopen the via-AWARE >=1.20 mm traverse - NO_PATH to the near D9.1 landing AND to the far node; the remaining ~47 control-field through-vias (`LTC_SHDN`/`LTC_OV`/`LTC_UV`/`N_POL`/`REF_POL`/`FAULT_N`/`BAT_SENSE`, each a THROUGH-via barrel across all layers at the 0.30 mm clearance) still wall the F.Cu traverse - **the taps are not the lever; the whole western through-via field is.** **(C) REGION SATURATION + the only path is a DETOUR:** even COPPER-ONLY there is NO_PATH at 1.50 mm (the D-275 target) to any landing and NO_PATH at 1.20 mm to the near D9.1 landing; the single copper-only >=1.20 mm path runs to the far node (40.67,70.71) and is a **47.5 mm SOUTHERN cross-board detour, path max-y 78.8 mm** (>> corridor y<75), capping at <=1.30 mm (NO_PATH at 1.40/1.50 mm, and NO_PATH with the 9 taps ALSO removed) - the same 48.9 mm/1.30 mm path `bridge_probe_003i` clause B reached, now characterised as a cross-board detour, NOT the corridor bridge. **Conclusion (engineering, CTO scope, NOT an OWNER decision):** no END-OF-RUN or via-RELOCATION change yields a viable bridge; candidate (b) is refuted, (d) [early/reserved bridge] is the 003I FAIL, (a) [widen] needs an envelope change (OWNER); the one remaining ROUTE-scope direction is **candidate (c)** - a disjoint bridge sub-box reserved in the sparse window with the western block forced into the complement - which changes CAPACITY, cannot be proven by a bounded probe, and needs a parent-supervised full run. **No false promotion:** no `phaseA_003j_fix.json` claims a clean/absorbed end-state; no driver change was committed (candidate b refuted, not implemented; the candidate c reservation is the next task); the authoritative PCB is 0 tracks / 0 vias. **SUITES ALL PASS:** `bridge_probe_003j` (NEW, clauses A/B/C/D/E), `bridge_probe_003i` (D-281 record intact), `router_regression` G1-G11 (D-280 off), `bridge_probe_003c`/`bridge_probe_003d` (003C/D-275 held FIXED), `u19_escape_probe_003e/003f/003g/003h`. Committed artifacts: `bridge_probe_003j.py`, the audit, the D-282 CTO row, the CHANGELOG + this PROGRESS entry. **Nothing moved and nothing relaxed:** D9, U18, R75-R83, Q3, shunt, FETs, C58, U19, D10 and the whole R84-R96/Q5-Q9 field frozen; `c3_00` NOT promoted; D-249..D-281 (incl. **D-275/D-277/D-278/D-279/D-280/D-281**) untouched; the proven 003C bridge geometry held fixed; the 0.200 mm clearance and 0.25 mm hole-to-hole floors ENFORCED not relaxed; no safety weakening; no topology/net/footprint/polarity change; no six-layer/GND change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**). Phase A NOT completed (the D-275 BPP bridge is still not integrated). **Next FBV2-P2-003K:** implement the minimal env-gated co-scheduled DISJOINT-SUB-BOX bridge reservation (reserve a >=1.50 mm F.Cu bridge lane in the southern band disjoint from the tap cluster - taps sit at y<74.7, the spare lane uses y>75 - in the sparse window, reusing the D-266/D-267 reservation machinery and the `AQROOT_BRIDGE_EARLY` 003I stage as the base, forcing the western LTC block into the complement) and MEASURE on a PARENT-SUPERVISED full run (recipe `c3_00` + SIXLAYER + D277..D280 + the south-reservation gate, ~35-40 min) whether BPP (`D9.1/C58` at >=1.20 mm) closes WITHOUT reintroducing the 003I `GND`/`BAT_MAIN`/`BAT_RAW` clearance/site failures; STOP CRITERIA: candidate only if BPP closes AND `GND`/`BAT_MAIN` hold >=0.200 mm AND `BAT_RAW` keeps its via site AND the DRC histogram equals baseline AND D-277..D-280 retained (any new clearance violation is GENUINE and MUST NOT be absorbed); if the southern reservation cannot hold >=1.20 mm or the western block cannot fit the complement, candidate (c) is exhausted and the fallback is a placement spread of the LTC4368 block (OWNER/mechanical); holding D-275/D-277..D-281 fixed, no netclass/width/clearance/hole-to-hole relaxation, no topology/net/footprint/polarity/safety change, no six-layer/GND change, the optional `BAT_SENSE TP20.1` (TEST) point SEPARATE, no authoritative promotion unless the full Phase-A gate passes, no long full run without CTO supervision. **No progress earned: PCB routing stays 0 %; overall stays 74 %.**

**FBV2-P2-003I (2026-08-28) - D-281 the route-order EARLY landing of the proven D-275 bridge is a MEASURED, REPRODUCIBLE FAIL - the bridge and the current-carrying corridor users (`LTC_GATE`/`BAT_RAW` tap, the `GND` pour and `BAT_MAIN`) CONTEND for one ~9 mm western corridor, so re-timing only changes WHICH high-current user fails, not WHETHER one fails; no authoritative promotion; D-275 and D-277..D-280 preserved; the topology/capacity fix is deferred to 003J.** 003H closed all four named dead-cell blockers and left the D-275 BPP bridge integration as the sole Phase-A promotion blocker. 003D (D-276) had integrated the exact D-275 mechanism as an END-OF-RUN stage and measured it to ABORT; 003I's preflight isolated the cause to western via-density (15 corridor vias vs 11 on the proven-sparse c3 board, `bridge_probe_003i` clause B: the >=1.20 mm via-AWARE traverse NO_PATHs while the copper-only traverse PATHs). **003I measured the obvious re-timing fix (env-gated `AQROOT_BRIDGE_EARLY`, off by default):** lay the EXACT D-275 bridge - the cardinality-1 `BAT_PROT_SHDN_CTL` vacate, the 4x entry array on `R75.2` (POFV), the >=1.20 mm F.Cu traverse, the 4x exit array, all single-sourced VERBATIM from `bridge_route_003c` - at the first stage-8 item, in the proven-sparse window, then restore the driver's via-blind obstacle model so later nets route around the real bridge copper. **It LAYS (necessary):** the parent-supervised full run (recipe `c3_00` + SIXLAYER + D277..D280 + `AQROOT_BRIDGE_EARLY=1`) laid it - `EARLY BRIDGE OK land=C58.1 traverse=8.920mm w=1.50 entry=4 exit=4` - and `bridge_probe_003i` clause E independently lays it on a reconstructed sparse placed board (entry 4, traverse 1.50 mm, exit 4, no new DRC on the sparse board). **But it is NOT sufficient - the MEASURED downstream FAIL:** the current-carrying corridor users routing AFTER the bridge failed their normal gates with two new clearance VIOLATIONS and a lost via site - `GND` clearance actual **0.0726 mm** vs 0.200 mm; `BAT_MAIN` actual **0.125 mm** vs 0.200 mm; `BAT_RAW` **NO_VIA_SITE**. Per CTO ruling these are GENUINE safety-clearance violations and MUST NOT be absorbed into the baseline; the run is INVALID as a candidate and the parent stopped it once the conflict became decisive. **The root cause is a SYMMETRY:** end-of-run the taps block the bridge (NO_PATH, why 003D aborted); early, the 1.50 mm bridge traverse gets in first and the SAME `LTC_GATE`/`BAT_RAW`-tap vias then have no legal site / lose clearance around it. **One corridor, two mutually-exclusive high-current users; route ORDER decides WHICH one fails, not WHETHER one fails - timing is not the lever, the corridor lacks CAPACITY for both.** **No false promotion:** the misleading incomplete interrupted-run board (scratch `FIX003I`) and its clobbered per-run `phaseA_journal.json` were removed / restored so no incomplete result masquerades as evidence; no `phaseA_003i_fix.json` claims a clean/absorbed end-state; the authoritative PCB is 0 tracks / 0 vias. **SUITES ALL PASS:** `bridge_probe_003i` (rewritten as the standing measured-FAIL record, A/B/C/E/F), `router_regression` G1-G11 (D-280 off), `bridge_probe_003c`/`bridge_probe_003d` (003C/D-275 held FIXED), `u19_escape_probe_003e/003f/003g/003h`. Committed artifacts: the env-gated `AQROOT_BRIDGE_EARLY` driver stage in `route_battery_block.py`, `bridge_early_003i.py`, `bridge_probe_003i.py`. **Nothing moved and nothing relaxed:** D9, U18, R75-R83, Q3, shunt, FETs, C58, U19, D10 frozen; `c3_00` NOT promoted; D-249..D-280 (incl. **D-275/D-277/D-278/D-279/D-280**) untouched; the proven 003C bridge geometry held fixed; the 0.200 mm clearance floor ENFORCED not relaxed; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**). Phase A NOT completed (the D-275 BPP bridge is still not integrated). **Next FBV2-P2-003J:** a TOPOLOGY/CAPACITY solution for the shared western corridor - widen or add a corridor, relocate the `LTC_GATE`/`BAT_RAW` taps out of the box, or re-plan so bridge and taps do not contend - preserving the proven D-275 geometry and the D-277..D-280 closures, WITHOUT weakening clearance or any product/electrical requirement; engineering scope within CTO authority, no OWNER decision. **No progress earned: PCB routing stays 0 %; overall stays 74 %.**

**FBV2-P2-003H (2026-08-28) - D-280 the 003G functional casualty `N_BATDIV C61.1->U19.6` is a CO-LOCATED THROUGH-VIA LANDING (NOT pad geometry, NOT a corridor) - the fast direct-escape via placement in `connect_hop` checked only COPPER clearance (waived for the via's own net) and NOT the net-agnostic hole-to-hole floor, so a hop escaping straight onto its co-terminal same-net barrel dropped a second drill on the first; an env-gated hole-to-hole guard rejects the co-locating site and falls the placement through to `via_site`'s legal 0.45 mm barrel, closing C61.1 on a full production run - net-positive, DRC-identical - with D-277/D-278/D-279 and the proven 003C bridge held FIXED.** 003G (D-279) closed both named dead-cell escape blockers and ROTATED one functional casualty onto `N_BATDIV C61.1->U19.6 NO ROUTE` (a bypass cap on the divider-sense node, NOT a test point). 003H discriminated A->B->C (`u19_escape_probe_003h.py`, PASS): **(A) REFUTED** - `U19.6` (SOT-23-8 hard against the west edge, ONE east escape lane) still escapes freely on the empty board (>=2 ways at 0.15 mm); **(B) route-order CONFIRMED as a CO-LOCATION** - two `N_BATDIV` connections are co-terminal at that single escape (`U19.6->R89.2` + the 46 mm cross-board `C61.1->U19.6`), so both want a THROUGH-via barrel there; on the committed 003G BASE board they land 0.450 mm centre - two 0.20 mm drills at EXACTLY the 0.25 mm floor, ZERO margin - and the 003G field re-pack tipped C61.1's landing onto the co-located point (0.035 mm / hole edge -0.165 mm), DRC answering `holes_co_located`/`hole_to_hole`; **the defect** is that `connect_hop`'s fast `free_everywhere` tested only COPPER clearance (`point_free` WAIVES it for the via's own net) and NOT hole-to-hole, while `via_site` (which does enforce it) is consulted only on `free_everywhere` failure; **(C) placement NOT required.** **The fix (D-280, env-gated `AQROOT_D280`):** `free_everywhere` now also enforces the net-agnostic `min_hole_to_hole` floor for the barrel about to be drilled (`max(hole radius)+via_drill/2+250000` vs every hole, own net included); a co-locating site is REJECTED and the placement falls through to `via_site`, which lands the base's own legal 0.45 mm barrel; the guard ONLY adds a rejection (relaxes nothing, moves nothing), unset it reproduces pre-003H byte-for-byte, and the `250000` (0.25 mm) IS the governing DRU `min_hole_to_hole`, byte-identical in structure to `via_site(hole_clr=250000)` and POFV - safely aligned, not a new/looser value. **Full production run (`phaseA_003h_fix.json`, scratch FIX003H3, recipe + `AQROOT_D279=1` + `AQROOT_D280=1`, c3_00 asserted, SIXLAYER, rc0; parent-supervised in session 62295, NOT re-run):** connections 69->**71**, skipped 96, ratsnest 709/-72 -> **708/-73** (one better), DRC identical to baseline, `bridge_eco null`; independent scan of all 52 through-via barrels finds ZERO hole-to-hole edges below 0.25 mm and the two co-terminal N_BATDIV barrels at U19.6 land 0.450 mm centre / **0.2500 mm hole-edge, at the floor** (D-280 off: 0.035 mm / -0.165 mm). **Casualty ledger vs 003G (exact, +2):** + `N_BATDIV C61.1->U19.6` (the D-280 target, RESTORED), + `BAT_RAW R77.1->R79.1`, + `LTC4368_FAULT_N R82.1->Q9.1` with - `LTC4368_FAULT_N Q9.1->(node)` (the SAME net - Q9.1 re-landed on its real pad, not a lost functional net); D-277 (`N_POL U19.3`), D-278 (`VREC_VCC U19.8`), D-279 (`VBRIDGE_TOP R85.1->D10.1`, `REF_HO R92.1<->R93.2`) gains RETAINED. **Terminal OPTIONAL TEST-point disclosure (NOT a functional regression):** the terminal fail is `BAT_SENSE TP20.1->(node)`, role (TEST) - a test point unrouted since 003F and terminal in 003G too; 003H does not newly break it, only its fail reason shifted (003G a D-269 clearance violation 0.30 vs 0.25; 003H NO_PATH at 0.200 mm). **SUITES ALL PASS AND UNREGRESSED:** `u19_escape_probe_003h` (A/B/C/D/E), `u19_escape_probe_003g` (D-279 intact), `u19_escape_probe_003f` (D-278 intact), `u19_escape_probe_003e` (D-277 intact), `router_regression` ALL CHECKS incl. G1-G11 (D-280 off), **`bridge_probe_003c` PASS (003C/D-275 held FIXED)**, `bridge_probe_003d` PASS. `phaseA_journal.json` scratch restored to HEAD; the incomplete `log_FIX003H2.txt` scratch trashed. **Nothing moved and nothing relaxed:** D9, U18, R75-R83, Q3, shunt, FETs, TP17, C58, U19, D10 and the whole R84-R96/Q5-Q9 field frozen; `c3_00` NOT promoted; D-249..D-279 (incl. **D-275/D-277/D-278/D-279**) untouched; the proven 003C bridge held fixed; the `min_hole_to_hole = 0.25 mm` DRU ENFORCED not relaxed; outer-1-oz/high-current policy unchanged; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**). Phase A NOT completed (the held-fixed 003C BPP bridge is proven only in isolation, not yet integrated into the production run); Phase B NOT run. **THE 003G FUNCTIONAL CASUALTY IS CLOSED; all four named dead-cell blockers (D-277/D-278/D-279/D-280) are closed on the full run.** **Next FBV2-P2-003I:** integrate the proven 003C `BAT_PROTECTED_P` vacate + F.Cu via-array bridge into the full production Phase-A run and measure whether BPP (`D9.1/C25/C36/C58` at >=1.20 mm) closes on real routed copper WITHOUT regressing the D-277..D-280 closures, holding D-275/D-277/D-278/D-279/D-280 fixed, no topology/net change, no safety weakening, no netclass/clearance/hole-to-hole relaxation, no authoritative promotion unless the full Phase-A gate passes; treat the optional `BAT_SENSE TP20.1` TEST point SEPARATELY. **No progress earned: PCB routing stays 0 %; overall stays 74 %.**

**FBV2-P2-003G (2026-08-28) - D-279 the dead-cell resistor-field congestion (`VBRIDGE_TOP R85.1->D10.1`, `REF_HO R92.1<->R93.2`) is an ANTISOCIAL B.Cu DETOUR in the packed 0402 field - NOT intrinsic geometry and NOT the D-278 crossing pin - and a measured route-time ANTISOCIAL-DETOUR LAYER HOP closes BOTH named blockers on a full production run (net-positive, DRC-identical), rotating one functional casualty (`N_BATDIV C61.1`) deferred to 003H; D-277/D-278 and the proven 003C bridge held FIXED.** D-278 (003F) cleared U19.8 and named these two blockers, both `NO_LEGAL_ESCAPE >=0.150 mm` in the packed 0402 dead-cell field (R84-R96/Q5-Q9, 0.65 mm pitch). 003G discriminated A->B->C (`u19_escape_probe_003g.py`, PASS): **(A) REFUTED** - empty-board escapes R85.1=8, D10.1=7, R92.1=8, R93.2=8; **(B) route-order CONFIRMED as an ANTISOCIAL DETOUR** - unlike U19.8 the committed `AQROOT_LOCAL=DEADCELL` bounded prefix ROUTES both victims (it omits the west `BAT_RAW` divider so the dead-cell `BAT_RAW` field taps that box R85.1 never lay), so the blockers are FULL-RUN emergent and attribution was done on the real routed baseline board (D-279 off, reproducing `phaseA_003f_fix.json`): R85.1 sealed to 0 by `N_POL R85.2->R86.1` routing 6.23 mm for a 2.48 mm span (2.5x) as a B.Cu HORSESHOE boxing R85.1 (removing it: 0->7 ways), R93.2 by REC_GATE_N wrapping it + the antisocial `REC_BAT_LOW Q7.1->R93.1` (23.1 mm/3.1x) (removing both: 0->8); routed DIRECT on the empty board those connections are harmless (N_POL R85.2->R86.1 = 2.52 mm, R85.1 stays 7) - the aggressor is the DETOUR, the general case of D-278's single crossing pin; **(C) placement NOT required.** **The fix (D-279, env-gated `AQROOT_D279`):** a dead-cell-class SIG B.Cu route whose copper > `D279_K`x its pad span AND > `D279_MIN_MM` (2.0/5.0 mm) is reverted and re-routed as an ordinary 0.35/0.20 through-via hop (D-257 preferred, no rule relaxed), inner signal layer FIRST (leaving outer F.Cu clear for cross-board runs), kept ONLY if legal and strictly shorter; inert for every wide/high-current net, TRUNK/TAP, node target, or route within 2x of its span; unset reproduces pre-003G byte-for-byte. **Full production run (`phaseA_003g_fix.json`, recipe + `AQROOT_D279=1`):** two connections hop onto In2.Cu (`N_POL R85.2->R86.1` 6.2->4.5 mm, `REC_BAT_LOW Q7.1->R93.1` 23.1->9.4 mm) and BOTH victims route; connections 68->**69**, ratsnest 710/−71 -> **709/−72** (one better), in-scope nets connected 23->**24** of 29, DRC identical to baseline, `bridge_eco null`; exactly three nets changed (VBRIDGE_TOP + REF_HO gained, N_BATDIV lost). **Casualty ledger (tracked, not hidden):** the coupled field rotates ONE casualty onto `N_BATDIV C61.1->U19.6` - a FUNCTIONAL bypass cap (NOT a test point), a pre-existing hyper-marginal 46 mm cross-board hop whose landing via co-locates with `U19.6->R89.2`'s via and survives baseline only by ~25 um; robust across F.Cu-first and inner-first hop variants; net +2 named closures −1 casualty = +1; deferred to 003H, NOT claimed closed - the same rotation pattern by which 003F closed U19.8. **SUITES ALL PASS AND UNREGRESSED:** `u19_escape_probe_003g` (A/B/C/D/E), `u19_escape_probe_003f` (D-278 intact), `u19_escape_probe_003e` (D-277 intact), `router_regression` ALL CHECKS incl. G1-G11 (D-279 off), **`bridge_probe_003c` PASS (003C/D-275 held FIXED)**, `bridge_probe_003d` PASS. `phaseA_journal.json` scratch restored to HEAD. **Nothing moved and nothing relaxed:** D9, U18, R75-R83, Q3, shunt, FETs, TP17, C58, U19, D10 and the whole R84-R96/Q5-Q9 field frozen; `c3_00` NOT promoted; D-249..D-278 (incl. **D-275/D-277/D-278**) untouched; the proven 003C bridge held fixed; outer-1-oz/high-current policy unchanged; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**). Phase A NOT completed (held-fixed 003C BPP bridge + C61.1 remain); Phase B NOT run. **BOTH NAMED BLOCKERS CLOSED; the rotated casualty `N_BATDIV C61.1` is the new named blocker.** **Next FBV2-P2-003H:** resolve the `N_BATDIV C61.1->U19.6` marginal cross-board landing (favour a bounded via-site reservation, the D-266/D-267 class, or an owner decision to accept the net-positive trade) WITHOUT moving the frozen field or relaxing the hole-to-hole floor, holding D-277/D-278/**D-279** and 003C fixed. **No progress earned: PCB routing stays 0 %; overall stays 74 %.**

**FBV2-P2-003F (2026-08-28) - D-278 the `VREC_VCC U19.8` NO_LEGAL_ESCAPE is a ROUTE-ORDER CROSSING DETOUR (cause B) - the D-277 crossing pin `REF_POL U19.2`, routed last on B.Cu, HORSE-SHOES over U19.8 - and sending that crossing pin off the outer layer with a LAYER HOP CLEARS U19.8 on a full production Phase-A run; the co-terminal `VBRIDGE_TOP R85.1` is a DISTINCT blocker deferred to 003G; the proven 003C bridge is held FIXED.** D-277 (003E) cleared N_POL U19.3 and named the next task: discriminate `VREC_VCC U19.8->(node) NO_LEGAL_ESCAPE` (blockers track x33, U19.7 x13, board_edge x5, U19.5 x5) and co-terminal `VBRIDGE_TOP R85.1` the same A->B->C way, without assuming another cardinality-0 fix. 003F measured each cause (`u19_escape_probe_003f.py`, PASS): **(A) REFUTED** - on the empty authoritative board U19.8 has 5 legal >=0.150 mm escapes, R85.1 has 8, D10.1 has 7; **(B) route-order CONFIRMED and LOCAL** - a new bounded `AQROOT_LOCAL=DEADCELL` prefix (class of R80/D256/U19, skips the whole west-margin prefix which cannot reach U19's y~=29 corridor) reproduces the blocker byte-similar (`track x34, U19.7 x14` vs the full run's `x33/x13`), so the ~33 blocking `track` hits are all dead-cell copper, and obstacle attribution on the real routed board shows the aggressor is the D-277 crossing pin `REF_POL U19.2` ITSELF - routed last (D-277 correctly routes U19.3 first), its direct southern lane filled by U19.3's copper, it takes a **13.372 mm NORTHERN HORSESHOE** over U19 and walls U19.8 with a segment `(4.65,29.85)->(3.05,29.85)` at d=0.495 mm plus a diagonal at d=0.901 mm (U19.8 -> 0 B.Cu escape, so it cannot even start the F.Cu-hop fallback); the D-277 planar span tie-break cannot catch this because U19.2's straight-line span does not contain U19.8 and U19.8 is a MULTI-LANE victim, not the tied single-lane class; **(C) placement NOT required.** **The fix (cardinality-0 placement):** reuse the exact D-277 `crossings>0 / fr<=1` predicate to mark the crossing pin in `hop_first_keys`; `run_once` then routes it with an ORDINARY 0.35/0.20 through-via F.Cu hop FIRST (D-257 preferred, no rule relaxed) instead of the antisocial B.Cu detour, falling through to the B.Cu ladder untouched on failure; fires only in the D-277 class (today only `REF_POL U19.2`), inert for any pin with a second way out, changes only which LAYER the already-identified crossing pin runs on, lays no authoritative copper. **Full production run (`phaseA_003f_fix.json`, base `phaseA_003d` config, no ECO, 2330 s):** `REF_POL TP24.1->U19.2` 8.610 mm F.Cu+2 vias (direct) and `VREC_VCC U19.8->R84.2` 22.408 mm OK - the D-277 blocker is CLEARED and Phase A advances. Aggregate a WASH BY DESIGN (relocates the binding blocker): connections 68, skipped 94, ratsnest 710 delta -71 (003E was 68/90/711/-70, ONE net better); DRC identical to baseline (`hole_clearance 5 / lib_footprint_issues 199 / solder_mask_bridge 1 / unconnected_items 499`); `bridge_eco null`. Journal diff vs 003E: +U19.8, +`REF_HO R91.2->R92.1`, +`REC_GATE_N TP21.1->R94.2`; -`BAT_SENSE TP20.1` (a test point), -`REC_GATE_N R94.2->(node)`, -`REF_HO R92.1->R93.2`. **The co-terminal `VBRIDGE_TOP R85.1` is a DISTINCT blocker -> 003G:** R85.1 was never routed in 003E either; on the real routed board it is boxed by **N_POL** (x10 within 2.0 mm) not the REF_POL crossing, and neither it nor its aggressor is single-lane, so the D-278 predicate correctly does not mark it; same pattern `REF_HO R92.1<->R93.2` boxed by REC_GATE_N x8 - the DEAD-CELL RESISTOR-FIELD CONGESTION class (packed 0402 cluster R84-R96 / Q5-Q9, casualties rotate); the BPP closure (`D9.1/C25/C36/C58 at >=1.20 mm`) is the KNOWN held-fixed 003C bridge case, not new. **SUITES ALL PASS AND UNREGRESSED:** `u19_escape_probe_003f` (A/B/C/D/E, E pinning that the committed full run routes U19.8 and does NOT route R85.1 - deferred, not over-claimed), `u19_escape_probe_003e` (D-277 intact), `router_regression` ALL CHECKS incl. G1-G11, **`bridge_probe_003c` PASS (003C/D-275 held fixed)**, `bridge_probe_003d` PASS (committed 003D FAIL artifacts still pin `N_POL U19.3`, un-regressed). `phaseA_journal.json` scratch restored to HEAD. **Nothing moved and nothing relaxed:** D9, U18, R75, R76..R83, Q3, the shunt, the FETs, TP17 and C58 all frozen; `c3_00` NOT promoted; D-249..D-277 (incl. **D-275**) untouched; outer-1-oz / high-current policy unchanged; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**, no source mutated). **U19.8 CLEARED; the dead-cell resistor-field congestion (`VBRIDGE_TOP R85.1`, `REF_HO R92/R93`) is the new named blocker.** Phase A NOT completed; Phase B NOT run. **Next FBV2-P2-003G:** discriminate `VBRIDGE_TOP R85.1` (boxed by N_POL) and `REF_HO R92.1<->R93.2` (boxed by REC_GATE_N) - the dead-cell resistor-field congestion - the same A->B->C way, WITHOUT assuming a single-pin hop suffices (R85.1 is a MULTI-LANE victim of a NON-crossing-class aggressor), holding D-277/D-278 and 003C fixed, no topology/net change, no safety weakening, no authoritative promotion unless a later full gate passes. **No progress earned: PCB routing stays 0 %; overall stays 74 %.**

**FBV2-P2-003E (2026-08-28) - D-277 the U19.3 N_POL NO_LEGAL_ESCAPE is a ROUTE-ORDER CONTENTION (cause B), NOT pad/board geometry; a CARDINALITY-0 planar tie-break in the driver CLEARS it on a full production Phase-A run and Phase A ADVANCES to a new deeper blocker `VREC_VCC U19.8`; the proven 003C bridge is held FIXED.** D-276 named `N_POL U19.3->(node) NO_LEGAL_ESCAPE at >=0.150 mm` (blockers board_edge x23, U19.4 x16, U19.2 x12, U19.6 x8) as the full-driver Phase-A blocker and named the next task: a bounded investigation distinguishing (A) pad-escape geometry, (B) route-order/copper obstruction, (C) minimum placement ECO, holding the proven 003C vacate + F.Cu 4-via bridge FIXED. 003E measured each cause with cheap analytic + isolated real-router probes (`u19_escape_probe_003e.py`, PASS) and found the cause is **(B) route-order**, not (A) geometry or (C) placement: **(A) REFUTED** - on the empty authoritative board (0 signal tracks; U19 is NOT moved by c3, which moves only R75/U18/R79) U19.3 HAS a legal >=0.150 mm escape east into the inter-row gap, U19.2 also escapes, both middle west-row pins are SINGLE-LANE (freedom 1); **(B) CONFIRMED and directional** - routing `REF_POL TP24.1->U19.2` FIRST drops U19.3 freedom to 0 and reproduces the D-276 fail string byte-for-byte, routing `N_POL TP23.1->U19.3` FIRST leaves U19.2 escapable and BOTH route, because U19.2 sits NORTH of U19.3 but its target TP24.1 is SOUTH so its route crosses south over U19.3's only lane and seals it, while U19.3's target TP23.1 does not cross U19.2 (textbook planar-fanout ordering); **(C) NOT REQUIRED** (B is fixable by order alone), left un-exercised per the A->B->C order. **The fix (cardinality-0):** `order_tight` already routes the tightest pin first but U19.2/U19.3 tie on EVERY key (slack +0.14, ways-out 1, width), so the order fell through to the arbitrary MST order that put U19.2 first; the repair adds ONE final tie-break on live geometry - among rows tied on `(slack, ways-out)` with ways-out <=1, `crossings[i]` counts tied siblings whose pad falls inside row i's pad->target span, sort key becomes `(slack, ways-out, width, crossings)`, U19.2's span contains U19.3 (crossing 1) and U19.3's does not contain U19.2 (crossing 0) so U19.3 routes first; the term is 0 for any pin with a second way out (guarded `fr_a <= 1`), is the LAST sort key (settles only exact ties, never reorders across tightness classes), and lays no copper. **Full production run (`phaseA_003e_fix.json`, base `phaseA_003d` config, no ECO, 2306.8 s):** the pin-field slack line now reads `U19.3 +0.14/1way  U19.2 +0.14/1way …` (reordered as predicted) and both boxed pins route (`N_POL TP23.1->U19.3` 6.118 mm OK, `REF_POL TP24.1->U19.2` 13.372 mm OK); the D-276 blocker is CLEARED and Phase A advances to `PHASE A: FAIL - VREC_VCC U19.8->(node) NO_LEGAL_ESCAPE at >=0.150 mm; blocked by track (x33), U19.7 (x13), board_edge (x5), U19.5 (x5)` (co-terminal `VBRIDGE_TOP R85.1` also NO_LEGAL_ESCAPE; both -0.15/0way, stable across all 3 passes). Aggregate is a WASH BY DESIGN (the fix relocates the binding blocker, it does not close Phase A): connections 68, skipped 90, ratsnest 711 delta -70 (003D-base 68/91/710/-71); DRC identical to baseline (`hole_clearance 5 / lib_footprint_issues 199 / solder_mask_bridge 1 / unconnected_items 499`); `bridge_eco null`. The U19.8 blocker is a DIFFERENT CLASS from D-276 - dominated by FOREIGN laid `track` (x33) on the EAST row, not board_edge + own pins - so the west-row planar tie-break does not apply and a route-order swap is unlikely to be sufficient. **SUITES ALL PASS AND UNREGRESSED:** `u19_escape_probe_003e`, `router_regression` ALL CHECKS incl. G1-G11, **`bridge_probe_003c` PASS (003C/D-275 held fixed)**, `bridge_probe_003d` PASS (committed 003D FAIL artifacts still pin `N_POL U19.3`, un-regressed). `phaseA_journal.json` scratch restored to HEAD. **Nothing moved and nothing relaxed:** D9, U18, R75, R76..R83, Q3, the shunt, the FETs, TP17 and C58 all frozen; `c3_00` NOT promoted; D-249..D-276 (incl. **D-275**) untouched; outer-1-oz / high-current policy unchanged; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion (Phase A did not pass). Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**, no source mutated). **U19.3 CLEARED; `VREC_VCC U19.8` is the new named blocker.** Phase A NOT completed; Phase B NOT run. **Next FBV2-P2-003F:** discriminate the `VREC_VCC U19.8` (and co-terminal `VBRIDGE_TOP R85.1`) NO_LEGAL_ESCAPE the same way 003E did U19.3 - (A) intrinsic east-row geometry vs (B) foreign-track contention vs (C) placement - WITHOUT assuming another cardinality-0 fix exists, holding 003C fixed, no topology/net change, no safety weakening, no authoritative promotion unless a later full gate passes. **No progress earned: PCB routing stays 0 %; overall stays 74 %.**

**FBV2-P2-003D (2026-08-28) - D-276 the DRIVER-INTEGRATED vacate + F.Cu bridge is a MEASURED REPRODUCIBLE FAIL; the full production driver fails UPSTREAM at U19.3 N_POL NO_LEGAL_ESCAPE and the 003C-style bridge ECO ABORTS (no >=1.20 mm F.Cu corridor); 003C/D-275 is NOT invalidated and remains the FIXED proven solution for 003E.** D-275 proved the western-corridor vacate + F.Cu via-array bridge as a POST-PROCESS of a hand-staged reproduced c3 board and named the next task: integrate that mechanism into the production Phase-A driver + drive it through a full 2-pass route (the D-271 discipline). 003D performs that integration (`route_battery_block.py` gains ONE `AQROOT_BRIDGE_ECO`-guarded call to `bridge_eco_003d.apply_eco`, single-sourcing the D-275 primitives verbatim from `bridge_route_003c`) and the full driver route **reproducibly fails on two independent passes**: (1) Phase A fails earlier at `N_POL U19.3->(node) NO_LEGAL_ESCAPE at >=0.150 mm`, blocked by board_edge (x23), U19.4 (x16), U19.2 (x12), U19.6 (x8); and (2) the integrated 003C-style vacate-then-bridge attempt reports `ECO ABORT: no >=1.20 mm F.Cu traverse corridor` (the vacate runs - 6 F.Cu tracks moved, 48 existing vias - but the production board has no >=1.20 mm F.Cu lane to bridge, unlike the hand-staged 003C board). **Reproduced (D-271):** `phaseA_003d_ecoC.json` / `ecoD.json` are not byte-identical (per-net `secs` jitter only) but every DECISIVE field is identical - the Phase-A fail string, `connections 68`, `skipped 91`, `ratsnest 710` delta `-71`, DRC `hole_clearance 5 / lib_footprint_issues 199 / solder_mask_bridge 1 / unconnected_items 499` (= authoritative baseline), and `bridge_eco.ok false` / `fail "no >= 1.20 mm F.Cu traverse corridor"` / `vacated 6` / `existing_vias 48`; the base `phaseA_003d.json` (no ECO) shows the SAME U19.3 fail, so it is upstream of the bridge ECO. **003C/D-275 NOT invalidated** - its post-processed reproducible `BAT_PROTECTED_P` closure stays the fixed proven solution for 003E (`bridge_probe_003c` re-run PASS); 003D fails production/full-driver promotion, it does not disprove D-275. **Orchestration failure (continuation loss, NOT engineering, NOT OWNER):** the CTO launched ecoC/ecoD `nohup setsid ... &` from a one-shot turn then ended with a normal text response and no `sessions_yield` / persistent waiter / completion callback tied to PIDs 274901/274902; the detached children finished at 04:31 UTC but a process exit cannot re-awaken an already-ended turn, and the finalize ACP session had ended at the wait boundary. Repair discipline: ACP owns foreground work and returns a completion event; CTO uses `sessions_yield` and resumes from it; no unregistered detached child batches. **Delivered + regression:** the env-guarded driver hook (inert with `AQROOT_BRIDGE_ECO` unset - the default), `bridge_eco_003d.py`, `bridge_gates_003d.py`, three result JSONs + ecoC/ecoD/c3repro logs; and **`bridge_probe_003d.py` CONVERTED to pin the measured reproducible FAIL** (it first presumed a passing gate that never existed since the ECO aborts) - A wired/ordered hook, B single-sourced D-275 primitives, C cardinality-1 control-role vacate, D each `phaseA_003d_eco*.json` records the FAIL with NO false promotion, E 2-pass determinism of the FAIL - **PASS**. Incomplete `ecoA`/`ecoB` scratch logs removed; `phaseA_journal.json` scratch churn restored. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**, no source mutated); all suites PASS incl. `router_regression` G1-G11, `bridge_probe_003d`, `bridge_probe_003c`, `via_array_probe`, `d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`. D-249..D-275 untouched; no safety weakening, no topology/net change, no authoritative promotion. **U19.3 is the new named blocker;** Phase A/B NOT run. **Next FBV2-P2-003E:** bounded investigation of the U19.3 `N_POL` NO_LEGAL_ESCAPE holding the proven 003C vacate + F.Cu 4-via bridge FIXED - pad-escape geometry vs route-order/copper obstruction vs minimum placement ECO; inspect U19.3/U19.2/U19.4/U19.6 + board edge; analytic pad-escape + smallest real-router probes; no broad placement search, no topology/net change, no safety weakening, no authoritative promotion unless a later full gate passes. **No progress earned: PCB routing stays 0 %; overall stays 74 %.**

**FBV2-P2-003C (2026-08-28) - D-275 the western-corridor VACATE ECO + F.Cu VIA-ARRAY BRIDGE is PROVEN; the minimum vacate is ONE low-current control branch, and the BAT_PROTECTED_P trunk CLOSES on real, reproducible copper (PR-40 9/9, U18 8/8, no new DRC, no regression) - the first trunk closure in the D-270..D-274 arc.** D-274 named the next step: a bounded control-net vacate ECO to open a >=1.20 mm F.Cu lane, then route the bridge. 003C runs it on the reproduced c3 board (`run_prefix_002z.py c3_00.json c3repro003c` -> `targets=111111101`, U18 8/8, sense 13.811 mm, byte-consistent with D-274) and it **succeeds**. The F.Cu cut-set study (`fcu_cutset_003c.py`, by INDIVIDUAL routed branch, never whole-net) finds the **MINIMUM vacate is cardinality 1: `BAT_PROT_SHDN_CTL`** - moving that one low-current control branch off F.Cu to In3 turns the R75.2->node A* from NO_PATH to PATH at both 1.50 and 1.20 (baseline flood dies at x=4.80 exactly as D-274; reproduced on c3repro003b and 003c). Only one branch discriminates, not D-274's three, because `BAT_PROT_SHDN_CTL`'s F.Cu is a 46 mm WALL (y 59.75..93.47) and removing it lets R75.2 detour to the OPEN node at x=38.5, avoiding the D9 single-via link. The real bridge (`bridge_route_003c.py`): VACATE the 6 F.Cu tracks to In3 (through-vias preserve continuity; In1/In4 GND planes kept intact; a control net needs no netclass rule); ENTRY 4x 0.80/0.40 through vias on R75.2's pad (POFV, D-258), hole-legal against the existing U18.8 sense via; TRAVERSE 50.99 mm of 1.40 mm F.Cu routed VIA-AWARE (`inject_vias` enforces the 0.30 mm D-269 clearance to existing vias that QBoard skips; 1.50 mm is NO_PATH, so 1.40 mm - above the 1.20 mm floor, target 1.50 honestly not reached); EXIT 4x 0.80/0.40 through vias landing on the node's 1.20 mm B.Cu copper, an ARRAY landing (no single via carries pack current). Gates (save/reload KiCad, `bridge_gates_003c.py`): PR-40 `111111101`->`111111111`, bit 8 CLOSED, U18 8/8, vacated `BAT_PROT_SHDN_CTL` stays connected, no regression, DRC identical to baseline (0 new), ratsnest 741->740 (-1) - **VERDICT PASS**. Electricals: R_bridge ~18.9 mOhm, 42.5 mW/28 mV at 1.5 A, 57.8 mW/33 mV at 1.75 A. New regression **`bridge_probe_003c.py`** (real copper+DRC): vacated control net on In3 ALLOWED, trunk on In2/In3 REJECTED, current-carrying never a vacate candidate, bridge board closes bit 8 no-new-DRC - **PASS**. **NOT an owner decision** - promotion to the authoritative product board requires driver integration + c3-placement promotion through a full 2-pass Phase-A route (the D-271 reproducibility discipline); that is the next task, CTO scope. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**, no source mutated); all suites PASS incl. `router_regression` G1-G11, `bridge_probe_003c`, `via_array_probe`, `d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`; `phaseA_journal.json` scratch churn restored. B-34 to be updated on promotion. U19 NOT searched; Phase A/B NOT run. **The western trunk blocker that stalled D-270..D-274 is BROKEN; no authoritative progress earned yet: PCB routing stays 0 %; overall stays 74 %.**

**FBV2-P2-003B (2026-08-28) - D-274 the bounded F.Cu HIGH-CURRENT VIA BRIDGE is DISPROVED; the two via
arrays exist but the F.Cu traverse does not at >=1.20 mm; the western margin is saturated on F.Cu exactly
as on B.Cu; a measured FAIL, next is a control-net corridor-vacate ECO.** D-273 named the F.Cu via bridge
as the next step; 003B investigates it on the reproduced c3 board (`run_prefix_002z.py c3_00.json
c3repro003b` -> `targets=111111101`, U18 8/8, sense 13.811 mm, byte-consistent with D-273) with
evidence-based via-array sizing and real searches. Measured islands (KiCad `GetConnectedItems`): TARGET
`{D9.1,C25.1,C36.1,U11.2}` (D9.1 already tied to U11.2 via the C25/C36 F.Cu cap copper through two SINGLE
0.80/0.40 vias); SOURCE `{R75.2,U18.8}` at x=2.80 - ~8 mm apart. Via-array sizing (`via_array_003b.py`,
board's own IPC-2221B, reproduces the DRU's 0.525 mm exactly): a 0.40/25um barrel carries 1.055 A at 10 K
internal; 1.75 A validation -> floor 3 (fault-tolerant), design 4. `bridge_feasibility_003b.py`: **ENTRY
feasible** (4-via array on R75.2's pad, F.Cu empty within 3.5 mm, via-in-pad/POFV), **EXIT feasible**
(4-via arrays on the node), **TRAVERSE IMPOSSIBLE at >=1.20 mm** - F.Cu full-width flood from R75.2 dies at
**x=4.80 mm** (only <=0.80 mm threads to x=11.6, below the mandatory 1.20 mm floor which may not be waived),
and full-budget A* R75.2->node returns **NO_PATH at 1.20 AND 1.50 mm by exhaustion**. Blocker: the LTC_GATE
x=5.75 vertical, the BAT_PROT_SHDN_CTL diagonal, the BAT_RAW y=72.45 run in the x 4.8..11 / y 66..73 window.
`c3_00` remains **EVIDENCE ONLY, NOT promoted**; bit 8 stays open. **NOT an owner decision** - the next
task is a **bounded western-corridor control-net vacate ECO** (CTO scope, the D-270 class) to open a
>=1.20 mm F.Cu lane, then route the bridge. New regression **`via_array_probe.py`** pins the via-array
sizing contract and rejects undersized (single-/two-via) transitions - **PASS**. Authoritative PCB UNCHANGED
(six layers, **0 tracks, 0 vias**, no source mutated); all suites PASS incl. `router_regression` G1-G11,
`via_array_probe`, `d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`; `phaseA_journal.json`
scratch churn restored. B-34 open. U19 NOT searched; Phase A/B NOT run. PCB routing stays 0 %; overall
stays 74 %.

**FBV2-P2-003A (2026-08-28) - D-273 the LONG outer-B.Cu ZERO-VIA route is DISPROVED at target 1.50 and
floor 1.20; a measured FAIL, corroborated by the router's own search; next is a bounded F.Cu high-current
via bridge.** D-272 sent the trunk question into a bounded routing proof - test the reservation-dependent
LONG outer-B.Cu route for `BAT_PROTECTED_P` BEFORE any F.Cu via bridge - and 003A runs it on the proven
c3 board (U18 8/8, trunk open, reproduced from `c3_00.json` via `run_prefix_002z.py`) and it FAILS. Bounded
family probe (`long_corridor_003a_bounded.py`, reproduced byte-identically): control `R75.2->D9.1` @1.50
NO_LEGAL_ESCAPE / @1.20 NO_PATH; four topologically distinct long families (north/mid/south + D9-reservation-
first, the ONE central free channel deduped by `occ_003a.py`) ALL FAIL both widths - @1.50 `R75.2` cannot
leave its pad at 1.5 mm, @1.20 it escapes ~2.7 mm then COARSE_BLOCKED. Corroborated WITHOUT the coarse
prefilter by `long_corridor_003a_corrob.py`: the SAME `QR.connect_role` the router uses for the trunk,
`R75.2` -> node copper, at FULL default budgets - all 8 trials FAIL, @1.20 NO_PATH after a 48-62 s reachable-
region exhaustion (not a timeout). `R75.2` is copper-locked in the western mass; the one central channel is
unreachable at trunk width. `c3_00` remains **EVIDENCE ONLY, NOT promoted**; bit 8 `BAT_PROTECTED_P
R75.2->U11.2` stays open. **This is NOT an owner decision** - the long-route proof was the gate D-272 set,
and it has run; the **next technical task is a bounded named-path F.Cu high-current via-bridge investigation**
(evidence-based via-array sizing - inner layers 0.5 oz, ~2.73 mm for 1.5 A at 10 K - + full safety / DRC /
connectivity gates), NOT implemented or tested here. Delivered the bounded probe + full-budget corroboration
+ three read-only geometry helpers; retained the naive un-bounded draft as the documented rejected approach;
new regression **G11** pins the bounded-search contract on the authoritative board (a tiny budget BOUNDS the
search; the probe budget does NOT fabricate a FAIL) - **4/4 PASS**. Authoritative PCB UNCHANGED (six layers,
**0 tracks, 0 vias**, no source mutated); all suites PASS incl. `router_regression` G1-G11,
`d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`; `phaseA_journal.json` scratch churn restored.
B-34 open. U19 NOT searched; Phase A/B NOT run. PCB routing stays 0 %; overall stays 74 %.

**FBV2-P2-002Z (2026-08-27) - D-272 western-margin PLACEMENT SCOPE is EXHAUSTED; the first
reproducible U18 8/8 does NOT close the BPP trunk; CTO CLOSEOUT, not an owner escalation.** Bounded
battery-block placement was CTO authority (D-249...D-271) and is now spent to its floor. The
cardinality ladder: baseline (U18 pose alone) **6/8**; c1 (one component) **ceiling 7/8**; c2
(R75+U18, 5 supervised) **ceiling 7/8 AND target bit 8 `BAT_PROTECTED_P R75.2->U11.2` FALSE in all
five** (the trunk routes freely at 1.50 mm with NO fanout but is dead at every width once the 8-pin
fanout is laid - the west margin is saturated in the PLANE, not along a length); c3 (R75+U18+one
divider) delivers the **first reproducible U18 8/8** (`c3_e10n_r79`/`c3_00`, targets `111111101`,
ledger 7/29, sense 13.811 mm) - the unique lever widening the analytic trunk 0.40->0.80 mm - **but
bit 8 is still FALSE and the 8/8 is knife-edge**; c4 the last family, a bounded-exhaustive **705-pose
U18-pose vacate sweep**, is **NEGATIVE** (102 fan-8 mech-clean poses, `trunk_best_w` only ever 0.40 mm
or dead, ZERO reach the 1.20 mm floor). No legal fan-8 placement reaches even 0.80 mm or closes bit 8.
`c3_00` is accepted **as EVIDENCE ONLY, NOT promoted** to placement or authoritative copper. **This
SUPERSEDES D-271's owner-escalation framing:** the placement-change half was CTO authority and is
exhausted, so the next technical task tests the **reservation-dependent LONG outer B.Cu route FIRST**
(preserves outer 1 oz + high-current zero-via policy; ~2.29x trunk resistance / ~18.9 mW at 1.5 A to
VERIFY, not escalate); the F.Cu high-current via bridge is a **deferred fallback, not authorized**.
Delivered a generalized process-unique DRC transient fix (`path_role_util.py`) + new regression **G10**
(4/4 PASS) that reproduces the concurrent-search DRC clobber. Authoritative PCB UNCHANGED (six layers,
**0 tracks, 0 vias**, verified); all suites PASS incl. `router_regression` G1-G10; `phaseA_journal.json`
scratch churn restored. B-34 open. PCB routing stays 0 %; overall stays 74 %.

**FBV2-P2-002Y (2026-08-27) - D-271 the 002W prefix is PINNED and DETERMINISTIC; the "proven 8/8"
board is NOT reconstructible from committed code; DECISION STOP.** The reproduction gap 002X flagged
is a reproducibility defect, not a router defect. On the AUTHORITATIVE placement the pinned recipe
reserves `U18.8` at **(3.000, 71.600)** on both attempts and IDENTICALLY at commits 002T/002U/HEAD -
so D-269's clearance change is NOT the cause (this supersedes 002X's attribution), and the site is the
sole candidate that seals no sibling at reservation time. The "3.750 / 8-of-8" board (13.532 mm sense
path) is not produced by the committed code with any recipe - even at the 002T commit it gives
18.200 mm and (3.000, 71.600). The true blocker is the current-carrying `BAT_SENSE` diagonal
(6.75,62.45)→(2.80,66.40), here `U18.7`'s casualty - confirming and tightening 002X on a reproducible
board. Delivered: `prefix_002w.py` + `prefix_002w_manifest.json` (DETERMINISM gate PASS pins the board;
GOVERNED-GOAL gate FAIL by design - U18 6/8 at the blocking site). The placement trap is guarded by
`AQROOT_EXPECT_PLACEMENT=AUTHORITATIVE` in the recipe. Authoritative PCB UNCHANGED (0 tracks, 0 vias);
no routing code or rule changed. All standing suites PASS. OWNER decision required (protection
architecture or placement). B-34 open. PCB routing stays 0 %; overall stays 74 %.

**FBV2-P2-002X (2026-08-27) - D-270 path-role OFFLOAD delivered and proven; DECISION STOP.**
A bounded low-current TAP branch on a power-named net may take In2/In3 inside its own corridor
(`d270_probe` 11/11 PASS; mechanism in `path_role_dru.INNER_OFFLOAD_AREAS` + `D270_SETS`), and
every current-carrying role is still barred. The per-branch offload probe (`offload_probe_002x.py`,
which cuts ONE routed branch's B.Cu, never a whole net) proves that **no low-current offload set of
any cardinality re-opens `R75.2 -> D9.1` at >=1.20 mm** - the binding blocker is the `BAT_SENSE`
1.00 mm shunt CURRENT path, which D-270 correctly refuses to move; the real harness confirms it
(trunk GATE_REJECTED on D-269 clearance 0.250<0.300 to `BAT_SENSE`). Bounded by a reproduction gap:
the 002W 8/8 prefix does not reproduce at HEAD (D-266 `U18.8` reservation lands at (3.000) not the
002T-proven (3.750); U18 7/8). Authoritative PCB UNCHANGED (0 tracks, 0 vias). All suites PASS. B-34
open. PCB routing stays 0 %; overall stays 74 %.

Date: 2026-08-27 (updated after **FBV2-P2-002R - **THE AUTHORITATIVE PCB IS NOW SIX LAYERS.** **A - six-layer architecture lock: PASS** (`f8c931b`); **B - D-263 routing: DECISION STOP**; the two are independent by section 2's ruling and the second does not undo the first. JLCPCB **JLC06161H-7628**, nominal 1.6 mm, 1 oz outer / 0.5 oz inner, **In1 and In4 solid GND**, In2/In3 internal signal, no blind/buried/laser vias, with rollback point **`beta-v2-p2-pre-sixlayer-authoritative`** pushed and verified at `5f10073` before any modification. Validated after save/reload/refill: 6 layers in order, published dielectrics 0.2104 / 0.4 / 0.2028 / 0.4 / 0.2104, **In1 one island and In4 one island**, no pour on In2/In3, **zero signal tracks and zero signal vias**, outline datum 72.000 x 148.000 mm, **324 of 324 footprint positions IDENTICAL** to the pre-lock board, **DRC byte-for-byte the four-layer baseline**, ERC unchanged, all five suites PASS - and `p1_regression` now guards BOTH reference planes. **THE D-263 ROUTING STOPS.** Section 10's reordering was implemented and **moves the casualty rather than removing it**: trunk-first cost `U18.2`/`U18.3`/`U18.7`, Kelvin-first cost four control pins, and **controls-first costs `U18.6` and the sense pads** (`R75.1`, `R75.2`, `Q3.5`, `Q3.6` all `NO_LEGAL_ESCAPE`) - **three orders, three casualties, one cause: there is not enough B.Cu around U18 and R75 for the pin field, the sense pair and the high-current chain to coexist.** With controls first `LTC_OV` closes as ONE COMPONENT on B.Cu with ZERO vias (`R77.2 -> R78.1` 2.457 mm), `LTC_GATE` closes all six functional pads, `FAULT_N` all four, `LTC_UV` 9.889 mm and VIN 4.910 mm - **but `LTC_SHDN U18.6 -> R80.2` is `NO_LEGAL_ESCAPE`**, so section 11's reservation never reaches 8/8. **AND SECTION 14'S PAIRED-INTERNAL KELVIN IS BARRED BY A STANDING RULE, NOT BY GEOMETRY:** `BAT_PROTECTED_P U18.8 -> R75.2` is rejected with **"Items not allowed (rule 'BAT_MAIN is outer-layer only')"** - the rule covers the whole net, the Kelvin tap is part of it, and it was written for the 1.5 A path with **no exception for a nanoamp sense branch that merely shares the net name**. **DECISIONS REQUIRED: scope `BAT_MAIN is outer-layer only` to current-carrying copper** (for instance by excluding the already-bounded D-249 sense corridors), then re-run sections 11-22; and **`LTC_SHDN U18.6 -> R80.2` needs its own look**. **No authoritative signal copper or placement ECO was written.** **U19 NOT SEARCHED**; Phase A/B NOT run. B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 % - no progress is earned by an architecture lock.** previously **FBV2-P2-002Q - PR-49 routing closeout. **FAIL at section 14. The authoritative stackup was NOT changed** (section 18 gates it on section 14), so the PCB is byte-identical to `adabe98` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper layers, zero signal tracks, zero signal vias**. All five suites PASS. **PR-49 IS DELIVERED, REGRESSION-PROVEN AND DEMONSTRATED TWICE ON REAL COPPER:** `BAT_PROTECTED_P R75.2 -> D9.1` routes 1.50 mm, is rejected on `copper_edge_clearance`, **falls to 1.20 mm and routes 19.219 mm on B.Cu with zero vias** - and a second instance appeared unprompted, `LTC_GATE U18.10 -> Q3.4` falling 0.20 -> 0.15 mm. **`BAT_PROTECTED_P` now carries `D9.1` in its functional island**, closing the split 002P reported. **The rule is GENERAL, not a board-specific hack** - it lives in one place, `route_battery_block.ladder_retry`, and **G9 in `router_regression.py`** pins all five properties (falls to the next authorised rung; **never invents a rung below the ladder**; fails cleanly when every rung is rejected; **does NOT walk the ladder on a non-gate failure**; leaves **no copper behind**). `router_regression` ALL CHECKS PASS, G1-G9, and `PLAN_1_BPP_TRUNK` remains exactly 1.50 mm target / 1.20 mm floor. **AND CLOSING THE TRUNK COSTS THREE U18 CONTROL PINS:** on the identical frozen placement 002P reported **U18 8/8 with the trunk ABSENT**, and with the trunk actually laid **U18 falls to 5/8** (`U18.2`, `U18.3`, `U18.7` open) - the two results do not conflict, they are the same board with one more connection on it, and **002P's 8/8 was in part an artefact of a connection that never got laid**. **THE SECTION 9 KELVIN-ORDERING HYPOTHESIS IS MEASURED FALSE**: Kelvin taps first gives U18 4/8 against 5/8 in plan order - the taps do not obstruct the trunk, they take the pin-field lanes the control nets need - and the flag stays in the harness, off, so a rejected hypothesis stays reproducible. **Routed Kelvin best case 8.667 / 11.130 mm, mismatch 2.463 mm**: the mismatch is inside 5.000 **but `R75.2 -> U18.8` exceeds the 10.000 mm cap by 1.130 mm**, and analytic Kelvin is NOT reported as a pass while the routed result fails. Section 14 PASSES on the stack, both GND planes, D9, the 1.20 mm trunk, `BAT_PROTECTED_P` one island, the `U11.2` flare, `BAT_SENSE` (1.00 mm B.Cu, zero vias), `Q3_CS`, `Q3_GATE`, Q3.3 POFV, `LTC_SHDN`, `BAT_RAW` and `BAT_MID` - and **FAILS on Kelvin, U18 8/8, `LTC_GATE`, `LTC_OV` and `FAULT_N`**. **U19 NOT SEARCHED** (section 20); Phase A NOT run. B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002P - D-261 closeout. **DECISION STOP** (section 17). **The authoritative stackup was NOT changed**, so the PCB is byte-identical to `b803f93` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper layers, zero signal tracks, zero signal vias**. All five suites PASS. **D-261'S D9 LEVER WORKS:** a **0.600 mm** eastward relocation of D9 - **placement only**, same part, footprint, orientation, net, polarity and topology - frees a **+1.00 mm** rigid-cluster shift and opens an R75 rot-180 window of **x 4.225..4.400** where the **Kelvin mismatch reaches 0.000 mm** with both branches at 7.321 mm, the first time since 002I that the Kelvin spec has been analytically satisfiable. +0.20 and +0.40 free only cluster +0.75, so **+0.60 is the measured minimum**, and **`D9.1 -> U11.2` SHORTENS 55.344 -> 54.748 mm**. **`BAT_SENSE Q3.6 -> R75.1` - THE BLOCKER STANDING SINCE 002M - IS CLOSED** at 1.00 mm on B.Cu with zero vias, and on the best candidate (D9 +0.600, cluster +0.75, R75 (4.150, 63.500) rot 180) the probe returns **all nine targets true with U18 8/8, `LTC_OV` one component and `LTC_GATE` one component** - the first board on which all of those hold at once, with **`LTC_OV` closed without moving R77 or R78 at all**. **A CONSTRAINT THE EARLIER ARITHMETIC MISSED: the corridor has to fit the TRUNK, not just the pad** - a 1.50 mm track centred on R75.2 needs that pad's centre 1.250 mm from the edge, 0.063 mm more than the +0.75 window gives, which is what the extra D9 displacement buys. **SECTION 17'S EXACT NEW FIRST BLOCKER: `BAT_PROTECTED_P R75.2 -> D9.1` is rejected at 1.50 mm on `copper_edge_clearance 0.5000; actual 0.4125` and IS NEVER RETRIED AT D-249'S OWN 1.20 mm FLOOR** - `run()` stops the width ladder as soon as `connect_role` returns ok and the DRC gate runs afterwards, so a width that routes geometrically but fails the gate is abandoned instead of falling to the next rung; the 1.20 rung needs R75.x >= 4.063, which the +0.75 window satisfies. **Recorded as PR-49, not fixed mid-stop because it changes router behaviour board-wide.** **Second blocker: the ROUTED Kelvin detour** - analytic 7.378 / 7.267 becomes routed **18.764 / 7.886**, a routing outcome rather than a placement one. **The trade:** cluster **+1.00** gives the 0.000 mm Kelvin window and **costs three control pins** (U18 5/8); cluster **+0.75** keeps **U18 8/8 and all nine targets** but cannot host the 1.50 mm trunk. **SECTION 18'S SHUNT RESERVE IS NOT TRIGGERED - R75 FITS - and 002O's suggestion that a shorter shunt might be needed is WITHDRAWN.** **U19 NOT SEARCHED** (section 21); Phase A NOT run. B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002O - D-260 joint cluster closeout. **DECISION STOP. The authoritative stackup was NOT changed** (section 17 gates it on section 14), so the PCB is byte-identical to `fcacf0e` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper layers, zero signal tracks, zero signal vias**. All five suites PASS. **D-260'S RIGID-CLUSTER HYPOTHESIS IS CONFIRMED**: moving U18 together with R76..R83 as one rigid body **eliminates 002N's three control-lane clearance failures**. **But the Kelvin blocker is now CLOSED ARITHMETIC:** R75 at rot 0/180 needs a **7.75 mm** corridor and only **6.80 mm** exists between the board-edge clearance and the divider column - west limit `R75.x >= 4.075`, east limit at cluster +0.50 `R75.x < 3.925`, **an empty window** - and it first opens at **cluster +0.75 mm**, which is exactly where **D9 overlaps R77 by 0.170 mm**. **Only cluster +0.50 mm is legal**; beyond it D9 blocks R77 at +0.75 and +1.00 while TP17 and C58 appear only at +1.25, so **section 13's test-point scan answers clearly: the obstruction is D9, a functional diode in the protected high-current path, not a test point, and it would need to move 0.170 mm east.** **The other orientation was re-measured with the cluster moved: rot 90/270 bottoms out at 5.132 mm mismatch against a 5.000 limit** (002N measured 5.177 unmoved), and routed it gives **U18 4 of 8** because moving R75 east far enough puts the shunt under U18's escape corridor. **Both routes miss by less than two tenths of a millimetre.** **WHAT DID CLOSE: `LTC_OV R77.2 -> R78.1` routed 2.901 mm on B.Cu with ZERO vias**, without moving R77, and section 11's fallback lock is now enforced so 002N's 13.087 mm F.Cu excursion cannot be reported as a pass again. **Two tooling defects found:** a pose filter that checked courtyards against the outline only and proposed a pad 0.325 mm from the edge against 0.500 mm (every connection rejected, nothing routed - the edge rule now applies to pads), and a placement guard that fired on `270.0` versus KiCad's `-90.0`, the same pose (angles now compared modulo 360). **DECISIONS REQUIRED: (a) authorise a 0.170 mm eastward move of D9**, admitting the +0.75 mm shift and a ~0.10 mm mismatch - a protection-architecture call; **(b) or relax the mismatch to 5.132 mm**, noting that pose also costs four U18 control pins; **(c) or change the shunt** - R75's 5.925 mm pad pitch pins the rot 90/270 mismatch AND makes the rot 0/180 corridor 7.75 mm wide, so a shorter 15 mOhm part relieves both. **U19 NOT SEARCHED** (section 20); Phase A NOT run. B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002N - D-259 closeout: published stackup, R75/Kelvin, local LTC_OV. **FAIL at section 11. THE AUTHORITATIVE STACKUP WAS NOT CHANGED** - section 16 gates the lock on section 11 - so the PCB is byte-identical to `7ff0337` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper layers, zero signal tracks, zero signal vias**. All five suites PASS. **D-259(c) CLOSED:** the derived inner split of 002M is gone and `sixlayer.py` now authors the **published JLC06161H-7628** table with the regression asserting those dielectrics - 0.2104 outer, 0.4000 cores, **0.2028 central prepreg**. Listed materials total **1.5544 mm** (1.5744 with masks), and **that is not a discrepancy**: the board is a **NOMINAL 1.6 mm construction** whose finished thickness also carries plating, resin flow and press tolerance, so the regression now RECORDS the total and ASSERTS the published values instead of testing the sum against 1.6. **SECTION 18 CLOSED: the datum is 72.000 x 148.000 mm** - `GetBoardEdgesBoundingBox()` reads 72.100 x 148.100 because it measures to the OUTSIDE of the 0.100 mm Edge.Cuts stroke, which 002M had quoted as though it were the requirement; both figures are now reported and Edge.Cuts is untouched. **THE R75 MEASUREMENT THAT MATTERS: translating R75 was never going to fix the Kelvin mismatch** - `U18.8` and `U18.9` are at the **same y** and R75 is a **5.925 mm** shunt whose pads lie along y, so any north/south move changes both Kelvin lengths equally and the mismatch stays at nearly the shunt's own length; over a +/-8 mm box at 0.5 mm in four rotations **28 poses reached the Kelvin test, ALL rot 90/270, best mismatch 5.177 mm against a 5.000 limit.** Turning the shunt so its pads lie along x drops the mismatch below 1 mm, and **every rot 0/180 pose is blocked by the R80/R81/R82 courtyards - the part costing the Kelvin spec is the divider column, not R75.** With that column shifted **1.0 mm east (the measured minimum)** R75 gets 8 poses, best **(4.300, 63.500) rot 180 with mismatch 0.771 mm** - **but the combination does not hold**: the shift puts BAT_MAIN copper into the LTC4368 control lanes, three connections are rejected by `BAT_MAIN routed clearance 0.3000` at 0.2750 / 0.2778 / 0.2371 mm, and **U18 falls to 6 of 8**. **LTC_OV becomes ONE COMPONENT with a 0.354 mm R78 move** (`R77.2 -> R78.1` 2.26 -> 1.577 mm, span 8.577 mm, U18 still 8/8) - **but `U18.3 -> R77.2` routed 13.087 mm on F.Cu with 2 vias**, exactly the long generic fallback section 13 forbids on a high-impedance comparator input, so **section 9's secondary R77 lever is the next instrument and was not spent.** **A HARNESS CHANGE WAS MADE, MEASURED AND DELIBERATELY REVERTED:** raising wide-net PADS to the 0.300 mm class clearance looked correct and immediately sealed `U18.8` and `U18.9`, the two D-249-ruled Kelvin taps, both `NO_LEGAL_ESCAPE` - they route legally at 0.150 mm under the later, more specific pad-escape rule, so **over-applying a clearance is how a legal escape becomes NO_LEGAL_ESCAPE.** **Section 13's U18 reserve was NOT opened** - it is conditioned on both individual searches succeeding, and LTC_OV succeeds only in a form section 8 does not accept. Impedance register updated to the published inputs, every controlled net marked PENDING. **U19 NOT SEARCHED** (section 20); Phase A NOT run. B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002M - six-layer architecture, Q3 POFV, U18/R75 local closeout. **FAIL at section 14. THE AUTHORITATIVE STACKUP WAS NOT CHANGED** - section 16 gates the lock on section 14 - so the PCB is byte-identical to `bc1d436` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper layers, zero signal tracks, zero signal vias**, In1.Cu one filled island. All five suites PASS. **THE SIX-LAYER MIGRATION IS PROVEN ON SCRATCH:** 6 copper layers in order (F.Cu / In1.Cu / In2.Cu / In3.Cu / In4.Cu / B.Cu), explicit **JLC06161H-7628** stackup, **1.6028 mm**, **In1.Cu AND In4.Cu each ONE GND island** built from the same outline, no outer or inner-signal pours, outline 72.100 x 148.100 mm - and a **DRC histogram IDENTICAL to the four-layer baseline**. The In1 guard was EXTENDED, not weakened. **PR-47 IS CLOSED ON SCRATCH:** `Q3_CS Q3.3 -> Q3.1` routes **4.626 mm at 0.25 mm on In2.Cu** through a filled/capped **0.35/0.20 ordinary THROUGH via-in-pad** at `Q3.3` with **0.125 mm of pad copper remaining each side**; `Q3_CS` is **one component**, `LTC_GATE` is **one component across all six functional pads**, **U18 is 8/8**, and the gate drive goes from 002L's only option - a 15.991 mm F.Cu excursion - to **5.500 mm on B.Cu with ZERO vias**, with the premium process spent on **one pad** and no footprint or toe modified. **BUT SECTION 14 FAILS ON TWO NETS, AND IT IS THE SAME TRADE ONE REGION OVER:** `BAT_SENSE Q3.6 -> R75.1` is rejected by `BAT_MAIN routed clearance 0.3000 mm; actual 0.2400 mm` because the 1.00 mm trunk and the POFV copper want the same corridor and a wide net cannot be sent inward (section 2 keeps high-current copper on outer 1 oz), and `LTC_OV R77.2 -> R78.1` returns `NO_VIA_SITE`, **which is section 13's stop condition in substance**. **Six layers removed the Q3 conflict, which is what they were bought for**; what remains is a clearance contest over a few square millimetres, which is a placement question. **The U18 six-layer re-screen and the R75 lever were NOT run** - re-screening against a prefix that cannot close `BAT_SENSE` or `LTC_OV` would measure the wrong board, and 002K is the standing lesson on that. **THREE HARNESS DEFECTS, ALL ONE FAMILY** (adding layers to a router that had only ever seen two): the obstacle model saw two layers and now DERIVES its copper set from the board with a through via registering copper on all of them; `connect_hop` sited its via checking only `near` and `far`, which on six layers put a via onto another net's inner copper and DRC answered `shorting_items`; and `connect_hop` could only reach F.Cu, so the new capacity was unreachable - `far` now defaults to every routable layer except `near`, **and never an inner layer for a wide net**. **THE RULE CORRECTION, A SECOND TIME:** the D-257 escape corridors were emitting a 0.20 mm clearance floor that fired on pairs it never meant to govern - **a relaxation applied where nothing needed relaxing is a restriction** - so escape corridors now carry **via geometry only**. **PR-48 RE-VERIFIED on six layers.** **POFV fabrication note and IMPEDANCE IMPACT REGISTER** written: the via is **PLATED OVER FILLED VIA**, recorded as a process order because Gerbers alone do not force it, and **no impedance width is claimed unchanged** - the **NFC transmit arms** are flagged as the real electrical change. **HONEST LIMIT: the inner stackup distribution is DERIVED and must be confirmed against JLCPCB's published table before Gerbers are ordered.** **U19 NOT SEARCHED** (section 20); Phase A NOT run. B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002L - D-257 manufacturable escape, PR-47, PR-48. **DECISION STOP** (section 17: if Q3 requires via-in-pad, 002L is a decision stop and not a pass). **No authoritative copper; the PCB is byte-identical to `cb17269` (md5 `a908cedfa9f9410aab327d8bd55b9f45`) - zero signal tracks, zero signal vias, In1.Cu one filled island.** All five suites PASS. **PR-48 PROVEN:** a local `clearance (min 0.20mm)` conditioned on net AND bounded corridor resolves all three measured cases - **`U18.1` VIN 10.107 mm at 0.20 mm** (was `clearance 0.3000; actual 0.2500`), **`U14.2` 7.401 mm at 0.15 mm** (was 0.2347), **`U14.3` joined** (was 0.2350) - and `BAT_PROTECTED_P` becomes ONE island including `U11.2`, `U14.2`, `U14.3`, `TP15.1`, `U18.8`, at **minimum measured clearance 0.200 mm with no new DRC class**. **A CORRECTION IS RECORDED:** the first cut also covered `BAT_PROT_TAP_U18` and `BAT_SENSE_KELVIN`, already running legally at **0.150 mm**, so the 'relaxation' RAISED the floor on compliant copper and rejected every connection after it - **a relaxation applied where nothing needed relaxing is a restriction.** **D-257 PROVEN ON THE PREFERRED GEOMETRY: every D-256 escape is carried by the 0.35/0.20 ordinary through via** (LTC_GATE x4, LTC_SHDN x2) **and the 0.25/0.15 reserve was never needed**; no microvia, no blind or buried via. **U18 SEARCH - FIVE POSES SCREENED, NONE CLOSES:** the **authoritative** pose routes **8 of 8** but misses Kelvin (straight-line 2.440/8.265, **mismatch 5.825** against a 5.000 limit); the **002F ECO** pose has Kelvin 4.464/4.464/0.000 and routes **6 of 8**; C01/C02 5 of 8; C03 7 of 8. **MOST OF THE AUTHORITATIVE POSE'S KELVIN FAILURE IS ROUTING, NOT PLACEMENT** - it misses by **0.825 mm straight-line** and carries a further **4.948 mm of detour** on `R75.2 -> U18.8`; **the lever section 6 held back is R75**, fixed 'initially' and in the 1.5 A path, so it is surfaced rather than taken. **PR-47: ORDINARY VIAS ARE MEASURED IMPOSSIBLE.** Q3 is `SOIC-8_3.9x4.9mm_P1.27mm` - 1.270 mm pitch, 1.950 x 0.600 mm pads, **0.670 mm copper gap** - with `Q3_CS` on pins 1/3 and `LTC_GATE` on 2/4 sharing one B.Cu slot, and **`Q3.3` has NO LEGAL ESCAPE at 0.25, 0.20 OR 0.15 mm** (blocked by `Q3.2` x27, `Q3.4` x20); both D-257 geometries at all three widths return `NO_LEGAL_ESCAPE`, because **a via needs a landing site and a landing site has to be REACHED from the pad**. **Section 13 geometry check: a filled/capped through via-in-pad at 0.35/0.20 FITS, with 0.125 mm of pad copper each side** - feasible and premium, hence the stop. **Section 14 alternative recorded not taken: a Q3 toe extension >= 0.40 mm.** **SIX-LAYER ASSESSMENT TRIGGERED** (non-destructive, nothing applied): 1.6 mm retainable, **P1 mechanical evidence stays valid**, U18 relieved directly - **but it does NOT solve PR-47.** **PROCESS FIX:** `checks/placement_fingerprint.py` prints the guarded poses at the head of every screen and `AQROOT_EXPECT_PLACEMENT` makes it an assertion that **fails before routing**. Standing section 11 flag: `LTC_OV` reached F.Cu through the ordinary fallback and split `R78.1`. **U19 NOT SEARCHED** (section 16); Phase A NOT run. B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002K - D-256 answered: the layer exists, the via does not fit U18. **FAIL at section 9.** No authoritative copper. **The west margin IS short of layer capacity exactly as D-256 ruled - and at the 002F placement the two pins needing the extra layer CANNOT REACH A VIA**: `U18.10` had no reachable through-via site at 0.60 down to 0.25 mm, and `U18.7` had NO legal escape at 0.25/0.20/0.15 mm. On the authoritative placement the same strategy worked - LTC_GATE ONE ISLAND, U18 6/8 -> 7/8. **Three harness defects fixed (PR-45 reachable via sites, PR-46 honest hop reasons and an end to silent DRC-gate rejections, D-249 corridor areas spanning both outer layers).** previously **FBV2-CLOUD-001 - the harness becomes reproducible on a second machine. **PASS. INFRASTRUCTURE / TOOLING ONLY - NO PCB PROGRESS EARNED.** No schematic, no copper, no placement, no architecture; the authoritative PCB is byte-identical to `a1cc687` with **0 signal tracks and 0 signal vias**. **Every FBV2-P2 verdict from 002A to 002J was measured on ONE Windows workstation** - a single point of failure for the whole evidence chain, since a measurement only one machine can reproduce is a step back toward being *recorded* rather than *measured*. **13 active portability defects** found: four scripts carried that machine's disk as literals (`P:/New folder (2)/bin/kicad-cli.exe`, `P:/Vaults/ClaudeVault/AQROOT/...`, `"<KICAD>/bin/python.exe"`). **The dangerous one: `router_regression.py` HAD a `KICAD_CLI` override but its DEFAULT was the Windows path** - unset on Linux it produced a nonexistent tool, and because both DRC call sites use `subprocess.run(capture_output=True)` with no returncode check, "the DRC tool is absent" was indistinguishable from an I/O error **inside the script that gates authoritative copper** - the G1 class from 002A, one layer down. **New `checks/harness_paths.py` holds one policy each: kicad-cli = `KICAD_CLI` -> `shutil.which` -> documented Windows fallbacks (`os.name=='nt'` only) -> LOUD `SystemExit`, never a silent default; project dir = `AQROOT_BETA_V2_PROJECT` else derived from `__file__` (checks/ -> beta-v2/ -> hardware/ -> repo root), with no username, mount point, home directory or vault path in it; interpreter = `sys.executable`, always.** **Windows is a strict SUPERSET** - the old machine still resolves with zero configuration and Windows paths pass verbatim. **`.kicad_prl` REMOVED from fork equivalence**: per-user KiCad editor state, gitignored since before the fork, and `beta-dm` has none at all - **no fake `.prl` generated, none committed, `.gitignore` unweakened**. **`checks/requirements.txt` = `numpy>=1.24` and nothing else**; `pcbnew` deliberately excluded because it comes from KiCad, not pip. **KiCad 10's Ubuntu `PROPERTY_ENUM` assertion noise is NOT suppressed** - hiding it would hide the next real error; judged on exit status. **All five suites PASS on Ubuntu 24.04 / KiCad 10.0.5** (`p1_regression`, `router_regression` ALL CHECKS incl. G1-G7 + G8-A..F and also with `KICAD_CLI` unset, `dru_probe`, `netclass_probe`, `fork_equivalence`). **No PCB, schematic or rule file was touched to make a test pass.** B-34 REMAINS OPEN; D-256 still awaits the CTO; **FBV2-P2-002K NOT STARTED.** **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002J - the R80/R81 lever fails. **FAIL. Authoritative PCB byte-identical to `984423c`; placement ECO STILL NOT APPLIED.** Preflight all PASS. **A validated section 5 LOCAL SCREEN (`AQROOT_LOCAL=R80`, 19 connections) reproduces D-255 exactly in 471 s against ~2 h - 15x cheaper - because the copper boxing `U18.7` is the `LTC_SHDN` `U18.6 -> R80.2` run, inside the U18 pin field itself.** **Six R80 poses screened; `R80.1` and `D12.1` connected in EVERY one; NONE reached 8/8.** K6 alone closes both D-255 pins. **Two full Phase A runs are both WORSE than doing nothing: K6 20/29 (`Q3_CS` splits, which section 12 protects), K1 22/29 (`LTC_GATE` in FIVE islands).** **The 002I baseline of 24 of 29 remains the best measured result - across 002I and 002J one reordering and seven placements have ALL landed at or below it.** The section 10 via reserve is NOT triggered (`U18.7` is the easy pin); **the section 10 STOP condition IS met - `LTC_GATE` degrades under every R80/R81 move.** U19 search NOT performed. **PR-44 CLOSED: `apply_areas` called `GetClass()` on track objects freed by a revert - a deterministic SIGSEGV that killed two full Phase A runs; UUIDs are now resolved against the board.** **CTO DECISION REQUIRED (D-256): the margin is short of LAYERS, not lanes.** B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002I - PR-43 answered. **FAIL on section 5 Case D: a protected path regressed.** The authoritative PCB is byte-identical to `984423c` and the placement ECO is STILL NOT APPLIED. Preflight all PASS. **PR-43 WORKS AND NEEDS NO PLACEMENT CHANGE: `BAT_RAW` reaches 11 of 12 pads in ONE island - `R80.1` and `D12.1` both CONNECTED - and `LTC_SHDN` closes too.** **But U18 falls 8 of 8 -> 6 of 8** (`U18.7` NO_LEGAL_ESCAPE, `U18.10` NO_PATH), both named in section 9. **The copper boxing those pads is NOT `BAT_RAW`**: `LTC_SHDN` and `BAT_PROTECTED_P` at 0.500 mm from `U18.7`, `BAT_SENSE` at 0.500 mm from `U18.10`. PR-43 unblocked `LTC_SHDN`, whose route then took `U18.7`'s lane. **So the west margin is OVERSUBSCRIBED - capacity, not ordering - both orderings score 24 of 29 and reordering only moves the casualty.** PR-43 is **flagged, not adopted** (`AQROOT_PR43=1`); the default keeps U18 at 8 of 8. **Improved: Kelvin 4.464/4.464 mm, mismatch 0.000 mm** (was 2.454); VIN 1.752 mm. Held: `BAT_PROTECTED_P` one island / 0 vias / 1.50 mm, `Q3_CS` and `Q2_CS` 0 vias, `U11.2` neck 0.20 mm no via, `U14`+`TP15`, zero out-of-scope copper, DRC classes unchanged. **U19 search NOT performed (section 6 needs Case C).** **CTO DECISION REQUIRED - see D-255.** B-34 REMAINS OPEN. **PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002G / 002H - routing truth and the BAT_RAW contention. **FAIL. The authoritative PCB is byte-identical to `984423c` (md5 `a908cedfa9f9410aab327d8bd55b9f45`) - zero signal tracks, zero signal vias - and the placement ECO is STILL NOT APPLIED.** Rollback tag `beta-v2-p2-battery-pre-authoritative` at `984423c`, pushed. **PR-39 CLOSED: router success now means the REQUESTED pads are one connected component**; a retarget that leaves the named pad isolated is reverted and does not count, and the journal records requested vs actual endpoints. Six regression cases **G8-A..G8-F all pass**. `checks/net_ledger.py` makes connectivity the primary truth. **PR-40 IMPLEMENTED: qualification is the FULL PREFIX** - bare-board escape, simultaneous stubs and reduced-prefix probes have each been wrong at least once; cost is ~40 min per candidate. **PR-41 CLOSED AND VALIDATED** - the closure stage gave every `BAT_RAW` pad the trunk ladder because `BAT_RAW` is WIDE, so the 0.20 mm divider chain was asked for 0.60 mm; afterwards **zero NO_LEGAL_ESCAPE board-wide**, but not sufficient. **PR-42 CLOSED (my own defect): a stray `break` made all eight 'joint' candidates share ONE R80/R81 pose**; fixed, it yields six distinct R80 poses. **MEASURED, REVERSING PART OF PR-34: a bare-board flood shows BOTH `BAT_RAW` bridges reach the battery node at 0.20 mm - the corridor EXISTS, the failure is CONTENTION, and no R80 pose is required.** **PR-43 APPLIED, UNPROVEN: schedule by corridor scarcity, not net role** - the 21.5 mm and 45.5 mm divider-chain bridges now route with the chain instead of after U18's pin field; its Phase A was killed before reaching them. **Phase A not passed, Phase B not run, no manifest. `U19` still 5 of 7 on the full prefix. B-34 REMAINS OPEN. PCB routing stays 0 %; overall stays 74 %.** previously **FBV2-P2-002F RESUMED - three harness defects fixed, 24 of 29
nets. **STILL FAIL; board byte-identical to `24f6611`.** Phase A run 8: **71 connections, ratsnest
781 -> 708 (-73)**, DRC identical to baseline, **24 of 29 in-scope nets single components** (was
23). **PR-37** (closure ignored D-249's per-pad widths and asked a 0.7 x 0.3 mm pad for 1.20 mm)
closed the MAX17048 island and PR-35; **PR-38** (ordering measured only the first-named pad of an
MST edge) closed `REF_POL`. **PR-39 OPEN and it is the most consequential: a connection can report
a length and appear in the journal having been built to a DIFFERENT endpoint** - `R79.1 -> R80.1`
reports 5.276 mm across a 12.030 mm gap with ZERO track endpoints in the pad. Section 14 must be
judged on connectivity, not the routed count. **CORRECTION: an earlier note that U19 need not move
is withdrawn** - run 8 moved the casualty from `U19.2`/`U19.3` to `U19.3`/`U19.8`, which is PR-25's
signature; PR-34 stands. **PCB routing stays 0 %; overall stays 74 %**; previously **FBV2-P2-002F - **FBV2-P2-002F - battery-block placement ECO and routeability
proof. **FAIL: Phase A did not complete, so Phase B never ran; the board is byte-identical to
`24f6611` and THE PLACEMENT ECO IS NOT APPLIED TO IT** (section 23 forbids committing an unproven
placement). **The placement question PR-25 asked is ANSWERED:** U18 rotates 90 -> 180 to
**(8.000, 65.250)** from a measured search of 13 284 poses, and **escapes 8 of 8 signal pins and
ROUTES 8 of 8** against 6 of 8 at 002E. **R75 Kelvin mismatch 20.620 -> 2.454 mm**, **`U18.1` VIN
32.204 -> 1.850 mm**, **MAX17048 branch 31.228 -> 6.387 mm with U14 unmoved**, **worst megohm
dead-cell node 64.01 -> 18.43 mm**, and **`Q3_CS` closes with ZERO vias** - section 5's authorised
layer drop was measured and declined. `LTC_GATE`, left in two pieces at 002E, is now ONE connected
component. **70 connections on one scratch board, ratsnest 781 -> 709 (-72), DRC identical to the
baseline at every step, zero out-of-scope copper, 23 of 29 in-scope nets single components.**
**Fails on section 14's no-partial-pass rule:** four stranded pads (`R80.1`, `U19.2`, `U19.3`) and
the `{TP15, U14.2, U14.3}` MAX17048 island remain (PR-34). Four new general harness rulings
(PR-30..PR-33) and one lesson - **an escape proof measures a stub, a connection is a route**.
**PCB routing stays 0 %; overall stays 74 %**; previously **FBV2-P2-002E - battery / protection
routing resumed from the `e09eb35` checkpoint. **FAIL: Phase A did not complete, so Phase B never
ran and the board is byte-identical to `e09eb35`.** 60 connections coexisting DRC-clean on scratch,
ratsnest 781 -> 718 (-63), the whole high-current path closed with the trunk at its 1.50 mm target,
zero vias, and the dead-cell network routed for the first time. Stopped with 15 open connections,
nine of them `NO_LEGAL_ESCAPE` at 0 s - a placement finding (PR-25), not a router finding. Five
harness defects fixed including a segmentation fault. **PCB routing stays 0 %; overall stays 74 %**;
previously **FBV2-P2-002C — battery path-role rules
and the first authoritative routing attempt. **FAIL: Phase A stopped at `LTC_GATE` `Q2.2 → TP17.1`, so Phase B
never ran and the board is byte-identical to `a52977e`.** Delivered **D-249**, the path-role
width ruling, and 27 coexisting DRC-clean connections on scratch. **PCB routing stays 0 %;
overall stays 74 %**; previously **FBV2-P2-002B — routing harness qualification.
**HARNESS QUALIFICATION = PASS.** All three router defects fixed and proved fixed on real geometry;
the two remaining cases are a **proved land-pattern / rule conflict** on five fine-pitch pads,
surfaced for a CTO ruling. **No copper committed; the board is byte-identical to `8b9efba`.**
**PCB routing stays 0 %; overall stays 74 %**; previously **FBV2-P2-002A — battery / protection routing attempt.
**FAIL: the block is NOT routed and nothing was committed as copper.** Delivered D-245 and a
working obstacle-aware router with per-net DRC gating. **PCB routing stays 0 %; overall stays
74 %**; previously **FBV2-P2-001 — power-routing attempt. **FAIL: the power tree is
NOT routed and the attempt was reverted.** Delivered the In1.Cu GND plane and the PM-2 support /
test-point placement corrections. **PCB routing stays 0 %; overall stays 74 %**; previously
**FBV2-EXP-002 — standard expansion interface implemented and
the combined re-floorplan executed. **FBV2-P1 RE-ISSUED = PASS, FBV2-P2 ENTRY = PASS, PM-1/PM-2/PM-3
and PT-1 CLOSED. NO PROGRESS EARNED — P1 was re-earned, not newly earned; overall stays 74%**;
previously **FBV2-EXP-001 — expansion ecosystem compatibility and
pre-routing architecture audit. AUDIT = PASS; **AUDIT ONLY, NO AUTHORITATIVE HARDWARE CHANGE, NO
PROGRESS EARNED: overall stays 74%**; previously **FBV2-P2-000 — P2 pre-routing entry gate and routing strategy
freeze. **FBV2-P2 ENTRY = FAIL** on one criterion of thirteen; **NO PROGRESS EARNED: overall stays
74%**, FBV2-P1 = PASS unchanged**; previously **FBV2-P1-002 — P1 closeout; **FBV2-P1 PASSES**; overall 68% → 74%**; previously **FBV2-P1-001 — enclosure-driven floorplan built; **FBV2-P1 DOES NOT PASS** on the 915 MHz pigtail reach; overall stays 68%**; previously FBV2-MECH-002 — pre-floorplan authority reconciliation and final
procurement sign-offs. NO PROGRESS EARNED: overall stays 68%, FBV2-S2 = PASS unchanged**; previously
FBV2-S2-002 — S2 release closeout, FBV2-S2 = PASS)
Repository HEAD at last update: `f8c931b` (FBV2-P2-002R; the authoritative PCB is NOW SIX LAYERS - architecture only, still zero signal tracks and zero signal vias)

---

## How percentages work here

**A percentage increases only when a gate passes.** It does not increase because
work was done, because a document was written, or because something looks close
to finished. A gate passes when its exit criterion is met and that fact is
recorded in this file with a date.

This rule exists because the programme has already been burned once by
progress that was asserted rather than measured: the enclosure reconciliation
that Field Slate v3 required was recorded as done in a commit title
("enclosure-driven PCB floorplan") while it had not happened. Percentages here
are gate-backed or they are not written.

Corollary: percentages can go **down** if a gate is later found not to have been
met.

---

## Beta-DM (preserved fallback / manufacturing baseline)

| item | status |
|---|---|
| PCB / design | **100%** |
| Fabrication | **PAUSED BEFORE PAYMENT** |
| Overall Beta-DM | **~81%** |
| Role | Preserved fallback and manufacturing baseline |

Beta-DM is not cancelled. It is the programme's insurance policy: a
design-side-complete board with DRC 0 errors and a generated fabrication package
that can be built if Full Beta v2 stalls. It must remain preserved
(CTO decision D-005).

---

## Full Beta v2

| phase | status |
|---|---|
| Requirements / product direction | **100%** |
| Pre-design audit | **100%** |
| Architecture freeze | **IN PROGRESS** |
| Schematic migration | **100%** — **all nine sheets landed. `fork_equivalence.py`'s "still Beta-DM" list is EMPTY.** |
| PCB placement | **100%** — **FBV2-P1 RE-ISSUED AND RE-PASSED on the new 72 × 148 outline (FBV2-EXP-002)** |
| PCB routing | **0%** — entry gate PASS; the router is **QUALIFIED** (FBV2-P2-002B) and the battery **path-role width ruling D-249 is settled** (FBV2-P2-002C). **Four routing attempts, none committed.** The best (FBV2-P2-002E) routed **60 of the block's connections coexisting DRC-clean on scratch, ratsnest 781 → 718** — the whole high-current path `J4→F1→Q2→Q3→R75→D9→U11.2` with the **`BAT_PROTECTED_P` trunk at its 1.50 mm TARGET on B.Cu, zero vias**, both R75 Kelvin branches, the U11.2 flare, the MAX17048 taps and **the dead-cell / recovery network for the first time**. It stopped with **15 open connections; nine failed `NO_LEGAL_ESCAPE` at 0 s**, which is a **placement** limit (**PR-25**: U18 escapes 6 of its 8 signal pins, 7 at best, through one ~2.2 mm corridor) rather than a routing one. The **In1.Cu GND plane is valid (1 island, 93.3 %)**; the authoritative board still has **zero tracks and zero signal vias** |
| DFM / release | **0%** |
| Physical validation | **0%** |

### Overall Full Beta v2: **~74%**

#### How 74% was reached — FBV2-P1-002

**Raised 68% → 74% by FBV2-P1-002, and FBV2-P1 = PASS** — the third of the twelve gates to pass,
and the first that is about physical geometry rather than about the schematic. The increment
matches the established method: FBV2-S1 awarded +7 and FBV2-S2 awarded +6 on the same twelve-gate
table.

**What the gate actually proves.** There is now a complete, collision-free, enclosure-driven
placement of all 321 schematic components on a 70 × 148 mm outline, and **every mechanical
relationship in it is re-derived from the board file by a committed script**
(`hardware/beta-v2/checks/p1_regression.py`) rather than asserted. The 915 MHz feed — the one
criterion that failed at FBV2-P1-001 — closes on a **measured 138.48 mm** routed path to an exact,
in-stock, orderable assembly with 46.52 mm of spare.

**That is not the same as "ready to route."** No track, via or pour exists; 499 connections are
unrouted, which is the correct P1 state. `.kicad_dru` still references E5/E6 rule areas the P1
rebuild deleted, and those must be re-created or retired before routing starts — a P2 entry
condition, recorded as P2-O5. **— CLOSED 2026-08-24 at FBV2-P2-000 (D-233), and it was 39 areas
and 22 inert rules, not just the E6 pockets.**

**One item is escalated and does not fail the gate:** the outline yields **two** legal
through-board M2 positions, not the three the closeout task assumed. Structural support is
completed by enclosure edge-capture rails and four reserved rear rib pads, which need no PCB holes.
A third screw would need a narrower battery, a narrower display, the SMA off the top-left, or an M2
with ≈ 1.4 mm of board to the edge — ~~**all CTO calls, none taken**~~ (D-226). **— CLOSED 2026-08-24 by D-232: two M2 is ACCEPTABLE, all four routes to a third are DECLINED, and retention is locked as a four-element architecture.**

### FBV2-EXP-001 — expansion ecosystem audit: **PASS.** No percentage earned.

**Held at 74%.** FBV2-EXP-001 is an audit and changed no authoritative hardware: the PCB blob is
byte-identical to `HEAD`, no sheet was opened, `J5` is unchanged, no Qwiic connector exists, `BOOT`
and `POWER` have not moved and no PM part moved.

**The product intent is achievable and the electronics need no architectural change — but the
interface does not fit the current floorplan, and the shortfall is paid in battery width.** A
right-angle through-hole socket puts its solder tails **6.5–6.9 mm inboard of its own mating face**,
so for the face to reach the right wall the tail row lands at x ≈ 63.5, **inside the battery
envelope**, where `BATTERY_SHADOW` forbids any through-hole lead. **Measured requirement:
(board right edge − battery right edge) ≥ 7.83 mm. Today it is 4.00 mm. Shortfall 3.83 mm.** Above
the battery the right wall offers only **41.00 mm** against the 1 × 24's **61.47 mm** body; the
largest socket that fits there is a 1 × 15, and that leaves nothing for Qwiic or the power switch.
Every other edge was tested and rejected — left is the 433 flex and the mandatory coax channel,
bottom is USB-C / microSD / both radios, top is the IR pair and the SMA.

**Two 1 × 12 sockets are rejected on geometry, not preference.** Samtec and Sullins both build a
2.54 mm body **N × 2.54 + 0.51 mm** long, so two butted bodies place their end contacts **3.050 mm
apart against a 2.540 mm pitch — a 0.510 mm interference.** They cannot form a continuous 24-position
grid, they need **5.59 mm MORE** wall length than the single 1 × 24, and they add a mis-plug mode the
1 × 24 does not have.

**Recommendation: one `SSQ-124-02-G-S-RA` (Samtec — the same manufacturer as the present `J5`) plus
one `SM04B-SRSS-TB` Qwiic connector, CONDITIONAL on two owner rulings**: **E-1** PCB 70 → 72 mm
(already the documented `FBV2_PCB_MAX_MM`; the 80 × 160 × 23 shell is unchanged) and **E-2** battery
60 → 57 mm wide, ≈ **−5 % capacity**. **If E-2 is declined the 24-line side header cannot be
delivered in this enclosure and `J5` stays as it is.**

**Three things were confirmed rather than assumed.** **(1)** Qwiic needs **no new components**: it
attaches at `EXT_SCL`/`EXT_SDA`, downstream of the 22 Ω resistors and at `D2`'s clamp, inheriting the
`TCA4307`, the 1.5 k pull-ups, the series resistance and the TVS; power is `ACC_3V3_SW` because
`U16`'s own VCC already is. **(2)** A **Manual / Bench power mode needs NO hardware change for either
rail** — `ACC_DETECT_N` reaches nothing but an expander input, so detect gating is entirely firmware
policy, while ILIM, reverse-current blocking, thermal shutdown and `FLT` stay in hardware.
**(3)** `SW1` **BOOT is SMD** and a measured **11.04 mm** bottom-edge window exists between the
microSD shell and the USB-C receptacle, with a **14 mm** free enclosure span for the tool hole — while
**lower-left BOOT is rejected on RF**, because that wall *is* the 433 flex region and the mandatory
915 coax channel.

**PM-2 and the new header want the same corner.** PM-2's fix is to consolidate the battery-protection
block at the battery-entry corner — exactly where the 1 × 24 now goes. **A combined re-floorplan
sequence is recommended so the connector change, PM-1, PM-2, PM-3 and PT-1 are solved once.** The
outline change invalidates the current FBV2-P1 PASS, so **FBV2-P1 would have to be re-issued.**

New: [`architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md`](architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md),
[`audits/2026-08-24-expansion-compatibility-audit.md`](audits/2026-08-24-expansion-compatibility-audit.md).
**D-081 / D-083 / D-093 / D-097 remain in force; supersession is marked PENDING CTO / OWNER RULING.**

### FBV2-EXP-002 — expansion interface built and the combined re-floorplan executed

**Held at 74%.** **FBV2-P1 was RE-ISSUED and PASSES; FBV2-P2 ENTRY was re-run and PASSES.** Neither
earns a percentage: the outline, the battery and `J5` all changed, so the P1 gate had to be re-run
in full — but P1 was **re-earned, not newly earned**, and the gate-backed method does not pay twice
for one gate. P2 entry earns none by its own terms.

**The battery gate ran first, and it changed the story.** Before any authoritative file was touched,
the 57 × 75 × 8 mm envelope was checked against real purchasable cells: **PKCELL `LP785060`
(7.3 × 50 × 60 mm, 2500 mAh typ, PCM fitted, JST-PH lead)** and **`LP755070` (7.5 × 50 × 70 mm,
**3000 mAh min**, PCM fitted, 500 cycles to 80%)** — both from manufacturer datasheets, neither a
marketplace mystery cell. **The predicted −5% capacity penalty does not materialise: both candidates
are 50 mm wide, so the 57 mm limit does not bind either of them, and `LP755070` sits at the TOP of
D-071's 2500–3000 mAh target.** The envelope was always larger than the cells that fill it.

**`J5` is now a Samtec `SSQ-124-02-G-S-RA` 1 × 24 2.54 mm female right-angle socket** — same
manufacturer as the part it replaces — with **`J8`, a `JST SM04B-SRSS-TB` Qwiic / STEMMA QT
connector, added for zero components** on the protected external I²C node. **All 24 electrical
functions are retained and not one protection part was removed.**

**ORDER-B is safe under 180° reversal by construction**, which is why it supersedes ORDER-A: a full
accessory inserted backwards maps 5V↔5V, GND↔GND, 3V3↔3V3 and 3.3 V logic to 3.3 V logic on every
remaining contact — **power-to-signal maps under reversal: ZERO**, proved pin by pin from the
netlist. The one-position slip stays physically impossible: a 60.96 mm male body in a closed-end
62.5 mm recess leaves **1.54 mm of play against a 2.54 mm pitch**, and **D-097's asymmetric key is
no longer needed.**

**The board grew SYMMETRICALLY, 70 → 72 mm**, so every part shifted +1.0 mm in X and every
part-to-part relationship is preserved; only the edge margins moved, to **1.5 mm on both sides —
the rule met exactly, with nothing to spare.** The enclosure is untouched. `ANT433_REGION` had to be
**re-derived rather than shifted**: its old 2.2 mm reservation does not fit a 1.5 mm gap and never
described anything real, since the flex is 0.28 mm thick and bonded flat to the wall.

> **PM-1, PM-2, PM-3 AND PT-1 ARE ALL CLOSED.** Converter IC-to-inductor spans fall to
> **4.80 / 4.34 / 3.86 / 3.79 mm** from 12.96 / 28.56 / 30.50 / **45.90 mm**, and each is now a
> complete power cell rather than an inductor moved next to an IC — `D8`, which sat **45.7 mm from
> its own inductor**, is now 3.56 mm from `U17`. The 1.5 A protection path is **30.86 mm, from
> 116.7 mm**, as one monotonic column, with the Kelvin pair at 6.60 mm and **no topology change:
> D-049 is untouched**. The NFC arms are mirrored at **Δx = 0.000 mm and arm-length Δ = 0.000 mm**.
> `U11` is out of the battery shadow. **B-34 improves by ≈ 53 mW at 1.5 A but does NOT close** — its
> 0.70 W is dominated by the BATFET, not by copper, and that is said rather than glossed.

**`BOOT` moved to the bottom band on the front face**; **lower-left was rejected on RF**, because
that wall *is* the 433 flex region and the mandatory coax channel. **POWER stays on the right wall.**
**Retention is still two M2** — widening the board did not buy a third and none was chased.

**DRC 26 → 1** (the `MK1` artefact accepted at D-227, still not suppressed); **ERC 0 errors / 27
warnings, histogram identical; 499 unrouted; ZERO tracks, ZERO signal vias, ZERO electrical pours.**

New: [`audits/2026-08-24-expansion-and-refloorplan-implementation.md`](audits/2026-08-24-expansion-and-refloorplan-implementation.md).

### FBV2-P2-000 — pre-routing entry gate: **FAIL.** No percentage earned.

**Held at 74%.** FBV2-P2-000 is an entry gate and earns no progress by its own terms. It closed
every routing precondition except one — and the one it did not close is the one it existed to find.

**The rule set was not merely stale; 22 of 71 rules could never fire.** `.kicad_dru` referenced
**39 rule areas and the board contained none of them.** P2-O5 had recorded this as *"E5/E6 rule
areas"*; measured, it was **every RF-band rule, every E5/E4 corridor rule, the header reservation,
the E2 button escapes and the ESP32 antenna rule as well.** KiCad's `intersectsArea()` returns
**false** for an unknown name — no warning, no error — so a rule that can never fire is
indistinguishable from a rule being satisfied. The set is rebuilt to **64 live rules** with a
written retirement register, and **`checks/dru_probe.py` now fails the build if any reference stops
resolving** (D-233).

**The netclass table had been lying since the fork.** The `BAT_MAIN` pattern was the root-sheet
path `/BAT_PROTECTED_P` while every v2 power net lives under `/01_POWER_TREE/`. **It matched
nothing, so the highest-current net on the board — 1.5 A sustained — was routing on the 0.20 mm
Default class**, and `BAT_RAW`, `BAT_MID` and `BAT_SENSE` were in no class at all. `NFC_5V_PA`
captured **no net whatsoever**. `ACC_5V_LX`, a 1.2 MHz boost switch node, had **never** been in
`SWITCH_NODE`. **14 classes → 18, 62 patterns → 57, and every surviving pattern now matches at
least one net** (D-234).

**Retention is LOCKED and D-226's escalation is closed. Two M2 is acceptable** — no component
moved, no battery reduced, no display moved, no SMA relocated — with retention completed by
moulded edge-capture rails, **four** rear non-metallic support ribs, the two screws, and the `J5`
backing boss carrying its ≈ 33 N insertion load into the enclosure rather than into solder joints
(D-232).

> **WHAT FAILS THE GATE — three electrically required placement moves, none fixable by routing
> (D-236).** **PM-1:** all four switching converters have their inductor **12.96–45.90 mm** from
> their own IC — the backlight's `L3 → D8 → C44` boost loop is **≈ 76 mm around**, switching to
> **39 V** on an open-LED fault, 13 mm from the microphone. **PM-2:** the single-fault
> battery-protection block is dispersed across three clusters over **96 mm**, with 2.2–3.65 MΩ
> trip-point nodes and a **≈ 20 µA charge-pump gate node spanning 95.6 mm** past four converters.
> **PM-3:** the two NFC matching arms differ by **10 mm before a track is drawn**, with `L5` and
> `L6` on opposite sides of `U9`. **All three are new; none existed in Beta-DM to be carried
> forward.** FBV2-P1 verified every *mechanical* relationship by script — nobody had yet looked at
> these blocks *electrically*.

**Everything else is closed and written down.** Stackup retained and layer roles now enforced by
rule; one solid In1 with a single authorised void; USB confirmed as Full Speed, ≈ 40 mm, F.Cu only,
**zero vias, no length matching**; SPI-A **63 % shorter** and SPI-B **21 % shorter** than the
Beta-DM versions that were accepted, so neither gets damping; internal I²C given a **derived
C_bus ≤ 161 pF budget**; and the community-port escape measured as **10 crossings needed against
22 available on one layer** — no nudge required. **DRC 47 → 26. ERC unchanged at 0 errors / 27
warnings. 499 unrouted, ZERO tracks, ZERO vias, ZERO pours** (D-235).

New: [`pcb/FBV2_P2_ROUTING_PLAN.md`](pcb/FBV2_P2_ROUTING_PLAN.md),
[`pcb/FBV2_P2_NETCLASS_LEDGER.csv`](pcb/FBV2_P2_NETCLASS_LEDGER.csv),
[`audits/2026-08-24-p2-entry-audit.md`](audits/2026-08-24-p2-entry-audit.md).

<details>
<summary>Superseded — the 68% assessment as written at FBV2-S2-002 and held through FBV2-P1-001</summary>

### Overall Full Beta v2: **~68%**

**Raised 62% → 68% by FBV2-S2-002, and FBV2-S2 = PASS** — the second of the twelve gates to
pass. **B-03, B-63, B-70, B-54, B-71 and O-8 all close.** The design is now **fabrication-release
ready at schematic level**: every footprint is manufacturer-drawing verified, every one of the 46
MPNs has an explicit first-five route to the board, and every DNP part carries a recorded reason.

**That is not the same as "ready to fabricate."** No PCB placement or routing exists, and the
NFC matching network still requires bench tuning at first article — which the CTO ruling is
explicit does not fail this gate.

</details>

<details>
<summary>Superseded — the 62% assessment as written at FBV2-S2-001</summary>

**HELD at 62% by FBV2-S2-001. FBV2-S2 = FAIL on two of fourteen exit criteria, so no
percentage was awarded.** A percentage rises when a gate passes, and this one did not.

</details>

**The audit earned its keep on the first thing it looked at.** `U9` **ST25R3916-AQET** and its
twelve mandatory supply-decoupling capacitors were still marked **`DNP`**, against **D-035** and
**D-055**, while the 27.12 MHz crystal, the complete matching network, the antenna connector and
the SPI wiring around them were all **FITTED**. **The first five boards would have carried a
finished 13.56 MHz front end with no NFC chip on it.** All thirteen parts are now FIT (D-192).
**That is the seventh consecutive sheet with a load-bearing inherited `DNP`, and the one that hid
longest** — sheet 04's own migration was about the antenna, so nobody re-read the population state
of the IC underneath.

**`D-077`'s display second source does not exist.** Both Hirose land patterns were read: FH69 is
**7.38 mm** deep with a 0.30 × 1.23 signal land and **top-and-bottom two-point contact**; FH52E is
**4.6 mm** deep, **bottom contact only**, and its own catalogue says its pattern is interchangeable
with the **FH12**. **They cannot share pads. The drop-in claim is struck** and `J1` is confirmed as
manual assembly (D-194).

**Two more carried numbers were corrected:** the accessory boost settle delay was derived against
the datasheet's 10 µF condition when `C65`/`C66` give ≈ 20 µF effective at 5 V bias, so the real
margin was 3.5× and not 7× — **raised to ≥ 10 ms** (D-198); and **`R68`, a 0 Ω DNP with no note at
all, turned out to be a bypass across `SW9`** that would wire the unit permanently ON and defeat
the only way to power down a hung board (D-199).

**P-14 resolved:** the MAX17048 **stays on `BAT_PROTECTED_P`** — it was never on `BAT_RAW`, and
moving it to the LTC4368's precision sense node would trade a ≤ 2.6 % SOC error for a differential
capacitance across the current-sense resistor. **Safety outranks SOC accuracy** (D-193).

**Nine stale register entries were closed on evidence** — P-01, P-04, B-45, B-46, B-47, B-49,
B-51, B-53, B-68 — and **three new items opened**: B-70, B-71 and O-8.

**What fails the gate: B-03** — 15 of 28 critical footprints are drawing-verified with a citation,
**eight are not** — and **B-71**, only 7 of 46 unique MPNs carry an LCSC code, so the assembly
classification cannot be produced. **Neither blocks PCB placement; both block fabrication
release.**

**ERC 27 / 0 errors / 27, unchanged. 0 duplicate references, 0 unresolved footprint references,
0 missing MPNs on actives or connectors, 0 orphan nets, 0 `*_TBD`, 0 unexplained DNP, and 0
same-text local labels split across sheets.** PCB untouched and still bit-identical to Beta-DM.

<details>
<summary>Superseded — the ~62% assessment as written at FBV2-S1-009</summary>


**Raised 55% → 62% by FBV2-S1-009, and FBV2-S1 = PASS — the first twelve-gate
entry to pass since FBV2-A2 on 2026-08-22.** The task gate
**FBV2-S1-COMMUNITY = PASS** (2026-08-23).

> **FBV2-S1 = PASS means SCHEMATIC MIGRATION COMPLETE. It does NOT mean
> fabrication ready.** No placement, no routing, no outline, no DFM, no
> mechanical CAD and no physical validation exist. See §"What FBV2-S1 does not
> mean" in
> [`audits/2026-08-23-s1-schematic-migration-closeout.md`](audits/2026-08-23-s1-schematic-migration-closeout.md).

**ERC 42 / 1 / 41 → 27 / 0 / 27. The design has ZERO ERC errors for the first
time in the programme.** 321 components, 0 duplicate references, 0 without a
footprint, 224 nets, 0 `*_TBD`. `fork_equivalence.py` PASS, `netclass_probe.py`
PASS, PCB still bit-identical to Beta-DM.

**Three CTO rulings were recorded before the work started.** **O-6 RATIFIED** —
`U23` and the front RGB are locked architecture and **B-37 is retired**, with 37
of 48 expander pins used and eleven free. **O-4 APPROVED** — `U16` becomes TI
`TCA4307DGKR`, fitted, replacing a DNP TCA9517A. **P-18 CLOSED with no mux** —
the TCA4307 solves *electrical* fault isolation and the address registry solves
*address* allocation.

**Sheet 09 had to be rebuilt, and it was hiding two serious defects.** `J5`
contact 1 carried **permanent raw `+3V3`**, against D-057. And **the community
port had no power at all**: `01:ACC_3V3_SW`, the real switched rail at `U20`, and
`09:ACC_3V3_SW`, fed by a **second, DNP TPS22918** nobody had noticed, were
**different nets**; `01:ACC_5V_SW` reached nothing outside sheet 01.

**The sixth consecutive migrated sheet carried a load-bearing inherited `DNP`** —
`U16`, `R49`, `R50` and six TVS arrays. The pattern recorded at FBV2-S1-007 held
to the last sheet without a single exception.

**Two numbers that had been carried were wrong and are now derived.** The
inherited external I²C pull-ups were **4.7 kΩ**, which gives **796 ns against a
300 ns fast-mode budget** at a 200 pF external bus — they could never have worked
at 400 kHz. They are now **1.5 kΩ = 254 ns**. And the 3.3 V `R_ILIM` was
re-derived against a budget that has grown by the IR transmitter and the RGB:
the accessory-short case moved from 86 % to **89 % of the TPS63020's 2 A**, so
1.5 kΩ still holds — but it was checked, not copied.

</details>

**Eight of nine schematic sheets are migrated. Only sheet `09` remains.**

**The task was interrupted by a session limit and resumed rather than restarted.**
All of its work existed as uncommitted working-tree change; it was inspected,
classified and finished. The interrupted session had converted both expanders
properly, deleted HOME, landed `TOUCH_INT_N` and `SX1262_DIO1`, selected and
verified the RGB part — and had written an honest note into the schematic saying
the pin budget did not close. **That diagnosis was correct.**

**35 committed signals against 32 expander pins, and every escape closed.** There
is **zero free native GPIO** (B-10; GPIO35/36/37 are the octal PSRAM), which makes
the brief's own WS2812 escape **impossible** — a smart LED needs RMT on a native
pin. `RESERVED_SPARE` is mandated by D-094, the ten XGPIO are locked by D-082, and
an LED driver IC would be a new part family for one indicator. **`U23`, a third
`PCAL9535APW,118` at `0x22`, closes it** with no new MPN, no new footprint, no new
driver and no new rail — and **retires B-37** with 12 spare I/O, the first slack
this programme has had. **Raised as O-6 for ratification.**

**Core, community and safety functions were placed before the RGB by
construction.** `U23` carries the status light and the reserved spare and nothing
else, so declining O-6 costs the light and **not one other function**.

**`RESERVED_SPARE` did not exist before this task.** D-094 had required it since
2026-08-23 and no sheet had implemented it.

**The fifth consecutive migrated sheet did NOT repeat the inherited-DNP trap** —
sheet 08 carries zero DNP parts, and HOME was deleted outright rather than marked
`DNP`.

**ERC 42 / 1 error / 41 warnings — identical violation set to the working tree
this task resumed from, and better than the 45 / 2 / 43 that stood before sheet 08
was touched.** Zero new errors. PCB still bit-identical to Beta-DM; sheet 09
untouched.

**The whole IR subsystem arrived DNP — for the fourth sheet running.** `U6`,
`D1`, `Q1`, `R21`, `R22`, `R23`, `R24` and `C11` were all marked `DNP`; only the
local bulk capacitor was fitted, decoupling a transmitter that was not there.
All eight are now fitted (D-153). **This is no longer a coincidence: a `DNP` on a
Beta-DM sheet describes what was populated on that reduced build, not what the
architecture requires. Sheets 08 and 09 must be assumed to carry the same trap.**

**The rating that binds an IR LED is not the one that looks biggest.** `IFSM` =
1.5 A is a **single-pulse surge for t ≤ 5 µs** and cannot justify carrier current;
the governing figure for a 38 kHz burst train is **`IFM` = 200 mA**. Peak current
is set at **150 mA — 75 % of `IFM`** — with 200 mA rejected for leaving no
tolerance margin and **300 mA rejected as out of spec** however comfortable the
thermals look (D-155). Thermally none of them is hard: 25 mW against a 160 mW
limit, ΔTj under 6 K. Range is not the constraint either — the receiver
datasheet quotes **45 m using a TSAL6200 at only 50 mA**.

**The supply preference is reversed: `+3V3`, not `SYS`** (D-156). On the
regulated rail 12 Ω gives **118–170 mA across every tolerance**; on `SYS` the
same job gives **64–166 mA**, so **IR range would visibly shorten as the battery
drains**. The noise objection that motivated `SYS` is answered by `C12` (40 mV of
38 kHz, 1.2 % of rail) and by the fact that **the only device specified against
carrier-frequency supply ripple — the IR receiver — already sits behind 41 dB**.

**`C12` was three times too small.** 4.7 µF gives 218 mV of carrier ripple;
**22 µF gives 40 mV**, and the part is specified 1210 X7R 16 V because the
requirement is ≥ 15 µF *effective* at 3.3 V bias (D-158).

**Two inherited open items closed.** The **AO3400A pinout is confirmed
1 = G, 2 = S, 3 = D** from the AOS datasheet, matching the existing wiring; and
the *"needs the official AOS land pattern"* blocker asked for a document that
**does not exist**, so it becomes an ordinary FBV2-S2 footprint item (D-159).
Safe-OFF is now proven rather than assumed: `R23` holds the gate at ≤ 10 mV
against a 650 mV threshold, a 65× margin.

**The receiver's existing supply filter turns out to be the load-bearing part of
the sheet.** `R21`/`C11` give **41 dB at 38 kHz**, and datasheet Fig. 7 shows the
receiver degrading from roughly **10 mV RMS of supply ripple at the carrier
frequency**. 40 mV on the rail becomes 0.1 mV at `VS` — **~90× margin**, and that
is what makes sharing `+3V3` safe (D-160).

**ERC 45 → 45: zero added, zero removed.** 311 components, 0 duplicates,
0 without a footprint, 0 `*_TBD` nets.

> **O-5 — NEW, REQUIRES A CTO DECISION. The receiver lock conflicts with the
> protocol list.** The brief locks `TSOP38438`; the brief also lists Sony/SIRC.
> **Vishay marks AGC4 "No" for Sony code** where the AGC2 `TSOP38238` is "Yes".
> The lock is a defensible trade — AGC4 is *"Preferred"* on five of six protocols
> and suppresses high-modulation fluorescent interference AGC2 cannot — but it is
> a trade. **It is receive-only: transmitting Sony is unaffected**, and reverting
> is a `lib_id` change because **the `TSOP38238` symbol was deliberately kept in
> the library**. Implemented as locked pending the ruling.

**B-65, B-66 opened.**

Full analysis:
[`audits/2026-08-23-s1-ir-implementation.md`](audits/2026-08-23-s1-ir-implementation.md).

<details>
<summary>Superseded — the ~51% assessment (FBV2-S1-006)</summary>

**Raised 49% → 51% by FBV2-S1-006.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-AUDIO = PASS** (2026-08-23).

**The finding that was not on the brief: the speaker output path has never been
built.** `U5` (the MAX98357A) and `J6` (the speaker connector) arrived from
Beta-DM marked **`DNP`** — while `C9` and `C10` *were* fitted, decoupling an
amplifier that was not there. Voice output is required, so **both are now
fitted** (D-144). This is the **third load-bearing inherited `DNP` in two
tasks**; a `DNP` on a Beta-DM sheet describes the reduced build, not the
architecture, and every migrated sheet has to re-decide it.

**The microphone replacement is not a drop-in.** PUI **`DMM-4026-B-I2S-R`** has
**seven pads, not six**, so a new symbol and a new footprint were built from the
manufacturer drawing. Its extra pin, **`CONFIG`, must be tied to GND** and has no
ICS-43434 equivalent. **`R120` 100 kΩ on `I2S_MIC_DIN` is a data-sheet
requirement** — `SD` tri-states for the whole unused half of every frame and the
inherited sheet had no pull-down at all (D-145).

**No 1.8 V rail is needed, and that was the biggest risk in the swap.** The part
is *rated* 1.8 V and PUI's catalogue line reads *"MICROPHONE -26DB 1.8VDC"*, but
its operating range is **1.5–3.6 V**, so `+3V3` and the existing `C8` are the
whole supply design.

**The brief's suggested 16 kHz cannot be run on the wire.** The microphone needs
**BCLK 2.048–4.096 MHz**; 16 kHz × 64 = 1.024 MHz is outside it, and below
320 kHz the part sleeps. **The bus runs at 48 kHz × 64 = 3.072 MHz and firmware
decimates to 16 kHz** (D-146). On the bench this would have looked like *the
microphone sometimes returns silence*.

**A gain strap was mismatched to the rail.** At `GAIN_SLOT` = GND (12 dB) a
0 dBFS sample asks for **5.07 Vrms** and the 3.3 V rail gives **2.33 Vrms** — the
**top 6.8 dB of the digital range was clipped by the supply**. `GAIN_SLOT` moves
to VDD = **6 dB**, where 0 dBFS lands on the rail. Maximum loudness is unchanged;
it is rail-limited, not gain-limited (D-147).

**Speaker locked: PUI `AS02008MR-LW152-R`** — Ø20 × 3 mm, 8 Ω, 0.5 W rated /
0.8 W max, 86 dBA at 0.1 W / 0.1 m, **500–4000 Hz voice band**, 152 mm AWG #32
leads that **crimp straight into the existing `J6` JST PH**, so the speaker is
replaceable without soldering (D-148). **Default maximum software volume
−6 dBFS → 0.17 W, ≈ 57 mA**; 0 dBFS (0.68 W, 230 mA) exceeds the rated power and
must not be continuous (D-149).

**EMI: nothing fitted.** The MAX98357A data sheet's own Figure 14 shows
compliance with **12 in of speaker cable and no filter at all**, and AQROOT's
lead is half that. `R121`/`R122` are fitted 0 Ω — a plain wire — with
`C81`/`C82` 1 nF DNP as the no-respin recovery (D-150).

**ERC 45 → 45: zero added, zero removed.** 308 components, 0 duplicates,
0 without a footprint, 0 `*_TBD` nets.

**No new item requires a CTO decision.** Every change sits inside the brief's own
instructions. **B-61–B-64 opened**; the microphone is confirmed in live
distributor stock, the speaker is **not**, and is carried as B-61 rather than
called confirmed.

Full analysis:
[`audits/2026-08-23-s1-audio-implementation.md`](audits/2026-08-23-s1-audio-implementation.md).

</details>

<details>
<summary>Superseded — the ~49% assessment (FBV2-S1-005)</summary>

**Raised 47% → 49% by FBV2-S1-005.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-I2C-IMU = PASS** (2026-08-23).

**First, a correction to a number this file has been repeating.** FBV2-S1-004,
004B and 004C all quote **"ERC 68"**. The stored reports do not say that — they
say **46**. The *deltas* those tasks reported ("zero added, zero removed") are
correct and reproducible; only the absolute figure was wrong, and it has been
carried for three tasks. **Sheet `04`'s migration genuinely took the count from
64 to 46.** Separately: `kicad-cli sch erc --severity-all` also counts
**Exclusions** and reports 104 on the same unmodified design. Every number in
this programme is `--severity-error --severity-warning`. **Compare like with like
or the gate is meaningless.**

**Nothing on Sheet 05 was wrong, and that is the honest headline.** The brief said
not to copy Beta-DM's BMI270 straps blindly. Every one of them was re-derived from
`BST-BMI270-DS000-08` Rev 1.6 — `SDO`→GND for 0x68, `CSB`→VDDIO because Bosch
recommends hard-wiring it, `ASDx`/`ASCx`→VDDIO with Bosch's explicit ***"Do not
connect to GND"***, `INT2`/`OCSB`/`OSDO` DNC as instructed, 100 nF at pins 5 and 8
— and they were all already correct (D-136).

**The one real defect was on the bus, not the IMU.** Measured from the netlist, the
internal I²C bus carries **≈ 85 pF worst case** (two expanders, the IMU, the fuel
gauge, the TCA9517A A-side, the touch controller through the 50-pin display flex,
two test points, ~120 mm of trace). At **4.7 kΩ** that is `t_r` = **338 ns — past
the 300 ns fast-mode limit** — while a typical 60 pF gives 239 ns and passes.
**A part that works on the bench and fails on the unit with the longest flex.**
`R19`/`R20` → **2.2 kΩ**: **158 ns, 47 % margin**, sink current **1.32 mA** against
a 2 mA BMI270 / 6 mA expander / 3 mA specification floor (D-139).

**`0x68` is now escapable by rework instead of a respin.** `SDO` was hard-wired to
GND, so an address collision meant cutting a trace at a 0.25 mm pad. It is now
`R118` 0 Ω **FIT** to GND (0x68) and `R119` 0 Ω **DNP** to `+3V3` (0x69), **fit one
only**. `0x68` is the most collision-prone address on a community bus — MPU6050,
ICM-20948 and the DS3231 RTC all default to it, and those are exactly what a
hobbyist accessory is built from (D-140).

**B-44 CLOSED.** The BMI270 pad drive is **`IOH`/`IOL` ≤ 2 mA**, and the strap load
draws **323 µA** — 6× inside spec.

**GPIO3 boot safety is now a timing proof, not a margin argument.** `INT1_IO_CTRL`
resets to `0x00` (output disabled); firmware cannot enable it before the 8 kB
config upload; and the ESP32-S3 strap hold time is **`tH` = 3 ms** with GPIO3
defaulting to **Floating**, so `R110` alone defines the strap. **The IMU cannot
reach the strapping window.** The pull-down also *dictates* the firmware
configuration: **push-pull + active-high are mandatory and open-drain is
forbidden**, because an open-drain output into a pull-down never produces an edge.
GPIO3 = `RTC_GPIO3`, so EXT0/EXT1 deep-sleep wake works and active-high is the
right polarity (D-137).

**The IMU stays permanently powered. No load switch** — it would save ≈ 9 µA and
destroy wake-on-motion (D-141).

**The BMI270 land pattern is verified and its "DO NOT ROUTE" gate is discharged.**
§8.3 is a raster drawing, so it was rendered at 12× and measured programmatically:
every printed dimension reproduces — 0.5, 0.25, 0.475, 0.675, 0.925, 3.0, 2.5 — as
does the peripheral pin order, which is the error that would have been fatal and
silent (D-143).

**ERC 46 → 45: zero added, one removed.** 303 components, 0 duplicates, 0 without a
footprint.

**One item needs a CTO decision: O-4** — evaluate a **TCA4307-class hot-swap I²C
buffer with stuck-bus recovery** in place of `U16`, at Sheet 09 migration. See the
audit; nothing is implemented.

Full analysis:
[`audits/2026-08-23-s1-i2c-imu-implementation.md`](audits/2026-08-23-s1-i2c-imu-implementation.md).
Registry:
[`architecture/I2C_ADDRESS_REGISTRY.md`](architecture/I2C_ADDRESS_REGISTRY.md).

</details>

<details>
<summary>Superseded — the ~47% assessment (FBV2-S1-004C)</summary>

**Raised 45% → 47% by FBV2-S1-004C.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-NFC-MATCHING = PASS** (2026-08-23).

**Two defects were found that were not on the brief.**

**The RX divider would have over-driven the receiver.** At full field the antenna
sits at 24.8 V pk-pk per side; the placeholder 47 pF / 220 pF divider would have
put **≈ 4.4 V pk-pk on `RFI1`/`RFI2` against a 3.0 V regulated rail**. That is
part stress, not mistuning. The new 27 pF / 620 pF divider gives **≈ 1.0 V pk-pk,
over 3× headroom** (D-135).

**The E24 grid is brutally steep at the series matching capacitor.** 270 pF and
300 pF per leg bracket the ideal 284 pF and give **16 Ω and 68 Ω** differential —
a 4× swing in load for one step on the grid. **300 pF was chosen on purpose**, the
low-current side: an under-driven antenna is a component swap, an over-driven one
risks the driver and the rail on first power-up (D-134).

**The antenna variant is corrected — A → B.** `FXC.46.52.0075X.**B**.dg`, reverse
ferrite, bonds **adhesive-side to the inner rear shell** and reads outward with the
ferrite facing **inward**. With the A version the ferrite would have sat between
the coil and the tag (D-131). **Board unaffected — `J7`, cable and connector are
identical.**

**B-56 CLOSED:** the EMC filter moved from a cut-off of **7.6 MHz — below the
carrier** — to **20.1 MHz**, outside AN5276's forbidden 13–14 MHz band.

**ERC 68 → 68: zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005 — the stored reports say 46 → 46. The delta was right.)*

Full analysis:
[`audits/2026-08-23-s1-nfc-matching-closeout.md`](audits/2026-08-23-s1-nfc-matching-closeout.md).

</details>

<details>
<summary>Superseded — the ~45% assessment (FBV2-S1-004B)</summary>

**Raised 43% → 45% by FBV2-S1-004B.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-NFC-ANTENNA-LOCK = PASS** (2026-08-23).

**B-06 is CLOSED.** *"NFC is undesigned, not merely unrouted"* has been true since
the pre-design audit and is not true any more: **crystal, matching topology,
antenna, connector and supply all exist**. What remains is tuning, which is a bench
activity, not a design gap.

**Two locks and a proven mate.** NFC IC = **`ST25R3916-AQET`**, non-B (**P-17
CLOSED**). NFC antenna = **Taoglas `FXC.46.52.0075X.A.dg`**, off-board, 46 mm
circular flex with integrated ferrite (**B-53 CLOSED**). Board side =
**`J7` JST `BM02B-ACHSS-GAN-ETF`**, whose mating housing `ACHR-02V-S` is exactly
the ACH(F) connector Taoglas fits to that antenna's cable — so **the antenna is
replaceable without soldering**.

**The matching network now has one number that can be trusted**: `R_q` = 1 Ω per
leg, derived from the antenna alone, taking `Q` from 58 to 25.8. `C_s` and `C_p`
follow from an L-match with a stated assumption. **The EMC pair was deliberately
NOT re-derived and is flagged as unbuildable as it stands** (**B-56**) — the whole
network waits on `STSW-ST25R004`.

**ERC 68 → 68: zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005 — the stored reports say 46 → 46. The delta was right.)*

Full analysis:
[`audits/2026-08-23-s1-nfc-antenna-closeout.md`](audits/2026-08-23-s1-nfc-antenna-closeout.md).

</details>

<details>
<summary>Superseded — the ~43% assessment (FBV2-S1-004)</summary>

**Raised 40% → 43% by FBV2-S1-004.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-RADIOS-NFC = PASS** (2026-08-23).

**This is the first migration task to REDUCE the project's error count.** ERC went
**4 errors → 2**, total **86 → 68**, with **zero added and eighteen removed** — and
it did so by deleting placeholder architecture, not by suppressing checks.

**Zero `*_TBD` nets remain anywhere in the project.** Sheet 04 alone retired
fourteen. NFC stopped being a promise: a real **27.12 MHz crystal** (`Y1`, LCSC
`C362365`) and a real **differential matching topology** now exist, with every value
labelled `TUNE` because they cannot be finalised without a measured antenna.

**B-41 is CLOSED** — `U9` `VDD`/`VDD_TX` finally sit on `NFC_SUPPLY`, so the 3.3 V
FIT / 5 V DNP select built in FBV2-S1-001 now drives something.

**RF architecture locked (D-118):** 433 MHz **internal** Taoglas `FXP450.07.0100C`
(mating **proven**, not assumed), 915 MHz **external** to a top-panel **SMA female**
bulkhead. Neither band puts a single millimetre of RF trace on the board.

**Two items are recommended, not locked, and need CTO sign-off:** **P-17** (keep the
non-B ST25R3916 — it is the only one of the two with a JLCPCB path) and **B-53** (NFC
antenna architecture — recommendation is a purchased flex + ferrite).

Full analysis:
[`audits/2026-08-23-s1-radios-nfc-implementation.md`](audits/2026-08-23-s1-radios-nfc-implementation.md).

</details>

<details>
<summary>Superseded — the ~40% assessment (FBV2-S1-003)</summary>

**Raised 37% → 40% by FBV2-S1-003.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-DISPLAY-SD = PASS** (2026-08-23).

**The most valuable thing this task produced is a fault it found.** The inherited
`J1` still carried the **2.8-inch panel's pin table** while its Value and Footprint
already read FH69. Against the locked `ER-TFT035IPS-6` it was wrong in **two
independent dead-on-arrival ways**: the backlight anode and cathode were reversed
(pin 1 is LEDA, not LEDK), and the SPI clock and data/command lines were swapped
(pins 36/37). **Neither is visible from a pin count, a connector MPN or an ERC
run.** A new symbol was authored with the vendor pin table verbatim.

`R111` is **FITTED** (D-111), closing the GPIO45 item. **B-43 is CLOSED with a
primary source** — the TPS61169 `CTRL` pin has a **300 kΩ internal pull-down**, so
it cannot raise the GPIO46 strap under any condition (D-116). **B-32 and B-28 are
also closed**, the latter with `R112` **DNP** rather than fitted, because the
display SDO risks the microSD to gain a feature AQROOT never uses.

**ERC: 4 errors → 4 errors, the error report byte-identical to after FBV2-S1-002.**
Total 63 → 64.

Full analysis:
[`audits/2026-08-23-s1-display-sd-implementation.md`](audits/2026-08-23-s1-display-sd-implementation.md).

</details>

<details>
<summary>Superseded — the ~37% assessment (FBV2-S1-002)</summary>

**Raised 34% → 37% by FBV2-S1-002.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-MCU-CORE = PASS** (2026-08-23).

**Three CTO pending decisions closed and a second sheet migrated.** `R95` locked at
**560 Ω** (D-105) and the LTC4368 OV trip **derived** to **4.63 V** from the
datasheet's 492.5/500/507.5 mV threshold rather than typed in (D-104). The blanket
"no scripted KiCad edits" rule is superseded by an **eight-condition** standing
process rule (D-107). `02_MCU_CORE` carries the v2 GPIO architecture:
**GPIO38 = `NATIVE_A`**, **GPIO47 = `NATIVE_B`**, **GPIO46 = `DISP_BL_CTL`** with a
dedicated strap pull-down and an isolation link, **GPIO43 withdrawn** from the
community port, and **GPIO3's missing strap pull added — B-09 CLOSED.**

**ERC: 5 errors on the Beta-DM baseline → 4. Zero new errors; `02_MCU_CORE` reports
nothing at all.** Warnings 55 → 63, all eight being root-sheet `isolated_pin_label`
entries on cross-sheet signals whose far end is an unmigrated sheet. **They were
left standing on purpose** — clearing them by adding a test point to an orphaned net
is the same anti-pattern as a `PWR_FLAG` that hides a missing driver.

**Honest accounting on B-27.** 680 Ω was not arbitrary: it was exactly the value
that produced B-27's recorded ≈ 13 mA single-fault ceiling. Locking 560 Ω raises
that ceiling to **≈ 15.9 mA nominal / ≈ 16.6 mA worst case**, and **B-27 is amended
in place rather than left reading a number that is no longer true.**

Full analysis:
[`audits/2026-08-23-s1-mcu-core-implementation.md`](audits/2026-08-23-s1-mcu-core-implementation.md).
Measured pin ledger and strap audit:
[`architecture/GPIO_LEDGER.md`](architecture/GPIO_LEDGER.md).

</details>

<details>
<summary>Superseded — the ~34% assessment (FBV2-S1-001)</summary>

**Raised 31% → 34% by FBV2-S1-001.** **No gate in the twelve-gate table passed.**
The task gate **FBV2-S1-POWER-TREE = PASS** (2026-08-23), on the same basis as
FBV2-DISP-LOCK and FBV2-COMM-LOCK before it.

**This is the first Full Beta v2 design-file work in the programme.**
`hardware/beta-v2/` exists, forked from Beta-DM with a **re-runnable**
byte-equivalence proof, and `01_power_tree.kicad_sch` carries the Full Beta v2
power architecture: reverse protection P2 with `U18` LTC4368-1, autonomous
dead-cell recovery, both accessory rails, the NFC no-respin source select, and
`VBUS_PRESENT` telemetry. 136 parts, all with footprints assigned. **B-01 is
closed at schematic level** — `BAT_CONNECTOR_P` is no longer a one-pad net.

**Why this is +3% and not more.** `01_POWER_TREE` is one sheet of nine, and it is
the only one carrying the v2 architecture; the other eight are byte-equivalent
copies of Beta-DM. Assigned footprints are **not verified** footprints. And the
PCB is untouched — `aqroot-Beta-v2.kicad_pcb` is still bit-identical to the
Beta-DM board and does not match this schematic.

**ERC: zero introduced.** Beta-DM baseline **58** → Beta-v2 **55**, lists diffed
rather than counted; three inherited violations retired, none added. That is
**not** "ERC clean" — 55 inherited violations remain on the unmigrated sheets and
belong to FBV2-S2.

**One locked decision had been contradicted and is corrected**: `U18` LTC4368-1
carried a **DFN-10 exposed-pad** footprint against a package policy that forbids
bottom-terminated parts anywhere in the battery-protection circuitry. Moved to
MSOP-10. **Two value deviations were found and deliberately NOT changed** — `R95`
680 R against a locked 560 R (**P-20**) and an `OV` trip of 5.05 V against a
documented ≈ 4.6 V (**P-21**). A value in a locked architecture is changed by a
ruling, not by a capture task.

Full analysis:
[`audits/2026-08-23-s1-power-tree-implementation.md`](audits/2026-08-23-s1-power-tree-implementation.md).

</details>

<details>
<summary>Superseded — the ~31% assessment (FBV2-COMM-002)</summary>

**Held at 31%.** FBV2-COMM-002 **corrected an error rather than adding progress**:
the connector locked by FBV2-COMM-001, Harwin `M20-7881242`, turned out to be
obsolete, and has been replaced by Samtec **`BCS-112-S-D-HE`**. The percentage does
not rise for repairing something that should not have been recorded as locked.

It does not fall either. Nothing that was genuinely achieved has been lost: the
24-contact allocation, the pin ordering, both accessory rails, the expander
architecture and the firmware contract all stand unchanged, and the replacement is
better on every measured axis — active and next-day stocked, a lower 5.33 mm
profile (Z spare 0.70 mm → **3.47 mm**), 4.6 A per contact, and extended-life
plating available. Three CTO opportunity rulings (O-1, O-2, O-3) were also
implemented.

**The percentage rule was applied honestly in both directions**: a correction is
not progress, and a corrected error is not a regression in what was actually built.

</details>

<details>
<summary>Superseded — the ~31% assessment as first written (FBV2-COMM-001)</summary>

**No gate in the twelve-gate table passed.** FBV2-COMM-LOCK is a *task* gate, not
one of the twelve, and it **PASSED** (2026-08-23, FBV2-COMM-001).

Raised three points. This was **the last architecture closeout before schematic
implementation**, and it earns three points for a specific reason: it closes the
final three pending CTO decisions that gated a schematic sheet — **P-02** (the
connector), **P-15** (the rail budget) and **P-16** — plus the long-standing
**B-08** WAKE-isolation defect, and it does so with a purchasable connector MPN, a
locked 24-contact pin ordering with a written mis-insertion proof, two protection
ICs verified line by line against their datasheets, and a binding firmware
mutual-exclusion contract.

It is **not** more than three because nothing was built, `hardware/beta-v2/` still
does not exist, and the design now has **zero spare expander capacity anywhere**
(B-37) — a constraint that will bite the first time a new I²C-mediated signal is
wanted.

</details>

<details>
<summary>Superseded — the ~28% assessment (FBV2-DISP-002)</summary>

**No gate in the twelve-gate table passed.** FBV2-DISP-LOCK is a *task* gate, not
one of the twelve, and it **PASSED** (2026-08-23, FBV2-DISP-002).

Raised three points, and **only** three, for a specific reason: this is the first
task in the programme that locked a **physical part with a purchasable MPN, a
mating connector proven from both manufacturers' drawings, and a driver circuit
re-derived to component values.** Everything before it was architecture on paper.
The three points are for **M-06 and M-07 closing**, which removes the last gate on
FBV2-S1 — sheet `03_spi_a_display_sd` is now unblocked and every sheet in the
migration can start.

It is **not** more than three because nothing was built: no schematic exists, no
board exists, `hardware/beta-v2/` does not exist, and the mating pair is proven on
paper rather than by a mated sample.

</details>

<details>
<summary>Superseded — the ~25% assessment (FBV2-MECH-001)</summary>

**FBV2-A2 PASSED** (2026-08-22, FBV2-MECH-001). Three of twelve gates now pass.
Every dimensional dependency that could have forced a late PCB redesign is
resolved: cavity, PCB envelope, battery, NFC/battery separation, connector exit,
antenna-vs-IR, USB/microSD, acoustics and mounting bosses.

Raised five points and **no more**. All three passed gates remain paper gates —
**no schematic exists, no PCB exists, no CAD exists**, and every mechanical figure
is TARGET (derived) rather than LOCKED (measured in CAD).

</details>

<details>
<summary>Superseded estimates</summary>

**~28%** — FBV2-DISP-002. **~25%** — FBV2-MECH-001. **~20%** — FBV2-PWR-002.
**~15%** — FBV2-PWR-001. **~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001.
**~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~20%

**FBV2-A1 PASSED** (2026-08-22, FBV2-PWR-002) — the first gate to pass since
FBV2-A0, and the largest remaining architecture unknown. All six criteria closed;
all 13 power/fault cases have defined safe behaviour; no power-tree branch remains
TBD.

Raised five points, and **deliberately not more.** Two of twelve gates have
passed and both are paper gates — no schematic exists, no board exists, and
**FBV2-A2 (mechanical) has not started**, with an internal cavity that has never
existed in this repository. Architecture certainty is not the same as progress
toward a working unit.

<details>
<summary>Superseded estimates</summary>

**~15%** — FBV2-PWR-001. **~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001.
**~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~15%

Raised from ~13% by **two points** for FBV2-PWR-001: five of the six FBV2-A1
criteria are now closed, the complete battery-protection topology is specified
element by element, and P-13 was closed outright by primary-source evidence.

**No gate passed. FBV2-A1 remains FAIL — but one CTO decision now closes it.**

<details>
<summary>Superseded estimates</summary>

**~13%** — FBV2-ARCH-002. **~10%** — FBV2-ARCH-001. **~8%** — FBV2-DOC-001.
</details>

### Previous estimate: ~13%

Raised from ~10% by **three points** for FBV2-ARCH-002: four of the eight
FBV2-A1 criteria are now genuinely resolved, the mandatory power/fault state
table exists, and the NFC no-respin fallback is fully specified down to a
FIT/DNP matrix and a rework procedure.

**No gate passed. FBV2-A1 explicitly CANNOT PASS** — see the gate table.

<details>
<summary>Superseded estimate</summary>

**~10%** — recorded 2026-08-22 after FBV2-ARCH-001.
</details>

### Previous estimate: ~10%

Raised from ~8% by **two points only**, and only because FBV2-ARCH-001 closed
four pending CTO decisions (P-03, P-05, P-06, P-08, P-09) and verified nine
architecture facts against vendor datasheets.

**No gate passed.** FBV2-A1 is still IN PROGRESS. The estimate stays deliberately
low because the largest remaining unknowns — mechanical cavity, connector freeze,
reverse-polarity architecture, NFC supply topology — are all still upstream of
any drawing, and three of the four need a CTO decision rather than engineering
work.

---

## Gate table

| gate | description | status | date |
|---|---|---|---|
| **FBV2-A0** | Pre-design audit | **PASS** | 2026-08-22 |
| **FBV2-A1** | CTO architecture decisions | **PASS** | 2026-08-22 |
| **FBV2-A2** | Mechanical interface freeze | **PASS** | 2026-08-22 |
| **FBV2-S1** | Schematic migration / rearchitecture | **PASS 2026-08-23.** `hardware/beta-v2/` was forked from Beta-DM with a re-runnable byte-equivalence proof, and **all nine sheets** — `01_POWER_TREE`, `02_MCU_CORE`, `03_SPI_A_DISPLAY_SD`, `04_SPI_B_RADIOS_NFC`, `05_I2C_DEVICES`, `06_AUDIO`, `07_IR`, `08_BUTTONS_EXPANDERS` and `09_COMMUNITY_HEADER` — now carry the v2 architecture (FBV2-S1-001 … 009). **All nine task gates PASS and `fork_equivalence.py`'s "still Beta-DM" list is EMPTY.** Closeout verified 321 components with 0 duplicates and 0 missing footprints, 224 nets with 0 `*_TBD`, the GPIO ledger re-read pin by pin with no boot-strap regression, three PCAL addresses at 0x20/0x21/0x22, the 24-contact allocation matching D-084, and **ERC 27 / 0 errors / 27**. **This gate is about the schematic and nothing else — it is not a fabrication-readiness statement.** | 2026-08-23 |
| **FBV2-S2** | ERC + footprint audit | **NOT STARTED** | — |
| **FBV2-P1** | Floorplan / placement | **NOT STARTED** | — |
| **FBV2-P2** | Routing | **NOT STARTED** | — |
| **FBV2-D1** | DRC / DFM / fab package | **NOT STARTED** | — |
| **FBV2-F1** | Fabrication / PCBA | **NOT STARTED** | — |
| **FBV2-B1** | Safe first power-up | **NOT STARTED** | — |
| **FBV2-B2** | Subsystem validation | **NOT STARTED** | — |
| **FBV2-B3** | Full showcase validation | **NOT STARTED** | — |

### Gate exit criteria

| gate | passes when |
|---|---|
| FBV2-A0 | A read-only audit pinned to a repository HEAD exists in `audits/`. **Met 2026-08-22.** |
| FBV2-A1 | Every item in the Pending CTO Decisions table of [CTO_DECISIONS.md](CTO_DECISIONS.md) is closed into a locked `D-xxx` ruling. |
| FBV2-A2 | Internal cavity X/Y/Z, wall thickness and PCB-to-wall clearance are published, and every dimensional dependency that could force a late PCB redesign is resolved. **Met 2026-08-22** via [mechanical/MECHANICAL_INTERFACE_SPEC.md](mechanical/MECHANICAL_INTERFACE_SPEC.md). ⚠ **`tools/check_mechanical_consistency.py` still reports UNKNOWN** — it parses the Field Slate v5 block, and FBV2-MECH-001 had **no authority** to modify `tools/` or the Field Slate. Reconciling the guard is a follow-up task, not a gate condition, because the guard reads a Beta-DM-era document rather than the v2 spec. |
| FBV2-S1 | `hardware/beta-v2/` exists, forked from Beta-DM with a byte-equivalence proof, and every schematic change in the migration order is landed. **Half met 2026-08-23:** the fork and its proof exist (`hardware/beta-v2/checks/fork_equivalence.py`, `hardware/beta-v2/reports/FBV2-S1-fork-equivalence.md`); **7 of 9 sheets** are landed. |
| FBV2-S2 | 0 ERC errors, 0 schematic-parity issues, and every project-library footprint verified against a vendor drawing with a per-footprint pad-overlap assertion. |
| FBV2-P1 | Outline derived from the published cavity; all mechanical keepouts instantiated; IR TX/RX escapes proven at placement time; U3/connector cluster placed at the right-side exit. |
| FBV2-P2 | Ratsnest zero including GND; no pin-specific budget exceptions. |
| FBV2-D1 | 0 DRC errors, 0 unconnected, same-net hole-to-hole checked at warning level, POFV control regenerated, BOM/CPL diffed against the MPN ledger rather than regenerated blind. |
| FBV2-F1 | Boards and assemblies received against a confirmed production file set. |
| FBV2-B1 | `+3V3` overshoot below 3.6 V; reversed-battery-with-USB fault test passed; no smoke, no thermal runaway. |
| FBV2-B2 | Each subsystem independently demonstrated. |
| FBV2-B3 | Full showcase demonstration on real hardware. |

---

## Current blockers

Carried from the pre-design audit (2026-08-22). Each maps to a pending CTO
decision or a mandatory gate.

### Fabrication blockers — cannot release to fab

| # | blocker | evidence | owner |
|---|---|---|---|
| **B-01** | **Reverse-polarity protection does not exist.** `BAT_CONNECTOR_P` is a single-pad net (`J4.1` only). Nothing bridges it to `BAT_PROTECTED_P`. The Design Decisions Log marks the block `DO NOT ROUTE. DO NOT RELEASE TO FAB.` A board built as-is will not run from battery at all. | Measured from the PCB pad-to-net map | CTO (P-01) |
| **B-02** | **Power / self-damage gates unresolved.** Regulator overshoot, NFC boost OVP, accessory-power reverse blocking, charger thermals, RF/audio/IR brownout budget. | Audit section 12 | Engineering + CTO (D-072) |
| **B-03** | **Footprint audit not performed.** Several project-library footprints are custom or explicitly marked "intended, not verified" — TCA9535PWR, `J5` Samtec, ST25R3916, MK1 custom pad ring, Ebyte modules, Coilcraft, TPS63020, MAX17048, BMI270, Hirose FPC. | Audit section 12 item 13 | Engineering (FBV2-S2) |

### Design blockers — cannot start placement

| # | blocker | evidence | owner |
|---|---|---|---|
| **B-04** | **Internal enclosure cavity has never been published.** `INTERNAL_CAVITY_MM: not published`, `WALL_THICKNESS_MM: not published`, `PCB_FIT_STATUS: UNVERIFIED`. The v2 board outline is a derived number and cannot be derived without it. | Field Slate v5 dimension authority table | CTO (P-07) |
| **B-05** | **20-pin connector architecture not locked.** C1/C2/C3 proposed, none approved. | Audit sections 6-7 | CTO (P-02) |
| **B-06** | **NFC is undesigned, not merely unrouted.** No 27.12 MHz crystal exists in the BOM; no matching network; no antenna. 13 dangling `*_TBD` nets on U9. | Measured: 13 single-pad nets on U9 | CTO (P-03, P-04) |

### Architecture defects — must be resolved in migration

| # | defect | evidence |
|---|---|---|
| ~~**B-07**~~ | ~~NFC rail architecture defect.~~ **RETIRED 2026-08-22 — the finding was wrong.** DS12484 Rev 3 p. 39 requires VDD and VDD_TX to share one supply; Tables 118/119 cap their difference at ±0.3 V abs max / ±0.2 V operating. The as-built assignment is **correct**. The residual sequencing question is now **P-10**. | ST25R3916 DS12484 Rev 3, Tables 2 / 118 / 119 |
| ~~**B-08**~~ | ~~WAKE line has no isolation gate.~~ **BUILT 2026-08-23 (FBV2-S1-009, D-187):** `Q10` 2N7002 with `R63` 10 k to `ACC_3V3_SW`, orientation verified. | Measured: `WAKE_GATE_S` = `Q10.2`, `R63.2`, `R66.1` |
| **B-09** | **GPIO3 has no strap-defining pull.** Required by the pin map, not implemented. Hazard currently low (the S3 ignores the GPIO3 strap unless `JTAG_SEL_ENABLE` is burned) but it leaves a CMOS input floating at reset. | Measured: `BMI270_INT1_STRAP` = `R18.2`, `TP3.1`, `U1.15` |
| **B-10** | **Zero free native GPIO.** 29 assigned + 2 strap test pads + 2 USB = 31 of 31 usable. | Measured from U1 pads |
| **B-11** | **GPIO18 / GPIO38 documentation mismatch.** The pin map states GPIO18 = SX1262 DIO1 and GPIO38 = NFC IRQ. The hardware is the reverse. | Measured from U1 pads |
| **B-12** | **Possible LoRa wake defect.** `SX1262_DIO1` on GPIO38 is not RTC-capable, so wake-on-LoRa-packet is impossible in the current pinout. | Consequence of B-11 |
| **B-13** | **RGB LED nets dangling.** `RGB_R/G/B_CTL` exist with one pad each; no LED part exists. | Measured: 3 single-pad nets |
| **B-14** | **RootProbe cannot connect.** `ROOTPROBE_IRQ_READY_N` has no header pin. | Measured: net = `R11.2`, `U2.20` |
| **B-15** | **No charge or VBUS telemetry.** `BQ25185_STAT1` reaches `TP6` only, `STAT2` reaches `TP7` only, `MAX17048_ALRT_N` reaches `TP11` only. No VBUS-present sense exists. The product cannot report charging state. | Measured from the PCB |

### Documentation defects

| # | defect |
|---|---|
| **B-16** | Field Slate v5 section 5 still lists "Volume +, Volume −, Power" on the right side. Volume controls have never existed electrically. The locked external layout text needs a CTO-approved correction so enclosure CAD is not driven by phantom controls. |

---

### FBV2-A1 gate assessment (2026-08-22, FBV2-PWR-002) — **PASS**

| criterion | status |
|---|---|
| Dead-cell recovery topology explicit | **YES** — Candidate B specified to component level: ratiometric bridge, thresholds, defaults, 3-input AND, FAULT handoff, full failure analysis |
| Main reverse protection single-FET-short tolerant | **YES** — P2, two back-to-back stages in **two separate packages**. Isolation, not fault-clearing time |
| All power/fault states have defined safe behaviour | **YES** — 13 of 13 |
| No additional power-tree branch remains TBD | **YES** — the recovery branch was the last one |

**FBV2-A1 = PASS.** Component-value optimisation (exact `R_LIM`, FET MPN, fuse
rating, divider trim) moves to schematic design.

**Next gate: FBV2-A2 — MECHANICAL INTERFACE FREEZE.** Long pole, nothing blocks
it. **Do not start FBV2-S1 before the placement constraints exist.**

<details>
<summary>Superseded — FBV2-A1 assessment (FBV2-PWR-001, FAIL)</summary>

### FBV2-A1 gate assessment (2026-08-22, FBV2-PWR-001)

| # | criterion | status |
|---|---|---|
| 1 | PCAL9535A choice closed | **YES** — D-061; no pin/package incompatibility found |
| 2 | GPIO38/GPIO47 closed | **YES** — D-063; DIO1 level-hold confirmed verbatim from Semtech §13.3.4 |
| 3 | NFC architecture closed | **YES** — D-055/D-056 |
| 4 | Community power architecture closed | **YES** — D-057/D-058 |
| 5 | 20-pin resource architecture closed | **YES** — D-062 |
| 6 | **Reverse-protection topology complete, no major new power-tree branch TBD** | **NO — P-11** |

**Verdict: FAIL.** Criteria 1–5 are closed and the reverse-protection topology
itself is complete (controller, dual N-FET, R_SENSE 15 mΩ, R_GATE 22 kΩ,
C_GATE 1 nF, UV recommended unused, OV divider, RETRY grounded, SHDN pull-up to
VIN, FAULT, fuse, clamp). **The dead-cell recovery branch (P-11) is a new
power-tree branch and is not chosen.** Per the CTO's instruction — *"Do not pass
the gate merely because a preferred idea exists"* — the gate is not passed.

**One decision closes it.** Selecting Candidate B or Candidate D closes criterion
6; P-12 then carries into the schematic phase as a bench item, since it changes
no topology.

</details>

### Blockers added or changed by FBV2-P2-000 (2026-08-24)

| # | item | status |
|---|---|---|
| **PM-1** | **ALL FOUR SWITCHING CONVERTERS HAVE THEIR INDUCTOR OFF THE IC.** `U12`/`L1` **12.96 mm**, `U13`/`L2` **28.56 mm**, `U21`/`L4` **30.50 mm**, `U17`/`L3` **45.90 mm**, against ≤ 5 mm. The backlight's `L3 → D8 → C44` boost loop is **≈ 76 mm around**, switching at 1.2 MHz to **up to 39 V** on an open-LED fault, down the left margin **13 mm from `MK1`**. All four inductors sit in the left-margin column at x ≈ 3 while their ICs are elsewhere | **OPEN — P2 ENTRY BLOCKER, CTO DECISION (D-236).** Loop area is a placement property; no routing repairs it |
| **PM-2** | **THE SINGLE-FAULT BATTERY-PROTECTION BLOCK IS DISPERSED OVER 96 mm** across three clusters. `LTC_GATE` **95.6 mm** (≈ 20 µA charge-pump node, damping 31–45 mm from the FETs), `BAT_SENSE` **96.5 mm** (1.5 A **and** the FET source reference), `LTC_OV`/`LTC_UV` 78.4/81.7 mm (**the battery trip points**, on 3.65 M / 510 k dividers), `VBRIDGE_TOP` 90.1, `VREF_TOP` 80.8, `REF_HO` 82.4 mm (2.2–3.65 MΩ dead-cell reference nodes; `REF_HO`'s two divider halves are **38 mm apart**). Total 1.5 A path ≈ **116.7 mm** | **OPEN — P2 ENTRY BLOCKER, CTO DECISION (D-236).** **The Kelvin sense itself is SOUND and D-049 is NOT compromised** — the recommendation moves parts, not topology. It also returns ≈ 0.13–0.18 W to **B-34** |
| **PM-3** | **THE NFC DIFFERENTIAL FRONT END IS NOT SYMMETRIC.** `NFC_MATCH_A` **24.18 mm** vs `NFC_MATCH_B` **34.21 mm** — 10 mm of asymmetry before a track is drawn; `L5`/`L6` **19.8 mm apart on opposite sides of `U9`**; antenna nodes 8.82 vs 12.49 mm; crystal load caps **13–15 mm from `Y1` on the far side of the IC** | **OPEN — P2 ENTRY BLOCKER, CTO DECISION (D-236).** With `R_q` 1.1 Ω/arm and Q ≈ 21 (D-204), routing cannot absorb it |
| **PT-1** | **`U11` BQ25185 dissipates ≈ 0.65 W while charging from INSIDE `BATTERY_SHADOW`**, doc (56.000, 32.000) on B.Cu, ≈ 10 mm inside the pouch envelope, in a sealed unvented enclosure against a 0–45 °C charge window | **OPEN, medium — ROUTING-STAGE ITEM (D-235).** Composes with PM-2 and B-34. **No thermal path may depend on the battery** |
| **P2-O6** | **The board file carries NO physical stackup object at all** (nor does Beta-DM's), so a fabricator builds to its own default and no impedance control is ordered | **OPEN, low — DFM / RELEASE ITEM (D-235).** Does not block routing: the one impedance-sensitive net is Full-Speed USB over ≈ 40 mm |
| **P2-R1** | **The 433 flex sits 0.2 mm outboard of the LEFT board edge** over doc Y 1.5 … 48.5, so board copper in X 0 … 3.0 of that band is an **aggressor into** it | **OPEN — ROUTING-STAGE ITEM (D-235).** Deliberately **not** instantiated as a rule area until PM-1 settles which parts occupy that band |
| ~~**P2-O5**~~ | ~~`.kicad_dru` references deleted E5/E6 rule areas~~ | **CLOSED 2026-08-24 (D-233), and it was 39 areas and 22 inert rules — not just the E6 pockets.** `checks/dru_probe.py` stops it recurring |
| ~~**B-63**~~ | ~~The PCB acoustic hole and the pad-4 paste pullback are not in the microphone footprint~~ | **STALE — already closed by D-203 and rebuilt by D-227. The register lists it twice; the later entry is wrong. Do not carry it forward** |
| ~~**B-64**~~ | ~~The PCB still carries `MK1` with the ICS-43434 footprint~~ | **STALE — closed by the FBV2-P1 rebuild; the PUI footprint is on the board, verified 2026-08-24. Do not carry it forward** |
| **B-34** | ≈ 0.70 W and ≈ 0.40 V in the BATFET + protection path at 1.75 A in a sealed enclosure | **OPEN, medium — unchanged, but now quantified further: PM-2's dispersal adds ≈ 0.13 W at 1.5 A / 0.18 W at 1.75 A on top, and PM-2 gives most of it back** |
| **O-5** | IR receiver AGC4 (`TSOP38438`) vs the Sony/SIRC protocol list | **OPEN — FIRST-ARTICLE ITEM, still needs a CTO ruling.** Receive-only; reverting is a `lib_id` change. **No routing impact**, classified and carried forward unchanged |

### Blockers added or changed by FBV2-COMM-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~D-083~~ | **Harwin `M20-7881242` REJECTED as obsolete** — `harwin.com` returns HTTP 404 for it. The MPN had been *configured from the catalogue ordering scheme*, and FBV2-COMM-001 §15 had flagged exactly that risk | **CORRECTED.** Replaced by Samtec `BCS-112-S-D-HE` (D-093) |
| **D-096** | **New standing rule:** a part number configured from an ordering scheme is a hypothesis, not a selection. Every MPN written into a locked document must first be confirmed against a live manufacturer or distributor record showing lifecycle and stock | **STANDING** |
| **B-39** | **Mating-cycle rating unconfirmed.** Only **100 cycles** is formally qualified for BCS; the **2 500-cycle** E.L.P. figure is **by similarity at 30 µin gold**. Confirm the rated count for `BCS-112-S-D-HE` with Samtec before production | **OPEN, medium.** Procurement |
| **B-40** | Which mating row terminates in which PTH row of the 7.87 mm pattern must be read off the Samtec print, not assumed | **OPEN, low.** FBV2-S2 |
| **B-29** | **Re-scoped.** The footprint must now be drawn to Samtec FIG 3 `BCS-1XX-XXX-D-HE`: 2 × 12 PTH, **2.54 mm within a row, 7.87 ± 0.05 mm between rows, 0.71 mm drill** — *not* interchangeable with any vertical 2×12 pattern | **OPEN, medium.** FBV2-S2 |
| ~~**B-37**~~ | Zero spare expander capacity | **RETIRED 2026-08-23 (D-175).** `RESERVED_SPARE` lives on `U23` P03 with `R130` and `TP41`, and eleven further `U23` pins are free |
| **M-09** | Connector body height | **DOWNGRADED to LOW.** Z column falls from 22.30 mm to **19.53 mm of 23.0 — 3.47 mm spare**; it is no longer the sole governing column. Confirm 5.33 mm against the Samtec 3D model at FBV2-P1 |
| **M-10** | Insertion load path | **DOWNGRADED.** ≈ **33 N average** (was ≈ 48 N max), peak higher. Enclosure boss still required (D-097) |
| **P-19** | The 24Cxx family spans `0x50`–`0x57`; only `0x50` is reserved. May need widening if multi-EEPROM accessories appear | **OPEN, low.** CTO, with P-18 |
| ~~O-1~~ | Wire-OR the `FLT` lines | **APPROVED and implemented** (D-094) |
| ~~O-2~~ | Accessory-ID EEPROM address `0x50` | **APPROVED and implemented** (D-095) |
| ~~O-3~~ | Share the accessory boost with the NFC fallback | **REJECTED and struck** (D-095) |

**Two NEW opportunities are flagged for a CTO ruling and were deliberately NOT
locked:** **N-1** publish an accessory reference design (footprint, the 4.34–6.35 mm
post-length rule, the detect-strap pattern, the shared-rail current rule, a board
template) — high value, documentation-only; **N-2** accessory retention — withdrawal
force is only ≈ 20 N average with no latch, so an enclosure detent or captive
fastener is worth considering.

### Blockers added or changed by FBV2-COMM-001 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~P-02~~ | Freeze the 20-pin connector | **CLOSED** — the 20-pin architecture is **superseded**; the port is 2×12 / 24 active contacts, female, `Harwin M20-7881242` (D-081…D-085) |
| ~~P-15~~ | 3V3 rail budget under simultaneous worst case | **CLOSED** — binding mutual-exclusion contract MX-1…MX-9 (D-092) |
| ~~P-16~~ | Repurpose one XGPIO as `ACC_DETECT`? | **CLOSED** — dedicated contact (pin 23) and dedicated `U3` input (D-082/D-085) |
| ~~B-08~~ | **WAKE line has no isolation gate** — a shorted accessory pin can permanently block internal button wake | **CLOSED IN COPPER 2026-08-23 (FBV2-S1-009, D-187).** `Q10` 2N7002, gate on `ACC_3V3_SW`, **source to the connector and drain to the internal line** so the body diode blocks with the rail off. Until this task the gate existed only as a decision |
| **B-34** | ≈ **0.70 W of series loss and ≈ 0.40 V of drop** in the BQ25185 BATFET (115 mΩ) + reverse-protection path at 1.75 A, inside a sealed enclosure | **OPEN, medium.** FBV2-S1 thermal review |
| **B-35** | **`TPS22950C` `FLT` does not assert on plain current limiting** — only on thermal shutdown and reverse current. A hard short reaches TSD in tens of ms and is then reported; a **partial** overload is invisible to the host | **OPEN, documented.** Firmware contract |
| **B-36** | Accessory-initiated wake now requires `ACC_3V3_SW` to remain enabled during sleep — a consequence of the B-08 gate | **OPEN, policy.** FBV2-B2 |
| ~~**B-37**~~ | ~~ZERO spare expander capacity on BOTH `U2` and `U3`~~ | **RETIRED 2026-08-23 (FBV2-S1-009, D-175).** O-6 ratified: `U23` is locked architecture. **37 of 48 expander pins used, ELEVEN spare** plus the formal `RESERVED_SPARE`. The programme carried this constraint from its first audit |
| **B-38** | The 5 V boost inductor must be **1 µH with `I_sat` ≥ 3 A** to survive a fault at the load switch's worst-high limit | **OPEN, low.** FBV2-S1 |
| **M-09** | The **connector region is the new governing Z column** — 22.30 mm of 23.0 mm external, 0.70 mm spare | **OPEN.** FBV2-P1 |
| **M-10** | Up to **48 N** insertion force; the enclosure must carry it on a boss/rib | **OPEN.** Enclosure CAD |
| **P-18** | External-I²C segmentation | **UNCHANGED, NOW PRECISELY CHARACTERISED (FBV2-S1-005).** `U16`, `R49`/`R50`, `U15` and `D2`/`D3` are **all DNP** — there is no fitted external I²C path today, so the choice costs no rework. TI: *"the TCA9517A logic and all I/Os are powered by the `VCCB` pin"*, and `VCCB` = `ACC_3V3_SW`, so a de-asserted rail leaves the buffer **unpowered and high-Z on both sides** — harder than a mux. **The weakness is not the buffer, it is the location of its disable control**: `ACC_PWR_EN` is `U3` P17, behind the bus it protects. 9-clock recovery frees the common case for free; a hard short needs a `+3V3` power cycle, since an MCU reset does not reset the expanders. **Address collision is not solvable by any buffer** — closed by D-142 instead. Decision deferred to Sheet 09 via **O-4** |

**Three opportunities are flagged for a CTO ruling and were deliberately NOT
locked:** wire-OR the two `FLT` lines to recover one expander pin; reserve an I²C
address for an accessory-ID EEPROM; a DNP 0 Ω link letting the accessory boost also
serve the NFC 5 V fallback.

### Blockers added or changed by FBV2-DISP-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~M-06~~ | Display MPN and FPC interface | **CLOSED** — `ER-TFT035IPS-6` + `ER-TPC035-6`; 50-pin, 0.50 mm, **bottom contact**, 0.30 ± 0.03 mm; FT6236 @ 0x38 (D-074/D-075) |
| ~~M-07~~ | Backlight driver re-derivation | **CLOSED** — TPS61169 retained from `+3V3`; `R69` = 1.87 R, `R70`–`R73` = 4 × 33 R; switch-peak margin 4.6× (D-079) |
| **B-28** | **ILI9488 `SDO` on the shared SPI-A bus is unverified.** Mitigated by design: fit a 0 R `R_SDO` isolation link plus a test point so the display can be made write-only without a respin | **OPEN, mitigated.** Closes at FBV2-B2 |
| **B-29** | **`J1` footprint must be redrawn** on the FH12-horizontal / FH52E standard land pattern (D-077) and verified with a per-footprint pad-overlap assertion against **both** connector drawings | **OPEN.** Closes at FBV2-S2 — folds into B-03 |
| **B-30** | The datasheet does not name which FPC pin feeds the FT6236 VDD. Immaterial here — VDDI, VCI and the CTP supply are all `+3V3` | **OPEN, informational.** First article |
| **B-31** | Display FPC contact plating is not stated; Hirose recommends gold | **OPEN, low.** PO / first article |
| **B-32** | Confirm ≥ 4.7 µF X5R input decoupling local to `U17` `VIN` — input ripple current rises ~47 % | **OPEN, low.** FBV2-S1 |
| **B-33** | **The 2.3 mm `J1` cannot sit in the display shadow** (0.8 mm limit). It competes for the 70.04 mm below the panel with the D-pad, A/B and the mic aperture | **OPEN.** Placement coupling; closes at FBV2-P1 (tracked as M-08 in the mechanical spec) |

**Two MEDIUM procurement risks remain and neither is a design change:** the vendor
also sells a CST340 touch panel for this size, so the purchase order must name
`ER-TPC035-6`; and the datasheet carries a "Backlight Update" revision, so
Rev 2.0 (18-Aug-2025) must be archived in-repo and cited by revision in the MPN
ledger.

### Blockers added or changed by FBV2-PWR-002 (2026-08-22)

| # | blocker | status |
|---|---|---|
| ~~B-20~~ | Dead-cell lockout created by the reverse protection | **CLOSED** — autonomous hardware-qualified recovery branch (D-065), specified to component level. No firmware dependency |
| ~~B-21~~ | Shorted pass FET reproduces the guarded fault | **CLOSED by isolation** — P2, two stages, two packages. The old fuse+clamp compliance argument is **withdrawn as invalid** |
| ~~B-23~~ | PCAL9535A facts unverified | **CLOSED** — CTO verified NXP Rev 2 (D-066). Land-pattern audit remains a separate pre-fab gate |
| **B-26** | **Pack-protector release current.** Recovery injects ~8 mA; a 1S protector needing more than ~10 mA to release its over-discharge latch would not be revived | **OPEN — part-dependent.** Verify against the chosen pack. Does not change topology |
| **B-27** | **Recovery branch is not tolerant to every single failure** — four failures each enable current into a reversed cell | **ACCEPTED, BOUNDED.** `R_LIM` caps every case at ≈13 mA (~0.007 C); `D_REC` keeps the branch unidirectional; the fault is self-annunciating |

<details>
<summary>Superseded — FBV2-A1 gate assessment (FBV2-ARCH-002)</summary>

### FBV2-A1 gate assessment (2026-08-22, FBV2-ARCH-002)

| # | criterion | status |
|---|---|---|
| 1 | 20-pin resource architecture resolved | **YES** — 11 XGPIO + 2 native + 2 I²C + 1 WAKE + 1 switched power + 3 GND = 20 |
| 2 | Expander family resolved | **NO** — PCAL9535A pin table not retrievable from a primary source |
| 3 | Native GPIO pair resolved | **NO** — GPIO38 gated on unverified SX1262 DIO1 level-hold behaviour |
| 4 | Default NFC architecture resolved | **YES** — 3.3 V, `sup3V`, VDD = VDD_TX = `NFC_SUPPLY`, VDD_IO = `+3V3` |
| 5 | NFC no-respin fallback resolved | **YES** — FIT/DNP matrix + rework procedure complete |
| 6 | Community accessory power resolved | **YES** — TPS22950C, permanent `+3V3` pin removed |
| 7 | Battery/reverse protection resolved at topology level | **NO** — dead-cell recovery and inrush/latch interaction both change the power tree |
| 8 | No unresolved issue can change the power-tree architecture | **NO** — P-11 adds a switched path across the pass FETs plus an ADC divider |

**Closing actions:** three of the four gaps are document reads (PCAL9535A pin
table; SX126x + E22 IRQ sections). The fourth is one CTO decision (P-11) plus one
protoboard experiment (P-13).

</details>

### Blockers added or changed by FBV2-S1-004C (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-56**~~ | EMC filter values inconsistent; cut-off below the carrier | **CLOSED.** 39 nH / 100 pF → **f_c = 20.1 MHz**, outside AN5276's forbidden 13-14 MHz band. The old pair sat at **7.6 MHz** and also presented 18.7 Ω of series reactance that was perturbing the match |
| ~~**B-48**~~ | AN5276 not retrieved; the driver target impedance was an assumption | **CLOSED ON SUBSTANCE.** ST's design rules were obtained and applied and the target is now **derived from the D-130 current budget** (≈ 36 Ω differential) rather than assumed. **The Rev 6 PDF still would not load in this environment** — see B-57 |
| **B-57** | **`STSW-ST25R004` / eDesignSuite run against a MEASURED antenna impedance has not been performed** | **OPEN, high.** Required before fabrication. It also closes most of B-55 |
| **B-58** | **`RFI` receiver linear-range spec not extracted** from DS12484 — the table is an image. The ≈ 1 V pk-pk working point is a conventional level with > 3× rail margin, not a figure quoted against a limit | **OPEN, medium.** First-article step 6 is a **pass/fail gate**, not an optimisation |
| **B-55** | `La`/`Rs`/`Q` not independently re-extracted | **OPEN, low.** The B-version published triple is coherent to ~3 % (`Q` 60.37 with 1.10 µH implies `Rs` 1.55 Ω, not 1.50 Ω). The network is re-derived from measurement anyway |
| **B-54** | ST25R3916 field current at 3.3 V | **OPEN, downgraded further.** The first-build network draws **≈ 60 mA at the driver**, comfortably inside the ≤ 150 mA budget. Measure at first article |

### Blockers added or changed by FBV2-S1-004B (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-06**~~ | NFC is undesigned, not merely unrouted | **CLOSED 2026-08-23.** Crystal, matching topology, antenna, connector and supply all exist. What remains is tuning, not design |
| ~~**B-53**~~ | NFC antenna architecture undecided | **CLOSED by D-127** — off-board Taoglas `FXC.46.52.0075X.A.dg` on a JST ACH connector |
| ~~**P-17**~~ | ST25R3916 or ST25R3916B | **CLOSED by D-126** — `ST25R3916-AQET`, non-B |
| **B-54** | ST25R3916 field current at 3.3 V | **DOWNGRADED.** Conservative estimate **≤ 150 mA** derived; TPS63020 worst case ≈ 66-74 % of 2 A and MX-1 keeps the field off during LoRa TX. Datasheet figure or measurement still owed |
| **B-55** | **`La`/`Rs`/`Q` not independently re-extracted** — the Taoglas electrical table is an image, and a secondary summary quoted a conflicting triple that most likely belongs to the FXC.40 | **OPEN, low.** The supplied triple is internally consistent (`ωL/Rs` = 58.0 exactly). Confirm at first article; the match must be re-derived from measurement regardless |
| **B-56** | **EMC filter values are inconsistent with the new shunt.** `L5`/`L6` 220 nH against ~2 nF resonates near **7.6 MHz — below the 13.56 MHz carrier** | **OPEN, high. Do not build to the current EMC values.** Must come out of the `STSW-ST25R004` run |

### Blockers added or changed by FBV2-S1-004 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-41**~~ | `NFC_SUPPLY` has no consumer | **CLOSED 2026-08-23 by D-122.** `U9` `VDD`/`VDD_TX` moved off the Beta-DM boost output; the 3.3 V FIT / 5 V DNP select now drives something |
| **B-06** | NFC is undesigned, not merely unrouted | **LARGELY CLOSED.** A real 27.12 MHz crystal and a real differential matching topology exist; only the antenna choice (B-53) and the tuning values (B-48) remain |
| **B-48** | **AN5276 not retrieved** — every st.com fetch timed out. All matching and RX-divider values are **initial values** | **OPEN, high.** Run STSW-ST25R004 against a measured antenna impedance before the BOM gate. No value is presented as an ST reference figure |
| ~~**B-49**~~ | **CLOSED 2026-08-23 (D-195) — THERE WAS NEVER A RISK.** Ebyte ships both modules with **IPEX *and* stamp holes on the standard part number**; no variant selection exists to get wrong. Original text: **IPEX socket population must be confirmed with the supplier** for the exact ordered `U7`/`U8` MPNs — Ebyte sells IPEX and stamp-hole variants under similar numbers | **OPEN, high.** The entire zero-board-RF plan collapses if stamp-hole units arrive. Hard procurement deadline |
| **B-50** | FXP450 bend radius, adhesive, ground clearance and temperature not retrieved — the datasheet is image-based beyond page 1 | **OPEN, medium.** Mechanical input for FBV2-P1 |
| ~~**B-51**~~ | **CLOSED 2026-08-23 (D-195): Amphenol RF `095-902-568-150`, Part Status ACTIVE** — AMC R/A plug → SMA straight bulkhead jack, IP67, RG-178, 50 Ω, 150 mm, 6 GHz. **One assembly: pigtail and bulkhead in a single orderable part.** Original text: 915 MHz pigtail assembly MPN not selected — the interface is locked, the part is not (D-096) | **OPEN, medium** |
| **B-52** | Top-panel spacing between the SMA bulkhead and the IR apertures recorded (**≥ 8 mm**, pigtail clear of the optical path) but **no CAD exists** | **OPEN, medium** |
| ~~**B-53**~~ | **CLOSED 2026-08-23 (D-200) — STALE**, decided by D-131: purchased flex + ferrite, `FXC.46.52.0075X.B.dg`, **B variant** locked. Original text: **NFC antenna architecture undecided** — main-board loop vs purchased flex + ferrite vs daughter antenna | **OPEN, high.** Recommendation: **flex + ferrite**. A main-board loop needs a 45 × 45 mm ground-plane keepout on every layer with the battery behind it |
| **B-54** | **ST25R3916 field current at 3.3 V not extracted.** The NFC PA load has moved from `SYS` to `+3V3`, so the TPS63020 budget does not yet include it | **OPEN, high.** D-092's 58-66 % figure must not be quoted as covering the NFC field in this form |

### Blockers added or changed by FBV2-S1-003 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-43**~~ | TPS61169 `CTRL` internal-pull specification not retrieved | **CLOSED 2026-08-23 by D-116.** SNVSA40B: **`R_PD` = 300 kΩ internal PULL-DOWN**, `V_H`/`V_L` 1.2/0.4 V. `CTRL` can only pull GPIO46 down — the strap is safe by construction, not merely by margin |
| ~~**B-32**~~ | Confirm ≥ 4.7 µF X5R local to `U17` `VIN` | **CLOSED** — `C43` 4.7 µF 0805 on `+3V3` at `U17.5`, marked `4.7uF 10V X5R` |
| ~~**B-28**~~ | ILI9488 `SDO` on a shared bus | **CLOSED by D-114** — `R112` 0 Ω **DNP**, `TP36` on the panel side. Opposite default to the one FBV2-DISP-002 sketched, because fitting risks the microSD to gain a feature nothing uses |
| ~~**B-46**~~ | **CLOSED 2026-08-23 (D-196) — THE ASSUMPTION WAS RIGHT.** Molex SD-502570-001 Rev A note 4: CARD INSERTING POSITION = CLOSE, NO CARD = OPEN, so with the lever grounded and `R113` pulling up, **LOW = card present**. No firmware correction, no hardware change. Original text: **microSD detect-switch polarity assumed, not confirmed** — the Molex drawing would not load. `SD_CARD_DETECT_N` assumes switch-closes-on-insertion | **OPEN, low.** Firmware constant on a PCAL9535A input; never a board change |
| ~~**B-47**~~ | **RESOLVED 2026-08-23 (D-194) — OUTCOME B, NOT COMPATIBLE, AND D-077'S DROP-IN CLAIM IS STRUCK.** FH69 layout depth **7.38 mm** with a 0.30 × 1.23 land and top-and-bottom two-point contact; FH52E **4.6 mm**, bottom contact only, and its catalogue points at the **FH12** pattern. `J1` keeps the dedicated FH69 footprint and is **MANUAL ASSEMBLY** for the first five. Original text: **FH52E second source and land-pattern migration unresolved.** Drop-in equivalence was **not** asserted without both Hirose drawings, so `J1` stays on the FH69-dedicated pattern | **OPEN, medium. There is currently no JLCPCB assembly path for `J1`.** Settle at FBV2-S2, before placement |
| **B-29** | `J1` land pattern verified with a pad-overlap assertion | **STILL OPEN, advanced.** Pad geometry measured: 50 pads, 0.500 mm pitch with no drift, 24.500 mm span, 0.300 × 1.230 mm pads, 2 hold-downs. The assertion itself is FBV2-S2 |

### Blockers and opportunities CLOSED by FBV2-S2-002 (2026-08-23)

**FBV2-S2 = PASS.** Six items close. Full analysis:
[`audits/2026-08-23-s2-release-closeout.md`](audits/2026-08-23-s2-release-closeout.md).
New working document:
[`assembly/FIRST_FIVE_ASSEMBLY_PLAN.md`](assembly/FIRST_FIVE_ASSEMBLY_PLAN.md).

| # | item | status |
|---|---|---|
| ~~**B-03**~~ | Footprint audit | **CLOSED 2026-08-23 by D-201/D-202.** All eight remaining Tier-2 footprints compared **dimension by dimension** against retrieved manufacturer drawings — **23 of 28 critical footprints are now Tier 1** and none was promoted on the strength of its name. **The MAX98357A looked like a real defect and was not:** Maxim land pattern **90-0032 Rev E** is issued for `T1633-5`, `-5C` **and** `-7C` together and specifies **one** land for all three, so the 1.23 mm EP does not depend on which variant the part carries. **No project-local footprint was created** — both deviations are ≤ 0.05 mm and on the safe side. `Y1`'s land is an **exact** match to the vendor's Suggested Layout |
| ~~**B-63**~~ | Microphone acoustic footprint | **CLOSED 2026-08-23 by D-203.** **Ø1.05 mm NPTH** (the drawing's own pad-4 ring ID — not invented), **paste pullback** to a separate ID 1.25 / OD 1.65 annular aperture (the 0.10 mm pullback is a **declared stencil choice**, and the footprint says so), keepout marked on `B.Fab` + `User.Comments`, **bottom-port orientation** recorded as **M-14**. Re-parsed through `pcbnew` to confirm validity |
| ~~**B-70**~~ | NFC EMC inductor MPN | **CLOSED 2026-08-23 by D-204.** Murata **`LQW18AN39NG80D`**, `C2042966`, 270 in stock. **Not locked from headline specs:** SRF 74× the third harmonic, X_L 3.32 Ω as D-134 assumed, **DCR 0.20 Ω max against `R_q` 1.1 Ω drops network Q 25.3 → ≈ 21.4** — further into the safe side, but **the antenna must be bench-tuned with this exact part fitted**, and the first lever if the field is short is `R_q`, **not** 39 nH |
| ~~**B-54**~~ | ST25R3916 field current at 3.3 V | **CLOSED 2026-08-23 by D-205.** DS12484 Rev 3 retrieved through a mirror. **`I_AL-AM` max 26 mA (IC) + ≈ 60 mA (driver into D-134's actual network) → allocate 100 mA.** **The 350 mA / 500 mA figures are ABSOLUTE MAXIMA and were deliberately not used.** TPS63020 **63–71 % of 2 A**. **Binding guard rail: a `C_s` move to 270 pF would draw ≈ 257 mA and requires the rail budget to be re-run first** |
| ~~**B-71**~~ | LCSC / JLC / manual assembly classification | **CLOSED 2026-08-23 by D-206/D-207.** All **46 MPNs** classified against live JLCPCB parts-API state; **65 `LCSC` fields written into the schematic**. **Two hand-soldered THT parts per board, zero hand-placed fine-pitch or QFN.** Ten stock shortfalls + one library gap, all handled by **consignment**. **Six substitution traps caught**, including `BAT54W` offered for `BAT54WS` and a clone for the **battery reverse-polarity pass FETs**. **`J1` improves to machine-placed** — JLC stocks the genuine Hirose. ***CORRECTED 2026-08-23 (D-211): the `BAT54W` trap was recorded as "single diode vs series pair". `BAT54WS` IS NOT A SERIES PAIR — SOD-323 is a two-terminal package and `D10`–`D12` are each one independent diode. `BAT54W,115` is wrong because it is SOT-323 (SC-70), a FOOTPRINT mismatch.*** |
| ~~**O-8**~~ | 915 MHz external antenna | **CLOSED 2026-08-23 by D-209.** Taoglas **`TI.92.2113`** verified against **SPE-19-8-076/A**. Every expectation in the CTO ruling checks out. **The marketed "2 dBi" is the bent-configuration peak — average gain is negative in both orientations, so budget the link with the average.** No hardware or schematic change required |
| — | **DNP hygiene** | **D-208.** Eight DNP parts still had **no recorded reason**: the six-part NFC 5 V boost branch (`U13`, `L2`, `R44`, `R45`, `C34`, `C35` — correct, and a D-049 no-respin escape), `R119` (BMI270 alternate address; **mutually exclusive with `R118`**) and `R112` (display `SDO` isolation; **must not be fitted while MX-8 is relied on**). **The design now has zero unexplained DNP** |

### Blockers added or changed by FBV2-S1-002 (2026-08-23)

| # | blocker | status |
|---|---|---|
| ~~**B-09**~~ | GPIO3 has no strap-defining pull; a CMOS input floats at reset | **CLOSED 2026-08-23 by D-109.** `R110` 10 kΩ pull-down at the MCU pin. LOW is the only correct level — GPIO3 = 1 would select external JTAG on GPIO39-42, which are the I²S bus. BMI270 `INT1` is bound to push-pull active-high; open-drain is forbidden on this pin |
| **B-43** | **TPS61169 `CTRL` internal-pull specification not retrieved** — TI's PDF text layer would not extract this session | **OPEN, low.** The GPIO46 strap is safe for any internal pull-up ≥ 30 kΩ with `R108` = 10 kΩ, and `R109` 0 Ω is the isolation escape. Confirm at FBV2-S2 |
| ~~**B-44**~~ | BMI270 `INT` pad drive current not retrieved | **CLOSED 2026-08-23 by D-136.** `BST-BMI270-DS000-08` Rev 1.6 Table 1: **`IOH`/`IOL` ≤ 2 mA, `VOH` ≥ 0.8·VDDIO, `VOL` ≤ 0.2·VDDIO.** The `R18` + `R110` load draws **323 µA — 6× inside spec** — and GPIO3 settles at 3.23 V. The 47 kΩ fallback is not needed. |
| **B-59** | **`ER-TPC035-6` touch-flex I²C pull-ups unknown.** If the module carries its own, the effective internal pull-up drops below 2.2 kΩ | **OPEN, low.** Direction is safe (faster edges); sink current stays inside every device even at a 1 kΩ equivalent. **First-article measurement** |
| **B-65** | **The `+3V3` / `SYS` IR source-select link listed in `ARCHITECTURE.md` cannot be built without a sheet-01 edit.** `BQ25185_SYS` is a sheet-01-local net, not published hierarchically. Building it is one hierarchical label on sheet 01 plus a DNP resistor on sheet 07 | **OPEN, low.** A provision, not a fix — `+3V3` is the analysed-correct choice (D-156) |
| **B-66** | **TSAL6100 ±10° beam ergonomics unvalidated.** The narrow cone is the one real risk in the emitter choice | **OPEN, medium.** First article: if aiming is fussy, fit the **TSAL6200** — a proven drop-in with identical package, `VF` and `IFM`, so `R24` is unchanged and `R123` trims the current back up |
| **B-61** | **`AS02008MR-LW152-R` availability not confirmed from a live listing.** PUI's product page would not render here after three attempts and Digi-Key search is bot-protected. The datasheet is served live from PUI's API today and the sibling `AS02008MR-R` is catalogued — but **D-096 asks for a live listing and that is not one** | **OPEN, medium.** Procurement, before the BOM gate |
| **B-62** | **AWG #32 into JST PH `SPH-002T-P0.5S` is the small end of the #32–#24 applicable range.** Inside spec, but a crimp pull test belongs at first article | **OPEN, low.** First article |
| **B-63** | **The PCB acoustic hole and the pad-4 paste pullback are not in the microphone footprint.** Ø1.05 mm NPTH concentric with pad 4, and a stencil aperture kept back from the hole edge so solder cannot wick into the port | **OPEN.** PCB stage / FBV2-S2 |
| **B-64** | **The PCB still carries `MK1` with the ICS-43434 footprint.** Part of the standing transitional state — the board is bit-identical to Beta-DM and matches no migrated sheet. Recorded so the microphone change is not lost when the PCB is redone | **OPEN.** FBV2-P1 |
| **B-60** | **`0x36` (MAX17048) and `0x38` (FT6236) are not datasheet-cited.** Every Analog Devices and FocalTech fetch failed here — analog.com timed out, the Mouser mirror returned HTML, focuslcds returned 403 | **OPEN, low.** Consistent across every prior audit and almost certainly right, but *almost certainly* is not this programme's standard. **A first-article bus scan closes it in ten seconds** |
| ~~**B-45**~~ | **CLOSED 2026-08-23 (D-200) — STALE.** `R61`/`R62` 100 Ω plus two `D2` TVS channels landed at FBV2-S1-009. Original text: **`NATIVE_A` / `NATIVE_B` have no protection yet.** D-090 requires 100 Ω series on both native pins plus a low-capacitance TVS array; both belong beside the connector | **OPEN, high.** These are the only two contacts with a direct MCU path. Sheet `09` work |
| **B-27** | Recovery branch is not tolerant to every single failure | **AMENDED 2026-08-23 by D-105.** The ceiling is **≈ 15.9 mA nominal / ≈ 16.6 mA worst case**, not ≈ 13 mA — 680 Ω was the value that produced the old figure. Still ~0.0066 C, still bounded, still self-annunciating |
| **B-15** | No charge or VBUS telemetry reaches the MCU | **STILL OPEN, unchanged by this task.** The crossings are sheet `08`/`09` |

### Blockers added or changed by FBV2-S1-001 (2026-08-23)

| # | blocker | status |
|---|---|---|
| **B-41** | **`NFC_SUPPLY` has no consumer.** The 3.3 V-FIT / 5 V-DNP source select exists on `01_POWER_TREE`, but `U9` `VDD` and `VDD_TX` are still on `NFC_5V_PA_PENDING` — the Beta-DM arrangement — because they live on sheet `04`, which FBV2-S1-001 was not authorised to modify | **OPEN, high.** The v2 NFC supply architecture is **half implemented**. First item of the sheet-`04` migration |
| **B-42** | **The NFC source select is mutually exclusive by FIT STATE ONLY.** Fitting both `R106` and `R107` shorts `+3V3` to the 5 V boost output. Nothing in copper prevents it | **OPEN, low.** Inherent to a 0 Ω source-select and exactly the mechanism D-049 asks for, but it must become an assembly-note and fab-drawing requirement |
| ~~**B-01**~~ | Reverse-polarity protection does not exist; `BAT_CONNECTOR_P` is a single-pad net | **CLOSED AT SCHEMATIC LEVEL 2026-08-23.** `BAT_CONNECTOR_P` = `J4.1` + `F1.1` + `TP34.1`; the full P2 chain to `BAT_PROTECTED_P` is captured. **Not closed at board level** — the PCB is still the Beta-DM board |
| **B-15** | No charge or VBUS telemetry | **STILL OPEN, advanced.** The `VBUS_PRESENT` divider (2.97 V at VBUS 5.0 V) now exists, as do `BQ25185_STAT1/2` and `ACC_POWER_FAULT_N`. **CLOSED FOR CHARGE STATE 2026-08-23 (FBV2-S1-008, D-170):** `BQ25185_STAT1` and `BQ25185_STAT2` now land on `U2` P05/P06 with 10 kΩ pull-ups, and the Table 7-2 decode is recorded. **`VBUS_PRESENT` and `MAX17048_ALRT_N` remain test-point only** — D-089 had pencilled them onto `U2`, but `TOUCH_INT_N` and `SD_CARD_DETECT_N` arrived later and outrank them (D-166). **Twelve `U23` pins are free** if that is revisited, so it is a wire and a firmware change rather than a respin |
| **B-03** | Footprint audit not performed | **STILL OPEN — AND IT IS THE FBV2-S2 EXIT-GATE FAILURE.** 2026-08-23: **15 of 28 critical footprints are manufacturer-drawing verified with a cited document number and revision** (13 project-local plus `U11` BQ25185, checked against TI drawing 4226298/A, plus the PCAL9535A SOT355-1). **EIGHT remain traceable-but-unread**: ESP32-S3-WROOM-1, GCT USB4105, JST ACH, JST PH, PTS645, JS102011SAQN, the MAX98357A TQFN exposed pad and the NFC crystal. **They block fabrication release, not placement.** Earlier text: **STILL OPEN, widened.** `U18` LTC4368-1 had been assigned a **DFN-10 exposed-pad** footprint against the locked *"no bottom-terminated parts"* package policy; corrected to MSOP-10. The land pattern itself is still unverified, and `U18`-`U22`, `Q2`-`Q9`, `D9`-`D12`, `F1`, `R75`, `L4` all join the FBV2-S2 list |

### Pending decisions opened by FBV2-S1-001

| # | item |
|---|---|
| **P-20** | **`R95` = 680 R against a locked `R_LIM` of 560 R.** Recovery injection falls from ≈ 8.4 mA to **≈ 6.9 mA** into a 0 V pack, moving the wrong way against **B-26**. Keep 680 R or restore 560 R |
| **P-21** | **`OV` trip captured at 5.05 V** (`R77` 4.02 M / `R78` 442 k) against a documented *"divider ≈ 4.6 V"*. Confirm the captured number or correct it |
| **P-22** | The standing *"do not generate or modify KiCad files automatically"* rule was overtaken — this capture was scripted, then verified with `kicad-cli` ERC and a netlist export. **Ratify or reinstate.** Recorded in place, not treated as repealed |

### Blockers added or changed by FBV2-PWR-001 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-20** | Dead-cell lockout created by the reverse protection | **STILL OPEN — P-11.** Now fully characterised: LTC4368 VIN UVLO 1.8/2.2/2.4 V; VOUT is a *sense* input and its charge-pump role only applies above ~5 V, so **system-side power cannot run the controller**. No inherent recovery path exists. Four candidate architectures analysed; **B recommended** |
| **B-21** | Shorted pass FET reproduces the guarded fault | **BOUNDED, not closed.** Clamp + fuse reduce the excursion from ≈−3.7 V to ≈−1 V, still ~3× the −0.3 V DC abs max. Residual is **P-12** |
| ~~B-22~~ | Latch-off vs hot-insertion inrush | **CLOSED.** Inrush is a designed parameter; latch-off applies to forward OC only |
| **B-23** | PCAL9535A pin table not obtainable from a primary source | **STILL OPEN, but no longer blocking.** Architecture locked by D-061; four secondary-sourced facts deferred to the land-pattern audit |
| ~~B-24~~ | SX1262 DIO1 level-hold unverified | **CLOSED** — confirmed verbatim from Semtech §13.3.4 (Rev. 1.2; re-confirm against V2.2 pre-fab) |

### Blockers added or changed by FBV2-ARCH-002 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-20** | **Dead-cell lockout created by the reverse protection.** Below LTC4368 UVLO (1.8–2.4 V) both gates are off and the body diodes are anti-series — a ~0 V pack can never be recharged. | **OPEN — P-11. Blocks FBV2-A1.** |
| **B-21** | **Shorted pass FET reproduces the guarded fault.** Without a fuse + Schottky clamp, −3.0 to −4.35 V lands on BQ25185 BAT against a −0.3 V abs max — a 10–14× DC violation. | **Mitigation identified** (fuse + clamp, required not optional); survivability of the residual excursion is **P-12**. |
| **B-22** | **Latch-off vs hot-insertion inrush unreconciled.** | **OPEN — P-13. Blocks FBV2-A1.** |
| **B-23** | **PCAL9535A pin table not obtainable** from a primary source (NXP 404, Digi-Key 410, Mouser HTML). | **OPEN.** Blocks criterion 2. One document read. |
| **B-24** | **SX1262 DIO1 level-hold behaviour unverified** (Semtech domain did not resolve; Mouser mirror returned HTML). | **OPEN.** Blocks criterion 3. Read the SX126x **and** E22-900M22S IRQ sections. |
| **B-25** | **Permanent raw `+3V3` connector pin** — unprotected always-live tap; defeats whatever is fitted on the switched pin. | **CLOSED by D-057** — pin removed from the 20-pin map. |
| ~~B-18~~ | TPS22918 lacks reverse-current blocking | **CLOSED by D-058** — replaced with TPS22950C (RCB confirmed for the C variant). My earlier TPS22913B/C suggestion was **wrong** — DSBGA-only and no current limit. |

### Blockers added or changed by FBV2-ARCH-001 (2026-08-22)

| # | blocker | status |
|---|---|---|
| **B-17** | **NFC supply topology undecided (P-10).** With TPS61023 true load disconnect confirmed, disabling the boost leaves VDD = VDD_TX = 0 V while VDD_IO = 3.3 V — unauthorised by DS12484 Table 119 (VDD min 2.4 V). | **OPEN — CTO decision.** N1 (3.3 V-only, delete the boost) recommended. |
| **B-18** | **`TPS22918` has no reverse-current blocking.** Datasheet confirms the integrated body diode conducts VOUT→VIN. An externally powered accessory can back-power `+3V3` through `ACC_3V3_SW`. | **OPEN.** Replacement identified (TPS22913B/C class); exact MPN needs a page-cited datasheet check. |
| **B-19** | **`NFC_IRQ` must never move to GPIO46.** A latched-high IRQ would block Joint Download Boot and make ROM-download recovery conditional on NFC state. | **CLOSED as a design rule** — recorded so it cannot be reintroduced. |
| ~~B-11 / B-12~~ | GPIO18/GPIO38 documentation mismatch and LoRa wake | **Mismatch still to fix in migration.** The *wake* consequence is retired by D-041 — LoRa deep-sleep packet wake is not a v2 requirement. |
| **B-16** | Field Slate v5 §5 lists phantom Volume controls | **Still open.** Needs a CTO-approved text correction. |

**Retired by verification:** B-07 (see above). **Partially advanced:** B-03 — `U9`'s
33-pad footprint mapping is now verified correct against three independent
DS12484 tables; every other footprint remains unverified.

---

## Change log for this file

| date | change |
|---|---|
| 2026-08-24 | **FBV2-EXP-001. Expansion ecosystem compatibility and pre-routing architecture AUDIT = PASS. AUDIT ONLY — NO AUTHORITATIVE HARDWARE CHANGE, NO PROGRESS EARNED; overall stays 74%.** **THE 24-LINE SIDE HEADER DOES NOT FIT THE CURRENT FLOORPLAN, AND THE NUMBER IS EXACT.** A right-angle THT socket puts its tails **6.5–6.9 mm inboard of its own mating face** (Sullins 1-row RA drawing 10493), so the tail row lands at x ≈ 63.5 — **inside `BATTERY_SHADOW`, which forbids any through-hole lead**. **Requirement: (board right edge − battery right edge) ≥ 7.83 mm; today 4.00 mm; SHORTFALL 3.83 mm.** Above the battery the wall offers **41.00 mm** against a **61.47 mm** body — a 1 × 15 is the largest that fits and leaves nothing for Qwiic or POWER. Left wall = 433 flex + mandatory coax channel; bottom = USB-C/microSD/both radios; top = IR pair + SMA. **All rejected on measurement.** **TWO 1 × 12 REJECTED ON GEOMETRY:** both Samtec and Sullins build the body **N × 2.54 + 0.51 mm**, so two butted bodies sit **3.050 mm apart against a 2.540 mm pitch — 0.510 mm interference**; they cannot form a continuous 24-grid, need **5.59 mm MORE** wall than one 1 × 24, and add a wrong-group mis-plug mode. **RECOMMENDED: one Samtec `SSQ-124-02-G-S-RA` (same manufacturer as the present `J5`; 01–50 positions/row, `-S` single row, `-RA` right angle, body 61.47 mm, 6.3 A/pin, accepts .025″ square post) + one `JST SM04B-SRSS-TB` Qwiic (SH 1.0 mm, 1 GND / 2 3V3 / 3 SDA / 4 SCL), CONDITIONAL on E-1 PCB 70 → 72 mm (already `FBV2_PCB_MAX_MM`, enclosure unchanged) and E-2 battery 60 → 57 mm, ≈ −5 % capacity.** **Sullins `PPTC241LGBN-RC` verified and deliberately NOT baselined — 0 stock, non-RC obsolete, sibling factory-order at 1,000 MOQ / 11 weeks: the third catalogue-part-is-not-a-stocked-part trap after Harwin M20 and the Amphenol pigtail.** **ALL 24 FUNCTIONS RETAINED**; recommended **ORDER-A** puts `3V3/SDA/SCL/GND` at pins 3-4-5-6 and **both 5 V contacts at the two physical ends with GND as their only neighbour — no 5 V pin is adjacent to any signal, removing two adjacencies the present order has**. **A closed-end 62.5 mm recess gives 1.54 mm of play against a 2.54 mm pitch, so a one-position shift is physically impossible — no proprietary shroud, and the asymmetric key (D-097) becomes unnecessary.** **QWIIC ADDS ZERO COMPONENTS:** it attaches at `EXT_SCL`/`EXT_SDA`, downstream of the 22 Ω resistors and at `D2`'s clamp, inheriting the `TCA4307`, the 1.5 k pull-ups, the series R and the TVS; **power is `ACC_3V3_SW` because `U16`'s own VCC already is**, and `ACC_5V_SW` is never exposed. Budget ≈ 55–75 pF for three daisy-chained boards against ≤ 200 pF — **no mux, no repeater.** **MANUAL/BENCH POWER NEEDS NO HARDWARE CHANGE FOR EITHER RAIL:** traced pin by pin, `ACC_DETECT_N` reaches nothing but `U3.P17`, so detect gating is entirely firmware, while ILIM, RCB, TSD and FLT stay in hardware; permanent 5 V remains physically impossible. **BOOT → bottom edge** (a measured 11.04 mm window; `SW1` is SMD; 14 mm free enclosure span for the tool hole); **lower-left BOOT REJECTED ON RF** — that wall *is* the 433 flex region and the mandatory coax channel. **0x50 stays an optional single-accessory convention needing a firmware signature, no PCB change.** **PM-2 AND THE NEW HEADER WANT THE SAME CORNER**, so a **COMBINED RE-FLOORPLAN** is recommended — outline and reservations, then the right-wall stack, then PM-2, PT-1, PM-1, PM-3, P2-R1 — and **FBV2-P1 would have to be re-issued** because the outline change invalidates its PASS. **VALIDATION: PCB blob `22c03150…` identical to HEAD; ERC 27 / 0 errors; DRC 26; 499 unrouted; 0 tracks / 0 vias / 0 pours; outline 70 × 148 unchanged; collisions 0; `p1_regression`, `dru_probe`, `netclass_probe`, `fork_equivalence` all PASS; Beta-DM, the frozen Beta tree and `hardware/beta/mechanical/` untouched.** **D-081 / D-083 / D-093 / D-097 REMAIN IN FORCE — supersession is PENDING CTO / OWNER RULING.** |
| 2026-08-24 | **FBV2-EXP-002. FBV2-P1 RE-ISSUED = PASS. FBV2-P2 ENTRY = PASS. PM-1, PM-2, PM-3 and PT-1 ALL CLOSED. NO PROGRESS EARNED — P1 was RE-earned, not newly earned; overall stays 74%.** **THE BATTERY GATE RAN FIRST AND CHANGED THE STORY:** before any authoritative file was touched, the 57 × 75 × 8 mm envelope was checked against **PKCELL `LP785060` (7.3 × 50 × 60 mm, 2500 mAh typ / 2375 min, PCM fitted, JST-PH lead)** and **`LP755070` (7.5 × 50 × 70 mm, 3000 mAh min / 3050 typ, PCM fitted, 4.275 V overcharge with 2.50 V resume, 500 cycles to 80%)**, both manufacturer datasheets. **THE PREDICTED −5% PENALTY DOES NOT MATERIALISE — both candidates are 50 mm wide, so the 57 mm limit binds neither, and `LP755070` sits at the TOP of D-071's 2500–3000 mAh target.** **`J5` → Samtec `SSQ-124-02-G-S-RA` 1 × 24 2.54 mm FEMALE RIGHT-ANGLE** (same manufacturer as the BCS it replaces; 01–50 positions/row, `-S` single row, `-RA`, body 61.47 mm, mates .025″ square post, 6.3 A/pin) with **`J8` `JST SM04B-SRSS-TB` Qwiic / STEMMA QT added for ZERO components** on `EXT_SDA`/`EXT_SCL` downstream of `U16` and the 22 Ω pair at `D2`'s clamp, powered from `ACC_3V3_SW` because **`U16`'s own VCC already is** — no buffer, no mux, no repeater, no extra pull-ups, no second TVS, and `ACC_5V_SW` never exposed. **ALL 24 FUNCTIONS RETAINED; NOT ONE PROTECTION PART REMOVED; the schematic change is a footprint swap plus a sheet-09 pin re-map — no net created, deleted, split or merged.** **ORDER-B SUPERSEDES ORDER-A BECAUSE IT IS SAFE UNDER 180° REVERSAL BY CONSTRUCTION: 5V↔5V, GND↔GND, 3V3↔3V3 and 3.3 V logic ↔ 3.3 V logic everywhere else — POWER-TO-SIGNAL MAPS UNDER REVERSAL: ZERO**, proved pin by pin from the netlist; the one-position slip stays impossible (60.96 mm male body, closed-end 62.5 mm recess, **1.54 mm of play against a 2.54 mm pitch**) and **D-097's asymmetric key is no longer needed.** **BOARD 70 → 72 mm SYMMETRICALLY** so every part shifted +1.0 mm in X and every part-to-part relationship is preserved; enclosure untouched; wall gap 2.5 → **1.5 mm both sides, the rule met EXACTLY**; **`ANT433_REGION` RE-DERIVED rather than shifted** because its 2.2 mm reservation never described anything real — the flex is 0.28 mm thick and bonded flat to the wall. **BATTERY 60 → 57 mm MAX: that 3 mm is the entire price of the header**, since a right-angle socket puts its tails 6.53 mm inboard of its mating face and needs (board right − cell right) ≥ 7.83 mm against 4.00. Measured: tail row X 65.900, **1.100 mm clear of the cell**, mating face 0.430 mm outboard with **1.070 mm to the cavity wall**. **PM-1: 12.96/28.56/30.50/45.90 → 4.80/4.34/3.86/3.79 mm**, each a COMPLETE POWER CELL — `D8`, which sat **45.7 mm from its own inductor**, is now 3.56 mm from `U17`, so the 39 V open-LED loop is local instead of a 76 mm perimeter 13 mm from the microphone. **PM-2: the 1.5 A path is 116.7 → 30.86 mm** as one monotonic column, Kelvin pair 6.60 mm, **NO FET, threshold, divider or recovery branch altered — D-049 UNTOUCHED**; **`J4` is the one part that could not join it and that is recorded, not hidden** — the left margin is also the coax lane, which parts ≤ 2.0 mm may share but a 5.75 mm connector cannot, so it sits at the column's head 8.59 mm from `F1`. **PT-1: `U11` out of `BATTERY_SHADOW` to (67.500, 70.200), 3.5 mm clear of the cell.** **B-34 RE-ESTIMATED, NOT CLAIMED ZERO: 38.8 → 15.2 mΩ, ≈ 53 mW better at 1.5 A — it IMPROVES MATERIALLY BUT DOES NOT CLOSE**, because its 0.70 W is dominated by the BATFET's 115 mΩ, which this task correctly did not change. **PM-3: the NFC arms mirror at Δx = 0.000 mm and arm-length Δ = 0.000 mm**, `Y1` 5.40 mm from `U9` with its load caps local, **no locked NFC value changed**. **`BOOT` → (28.300, 6.000) FRONT face** in the measured 11.04 mm window, tool hole in the FRONT wall so it clears both the card path and the USB-C plug; **LOWER-LEFT REJECTED ON RF.** **POWER stays on the right wall. Retention still TWO M2 — widening the board did not buy a third and none was chased.** **NFC loop ↔ `J5` metal improves 5.490 → 9.155 mm; NFC pair 41.73 → 31.23 mm; display offset 3.34 → 2.34 mm.** **`J5`'s courtyard overhangs the right edge by 0.975 mm — that is what a right-angle socket is FOR — and `p1_regression` now tests it explicitly instead of counting it as a part off the board.** **DRC 26 → 1** (the `MK1` artefact accepted at D-227, still NOT excluded and NOT suppressed); **ERC 0 errors / 27 warnings, histogram identical; 499 unrouted; ZERO tracks, ZERO signal vias, ZERO electrical pours; ZERO placement collisions**; `p1_regression`, `dru_probe`, `netclass_probe` and `fork_equivalence` all PASS with the **BCS 2 × 12 footprint RETAINED in the library, not deleted**, as Beta-DM's part and the fallback. **ONE NEW OWNER ITEM — E-7: the 57 mm envelope is now the LOWER bound of what fits, not a target; both cells are 50 mm wide, leaving 7 mm of reservation unused. Recorded, not decided.** |
| 2026-08-24 | **FBV2-P2-000. FBV2-P2 ENTRY GATE = FAIL on one criterion of thirteen. NO PROGRESS EARNED — overall stays 74%, FBV2-P1 = PASS unchanged.** **THE INHERITED RULE SET WAS NOT MERELY STALE: 22 OF 71 RULES COULD NEVER FIRE.** `.kicad_dru` referenced **39 rule areas and the board contained NONE of them** — not only the E6 pockets P2-O5 named, but **every RF-band rule, every E5/E4 corridor rule, the header reservation, the E2 button escapes and the ESP32 antenna rule**. KiCad's `intersectsArea()` returns **false** for an unknown name with no warning and no error, so a rule that can never fire looks exactly like a rule being satisfied. **Rebuilt to 64 live rules with a written RETIREMENT REGISTER (R1–R10) giving a reason for each of the 22 retirements**; the E6 escape-relief DOCTRINE is preserved in full even though its Beta-DM measurements are not. **`checks/dru_probe.py` is new and now fails the build if any rule reference or netclass pattern stops resolving — P2-O5 cannot recur silently** (D-233). **THE NETCLASS TABLE HAD BEEN LYING SINCE THE FORK:** `BAT_MAIN`'s pattern was the root-sheet path `/BAT_PROTECTED_P` while every v2 power net lives under `/01_POWER_TREE/`, so **it matched nothing and the highest-current net on the board — 1.5 A sustained — was routing at 0.20 mm**; `BAT_RAW`, `BAT_MID`, `BAT_SENSE` were in no class at all; `NFC_5V_PA` captured **no net whatsoever**; and **`ACC_5V_LX`, the `U21` boost SWITCH NODE, had never been in `SWITCH_NODE`**. **14 classes → 18, 62 patterns → 57, every surviving pattern now matches at least one net; four dead classes retired without weakening any net's parameters** (D-234). **RETENTION LOCKED AND D-226 CLOSED: two M2 is ACCEPTABLE**, no component moved, with rails + four rear non-metallic ribs + two screws + the `J5` backing boss, and three stale mechanical-spec entries corrected in the same pass (D-232). **ROUTING STRATEGY FROZEN:** stackup retained and **layer roles now ENFORCED BY RULE**, one solid In1 with a single authorised void (the 6.5 × 44 mm ESP32 notch), **USB confirmed FULL SPEED at ≈ 40 mm on F.Cu with ZERO vias and no length matching**, SPI-A **63 % shorter** and SPI-B **21 % shorter** than accepted Beta-DM versions so neither gets damping, internal I²C given a derived **C_bus ≤ 161 pF** budget, and the `J5` escape measured at **10 crossings needed against 22 available on one layer** — no nudge required (D-235). **WHAT FAILS THE GATE: THREE ELECTRICALLY REQUIRED PLACEMENT MOVES, SURFACED NOT DECIDED (D-236).** **PM-1** — all four switching converters have their inductor **12.96–45.90 mm** off the IC, the backlight loop **≈ 76 mm around** switching to **39 V** on an open-LED fault, 13 mm from `MK1`. **PM-2** — the single-fault battery-protection block dispersed across three clusters over **96 mm**, with 2.2–3.65 MΩ trip nodes and a **≈ 20 µA gate node spanning 95.6 mm**; the Kelvin sense itself is sound and D-049 is not compromised. **PM-3** — the NFC matching arms differ by **10 mm before a track is drawn**. **All three are NEW and none existed in Beta-DM: P1 verified every MECHANICAL relationship by script, and nobody had yet looked at these blocks ELECTRICALLY.** **DRC 47 → 26** (all 21 `clearance` violations closed by naming the four vendor land patterns that cause them, no routing clearance weakened); **ERC 0 errors / 27 warnings, histogram identical**; **499 unrouted, ZERO tracks, ZERO signal vias, ZERO electrical pours**; `netclass_probe`, `p1_regression`, `fork_equivalence` and the new `dru_probe` all PASS; **Beta-DM, the frozen Beta tree and `hardware/beta/mechanical/` untouched.** **ROUTING DOES NOT BEGIN UNTIL PM-1, PM-2 AND PM-3 ARE RULED ON.** |
| 2026-08-24 | **FBV2-P1-002. FBV2-P1 PASSES. Overall 68% → 74% — the third twelve-gate pass.** **THE 915 FEED CLOSES ON MEASURED GEOMETRY: 138.48 mm routed** from `U8` IPEX (9.00, 16.60) up the left rear channel to the SMA at (5.00, 148.00), **7.42 mm minimum available bend radius**, **0.600 mm** at its tightest to the Ø58 NFC exclusion and **ZERO violations** against the 433 flex, the battery, the speaker cavity, the microSD card travel, the USB aperture, both IR windows, the barrier, the community recess and `J5`. **The fix was WIDTH, not length** — the SMA is locked to the top-panel left half and the NFC region owned the whole upper-left, so no cable length could ever have worked. **NFC becomes CIRCULAR: clear Ø48, metal exclusion Ø58, centre doc (30.800, 124.500)**, the 48 × 48 square retained only as the placement-tolerance envelope; **+6.30 mm in X is the entire 915 solution** (75 mm cavity − 58 mm exclusion − 12.1 mm of `J5` = 4.9 mm of lane, and only pushed hard right — loop-to-`J5` now **5.490 mm** against ≥ 5) and **−1.50 mm in Y** buys the SMA its margin. **The radial clearance was NOT reduced: the Ø58 circle is inscribed in the superseded 58 × 51 rectangle**, so only the four corners are reclaimed. **Cost stated plainly:** NFC clear ↔ battery 3.50 → **2.00 mm, still ZERO overlap**; battery inside the Ø58 1.50 → 3.00 mm (D-224). **`U7`/`U8` SWAPPED for zero plan area** (identical footprints) and the **SMA moved x 12.000 → 5.000**, improving both SMA↔IR rules (D-222). **CABLE RE-SELECTED: RF Solutions `CBA-UFLSMA20IP`, 200 mm, IP67, RG-178, U.FL R/A → SMA(F) bulkhead** — ACTIVE, **296 in stock at DigiKey**, spare **46.52 mm** beyond the 15 mm service loop, loss ≈ 0.4 dB, **U.FL↔MHF1 COMPATIBLE**; **and it fixes a procurement risk — the superseded Amphenol part was 0 in stock on a 12-week lead** (D-223). **THREE FINDINGS THE PREVIOUS PASS HAD WRONG:** the ESP32 0.2 mm thermal vias were **never in violation** (global floor is 0.20 mm, not 0.30) — the twelve errors were **`copper_edge_clearance` on `J5`**, fixed by a **0.070 mm** nudge, with JLCPCB capability verified live and a **narrowly scoped guard** added that does **not** lower the global minimum (D-228); P1-001's **`BOSS2` was inside the mandatory opaque IR barrier and was never legal** — corrected, and the barrier **widened 3.0 → 5.0 mm** to fill the inter-window gap and carry the boss (D-226); and writing the IR forming requirement showed **the formed `TSAL6100` dome would have finished 1.2 mm OUTSIDE the shell** — `D1` moved to (50.750, 141.400), `TP39`/`R123` 1.750 mm, `U6` fits unmoved (D-229). **`MK1` PADSTACK FIXED, `padstack_invalid` 2 → 0**, with the Ø1.05 NPTH, the ID 1.05 / OD 1.65 annulus, the 0.10 mm paste pullback, the keep-out and the mic location **all unchanged** — and **no fake plated through-hole** (D-227). **B-52's floorplan half CLOSED** on the Ø9.238 hex / Ø10.2 washer envelope; only an enclosure-CAD residual remains (D-230). **DISPLAY: 3.34 mm left offset ACCEPTED as intentional and the Z stack NOT spent** — P1-001's raise-the-display recommendation is rejected and withdrawn (D-225). **RETENTION: the outline yields TWO legal M2 positions, not three — ESCALATED**, with support completed by edge-capture rails and four reserved rear rib pads that need no PCB holes (D-226). **DRC 64 → 47, every one classified; `padstack_invalid` 2 → 0, `copper_edge_clearance` 12 → 0, `lib_footprint_issues` 3 → 0; nothing fake-cleaned — no exclusion, no severity change, no relaxed global rule.** ERC 27 / 0 errors, histogram byte-identical; schematic connectivity UNCHANGED; **placement collisions 0**; **ZERO tracks, ZERO vias, ZERO pours, 499 unrouted.** `netclass_probe` PASS, `fork_equivalence` PASS with Beta-DM and the frozen Beta tree untouched. **FBV2-P2 has not begun.** |
| 2026-08-24 | **FBV2-P1-001. FBV2-P1 DOES NOT PASS. Overall stays 68% — no progress awarded.** **PCB modification authorised for the first time; the v2 board is no longer Beta-DM.** The board was **rebuilt from the current nine-sheet schematic**: pre-P1 file stripped to header, layer stack, `general` and `setup` (design rules byte-identical), **all Beta-DM footprints, tracks, vias, zones and graphics removed**, **321 footprints re-created one per component**, **224 nets / 991 pads** applied, plus a **70.000 x 148.000 x 1.6 mm** outline — **the TARGET, not the 72 x 152 maximum** — 13 named mechanical regions, 4 copper rule areas and 3 M2 NPTH bosses. **F.Cu 120 / B.Cu 201.** **Datum: lower-left board corner, X right, Y up; `Y_kicad = 148.000 - Y_doc`.** **SIX RULINGS RECORDED (D-214...D-219):** `F.Cu`=FRONT / `B.Cu`=REAR with **`MK1` on B.Cu listening forward through the board, 1.21 mm clear of the LiPo and 67.42 mm from the speaker** (**O-1 closed**); rear packing **NFC -> battery -> speaker, 48+75+20 = 143 mm in 155 mm** with **zero NFC/battery overlap** (**O-2 closed as a FALSE conflict**); **USB/microSD 16.40 mm BODY edge-to-edge** against the new >= 8 mm rule (**O-4 closed**); **internal 915 whip storage DELETED — the locked `TI.92.2113` is 198 mm against a 172 mm internal diagonal and never fitted; the freed LEFT wall restores D-118's LEFT/LOWER-SIDE 433 flex placement** (**O-6 closed**). **ZERO placement conflicts** on a side-aware review of all 321 courtyards; FPC margin **15.8 mm**, IR TX-RX **15.00 mm**, SMA-IR **39.55 mm centre / 31.05 mm edge**, NFC **48 x 48**. **THE GATE FAILS ON ONE CRITERION (D-218): the 100 mm 915 pigtail is SHORT BY ~90 mm** — every part taller than ~1.2 mm is excluded from the upper half, so `U8` sits at the bottom rear and the routed run is **~190 mm**; even the superseded 150 mm is short by ~40 mm, **and no length fixes it while the SMA is locked to the top-LEFT behind the NFC zone**. Recommended: **raise the display support ~3 mm into Column A's 9.9 mm of unused Z.** **ONLY 3 OF 6 M2 BOSSES CLOSE** (D-216) — no 6 mm side strip exists between the display, battery and NFC zone. **FOUR NEW ITEMS (D-221): the display cannot be centred (3.34 mm left of centre because `J5` must sit beside the panel band); `MK1`'s ring pad fails KiCad 10's padstack validator; the stock ESP32 footprint's 0.2 mm thermal vias break the 0.3 mm min-hole rule; and `netclass_probe` had been measuring Beta-DM net names — expectation corrected to the schematic, guard unchanged and still passing.** **ERC 27 -> 27, zero errors, histogram byte-identical. Schematic connectivity UNCHANGED. ZERO tracks, ZERO vias, ZERO pours; 499 unrouted, which is correct at P1.** `fork_equivalence` now reports the v2 PCB as **changed — the intended outcome of P1** — and confirms **Beta-DM and the frozen Beta tree untouched.** |
| 2026-08-23 | **FBV2-MECH-002. NO PROGRESS EARNED — overall stays 68%, FBV2-S2 = PASS unchanged.** **This was a reconciliation and sign-off task, not a design phase.** **Two procurement substitutions SIGNED OFF AND ADOPTED**: `F1` → **Littelfuse `0466005.NRHF`, `C57525`, 29,328 in stock, JLC Extended** — the halogen-free ordering option of the same 466/Nano2 family, and **the two LCSC records carry a character-for-character identical parametric string** (D-210); `D10`–`D12` → **Diodes Inc `BAT54WS-7-F`, `C124205`, 46,819 in stock, JLC Extended** (D-211). **THE "SERIES PAIR" SOURCING ERROR IS CORRECTED PROGRAMME-WIDE: `BAT54WS` IS NOT A SERIES PAIR** — SOD-323 is a two-terminal package, every `BAT54WS` in the LCSC library from eight manufacturers is catalogued **1 Independent**, and `D10`/`D11`/`D12` are each one two-pin `Device:D_Schottky` on a two-pad footprint, with `D10`/`D11` forming the ratiometric pair as **two separate components**. **The design was never wrong; six documents were.** `BAT54W,115` stays rejected **because it is SOT-323 (SC-70) — a footprint mismatch, not a diode count.** **Electrically verified, no material mismatch**: the bridge comparison `(BAT_RAW + V_F11 − V_F10)/2` **cancels the absolute drop** and runs at **≈1.1 µA through 4.4 MΩ**; `D12` sees **≈16.6 mA worst case against 100 mA — 6×**, and D-105's 5–10 mA band **needs no revision**. **Consignment 11 → 9 part numbers; CLASS D IS EMPTY; still exactly two hand-soldered parts per board (`J5`, `D1`).** **MECHANICAL AUTHORITY RECONCILED (D-212)**: **NFC zone 45×45 → 48×48 LOCKED** (stale in four places including the machine-readable block); **every current FH12/FH52E land-pattern and second-source claim REMOVED** — FH69 dedicated, not drop-in, single-source, **machine-placeable**; **`J1` is NOT manual assembly**; speaker Z column **4.0 → 3.0 mm (13.6 → 12.6)**; **"26 to 20 pins" → 24 contacts 2×12**; **"removes the RGB nets" → a front RGB `D13` was ADDED**. **915 SMA↔IR spacing TRACED, NOT resolved by preference: BOTH rules are current** — ≥15 mm **centre-to-centre** (FBV2-MECH-001) and ≥8 mm **edge-to-edge** (D-120), **re-asserted together by M-13**; the real defect was that neither said what it measured between, and both now carry a datum in a new §8.1. **B-52 stays OPEN, no CAD created.** **New handoff: `mechanical/P1_FLOORPLAN_INPUTS.md`, 120 constraints, no invented coordinates.** **SIX BLOCKERS SURFACED FOR CTO RULING (D-213)**, the two sharpest being arithmetic: **the rear face is over-constrained by ≈8 mm** (battery 75 + NFC 48 + speaker Ø20 + 20 mm separation = 163 in a 155 mm cavity) and **the internal antenna storage channel cannot hold the locked `TI.92.2113` whip** (198 mm against a 172 mm internal diagonal). **ERC 27 → 27, zero errors, histogram identical. Netlist 224 nets / 991 nodes IDENTICAL. Schematic diff PROPERTY-ONLY. PCB byte-identical and still bit-identical to Beta-DM.** |
| 2026-08-23 | FBV2-S2-002. **Overall raised 62% -> 68%. FBV2-S2 = PASS** - the second twelve-gate pass. **B-03 CLOSED**: all eight remaining Tier-2 footprints compared dimension-by-dimension against retrieved manufacturer drawings, 23 of 28 now Tier 1; the **MAX98357A "contradiction" dissolved** when Maxim land pattern **90-0032 Rev E** turned out to specify **one land for `T1633-5`, `-5C` and `-7C` together**, so **no project-local footprint was created**; `Y1` locked (`C362365`, 3,421 in stock) with an **exact** land match (D-201, D-202). **B-63 CLOSED**: the microphone acoustic port is now **drawn** - Ø1.05 NPTH from the drawing s own ring ID, paste pulled back 0.10 mm as a declared stencil choice, keepout and bottom-port orientation recorded as **M-14** (D-203). **B-70 CLOSED**: Murata **`LQW18AN39NG80D`** - and **the DCR is a first-order term**, dropping network Q 25.3 -> 21.4 against `R_q` = 1.1 Ohm, so the antenna must be tuned with this exact part fitted and **the first lever is `R_q`, not 39 nH** (D-204). **B-54 CLOSED**: DS12484 Rev 3 retrieved through a mirror; **`I_AL-AM` max 26 mA + ~60 mA driver -> allocate 100 mA**, the **350/500 mA abs-max figures deliberately NOT used**, TPS63020 **63-71 % of 2 A**, with a **binding guard rail** on any `C_s` move to 270 pF (D-205). **B-71 CLOSED**: all 46 MPNs classified against live JLCPCB parts-API state, **65 `LCSC` fields written into the schematic**, **two hand-soldered THT parts per board and zero hand-placed fine-pitch**, ten stock shortfalls handled by **consignment**, **six substitution traps caught** including `BAT54W` offered for `BAT54WS` (~~single vs series pair~~ - ***CORRECTED 2026-08-23 by D-211: `BAT54WS` IS NOT A SERIES PAIR.* SOD-323 is a two-terminal package and `D10`-`D12` are each ONE independent diode; `BAT54W,115` is wrong because it is SOT-323 (SC-70) - a FOOTPRINT mismatch.**) and a clone for the **battery reverse-polarity pass FETs**; **`J1` improves to machine-placed** (D-206, D-207). **O-8 CLOSED**: Taoglas **`TI.92.2113`** verified against SPE-19-8-076/A - and **the marketed "2 dBi" is the bent peak; average gain is negative in both orientations** (D-209). **Eight DNP parts still had no recorded reason and now do; the design has zero unexplained DNP** (D-208). **ERC 27 / 0 errors / 27, histogram identical.** **The schematic diff is PROPERTY-ONLY** - not one wire, label, junction, symbol or pin line changed. **PCB untouched and still bit-identical to Beta-DM.** |
| 2026-08-23 | FBV2-S2-001. **Overall HELD at 62% - FBV2-S2 = FAIL on two of fourteen exit criteria, and a failed gate awards no percentage.** **THE AUDIT FOUND A FABRICATION-BLOCKING DEFECT ON THE FIRST THING IT LOOKED AT: `U9` ST25R3916-AQET AND ITS TWELVE MANDATORY DECOUPLING CAPACITORS WERE STILL MARKED DNP**, against D-035 and D-055, while the crystal, the complete matching network, the antenna connector and the SPI wiring around them were all FITTED - **the first five boards would have carried a finished 13.56 MHz front end with no NFC chip on it**. All thirteen are now FIT (D-192). **Seventh consecutive sheet with a load-bearing inherited DNP, and the one that hid longest.** **`D-077`'S DISPLAY SECOND SOURCE DOES NOT EXIST** - both Hirose land patterns read: FH69 is 7.38 mm deep, 0.30 x 1.23 land, top-and-bottom two-point contact; FH52E is 4.6 mm, bottom contact only, and its own catalogue points at the FH12 pattern. **The drop-in claim is struck; `J1` is manual assembly** (D-194, B-47 resolved). **P-14 RESOLVED: the MAX17048 STAYS on `BAT_PROTECTED_P`** - it was never on `BAT_RAW`, and moving it to the LTC4368's precision sense node would trade a <= 2.6 % SOC error for a differential capacitance across the current-sense resistor (D-193). **O-7 CLOSED as Option A**: `R49` = `R50` = 1.5 k, published contract <= 200 pF at 400 kHz and <= 400 pF at 100 kHz, per UM10204 (D-191). **B-69 CORRECTED**: the 700 us soft start is specified at 10 uF and `C65`/`C66` give ~20 uF effective at 5 V bias, so the margin was 3.5x not 7x - **settle delay raised to >= 10 ms** (D-198). **B-68 CLOSED** - Wurth 74438357010 Isat 6.2 A against a 2.19 A peak; `L1` recorded at 1.4x as the tightest magnetics margin on the board; **two stale 'FOOTPRINT STILL BLOCKED' notes withdrawn** (D-197). **B-46 CLOSED and the guess was right** - Molex SD-502570-001 Rev A: card inserted = CLOSE, so LOW = card present (D-196). **B-49 and B-51 CLOSED** - Ebyte ships both modules with IPEX **and** stamp holes on the standard MPN, and the 915 MHz interface is **Amphenol `095-902-568-150`, ACTIVE**, one assembly carrying both the pigtail and the panel bulkhead (D-195). **P-01, P-04, B-45, B-53 closed as STALE** (D-200). **`R68`, a 0 R DNP with no note, is a BYPASS ACROSS `SW9` that would wire the unit permanently ON and defeat the only way to power down a hung board - now marked MUST STAY DNP**; `C21`/`C22` identified as dead pads; **six missing MPNs added, so every active and connector now carries an exact MPN** (D-199). **306 FITTED / 16 DNP / 0 unexplained DNP.** **B-70, B-71 and O-8 opened.** **FAILS: B-03 - 15 of 28 critical footprints drawing-verified, EIGHT traceable-but-unread; and B-71 - only 7 of 46 unique MPNs carry an LCSC code, so the JLC classification cannot be produced. Neither blocks placement; both block fabrication release.** ERC 27 / 0 / 27 unchanged; 0 duplicate refs, 0 unresolved footprints, 0 orphan nets, 0 same-text split labels; all seven PWR_FLAGs traced to a real supply. **PCB untouched and still bit-identical to Beta-DM. No PCB placement or routing was started.** |
| 2026-08-23 | FBV2-S1-009. Overall raised 55% → 62%. **FBV2-S1 = PASS — the first twelve-gate entry to pass since FBV2-A2.** Task gate **FBV2-S1-COMMUNITY = PASS**. **`09_COMMUNITY_HEADER` MIGRATED — THE SCHEMATIC MIGRATION IS COMPLETE, all nine sheets, and `fork_equivalence.py`'s "still Beta-DM" list is EMPTY.** Three CTO rulings recorded first: **O-6 RATIFIED** (`U23` + front RGB are locked architecture, **B-37 RETIRED** with 11 spare expander pins, D-175); **O-4 APPROVED** (`U16` TCA9517A → TI **`TCA4307DGKR`**, LCSC C880333, verified live at 3248 in stock, **FITTED** where the old part was DNP, D-176); **P-18 CLOSED with NO MUX** — the buffer solves electrical isolation, the address registry solves addresses (D-178). **SHEET 09 WAS REBUILT, NOT PATCHED, AND WAS HIDING TWO SERIOUS DEFECTS: `J5` contact 1 carried PERMANENT RAW +3V3 against D-057, and THE COMMUNITY PORT HAD NO POWER AT ALL** — `01:ACC_3V3_SW` and `09:ACC_3V3_SW` were different nets, the latter fed by a second, DNP TPS22918 (`U15`), and `01:ACC_5V_SW` reached nothing outside sheet 01 (D-189). Also removed: the 26-pin 2x13 **male** header, XGPIO10-13, `FAST_IO_GPIO43_HDR`, `RESERVED_NC`. **SIXTH CONSECUTIVE SHEET WITH A LOAD-BEARING INHERITED DNP** — `U16`, `R49`, `R50` and six TVS arrays. **Connector footprint re-derived from the Samtec RECOMMENDED PCB LAYOUT REV B FIG 3**: 2.54 mm in row, **7.87 ±0.05 mm row-to-row**, 0.71 mm PTH, 27.94 mm pin field — a vertical 2x12 is NOT a substitute; all 24 contacts verified pin by pin against D-084 (D-179, D-180). **THE INHERITED 4.7 k EXTERNAL I2C PULL-UPS COULD NEVER HAVE WORKED** — 796 ns against a 300 ns fast-mode budget at 200 pF; now **1.5 k = 254 ns**, with a published accessory ceiling of 200 pF at 400 kHz and 400 pF at 100 kHz (D-181). **Both current limits RE-DERIVED, not copied**: 3.3 V stays 1.5 k but the accessory-short case moved 86% → **89% of the TPS63020's 2 A** because of the IR transmitter and the RGB (D-184); 5 V stays 1.65 k, setpoint re-checked at 4.99 V, peak inductor current 2.19 A so **I_sat >= 3 A must be confirmed (B-68)**, and the rail is verified independent of USB VBUS and the NFC fallback (D-185). **5 V ENABLES SPLIT** — `ACC_5V_BOOST_EN` on `U3` P13 and `ACC_5V_SW_EN` on **`U23` P04**, each with its own 100 k pull-down (`R131` new), giving two independent series disconnects and making the boost start into a known 44 uF instead of an unknown accessory; the 5 ms settle delay is **7x the 700 us typical soft start, which has no published maximum (B-69)** (D-186). **B-08 CLOSED IN COPPER** — `Q10` 2N7002 with the source facing the connector so the body diode blocks with the rail off; the 5 V-injection residual is bounded at ~3 mA and is why `R66` is 330R (D-187). **ALL SIX TVS ARRAYS WERE DNP AND ARE NOW FITTED** — one `TPD4E1B06DRLR` MPN covers all sixteen exposed contacts at 0.7 pF, `TPD2E009DBZR` leaves the BOM, and **deliberately no TVS on either rail** because VRWM 5.5 V against a 5.0 V rail has no margin; `ACC_DETECT_N` gains the 100R series D-090 had omitted (D-188). **Hot-plug detect bounce is firmware, 20 ms/20 ms — an RC would DELAY REMOVAL DETECTION, and removal is the safety-critical edge under MX-6** (D-183). Eighteen-case abuse matrix run: **nothing NOT ACCEPTABLE**. `#FLG0105`, deleted by the rebuild, turned out to be **the only power-output driver on the entire GND net** and was re-created with a note. **B-68, B-69 opened; O-7 raised** (1.5 k sized for an estimated 200 pF). **ERC 42 / 1 / 41 → 27 / 0 / 27 — ZERO ERRORS FOR THE FIRST TIME.** PCB untouched and still bit-identical to Beta-DM. **FBV2-S2 and PCB work NOT started.** |
| 2026-08-23 | FBV2-S1-008. Overall raised 53% → 55%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-BUTTONS = PASS**. **`08_BUTTONS_EXPANDERS` MIGRATED — eight of nine sheets done.** **Task was INTERRUPTED by a session limit and RESUMED**; all work was uncommitted working-tree change, was inspected and classified, and nothing valid was discarded. **Both expanders are NXP `PCAL9535APW,118`, verified against the primary datasheet (Rev. 2, 23-Jan-2015) and NOT treated as a behavioural drop-in** — it powers up with **all interrupts masked**, the opposite of the TCA9535, so unchanged firmware sees no interrupts at all (D-164). `U2` = **0x20**, `U3` = **0x21**, preserved. **THE ALLOCATION GENUINELY FAILS: 35 committed signals against 32 pins**, with every escape closed — zero free native GPIO (B-10) makes the brief's own **WS2812 escape impossible**, `RESERVED_SPARE` is mandated by D-094 and the ten XGPIO by D-082. **Closed by `U23`, a THIRD `PCAL9535APW,118` at `0x22`: no new MPN, no new footprint, no new driver, no new rail, and B-37 RETIRED with 12 spare I/O** (D-165, **O-6 raised**). **Core, community and safety functions placed before the RGB by construction** — `U23` carries only the light and the spare, so declining O-6 costs nothing else (D-166). **`RESERVED_SPARE` DID NOT EXIST before this task**; it is now `U23` P03 with `R130` 100 k and `TP41` (D-173). **Front RGB LOCKED: MEIHUA `MHPA3528RGBCT` (LCSC C409779), common anode, PLCC-4, three unequal resistors 1k/680R/390R = 1.50/1.03/1.67 mA, white 4.20 mA** (D-167, D-168) — **dark by construction with NO external pull-ups**, because 06h = FF makes the pins high-Z and 02h = FF makes them drive HIGH on the transition (D-169). **Both charger STAT pins landed at 10 kΩ**, with the no-battery STAT2 toggle handled by the interrupt mask (D-170). **`TOUCH_INT_N`, `SD_CARD_DETECT_N` and `SX1262_DIO1` landed; `SX1262_BUSY` stays native; `SX1262_RXEN` stays expander-controlled with its pull-down.** **Six buttons, HOME deleted outright, volume not invented**, `PTS645SM43SMTR92LFS` verified orderable and the 10 µA wetting-current minimum checked for the first time (D-172). **O-5 CLOSED — IR receiver reverts to `TSOP38238` (AGC2), `TSOP38438` retained as a documented fallback** (D-163). **B-67 opened** — no published bounce time for the PTS645. Six root-sheet UUIDs with the non-hex prefix `fb080r00-` repaired. **ERC 42 / 1 / 41 — identical violation set to the recovered tree and better than the 45 / 2 / 43 pre-sheet-08 baseline; zero new errors.** PCB untouched and still bit-identical to Beta-DM. **Sheet 09 untouched.** |
| 2026-08-23 | FBV2-S1-007. Overall raised 51% → 53%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-IR = PASS**. **`07_IR` MIGRATED.** **The whole IR subsystem arrived DNP — eight parts — and is now FITTED** (D-153), **the fourth consecutive sheet with a load-bearing inherited DNP; sheets 08 and 09 must be assumed to carry the same trap**. **IR TX locked Vishay `TSAL6100`**, with the **TSAL6200 fallback proven a true drop-in** — identical package, `VF` and `IFM`, so `R24` is unchanged (D-154). **Peak current 150 mA = 75 % of `IFM`**: `IFSM` 1.5 A is a **single-pulse ≤ 5 µs surge and cannot justify carrier current**; 200 mA leaves no tolerance margin and **300 mA is out of spec** (D-155). **Supply preference REVERSED to `+3V3`, not `SYS`** — regulated gives 118–170 mA against 64–166 mA on `SYS`, where **IR range would visibly shorten as the battery drains** (D-156). **`R24` 18 Ω → 12 Ω plus `R123` DNP parallel trim, never below 10 Ω total** (D-157). **`C12` 4.7 µF → 22 µF**: 4.7 µF gave 218 mV of carrier ripple, 22 µF gives 40 mV (D-158). **AO3400A pinout CONFIRMED 1 = G / 2 = S / 3 = D and the "needs the official AOS land pattern" blocker CLOSED — AOS publishes none**; safe-OFF proven at 10 mV against a 650 mV threshold (D-159). **Receiver `TSOP38238` → `TSOP38438`, a pure MPN change**, and the inherited `R21`/`C11` filter is now **quantified at 41 dB at 38 kHz against a Fig. 7 knee of ~10 mV RMS — ~90× margin, and it is what makes sharing `+3V3` safe** (D-160). **No new mutual-exclusion rule** — IR averages 17 mA against the audio amplifier’s 230 mA peaks (D-161). `TP39`/`TP40` added. **O-5 raised for CTO: Vishay marks AGC4 "No" for Sony code**, conflicting with the brief’s own protocol list; receive-only, and reverting is a `lib_id` change because the `TSOP38238` symbol was kept. **B-65, B-66 opened.** **ERC 45 → 45, zero added, zero removed.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-23 | FBV2-S1-006. Overall raised 49% → 51%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-AUDIO = PASS**. **`06_AUDIO` MIGRATED.** **`U5` and `J6` arrived from Beta-DM marked DNP — the speaker output path had never been built — and are now FITTED** (D-144), the third load-bearing inherited DNP in two tasks. **Microphone locked: PUI `DMM-4026-B-I2S-R` replacing the obsolete ICS-43434 — SEVEN pads, not six, so a new symbol and footprint were built from the manufacturer drawing**; `CONFIG`→GND is mandatory and has no ICS equivalent; **`R120` 100 kΩ on `I2S_MIC_DIN` is a data-sheet requirement the inherited sheet lacked**; **no 1.8 V rail is needed** despite the 1.8 V rating (D-145). **The brief’s 16 kHz cannot be run on the wire**: the microphone needs BCLK 2.048–4.096 MHz, so **the bus runs 48 kHz × 64 = 3.072 MHz and firmware decimates** (D-146). **MAX98357A retained, PRODUCTION, MPN `MAX98357AETE+T`; `GAIN_SLOT` GND → VDD (12 dB → 6 dB)** because at 12 dB the top **6.8 dB of digital range was clipped by the 3.3 V rail** (D-147). **Speaker locked: PUI `AS02008MR-LW152-R`**, Ø20 × 3 mm, 8 Ω, 0.5/0.8 W, 500–4000 Hz voice band, AWG #32 leads crimping straight into the existing `J6` — replaceable without soldering (D-148). **Default max software volume −6 dBFS → 0.17 W, ≈ 57 mA**; 0 dBFS is 0.68 W / 230 mA and must not be continuous (D-149). **EMI: nothing fitted** — the data sheet’s Figure 14 shows compliance with 12 in of cable and no filter; `R121`/`R122` 0 Ω fitted, `C81`/`C82` 1 nF DNP (D-150). Acoustic interface measured from the drawing: **Ø1.05 mm PCB hole, bottom port, mic on the face opposite the aperture** (D-151). No hardware AEC; `SD_MODE` is already a hardware mute for half-duplex voice (D-152). **B-61–B-64 opened.** **ERC 45 → 45, zero added, zero removed.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-23 | FBV2-S1-005. Overall raised 47% → 49%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-I2C-IMU = PASS**. **`05_I2C_DEVICES` MIGRATED.** **Reported-ERC correction: FBV2-S1-004 / 004B / 004C quoted "68"; the stored reports say 46** — the deltas were always right, the absolute number was not. **BMI270 re-derived from `BST-BMI270-DS000-08` Rev 1.6 and every inherited strap proved correct** (D-136); **B-44 CLOSED** (`IOH`/`IOL` ≤ 2 mA vs a 323 µA load). **The BMI270 has NO tap or double-tap feature in any configuration** — stated because the brief asked for it. **GPIO3 boot safety is now a timing proof**: `INT1_IO_CTRL` resets to output-disabled, `tH` = 3 ms, GPIO3 defaults Floating, so **the IMU cannot reach the strap window**; the pull-down makes **push-pull + active-high mandatory and open-drain forbidden** (D-137). **`INT2` stays DNC; `RESERVED_SPARE` untouched** (D-138). **Internal I²C pull-ups 4.7 kΩ → 2.2 kΩ** — at ≈ 85 pF measured, 4.7 kΩ gives `t_r` **338 ns and FAILS the 300 ns fast-mode limit**; 2.2 kΩ gives 158 ns at 1.32 mA sink (D-139). **BMI270 address made strappable: `R118` 0 Ω FIT → 0x68, `R119` 0 Ω DNP → 0x69, fit one only** (D-140). **IMU permanently powered, no load switch** — saves 9 µA, costs wake-on-motion (D-141). **`I2C_ADDRESS_REGISTRY.md` created and normative** (D-142). **BMI270 land pattern verified against §8.3 by rendering and measuring the drawing — "DO NOT ROUTE" discharged** (D-143). **B-59, B-60 opened.** **O-4 flagged for CTO: TCA4307-class hot-swap buffer with stuck-bus recovery at Sheet 09** — nothing implemented. **ERC 46 → 45, zero added, one removed.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-23 | FBV2-S1-004C. Overall raised 45% → 47%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-NFC-MATCHING = PASS**. **Antenna corrected A → B: `FXC.46.52.0075X.B.dg`, reverse ferrite**, bonds adhesive-side to the **inner rear shell**, ferrite facing inward — with the A version the ferrite would have sat between the coil and the tag (D-131). Board unaffected. **B-version parameters adopted**: `La` 1.10 µH, `Rs` 1.50 Ω, `Q` 60.37, `SRF` 395 MHz (D-132). **Target impedance DERIVED from the D-130 current budget — ≈ 36 Ω differential, Q ≈ 25 — the earlier 20 Ω/side assumption is discarded** (D-133). **First-build set calculated**: `R_q` 1R1 (Q 25.3), `C_s` 300 pF, `C_p` 1.5 nF, EMC **39 nH / 100 pF → f_c 20.1 MHz** — **B-56 CLOSED**, the old pair sat at 7.6 MHz below the carrier (D-134). **RFI SAFETY DEFECT FOUND AND FIXED**: the placeholder 47 pF / 220 pF divider would have put ≈ **4.4 V pk-pk on RFI against a 3.0 V rail**; new 27 pF / 620 pF gives ≈ 1.03 V pk-pk (D-135). **B-48 closed on substance**; **B-57, B-58 opened**. First-article tuning **required** with rear shell, antenna, PCB and battery all installed. **ERC 68 → 68, zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005; the stored reports say 46 → 46. The delta was right.)* | Overall raised 43% → 45%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-NFC-ANTENNA-LOCK = PASS**. **NFC IC LOCKED `ST25R3916-AQET`, non-B — P-17 CLOSED** (D-126). **NFC antenna LOCKED Taoglas `FXC.46.52.0075X.A.dg`, off-board** — 13.56 MHz, 46 mm circular flex, 0.27 mm with ferrite, 3M peel-and-stick, 75 mm 28 AWG twisted pair, ACH(F), 40 mm typical read distance, all verified verbatim from `SPE-22-8-131-C` — **B-53 CLOSED** (D-127). **`J7` = JST `BM02B-ACHSS-GAN-ETF`** added between the matching network and the antenna; mating **proven** via `ACHR-02V-S` = the antenna's own ACH(F) housing, so **the antenna is replaceable without soldering** (D-128). **Brief corrected: JST classes ACH as TOP ENTRY, not right-angle** — the part is right, `J7` needs mating clearance above it. **Matching re-derived against the real antenna**: `R_q` 0 R → **1R0** (`Q` 58 → 25.8, derived from the antenna alone), `C_s` → **300 pF**, `C_p` → **1.8 nF** from an L-match with a stated assumption; **`L5`/`L6` + `C69`/`C70` deliberately NOT re-derived and flagged unbuildable (B-56)** (D-129). **NFC field current estimated ≤ 150 mA at 3.3 V; B-54 downgraded** (D-130). **B-06 CLOSED.** Mechanical: NFC clear region **48 × 48 mm**. **ERC 68 → 68, zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005; the stored reports say 46 → 46. The delta was right.)* B-55, B-56 opened. One item flagged for CTO: the **ferrite is directional** and Taoglas sells a reverse-ferrite variant — zero board change, but it must be settled against the enclosure stack before antennas are ordered. | Overall raised 40% → 43%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-RADIOS-NFC = PASS**. **`04_SPI_B_RADIOS_NFC` MIGRATED.** **RF architecture locked (D-118):** 433 MHz internal Taoglas `FXP450.07.0100C` (IPEX MHF-I mating **proven** against the module's IPEX-1 socket), 915 MHz external to a top-panel **SMA female** bulkhead; **no board RF trace, matching network, switch or diplexer in either band**; the `U7` IPEX must stay service-accessible. Both module stamp-hole pins are explicit no-connects. **NFC: B-41 CLOSED** — `VDD`/`VDD_TX` moved to `NFC_SUPPLY` = `+3V3` (D-122, `sup3V` firmware requirement); **`Y1` 27.12 MHz crystal** + load caps (D-123); **real differential matching and RX-divider topology** with every value `TUNE` and two trim positions per TX leg (D-124); `AAT`, `CSI/CSO`, `EXT_LM`, `MCU_CLK` explicit no-connects with recorded reasons. **`SX1262_DIO1` published for sheet 08.** **Zero `*_TBD` nets remain in the project.** **ERC 4 errors → 2, total 64 → 46, zero added** — the first migration task to reduce the error count. **P-17 recommended for closure (keep the non-B); B-53 opened** (antenna architecture). B-48, B-49, B-50, B-51, B-52, B-54 opened. PCB untouched and still bit-identical to Beta-DM. | Overall raised 37% → 40%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-DISPLAY-SD = PASS**. **`R111` FITTED** (D-111). **`03_SPI_A_DISPLAY_SD` MIGRATED:** new `ER-TFT035IPS-6_50P` symbol with the vendor pin table verbatim, **catching two dead-on-arrival faults in the inherited `J1`** — reversed backlight anode/cathode and swapped SCL / D-CX. Touch gains `TOUCH_INT_N` (panel pin 46, previously unrepresented). Backlight re-derived: `R69` **1.87 Ω**, `R70`–`R73` **4 × 33 Ω**, I_LED **109 mA typ / 117.6 mA worst case** against a 120 mA panel maximum; peak switch current 4.6× (3.9× at f_SW min). `SD_CARD_DETECT_TBD` → **`SD_CARD_DETECT_N`** with a 100 kΩ pull-up. `R112` 0 Ω **DNP** isolates the display SDO from the shared SPI-A. **B-43, B-32, B-28 CLOSED; B-46, B-47 opened.** `/03_SPI_A_DISPLAY_SD/LED_A` added to the `LED_BOOST` netclass — a latent FBV2-P2 defect no probe would have caught. **ERC 4 errors → 4 errors, error report byte-identical.** PCB untouched and still bit-identical to Beta-DM. | Overall raised 34% → 37%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-MCU-CORE = PASS**. **P-20, P-21 and P-22 CLOSED** (D-104…D-110). `R95` locked at **560 Ω** — recovery **8.36 mA** nominal, and **B-27's ceiling amended to ≈ 15.9 mA** because 680 Ω was the value that produced its old ≈ 13 mA figure. LTC4368 **OV trip derived to 4.63 V** (`R77` 3.65 M / `R78` 442 k) from the datasheet's 492.5/500/507.5 mV threshold; **removes a BOM line**. Scripted KiCad edits permitted under an **eight-condition** standing rule. **`02_MCU_CORE` MIGRATED:** GPIO38 = `NATIVE_A`, GPIO47 = `NATIVE_B`, GPIO46 = `DISP_BL_CTL` with `R108` 10 kΩ strap pull-down + `R109` 0 Ω isolation link + `TP2`, GPIO43 withdrawn from the community port (`TP35` UART0 TXD), **GPIO3 strap closed — B-09 retired**, `R111` 10 kΩ GPIO45 pull-down placed **DNP**. **ERC 5 errors → 4, zero new; `02_MCU_CORE` clean.** B-43, B-44, B-45 opened. **NO NEW DEBUG HARDWARE** — USB Serial/JTAG is the service interface. PCB untouched and still bit-identical to Beta-DM. | Overall raised 31% → 34%. **No gate in the twelve-gate table passed**; the task gate **FBV2-S1-POWER-TREE = PASS**. **First Full Beta v2 design-file work.** `hardware/beta-v2/` forked from Beta-DM with a **re-runnable** byte-equivalence proof; **`01_POWER_TREE` CAPTURED** — P2 reverse protection with `U18` LTC4368-1, autonomous dead-cell recovery, `ACC_3V3`/`ACC_5V` on one consolidated boost + load-switch BOM, NFC 3V3-FIT/5V-DNP select, `VBUS_PRESENT` telemetry, 19 test points, 136 parts. **ERC 58 baseline → 55, zero introduced** (three inherited violations retired). **B-01 closed at schematic level.** `U18` package corrected from a policy-violating DFN-10 to MSOP-10. Inherited `R_FB_TOP 1M` net label renamed `V3V3_FB`. **D-099…D-103 recorded; B-41, B-42, P-20, P-21, P-22 opened.** PCB untouched and still bit-identical to Beta-DM. |
| 2026-08-22 | Created. FBV2-A0 recorded as PASS. Initial blocker set B-01 through B-16 imported from the pre-design audit. |
| 2026-08-22 | FBV2-ARCH-001. Overall raised 8% → 10%; **no gate passed.** B-07 retired as incorrect. B-17/B-18/B-19 added. FBV2-A2 marked as the recommended next gate. |
| 2026-08-22 | FBV2-ARCH-002. Overall raised 10% → 13%; **no gate passed. FBV2-A1 assessed CANNOT PASS** (4 of 8 criteria). B-18 closed, B-25 closed. B-20…B-24 added. P-11…P-18 opened. Standing **NO-RESPIN RECOVERY POLICY** (D-049) established. |
| 2026-08-22 | FBV2-PWR-001. Overall raised 13% → 15%; **no gate passed. FBV2-A1 FAIL, 5 of 6 criteria closed.** D-061…D-064 recorded. **P-13 and B-24 closed** by primary-source evidence; B-22 closed. Complete battery-protection topology specified. Fuse **REQUIRED**, clamp **REQUIRED**, PTC **REJECTED**. |
| 2026-08-22 | FBV2-DISP-001. **No gate passed — percentage holds at 25%.** D-071/D-072/D-073 recorded. Display size LOCKED at **3.5″**; battery envelope LOCKED. **Display MPN and J1 deliberately NOT locked** — old-J1 compatibility is **UNPROVEN**. ESP32-S3 SPI verdict **PASS** (FSPI IO_MUX, 80 MHz, no bus merge). M-01/M-02 closed; **M-06/M-07 opened.** |
| 2026-08-22 | FBV2-MECH-001. Overall raised 20% → 25%. **FBV2-A2 = PASS.** D-069/D-070 recorded; cavity **75.0 × 155.0 × 18.5 mm** derived; PCB target **70 × 148**; **P-07 closed**; M-01/M-02 opened. Beta-DM 74 × 155 outline ruled **RE-FLOORPLAN REQUIRED**. Next gate: **FBV2-S1**. |
| 2026-08-23 | FBV2-COMM-002. **Overall HELD at 31% — a correction is not progress.** **Harwin `M20-7881242` REJECTED as obsolete** (404 on harwin.com; the MPN had been configured from an ordering scheme, which FBV2-COMM-001 had flagged). **Connector re-locked: Samtec `BCS-112-S-D-HE`** — 2×12 female Tiger Claw, horizontal entry, through-hole, 30 µin gold, ACTIVE, 385 pcs next-day, MOQ 1, 4.6 A/contact. `-S` chosen over the proposed `-L` because Samtec qualifies **both** platings at only **100 cycles** and the **2 500-cycle** extended-life data exists **only at 30 µin gold** — +$2.88/board. **Z column improves 22.30 → 19.53 mm of 23.0 (3.47 mm spare).** Pin ordering and electrical architecture **unchanged**. **O-1 approved** (`FLT` wire-OR → `ACC_POWER_FAULT_N`, `U3` P16 = `RESERVED_SPARE`), **O-2 approved** (I²C `0x50` reserved for an accessory-ID EEPROM), **O-3 rejected**. D-093…D-098 recorded; B-39, B-40, P-19 opened; B-37, M-09, M-10 downgraded. |
| 2026-08-23 | FBV2-COMM-001. Overall raised 28% → 31%. **No gate in the twelve-gate table passed**; the task gate **FBV2-COMM-LOCK = PASS**. **The 20-pin community port is SUPERSEDED.** New port **2×12, 24 active contacts, FEMALE device side**, ~~`Harwin M20-7881242`~~ *(rejected as obsolete 2026-08-23 — see FBV2-COMM-002)*, keying and shroud from the enclosure. Pin ordering locked with every power contact GND-paired so no row swap can put 5 V on a logic pin. **New 5 V accessory rail** `SYS → TPS61023 → TPS22950C → ACC_5V_SW`, and `+3V3 → TPS22950C → ACC_3V3_SW`; **one load-switch MPN and one boost MPN across both rails**. D-081…D-092 recorded. **P-02, P-15, P-16 and B-08 CLOSED**; B-34…B-38, M-09, M-10 opened. **Zero spare expander capacity now remains anywhere.** |
| 2026-08-23 | FBV2-DISP-002. Overall raised 25% → 28%. **No gate in the twelve-gate table passed**; the task gate **FBV2-DISP-LOCK = PASS**. **Display LOCKED** — EastRising `ER-TFT035IPS-6` + `ER-TPC035-6` (ILI9488 + FT6236 @ 0x38), 56.54 × 84.96 × 3.95 mm, one 50-pin 0.50 mm **bottom-contact** 0.30 mm FPC. **`J1` LOCKED** — Hirose `FH69-50S-0.5SH`, mating proven from both manufacturers' drawings, on the FH12/FH52E land pattern for a JLC second source. **Backlight closed** — TPS61169 retained, `R69` 2.55 R → **1.87 R**, `R70`–`R73` 4 × 39 R → **4 × 33 R**. D-074…D-080 recorded. **M-06 and M-07 CLOSED**; B-28…B-33 opened. ST7796S formally rejected on availability (D-078). |
| 2026-08-22 | FBV2-PWR-002. Overall raised 15% → 20%. **FBV2-A1 = PASS** — first gate since A0. D-065…D-068 recorded. Pass path changed to **P2** (4 FETs, 2 packages). Dead-cell recovery specified to component level. **P-11, P-12, B-20, B-21, B-23 closed**; B-26/B-27 opened. Clamp **demoted to secondary**, fuse **resized 3 A → ≈5 A**. Next gate: **FBV2-A2**. |
| 2026-08-27 | FBV2-P2-002S. **No gate passed - percentage holds at 74 %; PCB routing stays 0 %.** **D-264 DELIVERED**: outer-layer-only scoped by CURRENT PATH ROLE, exempting only the two bounded D-249 sense corridors; KiCad `disallow` proven to fire on every matching rule, so the unscoped block is excised from generated boards; new standing regression `d264_probe.py` A-F PASS. **`LTC_SHDN` CLOSED as one component** by the coordinated U18 schedule `6,10,7,1,3,2` - 002R item (c) closed with no placement change; `LTC_OV`, `LTC_GATE`, `FAULT_N`, `Q3_CS`, `Q2_CS` all whole; all nine PR-40 targets true. **FAIL at section 21: U18 6 of 8** (`U18.2` NO_PATH, `U18.9` NO_LEGAL_ESCAPE); `BAT_SENSE` five islands; trunk never laid, so sections 16-19 unreached. **Paired inner Kelvin NOT achieved** - one branch only, 9.930 mm on F.Cu + 2 vias, and not reported as a pass. **Key finding: `U18.9`/`U18.2`/`R75.1` still escape at 0.20-0.25 mm on the finished board** - they failed at the width demanded, not from being sealed; **`Q3.6` alone is genuinely walled in**. Authoritative PCB unchanged: six layers, zero signal tracks, zero signal vias. D-265 recorded. B-34 REMAINS OPEN. |
| 2026-08-27 | FBV2-P2-002T. **No gate passed - percentage holds at 74 %; PCB routing stays 0 %.** **D-266 SCARCE-PAD RESERVATION DELIVERED AND PROVEN.** On a clean board none of the four scarce sites is scarce (`Q3.6` 1.50 mm/3 dir, `R75.1` 1.50/5, `R75.2` 1.50/3, `U18.9`/`U18.8`/`U18.2` 0.25/2) - every scarcity 002M-002S reported was made by copper laid earlier. BAT_SENSE current path routed FIRST: `Q3.5->Q3.6` 3.770 mm and `Q3.6->R75.1` 13.532 mm, 1.00 mm B.Cu, zero vias. Kelvin exits reserved as neck+ordinary 0.35/0.20 via, both ends gated as one item, judged by an inverted gate (ratsnest must NOT move). **U18 8 OF 8 INCLUDING `U18.8` AND `U18.9`, all nine PR-40 targets true - a first**, with ONE control schedule instead of six; `LTC_GATE` 6/6, `LTC_SHDN`, `FAULT_N` 4/4, `LTC_OV` B.Cu zero vias, `LTC_UV`, `Q3_CS`, `Q2_CS`, `BAT_MID` all whole. **Paired inner Kelvin BUILT on In2:** A 7.989 mm, B 10.456 mm, mismatch 2.467 mm inside spec, **B 0.456 mm over the 10 mm cap**. `holes_co_located` GONE; `Q4.1->R83.1` closed (41.814 mm, F.Cu, 2 vias, no new exception). **FAIL at section 22 on the trunk alone:** `R75.2->D9.1` NO_LEGAL_ESCAPE at >=1.200 mm, `D9.1` behind 37 track segments; zero corridor families generated. **Section 23 NOT triggered - Q3 does not move.** Authoritative PCB unchanged: six layers, zero signal tracks, zero signal vias. D-264 untouched. D-266 recorded. B-34 REMAINS OPEN. |
| 2026-08-27 | FBV2-P2-002U. **No gate passed - percentage holds at 74 %; PCB routing stays 0 %.** **D-267 delivered:** an early high-current escape reservation for `D9.1` only, at the trunk target/floor, outer-layer-only, zero-via. `D9.1` escapes at 1.50 mm in SIX directions on a clean board; **F1 reserved 2.701 mm and F2 5.149 mm at the 1.50 mm target with zero vias, neither costing a control pin (U18 stayed 8/8).** **KELVIN B FIXED** - the 25 um lattice tried first: **A 7.644 mm, B 9.927 mm (inside the 10 mm cap), mismatch 2.283 mm**, same via sites, no relaxation. **TAP path-role via correction delivered:** via geometry follows the path role, and the board's own rules put the floor at **0.65/0.40** (0.35/0.20, 0.50/0.25 and 0.50/0.40 each correctly rejected); with it **`R79.1 -> R80.1` routes** and `D12.1 -> R77.1` improves to 13.682 mm at 0.30 mm on B.Cu with zero vias. **DECISION STOP at section 25: the trunk is blocked by a SEVERED PLANE, not a corridor** - both endpoints escape at 1.50 mm and there is no B.Cu path between them at ANY width down to 0.20 mm. **The early-trunk hypothesis is measured FALSE** (trunk routes 19.219 mm, U18 falls to 5/8). Authoritative PCB unchanged: six layers, zero signal tracks, zero signal vias. D-264 and D-266 untouched. D-267 recorded. B-34 REMAINS OPEN. |
| 2026-08-27 | FBV2-P2-002V. **No gate passed - percentage holds at 74 %; PCB routing stays 0 %.** **D-268 executed, and it found the lever was aimed at the wrong thing.** Removing TP17, C58 and TP15 ENTIRELY from the finished 002U board changes `R75.2 -> D9.1` at **no width from 1.50 down to 0.20 mm** - neither is on the cut. **The partition is routed CONTROL copper:** removing `LTC_OV`'s 27 B.Cu shapes restores 0.60 mm, removing all LTC control (77 shapes) restores 1.50 mm at 30.561 mm, removing all routed B.Cu gives back the 19.878 mm clean-board route. TP17 was searched (20 legal poses) and replayed at **(17.000, 79.000), 5.408 mm**: the full prefix reproduces - **U18 8/8, Kelvin A 7.644 / B 9.927 / mismatch 2.283 mm on In2** - **and the trunk is still NO LEGAL ESCAPE at >=1.200 mm; TP17 left the blocker list and nothing moved.** C58 characterized (1 uF X7R 0603, local HF decoupling 4.009 mm from `D9.1`) and **NOT moved**. `R79.1 -> R80.1` routes; **`R77.1 -> R79.1` fails on `BAT_MAIN routed clearance` - the fourth property still scoped by net name.** Long outer trunk unavailable without the D-267 reservation and costs **2.29x the resistance**. Zero new DRC classes, zero dangling copper. Authoritative PCB unchanged: six layers, 0 tracks, 0 vias. D-268 recorded. B-34 REMAINS OPEN. |
| 2026-08-27 | FBV2-P2-002W. **No gate passed - percentage holds at 74 %; PCB routing stays 0 %.** **D-269(a) DELIVERED: clearance is the fourth and last property to follow PATH ROLE** (after width D-249, layer D-264, via geometry D-267). 0.300 mm untouched on every current-carrying role; four bounded divider corridors fall back to the **existing board default 0.200 mm** - no new number invented. New regression `d269_probe.py`, six clauses on real copper, PASS. **`BAT_RAW` CLOSES FOR THE FIRST TIME** - `R77.1 -> R79.1` routes 12.454 mm at 0.20 mm on F.Cu with 2 legal 0.65/0.40 vias; all eleven functional pads one island. Prefix reproduces: **U18 8/8, Kelvin A 7.644 / B 9.927 / mismatch 2.283 mm on In2.** **DECISION STOP at section 25: NO control-offload cut set exists at ANY cardinality** - all 127 subsets of the seven B.Cu control nets tested at 1.20 and 1.50 mm, none opens 1.20 mm. **Only all-seven-controls PLUS `BAT_RAW` opens 1.50 mm (19.9 mm)** - because `R80.1 -> Q2.7` and `D12.1 -> R77.1`, the microamp TAP copper that closing `BAT_RAW` required, is now in the margin. Zero new DRC classes, zero dangling copper. TP17 and C58 untouched. Authoritative PCB unchanged: six layers, 0 tracks, 0 vias. D-269 recorded. B-34 REMAINS OPEN. |
