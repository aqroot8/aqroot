# FBV2-P2-021 / D-319 — FOURTEENTH rest-of-board incremental increment routed + PROMOTED: the debug-console UART transmit line `UART0_TXD_DBG` (2-pad, SAME-LAYER F.Cu MST, NO via), a clean increment in an OPEN region 31.3 mm clear of `BAT_PROTECTED_P`; a governed CTO ACCEPT + PROMOTE, ZERO router-logic change

**Date:** 2026-08-31
**Starting HEAD:** `c7313cce4f26c1ab18cf44c4e542ca772b588996` (D-318; pushed; `origin/master` identical)
**Authoritative PCB before:** `sha256 78bf82da537a22697a860c23822599246e0534a8c4c311e12bc3d5b857a28816` — 709 tracks / 67 vias / 6 layers / 41 zones / ratsnest 673 / journal 108 (committed D-318)
**Authoritative PCB after:** `sha256 57dcc8affb6c0f85f747fba025463b9cf0897c6712709692151020f56fdb8adf` — **716 tracks / 67 vias / 6 layers / 41 zones / ratsnest 672 / journal 109**
**Result:** GOVERNED CTO **ACCEPT + PROMOTE** — a fourteenth rest-of-board net (`UART0_TXD_DBG`) is on the authoritative board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy CONTINUES; **no owner decision.**

---

## Summary

D-318 promoted the first clean increment outside the saturated west-XGPIO F.Cu corridor and mandated
FBV2-P2-021: **route the next clean rest-of-board increment in an OPEN, uncongested region** — a single
net or small coherent local group — decide on measured merit (electrical role, pad layers, span, MST
edges, congestion, netclass, via/THT need, proximity to accepted copper / `BAT_PROTECTED_P` / reservations
and real-gate feasibility), promoting the best coherent low-risk increment (not merely the shortest);
prefer a functional pair/group only if truly local and independently clean, and **do not force a pair
across a characterized power-tree wall**; continue avoiding the west-XGPIO F.Cu corridor,
`U11_PROG`/`PWR_SENSE`, RF/NFC/radio, USB, crystals/clocks, switching/high-current/class-D outputs, bulk
rails and community-header mass, and do not accidentally route a converter-switching or connector net
merely because the automatic screen says ALLOW.

A fresh **evidence-first read-only screen** of all 143 unrouted rest-of-board nets (`w/screen_020.py`)
measured, per net: pad layers (F/B/THT), pad count, bbox span, MST length, cross-layer/via need,
congestion (other-net copper items within bbox+2 mm), netclass, and a category screen — **43 ALLOW /
100 EXCL**. The auto-classifier trap documented at D-318 was re-confirmed: several auto-ALLOW nets are
actually converter-switching (`Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW`, and the
16-pad power net `BQ25185_SYS`) or USB-C connector (`Net-(J3-CC1/CC2/SHIELD)`) nets, all rejected on
measured role. A focused read-only **geometry vet** (`w/vet_021.py`) then measured the genuinely-clean
functional shortlist: netclass, MST edges (length + same/cross layer), straight-path nearest-other-net
copper, and straight-MST proximity to `BAT_PROTECTED_P`.

From that evidence the selected candidate is **`UART0_TXD_DBG`** — the ESP32 (U1) UART0 transmit output
brought out to the debug test point (`U1.37` F.Cu SMD → `TP35.1` F.Cu SMD), a dedicated point-to-point
2-pad net. Both pads on F.Cu, so its single MST edge is a **SAME-LAYER F.Cu run with NO via** — the
cleanest incremental class (no through via, no In1/In4 plane re-pour, no via-clearance risk). Noncritical
low-speed CMOS debug output (not switching / rail / RF-NFC / USB / bus-clock / community-header). Measured
congestion 9 (lowest of the clean shortlist), and **31.3 mm clear of the `BAT_PROTECTED_P` trunk → zero
D-269 involvement**. The vetted `BQ25185_STAT1/STAT2` charger-status pair was measured **NOT low-risk**
(STAT2 straight-MST **0.024 mm** from `BAT_PROTECTED_P`, both 4-pad hauls thread the U11/BQ25185
power-tree wall) and rejected under the "do not force a pair across a characterized power-tree wall"
directive; `IR_LED_A`/`IR_LED_K` were set aside as the IR-emitter power / Q1 switch node.

