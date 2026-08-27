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
# FBV2-P2-002M / D-258: the layer set is DERIVED FROM THE BOARD, not assumed.
#
# Until now this was `{'F': F_Cu, 'B': B_Cu}` and every obstacle loop was
# `for L in ('F', 'B')`.  That was true while Full Beta v2 was four layers with
# In1 a solid GND reference and In2 reserved for slow power distribution, and
# it is exactly the assumption section 4 asks to be found.  On the six-layer
# stack L3 and L4 are ROUTABLE SIGNAL LAYERS, and a router that cannot see them
# cannot spend the capacity D-258 just bought.
LNAME = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu,
         'I1': pcbnew.In1_Cu, 'I2': pcbnew.In2_Cu,
         'I3': pcbnew.In3_Cu, 'I4': pcbnew.In4_Cu}

# Which layers a router may LAY COPPER ON, by copper-layer count.  The GND
# reference planes are never routable: on four layers In1 is the reference and
# In2 is power-distribution only (a D-249-era rule that predates this task and
# is not being relaxed here); on six layers In1 and In4 are the two solid
# references and In2/In3 are the new signal layers.
ROUTABLE = {4: ('F', 'B'), 6: ('F', 'B', 'I2', 'I3')}
ASTAR_BUDGET = 500000     # directional states
WAVE_BUDGET = 3000        # wavefront steps


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


def _pt_seg(px, py, x0, y0, x1, y1):
    vx, vy = float(x1 - x0), float(y1 - y0)
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / L2))
    return math.hypot(px - (x0 + t * vx), py - (y0 + t * vy))


