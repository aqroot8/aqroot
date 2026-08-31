# -*- coding: utf-8 -*-
"""FBV2-P2-006 -- REUSABLE INCREMENTAL REST-OF-BOARD ROUTER + PROMOTER.

The battery-block driver (route_battery_block.py) is power-tree scoped and the
in-repo "Phase B" replay machinery (replay_battery_block.py / SECTION-17) assumes
a copper-EMPTY authoritative base, so neither can add the 164 remaining
rest-of-board multi-pad nets onto the D-302 promoted board (see D-303 /
phaseB_bringup_probe_005.py).  This module is the missing piece: it routes a
bounded, named net-GROUP onto the promoted authoritative board **without ever
deleting, moving or re-routing a single strand of accepted Phase-A copper**, and
promotes the result only when a real full-board gate proves a genuine
no-casualty / no-new-DRC connectivity increment.

Design invariants (all enforced, not assumed):

  * PRESERVE PHASE-A EXACTLY.  QBoard loads the authoritative board and treats
    every existing track/via/pad/keep-out as an obstacle; new copper is ADDED
    (never Remove()d), so the accepted 432 tracks / 54 vias are carried through
    byte/geometry-equivalent.  The gate re-proves this as a copper-item multiset
    superset check -- if any Phase-A item is missing or altered, GATE FAIL.

  * ADD-ONLY, IN-SCOPE.  Every new copper item must belong to a net in the
    requested group.  New copper on any other net -> GATE FAIL.

  * REAL FULL-BOARD GATE (D-286).  Connectivity is judged by pcbnew connectivity
    on the whole board; legality by real kicad-cli DRC on the whole board.  No
    proxy / focused / post-hoc measurement promotes copper.

  * MONOTONIC.  Ratsnest and DRC unconnected_items must strictly DROP by exactly
    the requested connection count; no other DRC class may appear or increase;
    every prior Phase-A requested-connected pad pair must remain connected.

Commands (run one foreground experiment at a time):

    python3 incremental_router.py baseline
    python3 incremental_router.py route   FRONT_RGB
    python3 incremental_router.py gate     FRONT_RGB
    python3 incremental_router.py promote  FRONT_RGB     # only if gate PASS

`route` writes a scratch copy under checks/w/INC_<GROUP>/ and NEVER touches the
authoritative project.  `promote` copies that scratch board + a merged journal
back onto the authoritative project, but only after re-running the full gate.
"""
import os, sys, json, math, hashlib, shutil, collections
import numpy as np
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import qrouter as QR
import pcbnew

AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)
JOURNAL = os.path.join(SP, 'phaseA_journal.json')
WORK = os.path.join(SP, 'w')
BASELINE_JSON = os.path.join(SP, 'incremental_baseline_006.json')

