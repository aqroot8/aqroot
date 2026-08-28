# -*- coding: utf-8 -*-
"""D-275 standing probe -- THE WESTERN-CORRIDOR VACATE + F.Cu BRIDGE, BY PATH ROLE.

D-275 closes the BAT_PROTECTED_P western trunk that D-270..D-274 could not: the
MINIMUM vacate set is cardinality 1 -- one LOW-CURRENT control branch
(BAT_PROT_SHDN_CTL) is moved off F.Cu to In3, which opens a >= 1.20 mm (1.40 mm
achieved) F.Cu corridor from R75.2 to the eastern BPP node, and a 4-via / F.Cu /
4-via bridge carries the pack current across it.  This probe pins the mechanism's
contracts by REAL COPPER + DRC and by the recorded gate result, and REJECTS the
overbroad / current-carrying-inner-layer forms the mechanism must forbid:

  A  the VACATED net BAT_PROT_SHDN_CTL (a control signal) on In3      ALLOWED
  B  the high-current trunk BAT_PROTECTED_P on In2                    REJECTED
  C  the high-current trunk BAT_PROTECTED_P on In3                    REJECTED
  D  a current-carrying role is never a vacate candidate (classifier) REJECTED
  E  a control role IS a vacate candidate (classifier)                candidate
  F  the proven bridge board closes bit 8 with no new DRC, no regress GATE PASS

Via-array sizing (single / 2-via rejected, >= 3 floor) is pinned by
via_array_probe; corridor geometry (overbroad / foreign-net) by dru_probe.
Exit code 0 = pass, 1 = fail.
"""
import collections, json, os, shutil, subprocess, sys
SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import harness_paths as HP
import path_role_util as RU
import path_role_dru as DRU
import pcbnew
import fcu_cutset_003c as CS

N = '/01_POWER_TREE/'
WORK = os.path.join(SP, 'w', 'd275')
FAILED = []


def chk(name, got, want, ok):
    print('  %-4s %-56s %-24s expected %s'
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
    for k in ('violations', 'unconnected_items', 'schematic_parity'):
        for v in j.get(k, []):
            c[v.get('type', k)] += 1
    return c


def pad_xy(b, ref):
    r, n = ref.split('.')
    for f in b.GetFootprints():
        if f.GetReference() == r:
            for p in f.Pads():
                if p.GetNumber() == n:
                    return p.GetPosition().x, p.GetPosition().y
    return None


def lay_inner(base_dir, tag, net, a, b_, layer, width):
    """Lay one inner-layer track between two pads and ask DRC."""
    dst = os.path.join(WORK, tag)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(base_dir, dst)
    pcb = os.path.join(dst, RU.PCBNAME)
    b = pcbnew.LoadBoard(pcb)
    pa, pb = pad_xy(b, a), pad_xy(b, b_)
    if pa is None or pb is None:
        return None
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(*pa)); t.SetEnd(pcbnew.VECTOR2I(*pb))
    t.SetWidth(width); t.SetLayer(b.GetLayerID(layer))
    t.SetNet(b.FindNet(net))
    b.Add(t)
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
        print('bridge_probe_003c: needs the six-layer board (%d found)'
              % b0.GetCopperLayerCount())
        return 2
    b0.Save(base_pcb)
    DRU.write(base_pcb, [])
    base = drc(base_pcb, 'base')
    print('D-275 VACATE + F.Cu BRIDGE PATH-ROLE PROBE')
    print('  baseline DRC %s\n' % dict(sorted(base.items())))

    def barred(tag, net, a, b_, layer, width):
        c = lay_inner(base_dir, tag, net, a, b_, layer, width)
        if c is None:
            return -1
        return c.get('items_not_allowed', 0) - base.get('items_not_allowed', 0)

    # A -- the VACATED control net on In3 is ALLOWED (not BAT_MAIN class) -----
    n = barred('A_shdn_in3', N + 'BAT_PROT_SHDN_CTL', 'Q4.1', 'R83.1',
               'In3.Cu', 150000)
    chk('A  vacated BAT_PROT_SHDN_CTL on In3 is ALLOWED',
        '%d items_not_allowed' % n, '0', n == 0)

    # B / C -- the high-current trunk on an inner layer is REJECTED ----------
    nb = barred('B_trunk_in2', N + 'BAT_PROTECTED_P', 'R75.2', 'D9.1',
                'In2.Cu', 1400000)
    chk('B  trunk BAT_PROTECTED_P on In2 is REJECTED',
        '%d items_not_allowed' % nb, '>= 1', nb >= 1)
    nc = barred('C_trunk_in3', N + 'BAT_PROTECTED_P', 'R75.2', 'D9.1',
                'In3.Cu', 1400000)
    chk('C  trunk BAT_PROTECTED_P on In3 is REJECTED',
        '%d items_not_allowed' % nc, '>= 1', nc >= 1)

    # D / E -- the vacate CLASSIFIER refuses current-carrying, admits control -
    cur = CS.branch_role(N + 'BAT_SENSE', {'Q3.6', 'R75.1'})[0]
    chk('D  current-carrying BAT_SENSE is NOT a vacate candidate',
        '%s' % cur, 'None', cur is None)
    for badnet in ('BAT_PROTECTED_P', 'BAT_MID', 'BAT_CONNECTOR_P'):
        v = CS.branch_role(N + badnet, {'X.1', 'Y.1'})[0]
        chk('D  current-carrying %s is NOT a vacate candidate' % badnet,
            '%s' % v, 'None', v is None)
    ctl = CS.branch_role(N + 'BAT_PROT_SHDN_CTL', {'Q4.1', 'R83.1'})[0]
    chk('E  control BAT_PROT_SHDN_CTL IS a vacate candidate',
        '%s' % ctl, 'candidate', ctl == 'candidate')

    # F -- the recorded real-copper gate result closes bit 8, no new DRC -----
    gp = os.path.join(SP, 'place_002z', 'bridge_gates_003c.json')
    if os.path.exists(gp):
        g = json.load(open(gp))
        v = g.get('verdict', {})
        chk('F  bridge board closes bit 8 (R75.2->U11.2)',
            '%s' % v.get('bit8_closed'), 'True', bool(v.get('bit8_closed')))
        chk('F  bridge board: all 9 PR-40 targets true',
            '%s' % v.get('all9_targets'), 'True', bool(v.get('all9_targets')))
        chk('F  bridge board: U18 8/8',
            '%s' % v.get('u18_8of8'), 'True', bool(v.get('u18_8of8')))
        chk('F  bridge board: no new DRC vs baseline',
            '%s' % v.get('no_new_drc'), 'True', bool(v.get('no_new_drc')))
        chk('F  bridge board: no connectivity regression',
            '%s' % (v.get('control_not_regressed') and
                    v.get('targets_not_regressed')), 'True',
            bool(v.get('control_not_regressed') and v.get('targets_not_regressed')))
    else:
        chk('F  bridge gate record present', 'missing', 'present', False)

    shutil.rmtree(WORK, ignore_errors=True)
    print('\nD-275 BRIDGE PROBE:', 'PASS' if not FAILED else 'FAIL %s' % FAILED)
    return 0 if not FAILED else 1


if __name__ == '__main__':
    raise SystemExit(main())
