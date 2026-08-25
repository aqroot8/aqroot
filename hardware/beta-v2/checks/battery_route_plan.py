# -*- coding: utf-8 -*-
"""FBV2-P2-002C routing plan, written as PATH ROLES.

Every entry says what the copper IS, not just which net it belongs to.

  TRUNK  carries pack current.  1.50 mm on BAT_PROTECTED_P (D-249), 1.00 mm on
         the BAT_MAIN nets.  Never narrowed below the class floor.
  TAP    a microamp branch off a power node: a divider top, a clamp, a
         decoupling capacitor, a test point.  Routed at 0.60 mm - still inside
         BAT_MAIN's own 1.00 / 0.60 band, so NO rule exception is involved.
  SENSE  a ruled sense branch at 0.20 mm inside its own bounded rule area.
  SIG    an ordinary Default-class control net.

The LTC4368 divider resistors are megohm parts (R77 is 3.65 M), so R77/R79/R80,
R86/R89, D12, C59, TP16 and U18.1 carry microamps and are taps by inspection of
the schematic, not by assumption.
"""
N = '/01_POWER_TREE/'

W_TRUNK_BAT = 1000000
W_TRUNK_BPP = 1500000
W_TAP = 600000
W_SENSE = 200000
W_SIG = 250000

# (net, a, b, role, width ladder, area)
PLAN_A = [
    # ---- A1. the high-current chain, cell to protected node ----------------
    (N + 'BAT_CONNECTOR_P', 'J4.1', 'F1.1', 'TRUNK', [W_TRUNK_BAT, 800000, 600000], None),
    (N + 'BAT_RAW', 'F1.2', 'Q2.8', 'TRUNK', [W_TRUNK_BAT, 800000, 600000], None),
    (N + 'BAT_RAW', 'Q2.8', 'Q2.7', 'TRUNK', [W_TRUNK_BAT, 800000, 600000], None),
    (N + 'BAT_MID', 'Q2.5', 'Q2.6', 'TRUNK', [W_TRUNK_BAT, 800000, 600000], None),
    (N + 'BAT_MID', 'Q2.6', 'Q3.8', 'TRUNK', [W_TRUNK_BAT, 800000, 600000], None),
    (N + 'BAT_MID', 'Q3.8', 'Q3.7', 'TRUNK', [W_TRUNK_BAT, 800000, 600000], None),
    (N + 'BAT_SENSE', 'Q3.5', 'Q3.6', 'TRUNK', [W_TRUNK_BAT, 800000, 600000], None),
    (N + 'BAT_SENSE', 'Q3.6', 'R75.1', 'TRUNK', [W_TRUNK_BAT, 800000, 600000], None),
    # ---- A2. BAT_PROTECTED_P trunk, R75 -> charger BAT pin -----------------
    # The trunk is R75 -> D9 -> U11.2 and NOTHING ELSE.  C25, C36 and C58 are
    # 1 uF / 100 nF decoupling capacitors: they are SHUNT elements that tap the
    # node, and chaining the 1.5 A path through their solder joints would be
    # both electrically wrong and the reason the first attempt needed an 80 mm
    # detour to keep 1.20 mm through them.
    (N + 'BAT_PROTECTED_P', 'R75.2', 'D9.1', 'TRUNK', [W_TRUNK_BPP, 1200000], None),
]

# decoupling capacitors: shunt taps off the protected node, widest that fits
PLAN_CAPS = [
    (N + 'BAT_PROTECTED_P', 'C58.1', '(node)', 'TAP',
     [W_TRUNK_BPP, 1200000, 1000000, 800000, 600000], None),
    (N + 'BAT_PROTECTED_P', 'C36.1', '(node)', 'TAP',
     [W_TRUNK_BPP, 1200000, 1000000, 800000, 600000], None),
    (N + 'BAT_PROTECTED_P', 'C25.1', '(node)', 'TAP',
     [W_TRUNK_BPP, 1200000, 1000000, 800000, 600000], None),
]