# --------------------------------------------------------------------------- #
# GROUP REGISTRY.  A group is a bounded, isolated set of rest-of-board nets that
# is routed and gated as one increment.  Widths/clearances are the KiCad
# netclass floors the DRC enforces (FRONT_RGB nets are unmatched by any
# netclass pattern -> Default: 0.200 mm width, 0.200 mm clearance, no via).
GROUPS = {
    'FRONT_RGB': dict(
        sheet='08_BUTTONS_EXPANDERS',
        desc='front-panel RGB status-LED control lines (U23 expander -> R124/125/126); '
             'noncritical low-speed indicator nets, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['FRONT_RGB_R_N', 'FRONT_RGB_G_N', 'FRONT_RGB_B_N'],
    ),
    # FBV2-P2-007 / D-305 -- accelerometer 3V3 load-switch (U20) local control.
    # Two noncritical low-current control nets: the enable line ACC_3V3_EN
    # (driven from U3.15, pulled by R98, switched into U20.1, probed at TP26) and
    # the current-limit programming strap ACC_3V3_ILIM (set resistor R97 -> U20.4).
    # Both Default netclass (0.200 mm width/clearance, NO via), all B.Cu SMD; a
    # coherent standalone power-gating control subsystem in a low-congestion
    # region (only 4 Phase-A B.Cu strands within bbox+2 mm).  ACC_3V3_EN is a
    # 4-pad multi-terminal net (3-edge MST) -- the first promoted increment to
    # exercise multi-segment MST routing.
    'ACC_3V3_CTL': dict(
        sheet='01_POWER_TREE',
        desc='accelerometer 3V3 load-switch (U20) local control: enable '
             '(U3.15 -> R98/U20.1/TP26) + current-limit set (R97 -> U20.4); '
             'noncritical low-current control, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['ACC_3V3_EN', 'ACC_3V3_ILIM'],
    ),
    # FBV2-P2-008 / D-306 -- display reset control DISP_RST_N.  A single 3-pad
    # noncritical low-speed reset line whose pads DO NOT all share one layer:
    # R16.1 and J1.10 are F.Cu SMD, U2.8 is B.Cu SMD.  Its MST therefore has one
    # SAME-LAYER edge (R16.1<->J1.10, a pure F.Cu run -- the FIRST incremental
    # F.Cu route) and one CROSS-LAYER edge (J1.10<->U2.8, which must transition
    # F<->B through ONE board-legal through via -- the FIRST incremental via /
    # mixed-layer route).  The via is the Default netclass geometry the KiCad
    # DRC enforces here: 0.60 mm diameter / 0.30 mm drill (>= the 0.50 mm
    # min_via_diameter and 0.30 mm floor; NOT a microvia, not a POFV).  Widths
    # and clearances are the Default netclass floor (0.200 mm).  Low congestion:
    # only 2 accepted Phase-A copper items lie within the group bbox+2 mm.
    'DISP_RST': dict(
        sheet='03_SPI_A_DISPLAY_SD',
        desc='display reset DISP_RST_N (R16.1/J1.10 F.Cu, U2.8 B.Cu); '
             'noncritical low-speed reset line -- first incremental F.Cu run '
             '(R16.1<->J1.10) + first incremental cross-layer through via '
             '(J1.10<->U2.8, 0.60/0.30 Default netclass), no other via',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000,
        nets=['DISP_RST_N'],
    ),
    # FBV2-P2-009 / D-307 -- BQ25185 charger current-program strap PAIR.  Two
    # coherent same-chip (U11) low-current programming straps: ILIM_VSET (input
    # current-limit set resistor R36 -> U11.7) and ISET (charge-current set
    # resistor R37 -> U11.8).  Both Default netclass (0.200 mm width/clearance,
    # NO via), all B.Cu SMD, adjacent U11 east-edge pins -- a single coherent
    # charger-programming control cluster.  The region is congested (BQ25185 /
    # BPP trunk), so promotion is decided by the real full-board gate, not by
    # geometry alone.  Same-layer B.Cu mechanics (D-304/D-305) reused byte-for-
    # byte: no via, no plane re-pour.
    'U11_PROG': dict(
        sheet='01_POWER_TREE',
        desc='BQ25185 charger current-program straps: input-current-limit set '
             '(R36 -> U11.7 ILIM_VSET) + charge-current set (R37 -> U11.8 ISET); '
             'coherent same-chip low-current control, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['ILIM_VSET', 'ISET'],
    ),
    # FBV2-P2-009 fallback A -- west power-status sense pair: USB VBUS-present
    # divider (R104/R105/C68/TP31 VBUS_PRESENT) + MAX17048 fuel-gauge alert
    # (U14.5 -> TP11 MAX17048_ALRT_N).  Both Default netclass, all B.Cu SMD, no
    # via, tight far-west power-input corner.
    'PWR_SENSE': dict(
        sheet='01_POWER_TREE',
        desc='west power-status sense: USB VBUS-present divider (VBUS_PRESENT) + '
             'MAX17048 fuel-gauge alert (MAX17048_ALRT_N); low-current status '
             'sense, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['VBUS_PRESENT', 'MAX17048_ALRT_N'],
    ),
    # FBV2-P2-009 fallback B -- BMI270 IMU I2C address-select strap (U4/R118/
    # R119), a 3-pad B.Cu multi-terminal net, measured PRISTINE (0 accepted
    # copper within bbox+2mm).  Default netclass, no via.  The held clean
    # singleton fallback (favored IMU/I2C-local example).
    'IMU_ADDR': dict(
        sheet='05_I2C_DEVICES',
        desc='BMI270 IMU I2C address-select strap (R118/R119 -> U4.1 '
             'BMI270_SDO_ADDR); noncritical low-speed strap, all B.Cu SMD, no via',
        layer='B', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['BMI270_SDO_ADDR'],
    ),
    # FBV2-P2-010 / D-308 -- FRONT-PANEL RGB STATUS-INDICATOR COMPLETION.  D-304
    # (FRONT_RGB) routed the expander->resistor side of the front-panel RGB
    # status LED (U23 PCAL9535A GPIO -> R124/R125/R126 series limit resistors,
    # all B.Cu).  This group closes the SAME indicator on the LED-cathode side:
    # each series resistor's far pad (R124.2/R125.2/R126.2, B.Cu SMD) to the
    # matching cathode of D13 (MHPA3528RGBCT common-anode RGB LED, F.Cu SMD).
    # The three nets are Net-(D13-RK) (R124->D13.4 red), Net-(D13-GK)
    # (R125->D13.3 green), Net-(D13-BK) (R126->D13.2 blue).  Each is a 2-pad
    # CROSS-LAYER net (resistor B.Cu, LED F.Cu) so each closes with exactly ONE
    # board-legal Default through via (0.60/0.30) -- the SAME single-via-per-edge
    # mechanic proven at D-306, now applied THREE times in one increment (the
    # first MULTI-VIA increment; connect_cross is NOT changed, refill_planes
    # re-pours In1/In4 once for all three barrels).  Low current (R-limited
    # 2-6 mA status indicator, non-switching), low congestion (6-11 accepted
    # copper items per net bbox+2mm), a coherent local peripheral cluster that
    # directly extends an already-accepted increment.
    'FRONT_RGB_LED': dict(
        sheet='08_BUTTONS_EXPANDERS',
        desc='front-panel RGB status-LED cathode completion (R124/R125/R126 B.Cu '
             '-> D13 MHPA3528 cathodes F.Cu); closes the D-304 FRONT_RGB '
             'indicator on the LED side; low-current non-switching indicator, '
             'three cross-layer nets each one 0.60/0.30 Default through via',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000,
        nets=['Net-(D13-RK)', 'Net-(D13-GK)', 'Net-(D13-BK)'],
    ),
    # FBV2-P2-011 / D-309 candidate PRIMARY -- IR receiver local supply.
    # IR_RX_VS_LOCAL is the RC-filtered local supply node for the IR demodulator
    # U6 (07_IR): series filter R21.2 (F.Cu SMD) + decoupling C11.1 (F.Cu SMD) ->
    # U6.3 supply pin (THT, on BOTH faces).  All three pads share the F.Cu outer
    # layer (U6.3 is THT so F.Cu is available), so every MST edge is a SAME-LAYER
    # F.Cu run with NO via.  A tight NE-corner cluster (span ~10x4 mm), measured
    # PRISTINE (0 accepted copper within bbox+2 mm).  A coherent standalone
    # peripheral supply-filter group -- noncritical low-current, not a bulk rail.
    'IR_RX_VS': dict(
        sheet='07_IR',
        desc='IR receiver (U6) local filtered supply IR_RX_VS_LOCAL '
             '(R21.2 series + C11.1 decoupling -> U6.3 THT supply); '
             'pristine NE-corner cluster, all F.Cu, no via',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        nets=['IR_RX_VS_LOCAL'],
    ),
    # FBV2-P2-011 candidate -- coherent display/touch-panel control subset.
    # TOUCH_RST_N (J1.47 F, R12.1 F, U2.4 B) + TOUCH_INT_N (J1.46 F, U2.19 B):
    # the capacitive touch panel reset + interrupt lines from the display FPC
    # connector J1 to the touch-controller interface U2.  Both are long
    # cross-board hauls (33-38 mm) that transition F<->B (U2 is B.Cu) so each
    # closes with a Default through via.  MEASURED (screen_010): moderate mid-
    # board congestion (cu 21/24) -- promotion decided by the real full-board
    # gate, not geometry.
    # ==> D-309 MEASURED FAIL under the via-blind default: the router laid
    #     geometric paths (route ALL OK) but the real full-board gate reported +3
    #     new `clearance` violations -- the TOUCH_RST_N via/track collide with the
    #     ACCEPTED D-306 DISP_RST_N through-via in the congested U2 B.Cu escape
    #     region (U2.4/.7/.8/.11 stack on U2's west edge; the DISP_RST_N via sits
    #     1.19 mm west of that column so a westward escape via lands on it).
    # ==> FBV2-P2-012 / D-310 RESOLVED: `via_offset` walks the F<->B transition a
    #     bounded 2.5 mm off the nearest congesting barrel via the existing-via-
    #     aware `_offset_via_site` (screen_012: TOUCH_RST_N via 5.10 mm from DISP,
    #     TOUCH_INT_N is on U2's EAST edge already 5.9-8.4 mm clear).  Both nets
    #     pass the real full-board gate -> PROMOTED as the display/touch pair.
    'TOUCH_CTL': dict(
        sheet='03_SPI_A_DISPLAY_SD',
        desc='display/touch control: touch reset TOUCH_RST_N (J1.47/R12.1 F -> '
             'U2.4 B) + touch interrupt TOUCH_INT_N (J1.46 F -> U2.19 B); '
             'noncritical low-speed control, cross-layer through vias with a '
             'bounded 2.5 mm U2-escape via-site offset',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000, via_offset=2500000,
        nets=['TOUCH_RST_N', 'TOUCH_INT_N'],
    ),
    # FBV2-P2-011 candidate -- audio amplifier SD/mode strap.  AMP_SD_MODE
    # (R15.1 F, U5.4 F -> U2.7 B): the MAX98357 class-D amp SD/mode select strap
    # (a static logic-level strap, NOT the class-D output).  Cross-board haul to
    # U2 (~29 mm), one cross-layer edge -> one through via.  cu 57.
    # ==> D-309 MEASURED FAIL (NOT promoted): gate reported +7 `clearance` (via
    #     lands in the same congested U2 B.Cu escape beside DISP_RST_N; deferred
    #     to FBV2-P2-012 with the touch group).
    # ==> FBV2-P2-013 / D-311 RESOLVED: the U2 escape via-site offset proven at
    #     D-310 (TOUCH_CTL) applies unchanged.  Re-screened on the D-310 board
    #     (w/screen_013.py): the via-blind DEFAULT via is 0.100 mm from the
    #     DISP_RST_N barrel (CLASH, confirms D-309 +7); the bounded 2.5 mm offset
    #     walks the F<->B transition to (51.55,90.20) -> 1.760 mm to the nearest
    #     existing via (now the D-310 TOUCH_RST_N barrel) = CLEAR.  With
    #     via_offset the real full-board gate passes -> PROMOTED.
    'AMP_SD_MODE': dict(
        sheet='06_AUDIO',
        desc='audio amp SD/mode-select strap AMP_SD_MODE (R15.1/U5.4 F -> U2.7 B); '
             'static logic strap (not the class-D output), one cross-layer via '
             'with a bounded 2.5 mm U2-escape via-site offset',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000, via_offset=2500000,
        nets=['AMP_SD_MODE'],
    ),
    # FBV2-P2-011 candidate -- microSD card-detect.  SD_CARD_DETECT_N
    # (J2.10 F, R113.2 F -> U2.11 B): the microSD socket J2 card-detect switch
    # line (noncritical low-speed) to U2.  Cross-board haul (~59 mm), one
    # cross-layer edge -> one through via.  cu 57.
    # ==> D-309 MEASURED FAIL (NOT promoted): gate reported +2 `clearance` (via
    #     lands in the same congested U2 B.Cu escape; deferred to FBV2-P2-012).
    # ==> FBV2-P2-013 / D-311 RESOLVED: the D-309 +2 was TRACK-threading, not the
    #     via (re-screened on the D-310 board, w/screen_013.py: even the DEFAULT
    #     via is 1.301 mm clear of every barrel).  The always-on existing-via
    #     injection (D-310) fixes the track threading; the bounded 2.5 mm offset
    #     walks the transition SOUTH to (53.00,82.55) -> 3.850 mm clear (extra
    #     margin).  With via_offset the real full-board gate passes.
    'SD_DETECT': dict(
        sheet='03_SPI_A_DISPLAY_SD',
        desc='microSD card-detect SD_CARD_DETECT_N (J2.10/R113.2 F -> U2.11 B); '
             'noncritical low-speed detect, one cross-layer via with a bounded '
             '2.5 mm U2-escape via-site offset',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000, via_offset=2500000,
        nets=['SD_CARD_DETECT_N'],
    ),
    # ---------------------------------------------------------------------- #
    # FBV2-P2-015 -- XGPIO0..9 community-header GPIO long-haul bank.  Each
    # /XGPIOx is a 2-pad CROSS-LAYER net: the 100 R series resistor R5x.1 on
    # F.Cu (top resistor pack, y~17-36) -> the PCAL9535A U3 expander pin on
    # B.Cu (mid-board, y~74-80).  One MST edge, one F<->B through via each --
    # structurally identical to the U2 escape family, BUT the U3 escape goes
    # NORTH into open board (away from the U2 via cluster at y82-92), so the
    # READ-ONLY study (w/xgpio_study_015.py) measured every default via site
    # >=3.1 mm clear of every existing barrel and ZERO existing vias inside any
    # XGPIO routing bbox -- NO via_offset needed (unlike the U2 wall).  The one
    # real corridor risk the study found is INTER-XGPIO via crowding in the
    # shared north-of-U3 pocket (independent west-edge offset sites collide),
    # so the bank is routed as small adjacent pilots, member-by-member on
    # scratch + real full-board gate, never blindly as ten vias.  Netclass
    # Default (0.200/0.200, normal 0.60/0.30 via, In1.Cu forbidden -- the F/B
    # framework never touches In1).  These are the individually-screened
    # single-net entries; XGPIO_PILOT below is the combined transaction.
    'XGPIO8': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO8 series R59.1 F -> U3.13 B (east edge); '
             'noncritical 3V3 CMOS, one cross-layer through via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO8'],
    ),
    'XGPIO9': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO9 series R60.1 F -> U3.14 B (east edge); '
             'noncritical 3V3 CMOS, one cross-layer through via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO9'],
    ),
    'XGPIO7': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO7 series R58.1 F -> U3.11 B (west edge, northmost); '
             'noncritical 3V3 CMOS, one cross-layer through via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO7'],
    ),
    'XGPIO6': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO6 series R57.1 F -> U3.10 B (west edge); '
             'noncritical 3V3 CMOS, one cross-layer through via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO6'],
    ),
    'XGPIO5': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO5 series R56.1 F -> U3.9 B (west edge); '
             'noncritical 3V3 CMOS, one cross-layer through via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO5'],
    ),
    'XGPIO4': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO4 series R55.1 F -> U3.8 B (west edge); '
             'noncritical 3V3 CMOS, one cross-layer through via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO4'],
    ),
    # FBV2-P2-015 PILOT -- the credible coherent adjacent XGPIO subset chosen by
    # the corridor study (w/xgpio_study_015.py) and proven member-by-member on
    # the real full-board gate: XGPIO8 (R59.1 F -> U3.13 B) + XGPIO9 (R60.1 F ->
    # U3.14 B), the two EAST-edge community-GPIO nets on consecutive U3 pins.
    # Chosen over the west-edge members because the study measured the west nets'
    # cross-layer vias all crowding into one small pocket north of U3 (XGPIO6/7
    # picked the IDENTICAL site 55.55,76.15; 4/5 within 0.6 mm) -- an ordering-
    # sensitive shared-lane hazard -- whereas the east pair lands at (58.6,72.95)
    # and (58.45,75.65), 2.7 mm apart (2.1 mm copper gap), an independent legal
    # corridor.  All XGPIO nets need the D-269 0.300 mm clearance because the
    # 52.4 mm BAT_PROTECTED_P protected-battery F.Cu trunk sweeps diagonally
    # across the y~73-82 via-landing band (default 0.200 mm routing lands
    # 0.244-0.281 mm from it -> DRC clearance FAIL); routing the group at the
    # 0.300 mm D-269 floor is the correct clearance, NOT a new mechanism.  No
    # via_offset (every via site is >=3 mm clear of every existing barrel; the
    # U2-escape offset is not needed here).  Routed as ONE transaction: XGPIO8
    # first, then XGPIO9 sees XGPIO8's laid via and separates.
    'XGPIO_PILOT': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO east-edge pilot: XGPIO8 (R59.1 F -> U3.13 B) + '
             'XGPIO9 (R60.1 F -> U3.14 B); two adjacent 3V3 CMOS nets, each one '
             'cross-layer through via, routed at the D-269 0.300 mm clearance '
             'floor (BAT_PROTECTED_P trunk crosses the corridor), no via_offset',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO8', 'XGPIO9'],
    ),
    # FBV2-P2-016 -- the two SOUTHERNMOST west members (individually-screened
    # single-net entries, mirroring XGPIO4..9).  R52.1 F -> U3.5 B and
    # R51.1 F -> U3.4 B; U3's southmost GPIO pins, furthest from the crowded
    # north-of-U3 XGPIO6/7 via pocket.
    'XGPIO1': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO1 series R52.1 F -> U3.5 B (west edge, south); '
             'noncritical 3V3 CMOS, one cross-layer through via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO1'],
    ),
    'XGPIO0': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO0 series R51.1 F -> U3.4 B (west edge, southmost); '
             'noncritical 3V3 CMOS, one cross-layer through via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO0'],
    ),
    # FBV2-P2-016 WEST PILOT -- the credible coherent adjacent WEST subset chosen
    # by the recovery screen (w/screen_016.py + w/screen_016_one.py, live D-313
    # board, D-269 0.300 mm, no via_offset).  XGPIO0 + XGPIO1, the two SOUTHERNMOST
    # west community-GPIO nets on consecutive PCAL9535A U3 pins (U3.4, U3.5).
    # Unlike the northern west members (XGPIO6/7 collide in one via pocket), the
    # southern pair SELF-SEPARATES when routed XGPIO1-first: the screen measured
    # XGPIO1's via lands in the pocket at (55.40,79.00) and XGPIO0 (routed second,
    # seeing XGPIO1's laid via as a real obstacle) escapes WEST to (52.75,78.35) --
    # via-via copper 2.129 mm, both vias >=2.0 mm from the BAT_PROTECTED_P trunk
    # and >=3.6 mm from every existing barrel, all >> the 0.300 mm D-269 floor
    # (CLEAN).  ORDER MATTERS: the reverse order (XGPIO0-first) boxes XGPIO1 out
    # (no legal 0.200 mm corridor from R52.1) -> route XGPIO1 FIRST.  Same D-269
    # 0.300 mm clearance as the east pilot (BAT_PROTECTED_P crosses the y~73-82
    # via band), no via_offset (every site is >=2 mm clear of every barrel).
    'XGPIO_PILOT_W': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO west-edge south pilot: XGPIO1 (R52.1 F -> U3.5 B) + '
             'XGPIO0 (R51.1 F -> U3.4 B); two adjacent 3V3 CMOS nets, each one '
             'cross-layer through via, routed XGPIO1-FIRST at the D-269 0.300 mm '
             'clearance floor (BAT_PROTECTED_P trunk crosses the corridor), no '
             'via_offset; XGPIO0 self-separates west off XGPIO1 laid via',
        layer='F', width=200000, clr_pad=300000, clr_trk=300000,
        via_dia=600000, via_drill=300000, nets=['XGPIO1', 'XGPIO0'],
    ),
    # ---------------------------------------------------------------------- #
    # FBV2-P2-018 / D-316 -- a SINGLE west XGPIO net at the 0.200 mm Default
    # clearance (NOT the 0.300 mm blanket the pilot pairs used).  D-315
    # characterised the XGPIO2+XGPIO3 adjacent PAIR as a corridor-capacity WALL
    # (both orders NO_FAR_RUN -- the now D-313+D-314-congested F.Cu corridor
    # admits ONE 116 mm haul, not two parallel ones) and produced the decisive
    # positive lead: a SINGLE west member routes CLEAN at 0.200 mm and keeps the
    # D-269 0.300 mm floor to the BAT_PROTECTED_P trunk WITH MARGIN, because the
    # west haul's natural path clears BPP by >=0.47 mm (unlike the D-313 EAST
    # pilot whose 0.200 mm haul pinched BPP to 0.244-0.281 mm and therefore
    # needed the 0.300 mm floor).  The 0.300 mm blanket is over-conservative for a
    # single west haul AND is exactly what saturates the corridor, so the correct
    # clearance here is the 0.200 mm Default with the real full-board D-269-aware
    # KiCad DRC arbitrating the BPP clearance (D-286 gate) -- NOT a new mechanism,
    # NOT rule weakening (nothing below any floor is accepted; D-269 is satisfied
    # by measured geometry).  Target = XGPIO3 (R54.1 F.Cu -> U3.7 B.Cu): the
    # D-315 record + the FBV2-P2-018 live re-screen measured its cross-layer via
    # at (55.300,77.700) with the MOST-separated existing-via clearance (exv
    # copper 0.704 mm) and haul->BPP 0.474 mm >= 0.300.  One net, one MST edge,
    # one 0.60/0.30 Default through via; no via_offset (the via site is clear of
    # every barrel); In1/In4 re-poured once for the single anti-pad.  Do NOT
    # bundle XGPIO2 (D-315: the pair is a measured wall -- route one at a time).
    'XGPIO3': dict(
        sheet='09_COMMUNITY_HEADER',
        desc='community GPIO3 series R54.1 F -> U3.7 B (west edge); single-net '
             '3V3 CMOS increment at the 0.200 mm Default clearance (the west haul '
             'clears BPP by >=0.47 mm so the D-269 0.300 mm floor is kept by '
             'geometry, arbitrated by the real full-board D-269-aware gate), one '
             'cross-layer through via, no via_offset',
        layer='F', width=200000, clr_pad=200000, clr_trk=200000,
        via_dia=600000, via_drill=300000, nets=['XGPIO3'],
    ),
}


