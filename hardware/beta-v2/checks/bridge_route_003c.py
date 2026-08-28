# -*- coding: utf-8 -*-
"""FBV2-P2-003C / D-275 -- the REAL western-corridor vacate ECO + F.Cu high-
current via-array bridge for BAT_PROTECTED_P, on the reproduced c3 board.

The fcu_cutset_003c prefilter proved the MINIMUM vacate set is cardinality 1:
moving the single low-current control branch BAT_PROT_SHDN_CTL off F.Cu opens a
>= 1.50 mm F.Cu corridor from R75.2 to the eastern BPP node (NOT the D9 stub, so
the D-274 single-via D9->node link never carries pack current).  This script lays
the real copper and leaves a board for the DRC / connectivity gates:

  VACATE  the 6 F.Cu tracks of BAT_PROT_SHDN_CTL (0.15 mm SIG, a microamp SHDN
          control signal) are moved to In3.Cu.  Its two end transitions are
          already THROUGH vias (F<->B, so In3 is on the barrel), so continuity
          Q4.1 -B- via -In3- via -B- R83.1 is preserved and F.Cu is vacated.
          In3 is clear in the window (In1/In4 are the GND planes, kept intact;
          In2 already carries the Kelvin/Q3_CS inner copper).  A control net was
          never barred from the inner layers, so this needs NO netclass rule.

  BRIDGE  ENTRY  4x 0.80/0.40 through vias on R75.2's B.Cu pad (POFV, D-258),
                 fault-tolerant floor 3 (D-274 sizing).
          TRAVERSE >= 1.50 mm F.Cu from the entry array to the node landing.
          EXIT   4x 0.80/0.40 through vias landing on the node, each tied to the
                 node's 1.20 mm B.Cu copper -- an ARRAY landing, no single via
                 carries pack current.

Usage:
  python bridge_route_003c.py vacate     # stage 1: vacate + re-measure corridor
  python bridge_route_003c.py bridge      # stage 2: lay the full bridge
"""
import os, sys, math, shutil, json
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import pcbnew
import qrouter as QR
import path_role_util as RU
import battery_route_plan as PL

N = PL.N
NET = N + 'BAT_PROTECTED_P'
SHDN = N + 'BAT_PROT_SHDN_CTL'
CP, CTW = 200000, 300000
DIA, DRILL = 800000, 400000
W_TRAVERSE = 1500000            # >= 1.20 floor, 1.50 target (achieved)
W_LAND = 1200000               # node B.Cu stub, full trunk floor
PCBNAME = 'aqroot-Beta-v2.kicad_pcb'

SRC = os.path.join(SP, 'w', 'c3repro003c')
DST = os.path.join(SP, 'w', 'c3bridge003c')

# entry via sites on R75.2's pad (bridge_feasibility_003b, all vfree)
ENTRY_SITES = [(2.2e6, 67.8e6), (3.1e6, 67.8e6),
               (2.2e6, 68.7e6), (3.1e6, 68.7e6)]
ENTRY_CENTROID = (2.65e6, 68.25e6)
# node landing: the node's own 1.20 mm B.Cu copper (nearest_on_net)
NODE_AIM = (42.4e6, 76.4e6)


def fresh_copy():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    return os.path.join(DST, PCBNAME)


def vacate(pcb):
    """Move BAT_PROT_SHDN_CTL's F.Cu tracks to In3.Cu.  Returns count moved."""
    b = pcbnew.LoadBoard(pcb)
    moved = 0
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_TRACK':
            continue
        if t.GetNetname() == SHDN and t.GetLayer() == pcbnew.F_Cu:
            t.SetLayer(pcbnew.In3_Cu)
            moved += 1
    b.Save(pcb)
    return moved


def stage_vacate():
    pcb = fresh_copy()
    moved = vacate(pcb)
    print('VACATE: moved %d BAT_PROT_SHDN_CTL F.Cu tracks -> In3.Cu' % moved)
    # re-measure the F.Cu corridor on the ACTUAL vacated board
    qb = QR.QBoard(pcb)
    qb.wide_nets = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                             'BAT_MID', 'BAT_SENSE',
                                             'BAT_PROTECTED_P'))
    r = qb.pads[(NET, 'R75.2')]
    ax = QR
    import fcu_cutset_003c as CS
    sx, sy = r['x'], r['y']
    res = {}
    for w, lab in ((1500000, '1.50'), (1200000, '1.20')):
        rr, dt = CS.astar(qb, sx, sy, NODE_AIM[0], NODE_AIM[1], w)
        fe = CS.flood_east(qb, sx, sy, w)
        res[lab] = dict(astar_to_node=rr, flood_east_mm=fe, secs=dt)
        print('  %s mm: A* R75.2->node(%.1f,%.1f) = %s (%.2fs); flood east %s mm'
              % (lab, NODE_AIM[0] / 1e6, NODE_AIM[1] / 1e6, rr, dt, fe))
    json.dump(dict(moved=moved, board=os.path.relpath(pcb, SP), corridor=res),
              open(os.path.join(SP, 'place_002z', 'vacate_003c.json'), 'w'),
              indent=1)
    ok = res['1.50']['astar_to_node'] == 'PATH'
    print('VACATE corridor opens at 1.50 mm:', ok)
    return ok


