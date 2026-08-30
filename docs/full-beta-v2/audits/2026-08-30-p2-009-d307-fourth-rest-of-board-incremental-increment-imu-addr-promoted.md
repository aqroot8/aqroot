# FBV2-P2-009 / D-307 — Fourth rest-of-board incremental increment routed + PROMOTED (the BMI270 IMU I2C address-select strap `BMI270_SDO_ADDR`)

**Date:** 2026-08-30
**Class:** Governed CTO ACCEPT + PROMOTE — routine rest-of-board routing within CTO authority. **No owner decision raised.**
**Starting HEAD:** `73ea58e` (D-306; pushed; `origin/master` identical).
**Authoritative PCB:** `sha256 9c0586d8…3f62259` (494 trk / 55 via / 6 layers / 41 zones, ratsnest 695, journal 86) → **`sha256 a309f8ce022b48ef04baa2fef591c64eb1a643049ad31220a9cff24831279a50`** (502 trk / 55 via / 6 layers / 41 zones, ratsnest 693, journal 88).

---

## Summary

The fourth rest-of-board net is on the authoritative board. The same
`incremental_router.py` (baseline/route/gate/promote), with **zero new
mechanics** — only three new `GROUPS` entries screened this cycle — loaded the
D-306 promoted board and routed the **BMI270 IMU I2C address-select strap
`BMI270_SDO_ADDR`** (a 3-pad B.Cu multi-terminal net: R118.1 / R119.2 / U4.1)
WITHOUT touching a single strand of accepted Phase-A / FRONT_RGB / ACC /
DISP_RST copper. A real full-board gate proved a GENUINE no-casualty /
no-new-DRC connectivity increment (ratsnest 695→693, DRC unchanged, **every
zone byte-identical** — no via, so no plane re-pour) → **COPPER PROMOTED.**
Autonomy continues, D-275 and D-277..D-306 preserved.

This increment is notable for its **negative evidence discipline**: the two
higher-value congested 2-net candidates were each *empirically disproven on
scratch* (real router, authoritative untouched) before the pristine
single-net IMU/I2C-local fallback was routed — the fallback was EARNED, not
merely defaulted to.

---

## A — Group selection (measured; highest-value low-risk, not merely the shortest net)

Baseline `9c0586d8…` (494/55/6, ratsnest 695, journal 86). Candidates screened
by a refined READ-ONLY screen (`w/screen_009.py`) reporting per-net pad geometry
/ MST edges, layer + THT, group bbox, **and accepted-copper congestion within
bbox+1/+2 mm**, plus a footprint-local coherence dump (every remaining unrouted
multi-pad net touching the U4/U11/U14/U3 control footprints, to avoid missing a
natural cluster). All candidate nets confirmed **Default netclass** (0.200 mm
width / clearance, via 0.60/0.30) directly from the board.

Five candidates recorded (3–5 mandated); rejection rationale:

| Group | Nets | Layer | Closes | Congestion (bbox+2 mm) | Coherence | Verdict |
|---|---|---|---|---|---|---|
| **U11_PROG** | `ILIM_VSET`, `ISET` | B.Cu | 2 | 16 (BQ25185 / BPP trunk) | **strong** (same-chip U11.7/.8 charger current-program straps) | **PRIMARY → disproven** |
| **PWR_SENSE** | `VBUS_PRESENT`, `MAX17048_ALRT_N` | B.Cu | 4 | 12 (west BAT trunk / fuel-gauge) | medium (two-chip west power-status) | **fallback A → disproven** |
| **IMU_ADDR** | `BMI270_SDO_ADDR` | B.Cu | 2 | **0 (pristine)** | IMU/I2C-local strap (no clean IMU-local *pair* exists) | **fallback B → PROMOTED** |
| IMU_INT1 | `BMI270_INT1_STRAP` | F.Cu | 3 | 0, but 17 mm MST, MCU-adjacent | single long strap, not a local cluster | reject |
| IMU_COMBO | + `BMI270_INT1_RAW` | MIX | — | bbox spans 52 mm half-board, needs a via | not spatially coherent | reject |

