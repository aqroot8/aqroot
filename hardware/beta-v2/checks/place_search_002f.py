# -*- coding: utf-8 -*-
"""FBV2-P2-002F section 11 -- the BOUNDED PLACEMENT SEARCH.

Section 3 is explicit: "Do not choose placement by visual judgement.  Measure
candidate placements."  So nothing here is hand-picked.  The script enumerates
U18 poses, solves the divider/passive ring around each one, and scores every
survivor against the eleven section 11 criteria.  The winner is whatever the
table says, and the table is written into the audit.

STAGE 1  U18 pose  -- rotation x translation on a 0.25 mm grid, rejected on
         courtyard collision, board edge, battery-shadow height and the
         section 4 Kelvin envelope.  Cheap, analytic, thousands of candidates.
STAGE 2  the ring  -- R76..R83 are assigned to free slots by the pin each one
         serves, subject to collision and to a reserved BAT_PROTECTED_P trunk
         corridor.  A resistor that serves a U18 pin is placed BY that pin.
STAGE 3  the proof -- the survivors are written to real scratch boards and
         measured with the qrouter obstacle model: per-pad legal escape, then
         all eight escapes laid SIMULTANEOUSLY (section 3C), then a free-region
         flood for reachability, because an escape cell is not reachability.
"""
import os, sys, math, json, time, itertools, faulthandler
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import path_role_util as RU
import qrouter as QR
import pcbnew

N = '/01_POWER_TREE/'
CP, CT_W, CT_S = 200000, 300000, 200000
WORK = os.path.join(SP, 'w')
BOARD_H = 148.0
BATTERY = (7.0, 49.5, 64.0, 124.5)          # pcb coords, doc (7,23.5,64,98.5)

# ---------------------------------------------------------------- packages
# max body height, mm, from the package standard.  Used for the battery-shadow
# check: nothing this ECO moves may set a NEW maximum inside the shadow.
HEIGHT = {'MSOP-10': 1.10, 'R_0603': 0.60, 'C_0603': 0.95, 'R_1206': 0.75,
          'D_SOD-323': 1.00, 'D_SOD-123': 1.10, 'TestPoint': 0.00,
          'SOIC-8': 1.75, 'SOT-23': 1.45, 'R_2512': 0.65, 'Fuse_1206': 0.90}


def pkg_h(fpid):
    for k, v in HEIGHT.items():
        if k in fpid:
            return v
    return 1.10


# ---------------------------------------------------------------- the model
class Model(object):
    """One in-memory board, moved repeatedly.  Courtyards come from pcbnew so
    a rotated footprint is exact rather than assumed."""

    def __init__(self, pcb):
        self.pcb = pcb
        self.b = pcbnew.LoadBoard(pcb)
        self.fp = {f.GetReference(): f for f in self.b.GetFootprints()}
        self.home = {r: (f.GetPosition().x / 1e6, f.GetPosition().y / 1e6,
                         f.GetOrientationDegrees())
                     for r, f in self.fp.items()}
        self.fpid = {r: f.GetFPIDAsString() for r, f in self.fp.items()}
        bb = self.b.GetBoardEdgesBoundingBox()
        self.edge = (bb.GetLeft() / 1e6 + 0.05, bb.GetTop() / 1e6 + 0.05,
                     bb.GetRight() / 1e6 - 0.05, bb.GetBottom() / 1e6 - 0.05)
        self.rule = []
        for z in self.b.Zones():
            if z.GetIsRuleArea():
                zb = z.GetBoundingBox()
                self.rule.append((zb.GetLeft() / 1e6, zb.GetTop() / 1e6,
                                  zb.GetRight() / 1e6, zb.GetBottom() / 1e6))
        self._loc = {}

    def local(self, ref, rot):
        """Courtyard half-extents and pad offsets for this ref at this rotation,
        measured once by actually rotating the footprint."""
        key = (ref, rot)
        if key in self._loc:
            return self._loc[key]
        f = self.fp[ref]
        px, py, pr = self.home[ref]
        f.SetOrientationDegrees(rot)
        f.SetPosition(pcbnew.VECTOR2I(0, 0))
        cy = f.GetCourtyard(f.GetLayer())
        bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox()
        rect = (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                bb.GetRight() / 1e6, bb.GetBottom() / 1e6)
        pads = {}
        for p in f.Pads():
            pads[p.GetNumber()] = (p.GetPosition().x / 1e6, p.GetPosition().y / 1e6)
        f.SetOrientationDegrees(pr)
        f.SetPosition(pcbnew.VECTOR2I(int(px * 1e6), int(py * 1e6)))
        self._loc[key] = (rect, pads)
        return self._loc[key]

    def court(self, ref, x, y, rot):
        r = self.local(ref, rot)[0]
        return (x + r[0], y + r[1], x + r[2], y + r[3])

    def pad(self, ref, num, x, y, rot):
        o = self.local(ref, rot)[1][num]
        return (x + o[0], y + o[1])

    def local_padrects(self, ref, rot):
        """Pad bounding boxes relative to the footprint origin.  COPPER, not
        courtyard: a track may run under a component body, and only pads and
        other copper stop it.  Scoring on courtyards rejects the whole east
        side of R75 for no physical reason."""
        key = ('PR', ref, rot)
        if key in self._loc:
            return self._loc[key]
        f = self.fp[ref]
        px, py, pr = self.home[ref]
        f.SetOrientationDegrees(rot)
        f.SetPosition(pcbnew.VECTOR2I(0, 0))
        out = []
        for p in f.Pads():
            bb = p.GetBoundingBox()
            out.append((bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                        bb.GetRight() / 1e6, bb.GetBottom() / 1e6))
        f.SetOrientationDegrees(pr)
        f.SetPosition(pcbnew.VECTOR2I(int(px * 1e6), int(py * 1e6)))
        self._loc[key] = out
        return out

    def padrects(self, ref, x, y, rot):
        return [(x + r[0], y + r[1], x + r[2], y + r[3])
                for r in self.local_padrects(ref, rot)]

    def fixed_pads(self, movable, skip=()):
        """[(id, rect)] for every pad NOT on a movable footprint.  The id lets a
        branch exclude the two pads it actually terminates on, and NOTHING
        else: a BAT_PROTECTED_P branch may end on R75.2 but must still treat
        R75.1 - a different net, 5.9 mm away on the same part - as copper."""
        out = []
        for r, f in self.fp.items():
            if r in movable or r in skip:
                continue
            for p in f.Pads():
                bb = p.GetBoundingBox()
                out.append((r + '.' + p.GetNumber(),
                            (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                             bb.GetRight() / 1e6, bb.GetBottom() / 1e6)))
        return out

    def local_padids(self, ref, rot):
        key = ('PI', ref, rot)
        if key in self._loc:
            return self._loc[key]
        f = self.fp[ref]
        self._loc[key] = [ref + '.' + p.GetNumber() for p in f.Pads()]
        return self._loc[key]

    def padrects_id(self, ref, x, y, rot):
        return list(zip(self.local_padids(ref, rot),
                        self.padrects(ref, x, y, rot)))

    def fixed_courts(self, movable):
        out = []
        for r, f in self.fp.items():
            if r in movable:
                continue
            cy = f.GetCourtyard(f.GetLayer())
            bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox()
            out.append((r, f.IsFlipped(),
                        (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                         bb.GetRight() / 1e6, bb.GetBottom() / 1e6)))
        return out

    def write(self, path, pose):
        b = pcbnew.LoadBoard(self.pcb)
        for f in b.GetFootprints():
            r = f.GetReference()
            if r in pose:
                x, y, rot = pose[r]
                f.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6))))
                f.SetOrientationDegrees(rot)
        b.BuildConnectivity()
        b.Save(path)
        return b


