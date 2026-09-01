## 2026-08-31 - FBV2-P2-032: D-330 — remaining button-family framework bounded; F.Cu and split-inner hop variants refuted (no copper change)

Fast screens on clean D-329 state show D-328's endpoint hop is geometry-specific: `BTN_DOWN_N` and `BTN_A_N` have no F.Cu join corridor, while split In2/In3 joins fail the locked 0.60/0.30 via-site requirement at `R5.2` and `U2.17` respectively. No full gate was spent on dead candidates and authoritative D-328 copper remains byte-identical. D-325 duplicate-pad handling remains the generic accepted button framework; the three boxed west endpoints now defer to the generic boxed-endpoint framework. Next: bounded In2/In3 long-haul framework. Full evidence: [`audits/2026-08-31-p2-032-d330-button-family-framework-fast-screen.md`](audits/2026-08-31-p2-032-d330-button-family-framework-fast-screen.md).

## 2026-08-31 - FBV2-P2-031: D-329 — routing-wall registry + framework-first/batch-promotion transition (no copper change)

The owner-approved routing acceleration is now implemented at a clean process boundary. A machine-readable `routing_walls.json` captures nine accepted evidence-backed walls and prevents blind replay unless an explicit replacement framework is selected. `incremental_router.py` consults it; regression G40 proves deterministic registry integrity, blocks ordinary `BTN_DOWN_N`, and permits the accepted explicit `BTN_RIGHT_N` hop-anchor plan. `router_regression.py` G1–G40 ALL PASS. The authoritative D-328 PCB is byte-identical (`27db293c…`, 837 tracks / 73 vias / ratsnest 656 / journal 125); the full D-286 promotion gate and every electrical/manufacturing invariant remain unchanged. Next: finish the remaining button family as a coherent batch, then build the bounded In2/In3 long-haul framework. Full evidence: [`audits/2026-08-31-p2-031-d329-routing-wall-registry-framework-first-transition.md`](audits/2026-08-31-p2-031-d329-routing-wall-registry-framework-first-transition.md).

## 2026-08-31 - FBV2-P2-028: D-326 — `BTN_UP_N` promoted (twentieth rest-of-board increment; second SWx user button, cleaner than BTN_B_N, zero router-logic change)

**THE TWENTIETH INCREMENT, SECOND `SWx` BUTTON.** The navigation D-pad **UP** button `BTN_UP_N` routed on the SAME accepted D-325 duplicate-ref MST framework — ZERO router-logic change (a `GROUPS` registry entry + comment only) — and PASSED the real full-board gate. CLEANER than `BTN_B_N`: **one** through via, not two. Board `35d32343…` (800/70/662/119) → `adbea36b…` (821/71/659/122).

- **Note — mandate sha.** The FBV2-P2-028 mandate quoted the pre-work authoritative sha as `35d32343af5146b973f5231e76d252e90ddf796d274e63200da5ea41e5767ea7`; the live board file, `live_fingerprint.py`, the D-325 commit and CURRENT_STATE all agree the true D-325 sha is `35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220` (the two share only the 16-char abbreviation prefix `35d32343af5146b9`). The live board hashed byte-for-byte to the repo's own single-source-of-truth value, so work proceeded on that verified basis — the mandate tail was a transcription artifact, not a board discrepancy.
- **Candidate screen (read-only).** Every remaining `SWx` nav button shares `BTN_B_N`'s topology (switch SW2–SW6 is the same 4-pin `PTS645` tact switch with two pad-"1" lands 7.96 mm apart, a B.Cu pull-up R4–R8, a B.Cu PCAL expander GPIO U2.13–U2.17). Two independent read-only screens on the live D-325 board (`w/screen_020.py` bbox congestion + a faithful `physical_net_pads`/`mst_edges` route-plan vet) measured all five; `BTN_UP_N` is decisively cleanest — cross-haul **12.33 mm** / congestion **201** (vs `BTN_A` 42.35/429, `BTN_DOWN` 44.00/352, `BTN_LEFT` 50.15/568, `BTN_RIGHT` 56.89/508) — because SW2 sits in the SAME open south button field where `BTN_B_N` (SW7) already passed. Every nav button is a 1-via increment (the two F.Cu switch lands join by a same-layer F.Cu land-run — the D-325 lever edge — so only the haul to the R/U2 cluster needs a via). `Net-(SW9-A)` (5-pad power net touching U12.12 converter, the SPDT slide-switch output) and `BOOT_N` (characterized sensitive ESP32 boot strap) correctly EXCLUDED.
- **The increment.** `BTN_UP_N` = {`SW2.1` (two F.Cu lands at `(60.220,96.750)`/`(68.180,96.750)`), `R4.2` pull-up (B.Cu), `U2.13` expander GPIO (B.Cu)}. MST = `SW2.1a↔SW2.1b` (7.96 mm SAME-LAYER F.Cu land-run, NO via) + `R4.2↔U2.13` (SAME-LAYER B.Cu run, NO via) + `U2.13↔SW2.1` (ONE 0.60/0.30 Default THROUGH via at `(61.100,95.400)` in the OPEN south field, In1/In4 re-poured once). 21 tracks (6 F.Cu + 15 B.Cu), 1 through via. ZERO router-logic change (only `GROUPS['BTN_UP_N']` + comment).
- **Gate (real full-board, all 10 checks PASS).** No Phase-A copper deleted/altered; every new item in-scope (22 items); only In1/In4 planes re-poured; **all four physical pads in one copper cluster (`open_edges 3→0`, both `SW2.1` lands driven)**; all Phase-A pairs still connected; **ratsnest 662→659 (−3, the true KiCad count)**; no new/worse DRC class (`clearance` stays 0); `unconnected_items` 499→499. Promote: `35d32343…`→`adbea36b…`, journal 119→122. Realized copper 6.370 mm from `BAT_PROTECTED_P` → zero D-269; the via ≥ 4.804 mm from every barrel.
- **Tests / integrity (deterministic, twice).** `router_regression.py` ALL PASS **G1–G38**: new **G38** pins the increment (4 pads incl. both `SW2.1` lands joined to the R4.2 hub + U2.13, 21 trk/1 via legal = 6 F.Cu + 15 B.Cu, via ≥ 0.80 mm from barrels min 4.804 mm, ADD-ONLY); **G37 retained** (the D-325 framework lever); **G1–G37 unchanged**. `incremental_probe_006..025` + `phaseB_bringup_probe_005` (821/71/122; 28 routed rest nets, 136 unrouted) ALL PASS; new `incremental_probe_025.py` proves BOTH `SW2.1` lands copper-joined to the `R4.2` hub. `live_fingerprint.py` bumped once (D-326); `phaseB_bringup_probe_005.py` roster extended by `BTN_UP_N`; `incremental_baseline_006.json` left stale-by-design. Independent kicad-cli DRC identical to D-325. D-269/D-264/DRU A/B (committed D-325 vs promoted D-326): `d269` flips PASS↔FAIL(2) on both, `d264` 2-failed on both (B no worse than A), `dru` FAIL(2) IDENTICAL — the documented western battery/power-tree synthetic-probe flake, NONE involving `BTN_UP_N`; no regression.
- **Opportunity & simplification.** No repetitive-maintenance consolidation was due (one fingerprint bump, one probe, one G-contract, one roster line — all expected). The `SWx` family stays the largest unlocked block: four nav buttons remain (`BTN_A/DOWN/LEFT/RIGHT_N`), each a 1-via increment but with 42–57 mm cross-hauls carrying the corridor-wall risk — judge case-by-case (the "one bounded alternative if the first fails geometrically" discipline).
- **Governance.** No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged. **Open owner decisions: NONE** (autonomy continues). Rollback: `git revert` this commit restores the committed D-325 board (`35d32343…`, 800/70/662/119). All locked invariants preserved (D-249/D-257/D-269/D-275/D-288/D-290, In1/In4 GND roles, In2/In3 capacity, RF/USB/mechanical reservations, D-304..D-325); frozen `beta-full-reference-v1` untouched; journal authoritative (122). **NEXT FBV2-P2-029:** route the next `SWx` nav button (fresh screen + vet first, the west hauls need the wall-risk check) or the next genuinely-clean functional open-region net under the D-286 gate + adding `incremental_probe_026`+`G39` on promote; retain G37/G38. 136/164 rest nets unrouted. PCB routing ~19 %, overall ~76 %, readiness ~78 % (JLCPCB file unchanged). Full analysis: [`audits/2026-08-31-p2-028-d326-twentieth-rest-of-board-incremental-increment-btn-up-n-promoted.md`](audits/2026-08-31-p2-028-d326-twentieth-rest-of-board-incremental-increment-btn-up-n-promoted.md).

## 2026-08-31 - FBV2-P2-027: D-325 — DUPLICATE-REF MST framework fix + `BTN_B_N` promoted (nineteenth rest-of-board increment; the SWx user-button family unlocked)

**THE FIRST FRAMEWORK-DEPENDENT INCREMENT.** A bounded, generic, deterministic fix (in `incremental_router.py` ONLY — `qrouter.py` untouched, so every G-contract that routes through `QBoard` stays byte-identical) lets the MST and the gate treat a footprint's two same-numbered physical lands as distinct nodes. With it, `BTN_B_N` (navigation/boot button, the first net of the `SWx` user-button family) routed, PASSED the real full-board gate, and was PROMOTED. Board `a7bf8bdc…` (781/68/665/116) → `35d32343…` (800/70/662/119).

- **Root cause (precise).** `SW7` (Button_Switch_SMD:`SW_SPST_PTS645Sx43SMTR92`) is a 4-pin tact switch whose two mechanically-linked terminals BOTH carry pad NUMBER "1" on `BTN_B_N` at `(49.520,96.750)` and `(57.480,96.750)`, 7.96 mm apart. `qrouter.QBoard._scan` keys `self.pads[(net,"REF.NUM")]`, so the second `SW7.1` overwrote the first and one land was invisible to the MST → D-323 gate FAIL (`open_edges 2→1`). A MATCHING collapse lived in `cmd_gate.net_open_edges()`, which ref-deduped the two lands in its cluster count and under-counted the owed ratsnest edges (2 where KiCad owes 3 for 4 lands).
- **The fix (bounded, generic, deterministic; `qrouter.py` untouched).** (1) `physical_net_pads()` sources MST nodes by stable PHYSICAL identity `(ref,x,y)`, recovering any land the `(net,tag)`-keyed `qb.pads` dropped (rebuilt field-for-field like `_scan` via `_rr_pad_dict`); ordinary unique-pad nets return the exact `net_pads()` dict OBJECTS → byte-identical routing; `cmd_route` sorts by `(ref,x,y)` (ties never fire for unique nets). (2) `cmd_gate.net_open_edges()` rewritten as a physical-pad union-find (nodes `(ref,x,y)`, copper adjacency from `GetConnectedItems`) → counts copper clusters over PHYSICAL lands, matching KiCad's own ratsnest. Weakens no rule, netclass, clearance, via geometry, placement, footprint, or topology; adds nodes only for a genuinely duplicated pad number.
- **The increment.** `BTN_B_N` = {`SW7.1` (two F.Cu lands), `R9.2` pull-up (B.Cu), `U2.18` expander (B.Cu)}. MST hubs on `R9.2` → BOTH `SW7.1` lands (two 0.60/0.30 Default THROUGH vias at `(48.300,96.750)` and `(56.300,95.600)` in the OPEN south button field, In1/In4 re-poured once) + one SAME-LAYER B.Cu run `R9.2→U2.18`. 19 tracks (3 F.Cu + 16 B.Cu), 2 through vias.
- **Gate (real full-board, all 10 checks PASS).** No Phase-A copper deleted/altered; every new item in-scope; only In1/In4 planes re-poured; **all four physical pads in one copper cluster (`open_edges 3→0`, both `SW7.1` lands driven)**; all Phase-A pairs still connected; **ratsnest 665→662 (−3, the true KiCad count)**; no new/worse DRC class (`clearance` stays 0); `unconnected_items` 499→499. Promote: `a7bf8bdc…`→`35d32343…`, journal 116→119. Realized copper 10.68 mm from `BAT_PROTECTED_P` → zero D-269; both vias ≥ 2.915 mm from every barrel.
- **Tests / integrity (deterministic, twice).** `router_regression.py` ALL PASS **G1–G37**: new **G36** pins the increment (4 pads incl. both `SW7.1` lands connected, 19 trk/2 via legal, vias ≥ 0.80 mm from barrels, ADD-ONLY); new **G37** pins the framework lever (duplicate pad number → distinct nodes; MST spans all 4 lands; ordinary unique-pad net byte-identical SAME objects; deterministic); **G1–G35 unchanged**. `incremental_probe_006..024` + `phaseB_bringup_probe_005` (800/70/119; 27 routed rest nets, 137 unrouted) ALL PASS; new `incremental_probe_024.py` proves BOTH `SW7.1` lands copper-joined to the `R9.2` hub. `live_fingerprint.py` bumped once (D-325); `incremental_baseline_006.json` left stale-by-design. Independent kicad-cli DRC identical to D-323. D-269/D-264/DRU A/B (committed D-323 vs promoted D-325): `d269` FAIL(2) + `dru` FAIL(2) identical on both, `d264` up-to-2-failed (B no worse than A) — the documented western battery/power-tree synthetic-probe flake (BAT_RAW TAP, Q3.6→R75.1 In2), NONE involving `BTN_B_N`; no regression.
- **Opportunity & simplification.** The duplicate-ref lever is shared by router (`physical_net_pads`) and gate (`net_open_edges`), so the whole `SWx` user-button family (`BTN_A/UP/DOWN/LEFT/RIGHT_N` + `Net-(SW9-A)`, ~6 remaining genuine nets) is now routable by the proven mechanics — the largest coherent remaining functional block is unlocked.
- **Governance.** No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged. **Open owner decisions: NONE** (autonomy continues). Rollback: `git revert` this commit. All locked invariants preserved (D-249/D-257/D-269/D-275/D-288/D-290, In1/In4 GND roles, In2/In3 capacity, RF/USB/mechanical reservations, D-304..D-324); frozen `beta-full-reference-v1` untouched; journal authoritative (119). **NEXT FBV2-P2-028:** route the next `SWx` button net (fresh screen + vet first) or the next genuinely-clean functional open-region net under the D-286 gate + adding `incremental_probe_025`+`G38` on promote. 137/164 rest nets unrouted. PCB routing ~19 %, overall ~76 %, readiness ~78 % (JLCPCB file unchanged). Full analysis: [`audits/2026-08-31-p2-027-d325-duplicate-ref-mst-framework-btn-b-n-promoted.md`](audits/2026-08-31-p2-027-d325-duplicate-ref-mst-framework-btn-b-n-promoted.md).

## 2026-08-31 - FBV2-P2-026: D-324 — CHARACTERIZATION, no copper change (three pad-escape walls, no promote)

**NO COPPER CHANGE — the board is byte-identical to committed D-323** (`sha256 a7bf8bdc…`, 781 tracks / 68 vias / 6 layers / 41 zones / ratsnest 665 / journal 116). Three genuinely-functional open-region candidates from three different subsystems were vetted and scratch-routed and ALL hit characterized pad-escape walls at 0.200 mm; nothing was promotable via the proven mechanics without a deferred framework change (kept deferred by this mandate). ZERO router-logic change (three additive `GROUPS` characterization entries + comments only).

- **Screen + vet (READ-ONLY, live D-323 board).** `w/screen_020.py`: 138 unrouted rest nets, 38 ALLOW / 100 EXCL. The 38 ALLOW resolve to ~6 already-characterized walls + ~7 `SWx` duplicate-ref buttons (deferred) + converter/USB-C role-traps + the `BQ25185_STAT` power-tree pair + three huge hauls (`IR_RX_GPIO44` 132 mm, `DISP_SDO` 60 mm, `IR_GATE` 110 mm) + only THREE genuinely-clean functional candidates. `w/vet_021.py` measured the three.
- **Three characterized pad-escape walls (all scratch-routed, none promoted).** (1) `BMI270_INT1_RAW` (BMI270 IMU INT1 sensor-side leg `U4.4` B → series `R18.1` F, R18-isolated from the D-318 MCU-side strap; would COMPLETE the IMU interrupt path like D-308 completed D-304) → FAIL `NO_FAR_RUN` at 0.200 mm (R18.1 boxed in the dense MCU-south pocket; the `MCU_EN_RC` class). (2) `ACC_POWER_FAULT_N` (ACC 3V3 power-fault status `U20.6`+`U22.6`/`R103.2`/`TP27`+`TP33` → `U3.18`, all B.Cu) → FAIL `NO_LEGAL_ESCAPE` on `U20.6` (boxed by own-part pads U20.5/U20.1/U20.4; 3 of 5 edges route but the net can't complete; the `ISET`/`XGPIO2` boxed-pin class). (3) `DISP_BL_CTL` (backlight-driver control leg `R109.2` F → `U17.4` TPS61169 CTRL logic input B, R109-isolated from BL_SW/LED path) → FAIL `NO_FAR_RUN` at 0.200 mm (R109.2 in the same U1.16/backlight cluster that walled `DISP_BL_CTL_STRAP` at D-323). None has a bounded fix; all three `GROUPS` entries carry their OUTCOME annotation.
- **Board untouched.** `sha256 a7bf8bdc…` re-verified before/after (route writes only gitignored scratch `checks/w/INC_*`); `incremental_baseline_006.json` reverted stale-by-design.
- **Tests / integrity (board unchanged → all still PASS).** `router_regression.py` ALL PASS (G1–G35) deterministic twice (the three additive `GROUPS` entries are inert, like existing `BOOT_N`/`DISP_DC`/`MCU_EN_RC` records); `incremental_probe_006..023` + `phaseB_bringup_probe_005` (781/68/116; 26 routed rest nets, 138 unrouted) PASS; NO `live_fingerprint.py` bump (no copper); NO new probe / G-contract (no new copper to pin — the D-315 precedent); independent kicad-cli DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`); D-269/D-264/DRU trivially unchanged (byte-identical board → no regression possible; recorded run in the documented intrinsic-flake envelope `d269` FAIL(2) / `d264` 2-failed / `dru` FAIL(2)).
- **Opportunity & simplification.** Structural finding: after eighteen promoted increments the readily-clean open-region functional seam reachable by the proven mechanics is essentially mined out — the 138 remaining rest nets are dominated by role-excluded traps (~100), characterized walls, the `SWx` duplicate-ref button family, the saturated west-XGPIO F.Cu corridor, J1 display-FPC hauls, and boxed MCU/IC-pin pockets. Highest-value NEXT move: explicitly SELECT one deferred bounded framework task — the **duplicate-ref MST** (unlocks the ~7-net `SWx` user-input button family; `BTN_B_N` already routed ALL OK at D-323, failed only on the collapse) is recommended, or the In2/In3 inner-layer west-XGPIO traverse. No repetitive-maintenance consolidation due this round.
- **Governance.** No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged. **Open owner decisions: NONE** (the framework-task selection is a P2-027 recommendation, not a blocking decision — autonomy continues). Rollback: not applicable (no copper change). All locked invariants preserved (D-249/D-257/D-269/D-275/D-288/D-290, In1/In4 GND roles, In2/In3 capacity, RF/USB/mechanical reservations, D-304..D-323); frozen `beta-full-reference-v1` untouched; journal authoritative (116). **NEXT FBV2-P2-027:** EITHER select+land one bounded framework task (duplicate-ref MST recommended) routing its first newly-unlocked net under the D-286 gate + adding `incremental_probe_024.py`+`G36` on promote, OR route a genuinely-clean functional net if a fresh screen surfaces one. 138/164 rest nets unrouted. PCB routing ~18 %, overall ~76 %, readiness ~78 % (JLCPCB file unchanged). Full analysis: [`audits/2026-08-31-p2-026-d324-characterization-three-pad-escape-walls-no-promote.md`](audits/2026-08-31-p2-026-d324-characterization-three-pad-escape-walls-no-promote.md).

## 2026-08-31 - FBV2-P2-025: D-323 — EIGHTEENTH rest-of-board incremental increment routed and PROMOTED: the accelerometer/add-on presence-detect `ACC_DETECT_N` (3-pad cross-layer, ONE 0.60/0.30 through via + ONE same-layer B.Cu run), a clean increment in an OPEN region 3.88 mm-realized clear of `BAT_PROTECTED_P`; promoted after the cleaner-class `DISP_BL_CTL_STRAP` hit a characterized local wall and `BTN_B_N` failed the gate on the duplicate-ref tact-switch connectivity limit; a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision), ZERO router-logic change

**THE EIGHTEENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** D-322 promoted the reserved/spare community expander GPIO in an open region and mandated the next clean increment in an OPEN region, decided on measured merit (a meaningful coherent functional net preferred over an easy spare when equally clean; do not force a pair across a characterized wall; never route a converter-switching or USB-C connector net merely because the automatic screen says ALLOW). A fresh read-only screen (`w/screen_020.py`) + focused geometry vet (`w/vet_021.py`, live D-322 board) measured the genuinely-clean functional shortlist (netclass, MST edges, straight-path nearest-copper, `BAT_PROTECTED_P`/D-269 proximity). **Two cleaner-class candidates were tested FIRST and set aside:** `DISP_BL_CTL_STRAP` (the display backlight-control strap `U1.16` MCU GPIO / `TP2.1` test point / `R108.1` + `R109.1` series, R109 bridging to the SEPARATE downstream net `DISP_BL_CTL → U17.4` backlight driver — NOT in this increment; 4-pad, all F.Cu, no via, cong 185, 37.854 mm clear of BPP) hit a **characterized LOCAL WALL** — all three MST edges (incl. the SHORT `TP2.1↔U1.16` 5.44 mm and `TP2.1↔R109.1` 10.30 mm, not just the `U1.16↔R108.1` 24.77 mm haul) return `NO_PATH` at 0.200 mm (none even at the 0.05/0.025 mm fine grid) — the dense MCU/backlight pad pocket boxes every terminal (real 0.022 mm proximity to accepted D-318 `BMI270_INT1_STRAP` copper, 0.111 mm to `SD_CARD_DETECT_N`, 0.349 mm to `USB_D_ESD_P`), the `MCU_EN_RC` lesson repeated (`GROUPS['DISP_BL_CTL_STRAP']` annotated, do NOT naively retry at 0.200 mm); `BTN_B_N` (navigation/boot button `SW7.1` F.Cu → `R9.2` pull-up B.Cu → `U2.18` expander B.Cu, one 0.60/0.30 through via in the OPEN south button field, cong 141, 11.025 mm clear of BPP) **routed ALL OK but FAILED the real full-board gate on CONNECTIVITY** — the root cause (verified from the footprint) is that `SW7` is a 4-pin tactile switch whose TWO mechanically-linked terminals BOTH carry pad number "1" on `BTN_B_N` at (49.520, 96.750) and (57.480, 96.750) 7.96 mm apart, and the framework's per-ref MST (`pads_by_ref`) keys nodes by ref.padnum, so the two `SW7.1` pads collapse to a SINGLE node → the second terminal is never driven → one permanent open ratsnest edge (net open_edges 2→1 not 2→0) → gate FAIL; this is a connectivity gap of the WHOLE duplicate-ref button family (every `SWx` tact switch), NOT a copper casualty — the scratch route was discarded, the authoritative board never touched (`GROUPS['BTN_B_N']` annotated, do NOT naively retry any `SWx` net until a duplicate-ref MST lands). The selected candidate, **`ACC_DETECT_N`** (the accelerometer/add-on presence-detect: detect divider/pull `R64.1` F.Cu SMD north → series `R129.2` B.Cu SMD → PCAL9535A expander GPIO `U3.17` B.Cu SMD, a genuine functional low-current low-speed CMOS peripheral detect input — NOT the community-header bank, NOT a converter/rail), is a 3-pad net across TWO faces whose MST is ONE cross-layer edge `R64.1↔R129.2` (a single 0.60/0.30 Default THROUGH via) + ONE same-layer B.Cu edge `R129.2↔U3.17`, in an OPEN region **3.8831 mm-realized clear of `BAT_PROTECTED_P`** (>> the D-269 0.300 mm floor → zero D-269 involvement). Starting HEAD `36ffb2d` (D-322; pushed; `origin/master` identical).

- **Screen + vet (READ-ONLY, live D-322 board).** `w/vet_021.py` (re-verified): `ACC_DETECT_N` edges `R64.1↔R129.2` 19.64 mm CROSS + `R129.2↔U3.17` 19.31 mm same-B; congestion 103 (lowest of the genuinely-clean functional shortlist); straight-MST min to `BAT_PROTECTED_P` = 2.750 mm (>> D-269 0.300 floor). vet nearest-other-copper 0.228 mm (`NFC_5V_EN`) / 0.007 mm (`V3V3_FB`) = GUIDANCE ONLY. Default netclass (0.200 mm width/clearance).
- **`DISP_BL_CTL_STRAP` characterized local wall.** All three MST edges NO_PATH at 0.200 mm (fine grid too), including the short 5.44 mm and 10.30 mm edges — the boxed MCU/backlight pad pocket (cong 185), not an open MCU-pad escape like `SD_CS_N`/`UART0`. Characterized, annotated, not retried at 0.200 mm.
- **`BTN_B_N` duplicate-ref gate failure.** Routed clean on scratch but the per-ref MST collapses `SW7`'s two pad-"1" terminals (7.96 mm apart) to one node → one permanent open edge → gate FAIL (net open_edges 2→1). A connectivity gap of the whole `SWx` duplicate-ref button family, not a copper casualty; authoritative board NEVER touched; a "duplicate-ref MST" deferred framework task.
- **Route + gate (real full-board, D-286).** `route ACC_DETECT_N` ALL OK: `R129.2→U3.17` 35.311 mm B.Cu + `R129.2→R64.1` 20.861 mm (B+F via); 22 segments (3 F.Cu + 19 B.Cu, all 0.200 mm) + 1 via at (57.900, 38.800) in the OPEN north (34.157 mm from every existing barrel); routed copper clears `BAT_PROTECTED_P` by **3.8831 mm** → zero D-269. `gate ACC_DETECT_N` PASS every check: 0 Phase-A copper deleted/altered; 22 new tracks + 1 via all target-net; **only In1/In4 GND planes re-poured** (via anti-pad), other 39 zones identical; all three pads copper-connected, open_edges 2→0; 0 prior Phase-A/increment pairs regressed; ratsnest 667→665 (−2 exact); no new/worse DRC; unconnected 499→499. `promote` re-ran gate PASS, AUTH sha undrifted, merged 2 REST_INC edges (scratch board sha == AUTH sha, zero drift).
- **Promoted board.** `sha256 a861e30e…` → **`a7bf8bdc11f1bc39303c6f6b6c801e3a4a575add64596cc4be20745c57f9f626`**; tracks 759→**781** (+22: 3 F.Cu + 19 B.Cu, 0.200 mm); vias 67→**68** (+1 through via — the first new via since D-316); 6 layers / 41 zones; ratsnest 667→**665** (−2); journal 114→**116** (+2 REST_INC: `R129.2↔U3.17` B.Cu 35.311 mm, `R129.2↔R64.1` B+F via 20.861 mm). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests / integrity.** New **G35** (`ACC_DETECT_N` all 3 pads connected; copper legal 22 trk 0.200 = 3 F.Cu + 19 B.Cu + exactly 1 0.60/0.30 through via; via ≥ 0.80 mm from every barrel, measured 34.157 mm; ADD-ONLY — every prior increment + Phase-A 432/54 preserved); G18–G34 auto-generalise → `router_regression.py` ALL PASS G1–G35, deterministic twice (555 lines / 143 PASS each run, identical G-verdicts). New `incremental_probe_023.py` PASS; `_006..022` + `phaseB_bringup_probe_005` (781/68/116; 26 routed rest nets, 138 unrouted) PASS; `live_fingerprint.py` bumped once; `incremental_baseline_006.json` left stale-by-design (verified unmodified — the gate computes its baseline live). Independent kicad-cli DRC A/B IDENTICAL on committed D-322 and promoted D-323 (both same 6 violations, 499 unconnected). D-269/D-264/DRU board-swap A/B (committed D-322 vs promoted D-323), 4 runs each: `dru` FAIL(2)×4 on BOTH — IDENTICAL, deterministic; `d269` promoted PASS,FAIL(2),FAIL(2),FAIL(2) vs committed FAIL(2)×4 — flips, count always 2; `d264` promoted 2,1,2,3 vs committed 2,1,2,1 — both flip in the 1–3 range = documented intrinsic non-determinism (synthetic Phase-A DRU probes), pre-existing flakes not regressions (new copper is ~2.75–3.88 mm-from-BPP peripheral copper near R64/R129/U3.17, away from the BAT-divider/sense corridors the probes examine); live AUTH sha re-verified `a7bf8bdc…` after the swap.
- **Probe via-total generalization (the ONLY code beyond the GROUPS entry + comments).** D-323 lays the FIRST new via since D-316, so the board via total moved 67→68. The no-via probes `incremental_probe_018..022` pinned the board via total to a hard-coded **67** at their "no-via class" check; this was generalized to `len(via) == EXPECT_VIAS` (the `live_fingerprint` single source of truth), KEEPING each probe's per-net `len(i_via) == 0` contract intact (semantically sound + regression-safe: each net's no-via property is still asserted, only the redundant board-total literal now tracks the SoT, exactly as tracks/ratsnest/journal already do — all 8 prior via-probes `008..017` already pin the total via `EXPECT_VIAS`). `incremental_probe_023.py`'s second via check (which had hard-coded 68) was ALSO aligned to the same `EXPECT_VIAS` convention, keeping its per-net `i_via == 1` contract, so probe_023 survives the next via increment like every prior via-probe (re-verified PASS). ZERO contract weakened.
- **Opportunity & simplification.** New characterized walls: `DISP_BL_CTL_STRAP` boxed MCU/backlight pocket (all 3 edges NO_PATH at 0.200); the WHOLE duplicate-ref button family (`SWx`) blocked by the `pads_by_ref` MST collapse → a "duplicate-ref MST" deferred framework task (alongside the In2/In3 inner-layer west-XGPIO haul). `MCU_EN_RC`, the J1 display-connector haul (`DISP_CS_N`/`DISP_DC`), `BOOT_N`, `U11_PROG`/`PWR_SENSE` all remain characterized. 138/164 rest nets unrouted (26 routed) — continue one clean net/group at a time. No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged.
- **Open owner decisions: NONE.** Rollback: pre-promotion `sha256 a861e30e…` (committed D-322, HEAD `36ffb2d`). PCB routing ~18 %, overall ~76 %, readiness ~78 % (authoritative; JLCPCB file unchanged). **NEXT FBV2-P2-026:** route the next clean rest-of-board increment (single net or small coherent local group in an open region — a fresh `w/screen_020.py` + `w/vet_021.py` pick) at its netclass Default under the D-286 gate; add `incremental_probe_024.py`+`G36` and bump `live_fingerprint.py` once; continue avoiding the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass, the auto-ALLOW converter/USB-C connector traps and every characterized wall (`MCU_EN_RC`, the J1 display-connector haul `DISP_CS_N`/`DISP_DC`, `BOOT_N`, the `DISP_BL_CTL_STRAP` boxed pocket, `U11_PROG`/`PWR_SENSE`); do NOT retry the `SWx` duplicate-ref button family until a duplicate-ref MST lands; hold the inner-layer west-XGPIO haul + the duplicate-ref button MST as deferred framework tasks; 138/164 rest nets unrouted. Full analysis: [`audits/2026-08-31-p2-025-d323-eighteenth-rest-of-board-incremental-increment-acc-detect-n-promoted.md`](audits/2026-08-31-p2-025-d323-eighteenth-rest-of-board-incremental-increment-acc-detect-n-promoted.md).

## 2026-08-31 - FBV2-P2-024: D-322 — SEVENTEENTH rest-of-board incremental increment routed and PROMOTED: the reserved/spare community expander GPIO `RESERVED_SPARE` (3-pad, SAME-LAYER B.Cu MST, NO via), a clean increment in an OPEN region 15.5 mm clear of `BAT_PROTECTED_P`; the held clean alternate, promoted after the meaningful display-control candidates `DISP_CS_N`/`DISP_DC` hit a characterized J1 display-FPC-connector wall and `BOOT_N` routed only via poor 2.5× detours; a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision), ZERO router-logic change

**THE SEVENTEENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** D-321 promoted the microSD SPI chip-select in an open region and mandated the next clean increment in an OPEN region, deeply vetting `RESERVED_SPARE`, `BOOT_N`, `DISP_DC` plus 1–2 other genuinely-functional candidates — preferring meaningful function over a spare when equally clean, treating `BOOT_N` sensitivity carefully, and never routing a converter-switching or USB-C connector net merely because the automatic screen says ALLOW. A fresh read-only screen (`w/screen_020.py`) measured all 140 unrouted rest nets (40 ALLOW / 100 EXCL); the auto-classifier trap was re-confirmed and its converter-switching/IR-emitter/USB-C auto-ALLOW nets rejected on measured role. A focused geometry vet (`w/vet_021.py`) measured the mandate's shortlist + two other functional candidates: `RESERVED_SPARE` (cong 84, B.Cu, 15.5 mm clear of BPP), `DISP_CS_N` (cong 184), `DISP_DC` (cong 203), `BOOT_N` (cong 231), `DISP_BL_CTL_STRAP` (cong 185). **The meaningful display-control candidates were tested FIRST (prefer function over a spare):** `DISP_CS_N` (the display SPI chip-select `U1.18`/`R26.2`/`J1.38`, the direct analog of D-321's `SD_CS_N`) routes its short MCU-side edge clean off the series resistor `R26.2` but its long `J1.38↔R26.2` haul to the tight display connector returns `NO_PATH` at 0.200 mm (even the 0.05/0.025 mm fine grid); `DISP_DC` (`U1.22 → J1.37`, adjacent FPC pin) ALSO returns `NO_PATH` — **characterizing the J1 display-FPC-connector interior haul as a shared local wall** (`GROUPS['DISP_CS_N']`/`['DISP_DC']` annotated, do NOT naively retry). `BOOT_N` (the meaningful non-J1 alternative, the ESP32 boot-mode strap `SW1.1`/`R2.2`/`U1.27`) routed ALL OK but only via poor 2.5× detours (~110 mm of meandering copper for a boot-critical strap) — not equally clean, set aside (sensitivity treated carefully). The held clean alternate **`RESERVED_SPARE`** (`R130.2` + `TP41.1` + `U23.7` PCAL expander, all B.Cu → two SAME-LAYER B.Cu runs with NO via, the cleanest incremental class, in an OPEN region **15.5 mm clear of `BAT_PROTECTED_P`**) was routed, gated PASS, and promoted. Starting HEAD `e3e2a8d` (D-321; pushed; `origin/master` identical).

- **Screen + vet (READ-ONLY, live D-321 board).** `w/screen_020.py`: 140 unrouted rest nets, 40 ALLOW / 100 EXCL. `w/vet_021.py` measured the functional shortlist; `RESERVED_SPARE` = 3-pad Default B.Cu, MST 3.54 + 9.80 mm same-layer, 15.503 mm clear of `BAT_PROTECTED_P` (zero D-269).
- **J1 display-connector wall (`DISP_CS_N`/`DISP_DC`).** Scratch routes: `DISP_CS_N` short edge `R26.2↔U1.18` OK (2.9 mm) but long `J1.38↔R26.2` NO_PATH at 0.200 mm (fine grid); `DISP_DC` single `J1.37↔U1.22` NO_PATH at 0.200 mm. A genuine local congestion wall at the tight J1 display FPC connector; characterized, annotated, not retried at 0.200 mm.
- **`BOOT_N` set aside.** Scratch route ALL OK but `R2.2↔U1.27` 62.9 mm (vs 25.4 straight, 2.48×) + `U1.27↔SW1.1` 47.2 mm (vs 22.4, 2.11×) = ~110 mm of copper for a boot-critical strap — not equally clean, sensitivity treated carefully.
- **Route + gate (real full-board, D-286).** `route RESERVED_SPARE` ALL OK: `R130.2→U23.7` 4.434 mm + `U23.7→TP41.1` 10.939 mm, 10 B.Cu segments, 0 via. `gate RESERVED_SPARE` PASS every check: 0 Phase-A altered; 10 new items all target-net; **0 zones fill-changed** (no via → no In1/In4 re-pour); all three pads copper-connected, open_edges 2→0; 0 prior pairs regressed; ratsnest 669→667 (−2 exact); no new/worse DRC; unconnected 499→499. `promote` re-ran gate PASS, AUTH sha undrifted, merged 2 REST_INC edges.
- **Promoted board.** `sha256 68d44b54…` → **`a861e30e5760515288ef9a3fc0c21ea6d3e9c31409f9181dd66d56ed0628efd1`**; tracks 749→**759** (+10 B.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 669→**667** (−2); journal 112→**114** (+2 REST_INC). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests / integrity.** New **G34** (all three pads connected, 10 trk 0.200 B.Cu 0 vias, ADD-ONLY); G18–G33 auto-generalise → `router_regression.py` ALL PASS G1–G34, deterministic twice; new `incremental_probe_022.py` PASS; `_006..021` + `phaseB_bringup_probe_005` (759/67/114; 25 routed rest nets, 139 unrouted) PASS; `live_fingerprint.py` bumped once; `incremental_baseline_006.json` left stale-by-design (reverted); independent kicad-cli DRC matches (`clearance` 0, 0 schematic-parity); D-269/D-264/DRU board-swap A/B (committed D-321 vs promoted D-322) — `d269` FAIL(2)=FAIL(2) and `dru` FAIL(2)=FAIL(2) IDENTICAL, `d264` differed single-run (3 vs 2) but four-run repeats proved intrinsic (flips 1,2,2,2 on committed D-321 and 2,1,1,3 on promoted D-322, both byte-identical) = documented intrinsic non-determinism, all pre-existing flakes not regressions (new copper is B.Cu near U23/R130/TP41, ~15 mm from the BAT tree the probes test).
- **Governance.** No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged. Open owner decisions: NONE. Rollback: pre-promotion `sha256 68d44b54…` (committed D-321, HEAD `e3e2a8d`). PCB routing ~18 %, overall ~76 %, readiness ~78 % (authoritative; JLCPCB file unchanged). **NEXT FBV2-P2-025:** the next clean rest-of-board increment (a fresh screen pick) under the D-286 gate; add `incremental_probe_023.py`+`G35`; keep avoiding the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass, the auto-ALLOW converter/USB-C traps, the `MCU_EN_RC` wall and the J1 display-connector-haul wall; 139/164 rest nets unrouted.

## 2026-08-31 - FBV2-P2-023: D-321 — SIXTEENTH rest-of-board incremental increment routed and PROMOTED: the microSD SPI chip-select `SD_CS_N` (3-pad, SAME-LAYER F.Cu MST, NO via), a clean increment in an OPEN region 50.1 mm clear of `BAT_PROTECTED_P`; the mandate's headline candidate `Net-(U1-EN)` hit a characterized local wall and was set aside; a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision), ZERO router-logic change

**THE SIXTEENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** D-320 promoted the IR transmit carrier control leg in an open region and mandated the next clean increment in an OPEN region, decided on measured merit (a meaningful coherent functional net preferred over an easy spare when equally clean; treat MCU EN/BOOT sensitivity carefully; do not accidentally route a converter-switching or USB-C connector net merely because the automatic screen says ALLOW), deeply vetting `Net-(U1-EN)`, `RESERVED_SPARE`, `BOOT_N` plus 1–2 other functional candidates. A read-only screen (`w/screen_020.py`) measured all 141 unrouted rest nets (41 ALLOW / 100 EXCL); the auto-classifier trap was re-confirmed and its converter-switching (`Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW`), IR-emitter power (`IR_LED_A/K`) and USB-C connector (`Net-(J3-CC1/CC2/SHIELD)`) auto-ALLOW nets were rejected on measured role. A focused geometry vet (`w/vet_021.py`) measured the genuinely-clean functional shortlist: `Net-(U1-EN)` (cong 66), `RESERVED_SPARE` (cong 84), `SD_CS_N` (cong 102), `BOOT_N`/`DISP_DC` (cong 203). **The mandate's headline candidate `Net-(U1-EN)`** (the ESP32 EN power-on-reset RC: `U1.3` EN + `R1.1` pull-up + `C1.2` filter cap) was scratch-tested FIRST and hit a **characterized LOCAL WALL** — its natural MST short edge `C1.2↔U1.3` (7.81 mm) returns `NO_PATH` at 0.200 mm (none even at the 0.05/0.025 mm fine grid) in the dense U1-EN pad pocket, and the other edge only routes with a 58.46 mm detour (2.6× straight) — a poor path for a reset line also carrying a 0.335 mm `USB_D_MCU_N` proximity flag; treating the EN sensitivity carefully, EN was NOT promoted (`GROUPS['MCU_EN_RC']` annotated **do NOT naively retry**). The held functional alternate and selected candidate, **`SD_CS_N`** (`U1.25` MCU + `R25.2` + `J2.2` microSD socket, the microSD SPI chip-select), is a genuine functional **point-to-point control** (NOT a shared MOSI/MISO/CLK bus line — the chip-select travels with its own synchronous SPI-A bus, benign coupling) whose 3-pad MST is two **SAME-LAYER F.Cu runs with NO via** — the cleanest incremental class — in an OPEN region **50.1 mm clear of `BAT_PROTECTED_P`** (zero D-269 involvement), chosen over `RESERVED_SPARE` (a spare of lower merit, routed clean on scratch and HELD). Starting HEAD `bb7fed4` (D-320; pushed; `origin/master` identical).

- **Screen + vet (READ-ONLY, live D-320 board).** `w/screen_020.py`: 141 unrouted rest nets, 41 ALLOW / 100 EXCL (EXCL: 31 RF/NFC/radio, 16 switching/rail/class-D, 15 west/east XGPIO, 13 shared data/I2C bus, 8 USB, 4 RF SPI, 4 community-header, 3 crystal/clock, 2 `PWR_SENSE`, 2 `U11_PROG`, 2 bulk rail). `w/vet_021.py` measured the functional shortlist; `SD_CS_N` = 3-pad Default, MST 14.99 + 31.98 mm same-layer, 50.076 mm clear of `BAT_PROTECTED_P`.
- **MCU_EN_RC wall (`Net-(U1-EN)`).** Scratch route: `C1.2↔U1.3` NO_PATH (0.05/0.025 mm fine grid); `U1.3↔R1.1` OK but 58.457 mm (2.6×). A genuine local congestion wall around the EN pin; not worth a bounded framework change for a sensitive reset line with a USB-proximity flag. Characterized, held, not retried.
- **Route + gate (real full-board, D-286).** `route SD_CS_N` ALL OK: `J2.2→U1.25` 48.420 mm + `U1.25→R25.2` 21.081 mm, 20 F.Cu segments, 0 via. `gate SD_CS_N` PASS every check: 0 Phase-A altered; 20 new items all target-net; **0 zones fill-changed** (no via → no In1/In4 re-pour); all three pads copper-connected, open_edges 2→0; 0 prior pairs regressed; ratsnest 671→669 (−2 exact); no new/worse DRC; unconnected 499→499. `promote` re-ran gate PASS, AUTH sha undrifted, merged 2 REST_INC edges.
- **Promoted board.** `sha256 4e706490…` → **`68d44b54df91d607f689215c0da5db249b13fcd1ac189b9ab78ceb6366d25e46`**; tracks 729→**749** (+20 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 671→**669** (−2); journal 110→**112** (+2 REST_INC). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests / integrity.** New **G33** (all three pads connected, 20 trk 0.200 F.Cu 0 vias, ADD-ONLY); G18–G32 auto-generalise → `router_regression.py` ALL PASS (G1–G33), deterministic twice. New `incremental_probe_021.py` PASS; `_006..020` + `phaseB_bringup_probe_005` (749/67/112; 24 routed rest nets, 140 unrouted) PASS. `live_fingerprint.py` bumped once to D-321; `incremental_baseline_006.json` left stale-by-design (reverted). Independent kicad-cli DRC (`--format json --severity-error --schematic-parity`) = `{solder_mask_bridge:1, hole_clearance:5}`, 499 unconnected, 0 schematic-parity, 0 `clearance`. D-269/D-264/DRU board-swap A/B (committed D-320 vs promoted D-321): `dru` FAIL(2)=FAIL(2) IDENTICAL; `d269` (FAIL,PASS,FAIL,PASS) and `d264` (2,2,3,2) flip on the byte-identical D-320 board = documented intrinsic non-determinism, all pre-existing flakes not regressions (new copper is F.Cu near U1.25/J2.2/R25.2, ~50 mm from the BAT tree the probes test); live AUTH sha re-verified `68d44b54…` after the swap.
- **Opportunity & simplification.** Many of the 140 remaining rest nets are same-layer no-via control nets in open regions — continue one clean net/group at a time. Held clean alternates for FBV2-P2-024: `RESERVED_SPARE` (routed clean on scratch), `BOOT_N`, `DISP_DC`, or a fresh screen pick. `MCU_EN_RC` (`Net-(U1-EN)`) is a characterized wall — do NOT naively retry. The In2/In3 inner-layer west-XGPIO haul remains the deferred framework task. No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged.
- **Open owner decisions: NONE.** Rollback: pre-promotion `sha256 4e706490389655cb8b68f8c15249a813072f36a9ea9e6ffaeb1fdd2194c0bf34` (committed D-320, HEAD `bb7fed4`). Full analysis: [`audits/2026-08-31-p2-023-d321-sixteenth-rest-of-board-incremental-increment-sd-cs-n-promoted.md`](audits/2026-08-31-p2-023-d321-sixteenth-rest-of-board-incremental-increment-sd-cs-n-promoted.md).

---

## 2026-08-31 - FBV2-P2-022: D-320 — FIFTEENTH rest-of-board incremental increment routed and PROMOTED: the IR transmit carrier CONTROL leg `IR_TX_GPIO16` (2-pad, SAME-LAYER F.Cu MST, NO via), a clean increment in an OPEN region 35.2 mm clear of `BAT_PROTECTED_P`; a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision), ZERO router-logic change

**THE FIFTEENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** D-319 promoted the debug-console UART transmit line in an open region and mandated the next clean increment in an OPEN region, decided on measured merit (best coherent low-risk increment, not merely the shortest or the easiest spare; do not accidentally route a converter-switching or connector net merely because the automatic screen says ALLOW), with `IR_TX_GPIO16` to be treated as the low-current MCU control/carrier GPIO only — distinct from the excluded `IR_LED_A/K` emitter-power / switch path — and its topology/isolation verified before selection. A read-only screen (`w/screen_020.py`) measured all 142 unrouted rest nets (42 ALLOW / 100 EXCL); the auto-classifier trap was re-confirmed and its converter-switching (`Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW`) and USB-C connector (`Net-(J3-CC1/CC2/SHIELD)`) auto-ALLOW nets were rejected on measured role. A focused geometry vet (`w/vet_021.py`) measured the genuinely-clean functional shortlist and **confirmed the isolation**: the net `/IR_TX_GPIO16` = {`U1.9`, `R22.1`}; the far side `R22.2` belongs to the SEPARATE net `IR_GATE` ({`Q1.1`, `R22.2`, `R23.1`} = the Q1 gate/switch node) and the emitter-power path is `IR_LED_A`/`IR_LED_K` — both EXCLUDED and NOT part of this increment; series resistor R22 isolates the MCU control leg from the switching output. The selected candidate, **`IR_TX_GPIO16`** (`U1.9` ESP32 GPIO16 → `R22.1` series-drive resistor, the IR transmit carrier control leg), is a dedicated 2-pad point-to-point net whose single MST edge is a **SAME-LAYER F.Cu run with NO via** — the cleanest incremental class — in an OPEN region **35.2 mm clear of `BAT_PROTECTED_P`** (zero D-269 involvement). Starting HEAD `8d27e3a` (D-319; pushed; `origin/master` identical).

- **Evidence-first selection.** `w/vet_021.py` measured, per candidate, pad layers/positions, netclass, MST edges (length + same/cross layer), straight-path nearest-other copper, and straight-MST distance to `BAT_PROTECTED_P`. `IR_TX_GPIO16` (cong 38, no via, 35.2 mm from BPP, genuine functional MCU control role) was chosen over `Net-(U1-EN)` (cong 59, 2 edges incl. a 22 mm haul 0.335 mm from the USB_D_MCU_N diff pair, EN a more sensitive reset line) and `RESERVED_SPARE` (a mere spare of lower merit — not chosen when a meaningful control net is equally clean). The excluded IR switch/emitter nets `IR_GATE`/`IR_LED_A`/`IR_LED_K` were confirmed distinct and set aside.
- **Route→gate→promote (real full-board, D-286).** New single-net `GROUPS['IR_TX_GPIO16']` (`layer='F'`, Default 0.200 mm, no via); `incremental_router.py`/`qrouter.py` logic UNCHANGED. `route` ALL OK (single F.Cu run R22.1↔U1.9, a legal same-layer detour to 23.153 mm / 13 seg around the GND pinch on the straight 8.35 mm path, 0 via). `gate` PASS every check (0 Phase-A altered, 13 new items all target-net, 0 zones fill-changed — no via, net open_edges 1→0, 0 prior pairs regressed, ratsnest 672→671 −1, no new/worse DRC, unconnected 499→499). `promote` re-ran gate PASS, AUTH sha undrifted, merged 1 REST_INC edge.
- **Promoted:** `sha256 57dcc8af…` → **`4e706490389655cb8b68f8c15249a813072f36a9ea9e6ffaeb1fdd2194c0bf34`**; tracks 716→**729** (+13 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 672→**671** (−1); journal 109→**110** (+1 REST_INC). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests:** new **G32** (both pads connected; 13 trk 0.200 mm all F.Cu, 0 vias; ADD-ONLY); G18–G31 auto-generalise → `router_regression.py` ALL PASS (G1–G32), deterministic twice; new `incremental_probe_020.py` PASS; `_006..019` + `phaseB_bringup_probe_005` (729/67/110; 23 routed rest nets, 141 unrouted) PASS; `live_fingerprint.py` bumped once (D-320); `incremental_baseline_006.json` left stale-by-design (reverted); independent kicad-cli DRC matches (`clearance` 0); D-269/D-264/DRU board-swap A/B (committed D-319 vs promoted D-320) — `d269` FAIL(2)=FAIL(2) and `dru` FAIL(2)=FAIL(2) IDENTICAL, `d264` flips on both byte-identical boards (D-320 1,2,2,1; D-319 2,1,2,2) = documented intrinsic non-determinism, all pre-existing flakes not regressions.
- **Opportunity & Simplification:** many of the 141 remaining rest nets are same-layer no-via control nets in open regions away from the west corridor + BAT tree — continue one clean net/group at a time; `w/screen_020.py` + `w/vet_021.py` remain the reusable evidence-first pair; In2/In3 inner-layer west-XGPIO haul stays the deferred framework task. No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged.
- **NEXT FBV2-P2-023:** route the next clean rest-of-board increment (single net or small coherent local group in an open region — `Net-(U1-EN)`/`RESERVED_SPARE`/`BOOT_N` or a fresh screen pick) at its netclass Default under the D-286 gate, add `incremental_probe_021.py`+`G33` on promote; continue avoiding the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass and the auto-ALLOW converter-switching/USB-C connector traps; hold the inner-layer west-XGPIO haul as the deferred framework task. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 57dcc8af…` (committed D-319, HEAD `8d27e3a`). Full analysis: [`audits/2026-08-31-p2-022-d320-fifteenth-rest-of-board-incremental-increment-ir-tx-gpio16-promoted.md`](audits/2026-08-31-p2-022-d320-fifteenth-rest-of-board-incremental-increment-ir-tx-gpio16-promoted.md).

## 2026-08-31 - FBV2-P2-021: D-319 — FOURTEENTH rest-of-board incremental increment routed and PROMOTED: the debug-console UART transmit line `UART0_TXD_DBG` (2-pad, SAME-LAYER F.Cu MST, NO via), a clean increment in an OPEN region 31.3 mm clear of `BAT_PROTECTED_P`; a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision), ZERO router-logic change

**THE FOURTEENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** D-318 promoted the first clean increment outside the west-XGPIO corridor and mandated the next clean increment in an OPEN region, decided on measured merit (best coherent low-risk increment, not merely the shortest; do not force a pair across a characterized power-tree wall; do not accidentally route a converter-switching or connector net merely because the automatic screen says ALLOW). A read-only screen (`w/screen_020.py`) measured all 143 unrouted rest nets (43 ALLOW / 100 EXCL); the auto-classifier trap was re-confirmed and its converter-switching (`Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW`, the 16-pad power net `BQ25185_SYS`) and USB-C connector (`Net-(J3-CC1/CC2/SHIELD)`) auto-ALLOW nets were rejected on measured role. A focused geometry vet (`w/vet_021.py`) measured the genuinely-clean functional shortlist. The selected candidate, **`UART0_TXD_DBG`** (U1.37 ESP32 MCU → TP35.1 test point, the debug-console UART0 transmit output), is a dedicated 2-pad point-to-point net whose single MST edge is a **SAME-LAYER F.Cu run with NO via** — the cleanest incremental class — in an OPEN region **31.3 mm clear of `BAT_PROTECTED_P`** (zero D-269 involvement). Starting HEAD `c7313cc` (D-318; pushed; `origin/master` identical).

- **Evidence-first selection + pair rejection.** `w/vet_021.py` measured, per candidate, pad layers/positions, netclass, MST edges (length + same/cross layer), straight-path nearest-other copper, and straight-MST distance to `BAT_PROTECTED_P`. `UART0_TXD_DBG` (cong 9, no via, 31.3 mm from BPP) beat `IR_TX_GPIO16` (cong 38), `Net-(U1-EN)` (cong 56), `RESERVED_SPARE` (cong 84). The vetted `BQ25185_STAT1/STAT2` charger-status pair was measured **NOT low-risk** (STAT2 straight-MST 0.024 mm from `BAT_PROTECTED_P`, both 4-pad hauls thread the U11/BQ25185 power-tree wall) → rejected under "do not force a pair across a characterized power-tree wall"; `IR_LED_A`/`IR_LED_K` set aside as the IR-emitter power/Q1 switch node.
- **Route→gate→promote (real full-board, D-286).** New single-net `GROUPS['UART0_TXD_DBG']` (`layer='F'`, Default 0.200 mm, no via); `incremental_router.py`/`qrouter.py` logic UNCHANGED. `route` ALL OK (single F.Cu run TP35.1↔U1.37 31.755 mm; 7 seg, 0 via). `gate` PASS every check (0 Phase-A altered, 7 new items all target-net, 0 zones fill-changed — no via, net open_edges 1→0, 0 prior pairs regressed, ratsnest 673→672 −1, no new/worse DRC, unconnected 499→499). `promote` re-ran gate PASS, AUTH sha undrifted, merged 1 REST_INC edge.
- **Promoted:** `sha256 78bf82da…` → **`57dcc8affb6c0f85f747fba025463b9cf0897c6712709692151020f56fdb8adf`**; tracks 709→**716** (+7 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 673→**672** (−1); journal 108→**109** (+1 REST_INC). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests:** new **G31** (both pads connected; 7 trk 0.200 mm all F.Cu, 0 vias; ADD-ONLY); G18–G30 auto-generalise → `router_regression.py` ALL PASS (G1–G31), deterministic twice; new `incremental_probe_019.py` PASS; `_006..018` + `phaseB_bringup_probe_005` (716/67/109; 22 routed rest nets, 142 unrouted) PASS; `live_fingerprint.py` bumped once (D-319); `incremental_baseline_006.json` left stale-by-design (reverted); independent kicad-cli DRC matches (`clearance` 0); D-269/D-264/DRU board-swap A/B (committed D-318 vs promoted D-319) — `d269` FAIL(2)=FAIL(2) and `dru` FAIL(2)=FAIL(2) IDENTICAL, `d264` flips 1↔2 on the byte-identical D-319 board (1,2,2,1) = documented intrinsic non-determinism, all pre-existing flakes not regressions.
- **Opportunity & Simplification:** many of the 142 remaining rest nets are same-layer no-via control nets in open regions away from the west corridor + BAT tree — continue one clean net/group at a time; `w/vet_021.py` is now a reusable read-only geometry vet complementing `w/screen_020.py`; In2/In3 inner-layer west-XGPIO haul stays the deferred framework task. No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged.
- **NEXT FBV2-P2-022:** route the next clean rest-of-board increment (single net or small coherent local group in an open region — `IR_TX_GPIO16`/`Net-(U1-EN)`/`RESERVED_SPARE` or a fresh screen pick) at its netclass Default under the D-286 gate, add `incremental_probe_020.py`+`G32` on promote; continue avoiding the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass and the auto-ALLOW converter-switching/USB-C connector traps; hold the inner-layer west-XGPIO haul as the deferred framework task. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 78bf82da…` (committed D-318, HEAD `c7313cc`). Full analysis: [`audits/2026-08-31-p2-021-d319-fourteenth-rest-of-board-incremental-increment-uart0-txd-dbg-promoted.md`](audits/2026-08-31-p2-021-d319-fourteenth-rest-of-board-incremental-increment-uart0-txd-dbg-promoted.md).

## 2026-08-31 - FBV2-P2-020: D-318 — THIRTEENTH rest-of-board incremental increment routed and PROMOTED: the IMU/I2C-local interrupt strap `BMI270_INT1_STRAP` (4-pad, ALL F.Cu same-layer MST, NO via), the first clean increment OUTSIDE the saturated west-XGPIO F.Cu corridor (the D-317 mandate); a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision), ZERO router-logic change

**THE THIRTEENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD — the first OUTSIDE the west XGPIO corridor.** D-317 characterised `XGPIO2` as a corridor-capacity wall and mandated the next clean increment in an OPEN region. The stale `CURRENT_STATE.md` §5 (which still said FBV2-P2-018) was repaired to the D-317 truth (FBV2-P2-020); a read-only screen (`w/screen_020.py`) then measured all 144 unrouted rest nets (44 ALLOW / 100 EXCL). The selected candidate, **`BMI270_INT1_STRAP`** (R18.2/R110.1/TP3.1 → U1.15 GPIO, the BMI270 IMU INT1 interrupt MCU-side leg — the mandate's welcomed IMU/I2C-local category), is a 4-pad multi-terminal net whose MST is **three SAME-LAYER F.Cu runs with NO via** — the cleanest incremental class. Starting HEAD `cacb68d` (D-317; pushed; `origin/master` identical).

- **Evidence-first selection.** `w/screen_020.py` ranked all 144 unrouted rest nets (pad layers/span/MST/via-need/congestion/netclass + category screen); rejected the mandate-forbidden classes (west/east XGPIO corridor, RF/NFC/radio incl. `04_SPI_B`, USB, shared bus data/clocks, switching/boost/class-D, community-header mass, `U11_PROG`, `PWR_SENSE`, rails). Cleanest ALLOW no-via singletons vetted on merit (several auto-ALLOW nets are actually converter-switching / USB-C connector nets — rejected on inspection). Alternates held: `UART0_TXD_DBG`, `RESERVED_SPARE`, `BQ25185_STAT1/2`. No bundling for throughput.
- **Route→gate→promote (real full-board, D-286).** New single-net `GROUPS['IMU_INT1_STRAP']` (`layer='F'`, Default 0.200 mm, no via); `incremental_router.py`/`qrouter.py` logic UNCHANGED. `route` ALL OK (R110.1↔R18.2 2.829 mm, R18.2↔U1.15 4.646 mm, R110.1↔TP3.1 11.682 mm; 18 F.Cu seg, 0 via). `gate` PASS every check (0 Phase-A altered, 18 new items all target-net, 0 zones fill-changed — no via, net open_edges 3→0, 0 prior pairs regressed, ratsnest 676→673 −3, no new/worse DRC, unconnected 499→499). `promote` re-ran gate PASS, AUTH sha undrifted, merged 3 REST_INC edges.
- **Promoted:** `sha256 d730c74d…` → **`78bf82da537a22697a860c23822599246e0534a8c4c311e12bc3d5b857a28816`**; tracks 691→**709** (+18 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 676→**673** (−3); journal 105→**108** (+3 REST_INC). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests:** new **G30** (all four pads connected; 18 trk 0.200 mm all F.Cu, 0 vias; ADD-ONLY); G18–G29 auto-generalise → `router_regression.py` ALL PASS (G1–G30), deterministic twice; new `incremental_probe_018.py` PASS; `_006..017` + `phaseB_bringup_probe_005` (709/67/108; 21 routed rest nets, 143 unrouted) PASS; `live_fingerprint.py` bumped once (D-318); independent kicad-cli DRC matches (`clearance` 0, 0 schematic-parity); D-269/D-264/DRU board-swap A/B (committed D-316 vs promoted D-318) verdicts IDENTICAL (pre-existing synthetic/intrinsic flakes, not regressions).
- **Opportunity & Simplification:** many of the 143 remaining rest nets are same-layer no-via control nets in open regions away from the west corridor + BAT tree — continue one clean net/group at a time; In2/In3 inner-layer west-XGPIO haul stays the deferred framework task. No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged.
- **NEXT FBV2-P2-021:** route the next clean rest-of-board increment (single net or small coherent local group in an open region) at its netclass Default under the D-286 gate, add `incremental_probe_019.py`+`G31` on promote; continue avoiding the west XGPIO corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass; hold the inner-layer west-XGPIO haul as the deferred framework task. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 d730c74d…` (committed D-316, HEAD `cacb68d`). Full analysis: [`audits/2026-08-31-p2-020-d318-thirteenth-rest-of-board-incremental-increment-imu-int1-strap-promoted.md`](audits/2026-08-31-p2-020-d318-thirteenth-rest-of-board-incremental-increment-imu-int1-strap-promoted.md).

## 2026-08-31 - FBV2-P2-019: D-317 — the SINGLE west XGPIO net `XGPIO2` is now a MEASURED CORRIDOR-CAPACITY WALL on the live D-316 board — NOT PROMOTED; a governed CTO characterization with ZERO authoritative copper change (board byte-identical to committed D-316), autonomy CONTINUES, no owner decision

**NO COPPER CHANGE — CLEAN CHARACTERIZATION BOUNDARY.** D-316 promoted the single west XGPIO net `XGPIO3` (R54.1 F.Cu → U3.7 B.Cu) and named `XGPIO2` (R53.1 F.Cu → U3.6 B.Cu) as the next candidate, with the explicit caution that its pre-D-316 0.6859 mm BPP margin must not be assumed to survive the added XGPIO3 copper/via. Screened faithfully on the live D-316 board → **`XGPIO2` alone at 0.200 mm does not route (NO_FAR_RUN).** The authoritative PCB is untouched (`sha256 d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d`, 691 trk / 67 via / ratsnest 676 / journal 105). Starting HEAD `6410e1f` (D-316; pushed; `origin/master` identical).

- **`XGPIO2` alone @ 0.200 mm Default → FAIL NO_FAR_RUN** (`w/screen_019.py`, one managed foreground process, 67 existing barrels injected incl. the D-316 XGPIO3 via): escape from U3.6 succeeds but the long ~116 mm F.Cu haul from R53.1 has **no legal 0.200 mm corridor**. The **one authorized bounded alternative** — the existing D-310 `via_offset` transition relocation (2.5 mm, **zero new router logic**), `w/screen_019_offset.py` — **also FAILs NO_FAR_RUN**, proving the wall is the **haul corridor**, not the via site.
- **This is the D-315 corridor-capacity wall realized.** D-315 proved the D-313/D-314-congested west F.Cu corridor admits ONE 116 mm haul, not two parallel ones; D-316 spent that one slot on the `XGPIO3` haul (now REAL laid copper); `XGPIO2` (R53, U3.6) is the blocked second parallel haul. On the D-314 board (before XGPIO3) `XGPIO2` alone routed at (55.300, 78.150) — but that site is now 0.450 mm centre-to-centre from the D-316 `XGPIO3` barrel (55.300, 77.700), a hole-hole 0.150 mm < 0.25 collision — so **the 0.6859 mm margin did not survive**, exactly as the task required verifying.
- **Integrity (board pristine):** `sha256 d730c74d…` before/after both screens (no `route`/`gate`/`promote` on the authoritative project; only gitignored `w/{SGL019_2, SGL019O_2}` scratch; no orphan; git tree clean). `router_regression.py` **ALL PASS G1–G29 twice (deterministic)**; `incremental_probe_006..017` + `phaseB_bringup_probe_005` (691/67/105; 20 routed rest nets, 144 unrouted) all PASS; `live_fingerprint.py` SoT still at D-316. Independent `kicad-cli` DRC `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` (`clearance` 0) — matches the D-316 gate. D-269/D-264/DRU board-swap trivially byte-identical (current board IS committed D-316 → no regression possible; `d269` FAIL(2)/`d264` 2-failed/`dru` FAIL(2) are the known synthetic/intrinsic flakes characterized at D-316).
- **No rule/logic change; no owner decision.** Full analysis: [`audits/2026-08-31-p2-019-d317-xgpio2-single-west-corridor-capacity-wall-post-d316-characterized-no-promote.md`](audits/2026-08-31-p2-019-d317-xgpio2-single-west-corridor-capacity-wall-post-d316-characterized-no-promote.md).
- **Opportunity & Simplification:** the west F.Cu corridor is now **saturated for single hauls** — the remaining west members `XGPIO2/4/5/6/7` all contend for the one spent corridor as *second* hauls (do NOT keep retrying them). The In2/In3 inner **signal** layers remain fully available; an **inner-layer west-XGPIO haul** is the now concretely-justified deferred **framework** task. Near-term: route the next clean increment in an **open region** (144/164 rest nets unrouted, many outside the west band).
- **NEXT FBV2-P2-020:** route the next clean rest-of-board increment **outside** the saturated west XGPIO F.Cu corridor (single net or small coherent group) at its netclass Default under the D-286 gate, add `incremental_probe_018.py`+`G30` on promote; do NOT retry single west XGPIO F.Cu hauls, the XGPIO2+XGPIO3 PAIR, or `U11_PROG`/`PWR_SENSE`; hold the inner-layer west-XGPIO haul as the deferred framework task. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: none needed (no authoritative change; HEAD advances by documentation only).

## 2026-08-31 - FBV2-P2-018: D-316 — Twelfth rest-of-board incremental increment routed and PROMOTED (a SINGLE west XGPIO net `XGPIO3` at the 0.200 mm Default clearance) — the D-315 positive lead realised: one west haul keeps the D-269 0.300 mm floor to BAT_PROTECTED_P by geometry; a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision), ZERO router-logic change

**THE TWELFTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** A SINGLE west community-header GPIO net, `XGPIO3` (R54.1 F.Cu → U3.7 B.Cu), is routed at the **0.200 mm Default clearance** (NOT the 0.300 mm blanket the D-313/D-314 XGPIO pilot PAIRS used) and promoted — the fifth XGPIO0..9 bank member. D-315 characterised the `XGPIO2`+`XGPIO3` adjacent PAIR as a corridor-capacity wall (both orders NO_FAR_RUN — the corridor admits ONE 116 mm haul, not two) and produced the positive lead this increment realises. Starting HEAD `9f108bb` (D-315; pushed; `origin/master` identical).

- **0.200 mm is the correct floor, not rule weakening.** D-269's 0.300 mm governs clearance to `BAT_PROTECTED_P`; a single west haul clears BPP by ≥0.47 mm, so D-269 is satisfied **by geometry** (measured haul→BPP **0.4739 mm ≥ 0.300**). The real full-board **D-269-aware KiCad DRC** (D-286 gate) is the arbiter and reports no new/worse class. Contrast the D-313 EAST pilot whose 0.200 mm haul pinched BPP and genuinely needed the 0.300 mm floor — the blanket was over-conservative for west members, exactly as the D-315 Opportunity Scan flagged.
- **WIP recovery (gitignored scratch only, ZERO routing-logic change).** The preserved `w/screen_018.py` re-screen had stalled before persisting evidence because it did `from xgpio23_pair200_017 import haul_bpp_min, BPP`, and `w/xgpio23_pair200_017.py` runs its full XGPIO2+XGPIO3 **PAIR** routing driver **at module level** — the import re-routed the entire D-315-characterised wall every load (a cross-module recurrence of the D-314 module-level-driver bug). Fix = drop the import, inline the self-contained `haul_bpp_min`+`BPP`, restrict the screen to the single preferred `/XGPIO3`. One managed foreground process then completed and persisted the evidence.
- **Live re-screen (`w/screen_018.py`, one foreground process):** `/XGPIO3` @ 0.200 mm OK — via (55.300,77.700), exv copper 0.7038 mm (≥0.200), exv hole 1.0038 mm (≥0.25 D-257), **haul→BPP 0.4739 mm (≥0.300 D-269)**, 0.200 mm tracks + 0.60/0.30 through via legal, 118.261 mm haul. Reproduces the D-315 record exactly; authoritative sha unchanged during the screen.
- **Route→gate→promote (real full-board):** `route XGPIO3` ALL OK (cross-layer F/B via@(55.300,77.700), refilled exactly In1/In4 for the 1 anti-pad); `gate` PASS every check (23 new in-scope items, XGPIO3 open_edges 1→0, ratsnest 677→676 −1, no new DRC, only In1/In4 re-poured, 0 regressed); `promote` re-ran gate PASS, AUTH sha undrifted, merged 1 REST_INC.
- **Promoted:** `sha256 95bc07be…` → **`d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d`**; tracks 669→**691** (+22); vias 66→**67** (+1); 6 layers / 41 zones; ratsnest 677→**676** (−1); journal 104→**105** (+1 REST_INC). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests:** new **G29**; G18–G28 auto-generalise → `router_regression.py` ALL PASS (G1–G29), deterministic (run twice, identical: via centre 1.304 mm, BPP 0.4739 mm); new `incremental_probe_017.py` PASS; `_006..016` + `phaseB_bringup_probe_005` (691/67/105; **20 routed rest nets, 144 unrouted**) PASS; `live_fingerprint.py` bumped once. **Independent kicad-cli DRC** matches the gate (`clearance` 0). **D-269/D-264/DRU board-swap A/B** (committed D-314 vs promoted D-316): `dru` FAIL(2) and `d264` FAIL B/C identical on both; `d269` flipped PASS/FAIL — but it flips FAIL/FAIL/PASS/FAIL across repeated runs on the **byte-identical D-314 parent** too, so the flip is the probe's synthetic-injection + full-zone re-pour flake, not a regression (XGPIO3 is ~45 mm from the BAT-divider TAPs it examines).
- **Opportunity & Simplification:** route the remaining west XGPIO members **one net at a time** at the 0.200 mm Default (the D-315 wall was the two-parallel-haul contention — do NOT force adjacent PAIRS for the congested northern west pins); the 0.300 mm blanket is reserved for paths that approach BPP; the stall was a *cross-module* recurrence of the module-level-driver hazard (guard heavy drivers behind `__main__` or inline small helpers); In2/In3 remain fully available. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 95bc07be…` (committed D-314, parent `9f108bb`). Next: **FBV2-P2-019 — the next single west XGPIO member, or the next clean local group.** Full analysis: [`audits/2026-08-31-p2-018-d316-twelfth-rest-of-board-incremental-increment-single-west-xgpio3-promoted.md`](audits/2026-08-31-p2-018-d316-twelfth-rest-of-board-incremental-increment-single-west-xgpio3-promoted.md).

## 2026-08-31 - FBV2-P2-017: D-315 — XGPIO2+XGPIO3 south-west adjacent pair is a MEASURED CORRIDOR-CAPACITY WALL at the D-269 clearance — NOT PROMOTED; a governed CTO characterization with ZERO authoritative copper change (board byte-identical to committed D-314), autonomy CONTINUES, no owner decision

**NO COPPER CHANGE — CLEAN CHARACTERIZATION BOUNDARY.** D-314 predicted the "XGPIO-lower-first self-separates" recipe would carry the next south-west pair `XGPIO2`+`XGPIO3` (U3.6/U3.7); the task correctly required revalidating that hypothesis on the live D-314 board. Revalidated → **disproved for this pair.** The authoritative PCB is untouched (`sha256 95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605`, 669 trk / 66 via / ratsnest 677 / journal 104). Starting HEAD `8de847b` (D-314; pushed; `origin/master` identical).

- **Both route orders FAIL at the D-269 0.300 mm floor** (`w/screen_016_one.py`, one managed foreground process each, persisted): XGPIO2 U3.6 **NO LEGAL ESCAPE** (flanked middle pin boxed by U3.7/U3.4 + 8 via obstacles incl. the accepted XGPIO0/XGPIO1 barrels); XGPIO3 far-run R54.1→via blocked. Order-independent (`qb.escape` tries all 8 directions).
- **Per-clearance isolation** (`w/xgpio23_clr_017.py`, each net alone): at **0.200 mm** each routes (XGPIO2 via (55.300,78.150); XGPIO3 via (55.300,77.700)); at **0.300 mm** XGPIO2 fails escape (pad-limited), XGPIO3 fails NO_FAR_RUN (track-limited). The 0.300 mm blanket over-constrains the whole 116 mm haul to clear 0.300 mm from ALL copper.
- **The single bounded evidence-backed alternative — per-region clr split** (`clr_pad=0.200`/`clr_trk=0.300`, correct-per-region since every BAT_PROTECTED_P pad is B.Cu ≥9 mm away and the only BPP copper near the F.Cu haul is its F.Cu trunk; NOT rule weakening) fixes the escape but both nets still **FAIL NO_FAR_RUN** — the D-313+D-314-congested corridor admits ONE 0.300 mm-clearance haul, not two. Alternative spent.
- **Pair vs single:** PAIR @ 0.200 mm also fails (2nd net NO_FAR_RUN — two parallel hauls contend for one corridor). But a **SINGLE** west XGPIO net at 0.200 mm routes CLEAN and keeps D-269 with margin: **XGPIO2 haul→BPP 0.6859 mm, XGPIO3 0.4739 mm (both ≥0.300)** — the clean next path.
- **Integrity (board pristine):** `sha256 95bc07be…` before/after (no `route`/`gate`/`promote` on the authoritative project; only gitignored `w/…` scratch; no orphan). `router_regression.py` ALL PASS G1–G28 twice (deterministic); `incremental_probe_006..016` + `phaseB_bringup_probe_005` all PASS; real DRC unchanged (`clearance` 0). D-269/D-264/DRU board-swap trivially byte-identical (current board IS committed D-314 → no regression possible).
- **No rule/logic change; no owner decision.** Full analysis: [`audits/2026-08-31-p2-017-d315-xgpio2-3-southwest-pair-corridor-capacity-wall-characterized-no-promote.md`](audits/2026-08-31-p2-017-d315-xgpio2-3-southwest-pair-corridor-capacity-wall-characterized-no-promote.md).
- **NEXT FBV2-P2-018 (sharply defined):** route a SINGLE west XGPIO net (recommended `XGPIO3`, or `XGPIO2`) at `clr_pad=clr_trk=0.200` (NOT the 0.300 mm blanket), `route`→`gate`→`promote` under the D-286 real full-board gate (D-269-aware DRC arbitrates BPP), add `incremental_probe_017.py`+`G29`; do NOT re-attempt the XGPIO2+XGPIO3 PAIR or `U11_PROG`/`PWR_SENSE`; 145/164 rest nets unrouted.

## 2026-08-30 - FBV2-P2-016: D-314 — Eleventh rest-of-board incremental increment routed and PROMOTED (XGPIO west-edge SOUTH pilot `XGPIO1`+`XGPIO0`) — the FIRST west XGPIO bank members, promoted after a governed recovery of the west-pair corridor screen, at the D-269 0.300 mm corridor clearance: a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision)

**THE ELEVENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** The XGPIO west-edge SOUTH pilot `XGPIO1` (R52.1 F.Cu → U3.5 B.Cu) + `XGPIO0` (R51.1 F.Cu → U3.4 B.Cu) — the two SOUTHERNMOST west community-header GPIO nets on consecutive PCAL9535A U3 pins, the FIRST members of the eight-net **west** XGPIO group the D-313 study had deferred as an ordering-sensitive hazard — are routed and promoted. Starting HEAD `0faf85b` (D-313; pushed; `origin/master` identical).

- **Recovery of the west-pair screen (gitignored scratch only, ZERO routing-logic change).** The one-order runner `w/screen_016_one.py` imported `w/screen_016.py`, whose full 14-pair driver ran **at module level** — every import re-ran the whole screen and died before the single pair's ledger write (empty ledger, byte-identical SCR16_* dirs, no durable evidence). Fix = guard the ranker's driver behind `if __name__ == '__main__':` so importing it only exposes the routing functions; the runner then re-measures exactly one `(a,b,order)` and persists it.
- **Measured evidence (live D-313 board, D-269 0.300 mm, no via_offset; only missing/high-value southern orders re-run, one foreground process at a time).** Both priority pairs are **conclusive** — each has exactly ONE clean order = **XGPIO1-first**: XGPIO0/1 `1_0_0` CLEAN (via-via **2.129 mm**, BPP 2.038, exv 3.607); XGPIO1/2 `1_2_1` CLEAN (via-via 2.044, BPP 2.006); the reverse orders B-FAIL (the southern net routed first boxes XGPIO1 out). XGPIO1 routes first (via lands in the pocket at (55.40,79.00)); the southern net sees that laid via as an obstacle and escapes WEST off it. XGPIO2/3 fallback not needed.
- **Selection: `XGPIO0`+`XGPIO1`, XGPIO1-first** — the minimum coherent clean west pair (best margins; southernmost/most-independent, furthest from the crowded northern pocket the D-313 study flagged for XGPIO6/7).
- **Route→gate→promote (real full-board):** `route XGPIO_PILOT_W` ALL OK (XGPIO1 via@(55.400,79.000), XGPIO0 via@(52.750,78.350) — XGPIO0 self-separated west); `gate` PASS every check (ratsnest 679→677 −2, no new DRC, only In1/In4 re-poured, 0 prior pairs regressed); `promote` re-ran gate PASS, merged 2 REST_INC.
- **Promoted:** `sha256 a0d6fead…` → **`95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605`**; tracks 631→**669** (+38); vias 64→**66** (+2); 6 layers / 41 zones; ratsnest 679→**677** (−2); journal 102→**104**; PCB diff 404 ins / 36 del (40 seg/via added, 0 seg/via/fp del; all xy dels In1/In4 re-pour). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests:** new **G28**; G18–G27 auto-generalise → `router_regression.py` ALL PASS (G1–G28), deterministic (run twice); new `incremental_probe_016.py` PASS; `_006..015` + `phaseB_bringup_probe_005` (669/66/104; 19 routed rest nets, 145 unrouted) PASS; `live_fingerprint.py` bumped once. `d269`/`dru` board-swap A/B BYTE-IDENTICAL on committed D-313 vs promoted D-314; `d264` differed on a borderline U18 item far from the XGPIO copper — **proven intrinsic non-determinism** (re-run on the *identical* D-314 board flipped 2→1→3 fails), not a regression; the authoritative kicad-cli DRC is byte-stable and clean.
- **Opportunity & Simplification:** the SOUTH of the west group is open with the same zero-mechanism recipe (route at the D-269 floor, XGPIO-lower-first so the southern neighbour self-separates west); the characterised crowding is specifically the NORTHERN pins. In2/In3 remain fully available. Recovery-runner hardening (`__main__` guard + durable ledger) is a reusable lever. Non-blocking notice. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 a0d6fead…` (D-313; parent `0faf85b`). Next: **FBV2-P2-017 — the next XGPIO south-west pilot (XGPIO2/3), or the next clean local group.** Full analysis: [`audits/2026-08-30-p2-016-d314-eleventh-rest-of-board-incremental-increment-xgpio-west-south-pilot-promoted.md`](audits/2026-08-30-p2-016-d314-eleventh-rest-of-board-incremental-increment-xgpio-west-south-pilot-promoted.md).

## 2026-08-30 - FBV2-P2-015: D-313 — Tenth rest-of-board incremental increment routed and PROMOTED (XGPIO east-edge pilot `XGPIO8`+`XGPIO9`) — the FIRST XGPIO0..9 bank members, promoted after a full evidence-first READ-ONLY corridor study, at the D-269 0.300 mm corridor clearance: a governed CTO ACCEPT + PROMOTE (no Phase-A / prior-increment casualty, no new DRC, autonomy CONTINUES, no owner decision)

**THE TENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** The XGPIO east-edge pilot `XGPIO8` (R59.1 F.Cu → U3.13 B.Cu) + `XGPIO9` (R60.1 F.Cu → U3.14 B.Cu) — two adjacent community-header GPIO nets on consecutive PCAL9535A U3 pins, the FIRST members of the ten-net XGPIO0..9 bank — are routed and promoted after an evidence-first read-only corridor study. Starting HEAD `1eb80a9` (D-312; pushed; `origin/master` identical).

- **Evidence-first study (`w/xgpio_study_015.py`, READ-ONLY).** Each `/XGPIOx` is a 2-pad cross-layer net: 100 R series R5x.1 (F.Cu top pack) → U3 pin (B.Cu mid-board), one MST edge + one F↔B via. Study of all ten: **all escape U3 cleanly** (escape goes NORTH into open board, away from the completed U2 via cluster; every default via site ≥3.1 mm clear, zero existing vias in any XGPIO bbox → **no via_offset needed**); **shared-corridor/ordering risk is real** — the 8 west nets crowd one via pocket north of U3 (XGPIO6/7 pick the identical site) while the **east pair separates cleanly (2.7 mm)**; corridor crosses no mechanical/RF/USB reservation.
- **The real wall + correct fix.** At the default 0.200 mm, candidates routed geometrically but FAILED the real gate with new `clearance` — all against `BAT_PROTECTED_P` under the **D-269 BAT_MAIN 0.300 mm** rule: the 52.4 mm protected-battery F.Cu trunk sweeps across the y≈73–82 XGPIO via band. Fix = route at the **0.300 mm D-269 floor** (the correct clearance, NOT a new mechanism; only the group `clr` parameter — no router-logic change). All six screened candidates (4–9) then pass individually.
- **Route→gate→promote (member-by-member then combined):** each member gated PASS individually; `route XGPIO_PILOT` ALL OK (XGPIO8 via@(58.60,72.95), XGPIO9 via@(58.45,75.65) — XGPIO9 re-routed around XGPIO8's laid via); `gate` PASS every check (ratsnest 681→679 −2, no new DRC, only In1/In4 re-poured, 0 prior pairs regressed); `promote` re-ran gate PASS, merged 2 REST_INC.
- **Promoted:** `sha256 d6e0148a…` → **`a0d6fead125295441dda0f0008c1261f5c1cec39edb2b8c7bd925b214e7207eb`**; tracks 608→**631** (+23); vias 62→**64** (+2); 6 layers / 41 zones; ratsnest 681→**679** (−2); journal 100→**102**; PCB diff 316 ins / 66 del (23 seg + 2 via added, 0 seg/via/fp del; all xy dels In1/In4 re-pour). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- **Tests:** new **G27**; G18–G26 auto-generalise → `router_regression.py` ALL PASS (G1–G27), deterministic; new `w/xgpio_study_015.py` + `incremental_probe_015.py` PASS; `_006..014` + `phaseB_bringup_probe_005` (631/64/102; 17 routed rest nets, 147 unrouted) PASS; `live_fingerprint.py` bumped once; `d269`/`d264`/`dru` board-swap A/B BYTE-IDENTICAL on committed D-312 vs promoted D-313 (not regressed).
- **Opportunity & Simplification:** staged small-adjacent-pilot routing is safer than a blind ten-via bank (the members are coupled — west nets contend for one via pocket, the whole bank shares the D-269 corridor); the east pair is the naturally-independent island. **In2/In3 remain fully available** (routed on F/B outer layers only — inner-signal capacity deliberately preserved for the denser west members). Non-blocking notice. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 d6e0148a…` (D-312; parent `1eb80a9`). Next: **FBV2-P2-016 — the next XGPIO adjacent pilot (west-edge members, staggering the north-of-U3 via pocket), or the next clean local group.** Full analysis: [`audits/2026-08-30-p2-015-d313-tenth-rest-of-board-incremental-increment-xgpio-east-pilot-promoted.md`](audits/2026-08-30-p2-015-d313-tenth-rest-of-board-incremental-increment-xgpio-east-pilot-promoted.md).

## 2026-08-30 - FBV2-P2-014: D-312 — Ninth rest-of-board incremental increment routed and PROMOTED (microSD card-detect `SD_CARD_DETECT_N`) — the LAST D-309 U2 escape sibling, separately governed, completing the U2 escape family with zero per-net tuning: a governed CTO ACCEPT + PROMOTE (no Phase-A / FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED / IR_RX_VS / TOUCH / AMP casualty, no new DRC, autonomy CONTINUES, no owner decision)

**THE NINTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** `SD_CARD_DETECT_N` (the microSD socket J2 card-detect switch line — J2.10/R113.2 on F.Cu → U2.11 on B.Cu; noncritical low-speed detect) is routed and promoted as its own increment. It is the SECOND and LAST of the two remaining U2 west-edge escape siblings the D-310 via-offset unlocked, completing the D-309-characterised U2 escape family (DISP_RST_N D-306, TOUCH_RST_N+TOUCH_INT_N D-310, AMP_SD_MODE D-311, SD_CARD_DETECT_N D-312). D-311 promoted the sibling `AMP_SD_MODE` alone and deliberately held `SD_CARD_DETECT_N` (functionally distinct — audio strap vs microSD detect; no throughput-bundling). Starting HEAD `288d7ad` (D-311; pushed; `origin/master` identical).

- **Mechanism reused byte-for-byte (D-310), zero per-net tuning.** No `incremental_router.py` or `qrouter.py` change this increment: the `SD_DETECT` GROUPS entry already carried `via_offset=2500000`. The always-on existing-via injection makes escape/via_site/connect_role respect accepted barrels; the opt-in bounded offset walks the F↔B transition ~2.5 mm off the nearest congesting via.
- **Re-screen on the LIVE D-311 board was essential** (`w/screen_014.py`): D-311 added an AMP via at ~(51.55,90.20), changing the obstacle field. Result: `SD_CARD_DETECT_N` escapes U2.11 **SOUTH** (esc@(52.95,85.10), via y≈82.55), AWAY from the northern via cluster (DISP/TOUCH/AMP at y≈87–92) — **the new AMP via does not touch it**. The 2.5 mm site @(53.00,82.55) is **3.850 mm** clear (nearest DISP_RST_N), identical to the D-310-board measurement; even the via-blind DEFAULT is 1.301 mm clear. The 2.5 mm offset stays comfortably clear → **no site adjustment needed**.
- **Route→gate→promote (real full-board):** `route SD_DETECT` ALL OK (J2.10↔R113.2 14.145 mm F.Cu + R113.2↔U2.11 80.337 mm cross-via@(53.00,82.55); 28 seg + 1 via); `gate` PASS every check (ratsnest 683→681 −2, no new DRC, only In1/In4 re-poured, 0 prior pairs regressed); `promote` re-ran gate PASS, merged 2 REST_INC.
- **Promoted:** `sha256 9bf429ce…` → **`d6e0148a43a42895236b934cb6f7084036e50535a399f42fe09b300aabc5f1b8`**; tracks 580→**608** (+28); vias 61→**62** (+1); 6 layers / 41 zones; ratsnest 683→**681** (−2); journal 98→**100**; PCB diff 308 ins / 52 del (28 seg + 1 via added, 0 seg/via/fp del; all xy dels In1/In4 re-pour). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5`; 0 `clearance`).
- **Tests:** new **G26**; G18–G25 auto-generalise → `router_regression.py` ALL PASS (G1–G26), deterministic; new `incremental_probe_014.py` PASS; `_006..013` + `phaseB_bringup_probe_005` (608/62/100; 15 routed rest nets, 149 unrouted) PASS; `live_fingerprint.py` bumped once; `d269`/`d264`/`dru` board-swap A/B BYTE-IDENTICAL on committed D-311 vs promoted D-312 (not regressed).
- **Opportunity & Simplification:** U2 escape family COMPLETE. Graduating to the XGPIO0..9 corridor study is NOT justified blindly (10 separate ~55 mm hauls through un-characterised congestion ≠ the U2 single-landing wall) — the right next step is a READ-ONLY XGPIO corridor STUDY before routing, or a clean local group first. Non-blocking notice. **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 9bf429ce…` (D-311; parent `288d7ad`). Next: **FBV2-P2-015 — the XGPIO0..9 bank corridor STUDY (READ-ONLY characterisation), or the next clean local group.** Full analysis: [`audits/2026-08-30-p2-014-d312-ninth-rest-of-board-incremental-increment-sd-card-detect-u2-escape-via-offset-promoted.md`](audits/2026-08-30-p2-014-d312-ninth-rest-of-board-incremental-increment-sd-card-detect-u2-escape-via-offset-promoted.md).

## 2026-08-30 - FBV2-P2-013: D-311 — Eighth rest-of-board incremental increment routed and PROMOTED (audio-amp SD/mode-select strap `AMP_SD_MODE`) — the hardest D-309 U2 escape sibling completed with the D-310 bounded via-site offset, zero per-net tuning: a governed CTO ACCEPT + PROMOTE (no Phase-A / FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED / IR_RX_VS / TOUCH casualty, no new DRC, autonomy CONTINUES, no owner decision)

**THE EIGHTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD.** `AMP_SD_MODE` (the MAX98357 class-D amplifier's static SD/mode-select logic strap — R15.1/U5.4 on F.Cu → U2.7 on B.Cu; **not** the class-D output) is routed and promoted. It is one of the two remaining U2 west-edge escape siblings the D-310 via-offset unlocked, and it was the **hardest D-309 wall** (the via-blind default via landed 0.100 mm from the accepted D-306 `DISP_RST_N` barrel; D-309 +7 `clearance`). Starting HEAD `67d3ff6` (D-310; pushed; `origin/master` identical).

- **Mechanism reused byte-for-byte (D-310), zero per-net tuning.** No new routing mechanics: the only `incremental_router.py` change is adding `via_offset=2500000` to the pre-existing `AMP_SD_MODE`/`SD_DETECT` GROUPS entries (+ refreshed annotations). The always-on existing-via injection (mirrors `QBoard.via()`; `qrouter.py` untouched) makes escape/via_site/connect_role respect accepted barrels; the opt-in bounded offset walks the F↔B transition ~2.5 mm off the nearest congesting via via the general "away from the nearest existing via" rule.
- **Re-screen on the LIVE D-310 board was essential** (`w/screen_013.py`): the two new D-310 TOUCH vias shifted the geometry. `AMP_SD_MODE` DEFAULT via 0.100 mm from `DISP_RST_N` (CLASH, confirms D-309 +7); **2.5 mm offset → (51.55,90.20), 1.760 mm** clear of the nearest via (now `TOUCH_RST_N`); 3.5 mm collapses onto the fresh TOUCH via (0.206 mm) — **2.5 mm is correct, not more**.
- **Each sibling tested separately on scratch first.** `route AMP_SD_MODE` ALL OK (R15.1↔U5.4 4.188 mm F.Cu + U5.4↔U2.7 58.487 mm cross-via; 19 seg + 1 via) → `gate` PASS every check (ratsnest 685→683 −2, no new DRC); `route SD_DETECT` ALL OK (80.293 mm cross-via; 27 seg + 1 via) → `gate` PASS every check. Both pass independently with the identical unchanged mechanism; being functionally distinct they were NOT bundled. **`AMP_SD_MODE` promoted as the single D-311 increment**; `SD_CARD_DETECT_N` held for FBV2-P2-014.
- **Promoted.** `sha256 856f7a8a…` → **`9bf429cec07654d4522121d2fb595204d06f5173ae629f2292c4d0cb9f68b314`**; tracks 561→**580** (+19); vias 60→**61** (+1); 6 layers / 41 zones; ratsnest 685→**683** (−2); journal 96→**98** (+2 REST_INC); PCB diff **236 ins / 48 del** (19 `(segment)` + 1 `(via)` added, 0 seg/via/fp del; all 48 dels In1/In4 `(xy …)` anti-pad lines). Real KiCad DRC identical (`solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499`; 0 `clearance`).
- **Tests.** New **G25**; G18–G24 auto-generalise → `router_regression.py` **ALL PASS (G1–G25)**. New `incremental_probe_013.py` PASS; `_006..012` + `phaseB_bringup_probe_005` (580/61/98; 14 routed, 150 unrouted) PASS; `live_fingerprint.py` bumped once. `d269`/`d264`/`dru` board-swap A/B **BYTE-IDENTICAL** on committed D-310 vs promoted D-311 (not regressed).
- **Opportunity & Simplification Scan.** Reusable mechanism, individually gated: both siblings closed with zero per-net tuning (the offset is a genuine reusable primitive), but the long hauls (58/80 mm) touch different regions and the via geometry is sensitive to earlier increments' copper (the 3.5 mm AMP site collapsed onto the fresh D-310 TOUCH via) — each U2-family net must still be screened live + gated on the full board; do NOT auto-bundle. In2/In3 spare. **Open owner decisions: NONE.**
- **Rollback** = pre-promotion `sha256 856f7a8a…` (D-310; parent `67d3ff6`). All locks preserved; frozen `beta-full-reference-v1` untouched; DEVICE_SPEC unchanged; journal authoritative (98); no orphan process.
- **Next FBV2-P2-014:** 150/164 rest nets unrouted; the immediate target is the second U2 sibling `SD_CARD_DETECT_N` (proven clean on scratch), or another clean local group. Full analysis: [`audits/2026-08-30-p2-013-d311-eighth-rest-of-board-incremental-increment-amp-sd-mode-u2-escape-via-offset-promoted.md`](audits/2026-08-30-p2-013-d311-eighth-rest-of-board-incremental-increment-amp-sd-mode-u2-escape-via-offset-promoted.md).

## 2026-08-30 - FBV2-P2-012: D-310 — Seventh rest-of-board incremental increment routed and PROMOTED (display/touch control pair `TOUCH_RST_N` + `TOUCH_INT_N`) — the D-309 U2 B.Cu ESCAPE WALL BROKEN by a bounded via-site offset + existing-via awareness: a governed CTO ACCEPT + PROMOTE (no Phase-A / FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED / IR_RX_VS casualty, no new DRC, autonomy CONTINUES, no owner decision)

**THE SEVENTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD — and it is the group D-309 characterised as a WALL.** The coherent display/touch control pair (capacitive-touch reset + interrupt, display FPC J1 → touch-controller U2) is routed and promoted, breaking the U2 B.Cu escape wall with two generic, bounded, `qrouter.py`-UNTOUCHED mechanisms. Starting HEAD `f2bcac1` (D-309; pushed; `origin/master` identical).

- **Root cause of the D-309 wall — the router was BLIND to existing vias.** `qrouter.QBoard._scan` builds obstacles from footprint pads + `PCB_TRACK` but iterates `GetTracks()` and `continue`s on `PCB_VIA` — every accepted through-via is invisible to escape/via_site/connect_role. U2.4/.7/.8/.11 stack on U2's WEST edge (x=54.14); the accepted D-306 `DISP_RST_N` via sits at (52.95,87.0), 1.19 mm west of that column, so a westward cross-layer escape lands the new via (and threads its F.Cu run) right past the barrel; only real DRC caught it (D-309 +3; measured this cycle `AMP_SD_MODE` default via 0.100 mm copper to `DISP_RST_N`).
- **The fix — two generic, bounded mechanisms in `connect_cross` (qrouter untouched).** (1) **Existing-via awareness:** every accepted `PCB_VIA` barrel/hole is injected as an obstacle onto the per-route `QBoard` instance (mirroring `QBoard.via()` item-for-item), so escape/via_site/**connect_role's track search** all respect accepted vias; add-only, per-route, generic, and it touches only the transient route QBoard so every G-contract fixture (which re-routes through `qrouter`) is unaffected. (2) **Bounded via-site offset:** a group opts in with `via_offset` and the F↔B transition is deliberately walked ~2.5 mm off the nearest congesting barrel via `_offset_via_site` (a short host-face B.Cu fan-out) — the first increment that PLANS a via site rather than accepting the router's first via-blind legal one; groups without `via_offset` are byte-identical to D-306/D-308.
- **Screen (real-geometry clearance, before any gate).** READ-ONLY `w/geom_012.py` + `w/screen_012.py` reproduced `cmd_route`'s cross-layer edge and measured DEFAULT vs bounded offset sites against REAL existing-via copper+hole (qrouter-blind): `AMP_SD_MODE` default via 0.70 mm from DISP = **0.100 mm CLASH** (confirms D-309 +7); `TOUCH_RST_N`/`SD_DETECT` default vias clear the barrel but their tracks thread the west column (D-309 +3/+2); at 2.5 mm offset all four clear comfortably (via↔via 2.6–7.8 mm). `TOUCH_INT_N` is on U2's EAST edge, already 5.9 mm clear. Per the task preference the coherent display/touch PAIR was taken (both pass); unrelated nets NOT bundled.
- **Route → gate → promote.** `route TOUCH_CTL` ALL OK (injected 58 existing-via obstacles): J1.47↔R12.1 22.217 mm F.Cu + R12.1↔U2.4 28.553 mm cross-via@(52.95,92.10); J1.46↔U2.19 54.708 mm cross-via@(61.15,88.85); 26 seg 0.200 mm + 2 through vias 0.60/0.30; In1/In4 [39,40] re-poured. *(First attempt with via-offset ALONE still failed +3 — the via-blind track router threaded the F.Cu run 0.05 mm from the DISP barrel; the existing-via injection made connect_role via-aware and the re-route was clean — the offset fixes the via, the injection fixes the tracks.)* `gate` PASS every check (D-309 535 trk+58 via SUBSET; 28 new items all target-net; only zones 39/40 re-poured, all other 39 byte-identical; both nets connected open-edges 2→0 and 1→0; 0 prior pairs regressed; ratsnest 688→685 EXACTLY −3; **no new/worse DRC class, `clearance` 0→0**; unc 499→499); `promote` re-ran gate PASS, re-verified AUTH sha undrifted, merged 3 REST_INC.
- **Promoted.** Authoritative `sha256 5c5cae79…a339f63` → **`856f7a8adf0db9b114b9f09d7469308f921bc897aaf2ddce7f1c15c40a197114`**; tracks **535→561** (+26: 21 F.Cu + 5 B.Cu fan-out); vias **58→60** (+2 offset through vias); 6 layers / 41 zones; ratsnest **688→685** (−3); journal **93→96** (+3 `REST_INC`); PCB file diff **310 ins / 40 del** — additions 26 `(segment)` + 2 `(via)` (0 seg/via/fp del, grep-confirmed); all 40 dels are In1/In4 `filled_polygon` xy (2 via anti-pads), nothing else. Real KiCad DRC error-severity identical (`solder_mask_bridge:1 + hole_clearance:5`; 0 `clearance`).
- **Tests.** New contract **G24** (both nets connected across the U2 F/B hop; copper legal 26 trk 0.200 mm F.Cu+B.Cu + 2×0.60/0.30 through vias; **the offset cleared both vias of every existing via — min TOUCH-via↔other-via 4.998 mm ≥0.80 mm**; ADD-ONLY IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54). G18–G23 auto-generalise. `router_regression.py` = **ALL CHECKS PASS (G1–G24), 102 PASS lines**, deterministic. New probe `incremental_probe_012.py` PASS; `_006..011` PASS unchanged (pre-X checks auto-generalise); `phaseB_bringup_probe_005` updated (561/60/96; 13 routed rest nets, 151 unrouted) PASS; real-board `kicad-cli` DRC + pcbnew ratsnest 685 re-run independently — no new `clearance`. `d269`/`d264`/`dru` probes NOT regressed — a board-swap A/B test proves BYTE-IDENTICAL verdicts (`diff` empty) on the committed D-309 and promoted D-310 boards (pre-existing BAT_*/LTC power-tree reds far from the mid-board TOUCH copper).
- **Opportunity & Simplification Scan.** The via-site metadata is deliberately REUSABLE without hiding corridor coupling: the existing-via injection is unconditional (fixes a latent gap for EVERY future cross-layer increment) and re-proven by the defensive `_clears_existing_vias` guard for all groups; `via_offset` is an opt-in bounded scalar biasing "away from the nearest existing via" (a general rule, not a hand-tuned U2 vector), now available to the rest of the U2 family and any future control clearing a congesting barrel. Sibling U2 groups `AMP_SD_MODE`/`SD_DETECT` were NOT bundled (task preference; annotated with clean measured 2.5 mm sites for a future increment). No BOM/recoverability/testability/firmware/UX/mechanical change forced; In2/In3 spare. **Open owner decisions: NONE.**
- **Rollback** = pre-promotion `sha256 5c5cae79…a339f63` (D-309; parent `f2bcac1`). All locked invariants preserved (the 2 vias are D-257-legal 0.60/0.30 ≥0.50 min_via, ≥0.25 hole-hole; In1/In4 GND roles — only those two planes re-poured); frozen `beta-full-reference-v1` untouched; DEVICE_SPEC unchanged; journal authoritative (96); no orphan process.
- **Next: FBV2-P2-013** — the U2 escape family is UNLOCKED: complete it (`AMP_SD_MODE` U2.7, `SD_CARD_DETECT_N` U2.11 both measured clean at 2.5 mm offset — add `via_offset` and route/gate), or another clean local group (`RESERVED_SPARE`, short single-via controls); 151 of 164 rest nets unrouted. Full analysis: [`audits/2026-08-30-p2-012-d310-seventh-rest-of-board-incremental-increment-touch-ctl-u2-escape-via-offset-promoted.md`](audits/2026-08-30-p2-012-d310-seventh-rest-of-board-incremental-increment-touch-ctl-u2-escape-via-offset-promoted.md).

---

## 2026-08-30 - FBV2-P2-011: D-309 — Sixth rest-of-board incremental increment routed and PROMOTED (IR receiver local filtered supply `IR_RX_VS_LOCAL`) — CLEANEST CLASS (NO via); display/touch U2-escape wall characterised; shared live-fingerprint helper landed: a governed CTO ACCEPT + PROMOTE (no Phase-A / FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED casualty, no new DRC, autonomy CONTINUES, no owner decision)

**A SIXTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD — the IR receiver (U6) local filtered supply, the cleanest increment class (same-layer F.Cu, NO via), chosen on gate evidence over the task-preferred display/touch group.** Starting HEAD `49528f2` (D-308; pushed; `origin/master` identical).

- **Same framework, ZERO new routing mechanics.** `incremental_router.py` (baseline/route/gate/promote) took the sixth increment through only a new `GROUPS` entry — the proven same-layer no-via class (like D-307 IMU_ADDR, but on F.Cu); `connect_cross`/`refill_planes`/`qrouter.py` untouched.
- **Candidate selection — EARNED on the real gate, not defaulted.** Four groups were routed on scratch and put through the REAL full-board gate (authoritative untouched). The task-preferred coherent **display/touch group** `TOUCH_CTL` (`TOUCH_RST_N` + `TOUCH_INT_N`) and the alternatives `AMP_SD_MODE`, `SD_DETECT` (`SD_CARD_DETECT_N`) each routed ALL OK on the scratch router but **FAILED the real gate with NEW `clearance` violations (+3 / +7 / +2)** — they are long cross-board hauls (33–68 mm) whose cross-layer via lands in the **congested U2 B.Cu escape region beside the accepted D-306 `DISP_RST_N` through-via** (U2.4/.7/.11/.19 all sit beside U2.8). This is a **characterised wall** (like `U11_PROG`/`PWR_SENSE`), deferred to FBV2-P2-012 with a deliberate U2-escape corridor plan; the failing `GROUPS` entries are annotated. The "favor display/touch IF clean" preference was honored — tried first, empirically shown NOT clean. CHOSEN: **`IR_RX_VS`** (`IR_RX_VS_LOCAL`, R21.2 series + C11.1 decoupling → U6.3 THT supply) — pristine (0 accepted copper within bbox+2 mm), local NE-corner cluster, all F.Cu, no via.
- **The gate (real full-board, D-286) = PASS every check.** `route IR_RX_VS` → ALL OK (C11.1↔R21.2 3.113 mm + R21.2↔U6.3 9.291 mm; 8 F.Cu segments 0.200 mm, no via); D-308 527 trk + 58 via multiset a SUBSET (0 casualty); 8 new items all target-net; **all 41 zones byte-identical** (no via ⇒ no plane re-pour); `IR_RX_VS_LOCAL` fully connected (open-edges 2→0); 0 prior pairs regressed; pcbnew ratsnest 690→688 EXACTLY −2; real kicad-cli DRC no new/worse class.
- **Promoted.** Authoritative `sha256 f4e95dec…8559e7ee` → **`5c5cae79465416c81f9d7b8dba5b2e3a3325bd9a0680b65103badf0e1a339f63`**; tracks **527→535** (+8); vias **58** (no via); 6 layers / 41 zones; ratsnest **690→688** (−2); journal **91→93** (+2 `REST_INC`); PCB file diff **64 ins / 0 del** (all 8 additions `(segment)` F.Cu, 0 seg/via/fp del, 0 zone change — cleanest class, tied D-307); real KiCad DRC identical (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
- **Tests.** New contract **G23** (C11.1-R21.2-U6.3 one island; 8 trk F.Cu 0.200 mm no via; ADD-ONLY RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54); G18–G22 stay green unchanged; `router_regression.py` = **ALL CHECKS PASS (G1–G23), 98 PASS lines**, deterministic. New probe `incremental_probe_011.py` PASS; `_006/_007/_008/_009/_010` + `phaseB_bringup_probe_005` refreshed (535/58/93) PASS; real-board `kicad-cli` DRC + pcbnew ratsnest 688 re-run independently — no new `clearance`. `d269`/`d264`/`dru` probes NOT regressed — a board-swap A/B test proves byte-identical verdicts on the committed D-308 and promoted D-309 boards (pre-existing BAT_*/LTC power-tree reds ~60 mm from my copper; the flaky d269 full-zone-re-pour proxy NOT mistaken for authoritative DRC).
- **Opportunity & Simplification Scan (ACTED-ON — the exact one D-308 §E pre-flagged).** Introduced **`checks/live_fingerprint.py`**, a single source-of-truth `EXPECTED` dict bumped once per promotion; all six probes refactored to import it, replacing the ~25 identical per-increment `EXPECT_*` hand-edits. A pure DRY consolidation weakening no historical contract (each probe still asserts live-board == EXPECTED and keeps its own structural checks); bounded, reversible; all six PASS. Failing candidate `GROUPS` entries kept + annotated (self-documenting negative evidence). In2/In3 remain spare. **Open owner decisions: NONE.**
- **Rollback** = pre-promotion `sha256 f4e95dec…8559e7ee` (D-308; parent `49528f2`). All locked invariants preserved; frozen `beta-full-reference-v1` untouched; DEVICE_SPEC unchanged; journal authoritative (93); no orphan process.
- **Next: FBV2-P2-012** — the U2 B.Cu escape corridor (plan a via SITE off U2's edge to clear the `DISP_RST_N` barrel, unlocking the display/touch/SD/audio-strap family), or another clean local no-via/single-via group (153 of 164 rest nets unrouted). Full analysis: [`audits/2026-08-30-p2-011-d309-sixth-rest-of-board-incremental-increment-ir-rx-vs-promoted.md`](audits/2026-08-30-p2-011-d309-sixth-rest-of-board-incremental-increment-ir-rx-vs-promoted.md).

---

## 2026-08-30 - FBV2-P2-010: D-308 — Fifth rest-of-board incremental increment routed and PROMOTED (front-panel RGB status-indicator completion `Net-(D13-RK/GK/BK)`) — THE FIRST MULTI-VIA INCREMENT: a governed CTO ACCEPT + PROMOTE (no Phase-A / FRONT_RGB / ACC / DISP / IMU casualty, no new DRC, autonomy CONTINUES, no owner decision)

**A FIFTH REST-OF-BOARD INCREMENT IS ON THE AUTHORITATIVE BOARD — the coherent completion of the D-304 front-panel RGB indicator, and the first increment to lay MULTIPLE vias.** Starting HEAD `c939f35` (D-307; pushed; `origin/master` identical).

- **Same framework, ZERO new mechanics.** `incremental_router.py` (baseline/route/gate/promote) took the fifth increment through only a new `GROUPS` entry. The FIRST multi-via increment required NO change to `connect_cross`/`refill_planes`/`qrouter.py`: the existing per-edge loop calls `connect_cross` once per cross-layer edge (three times) and `refill_planes` re-pours In1/In4 once for all vias — a multi-net group of independent single-via nets is already within the D-306-proven mechanic.
- **Group selection (measured; coherent + local + clean).** Baseline `a309f8ce…` (502/55/6, ratsnest 693, journal 88) + a new READ-ONLY screen `w/screen_010.py` ranking ALL 156 remaining unrouted multi-pad nets by pad layers (same vs cross), THT, MST edges/length, bbox span and accepted-copper congestion within bbox+2 mm. CHOSEN: **FRONT_RGB_LED** (`Net-(D13-RK)`+`Net-(D13-GK)`+`Net-(D13-BK)`) — the coherent completion of the D-304 front-panel RGB indicator on the LED-cathode side (R124.2/R125.2/R126.2 B.Cu → D13 MHPA3528 cathodes F.Cu), local (span ≤26 mm), clean (cu 6–11), low-current (R-limited 2–6 mA, non-switching); three independent single-via cross-layer nets. EXCLUDED with evidence: XGPIO0…9 bank (10 nets but ~55 mm cross-board cross-layer hauls — not local), NFC front-end (RF/matching/antenna/crystal), USB, ACC_5V boost cluster (U21 TPS61023 switching, `ACC_5V_LX` inductor node), IR emitter `IR_LED_A/K` (Q1-switched TSAL6100 drive current — switching/high-current), SPK_P/N + connectors (MAX98357A class-D outputs), XGPIO*_HDR/EXT_*/NATIVE_*_HDR (community J5/J8 header mass), BTN_A/B/UP/DOWN/LEFT/RIGHT_N (scattered SW2–SW7, MIX, span 40–66 mm), U11_PROG + PWR_SENSE (D-307 hard walls). A coherent 3-net group is preferred to a safe singleton to demonstrate throughput beyond singletons/2-net clusters WITHOUT bundling unrelated nets.
- **Route → gate → promote (one foreground run; authoritative untouched).** `route FRONT_RGB_LED` → ALL OK (3/3): D13.4↔R124.2 22.532 mm via@(51.250,96.800), D13.3↔R125.2 26.124 mm via@(50.800,98.250), D13.2↔R126.2 29.999 mm via@(56.400,103.250); 25 segments F.Cu+B.Cu 0.200 mm + 3 through vias 0.60/0.30; REFILLED In1/In4 GND zones [39,40] once for the 3 anti-pads; scratch 527/58, AUTH sha UNCHANGED. `gate FRONT_RGB_LED` = **PASS, every check** (D-307 502 trk + 55 via multiset a SUBSET — 0 missing; 28 new items all target-net; ONLY zones 39/40 fill-changed, all other 39 zones byte-identical; all three D13 nets fully connected open-edges 1→0 each; 0 prior requested pairs regressed; ratsnest 693→690 EXACTLY −3; no new/worse DRC class; unc 499→499).
- **Result — GATE PASS, COPPER PROMOTED.** Authoritative `sha256 a309f8ce…31279a50` → **`f4e95dec…8559e7ee`**; tracks **502→527** (+25 D13-cathode); vias **55→58** (+3 through vias); 6 layers / 41 zones unchanged; ratsnest **693→690** (−3); journal **88→91** (+3 `REST_INC`); PCB file diff = **352 insertions / 59 deletions** — additions are 25 `segment` + 3 `via` lines (ZERO `segment`/`via`/`footprint` deletions, grep-confirmed); all 59 deletions are `(xy…)` points inside the In1/In4 GND `filled_polygon` re-pour (the 3 via anti-pads), nothing else; real KiCad DRC **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` — 0 clearance, hole_clearance unchanged at 5, 0 violations touch the D13 copper).
- **Tests.** New contract **G22** pins the increment (all three D13 nets connected across their F/B hop; copper legal = 25 trk F.Cu+B.Cu 0.200 mm + three 0.60/0.30 through vias one per net; ADD-ONLY = IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54). G18–G21 stay green unchanged — their ADD-ONLY invariants exclude ALL `REST_INC` nets and pin `phaseA_via`==54, so they auto-generalise as total vias grow 55→58. `router_regression.py` = **ALL CHECKS PASS (G1–G22), 94 PASS lines**, run twice, deterministic. New probe `incremental_probe_010.py` ALL PASS; `incremental_probe_006/007/008/009.py` refreshed to the D-308 board (`_009` pre-IMU-copper check generalised) ALL PASS; `phaseB_bringup_probe_005.py` updated (527/58/91; accepted set + the three D13 cathode nets; 164 rest nets, **10 routed, 154 unrouted**) ALL PASS. The Phase-A DRU-synthesis probes `d269_probe`/`d264_probe`/`dru_probe` are NOT part of the maintained increment regression and NOT regressed by D-308: `dru_probe`(2)/`d264`(1) carry the SAME pre-existing reds on the pristine HEAD board; `d269_probe` C/D is a FLAKY borderline (0.275 mm) between two REMOTE Phase-A items (`LTC_GATE` via vs a `BAT_RAW` In2.Cu zone track) under KiCad's non-byte-reproducible full-zone `ZONE_FILLER` re-pour — it flips on HEAD as well as D-308 (my copper is 45 mm away); the real byte-stable authoritative board is DRC-clean.
- **Opportunity & Simplification Scan.** The first multi-via increment forced no mechanic extension (the 'extend only if genuinely forced' bar was not crossed). Observed (not acted on, to avoid weakening historical contracts): the four prior probes share an identical fingerprint-constant refresh + 'pre-X copper' generalised-preservation idiom that could fold into one shared `incremental_fingerprints.py` on the sixth increment. Larger coherent batches ARE justified going forward, but batch size stays evidence-limited (remaining clean local multi-net clusters are mostly in excluded categories). No BOM/recoverability/testability/firmware/UX/mechanical change forced; In2/In3 remain spare. **Open owner decisions: NONE.**
- **Integrity & rollback.** Rollback = pre-promotion `sha256 a309f8ce…31279a50` (D-307; parent `c939f35`). All floors ENFORCED (D-249/D-269/D-257 via ladder — the three 0.60/0.30 vias ARE Default netclass ≥ 0.50 mm min_via / 0.60 BAT_MAIN / 0.200-0.150 signal / 0.25 hole-hole / D-275-D-288 bridge / **In1-In4 GND** — only these two planes re-poured for the anti-pads, every other zone byte-identical); no DRU/rule/placement/topology/net/footprint/value/polarity/outline/stackup change; no D-290 reauth; D-297/D-299/D-301/D-302 levers + G14–G21 preserved; DEVICE_SPEC unchanged; `beta-full-reference-v1` untouched; shared journal authoritative (91); no orphan process.
- **Next FBV2-P2-011:** continue rest-of-board routing via the same framework (**154 of 164 rest nets unrouted**); same-layer, single-via and now multi-via cross-layer groups all proven. Candidates (screen with `w/screen_010.py`): `RESERVED_SPARE` (U23 B.Cu 3-pad spare), short IR-receiver/audio non-switching straps (`IR_RX_VS_LOCAL`, `AMP_SD_MODE`), other short single-via mixed-layer controls (`TOUCH_RST_N`, `TOUCH_INT_N`, `SD_CARD_DETECT_N`). Still avoid U11_PROG/PWR_SENSE (hard walls); RF/NFC/USB/crystals/community-header/rails/switching/class-D deferred; the XGPIO0…9 bank needs a long cross-board haul accepted first. The first increment needing MULTIPLE series vias on ONE net / a via array / an In2/In3 inner-signal traverse must extend `connect_cross`/`refill_planes` deliberately. Full analysis: [`audits/2026-08-30-p2-010-d308-fifth-rest-of-board-incremental-increment-front-rgb-led-promoted.md`](audits/2026-08-30-p2-010-d308-fifth-rest-of-board-incremental-increment-front-rgb-led-promoted.md).

**PROGRESS EARNED (fifth rest-of-board increment promoted; first multi-via): PCB routing ~18 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical increment, not fab-readiness).**

---

## 2026-08-30 - FBV2-P2-009: D-307 — Fourth rest-of-board incremental increment routed and PROMOTED (the BMI270 IMU I2C address-select strap `BMI270_SDO_ADDR`): a governed CTO ACCEPT + PROMOTE (no Phase-A / FRONT_RGB / ACC / DISP casualty, no new DRC, autonomy CONTINUES, no owner decision)

**A FOURTH REST-OF-BOARD NET IS ON THE AUTHORITATIVE BOARD — and the fallback was EARNED, not defaulted to.** Starting HEAD `73ea58e` (D-306; pushed; `origin/master` identical).

- **Same framework, ZERO new mechanics.** `incremental_router.py` (baseline/route/gate/promote) took the fourth increment through only new `GROUPS` entries; a same-layer B.Cu multi-terminal net routed through the existing Prim-MST + `connect_role` path, and the D-306 via/`connect_cross`/`refill_planes` machinery was reused byte-for-byte and correctly did NOT engage (no via ⇒ no plane re-pour ⇒ all 41 zones byte-identical).
- **Group selection (measured; highest-value low-risk, not merely the shortest net).** Baseline `9c0586d8…` (494/55/6, ratsnest 695, journal 86) + a refined READ-ONLY screen (`w/screen_009.py`: per-net MST/layer/THT, group bbox, accepted-copper congestion within bbox+1/+2 mm, and a footprint-local coherence dump). All candidate nets confirmed **Default netclass** directly from the board. Five candidates recorded. CHOSEN PRIMARY: **U11_PROG** (`ILIM_VSET`+`ISET`, the coherent same-chip BQ25185 charger current-program straps U11.7/.8) — the most coherent multi-net group; a clean singleton is NOT bundled with unrelated nets to hit a count, and the favored IMU/I2C family has no clean local *pair* (the only other U4 net, `BMI270_INT1_RAW`, is a ~46 mm haul to the MCU). Fallbacks: **PWR_SENSE** (`VBUS_PRESENT`+`MAX17048_ALRT_N`, west power-status), then the pristine **IMU_ADDR** (`BMI270_SDO_ADDR`). REJECTED outright: IMU_INT1 (17 mm MCU-adjacent single strap), IMU_COMBO (52 mm half-board span, needs a via). EXCLUDED per mandate: community-header/RF/NFC/USB/crystals/switching (ACC_5V boost)/GND/+3V3 rails/class-D SPK.
- **Two congested primaries EMPIRICALLY DISPROVEN (one foreground run at a time, authoritative untouched).** `route U11_PROG` → INCOMPLETE: `ILIM_VSET` clean (4.857 mm) but `ISET` R37.1→**U11.8 has NO LEGAL ESCAPE** — boxed by BQ25185 pins U11.6/U11.9 + board edge (pad-local wall, order-independent). `route PWR_SENSE` → INCOMPLETE: 2/4 edges (R104.2→TP31.1, TP11.1→U14.5) have **no legal corridor even at the 0.025 mm fine grid** — the west `BAT_PROTECTED_P` trunk. Both confirm the congestion screen; AUTH sha verified UNCHANGED after each; no rule weakened, no brute force.
- **The pristine fallback, EARNED.** `route IMU_ADDR` → ALL OK (R118.1↔R119.2 2.709 mm, R119.2↔U4.1 3.454 mm; 8 segments; 0.200 mm B.Cu, 0 via; 3-pad/2-edge MST). `gate IMU_ADDR` = **PASS, every check** (D-306 494 trk + 55 via multiset a SUBSET; 8 new items all target-net; ZERO zones fill-changed — no via; `BMI270_SDO_ADDR` open edges 2→0; 0 prior pairs regressed; ratsnest 695→693 EXACTLY −2; DRC identical).
- **Result — GATE PASS, COPPER PROMOTED.** Authoritative `sha256 9c0586d8…3f62259` → **`a309f8ce…31279a50`**; tracks **494→502** (+8); vias **55** (unchanged — no via); 6 layers / 41 zones unchanged; ratsnest **695→693** (−2); journal **86→88** (+2 `REST_INC`); PCB file diff = **64 insertions / 0 deletions** — pure ADD-ONLY (8 B.Cu `segment` lines; zero `segment`/`via`/`footprint`/`filled_polygon` deletions, grep-confirmed — the cleanest increment yet); real KiCad DRC **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
- **Tests.** New contract **G21** pins the increment (`BMI270_SDO_ADDR` connected R118.1-R119.2-U4.1 one island; copper legal = 8 trk B.Cu 0.200 mm, no via; ADD-ONLY = DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54). G18–G20 stay green unchanged (their ADD-ONLY invariants already exclude all `REST_INC` nets generically). `router_regression.py` = **ALL 92 CHECKS PASS (G1–G21)**, run twice, deterministic. New probe `incremental_probe_009.py` ALL PASS; `incremental_probe_006/007/008.py` refreshed to the D-307 board (`_008`'s pre-DISP-copper check generalised) ALL PASS; `phaseB_bringup_probe_005.py` updated (502/55/88; accepted set FRONT_RGB + ACC_3V3_CTL + DISP_RST_N + BMI270_SDO_ADDR; 164 rest nets, **7 routed, 157 unrouted**) ALL PASS.
- **Opportunity & Simplification Scan.** Zero new mechanics needed; the one-edge/one-via plane plan was NOT evolved to multi-via/inner-signal metadata because no promoted group forced it. No BOM/recoverability/testability/firmware/UX/mechanical change forced; In2/In3 remain spare. **Open owner decisions: NONE.**
- **Integrity & rollback.** Rollback = pre-promotion `sha256 9c0586d8…3f62259` (D-306; parent `73ea58e`). All floors ENFORCED (D-249/D-269/D-257 via ladder — no via laid / 0.60 BAT_MAIN / 0.200-0.150 signal / 0.25 hole-hole / D-275-D-288 bridge / **In1-In4 GND** — both planes byte-identical); no DRU/rule/placement/topology/net/footprint/value/polarity/outline/stackup change; no D-290 reauth; D-297/D-299/D-301/D-302 levers + G14–G20 preserved; DEVICE_SPEC unchanged; `beta-full-reference-v1` untouched; shared journal authoritative (88); no orphan process.
- **Next FBV2-P2-010:** continue rest-of-board routing via the same framework (**157 of 164 rest nets unrouted**). The two congested regions are now characterised hard walls (BQ25185/BPP trunk — U11.8 boxed; west `BAT_PROTECTED_P` trunk — TP31/U14.5 no corridor): do NOT re-attempt naively. Candidates: short 08_BUTTONS controls (`RESERVED_SPARE`, `BTN_B_N`), other short single-via mixed-layer controls, or 07_IR/06_AUDIO non-switching straps (screen THT/analog first). The first multi-via / via-array / In2/In3 inner-signal increment should extend `connect_cross`/`refill_planes` deliberately. Full analysis: [`audits/2026-08-30-p2-009-d307-fourth-rest-of-board-incremental-increment-imu-addr-promoted.md`](audits/2026-08-30-p2-009-d307-fourth-rest-of-board-incremental-increment-imu-addr-promoted.md).

**PROGRESS EARNED (fourth rest-of-board increment promoted): PCB routing ~18 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical increment, not fab-readiness).**

---

## 2026-08-30 - FBV2-P2-008: D-306 — Third rest-of-board incremental increment routed and PROMOTED (the DISP_RST_N display-reset control net) — AND THE FIRST TO EXERCISE A VIA / MIXED-LAYER PRIMITIVE: a governed CTO ACCEPT + PROMOTE (no Phase-A / FRONT_RGB / ACC casualty, no new DRC, autonomy CONTINUES, no owner decision)

**A THIRD REST-OF-BOARD NET IS ON THE AUTHORITATIVE BOARD — the first with a via.** Starting HEAD `c22b9fd` (D-305; pushed; `origin/master` identical).

- **Same framework, minimally extended for the first via.** `incremental_router.py` gained exactly three generic mechanics, each forced by a concrete need: a **per-edge layer decision** (`edge_plan` — same-layer B.Cu groups stay byte-identical), a **`connect_cross`** helper composing only proven `qrouter` primitives (`escape` → `via_site` → `via` → two anchored `connect_role` runs — **`qrouter.py` untouched**, so the battery driver is unaffected), and a **`refill_planes`** step. No via-ladder abstraction, no blind/buried/microvia path, no multi-via arrays — those await the increment that forces them.
- **Group selection (measured, prefer a new safe primitive).** Baseline `f0046eb7…` (483/54/6, ratsnest 697, journal 84) + `w/screen_007.py` (READ-ONLY). CHOSEN: **DISP_RST (`/DISP_RST_N`)** — one 3-pad net with pads NOT all on one layer (R16.1/J1.10 F.Cu SMD, U2.8 B.Cu SMD): MST = one SAME-LAYER edge (R16.1↔J1.10, the **first incremental F.Cu run**) + one CROSS-LAYER edge (J1.10↔U2.8, the **first incremental via / mixed-layer route**, ONE 0.60/0.30 Default through via ≥ the 0.50 mm `min_via_diameter`). Low congestion (2 Phase-A items in bbox+2 mm), NONCRITICAL low-speed reset line. REJECTED: AUDIO_SPK (isolated F.Cu+THT but SPK_P/N are class-D SWITCHING outputs the mandate excludes), U11_PROG (16 items, coupled to the safety-critical BPP path), PWR_SENSE (12 items, west fuel-gauge congestion). FALLBACK held (not needed): IMU_STRAP `BMI270_SDO_ADDR` B.Cu singleton — DISP_RST was not disproven. EXCLUDED per mandate: community-header/RF/NFC/USB/crystals/GND/+3V3 rails.
- **The first-via blocker, characterised (not brute-forced).** The through via pierces the In1/In4 GND reference planes; the stale plane fill (poured before the via existed) had no anti-pad, so the first gate saw `clearance` ×2 + `hole_clearance` ×2 at (52.95,87.0) vs the In1/In4 GND zones. Focused evidence bounded the fix: a plain refill drifts ONLY zones 39/40 (In1/In4 GND, +35 poly-pts each — a stored-vs-current `ZONE_FILLER` discrepancy independent of the via) and NO other zone. So `route` re-pours EXACTLY In1/In4 when (and only when) a via was laid; DRC returns to baseline IDENTICALLY. Plane byte-equality is NOT claimed — the promotable standard is DRC-neutral + "only In1/In4 changed", proven.
- **The gate (real full-board, D-286).** (1) NO prior copper deleted/altered (D-305 483 trk + 54 via multiset is a SUBSET); (2) every new item a target-group net; (3) **only In1/In4 GND planes re-poured, all other 39 zones identical**; (4) DISP_RST_N fully connected across the hop (open edges 2→0); (5) 0 prior requested pairs regressed; (6) ratsnest dropped by EXACTLY the requested count (697→695); (7) real kicad-cli DRC — no new/worse class, `unconnected_items` not increased.
- **Result — GATE PASS, COPPER PROMOTED.** Authoritative `sha256 f0046eb7…04c7cd41` → **`9c0586d8…e3f62259`**; tracks **483→494** (+11 DISP_RST_N); vias **54→55** (+1 F↔B through via); 6 layers / 41 zones unchanged; ratsnest **697→695** (−2); journal **84→86** (+2 `REST_INC`); board diff **470 insertions / 336 deletions** — ALL 336 deletions are In1/In4 `filled_polygon` xy (the plane re-pour); ZERO deleted `segment`/`via`/`footprint` lines (grep-confirmed); real KiCad DRC **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
- **Tests.** New contract **G20** pins the increment (DISP_RST_N connected across the F/B hop; copper legal = 11 trk spanning F.Cu+B.Cu at 0.200 mm + exactly one 0.60/0.30 through via; ADD-ONLY = RGB 20 + ACC 31 + Phase-A 432/54). **G18/G19 generalised** — their ADD-ONLY via count now pins `phaseA_via`==54 (vias NOT owned by any `REST_INC` net) instead of `all_via`==54, so the pin survives increments that add vias (no change to their RGB/ACC claims). `router_regression.py` = **ALL 89 CHECKS PASS (G1–G20)**, run twice, deterministic. New probe `incremental_probe_008.py` ALL PASS; `incremental_probe_006/007.py` refreshed to the D-306 board (`_007` generalised) ALL PASS; `phaseB_bringup_probe_005.py` updated (494/55/86; accepted set FRONT_RGB + ACC_3V3_CTL + DISP_RST_N; 164 rest nets, 6 routed, 158 unrouted) ALL PASS.
- **Opportunity & Simplification Scan.** The first via increment needed exactly the three mechanics above and nothing more; the gate already fingerprinted vias generically, so only a zone-preservation proof was added. No BOM/recoverability/testability/firmware/UX/mechanical opportunity forces a change; In2/In3 remain spare capacity. **Open owner decisions: NONE.**
- **Integrity & rollback.** Rollback = pre-promotion `sha256 f0046eb7…04c7cd41` (D-305; parent `c22b9fd`). All floors ENFORCED (D-249/D-269/D-257 via ladder — the 0.60/0.30 via IS the Default netclass geometry ≥ 0.50 mm min_via / 0.60 BAT_MAIN / 0.200-0.150 signal / 0.25 hole-hole / D-275-D-288 bridge / **In1-In4 GND** — planes stay GND, only fill re-poured); no DRU/rule/placement/topology/net/footprint/value/polarity/outline/stackup change; no D-290 reauth; D-297/D-299/D-301/D-302 levers + G14–G19 preserved; DEVICE_SPEC unchanged; `beta-full-reference-v1` untouched; shared journal authoritative (86); no orphan process.
- **Next FBV2-P2-009:** continue rest-of-board routing via the same framework (158 of 164 rest nets unrouted); both same-layer and single-via cross-layer groups now proven. Candidates: IMU_STRAP `BMI270_SDO_ADDR` (held B.Cu fallback), short 08_BUTTONS controls, or another short mixed-layer control; the first increment needing MULTIPLE vias / a via array / an In2/In3 inner-signal traverse should extend `connect_cross`/`refill_planes` deliberately. Full analysis: [`audits/2026-08-30-p2-008-d306-third-rest-of-board-incremental-increment-disp-rst-via-promoted.md`](audits/2026-08-30-p2-008-d306-third-rest-of-board-incremental-increment-disp-rst-via-promoted.md).

## 2026-08-30 - FBV2-P2-007: D-305 — Second rest-of-board incremental increment routed and PROMOTED (the ACC_3V3_CTL accelerometer-3V3 load-switch control group): a governed CTO ACCEPT + PROMOTE (no Phase-A / FRONT_RGB casualty, no new DRC, autonomy CONTINUES, no owner decision)

**A SECOND REST-OF-BOARD NET-GROUP IS ON THE AUTHORITATIVE BOARD.** Starting HEAD `6353bd7` (D-304; pushed; `origin/master` identical).

- **Same reusable lever, ZERO new mechanics.** `incremental_router.py` (commands `baseline`/`route`/`gate`/`promote`) took the second increment through only a new `GROUPS` registry entry — no change to the router, gate or promoter. The framework is now proven for multi-terminal (multi-segment MST) nets, not just 2-pad pairs.
- **Group selection (measured, not convenient).** `incremental_router.py baseline` (452/54/6, ratsnest 701, journal 80) + `w/screen_007.py` (READ-ONLY) screened candidates by MST edges / layer-THT / Phase-A congestion within each net's bounding box. CHOSEN: **ACC_3V3_CTL** — the accelerometer 3V3 load-switch (U20) local control group: `ACC_3V3_EN` (enable U3.15 → R98/U20.1/TP26, a **4-pad multi-terminal net / 3-edge MST**) + `ACC_3V3_ILIM` (current-limit set R97 → U20.4). Both Default netclass (0.200 mm width / 0.200 mm clearance, **NO via**), all B.Cu SMD, **low-congestion** (only 4 Phase-A B.Cu strands within bbox + 2 mm), NONCRITICAL low-current control — satisfies "prefer 2–6 nets" AND adds the multi-segment MST primitive FRONT_RGB never exercised (all single-edge 2-pad). REJECTED: IMU_STRAP `BMI270_SDO_ADDR` (0 nearby copper but a singleton — kept as the bounded fallback); PWR_SENSE `VBUS_PRESENT`+`MAX17048_ALRT_N` (12 nearby copper, congested west battery-mgmt); U11_PROG `ILIM_VSET`+`ISET` (16 nearby, the D-302 U11.2 wall region); AUDIO_SPK (F.Cu/THT/analog near mic keepout); DISP_RST `DISP_RST_N` (MIX-layer, needs a via). EXCLUDED per mandate: community-header mass, RF/NFC, USB, crystals, GND/+3V3 rails.
- **The gate (real full-board, D-286).** (1) NO prior copper deleted/altered — the D-304 copper-item multiset (452 trk + 54 via) is a SUBSET of the routed items; (2) every new item is a target-group net; (3) both nets fully copper-connected (`GetConnectedItems`: ACC_3V3_ILIM 1→0, ACC_3V3_EN 3→0); (4) no prior requested pair regressed; (5) pcbnew ratsnest dropped by EXACTLY the requested count (701→697); (6) real kicad-cli DRC — no new class, none increased, `unconnected_items` not increased.
- **Result — GATE PASS, COPPER PROMOTED.** Authoritative `sha256 00c93bdb…dfb72aad` → **`f0046eb7…04c7cd41`**; tracks **452→483** (+31 ACC_3V3_CTL); vias **54** (no new via); 6 layers / 41 zones unchanged; ratsnest **701→697** (−4); journal **80→84** (+4 `REST_INC`); board diff **248 insertions / 0 deletions** (ADD-ONLY at the file level); real KiCad DRC **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
- **Tests.** New contract **G19** pins the increment (2 nets connected; 0.200 mm B.Cu, no via; ADD-ONLY = FRONT_RGB 20 + Phase-A 432 + 54 via + ACC 31). **G18 generalised** — its ADD-ONLY Phase-A count now excludes ALL journal `role=REST_INC` nets (not just FRONT_RGB), so the "Phase-A == 432 trk / 54 via" pin stays true as later increments are promoted (no change to its FRONT_RGB claims). `router_regression.py` = **ALL 86 CHECKS PASS (G1–G19)**, deterministic. New focused probe `incremental_probe_007.py` ALL PASS; `incremental_probe_006.py` refreshed to the D-305 board ALL PASS; `phaseB_bringup_probe_005.py` updated (483/84; accepted-increment set FRONT_RGB + ACC_3V3_CTL; 164 rest nets, 5 routed, 159 unrouted) ALL PASS.
- **Opportunity & Simplification Scan.** The framework held with zero new mechanics; the multi-terminal net routed/gated through the existing Prim-MST path. No generic need for multilayer/via/bus/group-transaction semantics yet — deliberately NOT generalised prematurely (MIX-layer/via and F.Cu/THT left for the increment that forces them, so the via/D-257 discipline is introduced against a concrete need). No BOM/recoverability/testability/firmware/UX/mechanical opportunity forces a change; In2/In3 remain spare capacity. **Open owner decisions: NONE.**
- **Integrity & rollback.** Rollback = pre-promotion `sha256 00c93bdb…dfb72aad` (D-304; parent `6353bd7`). All floors ENFORCED (D-249/D-269/D-257/0.60 BAT_MAIN/0.200-0.150 signal/0.25 hole-hole/D-275-D-288 bridge/In1-In4 GND); no DRU/rule/placement/topology/net/footprint/value/polarity/outline/stackup change; no D-290 reauth; D-297/D-299/D-301/D-302 levers + G14–G18 preserved; DEVICE_SPEC unchanged; `beta-full-reference-v1` untouched; shared journal authoritative (84); no orphan process.
- **Next FBV2-P2-008:** continue rest-of-board routing with the next sharply-bounded group via the same framework (good low-risk B.Cu candidates: IMU_STRAP `BMI270_SDO_ADDR`, short 08_BUTTONS controls, PWR_SENSE once characterised; introduce the via/D-257 discipline deliberately at the first MIX-layer group). Full analysis: [`audits/2026-08-30-p2-007-d305-second-rest-of-board-incremental-increment-acc-3v3-ctl-promoted.md`](audits/2026-08-30-p2-007-d305-second-rest-of-board-incremental-increment-acc-3v3-ctl-promoted.md).

**PROGRESS EARNED (second rest-of-board increment promoted): PCB routing ~16 %→~17 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical increment, not fab-readiness).**

---

## 2026-08-30 - FBV2-P2-006: D-304 — First rest-of-board incremental increment routed and PROMOTED (the FRONT_RGB indicator group): a governed CTO ACCEPT + PROMOTE (no Phase-A casualty, no new DRC, autonomy CONTINUES, no owner decision)

**FIRST REST-OF-BOARD COPPER IS ON THE AUTHORITATIVE BOARD.** Starting HEAD `50149f4` (D-303; pushed; `origin/master` identical).

- **The lever — a reusable, scoped INCREMENTAL router/promoter (`incremental_router.py`).** Loads the D-302 promoted board via `qrouter.QBoard` (all existing copper is an OBSTACLE; new copper is ADDED, never `Remove()`d), routes a bounded named net-GROUP into a scratch copy `checks/w/INC_<GROUP>/` (the authoritative project is never touched during the experiment — sha256 verified unchanged after `route`), and PROMOTES only on a real full-board gate PASS. Commands: `baseline` / `route` / `gate` / `promote`.
- **Group selection (measured, not convenient).** Rest-of-board geometry measured for every non-rail/non-scope multi-pad net (`w/measure_rest_006.py`, READ-ONLY). CHOSEN: **FRONT_RGB** (`/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N|G_N|B_N`) — front-panel RGB status-LED control (U23 expander → R124/125/126), 6 pads, all B.Cu SMD, Default netclass (0.200 mm width / 0.200 mm clearance, NO via), spans 4.77/3.85/5.09 mm, tightly localised, **region carries ZERO Phase-A copper**, electrically NONCRITICAL, no rail/RF/USB/high-current/clock/crystal/switching constraint — high information at minimum risk. REJECTED: 07_IR (F.Cu/THT near edge, moderate-current emitter); 01_POWER_TREE short pairs (power-adjacent, not a coherent subsystem); 05_I2C `BMI270_SDO_ADDR` (IMU-adjacent single net). EXCLUDED per mandate: community-header mass, RF/NFC, USB, crystals, GND/+3V3 rails.
- **The gate (real full-board, D-286).** (1) NO Phase-A copper deleted/altered — the D-302 copper-item multiset (432 trk + 54 via geometry signatures) is a SUBSET of the routed items; (2) every new item is a target-group net; (3) each target net fully copper-connected (`GetConnectedItems`, 1→0 open edges); (4) no prior Phase-A requested pair regressed (71 pairs); (5) pcbnew ratsnest dropped by EXACTLY the requested count (704→701); (6) real kicad-cli DRC — no new class, none increased, `unconnected_items` not increased.
- **Result — GATE PASS, COPPER PROMOTED.** Authoritative `sha256 63a9bc54…f87d6ba9` → **`00c93bdb…dfb72aad`**; tracks **432→452** (+20 FRONT_RGB); vias **54** (no new via); 6 layers / 41 zones unchanged; ratsnest **704→701** (−3); journal **77→80** (+3 `REST_INC`); real KiCad DRC **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
- **Tests.** New contract **G18** pins the increment (3 nets connected; 0.200 mm B.Cu, no via; ADD-ONLY = 432 other trk / 54 via / 20 rgb trk); `router_regression.py` = **ALL 82 CHECKS PASS (G1–G18)**, deterministic. New focused probe `incremental_probe_006.py` ALL PASS; `phaseB_bringup_probe_005.py` updated to the promoted state (452/80, 3 routed rest nets, 161 unrouted) ALL PASS.
- **Opportunity & Simplification Scan.** The incremental framework generalises to every future subsystem and cannot hide a cross-group casualty; it supersedes the stale one-shot `replay_battery_block.py`. No BOM/recoverability/testability/firmware/UX/mechanical opportunity forces a change. **Open owner decisions: NONE.**
- **Integrity & rollback.** Rollback = pre-promotion `sha256 63a9bc54…f87d6ba9` (D-302; parent `50149f4`). All floors ENFORCED (D-249/D-269/D-257/0.60 BAT_MAIN/0.200-0.150 signal/0.25 hole-hole/D-275-D-288 bridge/In1-In4 GND); no DRU/rule/placement/topology/footprint/outline/stackup change; no D-290 reauth; D-297/D-299/D-301/D-302 levers + G14–G17 preserved; DEVICE_SPEC unchanged; `beta-full-reference-v1` untouched; shared journal authoritative (80); no orphan process.
- **Next FBV2-P2-007:** continue rest-of-board routing with the next sharply-bounded group via the same framework. Full analysis: [`audits/2026-08-30-p2-006-d304-first-rest-of-board-incremental-increment-front-rgb-promoted.md`](audits/2026-08-30-p2-006-d304-first-rest-of-board-incremental-increment-front-rgb-promoted.md).

**PROGRESS EARNED (first rest-of-board copper promoted): PCB routing ~15 %→~16 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical increment, not fab-readiness).**

---

## 2026-08-30 - FBV2-P2-005: D-303 — Phase-B bring-up on the promoted board: a governed CTO CHARACTERIZATION + INTEGRITY + SCOPING milestone (no copper change, board byte-identical, autonomy CONTINUES, no owner decision)

**PHASE-B DEFINED, INTEGRITY RE-VERIFIED, STALE REPLAY MACHINERY CHARACTERIZED, REAL REMAINING PHASE-B SCOPED.** Starting HEAD `01a38a5` (D-302; pushed; `origin/master` identical).

- **Exact Phase-B definition (from the code).** "Phase B" in this repo is the battery-block REPLAY / IDEMPOTENCE verification of the D-271 discipline, NOT rest-of-board routing: `replay_battery_block.py` (verbatim scratch→authoritative promotion), `route_battery_block.py` SECTION 17 `AQROOT_REPLAY` (independent journal reproduction, frozen order / pinned widths / `passes=2`, on a clean scratch), `phaseB_compare.py` (the A-vs-B gate). The driver is scoped to the power tree ONLY.
- **Integrity baseline re-verified.** `HEAD == origin/master == 01a38a5`, clean; authoritative PCB `sha256 63a9bc54…f87d6ba9` / size 1475931; **432 tracks / 54 vias / 6 layers / 41 zones / 324 footprints**; journal **77 entries**; **all 432 routed tracks are in-scope power-tree nets (0 out-of-scope) → Phase-A battery-block copper ONLY**; `router_regression.py` = ALL 79 CHECKS PASS (G1–G17); shared journal not mutated.
- **The existing Phase-B drivers assume a copper-EMPTY base (proven, faithful evidence).** (i) `replay_battery_block.py:40-42` refuses a non-empty authoritative board (`raise SystemExit`) → post-promotion (432 tracks) it can never run again; its promotion role is already fulfilled byte-identically by D-302. (ii) SECTION-17 replay (`:2297`) SKIPS every `role=='TRUNK+ESCAPE'` entry — exactly the ONE entry that defines the promotion (`BAT_PROTECTED_P U11.2→C36.1, w=1.5, reinforcement=True`); a replay carries 76/77 items, dropping the wall closure, and would NOT reproduce the board. (iii) `phaseB_compare.py` needs a `phaseB.json` that was never produced. The replay machinery predates the D-297/D-299/D-301/D-302 levers and is stale.
- **The promotion is sound regardless.** The board is byte-identical to a scratch from a GENUINE full-authority Phase-A gate (`run_003t_full.sh 004b2`, `DRIVER_EXIT=0`, PHASE A COMPLETE) — real driver, real order, not a proxy (D-286) — DRC zero new copper classes, regression ALL PASS. So the D-271 reproduction proof is a modest-value nicety with stale machinery; re-running it as-is is not justified.
- **Real remaining Phase-B, scoped (next bounded lever).** Rest-of-board = **164 multi-pad nets, 0 routed**, across 9 subsystem sheets + rails (GND 259 pads, +3V3 86 pads; 09_COMMUNITY_HEADER 20 nets, 04_SPI_B_RADIOS_NFC 20, 01_POWER_TREE-beyond-block 18, top 17, 08_BUTTONS_EXPANDERS 10, …). ~85 % of remaining routing, NO driver (route_battery_block is power-tree only). Next lever: a new scoped INCREMENTAL driver that loads the promoted board, PRESERVES the Phase-A copper (never erase/reroute), routes a bounded isolated net-group first, gated by real full-board DRC (D-286), promoted only on a genuine no-casualty / no-new-DRC increment; generalize/retire the one-shot `replay_battery_block.py`.
- **Opportunity & Simplification Scan (mandated):** rest-of-board routing is core CTO-authority engineering, not an owner decision; decompose by sheet/net-group for small independently-promotable increments; retire the stale one-shot replay path. **Open owner decisions: NONE.**
- **Integrity.** No copper/placement/rule/floor/DRU/topology/footprint/outline change; authoritative PCB byte-identical; journal at HEAD; all floors + D-249/D-257/D-269/D-275/D-288/D-290 and the accepted D-297/D-299/D-301/D-302 levers (G14–G17) preserved; frozen `beta-full-reference-v1` untouched. Added: `checks/phaseB_bringup_probe_005.py` (READ-ONLY, reproducible; ALL PASS) → `checks/phaseB_bringup_005.json`. DEVICE_SPEC unchanged.
- **Next: FBV2-P2-006** — begin rest-of-board routing (build the incremental driver, route the first isolated net-group, real full-board DRC gate, no Phase-A casualty). Audit: [`audits/2026-08-30-p2-005-d303-phaseB-bringup-characterization-integrity-scope.md`](audits/2026-08-30-p2-005-d303-phaseB-bringup-characterization-integrity-scope.md).
- **NO PROGRESS EARNED (no copper routed): PCB routing ~15 %, overall ~76 %, readiness ~77 %.**

---

## 2026-08-30 - FBV2-P2-004B2: D-302 — the FIRST AUTHORITATIVE PHASE-A COPPER PROMOTION (verified `U11_RETARGET`→`C36.1` full-run board becomes the authoritative PCB: 432 tracks / 54 vias / 6 layers / direction-2 placement / ratsnest 704 / 77-entry journal / regenerated D-249…D-269 DRU) + the router-regression fixture-compatibility fix (primitives → copper-clean scratch fixture, new G17) so G1–G17 all PASS on the routed board; PHASE A COPPER ONLY — NOT ALL ROUTING COMPLETE; D-275 and D-277..D-301 preserved

**A COMMITTED PROMOTION + ROUTINE HARNESS FIX — AUTONOMY CONTINUES (no owner decision raised).** Starting HEAD `56d0ebe` (D-301; pushed) with the verified promotion staged in the working tree: the authoritative PCB byte-identical to the `checks/w/FULL003T_004b2_u11retarget` scratch, the regenerated DRU it requires, the 77-entry `phaseA_journal.json`, plus the already-committed `AQROOT_U11_RETARGET` lever / **G16** / `u11_retarget_probe_004b.py`.

**WHAT IS PROMOTED.** With `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 AQROOT_U11_RETARGET=1` the full run (`run_004b2_full.log`, `DRIVER_EXIT=0`, **PHASE A COMPLETE**) closes the D-301 terminal wall: `u11_escape()` retargets the `BAT_PROTECTED_P` trunk far endpoint from the impossible ~55 mm cross-board `D9.1` run to a SHORT wide tap into the nearest already-on-net ≥1.20 mm BPP node copper `C36.1` (63.750,74.325) — B.Cu **7.905 mm** at 1.50 mm min trunk width, journal-tagged `[current-path reinforcement]` (the 004B2 no-casualty refinement keeps the U11.2 0.20 mm SENSE tie, so the tap is judged by `reserve_gate(allow_dangle=False)` with the ratsnest EXACTLY unchanged, not a new `gate()` connection). Routed **74** / skipped-already-connected **101** / **ratsnest 704 (−77)**.

**THE PROMOTED ARTIFACT (integrity).** Authoritative PCB `sha256 63a9bc54…f87d6ba9` is **byte-identical** to the verified scratch; **432 tracks, 54 vias, 6 copper layers, direction-2 placement** (placement fingerprint `397dffe1f77e4d10` == artifact), 41 zones, 77-entry journal (incl. the `U11.2→C36.1` `reinforcement:True` entry). Real KiCad DRC on the authoritative board = **`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, unconnected_items:499}`** — **ZERO new copper DRC classes**, and the D-301 scratch's `track_width:1` is GONE (the regenerated D-249 trunk-width rule + real routed geometry resolve it). `u11_retarget_probe_004b.py` and the exact judge PASS on the real board.

**THE DRU IS THE ACCEPTED RULE SET, NOT A RELAXATION.** The regenerated DRU (67→119 rules, byte-identical to the scratch) ADDS the per-net escape/tap/stub/trunk/clearance rules the routed copper needs — D-249 (11 refs), D-257 (39: fine-pitch escape via/hole/annular), D-258/D-263/D-266 (escape/reservation vias), D-264 (BAT_MAIN outer-layer In2/In3 split), D-269 (current-path routed clearance) — and renames three generic rules to their specific accepted forms. **The old HEAD DRU is STALE and cannot accompany the routed board**: without these per-net rules the accepted routed escapes/taps/vias/stubs would be measured against the generic netclass rules and DRC would spuriously flag legal copper. NO floor is relaxed (D-249 ≥1.20 mm, D-269 0.300 mm, D-257 via ladder, 0.60 mm BAT_MAIN intact).

**THE HARNESS FIX (routine engineering, NOT an owner decision).** `router_regression.py` G3/G4/G6/G8/G9 (11 checks) failed only because `fresh()` copies the now-routed authoritative board into PRIMITIVE unit vehicles that lay a few tracks from scratch and assert exact ratsnest-fall / DRC-delta / widest-escape / requested-pad connectivity — they assume a copper-EMPTY base (temporarily restoring HEAD's 0-track board made all 11 pass with the same lever code, proving fixture coupling). Fix: a new **`scratch_clean(work,name)`** derives a fixture from the authoritative board's SAME placement / footprints / GND zones / rule areas / DRU+pro context and removes ONLY routed copper (board-level `PCB_TRACK`/`PCB_ARC`/`PCB_VIA`, stripped as balanced S-expressions on the file text so pcbnew is never mutated and the authoritative file is never touched). Every `fresh()` caller audited & classified — **CLEAN primitive fixture:** CASES G2–G6, CONFLICTS bisection, G7, G8, G9, G11, G12; **AUTHORITATIVE routed state (unchanged):** G1 (faithful copy whose DRC must EQUAL the authoritative DRC), G10 (concurrency baseline == authoritative DRC), and the real-DRC/probe/judge harnesses. Copper is hidden from NO check meant to validate the promoted board.

**CONFLICTS RE-PIN (placement, not relaxation).** The promoted direction-2 placement moves U18 (HEAD (3.0,72.4) rot 90°→authoritative (8.0,66.5) rot 180°), so `U18.8`/`U18.9` widest-legal-escape re-measures at U18's authoritative pose as **0.245 mm** (was 0.250 mm) — STILL far below their 1.20 / 0.60 mm floors, so both remain NO-LEGAL-ESCAPE (conflict PRESERVED). `U14.2/U14.3/U11.2` did not move (0.240/0.200 mm unchanged).

**NEW CONTRACT G17** — a standing guard that the fix is a fixture change, not a test weakening: the authoritative board MAY carry promoted copper (432/54); the clean fixture has ZERO tracks/arcs/vias; the authoritative file is byte-for-byte unchanged (sha256+size+mtime) after fixture building; placement/layers(6)/footprints(324)/zones(41)/DRU preserved in the fixture; and the authoritative DRC/connectivity is measured on the ROUTED board (auth ratsnest 704 < clean-fixture ratsnest 781). **`router_regression.py` = ALL 79 CHECKS PASS (G1–G17), run twice, deterministic.**

**INTEGRITY & ROLLBACK.** Pre-promotion authoritative PCB `sha256 2235e273…d642d7e` (HEAD `56d0ebe`, 0 tracks) remains the parent of this commit and is tagged for rollback (`beta-v2-p2-battery-pre-authoritative`, `beta-v2-p2-pre-sixlayer-authoritative`); D-290 untouched; the accepted `AQROOT_U18BPP_JOIN` (D-297), `AQROOT_U19CAP` (D-299/G14), `AQROOT_LTCGATE_KO` (D-301/G15), `AQROOT_U11_RETARGET` (D-302/G16), `place_003l` (D-285), the D-275/D-288 bridge, D-275 and D-277..D-301 preserved; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` NOT edited.

**NOT ALL ROUTING COMPLETE / NEXT.** This promotes **Phase-A battery-block copper ONLY** — ratsnest 704 / unconnected_items 499 remain (Phase B and the rest of the board unrouted). Next: **FBV2-P2-005 — Phase B bring-up on the promoted board**, screened full DRC (D-286), promote only on a genuine gate PASS. Full analysis: [`audits/2026-08-30-p2-004b2-d302-first-authoritative-phasea-copper-promotion-regression-fixture-fix.md`](audits/2026-08-30-p2-004b2-d302-first-authoritative-phasea-copper-promotion-regression-fixture-fix.md). **PROGRESS EARNED (first copper promoted): PCB routing 0 %→~15 % (Phase-A battery block), overall 74 %→~76 %, readiness ~77 % (JLCPCB file unchanged).**

---

## 2026-08-30 - FBV2-P2-004A: D-301 — the `AQROOT_LTCGATE_KO` path-shaping lever's full-authority gate CONFIRMED a GENUINE +1 (closes `LTC_GATE U18.10→Q3.4`, LOST 0, no new DRC) — so the minimum OFF-by-default lever + G15 are ACCEPTED and COMMITTED (byte-identical when unset); copper is NOT promoted because full Phase-A still FAILs at the newly-exposed `U11.2` BPP trunk wall, readiness/progress unchanged, autonomy CONTINUES, D-275 and D-277..D-300 preserved; DEVICE_SPEC.md created

**A GOVERNED CTO ACCEPT + COMMIT + OVERALL-RUN FAIL — AUTONOMY CONTINUES (a new terminal wall is not a stop reason; no owner decision is raised).** Starting HEAD `060a313` (D-300; pushed; `phaseA_journal.json` restored byte-identical at HEAD) carrying two uncommitted WIP files: the OFF-by-default `AQROOT_LTCGATE_KO` path-shaping lever in `checks/route_battery_block.py` (a `LTCGATE_KO` env-parse block + a scoped install/lift hook + a bulky ~118-line in-run probe `_ltcgate_probe`/`AQROOT_LTCGATE_PROBE`) and its **G15** contract in `checks/router_regression.py`. No router process live.

**THE LEVER (a path-shaping keep-out, NOT a re-order — D-300 refuted ordering).** `AQROOT_LTCGATE_KO` parses one or more net-foreign `QR.SEG(...,'KO')` capsules `(layer,(x0,y0,x1,y1,hw))` (`=1`/`AUTO`/`DEFAULT` → validated default; explicit `LAYER:x0,y0,x1,y1,hw;…` string in mm overrides). Guarded on the exact triple `(LTC_GATE,U18.10,Q3.4)` AND `LTCGATE_KO` non-empty, the capsules are installed immediately before the join and **lifted immediately after** (proven `AQROOT_U19CAP` mechanism — nothing else on the board sees them). Unset → `LTCGATE_KO==[]`, no keep-out installed, **byte-identical to every prior run**. The validated default seals the squeeze-gap just north of the `BAT_SENSE` 1.0 mm current-path track `(2.8,62.05)-(5.4,62.05)` on **each far run layer F/I2/I3** at `(2.6,62.5)-(5.5,62.5)`, half-width 0.4 mm, forcing the `connect_hop` far run WEST of x=2.8 so the join routes F.Cu `(5.15,64.75)→(4.0,64.75)→(1.9,62.65)→(1.9,60.7)`, **8.556 mm**, `gate()` PASS. The real cause of the wall is **D-269 alone** (clearance 0.2803 vs 0.300 mm, ~19.7 µm short; FINE_ESC legalises the D-257 via, so there is NO D-249 track_width violation in the real path — the earlier "0.20 mm D-249" was a raw-`connect_hop` probe artifact that bypassed FINE_ESC). Pinned OFF/ON + scoped by **G15**.

**THE FULL-AUTHORITY GATE RAN AND COMPLETED.** `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 bash w/run_003t_full.sh 004a_ltcgate1 w/cand_003t/t_a_r77e15n10_r79e15n10.json` (direction-2 placement, both prior accepted levers ON) → `checks/w/phaseA_003t_full_004a_ltcgate1.json` (secs **1500.2**, driver exited clean); the shared `phaseA_journal.json` was restored byte-identical to HEAD afterward and no process remains. A genuine full-authority artifact (not a proxy — D-286), judged by `python3 w/judge_004a.py`.

**VERDICT: a GENUINE +1, nothing lost.** vs the 003Y2 baseline (D-299): connections **72→73**, skipped-already-connected **101=101**, ratsnest **705/−76 → 704/−77**, journal **75→76**; the connected-set diff **GAINED 1 / LOST 0** = exactly `LTC_GATE Q3.4↔U18.10` (role SIG, layer F, 2 vias, `via_dia 0.35`, 8.556 mm) — **not a swap**. vs the 003W baseline (D-297): GAINED 3 (`LTC_GATE` + the two D-299 U19 pins `N_BATDIV R89.2↔U19.6` and `REC_BAT_LOW (node)↔U19.7`), LOST 0 — the accepted U18.8 / U19CAP gains are preserved and the LTC_GATE close is purely additive. `LTC_GATE U18.10↔Q3.4` in the connected set = True and no longer the terminal fail; final DRC histogram **identical** to 003Y2 (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}`), no new class/increase; no sub-0.50 non-fine via (run via diameters 0.35/0.60/0.65/0.80).

**RULING: ACCEPT + COMMIT.** The full gate (not a proxy) confirms a real, board-legal net gain, so `AQROOT_LTCGATE_KO` is **ACCEPTED and COMMITTED** — banked env-gated / OFF-by-default, byte-identical when unset, pinned by G15. Production WIP is **pruned to the narrow accepted lever**: the bulky in-run probe `_ltcgate_probe` (~118 lines) and its `AQROOT_LTCGATE_PROBE` hook are REMOVED (that engineering evidence lives in the audit/artifacts, not the router); net WIP reduced from +242 to +124 lines across the two tracked files.

**COPPER IS NOT PROMOTED — full Phase-A still FAILs at a NEW terminal wall.** 004A is the FIRST run in the whole arc to close every upstream wall (west/BAT_RAW, U18.8 In3-join D-297, the saturated U19 dead-cell field D-299, and now `LTC_GATE` D-301) and therefore the FIRST to reach the final `u11_escape()` step, which now FAILs: `PHASE A: FAIL -- U11.2 escape: none exists`. So readiness/progress are UNCHANGED and the authoritative board stays six layers / 0 tracks / 0 vias.

**THE NEW TERMINAL WALL, characterized sharply (no new long route).** `u11_escape()` (`route_battery_block.py:2149`) lays the **U11.2 end of the `BAT_PROTECTED_P` high-current trunk**, LAST after all 73 queue connections: escape `D9.1` at `W_TRUNK_BPP=1.50 mm`, flare `U11.2` (1.50→0.20 mm SENSE neck), `connect_role(launch→D9.1)` at 1.50/1.20 mm, `gate()`. Geometry (authoritative board): `U11.2`=(66.400,78.200) inside the EAST `BAT_PROTECTED_P` node cluster; `D9.1`=(11.350,72.500) in the WEST control-copper mass — a **~55 mm cross-board ≥1.20 mm B.Cu trunk**. The rest of the BPP backbone is already connected on the 004A board (`R75.2→(stage)` TRUNK 14.458 mm F.Cu; EARLY SOUTH BRIDGE land `C36.1` 70.925 mm; `C58.1→D9.1` TAP 5.092 mm; C36/C25/C58/D9.1 "already joined via R75.2"); `U11.2` already has its thin 0.20 mm SENSE tie (5.525 mm, a Kelvin/sense tie, not a current path). The single ≤~1.30 mm central west↔east channel is already occupied by the south bridge (ywest 82.40) and the R75.2 trunk, so a SECOND parallel cross-board 1.50 mm trunk has NO legal path — a structural **≥1.20 mm-trunk NO_LEGAL_PATH** (the D-273/274/281/282/283 class), NOT a ~20 µm DRC pinch like LTC_GATE.

**OPPORTUNITY & SIMPLIFICATION SCAN (mandated).** Path-shaping is essentially free / reversible / BOM-neutral: the accepted lever banks a proven +1 OFF-by-default with zero BOM/placement/rule impact, and pruning the probe removes complexity. The U11.2 wall is reducible: U11.2 is IN the east node (already on-net with D9.1 via the bridge/R75.2 backbone), so a SHORT wide tap into the nearest on-net ≥1.20 mm node copper is a better implementation than a cross-board trunk (the 004B lever). It is a high-current safety-relevant net, so 004B must preserve the ≥1.20 mm current path (no width waiver). The six-layer stack's bare In2/In3 remain spare capacity (the D-297 lesson). No BOM / recoverability (D-049) / testability / manufacturing / firmware / UX opportunity forces a change; no irreversible cost, no strategic fork, no opportunity loss. **Open owner decisions: NONE.**

**DEVICE_SPEC.** At this safe committed boundary the authoritative current-product spec/index **`docs/full-beta-v2/DEVICE_SPEC.md`** was created (mandatory before renders / website / Kickstarter / enclosure briefs / external-mechanical / product-description claims), grounded in the accepted schematic (9 functional sheets) / BOM / population matrix / accepted audits, with LOCKED/FITTED/DNP/TUNE/CAD-TO-VERIFY/UNRESOLVED and INTERNAL/EXTERNAL/MARKETING-SAFE labels and evidence pointers. CURRENT_STATE.md now references it.

**INTEGRITY.** Authoritative PCB byte-identical to HEAD (`sha256 2235e2736838…d642d7e`; six layers, 0 tracks, 0 vias, placement at home); no DRC absorbed (the U11.2 open is surfaced FAIL evidence on gitignored scratch, never in the authoritative board); `phaseA_journal.json` at HEAD; no via below the D-257 ladder; D-269 (0.300 mm), ≥1.20 mm BPP (D-249), 0.60 mm BAT_MAIN ENFORCED; D-290 untouched; the accepted `AQROOT_U18BPP_JOIN` (D-297), `AQROOT_U19CAP` (D-299, G14), `place_003l` (D-285), the D-275/D-288 bridge, D-275 and D-277..D-300 preserved; frozen `beta-full-reference-v1` untouched; `router_regression.py` ALL CHECKS PASS (G9–G15); gitignored 004A evidence preserved (`checks/w/phaseA_003t_full_004a_ltcgate1.json`, `w/judge_004a.py`, `w/FULL003T_004a_ltcgate1/`, `w/TEST004A_*/`, `w/run_004a_*.log`); `JLCPCB_READINESS` unchanged.

**NEXT — FBV2-P2-004B:** build ONE bounded env-gated (OFF-by-default) **U11.2 BPP trunk-endpoint retarget** lever — close the U11.2 trunk end as a SHORT ≥1.20 mm tap into the nearest already-connected BPP node copper (e.g. `C36.1` (63.75,73.75)) instead of the cross-board `u11_escape()` run to `D9.1`; keep `AQROOT_U18BPP_JOIN=I3`+`AQROOT_U19CAP=1`+`AQROOT_LTCGATE_KO=1` ON; full-authority-gate judged (connected-set diff vs `w/phaseA_003t_full_004a_ltcgate1.json`), verifying the retarget PRESERVES a valid high-current path (no width waiver, no functional regression). Fallback: a bounded immediate-neighbour placement ECO to open a ≥1.20 mm U11.2 corridor, re-screened with real full-placement DRC (D-286). Full analysis: [`audits/2026-08-30-p2-004a-d301-ltcgate-ko-path-shaping-lever-full-gate-plus1-accepted-committed-u11-trunk-wall.md`](audits/2026-08-30-p2-004a-d301-ltcgate-ko-path-shaping-lever-full-gate-plus1-accepted-committed-u11-trunk-wall.md).

---

## 2026-08-30 - FBV2-P2-003Z: D-300 — the `AQROOT_LTCGATE` defer-to-congestion lever's full-authority gate COMPLETED and it is BEHAVIOURALLY IDENTICAL to D-299 (gained 0 / lost 0, same `LTC_GATE U18.10→Q3.4` terminal wall, same D-249 track_width / D-269 clearance rejections, identical final DRC) — so a pure re-order is a NULL OPERATION on this wall: the lever and its G15 WIP are REJECTED/RETIRED and the false-positive probe is RETIRED; copper is NOT promoted, readiness/progress unchanged, autonomy CONTINUES, D-275 and D-277..D-299 preserved

**A GOVERNED CTO FAIL / LEVER REFUTATION + WIP RETIREMENT — AUTONOMY CONTINUES (a refuted bounded lever is not a stop reason; no owner decision is raised).** Starting HEAD `3ce5244` (D-299; pushed; `phaseA_journal.json` restored at HEAD) carrying three uncommitted WIP files: the OFF-by-default `AQROOT_LTCGATE` defer-to-congestion lever in `checks/route_battery_block.py` (+34/−1), its **G15** contract in `checks/router_regression.py` (+30), and the measured-record probe `checks/ltcgate_join_probe_003z.py` (untracked). No router process live.

**THE LEVER (a pure re-order).** `route_battery_block.py` removed the `LTC_GATE U18.10→Q3.4` branch from section `8b. LTC_GATE` (guarded on the flag AND the exact triple `(LTC_GATE, U18.10, Q3.4)`) and re-queued it as the LAST functional item — a new `13z` stage after the closure stage and test points — at the ordinary SIG ladder. OFF → the branch stays in 8b, byte-identical to every prior run; pinned OFF/ON + scoped by a G15 regression contract. **The theory (from the probe):** section 8b routes the join before the western margin is fully occupied, so `connect_role` takes a short central path that narrows to 0.20 mm inside the BPP 1.20 mm-trunk keep-region (D-249) and grazes a `BAT_MAIN` path at 0.2803 mm (~20 µm short of D-269); deferring the join to full congestion was supposed to force the router onto a clean west detour.

**THE GATE RAN AND COMPLETED.** `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE=1 bash w/run_003t_full.sh 003z3_ltcgate w/cand_003t/t_a_r77e15n10_r79e15n10.json` → `checks/w/phaseA_003t_full_003z3_ltcgate.json` (secs **1497.0**, driver exited clean); the shared `phaseA_journal.json` was restored **byte-identical to HEAD** afterward and no process remains; judged by `python3 w/judge_003z.py w/phaseA_003t_full_003z3_ltcgate.json`. A genuine full-authority artifact (not a proxy — D-286).

**VERDICT: IDENTICAL TO D-299 — THE LEVER DOES NOTHING.** vs the 003Y2 baseline (D-299): connections **72=72**, skipped **101=101**, ratsnest **705/−76 = 705/−76**, journal **75=75**; the connected-set diff **GAINED 0 / LOST 0**. The failing rung is byte-for-byte the same two frozen owner rules — `track_width` (rule 'BAT_PROTECTED_P high-current trunk width - D-249' min 1.2000 mm; actual 0.2000 mm) and `clearance` (rule 'BAT_MAIN routed clearance - current path role - D-269' 0.3000 mm; actual 0.2803 mm); `LTC_GATE U18.10↔Q3.4` NOT in the connected set, still the terminal fail; final DRC histogram identical (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}`); no sub-0.50 non-fine via (run via diameters 0.35/0.60/0.65/0.80). **Deferring the join to route last changed nothing** — the driver's `connect_role` greedily re-takes the identical rule-violating central path even when the branch is queued as the very last functional item. A re-order is a null operation on this wall.

**THE PROBE WAS A FALSE POSITIVE (D-286 reaffirmed).** `ltcgate_join_probe_003z.py` measured a legal **10.475 mm west detour** (B.Cu, w=0.20, 0 new DRC, ratsnest 705→704) via a post-hoc `QR.connect_role(U18.10, Q3.4)` on the **saved** D-299 full-run board — but that does NOT reproduce the driver's real in-run state (the reserved-lane keep-outs already lifted before the closure stage; a board that is not the post-hoc snapshot; the greedy path-cost model still offers and takes the shorter central rung because a re-order never physically blocks it). A post-hoc measurement on the final saved board is a **proxy the full gate overrides** — only a genuine full-authority Phase-A PASS promotes copper (D-286), and here it FAILs identically.

**RULING (D-300).** REJECT/RETIRE the `AQROOT_LTCGATE` lever and its G15 WIP via an **exact reverse patch** scoped to the two tracked files (`git diff -- route_battery_block.py router_regression.py | git apply -R`, NOT a broad destructive reset); RETIRE the false-positive probe (untracked, never committed) so **no artifact in the tree claims the lever works** — the negative finding is recorded in the audit and CTO_DECISIONS instead. Copper NOT promoted; the authoritative board stays six layers / 0 tracks / 0 vias; readiness/progress UNCHANGED (D-286). NOT an owner decision (no floor relaxed, no frozen part moved, no DRU change, no D-249/D-269 relaxation); `/home/aqroot8/.aqroot-autopilot-stop` ABSENT, autonomy CONTINUES. **Retirement proof:** post-revert `git hash-object` = `HEAD:` blob for each file (`route_battery_block.py` `ebcafae…`, `router_regression.py` `38eb3a8…`); `git grep LTCGATE|AQROOT_LTCGATE|13z|ltcgate_join_probe` over tracked Python source (excluding gitignored `checks/w/`) NO match; probe removed; `router_regression.py` ALL CHECKS PASS (G12/G13/G14 intact; G15 correctly gone).

**OPPORTUNITY & SIMPLIFICATION SCAN (mandated at this LTC_GATE / power-protection milestone).** No product-capability / BOM / recoverability (D-049) / testability / manufacturing / firmware / UX / future-option opportunity justifies changing architecture — the wall is a single internal LTC4368 gate-drive control-net join (all other `LTC_GATE` segments connected: `U18.10→R76.1` F.Cu FINE_ESC; `Q3.2→Q3.4`/`Q2.2→Q2.4`/`Q3.2→Q2.2` B.Cu), not a capability or BOM gap; no component change closes a 20 µm routing pinch; TP17 already covers testability; the six-layer stack's bare In2/In3 remain spare future capacity (the D-297 lesson). No irreversible cost / strategic fork. **Open owner decisions: NONE.** **Next best technical lever (grounded):** the probe proved a legal ~10.5 mm west detour exists; the driver just won't take it while the shorter central lane is offered — so the next lever is **path-shaping, not ordering**: an explicit local waypoint / central-lane keep-out (on the proven `AQROOT_U19CAP` KO mechanism, lifted after the join) that BLOCKS the rule-violating central lane and forces `connect_role` onto the west detour clear of the BPP trunk (D-249) and the `BAT_MAIN` path (D-269, miss ~19.7 µm). Fallback: a bounded immediate-neighbor placement ECO (~20 µm nudge) re-screened with full-placement DRC (D-286). Both preserve every floor; neither is an owner decision.

**INTEGRITY.** Authoritative PCB byte-identical to HEAD (`sha256 2235e2736838…d642d7e`; six layers, 0 tracks, 0 vias, placement at home); no DRC absorbed; `phaseA_journal.json` at HEAD; no via below the D-257 ladder; D-269 (0.300 mm), ≥1.20 mm BPP (D-249), 0.60 mm BAT_MAIN ENFORCED; D-290 untouched; the accepted `AQROOT_U18BPP_JOIN` (D-297) and `AQROOT_U19CAP` (D-299, G14), `place_003l` (D-285), the D-275/D-288 bridge, D-275 and D-277..D-299 preserved; frozen `beta-full-reference-v1` untouched; gitignored 003Z evidence preserved (`checks/w/phaseA_003t_full_003z3_ltcgate.json`, `w/judge_003z.py`, `w/FULL003T_003z*_ltcgate/`, `w/TEST003Z_*/`, `w/run_003z_ltcgate.log`); `JLCPCB_READINESS` unchanged.

**NEXT — FBV2-P2-004A:** build ONE bounded, env-gated (OFF-by-default) **path-shaping** lever for `LTC_GATE U18.10→Q3.4` (a central-lane keep-out forcing the west detour — NOT a re-order, refuted here), keep `AQROOT_U18BPP_JOIN=I3`+`AQROOT_U19CAP=1` ON, validate vs `router_regression.py` (authoritative byte-identical), full-authority-gate judged (connected-set diff vs `w/phaseA_003t_full_003y2_u19cap.json` and `w/phaseA_003t_full_003w_u18bpp_i3.json`); the placement ECO is the fallback. Full analysis: [`audits/2026-08-30-p2-003z-d300-ltcgate-defer-to-congestion-lever-refuted-false-positive-probe-retired.md`](audits/2026-08-30-p2-003z-d300-ltcgate-defer-to-congestion-lever-refuted-false-positive-probe-retired.md). **NO PROGRESS EARNED (no copper promoted): PCB routing 0 %, overall 74 %, readiness ~77 %.**

---

## 2026-08-30 - FBV2-P2-003Y: D-299 — the D-298 U19 CAPACITY lever's full-authority gate COMPLETED and it is a GENUINE +2 connected-set gain (NOT the D-296 swap) — so `AQROOT_U19CAP` is ACCEPTED and COMMITTED (banked env-gated / OFF-by-default, pinned by G14); but copper is NOT promoted because full Phase-A still FAILs, the terminal wall newly ADVANCING past the whole U19 field to `LTC_GATE U18.10→Q3.4` (candidate paths DRC-gate-rejected by the frozen D-249 BPP-trunk-width and D-269 BAT_MAIN-clearance rules), readiness/progress unchanged, autonomy CONTINUES, D-275 and D-277..D-298 preserved

**A GOVERNED CTO ACCEPT + COMMIT (the U19CAP source lands) + A GOVERNED FAIL OF THE OVERALL PHASE-A RUN + HANDOFF — AUTONOMY CONTINUES (a newly-exposed bounded wall is not a stop reason; no owner decision is raised).** Starting HEAD `7a39430` (D-298; `phaseA_journal.json` at HEAD) carrying the uncommitted OFF-by-default `AQROOT_U19CAP` U19 east-lane reservation + U19.7-first lever in `checks/route_battery_block.py` and its G14 contract in `checks/router_regression.py`. The CTO ran the FULL authority gate (the only judge that promotes copper — D-286).

**THE GATE RAN AND COMPLETED.** The governing foreground run `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 bash w/run_003t_full.sh 003y2_u19cap w/cand_003t/t_a_r77e15n10_r79e15n10.json` → `checks/w/phaseA_003t_full_003y2_u19cap.json` (secs **1463.2**, driver exited clean); the SHARED `phaseA_journal.json` was restored **byte-identical to HEAD** afterward and **no process remains**. A genuine full-authority artifact (not a proxy/focused vehicle — D-286), judged by `checks/w/judge_003y2.py`.

**THE VERDICT — A GENUINE +2, NOT A SWAP.** vs the D-297 003W baseline `w/phaseA_003t_full_003w_u18bpp_i3.json` (conn 70): connections **70→72**, skipped **99→101**, ratsnest **707/−74 → 705/−76**, journal **73→75**; the connected-set diff **GAINED exactly 2 — `N_BATDIV R89.2→U19.6` and `REC_BAT_LOW (node)→U19.7` (both SIG, F.Cu, 2 vias, board-legal 0.60/0.30) — and LOST 0.** Both boxed U19 pins close SIMULTANEOUSLY for a strict +2 with nothing lost — the categorical opposite of D-296's 1-for-1 swap; the U19 field is genuinely ENLARGED (`U19.7` 15.621 mm, `U19.6` 9.52 mm, both F.Cu 0.60/0.30 — the full router's board-legal choice, slightly different from the probe's In3/In2 route but the same +2). `LTC4368_FAULT_N` DETOURS CLEANLY (the D-298 §5 risk resolved): all three branches connected on B.Cu (`U18.7→R81.2` 8.478, `R81.2→R82.1` 2.719, `R82.1→Q9.1` **77.567** — the 64 mm run detoured ~13 mm longer and still cleared the per-connection `gate()`), FAULT_N not the terminal wall. Final DRC histogram **identical** to 003W `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}` — no new class, no increase; no sub-0.50 non-fine via (run via diameters 0.35/0.60/0.65/0.80, all on/above the D-257 ladder).

**THE NEW TERMINAL WALL — `LTC_GATE U18.10→Q3.4`, characterized without a new route.** The +2 U19 closure moved the wall two connections forward, past the whole U19 field, to the LTC4368 gate-drive net. It is **NOT** `NO_PATH`/`NO_LEGAL_ESCAPE` — candidate join paths ARE found but the per-connection `gate()` REJECTS every one for TWO FROZEN OWNER RULES: (1) **D-249** `BAT_PROTECTED_P` high-current trunk (min 1.20 mm) — the candidate narrows to 0.20 mm where the BPP trunk-area rule applies (it enters the western-margin BPP trunk keep-region); (2) **D-269** `BAT_MAIN` routed clearance (0.300 mm) — the candidate comes within **0.2803 mm**, only ~19.7 µm short. `LTC_GATE`'s other segments are all connected (`U18.10→R76.1` F.Cu FINE_ESC_3 2× 0.35/0.20 vias; `Q3.2→Q3.4`/`Q2.2→Q2.4`/`Q3.2→Q2.2` B.Cu); the failing connection is the JOIN bridging the `U18.10` F.Cu escape cluster to the `Q3.4` B.Cu gate cluster. This is the SAME family as the U18.8/U19 walls — a full-run-emergent congestion/corridor pinch on a flexible low-current control net squeezed between the BPP trunk (D-249) and a BAT_MAIN path (D-269) — **bounded and reducible in principle** (the join has slack; the D-269 miss is ~20 µm), a routing/ordering lever within CTO scope, NOT an owner decision and NOT a rule relaxation.

**RULING (D-299).** The U19 CAPACITY lever is a genuine +2 → **ACCEPTED and COMMITTED**: the two source files (`checks/route_battery_block.py` `AQROOT_U19CAP` lever, `checks/router_regression.py` G14) are retained and committed, banked env-gated / **OFF by default** (byte-identical when unset; D-298 deliberately deferred this commit to the gate). Copper is **NOT promoted** — full Phase-A still FAILs at the new LTC_GATE wall, so the authoritative board stays six layers / 0 tracks / 0 vias and readiness/progress DO NOT move (D-286: only a full PASS promotes). A governed CTO ACCEPT + COMMIT + overall-run FAIL, NOT an owner decision (no floor relaxed, no frozen part moved, no DRU change); `/home/aqroot8/.aqroot-autopilot-stop` ABSENT, autonomy CONTINUES.

**TESTS.** `python3 checks/router_regression.py` → **ALL CHECKS PASS**, incl. **G14** (lever OFF by default → byte-identical; `AQROOT_U19CAP` activates; reserved-lane geometry spans U19.7/U19.6; hooks scoped to the U19 east lane + REC_BAT_LOW-before-N_BATDIV).

**INTEGRITY.** Authoritative PCB byte-identical to HEAD (`sha256 2235e2736838…d642d7e`; six layers, 0 tracks, 0 vias, placement at home); no DRC absorbed; `phaseA_journal.json` at HEAD; no via below the D-257 ladder; D-269 (0.300 mm), ≥1.20 mm BPP (D-249), 0.60 mm BAT_MAIN ENFORCED; D-290 untouched; the accepted `AQROOT_U18BPP_JOIN` (D-297), `place_003l` (D-285), the D-275/D-288 bridge, D-275 and D-277..D-298 preserved; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged. **NEXT — FBV2-P2-003Z:** one narrowly-scoped env-gated (OFF-by-default) bounded lever that re-sites/re-orders/detours the `LTC_GATE U18.10→Q3.4` join corridor so its path stays clear of the `BAT_PROTECTED_P` 1.20 mm trunk region (preserving D-249) and opens the 0.300 mm `BAT_MAIN` clearance (preserving D-269), within D-257/D-266 mechanics, keeping `AQROOT_U18BPP_JOIN=I3`+`AQROOT_U19CAP=1` ON, full-authority-gate judged (connected-set diff vs `w/phaseA_003t_full_003y2_u19cap.json` and `w/phaseA_003t_full_003w_u18bpp_i3.json`), **without** any D-290 reauth, DRU/rule change, via below the D-257 ladder, D-249/D-269 relaxation, or topology/footprint/outline change. Full analysis: [`audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md`](audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md). **NO PROGRESS EARNED (no copper promoted): PCB routing 0 %, overall 74 %, readiness ~77 %.**

## 2026-08-30 - FBV2-P2-003W: D-297 — the SECONDARY U18.8 I2-join lever (the D-295/D-296 handoff) completes `BAT_PROTECTED_P U18.8→R75.2` on In3 for a GENUINE +1 connected-set gain — a PURE JOIN with NO casualty, NO new via, NO new DRC class, and the lone `via_dangling` cleared — so it is ACCEPTED and retained env-gated / OFF-by-default in tracked source; but copper is NOT promoted (the full run still FAILs on the saturated U19 field), readiness/progress unchanged, autonomy CONTINUES, D-275 and D-277..D-296 preserved

**A GOVERNED ACCEPT OF A SECONDARY LEVER + A GOVERNED FAIL OF THE OVERALL PHASE-A RUN — AUTONOMY CONTINUES (a normal Phase-A FAIL is not a stop reason; no owner decision is raised).** Starting HEAD `27f9790` (pushed; `phaseA_journal.json` at HEAD) carrying the uncommitted lever WIP `checks/route_battery_block.py` (+25/−1 lines: the env-gated, OFF-by-default `AQROOT_U18BPP_JOIN` lever the D-295/D-296 handoff designed), a G13 regression contract in `checks/router_regression.py`, and the measured-record probe `checks/u18_i3_join_probe_003w.py`. The CTO ran the FULL authority gate (the only judge that promotes copper — D-286).

**THE WALL (D-294/295).** At the D-293 direction-2 placement `t_a_r77e15n10_r79e15n10` the `BAT_PROTECTED_P` reserve pair places two ordinary 0.35/0.20 **THROUGH** vias at `R75.2` (2.800,66.800) and `U18.8` (7.200,66.500) on **In2**; their In2 JOIN is `NO_PATH` because a `BAT_RAW` 0.600 mm current-path wall runs vertically on In2 at x≈6.4→6.65 (y 50.45→70.40), severing the west→east lane between them. U18.8 stays open (non-fatal).

**THE LEVER (D-297).** The reserve vias are THROUGH vias (copper on every layer), so the join is electrically identical on In2 or In3. **In3.Cu is a routable six-layer signal layer** (`qrouter.ROUTABLE[6]=('F','B','I2','I3')`) that is **EMPTY across the whole corridor** on the real full-run board (2 In3 tracks board-wide, none here; no In3 pour — only the In1/In4 GND planes). `AQROOT_U18BPP_JOIN` (`'I2'`/`'I3'`, `.upper()`-normalised) names the join layer for **exactly one branch** — guarded on the env flag AND `net==BAT_PROTECTED_P and a=='U18.8' and b_=='R75.2'`, nothing wider; unset → the join stays on `va[2]` (In2), byte-identical to every prior run.

**PROBE (`u18_i3_join_probe_003w.py`, on the actual full-run routed board `w/FULL003T_e15n10cto/…kicad_pcb`, throwaway copy so the evidence board is never mutated):** In2 join `NO_PATH` (the D-294 wall reproduces); In3 join **ok 4.410 mm**; real KiCad DRC adds **ZERO new classes**; the lone `via_dangling` **1→0** (the join absorbs the previously-dangling reserve via). ALL CHECKS PASS.

**FULL AUTHORITY GATE (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`, secs 1272.5), vs the D-294 baseline `w/phaseA_003t_full_e15n10cto.json`:** connections **69→70** (+1), skipped-already-connected **98→99** (+1 — one downstream `BAT_PROTECTED_P` pad is now found already-joined on the closed net; a positive sign, not a loss), ratsnest **708/−73 → 707/−74** (one more edge cleared), journal **72→73** (+1: `JOIN U18.8→R75.2` layer **I3**, 4.410 mm, **0 vias**), DRC `via_dangling` **1→0** with **no new class** (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}`), terminal fatal wall **UNCHANGED** (`REC_BAT_LOW U19.7→(node) NO_LEGAL_ESCAPE`, `N_BATDIV U19.6` next-in-line).

**THE DECISIVE DIFF IS A STRICT PURE GAIN.** The entire journal delta is **exactly one added JOIN entry with NOTHING lost** — the categorical opposite of D-296's 1-for-1 swap. The In3 join takes routing capacity from **no other net** (In3 is unused in the corridor), so no casualty is possible and none occurs.

**RULING.** The SECONDARY lever is a genuine, board-legal, verified net gain — **ACCEPTED** and retained env-gated/OFF-by-default in tracked source (byte-identical when unset), pinned by the G13 contract + the probe. **But copper is NOT promoted:** Phase-A copper promotes only on a full-authority PASS (D-286), and the run still FAILs on the unchanged saturated U19 field — so the authoritative board stays six layers / 0 tracks / 0 vias and readiness/progress DO NOT move. D-297 **banks** the U18.8 closure in source: once the U19 field is separately enlarged, this lever (ON) yields the U18.8 join for free (no new via, no new DRC). A governed CTO ACCEPT + overall-run FAIL, NOT an owner decision (no floor relaxed, no frozen part moved, direction-2 not exhausted); `/home/aqroot8/.aqroot-autopilot-stop` ABSENT, autonomy CONTINUES.

**TESTS.** `router_regression.py` ALL CHECKS PASS incl. new **G13** (In3 routable; lever OFF by default → byte-identical; `AQROOT_U18BPP_JOIN=I3` activates the In3 join; a non-I2/I3 value never activates; override scoped to exactly `BAT_PROTECTED_P U18.8→R75.2`); `u18_i3_join_probe_003w.py` ALL CHECKS PASS.

**INTEGRITY.** Authoritative PCB byte-identical to HEAD (`sha256 2235e2736838…d642d7e`; six layers, 0 tracks, 0 vias, placement at home); no DRC absorbed (the +1 connection / `via_dangling` clear live only on gitignored full-run scratch); `phaseA_journal.json` at HEAD (backed up/restored around the run); no via below the D-257 ladder; D-269 (0.300 mm), ≥1.20 mm BPP, 0.60 mm BAT_MAIN ENFORCED; D-290 untouched; `place_003l` (D-285) and the D-275/D-288 bridge preserved; D-275 and D-277..D-296 preserved; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged; gitignored evidence preserved (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`, `w/FULL003T_e15n10cto/`, `w/TEST003W_PROBE/`).

**NEXT — FBV2-P2-003X:** the last Phase-A blocker is the **simultaneous `REC_BAT_LOW U19.7` + `N_BATDIV U19.6` closure** in the F.Cu/B.Cu-saturated U19 dead-cell field; per D-296 a single-pin reservation only swaps, so implement ONE bounded, env-gated (OFF-by-default) **U19 capacity** lever that offloads a saturating escape (the direction-2-induced `VREC_VCC U19.8` F.Cu pad-escape and/or a boxed U19 escape) onto a bare inner layer (In2/In3, proven free by D-297) within D-257/D-266 mechanics — no via below the D-257 ladder, no D-290 reauth, no DRU/rule/topology/footprint/outline change — judged by the full-authority connected-set diff (must close U19.7 AND U19.6 for a real gain; a 1-for-1 swap is NOT a gain), promoting copper only on a genuine full Phase-A PASS (keep the direction-2 placement and the accepted D-297 U18.8 lever ON).

**Evidence of record:** audit [`audits/2026-08-30-p2-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md`](audits/2026-08-30-p2-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md); committed source (`checks/route_battery_block.py`, `checks/router_regression.py` G13, `checks/u18_i3_join_probe_003w.py`); gitignored scratch (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`, `w/FULL003T_e15n10cto/`, `w/TEST003W_PROBE/`, `w/run_003t_full.sh`, `w/cand_003t/t_a_r77e15n10_r79e15n10.json`). **A GENUINE NET GAIN BANKED IN SOURCE, BUT NO COPPER PROMOTED: PCB routing 0 %, overall 74 %, readiness ~77 %.**

---

## 2026-08-30 - FBV2-P2-003V: D-296 — the PRIMARY U19.7 escape-reservation lever (the D-295 handoff) FIRES and CLOSES U19.7 with a board-legal 0.60/0.30 via, but it is a bounded ORDERING TRADE with NO connected-set progress — it merely chooses which pin of the saturated U19 field is the casualty (gains `REC_BAT_LOW U19.7`, loses `REF_POL U19.2`; conn 69/skip 98/ratsnest 708/−73 all unchanged; DRC identical; terminal wall moves U19.7→U19.6) — so it is REJECTED for production and the uncommitted `AQROOT_U19_RESV` source WIP is RETIRED; no source/copper/placement/rule change survives, no DRC absorbed, no promotion, autonomy CONTINUES, D-275 and D-277..D-295 preserved

**A GOVERNED FAIL / PRIMARY-FAMILY REFUTATION — AUTONOMY CONTINUES (a normal Phase-A FAIL is not a stop reason; no owner decision is raised).** Starting HEAD `a2e27fc` (pushed; `phaseA_journal.json` at HEAD) carrying one uncommitted WIP file `checks/route_battery_block.py` (+65 lines: the env-gated, OFF-by-default `AQROOT_U19_RESV` lever the D-295 handoff designed — reserve `REC_BAT_LOW U19.7`'s B.Cu escape + one through via, scored toward Q7.1, BEFORE the `tight='U19'` pin field runs). Two full authority runs were completed under CTO authority and are analysed here; **no new long run was performed in this closeout** (both artifacts already existed).

**RESV (0.35/0.20 rung) — BEHAVIOURALLY IDENTICAL TO D-294.** The corridor-less reservation has no FINE_ESC override, so the sub-minimum D-257 0.35/0.20 via is rejected on `via_diameter` (board minimum 0.50 mm) and `annular_width` (0.075 < 0.125 mm floor); the reservation (non-fatal) is dropped and the run falls through the ordinary path unchanged. `checks/w/phaseA_003t_full_003v_u19resv.json`: conn **69**, skip **98**, ratsnest **708/−73**, journal **72** (NO `RESERVE` step laid), DRC `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499, via_dangling:1}`, terminal fail still `REC_BAT_LOW U19.7→(node) NO_LEGAL_ESCAPE`. **Connected-set diff vs the D-294 governing baseline `w/phaseA_003t_full_e15n10cto.json` is EMPTY both ways** — exactly the promised "unset reproduces the run byte-for-byte" property.

**RESV2 (0.60/0.30 board-legal rung) — FIRES, CLOSES U19.7, BUT ONLY SWAPS THE CASUALTY.** The corridor-less rung self-corrects to the smallest via legal under GLOBAL rules with no corridor: the ordinary Default-class GENERAL_SIGNAL 0.60/0.30 (diameter 0.60 ≥ 0.50, annular 0.150 ≥ 0.125) — precisely the via `REC_BAT_LOW`'s own SIG route already lands. The reservation is laid (journal **73**: +1 `RESERVE` step `REC_BAT_LOW U19.7→Q7.1`, 1 via) and U19.7's SIG edge completes: **U19.7 ROUTES.** But the saturated U19 dead-cell pin field is not enlarged, only re-ordered — `checks/w/phaseA_003t_full_003v_u19resv2.json`: conn **69** (unchanged), skip **98** (unchanged), ratsnest **708/−73** (unchanged), **identical DRC histogram**, and the terminal wall MOVES to `N_BATDIV U19.6→(node) NO_LEGAL_ESCAPE` (blocked by U19.7 ×22, U19.5 ×20, track ×6, C60.2 ×5).

**THE DECISIVE CONNECTED-SET DIFF (D-294 → RESV2) IS A STRICT 1-FOR-1 SWAP.** GAINED `REC_BAT_LOW U19.7→Q7.1 (SIG)`; LOST `REF_POL TP24.1→U19.2 (SIG)`. Requested-connected count 68→68. Reserving U19.7's B.Cu lane simply takes it from an equally-saturated neighbour, so the greedy-tightest-first race walls on a different U19 pin — U19.2 open, wall at U19.6. **No connection is genuinely gained or lost; the field is capacity-saturated on F.Cu/B.Cu, not priority-limited for one pin.**

**POSITIVE FINDING (recorded, not promoted).** The reservation MECHANISM is REAL and the D-295 diagnosis is CONFIRMED: with a board-legal via the lever fires exactly as predicted, U19.7 is closable in principle, and the run stays fully board-legal (DRC histogram unchanged, no rule relaxed, no via below the D-257 ladder — the corridor-less rung self-corrects). But closing one pin at the cost of another in a saturated field is NOT a net gain, and per D-286 nothing — not even a genuine full-authority run — promotes copper without real connected-set progress.

**RULING (D-296) & RETIREMENT.** REJECTED for production; the `AQROOT_U19_RESV` source WIP is RETIRED via an **exact reverse patch** (`git diff -- checks/route_battery_block.py > /tmp/003v_u19resv_wip.patch; git apply -R` — scoped to the WIP hunks, NOT a destructive broad reset). Proof: `git diff --stat checks/route_battery_block.py` empty; worktree blob `bba62d35efd5de9451dbd12ec85cee89e608e912` = `HEAD:checks/route_battery_block.py` blob (byte-identical); `git grep U19_RESV` over tracked source (excluding gitignored `checks/w/`) returns NO match — no `AQROOT_U19_RESV` code remains in tracked source; working tree clean apart from these docs. Gitignored evidence preserved: `checks/w/phaseA_003t_full_003v_u19resv.json`, `…_u19resv2.json`, `w/FULL003T_003v_u19resv*/`, `w/TEST003V_U19RESV/`. This refutes the PRIMARY reservation family from the D-295 handoff — a governed FAIL, not an owner decision (the SECONDARY U18.8/U18.9 I2 reserve-via lever remains open); `/home/aqroot8/.aqroot-autopilot-stop` ABSENT, autonomy CONTINUES.

**INTEGRITY.** Authoritative PCB byte-identical to HEAD (`sha256 2235e2736838…d642d7e`; six layers, 0 tracks, 0 vias, placement at home); no DRC absorbed (the U18.8 open, the U19.6/U19.7/U19.2 no-escape and the lone scratch `via_dangling:1` are surfaced FAIL evidence on gitignored scratch, never in the authoritative board); no promotion; `place_003l` (D-285) and the D-275/D-288 bridge preserved; D-275 and D-277..D-295 preserved; frozen `beta-full-reference-v1` untouched; `phaseA_journal.json` at HEAD; `JLCPCB_READINESS` unchanged; 0.200 mm / 0.25 mm / **0.300 mm D-269** / ≥1.20 mm BPP / 0.60 mm BAT_MAIN floors ENFORCED, D-290 closed. **NEXT — FBV2-P2-003W:** execute the SECONDARY D-295 lever — a bounded U18.8/U18.9 I2 reserve-via siting/ordering study for a ≥0.200 mm `U18.8→R75.2` join lane within existing D-257/D-266 corridor mechanics, full-authority-gate judged (connected-set diff vs `phaseA_003o_b1_r75rot_cto.json` and `w/phaseA_003t_full_e15n10cto.json`), **without** any D-290 reauth, DRU/rule change, via below the D-257 ladder, or topology/footprint/outline change. Full analysis: [`audits/2026-08-30-p2-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md`](audits/2026-08-30-p2-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md). **NO PROGRESS EARNED: PCB routing 0 %, overall 74 %, readiness ~77 %.**

---

## 2026-08-30 - FBV2-P2-003U: D-295 — the two D-294 walls are FULL-RUN-EMERGENT ordering/congestion casualties (no cheap vehicle judges either at the direction-2 placement); the PRIMARY (REC_BAT_LOW U19.7) is diagnosed exactly and shown REDUCIBLE-in-principle (it escaped cleanly in 003O; direction-2's +2-connection congestion swapped VREC_VCC U19.8's pad-escape onto the F lane U19.7 needed); the governing ~22-min full gate cannot run foreground under the ACP 10-min cap, so 003U delivers a precise CTO handoff (exact lever design + ready-to-run full-authority command); no source/copper/placement/rule change, no DRC absorbed, no promotion, autonomy CONTINUES, D-275 and D-277..D-294 preserved

**A GOVERNED CHARACTERIZATION / NO-PROGRESS + HANDOFF MILESTONE — AUTONOMY CONTINUES (a normal Phase-A FAIL is not a stop reason; no owner decision is raised).** Starting HEAD `36662db` (clean; `phaseA_journal.json` at HEAD). D-294 defined FBV2-P2-003U as a bounded full-context reservation/ordering corridor study of the two 003T walls at the D-293 direction-2 placement (`t_a_r77e15n10_r79e15n10`): PRIMARY reserve `REC_BAT_LOW U19.7`'s escape before its neighbors / re-route the six blocking tracks; SECONDARY study the U18.8/U18.9 I2 reserve-via siting/ordering — no DRU change, no D-290 reauth, no via below the D-257 ladder, no D-269/topology change — judged only by the full authority gate.

**THE BINDING CONSTRAINT.** Full Phase-A runs take ~1300–1780 s (003T = 1313.8 s); the ACP exec wrapper caps a single call at 10 min and 003U bars `&`/`nohup`/detached/tracked jobs / `Monitor` / scheduled wakeups (foreground-only). The governing gate cannot run inside this task, so — exactly as the 003U discipline anticipates — the cheap bounded characterization is done and a precise ready-to-run handoff is delivered instead of an orphaned long run.

**DECISIVE CHEAP EVIDENCE (connected-set diff 003O→003T, no new long run).** Diffing the committed `checks/phaseA_003o_b1_r75rot_cto.json` (conn 67) against gitignored scratch `checks/w/phaseA_003t_full_e15n10cto.json` (conn 69) at U19: in **003O all seven U19 pins escaped**, including `REC_BAT_LOW U19.7→Q7.1` (F.Cu 14.907 mm). Direction-2 moves nothing near U19 (U19 @ 2.695,28.255,0°; Q7/R93 unmoved), so the escape GEOMETRY is identical — the wall is not geometric. The +2-connection congestion **swapped `VREC_VCC`'s two segments' layers**: `U19.8→C60.1` went **B.Cu(0 via) → F.Cu(2 via)** and `C60.1→R84.2` went F → B, so U19.8's pad-escape now occupies the F lane immediately south of U19.7 that carried U19.7→Q7.1 in 003O (`U19.8` ×26 is duly the dominant blocker, with U19.6 ×13, U19.5 ×7, track ×6). U19.7 is then a **greedy-tightest-first casualty**: the driver already re-measures `order_tight` before every fine-pitch pin (`route_battery_block.py:2169-2181`, PR-32), so this is NOT a stale-slack-table bug — U19.7 is loose early (neighbors unrouted) so it sorts LATE, its neighbors consume its lane, and it is re-measured with no legal escape when its turn comes; `REC_BAT_LOW` then routes `Q7.1→R93.1` first and U19.7 falls to the closure stage as `U19.7→(node)`, which the D-278 inner hop cannot rescue because that hook is guarded `and not node` (`:1039`). **A reducible, ordering-class wall — NOT a D-289/290/292-class placement mutual-exclusion.**

**VACUITY PROVEN, not assumed.** `AQROOT_LOCAL=DEADCELL` (~2 min) omits the west prefix / BAT_RAW divider field whose +2-connection congestion IS the cause and is placement-independent (same result at home/003O/003T), so it structurally cannot reproduce the direction-2 box; `LOCAL=U19` reproduces the emergent dead-cell blockers but lays the whole prefix (~15–20 min, over the 10-min cap); `R80`/`D256` never route U19. So no sub-10-min vehicle faithfully judges the U19.7 lever. For the SECONDARY, the 003T `R80` focused screen reported the exact failing candidate as conn 20 `fail=None` **U18.8 JOIN ok** — vacuous.

**SECONDARY (U18.8 I2 join corridor).** At U18 north +1.25 both inner reserve vias place on I2 (003T journal steps 5/6 `RESERVE_PAIR` ok) and **U18.9 JOINs** (step 26), but `U18.8→R75.2` JOIN FAILs `NO_PATH` ("no I2 corridor at 0.200 mm between the two reserved vias") → fallback `NO_VIA_SITE`. Measured reserve vias on the routed board: `BAT_PROTECTED_P` 0.35/0.20 at (2.8,66.8)&(7.2,66.5), `BAT_SENSE` 0.35/0.20 at (4.25,63.5)&(4.6,66.0); nearest reserve-via pair ≈1.97 mm apart, so the failure is a full-congestion I2 corridor pinch (the join track cannot thread a ≥0.200 mm lane), not touching vias. Bounded lever: reserve-via siting/ordering on I2 within D-257/D-266 mechanics — full-gate-only to judge.

**VERDICT / HANDOFF.** Both walls are BOUNDED full-context routing/ordering casualties (no floor relaxed, no frozen part moved, D-290 untouched, D-269 enforced at 0.300 mm); the PRIMARY is reducible-in-principle with an exact mechanism and a bounded escape-reservation lever, the SECONDARY is a reserve-via-siting question — but neither is judgeable by any cheap vehicle at the direction-2 placement and the governing ~22-min gate cannot run foreground here. Per D-286 no proxy promotes copper → **no promotion**; a governed CTO characterization / NO-PROGRESS + HANDOFF, NOT an owner decision (direction-2 remains authorized and is not exhausted); stop file ABSENT, autonomy CONTINUES. **FBV2-P2-003V** implements ONE narrowly-scoped, env-gated (OFF by default) bounded lever (PRIMARY: reserve U19.7's escape before its neighbors in the reserve_escape family, and/or relax the D-278 `and not node` guard for the U19 group, and/or hold `VREC_VCC U19.8` on B.Cu; SECONDARY: re-site/re-order the U18.8/U18.9 I2 reserve vias), validates it against `router_regression.py` (authoritative byte-identical), then runs the FULL authority gate `bash w/run_003t_full.sh 003v_u19resv w/cand_003t/t_a_r77e15n10_r79e15n10.json` (lever env set; back up/restore the shared `phaseA_journal.json` around it), judged by the full-run connected-set diff vs `phaseA_003o_b1_r75rot_cto.json` and `w/phaseA_003t_full_e15n10cto.json`; promote copper only on a genuine full-authority PASS.

**INTEGRITY.** No source/copper/placement/rule change survives (`git diff --stat HEAD` empty for all driver source); authoritative PCB byte-identical to HEAD (`sha256 2235e273…d642d7e`; six layers, 0 tracks, 0 vias, placement at home); no DRC absorbed (the U18.8 open, U19.7 no-escape and lone scratch `via_dangling:1` are surfaced FAIL evidence on gitignored scratch, never in the authoritative board); no promotion; `place_003l` (D-285) and the D-275/D-288 bridge preserved; D-275 and D-277..D-294 preserved; frozen `beta-full-reference-v1` untouched; `phaseA_journal.json` at HEAD; `JLCPCB_READINESS` unchanged; 0.200 mm / 0.25 mm / 0.300 mm D-269 / ≥1.20 mm BPP / 0.60 mm BAT_MAIN floors ENFORCED, D-290 closed. Full analysis: [`audits/2026-08-30-p2-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md`](audits/2026-08-30-p2-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md). **NO PROGRESS EARNED: PCB routing 0 %, overall 74 %, readiness ~77 %.**

---

## 2026-08-30 - FBV2-P2-003T: D-294 direction 2 (D-293) executed — a focused minimum candidate genuinely exists, but the governing full authority gate FAILs, so no candidate is promotable; direction-2 is productive (+2 connections vs 003O, the old REF_POL R87.2 wall is now past) but incomplete (U18.8 still open on the full-context I2 join corridor; a NEW governing wall surfaces at REC_BAT_LOW U19.7 NO_LEGAL_ESCAPE); no source/copper/placement/rule change, no DRC absorbed, no promotion, autonomy CONTINUES, D-275 and D-277..D-293 preserved

**A GOVERNED EVIDENCE / NO-PROGRESS MILESTONE — AUTONOMY CONTINUES (a normal Phase-A FAIL is not a stop reason; no owner decision is raised).** Starting HEAD `9c708f3` (clean; `phaseA_journal.json` at HEAD). D-293 (Alpha, 2026-08-29 22:34 UTC) authorized **direction 2**: relocate the minimum necessary escape targets so `BAT_RAW` (U18.1 east) and `BAT_PROTECTED_P` (U18.8 west) — the two opposite-edge current-path nets D-292 identified — leave U18 through independent corridors, with every floor preserved and D-290 closed. 003T executed exactly that: a cheap focused screen, then a **full CTO-authority** run (the CTO completed the decisive run directly after ACP-wrapper failures).

- **The focused minimum exists.** A bounded candidate grid was screened on a cheap focused vehicle. East-only moves leave the east `LTC_OV U18.3→R77.2` current pin gate-rejected (`e10`/`e20` → clearance 6; the window is narrow — too small keeps the corridor tight, too large re-breaches), north-only (`n125`) breaches `LTC_UV U18.2→R79.2` (clearance 1), and R80/R81-north (`t_b`) leaves `LTC_UV` NO_LEGAL_ESCAPE. **Exactly one** combined move — `t_a_r77e15n10_r79e15n10` (R77/R79 **+1.5 mm east +1.0 mm north**, U18 north **+1.25 mm**) — clears every east **and** west U18 pin with **zero added DRC**: focused **conn 20, `fail=None`, U18.8 JOIN ok and U18.9 JOIN ok** (`checks/w/phaseA_003t_t_a_r77e15n10_r79e15n10.json`). This is the focused minimum direction-2 candidate, and the one the CTO advanced to the full gate.

- **The governing full gate FAILs** (`checks/w/phaseA_003t_full_e15n10cto.json`, secs 1313.8): PHASE A **FAIL** at **`REC_BAT_LOW U19.7→(node) NO_LEGAL_ESCAPE`** (blocked by U19.8 ×26, U19.6 ×13, U19.5 ×7, track ×6); **conn 69, skipped 98, ratsnest 781→708 (−73)**. U18.9 JOINED (In2 Kelvin) but **U18.8 stayed OPEN** — `R75.2` join `NO_PATH` (no I2 corridor at 0.200 mm **between the two reserved vias**: the U18.9-Kelvin and U18.8-`BAT_PROTECTED_P` reserve vias pinch the join corridor under full congestion), then fallback `NO_VIA_SITE` (no 0.65 mm B via site). Final DRC `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499, via_dangling:1}` — the residual scratch dangling is SURFACED, not absorbed.

- **Direction-2 is productive but incomplete.** vs the committed 003O baseline (`checks/phaseA_003o_b1_r75rot_cto.json`: conn 67, skip 99, rats 708/−73, FAIL `REF_POL R87.2→(node) NO_PATH`), direction-2 routed the independent `BAT_RAW` east corridor (U18.1/U18.2/U18.3 all connect), gained **+2 connections (67→69)** and moved the terminal wall **past `REF_POL R87.2`** to a new `U19.7` escape wall — but U18.8 is still one trunk pad short.

- **D-293 verdict.** The focused closure is **vacuous vs the congested full run** (the governing gate) — the full context adds the I2 reserve-via pinch and the new U19.7 wall the cheap vehicle cannot see; a candidate that closes only in the focused vehicle is NOT promotable (D-286: no proxy promotes copper). **No 003T candidate passes the full authority gate → no promotion.** A governed CTO **FAIL**, NOT an owner decision (direction-2 was authorized, remains valid, and is not exhausted; the two walls are bounded full-context routing/ordering walls with no floor relaxed and no frozen part moved); `/home/aqroot8/.aqroot-autopilot-stop` stays **ABSENT** and autonomy CONTINUES.

- **Integrity.** No source, copper, placement or rule change; authoritative PCB **byte-identical to HEAD** (`sha256 2235e273…d642d7e`; six layers, 0 signal tracks, 0 signal vias, 0 arcs, placement at home); **no DRC absorbed** (the U18.8 open, the U19.7 no-escape, and the lone scratch `via_dangling` are the surfaced FAIL evidence, never in the authoritative board); `place_003l` (D-285) and the D-275/D-288 bridge preserved; D-275 and D-277..D-293 preserved; 0.200 mm clearance + 0.25 mm hole-to-hole + 0.300 mm D-269 current-path + ≥1.20 mm BPP trunk + 0.60 mm BAT_MAIN floors ENFORCED; frozen `beta-full-reference-v1` untouched; `phaseA_journal.json` at HEAD; `JLCPCB_READINESS` unchanged. Scratch evidence gitignored under `checks/w/` (`phaseA_003t_full_e15n10cto.json`, `FULL003T_e15n10cto/`, `phaseA_003t_t_*.json`, `log_003t_*.txt`, `Q003T_*/`, `cand_003t/`, `mkcands_003t.py`, `batch_003t.sh`). **NO PROGRESS EARNED: PCB routing 0 %, overall 74 %, readiness ~77 %.** **NEXT: FBV2-P2-003U** — a bounded full-context reservation-and-ordering corridor study of the two named walls at the D-293 placement: (1, PRIMARY) reserve `REC_BAT_LOW U19.7`'s escape before its neighbor pins U19.8/U19.5 and/or re-route the six blocking tracks (escape-ordering, no DRU change); (2, SECONDARY) study the U18.8/U18.9 I2 reserve-via siting/ordering to open a ≥0.200 mm join corridor within D-257/D-266 mechanics — without re-authorizing D-290, dropping any via below the D-257 ladder, weakening D-269, or changing topology/footprint/outline. Full analysis: [`audits/2026-08-30-p2-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md`](audits/2026-08-30-p2-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md).

## 2026-08-29 - FBV2-P2-003S: D-292 the owner-approved bounded LTC4368/R75 placement micro-ECO (D-291) is screened to EXHAUSTION — no bounded U18/R75 placement LEGALLY co-closes the U18 escape field; the wall is sharper than D-290 (U18 carries a current-path net on BOTH edges — BAT_PROTECTED_P/U18.8 west and BAT_RAW/U18.1 east — at a rigid 0.5 mm pitch, so a rigid move only trades which edge breaches the 0.300 mm D-269 floor); closing BAT_PROTECTED_P re-escalates to a genuine OWNER decision; no source/copper/placement/rule change, no DRC absorbed, no promotion, D-275 and D-277..D-291 preserved

**A GOVERNED EVIDENCE / NO-PROGRESS MILESTONE THAT RE-RAISES ONE OWNER DECISION.** Starting HEAD `951d7bf`. D-291 (Alpha) approved a bounded D-284/285-class LTC4368/R75 placement micro-ECO to open a *second, independent* U18.8 escape and co-close U18.7/U18.8/U18.9, with engineering proof a separate CTO gate. 003S is that gate: a cheap, in-scope placement screen with the explicit charter to **stop at exact-evidence exhaustion rather than broaden scope**.

- **The vehicle.** Candidates were built and bare-screened at the D-286 pre-copper boundary (`w/screen_003s.py`: real `kicad-cli` DRC + real `qb.escape` vs the `place_003l` clean reference), then co-closure-tested on **`AQROOT_LOCAL=R80`** — the narrower west-margin prefix (U18 8-pin field + D-266 Kelvin reservations + trunk + BAT_MAIN + BAT_RAW bridges; skips the east taps/gauge), validated **byte-identical to `D256` on the U18.7/8/9 verdict** and ~2.7× faster (≈350 s vs ≈915 s here). Baseline `b1_r75rot` = **conn 19, DRC clean, U18.8 the sole open pad** (the D-290 clash reproduced faithfully).

- **R75 is boxed on all four sides** (measured, `w/region_003s.py`): frozen **Q3** (BAT_SENSE current path) north edge y=59.575 leaves R75 ≈0.55 mm of southern travel before the 0.200 mm floor; board edge west (pad at x=2.188); U18 courtyard east (an R75 east move bare-overlaps/shorts — `s_r75e`/`s_r75e_n075` REJECT); R80/R81 north. U18 has ≈2.7 mm north headroom (to R80) and ≈1 mm south (to R77); west/south translations bare-overlap R75/R77 courtyards (`s_w05`/`s_s05` REJECT).

- **The screen (every candidate ≤ conn 19; baseline U18.8-open is the max LEGAL state).** EAST translation (`s_e05/e10/e15`) = conn 19, U18.8 stays open (never nears the fixed R75.2 — invariant); R75-south-alone (`s_r75smax`) = conn 19, U18.8 open (neutral); NORTH raises U18.8 toward R75.2 and **does open a legal inner-I2 via for U18.8** (the sought "second escape" genuinely exists) but the same move breaks the OTHER edge — `s_n05/n075` conn 18 (**U18.7** GATE_REJECTED 0.25<0.30, the exact D-290 arithmetic relocated), `s_n10` conn 17, `s_n125` conn 17 (**all 5 west close** but **east U18.1/U18.2/U18.3** GATE_REJECTED 0.275/0.284/0.296 < 0.300); the R75-south+U18-north align (`s_align/alignB/alignC`) conn 17-18 (breaks the **U18.9 Kelvin** or U18.1/U18.7). **The one candidate to reach PHASE A COMPLETE (`s_ne0707`, U18 NE +0.75/+0.75) does so ONLY by absorbing a genuine 0.1248 mm `BAT_RAW`↔`BAT_PROTECTED_P` D-269 breach (41 % of the 0.300 mm floor)** — DISQUALIFIED per the 003S reject criteria (sub-floor clearance) and D-286 no-absorption; no full Phase-A run is warranted (the congested full run is *less* forgiving than the cheap vehicle).

- **Root cause, sharper than D-290.** D-290 proved the west three-into-one-corner at fixed placement; 003S proves the owner-approved placement lever cannot resolve it because **U18 (LTC4368, MSOP-10) carries a current-path net on BOTH edges** — `BAT_PROTECTED_P` (U18.8, west) and `BAT_RAW` (U18.1, east) — and its 0.5 mm pitch is rigid on each, so a rigid translation only re-selects which edge's 0.300 mm D-269 clearance breaks; R75 (boxed) cannot help without breaking the Kelvin.

- **Why it re-raises an OWNER decision.** The remaining levers all fall OUTSIDE the D-291 envelope: U18 rotation (relocates the trunk pad off the west edge = a western-block refloorplan/direction-2, risks the frozen D-275/D-288 bridge); moving the escape targets R77/R79/R80/R81 (outside U18/R75 scope); or re-authorizing the D-290-refuted+retired off-layer vacate routing lever (a driver change re-opening a closed CTO decision). The charter instructed stopping at exhaustion, so this is a governed CTO **FAIL** that re-raises the OWNER decision; `/home/aqroot8/.aqroot-autopilot-stop` is re-created (OWNER_DECISION) and autonomy is HALTED.

- **Integrity.** No source, copper, placement or rule change survives; authoritative PCB byte-identical (six layers, 0 tracks, 0 vias); **no DRC absorbed into the authoritative board** (the lone `s_ne0707` absorption is the disqualifier on throwaway scratch, explicitly rejected). `place_003l` (D-285) preserved; D-275 and D-277..D-291 preserved; 0.200 mm clearance + 0.25 mm hole-to-hole + 0.300 mm D-269 current-path + ≥1.20 mm BPP trunk + 0.60 mm BAT_MAIN floors ENFORCED; frozen `beta-full-reference-v1` untouched; `phaseA_journal.json` restored to HEAD; `JLCPCB_READINESS` unchanged. Scratch evidence gitignored under `checks/w/` (`cand_003s/`, `screen_003s_results.json`, `phaseA_003s_*.json`, `log_003s_*.txt`, `drc_ne0707_check.json`). **NO PROGRESS EARNED: PCB routing 0 %, overall 74 %, readiness ~77 %.** **NEXT: OWNER DECISION** — (C) direction-2 spread/relocate-target; (D) re-authorize a routing lever (re-litigating D-290); or (B) accept U18.8 open (not fabricable). Full analysis: [`audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md`](audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md).

## 2026-08-29 - OWNER DECISION D-291: bounded LTC4368/R75 placement micro-ECO approved

Alpha ratified the CTO-recommended option A at 19:27 UTC: authorize the bounded D-284/285-class LTC4368/R75 placement micro-ECO required by FBV2-P2-003R / D-290 to open a second independent U18.8 escape. Approval is deliberately narrow: all safety/routing/clearance floors, topology, six-layer stack, frozen reference, and D-275/D-277..D-290 remain locked; no direction-2 widening, broad refloorplan, DRU relaxation, or open-U18.8 acceptance is authorized. No engineering result or progress/readiness increase is claimed by this decision record. **NEXT: FBV2-P2-003S** from clean `a6da795`: bounded placement screen, then full Phase-A integration of the first valid candidate.

## 2026-08-29 - FBV2-P2-003R: D-290 the LAST bounded routing-only U18 co-closure lever (off-layer vacate of U18.7) is REFUTED on cheap non-vacuous evidence (−1 regression, conn 34 vs baseline 35), the refutation is geometric and exact (the U18.7/U18.8/U18.9 3-into-one-corner contention is an irreducible placement-geometry mutual-exclusion at the 0.5 mm pad pitch vs the 0.300 mm current-path clearance floor — the vacate moves U18.7's escape transition from a 0.15 mm B.Cu neck 0.250 mm from U18.8's reserve via to a 0.35 mm through via 0.150 mm from it, CLOSER not farther, so In2 and In3 both revert; U18.9 is an independent casualty), so a bounded LTC4368/R75 placement micro-ECO is now a genuine OWNER DECISION; the D-290 WIP is retired, no source/copper/placement/rule change, D-275 and D-277..D-289 preserved

**A GOVERNED EVIDENCE / NO-PROGRESS MILESTONE THAT RAISES ONE OWNER DECISION.** Starting HEAD `9bd7aac`. D-289 named exactly one bounded routing-only lever left to co-close U18.7/U18.8/U18.9: vacate the contended pin (U18.7 → R81.2) off the single shared B lane onto an inner layer so U18.8 can reserve the corner alone. 003R implemented it (the D-290 WIP: `AQROOT_VACATE=U18_7` forcing U18.7 onto In2/In3 via a 0.35/0.20 through via FIRST, coupled with `AQROOT_U18_FIRST=1` reserving U18.8 alone) and screened it on the cheap non-vacuous `AQROOT_LOCAL=D256` west-prefix vehicle. **Metrics (verified from the committed JSONs):** baseline `phaseA_003r_baseline.json` conn **35** (U18.7 CLOSED B.Cu 9.728 mm / U18.9 CLOSED In2 north hop / U18.8 OPEN `NO_VIA_SITE`); lever `phaseA_003r_lever.json` (both `AQROOT_VACATE`/`AQROOT_U18_FIRST` in the log env) conn **34** — U18.8 closes but **U18.7 GATE_REJECTED** 0.250<0.300 (D-269) and **U18.9 NO_LEGAL_ESCAPE** (blocked by U18.10 ×25 / U18.7 ×17 / track ×15); identical final DRC (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}`), violation surfaced-and-reverted. **The vacate genuinely fired** (`VACATE_SETS['U18_7']` key matches `battery_route_plan.py:95`, `node=False`; `connect_hop(far='I2')` then `far='I3')` both reverted) **and is geometrically refuted, not "one implementation failed":** on the positive baseline board In1/In4 are the plane layers and In2/In3 are free signal layers (In3 empty in the corridor) and control nets were never barred from the inner layers — so no plane and no rule bars the hop; the blocker is the **pad-exit zone** at the fixed 0.5 mm pad pitch, where U18.8 sits BETWEEN U18.7's south escape and U18.9's north escape and every escape must exit within 0.5 mm of the adjacent pin's committed copper. Arithmetic: U18.7 neck(0.15)↔U18.8 reserve-via(0.35)=**0.250 mm** (== the measured DRC, FAIL vs the 0.300 mm floor); U18.7 vacate-via(0.35)↔U18.8 reserve-via(0.35)=**0.150 mm** (WORSE — why In2/In3 revert). A via ≤0.25 mm reaches 0.300 (== floor, zero margin) and two adjacent vias need sub-0.20 mm (below the D-257 ladder = a DRU change, BARRED; and the reserve via "answers a via-geometry question only … never [dropped] to buy a corridor a legal width could not have"), and none reopens U18.9 (dominant blocker U18.10, untouched). Ordering (D-289), off-layer vacate (D-290) and via-size are all refuted or barred — **no concrete legal routing-only site exists.** **This fires the standing policy trigger** (CURRENT_STATE §5/§8, D-289): a genuine OWNER DECISION — a bounded LTC4368/R75 placement micro-ECO (D-284/285 class) to open a *second* U18.8 escape, or direction-2 corridor widening — arises only if 003R also fails to co-close the three pins without relaxing a floor/rule or moving a frozen part. 003R failed exactly that way, so `/home/aqroot8/.aqroot-autopilot-stop` is now **PRESENT (OWNER_DECISION)** and autonomy is HALTED. The D-290 WIP is retired (reverted `battery_route_plan.py`, `route_battery_block.py`, `phaseA_journal.json`); committed evidence of record `checks/phaseA_003r_baseline.json` + `checks/phaseA_003r_lever.json`; scratch gitignored. No copper/placement/rule change; no DRC absorbed; `c3_00` not promoted; `place_003l` (D-285) preserved; D-275 and D-277..D-289 preserved; frozen `beta-full-reference-v1` untouched; `.aqroot-progress.env` NOT edited; readiness ~77 %, routing 0 %, overall 74 % unchanged. **NEXT: OWNER DECISION** — authorize (A, CTO-recommended) a bounded LTC4368/R75 placement micro-ECO to open a second independent U18.8 escape; or (B) accept U18.8 open (not fabricable); or (C) direction-2 widening / broader refloorplan. Full analysis: [`audits/2026-08-29-p2-003r-d290-off-layer-vacate-refuted-owner-decision.md`](audits/2026-08-29-p2-003r-d290-off-layer-vacate-refuted-owner-decision.md).

## 2026-08-29 - FBV2-P2-003Q: D-289 the rejected 003P WIP is retired with NO PROGRESS (independently verified byte-aggregate-equivalent to 003O, a lateral U18.7↔U18.8 swap), and the bounded U18.7/U18.8 co-closure lever (reservation ordering) is REFUTED on cheap non-vacuous evidence — reserving U18.8 first trades 1 casualty for 2 (U18.8 closes but U18.7 and U18.9 both open, −1 connection), because U18.8→R75.2 must escape NORTH into U18.7's single B lane with no alternative B via-site (a 3-into-one-corner placement-geometry mutual-exclusion, not an ordering defect); the terminal REF_POL R87.2 wall is characterized on the actual congested board as F.Cu routing capacity (N_POL 6.36 mm F.Cu saturates the R87.2→node corridor) with a named narrowest lawful lever (D-279-class N_POL F.Cu inner offload, not a DRU exception, no closure claimed); no source/copper/placement/rule change, D-275 and D-277..D-288 preserved

**A GOVERNED EVIDENCE / NO-PROGRESS MILESTONE.** The persistent CTO rejected the uncommitted 003P patch set (informal labels D-289/D-290/D-291 — never committed, now VOID). 003Q independently verified that rejection (003P's natural full run is byte-aggregate-equivalent to committed 003O: conn 67, skipped 99, ratsnest 708/−73, identical final DRC, identical terminal `REF_POL R87.2→(node) NO_PATH @ 0.150 mm`; the sense-pair-clearance change is a lateral U18.7↔U18.8 swap; the divider-tap-width change fires on other-branch copper / a true NO_PATH; the test-via change cured only a focused-vehicle artifact), cleanly retired it (5 tracked reverts + 6 untracked removals; tree clean at `bc1088d`), then continued with the next bounded CTO task. Task 2 (reserve U18.8 before U18.9, no clearance/geometry relaxation) is REFUTED on a cheap non-vacuous `AQROOT_LOCAL=D256` west-prefix screen: baseline (U18.9-first) conn 35 with U18.7✓/U18.9✓/U18.8-open; reorder (U18.8-first) conn 34 with U18.8✓ but U18.7 gate-rejected (0.25 mm < 0.30 mm D-269 clearance vs U18.8's north reservation) and U18.9 no-legal-escape — root cause is placement geometry (U18.8→R75.2 escapes NORTH into U18.7's only lane; no alternative B via-site), so ordering only selects the casualty. Task 3 characterized the terminal REF_POL R87.2→node wall on the actual congested 003O board (`w/refpol_wall_003q.py`): the node `{TP24.1,U19.2,R88.1}` is closed, R87.2 is isolated, and its F.Cu corridor is saturated by N_POL 6.36 mm + VREF_TOP 1.45 mm — an F.Cu routing-capacity wall, not a DRU rule; narrowest lawful lever is a D-279-class inner offload of the N_POL F.Cu run (D-279 today reverts only B.Cu detours), validated only on a full run. Committed D-289 supersedes the VOID informal 003P labels. NO source, copper, placement, or rule change; `.aqroot-progress.env` not edited; readiness ~77 %, routing 0 %, overall 74 % — all unchanged. Next: FBV2-P2-003R (off-layer vacate of U18.7 + reserve U18.8 first to co-close U18.7/U18.8/U18.9; extend the D-279 offload to the N_POL F.Cu run to open the REF_POL R87.2 corridor). Full analysis: [`audits/2026-08-29-p2-003q-d289-003p-rejection-and-u18-co-closure-refuted.md`](audits/2026-08-29-p2-003q-d289-003p-rejection-and-u18-co-closure-refuted.md).

## 2026-08-29 - FBV2-P2-003O: D-288 the D-275 south-bridge ENTRY-array two-layer tie is FIXED (rotation-aware in-pad POFV scan + a symmetric B.Cu tie-stub make the entry vias `via_dangling`-clean), proven by a non-vacuous regression (legacy off-pad array +4 dangling / fixed 0 dangling / no absorption) AND a natural-completion CTO full run (DRIVER_EXIT=0, no dangling cascade) - but the overall Phase-A run still FAILs on genuinely NEW downstream blockers (U18.8 BAT_PROTECTED_P escape NO_VIA_SITE + a terminal REF_POL/R87 F-corridor NO_PATH + BAT_RAW divider width vs BAT_MAIN); the bridge-code fix + regression are ACCEPTED/COMMITTED, no routing/overall progress, no readiness change, no promotion, D-275 and D-277..D-287 preserved

**A SUCCESSFUL BRIDGE-IMPLEMENTATION FIX IS DISTINCT FROM AN OVERALL PHASE-A PASS.** 003O closed the exact D-287 lever - the entry array that dangled on one layer - and the natural CTO full run proves it end-to-end (the D-287 `via_dangling` cascade is GONE, the south bridge now passes BOTH geometrically AND electrically, and the `BAT_PROTECTED_P` island closes R75.2 through seven pads). But the full run still FAILs, now on new, downstream, genuinely-different blockers the entry dangling had shadowed. No copper and no placement are promoted.

- **The fix (minimal, two parts, both in the bridge code).** (1) Root cause in `bridge_route_003c.scan_entry_sites`: it windowed on R75.2's UNROTATED `hx/hy` and sorted "south-first", so for the -90 deg-rotated R75 pad it scanned a tall-narrow box and actually picked the NORTHERNMOST sites - ~0.5-1.15 mm NORTH of the real B.Cu pad copper, over bare substrate (the D-287 dangle). New `_in_pad()` transforms each candidate into the pad's OWN rotated frame and requires the centre inside the pad rectangle inset by `IN_PAD_MARGIN=0.20 mm`; the scan walks the rotation-aware AABB and sorts CENTRE-OUT, so every entry via barrel genuinely overlaps R75.2's B.Cu pad (`point_free`/`hole_clear` unchanged). (2) `stage_bridge`/`bridge_early_003i.apply_early` now lay an explicit B.Cu tie-stub from each entry via to R75.2's pad centre (`qb.track(NET,'B',...,W_LAND)`) - the exact mirror of the exit array's `_lay_landing` stub - so each entry via is tied on TWO layers.

- **The D-288 regression is NON-VACUOUS (`screen_003n.py --bridge --validate`, exit 0).** NEGATIVE control reproduces the D-287 asymmetric array (4 vias at the MEASURED off-pad `LEGACY_ENTRY_SITES` + F.Cu bus, no B.Cu stub) and MUST dangle - measured **`via_dangling +4`** (KiCad's connectivity test genuinely catches the defect, so the fix cannot pass vacuously). POSITIVE control (the real fixed bridge) is CONNECTED, **`via_dangling == 0`, entry 4, exit 4, ywest 82.4, traverse 1.30 mm**. NO-ABSORPTION: the fixed bridge adds ZERO new hard-class DRC vs the identical no-bridge placed board. This replaces the D-287 dangling-control `--validate`.

- **The natural-completion CTO full run (`b1_r75rot`, `place_003l` + `AQROOT_BRIDGE_EARLY/SOUTH`, `DRIVER_EXIT=0`, secs 1776.5).** Evidence of record (pinned, committed): `checks/phaseA_003o_b1_r75rot_cto.json`; scratch log `w/log_003o_b1_r75rot_cto.txt` (gitignored). PHASE A **FAIL**; connections **67**, skipped-already-connected **99**, ratsnest **781 -> 708 (-73)**. The early south bridge now passes BOTH geometrically AND electrically - `land C36.1`, traverse **70.925 mm @ 1.30 mm**, **entry 4 @ y=67.95 GENUINELY INSIDE the rotated R75.2 pad** (bbox y in [67.35,68.58]), exit 4, disjoint `ywest 82.40`, `bridge_eco null` - and there is **NO `via_dangling` cascade** anywhere (the D-287 20-gate poisoning is gone; the fix holds at full-run scale). The `BAT_PROTECTED_P` island CLOSES **R75.2 through C36/C25/C58/D9/U11/U14/TP15**.

- **The NEW blockers (attributed, NOT absorbed).** (1) **`U18.8` remains OPEN** - its reservation was `GATE_REJECTED` on `clearance +1` (`rule 'BAT_MAIN routed clearance'`), then the main pass reports **`NO_VIA_SITE`** ("no via site of 0.65 mm reachable on B"; pass-2 "no 0.35 mm via site reachable on B") - so `BAT_PROTECTED_P` is NOT fully closed across all required pads (U18.8 is the one open trunk pad). (2) Terminal fail = **`REF_POL R87.2->(node)` NO_PATH - no F corridor at 0.150 mm** (also `R88.1->R87.2` NO_PATH). (3) **`BAT_RAW R89.1->(node)` NO_PATH at 0.600 mm** and **`R86.2`** walks the ladder 1.00->0.20 mm then `GATE_REJECTED` on **`track_width +4`** because four 0.20 mm BAT_RAW divider taps breach the `BAT_MAIN minimum width` 0.60 mm rule (a rule-conformance reject; the final board carries no such delta).

- **Final DRC (re-verified with `kicad-cli pcb drc --severity-all` on the final scratch board).** `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}` - reproduces the JSON exactly. **The single `track_width` item, truthfully:** a `BAT_PROTECTED_P` track on B.Cu, length **2.4749 mm @ (65.5, 76.05), actual 0.2000 mm**, violating rule **`BAT_PROTECTED_P high-current trunk width - D-249` (min 1.2000 mm)** - one thin 0.20 mm SENSE/Kelvin sub-branch of the high-current trunk net (a bounded sense tap), a genuine-but-benign copper item SURFACED not absorbed (same class as the lone `track_width +1` D-286 surfaced), NOT a fabrication blocker. Bounded stub exceptions present (`BAT_RAW_DIVIDER_TAP_1/2/3` 0.2 mm D-269, `BAT_STUB_3` BAT_PROTECTED_P 1.0 mm, `BAT_STUB_4` BAT_SENSE 0.2 mm).

- **Why NOT an owner decision.** The new blockers are BOUNDED technical work, not a placement wall and not un-fixable without relaxing a floor or moving a frozen part; direction-2 (broad LTC4368 refloorplan / corridor widening, OWNER/mechanical) is NOT the sole remaining option; `/home/aqroot8/.aqroot-autopilot-stop` stays ABSENT; open owner decisions remain NONE.

- **Cleanliness.** Source changes only in the bridge code / regression: `bridge_route_003c.py` (rotation-aware in-pad `scan_entry_sites` + entry B.Cu tie-stub), `bridge_early_003i.py` (entry B.Cu tie-stub in `apply_early`), `screen_003n.py` (D-288 `entry_tie_regression`). No driver/router/DRU/footprint/netclass/rule mutated; no rule/floor relaxed (0.200 mm clearance + 0.25 mm hole-to-hole + >=1.20 mm BPP trunk + 0.60 mm BAT_MAIN ENFORCED); no DRC absorbed (U18.8 `NO_VIA_SITE`, the REF_POL NO_PATH, and the BAT_RAW `track_width +4` are the FAIL/reject reasons). `c3_00` not promoted; `place_003l` (D-285) preserved and clean; optional `BAT_SENSE TP20.1` separate; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged. Authoritative PCB UNCHANGED (six layers, 0 tracks, 0 vias, placement at home); `phaseA_journal.json` restored to HEAD. Regressions GREEN: `screen_003n.py --bridge --validate` (negative +4 / positive 0 / no-absorption); the focused D-288 regression and router regression G1-G12 passed in the prior work. **NO PROGRESS EARNED: PCB routing stays 0 %, overall stays 74 %, readiness ~77 %.** Full analysis: [`audits/2026-08-29-p2-003o-d288-entry-tie-fix-and-full-run.md`](audits/2026-08-29-p2-003o-d288-entry-tie-fix-and-full-run.md). **Next: FBV2-P2-003P - (1) close U18.8's BAT_PROTECTED_P escape (a legal B-layer via site + reservation past the BAT_MAIN routed-clearance reject) to fully close the trunk; (2) investigate/close the terminal REF_POL R87.2 / R88.1->R87.2 F-corridor NO_PATH at 0.150 mm; (3) attribute the BAT_RAW R89.1/R86.2 divider-tap width vs the BAT_MAIN 0.60 mm rule - all with NO floor/rule relaxation and NO frozen-part move.**

## 2026-08-29 - FBV2-P2-003N: D-287 the full bounded direction-1 placement screen is EXHAUSTED (27/27) - only three candidates pass the D-286 zero-copper hard gates, and a cheap CTO-authorized bridge-connectivity probe REFUTES all three at the SAME genuine electrical fault: the D-275 south-bridge ENTRY array (R75.2 POFV) is bussed on F.Cu with NO symmetric B.Cu tie-stub, so its vias dangle on one layer regardless of placement - a BRIDGE-IMPLEMENTATION defect independent of placement (a narrower CTO lever), NOT a placement wall; direction-2 is NOT yet the sole option, so this is a CTO ENGINEERING FAIL, not an OWNER decision; no promotion, D-275 and D-277..D-286 preserved

**THE PLACEMENT SEARCH IS EXHAUSTED, BUT THE WALL IS IN THE BRIDGE CODE, NOT THE PLACEMENT.** 003N screened the complete bounded direction-1 LTC-block placement space on real full-placement D-286 DRC + the real router escape solver, then used a cheap CTO-authorized bridge-connectivity probe to refute the three survivors WITHOUT spending an expensive full run on each - decisively, at one reproducible electrical fault.

- **The 27-candidate screen (`checks/screen_003n.py`, the deliverable).** For every candidate the screen builds a REAL scratch board at the exact D-286 pre-copper boundary (002F ECO + `place_003l` + candidate -> connectivity -> zone fill -> save) and runs the real `kicad-cli pcb drc --severity-all` + the real `qb.escape` solver, rejecting any candidate that vs the `place_003l`-only CLEAN reference adds a different-net pad short / sub-0.200 mm clearance / hole breach / courtyard overlap, or leaves a required U18 pin un-escapable. The complete space is 27 - `b1`(6), `c3`(4), `cand_00..11`(12), `c2`(5). **24 REJECT at bare placement; only `b1_r75rot`, `b1_r75rotN`, `b1_q3rot` pass every hard gate + all U18 escapes.** `screen_003n.py --validate` (screen regression) PASS: `c3_00` REJECT `shorting_items +3`, `place_003l` reference clean.

- **All three survivors FAIL bridge integration at the same fault.** `b1_r75rot` was taken into a parent-supervised full run: the early south bridge reported a GEOMETRIC success (`land=C36.1 traverse=72.786 mm w=1.40 entry=4 exit=4 ywest=82.40`, disjoint) but every subsequent gate then rejected on brand-new `via_dangling +4` ("connected on only one layer") across 20 unrelated post-bridge gates until the persistent CTO stopped the poisoned cascade (`DRIVER_EXIT=143`). A cheap **bridge-connectivity probe** (added to `screen_003n.py --bridge`) reproduces the exact early bridge in ISOLATION on each survivor's placed board, fills, saves and gates KiCad `via_dangling` as the authoritative >=2-layer test; validated against the b1_r75rot control (reproduces +4). Result - `b1_r75rot` dangling **4**; `b1_r75rotN` dangling **4**; `b1_q3rot` dangling **2** AND not-disjoint (`ywest 61.04 < 75`). **0/3 truly connected.** The cheap probe evaluated both remaining survivors decisively; no expensive full run was warranted (each reproduces the identical dangling cascade).

- **Root cause - an asymmetric, placement-independent bridge defect.** Every dangling via is the ENTRY array on R75.2. Direct geometry (probe scratch board): R75.2's B.Cu pad spans y in [67.35, 68.58], but the entry vias land at y~66.19-66.81 - ~0.5-1.15 mm NORTH of the pad, over bare substrate - so on F.Cu they are tied by the `apply_early` bus while on B.Cu they touch nothing -> one-layer -> `via_dangling`. The EXIT array does NOT dangle because `bridge_early_003i._lay_landing` lays an explicit B.Cu tie-stub from each exit via to its landing pad; the ENTRY array has NO such symmetric B.Cu tie-stub (it relies on POFV vias overlapping R75.2's pad, which does not hold). The defect is structural to `bridge_early_003i.apply_early` / `bridge_route_003c.scan_entry_sites`, present in every placement (4 vs 2 dangling only reflects how many entry sites clip the pad). This re-qualifies the earlier "the D-275 bridge PASSED" claims (003K/L/M) as GEOMETRIC passes never electrically gated (masked by the c3_00 placement short); 003N is the first electrical gate of the bridge end-to-end, and it fails - consistent with the D-286 binding constraint to surface, never absorb.

- **Why NOT an owner decision.** The direction-1 candidate space is EXHAUSTED, but the three survivors fail on a bridge-connectivity IMPLEMENTATION defect independent of placement - the 003N charter's named "narrower CTO technical lever" - not on a placement wall. Fixing it moves no LTC-block footprint. So direction-2 (broad LTC4368 refloorplan / corridor widening, OWNER/mechanical) is NOT yet the sole remaining option; `/home/aqroot8/.aqroot-autopilot-stop` stays ABSENT; open owner decisions remain NONE.

- **Cleanliness.** Only new file `checks/screen_003n.py` (the D-286 screen + bridge-connectivity probe/regression); no driver/router/DRU/footprint/netclass/rule source mutated; no DRC absorbed (a `via_dangling` item IS the FAIL reason); no netclass/width/topology/net/footprint/value/polarity/six-layer/GND/safety change; `c3_00` not promoted; `place_003l` (D-285) preserved and clean; optional `BAT_SENSE TP20.1` separate; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged. Authoritative PCB UNCHANGED (six layers, 0 tracks, 0 vias, placement at home); `phaseA_journal.json` restored to HEAD (driver never authoritatively invoked). Regressions GREEN: `screen_003n.py --validate` and `screen_003n.py --bridge --validate`. **NO PROGRESS EARNED: PCB routing stays 0 %, overall stays 74 %.** Full analysis: [`audits/2026-08-29-p2-003n-d287-bridge-entry-array-dangling.md`](audits/2026-08-29-p2-003n-d287-bridge-entry-array-dangling.md). **Next: FBV2-P2-003O - fix the D-275 south-bridge ENTRY-array two-layer tie (add an explicit B.Cu tie-stub from each entry via to R75.2's pad centre and/or constrain `scan_entry_sites` to in-pad sites) so the entry vias are `via_dangling`-clean, symmetric to the proven exit array, with no rule/floor/topology/footprint change and no absorption; verify with `screen_003n.py --bridge` on `b1_r75rot` (via_dangling 0, entry >=3, exit >=3, disjoint ywest > 75, >=1.20 mm) then take it to a parent-supervised full Phase-A run and close BAT_PROTECTED_P.**

## 2026-08-29 - FBV2-P2-003M: D-286 the gate DRC/ratsnest baseline was measured BEFORE the candidate placement (latent since 002L), so c3_00's own placement DRC poisoned every gate; the harness now measures the baseline on the ACTUAL complete pre-copper placement, and with that correction the definitive full run SURFACES that candidate c3_00 is electrically invalid - U18 (LTC4368) collides with R83/R80 (three genuine different-net pad shorts + two sub-0.200 mm clearances, ZERO copper) and the LTC sense pins are un-escapable; harness fix + G12 regression COMMITTED, c3_00 recipe MEASURED FAIL, no authoritative promotion, D-275 and D-277..D-285 preserved

**A HARNESS-CORRECTNESS FIX THAT STOPS FALSE GATE POISONING AND, IN DOING SO, REVEALS A REAL PLACEMENT SHORT THE OLD ORDERING WAS HIDING.** The first parent-supervised 003M attempt was invalidated by a `GATE_REJECTED` cascade (`DRIVER_EXIT=143`, CTO-stopped) carrying a FIXED placement DRC delta across unrelated nets. Root-caused to a baseline measured one step too early; corrected; re-run to a defensible verdict.

- **The defect (D-286).** `route_battery_block.py` computed the gate baseline `base = RU.drc(pcb)` / `base_rn = RU.ratsnest(pcb)` right after the 002F ECO (+`AQROOT_ECO_EXTRA`) but BEFORE `AQROOT_PLACE_JSON` moved the candidate footprints a few lines below. So a candidate placement's OWN placement-derived DRC (`courtyards_overlap`/`solder_mask_bridge`/`shorting_items`/`clearance`) was never in the comparison baseline, and every per-connection gate `after − base` read those placement items as brand-new copper violations, rejecting unrelated nets (Q2_CS/Q3_CS/BAT_SENSE/LTC_SHDN/BAT_PROTECTED_P) both before and after the bridge. Latent since 002L; the dense c3_00 placement made it decisive. The bridge itself PASSED in that attempt (`land C36.1 traverse 72.786 mm w=1.40 entry 4 exit 4`), confirming the fault was in the gate baseline, not the bridge.

- **The fix (minimal, default-preserving).** The baseline is relocated to AFTER full candidate placement application + connectivity rebuild + zone fill + board save + `DRU.write` + fingerprint assertion, BEFORE any QBoard copper - so a gate delta is measured strictly against the real routed starting geometry. When no `AQROOT_PLACE_JSON` is supplied the on-disk board at the new point is byte-identical to the old point (placement block skipped, fingerprint block read-only), so default behaviour is unchanged. `DRU.write` writes a separate `.kicad_dru` sidecar, so the placement `Save` never clobbers the rules.

- **Do NOT blindly absorb - attribute.** Each corrected-baseline item was measured on independent zero-copper boards (`w/baseline_003m_audit.py`, `w/attrib_003m.py`): AUTHORITATIVE home `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1}`; **002F-ECO-only = identical (clean)**; **`place_003l` alone = identical (CLEAN - D-285 vindicated, introduces nothing)**; **`c3_00` alone = +clearance:2, +courtyards_overlap:3, +shorting_items:3, +silk_over_copper:6, solder_mask_bridge 1→4 (the SOLE cause).** c3_00 (`002Z-c3_e10n_r79`, prefilter rank 1) moves U18→(4.0,72.9,90°) onto R83/R80 (unmoved), producing THREE genuine different-net pad shorts - `R83.1[BAT_PROT_SHDN_CTL]` on `U18.3[LTC_OV]` and `U18.2[LTC_UV]`, `R80.1[BAT_RAW]` on `U18.10[LTC_GATE]` - plus GND 0.100 mm and Default **0.0088 mm** sub-floor gaps, all with ZERO routed copper. No route can remove a pad-on-pad short. The router's own escape solver names the identical culprits (`U18.10 blocked by R80.1 ×71`, `U18.3 blocked by R83.1 ×68`, `U18.2 blocked by R83.1 ×71`).

- **The definitive full run (corrected harness, exact D-285 recipe, `DRIVER_EXIT=0` natural completion, scratch `FIX003M`).** PHASE A **FAIL** - `BAT_PROT_SHDN_CTL R83.1→(node) NO_NODE`; connections **64**, skipped-already-connected 89, ratsnest **713 (−68)**. The early south bridge PASSED at full width - `land C36.1`, traverse **72.994 mm @ w=1.50 mm**, entry 4 / exit 4, disjoint (`ywest 82.4`), `bridge_eco null` - the run does NOT fail on the bridge; it fails on the c3_00-collided LTC4368 control cluster (`LTC_GATE`/`LTC_OV`/`LTC_UV`/`BAT_PROT_SHDN_CTL`/`FAULT_N`/`BAT_SENSE`). Gate discipline held: the ONLY class increased vs the corrected baseline is `track_width +1` (one 0.2 mm `BAT_PROTECTED_P` bounded-stub, genuine copper, SURFACED not absorbed); `shorting_items:3` and `clearance:2` sit identically in baseline AND final. Two independent gates - the router's connectivity result and the placement DRC audit - agree c3_00 is invalid.

- **Regression G12 (router_regression, G1-G11 unchanged and still PASS).** On a real scratch board it induces a placement DRC delta, proves the OLD pre-placement order FALSELY flags it, the NEW post-placement order yields ZERO spurious delta, a post-baseline copper violation is STILL surfaced, and the driver source order is asserted so the old ordering fails the test if it returns. Preflight all PASS: `router_regression` G1-G12; `bridge_probe_003c/003d/003i/003j/003k/003l`; `u19_escape_probe_003e/003f/003g/003h`.

- **Cleanliness.** Only source changes: the baseline relocation in `route_battery_block.py` and additive G12 in `router_regression.py`. No netclass/width/topology/net/footprint/value/polarity/six-layer/GND/safety change; no DRC absorbed (a genuine placement short IS the FAIL reason); `c3_00` NOT promoted; `place_003l` (D-285) preserved and clean; optional `BAT_SENSE TP20.1` separate; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged. Authoritative PCB UNCHANGED (six layers, 0 tracks, 0 vias, C36/U18 at home poses); `phaseA_journal.json` restored to HEAD after the FAIL run. **This is an ORDINARY ENGINEERING FAIL (CTO scope), NOT an OWNER decision** - other LTC-block placement candidates (`c3_01/02/03`, `cand_00..11`, the c2 family) exist and are unscreened; direction-2 (broad LTC4368 refloorplan) is NOT yet the sole option. **NO PROGRESS EARNED: PCB routing stays 0 %, overall stays 74 %.** Full analysis: [`audits/2026-08-29-p2-003m-d286-baseline-order-and-c3_00-placement-shorts.md`](audits/2026-08-29-p2-003m-d286-baseline-order-and-c3_00-placement-shorts.md). **Next: FBV2-P2-003N - re-screen the LTC-block placement candidates with the corrected D-286 post-placement baseline DRC (reject any bare-placement short or un-escapable LTC sense pin), then integrate the first genuinely short-free, routable candidate with place_003l + the proven south bridge on a parent-supervised full run.**

## 2026-08-28 - FBV2-P2-003L: D-284 (OWNER) + D-285 the minimal landing-opening PLACEMENT ECO OPENS a legal southern BAT_PROTECTED_P landing - C36 rotated to vertical (270) + shifted south and the +3V3 decoupler C5 relocated west; the proven D-275 south bridge now lays entry 4 / 1.40 mm F.Cu / exit 4 with ZERO east-landing DRC and nothing new added; governing landing clearance 0.2941 mm (47% over the 0.200 mm floor); PASS CANDIDATE for supervised Phase-A integration; no authoritative promotion; D-275 and D-277..D-283 preserved

**THE FIRST POSITIVE RESULT IN THE BAT_PROTECTED_P ARC: the landing OPENS, measured and reproducible.** D-284 is the OWNER decision (Alpha, ratifying the CTO call): open a legal southern landing by a **bounded placement spread of the C36/C25/U11/BQ25185_SYS neighbourhood** (landing-opening direction 1), not corridor widening, not a broad refloorplan. D-285 (FBV2-P2-003L) is the engineering result that delivers and proves it.

- **The two blockers 003K measured, and why the fix is forced.** The forced-south bridge lands on C36.1 and hit TWO independent violations: (1) GND 0.0726 mm to C36's OWN GND pad (1.55 mm east, same footprint) - INVARIANT under any C36 translation, so fixable ONLY by a C36 ROTATION; (2) BAT_MAIN 0.0864 mm to R68's fixed F.Cu BQ25185_SYS pad (R68 is 0R DNP but KiCad-connected: 16-pad net). A vertical C36 is 3.05 mm tall, so it cannot sit south enough to clear R68 without colliding C5's courtyard.

- **The minimal ECO (`place_003l`, two footprints, nothing else).** `C36` -> (63.75, 75.10, 270 deg): the rotation moves C36's GND pad 1.55 mm SOUTH of the north-poking exit array (blocker 1: 0.0726 -> 0.4750 mm); the ~1.35 mm south shift clears R68 by distance (blocker 2: 0.0864 -> 0.2941 mm). `C5` (100 nF +3V3/GND decoupler, the SOLE courtyard obstruction to the vertical C36) -> (61.95, 75.15, 90 deg). R68 is deliberately NOT moved (real 16-pad net, no nearby legal home); C5 was chosen for its plane-net routing latitude. Both moves are STRICTLY NECESSARY and inside the approved neighbourhood (C5 is 1.9 mm from C36), recorded not taken silently.

- **The measurement (`bridge_probe_003l`, PASS).** On the reconstructed sparse 002F board + the D-275 south bridge: LANE lays (land C36.1, traverse 1.40 mm F.Cu, entry 4, exit 4); DISJOINT (ywest 82.40 mm > 74.7); the LANDING OPENS - ZERO east-landing clearance violations, and the two named blockers now clear (C36.2 GND 0.4750, R68.1 BAT_MAIN 0.2941 mm); the DRC delta vs the 003K board is EXACTLY the two landing clearances removed - clearance 4 -> 2, the two survivors are the pre-existing WESTERN LTC-block issues (R83/U18 GND 0.100, R80/U18 LTC_GATE 0.0088), courtyards_overlap stays 3, every other class identical. NO new genuine DRC class or item, and NONE absorbed. Governing achieved landing clearance 0.2941 mm, 47% over the 0.200 mm floor; the bridge holds 1.40 mm (>= the 1.20 mm floor).

- **Why a CANDIDATE, not a promotion.** The proof is a REAL board + REAL kicad-cli DRC (not an analytical proxy) but proves the LANDING, not full-board connectivity - that needs the parent-supervised full Phase-A run, which task discipline forbids starting unsupervised. So the ECO is integrated DEFAULT-INERT via the existing 002J `AQROOT_ECO_EXTRA` override (`place_003l.json`) - no driver edit - and the authoritative PCB is left untouched (0 tracks / 0 vias, C36 at home pose).

- **The supervised follow-on (defined, NOT started) - FBV2-P2-003M.** The pinned D-271 recipe + `AQROOT_BRIDGE_EARLY=1 AQROOT_BRIDGE_SOUTH=1` + `AQROOT_ECO_EXTRA=hardware/beta-v2/checks/place_003l.json`, parent-supervised, to route all nets around the reserved bridge without reintroducing the 003I corridor failures and close BAT_PROTECTED_P with no new DRC. Only then does authoritative promotion and a routing-% award apply.

- **Cleanliness.** Three NEW additive files (`place_003l.py`, `place_003l.json`, `bridge_probe_003l.py`); no existing code modified, so every default path is byte-identical. `bridge_probe_003l` PASS; `bridge_probe_003c/003d/003i/003j/003k`, `router_regression` G1-G11, `u19_escape_probe_003e/003f/003g/003h` all PASS. Only C36/C5 moved (no frozen part - D9/U18/R75-R83/Q3/FETs/C58/U19/D10/R68/U11 held); no topology/net/footprint/polarity/value/layer-stack/GND/netclass/width/clearance/hole-floor change; no safety weakening; c3_00 not promoted; optional BAT_SENSE TP20.1 kept separate; JLCPCB_READINESS not touched. D-275 and D-277..D-283 preserved. **NO PROGRESS EARNED: PCB routing stays 0 %, overall stays 74 %** - the blocker is resolved at candidate level, awaiting the supervised gate. Full analysis: [`audits/2026-08-28-p2-003l-d285-landing-opening-placement.md`](audits/2026-08-28-p2-003l-d285-landing-opening-placement.md).

## 2026-08-28 - FBV2-P2-003K: D-283 the DISJOINT-SUB-BOX southern BAT_PROTECTED_P bridge (candidate c) LAYS its lane but has NO LEGAL LANDING - the only forced-south target-island pad (the far-east node cap C36.1) is boxed by GND and BAT_MAIN, so the exit array lands 0.0726 mm from GND and 0.0864 mm from BAT_MAIN; the ungated early bridge then poisons every subsequent gate and the full run cascades (140 rejections across 26 nets); candidate (c) is EXHAUSTED and the remaining lever is the OWNER/mechanical placement-spread fallback; no authoritative promotion; D-275 and D-277..D-282 preserved

**A MEASURED FAIL that exhausts the last route-scope candidate for closing BAT_PROTECTED_P, and localises the block to the LANDING (not the lane).** 003J (D-282) localised the one spare >=1.20 mm F.Cu lane to a SOUTHERN band DISJOINT from the tap cluster (taps y<74.7, lane y>75) and deferred the disjoint-sub-box candidate (c) to a supervised full run. 003K implements the minimal env-gated candidate and measures it.

- **The implementation (minimal, default-inert).** `AQROOT_BRIDGE_SOUTH` (`route_battery_block.py`, implies the `AQROOT_BRIDGE_EARLY` 003I stage so the bridge is laid exactly once, at the stage-8 boundary; no effect unless set). `bridge_early_003i.apply_early(..., south=True)` lays the SAME proven D-275 mechanism (cardinality-1 `BAT_PROT_SHDN_CTL` vacate, 4x R75.2 entry array, >=1.20 mm F.Cu traverse rule, 4x exit array, >=3 floor, single-sourced VERBATIM from `bridge_route_003c`) with two south-only additions: a TEMPORARY net-foreign obstacle wall over the corridor-north box (x 4.6-30, y 55-74.7) that forces the western leg BELOW the tap band - removed with the injected via phantoms, so it shapes ONLY the bridge's own search and never obstructs a real net - and `LAND_REFS_SOUTH = [C36.1, U11.2, C25.1]`, the far-east node caps (the forced-south leg cannot return to the corridor pads). `south=False` reproduces the 003I corridor stage byte-for-byte.

- **The DISJOINT LANE is viable (necessary precondition holds).** On the reconstructed sparse placed board the south bridge LAYS: entry 4, >=1.20 mm F.Cu traverse, exit 3, land `C36.1`, and the western leg dips to `ywest = 81.85 mm` - well south of the taps at y<74.7. This is the half 003J could not prove on the already-dense board (there the lane capped at <=1.30 mm); the sparse-window reservation does open it.

- **The LANDING is NOT viable (decisive FAIL).** `C36.1` is the ONLY target-island BPP pad the forced-south leg can reach - no target-island pad exists between `D9.1` (x=11) and `C25/C36` (x=62), and the OPEN node COPPER D-275 landed on at (40.67,70.71) does not exist at the early reservation point. Its neighbourhood cannot clear a >=0.200 mm exit array: DRC on the laid board shows the exit copper at 0.0726 mm from `C36`'s own GND pad (64.525,73.750) and 0.0864 mm from `R6`/`R68`'s BAT_MAIN (`BQ25185_SYS`) pad (63.459,71.606) - both < the 0.200 mm floor, the exact 003I clearance class (identical GND 0.0726 mm). The offending neighbours are FIXED pads, so the FAIL reproduces on the sparse board without the full run.

- **The full run (parent-supervised, measured).** Recipe c3_00 + SIXLAYER + D277..D280 + `AQROOT_BRIDGE_EARLY=1` + `AQROOT_BRIDGE_SOUTH=1`, scratch `FIX003K`, placement fingerprint identical to the 003H reference. The early stage laid the bridge - `EARLY BRIDGE SOUTH OK land=C36.1 traverse=70.377mm w=1.20 entry=4 exit=3 ywest=81.85` - then, because the early stage lays the bridge UNGATED, the fixed landing violation (GND 0.0726 / BAT_MAIN 0.0864) was read as `new DRC {clearance:2}` by EVERY subsequent per-connection gate and rejected it: **140 gate rejections across 26 distinct nets** (`BAT_RAW`, `LTC_GATE`, `LTC_GATE_RC`, `REF_POL`, `N_BATDIV`, `REC_*`, ...). The parent STOPPED the run once the cascade was decisive (as the 003I parent did); NO `phaseA_003k_fix.json` was written - no partial board masquerades as a result. The two clearance violations are GENUINE and are NOT absorbed into any baseline.

- **Conclusion.** Candidate (c) is EXHAUSTED at the LANDING, not the lane. With (b) refuted (D-282), (d) the 003I FAIL (D-281) and (a) an envelope change (OWNER), the only remaining lever is the FALLBACK - a placement spread of the LTC4368 block (OWNER/mechanical), either to OPEN the landing (spread `C36/C25/U11` / the `BQ25185_SYS` neighbourhood) or to WIDEN the corridor - NOT attempted here.

- **Suites (all PASS):** `bridge_probe_003k` (NEW, clauses A/B/C/D/E), `bridge_probe_003i` (D-281), `bridge_probe_003j` (D-282), `bridge_probe_003c`/`bridge_probe_003d` (D-275/D-276 held fixed), `router_regression` G1-G11 (D-280 off), `u19_escape_probe_003e/003f/003g/003h` (D-277..D-280). Authoritative PCB UNCHANGED (0 tracks / 0 vias); `phaseA_journal.json` restored to HEAD; scratch `FIX003K` gitignored. Nothing moved, nothing relaxed; D-275/D-277..D-282 held byte-fixed; the optional `BAT_SENSE TP20.1` (TEST) point treated separately; no authoritative promotion. **NO PROGRESS EARNED: PCB routing stays 0 %, overall stays 74 %.** Full analysis: `audits/2026-08-28-p2-003k-d283-south-disjoint-bridge.md`. **Next: FBV2-P2-003L (OWNER/mechanical) - a placement spread of the LTC4368 block.**

## 2026-08-28 - FBV2-P2-003J: D-282 the shared western-corridor BAT_PROTECTED_P bridge is a TOPOLOGY/CAPACITY wall, and 003J LOCALISES it - the 003I-proposed route-only fix (relocate the LTC_GATE/BAT_RAW corridor TAP via drops out of the box, candidate b) is MEASURED INSUFFICIENT, because the wall is the WHOLE western through-via + control-copper field, not the taps; the only >=1.20 mm F.Cu path that exists is a ~48 mm SOUTHERN cross-board detour capped at <=1.30 mm, not the D-275 >=1.50 mm corridor bridge; no authoritative promotion; D-275 and D-277..D-280 preserved; the disjoint-sub-box / co-scheduled candidate needs a parent-supervised full run

**A BOUNDED CAPACITY MEASUREMENT that refutes the leading fix and re-localises the root cause. 003I named four candidate directions for the shared corridor; 003J measures the cheapest (relocate the corridor tap via drops) and finds it INSUFFICIENT - the wall is the whole ~50-via western through-via + control-copper field, not the LTC_GATE/BAT_RAW taps. No route-only via relocation yields a viable >=1.20 mm F.Cu western-corridor bridge; the one spare lane is a long southern cross-board detour, not the bridge. No full run was launched; the decisive disjoint-sub-box candidate is handed to the CTO for a supervised run.** All work is in-memory on a scratch COPY of the committed dense 003H board (`w/FIX003H3`, bridge OFF, the clean 71-connection routed end-state); nothing on disk is mutated, the driver is never invoked, `phaseA_journal.json` is untouched.

- **The method (`bridge_probe_003j`, NEW, cheap, read-only):** copy the dense board, reconstruct the exact D-275 mechanism on it - `BR.vacate` (cardinality-1 `BAT_PROT_SHDN_CTL` -> In3, 9 F.Cu tracks moved) + `BR.scan_entry_sites` (4x 0.80/0.40 POFV entry array on R75.2) - build ONE QBoard, then run the bridge's own high-current traverse rule (>=W F.Cu, D-269 0.30 mm trunk-to-via clearance) via-AWARE against candidate landings with an arbitrary SUBSET of the board's 56 through-vias modelled as obstacles. All primitives/constants single-sourced VERBATIM from `bridge_route_003c`. Landings: the near west-cluster pad `D9.1` (11.35,72.5) and the far `NODE_AIM` (42.4,76.4) -> the node's 1.00 mm B.Cu trunk at (40.67,70.71).
- **(A) BASELINE (confirms D-281):** via-AWARE, all 56 vias, D9.1 near landing, 1.20 mm -> **NO_PATH**. The bridge does not fit end-of-run.
- **(B) CANDIDATE (b) REFUTED - the decisive new result:** removing the 9 corridor `LTC_GATE`/`BAT_RAW` TAP vias `(5.75,70.05) (5.85,71.65) (7.05,66.0) (7.20,71.90) (7.25,74.45) (7.40,67.80) (7.75,72.45) (8.00,74.70) (8.05,67.80)` from the obstacle model (simulating a route-target/staging relocation OUT of the box) does NOT reopen the via-AWARE >=1.20 mm traverse - **NO_PATH** to the near D9.1 landing AND to the far node. The remaining ~47 control-field through-vias (`LTC_SHDN`/`LTC_OV`/`LTC_UV`/`N_POL`/`REF_POL`/`FAULT_N`/`BAT_SENSE`, each a THROUGH-via barrel across all layers at the D-269 0.30 mm clearance) still wall the F.Cu traverse. **The taps are not the lever; the whole western through-via field is.**
- **(C) REGION SATURATION + the only path is a DETOUR:** even COPPER-ONLY (no via clearance at all), there is **NO_PATH at 1.50 mm** (the D-275 target) to any landing and **NO_PATH at 1.20 mm to the near D9.1 landing**; the single copper-only >=1.20 mm path runs to the far node and is a **47.5 mm SOUTHERN cross-board detour, path max-y 78.8 mm** (>> the corridor y<75), capping at <=1.30 mm (NO_PATH at 1.40/1.50 mm; also NO_PATH with the 9 taps ALSO removed). This is the same 48.9 mm/1.30 mm path `bridge_probe_003i` clause B reached, now characterised precisely: NOT the D-275 >=1.50 mm western-corridor bridge but a long, low-margin cross-board lane that would multiply the trunk resistance (B-34).
- **The conclusion (engineering, CTO scope, NOT an OWNER decision):** the corridor cannot host both a viable bridge and the western routing by any END-OF-RUN or via-RELOCATION means. Candidate (b) is refuted; candidate (d) [early/reserved bridge] is the 003I FAIL; candidate (a) [widen] needs board space / an envelope change (OWNER). The one remaining ROUTE-scope direction is **candidate (c)** - a DISJOINT bridge sub-box reserved in the sparse window with the whole western block forced into the complement - which changes CAPACITY (a co-scheduled joint reservation), cannot be proven by a bounded probe, and needs a parent-supervised full run. **No OWNER decision is forced yet.**

**No false promotion.** 003J ran no full route and promoted nothing; no `phaseA_003j_fix.json` claims a clean/absorbed end-state; the authoritative PCB is 0 tracks / 0 vias. **No driver change was committed** - candidate (b) is refuted (not implemented) and the candidate (c) reservation machinery is the next task (committing a large inert unproven reservation now would add risk with no measured backing). **SUITES ALL PASS:** `bridge_probe_003j` (NEW, the standing measured-capacity record, clauses A/B/C/D/E), `bridge_probe_003i` (D-281 record intact), `router_regression` G1-G11 (D-280 off), `bridge_probe_003c`/`bridge_probe_003d` (003C/D-275 held FIXED), `u19_escape_probe_003e/003f/003g/003h`. Committed artifacts: `bridge_probe_003j.py`, this audit, the D-282 CTO row, this CHANGELOG entry, the PROGRESS entry. **Nothing moved and nothing relaxed:** D9, U18, R75-R83, Q3, shunt, FETs, C58, U19, D10 and the whole R84-R96/Q5-Q9 field frozen; `c3_00` NOT promoted; D-249..D-281 (incl. **D-275/D-277/D-278/D-279/D-280/D-281**) untouched; the proven 003C bridge geometry held fixed; the 0.200 mm clearance and 0.25 mm hole-to-hole floors ENFORCED not relaxed; no safety weakening; no topology/net/footprint/polarity change; no six-layer/GND change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**). Phase A NOT completed (the D-275 BPP bridge is still not integrated). **`/home/aqroot8/.aqroot-progress.env` untouched - a measured FAIL earns no readiness. Next: FBV2-P2-003K - implement the minimal env-gated co-scheduled DISJOINT-SUB-BOX bridge reservation (reserve a >=1.50 mm F.Cu bridge lane in the southern band disjoint from the tap cluster, force the western LTC block into the complement) and MEASURE on a PARENT-SUPERVISED full run (~35-40 min) whether BPP closes without reintroducing the 003I GND/BAT_MAIN/BAT_RAW failures; if the southern reservation cannot hold >=1.20 mm or the western block cannot fit the complement, candidate (c) is exhausted and the fallback is a placement spread of the LTC4368 block (OWNER/mechanical).** Full analysis: [`audits/2026-08-28-p2-003j-d282-corridor-capacity.md`](audits/2026-08-28-p2-003j-d282-corridor-capacity.md).

## 2026-08-28 - FBV2-P2-003I: D-281 the route-order EARLY landing of the proven D-275 bridge is a MEASURED, REPRODUCIBLE FAIL - the bridge and the current-carrying corridor users (LTC_GATE/BAT_RAW tap, the GND pour and BAT_MAIN) CONTEND for one ~9 mm western corridor, so re-timing only changes WHICH high-current user fails, not WHETHER one fails; no authoritative promotion; D-275 and D-277..D-280 preserved; the topology/capacity fix is deferred to 003J

**A MEASURED FAIL, honestly closed. The obvious re-timing of the proven D-275 bridge - lay it EARLY, while the western corridor is still sparse, and let later routing route around it - was measured on a full supervised run and DOES NOT WORK, for a structural reason: the corridor lacks the CAPACITY for both the bridge and the taps, and a re-ordering cannot create room the geometry does not have.** 003D (D-276) integrated the exact D-275 mechanism as an END-OF-RUN stage and measured it to ABORT; 003I's preflight isolated the cause to western via-density (15 corridor vias vs 11 on the proven-sparse c3 board). 003I then measured the re-timing fix.

- **The mechanism (env-gated `AQROOT_BRIDGE_EARLY`, off by default):** the driver lays the EXACT D-275 bridge - the cardinality-1 `BAT_PROT_SHDN_CTL` vacate, the 4x 0.80/0.40 entry array on `R75.2` (POFV), the >=1.20 mm F.Cu traverse, the 4x exit array, all single-sourced VERBATIM from `bridge_route_003c` - at the first stage-8 queue item, in the proven-sparse window (after the D-266 Kelvin reservation + U18 field claim their sites, before the `LTC_GATE` / `BAT_RAW` taps inject the corridor-choking vias), then restores the driver's via-blind obstacle model so later nets route around the real bridge copper.
- **It LAYS (necessary):** the parent-supervised full run (recipe `c3_00` + SIXLAYER + D277..D280 + `AQROOT_BRIDGE_EARLY=1`) laid it - `EARLY BRIDGE OK land=C58.1 traverse=8.920mm w=1.50 entry=4 exit=4`. `bridge_probe_003i` clause E independently lays it on a reconstructed sparse placed board (entry 4, traverse 1.50 mm, exit 4, no new DRC on the sparse board).
- **But it is NOT sufficient - the MEASURED downstream FAIL:** the current-carrying corridor users that route AFTER the bridge failed their normal gates with two new clearance VIOLATIONS and a lost via site: `GND` clearance actual **0.0726 mm** vs 0.200 mm; `BAT_MAIN` actual **0.125 mm** vs 0.200 mm; `BAT_RAW` **NO_VIA_SITE**. Per CTO ruling these are GENUINE safety-clearance violations and MUST NOT be absorbed/refreshed into the baseline (that would waive real violations). The run is INVALID as a Phase-A candidate, not proof of success. The parent stopped it once the conflict became decisive.
- **The root cause is a SYMMETRY (cheap, reproduced by `bridge_probe_003i` clause B on the committed dense board FIX003H3):** the tight western corridor `R75.2 -> D9.1` carries 15 through-vias; the >=1.20 mm via-AWARE traverse NO_PATHs while the copper-only traverse PATHs. End-of-run the bridge cannot fit around the taps (why 003D aborted); early, the 1.50 mm bridge traverse gets in first and the SAME `LTC_GATE` / `BAT_RAW`-tap vias then have no legal site / lose clearance around it. **One corridor, two mutually-exclusive high-current users; route ORDER decides WHICH one fails, not WHETHER one fails. Timing is not the lever.**

**No false promotion.** The misleading incomplete interrupted-run board (scratch `FIX003I`) and its clobbered per-run `phaseA_journal.json` were removed / restored so no incomplete result masquerades as evidence; no `phaseA_003i_fix.json` claims a clean/absorbed end-state; the authoritative PCB is 0 tracks / 0 vias. **SUITES ALL PASS:** `bridge_probe_003i` (rewritten as the standing measured-FAIL record, clauses A/B/C/E/F), `router_regression` G1-G11 (D-280 off), `bridge_probe_003c` / `bridge_probe_003d` (003C/D-275 held FIXED), `u19_escape_probe_003e/003f/003g/003h`. Committed artifacts: the env-gated `AQROOT_BRIDGE_EARLY` driver stage in `route_battery_block.py`, `bridge_early_003i.py`, `bridge_probe_003i.py`. **Nothing moved and nothing relaxed:** D9, U18, R75-R83, Q3, shunt, FETs, C58, U19, D10 frozen; `c3_00` NOT promoted; D-249..D-280 (incl. **D-275/D-277/D-278/D-279/D-280**) untouched; the proven 003C bridge geometry held fixed; the 0.200 mm clearance floor ENFORCED not relaxed; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**). Phase A NOT completed (the D-275 BPP bridge is still not integrated into the production run). **`/home/aqroot8/.aqroot-progress.env` untouched - a failed candidate earns no readiness. Next: FBV2-P2-003J - a TOPOLOGY/CAPACITY solution (widen or add a western corridor, relocate the LTC_GATE/BAT_RAW taps, or re-plan so bridge and taps do not share the box) without weakening clearance.** Full analysis: [`audits/2026-08-28-p2-003i-d281-early-bridge-fail.md`](audits/2026-08-28-p2-003i-d281-early-bridge-fail.md).

## 2026-08-28 - FBV2-P2-003H: D-280 the 003G functional casualty N_BATDIV C61.1->U19.6 is a CO-LOCATED THROUGH-VIA LANDING (not pad geometry, not a corridor) - the fast direct-escape via placement in connect_hop checked only COPPER clearance (waived for the via's own net) and NOT the net-agnostic hole-to-hole floor, so a hop escaping straight onto its co-terminal same-net barrel dropped a second drill on the first; an env-gated hole-to-hole guard rejects the co-locating site and falls the placement through to via_site's legal 0.45 mm barrel, closing C61.1 on a full production run - net-positive, DRC-identical - with D-277/D-278/D-279 and the proven 003C bridge held FIXED; the terminal item is now the OPTIONAL BAT_SENSE TP20.1 TEST point (not a functional regression)

**A MEASURED ROUTING REPAIR that closes the 003G functional casualty on the full production run - net-positive on connectivity, identical DRC, ratsnest one better, every regression gate green - and honestly discloses the one optional test point left terminal.** 003G (D-279) closed both named dead-cell escape blockers and ROTATED one functional casualty onto `N_BATDIV C61.1->U19.6 NO ROUTE` (a bypass cap on the divider-sense node, NOT a test point). 003H measured its cause A->B->C and repaired it.

- **(A) intrinsic geometry REFUTED.** `U19.6` (SOT-23-8 hard against the west edge, ONE useful east escape lane) still escapes freely on the empty authoritative board (>=2 ways at 0.15 mm) - the pad is not the blocker.
- **(B) route-order CONFIRMED - a CO-LOCATION, not a corridor.** Two `N_BATDIV` connections are co-terminal at U19.6's single east escape (`U19.6->R89.2` and the 46 mm cross-board `C61.1->U19.6` hop), so both want a THROUGH-via barrel there. On the committed 003G BASE board they land 0.450 mm centre-to-centre - two 0.20 mm drills at EXACTLY the 0.25 mm `min_hole_to_hole` floor, ZERO margin. The 003G field re-pack tipped C61.1's landing off that zero-margin fit onto the co-located point (0.035 mm from the neighbour, hole edge -0.165 mm) and DRC answered `holes_co_located` / `hole_to_hole` every pass.
- **The defect (measured):** `connect_hop`'s fast `free_everywhere` via placement tested only COPPER clearance - which `point_free` WAIVES for the via's own net - and NOT hole-to-hole. `via_site` (the fallback) DOES enforce hole-to-hole but is only consulted when `free_everywhere` fails, so a hop escaping straight onto a co-terminal SAME-NET barrel dropped a second drill on the first.
- **(C) placement NOT required.**

**The fix (D-280, env-gated `AQROOT_D280`):** `free_everywhere` now also enforces the net-agnostic `min_hole_to_hole` floor for the barrel it is about to drill (`max(hole radius) + via_drill/2 + 250000` against every hole, own net included); a co-locating site is REJECTED and the placement falls through to `via_site`, which lands the base's own legal 0.45 mm barrel. The guard ONLY adds a rejection - it relaxes nothing, moves no part, invents no via; unset (`h2h=0`) it reproduces pre-003H byte-for-byte. The `250000` (0.25 mm) IS the governing DRU `min_hole_to_hole` and is byte-identical in structure to the existing `via_site(hole_clr=250000)` and POFV `max(h.hx,h.hy)+via_drill/2.0+250000` - safely aligned, not a new/looser value.

**Full production run (`phaseA_003h_fix.json`, scratch FIX003H3, recipe + `AQROOT_D279=1` + `AQROOT_D280=1`, c3_00 asserted, SIXLAYER, rc0; parent-supervised in session 62295, NOT re-run):** connections 69->**71**, skipped 96, ratsnest 709/-72 -> **708/-73** (one better), DRC histogram identical to baseline, `bridge_eco null`. Independent scan of all 52 through-via barrels: ZERO hole-to-hole edges below 0.25 mm; the two co-terminal N_BATDIV barrels at U19.6 land 0.450 mm centre / **0.2500 mm hole-edge, at the floor** (D-280 off: 0.035 mm / -0.165 mm).

**Casualty ledger vs 003G (exact, connections 69->71 = +2):** + `N_BATDIV C61.1->U19.6` (the D-280 target, RESTORED), + `BAT_RAW R77.1->R79.1`, + `LTC4368_FAULT_N R82.1->Q9.1` with - `LTC4368_FAULT_N Q9.1->(node)` (the SAME net - Q9.1 re-landed on its real pad, not a lost functional net). Functional C61.1 restored; D-277 (`N_POL U19.3`), D-278 (`VREC_VCC U19.8`), D-279 (`VBRIDGE_TOP R85.1->D10.1`, `REF_HO R92.1<->R93.2`) gains RETAINED. **Terminal OPTIONAL TEST-point disclosure (NOT a functional regression):** the terminal fail is `BAT_SENSE TP20.1->(node)`, role (TEST) - a test point unrouted since 003F and terminal in 003G too; 003H does not newly break it, only its fail reason shifted (003G a D-269 clearance violation 0.30 vs 0.25; 003H NO_PATH at 0.200 mm). With C61.1 closed, ALL FOUR named functional dead-cell blockers (D-277/D-278/D-279/D-280) are now closed on the full production run.

**SUITES ALL PASS AND UNREGRESSED:** new `u19_escape_probe_003h` (A/B/C/D/E), `u19_escape_probe_003g` (D-279 intact), `u19_escape_probe_003f` (D-278 intact), `u19_escape_probe_003e` (D-277 intact), `router_regression` ALL CHECKS incl. G1-G11 (D-280 off), **`bridge_probe_003c` PASS (003C/D-275 held FIXED)**, `bridge_probe_003d` PASS. `phaseA_journal.json` scratch restored to HEAD; the incomplete `log_FIX003H2.txt` scratch trashed. Committed artifacts: the driver change (env-gated D-280 guard in `qrouter.connect_hop`), `u19_escape_probe_003h.py`, `phaseA_003h_fix.json`. **Nothing moved and nothing relaxed:** D9, U18, R75-R83, Q3, shunt, FETs, TP17, C58, U19, D10 and the whole R84-R96/Q5-Q9 field frozen; `c3_00` NOT promoted; D-249..D-279 (incl. **D-275/D-277/D-278/D-279**) untouched; the proven 003C bridge held fixed; the `min_hole_to_hole = 0.25 mm` DRU ENFORCED not relaxed; outer-1-oz/high-current policy unchanged; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**). Phase A NOT completed (the held-fixed 003C BPP bridge is proven only in isolation, not yet integrated into the production run); Phase B NOT run. **THE 003G FUNCTIONAL CASUALTY IS CLOSED; all four named dead-cell blockers are closed; the Phase-A promotion blocker is the held-fixed 003C bridge integration. Next: FBV2-P2-003I.** Full analysis: [`audits/2026-08-28-p2-003h-d280-c61-landing-guard.md`](audits/2026-08-28-p2-003h-d280-c61-landing-guard.md).

## 2026-08-28 - FBV2-P2-003G: D-279 the dead-cell resistor-field congestion (VBRIDGE_TOP R85.1->D10.1, REF_HO R92.1<->R93.2) is an ANTISOCIAL B.Cu DETOUR in the packed 0402 field - not intrinsic geometry and not the D-278 crossing pin - and a measured route-time ANTISOCIAL-DETOUR LAYER HOP closes BOTH named blockers on a full production run (net-positive, DRC-identical), rotating one functional casualty (N_BATDIV C61.1) deferred to 003H; D-277/D-278 and the proven 003C bridge held fixed

**A MEASURED ROUTING REPAIR that closes BOTH named dead-cell escape blockers on a full production run - net-positive on connectivity, identical DRC, every regression gate green - and honestly TRACKS the one functional casualty it rotates.** D-278 (003F) cleared U19.8 and named these two blockers, both `NO_LEGAL_ESCAPE >=0.150 mm` in the packed 0402 dead-cell field (R84-R96/Q5-Q9, 0.65 mm pitch). 003G discriminated A->B->C.

- **(A) intrinsic geometry REFUTED:** empty-board escapes R85.1=8, D10.1=7, R92.1=8, R93.2=8.
- **(B) route-order CONFIRMED - an ANTISOCIAL DETOUR, not the D-278 crossing pin.** Reproduction note: unlike U19.8, the committed `AQROOT_LOCAL=DEADCELL` bounded prefix ROUTES both victims (it omits the west `BAT_RAW` divider, so the dead-cell `BAT_RAW` field taps that box R85.1 never lay) - the blockers are FULL-RUN emergent, so attribution was done on the real routed baseline board (a full run, D-279 off, reproducing `phaseA_003f_fix.json`: 68 conn, 710/−71, identical DRC). R85.1 is sealed to 0 by `N_POL R85.2->R86.1`, which routes 6.23 mm for a 2.48 mm span (2.5x) as a B.Cu HORSESHOE boxing R85.1 (removing it: 0->7 ways); R93.2 by REC_GATE_N copper wrapping it + the antisocial `REC_BAT_LOW Q7.1->R93.1` (23.1 mm/3.1x) (removing both: 0->8). Routed DIRECT on the empty board those same connections are harmless (N_POL R85.2->R86.1 = 2.52 mm, R85.1 stays 7) - the aggressor is the DETOUR, the general case of D-278's single crossing pin.
- **(C) placement NOT required.**

**The fix (D-279, env-gated `AQROOT_D279`):** in `run_once`, a dead-cell-class SIG B.Cu route whose copper came back > `D279_K`x its straight-line pad span AND > `D279_MIN_MM` (2.0 / 5.0 mm) is reverted and re-routed as an ordinary 0.35/0.20 through-via hop (D-257 preferred, no rule relaxed), inner signal layer (In2/In3) FIRST so the local field detour leaves outer F.Cu clear, kept ONLY if the hop is legal and strictly shorter. Adds an option, removes none; inert for every wide/high-current net, TRUNK/TAP, node target, or route within 2x of its span; unset reproduces pre-003G byte-for-byte.

**Full production run (`phaseA_003g_fix.json`, recipe + `AQROOT_D279=1`):** two connections hop onto In2.Cu (`N_POL R85.2->R86.1` 6.2->4.5 mm, `REC_BAT_LOW Q7.1->R93.1` 23.1->9.4 mm) and BOTH victims route (`VBRIDGE_TOP R85.1->D10.1` F.Cu+2 via; `REF_HO R92.1->R93.2` 3.8 mm). Aggregate: connections 68->**69**, ratsnest 710/−71 -> **709/−72** (one better), in-scope nets connected 23->**24** of 29, DRC histogram identical to baseline, `bridge_eco null`. Exactly three nets changed: VBRIDGE_TOP + REF_HO gained, N_BATDIV lost.

**Casualty ledger (tracked, not hidden):** the coupled field rotates ONE casualty onto `N_BATDIV C61.1->U19.6` - a FUNCTIONAL bypass cap (NOT a test point), a pre-existing hyper-marginal 46 mm cross-board hop whose landing via co-locates with `U19.6->R89.2`'s via and survives baseline only by ~25 um; robust across F.Cu-first and inner-first hop variants (identical aggregate). Net +2 named functional closures −1 functional casualty = +1; deferred to 003H, NOT claimed closed - the same rotation pattern by which 003F closed U19.8.

**SUITES ALL PASS AND UNREGRESSED:** new `u19_escape_probe_003g` (A/B/C/D/E), `u19_escape_probe_003f` (D-278 intact), `u19_escape_probe_003e` (D-277 intact), `router_regression` ALL CHECKS incl. G1-G11 (D-279 off), **`bridge_probe_003c` PASS (003C/D-275 held fixed)**, `bridge_probe_003d` PASS. `phaseA_journal.json` scratch restored to HEAD. Committed artifacts: the driver change (env-gated D-279 block + config), `u19_escape_probe_003g.py`, `phaseA_003g_base.json`, `phaseA_003g_fix.json`. **Nothing moved and nothing relaxed:** D9, U18, R75-R83, Q3, shunt, FETs, TP17, C58, U19, D10 and the whole R84-R96/Q5-Q9 field frozen; `c3_00` NOT promoted; D-249..D-278 (incl. **D-275/D-277/D-278**) untouched; the proven 003C bridge held fixed; outer-1-oz/high-current policy unchanged; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**). **BOTH NAMED BLOCKERS CLOSED; the rotated casualty `N_BATDIV C61.1` is the new named blocker. Next: FBV2-P2-003H.** Full analysis: [`audits/2026-08-28-p2-003g-d279-deadcell-field-hop.md`](audits/2026-08-28-p2-003g-d279-deadcell-field-hop.md).

## 2026-08-28 - FBV2-P2-003F: D-278 the VREC_VCC U19.8 NO_LEGAL_ESCAPE is a ROUTE-ORDER CROSSING DETOUR (the D-277 crossing pin REF_POL U19.2's antisocial B.Cu horseshoe); sending that crossing pin off the outer layer with a LAYER HOP clears U19.8 on a full production run; the co-terminal VBRIDGE_TOP R85.1 is a DISTINCT blocker deferred to 003G; the proven 003C bridge is held fixed

**A MEASURED, PROVEN ROUTE-ORDER/LAYER FIX for U19.8 - not a placement/topology/safety change; R85.1 is a SEPARATE blocker, measured and deferred, NOT over-claimed.** D-277 (003E) cleared N_POL U19.3 and Phase A advanced to `VREC_VCC U19.8->(node) NO_LEGAL_ESCAPE at >=0.150 mm` (blockers track x33, U19.7 x13, board_edge x5, U19.5 x5), co-terminal `VBRIDGE_TOP R85.1`. 003F discriminated the cause A->B->C with cheap analytic + isolated real-router probes and the full production driver.

- **(A) intrinsic east-row geometry REFUTED:** on the empty authoritative board U19.8 has 5 legal >=0.150 mm escapes, R85.1 has 8, D10.1 has 7.
- **(B) route-order CONFIRMED, and LOCAL to the dead-cell block:** a new bounded `AQROOT_LOCAL=DEADCELL` prefix (class of R80/D256/U19; skips the whole west-margin prefix, which cannot reach U19's y~=29 corridor) reproduces the blocker byte-similar (`track x34, U19.7 x14` vs the full run's `x33/x13`) - so the ~33 blocking `track` hits are all dead-cell copper. Obstacle attribution on the real routed board: the aggressor is the D-277 crossing pin `REF_POL U19.2` ITSELF - routed last (D-277 correctly routes U19.3 first), its direct southern lane filled by U19.3's copper, it takes a **13.372 mm NORTHERN HORSESHOE** over U19 and walls U19.8 with a segment `(4.65,29.85)->(3.05,29.85)` at d=0.495 mm and a diagonal at d=0.901 mm (U19.8 -> 0 B.Cu escape, so it cannot even start the F.Cu-hop fallback). The D-277 planar span tie-break cannot catch this: U19.2's straight-line span does not contain U19.8, and U19.8 is a MULTI-LANE victim, not the tied single-lane class.
- **(C) placement NOT required.**

**The fix (cardinality-0 placement):** reuse the exact D-277 `crossings>0 / fr<=1` predicate to mark the crossing pin in `hop_first_keys`; `run_once` then routes it with an ORDINARY 0.35/0.20 through-via F.Cu hop FIRST (D-257 preferred, no rule relaxed) instead of the antisocial B.Cu detour, falling through to the B.Cu ladder untouched on failure. Fires only in the D-277 class (today only `REF_POL U19.2`), inert for any pin with a second way out; changes only which LAYER the already-identified crossing pin runs on; lays no authoritative copper.

**Full production run (`phaseA_003f_fix.json`, base `phaseA_003d` config, no ECO, 2330 s):** `REF_POL TP24.1->U19.2` 8.610 mm F.Cu+2 vias (direct, no horseshoe) and `VREC_VCC U19.8->R84.2` 22.408 mm OK - the D-277 blocker is CLEARED and Phase A advances. Aggregate a WASH BY DESIGN (relocates the binding blocker): connections 68, skipped 94, ratsnest 710 delta -71 (003E was 68/90/711/-70, ONE net better); DRC identical to baseline (`hole_clearance 5 / lib_footprint_issues 199 / solder_mask_bridge 1 / unconnected_items 499`); `bridge_eco null`. Journal diff vs 003E: +U19.8, +`REF_HO R91.2->R92.1`, +`REC_GATE_N TP21.1->R94.2`; -`BAT_SENSE TP20.1` (a test point), -`REC_GATE_N R94.2->(node)`, -`REF_HO R92.1->R93.2`.

**The co-terminal `VBRIDGE_TOP R85.1` is a DISTINCT blocker -> 003G.** R85.1 was never routed in 003E either; on the real routed board it is boxed by **N_POL** (x10 within 2.0 mm) not the REF_POL crossing, and neither it nor its aggressor is single-lane, so the D-278 predicate correctly does not mark it. Same pattern: `REF_HO R92.1<->R93.2` boxed by REC_GATE_N x8. These are the DEAD-CELL RESISTOR-FIELD CONGESTION class (packed 0402 cluster R84-R96 / Q5-Q9, casualties rotate). The BPP closure (`D9.1/C25/C36/C58 at >=1.20 mm`) is the KNOWN held-fixed 003C bridge case, not new.

**SUITES ALL PASS AND UNREGRESSED:** new `u19_escape_probe_003f` (A/B/C/D/E, incl. E pinning that the committed full run routes U19.8 and does NOT route R85.1 - deferred, not over-claimed), `u19_escape_probe_003e` (D-277 intact), `router_regression` ALL CHECKS incl. G1-G11, **`bridge_probe_003c` PASS (003C/D-275 held fixed)**, `bridge_probe_003d` PASS (committed 003D FAIL artifacts still pin `N_POL U19.3`, un-regressed). `phaseA_journal.json` scratch restored to HEAD. Committed artifacts: the driver change, `u19_escape_probe_003f.py`, `phaseA_003f_fix.json`, `phaseA_003f_deadcell_base.json`, `phaseA_003f_deadcell_fix.json`. **Nothing moved and nothing relaxed:** D9, U18, R75, R76..R83, Q3, the shunt, the FETs, TP17 and C58 all frozen; `c3_00` NOT promoted; D-249..D-277 (incl. **D-275**) untouched; outer-1-oz / high-current policy unchanged; no safety weakening; no topology/net/footprint/polarity change; no authoritative promotion. Authoritative PCB UNCHANGED (six layers, **0 tracks, 0 vias**, no source mutated). **U19.8 CLEARED; the dead-cell resistor-field congestion (`VBRIDGE_TOP R85.1`, `REF_HO R92/R93`) is the new named blocker. Next: FBV2-P2-003G.** Full analysis: [`audits/2026-08-28-p2-003f-d278-u19-8-crossing-hop.md`](audits/2026-08-28-p2-003f-d278-u19-8-crossing-hop.md).

## 2026-08-28 - FBV2-P2-003E: D-277 the U19.3 N_POL NO_LEGAL_ESCAPE is a ROUTE-ORDER contention (cause B), not pad/board geometry; a cardinality-0 planar tie-break in the driver CLEARS it on a full production run and Phase A advances to a new deeper blocker VREC_VCC U19.8; the proven 003C bridge is held fixed

**A MEASURED, PROVEN ROUTE-ORDER FIX - not a placement/topology/safety change.** D-276 named
`N_POL U19.3->(node) NO_LEGAL_ESCAPE at >=0.150 mm` (blockers board_edge x23, U19.4 x16, U19.2 x12,
U19.6 x8) as the full-driver Phase-A blocker and named the next task: a bounded investigation of it
distinguishing (A) pad-escape geometry, (B) route-order/copper obstruction, (C) minimum placement ECO,
holding the proven 003C vacate + F.Cu 4-via bridge FIXED. 003E measured each cause and repaired the one
that is real.

- **(A) intrinsic pad/footprint/board-edge geometry - REFUTED.** On the empty authoritative board (0
  signal tracks; U19 is NOT moved by c3, which moves only R75/U18/R79) `qb.escape(U19.3, 'B', 0.150…)`
  returns a legal >=0.150 mm escape east into the inter-row gap; its sibling U19.2 also escapes; both
  middle west-row pins are SINGLE-LANE (freedom 1). The pad can leave its own copper.
- **(B) route-order / already-laid copper - CONFIRMED (the cause), and directional.** Isolated on the
  empty board, routing `REF_POL TP24.1->U19.2` FIRST drops U19.3 freedom to 0 and reproduces the D-276
  fail string byte-for-byte; routing `N_POL TP23.1->U19.3` FIRST leaves U19.2 escapable and BOTH route.
  U19.2 sits NORTH of U19.3 but its target TP24.1 is SOUTH, so its route crosses south through the gap
  over U19.3's only (east) lane and seals it; U19.3's target TP23.1 does not cross U19.2. Textbook
  planar-fanout ordering: among boxed pins exiting the same way, the one whose route crosses a sibling
  goes LAST.
- **(C) minimum placement ECO - NOT REQUIRED** (B is fixable by order alone), left un-exercised per the
  A->B->C investigation order.

**The fix - a measured planar tie-break, cardinality-0.** `order_tight` already routes the tightest pin
first, but U19.2/U19.3 tie on EVERY existing key (slack +0.14 mm, ways-out 1, width), so the order fell
through to the arbitrary MST order that put U19.2 first. The repair adds ONE final tie-break on live
geometry: among rows tied on `(slack, ways-out)` with ways-out <=1 (the boxed single-lane class),
`crossings[i]` counts tied siblings whose pad falls inside row i's pad->target bounding span, and the
sort key becomes `(slack, ways-out, width, crossings)`. U19.2's span contains U19.3 (crossing 1);
U19.3's does not contain U19.2 (crossing 0) -> U19.3 routes first, and both escape. The term is 0 for
every pin with a second way out (guarded by `fr_a <= 1`) and is the LAST sort key, so it only settles an
EXACT `(slack, ways-out, width)` tie that today resolves arbitrarily - it can never reorder across
tightness classes, and it lays no copper (read-only geometry).

**The full production Phase-A run** (`phaseA_003e_fix.json`, base `phaseA_003d` config, no ECO,
2306.8 s): the pin-field slack line now reads `U19.3 +0.14/1way  U19.2 +0.14/1way …` (reordered exactly
as the probe predicts) and both boxed pins route (`N_POL TP23.1->U19.3` 6.118 mm OK, `REF_POL
TP24.1->U19.2` 13.372 mm OK). The D-276 terminal blocker is CLEARED and Phase A ADVANCES to a NEW,
deeper terminal blocker `PHASE A: FAIL - VREC_VCC U19.8->(node) NO_LEGAL_ESCAPE at >=0.150 mm; blocked
by track (x33), U19.7 (x13), board_edge (x5), U19.5 (x5)` (co-terminal `VBRIDGE_TOP R85.1` also
NO_LEGAL_ESCAPE; both at -0.15/0way, stable across all 3 passes). Aggregate is a WASH BY DESIGN - the
fix relocates the binding blocker, it does not close Phase A: connections 68, skipped 90, ratsnest 711
delta -70 (003D-base 68/91/710/-71); DRC identical to the authoritative baseline (`hole_clearance 5 /
lib_footprint_issues 199 / solder_mask_bridge 1 / unconnected_items 499`); `bridge_eco null`. The U19.8
blocker is a DIFFERENT CLASS from D-276 - dominated by FOREIGN laid `track` (x33) on the EAST row, not
board_edge + own pins - so the west-row planar tie-break does not apply and a route-order swap is
unlikely to be sufficient; 003F must discriminate it afresh.

**Delivered + regression.** `route_battery_block.py` gains the scoped D-277 planar tie-break inside
`order_tight`; new probe **`u19_escape_probe_003e.py`** (A refuted, B both directions, C planar
prediction + lay-and-count lookahead agree, D driver carries the scoped tie-break) - **PASS**; result
artifact `phaseA_003e_fix.json`. **SUITES ALL PASS AND UNREGRESSED:** `u19_escape_probe_003e`,
`router_regression` ALL CHECKS incl. G1-G11, **`bridge_probe_003c` PASS (003C/D-275 held fixed)**,
`bridge_probe_003d` PASS (the committed 003D FAIL artifacts still pin `N_POL U19.3`, un-regressed).
`phaseA_journal.json` scratch restored to HEAD. **Nothing moved and nothing relaxed:** D9, U18, R75,
R76..R83, Q3, the shunt, the FETs, TP17 and C58 all frozen; `c3_00` NOT promoted; D-249..D-276 (incl.
**D-275**) untouched; outer-1-oz / high-current policy unchanged; no safety weakening; no
topology/net/footprint/polarity change; no authoritative promotion (Phase A did not pass). Authoritative
PCB UNCHANGED - six copper layers, 0 signal tracks, 0 signal vias. **U19.3 CLEARED; `VREC_VCC U19.8` is
the new named blocker. Next: FBV2-P2-003F.** Full analysis:
[`audits/2026-08-28-p2-003e-d277-u19-escape-order.md`](audits/2026-08-28-p2-003e-d277-u19-escape-order.md).
**NO PROGRESS EARNED: PCB routing stays 0 %, overall stays 74 %.**

## 2026-08-28 - FBV2-P2-003D: D-276 the driver-integrated vacate + F.Cu bridge is a MEASURED REPRODUCIBLE FAIL; the full production driver fails upstream at U19.3 N_POL NO_LEGAL_ESCAPE; 003C/D-275 stands as the fixed proven solution

**A MEASURED REPRODUCIBLE FAIL of production / full-driver promotion - NOT a disproof of 003C.** D-275
proved the western-corridor vacate + F.Cu via-array bridge as a POST-PROCESS of a hand-staged
reproduced c3 board and named the next task: integrate that mechanism into the production Phase-A
driver and drive it through a full 2-pass route (the D-271 discipline). 003D performs that integration
- `route_battery_block.py` gains ONE `AQROOT_BRIDGE_ECO`-guarded call to `bridge_eco_003d.apply_eco`
(single-sourcing the D-275 copper primitives verbatim from `bridge_route_003c`) - and the full driver
route **reproducibly fails on two independent passes**:

- **Phase A fails earlier, at the U19 recovery-comparator block:** `N_POL U19.3->(node) (SIG) :
  NO_LEGAL_ESCAPE : U19.3: NO LEGAL ESCAPE at >= 0.150 mm; blocked by board_edge (x23), U19.4 (x16),
  U19.2 (x12), U19.6 (x8)`.
- **The integrated 003C-style vacate-then-bridge ECO aborts:** `ECO ABORT: no >= 1.20 mm F.Cu traverse
  corridor` - the vacate runs (6 F.Cu tracks moved, 48 existing vias seen) but the production board
  offers no >= 1.20 mm F.Cu lane to bridge, unlike the hand-staged 003C board.

**Reproduced (2-pass D-271 discipline).** `phaseA_003d_ecoC.json` and `phaseA_003d_ecoD.json` are NOT
byte-identical (they differ only in per-net wall-clock `secs` jitter) but every DECISIVE field is
identical: the Phase-A `fail` string above; `connections 68`; `skipped 91`; `ratsnest 710`, delta
`-71`; DRC `hole_clearance 5 / lib_footprint_issues 199 / solder_mask_bridge 1 / unconnected_items
499` (identical to the authoritative baseline); `bridge_eco.ok false`, `fail "no >= 1.20 mm F.Cu
traverse corridor"`, `vacated 6`, `existing_vias 48`. The base `phaseA_003d.json` (no ECO) shows the
SAME U19.3 fail - the failure is upstream of and independent of the bridge ECO.

**003C / D-275 is NOT invalidated.** Its post-processed, reproducible `BAT_PROTECTED_P` closure remains
proven evidence and is the **fixed solution to preserve into 003E** (`bridge_probe_003c` re-run: PASS).
003D fails production / full-driver promotion; it does NOT disprove D-275. The gating problem is now a
new, distinct blocker: **U19.3 pad escape**, not the D-270..D-274 western-BPP-trunk arc.

**Orchestration failure (accurately diagnosed - continuation loss, not engineering, not OWNER).** The
CTO launched the ecoC/ecoD passes with `nohup setsid ... &` from a ONE-SHOT turn, then ended with a
normal text response and NO `sessions_yield`, NO persistent waiter, NO completion callback tied to PIDs
274901 / 274902. The detached children survived and finished at 04:31 UTC (correct result JSONs), but a
process exit cannot itself re-awaken an already-ended turn, and the finalize ACP session had ended at
the wait boundary. **Repair discipline recorded:** the ACP/finalize task OWNS foreground work and
returns a completion event; the CTO uses `sessions_yield` and RESUMES from that event; NO unregistered
detached child batches.

**Delivered + regression.** Kept: the env-guarded driver hook (inert with `AQROOT_BRIDGE_ECO` unset -
the default), `bridge_eco_003d.py`, `bridge_gates_003d.py`, and the three result JSONs + ecoC/ecoD/
c3repro logs as evidence. **`bridge_probe_003d.py` was CONVERTED to pin the measured reproducible
FAIL** - as first authored it presumed a PASSING driver gate (`bridge_gates_003d_*.json` with
`pr40_eco 111111111`) that never existed because the ECO aborts; it now pins A the wired/ordered hook,
B single-sourced D-275 primitives, C cardinality-1 control-role vacate, D each `phaseA_003d_eco*.json`
records the FAIL (ECO abort AND N_POL U19.3 NO_LEGAL_ESCAPE) with NO false promotion, E 2-pass
determinism of the FAIL. **D-276 DRIVER BRIDGE PROBE: PASS.** The incomplete `ecoA`/`ecoB` scratch
logs (422 lines, no verdict, no result JSON) removed. `phaseA_journal.json` scratch churn restored to
HEAD.

**Suites ALL PASS and unregressed:** `router_regression` G1-G11, `bridge_probe_003d` (rewritten),
`bridge_probe_003c`, `via_array_probe`, `d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`.
**Nothing moved and nothing relaxed:** D9, U18, R75, R76..R83, Q3, the shunt, the FETs, TP17 and C58 all
frozen; `c3_00` NOT promoted; D-249..D-275 untouched; outer-1-oz / high-current policy unchanged; no
safety weakening; no topology/net change; no authoritative promotion. Authoritative PCB UNCHANGED - six
copper layers, **0 signal tracks, 0 signal vias**, no KiCad source mutated. **U19.3 is now the named
blocker;** Phase A NOT passed; Phase B NOT run. B-34 unchanged. **Next - FBV2-P2-003E:** a bounded
investigation of the U19.3 `N_POL` NO_LEGAL_ESCAPE holding the proven 003C vacate + F.Cu 4-via bridge
FIXED - distinguishing pad-escape geometry vs route-order/copper obstruction vs minimum placement ECO;
inspecting U19.3 / U19.2 / U19.4 / U19.6 and the board edge; analytic pad-escape + smallest real-router
probes; no broad placement search, no topology/net change, no safety weakening, no authoritative
promotion unless a later full gate passes. Full analysis:
[`audits/2026-08-28-p2-003d-d276-driver-bridge-fail.md`](audits/2026-08-28-p2-003d-d276-driver-bridge-fail.md).
**NO PROGRESS EARNED: PCB routing stays 0 %, overall stays 74 %.**

## 2026-08-28 - FBV2-P2-003C: D-275 the western-corridor vacate ECO + F.Cu via-array bridge is PROVEN; the BAT_PROTECTED_P trunk closes on real, reproducible copper

**PROVEN - a real-copper PASS, the first BPP trunk closure in the D-270..D-274 arc.** D-274 named
the next step: a bounded control-net vacate ECO to open a >=1.20 mm F.Cu lane, then route the bridge.
003C runs it on the reproduced c3 board and it **succeeds**: the minimum vacate is CARDINALITY 1 - one
low-current control branch, `BAT_PROT_SHDN_CTL`, moved off F.Cu to In3 - which opens a >=1.20 mm
(1.40 mm achieved) F.Cu corridor from `R75.2` to the eastern BPP NODE, and a real 4-via / 1.40 mm
F.Cu / 4-via bridge closes bit 8 `BAT_PROTECTED_P R75.2->U11.2`. The authoritative PCB is UNCHANGED -
six copper layers, **zero signal tracks, zero signal vias**; no KiCad source mutated. Starting HEAD
`1fa37e1`.

- **The board under test, reproduced.** `run_prefix_002z.py c3_00.json c3repro003c` yields
  `applied+asserted true`, `mismatch false`, `targets=111111101`, `u18=8`, `ledger 7/29`,
  `sense 13.811 mm`, `rc 0` - byte-consistent with D-274.
- **The F.Cu vacate cut-set study (`fcu_cutset_003c.py`).** Models the vacate of an INDIVIDUAL routed
  F.Cu BRANCH (connected component of one candidate net's F.Cu copper), never a whole net, never
  current-carrying/destination copper. Baseline re-measures D-274 exactly (flood dies at x=4.80 @1.20
  / 4.65 @1.50, reaches island: no). **GREEDY MINIMAL = cardinality 1: `BAT_PROT_SHDN_CTL`** - that
  ONE branch turns the R75.2->node A* from NO_PATH to PATH at both 1.50 and 1.20; cardinality-0 does
  not open, so 1 is the PROVEN minimum (reproduced on c3repro003b and 003c). D-274 named three
  crossings for the full-width straight corridor; only one branch discriminates because
  `BAT_PROT_SHDN_CTL`'s F.Cu is a 46 mm WALL (y 59.75..93.47), and removing it lets R75.2 detour to
  the OPEN node at x=38.5 (avoiding the D9 single-via link).
- **The real vacate + bridge (`bridge_route_003c.py`).** VACATE: the 6 F.Cu tracks of
  `BAT_PROT_SHDN_CTL` move to In3.Cu (its end transitions are already THROUGH vias, so continuity
  holds; In3 clear; In1/In4 are the GND planes, kept intact; a control net was never barred inner, so
  NO netclass rule). ENTRY: 4x 0.80/0.40 through vias on R75.2's own B.Cu pad (POFV, D-258), scanned
  clear + hole-legal against the existing U18.8 sense via, united by a 1.50 mm F.Cu bus, no B.Cu ties.
  TRAVERSE: 50.99 mm of 1.40 mm F.Cu, routed VIA-AWARE (`inject_vias` adds every board via as an
  all-layer obstacle at the 0.30 mm D-269 clearance QBoard otherwise skips; 1.50 mm is NO_PATH with
  strict via clearance, so the ladder takes 1.40 mm, above the 1.20 mm floor - the 1.50 mm target is
  honestly not reached). EXIT: 4x 0.80/0.40 through vias landing on the node's 1.20 mm B.Cu copper at
  (42.40,76.40), each tied by a >=1.20 mm stub - an ARRAY landing, no single via carries pack current.
- **The gates (save/reload KiCad, `bridge_gates_003c.py`).** PR-40 `111111101` -> `111111111`; bit 8
  CLOSED; U18 8/8; the vacated `BAT_PROT_SHDN_CTL Q4.1->R83.1` stays connected; BAT_SENSE/LTC_* no
  regression; DRC identical to baseline (0 new of any class); ratsnest 741->740 (-1). **VERDICT PASS**
  on every clause. Electricals: R_bridge ~18.9 mOhm (17.9 traverse + 0.44 two arrays); 42.5 mW / 28 mV
  at 1.5 A, 57.8 mW / 33 mV at 1.75 A - the B-34 cost, updated on promotion.
- **New regression `bridge_probe_003c.py`** (real copper + DRC): the vacated control net on In3
  ALLOWED; the trunk on In2/In3 REJECTED (D-264); a current-carrying role is never a vacate candidate,
  a control role is; the bridge board closes bit 8 with no new DRC / no regression. **PASS.**
- **NOT an owner decision.** Promotion to the authoritative product board requires driver integration
  of the vacate+bridge mechanism + promotion of the c3 placement through a full 2-pass Phase-A route
  (the D-271 reproducibility discipline); that is the next task, CTO/engineering scope. The
  authoritative product board is kept unrouted (routing is a driver output) and is left untouched.
- **Suites ALL PASS and unregressed:** `router_regression` G1-G11, `bridge_probe_003c`,
  `via_array_probe`, `d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`;
  `phaseA_journal.json` scratch churn restored. D9, U18, R75, R76..R83, Q3, the shunt, the FETs, TP17
  and C58 all frozen; `c3_00` NOT promoted; D-249..D-274 untouched. U19 NOT searched; Phase A NOT
  completed; Phase B NOT run. Full analysis:
  [`audits/2026-08-28-p2-003c-d275-vacate-bridge-proven.md`](audits/2026-08-28-p2-003c-d275-vacate-bridge-proven.md).
  **The western trunk blocker that stalled D-270..D-274 is BROKEN; no authoritative progress earned
  yet: PCB routing stays 0 %, overall stays 74 %.**

## 2026-08-28 - FBV2-P2-003B: D-274 the bounded F.Cu high-current via bridge is disproved; the western margin is saturated on F.Cu exactly as on B.Cu

**BRIDGE-PROOF CLOSEOUT - a measured FAIL.** D-273 named the next step: a bounded named-path F.Cu
high-current via bridge for `BAT_PROTECTED_P`. 003B investigates it on the reproduced c3 board (U18 8/8,
trunk open) with evidence-based via-array sizing and real obstacle-aware searches, and it **fails**: the
two via-array transitions are individually feasible, but the F.Cu traversing segment between them does
not exist at the mandatory >=1.20 mm floor. The authoritative PCB is UNCHANGED - six copper layers,
**zero signal tracks, zero signal vias**; no KiCad source mutated. Starting HEAD `624f085`.

- **The board under test, reproduced.** `run_prefix_002z.py c3_00.json c3repro003b` yields `applied+asserted
  true`, `mismatch false`, `targets=111111101`, `u18=8`, `ledger 7/29`, `sense 13.811 mm`, `returncode 0`
  - byte-consistent with D-273. Measured islands (KiCad `GetConnectedItems`): TARGET `{D9.1,C25.1,C36.1,U11.2}`
  (D9.1 already tied to U11.2 via the C25/C36 F.Cu cap copper through two SINGLE 0.80/0.40 vias); SOURCE
  `{R75.2,U18.8}` - a 1.14 mm B.Cu stub at x=2.80. Bit 8 is open only because these two islands are ~8 mm apart.
- **Via-array sizing (board's own IPC-2221B, calibrated).** `via_array_003b.py`: reproduces the DRU's
  BAT_MAIN outer 0.525 mm exactly; a 0.40/25um through-via barrel as an INTERNAL FR4 conductor carries
  **1.055 A at 10 K** (conservative). For 1.75 A validation: ideal 2, **fault-tolerant floor 3** (3.17 A;
  lose one open via -> 2.11 A > 1.75 A), **design 4** (hottest via +6.5 K under 2:1 imbalance). Array R:
  N3 0.293, N4 0.220 mOhm.
- **The measurement.** `bridge_feasibility_003b.py`: **ENTRY feasible** - a 4-via array fits on R75.2's
  1.225x3.35 mm pad at 0.9 mm pitch, all copper layers clear, F.Cu empty within 3.5 mm (via-in-pad ->
  plated-over-filled, D-258 POFV precedent); **EXIT feasible** - 4-via arrays land on the node (527/855
  free sites) and a 3-via on the D9 stub; **TRAVERSE IMPOSSIBLE at >=1.20 mm** - an F.Cu full-width flood
  from R75.2 dies at **x=4.80 mm** (@1.50 4.65, @1.00 4.95, @0.80 11.6; island west edge x=10.05), and
  full-budget A* R75.2->node returns **NO_PATH at 1.20 AND 1.50 mm by region exhaustion (0.5-0.6 s)**.
  Blocker: the LTC_GATE x=5.75 vertical, the BAT_PROT_SHDN_CTL diagonal, and the BAT_RAW y=72.45 run in
  the x 4.8..11 / y 66..73 window. The 0.80 mm escape is recorded, not used - below the mandatory 1.20 mm
  trunk floor, which this task may not waive.
- **This tightens D-273:** the western margin cannot host a >=1.20 mm high-current trunk on EITHER outer
  layer - the saturation is in the plane, on both faces. The pre-existing D9->node single-via link is
  flagged as a latent bottleneck for any future stub-landing bridge.
- **Regression added.** `via_array_probe.py` pins the via-array sizing contract and REJECTS undersized
  (single-/two-via) transitions - the electrical half of the bridge guard; the overbroad/bounding-box/
  foreign-net geometric half is already carried by `dru_probe` corridor_checks. **PASS.**
- **CTO recommendation:** a bounded western-corridor control-net vacate ECO - re-route the three named F.Cu
  control crossings off the x 4.8..11 / y 66..73 window to open a >=1.20 mm F.Cu bridge lane, then route
  the bridge measured here. CTO/engineering scope (the D-270 class), NOT an owner call.
- **Suites ALL PASS and unregressed:** `router_regression` (G1-G11), `via_array_probe` (new),
  `d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`. `phaseA_journal.json` scratch churn
  restored. D-249, D-264, D-266, D-267, D-269, D-270, D-271, D-272, D-273 untouched; outer-1-oz / zero-via
  high-current policy unchanged; BAT_MAIN clearance not weakened; `c3_00` NOT promoted. **U19 NOT SEARCHED;
  Phase A NOT passed; Phase B NOT run; converter routing NOT started. B-34 REMAINS OPEN. NO PROGRESS
  EARNED: PCB routing stays 0 %, overall stays 74 %.** Full analysis:
  [`audits/2026-08-28-p2-003b-d274-fcu-bridge-disproved.md`](audits/2026-08-28-p2-003b-d274-fcu-bridge-disproved.md).

## 2026-08-28 - FBV2-P2-003A: D-273 the long outer-B.Cu zero-via route is disproved; next is a bounded F.Cu high-current via bridge

**ROUTING-PROOF CLOSEOUT - a measured FAIL.** D-272 sent the trunk question into a bounded routing proof:
test the reservation-dependent LONG outer-B.Cu route for `BAT_PROTECTED_P` BEFORE any F.Cu via bridge,
because it keeps the trunk on outer 1 oz with zero current-carrying vias. 003A runs it on the proven c3
board (U18 8/8, trunk open) and it **fails**: no long outer-B.Cu **zero-via** corridor carries
`BAT_PROTECTED_P` from `R75.2` to the eastern node copper at the **1.50 mm target or the 1.20 mm floor**.
The authoritative PCB is UNCHANGED - six copper layers, **zero signal tracks, zero signal vias**; no
KiCad source mutated. Starting HEAD `1a82652`.

- **The board under test, reproduced.** `w/c3repro003a_parent` = AUTHORITATIVE placement + pinned
  `c3_00.json` recipe via `run_prefix_002z.py`; the committed reproduction triple confirms U18 8/8,
  `targets=111111101`, `sense 13.811 mm`, `applied+asserted true`, `mismatch false`, `returncode 0`,
  and `BAT_PROTECTED_P R75.2->U11.2 = false` (the one open connection). Not a new placement.
- **The measurement (bounded families).** `long_corridor_003a_bounded.py` -> `long_corridor_003a_bounded.json`,
  re-run and reproduced byte-identically. `occ_003a.py` shows exactly ONE connected central free channel
  (x~13..38 mm) between the western margin and the node west edge, so the channel is not the
  discriminator - the ESCAPE LATITUDE is; three thinnest latitudes (north/mid/south) = F1/F2/F3, plus F4
  the D9-reservation exit; east is the node, west is the board edge, no fourth family. **Control
  `R75.2->D9.1`: @1.50 NO_LEGAL_ESCAPE, @1.20 NO_PATH. F1/F2/F3/F4 ALL FAIL both widths** - @1.50 `R75.2`
  cannot leave its pad at 1.5 mm; @1.20 it escapes ~2.7 mm to (5.5,67.95) then the first traversal out of
  the western mass is COARSE_BLOCKED; F4 COARSE_BLOCKED both. `legal B.Cu long corridor: NONE`.
- **The corroboration (full budgets, no coarse prefilter).** A 0.25 mm coarse grid can OVER-block, so
  COARSE_BLOCKED alone is not proof. `long_corridor_003a_corrob.py` runs the SAME `QR.connect_role` the
  router uses for the trunk, `R75.2` -> four node-copper points, at DEFAULT FULL budgets (ASTAR=500000,
  WAVE=3000), no prefilter, 120 s/trial cap. **All 8 trials FAIL:** @1.50 NO_LEGAL_ESCAPE (target-
  independent), @1.20 NO_PATH after a **48-62 s reachable-region exhaustion** (not a timeout). The long
  route is disproved by the router's own search, not just a coarse gate.
- **`c3_00` remains EVIDENCE ONLY, NOT promoted** to placement or authoritative copper; its bit 8
  `BAT_PROTECTED_P R75.2->U11.2` stays open. This is a measured FAIL, not analytic; no result is presented
  as a routed PASS.
- **This is NOT an OWNER decision.** The long-route proof was the gate D-272 set, and it has now run. The
  **next technical task is a bounded named-path F.Cu high-current via-bridge investigation** - evidence-
  based via-array sizing (inner layers are 0.5 oz, ~2.73 mm for 1.5 A at 10 K by the board's own
  `.kicad_dru`, so an array not one via) + full safety / DRC / connectivity gates. **NOT implemented or
  tested in 003A.**
- **Delivered.** the bounded probe + the full-budget corroboration + three read-only geometry helpers
  (`inspect_003a.py`, `occ_003a.py`, `joins_003a.py`); the naive un-bounded first draft
  `long_corridor_003a.py` is RETAINED as the documented rejected approach (its first east trial burned
  >18 min, rc130 - what motivated the bounded redesign); and **new regression G11** pinning the bounded-
  search contract on the AUTHORITATIVE board (a tiny budget must BOUND the search - prompt NO_PATH, no
  copper, no raise; the probe budget ASTAR=60000/WAVE=1200 must NOT fabricate a FAIL - still routes a
  routable short trunk; budgets saved/restored, no rule changed) - **4/4 PASS**.
- **Suites all PASS and unregressed:** `router_regression` ALL CHECKS incl. G1-G9 + G10 + G11,
  `d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`. `phaseA_journal.json` scratch churn
  restored.
- Full analysis: [`audits/2026-08-28-p2-003a-d273-long-route-disproved.md`](audits/2026-08-28-p2-003a-d273-long-route-disproved.md).
- **No progress earned:** PCB routing stays 0 %, overall stays 74 %. B-34 open. Nothing moved, nothing
  relaxed; D-249/D-264/D-266/D-267/D-269/D-270/D-271/D-272 untouched; high-current outer-1-oz / zero-via
  policy unchanged. U19 NOT searched; Phase A/B NOT run.

## 2026-08-27 - FBV2-P2-002Z: D-272 western-margin placement scope is exhausted; the first reproducible U18 8/8 does not close the BPP trunk

**PLACEMENT-SCOPE CLOSEOUT.** Bounded battery-block placement was **CTO authority (D-249...D-271) and
is now EXHAUSTED**. Across a full cardinality ladder no legal fan-8 placement makes the analytic
western `BAT_PROTECTED_P` trunk reach even **0.80 mm** on B.Cu, and none closes target bit 8
(`BAT_PROTECTED_P R75.2->U11.2`) in a supervised run. The authoritative PCB is UNCHANGED - six copper
layers, **zero signal tracks, zero signal vias** (verified: `pcbnew` load 6 layers / 0 tracks / 0 vias;
`kicad/` tree byte-for-byte HEAD). Starting HEAD `016aeee`.

- **The cardinality ladder, exhaustive.** baseline (U18 authoritative pose alone) **6/8** (`U18.7`+
  `U18.8` open); **c1** (one component) **ceiling 7/8** - no single move lands all of {7,8,2}; **c2**
  (R75+U18, 5 supervised) **ceiling 7/8 AND target bit 8 FALSE in all five** - the trunk routes freely
  at 1.50 mm (13.12 mm) with NO fanout but is dead at every width down to 0.40 mm once the 8-pin fanout
  is laid, so the binder is the whole fanout band saturating the board-edge-bounded west margin, not
  one obstacle; **c3** (R75+U18+one divider, 4 supervised) delivers the **first reproducible U18 8/8**
  (`c3_e10n_r79`/`c3_00`: R75 `[2.8,65,270]`, U18 `[4.0,72.9,90]`, R79 east `[9.825,67.825,0]`, targets
  `111111101`, ledger 7/29, sense 13.811 mm, returncode 0, applied+asserted true) - the unique lever of
  243 candidates, widening the analytic trunk 0.40->0.80 mm - **but target bit 8 is FALSE in all four**
  and the 8/8 is knife-edge (a 0.5 mm U18 x-shift re-opens `U18.7`); **c4** the last placement family,
  a bounded-exhaustive **705-pose U18-pose vacate sweep**, returns **NEGATIVE** (102 fan-8 mech-clean
  poses, `trunk_best_w` only ever 0.40 mm or dead, **zero reach 0.60 mm let alone the 1.20 mm floor**).
- **`c3_00` is accepted as EVIDENCE ONLY** - the first reproducible U18 8/8 - and is **NOT promoted** to
  the authoritative placement or to authoritative copper; its bit 8 `BAT_PROTECTED_P R75.2->U11.2`
  remains open.
- **Conclusion.** The west margin cannot host U18 8/8 AND the current-carrying `BAT_SENSE` path AND a
  >=1.20 mm B.Cu trunk at once - it is saturated **in the plane, not along a length**. Closing bit 8
  requires leaving the margin, a routing/topology move, not a placement ECO.
- **This is NOT an OWNER decision, and it SUPERSEDES D-271's owner-escalation framing.** The
  placement-change half D-271 offered was CTO authority all along and is now spent to exhaustion. The
  **next technical task tests the reservation-dependent LONG outer B.Cu route FIRST** (preserves outer
  1 oz and the high-current zero-via policy; ~2.29x trunk resistance / ~18.9 mW extra at 1.5 A is an
  engineering tradeoff to **verify**, not escalate). The **F.Cu high-current via bridge remains a
  DEFERRED FALLBACK, not authorized** - the via-policy question reaches the owner only if the long-route
  proof fails.
- **Delivered.** three analytic prefilters (`place_search_002z.py`, `place_search_c3_002z.py`,
  `place_search_c4_002z.py`) + the pinned arbiter `run_prefix_002z.py`; a **generalized process-unique
  DRC transient fix** in `path_role_util.py` (`RU.drc` wrote a FIXED-name transient that concurrent
  same-phase search prefixes on a shared WORK clobbered - now `drc_%s_%d.json % (tag, os.getpid())`,
  reclaimed after the read, **no routing result and no single-run output change**); and **new regression
  G10** whose guard IS the collision (two processes, shared WORK, same fixed tag; both must return the
  authoritative baseline histogram and neither may raise) - **4/4 PASS**.
- **Suites all PASS and unregressed:** `router_regression` ALL CHECKS incl. G1-G9 + G10,
  `d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`. `phaseA_journal.json` scratch churn
  restored.
- **No long B.Cu route and no F.Cu via bridge attempted** - both are next-task routing work.
- Full analysis: [`audits/2026-08-27-p2-002z-d272-placement-exhausted.md`](audits/2026-08-27-p2-002z-d272-placement-exhausted.md).
- **No progress earned:** PCB routing stays 0 %, overall stays 74 %. B-34 open. Nothing moved, nothing
  relaxed; D-249/D-264/D-266/D-267/D-269/D-270 untouched; high-current outer-1-oz / zero-via policy
  unchanged.

## 2026-08-27 - FBV2-P2-002Y: D-271 the 002W prefix is pinned and deterministic; the "proven 8/8" board is not reconstructible from committed code

**DECISION STOP.** The reproduction gap FBV2-P2-002X flagged is resolved as a **reproducibility
defect, not a router defect**. The 002W qualification prefix is now **pinned and self-describing**
(`prefix_002w.py` + `prefix_002w_manifest.json`), and the "proven 8/8" board is shown, with
evidence, to be **not reconstructible from the committed code**. The authoritative PCB is UNCHANGED -
six copper layers, zero signal tracks, zero signal vias; 002Y changes no routing code and no rule.
Starting HEAD `8725eea`.

- **The site drift is recipe non-pinning, not a clearance interaction.** On the AUTHORITATIVE
  placement the pinned recipe reserves `U18.8` at **(3.000, 71.600)** on both the scored and the
  nearest-exit attempt, and does so IDENTICALLY at commit `798d0ae` (002T), `6ebb009` (002U) and
  `8725eea` (HEAD). D-269's clearance rewrite (`6edc34a`) is therefore **not** the cause - the
  pre-D-269 code selects the same site. `reserve_escape`, the reservation plan and its order are
  byte-identical across 002T→HEAD; there is no tie-break instability and no state leakage
  (`RU.fresh` rebuilds from the authoritative source every run). **This supersedes 002X's
  "D-269-clearance / reservation-scoring interaction" attribution.**
- **The placement trap.** `RU.fresh` copies the AUTHORITATIVE board; `AQROOT_ECO_002F=1` silently
  swaps a placement differing in nine parts (`U18@3.000,72.400` vs `U18@8.000,65.250`, `R76..R83`).
  The guard is the driver's own `AQROOT_EXPECT_PLACEMENT=AUTHORITATIVE`, now pinned into the recipe -
  it refuses to route on the wrong board.
- **The site is the sole candidate and not the blocker.** Instrumented, `U18.8` has exactly one via
  candidate - (3.000, 71.600) - and laying it seals no sibling at reservation time; `U18.7` is sealed
  later, cumulatively. Forcing (3.750, 71.600) is DRC-illegal here (`solder_mask_bridge`,
  `shorting_items`, `clearance`) and `U18.7` stays blocked anyway.
- **The "3.750 / 8-of-8" board is not reconstructible.** The 002T audit records `BAT_SENSE
  Q3.6→R75.1` 13.532 mm, `R75.2` via (1.200, 65.700), U18 8/8; the committed code produces 18.200 mm,
  (2.800, 63.200), U18 6/8 - and reproduces those even at the 002T commit. The audited board's recipe
  is lost. Checked against git history and stored JSON with bounded scratch runs at three commits -
  not handwaved.
- **The true blocker, on a reproducible board.** The 18.200 mm sense path is the current-carrying
  diagonal wall (6.75,62.45)→(2.80,66.40) 002X named; here it is `U18.7`'s casualty, one pad west of
  the trunk's. No legal reservation site and no low-current offload set opens 8/8. This **confirms and
  tightens** 002X's `BAT_SENSE`-blocker conclusion on a deterministic board, and bounds it: the trunk
  question is not even reachable at 8/8.
- **Delivered.** `prefix_002w.py` - a one-command pinned regression with two gates: DETERMINISM
  (PASS; the board reproduces `prefix_002w_manifest.json`, so a future task cannot unknowingly study a
  different board) and GOVERNED GOAL (FAIL by design - U18 6/8 with `U18.8` at the blocking site;
  "must fail when U18.8 lands at the blocking site or U18 drops below 8/8").
- **No real B.Cu trunk attempted** - the prefix it must sit on is not 8/8, and a trunk on a 6/8 board
  would be a manufactured pass.
- **Suites all PASS and unregressed:** `d264/d266/d267/d269/d270_probe`, `dru_probe`,
  `netclass_probe`, `router_regression`.
- **Decision required (OWNER):** accept the western margin is oversubscribed at current-carrying
  roles and take the protection-architecture route (F.Cu via-array bridge, or the 2.29× long B.Cu
  route), or authorise a placement change to widen it. Neither taken.
- Full analysis: [`audits/2026-08-27-p2-002y-reproduction.md`](audits/2026-08-27-p2-002y-reproduction.md).
- **No progress earned:** PCB routing stays 0 %, overall stays 74 %. B-34 open. Nothing moved,
  nothing relaxed; D-249/D-264/D-266/D-267/D-269/D-270 untouched; high-current policy unchanged.

## 2026-08-27 - FBV2-P2-002X: D-270 path-role offload delivered and proven; the western-margin trunk blocker is current-carrying, not low-current

**DECISION STOP.** The D-270 offload mechanism is delivered and regression-proven, but the
offload does not open the trunk: measured by individual path role, the binding blocker of
`R75.2 -> D9.1` is the **`BAT_SENSE` 1.00 mm shunt current path**, which D-270 correctly
refuses to move. The authoritative PCB is UNCHANGED - six copper layers, zero signal tracks,
zero signal vias. Starting HEAD `6edc34a`.

- **D-270(a):** *"Western-margin offload candidate selection shall be by individual CURRENT
  PATH ROLE / ROUTED BRANCH, not whole net or net class. A bounded LOW-CURRENT / TAP branch on
  `BAT_RAW` or `BAT_MAIN` may be offered In2/In3 offload despite its power net name."* Offload
  is the fifth property to follow path role, after D-249 width, D-264 layer, D-267 via geometry
  and D-269 clearance - and it closes the candidate-list gap D-269's own audit named.
- **Mechanism.** `path_role_dru.INNER_OFFLOAD_AREAS` adds the authorised bounded corridors to
  the exact D-264 In2/In3 exclusion the two Kelvin sense corridors already carry; the router
  (`battery_route_plan.D270_SETS` + the offload block in `route_battery_block.run_once`) hops
  the named branch `B -> In2/In3 -> B` on the smallest via its netclass admits - the D-267
  0.65/0.40 POWER via, never the trunk's 0.80/0.40. Every current-carrying role is untouched.
- **New standing regression `d270_probe.py`** - real copper on the six-layer board, eleven
  clauses, **PASS**: a `BAT_RAW` bridge on In2 and In3 inside its corridor is ALLOWED; the same
  copper with no corridor is REJECTED; the trunk and the `BAT_SENSE` current path on In2 are
  REJECTED; **the bridge in its corridor but WITHOUT the D-270 authorisation is REJECTED**; the
  D-264 sense corridors are unregressed; **no width, clearance, via, hole or GND rule changes.**
- **The offload study is by individual branch, never whole-net.** `offload_probe_002x.py`
  records the B.Cu each `(net, a, b)` connection lays (router `AQROOT_BRANCH_TRK`) and cuts one
  routed branch at a time. **17 low-current branches sit in the trunk corridor; NO offload set
  of any cardinality opens `R75.2 -> D9.1` at >=1.20 mm.** The one cut that opens it removes
  **`BAT_SENSE`** - the 1.00 mm shunt CURRENT path `Q3.6 -> R75.1`, running between `R75.2` and
  `D9.1`. It is current-carrying; D-270 forbids offloading it (0.5 oz needs 2.73 mm for 1.5 A).
- **The real harness confirms it.** `AQROOT_D270=BRIDGES`: the bridges leave B.Cu, but the
  trunk is still GATE_REJECTED on the D-269 clearance - `0.3000 mm required; actual 0.2500 mm`
  - against `BAT_SENSE`. This is the D-263 tension localised by path role: the two roles that
  collide in the margin, the trunk and `BAT_SENSE`, are BOTH current-carrying.
- **Bounded by a reproduction gap, stated plainly.** The 002W 8/8 prefix (`probe_002w_W3.json`,
  `111111111`) does not reproduce at HEAD - every recipe lands at U18 6/8 or 7/8, `U18.7` the
  invariant casualty, because the D-266 `U18.8` reservation via lands at (3.000, 71.600) not
  the 002T-proven (3.750, 71.600). D-269 §6's `control+BAT_RAW -> 1.50 mm` was measured on that
  8/8 board; on every prefix reproducible at HEAD it takes `BAT_SENSE` too.
- **Decision required:** (a) reproduce the 8/8 prefix by resolving the `U18.8` reservation-site
  interaction, then re-measure - in scope for a follow-up; **or (b) accept that the margin
  cannot host both the `BAT_SENSE` current path and a >=1.20 mm trunk on B.Cu**, and take the
  F.Cu via-array bridge or the long B.Cu route (2.29x resistance) - an OWNER call, as 002W and
  D-268 framed.
- **Suites all PASS and unregressed:** `d270_probe` 11/11, `d264_probe`, `d269_probe`,
  `dru_probe`, `netclass_probe`, `router_regression` G1-G9. Authoritative DRC unchanged;
  scratch pass-1 screen is baseline + one dangling via (a screen, not a passed Phase A).
- **Nothing moved and nothing else relaxed.** TP17 and C58 frozen; D-249/D-264/D-266/D-267/
  D-269 untouched. **U19 NOT SEARCHED; Phase A NOT passed; Phase B NOT run; converters NOT
  started.** B-34 remains open. Full analysis:
  [`audits/2026-08-27-p2-002x-d270-offload.md`](audits/2026-08-27-p2-002x-d270-offload.md).

## 2026-08-27 - FBV2-P2-002W: D-269 path-role clearance closes BAT_RAW; no control-offload cut set exists

**DECISION STOP** (section 25). **`BAT_RAW` is one functional island for the first time.**
The authoritative PCB is UNCHANGED - six copper layers, zero signal tracks, zero signal vias.

- **D-269(a):** *"BAT_MAIN 0.300 mm routed clearance is a CURRENT-PATH-ROLE requirement, not
  an entire-net-name requirement."* Clearance is the fourth and last property to get what
  D-249 gave width, D-264 gave layer and D-267 gave via geometry.
- **0.300 mm is untouched on every current-carrying role.** The exclusion reaches four bounded
  corridors grown from the divider chain's own copper; inside them the **existing** rules
  govern - the board default **0.200 mm**. No new clearance number was invented.
- **One corridor per branch, not one per chain** - `enclosedByArea` honours only the first
  outline of a multi-outline rule area. **And a bounded TAP corridor must carry its width
  allowance too**: naming it for the clearance exclusion took away the anonymous `BAT_STUB`
  that had been carrying the width, and the copper came back as `track_width (rule 'BAT_MAIN
  minimum width')`.
- **New standing regression `d269_probe.py`** - real copper on two different BAT_MAIN-class
  nets, six clauses, **PASS**. (The first version used two same-net tracks and saw nothing:
  clearance is a between-nets rule.)
- **`BAT_RAW` CLOSES.** `R77.1 -> R79.1` routes **12.454 mm at 0.20 mm on F.Cu with 2 vias at
  the legal 0.65/0.40**; all eleven functional pads in one island, only `TP16` outstanding.
  No inner-layer exception, no clearance or hole relaxation. The proven prefix reproduces
  alongside: **U18 8/8, Kelvin A 7.644 / B 9.927 / mismatch 2.283 mm on In2.**
- **And no control-offload cut set exists.** Every subset of the seven control nets carrying
  B.Cu copper was tested by virtual removal at 1.20 and 1.50 mm - 7 singles, 21 pairs, 35
  triples, 35 four-sets, 21 five-sets, 7 six-sets, and the full seven - **not one opens a
  1.20 mm corridor.**
- **The reason is this task's own doing, and it is said plainly:** `R80.1 -> Q2.7`
  (0.50 mm x 29.022 mm) and `D12.1 -> R77.1` (0.60 mm x 14.637 mm) are now in the margin.
  **All seven control nets AND `BAT_RAW` removed = 1.50 mm at 19.9 mm**; anything less is
  0.60 mm at best. Those two runs are microamp TAP copper on a power-named net - section 9
  excluded power nets **by net class**, but **by path role** they are exactly what section 13
  would have moved.
- **Decision required:** extend the offload candidate set from net class to path role (needs
  an explicit ruling - section 6 forbids a `BAT_RAW` inner exception), or accept that the
  western margin cannot host both the control field and a >=1.20 mm trunk. **`BAT_RAW`'s
  closure should not be given back.**
- Zero new DRC classes, zero track_dangling, zero via_dangling. All eight suites PASS. No
  placement ECO, no signal copper, TP17 and C58 untouched. D-264/D-266/D-267 untouched.
- **No progress earned: PCB routing stays 0 %, overall stays 74 %.**
  See [`CTO_DECISIONS.md`](CTO_DECISIONS.md) D-269 and
  [`audits/2026-08-27-p2-002w-d269-clearance.md`](audits/2026-08-27-p2-002w-d269-clearance.md).

## 2026-08-27 - FBV2-P2-002V: D-268 - the western partition is routed control copper, not placement

**DECISION STOP** (sections 19 and 24). The authoritative PCB is UNCHANGED - six copper
layers, zero signal tracks, zero signal vias.

- **D-268:** *"The high-current BPP trunk remains on outer 1 oz copper with zero vias. The
  first placement lever for the severed western B.Cu plane is TP17, a non-functional test
  point routed last. C58 may move only if TP17-alone is measured insufficient.
  Inner-layer/high-current-via bypass is not authorized."*
- **The lever was aimed at the wrong thing, and one cheap measurement proved it.** Removing
  TP17, C58, TP15 - entirely, not relocating them - from the finished 002U board changes
  `R75.2 -> D9.1` at **no width from 1.50 down to 0.20 mm**. Neither is on the cut.
- **The cut is routed control copper.** By net: `LTC_OV` (27 B.Cu shapes) removed restores
  0.60 mm; **all LTC control (77 shapes) removed restores 1.50 mm at 30.561 mm**; all routed
  B.Cu removed gives back the 19.878 mm clean-board route. No single control net opens it to
  trunk width.
- **TP17 was searched and replayed anyway.** 20 legal poses outside the current corridor;
  selected **(17.000, 79.000), 5.408 mm**, same layer/net/footprint/region. The full prefix
  reproduces - **U18 8/8, all nine targets, Kelvin A 7.644 / B 9.927 / mismatch 2.283 mm on
  In2** - and the trunk is still `NO LEGAL ESCAPE at >= 1.200 mm`. **The blocker list went
  from `track (x37), R77.2 (x8), TP17.1 (x5)` to `track (x42), R77.2 (x8), R78...`: TP17 left
  the list and the trunk did not move.** It did open a 0.60 mm / 53.916 mm path - below the
  floor, so not a trunk.
- **C58 characterized and NOT moved:** 1 uF 25 V X7R 0603, `C58.1` on `BAT_PROTECTED_P`
  **4.009 mm from `D9.1`** with the bulk caps 50 mm away - local HF decoupling for the
  protected node. Section 9's search was not spent, on measured grounds.
- **BAT_RAW half closed:** `R79.1 -> R80.1` routes (4.532 mm, F.Cu, 2 vias at the legal
  0.65/0.40); **`R77.1 -> R79.1` still fails on `BAT_MAIN routed clearance`**. Microamp taps
  are held to the high-current clearance because they share a net name - D-249 fixed width,
  D-264 layer, D-267 via geometry; **clearance is the fourth and last property still scoped by
  net name.** Raised, not taken.
- **The long outer trunk is not available either:** `D9.1 -> R75.2` is `NO_LEGAL_ESCAPE` at
  1.50 and 1.20 mm - that exit exists only with the D-267 reservation. Comparison recorded:
  short 19.878 mm @1.50 = **6.53 mOhm / 9.79 mV / 14.7 mW** at 1.5 A; long 45.467 mm @1.50 =
  **14.93 mOhm / 22.40 mV / 33.6 mW** - **2.29x the resistance**.
- Zero new DRC classes, **zero track_dangling, zero via_dangling**. All seven suites PASS.
  No placement ECO, no signal copper written; no rule relaxed anywhere. D-264/D-266/D-267
  untouched. U19 NOT searched; Phase A and Phase B NOT run.
- **No progress earned: PCB routing stays 0 %, overall stays 74 %.**
  See [`CTO_DECISIONS.md`](CTO_DECISIONS.md) D-268 and
  [`audits/2026-08-27-p2-002v-d268-tp17.md`](audits/2026-08-27-p2-002v-d268-tp17.md).

## 2026-08-27 - FBV2-P2-002U: D-267 D9 exit reservation and TAP path role; Kelvin B fixed; trunk stops on a severed plane

**Section 25 DECISION STOP.** Two of 002T's three failures close. The authoritative PCB is
UNCHANGED - six copper layers, zero signal tracks, zero signal vias.

- **D-267:** *"An early high-current escape reservation is permitted only for D9.1, at the
  existing BPP trunk target/floor, outer-layer-only and zero-via. It preserves the pad exit
  without completing the current path early."*
- **The reservation works on its own terms.** `D9.1` escapes at 1.50 mm in SIX directions on a
  clean board. Staging families are prefixes of the measured clean-board trunk (19.878 mm at
  1.50 mm). **F1 reserved 2.701 mm and F2 5.149 mm, both at the 1.50 mm target, B.Cu, zero
  vias, and neither cost a control pin - U18 stayed 8/8 on both.**
- **`track_dangling` joins `via_dangling`** as a class absorbed only while a reservation is
  outstanding; the final board must carry neither.
- **KELVIN B IS FIXED by section 11 alone.** `join_reserved` tries the 25 um lattice first and
  keeps the shorter run. **A 7.989 -> 7.644 mm, B 10.456 -> 9.927 mm (inside the cap),
  mismatch 2.467 -> 2.283 mm.** Same via sites, same corridor - measured more carefully, not
  relaxed.
- **TAP path-role via correction delivered, and the board narrowed it.** Via geometry now
  follows the PATH ROLE. A TAP on a POWER net cannot have a small via: 0.35/0.20 fails
  `via_diameter`, 0.50/0.25 fails `drill_out_of_range`, 0.50/0.40 fails `annular_width` - all
  three rejections correct. **0.65/0.40 is the floor**, outer layers only. With it
  **`R79.1 -> R80.1` routes (4.532 mm)** and `D12.1 -> R77.1` improves from 28.058 mm at
  0.60 mm to **13.682 mm at 0.30 mm on B.Cu with zero vias**. Forbidding the hop outright was
  tried first and measured WORSE than 002T.
- **THE TRUNK STOPS ON A SEVERED PLANE.** `R75.2` escapes at 1.50 mm, the staging point
  escapes at 1.50 mm, and **there is no B.Cu corridor between them at 1.50 / 1.20 / 1.00 /
  0.80 / 0.60 / 0.40 / 0.30 / 0.20 mm.** After the control field the control copper partitions
  B.Cu in the western margin. Nothing that reserves a pad can repair that.
- **And the obvious next hypothesis is measured false:** trunk EARLY, with the D-266
  reservations in place, routes 19.219 mm at 1.20 mm and takes **U18 to 5/8** (`U18.3`,
  `U18.7`, `U18.9` open). Reserving the sense exits does not make an early trunk affordable.
- **Decision required, three options, none this task's to take:** a bounded layer exception
  for the trunk where it crosses the pin field; move `TP17`/`C58` out of the western margin;
  or accept a ~2.3x longer trunk that leaves the margin entirely.
- New standing regression `d267_probe.py` (19 checks). All suites PASS. No placement ECO, no
  signal copper written, no netclass / clearance / annular / hole rule relaxed anywhere.
  D-264 and D-266 untouched. U19 NOT searched; Phase A and Phase B NOT run.
- **No progress earned: PCB routing stays 0 %, overall stays 74 %.**
  See [`CTO_DECISIONS.md`](CTO_DECISIONS.md) D-267 and
  [`audits/2026-08-27-p2-002u-d267-d9-reservation.md`](audits/2026-08-27-p2-002u-d267-d9-reservation.md).

## 2026-08-27 - FBV2-P2-002T: D-266 SCARCE-PAD RESERVATION; U18 8/8 INCLUDING BOTH KELVIN PINS; gate fails on the trunk alone

**A - D-266 delivered and proven. B - decisive local gate: FAIL, on the trunk.**
The authoritative PCB is UNCHANGED - six copper layers, zero signal tracks, zero signal vias.

- **The premise is measured.** On a clean board at the frozen placement NOT ONE of the four
  scarce sites is scarce: `Q3.6` escapes at 1.50 mm / 3 dir, `R75.1` 1.50 / 5, `R75.2`
  1.50 / 3, `U18.9` / `U18.8` / `U18.2` 0.25 / 2 each, every one with a 0.35/0.20 through-via
  site reachable within 0.890-1.375 mm. Every scarcity 002M-002S reported was made by copper
  laid earlier.
- **`Q3.5 -> Q3.6` 3.770 mm and `Q3.6 -> R75.1` 13.532 mm**, both at the 1.00 mm target on
  B.Cu with **zero vias**, when routed first.
- **Kelvin exits reserved, both ends of a branch as one gated item** - a 0.20 mm neck plus one
  ordinary 0.35/0.20 through via, no microvia / blind / buried / POFV. A reservation is judged
  by an **inverted gate**: DRC gains no class and the ratsnest must NOT move. It is never
  counted as a route.
- **U18 8 of 8, `U18.8` and `U18.9` CONNECTED, all nine PR-40 targets true - a first.**
  `LTC_GATE` 6/6, `LTC_SHDN`, `LTC4368_FAULT_N` 4/4, `LTC_OV` (B.Cu, zero vias), `LTC_UV`,
  `Q3_CS`, `Q2_CS`, `BAT_MID` all one component. **One control schedule was needed, not six.**
- **Paired inner Kelvin built on In2, both branches, no F.Cu fallback:** A 7.989 mm / 2 vias,
  B 10.456 mm / 2 vias, **mismatch 2.467 mm (inside the 5.000 mm limit)** - and **branch B is
  0.456 mm over the 10.000 mm cap**, reported as a failure.
- **`holes_co_located` is gone.** `BAT_PROT_SHDN_CTL Q4.1 -> R83.1` closed at 41.814 mm,
  0.15 mm, F.Cu + 2 ordinary vias, no new clearance exception. `BAT_RAW R79.1` is split because
  a ruled microamp tap is asked for a wide-net 0.80 mm via - raised, not fixed.
- **The trunk is the whole remaining failure:** `R75.2 -> D9.1` = `NO LEGAL ESCAPE at
  >= 1.200 mm; blocked by track (x37), R77.2 (x8), TP17.1 (x5)`. Zero corridor families were
  generated because the failure is at `D9.1`'s escape, before a corridor question exists.
- **Section 23 not triggered; Q3 does not move.** `BAT_SENSE` carries `Q3.5`, `Q3.6`, `R75.1`
  and `U18.9` in one functional island with the full control field and both Kelvin branches on
  the board.
- New standing regression `d266_probe.py` (13 checks) and `scarce_char_002t.py`. All standing
  suites PASS. No placement ECO, no Q3 POFV, no signal copper written. U19 NOT searched;
  Phase A and Phase B NOT run; converter routing NOT started. B-34 remains open.
- **No progress earned: PCB routing stays 0 %, overall stays 74 %.**
  See [`CTO_DECISIONS.md`](CTO_DECISIONS.md) D-266 and
  [`audits/2026-08-27-p2-002t-d266-reservation.md`](audits/2026-08-27-p2-002t-d266-reservation.md).

## 2026-08-27 - FBV2-P2-002S: D-264 DELIVERED AND PINNED; `LTC_SHDN` CLOSES; gate fails at section 21

**A - D-264 path-role layer policy: DELIVERED.** **B - decisive local gate: FAIL.**
The authoritative PCB is UNCHANGED - six copper layers, zero signal tracks, zero signal vias.

- **Outer-layer-only is now a CURRENT PATH ROLE restriction, not an entire-net-name
  restriction.** `path_role_dru.outer_only_rules()` scopes `BAT_MAIN is outer-layer only`
  on In2/In3 with `!A.enclosedByArea('BAT_SENSE_KELVIN') && !A.enclosedByArea('BAT_PROT_TAP_U18')`.
  The only inner exceptions presently authorized are the two bounded R75-to-U18
  Kelvin/sense branches. Current-carrying `BAT_MAIN` copper stays barred from In2/In3.
- **KiCad `disallow` fires on EVERY matching rule, not last-match-wins.** Appending the
  scoped rule left the unscoped one live; the generated board now excises the static block.
  The authoritative `.kicad_dru` keeps it so `dru_probe` still reads the shipped intent.
- **New standing regression `d264_probe.py`** - six clauses A-F, all PASS.
- **`LTC_SHDN` was never a trapped pad.** Alone: 5 escape directions at 0.25 mm B.Cu, via
  sites at 0.60/0.50/0.35/0.25, `U18.6 -> R80.2` 10.269 mm. 002R's `NO_LEGAL_ESCAPE` was
  neighbour copper - so the U18 pin-field SCHEDULE is the variable.
- **Schedule hypothesis measured TRUE:** 10 of 12 schedules give U18 6/6 with all seven
  functional control nets whole. On `6,10,7,1,3,2`: all nine PR-40 targets true,
  **`LTC_SHDN` one component**, `LTC_OV` one component B.Cu zero vias, `LTC_GATE` six of
  six, `FAULT_N` four of four, `Q3_CS` one component through the POFV.
- **And it fails: U18 6 of 8**, open on `U18.2` (`NO_PATH`) and `U18.9` (`NO_LEGAL_ESCAPE`).
  `R75.1` unreachable takes `BAT_SENSE` to five islands and the trunk `R75.2 -> D9.1` with
  it, so sections 16-19 were never reached and no trunk corridor family was generated.
- **Section 14's paired inner Kelvin was NOT achieved and is not reported as one:**
  `U18.8 -> R75.2` routed 9.930 mm but on **F.Cu + 2 vias**, the fallback; `U18.9 -> R75.1`
  never routed. One branch, wrong layer, unpaired.
- **Three of the four failing pads are NOT sealed.** On the finished board `U18.9` escapes
  at 0.20 mm, `U18.2` at 0.20 mm, `R75.1` at 0.25 mm - they failed at the width and layer
  demanded at the time, not because copper walls them in. **`Q3.6` is the exception**: no
  legal escape at >= 0.150 mm, blocked by track (x28), `Q3.7`, `Q2.3` and the board edge.
- All five suites PASS. No placement ECO, no Q3 POFV, no signal copper written. U19 NOT
  searched; Phase A and Phase B NOT run; converter routing NOT started. B-34 remains open.
- **No progress earned: PCB routing stays 0 %, overall stays 74 %.**
  See [`CTO_DECISIONS.md`](CTO_DECISIONS.md) D-265 and
  [`audits/2026-08-27-p2-002s-d264-pathrole.md`](audits/2026-08-27-p2-002s-d264-pathrole.md).

## 2026-08-27 - FBV2-P2-002R: SIX-LAYER ARCHITECTURE LOCKED; D-263 routing stops on a standing rule

**A - authoritative six-layer lock: PASS** (`f8c931b`). **B - D-263 routing: DECISION STOP.**
The two results are independent by section 2's ruling, and the second does not undo the first.

- **THE AUTHORITATIVE PCB IS NOW SIX LAYERS.** JLCPCB **JLC06161H-7628**, nominal 1.6 mm, 1 oz outer
  / 0.5 oz inner, **In1 and In4 solid GND**, In2/In3 internal signal, no blind/buried/laser vias.
  Rollback point **`beta-v2-p2-pre-sixlayer-authoritative`** created at `5f10073`, pushed and
  verified on the remote BEFORE any modification.
- **Validated after save / reload / refill:** 6 copper layers in order, published dielectrics
  0.2104 / 0.4 / 0.2028 / 0.4 / 0.2104, **In1 one island and In4 one island**, no pour on In2/In3,
  **zero signal tracks and zero signal vias**, outline datum 72.000 x 148.000 mm, **324 of 324
  footprint positions IDENTICAL** to the pre-lock board, **DRC byte-for-byte the four-layer
  baseline** with no new violation class, ERC unchanged, and all five suites PASS. Committed and
  pushed **before** any routing, per section 8, so it survives Part B. `p1_regression` now guards
  **both** reference planes and asserts the copper layer count - the In1 check was EXTENDED, never
  weakened.
- **SECTION 10'S REORDERING WAS IMPLEMENTED AND IT MOVES THE CASUALTY RATHER THAN REMOVING IT.**
  Trunk-first (002Q) cost `U18.2`/`U18.3`/`U18.7`; Kelvin-first cost four control pins;
  **controls-first costs `U18.6` AND the sense pads** - `R75.1`, `R75.2`, `Q3.5` and `Q3.6` all
  `NO_LEGAL_ESCAPE`. **Three orders, three different casualties, one cause: there is not enough
  B.Cu around U18 and R75 for the pin field, the sense pair and the high-current chain to coexist**,
  and reordering only chooses who goes without.
- With controls first, `LTC_OV` closes as **ONE COMPONENT on B.Cu with ZERO vias**
  (`R77.2 -> R78.1` at 2.457 mm - the first time that has held in this order), `LTC_GATE` closes all
  six functional pads, `FAULT_N` all four, `LTC_UV` at 9.889 mm and VIN at 4.910 mm - **but
  `LTC_SHDN U18.6 -> R80.2` is `NO_LEGAL_ESCAPE`**, so section 11's control-lane reservation never
  reaches 8/8.
- **SECTION 14'S PAIRED-INTERNAL KELVIN IS BARRED BY A STANDING RULE, NOT BY GEOMETRY:**
  `BAT_PROTECTED_P U18.8 -> R75.2` is rejected with **"Items not allowed (rule 'BAT_MAIN is
  outer-layer only')"**. The rule covers the WHOLE net and the Kelvin tap is part of it; it was
  written for the 1.5 A path - 0.5 oz inner copper needs 2.73 mm for 1.5 A at a 10 K rise, the
  board's own arithmetic - and makes **no exception for a nanoamp sense branch that merely shares
  the net name**. Section 17 forbids falling back to 002Q's asymmetric F.Cu route, and a pair with
  one branch internal and one outer is not a matched pair either. **No trunk corridor family was
  generated** - section 20 is downstream of a control reservation that does not exist.
- **A via-override defect was found and fixed:** the FINE_ESC corridor carrying the D-257
  via-geometry override was allocated only for rows with NO area of their own, and the Kelvin rows
  carry `BAT_SENSE_KELVIN` and `BAT_PROT_TAP_U18` - so their 0.35/0.20 vias had no permitting rule
  and DRC answered `via_diameter ... min 0.5000; actual 0.3500`. The override now attaches to the
  corridor the row already has.
- **DECISIONS REQUIRED: (a) SCOPE `BAT_MAIN is outer-layer only` TO CURRENT-CARRYING COPPER** - for
  instance by excluding copper inside the already-bounded, already-named D-249 sense corridors; it
  is a protection-architecture rule and not this task's to change. **(b) Then re-run sections
  11-22** - with the sense pair off B.Cu the control reservation has a real chance at 8/8, and only
  then does the trunk corridor search mean anything. **(c) `LTC_SHDN U18.6 -> R80.2` needs its own
  look** - `NO_LEGAL_ESCAPE` with controls routed first and nothing else on the board.

**No authoritative signal copper or placement ECO was written; the authoritative PCB is six layers
with 0 tracks and 0 vias.** U19 NOT searched. Phase A/B NOT run. B-34 REMAINS OPEN. Converter
routing NOT STARTED. PCB routing 0 %, overall 74 % - **no progress earned by an architecture lock**.

## 2026-08-27 - FBV2-P2-002Q: PR-49 delivered and proven; closing the trunk costs three control pins

**FAIL at section 14.** **The authoritative stackup was NOT changed** - section 18 gates it on
section 14. PCB byte-identical to `adabe98` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper
layers, zero signal tracks, zero signal vias**. All five suites PASS.

- **PR-49 IS DELIVERED, REGRESSION-PROVEN AND DEMONSTRATED TWICE ON REAL COPPER.**
  `BAT_PROTECTED_P R75.2 -> D9.1`: **1.50 mm routed then rejected on `copper_edge_clearance`,
  `LADDER_RETRY` falls to 1.20 mm, and it routes 19.219 mm on B.Cu with zero vias** - exactly
  section 6's expected evidence. A second instance appeared unprompted: `LTC_GATE U18.10 -> Q3.4`,
  0.20 mm rejected, falling to 0.15 mm. **`BAT_PROTECTED_P` now carries `D9.1` in its functional
  island**, closing the split 002P reported.
- **THE RULE IS GENERAL, NOT A BOARD-SPECIFIC HACK.** It lives in one place,
  `route_battery_block.ladder_retry`, so it is regression-tested directly rather than by reading,
  and **G9 in `router_regression.py`** pins all five properties: falls to the next authorised rung;
  **never invents a rung below the ladder**; fails cleanly when every rung is rejected; **does NOT
  walk the ladder on a non-gate failure**; and leaves **no copper behind** (0 -> 5 -> 0 tracks).
  `router_regression`: **ALL CHECKS PASS**, G1-G9. The safety boundary is structural - the retry
  only ever walks the ladder the path role already had, so `PLAN_1_BPP_TRUNK` remains exactly
  **1.50 mm target / 1.20 mm floor**.
- **AND CLOSING THE TRUNK COSTS THREE U18 CONTROL PINS.** On the identical frozen 002P placement,
  002P reported **U18 8/8 with the trunk ABSENT**; with PR-49 laying 19.219 mm of 1.20 mm trunk,
  **U18 falls to 5/8** (`U18.2`, `U18.3`, `U18.7` open). The two results do not conflict - they are
  the same board with one more connection on it. **002P's 8/8 was in part an artefact of a
  connection that never got laid.**
- **THE SECTION 9 KELVIN-ORDERING HYPOTHESIS IS MEASURED FALSE.** Routing the Kelvin taps before
  the trunk gives **U18 4/8**; plan order gives 5/8. The same-net argument is correct and beside the
  point: the taps do not obstruct the TRUNK, they take the pin-field lanes `LTC_UV`, `LTC_OV`,
  `LTC_SHDN` and `FAULT_N` need. **The flag stays in the harness, off, so a rejected hypothesis
  stays reproducible instead of becoming folklore.**
- **Routed Kelvin, best case: 8.667 / 11.130 mm, mismatch 2.463 mm.** The mismatch is comfortably
  inside 5.000 - **but `R75.2 -> U18.8` exceeds the 10.000 mm cap by 1.130 mm**, and
  `R75.1 -> U18.9` takes an F.Cu excursion where section 8 prefers local B.Cu. Section 11's corridor
  topologies were never reached, because ordering - the cheaper instrument section 9 asks for first
  - made things worse. **Analytic Kelvin (7.378 / 7.267, mismatch 0.111) is NOT reported as a pass
  while the routed result fails.**
- **Section 14 PASSES on:** the published stack with In1/In4 one GND island each, D9 legal at
  (13.600, 72.500) rot 0, `R75.2 -> D9.1` at 1.20 mm with zero vias and edge clearance met,
  `BAT_PROTECTED_P` one functional island, the `U11.2` flare, `BAT_SENSE` one island (1.00 mm B.Cu,
  zero vias), `Q3_CS`, `Q3_GATE`, Q3.3 POFV, `LTC_SHDN`, `BAT_RAW` with `U18.1`/`R80.1`/`D12`,
  `BAT_MID` and `Q2_CS`. **It FAILS on:** Kelvin `R75.2 -> U18.8` 11.130 mm, U18 5/8, `LTC_GATE`
  split, `LTC_OV` three islands and `FAULT_N` `[Q9.1, R81.2, R82.1]` vs `[U18.7]`. **Section 15's
  sole-blocker clause does not apply** - FAULT_N is one of four and the cause is shared.
- **Where each width is used:** 1.50 mm is the target and is attempted first everywhere the plan
  asks for it; **1.20 mm is used on `R75.2 -> D9.1` alone**, because that pose puts R75.2's centre
  1.187 mm from the board edge and a 1.50 mm track centred there needs 1.250 mm. The 1.20 mm rung
  is D-249's standing floor, not a new concession.

**U19 NOT searched** (section 20). Phase A NOT run. No battery signal copper. B-34 REMAINS OPEN.
Converter routing NOT STARTED. PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-27 - FBV2-P2-002P: the D9 lever works, BAT_SENSE closes, and the gate fails elsewhere

**DECISION STOP** (section 17). **The authoritative stackup was NOT changed** - section 19 gates it
on section 16. PCB byte-identical to `b803f93` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper
layers, zero signal tracks, zero signal vias**. All five suites PASS.

- **D-261'S D9 LEVER WORKS, AND BETTER THAN THE RULING ASSUMED.** A **0.600 mm** eastward
  relocation of D9 - **placement only**: same part, footprint, orientation, net, polarity and
  topology - frees a **+1.00 mm** rigid-cluster shift, which opens an R75 rot-180 window of
  **x 4.225 .. 4.400** where the **Kelvin mismatch reaches 0.000 mm** with both branches at
  **7.321 mm**. That is the first time since 002I the Kelvin specification has been analytically
  satisfiable at all. Measured: D9 +0.20 and +0.40 free only cluster +0.75; **+0.60 is the minimum**
  that frees +1.00. **`D9.1 -> U11.2` SHORTENS**, 55.344 -> 54.748 mm.
- **`BAT_SENSE Q3.6 -> R75.1` - THE BLOCKER STANDING SINCE 002M - IS CLOSED**: 1.00 mm on B.Cu,
  **zero vias**, one functional island. On the best candidate (D9 +0.600, cluster +0.75, R75
  (4.150, 63.500) rot 180) the probe returns **all nine targets true and U18 8/8**, with **`LTC_OV`
  one component** and `LTC_GATE` one component - **the first board on which all of those hold at
  once** - and **`LTC_OV` closed without moving R77 or R78 at all**, so section 13's refinement
  budget was never spent.
- **A CONSTRAINT THE EARLIER ARITHMETIC MISSED: THE CORRIDOR HAS TO FIT THE TRUNK, NOT JUST THE
  PAD.** The first chain found R75 legal at x=4.125 with D9 moved only 0.200 mm, and the screen
  rejected `BAT_PROTECTED_P R75.2 -> D9.1` with `copper_edge_clearance 0.5000 mm; actual 0.4125 mm`.
  The pad cleared the edge; the **1.50 mm trunk leaving that pad** did not - it needs R75.2's CENTRE
  at least 1.250 mm from the edge, **0.063 mm more than the +0.75 window gives**. Cluster +1.00
  opens it, and that is what the extra 0.400 mm of D9 displacement buys.
- **SECTION 17'S EXACT NEW FIRST BLOCKER: `BAT_PROTECTED_P R75.2 -> D9.1` is rejected at 1.50 mm on
  edge clearance and IS NEVER RETRIED AT D-249'S OWN 1.20 mm FLOOR.** `run()` stops the width ladder
  the moment `connect_role` returns ok and the DRC gate runs afterwards, so a width that routes
  GEOMETRICALLY but fails the GATE is abandoned rather than falling to the next rung.
  `PLAN_1_BPP_TRUNK` carries `[1.50, 1.20]` precisely for this, and the 1.20 rung needs
  R75.x >= 4.063 - which the +0.75 window satisfies. **The rung that would close the trunk is legal
  and simply never tried.** Recorded as **PR-49**, not fixed mid-stop because it changes router
  behaviour board-wide.
- **SECOND BLOCKER: the ROUTED Kelvin detour.** Analytic **7.378 / 7.267**; routed **18.764 /
  7.886**. A routing outcome, not a placement one - the placement is inside spec by a wide margin -
  and the same class 002L recorded at 4.948 mm, now much larger.
- **THE TRADE, PLAINLY:** cluster **+1.00** gives the 0.000 mm Kelvin window and **costs three
  control pins** (`FAULT_N`, `LTC_SHDN`, `LTC_GATE` all rejected on `BAT_MAIN routed clearance` at
  0.2750 / 0.2500 / 0.2778, U18 5/8); cluster **+0.75** keeps **U18 8/8 and all nine targets** and
  puts R75 in the window that cannot host a 1.50 mm trunk.
- **SECTION 18 SHUNT RESERVE NOT TRIGGERED.** It is conditioned on R75 still not fitting after the
  minimum legal D9 move; **it fits**, the window was measured twice, and the analytic mismatch
  inside it reaches 0.000 mm. **No replacement-shunt requirement is produced, and 002O's suggestion
  that a shorter shunt might be needed is WITHDRAWN** - the D9 lever removed that need.
- **Section 15 scan:** D9 could not move less (+0.20/+0.40 free only +0.75); **no test point move
  reduces the displacement** - TP17 and C58 obstruct only from +1.25 mm and none was moved; R75 rot
  180 is both the simpler orientation and the better one (rot 0 gives a 17.4 mm BAT_SENSE run
  against 10.0 mm).

**U19 NOT searched** (section 21). Phase A NOT run. No battery signal copper. B-34 REMAINS OPEN.
Converter routing NOT STARTED. PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-26 - FBV2-P2-002O: the rigid-cluster hypothesis is confirmed and misses by 0.132 mm

**DECISION STOP.** **The authoritative stackup was NOT changed** - section 17 gates it on section 14.
PCB byte-identical to `fcacf0e` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper layers, zero
signal tracks, zero signal vias**. All five suites PASS.

- **D-260'S RIGID-CLUSTER HYPOTHESIS IS CORRECT ABOUT THE CAUSE.** Moving U18 together with
  R76..R83 as one rigid body **eliminates 002N's three control-lane clearance failures** - they do
  not recur. The hypothesis is confirmed; it simply cannot move far enough.
- **THE KELVIN BLOCKER IS NOW CLOSED ARITHMETIC, NOT A SEARCH RESULT.** R75 at rot 0/180 needs a
  **7.75 mm** corridor; the space between the board-edge clearance and the divider column is
  **6.80 mm**. West limit `R75.x >= 4.075` (pad edge at 0.500 mm); east limit at cluster +0.50 is
  `R75.x < 3.925` - **an empty window**. It first opens at **cluster +0.75 mm** (0.100 mm wide) -
  **and +0.75 mm is exactly where D9 overlaps R77 by 0.170 mm.**
- **ONLY CLUSTER +0.50 mm IS LEGAL.** Beyond it **D9** blocks R77 at +0.75 and +1.00; TP17 and C58
  only appear at +1.25. **Section 13's test-point scan therefore has a clear answer: the obstruction
  is D9, a functional diode in the protected high-current path, NOT a test point.** D9 would need to
  move **0.170 mm** east.
- **THE OTHER ORIENTATION, RE-MEASURED WITH THE CLUSTER MOVED: rot 90/270 bottoms out at 5.132 mm
  mismatch against a 5.000 mm limit** (002N measured 5.177 unmoved; the shift bought 0.045 mm).
  Routed anyway, that pose gives **U18 4 of 8** - moving R75 east far enough to improve the mismatch
  puts the shunt under U18's escape corridor. **Both routes miss by less than two tenths of a
  millimetre.**
- **WHAT DID CLOSE: `LTC_OV R77.2 -> R78.1` routed 2.901 mm on B.Cu with ZERO vias** - the section
  11 requirement, met, without moving R77 at all. And **section 11's fallback lock is now enforced**:
  `AQROOT_LTCOV_BCU` denies LTC_OV and LTC_UV the generic layer fallback during qualification, so
  002N's "connected, but 13.087 mm across F.Cu with two vias" **cannot be reported as a pass again**.
- **TWO TOOLING DEFECTS FOUND.** (1) The first pose filter checked courtyards against the outline
  and nothing else, and proposed R75 with its west pad **0.325 mm** from the edge against a 0.500 mm
  clearance - every connection was rejected from the first one and nothing routed; the edge rule now
  applies to the **pads**. (2) The placement guard refused a candidate because the file said `270.0`
  and KiCad reports `-90.0` - **the same pose**; angles are now compared modulo 360, because a guard
  that fires on a difference that is not a difference trains people to ignore it, and this guard
  exists precisely because 002K ran nine screens on the wrong placement.
- **DECISIONS REQUIRED:** (a) **authorise a 0.170 mm eastward move of D9**, which admits the
  +0.75 mm cluster shift and a Kelvin mismatch of ~0.10 mm - a protection-architecture call since D9
  is in the high-current path; (b) **or relax the mismatch from 5.000 to 5.132 mm**, noting the pose
  that achieves it also costs four U18 control pins so this alone does not close the gate; (c) **or
  change the shunt** - R75's 5.925 mm pad pitch is what pins the rot 90/270 mismatch AND what makes
  the rot 0/180 corridor 7.75 mm wide, so a physically shorter 15 mOhm part relieves both at once.
  Raised, not taken.

**U19 NOT searched** (section 20). Phase A NOT run. No battery signal copper. B-34 REMAINS OPEN.
Converter routing NOT STARTED. PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-26 - FBV2-P2-002N: D-259(c) closed, R75 Kelvin solved analytically, gate still FAILS

**FAIL at section 11.** **The authoritative stackup was NOT changed** - section 16 gates the lock on
section 11. PCB byte-identical to `7ff0337` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper
layers, zero signal tracks, zero signal vias**. All five suites PASS.

- **D-259(c) CLOSED.** The derived inner split of 002M is gone; `sixlayer.py` now authors the
  **published JLC06161H-7628** table and the regression asserts those dielectrics - 0.2104 outer,
  0.4000 cores, **0.2028 central prepreg**. Listed materials total **1.5544 mm** (1.5744 with both
  masks). **That is not a discrepancy**: the board is a **NOMINAL 1.6 mm construction**, the vendor
  lists nominal laminate and copper, and the finished board also carries plating, resin flow and
  press tolerance. The regression now RECORDS the total and ASSERTS the published values - it no
  longer tests the sum against 1.6 mm, because that was never the right test.
- **SECTION 18 CLOSED: the datum is 72.000 x 148.000 mm.** `GetBoardEdgesBoundingBox()` reads
  72.100 x 148.100 because it measures to the OUTSIDE of the 0.100 mm Edge.Cuts stroke; 002M quoted
  that artefact as though it were the requirement. Both figures are now reported and the stroke
  subtracted. **Edge.Cuts untouched, no new board-size requirement created.**
- **THE R75 MEASUREMENT THAT MATTERS: translating R75 was never going to fix the Kelvin mismatch.**
  `U18.8` and `U18.9` sit at the **same y**, and R75 is a **5.925 mm** shunt whose pads lie along y,
  so any north/south move changes both Kelvin lengths equally and the mismatch stays at very nearly
  the shunt's own length. Over a +/-8 mm box at 0.5 mm in four rotations, **28 poses reached the
  Kelvin test, ALL rot 90/270, best mismatch 5.177 mm against a 5.000 mm limit.** Turning the shunt
  so its pads lie along x drops the mismatch below 1 mm - and **every rot 0/180 pose is blocked by
  the R80/R81/R82 courtyards at x 7.30. The part costing the Kelvin spec is the divider column, not
  R75.**
- **With the column shifted 1.0 mm east - the measured minimum - R75 gets 8 poses**, best
  **(4.300, 63.500) rot 180, Kelvin 7.772 / 7.000, mismatch 0.771 mm** against a 5.000 limit.
  **But the combination does not hold:** moving the column east puts BAT_MAIN copper into the
  LTC4368 control lanes and three connections are rejected by `BAT_MAIN routed clearance 0.3000` at
  actuals of 0.2750, 0.2778 and 0.2371 mm, taking **U18 to 6 of 8**. The Kelvin fix is real; the
  price is paid one region over.
- **LTC_OV: ONE COMPONENT with a 0.354 mm R78 move** - `(8.825, 69.675) rot 0 -> (8.575, 69.925)
  rot 180`, `R77.2 -> R78.1` 2.26 -> **1.577 mm**, span **8.577 mm**, U18 stays **8/8** and every
  other section 11 item holds. **But `U18.3 -> R77.2` routed 13.087 mm on F.Cu with 2 vias** -
  exactly the long generic layer fallback section 13 forbids, on a high-impedance comparator input.
  **Section 9's secondary lever, a bounded R77 adjustment, is the next instrument and was not
  spent.**
- **A SEARCH DEFECT WORTH RECORDING:** the first R78 run returned `R77.2 -> R78.1 = 0.000 mm` and
  called it the best candidate. That is not a zero-length link - it is R78's pad sitting exactly on
  top of R77's, because R77 was in the movable set and therefore absent from the obstacle list.
  **A search allowed to overlap the part it is connecting to will always report a perfect score.**
- **A HARNESS CHANGE MADE, MEASURED AND DELIBERATELY REVERTED.** `BAT_MAIN routed clearance` fires
  on either side of the pair, so a control track passing a BAT_MAIN PAD looks like it owes 0.300 mm,
  and `margin()` returned 0.200 mm for every pad regardless of net. Raising wide-net pads to
  0.300 mm looked like the fix - **and immediately sealed `U18.8` and `U18.9`**, the two D-249-ruled
  Kelvin taps, both `NO_LEGAL_ESCAPE`. They route legally today at **0.150 mm** under the
  pad-escape necking block, a later and more specific rule, so DRC does not in fact demand 0.300 mm
  there. **Over-applying a clearance is how a legal escape becomes NO_LEGAL_ESCAPE.** Reverted, with
  the reasoning left in the code so it is not re-attempted.
- **Section 11 gate:** PASS on Q3 POFV, Q3_CS, LTC_GATE, Q3_GATE, U18 VIN, SHDN, FAULT_N, R80.1,
  D12, BAT_PROTECTED_P, U11.2 flare and LTC_OV-one-component. **FAIL on `BAT_SENSE Q3.6 -> R75.1`
  (0.2400 vs 0.3000), high-current clearance, Kelvin as routed, LTC_OV local B.Cu, and new DRC
  classes.** **Section 13's U18 reserve was NOT opened** - it is conditioned on both individual
  searches succeeding, and LTC_OV succeeds only in a form section 8 does not accept.
- Impedance register updated to the published inputs; every controlled net marked **PENDING**
  recalculation, with the **NFC transmit arms** still flagged as the real electrical change.

**U19 NOT searched** (section 20). Phase A NOT run. B-34 REMAINS OPEN. Converter routing NOT
STARTED. PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-26 - FBV2-P2-002M: six layers proven on scratch, PR-47 closed, gate FAILS on LTC_OV and BAT_SENSE

**FAIL at section 14.** **The authoritative stackup was NOT changed** - section 16 gates the lock on
section 14. PCB byte-identical to `bc1d436` (md5 `a908cedfa9f9410aab327d8bd55b9f45`): **4 copper
layers, zero signal tracks, zero signal vias**, In1.Cu one filled island. All five suites PASS.

- **SIX-LAYER MIGRATION PROVEN ON SCRATCH.** 6 copper layers in order
  (F.Cu / In1.Cu / In2.Cu / In3.Cu / In4.Cu / B.Cu), explicit **JLC06161H-7628** stackup,
  **1.6028 mm**, **In1.Cu AND In4.Cu each one GND island** built from the same outline, no outer or
  inner-signal pours, outline 72.100 x 148.100 mm - and a **DRC histogram IDENTICAL to the
  four-layer baseline**. The In1 guard was EXTENDED, not weakened: In4 gets the identical GND-only
  rule and `SWITCH_NODE never on In2` is repeated for In3.
- **PR-47 CLOSED ON SCRATCH.** `Q3_CS Q3.3 -> Q3.1` routes **4.626 mm at 0.25 mm on In2.Cu** through
  a filled/capped **0.35/0.20 ordinary THROUGH via-in-pad** at `Q3.3`, with **0.125 mm of pad copper
  remaining each side**; the far end keeps an ordinary via. `Q3_CS` **one component**, `LTC_GATE`
  **one component across all six functional pads**, **U18 8/8** - and the gate drive goes from
  002L's only option, a 15.991 mm F.Cu excursion, to **5.500 mm on B.Cu with ZERO vias**. The
  premium process is spent on **one pad**; no footprint or toe was modified.
- **BUT SECTION 14 FAILS ON TWO NETS, AND IT IS THE SAME TRADE ONE REGION OVER.**
  **`BAT_SENSE Q3.6 -> R75.1`**: `BAT_MAIN routed clearance 0.3000 mm; actual 0.2400 mm` - the
  1.00 mm trunk and the POFV copper want the same corridor, and a wide net cannot be sent inward
  because section 2 keeps high-current copper on outer 1 oz. **`LTC_OV R77.2 -> R78.1`**:
  `NO_VIA_SITE` - **this is section 13's stop condition in substance**, since section 13 forbids
  adopting the long generic F.Cu fallback as the final design. **Six layers removed the Q3 conflict,
  which is what they were bought for**; what remains is a clearance contest over a few square
  millimetres, which is a placement question.
- **U18 six-layer re-screen and the R75 lever were NOT run** - re-screening against a prefix that
  cannot close `BAT_SENSE` or `LTC_OV` would measure the wrong board, and 002K is the standing
  lesson on that.
- **THREE HARNESS DEFECTS, ALL ONE FAMILY - adding layers to a router that had only ever seen two.**
  (1) the obstacle model saw two layers; the copper and routable sets are now DERIVED FROM THE BOARD
  and a through via registers copper on all of them. (2) `connect_hop` sited its via checking only
  `near` and `far` - harmless while those WERE the stack; on six layers it put a via onto another
  net's inner copper and DRC said `shorting_items`. (3) `connect_hop` could only reach F.Cu, so the
  new capacity was unreachable; `far` now defaults to every routable layer except `near` - **and
  never an inner layer for a wide net**, which `BAT_MAIN is outer-layer only` proved three times in
  one connection.
- **THE RULE CORRECTION, A SECOND TIME:** the D-257 escape corridors were emitting a 0.20 mm
  clearance floor alongside their via-geometry override; the corridor is grown from the track with a
  0.3 mm tolerance, so it swallowed neighbours and the floor fired on pairs it never meant to govern
  - `LTC_OV` was rejected by a rule named after `LTC_GATE`'s escape. **A relaxation applied where
  nothing needed relaxing is a restriction.** Escape corridors now carry **via geometry only**.
- **PR-48 RE-VERIFIED on six layers:** `U18.1` VIN in the BAT_RAW main island; `U14.2`, `U14.3` and
  `TP15.1` all in the `BAT_PROTECTED_P` trunk island.
- **POFV FABRICATION NOTE and IMPEDANCE IMPACT REGISTER** written to
  `architecture/FBV2_SIXLAYER_STACKUP.md`. The via is **PLATED OVER FILLED VIA** - not tented, not
  mask-plugged, not open, not blind, not a microvia - recorded as a process order because Gerbers
  alone do not force it. **No impedance width is claimed unchanged**; every controlled net is
  scheduled for recalculation, and the **NFC transmit arms** are flagged as the real electrical
  change (reference moves from across a 1.065 mm core to In4 at 0.2104 mm).
- **HONEST LIMIT ON THE STACKUP NUMBERS:** the outer 0.2104 mm 7628 prepreg is carried from
  JLC04161H-7628; the **inner distribution is DERIVED** to total 1.6 mm and **must be confirmed
  against JLCPCB's published table before Gerbers are ordered**.
- Mechanically inert and re-measured as such: outline 72.100 x 148.100, 1.6 mm nominal, footprints
  unchanged, `p1_regression` PASS on every boss, keepout, envelope and connector check.

**U19 NOT searched** (section 20). Phase A NOT run. B-34 REMAINS OPEN. Converter routing NOT
STARTED. PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-26 - FBV2-P2-002L: PR-48 and D-257 proven, PR-47 is a via-in-pad decision

**DECISION STOP** (section 17: *"If Q3 requires via-in-pad: 002L = DECISION STOP, not PASS"*).
**No authoritative copper**; PCB byte-identical to `cb17269` (md5 `a908cedfa9f9410aab327d8bd55b9f45`),
**zero signal tracks, zero signal vias**, In1.Cu one filled island. All five suites PASS.

- **PR-48 PROVEN.** A local `clearance (min 0.20mm)` conditioned on net AND bounded corridor
  resolves all three measured cases: **`U18.1` VIN 10.107 mm at 0.20 mm** (was
  `clearance 0.3000; actual 0.2500`), **`U14.2` 7.401 mm at 0.15 mm** (was 0.2347), **`U14.3`
  joined** (was 0.2350). `BAT_PROTECTED_P` becomes ONE island including `U11.2`, `U14.2`,
  `U14.3`, `TP15.1`, `U18.8`. Minimum measured clearance 0.200 mm, no new DRC class.
  **AND A CORRECTION:** the first cut also covered `BAT_PROT_TAP_U18` and `BAT_SENSE_KELVIN`,
  which were already running legally at **0.150 mm** - so the "relaxation" RAISED the floor on
  compliant copper and rejected every connection after it. **A relaxation applied where nothing
  needed relaxing is a restriction.**
- **D-257 PROVEN ON THE PREFERRED GEOMETRY.** Every D-256 escape is carried by the **0.35/0.20
  ordinary through via** - LTC_GATE x4, LTC_SHDN x2 - and **the 0.25/0.15 reserve was never
  needed**. No microvia, no blind or buried via. Verified before adoption: a 0.35/0.20 via inside
  a named corridor reports `via_diameter` + `annular_width` without the rules and nothing with
  them; no other class moves.
- **U18 SEARCH: FIVE POSES SCREENED, NONE CLOSES.** The **authoritative** pose routes **8 of 8**
  and misses Kelvin (straight-line 2.440/8.265, **mismatch 5.825** against a 5.000 limit); the
  **002F ECO** pose has Kelvin 4.464/4.464/0.000 and routes **6 of 8**; C01/C02 **5 of 8**; C03
  **7 of 8**. **Most of the authoritative pose's Kelvin failure is ROUTING, not placement** - it
  misses by **0.825 mm straight-line** and carries a further **4.948 mm of detour** on
  `R75.2 -> U18.8`. **The lever section 6 held back is R75**, fixed "initially" and sitting in the
  1.5 A path, so it is surfaced rather than taken.
- **PR-47: ORDINARY VIAS ARE MEASURED IMPOSSIBLE.** Q3 is `SOIC-8_3.9x4.9mm_P1.27mm` - 1.270 mm
  pitch, 1.950 x 0.600 mm pads, **0.670 mm copper gap** - with `Q3_CS` on pins 1/3 and `LTC_GATE`
  on 2/4 sharing one B.Cu slot. **`Q3.3` has NO LEGAL ESCAPE at 0.25, 0.20 OR 0.15 mm**, blocked
  by `Q3.2` (x27) and `Q3.4` (x20); both D-257 geometries and all three widths return
  `NO_LEGAL_ESCAPE`. **A via needs a landing site and a landing site has to be REACHED from the
  pad** - the via's size is irrelevant. **Section 13 geometry check: a filled/capped through
  via-in-pad at 0.35/0.20 FITS, with 0.125 mm of pad copper each side**, the 0.670 mm pad gap
  unchanged and adjacent drills 2.540 mm apart. Feasible and premium - hence the stop.
  **Section 14 alternative, recorded not taken:** a Q3 toe extension of **>= 0.40 mm**.
- **SIX-LAYER ASSESSMENT TRIGGERED (non-destructive, nothing applied).** 1.6 mm retainable, **P1
  mechanical evidence stays valid**, two extra signal layers plus a second GND reference relieve
  U18 directly - **but it does NOT solve PR-47**, because `Q3.3` still has no B.Cu escape.
- **PROCESS FIX (section 2):** `checks/placement_fingerprint.py` prints the pose of U18, R75,
  R76-R83, Q2, Q3, U14, U19 at the head of every screen and `AQROOT_EXPECT_PLACEMENT` makes it an
  assertion that **fails before routing**; the candidate loader reads the SAME file the assertion
  checks. All eleven screens ran under it, and it caught its first defect immediately - a
  candidate with three courtyard overlaps that the geometric filter had cleared against a board
  the screen would never see.
- Standing **section 11 flag**: `LTC_OV` reached F.Cu through the ordinary fallback (2 vias at
  0.60/0.30) and split `R78.1`. High-impedance comparator input; not the only blocker; not moved
  silently.

**U19 NOT searched** (section 16). Phase A NOT run. B-34 REMAINS OPEN. Converter routing NOT
STARTED. PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-26 - FBV2-P2-002K: D-256 is right, and its instrument does not fit U18

**FAIL** at section 9. **No authoritative copper**; PCB byte-identical to `a5771a7`
(md5 `a908cedfa9f9410aab327d8bd55b9f45`), **zero signal tracks, zero signal vias**, In1.Cu one
filled island, placement ECO still not applied. Preflight all PASS.

- **THE ANSWER: the west margin IS short of layer capacity exactly as D-256 ruled - and at the
  FBV2-P2-002F placement the two pins that need the extra layer CANNOT REACH A VIA.**
  `U18.10`: escape 0.20 mm, one direction, and **no reachable through-via site at 0.60, 0.55,
  0.50, 0.45, 0.40, 0.35, 0.30 or 0.25 mm** - the smallest that fits is **0.20 mm**, which is
  `min_microvia_diameter`, not a through via. `U18.7`: **NO legal escape at 0.25, 0.20 OR
  0.15 mm**, blocked by `U18.8` and `U18.6`, its own adjacent pads. A layer change needs a via;
  a via needs somewhere to land; **U18 is an MSOP-10 on 0.50 mm pitch and the board's floor is
  `min_via_diameter` 0.50 mm.**
- **ON THE AUTHORITATIVE PLACEMENT THE SAME STRATEGY WORKS**, and that contrast is the finding:
  `LTC_GATE U18.10 -> R76.1` **8.794 mm F.Cu / 2 vias / 2 s** (was NO_PATH at 26 s),
  `U18.10 -> Q3.4` 15.552 mm, `LTC_SHDN U18.6 -> Q4.3` **24.525 mm at 0.25 mm** (was rejected),
  FAULT_N all four functional pads one island **on B.Cu unaided**, **LTC_GATE ONE ISLAND across
  all six functional pads - the first time with PR-43 in force** - and **U18 6/8 -> 7/8**.
  `BAT_PROTECTED_P` 167.401 mm with **zero vias**.
- **PLACEMENT ERROR, CAUGHT AND CORRECTED IN-TASK:** the first nine screens ran without
  `AQROOT_ECO_002F`. Section 14 caught it - Kelvin came out **3.179 / 13.152 mm, 9.973 mm
  mismatch** against 002I's 4.464 / 4.464 / 0.000. Repeated on the ECO placement; both sets are
  reported and labelled.
- **THREE HARNESS DEFECTS FIXED.** **PR-45**: `connect_hop` chose its via site by "closest point
  a via fits" instead of "closest point a via fits THAT THIS PAD CAN REACH" - for `U18.10` it
  returned a site 2.30 mm away on the far side of the copper the pin was escaping past; it now
  floods the near layer from the escape point, and rejects sites that break `min_hole_to_hole`.
  **PR-46**: two silences - every hop failure was reported as `NO_PATH: no F corridor` even when
  the far layer was never attempted, **and a connection rejected by the DRC gate was reverted and
  requeued with NO LOG LINE AT ALL**. Both now report. **D-249 corridor rule areas now span both
  outer layers** - they existed on B.Cu only, so an F.Cu escape by a ruled tap fell outside its
  own corridor and was judged against the 0.60 mm class floor.
- All five suites re-run after the harness changes: **PASS**.
- **U19 search NOT PERFORMED** - section 11 gates it on the section 9 screen. **Phase A, Phase B,
  manifest and authoritative write NOT PERFORMED.**
- **NEW CTO ISSUES.** **D-257**: D-256's instrument does not fit U18's pin field - microvia /
  via-in-pad (a reachable **0.20 mm** site exists 1.20 mm out from `U18.10`), a land-pattern
  change, moving U18 (forbidden by section 7), or accepting `U18.7`/`U18.10` unrouted.
  **PR-47**: the Q3 south row is a **proved land-pattern conflict** - `Q3_CS` (pins 1, 3) and
  `LTC_GATE` (pins 2, 4) interleave with one B.Cu slot and in all three orderings measured the
  loser's middle pad has no escape at any width on either layer. **PR-48**: D-249 relaxes WIDTH,
  not CLEARANCE - `U18.1` and the U14.2/U14.3 branches are all blocked by
  `BAT_MAIN routed clearance` (0.300 mm required, 0.250 / 0.2347 / 0.2350 mm actual).
  **Section 6 flag**: `LTC_OV` reached F.Cu through the generic fallback (13.604 mm, 4 vias) and
  it is a high-impedance comparator input.
- 11 screens, one at a time, 501-890 s each, ~1.8 h. **No cloud-vs-PC speedup claimed** - the
  committed PC figures are for unlike workloads.

B-34 REMAINS OPEN. Converter routing NOT STARTED.
PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-26 - FBV2-CLOUD-001: the harness becomes reproducible on a second machine

**PASS. INFRASTRUCTURE / TOOLING ONLY - NO PCB PROGRESS EARNED.** No schematic, no copper, no
placement, no architecture. Authoritative PCB byte-identical to `a1cc687`; **0 signal tracks,
0 signal vias.** All five suites PASS on Ubuntu 24.04 / KiCad 10.0.5.

- **The problem:** every FBV2-P2 verdict, 002A through 002J, was measured on ONE Windows
  workstation. Four active scripts had that machine's disk baked in as literals
  (`P:/New folder (2)/bin/kicad-cli.exe`, `P:/Vaults/ClaudeVault/AQROOT/...`,
  `"<KICAD>/bin/python.exe"`). **13 active portability defects** found and tabulated.
- **The dangerous one:** `router_regression.py` had a `KICAD_CLI` override, but its DEFAULT was
  the Windows path. Unset on Linux it yielded a nonexistent tool, and both DRC call sites use
  `subprocess.run(capture_output=True)` with no returncode check - so "the DRC tool is absent"
  looked like an I/O error, **inside the script that gates authoritative copper.** That is the
  G1 class from 002A, one layer down.
- **New `checks/harness_paths.py`** - one policy each. **kicad-cli:** `KICAD_CLI` ->
  `shutil.which` -> documented Windows fallbacks (`os.name=='nt'` only) -> **loud `SystemExit`,
  never a silent default.** **project dir:** `AQROOT_BETA_V2_PROJECT`, else derived from
  `__file__` (`checks/ -> beta-v2/ -> hardware/ -> repo root`) - no username, mount point, home
  directory or vault path. **interpreter:** `sys.executable`, always.
- **Windows is a strict superset**, verified statically: the old machine still resolves at the
  fallback with zero configuration; `C:\...\kicad-cli.exe` passes verbatim into `subprocess.run`;
  no Linux-only literal is mandatory anywhere.
- **`.kicad_prl` REMOVED from fork equivalence.** It is per-user KiCad editor state, gitignored
  since before the fork, and `beta-dm` has none at all - the probe was asserting a property of
  one person's KiCad session. **No fake `.prl` generated, none committed, `.gitignore` unweakened.**
- **`checks/requirements.txt`**: `numpy>=1.24` and nothing else. `pcbnew` deliberately excluded -
  it comes from KiCad, not pip, and the file says so.
- **KiCad 10's Ubuntu `PROPERTY_ENUM` assertion noise is NOT suppressed** - hiding it would hide
  the next real error. Judged on exit status and results.
- `p1_regression` PASS, `router_regression` **ALL CHECKS PASS** (G1-G7 + G8-A..F; also PASS with
  `KICAD_CLI` unset), `dru_probe` PASS, `netclass_probe` PASS, `fork_equivalence` PASS.

B-34 REMAINS OPEN; D-256 still awaits the CTO. FBV2-P2-002K NOT STARTED.
PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-26 - FBV2-P2-002J: the R80/R81 lever fails, and PR-44 unblocks Phase A

**FAIL.** No authoritative copper; board byte-identical to `984423c`. Preflight all PASS.

- **Section 5 local screen built and VALIDATED** (`AQROOT_LOCAL=R80`): 19 named connections,
  reproduces D-255 exactly (U18 6/8, open `U18.7`/`U18.10`) in **471 s vs ~2 h** - 15x cheaper.
  Sound because the copper boxing `U18.7` is the `LTC_SHDN` `U18.6 -> R80.2` run, inside the U18 field.
- **Six R80 poses screened.** `R80.1` and `D12.1` connected in every one. **None reached 8/8.**
  K6 (R80 8.000,68.000 r180 / R81 5.500,70.500 r90) is the only one closing BOTH D-255 pins.
- **Two full Phase A runs, both worse than doing nothing**: K6 **20/29** (`Q3_CS` splits -
  section 12 protects it), K1 **22/29** (`LTC_GATE` fragments into five islands).
- **The 002I baseline of 24/29 stands.** Across 002I+002J, one reordering and seven
  placements have all landed at or below it.
- **Section 10 via reserve NOT triggered** - `U18.7` is the easy pin. **The section 10 stop
  condition IS met**: `LTC_GATE` degrades under every R80/R81 move. Stopped for CTO review.
- **U19 search NOT performed** - section 9 needs an R80/R81 winner first.
- **PR-44 CLOSED**: `apply_areas` called `GetClass()` on PCB_TRACK objects freed by a revert -
  a deterministic SIGSEGV at connection 28 that killed two full Phase A runs. Store UUIDs and
  resolve against the board. `router_regression` ALL CHECKS PASS.

CTO decision required (D-256): the margin is short of layers, not lanes. B-34 OPEN.
PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-26 - FBV2-P2-002I: PR-43 answered - BAT_RAW closes, U18 loses two pins, the margin is full

**FAIL on section 5 Case D.** No authoritative copper; board byte-identical to `984423c`.
Preflight all PASS (p1_regression, router_regression 34 incl. G8-A..F, dru_probe,
netclass_probe, fork_equivalence; DRC 1 baseline violation; ERC 0).

- **PR-43 WORKS.** `BAT_RAW` goes to 11-of-12 pads in one island - `R80.1` and `D12.1` both
  CONNECTED - with **no placement change**. `LTC_SHDN`, previously NO_PATH, closes too.
- **And it costs U18 8/8 -> 6/8**: `U18.7` NO_LEGAL_ESCAPE, `U18.10` NO_PATH. Section 9
  protects both, so this is a Case D stop.
- **The blocking copper is not `BAT_RAW`.** Beside `U18.7` sit `LTC_SHDN` and
  `BAT_PROTECTED_P` at 0.500 mm; beside `U18.10`, `BAT_SENSE` at 0.500 mm. PR-43 unblocked
  `LTC_SHDN`, whose new route took `U18.7`'s lane. **Capacity, not ordering** - both
  orderings score 24 of 29, and reordering moves the casualty rather than removing it.
- **PR-43 flagged, not adopted** (`AQROOT_PR43=1`). The default keeps U18 at 8/8.
- Improved and worth keeping: **Kelvin 4.464/4.464 mm, mismatch 0.000 mm** (was 2.454);
  `U18.1` VIN 1.752 mm. Held: `BAT_PROTECTED_P` one island / 0 vias / 1.50 mm, `Q3_CS` and
  `Q2_CS` 0 vias, `U11.2` neck 0.20 mm no via, `U14`+`TP15` connected, 0 out-of-scope copper.
- **U19 search NOT performed** - section 6 requires Case C.

CTO decision required (see D-255). B-34 OPEN. PCB routing 0 %, overall 74 % - unchanged.

## 2026-08-25 - FBV2-P2-002G / 002H: routing truth (PR-39), full-prefix qualification (PR-40), and the BAT_RAW contention

**FAIL. No authoritative copper written; the placement ECO is still not applied.** The
authoritative PCB is byte-identical to `984423c` (md5 `a908cedfa9f9410aab327d8bd55b9f45`).
Rollback tag `beta-v2-p2-battery-pre-authoritative` created at `984423c` and pushed.

- **PR-39 CLOSED** - router success now means the *requested* pads are one connected
  component. A retarget that leaves the named pad isolated is reverted and does not count.
  Six regression cases G8-A..G8-F, all passing. `checks/net_ledger.py` makes connectivity
  the primary truth; the routed count is secondary.
- **PR-40 IMPLEMENTED** - qualification is the full prefix (`AQROOT_PROBE_PASS1`), not
  bare-board escape, simultaneous stubs, or a reduced prefix. Cost ~40 min/candidate.
- **PR-41 CLOSED AND VALIDATED** - the closure stage gave every `BAT_RAW` pad the trunk
  ladder because `BAT_RAW` is a WIDE net; the 0.20 mm divider chain was asked for 0.60 mm.
  Zero `NO_LEGAL_ESCAPE` board-wide afterwards. Not sufficient on its own.
- **PR-42 CLOSED** - a stray `break` made the 'joint' U19+R80/R81 search share one R80/R81
  pose across all eight candidates. Fixed: six distinct R80 poses; the two independent axes
  are swept separately. `AQROOT_SEARCH_ONLY` regenerates candidates without probing.
- **MEASURED** - a bare-board flood (negative test only) shows both `BAT_RAW` bridges reach
  the battery node at 0.20 mm. The corridor exists; the failure is contention, not geometry.
  This reverses the part of PR-34 that assumed R80 needed a placement search.
- **PR-43 APPLIED, UNPROVEN** - schedule by corridor scarcity, not net role: the 21.5 mm and
  45.5 mm divider-chain bridges now route with the chain instead of after U18's pin field.

Phase A not passed, Phase B not run, no manifest. B-34 remains OPEN. PCB routing 0 %,
overall Full Beta v2 74 % - unchanged.

## 2026-08-25 - resumed FBV2-P2-002F: three harness defects, 24 of 29 nets (FBV2-P2-002F cont.)

**Still FAIL, and the authoritative PCB is still byte-identical to `24f6611`.** Phase A run 8:
**71 connections, ratsnest 781 -> 708 (-73), DRC identical to the baseline, zero out-of-scope
copper, 24 of 29 in-scope nets single connected components** (was 23).

### Two fixes held

**PR-37.** The closure stage handed every `BAT_PROTECTED_P` pad the TRUNK ladder `[1.50, 1.20]`,
ignoring D-249's per-pad rulings, and so asked a 0.70 x 0.30 mm MAX17048 pad for 1.20 mm. The pads
escape fine at 0.15 mm - measured - and the island sat **10.862 mm** from `C58.1`. It was never a
corridor problem. `BAT_PROTECTED_P` is now ONE component, and the same fix closes PR-35.

**PR-38.** `order_tight` measured only the FIRST-NAMED pad of a connection. U18's pin field is
written pin-first so that worked; the dead-cell block is a minimum spanning tree, so
`TP24.1 -> U19.2` measured a 1.0 mm test pad with three ways out and never looked at the SOT-23-8
pin with one. A connection is as tight as its tighter end. `REF_POL` closed.

### PR-39 - the defect that matters most

`TAP BAT_RAW R79.1 -> R80.1 5.276 mm` is **not what was built.** Those pads are **12.030 mm**
apart, and the number of `BAT_RAW` track endpoints inside `R80.1`'s pad is **zero**. `run()`'s node
fallback silently retargets to the nearest point on the net's own copper while the log line and the
journal keep the original pad name - so a "successful" connection laid a redundant loop and left
the pad alone.

**Section 14 must be judged on connectivity, never on the routed count**, and a section 17 replay
would faithfully reproduce a connection that does not exist.

### And a correction

This document briefly recorded that U19 does not need to move, on the grounds that all seven of its
signal pins escape on the bare board and survive the section 3C simultaneity test. **Run 8
disproves it** - the casualty simply moved from `U19.2`/`U19.3` to `U19.3`/`U19.8`. That is
precisely the signature PR-25 named, and bare-board escapes are exactly the inference this task has
shown to be unsound. **PR-34 stands as originally written: U19 needs the measured placement
treatment PR-25 gave U18, and so do R80/R81.**

What is left is three pads - `R80.1`, `U19.3`, `U19.8` - all west-margin placement, plus two test
points (`TP18.1`, `TP19.1`) that escape with 8 and 5 directions and were simply never reached.

## 2026-08-25 - the placement question is answered, the block still does not close (FBV2-P2-002F)

**FBV2-P2-002F = FAIL.** Phase A did not complete, so Phase B never ran and
`aqroot-Beta-v2.kicad_pcb` is byte-identical to `24f6611`: zero tracks, zero signal vias. **The
placement ECO is NOT applied to the authoritative board** - section 23 forbids committing an
unproven placement, and a placement that does not pass section 13 is not proven. PCB routing stays
0 %, overall stays 74 %. Full analysis:
[`audits/2026-08-25-p2-battery-placement-eco.md`](audits/2026-08-25-p2-battery-placement-eco.md).

### PR-25 is closed, and closed by measurement

U18 rotates **90 -> 180** and moves **(3.000, 72.400) -> (8.000, 65.250)**. At 002E's pose it sat at
x 1.205..4.795 with R75 immediately south and the R76..R83 divider wall at x 7.300..10.350: every
north-row pin escaped through the same **2.505 mm** corridor, and R75's own 3.35 mm pads stood
between `U18.8` and its Kelvin target. **6 of 8 pins escaped, 7 at best.**

At rot 180 the pin rows face east and west and U18 straddles R75's midline, so `U18.8` and `U18.9`
look straight at `R75.2` and `R75.1`. **8 of 8 escape and 8 of 8 route.** The divider *wall* is
gone - every part is now placed by the U18 pin it serves.

The pose came from 13 284 candidates: 2 490 cleared collision and the section 4 Kelvin envelope,
1 331 kept both Kelvin branches under 10 mm with a legal 1.50 mm trunk, 20 were fully scored, and
the winner was re-confirmed by **routing all eight pins with the real router** against the real
trunk, chain and flare.

### `Q3_CS` closes with zero vias, and the authorised via was declined

Section 5 authorised one `Q3_CS` layer drop. It was measured across four variants of the same
prefix and **not taken**: CS-before-gate closes all twelve connections at Q3 on B.Cu with no vias;
moving Q3 1 mm loses **both** CS nets; and the authorised drop **cannot even start**, because
`Q3.3` has no B.Cu escape left once the gate has routed. The whole price is **2.188 mm** on one
gate link. `LTC_GATE`, which 002E left in two pieces, is now **one connected component**.

### The numbers

| target | 002E | 002F |
|---|---|---|
| U18 signal-pad escapes | 6 of 8 | **8 of 8, all routed** |
| R75 Kelvin mismatch | 20.620 mm | **2.454 mm** |
| `U18.1` VIN tap | 32.204 mm | **1.850 mm** |
| `U14.2` branch | 31.228 mm | **6.387 mm**, U14 did not move |
| worst megohm dead-cell node | 64.01 mm | **18.43 mm** |
| `Q3_CS` | `NO_LEGAL_ESCAPE` | **5.500 mm, zero vias** |
| connections on one scratch board | 60 | **70** |
| ratsnest | 781 -> 718 (-63) | **781 -> 709 (-72)** |
| in-scope nets fully connected | - | **23 of 29** |

DRC was identical to the baseline after every single connection, and there is zero out-of-scope
copper.

### Why it still fails

Section 14 allows no partial pass. Six nets sit in two islands and **four of them are one stranded
pad** - `R80.1`, `U19.2`, `U19.3` - plus the `{TP15, U14.2, U14.3}` MAX17048 island. `U19.2` and
`U19.3` are a U19 placement question of exactly the kind PR-25 answered for U18 (**PR-34, open**).

### Four harness rulings, and one lesson

**PR-30** fine-pitch slack ties break on how many ways out a pad still has. **PR-31** a partner must
sit on the side its pin faces, or the route wraps the package - `U18.10` cost 18.4 mm and took
`U18.2`'s only lane with it. **PR-32** re-measure before every fine-pitch pin. **PR-33** U19 is an
SOT-23-8 on 0.65 mm pitch and had no measured ordering at all; giving it one recovered three pins.

The lesson underneath all four: **an escape proof measures a 0.5 mm stub and a connection is a
route.** Four placements passed the section 12 gate - including its section 3C simultaneity test,
49 escapes laid at once with none lost - and then failed Phase A. The fix was not a better proxy
but a worse-scaling one: route the pin field with the real router, against the copper the plan lays
first.

**B-34 stays open.** Scratch pack-current copper is approximately 64.9 mOhm, essentially unchanged
from 002E, so the ECO cost the load path nothing. Physical validation remains mandatory.

## 2026-08-25 - the block routes, the pin field does not (FBV2-P2-002E)

**FBV2-P2-002E = FAIL.** Phase A did not complete, so Phase B never ran and
`aqroot-Beta-v2.kicad_pcb` is byte-identical to `e09eb35`: zero tracks, zero signal vias. PCB
routing stays 0 %, overall stays 74 %. Full analysis:
[`audits/2026-08-25-p2-battery-authoritative-route.md`](audits/2026-08-25-p2-battery-authoritative-route.md).

**First unresolved FUNCTIONAL connection: `BAT_RAW` `R80.1 -> Q2.7`. Most consequential:
`LTC_GATE` `U18.10 -> Q3.4`.**

### 60 connections, ratsnest -63, and a DRC that never moved

The previous best was 27 connections and -32. This run closed the whole high-current path end to
end - `J4 -> F1 -> Q2 -> Q3 -> R75 -> D9 -> U11.2` - with the `BAT_PROTECTED_P` trunk at its
**1.50 mm target on B.Cu carrying zero vias**, both R75 Kelvin branches, the U11.2 flare, the
MAX17048 taps, and **the dead-cell / recovery network for the first time**. DRC after every single
connection was identical to the baseline: no new violation of any class, ever.

### A segmentation fault, and four more harness defects

`split_at()` replaces one track in `qb.laid` with two, and the mark taken before it is an index
into that same list. Nothing shifted the mark, so `revert()` removed a track belonging to the
**trunk** and left one of the branch's own behind - and a second revert on the same trunk called
`BOARD::Remove` on an item no longer in the list, which segfaults rather than raising. Exit 139 at
`TP34.1`, 55 connections in, with no Python traceback because only the watchdog was armed.

Fixed, made undoable, `faulthandler.enable()` turned on, and pinned by a new **`router_regression`
G7** that checks the arithmetic rather than waiting for a crash. Also fixed: an item budget that
starved the F.Cu fallback and made the router look nondeterministic (**PR-20**); trunks silently
dropping width to buy a layer hop (**PR-21**); and an already-connected check that read a FILE
still holding reverted copper, so connections that had never been routed were counted as done
(**PR-22**).

### Ordering is section 8's, and inside the pin field it is measured

Putting U18's pin field before the trunk let a 0.20 mm sense tap take the 1.20 mm trunk's only
escape from `R75.2` - and copper on this board only accumulates, so no later pass can give it back.
Section 8's order (trunk first) is what buys the 1.50 mm trunk. Inside the pin field there is no
right fixed order at all: three hand-picked ones each moved the casualty. It is now measured by
binary search once per pass, tightest pin first. And section 9's gate-before-CS is proved on Q3,
where the CS route threads both 0.67 mm gaps and leaves `Q3.2` with no escape on any layer.

### What is left is placement, not routing

Nine of the fifteen open connections failed `NO_LEGAL_ESCAPE` at 0 s - the pad cannot emit a legal
track at any width on any layer before pathfinding is even attempted. **U18 escapes 6 of its 8
signal pins here, 7 at best**, because its whole north row shares one ~2.2 mm corridor between the
package and the R76/R77/R78/R79 divider wall. That is **PR-25**, and it needs a placement ruling
rather than another routing attempt. Section 11 forbids weakening the architecture to finish, so
nothing was dropped, re-aimed or re-valued.

**B-34 is not recalculated authoritatively and stays OPEN.** **PM-2 does not close.**

## 2026-08-24 - width becomes a path role, and the board still says no (FBV2-P2-002C)

**FBV2-P2-002C = FAIL.** Phase A did not complete, so Phase B never ran and
`aqroot-Beta-v2.kicad_pcb` is byte-identical to `a52977e`: zero tracks, zero signal vias. PCB
routing stays 0 %, overall stays 74 %. Full analysis:
[`audits/2026-08-24-p2-battery-authoritative-route.md`](audits/2026-08-24-p2-battery-authoritative-route.md).

**First unresolved connection: `LTC_GATE` `Q2.2 -> TP17.1`.**

### D-249: width is a path role

D-245 said `BAT_PROTECTED_P` should be 1.50 mm because it is the one long high-current run. That is
still right. What was wrong is that the rule said it about the NET NAME, and the same net also feeds
the MAX17048 fuel-gauge sense input, the LTC4368 VOUT sense input and a test point - none of which
carries load current, and none of whose land patterns can accept 1.20 mm. **As written, D-245 made
the net unroutable.**

The replacement keeps the trunk floor on the whole net and relaxes it ONLY inside a named rule area
that bounds one approved branch, through `enclosedByArea()`, which requires the WHOLE track to be
inside. A branch that wanders out of its area is measured against the trunk floor and fails.

**Where those rules live turned out to matter as much as what they say.** Section 9 of `.kicad_dru`
already records that KiCad applies the LAST matching rule and that the necking and land-pattern
blocks must sit at the end. Put the path-role rules in section 5b and they are silently overridden
by *"Pad-escape necking - width, fine-pitch power packages"* - which is exactly the trap section 9
was written to warn about. They now live in a new **section 10b at the very end**, widest first and
narrowest last so that overlapping areas resolve to the lower floor instead of a false violation.

### U11.2 did not need the 0.19 mm exception

Section 6 authorised dropping to 0.19 mm if 0.20 mm proved impossible. It is not impossible.
**TI's own DLH0010A land pattern is 0.2 mm pads on 0.4 mm pitch**, so 0.20 mm is the widest copper
that can ever leave that pad - the package is the bottleneck, not the rule - and JLCPCB's live
capability page gives 0.09 / 0.09 mm on 1 oz multilayer, so nothing here is fab-limited. The earlier
"0.195 mm" was an artefact of the router subtracting half a sampling step; with exact
segment-to-shape geometry the answer is **exactly 0.200 mm**.

The measured escape: **0.20 mm for 0.575 mm**, then 0.30, 0.40, 0.60, 0.80, 1.00 and 1.20 mm,
reaching the 1.50 mm trunk 5.079 mm from the pad. No via, no thermal relief, about 4.3 mOhm.

**One part of section 6 is NOT met and is flagged rather than smoothed over.** The neck complies at
0.575 mm against the 1.00 mm cap, but the copper BELOW the 1.20 mm trunk floor runs 4.738 mm. It
cannot be shorter: the nearest point to U11.2 that admits 1.20 mm *and is reachable from the rest of
the net* is 2.511 mm away.

### U14 misses 0.20 mm by five microns

`U14` sits 1.245 mm from the west board edge with its pin row facing that edge. Copper must be
>= 0.500 mm from the edge and >= 0.200 mm from pads whose west edge is at x = 0.895, so a track of
width w needs its centre at x >= 0.500 + w/2 AND x <= 0.695 - w/2 - solvable only for
**w <= 0.195 mm**. Section 5 locked 0.20 mm. It routes at **0.15 mm**, the board's own minimum and
1.7x JLCPCB's, carrying a nanoamp sense input. Flagged for ratification.

A related fix caught a violation on the way: the router now insets the board outline by half the
Edge.Cuts stroke, because copper-to-edge clearance is measured to the LINE, not to the outside of
the stroke. That 25 um is what turned a 0.475 mm edge clearance into a caught error rather than a
committed one.

### What routed

Twenty-seven connections coexisting on one scratch board, each gated on project-context DRC with the
In1 plane refilled every time: the `BAT_PROTECTED_P` trunk `R75 -> D9 -> U11.2` at **94.5 mm,
1.50 mm, B.Cu, ZERO vias**; `BAT_CONNECTOR_P`, `BAT_RAW` and `BAT_MID` at 0.80-1.00 mm; both R75
Kelvin branches at 0.20 mm with zero vias, **7.327 mm on the U18.9 side against 14.588 mm on the
U18.8 side, mismatch 7.261 mm**, both taken directly off the correct R75 pad; the fuel-gauge and
test taps; and three of the six LTC gate connections. Ratsnest 781 -> 749. **Zero new DRC violations
of any class, at every step.**

The only vias in the whole attempt are **four**: the `BAT_SENSE` `Q3 -> R75` trunk and the TP20 stub
hop to F.Cu, because the west margin cannot carry both that trunk and the 1.50 mm
`BAT_PROTECTED_P` past R75 on B.Cu alone.

### B-34 from real copper, and it is worse

Routed copper is **~75.0 mOhm**, not the ~50.6 mOhm the estimate assumed. With F1 at ~25 mOhm,
Q2+Q3 at ~46 mOhm and the BQ25185 BATFET at 115 mOhm the path is **~392 mV / 588 mW at 1.5 A** and
**~457 mV / 800 mW at 1.75 A**. The trunk is at its ruled 1.50 mm; the excess sits in `BAT_MID` and
`BAT_SENSE`, which the corridors forced to 0.80 mm instead of the 1.00 mm class target.
**B-34 stays OPEN - physical validation required.**

### And one weakness worth naming

Section 7 asked that the construction make it IMPOSSIBLE for a long high-current run to masquerade
as a branch. It does not fully manage that yet. The bounded areas are generated from each routed
branch's own bounding box, and three of them are tight - but the C58 decoupling tap's box is
**67 x 23 mm at a 0.80 mm floor**, which is a real hole in the trunk rule. The fix is to build the
area from the route's centre-line rather than its bounding box. That is a router change, not a rule
change, and it is carried as PR-11.

---

## 2026-08-24 - the router on trial, and a rule that cannot be routed (FBV2-P2-002B)

**ROUTER HARNESS QUALIFICATION = PASS.** No copper was committed; the authoritative PCB is
byte-identical to `8b9efba`, zero tracks, zero signal vias. PCB routing stays 0 %, overall stays
74 %. Full evidence:
[`audits/2026-08-24-routing-harness-qualification.md`](audits/2026-08-24-routing-harness-qualification.md).

### The scratch environment, first, because that was the last task's real bug

FBV2-P2-002A spent an entire routing attempt reading a phantom `clearance: 73,
lib_footprint_issues: 17` offset on every net. The cause: a `.kicad_pcb` copied on its own loses
`.kicad_dru`, the `.kicad_pro` netclasses and `fp-lib-table`, and DRC then silently measures against
KiCad **defaults**. Every board in this task is a **complete copy of the whole project directory**,
and the harness refuses to run DRC unless all five of those are present beside it. Required proof
holds exactly: authoritative and scratch baselines are both
`{solder_mask_bridge: 1, unconnected_items: 499}`. **Phantom DRC offset: none.**

### All three defects fixed, and a fourth found

**`track_dangling`** had two causes, and the coordinate one was the smaller. The emitter is now
**integer nanometres end to end**, so a neck's end and a trunk's start are the *same integer* rather
than two floats that agree to a rounding step. But the bigger cause was that **the old router never
checked which layer a pad was on** - it would start a `B.Cu` track at the centre of an `F.Cu`-only
pad, which is a dangling end by construction. That is not hypothetical: **`TP34.1` is an `F.Cu`-only
pad on the otherwise-`B.Cu` net `BAT_CONNECTOR_P`.**

**`track_width`** is now governed by one rule: **the routing rule minimum wins.** The escape width
ladder starts at the trunk width and stops at the applicable floor. It never derives a width from a
pad's short dimension. If nothing at or above the floor can leave the pad, the pad is classified
**NO LEGAL ESCAPE** and **nothing is emitted**.

**`shorting_items`** is fixed by giving the neck the *same* obstacle set as the trunk - foreign pads
as true rotated rounded rectangles rather than bounding boxes, tracks as capsules, every drilled
hole on every layer, rule areas, the board edge - and checking it **analytically**, so a short neck
gets a stricter test than the trunk rather than a weaker one.

**And a fourth defect that was not on the list.** A* proves that *grid cells* are clear; the emitted
track is a *continuous segment* between them and can pass three-quarters of a cell closer to an
obstacle than either endpoint. It duly produced `actual 0.1718 mm` against a 0.2000 mm rule. Every
obstacle now carries a **0.75 x grid guard band**. The price is honest: `R86.2 -> R89.1` no longer
fits at 0.05 mm and needs the local 0.025 mm grid.

### Six of eight cases route clean

`Q2_CS` 5.500 mm, `Q3_CS` 5.500 mm, `BAT_MID` 24.860 mm, `LTC_GATE` 66.982 mm, `LTC_OV` 15.179 mm,
`R86.2 -> R89.1` 45.274 mm. Each on its own fresh project-faithful copy, each with **zero** new DRC
violations of any class, **one** connected copper component after a real save and reload, **no**
foreign pad in the cluster, and the ratsnest falling by **exactly one edge per connection**.

### The two that did not are a rule conflict, and it is the finding of the task

Five pads cannot legally accept the width their rules demand. Bisected to 5 um against the
project's own clearances, and the closed-form arithmetic matches to the bisection step:

| pad | package | floor | widest legal escape |
|---|---|---|---|
| `U18.9` | MSOP-10, 0.50 mm pitch | 0.600 mm | **0.245 mm** |
| `U18.8` | MSOP-10, 0.50 mm pitch | 1.200 mm | **0.245 mm** |
| `U14.2` / `U14.3` | T822, 0.50 mm pitch | 1.200 mm | **0.295 mm** |
| `U11.2` | WSON-10, 0.40 mm pitch | 1.200 mm | **0.195 mm** |

**The problem is rule scope.** `BAT_MAIN`'s 0.60 mm floor and D-245's 1.20 mm floor are written as
**whole-net** constraints, but `BAT_SENSE` is a Kelvin sense line carrying microamps, and
`BAT_PROTECTED_P` carries the pack current *and* feeds the MAX17048's fuel-gauge sense input and a
test point, neither of which carries any current at all. D-245's comment already anticipates a neck
exception; **the rule body does not contain one**, so **as written D-245 makes `BAT_PROTECTED_P`
unroutable.** Section 6 said not to invent an exception and section 17 said not to hide it by
weakening rules. **Nothing in `.kicad_dru` was touched.** It is PR-7, and it needs a ruling.

### What the 1.50 mm trunk actually costs

`R75.2 -> U18.8 -> D9.1 -> C25.1` routes at **1.50 mm in 85.274 mm, 22 segments, B.Cu, ZERO vias**,
every segment at full width except the two mandatory 0.245 mm `U18.8` escapes. Past `C25.1` the
charger cluster caps the trunk at 0.60 mm and `U11.2`'s own land pattern caps it at 0.195 mm.

**And D-245's arithmetic needs correcting.** It used the **71 mm placement span**; the measured
route is **85.3 mm**, because copper goes around things. With the unavoidable `U18.8` neck at
7.8 mOhm in 3.9 mm of copper, `BAT_PROTECTED_P` as actually routable is **~35.7 mOhm**, so the net
gains **~6 mOhm rather than the predicted ~11.7 mOhm**. That does not argue against D-245 - it
argues that the neck exception, when ruled, should carry a bounded length and a stated resistance
budget.

### No placement was moved, and none needed to be

`R86.2 -> R89.1` routes legally at 1.00 mm (45.274 mm) and at 0.60 mm (16.848 mm). `TP15.1 ->
U14.2` routes legally at 0.20 mm (8.82 mm) - it was never a geometry problem, so **moving `TP15`
would not have helped and `U14` was never a candidate.** The <= 2.0 mm allowance was not spent.

### Also landed

**`hardware/beta-v2/checks/router_regression.py`** - 22 assertions across six guards, building and
removing its own throwaway project-faithful workspace, and **pinning the five proved land-pattern
conflicts by their exact widths** so that relaxing a rule or moving a part fails the test instead of
passing silently. **ALL CHECKS PASS.** The router is committed beside it as `qrouter.py` so the two
cannot drift apart.

**Opportunity scan (section 19): no native installed routing mechanism exists.** `kicad-cli pcb` has
no routing subcommand, `pcbnew` exposes no scriptable PNS, `kipy` is not installed, and Freerouting
is not installed - and would be the wrong tool anyway, since Specctra DSN carries netclass width and
clearance but **not** custom `.kicad_dru` rules, so D-245 and the rule areas would be invisible to
it. **Keep the qualified harness.**

---

## 2026-08-24 - a router that refuses to keep bad copper (FBV2-P2-002A)

**FBV2-P2-002A = FAIL. The battery / protection block is NOT routed.** No progress; PCB routing
stays 0 %, overall stays 74 %. Full analysis:
[`audits/2026-08-24-p2-battery-protection-routing.md`](audits/2026-08-24-p2-battery-protection-routing.md).

**The board still carries zero tracks and zero signal vias.** Two of twenty-nine nets came out
DRC-clean; the other twenty-seven were reverted automatically, and the two clean ones went with
them rather than be committed as an unrepresentative fragment.

### The deliverable is the method, and that was the point

FBV2-P2-001 failed because a minimum-spanning-tree router drew straight lines through other pads
and produced 505 violations. Section 4 of this task forbade that class of approach outright. What
replaced it:

**Obstacle-aware A\* on a 0.10 mm grid**, rebuilt per connection from the real board - every
foreign pad, every track already laid, every track-forbidding rule area including the one embedded
inside `U1`'s own footprint, and the board edge, each inflated by (clearance + width/2) so that a
legal path on the grid is a legal track on the board.

**Pad-escape necking**, because a 1.00 mm `BAT_MAIN` trunk physically cannot land on `U18` - an
MSOP-10 on 0.50 mm pitch whose pad-to-pad gap is **0.20 mm**. That is also why the first run
reported "NO PATH" on a 2.44 mm hop: the destination was genuinely unreachable at trunk width,
which is a property of the land pattern rather than a bug.

**Per-net DRC gating.** After every net the board is saved to its own path - so DRC sees the
project's own `.kicad_dru` and netclasses, which a scratch-file approach did not - and any new
violation of any class reverts that net before the next one starts. Violations never accumulate.

That last property is the one that matters: **the router refused to keep anything unclean, and the
result is a board with no copper on it rather than a board with hidden shorts.**

### Three defects remain, and all three are named

**`track_dangling` on seventeen nets** - the escape neck and the trunk do not register as joined at
the launch point. A geometry bug in the emitter, not an electrical problem, but a dangling end is
exactly what must never be committed. **`track_width` on `BAT_MID` and `BAT_SENSE`** - the neck
width is taken from the pad's short dimension and on an SO-8 that falls below the `BAT_MAIN`
0.60 mm floor; **the rule is right and the router is wrong.** **`shorting_items` on six nets** - the
neck is laid without consulting the obstacle grid, so it can cross a neighbour even where the trunk
cannot.

None of them is a reason to change placement, widths or topology.

Two connections have no path at trunk width at all - `R86.2` to `R89.1` and `TP15.1` to `U14.2`,
both in the dense left-margin resistor column. They need either a finer routing grid there or a
2 mm placement nudge, and per section 9 that is **surfaced rather than taken**.

### D-245: one net gets a wider trunk, and only one

`BAT_PROTECTED_P` now has a **scoped per-net override - 1.50 mm target, 1.20 mm floor** - added to
`.kicad_dru` and as row A2 of the ledger. **The `BAT_MAIN` class is untouched**: the other four
battery nets keep 1.00 mm / 0.60 mm, because none of them carries the pack current over anything
like the same distance.

The arithmetic is the whole justification. At about 71 mm this net is **about 69 % of the entire
protection path's copper resistance on its own** - 34.9 mOhm at 1.00 mm against 23.3 mOhm at
1.50 mm - taking path copper from about 50.6 to about 38.9 mOhm and the 1.5 A copper loss from 114
to 88 mW.

The neckdown allowance that comes with it is written as a policy, not a loophole: shortest length
that clears the package, never a traverse, length and width documented per pad, no thermal-relief
or single-via bottleneck. **The 1.20 mm figure is the trunk floor, not a licence for a narrow run.**

### B-34, with the unit confusion corrected

The FBV2-P2-001 write-up's copper figure is **about 50.6 mOhm**, not 525 mOhm. With `F1` about
25 mOhm, the two FETs about 46 mOhm and the BQ25185 BATFET's **115 mOhm**, the path is **about
355 mV / 532 mW at 1.5 A** and **about 414 mV / 724 mW at 1.75 A**. Nothing is clearly unsafe.
**B-34 stays open - physical validation required**, and D-245 takes the copper term to about
38.9 mOhm once the net is actually routed.

**PM-2 does not close.** Its placement correction is approved and retained; closure still waits on
DRC-clean routing, which is what it always said it would.

---

## 2026-08-24 — the ground plane, and a routing attempt that was reverted (FBV2-P2-001)

**FBV2-P2-001 = FAIL. The power tree is NOT routed.** No progress; PCB routing stays 0 %, overall
stays 74 %. Full analysis:
[`audits/2026-08-24-p2-power-routing.md`](audits/2026-08-24-p2-power-routing.md).
New working document: [`pcb/FBV2_P2_POWER_ROUTING.md`](pcb/FBV2_P2_POWER_ROUTING.md).
Pre-routing checkpoint tag **`beta-v2-p2-entry-pass` → `faa0c91`**, annotated and pushed.

**The board still carries zero tracks and zero signal vias.** What it gained is the In1.Cu ground
plane and two corrective placement passes that the routing exposed as prerequisites.

### The ground plane exists, and the regression now knows what it is

In1.Cu is one zone, **one island**, net GND, **9938.9 mm² of a 10656 mm² board — 93.3 %**, with a
solid pad connection and no thermal relief. No split, no analog island, and its single authorised
void — the ESP32 antenna keep-out — is cut by the four-layer rule area that already existed rather
than by a polygon carved by hand. F.Cu and B.Cu pours were deliberately **not** created: they are
the last step of FBV2-P2, and making them now would hide return paths rather than prove them.

`p1_regression.py` had a blanket *"0 fills"* expectation, which was right when nothing was allowed
to exist and wrong the moment a reference plane did. It now checks **0 tracks / 0 vias / 0 outer
pours**, and separately that **In1 is exactly one GND zone of exactly one island** — so a split
reference is a gate failure instead of an invisible mistake.

### PM-2 was closed on incomplete evidence, and the routing is what found it

FBV2-EXP-002 reported PM-2 closed on the chain: `J4 → F1 → Q2 → Q3 → R75 → U18`, 30.86 mm, Kelvin
6.60 mm. **That measurement was real and it is not withdrawn.** But it was reported as though it
closed the whole of PM-2, and it did not. The trip/gate and dead-cell support parts had been packed
into regions chosen while the chain still sat in the right column, and were never re-homed when the
chain moved. Measured on `faa0c91`, before this task touched anything: **`LTC_GATE` — a ≈ 20 µA
charge-pump node holding four pass FETs enhanced — spanned 70.4 mm.** `BAT_SENSE` 61.4. `REF_POL`
51.7. `REC_GATE_N` 50.6.

Routing those as they stood would have knowingly built the defect PM-2 exists to prevent, so the
support network was moved beside the chain it belongs to: **`LTC_GATE` 70.4 → 29.8 mm, `BAT_SENSE`
61.4 → 24.3, `REF_POL` 51.7 → 9.7, `REC_GATE_N` 50.6 → 15.6, `N_POL` 46.4 → 8.3, `LTC_OV`/`LTC_UV`
28.2/15.0 → 8.0/9.1.** No component value, no threshold, no topology and no net changed, and the
1.5 A chain itself did not move.

Twenty-nine power test points moved too. A test point 50 mm from its own net is not access, it is a
stub — and on a 1.5 A net it is a stub that forces load current somewhere it should not go. `TP34`
was 59 mm from `J4`; it is now 4.4 mm.

### Why the routing failed, said plainly

The first router computed a minimum spanning tree over each net's pads and drew each edge as a
direct segment. Inside a compact PM-1 cell that is adequate. Across a board it is not: **it draws
straight lines through other pads.** On 64 nets it produced **505 DRC violations — 102 shorting
items, 112 track crossings, 204 solder-mask bridges, 45 clearance.**

It was reverted in full. Committing 102 electrical shorts into the authoritative board, on the one
task whose subject is the *safety-critical* battery path, was not a defensible option — and a
partial pass would have been the asserted-rather-than-measured progress this file's own rules exist
to prevent. What the next task needs is an obstacle-aware path search or verified hand polylines;
the scope, the widths, the layer policy and the intended topology are all already settled and
written down, so none of that has to be re-derived.

### B-34, recomputed and still open

From the *intended* geometry at ledger widths — **an estimate, not a measurement, and labelled as
one**: copper 50.6 mΩ, fuse ≈ 25 mΩ, the two FETs ≈ 46 mΩ, and the BQ25185 BATFET's **115 mΩ**
dominating. **≈ 355 mV / 532 mW at 1.5 A; ≈ 414 mV / 724 mW at 1.75 A.** Nothing there is clearly
unsafe, so the escalate-and-halt condition did not fire — but an estimate from an unrouted board
cannot close a blocker, so **B-34 stays open, physical validation required.**

One number dominates: `BAT_PROTECTED_P` at ≈ 71 mm is **69 % of the copper resistance on its own**.
Widening it 1.00 → 1.50 mm takes the copper to 38.9 mΩ, at the cost of board area on a face that
has it.

### E-7 closed, with the wording corrected

**The battery envelope is 57 × 75 × 8.0 mm and that is a MAXIMUM reserved envelope.** 57 mm is not
a minimum cell width and not "the lower bound of what fits" — the EXP-002 phrasing was wrong and is
withdrawn. Both verified candidates are 50 mm wide. **The envelope is not shrunk to 50 mm:** the
unused 7 mm preserves alternate- and future-cell flexibility at zero current placement cost, and
reclaiming it would spend the only tolerance the design has against a different cell.

---

## 2026-08-24 — the header, the cell, and the three moves done once (FBV2-EXP-002)

**FBV2-P1 RE-ISSUED = PASS. FBV2-P2 ENTRY = PASS. PM-1, PM-2, PM-3 and PT-1 all CLOSED.**
**No progress earned; overall stays 74%.** Full analysis:
[`audits/2026-08-24-expansion-and-refloorplan-implementation.md`](audits/2026-08-24-expansion-and-refloorplan-implementation.md).
New library part: `Samtec_SSQ-124-02-G-S-RA.kicad_mod`.

**ZERO SIGNAL ROUTING.** 0 tracks, 0 signal vias, 0 electrical copper pours, 499 unrouted.

### The battery gate ran first, and it made the headline claim wrong in the good direction

Nothing authoritative was touched until the 57 × 75 × 8 mm envelope had been checked against cells
somebody can actually buy. Two, from manufacturer datasheets rather than marketplace listings:
**PKCELL `LP785060`** — 7.3 × 50 × 60 mm, 2500 mAh typical / 2375 minimum, PCM fitted with a ≈ 2.8 V
cut-out, ships on a genuine 2-pin JST-PH — and **`LP755070`** — 7.5 × 50 × 70 mm, **3000 mAh
minimum**, PCM fitted at 4.275 V ± 50 mV overcharge with a 2.50 V resume, 500 cycles to 80 %,
0–45 °C charge.

EXP-001 predicted a ≈ 5 % capacity penalty from scaling the volume. **That penalty does not
materialise, and saying so is the point of running the gate: both candidates are 50 mm wide, so the
57 mm limit binds neither of them, and `LP755070` lands at the TOP of D-071's 2500–3000 mAh
target.** The envelope was always larger than the cells that fill it. The capacity target is
unchanged, and the one new item this task raises is the mirror of that finding: **7 mm of the
reservation is now unused** (E-7), which is either reclaimable area or tolerance for a wider cell —
recorded, not decided.

### What was built

`J5` becomes a **Samtec `SSQ-124-02-G-S-RA`**, a 1 × 24 2.54 mm female right-angle socket —
**the same manufacturer as the `BCS-112-S-D-HE` it replaces**, so the account and the small-quantity
behaviour are already known. Body 61.47 mm, pin span 58.42 mm, mates a **.025″ square post**, which
is the ordinary male-header and Dupont standard. `J8`, a **`JST SM04B-SRSS-TB`** Qwiic / STEMMA QT
connector, joins it — **SMT and machine-placed**, so the manual-assembly list stays at two parts.

**All 24 electrical functions are retained and not one protection component was removed.** Twelve
100 Ω GPIO resistors, the 22 Ω I²C pair, the 330 Ω WAKE resistor, four TVS arrays, the TCA4307, both
load switches, the boost, the FLT wire-OR, the `Q10` WAKE gate and the `ACC_DETECT_N` protection are
all present and electrically identical. **The schematic change is a footprint swap plus a pin re-map
on one sheet — no net was created, deleted, split or merged.** The old 2 × 12 footprint stays in the
library: Beta-DM uses it, and it is the fallback if the owner ever reverses this.

Qwiic costs **zero components**. It taps `EXT_SDA` / `EXT_SCL` — downstream of the TCA4307 and the
22 Ω pair, at `D2`'s clamp, the same node as the header — so it inherits the buffer, the pull-ups,
the series resistance and the ESD array. Its power is `ACC_3V3_SW`, and that is architectural rather
than tidy: **`U16`'s own VCC already is**, so an unswitched feed would create a powered-device /
unpowered-bus state. `ACC_5V_SW` is not on it and cannot be.

### ORDER-B, because ORDER-A was safe against the wrong failure

ORDER-A protected against a one-position slip. It did not protect against someone turning the
accessory around. **ORDER-B is symmetric by construction**, so a full 24-pin accessory inserted
180° maps 5V↔5V, GND↔GND, 3V3↔3V3, and 3.3 V logic to 3.3 V logic on every remaining contact.
**Power-to-signal maps under reversal: zero** — proved pin by pin from the exported netlist, not
argued.

The lateral slip stays impossible for the same reason it always was: a mating male body is exactly
60.96 mm, the closed-end recess is 62.5 mm, and 1.54 mm of play against a 2.54 mm pitch is 61 % of
one position. **A pleasant consequence: D-097's asymmetric upper-edge key is no longer needed.**

### The board grew symmetrically, and one reservation turned out to be fiction

70 → 72 mm, **1.0 mm on each side**, so every part shifted +1.0 mm in X and **every part-to-part
relationship on the board is preserved exactly.** Only the edge margins moved, to 1.5 mm on both
sides — the ≥ 1.5 mm rule met exactly, with nothing to spare. The 80 × 160 × 23 enclosure is
untouched.

That last "nothing to spare" exposed something. `ANT433_REGION` was 2.2 mm wide, and 2.2 mm does not
fit inside a 1.5 mm gap. **It never described anything real:** the 433 flex is **0.28 mm thick** and
bonded flat to the cavity wall, so it projects inward by its thickness, not by 2.2 mm. The region is
now re-derived from the part at X −1.40 … −0.60, with 0.6 mm of air to the board edge.

And 3 mm of cell width is the entire price of the interface. A right-angle socket puts its tails
**6.53 mm inboard of its own mating face** — it has to, because it must swallow a 6 mm post — so the
requirement is (board right edge − cell right edge) ≥ 7.83 mm, against 4.00 mm before. Measured
result: tail row at X 65.900, **1.100 mm clear of the cell**, mating face 0.430 mm outboard of the
board edge with **1.070 mm to the wall** for the recess lip.

### Three placement moves, done once

**PM-1.** Converter IC-to-inductor spans fall from 12.96 / 28.56 / 30.50 / **45.90 mm** to
**4.80 / 4.34 / 3.86 / 3.79 mm**. But the brief was explicit that moving the inductor and leaving
the caps remote does not count, so each converter was rebuilt as a **complete power cell** in
electrical order. The clearest case: `D8`, the backlight catch diode, sat **45.7 mm from its own
inductor**; it is now 3.56 mm from `U17` and adjacent to `L3` and `C44`, so the loop that switches
to 39 V on an open-LED fault is local instead of a 76 mm perimeter running 13 mm from the
microphone.

**PM-2.** The 1.5 A protection path goes from **116.7 mm to 30.86 mm** as one monotonic column —
`J4` → `F1` → `Q2` → `Q3` → `R75` — with the Kelvin pair at 6.60 mm. **No FET, no threshold, no
divider value and no recovery branch was altered. D-049 is untouched.** One part could not join the
column and that is recorded rather than hidden: the left margin is also the mandatory 915 coax lane,
which parts ≤ 2.0 mm may share because the cable lies over them, but a **5.75 mm JST-PH with a
mating cable** cannot. `J4` therefore sits at the head of the column, north of the coax's western
excursion, 8.59 mm from `F1`.

**PM-3.** The NFC arms are mirrored about y = 118.000 at **Δx = 0.000 mm and arm-length Δ = 0.000
mm** — same topology, same orientation, same stage order, every pair equidistant from the axis. The
crystal's load capacitors moved from 13–15 mm away on the far side of the IC to beside `Y1`, which
is now 5.40 mm from `U9`. No locked NFC value changed.

**PT-1.** `U11` is out of the battery shadow, 3.5 mm clear of the cell, so its ≈ 0.65 W of charging
dissipation spreads into copper with nothing behind it.

### B-34 improves, and does not close

The brief said not to claim routing losses are zero, so: at 1 oz and 1.0 mm the protection-path
copper falls from **38.8 mΩ** (58 mV / 87 mW at 1.5 A) to **15.2 mΩ** (23 mV / 34 mW) — about 53 mW
better at 1.5 A and 72 mW at 1.75 A. **That is a material improvement and it is not a closure.**
B-34's ≈ 0.70 W is dominated by the BQ25185 BATFET's 115 mΩ and the FET R_DS(on), neither of which
this task should have touched. The copper share of the figure falls from roughly 17 % to 7 %.

### The rest

`BOOT` moved to the bottom band on the **front** face — it is an SMD switch whose actuator faces out
of the front shell, so its Ø2 mm service hole goes in the front wall and is therefore clear of both
the microSD card path and the USB-C plug envelope. **Lower-left was rejected on RF**: that wall *is*
the 433 flex region and the mandatory coax channel. `POWER` stays on the right wall. Retention is
still two M2 — **widening the board did not buy a third, and none was chased.**

Some numbers improved for free: NFC loop to `J5` metal **5.490 → 9.155 mm**, the NFC cable pair
**41.73 → 31.23 mm**, and the display's off-centre offset **3.34 → 2.34 mm**, because symmetric
growth halves it.

**DRC 26 → 1.** The single survivor is the `MK1` netless-NPTH-inside-its-own-GND-ring artefact
accepted at D-227 — still not excluded and still not suppressed. **ERC 0 errors / 27 warnings,
histogram identical. 499 unrouted. Zero placement collisions.** `p1_regression`, `dru_probe`,
`netclass_probe` and `fork_equivalence` all pass.

One check had to be taught something: **`J5`'s courtyard legitimately overhangs the right edge by
0.975 mm.** That is what a right-angle socket is *for*. `p1_regression.py` now measures the mating
face against the wall gap explicitly instead of counting it as a part that has fallen off the board.

---

## 2026-08-24 — the connector fits the users, not the board (FBV2-EXP-001)

**AUDIT = PASS. AUDIT ONLY — no authoritative hardware changed, no progress earned; overall stays
74%.** Full analysis:
[`audits/2026-08-24-expansion-compatibility-audit.md`](audits/2026-08-24-expansion-compatibility-audit.md).
New working document:
[`architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md`](architecture/EXPANSION_ECOSYSTEM_PROPOSAL.md).

**`J5` is unchanged, no sheet was opened, the PCB blob is byte-identical to `HEAD`, no Qwiic
connector exists, `BOOT` and `POWER` have not moved and no PM part moved.** D-081 / D-083 / D-093 /
D-097 remain in force; the proposed supersession is marked **PENDING CTO / OWNER RULING**.

### The answer is yes, and the price is 3.83 millimetres of battery

The owner's intent — ordinary 2.54 mm female sockets down the right side, one pin per line, Dupont
jumpers, Qwiic boards that just plug in — is achievable, and **the electronics behind the connector
need no architectural change whatsoever.** Every series resistor, every TVS array, the TCA4307, both
load switches, the boost and the FLT wire-OR stay exactly as they are. The schematic change is a
footprint swap and a pin re-map on sheet 09.

What does not work is the geometry, and the reason is specific rather than vague. **A right-angle
through-hole socket puts its solder tails 6.5–6.9 mm inboard of its own mating face** — it has to,
because it must swallow a 6 mm male pin. For the mating face to reach the right wall, the tail row
lands at x ≈ 63.5, and that is **inside `BATTERY_SHADOW`, which forbids any through-hole lead.**

> **Requirement: (board right edge − battery right edge) ≥ 7.83 mm. Today it is 4.00 mm.
> Shortfall 3.83 mm.**

Above the battery, where the lead rule does not apply, the right wall offers **41.00 mm** between the
cell and the IR receiver's optical corner. A 1 × 24 body is **61.47 mm**. The largest socket that
fits there is a **1 × 15**, and it would leave nothing for the Qwiic connector or the power switch.
Every other edge was measured and rejected: the left wall **is** the 433 flex region and the mandatory
915 coax channel, the bottom edge is microSD, USB-C and both radio modules, and the top edge is the
IR pair, the opaque barrier and the SMA. Mounting the socket on the rear face moves the conflict from
its leads to its body and gains nothing.

So the recommendation carries two conditions and they are the owner's to take: **PCB 70 → 72 mm**,
which is *already* the documented `FBV2_PCB_MAX_MM` and leaves the 80 × 160 × 23 shell untouched, and
**battery 60 → 57 mm wide — about 5 % of capacity.** With both, the margin is +1.17 mm and the wall
carries the header, the Qwiic connector and the power switch. **Without the battery change the
24-line side header cannot be delivered in this enclosure, and `J5` stays as it is.**

### Two 1 × 12 sockets are rejected on arithmetic, not taste

Both Samtec and Sullins build a 2.54 mm socket body **N × 2.54 + 0.51 mm** long — 1.525 mm of
insulator past the end contact at each end. Butt two of them and their end contacts sit **3.050 mm
apart against a required 2.540 mm pitch: a 0.510 mm interference.** They cannot form a continuous
24-position grid at all. They also need **5.59 mm more wall length** than the single 1 × 24, need two
recesses, and introduce a mis-plug mode the 1 × 24 does not have — a 12-way accessory in the wrong
group. **One 1 × 24. Not two 1 × 12.**

### The parts, verified

**`SSQ-124-02-G-S-RA` (Samtec)** — and Samtec is *the same manufacturer as the present `J5`*, so the
account and the small-quantity behaviour are already known. From the SSW/SSQ datasheet: 01–50
positions per row, `-S` single row, `-RA` right angle available with `-S`, body 61.47 mm, socket-axis
height selectable by lead style, insertion depth 3.68–6.35 mm, **mates .025″ (0.635 mm) square post**
— the Dupont standard — 6.3 A per pin, −55 to +125 °C, 100 cycles at 10 µin Au.

**`JST SM04B-SRSS-TB(LF)(SN)`** for Qwiic — SH series, **1.0 mm** pitch confirmed from JST's own
`eSH.pdf`, 4 circuits, side entry, SMT, 6.0 × 4.25 mm, 1.0 A, 50 V. Pin order is the ecosystem's, not
a choice: **1 GND, 2 3.3 V, 3 SDA, 4 SCL.**

**Sullins `PPTC241LGBN-RC` was verified and deliberately not baselined.** Its drawing is
authoritative and supplied the 6.53 mm depth figure the whole audit turns on — but DigiKey lists the
non-RC variant obsolete at 0 stock, and the 19-way sibling is factory-order only at 1,000 pieces and
11 weeks. **That is the third time this programme has met a catalogue part that is not a stocked
part**, after the Harwin `M20-7881242` and the Amphenol `095-902-568-100`. D-096 keeps earning its
keep.

### Three things confirmed rather than assumed

**Qwiic costs zero components.** It attaches at `EXT_SCL`/`EXT_SDA` — downstream of the 22 Ω
resistors, at `D2`'s clamp, the same node as the header — and inherits the hot-swap buffer, the
1.5 k pull-ups, the series resistance and the ESD array. Its power is `ACC_3V3_SW`, and that is
architectural rather than preferential: **`U16`'s own VCC is already `ACC_3V3_SW`**, so an unswitched
`+3V3` feed would create a powered-device / unpowered-bus state. `ACC_5V_SW` is never exposed.
Three daisy-chained boards on 100 mm cables come to roughly 55–75 pF against a ≤ 200 pF budget —
**no mux, no repeater, and none should be added.**

**A Manual / Bench power mode needs no hardware change for either rail.** Traced pin by pin:
`ACC_DETECT_N` goes through `R64` to `R129` and `U3.P17` and **nowhere else** — there is no AND gate,
no interlock and no bypass between it and the three enables. Detect gating is one hundred percent
firmware policy, while ILIM, reverse-current blocking, thermal shutdown and `FLT` stay in hardware,
and permanent 5 V remains physically impossible because both 5 V enables default OFF through 100 k
pull-downs. B-35 is carried forward unchanged: `FLT` still does not assert on plain current limiting,
which is exactly why bench mode needs its warning.

**BOOT can move without compromising anything.** `SW1` is **SMD**, and the bottom edge has a measured
**11.04 mm** free window between the microSD shell and the USB-C receptacle, with a **14 mm** free
span of enclosure wall for a Ø2 mm tool hole. **Lower-left is rejected on RF**: that wall *is*
`ANT433_REGION`, with the flex bonded 0.2 mm outboard of the board edge, and it is also the mandatory
`COAX_915_CHANNEL` — and P2-R1 already flags board copper in exactly that band as an aggressor.

### The pin order removes two hazards it did not have to

**ORDER-A** puts `3V3 / SDA / SCL / GND` at pins 3-4-5-6 — the same block every maker already knows
from Qwiic — and puts **both 5 V contacts at the two physical ends of the row, each with `GND` as its
only inboard neighbour.** No 5 V pin is adjacent to any signal. The present order has two such
adjacencies. A one-position slip from either 5 V pin now lands on ground: a current-limited short
with `FLT`, not 5 V into a 3.3 V input. All 24 functions are retained exactly — nothing added,
removed or merged.

And the mis-alignment problem turns out not to need a proprietary shroud at all. A mating 1 × 24 male
body is exactly 60.96 mm; a **closed-end recess 62.5 mm long** leaves **1.54 mm of play against a
2.54 mm pitch**, so a one-position shift is physically impossible. **The asymmetric upper-edge key of
D-097 becomes unnecessary.**

### What it costs, said plainly

A single row has **no roll couple** — the 2 × 12 has 7.87 mm of it, which is the direction a
leaned-on accessory actually loads a connector. In yaw the 1 × 24 is 2.09× better, but that is not the
direction that matters. The mitigation is non-electrical: the recess floor, its closed ends, and a
moulded ledge for the accessory board to rest on. **No new electrical connector, no new fastener, and
the manual-assembly list does not grow — the Qwiic part is SMT and machine-placed.**

And **two official full-header accessories should not be stacked.** One at a time; a second board
uses Qwiic or jumper wires. **No AQROOT hub is required and none should be built.**

### Do it once

PM-2's fix is to consolidate the battery-protection block at the battery-entry corner — **exactly the
corner the 1 × 24 now wants.** Deciding the connector separately from PM-1 / PM-2 / PM-3 / PT-1
guarantees a second full placement cycle. The audit therefore ends with a combined sequence: rule on
the changes, fix the outline and the reservations, place the right-wall stack, then PM-2, PT-1, PM-1,
PM-3 and P2-R1 — and **re-issue FBV2-P1**, because a 70 → 72 mm outline change invalidates its PASS.

---

## 2026-08-24 — twenty-two rules that could never fire (FBV2-P2-000)

**FBV2-P2 ENTRY GATE = FAIL on one criterion of thirteen. No progress earned; overall stays 74%.**
Full analysis: [`audits/2026-08-24-p2-entry-audit.md`](audits/2026-08-24-p2-entry-audit.md).
New working documents: [`pcb/FBV2_P2_ROUTING_PLAN.md`](pcb/FBV2_P2_ROUTING_PLAN.md),
[`pcb/FBV2_P2_NETCLASS_LEDGER.csv`](pcb/FBV2_P2_NETCLASS_LEDGER.csv).
New check: `hardware/beta-v2/checks/dru_probe.py`.

**ZERO ROUTING WAS PERFORMED.** No track, no signal via, no electrical pour. 499 unrouted,
unchanged. The only PCB edit is one board-level rule area.

### The rule file had been lying, and there was no way to see it

P2-O5 recorded that `.kicad_dru` *"still references E5/E6 rule areas that the P1 rebuild deleted."*
That was true and it was an understatement. **The file referenced thirty-nine rule areas. The board
contained none of them** — only `MIC_ACOUSTIC_KEEPOUT`, `BOSS1_KEEPOUT`, `BOSS2_KEEPOUT` and one
**unnamed** zone embedded in `U1`. **Twenty-two of seventy-one rules could never fire**: not only
the E6 pockets, but every RF-band rule, every E5/E4 corridor rule, the header reservation, the E2
button escapes, **and the ESP32 antenna rule**.

The reason nothing caught it is worth stating precisely, because it will happen again to somebody
else: **KiCad's `intersectsArea()` and `enclosedByArea()` return `false` for an unknown area name.
They do not warn and they do not error.** A rule whose condition can never be true produces no
violations — which is exactly what a rule being satisfied looks like. DRC was reporting a clean
result against protection that had been deleted three tasks earlier.

The ESP32 antenna was never actually unprotected: the `U1` footprint carries its own embedded rule
area with every keepout flag set on all four copper layers, and that has always been live. But the
*file* said the protection came from a named area that did not exist, and **nothing in the
toolchain could tell the difference.**

**The rule set is rebuilt: 71 → 64 rules, every one checked against the current board, with a
written retirement register (R1–R10) in the file header giving a reason for each of the twenty-two
retirements.** Nothing was retired for convenience. Where the intent survived it was re-expressed
against current objects; where the intent died with the Beta-DM geometry, that is stated as a
finding rather than papered over. **The E6 escape-relief doctrine is explicitly NOT retired** —
own-area sufficiency, `enclosedByArea()` never `intersectsArea()`, the 2.0 mm hard clearance-run
cap kept separate from the 6.0 mm narrow-width review trigger, and last-in-file precedence — even
though its Beta-DM measurements do not transfer to a differently sized, differently placed,
unrouted board (D-233).

**`checks/dru_probe.py` is the part that matters.** It fails if any rule reference stops resolving
or any netclass pattern stops matching. P2-O5 cannot recur silently.

### The highest-current net on the board was on the 0.20 mm default class

The inherited `BAT_MAIN` pattern was the root-sheet path `/BAT_PROTECTED_P`, while every Full Beta
v2 power net lives under `/01_POWER_TREE/`. **It matched nothing.** So
`/01_POWER_TREE/BAT_PROTECTED_P` — 1.5 A sustained — had been routing at 0.20 mm since the fork,
and `BAT_RAW`, `BAT_MID` and `BAT_SENSE`, which all carry the full pack current, were in no class
at all. The same defect killed `NFC_5V_PA` outright: it captured **no net whatsoever**. And
`ACC_5V_LX`, the `U21` accessory-boost switch node, had **never** been in `SWITCH_NODE` — a
1.2 MHz switching node sitting on the ordinary signal class.

**14 netclasses → 18; 62 patterns → 57; every surviving pattern now matches at least one board
net.** Four dead classes were retired, all of which either matched nothing or carried Default
values, so no net's electrical parameters were weakened by a retirement (D-234).

### Retention is locked, and D-226's escalation is closed

**Two currently legal M2 through-board screws are acceptable.** No component moved: the battery was
not reduced, the display was not moved, the SMA was not relocated. Retention is a four-element
architecture — moulded edge-capture rails, **four** rear non-metallic support ribs on reserved
component-free pads, the two screws, and the `J5` backing boss carrying its ≈ 33 N insertion load
into the enclosure rather than into solder joints. Every rib is outside the battery shadow, so no
support compresses the cell; every rib is non-metallic and far outside the Ø58 NFC exclusion. USB
and microSD insertion loads do not depend only on the screws — both connectors sit on the bottom
edge, which carries a continuous rail. **All four routes to a third screw are declined** (D-232).

Three stale mechanical-spec entries went with it: *"Count: 6 × M2"*, the `FBV2_BOSSES: 3 x M2 …
PARTIAL` line, and `FBV2_915_PIGTAIL: 095-902-568-100 … DOES NOT REACH`, which D-223 superseded
two tasks ago.

### What the strategy freeze actually decided

The 4-layer JLCPCB stack is **kept**, and the layer roles are now **enforced by rule rather than
asserted**: In1 solid GND with `severity error` on any non-GND track, and USB, both NFC transmit
arms, the NFC crystal, every switch node, the Class-D output and `BAT_MAIN` all **forbidden on
In2**, because In2's only continuous reference is In1 across a 1.065 mm core. One authorised void
in the plane — the ESP32 antenna keepout, a **6.5 × 44 mm notch on the right edge** in the same
corner as `U1`, `U11`, `U18`, `R75` and `D10`, so every return path there must be planned around a
plane edge.

**The USB answer is short because the design is short.** The ESP32-S3 has no High-Speed PHY, so
this is Full Speed at 12 Mbit/s with a 4–20 ns rise time and a 100 mm critical length. The measured
path is **≈ 40 mm per side, entirely on F.Cu over solid In1**, with an intrinsic placement skew of
2.4 mm = **17 ps** against a ≈ 1 ns budget. **No impedance control, no length matching, zero vias.**
The 90 Ω geometry stays as good practice and is marked STACKUP-TO-CONFIRM for one honest reason:
**the board file carries no physical stackup object at all**, so a fabricator would build to its own
default (P2-O6).

**No length-matching theatre anywhere else either.** SPI-A is 46.4 mm against Beta-DM's 126.5 —
**63 % shorter** — and SPI-B is 113.1 against 144.0, **21 % shorter**. Both are shorter than
versions that were already accepted, so neither gets matching or damping. **The one bus with a real
derived constraint is internal I²C**, at `C_bus ≤ 161 pF` for 400 kHz on 2.2 k pull-ups — a number
that ~100 mm of copper and eight devices is already close to — with 100 kHz as the recorded
fallback (D-235).

**The community-port escape was measured rather than feared.** `J5`'s inter-row channel is
**6.570 mm × 27.94 mm** with eleven inter-pad gaps at two tracks each per layer, three usable
layers, and both ends open: **10 crossings needed, 22 available on F.Cu alone.** M-12's warning
that the right-hand strip was "the most constrained region of the PCB" is discharged. No nudge.

### What fails the gate

**Three electrically required placement moves, and routing must not begin until they are ruled on.**
All three are new, all three are measured from the board, and **none of them existed in Beta-DM to
be carried forward** — the battery-protection block and the NFC front end are both new in Full Beta
v2. FBV2-P1 placed them into free rear pockets and verified every *mechanical* relationship by
script. Nobody had yet looked at either *electrically*. That is what an entry gate is for.

**PM-1 — all four switching converters have their inductor off the IC.** `U12`/`L1` 12.96 mm,
`U13`/`L2` 28.56 mm, `U21`/`L4` 30.50 mm, `U17`/`L3` **45.90 mm**, against a ≤ 5 mm requirement.
The backlight is the worst: `BL_SW` runs `U17.1` → `L3.2` while the catch diode `D8` sits **beside
the IC, 45.7 mm from the inductor**, so the `L3 → D8 → C44` boost energy loop is **≈ 76 mm around**,
switching at 1.2 MHz between 0 V and **up to 39 V** on the open-LED fault TI specifies — down the
left margin, **13 mm from the microphone**, through the band the 433 flex sits against. All four
inductors were placed in the left-margin column at x ≈ 3 while their ICs went elsewhere. That is
systemic, not four coincidences, and **loop area is a placement property that no routing repairs.**

**PM-2 — the single-fault battery-protection block is dispersed over 96 mm.** The 1.5 A path runs
`J4` → `F1` → `Q2` → `Q3` → **79.0 mm** → `R75` → `U11`, ≈ 116.7 mm in total. What is *right* stays
right and is worth saying first: **the Kelvin sense is sound** — `U18`'s SENSE and OUT pins both
land on `R75`'s pads with the controller 4.2 mm away, so the 47 mV measurement across the 15 mΩ
shunt at the 3.125 A trip is not corrupted. What is wrong is everything around it: `LTC_GATE` at
**95.6 mm** is a ≈ 20 µA charge-pump node holding four pass FETs enhanced, with its RC damping
31–45 mm from the FETs; `LTC_OV` and `LTC_UV` carry the **battery trip points** on 3.65 M and 510 k
dividers over 78–82 mm; and `REF_HO`'s two divider halves are **38 mm apart** with the comparator
52 mm from the top resistor. The block sits in three clusters with multi-megohm nodes strung
between them. **Routing cannot make a 3.65 MΩ node that crosses four switching converters immune to
coupled charge.** D-049 and the single-fault architecture are **not** compromised by this finding —
the recommendation moves parts, not circuits — and it returns ≈ 0.13–0.18 W to open blocker B-34.

**PM-3 — the NFC differential front end is not symmetric.** `NFC_MATCH_A` spans 24.18 mm against
`NFC_MATCH_B`'s 34.21 — **10 mm of asymmetry before a single track is drawn.** `L5` and `L6` are
19.8 mm apart on **opposite sides** of `U9`; the antenna nodes differ 8.82 vs 12.49 mm; each EMC
filter node's three capacitors are spread over 13.6–17.2 mm; and the crystal load caps sit 13–15 mm
from `Y1` on the far side of the IC, giving a ≈ 30 mm oscillator loop. With `R_q` at 1.1 Ω per arm
and a network Q of ≈ 21, and mandatory first-article bench tuning, that is not something routing
absorbs (D-236).

A fourth item is recorded but ranked below them: **`U11` dissipates ≈ 0.65 W while charging from
inside the battery shadow**, pressed against the cell it is charging, in a sealed unvented
enclosure (PT-1). *Do not rely on the battery as a heatsink* — this is the one place the board
currently does.

### Validation

**DRC 47 → 26**, and the 21 `clearance` violations closed by **naming the four vendor land patterns
that cause them** — `D2`, `U18`, `U19`, `U21`, all stock KiCad footprints whose minimum pad gap is
0.1500 mm by construction — **without weakening any routing clearance anywhere.** Residue is 24
`silk_over_copper` + 1 `silk_edge_clearance`, which is finishing work P2 owns, and the one `MK1`
`solder_mask_bridge` reviewed and accepted at D-227, still **not excluded and not suppressed**.
**ERC 0 errors / 27 warnings, violation-type histogram identical.** `netclass_probe`,
`p1_regression`, `fork_equivalence` and the new `dru_probe` all PASS. Board 70.000 × 148.000 mm,
placement collisions 0, **499 unrouted, ZERO tracks, ZERO signal vias, ZERO electrical pours.**
Beta-DM, the frozen Beta tree and `hardware/beta/mechanical/` untouched.

### A dead end worth recording

The first attempt to make the ESP32 antenna rule resolvable was to **name the rule area already
embedded in the `U1` footprint**. It works — `pcbnew` reads the name back — but it edits the board
copy of a library footprint, and DRC immediately reported `lib_footprint_mismatch` on `U1`, a class
FBV2-P1-002 had driven to zero. **Tested, observed, reverted.** The board-level duplicate carries
the identical polygon and flags, is visible in the board file, lets other rules name the region, and
leaves the library relationship alone. The reasoning is written into `.kicad_dru` §3 so nobody
re-tries the rename.

---

## 2026-08-24 — the circular keepout that opened the 915 lane (FBV2-P1-002)

**FBV2-P1 PASSES. Overall 68% → 74% — the third of the twelve gates.** Full analysis:
[`audits/2026-08-24-p1-floorplan-closeout.md`](audits/2026-08-24-p1-floorplan-closeout.md).
New working document: [`assembly/IR_LEAD_FORMING.md`](assembly/IR_LEAD_FORMING.md).

### The 915 feed closes, and the reason is width, not length

FBV2-P1-001 failed the gate on the 915 MHz pigtail, and the diagnosis in that audit was only half
right. Length was never the binding constraint: **the SMA is locked to the top-panel LEFT half and
the NFC region owned the entire upper-left**, so a 200 mm or a 300 mm cable would both have had to
cross the clear zone or run inside the 5 mm metal keep-out.

The circular geometry unlocks it — but **not because a circle is smaller than a square.** It is,
only at the corners, and the corners were never in the way. It unlocks it because a circle can be
**re-centred** against a hard right-hand limit in a way a 58-wide rectangle sitting at x −4.5 … 53.5
could not. The width budget is the whole argument: **75 mm of cavity, 58 mm of Ø58 exclusion,
12.1 mm owned by `J5` — 4.9 mm of coax lane, and only if the exclusion is pushed as far right as
`J5` allows.** It now is, with the loop perimeter **5.490 mm** from `J5`'s copper against a ≥ 5 mm
rule.

**NFC clear Ø48, metal exclusion Ø58, both centred doc (30.800, 124.500)**; the 48 × 48 square is
retained but only as the placement-tolerance envelope. The centre moved **+6.30 mm in X**, which is
the 915 solution, and **−1.50 mm in Y**, which buys the SMA its margin (D-224).

**Measured, not estimated: the route is 138.48 mm** including bend allowances, with a **7.42 mm**
minimum available bend radius against the ≥ 5 mm rule and **0.600 mm** at its tightest point to the
Ø58 exclusion — **zero violations** against the 433 flex, the battery, the speaker cavity, the
microSD card-travel volume, the USB aperture, both IR optical regions, the barrier, the community
recess and `J5` (D-222).

**`U7` and `U8` are swapped.** The two Ebyte footprints are dimensionally identical, so the swap
costs **zero plan area** and puts the length-critical 915 module beside the only north-south cable
channel on the board. The 433 flex needs 44 of its 100 mm either way. **The SMA bulkhead moves from
x 12.000 to x 5.000** — still top panel, left half, and the move only *improves* both SMA↔IR rules.

### The cable, and a procurement fix that came free

**`095-902-568-100` → RF Solutions `CBA-UFLSMA20IP`, 200 mm** (D-223). The CTO's own threshold
decides it: 138.48 mm is comfortably ≤ 180 mm, so the 200 mm assembly locks and the 250 mm Taoglas
`CAB.01034` stays a recorded fallback. Verified live under D-096 — DigiKey **ACTIVE, 296 in
stock**; CPC **IP67**, 7 in stock; the manufacturer drawing confirms *UFL right angle · waterproof
SMA female bulkhead straight · heatshrink · RG178*. **Mating verdict: COMPATIBLE** — Hirose U.FL
and I-PEX MHF1 are the same interface and the plug gender is right for the `E22-900M22S` socket.
**Spare 46.52 mm beyond the mandated 15 mm service loop. Feed loss ≈ 0.4 dB.**

**And the superseded part was ACTIVE but 0 in stock on a 12-week factory lead.** The replacement is
stocked at two distributors today.

### Three findings the previous pass had wrong

**The ESP32 thermal vias were never in violation.** The board's global floor is
`min_through_hole_diameter` = **0.20 mm**, not 0.30. The twelve errors P1-001 attributed to them
were **twelve `copper_edge_clearance` errors on `J5`**, whose PTH field ended 0.445 mm from the
board edge against a 0.5 mm rule. `J5` moved **0.070 mm** west and all twelve went away. JLCPCB
capability was verified live anyway — 0.20 mm holes in 0.60 mm pads are **supported at no
premium** — and a **narrowly scoped guard** was added to `.kicad_dru` so the manufacturer's array
stays legal if the global floor is ever raised. **The global minimum was not lowered** (D-228).

**`BOSS2` was never legal.** P1-001 placed it at (59.5, 145.0), inside the **mandatory opaque IR
barrier**. Corrected to (59.0, 145.0), with the barrier **widened 3.0 → 5.0 mm** to fill the whole
inter-window gap — strictly better optically, touching neither window — so barrier and boss are now
one moulded feature (D-226).

**Writing the IR forming requirement found that the formed LED did not fit.** A formed `TSAL6100`
occupies **0.6 mm of bend radius + 2.0 mm of straight lead (Vishay's stated minimum from the epoxy
case) + 8.7 ± 0.3 mm of body = up to 11.6 mm** in +Y from its pads. At P1-001's Y = 143.600 the
dome would have ended **1.2 mm outside the enclosure's external top face**. `D1` moved to
(50.750, 141.400); `TP39` and `R123` moved 1.750 mm to clear it; `U6` needs ≈ 9.0 mm and fits
unmoved (D-229).

### Retention: the honest number is two, and it is escalated

**Ø6.0 keep-out — zero legal sites. Ø4.5 — two.** The display owns X 3.39 … 59.93 on the front and
the battery owns X 6.00 … 66.00 on the rear; between them they leave a **3.39 mm left sliver and a
4.00 mm right sliver, both narrower than a Ø4.5 keep-out**. Only the 23.5 mm bottom band and the
8 mm top band can host a through-board screw at all, and each yields exactly one. The top-left
corner and the left margin are now the mandatory 915 coax channel.

Structural support is completed by the enclosure and needs no PCB holes: moulded edge-capture rails
plus four rear non-metallic support ribs on reserved component-free pads, all outside the battery
shadow. **§9 sets three as the acceptable minimum and this outline yields two — escalated, and the
only new item for CTO decision** (D-226).

### `MK1`, and what did not change

`padstack_invalid` **2 → 0**. The GND ring becomes a plain filled Ø1.65 mm SMD pad with the
concentric Ø1.05 mm **non-plated** hole drilling the centre out — same annulus, no custom pad, no
fake plated through-hole. The paste becomes one filled **C-shaped** polygon, the same ID 1.25 /
OD 1.65 ring with a 20° web. **Acoustic opening, annulus dimensions, paste pullback, keep-out and
microphone location all unchanged** (D-227).

**The display Z stack was not spent.** P1-001's recommendation to raise the display support by
≈ 3 mm as the primary 915 solution is **rejected and withdrawn** — the circular geometry closed the
feed without touching Column A's 9.9 mm of unused Z. The **3.34 mm left offset is accepted as
intentional** (D-225).

### Numbers

**DRC 64 → 47**, every one classified: 24 silkscreen, 21 vendor intra-footprint land patterns for
the P2 rule pass, 1 `MK1` mask-aperture artefact left in place, 1 silk edge. **`padstack_invalid`
2 → 0, `copper_edge_clearance` 12 → 0, `lib_footprint_issues` 3 → 0.** **Nothing was fake-cleaned:
no DRC exclusion, no severity change, no relaxed global rule.** ERC **27 / 0 errors**, histogram
byte-identical. Schematic connectivity **unchanged** — the sheets were not opened. Placement
collisions **0**. **ZERO tracks, ZERO vias, ZERO copper pours; 499 unrouted, the correct P1 state.**
`netclass_probe` **PASS**, `fork_equivalence` **PASS** with Beta-DM and the frozen Beta tree
untouched. **FBV2-P2 has not begun.**

---

## 2026-08-24 — the enclosure-driven floorplan, and the cable that cannot reach (FBV2-P1-001)

**FBV2-P1 DOES NOT PASS. Overall stays 68%.** One gate criterion fails — the 100 mm 915 MHz
pigtail does not reach the top-panel SMA — and the floorplan is otherwise complete and
collision-free. Full analysis:
[`audits/2026-08-24-p1-floorplan-implementation.md`](audits/2026-08-24-p1-floorplan-implementation.md).
New working documents: [`pcb/FBV2_P1_FLOORPLAN.md`](pcb/FBV2_P1_FLOORPLAN.md),
[`pcb/FBV2_P1_KEEPOUTS.md`](pcb/FBV2_P1_KEEPOUTS.md),
[`pcb/FBV2_P1_COORDINATES.csv`](pcb/FBV2_P1_COORDINATES.csv), [`pcb/review/`](pcb/review/).

**PCB modification was authorised for the first time, and the board is no longer Beta-DM.**

### The board was rebuilt, not edited

The pre-P1 PCB was still the inherited Beta-DM geometry — 188 footprints, 2,801 track segments,
424 vias, 43 zones — and a floorplan built around a different component set is not a baseline. So
the file was **stripped to its header, layer stack, `general` and `setup`**, keeping the design
rules byte for byte, and **rebuilt from the current nine-sheet schematic**: 321 footprints, one per
component, references and exact verified footprints preserved, **224 nets over 991 pads**, plus a
70.000 × 148.000 mm outline, 13 named mechanical regions, 4 copper rule areas and 3 M2 bosses.

**The schematic was never opened. ERC 27 / 0 errors, histogram byte-identical. Zero tracks, zero
vias, zero pours. 499 unrouted connections — the correct P1 state.**

**`fork_equivalence` now reports the v2 PCB as changed. That is the point of P1, not a failure**,
and the same run confirms Beta-DM is untouched.

### Six rulings, five clean

**F.Cu is the front and B.Cu is the rear**, and `MK1` sits on **B.Cu listening forward through the
board** — 1.21 mm clear of the LiPo, 67.42 mm from the speaker on the opposite face. The apparent
front-face/bottom-face contradiction was a **nomenclature collision between the enclosure face and
the PCB copper face**, not a requirement conflict.

The rear packs **NFC → battery → speaker** at **48 + 75 + 20 = 143 mm in a 155 mm cavity**, with
zero NFC/battery overlap, 81 mm from the speaker to the loop perimeter, and no attempt to squeeze a
Ø20 driver beside a 60 mm battery in a 75 mm cavity.

**USB-C to microSD achieved 16.40 mm body edge-to-edge** against the new ≥ 8 mm rule — twice what
was asked, measured on verified courtyards rather than the approximate widths.

**The internal 915 whip storage is deleted.** The locked `TI.92.2113` is 198 mm long and the
cavity's longest internal diagonal is 172 mm; it never fitted. The freed left wall goes to the
433 MHz flex, which restores D-118's *LEFT / LOWER-SIDE* placement exactly as locked.

### Only three of six mounting bosses close

A boss is a through-board feature. The display owns X 3.39–59.93 above Y 55, the battery owns
X 6.00–66.00 from Y 23.5 to 98.5, and the NFC zone owns X 0.50–48.50 above Y 102 and forbids screws
outright. **There is no 6 mm-wide side strip anywhere on a 70 mm board, and both top corners are
inside the NFC zone.** A full-board search finds **three** legal M2 positions, and only at a Ø4.5 mm
keepout. **Three fixings will not control flex on a 148 mm span with a battery behind it** — that is
escalated, not accepted.

### The 915 MHz feed is the blocker

Every part taller than about 1.2 mm is excluded from the upper half: the front is display shadow
(F.Cu ≤ 0.8 mm) and the rear is battery (≤ 1.2 mm) then NFC clear zone (≤ 1.0 mm, no shielding
cans). The one free strip above the battery is 16.5 mm wide and already carries `J5`'s 31.6 mm
through-hole field. **A 15.89 × 21.34 × 3.5 mm radio module fits nowhere above Y ≈ 55.**

`U8` therefore sits at the bottom rear, and the routed run to a top-panel SMA is **≈ 190 mm**:
**100 mm is short by ≈ 90 mm, and even the superseded 150 mm is short by ≈ 40 mm.** Length is only
half of it — the SMA is locked to the top-edge **left** half and the NFC 48 × 48 zone owns the whole
upper-left, so any coax from the bottom either crosses the NFC zone or runs inside the 5 mm metal
keepout. **No pigtail length fixes this on its own.**

The recommended resolution costs nothing dimensionally: **raise the display support by ≈ 3 mm.**
Column A of the mechanical spec totals 13.1 mm of the 23 mm budget and carries **9.9 mm of unused
Z**. Spending 3 mm of it puts a 3.5 mm module under the panel, frees the entire upper half, and
lets a short pigtail reach.

### Four things the floorplan found on its own

**The display cannot be centred on the enclosure.** `J5` needs 9.2 mm of board on the right and
cannot sit below the battery, so it takes Y 105–137 beside the display band, pushing the panel
**3.34 mm left of centre**. Widening to 72 mm does not fix it.

**`MK1`'s GND ring fails KiCad 10's padstack validator** — it is drawn as a stroked circle outline
rather than a filled annulus. Dimensionally right, structurally invalid; it must be redrawn before
fabrication.

**The stock ESP32 footprint's twelve thermal vias are 0.2 mm**, below this board's 0.3 mm
minimum-hole rule.

**`netclass_probe` was measuring the wrong board.** Its expectation listed `LED_A1`…`LED_A4` —
*Beta-DM* net names. The v2 schematic has one anode net, `/03_SPI_A_DISPLAY_SD/LED_A`, the net
D-111 deliberately added to `LED_BOOST`. It only passed for the last nine tasks because the PCB was
still Beta-DM's. The expectation now follows the schematic; **the guard — `LED_BOOST` must never
capture the IR transmitter nets — is unchanged and still passes.**

Also recorded, because it is written nowhere else: **`D1` and `U6` are flat-mount leaded parts
whose optical axis is normal to the BOARD**, so both must be **formed 90° at assembly** to look out
of the top panel.

## 2026-08-23 — pre-floorplan authority reconciliation, and a part that was never a series pair (FBV2-MECH-002)

**NO PROGRESS EARNED. Overall stays 68%. FBV2-S2 = PASS is unchanged.** This is a reconciliation
and sign-off task, not a design phase. Full analysis:
[`audits/2026-08-23-pre-floorplan-authority-reconciliation.md`](audits/2026-08-23-pre-floorplan-authority-reconciliation.md).
New working document:
[`mechanical/P1_FLOORPLAN_INPUTS.md`](mechanical/P1_FLOORPLAN_INPUTS.md).

**ERC 27 / 0 errors / 27 — histogram identical. Netlist 224 nets / 991 nodes — IDENTICAL. The
schematic diff is PROPERTY-ONLY. The PCB is byte-identical and still bit-identical to Beta-DM.**

### `BAT54WS` is not a series pair, and this programme said it was six times

FBV2-S2-002 wrote a reasonable-sounding inference into the record: `BAT54S` *is* a series pair, so
`BAT54WS` "must be the SOD-323 version of it". **The `S` in `BAT54WS` is a package code, not a
topology code**, and the claim then propagated into the assembly plan §5 and §8, this changelog,
the progress log, **D-206**, and **the `D10`/`D11`/`D12` symbols themselves**. Each copy cited the
others.

**Three independent proofs that it is wrong:**

- **SOD-323 is a two-terminal package.** A series pair needs three terminals.
- **Every `BAT54WS` in the LCSC library, from eight manufacturers, is catalogued `1 Independent`** —
  Diodes Inc, Changjing, Starsea, Hottech, PANJIT, AnBon. There is no series-pair `BAT54WS` in the
  library to substitute *for*.
- **AQROOT never used a pair.** `D10`, `D11` and `D12` are each one two-pin `Device:D_Schottky` on a
  two-pad `Diode_SMD:D_SOD-323`, and `D10`/`D11` form the ratiometric bridge as **two separate
  matched components**.

**The design was never wrong.** That is exactly why nothing caught it — **the error lived only
where nothing is validated by a tool.** The check that resolves it in one step is the one this task
ran: read the distributor's own parametric field.

Nexperia `BAT54W,115` stays rejected, **for the right reason**: it is **SOT-323 (SC-70)**, a
**footprint** mismatch against `Diode_SMD:D_SOD-323`, and it has 5 in stock against a need of 15.

### Two substitutions signed off, and the consignment list got shorter

| ref | now | LCSC | live state | route |
|---|---|---|---|---|
| `F1` | **Littelfuse `0466005.NRHF`** | **`C57525`** | **29,328** in stock, JLC **Extended** | class C → **class B, machine-placed** |
| `D10`–`D12` | **Diodes Inc `BAT54WS-7-F`** | **`C124205`** | **46,819** in stock, JLC **Extended** | class D → **class B, machine-placed** |

`F1` is the **halogen-free ordering option of the same Littelfuse 466 / Nano2 family** — and the two
LCSC records carry a **character-for-character identical parametric string**, so the distributor's
own data does not distinguish them electrically at all. Same footprint, same function, **not one
net, pin, wire, label or junction touched**.

**The `D10`/`D11` bridge is structurally insensitive to the parameter that changed.**
`INA+ − INA− = (BAT_RAW + V_F11 − V_F10) / 2` — the absolute Schottky drop **cancels**, and only the
mismatch survives. Each leg runs **≈ 1.1 µA** through 4.4 MΩ, six orders of magnitude below the
100 mA rating, and matching **improves** because both diodes now come from one MPN on one order
line. `D12` carries **≈ 16.6 mA worst case against 100 mA continuous — 6×** — and re-solving D-105
with this part's V_F gives **7.9–8.9 mA, still inside the accepted 5–10 mA band, so D-105 needs no
revision.**

**Consignment: 11 → 9 part numbers. Class D is now EMPTY. Hand-soldered parts per board: still
exactly two, `J5` and `D1`.**

### The mechanical spec disagreed with itself in six places

`MECHANICAL_INTERFACE_SPEC.md` is the authority for FBV2-P1, so a stale row in it is a defect that
propagates into a floorplan.

- **NFC zone 45 × 45 → 48 × 48 mm, LOCKED.** The 48 mm figure was ruled at FBV2-S1-004B and already
  sat in this document's own NFC banner. **Four places had never been updated — including the
  machine-readable block a guard script parses.**
- **`J1` land pattern.** Every current claim that `J1` uses the **FH12/FH52E standard land pattern**,
  that **FH52E is a drop-in second source**, or that **mating equivalence was proven**, is removed.
  Current truth: **FH69 dedicated footprint · FH52E not drop-in · single-source connector
  architecture · the genuine Hirose is JLC machine-placeable · re-check stock before ordering.**
- **`J1` is not manual assembly.** M-13 and the header both said it was; D-206/D-207 superseded that
  the same day. **Exactly two parts are manual per board.**
- **Speaker Z column 4.0 → 3.0 mm**, total **13.6 → 12.6 mm**. D-148 locked Ø20 × 3.0 and stated it
  released 1 mm of Z — and the derived column in the same document still summed 4.0.
- **§4.1 content list.** "changes the connector from **26 to 20 pins**" → **24 contacts, 2 × 12 at
  2.54 mm**; "removes HOME **and the RGB nets**" → a **front RGB status light `D13` was added**.
- **IR receiver naming** now puts the locked `TSOP38238` first and `TSOP38438` in parentheses.

### The 8 mm / 15 mm spacing was not a contradiction — and it was not resolved by preference

Both figures were in the document and it would have been easy to strike one. **The trace says
neither is stale.** The **≥15 mm** rule is FBV2-MECH-001, 2026-08-22, **centre-to-centre**, written
against a generic whip shadowing the emitter cone. The **≥8 mm** rule is **D-120**, 2026-08-23,
**edge-to-edge, SMA body to IR aperture**. **M-13 — the latest ruling to touch this, written after
D-120 and with the Amphenol bulkhead already chosen — states both in the same sentence.** So 15 mm
was **re-asserted**, not superseded.

**The actual defect was that neither figure said what it was measured between.** Both now carry an
explicit datum in a new **§8.1 authority trace**, with the consistency check written out: on a
~9.5–11 mm SMA hex body and a ~Ø5.5–6.0 mm aperture, **8 mm edge-to-edge implies ≈ 15.5–16.5 mm
centre-to-centre**, so the two agree and **8 mm is the binding one — satisfy whichever is larger.**
The Amphenol body OD is **CAD-TO-VERIFY**; **B-52 stays open and no CAD was created.**

### Six things P1 cannot floorplan around, surfaced not decided

The sharpest two are arithmetic, not opinion.

**The rear face is over-constrained by ≈ 8 mm.** It must hold, in Y: battery **75** + NFC clear zone
**48** + speaker **Ø20** + the **≥20 mm** speaker-to-loop separation = **163 mm against a 155 mm
cavity**. Putting the speaker beside the battery does not rescue it — a 60 mm battery in a 75.0 mm
cavity leaves **7.5 mm per side** against a Ø20 driver. And that is *before* the 5 mm NFC metal
keepout, the shell lip and the bosses. **All four constraints are currently recorded as binding;
one of them has to give.**

**The internal antenna storage channel cannot hold the locked 915 antenna.** §8 reserves a left-wall
channel *"sized for the stowed whip"*. The locked whip is Taoglas **`TI.92.2113`, 198 ± 3.3 mm ×
Ø13 mm**; the cavity's longest internal diagonal is **≈ 172 mm**. **It does not fit in any
orientation** — and that same left wall is the **LOCKED** mount region for the 433 MHz flex.
Withdrawing the storage requirement would free the entire left wall, which is the largest single
simplification available before floorplanning.

Also raised: the **microphone board-face assignment** (front aperture + bottom-port part = `MK1`
must sit on the copper face away from the front shell, and that side has never been assigned); the
**mid-span boss at Y ≈ 100** now inside the grown NFC keepout; the **microSD ↔ USB-C "≥8 mm
centre-to-centre"** figure, which is smaller than the two bodies physically allow (~11.6 mm before
they touch); and the **150 mm 915 pigtail** in a 155 mm cavity. **No substitution is proposed for
the pigtail — D-195 locked that MPN.**

## 2026-08-23 — S2 release closeout: the footprint that wasn't broken, and six wrong parts (FBV2-S2-002)

**Overall raised 62% → 68%. FBV2-S2 = PASS** — the second of the twelve gates to pass. Full
analysis: [`audits/2026-08-23-s2-release-closeout.md`](audits/2026-08-23-s2-release-closeout.md).
New working document:
[`assembly/FIRST_FIVE_ASSEMBLY_PLAN.md`](assembly/FIRST_FIVE_ASSEMBLY_PLAN.md).

**ERC 27 / 0 errors / 27 — the violation-type histogram is identical to the FBV2-S2-001 baseline.
The schematic diff is property-only. The PCB is untouched and still bit-identical to Beta-DM.**

### The MAX98357A footprint looked broken and was not

Maxim outline **21-0136** lists exposed-pad variations in which **`T1633-5` is 1.50 / 1.60 /
1.70 mm** while `T1633-2/-4/-7C` are 0.95 / **1.10** / 1.25. The KiCad footprint cites
**21-0136 (T1633-5)** in its own `descr` and then draws a **1.23 × 1.23** land — sized for the
1.10 family. That is a footprint contradicting its own citation, on a thermal pad, and the obvious
move was to fork a corrected project-local footprint.

**Maxim land pattern 90-0032 Rev E dissolves it.** The drawing is issued under **PKG. CODES
[T1633-5], [T1633-5C] and [T1633-7C] together** and specifies **one land for all three** — EP
**1.23 × 1.23**, pads **0.80 × 0.30**, pitch **0.50**, centreline span **2.85**. Maxim
deliberately recommends a land smaller than the T1633-5 pad, **so the question of which variant
`MAX98357AETE+T` carries does not have to be answered to get the land right** — which is
fortunate, because analog.com, Mouser and LCSC all refused the datasheet in this environment.

Against the library file: **EP exact, pitch exact, inner pad edge exact at 1.025** — so
EP-to-signal clearance is Maxim's own 0.410 mm — pad centre **+0.0125** (inside the drawing's own
±0.02), length **+0.025**, width **−0.05**. **No project-local footprint was created.** Forking
one to chase 0.05 mm of pad width, buying a side fillet at the cost of a thinner mask dam at
0.5 mm pitch, would have been a change made for the sake of having made one. **The right outcome
of a verification is sometimes "it was already correct" — but only after the drawing is read.**

**All eight remaining Tier-2 footprints are now Tier 1**, compared dimension by dimension. `Y1`'s
land is an **exact** match to the vendor's own Suggested Layout (1.4 × 1.2 at (±1.10, ±0.85)), and
`Y1` itself moves from **candidate to lock** — `C362365`, 3,421 in stock, ±30 ppm total against an
ISO/IEC 14443 requirement of ±516 ppm.

### The microphone port existed only as a sentence

`AQROOT_Beta:PUI_DMM-4026-B-I2S_4.0x3.0mm` was Tier 1 for its pads, and its `descr` then said the
acoustic port was *"NOT PART OF THIS FOOTPRINT … an FBV2-S2 / PCB-stage item."* **A port that
lives in a description is a port that gets forgotten at placement.**

It is now drawn: **Ø1.05 mm NPTH** — **the diameter is not invented, it is the inner diameter of
the manufacturer drawing's own pad-4 GND ring**, i.e. the part's own aperture — plus a **paste
pullback**, pad 4 losing `F.Paste` entirely in favour of a separate **ID 1.25 / OD 1.65** annular
aperture **0.10 mm** back from the copper edge. **The 0.10 mm is a declared stencil design choice,
not a drawing dimension, and the footprint says so.** Keepout marked on `B.Fab` and
`User.Comments`; **bottom-port orientation** — the part listens *through* the board, so the
enclosure aperture belongs on the **bottom** face — recorded as **M-14**.

### Six substitution traps, and two MPN strings that would have stalled the order

All 46 MPNs were checked against **live JLCPCB parts-API state**. A loose keyword search **returns
a plausible wrong part more often than it returns nothing**:

- **`BAT54W,115` offered for `BAT54WS,115`** — ~~a **single diode** for a **series pair**~~ ***CORRECTED 2026-08-23 by D-211: `BAT54WS` IS NOT A SERIES PAIR.* SOD-323 is a two-terminal package and `D10`–`D12` are each ONE independent diode; `BAT54W,115` is wrong because it is SOT-323 (SC-70) — a FOOTPRINT mismatch.**
- **G-Switch `GT-TC089A-H043-L1`** for **C&K `PTS645SM43SMTR92LFS`** — 35 placements
- **FUXINSEMI `SD103AWS`** for **onsemi `NSR0240HT1G`**
- **LRC `LBSS138LT1G`** for **onsemi `BSS138LT1G`**, which has 762,522 in stock
- **KOHERelec `SPM4030-1R0M`** for **Würth `74438357010`**
- a **VBsemi clone** for **onsemi `NTMD4820NR2G` — the battery reverse-polarity pass FETs**

**Every one is now recorded in the schematic symbol itself.** No substitute was adopted;
`BAT54WS-7-F` and `0466005.NRHF` are candidates awaiting sign-off.

**`J4` and `J6` are the same JST PH header and carried two different MPN strings.** Not cosmetic:
the bare order code is `C20504437` with **stock 0**, while `B2B-PH-K-S(LF)(SN)` is `C131337` with
**378,913**. `J7` had the identical fault. **A BOM that produces two lines for one part, one of
which cannot be filled, is a BOM that stalls at the quote stage.**

### The build closes — through consignment, not through hand assembly

**Two through-hole parts per board are hand-soldered (`J5`, `D1`). Zero fine-pitch or QFN parts
are hand-placed.** Ten parts have stock short of the first-five need and one is not in the LCSC
library at all; **all are consigned to JLC and stay machine-placed.** The sharpest case is
`U2`/`U3`/`U23` — **fifteen TSSOP-24 at 0.65 mm pitch against one in stock**. **`J1` improves**:
JLC carries the genuine Hirose `FH69-50S-0.5SH` with 1,072 in stock, so the display connector is
machine-placed after all.

### The NFC numbers are now datasheet numbers

DS12484 Rev 3 finally came through a **mikroe.com mirror** after st.com timed out repeatedly.
**`I_AL-AM` max 26 mA** for the IC with all blocks active plus **≈ 60 mA** for the driver into
D-134's *actual* first-build network → **allocate 100 mA**, replacing D-130's ≤ 150 mA estimate.
**Table 118's 350 mA and 500 mA are absolute maximum ratings and were deliberately not used** —
that is exactly the number a careless budget grabs. TPS63020 lands at **63–71 % of 2 A**.
**One binding guard rail: D-134 records that `C_s` 300 pF → 270 pF draws ≈ 257 mA, which this
allocation does not cover.**

**`L5`/`L6` = Murata `LQW18AN39NG80D`** — and the useful finding is that **the DCR is not
negligible**. `R_q` is only **1.1 Ω** per arm, so **0.20 Ω max drops the network Q from 25.3 to
≈ 21.4**. That moves further into the safe, under-driven side D-134 chose, but **the antenna must
be bench-tuned with this exact part fitted**, and **if the field is short the first lever is `R_q`,
not 39 nH.**

### Eight DNP parts still had no recorded reason

After seven consecutive sheets of load-bearing inherited `DNP`, an unexplained one is the single
thing this project cannot afford to leave lying around. **`U13`, `L2`, `R44`, `R45`, `C34`, `C35`
are the NFC 5 V boost branch** — correct, and a D-049 no-respin escape if the 3.3 V field measures
short. **`R119`** is the BMI270 alternate-address strap, **mutually exclusive with `R118`**.
**`R112`** isolates the display `SDO` from the shared MISO and **must not be fitted while MX-8 is
relied on**. **All eight now carry a note; the design has zero unexplained DNP.**

### O-8 — verified, not accepted

Taoglas **`TI.92.2113`** against **SPE-19-8-076/A**: 902–928 MHz, terminal-mount dipole, hinged
SMA(M), 198 ±3.3 mm × Ø13 mm, 1 W max input, and Taoglas' own statement that it *"performs very
well in free space … where there may be no ground plane."* Every expectation checks out. **Worth
saying anyway: the marketed "2 dBi" is the bent-configuration peak — the table gives 1.21 dBi
straight and negative average gain in both orientations. Budget the link with the average.**

### What was NOT done

No PCB placement, no routing, no outline change, no mechanical CAD, no firmware, no Beta-DM, no
frozen Beta. **No honest ERC warning was "fixed"** — no no-connect, power flag, pin electrical
type or exclusion was added, removed or altered anywhere. **No product feature was added.** No
part was substituted. Passive values remain unconsolidated.

---

# AQROOT Full Beta v2 — Changelog

Chronological engineering changes and why they happened. Newest entries at the
top. Each entry records what changed, not merely that something happened.

This file records **decisions and design changes**. Routine document edits are
not entries. A change that alters what gets built, or what may not be built, is
an entry.

---

## 2026-08-23 — Pre-placement release audit, and NFC was still DNP (FBV2-S2-001)

**Overall HELD at 62%. FBV2-S2 = FAIL on two of fourteen exit criteria** — and the audit earned
its keep on the first one it looked at. Full analysis:
[`audits/2026-08-23-s2-preplacement-release-audit.md`](audits/2026-08-23-s2-preplacement-release-audit.md).
Working documents:
[`assembly/FIRST_FIVE_POPULATION_MATRIX.md`](assembly/FIRST_FIVE_POPULATION_MATRIX.md) ·
[`assembly/SOURCING_LEDGER.md`](assembly/SOURCING_LEDGER.md) ·
[`assembly/FOOTPRINT_VERIFICATION_LEDGER.md`](assembly/FOOTPRINT_VERIFICATION_LEDGER.md) ·
[`assembly/OFF_BOARD_BOM.md`](assembly/OFF_BOARD_BOM.md).

**ERC 27 / 0 errors / 27 — unchanged. PCB untouched and still bit-identical to Beta-DM. No
percentage was awarded, because no gate passed.**

### The NFC chip was still marked DNP

`U9` **ST25R3916-AQET** and its **twelve mandatory supply-decoupling capacitors** were inherited
from Beta-DM marked `DNP` — against **D-035**, *"NFC is mandatory in the FIRST Full Beta v2
fabrication. No DNP showcase shortcut"*, and **D-055**, *"NFC must be FITTED and functional on the
first fabrication."*

**Everything around the chip was already fitted**: the 27.12 MHz crystal, the complete differential
matching network `C69`–`C80` / `L5` / `L6` / `R114`–`R117`, the antenna connector `J7`, the SPI
wiring, the `NFC_SUPPLY` selector. **The first five boards would have been built with a finished
13.56 MHz front end and no NFC chip on it.** All thirteen parts are now FIT.

**This is the seventh consecutive sheet carrying a load-bearing inherited `DNP`, and it is the one
that hid longest.** It survived four migrations because sheet 04's own migration
(FBV2-S1-004/4B/4C) was about the antenna and the matching network — nobody re-read the population
state of the IC underneath it. **The lesson is now a standing one: migrating a subsystem is not the
same as auditing its population.**

### Two carried numbers were wrong, and one register was full of ghosts

**`D-077`'s display second source does not exist.** It states that `J1` is *"laid out on the
FH12/FH52E standard land pattern so `FH52E-50S-0.5SH` is a drop-in second source."* Both Hirose
land patterns were read. **FH69: signal land 0.30 × 1.23, hold-down 0.36 × 4.25 at 28.73 c/c,
overall layout depth 7.38 mm, top-and-bottom two-point contact, back-flip actuator. FH52E: bottom
contact only, front-flip actuator, 0.8 land, 4.6 mm depth datum** — and the FH52 catalogue says in
its own words that its pattern is interchangeable with the **FH12**, not the FH69. **7.38 mm against
4.6 mm: they cannot share pads. The claim is struck**, and `J1` is confirmed as **manual assembly**
for the first five. Placement would otherwise have proceeded believing a second source existed.

**The accessory boost settle delay was derived against the wrong capacitance.** FBV2-S1-009 quoted
the TPS61023's 700 µs soft start as "seven times typical" for a 5 ms wait. The datasheet's
condition line says that 700 µs is at **C_OUT_EFF = 10 µF**. `C65` + `C66` are 2 × 22 µF 10 V X7R
0805, which at 5 V bias retain 40–60 % of nominal — **≈ 20 µF effective, twice the datasheet
condition**. The real margin was **3.5×, not 7×**, and the datasheet publishes no maximum.
**The first-build wait is raised to ≥ 10 ms** — a firmware constant, zero hardware cost, measured
at first article.

**Nine register entries were stale** and were closed on evidence: **P-01** (the reverse-polarity
path is fully built and FBV2-A1 passed in August), **P-04** (NFC is fully designed — and now
fitted), **B-45** (`NATIVE_A`/`NATIVE_B` gained their 100 Ω and TVS at FBV2-S1-009), **B-49**,
**B-51**, **B-53**, **B-68**, plus **B-46** and **B-47** resolved below. A register that carries
ghosts is a register nobody trusts.

### P-14 — the fuel gauge stays where it is

The CTO asked whether the MAX17048 should move to the clean node after the reverse-polarity FETs
but before the 15 mΩ sense resistor. **It should not — and it was never on `BAT_RAW`.** Measured
from the netlist, `U14` `CELL` and `VDD` are **already on `BAT_PROTECTED_P`**, the fully protected
node.

`BAT_SENSE` is the **LTC4368's precision current-sense input**. Hanging a gauge's `VDD` and its
bypass capacitor there puts a **differential capacitance across `R75`** that distorts the
reverse-current comparator during fast current steps, opens a deliberate blind spot in a protection
measurement, and injects I²C transients onto the sense node. **What it would buy is inside the
noise:** 15 mΩ costs 26 mV at the 1.75 A pack worst case, 4.5 mV at typical idle — **≤ 2.6 % SOC at
peak load, < 0.5 % typical** — which is coarser than the MAX17048's own ModelGauge error and is
**compensable in firmware by subtracting I × 15 mΩ**. **Safety outranks SOC accuracy.**

### RF is now fully sourced

**B-49 was never a risk:** Ebyte ships both the `E07-400M10S` and the `E22-900M22S` with **IPEX
*and* stamp holes on the standard part number** — there is no variant selection to get wrong.

**B-51 closed: Amphenol RF `095-902-568-150`**, Part Status **ACTIVE** — AMC right-angle plug →
**SMA straight bulkhead jack, IP67**, RG-178, 50 Ω, **150 mm**, 6 GHz, and Amphenol documents the
AMC series as **"compatible with Hirose U.FL and IPEX MHF1"**. **It is one assembly: pigtail and
panel bulkhead in a single orderable part**, so no separate bulkhead MPN exists or is needed. Loss
≈ 0.4 dB against a +22 dBm module. **433 MHz: Taoglas `FXP450.07.0100C`**, 410–470 MHz, MHF1,
100 mm, stocked at DigiKey/Arrow/TTI.

### B-46 closed, and the guess was right

Molex sales drawing **SD-502570-001 Rev A**, note 4: **CARD INSERTING POSITION = CLOSE, NO CARD =
OPEN.** With the detect lever grounded — the drawing's own pattern labels that land *"Vss :
GROUND"* — and `R113` pulling up, **card present drives `SD_CARD_DETECT_N` LOW**, exactly as D-117
assumed. **No firmware correction, no hardware change.**

### Two undocumented placeholders, one of them dangerous

**`R68` is a 0 Ω DNP bypass across `SW9`, the hard power switch.** Fitting it wires the unit
permanently ON and **defeats the one provision that lets a user power down a hung or unflashed
board** — the architecture is explicit that `SW9` is not a GPIO for exactly that reason. It arrived
from Beta-DM **with no note at all**. It is now marked **DNP AND IT MUST STAY DNP**.

**`C21`/`C22` are dead pads** — DNP with one terminal deliberately no-connect flagged, so fitting
them does nothing. Reserved rework pads by the USB block, usable only by cutting a trace.
Documented, and flagged as deletion candidates at placement.

**Six missing MPNs were added** — `D9` → `PMEG2010AEH,115`, `Q4`/`Q6`–`Q9` → `BSS138LT1G`. **Every
active and every connector now carries an exact MPN, and there are zero unexplained DNP.**

### What fails the gate

**B-03 — eight of twenty-eight critical footprints are traceable to a vendor part but have not been
read against a manufacturer drawing:** the ESP32-S3-WROOM-1 module, the GCT USB-C receptacle, both
JST families, the PTS645 and JS102011SAQN switches, the MAX98357A TQFN exposed pad and the NFC
crystal. The standing instruction is explicit — *do not mark a footprint verified because the
library name looks right* — so they are not marked verified. **They do not block placement; they
block fabrication release.** Fifteen are properly verified, including `U11` BQ25185, checked in
this task against TI's own `DLH0010A` board-layout drawing 4226298/A.

**B-71 (new) — only 7 of 46 unique MPNs carry an LCSC code**, so the JLC Basic/Extended split, the
assembly quote and the manual-placement list cannot be produced from the current metadata.
**B-70 (new) — `L5`/`L6`, the 39 nH NFC EMC inductors, have no MPN at all**; a tuned RF inductor
needs a specified part, not a value and an 0603 outline. **B-54 also sharpens: the ST25R3916 field
current at 3.3 V is still not extracted, and that now loads a rail the part is actually fitted on.**

### O-8 — one new item for the CTO

**The 915 MHz external whip antenna MPN is not selected.** Everything from the module socket to the
panel bulkhead is locked and orderable; the antenna that screws onto the outside is not.
Accessory-class, no board impact — but a range test means nothing without it.

### What was NOT done

No PCB placement, no routing, no outline change, no mechanical CAD, no firmware, no Beta-DM, no
frozen Beta. **No honest ERC warning was "fixed"** — no no-connect, power flag or pin-type was
added or altered anywhere. All seven `PWR_FLAG`s were individually traced to a real supply.
Passive values were **deliberately not consolidated**: doing that before the layout exists
optimises the wrong thing.

---

## 2026-08-23 — Community expansion port, and the schematic migration is complete (FBV2-S1-009)

**Overall 55% → 62%. FBV2-S1 = PASS — the first twelve-gate entry to pass since FBV2-A2.** Task
gate **FBV2-S1-COMMUNITY = PASS**. Full analysis:
[`audits/2026-08-23-s1-community-sheet09-implementation.md`](audits/2026-08-23-s1-community-sheet09-implementation.md);
programme closeout:
[`audits/2026-08-23-s1-schematic-migration-closeout.md`](audits/2026-08-23-s1-schematic-migration-closeout.md).

**ERC 42 / 1 / 41 → 27 / 0 / 27. THE DESIGN HAS ZERO ERC ERRORS FOR THE FIRST TIME.** 321
components, 0 duplicate references, 0 without a footprint, 224 nets, 0 `*_TBD`.
`fork_equivalence.py` PASS with an **empty** "still Beta-DM" list, `netclass_probe.py` PASS, PCB
still bit-identical to Beta-DM.

> **FBV2-S1 = PASS means SCHEMATIC MIGRATION COMPLETE. It does not mean fabrication ready.**
> No placement, no routing, no outline, no DFM, no mechanical CAD, no physical validation.

### Three CTO rulings recorded first

**O-6 RATIFIED (D-175).** `U23`, the third `PCAL9535APW,118` at `0x22`, and the front RGB status
light are now **locked architecture**. **B-37 — "zero expander spare", carried since the first
audit — is retired**: 37 of 48 expander pins are used and eleven are free.

**O-4 APPROVED (D-176).** `U16` TCA9517A → **TI `TCA4307DGKR`, LCSC C880333**, verified live per
D-096 at 3 248 in stock. **It is FITTED; the TCA9517A was DNP.**

**P-18 CLOSED (D-178). No I²C mux.** The external segment stays one logical address space with
the internal bus. **The TCA4307 solves *electrical* fault isolation; the address registry solves
*address* allocation.** A mux would add a part, a failure mode and a firmware dependency to
answer a problem a published reserved-address policy already answers. `0x50` is not widened.

### Sheet 09 was rebuilt, not patched, and what it was hiding

Almost nothing in the inherited Beta-DM community sheet survived contact with the locked v2
architecture — and two of its defects were serious:

- **`J5` contact 1 carried permanent raw `+3V3`**, against D-057.
- **The community port had no power at all.** `01:ACC_3V3_SW` — the real switched rail at `U20` —
  and `09:ACC_3V3_SW`, fed by a **second, DNP** TPS22918 (`U15`) that nobody had noticed was
  there, were **different nets**. `01:ACC_5V_SW` reached nothing outside sheet 01.
- 26-pin 2×13 **male** header, fourteen XGPIO, `FAST_IO_GPIO43_HDR` (withdrawn by D-106),
  `RESERVED_NC`, and `R66` wired straight through with **no isolation FET**.

**This is the sixth consecutive migrated sheet on which an inherited `DNP` was load-bearing** —
`U16`, `R49`, `R50` and six TVS arrays. The pattern first recorded at FBV2-S1-007 held to the
last sheet without a single exception.

### The connector footprint was re-derived from the drawing

`J5` = Samtec **`BCS-112-S-D-HE`**, re-confirmed live: ACTIVE, 385 pieces ship tomorrow. The land
pattern comes from the Samtec **RECOMMENDED PCB LAYOUT, REVISION B, FIG 3** — the
`BCS-1XX-XXX-D-HE-XXX` figure specifically: **2.54 mm within a row, row-to-row .310 ±.002 in =
7.87 ±0.05 mm, .028 in = 0.71 mm PTH**, 27.94 mm pin field. **A vertical 2×12 pattern is not a
substitute — its rows sit 2.54 mm apart.** Odd = row A, even = row B, verified pin by pin against
the netlist; all 24 contacts match D-084. If JLC cannot place a through-hole part automatically
it becomes **manual/secondary assembly for the first five boards**; the connector architecture is
not compromised for SMT convenience.

### The buffer change is not cosmetic

The community port is **hot-plug** and its external segment is **3.3 V only**, so the TCA9517A's
level translation was never used while its hot-insertion and stuck-bus weaknesses were. From
SCPS270B, read in this session: the IN side is not joined to the OUT side until a **STOP or
bus-idle**; **1 V precharge** on all four SDA/SCL pins; **stuck-bus recovery at
`tSTUCKBUS` 25 ms MIN / 40 typ / 65 MAX** followed by **up to 16 pulses on SCLOUT**; **powered-off
high-impedance I²C pins**; 400 kHz max — **fast mode, not 1 MHz**.

**The circular dependency is broken.** `ARCHITECTURE.md` recorded it plainly: *"its disable
control, `ACC_PWR_EN` = `U3` P17, sits behind the bus it protects."* A wedged accessory required
the MCU to command the expander **over the very bus that was wedged**. The buffer now disconnects
and clocks the bus free by itself; `ACC_PWR_EN` is a second, manual lever rather than the only
one.

> **Normative accessory rule (D-177): never hold `EXT_SDA` or `EXT_SCL` low for longer than
> 25 ms** — the `tSTUCKBUS` **minimum**, not the typical. That is a hard limit on clock stretching
> and on slow bit-banged accessory firmware.

### The inherited pull-ups could not have worked

`R49`/`R50` were **4.7 kΩ and DNP**. With `tr` = 0.8473 × R × C and a 200 pF external bus —
≈ 20 pF board, 5 pF connector, ≈ 100 pF for 300 mm of cable, 50 pF module — 4.7 kΩ gives **796 ns
against a 300 ns fast-mode budget: it fails 400 kHz by 2.7× and only ever worked at 100 kHz.**

**1.5 kΩ gives 254 ns and passes fast mode on the static pull-up alone**, with the TCA4307's
2–5 mA rise-time accelerator as margin rather than as the mechanism. Static sink 1.93 mA, inside
the 3 mA an I²C device must sink. **Published accessory rule: ≤ 200 pF for 400 kHz, ≤ 400 pF for
100 kHz bring-up.** The internal bus keeps `R19`/`R20` 2.2 kΩ as its only pair (D-139); nothing
was added there, and no 1 MHz claim is made anywhere.

### Both current limits were re-derived rather than copied

SLVSFJ2B gives **`ILIM` = 1.18 × (R_ILIM in kΩ)^−1.072**, verified against three datasheet rows,
±25 % band.

**3.3 V rail — 1.5 kΩ retained, and it survived a budget that has grown.** The IR transmitter
(+50 mA burst average; its 150 mA peaks come from `C12` 22 µF, not the rail) and the front RGB
(+4.2 mA) push the internal worst case from 769 mA to **≈ 823 mA**. An accessory hard short at the
0.955 A worst-high limit now puts `+3V3` at **1 778 mA = 89 % of the TPS63020's 2 A** — margin
narrowed from 86 %, **still no foldback**. 1.21 kΩ would reach 102 %. Worst-low 0.573 A against
the published 400 mA leaves 43 % headroom.

**5 V rail — 1.65 kΩ retained**, 0.690 A typ / 0.52–0.86 A, 73 % headroom over the published
300 mA and inside the boost's 3.7 A switch limit. Setpoint re-checked at **4.99 V**; peak inductor
current **2.19 A** at `V_SYS` 3.0 V, so **`I_sat` ≥ 3 A is a requirement to confirm at BOM lock
(B-68)**. **Verified from the netlist to be electrically independent of USB `VBUS` and of the NFC
5 V fallback** — only `SYS` and the TPS61023 device family are shared.

**Published limits for the first five boards remain 400 mA and 300 mA TOTAL — the duplicate
contacts share one rail limit and do not multiply it.**

### Splitting the 5 V enables buys more than tidiness

`ACC_5V_EN` becomes **`ACC_5V_BOOST_EN` (`U3` P13 → boost `EN`)** and **`ACC_5V_SW_EN`
(`U23` P04 → switch `ON`)**, each with its own 100 kΩ pull-down — `R102` and the new **`R131`**,
which is mandatory because the TPS22950C's internal 500 kΩ smart pull-down does not satisfy its
own datasheet.

Two gains beyond the obvious. **Two independent series disconnects**: the TPS61023 has *true*
input-to-output disconnection in shutdown and the load switch adds reverse-current blocking, so a
single stuck enable can no longer energise the contact. And **the start-up time becomes a board
constant** — with the load switch still off, the boost starts into a known **44 µF** of
`C65`/`C66` instead of an unknown hot-plugged accessory.

The **5 ms** settle delay is derived, not guessed: the TPS61023 soft start is **700 µs typical
with no published maximum**, so the first build uses 7× typical and measures it (**B-69**).
**No PGOOD IC was added.**

### B-08 exists in copper for the first time

`Q10` 2N7002 between the WAKE contact and `WAKE_INT_N`, gate on `ACC_3V3_SW`. **Orientation is
load-bearing: source to the connector, drain to the internal line**, so with the rail off an
accessory pulling the contact down **reverse-biases the body diode** against the internal 3.3 V.
Reverse the FET and the body diode alone defeats the arrangement. A shorted or hostile accessory
therefore **cannot hold `WAKE_INT_N` low and cannot starve the internal buttons**. `R63` 10 kΩ
must pull to `ACC_3V3_SW`, not `+3V3`, or the contact stays live with the rail off. Recorded
honestly: a hostile accessory *driving* the contact to 5 V injects **≈ 3 mA** through the body
diode and `R66` — bounded, inside every clamp, and the reason `R66` is 330 Ω.

### The ESD arrays were all DNP; they are now fitted

**TI `TPD4E1B06DRLR`** — 4-channel bidirectional, **±12 kV contact / ±15 kV air-gap**, **0.7 pF**
I/O capacitance, 0.5 nA leakage, `VRWM` ±5.5 V. Four arrays cover all sixteen exposed signal
contacts. D-090 protected only the natives and the I²C pair, on the reasoning that the natives are
the only contacts with a direct MCU path; **that under-weighted the XGPIO**, which reach a
PCAL9535A whose destruction costs a board rather than a $0.55 chip. **Deliberately no TVS on
either power rail** — `VRWM` 5.5 V against a 5.0 V nominal rail leaves no working margin, and a
clamp that close leaks and ages. **`TPD2E009DBZR` leaves the BOM**: one TVS MPN now covers
everything.

An inconsistency in D-090 was also closed: **`ACC_DETECT_N` had no series resistor** despite being
exposed and running straight to a PCAL input. It now has 100 Ω like every other signal contact.

### Detect bounce is a firmware problem, and an RC would make it worse

Debounce is **20 ms assert / 20 ms de-assert in firmware**. A passive filter cannot be asymmetric:
the same time constant that suppresses insertion chatter **delays removal detection**, and removal
is the safety-critical edge because **MX-6 requires both rails down within 100 ms of detect loss**.
No RC was added.

### Eighteen abuse cases, none unacceptable

The full matrix is in the audit. Nothing lands on NOT ACCEPTABLE; two rows are firmware-dependent
by design and both are already binding clauses of D-092. Highlights: a reversed accessory cannot
ground contact 23, so **detect never asserts and neither rail is ever enabled**; a one-column
offset is prevented mechanically by the closed-ended recess; `EXT_SDA` or `EXT_SCL` held low is
disconnected within 25–65 ms and clocked free; and 5 V on a logic contact is clamped by the TVS
with 100 Ω limiting the residual into a **5 V-tolerant** PCAL input.

### A correction worth recording

Rebuilding sheet 09 deleted **`#FLG0105`**, a `PWR_FLAG` sitting on the Beta-DM community sheet
that turned out to be **the only power-output driver on the entire GND net**. Its loss made every
GND `power_in` pin in the design undriven. It has been **re-created on sheet 09 with the same
reference and a note explaining its role**, so it is never deleted by accident again. This is not
a fake power flag added to silence a check — it is the restoration of the check's only legitimate
satisfier.

### One new item for the CTO

**O-7:** `R49`/`R50` are 1.5 kΩ sized for a **200 pF** external bus, and that capacitance is an
estimate rather than a measurement. Accept 200 pF as the published 400 kHz ceiling, or drop to
1.0 kΩ and cover 300 pF for 1 mA more static sink. **One 0603 either way, footprint fitted**, so
it closes on the first measured board.

---

## 2026-08-23 — Buttons, expanders and the front RGB status light (FBV2-S1-008)

**Overall 53% → 55%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-BUTTONS = PASS**. Full analysis:
[`audits/2026-08-23-s1-buttons-expanders-rgb-implementation.md`](audits/2026-08-23-s1-buttons-expanders-rgb-implementation.md).

**ERC 42 messages / 1 error / 41 warnings — the violation set is identical, line for line, to
the working tree this task resumed from, and better than the 45 / 2 / 43 that stood before
sheet 08 was touched.** Zero new errors. 319 components, 0 duplicate references, 0 without a
footprint, 0 `*_TBD` nets. `fork_equivalence.py` PASS, `netclass_probe.py` PASS, PCB still
bit-identical to Beta-DM. **Sheet 09 untouched.**

### This task was interrupted by a session limit and resumed, not restarted

All FBV2-S1-008 work existed as **uncommitted working-tree change** — nothing staged, no local
commits, local `master` equal to `origin/master` at `d894913`. The interrupted session had done
good work and it was kept: both expanders genuinely converted to `PCAL9535APW,118` with a
purpose-built symbol rather than a rename, addresses `0x20`/`0x21` preserved, HOME deleted
outright, volume buttons not invented, `TOUCH_INT_N` and `SX1262_DIO1` landed with matching root
plumbing, and the RGB part selected, symbolised and footprinted from the manufacturer drawing.
Zero DNP anywhere on the sheet — **the fifth consecutive sheet did not repeat the inherited-DNP
trap**.

It had also written an honest note into the schematic saying the pin budget did not close and
needed a ruling. **That diagnosis was correct**, and closing it is what this entry is about.

### 35 signals, 32 pins — the allocation genuinely fails

| group | pins | held down by |
|---|---:|---|
| safe-state control outputs | 5 | inherited, each with an external pull |
| user buttons | 6 | product lock |
| `TOUCH_INT_N` · `SX1262_DIO1` · `SD_CARD_DETECT_N` | 3 | FBV2-S1-003, D-108, **D-117** |
| `BQ25185_STAT1` · `BQ25185_STAT2` | 2 | **Ruling G** |
| `XGPIO0-9` | 10 | **D-082** |
| accessory control/status | 4 | D-089 / D-094 |
| `SX1262_RXEN` · `ACC_PWR_EN` | 2 | requirement / inherited |
| `RESERVED_SPARE` | 1 | **D-094** |
| front RGB | 3 | this brief |
| **total** | **35** | against **32** |

**Every escape route is closed.** There is **zero free native GPIO** — the ledger measures 33 of
33 assigned and GPIO35/36/37 are the octal PSRAM (B-10) — which also makes **the brief's own
WS2812 escape impossible**, because a smart LED needs RMT on a native pin and an expander cannot
produce it. `RESERVED_SPARE` is mandated by D-094. The ten XGPIO are locked by D-082, which
already surrendered the eleventh to pay for the fifth accessory-control pin. A dedicated I²C LED
driver would be a new part family, a new footprint and a new driver for one indicator.

### The answer is a third expander of the same part number

**`U23` = NXP `PCAL9535APW,118` at `0x22`** (D-165). It adds **no new MPN, no new footprint, no
new firmware driver and no new rail**, costs about $0.55 plus one 0603, and **retires B-37** by
leaving 12 spare I/O — the first slack this programme has ever had. Bus loading goes from five
devices to six: +6 pF maximum per line, ≈ 85 → 95 pF, rise time **158 → ~177 ns against the
300 ns fast-mode limit**.

**It carries the front RGB and the reserved spare, and nothing else** (D-166). That is how the
brief's rule *"preserve core/community/safety functionality before RGB when assigning pins"* is
satisfied **by construction**: delete `U23`, `D13` and `R124`–`R126` and the product loses its
status light and **not one other function**. Had the RGB kept `U2` P05–P07 and the charger
telemetry moved to the new part, declining it would have cost charge state and card detect —
exactly backwards. **Raised as O-6 for ratification.**

**It holds no interrupt source**, so it keeps the `FF` power-up mask and is never read while
servicing `WAKE_INT_N`. The third device costs **zero extra I²C traffic per event**.

### `RESERVED_SPARE` did not exist until now

D-094 has required a reserved expander resource since 2026-08-23 and **no sheet had implemented
it**. It exists now on `U23` P03 with `R130` 100 kΩ and `TP41`, which is where it belongs: a
reserve is worth more sitting beside twelve other free pins than alone on a full device.

`ACC_PWR_EN` is kept on `U3` P17 even though it drives only the DNP `U15`/`U16`, because
retiring it would leave two sheet-09 inputs undriven and sheet 09 is out of scope. **It is the
pin O-4 is expected to free.**

### The RGB is dark by construction, with no parts added to make it so

**`D13` = MEIHUA `MHPA3528RGBCT`, LCSC `C409779`** — confirmed live per D-096: in stock, 69 270
pieces. Common anode, PLCC-4 3.50 × 2.80 × 1.85 mm, 120°, water clear. **Pin 1 = anode,
2 = BLUE, 3 = GREEN, 4 = RED — not the `Device:LED_ARGB` order, which would have swapped red and
blue**, so a dedicated symbol and footprint were built from the manufacturer drawing.

The three resistors are **calculated separately and are deliberately unequal**, because the V_F
in the parts table is quoted at 20 mA and is useless at 1–2 mA; the numbers come off the Fig. 4
low-current curves:

| channel | R | V_F | nominal | corners |
|---|---|---:|---:|---|
| RED | **1 kΩ** | 1.75 V | **1.50 mA** | 1.18 – 1.70 mA |
| GREEN | **680 Ω** | 2.55 V | **1.03 mA** | 0.57 – 1.32 mA |
| BLUE | **390 Ω** | 2.60 V | **1.67 mA** | 0.86 – 2.17 mA |
| white | — | — | **4.20 mA** | 2.60 – 5.18 mA |

**Red gets the least current because it is the most efficient die** — 1070 mcd typ at 20 mA
against 500 for blue — giving roughly 80 / 87 / 42 mcd delivered.

**Default-off needs no external pull-ups.** Configuration 06h = `FF` at power-up makes the three
pins high-impedance inputs, so the cathode path is open and the only current is the **1 µA
leakage limit ≈ 0.05 mcd, invisible**; pull enable 46h = `00`, so the on-die 100 kΩ cannot light
it either; and Output port 02h = `FF`, so the pin **drives HIGH the instant it becomes an
output** — the anode potential — hence no glitch on the transition. **Three external pull-ups
would be three parts that do nothing** (D-169).

**ESD warning recorded in the symbol, the footprint and on the sheet: red is 2000 V HBM but
green and blue are only 150 V.**

**Front-facing is a requirement; the exact front position is deliberately NOT locked** — upper
bezel, lower bezel, beside the display or near the controls are all acceptable, it is **not** a
top-edge part, and it **must** sit behind a diffuser or light pipe with no protruding bare LED.
Placement and CAD own the final position.

### The PCAL9535A conversion is behavioural, and firmware must change

Verified against the primary source, **PCAL9535A Rev. 2, 23 January 2015**, retrieved and read
in this session. The pin-out is identical to the TCA9535 and no wire moved, but **the PCAL9535A
powers up with every interrupt masked, the exact opposite of the TCA9535 — unchanged firmware
sees no interrupts at all** (D-164). Two more contracts are now recorded: **write the Output
port register before the Configuration register**, or the five active-low resets and
`AMP_SD_MODE` glitch to their inactive state on the write that makes them outputs; and **`INT`
clears on a read of the input port register**, so firmware must read 00h/01h after the status
register or the line stays LOW and no further edge appears (D-171).

### Both charger status pins are landed, at 10 kΩ rather than Ruling G's 20 kΩ

SLUSF65A permits 1 kΩ–20 kΩ, so both are legal; 10 kΩ is a stiffer high against 1 µA of expander
leakage, reuses a value already dominant on the sheet, and its 0.33 mA flows only while the
charger is actually holding the pin LOW (D-170). **The decode is now recorded for firmware:**
STAT1 LOW = charging, STAT1 HIGH + STAT2 LOW = fault, both HIGH is **one** combined state
covering charge-complete, sleep and charge-disabled — which is why STAT1 alone was never enough.
**With no battery fitted STAT2 toggles forever**, so its interrupt mask bit stays SET by hardware
default and firmware polls it. That is precisely the capability the TCA9535 lacked, and it is
what makes D-061's family change load-bearing rather than cosmetic.

### The IR receiver reverts to AGC2 — O-5 closed

`U6` is **`TSOP38238`**, with **`TSOP38438` retained as a documented drop-in fallback** whose
symbol stays in the library (D-163). AGC2 is marked *Yes* for all six listed formats including
Sony, where AGC4 is marked **No**; the mechanism is the gap requirement — AGC2 needs > 5 × the
burst and takes 10–70 cycles per burst, AGC4 needs > 15 × and takes only 10–35, and SIRC breaks
the AGC4 limit. **The cost of the revert is the Fig. 15 high-modulation fluorescent suppression**
— a lighting-robustness margin, not a protocol. Every FBV2-S1-007 number survives untouched.

### Smaller findings

- **The switch MPN is real.** `PTS645SM43SMTR92LFS` appears as an orderable line: 1.6 N ± 0.3
  (~163 gf), 100 000 operations, 0.30 mm travel, SPST N.O. momentary, silver gull-wing SMD. The
  0.33 mA held current is **33× the datasheet's 10 µA minimum wetting current**, which had not
  previously been checked.
- **B-67 opened:** Littelfuse publishes **no bounce time** for the PTS645, so the schematic's
  earlier "≤ 5 ms" was not datasheet-backed. Use a 10–20 ms firmware window and measure.
- **Six root-sheet UUIDs were written with the prefix `fb080r00-`.** "r" is not a hex digit and
  KiCad silently reassigns invalid UUIDs on save, which would have destroyed pass traceability
  with no visible failure. Repaired.
- **Sheets 01 and 03 were touched only to publish nets the brief requires landing** — five and
  one local labels promoted to hierarchical, 28 and 5 lines of diff, no component, value,
  topology or DNP state changed (D-174). Without it, STAT1/STAT2 and card detect could not reach
  a PCAL input at all.
- **`MAX17048_ALRT_N` and `VBUS_PRESENT` remain test-point only.** D-089 had pencilled them onto
  `U2`; `TOUCH_INT_N` and `SD_CARD_DETECT_N` arrived later and outrank them. Twelve `U23` pins
  are free if that is ever revisited (D-166).
- **Noted, not actioned:** the project file still carries six stale ERC exclusion comments
  naming the retired `RGB_*_CTL` architecture and an unallocated `SD_CARD_DETECT`. They suppress
  nothing now; removing them strengthens ERC and is a separate hygiene task.

---

## 2026-08-23 — Infrared migrated (FBV2-S1-007)

**Overall 51% → 53%. No gate in the twelve-gate table passed**; the task gate **FBV2-S1-IR =
PASS**. Full analysis:
[`audits/2026-08-23-s1-ir-implementation.md`](audits/2026-08-23-s1-ir-implementation.md).

**ERC 45 → 45: zero added, zero removed.** Errors unchanged at 2, both inherited.
311 components, 0 duplicate references, 0 without a footprint, 0 `*_TBD` nets.

### The whole subsystem arrived DNP — for the fourth sheet running

`U6`, `D1`, `Q1`, `R21`, `R22`, `R23`, `R24` and `C11` all came from Beta-DM marked **`DNP`**.
Only `C12` was fitted — decoupling for a transmitter that was not there, exactly the pattern
found on sheet 06 with `C9`/`C10`. The brief opens with *"Full Beta v2 IR is a mandatory internal
feature"*, so **all eight are now fitted**.

**This is the fourth consecutive migrated sheet where an inherited `DNP` was load-bearing**
(sheet 09's `U16`/`R49`/`R50`/`U15`/`D2`/`D3`, sheet 06's `U5`/`J6`, now all of sheet 07). It is
no longer a coincidence: **a `DNP` on a Beta-DM sheet describes what was populated on that
reduced build, not what the architecture requires. Sheets 08 and 09 must be assumed to carry the
same trap.**

### The rating that binds is not the one that looks biggest

**`IFSM` = 1.5 A is a single-pulse surge for t ≤ 5 µs. It is not a remote-control rating.** The
figure that governs a 38 kHz burst train is **`IFM` = 200 mA**, specified at tp/T = 0.5 with
tp = 100 µs — a *longer* pulse at the same duty than a 38 kHz carrier produces, so the carrier
is less stressful than the specified condition, not more.

| candidate | % of `IFM` | avg LED power over an NEC frame | ΔTj | verdict |
|---|---|---|---|---|
| 100 mA | 50 % | 15 mW | 3.4 K | safe, leaves range on the table |
| **150 mA** | **75 %** | **25 mW** | **5.7 K** | **SELECTED** |
| 200 mA | 100 % | 35 mW | 8.1 K | **no tolerance margin left** |
| 300 mA | **150 %** | — | — | **REJECTED — out of spec** |

**Thermally none of these is difficult** — 25 mW against a 160 mW limit on a 230 K/W part. The
constraint is the repetitive rating, and it is hard. **Range is not the constraint either**: the
receiver datasheet quotes **45 m transmission distance using a TSAL6200 at only 50 mA**, and the
TSAL6100 at 150 mA is roughly 20× that intensity. Current buys off-axis margin, not headline
range.

### The supply preference is reversed — `+3V3`, not `SYS`

| | **`+3V3` (selected)** | `SYS` |
|---|---|---|
| resistor for 150 mA | **12 Ω** | 22 Ω |
| **peak across all tolerances** | **118–170 mA (1.44 : 1)** | **64–166 mA (2.6 : 1)** |
| as the battery drains | **nothing changes** | **IR range visibly shortens** |
| resistor dissipation | 0.27 W | 0.53 W |
| 38 kHz on the shared rail | ≈ 40 mV pk-pk | none |

**The noise objection that motivated `SYS` is real but bounded, and the one device that genuinely
cares is already behind 41 dB.** Everything else on `+3V3` lives with the audio amplifier's
**230 mA peaks** at 330 kHz, a 60 mA NFC field and ~100 mA of backlight boost. A 150 mA peak /
50 mA average IR load is the *smallest* pulsed load on the rail.

> **Scope, stated as fact and not as the reason:** `BQ25185_SYS` is a **sheet-01-local net**, so
> routing it to sheet 07 needs a sheet-01 edit this task is not authorised to make. **Had `SYS`
> won the analysis it would have been reported as blocked rather than quietly avoided.** It did
> not. The `ARCHITECTURE.md` source-select link is carried as **B-65**.

### `C12` was three times too small

Per carrier period the reservoir must supply `Q = I·D·(1−D)·T = 0.88 µC`, so ripple = 0.88 µC / C:

| `C` | ripple | % of rail |
|---|---|---|
| **4.7 µF (inherited)** | **218 mV** | 6.6 % |
| **22 µF (selected)** | **40 mV** | **1.2 %** |
| 47 µF | 19 mV | 0.6 % |

The package and voltage are specified deliberately — **1210 X7R 16 V** — because the requirement
is **≥ 15 µF *effective* at 3.3 V DC bias**, and a 6.3 V 0805 part would derate to roughly half
its marked value.

### The receiver's inherited filter turns out to be the load-bearing part of the sheet

`TSOP38238` → `TSOP38438` is a **pure MPN change** — same Minicast package, same pinning
1 = OUT / 2 = GND / 3 = VS, same footprint. `VS` 2.0–5.5 V, output **active low with an internal
30 kΩ pull-up**, so `OUT` drives GPIO44 directly and no external pull-up is needed.

`R21` 100 Ω + `C11` 4.7 µF match Vishay's application circuit exactly, and **Vishay prints the
topology but no values** — so ours had to be justified rather than inherited:

```
fc = 1 / (2 pi x 100 x 4.7u) = 339 Hz   ->   41 dB at 38 kHz
```

**Why that matters more than it looks:** datasheet **Fig. 7** shows the receiver's threshold
irradiance degrading from roughly **10 mV RMS of supply ripple *at the carrier frequency*** and
doubling by ≈ 50 mV — and our own transmitter runs at exactly that frequency. 40 mV pk-pk on the
rail becomes **≈ 0.1 mV RMS at `VS`, about 90× margin**. **This is what makes sharing `+3V3`
safe. Do not shrink `C11` for area without redoing this calculation.**

### Two inherited open items closed

**The AO3400A pinout is confirmed.** The AOS datasheet's SOT-23 top and bottom views show the
lone pin as **Drain** and the paired pins as **Gate** then **Source** — **1 = G, 2 = S, 3 = D**,
exactly what the symbol maps and the inherited wiring used.

**The `"Footprint BLOCKED: needs the official AOS recommended land pattern"` note asked for a
document that does not exist.** AOS publishes no land pattern in the AO3400A datasheet, so the
industry-standard IPC SOT-23 pattern applies and it becomes an ordinary FBV2-S2 item.

**Safe-OFF is proven, not assumed:** `R23` 100 kΩ with `IGSS` ≤ 100 nA holds the gate at
≤ **10 mV** against a **650 mV** minimum threshold — a 65× margin, so there is no IR emission at
boot, reset, GPIO high-impedance or a firmware crash.

### Protocol coverage — and a conflict inside the brief

`f0` = 38 kHz, 3 dB bandwidth `f0`/10 → 36.1–39.9 kHz. NEC / Samsung / Sharp / Mitsubishi sit at
full sensitivity; RC5/RC6 at 36 kHz and Sony at 40 kHz cost ~13–15 % of range, the ordinary
single-receiver compromise.

**But the brief §1 locks `TSOP38438` while §9 lists Sony/SIRC, and Vishay's suitable-data-format
table says those cannot both be true:** AGC4 is marked **"No" for Sony code** where the AGC2
`TSOP38238` is **"Yes"**. AGC4 is *"Preferred"* for NEC, RC5/RC6, Thomson RCA, Sharp and
Mitsubishi and adds **high-modulation fluorescent suppression (Fig. 15)** AGC2 lacks. Vishay's
framing: *"the higher the AGC, the better noise is suppressed, but the lower the code
compatibility."*

**The lock is a defensible trade, not an error.** Two things shrink it: **it is receive-only —
transmitting Sony/SIRC is completely unaffected**, and **reverting is a `lib_id` change** because
the `TSOP38238` symbol was deliberately retained in the project library. **Raised as O-5.**

### Power budget

150 mA nominal / 170 mA worst-case peak, 50 mA averaged over a burst, **≈ 17 mA averaged over a
whole NEC command**; receiver 0.35 mA continuous. **No new mutual-exclusion rule is proposed** —
MX-1 already covers concurrent high-power radio operation, and the brief says not to create rules
the power budget does not need.

### Nothing else was added

No second IR LED, no external IR accessory requirement, no multiple emitter angles, no extra
optical channels, no second receiver, no exotic carrier frequency, no dedicated LED-driver IC,
no RF-style test connectors, no analog optical detector, no new GPIO. `TP39` (LED current via the
drop across `R24`) and `TP40` (receiver output) added; `R123` DNP trim added with a hard 10 Ω
floor. **B-65 and B-66 opened.**

---

## 2026-08-23 — Audio migrated: microphone replaced, speaker locked (FBV2-S1-006)

**Overall 49% → 51%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-AUDIO = PASS**. Full analysis:
[`audits/2026-08-23-s1-audio-implementation.md`](audits/2026-08-23-s1-audio-implementation.md).

**ERC 45 → 45: zero added, zero removed.** Errors unchanged at 2, both inherited.
308 components, 0 duplicate references, 0 without a footprint, 0 `*_TBD` nets.

### The finding that was not on the brief

**`U5` (the MAX98357A) and `J6` (the speaker connector) arrived from Beta-DM marked `DNP`.**
Nobody wrote that down — it is in the inherited file. It means **the entire speaker output path
has never been populated on any AQROOT board**, while `C9` and `C10` *were* fitted, decoupling
an amplifier that was not there.

The brief says voice output remains required and Full Beta v2 is the feature-complete design,
so **both are now fitted**. Everything below — the power budget, the speaker choice, the EMI
provision — describes a path being built for the first time, and bring-up should read it that
way.

**This is the third load-bearing inherited `DNP` in two tasks** (`U16`, `R49`/`R50`, `U15`,
`D2`/`D3` on sheet 09 at FBV2-S1-005). **A `DNP` on a Beta-DM sheet is a statement about the
reduced build, not about the architecture.** Every migrated sheet has to re-decide it.

### The microphone is not a drop-in

| | ICS-43434 | **DMM-4026-B-I2S-R** |
|---|---|---|
| pads | **6** | **7** |
| body | 3.5 × 2.65 × 0.98 mm | **4.00 × 3.00 × 1.00 mm** |
| extra pin | — | **`CONFIG`** — no ICS equivalent |

**The pin count differs**, so both a new symbol and a new footprint were built from the PUI
drawing (Rev A, 5/26/2021). The brief's instruction not to reuse the ICS-43434 footprint was
right for a stronger reason than size.

Every pin re-derived from the data sheet: `LR`→GND selects the **left** slot; **`CONFIG`→GND
is mandatory** (*"Pull to ground. The state of this pin is used at power-up."*); `VDD`
1.62–3.63 V with `C8` 100 nF; and **`R120` 100 kΩ on `I2S_MIC_DIN` is a data-sheet
requirement** — *"The SD trace should have a 100 kΩ pull down resistor to discharge the line
during the time that all microphones on the bus have tri-stated their outputs."* With one
microphone the line still tri-states for the entire unused half of every frame, and the
inherited sheet had no pull-down at all.

**No 1.8 V rail is needed, and that was the single largest risk in the substitution.** The part
is *rated* 1.8 V and PUI's catalogue line reads *"MICROPHONE -26DB 1.8VDC"* — a 1.8 V-only
microphone would have forced a regulator the brief forbids. The data sheet gives an operating
range of **1.5–3.6 V** (pin table 1.62–3.63 V), so `+3V3` and the existing decoupling are the
whole supply design. 820–1000 µA normal, **5 µA sleep**, 20 ms startup, −26 dBFS, 64 dB(A).

### The brief's suggested sample rate cannot be run on the wire

**The microphone's normal-mode input clock is 2.048–4.096 MHz**, and below 320 kHz it sleeps.

| frame | BCLK | verdict |
|---|---|---|
| 16 kHz × 32 | 0.512 MHz | **outside normal mode** |
| 16 kHz × 64 | 1.024 MHz | **outside normal mode** |
| 32 kHz × 64 | 2.048 MHz | exactly on the limit |
| **48 kHz × 64** | **3.072 MHz** | **the data sheet typical, and the MAX98357A's own test condition** |

The amplifier independently restricts LRCLK to 8/16/32/44.1/48/88.2/96 kHz, and 48 kHz is on
that list. **The bus runs at 3.072 MHz and firmware decimates to 16 kHz.** 16 kHz is still the
right *application* rate — it is not a legal *wire* rate for this part. On the bench this would
have looked like *"the microphone sometimes returns silence"*, which is what sleep mode looks
like.

**Everything else about the I²S architecture is valid unchanged**: `BCLK` and `LRCLK` shared,
`MIC_DIN` and `SPK_DOUT` separate, one ESP32-S3 controller in master full duplex. **No pin, net
or GPIO change**, so the GPIO ledger is untouched.

### A gain strap that was mismatched to the rail

Gain is referenced to a 2.1 dBV full-scale DAC output, so `output (dBV) = input (dBFS) + 2.1 +
gain`:

| `GAIN_SLOT` | gain | 0 dBFS asks for | 3.3 V rail gives | result |
|---|---|---|---|---|
| **GND (inherited)** | **12 dB** | **5.07 Vrms** | 2.33 Vrms | **clips above −6.8 dBFS** |
| **VDD (selected)** | **6 dB** | **2.54 Vrms** | 2.33 Vrms | **0 dBFS ≈ the rail** |

At 12 dB the **top 6.8 dB of the digital range was unusable** — clipped by the supply, not the
amplifier. At 6 dB the whole range is usable and the noise floor is lower. **Maximum acoustic
output is identical either way: it is rail-limited, not gain-limited.** One net, no BOM impact.

`SD_MODE` needs **no series resistor** — the data sheet requires ~2 kΩ only when
`VDD < VDDIO`, and here both are the same `+3V3` net. Recorded because it is exactly the part
that gets added "just in case". `R15` 100 kΩ to GND holds shutdown through reset and boot.

**Firmware safety rule, verbatim:** *"Do not remove LRCLK while BCLK is present … can cause
unexpected output behavior, including a large DC output voltage."* Into an 8 Ω voice coil that
is a burnt speaker.

### Speaker — PUI `AS02008MR-LW152-R`

Ø20 ± 0.2 mm × **3 ± 0.2 mm**, **8 Ω ± 15 %**, **0.5 W rated / 0.8 W max**, 86 ± 3 dBA at
0.1 W / 0.1 m, 5 % max distortion, resonance 500 Hz, **response 500–4000 Hz**, metal housing,
Mylar cone, Nd-Fe-B magnet, 2.4 g, **152 mm UL1571 AWG #32 leads, RED (+) / BLACK (−)**.

**The 500–4000 Hz response is the reason to choose it, not a limitation to apologise for.** The
brief asked for intelligible speech and explicitly not music; a driver that puts all of its
0.5 W into the speech band is louder where it matters than a wider-range driver the same size.
It also fits the existing `SPEAKER_ENVELOPE` with 1 mm of depth to spare.

**`J6` is retained** — JST `B2B-PH-K-S` was already the right connector. Mating side
**`PHR-2` + `SPH-002T-P0.5S`**, and JST's applicable wire range is **AWG #32 to #24**, so the
speaker's leads crimp straight in: **no soldering to fit it, no soldering to replace it** — the
same serviceability principle as the NFC antenna (D-128). AWG #32 is the small end of that
range, carried as **B-62** for a first-article pull test rather than asserted.

### Power and the volume ceiling

```
rail limit     3.3 / sqrt(2) = 2.33 Vrms  ->  2.33^2 / 8 = 0.68 W peak
cross-check    data sheet 0.93 W at 3.7 V x (3.3/3.7)^2  = 0.74 W     consistent
current        0.68 W / 0.90 / 3.3 V                      = 230 mA
```

| level | output | +3V3 | vs the 0.5 W rating |
|---|---|---|---|
| 0 dBFS | 0.68 W | 230 mA | above rated, under the 0.8 W max — short alerts only |
| **−6 dBFS (default)** | **0.17 W** | **57 mA** | comfortably inside, ≈ 89 dB SPL at 0.1 m |
| shutdown | — | **0.6 µA** | — |

**No new mutual-exclusion rule is proposed**: MX-1 already covers concurrent high-power
operations, and voice does not need maximum output during radio TX. Thermally irrelevant —
~75 mW in a 1666 mW package.

### EMI — nothing fitted, everything recoverable

The decisive evidence is the data sheet's own **Figure 14, "EMI with 12 in of Speaker Cable and
No Output Filtering"**. AQROOT's lead is 152 mm, **half** that, and the part already uses
edge-rate control plus spread-spectrum modulation around 330 kHz.

**First build: `R121`/`R122` fitted as 0 Ω — the speaker path is a plain wire — with
`C81`/`C82` 1 nF DNP.** If emissions ever need taming, swap the 0 Ω for a ferrite bead and
populate the shunts: four 0603 positions, no respin. A 0603 0 Ω adds ~50 mΩ, i.e. 15 mV at
300 mA against 8 Ω.

**PCB requirement: `SPK_P`/`SPK_N` as a tight, equal-length differential pair from `U5` to
`J6`** whatever is fitted — the most effective EMI control on a filterless Class D output, and
free.

### Acoustics, measured from the drawing

§8.3 is a raster drawing; it was rendered and the pads measured programmatically, and the
geometry closes against the printed dimensions to **0.01 mm**. Pads 0.60 × 0.40 mm, columns
±1.075 mm, rows 0.65 mm, **pad 4 is a GND ring ID 1.05 / OD 1.65 mm**, port on the width
centreline 1.28 mm from the nearest row and 1.00 mm from the short edge, port in the can
Ø0.25 mm.

**It is a bottom-port part: sound enters through a hole in the PCB, so the microphone sits on
the face OPPOSITE the shell aperture.** PCB hole **Ø1.05 mm NPTH** concentric with pad 4 (the
spec previously said Ø0.8–1.0 mm — this is now the manufacturer's number), Ø1.65 mm mask and
copper keepout, Ø2.5 mm component keepout, gasket ID ≥ 1.5 mm, tunnel ≤ 2.5 mm, ≥ 60 mm from
the speaker on opposite faces. **The Nd-Fe-B speaker magnet must also stay clear of the NFC
zone.**

### Echo — no hardware, one free lever

`SD_MODE` is a **hardware mute**: shutdown puts the outputs high-Z at 0.6 µA and removes the
amplifier's own noise floor from the microphone's environment, which a digital mute cannot do.
**First firmware should be half-duplex**, muting via `SD_MODE` while listening; ramp the
digital data down first, because there is no volume ramp-down on entering shutdown. Software
AEC later if barge-in is wanted.

### Nothing added, and no new CTO decision

No codec, no DAC, no analog microphone amplifier, no 1.8 V rail, no acoustic wake detector, no
buzzer, no headphone jack, no second speaker, no hardware AEC, no alternate footprint, no new
GPIO. **BOM consolidation, free: the microphone and the speaker are now both PUI Audio.**

**B-61–B-64 opened.** The microphone is confirmed in live distributor stock (DigiKey 2 807,
Arrow 10 000). **The speaker is not** — PUI's product page would not render here after three
attempts and Digi-Key search is bot-protected. Its datasheet is served live from PUI's API
today, but D-096 asks for a live listing and that is not one, so it is carried as **B-61**.

**One probe was extended rather than silenced.** `fork_equivalence.py` asserted the `.pretty`
directory was bit-identical to Beta-DM's, which stopped being true the moment a migrated sheet
locked a new part. It now asserts every **inherited** footprint is still bit-identical and none
was deleted, and that every **addition is declared** in an `ADDED_FOOTPRINTS` table naming the
task that added it. An undeclared footprint is still a failure.

---

## 2026-08-23 — I²C devices and IMU migrated (FBV2-S1-005)

**Overall 47% → 49%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-I2C-IMU = PASS**. Full analysis:
[`audits/2026-08-23-s1-i2c-imu-implementation.md`](audits/2026-08-23-s1-i2c-imu-implementation.md).
New registry:
[`architecture/I2C_ADDRESS_REGISTRY.md`](architecture/I2C_ADDRESS_REGISTRY.md).

**ERC 46 → 45: zero added, one removed.** Errors unchanged at 2, both inherited.

### First: a number this programme has been repeating is wrong

FBV2-S1-004, 004B and 004C all quote **"ERC 68"**. The stored reports say **46**.

| report | messages | errors | warnings |
|---|---|---|---|
| `FBV2-S1-004-erc.rpt` | 46 | 2 | 44 |
| `FBV2-S1-004B-erc.rpt` | 46 | 2 | 44 |
| `FBV2-S1-004C-erc.rpt` | 46 | 2 | 44 |
| **`FBV2-S1-005-erc.rpt`** | **45** | **2** | **43** |

The **deltas** those tasks reported — "zero added, zero removed" — are correct and
reproducible from the stored files. Only the absolute figure was wrong, and it was carried
for three tasks. Sheet `04`'s migration genuinely took the count **64 → 46**.

A second trap, worth writing down because it will catch someone again:
`kicad-cli sch erc --severity-all` also counts **Exclusions** and reports **104** on the same
unmodified design. Every number in this programme is `--severity-error --severity-warning`,
matching the stored reports' own `Report includes: Errors, Warnings` header.
**Compare like with like or the gate is meaningless.**

### The BMI270 was re-derived, and it was already right

The brief said not to copy Beta-DM's straps blindly. Every one was checked against
**`BST-BMI270-DS000-08` Rev 1.6** (150 pages, fetched and extracted in full):

| pin | as drawn | Bosch |
|---|---|---|
| 1 `SDO` → GND | 0x68 | *"the default I²C address … 0b1101000 (0x68) … if the SDO pin is pulled to GND"* |
| 12 `CSB` → VDDIO | I²C mode | *"it is recommended to hard-wire the CSB line to VDDIO"* |
| 2 `ASDx` / 3 `ASCx` → VDDIO | secondary I/F unused | *"can be connected to VDDIO or left unconnected. **Do not connect to GND.**"* |
| 9 `INT2`, 10 `OCSB`, 11 `OSDO` → DNC | unused | *"If INT1 and/or INT2 are not used, please do not connect them (DNC)."* |
| `C6` / `C7` 100 nF at pins 5 and 8 | decoupling | *"recommended to use 100nF decoupling capacitors at pin 5 (VDDIO) and pin 8 (VDD)"* |

**Nothing was wrong.** That is the honest outcome and it is worth stating rather than dressing
up as a discovery (D-136). `VDD` 1.71–3.6 V, `VDDIO` 1.2–3.6 V, **no sequencing or slew-rate
constraint**, `tPO` 2 ms, FIFO 2048 B, 8 kB config upload after every POR. **`B-44` CLOSED**:
pad drive `IOH`/`IOL` ≤ 2 mA against a 323 µA load.

**One capability the brief asked about does not exist: the BMI270 has NO tap or double-tap
feature**, in any configuration. Its feature set is significant motion / any motion / motion
detect / no motion / stationary detect / wrist wear wakeup / wrist-worn step counter and
detector / activity change / push arm down / pivot up / wrist jiggle / flick in-out. So
wake-on-motion, significant motion, orientation, raise-to-wake (*"wrist wear wakeup"*) and the
FIFO are all supported; **tap is not**, and no hardware is proposed to compensate.

### The real defect was on the bus

Measured from the netlist rather than assumed — two expanders, the IMU, the fuel gauge, the
TCA9517A A-side, the touch controller through the 50-pin display flex, two test points, ~120 mm
of trace — the internal bus carries **≈ 85 pF worst case**.

| `R` | `t_r` = 0.8473·R·C at 85 pF | 100 kHz (1000 ns) | 400 kHz (300 ns) |
|---|---|---|---|
| **4.7 kΩ inherited** | **338 ns** | pass | **FAIL** |
| **2.2 kΩ selected** | **158 ns** | pass | **pass, 47 % margin** |

At a *typical* 60 pF, 4.7 kΩ gives 239 ns and passes. **That is the worst kind of defect — it
works on the bench and fails on the unit with the longest flex and the widest tolerances**, and
the programme's own 100 kHz-then-400 kHz bring-up rule would have found it late, on hardware,
as an intermittent. Sink current was checked before the change, as the brief required:
**1.32 mA at `VOL` 0.4 V**, against BMI270 2 mA, expander SDA 6 mA, the I²C-specification
minimum of 3 mA and an absolute floor of 967 Ω (D-139).

**There is exactly one pull-up pair on the internal net.** `R49`/`R50` are DNP and sit on the
switched accessory segment, on the far side of `U16`. The sheet note now says so, so nobody
adds a second pair helpfully.

### `0x68` becomes a rework instead of a respin

`SDO` was **hard-wired to GND**. Under D-049 that made an address collision a trace cut at a
0.25 mm pad. It is now `R118` 0 Ω **FIT** to GND (0x68) and `R119` 0 Ω **DNP** to `+3V3`
(0x69) — **fit one only; fitting both shorts `+3V3` to GND**.

**`0x68` is the single most collision-prone address on a community I²C bus.** MPU6050,
MPU9250, ICM-20948 and the DS3231/DS1307 RTC families all default to it, and those are exactly
the parts a hobbyist accessory is built from. **Reserving an address in a document does not stop
a $2 module from arriving at it.** Two 0603 pads, one populated (D-140).

### GPIO3: a timing proof, and a firmware constraint that falls out of it

1. `INT1_IO_CTRL` **resets to `0x00`** — the output driver is **disabled** at POR.
2. Firmware cannot enable it before the 8 kB config upload.
3. ESP32-S3 strap hold time **`tH` = 3 ms min**, and **GPIO3 defaults to "Floating"** with no
   internal pull, so `R110` alone defines the strap.

**The IMU physically cannot reach the strapping window.** And because `R110` is a pull-**down**:
**`INT1_IO_CTRL.od` = 0 (push-pull) and `.lvl` = 1 (active high) are MANDATORY; open-drain is
FORBIDDEN** — an open-drain output into a pull-down never produces an edge, and the interrupt
would be silently dead in a way that looks like a firmware bug for a week. GPIO3 = `RTC_GPIO3`,
so **EXT0/EXT1 deep-sleep wake works**, and active-high into a pull-down is exactly the polarity
it wants (D-137).

**Moving the interrupt behind a PCAL9535A is rejected** — it would put motion wake behind an
I²C transaction that cannot wake the SoC from deep sleep, `U2` is 16/16, and the boot-safety
reason that might have justified it does not exist.

### `INT2` stays DNC (D-138)

Bosch instructs DNC for unused interrupt pins; one pin is sufficient because *"if just one
interrupt pin is used all interrupts may be mapped to this interrupt pin"*, with the source read
from `INT_STATUS_0`/`INT_STATUS_1`; and two pins in latched mode would import a mapping
partition the design does not otherwise have. **`RESERVED_SPARE` is not consumed.** Pad 9 exists
on the land pattern, so a future second interrupt is a wire — which is what D-049 asks for.

### The IMU stays powered (D-141)

Accel-only low power is **down to 4 µA** plus **≈ 3 µA** of advanced features (10 µA spec'd at
25 Hz). A load switch would save **≈ 9 µA** while destroying wake-on-motion, forcing an 8 kB
config upload on every resume, and consuming one of the design's last expander pins. Nine
microamps is below the SoC's own deep-sleep floor.

### Land pattern verified — the "DO NOT ROUTE" note is discharged (D-143)

§8.3 is a **raster drawing**: no vector geometry, and nothing in the text layer but
*"Pad tolerance: ±50 µm"*. It was rendered at 12× and the pads measured programmatically,
calibrated on the printed 0.5 mm pitch. **Every printed dimension reproduces** — 0.5, 0.25,
0.475, 0.675, 0.925, 3.0, 2.5 — as do the pad sizes, the ±1.1625 columns, the ±0.9125 rows
and, critically, **the peripheral pin order 1–4 left / 5–7 bottom / 8–11 right / 12–14 top**.
That last one is the error that would have been fatal and silent.

### P-18 — characterised, not decided, and the characterisation moves the problem

**`U16` TCA9517A, `R49`/`R50`, `U15` and `D2`/`D3` are ALL DNP.** There is no fitted external
I²C path today, so whatever is chosen at Sheet 09 migration costs **no rework**.

TI settles the powered-off case: *"**VCCA is only used to provide the 0.3 × VCCA reference** …
**The TCA9517A logic and all I/Os are powered by the VCCB pin.**"* `VCCB` = `ACC_3V3_SW`, so a
de-asserted accessory rail leaves the buffer **completely unpowered and high-Z on both sides** —
a **harder** disconnect than an I²C mux, which stays powered.

**The weakness is not the buffer. It is the location of its disable control.** `ACC_PWR_EN` is
`U3` P17 — an expander output sitting behind the very bus a broken accessory would hold low. A
9-clock recovery pulse train frees the common case for nothing; a hard short escapes only via a
`+3V3` power cycle, because an MCU reset does not reset the expanders.

> **O-4 — NEW, REQUIRES A CTO DECISION.** Evaluate replacing `U16` with a **TCA4307-class
> hot-swap I²C buffer with stuck-bus recovery**, at Sheet 09 migration. The community header is
> a **hot-plug connector by definition**, and this is the only option that both **pre-charges on
> insertion** and **recovers a stuck bus without the host**. No rework cost, no net BOM, and the
> TCA9517A's one unique capability — level translation — is unused, because sheet `09` already
> declares *"COMMUNITY HEADER LOGIC = 3.3 V ONLY"* and `VCCB` is 3.3 V. Against: **not
> pin-compatible**, so the `U16` area must be re-routed, and the MPN must come from a **live
> listing** before any lock (D-096). **Nothing is implemented; `U16` remains TCA9517A.**

**No buffer of any kind solves address collision.** A repeater, a hot-swap buffer and a mux all
pass addresses through unchanged. That is a protocol problem, closed by the new registry (D-142)
and the `0x50` ID EEPROM — not by silicon.

### Blockers

**B-44 CLOSED.** **B-59 opened** — `ER-TPC035-6` touch-flex pull-ups unknown; direction is safe,
first-article measurement. **B-60 opened** — `0x36` and `0x38` are carried, not datasheet-cited;
every Analog Devices and FocalTech fetch failed here, and **a first-article bus scan closes it in
ten seconds**, which is more honest than editing a document.

### One inherited discrepancy, recorded and left alone

`U2`/`U3` still carry the schematic value **`TCA9535PWR`** while **D-061 locked NXP
`PCAL9535APW,118`**. The address base is identical (`0100 A2A1A0`), so nothing here depends on
it — and both parts live on **sheet 08**, which is not authorised in this task. Flagged now so
it is not discovered at BOM time.

---

## 2026-08-23 — NFC ferrite orientation corrected and first-build matching closed (FBV2-S1-004C)

**Overall 45% → 47%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-NFC-MATCHING = PASS**. Full analysis:
[`audits/2026-08-23-s1-nfc-matching-closeout.md`](audits/2026-08-23-s1-nfc-matching-closeout.md).

**ERC 68 → 68: zero added, zero removed.** *(the 68 is a transcription error corrected in FBV2-S1-005 — the stored reports say 46 → 46. The delta was right.)*

### Two defects found that were not on the brief

**1. The RX divider would have over-driven the receiver.** At full field the first-build
network puts **49.5 V pk-pk differential** across the coil — **24.8 V pk-pk per side**. The
placeholder 47 pF / 220 pF divider has a ratio of 0.176 and would therefore have placed
**≈ 4.4 V pk-pk on `RFI1`/`RFI2`, against a 3.0 V regulated analog rail**. That is a
part-stress condition, not a tuning imperfection, and it had been carried since the topology
was first drawn without ever being checked against a real antenna voltage.

**2. The E24 grid is brutally steep at the series matching capacitor.** `C_s` sits close to
series resonance where `dZ/dC` is enormous, and the two E24 neighbours of the ideal 284 pF
are not close in effect at all:

| `C_s` per leg | Z differential | RF power | driver current |
|---|---|---|---|
| 270 pF | ≈ 16 Ω | 0.55 W | **≈ 257 mA — over budget** |
| *284 pF (ideal)* | *36 Ω* | *0.247 W* | *≈ 115 mA* |
| **300 pF (selected)** | **≈ 68 Ω** | **0.13 W** | **≈ 60 mA** |

### Antenna variant corrected — A → B (D-131)

**`FXC.46.52.0075X.A.dg` is superseded. `FXC.46.52.0075X.B.dg` is locked.** Verified verbatim
from Taoglas `SPE-24-8-104-B`: *"NFC Flex Antenna (46*0.3mm) with a **Reverse Ferrite Layer**
and adhesive backing"*, *"13.56 MHz Antenna"*, *"Diameter: 46mm"*,
*"FXC.46.52.0075X.B.dg - NFC with ferrite and 75mm Twisted Pair 28AWG cable with ACH(F)
connector"*, *"Peel and stick 3M adhesive"*.

Per APN-24-8-001 the variants differ **only in stack order**:

| variant | stack, outside → inside | intended mounting |
|---|---|---|
| A | flex antenna / ferrite / **adhesive** | onto a **PCB or component surface** |
| **B** | **adhesive** / flex antenna / ferrite | to the **INSIDE of the enclosure**, reading through it |

**AQROOT bonds to the inner rear shell and reads outward — the B case exactly.** With the A
version the ferrite would sit **between the coil and the tag**, which is the one place a flux
director must never be.

**Connector, cable, diameter, adhesive and interface are unchanged, so `J7` and the board
are unaffected.** This is a purchasing-line change caught **before antennas were ordered** —
which is exactly why FBV2-S1-004B surfaced it. **No `…A.dg` reference remains anywhere in
`hardware/beta-v2/`.**

### B-version parameters (D-132)

`La` **1.10 µH**, `Rs` **1.50 Ω**, `Q` **60.37**, `SRF` **395 MHz**; `ωL` = **93.72 Ω**.

The published triple is coherent to **~3 %** — `Q` 60.37 with 1.10 µH implies `Rs` 1.55 Ω
rather than 1.50 Ω, ordinary rounding between separately-published figures. Recorded rather
than smoothed over. `Rs` = 1.50 Ω is used for damping because that is the resistance which
physically adds to `R_q`. **The 395 MHz SRF is a large improvement on the A version's
148 MHz**, so the coil behaves as a clean inductor across the band.

### Target impedance derived, not borrowed (D-133)

**The previous 20 Ω/side figure is discarded — it was an assumption with nothing behind it.**

AN5276 offers two design intents: maximum power transfer, or *"a certain current
consumption"*. AQROOT has a locked budget (D-130: ≤ 150 mA from `+3V3` with the field on,
~20–30 mA of it reader overhead), so the second intent **determines** the target:

```
driver budget        115 mA x 3.3 V              = 0.380 W in
at ~65 % efficiency                              = 0.247 W RF
differential square wave at VDD_TX = 3.3 V:
  fundamental RMS = (4/pi) * 3.3 / sqrt(2)       = 2.971 V
  Z = 8.827 / 0.247                              = 35.7 ohm differential
```

> **First-build target: Z ≈ 36 Ω differential (18 Ω per side), Q ≈ 25.**

No EMVCo constraint applies, so Q is set purely by ISO/IEC 14443 bandwidth at 106 kbit/s.

### First-build matching set — and one deliberate bias (D-134)

| ref | was | **now** | basis |
|---|---|---|---|
| `R114`, `R115` | 1R0 | **1R1 1 %** | `Q` 62.5 → **25.3**; depends on the antenna alone |
| `C71`, `C72` | 300 pF | **300 pF** | ideal 284 pF; E24 chosen on the **safe, low-current** side |
| `C73`, `C74` | 1.8 nF | **1.5 nF** | re-solved for the resulting match |
| `L5`, `L6` | 220 nH | **39 nH** | EMC cut-off |
| `C69`, `C70` | 220 pF | **100 pF** | EMC cut-off |
| `C75`, `C77` | 47 pF | **27 pF** | RFI divider — safety fix |
| `C76`, `C78` | 220 pF | **620 pF** | RFI divider — safety fix |

**300 pF is chosen on purpose.** On a first board an *under*-driven antenna is a
one-component swap, while an *over*-driven one risks the driver and the `+3V3` budget on
first power-up. 187 mA of coil current in a 46 mm loop is still a serviceable field —
roughly 72 % of what the 36 Ω design would produce.

**B-56 is CLOSED.** With the 1.6 nF total shunt, 39 nH puts the EMC cut-off at
**20.1 MHz** — outside AN5276's forbidden 13–14 MHz band. **The previous 220 nH pair sat at
7.6 MHz, below the carrier**, and also presented 18.7 Ω of series reactance that was badly
perturbing the match.

**Every value is still marked `TUNE`, but `TUNE` now means "expected to move at first
article", not "unknown".** Each is a **CALCULATED FIRST-BUILD VALUE** with its arithmetic
recorded — a different thing from the placeholders it replaced.
**CALCULATED FIRST-BUILD VALUE is not FINAL TUNED VALUE.**

### RFI input safety (D-135)

```
old:  ratio 47 / 267  = 0.176   ->  24.8 V pp * 0.176   = 4.4 V pp   vs a 3.0 V rail
new:  ratio 27 / 647  = 0.0417  ->  24.8 V pp * 0.0417  = 1.03 V pp  -> > 3x headroom
```

Purely capacitive, no DC path; it adds ≈ 26 pF of shunt at the antenna node, small against
`C_p` = 1.5 nF. **No 5 V reference divider was reused blindly** — the ratio comes from this
design's own antenna voltage at 3.3 V. The receiver's exact linear range could not be
extracted from DS12484 (**B-58**), so the first-article `RFI` measurement is a **pass/fail
gate**, not an optimisation.

### AN5276 — closed on substance, not on process

ST's governing rules were obtained and applied: a one-stage EMC filter of series inductor
plus parallel capacitor; *"the EMC cutoff frequency must not be comprised between 13 and
14 MHz"*; an L-topology match of one series and two parallel capacitors in differential
topology; and a capacitive divider back into `RFI`. **The captured topology already matched
that description — only the values changed.**

**The Rev 6 PDF still would not load in this environment** — st.com and the Mouser mirrors
timed out, and a direct download returned bot-protection HTML. **B-48 is closed on
substance; the `STSW-ST25R004` run against a measured antenna impedance is carried as
B-57** and is required before fabrication.

### The 5 V fallback is preserved and was NOT tuned for

The first-build network is a 3.3 V design. Moving to ~5 V later needs a firmware supply
change (clear `sup3V`), **revalidation of matching, damping and the RFI divider** — the
driver amplitude rises ~1.5×, so `RFI` would sit near 1.5 V pk-pk, still inside the rail but
it must be re-checked rather than assumed — and possibly a passive retune. **It needs no PCB
respin, no antenna replacement and no ST25R3916 replacement.**

### First-article tuning is required before anything is called final

And it must be done with the **rear shell fitted, the antenna adhered in its final position,
the PCB installed, the battery installed and the ferrite in its final orientation**. Every
conductor and dielectric within a few centimetres is part of an inductive near-field antenna,
so bench tuning on a bare board proves nothing about the product. The ten-step procedure —
measure installed impedance, run the tool, verify resonance, Q, differential match, `RFI`
voltage and driver current, then NFC-A/B/F/V tags and read/write distance through the shell —
is in the audit.

### Mechanical

Antenna **`FXC.46.52.0075X.B.dg`**; **adhesive side directly against the inner rear
surface**; field **outward through the rear plastic shell**; **ferrite faces inward** toward
the PCB and battery. **≥ 48 × 48 mm** clear zone, no battery or speaker-magnet overlap, no
screws or bosses through the active zone, no 433 MHz flex crossing it. No enclosure
external-size change.

### Nothing new added, and no new CTO decision requested

No AAT varactors, no extra RF switch, no extra external 433 connector, no custom NFC PCB
antenna, no RF TVS. The one candidate considered — an **E48 280 pF `C_s`** to land exactly on
36 Ω instead of 68 Ω — was rejected for the first build because it commits to a target
impedance nobody has measured yet. **It is a first-article component choice.**

---

## 2026-08-23 — NFC IC and antenna FINAL LOCK (FBV2-S1-004B)

**Overall 43% → 45%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-NFC-ANTENNA-LOCK = PASS**. Full analysis:
[`audits/2026-08-23-s1-nfc-antenna-closeout.md`](audits/2026-08-23-s1-nfc-antenna-closeout.md).

**ERC 68 → 68: zero added, zero removed — the violation lists are identical.** *(the 68 is a transcription error corrected in FBV2-S1-005 — the stored reports say 46 → 46.)*
301 components, 0 duplicate references, 0 without a footprint.

### B-06 is closed

*"NFC is undesigned, not merely unrouted"* has been on the blocker list since the
pre-design audit. It is not true any more. **Crystal, matching topology, antenna,
connector and supply all exist.** What remains is *tuning*, which is a bench activity,
not a design gap.

### NFC IC locked — P-17 CLOSED (D-126)

**`ST25R3916-AQET`. The B variant is not adopted.** CTO reasons as given: non-B is active
production; it **preserves capacitive low-power sensing**; AQROOT is not an EMVCo payment
terminal; AWS is not worth trading sourcing simplicity and feature breadth for; and the
first build already has 3.3 V operation plus a no-respin 5 V fallback. This agrees with
FBV2-S1-004's recommendation on independent grounds — the non-B is the **only one of the
two with an LCSC part number (`C5267441`)**, and therefore the only one with a JLCPCB
assembly path, at roughly half the unit cost.

**MPN metadata verified present in the schematic, not merely in prose:** `Value`, `MPN`,
`Manufacturer` and `LCSC` all carry it.

`U9`'s `Package` description was **rewritten**. It still named `NFC_5V_PA_PENDING` as the
supply and told the reader the RF and oscillator pins were *"on explicit named TBD nets —
DO NOT ROUTE"*. Both statements stopped being true in FBV2-S1-004.

### NFC antenna locked — B-53 CLOSED (D-127)

**Taoglas `FXC.46.52.0075X.A.dg`, off-board.** Verified verbatim from `SPE-22-8-131-C`:

| | |
|---|---|
| Description | *"Circular Form Factor Flexible Near Field Communications Antenna"* |
| Frequency | **13.56 MHz** |
| Diameter | **46 mm** |
| Ordering line | *"Thickness: 0.27 mm - FXC.46.52.0075X.A.dg - NFC with ferrite and 75mm Twisted Pair 28AWG cable with ACH(F) connector"* |
| Adhesive | *"Peel and stick 3M adhesive"* |
| Typical interrogation distance | **40 mm** |

**This replaces the abstract 45 × 45 mm custom-antenna assumption.** It keeps the antenna
**off the main PCB**, which is what avoids putting a 45 × 45 mm keepout through the ground
plane of a board that already carries three radios.

**The electrical triple — `L` = 1.09 µH, `Rs` = 1.6 Ω, `Q` ≈ 58 — is used as supplied, and
it checks out internally:** `ωL/Rs` = 92.87 / 1.6 = **58.0 exactly**. It could **not** be
re-extracted from the datasheet, whose electrical table is an image, so it is recorded for
first-article confirmation (**B-55**) — which costs nothing, because the match has to be
re-derived from measurement regardless.

### Board-side connector — mating proven (D-128)

**`J7` = JST `BM02B-ACHSS-GAN-ETF`.** ACH series, 2 circuits, 1.20 mm pitch, SMT, gold,
**2.0 A / 50 V**, −25…+85 °C, 1.4 mm high × 4.3 mm wide; **Active, 30,004 in stock,
$0.52 @ 1, MOQ 1**.

**Mating is proven, not assumed:** the header's mating housing is **`ACHR-02V-S`** — an ACH
receptacle, which is exactly the *"ACH(F) connector"* Taoglas fits to the `FXC.46` cable —
and the antenna's 28 AWG wire is the gauge JST rates the series at. **The antenna is
replaceable without soldering.** KiCad's footprint is named for this exact MPN.

**Correction to the brief: JST classes ACH as a TOP-ENTRY header, not right-angle.** JST's
own words: *"the socket half is mated with the header from the vertical direction, while
the wires come out from the horizontal direction of the socket connector."* Digi-Key's
parametric says "Right Angle", which most likely describes the cable exit; Newark, JST and
KiCad's own footprint name all say top entry / vertical. **The part is right and
unchanged** — the consequence is that **`J7` needs mating clearance above it** while the
cable leaves horizontally. FBV2-P1 placement note.

### Matching network — one number that can be trusted, and one that must not be built (D-129)

**`R114`/`R115` (`R_q`): 0 Ω → `1R0 TUNE`. This is the solid value**, because it depends on
the antenna alone:

```
Q0       = wL / Rs = 92.87 / 1.6      = 58.0     (far too high for ISO14443 bandwidth)
R_total  = wL / 26                    = 3.57 ohm
2 * R_q  = 3.57 - 1.6                 = 1.97 ohm  ->  R_q = 1R0 per leg,  Q = 25.8
```

**`C71`/`C72` (`C_s`): 100 pF → 300 pF. `C73`/`C74` (`C_p`): 100 pF → 1.8 nF.** Both follow
from an L-match lifting the damped 1.8 Ω per side to an **assumed 20 Ω per side** driver
target — the right shape and the right order of magnitude, **not a validated match**,
because AN5276 still would not load.

> **`L5`/`L6` and `C69`/`C70` were deliberately NOT re-derived, and are now inconsistent
> with the network around them.** With `C_p` at 1.8 nF the shunt on that node rose by an
> order of magnitude, and 220 nH against ~2 nF resonates near **7.6 MHz — below the
> 13.56 MHz carrier**, which would attenuate the carrier rather than the harmonics.
> **NOBODY MAY BUILD TO THE CURRENT EMC VALUES.** The on-sheet note says so in those words.
> **B-56.**

Everything stays `TUNE`, everything is 0603 and hand-reworkable, and **switching to the 5 V
fallback is a re-tune of these same passives, never a respin**.

### NFC field current — B-54 downgraded (D-130)

DS12484's current tables still would not text-extract, so this is derived and labelled as
such: a 3.3 V differential square-wave driver into the assumed 40 Ω differential match
delivers ≈ **0.22 W** of RF; at 60–70 % driver efficiency that is **95–112 mA** from `+3V3`,
plus ~20–30 mA of reader-mode overhead.

> **Budget ≤ 150 mA from `+3V3` with the field on.**

Against D-092's enforced case (1.16–1.32 A) that takes the TPS63020 to **≈ 66–74 % of 2 A**
— comfortable — and **MX-1 means the NFC field is never concurrent with LoRa TX anyway.**
**No simultaneous RF operation is claimed.** The datasheet figure or a bench measurement is
still owed before fabrication.

### Mechanical

**NFC antenna clear region: 48 × 48 mm minimum** — 46 mm antenna plus installation
tolerance. Rear upper region, no battery overlap, ferrite face toward the internal
electronics and ground plane, no speaker-magnet overlap, no bosses or screws through the
active zone, and the stored 433 MHz flex must not cross it. **No enclosure external-size
change.**

Two constraints follow from the parts rather than the zone: **`J7` needs vertical mating
clearance**, and **the antenna cable is 75 mm**, so `J7` must sit within 75 mm of routed
cable length of the antenna position — cheap to honour now, expensive after placement.

### Nothing prohibited was added

No full RF test connector, no AAT varactor network, no extra RF switches — no technical
blocker required any of them. `TP37`/`TP38` on the antenna terminals, `TP32` on
`NFC_SUPPLY` and the accessible `R106` FIT / `R107` DNP source-select links were already in
place. `J7` is the interface the locked antenna requires, not an addition.

**A reference collision was caught before it reached the netlist:** the new connector was
first drawn as `J6`, which is already the speaker connector on sheet `06`. It is `J7`.

### Flagged for CTO decision — the ferrite is directional

Taoglas catalogues an otherwise identical **reverse-ferrite** version of this same 46 mm
antenna with the same ACH(F) cable. Which one is correct depends on which face bonds to the
enclosure wall: the ferrite must end up **between the coil and the metal it is shielding** —
the PCB ground plane and the battery. **Zero board change and zero schematic change either
way; it is a purchasing line item** — but ordering the wrong orientation costs a lead time,
not a rework, so it must be settled against the actual enclosure stack **before the first
antennas are ordered**.

### Not done, and not claimed

Sheets `05`–`09`, the PCB, mechanical CAD, firmware and the Beta-DM / frozen-Beta trees
untouched. **No RF tuning performed and none claimed.** B-48, B-49, B-50, B-51 and B-52
remain open from FBV2-S1-004.

---

## 2026-08-23 — Radios and NFC migrated (FBV2-S1-004)

**Overall 40% → 43%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-RADIOS-NFC = PASS**. FBV2-S1 is **4 of 9 sheets**. Full analysis:
[`audits/2026-08-23-s1-radios-nfc-implementation.md`](audits/2026-08-23-s1-radios-nfc-implementation.md).

**ERC: 4 errors → 2. Total 86 → 68. Zero added, eighteen removed.** This is the first
migration task to *reduce* the project's error count, and it did it by deleting
placeholder architecture rather than by suppressing anything.

**Zero `*_TBD` nets remain anywhere in the project.** Sheet 04 alone retired fourteen.

### RF architecture locked (D-118)

| band | architecture |
|---|---|
| **433 MHz / CC1101** | **INTERNAL** flex. `U7` IPEX → 100 mm coax → Taoglas `FXP450.07.0100C` against a plastic wall |
| **915 MHz / SX1262** | **EXTERNAL.** `U8` IPEX → short pigtail → **top-panel SMA female bulkhead**, user-changeable |

**Neither band has a motherboard 50 Ω RF trace, matching network, RF switch or diplexer.**
Both modules present their own matched 50 Ω port, so the board's RF involvement at 433 and
915 MHz is *zero copper*. This **supersedes the internal-FXP890 plan for 915 MHz** in
`12 - RF and Antenna Plan v0.1`; 433 MHz is unchanged.

**The `U7` IPEX socket must stay service-accessible with the shell open.** If internal
433 MHz performance disappoints on the first units the flex unplugs and an external pigtail
replaces it — **no PCB respin**. That is an FBV2-P1 placement constraint, and it is the
whole reason the internal antenna is an acceptable first-build risk.

### 433 antenna verified, mating proven rather than assumed (D-119)

Taoglas datasheet `SPE-23-8-180-A`, verbatim: *"410-470MHz Flexible PCB Antenna with 100mm
1.37 IPEX MHFI"*. **47 × 17 × 0.28 mm**, adhesive mount, gain −0.36 / −1.57 / −0.05 dBi,
**Active, 54 in stock, $5.52 @ 1, MOQ 1**.

**The connector question is settled by two documents, not by inference:** the antenna
terminates in **IPEX MHF I**, and Ebyte's manual lists the `E07-400M10S` interface as
**IPEX-1 / stamp hole**. MHF I, IPEX-1 and U.FL are one mating interface. No cable variant
is required.

**Mechanical reservation recorded for FBV2-P1:** plastic wall, LEFT/LOWER-SIDE region,
**not laid on the PCB**, and clear of the LiPo, the NFC loop and its ferrite, the speaker
magnet, large ground pours, metal bosses, the USB shell, the 915 bulkhead and pigtail, and
the IR structures. The 100 mm cable decouples the antenna body from the module, so the zone
is a mechanical choice.

### 915 external interface defined (D-120)

`U8` **IPEX-1/MHF-I plug** → **1.13 mm or RG-178, 100–150 mm** → **SMA FEMALE bulkhead**.
Loss **≤ 0.3 dB** at 915 MHz — negligible against +22 dBm.

**Female is deliberate.** The 915 MHz LoRa ecosystem is SMA-male antennas onto female
jacks; RP-SMA is a Wi-Fi convention and would force users onto an adapter for nothing. No
proprietary interface.

**The interface is locked; the assembly MPN is not** — under D-096 a pigtail part number
must come from a live listing (**B-51**). Top panel: **≥ 8 mm** edge-to-edge between the SMA
body and either IR aperture, pigtail clear of the optical path (**B-52**, no CAD created).

### Both module stamp-hole feeds are now explicit no-connects (D-121)

`U7.21` and `U8.21` `ANT` are the alternative 50 Ω stamp-hole pads; AQROOT feeds both
modules through their IPEX sockets. `CC1101_ANT_TBD`, `RF_ANT_TBD`, `CC1101_RF_TBD` and
`SX1262_RF_TBD` are retired — **the last two were orphan labels on stubs connected to
nothing, and were two of the project's four ERC errors.**

### NFC supply — B-41 CLOSED (D-122)

`U9` pin 8 `VDD` and pin 10 `VDD_TX` leave the Beta-DM boost output and sit on
**`NFC_SUPPLY`**; `VDD_IO` stays on `+3V3`. First build **`NFC_SUPPLY` = `+3V3`** through
the `R106` FIT link; the `R107` DNP link is still the one-resistor 5 V fallback. **NFC is
never connected to the community 5 V rail.** **Firmware must set `sup3V`.**

The select network built in FBV2-S1-001 finally drives something:

```
/NFC_SUPPLY  (7)  R106.2 R107.2 TP32.1 C19.1 C55.1 U9.8[VDD] U9.10[VDD_TX]
```

Sheet 01 received **two label changes and one `PWR_FLAG` — no component, value or topology
change**: its `NFC_SUPPLY` label became hierarchical so the net can leave, and its
`NFC_5V_PA_PENDING` hierarchical label became local because that net no longer needs to
cross. The root crossing was **renamed rather than removed and re-added**, so no ERC entry
was created. The `PWR_FLAG` is **D-102-compliant**: the rail is genuinely `+3V3` through a
0 Ω link, KiCad cannot propagate a driver across a passive, and **the netlist is unchanged
by it**.

### NFC clock resolved (D-123)

DS12484 §2.2.8: *"The quartz crystal oscillator operates with 27.12 MHz crystals."*

**`Y1` = 27.12 MHz, 10 pF load, SMD 3225 4-pad**, with `C79`/`C80` **10 pF 50 V C0G TUNE**.
Candidate **`TXM27.12M0004322DBBDO00T`, LCSC `C362365`** — ±10 ppm, ESR 30 Ω, −40…+85 °C,
**3,420 in stock, $0.078**, JLCPCB-compatible, and a **candidate against a live listing,
not a lock** (D-096).

Load-cap sizing is stated openly rather than asserted: `C_L = C/2 + C_stray` gives ≈ 14 pF
ideal, **ST's own NUCLEO and DISCO boards populate 10 pF**, so the design starts at 10 pF
and trims — the right value depends on finished-board stray capacitance that does not exist
yet.

### NFC front end — real topology, honest values (D-124)

```
RFOx ── L_EMC ──┬── C_EMC ── GND
                ├── C_p   ── GND        (two trim positions, on purpose)
                └── C_s ── R_q ── NFC_ANT_x ── TP37 / TP38
NFC_ANT_x ── C_rx_s ──┬── C_rx_p ── GND
                      └── R_rx ── RFIx
```

Every part is **0603 and hand-reworkable**; every RF capacitor is **50 V C0G**, because the
antenna tank swings far above the 3.3 V driver supply and a 16 V part there would be a
latent field failure.

Two deliberate choices: **`C_EMC` and `C_p` are two separate shunt footprints on one node**,
giving two trim positions instead of one; and **`R_q` is fitted at 0 Ω rather than omitted**,
so raising damping is a component change and not a bodge.

> **All values are INITIAL and labelled `TUNE`.** They cannot be finalised until the
> 45 × 45 mm antenna impedance is measured and **STSW-ST25R004** is run against it, and
> **AN5276 could not be retrieved this session** — every st.com fetch timed out (**B-48**).
> **No value here is presented as an ST reference figure.**

`TP37`/`TP38` on the antenna terminals are not optional diagnostics — without probing those
two nodes the network cannot be tuned at all.

**Unused pins are explicit no-connects with recorded reasons**, not undecided ones:
`AAT_A`/`AAT_B` (AAT drives external varactors, and DS12484 warns against AAT with hardware
wake-up), `CSI`/`CSO` (capacitive sensing unused), `EXT_LM` (the internal load modulator is
used), `MCU_CLK` (the ESP32-S3 has its own clocks).

### CC1101 and SX1262

`U7`: SPI-B unchanged, `CSN` with a 10 kΩ pull-up so it is deselected through reset, `GDO0`
to GPIO15, `GDO2` still omitted, `VCC` = `+3V3`, decoupling local. No reset pin exists — the
CC1101 is reset by SPI command.

`U8`: SPI-B unchanged, `BUSY` **direct to GPIO8**, `NSS` direct with a pull-up, `NRST` from
the expander. **`SX1262_DIO1` is published as a hierarchical net** for sheet `08` to land on
the internal PCAL9535A (D-089) — it no longer reaches the MCU, because GPIO38 is now
`NATIVE_A`. Semtech §13.3.4 confirmed DIO1 is a level-holding, SPI-cleared IRQ, so an
expander input is a safe destination and a stuck-high DIO1 can no longer touch a strapping
pin, which was the reason for moving it. `DIO2`→`TXEN` on-module, `RXEN` from the expander,
`DIO3` internal TCXO at 2.2 V. LoRa deep-sleep packet wake remains **not a requirement**.

### Power budget — one rail change, and it is not yet covered (D-125)

Sheet 04 adds no new rail. But with `VDD`/`VDD_TX` on `+3V3`, **the NFC PA load moves off
`BQ25185_SYS`-via-`U13` and onto the TPS63020**, drawing proportionally more current at
3.3 V for the same field power.

**`I_VDD_TX` at 3 V supply mode was not extracted this session (B-54)**, so D-092's
58–66 % TPS63020 figure **must not be quoted as covering the NFC field in this form**.

**MX-1 is unchanged and binding: at most ONE of {Wi-Fi TX, LoRa TX +22 dBm, sub-GHz TX, NFC
field} at a time.** Firmware constraints recorded by this sheet: set `sup3V`; enable SX1262
**DIO2-as-RF-switch** or `TXEN` never asserts and TX silently fails; configure the driver
for **TCXO**; drive all three bus-B chip selects high before init and use a bus mutex.

### ESD — nothing added, and that is the finding

The 915 MHz bulkhead sees only the E22's own matched front end through a shielded pigtail —
no board trace, no exposed IC pin. An RF TVS transparent enough not to cost link budget at
+22 dBm is a real choice with real loss; **measure before adding**. The NFC loop is
magnetically coupled with series capacitors acting as a DC block. The module coax is
internal and shielded. **No random RF TVS parts were fitted.**

### Recommended, not locked — both need CTO sign-off

**P-17 — keep the non-B `ST25R3916-AQET`.** Same 32-UFQFPN package; Mouser 3,243 in stock;
**LCSC `C5267441` at ~$3.37 gives a JLCPCB assembly path the B does not have**, at roughly
half the unit cost. The B's advantages are EMVCo PCD L1 3.2a compliance and a better AWS
implementation — **AQROOT is not an EMVCo terminal**, so neither serves a stated priority,
and the B's `-AQWT` variant is a stock trap (0 units, restock quoted January 2028).
Switching would also require AN5768 and re-proving footprint equivalence. Flagged rather
than locked because it touches read range at the margin.

**B-53 — NFC antenna architecture.** Recommendation: **purchased flex + ferrite**. A
main-board loop needs a **45 × 45 mm keepout in the ground plane on every layer** in the
rear upper third, with the battery directly behind it. **The schematic is neutral**:
whichever is chosen lands on `NFC_ANT_A`/`NFC_ANT_B` and the front end does not change.

### Opened

**B-48** AN5276 not retrieved; matching values are initial. **B-49** IPEX socket population
must be confirmed with the supplier for the exact ordered `U7`/`U8` MPNs — the whole
zero-board-RF plan collapses if stamp-hole units arrive. **B-50** FXP450 bend radius,
adhesive and clearance guidance not retrieved. **B-51** 915 pigtail MPN not selected.
**B-52** SMA-vs-IR top-panel spacing recorded but no CAD. **B-53**, **B-54** as above.

### Not done, and not claimed

Sheets `05`–`09` untouched. PCB untouched and still **bit-identical** to Beta-DM. No
footprint verified with a pad-overlap assertion (**B-29**). No RF tuning performed — and
none is claimed.

---

## 2026-08-23 — Display, touch, backlight and microSD migrated (FBV2-S1-003)

**Overall 37% → 40%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-DISPLAY-SD = PASS**. FBV2-S1 is **3 of 9 sheets**. Full analysis:
[`audits/2026-08-23-s1-display-sd-implementation.md`](audits/2026-08-23-s1-display-sd-implementation.md).

### The inherited `J1` would have produced a dead display, twice over

`J1` still used the **2.8-inch `CH280QV10_CT_50P`** pin table while its Value and
Footprint fields already read `FH69-50S-0.5SH`. Pin count matched, connector matched,
ERC was silent. The pin **functions** did not match the locked `ER-TFT035IPS-6`:

| panel pin | old symbol | ER-TFT035IPS-6 | consequence |
|---|---|---|---|
| 1 / 2 / 3 | LEDK / LED-A1 / LED-A2 | **LEDA / LEDK / LEDK** | **backlight reverse-biased — no light** |
| 4, 5, 6 | LED-A3, LED-A4, IM0 | **NC** | anodes driven into NC pins |
| 7, 8, 9 | IM1, IM2, IM3 | **IM0, IM1, IM2** | by luck all three were already `+3V3` = `1 1 1` |
| **36 / 37** | WR_RS → `DISP_DC` / RS_SCL → `SPI_A_SCK` | **WRX(SCL) / D-CX** | **clock and D/C swapped — no valid command ever reaches the panel** |
| 46 | CTP_IRQ, unused | CTP IRQ | touch interrupt not represented at all |

**Neither fault is visible from a pin count, a connector MPN or an ERC run.** A new
project-library symbol **`ER-TFT035IPS-6_50P`** was authored with the vendor's table
verbatim, deliberately keeping the old pin geometry so the migration is a
pin-function change rather than a redraw. `CH280QV10_CT_50P` stays in the library —
Beta-DM still uses it — and is dropped from sheet `03`'s symbol cache.

**The PO must name BOTH `ER-TFT035IPS-6` and `ER-TPC035-6`. The vendor's CST340 touch
variant is NOT authorised without a new engineering review** — the FT6236 address,
the driver and the `TOUCH_RST_N` enumeration pulse are all locked around FT6236.

### `R111` fitted — GPIO45 closed (D-111)

10 kΩ, `GPIO45_VDDSPI_STRAP` → GND. VDD_SPI is now held LOW deterministically instead
of relying on the chip's internal pull-down alone. `TP1` retained, no capacitance on
the net, no peripheral on GPIO45.

### B-43 closed with a primary source (D-116)

TPS61169 datasheet **SNVSA40B**: **`R_PD` — CTRL pin internal pull-down resistor —
300 kΩ**, with `V_H`/`V_L` = 1.2 / 0.4 V and `t_SD` = 2.5 ms.

**`CTRL`'s only internal element pulls DOWN.** There is no mechanism by which the
backlight driver can raise the GPIO46 strap. With `R108` 10 kΩ in parallel GPIO46 sees
**9.68 kΩ to GND** — stronger than the strap provision alone — and the backlight is off
through reset by construction. `R109` is retained: its strap-escape justification is
retired, but a fitted 0 Ω costs nothing as a general isolation point. **GPIO46 strap
safety was not weakened for backlight convenience.**

### Backlight re-derived, not copied (D-115)

From SNVSA40B `V_REF` = **188 / 204 / 220 mV**:

* **`R69` = 1.87 Ω ±1 %** — an E96 stocked value, so no substitution was needed.
  **I_LED = 100.5 / 109.1 / 117.6 mA.** The panel is rated **120 mA maximum** with a
  90 mA life point: the worst-case corner sits **2.0 % below the maximum and never
  above it**. Per-LED current *falls* from 20 mA to 18.2 mA, so LED life improves.
* **`R70`–`R73` = 4 × 33 Ω in parallel = 8.25 Ω** on the single `LED_A` node. Four
  footprints retained and repurposed: quarter the per-part dissipation (24.6 mW in an
  0603 rated 100 mW) and three DNP-able trim steps available as pure rework.
* **Peak switch current 263 mA at 1.2 MHz (4.6×) and 309 mA at the 0.75 MHz minimum
  (3.9×)** against the 1.2 A minimum limit. `L3` 10.7×. **`D8` NSR0240 at 2.1× is the
  tightest item and is retained**; a same-footprint 0.5 A uprate is recommended, not
  required. **B-32 closed** — `C43` 4.7 µF X5R sits on `U17` `VIN`.

### Display SDO — **DNP**, and the reasoning is on the record (D-114)

The vendor says of pin 33 *"leave the pin open when not in use"* and does **not**
specify SDO's high-Z behaviour while `CSX` is high. SPI-A is shared with the microSD.

**The risk is asymmetric: fitting `R112` puts a core feature at risk of bus contention
to gain a feature nothing uses — AQROOT never reads the display.** `R112` is therefore
**0 Ω DNP**, with `TP36` on the panel side so SDO release can be characterised on the
first board without fitting anything. This closes **B-28** with the *opposite* default
to the one FBV2-DISP-002 sketched, which wrote "fit a 0 R" before weighing which of the
two features is load-bearing. **No series resistance was added to the `SPI_A_MISO` bus
itself** — the microSD `DAT0` path stays direct.

### Touch gains an interrupt

`CTP_IRQ` (panel pin 46) was not represented at all on Beta-DM. It now leaves the sheet
as **`TOUCH_INT_N`** and lands on an internal PCAL9535A input with sheet `08`. FT6236 at
**0x38** and the `TOUCH_RST_N` safe state are unchanged. **No second I²C pull-up pair
was added** — the internal bus keeps its single locked `R19`/`R20` pair, and a
panel-side pair would halve the effective pull-up for nothing. **`RESERVED_SPARE` was
not consumed.**

### microSD — the `*_TBD` net is gone (D-117)

`SD_CARD_DETECT_TBD` was a **one-pad net**: a switch terminal with no pull and no
destination. It is now **`SD_CARD_DETECT_N`** — `J2.10` DET-SW with **`R113` 100 kΩ to
`+3V3`**, `J2.11` DETECT_LEVER grounded — a real two-state signal whose destination is
an internal PCAL9535A input on sheet `08`. Polarity assumes the usual push-push
convention (**LOW = card present**); the Molex drawing would not load, so this is
assumed, not confirmed (**B-46**) — and the exposure is nil, because polarity is a
firmware constant on an expander input, never a board change.

Molex `5025700893` is **retained** — no lifecycle, mechanical or electrical reason to
change it was found. DAT1/DAT2 stay NC as validated on Beta-DM.

### `J1` footprint audit (D-113)

Measured from the footprint file: **50 pads, 0.500 mm pitch with no drift across all 49
gaps, 24.500 mm span, 0.300 × 1.230 mm pads, 2 hold-downs at ±14.365 mm.** Every
measurable parameter **PASSES** against the archived Hirose figures.

**FH52E is NOT claimed as a drop-in and `J1` did NOT move to the FH52E land pattern.**
FBV2-DISP-002 proposed that on the strength of a Hirose note that FH69 *also* fits the
FH52E pattern — which proves one direction only. Full footprint **and mechanical**
equivalence was not demonstrated from both drawings, so it is not asserted.
**Consequence: there is currently no JLCPCB assembly path for `J1`** (FH69 is not in
LCSC; FH52E is, as `C7465440`). **B-47** — settle at FBV2-S2, before placement.

### SPI-A stays passive

Both chip selects are pulled to `+3V3`, so display and microSD are deselected through
reset. **No bus mux and no series damping were added** — damping belongs with real trace
lengths, which do not exist until FBV2-P1. The ILI9488's 18-bit / 3-byte-per-pixel SPI
writes are accepted with **no architecture change and no new native GPIO**.

### Battery target unchanged

The backlight is the only load this task moved: **+11 mA at the pack** at default
brightness (118 → 129 mA). Runtime improves for any baseline browsing current above
**44 mA**, and the Beta-DM backlight alone draws 118 mA — so **60 × 75 × 8 mm /
~2500–3000 mAh gives equal or better runtime by a wide margin.** At a representative
250 mA the ratio is 1.20 at 2500 mAh and 1.44 at 3000 mAh.

### A latent defect caught by inspection, not by a check

The `LED_BOOST` netclass listed the four old anode nets by exact name and had no entry
for the new single `LED_A`, so the anode would have fallen to **Default clearance** at
FBV2-P2. `netclass_probe.py` reads the *board*, which is still Beta-DM, so no probe
would have caught it. `/03_SPI_A_DISPLAY_SD/LED_A` was added to `LED_BOOST`.

### ERC

**4 errors → 4 errors; the error report is byte-identical to after FBV2-S1-002.** Total
63 → 64: two `isolated_pin_label` warnings added for the `TOUCH_INT_N` crossing, one
removed because `SD_CARD_DETECT_TBD` ceased to exist.

Sheet `03` carries **18 inherited `pin_to_pin` warnings** — DB17–DB0 tied to a flagged
`GND` net. The count is unchanged from Beta-DM and **they were deliberately not
silenced**: re-typing the panel's parallel data pins as `passive` would clear all 18 and
would also make the symbol lie about the part.

### Not done, and not claimed

Sheets `04`–`09` untouched. PCB untouched and still **bit-identical** to Beta-DM. No
footprint verified against a vendor drawing with a pad-overlap assertion (**B-29**). No
MPN newly locked. **B-15** unchanged.

---

## 2026-08-23 — Power-tree rulings closed, MCU core migrated (FBV2-S1-002)

**Overall 34% → 37%. No gate in the twelve-gate table passed**; the task gate
**FBV2-S1-MCU-CORE = PASS**. FBV2-S1 itself is **2 of 9 sheets**. Full analysis:
[`audits/2026-08-23-s1-mcu-core-implementation.md`](audits/2026-08-23-s1-mcu-core-implementation.md);
measured pin ledger and strap audit:
[`architecture/GPIO_LEDGER.md`](architecture/GPIO_LEDGER.md).

### P-20 closed — `R95` = 560 Ω, and B-27 is amended rather than left wrong

Recovery current recomputed from the captured circuit: **8.36 mA** at VBUS 5.0 V into
a 0 V pack, **7.93–8.80 mA** across 4.75–5.25 V. That is inside the accepted 5–10 mA
band and restores the ≈ 8 mA the architecture assumed, which is what **B-26** is
measured against.

**680 Ω was not an arbitrary capture value.** It is exactly the value that produces
B-27's recorded ≈ 13 mA single-fault ceiling: `(5.00 − 0.32 + 4.2) / 680 = 13.06 mA`.
With 560 Ω the ceiling becomes **≈ 15.9 mA nominal, ≈ 16.6 mA worst case** — 0.0066 C
on a 2500 mAh pack, still bounded by `R95`, still unidirectional through `D12`, still
self-annunciating. **B-27 is restated in place.** The trade is explicit: ~21 % more
recovery current for ~22 % more single-fault current, and the CTO ruled for recovery.

### P-21 closed — OV trip **derived**, not typed

The datasheet threshold was obtained first (LTC4368, Farnell mirror `2243878`):
`V_OV` **492.5 / 500 / 507.5 mV** rising, hysteresis **20 / 25 / 32 mV**, UV/OV leakage
**10 nA max**, features page "Adjustable **±1.5 %**".

`R77` **4.02 M → 3.65 M 1 %**, `R78` unchanged at 442 k:
`0.500 × (3.65 M + 442 k) / 442 k` = **4.629 V**.

| | |
|---|---|
| Nominal trip | **4.63 V** |
| Comparator + 1 % resistors | **4.48 – 4.78 V** |
| Including 10 nA max pin leakage | 4.44 – 4.82 V |
| Release (25 mV hysteresis × 9.258) | **4.40 V** nominal |

Above a 4.35 V-class pack with 129 mV of worst-case margin, 420 mV below the 5.05 V
first capture, and **no lockout hazard** because release sits above the float voltage.
`3.65 M` is already carried by `R91`, so this **removes** a BOM line.

### P-22 closed — scripted KiCad edits, under eight conditions

The blanket Beta-DM prohibition is superseded by **D-107**: deterministic; narrowly
scoped; source-controlled and diffable; the project parses afterwards; netlist
validation; ERC against a stated baseline; preservation checks; and the output
reviewed against the CTO task item by item. **Scripts may not be used to bypass
engineering review** — a script that cannot show all eight is an unreviewed change.

### `02_MCU_CORE` migrated

* **GPIO38 = `NATIVE_A`** and **GPIO47 = `NATIVE_B`** — the two native community
  fast-IO signals (D-084/D-108). `SX1262_DIO1` **no longer reaches the MCU**; under
  D-089 it terminates on the internal expander `U2`, which is sheet `08`.
* **GPIO46 = `DISP_BL_CTL`.** GPIO46 is a strapping pin that **must read LOW at reset**
  — GPIO0 = 0 alone does not select Joint Download Boot, GPIO46 = 0 is also required.
  Three provisions make that safe: **`R108` 10 kΩ pull-down at the pin** (Espressif's
  own "strong pull-down" against the 45 kΩ internal pull), **`R109` 0 Ω FIT** isolating
  the TPS61169 `CTRL` so the strap survives even if `CTRL` sources current — failure
  direction "backlight off" — and **`TP2` on the strap node** so the level is measured.
  No capacitance was added; Espressif forbids bulk C on strapping pins.
  Quantified: any `CTRL` internal pull-up **≥ 30 kΩ** keeps GPIO46 below `V_IL`.
* **GPIO43 withdrawn from the community port** (D-106) — internal UART0 TXD only, with
  **`TP35`**. Consequence recorded: GPIO44 is IR RX, so **UART0 is TX-only**, and ROM
  download recovery is via the native **USB Serial/JTAG on GPIO19/20, never UART0**.
* **GPIO3 strap defined — B-09 CLOSED** (D-109). `R110` 10 kΩ pull-down. LOW is the
  only correct level: GPIO3 = 1 would select external JTAG on MTMS/MTDI/MTCK/MTDO =
  **GPIO39–42, which are the I²S bus**. **BMI270 `INT1` is bound to push-pull
  active-high; open-drain must never be configured on this pin.** The IMU cannot corrupt
  the strap at reset — `INT1` is high-Z until firmware enables it.
* **`R111` 10 kΩ GPIO45 pull-down placed DNP.** GPIO45 selects VDD_SPI (LOW = 3.3 V) and
  today is held only by the chip's internal pull-down while an exposed test pad sits on
  the net. Fitting it is referred to the CTO — see below.
* `TEST_GPIO45` / `TEST_GPIO46` renamed to `GPIO45_VDDSPI_STRAP` / `DISP_BL_CTL_STRAP`
  under D-100.

**`NFC_IRQ` verified still on GPIO18.** B-19 holds: it must never move to GPIO46.

### No new debug hardware

**D-110.** The service interface is the native USB Serial/JTAG on GPIO19/20 — one
USB-C cable gives console, ROM download and JTAG debug. No debug connector, no debug
IC, no JTAG header, no new user-facing button; `SW1` BOOT stays electrically real and
becomes mechanically recessed. **One test pad added — `TP35` on UART0 TXD** — because
the ROM boot log is the only view of a board whose USB will not enumerate, which is the
one failure USB cannot diagnose. An `EN` pad was considered and **rejected**.

### ERC

**5 errors on the Beta-DM baseline → 4. Zero new errors. `02_MCU_CORE` reports nothing
at all.** Warnings 55 → 63. All eight additions are root-sheet `isolated_pin_label`
entries on cross-sheet signals with one end drawn: `NATIVE_A`/`NATIVE_B` (await sheet
`09`), `SX1262_DIO1` (awaits sheet `08`), `FAST_IO_U0TXD_ROOTPROBE_CS` (dies with the
20-pin port). **Each was left standing deliberately** — silencing them by adding a test
point to an orphaned net is the same anti-pattern as a `PWR_FLAG` that hides a missing
driver.

### Opened

**B-43** TPS61169 `CTRL` internal-pull spec **not retrieved** — TI's PDF text layer
would not extract. The design is safe for any pull-up ≥ 30 kΩ and `R109` is the escape,
but the number is a blocker, not an assumption.
**B-44** BMI270 `INT` pad drive current **not retrieved** — Bosch's PDF likewise.
Fallback: `R110` → 47 kΩ, a value change with no board change.
**B-45** `NATIVE_A`/`NATIVE_B` still have **no D-090 series resistors and no TVS**. They
are the only two contacts with a direct MCU path. Sheet `09` work.

### Referred to the CTO

**Fit `R111`?** GPIO45 relies on the internal pull-down alone to hold VDD_SPI at 3.3 V,
with an exposed test pad on the net; a GPIO45 that reads HIGH at reset selects 1.8 V and
the 3.3 V flash and PSRAM do not boot. **Recommendation: fit it.** Placed DNP rather
than fitted because changing the electrical design of a strapping pin is a CTO call, not
a capture decision.

### Not done, and not claimed

Sheets `03`–`09` untouched. PCB untouched and still **bit-identical** to Beta-DM. No
footprint verified. No MPN locked. **B-15** unchanged — no telemetry crossing to
`U2`/`U3` exists.

---

## 2026-08-23 — Full Beta v2 power tree CAPTURED (FBV2-S1-001)

**The first Full Beta v2 design-file work.** `hardware/beta-v2/` is created, forked
from Beta-DM, and `01_power_tree.kicad_sch` now carries the Full Beta v2 power
architecture. Full analysis:
[`audits/2026-08-23-s1-power-tree-implementation.md`](audits/2026-08-23-s1-power-tree-implementation.md).

**Overall 31% → 34%. FBV2-S1 does NOT pass.** Its exit criterion requires *every*
schematic change in the migration order to be landed. One sheet of nine carries the
v2 architecture; the other eight are byte-equivalent copies of Beta-DM. What passes
is the task gate **FBV2-S1-POWER-TREE**.

### What is now in the file

136 parts on `01_POWER_TREE`, all with footprints assigned:

* **Battery reverse protection, P2** — `J4` → `F1` 5 A → `BAT_RAW` → `Q2` (stage A)
  → `BAT_MID` → `Q3` (stage B) → `BAT_SENSE` → `R75` 15 mΩ → `BAT_PROTECTED_P` →
  `U11` BAT. Controller `U18` LTC4368-1: `RETRY` grounded (latch-off), `UV` unused
  via 510 k to VIN per the datasheet, `OV` divider, 22 k/4.7 nF gate RC, `SHDN`
  pull-up with an N-FET pull-down, `D9` secondary negative clamp. Two stages in
  **two packages**, common-source pairs — **B-01 is closed at schematic level.**
* **Autonomous dead-cell recovery** — `U19` TLV7032 with a ratiometric polarity
  bridge (matched `D10`/`D11` Schottkys make the trip supply-independent at
  `BAT_RAW` = 0 and block pack drain when USB is absent), a handoff comparator
  asserting below ≈ 2.63 V of pack, a three-input **series** AND (`Q6`/`Q7`/`Q8`),
  `Q9` inverting `FAULT`, and `Q5`/`R95`/`D12` injecting current-limited,
  unidirectional charge. USB-powered and firmware-independent.
* **Accessory power** — `+3V3` → `U20` TPS22950C → `ACC_3V3_SW` and `BQ25185_SYS` →
  `U21` TPS61023 (4.99 V) → `U22` TPS22950C → `ACC_5V_SW`, both `FLT` pins wire-ORed
  onto `ACC_POWER_FAULT_N`. **D-088 BOM consolidation honoured exactly**: `L4` is the
  same Würth MPN as `L2`, `R99`/`R100` are the same 732 k/100 k divider as `R44`/`R45`,
  `C65`/`C66` mirror `C34`/`C35`. One boost family, one load-switch family, differing
  only in `R_ILIM` (1.5 k and 1.65 k, the values D-086/D-087 specify).
* **NFC no-respin source select** — `R106` 0 Ω **FIT** from `+3V3`, `R107` 0 Ω **DNP**
  from the boost.
* **Telemetry** — `VBUS_PRESENT` divided to 2.97 V at VBUS 5.0 V, so raw VBUS never
  reaches the expander; `LTC4368_FAULT_N`; `ACC_POWER_FAULT_N`; 19 test points.

### ERC: zero introduced

Beta-DM baseline **58** → Beta-v2 at resume **60** → Beta-v2 now **55**. The lists were
diffed, not counted. **Nothing was added.** Three inherited violations were retired: a
dangling root `BAT_PROTECTED_P` label, and two `isolated_pin_label` on
`BAT_CONNECTOR_P`, which was a one-pad net in Beta-DM and is now real.

**This is not "ERC clean" and must not be quoted as such.** 55 inherited violations
remain on the unmigrated sheets and belong to FBV2-S2.

Three defects were closed to get there: the missing `BAT_PROTECTED_P` label on the
`U11` pin-2 stub; a `PWR_FLAG` on `VREC_VCC`, whose drive arrives through `R84` and so
cannot be inferred by ERC — the electrical connection to VBUS was already correct and
no net was joined, split or renamed; and an orphaned wire and label left on the **root**
sheet when the `BAT_PROTECTED_P` hierarchical pin was removed.

### `U18` package corrected — a locked decision had been contradicted

`U18` LTC4368-1 had been assigned a **DFN-10 with an exposed pad**. FBV2-PWR-002 locks
the package policy for this circuitry: *"leaded and inspectable … no BGA, no WLCSP, no
bottom-terminated parts."* A DFN-10 is bottom-terminated, on the most safety-critical
part on the board. Corrected to `Package_SO:MSOP-10_3x3mm_P0.5mm` (the locked candidate
is `LTC4368IMS-1#PBF`, MSOP-10) in both the sheet and the project symbol library.
**The land pattern is still unverified** — that is FBV2-S2.

### `R_FB_TOP 1M` — an inherited net-name defect, fixed in v2

A literal net label reading `R_FB_TOP 1M` — a value annotation placed as a label.
`R39` is indeed 1 MΩ. The net is the TPS63020 `+3V3` feedback midpoint; renamed
**`V3V3_FB`** in `hardware/beta-v2/` only. Beta-DM is frozen and keeps it. All 56 labels
on the sheet were audited for embedded values, spaces, near-duplicate rails and isolated
single-pin nets; nothing else was found, and no correct name was touched.

### Fork provenance is now measured, not asserted

`checks/fork_equivalence.py` re-derives the classification of every forked file from
disk; `reports/FBV2-S1-fork-equivalence.md` pins the result. Sheets `02`–`09` are
byte-equivalent after normalising the project name **only**; `.kicad_pcb`, `.kicad_dru`,
both lib-tables and all 12 project footprints are **bit-identical**; `.kicad_pro` differs
by project name alone, so no design rule or netclass changed. `hardware/beta-dm/`,
`hardware/beta/` and `hardware/beta/mechanical/` are unchanged.

`checks/netclass_probe.py` had been copied without repointing and was still testing
**Beta-DM's** files from inside the v2 tree. Repointed; still PASS.

### Opened

**B-41** `NFC_SUPPLY` has no consumer — `U9` `VDD`/`VDD_TX` are still on
`NFC_5V_PA_PENDING` on sheet `04`, which this task could not modify. The v2 NFC supply
architecture is **half implemented**.
**B-42** the NFC source select is mutually exclusive **by fit state only**; fitting both
0 Ω links shorts `+3V3` to the boost output. Needs an assembly-note requirement.
**P-20** `R95` = 680 R against a locked 560 R. Injection falls to ≈ 6.9 mA, moving the
wrong way against **B-26**. Recorded, **not** silently changed — a value in a locked
architecture is changed by a ruling, not by a capture task.
**P-21** `OV` trip captured at 5.05 V against a documented ≈ 4.6 V.
**P-22** the standing *"no automatic KiCad file generation"* rule was overtaken: this
capture was scripted. Recorded in place and flagged for ratification or reinstatement
rather than treated as repealed.

### Recorded

**D-099** `U18` package corrected to MSOP-10. **D-100** net names describe nets, not
component values. **D-101** `TP34` added on `BAT_CONNECTOR_P`. **D-102** `PWR_FLAG` is
permitted only where a rail is genuinely driven and KiCad cannot infer it — never to
silence an error. **D-103** `BAT_PROTECTED_P` is local to `01_POWER_TREE`.

### Not done, and not claimed

No PCB work of any kind — `aqroot-Beta-v2.kicad_pcb` is still the Beta-DM board, bit for
bit, and does not match this schematic. No footprint verified. No MPN locked. Sheets
`02`–`09` untouched. `B-15` stays open: the `VBUS_PRESENT` divider exists but no charge
or VBUS telemetry crossing to `U2`/`U3` does.

---

## 2026-08-23 — Community connector CORRECTED and final-locked (FBV2-COMM-002)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.

**This entry corrects an error rather than adding progress, and the percentage is
held at 31% accordingly.**

### Harwin `M20-7881242` is rejected

The CTO's lifecycle finding stands and is corroborated:
**`harwin.com/products/M20-7881242` returns HTTP 404** — the part number does not
resolve to a live catalogue item.

It should never have been recorded as locked. **The MPN was configured from the
Harwin catalogue's ordering scheme** (`M20-78` + `8` for double row + `12` per row
+ `42` for gold+tin) rather than taken from a live listing, and FBV2-COMM-001's own
limitations section said so in as many words: *"It should be verified against a
live distributor listing before the BOM is issued."* The flag was right; the part
was written into the locked documents anyway.

That gap is now closed by rule rather than by intention. **D-096: a part number
configured from an ordering scheme is a hypothesis, not a selection. Every MPN
entering a locked document must first be confirmed against a live manufacturer or
distributor record showing lifecycle status and stock.** It applies to every
subsequent selection in the programme.

`M20-7881242` has been struck through in place — not deleted — in
`CTO_DECISIONS.md`, `ARCHITECTURE.md`, `MECHANICAL_INTERFACE_SPEC.md`,
`PROGRESS.md` and the FBV2-COMM-001 changelog entry.

### Connector re-locked: Samtec `BCS-112-S-D-HE`

.100 in / 2.54 mm, **2 × 12 / 24 contacts**, **FEMALE** Tiger Claw™ dual-beam
receptacle, **horizontal (right-angle) entry**, **through-hole**, **30 µin
selective gold** in the contact area with matte tin on the tail (D-093).

**ACTIVE**, with **385 pieces shipping next-day** from Samtec at **MOQ 1**
($7.314 @ 1, $5.667 @ 100). Digi-Key lists the series as *Active*. Body
**30.48 (L) × 8.13 (D) × 5.33 (H) mm**. **4.6 A per contact** mated with TSW,
450 VAC / 636 VDC, **−55 to +125 °C**, glass-filled LCP UL94 V-0, UL E111594,
halogen-free, MSL 1.

**The footprint is new and is not interchangeable with anything already drawn:**
2 × 12 plated through-holes, 2.54 mm within a row, **7.87 ± 0.05 mm *between*
rows** — the horizontal-entry tails splay outward — with **0.71 mm drills** and a
27.94 mm end-hole span. B-29 is re-scoped to this pattern.

### Why the locked MPN is `-S` and not the `-L` that was proposed

This is what verifying the extended-life information was for.

Samtec's own design-qualification report (187544 Rev 1) gives **100 mating cycles
for BOTH** the 10 µin (`-L`) and 30 µin (`-S`) gold options. The E.L.P.
extended-durability data — **2 500 cycles** — is qualified **by similarity at
30 µin gold only**.

So at `-L` the community port would have been rated **100 cycles**, which is
*worse* than the 300 gold cycles of the part just rejected. For a
**user-swappable community port on a maker platform, mating-cycle life is a
first-order product parameter**, not a detail. The `-S` upgrade costs **$2.88 per
board at quantity one — roughly $14 across the first five boards** — for the only
plating with extended-life evidence behind it. Same body, same footprint, one
character of the part number. **`BCS-112-L-D-HE` is retained as a plating-only
cost-down alternate requiring no board change.**

**Recorded honestly as B-39:** the 2 500-cycle figure is **by similarity**, and the
only count formally qualified for BCS itself is **100 cycles**. Samtec must confirm
the rating for `BCS-112-S-D-HE` before the production run. The design assumption
for the first five boards is *"≥ 100 cycles qualified, 2 500 supported by
similarity at 30 µin gold."* **It is not claimed as 2 500.**

### Commodity 2.54 mm compatibility is preserved — with one rule

BCS accepts standard **0.64 mm (.025 in) square posts**, and the horizontal-entry
engagement window is **4.34 mm to 6.35 mm**. An ordinary 2 × 12 2.54 mm header with
a ~6.0 mm post qualifies. **Extra-long-pin headers (8.13 mm / .320 in posts) must
NOT be used** — they exceed the window. Reference accessory mate:
**`TSW-112-07-L-D`** (5.84 mm post), or a `-RA` right-angle variant for a coplanar
accessory. That one sentence is what preserves the entire reason for choosing
2.54 mm in the first place.

### Enclosure keying and load path locked (D-097)

The connector carries **no integrated key** — the BCS polarized-position option
exists but consumes a contact, which D-081 forbids. So: the socket face is recessed
**≥ 1.5 mm** behind the right wall and the recess walls form the shroud; an
**asymmetric rib/step on the upper edge only** blocks upside-down insertion (the
two mating rows are just 2.54 mm apart, so the key must be unambiguous rather than
a chamfer); the recess is **closed at both ends** with ≤ 0.3 mm clearance so a
one-column offset is mechanically impossible; a moulded **shelf and backing rib
capture the connector body**; and the accessory shell bottoms on an **enclosure
boss** so the insertion force is never carried by the 24 solder joints.

Insertion force is **≈ 33 N average** (24 × 1.39 N) with **withdrawal ≈ 20 N
average** — better than the ≈ 48 N maximum of the rejected part. These are Samtec
*averages*; Samtec's own note explains the peak occurs during the contact-spreading
stage and exceeds the average, so the load path is sized with that acknowledged
rather than assumed away.

### Z-stack rechecked, and it improves

| layer | Harwin (rejected) | **Samtec BCS** |
|---|---|---|
| Connector body above PCB | 8.10 mm | **5.33 mm** |
| **Column total of the 23.0 mm external budget** | **22.30 mm** | **19.53 mm** |
| **Spare** | **0.70 mm** | **3.47 mm** |

**The connector region is no longer the sole governing column** — it is now level
with the control region's 19.5 mm. **3.47 mm is real, usable clearance**, which is
the standard the ruling demanded. The 5.33 mm figure is read from the Samtec series
print and cross-checked three ways (the `-S-HE` view differs by exactly one 2.54 mm
row pitch; the vertical `-D-TE` body width is .20 in; the vertical insulation height
of 7.37 mm matches). It must still be confirmed against the individual 3D model at
FBV2-P1 — **M-09, downgraded to LOW**, and the conclusion survives even a 2.8 mm
error.

### Electrical allocation unchanged

The BCS has the same 2 × 12 topology with the mating rows stacked vertically, so
**D-082 and D-084 transfer unchanged.** Power and ground remain distributed across
columns 2, 5, 8 and 11; every power contact is still vertically GND-paired; all
3.3 V is in row A and all 5 V in row B; both native pins still flank the GND at
pin 9; the detect strap is still one 0 Ω link between pins 21 and 23. **The entire
mis-insertion argument carries over intact.**

### The three opportunity rulings

**O-1 APPROVED** (D-094). The two TPS22950C `FLT` outputs are open-drain and are
**wire-OR'd into `ACC_POWER_FAULT_N`** — one 100 kΩ pull-up, one PCAL9535A input at
`U3` P15. **`U3` P16 becomes `RESERVED_SPARE` with no function assigned**, brought
out to a test pad with a 100 kΩ pull-up so it reads a defined level and can be
pressed into service by a wire and a firmware change rather than a respin. Rev 1
now retains an expander resource for recovery. Rail attribution is by **controlled
isolation** (MX-5a): disable one rail and observe whether the fault clears. **B-37
is half closed** — `U2` still has zero spare.

**O-2 APPROVED** (D-095). **External I²C address `0x50` is reserved** for an
optional AQROOT accessory-identification EEPROM — **protocol reservation only, no
main-board hardware, and no accessory is required to carry one.** It joins the
reserved table with 0x38, 0x68, 0x36, 0x20 and 0x21. One thing flagged rather than
locked (**P-19**): the 24Cxx family spans **0x50–0x57**, so an AQROOT ID EEPROM
must strap A0–A2 = 0, and 0x51–0x57 remain unreserved.

**O-3 REJECTED** (D-095). The accessory TPS61023 5 V rail is **not** connected to
the NFC fallback — no DNP link, no shared node beyond `SYS`. Sharing the TPS61023
*device family* is the extent of the BOM consolidation, exactly as D-056 intended.

### Accessory limits, and the rule most likely to be misread

**`ACC_3V3_SW` = 400 mA total. `ACC_5V_SW` = 300 mA total** for the first five
boards (D-098). Later targets of 600–800 mA and 500 mA require measured bring-up
and a CTO ruling; the hardware change is one 0603 resistor per rail.

> **The duplicate contacts SHARE the rail limit. They do not double it.**
> `ACC_5V` pin 10 + pin 22 = **300 mA combined, not 300 mA each.** There is one load
> switch and one current limit per rail; the second contact halves contact
> resistance and eases routing, and adds no current budget. This must appear in
> accessory documentation in these words.

### Two new opportunities, flagged not locked

**N-1** — publish an accessory reference design: the 2 × 12 footprint, the
4.34–6.35 mm post-length rule, the detect-strap pattern, the shared-rail current
rule and a board-outline template that fits the recess. High value,
documentation-only, zero main-board cost — but it is a deliverable this task was
not authorized to create. **N-2** — accessory retention: withdrawal force is only
≈ 20 N average with no latch, so an enclosure friction detent or a captive fastener
is worth considering; it is a mechanical and ergonomic trade-off for enclosure CAD.

Full analysis:
[`audits/2026-08-23-community-connector-correction.md`](audits/2026-08-23-community-connector-correction.md).

---

## 2026-08-23 — Community expansion port and accessory power LOCKED (FBV2-COMM-001)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.
**This was the last architecture closeout before schematic implementation.**

**COMMUNITY PORT LOCK = PASS. P-02, P-15, P-16 and B-08 all CLOSED.** No
architecture item now gates any schematic sheet.

### The 20-pin community port architecture is superseded

**D-059 and D-062 no longer describe this product** and nothing downstream may
cite them. The principles that survive are carried forward explicitly rather than
inherited: no duplicate GPIO (D-042), native and XGPIO documented distinctly
(D-045), no permanent raw `+3V3` (D-057), TPS22950C (D-058), native pair GPIO38 +
GPIO47 (D-063).

**New port: 2 rows × 12, 24 ACTIVE contacts, FEMALE on the device, male on the
accessory** (D-081). **10 XGPIO + 2 native + 2 I²C + 1 WAKE/ATTN + 2 switched
3.3 V + 2 switched 5 V + 4 GND + 1 `ACC_DETECT_N`** (D-082). Only the rails and
ground are duplicated, each a single net; **no GPIO is duplicated**. XGPIO falls
from 11 to 10, and **that one surrendered pin is exactly what pays for the fifth
accessory-control expander pin** — the arithmetic is tight to the pin.

### ~~Connector: Harwin `M20-7881242`~~ — **CORRECTED 2026-08-23, see FBV2-COMM-002**

> **This selection was WRONG and is superseded.** `M20-7881242` is obsolete and
> `harwin.com` returns HTTP 404 for it. The MPN had been configured from the
> catalogue ordering scheme rather than taken from a live listing — which the same
> entry's own limitations section had flagged. **The connector is now Samtec
> `BCS-112-S-D-HE`.** The reasoning below about *why keying must come from the
> enclosure at 2.54 mm* remains correct and still applies.

2.54 mm, 2×12, **female horizontal (right-angle) PC-tail socket**, through-hole
with two-point solder fixing, gold+tin. **3 A per contact, 300 mating cycles,
30 mΩ, 800 V AC proof, −40…+105 °C, UL94V-0.** Body ≈ 30.68 × 7.87 × 8.10 mm.
Mates with **any standard 2×12 0.64 mm square-post male header** (D-083).

A finding worth stating plainly: **at 2.54 mm there is effectively no mainstream
board-mount FEMALE connector with an integrated shroud and key.** The ubiquitous
shrouded, polarized 2.54 mm part is the *male* IDC box header, which is the wrong
gender. Samtec's Mini Mate `IPL1` is properly keyed, shrouded and latching — and
is a male box header whose mate is a Samtec part, so makers could not build
accessories from commodity components. 2.00 mm systems (Hirose DF11, Molex
Milli-Grid) do give a connector-side key and are ~20 % shorter, but they abandon
standard 2.54 mm male pins, which is the entire reason the pitch was chosen.

**So the key and the shroud come from the enclosure** — an asymmetric recess with
an off-centre lead-in rib, closed at both ends. That is explicitly permitted by
the ruling, it costs nothing in BOM, and it preserves the US$0.10 pin header as
the accessory interface.

### Pin ordering, and the mis-insertion proof

`1 XGPIO0 · 2 EXT_SCL · 3 ACC_3V3_SW · 4 GND · 5 XGPIO1 · 6 EXT_SDA ·
7 NATIVE_A · 8 XGPIO2 · 9 GND · 10 ACC_5V_SW · 11 NATIVE_B · 12 XGPIO3 ·
13 XGPIO4 · 14 WAKE_ATTN_N · 15 ACC_3V3_SW · 16 GND · 17 XGPIO5 · 18 XGPIO6 ·
19 XGPIO7 · 20 XGPIO8 · 21 GND · 22 ACC_5V_SW · 23 ACC_DETECT_N · 24 XGPIO9`
(D-084).

The ordering is not cosmetic. **Every power contact is vertically paired with
GND**, which is the constraint that forced power into columns 2, 5, 8 and 11 — so
**a row-swapped accessory can only ever produce a current-limited rail-to-ground
short, never 5 V on a logic pin.** All 3.3 V lives in row A and all 5 V in row B,
so a row-to-row bridge inside an accessory can short a rail to ground but never
5 V to 3.3 V. Both native fast pins flank the single GND at pin 9, which serves as
their return reference and separates them from each other. The I²C pair flanks the
GND at pin 4 for the same reason.

**The detect strap is one 0 Ω link between pins 21 and 23**, at the very end of the
row — the simplest accessory implementation possible. And because a flipped
accessory's strap lands in the other row, **a flipped accessory cannot assert
`ACC_DETECT_N`, so neither rail is ever enabled.** The mis-insertion case is
passively safe and self-announcing: the accessory simply does not come up.

A one-column lateral shift cannot be prevented electrically and is prevented
mechanically — the recess must be closed at both ends.

### Accessory detect

`ACC_DETECT_N` is pulled up to `+3V3` by AQROOT and grounded by the accessory
(D-085). Because the pull-up and the expander both run from `+3V3`, **detection
works with both accessory rails off**, which is the ordering the ruling demanded
and is what makes the flipped-accessory argument hold. **Neither rail may be
enabled unless detect is asserted.** As a free by-product, `U3`'s `/INT` is
wired-OR onto `WAKE_INT_N` → GPIO21, so **plugging or unplugging an accessory
raises an interrupt and can wake the device** at zero hardware cost.

### 3.3 V rail: TPS22950C confirmed line by line

`+3V3 → TPS22950C → ACC_3V3_SW` (D-086). Verified against SLVSFJ2B: `VIN`
1.8–5.5 V (so the same part works at 5 V too), **RCB = Yes** for the C variant,
`ILIM` **0.5–3.5 A** adjustable, auto-retry, TSD 170 °C, open-drain `FLT`, DDC
SOT-23-thin, 41 mΩ at 3.3 V, 550 µs slow turn-on so enabling the rail cannot step
`+3V3`. Default OFF with a **mandatory external 100 kΩ pull-down** — the internal
500 kΩ smart pull-down exists but the datasheet still says *"do not leave
floating"*.

### 5 V rail: a second TPS61023 and a second TPS22950C

`BQ25185_SYS → TPS61023 @ 5.0 V → TPS22950C → ACC_5V_SW` (D-087). **Not USB VBUS,
not the NFC fallback rail, tied to neither**; the only shared node is `SYS` on the
input side.

**Yes, reuse the TPS61023 — it is the right part, not merely the convenient one.**
0.5–5.5 V in, 2.2–5.5 V out, **3.7 A valley switch limit**, 94 % at 3.6 V → 5 V,
**true input-to-output disconnection in shutdown** at 0.1 µA, OVP, short-circuit
and thermal protection, SOT-563. Computed capability at 5 V is **≈ 2.3 A from a
3.0 V battery and ≈ 2.8 A from 3.6 V** — six to ten times what is being asked of
it. The limiter is the inductor, not the IC, so **1 µH with `I_sat` ≥ 3 A** is
specified (B-38). It shares its inductor, feedback divider and capacitors with the
DNP NFC fallback boost, so both circuits are one BOM line.

**Yes, use TPS22950C on both rails** (D-088). Same MPN, same footprint, same
safe-state pull-down, same `FLT` handling — **only `R_ILIM` differs**.

**Every back-feed path is closed**: accessory → boost (RCB, and constant reverse
blocking whenever `ON` is low, which is the default); `ACC_5V` → USB `VBUS`
(three series barriers — the switch's RCB, the boost's true disconnection, and the
BQ25185 power path); `ACC_5V` → `NFC_SUPPLY` (physically separate boost, separate
net, NFC on `+3V3` with its boost DNP on build 1).

### Why the published limits are below the CTO's targets on build 1

Recommended, **not fabrication-locked**: `R_ILIM` = **1.5 kΩ** on 3.3 V (≈ 0.76 A
typ) with a **published 400 mA continuous**, and **1.65 kΩ** on 5 V (≈ 0.69 A typ)
with a **published 300 mA continuous**.

Nothing about the switch or the connector prevents 800 mA — the TPS22950C is a
3.2 A part and the contacts are rated 3 A each. **The TPS63020 does.** The
TPS22950C is a *constant-current* limiter, so a shorted accessory holds `ILIM`
until thermal shutdown. Stacked on the internal worst case, `R_ILIM` = 1.15 kΩ
(600 mA published) drives `+3V3` to **101 % of the regulator's 2 A rating** —
foldback, brownout, SD corruption. At 1.5 kΩ the same fault reaches **86 %**. The
CTO's 600–800 mA target is met by changing one 0603 resistor once the internal
worst case is measured on real boards. That is D-049 applied exactly as intended.

**A structural advantage worth recording:** because the 5 V rail is boosted from
`SYS` rather than derived from `+3V3`, it consumes **none** of the TPS63020's 2 A
budget. Deriving it from `+3V3` would have cost roughly 500 mA of that budget.

### One honest caveat on fault visibility

SLVSFJ2B Table 9-1 is explicit: **`FLT` asserts on thermal shutdown and reverse
current only.** An output short leaves `FLT` **Hi-Z** while the device
current-limits. In practice a hard short dissipates 2.5–3.5 W in a SOT-23-thin
package and reaches the 170 °C TSD within tens of milliseconds, at which point
`FLT` does assert — but a **partial** overload that stays inside the thermal
envelope is invisible to the host. Firmware must not treat `FLT` as a complete
overcurrent indication (B-35). This is recorded because the ruling asked for
exactly this honesty rather than an invented fault output.

### Expander verdict: all five fit — exactly, with nothing left over

`U3` = **16/16**: `XGPIO0-9`, `ACC_3V3_EN`, `ACC_5V_EN`, `ACC_DETECT_N`,
`ACC_3V3_FAULT`, `ACC_5V_FAULT`, `SX1262_RXEN`. `U2` = **16/16**: the five pins
freed by removing HOME, the RGB LED and the RootProbe IRQ are exactly consumed by
`BQ25185_STAT1/2`, `MAX17048_ALRT_N`, `VBUS_PRESENT` and `SX1262_DIO1` (D-089).
Nothing was stolen — GPIO38 and GPIO47 remain the published natives, and SPI, I²S
and every internal MCU signal are untouched. One expander pin drives both the 5 V
boost `EN` and the 5 V switch `ON`.

**The design now has zero spare expander capacity anywhere (B-37).** That is the
price of fitting five accessory signals, and it is recorded as a standing
constraint rather than buried.

### Logic safety

**Every signal contact is 3.3 V CMOS. The 5 V power contact does not make any
signal 5 V-tolerant** (D-090). 100 Ω series on every XGPIO and both natives, 22 Ω
on the buffered I²C pair, 330 Ω on WAKE, plus a low-capacitance TVS array on the
two natives and the I²C pair — **the natives are the only contacts with a direct
path to the MCU**, and 5 V through 100 Ω is ≈ 11 mA into the clamp, inside
tolerance but with no sacrificial part in between. **Bidirectional level
translators are rejected**: they do not protect the A-side, they add direction
ambiguity on genuinely bidirectional GPIO, and they would imply 5 V logic is
supported, which it is not.

### B-08 closed with one MOSFET

A single N-channel pass gate between `WAKE_ATTN_N_HDR` and `WAKE_INT_N`, **gate
driven by `ACC_3V3_SW`** (D-091). The signal is only ever pulled low, so an N-FET
pass gate is sufficient. With accessory power off — the default — **a shorted
accessory pin can no longer hold `WAKE_INT_N` low, so internal button wake can
never be blocked.** Consequence, stated rather than hidden: accessory-initiated
wake now requires the rail to stay enabled during sleep (B-36).

### Power budget and the binding firmware contract

Naive simultaneity reaches **1 698 mA at `+3V3` = 85 % of the TPS63020's 2 A**
before transients — the P-15 concern, now quantified. With mutual exclusion
enforced the design case is **1 169 mA (58 %)**, or 1 314 mA (66 %) at the Wi-Fi
peak, and **1.65 A at the pack** (≈ 0.60 C on the 2 750 mAh class cell).

**MX-1…MX-9 are binding** (D-092): one high-power radio at a time; audio capped
during any transmit; rails detect-gated; 3.3 V enabled before 5 V by ≥ 5 ms; `FLT`
handled within 100 ms with a user action required rather than an endless
auto-retry into a short; both rails dropped on detect loss; 5 V disabled below
`V_BAT` 3.4 V and 3.3 V below 3.2 V; SPI-A arbitration; `U3` XGPIO interrupts
masked by default.

**A new thermal finding:** at 1.75 A the BQ25185 BATFET (115 mΩ) plus the
reverse-protection path costs **≈ 0.70 W and ≈ 0.40 V** inside a sealed
enclosure (B-34). BQ25185 supports 3.125 A discharge so the current is in spec,
but the loss and the `SYS` droop near a flat battery are real and are a further
argument for conservative first-build accessory limits.

### Mechanical: the connector region is now the governing Z column

2.0 shell + **8.10 connector** + 1.6 PCB + 8.0 battery + 0.6 + 2.0 shell =
**22.30 mm of the 23.0 mm external budget — 0.70 mm spare** (M-09). That displaces
the control region's 19.5 mm. Relief exists: the battery is 60 mm wide in a 75 mm
cavity, so the outer ~5 mm of each PCB edge has nothing behind it. The 8.10 mm
figure is read from the series catalogue and **must be re-confirmed against the
individual part drawing at FBV2-P1**. Insertion force reaches **48 N** (24 × 2.0 N
max) and must be carried by an enclosure boss, not by the PCB joints (M-10).

### Three opportunities flagged, deliberately not locked

**O-1** wire-OR the two `FLT` lines to recover one expander pin — slack versus
per-rail diagnostics, in a design that now has zero spare anywhere. **O-2** reserve
an I²C address for an accessory-ID EEPROM — zero hardware cost, but a
product/protocol decision that interacts with P-18. **O-3** a DNP 0 Ω link letting
the accessory boost also serve the NFC 5 V fallback — saves a part, but couples
NFC PA current to the accessory load, which is exactly what D-056 avoided. All
three need a CTO ruling.

Full analysis:
[`audits/2026-08-23-community-expansion-closeout.md`](audits/2026-08-23-community-expansion-closeout.md).

---

## 2026-08-23 — Display, connector and backlight LOCKED (FBV2-DISP-002)

Documentation only. No design file touched. `hardware/beta-v2/` was not created.

**FBV2-DISP-LOCK = PASS. M-06 CLOSED. M-07 CLOSED.** Sheet
`03_spi_a_display_sd` is unblocked, which removes the last gate on FBV2-S1.

**Display LOCKED: EastRising `ER-TFT035IPS-6` + `ER-TPC035-6`** (D-074) — 3.5″
IPS 320×480, **ILI9488** COG, **FocalTech FT6236** capacitive touch at **I²C
0x38**, assembled outline **56.54 × 84.96 × 3.95 ± 0.25 mm**, active
48.96 × 73.44 mm, 300 cd/m², 500:1, 80/80/80/80.

**FPC LOCKED (D-075): one 50-pin tail, 0.50 mm pitch, BOTTOM CONTACT,
0.30 ± 0.03 mm thick, 25.5 ± 0.15 mm wide, 30 ± 0.5 mm free length.** Display
*and* touch leave on that single tail — touch on pins 44–47. All three of the
parameters D-049 forbids guessing are printed in the vendor's own datasheet
(Rev 2.0, 18-Aug-2025). No second connector, no soldered flying lead.

**`J1` LOCKED: Hirose `FH69-50S-0.5SH`** (D-076). The compatibility argument is
the point: it is made from **both manufacturers' drawings**, not from a matching
pin count. The display tail is 0.30 ± 0.03 mm and the connector requires
0.30 ± 0.05 mm; the tail is bottom-contact and **FH69 accepts top *and* bottom
contacts** on a 2-point design. **The classic dead-first-article failure — an FPC
facing the wrong way — cannot occur with this pair.** Digi-Key: Active, 1,907 in
stock, US$2.16 @ 1, MOQ 1.

**`J1` is laid out on the FH12-horizontal / FH52E standard land pattern, not on
FH69's dedicated pattern** (D-077). Hirose states FH69 fits that pattern, and
doing so makes **`FH52E-50S-0.5SH` (LCSC `C7465440`, JLCPCB-orderable)** a genuine
drop-in second source with no board change. That is D-049 applied to a connector.

**D-073 is resolved, and the answer is that the connector was never the problem.**
As a by-product, `ER-TFT035-6` with CTP measures **56.54 × 84.96 mm** — the same
figures to 0.01 mm as Chenghao's `CH350HV40A-CT`, with the same active area and
the same 6-LED parallel backlight. The two are, to a high confidence, the same
glass from the same upstream supplier, and Chenghao's *"pin pitch 0.3 ~ 0.4 mm"*
is very likely a datasheet defect conflating tail thickness (0.3 mm) and conductor
width (0.35 mm) with pitch. **That is an inference, not a proof**, and Chenghao
stays rejected — a supplier that cannot state its own pitch cannot be designed
against. What it does retire is the fear that the *family* uses a sub-0.5 mm
pitch. It does not.

**ST7796S is formally rejected on availability, not on merit** (D-078). Eleven
suppliers were surveyed — Newhaven, Riverdi, EastRising, Winstar, Raystar, Focus
LCDs, DisplayModule, VIEWE, Chenghao and the hobby vendors. **No ST7796S / ST7796U
3.5″ 320×480 IPS module with a capacitive touch panel, a named touch controller
and a complete public FPC specification exists from a production supplier.**
ST7796S appears only on hobby breakouts (excluded by the brief), on touch-less
LCMs, or with ambiguous FPC data. Every candidate that meets the full requirement
set carries ILI9488. The cost is quantified: **+50 % SPI-A traffic; 46 ms
(21.7 fps) for a full 320×480 frame at 80 MHz FSPI IO_MUX against 31 ms for
ST7796S.** Accepted for menus, graphs, logs and status screens.

**Rejections, each on a recorded ground:** Riverdi `RVT35HITNWC00-B` — 59.56 ×
**93.34 × 5.66 mm** and a **10-LED, 14–16 V, 100 mA** backlight (~1.5 W). Focus
LCDs' IPS parts — **End of Life / NRND**, US$109 for 8 pcs. Focus `E35RG73248…-C`
— 61.90 × 91.04 mm and **two** connectors. Winstar `WF35UTYAIDNN0` and Raystar
`RFI350U-AYW-DNN` — excellent LCMs, **no touch variant**. Newhaven — current 3.5″
IPS is **640×480 MIPI DSI**, which the ESP32-S3 cannot drive. DisplayModule
`DM-TFT35-431` — ST7796S but **no documented touch controller**.

**Backlight closed (D-079). The TPS61169 stays, and for a structural reason:**
`U17` boosts from **`+3V3`**, not from the battery. A 6-LED *parallel* array sits
at only ~3.0–3.2 V, and a boost cannot regulate below its own input — had the
driver been fed from `VSYS` (3.0–4.35 V) this panel would have forced a buck-boost
or a linear sink. From a fixed 3.3 V, a modest ballast lifts the output to
~4.15 V and the converter stays firmly in boost at every corner.

New values: **`R69` (RSET) 2.55 R → 1.87 R ±1 %** → 109 mA typ, 100.5–117.6 mA
over the VREF band, always under the panel's 120 mA maximum. **`R70`–`R73`
4 × 39 R → 4 × 33 R, all in parallel on the single `LED_A` net** = 8.25 R, which
reuses the existing footprint group, quarters per-part dissipation to 24.6 mW and
leaves three DNP-able trim steps. Margins: **switch peak 263 mA against a 1.2 A
limit (4.6×)**; `L3` 12.5×; `D8` 2.1×; `C44` unchanged at 1.28× against the 39 V
OVP worst case. `L3`, `D8` and `C44` are all retained.

**The backlight is cheaper than FBV2-DISP-001 feared.** That audit assumed
6 × 20 mA and predicted roughly +50 %. The real panel is specified at **120 mA
maximum / 90 mA life point across six chips**, so per-LED current *falls* from
20 mA to 15 mA. At default brightness the pack sees **129 mA against Beta-DM's
118 mA — about +9 %** for 1.56× the screen area and 2× the pixels, and LED life
improves rather than degrades.

**Electrically the migration is free** (D-080). 4-wire SPI is selected by hard-tying
IM2/IM1/IM0 = 1/1/1 to VDDI, and the panel's SCK/MOSI/MISO/CS/DC/RESET land on the
existing GPIO12/11/13/10/14 and `U60 P04`; touch lands on the existing I²C bus with
the **same FT6236 at the same 0x38**, `TOUCH_RST_N` still on `U60 P00`. **Zero new
native GPIO. No new rail. No level shifting. No SPI bus merge.** B-10 is unaffected.

**One caution, mitigated by design:** the ILI9488's `SDO` behaviour on a bus shared
with microSD is not stated in the datasheet, and ILI9488 modules have a field
reputation for holding SDO driven. A **0 R `R_SDO` series link plus a test point**
lets the display be made write-only at bring-up without a respin, a trace cut or a
bodge (B-28).

**Mechanical PASS with margin.** 56.54 × 84.96 × **4.20 mm max** inside the
60 × 90 × 4.5 envelope; 9.23 mm of cavity each side; **70.04 mm** of the 155 mm
cavity height left for the D-pad, A/B and the mic aperture; front stack 7.30 mm
plus the 8.0 mm battery = 15.30 mm of the 18.5 mm cavity, **3.20 mm spare**. The
6 mm FPC bend corridor is retained and is generous against the ≥3 mm a 0.30 mm
tail needs. **One new placement coupling:** at 2.3 mm the connector cannot sit in
the display shadow (0.8 mm limit), so it competes for the space below the panel
(B-33 / M-08).

**Procurement risk LOW**, with two MEDIUM items that are closed on the purchase
order rather than in the design: the vendor also sells a **CST340** touch panel
for this size, so the PO must name `ER-TPC035-6`; and the datasheet carries a
**"Backlight Update" revision**, so Rev 2.0 must be archived in-repo and cited by
revision in the MPN ledger. Against that, EastRising publishes a written
**≥10-year continuity-supply commitment** — the only candidate in the survey that
does — at **MOQ 1**, in stock, **US$15.57 per display in prototype quantity**.

Full analysis:
[`audits/2026-08-23-display-procurement-lock.md`](audits/2026-08-23-display-procurement-lock.md).

---

## 2026-08-22 — Display size ruled 3.5″; MPN deliberately not locked (FBV2-DISP-001)

Documentation only. No design file touched.

**Battery envelope LOCKED** at 60 × 75 × 8.0 mm, ~2500–3000 mAh (D-071).
**Display size LOCKED at 3.5 inch** (D-072). **Display MPN and J1 are deliberately
NOT locked** (D-073), and the reasoning matters more than the conclusion.

**Was the old J1 ever compatible? UNPROVEN — not YES, not NO.** No source
obtainable to this audit states the CH280QV10-CT's FPC pitch, and the Phase-1
mechanical audit independently recorded the same gap. **J1 was selected without a
display FPC drawing on file and has never been proven to mate.** Its footprint is
verified against the *Hirose* drawing, which proves the connector footprint is
right and proves nothing about the display. The CTO's suspicion is strengthened by
the successor part in the same family quoting **0.3–0.4 mm**, not 0.5 mm — if that
is the family convention, the 2.8″ part may never have mated either.

**The 3.5″ candidate CH350HV40A-CT was verified and it fits** — 320×480 IPS,
ILI9488, 56.54 × 84.96 × 3.97 mm, active 48.96 × 73.44 mm, 50-pin, 6-LED parallel
backlight. It clears the ≤60 × 90 × 4.5 mm envelope and leaves 70 mm of the
155 mm cavity height for the controls. **Four defects stop it being locked:**
ILI9488 **cannot send RGB565 over SPI** and takes 3 bytes/pixel, a 1.5× bandwidth
penalty an ST7796S-class part simply does not have; the vendor states **"pin pitch
0.3 ~ 0.4 mm"**, a *range*, which directly violates D-049's *"no dependence on
undocumented pin pitch"*; module thickness is quoted as both 3.97 and 2.4 mm in the
same document; and the touch controller is never named.

**What is locked instead is the interface requirement** — 3.5″ IPS 320×480,
ST7796S/ST7796U preferred, I²C CTP of the FT6336U class, single documented FPC
pitch with 0.5 mm strongly preferred. **The mating connector cannot be chosen
until the panel's pitch, pin count and contact side are confirmed**; choosing one
now would repeat the exact mistake this audit found.

**ESP32-S3 SPI verdict: PASS, with no bus merge and no radio change.** The panel
touches only SPI-A; SPI-B keeps the radios and NFC. Usefully, `SPI_A_MOSI`/`SCK`/
`MISO` sit on GPIO11/12/13 and `DISP_CS` on GPIO10 — exactly the ESP32-S3 **FSPI
IO_MUX** pins, so the display bus already has the 80 MHz fast path rather than the
40 MHz matrix route. At 80 MHz an ST7796S-class controller writes a full 320×480
RGB565 frame in ~31 ms, the same as today's 2.8″ panel at 40 MHz — **the user
experience does not regress.** With ILI9488 it is ~46 ms instead.

**Backlight rises from 4 LEDs to 6 (+50 %)**, taking browsing draw from ~100 mA to
~130 mA — but D-071's larger pack takes capacity from 2000 mAh to ~2750 mAh, so
**runtime is flat to slightly better.** Neither ruling alone would have achieved
that. The TPS61169 `RSET` (2.55R) and its current capability must be re-derived for
six LEDs (M-07).

M-01 and M-02 closed. **M-06** (display MPN / FPC) and **M-07** opened. FBV2-A2
stays PASS. **No gate passed, so the percentage holds at 25 %.**

---

## 2026-08-22 — Mechanical interfaces frozen; **FBV2-A2 PASSED** (FBV2-MECH-001)

Documentation only. No design file touched. `hardware/beta/mechanical/` was read
only and is unmodified.

**FBV2-A2 = PASS.** Three of twelve gates now pass. New authoritative pre-CAD
source: `mechanical/MECHANICAL_INTERFACE_SPEC.md`, with every row marked LOCKED,
TARGET or TBD — and **nothing marked LOCKED on the strength of derivation alone.**

**Device orientation was resolved, not assumed.** The Beta-DM board is 74 × 155
(portrait) and the external target is 80 × 160; the axes map one to one. The
device is portrait, so the front is display-above-controls.

**23 mm passes with 3.5 mm spare**, and the interesting question was what to do
with the margin. The governing column is the control region with the battery
behind it: 19.5 mm of 23.0 mm. Left as air the margin is wasted; allocated to the
battery it raises the pack from the 5–6 mm a 2000 mAh cell needs to **8.0 mm**,
i.e. the **2500–3000 mAh class** — a 25–50% runtime gain for zero external size
change.

**The Beta-DM outline cannot be reused, and the reason is stark.** Against the
derived 75 × 155 mm cavity, the 74 × 155 mm board leaves 1.0 mm of clearance in X
and **zero in Y**. There is no room for the shell lip, six bosses, ribs or
assembly access. Combined with the v2 content changes — 20-pin connector, P2
four-FET stage, dead-cell recovery branch, NFC crystal and matching, restored IR,
new expanders — the verdict is **re-floorplan with a different outline**, targeting
**70 × 148 mm**. This is the PCB revision Field Slate v3 required in July and never
received.

**NFC and battery are separated in plan rather than stacked.** Because the display
occupies the front upper third, the rear upper third is free — NFC loop there
(45 × 45 mm), battery in the rear lower two-thirds. **Zero overlap is the policy,
not a mitigation.** Ferrite is still specified, because once the battery moves away
the PCB ground pour becomes the dominant near-field threat. The loop grows from
Beta-DM's measured 26 × 20 mm to 45 × 45 mm — a **3.9× area increase**, which is
where the range lost to 3.3 V NFC operation (D-055) is won back. Two constraints
fall out: the mid-span bosses and the left-side antenna storage channel must both
stay below Y = 100 mm.

**Acoustics and IR specified to interface level.** The ICS-43434 is bottom-port, so
the mic path is PCB hole → gasket → shell aperture with the tunnel ≤2.5 mm; longer
tunnels roll off exactly the frequencies that carry speech. Speaker rear-firing,
Ø20 × 4 mm, with a 1.5–2.0 cm³ **sealed** rear cavity, ≥60 mm from the mic and on
the opposite face. IR emitter and receiver ≥15 mm apart on the top edge with a
**mandatory opaque barrier** — separation alone does not fix self-blinding,
because the internal reflection path is the one that actually causes it.

**Honest limits recorded rather than glossed:** nothing is CAD-verified, several
component figures are class-typical, and the display is the weakest input — its
50 × 69 mm figure is a measured *keepout*, not a vendor outline, and the FPC bend
stack is unknown. That is why display size is raised as an open item.

Two CTO decisions opened: **M-01 display size** (the cavity comfortably accepts
3.2″ or 3.5″; blocks PCB floorplanning but not schematic migration) and **M-02
battery capacity target**. **P-07 closed.**

Progress 20% → 25%. Next gate: **FBV2-S1, schematic migration.**

---

## 2026-08-22 — Battery safety architecture finalised; **FBV2-A1 PASSED** (FBV2-PWR-002)

Documentation only. No design file touched.

**FBV2-A1 = PASS** — the first gate to pass since FBV2-A0, and the largest
remaining architecture unknown. All six criteria closed, all 13 power/fault cases
defined, no power-tree branch TBD. Next gate: **FBV2-A2, mechanical interface
freeze.**

**Candidate B selected and specified to component level** (D-065). The design
turns on one structural fact: **no passive switch can distinguish a 0 V cell from
a reversed one** — an N-FET referenced to a positive rail sees V_GS ≈ +3 V at 0 V
and ≈ +6.7 V at −3.7 V, so a reversed cell turns it *harder on*; the P-FET
arrangement fails the same way. An active, GND-referenced comparison is therefore
mandatory. The chosen sensing network is a **matched ratiometric bridge** whose
trip condition reduces to **V_BAT = 0 independent of VBUS** — supply-independence
by construction rather than by trimming. Handoff is taken from the **LTC4368
`FAULT` pin**, which is asserted precisely while VIN is below UVLO, so the
protection controller itself decides when it has taken over — no extra threshold,
no possibility of both paths being active. Recovery current **5–10 mA** (~0.004 C),
supplied from **VBUS rather than SYS** so the branch is dead by construction
without USB and costs **zero battery-side standby**.

**The pass path changes to P2** — two back-to-back stages in **two separate
packages**. A precise finding corrected the earlier account: **P1 fails one of the
two single-FET-short cases, not both.** A short on the `BAT_RAW`-side FET is
already blocked by its partner; it is specifically the **`BAT_PROT`-side** FET
whose short lets a reversed cell through. P2 leaves one complete back-to-back pair
intact under any single short, and additionally keeps the LTC4368's electronic
breaker functional with a FET shorted. Two die sharing one leadframe cannot be
called independent, so the two stages must not share a package.

**The previous fuse-and-clamp compliance argument is withdrawn as invalid.** A
Schottky sitting at ≈0.8–1.0 V does not protect a −0.3 V absolute maximum, and
ruling D was right to refuse it. With isolation doing the work, the **clamp is
demoted to secondary** duty (ESD, transient, double-fault) and the **fuse is
resized 3 A → ≈5 A**, because it is now a backstop that must not pre-empt the
3.33 A electronic breaker. Its one genuinely irreplaceable role is a harness short
between `BAT_RAW` and GND *upstream* of the FETs, where the breaker cannot act.
**PTC remains rejected.**

**Honest residual, recorded rather than smoothed over:** Candidate B is *not*
tolerant to every single failure — four failures each individually enable current
into a reversed cell. It meets the requirement as written because `R_LIM` bounds
every one to **≈13 mA (~0.007 C)**, `D_REC` keeps the branch unidirectional under
all faults, and the condition is self-annunciating. A fully redundant variation is
documented and **not** recommended: it would trade that bounded residual for a
permanent oscillation in the far more common battery-absent state.

**PCAL9535APW,118 locked for both expanders** (D-066), closing the four facts the
previous audit could not verify. **GPIO38 + GPIO47 remain locked** (D-067).

Progress 15% → 20%, held deliberately low: two of twelve gates, both paper, with
mechanical untouched.

---

## 2026-08-22 — Power architecture closed to a single open decision (FBV2-PWR-001)

Documentation only. No design file touched.

**Expander family locked** (D-061): both `U2` and `U3` become NXP
`PCAL9535APW,118` (LCSC C2669683) — an architecture lock, with the land-pattern
audit still required before fabrication. **Native pair locked** (D-063):
`NATIVE_A` = GPIO38, `NATIVE_B` = GPIO47, with `SX1262_DIO1` moving to the
internal expander and `BUSY` staying native. GPIO43 leaves the public connector.

**The SX1262 lock condition was met from a primary source.** Semtech
`DS.SX1261-2.W.APP` Rev. 1.2 §13.3.4 states verbatim that a DIO mapped to one IRQ
clears when that flag clears, and that with several IRQs mapped *"the DIO remains
set to one until all bits mapped to the DIO in the IRQ register are cleared."*
DIO1 is level-held, so an expander input with no capture register can service it.

**Two prior positions were corrected by the full LTC4368 datasheet.** P-13 is
**closed**: inrush is a designed parameter, `I_INRUSH = (C_OUT/C_GATE) ×
I_GATE(UP)`, giving ≈350 mA against a 3.33 A trip — and RETRY latch-off applies
to *forward* overcurrent only, while reverse faults reconnect automatically once
VOUT falls 100 mV below VIN. The earlier concern rested on an incomplete reading.

**The fuse-and-clamp language correction (D-064) was justified, and the analysis
vindicates it.** At the 20–25 A a 1S pack can deliver, a Schottky clamp sits at
≈0.8–1.0 V — about **3× the BQ25185 `BAT` −0.3 V absolute maximum**. The clamp
improves the excursion roughly fourfold but does **not** bring it inside the
limit. Both elements remain **REQUIRED** — the fuse because without it the clamp
is a permanent short across a Li-ion cell — but the residual is now named (P-12)
rather than assumed away. A **PTC is rejected** for this position: too slow, and
its auto-retry re-applies the fault every cycle.

**Dead-cell recovery is now the only thing blocking FBV2-A1.** The LTC4368 cannot
help here — VIN is the supply pin with a 2.2 V UVLO, and VOUT is a sense input
whose charge-pump role only engages above ~5 V, so system-side power cannot run
the controller. A single MOSFET also cannot distinguish a 0 V cell from a
reversed one: **both turn it more on**, so an explicit GND-referenced sensing
element is mandatory. Four candidates analysed; **Candidate B** — a
hardware-qualified comparator interlock, no firmware dependency, ~0 A into a
reversed cell — is recommended for the product, with service-only accepted as
defensible for the first five boards. **Not approved, so the gate is not passed.**

Progress 13% → 15%. **FBV2-A1 FAIL, 5 of 6 criteria closed.**

---

## 2026-08-22 — Critical architecture reconciled; no-respin policy established (FBV2-ARCH-002)

Documentation only. No design file touched.

**New standing policy: FIRST FIVE FULL BETA PCBAs — NO-RESPIN RECOVERY POLICY
(D-049).** Full Beta v2 Revision 1 must be designed so that reasonable
configuration and performance uncertainty is recoverable through *planned*
component rework — DNP/FIT options, 0 Ω source-selection links, accessible tuning
passives, test points — rather than through a board respin. Safety-critical power
paths are explicitly excluded: no ad-hoc bypasses around battery protection
merely for reworkability.

**An independent second-opinion review was archived verbatim** at
`reviews/2026-08-22-independent-cto-power-nfc-review.md`, marked
**ADVISORY — NOT AUTOMATICALLY AUTHORITATIVE**. It corrected the primary
engineering work on three points, and the corrections were accepted:

- **Discrete back-to-back N-FET reverse protection is withdrawn.** It is not
  under-specified but *unrealisable at 1S* — available V<sub>GS</sub> from any rail
  on this board is 0.3–1.5 V, and the P-channel variant that avoids a charge pump
  turns both FETs hard on into a reversed cell, creating the fault it was added to
  prevent. **LTC4368-1 adopted** (the `-2`'s −3 mV reverse trip would block
  charging outright).
- **"STAT1 only" was wrong, and so was the premise behind it.** BQ25185 SLUSF65A
  §7.3.10 places the STAT2 toggle in the **battery-absent** limit cycle, not in
  charge-complete/sleep — those are one state with both pins HIGH. STAT1 alone
  conveys only fault/no-fault. **Both are exposed**, with the wake-storm solved by
  changing the expander rather than by dropping a signal.
- **TPS22913B/C was the wrong replacement** for TPS22918 — DSBGA 0.9 × 0.9 mm only,
  and no current limit. **TPS22950C** adopted: RCB confirmed for the C variant
  (the L variant has none), leaded SOT-23-thin, adjustable limit, thermal
  shutdown.

**Verified this pass.** The TPS61169 `CTRL` pin has an internal **pull-down**,
which closes the last blocking condition on moving `DISP_BL_CTL` to GPIO46 and
frees GPIO47. **GPIO38 replaces GPIO43** as `NATIVE_A`, removing ROM-UART
push-pull contention from the public connector entirely.

**The mandatory power/fault state table now exists** — eleven cases across USB,
battery, power-switch and accessory states. Cases 1, 2, 5, 6, 8, 9 and 10 are OK
or correctly blocked. **Case 4 (dead cell) and Case 11 (hot insertion) are
UNRESOLVED and block schematic lock**, and Case 7 (shorted pass FET + reversed
cell) is only survivable with a series fuse and a Schottky clamp, which are
therefore required rather than optional.

**NFC ships at 3.3 V with a full no-respin 5 V fallback.** Two mutually exclusive
0 Ω links guarantee the sources can never be shorted. Pre-fit the inductor, the
FB divider and both boost capacitors; keep the TPS61023 and the 5 V link DNP.
Conversion is 3–9 soldering operations with exactly one fine-pitch part — no BGA
or QFN rework, no trace cuts, no bodge wires.

**Volume Up/Down removed from the Full Beta v2 mechanical requirements.**

**FBV2-A1 assessed: CANNOT PASS.** Four of eight criteria are resolved (20-pin
map, default NFC, NFC fallback, accessory power). Four remain — expander family,
native pair, reverse-protection topology completeness, and power-tree stability —
and three of those close with document reads. Progress 10% → 13%.

---

## 2026-08-22 — Architecture direction locked, blockers verified (FBV2-ARCH-001)

Documentation only. No design file touched. Commit `890db0b` pushed to
`origin/master` (`b8b5ebd..890db0b`).

**CTO rulings A–K recorded** as D-018, D-026, D-033…D-041, D-046…D-048. Four
pending decisions closed: P-05 (RGB removed), P-06 (RootProbe IRQ retired),
P-08 (IPEX → pigtail → bulkhead), P-09 (LoRa deep-sleep wake not required).

**Verification against vendor datasheets changed three things.**

- **The NFC supply split cannot be built.** ST25R3916 DS12484 Rev 3 p. 39: *"VDD
  and VDD_TX must be connected to the same power supply"*, with the difference
  capped at ±0.3 V absolute maximum. The requested 3.3 V / 5 V split would apply
  1.7 V across that pair. **The as-built rail assignment is correct**, and the
  pre-design audit's recommendation to change it was wrong and is withdrawn. The
  real residual question — what VDD does while the boost is off — is now P-10,
  with a 3.3 V-only NFC option that would delete eight components.
- **The proposed native-GPIO reclaim would have broken recovery.** Moving
  `NFC_IRQ` to GPIO46 makes ROM download boot conditional on NFC interrupt state,
  because the ST25R3916 IRQ is active-high, latches until read over SPI, and is
  not reset by an ESP32 reset. Substituted: move `DISP_BL_CTL` to GPIO46 and
  expose **GPIO47** as `NATIVE_B`. GPIO47 is strictly better — no power-up glitch,
  20 mA drive, unrestricted priority — and D-041 removed the only reason to want
  GPIO18's RTC capability.
- **`TPS22918` fails the accessory-isolation requirement.** Its integrated body
  diode conducts VOUT→VIN, so a powered accessory can back-power `+3V3`.
  Replacement identified in the TPS22913B/C class.

**Two prior findings were confirmed wrong and are corrected in the record:** the
TCA9517A *does* guarantee high-impedance pins when powered off and 5.5 V
tolerance while unpowered, so it passes; and the TPS61023 *does* provide true
load disconnect plus integrated output OVP.

Reverse-polarity architecture compared across three candidates and **discrete
back-to-back N-FETs recommended** over the LTC4368-1, primarily on quiescent
current (sub-µA vs ~80 µA) — flagged for independent second opinion as
instructed. A reverse-current-blocking load switch was evaluated and
**disqualified for this position**: it would block the charging direction.

Progress raised 8% → 10%. **No gate passed.** FBV2-A1 remains IN PROGRESS with
P-01, P-02, P-04, P-07 and P-10 open. **FBV2-A2 (mechanical interface freeze)
recommended as the next gate** — it is the long pole and nothing blocks it.

---

## 2026-08-22 — Full Beta v2 engineering record established (FBV2-DOC-001)

Documentation infrastructure only. No design file was touched.

- Created `docs/full-beta-v2/` as the authoritative engineering record.
- Established the precedence rule: `CTO_DECISIONS.md` outranks audits, which
  outrank architecture notes, which outrank transcripts.
- Made `transcripts/` append-only.
- Preserved the 2026-08-22 pre-design engineering audit verbatim under
  `audits/`, pinned to repository HEAD `b8b5ebd`.
- Preserved the FBV2-AUDIT-001 CTO prompt and Claude Code response verbatim
  under `transcripts/`.
- Opened the gate table FBV2-A0 through FBV2-B3 and recorded FBV2-A0 as PASS.

---

## 2026-08-22 — Full Beta v2 direction established

- **Beta-DM fabrication paused before payment.** The design-side release stands
  and no money has been committed. Beta-DM is retained as the preserved fallback
  and manufacturing baseline, not cancelled.
- **Full Beta v2 made the primary design.**
- **Decided not to blindly continue frozen Full Beta.** Its freeze recorded 281
  unconnected items and 58 ERC violations; it is a feature reference, not a
  fabrication-ready baseline. Its decisions are re-verified rather than
  inherited.
- **Beta-DM becomes the implementation / manufacturing baseline.** Full Beta v2
  is derived from it — its resolved MPNs, its validated blocks, its routing and
  DFM lessons.
- **Removed HOME from the future product.**
- **Volume Up / Down removed from the enclosure plan.** Audit finding: they
  never existed electrically. `SW2`-`SW8` are UP / DOWN / LEFT / RIGHT / A / B /
  HOME. Volume controls existed only in Field Slate v5 section 5, which must be
  corrected so enclosure CAD is not driven by phantom controls.
- **Physical BOOT retained but hidden/recessed.** It remains the last-resort
  recovery path when flash is blank or hard-bricked.
- **Software recovery required in addition to physical recovery**, with ROM
  download mode and firmware/OTA recovery held explicitly distinct — they fail
  in different situations and must never be conflated in UI copy.
- **Microphone retained** (ICS-43434 I2S MEMS, carried forward unchanged).
- **Speech output retained.** Not downgraded to a buzzer. MAX98357A-style I2S
  Class-D remains the leading architecture; the audit found no materially
  simpler option, because the ESP32-S3 has no DAC.
- **IR retained internally** — not removed, not moved to an accessory.
- **Community expansion target changed from 26 pins to 20 pins**, with a future
  requirement that the connector be keyed, shrouded/polarized and recessed.
- **External I2C retained**, pending validation of its protection, buffering and
  backfeed behaviour before architecture lock.
- **First Full Beta v2 pre-design audit completed** — read-only, pinned to
  repository HEAD `b8b5ebd`, zero repository changes. It established the
  measured GPIO budget (zero free native pins), three candidate 20-pin connector
  architectures, and the blocker set B-01 through B-16 now tracked in
  [PROGRESS.md](PROGRESS.md).
## 2026-08-29 - OWNER DECISION D-293: direction-2 LTC4368-block spread / escape-target relocation approved

Alpha ratified the D-292 CTO recommendation at 22:34 UTC: authorize a bounded LTC4368-block spread and/or minimum escape-target relocation (R77/R79 east, R80/R81 north as engineering evidence dictates) so `BAT_RAW` and `BAT_PROTECTED_P` escape through different corridors. The 0.300 mm D-269 current-path clearance and every other locked safety/routing/manufacturing floor remain mandatory; U18.8-open acceptance is prohibited; D-290 is not re-authorized or re-litigated. No engineering result, promotion, progress, or readiness increase is claimed by this decision record. **NEXT: FBV2-P2-003T** from clean pushed `b4f950b`: bounded direction-2 candidate screen followed by a full authority integration gate for the first legal candidate.
## 2026-08-31 - FBV2-P2-029: D-327 — west-button expander escape characterized; no copper change

GPT completed the first direct-hardware transition task. `BTN_DOWN_N`, `BTN_RIGHT_N`, and `BTN_A_N` were scratch-routed under the accepted duplicate-pad framework; all three were rejected because the short B.Cu pull-up-to-expander edge has no legal 0.200 mm escape. The authoritative D-326 board remains byte-identical (`adbea36b…`, 821 tracks / 71 vias / ratsnest 659 / journal 122). Regression G1–G38 passed twice, all incremental/Phase-B probes passed, and independent DRC was unchanged. Next: one bounded generic expander-endpoint escape improvement, then promote the first west button only on a full gate PASS. No owner decision; readiness remains 78. Full evidence: [`audits/2026-08-31-p2-029-d327-west-button-expander-escape-characterization-no-promote.md`](audits/2026-08-31-p2-029-d327-west-button-expander-escape-characterization-no-promote.md).

## 2026-08-31 - FBV2-P2-030: D-328 — BTN_RIGHT_N hop-anchor route promoted

GPT completed the primary-hardware-engineer transition acceptance test without Claude. A bounded opt-in hop-anchor plan joined the boxed `R7.2`/`U2.16` endpoint regions through two ordinary vias and F.Cu, then attached both `SW5.1` lands to the owned via anchor. The full gate passed with no casualty and no DRC delta. Promoted state: `27db293c…`, 837 tracks / 73 vias / ratsnest 656 / journal 125. Regression G1–G39 passed twice; probes 006–026, Phase-B, and standalone DRC passed. No product, rule, placement, schematic, BOM, or topology change. Readiness remains 78. Full evidence: [`audits/2026-08-31-p2-030-d328-btn-right-hop-anchor-promoted.md`](audits/2026-08-31-p2-030-d328-btn-right-hop-anchor-promoted.md).
## 2026-08-31 - FBV2-P2-033: D-331 — In2/In3 long-haul framework accepted; XGPIO2 promoted

GPT implemented the reusable low-speed inner-layer haul: short native-face escapes, two standard vias, and a long In2/In3 signal run. The `XGPIO2` pilot passed the unchanged full-board gate and was promoted (`98181354…`, 845 tracks / 75 vias / ratsnest 655 / journal 126). G1–G41 passed twice, all probes and independent DRC passed unchanged. Next: fast-screen and batch-route `XGPIO4/5/6/7` through the accepted framework. Full evidence: [`audits/2026-08-31-p2-033-d331-in2-long-haul-framework-xgpio2-promoted.md`](audits/2026-08-31-p2-033-d331-in2-long-haul-framework-xgpio2-promoted.md).
## 2026-08-31 - FBV2-P2-034: D-332 — XGPIO4/XGPIO5 inner-layer batch promoted

Routine D-331 framework reuse: the coherent `XGPIO4` + `XGPIO5` batch passed the unchanged full-board gate and is authoritative at `e5e6f4fc…`, 856 tracks / 79 vias / ratsnest 653 / journal 128. G1–G42, focused probes 023–027, Phase-B (32/164 routed), and independent DRC all pass; no new clearance class. Compact evidence is in `routing_ledger.json`. Next: fast-screen XGPIO6/XGPIO7 for a second inner-haul batch, then move to the generic boxed-endpoint framework.
## 2026-08-31 - FBV2-P2-035: D-333 — final XGPIO pair bounded at endpoint via-site wall (no copper change)

The accepted inner-layer long-haul framework was fast-screened on XGPIO6/XGPIO7. Each failed at a different endpoint because no legal reachable locked-size via site exists; neither reached the long-haul stage. Authoritative D-332 copper is byte-identical and the wall registry now directs both nets to the generic boxed-endpoint framework. Full evidence: [`audits/2026-08-31-p2-035-d333-xgpio6-xgpio7-inner-haul-endpoint-wall.md`](audits/2026-08-31-p2-035-d333-xgpio6-xgpio7-inner-haul-endpoint-wall.md).
## 2026-08-31 - FBV2-P2-036: D-334 — MCU EN same-face boxed-anchor pilot bounded

A bounded generic prototype successfully staged `U1.3` toward explicit F.Cu anchors, but none opened a legal 0.200 mm path to `C1.2`; the prototype was removed rather than retained as dead routing logic. No authoritative copper changed. Fresh regression, focused probes, Phase-B and KiCad DRC reconfirm D-332 unchanged with zero clearance class. Next is a layer-changing/owned-copper endpoint framework for the coherent west-button family. Full evidence: [`audits/2026-08-31-p2-036-d334-mcu-en-boxed-anchor-screen.md`](audits/2026-08-31-p2-036-d334-mcu-en-boxed-anchor-screen.md).
## 2026-08-31 - FBV2-P2-037: D-335 — west-button owned-anchor framework bounded

The bounded layer-changing/owned-copper prototype failed at the boxed pull-up staging step for both `BTN_DOWN_N` and `BTN_A_N`; no scratch route reached promotion and the prototype was removed. D-332 copper and the full validation histogram remain unchanged. Framework-first non-placement mechanisms are now bounded for this family; next is a reversible pull-up placement ECO screen. Full evidence: [`audits/2026-08-31-p2-037-d335-west-button-owned-anchor-screen.md`](audits/2026-08-31-p2-037-d335-west-button-owned-anchor-screen.md).
## 2026-09-01 - FBV2-P2-038: D-336 — west-button single-pull-up placement screen bounded

The recovered scratch harness completed 72 cardinality-1 R5/R8/R6 placement candidates. Courtyard conflicts reject most moves and every legal ±0.5/1.0 mm/native/180° candidate remains unroutable. No placement or copper was promoted; D-332 and all validation evidence remain unchanged. Next is a bounded coordinated pull-up-column spread. Full evidence: [`audits/2026-09-01-p2-038-d336-west-button-cardinality1-placement-screen.md`](audits/2026-09-01-p2-038-d336-west-button-cardinality1-placement-screen.md).

## 2026-09-01 - FBV2-P2-039: D-337 — coordinated pull-up-column spread bounded

Eight legal cardinality-3 R5/R8/R6 layouts produced no complete west-button route in 24 attempts. The fixed U2/pull-up cluster, not independent pull-up spacing, is now the bounded wall. No placement or copper was promoted; D-332 and all validation evidence remain unchanged. Next is the bounded J1 display-fanout framework, with a larger U2 cluster ECO retained as fallback. Full evidence: [`audits/2026-09-01-p2-039-d337-west-button-coordinated-column-spread.md`](audits/2026-09-01-p2-039-d337-west-button-coordinated-column-spread.md).
## 2026-09-01 - FBV2-P2-052: D-350 — exact U20 eight-item scope bounded

The minimum collision scope was replayed in scratch. Frozen copper and control connectivity were preserved, but the fault net remains unroutable and real DRC finds two dangling retained stubs. Nothing was promoted; board `2cdc9f33…` is unchanged. Next: expand only affected control branches to stable anchors.
