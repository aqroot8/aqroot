# FBV2-P2-028 / D-326 — twentieth rest-of-board increment: `BTN_UP_N` promoted (second SWx user button)

**Date:** 2026-08-31
**Decision:** D-326 (governed CTO accept + promote; ZERO router-logic change —
a `GROUPS` registry entry + comment only, on the accepted D-325 duplicate-ref MST
framework)
**Starting HEAD:** `4028157` (D-325; pushed; `origin/master` identical)
**Board before:** AUTH `sha256 35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220`,
800 tracks / 70 vias / 6 layers / 41 zones / ratsnest 662 / journal 119.
**Board after (promoted):** AUTH `sha256 adbea36b8bbcfa393f2810e989c93dbcfab4052b5538f9a7169bc71ff98b3e3f`,
821 tracks / 71 vias / 6 layers / 41 zones / ratsnest 659 / journal 122.

> **Note on the mandate's quoted board sha.** The FBV2-P2-028 mandate quoted the
> pre-work authoritative sha as `35d32343af5146b973f5231e76d252e90ddf796d274e63200da5ea41e5767ea7`.
> The live board file, `live_fingerprint.py`, the D-325 commit and CURRENT_STATE
> all agree the true D-325 sha is `35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220`
> — the two strings share only the 16-char abbreviation prefix `35d32343af5146b9`
> and diverge after it. The live board hashed byte-for-byte to the repo's own
> single-source-of-truth value, so work proceeded on that (verified) basis; the
> mandate's tail was a transcription artifact, not a board discrepancy.

## Outcome

The twentieth rest-of-board incremental increment and the SECOND net of the `SWx`
user-button family, routed on the SAME bounded D-325 duplicate-ref MST framework
(no framework change this time — only a registry entry). `BTN_UP_N`, the
navigation D-pad **UP** button, was routed and PASSED the real full-board gate,
and was PROMOTED. It is CLEANER than `BTN_B_N`: **one** through via, not two.

## The candidate screen (read-only, live D-325 board)

The remaining `SWx` family is `BTN_A/UP/DOWN/LEFT/RIGHT_N` + `Net-(SW9-A)`; every
`BTN_*_N` shares `BTN_B_N`'s exact topology — its switch (SW2–SW6) is the SAME
4-pin `SW_SPST_PTS645Sx43SMTR92` tact switch whose two mechanically-linked
terminals BOTH carry pad NUMBER "1" (7.96 mm apart), plus a B.Cu pull-up (R4–R8)
and a B.Cu PCAL9535A expander GPIO (U2.13–U2.17). Two independent read-only
screens on the live board (`w/screen_020.py` bbox congestion + a faithful
`physical_net_pads`/`mst_edges` route-plan vet mirroring what the router would lay)
measured all five:

| net | switch | cross-haul | bbox cong | straight-MST → BPP | vias |
|---|---|---|---|---|---|
| **BTN_UP_N** | SW2 (south field) | **12.33 mm** | **201** | 7.453 mm | 1 |
| BTN_A_N | SW6 (west-central) | 42.35 mm | 429 | 9.250 mm | 1 |
| BTN_DOWN_N | SW3 (far west) | 44.00 mm | 352 | 8.891 mm | 1 |
| BTN_LEFT_N | SW4 (far west) | 50.15 mm | 568 | 9.403 mm | 1 |
| BTN_RIGHT_N | SW5 (far-far west) | 56.89 mm | 508 | 5.483 mm | 1 |

Every nav button is a 1-via increment (its two F.Cu switch lands connect to each
other by a same-layer F.Cu land-run — the duplicate-land edge the D-325 lever
enables — so only the haul to the R/U2 cluster needs a via; this is CLEANER than
`BTN_B_N`, whose pull-up sat between its two lands forcing two vias). `BTN_UP_N`
is decisively the cleanest by BOTH screens: the shortest cross-haul (12.33 mm) AND
the lowest nav-button congestion (201), because SW2 sits in the SAME open south
button field where `BTN_B_N` (SW7) already routed and PASSED the gate. The west
buttons' 42–57 mm hauls carry the corridor-wall risk that walled `BMI270_INT1_RAW`
(48 mm) and `DISP_CS_N`.

**Excluded, not part of the clean user-button set:** `Net-(SW9-A)` is a 5-pad
power-domain net (SW9 is the SPDT power slide switch; the net touches U12.12, a
converter-switching pin — the auto-classifier trap class) and `BOOT_N` is the
characterized sensitive ESP32 boot-mode strap (D-322: poor 2.5× detours across the
congested MCU interior). Both correctly declined per the mandate's exclusions.

## The increment

`BTN_UP_N` = {`SW2.1` button (two F.Cu lands at `(60.220,96.750)` and
`(68.180,96.750)`), `R4.2` pull-up (B.Cu), `U2.13` expander GPIO (B.Cu)}. The
physical-pad MST is:

- `SW2.1a ↔ SW2.1b` — 7.96 mm SAME-LAYER F.Cu land-run, NO via (the duplicate-land
  edge the D-325 `physical_net_pads` lever enables);
- `R4.2 ↔ U2.13` — SAME-LAYER B.Cu run (routed as a 28.821 mm legal detour around
  the congested R4/U2 cluster), NO via;
- `U2.13 ↔ SW2.1` — the single CROSS-LAYER edge, closed by exactly ONE 0.60/0.30
  Default THROUGH via at `(61.100,95.400)` in the OPEN south button field (the
  D-306/D-308/D-325 In1/In4 re-pour mechanic runs once for the one anti-pad).

