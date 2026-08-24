#!/usr/bin/env python3
"""AQROOT Full Beta v2 - FBV2-P1 floorplan geometry model and regression checks.

Created at FBV2-P1-002 (2026-08-24).

Datum
-----
All geometry in this file uses the **P1 doc datum**: origin at the LOWER-LEFT
board corner, X to the right, Y UP, millimetres.  KiCad's file datum is the
upper-left with Y down, so ``Y_kicad = BOARD_H - Y_doc`` and X is unchanged.

Nothing here writes to the board.  It reads the .kicad_pcb through pcbnew and
reports.  The companion script ``p1_apply.py`` is the only writer.
"""
import math, json, sys, os

BOARD_W, BOARD_H = 70.0, 148.0
CAVITY = (-2.5, -3.5, 72.5, 151.5)          # x0,y0,x1,y1 in doc datum

# ---------------------------------------------------------------- NFC (D-220)
NFC_CX, NFC_CY = 30.8, 124.5                # circular geometry centre
NFC_CLEAR_D   = 48.0                        # Oe48 metal-free CLEAR region
NFC_METAL_D   = 58.0                        # Oe58 metal exclusion
NFC_PLACE_BOX = 48.0                        # 48 x 48 placement/tolerance box

# ---------------------------------------------------------------- reservations
BATTERY = (6.0, 23.5, 66.0, 98.5)           # 60 x 75 x 8.0, unchanged
SPEAKER = (48.0, 1.0, 68.0, 21.0)           # Oe20 x 3 + sealed cavity
SPEAKER_C = (58.0, 11.0)
DISPLAY = (3.39, 55.04, 59.93, 140.00)      # module envelope, FRONT
DISPLAY_ACTIVE = (7.18, 60.80, 56.14, 134.24)
ANT433  = (-2.40, 1.50, -0.20, 48.50)       # flex on the LEFT cavity wall
USB_AP  = (36.0, -3.5, 48.0, 1.2)
USD_AP  = (6.0, -21.0, 22.0, 1.2)
IR_TX_OPT = (48.0, 140.0, 56.5, 148.0)
IR_BARRIER= (57.5, 140.0, 60.5, 148.0)
IR_RX_OPT = (61.5, 140.0, 70.0, 148.0)
COMM_RECESS = (59.90, 104.0, 70.0, 138.0)
MIC_ACOUSTIC = (0.5, 46.5, 5.5, 53.5)

# ---------------------------------------------------------------- 915 SMA
SMA_X, SMA_Y = 5.0, 148.0                   # bulkhead hole centre, top panel
SMA_HOLE_D   = 6.5                          # panel clearance hole
SMA_HEX_AF   = 8.0                          # 8 HEX across flats  (drawing)
SMA_HEX_AC   = SMA_HEX_AF / math.cos(math.radians(30))   # across corners
SMA_WASHER_D = 10.2                         # Oe10.2 REF star washer (external)

# ---------------------------------------------------------------- 915 coax
COAX_OD = 1.80          # RG-178 worst case (CAB.01034 1.32 mm coax is smaller)
COAX_R  = COAX_OD / 2.0
BEND_R_MIN = 5.0
# U8 IPEX port, doc datum, after the U7/U8 swap
U8_IPEX = (9.0, 16.6)

COAX_PATH = [
    (9.00,  16.60),   # U8 IPEX, U.FL right-angle plug
    (5.40,  19.20),   # leaves the plug westward over U8's own body
    (3.00,  25.50),   # enters the left rear channel, clear of the battery
    (3.00, 108.00),   # straight north beside the battery, over MK1's sealed can
    (0.30, 118.50),   # eases west around the Oe58 NFC metal exclusion
    (0.30, 130.50),   # the pinch: 30.50 mm from the NFC centre
    (5.00, 143.00),   # back east, clear of the exclusion, toward the bulkhead
    (5.00, 148.00),   # SMA bulkhead, top panel
]
COAX_BEND_ALLOWANCE = 0.6   # mm added per interior vertex for the real radius
COAX_SERVICE_LOOP   = 15.0  # T-6, must be carried by the chosen assembly


