# -*- coding: utf-8 -*-
"""FBV2-P2-011 / D-309 -- SINGLE SOURCE OF TRUTH for the CURRENT authoritative
board fingerprint.

Every incremental read-only probe (incremental_probe_006..NNN,
phaseB_bringup_probe_005) and the G-contract regression pin the SAME live
authoritative board: its sha256, track / via / copper-layer / zone counts, the
ratsnest and the journal length.  Before D-309 these five constants were
declared IDENTICALLY inside each probe and had to be hand-edited (~25 identical
edits) on every promoted increment -- pure repetitive maintenance that the
Opportunity & Simplification Scan flagged.

This module centralises that pin to ONE place, bumped ONCE per promotion.  It is
a pure DRY consolidation and weakens NO historical contract: every probe still
asserts "live board == EXPECTED", exactly as before -- only the literal now lives
here instead of being copied into each file.  Each probe keeps ALL of its own
increment-specific structural / connectivity / DRC checks inline.

Bump procedure on each promoted increment: update the EXPECTED dict below to the
new authoritative sha / counts (the values `incremental_router.py baseline`
prints, or the promote summary).  Nothing else changes.
"""

# The authoritative board fingerprint after the most recently promoted increment.
EXPECTED = dict(
    decision='D-326',                 # FBV2-P2-028: the TWENTIETH rest-of-board increment and the SECOND SWx user-button net -- the navigation D-pad UP button BTN_UP_N (SW2.1 button two F.Cu tact-switch lands / R4.2 pull-up B.Cu / U2.13 PCAL9535A expander GPIO B.Cu) -- routed + PROMOTED on the D-325 duplicate-ref MST framework (physical_net_pads keys MST nodes by physical (ref,x,y); net_open_edges counts copper clusters over physical lands). SW2 is the SAME 4-pin PTS645 tact switch as SW7: two mechanically-linked pad-"1" lands 7.96 mm apart at (60.220,96.750) and (68.180,96.750). BTN_UP_N is the CLEANEST remaining nav button (shortest ~12.3 mm cross-haul, lowest congestion 201, in the SAME open south button field where BTN_B_N passed). MST = SW2.1a<->SW2.1b (7.96 mm same-layer F.Cu land-run, NO via) + R4.2<->U2.13 (same-layer B.Cu run, NO via) + ONE cross-layer edge U2.13<->SW2.1 closed by ONE 0.60/0.30 through via at (61.100,95.400) (In1/In4 re-poured once) -- ONE via, CLEANER than BTN_B_N's two. 21 tracks (6 F.Cu + 15 B.Cu 0.200 mm), ALL FOUR physical pads in one copper cluster (open_edges 3->0, both SW2.1 lands driven), via 4.804 mm from the nearest barrel, 7.453 mm clear of BAT_PROTECTED_P (zero D-269). ZERO router-logic change (GROUPS entry + comment only); ordinary unique-pad nets byte-identical; router_regression G1-G37 unchanged
    sha256='adbea36b8bbcfa393f2810e989c93dbcfab4052b5538f9a7169bc71ff98b3e3f',
    tracks=821,                       # 800 (D-325) + 21 BTN_UP_N (6 F.Cu: SW2.1 land-run + F escape/via leg; 15 B.Cu: R4.2->U2.13 run + U2.13 escape + via fan)
    vias=71,                          # 70 (D-325) + 1 BTN_UP_N 0.60/0.30 through via at (61.100,95.400)
    copper_layers=6,
    zones=41,                         # unchanged (1 via -> only the In1/In4 GND reference planes re-poured for the anti-pad; zone COUNT constant)
    ratsnest=659,                     # 662 (D-325) - 3 (BTN_UP_N 4-physical-pad net fully connected: 3 MST edges closed, both SW2.1 lands driven)
    journal=122,                      # 119 (D-325) + 3 BTN_UP_N REST_INC edges (R4.2<->U2.13 + U2.13<->SW2.1 + SW2.1<->SW2.1)
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
