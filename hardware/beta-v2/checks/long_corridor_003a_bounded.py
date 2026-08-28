# -*- coding: utf-8 -*-
"""FBV2-P2-003A / D-273 -- BOUNDED long-corridor family probe.

Replaces the un-bounded sampled-anchor sweep in ``long_corridor_003a.py`` (whose
first east trial burned >18 min of CPU on a single whole-board wave to a far
anchor, rc130).  Here the measurement is refactored into a SMALL, FIXED set of
geometrically distinct LONG route FAMILIES, each expressed as an explicit
waypoint chain so every obstacle-aware search runs over a SMALL bounded window.

Why families and not sampled anchors (D-273 coverage argument)
--------------------------------------------------------------
The proven c3 board has exactly ONE central free channel (x ~14..48 mm) linking
the western margin to the eastern BAT_PROTECTED_P node copper (cluster 1,
x 38.48..66.40).  The node's only west-reachable copper is its west "tip" vertex
(38.475, 80.325).  Every long B.Cu corridor from R75.2 to the node must (a)
escape the western control-copper mass and (b) cross that one channel.  The
channel is a single connected free region, so the traversal is NOT the
discriminator -- the ESCAPE LATITUDE out of the western mass is.  The western
mass is thinnest at three latitudes (north y~58, mid y~75, south y~83); there is
no fourth macroscopically distinct escape (east is the node, west is the board
edge).  So three R75.2 corridors + one "D9-reservation-first" corridor exhaust
the distinct families.  More sampled anchors would only re-probe the same
channel -- which is precisely the un-bounded trap this replaces.

Boundedness (D-273 requirement 3)
---------------------------------
  * Waypoints are spaced <= ~13 mm, so every hop window is small.
  * ``QR.ASTAR_BUDGET`` / ``QR.WAVE_BUDGET`` are capped to probe sizes, so a
    single unreachable hop cannot explore the whole board.
  * A SIGALRM per-hop wall-clock backstop turns any residual runaway into a
    recorded TIMEOUT failure -- a legitimate result, not a hang.
  * A coarse (0.25 mm) reachability PREFILTER gates each hop; a coarse-blocked
    hop is recorded without ever running the fine search.

Continuity / legality (D-273 requirement 4)
-------------------------------------------
Each hop lays real B.Cu copper at the trunk width (1.50 mm target / 1.20 mm
floor), zero vias, via ``connect_role`` (source escape) then ``join_reserved``
(plain B.Cu runs).  Consecutive hops share exact endpoints, so a successful
chain is one continuous B.Cu polyline.  The final hop targets the exact nearest
node-copper coordinate (``RU.nearest_on_net``) so the corridor physically joins
existing net copper.  The D9 reservation stub (D9.1 -> (10.800,73.000), already
on the board) is the trunk's committed FIRST segment; family F4 starts AT that
reserved end, measuring whether D9's own exit reaches the node the long way.

Every hop lays scratch copper and the whole chain is reverted after each family,
so the board is left byte-identical and every number is a real search result.

    python3 long_corridor_003a_bounded.py [board.kicad_pcb] [out.json]
"""
import os, sys, json, math, time, signal
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import qrouter as QR
import path_role_util as RU
import battery_route_plan as PL

NET = PL.N + 'BAT_PROTECTED_P'
CP, CT = 200000, 300000
W150, W120 = 1500000, 1200000

# ---- explicit search budgets (D-273 req 3) --------------------------------
QR.ASTAR_BUDGET = 60000      # Python A* states per hop (was 500000)
QR.WAVE_BUDGET = 1200        # numpy wavefront steps per hop (was 3000)
HOP_TIMEOUT = 10             # wall-clock seconds; SIGALRM backstop per hop
COARSE_G = 250000            # 0.25 mm prefilter grid


# ---- families: ordered waypoint chains in nm ------------------------------
# First element is either ('pad', ref) -- a real pad that must ESCAPE -- or
# ('pt', (x,y)) -- a committed-copper coordinate (the D9 reservation end).  The
# last element ('join', hint) is resolved to the exact nearest node copper.
def MM(x, y):
    return (int(x * 1e6), int(y * 1e6))


