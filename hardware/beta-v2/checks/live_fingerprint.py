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
    decision='D-322',                 # FBV2-P2-024: reserved/spare community expander GPIO RESERVED_SPARE (R130.2 / TP41.1 test point / U23.7 PCAL expander), 3-pad all-B.Cu SAME-LAYER MST, NO via -- the cleanest class (no plane re-pour); the held clean alternate, PROMOTED after the display-FPC-connector candidates DISP_CS_N (J1.38 haul) and DISP_DC (J1.37 haul) hit a characterized J1-corridor wall (NO_PATH at 0.200 mm even on the fine grid) and after BOOT_N (the meaningful non-J1 alternative) routed only via poor 2.5x detours (110 mm of copper across the congested MCU interior for a boot-critical strap -- not equally clean, sensitivity treated carefully); in an OPEN region 15.5 mm clear of BAT_PROTECTED_P (zero D-269 involvement); away from the west-XGPIO corridor / U11 power-tree wall / RF-NFC-USB-crystal-switching-rail-community mass
    sha256='a861e30e5760515288ef9a3fc0c21ea6d3e9c31409f9181dd66d56ed0628efd1',
    tracks=759,                       # 749 (D-321) + 10 RESERVED_SPARE (two same-layer B.Cu MST runs R130.2<->U23.7 4.43 mm + U23.7<->TP41.1 10.94 mm)
    vias=67,                          # unchanged (no via -- all three pads on B.Cu)
    copper_layers=6,
    zones=41,                         # unchanged (no via -> no plane re-pour; zone COUNT + FILL constant)
    ratsnest=667,                     # 669 (D-321) - 2 (RESERVED_SPARE 3-pad net fully connected: 2 MST edges closed)
    journal=114,                      # 112 (D-321) + 2 RESERVED_SPARE REST_INC edges
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
