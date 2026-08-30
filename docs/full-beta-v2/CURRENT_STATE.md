# AQROOT Full Beta v2 — CURRENT STATE (durable checkpoint)

> Checkpoint/index only. Authority precedence: **CTO_DECISIONS.md > accepted
> audits/engineering evidence > CURRENT_STATE.md > summaries/transcripts/session
> memory.** If this file conflicts with higher-authority evidence, repair this file.
>
> **PRODUCT-SPEC AUTHORITY.** For any external / mechanical / marketing claim — renders,
> website, Kickstarter, enclosure/industrial-design briefs, product descriptions, spec
> sheets — the authoritative current-product spec/index is **`docs/full-beta-v2/DEVICE_SPEC.md`**
> (created FBV2-P2-004A / D-301). It is **MANDATORY** to consult before making any such
> claim; do not publicly claim a dimension, capacity, antenna count, connector, protocol,
> frequency, feature or internal component unless DEVICE_SPEC marks it MARKETING-SAFE.
> This file references DEVICE_SPEC rather than duplicating full specs.

## 1. Authoritative HEAD
- **FBV2-P2-012 / D-310 (this checkpoint — SEVENTH REST-OF-BOARD INCREMENT PROMOTED; the D-309 U2 B.Cu ESCAPE
  WALL BROKEN by a bounded via-site offset + existing-via awareness):** a governed CTO **ACCEPT + PROMOTE** — the
  display/touch control pair `TOUCH_RST_N` + `TOUCH_INT_N` (capacitive-touch reset + interrupt, display FPC J1 →
  touch-controller U2), **the group D-309 measured as a WALL**, is on the authoritative board with **no Phase-A /
  FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED / IR_RX_VS casualty and no new DRC**; autonomy CONTINUES, **no
  owner decision.** Starting HEAD `f2bcac1` (D-309; pushed; `origin/master` identical). **(1) Root cause of the
  D-309 wall — the router was BLIND to existing vias.** `qrouter.QBoard._scan` builds obstacles from footprint
  pads + `PCB_TRACK` but iterates `GetTracks()` and `continue`s on `PCB_VIA`, so every accepted through-via is
  invisible to escape/via_site/connect_role. U2.4/.7/.8/.11 stack on U2's WEST edge (x=54.14); the accepted D-306
  `DISP_RST_N` via sits at (52.95,87.0), 1.19 mm west of that column, so a westward cross-layer escape lands the
  new via (and threads its F.Cu run) right past the barrel; only real DRC caught it (D-309 +3; measured this
  cycle `AMP_SD_MODE` default via 0.100 mm copper to `DISP_RST_N`). **(2) The fix — two generic, bounded,
  `qrouter.py`-UNTOUCHED mechanisms in `connect_cross`.** (a) EXISTING-VIA AWARENESS — every accepted `PCB_VIA`
  barrel/hole is injected as an obstacle onto the per-route `QBoard` instance (mirroring `QBoard.via()`
  item-for-item), so escape/via_site/**connect_role's track search** respect accepted vias (add-only, per-route,
  generic; touches only the transient route QBoard so G-contract fixtures are unaffected); (b) BOUNDED VIA-SITE
  OFFSET — a group opts in with `via_offset` and the F↔B transition is deliberately walked ~2.5 mm off the
  nearest congesting barrel via `_offset_via_site` (a short host-face B.Cu fan-out) — the first increment that
  PLANS a via site; groups without `via_offset` are byte-identical to D-306/D-308. **(3) Screen (real-geometry
  clearance, READ-ONLY `w/geom_012.py` + `w/screen_012.py`, before any gate):** `AMP_SD_MODE` default via 0.70 mm
  from DISP = 0.100 mm CLASH (confirms D-309 +7); `TOUCH_RST_N`/`SD_DETECT` default vias clear the barrel but
  their tracks thread the west column (D-309 +3/+2); at 2.5 mm offset all four clear (via↔via 2.6–7.8 mm);
  `TOUCH_INT_N` on U2's EAST edge already 5.9 mm clear. Per the task preference the coherent display/touch PAIR
  was taken (both pass); unrelated nets NOT bundled. **(4) The gate (real full-board, D-286):** `route TOUCH_CTL`
  ALL OK (injected 58 existing-via obstacles): J1.47↔R12.1 22.217 mm F.Cu + R12.1↔U2.4 28.553 mm cross-via@(52.95,
  92.10); J1.46↔U2.19 54.708 mm cross-via@(61.15,88.85); 26 seg + 2 through vias; In1/In4 re-poured. (First
  attempt with via-offset ALONE still failed +3 — the via-blind track router threaded the F.Cu run 0.05 mm from
  the DISP barrel; the existing-via injection made connect_role via-aware and the re-route was clean — the offset
  fixes the via, the injection fixes the tracks.) `gate` = PASS every check: prior copper 0 missing (D-309 535
  trk + 58 via a SUBSET); 28 new items all target-net; only zones 39/40 re-poured, all other 39 byte-identical;
  both nets connected open-edges 2→0 and 1→0; 0 prior pairs regressed; **ratsnest 688→685 EXACTLY −3**; real DRC
  no new/worse class (`clearance` 0→0). **GATE PASS.** **(5) Promoted:** `sha256 5c5cae79…a339f63` →
  **`856f7a8adf0db9b114b9f09d7469308f921bc897aaf2ddce7f1c15c40a197114`**; tracks **535→561** (+26: 21 F.Cu + 5
  B.Cu fan-out); vias **58→60** (+2 offset through vias); 6 layers / 41 zones; ratsnest **688→685** (−3); journal
  **93→96** (+3 `REST_INC`); PCB file diff **310 ins / 40 del** — additions 26 `(segment)` + 2 `(via)` (0
  seg/via/fp del), all 40 del are In1/In4 `filled_polygon` xy (2 via anti-pads); real KiCad DRC error-severity
  identical (`solder_mask_bridge:1 + hole_clearance:5`; 0 `clearance`). **(6) Tests:** new contract **G24** (both
  nets connected across the U2 F/B hop; copper legal 26 trk 0.200 mm F.Cu+B.Cu + 2×0.60/0.30 through vias; the
  offset cleared both vias of every existing via — min TOUCH-via↔other-via **4.998 mm** ≥0.80 mm; ADD-ONLY
  IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54); G18–G23 auto-generalise →
  `router_regression.py` **ALL CHECKS PASS (G1–G24), 102 PASS lines**, deterministic; new probe
  `checks/incremental_probe_012.py` PASS; `_006..011` PASS unchanged (pre-X checks auto-generalise);
  `phaseB_bringup_probe_005` updated (561/60/96; 13 routed rest nets, 151 unrouted) PASS; real-board `kicad-cli`
  DRC + pcbnew ratsnest 685 re-run independently — no new `clearance`. `d269`/`d264`/`dru` NOT regressed — a
  **board-swap A/B test proves BYTE-IDENTICAL verdicts (`diff` empty) on the committed D-309 and promoted D-310
  boards** (pre-existing BAT_*/LTC power-tree reds far from the mid-board TOUCH copper). **(7) Opportunity &
  Simplification:** the via-site metadata is deliberately REUSABLE without hiding corridor coupling — the
  existing-via injection is unconditional (fixes a latent gap for EVERY future cross-layer increment) and
  re-proven by the defensive `_clears_existing_vias` guard for all groups; `via_offset` is an opt-in bounded
  scalar biasing "away from the nearest existing via" (a general rule), now available to the rest of the U2
  family; sibling U2 groups `AMP_SD_MODE`/`SD_DETECT` NOT bundled (task preference; annotated with clean measured
  2.5 mm sites). **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion
  `sha256 5c5cae79…a339f63` (D-309; parent `f2bcac1`). Next: **FBV2-P2-013 — the U2 escape family is UNLOCKED:
  complete it (`AMP_SD_MODE` U2.7, `SD_CARD_DETECT_N` U2.11 both measured clean at 2.5 mm offset — add
  `via_offset` and route/gate), or another clean local group; 151 of 164 rest nets unrouted; `U11_PROG`/
  `PWR_SENSE` remain characterised walls.** Full analysis:
  [`audits/2026-08-30-p2-012-d310-seventh-rest-of-board-incremental-increment-touch-ctl-u2-escape-via-offset-promoted.md`](audits/2026-08-30-p2-012-d310-seventh-rest-of-board-incremental-increment-touch-ctl-u2-escape-via-offset-promoted.md).
  This checkpoint is written in the D-310 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-011 / D-309 (SIXTH REST-OF-BOARD INCREMENT PROMOTED; cleanest class, NO via;
  display/touch U2-escape wall characterised; shared live-fingerprint helper landed):** a governed CTO
  **ACCEPT + PROMOTE** — the IR receiver (U6) local filtered supply `IR_RX_VS_LOCAL` (series filter R21.2 +
  decoupling C11.1 → U6.3 THT supply pin, all same-layer F.Cu, **NO via**) is on the authoritative board, with
  **no Phase-A / FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED casualty and no new DRC**; autonomy CONTINUES,
  **no owner decision.** Starting HEAD `49528f2` (D-308; pushed; `origin/master` identical). **(1) Same
  `incremental_router.py`, ZERO new routing mechanics** — the proven same-layer no-via class (like D-307 but on
  F.Cu); `connect_cross`/`refill_planes`/`qrouter.py` untouched. **(2) Candidate selection — EARNED on gate
  evidence, not defaulted.** FOUR groups routed on scratch + put through the REAL full-board gate: the
  task-preferred **display/touch group** `TOUCH_CTL` (`TOUCH_RST_N`+`TOUCH_INT_N`) and `AMP_SD_MODE`,
  `SD_DETECT` (`SD_CARD_DETECT_N`) each routed ALL OK on the scratch router but **FAILED the real gate with NEW
  `clearance` (+3 / +7 / +2)** — long cross-board hauls (33–68 mm) whose cross-layer via lands in the
  **congested U2 B.Cu escape beside the accepted D-306 `DISP_RST_N` via** (U2.4/.7/.11/.19 sit beside U2.8): a
  CHARACTERISED WALL, deferred to FBV2-P2-012 with a deliberate U2-escape corridor plan (failing `GROUPS`
  entries annotated). The 'favor display/touch IF clean' preference was honored — tried first, empirically shown
  NOT clean. CHOSE **`IR_RX_VS`** — pristine (cu 0), local NE-corner cluster, same-layer F.Cu, no via.
  **(3) The gate (real full-board, D-286):** `route IR_RX_VS` → ALL OK (C11.1↔R21.2 3.113 mm + R21.2↔U6.3
  9.291 mm; 8 F.Cu segments 0.200 mm, no via); prior copper deleted/altered = 0 (D-308 527 trk + 58 via multiset
  a SUBSET); 8 new items all target-net; **ALL 41 zones byte-identical** (no via ⇒ no plane re-pour);
  `IR_RX_VS_LOCAL` fully connected (open-edges 2→0); 0 prior pairs regressed; pcbnew **ratsnest 690→688** (−2);
  real kicad-cli DRC no new/worse class. **GATE PASS.** **(4) Promoted:** authoritative
  `sha256 f4e95dec…8559e7ee` → **`5c5cae79465416c81f9d7b8dba5b2e3a3325bd9a0680b65103badf0e1a339f63`**; tracks
  **527→535** (+8); vias **58** (no via); 6 layers / 41 zones; ratsnest **690→688** (−2); journal **91→93** (+2
  `REST_INC`); PCB file diff **64 ins / 0 del** — all 8 additions `(segment)` F.Cu (0 seg/via/fp del, 0 zone
  change; cleanest class, tied D-307); real KiCad DRC **identical**
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
  **(5) Tests:** new contract **G23** (G18–G22 stay green unchanged — ADD-ONLY auto-generalises) →
  `router_regression.py` **ALL CHECKS PASS (G1–G23), 98 PASS lines**, deterministic; new probe
  `checks/incremental_probe_011.py` PASS; `_006/_007/_008/_009/_010` + `phaseB_bringup_probe_005` refreshed to
  the D-309 board (535/58/93; 11 routed rest nets, 153 unrouted) PASS; real-board `kicad-cli` DRC + pcbnew
  ratsnest 688 re-run independently — no new `clearance`. The Phase-A DRU-synthesis probes `d269`/`d264`/`dru`
  are NOT part of the maintained regression and NOT regressed — a **board-swap A/B test proves BYTE-IDENTICAL
  verdicts on the committed D-308 and promoted D-309 boards** (pre-existing BAT_*/LTC power-tree reds ~60 mm
  from my copper; the flaky `d269` full-zone-re-pour proxy was NOT mistaken for authoritative DRC).
  **(6) Opportunity & Simplification (ACTED-ON — the exact one D-308 §E pre-flagged):** introduced
  **`checks/live_fingerprint.py`**, a single source-of-truth `EXPECTED` dict (sha/tracks/vias/layers/zones/
  ratsnest/journal) bumped ONCE per promotion; all six probes refactored to import it, replacing the ~25
  identical per-increment `EXPECT_*` hand-edits — a pure DRY consolidation weakening NO historical contract
  (each probe still asserts live-board == EXPECTED and keeps its own structural checks), all six PASS.
  **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion
  `sha256 f4e95dec…8559e7ee` (D-308; parent `49528f2`). Next: **FBV2-P2-012 — the U2 B.Cu escape corridor
  (plan a via SITE off U2's edge to clear the `DISP_RST_N` barrel, unlocking the display/touch/SD/audio-strap
  family), or another clean local no-via/single-via group; `U11_PROG`/`PWR_SENSE` + the four U2-escape
  candidates remain characterised walls — do NOT re-attempt naively.** Full analysis:
  [`audits/2026-08-30-p2-011-d309-sixth-rest-of-board-incremental-increment-ir-rx-vs-promoted.md`](audits/2026-08-30-p2-011-d309-sixth-rest-of-board-incremental-increment-ir-rx-vs-promoted.md).
