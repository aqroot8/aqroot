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
    decision='D-318',                 # FBV2-P2-020: IMU/I2C-local interrupt strap BMI270_INT1_STRAP (R18.2/R110.1/TP3.1 -> U1.15 GPIO), 4-pad multi-terminal, ALL F.Cu SAME-LAYER MST, NO via -- the cleanest class (no plane re-pour), OUTSIDE the saturated west-XGPIO F.Cu corridor (D-317 mandate)
    sha256='78bf82da537a22697a860c23822599246e0534a8c4c311e12bc3d5b857a28816',
    tracks=709,                       # 691 (D-316) + 18 BMI270_INT1_STRAP (3 same-layer F.Cu MST runs)
    vias=67,                          # unchanged (no via -- all four pads on F.Cu)
    copper_layers=6,
    zones=41,                         # unchanged (no via -> no plane re-pour; zone COUNT + FILL constant)
    ratsnest=673,                     # 676 (D-316) - 3 (BMI270_INT1_STRAP 4-pad net fully connected)
    journal=108,                      # 105 (D-316) + 3 BMI270_INT1_STRAP REST_INC edges
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
