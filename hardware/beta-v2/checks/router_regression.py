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
# FBV2-P2-004B2 / D-302 re-pin: the first Phase-A copper promotion also lands the
# ACCEPTED direction-2 placement, which MOVES U18 (HEAD (3.0,72.4) rot 90 deg ->
# authoritative (8.0,66.5) rot 180 deg).  Re-measured at U18's authoritative pose
# on the copper-clean scratch fixture, U18.8 / U18.9 admit 0.245 mm (was 0.250 mm
# at the old pose) -- STILL far below their 1.20 / 0.60 mm floors, so both remain
# NO-LEGAL-ESCAPE: the land-pattern conflict is PRESERVED, only the pinned widest-
# escape tracks the accepted placement (this is a placement re-pin, not a rule
# relaxation).  U14.2/U14.3/U11.2 did not move and are unchanged (0.240/0.200 mm).
CONFLICTS = {
    'U18.9': (N + 'BAT_SENSE',       600000,  245000),   # D-302: U18 moved
    'U18.8': (N + 'BAT_PROTECTED_P', 1200000, 245000),   # D-302: U18 moved
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
    """A FAITHFUL scratch copy of the authoritative project -- it carries
    WHATEVER copper the authoritative board currently holds (zero tracks before
    the first Phase-A promotion, the promoted routed copper after it).  Use this
    for checks that must validate the REAL authoritative state (the G1 project-
    context copy, the G10 concurrency baseline that equals the authoritative DRC,
    the real-DRC / probe / judge harnesses)."""
    dst = os.path.join(work, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(PRJ, dst)
    return os.path.join(dst, PCBNAME)


def scratch_clean(work, name):
    """A copper-CLEAN scratch fixture for the primitive router unit/regression
    vehicles (CASES G2-G6, the CONFLICTS bisection, G7, G8, G9, G11, G12).

    Those vehicles lay a handful of tracks FROM SCRATCH and then assert exact
    ratsnest-fall, exact DRC-delta and requested-pad connectivity, so they
    implicitly assume a copper-EMPTY base.  Before the first Phase-A copper
    promotion the authoritative board WAS copper-empty and fresh() sufficed; the
    moment real routed copper is promoted a plain copy carries it and those
    primitives (correctly, for the wrong reason) trip -- a bisection escape hits
    routed copper, a "route this pair" is already connected, a rejected-rung
    board is not empty.  That is fixture coupling, not a routing regression.

    This derives the fixture from the SAME placement / footprints / GND copper
    zones / rule areas / DRU+pro rule context as the authoritative board and
    removes ONLY the routed copper (every PCB_TRACK / PCB_ARC / PCB_VIA) in the
    SCRATCH COPY.  The authoritative file is NEVER mutated (fresh() copies out of
    PRJ; we edit only the copy).  Footprints, the GND zones, the 4 authored
    DoNotAllowTracks keep-outs and the routing annotation rule areas all stay, so
    qrouter sees the identical obstacle set it saw on the pre-promotion board
    (qrouter only treats PCB_TRACK and DoNotAllowTracks rule areas as obstacles)
    and DRC still measures against the real, promoted rule set.  It does NOT hide
    copper from any check meant to validate the promoted authoritative board --
    those use fresh() / the authoritative file directly (see G1, G10, G17).

    The strip is done on the .kicad_pcb TEXT, not through pcbnew: board-level
    `(segment ...)`, `(via ...)` and `(arc ...)` are the only routed-copper
    s-expressions, they are emitted at exactly one tab of indentation, and
    removing whole balanced lists leaves a valid board.  (Mutating + re-saving a
    board through pcbnew's SWIG bindings to delete tracks is both slow and, on
    this KiCad build, prone to a teardown segfault -- the text strip is
    deterministic and side-effect free, so every clean fixture is identical.)"""
    dst = fresh(work, name)
    txt = io.open(dst, encoding='utf-8').read()
    out, i, n = [], 0, len(txt)
    heads = ('\t(segment', '\t(via', '\t(arc')
    while i < n:
        nl = txt.find('\n', i)
        line_end = n if nl < 0 else nl + 1
        line = txt[i:line_end]
        if any(line.startswith(h + '\n') or line.startswith(h + ' ')
               for h in heads):
            # drop this whole balanced (paren) list, however many lines it spans
            # (quote-aware: never count a paren that sits inside a "string").
            depth, j, instr = 0, txt.index('(', i), False
            while j < n:
                c = txt[j]
                if instr:
                    if c == '\\':
                        j += 2
                        continue
                    if c == '"':
                        instr = False
                elif c == '"':
                    instr = True
                elif c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                j += 1
            # also swallow the trailing newline so no blank line is left
            if j < n and txt[j] == '\n':
                j += 1
            i = j
            continue
        out.append(line)
        i = line_end
    io.open(dst, 'w', encoding='utf-8', newline='').write(''.join(out))
    return dst


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
        import hashlib
        auth = os.path.join(PRJ, PCBNAME)
        # Snapshot the authoritative file BEFORE any fixture is built, so G17 can
        # prove building the clean fixtures never mutated it.
        AUTH_HASH0 = hashlib.sha256(io.open(auth, 'rb').read()).hexdigest()
        AUTH_STAT0 = os.stat(auth)
        base_a = drc(auth, 'auth', work)
        # G1 validates that a plain project COPY carries the full rule context
        # (.kicad_dru / .kicad_pro netclasses / fp-lib-table / libraries) so DRC
        # cannot silently fall back to KiCad DEFAULTS.  It must therefore compare
        # a FAITHFUL copy of the authoritative board -- WHATEVER copper it now
        # carries -- against the authoritative DRC: identical copper, identical
        # rules, identical histogram.  (Post-promotion this copy carries the
        # promoted routed copper, exactly as intended.)
        ctx = fresh(work, 'ctx')
        chk('G1 scratch carries the full project context',
            'dru + pro + fp-lib-table + libraries present',
            not project_context(ctx))
        base_ctx = drc(ctx, 'ctx', work)
        chk('G1 faithful project copy DRC == authoritative DRC',
            '%s' % dict(sorted(base_ctx.items())), base_a == base_ctx)
        # The primitive router vehicles below (CASES G2-G6, the CONFLICTS
        # bisection, G7) lay a few tracks from scratch and assert EXACT
        # ratsnest-fall / DRC-delta, so they need a copper-CLEAN base.  Derive it
        # from the same placement/zones/rules with the routed copper stripped;
        # base_s is the delta reference, base_rn the ratsnest-fall reference.
        scratch = scratch_clean(work, 'base')
        base_s = drc(scratch, 'base', work)
        base_rn = ratsnest(scratch)

        # ---- G2..G6 per routed case --------------------------------------
        for title, net, spec, pairs in CASES:
            tag = title.split()[0]
            pcb = scratch_clean(work, tag)     # primitive route -> copper-clean base
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
        pcb8 = scratch_clean(work, 'G8')       # primitive route -> copper-clean base
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
        pcb8c = scratch_clean(work, 'G8C')     # primitive route -> copper-clean base
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

        # ---- G9  PR-49 WIDTH-LADDER SEMANTICS ----------------------------
        #
        # A width ladder is not a ladder until the GATE has spoken.  Until
        # FBV2-P2-002Q the driver treated a rung as accepted the moment
        # connect_role() returned geometrically ok, and ran DRC afterwards - so
        # a rung that routed and was then REJECTED abandoned the whole
        # connection and the remaining authorised rungs were never tried.
        #
        # FBV2-P2-002P is the case that proves the cost:
        # `BAT_PROTECTED_P R75.2 -> D9.1` routed at 1.50 mm, failed
        # `copper_edge_clearance 0.5000 mm; actual 0.4125 mm`, and stopped -
        # while PLAN_1_BPP_TRUNK carries [1.50, 1.20] exactly so the trunk can
        # fall to its D-249 floor, and 1.20 mm was legal at that pose.
        #
        # This pins the semantics AND the safety boundary: the retry only ever
        # walks the ladder it was given, so it can never take a net below its
        # standing floor.
        print('')
        print('  -- G9 PR-49 width-ladder semantics ---------------------------')
        import route_battery_block as RB

        LAD = [1500000, 1200000]
        seen = []

        def first_rung_gate_rejected(lad):
            seen.append(tuple(lad))
            if lad[0] == 1500000:
                return False, 1500000      # routed, then rejected by the gate
            return True, None              # 1.20 mm passes

        got = RB.ladder_retry(LAD, first_rung_gate_rejected)
        chk('G9 gate-rejected rung falls to the next authorised rung',
            'accepted=%s, tried %s' % (got, [[w / 1e6 for w in c] for c in seen]),
            got is True and len(seen) == 2 and seen[1] == (1200000,))
        chk('G9 the retry never invents a rung below the ladder',
            'rungs offered %s' % sorted({w for c in seen for w in c}),
            sorted({w for c in seen for w in c}) == sorted(LAD))

        seen2 = []

        def every_rung_gate_rejected(lad):
            seen2.append(tuple(lad))
            return False, lad[0]

        got2 = RB.ladder_retry(LAD, every_rung_gate_rejected)
        chk('G9 every rung rejected leaves the connection failed',
            'accepted=%s after %d attempt(s)' % (got2, len(seen2)),
            got2 is False and len(seen2) == 2)

        seen3 = []

        def not_a_gate_failure(lad):
            seen3.append(tuple(lad))
            return False, None             # NO_PATH / NO_LEGAL_ESCAPE

        got3 = RB.ladder_retry(LAD, not_a_gate_failure)
        chk('G9 a non-gate failure does not walk the ladder',
            'accepted=%s after %d attempt(s)' % (got3, len(seen3)),
            got3 is False and len(seen3) == 1)

        # And the board-state half of the rule: a rejected rung must leave NO
        # copper behind.  Measured on a real board rather than asserted.
        pcb9 = scratch_clean(work, 'G9')       # primitive route -> copper-clean base
        qb9 = QR.QBoard(pcb9)
        qb9.wide_nets = frozenset(N + x for x in
                                  ('BAT_CONNECTOR_P', 'BAT_RAW', 'BAT_MID',
                                   'BAT_SENSE', 'BAT_PROTECTED_P'))
        P9 = {}
        for (nt, rf), pd in qb9.pads.items():
            P9.setdefault(rf, pd)
        n9 = N + 'BAT_MID'
        before_tracks = len([t for t in qb9.b.GetTracks()])
        before_laid = len(qb9.laid)
        m9 = qb9.mark()
        r9 = QR.connect_role(qb9, n9, P9['Q2.6'], P9['Q3.8'], 'B',
                             1000000, 200000, 300000)
        mid_tracks = len([t for t in qb9.b.GetTracks()])
        qb9.revert(m9)
        chk('G9 a rejected rung leaves no copper on the board',
            '%d -> %d -> %d tracks, laid %d -> %d'
            % (before_tracks, mid_tracks,
               len([t for t in qb9.b.GetTracks()]), before_laid, len(qb9.laid)),
            r9['ok'] and mid_tracks > before_tracks
            and len([t for t in qb9.b.GetTracks()]) == before_tracks
            and len(qb9.laid) == before_laid)

        # ---- G10  FBV2-P2-002Z CONCURRENCY-SAFE DRC TRANSIENT ------------
        #
        # RU.drc() writes a transient json, reads it straight back, and uses it
        # nowhere else -- but the tag ("Abase"/"A"/"Afinal") is FIXED per phase.
        # The placement SEARCH runs many route_battery_block prefixes at once,
        # all sharing checks/w as WORK, so two runs in the same phase wrote the
        # SAME drc_Abase.json and one json.load() read a half-written file
        # ("Unterminated string ... "), crashing that prefix at random.
        #
        # The fix makes the transient path process-unique and removes it after
        # the read, changing NO routing result and NO single-run output.  This
        # guard is the collision itself: TWO processes call RU.drc with the same
        # tag on a shared WORK at the same time; both must return the exact
        # authoritative baseline histogram, and neither may raise.
        print('')
        print('  -- G10 FBV2-P2-002Z concurrency-safe DRC transient ----------')
        # source contract: the transient path is process-unique and reclaimed.
        ru_src = io.open(os.path.join(SP_DIR, 'path_role_util.py'),
                         encoding='utf-8').read()
        pid_unique = 'os.getpid()' in ru_src and 'drc_%s_%d.json' in ru_src
        reclaimed = 'os.remove(out)' in ru_src
        chk('G10 DRC transient path is process-unique and reclaimed',
            'pid_unique=%s reclaimed=%s' % (pid_unique, reclaimed),
            pid_unique and reclaimed)

        # behavioural collision: two processes, one shared WORK, same FIXED tag.
        worker = os.path.join(work, 'g10_worker.py')
        io.open(worker, 'w', encoding='utf-8').write(
            'import os, sys, json\n'
            'sys.path.insert(0, %r)\n'
            'import path_role_util as RU\n'
            'work = sys.argv[1]\n'
            'pcb = RU.fresh(work, "g10_" + str(os.getpid()))\n'
            'c, _ = RU.drc(pcb, "Abase", work)\n'
            'sys.stdout.write(json.dumps(dict(sorted(c.items()))))\n'
            % SP_DIR)
        shared = os.path.join(work, 'g10_shared')
        os.makedirs(shared, exist_ok=True)
        procs = [subprocess.Popen([sys.executable, worker, shared],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True) for _ in range(2)]
        outs = [p.communicate() for p in procs]
        rcs = [p.returncode for p in procs]
        base_hist = dict(sorted(base_a.items()))
        parsed, crash = [], ''
        for (o, e), rc in zip(outs, rcs):
            if rc != 0:
                crash = crash or (e.strip().splitlines() or [''])[-1]
            try:
                parsed.append(json.loads(o))
            except ValueError:
                parsed.append(None)
                crash = crash or 'unparseable DRC json (torn transient)'
        chk('G10 concurrent same-tag DRC does not clobber the transient',
            'rcs=%s %s' % (rcs, ('crash: ' + crash) if crash else 'both clean'),
            rcs == [0, 0] and not crash)
        chk('G10 both concurrent runs read the authoritative baseline histogram',
            '%s' % parsed,
            all(p == base_hist for p in parsed))
        # no transient may survive in the shared WORK after the read.
        leftover = [f for f in os.listdir(shared) if f.startswith('drc_')]
        chk('G10 no DRC transient left behind in shared WORK',
            leftover or 'none', not leftover)

        # ---- G11  FBV2-P2-003A BOUNDED-PROBE SEARCH CONTRACT ------------
        #
        # D-273's long-corridor probe caps QR.ASTAR_BUDGET / QR.WAVE_BUDGET so a
        # single unreachable hop gives up instead of exploring the whole board
        # (the >18-min trap the un-bounded first draft hit).  A FAIL reported by
        # that probe is only trustworthy if the cap does two things at once:
        #   1. it must actually BOUND the search -- a tiny budget must turn a
        #      genuinely routable trunk into a prompt give-up (NO_PATH) that lays
        #      NO copper, never a hang;
        #   2. it must NOT FABRICATE a FAIL -- the budget the probe actually uses
        #      (ASTAR=60000 / WAVE=1200) must still route a trunk that routes at
        #      the full default budget, so a bounded-budget FAIL is a real block
        #      and not a starved search.
        # Both are checked here on the authoritative board with a short routable
        # trunk, so the guarantee the D-273 measurement rests on is pinned in CI
        # even though the c3 scratch board it measured is not committed.  The
        # module budgets are saved and restored so no other check is perturbed.
        print('')
        print('  -- G11 FBV2-P2-003A bounded-probe search contract ----------')
        save_astar, save_wave = QR.ASTAR_BUDGET, QR.WAVE_BUDGET
        try:
            g11 = scratch_clean(work, 'g11')   # primitive probe -> copper-clean base
            qb11 = QR.QBoard(g11)
            net11 = N + 'Q2_CS'
            pa = qb11.pads.get((net11, 'Q2.3'))
            pb = qb11.pads.get((net11, 'Q2.1'))
            outcomes = {}
            for label, (ab, wb) in (('full', (500000, 3000)),
                                    ('tiny', (1, 1)),
                                    ('probe', (60000, 1200))):
                QR.ASTAR_BUDGET, QR.WAVE_BUDGET = ab, wb
                m11 = qb11.mark()
                before = len([t for t in qb11.b.GetTracks()])
                try:
                    r = QR.connect_role(qb11, net11, pa, pb, 'B',
                                        SIG['w'], SIG['cp'], SIG['ct'])
                    raised = None
                except Exception as e:               # a bounded give-up must not raise
                    r, raised = {}, '%s: %s' % (type(e).__name__, e)
                laid = len([t for t in qb11.b.GetTracks()]) - before
                qb11.revert(m11)
                outcomes[label] = dict(ok=bool(r.get('ok')),
                                       reason=r.get('reason'), laid=laid,
                                       raised=raised)
        finally:
            QR.ASTAR_BUDGET, QR.WAVE_BUDGET = save_astar, save_wave
        full_ok = outcomes['full']['ok'] and outcomes['full']['laid'] > 0
        chk('G11 short trunk routes at the full default budget',
            'ok=%s laid=%s' % (outcomes['full']['ok'], outcomes['full']['laid']),
            full_ok)
        t = outcomes['tiny']
        chk('G11 a tiny budget BOUNDS the search (give-up, no copper, no raise)',
            'ok=%s reason=%s laid=%s raised=%s'
            % (t['ok'], t['reason'], t['laid'], t['raised']),
            (not t['ok']) and t['reason'] == 'NO_PATH' and t['laid'] == 0
            and t['raised'] is None)
        p = outcomes['probe']
        chk('G11 the 003A probe budget does NOT fabricate a FAIL',
            'ok=%s laid=%s (ASTAR=60000 WAVE=1200 still routes the trunk)'
            % (p['ok'], p['laid']),
            p['ok'] and p['laid'] > 0)
        chk('G11 module search budgets restored after the probe',
            'ASTAR=%d WAVE=%d' % (QR.ASTAR_BUDGET, QR.WAVE_BUDGET),
            QR.ASTAR_BUDGET == save_astar and QR.WAVE_BUDGET == save_wave)

        # ---- G12  FBV2-P2-003M / D-286 BASELINE-ORDER CONTRACT ----------
        #
        # route_battery_block.py measures the DRC/ratsnest baseline the routing
        # gates subtract against.  Through 003L that baseline was taken after the
        # 002F ECO (+AQROOT_ECO_EXTRA) but BEFORE AQROOT_PLACE_JSON moved the
        # candidate footprints, so a placement that itself carried DRC items
        # (courtyards_overlap / solder_mask_bridge / shorting_items / clearance)
        # was NOT in the baseline.  Every gate then read those placement items as
        # brand-new copper violations and rejected unrelated nets -- the 003M
        # DRIVER_EXIT=143 cascade.  The gate delta is `after - base` excluding
        # unconnected_items (route_battery_block ~L477/L836); this pins that the
        # baseline must reflect the ACTUAL candidate placement, and that a
        # violation appearing AFTER the baseline boundary (from copper) is still
        # surfaced.  The driver source order is asserted too, so the pre-placement
        # ordering fails this test if it ever returns.
        print('')
        print('  -- G12 FBV2-P2-003M/D-286 baseline-order contract ----------')

        def _delta(after, base):        # driver gate semantics, verbatim
            return dict((k, v - base.get(k, 0)) for k, v in after.items()
                        if v > base.get(k, 0) and k != 'unconnected_items')

        g12 = scratch_clean(work, 'g12')             # placement test -> clean base
        base_pre = drc(g12, 'g12pre', work)          # OLD-order baseline (pre-place)
        rn_pre = ratsnest(g12)
        # A candidate placement that induces a placement-derived DRC item, the
        # way c3_00/place_003l did on the real board: stack C5 onto C36 so their
        # courtyards overlap.  Mirrors the driver's AQROOT_PLACE_JSON apply path
        # (move -> BuildConnectivity -> ZONE_FILLER.Fill -> Save).
        _bb = pcbnew.LoadBoard(g12)
        _fp = {f.GetReference(): f for f in _bb.GetFootprints()}
        _c36, _c5 = _fp.get('C36'), _fp.get('C5')
        chk('G12 candidate placement refs C36/C5 present',
            'C36=%s C5=%s' % (_c36 is not None, _c5 is not None),
            _c36 is not None and _c5 is not None)
        if _c36 is not None and _c5 is not None:
            _c5.SetPosition(_c36.GetPosition())      # deterministic courtyard overlap
            _bb.BuildConnectivity()
            pcbnew.ZONE_FILLER(_bb).Fill(_bb.Zones())
            _bb.Save(g12)
            base_post = drc(g12, 'g12post', work)    # NEW-order baseline (post-place)

            # (1) The placement is DECISIVE: it moves the DRC histogram in a
            #     placement-derived class, so WHICH baseline is used matters.
            induced = _delta(base_post, base_pre)
            chk('G12 candidate placement induces a placement-derived DRC delta',
                'induced=%s' % (induced or 'NONE'),
                bool(induced))

            # (2) OLD ORDER (pre-placement baseline) would spuriously flag the
            #     placement items on a legal, copper-free routed start.  A routed
            #     start that laid NO offending copper still equals base_post, so
            #     old-order delta = the induced placement items = a false gate hit.
            after_legal = collections.Counter(base_post)     # zero new copper
            old_delta = _delta(after_legal, base_pre)
            chk('G12 OLD pre-placement order FALSELY flags the placement (the bug)',
                'old_delta=%s' % (old_delta or 'NONE'),
                bool(old_delta) and old_delta == induced)

            # (3) NEW ORDER (post-placement baseline) yields ZERO spurious delta
            #     for the same legal routed start -- the gate is now relative to
            #     the actual routed starting geometry.
            new_delta = _delta(after_legal, base_post)
            chk('G12 NEW post-placement order yields ZERO spurious delta',
                'new_delta=%s' % (new_delta or 'NONE'),
                new_delta == {})

            # (4) A violation arising AFTER the baseline boundary (i.e. from
            #     copper the router lays) is STILL surfaced -- it cannot be
            #     hidden by absorbing placement into the baseline.
            after_copper = collections.Counter(base_post)
            after_copper['clearance'] += 1
            copper_delta = _delta(after_copper, base_post)
            chk('G12 a post-baseline copper violation is STILL surfaced',
                'copper_delta=%s' % copper_delta,
                copper_delta.get('clearance') == 1)

            # (5) ratsnest baseline is likewise measured on the placed board:
            #     the placement changed connectivity, so the reference ratsnest
            #     the gate subtracts must be the post-placement one.
            rn_post = ratsnest(g12)
            chk('G12 ratsnest baseline reflects the candidate placement',
                'rn_pre=%d rn_post=%d' % (rn_pre, rn_post),
                True)   # informational: both are recorded; gate uses rn_post

        # (6) DRIVER SOURCE ORDER: the baseline `RU.drc(pcb, "Abase"...)` must be
        #     computed AFTER the AQROOT_PLACE_JSON apply block AND after the
        #     placement fingerprint assertion, but before QBoard routing.  This
        #     fails the moment the pre-placement ordering is reintroduced.
        drv = open(os.path.join(SP_DIR, 'route_battery_block.py')).read()
        i_place = drv.find("_cand = os.environ.get('AQROOT_PLACE_JSON')")
        i_fp = drv.find('assert_placement')
        i_base = drv.find('base, _ = RU.drc(pcb, "Abase"')
        i_qboard = drv.find('qb = QR.QBoard(pcb)')
        chk('G12 driver anchors all found',
            'place=%d fingerprint=%d baseline=%d qboard=%d'
            % (i_place, i_fp, i_base, i_qboard),
            min(i_place, i_fp, i_base, i_qboard) > 0)
        chk('G12 driver baseline is AFTER candidate placement apply',
            'baseline@%d > place@%d' % (i_base, i_place),
            i_base > i_place)
        chk('G12 driver baseline is AFTER the fingerprint assertion',
            'baseline@%d > fingerprint@%d' % (i_base, i_fp),
            i_base > i_fp)
        chk('G12 driver baseline is BEFORE QBoard routing',
            'baseline@%d < qboard@%d' % (i_base, i_qboard),
            i_base < i_qboard)

        # ---- G13  FBV2-P2-003W / D-297  U18.8 I2-JOIN LEVER CONTRACT --------
        # The SECONDARY D-295 lever completes the BAT_PROTECTED_P U18.8->R75.2
        # reserve JOIN on In3 instead of the severed In2 lane.  This pins that
        # (a) In3 is a routable six-layer signal layer (the lever's premise),
        # (b) the lever is OFF by default -> byte-identical to every prior run,
        # (c) it activates only for I2/I3, and (d) it is scoped to exactly ONE
        # branch.  A future broadening of the gate or a flip of the default
        # trips this test and asks for a fresh ruling.
        print('  -- G13 FBV2-P2-003W/D-297 U18.8 I2-join lever ----------')
        chk('G13 In3 is a routable six-layer signal layer',
            'ROUTABLE[6]=%s' % (QR.ROUTABLE[6],),
            'I2' in QR.ROUTABLE[6] and 'I3' in QR.ROUTABLE[6])

        import importlib
        _saved = os.environ.pop('AQROOT_U18BPP_JOIN', None)
        try:
            import route_battery_block as RBB
            importlib.reload(RBB)
            off = RBB.U18BPP_JOIN
            chk('G13 lever OFF by default (byte-identical join layer=va[2])',
                'U18BPP_JOIN=%r active=%s' % (off, off in ('I2', 'I3')),
                off not in ('I2', 'I3'))
            os.environ['AQROOT_U18BPP_JOIN'] = 'I3'
            importlib.reload(RBB)
            chk('G13 AQROOT_U18BPP_JOIN=I3 activates the In3 join',
                'U18BPP_JOIN=%r' % (RBB.U18BPP_JOIN,),
                RBB.U18BPP_JOIN == 'I3')
            os.environ['AQROOT_U18BPP_JOIN'] = 'nonsense'
            importlib.reload(RBB)
            chk('G13 a non-I2/I3 value never activates the lever',
                'U18BPP_JOIN=%r active=%s'
                % (RBB.U18BPP_JOIN, RBB.U18BPP_JOIN in ('I2', 'I3')),
                RBB.U18BPP_JOIN not in ('I2', 'I3'))
        finally:
            if _saved is None:
                os.environ.pop('AQROOT_U18BPP_JOIN', None)
            else:
                os.environ['AQROOT_U18BPP_JOIN'] = _saved
            importlib.reload(RBB)

        src = io.open(os.path.join(HERE, 'route_battery_block.py'),
                      encoding='utf-8').read()
        # The override guard must name exactly this one branch and be gated on
        # the env flag and an I2/I3 layer -- nothing wider.
        scoped = ("net == N + 'BAT_PROTECTED_P'" in src
                  and "a == 'U18.8' and b_ == 'R75.2'" in src
                  and "U18BPP_JOIN in ('I2', 'I3')" in src)
        chk('G13 override is scoped to exactly BAT_PROTECTED_P U18.8->R75.2',
            'guard present=%s' % scoped, scoped)

        # -- G14 FBV2-P2-003X/D-298 U19 east-lane reservation lever ----------
        # The U19 capacity lever must be OFF by default (byte-identical: no
        # keep-out, ordinary DEADCELL close order), name the reserved-lane
        # geometry over the U19.7/U19.6 east row, and reorder ONLY when on.
        print('  -- G14 FBV2-P2-003X/D-298 U19 east-lane reservation lever ------')
        _s2 = os.environ.pop('AQROOT_U19CAP', None)
        try:
            importlib.reload(RBB)
            chk('G14 lever OFF by default (byte-identical: no reservation)',
                'U19CAP=%r' % (RBB.U19CAP,), RBB.U19CAP is False)
            os.environ['AQROOT_U19CAP'] = '1'
            importlib.reload(RBB)
            chk('G14 AQROOT_U19CAP activates the reservation',
                'U19CAP=%r' % (RBB.U19CAP,), RBB.U19CAP is True)
            # geometry: a keep-out over the U19 east row (x~4.7, y 27.55..28.95)
            ko = RBB.U19CAP_KO
            chk('G14 reserved-lane geometry spans U19.7 (y28.58) and U19.6 (y27.93)',
                'KO=%s' % (ko,),
                len(ko) == 5 and ko[1] <= 27930000 <= ko[3]
                and ko[1] <= 28580000 <= ko[3] and abs(ko[0] - 4700000) < 500000)
        finally:
            if _s2 is None:
                os.environ.pop('AQROOT_U19CAP', None)
            else:
                os.environ['AQROOT_U19CAP'] = _s2
            importlib.reload(RBB)
        # The lever is scoped: a KO keep-out (net=None), lifted at the '12b'
        # closure, and REC_BAT_LOW ordered before N_BATDIV -- nothing wider.
        u19_scoped = ("U19CAP" in src
                      and "'12b'" in src
                      and "N + 'REC_BAT_LOW'" in src
                      and "N + 'N_BATDIV'" in src)
        chk('G14 lever scoped to the U19 east lane + REC_BAT_LOW-before-N_BATDIV',
            'hooks present=%s' % u19_scoped, u19_scoped)

        # -- G15 FBV2-P2-004A/D-300 LTC_GATE U18.10->Q3.4 path-shaping lever ----
        # The join path-shaping keep-out must be OFF by default (byte-identical:
        # LTCGATE_KO empty, no keep-out installed), and when armed name a central-
        # lane keep-out on the far run layers that seals the squeeze-gap north of
        # the BAT_SENSE current-path track (y~62.5) so the D256_FCU connect_hop
        # crosses WEST.  It is a PATH-SHAPING capacity lever, not the D-300 pure
        # re-order (refuted): it physically blocks the rule-violating central lane
        # for exactly the ONE join and is lifted immediately after.
        print('  -- G15 FBV2-P2-004A/D-300 LTC_GATE path-shaping lever ----------')
        _s3 = os.environ.pop('AQROOT_LTCGATE_KO', None)
        try:
            importlib.reload(RBB)
            chk('G15 lever OFF by default (byte-identical: no keep-out)',
                'LTCGATE_KO=%r' % (RBB.LTCGATE_KO,), RBB.LTCGATE_KO == [])
            os.environ['AQROOT_LTCGATE_KO'] = '1'
            importlib.reload(RBB)
            ko = RBB.LTCGATE_KO
            # default: 3 capsules on the far layers F/I2/I3, sealing the graze
            # gap north of the BAT_SENSE 1.0 mm track (x 2.8..5.4, y~62.05).
            lays = [k[0] for k in ko]
            geo = ko[0][1] if ko else (0, 0, 0, 0, 0)
            chk('G15 AQROOT_LTCGATE_KO=1 arms the validated default',
                'layers=%s geo=%s' % (lays, geo),
                lays == ['F', 'I2', 'I3']
                and geo[1] == geo[3] == 62500000            # y-latitude of the wall
                and geo[0] <= 2800000 and geo[2] >= 5400000  # spans the BAT_SENSE x
                and geo[4] > 0)
            os.environ['AQROOT_LTCGATE_KO'] = 'F:1.0,60.0,4.0,64.0,0.5'
            importlib.reload(RBB)
            chk('G15 an explicit LAYER:x0,y0,x1,y1,hw override parses',
                'LTCGATE_KO=%r' % (RBB.LTCGATE_KO,),
                RBB.LTCGATE_KO == [('F', (1000000, 60000000, 4000000,
                                          64000000, 500000))])
        finally:
            if _s3 is None:
                os.environ.pop('AQROOT_LTCGATE_KO', None)
            else:
                os.environ['AQROOT_LTCGATE_KO'] = _s3
            importlib.reload(RBB)
        # Scoped: a KO capsule (net=None), installed ONLY for LTC_GATE U18.10->
        # Q3.4 and LIFTED right after the join -- nothing else ever sees it.
        ltcgate_scoped = ("LTCGATE_KO" in src
                          and "it['a'] == 'U18.10'" in src
                          and "it['b'] == 'Q3.4'" in src
                          and "None, 'KO'" in src
                          and "keep-out(s) lifted after join" in src)
        chk('G15 lever scoped to exactly LTC_GATE U18.10->Q3.4, KO lifted after',
            'hooks present=%s' % ltcgate_scoped, ltcgate_scoped)

        # -- G16 FBV2-P2-004B/D-302 U11.2 BPP trunk-endpoint retarget lever ------
        # u11_escape's default cross-board U11.2->D9.1 trunk has no legal >=1.20 mm
        # corridor.  The retarget lever names the FAR endpoint: OFF -> 'D9.1'
        # (byte-identical), AQROOT_U11_RETARGET=1/AUTO -> 'C36.1' (the nearest
        # already->=1.20 mm-connected BPP node copper, landed by the bridge), and an
        # explicit pad ref overrides.  FBV2-P2-004B2 (no-casualty refinement): the
        # U11.2 0.20 mm SENSE closure is KEPT lever-on or off (the 004A requested-
        # connected set is preserved), so the wide C36.1 tap is a CURRENT-PATH
        # REINFORCEMENT between already-joined points, judged by reserve_gate(
        # state['rn'], allow_dangle=False) -- no new DRC class/count AND ratsnest
        # EXACTLY unchanged -- not gate()'s ratsnest-fall; its journal entry is
        # marked reinforcement (not counted as a made/requested connection).
        # Screened faithfully on the exact final-run 004A board: B.Cu 3.521 mm at
        # 1.50 mm min trunk width, ZERO new KiCad DRC classes, >=1.20 mm continuity
        # C36.1->bridge->R75.2.
        print('  -- G16 FBV2-P2-004B/D-302 U11.2 trunk-endpoint retarget lever ----')
        _s4 = os.environ.pop('AQROOT_U11_RETARGET', None)
        try:
            importlib.reload(RBB)
            chk('G16 lever OFF by default (byte-identical: far endpoint D9.1)',
                'U11_RETARGET=%r' % (RBB.U11_RETARGET,), RBB.U11_RETARGET == '')
            os.environ['AQROOT_U11_RETARGET'] = '1'
            importlib.reload(RBB)
            chk('G16 AQROOT_U11_RETARGET=1 retargets U11.2 to the C36.1 node',
                'U11_RETARGET=%r' % (RBB.U11_RETARGET,), RBB.U11_RETARGET == 'C36.1')
            os.environ['AQROOT_U11_RETARGET'] = 'C25.1'
            importlib.reload(RBB)
            chk('G16 an explicit node-copper pad ref overrides the landing',
                'U11_RETARGET=%r' % (RBB.U11_RETARGET,), RBB.U11_RETARGET == 'C25.1')
        finally:
            if _s4 is None:
                os.environ.pop('AQROOT_U11_RETARGET', None)
            else:
                os.environ['AQROOT_U11_RETARGET'] = _s4
            importlib.reload(RBB)
        # Scoped: the far endpoint is `tgt = U11_RETARGET or 'D9.1'` (default D9.1),
        # both the escape and connect_role use pads[net][tgt], the reinforcement
        # branch judges with reserve_gate(..., allow_dangle=False) and marks the
        # journal entry reinforcement -- and NOTHING skips the U11.2 SENSE closure
        # (the no-casualty refinement removed that hook).
        u11_scoped = ("U11_RETARGET" in src
                      and "tgt = U11_RETARGET or 'D9.1'" in src
                      and "pads[net][tgt]" in src
                      and "reserve_gate(state['rn'], allow_dangle=False) if reinforce"
                          " else gate()" in src
                      and "je['reinforcement'] = True" in src
                      and "U11_RETARGET and ref_ == 'U11.2'" not in src)
        chk('G16 lever scoped to far endpoint + reinforcement gate, SENSE kept',
            'hooks present=%s' % u11_scoped, u11_scoped)

        # -- G17 FBV2-P2-004B2/D-302 first-copper-promotion / clean-fixture ------
        # The first authoritative Phase-A copper promotion means the authoritative
        # board now CARRIES routed copper.  Two invariants must hold TOGETHER:
        #   (a) the primitive router vehicles (CASES G2-G6, the CONFLICTS
        #       bisection, G7, G8, G9, G11, G12) run on a copper-CLEAN scratch
        #       fixture -- zero tracks/vias -- so their exact ratsnest-fall /
        #       DRC-delta / connectivity contracts still MEAN what they meant on
        #       the pre-promotion empty board; and
        #   (b) the fixture is NON-DESTRUCTIVE and hides copper from NO check that
        #       is supposed to validate the promoted board -- the authoritative
        #       file is byte-for-byte unchanged, and G1's context copy, G10's
        #       concurrency baseline and the real-DRC/probe/judge harnesses all
        #       still see the real routed copper.
        # This is the standing guard that the harness fix is a fixture change, not
        # a test weakening: it fails the moment the clean fixture leaks copper,
        # the authoritative file is mutated, or the copper is hidden from the
        # authoritative-state checks.
        print('  -- G17 FBV2-P2-004B2/D-302 promotion / clean-fixture contract --')
        auth_hash1 = hashlib.sha256(io.open(auth, 'rb').read()).hexdigest()
        auth_stat1 = os.stat(auth)
        chk('G17 authoritative board file is unchanged by fixture building',
            'sha256 %s..%s stat(size=%d,mtime=%s)'
            % (auth_hash1[:8], auth_hash1[-8:], auth_stat1.st_size,
               auth_stat1.st_mtime == AUTH_STAT0.st_mtime),
            auth_hash1 == AUTH_HASH0
            and auth_stat1.st_size == AUTH_STAT0.st_size
            and auth_stat1.st_mtime == AUTH_STAT0.st_mtime)

        _ab = pcbnew.LoadBoard(auth)
        auth_trk = len([t for t in _ab.GetTracks() if t.GetClass() == 'PCB_TRACK'])
        auth_via = len([t for t in _ab.GetTracks() if t.GetClass() == 'PCB_VIA'])
        chk('G17 authoritative board may carry promoted Phase-A copper',
            '%d tracks / %d vias on the authoritative board' % (auth_trk, auth_via),
            auth_trk > 0 and auth_via > 0)

        cf = scratch_clean(work, 'g17_clean')
        _cb = pcbnew.LoadBoard(cf)
        cf_trk = len([t for t in _cb.GetTracks() if t.GetClass() == 'PCB_TRACK'])
        cf_via = len([t for t in _cb.GetTracks() if t.GetClass() == 'PCB_VIA'])
        cf_arc = len([t for t in _cb.GetTracks() if t.GetClass() == 'PCB_ARC'])
        chk('G17 clean scratch fixture carries zero tracks, arcs and vias',
            '%d tracks / %d arcs / %d vias' % (cf_trk, cf_arc, cf_via),
            cf_trk == 0 and cf_arc == 0 and cf_via == 0)

        # placement / layers / footprints / rules are PRESERVED in the fixture --
        # only routed copper was stripped.
        same_fp = len(_cb.GetFootprints()) == len(_ab.GetFootprints())
        same_lay = (_cb.GetCopperLayerCount() == _ab.GetCopperLayerCount() == 6)
        same_zone = _cb.GetAreaCount() == _ab.GetAreaCount()
        has_ctx = not project_context(cf)
        chk('G17 clean fixture keeps placement, layers, zones, rules',
            'fp %d==%d, layers=%d, zones %d==%d, dru/pro present=%s'
            % (len(_cb.GetFootprints()), len(_ab.GetFootprints()),
               _cb.GetCopperLayerCount(), _cb.GetAreaCount(),
               _ab.GetAreaCount(), has_ctx),
            same_fp and same_lay and same_zone and has_ctx)

        # the promoted copper is NOT hidden from the authoritative-state checks:
        # the authoritative DRC (base_a, also the G10 concurrency reference) is
        # measured on the routed file and is reproduced by the faithful copy
        # (base_ctx == base_a), and the authoritative ratsnest -- measured on the
        # real routed board -- has fallen BELOW the copper-clean fixture's exactly
        # because the promoted Phase-A copper is real and connected.
        auth_rn = ratsnest(auth)
        chk('G17 authoritative DRC/connectivity measured on the routed board',
            'auth ratsnest %d < clean ratsnest %d, auth tracks %d > clean %d, '
            'base_a==base_ctx=%s'
            % (auth_rn, base_rn, auth_trk, cf_trk, base_a == base_ctx),
            auth_rn < base_rn and auth_trk > cf_trk and base_a == base_ctx)

        # -- G18 FBV2-P2-006/D-304 first rest-of-board incremental increment ----
        # The FRONT_RGB indicator group (U23 expander -> R124/125/126) was routed
        # onto the promoted board by incremental_router.py as a genuine
        # no-casualty / no-new-DRC increment.  G18 pins that increment on the
        # authoritative board: the three nets are fully copper-connected, their
        # copper is legal (0.200 mm B.Cu, NO new via), and the increment is
        # ADD-ONLY -- every non-FRONT_RGB track is still the accepted D-302
        # Phase-A copper (432 tracks), vias unchanged at 54.
        print('  -- G18 FBV2-P2-006/D-304 rest-of-board incremental increment --')
        _g18 = pcbnew.LoadBoard(auth)
        _g18.BuildConnectivity()
        _cc = _g18.GetConnectivity()
        RGB = ('/08_BUTTONS_EXPANDERS/FRONT_RGB_R_N',
               '/08_BUTTONS_EXPANDERS/FRONT_RGB_G_N',
               '/08_BUTTONS_EXPANDERS/FRONT_RGB_B_N')
        rgb_trk = [t for t in _g18.GetTracks()
                   if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in RGB]
        other_trk = [t for t in _g18.GetTracks()
                     if t.GetClass() == 'PCB_TRACK' and t.GetNetname() not in RGB]
        all_via = [t for t in _g18.GetTracks() if t.GetClass() == 'PCB_VIA']
        rgb_via = [t for t in all_via if t.GetNetname() in RGB]

        def _pad(ref):
            r, num = ref.split('.')
            for f in _g18.GetFootprints():
                if f.GetReference() == r:
                    for p in f.Pads():
                        if p.GetNumber() == num:
                            return p
            return None

        conn_ok = True
        for a, b in (('U23.4', 'R124.1'), ('U23.5', 'R125.1'), ('U23.6', 'R126.1')):
            pa = _pad(a)
            joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                      for p in _cc.GetConnectedItems(pa) if p.GetClass() == 'PAD'}
            conn_ok = conn_ok and (b in joined)
        chk('G18 FRONT_RGB nets fully copper-connected on the authoritative board',
            'U23.4-R124.1, U23.5-R125.1, U23.6-R126.1 joined=%s' % conn_ok, conn_ok)

        legal = (all(t.GetLayerName() == 'B.Cu' and t.GetWidth() == 200000
                     for t in rgb_trk) and not rgb_via)
        chk('G18 FRONT_RGB copper is legal (0.200 mm B.Cu, no via)',
            '%d tracks, widths=%s, layers=%s, rgb vias=%d'
            % (len(rgb_trk),
               sorted({t.GetWidth() for t in rgb_trk}),
               sorted({t.GetLayerName() for t in rgb_trk}), len(rgb_via)),
            legal)

        # ADD-ONLY is proven generically against ALL rest-of-board increment nets
        # recorded in the shared journal (role=REST_INC), so this contract stays
        # true as later increments are promoted: the Phase-A copper (everything
        # that is NOT a rest-increment net) must remain exactly 432 tracks / 54
        # vias, and FRONT_RGB itself must remain exactly its 20 B.Cu tracks.
        _jr = json.load(io.open(os.path.join(SP_DIR, 'phaseA_journal.json'),
                                encoding='utf-8'))
        _inc_nets = {e['net'] for e in _jr if e.get('role') == 'REST_INC'}
        phaseA_trk = [t for t in _g18.GetTracks()
                      if t.GetClass() == 'PCB_TRACK' and t.GetNetname() not in _inc_nets]
        # Phase-A vias are the vias NOT owned by a rest-of-board increment net;
        # they must stay 54 even as later increments add their own vias (D-306
        # DISP_RST_N is the first, +1) -- so the contract counts phaseA_via, not
        # all_via, and stays green as the board grows.
        phaseA_via = [t for t in all_via if t.GetNetname() not in _inc_nets]
        addonly = (len(phaseA_trk) == 432 and len(phaseA_via) == 54 and len(rgb_trk) == 20)
        chk('G18 increment is ADD-ONLY (Phase-A 432 trk / 54 via preserved)',
            'phaseA=%d (exp 432), phaseA_vias=%d (exp 54), all_vias=%d, rgb tracks=%d (exp 20)'
            % (len(phaseA_trk), len(phaseA_via), len(all_via), len(rgb_trk)),
            addonly)

        # -- G19 FBV2-P2-007/D-305 second rest-of-board incremental increment ---
        # The ACC_3V3_CTL group (accelerometer 3V3 load-switch U20 local control:
        # ACC_3V3_EN + ACC_3V3_ILIM) was routed onto the D-304 promoted board by
        # incremental_router.py as a genuine no-casualty / no-new-DRC increment.
        # G19 pins that increment on the authoritative board: the two nets are
        # fully copper-connected, their copper is legal (0.200 mm B.Cu, NO via),
        # and the increment is ADD-ONLY -- the FRONT_RGB increment (20 tracks) is
        # untouched and the Phase-A copper is still exactly 432 tracks.
        print('  -- G19 FBV2-P2-007/D-305 rest-of-board incremental increment --')
        ACC = ('/ACC_3V3_EN', '/01_POWER_TREE/ACC_3V3_ILIM')
        acc_trk = [t for t in _g18.GetTracks()
                   if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in ACC]
        acc_via = [t for t in all_via if t.GetNetname() in ACC]

        conn_ok = True
        for a, b in (('U20.1', 'R98.1'), ('U20.1', 'TP26.1'),
                     ('TP26.1', 'U3.15'), ('U20.4', 'R97.1')):
            pa = _pad(a)
            joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                      for p in _cc.GetConnectedItems(pa) if p.GetClass() == 'PAD'}
            conn_ok = conn_ok and (b in joined)
        chk('G19 ACC_3V3_CTL nets fully copper-connected on the authoritative board',
            'U20.1-R98.1, U20.1-TP26.1, TP26.1-U3.15, U20.4-R97.1 joined=%s' % conn_ok,
            conn_ok)

        acc_legal = (all(t.GetLayerName() == 'B.Cu' and t.GetWidth() == 200000
                         for t in acc_trk) and not acc_via)
        chk('G19 ACC_3V3_CTL copper is legal (0.200 mm B.Cu, no via)',
            '%d tracks, widths=%s, layers=%s, acc vias=%d'
            % (len(acc_trk),
               sorted({t.GetWidth() for t in acc_trk}),
               sorted({t.GetLayerName() for t in acc_trk}), len(acc_via)),
            acc_legal)

        acc_addonly = (len(acc_trk) == 31 and len(rgb_trk) == 20
                       and len(phaseA_trk) == 432 and len(phaseA_via) == 54)
        chk('G19 increment is ADD-ONLY (FRONT_RGB 20 + Phase-A 432 preserved)',
            'acc=%d (exp 31), rgb=%d (exp 20), phaseA=%d (exp 432), phaseA_vias=%d (exp 54)'
            % (len(acc_trk), len(rgb_trk), len(phaseA_trk), len(phaseA_via)),
            acc_addonly)

        # -- G20 FBV2-P2-008/D-306 third rest-of-board incremental increment ----
        # The DISP_RST_N display-reset control net was routed onto the D-305
        # promoted board by incremental_router.py.  It is the FIRST increment to
        # use a via: R16.1<->J1.10 is a pure F.Cu run and J1.10<->U2.8 crosses
        # F<->B through ONE board-legal 0.60/0.30 Default-netclass through via,
        # whose barrel required re-pouring the In1/In4 GND planes for its
        # anti-pad.  G20 pins that increment on the authoritative board: the net
        # is fully copper-connected across the hop, its copper spans F.Cu AND
        # B.Cu with exactly one legal via, and the increment is ADD-ONLY -- the
        # RGB (20) and ACC (31) increments and Phase-A (432 trk / 54 via) are
        # untouched.
        print('  -- G20 FBV2-P2-008/D-306 rest-of-board incremental increment --')
        DISP = ('/DISP_RST_N',)
        disp_trk = [t for t in _g18.GetTracks()
                    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in DISP]
        disp_via = [t for t in all_via if t.GetNetname() in DISP]

        joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in _cc.GetConnectedItems(_pad('J1.10')) if p.GetClass() == 'PAD'}
        conn_ok = ('R16.1' in joined) and ('U2.8' in joined)
        chk('G20 DISP_RST_N fully copper-connected across the F/B hop',
            'J1.10 joined R16.1 & U2.8 = %s (%s)' % (conn_ok, sorted(joined)), conn_ok)

        disp_layers = {t.GetLayerName() for t in disp_trk}
        _v = disp_via[0] if disp_via else None
        disp_legal = (len(disp_trk) == 11 and len(disp_via) == 1
                      and {'F.Cu', 'B.Cu'} <= disp_layers
                      and all(t.GetWidth() == 200000 for t in disp_trk)
                      and _v is not None and _v.GetWidth(pcbnew.F_Cu) == 600000
                      and _v.GetDrill() == 300000
                      and _v.GetViaType() == pcbnew.VIATYPE_THROUGH)
        chk('G20 DISP_RST_N copper legal (0.200 F.Cu+B.Cu, one 0.60/0.30 through via)',
            '%d trk layers=%s, vias=%d dia=%s drill=%s'
            % (len(disp_trk), sorted(disp_layers), len(disp_via),
               _v.GetWidth(pcbnew.F_Cu) if _v else None,
               _v.GetDrill() if _v else None),
            disp_legal)

        disp_addonly = (len(disp_trk) == 11 and len(acc_trk) == 31 and len(rgb_trk) == 20
                        and len(phaseA_trk) == 432 and len(phaseA_via) == 54)
        chk('G20 increment is ADD-ONLY (RGB 20 + ACC 31 + Phase-A 432/54 preserved)',
            'disp=%d (exp 11), acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(disp_trk), len(acc_trk), len(rgb_trk), len(phaseA_trk), len(phaseA_via)),
            disp_addonly)

        # -- G21 FBV2-P2-009/D-307 fourth rest-of-board incremental increment ---
        # The BMI270 IMU I2C address-select strap BMI270_SDO_ADDR (R118.1 /
        # R119.2 / U4.1) was routed onto the D-306 promoted board by
        # incremental_router.py as a genuine no-casualty / no-new-DRC increment.
        # It is a pristine same-layer B.Cu multi-terminal net (3-pad, 2-edge MST)
        # that reuses the D-304/D-305 B.Cu mechanics byte-for-byte -- NO via, so
        # vias stay 55 and no GND plane is re-poured.  G21 pins that increment on
        # the authoritative board: the net is fully copper-connected, its copper
        # is legal (0.200 mm B.Cu, no via), and the increment is ADD-ONLY -- the
        # RGB (20), ACC (31) and DISP (11) increments and Phase-A (432 trk / 54
        # via) are untouched.
        print('  -- G21 FBV2-P2-009/D-307 rest-of-board incremental increment --')
        IMU = ('/05_I2C_DEVICES/BMI270_SDO_ADDR',)
        imu_trk = [t for t in _g18.GetTracks()
                   if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in IMU]
        imu_via = [t for t in all_via if t.GetNetname() in IMU]

        joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in _cc.GetConnectedItems(_pad('R119.2')) if p.GetClass() == 'PAD'}
        conn_ok = ('R118.1' in joined) and ('U4.1' in joined)
        chk('G21 BMI270_SDO_ADDR fully copper-connected (R118.1-R119.2-U4.1 one island)',
            'R119.2 joined R118.1 & U4.1 = %s (%s)' % (conn_ok, sorted(joined)), conn_ok)

        imu_legal = (len(imu_trk) == 8 and not imu_via
                     and all(t.GetLayerName() == 'B.Cu' and t.GetWidth() == 200000
                             for t in imu_trk))
        chk('G21 BMI270_SDO_ADDR copper legal (0.200 mm B.Cu, no via)',
            '%d tracks, widths=%s, layers=%s, imu vias=%d'
            % (len(imu_trk),
               sorted({t.GetWidth() for t in imu_trk}),
               sorted({t.GetLayerName() for t in imu_trk}), len(imu_via)),
            imu_legal)

        imu_addonly = (len(imu_trk) == 8 and len(disp_trk) == 11 and len(acc_trk) == 31
                       and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                       and len(phaseA_via) == 54)
        chk('G21 increment is ADD-ONLY (DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'imu=%d (exp 8), disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(imu_trk), len(disp_trk), len(acc_trk), len(rgb_trk),
               len(phaseA_trk), len(phaseA_via)),
            imu_addonly)

        # -- G22 FBV2-P2-010/D-308 fifth rest-of-board incremental increment ----
        # The front-panel RGB status-indicator COMPLETION: D-304 (FRONT_RGB)
        # routed the expander->resistor side (U23 -> R124/R125/R126, B.Cu); this
        # increment closes the SAME indicator on the LED-cathode side -- the far
        # pad of each series resistor (R124.2/R125.2/R126.2, B.Cu SMD) to the
        # matching cathode of D13 (MHPA3528RGBCT RGB LED, F.Cu SMD).  It is the
        # FIRST MULTI-VIA increment: the three nets are each a 2-pad CROSS-LAYER
        # net that closes with exactly ONE board-legal 0.60/0.30 Default through
        # via, so THREE independent vias are laid (the single-via-per-edge D-306
        # mechanic applied three times; connect_cross unchanged; In1/In4 GND
        # planes re-poured ONCE for all three anti-pads).  G22 pins that increment
        # on the authoritative board: each net is fully copper-connected across
        # its F/B hop, its copper spans F.Cu AND B.Cu at 0.200 mm with exactly
        # three legal 0.60/0.30 through vias, and the increment is ADD-ONLY --
        # the IMU (8), DISP (11), ACC (31) and RGB (20) increments and Phase-A
        # (432 trk / 54 via) are untouched.
        print('  -- G22 FBV2-P2-010/D-308 rest-of-board incremental increment --')
        RGBLED = ('Net-(D13-RK)', 'Net-(D13-GK)', 'Net-(D13-BK)')
        rgbled_trk = [t for t in _g18.GetTracks()
                      if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in RGBLED]
        rgbled_via = [t for t in all_via if t.GetNetname() in RGBLED]

        conn_ok = True
        for a, b in (('D13.4', 'R124.2'), ('D13.3', 'R125.2'), ('D13.2', 'R126.2')):
            joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                      for p in _cc.GetConnectedItems(_pad(a)) if p.GetClass() == 'PAD'}
            conn_ok = conn_ok and (b in joined)
        chk('G22 FRONT_RGB_LED nets fully copper-connected across their F/B hops',
            'D13.4-R124.2, D13.3-R125.2, D13.2-R126.2 joined=%s' % conn_ok, conn_ok)

        rgbled_layers = {t.GetLayerName() for t in rgbled_trk}
        rgbled_legal = (len(rgbled_trk) == 25 and len(rgbled_via) == 3
                        and {'F.Cu', 'B.Cu'} <= rgbled_layers
                        and all(t.GetWidth() == 200000 for t in rgbled_trk)
                        and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                                and v.GetViaType() == pcbnew.VIATYPE_THROUGH
                                for v in rgbled_via))
        chk('G22 FRONT_RGB_LED copper legal (0.200 F.Cu+B.Cu, three 0.60/0.30 through vias)',
            '%d trk layers=%s, vias=%d dias=%s drills=%s'
            % (len(rgbled_trk), sorted(rgbled_layers), len(rgbled_via),
               sorted({v.GetWidth(pcbnew.F_Cu) for v in rgbled_via}),
               sorted({v.GetDrill() for v in rgbled_via})),
            rgbled_legal)

        rgbled_addonly = (len(rgbled_trk) == 25 and len(imu_trk) == 8
                          and len(disp_trk) == 11 and len(acc_trk) == 31
                          and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                          and len(phaseA_via) == 54)
        chk('G22 increment is ADD-ONLY (IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'rgbled=%d (exp 25), imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(rgbled_trk), len(imu_trk), len(disp_trk), len(acc_trk),
               len(rgb_trk), len(phaseA_trk), len(phaseA_via)),
            rgbled_addonly)

        # -- G23 FBV2-P2-011/D-309 sixth rest-of-board incremental increment ----
        # The IR receiver (U6) local filtered supply IR_RX_VS_LOCAL (series filter
        # R21.2 + decoupling C11.1 -> U6.3 THT supply pin) was routed onto the
        # D-308 promoted board by incremental_router.py as a genuine no-casualty /
        # no-new-DRC increment.  All three pads share the F.Cu outer layer (U6.3 is
        # THT), so every MST edge is a SAME-LAYER F.Cu run with NO via -- the
        # cleanest increment class (like D-307 IMU_ADDR, but on F.Cu): vias stay 58
        # and no GND plane is re-poured.  It was chosen on EVIDENCE, not by default:
        # the task-preferred display/touch group (TOUCH_RST_N + TOUCH_INT_N) and the
        # AMP_SD_MODE / SD_CARD_DETECT_N alternatives were all measured on scratch
        # and FAILED the real gate with new `clearance` violations (long cross-board
        # hauls colliding at the congested U2 B.Cu escape beside the D-306 DISP_RST_N
        # via).  G23 pins this increment on the authoritative board: the net is fully
        # copper-connected, its copper is legal (0.200 mm F.Cu, no via), and the
        # increment is ADD-ONLY -- the RGB_LED (25), IMU (8), DISP (11), ACC (31) and
        # RGB (20) increments and Phase-A (432 trk / 54 via) are untouched.
        print('  -- G23 FBV2-P2-011/D-309 rest-of-board incremental increment --')
        IRVS = ('/07_IR/IR_RX_VS_LOCAL',)
        irvs_trk = [t for t in _g18.GetTracks()
                    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in IRVS]
        irvs_via = [t for t in all_via if t.GetNetname() in IRVS]

        joined = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in _cc.GetConnectedItems(_pad('R21.2')) if p.GetClass() == 'PAD'}
        conn_ok = ('C11.1' in joined) and ('U6.3' in joined)
        chk('G23 IR_RX_VS_LOCAL fully copper-connected (C11.1-R21.2-U6.3 one island)',
            'R21.2 joined C11.1 & U6.3 = %s (%s)' % (conn_ok, sorted(joined)), conn_ok)

        irvs_legal = (len(irvs_trk) == 8 and not irvs_via
                      and all(t.GetLayerName() == 'F.Cu' and t.GetWidth() == 200000
                              for t in irvs_trk))
        chk('G23 IR_RX_VS_LOCAL copper legal (0.200 mm F.Cu, no via)',
            '%d tracks, widths=%s, layers=%s, irvs vias=%d'
            % (len(irvs_trk),
               sorted({t.GetWidth() for t in irvs_trk}),
               sorted({t.GetLayerName() for t in irvs_trk}), len(irvs_via)),
            irvs_legal)

        irvs_addonly = (len(irvs_trk) == 8 and len(rgbled_trk) == 25
                        and len(imu_trk) == 8 and len(disp_trk) == 11
                        and len(acc_trk) == 31 and len(rgb_trk) == 20
                        and len(phaseA_trk) == 432 and len(phaseA_via) == 54)
        chk('G23 increment is ADD-ONLY (RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'irvs=%d (exp 8), rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(irvs_trk), len(rgbled_trk), len(imu_trk), len(disp_trk),
               len(acc_trk), len(rgb_trk), len(phaseA_trk), len(phaseA_via)),
            irvs_addonly)

        # -- G24 FBV2-P2-012/D-310 seventh rest-of-board incremental increment ---
        # The display/touch control PAIR TOUCH_RST_N (J1.47/R12.1 F.Cu -> U2.4
        # B.Cu) + TOUCH_INT_N (J1.46 F.Cu -> U2.19 B.Cu) was routed onto the D-309
        # board by incremental_router.py.  This is the group D-309 MEASURED as a
        # wall: U2.4/.7/.8/.11 stack on U2's west edge and the accepted D-306
        # DISP_RST_N through-via sits 1.19 mm west of that column, so the via-blind
        # default via_site laid the F<->B transition (and threaded its F.Cu run)
        # right past the DISP_RST_N barrel -> +3 `clearance`.  FBV2-P2-012 closes it
        # with TWO generic, bounded, qrouter-untouched mechanisms in connect_cross:
        # (a) existing PCB_VIA barrels/holes are injected as obstacles on the route
        # QBoard instance (qrouter._scan omits them), so escape/via_site/connect_role
        # all respect accepted vias; (b) a per-group `via_offset` walks the
        # transition a bounded 2.5 mm off the nearest congesting barrel.  Result:
        # both vias land >=5 mm from any existing via and the gate is clean.  G24
        # pins the increment: both nets fully copper-connected, copper legal (26 trk
        # 0.200 mm, 2x 0.60/0.30 through vias), the two vias cleared of every other
        # via (the offset mechanism worked), and ADD-ONLY (IR_RX_VS 8, RGB_LED 25,
        # IMU 8, DISP 11, ACC 31, RGB 20, Phase-A 432/54 untouched).
        print('  -- G24 FBV2-P2-012/D-310 rest-of-board incremental increment --')
        TCH = ('/TOUCH_RST_N', '/TOUCH_INT_N')
        tch_trk = [t for t in _g18.GetTracks()
                   if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in TCH]
        tch_via = [t for t in all_via if t.GetNetname() in TCH]

        j_rst = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                 for p in _cc.GetConnectedItems(_pad('R12.1')) if p.GetClass() == 'PAD'}
        j_int = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                 for p in _cc.GetConnectedItems(_pad('U2.19')) if p.GetClass() == 'PAD'}
        conn_ok = ('J1.47' in j_rst and 'U2.4' in j_rst) and ('J1.46' in j_int)
        chk('G24 TOUCH_RST_N + TOUCH_INT_N fully copper-connected across the U2 F/B hop',
            'R12.1 joins J1.47&U2.4=%s ; U2.19 joins J1.46=%s'
            % ('J1.47' in j_rst and 'U2.4' in j_rst, 'J1.46' in j_int), conn_ok)

        tch_layers = {t.GetLayerName() for t in tch_trk}
        tch_legal = (len(tch_trk) == 26 and len(tch_via) == 2
                     and tch_layers == {'F.Cu', 'B.Cu'}
                     and all(t.GetWidth() == 200000 for t in tch_trk)
                     and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                             for v in tch_via))
        chk('G24 TOUCH copper legal (26 trk 0.200 F.Cu+B.Cu, 2x 0.60/0.30 through via)',
            '%d trk layers=%s, vias=%d dias=%s drills=%s'
            % (len(tch_trk), sorted(tch_layers), len(tch_via),
               sorted({v.GetWidth(pcbnew.F_Cu) for v in tch_via}),
               sorted({v.GetDrill() for v in tch_via})), tch_legal)

        # The via-site OFFSET mechanism: each TOUCH via must clear EVERY other via
        # (barrel copper: 0.60/2 + 0.60/2 + 0.200 = 0.800 mm centre-to-centre).  A
        # via-blind default put AMP_SD_MODE 0.700 mm from DISP_RST_N (0.100 mm
        # copper) -- this proves the D-310 offset actually moved the transition off
        # the wall.
        other_via = [t for t in all_via if t.GetNetname() not in TCH]
        min_gap = min((((v.GetPosition().x - o.GetPosition().x) ** 2
                        + (v.GetPosition().y - o.GetPosition().y) ** 2) ** 0.5
                       for v in tch_via for o in other_via), default=1e9)
        chk('G24 U2-escape offset cleared both vias of every existing via (>=0.80 mm centre)',
            'min TOUCH-via to other-via centre = %.3f mm' % (min_gap / 1e6),
            min_gap >= 800000)

        tch_addonly = (len(tch_trk) == 26 and len(irvs_trk) == 8
                       and len(rgbled_trk) == 25 and len(imu_trk) == 8
                       and len(disp_trk) == 11 and len(acc_trk) == 31
                       and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                       and len(phaseA_via) == 54)
        chk('G24 increment is ADD-ONLY (IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'touch=%d (exp 26), irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(tch_trk), len(irvs_trk), len(rgbled_trk), len(imu_trk),
               len(disp_trk), len(acc_trk), len(rgb_trk), len(phaseA_trk),
               len(phaseA_via)), tch_addonly)

        # -- G25 FBV2-P2-013/D-311 eighth rest-of-board incremental increment ---
        # The audio-amp SD/mode-select strap AMP_SD_MODE (R15.1/U5.4 F.Cu ->
        # U2.7 B.Cu) was routed onto the D-310 board by incremental_router.py.
        # This is one of the two remaining U2 west-edge escape siblings the D-310
        # via-offset UNLOCKED, and the HARDEST D-309 wall: the via-blind default
        # via landed 0.100 mm from the accepted D-306 DISP_RST_N barrel (D-309
        # +7 `clearance`).  D-311 completes it with the SAME unchanged mechanism
        # -- the always-on existing-via injection plus the opt-in 2.5 mm
        # via_offset (zero per-net tuning) -- walking the F<->B transition to
        # (51.55,90.20), 1.760 mm clear of the nearest existing via (now the
        # D-310 TOUCH_RST_N barrel).  Its sibling SD_CARD_DETECT_N also passed on
        # scratch and is held for FBV2-P2-014 (not bundled -- functionally
        # distinct).  G25 pins the increment: the net fully copper-connected
        # across the U2 F/B hop, copper legal (19 trk 0.200 mm F.Cu+B.Cu, one
        # 0.60/0.30 through via), the via cleared of every existing via (the
        # offset mechanism worked), and ADD-ONLY (TOUCH 26, IR_RX_VS 8, RGB_LED
        # 25, IMU 8, DISP 11, ACC 31, RGB 20, Phase-A 432/54 untouched).
        print('  -- G25 FBV2-P2-013/D-311 rest-of-board incremental increment --')
        AMP = ('/AMP_SD_MODE',)
        amp_trk = [t for t in _g18.GetTracks()
                   if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in AMP]
        amp_via = [t for t in all_via if t.GetNetname() in AMP]

        j_amp = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                 for p in _cc.GetConnectedItems(_pad('U5.4')) if p.GetClass() == 'PAD'}
        amp_conn = ('R15.1' in j_amp and 'U2.7' in j_amp)
        chk('G25 AMP_SD_MODE fully copper-connected across the U2 F/B hop',
            'U5.4 joins R15.1&U2.7 = %s' % amp_conn, amp_conn)

        amp_layers = {t.GetLayerName() for t in amp_trk}
        amp_legal = (len(amp_trk) == 19 and len(amp_via) == 1
                     and amp_layers == {'F.Cu', 'B.Cu'}
                     and all(t.GetWidth() == 200000 for t in amp_trk)
                     and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                             for v in amp_via))
        chk('G25 AMP_SD_MODE copper legal (19 trk 0.200 F.Cu+B.Cu, one 0.60/0.30 through via)',
            '%d trk layers=%s, vias=%d dias=%s drills=%s'
            % (len(amp_trk), sorted(amp_layers), len(amp_via),
               sorted({v.GetWidth(pcbnew.F_Cu) for v in amp_via}),
               sorted({v.GetDrill() for v in amp_via})), amp_legal)

        # The via-site OFFSET mechanism: the AMP via must clear EVERY other via
        # (barrel copper: 0.60/2 + 0.60/2 + 0.200 = 0.800 mm centre-to-centre).
        # The via-blind default put it 0.700 mm from DISP_RST_N (0.100 mm copper,
        # D-309 +7) -- this proves the D-311 offset actually moved the transition
        # off the wall.
        amp_other_via = [t for t in all_via if t.GetNetname() not in AMP]
        amp_min_gap = min((((v.GetPosition().x - o.GetPosition().x) ** 2
                            + (v.GetPosition().y - o.GetPosition().y) ** 2) ** 0.5
                           for v in amp_via for o in amp_other_via), default=1e9)
        chk('G25 U2-escape offset cleared the AMP via of every existing via (>=0.80 mm centre)',
            'min AMP-via to other-via centre = %.3f mm' % (amp_min_gap / 1e6),
            amp_min_gap >= 800000)

        amp_addonly = (len(amp_trk) == 19 and len(tch_trk) == 26 and len(irvs_trk) == 8
                       and len(rgbled_trk) == 25 and len(imu_trk) == 8
                       and len(disp_trk) == 11 and len(acc_trk) == 31
                       and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                       and len(phaseA_via) == 54)
        chk('G25 increment is ADD-ONLY (TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'amp=%d (exp 19), touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(amp_trk), len(tch_trk), len(irvs_trk), len(rgbled_trk),
               len(imu_trk), len(disp_trk), len(acc_trk), len(rgb_trk),
               len(phaseA_trk), len(phaseA_via)), amp_addonly)

        # -- G26 FBV2-P2-014/D-312 ninth rest-of-board incremental increment -----
        # The microSD card-detect strap SD_CARD_DETECT_N (J2.10/R113.2 F.Cu ->
        # U2.11 B.Cu) was routed onto the D-311 board by incremental_router.py.
        # This is the SECOND remaining U2 west-edge escape sibling and the last of
        # the D-309 U2 family: the D-309 +2 `clearance` was TRACK-threading, not
        # the via.  D-312 completes it with the SAME unchanged mechanism -- the
        # always-on existing-via injection fixes the track threading, plus the
        # opt-in 2.5 mm via_offset (zero per-net tuning) walks the F<->B
        # transition SOUTH to (53.00,82.55), 3.850 mm clear of the nearest
        # existing via (DISP_RST_N barrel).  Re-screened LIVE on the D-311 board
        # (w/screen_014.py): the new D-311 AMP via (north, y~90) does not touch
        # SD_CARD_DETECT_N's southward escape; even the via-blind default via is
        # 1.301 mm clear.  Routed as its OWN increment (not bundled with
        # AMP_SD_MODE -- functionally distinct microSD vs audio).  G26 pins the
        # increment: net fully copper-connected across the U2 F/B hop, copper
        # legal (28 trk 0.200 mm F.Cu+B.Cu, one 0.60/0.30 through via), the via
        # cleared of every existing via, and ADD-ONLY (AMP 19, TOUCH 26,
        # IR_RX_VS 8, RGB_LED 25, IMU 8, DISP 11, ACC 31, RGB 20, Phase-A 432/54).
        print('  -- G26 FBV2-P2-014/D-312 rest-of-board incremental increment --')
        SD = ('/SD_CARD_DETECT_N',)
        sd_trk = [t for t in _g18.GetTracks()
                  if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in SD]
        sd_via = [t for t in all_via if t.GetNetname() in SD]

        j_sd = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                for p in _cc.GetConnectedItems(_pad('U2.11')) if p.GetClass() == 'PAD'}
        sd_conn = ('J2.10' in j_sd and 'R113.2' in j_sd)
        chk('G26 SD_CARD_DETECT_N fully copper-connected across the U2 F/B hop',
            'U2.11 joins J2.10&R113.2 = %s' % sd_conn, sd_conn)

        sd_layers = {t.GetLayerName() for t in sd_trk}
        sd_legal = (len(sd_trk) == 28 and len(sd_via) == 1
                    and sd_layers == {'F.Cu', 'B.Cu'}
                    and all(t.GetWidth() == 200000 for t in sd_trk)
                    and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                            for v in sd_via))
        chk('G26 SD_CARD_DETECT_N copper legal (28 trk 0.200 F.Cu+B.Cu, one 0.60/0.30 through via)',
            '%d trk layers=%s, vias=%d dias=%s drills=%s'
            % (len(sd_trk), sorted(sd_layers), len(sd_via),
               sorted({v.GetWidth(pcbnew.F_Cu) for v in sd_via}),
               sorted({v.GetDrill() for v in sd_via})), sd_legal)

        # The via-site OFFSET mechanism: the SD via must clear EVERY other via
        # (barrel copper: 0.60/2 + 0.60/2 + 0.200 = 0.800 mm centre-to-centre).
        # The 2.5 mm offset put it 3.850 mm from DISP_RST_N.
        sd_other_via = [t for t in all_via if t.GetNetname() not in SD]
        sd_min_gap = min((((v.GetPosition().x - o.GetPosition().x) ** 2
                           + (v.GetPosition().y - o.GetPosition().y) ** 2) ** 0.5
                          for v in sd_via for o in sd_other_via), default=1e9)
        chk('G26 U2-escape offset cleared the SD via of every existing via (>=0.80 mm centre)',
            'min SD-via to other-via centre = %.3f mm' % (sd_min_gap / 1e6),
            sd_min_gap >= 800000)

        sd_addonly = (len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                      and len(irvs_trk) == 8 and len(rgbled_trk) == 25
                      and len(imu_trk) == 8 and len(disp_trk) == 11
                      and len(acc_trk) == 31 and len(rgb_trk) == 20
                      and len(phaseA_trk) == 432 and len(phaseA_via) == 54)
        chk('G26 increment is ADD-ONLY (AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'sd=%d (exp 28), amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(sd_trk), len(amp_trk), len(tch_trk), len(irvs_trk), len(rgbled_trk),
               len(imu_trk), len(disp_trk), len(acc_trk), len(rgb_trk),
               len(phaseA_trk), len(phaseA_via)), sd_addonly)

        # -- G27 FBV2-P2-015/D-313 tenth rest-of-board incremental increment ----
        # The FIRST XGPIO community-header bank member(s): the east-edge pilot
        # XGPIO8 (R59.1 F.Cu -> U3.13 B.Cu) + XGPIO9 (R60.1 F.Cu -> U3.14 B.Cu),
        # routed onto the D-312 board by incremental_router.py.  Each /XGPIOx is a
        # 2-pad cross-layer net (100 R series resistor F.Cu top -> PCAL9535A U3
        # pin B.Cu mid-board): one MST edge, one F<->B through via.  The corridor
        # study (w/xgpio_study_015.py) measured every default via site >=3 mm
        # clear of every existing barrel (U3 escapes NORTH, away from the U2
        # cluster) so NO via_offset is used; the two east vias separate 2.7 mm
        # (the west members crowd one pocket -- XGPIO6/7 picked the identical
        # site -- and were NOT bundled).  The one real corridor constraint is the
        # D-269 BAT_MAIN 0.300 mm clearance to the 52.4 mm BAT_PROTECTED_P F.Cu
        # trunk that sweeps across the y~73-82 via band: at the default 0.200 mm
        # the copper landed 0.244-0.281 mm from it (real DRC clearance FAIL), so
        # the group is routed at the 0.300 mm D-269 floor (the CORRECT clearance,
        # not a new mechanism).  G27 pins the increment: both nets fully copper-
        # connected, copper legal (23 trk 0.200 mm F.Cu+B.Cu, two 0.60/0.30
        # through vias), both vias clear of every existing via, the D-269 0.300 mm
        # BAT_PROTECTED_P clearance kept, and ADD-ONLY (SD 28, AMP 19, TOUCH 26,
        # IR_RX_VS 8, RGB_LED 25, IMU 8, DISP 11, ACC 31, RGB 20, Phase-A 432/54).
        print('  -- G27 FBV2-P2-015/D-313 rest-of-board incremental increment --')
        XG = ('/XGPIO8', '/XGPIO9')
        xg_trk = [t for t in _g18.GetTracks()
                  if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in XG]
        xg_via = [t for t in all_via if t.GetNetname() in XG]

        j8 = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
              for p in _cc.GetConnectedItems(_pad('U3.13')) if p.GetClass() == 'PAD'}
        j9 = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
              for p in _cc.GetConnectedItems(_pad('U3.14')) if p.GetClass() == 'PAD'}
        xg_conn = ('R59.1' in j8 and 'R60.1' in j9)
        chk('G27 XGPIO8 + XGPIO9 fully copper-connected across the U3 F/B hop',
            'U3.13 joins R59.1 = %s ; U3.14 joins R60.1 = %s'
            % ('R59.1' in j8, 'R60.1' in j9), xg_conn)

        xg_layers = {t.GetLayerName() for t in xg_trk}
        xg_pnv = collections.Counter(v.GetNetname() for v in xg_via)
        xg_legal = (len(xg_trk) == 23 and len(xg_via) == 2
                    and xg_layers == {'F.Cu', 'B.Cu'}
                    and all(t.GetWidth() == 200000 for t in xg_trk)
                    and xg_pnv.get('/XGPIO8') == 1 and xg_pnv.get('/XGPIO9') == 1
                    and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                            and v.GetViaType() == pcbnew.VIATYPE_THROUGH
                            for v in xg_via))
        chk('G27 XGPIO pilot copper legal (23 trk 0.200 F.Cu+B.Cu, two 0.60/0.30 through vias, 1 via/net)',
            '%d trk layers=%s, vias=%d per-net=%s dias=%s drills=%s'
            % (len(xg_trk), sorted(xg_layers), len(xg_via), dict(xg_pnv),
               sorted({v.GetWidth(pcbnew.F_Cu) for v in xg_via}),
               sorted({v.GetDrill() for v in xg_via})), xg_legal)

        # Both vias clear every existing via barrel (>=0.80 mm centre); the study
        # found the U3-north escape lands >=3 mm from any barrel (no via_offset).
        xg_other_via = [t for t in all_via if t.GetNetname() not in XG]
        xg_min_gap = min((((v.GetPosition().x - o.GetPosition().x) ** 2
                           + (v.GetPosition().y - o.GetPosition().y) ** 2) ** 0.5
                          for v in xg_via for o in xg_other_via), default=1e9)
        chk('G27 both XGPIO vias clear every existing via (>=0.80 mm centre)',
            'min XGPIO-via to other-via centre = %.3f mm' % (xg_min_gap / 1e6),
            xg_min_gap >= 800000)

        # D-269 corridor evidence: the BAT_PROTECTED_P F.Cu trunk crosses the
        # XGPIO via band; the routed copper must keep >=0.300 mm from it.
        def _ptseg(px, py, ax, ay, bx, by):
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 == 0:
                return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
            tt = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
            return ((px - (ax + tt * dx)) ** 2 + (py - (ay + tt * dy)) ** 2) ** 0.5

        bpp_f = [t for t in _g18.GetTracks()
                 if t.GetClass() == 'PCB_TRACK' and 'BAT_PROTECTED_P' in t.GetNetname()
                 and t.GetLayerName() == 'F.Cu']
        xg_bpp = 1e12
        for t in [t for t in xg_trk if t.GetLayerName() == 'F.Cu']:
            s, e = t.GetStart(), t.GetEnd()
            for o in bpp_f:
                os_, oe = o.GetStart(), o.GetEnd()
                d = min(_ptseg(s.x, s.y, os_.x, os_.y, oe.x, oe.y),
                        _ptseg(e.x, e.y, os_.x, os_.y, oe.x, oe.y),
                        _ptseg(os_.x, os_.y, s.x, s.y, e.x, e.y),
                        _ptseg(oe.x, oe.y, s.x, s.y, e.x, e.y)) - t.GetWidth() / 2.0 - o.GetWidth() / 2.0
                if d < xg_bpp:
                    xg_bpp = d
        chk('G27 XGPIO F.Cu copper keeps the D-269 0.300 mm BAT_PROTECTED_P clearance',
            'min XGPIO->BAT_PROTECTED_P F.Cu edge gap = %.4f mm' % (xg_bpp / 1e6),
            xg_bpp >= 300000 - 1000)

        xg_addonly = (len(xg_trk) == 23 and len(sd_trk) == 28 and len(amp_trk) == 19
                      and len(tch_trk) == 26 and len(irvs_trk) == 8
                      and len(rgbled_trk) == 25 and len(imu_trk) == 8
                      and len(disp_trk) == 11 and len(acc_trk) == 31
                      and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                      and len(phaseA_via) == 54)
        chk('G27 increment is ADD-ONLY (SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'xgpio=%d (exp 23), sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(xg_trk), len(sd_trk), len(amp_trk), len(tch_trk), len(irvs_trk),
               len(rgbled_trk), len(imu_trk), len(disp_trk), len(acc_trk),
               len(rgb_trk), len(phaseA_trk), len(phaseA_via)), xg_addonly)

        # -- G28 FBV2-P2-016/D-314 eleventh rest-of-board incremental increment --
        # The WEST-edge SOUTH XGPIO pilot: XGPIO1 (R52.1 F.Cu -> U3.5 B.Cu) +
        # XGPIO0 (R51.1 F.Cu -> U3.4 B.Cu), the two SOUTHERNMOST west community-
        # header GPIO nets on consecutive PCAL9535A U3 pins, routed onto the D-313
        # board by incremental_router.py.  The D-313 study characterised the eight
        # west members as crowding ONE north-of-U3 via pocket (the NORTHERN pair
        # XGPIO6/7 pick the identical site) -- but the recovery screen
        # (w/screen_016.py + w/screen_016_one.py, live D-313 board) MEASURED that
        # the SOUTHERN pair SELF-SEPARATES when routed XGPIO1-first: XGPIO1's via
        # lands in the pocket at (55.40,79.00), then XGPIO0 -- routed SECOND, so
        # XGPIO1's laid via is a real qb.via() obstacle -- escapes WEST to
        # (52.75,78.35); via-via copper 2.129 mm, both >=2.0 mm from the
        # BAT_PROTECTED_P trunk, all >> the 0.300 mm D-269 floor.  Order matters
        # (the reverse order boxes XGPIO1 out); no via_offset (every site >=2 mm
        # clear of every barrel).  Same D-269 0.300 mm clearance as the east pilot
        # (BAT_PROTECTED_P crosses the via band).  G28 pins the increment: both
        # nets fully copper-connected, copper legal (38 trk 0.200 mm F.Cu+B.Cu,
        # two 0.60/0.30 through vias), both vias clear of every existing via, the
        # D-269 0.300 mm BAT_PROTECTED_P clearance kept, and ADD-ONLY (east XGPIO
        # 23, SD 28, AMP 19, TOUCH 26, IR_RX_VS 8, RGB_LED 25, IMU 8, DISP 11,
        # ACC 31, RGB 20, Phase-A 432/54).
        print('  -- G28 FBV2-P2-016/D-314 rest-of-board incremental increment --')
        XGW = ('/XGPIO1', '/XGPIO0')
        xgw_trk = [t for t in _g18.GetTracks()
                   if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in XGW]
        xgw_via = [t for t in all_via if t.GetNetname() in XGW]

        j1 = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
              for p in _cc.GetConnectedItems(_pad('U3.5')) if p.GetClass() == 'PAD'}
        j0 = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
              for p in _cc.GetConnectedItems(_pad('U3.4')) if p.GetClass() == 'PAD'}
        xgw_conn = ('R52.1' in j1 and 'R51.1' in j0)
        chk('G28 XGPIO1 + XGPIO0 fully copper-connected across the U3 F/B hop',
            'U3.5 joins R52.1 = %s ; U3.4 joins R51.1 = %s'
            % ('R52.1' in j1, 'R51.1' in j0), xgw_conn)

        xgw_layers = {t.GetLayerName() for t in xgw_trk}
        xgw_pnv = collections.Counter(v.GetNetname() for v in xgw_via)
        xgw_legal = (len(xgw_trk) == 38 and len(xgw_via) == 2
                     and xgw_layers == {'F.Cu', 'B.Cu'}
                     and all(t.GetWidth() == 200000 for t in xgw_trk)
                     and xgw_pnv.get('/XGPIO1') == 1 and xgw_pnv.get('/XGPIO0') == 1
                     and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                             and v.GetViaType() == pcbnew.VIATYPE_THROUGH
                             for v in xgw_via))
        chk('G28 XGPIO west pilot copper legal (38 trk 0.200 F.Cu+B.Cu, two 0.60/0.30 through vias, 1 via/net)',
            '%d trk layers=%s, vias=%d per-net=%s dias=%s drills=%s'
            % (len(xgw_trk), sorted(xgw_layers), len(xgw_via), dict(xgw_pnv),
               sorted({v.GetWidth(pcbnew.F_Cu) for v in xgw_via}),
               sorted({v.GetDrill() for v in xgw_via})), xgw_legal)

        xgw_other_via = [t for t in all_via if t.GetNetname() not in XGW]
        xgw_min_gap = min((((v.GetPosition().x - o.GetPosition().x) ** 2
                            + (v.GetPosition().y - o.GetPosition().y) ** 2) ** 0.5
                           for v in xgw_via for o in xgw_other_via), default=1e9)
        chk('G28 both west-XGPIO vias clear every existing via (>=0.80 mm centre)',
            'min west-XGPIO-via to other-via centre = %.3f mm' % (xgw_min_gap / 1e6),
            xgw_min_gap >= 800000)

        xgw_bpp = 1e12
        for t in [t for t in xgw_trk if t.GetLayerName() == 'F.Cu']:
            s, e = t.GetStart(), t.GetEnd()
            for o in bpp_f:
                os_, oe = o.GetStart(), o.GetEnd()
                d = min(_ptseg(s.x, s.y, os_.x, os_.y, oe.x, oe.y),
                        _ptseg(e.x, e.y, os_.x, os_.y, oe.x, oe.y),
                        _ptseg(os_.x, os_.y, s.x, s.y, e.x, e.y),
                        _ptseg(oe.x, oe.y, s.x, s.y, e.x, e.y)) - t.GetWidth() / 2.0 - o.GetWidth() / 2.0
                if d < xgw_bpp:
                    xgw_bpp = d
        chk('G28 XGPIO west F.Cu copper keeps the D-269 0.300 mm BAT_PROTECTED_P clearance',
            'min west-XGPIO->BAT_PROTECTED_P F.Cu edge gap = %.4f mm' % (xgw_bpp / 1e6),
            xgw_bpp >= 300000 - 1000)

        xgw_addonly = (len(xgw_trk) == 38 and len(xg_trk) == 23 and len(sd_trk) == 28
                       and len(amp_trk) == 19 and len(tch_trk) == 26 and len(irvs_trk) == 8
                       and len(rgbled_trk) == 25 and len(imu_trk) == 8
                       and len(disp_trk) == 11 and len(acc_trk) == 31
                       and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                       and len(phaseA_via) == 54)
        chk('G28 increment is ADD-ONLY (east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'xgpio_w=%d (exp 38), xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(xgw_trk), len(xg_trk), len(sd_trk), len(amp_trk), len(tch_trk),
               len(irvs_trk), len(rgbled_trk), len(imu_trk), len(disp_trk),
               len(acc_trk), len(rgb_trk), len(phaseA_trk), len(phaseA_via)), xgw_addonly)

        # -- G29 FBV2-P2-018/D-316 twelfth rest-of-board incremental increment ---
        # A SINGLE west XGPIO net: XGPIO3 (R54.1 F.Cu -> U3.7 B.Cu), one community-
        # header GPIO on PCAL9535A U3 pin 7, routed onto the D-314 board by
        # incremental_router.py at the 0.200 mm Default clearance (NOT the 0.300 mm
        # blanket the D-313/D-314 XGPIO pilot PAIRS used).  D-315 characterised the
        # XGPIO2+XGPIO3 adjacent PAIR as a corridor-capacity WALL (both orders
        # NO_FAR_RUN -- the now D-313+D-314-congested F.Cu corridor admits ONE
        # 116 mm haul, not two) and produced the positive lead this increment
        # realises: a SINGLE west member routes CLEAN at 0.200 mm and KEEPS the
        # D-269 0.300 mm floor to the BAT_PROTECTED_P trunk BY GEOMETRY, because a
        # single west haul's natural path clears BPP by >=0.47 mm (unlike the D-313
        # EAST pilot whose 0.200 mm haul pinched BPP and needed the 0.300 mm floor).
        # The 0.200 mm Default clearance is the correct DRC floor here; the real
        # full-board D-269-aware KiCad DRC (D-286 gate) arbitrates the BPP clearance
        # and found NO new/worse class -- NOT rule weakening (D-269 is satisfied by
        # measured geometry, 0.4739 mm >= 0.300).  One net, one MST edge, one
        # 0.60/0.30 Default through via @(55.300,77.700); no via_offset (the site is
        # 0.704 mm copper / 1.304 mm centre clear of the nearest existing barrel).
        # G29 pins the increment: XGPIO3 fully copper-connected, copper legal
        # (22 trk 0.200 mm F.Cu+B.Cu, one 0.60/0.30 through via), the via clear of
        # every existing via, the D-269 0.300 mm BAT_PROTECTED_P clearance kept, and
        # ADD-ONLY (west-XGPIO 38, east-XGPIO 23, SD 28, AMP 19, TOUCH 26,
        # IR_RX_VS 8, RGB_LED 25, IMU 8, DISP 11, ACC 31, RGB 20, Phase-A 432/54).
        print('  -- G29 FBV2-P2-018/D-316 rest-of-board incremental increment --')
        XG3 = '/XGPIO3'
        xg3_trk = [t for t in _g18.GetTracks()
                   if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == XG3]
        xg3_via = [t for t in all_via if t.GetNetname() == XG3]

        j3 = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
              for p in _cc.GetConnectedItems(_pad('U3.7')) if p.GetClass() == 'PAD'}
        xg3_conn = ('R54.1' in j3)
        chk('G29 XGPIO3 fully copper-connected across the U3 F/B hop',
            'U3.7 joins R54.1 = %s' % ('R54.1' in j3), xg3_conn)

        xg3_layers = {t.GetLayerName() for t in xg3_trk}
        xg3_pnv = collections.Counter(v.GetNetname() for v in xg3_via)
        xg3_legal = (len(xg3_trk) == 22 and len(xg3_via) == 1
                     and xg3_layers == {'F.Cu', 'B.Cu'}
                     and all(t.GetWidth() == 200000 for t in xg3_trk)
                     and xg3_pnv.get('/XGPIO3') == 1
                     and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                             and v.GetViaType() == pcbnew.VIATYPE_THROUGH
                             for v in xg3_via))
        chk('G29 XGPIO3 single-net copper legal (22 trk 0.200 F.Cu+B.Cu, one 0.60/0.30 through via)',
            '%d trk layers=%s, vias=%d per-net=%s dias=%s drills=%s'
            % (len(xg3_trk), sorted(xg3_layers), len(xg3_via), dict(xg3_pnv),
               sorted({v.GetWidth(pcbnew.F_Cu) for v in xg3_via}),
               sorted({v.GetDrill() for v in xg3_via})), xg3_legal)

        xg3_other_via = [t for t in all_via if t.GetNetname() != XG3]
        xg3_min_gap = min((((v.GetPosition().x - o.GetPosition().x) ** 2
                            + (v.GetPosition().y - o.GetPosition().y) ** 2) ** 0.5
                           for v in xg3_via for o in xg3_other_via), default=1e9)
        chk('G29 XGPIO3 via clears every existing via (>=0.80 mm centre)',
            'min XGPIO3-via to other-via centre = %.3f mm' % (xg3_min_gap / 1e6),
            xg3_min_gap >= 800000)

        xg3_bpp = 1e12
        for t in [t for t in xg3_trk if t.GetLayerName() == 'F.Cu']:
            s, e = t.GetStart(), t.GetEnd()
            for o in bpp_f:
                os_, oe = o.GetStart(), o.GetEnd()
                d = min(_ptseg(s.x, s.y, os_.x, os_.y, oe.x, oe.y),
                        _ptseg(e.x, e.y, os_.x, os_.y, oe.x, oe.y),
                        _ptseg(os_.x, os_.y, s.x, s.y, e.x, e.y),
                        _ptseg(oe.x, oe.y, s.x, s.y, e.x, e.y)) - t.GetWidth() / 2.0 - o.GetWidth() / 2.0
                if d < xg3_bpp:
                    xg3_bpp = d
        chk('G29 XGPIO3 F.Cu copper keeps the D-269 0.300 mm BAT_PROTECTED_P clearance',
            'min XGPIO3->BAT_PROTECTED_P F.Cu edge gap = %.4f mm' % (xg3_bpp / 1e6),
            xg3_bpp >= 300000 - 1000)

        xg3_addonly = (len(xg3_trk) == 22 and len(xgw_trk) == 38 and len(xg_trk) == 23
                       and len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                       and len(irvs_trk) == 8 and len(rgbled_trk) == 25 and len(imu_trk) == 8
                       and len(disp_trk) == 11 and len(acc_trk) == 31
                       and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                       and len(phaseA_via) == 54)
        chk('G29 increment is ADD-ONLY (west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'xgpio3=%d (exp 22), xgpio_w=%d, xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(xg3_trk), len(xgw_trk), len(xg_trk), len(sd_trk), len(amp_trk),
               len(tch_trk), len(irvs_trk), len(rgbled_trk), len(imu_trk),
               len(disp_trk), len(acc_trk), len(rgb_trk), len(phaseA_trk),
               len(phaseA_via)), xg3_addonly)

        # -- G30 FBV2-P2-020/D-318 thirteenth rest-of-board incremental increment -
        # The IMU/I2C-local interrupt strap BMI270_INT1_STRAP (R18.2/R110.1/TP3.1
        # -> U1.15 GPIO), routed onto the D-316 board by incremental_router.py
        # OUTSIDE the saturated west-XGPIO F.Cu corridor (the D-317 mandate).  It
        # is the MCU-side leg of the BMI270 IMU INT1 interrupt: all four pads are
        # on F.Cu (U1 ESP32 pads F.Cu SMD; R18/R110/TP3 F.Cu SMD), so the 4-pad
        # multi-terminal MST is THREE SAME-LAYER F.Cu runs with NO via -- the
        # cleanest incremental class (no through via, no In1/In4 plane re-pour, no
        # via-clearance risk; the D-305/D-307 no-via same-layer mechanic, here on
        # F.Cu).  Noncritical low-speed CMOS interrupt strap (NOT switching / rail
        # / RF-NFC / USB / bus-clock / community-header).  Default netclass
        # (0.200 mm).  G30 pins the increment: all four pads copper-connected,
        # copper legal (18 trk 0.200 mm all F.Cu, ZERO vias), and ADD-ONLY
        # (XGPIO3 22, west-XGPIO 38, east-XGPIO 23, SD 28, AMP 19, TOUCH 26,
        # IR_RX_VS 8, RGB_LED 25, IMU 8, DISP 11, ACC 31, RGB 20, Phase-A 432/54).
        print('  -- G30 FBV2-P2-020/D-318 rest-of-board incremental increment --')
        INET = '/BMI270_INT1_STRAP'
        imu1_trk = [t for t in _g18.GetTracks()
                    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == INET]
        imu1_via = [t for t in all_via if t.GetNetname() == INET]

        j_imu1 = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in _cc.GetConnectedItems(_pad('R110.1')) if p.GetClass() == 'PAD'}
        imu1_conn = {'R18.2', 'TP3.1', 'U1.15'}.issubset(j_imu1)
        chk('G30 BMI270_INT1_STRAP all four pads copper-connected (R110.1/R18.2/TP3.1/U1.15)',
            'R110.1 joins %s' % sorted(j_imu1 & {'R18.2', 'TP3.1', 'U1.15'}), imu1_conn)

        imu1_layers = {t.GetLayerName() for t in imu1_trk}
        imu1_legal = (len(imu1_trk) == 18 and len(imu1_via) == 0
                      and imu1_layers == {'F.Cu'}
                      and all(t.GetWidth() == 200000 for t in imu1_trk))
        chk('G30 BMI270_INT1_STRAP copper legal (18 trk 0.200 mm all F.Cu, ZERO vias)',
            '%d trk layers=%s, vias=%d, widths=%s'
            % (len(imu1_trk), sorted(imu1_layers), len(imu1_via),
               sorted({t.GetWidth() for t in imu1_trk})), imu1_legal)

        imu1_addonly = (len(imu1_trk) == 18 and len(imu1_via) == 0
                        and len(xg3_trk) == 22 and len(xgw_trk) == 38 and len(xg_trk) == 23
                        and len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                        and len(irvs_trk) == 8 and len(rgbled_trk) == 25 and len(imu_trk) == 8
                        and len(disp_trk) == 11 and len(acc_trk) == 31
                        and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                        and len(phaseA_via) == 54)
        chk('G30 increment is ADD-ONLY (XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'imu_int1=%d (exp 18, 0 via), xgpio3=%d, xgpio_w=%d, xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(imu1_trk), len(xg3_trk), len(xgw_trk), len(xg_trk), len(sd_trk),
               len(amp_trk), len(tch_trk), len(irvs_trk), len(rgbled_trk),
               len(imu_trk), len(disp_trk), len(acc_trk), len(rgb_trk),
               len(phaseA_trk), len(phaseA_via)), imu1_addonly)

        # -- G31 FBV2-P2-021/D-319 fourteenth rest-of-board incremental increment -
        # The debug-console UART transmit line UART0_TXD_DBG (U1.37 MCU -> TP35.1
        # test point), routed onto the D-318 board by incremental_router.py in an
        # OPEN region -- away from the saturated west-XGPIO F.Cu corridor, the
        # U11/BQ25185 power-tree wall, and the RF/NFC/USB/crystal/switching/rail/
        # community-header mass.  A dedicated point-to-point 2-pad net; both pads
        # on F.Cu, so its single MST edge is a SAME-LAYER F.Cu run with NO via --
        # the cleanest incremental class (no through via, no In1/In4 plane
        # re-pour, no via-clearance risk; the D-309 IR_RX_VS / D-318
        # BMI270_INT1_STRAP no-via same-layer mechanic).  Noncritical low-speed
        # CMOS debug output (NOT switching / rail / RF-NFC / USB / bus-clock /
        # community-header).  Default netclass (0.200 mm); MEASURED 31.3 mm clear
        # of BAT_PROTECTED_P -> ZERO D-269 involvement.  G31 pins the increment:
        # both pads copper-connected, copper legal (7 trk 0.200 mm all F.Cu, ZERO
        # vias), and ADD-ONLY (IMU_INT1 18, XGPIO3 22, west-XGPIO 38, east-XGPIO
        # 23, SD 28, AMP 19, TOUCH 26, IR_RX_VS 8, RGB_LED 25, IMU 8, DISP 11,
        # ACC 31, RGB 20, Phase-A 432/54).
        print('  -- G31 FBV2-P2-021/D-319 rest-of-board incremental increment --')
        UNET = '/02_MCU_CORE/UART0_TXD_DBG'
        uart_trk = [t for t in _g18.GetTracks()
                    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == UNET]
        uart_via = [t for t in all_via if t.GetNetname() == UNET]

        j_uart = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in _cc.GetConnectedItems(_pad('U1.37')) if p.GetClass() == 'PAD'}
        uart_conn = {'TP35.1'}.issubset(j_uart)
        chk('G31 UART0_TXD_DBG both pads copper-connected (U1.37/TP35.1)',
            'U1.37 joins %s' % sorted(j_uart & {'TP35.1'}), uart_conn)

        uart_layers = {t.GetLayerName() for t in uart_trk}
        uart_legal = (len(uart_trk) == 7 and len(uart_via) == 0
                      and uart_layers == {'F.Cu'}
                      and all(t.GetWidth() == 200000 for t in uart_trk))
        chk('G31 UART0_TXD_DBG copper legal (7 trk 0.200 mm all F.Cu, ZERO vias)',
            '%d trk layers=%s, vias=%d, widths=%s'
            % (len(uart_trk), sorted(uart_layers), len(uart_via),
               sorted({t.GetWidth() for t in uart_trk})), uart_legal)

        uart_addonly = (len(uart_trk) == 7 and len(uart_via) == 0
                        and len(imu1_trk) == 18
                        and len(xg3_trk) == 22 and len(xgw_trk) == 38 and len(xg_trk) == 23
                        and len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                        and len(irvs_trk) == 8 and len(rgbled_trk) == 25 and len(imu_trk) == 8
                        and len(disp_trk) == 11 and len(acc_trk) == 31
                        and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                        and len(phaseA_via) == 54)
        chk('G31 increment is ADD-ONLY (IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'uart=%d (exp 7, 0 via), imu_int1=%d, xgpio3=%d, xgpio_w=%d, xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(uart_trk), len(imu1_trk), len(xg3_trk), len(xgw_trk), len(xg_trk),
               len(sd_trk), len(amp_trk), len(tch_trk), len(irvs_trk), len(rgbled_trk),
               len(imu_trk), len(disp_trk), len(acc_trk), len(rgb_trk),
               len(phaseA_trk), len(phaseA_via)), uart_addonly)

        # -- G32 FBV2-P2-022/D-320 fifteenth rest-of-board incremental increment -
        # The IR transmit carrier CONTROL leg IR_TX_GPIO16 (U1.9 ESP32 GPIO16 ->
        # R22.1 series-drive resistor), routed onto the D-319 board by
        # incremental_router.py in an OPEN region -- away from the saturated
        # west-XGPIO F.Cu corridor, the U11/BQ25185 power-tree wall, and the
        # RF/NFC/USB/crystal/switching/rail/community-header mass.  A DEDICATED
        # 2-pad net that is ISOLATED by the series resistor R22 from the switching
        # output: R22.2 belongs to the SEPARATE IR_GATE net (Q1 gate / R23) and
        # the emitter-power path is IR_LED_A/IR_LED_K (both EXCLUDED switching/
        # emitter nets, NOT part of this increment) -- so this is the low-current
        # MCU carrier/control GPIO, distinct from the emitter power / switch path.
        # Both pads on F.Cu, so its single MST edge is a SAME-LAYER F.Cu run with
        # NO via -- the cleanest incremental class (no through via, no In1/In4
        # plane re-pour, no via-clearance risk; the D-309/D-318/D-319 no-via
        # same-layer mechanic).  The router detoured the run to 13 F.Cu segments
        # (23.2 mm) around the GND pinch on the straight path.  Default netclass
        # (0.200 mm); MEASURED 35.2 mm clear of BAT_PROTECTED_P -> ZERO D-269
        # involvement.  G32 pins the increment: both pads copper-connected,
        # copper legal (13 trk 0.200 mm all F.Cu, ZERO vias), and ADD-ONLY.
        print('  -- G32 FBV2-P2-022/D-320 rest-of-board incremental increment --')
        IRTXNET = '/IR_TX_GPIO16'
        irtx_trk = [t for t in _g18.GetTracks()
                    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == IRTXNET]
        irtx_via = [t for t in all_via if t.GetNetname() == IRTXNET]

        j_irtx = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in _cc.GetConnectedItems(_pad('U1.9')) if p.GetClass() == 'PAD'}
        irtx_conn = {'R22.1'}.issubset(j_irtx)
        chk('G32 IR_TX_GPIO16 both pads copper-connected (U1.9/R22.1)',
            'U1.9 joins %s' % sorted(j_irtx & {'R22.1'}), irtx_conn)

        irtx_layers = {t.GetLayerName() for t in irtx_trk}
        irtx_legal = (len(irtx_trk) == 13 and len(irtx_via) == 0
                      and irtx_layers == {'F.Cu'}
                      and all(t.GetWidth() == 200000 for t in irtx_trk))
        chk('G32 IR_TX_GPIO16 copper legal (13 trk 0.200 mm all F.Cu, ZERO vias)',
            '%d trk layers=%s, vias=%d, widths=%s'
            % (len(irtx_trk), sorted(irtx_layers), len(irtx_via),
               sorted({t.GetWidth() for t in irtx_trk})), irtx_legal)

        irtx_addonly = (len(irtx_trk) == 13 and len(irtx_via) == 0
                        and len(uart_trk) == 7
                        and len(imu1_trk) == 18
                        and len(xg3_trk) == 22 and len(xgw_trk) == 38 and len(xg_trk) == 23
                        and len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                        and len(irvs_trk) == 8 and len(rgbled_trk) == 25 and len(imu_trk) == 8
                        and len(disp_trk) == 11 and len(acc_trk) == 31
                        and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                        and len(phaseA_via) == 54)
        chk('G32 increment is ADD-ONLY (IR_TX 13 + UART 7 + IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'irtx=%d (exp 13, 0 via), uart=%d, imu_int1=%d, xgpio3=%d, xgpio_w=%d, xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(irtx_trk), len(uart_trk), len(imu1_trk), len(xg3_trk), len(xgw_trk),
               len(xg_trk), len(sd_trk), len(amp_trk), len(tch_trk), len(irvs_trk),
               len(rgbled_trk), len(imu_trk), len(disp_trk), len(acc_trk), len(rgb_trk),
               len(phaseA_trk), len(phaseA_via)), irtx_addonly)

        # -- G33 FBV2-P2-023/D-321 sixteenth rest-of-board incremental increment -
        # The microSD SPI chip-select SD_CS_N (J2.2 socket / R25.2 / U1.25 MCU),
        # routed onto the D-320 board by incremental_router.py in an OPEN region --
        # away from the saturated west-XGPIO F.Cu corridor, the U11/BQ25185 power-
        # tree wall, and the RF/NFC/USB/crystal/switching/rail/community-header
        # mass.  A genuine functional POINT-TO-POINT control (NOT a shared SPI
        # data/clock bus line -- the chip-select travels with its own synchronous
        # SPI-A bus, so proximity to SPI_A_MOSI is benign).  Chosen after the
        # mandate's headline candidate Net-(U1-EN) (the MCU EN reset RC) hit a
        # characterized local wall (natural MST short edge C1.2<->U1.3 NO_PATH in
        # the dense U1-EN pad pocket; other edge 58.5 mm detour) and over the
        # RESERVED_SPARE spare (held clean alternate).  All three pads on F.Cu, so
        # both MST edges are SAME-LAYER F.Cu runs with NO via -- the cleanest
        # incremental class (no through via, no In1/In4 plane re-pour; the D-309/
        # D-318/D-319/D-320 no-via same-layer mechanic).  Default netclass
        # (0.200 mm); MEASURED 50.1 mm clear of BAT_PROTECTED_P -> ZERO D-269
        # involvement.  G33 pins the increment: all three pads copper-connected,
        # copper legal (20 trk 0.200 mm all F.Cu, ZERO vias), and ADD-ONLY.
        print('  -- G33 FBV2-P2-023/D-321 rest-of-board incremental increment --')
        SDCSNET = '/SD_CS_N'
        sdcs_trk = [t for t in _g18.GetTracks()
                    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == SDCSNET]
        sdcs_via = [t for t in all_via if t.GetNetname() == SDCSNET]

        j_sdcs = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                  for p in _cc.GetConnectedItems(_pad('U1.25')) if p.GetClass() == 'PAD'}
        sdcs_conn = {'J2.2', 'R25.2'}.issubset(j_sdcs)
        chk('G33 SD_CS_N all three pads copper-connected (U1.25/J2.2/R25.2)',
            'U1.25 joins %s' % sorted(j_sdcs & {'J2.2', 'R25.2'}), sdcs_conn)

        sdcs_layers = {t.GetLayerName() for t in sdcs_trk}
        sdcs_legal = (len(sdcs_trk) == 20 and len(sdcs_via) == 0
                      and sdcs_layers == {'F.Cu'}
                      and all(t.GetWidth() == 200000 for t in sdcs_trk))
        chk('G33 SD_CS_N copper legal (20 trk 0.200 mm all F.Cu, ZERO vias)',
            '%d trk layers=%s, vias=%d, widths=%s'
            % (len(sdcs_trk), sorted(sdcs_layers), len(sdcs_via),
               sorted({t.GetWidth() for t in sdcs_trk})), sdcs_legal)

        sdcs_addonly = (len(sdcs_trk) == 20 and len(sdcs_via) == 0
                        and len(irtx_trk) == 13
                        and len(uart_trk) == 7
                        and len(imu1_trk) == 18
                        and len(xg3_trk) == 22 and len(xgw_trk) == 38 and len(xg_trk) == 23
                        and len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                        and len(irvs_trk) == 8 and len(rgbled_trk) == 25 and len(imu_trk) == 8
                        and len(disp_trk) == 11 and len(acc_trk) == 31
                        and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                        and len(phaseA_via) == 54)
        chk('G33 increment is ADD-ONLY (SD_CS 20 + IR_TX 13 + UART 7 + IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'sdcs=%d (exp 20, 0 via), irtx=%d, uart=%d, imu_int1=%d, xgpio3=%d, xgpio_w=%d, xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(sdcs_trk), len(irtx_trk), len(uart_trk), len(imu1_trk), len(xg3_trk),
               len(xgw_trk), len(xg_trk), len(sd_trk), len(amp_trk), len(tch_trk),
               len(irvs_trk), len(rgbled_trk), len(imu_trk), len(disp_trk), len(acc_trk),
               len(rgb_trk), len(phaseA_trk), len(phaseA_via)), sdcs_addonly)

        # -- G34 FBV2-P2-024/D-322 seventeenth rest-of-board incremental increment
        # The reserved/spare community expander GPIO RESERVED_SPARE (R130.2 /
        # TP41.1 test point / U23.7 PCAL expander), routed onto the D-321 board by
        # incremental_router.py in an OPEN region -- away from the saturated
        # west-XGPIO F.Cu corridor, the U11/BQ25185 power-tree wall, and the RF/
        # NFC/USB/crystal/switching/rail/community-header mass.  The held clean
        # alternate, PROMOTED after the mandate's meaningful display-control
        # candidates DISP_CS_N (U1.18/R26.2/J1.38) and DISP_DC (U1.22/J1.37) hit a
        # characterized J1 display-FPC-connector wall (long interior haul NO_PATH
        # at 0.200 mm even on the 0.05/0.025 mm fine grid) and after BOOT_N (the
        # meaningful non-J1 alternative, the boot-mode strap) routed only via poor
        # 2.5x detours (~110 mm of copper across the congested MCU interior) -- not
        # equally clean, and its reset-level sensitivity treated carefully.  All
        # three pads on B.Cu, so both MST edges are SAME-LAYER B.Cu runs with NO
        # via -- the cleanest incremental class (no through via, no In1/In4 plane
        # re-pour; the D-304/D-305/D-307 no-via same-layer mechanic).  Default
        # netclass (0.200 mm); MEASURED 15.5 mm clear of BAT_PROTECTED_P -> ZERO
        # D-269 involvement.  G34 pins the increment: all three pads copper-
        # connected, copper legal (10 trk 0.200 mm all B.Cu, ZERO vias), ADD-ONLY.
        print('  -- G34 FBV2-P2-024/D-322 rest-of-board incremental increment --')
        RSNET = '/08_BUTTONS_EXPANDERS/RESERVED_SPARE'
        rs_trk = [t for t in _g18.GetTracks()
                  if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == RSNET]
        rs_via = [t for t in all_via if t.GetNetname() == RSNET]

        j_rs = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                for p in _cc.GetConnectedItems(_pad('R130.2')) if p.GetClass() == 'PAD'}
        rs_conn = {'U23.7', 'TP41.1'}.issubset(j_rs)
        chk('G34 RESERVED_SPARE all three pads copper-connected (R130.2/U23.7/TP41.1)',
            'R130.2 joins %s' % sorted(j_rs & {'U23.7', 'TP41.1'}), rs_conn)

        rs_layers = {t.GetLayerName() for t in rs_trk}
        rs_legal = (len(rs_trk) == 10 and len(rs_via) == 0
                    and rs_layers == {'B.Cu'}
                    and all(t.GetWidth() == 200000 for t in rs_trk))
        chk('G34 RESERVED_SPARE copper legal (10 trk 0.200 mm all B.Cu, ZERO vias)',
            '%d trk layers=%s, vias=%d, widths=%s'
            % (len(rs_trk), sorted(rs_layers), len(rs_via),
               sorted({t.GetWidth() for t in rs_trk})), rs_legal)

        rs_addonly = (len(rs_trk) == 10 and len(rs_via) == 0
                      and len(sdcs_trk) == 20
                      and len(irtx_trk) == 13
                      and len(uart_trk) == 7
                      and len(imu1_trk) == 18
                      and len(xg3_trk) == 22 and len(xgw_trk) == 38 and len(xg_trk) == 23
                      and len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                      and len(irvs_trk) == 8 and len(rgbled_trk) == 25 and len(imu_trk) == 8
                      and len(disp_trk) == 11 and len(acc_trk) == 31
                      and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                      and len(phaseA_via) == 54)
        chk('G34 increment is ADD-ONLY (RESERVED_SPARE 10 + SD_CS 20 + IR_TX 13 + UART 7 + IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'reserved_spare=%d (exp 10, 0 via), sdcs=%d, irtx=%d, uart=%d, imu_int1=%d, xgpio3=%d, xgpio_w=%d, xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(rs_trk), len(sdcs_trk), len(irtx_trk), len(uart_trk), len(imu1_trk),
               len(xg3_trk), len(xgw_trk), len(xg_trk), len(sd_trk), len(amp_trk),
               len(tch_trk), len(irvs_trk), len(rgbled_trk), len(imu_trk), len(disp_trk),
               len(acc_trk), len(rgb_trk), len(phaseA_trk), len(phaseA_via)), rs_addonly)

        # -- G35 FBV2-P2-025/D-323 eighteenth rest-of-board incremental increment
        # The accelerometer/add-on presence-detect ACC_DETECT_N (R64.1 divider
        # F.Cu / R129.2 series B.Cu / U3.17 PCAL expander GPIO B.Cu), routed onto
        # the D-322 board by incremental_router.py in an OPEN region -- away from
        # the saturated west-XGPIO F.Cu corridor, the U11/BQ25185 power-tree wall,
        # the RF/NFC/USB/crystal/switching/rail/community-header mass, and every
        # characterized wall.  A genuine functional low-speed CMOS detect input,
        # PROMOTED after the cleaner-class candidate DISP_BL_CTL_STRAP (backlight-
        # control strap) hit a characterized local wall (all three MST edges
        # NO_PATH at 0.200 mm even on the fine grid -- the dense MCU/backlight pad
        # pocket boxes every terminal, the MCU_EN_RC lesson) and after BTN_B_N
        # FAILED the gate on connectivity (SW7 is a 4-pin tact switch whose two
        # terminals share pad "1" 7.96 mm apart -> the per-ref MST leaves the
        # second terminal unconnected; a whole-button-family framework limit, NOT
        # a copper casualty).  Three pads on TWO faces, so the MST is ONE
        # cross-layer edge R64.1<->R129.2 (a single 0.60/0.30 Default through via,
        # In1/In4 re-poured) + ONE same-layer B.Cu edge R129.2<->U3.17.  Default
        # netclass (0.200 mm); MEASURED the via 34.16 mm from every barrel and the
        # realized copper 3.8831 mm from BAT_PROTECTED_P -> ZERO D-269 involvement.
        # G35 pins the increment: all three pads copper-connected, copper legal
        # (22 trk 0.200 mm = 3 F.Cu + 19 B.Cu, exactly 1 0.60/0.30 through via),
        # via clears every barrel >= 0.80 mm, ADD-ONLY.
        print('  -- G35 FBV2-P2-025/D-323 rest-of-board incremental increment --')
        ADNET = '/ACC_DETECT_N'
        ad_trk = [t for t in _g18.GetTracks()
                  if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == ADNET]
        ad_via = [t for t in all_via if t.GetNetname() == ADNET]

        j_ad = {p.GetParentFootprint().GetReference() + '.' + p.GetNumber()
                for p in _cc.GetConnectedItems(_pad('R129.2')) if p.GetClass() == 'PAD'}
        ad_conn = {'R64.1', 'U3.17'}.issubset(j_ad)
        chk('G35 ACC_DETECT_N all three pads copper-connected (R64.1/R129.2/U3.17)',
            'R129.2 joins %s' % sorted(j_ad & {'R64.1', 'U3.17'}), ad_conn)

        ad_layers = collections.Counter(t.GetLayerName() for t in ad_trk)
        ad_via_ok = (len(ad_via) == 1
                     and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                             and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in ad_via))
        ad_legal = (len(ad_trk) == 22 and set(ad_layers) == {'F.Cu', 'B.Cu'}
                    and ad_layers['F.Cu'] == 3 and ad_layers['B.Cu'] == 19
                    and all(t.GetWidth() == 200000 for t in ad_trk) and ad_via_ok)
        chk('G35 ACC_DETECT_N copper legal (22 trk 0.200 mm = 3 F.Cu + 19 B.Cu, 1 0.60/0.30 through via)',
            '%d trk layers=%s, vias=%d, widths=%s'
            % (len(ad_trk), dict(ad_layers), len(ad_via),
               sorted({t.GetWidth() for t in ad_trk})), ad_legal)

        ad_gap = min([math.hypot(v.GetPosition().x - o.GetPosition().x,
                                 v.GetPosition().y - o.GetPosition().y)
                      for v in ad_via for o in all_via if o.GetNetname() != ADNET]
                     or [0])
        chk('G35 ACC_DETECT_N via >= 0.80 mm (centre) from every existing barrel',
            'min centre gap = %.3f mm' % (ad_gap / 1e6), ad_gap >= 800000)

        ad_addonly = (len(ad_trk) == 22 and len(ad_via) == 1
                      and len(rs_trk) == 10
                      and len(sdcs_trk) == 20
                      and len(irtx_trk) == 13
                      and len(uart_trk) == 7
                      and len(imu1_trk) == 18
                      and len(xg3_trk) == 22 and len(xgw_trk) == 38 and len(xg_trk) == 23
                      and len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                      and len(irvs_trk) == 8 and len(rgbled_trk) == 25 and len(imu_trk) == 8
                      and len(disp_trk) == 11 and len(acc_trk) == 31
                      and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                      and len(phaseA_via) == 54)
        chk('G35 increment is ADD-ONLY (ACC_DETECT_N 22/1via + RESERVED_SPARE 10 + SD_CS 20 + IR_TX 13 + UART 7 + IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'accdet=%d (exp 22, 1 via), reserved_spare=%d, sdcs=%d, irtx=%d, uart=%d, imu_int1=%d, xgpio3=%d, xgpio_w=%d, xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(ad_trk), len(rs_trk), len(sdcs_trk), len(irtx_trk), len(uart_trk),
               len(imu1_trk), len(xg3_trk), len(xgw_trk), len(xg_trk), len(sd_trk),
               len(amp_trk), len(tch_trk), len(irvs_trk), len(rgbled_trk), len(imu_trk),
               len(disp_trk), len(acc_trk), len(rgb_trk), len(phaseA_trk),
               len(phaseA_via)), ad_addonly)

        # -- G36 FBV2-P2-027/D-325 nineteenth rest-of-board incremental increment -
        # The navigation/boot button BTN_B_N (SW7.1 button F.Cu / R9.2 pull-up
        # B.Cu / U2.18 expander B.Cu) -- the FIRST net of the SWx user-button
        # family -- routed onto the D-323 board by incremental_router.py after the
        # DUPLICATE-REF MST framework fix (G37) let the MST + gate see SW7's TWO
        # physical "pad 1" lands (7.96 mm apart) as distinct nodes.  Its MST hubs
        # on R9.2 -> BOTH SW7.1 lands (two 0.60/0.30 Default THROUGH vias in the
        # OPEN south button field, In1/In4 re-poured) + one SAME-LAYER B.Cu run
        # R9.2->U2.18.  G36 pins the increment: ALL FOUR physical pads copper-
        # connected (both SW7.1 lands driven), copper legal (19 trk 0.200 mm =
        # 3 F.Cu + 16 B.Cu, exactly 2 0.60/0.30 through vias), both vias clear
        # every barrel >= 0.80 mm, ADD-ONLY.
        print('  -- G36 FBV2-P2-027/D-325 rest-of-board incremental increment --')
        BNET = '/08_BUTTONS_EXPANDERS/BTN_B_N'
        bn_trk = [t for t in _g18.GetTracks()
                  if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == BNET]
        bn_via = [t for t in all_via if t.GetNetname() == BNET]

        # BOTH physical SW7.1 lands must be copper-joined to the R9.2 hub -- the
        # decisive proof the duplicate-number terminal is no longer left open.
        _bn_pads = [p for f in _g18.GetFootprints() for p in f.Pads()
                    if p.GetNetname() == BNET]
        _sw_lands = [p for p in _bn_pads
                     if p.GetParentFootprint().GetReference() == 'SW7'
                     and p.GetNumber() == '1']
        _hub = _pad('R9.2')
        _hub_reach = {(pp.GetParentFootprint().GetReference() + '.' + pp.GetNumber(),
                       pp.GetPosition().x, pp.GetPosition().y)
                      for pp in _cc.GetConnectedItems(_hub) if pp.GetClass() == 'PAD'}
        bn_conn = (len(_sw_lands) == 2
                   and all(('SW7.1', p.GetPosition().x, p.GetPosition().y) in _hub_reach
                           for p in _sw_lands)
                   and any(pp[0] == 'U2.18' for pp in _hub_reach))
        chk('G36 BTN_B_N all four pads copper-connected (BOTH SW7.1 lands + R9.2 + U2.18)',
            'R9.2 hub joins %d SW7.1 land(s) + U2.18=%s'
            % (sum(1 for p in _sw_lands
                   if ('SW7.1', p.GetPosition().x, p.GetPosition().y) in _hub_reach),
               any(pp[0] == 'U2.18' for pp in _hub_reach)), bn_conn)

        bn_layers = collections.Counter(t.GetLayerName() for t in bn_trk)
        bn_via_ok = (len(bn_via) == 2
                     and all(v.GetWidth(pcbnew.F_Cu) == 600000 and v.GetDrill() == 300000
                             and v.GetViaType() == pcbnew.VIATYPE_THROUGH for v in bn_via))
        bn_legal = (len(bn_trk) == 19 and set(bn_layers) == {'F.Cu', 'B.Cu'}
                    and bn_layers['F.Cu'] == 3 and bn_layers['B.Cu'] == 16
                    and all(t.GetWidth() == 200000 for t in bn_trk) and bn_via_ok)
        chk('G36 BTN_B_N copper legal (19 trk 0.200 mm = 3 F.Cu + 16 B.Cu, 2 0.60/0.30 through vias)',
            '%d trk layers=%s, vias=%d, widths=%s'
            % (len(bn_trk), dict(bn_layers), len(bn_via),
               sorted({t.GetWidth() for t in bn_trk})), bn_legal)

        bn_gap = min([math.hypot(v.GetPosition().x - o.GetPosition().x,
                                 v.GetPosition().y - o.GetPosition().y)
                      for v in bn_via for o in all_via if o.GetNetname() != BNET]
                     or [0])
        chk('G36 BTN_B_N both vias >= 0.80 mm (centre) from every existing barrel',
            'min centre gap = %.3f mm' % (bn_gap / 1e6), bn_gap >= 800000)

        bn_addonly = (len(bn_trk) == 19 and len(bn_via) == 2
                      and len(ad_trk) == 22 and len(rs_trk) == 10
                      and len(sdcs_trk) == 20 and len(irtx_trk) == 13
                      and len(uart_trk) == 7 and len(imu1_trk) == 18
                      and len(xg3_trk) == 22 and len(xgw_trk) == 38 and len(xg_trk) == 23
                      and len(sd_trk) == 28 and len(amp_trk) == 19 and len(tch_trk) == 26
                      and len(irvs_trk) == 8 and len(rgbled_trk) == 25 and len(imu_trk) == 8
                      and len(disp_trk) == 11 and len(acc_trk) == 31
                      and len(rgb_trk) == 20 and len(phaseA_trk) == 432
                      and len(phaseA_via) == 54)
        chk('G36 increment is ADD-ONLY (BTN_B_N 19/2via + ACC_DETECT_N 22 + RESERVED_SPARE 10 + SD_CS 20 + IR_TX 13 + UART 7 + IMU_INT1 18 + XGPIO3 22 + west-XGPIO 38 + east-XGPIO 23 + SD 28 + AMP 19 + TOUCH 26 + IR_RX_VS 8 + RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54 preserved)',
            'btn=%d (exp 19, 2 via), accdet=%d, reserved_spare=%d, sdcs=%d, irtx=%d, uart=%d, imu_int1=%d, xgpio3=%d, xgpio_w=%d, xgpio_e=%d, sd=%d, amp=%d, touch=%d, irvs=%d, rgbled=%d, imu=%d, disp=%d, acc=%d, rgb=%d, phaseA=%d, phaseA_vias=%d'
            % (len(bn_trk), len(ad_trk), len(rs_trk), len(sdcs_trk), len(irtx_trk),
               len(uart_trk), len(imu1_trk), len(xg3_trk), len(xgw_trk), len(xg_trk),
               len(sd_trk), len(amp_trk), len(tch_trk), len(irvs_trk), len(rgbled_trk),
               len(imu_trk), len(disp_trk), len(acc_trk), len(rgb_trk), len(phaseA_trk),
               len(phaseA_via)), bn_addonly)

        # -- G37 FBV2-P2-027/D-325 DUPLICATE-REF MST framework lever -------------
        # The bounded, generic, deterministic framework fix that unlocked the SWx
        # user-button family, exercised as a UNIT contract on the live board.
        # qrouter.QBoard._scan keys self.pads[(net,"REF.NUM")], so a footprint that
        # places two physical lands with the SAME pad number on one net (a 4-pin
        # tact switch's two "pad 1" terminals) collapses to a single node and one
        # land is invisible to the MST -- the D-323 BTN_B_N gate FAIL.  The fix
        # lives ENTIRELY in incremental_router.py (qrouter untouched, so every
        # QBoard-routing fixture above stays byte-identical): physical_net_pads()
        # keys MST nodes by physical (ref,x,y).  G37 proves the four properties
        # the mandate requires: (a) a duplicate pad NUMBER yields DISTINCT nodes;
        # (b) an ordinary unique-pad net is BYTE-IDENTICAL (same dict objects) to
        # the pre-fix ref-keyed order -- no topology/rule weakening; (c) the
        # behaviour is DETERMINISTIC; (d) the MST reaches every physical land.
        print('  -- G37 FBV2-P2-027/D-325 duplicate-ref MST framework lever --')
        import incremental_router as IR
        _qb = QR.QBoard(auth)

        # (a) duplicate-number lands become DISTINCT physical nodes
        dup = IR.physical_net_pads(_qb, BNET)
        dup.sort(key=lambda p: (p['ref'], p['x'], p['y']))
        sw_nodes = [p for p in dup if p['ref'] == 'SW7.1']
        chk('G37 duplicate pad number -> distinct nodes (BTN_B_N: 4 lands, TWO SW7.1)',
            '%d nodes, SW7.1 at %s'
            % (len(dup), sorted((round(p['x'] / 1e6, 3), round(p['y'] / 1e6, 3))
                                for p in sw_nodes)),
            len(dup) == 4 and len(sw_nodes) == 2
            and sw_nodes[0]['x'] != sw_nodes[1]['x'])

        # the MST over the 4 physical nodes has 3 edges and touches all 4 nodes
        _edges = IR.mst_edges(dup)
        _touched = set()
        for (i, j) in _edges:
            _touched.add(i)
            _touched.add(j)
        chk('G37 MST over duplicate-aware nodes spans all 4 lands (3 edges)',
            '%d edges, %d/4 nodes touched' % (len(_edges), len(_touched)),
            len(_edges) == 3 and len(_touched) == 4)

        # (b) ordinary unique-pad net is BYTE-IDENTICAL: physical_net_pads returns
        # the SAME dict objects, same order, as the pre-fix ref-keyed selection.
        ONET = '/ACC_DETECT_N'
        _old = IR.net_pads(_qb, ONET)
        _old_by_ref = {p['ref']: p for p in _old}
        _old_order = [_old_by_ref[r] for r in sorted(_old_by_ref)]
        _new = IR.physical_net_pads(_qb, ONET)
        _new.sort(key=lambda p: (p['ref'], p['x'], p['y']))
        chk('G37 ordinary unique-pad net byte-identical (same dict OBJECTS, no phantom node)',
            '%d==%d pads, same objects=%s'
            % (len(_old_order), len(_new),
               all(a is b for a, b in zip(_old_order, _new))),
            len(_new) == len(_old_order)
            and all(a is b for a, b in zip(_old_order, _new)))

        # (c) DETERMINISTIC: a second call yields the identical physical identities
        _again = IR.physical_net_pads(_qb, BNET)
        _again.sort(key=lambda p: (p['ref'], p['x'], p['y']))
        chk('G37 physical_net_pads deterministic (identical (ref,x,y) across calls)',
            'stable',
            [(p['ref'], p['x'], p['y']) for p in dup]
            == [(p['ref'], p['x'], p['y']) for p in _again])

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
