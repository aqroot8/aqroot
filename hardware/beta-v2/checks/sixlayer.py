# -*- coding: utf-8 -*-
"""FBV2-P2-002M / D-258 -- the SIX-LAYER migration, applied to a board.

D-258 moves Full Beta v2 from four copper layers to six, on JLCPCB's
JLC06161H-7628 1.6 mm impedance-control stackup: 1 oz outer, 0.5 oz inner,
NO HDI, NO blind, buried or laser microvias.  Filled-and-capped ordinary
THROUGH via-in-pad (POFV) is approved only where explicitly ruled.

WHY SIX RATHER THAN A PREMIUM 4-LAYER PROCESS.  FBV2-P2-002L closed D-256 and
PR-47 with measurements rather than argument: the west margin is short of layer
capacity, D-257's 0.35/0.20 ordinary through via IS reachable at U18 and closes
that half, and `Q3.3` cannot emit legal copper in ANY direction at ANY legal
width, so no external via can rescue it whatever its size.  That left exactly
two ways to route Q3: a filled/capped via inside the pad, or more layers.  The
ruling takes the layers AND keeps the POFV for Q3 alone, because six layers on
their own do NOT solve PR-47 -- `Q3.3` still has no B.Cu escape to reach an
external via from, and that was measured, not assumed.

    L1  F.Cu    components, critical/high-speed/RF, local power
    L2  In1.Cu  SOLID GND PLANE
    L3  In2.Cu  internal signals + slow power distribution
    L4  In3.Cu  internal signals + slow power distribution
    L5  In4.Cu  SOLID GND PLANE
    L6  B.Cu    components, local signals, battery/high-current copper

Neither GND plane is ever split into power islands.  High-current battery
copper stays on 1 oz OUTER copper: at 0.5 oz an inner layer needs 2.73 mm for
1.5 A at a 10 K rise, which defeats the purpose of moving it there, and that
figure is the existing .kicad_dru arithmetic, not a new claim.

STACKUP GEOMETRY.  The one figure carried over from the four-layer design is
the OUTER dielectric: 7628 prepreg, 0.2104 mm, F.Cu to In1.Cu and B.Cu to
In4.Cu -- the same geometry as JLC04161H-7628, which is what makes the outer
reference distance comparable.  The inner distribution below is DERIVED so the
stack totals 1.6 mm with 1 oz outer and 0.5 oz inner copper, and it must be
CONFIRMED against JLCPCB's published JLC06161H-7628 table before Gerbers are
ordered.  It is recorded here as a derivation, not as a quotation.
"""
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import pcbnew

CU_OUTER = 0.035          # 1 oz
CU_INNER = 0.0152         # 0.5 oz
MASK = 0.01
PP7628 = 0.2104           # one ply of 7628 prepreg
CORE = 0.2

# (kicad layer name, type, thickness, material) top to bottom
STACK = [
    ('F.SilkS', 'Top Silk Screen', None, None),
    ('F.Paste', 'Top Solder Paste', None, None),
    ('F.Mask', 'Top Solder Mask', MASK, None),
    ('F.Cu', 'copper', CU_OUTER, None),
    ('dielectric 1', 'prepreg', PP7628, '7628'),
    ('In1.Cu', 'copper', CU_INNER, None),
    ('dielectric 2', 'core', CORE, 'FR4'),
    ('In2.Cu', 'copper', CU_INNER, None),
    ('dielectric 3', 'prepreg', PP7628 * 3, '7628'),
    ('In3.Cu', 'copper', CU_INNER, None),
    ('dielectric 4', 'core', CORE, 'FR4'),
    ('In4.Cu', 'copper', CU_INNER, None),
    ('dielectric 5', 'prepreg', PP7628, '7628'),
    ('B.Cu', 'copper', CU_OUTER, None),
    ('B.Mask', 'Bottom Solder Mask', MASK, None),
    ('B.Paste', 'Bottom Solder Paste', None, None),
    ('B.SilkS', 'Bottom Silk Screen', None, None),
]

CU_LAYERS = ('F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu')
GND_PLANES = ('In1.Cu', 'In4.Cu')


def total_thickness():
    return sum(t for (_n, _ty, t, _m) in STACK if t)


