# -*- coding: utf-8 -*-
"""FBV2-P2-002D routing plan, written as PATH ROLES and ordered by scarcity.

Every entry says what the copper IS, not just which net it belongs to.

  TRUNK  carries pack current.  1.50 mm on BAT_PROTECTED_P (D-249), 1.00 mm on
         the BAT_MAIN nets, never narrowed below the class floor.
  TAP    a microamp branch off a power node: a divider top, a clamp, a
         decoupling capacitor.  0.60 mm - inside BAT_MAIN's own 1.00 / 0.60
         band, so no rule exception is involved.
  SENSE  a ruled sense branch at 0.20 mm (0.15 mm at U14) inside its own
         bounded corridor.
  SIG    an ordinary Default-class control net.
  TEST   a test-point stub.  Routed LAST, so a test point can never consume a
         corridor a functional route needs.

The LTC4368 divider resistors are megohm parts (R77 is 3.65 M), so R77/R79/R80,
R86/R89, D12, TP16 and U18.1 carry microamps and are taps by inspection of the
schematic rather than by assumption.

Section 12 order: scarce corridors first.  BAT_PROTECTED_P has a hard 1.20 mm
floor and no fallback ladder, so it goes first; test points go last.
"""
N = '/01_POWER_TREE/'

W_TRUNK_BAT = 1000000
W_TRUNK_BPP = 1500000
W_TAP = 600000
W_SENSE = 200000
W_U14 = 150000
W_SIG = 250000

LAD_BAT = [W_TRUNK_BAT, 800000, 600000]
LAD_TAP = [W_TAP, 500000, 400000, 300000, 250000, 200000]
LAD_SIG = [W_SIG, 200000, 150000]

# ---- 1. BAT_PROTECTED_P 1.50 mm trunk (the U11.2 flare is emitted with it,
#         because the trunk cannot exist without its own endpoint) ----------
PLAN_1_BPP_TRUNK = [
    (N + 'BAT_PROTECTED_P', 'R75.2', 'D9.1', 'TRUNK', [W_TRUNK_BPP, 1200000], None),
]

# ---- 2..5. the BAT_MAIN high-current chain -------------------------------
PLAN_2_CHAIN = [
    (N + 'BAT_SENSE', 'Q3.6', 'R75.1', 'TRUNK', LAD_BAT, None),
    (N + 'BAT_SENSE', 'Q3.5', 'Q3.6', 'TRUNK', LAD_BAT, None),
    (N + 'BAT_MID', 'Q2.6', 'Q3.8', 'TRUNK', LAD_BAT, None),
    (N + 'BAT_MID', 'Q2.5', 'Q2.6', 'TRUNK', LAD_BAT, None),
    (N + 'BAT_MID', 'Q3.8', 'Q3.7', 'TRUNK', LAD_BAT, None),
    (N + 'BAT_RAW', 'F1.2', 'Q2.8', 'TRUNK', LAD_BAT, None),
    (N + 'BAT_RAW', 'Q2.8', 'Q2.7', 'TRUNK', LAD_BAT, None),
    (N + 'BAT_CONNECTOR_P', 'J4.1', 'F1.1', 'TRUNK', LAD_BAT, None),
]

# ---- 6b. U18's own pin field, tightest escape first ----------------------
#
# U18.10 is the GATE output on the corner of an MSOP-10 whose 0.50 mm pitch
# admits at most 0.25 mm of copper.  Route the Kelvin branch off the adjacent
# U18.8 first and U18.10 has no escape left at any width - so the FUNCTIONAL
# gate connection goes first.  Same principle as section 12, one pin field down.
PLAN_6B_U18 = []

