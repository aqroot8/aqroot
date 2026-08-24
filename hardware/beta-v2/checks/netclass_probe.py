"""Full Beta v2 netclass regression probe.

Run:  python hardware/beta-v2/checks/netclass_probe.py

Asserts that the LED_BOOST netclass captures the six display backlight nets
and NOTHING else.  It exists because the original patterns were written with a
leading wildcard -- `*LED_K` -- which silently also captured `/07_IR/IR_LED_K`,
the infrared transmitter's LED cathode, and gave an unrelated net the elevated
0.30 mm backlight routing clearance.

Exit code 0 = pass, 1 = fail.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRO = os.path.join(HERE, '..', 'kicad', 'aqroot-beta-v2', 'aqroot-Beta-v2.kicad_pro')
PCB = os.path.join(HERE, '..', 'kicad', 'aqroot-beta-v2', 'aqroot-Beta-v2.kicad_pcb')

# UPDATED AT FBV2-P1-001.  Until P1 the PCB was still the inherited Beta-DM board,
# whose backlight carried FOUR separate anode nets LED_A1..LED_A4.  The Full Beta v2
# schematic captured at FBV2-S1-003 has ONE anode net -- `/03_SPI_A_DISPLAY_SD/LED_A`,
# the net D-111/FBV2-S1-003 deliberately added to the LED_BOOST class -- feeding the
# four 33 R ballast resistors R70..R73 in parallel.  The expectation therefore had to
# follow the schematic once the P1 board was rebuilt from it.  THE GUARD ITSELF IS
# UNCHANGED: LED_BOOST must still never capture the infrared transmitter nets.
EXPECTED_LED_BOOST = {
    '/03_SPI_A_DISPLAY_SD/LED_BOOST',
    '/03_SPI_A_DISPLAY_SD/LED_K',
    '/03_SPI_A_DISPLAY_SD/LED_A',
}
MUST_NOT_MATCH = {'/07_IR/IR_LED_K', '/07_IR/IR_LED_A'}


def netclass_patterns(pro_path):
    d = json.load(open(pro_path, encoding='utf-8'))
    out = []
    for q in d['net_settings']['netclass_patterns']:
        rx = '^' + re.escape(q['pattern']).replace(r'\*', '.*').replace(r'\?', '.') + '$'
        out.append((re.compile(rx), q['netclass'], q['pattern']))
    return out


def resolve(pats, name):
    """KiCad applies every matching pattern in order; the last one wins."""
    cls = 'Default'
    for rx, c, _p in pats:
        if rx.match(name):
            cls = c
    return cls


def board_nets(pcb_path):
    txt = open(pcb_path, 'rb').read().decode('utf-8')
    # KiCad 10 writes (net "NAME") on pads, tracks, vias and zones
    return sorted(set(m.group(1) for m in re.finditer(r'\(net "([^"]*)"\)', txt)))


def main():
    pats = netclass_patterns(PRO)
    nets = board_nets(PCB)
    if not nets:
        print('FAIL: no nets found in %s' % PCB)
        return 1
    got = set(n for n in nets if resolve(pats, n) == 'LED_BOOST')
    fails = []
    extra = got - EXPECTED_LED_BOOST
    missing = EXPECTED_LED_BOOST - got
    if extra:
        fails.append('LED_BOOST over-captures: %s' % ', '.join(sorted(extra)))
    if missing:
        fails.append('LED_BOOST fails to capture: %s' % ', '.join(sorted(missing)))
    for n in MUST_NOT_MATCH:
        if n not in nets:
            continue
        c = resolve(pats, n)
        if c == 'LED_BOOST':
            fails.append('%s resolves to LED_BOOST' % n)
        else:
            print('  %-32s -> %-10s  (must not be LED_BOOST)  OK' % (n, c))
    for n in sorted(EXPECTED_LED_BOOST):
        print('  %-32s -> %-10s  OK' % (n, resolve(pats, n)))
    print('  %d board nets scanned, %d resolve to LED_BOOST' % (len(nets), len(got)))
    if fails:
        for f in fails:
            print('FAIL: %s' % f)
        return 1
    print('NETCLASS PROBE: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
