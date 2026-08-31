# FBV2-P2-037 / D-335 — west-button owned-anchor screen

A bounded opt-in prototype tested the remaining west-button endpoint wall on representative `BTN_DOWN_N` and `BTN_A_N` geometries. Each boxed B.Cu pull-up was offered deterministic 1.5 mm and 2.5 mm staging offsets in eight directions, followed only by the locked 0.60/0.30 mm through-via transition to F.Cu and an owned-anchor switch attachment.

- Both nets stopped at the pull-up before a legal staging corridor existed (`R5.2` and `R8.2`: `NO_STAGING_PATH` at 0.200 mm).
- No scratch candidate reached a promotion gate; the prototype was removed rather than retained as dead routing logic.
- Authoritative D-332 copper remains byte-identical: `e5e6f4fc97c2677270f542f65d0037fb1329110a2ac844e84d2140f363d56e7d`, 856 tracks / 79 vias / ratsnest 653 / journal 128.
- G1–G42, focused probes 023–027, Phase-B (32/164 routed) and independent KiCad DRC all pass unchanged; DRC remains 205 violations / 499 unconnected with zero `clearance` class.

The framework-first search has now bounded ordinary, hop-anchor, split-inner, same-face staging and owned-copper layer-change mechanisms for this family. Next is a bounded pull-up placement ECO screen; placement is the remaining reversible lever that can create a legal escape without weakening any routing rule or changing topology.