# ---------------------------------------------------------------- 433 cable
# U7 sits in the middle bottom-rear slot after the FBV2-P1-002 swap; its flex
# lives on the LEFT cavity wall (region F).  The lead is dressed north-west
# over U8's can and down the wall.  It crosses the 915 coax ONCE, at about
# (4.5, 21.5), on top of U8 - two shielded 50 ohm coaxes, neither crossing a
# radiating element, so C-6 is satisfied.
ANT433_PATH = [
    (26.00, 16.60),   # U7 IPEX / MHF1
    (22.00, 20.60),
    (4.00, 21.60),
    (-1.00, 19.00),
    (-1.30, 6.00),    # flex tail on the left wall
]

# ---------------------------------------------------------------- bosses
# U1's F.CrtYd bbox is the manufacturer ANTENNA KEEP-OUT polygon, not the module
# body.  Collision review must use the body; the keep-out is tested separately.
U1_BODY = (42.90, 9.90, 63.06, 30.10)

BOSS_M2_KEEPOUT_PREF = 6.0
BOSS_M2_KEEPOUT_MIN  = 4.5


def rect_pts(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rect_overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def rect_gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return math.hypot(dx, dy)


def circ_rect_min_dist(cx, cy, r):
    """Closest distance from the circle CENTRE to rectangle r (0 if inside)."""
    dx = max(r[0] - cx, 0.0, cx - r[2])
    dy = max(r[1] - cy, 0.0, cy - r[3])
    return math.hypot(dx, dy)


def seg_point_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def seg_rect_dist(a, b, r):
    """Minimum distance between segment a-b and axis-aligned rectangle r."""
    corners = rect_pts(r)
    edges = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    # inside test
    for p in (a, b):
        if r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]:
            return 0.0
    best = min(seg_point_dist(c, a, b) for c in corners)
    for e in edges:
        best = min(best, seg_point_dist(a, *e), seg_point_dist(b, *e))
        # proper crossing
        if _seg_cross(a, b, e[0], e[1]):
            return 0.0
    return best


def _ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])


def _seg_cross(a, b, c, d):
    return (_ccw(a, c, d) * _ccw(b, c, d) < 0) and (_ccw(a, b, c) * _ccw(a, b, d) < 0)


def path_length(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def coax_routed_length(pts=COAX_PATH):
    return path_length(pts) + COAX_BEND_ALLOWANCE * (len(pts) - 2)


def bend_radii(pts):
    """Effective radius at each interior vertex for a tangent-arc fillet."""
    out = []
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        v1 = (a[0] - b[0], a[1] - b[1]); v2 = (c[0] - b[0], c[1] - b[1])
        n1 = math.hypot(*v1); n2 = math.hypot(*v2)
        if n1 == 0 or n2 == 0:
            continue
        cosang = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
        ang = math.acos(cosang)                       # interior angle
        turn = math.pi - ang                          # deviation
        if turn < 1e-6:
            out.append((i, float('inf'), math.degrees(turn)))
            continue
        avail = min(n1, n2) * 0.5
        out.append((i, avail / math.tan(turn / 2.0), math.degrees(turn)))
    return out


# =====================================================================
# Board reader
# =====================================================================
PCB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad",
                   "aqroot-beta-v2", "aqroot-Beta-v2.kicad_pcb")


