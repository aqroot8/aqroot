# FBV2-P2-026 / D-324 — CHARACTERIZATION: three pad-escape walls, no promote

**Date:** 2026-08-31
**Decision:** D-324 (governed CTO characterization; **no copper change**, zero router-logic change)
**Starting HEAD:** `89acc71` (D-323; pushed; `origin/master` identical)
**Board (unchanged):** AUTH `sha256 a7bf8bdc11f1bc39303c6f6b6c801e3a4a575add64596cc4be20745c57f9f626`,
781 tracks / 68 vias / 6 layers / 41 zones / ratsnest 665 / journal 116.

## Outcome

A characterization increment. Three genuinely-functional open-region candidates from
three different subsystems were vetted (`w/vet_021.py`) and scratch-routed
(`incremental_router.py route`, gitignored scratch only); **all three hit characterized
pad-escape walls at 0.200 mm**. No clean net remained promotable via the proven F/B
same-layer + single-through-via mechanics without a deferred framework change (which this
mandate keeps deferred). The authoritative board is byte-identical to committed D-323.

## Evidence-first screen + geometry vet

`w/screen_020.py` on the live D-323 board: **138 unrouted rest nets, 38 ALLOW / 100 EXCL**
(auto-classifier trap re-confirmed — converter-switching `Net-(L1/U12/U13-*)`/`BL_SW`/
`V3V3_FB`, IR-emitter/switch `IR_LED_A/K`/`IR_GATE`, USB-C `Net-(J3-*)` rejected on measured
role). The 38 ALLOW nets resolve to: ~6 already-characterized walls (`MCU_EN_RC`,
`DISP_CS_N`/`DISP_DC`, `DISP_BL_CTL_STRAP`, `BOOT_N`, `Net-(U11-TS_MR)`), ~7 `SWx`
duplicate-ref buttons (deferred framework), converter/USB-C role-traps, the
`BQ25185_STAT1/2` power-tree pair (near BPP), three huge cross-board hauls
(`IR_RX_GPIO44` 132 mm, `DISP_SDO` 60 mm J1, `IR_GATE` 110 mm), and only **three**
genuinely-clean functional candidates.

`w/vet_021.py` measured the three:

| net | pads | via | MST edge(s) | cong | straight-MST → BPP |
|---|---|---|---|---|---|
| `BMI270_INT1_RAW` | 2 (R18.1 F, U4.4 B) | 1 | 48.81 mm CROSS | 365 | 5.447 mm (zero D-269) |
| `ACC_POWER_FAULT_N` | 6 (all B.Cu) | 0 | 3.16–13.63 mm ×5 | 292 | 3.544 mm |
| `DISP_BL_CTL` | 2 (R109.2 F, U17.4 B) | 1 | 50.4 mm CROSS | 164 | — |

## The three characterized walls

1. **`BMI270_INT1_RAW`** — the BMI270 IMU INT1 interrupt **sensor-side** leg (`U4.4` IMU
   INT1 pin B.Cu → series `R18.1` F.Cu, R18-isolated from the D-318 MCU-side
   `BMI270_INT1_STRAP`; it would COMPLETE the IMU interrupt path the way D-308 completed
   D-304). `route` → FAIL `NO_FAR_RUN` at 0.200 mm (no legal corridor even on the
   0.05/0.025 mm fine grid): R18.1 is boxed in the dense MCU-south pocket (R18.2, the other
   pad of the same 0402, carries strap copper 0.84 mm away; USB_D_MCU diff pair + U1 pad
   row) so the 48.81 mm haul has no F.Cu exit — the `MCU_EN_RC` wall class.

2. **`ACC_POWER_FAULT_N`** — the accelerometer 3V3 power-fault status aggregation
   (`U20.6`+`U22.6` ACC load-switch fault outputs / `R103.2` / `TP27.1`+`TP33.1` → `U3.18`
   expander GPIO readback, all B.Cu). `route` → FAIL `NO_LEGAL_ESCAPE` on `U20.6`: the fault
   pin is boxed on B.Cu by its own-part neighbours (U20.5/U20.1/U20.4) + a track (3 of 5
   edges route, but the net cannot complete) — the `ISET` (U11.8, D-307) / `XGPIO2` (U3.6,
   D-315) pad-local boxed-pin class.