# ---- 7. the R75 Kelvin pair, straight off the correct sense-resistor pads --
# ---- 0. EVERYTHING THAT HAS TO LEAVE U18's PIN FIELD, BEFORE ANYTHING ELSE
#
# An MSOP-10 on 0.50 mm pitch gives each pin a 0.325 mm escape window and no
# second chance.  Route anything else first and whatever copper lands in the
# narrow band between the pad row and R75 closes the window for the pins that
# have not escaped yet - which is how FBV2-P2-002C lost U18.9, then U18.10,
# then U18.7, one per attempt.  The whole pin field goes first, inner pins
# before outer ones, and the trunk routes around the result.  The trunk has the
# whole board; these pins have 0.325 mm.
#
# PR-17, AND THE ORDER INSIDE THE PIN FIELD IS THE WHOLE POINT.
#
# U18 sits at x 1.23..4.83 with the divider wall R76/R77/R78/R79 at x 7.00..10.33.
# EVERY pin on the north row escapes through the same 2.2 mm corridor between
# them, and there is no second one.  Routing pins 6, 7, 8 and 9 first fills that
# corridor and pins 10 and 1 - the OUTERMOST pins, whose targets R76.1 and R77.1
# are the farthest east - are left with nothing: that is exactly what happened
# on the first FBV2-P2-002E run, where U18.10 failed NO_PATH to both R76.1 and
# Q3.4 and U18.1 failed its gate.
#
# The comment this list used to carry already said the FUNCTIONAL gate
# connection goes first.  The list did not do it.  It does now: U18.10 (the
# LTC4368 GATE output, section 9's functional net) claims the corridor first,
# U18.1 (the VIN tap, the other outer pin) second, and the inner pins - which
# have short northward escapes to R75 that do not use the corridor at all -
# take what is left.
PLAN_0_U18 = [
    (N + 'LTC_GATE', 'U18.10', 'R76.1', 'SIG', LAD_SIG, None),
    (N + 'BAT_RAW', 'U18.1', 'R77.1', 'SENSE', [W_SENSE], 'BAT_RAW_TAP_U18'),
    (N + 'BAT_SENSE', 'U18.9', 'R75.1', 'SENSE', [W_SENSE], 'BAT_SENSE_KELVIN'),
    (N + 'BAT_PROTECTED_P', 'U18.8', 'R75.2', 'SENSE', [W_SENSE], 'BAT_PROT_TAP_U18'),
    (N + 'LTC4368_FAULT_N', 'U18.7', 'R81.2', 'SIG', LAD_SIG, None),
    (N + 'LTC_SHDN', 'U18.6', 'R80.2', 'SIG', LAD_SIG, None),
    (N + 'LTC_OV', 'U18.3', 'R77.2', 'SIG', LAD_SIG, None),
    (N + 'LTC_UV', 'U18.2', 'R79.2', 'SIG', LAD_SIG, None),
]

PLAN_7_KELVIN = []

# The FET sense pairs come BEFORE the gate net, and that is a scarcity call
# rather than a priority one.  On each SOIC-8 south row Q*_CS owns pins 1 and 3
# while LTC_GATE owns 2 and 4, so the two nets INTERLEAVE and their spans
# overlap - on one layer they must cross.  LTC_GATE has an F.Cu hop available
# and takes it cleanly; Q*_CS, boxed between two gate pads, does not.
PLAN_8_CS = [
    (N + 'Q2_CS', 'Q2.1', 'Q2.3', 'SIG', LAD_SIG, None),
    (N + 'Q3_CS', 'Q3.1', 'Q3.3', 'SIG', LAD_SIG, None),
]

# ---- 8. LTC_GATE functional connections, TP17 deliberately excluded -------
PLAN_8_GATE = [
    (N + 'LTC_GATE', 'Q3.2', 'Q3.4', 'SIG', LAD_SIG, None),
    (N + 'LTC_GATE', 'Q2.2', 'Q2.4', 'SIG', LAD_SIG, None),
    (N + 'LTC_GATE', 'Q3.2', 'Q2.2', 'SIG', LAD_SIG, None),
    (N + 'LTC_GATE', 'U18.10', 'Q3.4', 'SIG', LAD_SIG, None),
    (N + 'LTC_GATE_RC', 'C57.1', 'R76.2', 'SIG', LAD_SIG, None),
]

# ---- 9. the LTC4368 trip network -----------------------------------------
PLAN_9_TRIP = [
    (N + 'LTC_OV', 'R77.2', 'R78.1', 'SIG', LAD_SIG, None),
    (N + 'LTC_SHDN', 'U18.6', 'Q4.3', 'SIG', LAD_SIG, None),
    (N + 'LTC4368_FAULT_N', 'R81.2', 'R82.1', 'SIG', LAD_SIG, None),
    (N + 'LTC4368_FAULT_N', 'R82.1', 'Q9.1', 'SIG', LAD_SIG, None),
    (N + 'BAT_PROT_SHDN_CTL', 'Q4.1', 'R83.1', 'SIG', LAD_SIG, None),
]

