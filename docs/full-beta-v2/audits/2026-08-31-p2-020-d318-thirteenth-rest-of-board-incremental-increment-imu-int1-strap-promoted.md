# FBV2-P2-020 / D-318 — THIRTEENTH rest-of-board incremental increment routed + PROMOTED: the IMU/I2C-local interrupt strap `BMI270_INT1_STRAP` (4-pad, ALL F.Cu same-layer MST, NO via), the first clean increment OUTSIDE the saturated west-XGPIO F.Cu corridor (the D-317 mandate); a governed CTO ACCEPT + PROMOTE, ZERO router-logic change

**Date:** 2026-08-31
**Starting HEAD:** `cacb68de32e78813fc5c875f927e00e4367afb66` (D-317; pushed; `origin/master` identical)
**Authoritative PCB before:** `sha256 d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d` — 691 tracks / 67 vias / 6 layers / 41 zones / ratsnest 676 / journal 105 (committed D-316; D-317 changed no copper)
**Authoritative PCB after:** `sha256 78bf82da537a22697a860c23822599246e0534a8c4c311e12bc3d5b857a28816` — **709 tracks / 67 vias / 6 layers / 41 zones / ratsnest 673 / journal 108**
**Result:** GOVERNED CTO **ACCEPT + PROMOTE** — a thirteenth rest-of-board net (`BMI270_INT1_STRAP`) is on the authoritative board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy CONTINUES; **no owner decision.**

---

## Summary

D-317 characterised the single west XGPIO net `XGPIO2` as a corridor-capacity wall on the live D-316
board and mandated FBV2-P2-020: **route the next clean rest-of-board increment in an OPEN, uncongested
region OUTSIDE the saturated west-XGPIO F.Cu corridor** — a single net or small coherent group — do NOT
retry single west XGPIO F.Cu hauls (`XGPIO2/4/5/6/7`), the XGPIO2+XGPIO3 PAIR, or `U11_PROG`/`PWR_SENSE`;
avoid RF/NFC/antenna, USB, crystals/clocks, switching/high-current/class-D, bulk rails and
community-header mass; hold the inner-layer west-XGPIO haul as the deferred framework task.

First the stale `CURRENT_STATE.md` §5 heading/body (which still said FBV2-P2-018) was repaired to the
repository truth at D-317 (FBV2-P2-020). Then a fresh **evidence-first read-only screen** of all 144
unrouted rest-of-board nets (`w/screen_020.py`) measured, per net: pad layers (F/B/THT), pad count, bbox
span, MST length, cross-layer/via need, congestion (other-net copper items within bbox+2 mm), netclass,
and a category screen. **44 ALLOW / 100 EXCL.** From that evidence the selected candidate was
**`BMI270_INT1_STRAP`** — the MCU-side leg of the BMI270 IMU INT1 interrupt (series resistor far pad
`R18.2` → pull resistor `R110.1` → test point `TP3.1` → ESP32 MCU GPIO `U1.15`). It matches the task's
explicitly welcomed **IMU/I2C-local controls** category; all four pads are on F.Cu, so the 4-pad
multi-terminal MST is **three SAME-LAYER F.Cu runs with NO via** — the cleanest incremental class (no
through via, no In1/In4 plane re-pour, no via-clearance risk). Noncritical low-speed CMOS interrupt strap.

`route` → `gate` → `promote` on the real full-board (D-286): route ALL OK (3 same-layer F.Cu edges, no
via); the gate PASSed every check; promotion re-ran the gate PASS and copied the scratch board + merged
journal onto the authoritative project. Authoritative `sha256 78bf82da…`; tracks 691 → **709** (+18);
vias **67** (unchanged — no via); ratsnest 676 → **673** (−3); journal 105 → **108** (+3 REST_INC edges).

---

## A — Screen (READ-ONLY, live board, `w/screen_020.py`)

