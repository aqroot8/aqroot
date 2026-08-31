# FBV2-P2-030 / D-328 — BTN_RIGHT_N hop-anchor route promoted

**Date:** 2026-08-31  
**Starting HEAD:** `7e6a397` (clean, pushed, D-327)  
**Starting board:** `adbea36b8bbcfa393f2810e989c93dbcfab4052b5538f9a7169bc71ff98b3e3f`, 821 tracks / 71 vias / ratsnest 659 / journal 122  
**Decision:** ACCEPT + PROMOTE; GPT primary-hardware-engineer transition acceptance PASS.

## Implementation

D-327 proved that the remaining west-button failures share a local pull-up/PCAL9535A endpoint wall. A focused scratch probe tested the already-qualified two-via `connect_hop` primitive on each endpoint pair. `BTN_RIGHT_N` alone admitted a legal F.Cu hop between its B.Cu `R7.2` and `U2.16` endpoints; the other measured candidates correctly rejected a via site.

The accepted implementation adds one opt-in `hop_anchor_plan` registry entry and a generic executor in `incremental_router.py`. It joins `R7.2↔U2.16` through two ordinary 0.60/0.30 vias at `(52.750,81.700)` and `(57.950,85.900)`, then connects both physical `SW5.1` F.Cu lands to the already-owned R7-side via anchor. This avoids requiring the boxed R7 pad to escape twice. Groups without `hop_anchor_plan` follow the pre-D-328 MST path unchanged; `qrouter.py` is untouched.

No schematic, footprint, placement, net, topology, netclass, clearance, DRU, stackup, outline, value, polarity, or layer-role change was made.

## Governed gate and promoted state

The D-286 full-board gate passed every check:

- zero accepted copper deleted or altered;
- all 18 new copper items belong to `BTN_RIGHT_N`;
- only In1/In4 GND plane fills changed for the two via anti-pads;
- all four physical pads form one copper cluster (`open_edges 3→0`);
- every prior requested pair remains connected;
- ratsnest 659→656, exactly the three owed edges;
- no new or increased DRC class; `unconnected_items` 499→499.

Promoted authoritative state: `sha256 27db293c8325832f585244b9d601103e8d72a6fcff13434a685f9472c21395c3`, 837 tracks / 73 vias / 6 layers / 41 zones / ratsnest 656 / journal 125. The increment is 16 tracks (12 F.Cu + 4 B.Cu) plus two through vias; the closest new-via to prior-barrel centre distance is 0.886 mm, above the 0.80 mm contract.

## Verification

- `router_regression.py`: G1–G39 ALL PASS, twice. G39 pins four-pad connectivity, 16-track/two-via geometry, barrel spacing, and that the lever is explicit and opt-in only.
- `incremental_probe_006.py` through `incremental_probe_026.py`: ALL PASS.
- `phaseB_bringup_probe_005.py`: PASS; 29 accepted routed rest nets, 135 unrouted.
- Independent `kicad-cli pcb drc`: unchanged histogram — `lib_footprint_issues:199`, `hole_clearance:5`, `solder_mask_bridge:1`, `unconnected_items:499`; no `clearance` class.

## Opportunity & simplification scan

The hop-anchor plan is the smallest reusable abstraction that closes the measured wall: registry-driven, absent by default, and composed from an existing qualified primitive. It does not generalize automatically to the other buttons because their via-site probes failed; each remaining candidate must be screened on live geometry. No BOM, mechanical, product-scope, firmware, sourcing, or manufacturing-process opportunity justifies a change at this milestone.

Open owner decisions: **NONE**. JLCPCB readiness remains **78** because one low-speed route increment improves completion but does not close a fabrication-level gate. Next: fresh screen of the remaining button candidates for legal hop-anchor reuse, otherwise select the next genuinely clean functional net and promote only on the full gate.