def inject_vias(qb):
    """QBoard skips PCB_VIA, so a through via's copper/hole is invisible to the
    router.  For a HIGH-CURRENT bridge that is not acceptable: the traverse must
    clear existing vias too.  Add every board via as all-layer copper + a hole."""
    n = 0
    for t in qb.b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            x, y = t.GetPosition().x, t.GetPosition().y
            dia, drill, net = t.GetWidth(), t.GetDrill(), t.GetNetname()
            # inject as a zero-length SEG (not RR) so margin() applies the
            # 0.30 mm TRACK clearance the D-269 rule demands between the trunk
            # and a via -- an RR would be treated as a pad and get only 0.20.
            for L in qb.cu:
                qb.shapes[L].append(QR.SEG(x, y, x, y, dia / 2.0, net, 'via'))
            qb.holes.append(QR.RR(x, y, drill / 2.0, drill / 2.0,
                                  drill / 2.0, 0, net, 'via/hole'))
            n += 1
    qb._obs_cache = None
    return n


VIA_R = DIA / 2.0            # 0.40 mm barrel radius
HH_MIN = 249500             # KiCad hole_to_hole floor 0.2495 mm (edge to edge)
PITCH = 700000             # 0.70 mm array pitch (comfortably over the hole floor)


def hole_clear(qb, x, y):
    """No hole_to_hole with any existing drill: edge gap >= 0.2495 mm."""
    return not any(math.hypot(h.cx - x, h.cy - y) < h.r + DRILL / 2.0 + HH_MIN
                   for h in qb.holes)


def scan_entry_sites(qb):
    """Via sites on R75.2's own B.Cu pad, clear on every layer and hole-legal,
    packed to 4 at 0.70 mm pitch.  Preferring the south (away from the existing
    U18.8 sense via at the pad's north end)."""
    r = qb.pads[(NET, 'R75.2')]
    px, py, hx, hy = r['x'], r['y'], r['hx'], r['hy']
    ok = []
    g = 25000
    y = py - hy - 100000
    while y <= py + hy + 100000:
        x = px - hx - 100000
        while x <= px + hx + 100000:
            if (all(qb.point_free(L, NET, x, y, DIA, CP, CTW, 25000)
                    for L in qb.cu) and hole_clear(qb, x, y)):
                ok.append((int(x), int(y)))
            x += g
        y += g
    ok.sort(key=lambda c: (c[1], c[0]))       # south-first
    arr = []
    for c in ok:
        if all(math.hypot(c[0] - e[0], c[1] - e[1]) >= PITCH for e in arr):
            arr.append(c)
        if len(arr) >= 4:
            break
    return arr


def anchor(ref, x, y):
    return dict(ref=ref, x=int(x), y=int(y), anchor=True, net=NET)


