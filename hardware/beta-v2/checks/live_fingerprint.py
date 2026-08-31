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
    decision='D-328',                 # FBV2-P2-030: BTN_RIGHT_N promoted by the opt-in hop-anchor plan; 16 tracks (12 F.Cu + 4 B.Cu), two 0.60/0.30 through vias, all four physical pads connected, no rule/placement/topology change
    sha256='27db293c8325832f585244b9d601103e8d72a6fcff13434a685f9472c21395c3',
    tracks=837,                       # 821 (D-326) + 16 BTN_RIGHT_N
    vias=73,                          # 71 (D-326) + 2 BTN_RIGHT_N through vias
    copper_layers=6,
    zones=41,                         # unchanged (1 via -> only the In1/In4 GND reference planes re-poured for the anti-pad; zone COUNT constant)
    ratsnest=656,                     # 659 (D-326) - 3 (four physical pads -> one cluster)
    journal=125,                      # 122 (D-326) + 3 BTN_RIGHT_N REST_INC edges
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
