# FBV2-P2-022 / D-320 — FIFTEENTH rest-of-board incremental increment routed + PROMOTED: the IR transmit carrier CONTROL leg `IR_TX_GPIO16` (2-pad, SAME-LAYER F.Cu MST, NO via), a clean increment in an OPEN region 35.2 mm clear of `BAT_PROTECTED_P`; a governed CTO ACCEPT + PROMOTE, ZERO router-logic change

**Date:** 2026-08-31
**Starting HEAD:** `8d27e3a781d1d90e2704edbbecddf7fd548c7e57` (D-319; pushed; `origin/master` identical)
**Authoritative PCB before:** `sha256 57dcc8affb6c0f85f747fba025463b9cf0897c6712709692151020f56fdb8adf` — 716 tracks / 67 vias / 6 layers / 41 zones / ratsnest 672 / journal 109 (committed D-319)
**Authoritative PCB after:** `sha256 4e706490389655cb8b68f8c15249a813072f36a9ea9e6ffaeb1fdd2194c0bf34` — **729 tracks / 67 vias / 6 layers / 41 zones / ratsnest 671 / journal 110**
**Result:** GOVERNED CTO **ACCEPT + PROMOTE** — a fifteenth rest-of-board net (`IR_TX_GPIO16`) is on the authoritative board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy CONTINUES; **no owner decision.**

---

## Summary

D-319 promoted the debug-console UART transmit line in an open region and mandated FBV2-P2-022: **route
the next clean rest-of-board increment in an OPEN region** — a single net or small coherent local group —
decide on measured merit (electrical role, pad layers, span, MST edges, congestion, netclass, via/THT
need, proximity to accepted copper / `BAT_PROTECTED_P` / reservations, and real-gate feasibility),
promoting the best coherent low-risk increment (not merely the shortest or the easiest spare); continue
avoiding the west-XGPIO F.Cu corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/radio, USB, crystals/clocks,
switching/high-current/class-D outputs, bulk rails and community-header mass, and do not accidentally route
a converter-switching or connector net merely because the automatic screen says ALLOW. The mandate
specifically flagged the three D-319 vetted alternates (`IR_TX_GPIO16`, `Net-(U1-EN)`, `RESERVED_SPARE`)
and directed that `IR_TX_GPIO16` be treated as the low-current MCU control/carrier GPIO only — distinct
from the excluded `IR_LED_A/K` emitter-power / switch path — with its exact topology and isolation verified
before selection.

A fresh **evidence-first read-only screen** of all 142 unrouted rest-of-board nets (`w/screen_020.py`)
measured, per net: pad layers (F/B/THT), pad count, bbox span, MST length, cross-layer/via need,
congestion (other-net copper items within bbox+2 mm), netclass, and a category screen — **42 ALLOW /
100 EXCL**. The auto-classifier trap documented at D-318/D-319 was re-confirmed: several auto-ALLOW nets
are actually converter-switching (`Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW`) or USB-C
connector (`Net-(J3-CC1/CC2/SHIELD)`) nets, all rejected on measured role. A focused read-only **geometry
vet** (`w/vet_021.py`) then measured the genuinely-clean functional shortlist (netclass, MST edges +
same/cross layer, straight-path nearest-other-net copper, straight-MST proximity to `BAT_PROTECTED_P`).

From that evidence the selected candidate is **`IR_TX_GPIO16`** — the MCU-side low-current **control** leg
of the IR transmit path: ESP32 (U1) GPIO16 pad `U1.9` (F.Cu SMD) → series-drive resistor `R22.1` (F.Cu
SMD). **Isolation verified:** the net `/IR_TX_GPIO16` contains exactly {`U1.9`, `R22.1`}; the far side
`R22.2` belongs to the SEPARATE net `IR_GATE` ({`Q1.1`, `R22.2`, `R23.1`} — the Q1 gate-drive / switch
node), and the IR-emitter power path is `IR_LED_A`/`IR_LED_K` (D1 anode / Q1 drain). So the series resistor
R22 isolates this MCU carrier/control GPIO from the switching output and the emitter power — exactly the
distinction the mandate required, and both the switch node and emitter-power nets are correctly EXCLUDED
and are NOT part of this increment. Both pads on F.Cu, so its single MST edge is a **SAME-LAYER F.Cu run
with NO via** — the cleanest incremental class (no through via, no In1/In4 plane re-pour, no via-clearance
risk). Measured congestion 38 (lowest of the genuine functional shortlist), and **35.2 mm clear of the
`BAT_PROTECTED_P` trunk → zero D-269 involvement**. It was chosen over `Net-(U1-EN)` (higher congestion
56, two MST edges incl. a 22 mm haul running 0.335 mm from the USB_D_MCU_N differential pair, and EN is a
more sensitive reset line) and over `RESERVED_SPARE` (a mere spare pin of lower functional merit — the
mandate directs not to pick a spare when a meaningful control net is equally clean).

