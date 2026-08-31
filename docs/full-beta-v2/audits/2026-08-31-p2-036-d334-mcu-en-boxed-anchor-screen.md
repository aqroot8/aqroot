# FBV2-P2-036 / D-334 — MCU EN boxed-anchor screen

The first generic boxed-endpoint pilot was run on the already-characterized `Net-(U1-EN)` wall. A bounded prototype used the qualified same-face `reserve_run` primitive to stage `U1.3` toward four explicit F.Cu anchors, then attempted ordinary 0.200 mm joins to `C1.2` and `R1.1`.

- Endpoint staging itself was possible, but every candidate still left `C1.2` unreachable (`NO_PATH` at both 0.050 and 0.025 mm grids).
- The prototype was rejected and removed; no dead router mechanism was retained.
- The authoritative PCB remained byte-identical to D-332 (`e5e6f4fc97c2677270f542f65d0037fb1329110a2ac844e84d2140f363d56e7d`, 856 tracks / 79 vias / ratsnest 653 / journal 128).
- Independent closeout re-ran G1–G42, probes 023–027, Phase-B (32/164 routed), and KiCad DRC; all passed with the unchanged histogram and zero `clearance` class.

This bounds same-face anchor staging for the MCU EN pocket without weakening rules or changing placement. Next: apply the boxed-endpoint framework only where a layer transition or owned-copper anchor can change reachability; prioritize the remaining west-button endpoint family as the coherent batch opportunity.
