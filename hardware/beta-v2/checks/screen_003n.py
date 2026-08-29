#!/usr/bin/env python3
"""FBV2-P2-003N -- standing LTC-block placement candidate screen (D-286 real DRC).

For every bounded direction-1 LTC-block placement candidate this tool applies,
on a REAL scratch board at the EXACT D-286 pre-copper boundary --

    002F ECO (place_p2_002f)  +  AQROOT_ECO_EXTRA = place_003l  +  candidate moves
    -> BuildConnectivity -> ZONE_FILLER.Fill -> Save

-- the real `kicad-cli pcb drc --severity-all` and the real QBoard pad-escape
solver (the SAME `qb.escape` the router uses), and rejects any candidate that
introduces, versus the place_003l-only CLEAN reference, a:

  * different-net pad short        (shorting_items)
  * sub-0.200 mm clearance         (clearance -- the floor is 0.200 mm, so ANY
                                    new clearance item is by definition a breach)
  * net-agnostic hole-floor breach (hole_clearance / holes_co_located)
  * courtyard / mechanical overlap (courtyards_overlap)
  * unescapable required LTC pin   (qb.escape == [] at the rule floor)

This is the instrument D-286 mandates: real full-placement DRC, NOT the analytic
"mech-clean" prefilter that graded the invalid c3_00 as rank-1.  Read-only;
throwaway scratch under w/screen_003n/.  Emits w/screen_003n/results.json and a
human table.  `screen_003n.py --validate` asserts the c3_00 self-check (must be
REJECT with >=1 shorting_items) and the place_003l reference (must be CLEAN) --
that is the 003N screen regression.
"""
import os, sys, json, shutil, subprocess, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew
import harness_paths as HP

CK = HERE
PRJ = HP.project_dir()
PCBNAME = HP.PCBNAME
WORK = os.path.join(CK, 'w', 'screen_003n')
CAND_DIR = os.path.join(CK, 'place_002z')
PLACE_003L = os.path.join(CK, 'place_003l.json')

# The COMPLETE bounded direction-1 candidate space (27) named by D-286 /
# CURRENT_STATE / the 003N inventory:
#   b1 family  (6): single-move R75/Q3/U18 rotations off AUTHORITATIVE home
#   c3 family  (4): card-3, U18+R79+R75
#   cand_00..11(12): card-2, U18+R81
#   c2 family  (5): card-2 east/west spreads
# b1 is screened FIRST -- its survivors are the primary integration candidates.
B1   = ['b1_r75rot.json', 'b1_r75rotN.json', 'b1_q3rot.json',
        'b1_r75rotE2.json', 'b1_r75rotNE.json', 'b1_u18ctrl.json']
C3   = ['c3_00.json', 'c3_01.json', 'c3_02.json', 'c3_03.json']
CAND = ['cand_%02d.json' % i for i in range(12)]
C2   = ['c2_e10n.json', 'c2_e10.json', 'c2_e05.json', 'c2_w05.json', 'c2_E2r.json']
CANDIDATES = B1 + C3 + CAND + C2

# U18 (LTC4368) routable pins that MUST be able to escape (4,5 are GND, exempt).
U18_REQUIRED = ['1', '2', '3', '6', '7', '8', '9', '10']

# clearance/hole floors (nm) -- reference only; kicad-cli enforces the DRU.
CP = 200000          # 0.200 mm pad/track clearance floor
CT_W = 300000        # 0.300 mm default track width (escape need)
FLOOR_ESCAPE = 50000  # 0.050 mm rule-minimum probe width -> [] means truly dead

HARD_CLASSES = ('shorting_items', 'clearance', 'hole_clearance',
                'holes_co_located', 'courtyards_overlap')
WARN_CLASSES = ('solder_mask_bridge', 'silk_over_copper', 'silk_overlap')