144 unrouted rest-of-board nets (≥2 pads, not power-tree scope, 0 tracks) were measured. A category screen
rejected the mandate-forbidden classes (100 EXCL): west/east XGPIO F.Cu corridor + bank (15), RF/NFC/radio
subsystem incl. `04_SPI_B_RADIOS_NFC` and NFC/SX1262/CC1101 (31 + 4), shared high-speed data/I2C bus
(SPI/I2S data, SDA/SCL) (13), USB (8), crystal/clock/bus-clock (SCK/BCLK/LRCLK) (3), switching/
high-current/rail/class-D (5V/BOOST/SPK/SUPPLY/VCC/VDD/`3V3_SW`/`PWR_EN`) (16), community-header mass (4),
`PWR_SENSE` (2), `U11_PROG` (2), bulk rails (2). The 44 ALLOW nets were ranked (no-via first, then low
congestion, then small span). The cleanest ALLOW no-via singletons were individually vetted on merit
(several auto-ALLOW nets — `Net-(L1-Pad1/2)`, `Net-(U13-SW)`, `BL_SW`, `Net-(J3-*)` — are in fact power
converter switching nodes or USB-C connector nets and were rejected on inspection). The selected candidate
was measured Default netclass, and all four pads confirmed on F.Cu (no via needed):

| net | sheet | pads | via | span mm | MST mm | congestion | pads (layer) |
|-----|-------|------|-----|---------|--------|------------|--------------|
| **BMI270_INT1_STRAP** | 02_MCU_CORE | 4 | — (no via) | 12.1 | 17.2 | 41 | R110.1:F R18.2:F TP3.1:F U1.15:F |

Alternates held in priority order (bounded fallbacks): `UART0_TXD_DBG` (debug UART, F.Cu no-via, cong 9),
`RESERVED_SPARE` (spare expander GPIO, B.Cu no-via, cong 84), `BQ25185_STAT1`/`STAT2` (charger status
pair, B.Cu no-via). No bundling of unrelated nets for throughput; a single coherent net was selected.

## B — Route (`incremental_router.py route IMU_INT1_STRAP`, scratch only)

A single-net `GROUPS['IMU_INT1_STRAP']` entry (`layer='F'`, `width=clr_pad=clr_trk=200000`, no via keys,
`nets=['BMI270_INT1_STRAP']`) was registered; **`incremental_router.py` / `qrouter.py` routing logic is
UNCHANGED** (a registry entry only, reusing the D-305/D-307 same-layer no-via mechanic on F.Cu). Route ALL
OK — the 4-pad MST is three same-layer F.Cu runs:

* `R110.1 → R18.2` F.Cu 2.829 mm
* `R18.2 → U1.15` F.Cu 4.646 mm
* `R110.1 → TP3.1` F.Cu 11.682 mm

18 F.Cu track segments, **0 vias**. Authoritative `sha256 d730c74d…` unchanged during the route (scratch
`w/INC_IMU_INT1_STRAP/` only).

## C — Gate (real full-board, D-286) — PASS every check

* **no Phase-A copper deleted or altered** (0 missing — the D-316 691 trk / 67 via multiset is a subset);
* **every new copper item is a target-group net** (0 out-of-scope); **copper actually added** (18 items);
* **only In1/In4 GND planes may re-pour; all other zones identical** — 0 zones fill-changed (no via → no
  re-pour), zone COUNT constant 41;
* **`BMI270_INT1_STRAP` fully connected by copper** (open_edges 3 → 0, all four pads joined);
* **all Phase-A requested pairs still copper-connected** (0 regressed);
* **ratsnest dropped by exactly the requested connections** 676 → 673 (−3);
* **no new DRC violation class; no DRC class increased; DRC unconnected_items did not increase** 499 → 499;
  DRC after `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199, unconnected_items:499}`.

**GATE PASS (0 checks failed).** `promote` re-ran the full gate (PASS), verified the authoritative sha had
not drifted since the gate, copied the scratch board onto the authoritative project, and merged 3
REST_INC journal edges.

## D — Promoted

