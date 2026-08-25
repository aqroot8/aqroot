# -*- coding: utf-8 -*-
"""FBV2-P2-002G sections 19 and 23 -- the ACCEPTED ROUTE MANIFEST.

Section 23 forbids redrawing authoritative copper from memory.  The manifest is
the source of truth for the authoritative replay: it records the accepted
placement, every piece of copper as literal geometry, the PR-39 requested /
actual endpoint ledger, and checksums of both the clean pre-route board and the
accepted result, so a replay can be proved identical rather than asserted to be.

    build   battery_manifest.py build  <accepted.kicad_pcb> <out.json>
    apply   battery_manifest.py apply  <manifest.json> <target.kicad_pcb>
    verify  battery_manifest.py verify <manifest.json> <board.kicad_pcb>
"""
import os, sys, json, math, hashlib, collections
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import net_ledger as NL
import path_role_util as RU
import pcbnew

N = NL.N


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def copper(b):
    """Every track and via, as literal geometry, sorted for stable comparison."""
    tr, vi = [], []
    for t in b.GetTracks():
        nm = t.GetNetname()
        short = nm[len(N):] if nm.startswith(N) else nm
        if t.GetClass() == 'PCB_VIA':
            vi.append(dict(net=short, x=t.GetPosition().x, y=t.GetPosition().y,
                           drill=t.GetDrill(), top=t.TopLayer(),
                           bottom=t.BottomLayer(),
                           width=t.GetWidth() if not hasattr(t, 'GetWidth')
                           else t.GetWidth()))
        else:
            tr.append(dict(net=short, layer=t.GetLayer(), w=t.GetWidth(),
                           x0=t.GetStart().x, y0=t.GetStart().y,
                           x1=t.GetEnd().x, y1=t.GetEnd().y))
    tr.sort(key=lambda d: (d['net'], d['layer'], d['w'], d['x0'], d['y0'],
                           d['x1'], d['y1']))
    vi.sort(key=lambda d: (d['net'], d['x'], d['y']))
    return tr, vi


def placement(b, refs):
    out = {}
    for f in b.GetFootprints():
        r = f.GetReference()
        if refs and r not in refs:
            continue
        out[r] = dict(x=f.GetPosition().x, y=f.GetPosition().y,
                      rot=round(f.GetOrientationDegrees(), 1),
                      flipped=bool(f.IsFlipped()))
    return out


def rule_areas(b):
    out = []
    for z in b.Zones():
        if not z.GetIsRuleArea() or not z.GetZoneName():
            continue
        o = z.Outline()
        polys = []
        for i in range(o.OutlineCount()):
            c = o.Outline(i)
            polys.append([[c.CPoint(k).x, c.CPoint(k).y]
                          for k in range(c.PointCount())])
        out.append(dict(name=z.GetZoneName(), outlines=polys))
    out.sort(key=lambda d: d['name'])
    return out


def build(accepted, out_path, clean=None, journal=None, moves=None):
    b = pcbnew.LoadBoard(os.path.abspath(accepted))
    b.BuildConnectivity()
    tr, vi = copper(b)
    lg = NL.ledger(accepted)
    byn = collections.defaultdict(lambda: dict(mm=0.0, widths=set(), vias=0,
                                               layers=set()))
    for t in tr:
        d = byn[t['net']]
        d['mm'] += math.hypot(t['x1'] - t['x0'], t['y1'] - t['y0']) / 1e6
        d['widths'].add(round(t['w'] / 1e6, 3))
        d['layers'].add(b.GetLayerName(t['layer']))
    for v in vi:
        byn[v['net']]['vias'] += 1
    nets = {k: dict(mm=round(v['mm'], 3), widths=sorted(v['widths']),
                    vias=v['vias'], layers=sorted(v['layers']),
                    connected=lg['nets'].get(k, {}).get('connected'),
                    islands=lg['nets'].get(k, {}).get('islands'))
            for k, v in sorted(byn.items())}
    man = dict(
        schema='aqroot-battery-route-manifest/1',
        accepted_pcb=os.path.basename(accepted),
        accepted_sha256=sha(accepted),
        clean_sha256=sha(clean) if clean else None,
        placement=placement(b, set(moves) if moves else None),
        rule_areas=rule_areas(b),
        tracks=tr, vias=vi,
        nets=nets,
        ledger=dict(connected=lg['connected'], total=lg['total'],
                    out_of_scope=lg['out_of_scope']),
        journal=journal or [],
        counts=dict(tracks=len(tr), vias=len(vi)))
    json.dump(man, open(out_path, 'w'), indent=1)
    return man