def build(name, place_json):
    """Real scratch board at the D-286 pre-copper boundary.  place_json=None
    builds the place_003l-only clean reference."""
    dst = os.path.join(WORK, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(PRJ, dst)
    pcb = os.path.join(dst, PCBNAME)
    import sixlayer as SIX
    SIX.convert(pcb)
    import place_p2_002f as ECO
    ov = json.load(open(PLACE_003L))
    saved = dict(ECO.MOVES)
    for r, v in ov.items():
        ECO.MOVES[r] = tuple(v)
    ECO.apply(pcb, report=False)
    ECO.MOVES.clear(); ECO.MOVES.update(saved)
    bb = pcbnew.LoadBoard(pcb)
    if place_json:
        spec = json.load(open(place_json))
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
    return pcb


def drc(pcb, tag):
    out = os.path.join(WORK, 'drc_%s.json' % tag)
    subprocess.run([HP.kicad_cli(), 'pcb', 'drc', '--severity-all', '--format',
                    'json', '-o', out, pcb], capture_output=True, text=True)
    j = json.load(open(out, encoding='utf-8'))
    cnt = collections.Counter()
    items = collections.defaultdict(list)
    for key in ('violations', 'unconnected_items', 'schematic_parity'):
        for v in j.get(key, []):
            t = v.get('type', key)
            cnt[t] += 1
            items[t].append(v)
    return cnt, items


def nearest_pads(pcb, x_nm, y_nm, k=3):
    b = pcbnew.LoadBoard(pcb)
    best = []
    for f in b.GetFootprints():
        for p in f.Pads():
            pos = p.GetPosition()
            d = ((pos.x - x_nm) ** 2 + (pos.y - y_nm) ** 2) ** 0.5
            best.append((d, '%s.%s[%s]' % (f.GetReference(), p.GetNumber(),
                                           p.GetNetname().split('/')[-1])))
    best.sort()
    return best[:k]


def attribute(pcb, items, cls):
    """Human strings mapping each item of `cls` to its nearest pads."""
    out = []
    for v in items.get(cls, []):
        desc = v.get('description', '')[:120]
        locs = []
        for it in v.get('items', []):
            pos = it.get('pos')
            if pos:
                xn = int(round(pos['x'] * 1e6)); yn = int(round(pos['y'] * 1e6))
                nn = nearest_pads(pcb, xn, yn)
                locs.append('@(%.3f,%.3f)->%s' % (
                    pos['x'], pos['y'],
                    '/'.join('%s(%.2f)' % (r, d / 1e6) for d, r in nn[:2])))
        out.append({'desc': desc, 'locs': locs})
    return out


def escape_probe(pcb):
    """Real QBoard escape for each required U18 pin on the bare placement.
    A required pin with [] escapes at the 0.05 mm rule floor is UNESCAPABLE."""
    import qrouter as QR
    qb = QR.QBoard(pcb)
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads[ref] = p
    res = {}
    unescapable = []
    for pin in U18_REQUIRED:
        ref = 'U18.%s' % pin
        pad = pads.get(ref)
        if pad is None:
            res[ref] = {'net': '?', 'floor_ok': None, 'ct_ways': None,
                        'why': 'pad not found on board'}
            continue
        net = pad['net'].split('/')[-1]
        e_floor = qb.escape(pad, 'B', FLOOR_ESCAPE, FLOOR_ESCAPE, CP, CT_W,
                            25000, qb.ex0, qb.ey0)
        e_ct = qb.escape(pad, 'B', CT_W, CT_W, CP, CT_W, 25000, qb.ex0, qb.ey0)
        why = '' if e_floor else '; '.join(qb.escape_why)[:160]
        res[ref] = {'net': net, 'floor_ok': bool(e_floor),
                    'ct_ways': len(e_ct), 'why': why}
        if not e_floor:
            unescapable.append('%s[%s]' % (ref, net))
    return res, unescapable


def _place_with_areas(tag, place_json):
    """Build the D-286 placed board (build) AND install the router's named areas +
    DRU rules, so the QBoard escape/traverse solver sees exactly what the full
    driver sees at the pre-route boundary.  Mirrors route_battery_block.main()
    lines 328-330 and bridge_early_003i.reconstruct_placed."""
    import route_battery_block as RB
    import path_role_util as RU
    import path_role_dru as DRU
    pcb = build(tag, place_json)
    b = pcbnew.LoadBoard(pcb)
    for a in RB.AREAS + RB.STUBAREAS + RB.FINEAREAS:
        RU.add_named_area(b, a, 0, 0, 1000, 1000)
    b.Save(pcb)
    DRU.write(pcb, [])
    return pcb


def bridge_probe(fname):
    """FBV2-P2-003N standing bridge-connectivity regression.

    Reproduces the EXACT early southern D-275 bridge (bridge_early_003i.apply_early
    south=True) in ISOLATION on this candidate's D-286 placed board -- the same
    stage the full driver fires at its first '8*' item -- then fills, saves and runs
    the real kicad-cli DRC.  This is the cheap discriminator for the b1_r75rot
    dangling-via mechanism: a geometrically-placed bridge (entry/exit array laid,
    traverse OK) is NOT electrical connectivity.  KiCad's `via_dangling` is the
    authoritative >=2-layer-connected test -- a via connected on only one layer (or
    to an isolated island) is a genuine electrical fault and MUST fail.  Each
    dangling via is attributed to its nearest pad so entry(R75.2) vs exit(C36.1/
    node) is identifiable.  Verdict CONNECTED iff the bridge laid AND via_dangling
    == 0 AND entry>=3 AND exit>=3 AND disjoint ywest>75 AND traverse w>=1.20 mm."""
    import qrouter as QR
    import bridge_early_003i as BE
    import bridge_route_003c as BR
    tag = fname.replace('.json', '')
    pcb = _place_with_areas('BP_' + tag, os.path.join(CAND_DIR, fname))
    qb = QR.QBoard(pcb)
    qb.wide_nets = frozenset(BR.N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                                'BAT_MID', 'BAT_SENSE',
                                                'BAT_PROTECTED_P'))
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(net, {})[ref] = p
    rec = BE.apply_early(qb, pads, south=True)
    laid = bool(rec.get('ok'))
    if laid:
        pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
        qb.save()
    cnt, items = drc(pcb, 'bp_' + tag)
    dangling = cnt.get('via_dangling', 0)
    dang_detail = attribute(pcb, items, 'via_dangling') if dangling else []
    trav = rec.get('traverse', {}) or {}
    ywest = rec.get('south_ywest_mm')
    entry_n = len(rec.get('entry_vias', []) or [])
    exit_n = rec.get('exit_vias', 0)
    ok = (laid and dangling == 0 and entry_n >= 3 and exit_n >= 3
          and (ywest is not None and ywest > 75.0)
          and bool(trav.get('ok')) and (trav.get('w_mm', 0) >= 1.20))
    reasons = []
    if not laid:
        reasons.append('bridge did NOT lay: ' + str(rec.get('fail', '?')))
    else:
        if dangling:
            reasons.append('via_dangling %d (genuine electrical fault)' % dangling)
        if entry_n < 3:
            reasons.append('entry array %d < 3' % entry_n)
        if exit_n < 3:
            reasons.append('exit array %d < 3' % exit_n)
        if ywest is None or ywest <= 75.0:
            reasons.append('not disjoint: ywest=%s !> 75' % ywest)
        if not trav.get('ok') or trav.get('w_mm', 0) < 1.20:
            reasons.append('traverse w=%s < 1.20' % trav.get('w_mm'))
    return {
        'file': fname, 'verdict': 'CONNECTED' if ok else 'FAIL',
        'reasons': reasons,
        'land': rec.get('land'), 'landing': rec.get('landing'),
        'traverse': trav, 'entry_vias': entry_n, 'exit_vias': exit_n,
        'ywest_mm': ywest, 'via_dangling': dangling,
        'via_dangling_detail': dang_detail,
        'bridge_fail': rec.get('fail'), 'bridge_tried': rec.get('tried'),
    }


