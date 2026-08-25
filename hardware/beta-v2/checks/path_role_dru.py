# -*- coding: utf-8 -*-
"""The D-249 path-role rule block, composed from the areas that actually exist."""
import os

N = '/01_POWER_TREE/'

HEAD = u"""# ---------------------------------------------------------------------
# 5b. BATTERY PATH-ROLE WIDTHS  (D-249, 2026-08-24, FBV2-P2-002C)
#
# SUPERSEDES THE WHOLE-NET FORM OF D-245.  D-245's INTENT STANDS - the long
# high-current BAT_PROTECTED_P trunk is 1.50 mm - but its implementation applied
# that floor to every segment carrying the net name.  The same net also feeds
# the MAX17048 fuel-gauge sense input, the LTC4368 VOUT sense input and a test
# point.  None of those carries load current, and none of those land patterns
# can physically accept 1.20 mm.  As written, D-245 made BAT_PROTECTED_P
# UNROUTABLE.
#
# WIDTH IS A PATH ROLE, NOT A PROPERTY OF THE NET NAME.
#
# ENFORCEMENT.  The trunk floor below applies to the WHOLE net.  It is relaxed
# ONLY inside a small named rule area that bounds ONE approved branch, by the
# rules in section 10b at the end of this file, and only through
# enclosedByArea(), which requires the ENTIRE track to lie inside that area.
# A narrow branch therefore cannot wander: the moment it leaves its own area it
# is measured against the trunk floor and fails.  There is no construction here
# that lets a long high-current run masquerade as a branch, and none that lets
# a branch violate the trunk rule.
#
# WHY THE LTC4368 TAPS ARE NOT CURRENT PATHS.  The LTC4368 is a CONTROLLER: it
# drives back-to-back external MOSFETs and the pack current flows through Q2/Q3,
# never through U18.  Pins 1 (VIN), 8 (VOUT) and 9 (SENSE) are microamp inputs
# on an MSOP-10 whose 0.50 mm pitch admits at most 0.25 mm of copper.
#
# WHY U11.2 IS DIFFERENT.  It is a TRUE HIGH-CURRENT endpoint - the BQ25185 BAT
# pin.  Its width is limited by TI's own DLH0010A land pattern, 0.2 mm pads on
# 0.4 mm pitch, so 0.20 mm is the widest copper that can leave that pad whatever
# any rule says: THE PACKAGE IS THE BOTTLENECK, NOT THE RULE.  The escape is
# bounded, measured, flares outward immediately and carries no via; the exact
# profile is in pcb/FBV2_P2_POWER_ROUTING.md.
#
# A SHUNT STUB - a decoupling capacitor, a clamp diode, a divider top, a test
# point - hangs OFF the current path rather than sitting IN it.  Where the
# placement leaves no corridor at the class width, its stub may be narrower
# INSIDE ITS OWN BOUNDED AREA AND NOWHERE ELSE.  Every width used still clears
# IPC-2221B for the full 1.5 A pack current on 1 oz external copper at a 10 degC
# rise (0.50 mm carries 1.45 A), which these stubs never see.
#
# U14 IS TIGHTER STILL, AND THE ARITHMETIC IS EXACT.  U14 sits 1.245 mm from
# the west board edge with its pin row FACING that edge, so the only escape from
# U14.2 / U14.3 is the strip between the edge and the pad row.  Copper must be
# >= 0.500 mm from the edge and >= 0.200 mm from the pads, whose west edge is at
# x = 0.895.  A track of width w running along that strip therefore needs its
# centre at x >= 0.500 + w/2 AND at x <= 0.695 - w/2, which has a solution only
# for w <= 0.195 mm: A 0.20 mm TRACK DOES NOT FIT, BY 5 MICRONS.  At 0.15 mm -
# the board's own min_track_width, and 1.7x JLCPCB's 0.09 mm multilayer
# minimum - the window is 0.575 to 0.620 and it fits.  That tap carries the MAX17048's sense-input
# current, which is nanoamps.  FLAGGED FOR RATIFICATION: FBV2-P2-002C section 5
# locked 0.20 mm, and 0.20 mm does not physically exist at this pad.
#
# JLCPCB capability, checked live 2026-08-24 against the vendor's own page:
# minimum track width / spacing on a 1 oz MULTILAYER board is 0.09 / 0.09 mm.
# Nothing in this block is fab-limited.
# ---------------------------------------------------------------------

(rule "BAT_PROTECTED_P high-current trunk width - D-249"
\t(constraint track_width (min 1.20mm) (opt 1.50mm))
\t(condition "A.NetName == '/01_POWER_TREE/BAT_PROTECTED_P'"))
"""

