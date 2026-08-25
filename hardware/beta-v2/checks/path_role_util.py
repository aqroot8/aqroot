# -*- coding: utf-8 -*-
"""Path-role support: named rule areas, the D-249 rule block, and net taps."""
import os, io, math, json, shutil, subprocess, collections
import pcbnew

KC = r"P:/New folder (2)/bin/kicad-cli.exe"
AUTH_DIR = r"P:/Vaults/ClaudeVault/AQROOT/hardware/beta-v2/kicad/aqroot-beta-v2"
PCBNAME = "aqroot-Beta-v2.kicad_pcb"
DRUNAME = "aqroot-Beta-v2.kicad_dru"
NEEDED = (DRUNAME, "aqroot-Beta-v2.kicad_pro", "fp-lib-table", "sym-lib-table", "libraries")


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
    subprocess.run([KC, "pcb", "drc", "--severity-all", "--format", "json",
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
def add_named_area(board, name, x0, y0, x1, y1, layers=('B.Cu',)):
    """A rule area that restricts NOTHING -- it exists only so a .kicad_dru rule
    can say `A.enclosedByArea('NAME')`.  That is what makes width a PATH ROLE
    rather than a property of the net name."""
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