`route` → `gate` → `promote` on the real full-board (D-286): route ALL OK (single same-layer F.Cu run;
the router detoured to 23.153 mm / 13 segments around the GND pinch on the straight 8.35 mm path; no via);
the gate PASSed every check; promotion re-ran the gate PASS and copied the scratch board + merged journal
onto the authoritative project. Authoritative `sha256 4e706490…`; tracks 716 → **729** (+13); vias **67**
(unchanged — no via); ratsnest 672 → **671** (−1); journal 109 → **110** (+1 REST_INC edge).

---

## A — Screen (READ-ONLY, live board, `w/screen_020.py`)

142 unrouted rest-of-board nets (≥2 pads, not power-tree scope, 0 tracks) were measured. The category
screen returned **42 ALLOW / 100 EXCL** (EXCL breakdown: 31 RF/NFC/radio, 16 switching/high-current/
rail/class-D, 15 west/east XGPIO corridor, 13 shared high-speed data/I2C bus, 8 USB, 4 RF/NFC radio SPI
subsystem, 4 community-header mass, 3 crystal/clock/bus-clock, 2 `PWR_SENSE`, 2 `U11_PROG`, 2 bulk rail).

**The auto-classifier is a FIRST pass only** (as documented at D-318/D-319). Its ALLOW list still contained
converter-switching nets whose names carry no excluded token — `Net-(L1-Pad1)`, `Net-(L1-Pad2)`,
`Net-(U13-SW)`, `Net-(U13-FB)`, `Net-(U12-PS_SYNC)`, `Net-(U12-PG)`, `BL_SW` (backlight boost SW node),
and the **16-pad `BQ25185_SYS` power net** — and USB-C connector nets `Net-(J3-CC1)`, `Net-(J3-CC2)`,
`Net-(J3-SHIELD)`. All of these were rejected on measured role before selection.

The genuinely-clean functional low-congestion ALLOW candidates were: `IR_TX_GPIO16` (IR carrier GPIO
control leg, 2-pad F.Cu, no via, cong 38), `Net-(U1-EN)` (MCU enable RC, 3-pad F.Cu, no via, cong 59),
`RESERVED_SPARE` (spare expander GPIO, 3-pad B.Cu, no via, cong 84), plus longer/more-congested
functional nets (`BOOT_N`, `DISP_DC`, `SD_CS_N`, …). `LED_A` is on the `LED_BOOST` netclass (display
backlight boost string) and is excluded as high-current/boost.

---

## B — Geometry vet (READ-ONLY, live board, `w/vet_021.py`)

Per candidate: pad positions/layers, real board netclass, MST edges (length + same/cross layer),
straight-path minimum distance to any other-net copper, and straight-MST minimum distance to
`BAT_PROTECTED_P` copper (D-269 relevance). Key results:

| net | pads | via | netclass | MST | cong | min→BAT_PROTECTED_P | verdict |
|-----|------|-----|----------|-----|------|---------------------|---------|
| **IR_TX_GPIO16** | 2 (U1.9 F, R22.1 F) | no | Default | 8.35 mm, same-layer | 38 | **35.232 mm** | **SELECTED** |
| Net-(U1-EN) | 3 (C1.2/R1.1/U1.3 F) | no | Default | 7.81 + 22.28 mm same | 59 | 40.366 mm | clean fallback |
| RESERVED_SPARE | 3 (R130.2/TP41.1/U23.7 B) | no | Default | 3.54 + 9.80 mm same | 84 | 15.503 mm | clean fallback (spare, lower merit) |
| BOOT_N | 3 (R2.2/SW1.1/U1.27 F) | no | Default | 22.38 + 25.38 mm same | 190 | 36.467 mm | clean but long |
| IR_GATE | 3 (Q1.1/R22.2/R23.1 F) | no | Default | 101.1 + 14.6 mm same | 553 | 8.054 mm | EXCLUDED (Q1 gate/switch node) |
| IR_LED_A / IR_LED_K | 4 / 2 (D1 THT + F) | no | Default | ~5 mm | 3 / 4 | 54.6 / 59.3 mm | EXCLUDED (IR-emitter power) |

**Isolation confirmed by measurement:** `IR_TX_GPIO16` = {`U1.9`, `R22.1`}; `IR_GATE` = {`Q1.1`, `R22.2`,
`R23.1`}. The series resistor R22 spans the two nets (pin 1 = MCU control leg, pin 2 = gate/switch node),
so `IR_TX_GPIO16` is exactly the low-current MCU carrier/control GPIO — distinct from the excluded switch
node (`IR_GATE`) and the emitter-power path (`IR_LED_A/K`). `IR_TX_GPIO16` is the best coherent low-risk
increment: the simplest topology (2-pad, one MST edge, both pads F.Cu → NO via, no plane re-pour), an
unambiguously clean and *meaningful* electrical role (a functional MCU control net, not a spare), the
lowest congestion of the genuine functional set, and completely clear of the D-269/`BAT_PROTECTED_P` wall.
The straight-MST 0.062 mm-to-GND figure is a pinch *indicator* only (the router detours; the real
full-board gate arbitrates) — and it did: the router laid a legal same-layer detour and the gate passed
with zero new DRC.

---

## C — Route + gate (real full-board, D-286)

New single-net `GROUPS['IR_TX_GPIO16']` (`layer='F'`, `width=200000`, `clr_pad=clr_trk=200000`, no via
keys); `incremental_router.py`/`qrouter.py` routing logic UNCHANGED.

- **`route IR_TX_GPIO16`** — ALL OK: `R22.1 → U1.9` [same F.Cu] 23.153 mm; 13 F.Cu segments, 0 via (a
  legal same-layer detour around the GND pinch on the straight 8.35 mm path). (67 existing-via obstacles
  injected on the per-route QBoard, as always.) Scratch under `checks/w/INC_IR_TX_GPIO16/`; authoritative
  untouched during the experiment.
- **`gate IR_TX_GPIO16`** — PASS every check: 0 Phase-A copper deleted/altered; 13 new items all
  target-net (0 out-of-scope); **0 zones fill-changed** (no via → no In1/In4 re-pour); `IR_TX_GPIO16`
  both pads copper-connected, open_edges 1→0; 0 prior requested pairs regressed; ratsnest 672 → 671 (−1
  exact); no new DRC class, no class increased; unconnected 499 → 499.
- **`promote IR_TX_GPIO16`** — re-ran the full gate PASS, re-checked the AUTH sha had not drifted, copied
  the scratch board + merged 1 REST_INC journal edge onto the authoritative project.

---

## D — Promoted board

