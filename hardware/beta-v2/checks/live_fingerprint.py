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
    decision='D-319',                 # FBV2-P2-021: debug-console UART TX UART0_TXD_DBG (U1.37 MCU -> TP35.1 test point), dedicated 2-pad point-to-point net, SAME-LAYER F.Cu MST, NO via -- the cleanest class (no plane re-pour), in an OPEN region 31.3 mm clear of BAT_PROTECTED_P (zero D-269 involvement); away from the west-XGPIO corridor / U11 power-tree wall / RF-NFC-USB-crystal-switching-rail-community mass
    sha256='57dcc8affb6c0f85f747fba025463b9cf0897c6712709692151020f56fdb8adf',
    tracks=716,                       # 709 (D-318) + 7 UART0_TXD_DBG (single same-layer F.Cu MST run, 7 segments)
    vias=67,                          # unchanged (no via -- both pads on F.Cu)
    copper_layers=6,
    zones=41,                         # unchanged (no via -> no plane re-pour; zone COUNT + FILL constant)
    ratsnest=672,                     # 673 (D-318) - 1 (UART0_TXD_DBG 2-pad net fully connected)
    journal=109,                      # 108 (D-318) + 1 UART0_TXD_DBG REST_INC edge
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