def ovl(a, c, gap=0.0):
    return not (a[2] + gap < c[0] or c[2] + gap < a[0] or
                a[3] + gap < c[1] or c[3] + gap < a[1])


def seg_rect(x0, y0, x1, y1, r, pad=0.0):
    """Does the segment touch the rect (expanded by pad)?"""
    R = (r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad)
    if max(x0, x1) < R[0] or min(x0, x1) > R[2]:
        return False
    if max(y0, y1) < R[1] or min(y0, y1) > R[3]:
        return False
    # separating axis on the segment normal
    dx, dy = x1 - x0, y1 - y0
    if dx == 0 and dy == 0:
        return R[0] <= x0 <= R[2] and R[1] <= y0 <= R[3]
    nx, ny = -dy, dx
    d = nx * x0 + ny * y0
    cs = [nx * R[0] + ny * R[1], nx * R[2] + ny * R[1],
          nx * R[0] + ny * R[3], nx * R[2] + ny * R[3]]
    return not (min(cs) > d or max(cs) < d)


# ------------------------------------------------------------- path metric
class PathGrid(object):
    """Courtyard-level shortest path, so a length is what a track would have to
    walk and not what a ruler says.  R75 physically separates U18.8 from its
    Kelvin target; a Euclidean score cannot see that and would rank the
    placement that produced FBV2-P2-002E's 20.6 mm mismatch as excellent."""

    def __init__(self, x0, y0, x1, y1, g=0.25):
        import numpy as np
        self.np = np
        self.g, self.x0, self.y0 = g, x0, y0
        self.nx = int((x1 - x0) / g) + 1
        self.ny = int((y1 - y0) / g) + 1

    @staticmethod
    def drop(pairs, exclude):
        return [r for (i, r) in pairs if i not in exclude]

    def build(self, rects, infl):
        np = self.np
        blk = np.zeros((self.ny, self.nx), dtype=bool)
        X = self.x0 + np.arange(self.nx) * self.g
        Y = self.y0 + np.arange(self.ny) * self.g
        XX, YY = np.meshgrid(X, Y)
        for r in rects:
            blk |= ((XX >= r[0] - infl) & (XX <= r[2] + infl) &
                    (YY >= r[1] - infl) & (YY <= r[3] + infl))
        return blk

    def path(self, blk, a, b, want_pts=False):
        """8-connected Dijkstra length in mm, or None."""
        import heapq
        np = self.np
        g = self.g
        si = (int(round((a[0] - self.x0) / g)), int(round((a[1] - self.y0) / g)))
        ti = (int(round((b[0] - self.x0) / g)), int(round((b[1] - self.y0) / g)))
        for p in (si, ti):
            if not (0 <= p[0] < self.nx and 0 <= p[1] < self.ny):
                return None
        free = ~blk
        free[si[1], si[0]] = True
        free[ti[1], ti[0]] = True
        INF = float('inf')
        dist = np.full((self.ny, self.nx), INF)
        dist[si[1], si[0]] = 0.0
        prev = {}
        pq = [(0.0, si[0], si[1])]
        D = 1.4142135623
        while pq:
            d, i, j = heapq.heappop(pq)
            if d > dist[j, i]:
                continue
            if (i, j) == ti:
                if not want_pts:
                    return d * g
                pts, cur = [], (i, j)
                while cur in prev:
                    pts.append((self.x0 + cur[0] * g, self.y0 + cur[1] * g))
                    cur = prev[cur]
                pts.append((self.x0 + si[0] * g, self.y0 + si[1] * g))
                pts.reverse()
                return d * g, pts
            for di, dj, w in ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                              (1, 1, D), (1, -1, D), (-1, 1, D), (-1, -1, D)):
                ii, jj = i + di, j + dj
                if not (0 <= ii < self.nx and 0 <= jj < self.ny):
                    continue
                if not free[jj, ii]:
                    continue
                nd = d + w
                if nd < dist[jj, ii]:
                    dist[jj, ii] = nd
                    prev[(ii, jj)] = (i, j)
                    heapq.heappush(pq, (nd, ii, jj))
        return None