# U14 sits 1.245 mm from the west edge with its pin row FACING that edge, so
# U14.2 and U14.3 have almost no routing slack at all - 0.295 mm of escape and
# one direction.  They go first, before anything with alternatives spends the
# corridor they need.
PLAN_SW = [
    (N + 'BAT_PROTECTED_P', 'TP15.1', 'U14.2', 'SENSE', [W_SENSE, 150000], 'BAT_PROT_TAP_U14'),
    (N + 'BAT_PROTECTED_P', 'U14.2', 'U14.3', 'SENSE', [W_SENSE, 150000], 'BAT_PROT_TAP_U14'),
    (N + 'BAT_PROTECTED_P', 'TP15.1', 'D9.1', 'SENSE', [W_SENSE, 150000], 'BAT_PROT_TAP_U14'),
]

# C59 is a 1 uF bulk capacitor boxed into the south-west corner between U14,
# C68, TP11, R105 and the board edge.  It has the least routing slack of
# anything in the block, so it goes early: leave it to the end and the corridor
# it needs has already been spent on something with alternatives.
PLAN_TIGHT = [
    (N + 'BAT_RAW', 'C59.1', 'R77.1', 'TAP',
     [W_TAP, 500000, 400000, 300000, 250000, 200000, 150000], None),
]

# ---- B. the ruled sense / Kelvin branches ---------------------------------
PLAN_B = [
    (N + 'BAT_SENSE', 'U18.9', 'R75.1', 'SENSE', [W_SENSE], 'BAT_SENSE_KELVIN'),
    (N + 'BAT_PROTECTED_P', 'U18.8', 'R75.2', 'SENSE', [W_SENSE], 'BAT_PROT_TAP_U18'),
]

# ---- E. fuel-gauge and test branches --------------------------------------
PLAN_E = [
    (N + 'BAT_CONNECTOR_P', 'TP34.1', '(node)', 'TAP', [W_TAP, 500000, 400000, 300000], None),
    (N + 'BAT_SENSE', 'TP20.1', '(node)', 'TAP', [W_TAP, 500000, 400000, 300000], None),
]

# routed after the BAT_RAW taps exist, so it can join the nearest node
PLAN_B2 = [
    (N + 'BAT_RAW', 'U18.1', '(node)', 'SENSE', [W_SENSE], 'BAT_RAW_TAP_U18'),
]

# ---- A3. microamp taps off the raw battery node ---------------------------
PLAN_TAPS = [
    (N + 'BAT_RAW', 'R80.1', 'Q2.7', 'TAP', [W_TAP, 500000, 400000, 300000], None),
    (N + 'BAT_RAW', 'R79.1', 'R80.1', 'TAP', [W_TAP, 500000, 400000, 300000], None),
    (N + 'BAT_RAW', 'R77.1', 'R79.1', 'TAP', [W_TAP, 500000, 400000, 300000], None),
    (N + 'BAT_RAW', 'D12.1', 'R77.1', 'TAP', [W_TAP, 500000, 400000, 300000], None),
    (N + 'BAT_RAW', 'TP16.1', 'Q2.7', 'TAP', [W_TAP, 500000, 400000, 300000], None),
    (N + 'BAT_RAW', 'R86.2', '(node)', 'TAP', [W_TAP, 500000, 400000, 300000, 250000], None),
    (N + 'BAT_RAW', 'R89.1', '(node)', 'TAP', [W_TAP, 500000, 400000, 300000, 250000], None),
]

# LTC_GATE first: it has seven pads spread over both FETs and the LTC, and its
# escapes share Q2/Q3's south pad rows with Q2_CS and Q3_CS.  Whichever of them
# is routed first owns those rows, and LTC_GATE is the one with no slack.
SIGNAL_ORDER = ['LTC_GATE', 'Q2_CS', 'Q3_CS', 'LTC_GATE_RC', 'LTC_OV', 'LTC_UV',
                'LTC_SHDN', 'LTC4368_FAULT_N', 'BAT_PROT_SHDN_CTL',
                'VBRIDGE_TOP', 'VREF_TOP', 'REF_HO', 'REF_POL', 'N_POL',
                'N_BATDIV', 'VREC_VCC', 'REC_GATE_N', 'REC_POL_OK', 'REC_AND1',
                'REC_AND2', 'REC_BAT_LOW', 'REC_FAULT_B', 'REC_LIM_IN',
                'REC_DIODE_IN']