# ---- the microamp taps off the raw battery node --------------------------
#
# PR-43: SCHEDULE BY CORRIDOR SCARCITY, NOT BY NET ROLE.
#
# These four are all 'TAP' by role, so PR-36 put the whole group after the
# trunk, the BAT_MAIN chain and U18's eight-pin field.  That is right for a
# tap in the usual sense - short, local, several ways out.  Two of them are
# not that:
#
#     R80.1 -> Q2.7    21.5 mm      D12.1 -> R77.1    45.5 mm
#
# They are the LTC4368 divider chain's only link to the battery node, and the
# only corridor they have is the west margin at x 4..10 - the same margin the
# 1.50 mm BAT_PROTECTED_P trunk, BAT_SENSE and BAT_MID have already taken by
# then.  Measured on a bare board, both reach Q2.7/Q2.8/F1.2/C59.1 at 0.20 mm,
# so the corridor EXISTS and the failure is contention, not geometry.
#
# So the two long bridges are scheduled with the chain, by the same scarcity
# argument PR-18 used for the trunk, and the genuinely local taps stay put.
# U18's pins are short and have alternatives; these have one corridor each.
PLAN_TAPS_BRIDGE = [
    (N + 'BAT_RAW', 'R80.1', 'Q2.7', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'D12.1', 'R77.1', 'TAP', LAD_TAP, None),
]

# With PR-43 off, the two bridges stay in the tap group where PR-36 put them,
# so the default ordering is unchanged from the measured 8-of-8 U18 baseline.
PLAN_TAPS = [
    (N + 'BAT_RAW', 'R80.1', 'Q2.7', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'R79.1', 'R80.1', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'R77.1', 'R79.1', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'D12.1', 'R77.1', 'TAP', LAD_TAP, None),
]

# PR-43 ON removes the two bridges from the tap group; the driver adds them
# right after the BAT_MAIN chain instead.
PLAN_TAPS_PR43 = [
    (N + 'BAT_RAW', 'R79.1', 'R80.1', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'R77.1', 'R79.1', 'TAP', LAD_TAP, None),
]

# ---- 10. the dead-cell / recovery network --------------------------------
DEADCELL = ['VBRIDGE_TOP', 'VREF_TOP', 'REF_HO', 'REF_POL', 'N_POL', 'N_BATDIV',
            'VREC_VCC', 'REC_GATE_N', 'REC_POL_OK', 'REC_AND1', 'REC_AND2',
            'REC_BAT_LOW', 'REC_FAULT_B', 'REC_LIM_IN', 'REC_DIODE_IN']
PLAN_10_DEADCELL_TAPS = [
    (N + 'BAT_RAW', 'R86.2', '(node)', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'R89.1', '(node)', 'TAP', LAD_TAP, None),
]

# ---- 11. fuel-gauge branches, PR-13: 0.15 mm, max 15 mm ------------------
PLAN_11_GAUGE = [
    (N + 'BAT_PROTECTED_P', 'U14.2', 'TP15.1', 'SENSE', [W_SENSE, W_U14], 'BAT_PROT_TAP_U14'),
    (N + 'BAT_PROTECTED_P', 'U14.3', 'U14.2', 'SENSE', [W_SENSE, W_U14], 'BAT_PROT_TAP_U14'),
]

# ---- 12. capacitor taps, now local to the nodes they support -------------
PLAN_12_CAPS = [
    (N + 'BAT_RAW', 'C59.1', 'F1.2', 'TAP', LAD_TAP, None),
    (N + 'BAT_PROTECTED_P', 'C58.1', 'D9.1', 'TAP',
     [W_TRUNK_BPP, 1200000, 1000000, 800000, 600000], None),
    (N + 'BAT_PROTECTED_P', 'C36.1', '(node)', 'TAP',
     [W_TRUNK_BPP, 1200000, 1000000, 800000, 600000], None),
    (N + 'BAT_PROTECTED_P', 'C25.1', '(node)', 'TAP',
     [W_TRUNK_BPP, 1200000, 1000000, 800000, 600000], None),
]

# ---- 13. test-point stubs, LAST so they never take a functional corridor --
PLAN_13_TEST = [
    (N + 'BAT_PROTECTED_P', 'TP15.1', '(node)', 'SENSE', [W_SENSE], 'BAT_PROT_TAP_U14'),
    # Section 9: TP17 hangs OFF the closed gate network at its nearest legal
    # point, never through a named pad at the far end of it.  Aimed at R76.1
    # this stub routed 24.1 mm with two vias - a second route on the net.
    (N + 'LTC_GATE', 'TP17.1', '(node)', 'TEST', LAD_SIG, None),
    (N + 'BAT_RAW', 'TP16.1', '(node)', 'TEST', LAD_TAP, None),
    (N + 'BAT_SENSE', 'TP20.1', '(node)', 'TEST', LAD_TAP, None),
    (N + 'BAT_CONNECTOR_P', 'TP34.1', '(node)', 'TEST', LAD_TAP, None),
]