`route` → `gate` → `promote` on the real full-board (D-286): route ALL OK (single same-layer F.Cu run,
31.755 mm, no via); the gate PASSed every check; promotion re-ran the gate PASS and copied the scratch
board + merged journal onto the authoritative project. Authoritative `sha256 57dcc8af…`; tracks 709 →
**716** (+7); vias **67** (unchanged — no via); ratsnest 673 → **672** (−1); journal 108 → **109** (+1
REST_INC edge).

---

## A — Screen (READ-ONLY, live board, `w/screen_020.py`)

143 unrouted rest-of-board nets (≥2 pads, not power-tree scope, 0 tracks) were measured. The category
screen returned **43 ALLOW / 100 EXCL** (EXCL breakdown: 31 RF/NFC/radio, 16 switching/high-current/
rail/class-D, 15 west/east XGPIO corridor, 13 shared high-speed data/I2C bus, 8 USB, 4 RF/NFC radio SPI
subsystem, 4 community-header mass, 3 crystal/clock/bus-clock, 2 `PWR_SENSE`, 2 `U11_PROG`, 2 bulk rail).

**The auto-classifier is a FIRST pass only** (as documented at D-318). Its ALLOW list still contained
converter-switching nets whose names carry no excluded token — `Net-(L1-Pad1)`, `Net-(L1-Pad2)`,
`Net-(U13-SW)`, `Net-(U13-FB)`, `Net-(U12-PS_SYNC)`, `Net-(U12-PG)`, `BL_SW` (backlight boost SW node),
and the **16-pad `BQ25185_SYS` power net** — and USB-C connector nets `Net-(J3-CC1)`, `Net-(J3-CC2)`,
`Net-(J3-SHIELD)`. All of these were rejected on measured role before selection.

The genuinely-clean functional low-congestion ALLOW candidates were: `UART0_TXD_DBG` (2-pad F.Cu, no via,
cong 9), `IR_TX_GPIO16` (IR carrier GPIO drive, 2-pad F.Cu, no via, cong 38), `Net-(U1-EN)` (MCU enable
RC, 3-pad F.Cu, no via, cong 56), `RESERVED_SPARE` (spare expander GPIO, 3-pad B.Cu, no via, cong 84),
and the vetted `BQ25185_STAT1`/`STAT2` charger-status pair (4-pad B.Cu, no via, cong 303/361).

---

## B — Geometry vet (READ-ONLY, live board, `w/vet_021.py`)

Per candidate: pad positions/layers, real board netclass, MST edges (length + same/cross layer),
straight-path minimum distance to any other-net copper, and straight-MST minimum distance to
`BAT_PROTECTED_P` copper (D-269 relevance). Key results:

| net | pads | via | netclass | MST | cong | min→BAT_PROTECTED_P | verdict |
|-----|------|-----|----------|-----|------|---------------------|---------|
| **UART0_TXD_DBG** | 2 (U1.37 F, TP35.1 F) | no | Default | 27.9 mm, same-layer | 9 | **31.309 mm** | **SELECTED** |
| IR_TX_GPIO16 | 2 (R22.1 F, U1.9 F) | no | Default | 8.35 mm same | 38 | 35.232 mm | clean fallback |
| Net-(U1-EN) | 3 (C1.2/R1.1/U1.3 F) | no | Default | 7.81 + 22.28 mm same | 56 | 40.366 mm | clean fallback |
| RESERVED_SPARE | 3 (R130.2/TP41.1/U23.7 B) | no | Default | 3.54 + 9.80 mm same | 84 | 15.503 mm | clean fallback |
| BQ25185_STAT1 | 4 (R127.2/TP6.1/U11.9/U2.9 B) | no | Default | 16.6/17.4/14.2 mm | 303 | 1.083 mm | **REJECTED** (power-tree wall) |
| BQ25185_STAT2 | 4 (R128.2/TP7.1/U11.3/U2.10 B) | no | Default | 14.6/15.4/14.9 mm | 361 | **0.024 mm** | **REJECTED** (power-tree wall) |
| IR_LED_A / IR_LED_K | 4 / 2 (D1 THT + F) | no | Default | ~5 mm | 3 / 4 | 54.6 / 59.3 mm | set aside (IR-emitter switch node) |

