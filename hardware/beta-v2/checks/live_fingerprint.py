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
    decision='D-325',                 # FBV2-P2-027: the DUPLICATE-REF MST framework increment. BTN_B_N (navigation/boot button SW7.1 F.Cu / R9.2 pull-up B.Cu / U2.18 expander B.Cu) -- the FIRST net of the SWx user-button family -- routed + PROMOTED after a bounded, generic, deterministic framework fix let the MST + gate see a footprint's TWO physical "pad 1" lands as distinct nodes (SW7 is a 4-pin tact switch whose two mechanically-linked pad-"1" terminals sit 7.96 mm apart at (49.520,96.750) and (57.480,96.750); the old (net,'REF.NUM')-keyed collapse hid one land -> D-323 gate FAIL open_edges 2->1). physical_net_pads() now keys MST nodes by physical (ref,x,y) and net_open_edges() counts copper clusters over physical pads, matching KiCad's own ratsnest (4 lands -> 3 edges). BTN_B_N MST = R9.2 hub -> BOTH SW7.1 lands (two 0.60/0.30 through vias at (48.300,96.750) and (56.300,95.600), In1/In4 re-poured) + one same-layer B.Cu run R9.2->U2.18; 19 tracks (3 F.Cu + 16 B.Cu 0.200 mm), 2 vias, ALL FOUR physical pads in one copper cluster (open_edges 3->0), vias >= 2.915 mm from every barrel, OPEN south button field 11 mm clear of BAT_PROTECTED_P (zero D-269). Ordinary unique-pad nets byte-identical; router_regression G1-G35 unchanged
    sha256='35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220',
    tracks=800,                       # 781 (D-323) + 19 BTN_B_N (3 F.Cu short via legs + 16 B.Cu: R9.2 hub -> two SW7.1 lands via 2 through vias + R9.2->U2.18 run)
    vias=70,                          # 68 (D-323) + 2 BTN_B_N 0.60/0.30 through vias at (48.300,96.750) and (56.300,95.600)
    copper_layers=6,
    zones=41,                         # unchanged (2 vias -> only the In1/In4 GND reference planes re-poured for the anti-pads; zone COUNT constant)
    ratsnest=662,                     # 665 (D-323) - 3 (BTN_B_N 4-physical-pad net fully connected: 3 MST edges closed, both SW7.1 lands driven)
    journal=119,                      # 116 (D-323) + 3 BTN_B_N REST_INC edges (R9.2<->SW7.1 x2 + R9.2<->U2.18)
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
