# FBV2-P2-023 / D-321 — SIXTEENTH rest-of-board incremental increment routed + PROMOTED: the microSD SPI chip-select `SD_CS_N` (3-pad, SAME-LAYER F.Cu MST, NO via), a clean increment in an OPEN region 50.1 mm clear of `BAT_PROTECTED_P`; the mandate's headline candidate `Net-(U1-EN)` hit a characterized local wall and was set aside; a governed CTO ACCEPT + PROMOTE, ZERO router-logic change

**Date:** 2026-08-31
**Starting HEAD:** `bb7fed46c2d01fe151b7ce3af2a0e340c5461195` (D-320; pushed; `origin/master` identical)
**Authoritative PCB before:** `sha256 4e706490389655cb8b68f8c15249a813072f36a9ea9e6ffaeb1fdd2194c0bf34` — 729 tracks / 67 vias / 6 layers / 41 zones / ratsnest 671 / journal 110 (committed D-320)
**Authoritative PCB after:** `sha256 68d44b54df91d607f689215c0da5db249b13fcd1ac189b9ab78ceb6366d25e46` — **749 tracks / 67 vias / 6 layers / 41 zones / ratsnest 669 / journal 112**
**Result:** GOVERNED CTO **ACCEPT + PROMOTE** — a sixteenth rest-of-board net (`SD_CS_N`) is on the authoritative board with **no Phase-A / prior-increment casualty and no new DRC**; autonomy CONTINUES; **no owner decision.**

---

## Summary

D-320 promoted the IR transmit carrier control leg in an open region and mandated FBV2-P2-023: **route
the next clean rest-of-board increment in an OPEN region** — a single net or small coherent local group —
deciding on measured merit (electrical role, pad layers, span, MST edges, congestion, netclass, via/THT
need, proximity to accepted copper / `BAT_PROTECTED_P` / reservations, real-gate feasibility), promoting
the best coherent low-risk increment (a meaningful coherent functional net preferred over an easy spare
when equally clean), and treating **MCU EN / BOOT sensitivity carefully**. Continue avoiding the west-XGPIO
F.Cu corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/radio, USB, crystals/clocks, switching/high-current/class-D
outputs, bulk rails and community-header mass, and do not accidentally route a converter-switching or USB-C
connector net merely because the automatic screen says ALLOW. The mandate directed deeply vetting
`Net-(U1-EN)`, `RESERVED_SPARE`, `BOOT_N` plus 1–2 other genuinely functional open-region candidates.

A fresh **evidence-first read-only screen** of all 141 unrouted rest-of-board nets (`w/screen_020.py`)
measured, per net: pad layers (F/B/THT), pad count, bbox span, MST length, cross-layer/via need,
congestion (other-net copper items within bbox+2 mm), netclass, and a category screen — **41 ALLOW /
100 EXCL**. The auto-classifier trap documented at D-318..D-320 was re-confirmed: several auto-ALLOW nets
are actually converter-switching (`Net-(L1-Pad1/2)`, `Net-(U13-SW/FB)`, `Net-(U12-*)`, `BL_SW`) or USB-C
connector (`Net-(J3-CC1/CC2/SHIELD)`) nets, all rejected on measured role. A focused read-only **geometry
vet** (`w/vet_021.py`) then measured the genuinely-clean functional shortlist (netclass, MST edges +
same/cross layer, straight-path nearest-other-net copper, straight-MST proximity to `BAT_PROTECTED_P`).

The mandate's headline candidate **`Net-(U1-EN)`** (the ESP32 EN power-on-reset RC network: `U1.3` EN +
`R1.1` pull-up + `C1.2` filter cap) — the cleanest by bbox congestion (66) — was **scratch-tested FIRST**
and hit a **characterized LOCAL WALL**: its natural MST short edge `C1.2 ↔ U1.3` (7.81 mm) has **NO LEGAL
CORRIDOR at 0.200 mm** (router `NO_PATH` even at the 0.05/0.025 mm fine grid), the EN pin `U1.3` sitting in
a dense pad pocket (U1 pin row + C1 + neighbouring parts, with the D-320 `IR_TX_GPIO16` detour copper
0.101 mm away on the straight line), and the other edge `U1.3 ↔ R1.1` only routes with a **58.46 mm
detour** (2.6× the 22.28 mm straight) — a poor, long path for a reset line that also carries the
`USB_D_MCU_N`-proximity flag. Treating the EN sensitivity carefully, EN was **NOT promoted**.

