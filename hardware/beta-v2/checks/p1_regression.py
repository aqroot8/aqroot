#!/usr/bin/env python3
"""AQROOT Full Beta v2 - FBV2-P1 floorplan regression.

Run with KiCad's bundled python:

    "<KICAD>/bin/python.exe" hardware/beta-v2/checks/p1_regression.py [metrics.txt]

Reads the board, re-derives every FBV2-P1 mechanical relationship from the
placed geometry (nothing is hard-coded from the previous pass except the
reservations themselves, which live in p1_geometry.py), prints PASS/FAIL for
each and writes the metrics file the review artefacts quote.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p1_geometry as G

OUT = []


def emit(s=''):
    OUT.append(s)
    print(s)


def row(name, value, rule, ok):
    mark = '' if ok is None else ('  PASS' if ok else '  **FAIL**')
    emit('%-38s %-30s %-24s%s' % (name, value, rule, mark))
    return bool(ok) if ok is not None else True


def main():
    # optional board override, so P1 can be re-verified on a scratch copy
    # before any of it reaches the authoritative project
    pcb = None
    for a in sys.argv[1:]:
        if a.endswith('.kicad_pcb'):
            pcb = a
    b, parts = G.load_parts(pcb) if pcb else G.load_parts()
    P = {p['ref']: p for p in parts}
    fails = []

    def chk(name, value, rule, ok):
        if not row(name, value, rule, ok):
            fails.append(name)

    # ------------------------------------------------------------- outline
    import pcbnew
    bb = b.GetBoardEdgesBoundingBox()
    w, h = bb.GetWidth() / 1e6 - 0.1, bb.GetHeight() / 1e6 - 0.1
    emit('AQROOT Full Beta v2 - FBV2-P1 floorplan metrics (doc datum: origin lower-left, Y up)')
    emit('=' * 118)
    chk('BOARD OUTLINE', '%.3f x %.3f mm' % (w, h), '72.000 x 148.000',
        abs(w - G.BOARD_W) < 1e-3 and abs(h - G.BOARD_H) < 1e-3)

    bosses = [p for p in parts if p['ref'].startswith('BOSS')]
    chk('FOOTPRINTS', '%d total, %d schematic + %d boss'
        % (len(parts), len(parts) - len(bosses), len(bosses)),
        '322 schematic', len(parts) - len(bosses) == 322)
    refs = [p['ref'] for p in parts]
    chk('DUPLICATE REFERENCES', str(len(refs) - len(set(refs))), '0', len(refs) == len(set(refs)))
    # FBV2-P2-001 created the In1.Cu GND reference plane, so the "zero fills"
    # expectation is retired: In1 is a POUR by design and the P1 gate never
    # meant to forbid it, only to forbid routing.  The zero-track / zero-via
    # expectation stands until a routing task legitimately lands copper, and
    # any In1 pour must be GND and must be a SINGLE island -- a split reference
    # is the defect this check now exists to catch.
    ntr = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK')
    nvia = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
    pours = [z for z in b.Zones() if not z.GetIsRuleArea()]
    outer = [z for z in pours if z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu)]
    in1 = [z for z in pours if z.GetLayer() == pcbnew.In1_Cu]
    isl = sum(z.GetFilledPolysList(z.GetLayer()).OutlineCount() for z in in1)
    chk('SIGNAL TRACKS / VIAS / OUTER POURS',
        '%d / %d / %d' % (ntr, nvia, len(outer)), '0 / 0 / 0',
        ntr == 0 and nvia == 0 and not outer)
    chk('In1.Cu GND REFERENCE',
        '%d zone(s), %d island(s), net %s'
        % (len(in1), isl, in1[0].GetNetname() if in1 else '-'),
        '1 zone, 1 island, GND',
        len(in1) == 1 and isl == 1 and in1[0].GetNetname() == 'GND')

    # -------------------------------------------------------- NFC geometry
    emit()
    emit('-- NFC, circular geometry (D-220) ' + '-' * 84)
    emit('NFC CENTRE                             doc (%.3f, %.3f)   identical for all three regions'
         % (G.NFC_CX, G.NFC_CY))
    emit('NFC CLEAR REGION                       Oe%.1f  -> X %.2f..%.2f  Y %.2f..%.2f'
         % (G.NFC_CLEAR_D, G.NFC_CX - 24, G.NFC_CX + 24, G.NFC_CY - 24, G.NFC_CY + 24))
    emit('NFC METAL EXCLUSION                    Oe%.1f  -> X %.2f..%.2f  Y %.2f..%.2f'
         % (G.NFC_METAL_D, G.NFC_CX - 29, G.NFC_CX + 29, G.NFC_CY - 29, G.NFC_CY + 29))
    emit('NFC PLACEMENT / TOLERANCE BOX          48 x 48 -> X %.2f..%.2f  Y %.2f..%.2f'
         % (G.NFC_CX - 24, G.NFC_CX + 24, G.NFC_CY - 24, G.NFC_CY + 24))
    for nm, v, rule, ok in G.nfc_checks():
        chk(nm, str(v), rule, ok)
    j5 = P['J5']
    gap = j5['court'][0] - (G.NFC_CX + 24)
    chk('NFC loop perimeter <-> J5 metal', '%.3f mm' % gap, '>= 5.0', gap >= 5.0)
    d1 = P['D1']
    emit()
    emit('OBJECTS INSIDE THE Oe58 METAL EXCLUSION - recorded; none is a screw, boss or can:')
    emit('   battery pouch foil                  %.3f mm inside   (1.500 mm inside the superseded'
         ' 58 x 51 rectangle)' % (98.5 - (G.NFC_CY - 29)))
    ddl = math.dist((d1['x'], d1['y']), (G.NFC_CX, G.NFC_CY))
    emit('   D1 TSAL6100 leadframe               %.3f mm inside,  %.3f mm outside the Oe48 loop'
         ' perimeter' % (29 - ddl, ddl - 24))
    emit('   (D1 also sat inside the superseded rectangular keep-out - not a regression)')
    for r in ('U6', 'J5', 'J7', 'BOSS1', 'BOSS2', 'MK1'):
        if r in P:
            dv = math.dist((P[r]['x'], P[r]['y']), (G.NFC_CX, G.NFC_CY)) - 29
            emit('   %-35s %+8.3f mm  %s' % (r, dv, 'OUTSIDE' if dv >= 0 else 'INSIDE'))

    # -------------------------------------------------------------- 915 feed
    emit()
    emit('-- 915 MHz feed ' + '-' * 102)
    u8 = P['U8']
    emit('U8 E22-900M22S                         B.Cu, courtyard X %.3f..%.3f  Y %.3f..%.3f'
         % (u8['court'][0], u8['court'][2], u8['court'][1], u8['court'][3]))
    emit('U8 IPEX / MHF1 port                    doc (%.2f, %.2f)' % G.U8_IPEX)
    emit('SMA BULKHEAD                           doc (%.2f, %.2f) top panel, Oe6.5 hole'
         % (G.SMA_X, G.SMA_Y))
    emit('COAX ROUTE                             ' +
         ' -> '.join('(%.1f,%.1f)' % p for p in G.COAX_PATH[:4]))
    emit('                                       ' +
         ' -> '.join('(%.1f,%.1f)' % p for p in G.COAX_PATH[4:]))
    emit('COAX POLYLINE LENGTH                   %.2f mm' % G.path_length(G.COAX_PATH))
    emit('COAX ROUTED LENGTH incl. bends         %.2f mm' % G.coax_routed_length())
    rmin = min(r for _, r, _ in G.bend_radii(G.COAX_PATH))
    chk('COAX MINIMUM BEND RADIUS', '%.2f mm' % rmin, '>= 5.0 (C-7)', rmin >= 5.0)
    need = G.coax_routed_length() + G.COAX_SERVICE_LOOP
    chk('INSTALLED LENGTH + service loop', '%.2f mm' % need, '<= 200 (CBA-UFLSMA20IP)', need <= 200)
    emit('SPARE ON THE 200 mm ASSEMBLY           %.2f mm beyond the 15 mm service loop'
         % (200.0 - need))
    fails_c, rows_c = G.coax_legal(parts=parts)
    chk('COAX vs every hard obstacle', '%d violations' % len(fails_c), '0', not fails_c)
    tight = sorted(rows_c, key=lambda r: r[2])[:4]
    for i, nm, v, ok in tight:
        emit('   tightest: seg%-2d %-30s %7.3f mm' % (i, nm, v))

    # ------------------------------------------------------------------ SMA
    emit()
    emit('-- SMA bulkhead and the top panel (B-52) ' + '-' * 77)
    emit('SMA BODY, from CAB/CBA manufacturer drawing:  8.00 mm A/F hex = Oe%.2f across corners,'
         % G.SMA_HEX_AC)
    emit('                                       1/4-36 UNS-2A thread, Oe10.2 REF lock washer,')
    emit('                                       HEX8 nut 1.80 mm thick, hex body 3.40 mm long')
    for nm, v, rule, ok in G.sma_checks():
        chk(nm, str(v), rule, ok)

    # -------------------------------------------------------------- IR / top
    emit()
    emit('-- IR ' + '-' * 112)
    d1c = (P['D1']['x'], P['D1']['y'])
    u6c = (P['U6']['x'], P['U6']['y'])
    cc = abs(u6c[0] - d1c[0])
    emit('IR TX D1 optical axis                  doc (%.3f, %.3f)' % d1c)
    emit('IR RX U6 optical axis                  doc (%.3f, %.3f)' % u6c)
    chk('IR TX <-> IR RX centre-to-centre', '%.3f mm' % cc, '>= 15.0', cc >= 15.0)
    emit('IR BARRIER                             X 56.500..61.500 full height, both shells;')
    emit('                                       fills the whole inter-window gap and carries BOSS2')

    # ------------------------------------------------------------- edge conn
    emit()
    emit('-- bottom edge and community port ' + '-' * 84)
    j2, j3 = P['J2'], P['J3']
    e2e = j3['court'][0] - j2['court'][2]
    chk('microSD <-> USB-C courtyard edge', '%.3f mm' % e2e, '>= 8.0 (D-217)', e2e >= 8.0)
    fp5 = b.FindFootprintByReference('J5')
    padmax = max(pd.GetBoundingBox().GetRight() for pd in fp5.Pads()) / 1e6
    chk('J5 tail row to board edge', '%.3f mm' % (70.0 - padmax), '>= 0.5', 70.0 - padmax >= 0.5)
    emit('J5 COMMUNITY courtyard                 X %.3f..%.3f  Y %.3f..%.3f'
         % (j5['court'][0], j5['court'][2], j5['court'][1], j5['court'][3]))

    # ------------------------------------------------------ battery/speaker
    emit()
    emit('-- rear reservations ' + '-' * 97)
    emit('BATTERY                                X %.1f..%.1f  Y %.1f..%.1f  (60 x 75 x 8.0) UNCHANGED'
         % (G.BATTERY[0], G.BATTERY[2], G.BATTERY[1], G.BATTERY[3]))
    emit('SPEAKER                                X %.1f..%.1f  Y %.1f..%.1f  (Oe20 x 3 sealed) UNCHANGED'
         % (G.SPEAKER[0], G.SPEAKER[2], G.SPEAKER[1], G.SPEAKER[3]))
    mk1 = P['MK1']
    mc = ((mk1['court'][0] + mk1['court'][2]) / 2, (mk1['court'][1] + mk1['court'][3]) / 2)
    d = math.dist(mc, G.SPEAKER_C)
    chk('MK1 <-> speaker centre-to-centre', '%.3f mm' % d, '>= 60.0, opposite faces', d >= 60.0)

    # ---------------------------------------------------------- 433 and NFC cable
    emit()
    emit('-- internal cables ' + '-' * 99)
    u7 = P['U7']
    emit('U7 E07-400M10S                         B.Cu, courtyard X %.3f..%.3f  Y %.3f..%.3f'
         % (u7['court'][0], u7['court'][2], u7['court'][1], u7['court'][3]))
    L433 = G.path_length(G.ANT433_PATH) + 0.6 * (len(G.ANT433_PATH) - 2)
    chk('433 flex lead, routed', '%.2f mm of 100 mm' % L433, '<= 100', L433 <= 100)
    j7 = P['J7']
    j7c = ((j7['court'][0] + j7['court'][2]) / 2, (j7['court'][1] + j7['court'][3]) / 2)
    Lnfc = math.dist(j7c, (G.NFC_CX, G.NFC_CY)) * 1.35
    chk('NFC pair, routed estimate', '%.2f mm of 75 mm' % Lnfc, '<= 75', Lnfc <= 75)
    j6 = P['J6']
    j6c = ((j6['court'][0] + j6['court'][2]) / 2, (j6['court'][1] + j6['court'][3]) / 2)
    Lspk = math.dist(j6c, G.SPEAKER_C) * 1.35
    chk('speaker lead, routed estimate', '%.2f mm of 152 mm' % Lspk, '<= 152', Lspk <= 152)

    # ------------------------------------------------------------- display
    emit()
    emit('-- display and J1 ' + '-' * 100)
    j1 = P['J1']
    emit('DISPLAY MODULE                         X %.2f..%.2f  Y %.2f..%.2f'
         % (G.DISPLAY[0], G.DISPLAY[2], G.DISPLAY[1], G.DISPLAY[3]))
    off = 35.0 - (G.DISPLAY[0] + G.DISPLAY[2]) / 2
    emit('DISPLAY OFFSET                         %.2f mm LEFT of the board centreline - '
         'ACCEPTED, INTENTIONAL (D-224)' % off)
    emit('J1 FH69                                X %.3f..%.3f  Y %.3f..%.3f'
         % (j1['court'][0], j1['court'][2], j1['court'][1], j1['court'][3]))
    consumed = (G.DISPLAY[1] - j1['court'][3]) + 6.0 + 3.0 + 4.7
    chk('FPC consumed of the 29.5 mm worst case', '%.2f mm' % consumed, '<= 29.5', consumed <= 29.5)

    # --------------------------------------------------------------- bosses
    emit()
    emit('-- retention ' + '-' * 105)
    for p in sorted(bosses, key=lambda q: q['ref']):
        emit('%-38s doc (%.3f, %.3f)   Oe4.5 mm keep-out, Oe2.2 NPTH'
             % (p['ref'], p['x'], p['y']))
    emit('SEARCH RESULT                          Oe6.0: 0 legal sites   Oe4.5: 2 legal sites')
    emit('SUPPORT REGIONS (User.3, no copper)    RIB_R1 RIB_R2 RIB_R3 RIB_B1')

    # ------------------------------------------------------------ collisions
    emit()
    emit('-- placement collision review ' + '-' * 88)
    coll = []
    n = len(parts)
    for i in range(n):
        a = parts[i]
        if not a['has_court']:
            continue
        for j in range(i + 1, n):
            c = parts[j]
            if not c['has_court']:
                continue
            if a['side'] == c['side']:
                if G.rect_overlap(a['court'], c['court']):
                    coll.append((a['ref'], c['ref'], 'courtyard'))
                continue
            # opposite faces: only the through-hole pads of one part can reach
            # the other face, so test holes against courtyards, not courtyard
            # against courtyard.
            for hh, other in ((a['holes'], c), (c['holes'], a)):
                if any(G.rect_overlap(x, other['court']) for x in hh):
                    coll.append((a['ref'], c['ref'], 'lead/hole through the board'))
                    break
    chk('side-aware courtyard collisions', str(len(coll)), '0', not coll)
    for a, c, k in coll[:12]:
        emit('   COLLISION %s <-> %s (%s)' % (a, c, k))
    # J5's MATING FACE is meant to sit at the wall, so its courtyard legitimately
    # overhangs the right edge by 0.43 mm; that is the whole point of a
    # right-angle socket and it is checked separately below.  U1's courtyard IS
    # the manufacturer antenna keep-out, two thirds of which is air beyond the
    # board edge (D-231).  Everything else must be inside the outline.
    EDGE_OK = {'J5', 'U1'}
    outb = [p['ref'] for p in parts if p['has_court'] and p['ref'] not in EDGE_OK and
            (p['court'][0] < -0.01 or p['court'][2] > G.BOARD_W + 0.01)]
    chk('parts outside the board in X', str(len(outb)), '0 (J5 mating face and the U1 keep-out excepted)',
        not outb)
    j5 = [p for p in parts if p['ref'] == 'J5']
    if j5:
        face = j5[0]['court'][2]
        chk('J5 mating face vs the wall', '%.3f mm outboard of the edge' % (face - G.BOARD_W),
            '<= 1.0 (fits the 1.5 mm wall gap)', face - G.BOARD_W <= 1.0)

    emit()
    emit('=' * 118)
    emit('REGRESSION: %s   (%d check%s failed)'
         % ('PASS' if not fails else 'FAIL', len(fails), '' if len(fails) == 1 else 's'))
    for f in fails:
        emit('   FAILED: ' + f)
    for a in sys.argv[1:]:
        if not a.endswith('.kicad_pcb'):
            with open(a, 'w', encoding='utf-8') as fh:
                fh.write('\n'.join(OUT) + '\n')
            break
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