- **FBV2-P2-010 / D-308 (FIFTH REST-OF-BOARD INCREMENT PROMOTED; the FIRST MULTI-VIA
  increment):** a governed CTO **ACCEPT + PROMOTE** — the front-panel RGB status-indicator completion (three
  LED-cathode nets `Net-(D13-RK)`/`Net-(D13-GK)`/`Net-(D13-BK)`) is on the authoritative board, closing the
  D-304 `FRONT_RGB` indicator on the LED side, with **no Phase-A / FRONT_RGB / ACC / DISP / IMU casualty and no
  new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `c939f35` (D-307; pushed; `origin/master`
  identical). **(1) Same `incremental_router.py`, ZERO new mechanics** — the FIRST multi-via increment needed NO
  change to `connect_cross`/`refill_planes`/`qrouter.py`: the existing per-edge loop lays one 0.60/0.30 Default
  through via per cross-layer edge (three times) and `refill_planes` re-pours In1/In4 once for all vias; a
  multi-net group of independent single-via nets is already within the D-306-proven mechanic. **(2) Group
  selection (measured; coherent + local + clean — baseline `a309f8ce…` 502/55/6, ratsnest 693, journal 88; new
  READ-ONLY screen `w/screen_010.py` ranking ALL 156 remaining unrouted multi-pad nets by pad layers / THT / MST
  / bbox-span / congestion).** CHOSE **FRONT_RGB_LED** (`Net-(D13-RK/GK/BK)`, R124.2/R125.2/R126.2 B.Cu → D13
  MHPA3528 cathodes F.Cu) — the coherent completion of the D-304 indicator, local (span ≤26 mm), clean (cu
  6–11), low-current non-switching; three independent single-via cross-layer nets. Excluded with evidence:
  XGPIO0…9 bank (~55 mm cross-board hauls — not local), NFC/RF/USB/crystals, ACC_5V boost (switching), IR-LED
  drive (Q1-switched), SPK class-D, community J5/J8 headers, scattered BTN_x_N buttons, U11_PROG + PWR_SENSE
  (D-307 hard walls). A coherent 3-net group preferred to a safe singleton to show throughput beyond
  singletons/2-net clusters WITHOUT bundling unrelated nets. **(3) The gate (real full-board, D-286):** `route
  FRONT_RGB_LED` → ALL OK (25 segments F.Cu+B.Cu 0.200 mm + 3 through vias 0.60/0.30; In1/In4 zones [39,40]
  re-poured once); prior copper deleted/altered = 0 (D-307 502 trk + 55 via multiset a SUBSET); 28 new items all
  target-net; ONLY zones 39/40 fill-changed, all other 39 zones byte-identical; all three D13 nets fully
  connected (open-edges 1→0 each); 0 prior pairs regressed; pcbnew **ratsnest 693→690** (−3); real kicad-cli DRC
  no new/worse class. **GATE PASS.** **(4) Promoted:** authoritative `sha256 a309f8ce…31279a50` →
  **`f4e95decb5be87f6e758f76803e57be68a4437afaef75973518983008559e7ee`**; tracks **502→527** (+25 D13-cathode);
  vias **55→58** (+3 through vias); 6 layers / 41 zones unchanged; ratsnest **693→690** (−3); journal **88→91**
  (+3 `REST_INC`); PCB file diff **352 ins / 59 del** — additions are 25 `segment` + 3 `via` lines (zero
  segment/via/footprint deletions, grep-confirmed); all 59 deletions are In1/In4 GND `filled_polygon` xy (the 3
  via anti-pads); real KiCad DRC **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}` — 0 clearance, hole_clearance unchanged at 5, 0 violations touch the D13 copper).
  **(5) Tests:** new contract **G22** (G18–G21 stay green unchanged — ADD-ONLY invariants exclude all `REST_INC`
  nets and pin `phaseA_via`==54, auto-generalising as total vias grow 55→58) → `router_regression.py` **ALL
  CHECKS PASS (G1–G22), 94 PASS lines**, deterministic; new probe `checks/incremental_probe_010.py` ALL PASS;
  `checks/incremental_probe_006/007/008/009.py` refreshed to the D-308 board (`_009` pre-IMU-copper check
  generalised) ALL PASS; `checks/phaseB_bringup_probe_005.py` updated (527/58/91; 10 routed rest nets, 154
  unrouted) ALL PASS. The Phase-A DRU-synthesis probes `d269`/`d264`/`dru_probe` are NOT part of the maintained
  increment regression and NOT regressed by D-308 (`dru_probe`(2)/`d264`(1) carry the SAME pre-existing reds on
  pristine HEAD; `d269` C/D is a flaky borderline between two REMOTE Phase-A items under KiCad's
  non-byte-reproducible full-zone re-pour — it flips on HEAD too; the byte-stable authoritative board is
  DRC-clean). **Open owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion
  `sha256 a309f8ce…31279a50` (D-307; parent `c939f35`). Next: **FBV2-P2-011 — continue rest-of-board routing
  (next bounded group, same framework); the two congested regions (BQ25185/BPP trunk, west BAT trunk) remain
  characterised hard walls — do NOT re-attempt naively.** Full analysis:
  [`audits/2026-08-30-p2-010-d308-fifth-rest-of-board-incremental-increment-front-rgb-led-promoted.md`](audits/2026-08-30-p2-010-d308-fifth-rest-of-board-incremental-increment-front-rgb-led-promoted.md).
  This checkpoint is written in the D-308 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-009 / D-307 (FOURTH REST-OF-BOARD INCREMENT PROMOTED; the promoted fallback was
  EARNED, not defaulted to):** a governed CTO **ACCEPT + PROMOTE** — a fourth rest-of-board net (the BMI270 IMU
  I2C address-select strap `BMI270_SDO_ADDR`) is on the authoritative board, with **no Phase-A / FRONT_RGB / ACC /
  DISP casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `73ea58e` (D-306;
  pushed; `origin/master` identical). **(1) Same `incremental_router.py`, ZERO new mechanics** — a same-layer
  B.Cu multi-terminal net routed through the existing Prim-MST + `connect_role` path; the D-306
  via/`connect_cross`/`refill_planes` machinery reused byte-for-byte correctly did NOT engage (no via ⇒ no plane
  re-pour ⇒ all 41 zones byte-identical). **(2) Group selection (measured; highest-value low-risk, not merely the
  shortest net — baseline `9c0586d8…` 494/55/6, ratsnest 695, journal 86; refined READ-ONLY screen
  `w/screen_009.py` reporting MST/layer/THT, group bbox, accepted-copper congestion within bbox+1/+2 mm and a
  footprint-local coherence dump; all candidate nets confirmed Default netclass from the board).** Five candidates
  recorded. CHOSE PRIMARY **U11_PROG** (`ILIM_VSET`+`ISET`, coherent same-chip BQ25185 charger current-program
  straps) — a clean singleton is NOT bundled with unrelated nets to hit a count, and the favored IMU/I2C family
  has no clean local *pair* (the only other U4 net `BMI270_INT1_RAW` is a ~46 mm haul to the MCU). Fallbacks:
  **PWR_SENSE** (`VBUS_PRESENT`+`MAX17048_ALRT_N`), then pristine **IMU_ADDR** (`BMI270_SDO_ADDR`, 0 nearby
  copper). Rejected: IMU_INT1 (17 mm MCU-adjacent single strap), IMU_COMBO (52 mm half-board span, needs a via);
  excluded per mandate community-header/RF/NFC/USB/crystals/switching (ACC_5V boost)/rails/class-D SPK.
  **(3) Two congested primaries EMPIRICALLY DISPROVEN (one foreground run each, authoritative untouched):**
  `route U11_PROG` → INCOMPLETE (1/2): `ILIM_VSET` clean (4.857 mm) but `ISET` R37.1→**U11.8 NO LEGAL ESCAPE** —
  boxed by BQ25185 pins U11.6/U11.9 + board edge (pad-local wall, order-independent); `route PWR_SENSE` →
  INCOMPLETE (2/4): R104.2→TP31.1 + TP11.1→U14.5 **no legal corridor** even at the 0.025 mm fine grid (west
  `BAT_PROTECTED_P` trunk); both confirm the congestion screen, AUTH sha UNCHANGED after each, no rule weakened.
  **(4) The pristine fallback, EARNED — the gate (real full-board, D-286):** `route IMU_ADDR` → ALL OK (R118.1↔
  R119.2 2.709 mm, R119.2↔U4.1 3.454 mm; 8 segments; 0.200 mm B.Cu, 0 via; 3-pad/2-edge MST); prior copper
  deleted/altered = 0 (D-306 494 trk + 55 via multiset is a SUBSET); every new item a target-group net; ZERO
  zones fill-changed (no via); `BMI270_SDO_ADDR` fully connected (open-edges 2→0); 0 prior pairs regressed; pcbnew
  **ratsnest 695→693** (−2); real kicad-cli DRC no new/worse class. **GATE PASS.** **(5) Promoted:** authoritative
  `sha256 9c0586d8…3f62259` → **`a309f8ce022b48ef04baa2fef591c64eb1a643049ad31220a9cff24831279a50`**; tracks
  **494→502** (+8 BMI270_SDO_ADDR); vias **55** (no new via); 6 layers / 41 zones unchanged; journal **86→88**
  (+2 `REST_INC`); PCB file diff **64 ins / 0 del** — pure ADD-ONLY (8 B.Cu `segment` lines; zero
  segment/via/footprint/filled_polygon deletions, grep-confirmed; cleanest increment yet); real KiCad DRC
  **identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`).
  **(6) Tests:** new contract **G21** (G18–G20 stay green unchanged — ADD-ONLY invariants already exclude all
  `REST_INC` nets generically) → `router_regression.py` **ALL 92 CHECKS PASS (G1–G21)**, deterministic; new probe
  `checks/incremental_probe_009.py` ALL PASS; `checks/incremental_probe_006/007/008.py` refreshed to the D-307
  board (`_008` pre-DISP-copper check generalised) ALL PASS; `checks/phaseB_bringup_probe_005.py` updated
  (502/55/88; 7 routed rest nets, 157 unrouted) ALL PASS. **Open owner decisions: NONE;** `JLCPCB_READINESS`
  unchanged (~77 %). Rollback: pre-promotion `sha256 9c0586d8…3f62259` (D-306; parent `73ea58e`). Next:
  **FBV2-P2-010 — continue rest-of-board routing (next bounded group, same framework); the two congested regions
  (BQ25185/BPP trunk, west BAT trunk) are now characterised hard walls — do NOT re-attempt naively.** Full
  analysis:
  [`audits/2026-08-30-p2-009-d307-fourth-rest-of-board-incremental-increment-imu-addr-promoted.md`](audits/2026-08-30-p2-009-d307-fourth-rest-of-board-incremental-increment-imu-addr-promoted.md).
