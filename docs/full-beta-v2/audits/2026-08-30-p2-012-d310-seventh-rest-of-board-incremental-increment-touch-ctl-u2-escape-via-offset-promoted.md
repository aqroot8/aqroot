# FBV2-P2-012 / D-310 — Seventh rest-of-board incremental increment routed + PROMOTED (display/touch control pair `TOUCH_RST_N` + `TOUCH_INT_N`) — the D-309 U2 B.Cu escape WALL BROKEN by a bounded via-site offset + existing-via awareness

**Date:** 2026-08-30
**Class:** Governed CTO ACCEPT + PROMOTE — routine rest-of-board routing within CTO authority. **No owner decision raised.**
**Starting HEAD:** `f2bcac1` (D-309; pushed; `origin/master` identical).
**Authoritative PCB:** `sha256 5c5cae79…a339f63` (535 trk / 58 via / 6 layers / 41 zones, ratsnest 688, journal 93) → **`sha256 856f7a8adf0db9b114b9f09d7469308f921bc897aaf2ddce7f1c15c40a197114`** (561 trk / 60 via / 6 layers / 41 zones, ratsnest 685, journal 96).

---

## Summary

The seventh rest-of-board increment is on the authoritative board, and it is the
group **D-309 measured as a WALL**: the coherent display/touch control pair
`TOUCH_RST_N` + `TOUCH_INT_N` (the capacitive-touch reset + interrupt lines from
the display FPC connector J1 to the touch-controller interface U2). The same
`incremental_router.py` (baseline/route/gate/promote) loaded the D-309 promoted
board and routed both nets WITHOUT touching a single strand of accepted Phase-A /
FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED / IR_RX_VS copper. A real full-board
gate proved a GENUINE no-casualty / no-new-DRC connectivity increment (ratsnest
688→685, **`clearance` stays 0**, only In1/In4 GND planes re-poured for the two new
via anti-pads) → **COPPER PROMOTED.** Autonomy continues; D-275 and D-277..D-309
preserved.

**Root cause of the D-309 wall — the router was BLIND to existing vias.**
`qrouter.QBoard._scan` builds its obstacle model from footprint pads and
`PCB_TRACK` segments but iterates `GetTracks()` and `continue`s on the `PCB_VIA`
class — so **every accepted through-via is invisible to escape / via_site /
connect_role.** U2.4/.7/.8/.11 stack on U2's **west** edge at x=54.14; the accepted
D-306 `DISP_RST_N` through-via sits at (52.95, 87.0), **1.19 mm west** of that
column. A westward cross-layer escape therefore lands the new via (and threads its
F.Cu run) right past the `DISP_RST_N` barrel, and only the real full-board DRC
caught it (D-309: +3 `clearance`; measured this cycle: `AMP_SD_MODE`'s default via
0.100 mm copper to `DISP_RST_N`).

**The fix — two generic, bounded, qrouter-UNTOUCHED mechanisms in
`connect_cross`.** (1) **Existing-via awareness:** every accepted `PCB_VIA`
barrel/hole is injected as an obstacle onto the per-route `QBoard` instance
(mirroring, item-for-item, what `QBoard.via()` already does for a via it lays
itself), so escape / via_site / **connect_role's track search** all respect
accepted vias. (2) **Bounded via-site offset:** a group opts in with `via_offset`
and the F↔B transition is deliberately walked ~2.5 mm off the nearest congesting
barrel (a short host-face B.Cu fan-out) — the first increment that **plans a via
site** rather than accepting the router's first via-blind legal one. Groups
WITHOUT `via_offset` and boards with no nearby vias are byte-identical to before;
`qrouter.py` is not modified, so every G-contract fixture that re-routes through
`QBoard` is unaffected.

---

## A — Screen (2–4 bounded candidate via sites, real-geometry clearance, before any gate)

The READ-ONLY `w/geom_012.py` located the exact geometry: DISP_RST_N via
@(52.950,87.000) dia 0.60; U2 west-edge column U2.4 `TOUCH_RST_N` (54.14,89.63),
U2.7 `AMP_SD_MODE` (54.14,87.68), U2.8 `DISP_RST_N` (54.14,87.03), U2.11
`SD_CARD_DETECT_N` (54.14,85.08); U2.19 `TOUCH_INT_N` on U2's **east** edge
(59.86,88.33).

