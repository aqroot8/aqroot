"""D-734.  Is /BQ25185_STAT2 able to leave U11.3 AT ALL?

Not "does the maze find a path" -- that is a search.  This asks the PHYSICAL
question directly: sweep a fine grid over the pocket west of U11's land column,
and for every cell ask whether a track of width W centred there is legal against
EVERY obstacle on B.Cu, at the clearance each obstacle is actually owed:

    * a PAD owes the pad-escape clearance (0.200 mm inside U11's courtyard)
    * a BAT_MAIN TRACK owes D-269's 0.300 mm, because D-269's condition is
      `A.hasNetclass('BAT_MAIN') && A.Type != 'Pad' && B.Type != 'Pad'`
    * everything else owes 0.200 mm
    * same-net copper owes nothing

Then flood-fill from U11.3's own land and report whether the legal set reaches
anywhere outside the pocket.  Run per width; a width whose flood never leaves
is a width the package cannot launch, at any lattice and by any router.

    python3 d734-screen-u11-3-escape.py BOARD [W_MM ...]
"""
import sys, json, math, pcbnew

BOARD = sys.argv[1]
WIDTHS = [float(w) for w in sys.argv[2:]] or [0.200, 0.150, 0.120, 0.100, 0.090]
NET = '/BQ25185_STAT2'
LAND = (66.400, 77.800)          # U11.3
# the pocket: west of the land column, north to south of U11's courtyard
X0, X1, Y0, Y1 = 63.000, 67.200, 75.200, 80.400
G = 0.010                         # 10 micron sweep -- finer than any lattice

b = pcbnew.LoadBoard(BOARD)
BCU = b.GetLayerID('B.Cu')

BAT = '/01_POWER_TREE/BAT_PROTECTED_P'
import os
D269 = float(os.environ.get('AQROOT_D269_MM', '0.300'))
def owed(netname, is_pad):
    if netname == NET:
        return None                       # same net: nothing owed
    if netname == BAT and not is_pad:
        return D269                       # D-269, track-to-track
    return 0.200

OBS = []   # (kind, geom, clearance, label)
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        if not t.IsOnLayer(BCU): continue
        c = owed(t.GetNetname(), False)
        if c is None: continue
        p = t.GetPosition()
        OBS.append(('seg', (p.x/1e6, p.y/1e6, p.x/1e6, p.y/1e6, t.GetWidth()/2e6),
                    c, 'via:' + t.GetNetname()))
    else:
        if t.GetLayer() != BCU: continue
        c = owed(t.GetNetname(), False)
        if c is None: continue
        s, e = t.GetStart(), t.GetEnd()
        OBS.append(('seg', (s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6, t.GetWidth()/2e6),
                    c, 'trk:' + t.GetNetname()))
for f in b.GetFootprints():
    for pad in f.Pads():
        if not pad.IsOnLayer(BCU): continue
        c = owed(pad.GetNetname(), True)
        if c is None: continue
        bb = pad.GetBoundingBox()
        OBS.append(('rect', (bb.GetLeft()/1e6, bb.GetTop()/1e6,
                             bb.GetRight()/1e6, bb.GetBottom()/1e6),
                    c, 'pad:%s.%s' % (f.GetReference(), pad.GetNumber())))
        if pad.GetDrillSize().x > 0:
            p = pad.GetPosition(); r = max(pad.GetDrillSize().x, pad.GetDrillSize().y)/2e6
            OBS.append(('seg', (p.x/1e6, p.y/1e6, p.x/1e6, p.y/1e6, r), max(c, 0.250),
                        'hole:%s.%s' % (f.GetReference(), pad.GetNumber())))

# keep only obstacles that can possibly bind inside the window
def _bb(kind, g, clr):
    if kind == 'seg':
        ax, ay, bx, by, r = g
        return (min(ax,bx)-r-clr, min(ay,by)-r-clr, max(ax,bx)+r+clr, max(ay,by)+r+clr)
    x0, y0, x1, y1 = g
    return (x0-clr, y0-clr, x1+clr, y1+clr)