# ------------------------------------------------------------ the ring spec
# Every divider / gate passive, the U18 pin it SERVES and the node it chains to.
# A resistor that serves a U18 pin is placed by that pin; that is what turns the
# wall from an obstacle into a service ring.
RING = [
    # ref   servicing pad -> U18 pin        chain pad -> target
    ('R76', '1', 'U18.10', '2', 'C57.1'),
    ('R77', '1', 'U18.1',  '2', 'U18.3'),
    ('R79', '2', 'U18.2',  '1', 'R77.1'),
    ('R80', '2', 'U18.6',  '1', 'R79.1'),
    ('R81', '2', 'U18.7',  '1', None),
    ('R78', '1', 'R77.2',  '2', None),
    ('R82', '1', 'R81.2',  '2', None),
    ('R83', '1', 'TP19.1', '2', None),
]
U18PINS = {'1': 'BAT_RAW', '2': 'LTC_UV', '3': 'LTC_OV', '6': 'LTC_SHDN',
           '7': 'LTC4368_FAULT_N', '8': 'BAT_PROTECTED_P', '9': 'BAT_SENSE',
           '10': 'LTC_GATE'}
# the rule minimum each U18 pad must be able to emit, from battery_route_plan
U18MIN = {'1': 200000, '2': 150000, '3': 150000, '6': 150000, '7': 150000,
          '8': 200000, '9': 200000, '10': 150000}
MOVABLE = ['U18', 'R76', 'R77', 'R78', 'R79', 'R80', 'R81', 'R82', 'R83',
           'C57', 'TP17', 'TP19', 'C58']


# ------------------------------------------------------------------ stage 1
SENSE_INFL = 0.20 + 0.10        # 0.20 mm branch, 0.20 mm clearance, half each
TRUNK_INFL = 0.20 + 0.75        # 1.50 mm trunk


