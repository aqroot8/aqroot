# -*- coding: utf-8 -*-
"""FBV2-P2-002T section 3 -- CHARACTERIZE THE FOUR SCARCE SITES FIRST.

002S proved three of four failing pads still had a legal escape on the finished
board, so the failures were width/layer selection at the moment of routing, not
geometric seals.  D-266 answers that with SCARCE-PAD ESCAPE RESERVATION, and a
reservation cannot be sized before the site is measured.  This module builds the
clean six-layer scratch board at the frozen placement and measures each site
BEFORE any significant signal copper exists.

    python scarce_char_002t.py            # characterize
"""
import os, sys, json, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import pcbnew
import path_role_util as RU
import battery_route_plan as PL
import path_role_dru as DRU
import qrouter as QR

WORK = os.path.join(SP, 'w')
N = PL.N
AREAS = ['BAT_PROT_TAP_U18', 'BAT_PROT_TAP_U14', 'BAT_PROT_ESCAPE_U11',
         'BAT_SENSE_KELVIN', 'BAT_RAW_TAP_U18']
STUBAREAS = ['BAT_STUB_%d' % k for k in range(10)]
FINEAREAS = ['FINE_ESC_%d' % k for k in range(16)]
WIDE = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                 'BAT_SENSE', 'BAT_PROTECTED_P'))
CP, CT_S, CT_W = 200000, 200000, 300000
G = 25000


def prep(tag, place_json, expect=True):
    """A clean six-layer scratch board at the frozen placement.

    Mirrors route_battery_block.main()'s preparation exactly -- same fresh copy,
    same TP34 face, same named areas, same DRU, same candidate placement -- so
    a site measured here is a site the router will meet.

    The authoritative board is ALREADY six-layer (002R), so no conversion is
    needed, and the 002F ECO is deliberately NOT applied: the candidate file
    carries ABSOLUTE poses for every guarded reference, while the ECO also
    moves parts the fingerprint does not guard.  Applying it puts the screen on
    a board nobody asked for -- measured, it adds `courtyards_overlap` and a
    second `solder_mask_bridge` AFTER the DRC baseline is taken, so every
    subsequent connection is rejected for a violation it did not cause.
    """
    import placement_fingerprint as FP
    pcb = RU.fresh(WORK, tag)
    b = pcbnew.LoadBoard(pcb)
    tp = [f for f in b.GetFootprints() if f.GetReference() == 'TP34'][0]
    if tp.GetLayer() != pcbnew.B_Cu:
        tp.Flip(tp.GetPosition(), False)
    for a in AREAS + STUBAREAS + FINEAREAS:
        RU.add_named_area(b, a, 0, 0, 1000, 1000)
    b.Save(pcb)
    DRU.write(pcb, [])
    spec = json.load(open(place_json))
    bb = pcbnew.LoadBoard(pcb)
    fp = {f.GetReference(): f for f in bb.GetFootprints()}
    for r, v in spec.get('moves', {}).items():
        f = fp[r]
        if len(v) > 3 and bb.GetLayerName(f.GetLayer()) != v[3]:
            f.Flip(f.GetPosition(), False)
        f.SetPosition(pcbnew.VECTOR2I(int(round(v[0] * 1e6)),
                                      int(round(v[1] * 1e6))))
        f.SetOrientationDegrees(v[2])
    bb.BuildConnectivity()
    pcbnew.ZONE_FILLER(bb).Fill(bb.Zones())
    bb.Save(pcb)
    if expect:
        FP.assert_placement(pcb, place_json, label='002T characterization')
    return pcb


# The six sites.  Four scarce (section 3 A-D) plus the two Kelvin partners
# section 3 also requires for the paired topology.
SITES = ['Q3.6', 'U18.9', 'U18.2', 'R75.1', 'U18.8', 'R75.2']
WIDTHS = [300000, 250000, 200000, 150000]
VIA_DIA, VIA_DRL = 350000, 200000


def characterize(pcb):
    qb = QR.QBoard(pcb)
    qb.wide_nets = WIDE
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(ref, p)
    out = {}
    for ref in SITES:
        p = pads[ref]
        wide = p['net'] in WIDE
        clr_trk = CT_W if wide else CT_S
        rec = dict(ref=ref, net=p['net'][len(N):] if p['net'].startswith(N)
                   else p['net'], wide=wide, layers={}, via=None, why=None)
        for lay in ('B', 'F'):
            for w in WIDTHS:
                e = qb.escape(p, lay, w, w, CP, clr_trk, G,
                              qb.ex0 - 2000000, qb.ey0 - 2000000)
                if e:
                    rec['layers'][lay] = dict(width=w / 1e6, dirs=len(e))
                    break
            else:
                rec['layers'][lay] = None
                if lay == 'B' and qb.escape_why:
                    rec['why'] = qb.escape_why[0]
        # nearest reachable ordinary 0.35/0.20 through-via site from B.Cu
        for lay in ('B', 'F'):
            info = rec['layers'].get(lay)
            if not info:
                continue
            w = int(round(info['width'] * 1e6))
            e = qb.escape(p, lay, w, w, CP, clr_trk, G,
                          qb.ex0 - 2000000, qb.ey0 - 2000000)
            best = None
            for far in ('I2', 'I3'):
                for esc in e:
                    v = qb.via_site(lay, far, p['net'], esc, w, VIA_DIA,
                                    CP, clr_trk, G, via_drill=VIA_DRL)
                    if not v:
                        continue
                    d = ((v[0] - p['x']) ** 2 + (v[1] - p['y']) ** 2) ** 0.5
                    if best is None or d < best[0]:
                        best = (d, far, v)
            if best:
                d, far, v = best
                rec['via'] = dict(near=lay, far=far,
                                  x=round(v[0] / 1e6, 3),
                                  y=round(v[1] / 1e6, 3),
                                  dist=round(d / 1e6, 3))
                break
        out[ref] = rec
    return qb, pads, out


def render(out):
    print('%-7s %-16s %-22s %-22s %s'
          % ('PAD', 'NET', 'B.Cu', 'F.Cu', 'nearest 0.35/0.20 via'))
    for ref, r in out.items():
        def f(k):
            v = r['layers'].get(k)
            return ('%.2f mm, %d dir' % (v['width'], v['dirs'])) if v \
                else 'NO LEGAL ESCAPE'
        v = r['via']
        vs = ('%s->%s @ %.3f mm (%.3f, %.3f)'
              % (v['near'], v['far'], v['dist'], v['x'], v['y'])) \
            if v else 'none reachable'
        print('%-7s %-16s %-22s %-22s %s' % (ref, r['net'], f('B'), f('F'), vs))
        if r['why']:
            print('        %s' % r['why'][:110])


if __name__ == '__main__':
    pcb = prep(os.environ.get('AQROOT_SCRATCH', 'T0'),
               os.environ.get('AQROOT_PLACE_JSON', 'cand_002p/Q02.json'))
    qb, pads, out = characterize(pcb)
    render(out)
    json.dump(out, open(os.environ.get('AQROOT_CHAR_OUT',
                                       'char_002t.json'), 'w'), indent=1)
