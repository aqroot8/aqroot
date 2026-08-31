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
    decision='D-316',                 # FBV2-P2-018: SINGLE west XGPIO net XGPIO3 (R54.1 F -> U3.7 B) at the 0.200 mm Default clearance (D-315 characterised the XGPIO2+XGPIO3 PAIR as a corridor-capacity wall; a SINGLE west haul clears BPP by >=0.47 mm so D-269 0.300 mm is kept by geometry)
    sha256='d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d',
    tracks=691,                       # 669 (D-314) + 22 XGPIO3 (F.Cu 118.261 mm haul + B.Cu fan-out)
    vias=67,                          # 66 (D-314) + 1 XGPIO3 cross-layer through via @(55.300,77.700)
    copper_layers=6,
    zones=41,                         # unchanged (In1/In4 re-poured for the 1 new anti-pad; zone COUNT constant)
    ratsnest=676,                     # 677 (D-314) - 1 (XGPIO3 R54.1<->U3.7 edge closed)
    journal=105,                      # 104 (D-314) + 1 XGPIO3 REST_INC
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