Default netclass (0.200 mm). Realized: **21 tracks** (6 F.Cu + 15 B.Cu), **1
through via**. ZERO router-logic change — only `GROUPS['BTN_UP_N']` + its comment
were added; `physical_net_pads`/`net_open_edges`/`qrouter.py` are byte-unchanged
from D-325.

## Gate (real full-board, all 10 checks PASS)

- no Phase-A copper deleted or altered; every new copper item is a target-group
  net; copper actually added (22 items); only In1/In4 GND planes re-poured (`[39,40]`).
- **target net fully connected by copper: `BTN_UP_N` pads=4 `open_edges 3→0`** —
  all four physical pads (both `SW2.1` lands + `R4.2` + `U2.13`) in one cluster.
- all Phase-A requested pairs still copper-connected.
- **ratsnest dropped by exactly the requested connections 662 → 659 (−3)** — the
  true KiCad count for a 4-land net.
- no new DRC violation class; no DRC class increased; `unconnected_items` 499→499.

Promote: AUTH `35d32343…` → `adbea36b…`, journal 119 → 122 (3 REST_INC edges).

## Integrity + tests (deterministic, twice)

- `router_regression.py` ALL PASS **G1–G38**, deterministic across two runs.
  - **G38** pins the increment: all four pads copper-connected (both `SW2.1` lands
    joined to the `R4.2` hub + `U2.13`), copper legal (21 trk 0.200 mm = 6 F.Cu +
    15 B.Cu, exactly 1 0.60/0.30 through via), the via ≥ 0.80 mm from every barrel
    (measured 4.804 mm), ADD-ONLY.
  - **G37 retained** — the D-325 duplicate-ref MST framework lever, unchanged.
  - **G1–G37 unchanged** — this increment touches no routing logic.
- `incremental_probe_006..025` + `phaseB_bringup_probe_005` (821/71/122; **28
  routed rest nets, 136 unrouted**) ALL PASS. `incremental_probe_025.py` is new and
  proves both `SW2.1` lands are copper-joined to the `R4.2` hub and all four
  physical pads form one cluster (realized copper 6.370 mm clear of BPP).
  `live_fingerprint.py` bumped ONCE to D-326; `phaseB_bringup_probe_005.py` roster
  extended by `BTN_UP_N` (27→28 accepted routed).
- Independent kicad-cli DRC identical to D-325 (`solder_mask_bridge:1 +
  hole_clearance:5 [+ lib_footprint_issues:199 warnings]`; `unconnected_items:499`;
  0 `clearance`).
- D-269/D-264/DRU A/B swap (committed D-325 board vs promoted D-326 board, via
  `AQROOT_BETA_V2_PROJECT` override): `d269` flips PASS↔FAIL(2) on BOTH (B:
  PASS,FAIL,FAIL,PASS / A: FAIL,FAIL,FAIL,PASS; count always 2); `d264` 2-failed on
  BOTH (B no worse than A); `dru` FAIL(2) IDENTICAL on both. All are the documented
  western battery/power-tree synthetic-probe intrinsic flake, NONE involving
  `BTN_UP_N` (which sits in the south button field 7.453 mm from BPP, realized
  copper 6.370 mm). No regression. `incremental_baseline_006.json` left
  stale-by-design.

## Opportunity & Simplification Scan

No repetitive-maintenance consolidation was due this increment (one fingerprint
bump, one new probe, one new G-contract, one roster line — all expected for a
promotion; the D-323 via-total generalization and the D-325 framework lever
already removed the prior hand-edit toil). The `SWx` user-button family remains
the largest coherent unlocked block: **four nav buttons remain** (`BTN_A/DOWN/LEFT/
RIGHT_N`), each a 1-via increment, but all with 42–57 mm cross-hauls that must be
judged case-by-case against the corridor-wall risk (the mandate's "one bounded
alternative if the first fails geometrically" discipline applies). No premature
generalization is warranted while each remaining member's haul geometry differs.

## Governance

No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC
unchanged. **Open owner decisions: NONE** (autonomy continues). All locked
invariants preserved (D-249/D-257/D-269/D-275/D-288/D-290, In1/In4 GND roles,
In2/In3 capacity, RF/USB/mechanical reservations, D-304..D-325); frozen
`beta-full-reference-v1` untouched; journal authoritative (122). Rollback:
pre-promotion `sha256 35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220`
(committed D-325, parent `4028157`). PCB routing ~19 %, overall ~76 %, readiness
~78 % (JLCPCB file unchanged).

**NEXT FBV2-P2-029:** route the next `SWx` nav button (a fresh screen + geometry
vet first — the west buttons' long hauls need the wall-risk check) or the next
genuinely-clean functional open-region net, under the D-286 gate + adding
`incremental_probe_026` + `G39` on promote; retain G37/G38; keep avoiding the west
XGPIO F.Cu corridor, `U11_PROG`/`PWR_SENSE`, RF/NFC/USB/crystals/switching/class-D/
rails/community-header mass, the auto-ALLOW converter/USB-C connector traps
(`Net-(SW9-A)` incl.), the sensitive `BOOT_N` strap, and every characterized wall
(`MCU_EN_RC`, J1 display-FPC `DISP_CS_N`/`DISP_DC`, `DISP_BL_CTL_STRAP`,
`BMI270_INT1_RAW`, `ACC_POWER_FAULT_N`); hold the inner-layer west-XGPIO haul as
the deferred framework task.