The held functional alternate **`SD_CS_N`** — the microSD socket SPI chip-select: MCU pad `U1.25`
(F.Cu SMD) + series/pull `R25.2` (F.Cu SMD) + microSD socket `J2.2` (F.Cu SMD) — was then routed and
gated: a genuine functional **point-to-point control** (NOT a shared MOSI/MISO/CLK bus line — a chip-select
travels with its own synchronous SPI-A bus, so proximity to `SPI_A_MOSI` is benign), all three pads on
F.Cu → both MST edges are **SAME-LAYER F.Cu runs with NO via** (the cleanest incremental class), and
**50.1 mm clear of `BAT_PROTECTED_P` → zero D-269 involvement**. It was chosen over `RESERVED_SPARE` (a
spare expander GPIO of lower functional merit — the mandate directs not to pick a spare when a meaningful
control net is equally clean; `RESERVED_SPARE` routed ALL OK on scratch and is **held** as a clean
alternate for FBV2-P2-024).

`route` → `gate` → `promote` on the real full-board (D-286): route ALL OK (`J2.2 ↔ U1.25` 48.42 mm +
`U1.25 ↔ R25.2` 21.08 mm; 20 F.Cu segments, 0 via); the gate PASSed every check; promotion re-ran the gate
PASS and copied the scratch board + merged journal onto the authoritative project. Authoritative
`sha256 68d44b54…`; tracks 729 → **749** (+20); vias **67** (unchanged — no via); ratsnest 671 → **669**
(−2); journal 110 → **112** (+2 REST_INC edges).

---

## A — Screen (READ-ONLY, live board, `w/screen_020.py`)

141 unrouted rest-of-board nets (≥2 pads, not power-tree scope, 0 tracks) were measured. The category
screen returned **41 ALLOW / 100 EXCL** (EXCL breakdown: 31 RF/NFC/radio, 16 switching/high-current/
rail/class-D, 15 west/east XGPIO corridor, 13 shared high-speed data/I2C bus, 8 USB, 4 RF/NFC radio SPI
subsystem, 4 community-header mass, 3 crystal/clock/bus-clock, 2 `PWR_SENSE`, 2 `U11_PROG`, 2 bulk rail).

**The auto-classifier is a FIRST pass only** (as documented at D-318..D-320). Its ALLOW list still
contained converter-switching nets whose names carry no excluded token — `Net-(L1-Pad1)`, `Net-(L1-Pad2)`,
`Net-(U13-SW)`, `Net-(U13-FB)`, `Net-(U12-PS_SYNC)`, `Net-(U12-PG)`, `BL_SW` (backlight boost SW node),
and the 16-pad `BQ25185_SYS` power net — the IR-emitter power path `IR_LED_A`/`IR_LED_K` (D1 anode / Q1
drain switch node), and USB-C connector nets `Net-(J3-CC1)`, `Net-(J3-CC2)`, `Net-(J3-SHIELD)`. All were
rejected on measured role before selection.

The genuinely-clean functional low-congestion ALLOW candidates were: `Net-(U1-EN)` (MCU enable RC, 3-pad
F.Cu, no via, cong 66), `RESERVED_SPARE` (spare expander GPIO, 3-pad B.Cu, no via, cong 84), `SD_CS_N`
(microSD SPI chip-select, 3-pad F.Cu, no via, cong 102), plus longer/more-congested functional nets
(`BOOT_N` cong 203, `DISP_DC` cong 203, `DISP_CS_N`, `DISP_BL_CTL_STRAP`, …).

---

## B — Geometry vet (READ-ONLY, live board, `w/vet_021.py`)

Per candidate: pad positions/layers, real board netclass, MST edges (length + same/cross layer),
straight-path minimum distance to any other-net copper, and straight-MST minimum distance to
`BAT_PROTECTED_P` copper (D-269 relevance). Key results:

| net | pads | via | netclass | MST | cong | min→BAT_PROTECTED_P | verdict |
|-----|------|-----|----------|-----|------|---------------------|---------|
| **SD_CS_N** | 3 (J2.2/R25.2/U1.25 F) | no | Default | 14.99 + 31.98 mm same | 102 | **50.076 mm** | **SELECTED** |
| Net-(U1-EN) | 3 (C1.2/R1.1/U1.3 F) | no | Default | 7.81 + 22.28 mm same | 66 | 40.366 mm | **CHARACTERIZED WALL** (see C) |
| RESERVED_SPARE | 3 (R130.2/TP41.1/U23.7 B) | no | Default | 3.54 + 9.80 mm same | 84 | 15.503 mm | clean; HELD (spare, lower merit) |
| BOOT_N | 3 (R2.2/SW1.1/U1.27 F) | no | Default | 22.38 + 25.38 mm same | 203 | 36.467 mm | clean but long; sensitive strap |
| DISP_DC | 2 (J1.37/U1.22 F) | no | Default | 38.55 mm same | 203 | 15.940 mm | clean but long single haul |