# ---- D-256: PLANNED F.Cu ESCAPE CAPACITY FOR THE LTC4368 CONTROL PATHS ----
#
# FBV2-P2-002J exhausted the R80/R81 placement lever: six poses plus the
# control, none reaching U18 8/8, and two full Phase A runs BELOW the 24-of-29
# baseline.  The measured conclusion was that the west margin at x 4..10 is
# short of LAYER CAPACITY, not of another B.Cu lane -- every route that wins a
# lane there takes it from a neighbour, so the casualty moves and the total
# does not improve.
#
# D-256 rules that conclusion accepted and authorises deliberate F.Cu capacity
# for selected LOW-CURRENT LTC4368 status and control paths, in priority order
# LTC_GATE, LTC4368_FAULT_N, then LTC_SHDN if required.
#
# The mechanism already exists: connect_hop() lays a short B.Cu escape at each
# pad, one through via, the run itself on F.Cu, and one through via down --
# exactly the "one via up, one via down" section 3 prefers.  What changes here
# is only WHEN it is used.  Until now it was a LAST-RESORT FALLBACK, reached
# after every B.Cu rung had failed, which meant a control net only left B.Cu
# after it had already spent the margin's copper trying not to.  For the nets
# named below the hop is now the FIRST choice, so the B.Cu lane is never taken
# in the first place.
#
# Nothing here is symmetric-for-symmetry's sake (section 3 forbids that): each
# entry is a run that was MEASURED crossing or boxing the contested margin.
#
#   * The two FAULT_N cross-board runs are 64 mm and they traverse the whole
#     west margin to reach Q9.  Section 4 is explicit that U18's scarce B.Cu
#     escape lane must not be spent to keep this net at zero vias.
#   * LTC_GATE's two runs OUT of U18's pin field (to R76.1 and to Q3.4) are the
#     ones that fragment; the three FET-local gate links (Q3.2<->Q3.4,
#     Q2.2<->Q2.4, Q3.2<->Q2.2) are NOT listed, because FBV2-P2-002F measured
#     them closing on B.Cu with zero vias and section 3 says use only the
#     length necessary to escape congestion.
#   * LTC_SHDN is the section 5 case: `U18.6 -> R80.2` is the run D-255 proved
#     was boxing U18.7, laid between two adjacent pins of the same MSOP-10, and
#     `U18.6 -> Q4.3` is 28 mm across the same margin.
#
# LTC_OV is DELIBERATELY ABSENT.  It is the high-impedance comparator input and
# section 6 keeps it local on B.Cu; if it ever becomes the final blocker that
# is a CTO stop, not a silent layer change.
#
# The sets are cumulative and are screened in increasing order of F.Cu use, so
# the answer records the MINIMUM intervention that works rather than the
# largest one that happens to pass.
_G = [
    (N + 'LTC_GATE', 'U18.10', 'R76.1'),
    (N + 'LTC_GATE', 'U18.10', 'Q3.4'),
]
_F = [
    (N + 'LTC4368_FAULT_N', 'R81.2', 'R82.1'),
    (N + 'LTC4368_FAULT_N', 'R82.1', 'Q9.1'),
]
_S_LONG = [
    (N + 'LTC_SHDN', 'U18.6', 'Q4.3'),
]
_S_FIELD = [
    (N + 'LTC_SHDN', 'U18.6', 'R80.2'),
    (N + 'LTC4368_FAULT_N', 'U18.7', 'R81.2'),
]

