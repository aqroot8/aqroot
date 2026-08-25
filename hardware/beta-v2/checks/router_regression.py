# -*- coding: utf-8 -*-
"""FBV2-P2-002B -- router qualification regression test.

Run with KiCad's own Python:

    "P:/New folder (2)/bin/python.exe" hardware/beta-v2/checks/router_regression.py

Six router defects put copper on this board that should never have been laid.
This script is the standing guard against all six coming back:

  G1  SCRATCH PROJECT MISSING RULE CONTEXT.  A .kicad_pcb copied on its own
      loses .kicad_dru, the .kicad_pro netclasses and fp-lib-table, and DRC then
      silently measures against KiCad DEFAULTS.  FBV2-P2-002A spent a whole
      routing attempt reading a phantom "clearance:73, lib_footprint_issues:17"
      offset that way.  Every scratch board here is a COMPLETE project copy, and
      its baseline DRC histogram must equal the authoritative one exactly.

  G2  NECK / TRUNK DISCONNECTION.  The escape neck and the trunk must be one
      connected copper component, judged by KiCad's own connectivity engine
      after a real save and reload -- never by looking at the geometry.

  G3  NECK BELOW RULE WIDTH.  A neck may not be narrower than the applicable
      rule minimum just because the pad is narrow.  Where the land pattern
      cannot accept the rule width the pad is classified NO LEGAL ESCAPE and
      nothing is emitted.

  G4  NECK COLLISION.  The neck is checked against the same obstacle set as the
      trunk.  A short segment is not exempt.

  G5  FOREIGN-NET SHORT.  No pad of another net may end up in the routed net's
      copper cluster, and DRC must gain no violation of any class.

  G6  ENDPOINT NOT CONNECTED.  The ratsnest must fall by exactly one edge per
      routed connection.

It also pins the five PROVED land-pattern conflicts (section 6 of FBV2-P2-002B).
If a rule is relaxed or a part is moved so that one of them becomes routable --
or if a new pad joins the list -- this test fails and asks for a fresh ruling
rather than letting the change pass unnoticed.
"""
import os, sys, json, shutil, subprocess, collections, math, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PRJ = os.path.join(REPO, 'hardware', 'beta-v2', 'kicad', 'aqroot-beta-v2')
PCBNAME = 'aqroot-Beta-v2.kicad_pcb'
KC = os.environ.get('KICAD_CLI', r'P:/New folder (2)/bin/kicad-cli.exe')
NEEDED = ('aqroot-Beta-v2.kicad_dru', 'aqroot-Beta-v2.kicad_pro',
          'fp-lib-table', 'sym-lib-table', 'libraries')

try:
    import pcbnew
except ImportError:
    print("router_regression: needs KiCad's bundled python (pcbnew).")
    raise SystemExit(2)
import qrouter as QR
import path_role_util as RU

N = '/01_POWER_TREE/'
# width / rule floor / pad clearance / track clearance, nm.  Taken from the
# project's own netclasses and .kicad_dru, NOT from KiCad defaults.
BAT = dict(w=1000000, minw=600000, cp=200000, ct=300000)
BPP = dict(w=1500000, minw=1200000, cp=200000, ct=300000)
SIG = dict(w=250000, minw=150000, cp=200000, ct=200000)

CASES = [
    ('Q2_CS   two-pad SOIC hop',        N + 'Q2_CS', SIG, [('Q2.3', 'Q2.1')]),
    ('BAT_MID 1.00 mm, 0.60 mm floor',  N + 'BAT_MID', BAT,
     [('Q2.5', 'Q2.6'), ('Q2.6', 'Q3.8'), ('Q3.8', 'Q3.7')]),
    ('LTC_OV  fine-pitch escape',       N + 'LTC_OV', SIG,
     [('U18.3', 'R77.2'), ('R77.2', 'R78.1')]),
]

# ref -> (net, rule floor nm, widest legal escape nm).  Proved by bisection in
# docs/full-beta-v2/audits/2026-08-24-routing-harness-qualification.md.
# Re-measured at FBV2-P2-002C after TWO corrections to the router:
#   * seg_shape_dist became EXACT.  The old sampled distance subtracted half a
#     step as a safety margin, so every figure was 5 um low - the difference
#     between "0.195 mm" and the truth, which is that U11.2 admits EXACTLY
#     0.200 mm, the width the CTO ruled for it.
#   * the board outline is now inset by half the Edge.Cuts stroke, because
#     copper-to-edge clearance is measured to the LINE, not to the outside of
#     the stroke.  That is 25 um, and it is what moves U14.2 / U14.3 from
#     0.300 mm to 0.240 mm: those two are EDGE-limited, not pad-limited.
CONFLICTS = {
    'U18.9': (N + 'BAT_SENSE',       600000,  250000),
    'U18.8': (N + 'BAT_PROTECTED_P', 1200000, 250000),
    'U14.2': (N + 'BAT_PROTECTED_P', 1200000, 240000),
    'U14.3': (N + 'BAT_PROTECTED_P', 1200000, 240000),
    'U11.2': (N + 'BAT_PROTECTED_P', 1200000, 200000),
}

