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
PLAN_TAPS = [
    (N + 'BAT_RAW', 'R80.1', 'Q2.7', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'R79.1', 'R80.1', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'R77.1', 'R79.1', 'TAP', LAD_TAP, None),
    (N + 'BAT_RAW', 'D12.1', 'R77.1', 'TAP', LAD_TAP, None),
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
