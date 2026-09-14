#!/usr/bin/env python3
"""READ-ONLY controls for verify_promotion's D-708 --board-outline-grown clause.

The clause is `outline_grew if claimed else not outline_changed`.  Six controls
exercise both arms and both failure directions, on real boards and on two
synthetic ones built by editing Edge.Cuts: a SHRUNK outline and a MOVED one,
each of which a bounding box would call "changed" and a containment test must
call a REFUSAL.
"""
import json, re, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import verify_promotion as V

AUTH = Path("/home/aqroot8/aqroot-demo/hardware/demo/kicad/aqroot-demo/"
            "aqroot-Beta-v2.kicad_pcb")
GROWN = Path("/home/aqroot8/aqroot-demo/w/d708/t2/aqroot-Beta-v2.kicad_pcb")
tmp = Path(tempfile.mkdtemp(prefix="d708-outline-"))


def edit_edges(src, dst, fn):
    txt = src.read_text()

    def sub(m):
        x, y = float(m.group(1)), float(m.group(2))
        nx, ny = fn(x, y)
        return "(%s %g %g)" % (m.group(0).split()[0][1:], nx, ny)
    out, i = [], 0
    for m in re.finditer(r'\t\(gr_line\n\t\t\(start ([-\d.]+) ([-\d.]+)\)\n'
                         r'\t\t\(end ([-\d.]+) ([-\d.]+)\)(.*?)\n\t\)\n',
                         txt, re.S):
        if '"Edge.Cuts"' not in m.group(5):
            continue
        sx, sy, ex, ey = (float(m.group(k)) for k in (1, 2, 3, 4))
        nsx, nsy = fn(sx, sy)
        nex, ney = fn(ex, ey)
        out.append((m.start(), m.end(),
                    '\t(gr_line\n\t\t(start %g %g)\n\t\t(end %g %g)%s\n\t)\n'
                    % (nsx, nsy, nex, ney, m.group(5))))
    for start, end, rep in reversed(out):
        txt = txt[:start] + rep + txt[end:]
    dst.write_text(txt)
    return len(out)


shrunk = tmp / "shrunk.kicad_pcb"
moved = tmp / "moved.kicad_pcb"
n1 = edit_edges(AUTH, shrunk, lambda x, y: (x * 0.98, y * 0.98))
n2 = edit_edges(AUTH, moved, lambda x, y: (x + 1.0, y))

sig = {k: V.outline_sig(p) for k, p in
       (("authority", AUTH), ("grown", GROWN),
        ("shrunk", shrunk), ("moved", moved))}


def clause(pre, post, claimed):
    opre, opost = sig[pre], sig[post]
    changed = opre != opost
    grew = (changed and len(opre) == 1 and len(opost) == 1
            and V.poly_is_contained(opre[0], opost[0]))
    return (grew if claimed else not changed), changed, grew


CONTROLS = [
    ("noop_unclaimed_passes",       "authority", "authority", False, True),
    ("noop_claimed_is_refused",     "authority", "authority", True,  False),
    ("grown_unclaimed_is_refused",  "authority", "grown",     False, False),
    ("grown_claimed_passes",        "authority", "grown",     True,  True),
    ("shrunk_claimed_is_refused",   "authority", "shrunk",    True,  False),
    ("moved_claimed_is_refused",    "authority", "moved",     True,  False),
]
probes, ok = [], True
for name, pre, post, claimed, expect in CONTROLS:
    got, changed, grew = clause(pre, post, claimed)
    probes.append(dict(control=name, pre=pre, post=post, claimed=claimed,
                       expected=expect, got=got, behaved=got == expect,
                       outline_changed=changed, outline_grew=grew))
    ok &= got == expect
report = dict(schema=1, decision="D-708",
              what="controls for verify_promotion.board_outline_as_claimed",
              edge_segments_edited=dict(shrunk=n1, moved=n2),
              extents_mm={k: V.outline_bbox_mm(v) for k, v in sig.items()},
              probes=probes, ok=bool(ok),
              verdict="PASS" if ok else "FAIL")
out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if out:
    out.write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
shutil.rmtree(tmp, ignore_errors=True)