def verdict(delta, unescapable):
    reasons = []
    for cls in HARD_CLASSES:
        if delta.get(cls, 0) > 0:
            reasons.append('%s +%d' % (cls, delta[cls]))
    if unescapable:
        reasons.append('unescapable: ' + ','.join(unescapable))
    warns = [('%s +%d' % (c, delta[c])) for c in WARN_CLASSES if delta.get(c, 0) > 0]
    return ('REJECT' if reasons else 'PASS'), reasons, warns


def screen_one(fname, ref_cnt):
    path = os.path.join(CAND_DIR, fname)
    spec = json.load(open(path))
    tag = fname.replace('.json', '')
    pcb = build('C_' + tag, path)
    cnt, items = drc(pcb, tag)
    delta = {k: cnt.get(k, 0) - ref_cnt.get(k, 0)
             for k in set(cnt) | set(ref_cnt) if cnt.get(k, 0) != ref_cnt.get(k, 0)}
    esc, unescapable = escape_probe(pcb)
    v, reasons, warns = verdict(delta, unescapable)
    rec = {
        'file': fname, 'name': spec.get('name'),
        'moves': {r: spec['moves'][r] for r in spec.get('moves', {})},
        'verdict': v, 'reasons': reasons, 'warns': warns,
        'drc_hist': dict(sorted(cnt.items())), 'delta_vs_ref': delta,
        'escape': esc, 'unescapable': unescapable,
        'short_detail': attribute(pcb, items, 'shorting_items'),
        'clearance_detail': attribute(pcb, items, 'clearance'),
        'courtyard_detail': attribute(pcb, items, 'courtyards_overlap'),
    }
    return rec


