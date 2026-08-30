# FBV2-P2-016 / D-314 — Eleventh rest-of-board incremental increment ROUTED + PROMOTED: XGPIO west-edge SOUTH pilot `XGPIO1`+`XGPIO0` (first WEST XGPIO bank members), after a governed recovery of the west-pair corridor screen

- **Task:** FBV2-P2-016 — the next XGPIO adjacent pilot (west-edge members), final governed recovery retry.
- **Decision:** D-314.
- **Starting HEAD:** `0faf85b` (D-313; pushed; `origin/master` identical). PCB `sha256 a0d6fead…`, 631 trk / 64 via / 6 layer / 41 zone / ratsnest 679 / journal 102.
- **Result:** GOVERNED CTO **ACCEPT + PROMOTE** — no owner decision. Autonomy continues.

## Summary

The two SOUTHERNMOST west community-header GPIO nets — `XGPIO1` (100 R series R52.1 F.Cu → PCAL9535A U3.5 B.Cu) + `XGPIO0` (R51.1 F.Cu → U3.4 B.Cu), on consecutive U3 pins — are routed and promoted as one incremental transaction onto the D-313 board (which carried the east pilot XGPIO8/XGPIO9). They are the FIRST members of the eight-net **west** XGPIO group, which the D-313 study had flagged as an ordering-sensitive shared-via-pocket hazard and deferred. A recovery screen on the live D-313 board measured that the **southern** west pair self-separates cleanly when routed **XGPIO1-first**, and a real full-board gate proved a genuine no-casualty / no-new-DRC increment → COPPER PROMOTED.

## A — Recovery of the west-pair corridor screen (root-cause fix, gitignored scratch only)

The recovery runner `checks/w/screen_016_one.py` (a durable one-order CLI over the faithful `checks/w/screen_016.py` ranker; both **gitignored** scratch) had a persistence/exit bug: `screen_016.py` carried its full 14-pair driver loop **at module level**, so `import screen_016` re-ran the entire 14-pair screen on every import, and the process died mid-import before the single pair's ledger write (the "attempted `1_0_0` ended before ledger write" symptom; the SCR16_* scratch dirs were byte-identical AUTH copies because `route_pair` never persisted; the recovery ledger was never written). **Fix (gitignored scratch only, ZERO routing-logic change):** guard `screen_016.py`'s standalone-ranker block behind `if __name__ == '__main__':` so importing it only exposes the routing functions/constants (`route_net_via`/`route_pair`/`analyse`/`W`/`CP`/`CT`). The runner then imports cleanly and re-measures exactly one `(a,b,order)` via the same `inject_existing_via_obstacles` + `connect_cross` machinery, persisting each row to a durable recovery ledger.

## B — The measured evidence (live D-313 board, D-269 0.300 mm, no via_offset)

No prior durable evidence survived (empty ledger, byte-identical scratch dirs). Only the missing/high-value southern-adjacent orders were re-run, one managed foreground process at a time, each persisted and inspected immediately:

| Pair | Route order | Verdict | via-via cu | BPP min | exv min |
|---|---|---|---|---|---|
| XGPIO0/1 | **XGPIO1→XGPIO0** (`1_0_0`) | **CLEAN** | **2.129 mm** | 2.038 mm | 3.607 mm |
| XGPIO0/1 | XGPIO0→XGPIO1 (`0_1_1`) | B-FAIL (XGPIO1 boxed out) | — | — | — |
| XGPIO1/2 | XGPIO2→XGPIO1 (`2_1_0`) | B-FAIL (XGPIO1 boxed out) | — | — | — |
| XGPIO1/2 | **XGPIO1→XGPIO2** (`1_2_1`) | **CLEAN** | 2.044 mm | 2.006 mm | 3.653 mm |