# --------------------------------------------------------------------------- #
# copper-item fingerprints (geometry-based Phase-A preservation proof)
def _track_sig(t):
    a = (t.GetStart().x, t.GetStart().y)
    z = (t.GetEnd().x, t.GetEnd().y)
    lo, hi = min(a, z), max(a, z)
    return ('T', t.GetNetname(), t.GetLayer(), lo, hi, t.GetWidth())


def _via_sig(t):
    p = t.GetPosition()
    return ('V', t.GetNetname(), (p.x, p.y), t.GetWidth(pcbnew.F_Cu), t.GetDrill())


def copper_sigs(board):
    c = collections.Counter()
    for t in board.GetTracks():
        cls = t.GetClass()
        if cls == 'PCB_TRACK':
            c[_track_sig(t)] += 1
        elif cls == 'PCB_VIA':
            c[_via_sig(t)] += 1
    return c


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


# --------------------------------------------------------------------------- #
def resolve_nets(qb, group):
    """Map each group base-net-name to its full net name on the board."""
    out = {}
    for base in group['nets']:
        hit = [nm for nm in qb.nets
               if nm == base or nm.endswith('/' + base)]
        if len(hit) != 1:
            raise SystemExit('net %r resolves to %r (expected exactly 1)' % (base, hit))
        out[base] = hit[0]
    return out


