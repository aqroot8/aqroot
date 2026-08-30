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
    decision='D-312',                 # FBV2-P2-014: microSD card-detect SD_CARD_DETECT_N, U2-escape via-site offset (2.5 mm)
    sha256='d6e0148a43a42895236b934cb6f7084036e50535a399f42fe09b300aabc5f1b8',
    tracks=608,                       # 580 (D-311) + 28 SD_CARD_DETECT_N (F.Cu + B.Cu fan-out)
    vias=62,                          # 61 (D-311) + 1 U2-escape offset through via
    copper_layers=6,
    zones=41,
    ratsnest=681,                     # 683 (D-311) - 2 (SD_CARD_DETECT_N 2 edges closed)
    journal=100,                      # 98 (D-311) + 2 SD_CARD_DETECT_N REST_INC
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
