# -*- coding: utf-8 -*-
"""Path-role support: named rule areas, the D-249 rule block, and net taps."""
import os, io, math, json, shutil, subprocess, collections
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness_paths as HP
import pcbnew

# FBV2-CLOUD-001: these were workstation literals ("P:/New folder (2)/...").
# They are now resolved from this file's own location and from PATH/KICAD_CLI,
# so the same committed script runs on the Windows machine and on the Ubuntu
# worker.  kicad-cli is resolved lazily -- importing this module must not fail
# on a machine that only needs the pcbnew half of it.
AUTH_DIR = HP.project_dir()
PCBNAME = HP.PCBNAME
DRUNAME = HP.DRUNAME
NEEDED = HP.PROJECT_CONTEXT


def assert_ctx(pcb):
    d = os.path.dirname(os.path.abspath(pcb))
    miss = [n for n in NEEDED if not os.path.exists(os.path.join(d, n))]
    if miss:
        raise SystemExit("PROJECT CONTEXT MISSING next to %s: %s" % (pcb, miss))
    return d


def fresh(workdir, name):
    dst = os.path.join(workdir, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(AUTH_DIR, dst)
    pcb = os.path.join(dst, PCBNAME)
    assert_ctx(pcb)
    return pcb


def drc(pcb, tag, work):
    assert_ctx(pcb)
    out = os.path.join(work, "drc_%s.json" % tag)
    subprocess.run([HP.kicad_cli(), "pcb", "drc", "--severity-all", "--format", "json",
                    "-o", out, pcb], capture_output=True, text=True)
    j = json.load(open(out, encoding='utf-8'))
    c = collections.Counter()
    det = collections.defaultdict(list)
    for key in ("violations", "unconnected_items", "schematic_parity"):
        for v in j.get(key, []):
            t = v.get("type", key)
            c[t] += 1
            det[t].append(v.get("description", ""))
    return c, det


def ratsnest(pcb):
    b = pcbnew.LoadBoard(pcb)
    b.BuildConnectivity()
    return b.GetConnectivity().GetUnconnectedCount(True)


# --------------------------------------------------------------------------
def add_named_area(board, name, x0, y0, x1, y1, layers=('B.Cu', 'F.Cu')):
    """A rule area that restricts NOTHING -- it exists only so a .kicad_dru rule
    can say `A.enclosedByArea('NAME')`.  That is what makes width a PATH ROLE
    rather than a property of the net name.

    FBV2-P2-002K: THE CORRIDOR NOW SPANS BOTH OUTER LAYERS, AND IT HAS TO.

    These areas were created on B.Cu alone, which was true of the board while
    every battery route was on B.Cu.  D-256 authorises planned F.Cu escapes for
    the LTC4368 low-current paths, and the moment a D-249-ruled tap takes one,
    `A.enclosedByArea('BAT_RAW_TAP_U18')` is FALSE for the F.Cu half of its own
    corridor -- so the 0.20 mm ruling silently stops applying and the segments
    are judged against BAT_RAW's 0.60 mm class floor instead.  That is exactly
    how `BAT_RAW U18.1 -> R77.1` came back from the gate as
    `new DRC {"track_width": 5, "clearance": 1}`: five F.Cu segments outside a
    B.Cu-only rule area.

    Nothing is weakened by the change.  A rule area here restricts NOTHING --
    DoNotAllowTracks/Vias/Pads/ZoneFills/Footprints are all False -- it only
    NAMES a region so a width rule can be conditioned on it.  Extending the
    name to the other outer layer of the same corridor makes the existing D-249
    ruling apply where the copper actually is."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName(name)
    ls = pcbnew.LSET()
    for L in layers:
        ls.addLayer(board.GetLayerID(L))
    z.SetLayerSet(ls)
    o = z.Outline()
    o.NewOutline()
    for (px, py) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(int(px), int(py))
    z.SetLocalClearance(0)
    board.Add(z)
    return z


def set_area_box(board, name, x0, y0, x1, y1):
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetZoneName() == name:
            o = z.Outline()
            o.RemoveAllContours()
            o.NewOutline()
            for (px, py) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                o.Append(int(px), int(py))
            return z
    return None


# --------------------------------------------------------------------------
def nearest_on_net(board, net, layer, x, y, exclude=()):
    """Nearest point on already-laid copper of `net`, and the track it lies on."""
    LID = board.GetLayerID(layer)
    best = None
    for t in board.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != LID:
            continue
        if t.GetNetname() != net or t in exclude:
            continue
        ax, ay = t.GetStart().x, t.GetStart().y
        bx, by = t.GetEnd().x, t.GetEnd().y
        vx, vy = float(bx - ax), float(by - ay)
        L2 = vx * vx + vy * vy
        s = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / L2))
        px, py = ax + s * vx, ay + s * vy
        d = math.hypot(x - px, y - py)
        if best is None or d < best[0]:
            best = (d, int(round(px)), int(round(py)), t)
    return best


def split_at(board, t, px, py):
    """Split a track so the tap point is an exact shared endpoint of three
    tracks -- an unambiguous junction rather than a touching overlap."""
    ax, ay = t.GetStart().x, t.GetStart().y
    bx, by = t.GetEnd().x, t.GetEnd().y
    if (px, py) in ((ax, ay), (bx, by)):
        return []
    made = []
    for (sx, sy, ex, ey) in ((ax, ay, px, py), (px, py, bx, by)):
        if sx == ex and sy == ey:
            continue
        n = pcbnew.PCB_TRACK(board)
        n.SetStart(pcbnew.VECTOR2I(sx, sy))
        n.SetEnd(pcbnew.VECTOR2I(ex, ey))
        n.SetWidth(t.GetWidth())
        n.SetLayer(t.GetLayer())
        n.SetNet(t.GetNet())
        board.Add(n)
        made.append(n)
    board.Remove(t)
    return made


def pseudo_pad(net, x, y, qr):
    """A zero-size anchor the router can treat as a terminal, used when a branch
    joins the middle of an existing trunk instead of another component pad."""
    return dict(ref='(tap)', x=int(x), y=int(y), F=False, B=True,
                shape=qr.RR(int(x), int(y), 1, 1, 0, 0, net, 'tap'),
                hx=1, hy=1, r=0, ang=0, net=net, tht=False)


# --------------------------------------------------------------------------
# PR-11: corridors, not bounding boxes.
#
# A bounding box around a 20 mm branch is a 67 x 23 mm hole in the trunk rule.
# A corridor is the branch's own centreline, buffered just far enough to
# enclose its copper plus a rule-area tolerance, so the exception covers the
# branch and nothing else.
CORRIDOR_TOL = 100000          # 0.10 mm per side beyond the copper envelope


def corridor_from_tracks(board, tracks, tol=CORRIDOR_TOL):
    """Union of oriented capsules along each track centreline."""
    ps = pcbnew.SHAPE_POLY_SET()
    for t in tracks:
        if t.GetClass() != 'PCB_TRACK':
            # A via contributes a square of its own diameter.  PCB_VIA.GetWidth()
            # WITHOUT A LAYER ARGUMENT asserts inside KiCad 10 and the assert
            # handler stalls the process for minutes - which is exactly how this
            # loop looked like a hung router.  Ask per layer.
            try:
                vw = t.GetWidth(pcbnew.B_Cu)
            except TypeError:
                vw = t.GetDrill() * 2
            r = vw / 2.0 + tol
            cx, cy = t.GetPosition().x, t.GetPosition().y
            one = pcbnew.SHAPE_POLY_SET()
            one.NewOutline()
            for (dx, dy) in ((-r, -r), (r, -r), (r, r), (-r, r)):
                one.Append(int(cx + dx), int(cy + dy))
            ps.BooleanAdd(one)
            continue
        x0, y0 = t.GetStart().x, t.GetStart().y
        x1, y1 = t.GetEnd().x, t.GetEnd().y
        r = t.GetWidth() / 2.0 + tol
        dx, dy = float(x1 - x0), float(y1 - y0)
        L = math.hypot(dx, dy)
        if L == 0:
            continue
        ux, uy = dx / L, dy / L
        px, py = -uy, ux
        ax, ay = x0 - ux * r, y0 - uy * r
        bx, by = x1 + ux * r, y1 + uy * r
        one = pcbnew.SHAPE_POLY_SET()
        one.NewOutline()
        for (X, Y) in ((ax + px * r, ay + py * r), (bx + px * r, by + py * r),
                       (bx - px * r, by - py * r), (ax - px * r, ay - py * r)):
            one.Append(int(X), int(Y))
        ps.BooleanAdd(one)
    ps.Simplify()
    return ps


def set_area_poly(board, name, ps):
    """Replace a named rule area's outline with an arbitrary polygon set."""
    for z in board.Zones():
        if not (z.GetIsRuleArea() and z.GetZoneName() == name):
            continue
        o = z.Outline()
        o.RemoveAllContours()
        for i in range(ps.OutlineCount()):
            c = ps.Outline(i)
            o.NewOutline()
            for k in range(c.PointCount()):
                o.Append(c.CPoint(k).x, c.CPoint(k).y)
        return z
    return None