def net_pads(qb, netfull):
    return [d for (nm, tag), d in qb.pads.items() if nm == netfull]


def _pad_layers(p):
    """The set of outer copper layers a pad has copper on ('F' and/or 'B')."""
    return {L for L in ('F', 'B') if p.get(L)}


def edge_plan(pa, pb, group):
    """Decide how ONE MST edge is routed from its two pads' layers.

    * SAME-LAYER (the pads share a routable outer layer) -> a flat run on that
      layer with QR.connect_role.  The layer preferred is the group's declared
      `layer` when it is one of the shared layers (so THT pads, which are on
      BOTH faces, and all-B / all-F groups behave exactly as before), else the
      single shared layer.
    * CROSS-LAYER (the pads have NO shared outer layer, e.g. one F.Cu SMD and
      one B.Cu SMD) -> a single board-legal through via via connect_cross.
    Returns (layer_or_None, 'same'|'cross')."""
    common = _pad_layers(pa) & _pad_layers(pb)
    if common:
        L = group['layer'] if group['layer'] in common else sorted(common)[0]
        return L, 'same'
    return None, 'cross'


# --------------------------------------------------------------------------- #
# EXISTING-VIA AWARENESS + BOUNDED VIA-SITE OFFSET  (FBV2-P2-012 / D-310).
#
# qrouter.QBoard._scan registers footprint pads and PCB_TRACK segments as
# obstacles but NOT existing PCB_VIA barrels/holes (it scans GetTracks() and
# `continue`s on the via class).  For every increment through D-309 this was
# harmless -- no new via landed beside an existing one.  The U2 display/touch
# escape family breaks that: U2.4/.7/.8/.11 stack on U2's west edge and the
# accepted D-306 DISP_RST_N through-via sits 1.19 mm west of that column, so a
# westward cross-layer escape via lands right on the DISP_RST_N barrel.  The
# router's via-blind via_site() happily returns that site (measured: AMP_SD_MODE
# 0.100 mm via-to-via, TOUCH/SD tracks threading the same congested column) and
# only the real full-board DRC catches the `clearance` violation -- exactly the
# D-309 wall.
#
# The correct, bounded, GENERIC fix lives HERE (a new caller composing existing
# QBoard primitives -- qrouter.py is NOT touched, so every G-contract fixture
# that re-routes through QBoard is byte-unchanged): connect_cross gains existing-
# via awareness and, when a group opts in with `via_offset`, DELIBERATELY places
# the F<->B transition a bounded distance off the congesting barrel -- a short
# B.Cu fan-out on the host face to a planned clear via site, rather than
# accepting the router's first via-blind legal one.  Groups WITHOUT `via_offset`
# call qb.via_site exactly as before (byte-identical to D-306/D-308).
def _existing_vias(qb):
    """All existing PCB_VIA barrels on the board (net,x,y,dia,drill) -- the
    obstacles qrouter._scan omits.  Cached on the QBoard instance."""
    cache = getattr(qb, '_inc_existing_vias', None)
    if cache is not None:
        return cache
    out = []
    for t in qb.b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            out.append(dict(net=t.GetNetname(), x=p.x, y=p.y,
                            dia=t.GetWidth(pcbnew.F_Cu), drill=t.GetDrill()))
    qb._inc_existing_vias = out
    return out


