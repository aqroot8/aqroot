# -*- coding: utf-8 -*-
"""D-269(a) standing probe -- CLEARANCE IS A PATH ROLE, NOT A NET NAME.

Run:  python hardware/beta-v2/checks/d269_probe.py

`BAT_MAIN routed clearance` is electrically right about what it was written for
-- 0.300 mm between conductors carrying 1.5 A of pack current -- and it was
conditioned on `A.hasNetclass('BAT_MAIN')`, which also catches the D-249 microamp
divider taps that carry nanoamps.  FBV2-P2-002T through 002V hit exactly that:
`BAT_RAW R77.1 -> R79.1`, two 0.20 mm taps, rejected with
`Clearance violation (rule 'BAT_MAIN routed clearance')`.

Clearance is the FOURTH and last property to get the treatment D-249 gave width,
D-264 gave layer and D-267 gave via geometry.  This probe proves all six clauses
of FBV2-P2-002W section 5 by LAYING REAL COPPER and asking KiCad, not by reading
the rule text:

  A  BAT_RAW current trunk copper outside the corridor    0.300 mm REQUIRED
  B  BAT_SENSE current path outside the corridor          0.300 mm REQUIRED
  C  R77.1 -> R79.1 TAP inside its corridor               NOT forced to 0.300
  D  R79.1 -> R80.1 TAP inside its corridor               NOT forced to 0.300
  E  same-net copper only PARTLY inside the corridor      0.300 mm REQUIRED
  F  no width, layer, via or hole rule changed

Exit code 0 = pass, 1 = fail.
"""
import collections, json, os, shutil, subprocess, sys, io

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import harness_paths as HP
import path_role_util as RU
import path_role_dru as DRU
import pcbnew

N = '/01_POWER_TREE/'
WORK = os.path.join(SP, 'w', 'd269')
AREA = 'BAT_RAW_DIVIDER_TAP_0'
GAP = 250000        # 0.25 mm edge-to-edge: under the 0.300 rule, over the 0.200 board default
W = 200000
FAILED = []


