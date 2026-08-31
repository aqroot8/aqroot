# FBV2-P2-025 / D-323 — EIGHTEENTH rest-of-board incremental increment routed + PROMOTED: the accelerometer/add-on presence-detect `ACC_DETECT_N` (3-pad, cross-layer MST — 1 through via + 1 same-layer B.Cu run), a clean increment in an OPEN region 2.750 mm clear of `BAT_PROTECTED_P`; promoted after the display backlight-control strap `DISP_BL_CTL_STRAP` hit a characterized boxed-MCU-pocket local wall and the navigation button `BTN_B_N` routed clean but FAILED the real full-board gate on the duplicate-ref tact-switch connectivity limit; a governed CTO ACCEPT + PROMOTE, ZERO router-logic change

**Date:** 2026-08-31
**Starting HEAD:** `36ffb2d26d3354e3f960d8687057723c5674eb5a` (D-322; pushed; `origin/master` identical)
**Authoritative PCB before:** `sha256 a861e30e5760515288ef9a3fc0c21ea6d3e9c31409f9181dd66d56ed0628efd1` — 759 tracks / 67 vias / 6 layers / 41 zones / ratsnest 667 / journal 114 (committed D-322)
**Authoritative PCB after:** `sha256 a7bf8bdc11f1bc39303c6f6b6c801e3a4a575add64596cc4be20745c57f9f626` — **781 tracks / 68 vias / 6 layers / 41 zones / ratsnest 665 / journal 116**
**Result:** GOVERNED CTO **ACCEPT + PROMOTE** — an eighteenth rest-of-board net (`ACC_DETECT_N`) is on the authoritative board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy CONTINUES; **no owner decision.**

---

## Summary

D-322 promoted the reserved/spare community expander GPIO in an open region and mandated the next clean
rest-of-board increment in an OPEN region, decided on measured merit via a fresh `w/screen_020.py` +
`w/vet_021.py` pick, continuing to avoid the west XGPIO F.Cu corridor, `U11_PROG`/`PWR_SENSE`, the
RF/NFC/USB/crystals/switching/class-D/rails/community-header mass, the auto-ALLOW converter-switching/USB-C
connector traps, and every characterized wall.

A fresh read-only screen (`w/screen_020.py`) measured the remaining **139** unrouted rest nets; its
auto-classifier ALLOW list still contained converter-switching / USB-C connector traps rejected here on
measured role. A focused read-only geometry vet (`w/vet_021.py`) measured the genuinely-functional shortlist.
Two cleaner-class / higher-preference candidates were tested FIRST and both set aside:

* `DISP_BL_CTL_STRAP` — the display backlight-control strap (`U1.16` MCU GPIO / `TP2.1` test point / `R108.1`
  + `R109.1` series), 4 pads all F.Cu, no via — returned **`NO_PATH` at 0.200 mm on ALL THREE MST edges**
  (including the SHORT 5.44 mm and 10.30 mm edges, none even at the 0.05/0.025 mm fine grid): the dense
  MCU/backlight pad pocket boxes every terminal. A characterized boxed-pocket local wall, the `MCU_EN_RC`
  lesson repeated.
* `BTN_B_N` — the navigation/boot button input (`SW7.1` button / `R9.2` pull-up / `U2.18` expander), 3 pads,
  one cross-layer through via in the OPEN south button field — **routed ALL OK but FAILED the real full-board
  gate on connectivity**: `SW7` is a tact switch whose two mechanically-linked terminals BOTH carry pad number
  "1", which the per-ref MST collapses to a single node, leaving one permanent open ratsnest edge. The
  authoritative board was NEVER touched.

The selected genuine functional detect **`ACC_DETECT_N`** — the accelerometer/add-on presence-detect (`R64.1` detect
divider/pull F.Cu + `R129.2` series B.Cu + `U3.17` PCAL9535A expander GPIO B.Cu), 3 pads on TWO faces → MST =
ONE cross-layer edge + ONE same-layer B.Cu run, in an OPEN region **2.750 mm clear of `BAT_PROTECTED_P` (its
routed copper clears BPP by 3.8831 mm) → zero D-269 involvement** — was routed, gated PASS on the real
full-board D-286 gate, and promoted. `incremental_router.py`/`qrouter.py` routing logic UNCHANGED (the only
code beyond the `GROUPS['ACC_DETECT_N']` entry + characterization comments was a probe via-total
generalization, §F).

---

## A — Screen (READ-ONLY, live board, `w/screen_020.py`)