The straight-path nearest-other-copper figures are **pinch indicators only** (the router detours; the real
full-board gate arbitrates). `SD_CS_N`'s straight `U1.25↔J2.2` haul passes 0.043 mm from `SPI_A_MOSI` — but
the chip-select travels with its **own** synchronous SPI-A bus (same clock domain, no cross-domain
coupling), so that proximity is benign, and the router laid a legal 48.42 mm detour.

---

## C — MCU_EN_RC (`Net-(U1-EN)`): the characterized local wall

Per the mandate's "treat MCU EN/BOOT sensitivity carefully", `Net-(U1-EN)` was scratch-tested **first** as
the most-meaningful, lowest-congestion functional candidate. On the live D-320 board:

- The natural MST short edge **`C1.2 ↔ U1.3`** (7.81 mm) returns **`NO_PATH`** — no legal corridor at
  0.200 mm, and none even at the router's 0.05/0.025 mm fine grid. The EN pin `U1.3` sits in a dense pad
  pocket (the U1 pin row + the C1 body + neighbouring parts; the D-320 `IR_TX_GPIO16` detour copper is
  0.101 mm from the straight line), boxing the short haul.
- The other edge **`U1.3 ↔ R1.1`** routes, but only with a **58.457 mm** detour — 2.6× the 22.28 mm
  straight edge — a long, poor path for a reset line, which additionally runs ~0.335 mm (straight line)
  from the `USB_D_MCU_N` differential pair.

This is a genuine local congestion wall around the EN pin — **NOT** a fixable-by-clearance case and NOT
worth a bounded generic framework change for a net that also carries reset-line sensitivity and
USB-proximity flags. EN's bbox congestion (66) understated the local wall. The `GROUPS['MCU_EN_RC']` entry
is annotated **characterized wall — do NOT naively retry the natural MST**. (EN sensitivity was mitigated
in the analysis by noting its own filter cap C1 is on this net at the pin; the wall, not the sensitivity,
is the disqualifier.)

---

## D — Route + gate (real full-board, D-286)

New single-net `GROUPS['SD_CS_N']` (`layer='F'`, `width=200000`, `clr_pad=clr_trk=200000`, no via keys);
`incremental_router.py`/`qrouter.py` routing logic UNCHANGED. (Two candidate alternates, `MCU_EN_RC` and
`RESERVED_SPARE`, were added to `GROUPS` and scratch-tested; only `SD_CS_N` was promoted.)

- **`route SD_CS_N`** — ALL OK: `J2.2 → U1.25` [same F.Cu] 48.420 mm; `U1.25 → R25.2` [same F.Cu]
  21.081 mm; 20 F.Cu segments, 0 via. (67 existing-via obstacles injected on the per-route QBoard, as
  always.) Scratch under `checks/w/INC_SD_CS_N/`; authoritative untouched during the experiment.
- **`gate SD_CS_N`** — PASS every check: 0 Phase-A copper deleted/altered; 20 new items all target-net
  (0 out-of-scope); **0 zones fill-changed** (no via → no In1/In4 re-pour; plane-set [39,40] untouched);
  `SD_CS_N` all three pads copper-connected, open_edges 2→0; 0 prior requested pairs regressed; ratsnest
  671 → 669 (−2 exact); no new DRC class, no class increased; unconnected 499 → 499.
- **`promote SD_CS_N`** — re-ran the full gate PASS, re-checked the AUTH sha had not drifted, copied the
  scratch board + merged 2 REST_INC journal edges onto the authoritative project.

---

## E — Promoted board

`sha256 4e706490…` → **`68d44b54df91d607f689215c0da5db249b13fcd1ac189b9ab78ceb6366d25e46`**;
tracks 729 → **749** (+20 F.Cu 0.200 mm); vias **67** (unchanged — no via); 6 layers / 41 zones; ratsnest
671 → **669** (−2); journal 110 → **112** (+2 REST_INC edges: `/SD_CS_N` J2.2↔U1.25 48.420 mm + U1.25↔R25.2
21.081 mm, F.Cu, w=0.2). Real KiCad DRC identical: `{solder_mask_bridge:1, hole_clearance:5,
lib_footprint_issues:199, unconnected_items:499}` (0 `clearance`).

---

## F — Tests / integrity

- **`router_regression.py` ALL PASS (G1–G33), deterministic twice.** New **G33** pins the increment:
  all three pads copper-connected (U1.25/J2.2/R25.2), copper legal (20 trk 0.200 mm all F.Cu, ZERO vias),
  ADD-ONLY (SD_CS 20 + IR_TX 13 + UART 7 + IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28
  + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54
  preserved). G18–G32 auto-generalise.
