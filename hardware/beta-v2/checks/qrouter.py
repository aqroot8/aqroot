# -*- coding: utf-8 -*-
"""AQROOT Full Beta v2 qualified obstacle-aware router (FBV2-P2-002B).

Everything is integer nanometres.  There is no float coordinate anywhere in the
emitted geometry, which is what makes the neck/trunk join EXACT rather than
merely close (defect PR-5A).

Three rules the previous harness broke, and how they are enforced here:

  PR-5A  the neck end and the trunk start are the SAME integer nm point, and
         both pads are checked to actually exist on the routing layer.
  PR-5B  a neck may never be narrower than the applicable KiCad rule minimum.
         If the land pattern cannot accept that width, the pad is classified
         NO LEGAL ESCAPE and nothing is emitted.
  PR-5C  the neck is checked against the SAME obstacle set as the trunk,
         analytically, before it is emitted.
"""
import math, heapq, collections
import numpy as np
import pcbnew

MM = 1000000            # nm per mm
EDGE_CLR = 500000       # 0.5 mm min copper->edge
LNAME = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}


# --------------------------------------------------------------------------
# geometry primitives, all in nm
# --------------------------------------------------------------------------
class RR(object):
    """Rounded rectangle: covers rect, roundrect, oval, circle, and (as a
    conservative bbox) trapezoid/chamfered/custom."""
    __slots__ = ('cx', 'cy', 'hx', 'hy', 'r', 'ca', 'sa', 'net', 'tag')

    def __init__(self, cx, cy, hx, hy, r, ang_deg, net, tag=''):
        self.cx, self.cy = cx, cy
        self.hx, self.hy = max(hx, 0), max(hy, 0)
        self.r = max(0, min(r, min(self.hx, self.hy)))
        a = math.radians(ang_deg)
        self.ca, self.sa = math.cos(a), math.sin(a)
        self.net, self.tag = net, tag

    def bbox(self, m):
        ex = abs(self.hx * self.ca) + abs(self.hy * self.sa) + m
        ey = abs(self.hx * self.sa) + abs(self.hy * self.ca) + m
        return self.cx - ex, self.cy - ey, self.cx + ex, self.cy + ey

    def dist(self, px, py):
        dx, dy = px - self.cx, py - self.cy
        lx = abs(dx * self.ca + dy * self.sa)
        ly = abs(-dx * self.sa + dy * self.ca)
        ax = max(lx - (self.hx - self.r), 0.0)
        ay = max(ly - (self.hy - self.r), 0.0)
        return math.hypot(ax, ay) - self.r

    def dist_np(self, X, Y):
        dx, dy = X - self.cx, Y - self.cy
        lx = np.abs(dx * self.ca + dy * self.sa)
        ly = np.abs(-dx * self.sa + dy * self.ca)
        ax = np.maximum(lx - (self.hx - self.r), 0.0)
        ay = np.maximum(ly - (self.hy - self.r), 0.0)
        return np.hypot(ax, ay) - self.r

    def extent(self, ux, uy):
        """How far the shape reaches from its centre along unit vector (ux,uy)."""
        lx = ux * self.ca + uy * self.sa
        ly = -ux * self.sa + uy * self.ca
        return abs(lx) * (self.hx - self.r) + abs(ly) * (self.hy - self.r) + self.r


class SEG(object):
    """A laid track: a capsule."""
    __slots__ = ('x0', 'y0', 'x1', 'y1', 'hw', 'net', 'tag')

    def __init__(self, x0, y0, x1, y1, hw, net, tag=''):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.hw, self.net, self.tag = hw, net, tag

    def bbox(self, m):
        return (min(self.x0, self.x1) - self.hw - m, min(self.y0, self.y1) - self.hw - m,
                max(self.x0, self.x1) + self.hw + m, max(self.y0, self.y1) + self.hw + m)

    def dist(self, px, py):
        vx, vy = float(self.x1 - self.x0), float(self.y1 - self.y0)
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - self.x0) * vx + (py - self.y0) * vy) / L2))
        return math.hypot(px - (self.x0 + t * vx), py - (self.y0 + t * vy)) - self.hw

    def dist_np(self, X, Y):
        vx, vy = float(self.x1 - self.x0), float(self.y1 - self.y0)
        L2 = vx * vx + vy * vy
        if L2 == 0:
            T = np.zeros_like(X, dtype=float)
        else:
            T = np.clip(((X - self.x0) * vx + (Y - self.y0) * vy) / L2, 0.0, 1.0)
        return np.hypot(X - (self.x0 + T * vx), Y - (self.y0 + T * vy)) - self.hw

    def extent(self, ux, uy):
        return self.hw