The favored IMU/I2C-local family has **no clean multi-net local pair**: the only
other U4-touching net, `BMI270_INT1_RAW` (R18 ↔ U4), is a ~46 mm haul because R18
sits at the MCU (y≈116), not at the IMU (y≈70). Per mandate, a clean singleton is
**not** bundled with unrelated nets to hit a count; the coherent same-chip
`U11_PROG` pair was therefore chosen as primary for real value, with `PWR_SENSE`
and the pristine `IMU_ADDR` as documented fallbacks. Excluded per mandate:
community-header mass, RF/NFC, USB, crystals/clocks, switching/high-current
(e.g. the ACC_5V boost cluster — `ACC_5V_LX` is an inductor switch node),
GND/+3V3 rails, class-D SPK outputs.

## B — Two congested primaries empirically DISPROVEN (one foreground experiment at a time)

- **`route U11_PROG`** → INCOMPLETE (1/2). `ILIM_VSET` R36.1→U11.7 routed clean
  (4.857 mm B.Cu). `ISET` R37.1→**U11.8 has NO LEGAL ESCAPE** at ≥0.200 mm —
  boxed in by adjacent BQ25185 pins U11.6 (×22) / U11.9 (×22), a track (×6) and
  the board edge (×5). A pad-local placement wall, independent of routing order
  (the first net succeeded); an order/path alternative cannot clear it, and
  forcing a via onto a congested B.Cu pad is unjustified. **REJECTED.**
- **`route PWR_SENSE`** → INCOMPLETE (2/4). `VBUS_PRESENT` closed C68.1→R105.1
  (1.900) and R105.1→R104.2 (2.534) but R104.2→**TP31.1 has no legal corridor**
  even at the 0.025 mm fine grid; `MAX17048_ALRT_N` TP11.1→**U14.5 no corridor**.
  Both blocked by the west-margin `BAT_PROTECTED_P` trunk congestion.
  **REJECTED.**

Both failures confirm the congestion screen: the two high-count regions (BPP
trunk, west BAT trunk) are hard walls. The authoritative `sha256` was verified
UNCHANGED after each scratch route (`9c0586d8…` throughout). No rule was weakened,
no brute force applied.

## C — The pristine fallback: `route IMU_ADDR` → gate → promote

- **`route IMU_ADDR`** → ALL OK (2/2): R118.1↔R119.2 2.709 mm, R119.2↔U4.1
  3.454 mm; all 0.200 mm B.Cu, **0 vias**; 8 segments; scratch 502/55; AUTH sha
  UNCHANGED. (3-pad, 2-edge Prim-MST — the multi-terminal path proven at D-305.)
- **`gate IMU_ADDR`** = **PASS, every check**: no prior copper deleted/altered
  (D-306 494 trk + 55 via multiset is a SUBSET); 8 new items, all target-net;
  **only In1/In4 GND planes listed as re-pourable but ZERO fill-changed** (no via
  laid → no re-pour → all 41 zones byte-identical); `BMI270_SDO_ADDR` fully
  connected (open edges 2→0); 0 prior requested pairs regressed; ratsnest
  695→693 EXACTLY −2; no new/worse DRC class; `unconnected_items` 499→499.
- **`promote IMU_ADDR`** re-ran the gate (PASS), re-verified the AUTH sha had not
  drifted, copied scratch→authoritative and merged the 2 route entries as
  `role=REST_INC`.

## D — What is promoted (integrity)

Authoritative `sha256 9c0586d8…3f62259` → **`a309f8ce…31279a50`**; tracks
**494→502** (+8 `BMI270_SDO_ADDR`); vias **55** (unchanged — **no via**); 6
layers / 41 zones unchanged; ratsnest **695→693** (−2); journal **86→88** (+2
`REST_INC`). PCB file diff = **64 insertions / 0 deletions** — pure ADD-ONLY at
the file level (8 B.Cu `segment` lines; zero `segment`/`via`/`footprint`
deletions and zero `filled_polygon` deletions, grep-confirmed — the cleanest
increment yet, since with no via there is no plane re-pour). Real KiCad DRC
**identical** (`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
unconnected_items:499}`). Every 432 Phase-A + 20 FRONT_RGB + 31 ACC + 11
DISP_RST track and all 55 vias present byte/geometry-identical; only new copper
is the 8 IMU B.Cu tracks. No placement/DRU/netclass/footprint/value/polarity/
outline/stackup change.

## E — Tests

New contract **G21** pins the increment (`BMI270_SDO_ADDR` fully connected =
R118.1-R119.2-U4.1 one island; copper legal = 8 trk B.Cu 0.200 mm, no via;
ADD-ONLY = DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54). G18–G20 stay green
unchanged — their ADD-ONLY invariants already exclude ALL `role=REST_INC` nets
generically, so the Phase-A 432/54 pin auto-generalises. `router_regression.py` =
**ALL 92 CHECKS PASS (G1–G21)**, run twice, deterministic.

