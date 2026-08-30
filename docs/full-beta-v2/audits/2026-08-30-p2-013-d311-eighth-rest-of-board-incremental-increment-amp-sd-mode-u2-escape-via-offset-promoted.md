# FBV2-P2-013 / D-311 — Eighth rest-of-board incremental increment routed + PROMOTED (audio-amp SD/mode-select strap `AMP_SD_MODE`) — the hardest D-309 U2 escape sibling completed with the D-310 bounded via-site offset

**Date:** 2026-08-30
**Class:** Governed CTO ACCEPT + PROMOTE — routine rest-of-board routing within CTO authority. **No owner decision raised.**
**Starting HEAD:** `67d3ff6` (D-310; pushed; `origin/master` identical).
**Authoritative PCB:** `sha256 856f7a8adf0db9b114b9f09d7469308f921bc897aaf2ddce7f1c15c40a197114` (561 trk / 60 via / 6 layers / 41 zones, ratsnest 685, journal 96) → **`sha256 9bf429cec07654d4522121d2fb595204d06f5173ae629f2292c4d0cb9f68b314`** (580 trk / 61 via / 6 layers / 41 zones, ratsnest 683, journal 98).

---

## Summary

The eighth rest-of-board increment is on the authoritative board: the audio-amp
SD/mode-select strap **`AMP_SD_MODE`** (a static logic-level strap for the
MAX98357 class-D amplifier — R15.1/U5.4 on F.Cu → U2.7 on B.Cu; **not** the
class-D output). It is one of the two remaining **U2 west-edge escape siblings**
that the D-310 via-site offset unlocked, and it was the **hardest D-309 wall**:
the via-blind default `via_site` laid the F↔B transition **0.100 mm** from the
accepted D-306 `DISP_RST_N` barrel (D-309: +7 `clearance`). The same
`incremental_router.py` (baseline/route/gate/promote), with the **D-310 mechanism
unchanged and zero per-net tuning**, loaded the D-310 promoted board and routed
the net WITHOUT touching a single strand of accepted Phase-A / FRONT_RGB / ACC /
DISP / IMU / FRONT_RGB_LED / IR_RX_VS / TOUCH copper. A real full-board gate
proved a GENUINE no-casualty / no-new-DRC connectivity increment (ratsnest
685→683, **`clearance` stays 0**, only In1/In4 GND planes re-poured for the one
new via anti-pad) → **COPPER PROMOTED.** Autonomy continues; D-275 and
D-277..D-310 preserved.

## The mechanism was reused byte-for-byte (D-310)

No new routing mechanics. D-310 landed two generic, bounded, `qrouter.py`-UNTOUCHED
mechanisms in `incremental_router.connect_cross`:

1. **Existing-via awareness (always on):** every accepted `PCB_VIA` barrel/hole is
   injected as an obstacle onto the per-route `QBoard` instance, mirroring
   `QBoard.via()` item-for-item, because `qrouter.QBoard._scan` builds obstacles
   from pads + `PCB_TRACK` but `continue`s on `PCB_VIA`. This is what makes
   escape / via_site / **connect_role's track search** respect accepted vias.
2. **Bounded via-site offset (opt-in `via_offset`):** the F↔B transition is
   walked ~`via_offset` mm off the nearest congesting barrel via `_offset_via_site`
   (a short host-face fan-out), instead of accepting the router's nearest
   via-blind cell.

For D-311 the only change to `incremental_router.py` is adding
`via_offset=2500000` to the pre-existing `AMP_SD_MODE` (and `SD_DETECT`) GROUPS
entries and refreshing their annotations. The `_offset_via_site` bias rule
("away from the nearest existing via") is a **general** rule, not a hand-tuned U2
vector — it applied to `AMP_SD_MODE` with no code change.

## Screen (real-geometry clearance, re-measured on the D-310 board — before any gate)

READ-ONLY `w/screen_013.py` (a snapshot of the D-310 `w/screen_012.py`, which
loads the **live** authoritative board) re-measured DEFAULT vs bounded-offset via
sites against REAL existing-via copper+hole (the qrouter-blind obstacles). Because
the board now carries the two new D-310 TOUCH vias, the geometry shifted vs
D-310's pre-promotion measurement — this re-screen was essential:

| Net | site | via@ | min clearance to nearest existing via | verdict |
|---|---|---|---|---|
| `AMP_SD_MODE` U2.7 | DEFAULT | (52.95,87.70) | **0.100 mm** (DISP_RST_N) | **CLASH** (confirms D-309 +7) |
| `AMP_SD_MODE` U2.7 | **OFF 2.5 mm** | (51.55,90.20) | **1.760 mm** (now TOUCH_RST_N) | CLEAR |
| `AMP_SD_MODE` U2.7 | OFF 3.5 mm | (52.15,92.20) | 0.206 mm (TOUCH_RST_N) | too tight — collides with the new D-310 via |
| `SD_CARD_DETECT_N` U2.11 | DEFAULT | (53.00,85.10) | 1.301 mm (DISP_RST_N) | CLEAR (D-309 +2 was **track**-threading, now fixed by injection) |
| `SD_CARD_DETECT_N` U2.11 | **OFF 2.5 mm** | (53.00,82.55) | 3.850 mm (DISP_RST_N) | CLEAR (extra margin) |

Key finding: **2.5 mm is the correct offset for `AMP_SD_MODE`, not more** — at
3.5 mm the site collapses onto the freshly-added D-310 TOUCH_RST_N barrel
(0.206 mm). This is exactly why the screen was re-run on the live D-310 board
rather than reusing D-310's pre-promotion numbers.

## Route → gate → promote (each sibling tested separately on scratch first)

Per the task, the two functionally-distinct siblings were routed and gated
**separately** on scratch (authoritative untouched) before any promotion:

- **`route AMP_SD_MODE`** — ALL OK (injected 60 existing-via obstacles):
  R15.1↔U5.4 4.188 mm F.Cu (same-layer) + U5.4↔U2.7 58.487 mm cross-layer via
  @(51.55,90.20); 19 seg 0.200 mm + 1 through via 0.60/0.30; In1/In4 [39,40]
  re-poured. **`gate AMP_SD_MODE` = PASS every check** (D-310 561 trk + 60 via a
  SUBSET; 20 new items all target-net; only zones 39/40 re-poured, all other 39
  byte-identical; net connected open-edges 2→0; 0 prior pairs regressed; ratsnest
  685→683 EXACTLY −2; no new/worse DRC class, `clearance` 0→0; unconnected_items
  499→499).
- **`route SD_DETECT`** — ALL OK: J2.10↔R113.2 14.145 mm F.Cu + R113.2↔U2.11
  80.293 mm cross-layer via @(53.00,82.55); 27 seg + 1 via. **`gate SD_DETECT` =
  PASS every check** (ratsnest 685→683 EXACTLY −2; 29 new items; no new DRC).

Both passed the real full-board gate independently, with the **identical unchanged
2.5 mm-offset mechanism and zero per-net tuning**. They are functionally distinct
(audio-amp strap vs microSD card-detect), so bundling them would be
throughput-bundling (explicitly out of scope). **`AMP_SD_MODE` was promoted as
the single D-311 increment**; `SD_CARD_DETECT_N` (proven clean on scratch) is held
for **FBV2-P2-014**.

**`promote AMP_SD_MODE`** re-ran the full gate (PASS), re-verified the AUTH sha
had not drifted, copied scratch→AUTH, and merged 2 `REST_INC` journal entries.

## Promoted result

- `sha256 856f7a8a…` → **`9bf429cec07654d4522121d2fb595204d06f5173ae629f2292c4d0cb9f68b314`**
- tracks 561 → **580** (+19: 18 F.Cu + 1 B.Cu host-face fan-out)
- vias 60 → **61** (+1 offset through via @(51.55,90.20), 0.60/0.30)
- 6 layers / 41 zones; ratsnest 685 → **683** (−2); journal 96 → **98** (+2 `REST_INC`)
- PCB file diff **236 ins / 48 del** — additions **19 `(segment)` + 1 `(via)`**
  (0 seg/via/fp del, grep-confirmed); all **48 dels are In1/In4 `(xy …)`
  filled-polygon lines** (the one via anti-pad), nothing else.
- Real KiCad DRC error-severity **identical**
  (`solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
  unconnected_items:499`; **0 `clearance`**).

## Tests / artifacts