def stage1(M, verbose=True):
    """U18 rotation x translation.

    Rejected on courtyard collision (a PLACEMENT rule), board edge, rule areas
    and the section 4 Kelvin envelope; then SCORED on COPPER-level path length,
    because what produced FBV2-P2-002E's 20.6 mm Kelvin mismatch is R75's own
    pads standing between U18.8 and R75.2, and a ruler cannot see that.
    """
    fixed = M.fixed_courts(MOVABLE)
    fixed_r = [c for (_, _, c) in fixed]
    r75_1 = M.pad('R75', '1', *M.home['R75'])
    r75_2 = M.pad('R75', '2', *M.home['R75'])
    d9_1 = M.pad('D9', '1', *M.home['D9'])
    shadow_max = max([pkg_h(M.fpid[r]) for (r, _, c) in fixed
                      if ovl(c, BATTERY)] or [1.10])
    PG = PathGrid(0.0, 52.0, 26.0, 84.0, 0.25)
    FP = M.fixed_pads(MOVABLE)

    b_k8 = PG.build(PG.drop(FP, {'R75.2'}), SENSE_INFL)
    b_k9 = PG.build(PG.drop(FP, {'R75.1'}), SENSE_INFL)
    b_tr = PG.build(PG.drop(FP, {'R75.2', 'D9.1'}), TRUNK_INFL)

    poses = []
    for rot in (0, 90, 180, 270):
        rect, _ = M.local('U18', rot)
        for xi in range(int((15.0 - 5.0) / 0.25) + 1):
            x = 5.0 + xi * 0.25
            for yi in range(int((78.0 - 58.0) / 0.25) + 1):
                y = 58.0 + yi * 0.25
                c = (x + rect[0], y + rect[1], x + rect[2], y + rect[3])
                if (c[0] < M.edge[0] or c[1] < M.edge[1] or
                        c[2] > M.edge[2] or c[3] > M.edge[3]):
                    continue
                if any(ovl(c, fr) for fr in fixed_r):
                    continue
                if any(ovl(c, rr) for rr in M.rule):
                    continue
                p8 = M.pad('U18', '8', x, y, rot)
                p9 = M.pad('U18', '9', x, y, rot)
                if math.dist(p8, r75_2) > 11.0 or math.dist(p9, r75_1) > 11.0:
                    continue
                poses.append((rot, x, y, c))
    if verbose:
        print('stage 1: %d U18 poses survive courtyard collision + Kelvin envelope'
              % len(poses))

    scored = []
    for (rot, x, y, uc) in poses:
        UP = M.padrects_id('U18', x, y, rot)
        p8 = M.pad('U18', '8', x, y, rot)
        p9 = M.pad('U18', '9', x, y, rot)
        k8 = PG.path(b_k8 | PG.build(PG.drop(UP, {'U18.8'}), SENSE_INFL), p8, r75_2)
        if k8 is None or k8 > 10.0:
            continue
        k9 = PG.path(b_k9 | PG.build(PG.drop(UP, {'U18.9'}), SENSE_INFL), p9, r75_1)
        if k9 is None or k9 > 10.0:
            continue
        mis = abs(k8 - k9)
        if mis > 5.0:
            continue
        trunk = PG.path(b_tr | PG.build([r for (_, r) in UP], TRUNK_INFL),
                        r75_2, d9_1)
        if trunk is None:
            continue
        scored.append(dict(rot=rot, x=round(x, 3), y=round(y, 3),
                           k8=round(k8, 3), k9=round(k9, 3), mis=round(mis, 3),
                           trunk=round(trunk, 3), court=uc))
    if verbose:
        print('stage 1: %d poses keep both Kelvin <= 10 mm, mismatch <= 5 mm '
              'and a 1.50 mm trunk corridor' % len(scored))
    scored.sort(key=lambda s: (s['mis'], s['k8'] + s['k9'], s['trunk']))
    return scored, dict(r75_1=r75_1, r75_2=r75_2, d9_1=d9_1, fixed=fixed,
                        fixed_r=fixed_r, shadow_max=shadow_max, PG=PG, FP=FP)


# ------------------------------------------------------------------ stage 2
# Every passive that serves a U18 pin, plus the test points section 8 releases.
# A part is placed BY THE PIN IT SERVES.  That is what turns the divider wall
# from an obstacle into a service ring: in FBV2-P2-002E the wall sat at
# x 7.30..10.35 as a solid 16 mm barrier and every north-row U18 pin had to
# cross the same 2.2 mm corridor to reach the far side of it.
RING2 = [
    # ref    pad -> target            chain pad -> target      weight
    ('R76', '1', 'U18.10', '2', 'C57.1'),
    ('R77', '1', 'U18.1', '2', 'U18.3'),
    ('R79', '2', 'U18.2', '1', 'R77.1'),
    ('R80', '2', 'U18.6', '1', 'R79.1'),
    ('R81', '2', 'U18.7', '1', None),
    ('R78', '1', 'R77.2', '2', None),
    ('R82', '1', 'R81.2', '2', None),
    ('R83', '1', 'TP19.1', '2', None),
    ('C57', '1', 'R76.2', '2', None),
    ('TP17', '1', 'U18.10', None, None),
    ('TP19', '1', 'R83.1', None, None),
    ('C58', '1', 'D9.1', '2', None),
]
SLOT_X = (4.0, 20.0, 0.5)
SLOT_Y = (56.0, 80.0, 0.5)


def slot_table(M, ctx):
    """Every (x, y, rot) at which each ring part clears the FIXED world.  Built
    once; the pose-dependent tests are then cheap."""
    tab = {}
    for (ref, _a, _b, _c, _d) in RING2:
        cand = []
        for rot in (0, 90):
            rect, _ = M.local(ref, rot)
            xi = SLOT_X[0]
            while xi <= SLOT_X[1] + 1e-9:
                yi = SLOT_Y[0]
                while yi <= SLOT_Y[1] + 1e-9:
                    c = (xi + rect[0], yi + rect[1], xi + rect[2], yi + rect[3])
                    if (c[0] >= M.edge[0] and c[1] >= M.edge[1] and
                            c[2] <= M.edge[2] and c[3] <= M.edge[3] and
                            not any(ovl(c, fr) for fr in ctx['fixed_r']) and
                            not any(ovl(c, rr) for rr in M.rule)):
                        cand.append((xi, yi, rot, c))
                    yi += SLOT_Y[2]
                xi += SLOT_X[2]
        tab[ref] = cand
    return tab