# Screened in increasing order of F.Cu use so the answer records the MINIMUM
# intervention that works.  The order follows the MEASURED failures rather than
# D-256's priority list alone: the FBV2-P2-002K control screen (PR-43 on, no
# F.Cu) leaves U18 at 6 of 8 with LTC_GATE fragmented (`Q3.2` NO_LEGAL_ESCAPE,
# `U18.10` NO_PATH to both R76.1 and Q2.2) and LTC_SHDN `U18.6 -> Q4.3` NO_PATH,
# while LTC4368_FAULT_N `U18.7 -> R81.2` CLOSES on B.Cu unaided.  So LTC_SHDN's
# long run is screened before FAULT_N's, because it is the one that is failing;
# adding vias to a net that already works would be exactly the unnecessary-via
# defect section 22 asks us to look for.
# Section 10's RESERVE, and it is not taken pre-emptively.
#
# MEASURED on the D-256 screen board, with Q3_CS's B.Cu route deleted and
# nothing else changed:
#
#     Q3.2 escape with Q3_CS present   0 directions at 0.15 mm  (NO_LEGAL_ESCAPE)
#     Q3.2 escape with Q3_CS removed   1 direction  at 0.25 mm
#     LTC_GATE  Q3.2 -> Q3.4  B.Cu     ROUTES, 5.500 mm at 0.25 mm, zero vias
#     Q3_CS     Q3.1 -> Q3.3  F.Cu     ROUTES, 5.583 mm at 0.25 mm, 2 vias
#
# This is PR-23's own prediction: on each SOIC-8 south row Q*_CS owns pins 1
# and 3 while LTC_GATE owns 2 and 4, the two nets INTERLEAVE, and a CS route
# threading both 0.67 mm inter-pad gaps SEALS the gate pad between them.  At
# the 002F prefix the CS-first order was measured better; with PR-43 in force
# it costs LTC_GATE the Q3.2 pad outright.
#
# So Q3_CS takes the layer excursion instead - one via up, one via down, the
# ORDINARY 0.60/0.30 Default-class geometry, no fine via needed - and LTC_GATE
# closes on B.Cu with no vias of its own.  Section 10 authorises exactly this
# and only once it is the measured local blocker, which it now is.
_Q3CS = [
    (N + 'Q3_CS', 'Q3.1', 'Q3.3'),
]

# Per-connection via geometry for a planned escape.  Anything not named here
# uses D256_VIA.  Q3_CS does not need the fine via and therefore does not get
# it: the reserve is a LAYER excursion, not a via-geometry exception.
D256_VIA_FOR = {
    (N + 'Q3_CS', 'Q3.1', 'Q3.3'): (600000, 300000),
    # D-266 section 9, option B.  `LTC_UV U18.2 -> R79.2` is authorised to take
    # an ORDINARY through via onto In2/In3 and return locally when B.Cu cannot
    # carry it - measured on the first D-266 screen, it is NO_PATH at 0.20 mm
    # and again at 0.15 mm, so option A is exhausted before option B is used.
    # The via is the D-257 PREFERRED 0.35/0.20, not the reserve, and no
    # clearance or width rule is relaxed to place it.
    (N + 'LTC_UV', 'U18.2', 'R79.2'): (350000, 200000),
}

# The other side of the Q3 south-row trade.  Instead of giving Q3_CS the layer
# excursion and the GATE the B.Cu slot, give Q3_CS the slot it already wins on
# PR-26's order and put the GATE's Q3 link on the planned F.Cu escape.  Both
# halves are measured; which one the board prefers is the question this set
# exists to answer, and it is answered by running it rather than by argument.
_GQ3 = [
    (N + 'LTC_GATE', 'Q3.2', 'Q3.4'),
]

_UV = [
    (N + 'LTC_UV', 'U18.2', 'R79.2'),
]

D256_SETS = {
    'G':     _G,
    # D-266 section 9: the GS board plus LTC_UV's authorised inner excursion.
    'GSU':   _G + _S_LONG + _UV,
    'GS':    _G + _S_LONG,
    'GSQ':   _G + _S_LONG + _Q3CS,
    'GSX':   _G + _S_LONG + _GQ3,
    # Both halves of the Q3 south row on their own planned escape: Q3_CS takes
    # section 10's excursion FIRST, so it leaves two stubs and two vias in the
    # inter-pad gaps instead of a full B.Cu run through them, and LTC_GATE's Q3
    # link then takes its own fine-via hop over the top.  Measured on the GSQ
    # board, that hop routes: 15.991 mm at 0.25 mm with the 0.50/0.25 via.
    'GSQX':  _G + _S_LONG + _Q3CS + _GQ3,
    'GSXF':  _G + _S_LONG + _GQ3 + _F,
    'GSQF':  _G + _S_LONG + _Q3CS + _F,
    'GSQFX': _G + _S_LONG + _Q3CS + _F + _S_FIELD,
}