OBS = [o for o in OBS
       if (lambda q: q[0] <= X1 and q[2] >= X0 and q[1] <= Y1 and q[3] >= Y0)(_bb(o[0], o[1], o[2]))]


def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx-ax, by-ay
    L2 = vx*vx + vy*vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-ax)*vx + (py-ay)*vy)/L2))
    return math.hypot(px-(ax+t*vx), py-(ay+t*vy))

def slack(px, py, all_near=False):
    """min over obstacles of (distance - own radius - clearance); who binds."""
    best, who = 1e9, None
    near = []
    for kind, g, clr, lbl in OBS:
        if kind == 'seg':
            ax, ay, bx, by, r = g
            d = seg_dist(px, py, ax, ay, bx, by) - r
        else:
            x0, y0, x1, y1 = g
            dx = max(x0-px, 0.0, px-x1); dy = max(y0-py, 0.0, py-y1)
            d = math.hypot(dx, dy)
        v = d - clr
        if all_near:
            near.append((round(v, 4), lbl))
        if v < best:
            best, who = v, lbl
    if all_near:
        near.sort()
        return best, who, near[:5]
    return best, who

nx = int((X1-X0)/G)+1; ny = int((Y1-Y0)/G)+1
S = [[0.0]*nx for _ in range(ny)]
W = [[None]*nx for _ in range(ny)]
for j in range(ny):
    py = Y0 + j*G
    for i in range(nx):
        S[j][i], W[j][i] = slack(X0 + i*G, py)

out = {'schema': 1, 'board': BOARD, 'net': NET, 'land': LAND,
       'window_mm': [X0, Y0, X1, Y1], 'grid_mm': G,
       'clearance_model': {'pad': 0.200, 'BAT_MAIN_track': 0.300, 'other': 0.200,
                           'same_net': 'nothing owed'},
       'widths': {}}

def cell(x, y):
    return (int(round((y-Y0)/G)), int(round((x-X0)/G)))

for w in WIDTHS:
    half = w/2.0
    free = [[S[j][i] >= half for i in range(nx)] for j in range(ny)]
    # seed: the part of U11.3's own land inside the window
    seeds = []
    for i in range(nx):
        x = X0 + i*G
        if 66.025 <= x <= 66.775:
            for j in range(ny):
                y = Y0 + j*G
                if 77.700 <= y <= 77.900 and free[j][i]:
                    seeds.append((j, i))
    seen = set(seeds); stack = list(seeds)
    while stack:
        j, i = stack.pop()
        for dj, di in ((1,0),(-1,0),(0,1),(0,-1)):
            v = (j+dj, i+di)
            if 0 <= v[0] < ny and 0 <= v[1] < nx and v not in seen and free[v[0]][v[1]]:
                seen.add(v); stack.append(v)
    # does the reachable set leave the pocket -- i.e. touch the window edge?
    escaped = any(j in (0, ny-1) or i in (0, nx-1) for (j, i) in seen)
    # widest legal cell anywhere in the channel west of the land
    bestslack, bestwho, bestxy = -9.9, None, None
    for j in range(ny):
        for i in range(nx):
            x, y = X0+i*G, Y0+j*G
            if 65.800 <= x <= 66.025 and 76.900 <= y <= 78.300:
                if S[j][i] > bestslack:
                    bestslack, bestwho, bestxy = S[j][i], W[j][i], (round(x,4), round(y,4))
    out['widths']['%.3f' % w] = {
        'legal_seed_cells': len(seeds),
        'reachable_cells': len(seen),
        'escapes_the_pocket': bool(escaped),
        'widest_half_slack_in_the_west_channel_mm': round(bestslack, 4),
        'widest_track_the_west_channel_admits_mm': round(2*bestslack, 4),
        'at': bestxy, 'bound_by': bestwho,
        'five_tightest_at_that_point': (slack(bestxy[0], bestxy[1], True)[2]
                                        if bestxy else None),
        'd269_clearance_used_mm': D269,
    }

print(json.dumps(out, indent=1))
