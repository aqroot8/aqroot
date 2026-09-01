# FBV2-P2-039 / D-337 — coordinated west-button pull-up-column spread bounded

GPT recovered and independently revalidated D-336, then executed its named next
task directly. `west_button_eco_039.py` moves all three still-unrouted pull-ups
(`R5`, `R8`, `R6`) together on scratch copies while keeping U2, accepted-button
pull-ups R4/R7/R9, switches, accepted copper, rules, topology and footprints fixed.

Eight legal cardinality-3 layouts were screened: four whole-column west
translations (0.5/1.0/1.5/2.0 mm), two centre-stagger layouts, and two small
west-plus-vertical spreads. Each layout was tested against all three complete
four-physical-pad nets: 24 route attempts total. `BTN_DOWN_N` and `BTN_A_N`
returned `NO_PATH` in every layout; `BTN_LEFT_N` returned `NO_LEGAL_ESCAPE` or
`NO_PATH`. No candidate reached a promotion gate.

Recovery also reran the committed D-336 harness with `AQROOT_ECO038_ONLY`
explicitly unset. It reproduced all 72 candidates and `NO SUCCESS`; the prior
24-entry ignored `results.json` was merely transient output from a focused rerun.
Router regression G1-G42, probes 023-027, Phase-B and independent DRC all pass.
The authoritative board remains byte-identical to D-332 (`e5e6f4fc...`, 856
tracks / 79 vias / ratsnest 653 / journal 128; zero clearance class).

The remaining wall is now the fixed U2/pull-up cluster itself, not independent
pull-up spacing. A future cluster ECO must include U2 and account for all already
routed U2 nets; otherwise the coherent next routing framework is J1 display
fanout. No owner decision is open and readiness remains 78%.