def load_parts(path=PCB):
    import pcbnew
    b = pcbnew.LoadBoard(os.path.abspath(path))
    mm = lambda v: v / 1e6
    parts = []
    for f in b.GetFootprints():
        lay = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd
        poly = f.GetCourtyard(lay)
        px, py = mm(f.GetPosition().x), mm(f.GetPosition().y)
        has = poly.OutlineCount() > 0
        if has:
            bb = poly.BBox()
            x0, x1 = mm(bb.GetLeft()), mm(bb.GetRight())
            yk0, yk1 = mm(bb.GetTop()), mm(bb.GetBottom())
        else:
            x0 = x1 = px
            yk0 = yk1 = py
        thru = any(p.GetAttribute() in (0, 3) for p in f.Pads())
        holes = []
        for pd in f.Pads():
            if pd.GetAttribute() not in (0, 3):
                continue
            hb = pd.GetBoundingBox()
            holes.append((round(mm(hb.GetLeft()), 4), round(BOARD_H - mm(hb.GetBottom()), 4),
                          round(mm(hb.GetRight()), 4), round(BOARD_H - mm(hb.GetTop()), 4)))
        parts.append(dict(
            ref=f.GetReference(), val=f.GetValue(),
            fp=str(f.GetFPID().GetUniStringLibId()),
            x=round(px, 4), y=round(BOARD_H - py, 4),
            side='B' if f.IsFlipped() else 'F',
            rot=round(f.GetOrientationDegrees(), 2),
            thru=thru, holes=holes, dnp=f.IsDNP(), has_court=has,
            court=(round(x0, 4), round(BOARD_H - yk1, 4),
                   round(x1, 4), round(BOARD_H - yk0, 4)),
        ))
    for p in parts:
        if p['ref'] == 'U1':
            p['keepout'] = p['court']
            p['court'] = U1_BODY
    return b, parts


# =====================================================================
# Regression checks
# =====================================================================
def nfc_checks():
    out = []
    rc, rm = NFC_CLEAR_D / 2.0, NFC_METAL_D / 2.0
    C = (NFC_CX, NFC_CY)
    d = circ_rect_min_dist(*C, BATTERY)
    out.append(("NFC clear <-> battery gap", round(d - rc, 3), ">= 0 zero overlap", d - rc >= 0))
    out.append(("battery inside NFC metal Oe58", round(max(0.0, rm - d), 3), "informational", None))
    ds = circ_rect_min_dist(*C, SPEAKER)
    out.append(("NFC loop <-> speaker", round(ds - rc, 3), ">= 20.0", ds - rc >= 20.0))
    d4 = circ_rect_min_dist(*C, ANT433)
    out.append(("NFC clear <-> 433 flex body", round(d4 - rc, 3), "> 0", d4 - rc > 0))
    ok = (C[0] - rc >= CAVITY[0] and C[1] - rc >= CAVITY[1] and
          C[0] + rc <= CAVITY[2] and C[1] + rc <= CAVITY[3])
    out.append(("NFC clear region inside cavity", "-", "true", ok))
    return out


def metal_intruders(parts, extra=()):
    rm = NFC_METAL_D / 2.0
    hits = []
    for p in parts:
        if not p['has_court']:
            continue
        if p['side'] == 'F' and not p['thru']:
            continue
        d = circ_rect_min_dist(NFC_CX, NFC_CY, p['court'])
        if d < rm:
            hits.append((p['ref'], p['side'], 'THRU' if p['thru'] else 'B.Cu',
                         round(rm - d, 3)))
    for name, rect in extra:
        d = circ_rect_min_dist(NFC_CX, NFC_CY, rect)
        if d < rm:
            hits.append((name, '-', 'reservation', round(rm - d, 3)))
    return sorted(hits, key=lambda h: -h[3])