- **FBV2-P2-008 / D-306 (THIRD REST-OF-BOARD INCREMENT PROMOTED; FIRST VIA / MIXED-LAYER
  PRIMITIVE):** a governed CTO **ACCEPT + PROMOTE** — a third rest-of-board net is on the authoritative board,
  and for the first time the increment uses a **via / mixed-layer route**, with **no Phase-A / FRONT_RGB / ACC
  casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `c22b9fd` (D-305; pushed;
  `origin/master` identical). **(1) Same `incremental_router.py`, minimally extended** — three generic mechanics,
  each forced by a concrete need: `edge_plan` (per-edge layer decision — same-layer B.Cu groups stay
  byte-identical), `connect_cross` (composes only proven `qrouter` primitives escape→via_site→via→two anchored
  `connect_role` runs, so **`qrouter.py` is untouched** and the battery driver unaffected), `refill_planes`
  (re-pours only In1/In4 when a via was laid). **(2) Group selection (measured, prefer a new safe primitive —
  baseline `f0046eb7…` 483/54/6, ratsnest 697, journal 84; `w/screen_007.py`, READ-ONLY):** CHOSE **DISP_RST
  (`/DISP_RST_N`)** — one 3-pad display-reset net with pads NOT all on one layer (R16.1/J1.10 F.Cu, U2.8 B.Cu):
  MST = one SAME-LAYER edge (R16.1↔J1.10, first incremental F.Cu run) + one CROSS-LAYER edge (J1.10↔U2.8, first
  incremental via / mixed-layer route, ONE 0.60/0.30 Default through via ≥ 0.50 mm min_via), low congestion (2
  Phase-A items in bbox+2 mm), NONCRITICAL low-speed reset. Rejected: AUDIO_SPK (F.Cu+THT but class-D SWITCHING
  outputs, excluded), U11_PROG (16 items, coupled to safety-critical BPP path), PWR_SENSE (12 items, congested);
  FALLBACK held (not needed): IMU_STRAP `BMI270_SDO_ADDR` B.Cu singleton; excluded per mandate
  community-header/RF/NFC/USB/crystals/rails. **(3) First-via blocker, characterised (not brute-forced):** the
  through via pierces the In1/In4 GND planes; the stale plane fill had no anti-pad (first gate: `clearance` ×2 +
  `hole_clearance` ×2 at (52.95,87.0)). Focused evidence — a plain refill drifts ONLY zones 39/40 (In1/In4 GND,
  +35 pts each, a stored-vs-current `ZONE_FILLER` discrepancy independent of the via) and no other zone — so
  `route` re-pours EXACTLY In1/In4 when a via was laid; DRC returns to baseline IDENTICALLY (plane byte-equality
  NOT claimed; standard = DRC-neutral + "only In1/In4 changed"). **(4) The gate (real full-board, D-286):** prior
  copper deleted/altered = 0 (D-305 483 trk + 54 via multiset is a SUBSET); every new item a target-group net;
  ONLY In1/In4 GND planes re-poured (all other 39 zones identical); DISP_RST_N fully connected across the hop
  (open-edges 2→0); 0 prior pairs regressed; pcbnew **ratsnest 697→695** (−2); real kicad-cli DRC no new/worse
  class. **GATE PASS.** **(5) Promoted:** authoritative `sha256 f0046eb7…04c7cd41` → **`9c0586d8…e3f62259`**;
  tracks **483→494** (+11 DISP_RST_N); vias **54→55** (+1 F↔B through via); 6 layers / 41 zones unchanged;
  journal **84→86** (+2 `REST_INC`); board diff **470 ins / 336 del** (all 336 deletions are In1/In4
  `filled_polygon` xy — the plane re-pour; zero deleted segment/via/footprint lines); real KiCad DRC **identical**
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`). **(6) Tests:**
  new contract **G20** (+ G18/G19 generalised to pin `phaseA_via`==54 instead of `all_via`==54) →
  `router_regression.py` **ALL 89 CHECKS PASS (G1–G20)**, deterministic; new probe
  `checks/incremental_probe_008.py` ALL PASS; `checks/incremental_probe_006/007.py` refreshed ALL PASS;
  `checks/phaseB_bringup_probe_005.py` updated (494/55/86; 6 routed rest nets, 158 unrouted) ALL PASS. **Open
  owner decisions: NONE;** `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256
  f0046eb7…04c7cd41` (D-305; parent `c22b9fd`). Next: **FBV2-P2-009 — continue rest-of-board routing (next
  bounded group, same framework).** Full analysis:
  [`audits/2026-08-30-p2-008-d306-third-rest-of-board-incremental-increment-disp-rst-via-promoted.md`](audits/2026-08-30-p2-008-d306-third-rest-of-board-incremental-increment-disp-rst-via-promoted.md).
  This checkpoint is written in the D-306 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-007 / D-305 (SECOND REST-OF-BOARD INCREMENT PROMOTED):** a governed CTO
  **ACCEPT + PROMOTE** — a second rest-of-board net-group is on the authoritative board, with **no Phase-A /
  FRONT_RGB casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `6353bd7`
  (D-304; pushed; `origin/master` identical). **(1) Same reusable lever** `checks/incremental_router.py`
  (no new mechanics — only a new `GROUPS` entry). **(2) Group selection (measured, `incremental_router.py
  baseline` + `w/screen_007.py`, READ-ONLY):** CHOSE **ACC_3V3_CTL** (`/ACC_3V3_EN` + `/01_POWER_TREE/
  ACC_3V3_ILIM`) — accelerometer 3V3 load-switch (U20) local control: enable (U3.15 → R98/U20.1/TP26, a
  4-pad multi-terminal net) + current-limit set (R97 → U20.4); both Default netclass (0.200 mm width /
  clearance, **no via**), all B.Cu SMD, low-congestion (only 4 Phase-A B.Cu strands within bbox + 2 mm),
  NONCRITICAL low-current control; **adds the multi-segment MST primitive** (FRONT_RGB were all single-edge
  2-pad). Rejected: IMU_STRAP `BMI270_SDO_ADDR` (clean but singleton — kept as fallback), PWR_SENSE (12
  nearby copper, congested), U11_PROG (16 nearby, D-302 wall region), AUDIO_SPK (F.Cu/THT/analog), DISP_RST
  (MIX-layer needs a via); excluded per mandate community-header/RF/NFC/USB/crystals/rails. **(3) The gate
  (real full-board, D-286):** prior copper deleted/altered = 0 (D-304 452 trk + 54 via multiset is a SUBSET);
  every new item a target-group net; both nets fully copper-connected (ACC_3V3_ILIM 1→0, ACC_3V3_EN 3→0); 0
  prior requested pairs regressed; pcbnew **ratsnest 701→697** (−4); real kicad-cli DRC no new/worse class.
  **GATE PASS.** **(4) Promoted:** authoritative `sha256 00c93bdb…dfb72aad` → **`f0046eb7…04c7cd41`**; tracks
  **452→483** (+31 ACC_3V3_CTL); vias **54** (no new via); 6 layers / 41 zones unchanged; journal **80→84**
  (+4 `REST_INC`); board diff **248 ins / 0 del** (ADD-ONLY at file level); real KiCad DRC **identical**
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`). **(5)
  Tests:** new contract **G19** (+ G18 generalised to exclude all `REST_INC` nets) → `router_regression.py`
  **ALL 86 CHECKS PASS (G1–G19)**, deterministic; new probe `checks/incremental_probe_007.py` ALL PASS;
  `checks/incremental_probe_006.py` refreshed ALL PASS; `checks/phaseB_bringup_probe_005.py` updated
  (483/84; 5 routed rest nets, 159 unrouted) ALL PASS. **Open owner decisions: NONE;** `JLCPCB_READINESS`
  unchanged (~77 %). Rollback: pre-promotion `sha256 00c93bdb…dfb72aad` (D-304; parent `6353bd7`). Next:
  **FBV2-P2-008 — continue rest-of-board routing (next bounded group, same framework).** Full analysis:
  [`audits/2026-08-30-p2-007-d305-second-rest-of-board-incremental-increment-acc-3v3-ctl-promoted.md`](audits/2026-08-30-p2-007-d305-second-rest-of-board-incremental-increment-acc-3v3-ctl-promoted.md).
  This checkpoint is written in the D-305 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-006 / D-304 (FIRST REST-OF-BOARD INCREMENT PROMOTED):** a governed CTO
  **ACCEPT + PROMOTE** — the first rest-of-board copper is on the authoritative board, with **no Phase-A
  casualty and no new DRC**; autonomy CONTINUES, **no owner decision.** Starting HEAD `50149f4` (D-303;
  pushed; `origin/master` identical). **(1) The reusable lever:** `checks/incremental_router.py` — a scoped
  INCREMENTAL router/promoter (commands `baseline`/`route`/`gate`/`promote`) that loads the promoted board via
  `qrouter.QBoard` (all existing copper is an OBSTACLE; new copper is ADDED, never `Remove()`d), routes a
  bounded named net-GROUP into a scratch copy `checks/w/INC_<GROUP>/` (authoritative project untouched during
  the experiment — sha256 verified unchanged after `route`), and PROMOTES only on a real full-board gate PASS.
  **(2) Group selection (measured, `w/measure_rest_006.py`, READ-ONLY):** CHOSE **FRONT_RGB**
  (`/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N|G_N|B_N`) — front-panel RGB status-LED control (U23 expander →
  R124/125/126), 6 pads, all B.Cu SMD, Default netclass (0.200 mm width / 0.200 mm clearance, **no via**),
  region carries **ZERO Phase-A copper** (isolated), NONCRITICAL, no rail/RF/USB/HV/clock constraint; rejected
  07_IR (F.Cu/THT near edge, moderate-current emitter), 01_POWER_TREE short pairs (power-adjacent), 05_I2C
  single net; excluded per mandate community-header/RF/NFC/USB/crystals/rails. **(3) The gate (real
  full-board, D-286):** Phase-A copper deleted/altered = 0 (D-302 copper-item multiset is a SUBSET of the
  routed items); every new item a target-group net; each target net fully copper-connected
  (`GetConnectedItems`, 1→0); 0 prior Phase-A requested pairs regressed (71); pcbnew **ratsnest 704→701**
  (−3); real kicad-cli DRC no new/worse class. **GATE PASS.** **(4) Promoted:** authoritative
  `sha256 63a9bc54…f87d6ba9` → **`00c93bdb…dfb72aad`**; tracks **432→452** (+20 FRONT_RGB); vias **54** (no
  new via); 6 layers / 41 zones unchanged; journal **77→80** (+3 `REST_INC`); real KiCad DRC **identical**
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`). **(5)
  Tests:** new contract **G18** + `router_regression.py` **ALL 82 CHECKS PASS (G1–G18)**, deterministic; new
  probe `checks/incremental_probe_006.py` ALL PASS; `checks/phaseB_bringup_probe_005.py` updated to the
  promoted state (452/80; 3 routed rest nets, 161 unrouted) ALL PASS. **Open owner decisions: NONE;**
  `JLCPCB_READINESS` unchanged (~77 %). Rollback: pre-promotion `sha256 63a9bc54…f87d6ba9` (D-302; parent
  `50149f4`). Next: **FBV2-P2-007 — continue rest-of-board routing (next bounded group, same framework).**
  Full analysis:
  [`audits/2026-08-30-p2-006-d304-first-rest-of-board-incremental-increment-front-rgb-promoted.md`](audits/2026-08-30-p2-006-d304-first-rest-of-board-incremental-increment-front-rgb-promoted.md).
  This checkpoint is written in the D-304 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-005 / D-303 (prior checkpoint — PHASE-B BRING-UP):** a governed CTO **CHARACTERIZATION +
  INTEGRITY + SCOPING** milestone on the promoted board — **no copper change, authoritative PCB byte-identical
  (`sha256 63a9bc54…f87d6ba9`), autonomy CONTINUES, no owner decision.** Starting HEAD `01a38a5` (D-302; pushed;
  `origin/master` identical). **(1) Exact Phase-B definition (from the code):** "Phase B" here is the
  battery-block REPLAY / IDEMPOTENCE verification of the D-271 discipline, **NOT** rest-of-board routing —
  `replay_battery_block.py` (verbatim scratch→authoritative promotion), `route_battery_block.py` SECTION 17
  `AQROOT_REPLAY` (independent journal reproduction, frozen order / pinned widths / `passes=2`, on a clean
  scratch), `phaseB_compare.py` (the A-vs-B gate); the driver is **power-tree scoped ONLY**. **(2) Integrity
  re-verified:** `HEAD == origin/master == 01a38a5`, clean; PCB `sha256 63a9bc54…f87d6ba9` / size 1475931;
  **432 tracks / 54 vias / 6 layers / 41 zones / 324 footprints**; journal **77 entries**; **all 432 routed
  tracks are in-scope power-tree nets (0 out-of-scope) → Phase-A battery-block copper ONLY**;
  `router_regression.py` = **ALL 79 CHECKS PASS (G1–G17)**; shared journal not mutated. **(3) The existing
  Phase-B drivers assume a copper-EMPTY base (the sharply-characterized blocker, proven):**
  `replay_battery_block.py:40-42` refuses a non-empty authoritative board (`raise SystemExit`) → post-promotion
  (432 tracks) it can never re-run (role already fulfilled byte-identically by D-302); SECTION-17 replay
  (`:2297`) SKIPS every `role=='TRUNK+ESCAPE'` entry — **exactly the one entry defining the promotion**
  (`BAT_PROTECTED_P U11.2→C36.1, w=1.5, reinforcement=True`) → a replay carries 76/77 items, drops the wall
  closure, would NOT reproduce the board; `phaseB_compare.py` needs a `phaseB.json` never produced. The replay
  machinery predates the D-297/D-299/D-301/D-302 levers and is **stale**. **(4) The promotion is sound
  regardless:** byte-identical to a scratch from a GENUINE full-authority Phase-A gate (`run_003t_full.sh 004b2`,
  `DRIVER_EXIT=0`, PHASE A COMPLETE) — real driver / real order, not a proxy (D-286) — DRC zero new copper
  classes, regression ALL PASS. **(5) Real remaining Phase-B, scoped (next lever):** rest-of-board = **164
  multi-pad nets, 0 routed** across 9 subsystem sheets + rails (GND 259 pads, +3V3 86; 09_COMMUNITY_HEADER 20
  nets, 04_SPI_B_RADIOS_NFC 20, 01_POWER_TREE-beyond-block 18, top 17, 08_BUTTONS_EXPANDERS 10, …) = ~85 % of
  remaining routing with **NO driver** — the next lever is a **new scoped INCREMENTAL driver** that loads the
  promoted board, **PRESERVES the Phase-A copper** (never erase/reroute), routes a bounded isolated net-group
  first, gated by real full-board DRC (D-286), promoted only on a genuine no-casualty / no-new-DRC increment.
  Added `checks/phaseB_bringup_probe_005.py` (READ-ONLY, reproducible; ALL PASS). **Open owner decisions: NONE;**
  `JLCPCB_READINESS` unchanged (~77 %). Next: **FBV2-P2-006 — begin rest-of-board routing.** Full analysis:
  [`audits/2026-08-30-p2-005-d303-phaseB-bringup-characterization-integrity-scope.md`](audits/2026-08-30-p2-005-d303-phaseB-bringup-characterization-integrity-scope.md).
  This checkpoint is written in the D-303 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-004B2 / D-302 (prior checkpoint — FIRST AUTHORITATIVE COPPER):** the **first authoritative
  Phase-A copper promotion** is COMMITTED. The verified `AQROOT_U11_RETARGET`→`C36.1` full-run board
  (`run_004b2_full.log`, `DRIVER_EXIT=0`, PHASE A COMPLETE) becomes the authoritative PCB — **byte-identical**
  to the `checks/w/FULL003T_004b2_u11retarget` scratch (`sha256 63a9bc54…f87d6ba9`): **432 tracks, 54 vias,
  6 copper layers, direction-2 placement** (fingerprint `397dffe1f77e4d10`), **ratsnest 704 (−77)**, 41 zones,
  and a **77-entry `phaseA_journal.json`** (incl. the `U11.2→C36.1` `reinforcement:True` tap that closes the
  D-301 wall as a SHORT ≥1.20 mm on-net reinforcement, not a cross-board trunk). It carries the **regenerated
  DRU** it requires (67→119 rules; the accepted D-249/D-257/D-258/D-263/D-264/D-266/D-269 per-net escape/tap/
  stub/trunk/clearance rule set — **not a relaxation**; the old HEAD DRU is stale because without those named
  rules DRC would spuriously flag legal accepted copper). Real KiCad DRC on the authoritative board =
  `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, unconnected_items:499}` — **ZERO new
  copper DRC classes** (the D-301 scratch `track_width:1` is resolved). **PHASE A COPPER ONLY — NOT ALL ROUTING
  COMPLETE** (ratsnest 704 / unconnected_items 499: Phase B and the remaining nets are unrouted). The
  router-regression harness was made compatible with a routed authoritative board (routine engineering, **not**
  an owner decision): a new copper-CLEAN `scratch_clean()` fixture feeds the primitive vehicles (CASES G2–G6,
  CONFLICTS, G7, G8, G9, G11, G12) while G1/G10 + the real-DRC/probe/judge harnesses keep validating the real
  routed board; CONFLICTS `U18.8`/`U18.9` re-pinned 0.250→**0.245 mm** (U18 moved by the accepted placement;
  still ≪ floor → conflict PRESERVED); new contract **G17** guards the promotion. `router_regression.py` =
  **ALL 79 CHECKS PASS (G1–G17)**, run twice, deterministic; `u11_retarget_probe_004b.py` = ALL PASS.
  **Rollback preserved:** pre-promotion PCB `sha256 2235e273…d642d7e` (parent `56d0ebe`) + tags
  `beta-v2-p2-battery-pre-authoritative` / `beta-v2-p2-pre-sixlayer-authoritative`. Mandated **Opportunity &
  Simplification Scan** (§9a): the fixture split makes the harness robust to every future promotion; **Open
  owner decisions: NONE.** `JLCPCB_READINESS` NOT edited (conservative: keep ~77 %, not fab-ready — Phase-A
  only). Next: **FBV2-P2-005 — Phase B bring-up on the promoted board** (screen full DRC per D-286, promote
  only on a genuine gate PASS). Full analysis:
  [`audits/2026-08-30-p2-004b2-d302-first-authoritative-phasea-copper-promotion-regression-fixture-fix.md`](audits/2026-08-30-p2-004b2-d302-first-authoritative-phasea-copper-promotion-regression-fixture-fix.md).
  This checkpoint is written in the D-302 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-004A / D-301 (prior checkpoint):** a governed **CTO ACCEPT + COMMIT + overall-run FAIL**
  — the `AQROOT_LTCGATE_KO` **path-shaping** lever (a net-foreign central-lane keep-out installed for
  exactly the `LTC_GATE U18.10→Q3.4` join and lifted right after, on the proven `AQROOT_U19CAP`
  mechanism — **NOT a re-order**, which D-300 refuted) was full-authority-gate-run
  (`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 … 004a_ltcgate1`, secs 1500.2,
  `checks/w/phaseA_003t_full_004a_ltcgate1.json`, judged by `w/judge_004a.py`) and proved a
  **GENUINE +1**: vs the D-299/003Y2 baseline connections **72→73**, ratsnest 705/−76 → 704/−77,
  journal 75→76, connected-set diff **GAINED 1 (`LTC_GATE Q3.4↔U18.10`, F.Cu, 2× 0.35 FINE_ESC vias,
  8.556 mm) / LOST 0** — not a swap; vs 003W it also preserves the D-299 U19 pins (LOST 0); final DRC
  **identical** (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1,
  unconnected_items:499}`), no new class, no sub-0.50 non-fine via. The real cause of the wall was
  **D-269 alone** (clearance 0.2803 vs 0.300 mm; FINE_ESC legalises the D-257 via, so no D-249
  track_width violation in the real path). So `AQROOT_LTCGATE_KO` is **ACCEPTED and COMMITTED** (banked
  env-gated / **OFF by default**, byte-identical when unset, pinned by **G15**); production WIP was
  **pruned to the narrow lever** (the bulky ~118-line in-run probe `_ltcgate_probe`/`AQROOT_LTCGATE_PROBE`
  removed; evidence lives in the audit/artifacts). **Copper is NOT promoted** — 004A is the FIRST run to
  close every upstream wall and reach the final `u11_escape()` step, which now FAILs: the terminal wall
  advances to **`U11.2 escape: none exists`** (the `BAT_PROTECTED_P` 1.5 mm high-current trunk endpoint;
  a structural ≥1.20 mm-trunk NO_LEGAL_PATH, the D-273/274/281/282/283 class — not a ~20 µm DRC pinch).
  **Readiness/progress UNCHANGED; autonomy CONTINUES** (no owner decision). Mandated Opportunity &
  Simplification Scan (§9a): the U11.2 wall is reducible (a short on-net ≥1.20 mm tap beats a cross-board
  trunk); no BOM/capability/architecture opportunity forces a change; **Open owner decisions: NONE.** Also
  created at this safe boundary: **`docs/full-beta-v2/DEVICE_SPEC.md`** (authoritative current-product
  spec/index). Next: **FBV2-P2-004B** — the `U11.2` BPP trunk-endpoint retarget lever (§5). This checkpoint
  is written in the D-301 commit; a fresh session must confirm the live tip with `git rev-parse HEAD` and
  `git rev-parse origin/master`.