def trunk_corridor(M, ctx, pose_u18, extra=None):
    """Section 3D.  The 1.50 mm BAT_PROTECTED_P trunk is the highest-priority
    corridor on this board (section 4's own order), so it is reserved BEFORE
    the ring is placed rather than checked afterwards.  A 0603 dropped on top
    of it is exactly how FBV2-P2-002E's predecessor lost the trunk to a
    0.20 mm sense tap."""
    PG = ctx['PG']
    UP = M.padrects('U18', pose_u18['x'], pose_u18['y'], pose_u18['rot'])
    pairs = list(ctx['FP'])
    if extra:
        for r, pos in extra.items():
            if r == 'U18':
                continue
            pairs += M.padrects_id(r, *pos)
    blk = PG.build(PG.drop(pairs, {'R75.2', 'D9.1'}), TRUNK_INFL) |         PG.build(UP, TRUNK_INFL)
    r = PG.path(blk, ctx['r75_2'], ctx['d9_1'], want_pts=True)
    return (None, []) if r is None else r


def near_poly(rect, pts, gap):
    for (px, py) in pts:
        if (rect[0] - gap <= px <= rect[2] + gap and
                rect[1] - gap <= py <= rect[3] + gap):
            return True
    return False


SIDE_PIN = {}          # filled per pose: pin -> (side, along-row coordinate)


def row_geometry(M, pose):
    """Which side of U18 each signal pin leaves by, and where it sits along
    that row.  An MSOP-10's pads can only emit along their own long axis - the
    0.15 mm between neighbouring pads is less than any legal track plus its
    clearance - so 'which side' is a fact about the package, not a preference."""
    x, y, rot = pose['x'], pose['y'], pose['rot']
    cx, cy = x, y
    out = {}
    for pin in U18PINS:
        px, py = M.pad('U18', pin, x, y, rot)
        if abs(px - cx) >= abs(py - cy):
            out[pin] = ('E' if px > cx else 'W', py)
        else:
            out[pin] = ('S' if py > cy else 'N', px)
    return out


def crossings(M, place, rows, targets):
    """Count order inversions between a pin row and the pads it serves.

    THIS IS THE DEFECT THAT COST FBV2-P2-002F ITS FIRST PHASE A.  The ring was
    scored on service DISTANCE alone, so R77 was placed with its BAT_RAW pad
    SOUTH of its LTC_OV pad - which put U18.1's target on the far side of
    U18.2 and U18.3.  U18.1 routed first (it is tighter), crossed in front of
    both, and `U18.2` came back NO_LEGAL_ESCAPE with its own neighbours and
    that track as the blockers.  A pin row and its targets have to be in the
    SAME ORDER or the routes cross, and on a 0.5 mm pitch there is no room to
    cross."""
    n = 0
    for side in ('E', 'W', 'N', 'S'):
        pins = sorted((v[1], k) for k, v in rows.items()
                      if v[0] == side and k in targets)
        seq = []
        for (_a, pin) in pins:
            tag = targets[pin]
            r, num = tag.split('.')
            pos = place.get(r, M.home.get(r))
            if pos is None:
                continue
            tx, ty = M.pad(r, num, *pos)
            seq.append(ty if side in ('E', 'W') else tx)
        for i in range(len(seq)):
            for j in range(i + 1, len(seq)):
                if seq[j] < seq[i]:
                    n += 1
    return n


def wrong_side(M, place, rows, targets):
    """A pin's target must be ON THE SIDE THE PIN FACES.

    PR-31, and it is the U18.10 detour stated geometrically.  A fine-pitch pad
    can only emit along its own axis - the 0.15 mm between neighbouring pads is
    less than any legal track plus its clearance - so a pin leaves by exactly
    one side of the package.  Put its partner on the OTHER side and the route
    does not shorten, it WRAPS: `U18.10` is a west-row pin and R76 was placed
    east of U18, which cost 18.4 mm of copper right across the lanes the east
    row needs, and `U18.2` lost its escape to it.

    Scored as the distance the target sits BEHIND the pad along the pin's own
    outward direction, so a partner that is merely off to one side is free and
    one that is genuinely on the far side is not.
    """
    pen = 0.0
    for pin, tag in targets.items():
        if pin not in rows:
            continue
        side = rows[pin][0]
        out = {'E': (1, 0), 'W': (-1, 0), 'S': (0, 1), 'N': (0, -1)}[side]
        r, num = tag.split('.')
        pos = place.get(r, M.home.get(r))
        if pos is None:
            continue
        tx, ty = M.pad(r, num, *pos)
        px, py = M.pad('U18', pin, *place['U18'])
        proj = (tx - px) * out[0] + (ty - py) * out[1]
        if proj < 0:
            pen += -proj
    return pen


# the pad each U18 signal pin is routed to first, from battery_route_plan
U18TARGET = {'1': 'R77.1', '2': 'R79.2', '3': 'R77.2', '6': 'R80.2',
             '7': 'R81.2', '8': 'R75.2', '9': 'R75.1', '10': 'R76.1'}