FAILED = []
def chk(name, detail, ok):
    print('  %-4s %-46s %s' % ('PASS' if ok else 'FAIL', name, detail))
    if not ok:
        FAILED.append(name)
    return ok


def project_context(pcb):
    d = os.path.dirname(os.path.abspath(pcb))
    return [n for n in NEEDED if not os.path.exists(os.path.join(d, n))]


def drc(pcb, tag, work):
    missing = project_context(pcb)
    if missing:
        raise RuntimeError('PROJECT CONTEXT MISSING next to %s: %s' % (pcb, missing))
    out = os.path.join(work, 'drc_%s.json' % tag)
    subprocess.run([KC, 'pcb', 'drc', '--severity-all', '--format', 'json',
                    '-o', out, pcb], capture_output=True, text=True)
    j = json.load(open(out, encoding='utf-8'))
    c = collections.Counter()
    for key in ('violations', 'unconnected_items', 'schematic_parity'):
        for v in j.get(key, []):
            c[v.get('type', key)] += 1
    return c


def fresh(work, name):
    dst = os.path.join(work, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(PRJ, dst)
    return os.path.join(dst, PCBNAME)


def ratsnest(pcb):
    b = pcbnew.LoadBoard(pcb)
    b.BuildConnectivity()
    return b.GetConnectivity().GetUnconnectedCount(True)


def cluster(pcb, net, refs):
    b = pcbnew.LoadBoard(pcb)
    b.BuildConnectivity()
    cn = b.GetConnectivity()
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            pads[f.GetReference() + '.' + p.GetNumber()] = p
    comps, foreign = [], set()
    for r in refs:
        p = pads[r]
        s = {str(p.m_Uuid.AsString())}
        for it in cn.GetConnectedItems(p):
            s.add(str(it.m_Uuid.AsString()))
            if it.GetClass() == 'PAD' and it.GetNetname() != net:
                fp = it.GetParentFootprint()
                foreign.add(fp.GetReference() if fp else '?')
        comps.append(s)
    merged = []
    for s in comps:
        merged.append(set(s))
    changed = True
    while changed:
        changed = False
        for i in range(len(merged)):
            for j in range(len(merged) - 1, i, -1):
                if merged[i] & merged[j]:
                    merged[i] |= merged.pop(j)
                    changed = True
    return len(merged), sorted(foreign)


def main():
    work = tempfile.mkdtemp(prefix='aqroot-router-regression-')
    try:
        print('router_regression -- FBV2-P2-002B')
        print('  workspace %s' % work)

        # ---- G1 project context ------------------------------------------
        auth = os.path.join(PRJ, PCBNAME)
        base_a = drc(auth, 'auth', work)
        scratch = fresh(work, 'base')
        chk('G1 scratch carries the full project context',
            'dru + pro + fp-lib-table + libraries present',
            not project_context(scratch))
        base_s = drc(scratch, 'base', work)
        chk('G1 scratch baseline DRC == authoritative baseline DRC',
            '%s' % dict(sorted(base_s.items())), base_a == base_s)
        base_rn = ratsnest(scratch)

        # ---- G2..G6 per routed case --------------------------------------
        for title, net, spec, pairs in CASES:
            tag = title.split()[0]
            pcb = fresh(work, tag)
            qb = QR.QBoard(pcb)
            refs, ok = set(), True
            for a, b in pairs:
                pa, pb = qb.pads.get((net, a)), qb.pads.get((net, b))
                if pa is None or pb is None:
                    ok = False
                    chk('G3/G4 %s' % title, 'missing pad %s/%s' % (a, b), False)
                    break
                refs |= {a, b}
                r = QR.connect(qb, net, pa, pb, 'B', spec['w'], spec['minw'],
                               spec['cp'], spec['ct'])
                if not r['ok']:
                    ok = False
                    chk('G3/G4 %s' % title, '%s->%s %s' % (a, b, r['reason']), False)
                    break
            if not ok:
                continue
            qb.save()

            widths = [t.GetWidth() for t in pcbnew.LoadBoard(pcb).GetTracks()
                      if t.GetClass() == 'PCB_TRACK']
            chk('G3 %s: no segment below the rule floor' % tag,
                'min %.3f mm >= %.3f mm' % (min(widths) / 1e6, spec['minw'] / 1e6),
                min(widths) >= spec['minw'])

            after = drc(pcb, tag, work)
            d = dict((k, v - base_s.get(k, 0)) for k, v in after.items()
                     if v > base_s.get(k, 0) and k != 'unconnected_items')
            chk('G4/G5 %s: no new DRC violation of any class' % tag,
                d or 'clean', not d)

            ncomp, foreign = cluster(pcb, net, sorted(refs))
            chk('G2 %s: one connected component after save/reload' % tag,
                '%d component(s)' % ncomp, ncomp == 1)
            chk('G5 %s: no foreign pad joined the cluster' % tag,
                foreign or 'none', not foreign)
            rn = ratsnest(pcb)
            chk('G6 %s: ratsnest fell by one edge per connection' % tag,
                'delta %+d, expected %+d' % (rn - base_rn, -len(pairs)),
                rn - base_rn == -len(pairs))

        # ---- proved land-pattern conflicts -------------------------------
        qb = QR.QBoard(scratch)
        for ref, (net, floor, proved) in sorted(CONFLICTS.items()):
            pad = qb.pads.get((net, ref))
            if pad is None:
                chk('conflict %s still present' % ref, 'pad missing from %s' % net, False)
                continue
            lo, hi, best = 50000, 2000000, 0
            while hi - lo > 5000:
                mid = ((lo + hi) // 2 // 5000) * 5000
                if qb.escape(pad, 'B', mid, mid, 200000, 300000, 25000, qb.ex0, qb.ey0):
                    best, lo = mid, mid
                else:
                    hi = mid
            chk('land-pattern conflict %s unchanged' % ref,
                'widest legal escape %.3f mm vs floor %.2f mm' % (best / 1e6, floor / 1e6),
                best == proved and best < floor)

        # ---- G7  SPLIT / REVERT INDEX ARITHMETIC (PR-15) ------------------
        #
        # split_at() replaces ONE track in qb.laid with TWO.  A mark taken
        # before the split is an index into that list, so every mark after the
        # split point is now off by one.  Reverting with a stale mark removed a
        # track belonging to the TRUNK and left one of the branch's own behind;
        # doing it twice on the same trunk called BOARD::Remove on an item that
        # was no longer in the list, which SEGFAULTS the interpreter rather than
        # raising.  That crash killed the first FBV2-P2-002E Phase A run at
        # BAT_CONNECTOR_P TP34.1 after 55 connections.
        #
        # The guard is arithmetic, not a crash test: lay copper, mark, split an
        # EARLIER track, undo the split, revert, and require the board and the
        # laid list to be exactly what they were.
        qb = QR.QBoard(scratch)
        net = '/01_POWER_TREE/BAT_CONNECTOR_P'
        nid = qb.b.FindNet(net)
        LID = qb.b.GetLayerID('B.Cu')

        def lay(x0, y0, x1, y1):
            t = pcbnew.PCB_TRACK(qb.b)
            t.SetStart(pcbnew.VECTOR2I(x0, y0))
            t.SetEnd(pcbnew.VECTOR2I(x1, y1))
            t.SetWidth(250000)
            t.SetLayer(LID)
            t.SetNet(nid)
            qb.b.Add(t)
            qb.laid.append(t)
            return t

        trunk = lay(20000000, 30000000, 30000000, 30000000)
        n0 = len(qb.laid)
        before = len(list(qb.b.GetTracks()))
        m = qb.mark()
        branch = lay(25000000, 30000000, 25000000, 34000000)
        at = qb.laid.index(trunk)
        made = RU.split_at(qb.b, trunk, 25000000, 30000000)
        chk('G7 split produced two halves', '%d halves' % len(made), len(made) == 2)
        qb.laid[at:at + 1] = made
        m2 = (m[0] + len(made) - 1, m[1], m[2]) if m[0] > at else m
        chk('G7 shifted mark still points at the branch',
            'laid[%d] is the branch' % m2[0],
            m2[0] < len(qb.laid) and qb.laid[m2[0]] is branch)
        # undo the split, then revert
        for t in made:
            qb.b.Remove(t)
        qb.laid[at:at + len(made)] = [trunk]
        m3 = (m2[0] - (len(made) - 1), m2[1], m2[2]) if m2[0] > at else m2
        qb.b.Add(trunk)
        qb.revert(m3)
        chk('G7 laid list restored exactly',
            '%d laid, expected %d' % (len(qb.laid), n0), len(qb.laid) == n0)
        chk('G7 trunk survived the undo', 'trunk is laid[%d]' % at,
            at < len(qb.laid) and qb.laid[at] is trunk)
        chk('G7 board track count restored',
            '%d tracks, expected %d' % (len(list(qb.b.GetTracks())), before),
            len(list(qb.b.GetTracks())) == before)
        # the halves must NOT still be on the board, and a second revert with
        # the ORIGINAL (unshifted) mark must not be reachable any more
        live = {id(t) for t in qb.b.GetTracks()}
        chk('G7 split halves removed from the board',
            '%d of 2 still present' % sum(1 for t in made if id(t) in live),
            not any(id(t) in live for t in made))

        print('')
        if FAILED:
            print('router_regression: %d CHECK(S) FAILED' % len(FAILED))
            for f in FAILED:
                print('   - %s' % f)
            return 1
        print('router_regression: ALL CHECKS PASS')
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    raise SystemExit(main())
