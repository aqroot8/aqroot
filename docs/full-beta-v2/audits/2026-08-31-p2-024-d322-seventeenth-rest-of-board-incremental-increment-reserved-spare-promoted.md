# FBV2-P2-024 / D-322 — SEVENTEENTH rest-of-board incremental increment routed + PROMOTED: the reserved/spare community expander GPIO `RESERVED_SPARE` (3-pad, SAME-LAYER B.Cu MST, NO via), a clean increment in an OPEN region 15.5 mm clear of `BAT_PROTECTED_P`; the held clean alternate, promoted after the meaningful display-control candidates `DISP_CS_N`/`DISP_DC` hit a characterized J1 display-FPC-connector wall and `BOOT_N` routed only via poor 2.5× detours; a governed CTO ACCEPT + PROMOTE, ZERO router-logic change

**Date:** 2026-08-31
**Starting HEAD:** `e3e2a8d1c688ce9eba6d48701f2b7f8cc6e6c2a7` (D-321; pushed; `origin/master` identical)
**Authoritative PCB before:** `sha256 68d44b54df91d607f689215c0da5db249b13fcd1ac189b9ab78ceb6366d25e46` — 749 tracks / 67 vias / 6 layers / 41 zones / ratsnest 669 / journal 112 (committed D-321)
**Authoritative PCB after:** `sha256 a861e30e5760515288ef9a3fc0c21ea6d3e9c31409f9181dd66d56ed0628efd1` — **759 tracks / 67 vias / 6 layers / 41 zones / ratsnest 667 / journal 114**
**Result:** GOVERNED CTO **ACCEPT + PROMOTE** — a seventeenth rest-of-board net (`RESERVED_SPARE`) is on the authoritative board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy CONTINUES; **no owner decision.**

---

## Summary

D-321 promoted the microSD SPI chip-select in an open region and mandated the next clean rest-of-board
increment in an OPEN region, decided on measured merit: deeply vet `RESERVED_SPARE`, `BOOT_N`, `DISP_DC`
plus 1–2 other genuinely-functional open-region candidates; **prefer meaningful function over a spare when
equally clean**; treat `BOOT_N` sensitivity carefully; do NOT naively retry the `MCU_EN_RC` characterized
wall; do not route a converter-switching or USB-C connector net merely because the automatic screen says
ALLOW.

A fresh read-only screen (`w/screen_020.py`) measured all **140** unrouted rest nets (**40 ALLOW / 100
EXCL**). A focused read-only geometry vet (`w/vet_021.py`) measured the mandate's shortlist plus two more
genuinely-functional candidates. The **meaningful display-control candidates were tested first**:

* `DISP_CS_N` — the display SPI chip-select (`U1.18` MCU + `R26.2` series + `J1.38` display FPC), the direct
  display analog of D-321's `SD_CS_N` — routes its short MCU-side edge `R26.2↔U1.18` (2.5 mm) clean off the
  series resistor, but its long `J1.38↔R26.2` haul to the tight display connector returns **`NO_PATH` at
  0.200 mm** (none even at the 0.05/0.025 mm fine grid).
* `DISP_DC` — the display data/command (`U1.22 → J1.37`, the FPC pin adjacent to J1.38) — hauls a single
  38.5 mm edge directly off the boxed MCU pad and **also returns `NO_PATH` at 0.200 mm**.

Two adjacent display-connector nets walling on the same long interior haul **characterizes the J1
display-FPC-connector haul as a shared local wall** on the live D-321 board (`GROUPS['DISP_CS_N']`/`['DISP_DC']`
annotated — do NOT naively retry at 0.200 mm).

`BOOT_N` — the meaningful non-J1 alternative (the ESP32 boot-mode strap `SW1.1` + `R2.2` + `U1.27` GPIO0) —
routed ALL OK but only via **poor 2.5× detours** (`R2.2↔U1.27` 62.9 mm vs 25.4 mm straight, 2.48×; `U1.27↔SW1.1`
47.2 mm vs 22.4 mm, 2.11×) = ~110 mm of meandering copper across the congested MCU interior for a
**boot-critical strap** whose reset-level sensitivity the mandate flagged. Not equally clean, so the
meaningful>spare rule does not force it; `BOOT_N` set aside (sensitivity treated carefully).

The held clean alternate **`RESERVED_SPARE`** — the reserved/spare community expander GPIO (`R130.2` +
`TP41.1` test point + `U23.7` PCAL community expander), all three pads B.Cu → both MST edges SAME-LAYER B.Cu
runs with **NO via** (the cleanest incremental class), in an OPEN region **15.5 mm clear of
`BAT_PROTECTED_P` → zero D-269 involvement** — was routed, gated PASS on the real full-board D-286 gate, and
promoted. `incremental_router.py`/`qrouter.py` routing logic UNCHANGED (the `GROUPS['RESERVED_SPARE']` entry
had existed since D-321 as the held alternate).

---

## A — Screen (READ-ONLY, live board, `w/screen_020.py`)

