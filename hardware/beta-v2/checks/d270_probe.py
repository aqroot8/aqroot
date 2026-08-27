# -*- coding: utf-8 -*-
"""D-270(a) standing probe -- WESTERN-MARGIN OFFLOAD IS A PATH ROLE.

Run:  python hardware/beta-v2/checks/d270_probe.py

D-264 barred In2/In3 for every BAT_MAIN-class track because distributing 1.5 A
of pack current on 0.5 oz inner copper needs 2.73 mm.  That is right for a
CURRENT-CARRYING role and stays in force.  D-270 adds, by INDIVIDUAL BRANCH, the
same bounded exception D-264 gave the two Kelvin sense corridors: a microamp
BAT_RAW divider bridge, authorised for offload and inside its own D-249/D-269
corridor, may take the inner layer despite sharing the BAT_RAW net name - while
the trunk and every other current-carrying role may not.

This proves the ruling by LAYING REAL COPPER on the six-layer board and asking
KiCad, not by reading the rule text.  With the D-270 offload corridors in force
(BAT_RAW_DIVIDER_TAP_0 / _3):

  A  BAT_RAW bridge R80.1 -> Q2.7 on In2, inside TAP_0      ALLOWED
  B  the same bridge on In3, inside TAP_0                   ALLOWED
  C  the same BAT_RAW copper on In2 with NO corridor        REJECTED
  D  current path R75.2 -> D9.1 (trunk) on In2              REJECTED
  E  current path Q3.6 -> R75.1 (BAT_SENSE) on In2          REJECTED
  F  BAT_RAW bridge on In2 inside TAP_0 but WITHOUT the
     D-270 authorisation (INNER_OFFLOAD_AREAS empty)        REJECTED
  G  the two D-264 sense corridors still ALLOWED (no regression)
  H  only the layer restriction moves: no width, clearance,
     current-path or GND-plane rule is touched

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
WORK = os.path.join(SP, 'w', 'd270')
OFFLOAD_AREAS = ('BAT_RAW_DIVIDER_TAP_0', 'BAT_RAW_DIVIDER_TAP_3')
FAILED = []


def chk(name, got, want, ok):
    print('  %-4s %-54s %-26s expected %s'
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


ALL_AREAS = ('BAT_SENSE_KELVIN', 'BAT_PROT_TAP_U18',
             'BAT_RAW_DIVIDER_TAP_0', 'BAT_RAW_DIVIDER_TAP_3')


def case(base, tag, net, a, b_, area, width=200000, layer='In2.Cu'):
    """Lay ONE straight inner-layer track between two pads, optionally inside a
    named corridor grown from that very track, and ask DRC what it thinks.
    DRU.INNER_OFFLOAD_AREAS is whatever the caller set it to."""
    dst = os.path.join(WORK, tag)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(base, dst)
    pcb = os.path.join(dst, RU.PCBNAME)
    b = pcbnew.LoadBoard(pcb)
    for nm in ALL_AREAS:
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
        print('d270_probe: needs the six-layer board (found %d layers)'
              % b0.GetCopperLayerCount())
        return 2
    for nm in ALL_AREAS:
        RU.add_named_area(b0, nm, 0, 0, 1, 1)
    b0.Save(base_pcb)
    DRU.INNER_OFFLOAD_AREAS = OFFLOAD_AREAS
    DRU.write(base_pcb, [])
    base, _d = drc(base_pcb, 'base')
    print('D-270 PATH-ROLE OFFLOAD POLICY PROBE')
    print('  offload corridors in force: %s' % ', '.join(OFFLOAD_AREAS))
    print('  baseline DRC %s' % dict(sorted(base.items())))
    print('')

    def barred(tag, net, a, b_, area, width, layer='In2.Cu'):
        c, det = case(base_dir, tag, net, a, b_, area, width, layer)
        n = c.get('items_not_allowed', 0) - base.get('items_not_allowed', 0)
        why = det['items_not_allowed'][0] if det.get('items_not_allowed') else ''
        return n, why

    # ---- A / B: the authorised BAT_RAW bridge takes the inner layer ---------
    DRU.INNER_OFFLOAD_AREAS = OFFLOAD_AREAS
    n, _w = barred('A_bridge_in2', N + 'BAT_RAW', 'R80.1', 'Q2.7',
                   'BAT_RAW_DIVIDER_TAP_0', 200000, 'In2.Cu')
    chk('A  BAT_RAW R80.1->Q2.7 on In2 inside TAP_0 is ALLOWED',
        '%d items_not_allowed' % n, '0', n == 0)

    n, _w = barred('B_bridge_in3', N + 'BAT_RAW', 'R80.1', 'Q2.7',
                   'BAT_RAW_DIVIDER_TAP_0', 200000, 'In3.Cu')
    chk('B  BAT_RAW R80.1->Q2.7 on In3 inside TAP_0 is ALLOWED',
        '%d items_not_allowed' % n, '0', n == 0)

    # ---- C: the same BAT_RAW copper with no corridor at all -----------------
    n, why = barred('C_bridge_bare', N + 'BAT_RAW', 'R80.1', 'Q2.7',
                    None, 200000, 'In2.Cu')
    chk('C  BAT_RAW bridge on In2 with NO corridor is REJECTED',
        '%d items_not_allowed  %s' % (n, why[:34]), '>= 1', n >= 1)

    # ---- D / E: current-carrying roles are NOT granted the inner layer ------
    n, why = barred('D_trunk', N + 'BAT_PROTECTED_P', 'R75.2', 'D9.1',
                    None, 1200000, 'In2.Cu')
    chk('D  current path R75.2 -> D9.1 on In2 is REJECTED',
        '%d items_not_allowed  %s' % (n, why[:34]), '>= 1', n >= 1)

    n, why = barred('E_sense_cur', N + 'BAT_SENSE', 'Q3.6', 'R75.1',
                    None, 1000000, 'In2.Cu')
    chk('E  current path Q3.6 -> R75.1 on In2 is REJECTED',
        '%d items_not_allowed  %s' % (n, why[:34]), '>= 1', n >= 1)

    # ---- F: WITHOUT the D-270 authorisation, TAP_0 is not enough ------------
    DRU.INNER_OFFLOAD_AREAS = ()
    n, why = barred('F_unauthorised', N + 'BAT_RAW', 'R80.1', 'Q2.7',
                    'BAT_RAW_DIVIDER_TAP_0', 200000, 'In2.Cu')
    chk('F  BAT_RAW bridge in TAP_0 WITHOUT D-270 is REJECTED',
        '%d items_not_allowed  %s' % (n, why[:34]), '>= 1', n >= 1)
    DRU.INNER_OFFLOAD_AREAS = OFFLOAD_AREAS

    # ---- G: the two D-264 sense corridors are unregressed -------------------
    n, _w = barred('G_prot_tap', N + 'BAT_PROTECTED_P', 'R75.2', 'U18.8',
                   'BAT_PROT_TAP_U18', 200000, 'In2.Cu')
    chk('G  D-264 sense R75.2 -> U18.8 inside its corridor still ALLOWED',
        '%d items_not_allowed' % n, '0', n == 0)

    # ---- H: nothing else moved ---------------------------------------------
    DRU.INNER_OFFLOAD_AREAS = OFFLOAD_AREAS
    txt = DRU.compose([], [])
    rules = txt.split('(rule "')[1:]
    disallow = [r.split('"')[0] for r in rules
                if 'disallow' in r and 'BAT_MAIN' in r]
    chk('H  only the layer restriction is re-emitted, twice, by layer',
        '%s' % disallow,
        'In2 + In3 forms only',
        len(disallow) == 2 and all('outer-layer only' in t for t in disallow))
    both_corr = all(('%s' % a) in txt for a in OFFLOAD_AREAS)
    chk('H  each offload corridor named in BOTH inner-layer forms',
        'TAP_0 and TAP_3 present' if both_corr else 'missing',
        'present', both_corr)
    chk('H  no GND-plane rule is emitted by this block',
        'In1/In4 rules untouched', 'untouched',
        'In1.Cu carries GND only' not in txt
        and 'In4.Cu carries GND only' not in txt)
    # D-270 changes ONLY the two disallow conditions; the disallow rule count is
    # still exactly two, so no new width/clearance/via rule was invented by it.
    off = DRU.INNER_OFFLOAD_AREAS
    DRU.INNER_OFFLOAD_AREAS = ()
    txt0 = DRU.compose([], [])
    DRU.INNER_OFFLOAD_AREAS = off
    same_but_cond = (txt0.count('(rule "') == txt.count('(rule "')
                     and txt0.count('disallow') == txt.count('disallow')
                     and txt0.count('track_width') == txt.count('track_width')
                     and txt0.count('clearance') == txt.count('clearance'))
    chk('H  D-270 adds only exclusion terms, no new rule of any kind',
        'rule/width/clearance counts unchanged', 'unchanged', same_but_cond)

    print('')
    if FAILED:
        print('D-270 PROBE: %d CHECK(S) FAILED' % len(FAILED))
        for f in FAILED:
            print('   - %s' % f)
        return 1
    print('D-270 PROBE: PASS')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(WORK, ignore_errors=True)