FAMILIES = [
    dict(key='F1_north', src=('pad', 'R75.2'),
         desc='escape north, cross channel high, join node NE diagonal',
         via=[MM(13.0, 60.0), MM(25.0, 58.5), MM(37.0, 62.0), MM(46.0, 71.0)],
         join_hint=MM(46.0, 72.5)),
    dict(key='F2_mid', src=('pad', 'R75.2'),
         desc='escape mid y75, cross channel, join node west tip',
         via=[MM(16.0, 75.0), MM(26.0, 77.0), MM(35.0, 79.5)],
         join_hint=MM(37.0, 80.0)),
    dict(key='F3_south', src=('pad', 'R75.2'),
         desc='escape south y83, cross channel low, join node SE diagonal',
         via=[MM(13.0, 83.0), MM(26.0, 86.0), MM(38.0, 88.0)],
         join_hint=MM(39.0, 86.0)),
    dict(key='F4_resv_first', src=('pt', MM(10.8, 73.0)),
         desc='D9 reservation free end as first segment, exit south to node tip',
         via=[MM(13.0, 80.0), MM(26.0, 80.0), MM(35.0, 80.0)],
         join_hint=MM(37.5, 80.3)),
]


# ---- SIGALRM per-hop wall-clock backstop ----------------------------------
class HopTimeout(Exception):
    pass


def _on_alarm(signum, frame):
    raise HopTimeout()


signal.signal(signal.SIGALRM, _on_alarm)


def timed(fn):
    """Run fn() under a HOP_TIMEOUT wall-clock alarm; TIMEOUT -> failure dict."""
    signal.setitimer(signal.ITIMER_REAL, HOP_TIMEOUT)
    t0 = time.time()
    try:
        r = fn()
    except HopTimeout:
        r = dict(ok=False, reason='TIMEOUT',
                 why='hop exceeded %d s wall clock' % HOP_TIMEOUT)
    except Exception as e:                       # a failed search is a result
        r = dict(ok=False, reason='ERROR', why='%s: %s' % (type(e).__name__, e))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    r['dt'] = round(time.time() - t0, 2)
    return r