- **FBV2-P2-003Z / D-300 (this checkpoint):** a governed **CTO FAIL / lever refutation + WIP retirement**
  — the `AQROOT_LTCGATE` **defer-to-congestion** lever (a pure re-order: pull `LTC_GATE U18.10→Q3.4`
  out of section `8b` and re-queue it LAST as a `13z` stage) was full-authority-gate-run
  (`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE=1 … 003z3_ltcgate`, secs 1497.0,
  `checks/w/phaseA_003t_full_003z3_ltcgate.json`, judged by `w/judge_003z.py`) and proved
  **behaviourally identical to D-299/003Y2**: connections 72=72, skipped 101=101, ratsnest 705/−76
  = 705/−76, journal 75=75, connected-set diff **GAINED 0 / LOST 0**, the SAME `LTC_GATE U18.10→Q3.4`
  terminal wall with the SAME `track_width` (D-249 min 1.2000 mm; actual 0.2000 mm) + `clearance`
  (D-269 0.3000 mm; actual 0.2803 mm) rejections, final DRC histogram identical. **A pure re-order is a
  NULL OPERATION on this wall** — the driver's `connect_role` greedily re-takes the identical
  rule-violating central path even queued last. The focused `ltcgate_join_probe_003z.py` was a
  **false-positive proxy** (its post-hoc `connect_role` on the SAVED board found a legal ~10.5 mm west
  detour that the real in-run driver never takes; per D-286 a proxy cannot override the full gate). So
  the lever and its **G15** WIP are **REJECTED/RETIRED** via an exact reverse patch scoped to the two
  tracked files (`git diff -- route_battery_block.py router_regression.py | git apply -R`, NOT a broad
  reset; post-revert `git hash-object` = `HEAD:` blob for each, `git grep` for the retired symbols NO
  match), and the false-positive probe is **retired** (untracked, never committed) so **no artifact
  claims the lever works**. **Copper is NOT promoted** — full Phase-A still FAILs at the unchanged
  `LTC_GATE U18.10→Q3.4` wall; **readiness/progress UNCHANGED; autonomy CONTINUES** (no owner decision).
  Mandated **Opportunity & Simplification Scan** (§9a): no product-capability / BOM / recoverability /
  testability / manufacturing / firmware / UX / future-option opportunity justifies changing
  architecture; **Open owner decisions: NONE.** Next: **FBV2-P2-004A** — the `LTC_GATE U18.10→Q3.4`
  **path-shaping** lever (a central-lane keep-out forcing the proven west detour — NOT a re-order, §5).
  This checkpoint is written in the D-300 commit; a fresh session must confirm the live tip with
  `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-003Y / D-299 (prior checkpoint):** a governed **CTO ACCEPT + COMMIT + overall-run FAIL + HANDOFF**
  — the D-298 U19 CAPACITY lever's **full-authority gate COMPLETED** and it is a **GENUINE +2** connected-set
  gain (NOT the D-296 swap): vs the D-297 003W baseline (conn 70) connections **70→72**, and the connected-set
  diff GAINED **exactly 2** — `N_BATDIV R89.2→U19.6` and `REC_BAT_LOW (node)→U19.7` (both SIG, F.Cu, 2 vias,
  board-legal 0.60/0.30) — with **LOST 0**; `LTC4368_FAULT_N` detours CLEANLY (`R82.1→Q9.1` 77.567 mm, not the
  terminal wall); final DRC **identical** to 003W, no sub-0.50 non-fine via. So `AQROOT_U19CAP` is **ACCEPTED and
  COMMITTED** (banked env-gated / **OFF by default**, byte-identical when unset, pinned by **G14**). **Copper is
  NOT promoted** — full Phase-A still FAILs, the terminal wall newly ADVANCING **past the whole U19 field** to
  `LTC_GATE U18.10→Q3.4` (candidate join paths **DRC-gate-rejected** by the frozen **D-249** BPP 1.20 mm
  trunk-width and **D-269** BAT_MAIN 0.300 mm clearance rules — actual 0.20 mm / 0.2803 mm; NOT `NO_PATH`). The
  gate artifact is `checks/w/phaseA_003t_full_003y2_u19cap.json` (secs 1463.2, judged by `w/judge_003y2.py`); the
  shared `phaseA_journal.json` was restored byte-identical to HEAD and no process remains. **Readiness/progress
  UNCHANGED; autonomy CONTINUES** (no owner decision). Next: **FBV2-P2-003Z** — the `LTC_GATE U18.10→Q3.4` join
  corridor lever (§5). This checkpoint is written in the D-299 commit; a fresh session must confirm the live tip
  with `git rev-parse HEAD` and `git rev-parse origin/master`.
- **FBV2-P2-003X / D-298 (prior checkpoint):** a governed **CTO IMPLEMENT + SCREEN + HANDOFF** — the
  bounded U19 CAPACITY lever (`AQROOT_U19CAP`: reserve the U19.7/U19.6 shared east escape lane so
  `LTC4368_FAULT_N` detours, and close `REC_BAT_LOW U19.7` before `N_BATDIV U19.6`) is implemented
  env-gated / **OFF by default**, pinned by regression **G14**, and **screened DRC-clean** on the real
  003W full-run board (both boxed U19 pins escape SIMULTANEOUSLY onto bare In3/In2 with the only
  board-legal 0.65/0.40 via — a capacity ADD, categorically distinct from the refuted D-296 swap).
  **Copper is NOT promoted** — the ~22-min full-authority gate (net +2 vs swap; FAULT_N clean detour)
  has not run (exceeds the ACP cap; may not be backgrounded). Source is left **uncommitted** (docs
  committed) per the 003X discipline; **autonomy CONTINUES** (no owner decision raised). Next:
  **FBV2-P2-003Y** executes the gate (§5).
- **FBV2-P2-003W / D-297 milestone commit (prior checkpoint):** a governed **ACCEPT of a
  SECONDARY lever + a governed FAIL of the overall Phase-A run** (source + docs + probe commit);
  **autonomy CONTINUES** (a normal Phase-A FAIL is not a stop reason; no owner decision raised).
  003W implemented the D-295/D-296 SECONDARY lever — an env-gated (`AQROOT_U18BPP_JOIN`, **OFF by
  default**) override that completes the `BAT_PROTECTED_P U18.8 → R75.2` reserve **JOIN on In3**
  instead of the severed In2 lane — as a +25/−1-line change to `checks/route_battery_block.py`, pinned
  by a **G13** regression contract in `checks/router_regression.py` and the measured-record probe
  `checks/u18_i3_join_probe_003w.py`. **The wall (D-294/295):** at the direction-2 placement
  `t_a_r77e15n10_r79e15n10` the two 0.35/0.20 **THROUGH** reserve vias land at `R75.2`(2.800,66.800)
  and `U18.8`(7.200,66.500) on In2, and their In2 JOIN is `NO_PATH` — a `BAT_RAW` 0.600 mm
  current-path wall runs vertically on In2 at x≈6.4→6.65 (y 50.45→70.40), severing the west→east
  lane. **The lever:** the reserve vias are THROUGH vias (copper on every layer), so the join is
  electrically identical on In2 or In3; **In3.Cu is a routable six-layer signal layer**
  (`ROUTABLE[6]=('F','B','I2','I3')`) that is **EMPTY across the whole corridor** on the real
  full-run board (2 In3 tracks board-wide, none here; no In3 pour — only the In1/In4 GND planes), so
  `AQROOT_U18BPP_JOIN=I3` completes the ONE branch on In3 with **NO new via, NO DRU/floor change, NO
  topology change**; unset → the join stays on `va[2]` (In2), byte-identical to every prior run. **The
  probe** (on the actual full-run routed board, throwaway copy): In2 join `NO_PATH`, In3 join **ok
  4.410 mm**, real KiCad DRC **ZERO new classes**, `via_dangling` **1→0**. **The full authority gate**
  (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`, secs 1272.5) vs the D-294 baseline
  `w/phaseA_003t_full_e15n10cto.json`: connections **69→70** (+1), skipped-already-connected **98→99**
  (+1 — one downstream `BAT_PROTECTED_P` pad now found already-joined on the closed net; a positive
  sign, not a loss), ratsnest **708/−73 → 707/−74**, journal **72→73** (+1: `JOIN U18.8→R75.2` layer
  **I3**, 4.410 mm, **0 vias**), DRC `via_dangling` **1→0** with **no new class**
  (`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1,
  unconnected_items:499}`), terminal fatal wall **UNCHANGED** (`REC_BAT_LOW U19.7→(node)
  NO_LEGAL_ESCAPE`, `N_BATDIV U19.6` next-in-line). **The decisive diff is a STRICT PURE GAIN:** the
  entire journal delta is **exactly one added JOIN entry with NOTHING lost** — the categorical
  opposite of D-296's 1-for-1 swap; the In3 join takes routing capacity from **no other net** (In3 is
  unused), so no casualty is possible and none occurs. **Ruling:** the SECONDARY lever is a genuine,
  board-legal, verified net gain — **ACCEPTED** and retained env-gated/OFF-by-default in tracked
  source (byte-identical when unset), pinned by G13 + the probe. **But copper is NOT promoted:**
  Phase-A copper promotes only on a full-authority PASS (D-286), and the run still FAILs on the
  unchanged saturated U19 field — so the authoritative board stays six layers / 0 tracks / 0 vias and
  **readiness/progress DO NOT move.** D-297 **banks** the U18.8 closure in source: once the U19 field
  is separately enlarged, this lever (ON) yields the U18.8 join for free (no new via, no new DRC).
  **No copper, no placement, no rule, no floor, no topology/footprint/outline change; no DRC absorbed;
  no promotion.** `/home/aqroot8/.aqroot-autopilot-stop` is ABSENT; autonomy continues with
  **FBV2-P2-003X** (§5) — a bounded U19 capacity lever for the simultaneous `REC_BAT_LOW U19.7` +
  `N_BATDIV U19.6` closure. Prior milestone: `27f9790` (D-296, 003V PRIMARY reservation family
  refuted). This checkpoint is written in the same commit; a fresh session must confirm the live tip
  with `git rev-parse HEAD` and `git rev-parse origin/master`.
- **Prior FBV2-P2-003V / D-296 milestone:** a governed **FAIL / primary-family refutation** commit
  (docs only); **autonomy CONTINUES**. 003V implemented the D-295 PRIMARY lever — an env-gated
  (`AQROOT_U19_RESV`, OFF by default) reservation of `REC_BAT_LOW U19.7`'s B.Cu escape scored toward
  Q7.1 — and full-gate-ran it twice. **RESV (0.35/0.20)** is behaviourally identical to D-294 (the
  corridor-less sub-minimum via is rejected on `via_diameter`/`annular_width`, the reservation is
  dropped, the run falls through unchanged; connected-set diff EMPTY both ways). **RESV2 (0.60/0.30
  board-legal)** FIRES and CLOSES U19.7 (rung self-corrects to the ordinary Default 0.60/0.30) — but
  it is a bounded **ordering trade**: conn 69 / skip 98 / ratsnest 708/−73 all unchanged, DRC
  identical, the terminal wall merely MOVES to `N_BATDIV U19.6`. **The decisive diff (D-294→RESV2) is
  a strict 1-for-1 swap:** GAINED `REC_BAT_LOW U19.7→Q7.1`, LOST `REF_POL TP24.1→U19.2`, count 68→68 —
  the U19 field is capacity-saturated, so reserving U19.7's lane only chooses which neighbour is
  abandoned. Positive finding recorded (the mechanism is REAL, U19.7 closable in principle,
  board-legal) but a swap is not a net gain, so per D-286 nothing promotes copper. **The
  `AQROOT_U19_RESV` source WIP was RETIRED** via an exact reverse patch (`git apply -R`; worktree blob
  `bba62d35…` = `HEAD:checks/route_battery_block.py`, `git grep U19_RESV` no match). No source/copper/
  placement/rule change survived; no DRC absorbed; no promotion. Prior milestone: `a2e27fc` (D-295).