**140 unrouted rest nets → 40 ALLOW / 100 EXCL.** EXCL breakdown: 31 RF/NFC/radio, 16 switching/rail/class-D,
15 west/east XGPIO corridor, 13 shared data/I2C bus, 8 USB, 4 RF SPI, 4 community-header, 3 crystal/clock,
2 `PWR_SENSE`, 2 `U11_PROG`, 2 bulk rail.

**The auto-classifier is a FIRST pass only** (as documented D-318..D-321). Its ALLOW list still contains
converter-switching (`Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW`), IR-emitter power
(`IR_LED_A/K`) and USB-C connector (`Net-(J3-CC1/CC2/SHIELD)`) nets — all rejected here on measured role.

---

## B — Geometry vet (READ-ONLY, live board, `w/vet_021.py`)

Measured the mandate's shortlist + two other genuinely-functional candidates (pads/layers, netclass, MST
edges same/cross + length, straight-path nearest-other copper (guidance only), straight-MST min-to-
`BAT_PROTECTED_P` for D-269):

| net | pads / layer | MST edges | BPP dist | via | role |
|-----|--------------|-----------|----------|-----|------|
| `RESERVED_SPARE` | 3 B.Cu | 3.54 + 9.80 mm | 15.503 mm | no | reserved/spare community expander GPIO (**held clean alternate**) |
| `DISP_CS_N` | 3 F.Cu | 2.50 + 32.57 mm | 15.855 mm | no | display SPI chip-select (`U1.18`/`R26.2`/`J1.38`) |
| `DISP_DC` | 2 F.Cu | 38.55 mm | 15.940 mm | no | display data/command (`U1.22`/`J1.37`) |
| `BOOT_N` | 3 F.Cu | 22.38 + 25.38 mm | 36.467 mm | no | ESP32 boot-mode strap (**sensitive**) |
| `DISP_BL_CTL_STRAP` | 4 F.Cu | 5.44 + 10.30 + 24.77 mm | 37.854 mm | no | backlight control strap |

All candidates are no-via and clear of the D-269 wall (≥15.5 mm). The vet's tiny straight-line
nearest-copper figures (e.g. `DISP_CS_N` 0.018 mm to +3V3 on its long edge) are **guidance only** — the
router detours and the real D-286 full-board gate arbitrates.

---

## C — J1 display-FPC-connector wall (`DISP_CS_N`/`DISP_DC`), and `BOOT_N` set aside

**`DISP_CS_N` (strongest meaningful pick, tested FIRST).** The short MCU-side MST edge `R26.2↔U1.18` routes
clean (2.9 mm) off the series resistor `R26`, but the long `J1.38↔R26.2` haul to the tight display FPC
connector returns **`NO_PATH` at 0.200 mm** — no legal corridor even at the 0.05/0.025 mm fine grid.

**`DISP_DC` (mandate headline candidate).** A single 38.5 mm MST edge `J1.37↔U1.22` hauling directly off the
boxed MCU pad `U1.22` to the FPC pin adjacent to `J1.38` **also returns `NO_PATH` at 0.200 mm**.

Two adjacent J1 display-connector nets walling on the same long interior haul confirms the **J1
display-FPC-connector interior haul at 0.200 mm as a shared local wall** on the live D-321 board (the tightly
pitched J1 FPC connector fans into a congested board interior corridor). `GROUPS['DISP_CS_N']` and
`GROUPS['DISP_DC']` are annotated (characterized wall — do NOT naively retry the connector haul at 0.200 mm).