# The via geometry a PLANNED D-256 escape is allowed to use.
#
# MEASURED, and it is the whole difference between D-256 being takeable and not:
# `U18.10` is the LTC4368 GATE output on the corner of an MSOP-10 at 0.50 mm
# pitch, and its single legal escape corridor is a dead-end slot.  With PR-45
# asking for a REACHABLE via site rather than merely a nearby one, the site
# exists at 0.50 mm and does NOT exist at 0.55 mm or 0.60 mm:
#
#     via 0.60 / 0.30   U18.10 -> R76.1   NO_VIA_SITE
#     via 0.55 / 0.25   U18.10 -> R76.1   NO_VIA_SITE
#     via 0.50 / 0.25   U18.10 -> R76.1   OK, 8.626 mm at 0.20 mm
#     via 0.50 / 0.25   U18.10 -> Q3.4    OK, 13.062 mm at 0.20 mm
#
# 0.50 / 0.25 is the board's OWN DECLARED FLOOR, not a relaxation of it:
#
#     min_via_diameter        0.50 mm   -> 0.50 is exactly at it
#     min_via_annular_width   0.125 mm  -> (0.50 - 0.25) / 2 = 0.125, exactly at it
#     min_through_hole_diameter 0.20 mm -> 0.25 clears it
#     min_hole_clearance      0.25 mm   -> enforced by DRC, per connection
#
# and the project already carries one non-Default fine via: the USB_D class at
# 0.55 / 0.25, the "approved 0.25/0.55 geometry" of retired rule R9.
#
# IT IS STILL A CTO MATTER, AND IT IS SURFACED RATHER THAN ADOPTED SILENTLY:
# a via that sits on TWO declared minimums at once is a fabrication-yield
# question, not a routing one, and it is raised as such in the closeout.  The
# harness's guard is unchanged - gate() refills the plane and runs full DRC
# after every single connection and rejects any new violation class - so an
# illegal via cannot survive to the manifest.
# D-257 (FBV2-P2-002L) SUPERSEDES the 002K 0.50/0.25 figure and it is a
# MANUFACTURING ruling, not a routing convenience:
#
#     PREFERRED  0.35 mm diameter / 0.20 mm drill    ordinary through via
#     RESERVE    0.25 mm diameter / 0.15 mm drill    ordinary through via
#
# and nothing smaller.  NO blind via, NO buried via, NO laser microvia: 002K
# found that `U18.10` has a reachable site at 0.20 mm and that finding is NOT a
# route, because KiCad's `min_microvia_diameter = 0.20` is a CAD default and not
# an authorisation from a fabricator.  The reserve is taken only where the
# preferred geometry is MEASURED impossible, and only on via geometry -- never
# to buy a corridor that a legal width could not have.
D257_VIA_PREFERRED = (350000, 200000)
D257_VIA_RESERVE = (250000, 150000)
D257_VIA_LADDER = (D257_VIA_PREFERRED, D257_VIA_RESERVE)

# Kept as the default for any planned escape that does not name its own.
D256_VIA = D257_VIA_PREFERRED


# ---- D-256 / section 10: the Q3 south row, gate BEFORE the sense pair -----
#
# PR-26 put Q*_CS ahead of LTC_GATE and it was MEASURED right at the 002F
# prefix.  With PR-43 in force it is measured wrong, and the reason is the one
# PR-23 wrote down: on each SOIC-8 south row Q*_CS owns pins 1 and 3 while
# LTC_GATE owns 2 and 4, the nets INTERLEAVE, and whichever goes first takes
# the slot.  Measured on the FBV2-P2-002K screen boards:
#
#   Q3_CS first, on B.Cu     Q3.2 boxed - LTC_GATE loses the pad outright
#   Q3_CS first, on F.Cu     Q3.2 still boxed: the hop leaves B.Cu ESCAPE STUBS
#                            and two vias in the very slot Q3.2 needs, and
#                            Q3.2 -> Q3.4 then costs 15.991 mm on F.Cu with
#                            two vias - on a MOSFET GATE DRIVE path
#   LTC_GATE first, on B.Cu  Q3.2 -> Q3.4 routes 5.500 mm on B.Cu, ZERO vias,
#                            and Q3_CS takes section 10's authorised layer
#                            excursion instead at 5.583 mm with two vias
#
# The gate drive is the path that should not be carrying vias and length, so
# the gate goes first and the sense pair takes the excursion.  Section 10's
# reserve is spent on exactly what section 10 describes - Q3_CS - and it is
# spent because it was measured to be the local blocker, not pre-emptively.
PLAN_8_GATE_Q3_FIRST = [
    (N + 'LTC_GATE', 'Q3.2', 'Q3.4', 'SIG', LAD_SIG, None),
]


