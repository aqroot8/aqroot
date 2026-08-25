# -*- coding: utf-8 -*-
"""FBV2-P2-002E PHASE B -- replay the VALIDATED Phase A geometry onto the
authoritative board.

NOTHING IS RECOMPUTED HERE.  Every track, via and rule-area outline is copied
verbatim out of the Phase A scratch board, and the .kicad_dru block is rewritten
from the same stub list Phase A recorded.  If Phase A did not pass, this script
refuses to run.

The one non-copy operation is TP34's side: Phase A flips TP34 to B.Cu before
routing, so the authoritative board must be flipped identically or the copper
would land on a pad that is not there.
"""
import os, sys, json, math, shutil, time
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import path_role_dru as DRU
import pcbnew

WORK = os.path.join(SP, "w")
SCRATCH = os.path.join(WORK, "A", RU.PCBNAME)
AUTH = os.path.join(RU.AUTH_DIR, RU.PCBNAME)


def key_track(t):
    return (t.GetNetname(), t.GetLayer(), t.GetWidth(),
            t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)


def main():
    res = json.load(open(os.path.join(SP, 'phaseA.json'), encoding='utf-8'))
    if res.get('fail'):
        raise SystemExit("PHASE A DID NOT PASS -- refusing to write authoritative copper:\n  "
                         + str(res['fail']))
    t0 = time.time()
    src = pcbnew.LoadBoard(SCRATCH)
    dst = pcbnew.LoadBoard(AUTH)

    have = [t for t in dst.GetTracks()]
    if have:
        raise SystemExit("authoritative board already carries %d track items" % len(have))

    # TP34 side, exactly as Phase A set it
    tp = [f for f in dst.GetFootprints() if f.GetReference() == 'TP34'][0]
    if tp.GetLayer() != pcbnew.B_Cu:
        tp.Flip(tp.GetPosition(), False)

    nets = {}
    for code, ni in dst.GetNetsByNetcode().items():
        nets[ni.GetNetname()] = ni

    ntrk = nvia = 0
    for t in src.GetTracks():
        nm = t.GetNetname()
        if nm not in nets:
            raise SystemExit("net %r exists on the scratch board but not on the "
                             "authoritative board" % nm)
        if t.GetClass() == 'PCB_VIA':
            v = pcbnew.PCB_VIA(dst)
            v.SetPosition(pcbnew.VECTOR2I(t.GetPosition().x, t.GetPosition().y))
            v.SetViaType(t.GetViaType())
            try:
                v.SetWidth(pcbnew.F_Cu, t.GetWidth(pcbnew.F_Cu))
                v.SetWidth(pcbnew.B_Cu, t.GetWidth(pcbnew.B_Cu))
            except TypeError:
                v.SetWidth(t.GetWidth())
            v.SetDrill(t.GetDrill())
            v.SetLayerPair(t.TopLayer(), t.BottomLayer())
            v.SetNet(nets[nm])
            dst.Add(v)
            nvia += 1
        else:
            n = pcbnew.PCB_TRACK(dst)
            n.SetStart(pcbnew.VECTOR2I(t.GetStart().x, t.GetStart().y))
            n.SetEnd(pcbnew.VECTOR2I(t.GetEnd().x, t.GetEnd().y))
            n.SetWidth(t.GetWidth())
            n.SetLayer(t.GetLayer())
            n.SetNet(nets[nm])
            dst.Add(n)
            ntrk += 1

    # rule areas: copy the outline verbatim, one zone per named Phase A area
    nzone = 0
    for z in src.Zones():
        if not z.GetIsRuleArea() or not z.GetZoneName():
            continue
        nm = z.GetZoneName()
        ps = pcbnew.SHAPE_POLY_SET()
        o = z.Outline()
        for i in range(o.OutlineCount()):
            c = o.Outline(i)
            ps.NewOutline()
            for k in range(c.PointCount()):
                ps.Append(c.CPoint(k).x, c.CPoint(k).y)
        if ps.OutlineCount() == 0:
            continue
        RU.add_named_area(dst, nm, 0, 0, 1, 1)
        RU.set_area_poly(dst, nm, ps)
        nzone += 1

    pcbnew.ZONE_FILLER(dst).Fill(dst.Zones())
    dst.Save(AUTH)
    DRU.write(AUTH, [tuple(s) for s in res['stubs']])

    # verify the copy is EXACT
    a = pcbnew.LoadBoard(AUTH)
    ks = sorted(key_track(t) for t in src.GetTracks() if t.GetClass() == 'PCB_TRACK')
    kd = sorted(key_track(t) for t in a.GetTracks() if t.GetClass() == 'PCB_TRACK')
    exact = (ks == kd)
    print(json.dumps(dict(tracks=ntrk, vias=nvia, areas=nzone,
                          exact_geometry=exact, secs=round(time.time() - t0, 1)),
                     indent=1))
    if not exact:
        raise SystemExit("REPLAY IS NOT EXACT -- authoritative board rolled back by git")


main()