**`BOOT_N` (meaningful non-J1 alternative) set aside.** It routed ALL OK but only via poor 2.5× detours:
`R2.2↔U1.27` 62.874 mm (vs 25.38 mm straight, 2.48×) + `U1.27↔SW1.1` 47.207 mm (vs 22.38 mm, 2.11×) = ~110 mm
of meandering copper across the congested MCU interior for a boot-critical strap. Per the mandate ("prefer
meaningful function over a spare **when equally clean**; treat `BOOT_N` sensitivity carefully"), a ~110 mm
detour path for a reset-level-sensitive boot strap is not equally clean vs the tidy short spare, so the
meaningful>spare preference does not force it. Set aside — not a wall, but a poor path for a sensitive net.

---

## D — Route + gate (real full-board, D-286)

**`route RESERVED_SPARE` ALL OK:** two SAME-LAYER B.Cu runs `R130.2→U23.7` 4.434 mm + `U23.7→TP41.1`
10.939 mm, 10 B.Cu segments, 0 via (minimal detour vs the 3.54 + 9.80 mm straight MST).

**`gate RESERVED_SPARE` PASS every check:** 0 Phase-A copper deleted/altered; 10 new items all target-net;
**0 zones fill-changed** (no via → no In1/In4 GND-plane re-pour); all three pads (`R130.2`/`U23.7`/`TP41.1`)
copper-connected, net open_edges 2→0; 0 prior Phase-A/increment requested pairs regressed; ratsnest 669→667
(−2 exact); no new/worse DRC class; DRC `unconnected_items` 499→499. `promote` re-ran the full gate PASS,
re-checked the AUTH sha had not drifted, copied scratch→AUTH, merged 2 `REST_INC` journal edges.

---

## E — Promoted board

`sha256 68d44b54…` → **`a861e30e5760515288ef9a3fc0c21ea6d3e9c31409f9181dd66d56ed0628efd1`**; tracks
749→**759** (+10 B.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest 669→**667**
(−2); journal 112→**114** (+2 `REST_INC`). Real KiCad DRC identical (`solder_mask_bridge:1 + hole_clearance:5
+ lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).

---

## F — Tests / integrity

* New **G34** in `router_regression.py` (all three `RESERVED_SPARE` pads connected; copper legal — 10 trk
  0.200 mm all B.Cu, 0 vias; ADD-ONLY — every prior increment + Phase-A 432/54 preserved). G18–G33
  auto-generalise. `router_regression.py` **ALL PASS (G1–G34), deterministic twice.**
* New `incremental_probe_022.py` **PASS**; `incremental_probe_006..021` + `phaseB_bringup_probe_005`
  (759/67/114; **25 routed rest nets, 139 unrouted**) **PASS**.
* `live_fingerprint.py` bumped once (D-322). `incremental_baseline_006.json` left **stale-by-design**
  (reverted — the gate computes its baseline live).
* Independent kicad-cli DRC matches (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499}`; `clearance` 0, 0 schematic-parity).
* **D-269/D-264/DRU board-swap A/B** (committed D-321 vs promoted D-322, via `AQROOT_BETA_V2_PROJECT`
  override): `d269` FAIL(2)=FAIL(2) and `dru` FAIL(2)=FAIL(2) **IDENTICAL**; `d264` differed in single runs
  (board A=3, board B=2) but four-run repeats proved intrinsic — it flips **1,2,2,2** on the byte-identical
  committed D-321 board and **2,1,1,3** on the byte-identical promoted D-322 board = documented intrinsic
  non-determinism, all pre-existing flakes not regressions (the new copper is B.Cu near U23/R130/TP41 at
  x≈52–63 / y≈93–98, ~15 mm from the BAT-divider/sense corridors these synthetic probes examine). Live AUTH
  sha re-verified `a861e30e…` after the swap.

---

## G — Opportunity & simplification

* **NEW characterized wall:** the J1 display-FPC-connector interior haul at 0.200 mm (`DISP_CS_N`/`DISP_DC`
  both `NO_PATH`) — annotated in `GROUPS`; do NOT naively retry. The remaining display connector-hauled nets
  (`DISP_SDO`, `LED_A/K`, `DISP_BL_CTL`) likely share this wall; screen before attempting.
* `BOOT_N` routes only via a poor ~110 mm detour for a sensitive boot strap — set aside, not forced.
* `MCU_EN_RC` (`Net-(U1-EN)`) remains a characterized wall (D-321).
* Many of the 139 remaining rest nets are still same-layer no-via control nets in open regions away from the
  west corridor + BAT tree — continue one clean net/group at a time; the In2/In3 inner-layer west-XGPIO haul
  stays the deferred framework task.
* No framework change was needed or made this increment; `incremental_router.py`/`qrouter.py` routing logic
  is byte-unchanged (the `GROUPS['RESERVED_SPARE']` entry existed since D-321; `GROUPS['DISP_CS_N']`/
  `['DISP_DC']`/`['BOOT_N']` were added as characterization/held entries only).

---

## Locked-invariant preservation

No DRU/rule/clearance/stackup/topology/net/footprint/value/polarity/outline change; no D-290 reauth. D-249
≥1.20 mm BPP, D-269 0.300/0.60 BAT_MAIN + 0.200/0.150 signal, ≥0.25 hole-hole (D-257), D-275/D-288,
In1/In4 GND reference-plane roles, In2/In3 inner-signal capacity, RF/USB/mechanical reservations, and
D-304..D-321 all preserved. Frozen `beta-full-reference-v1` untouched. Journal authoritative (114). No
BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged. **Open owner decisions:
NONE.** `JLCPCB_READINESS` ~78 % (authoritative; JLCPCB fabrication file unchanged).

---

## Next — FBV2-P2-025

Route the next clean rest-of-board increment (single net or small coherent local group in an open region — a
fresh `w/screen_020.py` + `w/vet_021.py` pick) at its netclass Default under the D-286 real full-board gate;
on promote add `incremental_probe_023.py` + a `G35` contract and bump `live_fingerprint.py` once. Continue
avoiding the west XGPIO F.Cu corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/rails/
community-header mass, the auto-ALLOW converter-switching/USB-C connector traps, the `MCU_EN_RC` characterized
wall, and the J1 display-connector-haul wall (`DISP_CS_N`/`DISP_DC`); hold the inner-layer west-XGPIO haul as
the deferred framework task. **139/164 rest nets unrouted.** Rollback: pre-promotion `sha256 68d44b54…`
(committed D-321, HEAD `e3e2a8d`).