def inject_existing_via_obstacles(qb):
    """Register every existing PCB_VIA as an obstacle ON THE QBoard INSTANCE so
    ALL qrouter primitives (escape / via_site / connect_role track search / grid)
    see the accepted barrels -- WITHOUT editing qrouter.py.

    qrouter._scan builds obstacles from footprint pads and PCB_TRACK segments but
    skips PCB_VIA (it iterates GetTracks() and `continue`s on the via class), so
    an incremental route is otherwise blind to accepted through-vias: it will lay
    a new via or thread a track straight past an existing barrel and only real
    DRC catches it (the D-309 U2 wall: the TOUCH_RST_N F.Cu run passed 0.05 mm
    from the DISP_RST_N via).  This mirrors, item-for-item, exactly what
    QBoard.via() already does for a via it lays itself (RR copper on every Cu
    layer + a hole), so it is faithful, generic, and add-only: it can only make a
    route MORE conservative, never delete/alter accepted copper, and it touches
    only this transient per-route QBoard instance -- the G-contract fixtures build
    their own QBoards and are unaffected.  Same-net vias are naturally not
    obstacles (QBoard.obstacles filters s.net != net)."""
    if getattr(qb, '_inc_vias_injected', False):
        return 0
    n = 0
    for v in _existing_vias(qb):
        x, y, dia, drill, net = v['x'], v['y'], v['dia'], v['drill'], v['net']
        for L in qb.cu:
            qb.shapes[L].append(QR.RR(x, y, dia / 2.0, dia / 2.0, dia / 2.0,
                                      0, net, 'via'))
        qb.holes.append(QR.RR(x, y, drill / 2.0, drill / 2.0, drill / 2.0,
                              0, net, 'via/hole'))
        n += 1
    qb._inc_vias_injected = True
    return n


def _clears_existing_vias(qb, vx, vy, net, vdia, vdrill, cp, hole_clr=250000):
    """True iff a via (vdia/vdrill) centred at (vx,vy) clears every existing via
    NOT on `net` by copper clearance `cp` AND hole-to-hole `hole_clr`."""
    for v in _existing_vias(qb):
        if v['net'] == net:
            continue
        d = math.hypot(v['x'] - vx, v['y'] - vy)
        if d < vdia / 2.0 + v['dia'] / 2.0 + cp:      # copper clearance
            return False
        if d < vdrill / 2.0 + v['drill'] / 2.0 + hole_clr:   # hole-to-hole
            return False
    return True


def _offset_via_site(qb, near, far, net, esc, width, vdia, cp, ct, G, vdrill,
                     off, span=8000000, hole_clr=250000):
    """A bounded, existing-via-aware analogue of qb.via_site.

    Same reachability/both-layer legality qb.via_site enforces (free_region on
    `near` from the escape, via_dia clearance grids on `near` and `far`, the
    net-agnostic hole-to-hole floor), with TWO additions the via-blind primitive
    cannot make:

      * existing PCB_VIA copper (every routed layer) and hole clearance are
        subtracted from the candidate mask, so a returned site is legal against
        the accepted D-306/D-308 barrels the router cannot otherwise see;
      * the site is chosen nearest to a BIAS point = escape + `off` mm along the
        unit vector pointing directly AWAY from the nearest existing via -- i.e.
        the transition is deliberately walked ~`off` mm off the congesting barrel
        (a short host-face fan-out), not left on the router's nearest cell.

    `off` bounds the plan: the picked site must lie within `off` + a one-cell
    guard of the escape's reachable region, so the fan-out can never wander far.
    Returns (x,y) or None (caller then tries the next escape / grid / fails)."""
    x0, y0 = esc['x'] - span, esc['y'] - span
    x1, y1 = esc['x'] + span, esc['y'] + span
    reach = qb.free_region(near, net, width, cp, ct, G, (esc['x'], esc['y']),
                           x0, y0, x1, y1)
    if reach is None:
        return None
    mask, ox, oy, g = reach
    bn = qb.grid(near, net, vdia, cp, ct, ox, oy, x1, y1, g)
    bf = qb.grid(far, net, vdia, cp, ct, ox, oy, x1, y1, g)
    ny = min(mask.shape[0], bn.shape[0], bf.shape[0])
    nx = min(mask.shape[1], bn.shape[1], bf.shape[1])
    good = mask[:ny, :nx] & ~bn[:ny, :nx] & ~bf[:ny, :nx]
    if not good.any():
        return None
    XX = (ox + np.arange(nx) * g).astype(float)
    YY = (oy + np.arange(ny) * g).astype(float)
    X, Y = np.meshgrid(XX, YY)
    # subtract existing-via copper + hole clearance (the qrouter-blind obstacles)
    nearest = None
    for v in _existing_vias(qb):
        if v['net'] == net:
            continue
        need = max(vdia / 2.0 + v['dia'] / 2.0 + cp,
                   vdrill / 2.0 + v['drill'] / 2.0 + hole_clr)
        good &= ~(np.hypot(X - v['x'], Y - v['y']) < need)
        d = math.hypot(v['x'] - esc['x'], v['y'] - esc['y'])
        if nearest is None or d < nearest[0]:
            nearest = (d, v)
    if not good.any():
        return None
    # bias point: `off` mm away from the nearest existing via (deliberate offset)
    if nearest is not None:
        ax, ay = esc['x'] - nearest[1]['x'], esc['y'] - nearest[1]['y']
        n = math.hypot(ax, ay) or 1.0
        bx, by = esc['x'] + ax / n * off, esc['y'] + ay / n * off
    else:
        bx, by = esc['x'], esc['y']
    jj, ii = np.nonzero(good)
    ci = (bx - ox) / float(g)
    cj = (by - oy) / float(g)
    d = (ii - ci) ** 2 + (jj - cj) ** 2
    k = int(np.argmin(d))
    return (int(ox + ii[k] * g), int(oy + jj[k] * g))