def apply(man_path, target):
    """Replay the manifest's copper onto a board, verbatim."""
    man = json.load(open(man_path))
    dst = pcbnew.LoadBoard(os.path.abspath(target))
    have = [t for t in dst.GetTracks()]
    if have:
        raise SystemExit('target already carries %d track items' % len(have))

    for r, p in man['placement'].items():
        f = [g for g in dst.GetFootprints() if g.GetReference() == r]
        if not f:
            raise SystemExit('manifest names a footprint the target lacks: %s' % r)
        f = f[0]
        if bool(f.IsFlipped()) != bool(p['flipped']):
            f.Flip(f.GetPosition(), False)
        f.SetPosition(pcbnew.VECTOR2I(int(p['x']), int(p['y'])))
        f.SetOrientationDegrees(p['rot'])
    dst.BuildConnectivity()

    nets = {}
    for code, ni in dst.GetNetsByNetcode().items():
        nets[ni.GetNetname()] = ni

    def netinfo(short):
        full = N + short
        if full in nets:
            return nets[full]
        if short in nets:
            return nets[short]
        raise SystemExit('manifest net not on the target board: %s' % short)

    for t in man['tracks']:
        n = pcbnew.PCB_TRACK(dst)
        n.SetStart(pcbnew.VECTOR2I(int(t['x0']), int(t['y0'])))
        n.SetEnd(pcbnew.VECTOR2I(int(t['x1']), int(t['y1'])))
        n.SetWidth(int(t['w']))
        n.SetLayer(int(t['layer']))
        n.SetNet(netinfo(t['net']))
        dst.Add(n)
    for v in man['vias']:
        q = pcbnew.PCB_VIA(dst)
        q.SetPosition(pcbnew.VECTOR2I(int(v['x']), int(v['y'])))
        try:
            q.SetWidth(pcbnew.F_Cu, int(v['width']))
            q.SetWidth(pcbnew.B_Cu, int(v['width']))
        except TypeError:
            q.SetWidth(int(v['width']))
        q.SetDrill(int(v['drill']))
        q.SetLayerPair(int(v['top']), int(v['bottom']))
        q.SetNet(netinfo(v['net']))
        dst.Add(q)

    for a in man['rule_areas']:
        ps = pcbnew.SHAPE_POLY_SET()
        for poly in a['outlines']:
            ps.NewOutline()
            for (x, y) in poly:
                ps.Append(int(x), int(y))
        if ps.OutlineCount():
            RU.add_named_area(dst, a['name'], 0, 0, 1, 1)
            RU.set_area_poly(dst, a['name'], ps)

    pcbnew.ZONE_FILLER(dst).Fill(dst.Zones())
    dst.Save(os.path.abspath(target))
    return man


def verify(man_path, board):
    man = json.load(open(man_path))
    b = pcbnew.LoadBoard(os.path.abspath(board))
    tr, vi = copper(b)
    same_t = (tr == man['tracks'])
    same_v = (vi == man['vias'])
    lg = NL.ledger(board)
    rows = [
        ('track geometry identical', '%d vs %d' % (len(tr), len(man['tracks'])), same_t),
        ('via geometry identical', '%d vs %d' % (len(vi), len(man['vias'])), same_v),
        ('in-scope nets connected', '%d of %d' % (lg['connected'], lg['total']),
         lg['connected'] == lg['total']),
        ('manifest ledger matches', '%d of %d' % (man['ledger']['connected'],
                                                  man['ledger']['total']),
         lg['connected'] == man['ledger']['connected'] and
         lg['total'] == man['ledger']['total']),
        ('no out-of-scope copper', str(len(lg['out_of_scope'])),
         not lg['out_of_scope']),
    ]
    bad = []
    for (nm, det, ok) in rows:
        print('  %-4s %-34s %s' % ('PASS' if ok else 'FAIL', nm, det))
        if not ok:
            bad.append(nm)
    return bad


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == 'build':
        m = build(sys.argv[2], sys.argv[3],
                  clean=sys.argv[4] if len(sys.argv) > 4 else None)
        print('manifest: %d tracks, %d vias, %d of %d nets connected'
              % (m['counts']['tracks'], m['counts']['vias'],
                 m['ledger']['connected'], m['ledger']['total']))
        return 0
    if cmd == 'apply':
        m = apply(sys.argv[2], sys.argv[3])
        print('applied %d tracks, %d vias, %d footprints, %d rule areas'
              % (m['counts']['tracks'], m['counts']['vias'],
                 len(m['placement']), len(m['rule_areas'])))
        return 0
    if cmd == 'verify':
        bad = verify(sys.argv[2], sys.argv[3])
        print('MANIFEST VERIFY: %s' % ('PASS' if not bad else 'FAIL'))
        return 0 if not bad else 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
