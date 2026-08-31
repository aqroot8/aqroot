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
    decision='D-321',                 # FBV2-P2-023: microSD SPI chip-select SD_CS_N (J2.2 socket / R25.2 / U1.25 MCU), a genuine functional POINT-TO-POINT control (NOT a shared MOSI/MISO/CLK bus line), 3-pad all-F.Cu SAME-LAYER MST, NO via -- the cleanest class (no plane re-pour); chosen over the walled MCU_EN_RC (Net-(U1-EN), natural MST short edge C1.2<->U1.3 NO_PATH in the congested U1-EN/IR_TX pocket) and over the RESERVED_SPARE spare (held clean alternate); in an OPEN region 50.1 mm clear of BAT_PROTECTED_P (zero D-269 involvement); away from the west-XGPIO corridor / U11 power-tree wall / RF-NFC-USB-crystal-switching-rail-community mass
    sha256='68d44b54df91d607f689215c0da5db249b13fcd1ac189b9ab78ceb6366d25e46',
    tracks=749,                       # 729 (D-320) + 20 SD_CS_N (two same-layer F.Cu MST runs J2.2<->U1.25 + U1.25<->R25.2, 69.5 mm total)
    vias=67,                          # unchanged (no via -- all three pads on F.Cu)
    copper_layers=6,
    zones=41,                         # unchanged (no via -> no plane re-pour; zone COUNT + FILL constant)
    ratsnest=669,                     # 671 (D-320) - 2 (SD_CS_N 3-pad net fully connected: 2 MST edges closed)
    journal=112,                      # 110 (D-320) + 2 SD_CS_N REST_INC edges
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