`sha256 57dcc8af…` → **`4e706490389655cb8b68f8c15249a813072f36a9ea9e6ffaeb1fdd2194c0bf34`**;
tracks 716 → **729** (+13 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest
672 → **671** (−1); journal 109 → **110** (+1 REST_INC edge: `/IR_TX_GPIO16` R22.1↔U1.9, F.Cu, w=0.2,
23.153 mm). Real KiCad DRC identical: `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
unconnected_items:499}` (0 `clearance`).

---

## E — Tests / integrity

- **`router_regression.py` ALL PASS (G1–G32), deterministic twice.** New **G32** pins the increment:
  both pads copper-connected (U1.9/R22.1), copper legal (13 trk 0.200 mm all F.Cu, ZERO vias), ADD-ONLY
  (IR_TX 13 + UART 7 + IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26
  + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved). G18–G31
  auto-generalise.
- **New `incremental_probe_020.py` PASS;** `incremental_probe_006..019` + `phaseB_bringup_probe_005`
  (729/67/110; 23 routed rest nets, 141 unrouted) PASS. `live_fingerprint.py` bumped once to D-320.
  `incremental_baseline_006.json` left **stale-by-design** (reverted — the gate computes its baseline live;
  it was committed at D-313 and is intentionally not bumped per increment).
- **Independent kicad-cli DRC** (`--format json --severity-error`): 6 error-severity violations
  `{solder_mask_bridge:1, hole_clearance:5}`, 499 unconnected, **zero `clearance`** — exactly the
  maintained histogram, no new copper class.
- **D-269 / D-264 / DRU board-swap A/B** (committed D-319 board via `AQROOT_BETA_V2_PROJECT` override vs
  promoted D-320 working tree): `d269` FAIL(2) = FAIL(2) and `dru` FAIL(2) = FAIL(2) **IDENTICAL** across
  the swap. `d264` differed 2 (D-320) vs 3 (D-319) in the single A/B pass, but a four-run repeat returned
  1, 2, 2, 1 on the byte-identical D-320 board and 2, 1, 2, 2 on the byte-identical D-319 board — the
  documented intrinsic non-determinism of these synthetic Phase-A probes, not a regression (the new copper
  is F.Cu near U1 at y≈111–119, ~35 mm from the BAT-divider / U18 / sense corridors the probes examine).
  Live AUTH sha re-verified `4e706490…` after the swap; the swap directory was removed.

---

## F — Opportunity & simplification

Many of the 141 remaining rest nets are same-layer no-via control nets in open regions away from the west
corridor and the BAT tree — the incremental framework continues one clean net/group at a time. Vetted
clean alternates held for FBV2-P2-023: `Net-(U1-EN)` (MCU enable RC, F.Cu no-via, cong 59),
`RESERVED_SPARE` (spare expander GPIO, B.Cu no-via, cong 84), `BOOT_N` (MCU boot strap, F.Cu no-via,
longer). `w/screen_020.py` (read-only inventory + category screen) and `w/vet_021.py` (read-only geometry
vet: netclass / MST / nearest-copper / BPP proximity) remain the reusable evidence-first pair; both are
gitignored scratch. The In2/In3 inner-layer west-XGPIO haul remains the concretely-justified deferred
**framework** task. No product-capability / BOM / footprint / value / polarity / mechanical / firmware / UX
change was implied or made; DEVICE_SPEC unchanged.

---

## Locked-invariant preservation

No DRU / rule / clearance / stackup / topology / net / footprint / value / polarity / outline change; no
D-290 reauth. D-249 ≥1.20 mm BPP trunk, D-269 0.300/0.60 mm BAT_MAIN + 0.200/0.150 mm signal, ≥0.25 mm
hole-hole (D-257), D-275/D-288, In1/In4 GND-plane roles, In2/In3 inner-signal capacity, and all RF / USB /
mechanical reservations (D-304..D-319) preserved. Frozen `beta-full-reference-v1` untouched; journal
authoritative (110). **Rollback:** pre-promotion `sha256 57dcc8affb6c0f85f747fba025463b9cf0897c6712709692151020f56fdb8adf`
(committed D-319, HEAD `8d27e3a`).

---

## Next — FBV2-P2-023

Route the next clean rest-of-board increment (single net or small coherent local group in an open region —
e.g. `Net-(U1-EN)`, `RESERVED_SPARE`, `BOOT_N`, or a fresh `w/screen_020.py` + `w/vet_021.py` pick) at its
netclass Default under the D-286 real full-board gate; add `incremental_probe_021.py` + a `G33` contract on
promote and bump `live_fingerprint.py` once. Continue avoiding the west-XGPIO F.Cu corridor,
`U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/community-header mass, **and the
auto-ALLOW converter-switching / USB-C connector traps** (`Net-(L1-*)`, `Net-(U12/U13-*)`, `BL_SW`,
`BQ25185_SYS`, `Net-(J3-*)`). Hold the inner-layer (In2/In3) west-XGPIO haul as the deferred framework
task. 141 of 164 rest-of-board nets remain unrouted.
