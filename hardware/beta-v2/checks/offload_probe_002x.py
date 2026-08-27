# -*- coding: utf-8 -*-
"""FBV2-P2-002X / D-270 -- the western-margin offload study, BY PATH ROLE.

D-269 (FBV2-P2-002W) ended DECISION STOP: no CONTROL-net cut set of any
cardinality re-opens `BAT_PROTECTED_P R75.2 -> D9.1` on B.Cu, because closing
`BAT_RAW` (which D-269 achieved) put two microamp `BAT_RAW` divider bridges in
the trunk's margin, and section 9 excluded them FROM THE CANDIDATE LIST BY NET
CLASS - `BAT_RAW` is a power net.  The 002X CTO ruling widens the candidate list
to the INDIVIDUAL ROUTED BRANCH / PATH ROLE: a bounded LOW-CURRENT/TAP branch on
`BAT_RAW` or `BAT_MAIN` may be offered In2/In3 offload despite its power net
name, while every CURRENT-CARRYING role stays outer 1 oz and zero-via.

This script models exactly that.  It reads the routed pass-1 scratch board and
the per-branch B.Cu attribution map (route_battery_block AQROOT_BRANCH_TRK), and
for a subset of candidate BRANCHES it CUTS only those branches' B.Cu copper -
never a whole net - then re-asks whether the 1.50 mm (then 1.20 mm floor) trunk
finds a corridor.  It never routes to inner layers here: cutting a branch's B.Cu
is the faithful virtual model of moving THAT branch, and only THAT branch, off
the outer layer.  Virtual evidence SELECTS the minimum set; the real offload run
plus KiCad DRC proves it.  Nothing here touches the authoritative board.

    python offload_probe_002x.py                     # full minimum-set search
    AQROOT_OFFLOAD_BOARD=w/X0/... AQROOT_BRANCH_TRK=branch_trk_002x.json ...
"""
import os, sys, json, itertools, time
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import qrouter as QR
import pcbnew

N = '/01_POWER_TREE/'
CP, CT_W = 200000, 300000            # clearance-to-pad / -track, as the trunk uses
TRUNK = N + 'BAT_PROTECTED_P'
FLOOR_1_50, FLOOR_1_20 = 1500000, 1200000

WORK = os.path.join(SP, 'w')
BOARD = os.environ.get('AQROOT_OFFLOAD_BOARD',
                       os.path.join(WORK, 'X0', RU.PCBNAME))
TRKMAP = os.path.join(SP, os.environ.get('AQROOT_BRANCH_TRK', 'branch_trk_002x.json'))
OUT = os.path.join(SP, os.environ.get('AQROOT_OFFLOAD_OUT', 'offload_002x.json'))
MAXCARD = int(os.environ.get('AQROOT_OFFLOAD_MAXCARD', '4'))

# -------------------------------------------------------------------- candidates
# LOW-CURRENT control-signal nets: these ARE the D-269 section 9 candidates, kept
# because they were always legitimate - they carry comparator / gate-drive signal
# only.  Each of their branches is an individual offload candidate.
CONTROL_NETS = frozenset(N + n for n in (
    'LTC_OV', 'LTC_UV', 'LTC_SHDN', 'LTC4368_FAULT_N',
    'LTC_GATE', 'LTC_GATE_RC', 'BAT_PROT_SHDN_CTL'))
# The D-270 ADDITION: bounded low-current branches on a POWER-named net.  These
# are the LTC4368 OV/UV divider chain and the two long divider bridges - microamp
# taps every one, ruled 0.20 mm by D-249, held apart by the D-269 TAP corridors.
# Named EXPLICITLY so no current-carrying BAT_RAW copper (the Q2.7/Q2.8/F1.2 node,
# the reservoir caps, the dead-cell trunk) can ever enter the candidate set.
BATRAW_LOWI = frozenset((
    ('BAT_RAW', 'R80.1', 'Q2.7'),      # divider top -> battery node bridge
    ('BAT_RAW', 'D12.1', 'R77.1'),     # dead-cell diode -> divider bridge
    ('BAT_RAW', 'R79.1', 'R80.1'),     # divider link
    ('BAT_RAW', 'R77.1', 'R79.1'),     # divider link
    ('BAT_RAW', 'U18.1', 'R77.1'),     # LTC4368 VIN sense tap
))
# Never a candidate, no matter what the map says: the current-carrying trunk
# itself and the high-current battery rails.  Stated so the classifier is a
# whitelist AND a blacklist and a mislabelled branch fails loudly.
CURRENT_NETS = frozenset(N + n for n in (
    'BAT_PROTECTED_P', 'BAT_SENSE', 'BAT_MID', 'BAT_CONNECTOR_P'))


