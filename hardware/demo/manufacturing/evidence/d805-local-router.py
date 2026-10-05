#!/usr/bin/env python3
"""D-805 local hand-copper router: a small A* on a 0.05 mm grid, F/In2/B,
foreign copper + holes + edge + keepout rule areas as obstacles.  Proposer only:
KiCad DRC on the result is the judge."""
import heapq, math, sys
import numpy as np
import pcbnew

MM = 1_000_000
G = 0.05  # grid mm
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
LCOST = {pcbnew.F_Cu: 1.3, pcbnew.In2_Cu: 1.0, pcbnew.B_Cu: 1.6}


class Router:
    def __init__(self, board, win):
        self.b = board
        self.x0, self.y0, self.x1, self.y1 = win
        self.nx = int(round((self.x1 - self.x0) / G)) + 1
        self.ny = int(round((self.y1 - self.y0) / G)) + 1
        xs = self.x0 + np.arange(self.nx) * G
        ys = self.y0 + np.arange(self.ny) * G
        self.X, self.Y = np.meshgrid(xs, ys)  # [iy, ix]
        sps = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(sps, False)
        self.outline = sps
        # edge distance grid (mm), negative outside
        chain = sps.Outline(0)
        pts = [(chain.CPoint(i).x / MM, chain.CPoint(i).y / MM) for i in range(chain.PointCount())]
        d = np.full(self.X.shape, 1e9)
        for a, c in zip(pts, pts[1:] + pts[:1]):
            d = np.minimum(d, self.seg_dist(self.X, self.Y, a, c))
        inside = np.zeros(self.X.shape, bool)
        for iy in range(self.ny):
            for ix in range(self.nx):
                inside[iy, ix] = sps.Contains(pcbnew.VECTOR2I(int(self.X[iy, ix] * MM), int(self.Y[iy, ix] * MM)))
        self.edge = np.where(inside, d, -1.0)

    def cells_bbox(self, bb, m):
        ix0 = max(0, int((bb[0] - m - self.x0) / G) - 1)
        ix1 = min(self.nx - 1, int((bb[2] + m - self.x0) / G) + 1)
        iy0 = max(0, int((bb[1] - m - self.y0) / G) - 1)
        iy1 = min(self.ny - 1, int((bb[3] + m - self.y0) / G) + 1)
        return ix0, ix1, iy0, iy1

    @staticmethod
    def seg_dist(X, Y, a, b):
        ax, ay = a; bx, by = b
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return np.hypot(X - ax, Y - ay)
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        return np.hypot(X - (ax + t * dx), Y - (ay + t * dy))

    def mark_shape(self, mask, shape, m, bb):
        ix0, ix1, iy0, iy1 = self.cells_bbox(bb, m)
        mn = int(m * MM)
        for iy in range(iy0, iy1 + 1):
            for ix in range(ix0, ix1 + 1):
                if mask[iy, ix]:
                    continue
                if shape.Collide(pcbnew.VECTOR2I(int(self.X[iy, ix] * MM), int(self.Y[iy, ix] * MM)), mn):
                    mask[iy, ix] = True

    def blocked(self, net, layer, m_cu, m_hole, m_edge, via=False):
        """mask of cells where a copper disc of the given margin may NOT sit."""
        mask = self.edge < m_edge
        w = (self.x0 - 2, self.y0 - 2, self.x1 + 2, self.y1 + 2)
        layers = [layer] if not via else [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
        for t in self.b.GetTracks():
            bb = t.GetBoundingBox()
            bbm = (bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
            if bbm[2] < w[0] or bbm[0] > w[2] or bbm[3] < w[1] or bbm[1] > w[3]:
                continue
            own = t.GetNetname() == net
            if t.GetClass() == "PCB_VIA":
                pos = (t.GetPosition().x / MM, t.GetPosition().y / MM)
                ix0, ix1, iy0, iy1 = self.cells_bbox(bbm, max(m_cu, m_hole) + 0.5)
                Xs, Ys = self.X[iy0:iy1 + 1, ix0:ix1 + 1], self.Y[iy0:iy1 + 1, ix0:ix1 + 1]
                d = np.hypot(Xs - pos[0], Ys - pos[1])
                sub = mask[iy0:iy1 + 1, ix0:ix1 + 1]
                if not own:
                    sub |= d < t.GetWidth(pcbnew.F_Cu) / MM / 2 + m_cu
                if via:  # hole to hole, any net
                    sub |= d < t.GetDrill() / MM / 2 + m_hole
                continue
            if own or t.GetLayer() not in layers:
                continue
            a = (t.GetStart().x / MM, t.GetStart().y / MM)
            c = (t.GetEnd().x / MM, t.GetEnd().y / MM)
            ix0, ix1, iy0, iy1 = self.cells_bbox(bbm, m_cu + 0.5)
            Xs, Ys = self.X[iy0:iy1 + 1, ix0:ix1 + 1], self.Y[iy0:iy1 + 1, ix0:ix1 + 1]
            mask[iy0:iy1 + 1, ix0:ix1 + 1] |= self.seg_dist(Xs, Ys, a, c) < t.GetWidth() / MM / 2 + m_cu
        for p in self.b.GetPads():
            bb = p.GetBoundingBox()
            bbm = (bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
            if bbm[2] < w[0] or bbm[0] > w[2] or bbm[3] < w[1] or bbm[1] > w[3]:
                continue
            own = p.GetNetname() == net and net != ""
            if not own:
                for L in layers:
                    if p.IsOnLayer(L) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                        self.mark_shape(mask, p.GetEffectiveShape(L), m_cu, bbm)
                        break
            if p.HasHole():
                hs = p.GetEffectiveHoleShape()
                # NPTH / foreign PTH: copper-to-hole; own PTH barrel only matters for vias
                if not own or via:
                    self.mark_shape(mask, hs, m_hole, bbm)
        for z in self.b.Zones():
            if not z.GetIsRuleArea():
                continue
            if not any(z.IsOnLayer(L) for L in layers):
                continue
            if not ((via and z.GetDoNotAllowVias()) or (not via and z.GetDoNotAllowTracks())):
                continue
            bb = z.GetBoundingBox()
            bbm = (bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
            self.mark_shape(mask, z.Outline(), m_cu, bbm)
        return mask

    def item_cells(self, layer, xy, net):
        """cells inside the own-net item at xy (pad/track/via)"""
        P = pcbnew.VECTOR2I(int(xy[0] * MM), int(xy[1] * MM))
        best = None
        for t in self.b.GetTracks():
            if t.GetNetname() == net and t.HitTest(P, 0) and (t.GetClass() == "PCB_VIA" or t.GetLayer() == layer):
                best = t; break
        if best is None:
            for p in self.b.GetPads():
                if p.GetNetname() == net and p.IsOnLayer(layer) and p.HitTest(P):
                    best = p; break
        assert best is not None, (layer, xy, net)
        isvia = best.GetClass() == "PCB_VIA"
        sh = best.GetEffectiveShape(layer)
        bb = best.GetBoundingBox()
        bbm = (bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
        m = np.zeros(self.X.shape, bool)
        self.mark_shape(m, sh, -0.0, bbm)
        # shrink: centre must be inside item
        return m, isvia

    def route(self, net, w, clr, via_d, via_drill, starts, goals, layers=None, allow_via=True,
              lcost=None, extra_block=None):
        layers = layers or LAYERS
        lcost = lcost or LCOST
        mt = clr + w / 2 + 0.03
        free = {L: ~self.blocked(net, L, mt, 0.25 + w / 2 + 0.03, 0.5 + w / 2 + 0.03) for L in layers}
        if extra_block is not None:
            for L in layers:
                free[L] &= ~extra_block(self.X, self.Y, L)
        vfree = None
        if allow_via:
            vfree = ~self.blocked(net, None, clr + via_d / 2 + 0.03, 0.25 + via_drill / 2 + 0.03,
                                  0.5 + via_d / 2 + 0.03, via=True)
            for L in layers:
                vfree &= free[L]
        S, Gm = {}, {}
        for (L, xy) in starts:
            m, isvia = self.item_cells(L, xy, net)
            for LL in (layers if isvia else [L]):
                S[LL] = S.get(LL, np.zeros(self.X.shape, bool)) | m
        for (L, xy) in goals:
            m, isvia = self.item_cells(L, xy, net)
            for LL in (layers if isvia else [L]):
                Gm[LL] = Gm.get(LL, np.zeros(self.X.shape, bool)) | m
        # target/start cells inside own copper are always enterable
        for L in layers:
            if L in S: free[L] = free[L] | S[L]
            if L in Gm: free[L] = free[L] | Gm[L]
        gpts = [(L, iy, ix) for L in Gm for iy, ix in zip(*np.nonzero(Gm[L]))]
        gx = np.array([p[2] for p in gpts]); gy = np.array([p[1] for p in gpts])

        def h(iy, ix):
            return float(np.min(np.hypot(gx - ix, gy - iy))) * G

        li = {L: i for i, L in enumerate(layers)}
        dist = {}
        prev = {}
        pq = []
        for L in S:
            if L not in li: continue
            for iy, ix in zip(*np.nonzero(S[L] & free[L])):
                k = (L, iy, ix)
                dist[k] = 0.0
                heapq.heappush(pq, (h(iy, ix), 0.0, k))
        moves = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        found = None
        n = 0
        while pq:
            f, d, k = heapq.heappop(pq)
            if d > dist.get(k, 1e18):
                continue
            L, iy, ix = k
            if L in Gm and Gm[L][iy, ix] and not (L in S and S[L][iy, ix]):
                found = k; break
            n += 1
            if n > 3_000_000:
                break
            for dx, dy in moves:
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < self.nx and 0 <= jy < self.ny) or not free[L][jy, jx]:
                    continue
                nd = d + (G * (1.4142 if dx and dy else 1.0)) * lcost[L]
                # discourage bends a little: prefer continuing direction
                pk = prev.get(k)
                if pk is not None and pk[0] == L and (iy - pk[1], ix - pk[2]) != (dy, dx):
                    nd += 0.02
                kk = (L, jy, jx)
                if nd < dist.get(kk, 1e18):
                    dist[kk] = nd; prev[kk] = k
                    heapq.heappush(pq, (nd + h(jy, jx), nd, kk))
            if allow_via and vfree[iy, ix]:
                for LL in layers:
                    if LL == L: continue
                    kk = (LL, iy, ix)
                    nd = d + 1.2
                    if nd < dist.get(kk, 1e18):
                        dist[kk] = nd; prev[kk] = k
                        heapq.heappush(pq, (nd + h(iy, ix), nd, kk))
        if found is None:
            return None
        path = [found]
        while path[-1] in prev:
            path.append(prev[path[-1]])
        path.reverse()
        return path

    def commit(self, path, net, w, via_d, via_drill):
        netobj = self.b.FindNet(net)
        segs, vias = [], []
        i = 0
        # split by layer runs
        runs = []
        cur = [path[0]]
        for k in path[1:]:
            if k[0] != cur[-1][0]:
                runs.append(cur); vias.append(k); cur = [k]
            else:
                cur.append(k)
        runs.append(cur)
        added = []
        for run in runs:
            if len(run) < 2:
                continue
            L = run[0][0]
            pts = [(r[2], r[1]) for r in run]
            # collapse collinear
            simp = [pts[0]]
            for j in range(1, len(pts) - 1):
                a, b_, c = simp[-1], pts[j], pts[j + 1]
                d1 = (b_[0] - a[0], b_[1] - a[1]); d2 = (c[0] - b_[0], c[1] - b_[1])
                n1 = (np.sign(d1[0]), np.sign(d1[1])); n2 = (np.sign(d2[0]), np.sign(d2[1]))
                if n1 != n2:
                    simp.append(b_)
            simp.append(pts[-1])
            for a, c in zip(simp, simp[1:]):
                t = pcbnew.PCB_TRACK(self.b)
                t.SetStart(pcbnew.VECTOR2I(int(round((self.x0 + a[0] * G) * MM)), int(round((self.y0 + a[1] * G) * MM))))
                t.SetEnd(pcbnew.VECTOR2I(int(round((self.x0 + c[0] * G) * MM)), int(round((self.y0 + c[1] * G) * MM))))
                t.SetWidth(int(round(w * MM))); t.SetLayer(L); t.SetNet(netobj)
                self.b.Add(t); added.append(("T", self.b.GetLayerName(L), (self.x0 + a[0] * G, self.y0 + a[1] * G), (self.x0 + c[0] * G, self.y0 + c[1] * G)))
        seen=set()
        for k in vias:
            if (k[1],k[2]) in seen: continue
            seen.add((k[1],k[2]))
            v = pcbnew.PCB_VIA(self.b)
            v.SetPosition(pcbnew.VECTOR2I(int(round((self.x0 + k[2] * G) * MM)), int(round((self.y0 + k[1] * G) * MM))))
            v.SetWidth(int(round(via_d * MM))); v.SetDrill(int(round(via_drill * MM)))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(netobj)
            self.b.Add(v); added.append(("V", (self.x0 + k[2] * G, self.y0 + k[1] * G)))
        return added
