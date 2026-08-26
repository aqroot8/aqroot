# -*- coding: utf-8 -*-
"""FBV2-P2-002L sections 6-9 -- the BOUNDED U18 placement search.

D-257 lifted the prohibition on moving U18, and it lifted it for a measured
reason.  FBV2-P2-002K left two poses on the table and NEITHER of them works:

  AUTHORITATIVE   U18 8 of 8 with PR-48 and the D-257 vias -- and the
                  BAT_PROTECTED_P Kelvin branch is 13.152 mm against
                  BAT_SENSE's 3.179 mm, a 9.973 mm mismatch, where section 8
                  allows 10 mm each and 5 mm of mismatch.
  002F ECO        Kelvin 4.464 / 4.464 / 0.000, and `U18.7` has NO LEGAL
                  ESCAPE AT ANY APPROVED WIDTH -- blocked by `U18.8` and
                  `U18.6`, its own adjacent pads -- while `U18.10` has no
                  reachable through-via site at any ruled geometry.

So one family can route the pins and cannot measure the shunt, and the other
can measure the shunt and cannot route the pins.  The search is therefore over
the CORRIDOR BETWEEN THEM, and it is the first U18 search run against
PR-39..PR-48 rather than against the routing model of 002F.

METHOD, and it is deliberately small (section 7 caps serious candidates at 12).

  A  RIGID GROUP.  U18 and its own divider / trip ring R76..R83 move together.
     Each family's intra-group geometry was optimised for that family and
     nothing here is trying to re-derive it; the question is what the block's
     relationship to R75, Q2/Q3 and the board edge should be.
  B  courtyard / edge / rule-area legality against everything that stays put
  C  every one of U18's eight signal pins needs a real outward band
  D  KELVIN, analytic: both branches <= 10 mm, mismatch <= 5 mm
  E  the two pins 002K proved are the binding constraint - `U18.7` and
     `U18.10` - must reach a MANUFACTURABLE 0.35/0.20 ordinary through via on
     a bare board.  A pose that cannot do that cannot take D-256's layer, and
     no amount of routing effort will change it.
  F  rank, and hand the survivors to the real local screen

Stage E is the expensive one and it is the one that matters, so it runs last
and only on what survives A-D.
"""
import json
import math
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
if SP not in sys.path:
    sys.path.insert(0, SP)
import place_search_002f as PS
import place_p2_002f as ECO
import path_role_util as RU
import qrouter as QR
import battery_route_plan as PL
import pcbnew

N = PL.N
CP, CT_W, CT_S = 200000, 300000, 200000
GROUP = ['U18', 'R76', 'R77', 'R78', 'R79', 'R80', 'R81', 'R82', 'R83']
U18SIG = ['1', '2', '3', '6', '7', '8', '9', '10']     # 4/5 are GND/NC
BIND = ['7', '10']                                     # 002K's binding pins

KELVIN_MAX = 10.0
KELVIN_MISMATCH = 5.0


def rot_about(px, py, cx, cy, deg):
    a = math.radians(deg)
    dx, dy = px - cx, py - cy
    return (cx + dx * math.cos(a) - dy * math.sin(a),
            cy + dx * math.sin(a) + dy * math.cos(a))


def base_board(work, tag, apply_eco):
    """A scratch board carrying the BASE placement a family is expressed
    against.  This is not a nicety: the 002F ECO also moves TP17, TP19, C57,
    C58, D10..D12, C60 and C61, which are NOT in the group.  A search that
    measured courtyards against the pre-ECO positions of those parts proposed
    C02, and C02 came back from the real screen with THREE courtyard overlaps
    on every single connection.  Each family is judged against the board it
    will actually be routed on."""
    pcb = RU.fresh(work, tag)
    if apply_eco:
        ECO.apply(pcb, report=False)
    return pcb


def seed_of(M, apply_eco):
    pose = {r: M.home[r][:3] for r in GROUP}
    return pose


def centroid(pose):
    return (sum(v[0] for v in pose.values()) / len(pose),
            sum(v[1] for v in pose.values()) / len(pose))


def moved(pose, dx, dy, drot):
    cx, cy = centroid(pose)
    out = {}
    for r, (x, y, rot) in pose.items():
        nx, ny = rot_about(x, y, cx, cy, drot) if drot else (x, y)
        out[r] = (round(nx + dx, 3), round(ny + dy, 3), (rot + drot) % 360.0)
    return out


def legal(M, pose, fixed_r, FPI):
    for r, (x, y, rot) in pose.items():
        c = M.court(r, x, y, rot)
        if (c[0] < M.edge[0] or c[1] < M.edge[1]
                or c[2] > M.edge[2] or c[3] > M.edge[3]):
            return False
        if any(PS.ovl(c, fr) for fr in fixed_r):
            return False
        if any(PS.ovl(c, rr) for rr in M.rule):
            return False
    # the group must not self-overlap after a rotation
    cs = [M.court(r, *pose[r]) for r in pose]
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            if PS.ovl(cs[i], cs[j]):
                return False
    return True


