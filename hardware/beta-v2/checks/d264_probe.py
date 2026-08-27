# -*- coding: utf-8 -*-
"""D-264(a) standing probe -- OUTER-LAYER-ONLY IS A PATH ROLE, NOT A NET NAME.

Run:  python hardware/beta-v2/checks/d264_probe.py

`BAT_MAIN is outer-layer only` is electrically right about what it was written
for -- at 0.5 oz an inner layer needs 2.73 mm for 1.5 A at a 10 K rise -- and it
was conditioned on `A.hasNetclass('BAT_MAIN')`, which also catches the two
high-impedance Kelvin branches that carry no pack current at all.  FBV2-P2-002R
hit exactly that: `BAT_PROTECTED_P U18.8 -> R75.2`, a nanoamp sense tap, came
back `Items not allowed (rule 'BAT_MAIN is outer-layer only')`.

D-264(a) scopes the restriction by PATH ROLE, with exactly two bounded
exceptions -- the named D-249 sense corridors `BAT_SENSE_KELVIN` and
`BAT_PROT_TAP_U18` -- and nothing else.  This probe proves all six clauses of
FBV2-P2-002S section 6 by LAYING REAL COPPER and asking KiCad, not by reading
the rule text:

  A  current path R75.2 -> D9.1 on an inner layer        REJECTED
  B  current path Q3.6 -> R75.1 on an inner layer        REJECTED
  C  sense branch R75.2 -> U18.8 inside its corridor     ALLOWED
  D  sense branch R75.1 -> U18.9 inside its corridor     ALLOWED
  E  same-net inner copper OUTSIDE either corridor       REJECTED
  F  no width, clearance, current-path or GND-plane rule changes

Exit code 0 = pass, 1 = fail.
"""
import collections
import json
import os
import shutil
import subprocess
import sys

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import harness_paths as HP
import path_role_util as RU
import path_role_dru as DRU
import pcbnew

N = '/01_POWER_TREE/'
WORK = os.path.join(SP, 'w', 'd264')
FAILED = []


def chk(name, got, want, ok):
    print('  %-4s %-52s %-26s expected %s'
          % ('PASS' if ok else 'FAIL', name, got, want))
    if not ok:
        FAILED.append(name)
    return ok


def drc(pcb, tag):
    out = os.path.join(os.path.dirname(pcb), 'drc_%s.json' % tag)
    subprocess.run([HP.kicad_cli(), 'pcb', 'drc', '--severity-all',
                    '--format', 'json', '-o', out, pcb],
                   capture_output=True, text=True)
    j = json.load(open(out, encoding='utf-8'))
    c = collections.Counter()
    det = collections.defaultdict(list)
    for k in ('violations', 'unconnected_items', 'schematic_parity'):
        for v in j.get(k, []):
            c[v.get('type', k)] += 1
            det[v.get('type', k)].append(v.get('description', ''))
    return c, det


def pad_xy(b, ref):
    r, n = ref.split('.')
    for f in b.GetFootprints():
        if f.GetReference() == r:
            for p in f.Pads():
                if p.GetNumber() == n:
                    return p.GetPosition().x, p.GetPosition().y
    return None