def connect_cross(qb, net, pa, pb, group, G=50000, fine=25000):
    """Route ONE cross-layer edge (pads on opposite outer faces) with exactly
    ONE board-legal through via, composing only proven qrouter primitives:

        escape(host, near) -> via_site(near, far) -> via(0.60/0.30) ->
        connect_role(host -> anchor@via, near) + connect_role(run -> anchor@via, far)

    The via geometry, the all-copper-layer clearance and the net-agnostic
    hole-to-hole floor are exactly what QBoard.via_site already enforces (the
    same legality connect_hop relies on); the two runs land on the via centre,
    which is same-net copper and therefore not an obstacle to either.  No
    qrouter.py behaviour is changed -- this is a new caller of existing methods.

    When the group declares `via_offset`, the via site is chosen by the bounded
    existing-via-aware `_offset_via_site` (FBV2-P2-012): the transition is walked
    ~via_offset mm off the nearest congesting barrel and proven clear of every
    existing via the router is blind to.  Without `via_offset` the site is
    qb.via_site's nearest legal cell, exactly as for D-306/D-308.
    """
    w, cp, ct = group['width'], group['clr_pad'], group['clr_trk']
    vd = group.get('via_dia', 600000)
    vk = group.get('via_drill', 300000)
    voff = group.get('via_offset')          # None -> router-blind via_site (D-306/D-308)

    def only(p):
        s = _pad_layers(p)
        return next(iter(s)) if len(s) == 1 else None
    near = only(pb)          # host the via beside pb (its single face)
    far = only(pa)           # run the far layer to pa
    if near is None or far is None or near == far:
        return dict(ok=False, reason='NOT_CROSS',
                    why='connect_cross needs two opposite single-layer pads '
                        '(%s on %s, %s on %s)'
                        % (pa['ref'], sorted(_pad_layers(pa)),
                           pb['ref'], sorted(_pad_layers(pb))))
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    fail = dict(ok=False, reason='NO_VIA_SITE',
                why='no reachable %s->%s via site for %s/%s'
                    % (near, far, pb['ref'], pa['ref']))
    for G_try in (G, fine):
        e = qb.escape(pb, near, w, w, cp, ct, G_try, ox, oy,
                      prefer=(pa['x'] - pb['x'], pa['y'] - pb['y']))
        if not e:
            return dict(ok=False, reason='NO_LEGAL_ESCAPE',
                        why=qb.escape_why[0], pad=pb['ref'])
        site = None
        for c in e[:6]:
            if voff:
                st = _offset_via_site(qb, near, far, net, c, w, vd, cp, ct,
                                      G_try, vk, off=voff)
            else:
                st = qb.via_site(near, far, net, c, w, vd, cp, ct, G_try,
                                 via_drill=vk)
            if st is not None:
                site = st
                break
        if site is None:
            continue
        vx, vy = site
        # Defensive: never lay a via that fails existing-via clearance (the
        # router's obstacle model is blind to existing barrels; the offset
        # picker enforces this, but re-prove it for every group unconditionally
        # so a via-blind site can never reach the gate).
        if not _clears_existing_vias(qb, vx, vy, net, vd, vk, cp):
            fail = dict(ok=False, reason='VIA_NEAR_EXISTING_VIA',
                        why='via site (%.3f,%.3f) within clearance of an '
                            'existing via barrel/hole' % (vx / 1e6, vy / 1e6),
                        pad=pb['ref'])
            continue
        m = qb.mark()
        qb.via(net, vx, vy, vd, vk)
        anchor = dict(ref='(via)', x=int(vx), y=int(vy), F=True, B=True,
                      anchor=True, net=net,
                      shape=QR.RR(int(vx), int(vy), 1, 1, 0, 0, net, 'via'),
                      hx=1, hy=1, r=0, ang=0, tht=False)
        rn = QR.connect_role(qb, net, pb, anchor, near, w, cp, ct, G=G_try)
        if not rn.get('ok'):
            qb.revert(m)
            fail = dict(ok=False, reason='NO_NEAR_RUN', why=rn.get('why'),
                        pad=pb['ref'])
            continue
        rf = QR.connect_role(qb, net, pa, anchor, far, w, cp, ct, G=G_try)
        if not rf.get('ok'):
            qb.revert(m)
            fail = dict(ok=False, reason='NO_FAR_RUN', why=rf.get('why'),
                        pad=pa['ref'])
            continue
        return dict(ok=True, mm=rn['mm'] + rf['mm'], vias=1,
                    layer='%s+%s via' % (far, near),
                    via_xy=[(round(vx / 1e6, 3), round(vy / 1e6, 3))],
                    why='cross-layer %s/%s through via 0.%03d/0.%03d mm at '
                        '(%.3f,%.3f)'
                        % (far, near, vd // 1000, vk // 1000,
                           vx / 1e6, vy / 1e6))
    return fail


def mst_edges(pads):
    """Prim MST over pad centres -> list of (i, j) index pairs."""
    n = len(pads)
    if n <= 1:
        return []
    INF = float('inf')
    intree = [False] * n
    best = [(INF, -1)] * n
    best[0] = (0.0, -1)
    edges = []
    for _ in range(n):
        u = min((i for i in range(n) if not intree[i]), key=lambda i: best[i][0])
        intree[u] = True
        if best[u][1] >= 0:
            edges.append((best[u][1], u))
        for v in range(n):
            if intree[v]:
                continue
            d = math.hypot(pads[u]['x'] - pads[v]['x'], pads[u]['y'] - pads[v]['y'])
            if d < best[v][0]:
                best[v] = (d, u)
    return edges


# --------------------------------------------------------------------------- #
def cmd_baseline():
    """Record the authoritative fingerprints, DRC, ratsnest and target open-set."""
    b = pcbnew.LoadBoard(AUTH)
    b.BuildConnectivity()
    trk = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    via = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    rats = b.GetConnectivity().GetUnconnectedCount(True)
    dc, _ = RU.drc(AUTH, 'Abase', WORK)
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    res = dict(
        sha256=sha256(AUTH),
        tracks=len(trk), vias=len(via),
        copper_layers=b.GetCopperLayerCount(),
        ratsnest=rats, journal=len(jr),
        drc=dict(dc),
        phaseA_requested_pairs=[(e['net'], e['a'], e['b'])
                                for e in jr if e.get('requested_connected')],
    )
    json.dump(res, open(BASELINE_JSON, 'w'), indent=1)
    print('BASELINE authoritative board:')
    print('  sha256    ', res['sha256'])
    print('  tracks/vias/layers %d / %d / %d' % (res['tracks'], res['vias'], res['copper_layers']))
    print('  ratsnest  ', res['ratsnest'])
    print('  journal   ', res['journal'], '(requested pairs %d)' % len(res['phaseA_requested_pairs']))
    print('  DRC       ', dict(dc))
    return 0


def scratch_pcb(name):
    return os.path.join(WORK, 'INC_' + name, RU.PCBNAME)


# --------------------------------------------------------------------------- #
# In1/In4 GND REFERENCE PLANES.  D-rules and [[fbv2-p2 In1/In4 GND roles]] pin
# In1.Cu and In4.Cu as the two solid GND reference planes.  A through via on a
# SIGNAL net crosses both, and the plane must open a clearance anti-pad around
# the barrel or DRC answers `clearance`/`hole_clearance` (measured: the first
# DISP_RST_N via, before any refill, showed 0.000 mm to both planes).  The B.Cu
# increments never laid a via so this never arose; the first via increment does.
# We therefore re-pour EXACTLY these two plane zones (and nothing else) when a
# via was laid -- every other zone, and every Phase-A track/via, is left byte-
# identical.  The plane fill is not byte-reproducible by the current KiCad
# ZONE_FILLER (a stored-vs-current drift of ~35 poly-points per plane exists
# independent of the via), so the re-pour is proven SAFE by the real full-board
# DRC being unchanged, not by byte-equality of the plane polygons.
def plane_zones(board):
    """The In1/In4 GND reference-plane zones (order-stable index + zone)."""
    out = []
    for i, z in enumerate(board.Zones()):
        lyrs = {pcbnew.BOARD.GetStandardLayerName(L)
                for L in z.GetLayerSet().CuStack()}
        if z.GetNetname() == 'GND' and lyrs and lyrs <= {'In1.Cu', 'In4.Cu'}:
            out.append((i, z))
    return out


