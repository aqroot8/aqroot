# FBV2-P2-015 / D-313 — Tenth rest-of-board incremental increment ROUTED + PROMOTED: XGPIO east-edge pilot `XGPIO8`+`XGPIO9` (first XGPIO bank members), after a full read-only XGPIO0..9 corridor study

**Date:** 2026-08-30
**Decision:** D-313 (governed CTO ACCEPT + PROMOTE; routine rest-of-board routing within CTO authority — no owner decision)
**Starting HEAD:** `1eb80a912abd6db11924a4bc7c1fee4f1202b6f2` (D-312; pushed; `origin/master` identical)
**Pre-promotion PCB:** `sha256 d6e0148a43a42895236b934cb6f7084036e50535a399f42fe09b300aabc5f1b8` — 608 tracks / 62 vias / 6 layers / 41 zones / ratsnest 681 / journal 100
**Promoted PCB:** `sha256 a0d6fead125295441dda0f0008c1261f5c1cec39edb2b8c7bd925b214e7207eb` — **631 tracks / 64 vias / 6 layers / 41 zones / ratsnest 679 / journal 102**

## Summary

FBV2-P2-015 was an **evidence-first** task: FIRST a faithful read-only corridor study of all ten `/XGPIO0..9` nets on the live routed board, THEN — only if the study found a credible pilot — a small coherent adjacent subset routed member-by-member on scratch and gated. The study found a credible pilot; the **east-edge pair `XGPIO8` (R59.1 F.Cu → U3.13 B.Cu) + `XGPIO9` (R60.1 F.Cu → U3.14 B.Cu)** — two adjacent community-header GPIO nets on consecutive U3 PCAL9535A pins — was routed and promoted. This is the FIRST XGPIO bank member(s) and the tenth rest-of-board increment.

Each `/XGPIOx` is a 2-pad **cross-layer** net: the 100 R community-header series resistor R5x.1 on F.Cu (top pack, y≈17–36) → the PCAL9535A U3 expander pin on B.Cu (mid-board, y≈74–80). One MST edge, one F↔B through via each — structurally the U2 escape family, but the U3 escape goes **NORTH into open board**, away from the completed U2 via cluster (y≈82–92).

## A — READ-ONLY corridor study (`w/xgpio_study_015.py`, authoritative untouched)

The study reproduced, on the live D-312 board, the exact `incremental_router` escape/via-site machinery for all ten nets and measured endpoints/layers/span, U3 escape feasibility, default+offset via sites with faithful clearance to every existing barrel (copper + hole), corridor congestion, adjacency, and cross-net via spacing. Full bank table (`w/xgpio_study_015.json`):

| net | R (F.Cu) | U3 pin (B.Cu) | edge | span mm | bbox cu / via | default via | min via-clr to existing |
|---|---|---|---|---|---|---|---|
| XGPIO0 | R51.1 | U3.4 (54.14,79.63) | WEST | 60.29 | 20 / 0 | (55.3,79.6) | 3.14 mm (SD_DETECT) |
| XGPIO1 | R52.1 | U3.5 (54.14,78.98) | WEST | 54.97 | 18 / 0 | (55.3,79.0) | 3.63 mm |
| XGPIO2 | R53.1 | U3.6 (54.14,78.33) | WEST | 51.94 | 17 / 0 | (55.3,78.3) | 4.23 mm |
| XGPIO3 | R54.1 | U3.7 (54.14,77.68) | WEST | 48.88 | 18 / 0 | (55.3,77.7) | 4.77 mm |
| XGPIO4 | R55.1 | U3.8 (54.14,77.03) | WEST | 55.52 | 18 / 0 | (55.3,77.0) | 5.41 mm |
| XGPIO5 | R56.1 | U3.9 (54.14,76.38) | WEST | 45.54 | 17 / 0 | (55.3,76.4) | 5.97 mm |
| XGPIO6 | R57.1 | U3.10 (54.14,75.73) | WEST | 39.84 | 20 / 0 | (55.5,76.05) | 6.36 mm |
| XGPIO7 | R58.1 | U3.11 (54.14,75.08) | WEST | 58.20 | 20 / 0 | (55.5,76.05) | 6.36 mm |
| XGPIO8 | R59.1 | U3.13 (59.86,74.43) | EAST | 41.69 | 26 / 0 | (58.7,73.05) | 3.90 mm (BAT_PROTECTED_P) |
| XGPIO9 | R60.1 | U3.14 (59.86,75.08) | EAST | 56.18 | 28 / 0 | (58.55,75.55) | 4.34 mm |