RESTARTS = [
    (0.5, None),
    (0.5, ['R77', 'R79', 'R81', 'R80', 'R76', 'R78', 'R82', 'R83', 'C57', 'TP17', 'TP19', 'C58']),
    (0.1, None),
    (1.5, None),
    (0.1, ['R79', 'R77', 'R80', 'R81', 'R76', 'R78', 'R82', 'R83', 'C57', 'TP17', 'TP19', 'C58']),
    (0.5, ['R76', 'R81', 'R80', 'R79', 'R77', 'R78', 'R82', 'R83', 'C57', 'TP17', 'TP19', 'C58']),
    (1.0, ['R77', 'R81', 'R79', 'R76', 'R80', 'R78', 'R82', 'R83', 'C57', 'TP17', 'TP19', 'C58']),
    (0.3, ['R80', 'R79', 'R77', 'R76', 'R81', 'R78', 'R82', 'R83', 'C57', 'TP17', 'TP19', 'C58']),
]


def ring(M, ctx, tab, pose_u18, corridor=(), rounds=4, chain_w=0.5, order=None):
    """Assign every ring part to the free slot that best serves its U18 pin.

    Iterated: R79 chains to R77.1 and R77 has not been placed on the first
    sweep, so one greedy pass scores half the ring against stale positions.
    Four sweeps are enough for this to stop moving.
    """
    rot_u, x_u, y_u = pose_u18['rot'], pose_u18['x'], pose_u18['y']
    place = {'U18': (x_u, y_u, rot_u)}
    for (ref, _a, _b, _c, _d) in RING2:
        place[ref] = M.home[ref]
    d9_1 = ctx['d9_1']

    def padof(tag, pl):
        r, n = tag.split('.')
        if r in pl:
            return M.pad(r, n, *pl[r])
        return M.pad(r, n, *M.home[r])

    def courts(pl, skip):
        return [M.court(r, *pl[r]) for r in pl if r != skip]

    rows = row_geometry(M, pose_u18)
    spec = {r[0]: r for r in RING2}
    seq = [spec[r] for r in order] if order else list(RING2)
    for _ in range(rounds):
        moved = False
        for (ref, pa, ta, pb, tb) in seq:
            others = courts(place, ref)
            best = None
            for (xi, yi, rot, c) in tab[ref]:
                if any(ovl(c, o) for o in others):
                    continue
                # 1.10 mm, not 0.30: the reserved path is the CENTRELINE of a
                # 1.50 mm trunk, so it needs 0.75 mm of half-width plus its
                # 0.20 mm clearance before a part may sit beside it.  At
                # 0.30 mm the ring crowded the trunk from both sides and
                # `R75.2 -> D9.1` detoured 17.625 -> 40.625 mm - which is
                # 23 mm of extra 1.50 mm copper straight onto B-34.
                if corridor and near_poly(c, corridor, 1.10):
                    continue
                cost = math.dist(M.pad(ref, pa, xi, yi, rot), padof(ta, place))
                if pb and tb:
                    cost += chain_w * math.dist(M.pad(ref, pb, xi, yi, rot),
                                                padof(tb, place))
                trial = dict(place)
                trial[ref] = (xi, yi, rot)
                cost += 12.0 * crossings(M, trial, rows, U18TARGET)
                cost += 4.0 * wrong_side(M, trial, rows, U18TARGET)
                if ref == 'C58':
                    # section 10: C58 stays on the trunk beside D9
                    dd = math.dist(M.pad(ref, '1', xi, yi, rot), d9_1)
                    if dd > 6.0:
                        continue
                if best is None or cost < best[0]:
                    best = (cost, xi, yi, rot)
            if best is None:
                return None
            if (best[1], best[2], best[3]) != tuple(place[ref]):
                moved = True
            place[ref] = (best[1], best[2], best[3])
        if not moved:
            break
    return place


# ------------------------------------------------------------------ stage 3
def qpads(qb):
    d = {}
    for (net, ref), p in qb.pads.items():
        d[ref] = p
        d.setdefault('by_net', {}).setdefault(net, {})[ref] = p
    return d


def esc(qb, pad, w, ct=CT_W, prefer=None):
    return qb.escape(pad, 'B', w, w, CP, ct, 25000, qb.ex0, qb.ey0, prefer=prefer)