3. **`DISP_BL_CTL`** — the backlight-driver CONTROL leg (`R109.2` series F.Cu → `U17.4`
   TPS61169 CTRL logic input B.Cu, R109-isolated from the switch node BL_SW and the LED
   path; a defensible control-leg role, the IR_TX_GPIO16 precedent). `route` → FAIL
   `NO_FAR_RUN` at 0.200 mm: R109.2 sits in the SAME dense U1.16/backlight-strap cluster
   that walled `DISP_BL_CTL_STRAP` at D-323.

None has a bounded fix (`via_offset` cannot help a far-run failure; the escapes are
pad-local walls; placement/clearance changes are forbidden). All three `GROUPS` entries
carry their OUTCOME annotation — do NOT naively retry.

## Integrity (board unchanged → all still PASS)

- AUTH `sha256 a7bf8bdc…` re-verified before/after (route writes only gitignored scratch
  `checks/w/INC_*`); `incremental_baseline_006.json` reverted stale-by-design.
- `router_regression.py` ALL PASS (G1–G35) deterministic twice. The three additive `GROUPS`
  entries are inert (never routed, like existing `BOOT_N`/`DISP_DC`/`MCU_EN_RC` records).
- `incremental_probe_006..023` + `phaseB_bringup_probe_005` (781/68/116; 26 routed rest
  nets, 138 unrouted) ALL PASS.
- NO `live_fingerprint.py` bump (no copper). NO new probe / G-contract (no new copper to
  pin — the D-315 characterization precedent).
- Independent kicad-cli DRC identical to D-323 (`solder_mask_bridge:1 + hole_clearance:5 +
  lib_footprint_issues:199 + unconnected_items:499`; 0 `clearance`).
- D-269/D-264/DRU: byte-identical board → A/B swap trivially identical, no regression
  possible (D-315 precedent); a recorded run sits in the documented intrinsic-flake
  envelope (`d269` FAIL(2), `d264` 2-failed, `dru` FAIL(2)).

## Opportunity & Simplification Scan

The key finding is structural: after eighteen promoted increments the readily-clean
open-region functional seam reachable by the proven mechanics is essentially exhausted. The
138 remaining rest nets are dominated by role-excluded traps (~100), characterized walls,
the `SWx` duplicate-ref button family, the saturated west-XGPIO F.Cu corridor, J1
display-FPC hauls, and boxed MCU/IC-pin pockets. The highest-value NEXT move is to
explicitly SELECT one of the two long-deferred bounded framework tasks:

- **(i) duplicate-ref MST** — teach `pads_by_ref` to keep same-ref pads at distinct
  locations as separate MST nodes. UNLOCKS the whole `SWx` user-input button family
  (`BTN_A/B/UP/DOWN/LEFT/RIGHT_N` + `Net-(SW9-A)`, ~7 genuine nets; `BTN_B_N` already routed
  ALL OK at D-323 and failed only on the collapse) — the largest coherent remaining
  functional block. **Recommended.**
- **(ii) In2/In3 inner-layer traverse** — relieve the saturated west-XGPIO corridor.

No repetitive-maintenance consolidation was due (no fingerprint bump / no new probe).

## Governance

No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC unchanged.
**Open owner decisions: NONE** (the framework-task selection is a P2-027 recommendation,
not a blocking decision — autonomy continues). All locked invariants preserved
(D-249/D-257/D-269/D-275/D-288/D-290, In1/In4 GND roles, In2/In3 capacity, RF/USB/mechanical
reservations, D-304..D-323); frozen `beta-full-reference-v1` untouched; journal
authoritative (116). PCB routing ~18 %, overall ~76 %, readiness ~78 % (JLCPCB file
unchanged).