- **Prior FBV2-P2-003U / D-295 milestone:** a governed **characterization / NO-PROGRESS + HANDOFF**
  commit (docs only); autonomy CONTINUES. 003U proved both D-294 walls are FULL-RUN-EMERGENT
  ordering/congestion casualties and NO cheap vehicle judges either at the direction-2 placement. The
  PRIMARY (`REC_BAT_LOW U19.7`) was diagnosed EXACTLY and shown REDUCIBLE-in-principle (it escaped
  cleanly in 003O as `U19.7→Q7.1` F.Cu 14.907 mm; direction-2's +2-connection congestion **swapped
  `VREC_VCC`'s two segments' layers** — `U19.8→C60.1` went B.Cu(0 via)→F.Cu(2 via) — so U19.8's
  pad-escape now occupies the F lane immediately south of U19.7 that carried U19.7 in 003O; `U19.8`
  ×26 the dominant blocker; U19.7 is a greedy-tightest-first casualty and, as a `(node)` join,
  ineligible for the D-278 inner hop guarded `and not node`). The SECONDARY (U18.8 I2 join corridor)
  is a full-congestion I2 pinch. The ~22-min governing gate cannot run foreground under the ACP
  10-min cap, so 003U delivered a precise CTO handoff. No source/copper/placement/rule change; no DRC
  absorbed; no promotion. Prior milestone: `36662db` (D-294).
- **HEAD == origin/master:** yes (committed and pushed at milestone closeout).
- **Prior milestones (full detail in §4 and CTO_DECISIONS):** `27f9790` D-296 (003V) PRIMARY
  reservation family refuted / WIP retired; `a2e27fc` D-295 (003U) two-walls characterization +
  handoff; `36662db` D-294 (003T) direction-2 executed / full gate FAIL; `9c708f3` D-293 owner
  approval of direction 2.

## 2. Mission
- Deliver Full Beta v2 to **READY FOR JLCPCB** — a fabricable, assembly-ready
  authoritative board with all governing routing / DRC / ERC / connectivity / safety
  gates passing and the final JLCPCB deliverables generated and reviewed.
- Terminal condition: **READY FOR JLCPCB**.

## 3. Current phase / gate
- **Phase P2 — battery/power-block Phase-A routing is COMPLETE and PROMOTED (D-302).** The authoritative
  board carries **432 tracks / 54 vias / 6 layers** of Phase-A battery-block copper (all in-scope power-tree
  nets, 0 out-of-scope), DRC zero new copper classes, `router_regression` ALL 79 PASS.
- **FBV2-P2-005 / D-303 defined "Phase B" and scoped the real remaining routing.** In-repo "Phase B"
  (`replay_battery_block.py` / SECTION-17 `AQROOT_REPLAY` / `phaseB_compare.py`) is the battery-block
  replay/idempotence verification and is now **stale + assumes a copper-empty base** (do NOT naively re-run;
  see §1). The promotion is sound without it (rests on a genuine full-authority gate, D-286).
- **Current fabrication blocker (updated by D-310): rest-of-board routing — IN PROGRESS, incrementally.**
  The reusable incremental router/promoter (`checks/incremental_router.py`) is proven across SEVEN promoted
  increments: of the 164 rest-of-board multi-pad nets, **13 are routed (FRONT_RGB 3 + ACC 2 + DISP 1 + IMU 1 +
  FRONT_RGB_LED 3 + IR_RX_VS 1 + TOUCH_CTL 2), 151 remain UNROUTED** across 9 subsystem sheets + rails; ratsnest
  **685**. Each future group is added to the `incremental_router.py` registry and routed → gated (real full-board
  DRC, D-286) → promoted on a genuine no-casualty / no-new-DRC increment (FBV2-P2-013, §5). The board carries
  Phase-A battery-block copper (432 trk / 54 via) **plus** the seven rest increments (129 trk / 6 via). Fingerprints
  for all increment probes are centralised in `checks/live_fingerprint.py` (D-309). **D-310 gave `connect_cross`
  existing-via awareness (qrouter._scan omits `PCB_VIA`; injected per-route) + a bounded `via_offset`, breaking
  the U2 escape wall** (`qrouter.py` untouched). Characterised walls (do NOT naively retry): `U11_PROG`/`PWR_SENSE`
  (D-307, hard pad-escape/corridor). **U2 escape family now UNLOCKED** — `TOUCH_RST_N`/`TOUCH_INT_N` ROUTED
  (D-310); `AMP_SD_MODE` (U2.7) / `SD_CARD_DETECT_N` (U2.11) measured clean at 2.5 mm offset, ready for the next
  increment.
- **Historical Phase-A blocker context (all CLOSED under D-302), updated by D-301.** Direction-2 (D-294) plus the accepted bounded
  levers (D-297 U18.8 In3-join, D-298/D-299 U19CAP, **D-301 LTC_GATE_KO**) have resolved the west/BAT_RAW,
  U18.8, the saturated U19 dead-cell field **and** the `LTC_GATE U18.10→Q3.4` join; **the SINGLE remaining
  Phase-A fabrication blocker is now `U11.2 escape: none exists`** — the `BAT_PROTECTED_P` **1.5 mm
  high-current trunk endpoint** (`u11_escape()`, `route_battery_block.py:2149`, run LAST after the whole
  queue). It lays a dedicated ≥1.20 mm B.Cu trunk from `U11.2`=(66.400,78.200) (EAST node cluster) to
  `D9.1`=(11.350,72.500) (WEST mass) — a **~55 mm cross-board wide trunk**. The BPP backbone is otherwise
  connected (R75.2→bridge→C36.1 node; C58.1→D9.1 TAP; C36/C25/C58/D9.1 already joined via R75.2; U11.2 has
  its 0.20 mm SENSE tie, not a current path). The single ≤~1.30 mm central channel is already occupied by
  the south bridge + R75.2 trunk, so a second parallel 1.50 mm trunk has **NO legal path** — a **structural
  ≥1.20 mm-trunk NO_LEGAL_PATH** (the D-273/274/281/282/283 class), **NOT** a ~20 µm DRC pinch like
  LTC_GATE. It is reducible in principle within CTO scope: U11.2 is IN the east node (already on-net with
  D9.1 via the bridge), so a short on-net ≥1.20 mm tap should replace the cross-board trunk (FBV2-P2-004B,
  §5). Status of the prior walls (all now closed under the full gate):
  - **`LTC_GATE U18.10→Q3.4` — CLOSED under the full gate (D-301), lever committed.** The
    `AQROOT_LTCGATE_KO` path-shaping keep-out forces the join onto the clean F.Cu west detour (8.556 mm),
    a genuine +1 (LOST 0), no new DRC; the real cause was D-269 alone (~19.7 µm), not D-249. ACCEPTED and
    COMMITTED env-gated / OFF-by-default (G15).
  - **U18.8 (`BAT_PROTECTED_P`) — CLOSED IN PRINCIPLE, banked (D-297).** The In3 reserve-JOIN lever
    is an ACCEPTED, board-legal +1 net gain (`U18.8→R75.2` on In3, 4.410 mm, 0 vias, `via_dangling`
    cleared, no new DRC). It is retained OFF-by-default in source and turns ON in the 003X full run;
    it is NOT yet promoted because the full run still fails on U19.
  - **REF_POL R87.2 F-corridor wall — PAST under direction-2** (+2 connections vs 003O); re-verify
    downstream on a full PASS.
  - **U19 dead-cell field — CLOSED under the full gate (D-299), lever committed.** D-296 proved a
    single-pin reservation only SWAPS the casualty; D-298 built the capacity ADD (`AQROOT_U19CAP`:
    reserve the U19.7/U19.6 shared east lane so `LTC4368_FAULT_N` detours + close U19.7 before U19.6);
    the FBV2-P2-003Y full-authority gate confirmed a **genuine +2** (both `REC_BAT_LOW U19.7` and
    `N_BATDIV U19.6` close, LOST 0, board-legal 0.60/0.30 vias, FAULT_N clean, DRC identical). ACCEPTED
    and COMMITTED env-gated / OFF-by-default (G14); re-verify downstream on a full PASS.
  - **`LTC_GATE U18.10→Q3.4` — the terminal blocker (D-299), re-order REFUTED (D-300).** Candidate paths
    DRC-gate-rejected by the frozen D-249 (BPP 1.20 mm trunk width) and D-269 (BAT_MAIN 0.300 mm
    clearance) rules. D-300 (003Z) tested the `AQROOT_LTCGATE` **defer-to-congestion re-order** (route the
    join LAST) under the full gate → **behaviourally identical to D-299** (gained 0 / lost 0, same wall,
    same rejections): a pure re-order is a **null operation** here — `connect_role` re-takes the identical
    central path even queued last, and the focused probe that predicted a west detour was a false-positive
    proxy. The wall stays a **bounded path-shaping** lever within CTO scope: force the proven ~10.5 mm west
    detour by blocking the central lane (FBV2-P2-004A, §5). NOT an owner decision.
  - **BAT_RAW R89.1/R86.2 divider taps** — a capacity symptom, not a width lever; re-verify on a full
    PASS.

## 4. Last accepted milestone
- **Latest milestone — FBV2-P2-004A · Decision:** **D-301** · **Result (a governed ACCEPT + COMMIT +
  overall-run FAIL, no copper):** THE `AQROOT_LTCGATE_KO` PATH-SHAPING LEVER'S FULL-AUTHORITY GATE
  CONFIRMED A **GENUINE +1** (closes `LTC_GATE U18.10→Q3.4`, LOST 0, no new DRC) — so the minimum
  OFF-by-default lever + **G15** are **ACCEPTED and COMMITTED** (byte-identical when unset); COPPER IS NOT
  PROMOTED because full Phase-A still FAILs at the newly-exposed `U11.2` BPP trunk wall (the FIRST run to
  reach the final `u11_escape()` step), so readiness/progress DO NOT MOVE. Gate:
  `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 bash w/run_003t_full.sh 004a_ltcgate1 …` →
  `checks/w/phaseA_003t_full_004a_ltcgate1.json` (secs 1500.2, driver exited clean; shared journal restored
  byte-identical to HEAD; no process remains), judged by `w/judge_004a.py`. vs 003Y2: conn 72→73, ratsnest
  705/−76→704/−77, journal 75→76, connected-set diff GAINED 1 (`LTC_GATE Q3.4↔U18.10`, F.Cu, 2× 0.35
  FINE_ESC vias, 8.556 mm) / LOST 0; vs 003W GAINED 3 / LOST 0 (preserves the D-299 U19 pins); DRC
  identical, no sub-0.50 non-fine via. Production WIP pruned to the narrow lever (bulky in-run probe
  removed). A governed CTO ACCEPT + COMMIT + overall-run FAIL, NOT an owner decision; autonomy CONTINUES;
  no copper/placement/rule/floor/topology change, no DRC absorbed, no promotion, D-275 and D-277..D-300
  preserved. Tests: `router_regression.py` ALL PASS incl. **G15** (lever OFF by default → byte-identical;
  `=1` arms the validated default; explicit override parses; scoped to `LTC_GATE U18.10→Q3.4`, KO lifted
  after). Also created: **`docs/full-beta-v2/DEVICE_SPEC.md`**. Evidence of record: audit
  [`audits/2026-08-30-p2-004a-d301-ltcgate-ko-path-shaping-lever-full-gate-plus1-accepted-committed-u11-trunk-wall.md`](audits/2026-08-30-p2-004a-d301-ltcgate-ko-path-shaping-lever-full-gate-plus1-accepted-committed-u11-trunk-wall.md);
  committed source (`checks/route_battery_block.py` `AQROOT_LTCGATE_KO` lever, `checks/router_regression.py`
  G15); gitignored full-gate artifact (`checks/w/phaseA_003t_full_004a_ltcgate1.json`, `w/judge_004a.py`).
- **Prior milestone — FBV2-P2-003Z · Decision:** **D-300** · **Result (a governed FAIL, no copper):**
  THE `AQROOT_LTCGATE` DEFER-TO-CONGESTION LEVER'S FULL-AUTHORITY GATE COMPLETED AND IT IS
  **BEHAVIOURALLY IDENTICAL TO D-299** (GAINED 0 / LOST 0, SAME `LTC_GATE U18.10→Q3.4` TERMINAL WALL,
  SAME D-249 track_width / D-269 clearance REJECTIONS, IDENTICAL FINAL DRC) — SO A PURE RE-ORDER IS A
  **NULL OPERATION** ON THIS WALL: THE LEVER AND ITS **G15** WIP ARE **REJECTED/RETIRED** AND THE
  FALSE-POSITIVE PROBE IS **RETIRED**; COPPER IS NOT PROMOTED, READINESS/PROGRESS UNCHANGED, AUTONOMY
  CONTINUES. The gate `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE=1 bash w/run_003t_full.sh
  003z3_ltcgate …` → `checks/w/phaseA_003t_full_003z3_ltcgate.json` (secs 1497.0, driver exited clean;
  shared `phaseA_journal.json` restored byte-identical to HEAD; no process remains), judged by
  `python3 w/judge_003z.py`. vs the 003Y2 baseline (D-299): connections 72=72, skipped 101=101, ratsnest
  705/−76 = 705/−76, journal 75=75, connected-set diff GAINED 0 / LOST 0; the failing rung is the same
  two frozen owner rules (`track_width` D-249 min 1.2000 mm actual 0.2000; `clearance` D-269 0.3000 mm
  actual 0.2803); no sub-0.50 non-fine via. Deferring the join to route LAST changed nothing — the
  driver's `connect_role` greedily re-takes the identical rule-violating central path. The probe
  (`ltcgate_join_probe_003z.py`) predicted a legal ~10.5 mm west detour via post-hoc `connect_role` on
  the SAVED board, but that never reproduces the real in-run state — a D-286 proxy the full gate
  overrode. RETIRED via exact reverse patch scoped to `checks/route_battery_block.py` +
  `checks/router_regression.py` (`git apply -R`; post-revert `git hash-object` = `HEAD:` blob for each;
  `git grep LTCGATE|13z|ltcgate_join_probe` NO match); probe removed; `router_regression.py` ALL PASS
  (G12/G13/G14; G15 gone). Mandated Opportunity & Simplification Scan recorded (§9a): no
  capability/BOM/architecture opportunity; next best lever is path-shaping (force the west detour), the
  bounded neighbour placement ECO is the fallback; **Open owner decisions: NONE.** A governed CTO FAIL,
  NOT an owner decision (no floor relaxed, no frozen part moved, no DRU change, no D-249/D-269
  relaxation); no copper/placement/rule/topology change, no DRC absorbed, no promotion, D-275 and
  D-277..D-299 preserved. Evidence of record: audit
  [`audits/2026-08-30-p2-003z-d300-ltcgate-defer-to-congestion-lever-refuted-false-positive-probe-retired.md`](audits/2026-08-30-p2-003z-d300-ltcgate-defer-to-congestion-lever-refuted-false-positive-probe-retired.md);
  gitignored evidence (`checks/w/phaseA_003t_full_003z3_ltcgate.json`, `w/judge_003z.py`,
  `w/FULL003T_003z*_ltcgate/`, `w/TEST003Z_*/`, `w/run_003z_ltcgate.log`).
