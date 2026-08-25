"""Full Beta v2 design-rule reference probe.

Run:  python hardware/beta-v2/checks/dru_probe.py

Created at FBV2-P2-000 to close P2-O5 permanently.

P2-O5 was this: the `.kicad_dru` inherited from Beta-DM referenced THIRTY-NINE
rule areas that the FBV2-P1 PCB rebuild had deleted.  KiCad's `intersectsArea()`
and `enclosedByArea()` return FALSE for an unknown area name -- they do not
error -- so twenty-two rules were silently inert and DRC was quietly reporting
a clean result against protection that no longer existed.  Nothing in the
toolchain could see it.

This probe asserts that every object a custom rule names still exists:

  * every `intersectsArea('X')` / `enclosedByArea('X')` resolves to a rule area
    in the board -- board-level zones AND footprint-embedded zones both count;
  * every `memberOfFootprint('X')` and `intersectsCourtyard('X')` resolves to a
    footprint reference on the board;
  * every `hasNetclass('X')` resolves to a netclass declared in the project;
  * every `A.NetName == 'X'` resolves to a net on the board;
  * every netclass PATTERN in the project matches at least one board net --
    a pattern that matches nothing is how `/BAT_PROTECTED_P` left the highest
    -current net on the board sitting on the 0.20 mm Default class.

Comment lines in the .kicad_dru are stripped before matching, so a name that
appears only in a retirement note is not treated as a live reference.

Exit code 0 = pass, 1 = fail.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.join(HERE, '..', 'kicad', 'aqroot-beta-v2')
DRU = os.path.join(KI, 'aqroot-Beta-v2.kicad_dru')
PRO = os.path.join(KI, 'aqroot-Beta-v2.kicad_pro')
PCB = os.path.join(KI, 'aqroot-Beta-v2.kicad_pcb')


def load():
    dru = open(DRU, 'rb').read().decode('utf-8')
    pcb = open(PCB, 'rb').read().decode('utf-8')
    pro = json.load(open(PRO, encoding='utf-8'))
    return dru, pcb, pro


def strip_comments(dru):
    return '\n'.join(l for l in dru.splitlines() if not l.lstrip().startswith('#'))


def board_areas(pcb):
    """Every named zone, board-level and footprint-embedded alike.

    Both kinds are rule areas to KiCad's DRC engine, so both are legal targets
    for intersectsArea().  The probe does not care which kind a name is.
    """
    return set(re.findall(r'\(name "([^"]+)"\)', pcb))


def board_refs(pcb):
    return set(re.findall(r'\(property "Reference" "([^"]+)"', pcb))


def board_nets(pcb):
    return set(re.findall(r'\(net "([^"]*)"\)', pcb))


def check(label, referenced, available, failures):
    missing = sorted(x for x in referenced if x not in available)
    mark = 'FAIL' if missing else 'OK'
    print('  %-22s %3d referenced, %d missing   %s'
          % (label, len(referenced), len(missing), mark))
    for m in missing:
        print('      MISSING: %r' % m)
        failures.append('%s: %r' % (label, m))


# --------------------------------------------------------------------------
# PR-11 / section 8: a width exception may only live inside a CORRIDOR.
#
# A bounding box around a 20 mm branch was a 67 x 23 mm hole in the trunk rule.
# These checks make that shape impossible to reintroduce quietly:
#
#   C1  every area a width rule names must exist on the board;
#   C2  a corridor must not be a rectangle - four vertices IS a bounding box;
#   C3  a corridor must fill most of its own bounding box, so it hugs the
#       branch instead of enclosing the neighbourhood;
#   C4  every track lying inside a corridor must belong to the corridor's own
#       net, so a corridor can never grant its lower floor to an unrelated
#       high-current traverse.
CORRIDOR_MIN_FILL = 0.35        # area / bbox area, below which it is a box
CORRIDOR_BOX_EXEMPT_MM2 = 9.0   # a genuinely tiny area may be a rectangle


def corridor_checks(failures):
    try:
        import pcbnew
    except ImportError:
        print('  corridors             skipped (needs KiCad python)')
        return
    dru = open(DRU, 'rb').read().decode('utf-8')
    body = strip_comments(dru)
    # area name -> net named in the same rule
    want = {}
    for m in re.finditer(r"\(rule \"([^\"]+)\"(.*?)\n\n", dru + '\n\n', re.S):
        txt = m.group(2)
        a = re.search(r"enclosedByArea\('([^']+)'\)", txt)
        n = re.search(r"NetName == '([^']+)'", txt)
        if a:
            want[a.group(1)] = n.group(1) if n else None
    if not want:
        print('  corridors               0 declared   OK')
        return
    b = pcbnew.LoadBoard(PCB)
    zones = {}
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetZoneName():
            zones[z.GetZoneName()] = z
    bad = 0
    for name, net in sorted(want.items()):
        z = zones.get(name)
        if z is None:
            failures.append('corridor missing: %r' % name)
            print('      MISSING CORRIDOR: %r' % name)
            bad += 1
            continue
        o = z.Outline()
        verts = sum(o.Outline(i).PointCount() for i in range(o.OutlineCount()))
        bb = z.GetBoundingBox()
        box = (bb.GetWidth() / 1e6) * (bb.GetHeight() / 1e6)
        area = o.Area() / 1e12
        fill = area / box if box else 1.0
        if box > CORRIDOR_BOX_EXEMPT_MM2 and (verts <= 4 or fill < CORRIDOR_MIN_FILL):
            failures.append('corridor %r is a bounding box (%.1f x %.1f mm, '
                            'fill %.2f, %d vertices)'
                            % (name, bb.GetWidth() / 1e6, bb.GetHeight() / 1e6,
                               fill, verts))
            print('      BOUNDING BOX: %-24s %.1f x %.1f mm  fill %.2f  %d vertices'
                  % (name, bb.GetWidth() / 1e6, bb.GetHeight() / 1e6, fill, verts))
            bad += 1
            continue
        # C4: nothing foreign may sit inside the corridor
        foreign = set()
        for t in b.GetTracks():
            if t.GetClass() != 'PCB_TRACK' or not net:
                continue
            if t.GetNetname() == net:
                continue
            if o.Collide(t.GetStart()) or o.Collide(t.GetEnd()):
                foreign.add(t.GetNetname() or '<none>')
        if foreign:
            failures.append('corridor %r admits foreign nets: %s'
                            % (name, ', '.join(sorted(foreign))))
            print('      FOREIGN IN CORRIDOR: %-20s %s'
                  % (name, ', '.join(sorted(foreign))))
            bad += 1
    print('  %-22s %3d declared, %d bad   %s'
          % ('corridors', len(want), bad, 'FAIL' if bad else 'OK'))


def main():
    dru, pcb, pro = load()
    body = strip_comments(dru)
    failures = []

    rules = re.findall(r'^\(rule "([^"]+)"', dru, re.M)
    dupes = sorted(r for r in set(rules) if rules.count(r) > 1)
    print('AQROOT Full Beta v2 -- .kicad_dru reference probe')
    print('  rules: %d, duplicate names: %d' % (len(rules), len(dupes)))
    for d in dupes:
        failures.append('duplicate rule name: %r' % d)
        print('      DUPLICATE: %r' % d)

    check('rule areas', set(re.findall(r"(?:intersectsArea|enclosedByArea)\('([^']+)'\)", body)),
          board_areas(pcb), failures)
    check('footprint refs', set(re.findall(r"memberOfFootprint\('([^']+)'\)", body)),
          board_refs(pcb), failures)
    check('courtyard refs', set(re.findall(r"intersectsCourtyard\('([^']+)'\)", body)),
          board_refs(pcb), failures)
    check('netclasses', set(re.findall(r"hasNetclass\('([^']+)'\)", body)),
          {c['name'] for c in pro['net_settings']['classes']}, failures)
    check('net names', set(re.findall(r"NetName == '([^']+)'", body)),
          board_nets(pcb), failures)

    # Netclass patterns that capture nothing.  KiCad applies every matching
    # pattern in order and the LAST one wins, so resolution is done the same way.
    nets = sorted(board_nets(pcb))
    pats = []
    for q in pro['net_settings']['netclass_patterns']:
        rx = '^' + re.escape(q['pattern']).replace(r'\*', '.*').replace(r'\?', '.') + '$'
        pats.append((re.compile(rx), q['netclass'], q['pattern']))
    used = set()
    resolved = {}
    for n in nets:
        cls = 'Default'
        for rx, c, p in pats:
            if rx.match(n):
                cls = c
                used.add(p)
        resolved[n] = cls
    dead = [p for _, _, p in pats if p not in used]
    print('  %-22s %3d patterns, %d match nothing   %s'
          % ('netclass patterns', len(pats), len(dead), 'FAIL' if dead else 'OK'))
    for p in dead:
        print('      MATCHES NOTHING: %r' % p)
        failures.append('netclass pattern matches nothing: %r' % p)

    # Declared classes that end up carrying no net are dead weight, not a defect.
    empty = sorted({c['name'] for c in pro['net_settings']['classes']}
                   - set(resolved.values()) - {'Default'})
    if empty:
        print('  note: netclasses carrying no net: %s' % ', '.join(empty))

    print('  %d board nets, %d classified, %d on Default'
          % (len(nets), sum(1 for v in resolved.values() if v != 'Default'),
             sum(1 for v in resolved.values() if v == 'Default')))

    corridor_checks(failures)

    if failures:
        print('DRU PROBE: FAIL (%d)' % len(failures))
        return 1
    print('DRU PROBE: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