def seg_shape_dist(x0, y0, x1, y1, shape, step=20000):
    """Distance from a segment centre-line to a shape.  Point-to-shape distance
    is 1-Lipschitz along the line, so sampling at `step` and subtracting half a
    step is a sound lower bound."""
    L = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(L / step) + 1)
    best = 1e18
    for k in range(n + 1):
        t = k / float(n)
        d = shape.dist(x0 + t * (x1 - x0), y0 + t * (y1 - y0))
        if d < best:
            best = d
    return best - (L / n) / 2.0


# --------------------------------------------------------------------------
class QBoard(object):
    def __init__(self, path):
        self.path = path
        self.b = pcbnew.LoadBoard(path)
        self.nets = {n.GetNetname(): n for n in self.b.GetNetsByName().values()}
        self.pads = {}          # (net, "REF.PAD") -> dict
        self.shapes = {'F': [], 'B': []}
        self.holes = []         # blocks every layer
        self.escape_why = []
        self._scan()
        bb = self.b.GetBoardEdgesBoundingBox()
        self.ex0, self.ey0 = bb.GetLeft(), bb.GetTop()
        self.ex1, self.ey1 = bb.GetRight(), bb.GetBottom()
        self.laid = []

    # ---------------------------------------------------------------- scan
    def _scan(self):
        for f in self.b.GetFootprints():
            ref = f.GetReference()
            for p in f.Pads():
                net = p.GetNetname()
                pos = p.GetPosition()
                sx, sy = p.GetSizeX() / 2.0, p.GetSizeY() / 2.0
                sh = p.GetShape()
                if sh in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL):
                    r = min(sx, sy)
                elif sh == pcbnew.PAD_SHAPE_ROUNDRECT:
                    r = p.GetRoundRectCornerRadius()
                else:
                    r = 0
                ang = p.GetOrientationDegrees()
                tag = ref + '.' + p.GetNumber()
                onF, onB = p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)
                s = RR(pos.x, pos.y, sx, sy, r, ang, net, tag)
                if onF:
                    self.shapes['F'].append(s)
                if onB:
                    self.shapes['B'].append(s)
                d = p.GetDrillSizeX()
                if d > 0:
                    dy = p.GetDrillSizeY() or d
                    self.holes.append(RR(pos.x, pos.y, d / 2.0, dy / 2.0,
                                         min(d, dy) / 2.0, ang, net, tag + '/hole'))
                if net and p.GetNumber():
                    self.pads[(net, tag)] = dict(
                        ref=tag, x=pos.x, y=pos.y, F=onF, B=onB, shape=s,
                        hx=sx, hy=sy, r=r, ang=ang, net=net,
                        tht=p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,
                                                 pcbnew.PAD_ATTRIB_NPTH))

        def addko(z, forceboth=False):
            # Honour the rule area exactly as authored.  Blocking layers the
            # zone does not claim invents NO-PATH results that DRC would never
            # have raised, and inventing obstacles is the same class of error as
            # ignoring them.  (U1's antenna keep-out is declared F.Cu only.)
            if not (z.GetIsRuleArea() and z.GetDoNotAllowTracks()):
                return
            bb = z.GetBoundingBox()
            s = RR((bb.GetLeft() + bb.GetRight()) / 2.0,
                   (bb.GetTop() + bb.GetBottom()) / 2.0,
                   bb.GetWidth() / 2.0, bb.GetHeight() / 2.0, 0, 0, None, 'KO')
            for L in ('F', 'B'):
                if z.IsOnLayer(LNAME[L]):
                    self.shapes[L].append(s)

        for z in self.b.Zones():
            addko(z)
        for f in self.b.GetFootprints():
            for z in f.Zones():
                addko(z, True)
        for t in self.b.GetTracks():
            if t.GetClass() != 'PCB_TRACK':
                continue
            for L in ('F', 'B'):
                if t.IsOnLayer(LNAME[L]):
                    self.shapes[L].append(SEG(t.GetStart().x, t.GetStart().y,
                                              t.GetEnd().x, t.GetEnd().y,
                                              t.GetWidth() / 2.0, t.GetNetname(), 'track'))

    def obstacles(self, layer, net):
        return ([s for s in self.shapes[layer] if s.net != net] +
                [h for h in self.holes if h.net != net])

    # ------------------------------------------------------------- raster
    def margin(self, s, width, clr_pad, clr_trk):
        """Per-obstacle clearance.  A keep-out admits no copper at all; a pad
        and a track can carry different rule clearances (BAT_MAIN is 0.20 mm to
        a pad and 0.30 mm to another track)."""
        if s.net is None and s.tag == 'KO':
            return width / 2.0
        return width / 2.0 + (clr_trk if isinstance(s, SEG) else clr_pad)

    def grid(self, layer, net, width, clr_pad, clr_trk, x0, y0, x1, y1, G):
        """Blocked-cell grid.

        GUARD BAND, and it is not optional: the search proves that GRID CELLS
        are clear, but the emitted track is a CONTINUOUS segment between them
        and can pass up to ~0.75 of a cell closer to an obstacle than either
        sampled endpoint.  Without this the router hands DRC a 0.172 mm gap on
        a 0.200 mm rule and calls it proved.  Section 9: grid conversion may
        never create geometry that violates the path the search proved."""
        nx = int((x1 - x0) // G) + 1
        ny = int((y1 - y0) // G) + 1
        guard = G * 0.75
        blk = np.zeros((ny, nx), dtype=bool)
        for s in self.obstacles(layer, net):
            mm_ = self.margin(s, width, clr_pad, clr_trk) + guard
            bx0, by0, bx1, by1 = s.bbox(mm_)
            i0 = max(0, int(math.floor((bx0 - x0) / G)))
            i1 = min(nx - 1, int(math.ceil((bx1 - x0) / G)))
            j0 = max(0, int(math.floor((by0 - y0) / G)))
            j1 = min(ny - 1, int(math.ceil((by1 - y0) / G)))
            if i1 < i0 or j1 < j0:
                continue
            XX = (x0 + np.arange(i0, i1 + 1) * G).astype(float)
            YY = (y0 + np.arange(j0, j1 + 1) * G).astype(float)
            X, Y = np.meshgrid(XX, YY)
            blk[j0:j1 + 1, i0:i1 + 1] |= (s.dist_np(X, Y) < mm_)
        lim = EDGE_CLR + width / 2.0 + guard
        XX = (x0 + np.arange(nx) * G).astype(float)
        YY = (y0 + np.arange(ny) * G).astype(float)
        X, Y = np.meshgrid(XX, YY)
        blk |= ((X < self.ex0 + lim) | (X > self.ex1 - lim) |
                (Y < self.ey0 + lim) | (Y > self.ey1 - lim))
        return blk

    # --------------------------------------------------------------- astar
    def astar(self, blk, s, t, bendcost=1.0):
        ny, nx = blk.shape
        if not (0 <= s[0] < nx and 0 <= s[1] < ny and 0 <= t[0] < nx and 0 <= t[1] < ny):
            return None
        flat = blk.reshape(-1)
        S, T = s[1] * nx + s[0], t[1] * nx + t[0]
        if flat[S] or flat[T]:
            return None
        D = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
             (1, 1, 1.41421356), (1, -1, 1.41421356),
             (-1, 1, 1.41421356), (-1, -1, 1.41421356))
        g = {(S, -1): 0.0}
        par = {}
        seen = set()
        pq = [(math.hypot(t[0] - s[0], t[1] - s[1]), 0.0, S, -1)]
        while pq:
            f, c, u, du = heapq.heappop(pq)
            if (u, du) in seen:
                continue
            seen.add((u, du))
            if u == T:
                path = [u]
                k = (u, du)
                while k in par:
                    k = par[k]
                    path.append(k[0])
                return [(p % nx, p // nx) for p in reversed(path)]
            ux, uy = u % nx, u // nx
            for di, (dx, dy, w) in enumerate(D):
                vx, vy = ux + dx, uy + dy
                if not (0 <= vx < nx and 0 <= vy < ny):
                    continue
                v = vy * nx + vx
                if flat[v]:
                    continue
                if dx and dy:
                    if flat[uy * nx + vx] or flat[vy * nx + ux]:
                        continue
                ng = c + w + (bendcost if (du >= 0 and di != du) else 0.0)
                if ng < g.get((v, di), 1e18):
                    g[(v, di)] = ng
                    par[(v, di)] = (u, du)
                    heapq.heappush(pq, (ng + math.hypot(t[0] - vx, t[1] - vy), ng, v, di))
        return None


    # ------------------------------------------------ wavefront + smoothing
    @staticmethod
    def wave(blk, t, s):
        """8-connected BFS distance field from `t`, vectorised.

        Exhaustive A* over a whole-board window is hundreds of millions of
        Python-level states; this is the same search done as ~one numpy shift
        per wavefront step.  It minimises STEP COUNT rather than Euclidean
        length, so the raw path staircases -- `smooth()` straightens it back
        out afterwards, and every straightened segment is re-tested against the
        SAME blocked grid, so nothing is straightened through an obstacle.
        """
        ny, nx = blk.shape
        free = ~blk
        dist = np.full((ny, nx), -1, dtype=np.int32)
        if not free[t[1], t[0]]:
            return None
        dist[t[1], t[0]] = 0
        cur = np.zeros((ny, nx), dtype=bool)
        cur[t[1], t[0]] = True
        d = 0
        while True:
            if cur[s[1], s[0]]:
                return dist
            nxt = np.zeros((ny, nx), dtype=bool)
            # orthogonal
            nxt[1:, :] |= cur[:-1, :]
            nxt[:-1, :] |= cur[1:, :]
            nxt[:, 1:] |= cur[:, :-1]
            nxt[:, :-1] |= cur[:, 1:]
            # diagonal, no corner cutting: both orthogonal neighbours must be free
            dn = np.zeros((ny, nx), dtype=bool)
            dn[1:, 1:] |= cur[:-1, :-1] & free[:-1, 1:] & free[1:, :-1]
            dn[1:, :-1] |= cur[:-1, 1:] & free[:-1, :-1] & free[1:, 1:]
            dn[:-1, 1:] |= cur[1:, :-1] & free[1:, 1:] & free[:-1, :-1]
            dn[:-1, :-1] |= cur[1:, 1:] & free[1:, :-1] & free[:-1, 1:]
            nxt |= dn
            nxt &= free
            nxt &= (dist < 0)
            if not nxt.any():
                return None
            d += 1
            dist[nxt] = d
            cur = nxt

    @staticmethod
    def descend(dist, s, t):
        """Walk the distance field downhill, preferring to keep going straight."""
        ny, nx = dist.shape
        D = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
        x, y = s
        out = [(x, y)]
        last = None
        guard = int(dist[y, x]) + 5
        while (x, y) != tuple(t) and guard > 0:
            guard -= 1
            want = dist[y, x] - 1
            best = None
            for di, (dx, dy) in enumerate(D):
                vx, vy = x + dx, y + dy
                if not (0 <= vx < nx and 0 <= vy < ny):
                    continue
                if dist[vy, vx] != want:
                    continue
                score = 0 if di == last else 1
                if best is None or score < best[0]:
                    best = (score, di, vx, vy)
            if best is None:
                return None
            _, last, x, y = best
            out.append((x, y))
        return out if (x, y) == tuple(t) else None

    @staticmethod
    def clear_line(blk, a, b):
        ny, nx = blk.shape
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        if n == 0:
            return True
        for k in range(n * 2 + 1):
            t = k / float(n * 2)
            i = int(round(a[0] + t * (b[0] - a[0])))
            j = int(round(a[1] + t * (b[1] - a[1])))
            if not (0 <= i < nx and 0 <= j < ny) or blk[j, i]:
                return False
        return True

    def smooth(self, blk, cells):
        """Greedy line-of-sight smoothing: replace staircases with the longest
        straight run that is still clear on the blocked grid.  The reach is
        found by exponential probe then bisection, so a 1400-cell path costs a
        few dozen line tests instead of a million."""
        out = [cells[0]]
        i = 0
        n = len(cells)
        while i < n - 1:
            step = 1
            good = i + 1
            while i + step < n and self.clear_line(blk, cells[i], cells[i + step]):
                good = i + step
                step *= 2
            lo, hi = good, min(i + step, n - 1)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if self.clear_line(blk, cells[i], cells[mid]):
                    lo = mid
                else:
                    hi = mid - 1
            j = max(lo, i + 1)
            out.append(cells[j])
            i = j
        return out

    def search(self, blk, si, ti):
        """A* while it is cheap; wavefront + smoothing once the window is big."""
        ny, nx = blk.shape
        if ny * nx <= 400000:
            return self.astar(blk, si, ti)
        dist = self.wave(blk, ti, si)
        if dist is None:
            return None
        raw = self.descend(dist, si, ti)
        if raw is None:
            return None
        return self.smooth(blk, raw)

    # -------------------------------------------------------------- escape
    def escape(self, pad, layer, trunk_w, rule_min, clr_pad, clr_trk, G, ox, oy):
        """Legal launch points for one terminal, widest legal width first.

        RULE MINIMUM WINS: no candidate is ever narrower than `rule_min`.
        Returns [] and fills self.escape_why when nothing legal exists.
        """
        self.escape_why = []
        if not pad[layer]:
            self.escape_why = ['%s is not on %s.Cu (SMD on the opposite face) - '
                               'a same-layer route can never connect to it'
                               % (pad['ref'], layer)]
            return []
        obs = self.obstacles(layer, pad['net'])
        a = math.radians(pad['ang'])
        ca, sa = math.cos(a), math.sin(a)
        base = [(ca, sa), (-ca, -sa), (-sa, ca), (sa, -ca)]
        diag = []
        for (u1, v1) in base[:2]:
            for (u2, v2) in base[2:]:
                n = math.hypot(u1 + u2, v1 + v2)
                diag.append(((u1 + u2) / n, (v1 + v2) / n))
        dirs = base + diag
        widths = []
        w = trunk_w
        while w > rule_min + 1000:
            widths.append(w)
            w -= 50000
        widths.append(rule_min)
        widths = sorted(set(x for x in widths if x >= rule_min), reverse=True)
        out = []
        blockers = collections.Counter()
        for w in widths:
            for ux, uy in dirs:
                reach = pad['shape'].extent(ux, uy)
                for slack in (150000, 300000, 500000, 800000, 1200000,
                              1800000, 2500000, 3200000, 4000000):
                    ln = reach + max(clr_pad, clr_trk) + w / 2.0 + slack
                    lx = int(round((pad['x'] + ux * ln - ox) / G)) * G + ox
                    ly = int(round((pad['y'] + uy * ln - oy) / G)) * G + oy
                    if (lx < self.ex0 + EDGE_CLR + w / 2.0 or
                            lx > self.ex1 - EDGE_CLR - w / 2.0 or
                            ly < self.ey0 + EDGE_CLR + w / 2.0 or
                            ly > self.ey1 - EDGE_CLR - w / 2.0):
                        blockers['board_edge'] += 1
                        continue
                    bad = None
                    for s in obs:
                        mm_ = self.margin(s, w, clr_pad, clr_trk)
                        bx0, by0, bx1, by1 = s.bbox(mm_)
                        if (min(pad['x'], lx) > bx1 or max(pad['x'], lx) < bx0 or
                                min(pad['y'], ly) > by1 or max(pad['y'], ly) < by0):
                            continue
                        if seg_shape_dist(pad['x'], pad['y'], lx, ly, s) < mm_:
                            bad = s
                            break
                    if bad is not None:
                        blockers[bad.tag] += 1
                        continue
                    if w < trunk_w and not self.point_free(
                            layer, pad['net'], lx, ly, trunk_w, clr_pad, clr_trk, G):
                        blockers['trunk cannot start here'] += 1
                        continue
                    out.append(dict(x=lx, y=ly, w=w,
                                    ln=math.hypot(lx - pad['x'], ly - pad['y']),
                                    dir=(ux, uy), necked=(w < trunk_w)))
                    break
            if out:
                break                 # widest workable width wins
        if not out:
            self.escape_why = ['%s: NO LEGAL ESCAPE at >= %.3f mm; blocked by %s'
                               % (pad['ref'], rule_min / 1e6,
                                  ', '.join('%s (x%d)' % kv for kv in blockers.most_common(4)))]
        return out

    def point_free(self, layer, net, x, y, width, clr_pad, clr_trk, G=50000):
        """Can a track of `width` legally exist centred on this point?"""
        guard = G * 0.75
        for s in self.obstacles(layer, net):
            if s.dist(x, y) < self.margin(s, width, clr_pad, clr_trk) + guard:
                return False
        lim = EDGE_CLR + width / 2.0 + guard
        return (self.ex0 + lim <= x <= self.ex1 - lim and
                self.ey0 + lim <= y <= self.ey1 - lim)

    def worst_gap(self, pad, layer, clr):
        """Diagnostic for a NO LEGAL ESCAPE report: the nearest foreign copper
        and the widest track that could physically leave this pad."""
        best = None
        for s in self.obstacles(layer, pad['net']):
            if s.tag == 'KO':
                continue
            d = s.dist(pad['x'], pad['y']) - pad['shape'].extent(
                *((s.cx - pad['x'], s.cy - pad['y']) if isinstance(s, RR) else (1.0, 0.0)))
            gap = s.dist(pad['x'], pad['y'])
            if best is None or gap < best[1]:
                best = (s.tag, gap)
        return best

    # ---------------------------------------------------------------- emit
    def track(self, net, layer, x0, y0, x1, y1, width):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        if x0 == x1 and y0 == y1:
            return None
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(pcbnew.VECTOR2I(x0, y0))
        t.SetEnd(pcbnew.VECTOR2I(x1, y1))
        t.SetWidth(int(width))
        t.SetLayer(LNAME[layer])
        t.SetNet(self.nets[net])
        self.b.Add(t)
        self.laid.append(t)
        self.shapes[layer].append(SEG(x0, y0, x1, y1, width / 2.0, net, 'track'))
        return t

    def mark(self):
        return len(self.laid), dict((L, len(self.shapes[L])) for L in self.shapes)

    def revert(self, m):
        n, sh = m
        for t in self.laid[n:]:
            self.b.Remove(t)
        self.laid = self.laid[:n]
        for L in sh:
            self.shapes[L] = self.shapes[L][:sh[L]]

    def save(self, path=None):
        self.b.Save(path or self.path)


# --------------------------------------------------------------------------
def simplify(cells, ox, oy, G):
    """Grid cells -> integer nm polyline with collinear runs merged.  The
    conversion is exact: every vertex is ox + i*G, so adjacent segments share
    an identical integer endpoint (PR-5A)."""
    pts = [(ox + i * G, oy + j * G) for i, j in cells]
    keep = [pts[0]]
    for k in range(1, len(pts) - 1):
        ax, ay = keep[-1]
        bx, by = pts[k]
        cx, cy = pts[k + 1]
        if (bx - ax) * (cy - ay) != (by - ay) * (cx - ax):
            keep.append(pts[k])
    keep.append(pts[-1])
    return keep


def connect(qb, net, pa, pb, layer, trunk_w, rule_min, clr_pad, clr_trk, G=50000,
            fine=25000, pad_margin=6000000, log=None, floor_override=None):
    """Route one pad-to-pad connection.

    `floor_override` maps a pad reference to a REDUCED escape floor.  It exists
    only so a feasibility study can measure the trunk past a land pattern that
    the rule cannot legally reach; every override is reported by name, width and
    length so it can never pass unnoticed.  Normal routing leaves it None."""
    fo = floor_override or {}

    def note(s):
        if log is not None:
            log.append(s)

    for G_try in (G, fine):
        ox = qb.ex0 - 2000000
        oy = qb.ey0 - 2000000
        ma = fo.get(pa['ref'], rule_min)
        mb = fo.get(pb['ref'], rule_min)
        ea = qb.escape(pa, layer, trunk_w, ma, clr_pad, clr_trk, G_try, ox, oy)
        if not ea:
            note(qb.escape_why[0])
            return dict(ok=False, reason='NO_LEGAL_ESCAPE', why=qb.escape_why[0], pad=pa['ref'])
        eb = qb.escape(pb, layer, trunk_w, mb, clr_pad, clr_trk, G_try, ox, oy)
        if not eb:
            note(qb.escape_why[0])
            return dict(ok=False, reason='NO_LEGAL_ESCAPE', why=qb.escape_why[0], pad=pb['ref'])
        for margin in (pad_margin, pad_margin * 2, pad_margin * 4):
            for A in ea[:4]:
                for B in eb[:4]:
                    x0 = min(A['x'], B['x'], pa['x'], pb['x']) - margin
                    x1 = max(A['x'], B['x'], pa['x'], pb['x']) + margin
                    y0 = min(A['y'], B['y'], pa['y'], pb['y']) - margin
                    y1 = max(A['y'], B['y'], pa['y'], pb['y']) + margin
                    x0 = max(x0, qb.ex0 - 1000000)
                    y0 = max(y0, qb.ey0 - 1000000)
                    x1 = min(x1, qb.ex1 + 1000000)
                    y1 = min(y1, qb.ey1 + 1000000)
                    ox2 = int(round((x0 - ox) / G_try)) * G_try + ox
                    oy2 = int(round((y0 - oy) / G_try)) * G_try + oy
                    blk = qb.grid(layer, net, trunk_w, clr_pad, clr_trk, ox2, oy2, x1, y1, G_try)
                    si = ((A['x'] - ox2) // G_try, (A['y'] - oy2) // G_try)
                    ti = ((B['x'] - ox2) // G_try, (B['y'] - oy2) // G_try)
                    ny, nx = blk.shape
                    for (ii, jj) in (si, ti):
                        if 0 <= ii < nx and 0 <= jj < ny:
                            blk[jj, ii] = False
                    path = qb.search(blk, si, ti)
                    if path is None:
                        continue
                    pts = simplify(path, ox2, oy2, G_try)
                    segs = []
                    segs.append((pa['x'], pa['y'], A['x'], A['y'], A['w']))
                    for k in range(len(pts) - 1):
                        segs.append((pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], trunk_w))
                    segs.append((pb['x'], pb['y'], B['x'], B['y'], B['w']))
                    total = 0
                    for (sx, sy, exx, eyy, w) in segs:
                        qb.track(net, layer, sx, sy, exx, eyy, w)
                        total += math.hypot(exx - sx, eyy - sy)
                    return dict(ok=True, mm=total / 1e6, segs=len([s for s in segs if
                                                                  s[0] != s[2] or s[1] != s[3]]),
                                grid=G_try / 1e6,
                                necks=[(pa['ref'], A['w'] / 1e6, A['ln'] / 1e6),
                                       (pb['ref'], B['w'] / 1e6, B['ln'] / 1e6)],
                                minw=min(A['w'], B['w'], trunk_w) / 1e6)
    return dict(ok=False, reason='NO_PATH',
                why='no legal corridor at %.3f mm wide from %s to %s at 0.05 or 0.025 mm grid'
                    % (trunk_w / 1e6, pa['ref'], pb['ref']))