The READ-ONLY `w/screen_012.py` reproduced `cmd_route`'s cross-layer edge for each
U2-family net and measured, against the REAL board geometry (existing-via copper +
hole, which `qrouter` cannot see), the DEFAULT via site vs bounded offset sites
biased away from the nearest existing via:

| net (U2 pad) | DEFAULT via | dist to DISP | via↔via clr | offset 2.5 mm via | dist to DISP | via↔via clr |
|---|---|---|---|---|---|---|
| `AMP_SD_MODE` (U2.7 W) | (52.95,87.70) | **0.70 mm** | **0.100 CLASH** | (52.85,90.20) | 3.20 mm | 2.602 CLEAR |
| `TOUCH_RST_N` (U2.4 W) | (52.95,89.60) | 2.60 mm | 2.000 | (52.95,92.10) | 5.10 mm | 4.398 CLEAR |
| `SD_CARD_DETECT_N` (U2.11 W) | (53.00,85.10) | 1.90 mm | 1.301 | (53.00,82.55) | 4.45 mm | 3.850 CLEAR |
| `TOUCH_INT_N` (U2.19 E) | (58.70,88.30) | 5.90 mm | 5.295 | (61.15,88.85) | 8.41 mm | 7.806 CLEAR |

`AMP_SD_MODE`'s default is a hard via-to-via CLASH (0.100 mm), confirming D-309's
+7. `TOUCH_RST_N`/`SD_DETECT` default vias clear the barrel but their near/far
**tracks** thread the congested west column (source of D-309's +3/+2). The offset
resolves all four with comfortable margin while the fan-out stays ≤2.8 mm off the
U2 pad. `2.5 mm` was chosen (comfortable clearance without wandering). Per the task
preference, the coherent display/touch pair `TOUCH_RST_N` + `TOUCH_INT_N` was
taken (both pass); unrelated nets were NOT bundled.

## B — Route → gate → promote (one foreground experiment; authoritative untouched)

- **`route TOUCH_CTL`** → ALL OK (3/3), "injected 58 existing-via obstacle(s)":
  `TOUCH_RST_N` J1.47↔R12.1 (22.217 mm same-layer F.Cu) + R12.1↔U2.4 (28.553 mm,
  cross-layer via @(52.950,92.100)); `TOUCH_INT_N` J1.46↔U2.19 (54.708 mm,
  cross-layer via @(61.150,88.850)); 26 segments (0.200 mm) + 2 through vias
  0.60/0.30; REFILLED In1/In4 GND zones [39,40] for the 2 anti-pads; scratch
  561/60; AUTH sha UNCHANGED (`5c5cae79…`). *First attempt with via-offset but the
  via-blind default track router still threaded the F.Cu run 0.05 mm from the DISP
  barrel (+3); adding the existing-via obstacle injection made connect_role's track
  search via-aware and the re-route was clean.*
- **`gate TOUCH_CTL`** = **PASS, every check:** no prior copper deleted/altered
  (D-309 535 trk + 58 via multiset is a SUBSET); 28 new items, all target-net;
  **only zones 39/40 (In1/In4) re-poured, all other 39 zones byte-identical**;
  `TOUCH_INT_N` open edges 1→0 and `TOUCH_RST_N` open edges 2→0; 0 prior requested
  pairs regressed; ratsnest 688→685 EXACTLY −3; **no new/worse DRC class (`clearance`
  0→0)**; `unconnected_items` 499→499.
- **`promote TOUCH_CTL`** re-ran the gate (PASS), re-verified the AUTH sha had not
  drifted (`5c5cae79…`), copied scratch→authoritative and merged the 3 route entries
  as `role=REST_INC`.

## C — What is promoted (integrity)

Authoritative `sha256 5c5cae79…a339f63` → **`856f7a8a…0a197114`**; tracks
**535→561** (+26 TOUCH: 21 F.Cu + 5 B.Cu host-face fan-out); vias **58→60** (+2
U2-escape offset through vias); 6 layers / 41 zones unchanged; ratsnest **688→685**
(−3); journal **93→96** (+3 `REST_INC`). PCB file diff = **310 insertions / 40
deletions**: additions are **26 `(segment)` + 2 `(via)`** lines (grep-confirmed **0
`segment`/`via`/`footprint` deletions**); all 40 deletions (and 378 of the added
`xy`) are points inside the In1/In4 GND `filled_polygon` re-pour (the 2 via
anti-pads), nothing else. Real KiCad DRC error-severity **unchanged**
(`solder_mask_bridge:1 + hole_clearance:5`, `unconnected_items` 499; full histogram
`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
unconnected_items:499}`; **0 `clearance`**). Every 432 Phase-A + 20 FRONT_RGB + 31
ACC + 11 DISP + 8 IMU + 25 FRONT_RGB_LED + 8 IR_RX_VS track and all 58 prior vias
present byte/geometry-identical; only new copper is the 26 TOUCH tracks + 2 vias. No
placement/DRU/netclass/footprint/value/polarity/outline/stackup change.

## D — Tests

New contract **G24** pins the increment: both nets fully copper-connected across the
U2 F/B hop (R12.1 joins J1.47 & U2.4; U2.19 joins J1.46); copper legal (26 trk
0.200 mm F.Cu+B.Cu, 2× 0.60/0.30 through vias); the **U2-escape offset cleared both
vias of every existing via** (min TOUCH-via to other-via centre = **4.998 mm** ≥ the
0.800 mm floor — proof the offset actually moved the transition off the wall); and
ADD-ONLY (IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A
432/54 untouched). G18–G23 stay green unchanged — their ADD-ONLY invariants exclude
ALL `role=REST_INC` nets generically and pin `phaseA_via`==54, so they
auto-generalise as total vias grow 58→60. `router_regression.py` = **ALL CHECKS PASS
(G1–G24), 102 PASS lines, 0 failed**, run twice, deterministic; G17 confirms 561 trk
/ 60 via / ratsnest 685 / 41 zones on the live board.

New focused probe `incremental_probe_012.py` (READ-ONLY: D-310 fingerprints;
pre-D-310 copper preserved exactly = 535 trk + 58 via; 26-track F.Cu+B.Cu increment
+ 2 vias; both TOUCH nets connected; **both vias ≥0.80 mm from every existing via**;
no pair regressed; only In1/In4 re-poured; DRC unchanged) ALL PASS.
`incremental_probe_006/007/008/009/010/011.py` PASS on the D-310 board unchanged
(each still proving its own net intact; the "pre-X copper" checks auto-generalise —
any group not in a probe's `PRE_GROUPS` is excluded as a post-X increment).
`phaseB_bringup_probe_005.py` updated (561/60/96; accepted-increment set +
TOUCH_RST_N + TOUCH_INT_N; 164 rest nets, **13 routed, 151 unrouted**) ALL PASS.

**Real-board DRC / connectivity re-run independently on the promoted board:**
`kicad-cli` error-severity DRC = `solder_mask_bridge:1` + `hole_clearance:5`,
`unconnected_items` 499; pcbnew ratsnest 685 — **no new `clearance` class from the
increment.**

**Phase-A DRU-synthesis probes (`d269_probe`, `d264_probe`, `dru_probe`) — NOT part
of the maintained increment regression, and NOT regressed by D-310.** Proven by a
board-swap A/B test: the committed D-309 board and the promoted D-310 board give
**byte-identical** probe signatures (`diff` empty) — `d269` FAIL(2) (checks C/D,
the flaky borderline BAT_RAW-divider synthetic clearance), `d264` FAIL(2) (checks
B/C, pre-existing path-role rule-emission reds), `dru` FAIL(2) (pre-existing). These
probes analyze the BAT_\*/LTC power-tree DRU rules; the TOUCH increment is 26
tracks + 2 vias in the mid-board display region far from them and cannot affect
them. No rule was touched or weakened; the flaky full-zone-re-pour proxy was not
mistaken for authoritative DRC (the real byte-stable board is DRC-clean, 0
`clearance`).

## E — Opportunity & Simplification Scan (mandated)

**Is the explicit via-site metadata reusable for the U2 family and future long
controls?** Yes, and deliberately so. The two mechanisms are generic, not
corridor-specific: **(1)** the existing-via obstacle injection is unconditional in
`cmd_route` and fixes a latent correctness gap for *every* future cross-layer
increment (no increment should ever thread an accepted barrel again); **(2)**
`via_offset` is opt-in per group and now available to the rest of the U2 family
(`AMP_SD_MODE`, `SD_CARD_DETECT_N`, and other U2-edge controls that measured clean
at 2.5 mm offset) and any future control whose transition must clear a congesting
barrel — without hiding corridor-specific coupling (the offset is a bounded scalar,
and the site is re-proven against real existing-via clearance by the defensive
`_clears_existing_vias` guard for *all* groups). The `_offset_via_site` bias points
"away from the nearest existing via," which is a general rule, not a hand-tuned U2
vector.

*Not acted on (bounded-scope discipline):* the three sibling U2 groups
(`AMP_SD_MODE`, `SD_DETECT`) were NOT bundled — the task said prefer the display/
touch pair and not force unrelated nets; they now have a proven mechanism and clean
measured sites for a future increment (annotated). No BOM / recoverability /
testability / firmware / UX / mechanical change forced; In2/In3 remain spare
capacity. **Open owner decisions: NONE.** DEVICE_SPEC unchanged (no hardware fact
changed — the touch reset/interrupt lines were always in the netlist; only their
copper is now routed).

## F — Integrity & rollback

Rollback = pre-promotion `sha256 5c5cae79…a339f63` (D-309; parent `f2bcac1`;
restored by `git checkout` of the PCB + journal; the D-302/D-304..D-309 rollback
points still stand). All locked invariants preserved: no
DRU/rule/clearance/stackup/topology/net/footprint/value/polarity/outline change; no
D-290 reauth; the 2 new vias are 0.60/0.30 Default through vias ≥ the 0.50 mm
min_via (D-257 legal), ≥0.25 mm hole-hole; D-249 (≥1.20 mm BPP), D-269 (0.300 mm),
0.300/0.60 BAT_MAIN, 0.200/0.150 signal, D-257/D-258/D-263/D-264/D-266, D-275/D-288
bridge, **In1/In4 GND roles** (only these two planes re-poured for the anti-pads,
every other zone byte-identical), USB/RF/mechanical reservations ENFORCED;
`AQROOT_U18BPP_JOIN` (D-297), `AQROOT_U19CAP` (D-299/G14), `AQROOT_LTCGATE_KO`
(D-301/G15), `AQROOT_U11_RETARGET` (D-302/G16), fixture split (G17), FRONT_RGB
(G18/D-304), ACC_3V3_CTL (G19/D-305), DISP_RST_N (G20/D-306), IMU_ADDR (G21/D-307),
FRONT_RGB_LED (G22/D-308), IR_RX_VS (G23/D-309), TOUCH_CTL (G24/D-310), `place_003l`
(D-285), D-275 and D-277..D-309 preserved; frozen `beta-full-reference-v1`
untouched; DEVICE_SPEC unchanged; shared journal authoritative (96 entries); no
orphan process.

## G — Next: FBV2-P2-013

Continue rest-of-board routing via the same framework (**151 of 164 rest nets
unrouted**). The U2 escape family is now UNLOCKED behind the proven mechanism:

1. **Complete the U2 escape family.** `AMP_SD_MODE` (audio amp SD/mode strap, U2.7)
   and `SD_CARD_DETECT_N` (microSD card-detect, U2.11) both measured clean at the
   2.5 mm offset (via↔via 2.602 / 3.850 mm) — a coherent next increment (add
   `via_offset` to their `GROUPS` entries and route/gate; they are already annotated).
   Verify each on the real gate (long hauls — `SD_DETECT` ~68 mm — may surface
   track-level congestion elsewhere).
2. **Other clean local groups** via `w/screen_010.py` (e.g. `RESERVED_SPARE` U23
   B.Cu 3-pad; short single-via mixed-layer controls). The XGPIO0…9 bank is a real
   10-net coherent target but a ~55 mm cross-board cross-layer haul — screen its
   corridor first.

**Still avoid** naive retry of `U11_PROG`/`PWR_SENSE` (hard pad-escape/corridor
walls); RF/NFC/USB/crystals/community-header/rails/switching/class-D remain deferred.
The first increment needing MULTIPLE series vias on ONE net / a via array / an
In2/In3 inner-signal traverse must extend `connect_cross`/`refill_planes`
deliberately.

**PROGRESS EARNED (seventh rest-of-board increment promoted; the D-309 U2 escape wall broken by a bounded via-site offset + existing-via awareness; display/touch control pair closed): PCB routing ~18 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical control increment, not fab-readiness).**