def chk(name, got, want, ok):
    print('  %-4s %-54s %-24s expected %s'
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
    c, det = collections.Counter(), collections.defaultdict(list)
    for k in ('violations', 'unconnected_items', 'schematic_parity'):
        for v in j.get(k, []):
            c[v.get('type', k)] += 1
            det[v.get('type', k)].append(v.get('description', ''))
    return c, det


def case(base, tag, nets, inside):
    """Two parallel 0.20 mm tracks 0.25 mm apart in empty board space, on TWO
    DIFFERENT BAT_MAIN-class nets - clearance is a between-nets rule and two
    same-net tracks have no spacing requirement at all, which is why the first
    version of this probe reported zero violations everywhere.  `inside` says
    how many of them the bounded TAP corridor is grown around: 2 = the whole
    branch, 1 = only half of it, 0 = no corridor at all."""
    dst = os.path.join(WORK, tag)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(base, dst)
    pcb = os.path.join(dst, RU.PCBNAME)
    b = pcbnew.LoadBoard(pcb)
    RU.add_named_area(b, AREA, 0, 0, 1, 1)
    x0, y0 = 30000000, 100000000
    pitch = W + GAP
    ts = []
    for k in (0, 1):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(x0, y0 + k * pitch))
        t.SetEnd(pcbnew.VECTOR2I(x0 + 6000000, y0 + k * pitch))
        t.SetWidth(W)
        t.SetLayer(b.GetLayerID('B.Cu'))
        t.SetNet(b.FindNet(nets[k]))
        b.Add(t)
        ts.append(t)
    if inside:
        ps = RU.corridor_from_tracks(b, ts[:inside])
        if inside == 2:
            # ONE polygon, not two.  `enclosedByArea` honours only the FIRST
            # outline of a multi-outline rule area - the fact D-266 learned the
            # hard way - and two capsules 0.25 mm apart with a 0.10 mm tolerance
            # do not merge on their own.  A real divider TAP corridor is grown
            # from CONTIGUOUS copper and is one polygon by construction, so
            # bridging the two here is what makes the probe represent the board
            # rather than an artefact of the probe's own geometry.
            ps.BooleanAdd(RU.capsule(ts[0].GetStart().x + 3000000,
                                     ts[0].GetStart().y,
                                     ts[1].GetStart().x + 3000000,
                                     ts[1].GetStart().y, W))
            ps.Simplify()
        RU.set_area_poly(b, AREA, ps)
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
        print('d269_probe: needs the six-layer board (found %d)'
              % b0.GetCopperLayerCount())
        return 2
    RU.add_named_area(b0, AREA, 0, 0, 1, 1)
    b0.Save(base_pcb)
    DRU.write(base_pcb, [])
    base, _ = drc(base_pcb, 'base')
    print('D-269 PATH-ROLE CLEARANCE PROBE   (test gap %.3f mm, tracks %.2f mm)'
          % (GAP / 1e6, W / 1e6))
    print('  baseline DRC %s' % dict(sorted(base.items())))
    print('')

    def clr(tag, nets, inside):
        c, det = case(base_dir, tag, nets, inside)
        n = c.get('clearance', 0) - base.get('clearance', 0)
        why = det['clearance'][0] if det.get('clearance') else ''
        return n, why

    n, why = clr('A_raw_trunk', (N + 'BAT_RAW', N + 'BAT_PROTECTED_P'), 0)
    chk('A  BAT_RAW copper outside the corridor still needs 0.300 mm',
        '%d clearance  %s' % (n, why[:38]), '>= 1', n >= 1)

    n, why = clr('B_sense_cur', (N + 'BAT_SENSE', N + 'BAT_MID'), 0)
    chk('B  BAT_SENSE current path still needs 0.300 mm',
        '%d clearance  %s' % (n, why[:38]), '>= 1', n >= 1)

    n, why = clr('C_tap_7779', (N + 'BAT_RAW', N + 'BAT_PROTECTED_P'), 2)
    chk('C  BAT_RAW TAP inside %s is NOT forced to 0.300 mm' % AREA,
        '%d clearance' % n, '0', n == 0)

    n, why = clr('D_tap_7980', (N + 'BAT_RAW', N + 'BAT_MID'), 2)
    chk('D  the second TAP pair gets the same path-role treatment',
        '%d clearance' % n, '0', n == 0)

    n, why = clr('E_half_in', (N + 'BAT_RAW', N + 'BAT_PROTECTED_P'), 1)
    chk('E  copper only PARTLY inside the corridor still needs 0.300 mm',
        '%d clearance  %s' % (n, why[:38]), '>= 1', n >= 1)

    # ---- F: nothing else moved ------------------------------------------
    src = io.open(os.path.join(SP, 'path_role_dru.py'), encoding='utf-8').read()
    chk('F  the exclusion names one bounded corridor per TAP branch',
        '%d corridor(s): %s' % (len(DRU.TAP_CLEARANCE_AREAS),
                                ', '.join(DRU.TAP_CLEARANCE_AREAS)),
        'one per divider branch',
        len(DRU.TAP_CLEARANCE_AREAS) == 4 and AREA in DRU.TAP_CLEARANCE_AREAS)
    chk('F  the current-path requirement is still 0.30 mm',
        'min 0.30mm in the scoped rule', 'unchanged',
        '(constraint clearance (min 0.30mm))' in ''.join(
            DRU.main_clearance_rules()))
    chk('F  D-264 layer scoping unchanged',
        '%s' % (DRU.INNER_SENSE_AREAS,), 'two sense corridors',
        DRU.INNER_SENSE_AREAS == ('BAT_SENSE_KELVIN', 'BAT_PROT_TAP_U18'))
    chk('F  no width, via or hole rule text changed by D-269',
        'D-269 emits clearance only',
        'clearance only',
        'D-269' in src
        and 'via_diameter' not in ''.join(DRU.main_clearance_rules())
        and 'hole_size' not in ''.join(DRU.main_clearance_rules())
        and 'track_width' not in ''.join(DRU.main_clearance_rules()))

    print('=' * 92)
    if FAILED:
        print('D-269 PROBE: FAIL (%d)' % len(FAILED))
        for f in FAILED:
            print('   %s' % f)
        return 1
    print('D-269 PROBE: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