The read-only screen measured the remaining **139 unrouted rest nets** on the live D-322 board.

**The auto-classifier is a FIRST pass only** (as documented D-318..D-322). Its ALLOW list still contained
converter-switching (`Net-(L1-*)`, `Net-(U12/U13-*)`, `BL_SW`, `BQ25185_SYS`) and USB-C connector
(`Net-(J3-*)`) traps — all rejected here on measured role — so the screen is a candidate funnel, not an
authorization.

---

## B — Geometry vet (READ-ONLY, live board, `w/vet_021.py`)

Measured the genuinely-functional shortlist (pads/layers, netclass MST edges same/cross + length, straight-MST
min-to-`BAT_PROTECTED_P` for D-269, and via class):

| net | pads / layer | MST edges | BPP dist | via | role |
|-----|--------------|-----------|----------|-----|------|
| `ACC_DETECT_N` | 3, two faces (F.Cu + B.Cu) | `R64.1↔R129.2` 19.64 mm CROSS + `R129.2↔U3.17` 19.31 mm same-B | 2.750 mm | 1 through | accelerometer/add-on presence-detect (**held clean alternate**) |
| `DISP_BL_CTL_STRAP` | 4 F.Cu | `TP2.1↔U1.16` 5.44 mm + `TP2.1↔R109.1` 10.30 mm + `U1.16↔R108.1` 24.77 mm | 37.854 mm | no | display backlight-control strap (`U1.16`/`TP2.1`/`R108.1`+`R109.1`) |
| `BTN_B_N` | 3, two faces (F.Cu + B.Cu) | `SW7.1↔R9.2` / `R9.2↔U2.18` (cross-layer through via, OPEN south button field) | 11.025 mm | 1 through | navigation/boot button input (`SW7.1`/`R9.2`/`U2.18`) |

`ACC_DETECT_N` carried congestion **103** — the lowest of the genuinely-clean functional shortlist
(`DISP_BL_CTL_STRAP` cong 185, `BTN_B_N` cong 141). Its vet nearest-other-copper figures (0.228 mm to
`NFC_5V_EN`, 0.007 mm to `V3V3_FB`) are **guidance only** — the router detours and the real D-286 full-board
gate arbitrates; the straight-MST min-to-BPP of 2.750 mm is >> the D-269 0.300 floor.

---

## C — the two set-aside candidates

**`DISP_BL_CTL_STRAP` — characterized boxed-MCU-pocket local wall, NOT promoted.** The low-current MCU
control/PWM strap (`U1.16` MCU GPIO / `TP2.1` test point / `R108.1` + `R109.1` series; `R109` bridges to the
SEPARATE downstream net `DISP_BL_CTL` → `U17.4` backlight driver, NOT in this increment), 4 pads all F.Cu,
no via, 37.854 mm clear of BPP. The vet measured nearest-other copper of 0.111 mm (`SD_CARD_DETECT_N`),
0.022 mm (accepted D-318 `BMI270_INT1_STRAP` copper) and 0.349 mm (`USB_D_ESD_P`). **ALL THREE MST edges
return `NO_PATH` at 0.200 mm** — including the SHORT 5.44 mm and 10.30 mm edges, not just the 24.77 mm long
haul, and none even at the 0.05/0.025 mm fine grid. The dense MCU/backlight pad pocket (cong 185) boxes every
terminal (the 0.022/0.111 mm proximities to accepted copper are real congestion). This is the `MCU_EN_RC`
lesson repeated — a boxed MCU-adjacent pocket, not an open MCU-pad escape like `SD_CS_N`/`UART0`.
`GROUPS['DISP_BL_CTL_STRAP']` is annotated — do NOT naively retry at 0.200 mm.

**`BTN_B_N` — routed ALL OK but FAILED the real full-board gate on connectivity, NOT promoted.** The
navigation/boot button input (`SW7.1` button F.Cu → `R9.2` pull-up B.Cu → `U2.18` expander B.Cu), 3 pads with
one 0.60/0.30 cross-layer through via in the OPEN south button field (NOT the characterized U2 west-edge
escape wall — the `U2.18` leg is a flat same-layer B.Cu run), cong 141, 11.025 mm clear of BPP. **Root cause**
(independently verified from the footprint): `SW7` is a 4-pin tactile switch whose TWO mechanically-linked
terminals BOTH carry pad number "1" on net `BTN_B_N`, at `(49.520, 96.750)` and `(57.480, 96.750)`, 7.96 mm
apart (and two pad "2" on GND likewise). The framework's per-ref MST (`pads_by_ref`) keys nodes by
`ref.padnum`, so the two `SW7.1` pads collapse to a SINGLE node → the second terminal is never driven → one
permanent open ratsnest edge (net open_edges 2→1, not 2→0) → **gate FAIL**. This is a connectivity gap of the
WHOLE duplicate-ref button family (every `SWx` tact switch), NOT a copper casualty — the scratch route was
discarded and the authoritative board was NEVER touched. `GROUPS['BTN_B_N']` is annotated — do NOT naively
retry any `SWx` button net until the framework grows a duplicate-ref MST (a deferred framework task).

