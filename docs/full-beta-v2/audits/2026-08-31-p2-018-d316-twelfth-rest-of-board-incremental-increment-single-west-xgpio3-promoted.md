# FBV2-P2-018 / D-316 — Twelfth rest-of-board incremental increment routed and PROMOTED: a SINGLE west XGPIO net (`XGPIO3`) at the 0.200 mm Default clearance — the D-315 positive lead realised, ZERO router-logic change

**Date:** 2026-08-31
**Starting HEAD:** `9f108bb1ee2d8fd87f966f4f23ba6000b4ce8ae9` (D-315; pushed; `origin/master` identical)
**Authoritative PCB before:** `sha256 95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605` — 669 trk / 66 via / 6 layers / 41 zones / ratsnest 677 / journal 104 (committed D-314; D-315 changed no copper)
**Authoritative PCB after:** `sha256 d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d` — **691 trk / 67 via / 6 layers / 41 zones / ratsnest 676 / journal 105**
**Result:** GOVERNED CTO **ACCEPT + PROMOTE** — no Phase-A / prior-increment casualty, no new DRC class, autonomy CONTINUES, **no owner decision.**

---

## Summary

FBV2-P2-017 / D-315 characterised the `XGPIO2`+`XGPIO3` adjacent PAIR as a **corridor-capacity wall** at the
D-269 0.300 mm clearance (both orders NO_FAR_RUN — the now D-313+D-314-congested F.Cu corridor admits ONE
116 mm haul, not two) and produced the decisive **positive lead**: a *single* west XGPIO net routes cleanly at
the **0.200 mm Default clearance** and keeps the D-269 0.300 mm floor to `BAT_PROTECTED_P` **by geometry**
(measured haul→BPP: XGPIO3 0.4739 mm, XGPIO2 0.6859 mm). FBV2-P2-018 realises that lead: **`XGPIO3` alone is
routed at 0.200 mm and promoted** — the twelfth rest-of-board increment and the fifth XGPIO bank member.

The 0.200 mm Default is the *correct* DRC floor here, not rule weakening: D-269's 0.300 mm governs clearance
to `BAT_PROTECTED_P`, and a single west haul clears BPP by ≥0.47 mm; the real full-board **D-269-aware KiCad
DRC** (the D-286 gate) is the arbiter and reports **no new/worse class** (`clearance` stays 0). Contrast the
D-313 EAST pilot, whose 0.200 mm haul pinched BPP and therefore genuinely needed the 0.300 mm floor — the
blanket was over-conservative for west members, exactly as the D-315 Opportunity Scan flagged.

**ZERO router-logic change** (`incremental_router.py`/`qrouter.py` mechanism untouched): the only source change
is a new single-net `GROUPS` entry `XGPIO3` at `clr_pad=clr_trk=200000`, no `via_offset`. The FBV2-P2-018 live
re-screen (`w/screen_018.py`, one managed foreground process) reproduced the D-315 measurement exactly on the
live board before route→gate→promote.

---

## A — WIP recovery: why the persisted re-screen had stalled (gitignored scratch only)

The task resumed from preserved WIP: the tracked `GROUPS['XGPIO3']` entry was already authored, and a gitignored
`w/screen_018.py` had produced SGL018_* scratch boards but stopped **before** writing `screen_018_evidence.json`.

**Root cause (diagnosed, then fixed in the gitignored screen only):** `screen_018.py` did
`from xgpio23_pair200_017 import haul_bpp_min, BPP`, and `w/xgpio23_pair200_017.py` runs its full XGPIO2+XGPIO3
**PAIR** routing driver **at module level** (lines 75-99). So the import re-routed the entire D-315-characterised
WALL on every load — the expensive, already-disproved pair — and stalled the screen before it could persist
evidence. This is the exact class of bug D-314 fixed in `w/screen_016.py` (module-level driver → guard behind
`__main__`), recurring through a cross-module import.

**Fix (gitignored `w/screen_018.py` only, zero routing-logic change):** removed the import dependency and
**inlined** the self-contained `haul_bpp_min` + `BPP` (they need only `math`/`pcbnew`); restricted the screen to
the single preferred net `/XGPIO3` (do **not** re-route XGPIO2 or the characterised pair). One managed foreground
process then ran to completion and persisted `w/screen_018_evidence.json`.