New focused probe `incremental_probe_009.py` (READ-ONLY: D-307 fingerprints,
pre-D-306 copper preserved exactly, 8-track B.Cu no-via increment,
`BMI270_SDO_ADDR` connected, no pair regressed, DRC unchanged) ALL PASS.
`incremental_probe_006/007/008.py` refreshed to the D-307 board (each still
proving its own net intact; `_008`'s "pre-DISP copper" check generalised to
exclude post-DISP increments so it stays green as the board grows) ALL PASS.
`phaseB_bringup_probe_005.py` updated (502/55/88; accepted-increment set
FRONT_RGB + ACC_3V3_CTL + DISP_RST_N + BMI270_SDO_ADDR; 164 rest nets, **7
routed, 157 unrouted**) ALL PASS.

## F — Opportunity & Simplification Scan (mandated)

The framework held with **zero new mechanics** — a same-layer B.Cu
multi-terminal net routed/gated/promoted through the existing Prim-MST +
`connect_role` path; the D-306 via/`connect_cross`/`refill_planes` machinery was
reused byte-for-byte and correctly did NOT engage (no via ⇒ no plane re-pour ⇒
all zones byte-identical). No generic need for multi-via/via-array or
In2/In3 inner-signal metadata was forced this cycle; the one-edge/one-via plane
plan was **not** evolved, because no promoted group forced it (the two
disproven congested candidates would not have needed inner-signal traverses
either — they hit pad-escape / corridor walls, not layer-capacity walls). No
BOM/recoverability/testability/firmware/UX/mechanical change forced; In2/In3
remain spare capacity. **Open owner decisions: NONE.**

## G — Integrity & rollback

Rollback = pre-promotion `sha256 9c0586d8…3f62259` (D-306; parent `73ea58e`;
restored by `git checkout` of the PCB + journal; the D-302/D-304/D-305/D-306
rollback points still stand). All locked invariants preserved: no
DRU/rule/clearance/stackup/topology/net/footprint/value/polarity/outline change;
no D-290 reauth; NO via below the D-257 ladder (this increment lays **no** via);
D-249 (≥1.20 mm BPP), D-269 (0.300 mm), 0.60 mm BAT_MAIN, 0.200/0.150 signal,
0.25 hole-hole, D-275/D-288 bridge, **In1/In4 GND roles** (both planes
byte-identical), USB/RF/mechanical reservations ENFORCED; `AQROOT_U18BPP_JOIN`
(D-297), `AQROOT_U19CAP` (D-299/G14), `AQROOT_LTCGATE_KO` (D-301/G15),
`AQROOT_U11_RETARGET` (D-302/G16), fixture split (G17), FRONT_RGB (G18/D-304),
ACC_3V3_CTL (G19/D-305), DISP_RST_N (G20/D-306), `place_003l` (D-285), D-275 and
D-277..D-306 preserved; frozen `beta-full-reference-v1` untouched; DEVICE_SPEC
unchanged (no hardware fact changed); shared journal authoritative (88 entries);
no orphan process.

## H — Next: FBV2-P2-010

Continue rest-of-board routing via the same framework (**157 of 164 rest nets
unrouted**). Both same-layer (B.Cu/F.Cu) and single-via cross-layer groups are
proven; multi-terminal MST proven. **The two congested regions are now
characterised hard walls** (BQ25185/BPP trunk — U11.8 boxed by U11.6/U11.9 +
board edge; west `BAT_PROTECTED_P` trunk — TP31/U14.5 no corridor): defer those
until a placement micro-move or a deliberate multi-via/inner-signal escape is
justified, and do NOT re-attempt them naively. Good next low-risk candidates:
short isolated 08_BUTTONS controls (e.g. `RESERVED_SPARE` B.Cu 3-pad,
`BTN_B_N`), other short single-via mixed-layer controls, or the `07_IR` /
`06_AUDIO` local non-switching straps (screen for THT/analog first). The first
increment needing MULTIPLE vias / a via array / an In2/In3 inner-signal traverse
must extend `connect_cross`/`refill_planes` deliberately (the current helper
handles exactly one via + the In1/In4 re-pour). Defer RF/NFC/USB/
community-header/rails/switching.

**PROGRESS EARNED (fourth rest-of-board increment promoted): PCB routing ~18 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical increment, not fab-readiness).**