def render_stackup():
    out = ['\t\t(stackup']
    for (name, ty, th, mat) in STACK:
        row = '\t\t\t(layer "%s" (type "%s")' % (name, ty)
        if mat:
            row += ' (material "%s")' % mat
        if th is not None:
            row += ' (thickness %s)' % ('%.4f' % th).rstrip('0').rstrip('.')
        if ty in ('prepreg', 'core'):
            row += ' (epsilon_r 4.4) (loss_tangent 0.02)'
        row += ')'
        out.append(row)
    out.append('\t\t\t(copper_finish "ENIG")')
    out.append('\t\t\t(dielectric_constraints no)')
    out.append('\t\t)')
    return '\n'.join(out)


DRU_MARK = '# 2b. In4.Cu IS THE SECOND GND REFERENCE PLANE  (D-258)'

DRU_BLOCK = u"""
# ---------------------------------------------------------------------
# 2b. In4.Cu IS THE SECOND GND REFERENCE PLANE  (D-258, FBV2-P2-002M)
#
# The six-layer migration adds a SECOND solid reference, and it gets the
# same rule as the first rather than a weaker one.  L2 (In1) references the
# F.Cu side, L5 (In4) references the B.Cu side, and the two new signal
# layers L3/L4 sit between them - so every internal route has a plane on
# one side and every outer route has a plane 0.2104 mm away, which is the
# geometry that made the four-layer outer reference work.
#
# Neither plane may be split into power islands.  The only authorised void
# is still the ESP32 antenna keepout of section 3, which is a manufacturer
# requirement and overrides plane continuity locally on every layer.
# ---------------------------------------------------------------------

(rule "In4.Cu carries GND only - no signal or power tracks"
	(layer "In4.Cu")
	(severity error)
	(constraint disallow track)
	(condition "A.NetName != 'GND'"))

(rule "SWITCH_NODE: outer layers only - never on In3"
	(layer "In3.Cu")
	(severity error)
	(constraint disallow track via)
	(condition "A.hasNetclass('SWITCH_NODE')"))
"""


def patch_dru(pcb, verbose=True):
    """Extend the layer rules to the six-layer stack.

    Section 5 says to EXTEND the In1 guard, not weaken it, and that is what
    this does: In1's rule is untouched, In4 gets the identical rule, and the
    `SWITCH_NODE never on In2` prohibition is repeated for In3 so the second
    new signal layer inherits the same protection as the first.  Nothing that
    already existed is relaxed.
    """
    d = os.path.join(os.path.dirname(pcb), 'aqroot-Beta-v2.kicad_dru')
    raw = open(d, 'rb').read().decode('utf-8')
    crlf = '\r\n' in raw
    t = raw.replace('\r\n', '\n')
    if DRU_MARK in t:
        return False
    anchor = '(rule "In1.Cu carries GND only - no signal or power tracks"'
    i = t.index(anchor)
    j = t.index('\n\n', t.index('(condition "A.NetName != \'GND\'"))', i))
    t = t[:j] + '\n' + DRU_BLOCK + t[j:]
    open(d, 'wb').write((t.replace('\n', '\r\n') if crlf else t).encode('utf-8'))
    if verbose:
        print('  .kicad_dru         In4 GND rule + In3 SWITCH_NODE rule added')
    return True