- **New `incremental_probe_021.py` PASS;** `incremental_probe_006..020` + `phaseB_bringup_probe_005`
  (749/67/112; 24 routed rest nets, 140 unrouted) PASS. `live_fingerprint.py` bumped once to D-321.
  `incremental_baseline_006.json` left **stale-by-design** (reverted — the gate computes its baseline live;
  it was committed at D-313 and is intentionally not bumped per increment).
- **Independent kicad-cli DRC** (`--format json --severity-error --schematic-parity`): 6 error-severity
  violations `{solder_mask_bridge:1, hole_clearance:5}`, 499 unconnected, 0 schematic-parity, **zero
  `clearance`** — exactly the maintained histogram, no new copper class.
- **D-269 / D-264 / DRU board-swap A/B** (committed D-320 board via `AQROOT_BETA_V2_PROJECT` override vs
  promoted D-321 working tree): `dru` FAIL(2) = FAIL(2) **IDENTICAL** across the swap. `d269` differed
  PASS (D-320, single run) vs FAIL(2) (D-321), and `d264` differed 2 vs 3 in single runs — but four-run
  repeats proved both intrinsic: **d269 flips FAIL, PASS, FAIL, PASS on the byte-identical D-320 board**
  and **d264 flips 2, 2, 3, 2 on the byte-identical D-320 board** (and 3→2,2,2,2 across repeats on the
  byte-identical D-321 board). These are the documented intrinsic non-determinism of the synthetic Phase-A
  DRU probes, not regressions — the new copper is F.Cu near `U1.25`/`J2.2`/`R25.2`, ~50 mm from the
  BAT-divider / sense corridors the probes examine. Live AUTH sha re-verified `68d44b54…` after the swap;
  the swap directory was removed.

---

## G — Opportunity & simplification

Many of the 140 remaining rest nets are same-layer no-via control nets in open regions away from the west
corridor and the BAT tree — the incremental framework continues one clean net/group at a time. Vetted
clean alternates held for FBV2-P2-024: `RESERVED_SPARE` (spare expander GPIO, B.Cu no-via, routed clean on
scratch, cong 84) plus fresh screen picks (`BOOT_N`, `DISP_DC`, `DISP_CS_N`, …). `MCU_EN_RC` (`Net-(U1-EN)`)
is a **characterized local wall** — do not naively retry its natural MST. `w/screen_020.py` (read-only
inventory + category screen) and `w/vet_021.py` (read-only geometry vet: netclass / MST / nearest-copper /
BPP proximity) remain the reusable evidence-first pair; both are gitignored scratch. The In2/In3
inner-layer west-XGPIO haul remains the concretely-justified deferred **framework** task (the west F.Cu
corridor is saturated for second single-net hauls). No product-capability / BOM / footprint / value /
polarity / mechanical / firmware / UX change was implied or made; DEVICE_SPEC unchanged.

---

## Locked-invariant preservation

No DRU / rule / clearance / stackup / topology / net / footprint / value / polarity / outline change; no
D-290 reauth. D-249 ≥1.20 mm BPP trunk, D-269 0.300/0.60 mm BAT_MAIN + 0.200/0.150 mm signal, ≥0.25 mm
hole-hole (D-257), D-275/D-288, In1/In4 GND-plane roles, In2/In3 inner-signal capacity, and all RF / USB /
mechanical reservations (D-304..D-320) preserved. Frozen `beta-full-reference-v1` untouched; journal
authoritative (112). **Rollback:** pre-promotion `sha256 4e706490389655cb8b68f8c15249a813072f36a9ea9e6ffaeb1fdd2194c0bf34`
(committed D-320, HEAD `bb7fed4`).

---

## Next — FBV2-P2-024

Route the next clean rest-of-board increment (single net or small coherent local group in an open region —
`RESERVED_SPARE`, `BOOT_N`, `DISP_DC`, or a fresh `w/screen_020.py` + `w/vet_021.py` pick) at its netclass
Default under the D-286 real full-board gate; add `incremental_probe_022.py` + a `G34` contract on promote
and bump `live_fingerprint.py` once. Continue avoiding the west-XGPIO F.Cu corridor, `U11_PROG`/`PWR_SENSE`,
RF/NFC/USB/crystals/switching/class-D/rails/community-header mass, **and the auto-ALLOW converter-switching
/ USB-C connector traps** (`Net-(L1-*)`, `Net-(U12/U13-*)`, `BL_SW`, `BQ25185_SYS`, `Net-(J3-*)`). Do NOT
naively retry the `MCU_EN_RC` (`Net-(U1-EN)`) characterized wall. Hold the inner-layer (In2/In3)
west-XGPIO haul as the deferred framework task. 140 of 164 rest-of-board nets remain unrouted.