**Study findings (all measured, none assumed):**

1. **All ten nets escape U3 cleanly** (B→F) — this is NOT a pad-escape wall like the D-309 U2 family. Every default via site clears every existing barrel by **≥3.1 mm** copper, and there are **ZERO existing vias inside any XGPIO routing bbox** — so **no `via_offset` is needed** (the U2-escape offset addresses a different, congested-landing problem).
2. **Shared-corridor capacity / ordering sensitivity is real.** The eight west-edge nets (0–7) all funnel their F↔B transition into ONE small open pocket north of U3; computed independently their offset via-sites collide (XGPIO5↔4/6↔5/3↔2 at cu −0.35 to −0.60 mm) and XGPIO6 & XGPIO7 pick the **identical** site (55.55,76.15). A large west multi-via group is therefore ordering-sensitive and risky. The **east pair XGPIO8+XGPIO9 separates cleanly (2.19 mm independent, 2.70 mm as routed)** — an independent legal corridor.
3. **Mechanical/RF/USB reservations:** the XGPIO corridor (x54–64, y17–80) crosses **none** — BOSS1/2, COAX_915_CHANNEL, ANT433_REGION and the NFC regions are all elsewhere.
4. **Netclass:** Default (0.200 mm width/clearance, normal 0.60/0.30 via, In1.Cu forbidden — the F/B incremental framework never touches In1).

## B — The real corridor wall found by the first gate, and the correct fix

Routing the four northern candidates (6,7,8,9) at the default **0.200 mm** clearance produced geometrically-complete paths (`route` ALL OK) that all **FAILED the real full-board gate** with new `clearance` violations (1–2 each). Root cause, consistent across all four: **every violation is against `/01_POWER_TREE/BAT_PROTECTED_P` under the D-269 BAT_MAIN routed-clearance rule (0.300 mm)**, not the default 0.200 mm. The 52.4 mm × 1.30 mm-wide protected-battery F.Cu trunk (12.10,82.40)→(63.75,73.40) sweeps **diagonally across the exact y≈73–82 band where every XGPIO via must land** north of U3, ending at the BAT_PROTECTED_P via cluster by U3's east edge. At 0.200 mm the copper landed **0.244–0.281 mm** from it — short of the enhanced battery clearance by ~0.02–0.06 mm.

**The correct, minimal fix is NOT a new mechanism:** route the XGPIO group at the **0.300 mm D-269 clearance floor** — the correct clearance the corridor demands. No `incremental_router.py`/`qrouter.py` logic change; only the group's `clr_pad`/`clr_trk` parameter (set to 300000 on the XGPIO GROUPS entries). Re-routed at 0.300 mm, **both a west net (XGPIO7) and an east net (XGPIO8) pass the real full-board gate individually**, and all six candidates (4–9) pass individually.

## C — Route → Gate → Promote (real full-board, member-by-member then combined)

Per the task, each pilot member was first routed and gated **individually** on scratch (both PASS), then the combined transaction:

- `route XGPIO_PILOT` → ALL OK (injected 62 existing-via obstacles): XGPIO8 43.794 mm cross-layer F/B through via 0.60/0.30 @ (58.600,72.950); XGPIO9 75.200 mm through via @ (58.450,75.650) — XGPIO9 re-routed around XGPIO8's laid via (79.1→75.2 mm), confirming clean in-group separation; In1/In4 [39,40] re-poured for 2 anti-pads. Authoritative sha UNCHANGED after route (scratch-only).
- `gate XGPIO_PILOT` → **PASS every check:** prior copper 0 missing (D-312 608 trk + 62 via a SUBSET); 25 new items all target-net; only zones 39/40 re-poured, all other 39 byte-identical; XGPIO8 and XGPIO9 each open-edges 1→0; 0 prior requested pairs regressed; **ratsnest 681→679 EXACTLY −2**; no new/worse DRC class, `clearance` 0→0; unconnected_items 499→499.
- `promote XGPIO_PILOT` → re-ran gate PASS, re-verified AUTH sha undrifted, merged 2 REST_INC journal entries.

## D — Promoted delta

| metric | D-312 | D-313 | Δ |
|---|---|---|---|
| tracks | 608 | 631 | +23 (XGPIO8 6 + XGPIO9 17; F.Cu haul + B.Cu fan-out) |
| vias | 62 | 64 | +2 (one cross-layer through via per net) |
| copper layers | 6 | 6 | 0 |
| zones | 41 | 41 | 0 |
| ratsnest | 681 | 679 | −2 (each net's 1 edge closed) |
| journal | 100 | 102 | +2 REST_INC |

PCB file diff **316 ins / 66 del** — additions 23 `(segment)` + 2 `(via)` (0 segment/via/footprint deletions, grep-confirmed); all 66 xy deletions are In1/In4 `filled_polygon` re-pour (2 via anti-pads). Real KiCad DRC error-severity identical: `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` — 0 `clearance`.

## E — Tests / artifacts

- New study **`w/xgpio_study_015.py`** (READ-ONLY) + `w/xgpio_study_015.json` — the faithful ten-net corridor characterisation.
- New contract **G27** (`router_regression.py`): XGPIO8+XGPIO9 fully copper-connected across the U3 F/B hop (U3.13↔R59.1, U3.14↔R60.1); copper legal (23 trk 0.200 mm F.Cu+B.Cu + two 0.60/0.30 through vias, 1 via/net); both vias clear every existing via (min 4.700 mm ≥ 0.80); **D-269 0.300 mm BAT_PROTECTED_P clearance kept (measured min F.Cu edge gap 0.3516 mm)**; ADD-ONLY (SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved). G18–G26 auto-generalise.
- `router_regression.py` = **ALL CHECKS PASS (G1–G27)**, deterministic.
- New `incremental_probe_015.py` PASS (READ-ONLY re-proof on the live board of exactly what the gate promoted, incl. the D-269 corridor clearance).
- `incremental_probe_006..014` PASS unchanged (auto-generalise via the shared `live_fingerprint.py` pin + REST_INC exclusion).
- `phaseB_bringup_probe_005.py` updated (631/64/102; **17 routed rest nets, 147 unrouted**) PASS.
- `live_fingerprint.py` bumped once (single source of truth → D-313).
- Real-board `kicad-cli` DRC + pcbnew ratsnest 679 re-run independently — no new `clearance`.
- **`d269`/`d264`/`dru` NOT regressed** — a board-swap A/B test proves **BYTE-IDENTICAL verdicts** (`diff` empty) on the committed D-312 board and the promoted D-313 board. The pre-existing power-tree reds (BAT_*/LTC synthetic-copper full-zone-re-pour proxies) are ~40 mm from the XGPIO copper and unchanged; they are NOT part of the maintained regression and were not weakened or misclassified.

## F — Opportunity & Simplification Scan (bounded to the subsystem)

**Is a shared XGPIO bank corridor a reusable throughput opportunity, or does per-net long-haul coupling make staged routing safer?** The study answers decisively: **staged, small-adjacent-pilot routing is safer.** The bank's ten members are NOT independent — the eight west-edge nets contend for one small via pocket north of U3 (independent offset sites collide; XGPIO6/7 want the identical cell), and the whole bank shares the D-269 BAT_PROTECTED_P clearance corridor. A blind ten-via group would be highly ordering-sensitive. The east pair is the naturally-independent island; the remaining bank should be taken as further small adjacent pilots (west nets need their vias explicitly staggered, or per-net site selection, when routed together) — not as one transaction.

**The one generic thing this increment established, grounded in measurement:** the XGPIO corridor is a **D-269-clearance corridor** (0.300 mm to the BAT_PROTECTED_P trunk), so all XGPIO GROUPS entries carry `clr_pad`/`clr_trk`=300000. This is the correct clearance, not a new primitive; the existing existing-via-aware framework handled the rest unchanged.

**Future option value of In2/In3:** untouched and preserved. The XGPIO netclass names F.Cu + In2.Cu as preferred layers with the J5 inter-row channel as the crossing lane; the current F/B outer-layer framework routed the pilot without needing an inner signal layer, so **In2/In3 remain fully available** as future capacity for the denser west-edge XGPIO members or any bus segment — a deliberately-preserved option, not spent.

No BOM / recoverability / testability / firmware / UX / mechanical change forced by this increment. **This is a non-blocking opportunity notice, not an owner decision.**

## G — Rollback

Pre-promotion `sha256 d6e0148a43a42895236b934cb6f7084036e50535a399f42fe09b300aabc5f1b8` (D-312; parent `1eb80a9`). Restore that PCB blob to revert; all other tracked changes (fingerprint/regression/probe/journal/GROUPS) are add-only or single-line bumps.

## H — Locked invariants preserved

No DRU / rule / clearance / stackup / topology / net / footprint / value / polarity / outline / placement change; no D-290 reauth. The two new vias are D-257-legal 0.60/0.30 (≥ 0.50 min_via, ≥ 0.25 mm hole-hole; measured 2.704 mm centre apart, 4.700 mm from any existing barrel). D-249 (≥ 1.20 BPP), **D-269 (0.300 — the binding XGPIO corridor rule, satisfied 0.352 mm)**, BAT_MAIN 0.60, D-257/D-258/D-263/D-264/D-266, D-275/D-288, In1/In4 GND roles (only those two planes re-poured), USB/RF/mechanical reservations — all ENFORCED. G18–G27 / D-304..D-312, `place_003l` (D-285), D-275 and D-277..D-312 preserved; frozen `beta-full-reference-v1` untouched; DEVICE_SPEC unchanged (no hardware/product fact changed — the XGPIO0..9 community GPIO bank is already specified); shared journal authoritative (102 entries); no orphan process.

## I — Next: FBV2-P2-016

**147 / 164 rest-of-board nets unrouted (17 routed: RGB 3 + ACC 2 + DISP 1 + IMU 1 + RGB_LED 3 + IR_RX_VS 1 + TOUCH 2 + AMP 1 + SD 1 + XGPIO 2).** The XGPIO bank is now characterised and opened. Sharply-defined next task:

**FBV2-P2-016 — the next XGPIO adjacent pilot (west-edge members) OR another clean local group.** The XGPIO corridor is proven (escape clean, D-269 0.300 mm clearance is the rule, east island done). The remaining nine XGPIO members are all routable individually at 0.300 mm (4–7 gate-clean individually); the open engineering question for a west multi-net pilot is **staggering the crowded north-of-U3 via pocket** (per-net site selection or a deliberate via stagger) so 2–4 west members co-route without via collision — the study quantified the crowding (independent sites collide; sequential in-group routing separates them via the grid mask, to be confirmed by a combined gate). Still avoid `U11_PROG` / `PWR_SENSE` (characterised hard walls); RF / NFC / USB / crystals / rails / switching / class-D deferred.

**Progress:** tenth rest-of-board increment; the FIRST XGPIO bank members, promoted after a full read-only corridor study, at the D-269 0.300 mm corridor clearance, zero router-logic change. PCB routing ~18 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged).