def coax_legal(pts=COAX_PATH, parts=None):
    rm = NFC_METAL_D / 2.0
    fails, rows = [], []
    obstacles = [
        ("433 flex body", ANT433), ("battery envelope", BATTERY),
        ("speaker cavity", SPEAKER), ("microSD card travel", USD_AP),
        ("USB-C aperture", USB_AP), ("IR TX optical", IR_TX_OPT),
        ("IR barrier", IR_BARRIER), ("IR RX optical", IR_RX_OPT),
        ("community recess", COMM_RECESS),
    ]
    if parts:
        j5 = next((p for p in parts if p['ref'] == 'J5'), None)
        if j5:
            obstacles.append(("J5 courtyard", j5['court']))
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        clr = seg_point_dist((NFC_CX, NFC_CY), a, b) - rm - COAX_R
        rows.append((i, "NFC Oe58 metal exclusion", round(clr, 3), clr >= 0))
        if clr < 0:
            fails.append((i, "NFC Oe58 metal exclusion", round(clr, 3)))
        for name, rect in obstacles:
            d = seg_rect_dist(a, b, rect) - COAX_R
            rows.append((i, name, round(d, 3), d >= 0))
            if d < 0:
                fails.append((i, name, round(d, 3)))
        for p in (a, b):
            if not (CAVITY[0] + COAX_R <= p[0] <= CAVITY[2] - COAX_R and
                    CAVITY[1] <= p[1] <= CAVITY[3] + 0.001):
                fails.append((i, "cavity containment", p))
    return fails, rows


def sma_checks():
    out = []
    rm = NFC_METAL_D / 2.0
    d = math.dist((SMA_X, SMA_Y), (NFC_CX, NFC_CY))
    v = d - SMA_HEX_AC / 2 - rm
    out.append(("SMA hex Oe%.2f <-> NFC Oe58" % SMA_HEX_AC, round(v, 3), ">= 0", v >= 0))
    v = d - SMA_WASHER_D / 2 - rm
    out.append(("SMA washer Oe10.2 <-> NFC Oe58", round(v, 3), ">= 0", v >= 0))
    for nm, ap in (("IR TX", IR_TX_OPT), ("IR RX", IR_RX_OPT)):
        cc = abs((ap[0] + ap[2]) / 2 - SMA_X)
        out.append((f"SMA <-> {nm} window centre-to-centre", round(cc, 3), ">= 15.0", cc >= 15.0))
        ee = ap[0] - (SMA_X + SMA_HEX_AC / 2)
        out.append((f"SMA body <-> {nm} aperture edge-to-edge", round(ee, 3), ">= 8.0", ee >= 8.0))
    v = (SMA_X - SMA_WASHER_D / 2) - CAVITY[0]
    out.append(("SMA washer edge -> cavity left wall", round(v, 3), ">= 0", v >= 0))
    return out


def boss_search(parts, keepout_d, coax=COAX_PATH, step=0.25, edge=1.0, skip_boss=True):
    r = keepout_d / 2.0
    rm = NFC_METAL_D / 2.0
    blocked = [DISPLAY, BATTERY, SPEAKER, USD_AP, USB_AP,
               IR_TX_OPT, IR_BARRIER, IR_RX_OPT, MIC_ACOUSTIC, COMM_RECESS]
    courts = [p['court'] for p in parts
              if p['has_court'] and not (skip_boss and p['ref'].startswith('BOSS'))]
    found = []
    y = edge + r
    while y <= BOARD_H - edge - r + 1e-9:
        x = edge + r
        while x <= BOARD_W - edge - r + 1e-9:
            k = (x - r, y - r, x + r, y + r)
            ok = math.dist((x, y), (NFC_CX, NFC_CY)) >= rm + r
            if ok:
                ok = not any(rect_overlap(k, br) for br in blocked)
            if ok:
                ok = not any(rect_overlap(k, c) for c in courts)
            if ok:
                ok = all(seg_rect_dist(coax[i], coax[i + 1], k) >= COAX_R
                         for i in range(len(coax) - 1))
            if ok:
                found.append((round(x, 3), round(y, 3)))
            x += step
        y += step
    return found


def cluster(points, sep=6.0):
    out = []
    for p in points:
        if all(math.dist(p, q) > sep for q in out):
            out.append(p)
    return out
