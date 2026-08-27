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

# ---------------------------------------------------------------------
# PR-48 / D-257  (FBV2-P2-002L)
#
# D-249 ruled WIDTH by path role and said nothing about CLEARANCE, and the two
# are not interchangeable.  `BAT_RAW U18.1 -> R77.1` is a ruled 0.20 mm microamp
# VIN tap that passes every width rule and is still rejected by
# `BAT_MAIN routed clearance` - 0.300 mm required, 0.250 mm measured - because
# the wide-net spacing rule fires on the tap's own target pad.  The U14.2 and
# U14.3 fuel-gauge branches fail the identical rule at 0.2347 / 0.2350 mm.
# A corridor that relaxes width for a nanoamp branch has to decide what it does
# about spacing too, or the branch is unroutable for a reason nobody ruled.
#
# The CTO ruling is a LOCAL 0.20 mm clearance for short low-current escape and
# tap corridors around U18, U14 and Q3's control/sense pins.  It is conditioned
# on A.NetName AND A.enclosedByArea(), exactly like the width overrides, so it
# reaches one net inside one bounded corridor and nothing else.  It does NOT
# touch the global board clearance, the high-current trunk spacing, board-edge
# clearance, or the hole rules.
#
# D-257 additionally rules the ORDINARY THROUGH VIA a fine-pitch escape may use:
# 0.35 / 0.20 preferred, 0.25 / 0.15 as an absolute reserve, and NOTHING
# SMALLER.  No blind via, no buried via, no laser microvia - the KiCad
# `min_microvia_diameter` value is a CAD default, not a manufacturing
# authorisation, and 002K's finding that a 0.20 mm site exists for U18.10 is
# therefore not a route.  Both ruled geometries sit below the board's global
# `min_via_diameter` 0.50 mm and `min_via_annular_width` 0.125 mm, so each
# bounded escape corridor carries its own via_diameter / annular_width /
# hole_size override.  MEASURED: with these rules a 0.35/0.20 through via inside
# a named area clears DRC, and without them it reports `via_diameter` and
# `annular_width`; no other violation class moves either way.
# ---------------------------------------------------------------------
# D-264(a)  (FBV2-P2-002S)
#
# OUTER-LAYER-ONLY IS A CURRENT PATH ROLE RESTRICTION, NOT AN
# ENTIRE-NET-NAME RESTRICTION.
#
# `BAT_MAIN is outer-layer only` is electrically right about what it was
# written for: at 0.5 oz an inner layer needs 2.73 mm for 1.5 A at a 10 K
# rise, so distributing pack current on In2/In3 defeats the point of the
# layer.  But it is conditioned on `A.hasNetclass('BAT_MAIN')`, and a
# high-impedance Kelvin branch shares that netclass while carrying
# essentially no current at all.  FBV2-P2-002R hit exactly that:
# `BAT_PROTECTED_P U18.8 -> R75.2`, a nanoamp sense tap, was rejected with
# `Items not allowed (rule 'BAT_MAIN is outer-layer only')`.
#
# This is D-249's lesson one property over.  D-249 replaced a net-wide WIDTH
# floor with path role because the same net feeds a 1.5 A trunk and a
# nanoamp sense input; the LAYER rule has the same shape and now gets the
# same treatment.  The restriction is re-emitted here, LAST so it governs,
# with exactly two bounded exceptions - the two named D-249 sense corridors
# and nothing else.  Same-net copper anywhere outside those corridors is
# still barred from In2 AND, closing a gap the six-layer migration opened,
# from In3.
#
# Nothing else moves: no width, no clearance, no current-path rule, no GND
# plane.  The corridors are the ones that already exist, already bounded and
# already grown from the branch's own copper.
INNER_SENSE_AREAS = ('BAT_SENSE_KELVIN', 'BAT_PROT_TAP_U18')

OUTER_ONLY = (u'(rule "BAT_MAIN is outer-layer only - %s - D-264"\n'
              u'\t(layer "%s")\n'
              u'\t(severity error)\n'
              u'\t(constraint disallow track)\n'
              u'\t(condition "A.hasNetclass(\'BAT_MAIN\') && %s"))\n')


def outer_only_rules():
    """The D-264 path-role form of the outer-layer restriction."""
    excl = ' && '.join("!A.enclosedByArea('%s')" % a for a in INNER_SENSE_AREAS)
    return [OUTER_ONLY % (L.split('.')[0], L, excl)
            for L in ('In2.Cu', 'In3.Cu')]


LOCAL_CLR = (u'(rule "%s - local fine-pitch clearance, PR-48"\n'
             u'\t(constraint clearance (min %.2fmm))\n'
             u'\t(condition "A.NetName == \'%s\' && A.enclosedByArea(\'%s\')"))\n')

FINE_VIA = (u'(rule "%s - fine-pitch escape via, D-257"\n'
            u'\t(constraint via_diameter (min %.2fmm) (opt 0.35mm))\n'
            u'\t(condition "A.NetName == \'%s\' && A.enclosedByArea(\'%s\')"))\n'
            u'\n'
            u'(rule "%s - fine-pitch escape annular ring, D-257"\n'
            u'\t(constraint annular_width (min %.3fmm))\n'
            u'\t(condition "A.NetName == \'%s\' && A.enclosedByArea(\'%s\')"))\n'
            u'\n'
            u'(rule "%s - fine-pitch escape hole, D-257"\n'
            u'\t(constraint hole_size (min %.2fmm) (opt 0.20mm))\n'
            u'\t(condition "A.NetName == \'%s\' && A.enclosedByArea(\'%s\')"))\n')

