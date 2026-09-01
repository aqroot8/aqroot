# FBV2-P2-042 — D-340 XGPIO boxed-endpoint anchor characterization

Starting authority: `f1fc61f`, board `d52daca8…` (867 tracks / 83 vias / ratsnest 650 / journal 131).

The generic owned-copper endpoint-anchor alternative was bounded first at the shared XGPIO6/XGPIO7 wall. Deterministic live geometry found legal 0.200 mm native-face escapes at both endpoints: U3.10 has two B.Cu launches and U3.11 has one; R57.1 and R58.1 each have multiple F.Cu launches. The failure is therefore not pad escape or the In2/In3 long haul. It is the layer transition: the reachable endpoint pocket contains no through-via site legal on every copper layer.

The screen tested the locked 0.60/0.30 mm ordinary via, the board-minimum 0.50/0.30 mm through-via, endpoint-first reservation order, and a 20 mm reachable-region span. Neither net obtained an all-layer-legal transition at U3.10/U3.11. Via-in-pad is unavailable because the U3 land is only 0.40 mm tall, smaller than the 0.50 mm board via-diameter floor. No blind/buried via was attempted because that changes the manufacturing process and requires an owner decision.

No authoritative PCB, placement, rule, topology, footprint, stackup, or accepted copper changed. Board SHA-256 remains `d52daca8df4351bb0052ba4e260e5c56d0cdcac4806d610c536bd78c599c05c8`.

Next fabrication blocker: screen other boxed endpoints for the ordinary-through-via anchor framework; defer XGPIO6/XGPIO7 until a bounded U3-cluster accepted-copper impact map shows a safe placement ECO, or the owner explicitly authorizes a blind-via manufacturing process.
