# FBV2-P2-031 / D-329 — routing-wall registry and framework-first transition

## Result

**PASS — process/framework milestone; no authoritative copper change.** The owner-approved
framework-first and coherent-batch routing strategy is active at live `HEAD 274a430` / D-328.
The full D-286 promotion gate is unchanged: accepted-copper preservation, full-board
connectivity, real KiCad DRC, routing invariants, regression preservation, and journal/rollback
integrity remain mandatory before any copper promotion.

## Implemented boundary

- Added machine-readable `hardware/beta-v2/checks/routing_walls.json`, populated from accepted
  D-316/D-318 and D-321..D-328 evidence. It records nine characterized walls, disproven
  mechanisms, permitted next frameworks, `do_not_retry`, and decision references.
- `incremental_router.py` consults the registry before scratch routing. A characterized blind
  retry is rejected unless the group explicitly declares a replacement framework such as a
  hop-anchor, inner long-haul, boxed-endpoint escape, or connector fanout plan.
- The registry is advisory. Accepted PCB copper, CTO decisions, and deterministic full-board
  evidence remain higher authority.
- Added regression G40: schema/ID integrity is deterministic; a blind `BTN_DOWN_N` replay is
  blocked while the accepted explicit `BTN_RIGHT_N` hop-anchor plan remains allowed.

## Validation

- JSON parse: PASS.
- `git diff --check`: PASS.
- `router_regression.py`: **G1–G40 ALL PASS**.
- Authoritative PCB remains byte-identical to D-328:
  `sha256 27db293c8325832f585244b9d601103e8d72a6fcff13434a685f9472c21395c3`,
  837 tracks / 73 vias / ratsnest 656 / journal 125.
- No DRU, clearance, netclass, stackup, topology, placement, footprint, schematic, BOM, or
  manufacturing rule changed.

## Next

Finish the remaining coherent `SWx` button batch by extending the accepted duplicate-pad and
endpoint-anchor mechanics only where live geometry supports them. Then build the bounded
In2/In3 long-haul framework for west XGPIO/appropriate low-speed signals. Synthetic probes
already shown non-deterministic on byte-identical boards are advisory; their electrical rules
remain enforced by deterministic full-board evidence.