---

## B — Live re-screen (`w/screen_018.py`, one foreground process, live D-315 board = committed D-314 bytes)

`/XGPIO3` @ 0.200/0.200 mm Default clearance: **OK** — reproduces the D-315 record exactly.

| quantity | measured | floor | verdict |
|----------|----------|-------|---------|
| cross-layer via site | (55.300, 77.700) | — | 1 through via |
| via exv copper (nearest existing barrel) | **0.7038 mm** | ≥0.200 | most-separated |
| via exv hole-hole | **1.0038 mm** | ≥0.25 (D-257) | OK |
| via → BPP copper | 1.8356 mm | — | — |
| **HAUL → BPP min copper (D-269)** | **0.4739 mm** | **≥0.300** | **OK by geometry** |
| track widths | 0.200 mm | Default | legal |
| via dia/drill | 0.60/0.30 through | Default | legal |
| F.Cu haul | 118.261 mm, 22 trk (F.Cu+B.Cu) | — | — |

Authoritative sha unchanged during the screen (`95bc07be…`); only gitignored `w/SGL018_*` scratch written.

---

## C — Route → gate → promote (real full-board, `incremental_router.py`)

* **`route XGPIO3`** — ALL OK: injected 66 existing-via obstacles; `XGPIO3` R54.1→U3.7 cross-layer F/B through
  via 0.60/0.30 at (55.300,77.700), 118.261 mm; refilled exactly In1/In4 GND planes (zones 39,40) for the 1 new
  via anti-pad; all other zones untouched. Scratch only (`w/INC_XGPIO3/`), authoritative UNTOUCHED.
* **`gate XGPIO3`** — PASS every check: 0 Phase-A copper deleted/altered; 23 new items all in-scope (`/XGPIO3`);
  only In1/In4 re-poured (fill-changed zones = plane-set = [39,40]); `XGPIO3` fully connected (open_edges 1→0);
  0 prior requested pairs regressed; ratsnest **677 → 676** (exactly −1); **no new DRC class, none increased**;
  `unconnected_items` 499 → 499.
* **`promote XGPIO3`** — re-ran the gate PASS, re-checked the AUTH sha had not drifted (`95bc07be…`), copied
  scratch → authoritative, merged 1 `REST_INC` journal entry.

**Promoted:** `sha256 95bc07be…` → **`d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d`**;
tracks 669 → **691** (+22); vias 66 → **67** (+1); 6 layers / 41 zones; ratsnest 677 → **676** (−1); journal
104 → **105** (+1 REST_INC). Real KiCad DRC identical: `{solder_mask_bridge:1, hole_clearance:5,
lib_footprint_issues:199, unconnected_items:499}` — `clearance` stays 0.

---

## D — Tests / integrity

* **`router_regression.py` — ALL CHECKS PASS (G1–G29), run twice, identical (deterministic).** New **G29** pins
  the increment: `XGPIO3` fully copper-connected across the U3 F/B hop; copper legal (22 trk 0.200 mm F.Cu+B.Cu,
  one 0.60/0.30 through via); via clears every existing via (centre 1.304 mm ≥ 0.80); D-269 0.300 mm
  `BAT_PROTECTED_P` clearance kept (F.Cu edge gap **0.4739 mm**); ADD-ONLY (west-XGPIO 38 + east-XGPIO 23 + SD 28
  + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54). G18–G28
  auto-generalise (ADD-ONLY excludes all `role=REST_INC` nets via the shared journal).
* New **`incremental_probe_017.py`** — PASS (integrity vs the D-316 fingerprint; D-314 copper preserved exactly
  as 669 trk + 66 via; XGPIO3 = 22 trk + 1 via F.Cu+B.Cu; connectivity gain; only In1/In4 re-poured; real DRC
  unchanged). `incremental_probe_006..016` + `phaseB_bringup_probe_005` (691/67/105; **20 routed rest nets, 144
  unrouted**) — all PASS. `live_fingerprint.py` (single SoT) bumped once to D-316.