# ---- PR-47 / D-258: the Q3 south-row POFV escape -------------------------
#
# `Q3.3` cannot emit legal copper in any direction at any legal width, so it
# takes a filled/capped ordinary THROUGH via-in-pad and leaves on one of the
# six-layer stack's internal signal layers.  `Q3.1` keeps an ORDINARY external
# via - it has four escape directions and does not need the premium process,
# and section 6 forbids adding via-in-pad to unrelated pads pre-emptively.
#
# With Q3_CS off the B.Cu south row entirely, `LTC_GATE Q3.2 -> Q3.4` gets the
# slot back on B.Cu with zero vias - which is the right answer for a MOSFET
# gate drive and the reason this is worth a premium via on one pad.
POFV_Q3 = {
    (N + 'Q3_CS', 'Q3.3', 'Q3.1'): dict(pofv='Q3.3', inner='I2',
                                        via=(350000, 200000)),
}

PLAN_8_CS_POFV = [
    (N + 'Q2_CS', 'Q2.1', 'Q2.3', 'SIG', LAD_SIG, None),
    (N + 'Q3_CS', 'Q3.3', 'Q3.1', 'SIG', LAD_SIG, None),
]


# ---- FBV2-P2-002Q section 9: the R75 Kelvin taps, routed EARLY -----------
#
# D-262 read FBV2-P2-002P's Kelvin result correctly: the placement is fine and
# the ROUTE is the problem.  Analytic 7.378 / 7.267 mm came back routed as
# 18.764 / 7.886 - an eleven-millimetre detour on a measurement branch whose
# direct path is under eight.
#
# The cause is ordering.  Inside PLAN_0_U18 the two Kelvin taps are queued with
# the rest of U18's pin field, which runs AFTER the 1.50 mm trunk and the whole
# BAT_MAIN chain.  By then the wide copper has taken the direct lane and the
# tap goes round it.
#
# Each tap SHARES ITS NET with the current path it measures - `U18.9`/`R75.1`
# are both BAT_SENSE, `U18.8`/`R75.2` are both BAT_PROTECTED_P - so early
# Kelvin copper is same-net to the trunk that follows and cannot obstruct it as
# a foreign net.  That is the argument for going first; it is NOT taken on
# faith, and section 9 requires it measured on the real prefix.
PLAN_0A_KELVIN = [
    (N + 'BAT_SENSE', 'U18.9', 'R75.1', 'SENSE', [W_SENSE], 'BAT_SENSE_KELVIN'),
    (N + 'BAT_PROTECTED_P', 'U18.8', 'R75.2', 'SENSE', [W_SENSE],
     'BAT_PROT_TAP_U18'),
]
KELVIN_KEYS = frozenset((r[0], r[1], r[2]) for r in PLAN_0A_KELVIN)


# ---- D-263 section 14: the Kelvin pair on a PAIRED INTERNAL LAYER --------
#
# FBV2-P2-002Q measured the Kelvin pair routed as 8.667 / 11.130 mm against a
# 10.000 mm cap, with one branch taking an F.Cu excursion and the other a B.Cu
# detour - and section 17 forbids accepting that asymmetry as the final answer.
#
# The pair is LOW-CURRENT SENSE routing.  It carries no pack current, so it has
# no business competing for B.Cu with the trunk and the pin field, and the
# six-layer stack exists precisely so it does not have to.  Both branches go on
# the SAME internal signal layer with the SAME topology and the SAME via count:
# short B.Cu pad escape, one ordinary 0.35/0.20 through via, internal run, one
# ordinary through via, short B.Cu destination escape.  Two vias per branch,
# no POFV, no microvia.
#
# Symmetry is the point.  A Kelvin pair whose two halves take different layers
# and different via counts is not a matched measurement pair, whatever its
# lengths come out at.
KELVIN_INNER = {
    (N + 'BAT_SENSE', 'U18.9', 'R75.1'):
        dict(layer='I2', via=(350000, 200000)),
    (N + 'BAT_PROTECTED_P', 'U18.8', 'R75.2'):
        dict(layer='I2', via=(350000, 200000)),
}

