# -*- coding: utf-8 -*-
"""FBV2-P2-002L section 2 -- ASSERT WHICH BOARD YOU ARE ROUTING.

FBV2-P2-002K ran NINE screens on the wrong placement.  `AQROOT_ECO_002F` was
never set, so every one of them measured the AUTHORITATIVE poses while the
task, the plan and every verdict from 002F to 002J assume the 002F ECO.  It was
caught -- section 14's Kelvin check came out 3.179 / 13.152 mm, a 9.973 mm
mismatch against a standing 4.464 / 4.464 / 0.000 -- but it was caught by a
DOWNSTREAM MEASUREMENT AND BY LUCK OF ORDERING, four hours in, and it could as
easily have been caught after an authoritative write.

The failure was not that a flag was forgotten.  It was that NOTHING IN THE RUN
STATED WHICH BOARD IT WAS ROUTING.  A run that cannot name its own placement
cannot be compared with another run, and a screen whose placement is implicit
is not evidence.

So: every routing screen now prints a PLACEMENT FINGERPRINT of the poses that
decide the west margin, and `AQROOT_EXPECT_PLACEMENT` makes it an assertion.
A mismatch is a FAIL BEFORE ROUTING, not a footnote afterwards.
"""
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import pcbnew

# The parts whose pose decides the contested west margin.  Section 2 names
# U18, R75, R80, R81, Q2, Q3 and U19; R76..R79 and R82/R83 are included because
# they are U18's own divider and trip ring and a screen that moves them is not
# the same experiment either.
GUARDED = ('U18', 'R75', 'R76', 'R77', 'R78', 'R79', 'R80', 'R81', 'R82',
           'R83', 'Q2', 'Q3', 'U14', 'U19')

TOL_MM = 0.0005      # half a micron: these are exact numbers, not measurements


def fingerprint(board):
    """{ref: (x_mm, y_mm, rot_deg, layer)} for the guarded refs."""
    b = pcbnew.LoadBoard(os.path.abspath(board)) if isinstance(board, str) else board
    out = {}
    for f in b.GetFootprints():
        r = f.GetReference()
        if r in GUARDED:
            out[r] = (round(f.GetPosition().x / 1e6, 3),
                      round(f.GetPosition().y / 1e6, 3),
                      round(f.GetOrientationDegrees(), 1),
                      b.GetLayerName(f.GetLayer()))
    return out


def render(fp):
    return '  '.join('%s@%.3f,%.3f/%.0f%s' % (r, v[0], v[1], v[2],
                                              '' if v[3] == 'B.Cu' else '/' + v[3])
                     for r, v in sorted(fp.items()))


def differs(a, b_):
    """Refs whose pose differs between two fingerprints, with both values."""
    out = []
    for r in sorted(set(a) | set(b_)):
        x, y = a.get(r), b_.get(r)
        if x is None or y is None:
            out.append((r, x, y))
            continue
        # ANGLES ARE COMPARED MODULO 360.  KiCad stores 270 deg as -90, so a
        # candidate file saying `270.0` and a board reporting `-90.0` describe
        # the SAME pose - and the guard refused to route on exactly that,
        # correctly by its own logic and uselessly in fact.  A guard that fires
        # on a difference that is not a difference trains people to ignore it,
        # which is the one thing this guard must never do.
        if (abs(x[0] - y[0]) > TOL_MM or abs(x[1] - y[1]) > TOL_MM
                or abs((x[2] - y[2]) % 360.0) > 0.05
                and abs((x[2] - y[2]) % 360.0 - 360.0) > 0.05
                or x[3] != y[3]):
            out.append((r, x, y))
    return out


def expected(name):
    """The pose set a named placement is DEFINED to have.

    AUTHORITATIVE is read from the committed board, so it cannot drift.
    ECO_002F is the AUTHORITATIVE set with place_p2_002f.MOVES applied, which
    is exactly what route_battery_block does with AQROOT_ECO_002F=1 -- the
    expectation is derived from the same source as the action, not restated
    beside it where the two could disagree.
    """
    import harness_paths as HP
    base = fingerprint(HP.project_file(HP.PCBNAME))
    key = (name or '').upper()
    # A candidate placement is named by a JSON file of {ref: [x, y, rot, layer]}
    # overrides on top of a base placement, written by the search that proposed
    # it.  A candidate is therefore just as assertable as the two standing
    # placements - which is the point: the U18 search of section 6 moves nine
    # parts, and a screen that cannot state which of twelve candidates it is on
    # is exactly the 002K failure one level down.
    if name and os.path.isfile(name):
        import json
        spec = json.load(open(name))
        out = dict(expected(spec.get('base', 'ECO_002F')))
        for ref, v in spec.get('moves', {}).items():
            if ref in out:
                out[ref] = (round(v[0], 3), round(v[1], 3), round(v[2], 1),
                            v[3] if len(v) > 3 else out[ref][3])
        return out
    if key in ('AUTHORITATIVE', 'AUTH', ''):
        return base
    if key in ('ECO_002F', 'ECO', '002F'):
        import place_p2_002f as ECO
        out = dict(base)
        for ref, (x, y, rot, lay) in ECO.MOVES.items():
            if ref in out:
                out[ref] = (round(x, 3), round(y, 3), round(rot, 1), lay)
        return out
    raise SystemExit('unknown placement name %r '
                     '(AUTHORITATIVE | ECO_002F | path to a candidate json)' % name)


def assert_placement(board, name, label='screen'):
    """FAIL BEFORE ROUTING if the board is not the placement that was asked for."""
    got = fingerprint(board)
    want = expected(name)
    bad = differs(want, got)
    if bad:
        msg = ['PLACEMENT IDENTITY MISMATCH -- refusing to route.',
               '  %s expected placement: %s' % (label, name),
               '  the board does not match it in %d part(s):' % len(bad)]
        for (r, w, g) in bad:
            msg.append('    %-5s expected %s   measured %s' % (r, w, g))
        msg.append('  Nothing was routed.  FBV2-P2-002K ran nine screens on the')
        msg.append('  wrong placement because no run stated which board it was on.')
        raise SystemExit('\n'.join(msg))
    return got


def main():
    import harness_paths as HP
    pcb = sys.argv[1] if len(sys.argv) > 1 else HP.project_file(HP.PCBNAME)
    fp = fingerprint(pcb)
    print('PLACEMENT FINGERPRINT  %s' % os.path.basename(pcb))
    print('  ' + render(fp))
    for nm in ('AUTHORITATIVE', 'ECO_002F'):
        bad = differs(expected(nm), fp)
        print('  vs %-14s %s' % (nm, 'MATCH' if not bad
                                 else '%d part(s) differ: %s'
                                      % (len(bad), ', '.join(r for r, _, _ in bad))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