`ACC_DETECT_N` (3 distinct-ref pads, gates clean) was promoted instead.

---

## D — Route + gate (real full-board, D-286)

**`route ACC_DETECT_N` ALL OK:** `R129.2↔U3.17` 35.311 mm B.Cu + `R129.2↔R64.1` 20.861 mm (B+F via) — 22
segments (3 F.Cu + 19 B.Cu, all 0.200 mm) + 1 via, the through via at `(57.900, 38.800)` in the OPEN north,
34.157 mm from every existing barrel. Realized routed copper clears `BAT_PROTECTED_P` by **3.8831 mm** (>>
D-269 floor) → ZERO D-269 involvement.

**`gate ACC_DETECT_N` PASS every check:** 0 Phase-A copper deleted/altered; 22 new tracks + 1 via all
target-net; **only the In1/In4 GND planes re-poured** (the via anti-pad), the other 39 zones identical; all
three pads (`R64.1`/`R129.2`/`U3.17`) copper-connected, net open_edges 2→0; 0 prior Phase-A/increment
requested pairs regressed; ratsnest 667→665 (−2 exact); no new/worse DRC class; DRC `unconnected_items`
499→499. `promote` re-ran the full gate PASS, re-checked the AUTH sha had not drifted, copied scratch→AUTH
(scratch `INC_ACC_DETECT_N` board sha == AUTH sha, zero drift — independently verified), merged 2 `REST_INC`
journal edges.

---

## E — Promoted board

`sha256 a861e30e…` → **`a7bf8bdc11f1bc39303c6f6b6c801e3a4a575add64596cc4be20745c57f9f626`**; tracks
759→**781** (+22, 3 F.Cu + 19 B.Cu, all 0.200 mm); vias 67→**68** (+1, one 0.60/0.30 through via); 6 layers /
41 zones; ratsnest 667→**665** (−2); journal 114→**116** (+2 `REST_INC`: `R129.2↔U3.17` B.Cu 35.311 mm,
`R129.2↔R64.1` B+F via 20.861 mm). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5 +
lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).

---

## F — Tests / integrity

* New **G35** in `router_regression.py` (all three `ACC_DETECT_N` pads connected; copper legal — 22 trk
  0.200 mm = 3 F.Cu + 19 B.Cu + exactly 1 0.60/0.30 through via; via ≥ 0.80 mm from every barrel, measured
  34.157 mm; ADD-ONLY — every prior increment + Phase-A 432/54 preserved). G18–G34 auto-generalise.
  `router_regression.py` **ALL PASS (G1–G35), deterministic twice** (555 lines / 143 PASS each run, identical
  G-verdicts).
* New `incremental_probe_023.py` **PASS**; `incremental_probe_006..022` + `phaseB_bringup_probe_005`
  (781/68/116; **26 routed rest nets, 138 unrouted**) **PASS**.
* **Probe via-total generalization (the ONLY code beyond the `GROUPS` entry + comments).** D-323 lays the
  FIRST new via since D-316, so the board via total moved 67→68. The no-via probes
  `incremental_probe_018..022` pinned the board via total to a hard-coded `67` at their "no-via class" check;
  this was generalized to `len(via) == EXPECT_VIAS` (the `live_fingerprint` single source of truth), KEEPING
  each probe's per-net `len(i_via) == 0` contract intact. Semantically sound + regression-safe: each net's
  no-via property is still asserted; only the redundant board-total literal now tracks the SoT, exactly as
  tracks/ratsnest/journal already do (verified: all 8 prior via-probes 008..017 already pin the total via
  `EXPECT_VIAS`). During recovery `incremental_probe_023.py`'s second via check (which had hard-coded `68`)
  was aligned to the same `EXPECT_VIAS` convention, keeping its per-net `i_via == 1` contract — so probe_023
  survives the next via increment like every prior via-probe. **ZERO contract weakened**, re-verified PASS.