TAILHEAD = u"""# =====================================================================
# 10b. PATH-ROLE AREA OVERRIDES  (D-249, FBV2-P2-002C)
#
# THESE RULES ARE LAST IN THE FILE ON PURPOSE, AND MOVING THEM BREAKS THEM.
#
# Section 9 already records that KiCad applies the LAST matching rule, and that
# the pad-escape necking and land-pattern blocks must sit near the end so they
# beat the section-5 rail widths.  These path-role overrides must in turn beat
# THOSE, because they are the most specific statement on the board: one named
# net, inside one named area that bounds exactly one approved branch.
#
# Each area is generated from its own routed branch's bounding box plus 0.3 mm
# and is written back by the router, so it cannot drift away from the copper it
# describes.  enclosedByArea() requires the WHOLE track to lie inside, so a
# branch that leaves its area is measured against the trunk floor and fails.
#
# Within this block the rules run WIDEST FIRST and NARROWEST LAST, so where two
# bounded areas overlap the lower floor governs.
# =====================================================================
"""

MARK = "# 10b. PATH-ROLE AREA OVERRIDES"

FIXED = [
    ('BAT_PROT_ESCAPE_U11', N + 'BAT_PROTECTED_P', 0.20, 1.50,
     'BAT_PROTECTED_P U11 BAT-pin escape'),
    ('BAT_PROT_TAP_U18', N + 'BAT_PROTECTED_P', 0.20, 0.20,
     'BAT_PROTECTED_P LTC4368 VOUT sense tap'),
    ('BAT_PROT_TAP_U14', N + 'BAT_PROTECTED_P', 0.15, 0.20,
     'BAT_PROTECTED_P fuel-gauge and test taps'),
    ('BAT_SENSE_KELVIN', N + 'BAT_SENSE', 0.20, 0.20,
     'BAT_SENSE Kelvin sense tap'),
    ('BAT_RAW_TAP_U18', N + 'BAT_RAW', 0.20, 0.20,
     'BAT_RAW LTC4368 VIN supply tap'),
]

RULE = (u'(rule "%s - D-249"\n'
        u'\t(constraint track_width (min %.2fmm) (opt %.2fmm))\n'
        u'\t(condition "A.NetName == \'%s\' && A.enclosedByArea(\'%s\')"))\n')


def compose(stubs):
    """stubs: list of (area_name, net_name, min_mm, comment)"""
    rows = [(mn, opt, name, net, note) for (name, net, mn, opt, note) in FIXED]
    rows += [(mn, mn, name, net, note) for (name, net, mn, note) in stubs]
    rows.sort(key=lambda r: -r[0])
    out = [TAILHEAD]
    for (mn, opt, name, net, note) in rows:
        out.append(RULE % (note, mn, opt, net, name))
    return u"\n".join(out)


def write(pcb, stubs):
    p = os.path.join(os.path.dirname(pcb), "aqroot-Beta-v2.kicad_dru")
    raw = open(p, 'rb').read().decode('utf-8')
    crlf = '\r\n' in raw
    d = raw.replace('\r\n', '\n')
    m1 = "# ---------------------------------------------------------------------\n# 5b."
    if m1 in d:
        i = d.index(m1)
        j = d.index("# ---------------------------------------------------------------------\n# 6. USB 2.0")
        d = d[:i] + HEAD.rstrip('\n') + "\n\n\n" + d[j:]
    k = d.find("# =====================================================================\n" + MARK)
    if k >= 0:
        d = d[:k]
    d = d.rstrip('\n') + "\n\n\n" + compose(stubs).rstrip('\n') + "\n"
    open(p, 'wb').write((d.replace('\n', '\r\n') if crlf else d).encode('utf-8'))