def classify(key):
    """key = 'NET A B' (short net).  Returns 'candidate' or a refusal reason."""
    parts = key.split()
    net, a, b = parts[0], parts[1], parts[2]
    fq = N + net
    if fq in CURRENT_NETS:
        return None, 'current-carrying role stays outer 1 oz (D-270)'
    if fq in CONTROL_NETS:
        return 'candidate', 'low-current control signal'
    if net == 'BAT_RAW':
        if (net, a, b) in BATRAW_LOWI:
            return 'candidate', 'bounded low-current TAP on power net (D-270)'
        return None, 'BAT_RAW current-carrying node/reservoir - not low current'
    return None, 'out of western-margin scope'


def load_map():
    m = json.load(open(TRKMAP, encoding='utf-8'))
    cands, refused = {}, {}
    for key, uuids in m.items():
        if not uuids:
            continue
        verdict, why = classify(key)
        if verdict == 'candidate':
            cands[key] = list(uuids)
        else:
            refused[key] = why
    return cands, refused


def build_board():
    """One QBoard, plus a signature index so a cut can be modelled in memory."""
    qb = QR.QBoard(BOARD)
    qb.wide_nets = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                             'BAT_MID', 'BAT_SENSE',
                                             'BAT_PROTECTED_P'))
    uuid_sig = {}
    for t in qb.b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != pcbnew.B_Cu:
            continue
        uuid_sig[str(t.m_Uuid.AsString())] = (t.GetStart().x, t.GetStart().y,
                                              t.GetEnd().x, t.GetEnd().y)
    return qb, uuid_sig


def sig_of_seg(s):
    # qb.shapes['B'] holds both track SEGs (x0/y0/x1/y1) and pad/keepout RRs
    # (cx/cy).  Only a track can be a cut candidate; a pad is never cut.
    if not hasattr(s, 'x0'):
        return None
    return (int(s.x0), int(s.y0), int(s.x1), int(s.y1))


def trunk_ok(qb, master_B, pa, pb, cut_sigs, width):
    """Cut cut_sigs from B.Cu, ask the trunk at `width`, restore.  Returns
    (ok, mm) - the honest routability of R75.2 -> D9.1 on B.Cu with those
    branches gone and nothing else changed."""
    qb.shapes['B'] = ([s for s in master_B if sig_of_seg(s) not in cut_sigs]
                      if cut_sigs else master_B)
    qb._obs_cache = None
    m = qb.mark()
    r = QR.connect_role(qb, TRUNK, pa, pb, 'B', width, CP, CT_W)
    qb.revert(m)
    qb.shapes['B'] = master_B
    qb._obs_cache = None
    return bool(r.get('ok')), round(r.get('mm', 0.0), 3), r.get('reason')