def bridge_main(only):
    """--bridge: run the standing bridge-connectivity regression on the given
    candidates (default: the three D-286 hard-gate survivors)."""
    os.makedirs(WORK, exist_ok=True)
    todo = only if only else ['b1_r75rot.json', 'b1_r75rotN.json', 'b1_q3rot.json']
    recs = []
    for fname in todo:
        if not os.path.exists(os.path.join(CAND_DIR, fname)):
            print('  SKIP %-16s (absent)' % fname); continue
        r = bridge_probe(fname)
        recs.append(r)
        print('%-14s %-9s land=%-6s trav=%s w=%s entry=%d exit=%d ywest=%s '
              'dangling=%d %s' % (
                  fname, r['verdict'], r['land'],
                  (r['traverse'].get('mm') if r['traverse'] else None),
                  (r['traverse'].get('w_mm') if r['traverse'] else None),
                  r['entry_vias'], r['exit_vias'], r['ywest_mm'],
                  r['via_dangling'],
                  ('| ' + '; '.join(r['reasons'])) if r['reasons'] else ''))
        for d in r['via_dangling_detail']:
            print('        dangling @ %s' % '; '.join(d.get('locs', [])))
    with open(os.path.join(WORK, 'bridge_probe.json'), 'w') as f:
        json.dump({'results': recs}, f, indent=1)
    conn = [r for r in recs if r['verdict'] == 'CONNECTED']
    print('\n=== BRIDGE PROBE: %d/%d truly-connected (zero dangling) ===' % (
        len(conn), len(recs)))
    if '--validate' in sys.argv:
        # Standing bridge integration regression: the D-275 south-bridge ENTRY array
        # (R75.2 POFV) is bussed on F.Cu with NO symmetric B.Cu tie-stub, so its
        # vias dangle -- a GENUINE electrical fault the probe MUST catch and FAIL.
        by = {r['file']: r for r in recs}
        c = by.get('b1_r75rot.json')
        if not (c and c['verdict'] == 'FAIL' and c['via_dangling'] >= 1):
            print('VALIDATE FAIL: b1_r75rot must be FAIL with >=1 via_dangling '
                  '(the entry-array dangling control)')
            sys.exit(1)
        print('VALIDATE OK: b1_r75rot FAIL (via_dangling +%d, entry array on R75.2) '
              'reproduced -- geometric bridge != electrical connectivity'
              % c['via_dangling'])
        sys.exit(0)
    return recs


def main():
    validate = '--validate' in sys.argv
    bridge = '--bridge' in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    if bridge:
        bridge_main(only)
        return
    os.makedirs(WORK, exist_ok=True)

    print('Building place_003l-only CLEAN reference (D-286 boundary) ...')
    ref_pcb = build('REF_place_003l', None)
    ref_cnt, _ = drc(ref_pcb, 'ref')
    print('REFERENCE histogram:', dict(sorted(ref_cnt.items())))
    print()

    todo = only if only else CANDIDATES
    results = []
    for fname in todo:
        if not os.path.exists(os.path.join(CAND_DIR, fname)):
            print('  SKIP %-16s (absent)' % fname); continue
        rec = screen_one(fname, ref_cnt)
        results.append(rec)
        u = rec['moves'].get('U18')
        print('%-14s %-7s U18=%-22s delta=%s %s' % (
            fname, rec['verdict'], (str(u[:3]) if u else '(home)'),
            rec['delta_vs_ref'] or '{}',
            ('| ' + '; '.join(rec['reasons'])) if rec['reasons'] else ''))

    payload = {'reference_hist': dict(sorted(ref_cnt.items())),
               'u18_required': U18_REQUIRED, 'results': results}
    with open(os.path.join(WORK, 'results.json'), 'w') as f:
        json.dump(payload, f, indent=1)

    passes = [r for r in results if r['verdict'] == 'PASS']
    print('\n=== SCREEN SUMMARY: %d/%d candidates PASS Stage-1+2 ===' % (
        len(passes), len(results)))
    for r in passes:
        print('  PASS', r['file'], r['moves'].get('U18'))

    if validate:
        by = {r['file']: r for r in results}
        ok = True
        c = by.get('c3_00.json')
        if not (c and c['verdict'] == 'REJECT' and
                c['delta_vs_ref'].get('shorting_items', 0) >= 1):
            print('VALIDATE FAIL: c3_00 must be REJECT with >=1 new shorting_items')
            ok = False
        else:
            print('VALIDATE OK: c3_00 REJECT (shorting_items +%d) reproduced'
                  % c['delta_vs_ref'].get('shorting_items', 0))
        if any(ref_cnt.get(x, 0) for x in ('shorting_items', 'clearance',
                                           'courtyards_overlap')):
            print('VALIDATE FAIL: place_003l reference is not clean:',
                  dict(ref_cnt))
            ok = False
        else:
            print('VALIDATE OK: place_003l reference clean (no short/clearance/courtyard)')
        sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