# ---------------------------------------------------------------- D-266 -----
# FBV2-P2-002T sections 5-9 and 14: SCARCE-PAD ESCAPE RESERVATION.
#
# The order below is the ruling, and each step exists because a measurement
# said so:
#
#   s5  the BAT_SENSE CURRENT path goes first.  On a clean board Q3.6, Q3.5,
#       R75.1 and R75.2 every one escape at 1.50 mm with 2-5 directions
#       (002T section 3), and 002S watched Q3.6 lose all of that to 28 track
#       segments laid for other branches.  This is real 1.00 mm outer copper,
#       zero vias, not a stub.
#   s6-7 the four Kelvin endpoints reserve ONLY their neck and via.  Measured
#       on the clean board, each has a 0.35/0.20 through-via site reachable
#       within 0.89-1.38 mm on B.Cu -> In2.  Reserving is cheap; losing the
#       exit is not.
#   s14 the two branches are then JOINED on the SAME inner layer, which cannot
#       fail for want of a lane because the scarce part was already spent.
PLAN_D266_SENSE = [
    (N + 'BAT_SENSE', 'Q3.5', 'Q3.6', 'TRUNK', LAD_BAT, None),
    (N + 'BAT_SENSE', 'Q3.6', 'R75.1', 'TRUNK', LAD_BAT, None),
]

# BOTH ENDS OF A BRANCH ARE RESERVED AS ONE ITEM, AND GATED ONCE.
#
# Reserved end-by-end, the second stub of a pair was rejected with
# `via_diameter`, `track_width` and `drill_out_of_range` together - the
# signature of copper judged OUTSIDE its own D-249 corridor - while the first
# passed, on either order.  A Kelvin branch is one path role and one corridor;
# splitting its reservation into two separately-gated items asks DRC about half
# a branch, which is not a question the rules were written to answer.
PLAN_D266_RESERVE = [
    (N + 'BAT_SENSE', 'U18.9', 'R75.1', 'RESERVE_PAIR', [W_SENSE], 'BAT_SENSE_KELVIN'),
    (N + 'BAT_PROTECTED_P', 'U18.8', 'R75.2', 'RESERVE_PAIR', [W_SENSE], 'BAT_PROT_TAP_U18'),
]

PLAN_D266_JOIN = [
    (N + 'BAT_SENSE', 'U18.9', 'R75.1', 'JOIN', [W_SENSE], 'BAT_SENSE_KELVIN'),
    (N + 'BAT_PROTECTED_P', 'U18.8', 'R75.2', 'JOIN', [W_SENSE], 'BAT_PROT_TAP_U18'),
]

# D-266 section 9.  LTC_UV U18.2 -> R79.2 MAY BEGIN AT ITS MEASURED RUNG.
#
# 002S measured U18.2 still escaping at 0.20 mm on the finished board while the
# branch had failed NO_PATH; 002T section 3 measures the same 0.20 mm exit on a
# CLEAN board with two directions.  LAD_SIG already contains 0.20 - the branch
# simply spent its corridor at 0.25 first.  Starting it one rung down is NOT a
# new minimum and NOT a global ladder change: it applies to this ONE branch,
# every other SIG connection keeps LAD_SIG unchanged, and nothing here goes
# below the 0.15 mm floor LAD_SIG already carries.
D266_LADDER = {
    (N + 'LTC_UV', 'U18.2', 'R79.2'): [200000, 150000],
}


# ---------------------------------------------------------------- D-267 -----
# FBV2-P2-002U section 2: EARLY HIGH-CURRENT ESCAPE RESERVATION, D9.1 ONLY.
#
# > An early high-current escape reservation is permitted only for D9.1, at the
# > existing BPP trunk target/floor, outer-layer-only and zero-via.  It
# > preserves the pad exit without completing the current path early.
#
# 002T left exactly one thing standing: `R75.2 -> D9.1` returned NO LEGAL
# ESCAPE at >= 1.200 mm with `D9.1` behind 37 track segments, because the trunk
# is routed LAST - which is what protects the pin field and is not up for
# revision.  Measured on a CLEAN board `D9.1` escapes at 1.50 mm in SIX
# directions and at 1.20 mm in six, so nothing about the pad is the problem.
#
# The staging points below are taken from the clean-board trunk itself: routed
# with nothing in its way, `R75.2 -> D9.1` runs 19.878 mm at 1.50 mm and leaves
# D9 heading south-west to (10.800, 73.000), then west along y = 73.0 past the
# divider column to (7.700, 73.000) and (7.000, 72.300).  Reserving a prefix of
# THAT path is what keeps the exit; inventing a staging point would not.
D267_STAGING = {
    'F1': (10800000, 73000000),    # clear of D9's immediate neighbourhood
    'F2': (7700000, 73000000),     # west of the R77/R78 divider column
    'F3': (7000000, 72300000),     # at the turn north, furthest committed
}

# The trunk's own ladder, unchanged: 1.50 mm target, 1.20 mm floor, PR-49 walks
# it.  A reservation NEVER goes below 1.20 mm.
LAD_D9_RESERVE = [W_TRUNK_BPP, 1200000]
