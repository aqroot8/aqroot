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
    decision='D-313',                 # FBV2-P2-015: XGPIO east-edge pilot XGPIO8+XGPIO9 (R59/R60 F -> U3.13/.14 B), D-269 0.300 mm clearance
    sha256='a0d6fead125295441dda0f0008c1261f5c1cec39edb2b8c7bd925b214e7207eb',
    tracks=631,                       # 608 (D-312) + 23 XGPIO8/XGPIO9 (F.Cu haul + B.Cu fan-out)
    vias=64,                          # 62 (D-312) + 2 XGPIO cross-layer through vias
    copper_layers=6,
    zones=41,
    ratsnest=679,                     # 681 (D-312) - 2 (XGPIO8 + XGPIO9 edges closed)
    journal=102,                      # 100 (D-312) + 2 XGPIO REST_INC
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