- **Last ACCEPTED milestone — Task:** FBV2-P2-003Y · **Decision:** **D-299** · **Result:** THE D-298 U19 CAPACITY LEVER'S
  FULL-AUTHORITY GATE COMPLETED AND IT IS A **GENUINE +2** CONNECTED-SET GAIN (NOT THE D-296 SWAP) — SO
  `AQROOT_U19CAP` IS **ACCEPTED AND COMMITTED** (banked env-gated / OFF-by-default, byte-identical when
  unset, pinned by **G14**); BUT COPPER IS NOT PROMOTED BECAUSE FULL PHASE-A STILL FAILs, THE TERMINAL
  WALL NEWLY ADVANCING PAST THE WHOLE U19 FIELD TO `LTC_GATE U18.10→Q3.4`, SO READINESS/PROGRESS DO NOT
  MOVE. The governing foreground run `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 bash w/run_003t_full.sh
  003y2_u19cap …` → `checks/w/phaseA_003t_full_003y2_u19cap.json` (secs 1463.2, driver exited clean;
  shared `phaseA_journal.json` restored byte-identical to HEAD; no process remains), judged by
  `checks/w/judge_003y2.py`. vs the D-297 003W baseline `w/phaseA_003t_full_003w_u18bpp_i3.json` (conn
  70): connections **70→72**, skipped **99→101**, ratsnest **707/−74→705/−76**, journal **73→75**; the
  connected-set diff GAINED **exactly 2** — `N_BATDIV R89.2→U19.6` and `REC_BAT_LOW (node)→U19.7` (both
  SIG, F.Cu, 2 vias, board-legal 0.60/0.30) — and LOST 0 (`U19.7` 15.621 mm, `U19.6` 9.52 mm). Both
  boxed U19 pins close SIMULTANEOUSLY for a strict +2 with nothing lost — the categorical opposite of
  D-296's 1-for-1 swap. `LTC4368_FAULT_N` DETOURS CLEANLY (all three branches on B.Cu; `R82.1→Q9.1`
  77.567 mm; not the terminal wall). Final DRC histogram IDENTICAL to 003W (`{hole_clearance:5,
  lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}`, no new
  class/increase); no sub-0.50 non-fine via (run via diameters 0.35/0.60/0.65/0.80). The new terminal
  wall `LTC_GATE U18.10→Q3.4` is candidate-paths-found-but-DRC-gate-rejected by the frozen D-249 (BPP
  1.20 mm, actual 0.20) and D-269 (BAT_MAIN 0.300 mm, actual 0.2803) rules — a bounded reducible
  corridor/ordering wall within CTO scope. A governed CTO ACCEPT + COMMIT + overall-run FAIL, NOT an
  owner decision (no floor relaxed, no frozen part moved, no DRU change); autonomy CONTINUES; no
  copper/placement/rule/floor/topology change, no DRC absorbed, no promotion, D-275 and D-277..D-298
  preserved. Tests: `router_regression.py` ALL PASS incl. **G14** (lever OFF by default → byte-identical;
  `AQROOT_U19CAP` activates; reserved-lane geometry spans U19.7/U19.6; hooks scoped to the U19 east lane
  + REC_BAT_LOW-before-N_BATDIV). Evidence of record: audit
  [`audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md`](audits/2026-08-30-p2-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md);
  committed source (`checks/route_battery_block.py` `AQROOT_U19CAP` lever, `checks/router_regression.py`
  G14); gitignored full-gate artifact (`checks/w/phaseA_003t_full_003y2_u19cap.json`, `w/judge_003y2.py`).
- **Prior milestone — FBV2-P2-003W · Decision:** **D-297** · **Result:** THE SECONDARY U18.8 I2-JOIN LEVER
  (the D-295/D-296 HANDOFF) COMPLETES `BAT_PROTECTED_P U18.8→R75.2` ON In3 FOR A **GENUINE +1
  CONNECTED-SET GAIN** — A PURE JOIN WITH NO CASUALTY, NO NEW VIA, NO NEW DRC CLASS, AND THE LONE
  `via_dangling` CLEARED — SO IT IS **ACCEPTED** AND RETAINED ENV-GATED / OFF-BY-DEFAULT IN TRACKED
  SOURCE; BUT COPPER IS NOT PROMOTED (THE FULL RUN STILL FAILs ON THE SATURATED U19 FIELD), SO
  READINESS/PROGRESS DO NOT MOVE. The reserve vias are THROUGH vias, so the join is electrically
  identical on In2/In3; In3.Cu is a routable six-layer signal layer (`ROUTABLE[6]=('F','B','I2','I3')`)
  EMPTY across the whole corridor (only In1/In4 GND pours), so `AQROOT_U18BPP_JOIN=I3` completes the
  ONE branch on In3 within D-257/D-266 mechanics. Probe (on the actual full-run routed board): In2
  `NO_PATH`, In3 **ok 4.410 mm**, real KiCad DRC ZERO new classes, `via_dangling` 1→0. Full gate
  (`w/phaseA_003t_full_003w_u18bpp_i3.json`, secs 1272.5) vs the D-294 baseline
  `w/phaseA_003t_full_e15n10cto.json`: connections **69→70**, skipped-already-connected **98→99**,
  ratsnest **708/−73→707/−74**, journal **72→73** (+1 `JOIN U18.8→R75.2` I3 4.410 mm 0 vias),
  `via_dangling` **1→0** with no new DRC class, terminal fatal wall UNCHANGED (`REC_BAT_LOW U19.7`,
  `N_BATDIV U19.6` next). The entire journal delta is EXACTLY one added JOIN with NOTHING lost — the
  opposite of D-296's swap; the In3 join takes capacity from no other net (In3 unused). A governed CTO
  ACCEPT + overall-run FAIL, NOT an owner decision (no floor relaxed, no frozen part moved, direction-2
  not exhausted); autonomy CONTINUES; no copper/placement/rule/floor/topology change, no DRC absorbed,
  no promotion, D-275 and D-277..D-296 preserved. Tests: `router_regression.py` ALL PASS incl. new
  **G13** (In3 routable; lever OFF by default → byte-identical; `=I3` activates; non-I2/I3 never
  activates; override scoped to exactly `BAT_PROTECTED_P U18.8→R75.2`); `u18_i3_join_probe_003w.py`
  ALL PASS. Evidence of record: audit
  [`audits/2026-08-30-p2-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md`](audits/2026-08-30-p2-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md);
  committed source (`checks/route_battery_block.py`, `checks/router_regression.py` G13,
  `checks/u18_i3_join_probe_003w.py`); gitignored scratch (`checks/w/phaseA_003t_full_003w_u18bpp_i3.json`,
  `w/FULL003T_e15n10cto/`, `w/TEST003W_PROBE/`, `w/run_003t_full.sh`,
  `w/cand_003t/t_a_r77e15n10_r79e15n10.json`).
- **Prior milestone — FBV2-P2-003V · Decision:** **D-296** · **Result:** THE PRIMARY U19.7
  ESCAPE-RESERVATION LEVER (the D-295 handoff) FIRES AND CLOSES U19.7 WITH A BOARD-LEGAL 0.60/0.30
  VIA, BUT IT IS A BOUNDED ORDERING TRADE WITH NO CONNECTED-SET PROGRESS — IT MERELY CHOOSES WHICH PIN
  OF THE SATURATED U19 FIELD IS THE CASUALTY (RESV2 GAINED `REC_BAT_LOW U19.7→Q7.1`, LOST `REF_POL
  TP24.1→U19.2`; conn 69/skip 98/ratsnest 708/−73 all unchanged; DRC identical; wall moves U19.7→U19.6;
  requested-connected 68→68). RESV (0.35/0.20) is behaviourally identical to D-294 (illegal
  sub-minimum via dropped; diff EMPTY both ways). REJECTED for production; the `AQROOT_U19_RESV` source
  WIP RETIRED via exact reverse patch (worktree blob `bba62d35…` = `HEAD:checks/route_battery_block.py`;
  `git grep U19_RESV` no match). Positive finding preserved (mechanism real, U19.7 closable in
  principle, board-legal). A governed FAIL, NOT an owner decision; autonomy CONTINUES; no
  source/copper/placement/rule change, no DRC absorbed, no promotion, D-275 and D-277..D-295 preserved.
  Evidence of record: audit
  [`audits/2026-08-30-p2-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md`](audits/2026-08-30-p2-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md);
  gitignored evidence (`checks/w/phaseA_003t_full_003v_u19resv.json`, `…_u19resv2.json`,
  `w/FULL003T_003v_u19resv*/`, `w/TEST003V_U19RESV/`).
- **Prior milestone — FBV2-P2-003U · Decision:** **D-295** · **Result:** THE TWO D-294 WALLS ARE
  FULL-RUN-EMERGENT ORDERING/CONGESTION CASUALTIES — NO CHEAP VEHICLE JUDGES EITHER AT THE DIRECTION-2
  PLACEMENT — AND THE PRIMARY (`REC_BAT_LOW U19.7`) IS DIAGNOSED EXACTLY AND SHOWN
  REDUCIBLE-IN-PRINCIPLE; THE GOVERNING ~22-min FULL GATE CANNOT RUN FOREGROUND UNDER THE ACP 10-min
  CAP, SO 003U DELIVERS A PRECISE CTO HANDOFF. A governed CTO characterization / NO-PROGRESS + HANDOFF,
  NOT an owner decision; autonomy CONTINUES; no source/copper/placement/rule change, no DRC absorbed,
  no promotion, D-275 and D-277..D-294 preserved. Evidence of record: audit
  [`audits/2026-08-30-p2-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md`](audits/2026-08-30-p2-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md).
- **Prior milestone — FBV2-P2-003T · Decision:** **D-294** · **Result:** DIRECTION 2 (D-293)
  EXECUTED — A FOCUSED MINIMUM CANDIDATE (`t_a_r77e15n10_r79e15n10`) GENUINELY EXISTS, BUT THE
  GOVERNING FULL AUTHORITY GATE FAILs, SO NO CANDIDATE IS PROMOTABLE. Direction-2 is PRODUCTIVE (+2
  connections vs 003O, `REF_POL R87.2` wall now past) but INCOMPLETE (U18.8 I2 join `NO_PATH`; new
  terminal `REC_BAT_LOW U19.7 NO_LEGAL_ESCAPE`). A governed CTO FAIL, NOT an owner decision; autonomy
  CONTINUES; no promotion, D-275 and D-277..D-293 preserved. Evidence: audit
  [`audits/2026-08-30-p2-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md`](audits/2026-08-30-p2-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md).
- **Prior milestone — FBV2-P2-003S · Decision:** **D-292** · **Result:** THE OWNER-APPROVED BOUNDED
  LTC4368/R75 PLACEMENT MICRO-ECO (D-291) IS SCREENED TO EXHAUSTION — NO BOUNDED U18/R75 PLACEMENT
  LEGALLY CO-CLOSES THE U18 ESCAPE FIELD (a both-edges current-path footprint geometry). A governed
  CTO FAIL that re-raised the OWNER decision (resolved by D-293). Evidence: audit
  [`audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md`](audits/2026-08-29-p2-003s-d292-u18-r75-placement-microeco-exhausted.md).
- **Prior milestones — D-290/D-289/D-288/D-287/D-286** (full detail in CTO_DECISIONS and the audits):
  D-290 the last routing-only U18 co-closure lever refuted (owner decision, resolved by D-293);
  D-289 the 003P WIP retired and U18 co-closure refuted; D-288 the D-275 south-bridge entry-array
  two-layer tie fixed (`via_dangling`-clean, electrical pass); D-287 direction-1 space exhausted
  (27/27); D-286 the gate baseline measured on the actual complete pre-copper placement (regression
  G12).

## 5. Next task — FBV2-P2-013 (continue rest-of-board routing, next bounded group)

- **Where 012 left it (D-310).** SEVEN increments promoted; **151 of 164 rest nets unrouted**; authoritative
  `sha256 856f7a8a…0a197114` (561 trk / 60 via / ratsnest 685 / journal 96). All proven classes: same-layer
  (B.Cu/F.Cu no via), single-via + multi-via cross-layer, multi-terminal MST, **and now the bounded U2-escape
  via-site offset + existing-via-aware `connect_cross`** (D-310; `qrouter.py` untouched). Fingerprint pin
  centralised in `checks/live_fingerprint.py`.
- **The lever (FBV2-P2-013) — the U2 escape family is UNLOCKED.** (1) **Complete the U2 escape family.**
  `AMP_SD_MODE` (audio amp SD/mode strap, U2.7) and `SD_CARD_DETECT_N` (microSD card-detect, U2.11) both measured
  clean at the 2.5 mm `via_offset` (via↔via 2.602 / 3.850 mm to the nearest barrel); a coherent next increment —
  add `via_offset` to their `GROUPS` entries (already annotated) and route → gate; verify each on the real gate
  (long hauls, `SD_DETECT` ~68 mm, may surface track-level congestion elsewhere). (2) Else another **clean local
  no-via/single-via group** (screen `w/screen_010.py`; e.g. `RESERVED_SPARE` U23-local B.Cu 3-pad, or verify
  `DIO2_TXEN` U8 intra-chip strap is a control tie not RF matching); the XGPIO0…9 bank is a real 10-net target but
  a ~55 mm cross-board haul (screen its corridor first). Promote **only a genuine no-casualty / no-new-DRC
  increment** (the gate enforces this); add a G-contract + a focused probe per accepted group and bump
  `live_fingerprint.py` once. All floors ENFORCED; no DRU/rule relaxation, no D-290 reauth, no
  topology/footprint/outline change. `U11_PROG`/`PWR_SENSE` remain characterised hard walls (do NOT re-attempt
  naively).