Both priority pairs are **conclusive** (each has exactly one clean order = XGPIO1-first) → the fallback XGPIO2/3 screen was not needed. The clean pattern is: XGPIO1 routes first and its via lands in the shared pocket at (55.40,79.00); the SECOND (southern) net sees XGPIO1's laid via as a real `qb.via()` obstacle and escapes WEST off it (XGPIO0 → (52.75,78.35)). Routing the southern net first boxes XGPIO1 out (no legal 0.200 mm corridor from R52.1). This contrasts with the NORTHERN west pins the D-313 study flagged (XGPIO6/7 collide onto the identical pocket cell) — the southern pair has room to fall west.

**Selection:** `XGPIO0 + XGPIO1`, routed **XGPIO1-first** — the minimum coherent clean west pair: marginally better margins than XGPIO1/2 (via-via 2.129 vs 2.044, BPP 2.038 vs 2.006), and the southernmost / most-independent pair, furthest from the crowded northern pocket. No via_offset (every site ≥2 mm from every barrel). Same D-269 0.300 mm clearance as the east pilot (the `BAT_PROTECTED_P` trunk crosses the via band).

## C — Route → Gate → Promote (real full-board, D-286)

- New `GROUPS` entry `XGPIO_PILOT_W` (`nets=['XGPIO1','XGPIO0']` — the clean route order; `clr_pad=clr_trk=300000`; no via_offset) + single-net `XGPIO1`/`XGPIO0` entries mirroring XGPIO4–9. Standard promotion path (a group definition, not a copper mutation); `incremental_router.py`/`qrouter.py` routing logic UNCHANGED.
- `route XGPIO_PILOT_W`: ALL OK — XGPIO1 R52.1↔U3.5 84.499 mm cross-via@(55.400,79.000); XGPIO0 R51.1↔U3.4 91.475 mm cross-via@(52.750,78.350) (XGPIO0 self-separated west off XGPIO1's laid via). 38 seg + 2 through vias; In1/In4 re-poured once. Authoritative sha UNCHANGED during route (`a0d6fead…`).
- `gate XGPIO_PILOT_W`: PASS every check — 0 Phase-A copper deleted/altered; 40 new items all target-net; only In1/In4 re-poured; both nets fully copper-connected (open-edges 1→0 each); 0 prior requested pairs regressed; ratsnest **679→677 (−2 exact)**; real DRC no new/worse class, `unconnected_items` 499→499.
- `promote`: re-ran gate PASS, AUTH sha unchanged since gate, copied scratch→AUTH, merged 2 `REST_INC` journal entries.

## D — Promoted delta

- **sha256** `a0d6fead125295441dda0f0008c1261f5c1cec39edb2b8c7bd925b214e7207eb` → **`95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605`**.
- tracks 631 → **669** (+38: XGPIO1 19 + XGPIO0 19, F.Cu haul + B.Cu fan-out); vias 64 → **66** (+2 through vias); 6 copper layers / 41 zones; ratsnest 679 → **677** (−2); journal 102 → **104** (+2 `REST_INC`).
- PCB file diff **404 ins / 36 del** — 40 `(segment)`/`(via)` lines added, **0 seg/via/footprint deletions**; all 36 deletions are In1/In4 `filled_polygon` xy (the 2 new via anti-pads).
- Real KiCad DRC error-severity **identical** to D-313: independent `kicad-cli pcb drc --severity-error` = `{solder_mask_bridge:1, hole_clearance:5}` (both pre-existing, unchanged); full histogram `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}` — **0 `clearance`**. pcbnew ratsnest re-run independently = **677**.

## E — Tests / artifacts

- New contract **G28** (both nets connected across the U3 F/B hop; copper legal 38 trk 0.200 mm F.Cu+B.Cu + 2× 0.60/0.30 through vias, 1 via/net; both vias ≥0.80 mm from every barrel — measured **min 4.207 mm**; D-269 0.300 mm `BAT_PROTECTED_P` clearance kept — measured F.Cu edge gap **2.2382 mm**; ADD-ONLY). G18–G27 auto-generalise → `router_regression.py` **ALL PASS (G1–G28), deterministic** (run twice, identical).
- New `checks/incremental_probe_016.py` PASS (integrity, prior-copper-preserved-exactly 631+64, Phase-A 432+54 intact, add-only F/B + 2 vias, via separation 2.729 mm centre, D-269 kept, connectivity gain, In1/In4-only re-pour, DRC unchanged).
- `_006..015` + `phaseB_bringup_probe_005` (669/66/104; 19 routed rest nets, 145 unrouted) all PASS; `live_fingerprint.py` bumped once (single source of truth).
- Recovery screen artifacts (gitignored): `w/screen_016_one.py` (fixed), `w/screen_016.py` (`__main__`-guarded), `w/screen_016_recovery.json` ledger.
- **`d269`/`d264`/`dru` are NOT part of the maintained deterministic regression (documented flaky ZONE_FILLER full-zone-repour proxies).** Board-swap A/B (committed D-313 vs promoted D-314): **d269 FAIL(2)==FAIL(2) identical; dru FAIL(2)==FAIL(2) identical.** `d264` differed (D-314 → 1 fail, D-313 → 2 fails) on a borderline U18 sense-corridor item (`R75.2→U18.8`) far from the XGPIO copper — **proven intrinsic non-determinism, not a regression**: re-running `d264` three times on the *identical* fixed D-314 board (sha `95bc07be`) flipped the count **2 → 1 → 3**. The authoritative DRC evidence (the gate + `incremental_probe_016` + independent `kicad-cli`) is byte-stable and clean.

## F — Opportunity & Simplification Scan (bounded to the subsystem)

- **The south of the west group is now open with the SAME zero-mechanism recipe** the east pilot used (route at the D-269 0.300 mm floor, XGPIO-lower-index-first so the southern neighbour self-separates west). The characterised hazard is specifically the NORTHERN pins (XGPIO5/6/7 crowd one pocket cell); the south (0/1/2/3) has room to escape west. Next west pilot (XGPIO2/3) should be screened live the same way — order still matters, do NOT auto-bundle.
- **In2/In3 inner-signal layers remain fully available** — the whole XGPIO bank is routed F/B only; inner capacity is deliberately preserved for any future denser routing.
- **Recovery-runner hardening is a reusable lever:** the `__main__` guard means the ranker module can be imported for any future single-order re-measurement without re-running the full screen; the durable ledger prevents silent evidence loss on a mid-run death. Non-blocking notice.
- No BOM / placement / stackup / mechanical / RF / safety change; both nets are noncritical 3V3 CMOS community-header GPIO straps.

## G — Rollback

Pre-promotion `sha256 a0d6fead125295441dda0f0008c1261f5c1cec39edb2b8c7bd925b214e7207eb` (D-313; parent `0faf85b`). Reverting the PCB + `phaseA_journal.json` to that sha and dropping the `XGPIO_PILOT_W` group restores D-313 exactly.

## H — Locked invariants preserved

All D-269 / D-264 / DRU rules, placement, stackup, netlist, topology, safety, RF/USB/mechanical reservations, DNP/tuning provisions unchanged. Phase-A copper 432 trk / 54 via intact; all ten prior rest increments intact. Frozen `beta-full-reference-v1` untouched. DEVICE_SPEC unchanged (no product-fact change — community-header GPIO already specified). Shared journal authoritative (104). No orphan process.

## I — Next: FBV2-P2-017

145 of 164 rest-of-board nets unrouted (19 routed: RGB 3 + ACC 2 + DISP 1 + IMU 1 + RGB_LED 3 + IR_RX_VS 1 + TOUCH 2 + AMP 1 + SD 1 + XGPIO8/9 2 + XGPIO1/0 2). The immediate target is the next XGPIO adjacent SOUTH-west pilot (**XGPIO2/3**, screened live with the XGPIO-lower-first order recipe), or another clean local group. `U11_PROG` / `PWR_SENSE` remain characterised hard walls — do NOT re-attempt naively.