def route_traverse(qb, sx, sy, tx, ty, width):
    """Bounded F.Cu search (same shape as fcu_cutset astar), then EMIT the
    simplified polyline as real F.Cu tracks.  Returns (ok, mm, npts)."""
    G = 50000
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    x0 = max(min(sx, tx) - 9e6, qb.ex0 - 1e6)
    y0 = max(min(sy, ty) - 9e6, qb.ey0 - 1e6)
    x1 = min(max(sx, tx) + 9e6, qb.ex1 + 1e6)
    y1 = min(max(sy, ty) + 9e6, qb.ey1 + 1e6)
    ox2 = int(round((x0 - ox) / G)) * G + ox
    oy2 = int(round((y0 - oy) / G)) * G + oy
    blk = qb.grid('F', NET, width, CP, CTW, ox2, oy2, x1, y1, G)
    si = (int((sx - ox2) // G), int((sy - oy2) // G))
    ti = (int((tx - ox2) // G), int((ty - oy2) // G))
    ny, nx = blk.shape
    for ii, jj in (si, ti):
        if 0 <= ii < nx and 0 <= jj < ny:
            blk[jj, ii] = False
    path = qb.search(blk, si, ti)
    if not path:
        return False, 0.0, 0
    pts = QR.simplify(path, ox2, oy2, G)
    # stitch anchors exactly to the entry/exit points
    pts = [(int(sx), int(sy))] + [(int(a), int(b)) for a, b in pts] + \
          [(int(tx), int(ty))]
    total = 0.0
    for k in range(len(pts) - 1):
        (a, b), (c, d) = pts[k], pts[k + 1]
        if (a, b) != (c, d):
            qb.track(NET, 'F', a, b, c, d, width)
            total += math.hypot(c - a, d - b)
    return True, total / 1e6, len(pts)


def stage_bridge():
    pcb = fresh_copy()
    moved = vacate(pcb)
    print('VACATE: moved %d BAT_PROT_SHDN_CTL F.Cu tracks -> In3.Cu' % moved)
    qb = QR.QBoard(pcb)
    qb.wide_nets = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                             'BAT_MID', 'BAT_SENSE',
                                             'BAT_PROTECTED_P'))
    nvia = inject_vias(qb)
    print('  modelled %d existing vias as obstacles' % nvia)
    rec = dict(moved=moved, board=os.path.relpath(pcb, SP), existing_vias=nvia)

    # ---- ENTRY ARRAY on R75.2 (no B.Cu ties: vias sit on the pad copper) --
    entry_vias = scan_entry_sites(qb)
    if len(entry_vias) < 3:
        print('  ENTRY: only %d clear sites on R75.2 -- abort' % len(entry_vias))
        return False
    for (x, y) in entry_vias:
        qb.via(NET, x, y, DIA, DRILL)
    ex = sorted(x for x, y in entry_vias)
    ey0 = sum(y for x, y in entry_vias) / len(entry_vias)
    # a 1.50 mm F.Cu bus across the array unites the 4 via tops into the trunk
    qb.track(NET, 'F', ex[0], int(ey0), ex[-1], int(ey0), W_TRAVERSE)
    entry_bus = (ex[-1], int(ey0))
    rec['entry_vias'] = [[round(x/1e6, 3), round(y/1e6, 3)] for x, y in entry_vias]
    print('  ENTRY: %d vias on R75.2 pad + 1.50 mm F.Cu bus (no B.Cu ties)'
          % len(entry_vias))

    # ---- F.Cu TRAVERSE from the entry bus to the node landing ----------
    nb = RU.nearest_on_net(qb.b, NET, 'B.Cu', NODE_AIM[0], NODE_AIM[1])
    if nb is None:
        print('  no node B.Cu copper found near aim -- abort'); return False
    nd, npx, npy, ntrack = nb
    print('  node landing on B.Cu copper (%.3f,%.3f) w=%.2f'
          % (npx/1e6, npy/1e6, ntrack.GetWidth()/1e6))
    exit_centroid = (npx, npy - 900000)     # F.Cu drop point just N of node copper
    # width ladder: 1.50 target down to the 1.20 mandatory floor, widest first
    wtrav = None
    for w in (1500000, 1400000, 1300000, 1200000):
        ok, mm, npts = route_traverse(qb, entry_bus[0], entry_bus[1],
                                      exit_centroid[0], exit_centroid[1], w)
        if ok:
            wtrav = w
            break
    if wtrav is None:
        print('  TRAVERSE FAILED (no >= 1.20 mm F.Cu corridor)')
        rec['traverse'] = dict(ok=False)
        json.dump(rec, open(os.path.join(SP, 'place_002z',
                                         'bridge_003c.json'), 'w'), indent=1)
        return False
    print('  TRAVERSE: %.3f mm F.Cu at %.2f mm, %d pts'
          % (mm, wtrav/1e6, npts))
    rec['traverse'] = dict(ok=True, mm=round(mm, 3), w_mm=wtrav/1e6, pts=npts)

    # ---- EXIT ARRAY: 4 vias around the drop, tied to node B.Cu ----------
    # sites in the open node region; F.Cu bus at 1.50, B.Cu stubs at 1.20
    exit_sites = [(npx-450000, npy-1350000), (npx+450000, npy-1350000),
                  (npx-450000, npy-450000), (npx+450000, npy-450000)]
    laid = 0
    laid_pts = []
    for (x, y) in exit_sites:
        free = all(qb.point_free(L, NET, x, y, DIA, CP, CTW, 25000)
                   for L in qb.cu)
        if not free or not hole_clear(qb, x, y):
            print('    exit via (%.2f,%.2f) not free/hole-clear, skip'
                  % (x/1e6, y/1e6))
            continue
        qb.via(NET, x, y, DIA, DRILL)
        # F.Cu tie from the traverse-end centroid to the via (>= trunk floor)
        qb.track(NET, 'F', exit_centroid[0], exit_centroid[1], x, y, W_LAND)
        # B.Cu stub from the via to the node copper junction (>= trunk floor)
        qb.track(NET, 'B', x, y, npx, npy, W_LAND)
        laid += 1
        laid_pts.append((x, y))
    print('  EXIT: %d vias landed on node' % laid)
    rec['exit_vias'] = laid
    if laid < 3:
        print('  EXIT array below fault-tolerant floor 3 -- abort');
        json.dump(rec, open(os.path.join(SP, 'place_002z',
                                         'bridge_003c.json'), 'w'), indent=1)
        return False
    # make the node track a real junction at the landing point
    RU.split_at(qb.b, ntrack, npx, npy)

    # ---- fill zones + save ----------------------------------------------
    pcbnew.ZONE_FILLER(qb.b).Fill(qb.b.Zones())
    qb.save()
    json.dump(rec, open(os.path.join(SP, 'place_002z',
                                     'bridge_003c.json'), 'w'), indent=1)
    print('BRIDGE laid, saved %s' % os.path.relpath(pcb, SP))
    return True


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else 'vacate'
    if stage == 'vacate':
        return 0 if stage_vacate() else 1
    if stage == 'bridge':
        return 0 if stage_bridge() else 1
    print('usage: bridge_route_003c.py [vacate|bridge]')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
