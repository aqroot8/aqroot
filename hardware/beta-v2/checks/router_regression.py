# -*- coding: utf-8 -*-
"""FBV2-P2-002B -- router qualification regression test.

Run with KiCad's own Python:

    python hardware/beta-v2/checks/router_regression.py

(any interpreter that can import pcbnew -- KiCad's bundled python.exe on the
Windows machine, the venv python on the Ubuntu worker)

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
import io, os, sys, json, shutil, subprocess, collections, math, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness_paths as HP

# FBV2-CLOUD-001: repository, project and kicad-cli all come from the shared
# resolution policy now.  The old KICAD_CLI default was a Windows drive-letter
# path, so an unset variable on Linux produced a kicad-cli that does not exist
# -- and subprocess.run(capture_output=True) swallowed the failure, leaving the
# DRC json missing rather than reporting why.
REPO = HP.REPO_ROOT
PRJ = HP.project_dir()
PCBNAME = HP.PCBNAME
NEEDED = HP.PROJECT_CONTEXT

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

SP_DIR = os.path.dirname(os.path.abspath(__file__))
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
    subprocess.run([HP.kicad_cli(), 'pcb', 'drc', '--severity-all', '--format', 'json',
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

        # ---- G8: PR-39, ROUTER SUCCESS MUST MEAN REAL CONNECTIVITY -------
        #
        # FBV2-P2-002F reported `BAT_RAW R79.1 -> R80.1` as routed at 5.276 mm
        # across a 12.030 mm gap, with ZERO track endpoints in R80.1's pad and
        # R80.1 alone in its own copper component.  The node fallback had
        # retargeted silently while the log line, the journal and the routed
        # count all kept the requested pair.  These cases pin the contract:
        # a route is SUCCESS only if the REQUESTED pads end up connected.
        print('')
        print('  -- G8 PR-39 router truth ------------------------------------')
        import net_ledger as NL

        def connected(pcb_, net_, a_, b_):
            """Requested-pad connectivity, judged on a SAVED AND RELOADED board."""
            bd = pcbnew.LoadBoard(pcb_)
            bd.BuildConnectivity()
            cn_ = bd.GetConnectivity()
            pp = {}
            for f_ in bd.GetFootprints():
                for q_ in f_.Pads():
                    pp[f_.GetReference() + '.' + q_.GetNumber()] = q_
            if a_ not in pp or b_ not in pp:
                return None
            grp = {str(i.m_Uuid.AsString()) for i in cn_.GetConnectedItems(pp[a_])}
            return str(pp[b_].m_Uuid.AsString()) in grp

        NBR = '/01_POWER_TREE/BAT_RAW'
        pcb8 = fresh(work, 'G8')
        qb8 = QR.QBoard(pcb8)
        qb8.wide_nets = frozenset([NBR])

        # TEST A -- a named pair that routes directly is SUCCESS, and the
        # requested pads really are connected afterwards.
        pa = qb8.pads.get((NBR, 'F1.2'))
        pb = qb8.pads.get((NBR, 'Q2.8'))
        ra = QR.connect_role(qb8, NBR, pa, pb, 'B', 1000000, 200000, 300000)
        qb8.save()
        ca = connected(pcb8, NBR, 'F1.2', 'Q2.8')
        chk('G8-A direct named pair routes and connects',
            'ok=%s connected=%s' % (ra['ok'], ca), bool(ra['ok']) and ca is True)

        # TEST B -- a fallback that lands on same-net copper and GENUINELY
        # joins the requested pads is still SUCCESS.
        pc = qb8.pads.get((NBR, 'Q2.7'))
        rb = QR.connect_role(qb8, NBR, pc, pa, 'B', 800000, 200000, 300000)
        qb8.save()
        cb = connected(pcb8, NBR, 'Q2.7', 'F1.2')
        chk('G8-B fallback that truly joins is SUCCESS',
            'ok=%s connected=%s' % (rb['ok'], cb), bool(rb['ok']) and cb is True)

        # TEST C -- the defect itself.  Route a pad to a POINT on its own net
        # that does not reach the requested end; the router reports ok, and the
        # contract must still call the REQUESTED pair NOT CONNECTED.
        pcb8c = fresh(work, 'G8C')
        qb8c = QR.QBoard(pcb8c)
        qb8c.wide_nets = frozenset([NBR])
        src = qb8c.pads.get((NBR, 'F1.2'))
        far = qb8c.pads.get((NBR, 'R80.1'))
        e = qb8c.escape(src, 'B', 600000, 600000, 200000, 300000, 50000,
                        qb8c.ex0, qb8c.ey0)
        laid = False
        if e:
            qb8c.track(NBR, 'B', src['x'], src['y'], e[0]['x'], e[0]['y'], 600000)
            laid = True
        qb8c.save()
        cc = connected(pcb8c, NBR, 'F1.2', 'R80.1')
        chk('G8-C copper laid but requested end isolated -> NOT CONNECTED',
            'laid=%s requested_connected=%s' % (laid, cc), laid and cc is False)

        # TEST D -- the journal must carry requested AND actual endpoints.
        # READ the driver's source; do NOT import it.  route_battery_block.py
        # calls main() at module level, so importing it starts a Phase A run.
        src_txt = io.open(os.path.join(SP_DIR, 'route_battery_block.py'),
                          encoding='utf-8').read()
        has_fields = all(k in src_txt for k in
                         ('requested_a=', 'requested_b=', 'actual_a=',
                          'actual_b=', 'requested_connected='))
        gated = 'PR-39 requested pads NOT' in src_txt
        chk('G8-D journal records requested AND actual endpoints',
            'fields=%s rejection_path=%s' % (has_fields, gated),
            has_fields and gated)

        # TEST E -- a save/reload preserves the verdict.
        ca2 = connected(pcb8, NBR, 'F1.2', 'Q2.8')
        cc2 = connected(pcb8c, NBR, 'F1.2', 'R80.1')
        chk('G8-E save/reload preserves the connectivity verdict',
            'A %s->%s   C %s->%s' % (ca, ca2, cc, cc2),
            ca2 == ca and cc2 == cc)

        # TEST F -- the ledger, which is what Phase A/B are judged on, must
        # report the isolated case as NOT fully connected.
        lg = NL.ledger(pcb8c)
        br = lg['nets']['BAT_RAW']
        chk('G8-F ledger reports the isolated net as unconnected',
            '%d islands, connected=%s' % (br['islands'], br['connected']),
            br['islands'] > 1 and br['connected'] is False)

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