def zone_fp(z):
    """Fingerprint a zone's identity + fill (net, layers, priority, points)."""
    lyrs = tuple(sorted(pcbnew.BOARD.GetStandardLayerName(L)
                        for L in z.GetLayerSet().CuStack()))
    pts = sum(z.GetFilledPolysList(L).FullPointCount()
              for L in z.GetLayerSet().CuStack())
    return (z.GetNetname(), lyrs, z.GetAssignedPriority(), pts)


def refill_planes(board):
    """Re-pour only the In1/In4 GND reference planes; return their indices."""
    planes = plane_zones(board)
    if planes:
        pcbnew.ZONE_FILLER(board).Fill([z for _, z in planes])
    return [i for i, _ in planes]


def cmd_route(name):
    group = GROUPS[name]
    pcb = RU.fresh(WORK, 'INC_' + name)          # copy of the authoritative project
    qb = QR.QBoard(pcb)
    # qrouter._scan omits existing vias; register them as obstacles on this
    # instance so escape/via_site/connect_role all respect accepted barrels
    # (FBV2-P2-012).  Add-only, per-route, generic; qrouter.py untouched.
    nvia_obs = inject_existing_via_obstacles(qb)
    nets = resolve_nets(qb, group)
    layer, w = group['layer'], group['width']
    cp, ct = group['clr_pad'], group['clr_trk']
    jrn = []
    print('ROUTE group %s on %s.Cu at %.3f mm (%s)' % (name, layer, w / 1e6, group['desc']))
    if nvia_obs:
        print('  injected %d existing-via obstacle(s) (qrouter._scan omits vias)' % nvia_obs)
    for base in group['nets']:
        nf = nets[base]
        pads = net_pads(qb, nf)
        pads_by_ref = {p['ref']: p for p in pads}
        order = sorted(pads_by_ref)                # deterministic
        pads = [pads_by_ref[r] for r in order]
        for (i, j) in mst_edges(pads):
            pa, pb = pads[i], pads[j]
            el, kind = edge_plan(pa, pb, group)
            if kind == 'same':
                r = QR.connect_role(qb, nf, pa, pb, el, w, cp, ct)
                elabel, vias = el + '.Cu', 0
            else:
                r = connect_cross(qb, nf, pa, pb, group)
                elabel, vias = r.get('layer', 'cross'), r.get('vias', 0)
            rec = dict(net=base, netfull=nf, a=pa['ref'], b=pb['ref'],
                       layer=elabel, w=w / 1e6, ok=bool(r.get('ok')),
                       mm=round(r.get('mm', 0), 3), vias=vias,
                       via_xy=r.get('via_xy'), kind=kind,
                       reason=r.get('reason'), why=r.get('why'))
            jrn.append(rec)
            print('  %-12s %-8s -> %-8s [%-4s %s] %s %s'
                  % (base, pa['ref'], pb['ref'], kind, elabel,
                     'ok %.3f mm' % r['mm'] if r.get('ok') else 'FAIL ' + str(r.get('reason')),
                     r.get('why', '') or ''))
    # A through via crosses the In1/In4 GND planes; re-pour ONLY those two so
    # the barrel gets its clearance anti-pad.  No via -> no refill -> the B.Cu
    # increments stay byte-identical exactly as before.
    nvia = sum(1 for v in qb.laid if v.GetClass() == 'PCB_VIA')
    if nvia:
        idx = refill_planes(qb.b)
        print('  REFILLED %d In1/In4 GND plane zone(s) %s for %d new via(s) '
              '(anti-pad); all other zones untouched' % (len(idx), idx, nvia))
    qb.save(pcb)
    json.dump(jrn, open(os.path.join(WORK, 'INC_' + name, 'route_journal.json'), 'w'), indent=1)
    allok = all(r['ok'] for r in jrn)
    print('ROUTE %s: %s (%d connections, %d ok)'
          % (name, 'ALL OK' if allok else 'INCOMPLETE',
             len(jrn), sum(r['ok'] for r in jrn)))
    print('  scratch board:', pcb, '(authoritative UNTOUCHED)')
    return 0 if allok else 1