- **(historical) Next task as of FBV2-P2-007 (continue rest-of-board routing, next bounded group)**
- **Where 006 left it (D-304).** The reusable incremental router/promoter `checks/incremental_router.py`
  EXISTS and is proven: it loaded the D-302 promoted board, routed the FRONT_RGB indicator group (3 nets, 20
  B.Cu tracks, no via) with a real full-board gate (Phase-A copper preserved exactly, 0 casualty, ratsnest
  704→701, DRC unchanged), and PROMOTED it (authoritative `sha256 00c93bdb…`; 452 trk / 54 via; journal 80).
  **161 of the 164 rest-of-board nets remain unrouted.**
- **The lever (FBV2-P2-007).** Pick the next sharply-bounded group from measured geometry
  (`w/measure_rest_006.py` ranks candidates), add it to the `GROUPS` registry in `incremental_router.py`, then
  `route` → `gate` → `promote`. Good next candidates: the remaining short, isolated 08_BUTTONS_EXPANDERS /
  01_POWER_TREE-local / 05_I2C control pairs, then short bus segments; **defer** the RF/NFC radios, USB,
  community-header mass and GND/+3V3 bulk rails until the framework has more mileage. Promote **only a genuine
  no-casualty / no-new-DRC increment** (the gate enforces this). All floors ENFORCED (D-249 ≥1.20 mm BPP,
  D-269 0.300 mm, D-257 via ladder, 0.60 mm BAT_MAIN, 0.200/0.150 signal, 0.25 hole-hole, D-275/D-288 bridge);
  no DRU/rule relaxation, no D-290 reauth, no topology/footprint/outline change. Add a G-contract per accepted
  group (G18 is the FRONT_RGB template).
- **Superseded (kept for context) — FBV2-P2-004B (the `U11.2` BPP trunk-endpoint retarget lever), CLOSED by
  D-302.** `LTC_GATE U18.10→Q3.4` is CLOSED (accepted `AQROOT_LTCGATE_KO`
  lever). The full run is the FIRST to reach the final `u11_escape()` step, and the single terminal
  Phase-A wall is now **`U11.2 escape: none exists`**. Copper is still NOT promoted.
- **Root cause (measured, `checks/w/phaseA_003t_full_004a_ltcgate1.json` + `w/run_004a_full.log`,
  no new long route).** `u11_escape()` (`route_battery_block.py:2149`) lays the U11.2 end of the
  `BAT_PROTECTED_P` high-current trunk LAST: escape `D9.1` at `W_TRUNK_BPP=1.50 mm`, flare `U11.2`
  (1.50→0.20 mm SENSE neck), `connect_role(launch→D9.1)` at 1.50/1.20 mm, `gate()`. Geometry:
  `U11.2`=(66.400,78.200) in the EAST `BAT_PROTECTED_P` node cluster; `D9.1`=(11.350,72.500) in the WEST
  mass — a **~55 mm cross-board ≥1.20 mm B.Cu trunk**. The BPP backbone is otherwise connected
  (R75.2→(stage) TRUNK 14.458 mm F.Cu; EARLY SOUTH BRIDGE land C36.1 70.925 mm; C58.1→D9.1 TAP 5.092 mm;
  C36/C25/C58/D9.1 "already joined via R75.2"); U11.2 already has its 0.20 mm SENSE tie (5.525 mm, not a
  current path). The single ≤~1.30 mm central channel is already occupied by the south bridge + R75.2
  trunk, so a second parallel 1.50 mm trunk has **NO legal path** — a **structural ≥1.20 mm-trunk
  NO_LEGAL_PATH** (the D-273/274/281/282/283 class), NOT a ~20 µm DRC pinch.
- **The lever (build ONE, env-gated OFF-by-default) — RETARGET, NOT a cross-board trunk.** U11.2 is IN
  the east node, already on-net with D9.1 via the bridge/R75.2 backbone, so close the U11.2 trunk
  endpoint as a **SHORT wide tap into the nearest already-connected ≥1.20 mm BPP node copper** (candidate:
  `C36.1`=(63.75,73.75), ~2.9 mm east, or the bridge landing) instead of the distant `D9.1`. Keep
  `AQROOT_U18BPP_JOIN=I3`, `AQROOT_U19CAP=1`, `AQROOT_LTCGATE_KO=1` **ON** (all accepted). The tap must
  remain a legal **≥1.20 mm** current path (D-249/D-269/0.60 mm BAT_MAIN ENFORCED — no width waiver; this
  is a high-current safety-relevant net), and 004B must **verify the retarget preserves a valid
  high-current path** (U11 load current still reaches the bulk-cap/protection output at ≥1.20 mm; a short
  tap that leaves U11 fed only through the thin cap-via tie would be a functional regression, not a gain).
  **Fallback** (only if no legal on-net tap sites the ≥1.20 mm path): a bounded immediate-neighbour
  placement ECO to open a ≥1.20 mm `U11.2` corridor, re-screened with real full-placement DRC (D-286).
  If the ≥1.20 mm trunk truly cannot be closed within CTO-scope routing/tap/bounded-ECO (the
  D-281/282/283 western-corridor wall genuinely re-surfacing as unsolvable without a topology/mechanical
  change), that would re-raise an OWNER decision — but 004B must first exhaust the bounded retarget.
- **The governing run (CTO, persistent terminal, ~25 min):**
  `cd hardware/beta-v2/checks && cp phaseA_journal.json /tmp/phaseA_journal.HEAD.json &&
  AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 <u11-retarget env> bash w/run_003t_full.sh
  004b_u11 w/cand_003t/t_a_r77e15n10_r79e15n10.json && cp /tmp/phaseA_journal.HEAD.json phaseA_journal.json`.
  **Judge by the full-run connected-set diff** vs `w/phaseA_003t_full_004a_ltcgate1.json`: the run must
  close the `U11.2` trunk endpoint for a real net gain with no new DRC class and no lost connection, and
  preserve the high-current path. **Do not trust a focused/post-hoc probe** (the D-300 lesson).
  **Promote copper only on a genuine full-authority Phase-A PASS** (D-286). All floors ENFORCED; D-290
  stays closed.
- **Downstream, still CTO-scope:** on a full PASS, re-verify the (now-past) `REF_POL R87.2` F-corridor
  and the BAT_RAW R89.1/R86.2 divider taps.

## 6. Authoritative PCB state
- **Routing/promotion (D-310): Phase-A copper + SEVEN rest-of-board increments.** Authoritative board =
  **six copper layers, 561 signal tracks, 60 vias, 41 zones** (verified `sha256 856f7a8a…0a197114`), carrying the
  **432-track Phase-A battery block (D-302) PLUS** FRONT_RGB 20 (D-304) + ACC 31 (D-305) + DISP 11/1 via (D-306)
  + IMU 8 (D-307) + FRONT_RGB_LED 25/3 via (D-308) + IR_RX_VS 8 (D-309) + TOUCH_CTL 26/2 via (D-310); ratsnest
  **685**; journal **96** (77 Phase-A + 19 `REST_INC`); real KiCad DRC unchanged (`{solder_mask_bridge:1,
  hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`); **151 rest-of-board nets remain unrouted.**
  `router_regression.py` ALL PASS (G1–G24, 102 lines). Rollback: pre-D-310 `sha256 5c5cae79…a339f63` (D-309;
  parent `f2bcac1`).