def _seg_seg(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    """Exact distance between two segments."""
    d1x, d1y = ax1 - ax0, ay1 - ay0
    d2x, d2y = bx1 - bx0, by1 - by0
    den = d1x * d2y - d1y * d2x
    if den != 0:
        ex, ey = bx0 - ax0, by0 - ay0
        t = (ex * d2y - ey * d2x) / float(den)
        u = (ex * d1y - ey * d1x) / float(den)
        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
            return 0.0
    return min(_pt_seg(ax0, ay0, bx0, by0, bx1, by1),
               _pt_seg(ax1, ay1, bx0, by0, bx1, by1),
               _pt_seg(bx0, by0, ax0, ay0, ax1, ay1),
               _pt_seg(bx1, by1, ax0, ay0, ax1, ay1))


def _seg_box(x0, y0, x1, y1, hx, hy):
    """Exact distance from a segment to an axis-aligned box centred at the
    origin.  Both are convex, so the closest pair is a vertex of one against
    the other -- no sampling, no conservative fudge, and therefore no
    false NO-LEGAL-ESCAPE on a pad that is exactly at the limit."""
    def ptbox(px, py):
        return math.hypot(max(abs(px) - hx, 0.0), max(abs(py) - hy, 0.0))
    if ptbox(x0, y0) == 0.0 or ptbox(x1, y1) == 0.0:
        return 0.0
    best = min(ptbox(x0, y0), ptbox(x1, y1))
    for cx, cy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
        d = _pt_seg(cx, cy, x0, y0, x1, y1)
        if d < best:
            best = d
    # segment crossing the box entirely, both endpoints outside
    for (ex0, ey0, ex1, ey1) in ((-hx, -hy, hx, -hy), (hx, -hy, hx, hy),
                                 (hx, hy, -hx, hy), (-hx, hy, -hx, -hy)):
        if _seg_seg(x0, y0, x1, y1, ex0, ey0, ex1, ey1) == 0.0:
            return 0.0
    return best


def seg_shape_dist(x0, y0, x1, y1, shape, step=20000):
    """EXACT distance from a segment centre-line to a shape.

    This used to sample the segment and subtract half a step as a conservative
    lower bound.  That was safe but it lied at the margin: a 0.20 mm track
    leaving a 0.40 mm-pitch WSON pad has EXACTLY 0.20 mm of clearance, and a
    10 um fudge turned a legal escape into NO LEGAL ESCAPE.  Both shapes are
    convex, so the distance is computed closed-form instead."""
    if isinstance(shape, SEG):
        return _seg_seg(x0, y0, x1, y1,
                        shape.x0, shape.y0, shape.x1, shape.y1) - shape.hw
    ca, sa = shape.ca, shape.sa
    ax = (x0 - shape.cx) * ca + (y0 - shape.cy) * sa
    ay = -(x0 - shape.cx) * sa + (y0 - shape.cy) * ca
    bx = (x1 - shape.cx) * ca + (y1 - shape.cy) * sa
    by = -(x1 - shape.cx) * sa + (y1 - shape.cy) * ca
    return _seg_box(ax, ay, bx, by,
                    shape.hx - shape.r, shape.hy - shape.r) - shape.r


# --------------------------------------------------------------------------
class QBoard(object):
    def __init__(self, path):
        self.path = path
        self.b = pcbnew.LoadBoard(path)
        self.nets = {n.GetNetname(): n for n in self.b.GetNetsByName().values()}
        self.pads = {}          # (net, "REF.PAD") -> dict
        ncu = self.b.GetCopperLayerCount()
        self.cu = tuple(L for L in ('F', 'I1', 'I2', 'I3', 'I4', 'B')
                        if self.b.IsLayerEnabled(LNAME[L]))
        self.routable = ROUTABLE.get(ncu, ('F', 'B'))
        self.shapes = dict((L, []) for L in self.cu)
        self.holes = []         # blocks every layer
        self.escape_why = []
        self._scan()
        # GetBoardEdgesBoundingBox() measures to the OUTSIDE of the Edge.Cuts
        # stroke, but copper-to-edge clearance is measured to the LINE ITSELF.
        # Half a line width is 0.025 mm here, and that is exactly the amount by
        # which a track hard against the west edge failed DRC at 0.475 mm.
        bb = self.b.GetBoardEdgesBoundingBox()
        lw = 0
        for d in self.b.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts:
                lw = max(lw, d.GetWidth())
        half = lw // 2
        self.ex0, self.ey0 = bb.GetLeft() + half, bb.GetTop() + half
        self.ex1, self.ey1 = bb.GetRight() - half, bb.GetBottom() - half
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
                for L in self.cu:
                    if p.IsOnLayer(LNAME[L]):
                        self.shapes[L].append(s)
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
            for L in self.cu:
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
            for L in self.cu:
                if t.IsOnLayer(LNAME[L]):
                    self.shapes[L].append(SEG(t.GetStart().x, t.GetStart().y,
                                              t.GetEnd().x, t.GetEnd().y,
                                              t.GetWidth() / 2.0, t.GetNetname(), 'track'))

    _obs_cache = None

    def obstacles(self, layer, net):
        """Memoised: this list is rebuilt from ~2000 shapes and is asked for
        once per point test, which turns an inner loop into an O(n^2) one."""
        key = (layer, net, len(self.shapes[layer]), len(self.holes))
        if self._obs_cache is not None and self._obs_cache[0] == key:
            return self._obs_cache[1]
        out = ([s for s in self.shapes[layer] if s.net != net] +
               [h for h in self.holes if h.net != net])
        self._obs_cache = (key, out)
        return out

    # ------------------------------------------------------------- raster
    wide_nets = frozenset()

    def margin(self, s, width, clr_pad, clr_trk):
        """Per-obstacle clearance.

        A keep-out admits no copper at all.  A pad and a track carry different
        rule clearances.  And `wide_nets` -- the BAT_MAIN-class nets, whose
        .kicad_dru rule demands 0.30 mm track-to-track -- pull the wider figure
        even when the net being routed is an ordinary signal, because that rule
        fires on either side of the pair."""
        if s.net is None and s.tag == 'KO':
            return width / 2.0
        # A NOTE ON WIDE-NET PADS, AND WHY THE BUMP IS *NOT* APPLIED HERE.
        #
        # `BAT_MAIN routed clearance` is a rule about the NET and it fires on
        # either side of the pair, so on the face of it a control track passing
        # a BAT_MAIN PAD owes it 0.300 mm just as it owes a BAT_MAIN track
        # 0.300 mm, and FBV2-P2-002N tried exactly that.  It is wrong, and the
        # board says so: raising every wide-net PAD to 0.300 mm immediately
        # sealed `U18.8` and `U18.9` - the two D-249-ruled Kelvin taps that must
        # leave an MSOP-10 pin field straight past R75's own pads - and both
        # came back NO_LEGAL_ESCAPE.  Those taps route legally today at 0.150 mm
        # under the pad-escape necking block, a LATER and more specific rule
        # than the class clearance, so DRC does not in fact demand 0.300 mm
        # there.  A router-side bump cannot see which corridor rule governs a
        # given pair, so it would have to over-apply - and over-applying a
        # clearance is how a legal escape becomes NO_LEGAL_ESCAPE.  The gate's
        # own DRC stays the authority: a route that really does violate 0.300 mm
        # beside a wide-net pad is rejected there, per connection, by name.
        if not isinstance(s, SEG):
            return width / 2.0 + clr_pad
        c = clr_trk
        if s.net in self.wide_nets and c < 300000:
            c = 300000
        return width / 2.0 + c

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
        # SEARCH CEILING.  A* that cannot reach its target explores the entire
        # reachable region, and on a board where F.Cu is almost empty that is
        # millions of directional states for a connection the retry queue is
        # about to set aside anyway.  Giving up is the same answer, sooner.
        budget = ASTAR_BUDGET
        while pq:
            budget -= 1
            if budget <= 0:
                return None
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
        steps = WAVE_BUDGET
        while True:
            steps -= 1
            if steps <= 0:
                return None
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
    def escape(self, pad, layer, trunk_w, rule_min, clr_pad, clr_trk, G, ox, oy,
               prefer=None):
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
        if prefer is not None:
            # ESCAPE TOWARDS WHERE YOU ARE GOING.  Leaving a corner pin along
            # its long axis is the textbook answer and usually right, but on
            # U18.10 it means escaping NORTH and then walking back around the
            # package to reach R76 in the south - straight across the lane
            # U18.9 needs.  Ordering the candidate directions by how well they
            # point at the destination costs nothing and removes that whole
            # class of self-inflicted blockage.
            px_, py_ = prefer
            n = math.hypot(px_, py_)
            if n > 0:
                px_, py_ = px_ / n, py_ / n
                dirs = sorted(dirs, key=lambda d: -(d[0] * px_ + d[1] * py_))
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

    # ------------------------------------------------------- flared escape
    def clearance_at(self, layer, net, x, y, clr_pad, clr_trk):
        """Largest track half-width that could be centred on this point."""
        best = 1e18
        for sh in self.obstacles(layer, net):
            if sh.net is None and sh.tag == 'KO':
                d = sh.dist(x, y)
            else:
                d = sh.dist(x, y) - (clr_trk if isinstance(sh, SEG) else clr_pad)
            if d < best:
                best = d
        for lim, v in ((self.ex0 + EDGE_CLR, x - (self.ex0 + EDGE_CLR)),
                       (self.ex1 - EDGE_CLR, (self.ex1 - EDGE_CLR) - x),
                       (self.ey0 + EDGE_CLR, y - (self.ey0 + EDGE_CLR)),
                       (self.ey1 - EDGE_CLR, (self.ey1 - EDGE_CLR) - y)):
            if v < best:
                best = v
        return best

    def nearest_free(self, layer, net, x, y, width, clr_pad, clr_trk, G,
                     span=12000000, region=None):
        """Nearest grid point to (x, y) on which a track of `width` may be
        centred.  Used to find where a flare can take its next step up."""
        ox = int(round((x - span) / G)) * G
        oy = int(round((y - span) / G)) * G
        blk = self.grid(layer, net, width, clr_pad, clr_trk,
                        ox, oy, x + span, y + span, G)
        ny, nx = blk.shape
        ci = int((x - ox) // G)
        cj = int((y - oy) // G)
        best = None
        for r in range(0, int(span / G)):
            found = False
            for dj in range(-r, r + 1):
                for di in range(-r, r + 1):
                    if max(abs(di), abs(dj)) != r:
                        continue
                    ii, jj = ci + di, cj + dj
                    if not (0 <= ii < nx and 0 <= jj < ny):
                        continue
                    if blk[jj, ii]:
                        continue
                    if region is not None:
                        rmask, rox, roy, rG = region
                        ri = int((ox + ii * G - rox) // rG)
                        rj = int((oy + jj * G - roy) // rG)
                        rny, rnx = rmask.shape
                        if not (0 <= ri < rnx and 0 <= rj < rny and rmask[rj, ri]):
                            continue
                    d = (di * di + dj * dj)
                    if best is None or d < best[0]:
                        best = (d, ox + ii * G, oy + jj * G)
                    found = True
            if found and best is not None:
                return (best[1], best[2])
        return None

    def via_site(self, near, far, net, esc, width, via_dia, clr_pad, clr_trk,
                 G, span=8000000, via_drill=0, hole_clr=250000):
        """PR-45.  THE FIRST POINT A VIA CAN SIT ON THAT THE ESCAPE CAN REACH.

        connect_hop used to pick its via site with nearest_free(), which
        answers "where is the closest point a via fits" - a question about
        GEOMETRY.  The question that matters is "where is the closest point a
        via fits THAT THIS PAD CAN GET TO", which is a question about
        REACHABILITY, and beside a fine-pitch pin in a congested field the two
        answers are not the same place.

        `U18.10` is the case that exposed it.  It is the LTC4368 GATE output on
        the corner of an MSOP-10 whose 0.50 mm pitch leaves ONE legal escape
        direction.  A 0.60 mm via does not fit at that escape point, so
        nearest_free() went looking and returned a site 2.30 mm away - on the
        far side of the copper the pin is trying to escape past.  The walk to
        it then failed, the hop was abandoned, and D-256's planned F.Cu escape
        for LTC_GATE could never be taken.  The F.Cu corridor was never the
        problem: measured, F.Cu over that margin is 0.00 mm2 occupied and the
        run itself was never attempted.

        So: flood the near layer at TRACK width from the escape point, and take
        the nearest cell of that reachable region which also admits the VIA on
        both layers.  A site returned here is reachable by construction, so the
        walk that follows cannot fail for want of a corridor.
        """
        x0, y0 = esc['x'] - span, esc['y'] - span
        x1, y1 = esc['x'] + span, esc['y'] + span
        reach = self.free_region(near, net, width, clr_pad, clr_trk, G,
                                 (esc['x'], esc['y']), x0, y0, x1, y1)
        if reach is None:
            return None
        mask, ox, oy, g = reach
        bn = self.grid(near, net, via_dia, clr_pad, clr_trk, ox, oy, x1, y1, g)
        bf = self.grid(far, net, via_dia, clr_pad, clr_trk, ox, oy, x1, y1, g)
        ny = min(mask.shape[0], bn.shape[0], bf.shape[0])
        nx = min(mask.shape[1], bn.shape[1], bf.shape[1])
        good = mask[:ny, :nx] & ~bn[:ny, :nx] & ~bf[:ny, :nx]
        if not good.any():
            return None
        jj, ii = np.nonzero(good)
        ci = (esc['x'] - ox) / float(g)
        cj = (esc['y'] - oy) / float(g)
        d = (ii - ci) ** 2 + (jj - cj) ** 2
        # HOLE-TO-HOLE IS NOT A COPPER RULE, so the clearance grids above do
        # not see it: they test whether a via's PAD clears other copper, and
        # `min_hole_to_hole` is a drill-to-drill spacing the fabricator needs
        # between two barrels.  The first D-256 screen put the `U18.10 -> Q3.4`
        # escape via on a site that was clean on both layers and still came
        # back from DRC as `hole_to_hole: 1`.  Rejecting those sites here costs
        # one distance test per candidate and saves a whole gated connection.
        if via_drill:
            hx = np.array([h.cx for h in self.holes], dtype=float) \
                if self.holes else np.zeros(0)
            hy = np.array([h.cy for h in self.holes], dtype=float) \
                if self.holes else np.zeros(0)
            hr = np.array([max(h.hx, h.hy) for h in self.holes], dtype=float) \
                if self.holes else np.zeros(0)
            if hx.size:
                order = np.argsort(d)
                for k in order:
                    px = ox + ii[k] * g
                    py = oy + jj[k] * g
                    need = hr + (via_drill / 2.0) + hole_clr
                    if np.all(np.hypot(hx - px, hy - py) >= need):
                        return (int(px), int(py))
                return None
        k = int(np.argmin(d))
        return (int(ox + ii[k] * g), int(oy + jj[k] * g))

    def free_region(self, layer, net, width, clr_pad, clr_trk, G,
                    seed, x0, y0, x1, y1):
        """Flood-fill the trunk-width-free space from `seed`.

        A point that admits the trunk width is not necessarily a point the
        trunk can REACH.  This is the difference between the two, computed
        once and reused."""
        ox = int(round((x0) / G)) * G
        oy = int(round((y0) / G)) * G
        blk = self.grid(layer, net, width, clr_pad, clr_trk, ox, oy, x1, y1, G)
        ny, nx = blk.shape
        si = int((seed[0] - ox) // G)
        sj = int((seed[1] - oy) // G)
        if not (0 <= si < nx and 0 <= sj < ny):
            return None
        free = ~blk
        free[sj, si] = True
        seen = np.zeros((ny, nx), dtype=bool)
        seen[sj, si] = True
        cur = seen.copy()
        while cur.any():
            nxt = np.zeros((ny, nx), dtype=bool)
            nxt[1:, :] |= cur[:-1, :]
            nxt[:-1, :] |= cur[1:, :]
            nxt[:, 1:] |= cur[:, :-1]
            nxt[:, :-1] |= cur[:, 1:]
            nxt &= free
            nxt &= ~seen
            seen |= nxt
            cur = nxt
        return (seen, ox, oy, G)

    def flare(self, net, pad, layer, trunk_w, neck_w, clr_pad, clr_trk, G,
              ladder=(300000, 400000, 600000, 800000, 1000000, 1200000),
              region=None):
        """ROUTED flare out of a fine-pitch high-current pad.

        Section 6: the neck must be the shortest possible and must flare
        outward immediately.  A straight ray cannot do that here -- west of
        U11.2 the corridor pinches again at 1.5 mm -- so the flare is a short
        chain of grid routes at increasing width, each one ending at the
        nearest point where the NEXT width becomes legal.

        The analytic neck out of the pad carries no grid guard band, because it
        is analytic; every routed step does, because it is grid-derived.

        Emits copper.  Returns a profile dict, or None.
        """
        ox = self.ex0 - 2000000
        oy = self.ey0 - 2000000
        e = self.escape(pad, layer, neck_w, neck_w, clr_pad, clr_trk, G, ox, oy)
        if not e:
            return None
        # SHORTEN THE NECK.  escape() launches clear of the package with slack to
        # spare, which is right for a trunk but wrong here: section 6 wants the
        # shortest neck that exists.  Walk back along the same direction to the
        # first grid point that still admits neck_w.
        ux = e[0]['x'] - pad['x']
        uy = e[0]['y'] - pad['y']
        L0 = math.hypot(ux, uy)
        cx, cy = e[0]['x'], e[0]['y']
        if L0 > 0:
            ux, uy = ux / L0, uy / L0
            obs = self.obstacles(layer, pad['net'])
            k = 1
            while k * 25000 <= L0:
                d = k * 25000
                px = int(round((pad['x'] + ux * d) / G)) * G
                py = int(round((pad['y'] + uy * d) / G)) * G
                if self.point_free(layer, pad['net'], px, py, neck_w,
                                   clr_pad, clr_trk, G):
                    bad = False
                    for sh in obs:
                        m = self.margin(sh, neck_w, clr_pad, clr_trk)
                        if seg_shape_dist(pad['x'], pad['y'], px, py, sh) < m:
                            bad = True
                            break
                    if not bad:
                        cx, cy = px, py
                        break
                k += 1
        segs = [(pad['x'], pad['y'], cx, cy, neck_w)]
        levels = [w for w in ladder if neck_w < w < trunk_w] + [trunk_w]
        cur_w = neck_w
        for w in levels:
            if self.point_free(layer, net, cx, cy, w, clr_pad, clr_trk, G):
                cur_w = w
                continue
            # REACHABILITY AT EVERY RUNG.  Applying it only to the final width
            # lets the earlier steps walk into a pocket that admits the width
            # but has no corridor out of it; the flare then succeeds and the
            # trunk is stranded.  Ask, at every rung, for the nearest point of
            # that width that the DESTINATION can actually reach.
            reg = region.get(w) if isinstance(region, dict) else (
                region if (region is not None and w == levels[-1]) else None)
            tgt = self.nearest_free(layer, net, cx, cy, w, clr_pad, clr_trk, G,
                                    region=reg)
            if tgt is None:
                return None
            blk = self.grid(layer, net, cur_w, clr_pad, clr_trk,
                            min(cx, tgt[0]) - 6000000, min(cy, tgt[1]) - 6000000,
                            max(cx, tgt[0]) + 6000000, max(cy, tgt[1]) + 6000000, G)
            ny, nx = blk.shape
            gx0 = int(round((min(cx, tgt[0]) - 6000000 - ox) / G)) * G + ox
            gy0 = int(round((min(cy, tgt[1]) - 6000000 - oy) / G)) * G + oy
            blk = self.grid(layer, net, cur_w, clr_pad, clr_trk, gx0, gy0,
                            max(cx, tgt[0]) + 6000000, max(cy, tgt[1]) + 6000000, G)
            ny, nx = blk.shape
            si = ((cx - gx0) // G, (cy - gy0) // G)
            ti = ((tgt[0] - gx0) // G, (tgt[1] - gy0) // G)
            for (ii, jj) in (si, ti):
                if 0 <= ii < nx and 0 <= jj < ny:
                    blk[jj, ii] = False
            path = self.search(blk, si, ti)
            if path is None:
                return None
            pts = simplify(path, gx0, gy0, G)
            for k in range(len(pts) - 1):
                segs.append((pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], cur_w))
            cx, cy = tgt
            cur_w = w
        for (x0, y0, x1, y1, w) in segs:
            self.track(net, layer, x0, y0, x1, y1, w)
        L = lambda a: math.hypot(a[2] - a[0], a[3] - a[1])
        return dict(x=cx, y=cy,
                    segs=[(round(L(a) / 1e6, 4), a[4] / 1e6) for a in segs],
                    neck_len=sum(L(a) for a in segs if a[4] <= neck_w) / 1e6,
                    sub_trunk=sum(L(a) for a in segs if a[4] < trunk_w) / 1e6,
                    total=sum(L(a) for a in segs) / 1e6,
                    bbox=(min(min(a[0], a[2]) for a in segs),
                          min(min(a[1], a[3]) for a in segs),
                          max(max(a[0], a[2]) for a in segs),
                          max(max(a[1], a[3]) for a in segs)))

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

    def via(self, net, x, y, dia=800000, drill=400000):
        """Through via on every copper layer.  0.40 mm drill satisfies the
        POWER-class hole rule; (0.80-0.40)/2 = 0.20 mm annular ring satisfies
        the 0.125 mm floor."""
        x, y = int(x), int(y)
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(x, y))
        v.SetWidth(int(dia))
        v.SetDrill(int(drill))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.nets[net])
        self.b.Add(v)
        self.laid.append(v)
        # A THROUGH via is copper on every layer it passes, and on a six-layer
        # board that is six, not two.  Missing the inner four is how an inner
        # route would have been laid straight through a via barrel.
        for L in self.cu:
            self.shapes[L].append(RR(x, y, dia / 2.0, dia / 2.0, dia / 2.0,
                                     0, net, 'via'))
        self.holes.append(RR(x, y, drill / 2.0, drill / 2.0, drill / 2.0,
                             0, net, 'via/hole'))
        return v

    def mark(self):
        return (len(self.laid), dict((L, len(self.shapes[L])) for L in self.shapes),
                len(self.holes))

    def revert(self, m):
        n, sh, nh = m
        for t in self.laid[n:]:
            self.b.Remove(t)
        self.laid = self.laid[:n]
        for L in sh:
            self.shapes[L] = self.shapes[L][:sh[L]]
        self.holes = self.holes[:nh]

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
        # SEARCH BUDGET.  Three window sizes against four escape candidates a
        # side is forty-eight whole-board wavefronts for a connection that is
        # going to fail anyway, and a failing connection is exactly what the
        # retry queue needs to get through quickly.  Two and two is eight.
        for margin in (pad_margin, pad_margin * 3):
            for A in ea[:2]:
                for B in eb[:2]:
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


def connect_role(qb, net, pa, pb, layer, trunk_w, clr_pad, clr_trk,
                 neck=None, G=50000, fine=25000, pad_margin=6000000):
    """Route one connection with PATH-ROLE widths.

    `neck` maps a pad reference to the width its land pattern may legally take
    when it is below the trunk width.  Where a pad appears in `neck`, the escape
    is FLARED: narrow at the pad, widening as soon as the surrounding copper
    allows, and the exact length spent at each width is returned so it can be
    documented rather than assumed.
    """
    neck = neck or {}
    for G_try in (G, fine):
        ox = qb.ex0 - 2000000
        oy = qb.ey0 - 2000000
        ends = []
        for p in (pa, pb):
            nw = neck.get(p['ref'])
            if p.get('anchor'):
                # A junction on copper this net already owns.  There is nothing
                # to escape FROM: the point itself is the launch.
                ends.append(dict(kind='plain', x=p['x'], y=p['y'], w=trunk_w,
                                 ln=0, pad=p))
            elif nw is None or nw >= trunk_w:
                other = pb if p is pa else pa
                e = qb.escape(p, layer, trunk_w, trunk_w, clr_pad, clr_trk,
                              G_try, ox, oy,
                              prefer=(other['x'] - p['x'], other['y'] - p['y']))
                if not e:
                    return dict(ok=False, reason='NO_LEGAL_ESCAPE',
                                why=qb.escape_why[0], pad=p['ref'])
                ends.append(dict(kind='plain', x=e[0]['x'], y=e[0]['y'],
                                 w=e[0]['w'], ln=e[0]['ln'], pad=p))
            else:
                f = qb.flare(p, layer, trunk_w, nw, clr_pad, clr_trk, G_try)
                if f is None:
                    return dict(ok=False, reason='NO_FLARE',
                                why='%s: no flared escape from %.3f mm to %.3f mm'
                                    % (p['ref'], nw / 1e6, trunk_w / 1e6),
                                pad=p['ref'])
                ends.append(dict(kind='flare', pad=p, **f))
        A, B = ends
        for margin in (pad_margin, pad_margin * 2, pad_margin * 4):
            x0 = min(A['x'], B['x'], pa['x'], pb['x']) - margin
            x1 = max(A['x'], B['x'], pa['x'], pb['x']) + margin
            y0 = min(A['y'], B['y'], pa['y'], pb['y']) - margin
            y1 = max(A['y'], B['y'], pa['y'], pb['y']) + margin
            x0 = max(x0, qb.ex0 - 1000000); y0 = max(y0, qb.ey0 - 1000000)
            x1 = min(x1, qb.ex1 + 1000000); y1 = min(y1, qb.ey1 + 1000000)
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
            total = 0
            prof = []
            for E in ends:
                p = E['pad']
                if E['kind'] == 'plain':
                    if not p.get('anchor'):
                        qb.track(net, layer, p['x'], p['y'], E['x'], E['y'], E['w'])
                        total += E['ln']
                        prof.append((p['ref'], E['w'] / 1e6, E['ln'] / 1e6))
                else:
                    ux, uy = E['dir']
                    for (d0, d1, w) in E['segs']:
                        sx = p['x'] + ux * d0 if d0 else p['x']
                        sy = p['y'] + uy * d0 if d0 else p['y']
                        exx, eyy = p['x'] + ux * d1, p['y'] + uy * d1
                        if abs(d1 - E['total']) < 1:
                            exx, eyy = E['x'], E['y']
                        qb.track(net, layer, sx, sy, exx, eyy, w)
                        total += math.hypot(exx - sx, eyy - sy)
                        prof.append((p['ref'], w / 1e6,
                                     math.hypot(exx - sx, eyy - sy) / 1e6))
            for k in range(len(pts) - 1):
                qb.track(net, layer, pts[k][0], pts[k][1],
                         pts[k + 1][0], pts[k + 1][1], trunk_w)
                total += math.hypot(pts[k + 1][0] - pts[k][0],
                                    pts[k + 1][1] - pts[k][1])
            return dict(ok=True, mm=total / 1e6, grid=G_try / 1e6, profile=prof,
                        trunk_mm=trunk_w / 1e6,
                        minw=min([w for _, w, _ in prof] + [trunk_w / 1e6]))
    return dict(ok=False, reason='NO_PATH',
                why='no legal corridor at %.3f mm from %s to %s at 0.05 or 0.025 mm'
                    % (trunk_w / 1e6, pa['ref'], pb['ref']))


def connect_hop(qb, net, pa, pb, width, clr_pad, clr_trk, near='B', far=None,
                G=50000, fine=25000, via_dia=800000, via_drill=400000):
    """Route pad-to-pad with a layer hop: a short escape on `near` at each pad,
    a through via, and the run itself on `far`.

    Returns the same shape as connect_role plus the via count, so a hop can
    never be reported as if it were a flat route.

    D-258: `far` now DEFAULTS TO EVERY ROUTABLE LAYER THAT IS NOT `near`, tried
    in order.  On four layers that is F.Cu and the behaviour is exactly what it
    always was; on the six-layer stack it is F.Cu, In2.Cu and In3.Cu, so a net
    that cannot find an F.Cu corridor gets offered the two new internal signal
    layers instead of being told there is no corridor at all.  Spending the
    capacity D-258 bought is the whole point of buying it.
    """
    if far is None:
        far = [L for L in qb.routable if L != near]
        # D-258 section 2: HIGH-CURRENT BATTERY COPPER STAYS ON OUTER 1 oz.
        # The inner layers are 0.5 oz, where 1.5 A at a 10 K rise needs 2.73 mm
        # by the .kicad_dru's own arithmetic - which defeats the point of going
        # there - and the board already carries `BAT_MAIN is outer-layer only`
        # as a rule.  Offering In2/In3 to a wide net produced exactly that
        # rejection, three times, on `BAT_SENSE Q3.5 -> (node)`.  The new
        # capacity is for the CONTROL nets; the trunk was never short of a
        # layer, it was short of a lane.
        if net in qb.wide_nets:
            far = [L for L in far if L in ('F', 'B')]
    if not isinstance(far, (list, tuple)):
        far = [far]
    if len(far) > 1:
        best = None
        for L in far:
            r = connect_hop(qb, net, pa, pb, width, clr_pad, clr_trk,
                            near=near, far=L, G=G, fine=fine,
                            via_dia=via_dia, via_drill=via_drill)
            if r['ok']:
                return r
            best = best or r
        return best
    far = far[0]
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    # PR-46: connect_hop used to report EVERY failure as
    # 'NO_PATH: no F corridor', including the two that have nothing to do with
    # the far layer - no reachable via site, and no near-layer walk to it.  The
    # far-layer run is the LAST thing it tries, so a hop that died before ever
    # reaching it was still being reported as an F.Cu capacity failure.  That
    # misreport is what made the layer option look exhausted when it had not
    # been exercised.  The real reason is carried out now.
    fail = None
    for G_try in (G, fine):
        ends = []
        ok = True
        for p in (pa, pb):
            other = pb if p is pa else pa
            e = qb.escape(p, near, width, width, clr_pad, clr_trk, G_try, ox, oy,
                          prefer=(other['x'] - p['x'], other['y'] - p['y']))
            if not e:
                return dict(ok=False, reason='NO_LEGAL_ESCAPE',
                            why=qb.escape_why[0], pad=p['ref'])
            # The via must clear BOTH layers.  Beside a fine-pitch pad there is
            # usually no room for it right at the escape point, so walk out on
            # the near layer to the closest point that can hold one instead of
            # giving up.
            def free_everywhere(x, y):
                """A THROUGH via is copper on every layer of the stack.
                Checking only `near` and `far` was harmless while those WERE
                the stack; on six layers it let a hop drop its via straight
                onto another net's inner copper, and DRC answered
                `shorting_items`.  The via has to clear the board, not the two
                layers the hop happens to be thinking about."""
                return all(qb.point_free(L, net, x, y, via_dia,
                                         clr_pad, clr_trk, G_try)
                           for L in qb.cu)

            cand = None
            for c in e[:6]:
                if free_everywhere(c['x'], c['y']):
                    cand = dict(c)
                    cand['walk'] = None
                    break
            if cand is None:
                # PR-45: ask for the nearest via site the escape can REACH,
                # not merely the nearest one that exists.  See QBoard.via_site.
                site = None
                for c in e[:6]:
                    st = qb.via_site(near, far, net, c, width, via_dia,
                                     clr_pad, clr_trk, G_try,
                                     via_drill=via_drill)
                    if st is not None and free_everywhere(st[0], st[1]):
                        site = st
                        break
                if site is None:
                    fail = dict(ok=False, reason='NO_VIA_SITE',
                                why='%s: no via site of %.2f mm reachable on %s'
                                    % (p['ref'], via_dia / 1e6, near),
                                pad=p['ref'])
                    ok = False
                    break
                cand = dict(c)
                cand['walk'] = site
            ends.append((p, cand))
        if not ok:
            continue
        m = qb.mark()
        total = 0.0
        for (p, c) in ends:
            qb.track(net, near, p['x'], p['y'], c['x'], c['y'], c['w'])
            total += c['ln']
            if c.get('walk'):
                blkn = qb.grid(near, net, c['w'], clr_pad, clr_trk,
                               min(c['x'], c['walk'][0]) - 6000000,
                               min(c['y'], c['walk'][1]) - 6000000,
                               max(c['x'], c['walk'][0]) + 6000000,
                               max(c['y'], c['walk'][1]) + 6000000, G_try)
                gx0 = min(c['x'], c['walk'][0]) - 6000000
                gy0 = min(c['y'], c['walk'][1]) - 6000000
                si = ((c['x'] - gx0) // G_try, (c['y'] - gy0) // G_try)
                ti = ((c['walk'][0] - gx0) // G_try, (c['walk'][1] - gy0) // G_try)
                nyy, nxx = blkn.shape
                for (ii, jj) in (si, ti):
                    if 0 <= ii < nxx and 0 <= jj < nyy:
                        blkn[jj, ii] = False
                pth = qb.search(blkn, si, ti)
                if pth is None:
                    fail = dict(ok=False, reason='NO_NEAR_WALK',
                                why='%s: no %s corridor from the escape to its '
                                    'via site' % (p['ref'], near), pad=p['ref'])
                    ok = False
                    break
                pp = simplify(pth, int(gx0), int(gy0), G_try)
                for k in range(len(pp) - 1):
                    qb.track(net, near, pp[k][0], pp[k][1], pp[k + 1][0], pp[k + 1][1], c['w'])
                    total += math.hypot(pp[k + 1][0] - pp[k][0], pp[k + 1][1] - pp[k][1])
                c['x'], c['y'] = c['walk']
            qb.via(net, c['x'], c['y'], via_dia, via_drill)
        if not ok:
            qb.revert(m)
            continue
        A, B = ends[0][1], ends[1][1]
        margin = 8000000
        x0 = max(min(A['x'], B['x']) - margin, qb.ex0 - 1000000)
        y0 = max(min(A['y'], B['y']) - margin, qb.ey0 - 1000000)
        x1 = min(max(A['x'], B['x']) + margin, qb.ex1 + 1000000)
        y1 = min(max(A['y'], B['y']) + margin, qb.ey1 + 1000000)
        ox2 = int(round((x0 - ox) / G_try)) * G_try + ox
        oy2 = int(round((y0 - oy) / G_try)) * G_try + oy
        blk = qb.grid(far, net, width, clr_pad, clr_trk, ox2, oy2, x1, y1, G_try)
        si = ((A['x'] - ox2) // G_try, (A['y'] - oy2) // G_try)
        ti = ((B['x'] - ox2) // G_try, (B['y'] - oy2) // G_try)
        ny, nx = blk.shape
        for (ii, jj) in (si, ti):
            if 0 <= ii < nx and 0 <= jj < ny:
                blk[jj, ii] = False
        path = qb.search(blk, si, ti)
        if path is None:
            qb.revert(m)
            continue
        pts = simplify(path, ox2, oy2, G_try)
        for k in range(len(pts) - 1):
            qb.track(net, far, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], width)
            total += math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
        return dict(ok=True, mm=total / 1e6, grid=G_try / 1e6, vias=2,
                    trunk_mm=width / 1e6, minw=width / 1e6, layer=far,
                    via_dia=via_dia / 1e6, via_drill=via_drill / 1e6,
                    via_xy=[(round(ends[0][1]['x'] / 1e6, 3),
                             round(ends[0][1]['y'] / 1e6, 3)),
                            (round(ends[1][1]['x'] / 1e6, 3),
                             round(ends[1][1]['y'] / 1e6, 3))],
                    profile=[(pa['ref'], ends[0][1]['w'] / 1e6, ends[0][1]['ln'] / 1e6),
                             (pb['ref'], ends[1][1]['w'] / 1e6, ends[1][1]['ln'] / 1e6)])
    if fail is not None:
        return fail
    return dict(ok=False, reason='NO_PATH',
                why='no %s corridor at %.3f mm from %s to %s'
                    % (far, width / 1e6, pa['ref'], pb['ref']))


def connect_pofv(qb, net, pa, pb, width, clr_pad, clr_trk, inner='I2',
                 near='B', G=50000, fine=25000,
                 via_dia=350000, via_drill=200000):
    """PR-47: escape a pad that CANNOT escape, by putting the via IN it.

    `Q3.3` is the case this exists for.  FBV2-P2-002L measured it as having NO
    LEGAL ESCAPE at 0.25, 0.20 or 0.15 mm - blocked by `Q3.2` and `Q3.4`, its
    own neighbours on a 1.27 mm SOIC-8 row where `Q3_CS` owns pins 1/3 and
    `LTC_GATE` owns 2/4 and there is one B.Cu slot.  Both D-257 via geometries
    failed the same way, and they had to: a via needs a landing site, a landing
    site has to be REACHED from the pad, and no via size helps a pad that
    cannot emit copper in any direction.

    So the via goes INSIDE the pad.  D-258 authorises a filled-and-capped
    ordinary THROUGH via-in-pad (POFV) for exactly this pad - not a blind via,
    not a buried via, not a laser microvia - and the route leaves on one of the
    six-layer stack's new internal signal layers, where the south-row conflict
    does not exist.  The other end takes an ordinary external via, because it
    has four escape directions and does not need the premium process.

    THE FABRICATION PROCESS IS NOT OPTIONAL AND IT IS NOT IMPLIED BY THE
    GERBERS.  A via inside a pad that is merely tented, mask-plugged or left
    open wicks solder off the joint.  See docs FABRICATION_NOTES: this via must
    be ordered as PLATED OVER FILLED VIA.
    """
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    if inner not in qb.shapes:
        return dict(ok=False, reason='NO_LAYER',
                    why='%s is not a copper layer on this board' % inner)
    # ---- pad A: the via sits in the pad, so there is no escape to find -----
    ax, ay = pa['x'], pa['y']
    half = min(pa['hx'], pa['hy'])
    if via_dia / 2.0 > half:
        return dict(ok=False, reason='POFV_TOO_LARGE',
                    why='%s: %.2f mm via does not fit inside a %.2f mm pad'
                        % (pa['ref'], via_dia / 1e6, 2 * half / 1e6))
    # hole-to-hole is a drill rule the copper grids cannot see
    for h in qb.holes:
        if h.net == net:
            continue
        need = max(h.hx, h.hy) + via_drill / 2.0 + 250000
        if math.hypot(h.cx - ax, h.cy - ay) < need:
            return dict(ok=False, reason='POFV_HOLE_CLEARANCE',
                        why='%s: via-in-pad too close to an existing hole'
                            % pa['ref'])
    # The via is inside its own pad on the pad's own layer, but it is a THROUGH
    # via and therefore copper on the other five as well - including whatever
    # sits at the same coordinates on the opposite face.
    for L in qb.cu:
        if L == near:
            continue
        if not qb.point_free(L, net, ax, ay, via_dia, clr_pad, clr_trk, fine):
            return dict(ok=False, reason='POFV_LAYER_CONFLICT',
                        why='%s: via-in-pad is not clear on %s' % (pa['ref'], L))
    for G_try in (G, fine):
        # ---- pad B: an ordinary external escape and a reachable via -------
        other = pa
        e = qb.escape(pb, near, width, width, clr_pad, clr_trk, G_try, ox, oy,
                      prefer=(other['x'] - pb['x'], other['y'] - pb['y']))
        if not e:
            return dict(ok=False, reason='NO_LEGAL_ESCAPE',
                        why=qb.escape_why[0], pad=pb['ref'])
        def all_layers_free(x, y):
            """A THROUGH via is copper on EVERY layer, and the first six-layer
            POFV attempt proved why that must be checked on every one of them:
            checking only B.Cu and the inner run layer put a via through an
            F.Cu pad and DRC returned
            `shorting_items: Q3_CS and BAT_SENSE`.  A via that clears the two
            layers you were thinking about is not a via that clears the board."""
            return all(qb.point_free(L, net, x, y, via_dia,
                                     clr_pad, clr_trk, G_try)
                       for L in qb.cu)

        site = None
        cb = None
        for c in e[:6]:
            if all_layers_free(c['x'], c['y']):
                site, cb = (c['x'], c['y']), c
                break
        if site is None:
            for c in e[:6]:
                st = qb.via_site(near, inner, net, c, width, via_dia,
                                 clr_pad, clr_trk, G_try, via_drill=via_drill)
                if st and all_layers_free(st[0], st[1]):
                    site, cb = st, c
                    break
        if site is None:
            return dict(ok=False, reason='NO_VIA_SITE',
                        why='%s: no via site of %.2f mm reachable on %s'
                            % (pb['ref'], via_dia / 1e6, near), pad=pb['ref'])
        m = qb.mark()
        total = 0.0
        qb.track(net, near, pb['x'], pb['y'], cb['x'], cb['y'], cb['w'])
        total += cb['ln']
        if (cb['x'], cb['y']) != site:
            gx0 = min(cb['x'], site[0]) - 6000000
            gy0 = min(cb['y'], site[1]) - 6000000
            blkn = qb.grid(near, net, cb['w'], clr_pad, clr_trk, gx0, gy0,
                           max(cb['x'], site[0]) + 6000000,
                           max(cb['y'], site[1]) + 6000000, G_try)
            si = ((cb['x'] - gx0) // G_try, (cb['y'] - gy0) // G_try)
            ti = ((site[0] - gx0) // G_try, (site[1] - gy0) // G_try)
            nyy, nxx = blkn.shape
            for (ii, jj) in (si, ti):
                if 0 <= ii < nxx and 0 <= jj < nyy:
                    blkn[jj, ii] = False
            pth = qb.search(blkn, si, ti)
            if pth is None:
                qb.revert(m)
                continue
            pp = simplify(pth, int(gx0), int(gy0), G_try)
            for k in range(len(pp) - 1):
                qb.track(net, near, pp[k][0], pp[k][1],
                         pp[k + 1][0], pp[k + 1][1], cb['w'])
                total += math.hypot(pp[k + 1][0] - pp[k][0],
                                    pp[k + 1][1] - pp[k][1])
        qb.via(net, site[0], site[1], via_dia, via_drill)
        qb.via(net, ax, ay, via_dia, via_drill)          # <- the POFV
        # ---- the run itself, on the internal signal layer -----------------
        margin = 8000000
        x0 = max(min(ax, site[0]) - margin, qb.ex0 - 1000000)
        y0 = max(min(ay, site[1]) - margin, qb.ey0 - 1000000)
        x1 = min(max(ax, site[0]) + margin, qb.ex1 + 1000000)
        y1 = min(max(ay, site[1]) + margin, qb.ey1 + 1000000)
        ox2 = int(round((x0 - ox) / G_try)) * G_try + ox
        oy2 = int(round((y0 - oy) / G_try)) * G_try + oy
        blk = qb.grid(inner, net, width, clr_pad, clr_trk, ox2, oy2, x1, y1, G_try)
        si = ((ax - ox2) // G_try, (ay - oy2) // G_try)
        ti = ((site[0] - ox2) // G_try, (site[1] - oy2) // G_try)
        ny, nx = blk.shape
        for (ii, jj) in (si, ti):
            if 0 <= ii < nx and 0 <= jj < ny:
                blk[jj, ii] = False
        path = qb.search(blk, si, ti)
        if path is None:
            qb.revert(m)
            continue
        pts = simplify(path, ox2, oy2, G_try)
        for k in range(len(pts) - 1):
            qb.track(net, inner, pts[k][0], pts[k][1],
                     pts[k + 1][0], pts[k + 1][1], width)
            total += math.hypot(pts[k + 1][0] - pts[k][0],
                                pts[k + 1][1] - pts[k][1])
        return dict(ok=True, mm=total / 1e6, grid=G_try / 1e6, vias=2,
                    pofv=[pa['ref']], layer=inner,
                    via_dia=via_dia / 1e6, via_drill=via_drill / 1e6,
                    via_xy=[(round(ax / 1e6, 3), round(ay / 1e6, 3)),
                            (round(site[0] / 1e6, 3), round(site[1] / 1e6, 3))],
                    pad_copper_mm=round((2 * half - via_dia) / 2e6, 4),
                    trunk_mm=width / 1e6, minw=width / 1e6)
    return dict(ok=False, reason='NO_PATH',
                why='no %s corridor at %.3f mm from %s to %s'
                    % (inner, width / 1e6, pa['ref'], pb['ref']))


def reserve_escape(qb, net, pa, width, clr_pad, clr_trk, near='B', far='I2',
                   G=50000, fine=25000, via_dia=350000, via_drill=200000,
                   toward=None, target=None):
    """D-266.  RESERVE ONE PAD'S EXIT, AND NOTHING MORE.

    002S measured three of its four failing pads still escaping at 0.20-0.25 mm
    on the FINISHED board: they were not walled in, they lost their lane to
    copper laid earlier for a branch that had the whole board to work with.
    002M-002S then showed that permuting whole-branch order only moves the
    casualty, because every order still asks a scarce pad to win a race against
    a branch that does not need to.

    A reservation breaks the race instead of re-running it.  It lays the
    MINIMUM neck the pad needs to leave `near`, plants one ordinary through via
    at the nearest site that neck can actually reach, and stops.  The long run
    is completed later, from the via, over a layer that is not scarce.

    It is deliberately NOT a connection:

      * it joins the pad to nothing, so it must never be counted as a route;
      * it is one neck plus one via, so it cannot become an alternate current
        path - a 0.20 mm sense stub carries no current a trunk would take;
      * the via is chosen by via_site(), so it is reachable BY CONSTRUCTION
        from this pad rather than merely nearby;
      * the via clears every copper layer, because a through via is copper on
        all of them (the same fact PR-47 learned as POFV_LAYER_CONFLICT).

    Returns dict(ok, mm, via=(x, y), layer, vias=1) or a reason.
    """
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    fail = None
    for G_try in (G, fine):
        prefer = toward
        e = qb.escape(pa, near, width, width, clr_pad, clr_trk, G_try, ox, oy,
                      prefer=prefer)
        if not e:
            # NOT a return.  A coarse grid can miss an exit a fine one finds -
            # measured: `U18.9` escapes at 0.25 mm with two directions at
            # 25 um and reports NO LEGAL ESCAPE at 50 um on the same copper -
            # and reporting the coarse answer as the pad's verdict is exactly
            # the misdiagnosis 002S spent a section on.  Fall to the fine grid
            # and only then believe it.
            fail = dict(ok=False, reason='NO_LEGAL_ESCAPE',
                        why=qb.escape_why[0], pad=pa['ref'])
            continue

        def free_everywhere(x, y):
            return all(qb.point_free(L, net, x, y, via_dia, clr_pad, clr_trk,
                                     G_try) for L in qb.cu)

        # WHERE THE VIA LANDS DECIDES THE BRANCH LENGTH, so when the partner
        # endpoint is known the site is CHOSEN rather than merely taken.
        #
        # `via_site` answers "nearest reachable site to this escape point",
        # which is the right question for a hop that only has to get off the
        # layer.  A Kelvin branch is judged on its TOTAL length against a
        # 10.000 mm cap, and the nearest site can sit on the wrong side of the
        # pad: measured, `R75.2`'s first reservation went 2.550 mm WEST while
        # its partner `U18.8` lies north-east, and the branch came to 10.456 mm
        # against the cap.  Scoring candidates on stub + remaining distance
        # costs nothing and picks the exit that leaves the shortest run.
        def score(x, y, stub):
            if target is None:
                return stub
            return stub + math.hypot(target[0] - x, target[1] - y)

        best, cand = None, None
        if target is None:
            # NO TARGET: keep the original two-phase preference EXACTLY - every
            # escape point is tested for a via site AT the escape first, and
            # only when none of them has one is a walk considered.  Collapsing
            # the two phases into one loop changes which site a pad takes even
            # when nothing else changed, and the `U18.8` pair that had been
            # accepted came back rejected on `BAT_MAIN routed clearance`.  A
            # fallback has to be the thing it is falling back TO.
            for c in e[:6]:
                if free_everywhere(c['x'], c['y']):
                    cand = dict(c)
                    cand['walk'] = None
                    break
            if cand is None:
                for c in e[:6]:
                    st = qb.via_site(near, far, net, c, width, via_dia,
                                     clr_pad, clr_trk, G_try,
                                     via_drill=via_drill)
                    if st is not None and free_everywhere(st[0], st[1]):
                        cand = dict(c)
                        cand['walk'] = st
                        break
        else:
            for c in e[:6]:
                if free_everywhere(c['x'], c['y']):
                    sc = score(c['x'], c['y'], c['ln'])
                    if best is None or sc < best:
                        best = sc
                        cand = dict(c)
                        cand['walk'] = None
                st = qb.via_site(near, far, net, c, width, via_dia,
                                 clr_pad, clr_trk, G_try, via_drill=via_drill)
                if st is not None and free_everywhere(st[0], st[1]):
                    sc = score(st[0], st[1], c['ln'] + math.hypot(
                        st[0] - c['x'], st[1] - c['y']))
                    if best is None or sc < best:
                        best = sc
                        cand = dict(c)
                        cand['walk'] = st
        if cand is None:
            fail = dict(ok=False, reason='NO_VIA_SITE',
                        why='%s: no %.2f mm via site reachable on %s'
                            % (pa['ref'], via_dia / 1e6, near),
                        pad=pa['ref'])
            continue
        m = qb.mark()
        total = 0.0
        qb.track(net, near, pa['x'], pa['y'], cand['x'], cand['y'], cand['w'])
        total += cand['ln']
        if cand.get('walk'):
            gx0 = min(cand['x'], cand['walk'][0]) - 6000000
            gy0 = min(cand['y'], cand['walk'][1]) - 6000000
            blkn = qb.grid(near, net, cand['w'], clr_pad, clr_trk, gx0, gy0,
                           max(cand['x'], cand['walk'][0]) + 6000000,
                           max(cand['y'], cand['walk'][1]) + 6000000, G_try)
            si = ((cand['x'] - gx0) // G_try, (cand['y'] - gy0) // G_try)
            ti = ((cand['walk'][0] - gx0) // G_try,
                  (cand['walk'][1] - gy0) // G_try)
            nyy, nxx = blkn.shape
            for (ii, jj) in (si, ti):
                if 0 <= ii < nxx and 0 <= jj < nyy:
                    blkn[jj, ii] = False
            pth = qb.search(blkn, si, ti)
            if pth is None:
                qb.revert(m)
                fail = dict(ok=False, reason='NO_NEAR_WALK',
                            why='%s: no %s corridor from the escape to its via '
                                'site' % (pa['ref'], near), pad=pa['ref'])
                continue
            pp = simplify(pth, int(gx0), int(gy0), G_try)
            for k in range(len(pp) - 1):
                qb.track(net, near, pp[k][0], pp[k][1],
                         pp[k + 1][0], pp[k + 1][1], cand['w'])
                total += math.hypot(pp[k + 1][0] - pp[k][0],
                                    pp[k + 1][1] - pp[k][1])
            cand['x'], cand['y'] = cand['walk']
        qb.via(net, cand['x'], cand['y'], via_dia, via_drill)
        return dict(ok=True, mm=total / 1e6, grid=G_try / 1e6, vias=1,
                    reservation=True, layer=far, near=near,
                    trunk_mm=width / 1e6, minw=width / 1e6,
                    via_dia=via_dia / 1e6, via_drill=via_drill / 1e6,
                    via=(int(cand['x']), int(cand['y'])),
                    via_xy=[(round(cand['x'] / 1e6, 3),
                             round(cand['y'] / 1e6, 3))])
    if fail is not None:
        return fail
    return dict(ok=False, reason='NO_LEGAL_ESCAPE',
                why='%s: no reservation possible at %.3f mm on %s'
                    % (pa['ref'], width / 1e6, near), pad=pa['ref'])


def join_reserved(qb, net, va, vb, width, clr_pad, clr_trk, layer='I2',
                  G=50000, fine=25000):
    """D-266.  COMPLETE A BRANCH BETWEEN TWO ALREADY-RESERVED VIA ENDPOINTS.

    Both endpoints already exist and are already connected to their pads, so
    this is a plain same-layer run between two points - no escape, no via
    siting, nothing that can be lost to a race.  That is the whole return on
    reserving: the part that was scarce is already spent.
    """
    ox, oy = qb.ex0 - 2000000, qb.ey0 - 2000000
    for G_try in (G, fine):
        margin = 8000000
        x0 = max(min(va[0], vb[0]) - margin, qb.ex0 - 1000000)
        y0 = max(min(va[1], vb[1]) - margin, qb.ey0 - 1000000)
        x1 = min(max(va[0], vb[0]) + margin, qb.ex1 + 1000000)
        y1 = min(max(va[1], vb[1]) + margin, qb.ey1 + 1000000)
        ox2 = int(round((x0 - ox) / G_try)) * G_try + ox
        oy2 = int(round((y0 - oy) / G_try)) * G_try + oy
        blk = qb.grid(layer, net, width, clr_pad, clr_trk, ox2, oy2, x1, y1,
                      G_try)
        si = ((va[0] - ox2) // G_try, (va[1] - oy2) // G_try)
        ti = ((vb[0] - ox2) // G_try, (vb[1] - oy2) // G_try)
        ny, nx = blk.shape
        for (ii, jj) in (si, ti):
            if 0 <= ii < nx and 0 <= jj < ny:
                blk[jj, ii] = False
        path = qb.search(blk, si, ti)
        if path is None:
            continue
        pts = simplify(path, ox2, oy2, G_try)
        total = 0.0
        m = qb.mark()
        for k in range(len(pts) - 1):
            qb.track(net, layer, pts[k][0], pts[k][1],
                     pts[k + 1][0], pts[k + 1][1], width)
            total += math.hypot(pts[k + 1][0] - pts[k][0],
                                pts[k + 1][1] - pts[k][1])
        return dict(ok=True, mm=total / 1e6, grid=G_try / 1e6, vias=0,
                    layer=layer, trunk_mm=width / 1e6, minw=width / 1e6,
                    inner_mm=total / 1e6)
    return dict(ok=False, reason='NO_PATH',
                why='no %s corridor at %.3f mm between the two reserved vias'
                    % (layer, width / 1e6))