def band_ok(M, ref, x, y, rot, pins, FPI, depth=1.10):
    d = dict(M.padrects_id(ref, x, y, rot))
    for n_ in pins:
        r = d.get(ref + '.' + n_)
        if r is None:
            return False
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        dx, dy = cx - x, cy - y
        if abs(dx) >= abs(dy):
            band = ((r[2] + 0.05, r[1] - 0.05, r[2] + depth, r[3] + 0.05)
                    if dx > 0 else
                    (r[0] - depth, r[1] - 0.05, r[0] - 0.05, r[3] + 0.05))
        else:
            band = ((r[0] - 0.05, r[3] + 0.05, r[2] + 0.05, r[3] + depth)
                    if dy > 0 else
                    (r[0] - 0.05, r[1] - depth, r[2] + 0.05, r[1] - 0.05))
        if (band[0] < M.edge[0] + 0.30 or band[1] < M.edge[1] + 0.30
                or band[2] > M.edge[2] - 0.30 or band[3] > M.edge[3] - 0.30):
            return False
        if any(PS.ovl(band, rr) for (_i, rr) in FPI):
            return False
    return True


def kelvin(M, pose):
    """Both R75 branches, measured pad centre to pad centre."""
    u = pose['U18']
    p9 = M.pad('U18', '9', *u)
    p8 = M.pad('U18', '8', *u)
    r751 = M.pad('R75', '1', *M.home['R75'][:3])
    r752 = M.pad('R75', '2', *M.home['R75'][:3])
    a = math.dist(p9, r751)
    b_ = math.dist(p8, r752)
    return a, b_, abs(a - b_)


def vin_mm(M, pose):
    u = pose['U18']
    return math.dist(M.pad('U18', '1', *u),
                     M.pad('R77', '1', *pose['R77']))


def via_ok(pcb, pose, vias=(PL.D257_VIA_PREFERRED,)):
    """Stage E.  On a BARE board with this pose applied, can U18.7 and U18.10
    each escape at a legal width AND reach a manufacturable through via?"""
    b = pcbnew.LoadBoard(pcb)
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    for r, (x, y, rot) in pose.items():
        f = fp[r]
        f.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6))))
        f.SetOrientationDegrees(rot)
    b.BuildConnectivity()
    b.Save(pcb)
    qb = QR.QBoard(pcb)
    qb.wide_nets = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                             'BAT_MID', 'BAT_SENSE',
                                             'BAT_PROTECTED_P'))
    pads = {}
    for (net, ref), p in qb.pads.items():
        pads.setdefault(ref, p)
    out = {}
    for n_ in BIND:
        ref = 'U18.' + n_
        p = pads.get(ref)
        if p is None:
            return None
        got = None
        for w in (250000, 200000):
            e = qb.escape(p, 'B', w, w, CP, CT_S, 25000,
                          qb.ex0 - 2000000, qb.ey0 - 2000000)
            if e:
                got = (w, e)
                break
        if not got:
            out[ref] = None
            continue
        w, e = got
        site = None
        used = None
        for (vd, vk) in vias:
            for c in e[:6]:
                site = qb.via_site('B', 'F', p['net'], c, w, vd, CP, CT_S,
                                   25000, via_drill=vk)
                if site:
                    used = (vd, vk)
                    break
            if site:
                break
        out[ref] = None if site is None else dict(
            w=w / 1e6, via=[used[0] / 1e6, used[1] / 1e6],
            xy=[round(site[0] / 1e6, 3), round(site[1] / 1e6, 3)],
            out_mm=round(math.hypot(site[0] - p['x'], site[1] - p['y']) / 1e6, 3))
    return out


def courtyard_overlaps(pcb):
    """How many courtyard overlaps KiCad itself reports on this board."""
    import collections
    import json as _j
    import subprocess
    import harness_paths as HP
    out = os.path.join(os.path.dirname(pcb), 'drc_cy.json')
    subprocess.run([HP.kicad_cli(), 'pcb', 'drc', '--severity-all',
                    '--format', 'json', '-o', out, pcb],
                   capture_output=True, text=True)
    j = _j.load(open(out, encoding='utf-8'))
    n = 0
    for k in ('violations',):
        for v in j.get(k, []):
            if v.get('type') == 'courtyards_overlap':
                n += 1
    return n