# ---- coarse reachability prefilter (staged / hierarchical, D-273 req 2) ----
def coarse_reachable(qb, w, a, b):
    """0.25 mm same-window B.Cu reachability check -- cheap gate before the fine
    search.  Returns (ok, dt)."""
    t0 = time.time()
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    margin = 8000000
    x0 = max(min(a[0], b[0]) - margin, qb.ex0 - 1000000)
    y0 = max(min(a[1], b[1]) - margin, qb.ey0 - 1000000)
    x1 = min(max(a[0], b[0]) + margin, qb.ex1 + 1000000)
    y1 = min(max(a[1], b[1]) + margin, qb.ey1 + 1000000)
    G = COARSE_G
    ox2 = int(round((x0 - ox) / G)) * G + ox
    oy2 = int(round((y0 - oy) / G)) * G + oy
    blk = qb.grid('B', NET, w, CP, CT, ox2, oy2, x1, y1, G)
    ny, nx = blk.shape
    si = (int((a[0] - ox2) // G), int((a[1] - oy2) // G))
    ti = (int((b[0] - ox2) // G), int((b[1] - oy2) // G))
    for (ii, jj) in (si, ti):
        if 0 <= ii < nx and 0 <= jj < ny:
            blk[jj, ii] = False
    ok = qb.search(blk, si, ti) is not None
    return ok, round(time.time() - t0, 2)


def run_family(qb, fam, w):
    """Lay the whole chain at width w; measure; revert.  Bounded per hop."""
    # resolve the exact node-copper join coordinate
    hint = fam['join_hint']
    best = RU.nearest_on_net(qb.b, NET, 'B.Cu', hint[0], hint[1])
    join = (best[1], best[2]) if best else hint
    # build the ordered point list; source may be a pad (escape) or a point
    src_kind, src_val = fam['src']
    pts = list(fam['via']) + [join]
    hops = []
    total = 0.0
    m = qb.mark()
    ok = True

    # hop 0.  A PAD source ESCAPES first (bounded geometric search, no wave), and
    # the pad->escape stub is laid; the corridor is then chained from the escape
    # LANDING point.  This separates "can the pad leave B.Cu at width w?" from
    # "does a corridor exist?", and keeps every windowed search a plain hop.
    if src_kind == 'pad':
        src = qb.pads[(NET, src_val)]
        ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
        pref = (pts[0][0] - src['x'], pts[0][1] - src['y'])
        t0 = time.time()
        try:                                       # escape is bounded (no wave)
            e = qb.escape(src, 'B', w, w, CP, CT, 50000, ox, oy, prefer=pref)
        except Exception as ex:
            e, qb.escape_why = [], ['%s: %s' % (type(ex).__name__, ex)]
        edt = round(time.time() - t0, 2)
        if not e:
            hops.append(dict(hop='esc %s' % src_val, ok=False,
                             reason='NO_LEGAL_ESCAPE',
                             why=(qb.escape_why[0] if qb.escape_why else None),
                             dt=edt))
            ok = False
            prev = None
        else:
            c = e[0]
            qb.track(NET, 'B', src['x'], src['y'], c['x'], c['y'], c['w'])
            hops.append(dict(hop='esc %s' % src_val, ok=True,
                             mm=round(c['ln'] / 1e6, 3),
                             end=[int(c['x']), int(c['y'])], dt=edt))
            total += c['ln'] / 1e6
            prev = (int(c['x']), int(c['y']))
        rest = pts                                # chain from the escape landing
    else:
        prev = src_val                            # the D9 reservation free end
        rest = pts

    # interior + final hops: plain B.Cu runs, zero via, bounded window
    if ok:
        for k, nxt in enumerate(rest):
            cok, cdt = coarse_reachable(qb, w, prev, nxt)
            label = 'run p%d->%s' % (k, 'join' if nxt is join else 'w%d' % k)
            if not cok:
                hops.append(dict(hop=label, ok=False, reason='COARSE_BLOCKED',
                                 coarse_dt=cdt))
                ok = False
                break
            r = timed(lambda a=prev, b=nxt:
                      QR.join_reserved(qb, NET, a, b, w, CP, CT, layer='B'))
            r['hop'] = label
            r['coarse_dt'] = cdt
            hops.append(r)
            total += r.get('mm', 0) or 0
            if not r.get('ok'):
                ok = False
                break
            prev = nxt

    qb.revert(m)
    return dict(key=fam['key'], desc=fam['desc'], width_mm=w / 1e6,
                join=[join[0], join[1]], join_mm=[round(join[0] / 1e6, 3),
                round(join[1] / 1e6, 3)], ok=ok, total_mm=round(total, 3),
                hops=hops)


def control(qb):
    """Regression: the SHORT direct R75.2->D9.1 hop, expected to fail at 1.5/1.2
    (D-272).  Bounded connect_role, small window."""
    out = {}
    src = qb.pads[(NET, 'R75.2')]
    d9 = qb.pads[(NET, 'D9.1')]
    anchor = RU.pseudo_pad(NET, d9['x'], d9['y'], QR)
    anchor['anchor'] = True
    anchor['ref'] = '(D9.1)'
    for w in (W150, W120):
        m = qb.mark()
        r = timed(lambda: QR.connect_role(qb, NET, src, anchor, 'B', w, CP, CT))
        qb.revert(m)
        out['%.2f' % (w / 1e6)] = dict(ok=bool(r.get('ok')),
                                       reason=r.get('reason'),
                                       mm=round(r.get('mm', 0) or 0, 3),
                                       dt=r['dt'])
    return out


def main():
    board = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        SP, 'w', 'c3repro003a_parent', 'aqroot-Beta-v2.kicad_pcb')
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        SP, 'place_002z', 'long_corridor_003a_bounded.json')
    qb = QR.QBoard(board)
    qb.wide_nets = frozenset(PL.N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                             'BAT_MID', 'BAT_SENSE', 'BAT_PROTECTED_P'))
    src = qb.pads[(NET, 'R75.2')]
    print('board  %s' % board)
    print('R75.2  (%.3f, %.3f)   budgets ASTAR=%d WAVE=%d  hop_timeout=%ds'
          % (src['x'] / 1e6, src['y'] / 1e6, QR.ASTAR_BUDGET, QR.WAVE_BUDGET,
             HOP_TIMEOUT))

    rec = dict(board=board, astar_budget=QR.ASTAR_BUDGET,
               wave_budget=QR.WAVE_BUDGET, hop_timeout_s=HOP_TIMEOUT,
               control={}, families=[])

    print('-- CONTROL  R75.2 -> D9.1 (short, expect FAIL) --')
    rec['control'] = control(qb)
    for k, v in rec['control'].items():
        print('   @%s  ok=%s  %s  %.2fs' % (k, v['ok'], v['reason'], v['dt']))

    print('-- LONG families (bounded) --')
    for fam in FAMILIES:
        for w in (W150, W120):
            r = run_family(qb, fam, w)
            rec['families'].append(r)
            tag = 'OK %.3fmm' % r['total_mm'] if r['ok'] else 'FAIL'
            last = r['hops'][-1] if r['hops'] else {}
            print('   %-14s @%.2f  %-12s join(%.2f,%.2f)  last=%s %s'
                  % (r['key'], w / 1e6, tag, r['join_mm'][0], r['join_mm'][1],
                     last.get('reason', 'ok'),
                     'dt=%.1fs' % sum(h.get('dt', 0) for h in r['hops'])))

    json.dump(rec, open(out, 'w'), indent=1)
    okfams = sorted(set(r['key'] for r in rec['families'] if r['ok']))
    print('=' * 72)
    print('bounded families with a legal B.Cu long corridor: %s'
          % (okfams if okfams else 'NONE'))
    print('wrote %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