- New contract **G25** (`router_regression.py`): `AMP_SD_MODE` fully
  copper-connected across the U2 F/B hop (U5.4 joins R15.1 & U2.7); copper legal
  (19 trk 0.200 mm F.Cu+B.Cu, one 0.60/0.30 through via); **the offset cleared the
  AMP via of every existing via — min AMP-via↔other-via centre = 2.360 mm ≥ 0.80
  mm** (the via-blind default was 0.100 mm copper from DISP); ADD-ONLY (TOUCH 26 +
  IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54
  preserved). G18–G24 auto-generalise (the journal-derived `_inc_nets` keeps
  `phaseA_via`==54; G24's min-gap check re-reports 2.360 mm — the new AMP via is
  now the nearest to TOUCH_RST_N — still ≥ 0.80 mm). `router_regression.py` =
  **ALL CHECKS PASS (G1–G25)**, deterministic.
- New probe `checks/incremental_probe_013.py` PASS; `_006..012` PASS unchanged
  (pre-X checks auto-generalise via the journal); `phaseB_bringup_probe_005`
  updated (580/61/98; 14 routed rest nets, 150 unrouted) PASS.
- `live_fingerprint.py` bumped once (D-311; 9bf429ce / 580 / 61 / 683 / 98).
- Real-board `kicad-cli` DRC + pcbnew ratsnest 683 re-run independently — no new
  `clearance`.
- **`d269` / `d264` / `dru` NOT regressed** — a board-swap A/B test proves
  **BYTE-IDENTICAL verdicts (`diff` empty)** on the committed D-310 board and the
  promoted D-311 board (the pre-existing BAT_*/LTC power-tree DRU reds are far from
  the mid-board `AMP_SD_MODE` copper; the standalone DRU-synthesis proxies were
  not weakened and were not mistaken for authoritative DRC).

## Opportunity & Simplification Scan

The bounded question posed by the task: *does completing the two U2 siblings
validate a reusable corridor family, or demonstrate long-haul coupling that must
remain individually gated?*

**Answer: reusable mechanism, individually gated corridor.** Both siblings closed
with the identical unchanged 2.5 mm-offset mechanism and **zero per-net tuning** —
strong evidence the U2 west-edge escape offset is a genuinely reusable primitive
(not a hand-fit for TOUCH). BUT the two hauls are long (58.5 mm and 80.3 mm) and
traverse different mid-board regions, and the via-site geometry is sensitive to
copper added by *earlier* increments (the 3.5 mm site for `AMP_SD_MODE` collapsed
onto the freshly-added D-310 TOUCH via — 0.206 mm). Therefore each U2-family net
must still be **screened on the live board and gated on the full board
independently**; the mechanism is reusable, but auto-bundling the family would
hide real per-net corridor coupling. **Do NOT generalize to a batch U2 route.**
No BOM / recoverability / testability / firmware / UX / mechanical change forced;
In2/In3 remain spare. Non-blocking opportunity recorded: `SD_CARD_DETECT_N` is
already proven clean on scratch — FBV2-P2-014 can re-screen/route/gate it on the
D-311 board immediately.

## Rollback

Pre-promotion `sha256 856f7a8adf0db9b114b9f09d7469308f921bc897aaf2ddce7f1c15c40a197114`
(D-310; parent `67d3ff6`). All locked invariants preserved: no
DRU/rule/clearance/stackup/topology/net/footprint/value/polarity/outline change;
no D-290 reauth; the 1 via is D-257-legal 0.60/0.30 ≥ 0.50 min_via, ≥ 0.25
hole-hole; D-249 ≥1.20 BPP, D-269 0.300, BAT_MAIN 0.60,
D-257/D-258/D-263/D-264/D-266, 0.200/0.150 signal widths, D-275/D-288, In1/In4 GND
roles (only those two planes re-poured), USB/RF/mechanical reservations ENFORCED;
G18–G25 / D-304..D-311, `place_003l` (D-285), D-275 and D-277..D-310 preserved;
frozen `beta-full-reference-v1` untouched; DEVICE_SPEC unchanged; journal
authoritative (98); no orphan process.

## Next — FBV2-P2-014

150 of 164 rest-of-board nets remain unrouted. The immediate live target is the
second U2 sibling **`SD_CARD_DETECT_N`** (U2.11, `via_offset=2.5 mm` already set,
proven clean on scratch — re-screen/route/gate on the D-311 board and promote if
the real full-board gate passes), or another clean local group (`RESERVED_SPARE`,
short single-via controls). The XGPIO0…9 bank is a real 10-net target but a
~55 mm haul (screen the corridor first). Still avoid `U11_PROG` / `PWR_SENSE`
(characterised hard walls); RF/NFC/USB/crystals/community-header/rails/switching/
class-D output deferred.