def cmd_gate(name, promote=False):
    group = GROUPS[name]
    pcb = scratch_pcb(name)
    if not os.path.exists(pcb):
        raise SystemExit('no scratch board for %s -- run route first' % name)

    fails = []

    def chk(cond, label, detail=''):
        print('  %s %s %s' % ('PASS' if cond else '**FAIL**', label, detail))
        if not cond:
            fails.append(label)

    print('GATE group %s' % name)
    ab = pcbnew.LoadBoard(AUTH)
    rb = pcbnew.LoadBoard(pcb)
    ab.BuildConnectivity()
    rb.BuildConnectivity()

    # The baseline is computed LIVE from the CURRENT authoritative board (which,
    # during route->gate before promote, is exactly the pre-increment state) --
    # NOT from a persisted file, so each successive group self-corrects and no
    # stale snapshot can ever govern a later increment.
    jr0 = json.load(open(JOURNAL, encoding='utf-8'))
    base = dict(
        sha256=sha256(AUTH),
        ratsnest=ab.GetConnectivity().GetUnconnectedCount(True),
        drc=dict(RU.drc(AUTH, 'Abase', WORK)[0]),
        phaseA_requested_pairs=[(e['net'], e['a'], e['b'])
                                for e in jr0 if e.get('requested_connected')],
    )

    # -- 1. Phase-A copper preserved EXACTLY (superset, add-only, in-scope) ----
    base_sig = copper_sigs(ab)
    routed_sig = copper_sigs(rb)
    missing = base_sig - routed_sig       # any authoritative item lost/altered
    added = routed_sig - base_sig         # new copper items
    chk(not missing, 'no Phase-A copper deleted or altered',
        '(%d missing)' % sum(missing.values()))
    nf_set = set()
    qbnets = {n.GetNetname() for n in rb.GetNetsByName().values()}
    for b_ in group['nets']:
        hit = [nm for nm in qbnets if nm == b_ or nm.endswith('/' + b_)]
        nf_set.add(hit[0])
    oos = [sig for sig in added if sig[1] not in nf_set]
    chk(not oos, 'every new copper item is a target-group net',
        '(%d out-of-scope new items)' % len(oos))
    chk(len(added) > 0, 'copper was actually added', '(%d new items)' % sum(added.values()))

    # -- 1b. ZONES preserved: only the In1/In4 GND reference planes may re-pour -
    # (to carve a through-via anti-pad); every OTHER zone must be byte-identical
    # in net / layers / priority / filled-poly count, and even the planes may
    # only change their FILL, never their identity.  A B.Cu increment lays no
    # via, so no plane re-pours and this reduces to "all zones identical".
    a_zones, r_zones = list(ab.Zones()), list(rb.Zones())
    plane_idx = {i for i, _ in plane_zones(rb)}
    zchg, zbad = [], []
    if len(a_zones) != len(r_zones):
        zbad.append('zone COUNT %d->%d' % (len(a_zones), len(r_zones)))
    else:
        for i, (za, zr) in enumerate(zip(a_zones, r_zones)):
            fa, fr = zone_fp(za), zone_fp(zr)
            if fa == fr:
                continue
            zchg.append(i)
            if fa[:3] != fr[:3]:
                zbad.append('zone %d IDENTITY %s->%s' % (i, fa[:3], fr[:3]))
            elif i not in plane_idx:
                zbad.append('zone %d (non-plane) fill %d->%d' % (i, fa[3], fr[3]))
    chk(not zbad,
        'only In1/In4 GND planes re-poured; all other zones identical',
        '(fill-changed zones=%s plane-set=%s%s)'
        % (zchg, sorted(plane_idx), '' if not zbad else ' BAD=' + str(zbad)))

    # -- 2. requested connectivity GAIN: each target net fully connected -------
    # GetConnectedPads(pad) lists pads joined to `pad` by COPPER (ratsnest
    # excluded), so a net is fully connected iff, from any one of its pads, the
    # copper-connected set covers every other pad on the net.
    rats_after = rb.GetConnectivity().GetUnconnectedCount(True)
    cca, ccr = ab.GetConnectivity(), rb.GetConnectivity()

    def pads_of(board, netfull):
        out = []
        for f in board.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() == netfull:
                    out.append(p)
        return out

    def _ref(p):
        return p.GetParentFootprint().GetReference() + '.' + p.GetNumber()

    def copper_connected(cc, pad):
        """Refs of pads joined to `pad` by COPPER (ratsnest excluded).
        GetConnectedItems(pad) with a single arg is the KiCad-10 call that
        works here; GetConnectedPads() returns [] in this build."""
        out = set()
        for it in cc.GetConnectedItems(pad):
            if it.GetClass() == 'PAD':
                out.add(it.GetParentFootprint().GetReference() + '.' + it.GetNumber())
        return out

    def net_open_edges(board, cc, netfull):
        """Ratsnest edges owed by this net = (#copper clusters over its pads) - 1."""
        pads = pads_of(board, netfull)
        if not pads:
            return 0
        seen, clusters = set(), 0
        for p in pads:
            ref = _ref(p)
            if ref in seen:
                continue
            clusters += 1
            seen |= copper_connected(cc, p) | {ref}
        return clusters - 1

    exp_drop = 0
    for nf in sorted(nf_set):
        pads = pads_of(rb, nf)
        refs = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber() for p in pads}
        reach = set()
        for p in pads:
            reach |= copper_connected(ccr, p) | {
                p.GetParentFootprint().GetReference() + '.' + p.GetNumber()}
        full = refs.issubset(reach) and net_open_edges(rb, ccr, nf) == 0
        chk(full, 'target net fully connected by copper: ' + nf.split('/')[-1],
            'pads=%d open_edges %d->%d' % (len(pads),
                                           net_open_edges(ab, cca, nf),
                                           net_open_edges(rb, ccr, nf)))
        exp_drop += net_open_edges(ab, cca, nf)

    # -- 3. no Phase-A requested pair regressed --------------------------------
    # (The copper-superset check in step 1 already proves no Phase-A strand
    #  changed, so this is a redundant belt-and-braces electrical re-proof.)
    regressed = []
    for (nm, a, b_) in base['phaseA_requested_pairs']:
        pa = _pad(rb, a)
        pb = _pad(rb, b_)
        if pa is None or pb is None:
            continue
        conn = copper_connected(ccr, pa) | {
            pa.GetParentFootprint().GetReference() + '.' + pa.GetNumber()}
        if b_ not in conn:
            regressed.append((nm, a, b_))
    chk(not regressed, 'all Phase-A requested pairs still copper-connected',
        '(%d regressed)' % len(regressed))

    # -- 4. ratsnest strictly dropped by exactly the requested gain ------------
    chk(rats_after == base['ratsnest'] - exp_drop and exp_drop > 0,
        'ratsnest dropped by exactly the requested connections',
        '%d -> %d (expected -%d)' % (base['ratsnest'], rats_after, exp_drop))

    # -- 5. real full-board DRC delta: no new/worse class, unconnected drops ---
    dc, det = RU.drc(pcb, 'Ainc', WORK)
    b_drc = base['drc']
    newcls = [k for k in dc if k not in b_drc and k != 'unconnected_items']
    worse = [k for k in dc if k != 'unconnected_items' and dc[k] > b_drc.get(k, 0)]
    chk(not newcls, 'no new DRC violation class', str({k: dc[k] for k in newcls}))
    chk(not worse, 'no DRC class increased', str({k: (b_drc.get(k, 0), dc[k]) for k in worse}))
    # kicad-cli DRC's "unconnected_items" enumerates a different (smaller) set
    # than pcbnew's GetUnconnectedCount ratsnest -- the project's connectivity
    # authority, the "ratsnest 704" of D-302.  The connectivity GAIN is proven
    # above by the exact ratsnest drop (step 4) + per-net GetConnectedItems
    # (step 2); DRC's role here is LEGALITY: its unconnected_items must not
    # INCREASE (my copper must not sever anything DRC counts).
    un_b = b_drc.get('unconnected_items', 0)
    un_a = dc.get('unconnected_items', 0)
    chk(un_a <= un_b, 'DRC unconnected_items did not increase',
        '%d -> %d' % (un_b, un_a))
    print('  DRC after:', dict(dc))

    verdict = not fails
    new_vias = sum(1 for sig in added if sig[0] == 'V')
    art = dict(group=name, scratch=pcb, scratch_sha=sha256(pcb),
               auth_sha_pre=base['sha256'],
               new_copper_items=sum(added.values()),
               new_vias=new_vias,
               planes_repoured=sorted(plane_idx), zones_fill_changed=zchg,
               ratsnest_before=base['ratsnest'], ratsnest_after=rats_after,
               connections_gained=exp_drop,
               drc_before=b_drc, drc_after=dict(dc),
               target_nets=sorted(nf_set), fails=fails, verdict='PASS' if verdict else 'FAIL')
    json.dump(art, open(os.path.join(WORK, 'INC_' + name, 'gate_006.json'), 'w'), indent=1)
    print('GATE %s: %s (%d check%s failed)'
          % (name, 'PASS' if verdict else 'FAIL', len(fails), '' if len(fails) == 1 else 's'))

    if promote:
        if not verdict:
            raise SystemExit('REFUSING TO PROMOTE: gate FAILed (%s)' % fails)
        _promote(name, pcb, art)
    return 0 if verdict else 1


def _pad(board, ref):
    # Some Phase-A journal terminals are pseudo-pads / net nodes ("(tap)",
    # "(node)") with no "REF.PAD" form -- they have no single pad to test.
    if not ref or ref.count('.') != 1 or ref.startswith('('):
        return None
    r, num = ref.split('.')
    for f in board.GetFootprints():
        if f.GetReference() == r:
            for p in f.Pads():
                if p.GetNumber() == num:
                    return p
    return None


def _promote(name, pcb, art):
    """Copy the gated scratch board + merged journal onto the authoritative
    project.  Only the .kicad_pcb changes -- placement, DRU, netlist unchanged."""
    pre = sha256(AUTH)
    if pre != art['auth_sha_pre']:
        raise SystemExit('authoritative sha changed since gate (%s != %s)'
                         % (pre[:16], art['auth_sha_pre'][:16]))
    shutil.copyfile(pcb, AUTH)
    # merge the route journal into phaseA_journal.json as rest-of-board entries
    jr = json.load(open(JOURNAL, encoding='utf-8'))
    rj = json.load(open(os.path.join(WORK, 'INC_' + name, 'route_journal.json'), encoding='utf-8'))
    for r in rj:
        jr.append(dict(net=r['netfull'], a=r['a'], b=r['b'], role='REST_INC',
                       layer=r['layer'], w=r['w'], mm=r['mm'],
                       requested_connected=True, group=name))
    json.dump(jr, open(JOURNAL, 'w'), indent=1)
    print('PROMOTED %s: authoritative sha %s -> %s ; journal %d -> %d'
          % (name, pre[:16], sha256(AUTH)[:16], len(jr) - len(rj), len(jr)))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == 'baseline':
        return cmd_baseline()
    if cmd == 'route':
        return cmd_route(argv[2])
    if cmd == 'gate':
        return cmd_gate(argv[2])
    if cmd == 'promote':
        return cmd_gate(argv[2], promote=True)
    print('unknown command', cmd)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