* **Independent DRC** (`kicad-cli pcb drc`, outside the framework helper): 205 violations =
  `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199}`, `unconnected_items:499`,
  **`clearance` = 0** — matches the gate exactly.
* **D-269 / D-264 / DRU board-swap A/B (committed D-314 `95bc07be…` vs promoted D-316 `d730c74d…`):** `dru` FAIL(2)
  on both (identical pre-existing reds); `d264` FAIL B/C on both (the D-314-characterised intrinsic
  non-determinism, unrelated U18 sense item ~45 mm away). `d269` **flipped PASS/FAIL between the two boards, but
  it flips PASS/FAIL across repeated runs on the byte-identical D-314 board too** (measured FAIL/FAIL/PASS/FAIL in
  four runs on the fixed parent) — the flake is the probe's synthetic BAT_MAIN injection + non-reproducible
  full-zone `ZONE_FILLER` re-pour, **not** a regression; the XGPIO3 copper is ~45 mm from the BAT-divider TAPs it
  examines, and the authoritative kicad-cli DRC is byte-stable with `clearance` 0. The D-316 board was restored
  and its sha re-verified (`d730c74d…`) after the swap.

---

## E — Opportunity & Simplification Scan (bounded to the XGPIO west bank)

* **A (near-free capability):** more single west XGPIO members are connectable now with this exact recipe
  (single net, 0.200 mm Default, real-gate D-269 arbitration). Route **one net at a time** — the D-315 wall was
  the two-parallel-haul contention, so do NOT force adjacent PAIRS for the congested northern west pins.
* **B (removed unnecessary constraint — DONE):** the blanket `clr_pad=clr_trk=0.300` XGPIO recipe was
  over-conservative for west members whose haul clears BPP by ≥0.47 mm. D-316 uses the correct **0.200 mm Default
  with the real D-269-aware gate arbitrating** — simpler and it does not saturate the corridor. Reserve the
  0.300 mm floor for paths that actually approach BPP (the east pilot).
* **C (recurring cross-module import hazard):** the stall was a *cross-module* recurrence of the D-314
  module-level-driver bug. Reusable lesson: gitignored read-only scratch tools must guard **all** heavy drivers
  behind `__main__` **and** be safe to import for their helpers — or the helper should be small enough to inline
  at the point of use (as done here). Non-blocking notice.
* **E/F (capacity):** In2/In3 inner **signal** layers remain fully available (F/B-only routing today); an inner
  XGPIO haul is a future option if the F.Cu corridor saturates further — a larger framework change, deferred.
* No BOM / footprint / value / polarity / mechanical / firmware / UX change; DEVICE_SPEC unchanged.

## F — Locked invariants preserved

No DRU / rule / clearance-floor / stackup / topology / net / footprint / value / polarity / outline change; no
D-290 reauth. D-249 ≥1.20 BPP, **D-269 0.300 / 0.60 BAT_MAIN kept (measured 0.4739 mm to BPP)**, general 0.200 /
applicable 0.150 signals, ≥0.25 hole-hole (D-257, measured 1.0038 mm), D-275/D-288 bridge, In1/In4 GND roles,
In2/In3 capacity, RF/USB/mechanical reservations, every accepted increment (D-304…D-314) — all preserved.
Frozen `beta-full-reference-v1` untouched. Shared journal authoritative (105); no orphan process.

## G — NEXT: FBV2-P2-019

Route the next clean increment: another **single** west XGPIO member (e.g. `XGPIO2`, BPP margin 0.686 mm, but
its via exv to the XGPIO1 barrel is tighter at 0.256 mm — re-screen live) or `XGPIO4`, **one net at a time** at
`clr_pad=clr_trk=0.200` under the D-286 real full-board gate; add `incremental_probe_018.py` + `G30`. Do **not**
re-attempt the XGPIO2+XGPIO3 PAIR (D-315 wall) or `U11_PROG`/`PWR_SENSE` (hard walls). **144 of 164 rest nets
remain unrouted.**

**Rollback:** pre-promotion `sha256 95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605` (committed
D-314, parent `9f108bb`).