- **(historical) Routing/promotion (D-304): Phase-A copper + first rest-of-board increment.** Authoritative board =
  **six copper layers, 452 signal tracks, 54 vias, 41 zones** (verified `sha256 00c93bdb…dfb72aad`), carrying
  the **432-track Phase-A battery block (D-302) PLUS the 20-track FRONT_RGB indicator increment (D-304)**;
  ratsnest **701**; journal **80** (77 Phase-A + 3 `REST_INC`); real KiCad DRC unchanged
  (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`); 161 rest-of-
  board nets remain unrouted. `router_regression.py` ALL 82 PASS (G1–G18). Rollback: pre-D-304
  `sha256 63a9bc54…f87d6ba9` (D-302; parent `50149f4`).
- **(historical) Routing/promotion (D-302): FIRST AUTHORITATIVE COPPER PROMOTED.** Authoritative board = **six copper
  layers, 432 signal tracks, 54 vias, 41 zones** (verified `sha256 63a9bc54…f87d6ba9`, size 1475931), carrying
  **Phase-A battery-block copper ONLY** (all 432 tracks in-scope power-tree; 0 out-of-scope); direction-2
  placement (fingerprint `397dffe1f77e4d10`; U18 moved to (8.0,66.5,180°), C36.1 at (63.750,74.325)); 77-entry
  `phaseA_journal.json`; regenerated 119-rule DRU (the accepted D-249/D-257/D-258/D-263/D-264/D-266/D-269
  per-net set, NOT a relaxation). Real KiCad DRC `{hole_clearance:5, lib_footprint_issues:199,
  solder_mask_bridge:1, unconnected_items:499}` — zero new copper classes. **Rest of board (164 multi-pad
  nets, 9 sheets + rails) UNROUTED** (ratsnest 704 / unconnected 499). **Rollback:** pre-promotion PCB
  `sha256 2235e273…d642d7e` (parent `56d0ebe`, tag `beta-v2-p2-pre-copper-authoritative`).
- **(historical) prior authoritative PCB state before D-302** = six copper layers, 0 signal tracks, 0 signal
  vias (`sha256 2235e273…d642d7e`, byte-identical to the pre-promotion HEAD). All 003O/003T/003W bridge/
  full-run copper lived only in gitignored scratch (`checks/w/`) and override files; the natural-run
  003O result `checks/phaseA_003o_b1_r75rot_cto.json` is committed as evidence of record, and the
  003T/003W full-authority results stay gitignored under scratch
  (`checks/w/phaseA_003t_full_e15n10cto.json`, `…003w_u18bpp_i3.json`, `FULL003T_e15n10cto/`).
- **Banked in source (D-297), NOT in copper:** the OFF-by-default `AQROOT_U18BPP_JOIN` In3-join lever
  (byte-identical when unset) closes `U18.8→R75.2` for a proven +1 gain when ON; it awaits the U19
  field closure and a full Phase-A PASS before any copper is promoted.
- **Banked in source (D-299), NOT in copper:** the OFF-by-default `AQROOT_U19CAP` U19 east-lane
  reservation + U19.7-first lever (byte-identical when unset), pinned by regression **G14** and now
  **gate-validated as a genuine +2** (FBV2-P2-003Y: closes `REC_BAT_LOW U19.7` + `N_BATDIV U19.6`, LOST
  0, board-legal 0.60/0.30 vias, FAULT_N clean, DRC identical). Source (`checks/route_battery_block.py`,
  `checks/router_regression.py`) is **COMMITTED**; it awaits the `LTC_GATE` closure and a full Phase-A
  PASS before any copper is promoted. Full-gate artifact (gitignored):
  `checks/w/phaseA_003t_full_003y2_u19cap.json`, judged by `checks/w/judge_003y2.py`.
- `phaseA_journal.json` at its committed HEAD state (driver never authoritatively invoked; the shared
  journal was backed up and restored around the full run; scratch churn discarded).
- PCB routing **0 %**; overall repo progress **74 %**.

## 7. Locked invariants (reference the D-xxx rulings, not the history)
- **D-275** forced-south `BAT_PROTECTED_P` bridge geometry (lane + landing proven). **D-288** the
  entry-array two-layer tie is FIXED (rotation-aware in-pad `scan_entry_sites` + symmetric B.Cu
  tie-stub, `via_dangling`-clean; an electrical pass, not merely geometric). The **0.60 mm BAT_MAIN
  minimum width** rule is a hard floor.
- **D-277..D-280** U19/deadcell escape + C61 landing-guard gains.
- **D-281/282/283** western-corridor route-scope fixes exhausted; **D-284 (OWNER)** approved
  landing-opening direction 1; **D-285** `place_003l` opens the C36.1 landing (clean).
- **D-286** the gate baseline is measured on the actual complete pre-copper placement; candidate
  placements must be screened with real full-placement DRC; a genuine placement short must be
  surfaced, never absorbed. **No proxy (focused vehicle / partial run) promotes copper — only a
  genuine full-authority Phase-A PASS does.** Regression G12 pins the corrected baseline order.
- **D-287** the bounded direction-1 placement space is EXHAUSTED (27/27); a `via_dangling` item is a
  genuine electrical fault and MUST fail.
- **D-289/D-290** the residual U18.8 `BAT_PROTECTED_P` escape is a **placement-geometry
  mutual-exclusion** at the 0.5 mm pad pitch vs the 0.300 mm current-path floor (D-269); the
  routing-only co-closure space (off-layer vacate of U18.7) is REFUTED — no routing-only site
  remains, so the U18.8 escape was an OWNER decision, **RESOLVED by D-293 (direction 2 authorized).**
- **D-293 (OWNER)** authorized **direction 2** — bounded LTC4368-block spread / escape-target
  relocation (R77/R79 east, R80/R81 north) so `BAT_RAW` (U18.1 east) and `BAT_PROTECTED_P` (U18.8
  west) escape through independent corridors — without relaxing D-269 or any floor, without accepting
  U18.8 open, without re-litigating D-290.
- **D-294 (003T)** direction 2 was EXECUTED under full CTO authority: a focused minimum candidate
  exists but the full gate FAILs, so no candidate is promotable. Direction-2 is PRODUCTIVE (+2 vs
  003O, `REF_POL R87.2` now past) but INCOMPLETE. **A focused `fail=None` is VACUOUS vs the congested
  full run — judge Phase-A changes by the full-run connected-set diff, promote copper only on
  full-authority evidence.**
- **D-295 (003U)** the two D-294 walls are full-run-emergent ordering/congestion casualties and no
  cheap vehicle judges either at the direction-2 placement; the PRIMARY (`REC_BAT_LOW U19.7`) is
  reducible-in-principle (direction-2's +2-connection congestion swapped `VREC_VCC U19.8`'s pad-escape
  from B.Cu onto the F lane U19.7 needs); both bounded levers are judgeable only by the ~22-min full
  gate. The U19.7 wall is an ordering class, NOT a D-289/290/292 placement mutual-exclusion.
- **D-296 (003V)** the PRIMARY U19.7 escape-reservation family is **REFUTED**: with a board-legal
  0.60/0.30 via the reservation fires and closes U19.7, but the U19 dead-cell field is
  **capacity-saturated on F.Cu/B.Cu**, so a single-pin reservation is a bounded **ordering trade** —
  it swaps the casualty (U19.7 ⇄ U19.2, wall U19.7→U19.6), earning NO net connected-set progress. Do
  NOT re-try single-pin U19 reservation; the U19 field needs a lever that ENLARGES capacity, not one
  that re-orders it.
- **D-297 (003W)** the SECONDARY U18.8 I2-join is closed by a **capacity add, not an ordering trade**:
  the reserve vias are THROUGH vias, In3.Cu is a routable six-layer signal layer that is bare across
  this corridor, so completing `U18.8→R75.2` on In3 (`AQROOT_U18BPP_JOIN=I3`) is a **genuine +1
  connected-set gain with no casualty, no new via, no new DRC class, and clears `via_dangling`** —
  because it takes capacity from no other net. **ACCEPTED and banked env-gated/OFF-by-default in
  source; copper is NOT promoted while the full run still FAILs on the U19 field.** The general lesson:
  the bare inner signal layers In2/In3 are unused capacity in this corridor and are the correct
  vehicle for enlarging a saturated F.Cu/B.Cu field (the U19 direction for 003X).
- **D-298 (003X)** the U19 field is closable by a **capacity ADD, not a swap**: U19.6/U19.7 (BOTTOM
  SOT-23-8) are pad-boxed N/S; their shared EAST lane is walled by the same `LTC4368_FAULT_N`
  cross-board run; POFV is DRU-barred (U19.6/U19.7 lack the D-257 fine-via exception the other three
  U19 pins have), so the escape needs a clear lateral lane + the legal 0.65/0.40 via. The
  `AQROOT_U19CAP` lever **reserves the shared east lane** (FAULT_N detours) and **closes U19.7 before
  U19.6** — both then escape, screened DRC-clean. IMPLEMENTED, regression-pinned (G14), OFF-by-default.
  Categorically distinct from the refuted D-296 single-pin lateral swap.
- **D-299 (003Y)** the D-298 lever's **full-authority gate CONFIRMED a genuine +2** (both `REC_BAT_LOW
  U19.7` and `N_BATDIV U19.6` close, LOST 0, board-legal 0.60/0.30 vias, `LTC4368_FAULT_N` detours
  clean, DRC identical) — so `AQROOT_U19CAP` is **ACCEPTED and COMMITTED** (banked OFF-by-default).
  **Copper NOT promoted** (D-286): full Phase-A still FAILs, the terminal wall newly advancing past the
  whole U19 field to **`LTC_GATE U18.10→Q3.4`** — candidate join paths found but **DRC-gate-rejected**
  by the frozen **D-249** (BPP 1.20 mm trunk, actual 0.20) and **D-269** (BAT_MAIN 0.300 mm clearance,
  actual 0.2803) rules; a bounded reducible corridor wall, NOT `NO_PATH`.
- **D-300 (003Z)** the `LTC_GATE U18.10→Q3.4` **defer-to-congestion re-order** (`AQROOT_LTCGATE`: pull
  the join out of section 8b, re-queue it LAST) is **REFUTED** — the full gate is behaviourally
  identical to D-299 (gained 0 / lost 0, same wall, same D-249/D-269 rejections, identical DRC): **a
  pure re-order is a NULL OPERATION** on this wall because the driver's `connect_role` greedily
  re-takes the identical rule-violating central path even when queued last. Do NOT re-try ordering on
  this wall. The focused `ltcgate_join_probe_003z.py` was a **false-positive proxy** — its post-hoc
  `connect_role` on the SAVED board found a ~10.5 mm west detour the real in-run driver never takes; per
  D-286 a post-hoc/focused proxy cannot override the full gate. The correct lever is **path-shaping**
  (physically block the central lane to force the detour), not ordering (FBV2-P2-004A, §5). The lever +
  its G15 WIP were retired via exact reverse patch; the probe was retired.
- Rule floors ENFORCED: **0.200 mm** clearance, **0.25 mm** hole-to-hole, **0.300 mm** current-path
  routed clearance (D-269), **≥1.20 mm** BPP trunk width (D-249), **0.60 mm** BAT_MAIN minimum width.
  Six-layer stack, GND, netclasses, footprints, polarity, safety set — all frozen. Frozen
  `beta-full-reference-v1` untouched.

## 8. Open owner decisions
- **NONE. D-293 resolved the last owner decision (direction 2 authorized); D-294..D-301 each re-raised
  none.** Direction 2 is being executed under full CTO authority; the U18.8 wall is closed in principle
  by the accepted D-297 In3-join lever, the U19 field by the committed D-299 U19CAP lever, and the
  `LTC_GATE U18.10→Q3.4` join by the committed D-301 LTCGATE_KO lever (all banked OFF-by-default in
  source). The sole remaining Phase-A blocker — `U11.2 escape: none exists` (the BPP 1.5 mm high-current
  trunk endpoint) — is **bounded CTO-scope routing work (a trunk-endpoint retarget), not an owner
  decision** (no floor relaxed, no frozen part moved, no DRU change, no D-249/D-269 relaxation); the D-301
  mandated Opportunity & Simplification Scan (§9a) found **no** irreversible opportunity loss or strategic
  fork. Autonomy CONTINUES with **FBV2-P2-004B** (§5). Only if the ≥1.20 mm BPP trunk truly cannot be
  closed within CTO-scope routing/tap/bounded-ECO would an OWNER decision re-surface; 004B must first
  exhaust the bounded retarget. Historical options (B accept-U18.8-open, D re-litigate-D-290) are retained
  only as context and are not active.
- **Nothing has been changed under any decision:** no part moved, no floor relaxed, no DRC absorbed
  into the authoritative board; the authoritative PCB is six layers / 0 tracks / 0 vias.

## 9a. Opportunity & Simplification Scan (D-301, LTC_GATE close / BPP trunk milestone)
- **Mandated bounded scan** at this milestone, grounded in the accepted `AQROOT_LTCGATE_KO` lever and the
  newly-exposed `U11.2` BPP trunk wall (U11.2=(66.400,78.200) EAST node; D9.1=(11.350,72.500) WEST; the
  `u11_escape()` cross-board 1.50 mm trunk has no legal corridor on the saturated western margin).
- **Path-shaping (accepted, cheapest lever).** The `AQROOT_LTCGATE_KO` central-lane keep-out closes the
  LTC_GATE join with **zero BOM/placement/rule impact**, OFF-by-default, byte-identical when unset; the
  probe was pruned (complexity removed). Cheapest, reversible.
- **U11.2 retarget (recommended next lever, 004B).** U11.2 is IN the east node, already on-net with D9.1
  via the bridge, so a **short on-net ≥1.20 mm tap** (e.g. into C36.1) beats the obvious cross-board
  trunk. Reversible, env-gated OFF-by-default. High-current safety-relevant net → must preserve the
  ≥1.20 mm path (no width waiver).
- **Bounded local placement ECO — the fallback** if no legal on-net tap sites the ≥1.20 mm path;
  re-screened with real full-placement DRC (D-286). Larger blast radius, second choice.
- **BOM.** No opportunity — the wall is a routing pinch, not a component gap; the LTC4368 + Q2/Q3
  back-to-back-FET reverse-protection topology is frozen and correct. **No cost lever.**
- **Recoverability (D-049) / testability / manufacturing / firmware / UX.** The accepted lever is a
  low-current internal control-net join with no footprint/outline/stackup/silk/firmware surface. The
  U11.2 trunk is high-current safety-relevant, so 004B must not waive the ≥1.20 mm width.
- **Future option (preserved).** The six-layer stack's bare inner signal layers In2/In3 remain spare
  capacity (the D-297 lesson) — a preserved vehicle if the U11.2 tap corridor proves congested. Nothing
  is foreclosed.
- **Cost classification / conclusion.** No product-capability or BOM opportunity justifies changing
  architecture; no irreversible cost, no strategic fork, no opportunity loss. **Open owner decisions:
  NONE.** The deferred opportunity is only the *technical* 004B lever above, pursued under CTO autonomy.

## 9. JLCPCB readiness
- **JLCPCB readiness ~77 %** (unchanged — 004A earned NO copper: it accepted a genuine +1 (LTC_GATE join
  closed) and committed it OFF-by-default in source, but the full Phase-A run still FAILs at the newly-
  exposed `U11.2` BPP trunk wall, so no copper promoted; the authoritative board is still six layers /
  0 tracks / 0 vias). `/home/aqroot8/.aqroot-progress.env` unchanged (CTO owns readiness).
- **Repo progress 74 %** (governed value in PROGRESS.md).
- **What remains before fabrication:** close the `U11.2` BPP trunk endpoint (a short on-net ≥1.20 mm tap)
  and complete a full Phase-A PASS at the direction-2 placement (with the accepted D-297/D-299/D-301
  levers ON); promote the authoritative copper; then Phase-B production routing; full DRC/ERC/connectivity
  and
  regression closure on the authoritative board; RF/power/thermal/safety validation; BOM/footprint/
  polarity/DNP + assembly review; board-outline/stackup/fab-rule review; Gerber/drill/BOM/CPL
  generation and independent manufacturing-package review.

## 10. Active orchestration
- **Persistent CTO session:** `agent:main:aqroot-fbv2-cto` — sole owner of Claude engineering
  launches; receives every completion event.
- **Autopilot:** cron/systemd may only WAKE the persistent CTO; it must never launch Claude or become
  a task parent. No owner decision is open; the stop file is ABSENT and the persistent CTO continues
  one-Claude-at-a-time engineering.
- **Should an engineering process be active now?** **Yes.** FBV2-P2-004B implements ONE bounded,
  env-gated (OFF-by-default) `U11.2` **BPP trunk-endpoint retarget** lever (close the U11.2 trunk end as a
  short on-net ≥1.20 mm tap into the nearest already-connected BPP node copper — e.g. C36.1 — instead of
  the cross-board `u11_escape()` run to D9.1; no width waiver, high-current safety-relevant net), validate
  it against `router_regression.py` (authoritative byte-identical), then run the FULL authority gate
  (`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 <u11-retarget-lever> bash w/run_003t_full.sh
  004b_u11 w/cand_003t/t_a_r77e15n10_r79e15n10.json`, ~25 min, in a persistent terminal) and judge by the
  full-run connected-set diff vs `w/phaseA_003t_full_004a_ltcgate1.json` (never a focused/post-hoc probe
  — the D-300 lesson), verifying the retarget preserves a valid high-current path. The bounded neighbour
  placement ECO (re-screened full-placement DRC) is the fallback. Promote copper only on a genuine full
  Phase-A PASS.
- **DEVICE_SPEC gate:** before any render / website / Kickstarter / enclosure brief / external-mechanical
  / product-description claim, consult `docs/full-beta-v2/DEVICE_SPEC.md` and claim only MARKETING-SAFE rows.

## 11. Recovery instructions (a fresh CTO/Claude reads these, in order)
0. `docs/full-beta-v2/DEVICE_SPEC.md` — the authoritative current-product spec/index (MCU/radios/antennas/
   power/connectors/mechanical, with LOCKED/FITTED/DNP/UNRESOLVED + MARKETING-SAFE labels). **MANDATORY**
   before any external / mechanical / marketing claim.
1. `docs/full-beta-v2/CTO_DECISIONS.md` — authoritative rulings (latest: **D-301**, FBV2-P2-004A the
   `AQROOT_LTCGATE_KO` **path-shaping** lever ACCEPTED and COMMITTED (genuine +1: closes `LTC_GATE
   U18.10→Q3.4`, LOST 0, no new DRC; OFF-by-default, byte-identical when unset, pinned by G15); copper NOT
   promoted — full Phase-A now FAILs at the newly-exposed `U11.2` BPP 1.5 mm trunk wall; autonomy
   CONTINUES; preceded by **D-300** (003Z re-order refuted) and **D-299** (003Y U19CAP +2 accepted/committed)).
2. Newest audits — `audits/2026-08-30-p2-004a-d301-ltcgate-ko-path-shaping-lever-full-gate-plus1-accepted-committed-u11-trunk-wall.md`,
   then `…-003z-d300-ltcgate-defer-to-congestion-lever-refuted-false-positive-probe-retired.md`,
   then `…-003y-d299-u19cap-full-gate-plus2-accepted-committed-ltc-gate-wall.md`,
   then `…-003x-d298-u19-capacity-east-lane-reservation-lever-screened-clean-handoff.md`,
   then `…-003w-d297-secondary-u18bpp-i3-join-lever-net-gain-accepted.md`,
   then `…-003v-d296-primary-reservation-lever-ordering-trade-no-progress-retired.md`,
   then `…-003u-d295-two-walls-full-run-emergent-ordering-cheap-vacuous-handoff.md`,
   `…-003t-d294-direction2-full-gate-fail-u18-corridor-u19-escape.md`,
   `…-003s-d292-u18-r75-placement-microeco-exhausted.md`,
   `…-003r-d290-off-layer-vacate-refuted-owner-decision.md`, `…-003q-d289-…`, `…-003o-d288-…`.
3. `docs/full-beta-v2/CHANGELOG.md` and `docs/full-beta-v2/PROGRESS.md` (top entries).
4. Git HEAD + recent commits; the 003W instruments — the accepted D-297 lever in
   `hardware/beta-v2/checks/route_battery_block.py` (env `AQROOT_U18BPP_JOIN`, the `main()` join
   site), its **G13** contract in `checks/router_regression.py`, and the measured-record probe
   `checks/u18_i3_join_probe_003w.py`. The fixed bridge sites `bridge_early_003i.py` /
   `bridge_route_003c.py` (D-288).
5. Evidence + recipe + probes: the pinned natural-run
   `hardware/beta-v2/checks/phaseA_003o_b1_r75rot_cto.json`; the governing full recipe
   `w/run_003t_full.sh` + `w/cand_003t/t_a_r77e15n10_r79e15n10.json`; gitignored full-run results
   `w/phaseA_003t_full_e15n10cto.json` (D-294 baseline) and `w/phaseA_003t_full_003w_u18bpp_i3.json`
   (D-297); `place_003l.json`, `place_002z/` candidate set.
- **Never** trust this checkpoint over a conflicting `CTO_DECISIONS.md`; repair this file if they
  diverge.