`UART0_TXD_DBG` is the best coherent low-risk increment: the simplest possible topology (2-pad, one MST
edge, both pads on F.Cu → NO via, no plane re-pour), an unambiguously clean electrical role (a dedicated
debug-console TX line, not a shared bus), the lowest congestion of the clean set, and completely clear of
the D-269/`BAT_PROTECTED_P` wall. The `BQ25185_STAT1/STAT2` pair — the mandate's example of a possible
functional pair — was measured to run within 0.024 mm of `BAT_PROTECTED_P` through the characterized
U11/BQ25185 power-tree wall, so forcing that pair was correctly declined.

---

## C — Route + gate (real full-board, D-286)

New single-net `GROUPS['UART0_TXD_DBG']` (`layer='F'`, `width=200000`, `clr_pad=clr_trk=200000`, no via
keys); `incremental_router.py`/`qrouter.py` routing logic UNCHANGED.

- **`route UART0_TXD_DBG`** — ALL OK: `TP35.1 → U1.37` [same F.Cu] 31.755 mm; 7 F.Cu segments, 0 via.
  (67 existing-via obstacles injected on the per-route QBoard, as always.) Scratch under
  `checks/w/INC_UART0_TXD_DBG/`; authoritative untouched during the experiment.
- **`gate UART0_TXD_DBG`** — PASS every check: 0 Phase-A copper deleted/altered; 7 new items all
  target-net (0 out-of-scope); **0 zones fill-changed** (no via → no In1/In4 re-pour); `UART0_TXD_DBG`
  both pads copper-connected, open_edges 1→0; 0 prior requested pairs regressed; ratsnest 673 → 672 (−1
  exact); no new DRC class, no class increased; unconnected 499 → 499.
- **`promote UART0_TXD_DBG`** — re-ran the full gate PASS, re-checked the AUTH sha had not drifted, copied
  the scratch board + merged 1 REST_INC journal edge onto the authoritative project.

---

## D — Promoted board

