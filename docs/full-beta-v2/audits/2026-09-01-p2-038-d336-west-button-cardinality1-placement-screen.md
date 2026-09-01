# FBV2-P2-038 / D-336 — west-button cardinality-1 placement screen

Recovery preserved and completed the interrupted `west_button_eco_038.py` scratch harness. It moves exactly one pull-up (`R5`, `R8`, or `R6`) while U2, switches, accepted copper, rules, topology, values and every other footprint remain fixed. Each part received twelve ±0.5/1.0 mm compass/diagonal translations at its native and 180° orientations: 72 bounded candidates total.

- Same-face courtyard, board-edge and rule-area conflicts were rejected before routing.
- Every legal `BTN_DOWN_N`, `BTN_A_N`, and `BTN_LEFT_N` candidate still returned `NO_PATH` or `NO_LEGAL_ESCAPE`; none completed all four physical pads, so none reached a promotion gate.
- The screen is retained as reproducible characterization evidence; generated boards remain under ignored `checks/w/` scratch state.
- Authoritative D-332 copper remains byte-identical (`e5e6f4fc97c2677270f542f65d0037fb1329110a2ac844e84d2140f363d56e7d`, 856 tracks / 79 vias / ratsnest 653 / journal 128).
- G1–G42, probes 023–027, Phase-B (32/164 routed), and standalone KiCad DRC pass unchanged: 205 violations / 499 unconnected / zero `clearance` class.

Single-part micro-moves are therefore bounded. The collision pattern shows why: each pull-up is constrained by U2 and its adjacent pull-ups. The next reversible engineering lever is one bounded coordinated pull-up-column spread, screened on scratch before any authoritative placement or copper change.
