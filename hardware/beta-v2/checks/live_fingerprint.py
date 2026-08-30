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
    decision='D-314',                 # FBV2-P2-016: XGPIO west-edge SOUTH pilot XGPIO1+XGPIO0 (R52/R51 F -> U3.5/.4 B), XGPIO1-first, D-269 0.300 mm clearance
    sha256='95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605',
    tracks=669,                       # 631 (D-313) + 38 XGPIO1/XGPIO0 (F.Cu haul + B.Cu fan-out, 19 each)
    vias=66,                          # 64 (D-313) + 2 XGPIO cross-layer through vias
    copper_layers=6,
    zones=41,
    ratsnest=677,                     # 679 (D-313) - 2 (XGPIO1 + XGPIO0 edges closed)
    journal=104,                      # 102 (D-313) + 2 XGPIO REST_INC
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
