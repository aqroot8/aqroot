# FBV2-P2-033 / D-331 — In2/In3 long-haul framework; XGPIO2 pilot promoted

## Result

**NEW REUSABLE FRAMEWORK ACCEPTED; AUTHORITATIVE COPPER PROMOTED.** Starting clean pushed D-330, GPT implemented an explicit low-speed signal framework that reserves a short legal escape on each endpoint's native outer layer, places one ordinary 0.60/0.30 through via per end, and joins the anchors on In2 (fallback In3). Wide/high-current nets are refused. Groups without `inner_long_haul_plan` remain on their prior routing path.

The `XGPIO2` pilot (`R53.1` F.Cu ↔ `U3.6` B.Cu) completed on In2: 8 tracks (2 F.Cu + 2 In2.Cu + 4 B.Cu), two standard through vias at `(55.0,27.3)` and `(55.9,78.3)`, total routed length 53.817 mm. This offloads the saturated west F.Cu corridor without changing any rule, clearance, stackup role, placement, footprint, topology, or schematic.

## Full promotion gate

The unchanged D-286 gate passed every check: zero accepted copper altered, all 10 new items in scope, only In1/In4 GND planes re-poured for via anti-pads, `XGPIO2 open_edges 1→0`, every prior requested pair connected, ratsnest 656→655 exactly, no new/increased DRC class, and `unconnected_items` 499→499.

Promoted board: `sha256 98181354b3378e9cfb527e858b5120704adfa628c25ce8e6a351267a4f71e098`, 845 tracks / 75 vias / 6 layers / 41 zones / ratsnest 655 / journal 126.

## Deterministic verification

- `router_regression.py` G1–G41 ALL PASS twice. G41 pins the pilot geometry/connectivity and explicit opt-in framework contract; G40 retains routing-wall enforcement.
- `incremental_probe_006..027` and Phase-B probe ALL PASS; 30/164 rest nets routed, 134 unrouted.
- Independent full-board KiCad DRC unchanged: `lib_footprint_issues:199`, `hole_clearance:5`, `solder_mask_bridge:1`, `unconnected_items:499`, no copper-clearance class.
- Intrinsically flaky synthetic battery probes were not re-spent; their D-249/D-257/D-269 physical rules remain binding and are covered by deterministic board evidence.

## Next batch

Fast-screen `XGPIO4/5/6/7` against the accepted framework on the live D-331 board, allocate In2/In3 deterministically to avoid self-congestion, and promote a small coherent batch only if the same full-board gate passes. Full narrative audits are not required for ordinary clean reuse; record those routes in `routing_ledger.json` plus grouped governance.

Open owner decisions: NONE. DEVICE_SPEC unchanged. JLCPCB readiness remains 78.