# The D-249 corridors that PR-48's local clearance applies to as standing rule.
# These are the three MEASURED PR-48 cases plus the two other ruled U18 taps
# that share the same pin field and the same wide-net neighbour copper.
# EXACTLY THE THREE MEASURED PR-48 CASES, AND NOTHING ELSE.
#
# The first cut of this list also carried BAT_PROT_TAP_U18 and
# BAT_SENSE_KELVIN, on the reasoning that they share U18's pin field.  That was
# wrong, and the board said so within one screen: a clearance rule states a
# MINIMUM, this block is written LAST so it wins, and both of those corridors
# were already running legally at 0.150 mm under the pad-escape rules.  Adding
# a 0.20 mm floor there did not relax anything - it RAISED the requirement on
# copper that was already compliant, and `BAT_SENSE Kelvin sense tap ...
# clearance 0.2000 mm; actual 0.1500 mm` then rejected every connection after
# it.  A relaxation that is applied where nothing needed relaxing is a
# restriction.  Section 4 says to use the smallest corridor necessary; these
# are the corridors that were measured to need it.
FIXED_CLR = [
    ('BAT_RAW_TAP_U18', N + 'BAT_RAW', 0.20,
     'BAT_RAW LTC4368 VIN supply tap'),          # PR-48 case A, U18.1
    ('BAT_PROT_TAP_U14', N + 'BAT_PROTECTED_P', 0.20,
     'BAT_PROTECTED_P fuel-gauge and test taps'),  # PR-48 cases B and C
]


def compose(stubs, fine=()):
    """stubs: list of (area_name, net_name, min_mm, comment)
    fine:  list of (area_name, net_name, clr_mm, via_dia_mm, via_drill_mm, note)
           -- PR-48 / D-257 bounded fine-pitch escape corridors."""
    rows = [(mn, opt, name, net, note) for (name, net, mn, opt, note) in FIXED]
    rows += [(mn, mn, name, net, note) for (name, net, mn, note) in stubs]
    rows.sort(key=lambda r: -r[0])
    out = [TAILHEAD]
    for (mn, opt, name, net, note) in rows:
        out.append(RULE % (note, mn, opt, net, name))
    # PR-48 / D-257 come LAST of all: they are the most specific statement on
    # the board -- one net, inside one corridor bounding one approved escape --
    # and KiCad applies the last matching rule.
    for (name, net, clr, note) in FIXED_CLR:
        out.append(LOCAL_CLR % (note, clr, net, name))
    # D-264(a) LAST OF ALL: the path-role form of the outer-layer restriction
    # governs, and its two bounded exceptions are the only inner-layer
    # authority any BAT_MAIN-class copper has.
    out.extend(outer_only_rules())
    for (name, net, clr, vdia, vdrill, note) in fine:
        # VIA GEOMETRY ONLY.  A D-257 escape corridor exists so a 0.35/0.20
        # through via is legal inside it; it does NOT need, and must not carry,
        # a clearance floor.  The first six-layer screen showed why: the
        # corridor is grown from the laid track with a 0.3 mm tolerance, so it
        # swallows neighbouring copper, and a 0.20 mm floor imposed there then
        # fires on pairs the corridor was never meant to govern -
        # `LTC_OV R77.2 -> R78.1` was rejected by
        # `D-257 LTC_GATE U18.10->Q3.4 escape ... clearance 0.2000; actual
        # 0.1000`.  This is the FBV2-P2-002L lesson a second time: relax
        # exactly what was measured to need relaxing.  The three PR-48 cases
        # keep their clearance in FIXED_CLR, where they were measured.
        ann = (vdia - vdrill) / 2.0
        out.append(FINE_VIA % (note, vdia, net, name,
                               note, ann, net, name,
                               note, vdrill, net, name))
    return u"\n".join(out)


def write(pcb, stubs, fine=()):
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
    # D-264(a): REMOVE THE UNSCOPED FORM, DO NOT MERELY OUTRANK IT.
    #
    # KiCad's `disallow` constraint is not last-match-wins the way a width or
    # clearance constraint is - EVERY matching disallow rule fires.  So
    # appending the path-role form after the net-name form leaves both live and
    # the sense corridors are still barred; measured, C and D of the D-264 probe
    # failed exactly that way while A, B and E passed.  The static rule is
    # therefore excised from the board this block is written onto and re-emitted
    # in its scoped form.  The AUTHORITATIVE .kicad_dru keeps the original text,
    # because the sense corridors are router-created and a rule naming an area
    # that does not exist is what dru_probe exists to catch.
    old_rule = '(rule "BAT_MAIN is outer-layer only"'
    i2 = d.find(old_rule)
    if i2 >= 0:
        j2 = d.find('\n\n', d.find('(condition', i2))
        d = d[:i2] + d[j2 + 2:] if j2 > 0 else d[:i2]
    d = d.rstrip('\n') + "\n\n\n" + compose(stubs, fine).rstrip('\n') + "\n"
    open(p, 'wb').write((d.replace('\n', '\r\n') if crlf else d).encode('utf-8'))