def convert(pcb, verbose=True):
    """Six copper layers, the explicit stackup, and the second GND plane."""
    b = pcbnew.LoadBoard(pcb)
    if b.GetCopperLayerCount() != 6:
        ls = b.GetEnabledLayers()
        for L in (pcbnew.In3_Cu, pcbnew.In4_Cu):
            ls.addLayer(L)
        b.SetEnabledLayers(ls)
        b.SetCopperLayerCount(6)
        b.Save(pcb)
        b = pcbnew.LoadBoard(pcb)

    # ---- the second GND reference plane, In4.Cu ------------------------
    # Built from the In1 pour's own outline, so the two references cover
    # exactly the same area and neither can drift away from the other.
    src = None
    have4 = False
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        if z.IsOnLayer(pcbnew.In1_Cu):
            src = z
        if z.IsOnLayer(pcbnew.In4_Cu):
            have4 = True
    if src is None:
        raise SystemExit('no In1.Cu GND pour to mirror -- refusing to guess an outline')
    if not have4:
        # Duplicate() hands back a BOARD_ITEM; Cast_to_ZONE gets the zone API
        # back so the layer set and net can be set on it.
        z = pcbnew.Cast_to_ZONE(src.Duplicate(False))
        ls = pcbnew.LSET()
        ls.addLayer(pcbnew.In4_Cu)
        z.SetLayerSet(ls)
        z.SetNet(src.GetNet())
        b.Add(z)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(pcb)

    # ---- the explicit stackup, written as text -------------------------
    # BOARD_STACKUP is not reachable through the SWIG bindings (it comes back
    # as an opaque SwigPyObject), so the block is authored here.  KiCad
    # re-parses it on the next load, which is what the verify below checks.
    raw = open(pcb, 'rb').read().decode('utf-8')
    crlf = '\r\n' in raw
    d = raw.replace('\r\n', '\n')
    if '(stackup' not in d:
        anchor = '\t(setup\n'
        i = d.index(anchor) + len(anchor)
        d = d[:i] + render_stackup() + '\n' + d[i:]
        open(pcb, 'wb').write((d.replace('\n', '\r\n') if crlf else d).encode('utf-8'))
    if verbose:
        print('SIX-LAYER MIGRATION: %s' % os.path.basename(pcb))
        print('  copper layers      %d' % pcbnew.LoadBoard(pcb).GetCopperLayerCount())
        print('  stack thickness    %.4f mm (target 1.6)' % total_thickness())
    patch_dru(pcb, verbose)
    return pcb


def verify(pcb):
    """Everything section 17 asks, measured from a reloaded board."""
    b = pcbnew.LoadBoard(pcb)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    rows = []
    names = [b.GetLayerName(L) for L in
             (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
              pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)]
    rows.append(('copper layer count', b.GetCopperLayerCount(), 6,
                 b.GetCopperLayerCount() == 6))
    rows.append(('layer names / order', ' '.join(names), ' '.join(CU_LAYERS),
                 names == list(CU_LAYERS)))
    raw = open(pcb, 'rb').read().decode('utf-8')
    rows.append(('explicit stackup present', '(stackup' in raw, True,
                 '(stackup' in raw))
    rows.append(('stack thickness mm', round(total_thickness(), 4), 1.6,
                 abs(total_thickness() - 1.6) <= 0.01))
    pours = [z for z in b.Zones() if not z.GetIsRuleArea()]
    for nm, lid in (('In1.Cu', pcbnew.In1_Cu), ('In4.Cu', pcbnew.In4_Cu)):
        zs = [z for z in pours if z.IsOnLayer(lid)]
        isl = sum(z.GetFilledPolysList(lid).OutlineCount() for z in zs)
        net = zs[0].GetNetname() if zs else '-'
        rows.append(('%s GND plane' % nm,
                     '%d zone %d island net %s' % (len(zs), isl, net),
                     '1 zone 1 island net GND',
                     len(zs) == 1 and isl == 1 and net == 'GND'))
    outer = [z for z in pours
             if z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu)]
    inner_sig = [z for z in pours
                 if z.GetLayer() in (pcbnew.In2_Cu, pcbnew.In3_Cu)]
    rows.append(('no outer / inner-signal pours',
                 '%d outer, %d on In2/In3' % (len(outer), len(inner_sig)),
                 '0, 0', not outer and not inner_sig))
    ntr = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK')
    nvia = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
    rows.append(('signal tracks / vias', '%d / %d' % (ntr, nvia), '0 / 0',
                 ntr == 0 and nvia == 0))
    bb = b.GetBoardEdgesBoundingBox()
    dims = '%.3f x %.3f' % (bb.GetWidth() / 1e6, bb.GetHeight() / 1e6)
    rows.append(('board outline mm', dims, '72.100 x 148.100',
                 dims == '72.100 x 148.100'))
    return rows


def main():
    import harness_paths as HP
    pcb = sys.argv[1] if len(sys.argv) > 1 else HP.project_file(HP.PCBNAME)
    if '--verify' not in sys.argv:
        convert(pcb)
    print('\nSIX-LAYER REGRESSION  %s' % os.path.basename(pcb))
    bad = 0
    for (nm, got, want, ok) in verify(pcb):
        print('  %-4s %-30s %-28s expected %s'
              % ('PASS' if ok else 'FAIL', nm, got, want))
        bad += 0 if ok else 1
    print('SIX-LAYER: %s' % ('PASS' if not bad else 'FAIL (%d)' % bad))
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