* `live_fingerprint.py` bumped once (D-323) — the single source of truth. `incremental_baseline_006.json`
  left **stale-by-design** (verified unmodified vs HEAD — the gate computes its baseline live).
* Independent kicad-cli DRC (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}`; `clearance` 0). **A/B IDENTICAL** on committed D-322 and promoted D-323 (both
  boards same 6 violations, 499 unconnected).
* **D-269/D-264/DRU board-swap A/B** (committed D-322 vs promoted D-323 via `AQROOT_BETA_V2_PROJECT`, 4 runs
  each): `dru` FAIL(2)×4 on BOTH boards — IDENTICAL, deterministic; `d269` promoted D-323 =
  PASS,FAIL(2),FAIL(2),FAIL(2) and committed D-322 = FAIL(2)×4 — flips, count always 2; `d264` promoted
  D-323 = 2,1,2,3 and committed D-322 = 2,1,2,1 — both flip in the 1–3 range. All documented intrinsic
  non-determinism (synthetic Phase-A DRU probes), pre-existing flakes NOT regressions — the new copper is
  ~2.75–3.88 mm-from-BPP peripheral copper near `R64`/`R129`/`U3.17`, away from the BAT-divider/sense
  corridors these probes examine. Live AUTH sha re-verified `a7bf8bdc…` after the swap.

---

## G — Opportunity & simplification

* **Probe via-total generalization (§F)** — the probes 018–022 change to `EXPECT_VIAS` + the probe_023
  alignment, so the whole via-probe family now tracks the `live_fingerprint` SoT and survives future via
  increments without weakening any per-net contract.
* **Two NEW characterized walls:** `DISP_BL_CTL_STRAP` — the boxed MCU/backlight pocket (all 3 MST edges
  `NO_PATH` at 0.200 mm); and the WHOLE duplicate-ref button family (`SWx`) — blocked by the `pads_by_ref`
  MST collapse of dual pad-"1" tact-switch terminals → a **"duplicate-ref MST" deferred framework task**.
  `MCU_EN_RC`, the J1 display-connector haul (`DISP_CS_N`/`DISP_DC`), `BOOT_N` (poor detour, sensitive), and
  `U11_PROG`/`PWR_SENSE` all remain characterized.
* **138/164 rest nets unrouted** (26 routed) — continue one clean net/group at a time. Deferred framework
  tasks: the In2/In3 inner-layer west-XGPIO haul + the duplicate-ref button MST.
* No BOM/footprint/value/polarity/mechanical/firmware/UX change; `DEVICE_SPEC` unchanged.

---

## Locked-invariant preservation

No DRU/rule/clearance/stackup/topology/net/footprint/value/polarity/outline change; no D-290 reauth. D-249
≥1.20 mm BPP, D-269 0.300/0.60 BAT_MAIN + 0.200/0.150 signal, ≥0.25 hole-hole (D-257), D-275/D-288,
In1/In4 GND reference-plane roles, In2/In3 inner-signal capacity, RF/USB/mechanical reservations, and
D-304..D-322 all preserved. Frozen `beta-full-reference-v1` untouched. Journal authoritative (**116**). No
BOM/footprint/value/polarity/mechanical/firmware/UX change; `DEVICE_SPEC` unchanged. **Open owner decisions:
NONE.** `JLCPCB_READINESS` ~78 % (authoritative; JLCPCB fabrication file unchanged); PCB routing ~18 %;
overall ~76 %.

---

## Next — FBV2-P2-026

Route the next clean rest-of-board increment (single net or small coherent local group in an open region — a
fresh `w/screen_020.py` + `w/vet_021.py` pick) at its netclass Default under the D-286 real full-board gate;
on promote add `incremental_probe_024.py` + a `G36` contract and bump `live_fingerprint.py` once. Continue
avoiding the west XGPIO F.Cu corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/
community-header mass, the auto-ALLOW converter-switching/USB-C connector traps, and every characterized wall
(`MCU_EN_RC`, the J1 display-connector haul `DISP_CS_N`/`DISP_DC`, `BOOT_N`, the `DISP_BL_CTL_STRAP` boxed
pocket, `U11_PROG`/`PWR_SENSE`). Do NOT retry the `SWx` duplicate-ref button family until a duplicate-ref MST
lands. Hold the inner-layer west-XGPIO haul + the duplicate-ref button MST as deferred framework tasks.
**138/164 rest nets unrouted.** Rollback: pre-promotion `sha256 a861e30e…` (committed D-322, HEAD `36ffb2d`).