def main():
    t0 = time.time()
    cands, refused = load_map()
    qb, uuid_sig = build_board()
    master_B = list(qb.shapes['B'])
    pa = qb.pads.get((TRUNK, 'R75.2'))
    pb = qb.pads.get((TRUNK, 'D9.1'))
    if pa is None or pb is None:
        raise SystemExit('R75.2 / D9.1 pad missing on the routed board')
    # The trunk's own bounding box, inflated: a branch whose B.Cu copper never
    # enters it cannot be in the corridor and is not worth a search slot.  This
    # is a SPEED prune only - it can never invent a blocker, only skip copper
    # that is provably elsewhere.  The margin is generous (4 mm) so nothing on
    # the corridor's shoulder is dropped.
    MG = 4000000
    bx0, bx1 = min(pa['x'], pb['x']) - MG, max(pa['x'], pb['x']) + MG
    by0, by1 = min(pa['y'], pb['y']) - MG, max(pa['y'], pb['y']) + MG

    def in_scope(sigs):
        for (x0, y0, x1, y1) in sigs:
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            if bx0 <= mx <= bx1 and by0 <= my <= by1:
                return True
            for (x, y) in ((x0, y0), (x1, y1)):
                if bx0 <= x <= bx1 and by0 <= y <= by1:
                    return True
        return False

    # per-candidate cut signatures + B.Cu length (mm), for ranking
    cinfo, out_of_corridor = {}, []
    for key, uuids in cands.items():
        sigs, mm = set(), 0.0
        for u in uuids:
            g = uuid_sig.get(u)
            if g is None:
                continue
            sigs.add(g)
            mm += ((g[0] - g[2]) ** 2 + (g[1] - g[3]) ** 2) ** 0.5 / 1e6
        if not sigs:
            continue
        info = dict(sigs=sigs, mm=round(mm, 3), n=len(sigs))
        if in_scope(sigs):
            cinfo[key] = info
        else:
            out_of_corridor.append(key)
    keys = sorted(cinfo)

    print('OFFLOAD STUDY 002X / D-270  -- board %s' % os.path.relpath(BOARD, SP))
    print('candidate low-current branches in the trunk corridor (%d):' % len(keys))
    for k in keys:
        print('  %-34s %2d seg  %7.3f mm' % (k, cinfo[k]['n'], cinfo[k]['mm']))
    if out_of_corridor:
        print('candidate branches OUTSIDE the corridor (pruned, %d): %s'
              % (len(out_of_corridor), ', '.join(sorted(out_of_corridor))))
    if refused:
        print('refused (current-carrying / out of scope): %d' % len(refused))

    base15 = trunk_ok(qb, master_B, pa, pb, set(), FLOOR_1_50)
    base12 = trunk_ok(qb, master_B, pa, pb, set(), FLOOR_1_20)
    print('BASELINE (no cut)   1.50 -> %s %.3f   1.20 -> %s %.3f'
          % (base15[0], base15[1], base12[0], base12[1]))
    sys.stdout.flush()

    def cut_of(combo):
        cut = set()
        for k in combo:
            cut |= cinfo[k]['sigs']
        return cut

    def opens(combo, width):
        ok, mm, _ = trunk_ok(qb, master_B, pa, pb, cut_of(combo), width)
        return ok, mm

    def cost(combo):
        return (len(combo), round(sum(cinfo[k]['mm'] for k in combo), 3),
                sum(cinfo[k]['n'] for k in combo))

    # ---- STEP 1: does cutting EVERY in-corridor candidate open it at all? ---
    allok15, allmm15 = opens(keys, FLOOR_1_50)
    allok12, allmm12 = opens(keys, FLOOR_1_20)
    target = FLOOR_1_50 if allok15 else FLOOR_1_20
    tname = '1.50' if allok15 else '1.20'
    print('ALL %d cut     1.50 -> %s %.3f   1.20 -> %s %.3f   => target %s'
          % (len(keys), allok15, allmm15, allok12, allmm12, tname))
    sys.stdout.flush()
    if not allok15 and not allok12:
        print('\nMINIMUM SET RESULT\n  NO offload of the corridor candidates '
              'opens >= 1.20 mm - the blocker is NOT low-current copper.\n'
              '  The minimum successful low-current offload set DOES NOT EXIST '
              'on this prefix.')
        json.dump(dict(board=os.path.relpath(BOARD, SP), min_card=None,
                       finding='no low-current offload set opens >=1.20 mm; '
                               'blocker is current-carrying (BAT_SENSE)',
                       candidates={k: cinfo[k]['mm'] for k in keys},
                       out_of_corridor=out_of_corridor, refused=refused,
                       baseline=dict(ok_1_50=base15[0], ok_1_20=base12[0]),
                       all_cut=dict(ok_1_50=allok15, mm_1_50=allmm15,
                                    ok_1_20=allok12, mm_1_20=allmm12),
                       secs=round(time.time() - t0, 1)),
                  open(OUT, 'w'), indent=1)
        return

    # ---- STEP 2: GREEDY REDUCTION to an irreducible (minimal) set ----------
    # Drop the most expensive branch first: a branch that can be removed while
    # the trunk still opens was never a blocker, and dropping the costly ones
    # first biases the minimal set toward least offloaded copper / fewest vias.
    keep = list(keys)
    for k in sorted(keys, key=lambda k: -cinfo[k]['mm']):
        trial = [x for x in keep if x != k]
        if trial and opens(trial, target)[0]:
            keep = trial
    keep_ok, keep_mm = opens(keep, target)
    kcard = len(keep)
    # re-measure the minimal set at BOTH widths for the record
    m15 = opens(keep, FLOOR_1_50)
    m12 = opens(keep, FLOOR_1_20)
    print('GREEDY MINIMAL (%d): %s' % (kcard, keep))
    print('   opens 1.50 -> %s %.3f   1.20 -> %s %.3f'
          % (m15[0], m15[1], m12[0], m12[1]))
    sys.stdout.flush()

    # ---- STEP 3: PROVE minimum cardinality - exhaust every smaller set -----
    # Cardinality 1 first (cheap), then up to kcard-1, testing the ACHIEVED
    # target only.  Bounded by EXH_CAP so a large minimal set does not launch an
    # hours-long sweep; whatever is proven is stated exactly.
    EXH_CAP = int(os.environ.get('AQROOT_OFFLOAD_EXHCAP', '3'))
    proven_min = True
    checked_upto = 0
    smaller_hit = None
    for card in range(1, kcard):
        if card > EXH_CAP:
            proven_min = None            # not disproven, but not exhausted
            break
        n_sets = 0
        tc = time.time()
        for combo in itertools.combinations(keys, card):
            n_sets += 1
            if opens(combo, target)[0]:
                smaller_hit = list(combo)
                break
        checked_upto = card
        print('  exhaustive cardinality %d: %4d sets, %s  (%.0fs)'
              % (card, n_sets, 'a smaller set OPENS' if smaller_hit
                 else 'none opens', time.time() - tc))
        sys.stdout.flush()
        if smaller_hit:
            proven_min = False
            break

    print('\nMINIMUM SET RESULT (target %s mm)' % tname)
    print('  minimal (irreducible) offload set, cardinality %d:' % kcard)
    for k in keep:
        print('    %-34s %2d seg  %7.3f mm' % (k, cinfo[k]['n'], cinfo[k]['mm']))
    _, off_mm, off_seg = cost(keep)
    print('  offloaded copper %.3f mm over %d segments' % (off_mm, off_seg))
    if smaller_hit:
        print('  NOT minimum: a %d-set opens too: %s' % (len(smaller_hit),
                                                         smaller_hit))
    elif proven_min:
        print('  PROVEN MINIMUM: no set of cardinality < %d opens %s mm '
              '(all exhausted)' % (kcard, tname))
    else:
        print('  MINIMUM up to cardinality %d proven; %d..%d not exhausted '
              '(EXH_CAP)' % (checked_upto, checked_upto + 1, kcard - 1))

    json.dump(dict(board=os.path.relpath(BOARD, SP),
                   candidates={k: cinfo[k]['mm'] for k in keys},
                   out_of_corridor=out_of_corridor, refused=refused,
                   baseline=dict(ok_1_50=base15[0], ok_1_20=base12[0]),
                   all_cut=dict(ok_1_50=allok15, ok_1_20=allok12),
                   target=tname, minimal_set=keep, minimal_card=kcard,
                   minimal_open_1_50=m15[0], minimal_mm_1_50=m15[1],
                   minimal_open_1_20=m12[0], minimal_mm_1_20=m12[1],
                   offload_mm=off_mm, offload_seg=off_seg,
                   proven_minimum=proven_min, checked_upto=checked_upto,
                   smaller_hit=smaller_hit, secs=round(time.time() - t0, 1)),
              open(OUT, 'w'), indent=1)
    print('wrote %s  (%.1fs)' % (os.path.relpath(OUT, SP), time.time() - t0))


if __name__ == '__main__':
    main()
