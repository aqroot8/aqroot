# -*- coding: utf-8 -*-
"""FBV2-P2-038 -- bounded cardinality-1 west-button pull-up placement ECO screen.

Moves only R5/R8/R6 on scratch copies.  Existing copper, U2, and every switch
stay fixed.  Candidates must clear same-face courtyards/board edges, then the
real incremental router must complete the whole four-physical-pad net.
"""
import os, sys, json, math, shutil
import pcbnew

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import qrouter as QR
import incremental_router as IR

OUT = os.path.join(SP, 'w', 'ECO_038')
TARGETS = [('BTN_DOWN_N', 'R5'), ('BTN_A_N', 'R8'), ('BTN_LEFT_N', 'R6')]

def rect(f):
    cy = f.GetCourtyard(f.GetLayer())
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox()
    return (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())

def overlaps(a, b, gap=0):
    return not (a[2]+gap < b[0] or b[2]+gap < a[0] or
                a[3]+gap < b[1] or b[3]+gap < a[1])

def legal(b, ref):
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    f, a = fp[ref], rect(fp[ref])
    eb = b.GetBoardEdgesBoundingBox()
    if a[0] < eb.GetLeft() or a[1] < eb.GetTop() or a[2] > eb.GetRight() or a[3] > eb.GetBottom():
        return False, 'edge'
    for g in b.GetFootprints():
        if g.GetReference() == ref or g.IsFlipped() != f.IsFlipped():
            continue
        if overlaps(a, rect(g)):
            return False, g.GetReference()
    for z in b.Zones():
        if z.GetIsRuleArea():
            q=z.GetBoundingBox()
            if overlaps(a, (q.GetLeft(),q.GetTop(),q.GetRight(),q.GetBottom())):
                return False, 'ruleArea'
    return True, ''

def try_one(net, ref, dx, dy, rot):
    tag = '%s_%+d_%+d_r%d' % (ref, int(dx*1000), int(dy*1000), int(rot))
    d = os.path.join(OUT, tag); os.makedirs(d, exist_ok=True)
    pcb = os.path.join(d, RU.PCBNAME); shutil.copyfile(IR.AUTH, pcb)
    b = pcbnew.LoadBoard(pcb); fp={f.GetReference():f for f in b.GetFootprints()}
    f=fp[ref]; p=f.GetPosition(); old=(p.x,p.y,f.GetOrientationDegrees())
    f.SetPosition(pcbnew.VECTOR2I(p.x+int(dx*1e6),p.y+int(dy*1e6)))
    f.SetOrientationDegrees(rot)
    ok, why=legal(b,ref)
    if not ok: return dict(net=net,ref=ref,dx=dx,dy=dy,rot=rot,ok=False,reason='collision:'+why)
    b.Save(pcb)
    qb=QR.QBoard(pcb); IR.inject_existing_via_obstacles(qb)
    # BTN_LEFT_N was characterized by the family wall before receiving a
    # persistent incremental-router registry entry.  It has the same locked
    # Default signal geometry as the other navigation buttons; construct that
    # ordinary group explicitly instead of confusing registry absence with a
    # hardware result.
    if net in IR.GROUPS:
        group=dict(IR.GROUPS[net]); group.pop('hop_anchor_plan',None)
    else:
        group=dict(layer='B', width=200000, clr_pad=200000, clr_trk=200000,
                   via_dia=600000, via_drill=300000, nets=[net])
    nf=IR.resolve_nets(qb,group)[net]
    pads=IR.physical_net_pads(qb,nf); pads.sort(key=lambda x:(x['ref'],x['x'],x['y']))
    rec=[]
    for i,j in IR.mst_edges(pads):
        a,c=pads[i],pads[j]; lay,kind=IR.edge_plan(a,c,group)
        if kind=='same': r=QR.connect_role(qb,nf,a,c,lay,group['width'],group['clr_pad'],group['clr_trk'])
        else: r=IR.connect_cross(qb,nf,a,c,group)
        rec.append(dict(a=a['ref'],b=c['ref'],kind=kind,ok=bool(r.get('ok')),reason=r.get('reason'),mm=r.get('mm',0)))
        if not r.get('ok'): break
    success=len(rec)==len(pads)-1 and all(x['ok'] for x in rec)
    if success:
        if any(x.GetClass()=='PCB_VIA' for x in qb.laid): IR.refill_planes(qb.b)
        qb.save(pcb)
    else:
        shutil.rmtree(d)
    reason = '' if success else (rec[-1].get('reason') or 'incomplete' if rec else 'no_edges')
    return dict(net=net,ref=ref,dx=dx,dy=dy,rot=rot,old=old,ok=success,
                reason=reason,route=rec,pcb=pcb if success else None)

def main():
    os.makedirs(OUT,exist_ok=True)
    b=pcbnew.LoadBoard(IR.AUTH); fp={f.GetReference():f for f in b.GetFootprints()}
    results=[]
    only = os.environ.get('AQROOT_ECO038_ONLY')
    targets = [t for t in TARGETS if not only or t[0] == only]
    if only and not targets:
        raise SystemExit('unknown AQROOT_ECO038_ONLY=%r' % only)
    # Cardinality one; compact 0.5/1.0 mm compass/diagonal translations and 180 flip.
    offsets=[(x,y) for x,y in [(0,-1),(0,-.5),(0,.5),(0,1),(-1,0),(-.5,0),(.5,0),(1,0),
                                (-.5,-.5),(.5,-.5),(-.5,.5),(.5,.5)]]
    for net,ref in targets:
        home=fp[ref].GetOrientationDegrees()
        for rot in (home,(home+180)%360):
            for dx,dy in offsets:
                r=try_one(net,ref,dx,dy,rot); results.append(r)
                print('%s %s dx=%+.1f dy=%+.1f r=%d %s' %(net,ref,dx,dy,rot,'PASS' if r['ok'] else r.get('reason','FAIL')))
                if r['ok']:
                    json.dump(results,open(os.path.join(OUT,'results.json'),'w'),indent=1)
                    print('FIRST SUCCESS',r['pcb']); return 0
    json.dump(results,open(os.path.join(OUT,'results.json'),'w'),indent=1)
    print('NO SUCCESS in %d legal/bounded candidates'%len(results)); return 1

if __name__=='__main__': sys.exit(main())