def reach(qb, pad_a, ea, w, pad_b, ct=CT_W):
    """Is pad_b's escape in the same free region as pad_a's?

    An escape cell is NOT reachability: a pad can emit a perfectly legal
    0.20 mm stub into a sealed pocket.  Flood the whole free region and ask.
    """
    reg = qb.free_region('B', pad_a['net'], w, CP, ct, 50000,
                         (ea['x'], ea['y']),
                         qb.ex0 - 1000000, qb.ey0 - 1000000,
                         qb.ex1 + 1000000, qb.ey1 + 1000000)
    if reg is None:
        return False
    seen, ox, oy, G = reg
    eb = esc(qb, pad_b, w, ct)
    for e in eb:
        i = int((e['x'] - ox) // G)
        j = int((e['y'] - oy) // G)
        if 0 <= j < seen.shape[0] and 0 <= i < seen.shape[1] and seen[j, i]:
            return True
    return False


def stage3(M, place, tag, verbose=False):
    """The real obstacle model.  Per-pad legal escape, then all eight U18
    escapes laid SIMULTANEOUSLY (section 3C), then free-region reachability."""
    d = os.path.join(WORK, tag)
    if not os.path.isdir(d):
        RU.fresh(WORK, tag)
    pcb = os.path.join(WORK, tag, RU.PCBNAME)
    M.write(pcb, place)
    qb = QR.QBoard(pcb)
    qb.wide_nets = frozenset(N + n for n in ('BAT_CONNECTOR_P', 'BAT_RAW',
                                             'BAT_MID', 'BAT_SENSE',
                                             'BAT_PROTECTED_P'))
    P = qpads(qb)
    out = dict(tag=tag, escapes={}, laid=0, independent=True, reach={})

    # ---- 1. every U18 signal pad, on the BARE board
    want = []
    for n_, net in U18PINS.items():
        p = P.get('U18.' + n_)
        if p is None:
            out['escapes']['U18.' + n_] = None
            continue
        e = esc(qb, p, U18MIN[n_])
        out['escapes']['U18.' + n_] = (round(e[0]['w'] / 1e6, 3) if e else None)
        if e:
            want.append(('U18.' + n_, p, e[0], U18MIN[n_]))
    out['u18'] = sum(1 for v in out['escapes'].values() if v)

    # ---- 2. Q3 gate and CS, same test
    for n_ in ('1', '2', '3', '4'):
        p = P.get('Q3.' + n_)
        e = esc(qb, p, 150000, CT_S) if p else None
        out['escapes']['Q3.' + n_] = (round(e[0]['w'] / 1e6, 3) if e else None)
    out['q3'] = sum(1 for k, v in out['escapes'].items()
                    if k.startswith('Q3.') and v)

    # ---- 3. SIMULTANEITY.  Section 3C: no escape may depend on another U18
    #         signal already being routed.  Lay every stub, then require that
    #         every pad that had an escape on the bare board STILL has one.
    m = qb.mark()
    for (ref, p, e, w) in want:
        qb.track(p['net'], 'B', p['x'], p['y'], e['x'], e['y'], w)
        out['laid'] += 1
    for (ref, p, e, w) in want:
        if not esc(qb, p, w):
            out['independent'] = False
            out.setdefault('dependent', []).append(ref)
    qb.revert(m)

    # ---- 4. REACHABILITY, on the bare board
    TARGETS = {'8': 'R75.2', '9': 'R75.1'}
    for n_, tgt in TARGETS.items():
        a, b = P.get('U18.' + n_), P.get(tgt)
        ea = esc(qb, a, U18MIN[n_]) if a else None
        out['reach']['U18.%s->%s' % (n_, tgt)] = bool(
            ea and b and reach(qb, a, ea[0], U18MIN[n_], b))
    # the 1.50 mm trunk, R75.2 -> D9.1, must still reach
    a, b = P.get('R75.2'), P.get('D9.1')
    ea = esc(qb, a, 1500000)
    out['trunk_escape'] = round(ea[0]['w'] / 1e6, 3) if ea else None
    out['reach']['R75.2->D9.1@1.50'] = bool(ea and reach(qb, a, ea[0], 1500000, b))
    return out, pcb


# --------------------------------------------------------------------- main
def fanout(M, place, PG, FP, rows=None):
    """Route all eight U18 pin -> target paths SEQUENTIALLY, in the routing
    plan's own order, each one blocking the next.

    This is the test the first FBV2-P2-002F ring did not have, and it is the
    only one that matters.  Scoring the ring on service DISTANCE put R77's
    BAT_RAW pad on the far side of U18.2 and U18.3; scoring it on ORDER alone
    then stacked all three targets on the same y, so U18.2 had to cross R77's
    body to reach R79.  Neither is visible one-pin-at-a-time on an empty board
    - both are obvious the moment the pins are routed together.
    """
    order = ['9', '8', '1', '7', '3', '2', '10', '6']       # plan / slack order
    pairs = list(FP)
    for r, pos in place.items():
        pairs += M.padrects_id(r, *pos)
    laid = []
    ok, lens = [], {}
    for pin in order:
        tag = U18TARGET[pin]
        r, num = tag.split('.')
        pos = place.get(r, M.home.get(r))
        if pos is None:
            continue
        w = U18MIN[pin]
        infl = 0.10 + w / 2e6 + 0.10
        blk = PG.build(PG.drop(pairs, {'U18.' + pin, tag}), infl)
        for pts in laid:
            blk |= PG.build([(x - 0.15, y - 0.15, x + 0.15, y + 0.15)
                             for (x, y) in pts], infl)
        a = M.pad('U18', pin, *place['U18'])
        b = M.pad(r, num, *pos)
        got = PG.path(blk, a, b, want_pts=True)
        if got is None:
            ok.append(pin + ':X')
            continue
        d, pts = got
        lens[pin] = round(d, 2)
        laid.append(pts[::3])
        ok.append(pin)
    return sum(1 for k in ok if not k.endswith(':X')), lens, ok


def shortlist(scored, n=24):
    """A DIVERSE shortlist, not just the top of the sort.  Taking the best n
    rows returns twenty variants of one pose 0.25 mm apart and proves nothing;
    one representative per (rotation, 1 mm cell) keeps the families that the
    stage 1 table actually found."""
    seen, out = set(), []
    for s in scored:
        key = (s['rot'], round(s['x']), round(s['y']))
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= n:
            break
    return out


def build_ctx(M):
    fixed = M.fixed_courts(MOVABLE)
    return dict(r75_1=M.pad('R75', '1', *M.home['R75']),
                r75_2=M.pad('R75', '2', *M.home['R75']),
                d9_1=M.pad('D9', '1', *M.home['D9']),
                fixed=fixed, fixed_r=[c for (_, _, c) in fixed],
                shadow_max=max([pkg_h(M.fpid[r]) for (r, _, c) in fixed
                                if ovl(c, BATTERY)] or [1.10]),
                PG=PathGrid(0.0, 52.0, 26.0, 84.0, 0.25),
                FP=M.fixed_pads(MOVABLE))


PLAN = os.path.join(SP, 'place_002f_plan.json')


def do_plan():
    """Stages 1 and 2.  Writes one placement per candidate; the escape proof
    runs in a SEPARATE PROCESS per candidate, because holding a dozen pcbnew
    BOARD objects alive in one interpreter segfaults it - which is how this
    script died twice before the split."""
    t0 = time.time()
    cache = os.path.join(SP, 'place_002f_stage1.json')
    M = Model(RU.fresh(WORK, 'M0'))
    ctx = build_ctx(M)
    if os.path.exists(cache) and '--rescan' not in sys.argv:
        scored = json.load(open(cache))['scored']
    else:
        scored, _c = stage1(M)
        json.dump(dict(scored=scored), open(cache, 'w'), indent=1)
    print('stage 1: %d poses on the table' % len(scored))
    tab = slot_table(M, ctx)
    print('stage 2: %d slots per 0603' % len(tab['R76']))
    sys.stdout.flush()
    out = []
    for k, s_ in enumerate(shortlist(scored, int(os.environ.get('AQROOT_SHORTLIST', '20')))):
        tag = 'C%02d' % k
        tl, corr = trunk_corridor(M, ctx, s_)
        if tl is None:
            print('  %s  NO TRUNK CORRIDOR' % tag)
            continue
        # RESTARTS.  The ring is a coordinate descent and it has local minima
        # that look fine on distance and fail on fan-out, so several are tried
        # and the one that actually routes eight of eight wins.
        best = None
        for k, (cw, order) in enumerate(RESTARTS):
            pl = ring(M, ctx, tab, s_, corridor=corr, chain_w=cw, order=order)
            if pl is None:
                continue
            n_, lens, det = fanout(M, pl, ctx['PG'], ctx['FP'])
            # the trunk is re-measured WITH the ring in place: section 4 puts
            # the legal trunk above every U18 quality target, so a ring that
            # buys a short VIN tap with 20 mm of extra 1.50 mm copper loses.
            tl2, _c2 = trunk_corridor(M, ctx, s_, extra=pl)
            tl2 = 999.0 if tl2 is None else tl2
            svc = sum(lens.values())
            score = (n_, -round(tl2, 1), -svc)
            if best is None or score > best[0]:
                best = (score, pl, det, svc, lens, tl2)
            if n_ == 8 and tl2 <= tl + 3.0:
                break
        if best is None:
            print('  %s  RING INFEASIBLE' % tag)
            continue
        (n_, _nt, _ns), pl, det, svc, lens, tl2 = best
        out.append(dict(id=tag, rot=s_['rot'], x=s_['x'], y=s_['y'], k8=s_['k8'],
                        k9=s_['k9'], mis=s_['mis'], trunk=round(tl2, 3),
                        trunk_bare=round(tl, 3), fanout=n_, fanout_lens=lens,
                        place={a: [round(v, 3) for v in b] for a, b in pl.items()}))
        print('  %s rot=%3d (%6.2f,%6.2f) k8=%5.2f k9=%5.2f mis=%5.2f trunk=%5.2f'
              '->%5.2f  FANOUT %d/8  %s'
              % (tag, s_['rot'], s_['x'], s_['y'], s_['k8'], s_['k9'], s_['mis'],
                 tl, tl2, n_, ' '.join(det)))
        sys.stdout.flush()
    json.dump(out, open(PLAN, 'w'), indent=1)
    print('plan: %d candidates in %.1f s' % (len(out), time.time() - t0))


def do_probe(tag):
    plan = {c['id']: c for c in json.load(open(PLAN))}
    c = plan[tag]
    M = Model(RU.fresh(WORK, 'M1'))
    place = {k: tuple(v) for k, v in c['place'].items()}
    r, _p = stage3(M, place, tag)
    r.update({k: c[k] for k in ('rot', 'x', 'y', 'k8', 'k9', 'mis', 'trunk')})
    json.dump(r, open(os.path.join(SP, 'place_002f_probe_%s.json' % tag), 'w'), indent=1)
    print('%s U18 %d/8  Q3 %d/4  indep=%s  reach=%s'
          % (tag, r['u18'], r['q3'], r['independent'],
             ''.join('1' if v else '0' for v in r['reach'].values())))


def main():
    faulthandler.enable()
    if '--probe' in sys.argv:
        return do_probe(sys.argv[sys.argv.index('--probe') + 1])
    return do_plan()


if __name__ == '__main__':
    main()
