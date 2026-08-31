# FBV2-P2-035 / D-333 — XGPIO6/XGPIO7 inner-haul endpoint wall

The final two members of the west-XGPIO family were screened on the clean pushed D-332 board. The accepted D-331 inner-layer long-haul framework was reused exactly; no routing rule, clearance, via geometry, layer role, placement, footprint, or topology changed.

- `XGPIO6` failed before copper promotion because `U3.10` had no legal reachable 0.60/0.30 mm via site from B.Cu on either allowed signal layer.
- `XGPIO7` failed before copper promotion because `R58.1` had no legal reachable 0.60/0.30 mm via site from F.Cu on either allowed signal layer.
- These are endpoint-reservation failures, not long-haul failures. The same framework remains accepted for XGPIO2/4/5; it is not generalized through geometry that does not support its locked via.
- Scratch routing only was performed. The authoritative board remained byte-identical to D-332 (`e5e6f4fc97c2677270f542f65d0037fb1329110a2ac844e84d2140f363d56e7d`, 856 tracks / 79 vias / ratsnest 653 / journal 128).
- `routing_walls.json` now prevents blind replay and directs both nets to the generic boxed-pad endpoint framework.

This is an ordinary engineering characterization, not an owner decision. Next: implement the bounded generic boxed-pad/endpoint-anchor framework and prove it first on an already-characterized functional wall under the unchanged full-board gate.