Authoritative `sha256 d730c74d186ebcc7…` → **`78bf82da537a22697a860c23822599246e0534a8c4c311e12bc3d5b857a28816`**;
tracks **691 → 709** (+18 all F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones;
ratsnest **676 → 673** (−3); journal **105 → 108** (+3 REST_INC). Real KiCad DRC identical
(`solder_mask_bridge:1 + hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; `clearance` 0).

## E — Tests

* **`router_regression.py` ALL CHECKS PASS (G1–G30), run twice, identical (deterministic).** New **G30**
  pins the increment: all four pads copper-connected (`R110.1` joins `R18.2`/`TP3.1`/`U1.15`); copper legal
  (18 trk 0.200 mm all F.Cu, ZERO vias); ADD-ONLY (XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 +
  AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54
  preserved). G18–G29 auto-generalise (the ADD-ONLY roster is derived generically from the shared journal).
* New **`incremental_probe_018.py` PASS** (integrity vs D-318 fingerprints; D-316 copper 691/67 intact;
  Phase-A 432/54 intact; 18 F.Cu tracks + 0 vias; all four pads connected; no prior pair regressed; NO
  zone re-poured; DRC histogram unchanged). `incremental_probe_006..017` + `phaseB_bringup_probe_005`
  (709/67/108; **21 routed rest nets, 143 unrouted**) all PASS. `live_fingerprint.py` bumped once (D-318).
* **Independent DRC** (`kicad-cli pcb drc --severity-error --schematic-parity`, outside the framework
  helper): `{solder_mask_bridge:1, hole_clearance:5}` error-severity, `unconnected_items:499`, **`clearance`
  = 0**, **0 schematic-parity issues** — matches the D-316 gate.
* **D-269 / D-264 / DRU board-swap A/B** (committed D-316 `d730c74d…` vs promoted D-318 `78bf82da…`, via
  the `AQROOT_BETA_V2_PROJECT` override): verdicts **IDENTICAL** — `d269` FAIL(2) == FAIL(2), `d264`
  2-failed == 2-failed, `dru` FAIL(2) == FAIL(2). These are the known pre-existing synthetic/intrinsic
  Phase-A DRU-probe flakes (characterised at D-316); the new copper is on F.Cu near the U1 MCU, far from
  the BAT power-tree corridors these synthetic probes test — **not a regression.** Live AUTH sha
  re-verified `78bf82da…` after the swap; temp project removed.

## F — Opportunity & Simplification Scan (bounded to this increment)

* **The cleanest class is available in open regions.** The screen shows many of the remaining 143 unrouted
  rest nets are same-layer no-via control/peripheral nets in uncongested regions well away from the west
  XGPIO corridor and the BAT power tree — the zero-new-mechanism momentum continues by routing them one
  clean net (or small coherent group) at a time. The vetted alternates (`UART0_TXD_DBG`, `RESERVED_SPARE`,
  `BQ25185_STAT1/2`) are ready near-term candidates.
* **Screen reuse.** `w/screen_020.py` is a reusable read-only inventory + category screen; its
  auto-classifier is a first pass only — several auto-ALLOW nets are actually converter/switching or USB-C
  connector nets and must still be vetted on measured geometry before selection (the selection stays a CTO
  judgment on evidence, not an automated pick).
* **No BOM / footprint / value / polarity / mechanical / firmware / UX change; DEVICE_SPEC unchanged** (an
  internal low-current control-net route with no external-product surface).
* **Deferred framework option preserved:** the In2/In3 inner signal layers remain fully available; the
  inner-layer west-XGPIO haul remains the concretely-justified deferred framework task (D-317) for when
  the open regions are exhausted. Nothing is foreclosed. **Open owner decisions: NONE.**

## G — Locked invariants preserved

No DRU / rule / clearance / stackup / topology / net / footprint / value / polarity / outline change; no
D-290 reauth; D-249 ≥1.20 BPP, D-269 0.300 / 0.60 BAT_MAIN, general 0.200 / applicable 0.150 signals,
≥0.25 hole-hole (D-257), D-275/D-288 bridge, In1/In4 GND roles, In2/In3 capacity, RF/USB/mechanical
reservations, every accepted increment (D-304…D-316) — all preserved (superset copper check + G-contracts).
Frozen `beta-full-reference-v1` untouched. Shared journal authoritative (108); no orphan process.

## H — NEXT: FBV2-P2-021

Route the next clean rest-of-board increment — a single net or small coherent local group in an open,
uncongested region (the vetted alternates `UART0_TXD_DBG` / `RESERVED_SPARE` / `BQ25185_STAT1+STAT2`, or a
fresh screen pick) — at its netclass Default under the D-286 real full-board gate, zero router-logic change;
add `incremental_probe_019.py` + `G31` on promote. Continue to avoid the saturated west-XGPIO F.Cu corridor
(`XGPIO2/4/5/6/7`, the pair), `U11_PROG`/`PWR_SENSE`, RF/NFC/antenna, USB, crystals/clocks, switching/
high-current/class-D, bulk rails and community-header mass; hold the inner-layer west-XGPIO haul as the
deferred framework task. **143 of 164 rest nets remain unrouted.**

**Rollback:** pre-promotion `sha256 d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d`
(committed D-316, HEAD `cacb68d` / D-317).