def main():
    work = os.path.join(SP, 'w')
    span = float(os.environ.get('AQROOT_U18_SPAN', '6.0'))
    step = float(os.environ.get('AQROOT_U18_STEP', '1.0'))
    cands = []
    fams = [('AUTH', False, 'U18BA'), ('ECO', True, 'U18BE')]
    models = {}
    for (fam, use_eco, tag) in fams:
        pcb = base_board(work, tag, use_eco)
        M = PS.Model(pcb)
        models[fam] = (M, pcb,
                       [c for (_, _, c) in M.fixed_courts(GROUP)],
                       M.fixed_pads(GROUP))
    for (fam, use_eco, tag) in fams:
        M, _pcb, fixed_r, FPI = models[fam]
        seed = seed_of(M, use_eco)
        seen = set()
        for drot in (0.0, 90.0, 180.0, 270.0):
            n = int(span / step)
            for i in range(-n, n + 1):
                for j in range(-n, n + 1):
                    dx, dy = i * step, j * step
                    pose = moved(seed, dx, dy, drot)
                    key = tuple(sorted((r, pose[r]) for r in pose))
                    if key in seen:
                        continue
                    seen.add(key)
                    if not legal(M, pose, fixed_r, FPI):
                        continue
                    if not band_ok(M, 'U18', *pose['U18'],
                                   pins=U18SIG, FPI=FPI):
                        continue
                    ka, kb, km = kelvin(M, pose)
                    if max(ka, kb) > KELVIN_MAX or km > KELVIN_MISMATCH:
                        continue
                    cands.append(dict(fam=fam, drot=drot, dx=dx, dy=dy,
                                      pose=pose, kelvin=[round(ka, 3),
                                                         round(kb, 3),
                                                         round(km, 3)],
                                      vin=round(vin_mm(M, pose), 3)))
    print('stage A-D: %d poses legal, all eight pins banded, Kelvin '
          '<= %.0f mm each and <= %.0f mm mismatch'
          % (len(cands), KELVIN_MAX, KELVIN_MISMATCH))
    cands.sort(key=lambda c: (c['kelvin'][2], max(c['kelvin'][:2]), c['vin']))
    # Keep the field diverse: at most three poses from any one (family,
    # rotation) cell, so twelve candidates are not twelve neighbours.
    picked, cell = [], {}
    for c in cands:
        k = (c['fam'], c['drot'])
        if cell.get(k, 0) >= 3:
            continue
        cell[k] = cell.get(k, 0) + 1
        picked.append(c)
        if len(picked) >= 40:
            break

    print('stage E: bare-board escape + manufacturable via site for U18.7 and '
          'U18.10, on the %d best-ranked' % len(picked))
    keep = []
    for c in picked:
        M, _b, _fr, _fp = models[c['fam']]
        probe = base_board(work, 'U18P', c['fam'] == 'ECO')
        # A candidate that overlaps a courtyard is not a candidate.  C02 taught
        # this the expensive way: the geometric filter said legal, the board
        # said `courtyards_overlap: 3`, and every connection in a twelve-minute
        # screen was rejected by the gate for it.
        v = via_ok(probe, c['pose'],
                   vias=(PL.D257_VIA_PREFERRED, PL.D257_VIA_RESERVE))
        cy = courtyard_overlaps(probe)
        c['courtyards_overlap'] = cy
        if cy:
            print('  %-4s rot%+4.0f d(%+.1f,%+.1f)  REJECTED: %d courtyard '
                  'overlap(s) on the real board'
                  % (c['fam'], c['drot'], c['dx'], c['dy'], cy))
            sys.stdout.flush()
            continue
        c['via'] = v
        ok = v is not None and all(v.get('U18.' + n_) for n_ in BIND)
        print('  %-4s rot%+4.0f d(%+.1f,%+.1f)  kelvin %.3f/%.3f (%.3f)  '
              'vin %.3f  U18.7 %-5s U18.10 %-5s'
              % (c['fam'], c['drot'], c['dx'], c['dy'],
                 c['kelvin'][0], c['kelvin'][1], c['kelvin'][2], c['vin'],
                 'ok' if (v or {}).get('U18.7') else 'NO',
                 'ok' if (v or {}).get('U18.10') else 'NO'))
        sys.stdout.flush()
        if ok:
            keep.append(c)
            if len(keep) >= 12:
                break
    print('\nSERIOUS CANDIDATES: %d' % len(keep))
    out = os.path.join(SP, 'u18_candidates_002l.json')
    json.dump(keep, open(out, 'w'), indent=1)
    for k, c in enumerate(keep):
        print('  C%02d %-4s rot%+4.0f d(%+.1f,%+.1f)  U18 %.3f,%.3f/%.0f  '
              'kelvin %.3f/%.3f (%.3f)  vin %.3f'
              % (k, c['fam'], c['drot'], c['dx'], c['dy'],
                 c['pose']['U18'][0], c['pose']['U18'][1], c['pose']['U18'][2],
                 c['kelvin'][0], c['kelvin'][1], c['kelvin'][2], c['vin']))
    print('written: %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