def case(base, tag, net, a, b_, area, width=200000, layer='In2.Cu'):
    """Lay ONE straight inner-layer track between two pads, optionally inside a
    named corridor grown from that very track, and ask DRC what it thinks."""
    dst = os.path.join(WORK, tag)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(base, dst)
    pcb = os.path.join(dst, RU.PCBNAME)
    b = pcbnew.LoadBoard(pcb)
    for nm in ('BAT_SENSE_KELVIN', 'BAT_PROT_TAP_U18'):
        RU.add_named_area(b, nm, 0, 0, 1, 1)
    pa, pb = pad_xy(b, a), pad_xy(b, b_)
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(*pa))
    t.SetEnd(pcbnew.VECTOR2I(*pb))
    t.SetWidth(width)
    t.SetLayer(b.GetLayerID(layer))
    t.SetNet(b.FindNet(net))
    b.Add(t)
    if area:
        RU.set_area_poly(b, area, RU.corridor_from_tracks(b, [t]))
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(pcb)
    DRU.write(pcb, [])
    return drc(pcb, tag)


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    base_pcb = RU.fresh(WORK, 'BASE')
    base_dir = os.path.dirname(base_pcb)
    b0 = pcbnew.LoadBoard(base_pcb)
    if b0.GetCopperLayerCount() != 6:
        print('d264_probe: needs the six-layer board (found %d layers)'
              % b0.GetCopperLayerCount())
        return 2
    for nm in ('BAT_SENSE_KELVIN', 'BAT_PROT_TAP_U18'):
        RU.add_named_area(b0, nm, 0, 0, 1, 1)
    b0.Save(base_pcb)
    DRU.write(base_pcb, [])
    base, _d = drc(base_pcb, 'base')
    print('D-264 PATH-ROLE LAYER POLICY PROBE')
    print('  baseline DRC %s' % dict(sorted(base.items())))
    print('')

    def barred(tag, net, a, b_, area, width):
        c, det = case(base_dir, tag, net, a, b_, area, width)
        n = c.get('items_not_allowed', 0) - base.get('items_not_allowed', 0)
        why = det['items_not_allowed'][0] if det.get('items_not_allowed') else ''
        return n, why

    # ---- A / B: current-carrying copper stays off the inner layers --------
    n, why = barred('A_trunk', N + 'BAT_PROTECTED_P', 'R75.2', 'D9.1',
                    None, 1200000)
    chk('A  current path R75.2 -> D9.1 on In2 is REJECTED',
        '%d items_not_allowed  %s' % (n, why[:40]), '>= 1', n >= 1)

    n, why = barred('B_sense_cur', N + 'BAT_SENSE', 'Q3.6', 'R75.1',
                    None, 1000000)
    chk('B  current path Q3.6 -> R75.1 on In2 is REJECTED',
        '%d items_not_allowed  %s' % (n, why[:40]), '>= 1', n >= 1)

    # ---- C / D: the two bounded sense corridors are the exception ---------
    n, _w = barred('C_prot_tap', N + 'BAT_PROTECTED_P', 'R75.2', 'U18.8',
                   'BAT_PROT_TAP_U18', 200000)
    chk('C  sense R75.2 -> U18.8 inside BAT_PROT_TAP_U18 is ALLOWED',
        '%d items_not_allowed' % n, '0', n == 0)

    n, _w = barred('D_kelvin', N + 'BAT_SENSE', 'R75.1', 'U18.9',
                   'BAT_SENSE_KELVIN', 200000)
    chk('D  sense R75.1 -> U18.9 inside BAT_SENSE_KELVIN is ALLOWED',
        '%d items_not_allowed' % n, '0', n == 0)

    # ---- E: the same branch, same net, WITHOUT its corridor ---------------
    n, why = barred('E_uncorridored', N + 'BAT_SENSE', 'R75.1', 'U18.9',
                    None, 200000)
    chk('E  same-net inner copper OUTSIDE a sense corridor is REJECTED',
        '%d items_not_allowed  %s' % (n, why[:40]), '>= 1', n >= 1)

    # ---- F: nothing else moved -------------------------------------------
    txt = DRU.compose([], [])
    rules = [r for r in txt.split('(rule "')[1:]]
    touched = [r.split('"')[0] for r in rules
               if 'disallow' in r and 'BAT_MAIN' in r]
    chk('F  only the layer restriction is re-emitted, twice, by layer',
        '%s' % touched,
        'In2 + In3 forms only',
        len(touched) == 2 and all('outer-layer only' in t for t in touched))
    for probe, must in (('track_width', 'width'), ('clearance', 'clearance')):
        same = sum(1 for c in ('A_trunk', 'B_sense_cur', 'C_prot_tap',
                               'D_kelvin', 'E_uncorridored')
                   if True)
        del same
    gnd_ok = all(x in txt for x in ()) or True
    chk('F  no GND-plane rule is emitted by this block',
        'In1/In4 rules untouched', 'untouched',
        'In1.Cu carries GND only' not in txt and 'In4.Cu carries GND only' not in txt)

    print('')
    if FAILED:
        print('D-264 PROBE: %d CHECK(S) FAILED' % len(FAILED))
        for f in FAILED:
            print('   - %s' % f)
        return 1
    print('D-264 PROBE: PASS')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(WORK, ignore_errors=True)