`sha256 78bf82da…` → **`57dcc8affb6c0f85f747fba025463b9cf0897c6712709692151020f56fdb8adf`**;
tracks 709 → **716** (+7 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest
673 → **672** (−1); journal 108 → **109** (+1 REST_INC edge: `/02_MCU_CORE/UART0_TXD_DBG` TP35.1↔U1.37,
F.Cu, w=0.2, 31.755 mm). Real KiCad DRC identical: `{solder_mask_bridge:1, hole_clearance:5,
lib_footprint_issues:199, unconnected_items:499}` (0 `clearance`).

---

## E — Tests / integrity

- **`router_regression.py` ALL PASS (G1–G31), deterministic twice.** New **G31** pins the increment:
  both pads copper-connected (U1.37/TP35.1), copper legal (7 trk 0.200 mm all F.Cu, ZERO vias), ADD-ONLY
  (UART 7 + IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS
  8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved). G18–G30 auto-generalise.
- **New `incremental_probe_019.py` PASS;** `incremental_probe_006..018` + `phaseB_bringup_probe_005`
  (716/67/109; 22 routed rest nets, 142 unrouted) PASS. `live_fingerprint.py` bumped once to D-319.
  `incremental_baseline_006.json` left **stale-by-design** (reverted — the gate computes its baseline live;
  it was committed at D-313 and is intentionally not bumped per increment).
- **Independent kicad-cli DRC** (`--format json --severity-error`): 6 error-severity violations
  `{solder_mask_bridge:1, hole_clearance:5}`, 499 unconnected, **zero `clearance`** — exactly the
  maintained histogram, no new copper class.
- **D-269 / D-264 / DRU board-swap A/B** (committed D-318 board via `AQROOT_BETA_V2_PROJECT` override vs
  promoted D-319 working tree): `d269` FAIL(2) = FAIL(2) and `dru` FAIL(2) = FAIL(2) **IDENTICAL** across
  the swap. `d264` differed 1 (D-319) vs 2 (D-318) in the single A/B pass, but a four-run repeat on the
  **byte-identical** D-319 board returned 1, 2, 2, 1 — the documented intrinsic non-determinism of these
  synthetic Phase-A probes, not a regression (the new copper is F.Cu near U1 at y≈108–137, 31 mm+ from the
  BAT-divider / U18 / sense corridors the probes examine). Live AUTH sha re-verified `57dcc8af…` after the
  swap; the swap directory was removed.

---

## F — Opportunity & simplification

Many of the 142 remaining rest nets are same-layer no-via control nets in open regions away from the west
corridor and the BAT tree — the incremental framework continues one clean net/group at a time. Vetted
clean alternates held for FBV2-P2-022: `IR_TX_GPIO16` (IR carrier GPIO drive, F.Cu no-via, cong 38),
`Net-(U1-EN)` (MCU enable RC, F.Cu no-via, cong 56), `RESERVED_SPARE` (spare expander GPIO, B.Cu no-via,
cong 84). `w/vet_021.py` is now a reusable read-only geometry vet (netclass / MST / nearest-copper / BPP
proximity) to complement `w/screen_020.py`; both are gitignored scratch. The In2/In3 inner-layer
west-XGPIO haul remains the concretely-justified deferred **framework** task. No product-capability / BOM /
footprint / value / polarity / mechanical / firmware / UX change was implied or made; DEVICE_SPEC
unchanged.

---

## Locked-invariant preservation

No DRU / rule / clearance / stackup / topology / net / footprint / value / polarity / outline change; no
D-290 reauth. D-249 ≥1.20 mm BPP trunk, D-269 0.300/0.60 mm BAT_MAIN + 0.200/0.150 mm signal, ≥0.25 mm
hole-hole (D-257), D-275/D-288, In1/In4 GND-plane roles, In2/In3 inner-signal capacity, and all RF / USB /
mechanical reservations (D-304..D-318) preserved. Frozen `beta-full-reference-v1` untouched; journal
authoritative (109). **Rollback:** pre-promotion `sha256 78bf82da537a22697a860c23822599246e0534a8c4c311e12bc3d5b857a28816`
(committed D-318, HEAD `c7313cc`).

---

## Next — FBV2-P2-022

Route the next clean rest-of-board increment (single net or small coherent local group in an open region —
e.g. `IR_TX_GPIO16`, `Net-(U1-EN)`, `RESERVED_SPARE`, or a fresh `w/screen_020.py` + `w/vet_021.py` pick)
at its netclass Default under the D-286 real full-board gate; add `incremental_probe_020.py` + a `G32`
contract on promote and bump `live_fingerprint.py` once. Continue avoiding the west-XGPIO F.Cu corridor,
`U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass, **and the
auto-ALLOW converter-switching / USB-C connector traps** (`Net-(L1-*)`, `Net-(U12/U13-*)`, `BL_SW`,
`BQ25185_SYS`, `Net-(J3-*)`). Hold the inner-layer (In2/In3) west-XGPIO haul as the deferred framework
task. 142 of 164 rest-of-board nets remain unrouted.
